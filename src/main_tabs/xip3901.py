import streamlit as st

import src.utils as utils
from src.xip3901.default import Defaults


def tab(xips: dict, control_port: int):
    """Render the XIP3901 page."""
    # Device picker
    col1, col2, col3, col4 = st.columns([2, 0.8, 1, 1])
    select = col1.selectbox("Select XIP3901", xips)

    if select == "Select":
        st.info("Pick a device to begin.")
        return

    host = xips.get(select, "")
    if not host:
        st.error("Selected device has no IP address in the list.")
        return

    # Quick actions
    col3.write("")  # spacing
    if col3.button("Ping", key="xip_ping"):
        st.success("Online" if utils.ping(host, timeout=2) else "Offline")

    col4.link_button("Goto Control", f"http://{host}", use_container_width=True)

    # Build Defaults helper
    defaults = Defaults(name=select, host=host, port=control_port)

    # Preview multicast + UDP plan
    with st.expander("Preview multicast & UDP plan"):
        st.json(defaults.preview_summary())

    st.divider()
    st.subheader("Apply Configuration")

    a, b, c = st.columns([1, 1, 1])
    d, e, f = st.columns([1, 1, 1])

    # Hostname only
    if a.button("Set Hostname", use_container_width=True):
        with st.spinner("Setting hostname..."):
            res = defaults.apply_network_and_hostname()
        _render_result(res)

    # Interfaces (eth1/eth2 DHCP, eth3 Static, frame Off)
    if b.button("Configure Interfaces", use_container_width=True):
        with st.spinner("Configuring eth1/eth2 DHCP, eth3 static, frame off..."):
            res = defaults.apply_interfaces()
        _render_result(res)

    # NMOS + PTP defaults
    if c.button("Apply NMOS + PTP", use_container_width=True):
        with st.spinner("Applying NMOS label/IS-04 and PTP defaults..."):
            res = defaults.apply_nmos_and_ptp()
        _render_result(res)

    # 2110 senders (video/audio/meta)
    if d.button("Apply 2110 Senders", use_container_width=True):
        with st.spinner("Pushing 2110 video/audio/meta senders..."):
            res = defaults.apply_senders()
        _render_result(res)

    # Advanced QoS (DSCP & payloadType)
    if e.button("Apply Advanced QoS", use_container_width=True):
        with st.spinner("Applying DSCP/payload types + global min delay..."):
            res = defaults.apply_advanced_qos()
        _render_result(res)

    # Everything end-to-end
    if f.button("Apply EVERYTHING", use_container_width=True):
        with st.spinner("Applying hostname, interfaces, NMOS+PTP, senders, QoS..."):
            res1 = defaults.apply_network_and_hostname()
            res2 = defaults.apply_interfaces()
            res3 = defaults.apply_nmos_and_ptp()
            res4 = defaults.apply_senders()
            res5 = defaults.apply_advanced_qos()
        _render_result({
            "hostname": res1,
            "interfaces": res2,
            "nmos_ptp": res3,
            "senders": res4,
            "qos": res5
        })


def _render_result(obj):
    """Pretty-print any result dict/list and surface errors inline."""
    if isinstance(obj, dict):
        if "error" in obj:
            st.error(obj["error"])
        st.json(obj)
    elif isinstance(obj, list):
        st.json(obj)
    else:
        st.write(obj)