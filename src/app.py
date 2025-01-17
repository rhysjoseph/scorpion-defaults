import json
import os
import re
from time import sleep

import pandas
import streamlit as st
from requests.exceptions import RequestException
from src.scorpion.api import Call 
from src.scorpion.default import Defaults
from src.mcm.api import Call as McmCall

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PARENT_DIR)

def ping(host, timeout=.1): 
    """
    Pings a host with a specified timeout and returns True if the host is reachable, 
    False otherwise.
    """
    response = os.system("ping -c 1 -W " + str(timeout) + " " + host)
    if response == 0:
        return True
    else:
        return False

def discover_devices(scorpions, mcms, switches):
    devices = scorpions | mcms| switches
    status = {}
    for device in devices:
        ip_address = (devices[device])
        if ping(ip_address):
            status[device] = True
        else:
            status[device] = False
    print(status)
    return (status)


def _get_config():
    with open(f"{ROOT_DIR}/config/config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    scorpions = _get_scorpion_unit_list(config)
    return config, scorpions, config["MCM_LIST"], config["SWITCH_LIST"]


def _get_scorpion_unit_list(config):
    if config.get("SCORPION_RANGE"):
        start = config.get("SCORPION_RANGE").split("-")[0]
        end = config.get("SCORPION_RANGE").split("-")[1]
        return {
            f"{config['SCORPION_RANGE_NAME_PFIX']}{i:03}": f"{config['CONTROL_PREFIX']}.{int(i)}"
            for i in range(int(start), int(end) + 1)
        }
    else:
        return config["SCORPION_LIST"]



def main():
    st.set_page_config(
        initial_sidebar_state="collapsed",
        layout="wide",
        page_title="CT 2110",
        page_icon=f"{PARENT_DIR}/assets/app/static/4. CT Mark - Colour PNG.png",
        # layout="wide",
    )
    with open(f"{PARENT_DIR}/assets/app/style.css", encoding="utf-8") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

    st.image(
        f"{PARENT_DIR}/assets/app/static/1. Super Landscape - Without Box - Colour With Black Text - PNG.png"
    )

    config, scorpions, mcms, switches = _get_config()    

    home_page, mcm_page, scorpion_page = st.tabs(["Home","MCM", "Scorpions"])
    with home_page:

        col1, col2,col3,col4 = st.columns([1,1,1,1])
        col1.link_button("hi",f"http://{config['LINKS']['hi']}", use_container_width=True)
        col2.link_button("Prism",f"http://{config['LINKS']['Prism']}", use_container_width=True)

        col1, col2,col3,col4, col5 = st.columns([1,.7,.25,1,1])
        selected_cisco = col1.selectbox("Select Switch:", config["SWITCH_LIST"])
        col2.write("")
        col2.write("")
        col2.link_button("Goto control", f"http://{config['SWITCH_LIST'][selected_cisco]}", use_container_width=True)
        col3.write("")
        col3.write("")
        col3.text("Copy SSH")

        col4.write("")
        col4.write("")
        text_to_copy = f"ssh admin@{config['SWITCH_LIST'][selected_cisco]}"
        hosted_html_file = "https://ct-testing-east-cm.s3.us-east-1.amazonaws.com/copy.html"
        iframe_url = f"{hosted_html_file}?copy={text_to_copy}"
        col4.markdown(f'<iframe style="overflow: hidden;  width: 50px; height: 50px;" src="{iframe_url}"></iframe>', unsafe_allow_html=True)
                
        col5.write("")
        col5.write("")
        if col5.button("Ping"):
            if ping(config['SWITCH_LIST'][selected_cisco], timeout=2):
                st.info("PONG")
            else:
                st.error("wa wa")
        device_status={}
        st.write("")
        st.write("")
        if st.button("Discover All Devices"):
            with st.spinner("Discovering Devices..."):
                device_status= discover_devices(scorpions, mcms, switches)
        if device_status:
            for unit, status in device_status.items():
                if status:
                    st.write(f"<span style='color:green;'>{unit}: Online</span>", unsafe_allow_html=True)
                else:
                    st.write(f"<span style='color:red;'>{unit}: Offline</span>", unsafe_allow_html=True)
    with scorpion_page:
        col1, col2, col3, col4, col5 = st.columns([2, 0.5, 1, 1,1])
        select = col1.selectbox("Select Unit", scorpions)
        col5.write("")
        col5.write("")
        if col5.button("Ping", "scorpion_ping"):
            if ping(scorpions[select], timeout=2):
                st.info("PONG")
            else:
                st.error("wa wa")
        try:
            scorpion = Defaults(
                name=select,
                host=scorpions[select],
                port=config.get("SCORPION_CONTROL_PORT", 80),
            )
        except RequestException as exc:
            scorpion = None
            st.write(f"Scorpion Api Error: {exc}")

        if scorpion:
            col3.write("")  # hacky way to lower the button
            col3.write("")
            col4.write("")
            col4.write("")
            col4.link_button("Goto Control", f"http://{scorpions[select]}")

            if col3.button("Set Defaults"):
                with st.spinner("Setting Defaults..."):
                    response = scorpion.set_defaults()
                st.write(response)
            st.divider()
            with st.spinner("Getting Current Settings..."):
                data = scorpion.get_current()
            if isinstance(data, str):
                st.write(data)
            else:
                colms = st.columns((1, 2, 1, 2, 2))
                fields = ["№", "Setting", "Code", "Value", "Set Default"]
                for col, field_name in zip(colms, fields):
                    col.write(field_name)

                for x, variable in enumerate(data["name"]):
                    command_id = data["code"][x].split("@")[0]
                    col1, col2, col3, col4, col5 = st.columns((1, 2, 1, 2, 2))
                    col1.write(x)  # index
                    col2.write(data["name"][x])  # email
                    col3.write(command_id)  # unique ID
                    col4.write(data["value"][x])  # email status
                    button_type = (
                        f"Set Default ({data['default'][x]})"
                        if data["value"][x] != data["default"][x]
                        else "Current"
                    )

                    button_phold = col5.empty()  # create a placeholder
                    do_action = None
                    if button_type.startswith("Set Default"):
                        command = {command_id: data["default"][x]}
                        do_action = button_phold.button(button_type, key=x)
                    if do_action:
                        scorpion_direct = Call(
                            host=units[select], port=config.get("SCORPION_CONTROL_PORT", 80)
                        )
                        if str(command_id).startswith("3009"):
                            command_reset = {command_id: 0}
                            call = scorpion_direct.post(command_reset)
                        call = scorpion_direct.post(command)
                        st.write(call.get("status", "Failed!"))
                        sleep(3)
                        st.rerun()
    with mcm_page:

        col1, col2, col3, col4, col5 = st.columns([1, 1,1,1,1])
        mcm_select = col1.selectbox("Select MCM", mcms)
        col2.write("")
        col2.write("")

        col2.link_button("Goto Control", f"http://{mcms[mcm_select]}")
        col3.write("")
        col3.write("")
        if col3.button("Ping", "mcm_ping"):
            if ping(mcms[mcm_select], timeout=2):
                st.info("PONG")
            else:
                st.error("wa wa")
        try:
            mcm = McmCall(
                host=mcms[mcm_select]
            )
        except RequestException as exc:
            scorpion = None
            st.write(f"Scorpion Api Error: {exc}")
        if mcm:
            st.header("Commands")
            if st.button("All Off"):
                with st.spinner("Unmonitoring all..."):
                    response = mcm.monitor_all_channels("off")
                st.write(response)
            if st.button("All On"):
                with st.spinner("Monitoring all..."):
                    response = mcm.monitor_all_channels("on")
                st.write(response)
main()
