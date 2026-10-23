# providers/ —— 供应商配置目录索引

本目录收录 v1 白名单内的 **26 家**供应商，每家一个配置文件。目录内的配置在出厂态**全部处于关闭状态**，不会给后续的配置检查添乱。

## 供应商清单

```
openai
anthropic
google
ollama
xai
mistral
qwen
deepseek
doubao
kimi
zhipu
minimax
tencent
xiaomi
stepfun
openai-compatible
meta
bedrock
groq
fireworks
together
cohere
perplexity
databricks
cerebras
openrouter
```

## 命名规则

一 provider 一文件，**文件名 stem == provider_id**（例如 `openai.toml` 的 stem 是 `openai`）。

`default.toml` 是保留名，用于存放全局默认，**不可**用作供应商名。

## 启用三步

1. 把对应文件里的 `enabled` 改成 `true`；
2. 填入凭据（`api_key` / `aws_*` 等，按各家的专属账号字段规则）；
3. 在 `providers/default.toml` 里设置 `default_provider` 与 `default_model`。

## 未启用的文件完全惰性

`enabled = false` 的文件**完全惰性**：不校验字段、不要求填入凭据、不参与连通性检查 —— 只有文件名 stem 会被核对是否属于上面的白名单。

文件名不在上面 26 家之内时，`donkey load` 会报错（错误码见 `donkey load` 的文档）。
