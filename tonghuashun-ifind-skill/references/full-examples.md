# 全面例子

这份文档专门给 Agent 和开发者看，目标是把当前命令面用一组真实 A 股例子串起来。

说明：

- 所有查询都必须先完成 iFinD 鉴权
- `smart-query` 和稳定路由是当前最推荐的入口
- 常见路由不够时，先看 `endpoint-list` / `endpoint-call`
- `basic-data`、`smart-pick`、`report-query`、`date-sequence` 属于透传 wrapper
- 如果你的 iFinD 账号对某个 endpoint 有更严格的字段要求，以你账号对应文档为准

运行前请先把 `{baseDir}` 替换成 skill 根目录。

## 1. 一套完整流程

### 1.1 官方 refresh_token 鉴权

```bash
python3 {baseDir}/scripts/ifind_cli.py auth-set-refresh-token \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

适用场景：

- 用户已经从 iFinD 超级命令客户端或网页版账号详情复制了 `refresh_token`
- 需要按官方 HTTP 接口方式换取并缓存 `access_token`

### 1.2 手动注入双 token

```bash
python3 {baseDir}/scripts/ifind_cli.py auth-set-tokens \
  --access-token "$IFIND_ACCESS_TOKEN" \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

适用场景：

- 你已经有可用的 `access_token` 和 `refresh_token`

### 1.3 先用自然语言问一个最常见问题

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看看贵州茅台现在股价"
```

这条命令会命中：

- intent: `quote_realtime`
- endpoint: `/real_time_quotation`

### 1.4 再问一个历史走势问题

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看下宁德时代近一个月走势"
```

这条命令会命中：

- intent: `quote_history`
- endpoint: `/cmd_history_quotation`

### 1.5 再问一个榜单问题

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "A股成交额榜前十"
```

这条命令会命中：

- intent: `leaderboard_screen`
- endpoint: `/smart_stock_picking`
- payload: `{"searchstring":"A股成交额榜前十","searchtype":"stock"}`

## 2. `smart-query` 全路由真实例子

### 2.1 个股实时行情

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看看贵州茅台现在股价"
```

关注返回字段：

- `data.intent`
- `data.entity.symbol`
- `data.response`

### 2.2 个股历史走势

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "贵州茅台最近一周表现"
```

关注返回字段：

- `data.intent`
- `data.request.payload.startdate`
- `data.request.payload.enddate`
- `data.response`

### 2.3 大盘 / 指数快照

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "沪深300现在怎么样"
```

关注返回字段：

- `data.intent`
- `data.request.payload.codes`
- `data.response`

### 2.4 基础财务指标

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看看宁德时代基本面"
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

关注返回字段：

- `data.intent`
- `data.request.payload.searchstring`
- `data.response`

### 2.6 A 股榜单

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
- `data.request.payload.searchstring`
- `data.response`

### 2.7 个股画像 / 主营业务

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "贵州茅台主营业务是什么"
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

关注返回字段：

- `data.intent`
- `data.request.payload.searchstring`
- `data.response`

### 2.9 A 股常见数据查询

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "宁德时代融资余额和北向持股情况"
```

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "贵州茅台最近公告、分红记录和龙虎榜"
```

这类问题不要因为出现股票名就改查实时行情。关注返回字段：

- `data.intent`，通常是 `generic_smart_query`
- `data.request.payload.searchstring`
- `data.response`

### 2.10 复杂自然语言筛选

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "筛一下新能源车产业链里市盈率低于30且近一个月放量的股票"
```

这类问题不要让 Agent 先拆 endpoint 和 payload。关注返回字段：

- `data.intent`，通常是 `generic_smart_query`
- `data.request.payload.searchstring`
- `data.response`

## 3. 显式稳定命令真实例子

### 3.1 `quote-realtime`

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-realtime --symbol 600519
```

适合：

- 已经知道证券代码
- 只需要实时行情

### 3.2 `quote-history`

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-history \
  --symbol 300750 \
  --days 30
```

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-history \
  --symbol 600004.SH \
  --start-date 2026-04-21 \
  --end-date 2026-04-21
```

适合：

- 已经知道证券代码
- 需要明确日期窗口

### 3.3 `market-snapshot`

```bash
python3 {baseDir}/scripts/ifind_cli.py market-snapshot
python3 {baseDir}/scripts/ifind_cli.py market-snapshot --symbol 沪深300
```

### 3.4 `fundamental-basic`

```bash
python3 {baseDir}/scripts/ifind_cli.py fundamental-basic --symbol 300750
```

## 4. 命名接口目录

查看目录：

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-list
```

按名字调用：

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call \
  --name real_time_quote \
  --payload '{"codes":"600519.SH","indicators":"open,high,low,latest,changeRatio,change,preClose,volume,amount"}'
```

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call \
  --name history_quote \
  --payload '{"codes":"600004.SH","indicators":"open,close,high,low,volume","startdate":"2026-04-21","enddate":"2026-04-21"}'
```

## 5. 原始薄封装

```bash
python3 {baseDir}/scripts/ifind_cli.py basic-data \
  --payload '{"codes":"300750.SZ","indicators":"ths_close_price_stock"}'

python3 {baseDir}/scripts/ifind_cli.py smart-pick \
  --payload '{"searchstring":"今天的A股涨停数据","searchtype":"stock"}'

python3 {baseDir}/scripts/ifind_cli.py report-query \
  --payload '{"codes":"300750.SZ"}'

python3 {baseDir}/scripts/ifind_cli.py date-sequence \
  --payload '{"startdate":"2026-04-01","enddate":"2026-04-30"}'
```

## 6. 可选 LLM 路由

```bash
export IFIND_ROUTE_LLM_ENABLED=1
export IFIND_ROUTE_LLM_API_KEY="$OPENAI_API_KEY"
export IFIND_ROUTE_LLM_MODEL="gpt-4o-mini"

python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "帮我看一下茅台四月以来的日线表现"
```

如果大模型返回低置信度或不可解析结果，skill 会自动回到本地确定性路由。

## 7. 失败处理示例

没有可用 token 时：

```json
{
  "ok": false,
  "error": {
    "type": "auth_required"
  }
}
```

处理方式：

1. 先运行 `auth-set-refresh-token`
2. 鉴权成功后重试原查询
3. 不要使用其它数据源替代
