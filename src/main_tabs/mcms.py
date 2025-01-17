import streamlit as st
from requests.exceptions import RequestException

import src.utils as utils
from src.mcm.api import Call

def tab(mcms):    
    col1, col2, col3, col4, col5 = st.columns([1, 1,1,1,1])
    mcm_select = col1.selectbox("Select MCM", mcms)
    col2.write("")
    col2.write("")

    col2.link_button("Goto Control", f"http://{mcms[mcm_select]}")
    col3.write("")
    col3.write("")
    if col3.button("Ping", "mcm_ping"):
        if utils.ping(mcms[mcm_select], timeout=2):
            st.info("PONG")
        else:
            st.error("WA WA")
    try:
        mcm = Call(
            host=mcms[mcm_select]
        )
    except RequestException as exc:
        mcm = None
        st.write(f"MCM Api Error: {exc}")
    if mcm:
        st.header("Commands")
        col1, col2 = st.columns([1, 1])
        
        if col1.button("All Off", use_container_width=True):
            with st.spinner("Unmonitoring all..."):
                response = mcm.monitor_all_channels("off")
            st.write(response)
        if col2.button("All On", use_container_width=True):
            with st.spinner("Monitoring all..."):
                response = mcm.monitor_all_channels("on")
            st.write(response)