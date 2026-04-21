# 全面例子

这份文档专门给 Agent 和开发者看，目标是把这个 skill 当前所有命令面都用一组真实 A 股例子串起来。

说明：

- 下面全部使用真实股票、指数、日期和自然语言问法，不再用占位符股票名
- `smart-query` 和稳定路由是当前最推荐的入口
- 常见路由不够时，先看 `endpoint-list` / `endpoint-call`
- `basic-data`、`smart-pick`、`report-query`、`date-sequence` 属于透传 wrapper，示例会给最小可抄写法
- 如果你的 iFinD 账号对某个 endpoint 有更严格的字段要求，以你账号对应文档为准

运行前请先把 `{baseDir}` 替换成 skill 根目录。

## 1. 一套完整流程

### 1.1 手动注入双 token

```bash
python3 {baseDir}/scripts/ifind_cli.py auth-set-tokens \
  --access-token "$IFIND_ACCESS_TOKEN" \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

适用场景：

- 你已经有可用的 `access_token` 和 `refresh_token`
- 想避免浏览器登录流程

### 1.2 先用自然语言问一个最常见问题

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看看贵州茅台现在股价"
```

这条命令会命中：

- intent: `quote_realtime`
- endpoint: `/real_time_quotation`

### 1.3 再问一个历史走势问题

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看下宁德时代近一个月走势"
```

这条命令会命中：

- intent: `quote_history`
- endpoint: `/cmd_history_quotation`

### 1.4 再问一个免费回退能力明确的问题

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "A股成交额榜前十"
```

这条命令会命中：

- intent: `leaderboard_screen`
- endpoint: `/smart_stock_picking`
- iFinD 失败时自动回退东方财富公开排行榜

### 1.5 没有 iFinD 账号时也能查的真实例子

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-history \
  --symbol 600004.SH \
  --start-date 2026-04-21 \
  --end-date 2026-04-21
```

免费源实测可返回：

- 开盘 `8.88`
- 收盘 `8.89`

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-realtime --symbol 600004.SH
```

免费源实测可返回：

- 名称 `白云机场`

如果用户还需要量比，这个 skill 当前应继续补查公开源，而不是停在“没有 iFinD 账号”。

## 2. `smart-query` 全路由真实例子

### 2.1 个股实时行情

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看看贵州茅台现在股价"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "宁德时代最新价"
```

关注返回字段：

- `data.intent`
- `data.entity.symbol`
- `data.response.quotes[0].latest`

### 2.2 个股历史走势

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看下宁德时代近一个月走势"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "贵州茅台最近一周表现"
```

关注返回字段：

- `data.intent`
- `data.request.payload.startdate`
- `data.request.payload.enddate`
- `data.response.candles`

### 2.3 大盘 / 指数快照

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看一下大盘"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "沪深300现在怎么样"
```

关注返回字段：

- `data.intent`
- `data.request.payload.codes`
- `data.response.quotes`

### 2.4 基础财务指标

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看看宁德时代基本面"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "贵州茅台估值怎么样"
```

关注返回字段：

- `data.intent`
- `data.request.payload.searchstrings`
- `data.results.financials`
- `data.results.valuation`
- `data.results.forecast`

### 2.5 涨停数据

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "今天的A股涨停数据"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "今日涨停"
```

关注返回字段：

- `data.intent`
- `data.provider.name`
- `data.response.limit_up_stocks`

### 2.6 A 股榜单

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "A股成交额榜前十"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "今日涨幅榜前二十"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "量比榜前十"
```

关注返回字段：

- `data.intent`
- `data.request.payload.fallback_type`
- `data.request.payload.limit`
- `data.response.items`

### 2.7 个股画像 / 主营业务

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "贵州茅台主营业务是什么"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "宁德时代公司简介"
```

关注返回字段：

- `data.intent`
- `data.entity.symbol`
- `data.response`

### 2.8 资金流

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "今天主力资金流入前十"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "宁德时代资金流向"
```

关注返回字段：

- `data.intent`
- `data.request.payload.searchstring`
- `data.response`

## 3. 显式稳定命令真实例子

### 3.1 `quote-realtime`

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-realtime --symbol 600519
```

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-realtime --symbol 300750.SZ
```

适合：

- 你已经知道证券代码
- 不需要走自然语言识别

### 3.2 `quote-history`

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-history \
  --symbol 300750 \
  --days 30
```

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-history \
  --symbol 600519.SH \
  --start-date 2026-03-01 \
  --end-date 2026-04-21
```

### 3.3 `market-snapshot`

```bash
python3 {baseDir}/scripts/ifind_cli.py market-snapshot
```

```bash
python3 {baseDir}/scripts/ifind_cli.py market-snapshot --symbol 沪深300
```

### 3.4 `fundamental-basic`

```bash
python3 {baseDir}/scripts/ifind_cli.py fundamental-basic --symbol 300750
```

```bash
python3 {baseDir}/scripts/ifind_cli.py fundamental-basic --symbol 600519.SH
```

## 4. 命名接口目录真实例子

### 4.1 先列出当前已封装接口

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-list
```

你应该能看到至少这些名字：

- `basic_data`
- `smart_pick`
- `report_query`
- `date_sequence`
- `real_time_quote`
- `history_quote`
- `limit_up_screen`
- `leaderboard_screen`
- `fundamental_basic`
- `entity_profile`
- `capital_flow`

### 4.2 按命名接口取实时行情

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call \
  --name real_time_quote \
  --payload '{"codes":"600519.SH,000300.SH"}'
```

对应实际 endpoint：

- `/real_time_quotation`

### 4.3 按命名接口取历史行情

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call \
  --name history_quote \
  --payload '{"codes":"600004.SH","indicators":"open,close,high,low,volume","startdate":"2026-04-21","enddate":"2026-04-21"}'
```

对应实际 endpoint：

- `/cmd_history_quotation`

### 4.4 按命名接口取涨停池

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call \
  --name limit_up_screen \
  --payload '{"searchstring":"今天的A股涨停数据","searchtype":"stock"}'
```

对应实际 endpoint：

- `/smart_stock_picking`

说明：

- `limit_up_screen` 是能力别名，底层仍调用 `/smart_stock_picking`
- 如果 iFinD 不可用，常见问法更推荐继续走 `smart-query`，这样 skill 才能自动回退到免费源

## 5. 原始 `api-call` 真实例子

当你已经明确知道 endpoint 和 payload 时，直接用：

```bash
python3 {baseDir}/scripts/ifind_cli.py api-call \
  --endpoint /basic_data_service \
  --payload '{"codes":"300750.SZ","indicators":"ths_close_price_stock","functionpara":{"Interval":"D","StartDate":"2026-04-01","EndDate":"2026-04-21"}}'
```

另一个更贴近实时行情的例子：

```bash
python3 {baseDir}/scripts/ifind_cli.py api-call \
  --endpoint /real_time_quotation \
  --payload '{"codes":"600519.SH","indicators":"open,high,low,latest,changeRatio,change,preClose,volume,amount"}'
```

## 6. 四个薄封装 wrapper 的真实例子

这四个命令本质上都是把 payload 原样转发给对应 endpoint。

### 5.1 `basic-data`

```bash
python3 {baseDir}/scripts/ifind_cli.py basic-data \
  --payload '{"codes":"300750.SZ","indicators":"ths_close_price_stock","functionpara":{"Interval":"D","StartDate":"2026-04-01","EndDate":"2026-04-21"}}'
```

对应 endpoint：

- `/basic_data_service`

### 5.2 `smart-pick`

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-pick \
  --payload '{"searchstring":"贵州茅台 市盈率 市净率 总市值","searchtype":"stock"}'
```

对应 endpoint：

- `/smart_stock_picking`

### 5.3 `report-query`

这是研报 / 报告类透传入口。不同账号权限下字段要求可能不同，下面给最小真实股票例子：

```bash
python3 {baseDir}/scripts/ifind_cli.py report-query \
  --payload '{"codes":"600519.SH"}'
```

如果你的账号文档要求更完整条件，再在这个基础上补充，例如你自己的报告类型、日期区间、筛选条件。

对应 endpoint：

- `/report_query`

### 5.4 `date-sequence`

```bash
python3 {baseDir}/scripts/ifind_cli.py date-sequence \
  --payload '{"startdate":"2026-04-01","enddate":"2026-04-30"}'
```

如果你的账号文档支持更多交易日历参数，也是在这个 payload 上继续补。

对应 endpoint：

- `/date_sequence`

## 7. 推荐怎么选接口

如果你只是想让 Agent 回答大多数 A 股常见问题：

1. 先用 `smart-query`
2. 已知证券代码且只想查行情时，再用 `quote-realtime` / `quote-history`
3. 常见路由不够但 skill 已经封了名字时，先 `endpoint-list`，再 `endpoint-call`
4. 已知 endpoint 和 payload 时，才用 `api-call`
5. 只有明确知道某个薄封装对应接口时，才直接用 `basic-data` / `smart-pick` / `report-query` / `date-sequence`

## 8. 一个不要乱猜的反例

下面这种请求不要直接编 payload：

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "帮我找贵州茅台公告PDF下载链接并按日期排序"
```

这类请求如果命中 `manual_api_lookup_required`，就回到：

- `references/routing.md`
- `references/use-cases.md`

如果文档里仍没有明确映射，就直接告诉用户当前 skill 未稳定覆盖该能力。
