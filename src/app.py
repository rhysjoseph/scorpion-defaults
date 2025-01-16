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


def _get_config():
    with open(f"{ROOT_DIR}/config/config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    return config


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

def _get_mcm_unit_list(config):
    return config["MCM_LIST"]

def main():
    st.set_page_config(
        initial_sidebar_state="collapsed",
        layout="wide",
        page_title="Scorpion Defaults",
        page_icon=f"{PARENT_DIR}/assets/app/static/4. CT Mark - Colour PNG.png",
        # layout="wide",
    )
    with open(f"{PARENT_DIR}/assets/app/style.css", encoding="utf-8") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

    st.image(
        f"{PARENT_DIR}/assets/app/static/1. Super Landscape - Without Box - Colour With Black Text - PNG.png"
    )

    config = _get_config()    

    home_page, mcm_page, scorpion_page = st.tabs(["Home","MCM", "Scorpions"])
    with home_page:
        col1, col2,col3,col4 = st.columns([1,1,1,1])
        col1.link_button("hi",f"http://{config['LINKS']['hi']}", use_container_width=True)
        col2.link_button("Prism",f"http://{config['LINKS']['Prism']}", use_container_width=True)

        col1, col2,col3,col4 = st.columns([1,.7,.25,1])
        selected_cisco = col1.selectbox("Select Switch:", config["CISCO_LIST"])
        col2.write("")
        col2.write("")
        col2.link_button("Goto control", f"http://{config['CISCO_LIST'][selected_cisco]}", use_container_width=True)
        col3.write("")
        col3.write("")
        col4.write("")
        col4.write("")
        text_to_copy = f"ssh admin@{config['CISCO_LIST'][selected_cisco]}"
        hosted_html_file = "https://ct-testing-east-cm.s3.us-east-1.amazonaws.com/copy.html"
        iframe_url = f"{hosted_html_file}?copy={text_to_copy}"
        col4.markdown(f'<iframe style="overflow: hidden;  width: 50px; height: 50px;" src="{iframe_url}"></iframe>', unsafe_allow_html=True)
        
        col3.text("Copy SSH")

    with scorpion_page:
        units = _get_scorpion_unit_list(config)
        col1, col2, col3, col4 = st.columns([2, 0.5, 1, 1])
        select = col1.selectbox("Select Unit", units)

        try:
            scorpion = Defaults(
                name=select,
                host=units[select],
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
            col4.link_button("Goto Control", f"http://{units[select]}")

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
        mcm_units = _get_mcm_unit_list(config)
        col1, col2, col3, col4 = st.columns([1, 1,1,1])
        mcm_select = col1.selectbox("Select MCM", mcm_units)
        col2.write("")
        col2.write("")

        col2.link_button("Goto Control", f"http://{mcm_units[mcm_select]}")
        try:
            mcm = McmCall(
                host=mcm_units[mcm_select]
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
