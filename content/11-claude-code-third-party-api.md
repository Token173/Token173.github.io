# 国内直连 Claude：把 Claude Code 指到第三方 API 的完整配置

Claude Code 走的是 Anthropic 协议，不是 OpenAI 那套。很多聚合站只给一个 OpenAI 兼容地址，直接填进去会 401 或者干脆不认。这篇把配置和排错完整过一遍。

## 三个变量就够了

CLI 版读环境变量。macOS / Linux 加到 `~/.zshrc` 或 `~/.bashrc`：

```bash
export ANTHROPIC_BASE_URL="https://token173.net"
export ANTHROPIC_AUTH_TOKEN="sk-你的令牌"
export ANTHROPIC_MODEL="claude-sonnet-5-5"

# 后台小任务也指到可用型号，否则容易撞上不存在的默认 ID
export ANTHROPIC_DEFAULT_HAIKU_MODEL="claude-haiku-5-5"
export ANTHROPIC_DEFAULT_SONNET_MODEL="claude-sonnet-5-5"
```

Windows PowerShell：

```powershell
$env:ANTHROPIC_BASE_URL = "https://token173.net"
$env:ANTHROPIC_AUTH_TOKEN = "sk-你的令牌"
$env:ANTHROPIC_MODEL = "claude-sonnet-5-5"
```

也可以写进 `~/.claude/settings.json`，团队里统一发一份配置更方便：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://token173.net",
    "ANTHROPIC_AUTH_TOKEN": "sk-你的令牌",
    "ANTHROPIC_MODEL": "claude-sonnet-5-5",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-5-5",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-5-5"
  }
}
```

改完重开终端，进任意项目跑 `claude`，让它读一遍 README 做个小任务。能正常读文件、能回答，链路就通了。

## 两个最容易填错的地方

**Base URL 带不带 `/v1`。** 不同平台、不同协议端点要求不一样。Claude Code 这类 Anthropic 客户端通常会自己拼 `/v1/messages`，如果你填的地址已经带了路径，就会出现 `/v1/v1/messages`。以平台文档给的 Anthropic 端点为准，别照搬 OpenAI 兼容那个地址。

**鉴权头。** Anthropic 客户端发的是 `x-api-key`，OpenAI 系发 `Authorization: Bearer`。有的平台两种都收，有的只收一种，还有的要靠 `ANTHROPIC_AUTH_TOKEN` 而不是 `ANTHROPIC_API_KEY`。401 先查这里。

搞不定的时候用 curl 打一次最小请求，把问题从工具里剥出来：

```bash
curl -sS -X POST "https://token173.net/v1/messages" \
  -H "x-api-key: sk-你的令牌" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-5-5",
    "max_tokens": 64,
    "messages": [{"role": "user", "content": "说一句话"}]
  }'
```

curl 通、Claude Code 不通，问题在工具配置；curl 就不通，问题在地址或密钥。

## 报错速查

| 现象 | 常见原因 | 动作 |
|---|---|---|
| 401 / invalid api key | 令牌错、带空格、鉴权头不对 | 核对令牌，试 `ANTHROPIC_AUTH_TOKEN` 与 `ANTHROPIC_API_KEY` 的区别 |
| 404 / model not found | 模型 ID 与平台列表不一致 | 拉 `/v1/models` 复制 ID，别手打 |
| 连接超时 | 地址写错、协议混用、本地代理干扰 | 换成文档给的 Anthropic 端点，检查环境变量是否覆盖 |
| 长任务中途断 | 客户端读超时太短 + 自动重试 | 长任务读超时放宽，重试设上限 |
| 后台小任务报错 | 默认 haiku / sonnet 型号没配 | 把两个 DEFAULT 变量都填上 |
| 工具能聊但不会改文件 | 型号不支持 tool calling | 换支持工具调用的型号，查平台模型说明 |

## 平台选择

需要国内直连、又不想为 Claude 单独开一套境外账号的话，关键是找同时给两种协议入口的平台。我这条链用的是 [token173.net](https://token173.net)：OpenAI 兼容地址给 Cursor、Cherry Studio 这类工具，`https://token173.net` 一栏给 Claude Code 走 Anthropic 协议，两边共用一把 Key 和一份账单。控制台里 `claude-opus-5-5`、`claude-sonnet-5-5`、`claude-haiku-5-5`、`claude-opus-4-8` 这些 ID 和 GPT、Gemini、国产线列在一起，编程工具里想临时换个模型做对照不用改地址。

重度用 Claude Code 的话，额外盯两件事：长会话的通道是否稳定（中途换上游会丢上下文缓存，回答风格会飘），以及后台能不能把缓存命中字段单独列出来。重复带着大段代码上下文的请求，缓存这一项对账单的影响比单价大得多 —— 一个中等规模的重构任务，单轮输入两三万 token 很正常。

Anthropic 端点的具体路径以平台当前文档为准，别照搬 OpenAI 兼容那个 `/v1`。

## 收尾几条纪律

密钥只放环境变量或服务端配置，别提交进 git，`.env` 加进 `.gitignore`；开发、预发、生产分开建 Key，各自设额度上限；模型 ID 从控制台复制，别写死在团队文档里；地址、令牌、模型名必须来自同一个后台，混用必然报错。

最后，托管中转意味着代码和 prompt 会经过第三方服务器。公司私有仓库的核心代码别往里发，这条边界跟配置无关，自己心里划好线。

## 2026 年协议兼容多了哪几处变化

两年前大部分中转只做 `/v1/chat/completions` 一层转发，Claude Code 这类工具得靠本地反代转换协议。现在主流聚合平台陆续把 `/v1/messages`、Gemini 原生格式、Realtime 相关端点做进了同一套网关，配置从「装个转换层」变成了「填两个环境变量」。

但兼容深度仍有差别，接之前值得单独测三处：

- 流式里的 tool call 事件能不能完整透传，有没有被合并或丢弃；
- `thinking` / reasoning 类参数是否支持，返回结构是否被改写；
- 长连接有没有 keep-alive 注释帧，无人值守的长任务跑几十分钟会不会被中间设备掐断。

第三处最容易被忽略。Claude Code 跑长任务时，模型会有一段不出 token 的思考静默期，TCP 还活着；没有心跳帧的链路，容易被 nginx 或本机代理按空闲超时断开。断开后工具自动重试，整个代码上下文再付一遍钱。

## 团队里怎么统一发配置

别让每个人自己改 `~/.claude/settings.json`。做法是管理员建好按项目分的 Key，各自设额度上限，然后把下面这份片段放进内部文档，令牌通过安全渠道单独发：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://token173.net",
    "ANTHROPIC_AUTH_TOKEN": "<由管理员单独提供>",
    "ANTHROPIC_MODEL": "claude-sonnet-5-5",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-5-5",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-5-5"
  }
}
```

配套写清楚三件事：Key 不进 git 和群聊、私有仓库核心代码不往第三方链路发、出错时附 request_id 和原始报错找谁。配置本身十分钟能填完，边界不写清楚，后面一定出事。
