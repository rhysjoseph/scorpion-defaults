import os
import streamlit as st

import src.main_tabs.home as home_tab
import src.main_tabs.scorpions as scorpions_tab
import src.main_tabs.mcms as mcms_tab
import src.main_tabs.arista as arista_tab
import src.main_tabs.switches as switches_tab
import src.main_tabs.xip3901 as xip3901_tab  # NEW

import src.utils as utils

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PARENT_DIR)


def main():
    st.set_page_config(
        initial_sidebar_state="collapsed",
        layout="wide",
        page_title="CT 2110",
        page_icon=f"{PARENT_DIR}/assets/app/static/4. CT Mark - Colour PNG.png",
    )
    with open(f"{PARENT_DIR}/assets/app/style.css", encoding="utf-8") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

    st.image(
        f"{PARENT_DIR}/assets/app/static/1. Super Landscape - Without Box - Colour With Black Text - PNG.png"
    )

    # Existing tuple: (config, scorpions, mcms, switches, aristas)
    config, scorpions, mcms, switches, aristas = utils.get_config()

    # NEW: build XIP list from config without disturbing the get_config() contract
    xips = utils.get_xip3901_unit_list(config)

    home_page, mcm_page, scorpion_page, xip_page, arista_page, switches_page = st.tabs(
        ["Home", "MCM", "Scorpions", "XIP3901", "Aristas", "Switches"]
    )

    with home_page:
        # Pass XIPs so the Home tab can include them in Discover Devices
        home_tab.tab(config, scorpions, mcms, switches, xips)

    with scorpion_page:
        scorpions_tab.tab(scorpions, config.get("SCORPION_CONTROL_PORT", 80))

    with xip_page:
        xip3901_tab.tab(xips, config.get("XIP3901_CONTROL_PORT", 80))  # NEW

    with mcm_page:
        mcms_tab.tab(mcms)

    with arista_page:
        arista_tab.tab(aristas)

    with switches_page:
        switches_tab.tab(config)


main()