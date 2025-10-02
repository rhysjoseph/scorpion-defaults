# src/scorpion/default.py

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional

import json
import os
from math import ceil
from copy import deepcopy

from requests.exceptions import RequestException
from src.scorpion.api import Call

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.dirname(PARENT_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)


# ---------------------------
# 2110 expansion helpers
# ---------------------------
def expand_2110_outputs(default_params: dict, config: dict, device_ip: str, outputs: int = 8) -> dict:
    """
    Expand/default params to include explicit per-output/trunk entries for 2110 video/audio/meta.

    VIDEO/META:
      IP format:    <param>.<out>.<trunk>               (6501 / 6601)
      UDP format:   <param>.<out>.<trunk>               (6502/6503, 6602/6603)
      ENABLE format:<param>.<out>.<trunk>               (6500 / 6600)

    AUDIO:
      IP format:    <param>.<out>.<stream>.<trunk>      (6551)
      UDP format:   <param>.<out>.<stream>.<trunk>      (6552/6553)
      ENABLE format:<param>.<out>.<stream>.<trunk>      (6550)

    Precedence (most specific → least) applies:
      fully-qualified key → less-qualified key → base key → generated value
    """
    def parse_range_string(r):
        if r is None:
            return []
        if isinstance(r, (list, tuple)):
            return list(r)
        s = str(r).strip()
        if "-" in s:
            a, b = s.split("-", 1)
            return list(range(int(a), int(b) + 1))
        if "," in s:
            return [int(x.strip()) for x in s.split(",") if x.strip()]
        return [int(s)]

    def _ensure_dot_suffix(s):
        s = str(s)
        return s if s.endswith(".") else s + "."

    params = deepcopy(default_params or {})
    last_octet = str(device_ip).strip().split(".")[-1]

    # Config
    audio_streams = int(config.get("2110_AUDIO_STREAMS", 4))
    if audio_streams < 1:
        audio_streams = 1

    media_map = {
        "video": {
            "enable": "6500",
            "ip": "6501",
            "udp": "6502",
            "src_udp": "6503",
            "range_key": "2110_VIDEO_RANGE",
            "flat_udp": "50100",
        },
        "audio": {
            "enable": "6550",
            "ip": "6551",
            "udp": "6552",
            "src_udp": "6553",
            "range_key": "2110_AUDIO_RANGE",
            "flat_udp": "50200",
        },
        "meta": {
            "enable": "6600",
            "ip": "6601",
            "udp": "6602",
            "src_udp": "6603",
            "range_key": "2110_META_RANGE",
            "flat_udp": "50300",
        },
    }

    red_prefix = _ensure_dot_suffix(config.get("2110_Red", "232.20."))
    blue_prefix = _ensure_dot_suffix(config.get("2110_Blue", "232.120."))

    # Base defaults (flat UDPs; will also write specifics below)
    for m in media_map.values():
        params.setdefault(m["enable"], 1)
        params.setdefault(m["udp"], m["flat_udp"])
        params.setdefault(m["src_udp"], m["flat_udp"])

    # Parse ranges
    video_rng = parse_range_string(config.get(media_map["video"]["range_key"], "101-108"))
    meta_rng = parse_range_string(config.get(media_map["meta"]["range_key"], "1-8"))
    audio_rng = parse_range_string(config.get(media_map["audio"]["range_key"], "201-232"))

    # Pad video/meta ranges to outputs if needed (repeat last)
    if len(video_rng) < outputs:
        base = video_rng or [101]
        video_rng = base + [base[-1]] * (outputs - len(base))
    if len(meta_rng) < outputs:
        base = meta_rng or [1]
        meta_rng = base + [base[-1]] * (outputs - len(base))

    # AUDIO: linear suffix across ALL outputs/streams (avoid duplication)
    audio_start = audio_rng[0] if audio_rng else 201

    # -------- VIDEO (per-output, per-trunk) --------
    v = media_map["video"]
    video_udp_flat = str(params.get(v["udp"], v["flat_udp"]))
    video_src_udp_flat = str(params.get(v["src_udp"], v["flat_udp"]))
    video_enable_flat = str(params.get(v["enable"], 1))

    for out_idx in range(outputs):
        suffix_value = video_rng[out_idx]
        for trunk in (0, 1):
            # IP (6501)
            ip_key_specific = f"{v['ip']}.{out_idx}.{trunk}"
            if ip_key_specific not in params:
                ip_key_output = f"{v['ip']}.{out_idx}"
                ip_key_base = f"{v['ip']}"
                if ip_key_output in params:
                    params[ip_key_specific] = params[ip_key_output]
                elif ip_key_base in params:
                    params[ip_key_specific] = params[ip_key_base]
                else:
                    prefix = red_prefix if trunk == 0 else blue_prefix
                    params[ip_key_specific] = f"{prefix}{last_octet}.{suffix_value}"

            # UDP DEST (6502)
            udp_key_specific = f"{v['udp']}.{out_idx}.{trunk}"
            if udp_key_specific not in params:
                udp_key_output = f"{v['udp']}.{out_idx}"
                udp_key_base = f"{v['udp']}"
                if udp_key_output in params:
                    params[udp_key_specific] = params[udp_key_output]
                elif udp_key_base in params:
                    params[udp_key_specific] = video_udp_flat
                else:
                    params[udp_key_specific] = video_udp_flat

            # UDP SRC (6503)
            src_udp_key_specific = f"{v['src_udp']}.{out_idx}.{trunk}"
            if src_udp_key_specific not in params:
                src_udp_key_output = f"{v['src_udp']}.{out_idx}"
                src_udp_key_base = f"{v['src_udp']}"
                if src_udp_key_output in params:
                    params[src_udp_key_specific] = params[src_udp_key_output]
                elif src_udp_key_base in params:
                    params[src_udp_key_specific] = video_src_udp_flat
                else:
                    params[src_udp_key_specific] = video_src_udp_flat

            # ENABLE (6500)
            en_key_specific = f"{v['enable']}.{out_idx}.{trunk}"
            if en_key_specific not in params:
                en_key_output = f"{v['enable']}.{out_idx}"
                en_key_base = f"{v['enable']}"
                if en_key_output in params:
                    params[en_key_specific] = params[en_key_output]
                elif en_key_base in params:
                    params[en_key_specific] = video_enable_flat
                else:
                    params[en_key_specific] = "1"

    # -------- META (per-output, per-trunk) --------
    m = media_map["meta"]
    meta_udp_flat = str(params.get(m["udp"], m["flat_udp"]))
    meta_src_udp_flat = str(params.get(m["src_udp"], m["flat_udp"]))
    meta_enable_flat = str(params.get(m["enable"], 1))

    for out_idx in range(outputs):
        suffix_value = meta_rng[out_idx]
        for trunk in (0, 1):
            # IP (6601)
            ip_key_specific = f"{m['ip']}.{out_idx}.{trunk}"
            if ip_key_specific not in params:
                ip_key_output = f"{m['ip']}.{out_idx}"
                ip_key_base = f"{m['ip']}"
                if ip_key_output in params:
                    params[ip_key_specific] = params[ip_key_output]
                elif ip_key_base in params:
                    params[ip_key_specific] = params[ip_key_base]
                else:
                    prefix = red_prefix if trunk == 0 else blue_prefix
                    params[ip_key_specific] = f"{prefix}{last_octet}.{suffix_value}"

            # UDP DEST (6602)
            udp_key_specific = f"{m['udp']}.{out_idx}.{trunk}"
            if udp_key_specific not in params:
                udp_key_output = f"{m['udp']}.{out_idx}"
                udp_key_base = f"{m['udp']}"
                if udp_key_output in params:
                    params[udp_key_specific] = params[udp_key_output]
                elif udp_key_base in params:
                    params[udp_key_specific] = meta_udp_flat
                else:
                    params[udp_key_specific] = meta_udp_flat

            # UDP SRC (6603)
            src_udp_key_specific = f"{m['src_udp']}.{out_idx}.{trunk}"
            if src_udp_key_specific not in params:
                src_udp_key_output = f"{m['src_udp']}.{out_idx}"
                src_udp_key_base = f"{m['src_udp']}"
                if src_udp_key_output in params:
                    params[src_udp_key_specific] = params[src_udp_key_output]
                elif src_udp_key_base in params:
                    params[src_udp_key_specific] = meta_src_udp_flat
                else:
                    params[src_udp_key_specific] = meta_src_udp_flat

            # ENABLE (6600)
            en_key_specific = f"{m['enable']}.{out_idx}.{trunk}"
            if en_key_specific not in params:
                en_key_output = f"{m['enable']}.{out_idx}"
                en_key_base = f"{m['enable']}"
                if en_key_output in params:
                    params[en_key_specific] = params[en_key_output]
                elif en_key_base in params:
                    params[en_key_specific] = meta_enable_flat
                else:
                    params[en_key_specific] = "1"

    # -------- AUDIO (per-output, per-stream, per-trunk) --------
    a = media_map["audio"]
    audio_udp_flat = str(params.get(a["udp"], a["flat_udp"]))
    audio_src_udp_flat = str(params.get(a["src_udp"], a["flat_udp"]))
    audio_enable_flat = str(params.get(a["enable"], 1))

    for out_idx in range(outputs):
        for stream_idx in range(audio_streams):
            linear = out_idx * audio_streams + stream_idx
            ip_suffix_value = audio_start + linear
            for trunk in (0, 1):
                # IP (6551)
                ip_key_specific = f"{a['ip']}.{out_idx}.{stream_idx}.{trunk}"
                if ip_key_specific not in params:
                    ip_key_stream = f"{a['ip']}.{out_idx}.{stream_idx}"
                    ip_key_output = f"{a['ip']}.{out_idx}"
                    ip_key_base = f"{a['ip']}"
                    if ip_key_stream in params:
                        params[ip_key_specific] = params[ip_key_stream]
                    elif ip_key_output in params:
                        params[ip_key_specific] = params[ip_key_output]
                    elif ip_key_base in params:
                        params[ip_key_specific] = params[ip_key_base]
                    else:
                        prefix = red_prefix if trunk == 0 else blue_prefix
                        params[ip_key_specific] = f"{prefix}{last_octet}.{ip_suffix_value}"

                # UDP DEST (6552)
                udp_key_specific = f"{a['udp']}.{out_idx}.{stream_idx}.{trunk}"
                if udp_key_specific not in params:
                    udp_key_stream = f"{a['udp']}.{out_idx}.{stream_idx}"
                    udp_key_output = f"{a['udp']}.{out_idx}"
                    udp_key_base = f"{a['udp']}"
                    if udp_key_stream in params:
                        params[udp_key_specific] = params[udp_key_stream]
                    elif udp_key_output in params:
                        params[udp_key_specific] = params[udp_key_output]
                    elif udp_key_base in params:
                        params[udp_key_specific] = audio_udp_flat
                    else:
                        params[udp_key_specific] = audio_udp_flat

                # UDP SRC (6553)
                src_udp_key_specific = f"{a['src_udp']}.{out_idx}.{stream_idx}.{trunk}"
                if src_udp_key_specific not in params:
                    src_udp_key_stream = f"{a['src_udp']}.{out_idx}.{stream_idx}"
                    src_udp_key_output = f"{a['src_udp']}.{out_idx}"
                    src_udp_key_base = f"{a['src_udp']}"
                    if src_udp_key_stream in params:
                        params[src_udp_key_specific] = params[src_udp_key_stream]
                    elif src_udp_key_output in params:
                        params[src_udp_key_specific] = params[src_udp_key_output]
                    elif src_udp_key_base in params:
                        params[src_udp_key_specific] = audio_src_udp_flat
                    else:
                        params[src_udp_key_specific] = audio_src_udp_flat

                # ENABLE (6550)
                en_key_specific = f"{a['enable']}.{out_idx}.{stream_idx}.{trunk}"
                if en_key_specific not in params:
                    en_key_stream = f"{a['enable']}.{out_idx}.{stream_idx}"
                    en_key_output = f"{a['enable']}.{out_idx}"
                    en_key_base = f"{a['enable']}"
                    if en_key_stream in params:
                        params[en_key_specific] = params[en_key_stream]
                    elif en_key_output in params:
                        params[en_key_specific] = params[en_key_output]
                    elif en_key_base in params:
                        params[en_key_specific] = audio_enable_flat
                    else:
                        params[en_key_specific] = "1"

    return params


# ---------------------------
# Defaults class
# ---------------------------
class Defaults:
    """Connects to scorpion to set or read a list of defaults"""

    def _make_device_label(self) -> str:
        """
        Build label from config prefix + last octet of control IP, zero-padded.
        Example: SCORPION_RANGE_NAME_PFIX='SC_' and host '10.169.20.70' -> 'SC_070'
        """
        pfix = str(self.config.get("SCORPION_RANGE_NAME_PFIX", "SC_"))
        # derive last octet robustly
        try:
            n = int(str(self.host).strip().split(".")[-1])
        except Exception:
            try:
                n = int(self.last_octet)
            except Exception:
                n = 0
        return f"{pfix}{n:03d}"

    def __init__(self, name, host, port=80):
        """
        Args:
            name (str): NMOS name / alias used for the device
            host (str): control IP or hostname of the scorpion device (eg "10.169.20.51")
            port (int): control HTTP port (usually 80)
        """
        self.name = name
        self.host = host
        self.scorpion = Call(host=host, port=port)
        self.last_octet = host.split(".")[-1] if isinstance(host, str) and "." in host else host
        self.config = self._get_config()
        self.default_params: Optional[Dict[str, Any]] = None

    # ---- file helpers ----
    def _get_config(self) -> Dict[str, Any]:
        """Load config/config.json from repo root."""
        cfg_path = f"{ROOT_DIR}/config/config.json"
        try:
            with open(cfg_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _read_default_params(self) -> Dict[str, Any]:
        dp_path = f"{ROOT_DIR}/config/default_params.json"
        try:
            with open(dp_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    # ---- small utils ----
    def _split_dict(self, dict_, dict_size):
        """Split a dict into a list of smaller dicts each of size dict_size."""
        items = list(dict_.items())
        dicts = [dict(items[i : i + dict_size]) for i in range(0, len(items), dict_size)]
        return dicts

    def _send_params(self, params):
        """
        Send params to the scorpion device using POST requests.
        Splits the dict into chunks (size 10 by default).
        Returns (responses, fails) where responses is a list and fails is a list of items
        containing an 'error' key.
        """
        responses = []
        queries = self._split_dict(params, 10)
        for split_query in queries:
            try:
                response = self.scorpion.post(query=split_query)
            except RequestException as exc:
                return [], [{"error": str(exc)}]

            if isinstance(response, list):
                responses.extend(response)
            elif isinstance(response, dict):
                responses.append(response)
            else:
                responses.append(response)

        fails = [item for item in responses if isinstance(item, dict) and item.get("error")]
        return responses, fails

    # ---- defaults preparation ----
    def get_user_defaults(self) -> Dict[str, Any]:
        """
        Read config/default_params.json, inject dynamic values (names),
        and expand 2110 outputs (video/audio/meta).
        """
        defaults = self._read_default_params()
        if not defaults:
            raise RuntimeError("Failed to load default_params.json")

        # NMOS Name alias (original behaviour)
        label = self._make_device_label()
        defaults["55"] = label
        defaults["5204"] = label

        # NOTE: we no longer set 6000.* here (trunk IPs) — trunks are applied from config
        # via apply_trunks_from_config() to avoid conflicts with DHCP/Static toggle (6022.x).

        # Expand 2110 outputs for video/audio/meta (with audio streams)
        expanded = expand_2110_outputs(defaults, self.config, self.host, outputs=8)
        self.default_params = expanded
        return expanded

    # ---- apply groups ----
    def set_defaults(self, factory=False):
        """
        Legacy entry point: send prepared default parameters as one batch.
        (Kept for backward compatibility; prefer apply_all_defaults() in UI.)
        """
        if self.default_params is None:
            try:
                self.get_user_defaults()
            except Exception as exc:
                return f"Failed to prepare defaults: {exc}"

        responses, fails = self._send_params(self.default_params)
        if fails:
            return {"status": "partial_failure", "responses": responses, "fails": fails}
        return {"status": "success", "responses": responses}

    def set_default_routes(self, test: bool = False) -> Dict[str, Any]:
        """
        Clear route table entries (3009.0..31) and then set the project's default mapping.
        If test=True, only clear and set 16..23 to 31 (as per your one-off requirement).
        """
        # --- 1) Clear all 32 entries to 0 (disconnect) ---
        clear_routes = {f"3009.{i}": "0" for i in range(32)}
        responses, fails = self._send_params(clear_routes)
        if fails:
            return {"status": "failed_to_clear", "responses": responses, "fails": fails}

        if test:
            # Special block: set 16..23 to 31
            special = {f"3009.{dst}": "31" for dst in range(16, 24)}
            responses2, fails2 = self._send_params(special)
            ok = {"status": "cleared_and_set_16_23_to_31", "responses": responses2}
            if fails2:
                ok["fails"] = fails2
            return ok

        # --- 2) Apply your standard mapping ---
        # block A: 3009.4..11 => 17..24
        block_a = {f"3009.{dst}": str(src) for dst, src in zip(range(4, 12), range(17, 25))}
        # block B: 3009.16..23 => 5..12
        block_b = {f"3009.{dst}": str(src) for dst, src in zip(range(16, 24), range(5, 13))}
        routes = {}
        routes.update(block_a)
        routes.update(block_b)

        responses3, fails3 = self._send_params(routes)
        if fails3:
            return {"status": "failed_to_set_routes", "responses": responses3, "fails": fails3}

        return {"status": "routes_set", "responses": responses3}

    # ---- trunks (SCORPION_TRUNKS) ----
    def apply_trunks_from_config(self) -> Dict[str, Any]:
        """
        Uses config.json → SCORPION_TRUNKS to push:
          - DHCP toggle: 6022.0(A)/6022.1(B) where 1=DHCP, 0=Static
          - IP:          6000.0(A)/6000.1(B)
          - Netmask:     6001.0(A)/6001.1(B)
          - Gateway:     6002.0(A)/6002.1(B)
        """
        trunks = self.config.get("SCORPION_TRUNKS", {}) if isinstance(self.config.get("SCORPION_TRUNKS", {}), dict) else {}
        A = trunks.get("A", {}) if isinstance(trunks.get("A", {}), dict) else {}
        B = trunks.get("B", {}) if isinstance(trunks.get("B", {}), dict) else {}

        def one(side: Dict[str, Any], idx: int) -> Dict[str, str]:
            mode = str(side.get("mode", "Auto (DHCP)"))
            is_dhcp = 1 if mode.lower().startswith("auto") else 0  # IMPORTANT: 1=DHCP, 0=Static
            out = {f"6022.{idx}": str(is_dhcp)}
            if is_dhcp == 0:
                prefix = str(side.get("prefix", "10.20." if idx == 0 else "10.120."))
                suffix = str(side.get("suffix", "")).lstrip(".")  # e.g. "34.10"
                ip = f"{prefix}{suffix}" if suffix else ""
                mask = str(side.get("subnetMask", "255.255.255.252"))
                gw = str(side.get("gateway", ""))

                if ip:
                    out[f"6000.{idx}"] = ip
                if mask:
                    out[f"6001.{idx}"] = mask
                if gw:
                    out[f"6002.{idx}"] = gw
            return out

        params: Dict[str, str] = {}
        params.update(one(A, 0))  # A
        params.update(one(B, 1))  # B

        try:
            resp, fails = self._send_params(params)
            return {"applied": resp, "fails": fails}
        except Exception as exc:
            return {"error": str(exc)}

    # ---- helper to split ip-output family vs others ----
    @staticmethod
    def _is_ip_output_family_key(k: str) -> bool:
        try:
            root = int(str(k).split(".", 1)[0])
        except Exception:
            return False
        return (6500 <= root <= 6503) or (6550 <= root <= 6553) or (6600 <= root <= 6603)

    @staticmethod
    def _is_trunk_key(k: str) -> bool:
        # exclude trunk params when we apply trunks from config block
        try:
            root = int(str(k).split(".", 1)[0])
        except Exception:
            return False
        return root in (6000, 6001, 6002, 6022)

    # ---- new one-shot that the page will call ----
    def apply_all_defaults(self) -> Dict[str, Any]:
        """
        Safe 'apply all':
          1) Clear routes → mapping;
          2) Apply trunks (DHCP/Static + addressing) from config;
          3) Push 2110 IP/UDP/enable grid;
          4) Push remaining default_params.json keys (excluding trunk & 2110 families).
        """
        out: Dict[str, Any] = {}

        # 1) routes first
        try:
            out["routes"] = self.set_default_routes(test=False)
        except Exception as exc:
            out["routes"] = {"error": str(exc)}

        # 2) trunks from config
        out["trunks"] = self.apply_trunks_from_config()

        # 3 & 4) build from default_params.json (expanded) then split
        try:
            complete = self.get_user_defaults()  # includes expanded 2110 IP/UDP/enables
        except Exception as exc:
            out["defaults"] = {"error": f"prep_failed: {exc}"}
            return out

        ip_outputs = {k: v for k, v in complete.items() if self._is_ip_output_family_key(k)}
        other = {k: v for k, v in complete.items() if not self._is_ip_output_family_key(k) and not self._is_trunk_key(k)}

        # 3) apply 2110 family
        try:
            resp1, fails1 = self._send_params(ip_outputs) if ip_outputs else ([], [])
            out["ip_outputs"] = {"applied": resp1, "fails": fails1}
        except Exception as exc:
            out["ip_outputs"] = {"error": str(exc)}

        # 4) apply remaining defaults
        try:
            resp2, fails2 = self._send_params(other) if other else ([], [])
            out["default_params"] = {"applied": resp2, "fails": fails2} if other else {"info": "No additional defaults to apply."}
        except Exception as exc:
            out["default_params"] = {"error": str(exc)}

        return out

    # ---- debug/readback ----
    def get_current(self):
        """Returns a dictionary of lists for current status of all default values"""
        current = {"name": [], "code": [], "value": [], "default": []}

        if self.default_params is None:
            try:
                self.get_user_defaults()
            except Exception as exc:
                return {"error": f"Could not load defaults: {exc}"}

        for key, default_value in self.default_params.items():
            try:
                call = self.scorpion.get(key)
            except RequestException as exc:
                return {"error": f"Scorpion API Call Failed: {exc}"}

            name = call.get("name") if isinstance(call, dict) else None
            code = call.get("id") if isinstance(call, dict) else key
            value = call.get("value") if isinstance(call, dict) else default_value

            current["name"].append(name)
            current["code"].append(code)
            current["value"].append(value)
            current["default"].append(default_value)

        return current