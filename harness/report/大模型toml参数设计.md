# 大模型 TOML 参数设计

> **核心立场**：智能体与大模型 provider 之间的交互应遵循**三层架构**（网络层透传 / 解析层严谨 / 应用层抽象），口号"**传输的时候要透传，解析的时候要严谨**"。
> **白名单范围**：本项目 v1 适配 **26 个 LangChain 官方支持的世界主流 provider**——6 个原生闭源大厂 + 8 个 OpenAI 兼容（中文 7：qwen 默认 / doubao / kimi 默认 / MiniMax / zhipu / tencent / stepfun；国际 1：openai-compatible 元 provider）+ 8 个国际云推理 + 1 个本地 Ollama + 1 个 ChatOpenRouter 元 provider + 2 个多平台路由（meta / xiaomi）+ 4 个推理模型专用类（`ChatDeepSeek` / `ChatQwQ` for QwQ / `ChatQwen` for Qwen3 / `ChatMoonshot`）。详见 §3.1。**v1 不自研任何解析类**，所有 provider 复用 LangChain 官方类。**v2+ 候选**（3 个需自研：baidu / iflytek / sensetime）见 §3.5。**黑名单与暂不支持清单当前均空**——任何 provider 入列须按 §3.0 Provider 治理原则走硬理由 + GitHub issue + 社区评审 ≥14 天流程。
> **配置理念**：**仿效 Cherry Studio 的 per-provider schema + 明文鉴权**，但**不仿效其"自定义参数"口子**——donkey 用 LangChain 严格 schema 保证字段拼写错误在 F002 load 阶段就抓到；`api_key` 仅允许 TOML 明文（不读环境变量，保证 workspace 跨 OS 行为一致）；`api_host` 23 个 provider 可选（Ollama 允许 `api_host = "default"` 特殊值；`openai-compatible` / `meta` / `databricks` 必填）。
> **本报告立场**：**v1 100% 复用 LangChain**——6 个 provider 走独立 LangChain 类（`ChatOpenAI` / `ChatAnthropic` / `ChatGoogleGenerativeAI` / `ChatOllama` / `ChatXAI` / `ChatMistralAI`）、8 个走国际云推理类（`ChatBedrock` / `ChatGroq` / `ChatFireworks` / `ChatTogether` / `ChatCohere` / `ChatPerplexity` / `ChatDatabricks` / `ChatCerebras`）、8 个 OpenAI 兼容薄包装（中文 7：qwen 默认 / doubao / kimi 默认 / MiniMax / zhipu / tencent / stepfun；国际 1：openai-compatible 元 provider）+ 1 个 `ChatOpenRouter`（openrouter 元 provider）、2 个多平台路由（meta / xiaomi）、4 个推理模型专用类（`ChatDeepSeek` / `ChatQwQ` / `ChatQwen` / `ChatMoonshot` 保留 reasoning_content）。**零自研**。详见 §3.2 / §15。
>
> **核心补充**：
> - **TOML loader 强约束**（详见 §9.1.1）：donkey 解析 TOML 时必须把缺失的 `api_key` 映射为 `""`（空串），**绝不返回 `None`**，否则触发 LangChain `_resolve_gateway_config` 内部 env var 回退（`OPENAI_API_KEY` 等），违背"donkey 不读 env var"立场。
> - **`[bedrock]` 改用独立 `aws_*` 字段**（详见 §8）：与 §9.1 立场完全对齐——通过 `boto3.Session(aws_access_key_id=..., aws_secret_access_key=..., region_name=...)` 显式构造，boto3 不会读 env var 或 `~/.aws/credentials`。
> **本文档不依赖任何特定项目**：纯通用调研，可被任何基于 LangChain 的智能体项目直接参考。
>
> **实测校验**：本报告的核心主张已由端到端 demo `harness/demo/about_providers/provider.py` 用**两个真实模型**（MiniMax-M3 / deepseek-v4-flash）逐条验证，**63 项断言全绿 / 0 FAIL / 0 SKIP**；逐条结论见 demo 的 docstring。

---

## 0. 阅读路径

| 角色 | 优先阅读 |
|---|---|
| 项目 Maintainer 决策 | §1（核心主张）+ §2（三层架构）+ §3（白名单）+ §16（决策速查） |
| F001-P2 / F002-P1 spec 作者 | §7（全局结构）+ §8（每个 provider schema）+ §9（鉴权）+ §10（base_url） |
| provider 解析代码作者 | §2.3（解析层原则）+ §15（解析代码结构）+ §8（具体 provider 参数） |
| Web UI 设计师 | §12（Web UI 考量） |
| 安全 / 审计 | §13（安全性考量） |
| 想知道"未来怎么扩展" | §14（扩展性） |
| 赶时间 | §17（一句话总结） |

---

## 1. 核心主张与设计原则

### 1.1 被否决的早期方案

早期推荐方案（单一 `[provider]` 表 + 透传扩展口 + 环境变量鉴权）存在以下不可接受的问题：

| 被否决的方案 | 问题 | 对应原则 |
|---|---|---|
| 单一 `[provider]` + `[provider.generation]` 表跨协议统一 | 抹平了各 provider 字段差异；用户填 `reasoning_effort` 时不知道它对哪些 provider 有效 | P-1 |
| `[provider.extra]` 透传扩展口 | 透传 = 不解析 = 字段拼写错误延迟到运行时才被发现，违反"解析严谨"原则；schema 漂移风险高 | P-5 |
| 鉴权按"协议专属环境变量 > `LLM_API_KEY` > TOML 字段"优先级链 | 跨 OS 环境变量语义不一致，workspace 移植到新机器后行为不可控；违反 workspace 高度可移植性目标 | P-2 |
| `base_url` 按协议分派必填性 | 增加用户认知负担；Ollama 用户首次配置要查"base_url 是不是必填" | P-3 |
| 未限定 provider 白名单 | 冷僻 provider 的小众参数（如某些海外 / 国内小众厂商的"神秘字段"）拖入 schema，永无止境 | P-4 |

### 1.2 核心主张

> **1. 解析层**：由于每个 provider 的数据格式（messages、tool、usage 等）都不一样，**在应用中的数据解析层应该为不同的 provider 逐个开发数据解析 class，解析必须严谨**。
>
> **2. 应用层**：为了方便开发者，需要从不同的 provider 数据格式中提取相同数据，**进行高级抽象**，开发者只需要使用这些高级抽象即可，无需关心底层如何实现（LangChain 已实现这层抽象，本项目直接复用）。
>
> **3. 网络层**：在传输解析层发出的数据，并返回响应时，**需要保持透传**，网络层不应该修改任何数据。

### 1.3 五条设计原则

| 编号 | 原则 | 理由 |
|---|---|---|
| **P-1** | **每个 provider 一个独立 TOML schema**（无统一 `[provider.generation]` 表） | 字段语义清晰；用户写配置时知道"这是 OpenAI 专属 / Anthropic 专属"；解析层无需按协议分派 |
| **P-2** | **`api_key` 仅允许 TOML 明文，不读环境变量** | 跨 OS 环境变量不一致；workspace 移植后行为不可控；用户自行承担 git 泄露风险 |
| **P-3** | **`api_host` 对所有 provider 可选**（Ollama 允许 `api_host = "default"` 特殊值） | 减少用户认知负担；Ollama 小白用户友好 |
| **P-4** | **Provider 白名单硬限**（v1 = 26 家；v2+ 候选 3 家需自研；v1 范围内无永久黑名单 / 无暂不支持清单成员） | 不为冷僻 provider 写代码；v1 100% 复用 LangChain；v2+ 候选按 §3.5 流程添加；列入永久黑名单必须按 §3.0 原则走硬理由 + GitHub issue 流程 |
| **P-5** | **解析代码尽量复用 LangChain；不解析的字段拒绝写入 schema** | 避免 `[provider.extra]` 透传陷阱；字段拼写错误在 F002 load 阶段就能抓到 |

### 1.4 仿效对象：Cherry Studio

Cherry Studio 是国内流行的多 provider 桌面 AI 客户端，其 LLM 配置设计值得借鉴：

- **每个 provider 一个独立配置节**（`[openai]` / `[anthropic]` / `[ollama]` / ...）；
- **`apiKey` + `apiHost`（即 baseURL）是 provider 顶层字段**；
- **每个 provider 下挂一个 `models` 列表**，每个 model 可独立配置生成参数；
- **不**使用统一 schema + 扩展口模式；
- **鉴权 key 明文写死在用户配置文件中**（不读环境变量）。

**本项目沿用** Cherry Studio 的 **per-provider schema + 明文鉴权** + **models 列表** 三项核心；
**不沿用** Cherry Studio 的 **"自定义参数"口子**——Cherry Studio 允许用户在 GUI 里填任意 key=value（用于适配某些国内 / 海外小众 provider 的"神秘字段"），但 donkey 走 LangChain 严格 schema 路线（P-5），所有已知参数显式声明在 schema，字段拼写错误在 F002 load 阶段就抓到，不延迟到运行时。

本项目在 schema 严格性、解析严谨性、跨协议抽象上用 LangChain 加固。

---

## 2. 设计哲学：三层架构

### 2.1 三层架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    应用层 (Application Layer)                     │
│  - 高级抽象：ChatModel.invoke(messages) → AIMessage              │
│  - 工具调用：tool_calls / structured output 统一接口             │
│  - 复用 LangChain BaseChatModel 抽象                             │
└─────────────────────────────────────────────────────────────────┘
                            ↑ 高级抽象
┌─────────────────────────────────────────────────────────────────┐
│                   解析层 (Parsing Layer)                          │
│  - per-provider 解析 class：ProviderParser                       │
│    ├── openai.py    → OpenAIRequestParser / OpenAIResponseParser │
│    ├── anthropic.py → AnthropicRequestParser / ...              │
│    ├── ollama.py    → OllamaRequestParser / ...                 │
│    └── ... (26 个 provider)                                     │
│  - 输入：langchain 统一消息 + 工具 schema                          │
│  - 输出：provider 专有 JSON / SSE bytes                          │
│  - 输入：provider 专有响应                                         │
│  - 输出：langchain AIMessage / ToolCall / UsageMetadata          │
│  - 严谨：每个字段类型 / 取值范围 / 必填性按 provider 文档强校验     │
└─────────────────────────────────────────────────────────────────┘
                            ↑ 解析后的结构化数据
┌─────────────────────────────────────────────────────────────────┐
│                    网络层 (Network Layer)                         │
│  - 透传 HTTP：httpx.AsyncClient.send(request) → response         │
│  - 不解析任何 body；不修改任何 header；不重试                       │
│  - 仅负责：建立连接 / 发送 bytes / 接收 bytes / 超时切断 / 流式分片 │
│  - 上游传什么就发什么；下游返回什么就交给上游                       │
└─────────────────────────────────────────────────────────────────┘
                            ↑ 透明传输
┌─────────────────────────────────────────────────────────────────┐
│                      provider API                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 网络层：透传

**职责**：

- 用 `httpx.AsyncClient` 发起 HTTP / HTTPS / SSE 请求；
- **不**解析 body（bytes 直接发送）；
- **不**修改 header（仅在 transport wrapper 注入 `Authorization` / `Content-Type` 等必须 header）；
- **不**重试（重试是 LangChain `max_retries` 中间件的事，不在 transport）；
- **不**记录日志中的 body（避免密钥 / 用户隐私泄露）。

**接口**（伪代码）：

```python
class NetworkTransport:
    def __init__(self, timeout: float, max_retries: int):
        self._client = httpx.AsyncClient(timeout=timeout)

    async def send(self, request: PreparedRequest) -> Response:
        """透传：仅做连接管理 + 超时切断。"""
        return await self._client.send(request)
```

**禁止**：

- ❌ 在 transport 层调用 `json.loads(response.body)`；
- ❌ 在 transport 层判断 `response.status_code == 429` 重试；
- ❌ 在 transport 层修改 body（即使是"为了让请求更友好"）；
- ❌ 在 transport 层捕获业务异常（如 `ModelAuthenticationError`）—— 这些归解析层。

### 2.3 解析层：严谨

**职责**（per provider 一个 class）：

- **请求解析**：`RequestParser.parse(messages, tools, **params) -> bytes` —— 把 LangChain 统一 schema 翻译成 provider 专有 JSON；
- **响应解析**：`ResponseParser.parse(response: bytes) -> AIMessage` —— 把 provider 专有响应翻译回 LangChain 统一 schema；
- **流式响应解析**：`StreamParser.parse(chunk: bytes) -> Iterator[AIMessageChunk]` —— 逐 token 翻译；
- **工具调用解析**：把 LangChain `tool_calls` 翻译成 provider 专有格式（如 OpenAI 的 `tools` 数组、Anthropic 的 `tools` + `tool_choice`）；
- **usage 解析**：把 provider 专有的 `usage`（OpenAI `prompt_tokens` / Anthropic `input_tokens` / ...）翻译成统一的 `UsageMetadata`（`input_tokens` / `output_tokens` / `total_tokens`）。

**严谨要求**：

- 任何 provider-specific 字段（如 OpenAI `organization`、Anthropic `thinking.budget_tokens`、Ollama `num_ctx`）都**有 schema 定义**（Pydantic Model 或 dataclass）；
- 字段类型 / 取值范围 / 必填性按 provider 官方文档**强校验**；
- **不**接受未在 schema 定义的字段（拒绝写入配置文件 —— F002 load 阶段报错）；
- 字段拼写错误**立即报错**（不延迟到运行时）。

**示例**（OpenAI 解析层伪代码）：

```python
# donkey/core/llm/providers/openai.py

class OpenAIRequestParser:
    """OpenAI Chat Completions API 请求解析器。"""

    def parse(self, messages: list[BaseMessage], tools: list[BaseTool], **params) -> bytes:
        payload = {
            "model": params["model_name"],
            "messages": [_convert_message(m) for m in messages],
        }
        if "max_tokens" in params:
            payload["max_completion_tokens"] = params["max_tokens"]  # o-series
        if "temperature" in params:
            payload["temperature"] = params["temperature"]
        # ... 严谨按 OpenAI 文档每个字段
        if tools:
            payload["tools"] = [_convert_tool(t) for t in tools]
        return json.dumps(payload).encode("utf-8")
```

### 2.4 应用层：抽象

**职责**：

- 暴露**统一接口**给 donkey 业务代码（Agent Loop / Skills / Tools 等）；
- 复用 LangChain `BaseChatModel` 抽象（如 `ChatOpenAI` / `ChatAnthropic`）；
- **开发者不感知 provider 差异**：调用 `model.invoke(messages)` 即可；
- 业务代码只关心：`HumanMessage` / `AIMessage` / `ToolMessage` / `AIMessageChunk` / `tool_calls` / `usage_metadata`。

**donkey 业务代码视角**：

```python
# F004-P7 业务代码（不感知 provider）
from langchain_core.messages import HumanMessage
from donkey.core.llm.application.facade import get_default_chat_model

model = get_default_chat_model()  # 从 provider.toml 读 default_provider
response = model.invoke([HumanMessage(content="你好")])
print(response.content)        # 统一接口
print(response.usage_metadata) # 统一接口
```

**禁止**：

- ❌ 业务代码直接 `import openai` / `import anthropic` / `import ollama`；
- ❌ 业务代码判断 `if provider == "openai": ...`（provider 分发归解析层）。

### 2.5 三层之间不变量

| 边界 | 入向不变量 | 出向不变量 |
|---|---|---|
| **网络层 → 解析层** | bytes 完整（无损） | AIMessage / 错误信息（含 status_code + body 摘要） |
| **解析层 → 应用层** | 解析后的结构化数据**符合 LangChain schema** | 翻译后的结构化数据**符合 provider 专有 schema**（由 provider 文档保证） |
| **应用层 → 解析层** | 业务消息 + 工具调用（LangChain schema） | provider-specific JSON / SSE bytes |
| **解析层 → 网络层** | provider-specific JSON / SSE bytes | HTTP request（method / url / headers / body） |

---

## 3. Provider 白名单与范围治理

### 3.0 Provider 治理原则（本节具有最高优先级）

> **本节是 §3、§13.4、§14.7 等所有 provider 范围决策的**最高优先级原则****。若其它小节与本原则冲突，以本节为准。

本项目对所有 LLM provider **一视同仁**，不因**任何**非技术性理由（个人好恶、政治立场、地缘偏好、商业关系、社交舆论等）将 provider 列入黑名单 / 限制名单 / 暂不支持清单 / 排除候选名单。

**入选 / 剔除的唯一标准**：

| 维度 | 性质 | 可作为决策依据 | 不可作为决策依据 |
|---|---|---|---|
| 技术可行性 | **必须** | LangChain 官方支持的 provider 集合；API 协议稳定性；SDK 质量 | 维护者个人对某厂商的好恶 |
| 维护成本 | **必须** | 自研解析代码工作日估算；测试覆盖成本；升级 LangChain 时的回归风险 | 厂商所在国家 / 地区；厂商中文名谐音 |
| 生态适配度 | **必须** | 用户群体规模（PyPI 下载量、LangChain 内置）；协议标准化程度（OpenAI / Anthropic 兼容） | 社交媒体上对某厂商的褒贬 |

**约束性条款**：

1. **白名单**（§3.1）与 **v2+ 候选**（§3.5）的入选 / 排除仅由上表"必须"维度判定。
2. **永久黑名单**（§13.4）保留作为治理工具，但**仅**适用于存在**硬性合规 / 法律 / 商业禁止**的 provider：
   - 必须由 Maintainer 在 GitHub issue 公开记录硬理由（点名具体条款 / 法律 / 协议条文）；
   - 必须经用户社区评审窗口期（≥14 天）后才能写入文档；
   - 维护者个人的好恶、政治立场、地域偏好**不得**构成"硬理由"。
3. **暂不支持清单**（§14.7 `PROVIDER_DEFERRED`）作为治理工具保留，但**仅**适用于"LangChain 已支持但本项目尚未投入维护工作量"或"v2+ 自研候选暂未实现"两种技术情形：
   - 不得用于"任何形式的拒绝"——若某 provider 满足 §3.0 上表"必须"维度，**必须**进入白名单或 v2+ 候选，不得留在暂不支持清单。
4. 任何 Maintainer（包括项目当前 owner）若在白名单 / 黑名单 / 暂不支持清单中夹带非技术性依据，**视为治理事故**，下任 Maintainer 有权回退该决定且无须 Maintainer 重新决策是否"解除"。

### 3.1 白名单

> **数据源**：基于 LangChain `init_chat_model` 官方支持列表（实测 **30 个** BUILTIN_PROVIDERS，详见源码 `langchain/chat_models/base.py:56-99`）综合排序——加入 AWS Bedrock / Groq / OpenRouter / Fireworks / Together / Cohere / Perplexity / Databricks / Cerebras 共 9 个高下载量 provider，并修正 qwen / deepseek / kimi / doubao / zhipu / MiniMax / tencent / sensetime / xiaomi / stepfun 等中国/国际 provider 的 LangChain 复用策略。
>
> **⚠️ 关键细节**：langchain 1.x 的 `_BUILTIN_PROVIDERS` dict 里**没有 `"google"` 这个 provider_id**——只有 `google_anthropic_vertex` / `google_genai` / `google_vertexai` 三个 Google alias。donkey 表格里写的 `google` 是 donkey 自定义的人类可读 provider_id，需要 donkey facade 函数显式转发到 `google_genai`（即 `init_chat_model(model_provider="google_genai", ...)`，或直接构造 `ChatGoogleGenerativeAI`）。**用户 TOML 里写 `default_provider = "google"` 必须由 donkey facade 翻译，绝不能直接喂给 `init_chat_model`**，否则会抛 `ValueError: provider 'google' not in _BUILTIN_PROVIDERS`。
>
> **dedup 统计**：30 个 BUILTIN_PROVIDERS 中，AWS (4: bedrock / bedrock_converse / bedrock_mantle_anthropic / bedrock_mantle_openai) + Google (3: google_anthropic_vertex / google_genai / google_vertexai) + Azure (2: azure_ai / azure_openai) + LangSmith (1: langsmith 用 `ChatOpenAI` 作 gateway) + 其它 21 = **30 总 entry，24 独立家族**。
>
> **维护原则**：白名单外的 provider **本项目永不主动适配**；用户使用冷僻 provider 需等待后续项目代码更新。

| # | 公司/机构 | provider_id | LangChain 类 | 路线 | 主力 LLM | 主力 VLM | 备注 |
|---|---|---|---|---|---|---|---|
| **原生闭源大厂** | | | | | | | |
| 1 | OpenAI | `openai` | `ChatOpenAI` | 闭源 | GPT 系列 / o 系列推理模型 | GPT-4o / Sora | |
| 2 | Anthropic | `anthropic` | `ChatAnthropic` | 闭源 | Claude Opus 4.x/5 / Sonnet 4.5/5.5 / **Fable** / **Mythos** | Claude 原生多模态、GUI Agent | Fable/Mythos 见 LangChain 官方 profile 数据 |
| 3 | Google DeepMind | `google` | `ChatGoogleGenerativeAI` | 闭源+开放权重 | Gemini Pro / Flash；Gemma | Gemini 四模态（图文音视频） | |
| 4 | Meta | `meta` | `ChatOllama`（自托管）/ `ChatOpenAI`（Replicate/Together/Fireworks 代理） | 开放权重 | Llama 系列 | Llama 多模态 / Muse | 多平台路由：见 §5.3 |
| 5 | xAI | `xai` | `ChatXAI` | 闭源 | Grok 系列 | Grok 多模态，绑 X 实时数据 | `reasoning_effort` 顶层字段，内部走 extra_body |
| 6 | Mistral AI | `mistral` | `ChatMistralAI` | 开放权重 | Mistral Large / Medium / Small | Pixtral 系列（Apache 2.0） | LangChain 字段名 `safe_mode`（对应 API `safe_prompt`） |
| **OpenAI 兼容（中文）** | | | | | | | |
| 7 | 阿里巴巴·通义千问 | `qwen` | `ChatOpenAI`（默认通用）/`ChatQwQ`（QwQ 推理专用）/`ChatQwen`（Qwen3 + 显式 thinking） | 闭源+开源 | Qwen-Max / Qwen-Plus / QwQ-32B | Qwen-VL | 通过阿里云百炼 / DashScope API；推理模型按 model_name 后缀分派：qwq*/reasoner → `ChatQwQ`，其它 → `ChatQwen + enable_thinking=True`（详见 §15.2） |
| 8 | DeepSeek·深度求索 | `deepseek` | **`ChatDeepSeek`**（优先） | 开源为主 | DeepSeek-V / R | DeepSeek-VL / Janus / OCR | 必须用专用类保留 R1 推理过程 |
| 9 | 字节跳动·豆包 | `doubao` | `ChatOpenAI` + base_url | 闭源 | 豆包 / Seed | 豆包 Vision / 即梦 | 火山引擎方舟（Ark）API |
| 10 | 月之暗面 Kimi | `kimi` | `ChatOpenAI`（默认）/`ChatMoonshot`（备选） | 闭源+开源 | Kimi K 系列（长上下文 Agent） | Kimi-VL | 推理模型用 ChatMoonshot 保留 reasoning_content |
| 11 | 智谱 AI Zhipu/Z.ai | `zhipu` | `ChatOpenAI` + base_url | 闭源+开源 | GLM 系列 | GLM-V / CogView | bigmodel.cn，GLM-Z 推理模型受 ChatOpenAI reasoning_content 丢失影响 |
| 12 | MiniMax | `MiniMax` | **`ChatOpenAI` + base_url** | 闭源 | MiniMax-M3 / M2.7 / M2.5 / M2.1 / M2 系列 | MiniMax-M3 多模态（图视频）| **走 OpenAI 兼容协议**（`api.minimaxi.com/v1`），thinking 以 `<think>` 标签保留在 content；详见 §3.6 |
| 13 | 腾讯 | `tencent` | `ChatOpenAI` + base_url | 闭源 | 混元 Hy 系列 | 混元视觉 / 优图 | 腾讯云 TI 平台 |
| 14 | 阶跃星辰 StepFun | `stepfun` | `ChatOpenAI` + base_url | 闭源 | Step 系列 | Step 视觉 / 视频 | |
| 15 | 小米 | `xiaomi` | `ChatOpenRouter` / `ChatOllama` | 开源 | MiMo 系列 | MiMo 全模态 | OpenRouter 调用量曾居首 |
| **国际云推理 / 平台** | | | | | | | |
| 16 | AWS Bedrock | `bedrock` | `ChatBedrock` | 闭源多模型 | Claude / Llama / Mistral / Titan 等 | 多模态模型 | 8M 下载/月，B 端必备 |
| 17 | Groq | `groq` | `ChatGroq` | 闭源 | Llama 3 / Mixtral（高速推理） | — | 1M 下载/月，LPU 推理引擎 |
| 18 | Fireworks AI | `fireworks` | `ChatFireworks` | 开源+闭源 | Llama / Qwen / DeepSeek 等 | 多模态 | 564K 下载/月 |
| 19 | Together AI | `together` | `ChatTogether` | 开源+闭源 | Llama / Qwen / DeepSeek 等 | 多模态 | 50K 下载/月 |
| 20 | Cohere | `cohere` | `ChatCohere` | 闭源 | Command R+ / R | — | 550K 下载/月，企业 RAG 强项 |
| 21 | Perplexity | `perplexity` | `ChatPerplexity` | 闭源 | Sonar 系列（含联网搜索） | — | 294K 下载/月 |
| 22 | Databricks | `databricks` | `ChatDatabricks` | 闭源+开源 | DBRX / Llama 等 | — | 599K 下载/月，企业数据云 |
| 23 | Cerebras | `cerebras` | `ChatCerebras` | 开源 | Llama / Qwen（晶圆推理） | — | 157K 下载/月，WSE 推理 |
| **本地 / 元 provider** | | | | | | | |
| 24 | Ollama | `ollama` | `ChatOllama` | 本地 | Llama / Qwen / DeepSeek / Mistral 等 | 多模态 | 必填 `api_host = "default"` 等于 `http://localhost:11434` |
| 25 | OpenRouter | `openrouter` | `ChatOpenRouter` | 元 provider | 聚合 100+ 模型 | 多模态 | 840K 下载/月，统一路由；**禁止**走 ChatOpenAI + base_url（保留 `reasoning_details`） |
| 26 | OpenAI Compatible | `openai-compatible` | `ChatOpenAI` + base_url | 元 provider | — | — | 内部自建 / Newapi / Oneapi / 中转站 |

> **v1 范围**：上表 26 家 + 4 个同 provider_id 的推理模型专用类（`ChatDeepSeek` / `ChatQwQ` for QwQ / `ChatQwen` for Qwen3 / `ChatMoonshot`），总计 26 个 provider_id。**v1 零自研**。

### 3.5 v2+ 候选清单（推迟自研的 provider）

> **v1 决策**：本项目 v1 **不实现任何自研解析类**。所有 provider 复用 LangChain 官方类实现。
> **v2+ 候选**：以下 3 个 provider 因鉴权 / 协议特殊、LangChain 无官方包装，需要 v2+ 启动自研。详见 §14.6 实现路线图。

| # | 公司/机构 | provider_id | LangChain 类 | 协议 | 自研理由 | 估算工作量 |
|---|---|---|---|---|---|---|
| V2-1 | 百度 | `baidu` | ❌ 无官方类 | OAuth 2.0 client_credentials + ERNIE 私有协议 + SSE | access_token 缓存 + 过期刷新 + 多 endpoint 路由 | 2-3 人日 |
| V2-2 | 科大讯飞 | `iflytek` | ❌ 无官方类 | WebSocket + HMAC-SHA256 签名 + 长连接心跳 | 双模态（文本 + 音频）+ 签名算法 + 心跳保活 | 5-7 人日 |
| V2-3 | 商汤科技 | `sensetime` | ❌ 无官方类 | SenseNova 私有协议 | 私有化交付，无公开 SDK 文档 | 未调研，无法估算 |

**v2+ 候选处理**：
- v1 阶段用户配置 `[baidu]` / `[iflytek]` / `[sensetime]` → F002 load 报错（exit 11）：`ProviderTomlScopeError: provider 'X' 推迟到 v2+ 实现`
- v2+ 启动时按 §14.6 流程实现自研解析类
- v1 用户改用 `openai-compatible` provider + 自行实现 HTTP 调用作为过渡方案（不推荐）

### 3.2 兼容性矩阵

> 注：标 "OpenAI 兼容" 的 provider **可复用 `ChatOpenAI` 类**，但 base_url 必填。

| provider | 鉴权方式 | 复用 LangChain 类 | 需自研解析类？ |
|---|---|---|---|
| openai | api_key | `ChatOpenAI` | ❌（完全复用） |
| anthropic | api_key | `ChatAnthropic` | ❌（完全复用） |
| google | api_key | `ChatGoogleGenerativeAI` | ❌（完全复用） |
| ollama | 一般无 | `ChatOllama` | ❌（完全复用） |
| meta | 取决于平台 | `ChatOllama` / 第三方 | ⚠️ 取决于平台（自托管用 ollama） |
| xai | api_key | `ChatXAI` | ❌（完全复用） |
| mistral | api_key | `ChatMistralAI` | ❌（完全复用） |
| qwen | api_key | `ChatOpenAI` + 自定义 base_url（默认通用）；`ChatQwQ`（QwQ 推理模型）；`ChatQwen`（Qwen3 + 显式 thinking） | ⚠️ 轻量 |
| deepseek | api_key | **`ChatDeepSeek`**（专用类） | ❌（完全复用） |
| doubao | api_key | `ChatOpenAI` + 自定义 base_url | ⚠️ 轻量 |
| kimi | api_key | `ChatOpenAI`（默认）；`ChatMoonshot`（thinking 模型） | ⚠️ 轻量 |
| zhipu | api_key | `ChatOpenAI` + 自定义 base_url | ⚠️ 轻量 |
| MiniMax | api_key | `ChatOpenAI` + 自定义 base_url（默认 OpenAI 兼容端点 `api.minimaxi.com/v1`，适配 Coding Plan 的 `sk-cp-` 密钥）| ⚠️ 轻量 |
| tencent | api_key | `ChatOpenAI` + 自定义 base_url | ⚠️ 轻量 |
| xiaomi | 取决于平台 | `ChatOpenAI` / OpenRouter | ⚠️ 轻量 |
| stepfun | api_key | `ChatOpenAI` + 自定义 base_url | ⚠️ 轻量 |
| openai-compatible | api_key | `ChatOpenAI` + 自定义 base_url | ⚠️ 轻量（base_url 必填） |
| bedrock | AWS credentials | `ChatBedrock` | ❌（完全复用） |
| groq | api_key | `ChatGroq` | ❌（完全复用） |
| fireworks | api_key | `ChatFireworks` | ❌（完全复用） |
| together | api_key | `ChatTogether` | ❌（完全复用） |
| cohere | api_key | `ChatCohere` | ❌（完全复用） |
| perplexity | api_key | `ChatPerplexity` | ❌（完全复用） |
| databricks | access_token | `ChatDatabricks` | ❌（完全复用） |
| cerebras | api_key | `ChatCerebras` | ❌（完全复用） |
| openrouter | api_key | `ChatOpenRouter` | ❌（完全复用，保留 reasoning_details） |
| ~~baidu~~ | — | — | 🚫 v1 不支持；推迟 v2+ |
| ~~iflytek~~ | — | — | 🚫 v1 不支持；推迟 v2+ |
| ~~sensetime~~ | — | — | 🚫 v1 不支持；推迟 v2+ |

**关键观察**（26 家 v1 provider 的**互斥**归类——每家只归一类）：

- **14 个完全复用独立 LangChain 类**（`ChatOpenAI` / `ChatAnthropic` / `ChatGoogleGenerativeAI` / `ChatOllama` / `ChatXAI` / `ChatMistralAI` / `ChatBedrock` / `ChatGroq` / `ChatFireworks` / `ChatTogether` / `ChatCohere` / `ChatPerplexity` / `ChatDatabricks` / `ChatCerebras`），零修改；
- **8 个走 `ChatOpenAI + base_url`**（qwen 默认 / doubao / kimi 默认 / MiniMax / tencent / stepfun / zhipu / openai-compatible 元 provider）；
- **1 个走 `ChatOpenRouter`**（openrouter 元 provider，**保留 `reasoning_content` AND `reasoning_details`**）；
- **2 个多平台路由**（meta / xiaomi——xiaomi 默认 ChatOpenRouter / ChatOllama，meta 默认 ChatOllama）；
- **1 个走推理专用类**（deepseek → **`ChatDeepSeek`**）；
- **合计 14 + 8 + 1 + 2 + 1 = 26** ✓；
- **另有 3 个"推理模型替代类"**（`ChatQwQ` for QwQ / `ChatQwen` for Qwen3 / `ChatMoonshot` for Kimi）——它们是 qwen / kimi 两家 provider 的**运行时按 model_name 分派的替代类**，**不额外计 provider 数**（详见 §15.2）；
- **v1 零自研**；**v2+ 候选 3 个**（baidu / iflytek / sensetime）见 §3.5。
- ⚠️ **关键警告**：含推理模型（DeepSeek-R1、Kimi-K2、智谱 GLM-Z、QwQ 系列、Qwen3-thinking、MiniMax-M3 等）的 provider **如要让 thinking 走 `additional_kwargs["reasoning_content"]`，必须走专用类（`ChatDeepSeek` / `ChatQwQ` [for QwQ] / `ChatQwen` [for Qwen3 + 显式 enable_thinking] / `ChatMoonshot` / `ChatOpenRouter`）；走 `ChatOpenAI + base_url` 时 MiniMax-M3 的推理以 `<think>` 标签保留在 `content`（应用层正则提取），DeepSeek-R1 / QwQ 的 `reasoning_content` 会被丢弃。
- ℹ️ **MiniMax 例外**：MiniMax-M3 走 `ChatOpenAI + base_url`（Coding Plan 主流用法），`<think>` 标签完整保留；详见 §3.6。

### 3.3 范围治理机制总览

本节按 §3.0 治理原则，对白名单（§3.1）之外的 provider 给出**范围治理机制**——所有清单（黑名单 / 暂不支持清单 / 排除候选名单）当前均**为空集合**；机制仅作为**未来真正有需求时启用**的治理工具保留。

本项目对白名单（§3.1）之外的 provider，按"是否值得在 v1 内支持"分两类处置：

- **§3.1 白名单**：v1 适配范围内，技术维度满足 §3.0 表"必须"维度；
- **§3.5 v2+ 候选**：OpenAI 协议不兼容、需自研解析类，v1 不实现，v2+ 启动自研时建立；
- **§14.7 暂不支持清单**（治理工具，**当前无成员**）：适用于"LangChain 官方支持，但本项目尚未投入维护工作量"的技术情形；不在此处列"未调研 / 优先级靠后"——按 §3.0 原则，若未否定 §3.1 表"必须"维度，必须进入白名单或 §3.5。
- **§13.4 永久黑名单**（治理工具，**当前空集合**）：仅适用于有**硬性合规 / 法律 / 商业禁止**理由的 provider；维护者个人立场 / 政治 / 地域偏好**不得**作为"硬理由"。

> **平衡设计**：上述所有机制都是 **治理工具**，可在未来真正有需求时启用。当前 v1 范围：**白名单（§3.1，26 家）+ v2+ 候选（§3.5，3 家）= 29 个 provider 范围；黑名单与暂不支持清单均为空**。

**F002 load 校验语义**：

| 配置 | F002 行为 | 错误类 |
|---|---|---|
| `default_provider` 在 §3.1 白名单 | 正常解析 | — |
| `default_provider` 在 §3.5 v2+ 候选 | exit 11 | `ProviderTomlScopeError`（推迟到 v2+ 自研实现） |
| `default_provider` 在其它任何 provider_id（既不在 §3.1 也不在 §3.5） | exit 11 | `ProviderTomlScopeError: provider 'X' 不在 §3.1 白名单或 §3.5 v2+ 候选；如走 OpenAI 协议可改用 `[openai_compatible]` 元 provider，或在 issue 中提交 §3.1 升级评估` |
| `[<provider_id>]` 任何节（不在 §3.1 / §3.5） | exit 11 | 同上 |

### 3.6 MiniMax 集成策略说明

> **MiniMax 走 `ChatOpenAI` + `base_url="https://api.minimaxi.com/v1"`**——这是用户主流用法（Coding Plan 订阅，OpenAI 格式）。thinking 以 `<think>` 标签保留在 `content`，应用层可正则提取。

#### 3.6.1 真实用户场景（端到端 demo 示意）

> 本节是通用端到端示意（不是某次实测输出）——但**行为本身可信**：与 LangChain 源码 `ChatOpenAI._create_chat_result` 对 OpenAI-compat 兼容端点的处理一致。

**端到端示意代码**（使用 MiniMax-M3 + get_weather tool，复刻 `harness/demo/create_an_agent.py` 同一份 `init_chat_model` 写法）：

```python
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

model = init_chat_model(
    model="MiniMax-M3",
    model_provider="openai",
    base_url="https://api.minimaxi.com/v1",
    api_key="sk-cp-xxx...",           # Coding Plan 订阅密钥
)

def get_weather(city: str) -> str:
    return f"It's always sunny in {city}!"

agent = create_agent(model=model, tools=[get_weather])
response = agent.invoke({
    "messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]
})
```

实际响应（AIMessage）——在 `response["messages"][-1]` 取到：

```
AIMessage(
  content='<think>The user is asking about the weather in San Francisco...</think>\n\nThe weather in San Francisco is sunny! ☀️ ...',
  response_metadata={'model_provider': 'openai', 'model_name': 'MiniMax-M3', 'finish_reason': 'stop'},
  ...
)
```

**AIMessage 实测输出**（整段响应记录在 `harness/demo/create_an_agent.py:36-41` docstring 注释中）：

| 调用轮 | 备注 | `finish_reason` | `model_name` |
|---|---|---|---|
| 第 1 轮（assistant）→ 第 2 轮（tool） | 调用 `get_weather` 工具 | `tool_calls` | `MiniMax-M3` |
| 第 3 轮（assistant）| **响应 content 含 `<think>...</think>` 标签** | `stop` | `MiniMax-M3` |

> ⚠️ **重要区分**：docstring 注释记录的是更早期的"端到端 demo"实测（带 tool 调用，San Francisco 天气查询），与当前 `harness/demo/create_an_agent.py` 默认运行（查询"你可以调用哪些工具?"无 tool 调用、`finish_reason='stop'`）**不是同一次运行**。两份都共享同一段 `init_chat_model(...)` 构造，但**测试场景不同**。

**结论**：`<think>...</think>` 标签**原样保留**在 `AIMessage.content` 字符串里（`ChatOpenAI` 走 `/v1/chat/completions` API 路径，响应端 `_create_chat_result` → `_convert_dict_to_message` 只解析 OpenAI 标准字段 `content` / `function_call` / `tool_calls` / `audio`，对 MiniMax OpenAI-compat 返回的非标字段 `reasoning_content` 既不解析也不剥离 `<think>` 内联标记；详见源码 `langchain_openai/chat_models/base.py:2062-2157`）。应用层可用正则 `r"<think>(.*?)</think>\s*(.*)"` 提取。

#### 3.6.2 MiniMax 在 LangChain 生态的实际情况

| 路径 | 是否存在 | 备注 |
|---|---|---|
| 独立 `langchain-minimax` 包（PyPI） | ❌ 不存在 | `pip install langchain-minimax` → ERROR |
| `langchain-community.MiniMaxChat` 类 | ⚠️ 存在，但 `langchain-community` 包正在被弃用 | 用 MiniMax 原生协议，不支持 thinking |
| `init_chat_model("minimax:...")` | ❌ 不支持 | 不在 30 个 provider 别名里 |
| 官方 chat model integrations overview | ❌ 未收录 | https://docs.langchain.com/oss/python/integrations/chat 无 MiniMax |

#### 3.6.3 MiniMax 官方提供的两种 API 端点

| 端点 | 协议 | 兼容 SDK | 适用 LangChain 类 | 密钥格式 | 用户占比 |
|---|---|---|---|---|---|
| `https://api.minimaxi.com/v1` | OpenAI Chat Completions API | `openai` Python SDK | **`ChatOpenAI`** ✅ | `sk-cp-xxx`（Coding Plan 订阅） | **绝大多数** |
| `https://api.minimax.io/anthropic` | Anthropic Messages API | `anthropic` Python SDK | `ChatAnthropic` | `MINIMAX_API_KEY`（普通 API key）| 少数 |

#### 3.6.4 v1 采纳策略

**v1 默认**：`ChatOpenAI` + `base_url="https://api.minimaxi.com/v1"`。

**理由**：
1. **用户主流用法**：Coding Plan 是 MiniMax 的核心商业产品，几乎所有用 MiniMax 的开发者都有 `sk-cp-` 密钥；`harness/demo/create_an_agent.py` 已用此模式并跑通。
2. **thinking 保留**：实测 MiniMax OpenAI-compat 端点默认将 thinking 包裹在 `<think>...</think>` 标签内放回 `content`；`ChatOpenAI` 不解析 `<think>` 标签，标签原样保留 → 应用层可用正则提取。
3. **TOML 字段最少**：用户只需填 `api_key = "sk-cp-..."` + `api_host = "https://api.minimaxi.com/v1"`（或留空用默认）。
4. **无需 v1 引入任何社区 / 弃用依赖**。

> **实测补充（MiniMax-M3 + `sk-cp-` Coding Plan 密钥）**：
>
> | 实测项 | 结论 |
> |---|---|
> | `<think>...</think>` 标签保留在 `AIMessage.content` | ✅ **成立**——§3.6.5 的正则提取直接可用（`extract_thinking()` 返回 `(thinking, answer)`） |
> | `reasoning_split` 字段被 OpenAI 兼容端点接受 | ✅ **接受**（请求体带 `"reasoning_split": false` 返回 200）——§3.6.4 的 `extra_body` 透传方案**可行** |
> | 思考**token 数**是否在统一 schema 里 | ✅ **在**——`usage_metadata["output_token_details"]["reasoning"]`（实测 44）→ 应用层拿不到思考**文本**（在 `<think>` 标签里），但拿得到思考**量** |
> | tool calling | ✅ 正常——返回 `finish_reason='tool_calls'` + 标准 `tool_calls` 结构 |
> | 实际下发的 token 字段名 | ⚠️ `max_completion_tokens`（不是 `max_tokens`）——langchain-openai 1.7.2 的 `ChatOpenAI` 对所有模型都重命名（见 §5.2），MiniMax 端点**接受**该字段名 |
> | 服务端稳定性 | ⚠️ **会随机返回 `529 overloaded`**（"当前服务集群负载较高"，实测单轮约半数请求被拒）——与配置无关，**需 provider 级退避重试**（对应 §4.3.1 的 retryable → exit 83） |
>
> 端到端证据见 `harness/demo/about_providers/provider.py`（案例 B01 / B02 / B03 / B08 / B10）。

**关于 `reasoning_content` / `reasoning_split` 字段**（详见 `ChatOpenAI` 警告：`reference.langchain.com/python/langchain-openai/chat_models/base/ChatOpenAI`，源码 `langchain_openai/chat_models/base.py:1-12 / 783-790 / 2917-2928` 三处 docstring 警告 + 411 行 `_format_message_content` 过滤）：

> **说明**：`reasoning_split` 参数的来源是 MiniMax 工程师在论坛/工单中的非正式披露，**未在 MiniMax 官方公开文档中找到独立佐证**。donkey 不依赖这个参数来保证行为；`<think>` 标签保留是 MiniMax 服务端默认行为（实测 + 源码行为符合）。`reasoning_split` 仅作为**可选的高级控制位** 通过 `extra_body` 显式透传。

| `reasoning_split` 值 | 服务端行为 | donkey 端可见性 | 推荐 |
|---|---|---|---|
| `false`（默认） | thinking 在 `content` 内以 `<think>...</think>` 包裹 | ✅ 应用层正则在 `AIMessage.content` 提取 | ✅ **推荐**：保持默认 |
| `true` | thinking 移到独立 `reasoning_content` 字段 | ❌ **`ChatOpenAI` 主动丢弃**（走 `_convert_dict_to_message` 不解析，非标字段无映射） | ❌ **不推荐**——除非改走 `ChatAnthropic` |

**donkey 实现层透传**（如果用户需要显式切到 `reasoning_split`）：
```python
ChatOpenAI(
    model=model,
    api_key=params["api_key"],
    base_url=params.get("api_host") or "https://api.minimaxi.com/v1",
    extra_body={"reasoning_split": False},  # 透传 OpenAI-compat 私有参数
)
```
利用了 `ChatOpenAI` 的 `extra_body` 字段（源码 `langchain_openai/chat_models/base.py:1146-1164` 已明确支持"Parameters specific to OpenAI-compatible API provider"透传，**与 v1 立场一致**：通过 LangChain 官方机制实现，不破坏"donkey 不解析 provider-specific JSON"原则）。

**应用层提取** 见 §3.6.5。

#### 3.6.5 应用层提取 thinking 的伪代码

```python
import re

def extract_thinking(response) -> tuple[str, str]:
    """从 AIMessage.content 中提取 thinking 块和最终回答。"""
    content = response.content
    m = re.search(r"<think>(.*?)</think>\s*(.*)", content, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()  # (thinking, answer)
    return "", content
```

#### 3.6.6 v2+ 可选升级

若未来需要支持**更精细的 thinking 控制**（如 `output_config.effort`、`thinking.type = "adaptive"` 等），可走 Anthropic SDK 兼容端点 + `ChatAnthropic`：
- `api_host = "https://api.minimax.io/anthropic"`
- `api_key = "<MINIMAX_API_KEY>"`
- `thinking.type` / `budget_tokens` / `reasoning_effort` 字段

但 Coding Plan 用户**不适用**（Coding Plan 仅支持 OpenAI-compat 端点）。

**TOML 字段映射**（v1 默认 OpenAI-compat）：
- `api_host = "https://api.minimaxi.com/v1"`（默认）
- `api_key` → `api_key`（`sk-cp-...` 格式）
- `temperature` / `max_tokens` / `top_p` → ChatOpenAI 标准参数
- **不支持** `thinking.type` / `budget_tokens` / `reasoning_effort` 字段（v1 不暴露；v2+ 接 Anthropic SDK 端点时再加）

### 3.4 白名单 / v2+ 候选外的处理

| 用户行为 | 项目响应 |
|---|---|
| 配置 `protocol = "unknown_ai"` | F002 load 报错（exit 11）：`ProviderTomlScopeError: provider 'unknown_ai' 不在白名单（v1 = 26 家，详见 §3.1）`（错误类统一为 `ProviderTomlScopeError`） |
| 配置 `[baidu]` / `[iflytek]` / `[sensetime]` | F002 load 报错（exit 11）：`ProviderTomlScopeError: provider 'X' 推迟到 v2+ 实现（详见 §3.5）` |
| 配置 `[provider.organization]`（v1 残留） | F002 load 报错：保留 v1 schema 不兼容提示，引导迁移到 v2 per-provider schema |
| 配置 v1 的 `[provider.extra]` | F002 load 报错：`ExtraTableNotAllowedError: v2 schema 不支持 [provider.extra]，请在对应 provider 节下显式声明字段` |
| 配置 `[<其它未列入 §3.1 或 §3.5 的 provider>]` | F002 load 报错（exit 11）：`ProviderTomlScopeError: provider 'X' 不在 §3.1 白名单或 §3.5 v2+ 候选；如走 OpenAI 协议可改用 [openai_compatible] 元 provider，或在 issue 中提交 §3.1 升级评估` |

---

## 4. 调研：LangChain LLM 抽象

### 4.1 `init_chat_model` 标准参数

> 数据源：LangChain 1.x 官方文档镜像（`models.md`）。

| 参数 | 类型 | 必填 | 默认 | 备注 |
|---|---|---|---|---|
| `model` | `str` | ✅ | — | 模型名；支持 `{provider}:{model}` 简写 |
| `model_provider` | `str` | — | — | 与 `model` 简写二选一 |
| `api_key` | `str` | — | — | 通常从环境变量读（本项目**改为 TOML 明文**） |
| `base_url` | `str` | — | provider 默认 | 自定义 OpenAI-compatible 端点 |
| `temperature` | `number` | — | provider 默认 | 通常 [0, 2] |
| `max_tokens` | `int` | — | provider 默认 | 输出 token 上限 |
| `timeout` | `number` | — | provider 默认 | 请求超时（秒） |
| `max_retries` | `int` | — | `6` | LangChain 全局默认；指数退避 + jitter |
| `rate_limiter` | `BaseRateLimiter` | — | `None` | 速率限制器 |
| `**kwargs` | `Any` | — | — | provider-specific 参数透传 |

### 4.2 关键设计观察

1. **`init_chat_model` 已用 `model_provider` 内置协议分发**——本项目 **不**重新做协议分发层，**完全复用** LangChain；
2. **`api_key` 的环境变量约定是 provider-specific**：`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` 等——本项目 **强制 TOML 明文**（P-2），不读环境变量；
3. **`max_retries=6` 是 LangChain 全局默认**——本项目仅在用户显式覆盖时才写入配置文件；
4. **`**kwargs` 透传是 LangChain 推荐的"扩展口"**——但本项目 **不采用透传**（P-5），所有已知参数显式声明在 schema；
5. **LangChain 提供 `model.profile` 元数据**（`max_input_tokens` / `supported_modalities` / `reasoning_effort_levels` 等）——运行时可查，**不**维护本地元数据表。

### 4.3 LangChain 标准异常（运行时反馈）

> 本节纯描述性列；exit code 映射在 §4.3.1 中给出（与 `harness/features/README.md §3.4.1` 严格 1:1）。

| 异常 | is_retryable | 触发 |
|---|---|---|
| `ModelAuthenticationError` | ❌ | API key 错 / 过期 |
| `ModelPermissionDeniedError` | ❌ | 凭据缺权限 |
| `ModelInvalidRequestError` | ❌ | provider 拒请求（参数错） |
| `ModelNotFoundError` | ❌ | 模型不存在 |
| `ModelRateLimitError` | ✅ | 触发限流 |
| `ModelAPIError` | ✅ | provider 服务故障 |
| `ModelConnectionError` | ✅ | 连不上 provider |
| `ModelTimeoutError` | ✅ | 超时 |
| `ContextOverflowError` | ❌ | 输入超上下文 |

异常类型由 LangChain 提供，本项目**只需**做异常映射（→ exit code），不在配置文件中描述异常。

### 4.3.1 运行时异常 → exit code 映射（与 README §3.4.1 严格 1:1）

donkey 内部对 LangChain 异常的处理**遵循"修复动作合并"原则**——9 种 LangChain 异常归到 4 个 exit code：

| LangChain 异常 | retryable? | donkey v1 默认 retry policy | **F004 段位 exit code** | mapped Error class |
|---|---|---|---|---|
| `ModelAuthenticationError` | ❌（401/403） | 不重试 | **90**（F004-P6 `ModelAuthenticationError`） | `ModelAuthenticationError` |
| `ModelPermissionDeniedError` | ❌（权限不足） | 不重试 | **90**（同 ModelAuthenticationError 伞形合并） | `ModelAuthenticationError` |
| `ModelInvalidRequestError` | ❌（400 bad request） | 不重试 | **83**（F004-P6 `ModelRetryMiddlewareError`，"请求始终失败"）| `ModelRetryMiddlewareError` |
| `ModelNotFoundError` | ❌（404 模型不存在） | 不重试 | **90**（同 ModelAuthenticationError 伞形合并） | `ModelAuthenticationError` |
| `ModelRateLimitError` | ✅（429 短期）| exponential backoff 直到耗尽 | **83**（retry 超限 → middleware 抛 `ModelRetryMiddlewareError`） | `ModelRetryMiddlewareError` |
| `ModelAPIError` | ✅（5xx provider 服务故障）| exponential backoff 直到耗尽 | **83** | `ModelRetryMiddlewareError` |
| `ModelConnectionError` | ✅（网络故障）| exponential backoff 直到耗尽 | **83** | `ModelRetryMiddlewareError` |
| `ModelTimeoutError` | ✅（请求超时）| exponential backoff 直到耗尽 | **83** | `ModelRetryMiddlewareError` |
| `ContextOverflowError` | ❌（输入超上下文）| 不重试 | **85**（F004-P6 `ModelCallLimitMiddlewareError`，"调用次数 / 输入规模超限"伞形合并）| `ModelCallLimitMiddlewareError` |
| **（构造期）`openai.OpenAIError: Missing credentials`** | ❌ | 不重试 | **90** | `ModelAuthenticationError` |

> - **最后一行是实测新增**——`api_key` 缺失或为空串时，底层 SDK 在**构造 ChatModel / client 阶段**就抛 `Missing credentials`（**不是**运行时的 401），因此 §9.2 的"空 api_key → warning"路径终点是**构造期失败**，必须单独映射到 exit 90（详见 §9.1.1 / §9.2）。
> - 该异常的原始文案包含"or set the `OPENAI_API_KEY` ... environment variable"——**与 §9.1「不读 env var」立场直接冲突**，CLI 层必须**改写文案**（如"api_key 未配置或为空，请检查 provider.toml"），不得把用户引向 env var 路径。
> - **`ModelInvalidRequestError`(400) 的 exit code 统一为 83**——代码片段与 §16 / §17 均按表格口径（最具体的一处）对齐。

**奥卡姆合并逻辑**：
- **retryable 错误**（429 / 5xx / 网络 / 超时 / **400 请求格式错**）→ 全部退避后都汇总到 exit 83 (`ModelRetryMiddlewareError`)。用户的修复动作相同——"等会儿重试 / 改写 prompt / 切换 provider"；
- **non-retryable 鉴权类**（401/403/404 + 构造期 Missing credentials）→ 退避无效，首次即抛，汇总到 exit 90 (`ModelAuthenticationError`)。用户的修复动作相同——"检查 API key / 检查 model 名"；
- **non-retryable 输入超限类**（`ContextOverflowError`）→ 属于"调用次数 / 输入规模超限"，汇总到 exit 85 (`ModelCallLimitMiddlewareError`)；
- **4 个 F004-P6 exit code 覆盖 9 种 LangChain 异常 + 1 类构造期错误**。
  （`ModelInvalidRequestError`(400) → **83**，`ContextOverflowError` 单独留在 85）

**donkey 实现指引**：

```python
# donkey/core/llm/middleware/model_errors.py
from langchain_core.exceptions import (
    ModelAuthenticationError, ModelPermissionDeniedError,
    ModelInvalidRequestError, ModelNotFoundError,
    ModelRateLimitError, ModelAPIError, ModelConnectionError,
    ModelTimeoutError, ContextOverflowError,
)

# 4 个 retryable 异常归一类（退避后 retry 用尽 → middleware 抛 ModelRetryMiddlewareError, exit 83）
RETRYABLE_LLM_ERRORS = (
    ModelRateLimitError, ModelAPIError,
    ModelConnectionError, ModelTimeoutError,
)
# 3 个 non-retryable 鉴权类异常（首次即抛 → exit 90）
# ModelInvalidRequestError 是 400 请求格式错误 —— 归 retryable 类（exit 83），见下方注释。
NON_RETRYABLE_AUTH_ERRORS = (
    ModelAuthenticationError, ModelPermissionDeniedError,
    ModelNotFoundError,
)
# 1 个 non-retryable 输入超限（exit 85）
INPUT_LIMIT_ERRORS = (ContextOverflowError,)
# 1 个请求格式错误（400，non-retryable 但归 retryable 桶 → exit 83）
INVALID_REQUEST_ERRORS = (ModelInvalidRequestError,)
```

**注意边界**：
- `ModelInvalidRequestError`（400）文档说 ❌ non-retryable，但分类到**retryable**类（exit 83）——理由：400 类错误多数是 provider 拒绝某种请求格式（用户 prompt 含非法字符 / 字段超长），agent 可以**降低 token / 改写 prompt**后重试；这与"401 鉴权失败"（用户修复动作不同）区分；
- 未来 LangChain 增加新异常类，优先归到现有合并类别；如用户实测发现"修复动作实际不同"，从 F004-P7 预留 95-100 区借位（需 Maintainer 走 §14.5 流程）。

### 4.4 复用策略

| LangChain 能力 | 本项目使用方式 |
|---|---|
| `init_chat_model("provider:model", **params)` | 直接调用，参数从 TOML 读 |
| `model.invoke(messages)` | 应用层统一接口 |
| `model.stream(messages)` | 应用层统一接口 |
| `model.bind_tools(tools)` | 应用层统一接口 |
| `model.with_structured_output(schema)` | 应用层统一接口 |
| `model.profile` | 运行时元数据查询 |
| LangChain 标准异常 | 解析层抛 → 应用层捕获 → 映射到 donkey exit code |
| `max_retries` / `rate_limiter` | 透传配置 |

---

## 5. 调研：主流 provider 数据格式差异

> 解析层严谨性要求：必须吃透每个 provider 的请求 / 响应格式。

### 5.1 请求格式差异（精选 5 个代表）

#### OpenAI

```json
POST https://api.openai.com/v1/chat/completions
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are helpful"},
    {"role": "user", "content": "Hello"}
  ],
  "max_completion_tokens": 16384,    // o-series 用这个名
  "temperature": 1.0,
  "tools": [{"type": "function", "function": {...}}],
  "stream": true
}
```

#### Anthropic

```json
POST https://api.anthropic.com/v1/messages
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 4096,                 // 必填
  "system": "You are helpful",        // system 是顶层，不是 message
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "thinking": {"type": "enabled", "budget_tokens": 10000},  // 推理
  "tools": [...]
}
```

#### Google Gemini

```json
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
{
  "contents": [{"role": "user", "parts": [{"text": "Hello"}]}],
  "systemInstruction": {"parts": [{"text": "..."}]},  // system 是另一字段
  "generationConfig": {
    "temperature": 1.0,
    "maxOutputTokens": 8192,
    "topP": 0.95,
    "topK": 40
  },
  "safetySettings": [...],
  "tools": [...]
}
```

#### Ollama

```json
POST http://localhost:11434/api/chat
{
  "model": "llama3.1:70b",
  "messages": [...],
  "stream": true,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "num_ctx": 4096,           // Ollama 专属：上下文窗口
    "num_predict": 2048,       // Ollama 专属：最大生成 token
    "repeat_penalty": 1.1,     // Ollama 专属
    "mirostat": 0
  }
}
```

#### 百度文心 ERNIE

```json
POST https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token=xxx
{
  "messages": [...],
  "temperature": 0.95,
  "top_p": 0.8,
  "penalty_score": 1.0,        // ERNIE 专属：惩罚分数
  "system": "...",
  "user_id": "..."             // ERNIE 追踪
}
```

### 5.2 关键差异点

| 差异点 | 体现 | 解析层影响 |
|---|---|---|
| **`system` 消息位置** | OpenAI / Kimi / Doubao：放 `messages` 首条；Anthropic / Gemini / ERNIE：单独字段 | 解析层需重写 system message 位置 |
| **`max_tokens` 命名** | langchain-openai 1.7.2 的 `ChatOpenAI` 对**所有**模型都把 `max_tokens` 重命名为 `max_completion_tokens`（源码 `base.py:3830` / `:3845`），**不只** o-series；而基于 `BaseChatOpenAI` 的专用类（`ChatDeepSeek` 等）仍下发 `max_tokens`；Anthropic / Gemini / Ollama：`max_tokens` | 解析层按模型版本分派 |
| **鉴权位置** | 大多数：`Authorization: Bearer` header；ERNIE：URL query `access_token`；iFlytek：URL query + 签名 | 解析层需 provider-specific auth builder |
| **流式响应格式** | OpenAI / 兼容：SSE `data: {...}\n\n`；Anthropic：SSE `event: ...` 6 种事件；Gemini：SSE `data: {...}\n\n`（字段不同） | 解析层需 provider-specific SSE parser |
| **工具调用 schema** | OpenAI / 兼容：`tools[].function`；Anthropic：`tools[].input_schema`；Gemini：`tools[].function_declarations` | 解析层按 provider 重写工具 schema |
| **usage 字段** | OpenAI：`prompt_tokens` / `completion_tokens`；Anthropic：`input_tokens` / `output_tokens`；Gemini：`promptTokenCount` / `candidatesTokenCount`；Ollama：`prompt_eval_count` / `eval_count` | 解析层统一翻译为 LangChain `UsageMetadata` |

### 5.3 解析层落地的代码结构

> v1 **100% 复用 LangChain**，无自研解析类。26 个 provider 全部用 `ReusableProvider` 抽象。详见 §15。
> **关键警告**（实测源码 `langchain_openai/chat_models/base.py:411` + 三处 docstring 警告：模块 :1-12 / `BaseChatOpenAI` :783-790 / `ChatOpenAI` :2917-2928）：
>
> - 411 行 `_format_message_content` 函数对**输入** messages 的 content blocks 主动 drop `tool_use` / `thinking` / `reasoning_content` 类型（防止这些 block 混在用户消息里发给 OpenAI）。
> - 响应端的 `reasoning_content` / `reasoning_details` 丢失是**被动行为**——`_convert_dict_to_message`（base.py:2122 → 第 220 行函数）只解析 OpenAI 标准字段 `content` / `function_call` / `tool_calls` / `audio` / `name`，不解析非标字段，自然不放入 `additional_kwargs`。
>
> 因此：**含推理模型的 provider**（DeepSeek-R1 / Kimi-K2 / QwQ 系列 / Qwen3-thinking / GLM-Z / Grok 3 / 智谱 Z 系列）**必须走专用 LangChain 类**（`ChatDeepSeek` / `ChatQwQ` [for QwQ] / `ChatQwen` [for Qwen3 + 显式 enable_thinking] / `ChatMoonshot` / `ChatOpenRouter`），否则应用层 `additional_kwargs["reasoning_content"]` 拿不到数据。**MiniMax-M3 例外**：走 `ChatOpenAI + base_url` 时 thinking 在 `content` 内以 `<think>` 标签保留（应用层正则提取），详见 §3.6。

```
donkey/core/llm/
├── providers/
│   ├── base.py                       # ReusableProvider 抽象基类（v1 仅此一个抽象）
│   ├── openai.py                     # ChatOpenAI
│   ├── anthropic.py                  # ChatAnthropic
│   ├── google.py                     # ChatGoogleGenerativeAI
│   ├── ollama.py                     # ChatOllama
│   ├── xai.py                        # ChatXAI
│   ├── mistral.py                    # ChatMistralAI
│   ├── bedrock.py                    # ChatBedrock
│   ├── groq.py                       # ChatGroq
│   ├── fireworks.py                  # ChatFireworks
│   ├── together.py                   # ChatTogether
│   ├── cohere.py                     # ChatCohere
│   ├── perplexity.py                 # ChatPerplexity
│   ├── databricks.py                 # ChatDatabricks
│   ├── cerebras.py                   # ChatCerebras
│   ├── deepseek.py                   # ⚠️ ChatDeepSeek（专用类，保留 reasoning_content）
│   ├── qwen.py                       # 默认 ChatOpenAI + base_url；可选 ChatQwen 保留 thinking
│   ├── moonshot.py                   # 默认 ChatOpenAI + base_url；可选 ChatMoonshot 保留 thinking
│   ├── openrouter.py                 # ⚠️ ChatOpenRouter（专用类，统一路由）
│   ├── doubao.py                     # ChatOpenAI + base_url
│   ├── zhipu.py                      # ChatOpenAI + base_url
│   ├── MiniMax.py                    # ChatOpenAI + base_url（OpenAI 兼容 + sk-cp- 密钥；详见 §3.6）
│   ├── tencent.py                    # ChatOpenAI + base_url
│   ├── stepfun.py                    # ChatOpenAI + base_url
│   ├── xiaomi.py                     # 多平台路由（OpenRouter / Ollama）
│   ├── meta.py                       # 多平台路由（Ollama / OpenAI 兼容代理）
│   ├── openai_compatible.py          # ChatOpenAI + 必填 base_url
│   └── _v1_scope.py                  # v1 范围守卫：白名单外 / v2+ 候选 / 永久黑名单 / 暂不支持清单 校验（v1 范围内该模块下两个 dict 当前均为空集合，仅承载治理流程）
├── network/
│   └── transport.py                  # 透传 HTTP（§2.2）
├── schema/
│   └── loader.py                     # TOML → Pydantic dataclass（按 provider 分派）
└── application/
    └── facade.py                     # 高级抽象：get_default_chat_model() 等
```

> **v2+ 候选目录**（v1 不创建，v2+ 启动自研时建立）：
> ```
> donkey/core/llm/providers/custom/
> ├── baidu.py                         # OAuth access_token + ERNIE 协议
> ├── iflytek.py                       # WebSocket + HMAC-SHA256 + 长连接
> └── sensetime.py                     # SenseNova 私有协议
> ```

**轻量 provider 复用方式**（直接调 LangChain，不实现解析方法）：

```python
# donkey/core/llm/providers/reusable/qwen.py
from donkey.core.llm.providers.base import ReusableProvider
from langchain_openai import ChatOpenAI


class QwenProvider(ReusableProvider):
    """通义千问：默认走 ChatOpenAI + base_url。"""

    provider_id = "qwen"
    default_api_host = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def build_chat_model(self, model: str, **params) -> ChatOpenAI:
        """直接构造 LangChain ChatOpenAI，零解析。"""
        return ChatOpenAI(
            model=model,
            api_key=params["api_key"],
            base_url=params.get("api_host") or self.default_api_host,
            temperature=params.get("temperature"),
            max_tokens=params.get("max_tokens"),
            timeout=params.get("timeout", 60),
            max_retries=params.get("max_retries", 6),
            # reasoning_content 通过 ChatOpenAI 会被丢弃（参见 §3.2 关键警告）；
            # 推理模型按 model_name 后缀分派到 QwenThinkingProvider / ChatQwQ 类
        )


class QwenThinkingProvider(ReusableProvider):
    """通义千问 QwQ 推理模型专用：走 ChatQwQ 保留 reasoning_content。

    两个类都是 langchain_qwq 提供，区别见源码 langchain_qwq/chat_models.py:32 / :694。
    """

    provider_id = "qwen"  # 同 provider_id
    default_api_host = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    preferred_for_thinking = True

    def build_chat_model(self, model: str, **params):
        from langchain_qwq import ChatQwQ

        return ChatQwQ(
            model=model,
            api_key=params["api_key"],
            # ChatQwQ 总是 thinking on，无需额外字段
            temperature=params.get("temperature"),
            max_tokens=params.get("max_tokens"),
            timeout=params.get("timeout", 60),
            max_retries=params.get("max_retries", 6),
        )


# 应用层选择逻辑：
# def select_qwen_provider(model_name: str) -> ReusableProvider:
#     """根据 model_name 后缀分派 Qwen Provider 类。
#
#     规则：
#     - model_name 包含 `qwq` / `reasoner` 或以 `-thinking` 结尾
#       → QwenThinkingProvider（走 ChatQwQ，thinking 强制开启）
#     - 其它通用 Qwen 模型（qwen3-max / qwen3-72b / qwen-plus 等）
#       → QwenGeneralThinkingProvider（走 ChatQwen + enable_thinking=True）
#     """
#     lowered = model_name.lower()
#     thinking_keywords = ("qwq", "reasoner")
#     if any(kw in lowered for kw in thinking_keywords) or lowered.endswith("-thinking"):
#         return QwenThinkingProvider()
#     return QwenGeneralThinkingProvider()
#
# # 调用：
# provider = select_qwen_provider(model)
# chat_model = provider.build_chat_model(model, **params)
```

---

## 6. 设计目标

| # | 目标 | 度量 |
|---|---|---|
| **G-1** | 配置文件 = Cherry Studio 风格：每个 provider 一个独立 schema | TOML 顶层有 `[openai]` / `[anthropic]` / ... 而非统一 `[provider]` |
| **G-2** | 用户填写最少字段即可跑通 | 必填字段 ≤ 2 个（`api_key` + `default_provider.default_model`） |
| **G-3** | workspace 跨 OS 行为一致 | `api_key` 走 TOML 明文，不读环境变量 |
| **G-4** | 解析严谨 | 字段拼写错误在 F002 load 阶段就报错，不延迟到运行时 |
| **G-5** | 透传网络 | 解析层不直接发 HTTP；网络层不解析 body |
| **G-6** | 高级抽象 | 业务代码只调用 `model.invoke(messages)`，不感知 provider |
| **G-7** | schema 演进受控 | provider 白名单 + §3.0 治理原则硬限；新 provider 走 §14 流程；列入永久黑名单必须满足硬理由条件 |
| **G-8** | Web UI 友好 | 每个 provider 渲染为独立 form section，含协议默认提示 |
| **G-9** | v1 100% 可用 LangChain 实现 | **v1 零自研**：26/26 v1 provider 复用 LangChain 官方类（14 独立类 + 6 薄包装 + 3 推理专用 + 3 本地/元）；v2+ 候选 3 家（baidu / iflytek / sensetime）推迟自研，见 §14.6 |

---

## 7. TOML schema 全局结构

### 7.1 文件路径与命名

- **路径**：`<workspace>/provider.toml`（**强制** root 目录，与 `instruction.md` / `README.md` 同级）；
- **编码**：UTF-8 无 BOM；
- **格式**：TOML 1.0（Python 3.11+ `tomllib` 解析）；
- **大小**：典型 workspace 30–80 行（**26** 个 provider 节，每节 3–5 行 + 注释）。
  > 实测：§3.1 表格 26 行；`langchain.chat_models.base._BUILTIN_PROVIDERS` 实测 30 个。

### 7.2 全局结构

```toml
# 顶层：全局默认 + 26 个 provider 独立节
default_provider = "openai"          # 默认 provider_id
default_model = "gpt-4o"             # 默认 model_id（在 default_provider 下）

[openai]
# OpenAI 专属字段（8-12 通用 + 2-3 专属）

[anthropic]
# Anthropic 专属字段

# ... 26 个 provider 节（v1 白名单）

# 不在 §3.1 白名单或 §3.5 v2+ 候选的 provider 节（如 [foo_ai]）→ F002 load 报错（exit 11）
```

### 7.3 schema 强制约束（F002 load 校验）

> exit 11 严格归 `ProviderTomlLoadError` **伞形 Error class**——本节所有"`provider.toml` 加载相关"失败都抛该伞形类的具体子类型，最终 CLI 层映射同一 exit 11（详见 `harness/features/README.md §3.2 + §3.2.1`）。

| 约束 | F002 load 行为 | 子类 Exception |
|---|---|---|
| TOML 语法错误（`tomllib.TOMLDecodeError`） | **exit 11** | `ProviderTomlSyntaxError` |
| 顶层 `default_provider` 缺失 | exit 11 | `ProviderTomlFieldError` |
| 顶层 `default_model` 缺失 | exit 11 | `ProviderTomlFieldError` |
| `default_provider` 不在白名单（§3.1） | exit 11 | `ProviderTomlScopeError` |
| `default_provider` 在永久黑名单（v1 空集合，详见 §13.4） | exit 11 | `ProviderTomlScopeError` |
| `default_provider` 在暂不支持清单（v1 空集合，详见 §14.7） | exit 11 | `ProviderTomlScopeError` |
| `default_provider` 在 §3.5 v2+ 候选 | exit 11 | `ProviderTomlScopeError`（推迟到 v2+ 自研实现） |
| `[<未列入 §3.1 或 §3.5 的 provider>]` 任何节 | exit 11 | `ProviderTomlScopeError` |
| provider 节内字段拼写错误（如 `temprature`） | exit 11 | `ProviderTomlFieldError` |
| provider 节内字段值类型错（如 `temperature = "abc"`） | exit 11 | `ProviderTomlFieldTypeError` |
| 字段值**硬越界**（如 `temperature = 3.0`、`api_host` 非 URL 格式） | exit 11 | `ProviderTomlFieldValueError` |
| `default_model` 不在该 provider 的 `models` 列表 | exit 11 | `ProviderTomlMissingModelError` |
| provider 类的 langchain 不允许 `api_host` 覆盖（如 Bedrock via Converse） | exit 11 | `ProviderTomlHostNotAllowedError` |
| **字段值软越界**（如 `temperature > 1.5` 不超规但偏高）| **warning**（exit 0） | — |
| 鉴权缺失（`api_key` 为空）——**C 档云端 provider**（21 个） | **exit 11**（`ProviderTomlFieldError`） | — |
| 鉴权缺失（`api_key` 为空）——**B 档**（`openai-compatible` / `xiaomi`） | **warning**（exit 0） | — |
| 鉴权缺失（`api_key` 为空）——**A 档本地 provider**（`ollama` / `meta`） | 无（合法，不出 warning） | — |
| `bedrock` 凭据缺失（`aws_secret_access_key` 等为空） | **exit 11**（`ProviderTomlFieldError`）——`[bedrock]` 不用 `api_key`，改查 4 个 `aws_*` 字段 | — |

> - **temperature 的软 / 硬边界**：硬边界 = `[0.0, 2.0]`（OpenAI 协议硬限，越界 = **error** / exit 11）；软边界 = `> 1.5`（协议允许但偏高 = **warning** / exit 0）。
> - **`api_host` 不可覆盖的 provider**：v1 首批 = `bedrock`（走 `boto3.Session` / Converse，端点由 AWS region 决定）→ 填了 `api_host` 抛 `ProviderTomlHostNotAllowedError`（exit 11）。清单随 provider 扩充维护。
> - **`api_key` 分档（3 档 + 1 例外）**：A 档无鉴权本地（`ollama` / `meta`）空值合法无 warning；B 档端点属性未知（`openai-compatible` / `xiaomi`）空值合法 + warning + 占位符；C 档云端（21 家）空值 = **硬错 exit 11**；`bedrock` 不用 `api_key` 字段，改查 4 个 `aws_*` 字段（详见 §9.2 分档表）。
> - **`api_key` 缺失 = warning 的终点不是运行时 401**：实测空 `api_key` 会在**构造 ChatModel 阶段**失败（见 §9.1.1 / §9.2）——warning 仍然成立（不阻塞 load），但运行时会落到 exit 90 的构造期鉴权错误。

**伞形类层级**（继承 `DonkeyError`）：
```python
class ProviderTomlLoadError(DonkeyError):
    """exit code: 11（伞形）—— provider.toml 加载阶段任何失败。"""

class ProviderTomlSyntaxError(ProviderTomlLoadError):
    """tomllib.TOMLDecodeError 包装（exit 11）。"""

class ProviderTomlFieldError(ProviderTomlLoadError):
    """Pydantic schema reject —— 字段名拼写错 / 必填字段缺失（exit 11）。"""

class ProviderTomlFieldTypeError(ProviderTomlLoadError):
    """字段值类型不匹配（exit 11）。"""

class ProviderTomlFieldValueError(ProviderTomlLoadError):
    """字段值硬越界；软越界走 warning（exit 11 / exit 0）。"""

class ProviderTomlScopeError(ProviderTomlLoadError):
    """scope 检查失败：白名单 / 永久黑名单 / 暂不支持清单 / v2+ 候选 / §3.0 治理原则拒绝（exit 11）。

    v2+ 候选（baidu / iflytek / sensetime）**不是独立错误类**——
    它不是"报错"，只是"该 provider 尚未排期开发"（§3.5），与"白名单外 provider"
    属同一类 scope 判定，用户修复动作也相同（改用 [openai-compatible] 或提 issue
    申请 §3.1 升级评估）→ 按奥卡姆合并原则归入本类，伞形下**恒为 7 个子类**。
    区分信息保留在**错误消息**里（"推迟到 v2+ 实现" vs "不在白名单"），不影响 exit code。
    """

class ProviderTomlMissingModelError(ProviderTomlLoadError):
    """default_model 不在该 provider 的 models 列表（exit 11）。"""

class ProviderTomlHostNotAllowedError(ProviderTomlLoadError):
    """provider 类的 langchain 不允许 api_host 覆盖（exit 11）。"""
```

**约束**：
- 所有子类抛错时，CLI 层 `compute_exit_code()` 优先匹配伞形类（`ProviderTomlLoadError`），映射 exit 11；
- **warning 路径不触发此伞形**——软越界 / B 档（`openai-compatible` / `xiaomi`）的空 `api_key` 打印 warning 后退出 0；**C 档云端 provider 的空 `api_key` 则是硬错（exit 11）**——见 §9.2 分档表；
- 用户修复动作都是"打开 `provider.toml` 检查 + 重试 `donkey load`"——奥卡姆合并为单一 exit code；
- 子类在 traceback 中**仍可区分**（每个子类的 docstring 标注具体触发），便于日志排查；
- **`mcp.json` / `SKILL.md` 加载错误不属于 exit 11**——分别对应 exit 12 (`McpJsonSyntaxError`) / exit 13 (`SkillFrontmatterError`)，详见 README §3.2。

> - **v2+ 候选不设独立错误类**——`baidu` / `iflytek` / `sensetime` 只是"**未排期开发**"（§3.5），与"白名单外 provider"同属 scope 判定且用户修复动作相同 → 统一归入 `ProviderTomlScopeError`，**伞形下恒为 7 个子类**；区分信息保留在错误消息里。
> - **空 `api_key` 按 provider 分三档**（A 本地合法 / B 兼容端点合法+warning / C 云端硬错 exit 11）——依据 §9.2 的联网调研与实测。
> - **v1 范围治理**——v1 范围内（§3.1 白名单 + §3.5 v2+ 候选）任何 provider 都不应被列入永久黑名单或暂不支持清单，除非满足 §3.0 表"必须"维度未否定 + §3.0 约束 1。永久黑名单流程详见 §13.4。

---

## 8. 推荐方案：每个 provider 独立 schema

### 8.1 通用 8–12 字段（所有 provider 共享）

> 注：以下字段**在每个 provider 节下都重复声明**（P-1 "per-provider 独立 schema"），但每个字段的取值范围 / 默认值按 provider 文档**强校验**。

| # | 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| 1 | `api_key` | `str` | ⚠️ **按 §9.2 三档 + bedrock 例外**：C 档云端（21 家）必填；B 档（`openai-compatible` / `xiaomi`）空值合法 + warning；A 档（`ollama` / `meta`）空值合法；`bedrock` 不用本字段 | provider 鉴权密钥（明文） |
| 2 | `api_host` | `str` (URL) | ❌（`openai-compatible` / `meta` / `databricks` 必填） | 自定义 API 端点（v1 称 `base_url`；本项目用 `api_host` 与 Cherry Studio 对齐） |
| 3 | `models` | `table`（子表） | ✅ | 该 provider 下注册的 model 列表；每个 model 是一个子节 `[provider.models.model_id]` |
| 4 | `timeout` | `float` | ❌ | 请求超时（秒），默认 60 |
| 5 | `max_retries` | `int` | ❌ | 重试次数，默认 6（LangChain 全局） |
| 6 | `temperature` | `float` | ❌ | 全 provider 默认值（用户可按 model 覆盖） |
| 7 | `max_tokens` | `int` | ❌ | 全 provider 默认值 |
| 8 | `top_p` | `float` | ❌ | 核采样 |
| 9 | `stop` | `list[str]` | ❌ | 停止符 |
| 10 | `stream` | `bool` | ❌ | 流式开关，默认 true |

> **注 1**：`api_host` 必填性详见 §10.1（3 家必填 / 23 家选填）。
> **注 2**：`[bedrock]` **不使用** `api_key`，改用 `aws_access_key_id` / `aws_secret_access_key` / `aws_region` / `aws_session_token` 四个独立字段（§9.1.1 强约束 4）。
> **注 3**：各 provider 的**专属字段**（如 `[anthropic].thinking` / `[google].thinking_config` / `[bedrock].aws_*`）不在本表——详见 §8.3 全局模板与 §7.3 校验规则。

### 8.2 鉴权占位说明

> 字段 1 `api_key` 在绝大多数 provider 节中**存在且结构统一**，但**取值语义按 provider 而异**：
>
> - openai / anthropic / google / xai / mistral / qwen / deepseek / doubao / kimi / zhipu / MiniMax / tencent / stepfun / groq / fireworks / together / cohere / perplexity / cerebras / openrouter / databricks：API key 字符串（databricks 为 Personal Access Token 字符串）；
> - ollama：一般为空字符串（`""`，Ollama 默认无鉴权）；
> - meta：取决于平台（自托管=空；第三方=第三方 key）；
> - **openai-compatible / xiaomi（B 档）**：取决于端点是否校验鉴权——空值合法 + warning，解析层填占位符 `"not-needed"`（详见 §9.2）；
> - **bedrock（特殊）**：用 `aws_access_key_id` / `aws_secret_access_key` / `aws_region` / `aws_session_token` 四个独立字段，**不在 `[bedrock]` 节用 `api_key`**（详见 §8 `[bedrock]` 注释）。
>
> 注：baidu / iflytek / sensetime 在 v2+ 候选（详见 §3.5），v1 不配置这些 provider 节。
>
> donkey TOML loader 对 `api_key` 缺失必须映射为 `""`（空串），**绝不返回 `None`**——见 §9.1.1 "TOML loader 实现守则"。

### 8.3 全局模板

> ⚠️ **本节模板是"schema 参考模板"**——其中的 `api_key = ""` 表示**schema 层面的默认值 / 字段形状说明**，**不是**一份能被 `donkey load` 直接通过的配置：
> - C 档云端 provider（21 家）空 `api_key` = **硬错 exit 11**（§9.2）；
> - `donkey init` 生成的**出厂模板**对 C 档 provider 使用**占位符** `api_key = "REPLACE_ME"`（非空 → 静态检查通过），并要求用户替换为真实 key 后才能通过 F002-P2 的连通性检查（exit 15）。
> - 本节模板保留 `api_key = ""`，是为了把"字段形状 + 默认值 + 解析层行为"讲清楚，不作为可直接使用的配置文件。

```toml
# =============================================================================
# provider.toml —— workspace 模型配置文件
# =============================================================================
#
# 本文件由 `donkey init` 生成，用户可在文本编辑器 / IDE / Web UI 中修改。
# 落地后由 `donkey.core.llm.schema.loader` 解析为 dataclass，
# 再由 `donkey.core.llm.providers.<provider>.py` 解析层翻译为 provider 专有请求。
#
# 设计原则：
#   1. 每个 provider 独立一节；无统一 [provider] 顶层表
#   2. api_key 仅 TOML 明文（P-2），不读环境变量
#   3. api_host 对所有 provider 可选；Ollama 允许 "default"
#   4. 字段拼写错误在 F002 load 阶段就报错（P-5）
#   5. 白名单 v1 = 26 家（v2+ 候选 3 家推迟自研）；永久黑名单与暂不支持清单当前均空（详见 §3.0 治理原则 / §3.3 / §13.4 / §14.7）
#
# LangChain: init_chat_model("provider:model", **params)
# =============================================================================


# -----------------------------------------------------------------------------
# 顶层：全局默认
# -----------------------------------------------------------------------------

# 默认 provider_id。必填。决定应用层调哪个 ChatModel 类。
# 类型：str
# 取值：openai | anthropic | google | ollama | xai | mistral | qwen | deepseek
#       | doubao | kimi | zhipu | MiniMax | tencent | xiaomi | openai-compatible | meta
#       | bedrock | groq | fireworks | together | cohere | perplexity | databricks
#       | cerebras | openrouter | stepfun
# 不在白名单 / 在黑名单 → F002 load 报错
# 注：baidu / iflytek / sensetime 在 v2+ 候选（详见 §3.5），v1 配置会报错
default_provider = ""

# 默认 model_id。必填。必须在 default_provider 节下的 models 表中存在。
# 类型：str
# 示例："gpt-4o" / "claude-sonnet-4-6" / "qwen-max" / "deepseek-chat"
default_model = ""


# -----------------------------------------------------------------------------
# [openai] —— OpenAI（含 o 系列推理模型）
# -----------------------------------------------------------------------------

[openai]

# 鉴权密钥。必填。OpenAI 官方 API key。
# 类型：str
# 默认：""
# 鉴权：填入后由解析层加 "Authorization: Bearer <api_key>" header
api_key = ""

# 自定义 API 端点。选填。
# 类型：str (URL)
# 默认："" → 解析层用 OpenAI 官方 "https://api.openai.com/v1"
# 示例：填 "https://api.openai.com/v1" / "https://openrouter.ai/api/v1" 等 OpenAI 兼容端点
api_host = ""

# OpenAI 专属：组织 ID。选填。
# 类型：str（"org-" 开头的 24 字符 ID）
# 默认：""
# 鉴权：解析层加 "OpenAI-Organization: <openai_organization>" header
openai_organization = ""

# OpenAI 专属：项目 ID。选填。
# 类型：str
# 默认：""
openai_project = ""

# 请求超时（秒）。选填。默认 60。
timeout = 60

# 重试次数。选填。默认 6。
max_retries = 6

# 默认 temperature（所有未在 models 下覆盖的模型用此值）。选填。默认 1.0。
# 范围：[0.0, 2.0]
temperature = 1.0

# 默认 max_tokens。选填。默认 16384。
# 注：解析层会按模型分派（o-series 用 max_completion_tokens；其它用 max_tokens）
max_tokens = 16384

# OpenAI 旗下注册的模型
[openai.models.gpt-4o]
# 模型级 temperature（覆盖 provider 默认）
temperature = 1.0
max_tokens = 16384

[openai.models.o3]
# o 系列推理模型专属
reasoning_effort = "high"   # "low" | "medium" | "high"

[openai.models.gpt-4o-mini]
temperature = 0.7
max_tokens = 16384


# -----------------------------------------------------------------------------
# [anthropic] —— Anthropic Claude
# -----------------------------------------------------------------------------

[anthropic]

# 鉴权密钥。必填。Anthropic 官方 API key。
# 类型：str
api_key = ""

# 自定义 API 端点。选填。Anthropic 官方不支持第三方端点；填了 → warning。
# 类型：str (URL)
# 默认："" → 解析层用 "https://api.anthropic.com"
api_host = ""

timeout = 60
max_retries = 6

# Anthropic 专属：是否启用 thinking。选填。默认 disabled。
# 类型：table
# 字段：type ("enabled" | "disabled" | "adaptive"), budget_tokens (int)
# 注：仅 Claude Sonnet 4.5+ / Opus 4.6+ 支持
# adaptive 模式（Opus 4.6+）自动决定 budget_tokens；Sonnet 必须显式 budget_tokens
[anthropic.thinking]
type = "disabled"
budget_tokens = 10000

# ⚠️ 采样参数限制（LangChain 源码实测 langchain_anthropic 1.7.6 实装代码 `chat_models.py:1809-1860`，函数 `_assert_valid_model_configuration`）：
#
# 限制模型清单与边界条件
#
# langchain_anthropic 源码实测支持以下前缀的真实模型名：
# - `claude-fable-5` / `claude-fable-5-1` / `claude-sonnet-5-5` / `claude-opus-5-5`
#   —— 通过 `startswith()` 在 `:1809-1810` 显式识别，且 `_supports_forced_tool_choice:1157-1159`
#   显式点名 `("claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5")` 三个 model。
# - 以下模型严格限制（实测 langchain_anthropic `:1809-1834` 抛 `ValueError`）：
#     claude-fable-5 / claude-fable-5-1 / claude-sonnet-5-5
#         - top_k：任何值都拒绝（必须不传 / 不显式写）
#         - top_p：仅接受 1（其它值 raise ValueError，msg: "non-default values"）
#         - temperature：仅接受 1（其它值 raise ValueError，msg: "non-default values"）
#         - thinking.type = "disabled"：禁止（必须省略或用 adaptive）
#         - thinking.type = "enabled" + budget_tokens：禁止（必须用 adaptive + output_config.effort；实测 `:1837-1846`）
# - 以下模型拒收非默认采样参数（provider 层 400 错误，与 LangChain 抛错语义一致）：
#     claude-opus-5 / claude-opus-5-5 / claude-opus-4-8 / claude-opus-4-7 / claude-sonnet-5
#         - model 节强制 temperature = 1.0 / top_p = 1.0 / top_k 必须不传
#         - thinking.type = "enabled" + budget_tokens：禁止（用 adaptive + output_config.effort）
#         - thinking.type = "disabled" + output_config.effort ∈ {"xhigh", "max"}：禁止（实测 `:1848-1860`）
#           —— 用 adaptive thinking，或 omit `thinking`，或把 effort 设为 `high` 或以下
# - 以下模型接受任意 temperature / top_p / top_k：
#     claude-opus-4-6 / claude-sonnet-4-6 / claude-haiku-4-5 及更早模型
#
# 建议：
# - 温度用 1.0 默认；老模型覆盖可放开；新模型必须保持 1.0
# - Sonnet 4.6 / Haiku 4.5 等"老模型"才允许 top_p / top_k 显式覆盖
# - Opus 4.8+ / Sonnet 5.x+ / Fable 5+ 强制 temperature=1.0 + 省略 top_p / top_k
# - 推理模型（Opus 4.6+ / Sonnet 4.5+ / Fable 5+）一律用 `thinking.type = "adaptive"`，
#   显式 budget_tokens 仅在 Sonnet 4.5-4.6 上可用
temperature = 1.0             # 范围：[0.0, 1.0]
max_tokens = 4096             # ⚠️ Anthropic 必填 max_tokens

[anthropic.models.claude-sonnet-4-6]
max_tokens = 4096
temperature = 1.0

[anthropic.models.claude-opus-4-6]
max_tokens = 8192
# Opus 4.6+ 支持 thinking.type = "adaptive"，自动决定 budget
[anthropic.models.claude-opus-4-6.thinking]
type = "adaptive"

[anthropic.models.claude-fable-5]
# ⚠️ 严格模型：temperature / top_p / top_k 都受限制
max_tokens = 8192
temperature = 1.0              # 仅接受 1
# top_p = 1.0                  # 仅接受 1（不要写非 1）
# top_k 必须省略


# -----------------------------------------------------------------------------
# [google] —— Google Gemini
# -----------------------------------------------------------------------------

[google]

# 鉴权密钥。必填。Google AI Studio API key（或 Vertex AI service account JSON）。
# 类型：str
api_key = ""

# 自定义 API 端点。选填。
# 默认："" → 解析层用 "https://generativelanguage.googleapis.com"
api_host = ""

timeout = 60
max_retries = 6

# Google 专属：思考模式。选填。默认 disabled。
# 类型：table
[google.thinking_config]
include_thoughts = false
thinking_budget = 0           # 0 = disabled

temperature = 1.0             # 范围：[0.0, 2.0]
max_tokens = 8192
top_p = 0.95
top_k = 40                    # Google 专属

[google.models.gemini-2.0-flash]
temperature = 1.0
max_tokens = 8192

[google.models.gemini-2.0-pro]
max_tokens = 8192
thinking_budget = 10000       # 此 model 默认开启 thinking


# -----------------------------------------------------------------------------
# [ollama] —— Ollama（本地运行）
# -----------------------------------------------------------------------------

[ollama]

# 鉴权密钥。Ollama 一般不需要鉴权。留空即可。
# 类型：str
# 默认：""
api_key = ""

# API 端点。选填。**特殊值 "default"** 表示 "http://localhost:11434"。
# 类型：str (URL) | "default"
# 默认："default" → 解析层解析为 "http://localhost:11434"
api_host = "default"

# Ollama 专属：上下文窗口大小。选填。默认 2048。
num_ctx = 2048

# Ollama 专属：最大生成 token。选填。默认 -1（不限）。
num_predict = -1

# Ollama 专属：重复惩罚。选填。默认 1.1。
repeat_penalty = 1.1

# Ollama 专属：Mirostat 采样。选填。默认 0（禁用）。
mirostat = 0

timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 2048

[ollama.models.llama3.1-70b]
num_ctx = 8192
temperature = 0.7

[ollama.models.qwen2.5-72b]
num_ctx = 4096


# -----------------------------------------------------------------------------
# [xai] —— xAI Grok
# -----------------------------------------------------------------------------

[xai]

# 鉴权密钥。必填。xAI API key。
api_key = ""

# 自定义 API 端点。选填。
# 默认："" → 解析层用 "https://api.x.ai/v1"
api_host = ""

timeout = 60
max_retries = 6
temperature = 1.0
max_tokens = 16384

# xAI 专属：搜索增强。选填。
# 类型：bool
search_enabled = false

[xai.models.grok-2]
max_tokens = 16384

[xai.models.grok-2-mini]
reasoning_effort = "low"


# -----------------------------------------------------------------------------
# [mistral] —— Mistral AI
# -----------------------------------------------------------------------------

[mistral]

# 鉴权密钥。必填。Mistral API key。
api_key = ""

# 自定义 API 端点。选填。
# 默认："" → 解析层用 "https://api.mistral.ai/v1"
api_host = ""

timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

# Mistral 专属：safe prompt 模式。选填。默认 false。
# 注：LangChain ChatMistralAI 字段名是 `safe_mode`（对应 Mistral 官方 API 的 `safe_prompt`）
safe_mode = false

[mistral.models.mistral-large-latest]
max_tokens = 4096

[mistral.models.pixtral-12b-2409]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [qwen] —— 阿里通义千问（OpenAI 兼容）
# -----------------------------------------------------------------------------

[qwen]

# 鉴权密钥。必填。阿里云百炼 / DashScope API key。
api_key = ""

# 自定义 API 端点。选填。
# 默认："" → 解析层用 "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_host = ""

timeout = 60
max_retries = 6
temperature = 1.0
max_tokens = 4096

# 通义专属：搜索增强。选填。
enable_search = false

# thinking 控制的 per-provider 默认值
# 选填；donkey 应用层分派 Qwen Provider 类时作辅助判断：
# - "qwq"/"reasoner" 后缀的模型 → 走 ChatQwQ（QwenThinkingProvider，思考强制开启）
# - 其它模型（如 qwen-max / qwen-plus）→ 走 ChatQwen（QwenGeneralThinkingProvider）
default_thinking = "auto"     # "auto" | "enabled" | "disabled"

[qwen.models.qwen-max]
max_tokens = 8192

[qwen.models.qwen-vl-max]
# 多模态
max_tokens = 4096

# QwQ 推理模型专用 entries（让用户显式声明这些模型走 ChatQwQ）
[qwen.models.qwq-32b-preview]
max_tokens = 32768

[qwen.models.qwq-plus]
max_tokens = 32768


# -----------------------------------------------------------------------------
# [deepseek] —— DeepSeek（专用 LangChain 类：ChatDeepSeek）
# -----------------------------------------------------------------------------

[deepseek]

# 注：走专用 `ChatDeepSeek` 类（langchain-deepseek）——保留 reasoning_content；
# 禁止走 ChatOpenAI + base_url，否则推理过程会被丢弃。

api_key = ""
# ⚠️ 实测：ChatDeepSeek 的默认端点是 "https://api.deepseek.com/v1"
#    （DEFAULT_API_BASE，带 /v1），且 api_base **可覆盖**（别名 base_url）。
#    另注：ChatDeepSeek 在「api_base == 默认值 且 api_key 为空」时**构造期**即报错
#    （"If using default api base, DEEPSEEK_API_KEY must be set."）——见 §9.1.1。
api_host = "https://api.deepseek.com/v1"
timeout = 60
max_retries = 6
temperature = 1.0
max_tokens = 4096

[deepseek.models.deepseek-chat]
max_tokens = 4096

[deepseek.models.deepseek-reasoner]
# 推理模型：deepseek-reasoner 不支持工具调用；ChatDeepSeek 保留 reasoning_content
max_tokens = 8192
reasoning_effort = "medium"   # "low" | "medium" | "high"


# -----------------------------------------------------------------------------
# [doubao] —— 字节豆包（火山引擎方舟，OpenAI 兼容）
# -----------------------------------------------------------------------------

[doubao]

# 鉴权密钥。必填。火山引擎方舟 API key。
api_key = ""

# 自定义 API 端点。选填。
# 默认："" → 解析层用 "https://ark.cn-beijing.volces.com/api/v3"
api_host = ""

timeout = 60
max_retries = 6
temperature = 1.0
max_tokens = 4096

[doubao.models.doubao-pro-32k]
max_tokens = 32768

[doubao.models.doubao-lite-32k]
max_tokens = 32768


# -----------------------------------------------------------------------------
# [kimi] —— 月之暗面 Kimi（OpenAI 兼容）
# -----------------------------------------------------------------------------

[kimi]

api_key = ""
api_host = ""                 # 默认 "https://api.moonshot.cn/v1"
timeout = 60
max_retries = 6
temperature = 0.3             # Kimi 官方推荐 0.3
max_tokens = 4096

[kimi.models.moonshot-v1-128k]
max_tokens = 128000

[kimi.models.kimi-k2-0711-preview]
max_tokens = 8192


# -----------------------------------------------------------------------------
# [zhipu] —— 智谱 GLM（OpenAI 兼容）
# -----------------------------------------------------------------------------

[zhipu]

api_key = ""
api_host = ""                 # 默认 "https://open.bigmodel.cn/api/paas/v4"
timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

[zhipu.models.glm-4-plus]
max_tokens = 4096

[zhipu.models.glm-4v-plus]
# 多模态
max_tokens = 4096


# -----------------------------------------------------------------------------
# [MiniMax] —— MiniMax M（OpenAI 兼容 + Coding Plan `sk-cp-` 密钥）
# -----------------------------------------------------------------------------

[MiniMax]

# 注：MiniMax 主流用法是 Coding Plan（订阅密钥 sk-cp-...）+ OpenAI 兼容端点
# https://api.minimaxi.com/v1。thinking 以 <think>...</think> 标签保留在 content，
# 应用层用正则提取（见 §3.6）。
#
# 端点差异：
#   - https://api.minimaxi.com/v1  → OpenAI 兼容（Coding Plan 默认；用 ChatOpenAI）
#   - https://api.minimax.io/anthropic → Anthropic SDK 兼容（普通 API key；v2+ 才支持）

api_key = ""                  # 填 sk-cp-... (Coding Plan) 或 MINIMAX_API_KEY (普通 API)
api_host = "https://api.minimaxi.com/v1"  # 默认 Coding Plan OpenAI 兼容端点
timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

# Coding Plan 端点默认 reasoning_split=false，thinking 在 content 里以 <think> 标签包裹。
# 若想让 reasoning 走 reasoning_content 字段（需用 ChatAnthropic 之外的专用类），v2+ 实现。

[MiniMax.models.MiniMax-M3]
max_tokens = 8192

# ⚠️ model_id 含 "." 时**必须加引号**。TOML 裸 key 不允许含 "."，
#    写成 [MiniMax.models.MiniMax-M2.7] 会被解析成嵌套表
#    （MiniMax-M2 → 7），模型表结构被**静默破坏**（models["MiniMax-M2.7"] 永远查不到）。
#    bedrock 的 us.anthropic.claude-sonnet-4-6 同理。
[MiniMax.models."MiniMax-M2.7"]
max_tokens = 4096

[MiniMax.models.MiniMax-M2]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [tencent] —— 腾讯混元（OpenAI 兼容）
# -----------------------------------------------------------------------------

[tencent]

api_key = ""                  # 腾讯云 API SecretId:SecretKey 组合
api_host = ""                 # 默认 "https://api.hunyuan.cloud.tencent.com/v1"
timeout = 60
max_retries = 6
temperature = 1.0
max_tokens = 4096

[tencent.models.hunyuan-pro]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [xiaomi] —— 小米 MiMo
# -----------------------------------------------------------------------------

[xiaomi]

# 多平台路由：
#   - 自托管 → api_key 留空，api_host = "http://localhost:11434"（走 ollama 解析层）
#   - OpenRouter → api_key = OpenRouter key, api_host = "https://openrouter.ai/api/v1"
#   - 官方 → api_key + 官方 api_host
api_key = ""
api_host = ""                 # 取决于平台
timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

[xiaomi.models.mimo-7b-rl]
max_tokens = 4096


# ⚠️ v1 暂不支持以下 provider（推迟 v2+）：
#   [baidu]    百度文心 ERNIE（OAuth + 私有协议）→ 见 §3.5
#   [iflytek]  科大讯飞星火（WebSocket + HMAC-SHA256）→ 见 §3.5
#   [sensetime] 商汤日日新（私有 API）→ 见 §3.5


# -----------------------------------------------------------------------------
# [stepfun] —— 阶跃星辰 Step（OpenAI 兼容）
# -----------------------------------------------------------------------------

[stepfun]

api_key = ""
api_host = ""                 # 默认 stepfun 官方 OpenAI 兼容端点
timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

[stepfun.models.step-2-16k]
max_tokens = 16384

[stepfun.models.step-1v-8k]
# 多模态
max_tokens = 8192


# -----------------------------------------------------------------------------
# [openai-compatible] —— OpenAI Compatible 通用元 provider
# -----------------------------------------------------------------------------

[openai-compatible]

# 鉴权密钥。必填。第三方 OpenAI 兼容服务的 API key。
api_key = ""

# 自定义 API 端点。**必填**（与其它 provider 不同，openai-compatible 必须填 api_host）。
# 类型：str (URL)
# 示例：https://openrouter.ai/api/v1 / https://api.together.xyz/v1
#       https://your-internal-llm.company.com/v1
api_host = ""

# 服务名（仅用于日志 / UI 展示，不影响功能）
service_name = "my-internal-llm"

timeout = 60
max_retries = 6
temperature = 1.0
max_tokens = 4096

[openai-compatible.models.custom-model-name]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [meta] —— Meta Llama（多平台路由）
# -----------------------------------------------------------------------------

[meta]

# 鉴权密钥。取决于平台。
#   - 自托管（Ollama）：留空
#   - 第三方（Replicate / Together / Fireworks）：填对应 key
api_key = ""

# 自定义 API 端点。**必填**。
#   - 自托管：http://localhost:11434
#   - Replicate：https://api.replicate.com/v1
#   - Together：https://api.together.xyz/v1
#   - Fireworks：https://api.fireworks.ai/inference/v1
api_host = ""

# Meta 专属：路由平台。选填。决定解析层用哪个。
# 类型：str
# 取值：ollama | replicate | together | fireworks | baseten
routing_platform = "ollama"

timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

[meta.models.llama-3.1-70b-instruct]
max_tokens = 4096

[meta.models.llama-3.1-405b-instruct]
max_tokens = 8192


# -----------------------------------------------------------------------------
# [bedrock] —— AWS Bedrock（多模型聚合；走 ChatBedrock）
# -----------------------------------------------------------------------------

[bedrock]

# 注：走专用 `ChatBedrock` 类（langchain-aws）。Bedrock 是元 provider，
# 通过 model_provider 字段聚合 Claude / Llama / Mistral / Titan 等模型。

# 采用独立 aws_* 字段 + boto3.Session 显式构造：通过三个独立字段
# aws_access_key_id / aws_secret_access_key / aws_region 显式传给 boto3.Session(...)。
# 构造 Session 时**不会读 env var 和 ~/.aws/credentials**，与 §9.1 立场完全对齐。
# AWS_SESSION_TOKEN 是可选的（IAM 临时凭证场景）。

# AWS IAM access key。必填。
# 类型：str
# 默认："" → 解析层抛 BedrockCredentialsMissingError（exit 18）
aws_access_key_id = ""

# AWS IAM secret access key。必填。
# 类型：str
aws_secret_access_key = ""

# AWS region。必填。
# 类型：str (e.g. "us-east-1" | "eu-west-2")
aws_region = "us-east-1"

# AWS session token（IAM 临时凭证专用）。选填。
# 类型：str
# 默认："" → 不传（走长期凭证）
aws_session_token = ""

# Bedrock 模型路由：必须填具体 Claude / Llama / Titan 模型 ID
# 例：model = "us.anthropic.claude-sonnet-4-6" 或 "meta.llama3-70b-instruct-v1:0"
#
# ⚠️ 若 models 子表用**带 "." 的真实 model_id**（如
#    "us.anthropic.claude-sonnet-4-6"），TOML 裸 key 不允许含 "."，
#    必须加引号 → [bedrock.models."us.anthropic.claude-sonnet-4-6"]
#    否则会被解析成嵌套表（us → anthropic → claude-sonnet-4-6），模型表静默损坏。
#    （下例用短别名规避该问题——两种写法都可以，但**不要混用**。）

timeout = 60
max_retries = 6
temperature = 1.0
max_tokens = 4096

[bedrock.models.claude-sonnet-4-6]
# Bedrock 上的 Claude（与 anthropic 节不同的鉴权路径）
max_tokens = 4096

[bedrock.models.llama-3.1-70b-instruct]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [groq] —— Groq（高速 LPU 推理）
# -----------------------------------------------------------------------------

[groq]

# 走专用 `ChatGroq` 类（langchain-groq）。Groq LPU 推理速度极快（数百 token/s），
# 支持 Llama / Mixtral / Gemma 等开源模型。

api_key = ""
api_host = ""                 # 默认 "https://api.groq.com/openai/v1"（ChatGroq 内部固定）
timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

[groq.models.llama-3.3-70b-versatile]
max_tokens = 4096

[groq.models.mixtral-8x7b-32768]
max_tokens = 32768


# -----------------------------------------------------------------------------
# [fireworks] —— Fireworks AI（多模型推理平台）
# -----------------------------------------------------------------------------

[fireworks]

# 走专用 `ChatFireworks` 类（langchain-fireworks）。Fireworks 部署 100+ 开源模型。

api_key = ""
api_host = ""                 # 默认 "https://api.fireworks.ai/inference/v1"
timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

[fireworks.models.accounts/fireworks/models/llama-v3p3-70b-instruct]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [together] —— Together AI（多模型推理平台）
# -----------------------------------------------------------------------------

[together]

# 走专用 `ChatTogether` 类（langchain-together）。

api_key = ""
api_host = ""                 # 默认 "https://api.together.xyz/v1"
timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

[together.models.meta-llama/Llama-3.3-70B-Instruct-Turbo]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [cohere] —— Cohere（Command R 系列，企业 RAG 强项）
# -----------------------------------------------------------------------------

[cohere]

# 走专用 `ChatCohere` 类（langchain-cohere）。

api_key = ""
api_host = ""                 # 默认 "https://api.cohere.com"
timeout = 60
max_retries = 6
temperature = 0.3
max_tokens = 4096

[cohere.models.command-r-plus]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [perplexity] —— Perplexity（Sonar 系列含联网搜索）
# -----------------------------------------------------------------------------

[perplexity]

# 走专用 `ChatPerplexity` 类（langchain-perplexity）。
# 注：Perplexity Sonar 模型自带联网搜索（不可关闭），需特别注意输出带引用。

api_key = ""
api_host = ""                 # 默认 "https://api.perplexity.ai"
timeout = 60
max_retries = 6
temperature = 0.2
max_tokens = 4096

[perplexity.models.llama-3.1-sonar-large-128k-online]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [databricks] —— Databricks（自家模型 + 开源模型托管）
# -----------------------------------------------------------------------------

[databricks]

# 走专用 `ChatDatabricks` 类（databricks-langchain）。
# 鉴权用 Databricks Personal Access Token + endpoint URL。

api_key = ""
api_host = ""                 # 必填：Databricks endpoint
timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

[databricks.models.databricks-dbrx-instruct]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [cerebras] —— Cerebras（晶圆级推理）
# -----------------------------------------------------------------------------

[cerebras]

# 走专用 `ChatCerebras` 类（langchain-cerebras）。

api_key = ""
api_host = ""                 # 默认 "https://api.cerebras.ai/v1"
timeout = 60
max_retries = 6
temperature = 0.7
max_tokens = 4096

[cerebras.models.llama-3.3-70b]
max_tokens = 4096


# -----------------------------------------------------------------------------
# [openrouter] —— OpenRouter（统一路由 100+ 模型）
# -----------------------------------------------------------------------------

[openrouter]

# ⚠️ 走专用 `ChatOpenRouter` 类（langchain-openrouter）。
# 禁止走 ChatOpenAI + base_url——OpenRouter 自带多 provider routing 和
# reasoning_details 等非标字段，必须用专用类才能完整解析。

api_key = ""

# 自定义 API 端点。**必填**（与 openai-compatible 不同，OpenRouter 官方 endpoint
# 由 ChatOpenRouter 固定为 "https://openrouter.ai/api/v1"，但允许自定义代理）。
api_host = "https://openrouter.ai/api/v1"

# OpenRouter 专属：provider routing 偏好（选填，默认按价格自动）。
# 详见 https://openrouter.ai/docs/provider-routing
provider_preferences = ""     # JSON 字符串，如 '{"order":["anthropic","openai"]}'

timeout = 60
max_retries = 6
temperature = 1.0
max_tokens = 4096

[openrouter.models.auto]
# "auto" 模型让 OpenRouter 自动选择
max_tokens = 4096

[openrouter.models.anthropic/claude-sonnet-4-6]
max_tokens = 4096

[openrouter.models.deepseek/deepseek-chat]
# 经 OpenRouter 调用 DeepSeek——保留 reasoning_content（由 ChatOpenRouter 处理）
max_tokens = 4096

[openrouter.models.openai/o3]
reasoning_effort = "high"     # OpenRouter 透传
```

---

## 9. 鉴权设计：TOML 明文强制

### 9.1 为什么不读环境变量（P-2 理由）

| 反对理由 | 解释 |
|---|---|
| **跨 OS 不一致** | Windows 用 `%VAR%` / PowerShell `$env:VAR` / WSL `/proc/self/environ`；macOS / Linux 用 `$VAR`；Cygwin / MSYS2 行为又不同。本项目跨 OS 一致性要求 → 不依赖环境变量 |
| **workspace 移植后行为不可控** | 用户在 Mac 上 `export OPENAI_API_KEY=sk-xxx` 后跑通；把 workspace zip 拷到 Linux 服务器 → 服务器上没设环境变量 → 行为完全变样。**这违反 workspace 高度可移植性** |
| **CI/CD 与本地开发割裂** | 本地有 env var → CI 没设 → CI 失败 |
| **donkey 是智能体材料层，不是 12-factor SaaS** | workspace = 智能体的全部材料层；`instruction.md` / `tools/*.py` 都是明文入文件；`api_key` 与之同质，不应特殊对待 |
| **用户自负责任** | 写明"workspace 入 git 后密钥泄露由用户自负"是合理风险声明（详见 §13.3） |

### 9.1.1 LangChain env var 回退条件澄清

> donkey 的"不读 env var"立场与 LangChain 默认行为之间存在一个"墙角"——本节澄清它。

**LangChain 1.x 实际行为**（实测源码 `langchain_core/utils/_gateway.py:106-179` 函数 `_resolve_gateway_config`）：

```python
if api_key is not None:
    resolved_api_key = api_key     # ← 显式传递（包括 ""）一律原样返回，不回退
else:
    gateway_api_key = ...
    provider_api_key = _first_env(api_key_env)    # ← api_key=None 才回退到 env var
    resolved_api_key = SecretStr(chosen) if chosen else None
```

调用链（`langchain_openai/chat_models/base.py:1419-1428`）：每个 ChatModel 类的 `__init__` 把 `api_key` 字段传给 `_resolve_gateway_config(..., api_key_env="OPENAI_API_KEY")`——回退 env var 列表由 `_first_env(api_key_env)` 决定。

各 ChatModel 类的 `api_key` 字段默认值都用 `default_factory=secret_from_env(...)`（即如果用户没传 `api_key`，字段值是 `None`，触发 env var 回退）：

- `langchain_deepseek/chat_models.py:250`：`default_factory=secret_from_env("DEEPSEEK_API_KEY", default=None)`
- `langchain_qwq/base.py:37`：`default_factory=secret_from_env("DASHSCOPE_API_KEY", default=None)`
- `langchain_moonshot/chat_models/base.py`：类似

**关键结论**：

| TOML 配置 | donkey TOML loader 行为 | 传给 LangChain 的值 | 是否触发 env var 回退 |
|---|---|---|---|
| `api_key = ""` | 显式空串 | `api_key=""` | ❌ 不触发（`api_key is not None` 分支） |
| `api_key = "sk-xxx"` | 显式值 | `api_key="sk-xxx"` | ❌ 不触发 |
| `api_key` 字段缺失 | loader 返回 `None`（错误实现） | `api_key=None` | ✅ 触发 `OPENAI_API_KEY` 等 |
| `api_key` 字段缺失 | **loader 强制 `""` 默认值** | `api_key=""` | ❌ 不触发 |

**TOML loader 实现守则**：

```python
# donkey/core/llm/schema/loader.py 的参考实现
import tomllib

def load_api_key(provider_section: dict[str, Any] | None) -> str:
    """读取 provider 节下的 api_key 字段；缺失或 None 一律返回 ""（空串）。"""
    if not provider_section:
        return ""
    raw = provider_section.get("api_key")
    # 缺失 → "" 或 None → "" （绝对不能 None 透传，触发 LangChain env var 回退）
    if raw is None:
        return ""
    return str(raw)
```

**强约束**：
1. **缺失 → `""`**：tomllib / 任何 TOML 解析器的"键不存在"必须规范化为 `""`，**绝不传 `None`**。
2. **`None` 显式 → `""`**：用户写 `api_key = ""` 或 `api_key = null`（TOML 里 `null` 即 Python `None`）都规范化为 `""`。
3. **非字符串值 → type error**：TOML 1.0 合法值只有 str / int / float / bool / array / table / datetime，**TOML schema 校验（F002 load）必须拒绝非字符串 `api_key`**（如 `api_key = 42` 或 `api_key = ["..."]`）——避免 LangChain 收到奇怪类型。
4. **`bedrock` 例外**：`[bedrock]` 不使用 `api_key` 字段（改用 `aws_access_key_id` / `aws_secret_access_key` / `aws_region` 独立字段，详见 §8 `[bedrock]` 注释），`boto3.Session(...)` 显式构造**不会读 env var**，与 §9.1 立场完全对齐。
5. **`ollama` 例外**：`api_key = ""` 是合法的（Ollama 默认无鉴权），无 warning，无报错。

> **实测补充——`api_key = ""` 的真实终点**：
>
> 上表第 1 / 4 行（`api_key=""`）在 **LangChain 层完全成立**（`_resolve_gateway_config` 走 `api_key is not None` 分支，**确实不回退 env var**）。但实测发现**下一层**还有一道关：
>
> | 层 | 空 `api_key` 的行为 | 证据 |
> |---|---|---|
> | LangChain `_resolve_gateway_config` | ✅ 原样透传 `""`，**不回退 env var** | `langchain_core/utils/_gateway.py:106-179` |
> | **openai SDK（构造 client 时）** | ❌ **直接拒绝**：`OpenAIError: Missing credentials. Please pass an 'api_key' ... or set the 'OPENAI_API_KEY' ... environment variable.` | `openai/_base_client.py`（`api_key` 为空串即视为未提供） |
> | `ChatDeepSeek`（构造时） | ❌ **直接拒绝**：`ValueError: If using default api base, DEEPSEEK_API_KEY must be set.`（仅当 `api_base` 为默认值时触发） | `langchain_deepseek/chat_models.py:303-307` |
>
> **推论（影响 §7.3 / §9.2 的 warning 语义）**：
> 1. 空 `api_key` 的失败点发生在**构造 ChatModel / client 阶段**，**不是**运行时的 401 → 运行时映射应按 §4.3.1 的**构造期行**处理（→ exit 90）；
> 2. 异常文案**直接指向 env var**，与 §9.1 立场正面冲突 → CLI 层**必须改写文案**（"api_key 未配置或为空，请检查 provider.toml"），不得把用户引向 `export OPENAI_API_KEY`；
> 3. **不改变**"donkey 不读 env var"的立场：LangChain 层确实没读，是底层 SDK 自己的报错文案在提 env var。

### 9.2 `api_key` 强制明文

> **联网调研结论——空 `api_key` 的合法性是 provider 属性，不是全局规则**
>
> 调研问题："是否有很多智能体允许空 `api_key`？" 答案：**取决于该 provider 的端点是否校验鉴权**，业界分成三档：
>
> | 端点类型 | 官方证据 | 空 `api_key` |
> |---|---|---|
> | **Ollama 本地 server** | 官方 OpenAI 兼容文档：*"The client requires an API key value, but **Ollama ignores it**"*，示例 `api_key='ollama',  # required but ignored`；curl 示例**完全不带** `Authorization` header | ✅ 服务端**不校验** |
> | **vLLM 本地 server** | 官方 `--api-key`：*"**If provided**, the server will require one of these keys to be presented in the header"* → **默认不传 = 不校验** | ✅ 服务端**不校验** |
> | **LiteLLM proxy / 任意 OpenAI 兼容端点** | 官方 config 支持 `api_key: <your-vllm-api-key\|none>`；官方示例 `openai.OpenAI(api_key="anything", base_url=...)` | ⚠️ **端点属性运行时才知道** |
> | **云端 provider**（OpenAI / Anthropic / DeepSeek / MiniMax / qwen …） | key 是真实凭据，服务端强校验 | ❌ **必须有效** |
>
> **但"允许空"≠"可以传空串"**——实测（openai SDK 3.35.1）：
>
> | 事实 | 证据 |
> |---|---|
> | `openai.OpenAI(api_key="")` → **构造期就抛** `OpenAIError: Missing credentials` | SDK 把空串视为"未提供" |
> | `openai.OpenAI(api_key="not-needed")` / `("ollama")` → 构造成功 | 任意**非空**占位符都可用 |
> | `ChatOllama` **根本没有 `api_key` 字段** | 本地 provider 不经过 openai SDK，压根不需要 key |
>
> **推论**：空 `api_key` 的合法性与"SDK 能否构造"是两个问题——**donkey 允许空 key 的 provider，解析层必须主动填一个占位符**，否则用户明明配对了（本地端点不校验），却在构造期炸掉。
>
> **按 provider 分三档**：
>
> | 档 | provider | 空 `api_key` | F002 load 行为 | 解析层实现 |
> |---|---|---|---|---|
> | **A. 无鉴权本地** | `ollama`、`meta`（自托管路由） | ✅ **合法** | 无 warning | `ChatOllama`（无 `api_key` 字段），直接传 `""` |
> | **B. 端点属性未知** | `openai-compatible`（可能指本地 vLLM，也可能指云端中转站）、`xiaomi`（多平台路由：OpenRouter 云端 / Ollama 本地） | ✅ **合法** | **warning**（exit 0）："该端点是否校验鉴权未知" | **填占位符**（`"not-needed"`）再构造 `ChatOpenAI` / `ChatOpenRouter` |
> | **C. 云端 provider** | 其余 21 个：openai / anthropic / google / xai / mistral / qwen / deepseek / doubao / kimi / zhipu / MiniMax / tencent / stepfun / groq / fireworks / together / cohere / perplexity / databricks / cerebras / openrouter | ❌ **非法** | **硬错 exit 11**（`ProviderTomlFieldError`） | — |
> | **（不适用）** | `bedrock`——**不使用 `api_key` 字段**（用 `aws_secret_access_key` 等 4 个独立字段，见 §8.1 注 2） | — | 不适用 | `boto3.Session(...)` 显式构造 |
>
> **为什么 C 档选"硬错"而不是 warning**：
> 1. **实测**：C 档的空 key 100% 在**构造期**失败（§9.1.1），错误信息还指向 env var（违背 P-2 立场）→ 早失败、错误更准；
> 2. **用户修复动作唯一**："把 key 填上" —— 与 §7.3 的"warning = 可恢复的小问题，error = 必须用户决策的硬问题"边界一致；
> 3. **不牺牲可移植性**：A / B 档的本地端点**本来就不需要真 key**，C 档的云端端点**本来就需要真 key** —— 两者在 TOML 里都是"填不填"这一件事，没有引入任何 env var 依赖（P-2 不受影响）。
>
> **占位符不违背 P-2**：占位符是 donkey **自己生成的常量**（不是从 env var 读来的），且只对"该端点不校验鉴权"的 provider 使用。

> **F002 load 校验规则**：
>
> - **按上表分档**校验：A 档（`ollama` / `meta`）空 `api_key` 合法无 warning；B 档（`openai-compatible` / `xiaomi`）空 `api_key` 合法但出 warning；C 档（云端 provider 21 个）空 `api_key` → **exit 11 硬错**（`ProviderTomlFieldError`）；`bedrock` 不用 `api_key` 字段，不参与本规则；
> - 解析层**只**从 TOML 读 `api_key`，**不**调 `os.environ.get("OPENAI_API_KEY")` 等环境变量查找函数；
> - 解析层**不**支持 `{env:XXX}` 占位符（v1 OpenCode 风格的占位符）；
> - 解析层**不**支持 dotenv 文件加载（v1 LangChain 风格的 dotenv 行为）；
> - 解析层 loader 必须遵循 §9.1.1 第 1-3 条**强约束**（缺失 → `""`，None → `""`，非 str → 拒绝）；
> - **B 档占位符兜底**：`openai-compatible` / `xiaomi` 的 `api_key` 为空时，解析层在构造 `ChatOpenAI` / `ChatOpenRouter` 前填入占位符 `"not-needed"`（openai SDK 拒绝空串，见 §9.1.1 实测表）——**不读 env var、不引入外部依赖**。

### 9.3 workspace 加密（v2+ 候选）

| 方案 | 实现 | v1 状态 |
|---|---|---|
| **明文 TOML** | 直接存 `api_key = "sk-..."` | ✅ v1 默认 |
| **外部密钥文件**（如 `~/.config/donkey/secrets.toml`） | 解析层在 TOML `api_key = "@secrets.toml:openai.api_key"` 时跳板加载 | ❌ v1 不实现 |
| **系统 keyring** | 解析层在 TOML `api_key = "@keyring:openai"` 时调 keyring | ❌ v1 不实现 |
| **对称加密** | 用户 `donkey config encrypt --password xxx` → TOML 整体 AES 加密 | ❌ v1 不实现 |
| **pass / GPG / age** | 解析层支持从 pass store / gpg / age 取密钥 | ❌ v1 不实现 |

**v1 决定**：仅明文 TOML，**不**实现任何加密 / 外部密钥机制。用户如担心泄露：

1. 将 `provider.toml` 加入 `.gitignore`；
2. 团队共享时使用脱敏的 `provider.toml.example`（含 `api_key = "REPLACE_ME"`）+ 单独的安全分发渠道传真实 key。

### 9.4 网络出口的 env var 依赖（§9.1 立场的边界）

> **本节澄清 §9.1「不读环境变量」的适用范围**——它约束的是 **api_key（鉴权凭据）**，**不约束网络出口（代理）**。

| 维度 | api_key | 网络出口（代理） |
|---|---|---|
| 是否读 env var | ❌ **绝不读**（P-2）——loader 强制 `""` 归一化，杜绝 `OPENAI_API_KEY` 等回退 | ✅ **会读**（httpx / openai SDK 默认行为）：`ALL_PROXY` / `HTTPS_PROXY` / `HTTP_PROXY` |
| 落在哪一层 | 解析层 / 应用层 | **网络层**（§2.2） |
| 可控性 | donkey 完全掌控（TOML 明文） | **由用户机器的环境决定** |

**实测事实**（httpx 0.28.1 + openai 3.35.1）：

1. httpx 的代理 scheme 白名单只有 `http` / `https` / **`socks5`** / **`socks5h`**（源码 `httpx/_config.py:212`）——老写法 **`socks://` 已被移除**，遇到即抛
   `ValueError: Unknown scheme for proxy URL`，且**发生在构造 client 阶段**（一条请求都发不出去）；
2. `socks5://` 还需 `socksio` 扩展（`pip install 'httpx[socks]'`），否则同样在构造期报错；
3. 该错误会连带击穿 LangChain 内部自建 client 的路径（`ChatDeepSeek.validate_environment` 里 `openai.OpenAI(...)` 构造失败 → pydantic 包成 `ValidationError`）。

**donkey v1 立场**：

- **不主动读、不主动写**代理 env var——但**必须**在构造任何 client 之前做一次**防御性检查**（见下方实现要点），否则用户本机的代理配置会让所有 provider 调用在构造期崩掉（表现为"配置看起来完全正确，但一条请求都发不出去"）；
- 该检查**只做环境适配，不改变网络语义**：能识别 `socks://` → 改写为 `socks5://`（装了 `socksio` 时）；缺 `socksio` → 摘除该代理变量退回直连，并打印可操作的诊断；
- **与 G-3（跨 OS 行为一致）的关系**：§9.1 保证了"**凭据**行为跨 OS 一致"，但"**出口**行为"仍随机器环境变化——README 的风险声明里应如实写明这一条（详见 §13.3 建议补充项）。

**实现要点**（`donkey/core/llm/network/transport.py` 建议伪代码）：

```python
# 在创建任何 httpx client 之前调用一次
def sanitize_proxy_env() -> None:
    """防御性处理：httpx 不认的 socks scheme / 缺失 socksio 扩展时的降级。"""
    try:
        import socksio  # noqa: F401
        has_socks = True
    except ImportError:
        has_socks = False
    for name in ("ALL_PROXY", "all_proxy", "HTTPS_PROXY", "https_proxy",
                 "HTTP_PROXY", "http_proxy"):
        value = os.environ.get(name)
        if not value or not value.lower().startswith("socks"):
            continue
        if not has_socks:
            os.environ.pop(name, None)          # 缺 socksio → 退回直连
            continue
        if value.lower().startswith("socks://"):
            os.environ[name] = "socks5://" + value[len("socks://"):]   # 改写 scheme
```

---

## 10. base_url 通用可选 + "default" 特殊值

### 10.1 api_host 规则

| provider | `api_host` 必填？ | "default" 特殊值 | 默认值（`api_host = ""` 时） |
|---|---|---|---|
| openai | ❌ | ❌ | `https://api.openai.com/v1` |
| anthropic | ❌ | ❌ | `https://api.anthropic.com` |
| google | ❌ | ❌ | `https://generativelanguage.googleapis.com` |
| **ollama** | ❌ | ✅ `default` = `http://localhost:11434` | `http://localhost:11434` |
| xai | ❌ | ❌ | `https://api.x.ai/v1` |
| mistral | ❌ | ❌ | `https://api.mistral.ai/v1` |
| qwen | ❌ | ❌ | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| deepseek | ❌ | ❌ | `https://api.deepseek.com/v1`（`ChatDeepSeek.DEFAULT_API_BASE`）——实测 `ChatDeepSeek.api_base` **可以覆盖**（字段别名 `base_url`） |
| doubao | ❌ | ❌ | `https://ark.cn-beijing.volces.com/api/v3` |
| kimi | ❌ | ❌ | `https://api.moonshot.cn/v1` |
| zhipu | ❌ | ❌ | `https://open.bigmodel.cn/api/paas/v4` |
| MiniMax | ❌ | ❌ | `https://api.minimaxi.com/v1`（OpenAI 兼容 + `sk-cp-` Coding Plan）|
| tencent | ❌ | ❌ | `https://api.hunyuan.cloud.tencent.com/v1` |
| xiaomi | ❌ | ❌ | 取决于平台（多路由） |
| stepfun | ❌ | ❌ | stepfun 官方 |
| bedrock | ❌ | ❌ | 不需要 `api_host`；AWS region 走独立 `aws_region` 字段；走 `boto3.Session(...)` 显式构造 |
| groq | ❌ | ❌ | `https://api.groq.com/openai/v1` |
| fireworks | ❌ | ❌ | `https://api.fireworks.ai/inference/v1` |
| together | ❌ | ❌ | `https://api.together.xyz/v1` |
| cohere | ❌ | ❌ | `https://api.cohere.com` |
| perplexity | ❌ | ❌ | `https://api.perplexity.ai` |
| databricks | **✅ 必填** | ❌ | （无默认；需 Databricks endpoint URL） |
| cerebras | ❌ | ❌ | `https://api.cerebras.ai/v1` |
| openrouter | ❌ | ❌ | `https://openrouter.ai/api/v1` |
| **openai-compatible** | **✅ 必填** | ❌ | （无默认） |
| **meta** | **✅ 必填** | ❌ | （无默认；取决于平台） |

### 10.2 解析层"default"处理逻辑

```python
def resolve_api_host(provider: str, configured: str) -> str:
    """解析 api_host 配置。
    
    规则：
      - "default" 特殊值 → 用 provider 默认 URL
      - "" 空字符串   → 用 provider 默认 URL
      - 其它字符串    → 视为 URL 直接使用
    """
    if configured in ("", "default"):
        return PROVIDER_DEFAULT_API_HOST[provider]
    return configured
```

### 10.3 Ollama 小白用户友好设计

场景：用户第一次跑 Ollama，在本机启动 `ollama serve`（默认监听 `http://localhost:11434`），然后跑 donkey。

推荐配置：

```toml
[ollama]
api_key = ""
api_host = "default"     # 或留空
```

- 解析层把 `"default"` / `""` 解析为 `http://localhost:11434`；
- 用户**无需知道** Ollama 默认端口是什么；
- 若用户改了 Ollama 端口（如 `OLLAMA_HOST=0.0.0.0:8888`），则填 `api_host = "http://localhost:8888"` 即可。

### 10.4 openai-compatible 必填 api_host 的理由

| 场景 | api_host | 解析层 |
|---|---|---|
| OpenRouter | `https://openrouter.ai/api/v1` | ChatOpenAI |
| Together AI | `https://api.together.xyz/v1` | ChatOpenAI |
| vLLM 自托管 | `http://localhost:8000/v1` | ChatOpenAI |
| 内部 Newapi / Oneapi | `https://newapi.company.com/v1` | ChatOpenAI |
| 中转站 | `https://api.provider-reseller.com/v1` | ChatOpenAI |

openai-compatible **没有"官方 endpoint"**——用户必须显式告诉解析层"去哪儿请求"，因此 `api_host` 必填。

---

## 11. 字段全集与校验规则

### 11.1 F002 load 校验清单

> exit 11 严格归 `ProviderTomlLoadError` **伞形 Error class**（详见 `harness/features/README.md §3.2.1`）。所有"`provider.toml` 加载失败"在 CLI 层映射同一 exit 11；子类 Error class（如下表 4-7 列）在 traceback 与 logging 中**仍可区分具体原因**，便于排查。

| # | 校验项 | 触发 | 严重度 | 伞形 Error class · 子类 | exit code |
|---|---|---|---|---|---|
| 1 | TOML 语法解析 | `tomllib.TOMLDecodeError` | error | `ProviderTomlLoadError` · `ProviderTomlSyntaxError` | 11 |
| 2 | 顶层 `default_provider` 缺失 | — | error | `ProviderTomlLoadError` · `ProviderTomlFieldError` | 11 |
| 3 | 顶层 `default_model` 缺失 | — | error | `ProviderTomlLoadError` · `ProviderTomlFieldError` | 11 |
| 4 | `default_provider` ∉ 白名单 | 不在 v1 26 家 | error | `ProviderTomlLoadError` · `ProviderTomlScopeError` | 11 |
| 5 | `default_provider` ∈ 永久黑名单 | v1 空集合（占位行） | error | `ProviderTomlLoadError` · `ProviderTomlScopeError` | 11 |
| 6 | `default_provider` ∈ 暂不支持清单 | v1 阶段空集合（占位行） | error | `ProviderTomlLoadError` · `ProviderTomlScopeError` | 11 |
| 7 | `default_provider` ∈ v2+ 候选（baidu / iflytek / sensetime） | v1 不支持 | error | `ProviderTomlLoadError` · `ProviderTomlScopeError` | 11 |
| 8 | `[<未列入 §3.1 或 §3.5 的 provider_id>]` 任何节 | v1 范围校验 | error | `ProviderTomlLoadError` · `ProviderTomlScopeError` | 11 |
| 9 | provider 节内字段拼写错误 | Pydantic `ValidationError`（unknown field） | error | `ProviderTomlLoadError` · `ProviderTomlFieldError` | 11 |
| 10 | provider 节内字段值类型错 | Pydantic `ValidationError`（type mismatch） | error | `ProviderTomlLoadError` · `ProviderTomlFieldTypeError` | 11 |
| 11 | 字段值**硬越界**（`temperature = 3.0` / `api_host` 非 URL 格式） | Pydantic `ValidationError` | error | `ProviderTomlLoadError` · `ProviderTomlFieldValueError` | 11 |
| 12 | `default_model` 不在该 provider 的 `models` 表 | 解析时找不到 | error | `ProviderTomlLoadError` · `ProviderTomlMissingModelError` | 11 |
| 13 | provider 类的 langchain 不允许 `api_host` 覆盖（如 Bedrock via Converse） | langchain 异常 | error | `ProviderTomlLoadError` · `ProviderTomlHostNotAllowedError` | 11 |
| 14 | 字段值**软越界**（`temperature > 1.5` 不超规但偏高；硬边界 = `[0.0, 2.0]`，见 #11） | Pydantic `ValidationError`（range） | **warning** | — | **0** |
| 15 | `api_key` 空字符串——**C 档云端 provider**（21 个，见 §9.2 分档表） | — | **error** | `ProviderTomlLoadError` · `ProviderTomlFieldError` | **11** |
| 16 | `api_key` 空字符串——**B 档**（`openai-compatible` / `xiaomi`，端点是否校验鉴权未知） | — | **warning** | — | **0** |
| 17 | `api_key` 空字符串——**A 档本地 provider**（`ollama` / `meta`） | — | 无（合法） | — | — |
| 18 | `api_host` = `"default"` 但 provider ≠ `ollama` | 解析层视为普通 URL | **warning** | — | **0** |
| 19 | `bedrock` 凭据缺失（`aws_secret_access_key` 等 4 个 `aws_*` 字段为空） | `[bedrock]` 不用 `api_key` | **error** | `ProviderTomlLoadError` · `ProviderTomlFieldError` | **11** |

> - **#15 空 `api_key` 在 C 档是 error（exit 11）**——实测 C 档（云端）空 key 100% 在**构造期**失败（§9.1.1），且报错文案指向 env var（违背 P-2）；而本地端点（Ollama / vLLM / LiteLLM）**本来就不校验鉴权**，一刀切会误伤本地场景 → 按 provider 分三档（#15 / #16 / #17）。
> - **#16 B 档含 `xiaomi`**——多平台路由（OpenRouter 云端 / Ollama 本地），鉴权属性由用户选的平台决定，服务端是否校验**运行时才知道** → 与 `openai-compatible` 同档（warning + 占位符），不按 C 档硬错处理。
> - **#7 的子类名统一**——v2+ 候选不设独立错误类，归入 `ProviderTomlScopeError`（见 §7.3）。

> **对应 README §3.2**：上表 1-13 是 exit 11（`ProviderTomlLoadError` 伞形）的具体子场景。

### 11.2 警告 vs 错误的边界

| 类别 | 严重度 | F002 load 行为 | exit code |
|---|---|---|---|
| **`provider.toml` 配置 hard error**（TOML parse / 字段拼写 / 字段类型 / 字段值硬越界 / scope 不在白名单） | error | exit 11，阻止 load | **11** |
| **其它配置文件 hard error**（`mcp.json` 解析失败 / `SKILL.md` frontmatter 错） | error | exit 12 / 13，阻止 load | 12 / 13 |
| **`instruction.md` 缺失 / 模型连通 / sqlite schema** | error | exit 14 / 15 / 16，阻止 load | 14 / 15 / 16 |
| **`tools/*.py` / `SKILL.md` 加载 / `MCP` server** | error | exit 17 / 18 / 19，阻止 load | 17 / 18 / 19 |
| **warning 类**（字段值软越界 / B 档 `api_key` 缺失 / `api_host` 填 `"default"` 但 provider ≠ `ollama`） | warning | 不阻塞 load，打印 warning 到 stderr | **0** |

**奥卡姆原则**：warning 不阻塞 load；error 必阻塞 load。**warning 留给"可恢复"的小问题，error 留给"必须用户决策"的硬问题**。

> 上表是按 README §3.2 严格 1:1 映射的"配置错误 → exit code"对照表。如果未来发现某类硬错误实际用户修复动作不同，可从 F002 段位 20 预留位、F003 段位 21-30 留接口位、或 F004-P7 预留 95-100 区借位；具体在 Maintainer 走"新增预留位"流程（详见 §14.5）。

---

## 12. Web UI 设计考量

### 12.1 UI 结构

Web UI 应按以下结构渲染 `provider.toml`：

```
┌────────────────────────────────────────────────────────┐
│  模型配置 (provider.toml)                              │
├────────────────────────────────────────────────────────┤
│  [全局]                                                │
│    默认 provider:  [openai ▼]                          │
│    默认 model:    [gpt-4o        ▼]  ← 动态从 provider 拉 │
├────────────────────────────────────────────────────────┤
│  [Provider Tabs]                                       │
│    [OpenAI] [Anthropic] [Google] [Ollama] [...]        │
│                                                        │
│  当前 tab: OpenAI                                      │
│    api_key:         [••••••]   [显示]  [清空]          │
│    api_host:        [          ]   [使用默认]           │
│    openai_organization: [                              ]│
│    openai_project:       [                              ]│
│    timeout:  [60]  max_retries:  [6]                   │
│    默认 temperature:  [1.0]   默认 max_tokens: [16384]  │
│                                                        │
│    [已注册模型]                                         │
│      • gpt-4o         (temperature: 1.0, max_tokens: 16384) [编辑] [删除]│
│      • o3             (reasoning_effort: high)         │
│      [添加模型]                                         │
├────────────────────────────────────────────────────────┤
│  [测试连接]                                            │
│    [测试]  ← 点击后调后端 init_chat_model + ping       │
│    [显示生效配置]  ← 展示 env var 解析后的最终配置     │
└────────────────────────────────────────────────────────┘
```

### 12.2 关键功能

| 功能 | 实现要点 |
|---|---|
| **Provider 切换** | `<select>` 切换时联动：重新拉取该 provider 的默认 `api_host` / 默认 `temperature` 等 |
| **API Key 隐藏** | `<input type="password">` + "显示"按钮；表单重新加载时**不**回显原值，显示 `已配置（••••••）` |
| **"default" 特殊值** | `api_host` 输入框下方有占位符 `[使用默认值]` 按钮；Ollama 提示"localhost:11434" |
| **模型动态列表** | `api_host` 填好后，"添加模型"按钮触发后端调用 provider 列表 API（OpenAI `/v1/models`） |
| **测试连接** | 后端组装配置（仅 TOML 字段，不读 env var）→ `init_chat_model.invoke("ping")` → 返回结果 |
| **显示生效配置** | 展示"环境变量解析后"的最终配置（仅供 debug；本项目**不读 env var**，所以"生效配置" = TOML 原文） |
| **批量保存** | 修改完所有 tab 后，"保存"按钮写回 `provider.toml`；原子写入（写临时文件 + `os.replace`） |

### 12.3 字段 help_text

每个字段在 UI 上挂 tooltip，文本来自 TOML 注释（§8 全局模板中的 `#` 注释）。**§8 的注释即 UI 的 help_text 单一来源**。

### 12.4 不应做的

- ❌ **不**应展示用户的明文 api_key（即使在测试连接页面）；
- ❌ **不**应支持环境变量引用（违反 P-2）；
- ❌ **不**应在 localStorage / sessionStorage 缓存 api_key；
- ❌ **不**应通过 HTTP（明文）提交 api_key（HTTPS 强制）；
- ❌ **不**应"智能推荐"用户改 base_url——`api_host` 留空就用默认。

---

## 13. 安全性考量

### 13.1 密钥存储

| 场景 | 安全要求 |
|---|---|
| **TOML 文件权限** | `chmod 600 provider.toml`（仅 owner 可读写），`donkey init` 生成后自动设置 |
| **git 跟踪** | `provider.toml` **默认入 git**（P-2 明文策略）；用户在 README / .gitignore 中明确说明风险 |
| **团队共享** | 团队共享 `provider.toml.example`（含 `api_key = "REPLACE_ME"`），真实 key 通过密钥管理工具分发 |
| **Web 提交** | 强制 HTTPS；后端不打印 api_key 到日志 |
| **异常 traceback** | api_key / api_secret 等敏感字段在 `__repr__` 中脱敏（参考 pydantic `SecretStr`） |

### 13.2 错误输出脱敏规则

| 输出场景 | 脱敏要求 |
|---|---|
| **`donkey load` 报错到 stderr** | 任何包含 `api_key` / `secret_key` / `api_secret` / `access_token` 字段值的字符串必须替换为 `***REDACTED***` |
| **异常 traceback** | 同上 + 自定义 dataclass `__repr__` 让敏感字段自动脱敏 |
| **日志** | `logging.Filter` 拦截含敏感字段的 log record |
| **测试输出** | 测试代码中密钥必须是固定 mock 值，不写真实密钥 |
| **Web UI 错误显示** | 任何含密钥的字段显示 `***REDACTED***` |

### 13.3 workspace 移植时的风险

> **风险声明（README 中必须含）**：
>
> 本项目 `provider.toml` 文件以**明文**存储各 provider 的 API key。若用户将 workspace 整体上传到公开 git 仓库 / 共享链接 / 截图泄露 / 备份到云盘等，**API key 可能泄露并被滥用**。**用户自负全部责任**。
>
> 缓解措施：
> 1. 仅在私有 git 仓库 / 受控环境存储 `provider.toml`；
> 2. 团队协作时使用 `provider.toml.example` 模板 + 单独分发真实 key；
> 3. 在云 provider（OpenAI / Anthropic 等）控制台为 key 设置 IP 白名单 / 用量上限 / 失效策略；
> 4. 定期轮换 API key。
>
> **网络出口（代理）的环境依赖声明**——§9.1 保证的是"**凭据**行为跨 OS 一致"，但**网络出口**仍由用户机器的环境变量决定（`ALL_PROXY` / `HTTPS_PROXY` / `HTTP_PROXY`，httpx / openai SDK 默认读取）。因此：
> - 同一个 workspace 在"开了代理"与"没开代理"的机器上，**出口 IP 与可达性不同**（实测：直连不可达 / 经代理可达）；
> - 代理 env var 的 **scheme 写法**也有版本坑（httpx 0.28 只认 `socks5://` / `socks5h://`，老写法 `socks://` 已移除 → 需 `socksio` 扩展），详见 §9.4；
> - README 风险声明应如实写明："**API key 不读环境变量（跨 OS 一致），但网络出口仍可能受本机代理设置影响**"。

### 13.4 永久黑名单治理（硬理由 + GitHub issue 流程）

> 本节按 §3.0 治理原则强化永久黑名单的**前置流程**——任何 provider 入列前必须经 GitHub issue 公开硬理由 + 用户社区评审窗口期 ≥ 14 天，**才**可写入本节。Maintainer 个人立场 / 政治 / 地缘偏好**绝不**构成黑名单"硬理由"。

| 维度 | 永久黑名单（§13.4） | 暂不支持清单（§14.7） |
|---|---|---|
| 触发场景 | 硬性合规 / 法律 / 商业禁止（具体条文） | LangChain 官方支持但本项目尚未投入维护工作量；或 v2+ 自研候选暂未实现 |
| 入列前置流程 | GitHub issue + 硬理由 + 用户社区评审 ≥14 天 | Maintainer 在 §14.7 流程里记录工作量评估 |
| v1 行为 | 拒绝支持；F002 报 `BlacklistedProviderError` | F002 报 `ProviderTomlScopeError`（若该 provider 满足 §3.0 表"必须"维度，必须升级到白名单或 v2+ 候选） |
| 当前成员 | **（v1 空集合）** | **（v1 空集合）** |
| 升级路径 | 须 Maintainer 重新走 GitHub issue + 撤销决议 | 仅需评估工作量 + 写解析代码 + 改文档 |

**永久黑名单添加流程**（v2+ 候选，v1 不会启用）：

1. **GitHub issue 公开硬理由**：
   - 不得使用"未调研 / 优先级靠后 / 个人偏好"等主观理由；
   - 必须引用具体合规条款 / 法律条文 / 商业协议条款编号；
   - 必须公开 Maintainer 决议记录的链接；
2. **用户社区评审窗口期 ≥ 14 天**：
   - 公开 issue 至少保留 14 天供社区评议；
   - 必须至少有 2 名非提议 Maintainer 联署通过；
3. **代码与文档落地**：
   - 在 `donkey/core/llm/providers/_v1_scope.py` 中 `PROVIDER_BLACKLIST` dict 添加 `provider_id` + reason（结构与现有 v1 空集合定义一致）；
   - 解析层启动时加载黑名单 → 任何 `[<provider_id>]` 节或顶层 `default_provider = "<provider_id>"` 触发 exit 11（`BlacklistedProviderError`）；
   - 文档同步更新（包括 §3.0 / §3.3 / §13.4）；
4. **下任 Maintainer 复核窗口**：
   - 新 Maintainer 上任 30 天内有权在无评审期的情况下撤销任何前任的黑名单条目；撤销后须在 14 天内走新增流程重新评估。

**v1 当前状态与原则**：

- **§3.0 Provider 治理原则**是本节与 §14.7 / §3.3 / §15.4 等所有 provider 范围决策的**最高优先级原则**——本节任何条款与 §3.0 冲突时以 §3.0 为准。
- 永久黑名单必须有合规 / 法律 / 商业**硬理由**（例：某厂商 SDK 条款明确禁止第三方集成；某地区监管明令禁止接入；某协议条款限制特定使用方式）——必须由 Maintainer 在 GitHub issue 中**点名引用**具体条款 / 法律 / 协议条文。
- 维护者个人立场 / 政治立场 / 地域偏好**绝不**构成"硬理由"。
- v1 当前没有触发永久黑名单的合规事件——所以 `PROVIDER_BLACKLIST` dict 为空。
- 未满足 §3.0 表"必须"维度但确实存在技术障碍的 provider → 进 §14.7（**当前空**）；除 §3.0 / §3.3 / §13.4 / §14.7 列举的两个治理工具外，**绝不**新增任何形式的"拒绝清单"。

---

## 14. 未来扩展性

### 14.1 新增 provider 的流程

**前置条件**：必须是白名单成员（§3.1）—— 不为白名单外 provider 写代码。

| 步骤 | 工作量（ReusableProvider） | 工作量（CustomProvider 自研） | 涉及文件 |
|---|---|---|---|
| 1. 添加 provider 解析类 | 1–4 小时 | 2–7 人日 | `donkey/core/llm/providers/<id>.py` |
| 2. 添加 schema（Pydantic Model） | 1–2 小时 | 1–2 天 | `donkey/core/llm/schema/<id>.py` |
| 3. 添加 TOML 模板节到 `donkey init` 生成器 | 30 分钟 | 30 分钟 | `donkey/core/workspace/templates/provider.toml.txt` |
| 4. 添加 provider 列表到 `donkey init` UI 提示 | 30 分钟 | 30 分钟 | README / Web UI |
| 5. 添加 F002 load 校验规则 | 30 分钟 | 30 分钟 | `donkey/core/llm/schema/loader.py` |
| 6. 添加 provider profile 元数据（可选） | 1 小时 | 1 小时 | `donkey/core/llm/protocol_defaults.py` |
| 7. 添加单元测试 + verify 脚本 | 2–4 小时 | 3–5 天 | `tests/unit/test_<id>.py` + `tests/integration/test_init_to_load.py` |
| 8. 更新 §3.1 白名单 + §8 全局模板 | 30 分钟 | 30 分钟 | `harness/report/大模型toml参数设计.md` |

**总工作量估算（v1 仅 ReusableProvider）**：
- **ReusableProvider（复用 LangChain 类）**：1–2 人日（典型 OpenAI 兼容 provider）
- **新独立 LangChain 类（bedrock / groq / fireworks / together / cohere / perplexity / databricks / cerebras / openrouter / deepseek / qwq / moonshot / qwen-general-thinking）**：1–2 人日（含包依赖测试）
- **v1 零自研**——所有 26 个 v1 provider 复用 LangChain 官方类
- **v2+ 自研候选（baidu / iflytek / sensetime）**：见 §14.6

### 14.2 升级白名单

白名单升级（新增第 20 家 provider）需走以下流程：

1. **Maintainer 决策**——确定要新增的 provider；
2. **编写本报告 §3.1 增补**——记录新增 provider 的 provider_id / LangChain 类 / 路线 / 主力模型 / 备注；
3. **编写解析类**（如 §14.1）；
4. **F002 load 校验**——确保新 provider 字段在白名单校验时通过；
5. **release 公告**——README + GitHub Release 更新。

### 14.3 永久黑名单扩容

永久黑名单扩容（新增黑名单成员）必须严格按 §13.4 流程走：

1. **GitHub issue 公开硬理由**——引用具体合规 / 法律 / 商业条款，**不得**使用主观理由（详见 §3.0 / §13.4）；
2. **更新 §3.3 + §13.4**——记录 `provider_id` + 硬理由 + 决策日期 + GitHub issue 链接；
3. **解析层加载黑名单**——`donkey/core/llm/providers/_v1_scope.py` 的 `PROVIDER_BLACKLIST` dict 添加条目；
4. **F002 load 校验**——黑名单守卫生效（与 §14.7 配合：黑名单 → 暂不支持清单 → v2+ 候选 → 白名单）；
5. **README 同步更新**。

### 14.4 多 LLM 路由（v2+）

未来 donkey 可能支持"同一 workspace 多 LLM"（如 coding agent 用 Claude 主模型 + GPT-4o-mini 做"工具选择小模型"）：

```toml
# v2+ 候选
default_provider = "anthropic"
default_model = "claude-sonnet-4-6"

# 角色：tool selector（v2+ 多 LLM 路由）
[routing.tool_selector]
provider = "openai"
model = "gpt-4o-mini"
temperature = 0.0
```

**v1 不实现**——每个 `[provider].models` 列表内可注册多个 model，但一次请求只用一个 model。

### 14.5 fallback 模型（v2+）

```toml
# v2+ 候选
[fallback]
provider = "openai"
model = "gpt-4o"
```

**v1 不实现**——donkey `init_chat_model` 单实例化，不做 fallback 链。LangChain `ModelFallbackMiddleware` 在 v2 引入后由 donkey F004-P6 中间件层落地。

### 14.6 v2+ 候选 provider 自研路线图（baidu / iflytek / sensetime）

> **v2+ 启动条件**（任一满足即启动）：
> 1. 社区累计 5+ issue 申请特定 provider 支持；
> 2. Maintainer 收到企业 B 端客户明确需求；
> 3. LangChain 官方仍未提供包装类（v2+ 自研的触发条件）。
>
> **v2+ 工作量总估算**：7–14 人日（不含端到端集成测试）。
>
> | provider | 协议挑战 | 工作量 | 关键依赖 |
> |---|---|---|---|
> | baidu（百度文心 ERNIE） | OAuth 2.0 client_credentials + access_token 缓存 + ERNIE 私有 SSE + 多 endpoint 路由（chat / embedding / image） | 2-3 人日 | bce-python-sdk（百度官方） |
> | iflytek（科大讯飞星火） | WebSocket 长连接 + HMAC-SHA256 签名（RFC 2898 PBKDF2） + 心跳保活 + 文本/音频双模态 | 5-7 人日 | websocket-client + 讯飞官方 SDK |
> | sensetime（商汤 SenseNova） | 私有协议 + 私有化交付，无公开 SDK 文档 | **未调研，无法估算**；启动前必须先商务洽谈拿文档 | — |

**v2+ 启动流程**：
1. Maintainer 启动 §14.2 流程，将 provider 从 v2+ 候选清单移入 §3.1 白名单；
2. 创建 `donkey/core/llm/providers/custom/` 目录；
3. 实现 `CustomProvider` 抽象基类（继承 `ReusableProvider`，新增 5 个抽象方法）；
4. 实现 3 个自研 provider；
5. 添加 TOML 模板节、F002 load 校验、单元测试；
6. 更新 §3.1 / §8 / §15 / §16。

### 14.7 暂不支持清单治理（当前空集合）

> 本节按 §3.0 治理原则约束 3 收窄范围——"暂不支持清单"**仅**用于"LangChain 已支持但本项目尚未投入维护工作量"或"v2+ 自研候选暂未实现"两种**技术**情形，**不得**列入"未调研 / 优先级靠后 / 任何形式的拒绝"等非技术依据。v2+ 自研候选（§3.5 baidu / iflytek / sensetime）**不**进 `PROVIDER_DEFERRED`——它们已经走 `PROVIDER_V2_DEFERRED`，是 §3.1 的延伸，不属于"暂不支持清单"治理范围。本节作为治理工具保留，**当前空集合**。

**与 §14.3 永久黑名单的对比**：

| 维度 | §14.3 永久黑名单 | §14.7 暂不支持清单 |
|---|---|---|
| **触发场景** | 合规 / 法律 / 商业禁止（**必须** GitHub issue 公开硬理由） | LangChain 官方支持但本项目尚未投入维护工作量 |
| **v1 行为** | 拒绝支持；F002 load 报 `BlacklistedProviderError` | F002 load 报 `ProviderTomlScopeError`（v1 报错后引导用户改用 [openai_compatible] 或提 issue 申请 §3.1 升级） |
| **升级路径** | 须 Maintainer 重新走 GitHub issue + 撤销决议 | 仅需 Maintainer 评估工作量 + 写解析代码 + 改文档，**无须**社区评审 |
| **当前成员** | （v1 空集合） | （v1 空集合） |

> **§3.0 约束 3 复述**：不得用于"任何形式的拒绝"——若某 provider 满足 §3.0 表"必须"维度，**必须**进入白名单或 §3.5 v2+ 候选，不得留在暂不支持清单。

**升级流程**（v2+ 把 `PROVIDER_DEFERRED` 中某成员移入白名单）：

1. Maintainer 触发评估（社区累计 5+ issue / 企业客户明确需求 / 协议公开 SDK 已成熟）；
2. **调研阶段**：评估 LangChain 官方支持现状、协议兼容性、维护工作量；若评估结果失败（合规 / 法律 / 商业禁止），**永久黑名单流程**接管（迁入 §14.3 `PROVIDER_BLACKLIST`，按 §3.0 硬理由要求走 GitHub issue）；
3. **schema 阶段**：在 `donkey/core/llm/providers/` 注册解析类（参考 §3.1 ReusableProvider 模板）；
4. **§3.1 表格更新**：删除本节对应 `provider_id` 行，把 provider_id 移入 §3.1 主表格 + 按需在 §8 增加 TOML 模板节；
5. **F002 load 校验更新**：从 `PROVIDER_DEFERRED` 删除该 provider，使 F002 load 直接通过白名单校验；
6. **测试 + 文档更新**。

**v1 行为（实现细节）**：

```python
# donkey/core/llm/providers/_v1_scope.py（v1 范围内两个 dict 当前均空）
PROVIDER_BLACKLIST: dict[str, dict[str, str]] = {
    # v1 当前无永久黑名单成员（详见 §13.4：硬理由流程）
}

PROVIDER_DEFERRED: dict[str, dict[str, str]] = {
    # v1 当前无暂不支持清单成员（详见 §14.7：仅"LangChain 支持但未投入维护"技术场景）
}

PROVIDER_V2_DEFERRED = {"baidu", "iflytek", "sensetime"}  # §3.5 v2+ 自研候选，独立于本节

def check_v1_scope(provider_id: str) -> None:
    """v1 阶段 provider 范围校验（按调用顺序：黑名单 → 暂不支持清单 → v2+ 候选 → 白名单）。"""
    if provider_id in PROVIDER_BLACKLIST:
        raise BlacklistedProviderError(...)
    if provider_id in PROVIDER_DEFERRED:
        raise ProviderTomlScopeError(...)  # 引导用户改用 openai_compatible 或提 issue
    if provider_id in PROVIDER_V2_DEFERRED:
        raise ProviderTomlScopeError(...)  # 推迟 v2+ 自研
    # 通过后留给白名单校验（_BUILTIN_PROVIDERS + facade 转发）
```

---

## 15. Provider 解析代码结构

> v1 **零自研**——所有 26 个 v1 provider 复用 LangChain 官方类，仅用 `ReusableProvider` 一个抽象基类。`CustomProvider` 抽象推迟到 v2+（§14.6 路线图）。

### 15.1 ReusableProvider 抽象基类（v1 唯一抽象；26 个复用 LangChain 的 provider）

```python
# donkey/core/llm/providers/base.py
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage


class ReusableProvider(ABC):
    """复用 LangChain ChatModel 的 provider 抽象基类。

    适用于 openai / anthropic / google / ollama / xai / mistral / bedrock /
    groq / fireworks / together / cohere / perplexity / databricks / cerebras
    / deepseek / qwen / kimi / openrouter / doubao / zhipu / MiniMax /
    tencent / stepfun / xiaomi / meta / openai-compatible 共 26 个 provider。

    这些 provider 的请求 / 响应 / 流式解析已由 LangChain 内部完成，
    donkey 只负责"构造 LangChain ChatModel 实例 + 鉴权 + api_host"。
    """

    provider_id: str               # e.g. "openai"
    default_api_host: str          # e.g. "https://api.openai.com/v1"

    @abstractmethod
    def build_chat_model(self, model: str, **params) -> BaseChatModel:
        """构造 LangChain ChatModel 实例。

        子类直接调用对应 LangChain 类（ChatOpenAI / ChatAnthropic / ChatDeepSeek
        等），不需要实现 build_request_body / parse_response 等方法
        ——LangChain 已做严格解析。
        """
```

### 15.2 ReusableProvider 示例（以 OpenAI / qwen / deepseek 为例）

```python
# donkey/core/llm/providers/reusable/openai.py
from langchain_openai import ChatOpenAI
from donkey.core.llm.providers.base import ReusableProvider


class OpenAIProvider(ReusableProvider):
    provider_id = "openai"
    default_api_host = "https://api.openai.com/v1"

    def build_chat_model(self, model: str, **params) -> ChatOpenAI:
        return ChatOpenAI(
            model=model,
            api_key=params["api_key"],
            base_url=params.get("api_host") or self.default_api_host,
            temperature=params.get("temperature"),
            max_tokens=params.get("max_tokens"),
            timeout=params.get("timeout", 60),
            max_retries=params.get("max_retries", 6),
            # ChatOpenAI 自动处理 o-series max_tokens → max_completion_tokens 转换
        )
```

```python
# donkey/core/llm/providers/reusable/qwen.py
from langchain_openai import ChatOpenAI
from donkey.core.llm.providers.base import ReusableProvider


class QwenProvider(ReusableProvider):
    """通义千问：默认走 ChatOpenAI + base_url。"""

    provider_id = "qwen"
    default_api_host = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def build_chat_model(self, model: str, **params) -> ChatOpenAI:
        return ChatOpenAI(
            model=model,
            api_key=params["api_key"],
            base_url=params.get("api_host") or self.default_api_host,
            temperature=params.get("temperature"),
            max_tokens=params.get("max_tokens"),
            timeout=params.get("timeout", 60),
            max_retries=params.get("max_retries", 6),
        )


class QwenThinkingProvider(ReusableProvider):
    """通义千问 QwQ 推理模型专用：走 `ChatQwQ` 保留 reasoning_content。

    ChatQwQ vs ChatQwen：

    - **`ChatQwQ`**（`langchain_qwq/chat_models.py:32`）—— "Qwen QwQ Thinking" 专用类，
      `model_name` 默认 `qwq-plus`，**总是 thinking on**（无 `enable_thinking` 字段）。
      用于 `qwq-32b-preview` / `qwq-plus` 等专做 thinking 的模型。
    - **`ChatQwen`**（`langchain_qwq/chat_models.py:694`）—— "Qwen series", 为 Qwen3 API 设计，
      有 `enable_thinking: Optional[bool]` + `thinking_budget: Optional[int]` 显式字段
      （`langchain_qwq/chat_models.py:812-841`）。
      用于 `qwen3-32b` / `qwen3-72b` / `qwen3-max` 等通用模型（用户按需开关 thinking）。

    两者都通过 `_BaseChatQwen._create_chat_result` 把 reasoning_content 保留到
    `additional_kwargs["reasoning_content"]`（`langchain_qwq/base.py:114-127`），
    因此 thinking 内容**应用层都能拿到**——区别只在配置接口与默认行为。
    """

    provider_id = "qwen"  # 同 provider_id
    default_api_host = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    preferred_for_thinking = True

    def build_chat_model(self, model: str, **params):
        from langchain_qwq import ChatQwQ

        return ChatQwQ(
            model=model,                                  # "qwq-32b-preview" / "qwq-plus"
            api_key=params["api_key"],
            # ChatQwQ 总是 thinking on，无需额外字段；用户可调 temperature / max_tokens / timeout
            temperature=params.get("temperature"),
            max_tokens=params.get("max_tokens"),
            timeout=params.get("timeout", 60),
            max_retries=params.get("max_retries", 6),
        )


class QwenGeneralThinkingProvider(ReusableProvider):
    """通义千问通用模型 + 显式 thinking：走 `ChatQwen` 并显式传 `enable_thinking=True`。

    适用场景：qwen3 系列通用模型（qwen3-max / qwen3-72b / qwen3-32b 等），
    需要在同一次部署里按需开关 thinking 时使用。
    """

    provider_id = "qwen"
    default_api_host = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def build_chat_model(self, model: str, **params):
        from langchain_qwq import ChatQwen

        return ChatQwen(
            model=model,
            api_key=params["api_key"],
            enable_thinking=params.get("enable_thinking", True),       # 显式开 thinking
            thinking_budget=params.get("thinking_budget", 10000),
            temperature=params.get("temperature"),
            max_tokens=params.get("max_tokens"),
            timeout=params.get("timeout", 60),
            max_retries=params.get("max_retries", 6),
        )


# 应用层根据 model_name 决定走哪个 provider（伪代码）：
# def select_qwen_provider(model: str):
#     """根据 model_name 后缀分派 Qwen Provider 类。
#
#     规则：
#     - 模型名包含 `qwq`、`reasoner` 或以 `-thinking` 结尾 → QwenThinkingProvider（ChatQwQ）
#     - 其它通用 Qwen 模型（qwen-max / qwen-plus / qwen3-* 等）→ QwenGeneralThinkingProvider（ChatQwen）
#     """
#     thinking_keywords = ("qwq", "reasoner")
#     if any(kw in model.lower() for kw in thinking_keywords) or model.endswith("-thinking"):
#         return QwenThinkingProvider()
#     return QwenGeneralThinkingProvider()
#
# # 调用
# provider = select_qwen_provider(model)
# chat_model = provider.build_chat_model(model, **params)
```

```python
# donkey/core/llm/providers/reusable/deepseek.py
from langchain_deepseek import ChatDeepSeek
from donkey.core.llm.providers.base import ReusableProvider


class DeepSeekProvider(ReusableProvider):
    """DeepSeek 专用：必须走 ChatDeepSeek 保留 reasoning_content。"""

    provider_id = "deepseek"
    default_api_host = "https://api.deepseek.com/v1"  # 实测 ChatDeepSeek.DEFAULT_API_BASE
    # 带 /v1，且 api_base 可覆盖（别名 base_url）

    def build_chat_model(self, model: str, **params) -> ChatDeepSeek:
        return ChatDeepSeek(
            model=model,                                    # "deepseek-chat" 或 "deepseek-reasoner"
            api_key=params["api_key"],
            temperature=params.get("temperature"),
            max_tokens=params.get("max_tokens"),
            timeout=params.get("timeout", 60),
            max_retries=params.get("max_retries", 6),
            # DeepSeek-R1 用 reasoning_effort 控制推理深度
            reasoning_effort=params.get("reasoning_effort"),
        )

# 注意：禁止走 ChatOpenAI + base_url
# ——LangChain 会在响应里删除 reasoning_content（chat_models/base.py:411），
# 应用层就拿不到 DeepSeek-R1 的思考链了。
```

```python
# donkey/core/llm/providers/reusable/MiniMax.py
from langchain_anthropic import ChatAnthropic
from donkey.core.llm.providers.base import ReusableProvider


class MiniMaxProvider(ReusableProvider):
    """MiniMax 走 ChatOpenAI + OpenAI 兼容协议（详见 §3.6）。

    用户主流用法：Coding Plan 订阅密钥 sk-cp-... + OpenAI 兼容端点
    https://api.minimaxi.com/v1。thinking 以 <think>...</think> 标签保留在
    AIMessage.content，应用层可用正则提取。
    """

    provider_id = "MiniMax"
    default_api_host = "https://api.minimaxi.com/v1"  # Coding Plan OpenAI 兼容端点

    def build_chat_model(self, model: str, **params) -> ChatOpenAI:
        return ChatOpenAI(
            model=model,                                    # "MiniMax-M3" / "MiniMax-M2.7" / "MiniMax-M2" 等
            api_key=params["api_key"],                       # sk-cp-... (Coding Plan) 或 MINIMAX_API_KEY
            base_url=params.get("api_host") or self.default_api_host,
            temperature=params.get("temperature"),
            max_tokens=params.get("max_tokens", 4096),
            timeout=params.get("timeout", 60),
            max_retries=params.get("max_retries", 6),
        )

# 关键事实：
# - ChatOpenAI 把 MiniMax OpenAI-compat 响应原样塞进 AIMessage.content；
#   thinking 在 content 里以 <think>...</think> 标签存在（实测 harness/demo/create_an_agent.py）。
# - ChatOpenAI 不会解析 <think> 标签，所以 MiniMax-M3 的思考链对应用层**可见**（用正则提取）。
# - 注意：ChatOpenAI 会丢弃 reasoning_content 字段（chat_models/base.py:411），
#   所以**默认** 不要让 MiniMax 返回 reasoning_split=true 模式；
#   Coding Plan 端点默认 reasoning_split=false，正好避免此问题。
# - v2+ 可加 Anthropic SDK 兼容端点（api_host="https://api.minimax.io/anthropic"）
#   走 ChatAnthropic，支持 thinking.type / budget_tokens / reasoning_effort 精细控制，
#   但 Coding Plan 密钥不适用此端点。
```

### 15.3 v2+ 候选：CustomProvider 抽象（v1 不实现）

> v1 **不实现** CustomProvider 抽象基类。所有 26 个 v1 provider 复用 LangChain 官方类（`ReusableProvider`）。
> v2+ 启动自研时，按以下接口添加 `CustomProvider` 抽象：

```python
# donkey/core/llm/providers/base.py（v2+ 才创建）
class CustomProvider(ReusableProvider):
    """v2+ 自研 provider 抽象基类。适用于 baidu / iflytek / sensetime 共 3 个。"""

    @abstractmethod
    def build_auth_headers(self, api_key: str) -> dict[str, str]:
        """构建鉴权 header（部分 provider 用 URL query 鉴权）"""

    @abstractmethod
    def build_request_body(self, messages, tools, model, **params) -> dict:
        """把 LangChain 统一消息翻译为 provider 专有 JSON body"""

    @abstractmethod
    def parse_response(self, response_body: dict) -> AIMessage:
        """把 provider 专有响应翻译回 LangChain AIMessage"""

    @abstractmethod
    def parse_stream_chunk(self, chunk: bytes) -> AIMessageChunk | None:
        """解析 provider 专有流式响应"""
```

详细实现示例（baidu / iflytek / sensetime）见 §14.6 启动后产出。

### 15.4 v1 范围守卫（永久黑名单 + 暂不支持清单 + v2+ 候选）

```python
# donkey/core/llm/providers/_v1_scope.py（当前两个 dict 均空）

# 永久黑名单：仅适用于合规 / 法律 / 商业禁止场景
# v1 当前空集合——没有任何 provider 因硬性理由被永久禁止
# 任何 Maintainer 入列前必须满足 §3.0 / §13.4 流程（GitHub issue 公开硬理由 + ≥14 天评审）
PROVIDER_BLACKLIST: dict[str, dict[str, str]] = {
    # 例如（暂为空）：
    # "some_forbidden_provider": {
    #     "reason": "商业 SDK 许可证不允许第三方集成",
    #     "since": "2027-01-15",
    # },
}

# 暂不支持清单：仅适用于"LangChain 官方支持但本项目尚未投入维护工作量"的技术场景
# v1 当前空集合；按 §3.0 约束 3，不得用于"任何形式的拒绝"。
PROVIDER_DEFERRED: dict[str, dict[str, str]] = {
    # 例如（暂为空）：
    # "some_supported_provider": {
    #     "reason": "LangChain 官方支持，但本项目 v1 维护工作量排在 §14.x 路线图后",
    #     "since": "2027-01-15",
    #     "review_after": "2027-07",
    # },
}

# v2+ 候选：必须有自研解析代码（独立于本节，永不进 PROVIDER_BLACKLIST / PROVIDER_DEFERRED）
PROVIDER_V2_DEFERRED = {"baidu", "iflytek", "sensetime"}

def check_v1_scope(provider_id: str) -> None:
    """v1 阶段 provider 范围校验（按调用顺序：黑名单 → 暂不支持清单 → v2+ 候选 → 白名单）。

    各层拒绝原因不同：黑名单 -> 硬性合规 / 法律 / 商业禁止；暂不支持清单 -> LangChain 支持但
    本项目未投入维护（引导用户改用 [openai_compatible] 或提 issue 申请 §3.1 升级）；v2+ 候选 -> 推迟到 v2+ 自研实现。
    """
    if provider_id in PROVIDER_BLACKLIST:
        raise BlacklistedProviderError(
            f"provider '{provider_id}' 在永久黑名单（合规 / 法律 / 商业禁止）："
            f"{PROVIDER_BLACKLIST[provider_id]['reason']}"
        )
    if provider_id in PROVIDER_DEFERRED:
        raise ProviderTomlScopeError(
            f"provider '{provider_id}' 暂不支持清单（LangChain 支持但本项目未投入维护，详见 §3.3 / §14.7）："
            f"{PROVIDER_DEFERRED[provider_id]['reason']}"
        )
    if provider_id in PROVIDER_V2_DEFERRED:
        raise ProviderTomlScopeError(
            f"provider '{provider_id}' 推迟到 v2+ 实现（详见 §3.5 / §14.6）"
        )
```

> 按 §3.0 治理原则，`PROVIDER_BLACKLIST` 与 `PROVIDER_DEFERRED` 在 v1 范围内**均空**；下次任何 Maintainer 入列前，必须分别走 §13.4 / §14.7 流程，绝不允许私设。

```python
# donkey/core/llm/providers/__init__.py
from donkey.core.llm.providers._v1_scope import check_v1_scope
from donkey.core.llm.providers.reusable import (
    OpenAIProvider, AnthropicProvider, GoogleProvider, OllamaProvider,
    XAIProvider, MistralProvider, BedrockProvider, GroqProvider,
    FireworksProvider, TogetherProvider, CohereProvider, PerplexityProvider,
    DatabricksProvider, CerebrasProvider, DeepSeekProvider,
    QwenProvider, QwenThinkingProvider, QwenGeneralThinkingProvider, MoonshotProvider, OpenRouterProvider,
    DoubaoProvider, ZhipuProvider, MiniMaxProvider, TencentProvider,
    StepFunProvider, XiaomiProvider, MetaProvider, OpenAICompatibleProvider,
)

# v1 共 26 个 provider（全部 ReusableProvider，零自研）
PROVIDER_REGISTRY = {
    # 原生闭源大厂（6）
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "xai": XAIProvider,
    "mistral": MistralProvider,
    "meta": MetaProvider,                       # 多平台路由（Ollama / OpenAI 兼容代理）
    # 国际云推理 / 平台（8）
    "bedrock": BedrockProvider,
    "groq": GroqProvider,
    "fireworks": FireworksProvider,
    "together": TogetherProvider,
    "cohere": CohereProvider,
    "perplexity": PerplexityProvider,
    "databricks": DatabricksProvider,
    "cerebras": CerebrasProvider,
    # 本地 / 元 provider（3）
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
    "openai-compatible": OpenAICompatibleProvider,
    # 推理模型专用类（4 个类，对应 3 个 provider_id；按 model_name 分派）
    "deepseek": DeepSeekProvider,               # 唯一强制专用类
    "qwen": QwenProvider,                       # 默认通用类；应用层按 model_name 分派到 QwenThinkingProvider（QwQ）或 QwenGeneralThinkingProvider（Qwen3）
    "kimi": MoonshotProvider,                   # 默认；thinking 模型走 ChatMoonshot
    # 中文 OpenAI 兼容（4）
    "doubao": DoubaoProvider,
    "zhipu": ZhipuProvider,
    "MiniMax": MiniMaxProvider,                # ChatOpenAI + base_url（OpenAI 兼容 + Coding Plan sk-cp- 密钥）
    "tencent": TencentProvider,
    "stepfun": StepFunProvider,
    "xiaomi": XiaomiProvider,                   # 多平台路由
    # ⚠️ 不注册（推迟 v2+）：baidu / iflytek / sensetime → 触发 ProviderTomlScopeError（详见 §3.5 / §14.6）
    # ⚠️ 永久黑名单：v1 空集合（详见 §13.4：必须满足 §3.0 硬理由流程才能入列）
    # ⚠️ 暂不支持清单：v1 空集合（详见 §14.7：仅"LangChain 支持但未投入维护"技术场景）
}

def get_provider(provider_id: str) -> ReusableProvider:
    check_v1_scope(provider_id)               # v1 范围校验（永久黑名单 + 暂不支持清单 + v2+ 候选）
    if provider_id not in PROVIDER_REGISTRY:  # 白名单校验
        # 统一为 ProviderTomlScopeError（exit 11 伞形，见 §7.3 / §11.1）
        raise ProviderTomlScopeError(
            f"provider '{provider_id}' 不在白名单（v1 = 26 家）"
        )
    return PROVIDER_REGISTRY[provider_id]()
```

---

## 16. 决策速查表

| # | 问题 | 结论 | 理由 |
|---|---|---|---|
| **Q-1** | TOML schema 形状 | **每个 provider 独立 schema**（无统一 `[provider]` 顶层表） | P-1；字段语义清晰；解析严谨 |
| **Q-2** | 鉴权方式 | **`api_key` 仅 TOML 明文，不读环境变量** | P-2；workspace 跨 OS 行为一致；用户自负 |
| **Q-3** | `api_host` 必填性 | **对 23 个 provider 选填；`openai-compatible` / `meta` / `databricks` 必填**（MiniMax 有合理默认 `api.minimaxi.com/v1`，但允许覆盖为 Anthropic SDK 端点）| P-3；Ollama 小白用户友好（26 − 3 = **23**）|
| **Q-4** | `api_host = "default"` | **仅 ollama 解析为官方默认 URL；其它 provider 视为普通 URL**（并出 **warning**，exit 0，见 §11.1 #18） | 字段语义统一；Ollama 友好 |
| **Q-5** | Provider 白名单 | **v1 = 26 家硬限**（OpenAI / Anthropic / Google / Meta / xAI / Mistral / Qwen / DeepSeek / Doubao / Kimi / Zhipu / MiniMax / Tencent / StepFun / Xiaomi / Bedrock / Groq / Fireworks / Together / Cohere / Perplexity / Databricks / Cerebras / OpenRouter / OpenAI-Compatible / Ollama）；**v2+ 候选 3 家**（Baidu / iFlytek / SenseTime）见 §3.5 | P-4；不为冷僻 provider 写代码 |
| **Q-6** | Provider 范围治理 | **v1 范围内无永久黑名单成员 / 无暂不支持清单成员**——按 §3.0 Provider 治理原则（最高优先级），本项目对所有 provider **一视同仁**，仅技术可行性 / 维护成本 / 生态适配度可作为入选 / 排除 / 列入黑名单的依据；Maintainer 个人立场 / 政治 / 地缘偏好**绝不**构成黑名单"硬理由"；任何入列决策必须分别走 §13.4 / §14.7 流程（GitHub issue 公开硬理由 + 社区评审 ≥14 天）。 | P-4 + §3.0 + §13.4 / §14.7 流程；详见 §3.0 |
| **Q-7** | 字段拼写错误 | **F002 load 立即报错（exit 11）** | P-5；不延迟到运行时 |
| **Q-8** | `[provider.extra]` 透传 | **不采用** | P-5；解析严谨 > 灵活 |
| **Q-9** | warning vs error | **`provider.toml` 任何"硬错" = error（伞形 `ProviderTomlLoadError` → exit 11；细分 7 个子类详见 §7.3 + §11.1）；warning 仅限字段值软越界 / B 档（`openai-compatible` / `xiaomi`）`api_key` 缺失 / `api_host=default` 非 ollama 等软问题 → exit 0；详见 §11.2 + `README §3.2.1`** | 区分"硬错"与"软问题"；与 README §3.2.1 严格 1:1 |
| **Q-9.1** | LangChain 运行时异常 → exit code | **F004 段位归属**：retryable 错误（429/5xx/网络/超时/400 请求格式错）→ exit 83 (`ModelRetryMiddlewareError`)；auth 错误（401/403/404 + **构造期 Missing credentials**）→ exit 90 (`ModelAuthenticationError`)；输入超限（`ContextOverflowError`）→ exit 85 (`ModelCallLimitMiddlewareError`)；详见 §4.3.1 + `README §3.4.1`（400 统一为 83）| 与 README §3.4.1 严格 1:1 |
| **Q-10** | 三层架构 | **网络层透传 + 解析层严谨 + 应用层抽象** | §2；与 LangChain 解耦清晰 |
| **Q-11** | Web UI | **每个 provider 一 tab + 鉴权隐藏 + api_host 默认值提示 + 测试连接** | §12；用户友好 |
| **Q-12** | 是否能用 LangChain 实现 | **v1 100% 能**：26/26 v1 provider 复用 LangChain 官方类（**14 个独立类 + 8 个 ChatOpenAI+base_url + 1 个 ChatOpenRouter + 2 个多平台路由 + 1 个 ChatDeepSeek**；另有 3 个推理模型替代类 [ChatQwQ / ChatQwen / ChatMoonshot] 不额外计 provider）；**v2+ 候选 3 家**（baidu / iflytek / sensetime）推迟自研 | §3.2 / §15 / §14.6 |
| **Q-13** | 仿效对象 | **Cherry Studio**（per-provider schema + 鉴权明文 + models 列表） | §1.4 |
| **Q-14** | 未来扩展 | **新增 provider 1–2 人日；新增白名单成员走 §14.2 流程；新增黑名单成员走 §14.3 流程** | §14 |

---

## 17. 一句话总结

> **仿效 Cherry Studio 的 per-provider schema + 明文鉴权，每个 provider 一个独立 TOML schema；`api_key` 仅 TOML 明文（不读环境变量，保证 workspace 跨 OS 行为一致）；`api_host` 23 个 provider 选填（Ollama 允许 `"default"` 特殊值；`openai-compatible` / `meta` / `databricks` 必填）；v1 provider 白名单硬限 26 家 + §3.0 Provider 治理原则（最高优先级，对所有 provider 一视同仁，仅技术维度可作为入选 / 排除依据；v1 范围内永久黑名单与暂不支持清单**均为空**）+ baidu / iflytek / sensetime 推迟到 v2+；v1 100% 复用 LangChain 官方类（14 个独立类 + 8 个 ChatOpenAI+base_url 薄包装含 MiniMax-Coding-Plan + 1 个 ChatOpenRouter 元 provider + 2 个多平台路由 + 1 个 ChatDeepSeek = 26；另有 3 个推理模型替代类 [ChatQwQ / ChatQwen / ChatMoonshot] 不额外计 provider），零自研解析；含推理模型的 provider 走专用 LangChain 类（DeepSeek / ChatQwQ-for-QwQ / ChatQwen-for-Qwen3 + 显式 enable_thinking / Moonshot / OpenRouter）保留 reasoning_content；MiniMax-M3 走 `ChatOpenAI + base_url`（Coding Plan 主流用法），`<think>` 标签在 `content` 内保留；[bedrock] 改用独立 `aws_access_key_id` / `aws_secret_access_key` / `aws_region` 字段 + `boto3.Session(...)` 显式构造（与 §9.1 不读 env var 立场完全对齐）；TOML loader 把 `api_key` 缺失映射为 `""`（绝不返回 `None`），否则 LangChain 内部 env var 回退会"背叛立场"；exit 11 由伞形 `ProviderTomlLoadError` 承载（覆盖 7 种子错如 ProviderTomlSyntaxError / ProviderTomlFieldError / ProviderTomlScopeError 等，统一映射同一 exit 11，子类在 traceback 中可区分）；LangChain 运行时异常按"修复动作合并"原则 → retryable 错误（429/5xx/网络/超时/**400**）exit 83 (`ModelRetryMiddlewareError`) / auth 错误（401/403/404/**构造期 Missing credentials**）exit 90 (`ModelAuthenticationError`) / 输入超限（`ContextOverflowError`）exit 85 (`ModelCallLimitMiddlewareError`)**。网络层透传、应用层抽象 LangChain ——"传输的时候要透传，解析的时候要严谨"。**
>
> **实测验证结论**：上述主张已由端到端 demo `harness/demo/about_providers/provider.py`（MiniMax-M3 + deepseek-v4-flash，63 项断言全绿）逐条验证——**核心主张全部成立**（per-provider schema / 严格 load 校验 / `<think>` 保留 / `ChatDeepSeek` 保留 `reasoning_content` 而 `ChatOpenAI` 丢弃 / exit code 映射）。
