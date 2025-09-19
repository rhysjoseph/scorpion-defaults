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
def expand_2110_outputs(default_params: dict, config: dict, device_ip: str, outputs: int = 8):
    """
    Expand default_params to include per-output/trunk entries for 2110 video/audio/meta.

    VIDEO/META:
      IP format:   <param>.<out>.<trunk>      (6501 / 6601)
      UDP format:  <param>.<out>.<trunk>      (6502/6503, 6602/6603)  <-- now explicit

    AUDIO:
      IP format:   <param>.<out>.<stream>.<trunk>  (6551)
      UDP format:  <param>.<out>.<stream>.<trunk>  (6552/6553)        (flat ports)

    Precedence (most specific → least) always applies:
      fully-qualified key → less-qualified key → base key → generated value
    """
    from copy import deepcopy

    def parse_range_string(r):
        if r is None: return []
        if isinstance(r, (list, tuple)): return list(r)
        s = str(r).strip()
        if '-' in s:
            a, b = s.split('-', 1)
            return list(range(int(a), int(b) + 1))
        if ',' in s:
            return [int(x.strip()) for x in s.split(',') if x.strip()]
        return [int(s)]

    def _ensure_dot_suffix(s):
        s = str(s)
        return s if s.endswith('.') else s + '.'

    params = deepcopy(default_params or {})
    last_octet = str(device_ip).strip().split('.')[-1]

    # Config
    audio_streams = int(config.get('2110_AUDIO_STREAMS', 4))
    if audio_streams < 1:
        audio_streams = 1

    media_map = {
        'video': {
            'enable': '6500', 'ip': '6501', 'udp': '6502', 'src_udp': '6503',
            'range_key': '2110_VIDEO_RANGE', 'flat_udp': '50100'
        },
        'audio': {
            'enable': '6550', 'ip': '6551', 'udp': '6552', 'src_udp': '6553',
            'range_key': '2110_AUDIO_RANGE', 'flat_udp': '50200'
        },
        'meta': {
            'enable': '6600', 'ip': '6601', 'udp': '6602', 'src_udp': '6603',
            'range_key': '2110_META_RANGE', 'flat_udp': '50300'
        }
    }

    red_prefix = _ensure_dot_suffix(config.get('2110_Red', '232.20.'))
    blue_prefix = _ensure_dot_suffix(config.get('2110_Blue', '232.120.'))

    # Ensure base defaults exist (flat UDPs come from base, but we will also write specifics)
    for m in media_map.values():
        params.setdefault(m['enable'], 1)
        params.setdefault(m['udp'], m['flat_udp'])
        params.setdefault(m['src_udp'], m['flat_udp'])

    # Parse ranges
    video_rng = parse_range_string(config.get(media_map['video']['range_key'], '1-8'))
    meta_rng  = parse_range_string(config.get(media_map['meta']['range_key'],  '1-8'))
    audio_rng = parse_range_string(config.get(media_map['audio']['range_key'], '1-8'))

    # Pad video/meta ranges to outputs if needed (repeat last)
    if len(video_rng) < outputs:
        base = video_rng or [1]
        video_rng = base + [base[-1]] * (outputs - len(base))
    if len(meta_rng) < outputs:
        base = meta_rng or [1]
        meta_rng  = base + [base[-1]] * (outputs - len(base))

    # AUDIO: linear suffix across ALL outputs/streams (avoid duplication)
    audio_start = audio_rng[0] if audio_rng else 201

    # -------- VIDEO (per-output, per-trunk) --------
    v = media_map['video']
    video_udp_flat     = str(params.get(v['udp'], v['flat_udp']))
    video_src_udp_flat = str(params.get(v['src_udp'], v['flat_udp']))

    for out_idx in range(outputs):
        suffix_value = video_rng[out_idx]
        for trunk in (0, 1):
            # IP (6501)
            ip_key_specific = f"{v['ip']}.{out_idx}.{trunk}"
            if ip_key_specific not in params:
                ip_key_output = f"{v['ip']}.{out_idx}"
                ip_key_base   = f"{v['ip']}"
                if ip_key_output in params:
                    params[ip_key_specific] = params[ip_key_output]
                elif ip_key_base in params:
                    params[ip_key_specific] = params[ip_key_base]
                else:
                    prefix = red_prefix if trunk == 0 else blue_prefix
                    params[ip_key_specific] = f"{prefix}{last_octet}.{suffix_value}"

            # UDP DEST (6502) explicit
            udp_key_specific = f"{v['udp']}.{out_idx}.{trunk}"
            if udp_key_specific not in params:
                udp_key_output = f"{v['udp']}.{out_idx}"
                udp_key_base   = f"{v['udp']}"
                if udp_key_output in params:
                    params[udp_key_specific] = params[udp_key_output]
                elif udp_key_base in params:
                    params[udp_key_specific] = video_udp_flat
                else:
                    params[udp_key_specific] = video_udp_flat

            # UDP SRC (6503) explicit
            src_udp_key_specific = f"{v['src_udp']}.{out_idx}.{trunk}"
            if src_udp_key_specific not in params:
                src_udp_key_output = f"{v['src_udp']}.{out_idx}"
                src_udp_key_base   = f"{v['src_udp']}"
                if src_udp_key_output in params:
                    params[src_udp_key_specific] = params[src_udp_key_output]
                elif src_udp_key_base in params:
                    params[src_udp_key_specific] = video_src_udp_flat
                else:
                    params[src_udp_key_specific] = video_src_udp_flat

    # -------- META (per-output, per-trunk) --------
    m = media_map['meta']
    meta_udp_flat     = str(params.get(m['udp'], m['flat_udp']))
    meta_src_udp_flat = str(params.get(m['src_udp'], m['flat_udp']))

    for out_idx in range(outputs):
        suffix_value = meta_rng[out_idx]
        for trunk in (0, 1):
            # IP (6601)
            ip_key_specific = f"{m['ip']}.{out_idx}.{trunk}"
            if ip_key_specific not in params:
                ip_key_output = f"{m['ip']}.{out_idx}"
                ip_key_base   = f"{m['ip']}"
                if ip_key_output in params:
                    params[ip_key_specific] = params[ip_key_output]
                elif ip_key_base in params:
                    params[ip_key_specific] = params[ip_key_base]
                else:
                    prefix = red_prefix if trunk == 0 else blue_prefix
                    params[ip_key_specific] = f"{prefix}{last_octet}.{suffix_value}"

            # UDP DEST (6602) explicit
            udp_key_specific = f"{m['udp']}.{out_idx}.{trunk}"
            if udp_key_specific not in params:
                udp_key_output = f"{m['udp']}.{out_idx}"
                udp_key_base   = f"{m['udp']}"
                if udp_key_output in params:
                    params[udp_key_specific] = params[udp_key_output]
                elif udp_key_base in params:
                    params[udp_key_specific] = meta_udp_flat
                else:
                    params[udp_key_specific] = meta_udp_flat

            # UDP SRC (6603) explicit
            src_udp_key_specific = f"{m['src_udp']}.{out_idx}.{trunk}"
            if src_udp_key_specific not in params:
                src_udp_key_output = f"{m['src_udp']}.{out_idx}"
                src_udp_key_base   = f"{m['src_udp']}"
                if src_udp_key_output in params:
                    params[src_udp_key_specific] = params[src_udp_key_output]
                elif src_udp_key_base in params:
                    params[src_udp_key_specific] = meta_src_udp_flat
                else:
                    params[src_udp_key_specific] = meta_src_udp_flat

    # -------- AUDIO (per-output, per-stream, per-trunk) --------
    a = media_map['audio']
    audio_udp_flat     = str(params.get(a['udp'], a['flat_udp']))
    audio_src_udp_flat = str(params.get(a['src_udp'], a['flat_udp']))

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
                    ip_key_base   = f"{a['ip']}"
                    if ip_key_stream in params:
                        params[ip_key_specific] = params[ip_key_stream]
                    elif ip_key_output in params:
                        params[ip_key_specific] = params[ip_key_output]
                    elif ip_key_base in params:
                        params[ip_key_specific] = params[ip_key_base]
                    else:
                        prefix = red_prefix if trunk == 0 else blue_prefix
                        params[ip_key_specific] = f"{prefix}{last_octet}.{ip_suffix_value}"

                # UDP DEST (6552) flat, explicit
                udp_key_specific = f"{a['udp']}.{out_idx}.{stream_idx}.{trunk}"
                if udp_key_specific not in params:
                    udp_key_stream = f"{a['udp']}.{out_idx}.{stream_idx}"
                    udp_key_output = f"{a['udp']}.{out_idx}"
                    udp_key_base   = f"{a['udp']}"
                    if udp_key_stream in params:
                        params[udp_key_specific] = params[udp_key_stream]
                    elif udp_key_output in params:
                        params[udp_key_specific] = params[udp_key_output]
                    elif udp_key_base in params:
                        params[udp_key_specific] = audio_udp_flat
                    else:
                        params[udp_key_specific] = audio_udp_flat

                # UDP SRC (6553) flat, explicit
                src_udp_key_specific = f"{a['src_udp']}.{out_idx}.{stream_idx}.{trunk}"
                if src_udp_key_specific not in params:
                    src_udp_key_stream = f"{a['src_udp']}.{out_idx}.{stream_idx}"
                    src_udp_key_output = f"{a['src_udp']}.{out_idx}"
                    src_udp_key_base   = f"{a['src_udp']}"
                    if src_udp_key_stream in params:
                        params[src_udp_key_specific] = params[src_udp_key_stream]
                    elif src_udp_key_output in params:
                        params[src_udp_key_specific] = params[src_udp_key_output]
                    elif src_udp_key_base in params:
                        params[src_udp_key_specific] = audio_src_udp_flat
                    else:
                        params[src_udp_key_specific] = audio_src_udp_flat

    return params

# ---------------------------
# Defaults class
# ---------------------------
class Defaults:
    """Connects to scorpion to set or read a list of defaults"""

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
        self.default_params = None

    def _get_config(self):
        """Load config/config.json from repo root."""
        cfg_path = f"{ROOT_DIR}/config/config.json"
        try:
            with open(cfg_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _split_dict(self, dict_, dict_size):
        """Split a dict into a list of smaller dicts each of size dict_size."""
        items = list(dict_.items())
        dicts = [
            dict(items[i : i + dict_size]) for i in range(0, len(items), dict_size)
        ]
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

    def get_user_defaults(self):
        """Gets parameters from config/default_params.json and prepares final defaults
           including the 2110 expansion.
        Returns:
            dict: The default parameters (expanded)
        """
        dp_path = f"{ROOT_DIR}/config/default_params.json"
        try:
            with open(dp_path, encoding="utf-8") as f:
                defaults = json.load(f)
        except Exception as exc:
            raise RuntimeError(f"Failed to load default_params.json: {exc}")

        # Set NMOS Name to alias / remove rack number (original behaviour)
        defaults["55"] = self.name
        defaults["5204"] = self.name

        # Set unit number as last octet of trunks if present in config
        trunk_a = self.config.get("TRUNK_A_PREFIX", None)
        trunk_b = self.config.get("TRUNK_B_PREFIX", None)
        if trunk_a:
            defaults["6000.0"] = f"{trunk_a}.{self.last_octet}"
        if trunk_b:
            defaults["6000.1"] = f"{trunk_b}.{self.last_octet}"

        # --- Expand 2110 outputs for video/audio/meta (with audio streams) ---
        defaults = expand_2110_outputs(defaults, self.config, self.host, outputs=8)

        self.default_params = defaults
        return defaults

    def set_defaults(self, factory=False):
        """
        Send the prepared default parameters to the Scorpion device.
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

    def set_default_routes(self, test: bool = False):
        """
        Clear route table entries (3009.x) and then set the required mapping.

        When test=True:
            - After clearing, set 3009.16..3009.24 to 31 (inclusive), then return.

        When test=False (normal):
            - Set:
                3009.4  -> 17
                3009.5  -> 18
                3009.6  -> 19
                3009.7  -> 20
                3009.8  -> 21
                3009.9  -> 22
                3009.10 -> 23
                3009.11 -> 24

                3009.16 -> 5
                3009.17 -> 6
                3009.18 -> 7
                3009.19 -> 8
                3009.20 -> 9
                3009.21 -> 10
                3009.22 -> 11
                3009.23 -> 12
        """
        # 1) Clear all 32 entries to "0"
        clear_routes = {f"3009.{i}": "0" for i in range(32)}
        responses, fails = self._send_params(clear_routes)
        if fails:
            return {"status": "failed_to_clear", "responses": responses, "fails": fails}

        # 2) Test mode: set 3009.16..3009.24 to "31"
        if test:
            test_routes = {f"3009.{i}": "31" for i in range(16, 25)}  # inclusive 24
            responses, fails = self._send_params(test_routes)
            if fails:
                return {"status": "failed_to_set_test_routes", "responses": responses, "fails": fails}
            return {"status": "test_routes_set", "responses": responses}

        # 3) Normal mapping
        block_a = {f"3009.{dst}": str(src) for dst, src in zip(range(4, 12), range(17, 25))}
        block_b = {f"3009.{dst}": str(src) for dst, src in zip(range(16, 24), range(5, 13))}
        routes = {**block_a, **block_b}

        responses, fails = self._send_params(routes)
        if fails:
            return {"status": "failed_to_set_routes", "responses": responses, "fails": fails}

        return {"status": "success", "responses": responses}

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