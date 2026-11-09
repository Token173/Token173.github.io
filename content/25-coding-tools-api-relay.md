# Claude Code 和 Cursor 接中转 API：一套配置管住所有编程工具

> 「Claude Code 第三方 API 配置」「Cursor 自定义模型 中转站」「ANTHROPIC_BASE_URL 怎么填」「AI 编程 中转站推荐」—— 2026 年这类问题特别多，根源是 AI 编程工具吃 token 的速度远超聊天场景，一个中等规模的重构任务就能烧掉十万以上 token，大家都在找更省、更稳的接入方式。

麻烦不在接口本身，在工具太杂。Claude Code 说 Anthropic 协议，Cursor 说 OpenAI 兼容，Codex CLI 又是自己的一套配置文件，Cherry Studio、Cline、TRAE 各有各的填写入口。每个工具里塞一把 Key，换平台时挨个改，还容易漏。

## 先分清两种协议入口

| 工具类型 | 用什么协议 | 关键变量 / 字段 |
|---|---|---|
| Claude Code CLI | Anthropic Messages | `ANTHROPIC_BASE_URL`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_MODEL` |
| Claude Code VS Code 扩展 | 同上，但读扩展设置 | `claudeCode.environmentVariables` |
| OpenAI 兼容工具（Cursor / Cline / Cherry Studio / Chatbox） | Chat Completions | `OPENAI_BASE_URL` 或界面里的 Base URL |
| Codex CLI | 可配 chat completions | `~/.codex/config.toml`、`auth.json` |

最常犯的错是把 OpenAI 兼容地址填进 `ANTHROPIC_BASE_URL`。有的平台两个端点都提供，路径还不一样，填错就是 401 或 404。接之前先看平台文档里「Anthropic 协议」那一栏，别照搬 `/v1` 那个地址。

## Claude Code 的最小可用配置

`~/.claude/settings.json`：

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

后两行别省。Claude Code 会拿小模型跑摘要、压缩上下文这类后台任务，不指定的话它会去撞一个平台并不存在的默认 ID，报 `model not found`，而且报错位置很隐蔽，能查半天。

VS Code 扩展要在用户设置里单独写：

```json
{
  "claudeCode.environmentVariables": [
    { "name": "ANTHROPIC_BASE_URL", "value": "https://token173.net" },
    { "name": "ANTHROPIC_AUTH_TOKEN", "value": "sk-你的令牌" }
  ]
}
```

扩展在启动前会校验凭据，写在 `settings.json` 里的值能到达进程，但不参与这一步校验 —— 这是很多人「CLI 能用、插件报认证失败」的原因。

## OpenAI 兼容工具：三件套

Cursor、Cline、Cherry Studio、Chatbox 这类，字段名字不同，内容永远是这三样：

```
Base URL : https://token173.net/v1      （不要写完整 /chat/completions）
API Key  : sk-你的令牌
Model    : 控制台模型列表里的 ID
```

SDK 会自己拼路径，填完整端点会变成 `/v1/chat/completions/chat/completions`。反过来，手写 curl 就要用完整地址。

先用 curl 把链路问题从工具里剥出来：

```bash
curl -sS -X POST "https://token173.net/v1/chat/completions" \
  -H "Authorization: Bearer sk-你的令牌" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-6.1-sol","messages":[{"role":"user","content":"只回复 OK"}]}'
```

curl 通、工具不通，问题在工具配置；curl 就不通，问题在地址、密钥或模型 ID。

## 工具太多时，加一层本地路由

装了四五个工具之后，我改用本地代理统一收口：cc-switch 这类工具在本机起一个 `http://127.0.0.1:15721/v1`，真实 Key 只存在它里面，所有工具统一指向这个本地地址，Key 随便填（本地不校验）。

好处很具体：换平台只改一处；每个工具的调用记录能在一个面板里看到；Key 不散落在五个配置文件里。查「某个工具到底有没有走中转」这种问题，看转发记录就行，不用抓包。

一个通用公式：凡是支持自定义 Base URL 的工具，都能这么接。配置三件套变成 `Base URL = 本地代理地址`、`API Key = 任意值`、`Model = 上游实际 ID`。

## 报错速查

| 现象 | 常见原因 | 动作 |
|---|---|---|
| 401 / invalid key | 令牌带空格、鉴权头不对、协议端点混用 | 区分 `ANTHROPIC_AUTH_TOKEN` 与 `ANTHROPIC_API_KEY`，确认端点类型 |
| 404 model not found | ID 与平台列表不一致、后台默认型号没配 | 拉 `/v1/models` 复制 ID；补齐两个 DEFAULT 变量 |
| Connection refused | 本地路由没开、端口被占 | 检查路由总开关，`lsof -i :15721` |
| 长任务中途断 | 读超时 30 秒 + 自动重试 | 长任务读超时放宽到 120s，重试上限 1 |
| 能聊天不会改文件 | 型号不支持 tool calling | 换支持工具调用的型号，查模型说明 |
| 账单比预估高 | 超时重发、后台小任务走了重型模型 | 查 request_id 附近有没有重复调用；指定 haiku 档 |

最后一条在编程工具里格外常见。长会话反复带着整个代码文件，缓存命中率直接决定账单。选型时留意后台能不能把 `cache_read_tokens` 单列、冷热调用扣费是不是真有差别。

## 配置这块我怎么收口

Key 按环境拆：本地开发一个、CI 一个、团队共用走子账号，各自设额度上限。所有值放环境变量或服务端配置，`.env` 加进 `.gitignore`，别提交进仓库，也别发群里。

平台这边我用 [token173.net](https://token173.net)，主要是它同时给 OpenAI 兼容和 Anthropic 协议两个入口，控制台里 `claude-opus-5-5`、`claude-sonnet-5-5`、`claude-haiku-5-5` 和 GPT、国产那几条线在一个 Key 下面。上面那套「CLI 走 Anthropic、Cursor 走 OpenAI 兼容」的混合配置，不用开两个账号、也不用对两份账单。

## 收尾几句

编程工具对协议兼容、响应速度和缓存命中都比普通聊天敏感。配好之后别只问「你好」，拿一个真实任务试：让它读 README、改一个函数、补一组测试。能完整跑完三轮，才算真接好了。

模型 ID、协议端点和参数支持范围会调整，上线前拉一次 `/v1/models`，以平台当前文档为准。
