# Token173 API 中转笔记 · 静态站

纯静态站点，无构建依赖、无外部 CDN、无第三方脚本。GitHub Pages 直接托管。

- 站点地址：`https://token173.github.io/`
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
