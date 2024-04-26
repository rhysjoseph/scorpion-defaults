import json
import os
import re
from time import sleep

import pandas
import streamlit as st

from src.scorpion.api import Call

# from streamlit_js_eval import get_page_location
from src.scorpion.default import get_current, set_defaults

dir_path = os.path.dirname(os.path.realpath(__file__))


def main():
    # Call("10.244.245.6")
    st.set_page_config(
        initial_sidebar_state="collapsed",
        page_title="App",
        page_icon=f"{dir_path}/assets/app/static/4. CT Mark - Colour PNG.png",
        layout="wide",
    )
    with open(f"{dir_path}/assets/app/style.css", encoding="utf-8") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

    st.image(
        f"{dir_path}/assets/app/static/1. Super Landscape - Without Box - Colour With Black Text - PNG.png"
    )
    unit_number = [f"SCPN6-{i:03}" for i in range(1, 37)]
    select = st.selectbox("Select Unit", unit_number)
    if st.button("Set Defaults"):
        with st.spinner("Setting Defaults..."):
            response = set_defaults(host=f"10.244.245.{int(select[-3:])}")
        st.write(response)

    with st.spinner("Getting Current..."):
        data = get_current(host=f"10.244.245.{int(select[-3:])}")
    if isinstance(data, str):
        st.write(data)
    else:
        colms = st.columns((1, 2, 1, 2, 2))
        fields = ["№", "Setting", "Code", "Value", "Set Default"]
        for col, field_name in zip(colms, fields):
            # header
            col.write(field_name)

        for x, email in enumerate(data["name"]):
            command_id = data["code"][x].split("@")[0]
            col1, col2, col3, col4, col5 = st.columns((1, 2, 1, 2, 2))
            col1.write(x)  # index
            col2.write(data["name"][x])  # email
            col3.write(command_id)  # unique ID
            col4.write(data["value"][x])  # email status
            button_type = (
                "Set Default" if data["value"][x] != data["default"][x] else "Current"
            )

            button_phold = col5.empty()  # create a placeholder
            do_action = None
            if button_type == "Set Default":
                command = f"{command_id}={data['default'][x]}"
                do_action = button_phold.button(button_type, key=x)
            if do_action:
                scorpion = Call(host=f"10.244.245.{int(select[-3:])}")
                call = scorpion.post(command)
                st.write(call.get("status", "Failed!"))
                sleep(3)
                st.rerun()


main()
