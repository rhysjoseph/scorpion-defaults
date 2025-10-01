# src/main_tabs/scorpions.py
from __future__ import annotations

from typing import Dict, Any, List, Tuple

import os
import json
import socket
import subprocess
import shlex
import streamlit as st

# Robust import of Scorpion defaults; keep working UI if it fails
try:
    from src.scorpion.default import Defaults as ScorpionDefaults
    _IMPORT_ERROR = None
except Exception as e:  # keep the exception for display
    ScorpionDefaults = None
    _IMPORT_ERROR = e

# ----- Robust repo paths -----
_THIS_DIR = os.path.dirname(os.path.realpath(__file__))               # /app/src/main_tabs
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))     # /app
_CONFIG_CANDIDATES = [
    os.path.join(_REPO_ROOT, "config", "config.json"),                # /app/config/config.json
    "/app/config/config.json",                                        # explicit in-container default
    os.path.abspath(os.path.join(_THIS_DIR, "..", "config", "config.json")),
]


def _load_config() -> Dict[str, Any]:
    """Load config.json from the first existing candidate path; return {} if not found."""
    for p in _CONFIG_CANDIDATES:
        try:
            if os.path.isfile(p):
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Failed reading config at {p}: {e}")
    st.error(
        "config.json not found at any known location.\n"
        + "\n".join(f"• {p}" for p in _CONFIG_CANDIDATES)
    )
    return {}


def _parse_targets(s: str) -> List[str]:
    # Accept comma, space or newline-separated
    raw = [x.strip() for x in s.replace(",", " ").split()]
    return [x for x in raw if x]


def _build_trunk_params(cfg: Dict[str, Any]) -> Dict[str, str]:
    """
    Build parameter map for trunk A/B using your var IDs:
      - DHCP toggle: 6022.0 (A), 6022.1 (B) where 1=DHCP, 0=Static
      - IP:          6000.0 (A), 6000.1 (B)
      - Netmask:     6001.0 (A), 6001.1 (B)
      - Gateway:     6002.0 (A), 6002.1 (B)
    Values come from config.json → SCORPION_TRUNKS.
    """
    trunks = cfg.get("SCORPION_TRUNKS", {}) if isinstance(cfg.get("SCORPION_TRUNKS", {}), dict) else {}
    A = trunks.get("A", {}) if isinstance(trunks.get("A", {}), dict) else {}
    B = trunks.get("B", {}) if isinstance(trunks.get("B", {}), dict) else {}

    def one(side: Dict[str, Any], idx: int) -> Dict[str, str]:
        mode = str(side.get("mode", "Auto (DHCP)"))
        # IMPORTANT: 6022.x => 1 = DHCP, 0 = Static
        is_dhcp = 1 if mode.lower().startswith("auto") else 0
        out = {f"6022.{idx}": str(is_dhcp)}

        if is_dhcp == 0:
            # Build IP from prefix + suffix when Static
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

    params = {}
    params.update(one(A, 0))  # Trunk A
    params.update(one(B, 1))  # Trunk B
    return params


def _call_optional_defaults_apply(d: ScorpionDefaults) -> Tuple[str, Any]:
    """
    Preferred: apply_all_defaults()
    Fallbacks: apply_defaults(), apply_all(), apply_default_params()
    """
    for method in ("apply_all_defaults", "apply_defaults", "apply_all", "apply_default_params"):
        if hasattr(d, method) and callable(getattr(d, method)):
            try:
                res = getattr(d, method)()
                return (method, res)
            except Exception as exc:
                return (method, {"error": str(exc)})
    return ("none", {"info": "No default-apply method found; only routes/trunks were applied."})


def _build_option_labels(scorpions: List[str] | Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    """
    Returns (labels, label->ip) for the multiselect.
    - If dict: show 'name — ip'
    - If list/tuple: show just the ip
    """
    labels: List[str] = []
    label_to_ip: Dict[str, str] = {}

    if isinstance(scorpions, dict):
        for name, ip in scorpions.items():
            if not ip:
                continue
            label = f"{name} — {ip}"
            labels.append(label)
            label_to_ip[label] = str(ip)
    elif isinstance(scorpions, (list, tuple)):
        for ip in scorpions:
            if not ip:
                continue
            label = str(ip)
            labels.append(label)
            label_to_ip[label] = str(ip)

    # de-duplicate while preserving order
    seen = set()
    uniq_labels: List[str] = []
    uniq_map: Dict[str, str] = {}
    for lab in labels:
        if lab in seen:
            continue
        seen.add(lab)
        uniq_labels.append(lab)
        uniq_map[lab] = label_to_ip[lab]

    return uniq_labels, uniq_map


def _make_url(ip: str, port: int) -> str:
    return f"http://{ip}" if int(port) == 80 else f"http://{ip}:{int(port)}"


def _ping_host(ip: str, control_port: int = 80, timeout: float = 1.0) -> Tuple[bool, str]:
    """
    Try ICMP ping (-c 1 -W 1). If ping is unavailable or fails, fall back to TCP connect
    to control_port. Returns (is_up, method_used).
    """
    # Attempt ICMP ping if available
    try:
        cmd = f"ping -c 1 -W 1 {shlex.quote(ip)}"
        rc = subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc == 0:
            return True, "icmp"
    except Exception:
        pass

    # Fallback: TCP to control port
    try:
        with socket.create_connection((ip, int(control_port)), timeout=timeout):
            return True, f"tcp:{control_port}"
    except Exception:
        return False, "unreachable"


def tab(scorpions: List[str] | Dict[str, str], control_port: int = 80):
    st.header("Scorpion Devices")

    config = _load_config()

    if ScorpionDefaults is None:
        st.warning(f"Scorpion defaults module not available: {_IMPORT_ERROR}")

    # ---- Device selection (dropdown-style, like XIP page) ----
    labels, label_to_ip = _build_option_labels(scorpions)

    colsel1, colsel2 = st.columns([2, 1])
    with colsel1:
        selected_labels = st.multiselect(
            "Select Scorpion devices",
            options=labels,
            default=[],
            help="Choose from discovered/known devices",
        )
    with colsel2:
        select_all = st.checkbox("Select all listed", value=False, key="scorp_select_all")
        if select_all:
            selected_labels = labels

    manual_extra = st.text_input(
        "Add extra IPs (optional)",
        value="",
        help="Comma, space, or newline separated. Example: 10.169.20.51 10.169.20.52",
    )
    manual_ips = _parse_targets(manual_extra)

    # Final target list (sorted for stability, de-duplicated)
    selected_ips = [label_to_ip[l] for l in selected_labels if l in label_to_ip]
    targets = list(dict.fromkeys(selected_ips + manual_ips))  # dedupe preserve order

    st.caption(f"Selected targets: {', '.join(targets) if targets else '(none)'}")

    # ---- Quick actions: Ping & Go To Control ----
    st.subheader("Quick actions")

    qa1, qa2 = st.columns([1, 2])

    with qa1:
        if st.button("Ping selected", disabled=not targets):
            results = {}
            for ip in targets:
                up, method = _ping_host(ip, control_port=control_port, timeout=1.0)
                results[ip] = {"up": up, "via": method}
            st.json(results)

    with qa2:
        if targets:
            st.caption("Open device control UIs:")
            # Show a link button per target
            for ip in targets:
                st.link_button(f"Go to {ip}", _make_url(ip, control_port), use_container_width=False)

    # ---- Show trunk config from file for visibility ----
    st.subheader("Trunk A/B configuration (from config.json → SCORPION_TRUNKS)")
    st.json(config.get("SCORPION_TRUNKS", {}))

    col1, col2, col3 = st.columns([1, 1, 1])
    import_ok = ScorpionDefaults is not None

    with col1:
        if st.button("Set Defaults (safe)", disabled=(not targets) or (not import_ok)):
            results = {}
            for ip in targets:
                d = ScorpionDefaults(name=f"SC@{ip}", host=ip, port=control_port)

                # Prefer the consolidated method if present (now implemented):
                if hasattr(d, "apply_all_defaults") and callable(getattr(d, "apply_all_defaults")):
                    try:
                        results[ip] = d.apply_all_defaults()
                    except Exception as exc:
                        results[ip] = {"error": str(exc)}
                else:
                    # Fallback: do the safe sequence manually (older builds)
                    try:
                        route_res = d.set_default_routes(test=False)
                    except Exception as exc:
                        route_res = {"error": f"routes: {exc}"}

                    trunk_params = _build_trunk_params(config)
                    try:
                        if hasattr(d, "_send_params") and callable(getattr(d, "_send_params")):
                            resp, fails = d._send_params(trunk_params)
                            trunk_apply = {"applied": resp, "fails": fails}
                        else:
                            trunk_apply = {"error": "Defaults._send_params not available"}
                    except Exception as exc:
                        trunk_apply = {"error": str(exc)}

                    method_used, def_res = _call_optional_defaults_apply(d)

                    results[ip] = {
                        "routes": route_res,
                        "trunks": trunk_apply,
                        "defaults_apply_method": method_used,
                        "defaults_apply_result": def_res,
                    }

            st.json(results)

    with col2:
        if st.button("Apply Trunk A/B to selected", disabled=(not targets) or (not import_ok)):
            results = {}
            params = _build_trunk_params(config)
            for ip in targets:
                d = ScorpionDefaults(name=f"SC@{ip}", host=ip, port=control_port)
                if hasattr(d, "_send_params") and callable(getattr(d, "_send_params")):
                    try:
                        resp, fails = d._send_params(params)
                        results[ip] = {"applied": resp, "fails": fails}
                    except Exception as exc:
                        results[ip] = {"error": str(exc)}
                else:
                    results[ip] = {"error": "Defaults._send_params not available"}
            st.json(results)

    with col3:
        if st.button("Set Routes 1:1 (safe)", disabled=(not targets) or (not import_ok)):
            results = {}
            for ip in targets:
                d = ScorpionDefaults(name=f"SC@{ip}", host=ip, port=control_port)
                res = d.set_default_routes(test=False)
                results[ip] = res
            st.json(results)

    st.caption("Tip: use the Config Manager page to edit SCORPION_TRUNKS prefixes/suffixes and save first.")