# 路由规则

这个 skill 的目标不是把所有 iFinD API 都自动猜出来，而是先把高频问题做成稳定路由。

如果你要先判断“这个能力有没有、该走哪个入口”，先看：

- [能力矩阵](capability-matrix.md)

## 优先顺序

1. 对于常见问题，优先使用 `smart-query`
2. 如果请求已经很明确，也可以直接使用显式稳定命令
3. 如果需要更多已封装接口，先用 `endpoint-list` 查看目录，再用 `endpoint-call`
4. 本地规则没有稳定命中时，`smart-query` 会透传到 iFinD `/smart_stock_picking`
5. 只有在自然语言入口和命名接口目录都未覆盖时，才考虑 `api-call`

## 强制 iFinD 数据源

所有查询都必须先完成 iFinD 鉴权。

- 没有 token 或 refresh 失败：返回 `auth_required`
- iFinD API 返回错误：保留 iFinD 错误并返回
- 账号无接口权限：直接告诉用户 iFinD 权限不足
- 不切换到腾讯财经、东方财富或其它公开源

## 可选 LLM 路由

默认路由是本地确定性规则。配置 `IFIND_ROUTE_LLM_ENABLED=1` 后，`smart-query` 会先调用大模型生成路由计划。

LLM 路由只能输出：

- 已支持 intent
- iFinD endpoint
- iFinD payload
- 股票或指数标的
- 日期窗口

LLM 路由不能输出：

- 非 iFinD provider
- `fallback_type`
- 公开源 URL
- 与 iFinD payload 无关的字段

低置信度或模型失败时，自动回到本地规则。

## 当前内置支持

### 0. 口语简称 / 昵称纠偏

适用说法：

- 茅台咋样
- 宁王今天咋样
- 招行现在多少
- 东财最近走势
- 中芯、迈瑞、药明、工行、平安等高频简称

默认规则：

- 正式中文名优先用 iFinD `/smart_stock_picking` 解析代码
- 高频口语简称允许用内置小型别名纠偏，避免 iFinD 把昵称误识别成无关股票
- 纠偏只用于确定 iFinD 证券代码；实际数据仍调用 iFinD 行情、历史或 `/smart_stock_picking`

### 1. 个股最新价

适用说法：

- 某股票现在股价
- 最新价
- 现价
- 行情

实际接口：

- `/real_time_quotation`

### 2. 个股历史走势

适用说法：

- 近一个月走势
- 最近一周
- 历史行情
- K线
- 指定日期开盘价、收盘价、最高价、最低价

实际接口：

- `/cmd_history_quotation`

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
- 排名方向和数量保留在自然语言里交给 iFinD 解析

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

### 9. A 股常见自然语言查询

适用说法：

- 贵州茅台最近公告
- 贵州茅台分红记录
- 贵州茅台龙虎榜
- 宁德时代融资余额和北向持股情况
- 宁德时代限售解禁安排
- 宁德时代所属概念和产业链
- 明天A股有哪些新股申购

实际接口：

- `/smart_stock_picking`

默认规则：

- 默认把用户原始问题作为 `searchstring`
- 如果用户说“公告有啥、分红怎么样、有啥研报、啥消息”这类口语，先改写成 iFinD 更稳定的正式词，例如“最近公告、分红记录、研报”
- `searchtype` 固定为 `stock`
- intent: `generic_smart_query`
- 不要因为问题里出现了股票名，就把公告、分红、龙虎榜、两融、北向持股等问法误路由成实时行情

### 10. 交易日 / 休市日

适用说法：

- 下一个交易日是什么时候
- 下个交易日是哪天
- 明天开不开盘
- 今天A股休市吗

实际接口：

- `/date_sequence`

默认规则：

- 使用上证指数 `000001.SH` 的 iFinD 日期序列能力
- `functionpara` 固定为 `{"Days": "Tradedays", "Fill": "Omit"}`
- 返回里的 `time` 字段就是 iFinD 给出的交易日序列

### 11. 复杂自然语言泛化查询

适用说法：

- 筛一下新能源车产业链里市盈率低于30且近一个月放量的股票
- 查一下贵州茅台近三年营收和毛利率
- 找一下半导体行业今天主力资金流入靠前的股票
- 看一下最近成交额活跃的行业

实际接口：

- `/smart_stock_picking`

默认规则：

- 本地规则没命中稳定路由时，直接把用户原始问题作为 `searchstring`
- `searchtype` 固定为 `stock`
- intent: `generic_smart_query`
- 不要求 Agent 先手写 endpoint 或 payload

## 什么时候不要猜

以下情况不要直接乱拼 `api-call`：

- 公告 PDF 下载
- 原文下载链接
- skill 里没写过的细分接口
- 你不确定 payload 结构

这时应该：

1. 回到本文件和 `usage.md`
2. 如果仍然没有明确映射，告诉用户：

`当前 tonghuashun-ifind-skill skill 没有稳定覆盖这个 iFinD 能力。`

如果 `smart-query` 和 iFinD 自然语言透传都失败，但 skill 里可能已经封过接口名，先执行：

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-list
```

如果目录里已经有目标能力，对应执行：

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call --name history_quote --payload '{...}'
```

## 手动 API 调用

只有在你已经明确知道目标 endpoint 和 payload 的情况下，才使用：

```bash
python3 {baseDir}/scripts/ifind_cli.py api-call --endpoint /xxx --payload '{...}'
```
