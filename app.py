"""
L3-Advisor — AI-powered Layer 3 network troubleshooting assistant.

Connects to the Azure AI Inference endpoint using an OpenAI-compatible client.
Set the GITHUB_TOKEN (or AZURE_INFERENCE_TOKEN) environment variable before
running, or enter the key in the sidebar at runtime.
"""

from __future__ import annotations

import datetime
import os

import streamlit as st
from openai import OpenAI, AuthenticationError, APIConnectionError

# ---------------------------------------------------------------------------
# Page config — must be the very first Streamlit call
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
        "You are an expert in OSPF (Open Shortest Path First). "
        "Focus on areas such as neighbor adjacency issues, DR/BDR elections, "
        "area types, LSA flooding, SPF calculation, and route redistribution."
    ),
    "BGP": (
        "You are an expert in BGP (Border Gateway Protocol). "
        "Focus on eBGP/iBGP peering, AS-path manipulation, route reflectors, "
        "communities, route filtering, and convergence troubleshooting."
    ),
    "EIGRP": (
        "You are an expert in EIGRP (Enhanced Interior Gateway Routing Protocol). "
        "Focus on DUAL algorithm, feasible successors, stuck-in-active states, "
        "K-value mismatches, and redistribution."
    ),
    "Static Routing": (
        "You are an expert in static routing. "
        "Focus on administrative distance, floating static routes, recursive "
        "routing loops, null routes, and policy-based routing."
    ),
}

SYSTEM_PROMPT_TEMPLATE = """\
You are L3-Advisor, a senior network engineer AI specialising in Layer 3 \
routing troubleshooting. {protocol_context}

When responding to a troubleshooting query, you MUST structure every answer \
using the following Markdown headers in this exact order:

## 🔎 Analysis
Describe the likely root cause(s) based on the symptoms provided. Reference \
specific protocol behaviour where relevant.

## 🛠️ Resolution Steps
Provide a numbered, step-by-step remediation plan that a network engineer can \
follow sequentially.

## 💻 CLI Commands
Provide all relevant diagnostic and corrective CLI commands inside fenced code \
blocks, for example:

```
show ip ospf neighbor
debug ip ospf adj
```

Always be precise, professional, and concise. If the user has already \
attempted steps mentioned in the conversation history, do not repeat them — \
acknowledge what has been tried and advance the troubleshooting."""


# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
def _init_session_state() -> None:
    """Initialise all session-state keys on first run."""
    if "messages" not in st.session_state:
        st.session_state.messages = []          # list of {"role": ..., "content": ...}
    if "protocol" not in st.session_state:
        st.session_state.protocol = PROTOCOLS[0]
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("GITHUB_TOKEN", "")
    if "connected" not in st.session_state:
        st.session_state.connected = False


# ---------------------------------------------------------------------------
# OpenAI-compatible client
# ---------------------------------------------------------------------------
def _get_client(api_key: str) -> OpenAI:
    return OpenAI(base_url=AZURE_ENDPOINT, api_key=api_key)


def _build_system_prompt(protocol: str) -> str:
    context = PROTOCOL_CONTEXT.get(protocol, "")
    return SYSTEM_PROMPT_TEMPLATE.format(protocol_context=context)


def _chat(api_key: str, protocol: str, messages: list[dict]) -> str:
    """Send messages to the model and return the assistant reply."""
    client = _get_client(api_key)
    system_msg = {"role": "system", "content": _build_system_prompt(protocol)}
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[system_msg, *messages],
        temperature=0.3,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Export helper
# ---------------------------------------------------------------------------
def _build_audit_log(messages: list[dict], protocol: str) -> str:
    """Build a formatted Incident Audit Log from the chat history."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = [
        "=" * 70,
        "           L3-ADVISOR — INCIDENT AUDIT LOG",
        "=" * 70,
        f"Generated  : {timestamp}",
        f"Protocol   : {protocol}",
        f"Total turns: {len(messages)}",
        "=" * 70,
        "",
    ]
    for i, msg in enumerate(messages, start=1):
        role = msg["role"].upper()
        lines.append(f"[{i}] {role}")
        lines.append("-" * 40)
        lines.append(msg["content"])
        lines.append("")
    lines.append("=" * 70)
    lines.append("END OF LOG")
    lines.append("=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def _render_sidebar() -> None:
    with st.sidebar:
        # Logo / branding placeholder
        st.markdown(
            """
            <div style="text-align:center; padding: 10px 0 20px 0;">
                <span style="font-size:3rem;">🌐</span>
                <h2 style="margin:0; color:#1f77b4;">L3-Advisor</h2>
                <p style="margin:0; font-size:0.8rem; color:grey;">
                    AI Network Troubleshooting
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # API key input
        api_key_input = st.text_input(
            "🔑 API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="Paste your GitHub / Azure token…",
            help=(
                "Set the GITHUB_TOKEN environment variable, or enter the key "
                "here. The key is used only within this session."
            ),
        )
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input
            st.session_state.connected = False

        # Protocol selector
        st.markdown("### 📡 Protocol Focus")
        selected = st.selectbox(
            "Select routing protocol",
            PROTOCOLS,
            index=PROTOCOLS.index(st.session_state.protocol),
            label_visibility="collapsed",
        )
        if selected != st.session_state.protocol:
            st.session_state.protocol = selected

        st.divider()

        # Status indicators
        st.markdown("### 📊 Status")
        if st.session_state.api_key:
            st.success("🟢 API Key: Configured")
        else:
            st.error("🔴 API Key: Missing")

        st.info(f"🔵 Protocol: **{st.session_state.protocol}**")
        st.info(f"💬 Messages in session: **{len(st.session_state.messages)}**")

        st.divider()

        # Export button
        if st.session_state.messages:
            audit_log = _build_audit_log(
                st.session_state.messages, st.session_state.protocol
            )
            st.download_button(
                label="📥 Download Incident Audit Log",
                data=audit_log,
                file_name=f"l3_advisor_audit_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # Clear chat
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


# ---------------------------------------------------------------------------
# Main chat interface
# ---------------------------------------------------------------------------
def _render_chat() -> None:
    st.title("🌐 L3-Advisor")
    st.caption(
        f"AI-powered Layer 3 troubleshooting assistant — "
        f"currently focused on **{st.session_state.protocol}**"
    )

    # Render existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Describe your routing issue…"):
        # Validate API key before doing anything
        if not st.session_state.api_key:
            st.error(
                "⚠️ No API key configured. Please enter your GitHub / Azure "
                "token in the sidebar before sending a message."
            )
            return

        # Display user message immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analysing…"):
                try:
                    reply = _chat(
                        api_key=st.session_state.api_key,
                        protocol=st.session_state.protocol,
                        messages=st.session_state.messages,
                    )
                    st.session_state.connected = True
                except AuthenticationError:
                    reply = (
                        "❌ **Authentication Error** — the API key provided is "
                        "invalid or has expired. Please update it in the sidebar."
                    )
                    st.session_state.connected = False
                except APIConnectionError as exc:
                    reply = (
                        f"❌ **Connection Error** — could not reach the inference "
                        f"endpoint.\n\nDetails: `{exc}`"
                    )
                    st.session_state.connected = False
                except Exception as exc:  # noqa: BLE001
                    reply = (
                        f"❌ **Unexpected Error** — `{type(exc).__name__}: {exc}`"
                    )
                    st.session_state.connected = False

            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    _init_session_state()
    _render_sidebar()
    _render_chat()


if __name__ == "__main__":
    main()
