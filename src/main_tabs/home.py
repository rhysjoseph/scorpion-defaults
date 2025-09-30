import os
import streamlit as st

import src.utils as utils

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PARENT_DIR)


def _norm_url(v: str | None) -> str | None:
    """
    Normalize a URL-like value:
      - return None for empty/missing values
      - if it lacks a scheme, prefix with http://
    """
    if not v:
        return None
    v = v.strip()
    if v.startswith(("http://", "https://")):
        return v
    return f"http://{v}"


def tab(config, scorpions, mcms, switches, xips):
    # Safely read LINKS map
    links = (config.get("LINKS") or {}) if isinstance(config, dict) else {}

    # Top quick links (render as enabled only if present)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    buttons = [
        ("hi", links.get("hi")),
        ("Prism", links.get("Prism")),
        ("CoreSwitch", links.get("CoreSwitch")),
        ("EBU Tech 3371", links.get("EBUTech3371")),
    ]
    for (label, raw_url), col in zip(buttons, (col1, col2, col3, col4)):
        url = _norm_url(raw_url)
        if url:
            col.link_button(label, url, use_container_width=True)
        else:
            # Disabled placeholder to keep layout consistent when a link is missing
            col.button(label, disabled=True, use_container_width=True)

    # Device discovery (includes XIP3901s)
    st.header("Discover Devices")
    discover = st.button("Discover", key="discover_devices")
    device_status = {}
    if discover:
        with st.spinner("Discovering Devices..."):
            device_status = utils.discover_devices(scorpions, mcms, switches, xips=xips)

    if device_status:
        for unit, status in device_status.items():
            st.markdown(
                f"<span style='color:{'green' if status else 'red'};'>{unit}: {'Online' if status else 'Offline'}</span>",
                unsafe_allow_html=True,
            )