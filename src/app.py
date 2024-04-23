import json
import os
import re
from time import sleep

import streamlit as st

# from streamlit_js_eval import get_page_location
from src.scorpion.default import set_defaults

dir_path = os.path.dirname(os.path.realpath(__file__))


def main():
    st.set_page_config(
        initial_sidebar_state="collapsed",
        page_title="App",
        page_icon=f"{dir_path}/assets/app/static/4. CT Mark - Colour PNG.png",
    )
    with open(f"{dir_path}/assets/app/style.css", encoding="utf-8") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

    st.image(
        f"{dir_path}/assets/app/static/1. Super Landscape - Without Box - Colour With Black Text - PNG.png"
    )

    st.button("Set Defaults", on_click=set_defaults(host="70.187.125.3", port=8000))


main()
