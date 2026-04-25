# 能力矩阵

这份文档专门给 Agent 看。

目的不是讲实现细节，而是明确回答三件事：

1. 这个 skill 当前到底能处理什么问题
2. 哪些能力需要 iFinD 鉴权
3. 哪些能力当前不要假装能做

## 使用规则

- 所有已支持能力都要求 iFinD 鉴权。
- 不接入公开免费源；没有可用 token、refresh 失败、账号无权限或 iFinD API 返回错误时，直接把 iFinD 失败状态交还给用户。
- 自然语言问题先走 `smart-query`。
- 本地规则没命中特定能力时，`smart-query` 会把用户原话交给 iFinD `/smart_stock_picking`；少数“有啥/怎么样/昵称”口语会先改写成 iFinD 更稳定的正式查询词。
- 只有自然语言入口和命名接口都不够时，才用 `api-call`。

## 总表

| 能力 | 当前状态 | 数据来源 | 主入口 | 备注 |
|------|----------|----------|--------|------|
| 个股实时行情 | 已支持 | iFinD | `smart-query` / `quote-realtime` | 必须鉴权 |
| 个股历史走势 | 已支持 | iFinD | `smart-query` / `quote-history` | 必须鉴权 |
| 单日开盘/收盘/最高/最低 | 已支持 | iFinD | `smart-query` / `quote-history` | 必须鉴权 |
| 大盘 / 指数快照 | 已支持 | iFinD | `smart-query` / `market-snapshot` | 必须鉴权 |
| 涨停数据 | 已支持 | iFinD | `smart-query` | 走 `/smart_stock_picking` |
| A 股榜单 | 已支持 | iFinD | `smart-query` | 走 `/smart_stock_picking` |
| 成交额榜 | 已支持 | iFinD | `smart-query` | 限制条件保留在自然语言 `searchstring` |
| 涨幅榜 / 跌幅榜 | 已支持 | iFinD | `smart-query` | 限制条件保留在自然语言 `searchstring` |
| 换手率榜 | 已支持 | iFinD | `smart-query` | 限制条件保留在自然语言 `searchstring` |
| 振幅榜 | 已支持 | iFinD | `smart-query` | 限制条件保留在自然语言 `searchstring` |
| 量比榜 | 已支持 | iFinD | `smart-query` | 限制条件保留在自然语言 `searchstring` |
| 基础财务指标 | 已支持 | iFinD | `smart-query` / `fundamental-basic` | 固定查询财务、估值、预测三组模板 |
| 精确财务指标 | 已支持 | iFinD | `smart-query` | 例如营收、毛利率、市盈率、总市值；保留原问题交给 iFinD |
| 个股画像 / 主营业务 | 已支持 | iFinD | `smart-query` | 走 `/smart_stock_picking` |
| 资金流相关问法 | 已支持 | iFinD | `smart-query` | 走 `/smart_stock_picking` |
| 公告摘要 / 公告检索 | 已支持 | iFinD | `smart-query` | 走 `/smart_stock_picking`；PDF 原文下载仍需手动接口确认 |
| 研报 / 评级 / 目标价 | 已支持 | iFinD | `smart-query` | 保留原始 `searchstring` |
| 龙虎榜 / 大宗交易 / 异动 | 已支持 | iFinD | `smart-query` | 保留原始 `searchstring` |
| 融资融券 / 北向 / 沪深股通 | 已支持 | iFinD | `smart-query` | 保留原始 `searchstring` |
| 股东 / 持仓 / 机构持仓 | 已支持 | iFinD | `smart-query` | 保留原始 `searchstring` |
| 分红派息 / 送转 / 解禁 | 已支持 | iFinD | `smart-query` | 保留原始 `searchstring` |
| 停牌复牌 / 风险警示 / 退市 | 已支持 | iFinD | `smart-query` | 保留原始 `searchstring` |
| 概念板块 / 题材 / 产业链 | 已支持 | iFinD | `smart-query` | 保留原始 `searchstring` |
| 新股申购 / 中签 / 发行上市 | 已支持 | iFinD | `smart-query` | 保留原始 `searchstring` |
| 交易日 / 休市日 | 已支持 | iFinD | `smart-query` | 走 `/date_sequence`，返回的 `time` 字段为交易日序列 |
| 复杂筛选 / 选股条件组合 | 可自然语言透传 | iFinD | `smart-query` | 透传到 `/smart_stock_picking` |
| 专业接口 | 透传能力 | iFinD | `report-query` / `date-sequence` / `api-call` | 自然语言入口不够时再用 |
| 全市场分位筛选 | 当前无稳定能力 | iFinD 理论可做 | 无 | 例如“前 15% 市值的沪深股票” |

## A. 必须先鉴权

以下能力即使看起来可以从公开网页拿到，也必须通过 iFinD：

- 个股实时行情
- 个股历史走势
- 单日开盘价 / 收盘价 / 高低点
- 大盘 / 指数快照
- 涨停数据
- A 股榜单
- 成交额榜、涨跌幅榜、换手率榜、振幅榜、量比榜
- 基本面、画像、资金流
- 公告、研报、龙虎榜、两融、北向、股东、持仓、分红、解禁、停复牌、概念板块、新股、交易日

如果没有可用 iFinD token，返回 `auth_required`，不要继续查其它来源。

## B. 可选大模型路由

如果配置了 `IFIND_ROUTE_LLM_ENABLED=1` 和 API key，`smart-query` 会先尝试用大模型生成 iFinD 路由计划。

大模型路由的边界：

- 只能输出已支持 intent 和 iFinD payload
- 不能输出公开源 provider
- 不能输出 `fallback_type`
- 低置信度或解析失败时回到本地确定性路由

## C. 复杂自然语言怎么处理

以下问题不要求 Agent 自己拆 payload，先交给 `smart-query`：

- `筛一下新能源车产业链里市盈率低于30且近一个月放量的股票`
- `查一下贵州茅台近三年营收和毛利率`
- `找一下今天主力资金流入靠前的半导体股票`
- `按成交额看一下最近市场最活跃的行业`

处理结果：

- 本地规则能识别的，走稳定路由
- 本地规则识别不了的，走 `generic_smart_query`
- `generic_smart_query` 会调用 `/smart_stock_picking`
- 数据仍然只来自 iFinD

## D. 当前不要假装能做

以下问题当前不要告诉用户“已经支持”：

- `帮我找前15%市值的沪深股票`
- `筛出市值前 20% 且换手率大于 3% 的股票`
- `按多个条件做全市场选股并返回结果`

原因：

- 这类问题超出当前已验证的稳定路由
- 可以先让 `smart-query` 透传给 iFinD
- 如果 iFinD 返回失败，再告诉用户当前没有稳定覆盖，不要自己乱拼 payload

对外回复应使用类似口径：

`当前 tonghuashun-ifind-skill skill 还没有稳定覆盖这类全市场筛选能力。`

## E. Agent 决策口诀

- 所有查询都先确认 iFinD 鉴权
- 用户只要是自然语言查询，先用 `smart-query`
- 不要为了“看起来更专业”先写 `api-call`
- `smart-query` 失败后再看 `endpoint-list`
- 找不到稳定接口就明确说当前未覆盖，不乱猜 payload
