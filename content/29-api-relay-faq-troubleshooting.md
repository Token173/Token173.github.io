# API 中转站 FAQ：401、404、model not found、流式断流，按现象查

2026 年这类问题里，真正出在中转平台本身的其实不多。多数是三件套没对齐 —— API Key、Base URL、模型名，或者客户端的超时和重试配置还停留在聊天场景。下面按遇到频率排。

---

### Q：401 / invalid_api_key / 认证失败

先按顺序排除：

1. Key 复制带了前后空格，或者粘进配置文件时多了换行。
2. Key 来自 A 平台，Base URL 填了 B 平台。三件套必须同源。
3. 鉴权头不对。Anthropic 客户端发 `x-api-key`，OpenAI 系发 `Authorization: Bearer`；有的平台两种都收，有的只收一种。Claude Code 还要区分 `ANTHROPIC_AUTH_TOKEN` 与 `ANTHROPIC_API_KEY`。
4. Key 被回收、额度用尽、或后台设了 IP 白名单而出口 IP 变了。
5. 环境变量没生效 —— 改完 `.zshrc` 忘了重开终端，或者 systemd / CI 里读的是另一份配置。

拿 curl 打一次最小请求。curl 通、工具不通，问题在工具配置层。

---

### Q：404 / model not found

聚合平台的模型 ID 是平台自己维护的别名，不必然等于厂商官方文档里的版本号。带日期后缀的（`deepseek-v4-pro-0813`、`doubao-seedance-2-0-fast-260128`）、带变体后缀的（`gpt-image-2-d`）、大小写和连字符，差一个字符就是 404。

处理：

```bash
curl -sS "https://token173.net/v1/models" \
  -H "Authorization: Bearer $RELAY_API_KEY" \
  | python3 -c "import sys,json; print('\n'.join(m['id'] for m in json.load(sys.stdin)['data']))"
```

从返回里复制，别手打，也别照抄任何教程（包括这篇）。另外模型会上下架，把这次校验固化进部署脚本更省事。

Claude Code 还有个专属坑：后台小任务会去找默认 haiku / sonnet 型号，没显式指定的话会报一个来源很隐蔽的 404。把 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 和 `ANTHROPIC_DEFAULT_SONNET_MODEL` 都填上。

---

### Q：模型列表拉不出来 / 客户端显示空

有些聚合端点不返回 `/v1/models`，或返回格式客户端解析不了。这不代表不能用。Chatbox、Cherry Studio 里手动添加模型 ID，再发一条消息验证即可。别卡在列表上。

---

### Q：Base URL 到底填到哪儿

多数 SDK 和客户端自己拼 `/chat/completions`，所以填到 `/v1` 就够，填完整端点会变成 `/v1/chat/completions/chat/completions`。手写 curl、`requests`、Postman 则要用完整地址。

Anthropic 协议端点是另一套，Claude Code 会自己拼 `/v1/messages`，地址以平台文档里「Anthropic 端点」那一栏为准，别照搬 OpenAI 兼容地址。Cherry Studio 部分版本还要求去掉末尾斜杠，看字段旁的提示。

---

### Q：流式输出生成到一半断了

分三种：

**连接真断了** —— 看有没有收到 FIN、有没有 keep-alive 注释帧。业务侧缓存已生成的增量文本，断连后带 `partial_completion` 续写，别把整个 prompt 原样重发。

**模型在长思考，连接还活着** —— TCP 没断，只是暂时没有 token。这时候重连只会多扣一次钱。区分靠 keep-alive 和连接状态，别只看「多久没出字」。

**自己的解析器提前退出了** —— 只处理带 `content` 的 chunk，遇到空 content 就 break，或者没处理最后一个只带 usage 的帧和 `[DONE]`。换模型时特别容易暴露，因为不同上游的 SSE 分片习惯不一样。

```python
for chunk in stream:
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta.content
    if delta:
        buffer.append(delta)
# 只在 [DONE] 时结束，空 content 跳过而不是中断
```

---

### Q：长任务老超时，账单还变高了

典型组合：读超时 30 秒 + 自动重试。长回答超时断开，客户端重发全量请求，上游那一次其实已经完整生成并计费了。两次调用，两份钱。

改法：连接超时 5 秒、读超时按任务类型分开（分类 10 秒、长分析 / 生图 / 视频 120 秒以上）；重试上限 1～2 次，指数退避；视频类任务提交后改轮询，超时先按 task_id 查状态再决定要不要重提。

---

### Q：余额明明够，却报 402 / insufficient_quota

几种可能：分组额度独立于总余额、子账号设了单独上限、余额低于某阈值时并发被限到 1、有未完成的长任务预扣冻结、或者欠费阈值触发了保护。去后台看按 Key 的额度明细，别只看总余额。

---

### Q：429 和「静默变慢」哪个更麻烦

后者。明确返回 429，客户端能退避、能排队、能提示用户；静默降速会让客户端误判成超时，触发重试，成功率、延迟、账单三样一起变差。压测时专门测这一项：高并发下有没有明确错误码，超时前后 10 秒内有没有重复的 request_id。

---

### Q：账单和预估对不上

先别怀疑偷量。锁定一条 request_id，把 `prompt_tokens`、`completion_tokens`、缓存字段拆开，检查完整 `messages`（含 system、历史、工具 schema、图片 base64）本地重算输入侧，再看前后 10 秒有没有重复请求和 `client_gone` / `timeout`。大部分差异来自上下文累积和超时重试。

冷热调用各跑十次，确认缓存命中时扣费是不是真降了。报告命中却不按缓存价结算，属于该换平台的信号。

---

### Q：怎么判断问题出在工具还是平台

最小请求用 curl 打一次，通了说明地址、Key、模型名没问题，往后查工具配置、环境变量、解析器、超时。curl 就不通，往前查三件套和协议端点。这个二分能省掉大半瞎猜的时间。

---

### Q：出问题时该给客服什么

request_id、精确到秒的时间、模型 ID、完整错误信息（含错误码）、最小可复现的 curl。只发一句「用不了」或者一张没有请求编号的截图，对方也只能回「请稍后重试」。

这也是选型时值得提前确认的一点：后台能不能按请求查到原始 usage 和错误码。我目前用的 [token173.net](https://token173.net) 控制台能展开单条调用，排查时省了很多来回；换任何平台，先把「出问题能不能拿到一条可复核的请求」问清楚，比问便宜几折实在。

---
