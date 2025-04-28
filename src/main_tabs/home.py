import os

import streamlit as st

import src.utils as utils

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PARENT_DIR)


def tab(config, scorpions, mcms, switches):
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    col1.link_button("hi", f"http://{config['LINKS']['hi']}", use_container_width=True)
    col2.link_button(
        "Prism", f"http://{config['LINKS']['Prism']}", use_container_width=True
    )

    device_status = {}
    if st.button("Discover All Devices"):
        with st.spinner("Discovering Devices..."):
            device_status = utils.discover_devices(scorpions, mcms, switches)
    if device_status:
        for unit, status in device_status.items():
            if status:
                st.write(
                    f"<span style='color:green;'>{unit}: Online</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.write(
                    f"<span style='color:red;'>{unit}: Offline</span>",
                    unsafe_allow_html=True,
                )
