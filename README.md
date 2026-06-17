<!-- markdownlint-disable MD033 -->

<p align="center">
  <h1 align="center">🚀 tracellm</h1>
  <p align="center"><i>轻量级 LLM API 调用追踪器 · Lightweight LLM Call Tracker</i></p>
</p>

<p align="center">
  <b>一个简单的 Python 装饰器，用于记录、监控和分析 LLM API 调用。</b><br>
  <b>A simple Python decorator to log, monitor, and analyze LLM API calls.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/status-alpha-orange.svg" alt="Alpha">
</p>

---

**English** · [中文](#中文文档)

---

## English

### What is tracellm?

**tracellm** is a lightweight, zero-dependency Python package that adds observability to your LLM API calls with a single `@track_llm_call` decorator.

Inspired by [Usage AI](https://usage.ai) ($0 → millions ARR in <1yr), tracellm helps you track:

- **Which model** was called
- **How long** it took (latency)
- **How many tokens** were used
- **Error rate** tracking across all calls

All data is stored locally as JSONL files (rotated at 1000 entries, no external dependencies needed).

### Quick Start

```bash
pip install tracellm
```

Decorate any LLM call function:

```python
from tracellm import track_llm_call, compute_stats

@track_llm_call(model="gpt-4", max_retries=2)
def call_openai(prompt: str) -> str:
    # Your LLM API call here
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Use normally
result = call_openai("What is the meaning of life?")

# Get aggregated stats
stats = call_openai.stats()
# or: stats = compute_stats()
print(stats)
# {
#   "total_calls": 42,
#   "avg_latency_ms": 1234.56,
#   "error_rate": 0.0238,
#   "calls_by_model": {"gpt-4": 42},
#   "calls_by_function": {"call_openai": 42}
# }
```

### Features

| Feature | Description |
|---------|-------------|
| ✅ **Sync & Async** | Works with both sync and async functions |
| ✅ **Auto-retry** | Configurable `max_retries` with exponential backoff |
| ✅ **Token tracking** | Auto-extracts token usage from common response formats (OpenAI, Anthropic, LiteLLM) |
| ✅ **Error handling** | Catches and logs errors without crashing your app |
| ✅ **JSONL storage** | Append-only log format, auto-rotates at 1000 entries |
| ✅ **Stats API** | Built-in `compute_stats()` for aggregation |
| ✅ **Zero deps** | Pure Python, no external dependencies |

### Advanced Usage

#### Async Functions

```python
@track_llm_call(model="gpt-4")
async def async_call(prompt: str) -> str:
    response = await async_client.chat.completions.create(...)
    return response.choices[0].message.content

result = await async_call("Hello!")
```

#### Custom Log Directory

```python
from tracellm import track_llm_call, compute_stats

@track_llm_call(model="claude-3", log_dir="/var/log/tracellm")
def my_call(prompt: str) -> str:
    ...

stats = compute_stats(log_dir="/var/log/tracellm")
```

#### Error Handling

Errors are logged but never crash the caller (they're re-raised after logging):

```python
@track_llm_call(model="gpt-4", max_retries=3)
def flaky_call(prompt: str) -> str:
    if some_condition:
        raise RuntimeError("API error")
    return "OK"

try:
    result = flaky_call("test")
except RuntimeError:
    # Error is already logged to JSONL
    pass
```

#### Real AI API Wrapper Example

```python
import os
from openai import OpenAI
from tracellm import track_llm_call

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@track_llm_call(model="gpt-4o", max_retries=2)
def ask_gpt4o(prompt: str, temperature: float = 0.7) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content

@track_llm_call(model="claude-3-opus", max_retries=1)
def ask_claude(prompt: str) -> str:
    # ... your Anthropic SDK call
    pass
```

### Roadmap

- [x] Core decorator (sync + async)
- [x] JSONL file storage with rotation
- [x] Stats aggregation
- [ ] Cost tracking (price per model)
- [ ] Dashboard (local web UI)
- [ ] Export to CSV/Parquet
- [ ] Integration with LangChain / LlamaIndex
- [ ] OpenTelemetry export
- [ ] Batch log query API
- [ ] CLI tool: `tracellm stats`, `tracellm logs`

### GitHub Setup

Run the following to push tracellm to GitHub (replace `YOUR_USERNAME`):

```bash
# Create repository on GitHub first (empty, no README, no license)
# Then:
cd ~/llm-call-tracker
git init
git add .
git commit -m "feat: initial tracellm MVP — LLM call tracking decorator"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tracellm.git
git push -u origin main

# Install from local source for development
pip install -e .
```

---

## 中文文档

### tracellm 是什么？

**tracellm** 是一个轻量级的 Python 包，通过一个简单的 `@track_llm_call` 装饰器，为你的 LLM API 调用添加可观测性。

灵感来源于 [Usage AI](https://usage.ai)（从 0 到数百万美元年经常性收入，不到一年时间），tracellm 帮助你追踪：

- **调用了哪个模型**
- **调用耗时**（延迟时间）
- **使用了多少 token**
- **错误率**统计

所有数据以 JSONL 格式本地存储（每 1000 条自动轮转），零外部依赖。

### 快速开始

```bash
pip install tracellm
```

在你的 LLM 调用函数上添加装饰器：

```python
from tracellm import track_llm_call, compute_stats

@track_llm_call(model="gpt-4", max_retries=2)
def call_openai(prompt: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 正常使用
result = call_openai("生命的意义是什么？")

# 获取聚合统计信息
stats = call_openai.stats()
# 或: stats = compute_stats()
print(stats)
# {
#   "total_calls": 42,
#   "avg_latency_ms": 1234.56,
#   "error_rate": 0.0238,
#   "calls_by_model": {"gpt-4": 42},
#   "calls_by_function": {"call_openai": 42}
# }
```

### 功能特性

| 功能 | 说明 |
|------|------|
| ✅ **同步 & 异步** | 同时支持同步和异步函数 |
| ✅ **自动重试** | 可配置最大重试次数，带指数退避 |
| ✅ **Token 追踪** | 自动从常见响应格式提取 token 用量（OpenAI、Anthropic、LiteLLM） |
| ✅ **错误处理** | 记录错误但不影响程序运行 |
| ✅ **JSONL 存储** | 追加写入日志格式，1000 条自动轮转 |
| ✅ **统计 API** | 内置 `compute_stats()` 聚合函数 |
| ✅ **零依赖** | 纯 Python 实现，无需安装额外包 |

### 高级用法

#### 异步函数

```python
@track_llm_call(model="gpt-4")
async def async_call(prompt: str) -> str:
    response = await async_client.chat.completions.create(...)
    return response.choices[0].message.content

result = await async_call("你好！")
```

#### 自定义日志目录

```python
from tracellm import track_llm_call, compute_stats

@track_llm_call(model="claude-3", log_dir="/var/log/tracellm")
def my_call(prompt: str) -> str:
    ...

stats = compute_stats(log_dir="/var/log/tracellm")
```

#### 错误处理

错误会被记录但不会导致程序崩溃（记录后重新抛出）：

```python
@track_llm_call(model="gpt-4", max_retries=3)
def flaky_call(prompt: str) -> str:
    if some_condition:
        raise RuntimeError("API error")
    return "OK"

try:
    result = flaky_call("test")
except RuntimeError:
    # 错误已记录到 JSONL 文件
    pass
```

#### 真实 AI API 封装示例

```python
import os
from openai import OpenAI
from tracellm import track_llm_call

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@track_llm_call(model="gpt-4o", max_retries=2)
def ask_gpt4o(prompt: str, temperature: float = 0.7) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content

@track_llm_call(model="claude-3-opus", max_retries=1)
def ask_claude(prompt: str) -> str:
    # ... 你的 Anthropic SDK 调用
    pass
```

### 开发路线图

- [x] 核心装饰器（同步 + 异步）
- [x] JSONL 文件存储及轮转
- [x] 统计聚合
- [ ] 成本追踪（按模型计价）
- [ ] 仪表盘（本地 Web UI）
- [ ] 导出 CSV/Parquet
- [ ] 集成 LangChain / LlamaIndex
- [ ] OpenTelemetry 导出
- [ ] 批量日志查询 API
- [ ] CLI 工具：`tracellm stats`，`tracellm logs`

### GitHub 部署

运行以下命令将 tracellm 推送到 GitHub（将 `YOUR_USERNAME` 替换为你的用户名）：

```bash
# 先在 GitHub 上创建仓库（空的，不要 README 和 license）
# 然后：
cd ~/llm-call-tracker
git init
git add .
git commit -m "feat: initial tracellm MVP — LLM call tracking decorator"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tracellm.git
git push -u origin main

# 本地开发安装
pip install -e .
```

---

<p align="center">
  <b>Made with ❤️ for the LLM community</b><br>
  <i>Built by Hermes Agent</i>
</p>
