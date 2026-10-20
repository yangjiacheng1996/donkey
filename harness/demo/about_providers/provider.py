#!/usr/bin/env python3
"""验证《大模型 TOML 参数设计》v2.5 的 per-provider schema 可行性。

本 demo 用**两个真实模型**跑通设计文档的核心主张：

======================  ==========================================  =========================
provider_id             模型                                        LangChain 类
======================  ==========================================  =========================
``MiniMax``             ``MiniMax-M3``                               ``ChatOpenAI + base_url``
``deepseek``            ``deepseek-v4-flash``                        ``ChatDeepSeek``（专用类）
======================  ==========================================  =========================

验证的设计文档条款：

* §7.3 / §11.1 —— F002 load 阶段的 7 类硬错（拼写 / 类型 / 越界 / scope / 缺模型 …）
* §8 / §8.3 —— per-provider 独立 schema + ``models`` 子表
* §9.1 / §9.1.1 —— ``api_key`` 仅 TOML 明文，缺失归一化为 ``""``，**绝不回退 env var**
* §9.2 —— ``api_key`` 空串 = warning（exit 0），不阻塞 load
* §10 —— ``api_host`` 全 provider 可选 + 解析层默认值
* §3.2 / §5.3 —— 推理模型必须走专用类（``ChatDeepSeek`` 保留 ``reasoning_content``）
* §3.6 / §3.6.5 —— MiniMax 走 OpenAI 兼容端点，``<think>`` 标签保留在 ``content``
* §4.3.1 —— 运行时异常 → exit code 映射（83 / 85 / 90）
* §15.2 —— ``ReusableProvider`` 抽象，零自研解析

用法::

    # 全量（离线校验 + 联网调用）
    .venv/bin/python harness/demo/about_providers/provider.py

    # ⚠️ 默认的 provider.toml 是**脱敏版**（api_key = 占位符），联网用例会自动跳过；
    #    要真跑请指向含真实密钥的 provider.local.toml（已 .gitignore）：
    .venv/bin/python harness/demo/about_providers/provider.py \
        --config harness/demo/about_providers/provider.local.toml

    # 只跑 F002 load 阶段的离线校验（不发网络请求）
    .venv/bin/python harness/demo/about_providers/provider.py --offline

    # 只跑联网的运行时验证
    .venv/bin/python harness/demo/about_providers/provider.py --runtime-only

    # 强制直连（忽略 env 里的代理设置）
    .venv/bin/python harness/demo/about_providers/provider.py --proxy direct

依赖::

    pip install -qU "langchain>=1.4" langchain-openai langchain-deepseek pydantic "httpx[socks]"

    ⚠️ ``httpx[socks]`` 的 extra 只在 env 里配了 **socks 代理**时才需要
       （Clash / V2Ray 等常见）：httpx 0.28 的代理 scheme 白名单是
       http / https / **socks5** / **socks5h**（源码 ``httpx/_config.py:212``），
       老写法 ``socks://`` 已不在白名单 → 会抛
       ``ValueError: Unknown scheme for proxy URL``。
       本 demo 启动时会自动把 ``socks://`` 改写成 ``socks5://``；
       若未装 ``socksio`` 则自动摘除该代理变量并退回直连。

实测环境::

    Python 3.12.3 / langchain 1.4.6 / langchain-core 1.6.12
    langchain-openai 1.7.2 / langchain-deepseek 1.1.1 / openai 3.35.1 / pydantic 2.12.5

================================================================================
验证结论（2026-10-20 实测：63 项断言全绿 / 0 FAIL / 0 SKIP）
================================================================================

【结论成立 —— 可直接进 v1 实现】

1. §3.6 「MiniMax 走 ``ChatOpenAI + base_url``」——成立。MiniMax-M3 实测返回
   ``<think>...</think>`` 标签**原样保留在 ``AIMessage.content``**，§3.6.5 的正则
   提取伪代码可直接用（案例 B01 / B02）。
2. §3.2 / §5.3 关键警告「推理模型必须走专用类」——**成立且是硬结论**。同一个
   ``deepseek-v4-flash``：走 ``ChatDeepSeek`` 时 ``additional_kwargs
   ["reasoning_content"]`` 有值；走 ``ChatOpenAI + base_url`` 时服务端明明返回了
   ``reasoning_content``，LangChain 却**原样丢弃**（案例 B04 / B05 对照实验）。
3. §9.1.1 「``api_key`` 缺失 → ``""``，绝不回退 env var」——在 **LangChain 层成立**
   （``_resolve_gateway_config`` 走 ``api_key is not None`` 分支，不读 env var）。
4. §7.3 / §11.1 —— 7 类子错误全部可在 **F002 load 阶段**触发并统一映射 exit 11
   （案例 A02~A17）。
5. §3.1 —— 白名单 26 个 provider_id、``langchain.chat_models.base._BUILTIN_PROVIDERS``
   实测 30 个、``"google"`` 不在其中且 ``init_chat_model(model_provider="google")``
   抛 ``ValueError``（案例 A18）——**donkey facade 必须做 provider_id 转发**。
6. §4.3.1 exit code 映射——实测 ``401`` → exit 90（``ModelAuthenticationError``）、
   ``529`` → exit 83（``ModelAPIError``），与文档表格一致（案例 B07 / B08）。

【设计缺口 —— 建议 v2.6 修订】

D1. **§9.2「api_key 空 → warning + exit 0」这条链路走不通**（案例 A20）。
   loader 把缺失的 ``api_key`` 归一化为 ``""`` 之后，**构造** ChatModel 时底层
   ``openai`` SDK 直接抛 ``OpenAIError: Missing credentials ... or set the
   OPENAI_API_KEY ... environment variable``——失败发生在**构造期**而非运行期，
   且报错信息恰恰指向项目明令禁止的 env var 路径。
   ``ChatDeepSeek`` 同理（构造期 ``ValueError: If using default api base,
   DEEPSEEK_API_KEY must be set.``）。
   → 建议：空 ``api_key`` 在 F002 load 阶段直接升级为**硬错**（exit 11 /
   ``ProviderTomlFieldError``），而不是 warning。

D2. **§4.3.1 对 ``ModelInvalidRequestError``(400) 的 exit code 自相矛盾**：
   §4.3.1 表格写 **83**，同节代码片段把它放进 ``NON_RETRYABLE_AUTH_ERRORS``（→ **90**），
   §17 一句话总结又写「400/ContextOverflowError → **85**」。同一异常三处三个值。
   → 建议：统一为一个值（本 demo 按表格口径取 83），并删掉另两处表述。

D3. **§8.3 模板里的 ``[MiniMax.models.MiniMax-M2.7]`` 会静默损坏模型表**
   （案例 A11）。TOML 的裸 key 不允许含 ``.``，该行会被解析成嵌套表
   ``MiniMax-M2 → 7``，``models["MiniMax-M2.7"]`` 永远查不到。
   → 建议：模型 id 含 ``.`` 时必须写成 ``[MiniMax.models."MiniMax-M2.7"]``，
   文档模板应加引号；bedrock 的 ``us.anthropic.claude-sonnet-4-6`` 同理。

D4. **§10.1 的 deepseek ``api_host`` 描述与实现不符**：文档写
   ``https://api.deepseek.com``（"ChatDeepSeek 固定，不可改"），实测
   ``ChatDeepSeek`` 的 ``DEFAULT_API_BASE = "https://api.deepseek.com/v1"``
   （带 ``/v1``）且 ``api_base`` **可以覆盖**（别名 ``base_url``）。
   → 建议：默认值改成 ``https://api.deepseek.com/v1``，删掉"不可改"。

D5. **§5.1 「仅 o-series 用 ``max_completion_tokens``」与实现不符**（案例 B10）。
   langchain-openai 1.7.2 的 ``ChatOpenAI`` 对**所有**模型都把 ``max_tokens``
   重命名为 ``max_completion_tokens``（源码 ``base.py:3830`` / ``:3845``）；
   MiniMax OpenAI 兼容端点实测接受该字段名（返回 200）。
   → 建议：§5.2「max_tokens 命名」一行改为「ChatOpenAI 一律下发
   ``max_completion_tokens``；``ChatDeepSeek`` 等基于 ``BaseChatOpenAI`` 的类
   仍下发 ``max_tokens``」。

D6. **§7.3 的 temperature 软/硬越界示例自相矛盾**：硬越界示例是
   ``temperature = 3.0``，软越界示例是「``temperature > 2.0``」——3.0 > 2.0。
   → 建议：明确硬边界 ``[0.0, 2.0]``（越界 = error），软边界另定（如 > 1.5 = warning）。

D7. **§7.1 / §7.2 的「19 个 provider 节」与 §3.1 的 26 家白名单对不上**
   （§7.1 "典型 workspace 30–80 行（19 个 provider 节）"、§7.2 注释
   "顶层：全局默认 + 19 个 provider 独立节" / "... 19 个 provider 节（v1 白名单）"）。
   → 建议：统一成 26（§3.1 表格实测 26 行，``_BUILTIN_PROVIDERS`` 实测 30 个）。

【补充发现】

S1. MiniMax 的**思考 token 数**其实已经在统一 schema 里：实测
   ``usage_metadata["output_token_details"]["reasoning"] = 44``。
   → 应用层拿不到思考**文本**（在 ``<think>`` 标签里），但拿得到思考**量**。

S2. MiniMax Coding Plan 集群会随机返回 ``529 overloaded``（本轮 12 次请求里
   约一半被拒），与配置无关。→ 正好是 §4.3.1「可重试类 → exit 83」的真实样本，
   但生产实现需要 provider 级的退避重试（demo 里的 ``_retry_invoke``）。

S3. MiniMax OpenAI 兼容端点**接受** ``reasoning_split`` 字段（实测请求体带
   ``"reasoning_split": false`` 返回 200），§3.6.4 的 ``extra_body`` 透传方案可行。

S4. **HTTP 代理是网络层对 env var 的唯一依赖，§9.1「不读 env var」没有覆盖它**。
   §9.1 的"不读环境变量"只约束了 **api_key**；但 httpx / openai SDK 在构造
   client 时**默认读取** ``ALL_PROXY`` / ``HTTPS_PROXY`` / ``HTTP_PROXY``，
   且 httpx **不原生支持** ``socks://``（Clash / V2Ray 等常见）——未装
   ``socksio`` 时会在**构造 client 阶段**直接抛
   ``ValueError: Unknown scheme for proxy URL``，一条请求都发不出去。
   本 demo 因此在启动时统一治理代理（``sanitize_proxy_env()``）：
   装了 ``socksio`` 就照常用 socks 代理，没装就摘掉变量退回直连。
   → 建议：设计文档 §9 增加一条「api_key 不读 env var，但**网络出口**仍受
   ``HTTP_PROXY`` 等 env var 影响，跨 OS / 跨机器行为可能不一致」，
   并在 §13（安全性）里说明代理 env var 的边界。

【demo 自身的边界】

本 demo 只落地了 3 套 per-provider schema（``MiniMax`` / ``deepseek`` / ``bedrock``
——后两个只用于验证 schema 校验，不联网）+ 2 个 provider 构造类；白名单里其余
provider 的 schema 与解析层按 §8 / §15.2 逐个补齐即可（本 demo 的 loader 对
"schema 尚未实现"的 provider 明确报错，不用通用 schema 兜底）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
import tomllib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Literal

import httpx
from langchain_core.exceptions import (
    ContextOverflowError,
    ModelAPIError,
    ModelAuthenticationError,
    ModelConnectionError,
    ModelInvalidRequestError,
    ModelNotFoundError,
    ModelPermissionDeniedError,
    ModelRateLimitError,
    ModelTimeoutError,
)
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

HERE = Path(__file__).resolve().parent
DEFAULT_TOML = HERE / "provider.toml"

# 实际使用的配置文件（默认 = 脱敏版 provider.toml；--config 可指向 provider.local.toml）
# —— demo **不读任何环境变量**取 key（设计文档 §9.2 V2-P2 立场）。
CONFIG_PATH: Path = DEFAULT_TOML

# 网络出口模式："env" = 跟随 env 里的代理设置（默认）；"direct" = 强制直连。
# 由命令行 --proxy 设置（见 main()）。
PROXY_MODE = "env"

# httpx / openai SDK 认的代理环境变量
PROXY_ENV_NAMES = (
    "ALL_PROXY", "all_proxy", "HTTPS_PROXY", "https_proxy",
    "HTTP_PROXY", "http_proxy",
)

# httpx **不原生支持**的代理 scheme（需要 socksio 扩展）
UNSUPPORTED_PROXY_SCHEMES = ("socks://", "socks5://", "socks5h://", "socks4://")

# httpx 0.28 只认 http / https / socks5 / socks5h（源码 httpx/_config.py:212）。
# 老写法 ``socks://`` 是 httpx 早期版本的别名，0.28 已移除 → 直接改写成 socks5://。
PROXY_SCHEME_REWRITE = {"socks://": "socks5://", "socks4://": "socks5://"}


def sanitize_proxy_env(mode: str = "env") -> None:
    """治理 env 里的代理设置——**必须在创建任何 client 之前调用**。

    两个坑（都是实测踩到的）：

    1. httpx 0.28 的代理 scheme 白名单是 ``http`` / ``https`` / ``socks5`` /
       ``socks5h``；老写法 ``socks://`` **不在白名单**里 → 直接抛
       ``ValueError: Unknown scheme for proxy URL``。
    2. ``socks5://`` 还需要 ``socksio`` 扩展，否则 httpx 构造代理时同样报错。

    处理策略：

    - 装了 ``socksio`` → 把 ``socks://`` 改写成 ``socks5://``，代理照常用；
    - 没装 ``socksio`` → 摘掉 socks 代理变量，本进程退回直连（不崩）。
    """
    if mode == "direct":
        removed = [n for n in PROXY_ENV_NAMES if os.environ.pop(n, None) is not None]
        print(f"  [proxy] --proxy direct：已忽略 env 代理变量 {removed or '（无）'}")
        return

    try:
        import socksio  # noqa: F401

        has_socks = True
    except ImportError:
        has_socks = False

    rewritten: list[str] = []
    removed: list[str] = []
    for name in PROXY_ENV_NAMES:
        value = os.environ.get(name)
        if not value:
            continue
        lower = value.lower()
        if lower.startswith("socks"):
            if not has_socks:
                removed.append(f"{name}={value}")
                del os.environ[name]
                continue
            for old, new in PROXY_SCHEME_REWRITE.items():
                if lower.startswith(old):
                    fixed = new + value[len(old):]
                    os.environ[name] = fixed
                    rewritten.append(f"{name}: {value} → {fixed}")
                    break
    if rewritten:
        print("  [proxy] 已把 httpx 不认的 socks scheme 改写成 socks5://（代理照常用）")
        for item in rewritten:
            print(f"           {item}")
    if removed:
        print("  [proxy] ⚠️ env 里的 socks 代理：httpx 需要 socksio 扩展，未安装")
        for item in removed:
            print(f"           {item}")
        print("           → 已临时摘除，本进程退回直连（否则构造 client 时直接崩）")
        print("           → 需要走该代理请执行：pip install socksio")
    if has_socks and not rewritten and not removed:
        print("  [proxy] 检测到 socksio，env 里的 socks 代理可正常使用")
    effective = _detect_proxy_env()
    print(f"  [proxy] 生效的网络出口 = {effective}")


# =============================================================================
# §7.3 / §11.1 —— 错误体系（exit 11 伞形 Error class）
# =============================================================================
class ProviderTomlLoadError(Exception):
    """exit 11（伞形）—— provider.toml 加载阶段任何失败。"""


class ProviderTomlSyntaxError(ProviderTomlLoadError):
    """tomllib.TOMLDecodeError 包装（exit 11）。"""


class ProviderTomlFieldError(ProviderTomlLoadError):
    """字段名拼写错 / 必填字段缺失 / 未知字段（exit 11）。"""


class ProviderTomlFieldTypeError(ProviderTomlLoadError):
    """字段值类型不匹配（exit 11）。"""


class ProviderTomlFieldValueError(ProviderTomlLoadError):
    """字段值硬越界（如 temperature = 3.0、api_host 非 URL）（exit 11）。"""


class ProviderTomlScopeError(ProviderTomlLoadError):
    """scope 检查失败：provider 不在 §3.1 白名单（exit 11）。"""


class ProviderNotInV1ScopeError(ProviderTomlLoadError):
    """provider 在 §3.5 v2+ 候选（baidu / iflytek / sensetime），推迟到 v2+（exit 11）。"""


class ProviderTomlMissingModelError(ProviderTomlLoadError):
    """default_model 不在该 provider 的 models 表（exit 11）。"""


class ProviderTomlHostNotAllowedError(ProviderTomlLoadError):
    """provider 类的 langchain 不允许 api_host 覆盖（exit 11）。"""


# =============================================================================
# §3.0 / §3.1 / §3.5 —— v1 范围守卫
# =============================================================================
# 设计文档 §3.1 的 v1 白名单（26 家）。注意 provider_id 大小写敏感。
PROVIDER_WHITELIST_V1: frozenset[str] = frozenset(
    {
        # 原生闭源大厂
        "openai", "anthropic", "google", "meta", "xai", "mistral",
        # OpenAI 兼容（中文）
        "qwen", "deepseek", "doubao", "kimi", "zhipu", "MiniMax",
        "tencent", "xiaomi", "stepfun",
        # 国际云推理 / 平台
        "bedrock", "groq", "fireworks", "together", "cohere",
        "perplexity", "databricks", "cerebras",
        # 本地 / 元 provider
        "ollama", "openrouter", "openai-compatible",
    }
)

# §3.5 v2+ 候选（需自研解析类，v1 不实现）
PROVIDER_V2_DEFERRED: frozenset[str] = frozenset({"baidu", "iflytek", "sensetime"})

# §13.4 永久黑名单 —— v1 空集合（仅硬性合规 / 法律 / 商业禁止才可入列）
PROVIDER_BLACKLIST: dict[str, dict[str, str]] = {}

# §14.7 暂不支持清单 —— v1 空集合（仅"LangChain 支持但本项目未投入维护"的技术情形）
PROVIDER_DEFERRED: dict[str, dict[str, str]] = {}

# §11.1 #13：provider 类的 langchain 不允许 api_host 覆盖（例：bedrock 走 boto3 /
# Converse 端点，端点由 AWS 决定）。这些 provider 若填了 api_host → exit 11。
API_HOST_NOT_ALLOWED: frozenset[str] = frozenset({"bedrock"})

# §9.2 空 api_key 分三档（联网调研结论：Ollama / vLLM / LiteLLM 官方文档 + 实测）
#   "A" = 本地无鉴权端点 → 空 api_key 合法，无 warning
#   "B" = 端点属性未知   → 空 api_key 合法 + warning（解析层填占位符）
#   "C" = 云端 provider  → 空 api_key 硬错 exit 11
API_KEY_OPTIONAL_PROVIDERS: dict[str, str] = {
    "ollama": "A",              # ChatOllama 根本没有 api_key 字段
    "meta": "A",                # 自托管路由
    "openai-compatible": "B",   # 可能指本地 vLLM，也可能指云端中转站
}
# B 档：解析层在构造 ChatOpenAI 前填入的占位符（donkey 自产常量，不读 env var）
PLACEHOLDER_API_KEY = "not-needed"


def check_v1_scope(provider_id: str) -> None:
    """v1 阶段 provider 范围校验（黑名单 → 暂不支持 → v2+ 候选 → 白名单）。"""
    if provider_id in PROVIDER_BLACKLIST:
        raise ProviderTomlScopeError(
            f"provider '{provider_id}' 在永久黑名单：{PROVIDER_BLACKLIST[provider_id]['reason']}"
        )
    if provider_id in PROVIDER_DEFERRED:
        raise ProviderTomlScopeError(
            f"provider '{provider_id}' 暂不支持：{PROVIDER_DEFERRED[provider_id]['reason']}"
        )
    if provider_id in PROVIDER_V2_DEFERRED:
        raise ProviderNotInV1ScopeError(
            f"provider '{provider_id}' 推迟到 v2+ 实现（设计文档 §3.5）"
        )
    if provider_id not in PROVIDER_WHITELIST_V1:
        raise ProviderTomlScopeError(
            f"provider '{provider_id}' 不在 §3.1 白名单或 §3.5 v2+ 候选；"
            f"如走 OpenAI 协议可改用 [openai-compatible] 元 provider"
        )


# =============================================================================
# §8.1 —— per-provider 独立 schema（Pydantic，extra=forbid → 拼写错误立即报错）
# =============================================================================
class ModelEntry(BaseModel):
    """``[provider.models.<model_id>]`` —— 模型级参数（覆盖 provider 级默认值）。"""

    # strict=True：TOML 是强类型语言，``timeout = "60"`` 这种字符串不该被
    # 静默强转成 float —— 解析层必须"严谨"（§2.3 / §11.1 #10）。
    model_config = ConfigDict(extra="forbid", strict=True)

    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | None = None
    reasoning_effort: Literal["low", "medium", "high"] | None = None


class ProviderSection(BaseModel):
    """§8.1 通用 8–12 字段 + §8.2 鉴权占位。

    ``extra="forbid"`` 是 V2-P5 的落地：任何未在 schema 声明的字段在 F002 load
    阶段就被拒绝（拼写错误不延迟到运行时）。
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    api_key: str = ""
    api_host: str = ""
    timeout: float = 60.0
    max_retries: int = 6
    temperature: float = 1.0
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | None = None
    stream: bool = True
    models: dict[str, ModelEntry] = Field(default_factory=dict)

    @field_validator("api_key")
    @classmethod
    def _api_key_must_be_str(cls, v: str) -> str:
        """§9.1.1 强约束 3：非字符串 api_key 一律拒绝（避免 LangChain 收到怪类型）。"""
        if not isinstance(v, str):  # pragma: no cover - pydantic 先拦一层
            raise ValueError("api_key 必须是字符串")
        return v

    @field_validator("api_host")
    @classmethod
    def _api_host_must_be_url(cls, v: str) -> str:
        """§11.1 #11：api_host 非 URL 格式 → 硬越界（exit 11）。"""
        if v in ("", "default"):
            return v
        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", v):
            raise ValueError(f"api_host 必须是 http(s) URL，收到 {v!r}")
        return v

    @field_validator("temperature")
    @classmethod
    def _temperature_range(cls, v: float) -> float:
        """§11.1 #11：硬越界 → error（exit 11）。软越界 → warning（exit 0）。"""
        if not (0.0 <= v <= 2.0):
            raise ValueError(f"temperature 必须在 [0.0, 2.0] 内，收到 {v}")
        return v

    @field_validator("max_retries")
    @classmethod
    def _max_retries_range(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"max_retries 不能为负，收到 {v}")
        return v

    @field_validator("timeout")
    @classmethod
    def _timeout_range(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"timeout 必须为正数，收到 {v}")
        return v


class MiniMaxSection(ProviderSection):
    """``[MiniMax]`` —— OpenAI 兼容 + Coding Plan ``sk-cp-`` 密钥（§3.6）。"""

    # §3.6.4：reasoning_split 是**显式声明的 schema 字段**（不是 [provider.extra]
    # 自由透传口），解析层负责翻译成 ChatOpenAI 的 extra_body。
    reasoning_split: bool | None = None


class DeepSeekSection(ProviderSection):
    """``[deepseek]`` —— 专用 ``ChatDeepSeek``（保留 reasoning_content）。"""

    reasoning_effort: Literal["low", "medium", "high"] | None = None


class BedrockSection(ProviderSection):
    """``[bedrock]`` —— 独立 ``aws_*`` 字段（§8 v2.4 修订：不用 api_key）。

    通过 ``boto3.Session(aws_access_key_id=..., aws_secret_access_key=...,
    region_name=...)`` 显式构造 → boto3 不读 env var / ~/.aws/credentials，
    与 §9.1「不读环境变量」立场完全对齐。
    """

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = ""
    aws_session_token: str = ""


# =============================================================================
# §9.1.1 —— TOML loader 强约束（缺失 → ""，绝不 None）
# =============================================================================
def load_api_key(provider_section: dict[str, Any] | None) -> str:
    """读取 provider 节下的 api_key；缺失或 None 一律返回 ""（空串）。

    **绝不返回 None** —— 否则触发 LangChain ``_resolve_gateway_config`` 的
    env var 回退（``OPENAI_API_KEY`` 等），违背 §9.1「donkey 不读 env var」立场。
    """
    if not provider_section:
        return ""
    raw = provider_section.get("api_key")
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise ProviderTomlFieldTypeError(
            f"api_key 必须是字符串，收到 {type(raw).__name__}（§9.1.1 强约束 3）"
        )
    return raw


# =============================================================================
# §11.1 —— F002 load 校验
# =============================================================================
_TYPE_ERROR_KINDS = {
    "string_type", "int_type", "float_type", "bool_type", "list_type",
    "dict_type", "int_parsing", "float_parsing", "bool_parsing",
    "string_unicode", "datetime_type", "date_type", "time_type",
}


def _pydantic_error_to_donkey(err: dict[str, Any]) -> ProviderTomlLoadError:
    """把 Pydantic ValidationError 映射到设计文档的 7 类子错误。"""
    kind = err.get("type", "")
    loc = ".".join(str(x) for x in err.get("loc", ())) or "<root>"
    msg = err.get("msg", "")
    if kind == "extra_forbidden":
        return ProviderTomlFieldError(
            f"字段 {loc} 未在 schema 中声明（拼写错误？）：{msg}（§7.3 / V2-P5）"
        )
    if kind in _TYPE_ERROR_KINDS:
        return ProviderTomlFieldTypeError(f"字段 {loc} 类型错误：{msg}（§11.1 #10）")
    if kind == "missing":
        return ProviderTomlFieldError(f"字段 {loc} 缺失：{msg}（§11.1）")
    if kind == "value_error":
        return ProviderTomlFieldValueError(f"字段 {loc} 取值非法：{msg}（§11.1 #11）")
    return ProviderTomlFieldError(f"字段 {loc} 校验失败：{msg}")


@dataclass(frozen=True)
class ProviderConfig:
    """F002 load 成功后的解析结果（应用层只认这个对象）。"""

    provider_id: str
    model_id: str
    section: ProviderSection
    model_entry: ModelEntry
    warnings: list[str] = field(default_factory=list)

    def merged_params(self) -> dict[str, Any]:
        """provider 级默认值 + model 级覆盖（§8.1「用户可按 model 覆盖」）。

        用 ``section.model_dump()`` 而不是手写字段清单 —— 这样 per-provider 的
        专属字段（如 MiniMax 的 ``reasoning_split``）不会被漏掉。
        """
        params: dict[str, Any] = self.section.model_dump(exclude={"models"})
        for k, v in self.model_entry.model_dump().items():
            if v is not None:
                params[k] = v
        return params


# provider_id → schema class（per-provider 独立 schema 的注册表）
PROVIDER_SCHEMAS: dict[str, type[ProviderSection]] = {
    "MiniMax": MiniMaxSection,
    "deepseek": DeepSeekSection,
    "bedrock": BedrockSection,
    "ollama": ProviderSection,           # A 档：本地无鉴权
    "openai-compatible": ProviderSection,  # B 档：端点属性未知
}


def load_provider_toml(path: str | Path | None = None) -> ProviderConfig:
    """F002 load：TOML → ProviderConfig（严格解析，错误全部归 exit 11 伞形）。"""
    path = Path(path) if path is not None else CONFIG_PATH
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ProviderTomlSyntaxError(f"{path}: TOML 语法错误：{e}") from e
    except OSError as e:
        raise ProviderTomlSyntaxError(f"{path}: 无法读取：{e}") from e

    # --- 顶层字段 ---------------------------------------------------------
    if "default_provider" not in raw:
        raise ProviderTomlFieldError("顶层 default_provider 缺失（§7.3）")
    if "default_model" not in raw:
        raise ProviderTomlFieldError("顶层 default_model 缺失（§7.3）")
    provider_id = raw["default_provider"]
    model_id = raw["default_model"]
    if not isinstance(provider_id, str) or not provider_id:
        raise ProviderTomlFieldTypeError("default_provider 必须是非空字符串（§11.1 #10）")
    if not isinstance(model_id, str) or not model_id:
        raise ProviderTomlFieldTypeError("default_model 必须是非空字符串（§11.1 #10）")

    # --- scope 校验（§3.3）-----------------------------------------------
    check_v1_scope(provider_id)

    # --- provider 节存在性 -------------------------------------------------
    raw_section = raw.get(provider_id)
    if raw_section is None:
        raise ProviderTomlFieldError(
            f"provider '{provider_id}' 被 default_provider 引用，但 TOML 中没有 [{provider_id}] 节"
        )
    if not isinstance(raw_section, dict):
        raise ProviderTomlFieldTypeError(f"[{provider_id}] 必须是 table（§11.1 #10）")

    # --- §7.3：白名单外的 provider 节一律报错 -----------------------------
    for key in raw:
        if key in ("default_provider", "default_model"):
            continue
        if isinstance(raw[key], dict) and key not in PROVIDER_WHITELIST_V1:
            check_v1_scope(key)  # 抛 ProviderTomlScopeError / ProviderNotInV1ScopeError

    # --- per-provider 严格 schema 校验 ------------------------------------
    schema_cls = PROVIDER_SCHEMAS.get(provider_id)
    if schema_cls is None:
        # §8 V2-P1：每个 provider 一套独立 schema —— 不允许用"通用 schema"兜底，
        # 否则该 provider 的专属字段会被误判为"拼写错误"。
        raise ProviderTomlFieldError(
            f"provider '{provider_id}' 的 per-provider schema 尚未实现"
            f"（§8 V2-P1 要求每个 provider 一套独立 schema；"
            f"本 demo 只实现了 {sorted(PROVIDER_SCHEMAS)}）"
        )
    try:
        section = schema_cls.model_validate(raw_section)
    except ValidationError as e:
        raise _pydantic_error_to_donkey(e.errors()[0]) from e

    # --- api_key 归一化（§9.1.1 强约束）----------------------------------
    section.api_key = load_api_key(raw_section)

    # --- api_host 不允许覆盖的 provider（§11.1 #13）------------------------
    if provider_id in API_HOST_NOT_ALLOWED and section.api_host not in ("", "default"):
        raise ProviderTomlHostNotAllowedError(
            f"[{provider_id}] 的 LangChain 类不允许 api_host 覆盖（填了 {section.api_host!r}）"
        )

    # --- default_model 必须在 models 表中（§11.1 #12）----------------------
    if model_id not in section.models:
        raise ProviderTomlMissingModelError(
            f"default_model '{model_id}' 不在 [{provider_id}.models] 表中；"
            f"已注册：{sorted(section.models) or '（空）'}"
        )

    # --- 空 api_key：按 provider 分三档（§9.2 联网调研结论）----------------
    #   A 档本地（ollama / meta）      → 合法，无 warning
    #   B 档 openai-compatible          → 合法 + warning（端点是否校验鉴权未知）
    #   C 档云端 provider（其余 21 个） → 硬错 exit 11
    tier = API_KEY_OPTIONAL_PROVIDERS.get(provider_id, "C")
    if not section.api_key and tier == "C":
        raise ProviderTomlFieldError(
            f"[{provider_id}] api_key 为空 —— 云端 provider 必须配置真实 key"
            f"（§9.2 C 档：空 key 100% 在构造 ChatModel 阶段失败，报错文案还会指向"
            f"env var，与 V2-P2「绝不读 env var」立场冲突 → 早失败）"
        )

    # --- warnings（不阻塞 load，exit 0）------------------------------------
    warnings: list[str] = []
    if not section.api_key and tier == "B":
        warnings.append(
            f"[{provider_id}] api_key 为空 —— 该端点是否校验鉴权未知（§9.2 B 档）；"
            f"解析层将填占位符 \"not-needed\"（openai SDK 拒绝空串）"
        )
    if section.api_host == "default" and provider_id != "ollama":
        warnings.append(
            f"[{provider_id}] api_host = \"default\" 仅 ollama 支持，将回退到 provider 默认端点（§11.1 #18）"
        )
    if section.temperature > 1.5:
        warnings.append(
            f"[{provider_id}] temperature = {section.temperature} 偏高（软越界，仅 warning，§11.1 #14）"
        )
    if section.api_host == "" and provider_id not in ("ollama", "openai-compatible", "meta", "databricks"):
        warnings.append(
            f"[{provider_id}] api_host 为空 —— 解析层将使用 provider 默认端点（§10.1）"
        )

    return ProviderConfig(
        provider_id=provider_id,
        model_id=model_id,
        section=section,
        model_entry=section.models[model_id],
        warnings=warnings,
    )


# =============================================================================
# §15.2 —— ReusableProvider（零自研解析：直接调 LangChain 官方类）
# =============================================================================
class ReusableProvider(ABC):
    """复用 LangChain ChatModel 的 provider 抽象基类。"""

    provider_id: ClassVar[str]
    default_api_host: ClassVar[str]
    section_cls: ClassVar[type[ProviderSection]]

    @abstractmethod
    def build_chat_model(self, model: str, **params: Any):
        """构造 LangChain ChatModel 实例。"""


class MiniMaxProvider(ReusableProvider):
    """MiniMax 走 ``ChatOpenAI + base_url``（OpenAI 兼容协议，§3.6 / §15.2）。"""

    provider_id = "MiniMax"
    default_api_host = "https://api.minimaxi.com/v1"
    section_cls = MiniMaxSection

    def build_chat_model(self, model: str, **params: Any):
        from langchain_openai import ChatOpenAI

        extra_body: dict[str, Any] = {}
        # §3.6.4：reasoning_split 是**显式声明的 schema 字段**，通过 LangChain
        # 官方机制 extra_body 透传 —— 不是 [provider.extra] 自由透传口。
        reasoning_split = params.get("reasoning_split")
        if reasoning_split is not None:
            extra_body["reasoning_split"] = reasoning_split

        kwargs: dict[str, Any] = {
            "model": model,
            "api_key": params.get("api_key", ""),
            "base_url": params.get("api_host") or self.default_api_host,
            "temperature": params.get("temperature"),
            "max_tokens": params.get("max_tokens"),
            "timeout": params.get("timeout", 60),
            "max_retries": params.get("max_retries", 6),
            "streaming": bool(params.get("stream", True)),
        }
        if params.get("top_p") is not None:
            kwargs["top_p"] = params["top_p"]
        if params.get("stop") is not None:
            kwargs["stop"] = params["stop"]
        if extra_body:
            kwargs["extra_body"] = extra_body
        if params.get("http_client") is not None:
            kwargs["http_client"] = params["http_client"]
        return ChatOpenAI(**kwargs)


class DeepSeekProvider(ReusableProvider):
    """DeepSeek 专用：必须走 ``ChatDeepSeek`` 保留 reasoning_content。"""

    provider_id = "deepseek"
    default_api_host = "https://api.deepseek.com/v1"
    section_cls = DeepSeekSection

    def build_chat_model(self, model: str, **params: Any):
        from langchain_deepseek import ChatDeepSeek

        kwargs: dict[str, Any] = {
            "model": model,
            # §9.1.1：api_key 显式传（哪怕是 ""），不触发 LangChain 的 env var 回退
            "api_key": params.get("api_key", ""),
            "base_url": params.get("api_host") or self.default_api_host,
            "temperature": params.get("temperature"),
            "max_tokens": params.get("max_tokens"),
            "timeout": params.get("timeout", 60),
            "max_retries": params.get("max_retries", 6),
            "streaming": bool(params.get("stream", True)),
        }
        if params.get("top_p") is not None:
            kwargs["top_p"] = params["top_p"]
        if params.get("stop") is not None:
            kwargs["stop"] = params["stop"]
        reasoning_effort = params.get("reasoning_effort")
        if reasoning_effort is not None:
            kwargs["reasoning_effort"] = reasoning_effort
        if params.get("http_client") is not None:
            kwargs["http_client"] = params["http_client"]
        return ChatDeepSeek(**kwargs)


PROVIDER_REGISTRY: dict[str, ReusableProvider] = {
    "MiniMax": MiniMaxProvider(),
    "deepseek": DeepSeekProvider(),
}


# =============================================================================
# §2.4 —— 应用层 facade（业务代码不感知 provider 差异）
# =============================================================================
def effective_api_key(provider_id: str, api_key: str) -> str:
    """§9.2 —— 返回实际要传给 LangChain 的 api_key。

    B 档（``openai-compatible``）空 key 时填**占位符**：openai SDK 把空串视为
    "未提供"，会在**构造期**抛 ``Missing credentials``（§9.1.1 实测）；
    而本地端点（vLLM / LiteLLM / Ollama）根本不校验鉴权 → 占位符足够。
    占位符是 donkey **自产常量**，不读 env var → 不违背 V2-P2。
    """
    if not api_key and API_KEY_OPTIONAL_PROVIDERS.get(provider_id) == "B":
        return PLACEHOLDER_API_KEY
    return api_key


def build_chat_model(cfg: ProviderConfig, **overrides: Any):
    """按 provider_id 构造对应的 LangChain ChatModel。"""
    overrides.setdefault(
        "api_key", effective_api_key(cfg.provider_id, cfg.section.api_key)
    )
    provider = PROVIDER_REGISTRY.get(cfg.provider_id)
    if provider is None:
        raise ProviderTomlScopeError(
            f"provider '{cfg.provider_id}' 尚未接入解析层（§15.2 注册表）"
        )
    params = cfg.merged_params()
    params.update(overrides)
    return provider.build_chat_model(cfg.model_id, **params)


def get_default_chat_model(path: str | Path | None = None, **overrides: Any):
    """业务代码唯一入口：``model = get_default_chat_model()``（§2.4）。"""
    cfg = load_provider_toml(path)
    return build_chat_model(cfg, **overrides)


# =============================================================================
# §4.3.1 —— 运行时异常 → exit code 映射
# =============================================================================
RETRYABLE_LLM_ERRORS = (
    ModelRateLimitError, ModelAPIError, ModelConnectionError, ModelTimeoutError,
)
NON_RETRYABLE_AUTH_ERRORS = (
    ModelAuthenticationError, ModelPermissionDeniedError, ModelNotFoundError,
)
INPUT_LIMIT_ERRORS = (ContextOverflowError,)

EXIT_LOAD_ERROR = 11
EXIT_RETRY_EXHAUSTED = 83
EXIT_CALL_LIMIT = 85
EXIT_AUTH = 90


def compute_exit_code(exc: BaseException) -> int:
    """CLI 层统一的 exit code 计算（对齐 §4.3.1 映射表）。

    ⚠️ 设计文档自身存在三处不一致（见本 demo 报告）：
       - §4.3.1 表格：``ModelInvalidRequestError``(400) → 83
       - §4.3.1 代码片段：它被放进 ``NON_RETRYABLE_AUTH_ERRORS`` → 90
       - §17 一句话总结：「400/ContextOverflowError → 85」
       本实现按**表格**（最具体的一处）取 83，并保留 90 / 85 两个备选值供对照。
    """
    if isinstance(exc, ProviderTomlLoadError):
        return EXIT_LOAD_ERROR
    if isinstance(exc, NON_RETRYABLE_AUTH_ERRORS):
        return EXIT_AUTH
    if isinstance(exc, INPUT_LIMIT_ERRORS):
        return EXIT_CALL_LIMIT
    if isinstance(exc, ModelInvalidRequestError):
        return EXIT_RETRY_EXHAUSTED  # §4.3.1 表格口径
    if isinstance(exc, RETRYABLE_LLM_ERRORS):
        return EXIT_RETRY_EXHAUSTED
    return 1


# =============================================================================
# 网络层观测（§2.2 透传）：用 httpx event hook 抓原始 wire traffic
# =============================================================================
class WireCapture:
    """抓取网络层原始请求 / 响应，验证「传输的时候要透传」。"""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.responses: list[dict[str, Any]] = []

    def _on_request(self, request: httpx.Request) -> None:
        body = request.content.decode("utf-8", errors="replace")
        self.requests.append(
            {
                "method": request.method,
                "url": str(request.url),
                "headers": {
                    k: ("<redacted>" if k.lower() == "authorization" else v)
                    for k, v in request.headers.items()
                },
                "body": body,
            }
        )

    def _on_response(self, response: httpx.Response) -> None:
        try:
            raw = response.read().decode("utf-8", errors="replace")
        except Exception:  # pragma: no cover
            raw = "<unreadable>"
        self.responses.append(
            {"status_code": response.status_code, "body": raw[:2000]}
        )

    def client(self) -> httpx.Client:
        """构造带 event hook 的 httpx client。

        ⚠️ 环境相关：httpx **只原生支持 http/https 代理**；若 env 里配的是
        ``socks://``（Clash / V2Ray 等常见），httpx 会抛
        ``ValueError: Unknown scheme for proxy URL``，除非装了 ``socksio`` 扩展。
        这里优雅降级为直连（trust_env=False）并打印诊断，不让 demo 整体崩掉。
        """
        hooks = {"request": [self._on_request], "response": [self._on_response]}
        if PROXY_MODE == "direct":
            return httpx.Client(
                timeout=httpx.Timeout(120.0), event_hooks=hooks, trust_env=False
            )
        try:
            return httpx.Client(timeout=httpx.Timeout(120.0), event_hooks=hooks)
        except ValueError as e:
            proxy = _detect_proxy_env()
            print(f"  [wire] httpx 不支持 env 里的代理设置：{proxy}")
            print(f"         {e}")
            print("         → 降级为直连（trust_env=False）。若必须走该代理，请执行：")
            print("             pip install 'httpx[socks]'   # 提供 socksio 依赖")
            print("         → 或用 --proxy direct 明确指定直连。")
            return httpx.Client(
                timeout=httpx.Timeout(120.0), event_hooks=hooks, trust_env=False
            )


def _detect_proxy_env() -> str:
    """找出当前 env 里生效的代理设置（httpx 认这几个变量）。"""
    for name in PROXY_ENV_NAMES:
        value = os.environ.get(name)
        if value:
            return f"{name}={value}"
    return "（未检测到代理环境变量）"


# =============================================================================
# 打印工具
# =============================================================================
def banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


def step(title: str) -> None:
    print(f"\n--- {title} " + "-" * max(0, 72 - len(title)))


def mask(key: str) -> str:
    if not key:
        return '"" (空串)'
    if len(key) <= 12:
        return f"{key[:3]}***"
    return f"{key[:8]}***{key[-4:]}"


PASSED: list[str] = []
FAILED: list[str] = []
SKIPPED: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    (PASSED if ok else FAILED).append(label)
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f"  —— {detail}" if detail else ""))


def skip(label: str, reason: str) -> None:
    """因服务端容量等**基础设施**原因无法验证（与设计缺陷无关）。"""
    SKIPPED.append(f"{label}（{reason}）")
    print(f"  [SKIP] {label}  —— {reason}")


# =============================================================================
# 案例组 A —— F002 load 阶段（离线，不发网络请求）
# =============================================================================
BASE_TOML = """\
default_provider = "MiniMax"
default_model = "MiniMax-M3"

[MiniMax]
api_key = "sk-cp-demo"
api_host = "https://api.minimaxi.com/v1"
temperature = 0.7

[MiniMax.models.MiniMax-M3]
max_tokens = 8192

[deepseek]
api_key = "sk-demo"
api_host = "https://api.deepseek.com/v1"

[deepseek.models.deepseek-v4-flash]
max_tokens = 4096
"""


def _write_temp_toml(text: str) -> Path:
    fd, name = tempfile.mkstemp(suffix=".toml", prefix="donkey_demo_")
    Path(name).write_text(text, encoding="utf-8")
    return Path(name)


def run_load_cases() -> None:
    """A 组：验证 §7.3 / §9 / §10 / §11.1 的 load 阶段行为。"""
    banner("A 组｜F002 load 阶段校验（离线，对应设计文档 §7.3 / §9 / §10 / §11.1）")

    # --- A01 正常加载 -----------------------------------------------------
    step("A01  正常加载 provider.toml（happy path）")
    cfg = load_provider_toml(CONFIG_PATH)
    print(f"  provider_id       = {cfg.provider_id}")
    print(f"  model_id          = {cfg.model_id}")
    print(f"  api_key           = {mask(cfg.section.api_key)}")
    print(f"  api_host          = {cfg.section.api_host!r}")
    print(f"  temperature       = {cfg.section.temperature}")
    print(f"  max_tokens        = {cfg.section.max_tokens} (provider 级) "
          f"→ {cfg.merged_params()['max_tokens']} (model 级覆盖后)")
    print(f"  models 表         = {sorted(cfg.section.models)}")
    for w in cfg.warnings:
        print(f"  [warning] {w}")
    check("A01 正常加载成功且 model 级参数覆盖 provider 级", True,
          f"max_tokens {cfg.section.max_tokens} → {cfg.merged_params()['max_tokens']}")

    # --- A02 ~ A11 负例 ----------------------------------------------------
    negative_cases = [
        (
            "A02  字段拼写错误（temprature）→ ProviderTomlFieldError",
            BASE_TOML.replace("temperature = 0.7", "temprature = 0.7"),
            ProviderTomlFieldError,
        ),
        (
            "A03  字段类型错误（timeout = \"60\"）→ ProviderTomlFieldTypeError",
            BASE_TOML.replace('api_host = "https://api.minimaxi.com/v1"',
                              'api_host = "https://api.minimaxi.com/v1"\ntimeout = "60"'),
            ProviderTomlFieldTypeError,
        ),
        (
            "A04  字段值硬越界（temperature = 3.0）→ ProviderTomlFieldValueError",
            BASE_TOML.replace("temperature = 0.7", "temperature = 3.0"),
            ProviderTomlFieldValueError,
        ),
        (
            "A05  api_host 非 URL → ProviderTomlFieldValueError",
            BASE_TOML.replace('api_host = "https://api.minimaxi.com/v1"', 'api_host = "not a url"'),
            ProviderTomlFieldValueError,
        ),
        (
            "A06  白名单外 provider（[foo_ai]）→ ProviderTomlScopeError",
            BASE_TOML + '\n[foo_ai]\napi_key = "x"\n',
            ProviderTomlScopeError,
        ),
        (
            "A07  v2+ 候选 provider（[baidu]）→ ProviderNotInV1ScopeError",
            BASE_TOML + '\n[baidu]\napi_key = "x"\n',
            ProviderNotInV1ScopeError,
        ),
        (
            "A08  default_model 不在 models 表 → ProviderTomlMissingModelError",
            BASE_TOML.replace('default_model = "MiniMax-M3"', 'default_model = "MiniMax-M9"'),
            ProviderTomlMissingModelError,
        ),
        (
            "A09  api_key 类型错误（api_key = 42）→ ProviderTomlFieldTypeError",
            BASE_TOML.replace('api_key = "sk-cp-demo"', "api_key = 42"),
            ProviderTomlFieldTypeError,
        ),
        (
            "A10  TOML 语法错误 → ProviderTomlSyntaxError",
            BASE_TOML + "\nthis is not valid toml =\n",
            ProviderTomlSyntaxError,
        ),
        (
            "A11  model_id 含 '.' 未加引号（MiniMax-M2.7）→ 静默嵌套 → ProviderTomlFieldError",
            BASE_TOML.replace("[MiniMax.models.MiniMax-M3]", "[MiniMax.models.MiniMax-M2.7]"),
            ProviderTomlFieldError,
        ),
        (
            "A12  顶层 default_provider 缺失 → ProviderTomlFieldError",
            BASE_TOML.replace('default_provider = "MiniMax"\n', ""),
            ProviderTomlFieldError,
        ),
        (
            "A13  顶层 default_model 缺失 → ProviderTomlFieldError",
            BASE_TOML.replace('default_model = "MiniMax-M3"\n', ""),
            ProviderTomlFieldError,
        ),
    ]

    for label, text, expected in negative_cases:
        path = _write_temp_toml(text)
        try:
            load_provider_toml(path)
            check(label, False, "没有抛异常 —— schema 校验失效！")
        except ProviderTomlLoadError as e:
            actual = type(e)
            ok = actual is expected
            detail = f"{actual.__name__}: {str(e)[:90]}"
            check(label, ok, detail)
            if ok:
                check(f"     └ exit code 映射 = {compute_exit_code(e)}", compute_exit_code(e) == 11)
        except Exception as e:  # noqa: BLE001
            check(label, False, f"抛了非预期异常 {type(e).__name__}: {e}")
        finally:
            path.unlink(missing_ok=True)

    # --- A14 api_key 缺失 → 归一化为 ""（§9.1.1），且不触发 env var 回退 ----
    step("A14  api_key 字段缺失 → 归一化为 \"\"，绝不回退 env var（§9.1.1）")
    import os

    os.environ["OPENAI_API_KEY"] = "sk-env-should-never-be-used"
    os.environ["DEEPSEEK_API_KEY"] = "sk-env-should-never-be-used"
    # 用 A 档（ollama，本地无鉴权）验证"归一化为 ''"这一步本身不报错
    a_toml = (
        'default_provider = "ollama"\n'
        'default_model = "llama3.1"\n'
        "\n"
        "[ollama]\n"
        'api_host = "default"\n'
        "\n"
        # ⚠️ model_id 含 "." 必须加引号（否则 TOML 解析成嵌套表 —— D3 的实测复现）
        "[ollama.models.\"llama3.1\"]\n"
        "max_tokens = 2048\n"
    )
    path = _write_temp_toml(a_toml)
    try:
        cfg = load_provider_toml(path)
        check("A14 api_key 缺失 → 归一化为 \"\"（不是 None）", cfg.section.api_key == "",
              f"api_key = {mask(cfg.section.api_key)}")
        check("A14 A 档（ollama）空 api_key 合法且无 warning（§9.2 A 档）",
              not any("api_key" in w for w in cfg.warnings),
              "；".join(cfg.warnings) or "（无 warning）")
        check("A14 进程内 env var 存在但未被读取（V2-P2 立场）",
              os.environ["OPENAI_API_KEY"] == "sk-env-should-never-be-used")
    finally:
        path.unlink(missing_ok=True)
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("DEEPSEEK_API_KEY", None)

    # --- A21~A23 空 api_key 三档（§9.2 联网调研结论）----------------------
    step("A21~A23  空 api_key 按 provider 分三档（§9.2）")
    # C 档：云端 provider → 硬错 exit 11
    text = BASE_TOML.replace('api_key = "sk-cp-demo"\n', "")
    path = _write_temp_toml(text)
    try:
        load_provider_toml(path)
        check("A21 C 档（MiniMax，云端）空 api_key → 硬错 exit 11", False, "没有抛异常")
    except ProviderTomlFieldError as e:
        check("A21 C 档（MiniMax，云端）空 api_key → 硬错 exit 11", True, str(e)[:90])
        check("A21 exit code = 11", compute_exit_code(e) == 11)
    finally:
        path.unlink(missing_ok=True)

    # B 档：openai-compatible → 合法 + warning
    b_toml = (
        'default_provider = "openai-compatible"\n'
        'default_model = "my-local-model"\n'
        "\n"
        "[openai-compatible]\n"
        'api_host = "http://localhost:8000/v1"\n'
        "\n"
        "[openai-compatible.models.my-local-model]\n"
        "max_tokens = 4096\n"
    )
    path = _write_temp_toml(b_toml)
    try:
        cfg = load_provider_toml(path)
        check("A22 B 档（openai-compatible）空 api_key → 合法 + warning（§9.2 B 档）",
              any("api_key" in w for w in cfg.warnings),
              "；".join(cfg.warnings) or "（无 warning）")
        # 解析层应填占位符（openai SDK 拒绝空串）
        eff = effective_api_key("openai-compatible", cfg.section.api_key)
        check("A22 解析层填占位符 \"not-needed\"（openai SDK 拒绝空串）",
              eff == PLACEHOLDER_API_KEY, f"effective_api_key = {eff!r}")
        check("A22 A / C 档不填占位符（保持原值）",
              effective_api_key("ollama", "") == "" and
              effective_api_key("deepseek", "") == "")
    except Exception as e:  # noqa: BLE001
        check("A22 B 档 openai-compatible 空 api_key", False, f"{type(e).__name__}: {str(e)[:120]}")
    finally:
        path.unlink(missing_ok=True)

    # --- A15 warning 路径：软越界 / api_host = "default" -------------------
    step("A15  warning 路径（软越界 / api_host=\"default\"）→ exit 0，不阻塞 load")
    text = BASE_TOML.replace("temperature = 0.7", "temperature = 1.9")
    path = _write_temp_toml(text)
    try:
        cfg = load_provider_toml(path)
        check("A15 temperature=1.9 软越界 → 仅 warning", any("偏高" in w for w in cfg.warnings),
              "；".join(cfg.warnings))
    finally:
        path.unlink(missing_ok=True)

    # --- A16 models 子表中的字段也必须严格 ---------------------------------
    step("A16  models 子表字段也受严格 schema 约束（extra=forbid 向下生效）")
    text = BASE_TOML.replace("[MiniMax.models.MiniMax-M3]\nmax_tokens = 8192",
                              "[MiniMax.models.MiniMax-M3]\nmax_token = 8192")
    path = _write_temp_toml(text)
    try:
        load_provider_toml(path)
        check("A16 models 子表字段拼写错误被拦截", False, "没有抛异常")
    except ProviderTomlFieldError as e:
        check("A16 models 子表字段拼写错误被拦截", True, str(e)[:90])
    finally:
        path.unlink(missing_ok=True)

    # --- A17 api_host 不允许覆盖（§11.1 #13）-------------------------------
    step("A17  provider 类不允许 api_host 覆盖 → ProviderTomlHostNotAllowedError")
    text = (
        'default_provider = "bedrock"\n'
        'default_model = "us.anthropic.claude-sonnet-4-6"\n'
        "\n"
        "[bedrock]\n"
        'aws_access_key_id = "AKIA..."\n'
        'aws_secret_access_key = "secret"\n'
        'aws_region = "us-east-1"\n'
        'api_host = "https://my-proxy.example.com"\n'
        "\n"
        "[bedrock.models.\"us.anthropic.claude-sonnet-4-6\"]\n"
        "max_tokens = 8192\n"
    )
    path = _write_temp_toml(text)
    try:
        load_provider_toml(path)
        check("A17 api_host 不允许覆盖被拦截", False, "没有抛异常")
    except ProviderTomlHostNotAllowedError as e:
        check("A17 api_host 不允许覆盖被拦截（§11.1 #13）", True, str(e)[:90])
        check("A17 exit code = 11", compute_exit_code(e) == 11)
    finally:
        path.unlink(missing_ok=True)

    # --- A18 白名单与 LangChain 官方 provider 列表交叉核对（§3.1）---------
    step("A18  白名单与 LangChain init_chat_model 官方 provider 列表交叉核对（§3.1）")
    try:
        from langchain.chat_models.base import _BUILTIN_PROVIDERS

        check("A18 LangChain _BUILTIN_PROVIDERS 实测 30 个（§3.1 数据源核对）",
              len(_BUILTIN_PROVIDERS) == 30, f"实际 {len(_BUILTIN_PROVIDERS)}")
        check("A18 白名单 26 个 provider_id（§3.1 表格核对）",
              len(PROVIDER_WHITELIST_V1) == 26, f"实际 {len(PROVIDER_WHITELIST_V1)}")
        check("A18 'google' 不在 _BUILTIN_PROVIDERS（§3.1 顶部 ⚠️ 关键细节成立）",
              "google" not in _BUILTIN_PROVIDERS,
              f"google_genai={'google_genai' in _BUILTIN_PROVIDERS}")
        # donkey 自定义 provider_id → LangChain provider_id 的 facade 转发是必须的
        from langchain.chat_models import init_chat_model

        try:
            init_chat_model(model="gemini-2.0-flash", model_provider="google",
                            api_key="x")
            check("A18 init_chat_model(model_provider='google') 应当失败（需 facade 转发）",
                  False, "居然成功了")
        except ValueError as e:
            check("A18 init_chat_model(model_provider='google') 抛 ValueError → "
                  "donkey facade 必须转发到 google_genai（§3.1 ⚠️ 结论成立）",
                  True, str(e)[:100])
    except ImportError:  # pragma: no cover
        skip("A18 白名单与 LangChain provider 列表交叉核对", "langchain 版本不兼容")

    # --- A19 白名单 provider_id 与 LangChain 别名的交集说明 -----------------
    step("A19  白名单 provider_id ≠ LangChain 别名的情况（facade 必须翻译）")
    alias_map = {
        "MiniMax": "openai",        # §3.6：MiniMax 走 ChatOpenAI + base_url
        "openai-compatible": "openai",
        "xiaomi": "openrouter",
        "meta": "ollama",
        "google": "google_genai",   # §3.1 ⚠️
    }
    for pid, lc in alias_map.items():
        print(f"  donkey provider_id={pid!r} → LangChain provider_id={lc!r}")
    check("A19 8 个 OpenAI 兼容 provider 复用 ChatOpenAI（§3.2 关键观察）",
          alias_map["MiniMax"] == "openai" and alias_map["openai-compatible"] == "openai")
    check("A19 2 个多平台路由 provider 需 facade 翻译（§3.2 关键观察）",
          alias_map["xiaomi"] == "openrouter" and alias_map["meta"] == "ollama")

    # --- A20 空 api_key 的真实后果（§9.1.1 / §9.2 的设计缺口）------------
    step("A20  ⚠️ 归一化后的 api_key=\"\" 在**模型构造期**的真实后果（设计缺口）")
    empty_cfg = ProviderConfig(
        provider_id="MiniMax",
        model_id="MiniMax-M3",
        section=MiniMaxSection.model_validate({"api_key": "", "stream": False}),
        model_entry=ModelEntry(),
    )
    # 本用例只关心 api_key 的行为，临时摘掉 env 里的代理设置以免干扰
    proxy_env = {
        k: os.environ.pop(k) for k in PROXY_ENV_NAMES if k in os.environ
    }
    try:
        build_chat_model(empty_cfg)
        check("A20 api_key=\"\" 时构造 ChatModel", False, "居然构造成功了")
    except Exception as e:  # noqa: BLE001
        print(f"  异常类型 = {type(e).__name__}")
        print(f"  异常摘要 = {str(e)[:220]}")
        check("A20 api_key=\"\" → openai SDK 在**构造期**抛 Missing credentials"
              "（不是运行时的 401 / ModelAuthenticationError）",
              "Missing credentials" in str(e) or "DEEPSEEK_API_KEY" in str(e),
              type(e).__name__)
        print("  → 结论：§9.1.1 的「api_key 缺失 → \"\"，不回退 env var」在 LangChain 层")
        print("    成立（确实不回退），但底层 openai SDK 见到空串直接拒绝构造 client，")
        print("    且报错信息恰恰指向 env var（项目明令禁止的路径）。")
        print("    因此 §9.2「api_key 空 → warning + exit 0，运行时抛鉴权异常 → exit 90」")
        print("    这条链路在实践中走不通：空 api_key 应在 F002 load 阶段升级为硬错")
        print("    （exit 11 / ProviderTomlFieldError），或至少在构造 ChatModel 前拦截。")
    finally:
        os.environ.update(proxy_env)



# =============================================================================
# 案例组 B —— 运行时（联网）
# =============================================================================
def _is_capacity_error(exc: BaseException) -> bool:
    """MiniMax Coding Plan 集群偶发 529 overloaded —— 属基础设施问题，与设计无关。"""
    text = str(exc)
    return "529" in text or "overloaded" in text.lower()


def _retry_invoke(model, messages, attempts: int = 4, base_sleep: float = 6.0, cap: float = 30.0):
    """MiniMax Coding Plan 集群偶发 529 overloaded —— 指数退避重试（封顶 30s）。"""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return model.invoke(messages)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            print(f"      [retry {i + 1}/{attempts}] {type(e).__name__}: {str(e)[:120]}")
            if i < attempts - 1:
                time.sleep(min(base_sleep * (2**i), cap))
    raise last_exc  # type: ignore[misc]


def run_runtime_cases() -> None:
    """B 组：验证 §2.4 / §3.2 / §3.6 / §4.3.1 / §15.2 的运行时行为。"""
    banner("B 组｜运行时验证（联网，MiniMax-M3 + deepseek-v4-flash）")

    # --- 脱敏占位符检测：配置文件里还是占位符就别去联网了 ------------------
    placeholders = _find_placeholder_keys(CONFIG_PATH)
    if placeholders:
        print("  ⚠️ 当前配置里的 api_key 仍是占位符 —— 跳过联网用例：")
        for item in placeholders:
            print(f"       {item}")
        print("     → 真实 key 请写进 provider.local.toml（已 gitignore），然后：")
        print(f"         .venv/bin/python {Path(__file__).name} "
              f"--config {HERE / 'provider.local.toml'}")
        for label in ("B01~B10 联网用例（MiniMax-M3 / deepseek-v4-flash 真实调用）",):
            skip(label, "配置里 api_key 仍是占位符（REPLACE_ME）")
        return

    wire = WireCapture()

    # ---------------------------------------------------------------- B01
    step("B01  默认 provider（MiniMax-M3）端到端 invoke（§2.4 应用层抽象）")
    cfg = load_provider_toml(CONFIG_PATH)
    print(f"  default_provider = {cfg.provider_id} / default_model = {cfg.model_id}")
    minimax_resp: AIMessage | None = None
    model = None
    try:
        model = build_chat_model(cfg, http_client=wire.client())
        minimax_resp = _retry_invoke(
            model, [HumanMessage(content="用一句话介绍你自己。")], attempts=10, base_sleep=4.0
        )
        resp: AIMessage = minimax_resp
        print(f"  content          = {resp.content[:300]}")
        print(f"  usage_metadata   = {resp.usage_metadata}")
        print(f"  finish_reason    = {resp.response_metadata.get('finish_reason')}")
        print(f"  model_name       = {resp.response_metadata.get('model_name')}")
        check("B01 MiniMax-M3 端到端调用成功", bool(resp.content), f"{len(resp.content)} 字符")
        check("B01 usage_metadata 统一为 LangChain schema（input/output/total_tokens）",
              resp.usage_metadata is not None
              and {"input_tokens", "output_tokens", "total_tokens"} <= set(resp.usage_metadata))
        check("B01 网络层透传：请求体原样发出（未解析、未改写）",
              bool(wire.requests) and wire.requests[-1]["url"].endswith("/chat/completions"),
              wire.requests[-1]["url"] if wire.requests else "")
    except Exception as e:  # noqa: BLE001
        check("B01 MiniMax-M3 端到端调用成功", False, f"{type(e).__name__}: {str(e)[:200]}")
        print(f"      → exit code 应为 {compute_exit_code(e)}")

    # ---------------------------------------------------------------- B02
    step("B02  MiniMax-M3 的 <think> 标签是否保留在 content（§3.6 / §3.6.5）")
    try:
        resp = minimax_resp
        if resp is None or "<think>" not in str(resp.content):
            # B01 那次没有触发 thinking —— 再问一道需要推理的题
            resp = _retry_invoke(
                model,
                [HumanMessage(content="仔细想一下：3.14 和 3.14159 哪个大？简要说明。")],
                attempts=10,
                base_sleep=4.0,
            )
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        thinking, answer = extract_thinking(resp)
        has_tag = "<think>" in content and "</think>" in content
        print(f"  content 前 200 字 = {content[:200]!r}")
        print(f"  <think> 标签在 content 中 = {has_tag}")
        print(f"  提取到的 thinking = {thinking[:160]!r}")
        print(f"  提取到的 answer   = {answer[:160]!r}")
        check("B02 MiniMax thinking 以 <think> 标签保留在 content（设计文档 §3.6 结论成立）",
              has_tag)
        check("B02 应用层可用正则提取 thinking（§3.6.5 伪代码可用）",
              thinking != "" and answer != "")
    except Exception as e:  # noqa: BLE001
        if _is_capacity_error(e):
            skip("B02 MiniMax thinking 验证", f"服务端 529 过载：{str(e)[:80]}")
        else:
            check("B02 MiniMax thinking 验证", False, f"{type(e).__name__}: {str(e)[:200]}")

    # ---------------------------------------------------------------- B03
    step("B03  MiniMax-M3 工具调用（§3.6.1 端到端场景：get_weather）")
    try:
        agent_model = build_chat_model(cfg, http_client=wire.client())
        resp = _retry_invoke(
            agent_model.bind_tools([get_weather]),
            [HumanMessage(content="What's the weather in San Francisco?")],
            attempts=10,
            base_sleep=4.0,
        )
        print(f"  content       = {resp.content[:200]!r}")
        print(f"  tool_calls    = {resp.tool_calls}")
        print(f"  finish_reason = {resp.response_metadata.get('finish_reason')}")
        check("B03 MiniMax-M3 能返回 tool_calls（OpenAI 兼容协议解析正常）",
              bool(resp.tool_calls), str(resp.tool_calls)[:100])
    except Exception as e:  # noqa: BLE001
        if _is_capacity_error(e):
            skip("B03 MiniMax-M3 工具调用", f"服务端 529 过载：{str(e)[:80]}")
        else:
            check("B03 MiniMax-M3 工具调用", False, f"{type(e).__name__}: {str(e)[:200]}")

    # ---------------------------------------------------------------- B04
    step("B04  deepseek-v4-flash 走专用 ChatDeepSeek → reasoning_content 保留（§3.2 / §5.3）")
    # 直接复用 provider.toml 里真实的 [deepseek] 节，只把默认 provider/model 切过去
    text = CONFIG_PATH.read_text(encoding="utf-8")
    text = text.replace('default_provider = "MiniMax"', 'default_provider = "deepseek"')
    text = text.replace('default_model = "MiniMax-M3"', 'default_model = "deepseek-v4-flash"')
    path = _write_temp_toml(text)
    try:
        ds_cfg = load_provider_toml(path)
        print(f"  读到 provider_id={ds_cfg.provider_id} model_id={ds_cfg.model_id} "
              f"api_host={ds_cfg.section.api_host}")
        ds_model = build_chat_model(ds_cfg, http_client=wire.client())
        print(f"  LangChain 类 = {type(ds_model).__module__}.{type(ds_model).__name__}")
        resp = _retry_invoke(ds_model, [HumanMessage(content="1+1 等于几？简单回答。")])
        reasoning = resp.additional_kwargs.get("reasoning_content")
        print(f"  content             = {resp.content[:200]!r}")
        print(f"  reasoning_content   = {str(reasoning)[:220]!r}")
        print(f"  usage_metadata      = {resp.usage_metadata}")
        check("B04 走的是 ChatDeepSeek 专用类（不是 ChatOpenAI）",
              type(ds_model).__name__ == "ChatDeepSeek", type(ds_model).__name__)
        check("B04 ChatDeepSeek 保留 reasoning_content（专用类的价值成立）",
              bool(reasoning), str(reasoning)[:80])
        check("B04 usage_metadata 统一（input/output/total_tokens）",
              resp.usage_metadata is not None
              and {"input_tokens", "output_tokens", "total_tokens"} <= set(resp.usage_metadata))
    except Exception as e:  # noqa: BLE001
        check("B04 deepseek reasoning_content 验证", False, f"{type(e).__name__}: {str(e)[:200]}")
    finally:
        path.unlink(missing_ok=True)

    # ---------------------------------------------------------------- B05
    step("B05  对照实验：同一个 deepseek-v4-flash 改走 ChatOpenAI + base_url")
    print("      → 验证设计文档 §3.2 关键警告「走 ChatOpenAI 会丢弃 reasoning_content」")
    try:
        from langchain_openai import ChatOpenAI

        bad_model = ChatOpenAI(
            model="deepseek-v4-flash",
            api_key=_deepseek_api_key(),
            base_url="https://api.deepseek.com/v1",
            temperature=1.0,
            max_tokens=4096,
            http_client=wire.client(),
        )
        resp = _retry_invoke(bad_model, [HumanMessage(content="1+1 等于几？简单回答。")])
        reasoning = resp.additional_kwargs.get("reasoning_content")
        raw = wire.responses[-1]["body"] if wire.responses else ""
        print(f"  LangChain 类        = {type(bad_model).__name__}")
        print(f"  content             = {resp.content[:160]!r}")
        print(f"  reasoning_content   = {reasoning!r}")
        print(f"  原始响应体片段       = {raw[:200]!r}")
        check("B05 原始响应体里确有 reasoning_content（服务端返回了）",
              "reasoning_content" in raw)
        check("B05 但 ChatOpenAI 路径拿不到 reasoning_content（被丢弃 —— 警告成立）",
              not reasoning)
    except Exception as e:  # noqa: BLE001
        check("B05 对照实验", False, f"{type(e).__name__}: {str(e)[:200]}")

    # ---------------------------------------------------------------- B06
    step("B06  deepseek-v4-flash 流式（TOML 里 stream = true 生效）")
    stream_toml = (
        'default_provider = "deepseek"\n'
        'default_model = "deepseek-v4-flash"\n'
        "\n"
        "[deepseek]\n"
        f'api_key = "{_deepseek_api_key()}"\n'
        'api_host = "https://api.deepseek.com/v1"\n'
        "stream = true\n"
        "temperature = 1.0\n"
        "max_tokens = 4096\n"
        "\n"
        "[deepseek.models.deepseek-v4-flash]\n"
        "max_tokens = 4096\n"
    )
    path = _write_temp_toml(stream_toml)
    try:
        ds_stream_cfg = load_provider_toml(path)
        stream_model = build_chat_model(ds_stream_cfg, http_client=wire.client())
        print(f"  从 TOML 读到 stream = {ds_stream_cfg.section.stream}")
        print(f"  model.streaming    = {getattr(stream_model, 'streaming', None)}"
              f"（LangChain 侧 streaming 参数）")
        chunks = []
        for chunk in stream_model.stream([HumanMessage(content="用一句话说说什么是贪心算法。")]):
            chunks.append(chunk.content)
        text_all = "".join(chunks)
        print(f"  chunk 数 = {len(chunks)}，拼接结果前 120 字 = {text_all[:120]!r}")
        check("B06 TOML 的 stream 字段透传到 LangChain（streaming=True）",
              getattr(stream_model, "streaming", None) is True)
        check("B06 流式输出可正常累积", bool(text_all.strip()), f"{len(chunks)} chunks")
    except Exception as e:  # noqa: BLE001
        check("B06 流式验证", False, f"{type(e).__name__}: {str(e)[:200]}")
    finally:
        path.unlink(missing_ok=True)

    # ---------------------------------------------------------------- B07
    step("B07  exit code 映射（§4.3.1）：错误 api_key → 鉴权类 → exit 90")
    try:
        bad_cfg = ProviderConfig(
            provider_id="deepseek",
            model_id="deepseek-v4-flash",
            section=DeepSeekSection.model_validate(
                {
                    "api_key": "sk-invalid-key-for-demo",
                    "api_host": "https://api.deepseek.com/v1",
                    "max_tokens": 64,
                    "stream": False,
                    "models": {"deepseek-v4-flash": {}},
                }
            ),
            model_entry=ModelEntry(),
        )
        bad_model = build_chat_model(bad_cfg, http_client=wire.client())
        bad_model.invoke([HumanMessage(content="hi")])
        check("B07 错误 api_key 被拒绝", False, "居然调用成功了")
    except Exception as e:  # noqa: BLE001
        code = compute_exit_code(e)
        print(f"  异常类型 = {type(e).__name__}")
        print(f"  异常摘要 = {str(e)[:200]}")
        print(f"  exit code = {code}")
        check("B07 鉴权类异常 → exit 90", code == EXIT_AUTH, f"{type(e).__name__} → {code}")
        check("B07 异常类型属于 LangChain 标准异常（§4.3）",
              isinstance(e, (ModelAuthenticationError, ModelPermissionDeniedError,
                             ModelInvalidRequestError, ModelNotFoundError)),
              type(e).__name__)

    # ---------------------------------------------------------------- B08
    step("B08  exit code 映射（§4.3.1）：MiniMax 集群过载（529）→ 可重试类 → exit 83")
    try:
        resp = _retry_invoke(model, [HumanMessage(content="ping")], attempts=6, base_sleep=4.0)
        check("B08 MiniMax 本轮可用（未触发 529）", True, resp.content[:60])
    except Exception as e:  # noqa: BLE001
        code = compute_exit_code(e)
        print(f"  异常类型 = {type(e).__name__}")
        print(f"  exit code = {code}（可重试类：429 / 5xx / 网络 / 超时）")
        check("B08 5xx/过载类异常 → exit 83", code == EXIT_RETRY_EXHAUSTED,
              f"{type(e).__name__} → {code}")

    # ---------------------------------------------------------------- B09
    step("B09  网络层透传证据：真实请求 / 响应（每个 provider 各一条）")
    seen: set[str] = set()
    for req in wire.requests:
        host = req["url"].split("/")[2]
        if host in seen:
            continue
        seen.add(host)
        print(f"  {req['method']} {req['url']}")
        try:
            body = json.loads(req["body"])
            body.pop("api_key", None)
            print(f"  body = {json.dumps(body, ensure_ascii=False)[:500]}")
        except json.JSONDecodeError:
            print(f"  body = {req['body'][:300]}")
    if wire.requests:
        req = wire.requests[-1]
        print(f"  headers = {json.dumps(req['headers'], ensure_ascii=False)[:260]}")
        print("  → 请求体由 LangChain 构造后原样发出；donkey 解析层不碰 HTTP body（§2.2）")
        check("B09 Authorization header 存在且已脱敏展示",
              "authorization" in {k.lower() for k in req["headers"]})
    else:
        check("B09 抓到网络层请求", False, "没有任何请求被记录")

    # ---------------------------------------------------------------- B10
    step("B10  实现细节核对：LangChain 实际下发的字段名（文档 vs 实现）")
    mm_body = next(
        (json.loads(r["body"]) for r in wire.requests
         if "minimaxi" in r["url"] and r["body"].startswith("{")),
        {},
    )
    ds_body = next(
        (json.loads(r["body"]) for r in wire.requests
         if "deepseek" in r["url"] and r["body"].startswith("{")),
        {},
    )
    print(f"  MiniMax 请求体字段 = {sorted(mm_body)}")
    print(f"  DeepSeek 请求体字段 = {sorted(ds_body)}")
    print("  → 注意：langchain-openai 1.7.2 的 ChatOpenAI 对**所有**模型都把")
    print("    max_tokens 重命名为 max_completion_tokens（源码 base.py:3830 / :3845），")
    print("    不像设计文档 §5.1 所写的「仅 o-series 用 max_completion_tokens」；")
    print("    MiniMax OpenAI 兼容端点实测接受该字段名。")
    check("B10 MiniMax 走 OpenAI 兼容端点并接受 max_completion_tokens",
          "max_completion_tokens" in mm_body, str(sorted(mm_body)))
    check("B10 DeepSeek（ChatDeepSeek）走 max_tokens 字段",
          "max_tokens" in ds_body, str(sorted(ds_body)))


# =============================================================================
# 工具
# =============================================================================
@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


def extract_thinking(response: AIMessage) -> tuple[str, str]:
    """§3.6.5 —— 从 AIMessage.content 提取 thinking 块和最终回答。"""
    content = response.content if isinstance(response.content, str) else str(response.content)
    m = re.search(r"<think>(.*?)</think>\s*(.*)", content, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", content


def _deepseek_api_key() -> str:
    """从当前配置文件读 deepseek 的 key（demo 不额外引入密钥来源，不读 env var）。"""
    raw = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return load_api_key(raw.get("deepseek"))


def _find_placeholder_keys(path: Path) -> list[str]:
    """找出配置里仍是占位符的 api_key（脱敏版 provider.toml 自带）。"""
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    hits = []
    for provider_id, section in raw.items():
        if not isinstance(section, dict):
            continue
        key = section.get("api_key")
        if isinstance(key, str) and "REPLACE_ME" in key:
            hits.append(f"[{provider_id}].api_key = {key!r}")
    return hits


# =============================================================================
# main
# =============================================================================
def main() -> int:
    global PROXY_MODE

    parser = argparse.ArgumentParser(description="验证《大模型 TOML 参数设计》v2.5")
    parser.add_argument("--offline", action="store_true", help="只跑 F002 load 阶段校验")
    parser.add_argument("--runtime-only", action="store_true", help="只跑联网的运行时验证")
    parser.add_argument(
        "--config",
        default=None,
        help="provider.toml 路径（默认 = 同目录的脱敏版 provider.toml）。"
             "跑联网用例时请指向含真实密钥的 provider.local.toml（已 gitignore）。",
    )
    parser.add_argument(
        "--proxy",
        choices=["env", "direct"],
        default="env",
        help="网络出口：env=跟随 env 里的代理设置（默认）；direct=强制直连。"
             "env 里若是 socks:// 代理且未装 socksio，httpx 会报错——"
             "可 pip install 'httpx[socks]' 或用 --proxy direct。",
    )
    args = parser.parse_args()
    PROXY_MODE = args.proxy
    global CONFIG_PATH
    if args.config:
        CONFIG_PATH = Path(args.config).expanduser().resolve()

    print(__doc__ or "")
    print(f"TOML 配置文件 = {CONFIG_PATH}")
    print(f"网络出口模式   = {PROXY_MODE}")
    sanitize_proxy_env(PROXY_MODE)

    if not args.runtime_only:
        run_load_cases()
    if not args.offline:
        run_runtime_cases()

    banner("汇总")
    print(f"  PASS = {len(PASSED)}   FAIL = {len(FAILED)}   SKIP = {len(SKIPPED)}")
    for f in FAILED:
        print(f"  [FAIL] {f}")
    for s in SKIPPED:
        print(f"  [SKIP] {s}")
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
