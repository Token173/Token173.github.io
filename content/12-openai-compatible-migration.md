# 国内直连 GPT：把现有项目迁到 OpenAI 兼容接口，实际改两行

「零成本迁移」听着像广告，但 OpenAI 兼容这件事本身是真的做了减法：SDK 还是那个 SDK，请求体还是那个请求体，换的是请求发到哪儿、用哪把钥匙。

## 迁移前先记下这三样

- 当前项目里所有硬编码的 `api.openai.com`
- 用到官方专属能力的地方（Responses API、Batch、Assistants、特定的 beta 头）
- 超时、重试、流式解析的封装位置

第三项最常被忘。中转的链路比直连多一跳，延迟分布不一样，原来给官方调的 30 秒读超时，在长任务里可能误杀。

## 改动本身

Python：

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-你的令牌",       # 改这里
    base_url="https://token173.net/v1",  # 和这里
)

r = client.chat.completions.create(
    model="gpt-6.1-sol",
    messages=[{"role": "user", "content": "把这个接口的错误处理列出来"}],
    stream=True,
)
for chunk in r:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

Node.js：

```js
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-你的令牌',
  baseURL: 'https://token173.net/v1',
});

const stream = await client.chat.completions.create({
  model: 'gpt-6.1-sol',
  messages: [{ role: 'user', content: '把这个接口的错误处理列出来' }],
  stream: true,
});
for await (const part of stream) {
  process.stdout.write(part.choices[0]?.delta?.content ?? '');
}
```

curl：

```bash
curl -sS -X POST "https://token173.net/v1/chat/completions" \
  -H "Authorization: Bearer sk-你的令牌" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-6.1-sol","messages":[{"role":"user","content":"你好"}]}'
```

更推荐把两处都放进环境变量，将来切备用平台不用改代码：

```bash
export OPENAI_API_KEY="sk-你的令牌"
export OPENAI_BASE_URL="https://token173.net/v1"
```

## 逐个验，别一把梭

1. `/v1/models` 能不能拉到当前可用 ID，从返回里复制模型名。
2. 非流式短问答，确认鉴权和路径。
3. 流式输出，确认 SSE 分片和 `[DONE]` 处理。
4. `tools` / `tool_choice`，确认工具调用透传。
5. 长上下文，确认 `prompt_tokens` 和本地估算在一个量级。
6. 错误路径：故意传错模型名，看返回是不是结构化、有没有 request_id。
7. 晚高峰跑一轮，记录成功率和 P95 耗时。

第 6 步值得单独说。有些网关把所有上游错误都糊成一句「服务异常」，出故障时你连是哪一层出的问题都不知道。能给出清晰错误码和请求标识的，后面省的时间非常多。

## 兼容性边界

不是所有官方能力都能一一对应。图像生成走 `/v1/images/generations`，视频多为异步提交加轮询，嵌入和重排序模型各家覆盖不一；新版 Responses API 的某些字段、beta 头、批处理端点，聚合平台未必实现。迁移时把用到的端点列个清单，逐个确认，别等上线才发现某个分支一直 404。

还有个细节：SDK 的 `base_url` 一般填到 `/v1` 就够，SDK 会自己拼 `/chat/completions`。手填完整端点会拼出重复路径。反过来，curl 和 `requests` 这类裸 HTTP 调用要用完整地址。

## 平台

国内直连这一档，我手上项目迁到了 [Token173](https://token173.net) 的 `https://token173.net/v1`。控制台里 GPT 那几个 ID（`gpt-6.1-sol`、`gpt-6-sol`、`gpt-6-astra`、`gpt-5.6-sol`、`gpt-5.6-terra`、`gpt-5.5`、`gpt-5.4`）和 `gpt-image-2`、`gpt-image-2-d` 这些图像型号，以及 Claude、Gemini、Grok、国产线，共用一把 Key 和一份调用记录；境内访问不用配代理，人民币结算。

迁移时真正省事的地方不是「改两行」，是改完之后还能查：每条请求的 usage、错误码、耗时都在同一个后台，第 6 步故意传错模型名的验证也做得下去。有的网关把所有上游错误糊成一句「服务异常」，出了问题连是哪一层都不知道，那种迁移等于把可观测性一起丢了。

型号 ID 和价格会调整，上线前拉一次 `/v1/models`，以价格页当前公示为准，别把这篇里的字符串写死进配置。

## 迁移完再做一件事

把备用平台也写进环境变量，注释里留好切换命令。中转这层依赖上游供给，主力通道波动时，改一行就能切过去，比临时找站、临时充值从容得多。

## 迁移后第一周该盯什么

改完地址不等于迁完。上线第一周我会盯四组数：

| 指标 | 看什么 | 异常时的常见原因 |
|---|---|---|
| 成功率 | 分模型、分时段 | 晚高峰通道波动、限流策略差异 |
| P95 耗时 | 与迁移前基线比 | 多一跳转发、跨境段绕路 |
| 账单 / 请求数 | 按日对账 | 重试、失败请求计费、缓存口径不同 |
| `model not found` 次数 | 按 ID 统计 | 型号下架或别名不一致 |

第 3 项最容易出现「明明没换模型，钱却变多了」。多数情况不是平台问题：官方 SDK 的默认重试策略，遇上中转链路略高的超时率，会把请求重发一次，而上游那次已经完整计费。把重试上限、退避和读超时重新按新链路调一遍，通常就回去了。

## 一份回滚预案

迁移最怕的不是出错，是出错时回不去。所以三件套从一开始就放环境变量：

```bash
# 生产
export OPENAI_BASE_URL="https://token173.net/v1"
export OPENAI_API_KEY="sk-生产Key"

# 回滚：改回这一行即可，业务代码不动
# export OPENAI_BASE_URL="https://api.openai.com/v1"
```

再配一张最小健康检查：每十分钟打一次 `/v1/models` 和一条短问答，失败连续三次就告警。真要回滚时，改一行环境变量重启，比临时翻代码找硬编码地址从容得多。

备用平台也建议提前配好同一套环境变量命名。主力通道波动时，「改一行切走」和「临时注册、充值、改代码」是两种完全不同的事故时长。
