import os

import streamlit as st

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PARENT_DIR)


def tab(config):
    col1, col2, col3, col4 = st.columns([1, 0.5, 0.5, 1])
    selected_cisco = col1.selectbox("Select Switch:", config["SWITCH_LIST"])
    col2.write("")
    col2.write("")
    col2.link_button(
        "Goto control",
        f"http://{config['SWITCH_LIST'][selected_cisco]}",
        use_container_width=True,
    )

    col3.write("")
    col3.write("")
    if col3.button("Ping", use_container_width=True):
        if utils.ping(config["SWITCH_LIST"][selected_cisco], timeout=2):
            st.info("PONG")
        else:
            st.error("WA WA")
            st.audio(
                f"{ROOT_DIR}/assets/cartoon-fail-trumpet-278822.mp3", autoplay=True
            )
    col4.write("")
    col4.write("")
    ssh_command = f"ssh admin@{config['SWITCH_LIST'][selected_cisco]}"
    col4.code(ssh_command, language="python")
