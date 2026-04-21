# 路由规则

这个 skill 的目标不是把所有 iFinD API 都自动猜出来，而是先把高频问题做成稳定路由。

如果你要先判断“这个能力有没有、免费源能不能兜底”，先看：

- [能力矩阵](capability-matrix.md)

## 优先顺序

1. 对于常见问题，优先使用 `smart-query`
2. 如果请求已经很明确，也可以直接使用显式稳定命令
3. 如果需要更多已封装接口，先用 `endpoint-list` 查看目录，再用 `endpoint-call`
4. 只有在常见路由和命名接口目录都未覆盖时，才考虑 `api-call`

## 自动兜底

以下三类请求会先走 iFinD，失败时自动回退到腾讯财经公开行情源：

1. `quote_realtime`
2. `quote_history`
3. `market_snapshot`

以下两类请求会先走 iFinD，失败时自动回退到东方财富公开接口：

1. `limit_up_screen`
2. `leaderboard_screen`

`fundamental_basic`、`entity_profile`、`capital_flow` 目前没有公开源兜底。

这意味着：

- 没有 iFinD 账号时，`quote_realtime`、`quote_history`、`market_snapshot`、`limit_up_screen`、`leaderboard_screen` 仍然应该继续执行
- 不要因为“没有 iFinD 账号”就直接告诉用户当前 skill 不能用
- 回复里应明确说明当前结果来自免费公开源

## 当前内置支持

### 1. 个股最新价

适用说法：

- 某股票现在股价
- 最新价
- 现价
- 行情

实际接口：

- `/real_time_quotation`
- fallback: 腾讯财经 `https://qt.gtimg.cn/q=...`

### 2. 个股历史走势

适用说法：

- 近一个月走势
- 最近一周
- 历史行情
- K线

实际接口：

- `/cmd_history_quotation`
- fallback: 腾讯财经 `https://web.ifzq.gtimg.cn/appstock/app/fqkline/get`

默认规则：

- 没给时间时，默认最近 30 天

### 3. 大盘或指数快照

适用说法：

- 看一下大盘
- 看指数
- 看盘面

默认指数包：

- 上证指数 `000001.SH`
- 深证成指 `399001.SZ`
- 创业板指 `399006.SZ`
- 沪深300 `000300.SH`

实际接口：

- `/real_time_quotation`
- fallback: 腾讯财经 `https://qt.gtimg.cn/q=...`

### 4. 基础财务指标

适用说法：

- 基本面
- 财务
- 估值
- 市盈率 / 市净率 / 市值

实际接口：

- `/smart_stock_picking`

当前会固定查询三组模板：

- 财务指标
- 估值指标
- 预测指标

公开源兜底：

- 当前不支持
- 如果 iFinD 不可用，直接告诉用户当前 skill 没有稳定覆盖公开源基本面能力

### 5. 涨停数据

适用说法：

- 今天的A股涨停数据
- 今日涨停
- 涨停板
- 封板数据

实际接口：

- `/smart_stock_picking`

默认规则：

- 直接把用户原始问题作为 `searchstring`
- `searchtype` 固定为 `stock`

公开源兜底：

- 东方财富公开涨停池 `https://push2ex.eastmoney.com/getTopicZTPool`
- 如果 iFinD 不可用，自动回退到东方财富公开涨停池

### 6. A 股榜单查询

适用说法：

- A股成交额榜前十
- 今日涨幅榜
- 跌幅榜前二十
- 换手率排行
- 振幅榜
- 量比榜

实际接口：

- `/smart_stock_picking`

默认规则：

- 直接把用户原始问题作为 `searchstring`
- `searchtype` 固定为 `stock`
- 内部会补充 `fallback_type` 和 `limit`

公开源兜底：

- 东方财富公开排行接口 `https://push2.eastmoney.com/api/qt/clist/get`
- 当前稳定支持：`turnover`、`gainers`、`losers`、`turnover_ratio`、`amplitude`、`volume_ratio`

### 7. 个股画像 / 主营业务

适用说法：

- 贵州茅台主营业务是什么
- 宁德时代公司简介
- 这家公司是做什么的

实际接口：

- `/smart_stock_picking`

默认规则：

- 先解析股票标的
- 再把用户原始问题作为 `searchstring`

公开源兜底：

- 当前不支持

### 8. 资金流问题

适用说法：

- 今天主力资金流入前十
- 某股票资金流向
- 资金净流入排行

实际接口：

- `/smart_stock_picking`

默认规则：

- 直接把用户原始问题作为 `searchstring`
- `searchtype` 固定为 `stock`

公开源兜底：

- 当前不支持

## 什么时候不要猜

以下情况不要直接乱拼 `api-call`：

- 公告 PDF 下载
- 原文下载链接
- skill 里没写过的细分接口
- 你不确定 payload 结构

这时应该：

1. 回到本文件和 `usage.md`
2. 如果仍然没有明确映射，告诉用户：

`当前 tonghuashun-ifind skill 没有稳定覆盖这个 iFinD 能力。`

如果只是“常见路由没命中，但 skill 里可能已经封过接口名”，先执行：

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-list
```

如果目录里已经有目标能力，对应执行：

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call --name history_quote --payload '{...}'
```

## 手动兜底

只有在你已经明确知道目标 endpoint 和 payload 的情况下，才使用：

```bash
python3 {baseDir}/scripts/ifind_cli.py api-call --endpoint /xxx --payload '{...}'
```
