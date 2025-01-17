import streamlit as st

import src.utils as utils

def tab(config, scorpions, mcms, switches):
    col1, col2,col3,col4 = st.columns([1,1,1,1])
    col1.link_button("hi",f"http://{config['LINKS']['hi']}", use_container_width=True)
    col2.link_button("Prism",f"http://{config['LINKS']['Prism']}", use_container_width=True)

    col1, col2,col3, col4 = st.columns([1,.5,.5,1])
    selected_cisco = col1.selectbox("Select Switch:", config["SWITCH_LIST"])
    col2.write("")
    col2.write("")
    col2.link_button("Goto control", f"http://{config['SWITCH_LIST'][selected_cisco]}", use_container_width=True)

    col3.write("")
    col3.write("")
    if col3.button("Ping", use_container_width=True):
        if utils.ping(config['SWITCH_LIST'][selected_cisco], timeout=2):
            st.info("PONG")
        else:
            st.error("WA WA")
    col4.write("")
    col4.write("")
    ssh_command = f"ssh admin@{config['SWITCH_LIST'][selected_cisco]}"
    col4.code(ssh_command, language="python")        
    st.write("")
    st.write("")

    device_status={}
    if st.button("Discover All Devices"):
        with st.spinner("Discovering Devices..."):
            device_status= utils.discover_devices(scorpions, mcms, switches)
    if device_status:
        for unit, status in device_status.items():
            if status:
                st.write(f"<span style='color:green;'>{unit}: Online</span>", unsafe_allow_html=True)
            else:
                st.write(f"<span style='color:red;'>{unit}: Offline</span>", unsafe_allow_html=True)