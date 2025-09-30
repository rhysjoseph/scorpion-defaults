import json
from typing import Any, Dict, Optional
from requests.exceptions import RequestException

from src.xip3901.api import Call


def _ensure_dot_suffix(s: str) -> str:
    s = (s or "").strip()
    return s if s.endswith(".") else f"{s}."


def _norm_url(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    v = v.strip()
    if v.startswith(("http://", "https://")):
        return v
    return f"http://{v}"


def _host_only(v: Optional[str]) -> str:
    """Return just the host (IPv4) from '10.1.2.3', 'http://10.1.2.3:80', etc."""
    if not v:
        return ""
    v = v.strip()
    if "://" in v:
        v = v.split("://", 1)[1]
    v = v.split("/", 1)[0]
    v = v.split(":", 1)[0]
    return v


class Defaults:
    """
    XIP3901 defaults: hostname, interfaces, NMOS, PTP, 2110 senders, QoS.
    Reads global ranges from config/config.json and API standards from
    config/xip3901_parameters_reference.json.
    """

    def __init__(self, name: str, host: str, port: int = 80):
        self.name = name
        self.host = host
        self.port = port
        self.client = Call(host=host, port=port)

        self.config = self._load_json_from_repo("config/config.json")
        self.refs   = self._load_json_from_repo("config/xip3901_parameters_reference.json")

        # Control IP last octet
        try:
            self.last_octet = int(str(host).split(".")[-1])
        except Exception:
            self.last_octet = int(host)

        # Multicast prefixes and media ranges
        self.red_prefix  = _ensure_dot_suffix(self.config.get("2110_Red", "232.20."))
        self.blue_prefix = _ensure_dot_suffix(self.config.get("2110_Blue", "232.120."))
        self.video_rng   = self._expand_range(self.config.get("2110_VIDEO_RANGE", "101-108"))
        self.meta_rng    = self._expand_range(self.config.get("2110_META_RANGE",  "1-8"))
        a_start, a_end   = self._expand_range_pair(self.config.get("2110_AUDIO_RANGE", "201-232"))
        self.audio_rng_start = a_start
        self.audio_rng_end   = a_end

        # XIP: only one audio stream per channel
        self.audio_streams = int(self.refs["defaults"].get("audio_streams_per_output", 1))

        # UDPs and audio type/profile from standards JSON
        self.udp_video = int(self.refs["defaults"]["udp_ports"]["video"])
        self.udp_audio = int(self.refs["defaults"]["udp_ports"]["audio"])
        self.udp_meta  = int(self.refs["defaults"]["udp_ports"]["meta"])
        self.audio_type    = self.refs["defaults"]["audio_type"]
        self.audio_profile = self.refs["defaults"]["audio_profile"]

    # -------------------------------------------------------------------------
    # Preview (unchanged)
    # -------------------------------------------------------------------------
    def preview_summary(self) -> Dict[str, Any]:
        summary = {
            "unit": self.name,
            "host": self.host,
            "udp_ports": {"video": self.udp_video, "audio": self.udp_audio, "meta": self.udp_meta},
            "video": {}, "audio": {}, "meta": {}
        }

        for out_idx in range(8):
            v_oct = self.video_rng[out_idx]
            summary["video"][f"out{out_idx+1}"] = {
                "trunk1": f"{self.red_prefix}{self.last_octet}.{v_oct}",
                "trunk2": f"{self.blue_prefix}{self.last_octet}.{v_oct}",
            }

        cur = self.audio_rng_start
        for out_idx in range(8):
            out_key = f"out{out_idx+1}"
            summary["audio"][out_key] = {
                "stream1": {
                    "trunk1": f"{self.red_prefix}{self.last_octet}.{cur}",
                    "trunk2": f"{self.blue_prefix}{self.last_octet}.{cur}",
                }
            }
            cur += 1

        for out_idx in range(8):
            m_oct = self.meta_rng[out_idx]
            summary["meta"][f"out{out_idx+1}"] = {
                "trunk1": f"{self.red_prefix}{self.last_octet}.{m_oct}",
                "trunk2": f"{self.blue_prefix}{self.last_octet}.{m_oct}",
            }
        return summary

    # -------------------------------------------------------------------------
    # Hostname (unchanged)
    # -------------------------------------------------------------------------
    def apply_network_and_hostname(self) -> Dict[str, Any]:
        results = {}
        hostname = f"{self.config.get('XIP3901_RANGE_NAME_PFIX','XIP3901-')}{self.last_octet:03}"
        path = self.refs.get("networking", {}).get("host", {}).get("path", "networking/host")
        try:
            results["hostname"] = self.client.put(path, json_data={"hostname": hostname})
        except RequestException as exc:
            results["hostname"] = {"error": str(exc)}
        return results

    # -------------------------------------------------------------------------
    # Interfaces (unchanged)
    # -------------------------------------------------------------------------
    def apply_interfaces(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        ctrl_pfix = self.config.get("XIP3901_CONTROL_PREFIX", "10.169.60")
        mask = self.config.get("XIP3901_NETMASK", "255.255.0.0")
        gw   = self.config.get("XIP3901_GATEWAY", f"{ctrl_pfix}.1")

        def body(mode: str, ip="0.0.0.0", sm="0.0.0.0", gw_="0.0.0.0"):
            return {"mode": mode, "ipAddress": ip, "subnetMask": sm, "gateway": gw_}

        payloads = {
            "eth1": body("Auto (DHCP)"),
            "eth2": body("Auto (DHCP)"),
            "eth3": body("Static", ip=f"{ctrl_pfix}.{self.last_octet}", sm=mask, gw_=gw),
            "frame": body("Off")
        }

        for ifid, b in payloads.items():
            try:
                results[ifid] = self.client.put(f"networking/interfaces/{ifid}", json_data=b)
            except RequestException as exc:
                results[ifid] = {"error": str(exc)}

        return results

    # -------------------------------------------------------------------------
    # NMOS + PTP (UPDATED ENDPOINTS)
    # -------------------------------------------------------------------------
    def apply_nmos_and_ptp(self) -> Dict[str, Any]:
        """
        Force-apply NMOS + PTP in a deterministic sequence:
        1) NMOS global -> OFF (graceful stop)
        2) NMOS registry -> set address/ports
        3) NMOS global -> desired mode + label
        4) PTP -> domain/interval/timeout/dscp
        Skips any read-before-write checks; always overwrites.
        """
        import time
        out: Dict[str, Any] = {}

        # ---- Defaults & paths ----
        nmos_mode   = self.refs.get("defaults", {}).get("nmos_mode", "IS-04 & IS-05")
        reg_mode    = self.refs.get("defaults", {}).get("registry_mode", "Static")
        reg_port    = int(self.refs.get("defaults", {}).get("registry_port", 3020))
        query_port  = int(self.refs.get("defaults", {}).get("query_port", 3021))

        ptp_domain  = int(self.refs.get("defaults", {}).get("ptp_domain", 127))
        ptp_int     = str(self.refs.get("defaults", {}).get("ptp_announce_interval", "1"))
        ptp_to      = int(self.refs.get("defaults", {}).get("ptp_announce_timeout", 3))
        ptp_dscp    = int(self.refs.get("defaults", {}).get("ptp_dscp", 46))

        hostname = f"{self.config.get('XIP3901_RANGE_NAME_PFIX','XIP3901-')}{self.last_octet:03}"

        nmos_global_path = self.refs.get("nmos", {}).get("global", {}).get("path", "nmos/global")
        nmos_reg_path    = self.refs.get("nmos", {}).get("registry", {}).get("path", "nmos/registry")
        ptp_path         = self.refs.get("ptp", {}).get("path", "reference/ptp")

        # bare IPv4 for registry httpAddress
        links = self.config.get("LINKS") or {}
        hi = links.get("hi") if isinstance(links, dict) else None
        reg_ip = _host_only(hi)

        long_timeout = 12.0  # NMOS can take a moment to cycle

        # ---- 1) NMOS OFF ----
        try:
            off_body = {"mode": "OFF", "label": hostname}
            out["nmos_global_off"] = self.client.put(nmos_global_path, json_data=off_body, timeout=long_timeout)
        except RequestException as exc:
            out["nmos_global_off"] = {"error": str(exc)}
        time.sleep(0.8)

        # ---- 2) Registry ----
        try:
            reg_body = {
                "registryMode": reg_mode,           # "Auto" | "Static"
                "httpAddress": reg_ip,              # bare IPv4
                "registrationPort": reg_port,
                "queryPort": query_port
            }
            out["nmos_registry"] = self.client.put(nmos_reg_path, json_data=reg_body, timeout=long_timeout)
        except RequestException as exc:
            out["nmos_registry"] = {"error": str(exc)}
        time.sleep(0.8)

        # ---- 3) NMOS desired mode + label ----
        try:
            on_body = {"mode": nmos_mode, "label": hostname}
            out["nmos_global_on"] = self.client.put(nmos_global_path, json_data=on_body, timeout=long_timeout)
        except RequestException as exc:
            out["nmos_global_on"] = {"error": str(exc)}
        time.sleep(0.8)

        # ---- 4) PTP ----
        try:
            ptp_body = {
                "domainNumber": ptp_domain,
                "announceInterval": ptp_int,                # must be string per API
                "announceReceiptTimeoutCount": ptp_to,
                "dscp": ptp_dscp
            }
            out["ptp"] = self.client.put(ptp_path, json_data=ptp_body, timeout=long_timeout)
        except RequestException as exc:
            out["ptp"] = {"error": str(exc)}

        return out

    # -------------------------------------------------------------------------
    # 2110 Senders / Advanced QoS / Internals (unchanged)
    # -------------------------------------------------------------------------
    def apply_senders(self) -> Dict[str, Any]:
        results = {"video": [], "audio": [], "meta": []}

        v_ref = self.refs["senders"]["video"]
        for out_idx in range(8):
            v_oct = self.video_rng[out_idx]
            body = self._fill_rtp_body(v_ref["body_template"], v_oct, self.udp_video)
            path = v_ref["path_template"].format(channelId=out_idx + 1)
            try:
                results["video"].append(self.client.put(path, json_data=body))
            except RequestException as exc:
                results["video"].append({"error": str(exc)})

        a_ref = self.refs["senders"]["audio"]
        cur = self.audio_rng_start
        for out_idx in range(8):
            body = self._fill_rtp_body(a_ref["body_template"], cur, self.udp_audio, audio=True)
            path = a_ref["path_template"].format(channelId=out_idx + 1)
            try:
                results["audio"].append(self.client.put(path, json_data=body))
            except RequestException as exc:
                results["audio"].append({"error": str(exc)})
            cur += 1

        m_ref = self.refs["senders"]["meta"]
        for out_idx in range(8):
            m_oct = self.meta_rng[out_idx]
            body = self._fill_rtp_body(m_ref["body_template"], m_oct, self.udp_meta)
            path = m_ref["path_template"].format(channelId=out_idx + 1)
            try:
                results["meta"].append(self.client.put(path, json_data=body))
            except RequestException as exc:
                results["meta"].append({"error": str(exc)})

        return results

    def apply_advanced_qos(self) -> Dict[str, Any]:
        adv = self.refs.get("advanced", {})
        out: Dict[str, Any] = {}

        try:
            out["video"] = self.client.put(adv["video"]["path"], json_data={
                "dscp": adv["video"]["dscp"], "payloadType": adv["video"]["payloadType"]
            })
        except Exception as exc:
            out["video"] = {"error": str(exc)}

        try:
            out["audio30"] = self.client.put(adv["audio30"]["path"], json_data={
                "dscp": adv["audio30"]["dscp"], "payloadType": adv["audio30"]["payloadType"]
            })
        except Exception as exc:
            out["audio30"] = {"error": str(exc)}

        try:
            out["audio31"] = self.client.put(adv["audio31"]["path"], json_data={
                "dscp": adv["audio31"]["dscp"], "payloadType": adv["audio31"]["payloadType"]
            })
        except Exception as exc:
            out["audio31"] = {"error": str(exc)}

        try:
            out["meta"] = self.client.put(adv["meta"]["path"], json_data={
                "dscp": adv["meta"]["dscp"], "payloadType": adv["meta"]["payloadType"]
            })
        except Exception as exc:
            out["meta"] = {"error": str(exc)}

        if "global" in adv and "minimumProcessingDelayEnable" in adv["global"]:
            try:
                out["global"] = self.client.put(adv["global"]["path"], json_data={
                    "minimumProcessingDelayEnable": adv["global"]["minimumProcessingDelayEnable"]
                })
            except Exception as exc:
                out["global"] = {"error": str(exc)}

        return out

    def _fill_rtp_body(self, template: Dict[str, Any], suffix_octet: int, udp_port: int, audio: bool = False) -> Dict[str, Any]:
        t = json.loads(json.dumps(template))  # deep copy
        red  = f"{self.red_prefix}{self.last_octet}.{suffix_octet}"
        blue = f"{self.blue_prefix}{self.last_octet}.{suffix_octet}"

        t["rtp"][0]["txStreamAddress"] = red
        t["rtp"][1]["txStreamAddress"] = blue
        t["rtp"][0]["txStreamPort"] = udp_port
        t["rtp"][1]["txStreamPort"] = udp_port

        if audio:
            t["smpteType"] = self.audio_type
            t["profile"]   = self.audio_profile

        return t

    @staticmethod
    def _expand_range(s: str):
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))

    @staticmethod
    def _expand_range_pair(s: str):
        a, b = s.split("-")
        return int(a), int(b)

    @staticmethod
    def _load_json_from_repo(rel_path: str) -> Dict[str, Any]:
        import os
        here = os.path.dirname(os.path.realpath(__file__))
        src  = os.path.dirname(here)
        root = os.path.dirname(src)
        with open(f"{root}/{rel_path}", "r", encoding="utf-8") as f:
            return json.load(f)