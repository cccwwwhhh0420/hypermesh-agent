# HyperMesh 智能体命令中心 (HyperMesh AI Agent)

<p align="center">
  <a href="README.md"><b>English</b></a> |
  <a href="README_zh.md"><b>简体中文</b></a>
</p>

---

HyperMesh AI Agent 是基于 Python 开发的 HyperMesh 2022 智能体命令行交互系统。
系统基于 ReAct（Reasoning + Acting）自主推理循环，结合 CAE 领域提示工程、内置 3650+ 条 HyperMesh 官方 Tcl 指令库与本地 TCP 双向桥接机制，实现大语言模型对 HyperMesh 的实时自动化脚本调度、有限元状态感知与工程交互。

---

## 核心特性

1. 轻量独立与解耦架构：
   - 纯 Python 编写，无需配置 Node.js 或复杂前端环境，终端秒级启动。
2. 内置 3650+ 条 Tcl 指令集知识库：
   - 离线收录 HyperMesh 2022 完整官方命令手册与参数索引。
   - 智能体可通过内置工具动态检索指令语法、参数要求及官方示例。
3. ReAct 自愈式闭环控制：
   - 遵循 [任务分析 -> 检索手册 -> 生成 Tcl -> TCP 执行 -> 状态感知 -> 纠错修正] 的闭环流程，具备错误重试与自愈能力。
4. 模型状态感知与差异比对 (Diff)：
   - 支持实时捕获工程师在 HyperMesh 图形界面中的手动修改（组件、材料、属性、载荷、节点/单元等）。
5. 广泛兼容的大模型后端：
   - 兼容任意标准 OpenAI 格式接口，支持 DeepSeek、OpenAI、Claude，以及本地私有化部署的 vLLM、Ollama 等。
6. 友好的终端交互体验：
   - 支持流式打字输出、Tcl 语法高亮卡片展示及丰富的快捷斜杠指令。

---

## 快速使用指南

### 1. 环境准备

- 操作系统：Windows 10 / Windows 11
- Python 版本：Python 3.9 及以上
- CAE 软件：Altair HyperMesh 2022（或 API 兼容版本）

### 2. 克隆仓库与创建虚拟环境

打开终端，克隆仓库并进入工作目录：

```bash
git clone https://github.com/cccwwwhhh0420/hypermesh-agent.git
cd hypermesh-agent
```

建议使用 Conda 创建独立的 Python 虚拟环境：

```bash
conda create -n hm_agent python=3.10 -y
conda activate hm_agent
```

安装所需 Python 依赖：

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

从模板创建 `.env` 配置文件：

```bash
# Windows CMD
copy .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

打开 `.env` 文件，填入大模型 API 配置（支持任意 OpenAI 标准格式接口）：

```ini
# 大模型 API 配置（兼容 OpenAI、DeepSeek、Qwen、vLLM、Ollama 等任意标准接口）
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://your-api-endpoint.com/v1
MODEL_NAME=your_model_name_here

# HyperMesh TCP 桥接配置
HM_BRIDGE_HOST=127.0.0.1
HM_BRIDGE_PORT=23456
HM_TIMEOUT=300.0

# 单轮对话最大推理步数
MAX_AGENT_STEPS=15
```

---

## 运行步骤

1. **在 HyperMesh 中启动桥接**：
   打开 HyperMesh 软件及模型，点击顶部菜单 `File -> Run -> Tcl/Tk Script`，选择运行 `hm_agent/mount_bridge.tcl`。
   控制台输出 `HyperMesh AI Bridge listening on port 23456` 即表示挂载成功。

2. **在终端启动智能体**：
   确保已激活虚拟环境，在项目根目录下执行：
   ```bash
   python run.py
   ```
   连接成功后，即可直接使用自然语言输入建模与分析指令。

---

## 常用快捷指令

在交互终端中支持以下斜杠指令：

| 指令 | 说明 |
| :--- | :--- |
| `/workspace`, `/pwd` | 查看当前工作路径、`command1.tcl` 及模型文件 |
| `/log [n]` | 查看当前工作目录下最近 n 条用户 GUI 操作日志 |
| `/status` | 查询模型统计数据（节点、单元、组件、载荷等） |
| `/run <tcl>` | 向 HyperMesh 发送执行原生 Tcl 脚本 |
| `/search <query>` | 检索 3650+ 条 HyperMesh 指令语法与示例 |
| `/snapshot [tag]` | 拍摄当前模型状态快照 |
| `/diff [a] [b]` | 比对两次快照差异 |
| `/ping` | 测试与 HyperMesh 桥接通信及延迟 |
| `/reset` | 清除当前上下文历史 |
| `/help` | 查看帮助与指令列表 |
| `/exit` | 退出终端程序 |

---

## 项目结构

```text
hypermesh_agent/
|-- .env.example          # 环境变量配置模板
|-- LICENSE               # 开源许可协议 (MIT)
|-- README.md             # 英文说明文档
|-- README_zh.md          # 中文说明文档
|-- requirements.txt      # Python 依赖清单
|-- run.py                # 命令行统一启动入口
`-- hm_agent/             # 核心模块包
    |-- agent/            # ReAct 智能体核心逻辑与提示工程
    |-- bridge/           # HyperMesh TCP 通信与状态感知
    |-- bridge_server/    # HyperMesh 端 Tcl 桥接服务
    |-- docs/             # 3650+ 条 HyperMesh 命令参考知识库
    |-- tools/            # 智能体工具注册库
    `-- workflows/        # CAE 典型工作流参考
```

---

## 常见问题 (FAQ)

1. **连接失败：提示 Connection refused**
   - 确认 HyperMesh 已启动并运行了 `hm_agent/mount_bridge.tcl`。
   - 可在终端中使用 `/ping` 指令测试连通性。
   - 检查防火墙是否拦截了本地 23456 端口。

2. **大模型 API 报错或超时**
   - 检查 `.env` 中的 `DEEPSEEK_API_KEY` 与 `OPENAI_BASE_URL` 是否正确配置。

3. **复杂网格划分或几何操作超时**
   - 可在 `.env` 中调大 `HM_TIMEOUT`（默认为 300.0 秒）。

---

## 开源许可证

本项目基于 [MIT License](LICENSE) 开源协议。
