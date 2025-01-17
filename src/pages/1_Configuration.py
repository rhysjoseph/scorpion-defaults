import streamlit as st
import json
import os
import src.utils as utils
# ... your existing code (including get_config) ...
PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.dirname(PARENT_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)

def save_config(config):
    """Saves the updated config to the config.json file."""
    with open(f"{ROOT_DIR}/config/config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)  # Use indent for better readability

def config_editor():
    """Streamlit UI for editing and saving the config file."""
    st.header("Configuration Editor")

    config, scorpions, mcm_list, switch_list = utils.get_config()

    st.subheader("LINKS")
    for link_name, link_value in config["LINKS"].items():
        new_link = st.text_input(f"Edit {link_name}:", value=link_value)
        if st.button(f"Update {link_name}"):
            config["LINKS"][link_name] = new_link
            save_config(config)
            st.success(f"{link_name} updated!")

    st.subheader("SCORPION_CONTROL_PORT")
    new_port = st.text_input("Enter new port:", value=config["SCORPION_CONTROL_PORT"])
    if st.button("Update Port"):
        config["SCORPION_CONTROL_PORT"] = new_port
        save_config(config)
        st.success("SCORPION_CONTROL_PORT updated!")

    st.download_button(
        label="Download Config",
        data=json.dumps(config, indent=4),
        file_name="config.json",
        mime="application/json",
    )

    uploaded_file = st.file_uploader("Upload Config", type="json")
    if uploaded_file is not None:
        try:
            new_config = json.load(uploaded_file)
            save_config(new_config)
            st.success("Config file uploaded and saved!")
        except json.JSONDecodeError:
            st.error("Invalid JSON file!")

config_editor()