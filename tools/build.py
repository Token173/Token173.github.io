#!/usr/bin/env python3
# Token173 静态站构建器：从 content/*.md 生成完整静态站点。
# 用法：python3 tools/build.py
# 可选环境变量：SITE_BASE_URL（换自定义域名后重建 canonical / sitemap）、CONTENT_DIR
import os
import re
import json
import html
import shutil
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
CONTENT = Path(os.environ.get("CONTENT_DIR", str(ROOT / "content")))
BASE = os.environ.get("SITE_BASE_URL", "https://token173.github.io").rstrip("/")
TODAY = os.environ.get("SITE_DATE", date.today().isoformat())
BRAND = "Token173"
SITE_NAME = "Token173 API 中转笔记"
SITE_TAGLINE = "大模型 API 中转、聚合与接入的选型、排错和成本笔记"
DOMAIN = "token173.net"

TOPICS = {
    "selection": ("选型与推荐", "好用的中转站推荐、靠谱的 token 中转站、老牌稳定的大模型聚合平台、2026 中转站横向对比与验收方法", "如何判断一家 API 中转站能不能进生产：判断标准、压测方法、企业采购清单、自建与托管的成本账，以及不同平台的定位差异。"),
    "access": ("国内直连与接入", "AI 中转站推荐、国内直连 GPT 平台、国内直连 Claude 平台、不用代理调用 API、base_url 配置教程", "从概念到跑通：OpenAI 兼容接口迁移、Claude Code 与 Cursor 环境变量、客户端自定义服务商、跨境链路延迟，以及 401 / 404 / 流式断流的排查。"),
    "models": ("模型与型号专题", "GPT 中转平台、Claude 中转平台、Gemini 中转平台、Grok 中转平台、模型列表、生图与视频 API", "按家族整理的型号清单与选型笔记，覆盖文本、图像、视频和国产线；每个专题都带接入踩坑、协议差异与成本口径。"),
    "billing": ("计费与成本", "API 中转站倍率是什么意思、token 扣费对不上、综合单价、余额清零、缓存命中成本", "把中转站的账算明白：倍率与兑换口径、请求级 usage 对账、扣费异常的四类原因、长上下文与缓存命中对成本的影响。"),
    "risk": ("避坑与风险", "中转站会不会跑路、模型降智、掺水、共享密钥池、余额清零、数据留存", "这一层的结构性风险与自查动作：共享密钥池连带封号、模型替换、计费黑盒、预充值敞口和敏感数据边界。"),
    "engineering": ("工程实践", "统一 API 网关、一个 Key 多模型、Agent 多模型调度、流式输出、异步任务、压测", "面向真实项目的工程笔记：聚合层四道工序、降级链与路由策略、视频任务状态机、多模态流水线、调用链排查。"),
}

MODELS = {
    "Claude 系": ["claude-opus-5-5", "claude-opus-4-8", "claude-sonnet-5-5", "claude-haiku-5-5", "claude-fable-5", "claude-fable-5-1"],
    "GPT 系": ["gpt-6.1-sol", "gpt-6-sol", "gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.5", "gpt-5.4", "gpt-image-2", "gpt-image-2-d"],
    "Gemini / Grok": ["gemini-3.8-flash", "grok-4.7", "grok-4.5"],
    "国产线": ["glm-5.3-flash", "deepseek-v4", "deepseek-v4-pro-0813", "deepseek-v4-flash-0731", "kimi-k3", "minimax-h3"],
    "视觉生成": ["doubao-seedance-2-0-fast-260128", "sd-2-5-480p"],
}

# no, slug, seo_title, description, primary_kw, extra_kws, topic, extra_related
META = [
(1,"best-api-relay-2026","2026 好用的 API 中转站推荐：稳定靠谱实测对比","换了七八家之后总结的 API 中转站验收标准与横向对比，含踩坑经过、48 小时压测动作、主流平台定位和 2026 年行业背景。","好用的API中转站推荐",["稳定靠谱好用中转站推荐","2026中转站推荐","API中转站横评"],"selection",[2,17,4]),
(2,"token-relay-trust-checklist","靠谱的 token 中转站推荐：五条自检标准","不靠口碑判断中转站靠不靠谱：请求级日志、倍率与兑换口径、小额起充、运营主体、状态页，附一次真实筛选记录和风险自查表。","靠谱的token中转站推荐",["中转站会不会跑路","API中转站怎么判断","稳定中转站"],"risk",[14,15,4]),
(3,"ai-api-proxy-china-direct","AI 中转站推荐：国内直连 GPT 和 Claude 不用代理","讲清「国内直连」是 API 层而非网页版，三件套配置、最小 curl 验证、不用代理的三种误解，以及超时这个第四字段。","AI中转站推荐",["国内直连GPT平台","国内直连Claude平台","不用梯子调用API"],"access",[11,12,25]),
(4,"llm-api-aggregator-longrun","老牌稳定的大模型 API 聚合平台：怎么自己验证","「老牌」「稳定」「用户量大」都可以查：域名与备案、更新日志、社区痕迹、压测数据、投放软文识别，附 2026 年行业判断。","老牌稳定的大模型API聚合平台",["用户量大的中转站","专业靠谱中转聚合平台","中转站怎么验证"],"selection",[2,17,1]),
(5,"one-key-multi-model-api","第三方 API 巨模平台：一个 Key 调用多模型","聚合层实际做的四件事——鉴权、协议适配、调度、计量；附多模态流水线配置示例与调度、计费两道工序的拆解。","第三方API巨模平台",["大模型聚合平台","一个Key调用多模型","统一API网关"],"engineering",[28,19,21]),
(6,"overseas-llm-relay-latency","海外模型中转平台：跨境链路延迟怎么测","把一次请求拆成四段计时，TTFT / P95 / 静默降速的测法、故障注入、记录表模板，以及 2026 年链路环境的变化。","海外模型中转平台",["GPT API 延迟","跨境专线","首字延迟TTFT"],"access",[17,24,3]),
(7,"gpt-api-relay-models","GPT 中转平台：gpt-6-sol 与 gpt-5.6-terra 怎么选","按轻中重三档绑型号，用综合单价而非折扣横比；附 2026 年型号命名规则、A/B 记录模板和默认旗舰习惯的成本账。","GPT中转平台",["gpt-6-sol调用","gpt-5.6-terra对比","GPT API国内直连"],"models",[19,27,8]),
(8,"claude-api-relay-models","Claude 中转平台：长任务翻车复盘与型号配置","一次超时重发导致的缓存失效复盘，claude-opus-5-5 / sonnet-5-5 / haiku-5-5 分档、缓存命中率算法与长任务参数清单。","Claude中转平台",["claude-opus-5-5","Claude长任务断流","Claude Code中转"],"models",[27,11,19]),
(9,"gemini-api-relay-china","Gemini 中转平台：gemini-3.8-flash 国内调用","多模态上传慢在哪、长上下文被截断的四类原因、协议差异、finish_reason 对照表与体积账。","Gemini中转平台",["gemini-3.8-flash","Gemini API国内","多模态上传超时"],"models",[20,21,19]),
(10,"grok-api-relay-notes","Grok 中转平台：grok-4.7 和 grok-4.5 接入记录","按天记录的接入日志：404、SSE 解析、账单异常、并发压测、/v1/models 校验脚本，附可复用的记录模板。","grok中转平台",["grok-4.7接入","Grok API国内","model not found"],"models",[29,19,7]),
(11,"claude-code-third-party-api","国内直连 Claude：Claude Code 配置第三方 API 教程","ANTHROPIC_BASE_URL / AUTH_TOKEN / MODEL 三个变量，settings.json、VS Code 扩展、curl 最小验证与报错速查表。","国内直连Claude平台",["Claude Code第三方API","ANTHROPIC_BASE_URL","Claude API配置"],"access",[25,8,29]),
(12,"openai-compatible-migration","国内直连 GPT：OpenAI 兼容接口迁移只改两处","Python / Node / curl 迁移示例、七步验证清单、兼容性边界、第一周监控指标与一份回滚预案。","国内直连GPT平台",["OpenAI兼容接口","base_url替换","API迁移教程"],"access",[3,25,6]),
(13,"api-relay-pricing-ratio","API 中转站倍率是什么意思：计费口径与对账","两层换算拆开讲，倍率按方向 / 模型 / 分组 / 时段的差异、综合单价公式、四类搜索意图与可填的比价工作表。","API中转站倍率",["中转站0.2倍率","token扣费怎么算","中转站价格对比"],"billing",[16,27,15]),
(14,"api-relay-pitfalls","AI 中转站避坑：模型降智、掺水与共享密钥池","按层拆解共享密钥池连带封号、模型替换与 IDE 反代污染、计费黑盒、数据经过第三方，附 2026 年背景与风险自查表。","AI中转站避坑",["模型降智","纯血原版","共享密钥池","中转站风险"],"risk",[2,15,16]),
(15,"token-relay-balance-risk","Token 中转站余额清零与跑路风险：小额试跑清单","预充值结构的五类资金损失方式、五条资金纪律、小额试跑清单，以及 2026 双十一囤 Token 的三个坑与资金敞口表。","token中转站跑路",["余额清零","中转站退款","囤token划算吗"],"risk",[2,14,13]),
(16,"token-billing-reconcile","API 中转站 Token 扣费对不上：四类原因排查","从一条 request_id 开始，按正常消耗漏算、协议口径、网关 bug、真实动手脚四层排查，附 5 分钟顺序表与换平台信号。","token扣费对不上",["中转站偷量","账单对不上","usage字段"],"billing",[13,27,29]),
(17,"api-relay-benchmark","稳定好用的中转站怎么压测：TTFT 与 P95 延迟","六个可观测指标、五组真实样本、白天与晚高峰时间窗、并发阶梯、故障注入、记录表模板与上线硬线。","稳定好用的中转站",["中转站压测","P95延迟","流式中断率"],"selection",[6,1,4]),
(18,"enterprise-llm-gateway-checklist","企业选大模型 API 中转站：发票、对公与子账号清单","财务 / 法务 / 运维三组视角、九项采购验收表、按真实业务跑的技术验证、费用口径写进合同，以及托管中转的结构性边界。","企业级API中转站",["中转站开发票","对公结算","子账号管理"],"selection",[2,23,4]),
(19,"llm-relay-model-list-2026","AI 中转站支持哪些模型：2026 型号 ID 整理","26 个型号按 Claude / GPT / Gemini / Grok / 国产 / 视觉分组，附命名规则、/v1/models 校验脚本与最小验证组。","AI中转站模型列表",["中转站支持哪些模型","gpt-6-sol","claude-opus-5-5"],"models",[7,8,20]),
(20,"gpt-image-2-api-relay","gpt-image-2 生图 API 中转：调用与批量跑","图像端点与文本端点差异、按次计费口径、上传体积、超时重试、结果落地、批量前检查清单与排错表。","gpt-image-2 API",["gpt-image-2-d","生图API中转","GPT图像生成国内直连"],"models",[21,19,9]),
(21,"seedance-video-api-relay","Seedance 视频生成 API 中转：异步任务与轮询","提交—轮询—转存的任务状态机、幂等提交、指数退避、临时 URL、按次计费，附可复用代码骨架与上线检查清单。","Seedance视频生成API",["doubao-seedance-fast","视频模型中转","异步任务轮询"],"models",[20,19,5]),
(22,"domestic-llm-api-aggregator","国产模型中转 API：DeepSeek、GLM、Kimi、MiniMax 混合调度","按任务分档的降级链、升级触发条件、缓存与峰谷计价、跨家族兜底，以及带日期后缀型号 ID 的实测细节。","国产模型中转API",["DeepSeek API聚合","GLM Kimi MiniMax","一个Key多家模型"],"models",[19,28,27]),
(23,"selfhost-vs-managed-gateway","自建 One API 还是托管中转站：隐性成本对比","七项长期运维成本、适合自建的五个条件、BYOK 第三条路、半年期实际开销对照与重新评估的信号。","自建One-API还是中转站",["New API自建","API网关成本","BYOK调度"],"selection",[18,5,24]),
(24,"openrouter-vs-cn-relay","OpenRouter 和国内中转平台怎么选","型号覆盖、国内链路、支付结算、企业流程四条线的差异，双栈环境变量配置、评测与生产账单分开归集。","OpenRouter国内替代",["OpenRouter对比","海外模型中转平台","国内直连GPT"],"selection",[6,3,23]),
(25,"coding-tools-api-relay","Claude Code 与 Cursor 接入中转 API：环境变量配置","Anthropic 与 OpenAI 兼容两种协议入口、settings.json、VS Code 扩展、cc-switch 本地路由、报错速查与长任务参数。","Claude Code中转API",["Cursor自定义模型","AI编程中转站","ANTHROPIC_BASE_URL"],"access",[11,27,29]),
(26,"chat-client-custom-provider","Cherry Studio 和 Chatbox 自定义服务商配置","三件套字段、模型列表为空的处理、给非开发同事的一页配置说明、部门 Key 台账与管理员冒烟测试。","Cherry Studio自定义服务商",["Chatbox填API地址","中转Key配置","团队共用API"],"access",[12,18,29]),
(27,"coding-relay-cache-cost","AI 编程中转站：长上下文缓存命中与成本","编程场景输入占比为何远大于输出、缓存命中率算法、五次成本复盘、会话粘性与长连接稳定性要求。","AI编程中转站推荐",["Claude Code缓存命中","编程模型成本","Cline中转"],"billing",[8,16,25]),
(28,"agent-multi-model-routing","AI Agent 工作流多模型调度：统一 API 网关实践","网关层四件事、成本 / 性能 / 稳定三种路由策略、分层结构图、按步骤打标签的记账方式与兜底清单。","Agent多模型调度",["统一API网关","多模型路由","工作流降级"],"engineering",[5,22,21]),
(29,"api-relay-faq-troubleshooting","API 中转站 FAQ：401、404、流式断流排查","按现象组织的速查：认证失败、model not found、模型列表为空、Base URL、断流、超时重试、402、429、账单差异。","API中转站报错排查",["401 invalid api key","model not found","流式输出断掉"],"engineering",[10,16,25]),
(30,"indie-dev-llm-api-starter","个人开发者低成本调用大模型 API：小额试用路线","三条免费 / 自建 / 聚合路线对比、六步上手、免费额度四条纪律、不碰无限套餐与充值赠送的理由。","个人开发者大模型API",["免费大模型API","学生党GPT API","小额试用中转站"],"selection",[2,15,19]),
]
META_BY_NO = {m[0]: m for m in META}


def esc(s):
    return html.escape(s, quote=False)


def inline(s):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def is_table_sep(line):
    return bool(re.match(r"^\s*\|?[\s:\-\|]+\|[\s:\-\|]*$", line)) and "-" in line


def md_to_html(text):
    """够用的 Markdown 子集解析器：标题/引用/列表/表格/代码块/水平线/段落。"""
    lines = text.splitlines()
    out, toc, i = [], [], 0
    sec = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            lang = line[3:].strip()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            cls = ' class="language-%s"' % esc(lang) if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, esc("\n".join(buf))))
            continue
        if not line.strip():
            i += 1; continue
        if re.match(r"^\s*---+\s*$", line):
            out.append("<hr>"); i += 1; continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1)); txt = m.group(2).strip()
            if lvl == 1:
                i += 1; continue  # H1 由模板统一输出
            sec += 1
            anchor = "sec-%d" % sec
            out.append('<h%d id="%s">%s</h%d>' % (min(lvl, 4), anchor, inline(txt), min(lvl, 4)))
            if lvl == 2:
                toc.append((anchor, re.sub(r"<[^>]+>", "", inline(txt))))
            i += 1; continue
        if line.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:]); i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(buf)))
            continue
        if line.startswith("|") and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            th = "".join("<th>%s</th>" % inline(c) for c in head)
            tb = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in rows)
            out.append('<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, tb))
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            tag = "ol" if ordered else "ul"
            buf = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                buf.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i])); i += 1
            items = "".join("<li>%s</li>" % inline(x) for x in buf)
            # 任务清单
            items = items.replace("<li>[ ] ", '<li class="task">').replace("<li>[x] ", '<li class="task done">')
            out.append("<%s>%s</%s>" % (tag, items, tag))
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|```|\s*---+\s*$|>\s|\|)", lines[i]) \
                and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
            buf.append(lines[i].strip()); i += 1
        if buf:
            out.append("<p>%s</p>" % inline(" ".join(buf)))
        else:
            i += 1
    return "\n".join(out), toc


def jsonld(obj):
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def shell(*, title, seo_title, desc, kws, body, canonical, breadcrumbs, extra_head="", page_type="website"):
    bc_html = "".join(
        '<li><a href="%s">%s</a></li>' % (u, esc(t)) if u else '<li aria-current="page">%s</li>' % esc(t)
        for t, u in breadcrumbs
    )
    bc_ld = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": n + 1, "name": t,
                             "item": BASE + u if u else BASE + canonical} for n, (t, u) in enumerate(breadcrumbs)],
    }
    org = {"@context": "https://schema.org", "@type": "Organization",
           "name": BRAND, "url": "https://" + DOMAIN + "/"}
    search_ld = "" if page_type != "home" else jsonld({
        "@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": BASE + "/",
        "potentialAction": {"@type": "SearchAction", "target": BASE + "/?q={search_term_string}",
                            "query-input": "required name=search_term_string"},
    })
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{seo_title}</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{kws}">
<meta name="author" content="{brand}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{base}{canonical}">
<meta property="og:type" content="{ogtype}">
<meta property="og:site_name" content="{site_name}">
<meta property="og:title" content="{seo_title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{base}{canonical}">
<meta property="og:locale" content="zh_CN">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{seo_title}">
<meta name="twitter:description" content="{desc}">
<link rel="stylesheet" href="/assets/style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2316509b'/%3E%3Ctext x='16' y='22' font-size='17' font-family='sans-serif' font-weight='700' fill='white' text-anchor='middle'%3ET%3C/text%3E%3C/svg%3E">
{extra_head}{ld}{search_ld}
</head>
<body>
<a class="skip" href="#main">跳到正文</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/"><span class="brand-mark">T</span><span>{brand}</span><em>API 中转笔记</em></a>
    <nav class="nav" aria-label="主导航">
      <a href="/">首页</a>
      <a href="/topics/">分类</a>
      <a href="/models/">型号</a>
      <a href="/faq/">FAQ</a>
      <a href="/about/">关于</a>
    </nav>
    <form class="search" role="search" onsubmit="return false">
      <input id="q" type="search" placeholder="搜索教程、型号、报错…" autocomplete="off" aria-label="站内搜索">
      <div id="search-results" class="search-results" hidden></div>
    </form>
  </div>
</header>
<nav class="wrap breadcrumbs" aria-label="面包屑"><ol>{bc_html}</ol></nav>
<main id="main" class="wrap">{body}</main>
<footer class="site-footer">
  <div class="wrap footer-inner">
    <div><strong>{brand}</strong> · {site_tagline}</div>
    <nav aria-label="页脚导航">
      <a href="/topics/">分类</a><a href="/models/">型号索引</a><a href="/faq/">常见问题</a>
      <a href="/about/">关于本站</a><a href="/sitemap.xml">站点地图</a>
    </nav>
    <p class="disclaimer">本站为技术笔记，内容按公开资料与实际接入经验整理。模型型号、价格与平台规则会调整，请以各平台控制台当前公示为准。使用第三方接口服务请自行评估数据与资金风险。</p>
  </div>
</footer>
<script src="/assets/app.js" defer></script>
</body>
</html>""".format(
        seo_title=esc(seo_title), desc=esc(desc), kws=esc(kws), brand=BRAND,
        site_name=esc(SITE_NAME), site_tagline=esc(SITE_TAGLINE), base=BASE,
        canonical=canonical, ogtype="article" if page_type == "article" else "website",
        extra_head=extra_head, ld=jsonld(bc_ld) + jsonld(org), search_ld=search_ld,
        bc_html=bc_html, body=body,
    )


def article_card(no, compact=False):
    m = META_BY_NO[no]
    kw = m[4]
    return ('<article class="card"><a class="card-title" href="/articles/{slug}/">{title}</a>'
            '<p class="card-desc">{desc}</p><div class="card-meta"><span class="tag">{topic}</span>'
            '<span class="kw">{kw}</span></div></article>').format(
        slug=m[1], title=esc(m[2]), desc=esc(m[3][:88]),
        topic=esc(TOPICS[m[6]][0]), kw=esc(kw))


def write(relpath, content):
    p = ROOT / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


CSS = r"""/* Token173 静态站 · 无外部依赖 */
:root{
  --brand:#16509b; --brand-dark:#0e3a73; --brand-soft:#eef4fc;
  --accent:#c2410c; --ink:#1a1d21; --muted:#5b6572; --line:#e3e7ed;
  --bg:#ffffff; --bg-soft:#f7f9fb; --code:#f4f6f8;
  --radius:10px; --wrap:1120px;
  --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.75 var(--sans);letter-spacing:.01em}
a{color:var(--brand);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:var(--wrap);margin:0 auto;padding:0 24px}
.skip{position:absolute;left:-9999px}
.skip:focus{left:12px;top:12px;background:#fff;padding:8px 14px;z-index:99;border-radius:6px}
.site-header{border-bottom:1px solid var(--line);background:rgba(255,255,255,.96);position:sticky;top:0;z-index:20;backdrop-filter:blur(8px)}
.header-inner{display:flex;align-items:center;gap:28px;min-height:64px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:9px;font-weight:700;font-size:18px;color:var(--ink);white-space:nowrap}
.brand:hover{text-decoration:none}
.brand-mark{display:grid;place-items:center;width:28px;height:28px;border-radius:7px;background:var(--brand);color:#fff;font-size:16px;font-weight:800}
.brand em{font-style:normal;font-weight:400;font-size:13px;color:var(--muted);border-left:1px solid var(--line);padding-left:10px}
.nav{display:flex;gap:20px;font-size:14px;flex:1}
.nav a{color:var(--muted)}
.nav a:hover{color:var(--brand)}
.search{position:relative;width:230px}
.search input{width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:8px;font:14px var(--sans);background:var(--bg-soft);outline:none}
.search input:focus{border-color:var(--brand);background:#fff;box-shadow:0 0 0 3px var(--brand-soft)}
.search-results{position:absolute;top:42px;right:0;width:360px;max-height:420px;overflow:auto;background:#fff;border:1px solid var(--line);border-radius:var(--radius);box-shadow:0 12px 34px rgba(20,35,60,.13);padding:8px;z-index:30}
.search-results a{display:block;padding:9px 10px;border-radius:6px;color:var(--ink);font-size:14px;line-height:1.5}
.search-results a:hover{background:var(--brand-soft);text-decoration:none}
.search-results small{display:block;color:var(--muted);font-size:12px}
.search-results .empty{padding:14px;color:var(--muted);font-size:13px}
.breadcrumbs{padding-top:18px;font-size:13px;color:var(--muted)}
.breadcrumbs ol{display:flex;flex-wrap:wrap;gap:8px;list-style:none;margin:0;padding:0}
.breadcrumbs li+li:before{content:"/";margin-right:8px;color:#b9c1cb}
main{padding-top:26px;padding-bottom:64px;min-height:60vh}
.hero{padding:36px 0 30px;border-bottom:1px solid var(--line);margin-bottom:34px}
.hero h1{font-size:34px;line-height:1.35;margin:0 0 14px;letter-spacing:-.01em}
.hero p{font-size:17px;color:var(--muted);max-width:760px;margin:0 0 18px}
.hero-kws{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
.pill{background:var(--brand-soft);color:var(--brand-dark);border-radius:999px;padding:5px 13px;font-size:13px}
h1{font-size:30px;line-height:1.4;margin:0 0 18px}
h2{font-size:22px;margin:38px 0 14px;padding-bottom:9px;border-bottom:1px solid var(--line);scroll-margin-top:86px}
h3{font-size:18px;margin:26px 0 10px;scroll-margin-top:86px}
h4{font-size:16px;margin:20px 0 8px}
p{margin:0 0 15px}
blockquote{margin:0 0 20px;padding:14px 18px;background:var(--brand-soft);border-left:3px solid var(--brand);border-radius:0 var(--radius) var(--radius) 0;color:#2c405c;font-size:14.5px;line-height:1.75}
blockquote p{margin:0}
ul,ol{margin:0 0 18px;padding-left:24px}
li{margin:5px 0}
li.task{list-style:none;margin-left:-20px}
li.task:before{content:"☐ ";color:var(--muted)}
li.task.done:before{content:"☑ ";color:var(--brand)}
code{font-family:var(--mono);font-size:.88em;background:var(--code);padding:2px 5px;border-radius:4px;color:#a3305c}
pre{background:#1e2530;color:#e6edf3;padding:18px 20px;border-radius:var(--radius);overflow-x:auto;font:13px/1.7 var(--mono);margin:0 0 22px}
pre code{background:none;color:inherit;padding:0;font-size:inherit}
hr{border:0;border-top:1px solid var(--line);margin:32px 0}
.table-wrap{overflow-x:auto;margin:0 0 22px;border:1px solid var(--line);border-radius:var(--radius)}
table{border-collapse:collapse;width:100%;font-size:14px;min-width:520px}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--bg-soft);font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:0}
.article-layout{display:grid;grid-template-columns:minmax(0,1fr) 232px;gap:46px;align-items:start}
.article-body{min-width:0;font-size:15.5px}
.article-lead{font-size:16.5px;color:#3b4654;background:var(--bg-soft);border-radius:var(--radius);padding:18px 20px;margin-bottom:26px}
.toc{position:sticky;top:86px;font-size:13.5px;border-left:1px solid var(--line);padding-left:16px;max-height:calc(100vh - 110px);overflow:auto}
.toc strong{display:block;font-size:12px;letter-spacing:.08em;color:var(--muted);margin-bottom:10px;text-transform:uppercase}
.toc a{display:block;color:var(--muted);padding:4px 0;line-height:1.5}
.toc a:hover{color:var(--brand)}
.meta-line{display:flex;flex-wrap:wrap;gap:10px;align-items:center;font-size:13px;color:var(--muted);margin-bottom:22px}
.tag{background:var(--brand-soft);color:var(--brand-dark);border-radius:5px;padding:2px 9px;font-size:12px}
.dot{color:#c3cad3}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;margin:0 0 30px}
.card{display:block;border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px;background:#fff;transition:border-color .15s,box-shadow .15s}
.card:hover{border-color:#b7cbe8;box-shadow:0 6px 20px rgba(22,80,155,.07);text-decoration:none}
.card-title{display:block;font-weight:650;font-size:16px;line-height:1.5;color:var(--ink);margin-bottom:8px}
.card:hover .card-title{color:var(--brand)}
.card-desc{color:var(--muted);font-size:13.5px;line-height:1.65;margin:0 0 12px}
.card-meta{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.kw{color:#8b96a3}
.section{margin:40px 0}
.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:14px;margin-bottom:14px;flex-wrap:wrap}
.section-head h2{margin:0;border:0;padding:0;font-size:21px}
.section-head a{font-size:13.5px}
.section-desc{color:var(--muted);font-size:14px;margin:0 0 16px}
.topic-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-bottom:38px}
.topic-card{border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px}
.topic-card h3{margin:0 0 8px;font-size:17px}
.topic-card h3 a{color:var(--ink)}
.topic-card h3 a:hover{color:var(--brand)}
.topic-card p{font-size:13.5px;color:var(--muted);margin:0 0 12px;line-height:1.65}
.count{font-size:12px;color:var(--muted)}
.model-group{margin:0 0 30px}
.model-group h2{margin-top:24px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.chips code{background:var(--bg-soft);border:1px solid var(--line);color:var(--brand-dark);padding:6px 11px;font-size:13px;border-radius:6px}
.related{border-top:1px solid var(--line);margin-top:44px;padding-top:26px}
.related h2{margin-top:0;border:0;padding:0;font-size:19px}
.cta{background:var(--brand-soft);border:1px solid #d5e4f8;border-radius:var(--radius);padding:20px 22px;margin:34px 0 0;font-size:14.5px}
.cta strong{color:var(--brand-dark)}
.site-footer{border-top:1px solid var(--line);background:var(--bg-soft);padding:30px 0 38px;font-size:13.5px;color:var(--muted)}
.footer-inner nav{display:flex;flex-wrap:wrap;gap:16px;margin:12px 0}
.disclaimer{font-size:12.5px;line-height:1.75;max-width:860px;margin:14px 0 0;color:#7a8592}
.faq-item{border-bottom:1px solid var(--line);padding:16px 0}
.faq-item h3{margin:0 0 8px;font-size:16.5px}
.faq-item p{margin:0;color:#3d4753;font-size:14.5px}
.notfound{text-align:center;padding:80px 0}
@media(max-width:900px){
  .article-layout{grid-template-columns:1fr;gap:0}
  .toc{position:static;max-height:none;border-left:0;border:1px solid var(--line);border-radius:var(--radius);padding:14px 18px;margin-bottom:26px}
  .nav{order:3;width:100%;flex:none;overflow-x:auto;padding-bottom:10px}
  .search{width:180px;margin-left:auto}
  .hero h1{font-size:27px}
  h1{font-size:25px}
}
@media(max-width:560px){
  .wrap{padding:0 16px}
  .brand em{display:none}
  .search{width:100%;order:4;margin:0 0 10px}
  .search-results{width:100%;left:0;right:auto}
  .hero{padding:22px 0}
  .hero h1{font-size:23px}
  .grid,.topic-grid{grid-template-columns:1fr}
  pre{font-size:12px;padding:14px}
}
"""

JS = r"""/* 纯前端站内搜索，无外部依赖 */
(function(){
  var input=document.getElementById('q'), box=document.getElementById('search-results'), idx=null;
  if(!input||!box) return;
  function load(){
    if(idx) return Promise.resolve(idx);
    return fetch('/assets/search-index.json').then(function(r){return r.json()}).then(function(d){idx=d;return d});
  }
  function render(q){
    load().then(function(items){
      var terms=q.toLowerCase().split(/\s+/).filter(Boolean);
      var hits=items.filter(function(it){
        var hay=(it.t+' '+it.d+' '+it.k+' '+it.c).toLowerCase();
        return terms.every(function(t){return hay.indexOf(t)>-1});
      }).slice(0,12);
      if(!hits.length){box.innerHTML='<div class="empty">没有匹配的内容，试试「倍率」「Claude Code」「model not found」</div>';return}
      box.innerHTML=hits.map(function(it){
        return '<a href="'+it.u+'">'+it.t+'<small>'+it.c+' · '+it.d.slice(0,46)+'</small></a>';
      }).join('');
    }).catch(function(){box.innerHTML='<div class="empty">索引加载失败</div>'});
  }
  var timer;
  input.addEventListener('input',function(){
    var q=this.value.trim(); clearTimeout(timer);
    if(!q){box.hidden=true;return}
    box.hidden=false;
    timer=setTimeout(function(){render(q)},120);
  });
  document.addEventListener('click',function(e){if(!e.target.closest('.search')) box.hidden=true});
  input.addEventListener('focus',function(){if(this.value.trim()) box.hidden=false});
  var params=new URLSearchParams(location.search).get('q');
  if(params){input.value=params;box.hidden=false;render(params)}
})();
"""


def main():
    # 载入源文
    src_root = Path(os.environ.get("ARTICLES_DIR", str(Path(__file__).resolve().parent.parent.parent / "token173-articles")))
    docs = {}
    for no, slug, *_ in META:
        d = src_root / ("%02d-" % no)
        if not d.exists():
            cand = list(src_root.glob("%02d-*" % no))
            d = cand[0] if cand else None
        p = (d / "readme.md") if d else None
        if not p or not p.exists():
            raise SystemExit("缺少源文件: %02d" % no)
        docs[no] = p.read_text(encoding="utf-8")
        # 同步源文到仓库，便于复现构建
        write("content/%02d-%s.md" % (no, slug), docs[no])

    # 清理旧产物
    for d in ["articles", "topics"]:
        shutil.rmtree(ROOT / d, ignore_errors=True)
    write("assets/style.css", CSS)
    write("assets/app.js", JS)
    write(".nojekyll", "")
    write(".gitignore", "*.pyc\n__pycache__/\n.DS_Store\n")
    write("CNAME.example", "docs.token173.net\n")

    search_index, sitemap = [], []

    # ---- 文章页 ----
    for no, slug, seo_title, desc, kw, extras, topic, extra_related in META:
        raw = docs[no]
        h1 = re.search(r"^#\s+(.*)$", raw, re.M).group(1).strip()
        body_html, toc = md_to_html(raw)
        # 引言段单独提出来做 lead
        lead = ""
        lm = re.search(r"^>\s+(.*)$", raw, re.M)
        if lm:
            lead = '<div class="article-lead">%s</div>' % inline(lm.group(1))
            body_html = re.sub(r"<blockquote>.*?</blockquote>", "", body_html, count=1, flags=re.S)
        related = []
        for r in list(extra_related) + [x[0] for x in META if x[6] == topic and x[0] != no]:
            if r != no and r not in related and r in META_BY_NO:
                related.append(r)
            if len(related) >= 6: break
        toc_html = "".join('<a href="#%s">%s</a>' % (a, t) for a, t in toc)
        art_ld = {
            "@context": "https://schema.org", "@type": "BlogPosting",
            "headline": h1, "description": desc,
            "datePublished": TODAY, "dateModified": TODAY,
            "inLanguage": "zh-CN", "keywords": ", ".join([kw] + list(extras)),
            "author": {"@type": "Organization", "name": BRAND},
            "publisher": {"@type": "Organization", "name": BRAND, "url": "https://" + DOMAIN + "/"},
            "mainEntityOfPage": {"@type": "WebPage", "@id": BASE + "/articles/" + slug + "/"},
            "articleSection": TOPICS[topic][0],
        }
        # 含 Q&A 的页面补 FAQPage
        qa = re.findall(r"^###\s+Q[：:]\s*(.+)$", raw, re.M)
        if len(qa) >= 3:
            art_ld = [art_ld, {"@context": "https://schema.org", "@type": "FAQPage",
                               "mainEntity": [{"@type": "Question", "name": q,
                                               "acceptedAnswer": {"@type": "Answer", "text": "见正文对应小节"}} for q in qa[:12]]}]
        body = """<div class="article-layout">
<div class="article-body">
<h1>{h1}</h1>
<div class="meta-line"><span class="tag">{topic}</span><span>{date}</span><span class="dot">·</span><span>{kw}</span></div>
{lead}
{content}
<div class="cta"><strong>继续看：</strong><a href="/topics/{topic}/">{tname}</a> ·
<a href="/models/">型号 ID 清单</a> · <a href="/faq/">报错速查</a>。
型号与价格会调整，接入前以平台控制台当前列表为准。</div>
<section class="related"><h2>相关文章</h2><div class="grid">{related}</div></section>
</div>
<aside class="toc"><strong>本文目录</strong>{toc}</aside>
</div>""".format(h1=esc(h1), topic=esc(topic), date=TODAY, kw=esc(kw),
                 tname=esc(TOPICS[topic][0]), lead=lead, content=body_html,
                 related="".join(article_card(r) for r in related), toc=toc_html)
        canonical = "/articles/%s/" % slug
        write("articles/%s/index.html" % slug, shell(
            title=h1, seo_title=seo_title, desc=desc,
            kws=", ".join([kw] + list(extras) + ["Token173", "token173.net"]),
            body=body, canonical=canonical, page_type="article",
            breadcrumbs=[("首页", "/"), (TOPICS[topic][0], "/topics/%s/" % topic), (h1, "")],
            extra_head=jsonld(art_ld)))
        search_index.append({"t": seo_title, "d": desc, "u": canonical,
                             "k": " ".join([kw] + list(extras)), "c": TOPICS[topic][0]})
        sitemap.append(canonical)

    # ---- 分类页 ----
    for key, (name, kws, desc) in TOPICS.items():
        nos = [m[0] for m in META if m[6] == key]
        body = """<h1>{name} · {count} 篇</h1>
<p class="section-desc">{desc}</p>
<div class="hero-kws">{pills}</div>
<div class="section"><div class="grid">{cards}</div></div>""".format(
            name=esc(name), count=len(nos), desc=esc(desc),
            pills="".join('<span class="pill">%s</span>' % esc(k.strip()) for k in kws.split("、")),
            cards="".join(article_card(n) for n in nos))
        canonical = "/topics/%s/" % key
        write("topics/%s/index.html" % key, shell(
            title=name, seo_title="%s｜API 中转教程与选型笔记 - Token173" % name,
            desc=desc[:150], kws=kws.replace("、", ",") + ",Token173",
            body=body, canonical=canonical,
            breadcrumbs=[("首页", "/"), ("分类", "/topics/"), (name, "")]))
        sitemap.append(canonical)
        search_index.append({"t": name + " 分类", "d": desc, "u": canonical, "k": kws, "c": "分类"})

    topics_body = "<h1>全部分类</h1><p class=\"section-desc\">按搜索意图归类的六组内容，每组围绕一组长尾词展开。</p><div class=\"topic-grid\">"
    for key, (name, kws, desc) in TOPICS.items():
        n = len([m for m in META if m[6] == key])
        topics_body += ('<div class="topic-card"><h3><a href="/topics/{k}/">{name}</a></h3>'
                        '<p>{desc}</p><span class="count">{n} 篇 · {kws}</span></div>').format(
            k=key, name=esc(name), desc=esc(desc[:110]), n=n, kws=esc(kws.split("、")[0]))
    topics_body += "</div>"
    write("topics/index.html", shell(
        title="分类", seo_title="API 中转教程分类｜选型、接入、型号、计费、避坑 - Token173",
        desc="按搜索意图整理的六组 API 中转内容：选型与推荐、国内直连与接入、模型与型号专题、计费与成本、避坑与风险、工程实践。",
        kws="API中转教程,中转站分类,大模型API选型,Token173",
        body=topics_body, canonical="/topics/",
        breadcrumbs=[("首页", "/"), ("分类", "")]))
    sitemap.append("/topics/")

    # ---- 型号页 ----
    model_links = {7: "GPT", 8: "Claude", 9: "Gemini", 10: "Grok", 20: "生图", 21: "视频", 22: "国产"}
    mb = ['<h1>2026 中转站模型 ID 索引</h1>',
          '<p class="section-desc">按家族整理的 26 个型号 ID。聚合平台的模型名是平台自维护的别名，'
          '不必然等于厂商官方版本号；每次上线前用 <code>/v1/models</code> 拉一次当前列表，别照抄任何教程。</p>',
          '<div class="cta"><strong>校验脚本：</strong><code>curl -sS "https://token173.net/v1/models" -H "Authorization: Bearer $RELAY_API_KEY"</code></div>']
    for group, ids in MODELS.items():
        mb.append('<section class="model-group"><h2>%s</h2><div class="chips">%s</div>' % (
            esc(group), "".join("<code>%s</code>" % esc(i) for i in ids)))
        mb.append('<p class="section-desc">相关专题：%s</p></section>' % " · ".join(
            '<a href="/articles/%s/">%s</a>' % (META_BY_NO[n][1], esc(t)) for n, t in
            [(19, "完整型号清单"), (7, "GPT 中转"), (8, "Claude 中转"), (9, "Gemini 中转"),
             (10, "Grok 中转"), (20, "生图 API"), (21, "视频 API"), (22, "国产模型")][:4]))
    mb.append('<section class="related"><h2>从型号继续看</h2><div class="grid">%s</div></section>' %
              "".join(article_card(n) for n in [19, 7, 8, 9, 10, 20, 21, 22]))
    write("models/index.html", shell(
        title="模型 ID 索引",
        seo_title="AI 中转站支持哪些模型｜2026 型号 ID 清单 - Token173",
        desc="26 个中转站模型 ID 按 Claude、GPT、Gemini、Grok、国产线、视觉生成分组整理，附命名规则与 /v1/models 校验方法。",
        kws="中转站模型列表,claude-opus-5-5,gpt-6-sol,gemini-3.8-flash,grok-4.7,gpt-image-2,Token173",
        body="\n".join(mb), canonical="/models/",
        breadcrumbs=[("首页", "/"), ("型号索引", "")]))
    sitemap.append("/models/")
    search_index.append({"t": "2026 中转站模型 ID 索引", "d": "26 个型号按家族分组，含校验脚本",
                         "u": "/models/", "k": " ".join(sum(MODELS.values(), [])), "c": "型号"})

    # ---- FAQ 页 ----
    FAQS = [
        ("API 中转站是什么，和官方 API 有什么区别？",
         "中转站是应用与模型厂商之间的一层网关，负责鉴权、协议适配、路由调度和计量。它不生产模型能力；官方 API 适合直连与强合规场景，中转站解决的是多模型统一接入、国内链路和本地结算。"),
        ("国内直连 GPT / Claude 需要自己配代理吗？",
         "API 层不需要。程序把请求发到境内可直连的地址，由平台转发到上游。注意这不等于能直接打开官方网页版，也不代表链路里没有跨境段。"),
        ("好用的中转站推荐怎么判断，看排行榜靠谱吗？",
         "排行榜大多是投放内容。可自己验的五项：请求级日志、倍率与兑换口径同时公开、支持小额起充、能查到运营主体、有状态页和更新记录。"),
        ("中转站的「倍率」是什么意思？",
         "倍率是平台设定的计费权重，通常还要乘上「1 美元官方标价兑多少平台币」这层换算。只看倍率数字无法横比，要按自己业务的输入输出占比算综合单价。"),
        ("token 扣费对不上，是不是被偷量了？",
         "先排除四类：上下文与系统提示词漏算、协议口径差异、网关流式解析 bug、自己的超时重试。锁定一条 request_id 拆开 usage 字段，五分钟基本能定位。"),
        ("model not found / 404 怎么解决？",
         "聚合平台的模型 ID 是平台自维护的别名，带日期后缀和变体后缀的最容易手打错。从 /v1/models 返回里复制，别照抄教程。"),
        ("Claude Code 怎么接第三方 API？",
         "设 ANTHROPIC_BASE_URL、ANTHROPIC_AUTH_TOKEN、ANTHROPIC_MODEL，并补齐两个 DEFAULT 型号变量，否则后台小任务会去撞不存在的默认 ID。Anthropic 端点别照搬 OpenAI 兼容地址。"),
        ("中转站会不会跑路，余额怎么办？",
         "有这个风险，包括任何一家。按周小额充值、不参加充值赠送、不买长期年卡、留好充值凭证、主力之外留备用通道，是控制敞口最有效的几件事。"),
        ("模型会被掺水或降智吗？",
         "行业里确实存在。用带唯一答案的固定样本定期复测、看后台有没有请求级 usage 和上游路由信息，比凭聊天手感判断可靠得多。"),
        ("可以把公司敏感数据发到中转站吗？",
         "不建议。prompt、上传文件和响应都会完整经过第三方服务器，这是托管中转的结构决定的。敏感业务走官方 API 或可审计、数据责任边界明确的方案。"),
    ]
    fb = ['<h1>常见问题 FAQ</h1>',
          '<p class="section-desc">按真实搜索问法整理，覆盖选型、接入、计费、报错与风险。更完整的 401 / 404 / 流式断流排错见 <a href="/articles/api-relay-faq-troubleshooting/">报错速查</a>。</p>']
    for q, a in FAQS:
        fb.append('<div class="faq-item"><h3>%s</h3><p>%s</p></div>' % (esc(q), esc(a)))
    fb.append('<section class="related"><h2>深入阅读</h2><div class="grid">%s</div></section>' %
              "".join(article_card(n) for n in [1, 2, 3, 13, 16, 29]))
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]}
    write("faq/index.html", shell(
        title="常见问题", seo_title="API 中转站常见问题 FAQ｜选型、接入、计费、报错 - Token173",
        desc="中转站是什么、国内直连要不要代理、倍率怎么算、扣费对不上怎么查、model not found、Claude Code 配置、余额与数据风险，十个高频问题一次讲清。",
        kws="API中转站FAQ,中转站倍率,model not found,Claude Code配置,余额清零,Token173",
        body="\n".join(fb), canonical="/faq/",
        breadcrumbs=[("首页", "/"), ("常见问题", "")], extra_head=jsonld(faq_ld)))
    sitemap.append("/faq/")
    for q, a in FAQS:
        search_index.append({"t": q, "d": a, "u": "/faq/", "k": q, "c": "FAQ"})

    # ---- 关于页 ----
    about = """<h1>关于本站</h1>
<p class="section-desc">一份关于大模型 API 中转、聚合与接入的技术笔记。</p>
<h2>写什么</h2>
<p>选型与验收、国内直连与协议配置、模型型号清单、计费口径与对账、风险边界、多模型调度工程实践。内容按公开资料和实际接入过程整理，带可复现的命令、字段名、报错码和记录表。</p>
<h2>不写什么</h2>
<p>不列无来源的排行榜，不承诺任何平台的稳定性或折扣数字，不代任何平台作资质背书。所有型号 ID、价格与规则都会调整，文中一律以平台控制台当前公示为准。</p>
<h2>风险提示</h2>
<p>第三方 API 中转属于预充值、请求经过第三方服务器的服务形态，存在上游波动、账号风控、数据留存与资金敞口风险。请自行评估，敏感数据不要走公共托管链路，额度按周小额充值。</p>
<h2>站点信息架构</h2>
<div class="table-wrap"><table><thead><tr><th>层级</th><th>承接的搜索意图</th><th>页面</th></tr></thead><tbody>
<tr><td>核心词</td><td>AI 中转站推荐 / API 中转站 / 大模型聚合平台</td><td><a href="/">首页</a></td></tr>
<tr><td>修饰长尾</td><td>好用 / 靠谱 / 稳定 / 老牌 / 国内直连 / 各模型家族</td><td><a href="/topics/">六个分类页</a></td></tr>
<tr><td>问题与教程词</td><td>怎么配 / 怎么查 / 怎么算 / 怎么测</td><td>30 篇教程页</td></tr>
<tr><td>型号词</td><td>具体模型 ID 能不能用、怎么调用</td><td><a href="/models/">型号索引</a></td></tr>
<tr><td>疑问词</td><td>是什么 / 会不会 / 怎么办</td><td><a href="/faq/">FAQ</a></td></tr>
</tbody></table></div>
<p><a href="/sitemap.xml">站点地图</a> · <a href="/topics/">全部分类</a></p>"""
    write("about/index.html", shell(
        title="关于", seo_title="关于本站｜Token173 API 中转笔记",
        desc="本站的内容范围、写作口径、风险提示与 SEO 信息架构说明。",
        kws="关于本站,Token173,API中转笔记", body=about, canonical="/about/",
        breadcrumbs=[("首页", "/"), ("关于", "")]))
    sitemap.append("/about/")

    # ---- 首页 ----
    home = ['<section class="hero">',
            '<h1>大模型 API 中转、聚合与接入的选型笔记</h1>',
            '<p>好用的中转站怎么挑、国内直连 GPT 与 Claude 怎么配、倍率和账单怎么算、流式断流怎么查。30 篇按真实搜索意图组织的技术笔记，带可复现的命令、字段与记录表。</p>',
            '<div class="hero-kws">']
    for k in ["好用的API中转站推荐", "靠谱的token中转站推荐", "AI中转站推荐", "老牌稳定的大模型聚合平台",
              "第三方API巨模平台", "国内直连GPT平台", "国内直连Claude平台", "GPT中转平台",
              "Claude中转平台", "Gemini中转平台", "grok中转平台", "中转站倍率"]:
        home.append('<span class="pill">%s</span>' % esc(k))
    home += ['</div></section>', '<section class="section"><div class="section-head"><h2>按主题浏览</h2><a href="/topics/">全部分类 →</a></div><div class="topic-grid">']
    for key, (name, kws, desc) in TOPICS.items():
        n = len([m for m in META if m[6] == key])
        home.append('<div class="topic-card"><h3><a href="/topics/{k}/">{name}</a></h3><p>{desc}</p><span class="count">{n} 篇</span></div>'.format(
            k=key, name=esc(name), desc=esc(desc[:100]), n=n))
    home += ['</div></section>', '<section class="section"><div class="section-head"><h2>选型与避坑必读</h2><a href="/topics/selection/">更多 →</a></div><div class="grid">']
    home += [article_card(n) for n in [1, 2, 4, 14, 17, 18]]
    home += ['</div></section>', '<section class="section"><div class="section-head"><h2>接入与配置</h2><a href="/topics/access/">更多 →</a></div><div class="grid">']
    home += [article_card(n) for n in [3, 11, 12, 25, 26, 29]]
    home += ['</div></section>', '<section class="section"><div class="section-head"><h2>型号与计费</h2><a href="/models/">型号索引 →</a></div><div class="grid">']
    home += [article_card(n) for n in [19, 7, 8, 13, 16, 27]]
    home += ['</div></section>', '<section class="section"><div class="section-head"><h2>全部 30 篇</h2></div><div class="grid">']
    home += [article_card(m[0], compact=True) for m in META]
    home.append('</section>')
    write("index.html", shell(
        title="首页",
        seo_title="AI 中转站推荐与大模型 API 接入教程｜2026 选型笔记 - Token173",
        desc="好用的 API 中转站推荐、靠谱的 token 中转站怎么判断、国内直连 GPT 与 Claude 配置、模型型号清单、倍率对账与报错排查。30 篇可复现的技术笔记。",
        kws="AI中转站推荐,好用的API中转站推荐,靠谱的token中转站推荐,大模型API聚合平台,国内直连GPT,国内直连Claude,Token173",
        body="\n".join(home), canonical="/", page_type="home",
        breadcrumbs=[("首页", "")]))
    sitemap.append("/")

    # ---- 404 ----
    write("404.html", shell(
        title="页面不存在", seo_title="页面不存在 - Token173",
        desc="页面不存在。", kws="Token173",
        body='<div class="notfound"><h1>404 · 页面不存在</h1><p>链接可能已调整，换个入口继续看。</p>'
             '<p><a href="/">回到首页</a> · <a href="/topics/">按分类浏览</a> · <a href="/sitemap.xml">站点地图</a></p></div>',
        canonical="/404.html", breadcrumbs=[("首页", "/"), ("404", "")]))

    # ---- sitemap / robots / 搜索索引 ----
    urls = sorted(set(sitemap), key=lambda u: (u.count("/"), u))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        pr = "1.0" if u == "/" else ("0.8" if u.startswith(("/topics/", "/models/", "/faq/")) else "0.7")
        sm.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>%s</priority></url>" % (BASE, u, TODAY, pr))
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm))
    write("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE)
    write("assets/search-index.json", json.dumps(search_index, ensure_ascii=False, indent=1))

    # ---- 仓库 README ----
    readme = """# Token173 API 中转笔记 · 静态站

纯静态站点，无构建依赖、无外部 CDN、无第三方脚本。GitHub Pages 直接托管。

- 站点地址：`%s/`
- 内容源：`content/*.md`（30 篇）
- 构建器：`tools/build.py`

## 重新构建

```bash
python3 tools/build.py
```

换自定义域名后，用环境变量重建 canonical、og:url 与 sitemap：

```bash
SITE_BASE_URL=https://docs.token173.net python3 tools/build.py
```

## SEO 结构

| 层级 | 承接意图 | 页面 |
|---|---|---|
| 核心词 | AI 中转站推荐 / API 中转站 / 大模型聚合平台 | `/` |
| 修饰长尾 | 好用 / 靠谱 / 稳定 / 老牌 / 国内直连 / 各模型家族 | `/topics/<topic>/` |
| 问题与教程词 | 怎么配 / 怎么查 / 怎么算 / 怎么测 | `/articles/<slug>/` × 30 |
| 型号词 | 26 个具体模型 ID | `/models/` |
| 疑问词 | 是什么 / 会不会 / 怎么办 | `/faq/` |

每页含唯一 H1、定制 title / description / keywords、canonical、Open Graph、BreadcrumbList 与 Organization 结构化数据；文章页另有 BlogPosting，含问答的页面与 FAQ 页另有 FAQPage。全站静态 HTML，爬虫无需执行 JS 即可读取正文。

内链：面包屑 → 分类页 → 文章页 → 相关文章 → 型号页 / FAQ，形成 Hub 与内容页的双向链接，避免孤岛页。

## 绑定自定义域名

**推荐用现有主域的子域，而不是另买新域**：子域能继承主域权重、品牌集中、零成本，新独立域要从零积累信任且需单独备案。

候选子域（按推荐顺序）：

| 子域 | 说明 |
|---|---|
| `docs.token173.net` | 首选，文档 / 教程语义清晰 |
| `guide.token173.net` | 备选，教程导向 |
| `wiki.token173.net` | 备选，知识库导向 |
| `blog.token173.net` | 备选，笔记导向 |

不建议 `api.token173.net`：容易和真实 API 端点混淆。

配置步骤：

1. 在 `token173.net` 的 DNS 管理里加一条记录：
   `docs  CNAME  Token173.github.io.`（TTL 可设 3600）
2. 把仓库里的 `CNAME.example` 改名为 `CNAME`，内容保持 `docs.token173.net`。
3. GitHub 仓库 Settings → Pages → Custom domain 填 `docs.token173.net`，保存后等 DNS 生效，再勾 Enforce HTTPS。
4. 用 `SITE_BASE_URL=https://docs.token173.net python3 tools/build.py` 重建，把 canonical 与 sitemap 换成新域名。

DNS 未生效前不要放 `CNAME` 文件，否则默认域名会被重定向到一个还解析不了的地址。

另买独立新域（可选，非首选）时，方向是「AI 教程 / API 文档」类短词组合；注册前先查可注册性与商标情况，国内解析还需备案。

## 内容口径

内容按公开资料与实际接入过程整理，不列无来源排行、不承诺折扣或 SLA 数字。型号 ID、价格与平台规则会调整，一律以平台控制台当前公示为准。第三方中转存在数据与资金风险，站点已作提示。

站点与提交记录不包含任何个人联系方式。
""" % BASE
    write("README.md", readme)

    print("构建完成：%d 篇文章 / %d 个 URL / %d 条搜索索引" % (len(META), len(urls), len(search_index)))
    print("Base URL:", BASE)


if __name__ == "__main__":
    main()
