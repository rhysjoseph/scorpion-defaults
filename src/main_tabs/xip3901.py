# src/main_tabs/xip3901.py
from __future__ import annotations

from typing import Dict, Any, List, Tuple

import os
import json
import socket
import subprocess
import shlex
import streamlit as st
import base64

from src.utils import ping as ping_host

# --- Ping UI helpers (use utils.ping for reachability) ---
_PONG_ICON_CANDIDATES = [
    "assets/pong.png",
    "src/assets/pong.png",
    "assets/icons/pong.png",
    "src/static/pong.png",
    "/app/src/assets/pong.png",
]
_FAIL_MP3_CANDIDATES = [
    "assets/cartoon-fail-trumpet-278822.mp3",
    "src/assets/cartoon-fail-trumpet-278822.mp3",
    "/app/src/assets/cartoon-fail-trumpet-278822.mp3",
]

def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def _autoplay_audio(file_path: str):
    try:
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        # Hidden, autoplaying audio element
        st.markdown(
            f"""
            <audio autoplay>
              <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
            </audio>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        # Fallback (just in case): visible player
        st.audio(file_path, format="audio/mp3")

def _show_ping_ok(ip: str):
    c1, c2 = st.columns([1, 5])
    with c1:
        icon = _first_existing(_PONG_ICON_CANDIDATES)
        if icon:
            st.image(icon, use_container_width=True)
        else:
            st.markdown("### ✅")
    with c2:
        st.markdown(f"**PONG** — {ip}")

def _show_ping_fail(ip: str):
    c1, c2 = st.columns([1, 5])
    with c1:
        st.markdown("### ❌")
    with c2:
        st.error(f"WA WA — {ip} unreachable")
        mp3 = _first_existing(_FAIL_MP3_CANDIDATES)
        if mp3:
            _autoplay_audio(mp3)  # <-- autoplay immediately

try:
    from src.xip3901.default import Defaults as XipDefaults
    _IMPORT_ERROR = None
except Exception as e:
    XipDefaults = None
    _IMPORT_ERROR = e

_THIS_DIR = os.path.dirname(os.path.realpath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_CONFIG_CANDIDATES = [
    os.path.join(_REPO_ROOT, "config", "config.json"),
    "/app/config/config.json",
    os.path.abspath(os.path.join(_THIS_DIR, "..", "config", "config.json")),
]


def _load_config() -> Dict[str, Any]:
    for p in _CONFIG_CANDIDATES:
        try:
            if os.path.isfile(p):
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Failed reading config at {p}: {e}")
    st.error("config.json not found.\n" + "\n".join(f"• {p}" for p in _CONFIG_CANDIDATES))
    return {}


def _build_option_labels(xips: List[str] | Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    labels: List[str] = []
    label_to_ip: Dict[str, str] = {}
    if isinstance(xips, dict):
        for name, ip in xips.items():
            if not ip:
                continue
            lab = f"{name} — {ip}"
            labels.append(lab)
            label_to_ip[lab] = str(ip)
    else:
        for ip in xips or []:
            lab = str(ip)
            labels.append(lab)
            label_to_ip[lab] = str(ip)

    # de-dup while preserving order
    seen = set()
    uniq_labels, uniq_map = [], {}
    for lab in labels:
        if lab in seen:
            continue
        seen.add(lab)
        uniq_labels.append(lab)
        uniq_map[lab] = label_to_ip[lab]
    return uniq_labels, uniq_map


def _parse_targets(s: str) -> List[str]:
    raw = [x.strip() for x in (s or "").replace(",", " ").split()]
    return [x for x in raw if x]


def _make_url(ip: str, port: int) -> str:
    return f"http://{ip}" if int(port) == 80 else f"http://{ip}:{int(port)}"


def _ping_host(ip: str, control_port: int = 80, timeout: float = 2.0):
    try:
        cmd = f"ping -c 1 -W 1 {shlex.quote(ip)}"
        rc = subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc == 0:
            return True, "icmp"
    except Exception:
        pass
    try:
        with socket.create_connection((ip, int(control_port)), timeout=timeout):
            return True, f"tcp:{control_port}"
    except Exception:
        return False, "unreachable"


def tab(xips: List[str] | Dict[str, str], control_port: int = 80):
    st.header("XIP3901 / XIP3911 Devices")

    if XipDefaults is None:
        st.error(f"Failed to import XIP defaults module: {_IMPORT_ERROR}")
        return

    _ = _load_config()

    labels, label_to_ip = _build_option_labels(xips)

    colsel1, colsel2 = st.columns([2, 1])
    with colsel1:
        selected_labels = st.multiselect(
            "Select XIP devices",
            options=labels,
            default=[],
            help="Choose from discovered/known devices",
            key="xip_select_devices",
        )
    with colsel2:
        select_all = st.checkbox("Select all listed", value=False, key="xip_select_all")
        if select_all:
            selected_labels = labels

    manual_extra = st.text_input(
        "Add extra IPs (optional)",
        value="",
        help="Comma, space, or newline separated. Example: 10.169.60.1 10.169.60.2",
        key="xip_manual_ips",
    )

    selected_ips = [label_to_ip[l] for l in selected_labels if l in label_to_ip]
    targets = list(dict.fromkeys(selected_ips + _parse_targets(manual_extra)))
    st.caption(f"Selected targets: {', '.join(targets) if targets else '(none)'}")

    # Quick actions
    st.subheader("Quick actions")
    qa1, qa2 = st.columns([1, 2])
    with qa1:
        if st.button("Ping selected", disabled=not targets, key="sc_ping"):
            st.subheader("Ping results")
            for ip in targets:
                if ping_host(ip):
                    _show_ping_ok(ip)
                else:
                    _show_ping_fail(ip)
    with qa2:
        if targets:
            st.caption("Open device control UIs:")
            for ip in targets:
                # NOTE: Streamlit version here does not support `key` for link_button.
                st.link_button(f"Go to {ip}", _make_url(ip, control_port), use_container_width=False)

    st.divider()

    # Preview (optional)
    with st.expander("Preview multicast & UDP plan (optional)", expanded=False):
        if not targets:
            st.info("Select at least one XIP to preview.")
        else:
            previews = {}
            for ip in targets:
                d = XipDefaults(name=f"XIP@{ip}", host=ip, port=control_port)
                try:
                    previews[ip] = d.preview_summary()
                except Exception as exc:
                    previews[ip] = {"error": f"preview failed: {exc}"}
            st.json(previews)

    st.divider()

    # Apply actions (multi-target)
    row1 = st.columns([1, 1, 1, 1, 1])
    with row1[0]:
        if st.button("Apply ALL defaults (safe sequence)", disabled=not targets, key="xip_apply_all"):
            results = {}
            for ip in targets:
                d = XipDefaults(name=f"XIP@{ip}", host=ip, port=control_port)
                try:
                    if hasattr(d, "apply_all_defaults"):
                        results[ip] = d.apply_all_defaults()
                    else:
                        results[ip] = {
                            "hostname": d.apply_network_and_hostname(),
                            "interfaces": d.apply_interfaces(),
                            "nmos_ptp": d.apply_nmos_and_ptp(),
                            "senders": d.apply_senders(),
                            "advanced_qos": d.apply_advanced_qos(),
                        }
                except Exception as exc:
                    results[ip] = {"error": str(exc)}
            st.json(results)
    
    with row1[1]:
        if st.button("Apply Interfaces + Hostname", disabled=not targets, key="xip_apply_if_host"):
            results = {}
            for ip in targets:
                d = XipDefaults(name=f"XIP@{ip}", host=ip, port=control_port)
                try:
                    res = d.apply_network_and_hostname()
                    res["interfaces"] = d.apply_interfaces()
                    results[ip] = res
                except Exception as exc:
                    results[ip] = {"error": str(exc)}
            st.json(results)

    with row1[2]:
        if st.button("Apply NMOS + PTP", disabled=not targets, key="xip_apply_nmos_ptp"):
            results = {}
            for ip in targets:
                d = XipDefaults(name=f"XIP@{ip}", host=ip, port=control_port)
                try:
                    results[ip] = d.apply_nmos_and_ptp()
                except Exception as exc:
                    results[ip] = {"error": str(exc)}
            st.json(results)

    with row1[3]:
        if st.button("Apply 2110 Senders", disabled=not targets, key="xip_apply_senders"):
            results = {}
            for ip in targets:
                d = XipDefaults(name=f"XIP@{ip}", host=ip, port=control_port)
                try:
                    results[ip] = d.apply_senders()
                except Exception as exc:
                    results[ip] = {"error": str(exc)}
            st.json(results)

    with row1[4]:
        if st.button("Apply Advanced QoS", disabled=not targets, key="xip_apply_qos"):
            results = {}
            for ip in targets:
                d = XipDefaults(name=f"XIP@{ip}", host=ip, port=control_port)
                try:
                    results[ip] = d.apply_advanced_qos()
                except Exception as exc:
                    results[ip] = {"error": str(exc)}
            st.json(results)