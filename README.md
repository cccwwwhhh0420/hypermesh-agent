# HyperMesh AI Command Center (HyperMesh AI Agent)

<p align="center">
  <a href="README.md"><b>English</b></a> |
  <a href="README_zh.md"><b>简体中文</b></a>
</p>

---

HyperMesh AI Agent is an autonomous, lightweight AI agent command-line system built for Altair HyperMesh 2022.
Powered by a ReAct (Reasoning + Acting) autonomous inference cycle, domain-specific CAE prompt engineering, an offline knowledge base of 3,650+ official HyperMesh Tcl commands, and a local bidirectional TCP bridge, it enables large language models to perform real-time CAE modeling automation, finite element state perception, and human-AI collaborative workflows.

---

## Key Features

1. Lightweight and Decoupled Architecture:
   - Pure Python implementation with zero Node.js or web runtime dependencies.
2. Built-in 3,650+ Tcl Command Knowledge Base:
   - Complete offline index of official HyperMesh 2022 command documentation and syntax parameters.
   - Built-in tool dynamic retrieval for signatures, requirements, and official code examples.
3. Autonomous ReAct Closed-Loop Execution:
   - Operates through [Task Analysis -> Manual Lookup -> Tcl Generation -> TCP Bridge Execution -> State Sensing -> Self-Correction], featuring automatic error capture and retries.
4. Live GUI State Perception and Diffing:
   - Real-time tracking and differential analysis of engineer modifications in the HyperMesh GUI (components, materials, properties, load collectors, nodes/elements).
5. Broad LLM Backend Compatibility:
   - Compatible with any standard OpenAI-compatible API (DeepSeek, OpenAI, Claude, vLLM, Ollama, etc.).
6. Rich Terminal Experience:
   - Streaming token output, syntax-highlighted Tcl cards, and slash command utilities.

---

## Quick Start Guide

### 1. Prerequisites

- Operating System: Windows 10 / Windows 11
- Python Version: Python 3.9 or higher
- CAE Software: Altair HyperMesh 2022 (or API-compatible version)

### 2. Clone Repository and Setup Virtual Environment

Open your terminal, clone the repository, and enter the directory:

```bash
git clone https://github.com/cccwwwhhh0420/hypermesh-agent.git
cd hypermesh-agent
```

It is recommended to create an isolated Python virtual environment using Conda:

```bash
conda create -n hm_agent python=3.10 -y
conda activate hm_agent
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` configuration file in the project root directory from the template:

```bash
# Windows CMD
copy .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Open `.env` in any text editor and configure your model API credentials (supports any OpenAI-compatible API):

```ini
# Large Language Model API Configuration (OpenAI-compatible format)
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://your-api-endpoint.com/v1
MODEL_NAME=your_model_name_here

# HyperMesh TCP Bridge Configuration
HM_BRIDGE_HOST=127.0.0.1
HM_BRIDGE_PORT=23456
HM_TIMEOUT=300.0

# Maximum autonomous reasoning steps per conversation turn
MAX_AGENT_STEPS=15
```

---

## Execution Steps

1. **Launch Bridge in HyperMesh**:
   Open HyperMesh and your model, click top menu `File -> Run -> Tcl/Tk Script`, and select `hm_agent/mount_bridge.tcl`.
   The console will output `HyperMesh AI Bridge listening on port 23456`.

2. **Start AI Agent**:
   Ensure your Python virtual environment is activated, then run from the project root:
   ```bash
   python run.py
   ```
   Once connected, interact directly using natural language.

---

## Built-in Slash Commands

| Command | Description |
| :--- | :--- |
| `/workspace`, `/pwd` | Display active working directory, `command1.tcl`, and model file |
| `/log [n]` | View latest `n` GUI actions recorded in `command1.tcl` |
| `/status` | Query model entity counts: nodes, elements, components, loads |
| `/run <tcl>` | Send and execute raw Tcl commands directly in HyperMesh |
| `/search <query>` | Search syntax and examples across 3,650+ HyperMesh command manuals |
| `/snapshot [tag]` | Capture a JSON snapshot of current model state |
| `/diff [a] [b]` | Compare two model snapshots to inspect modifications |
| `/ping` | Test TCP connection and roundtrip latency to the HyperMesh bridge |
| `/reset` | Clear current conversational context |
| `/help` | Display command help |
| `/exit` | Exit the CLI session |

---

## Project Structure

```text
hypermesh_agent/
|-- .env.example          # Environment variable configuration template
|-- LICENSE               # Open source license (MIT)
|-- README.md             # English documentation
|-- README_zh.md          # Chinese documentation
|-- requirements.txt      # Python dependencies list
|-- run.py                # Unified application CLI entry point
`-- hm_agent/             # Core package
    |-- agent/            # ReAct agent core & prompt logic
    |-- bridge/           # TCP communication & state diffing
    |-- bridge_server/    # HyperMesh-side Tcl bridge service
    |-- docs/             # 3,650+ HyperMesh command references
    |-- tools/            # Agent tool definitions
    `-- workflows/        # CAE workflow references
```

---

## Troubleshooting (FAQ)

1. **Connection Error: Connection refused**
   - Verify HyperMesh is running and `hm_agent/mount_bridge.tcl` has been executed.
   - Use `/ping` inside the CLI to test TCP connectivity.
   - Ensure local port 23456 is not blocked by a firewall.

2. **LLM API Error or Timeout**
   - Check `DEEPSEEK_API_KEY` and `OPENAI_BASE_URL` in `.env`.

3. **Operation Timeout on Heavy Operations**
   - Increase `HM_TIMEOUT` in `.env` (default is 300.0 seconds).

---

## License

This project is licensed under the [MIT License](LICENSE).
