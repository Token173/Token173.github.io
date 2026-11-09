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
SITE_BASE_URL=https://guide.token173.net python3 tools/build.py
```

## 站点结构

`/` 首页、`/topics/` 分类、`/articles/` 文章、`/models/` 型号索引、`/faq/` 常见问题、`/about/` 关于；附 `sitemap.xml` 与 `robots.txt`。全站纯静态 HTML，无外部依赖。

## 绑定自定义域名

**推荐用现有主域的子域，而不是另买新域**：子域能继承主域权重、品牌集中、零成本，新独立域要从零积累信任且需单独备案。

### 已核查的占用情况（2026-11-09 DNS 实测）

| 子域 | 状态 | 说明 |
|---|---|---|
| `docs.token173.net` | **已占用** | CNAME 指向 Apifox 文档服务，不要动它 |
| `api.token173.net` | **已占用** | CNAME 指向现有接口服务，不要动它 |
| `guide.token173.net` | 空闲 | **首选**，教程 / 选型笔记语义，与现有 docs 参考文档正好分工 |
| `apidocs.token173.net` | 空闲 | 备选，API 教程语义更精准 |
| `wiki.token173.net` | 空闲 | 备选，知识库导向 |
| `learn.token173.net` / `handbook.token173.net` / `blog.token173.net` | 空闲 | 备选 |

主域 NS 托管在 Cloudflare（`elly.ns.cloudflare.com` / `fred.ns.cloudflare.com`），子域也在这里加。

### 配置步骤

1. Cloudflare → `token173.net` → DNS → 添加记录：
   `Type: CNAME` / `Name: guide` / `Target: Token173.github.io` / `TTL: Auto`。
   **代理状态必须选「仅 DNS / DNS only」（灰云）**，开橙云代理会让 GitHub 的域名所有权校验和证书签发失败。
2. 把仓库里的 `CNAME.example` 改名为 `CNAME`，内容保持 `guide.token173.net`。
3. GitHub 仓库 Settings → Pages → Custom domain 填 `guide.token173.net`，保存后等 DNS 生效，再勾 Enforce HTTPS。
4. 用 `SITE_BASE_URL=https://guide.token173.net python3 tools/build.py` 重建，把 canonical、og:url 与 sitemap 换成新域名，再提交推送。
5. 到 Search Console / 百度站长平台提交新域名的 sitemap；默认域名 `token173.github.io` 会 301 到自定义域，无需额外处理。

DNS 未生效前不要放 `CNAME` 文件，否则默认域名会被重定向到一个还解析不了的地址。

### 要不要另买独立新域

不建议作为首选。新域没有历史权重、外链要从零积累、国内解析需备案，还会把品牌权重分散。确有隔离需求时，方向是「AI 教程 / API 文档」类短词组合，注册前先查可注册性与商标情况；买来后仍按上面的方式 CNAME 到本站即可。

## 内容口径

内容按公开资料与实际接入过程整理，不列无来源排行、不承诺折扣或 SLA 数字。型号 ID、价格与平台规则会调整，一律以平台控制台当前公示为准。第三方中转存在数据与资金风险，站点已作提示。

站点与提交记录不包含任何个人联系方式。
