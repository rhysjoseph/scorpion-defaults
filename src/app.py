import json
import os
from ipaddress import IPv4Network
from time import sleep

import streamlit as st
from netaddr import IPAddress
from streamlit_js_eval import get_page_location

from src.net.adaptor import Address

dir_path = os.path.dirname(os.path.realpath(__file__))


def get_mask(mask_bit):
    return IPv4Network(f"0.0.0.0/{mask_bit}").netmask


def get_files():
    return ["test", "one", "two"]


def main():
    adaptor = Address()
    current_cidr = adaptor.config.get("static_ip")
    current_ip = current_cidr.split("/")[0]
    current_mask_bit = int(current_cidr.split("/")[1])
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

    # Link to another address on server
    page_loc = get_page_location() or {"origin": "localhost"}
    link = f"{page_loc.get('origin')}/anotherplace"

    st.markdown(
        """
    <style>
    .big-font {
        font-size:30px !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<a class="big-font" href="{link}" target="_self">Go To Link</a>',
        unsafe_allow_html=True,
    )

    st.divider()
    tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

    with tab1:
        st.write("Load from file")
        with st.form(key="store-file"):
            select = st.selectbox("File Name", get_files())
            def_form_submit = st.form_submit_button("Select File")
        if def_form_submit:
            st.write(f"File Selected {select}")

    with tab2:
        st.write("Set Static Ip")
        st.write("Requires Network Manager and interface definintion in install.sh")
        with st.expander("Bit Mask Calculator", expanded=False):
            mask_bit = st.slider("Subnet Calculator", 0, 32, value=current_mask_bit)
            mask = get_mask(mask_bit)
            st.write(f"The subnet mask is {mask}")
        with st.form(key="my-form"):
            ip = st.text_input("Enter the static ip address", value=current_ip)
            mask = st.text_input(
                "Enter the subnet mask",
                value=mask,
            )
            gateway = st.text_input(
                "Enter the gateway", value=adaptor.config.get("gateway", "192.168.1.1")
            )
            submit = st.form_submit_button("Set to Static IP")

        if submit:
            mask_bit = IPAddress(mask).netmask_bits()
            st.write(
                "Changing IP!! Please use the following links... (Takes 5-10 Seconds)"
            )
            st.page_link(f"http://{ip}", label="Click to Open This page at New Address")
            sleep(5)
            adaptor.set_adaptor_static(f"{ip}/{mask_bit}", gateway)

    with tab3:
        st.write("Factory Reset")
        with st.form(key="reset"):
            reset_submit = st.form_submit_button("Reset")
        if reset_submit:
            st.write("This is just an example!")


main()
