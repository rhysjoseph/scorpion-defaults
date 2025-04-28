import streamlit as st
from requests.exceptions import RequestException
import src.utils as utils
from src.scorpion.api import Call
from src.scorpion.default import Defaults
from time import sleep


def tab(scorpions, control_port):
    col1, col2, col3, col4, col5 = st.columns([2, 0.5, 1, 1, 1])
    select = col1.selectbox("Select Unit", scorpions)
    if select != "Select":
        col5.write("")
        col5.write("")
        if col5.button("Ping", "scorpion_ping"):
            if utils.ping(scorpions[select], timeout=2):
                st.info("PONG")
            else:
                st.error("WA WA")

        try:
            scorpion = Defaults(
                name=select,
                host=scorpions[select],
                port=control_port,
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
                            host=scorpions[select], port=control_port
                        )
                        if str(command_id).startswith("3009"):
                            command_reset = {command_id: 0}
                            call = scorpion_direct.post(command_reset)
                        call = scorpion_direct.post(command)
                        st.write(call.get("status", "Failed!"))
                        sleep(3)
                        st.rerun()
