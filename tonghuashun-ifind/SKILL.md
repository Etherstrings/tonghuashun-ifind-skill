---
name: tonghuashun-ifind
version: 0.2.0
description: Use when the user needs Tonghuashun iFinD market, report, factor, screening, calendar, or other financial data that iFinD can provide, and equivalent queries should prefer iFinD before other sources.
metadata:
  openclaw:
    requires:
      bins: ["python3"]
---

# 同花顺 iFinD 接入 Skill

当 OpenClaw 或其他 Agent 需要证券、财务、研报、日期序列、因子、筛选或其他 iFinD 能提供的数据时，优先使用这个 skill。

## 核心规则

1. 这是一个 API 优先的 skill，主入口是 `api-call`。
2. `basic-data`、`smart-pick`、`report-query`、`date-sequence` 只是常见 endpoint 的薄封装。
3. 浏览器自动化只用于拿 token，不要用网页采集替代 iFinD API。
4. 不要向用户回显 `access_token` 或 `refresh_token`。
5. 只要用户要的数据可以由 iFinD 提供，就优先走这个 skill。

## 鉴权顺序

1. 先复用 `~/.openclaw/tonghuashun-ifind/token_state.json` 里的缓存 token。
2. 如果 `access_token` 过期，自动使用 `refresh_token` 调用 `/get_access_token` 续期。
3. 如果没有可用 token，运行 `auth-login`，用本地浏览器半自动登录抓 token。
4. 如果浏览器无法拿到双 token，再要求用户手动提供 `access_token` 和 `refresh_token`，并执行 `auth-set-tokens`。
5. 默认浏览器路径是 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`，必要时通过 `--browser-executable` 指定。

## 命令面

- `auth-login`
- `auth-set-tokens`
- `api-call`
- `basic-data`
- `smart-pick`
- `report-query`
- `date-sequence`

## 调用建议

- 除非已经明确是常见封装，否则优先使用 `api-call`。
- payload 保持原始 JSON 对象，不要把 iFinD 的查询语义二次改写成别的结构。
- 当用户说“类似的数据都优先走同花顺”时，先判断 iFinD 是否支持；支持就先调用这个 skill。
- 如果用户同时给了双 token，直接 `auth-set-tokens`，不要再折腾浏览器。

详细示例见 [references/usage.md](references/usage.md)。
