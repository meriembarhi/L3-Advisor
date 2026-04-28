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

SHOW_COMMAND_TEMPLATES: dict[str, list[str]] = {
    "OSPF": [
        "show ip ospf neighbor",
        "show ip ospf interface",
        "show ip route ospf",
        "show ip ospf database",
    ],
    "BGP": [
        "show ip bgp summary",
        "show ip bgp neighbors",
        "show ip route bgp",
        "show ip bgp",
    ],
    "EIGRP": [
        "show ip eigrp neighbors",
        "show ip eigrp topology",
        "show ip route eigrp",
        "show ip eigrp interfaces",
    ],
    "Static Routing": [
        "show ip route static",
        "show ip route",
        "show running-config | include ip route",
    ],
}

SYSTEM_PROMPT_TEMPLATE = """\
You are L3-Advisor, a senior network engineer AI specialising in Layer 3 \
routing troubleshooting. {protocol_context}

{device_context_section}

When responding to a troubleshooting query, you MUST structure every answer \
using the following Markdown headers in this exact order:

## 🔎 Analysis
Describe the likely root cause(s) based on the symptoms provided. Reference \
specific protocol behaviour where relevant. If device output was provided, \
analyse it directly and highlight specific lines or values that point to the issue.

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

DEVICE_CONTEXT_PROMPT = """\
The engineer has provided the following device output for context. Analyse this \
output directly when diagnosing the issue — reference specific values, interface \
names, neighbour IDs, or anomalies you observe in it:

--- DEVICE OUTPUT START ---
{device_output}
--- DEVICE OUTPUT END ---
"""

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
    if "connected" not in st.session_state:
        st.session_state.connected = False
    if "device_output" not in st.session_state:
        st.session_state.device_output = ""

# ---------------------------------------------------------------------------
# OpenAI-compatible client
# ---------------------------------------------------------------------------
def _get_client(api_key: str) -> OpenAI:
    return OpenAI(base_url=AZURE_ENDPOINT, api_key=api_key)


def _build_system_prompt(protocol: str, device_output: str) -> str:
    context = PROTOCOL_CONTEXT.get(protocol, "")
    device_section = ""
    if device_output.strip():
        device_section = DEVICE_CONTEXT_PROMPT.format(device_output=device_output.strip())
    return SYSTEM_PROMPT_TEMPLATE.format(
        protocol_context=context,
        device_context_section=device_section,
    )


def _chat(api_key: str, protocol: str, device_output: str, messages: list[dict]) -> str:
    client = _get_client(api_key)
    system_msg = {
        "role": "system",
        "content": _build_system_prompt(protocol, device_output),
    }
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[system_msg, *messages],
        temperature=0.3,
    )
    return response.choices[0].message.content

# ---------------------------------------------------------------------------
# Export helper
# ---------------------------------------------------------------------------
def _build_audit_log(messages: list[dict], protocol: str, device_output: str) -> str:
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = [
        "=" * 70,
        " L3-ADVISOR — INCIDENT AUDIT LOG",
        "=" * 70,
        f"Generated : {timestamp}",
        f"Protocol  : {protocol}",
        f"Total turns: {len(messages)}",
        "=" * 70,
        "",
    ]

    if device_output.strip():
        lines += [
            "--- DEVICE OUTPUT PROVIDED ---",
            device_output.strip(),
            "--- END DEVICE OUTPUT ---",
            "",
        ]

    for i, msg in enumerate(messages, start=1):
        role = msg["role"].upper()
        lines.append(f"[{i}] {role}")
        lines.append("-" * 40)
        lines.append(msg["content"])
        lines.append("")

    lines += ["=" * 70, "END OF LOG", "=" * 70]
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def _render_sidebar() -> None:
    with st.sidebar:
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
        if st.session_state.device_output.strip():
            st.success("📋 Device output: **Loaded**")
        else:
            st.warning("📋 Device output: **Not provided**")

        st.divider()

        # Export button
        if st.session_state.messages:
            audit_log = _build_audit_log(
                st.session_state.messages,
                st.session_state.protocol,
                st.session_state.device_output,
            )
            st.download_button(
                label="📥 Download Incident Audit Log",
                data=audit_log,
                file_name=f"l3_advisor_audit_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.device_output = ""
            st.rerun()

# ---------------------------------------------------------------------------
# Device context panel
# ---------------------------------------------------------------------------
def _render_device_context_panel() -> None:
    """Collapsible panel for pasting show command output."""
    protocol = st.session_state.protocol
    suggested = SHOW_COMMAND_TEMPLATES.get(protocol, [])
    hint = ", ".join(f"`{cmd}`" for cmd in suggested)

    with st.expander("📋 Paste Device Output (optional but recommended)", expanded=False):
        st.markdown(
            f"Paste output from your device to get **device-specific** diagnosis "
            f"instead of generic advice. Suggested commands for **{protocol}**: {hint}"
        )

        col1, col2 = st.columns([5, 1])
        with col1:
            device_output = st.text_area(
                "Device output",
                value=st.session_state.device_output,
                height=200,
                placeholder=(
                    f"Paste your '{suggested[0] if suggested else 'show ip route'}' "
                    f"output here…"
                ),
                label_visibility="collapsed",
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ Apply", use_container_width=True):
                st.session_state.device_output = device_output
                st.success("Loaded!")
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.device_output = ""
                st.rerun()

        # Live preview of what's loaded
        if st.session_state.device_output.strip():
            char_count = len(st.session_state.device_output)
            line_count = st.session_state.device_output.count("\n") + 1
            st.caption(f"✅ {line_count} lines · {char_count} characters loaded into context")

# ---------------------------------------------------------------------------
# Main chat interface
# ---------------------------------------------------------------------------
def _render_chat() -> None:
    st.title("🌐 L3-Advisor")
    st.caption(
        f"AI-powered Layer 3 troubleshooting assistant — "
        f"currently focused on **{st.session_state.protocol}**"
    )

    # Device context panel sits above the chat
    _render_device_context_panel()

    st.divider()

    # Render existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Describe your routing issue…"):
        if not st.session_state.api_key:
            st.error(
                "⚠️ No API key configured. Please enter your GitHub / Azure "
                "token in the sidebar before sending a message."
            )
            return

        # Hint if no device output is provided
        if not st.session_state.device_output.strip() and not st.session_state.messages:
            st.info(
                "💡 **Tip:** Paste device output in the panel above for more accurate, "
                "device-specific diagnosis."
            )

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analysing…"):
                try:
                    reply = _chat(
                        api_key=st.session_state.api_key,
                        protocol=st.session_state.protocol,
                        device_output=st.session_state.device_output,
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
