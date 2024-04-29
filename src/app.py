import json
import os
import re
from time import sleep

import pandas
import streamlit as st

from src.scorpion.api import Call

# from streamlit_js_eval import get_page_location
from src.scorpion.default import Defaults

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PARENT_DIR)


def _get_config():
    with open(f"{ROOT_DIR}/config/config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    return config


def _get_unit_list(config):
    if config.get("SCORPION_RANGE"):
        start = config.get("SCORPION_RANGE").split("-")[0]
        end = config.get("SCORPION_RANGE").split("-")[1]
        return {
            f"{config['SCORPION_RANGE_NAME_PFIX']}{i:03}": f"10.244.245.{int(i)}"
            for i in range(int(start), int(end) + 1)
        }
    else:
        return config["SCORPION_LIST"]


def main():
    st.set_page_config(
        initial_sidebar_state="collapsed",
        page_title="App",
        page_icon=f"{PARENT_DIR}/assets/app/static/4. CT Mark - Colour PNG.png",
        layout="wide",
    )
    with open(f"{PARENT_DIR}/assets/app/style.css", encoding="utf-8") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

    st.image(
        f"{PARENT_DIR}/assets/app/static/1. Super Landscape - Without Box - Colour With Black Text - PNG.png"
    )

    config = _get_config()

    units = _get_unit_list(config)

    select = st.selectbox("Select Unit", units)
    scorpion = Defaults(
        host=units[select], port=config.get("SCORPION_CONTROL_PORT", 80)
    )
    if st.button("Set Defaults"):
        with st.spinner("Setting Defaults..."):
            response = scorpion.set_defaults()
        st.write(response)

    with st.spinner("Getting Current..."):
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


main()
