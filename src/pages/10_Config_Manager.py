# src/pages/10_Config_Manager.py
from __future__ import annotations
import os
import json
import time
from typing import Any, Dict, Optional, List

import streamlit as st

# ---------- Resolve repo paths ----------
PAGES_DIR = os.path.dirname(os.path.realpath(__file__))                 # .../src/pages
SRC_DIR   = os.path.dirname(PAGES_DIR)                                  # .../src
ROOT_DIR  = os.path.dirname(SRC_DIR)                                    # repo root
CONF_DIR  = os.path.join(ROOT_DIR, "config")

CONFIG_JSON_PATH   = os.path.join(CONF_DIR, "config.json")
DEFAULTS_JSON_PATH = os.path.join(CONF_DIR, "default_params.json")
XIP_JSON_PATH      = os.path.join(CONF_DIR, "xip3901_parameters_reference.json")

# ---------- Small helpers ----------
def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        st.error(f"JSON decode error in {path}: {e}")
        return {}

def _write_json(path: str, data: Dict[str, Any], backup: bool = True) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if backup and os.path.exists(path):
            ts = time.strftime("%Y%m%d-%H%M%S")
            bak = f"{path}.{ts}.bak"
            with open(bak, "w", encoding="utf-8") as f:
                json.dump(_read_json(path), f, indent=2, ensure_ascii=False)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Failed to write {path}: {e}")
        return False

def _comma_int(s: str, default: int) -> int:
    try:
        return int(str(s).strip())
    except Exception:
        return default

def _range_str_ok(s: str) -> bool:
    """Validates simple 'A-B' range strings like '51-70' (both ints and A <= B)."""
    try:
        left, right = str(s).split("-", 1)
        a, b = int(left), int(right)
        return a <= b
    except Exception:
        return False

def _info_pair(label: str, desc: str):
    st.markdown(f"**{label}**")
    st.caption(desc)

# ---------- Enumerations ----------
NMOS_MODES = ["IS-04 & IS-05", "IS-04", "OFF"]
REGISTRY_MODES = ["Static", "Auto"]
PTP_ANNOUNCE_INTERVALS = ["0.125", "0.250", "0.500", "1", "2", "4", "8", "16"]
AUDIO_TYPES = ["SMPTE ST 2110-30", "SMPTE ST 2110-31"]

AUDIO_PROFILES_COMMON = [
    "125 usec, 1ch", "125 usec, 2ch", "125 usec, 4ch", "125 usec, 8ch", "125 usec, 16ch",
    "250 usec, 1ch", "250 usec, 2ch", "250 usec, 4ch", "250 usec, 8ch", "250 usec, 16ch",
    "1 msec, 1ch", "1 msec, 2ch", "1 msec, 4ch", "1 msec, 8ch",
]
AUDIO_PROFILES = AUDIO_PROFILES_COMMON + ["Custom…"]

IFACE_MODES = ["Auto (DHCP)", "Static", "Off"]  # For XIP interfaces (we expose eth1, eth2, frame)
SC_TRUNK_MODES = ["Auto (DHCP)", "Static"]      # For Scorpion trunk A/B

# ---------- UI ----------
st.title("Configuration Manager")
st.caption(
    "Edit the app configuration files directly from the UI. On save, a timestamped backup "
    "(.bak) is written next to the original file."
)

# Load all files once (we re-write on Save)
cfg_config    = _read_json(CONFIG_JSON_PATH)
cfg_defaults  = _read_json(DEFAULTS_JSON_PATH)            # Scorpion defaults (raw JSON editor)
cfg_xip       = _read_json(XIP_JSON_PATH)

with st.expander("Paths & files", expanded=False):
    st.code(f"config.json: {CONFIG_JSON_PATH}")
    st.code(f"default_params.json: {DEFAULTS_JSON_PATH}")
    st.code(f"xip3901_parameters_reference.json: {XIP_JSON_PATH}")

st.divider()

# =========================
# Section A: config.json
# =========================
st.header("A) config.json (global app & ranges)")
st.caption("General ranges, prefixes, and links used by the app and devices.")

config_work = dict(cfg_config) if isinstance(cfg_config, dict) else {}

st.subheader("Links (home screen buttons)")
_links = config_work.get("LINKS", {})
colA, colB, colC, colD = st.columns(4)
with colA:
    _info_pair("hi", "Main landing (used for NMOS registry HTTP address)")
    links_hi = st.text_input("hi", value=str(_links.get("hi", "")), label_visibility="collapsed")
with colB:
    _info_pair("Prism", "Tek/Bridge/Prism or monitoring UI")
    links_prism = st.text_input("Prism", value=str(_links.get("Prism", "")), label_visibility="collapsed")
with colC:
    _info_pair("CoreSwitch", "Core switch UI (optional)")
    links_core = st.text_input("CoreSwitch", value=str(_links.get("CoreSwitch", "")), label_visibility="collapsed")
with colD:
    _info_pair("EBUTech3371", "EBU Tech 3371 reference")
    links_ebu = st.text_input("EBUTech3371", value=str(_links.get("EBUTech3371", "")), label_visibility="collapsed")

st.subheader("ST 2110 multicast base prefixes (Scorpion & XIP)")
col1, col2 = st.columns(2)
with col1:
    _info_pair("2110_Red", "Primary/Trunk1 multicast prefix (e.g. '232.20.')")
    red = st.text_input("2110_Red", value=str(config_work.get("2110_Red", "")), label_visibility="collapsed")
with col2:
    _info_pair("2110_Blue", "Secondary/Trunk2 multicast prefix (e.g. '232.120.')")
    blue = st.text_input("2110_Blue", value=str(config_work.get("2110_Blue", "")), label_visibility="collapsed")

col3, col4, col5 = st.columns(3)
with col3:
    _info_pair("2110_VIDEO_RANGE", "Per-output last-octet range for **video** (e.g. '101-108')")
    v_rng = st.text_input("2110_VIDEO_RANGE", value=str(config_work.get("2110_VIDEO_RANGE", "")), label_visibility="collapsed")
with col4:
    _info_pair("2110_AUDIO_RANGE", "Starting last-octet for **audio** sequence (e.g. '201-232')")
    a_rng = st.text_input("2110_AUDIO_RANGE", value=str(config_work.get("2110_AUDIO_RANGE", "")), label_visibility="collapsed")
with col5:
    _info_pair("2110_META_RANGE", "Per-output last-octet range for **anc/meta** (e.g. '1-8')")
    m_rng = st.text_input("2110_META_RANGE", value=str(config_work.get("2110_META_RANGE", "")), label_visibility="collapsed")

# ---- Scorpion control addressing ----
st.subheader("Scorpion control addressing")
colS1, colS2, colS3 = st.columns(3)
with colS1:
    _info_pair("CONTROL_PREFIX", "Scorpion OOB control prefix (e.g. '10.169.20.')")
    sc_ctrl_prefix = st.text_input("CONTROL_PREFIX", value=str(config_work.get("CONTROL_PREFIX", "")), label_visibility="collapsed")
with colS2:
    _info_pair("SCORPION_RANGE", "Scorpion unit allocation range (e.g. '51-70')")
    sc_range = st.text_input("SCORPION_RANGE", value=str(config_work.get("SCORPION_RANGE", "")), label_visibility="collapsed")
with colS3:
    _info_pair("SCORPION_RANGE_NAME_PFIX", "Scorpion hostname prefix (e.g. 'SC_')")
    sc_name_pfix = st.text_input("SCORPION_RANGE_NAME_PFIX", value=str(config_work.get("SCORPION_RANGE_NAME_PFIX", "")), label_visibility="collapsed")

# ---- Scorpion trunk ports (A/B) ----
st.subheader("Scorpion 2110 trunk ports (A / B)")
st.caption("For Static, IP is PREFIX + SUFFIX (two octets). DHCP/Static maps to device params (remember: 6022.{0,1} is 1=DHCP, 0=Static).")

trunk = config_work.get("SCORPION_TRUNKS", {}) if isinstance(config_work.get("SCORPION_TRUNKS", {}), dict) else {}

def _trunk_defaults(side: str):
    return {
        "mode": "Auto (DHCP)",
        "prefix": "10.20." if side == "A" else "10.120.",
        "suffix": "",  # like "34.10"
        "subnetMask": "255.255.255.252",
        "gateway": ""
    }

tA = {**_trunk_defaults("A"), **(trunk.get("A", {}) if isinstance(trunk.get("A", {}), dict) else {})}
tB = {**_trunk_defaults("B"), **(trunk.get("B", {}) if isinstance(trunk.get("B", {}), dict) else {})}

cola, colb = st.columns(2)
with cola:
    st.markdown("**Trunk A**")
    ta_mode = st.selectbox("Mode (A)", SC_TRUNK_MODES, index=max(0, SC_TRUNK_MODES.index(tA.get("mode", "Auto (DHCP)"))))
    ta_prefix = st.text_input("TRUNK_A_PREFIX", value=str(tA.get("prefix", "10.20.")))
    ta_suffix = st.text_input("TRUNK_A_SUFFIX (last two octets, e.g. '34.10')", value=str(tA.get("suffix", "")))
    ta_mask   = st.text_input("TRUNK_A_NETMASK", value=str(tA.get("subnetMask", "255.255.255.252")))
    ta_gw     = st.text_input("TRUNK_A_GATEWAY", value=str(tA.get("gateway", "")))
with colb:
    st.markdown("**Trunk B**")
    tb_mode = st.selectbox("Mode (B)", SC_TRUNK_MODES, index=max(0, SC_TRUNK_MODES.index(tB.get("mode", "Auto (DHCP)"))))
    tb_prefix = st.text_input("TRUNK_B_PREFIX", value=str(tB.get("prefix", "10.120.")))
    tb_suffix = st.text_input("TRUNK_B_SUFFIX (last two octets, e.g. '34.11')", value=str(tB.get("suffix", "")))
    tb_mask   = st.text_input("TRUNK_B_NETMASK", value=str(tB.get("subnetMask", "255.255.255.252")))
    tb_gw     = st.text_input("TRUNK_B_GATEWAY", value=str(tB.get("gateway", "")))

# XIP3901 control addressing
st.subheader("XIP3901 control addressing")
col6, col7, col8, col9 = st.columns(4)
with col6:
    _info_pair("XIP3901_CONTROL_PREFIX", "Out-of-band control network (e.g. '10.169.60.')")
    xip_ctrl_pfx = st.text_input("XIP3901_CONTROL_PREFIX", value=str(config_work.get("XIP3901_CONTROL_PREFIX", "")), label_visibility="collapsed")
with col7:
    _info_pair("XIP3901_NETMASK", "Control subnet mask (e.g. '255.255.0.0')")
    xip_mask = st.text_input("XIP3901_NETMASK", value=str(config_work.get("XIP3901_NETMASK", "")), label_visibility="collapsed")
with col8:
    _info_pair("XIP3901_GATEWAY", "Control default gateway (e.g. '10.169.0.1')")
    xip_gw = st.text_input("XIP3901_GATEWAY", value=str(config_work.get("XIP3901_GATEWAY", "")), label_visibility="collapsed")
with col9:
    _info_pair("XIP3901_RANGE", "Unit allocation range (e.g. '1-40')")
    xip_range = st.text_input("XIP3901_RANGE", value=str(config_work.get("XIP3901_RANGE", "")), label_visibility="collapsed")

col10, col11 = st.columns(2)
with col10:
    _info_pair("XIP3901_RANGE_NAME_PFIX", "XIP hostname prefix (e.g. 'XIP3901-')")
    xip_name_pfix = st.text_input("XIP3901_RANGE_NAME_PFIX", value=str(config_work.get("XIP3901_RANGE_NAME_PFIX", "XIP3901-")), label_visibility="collapsed")
with col11:
    _info_pair("XIP3901_CONTROL_PORT", "XIP HTTP control port (default 80)")
    xip_port = st.number_input("XIP3901_CONTROL_PORT", value=_comma_int(config_work.get("XIP3901_CONTROL_PORT", 80), 80), step=1)

# ---- XIP3901 Interfaces editor (eth1, eth2, frame only) ----
st.subheader("XIP3901 network interfaces (eth1 / eth2 / frame)")
st.caption("eth3 (out-of-band control) is auto-derived from XIP3901_CONTROL_PREFIX + device last octet and cannot be edited here.")

def _iface_defaults(name: str):
    if name in ("eth1", "eth2"):
        return {"mode": "Auto (DHCP)", "ipAddress": "0.0.0.0", "subnetMask": "0.0.0.0", "gateway": "0.0.0.0"}
    # frame default Off
    return {"mode": "Off", "ipAddress": "0.0.0.0", "subnetMask": "0.0.0.0", "gateway": "0.0.0.0"}

xip_ifaces = config_work.get("XIP3901_INTERFACES", {})
if not isinstance(xip_ifaces, dict):
    xip_ifaces = {}

# Merge defaults for eth1/eth2/frame only
eth1_defaults = {**_iface_defaults("eth1"), **(xip_ifaces.get("eth1") or {})}
eth2_defaults = {**_iface_defaults("eth2"), **(xip_ifaces.get("eth2") or {})}
frm_defaults  = {**_iface_defaults("frame"), **(xip_ifaces.get("frame") or {})}

cols = st.columns(3)

with cols[0]:
    st.markdown("**eth1 (2110 primary)**")
    eth1_mode = st.selectbox("Mode (eth1)", IFACE_MODES, index=max(0, IFACE_MODES.index(eth1_defaults["mode"])))
    eth1_ip   = st.text_input("eth1 ipAddress", value=str(eth1_defaults["ipAddress"]))
    eth1_sm   = st.text_input("eth1 subnetMask", value=str(eth1_defaults["subnetMask"]))
    eth1_gw   = st.text_input("eth1 gateway", value=str(eth1_defaults["gateway"]))

with cols[1]:
    st.markdown("**eth2 (2110 secondary)**")
    eth2_mode = st.selectbox("Mode (eth2)", IFACE_MODES, index=max(0, IFACE_MODES.index(eth2_defaults["mode"])))
    eth2_ip   = st.text_input("eth2 ipAddress", value=str(eth2_defaults["ipAddress"]))
    eth2_sm   = st.text_input("eth2 subnetMask", value=str(eth2_defaults["subnetMask"]))
    eth2_gw   = st.text_input("eth2 gateway", value=str(eth2_defaults["gateway"]))

with cols[2]:
    st.markdown("**frame (backplane/management)**")
    frm_mode = st.selectbox("Mode (frame)", IFACE_MODES, index=max(0, IFACE_MODES.index(frm_defaults["mode"])))
    frm_ip   = st.text_input("frame ipAddress", value=str(frm_defaults["ipAddress"]))
    frm_sm   = st.text_input("frame subnetMask", value=str(frm_defaults["subnetMask"]))
    frm_gw   = st.text_input("frame gateway", value=str(frm_defaults["gateway"]))

# ---- Validation & Save (config.json) ----
config_errors: List[str] = []
if v_rng and not _range_str_ok(v_rng): config_errors.append("2110_VIDEO_RANGE must be like '101-108'.")
if a_rng and not _range_str_ok(a_rng): config_errors.append("2110_AUDIO_RANGE must be like '201-232'.")
if m_rng and not _range_str_ok(m_rng): config_errors.append("2110_META_RANGE must be like '1-8'.")
if xip_range and not _range_str_ok(xip_range): config_errors.append("XIP3901_RANGE must be like '1-40'.")
if sc_range and not _range_str_ok(sc_range): config_errors.append("SCORPION_RANGE must be like '51-70' (or similar 'A-B').")

if config_errors:
    st.warning(" • " + "\n • ".join(config_errors))

save_cfg = st.button("Save config.json", type="primary", disabled=bool(config_errors))
if save_cfg:
    config_work.setdefault("LINKS", {})
    config_work["LINKS"]["hi"] = links_hi
    config_work["LINKS"]["Prism"] = links_prism
    config_work["LINKS"]["CoreSwitch"] = links_core
    config_work["LINKS"]["EBUTech3371"] = links_ebu

    config_work["2110_Red"] = red
    config_work["2110_Blue"] = blue
    config_work["2110_VIDEO_RANGE"] = v_rng
    config_work["2110_AUDIO_RANGE"] = a_rng
    config_work["2110_META_RANGE"]  = m_rng

    # Scorpion fields
    config_work["CONTROL_PREFIX"] = sc_ctrl_prefix
    config_work["SCORPION_RANGE"] = sc_range
    config_work["SCORPION_RANGE_NAME_PFIX"] = sc_name_pfix

    # Scorpion trunks A/B (consumed by Scorpion defaults)
    config_work["SCORPION_TRUNKS"] = {
        "A": {
            "mode": ta_mode,
            "prefix": ta_prefix,
            "suffix": ta_suffix,        # e.g. "34.10"
            "subnetMask": ta_mask,
            "gateway": ta_gw,
        },
        "B": {
            "mode": tb_mode,
            "prefix": tb_prefix,
            "suffix": tb_suffix,        # e.g. "34.11"
            "subnetMask": tb_mask,
            "gateway": tb_gw,
        }
    }

    # XIP base fields
    config_work["XIP3901_CONTROL_PREFIX"] = xip_ctrl_pfx
    config_work["XIP3901_NETMASK"] = xip_mask
    config_work["XIP3901_GATEWAY"] = xip_gw
    config_work["XIP3901_RANGE"]   = xip_range
    config_work["XIP3901_RANGE_NAME_PFIX"] = xip_name_pfix
    config_work["XIP3901_CONTROL_PORT"]    = int(xip_port)

    # XIP interfaces — SAVE ONLY eth1, eth2, frame (eth3 is intentionally omitted/ignored)
    config_work["XIP3901_INTERFACES"] = {
        "eth1": {"mode": eth1_mode, "ipAddress": eth1_ip, "subnetMask": eth1_sm, "gateway": eth1_gw},
        "eth2": {"mode": eth2_mode, "ipAddress": eth2_ip, "subnetMask": eth2_sm, "gateway": eth2_gw},
        "frame": {"mode": frm_mode, "ipAddress": frm_ip, "subnetMask": frm_sm, "gateway": frm_gw},
    }

    if _write_json(CONFIG_JSON_PATH, config_work, backup=True):
        st.success("Saved config.json")

st.divider()

# =========================
# Section B: xip3901_parameters_reference.json
# =========================
st.header("B) xip3901_parameters_reference.json (XIP3901 defaults)")
st.caption("Strongly-typed editor for XIP3901 defaults (NMOS, PTP, Audio, UDP).")

xip_work = dict(cfg_xip) if isinstance(cfg_xip, dict) else {}
xip_defaults = xip_work.get("defaults", {}) if isinstance(xip_work.get("defaults", {}), dict) else {}

st.subheader("NMOS")
col1, col2 = st.columns(2)
with col1:
    _info_pair("Mode", "Global NMOS mode.")
    nm_mode = st.selectbox("NMOS Mode", NMOS_MODES,
                           index=max(0, NMOS_MODES.index(str(xip_defaults.get("nmos_mode", "IS-04 & IS-05")))))
with col2:
    _info_pair("Registry Mode", "NMOS registry discovery mode.")
    reg_mode = st.selectbox("Registry Mode", REGISTRY_MODES,
                            index=max(0, REGISTRY_MODES.index(str(xip_defaults.get("registry_mode", "Static")))))

col3, col4, col5 = st.columns(3)
with col3:
    _info_pair("Registry Port", "IS-04 registration port (e.g. 3020 or 30010).")
    reg_port = st.number_input("Registration Port", value=_comma_int(xip_defaults.get("registry_port", 3020), 3020), step=1, min_value=0, max_value=65535)
with col4:
    _info_pair("Query Port", "IS-04 query API port (e.g. 3021 or 30010).")
    qry_port = st.number_input("Query Port", value=_comma_int(xip_defaults.get("query_port", 3021), 3021), step=1, min_value=0, max_value=65535)
with col5:
    _info_pair("Label (auto)", "We set label to the hostname at apply-time; no input needed here.")
    st.text_input("Label (derived at apply)", value="hostname (derived)", disabled=True, label_visibility="collapsed")

st.subheader("PTP")
col6, col7, col8, col9 = st.columns(4)
with col6:
    _info_pair("Domain Number", "PTP domain (0–127).")
    ptp_domain = st.number_input("Domain", value=_comma_int(xip_defaults.get("ptp_domain", 127), 127), step=1, min_value=0, max_value=127)
with col7:
    _info_pair("Announce Interval", "PTP announce interval.")
    ann_iv = st.selectbox("announceInterval", PTP_ANNOUNCE_INTERVALS,
                          index=max(0, PTP_ANNOUNCE_INTERVALS.index(str(xip_defaults.get("ptp_announce_interval", "1")))))
with col8:
    _info_pair("Announce Timeout Count", "Number of missed announces before expiry.")
    ann_to = st.selectbox("announceReceiptTimeoutCount", [2,3,4,5,6,7,8,9,10],
                          index=max(0, [2,3,4,5,6,7,8,9,10].index(int(xip_defaults.get("ptp_announce_timeout", 3)))))
with col9:
    _info_pair("DSCP", "QoS DSCP (0–63).")
    ptp_dscp = st.slider("PTP DSCP", min_value=0, max_value=63, value=int(xip_defaults.get("ptp_dscp", 46)))

st.subheader("Audio defaults")

# We'll compute the final profile string into this variable
result_audio_profile: Optional[str] = None

col10, col11 = st.columns(2)
with col10:
    _info_pair("SMPTE Type", "Audio essence type")
    a_type = st.selectbox(
        "Audio Type",
        AUDIO_TYPES,
        index=max(0, AUDIO_TYPES.index(str(xip_defaults.get("audio_type", "SMPTE ST 2110-30")))),
        key="xip_audio_type",
    )

with col11:
    _info_pair("Profile", "Packet time & channel count profile.")
    existing_prof = str(xip_defaults.get("audio_profile", "125 usec, 16ch"))
    start_idx = AUDIO_PROFILES.index(existing_prof) if existing_prof in AUDIO_PROFILES else AUDIO_PROFILES.index("Custom…")

    prof_pick = st.selectbox(
        "Audio Profile",
        AUDIO_PROFILES,
        index=start_idx,
        key="xip_audio_profile_pick",
    )

    if prof_pick == "Custom…":
        prefill = existing_prof if existing_prof not in AUDIO_PROFILES_COMMON else ""
        custom_prof = st.text_input(
            "Custom profile",
            value=prefill,
            key="xip_audio_profile_custom",
        )
        result_audio_profile = custom_prof.strip() or existing_prof
    else:
        result_audio_profile = prof_pick

st.subheader("UDP ports")
col12, col13, col14 = st.columns(3)
with col12:
    _info_pair("Video UDP", "Destination & source UDP for video senders.")
    v_udp = st.text_input("Video UDP", value=str(xip_defaults.get("video_udp", "50100")))
with col13:
    _info_pair("Audio UDP", "Destination & source UDP for audio senders.")
    a_udp = st.text_input("Audio UDP", value=str(xip_defaults.get("audio_udp", "50200")))
with col14:
    _info_pair("Meta UDP", "Destination & source UDP for ancillary senders.")
    m_udp = st.text_input("Meta UDP", value=str(xip_defaults.get("meta_udp", "50300")))

save_xip = st.button("Save xip3901_parameters_reference.json", type="primary")
if save_xip:
    xip_work.setdefault("defaults", {})
    xip_work["defaults"].update({
        "nmos_mode": nm_mode,
        "registry_mode": reg_mode,
        "registry_port": int(reg_port),
        "query_port": int(qry_port),
        "ptp_domain": int(ptp_domain),
        "ptp_announce_interval": ann_iv,
        "ptp_announce_timeout": int(ann_to),
        "ptp_dscp": int(ptp_dscp),
        "audio_type": a_type,
        "audio_profile": result_audio_profile or str(xip_defaults.get("audio_profile", "125 usec, 16ch")),
        "video_udp": v_udp,
        "audio_udp": a_udp,
        "meta_udp": m_udp,
    })
    if _write_json(XIP_JSON_PATH, xip_work, backup=True):
        st.success("Saved xip3901_parameters_reference.json")

st.divider()

# =========================
# Section C: default_params.json (Scorpion defaults; raw JSON)
# =========================
st.header("C) default_params.json (Scorpion defaults)")
st.caption("This file contains many parameter mappings. Edit as JSON (validated on save).")

defaults_text = st.text_area(
    "default_params.json",
    value=json.dumps(cfg_defaults, indent=2, ensure_ascii=False) if cfg_defaults else "{}",
    height=300,
)

if st.button("Validate & Save default_params.json", type="secondary"):
    try:
        parsed = json.loads(defaults_text)
        if not isinstance(parsed, dict):
            raise ValueError("Root must be a JSON object (dict).")
        if _write_json(DEFAULTS_JSON_PATH, parsed, backup=True):
            st.success("Saved default_params.json")
    except Exception as e:
        st.error(f"Validation failed: {e}")