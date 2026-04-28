# 🌐 L3-Advisor

> **AI-powered Layer 3 network troubleshooting assistant** — get structured, protocol-aware diagnostic guidance in seconds.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![Model](https://img.shields.io/badge/Model-GPT--4o-412991?logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 What Is This?

L3-Advisor is a Streamlit-based chat interface that acts as a senior network engineer AI. You describe a routing issue, and it responds with a structured breakdown:

- **🔎 Analysis** — likely root causes tied to specific protocol behavior
- **🛠️ Resolution Steps** — numbered, sequential remediation plan
- **💻 CLI Commands** — exact diagnostic and corrective commands, ready to copy

It supports **OSPF, BGP, EIGRP, and Static Routing**, with a protocol-specific system prompt for each.

---

## ⚡ Quickstart

### 1. Clone the repo
\```bash
git clone https://github.com/meriembarhi/L3-Advisor.git
cd L3-Advisor
\```

### 2. Install dependencies
\```bash
pip install -r requirements.txt
\```

### 3. Set your API key
\```bash
export GITHUB_TOKEN=your_token_here
\```

### 4. Run
\```bash
streamlit run app.py
\```

Open http://localhost:8501 in your browser.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GITHUB_TOKEN` | ✅ Yes | Your GitHub Models / Azure Inference API key |

---

## 🧠 How It Works

\```
User describes symptom → Protocol-specific system prompt injected
→ GPT-4o via Azure AI Inference
→ 🔎 Analysis + 🛠️ Steps + 💻 CLI Commands
→ Exportable Incident Audit Log
\```

---

## 📡 Supported Protocols

| Protocol | Focus Areas |
|---|---|
| **OSPF** | Neighbor adjacency, DR/BDR, area types, SPF, redistribution |
| **BGP** | eBGP/iBGP peering, route reflectors, communities, filtering |
| **EIGRP** | DUAL algorithm, feasible successors, stuck-in-active, K-values |
| **Static Routing** | Admin distance, floating statics, recursive loops, null routes |

---

## 📥 Incident Audit Log

Export any session as a structured `.txt` log from the sidebar — useful for post-incident docs, team sharing, or change tickets.

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "feat: your feature"`
4. Push & open a Pull Request

---

## 📄 License

[MIT](./LICENSE) — **Meriem Barhi**

> *Built for network engineers who need answers fast, not documentation they already know.*
