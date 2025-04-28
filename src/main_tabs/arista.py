import os
import re

import streamlit as st

from src.arista.api import Call
from src.utils import ping

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PARENT_DIR)

arista_api = Call()


def display_interface_toggles(interface_status_dict):
    """
    Displays interface status as toggle switches in rows of 8 using Streamlit.
    Orders the dictionary and sets the toggle state based on "connected" status.

    Args:
      interface_status_dict: A dictionary with interface names as keys and
                             interfaceStatus as values.
    """

    def natural_sort_key(s):
        """
        Key function for natural sorting (letters then numbers).
        """
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split("(\d+)", s)
        ]

    # Order the dictionary using natural sorting
    ordered_interfaces = dict(
        sorted(
            interface_status_dict.items(), key=lambda item: natural_sort_key(item[0])
        )
    )

    # Calculate the number of rows needed
    num_rows = len(ordered_interfaces) // 8
    if len(ordered_interfaces) % 8 != 0:
        num_rows += 1

    # Create rows of toggle switches
    for row_num in range(num_rows):
        cols = st.columns(8)  # Create 8 columns per row
        start_index = row_num * 8
        end_index = min(start_index + 8, len(ordered_interfaces))
        for i, (interface_name, status) in enumerate(
            list(ordered_interfaces.items())[start_index:end_index]
        ):
            with cols[i]:
                st.write(interface_name)
                # Set the toggle to on if status is "connected"

                is_disabled = status != "disabled"
                if interface_name not in st.session_state:
                    st.session_state[interface_name] = is_disabled

                st.toggle(
                    f"Status: {status}",
                    value=st.session_state[interface_name],
                    key=interface_name,
                    on_change=handle_toggle_change,
                    args=(interface_name,),
                    disabled=True if status == "connected" else False,
                )


def handle_toggle_change(interface_name):
    arista_api.enable_port(interface_name, st.session_state[interface_name])


def tab(aristas):
    col1, col2, col3, col4 = st.columns([1, 0.5, 0.5, 1])
    select_key = {"Select": ""}
    arista_select = select_key.copy()
    arista_select.update(aristas)
    selected_arista = col1.selectbox("Select Switch:", arista_select)

    if selected_arista != "Select":
        col2.write("")
        col2.write("")
        col2.link_button(
            "Goto control",
            f"http://{aristas[selected_arista]}",
            use_container_width=True,
        )

        col3.write("")
        col3.write("")
        if col3.button("Ping", key="arista_ping", use_container_width=True):
            if ping(aristas[selected_arista], timeout=2):
                st.info("PONG")
            else:
                st.error("WA WA")
                st.audio(
                    f"{ROOT_DIR}/assets/cartoon-fail-trumpet-278822.mp3", autoplay=True
                )
        col4.write("")
        col4.write("")
        ssh_command = f"ssh admin@{aristas[selected_arista]}"
        col4.code(ssh_command, language="python")
        ports = arista_api.get_status()
        c = 0

        port1, port2, port3, port4, port5, port6, port7, port8 = st.columns(8)
        display_interface_toggles(ports)
