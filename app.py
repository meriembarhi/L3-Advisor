# app.py
import streamlit as st
from core.llm import get_advisor_response
from utils.export import generate_audit_log

st.set_page_config(page_title="L3-Advisor", page_icon="📡")

st.title("📡 L3-Advisor: Senior Network Engineer AI")

# Sidebar for Protocol Selection
with st.sidebar:
    st.header("Settings")
    protocol = st.selectbox("Select Protocol", ["OSPF", "BGP", "EIGRP", "Static Routing"])
    
    if st.button("Export Incident Audit Log"):
        log_file = generate_audit_log(st.session_state.messages)
        st.download_button("Download .txt", log_file, file_name="audit_log.txt")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Describe the routing issue..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = get_advisor_response(protocol, prompt)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})