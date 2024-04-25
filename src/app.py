import json
import os
import re
from time import sleep

import pandas
import streamlit as st

# from streamlit_js_eval import get_page_location
from src.scorpion.default import get_defaults, set_defaults

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
    unit_number = [str(i) for i in range(1, 33)]
    select = st.selectbox("Unit Number", unit_number)
    if st.button("Set Defaults"):
        with st.spinner("Setting Defaults..."):
            response = set_defaults(host=f"10.244.245.{select}")
        st.write(response)
    # df = pandas.DataFrame(data)
    # st.dataframe(df)
    # if st.button("Set Defaults"):
    #     with st.spinner("Setting Defaults..."):
    #         set_defaults(host="70.187.125.3", port=8000)
    #     st.success("Done")
    # button_text = "foo", "bar", "baz"

    # for text, col in zip(button_text, st.columns(len(button_text))):
    #     if col.button(text):
    #         col.write(f"{text} clicked")

    # # Show users table
    # colms = st.columns((1, 2, 1, 2, 2))
    # fields = ["№", "setting", "code", "value", "default"]
    # for col, field_name in zip(colms, fields):
    #     # header
    #     col.write(field_name)

    # for x, email in enumerate(data["name"]):
    #     col1, col2, col3, col4, col5 = st.columns((1, 2, 1, 2, 2))
    #     col1.write(x)  # index
    #     col2.write(data["name"][x])  # email
    #     col3.write(data["code"][x])  # unique ID
    #     col4.write(data["value"][x])  # email status
    #     disable_status = data["default"][x]  # flexible type of button
    #     button_type = (
    #         "Set Default" if data["value"][x] != data["default"][x] else "Current"
    #     )
    #     button_phold = col5.empty()  # create a placeholder
    #     do_action = button_phold.button(button_type, key=x)
    #     if do_action:
    #         st.write(f"Button {x} clicked")
    #         pass  # do some action with row's data
    #         # button_phold.empty()  #  remove button


main()
