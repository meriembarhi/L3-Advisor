"""
L3-Advisor — AI-powered Layer 3 network troubleshooting assistant.
"""

from __future__ import annotations

import datetime
import os

import streamlit as st
from openai import OpenAI, AuthenticationError, APIConnectionError

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="L3-Advisor",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AZURE_ENDPOINT = "https://models.inference.ai.azure.com"
DEFAULT_MODEL = "gpt-4o"

PROTOCOLS = ["OSPF", "BGP", "EIGRP", "Static Routing"]

PROTOCOL_CONTEXT: dict[str, str] = {
    "OSPF": (
        "You are an expert in OSPF. Focus on neighbor adjacency issues, DR/BDR elections, "
        "area types, LSA flooding, SPF calculation, and route redistribution."
    ),
    "BGP": (
        "You are an expert in BGP. Focus on eBGP/iBGP peering, AS-path manipulation, "
        "route reflectors, communities, route filtering, and convergence troubleshooting."
    ),
    "EIGRP": (
        "You are an expert in EIGRP. Focus on DUAL algorithm, feasible successors, "
        "stuck-in-active states, K-value mismatches, and redistribution."
    ),
    "Static Routing": (
        "You are an expert in static routing. Focus on administrative distance, "
        "floating static routes, recursive loops, and policy-based routing."
    ),
}

SYSTEM_PROMPT_TEMPLATE = """\
You are L3-Advisor, a senior network engineer AI specialising in Layer 3 \
routing troubleshooting. {protocol_context}

When responding, you MUST structure every answer using:
## 🔎 Analysis
## 🛠️ Resolution Steps
## 💻 CLI Commands

Always be precise. If the user provides device output (logs/configs), analyze them \
specifically to provide a tailored diagnosis."""

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
def _init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "protocol" not in st.session_state:
        st.session_state.protocol = PROTOCOLS[0]
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("GITHUB_TOKEN", "")
    if "device_logs" not in st.session_state:
        st.session_state.device_logs = ""
    if "connected" not in st.session_state:
        st.session_state.connected = False

# ---------------------------------------------------------------------------
# Logic & Chat
# ---------------------------------------------------------------------------
def _get_client(api_key: str) -> OpenAI:
    return OpenAI(base_url=AZURE_ENDPOINT, api_key=api_key)

def _build_system_prompt(protocol: str) -> str:
    context = PROTOCOL_CONTEXT.get(protocol, "")
    return SYSTEM_PROMPT_TEMPLATE.format(protocol_context=context)

def _chat(api_key: str, protocol: str, messages: list[dict], device_context: str = "") -> str:
    client = _get_client(api_key)
    system_msg = {"role": "system", "content": _build_system_prompt(protocol)}
    
    # We create a copy of messages to avoid messing up the UI history
    chat_history = list(messages)
    
    # If there is device context, we modify the latest user message for the AI only
    if device_context and chat_history:
        last_msg = chat_history[-1]
        if last_msg["role"] == "user":
            enriched_content = (
                f"{last_msg['content']}\n\n"
                f"### ATTACHED DEVICE DATA ###\n{device_context}"
            )
            chat_history[-1] = {"role": "user", "content": enriched_content}

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[system_msg, *chat_history],
        temperature=0.3,
    )
    return response.choices[0].message.content

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """<div style="text-align:center; padding: 10px 0 20px 0;">
               <span style="font-size:3rem;">🌐</span>
               <h2 style="margin:0; color:#1f77b4;">L3-Advisor</h2>
               <p style="margin:0; font-size:0.8rem; color:grey;">AI Network Troubleshooting</p>
               </div>""", unsafe_allow_html=True
        )

        st.divider()

        # API Key
        st.session_state.api_key = st.text_input(
            "🔑 API Key", value=st.session_state.api_key, type="password"
        )

        # Protocol
        st.markdown("### 📡 Protocol Focus")
        st.session_state.protocol = st.selectbox(
            "Select routing protocol", PROTOCOLS, 
            index=PROTOCOLS.index(st.session_state.protocol),
            label_visibility="collapsed"
        )

        st.divider()

        # NEW: Device Context Box
        st.markdown("### 📋 Device Context")
        st.session_state.device_logs = st.text_area(
            "Paste 'show' output here:",
            value=st.session_state.device_logs,
            placeholder="e.g. show ip route, show running-config...",
            height=250,
            help="The AI will analyze this specific data to help troubleshoot."
        )

        st.divider()

        # Export & Clear
        if st.session_state.messages:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

# ---------------------------------------------------------------------------
# Main chat interface
# ---------------------------------------------------------------------------
def _render_chat() -> None:
    st.title("🌐 L3-Advisor")
    st.caption(f"Currently focused on **{st.session_state.protocol}**")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Describe your routing issue…"):
        if not st.session_state.api_key:
            st.error("⚠️ Please enter your API token in the sidebar.")
            return

        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Analysing with context…"):
                try:
                    reply = _chat(
                        api_key=st.session_state.api_key,
                        protocol=st.session_state.protocol,
                        messages=st.session_state.messages,
                        device_context=st.session_state.device_logs
                    )
                except Exception as exc:
                    reply = f"❌ **Error** — `{exc}`"

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

def main() -> None:
    _init_session_state()
    _render_sidebar()
    _render_chat()

if __name__ == "__main__":
    main()