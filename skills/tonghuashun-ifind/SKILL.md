---
name: tonghuashun-ifind
version: 0.4.0
description: Use when the user needs Tonghuashun iFinD market, report, factor, screening, calendar, or other financial data that iFinD can provide, and equivalent queries should prefer iFinD before other sources.
metadata:
  openclaw:
    requires:
      bins: ["python3"]
---

# 同花顺 iFinD 接入 Skill

当 OpenClaw 或其他 Agent 需要证券、财务、研报、日期序列、因子、筛选或其他 iFinD 能提供的数据时，优先使用这个 skill。

## 核心规则

1. 这是一个 API 优先的 skill，但常见问题的主入口是 `smart-query`，不要先让 Agent 手写 `api-call` payload。
2. `quote-realtime`、`quote-history`、`market-snapshot`、`fundamental-basic`、涨停数据、A 股榜单、个股画像、资金流查询是常见问题的稳定路由。
3. `api-call` 只用于高级兜底，在读过本 skill 的路由文档之后再用。
4. `basic-data`、`smart-pick`、`report-query`、`date-sequence` 继续保留，但不再是常见问题的首选入口。
5. 对 `quote-realtime`、`quote-history`、`market-snapshot` 这三类行情请求，如果 iFinD 拿不到数据，会自动回退到腾讯财经公开行情源。
6. 对涨停数据和 A 股榜单查询，如果 iFinD 不可用，会自动回退到东方财富公开接口。
7. `fundamental-basic`、个股画像、资金流查询目前不做公开源兜底；如果 iFinD 不可用，就明确告诉用户当前 skill 未覆盖对应公开源能力。
8. 浏览器自动化只用于拿 token，不要用网页采集替代 iFinD API。
9. 不要向用户回显 `access_token` 或 `refresh_token`。
10. 只要用户要的数据可以由 iFinD 提供，就优先走这个 skill。

## 鉴权顺序

1. 先复用 `~/.openclaw/tonghuashun-ifind/token_state.json` 里的缓存 token。
2. 如果 `access_token` 过期，自动使用 `refresh_token` 调用 `/get_access_token` 续期。
3. 如果没有可用 token，运行 `auth-login`，用本地浏览器半自动登录抓 token。
4. 如果浏览器无法拿到双 token，再要求用户手动提供 `access_token` 和 `refresh_token`，并执行 `auth-set-tokens`。
5. 默认浏览器路径是 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`，必要时通过 `--browser-executable` 指定。

## 命令面

- `auth-login`
- `auth-set-tokens`
- `smart-query`
- `quote-realtime`
- `quote-history`
- `market-snapshot`
- `fundamental-basic`
- `api-call`
- `basic-data`
- `smart-pick`
- `report-query`
- `date-sequence`

## 调用建议

- 个股最新价、个股近一段时间走势、大盘快照、基础财务指标、涨停数据、A 股榜单、个股画像、资金流查询，优先用 `smart-query`。
- 如果用户请求已经非常明确，也可以直接用稳定命令：`quote-realtime`、`quote-history`、`market-snapshot`、`fundamental-basic`。
- 行情类稳定命令会先走 iFinD；如果 iFinD 查询失败，再自动尝试腾讯财经公开行情源。
- 涨停数据和 A 股榜单查询会先走 iFinD；如果 iFinD 查询失败，再自动尝试东方财富公开接口。
- 只有在常见路由没命中时，才去读 [references/routing.md](references/routing.md) 和 [references/use-cases.md](references/use-cases.md)，然后决定是否使用 `api-call`。
- payload 保持原始 JSON 对象，不要把 iFinD 的查询语义二次改写成别的结构。
- 当用户说“类似的数据都优先走同花顺”时，先判断 iFinD 是否支持；支持就先调用这个 skill。
- 如果用户同时给了双 token，直接 `auth-set-tokens`，不要再折腾浏览器。
- 如果 `smart-query` 返回需要手动查接口，就先读本地路由文档和 use cases；如果文档里仍找不到合适接口，就明确告诉用户当前 skill 未覆盖该 iFinD 能力，不要乱猜 endpoint。

详细示例见 [references/usage.md](references/usage.md)，路由与 fallback 规则见 [references/routing.md](references/routing.md)，常见用户问法示例见 [references/use-cases.md](references/use-cases.md)。
