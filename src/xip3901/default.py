# src/xip3901/default.py
from __future__ import annotations

import json
from typing import Any, Dict, Optional
from requests.exceptions import RequestException

from src.xip3901.api import Call


def _ensure_dot_suffix(s: str) -> str:
    s = (s or "").strip()
    return s if s.endswith(".") else f"{s}."


def _host_only(v: Optional[str]) -> str:
    if not v:
        return ""
    v = v.strip()
    if "://" in v:
        v = v.split("://", 1)[1]
    v = v.split("/", 1)[0]
    v = v.split(":", 1)[0]
    return v


class Defaults:
    def __init__(self, name: str, host: str, port: int = 80):
        self.name = name
        self.host = host
        self.port = port
        self.client = Call(host=host, port=port)

        self.config = self._load_json_from_repo("config/config.json")
        self.refs   = self._load_json_from_repo("config/xip3901_parameters_reference.json")

        try:
            self.last_octet = int(str(host).split(".")[-1])
        except Exception:
            self.last_octet = int(host)

        self.red_prefix  = _ensure_dot_suffix(self.config.get("2110_Red", "232.20."))
        self.blue_prefix = _ensure_dot_suffix(self.config.get("2110_Blue", "232.120."))
        self.video_rng   = self._expand_range(self.config.get("2110_VIDEO_RANGE", "101-108"))
        self.meta_rng    = self._expand_range(self.config.get("2110_META_RANGE",  "1-8"))
        a_start, a_end   = self._expand_range_pair(self.config.get("2110_AUDIO_RANGE", "201-232"))
        self.audio_rng_start = a_start
        self.audio_rng_end   = a_end

        udp_flat   = self.refs.get("defaults", {})
        udp_nested = udp_flat.get("udp_ports", {}) if isinstance(udp_flat.get("udp_ports", {}), dict) else {}

        def _pick(k_flat: str, k_nested: str, dflt: int) -> int:
            v_flat = udp_flat.get(k_flat)
            if isinstance(v_flat, (int, str)) and str(v_flat).strip():
                return int(v_flat)
            v_nested = udp_nested.get(k_nested)
            if isinstance(v_nested, (int, str)) and str(v_nested).strip():
                return int(v_nested)
            return dflt

        self.udp_video = _pick("video_udp", "video", 50100)
        self.udp_audio = _pick("audio_udp", "audio", 50200)
        self.udp_meta  = _pick("meta_udp",  "meta",  50300)

        self.audio_type    = udp_flat.get("audio_type", "SMPTE ST 2110-30")
        self.audio_profile = udp_flat.get("audio_profile", "125 usec, 16ch")

        self.audio_streams = int(self.refs.get("defaults", {}).get("audio_streams_per_output", 1))

    def preview_summary(self) -> Dict[str, Any]:
        summary = {"unit": self.name, "host": self.host,
                   "udp_ports": {"video": self.udp_video, "audio": self.udp_audio, "meta": self.udp_meta},
                   "video": {}, "audio": {}, "meta": {}}
        for out_idx in range(8):
            v_oct = self.video_rng[out_idx]
            summary["video"][f"out{out_idx+1}"] = {
                "trunk1": f"{self.red_prefix}{self.last_octet}.{v_oct}",
                "trunk2": f"{self.blue_prefix}{self.last_octet}.{v_oct}",
            }
        cur = self.audio_rng_start
        for out_idx in range(8):
            summary["audio"][f"out{out_idx+1}"] = {
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

    def apply_network_and_hostname(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        hostname = f"{self.config.get('XIP3901_RANGE_NAME_PFIX','XIP3901-')}{self.last_octet:03}"
        path = self.refs.get("networking", {}).get("host", {}).get("path", "networking/host")
        try:
            results["hostname"] = self.client.put(path, json_data={"hostname": hostname})
        except RequestException as exc:
            results["hostname"] = {"error": str(exc)}
        return results

    def apply_interfaces(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        def _body(mode: str, ip="0.0.0.0", sm="0.0.0.0", gw_="0.0.0.0"):
            return {"mode": mode, "ipAddress": ip, "subnetMask": sm, "gateway": gw_}

        ifaces_cfg = self.config.get("XIP3901_INTERFACES")
        if isinstance(ifaces_cfg, dict) and all(k in ifaces_cfg for k in ("eth1", "eth2", "eth3", "frame")):
            for ifid in ("eth1", "eth2", "eth3", "frame"):
                c = ifaces_cfg.get(ifid) or {}
                mode = str(c.get("mode", "Auto (DHCP)"))
                ip   = str(c.get("ipAddress", "0.0.0.0"))
                sm   = str(c.get("subnetMask", "0.0.0.0"))
                gw   = str(c.get("gateway", "0.0.0.0"))
                try:
                    results[ifid] = self.client.put(f"networking/interfaces/{ifid}",
                                                    json_data=_body(mode, ip, sm, gw))
                except RequestException as exc:
                    results[ifid] = {"error": str(exc)}
            return results

        ctrl_net = (self.config.get("XIP3901_CONTROL_PREFIX", "10.169.60") or "10.169.60").rstrip(".")
        mask = self.config.get("XIP3901_NETMASK", "255.255.0.0")
        gw   = self.config.get("XIP3901_GATEWAY", f"{ctrl_net}.1")
        payloads = {
            "eth1": _body("Auto (DHCP)"),
            "eth2": _body("Auto (DHCP)"),
            "eth3": _body("Static", ip=f"{ctrl_net}.{self.last_octet}", sm=mask, gw_=gw),
            "frame": _body("Off"),
        }
        for ifid, b in payloads.items():
            try:
                results[ifid] = self.client.put(f"networking/interfaces/{ifid}", json_data=b)
            except RequestException as exc:
                results[ifid] = {"error": str(exc)}
        return results

    def apply_nmos_and_ptp(self) -> Dict[str, Any]:
        import time
        out: Dict[str, Any] = {}

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

        links = self.config.get("LINKS") or {}
        reg_ip = _host_only((links.get("hi") if isinstance(links, dict) else None))

        try:
            out["nmos_global_off"] = self.client.put(nmos_global_path, json_data={"mode": "OFF", "label": hostname})
        except RequestException as exc:
            out["nmos_global_off"] = {"error": str(exc)}
        time.sleep(0.6)

        try:
            out["nmos_registry"] = self.client.put(nmos_reg_path, json_data={
                "registryMode": reg_mode,
                "httpAddress": reg_ip,
                "registrationPort": reg_port,
                "queryPort": query_port
            })
        except RequestException as exc:
            out["nmos_registry"] = {"error": str(exc)}
        time.sleep(0.6)

        try:
            out["nmos_global_on"] = self.client.put(nmos_global_path, json_data={"mode": nmos_mode, "label": hostname})
        except RequestException as exc:
            out["nmos_global_on"] = {"error": str(exc)}
        time.sleep(0.6)

        try:
            out["ptp"] = self.client.put(ptp_path, json_data={
                "domainNumber": ptp_domain,
                "announceInterval": ptp_int,
                "announceReceiptTimeoutCount": ptp_to,
                "dscp": ptp_dscp
            })
        except RequestException as exc:
            out["ptp"] = {"error": str(exc)}

        return out

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

    # NEW: one-shot wrapper
    def apply_all_defaults(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        try:
            out["hostname"] = self.apply_network_and_hostname()
        except Exception as exc:
            out["hostname"] = {"error": str(exc)}

        try:
            out["interfaces"] = self.apply_interfaces()
        except Exception as exc:
            out["interfaces"] = {"error": str(exc)}

        try:
            out["nmos_ptp"] = self.apply_nmos_and_ptp()
        except Exception as exc:
            out["nmos_ptp"] = {"error": str(exc)}

        try:
            out["senders"] = self.apply_senders()
        except Exception as exc:
            out["senders"] = {"error": str(exc)}

        try:
            out["advanced_qos"] = self.apply_advanced_qos()
        except Exception as exc:
            out["advanced_qos"] = {"error": str(exc)}

        return out

    def _fill_rtp_body(self, template: Dict[str, Any], suffix_octet: int, udp_port: int, audio: bool = False) -> Dict[str, Any]:
        t = json.loads(json.dumps(template))
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