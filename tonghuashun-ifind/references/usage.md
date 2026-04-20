# 使用说明

运行命令前，请先把 `{baseDir}` 替换成这个 skill 的目录。

## 手动注入双 token

```bash
python3 {baseDir}/scripts/ifind_cli.py auth-set-tokens \
  --access-token "$IFIND_ACCESS_TOKEN" \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

## 半自动浏览器登录

```bash
python3 {baseDir}/scripts/ifind_cli.py auth-login \
  --username "$IFIND_USERNAME" \
  --password "$IFIND_PASSWORD"
```

如果需要指定本地浏览器路径：

```bash
python3 {baseDir}/scripts/ifind_cli.py auth-login \
  --username "$IFIND_USERNAME" \
  --password "$IFIND_PASSWORD" \
  --browser-executable "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

## 原始 API 调用

```bash
python3 {baseDir}/scripts/ifind_cli.py api-call \
  --endpoint /basic_data_service \
  --payload '{"codes":"300750.SZ","indicators":"ths_close_price_stock","functionpara":{"Interval":"D","StartDate":"2025-01-01","EndDate":"2025-01-31"}}'
```

## 常见查询主入口

优先让 Agent 用 `smart-query`，直接把用户的问题交给 skill 路由：

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看看贵州茅台现在股价"

python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看下宁德时代近一个月走势"

python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看一下大盘"

python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "看看宁德时代基本面"

python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "今天的A股涨停数据"
```

## 显式稳定命令

```bash
python3 {baseDir}/scripts/ifind_cli.py quote-realtime --symbol 600519
python3 {baseDir}/scripts/ifind_cli.py quote-history --symbol 300750 --days 30
python3 {baseDir}/scripts/ifind_cli.py market-snapshot
python3 {baseDir}/scripts/ifind_cli.py market-snapshot --symbol 沪深300
python3 {baseDir}/scripts/ifind_cli.py fundamental-basic --symbol 300750
```

说明：

- `quote-realtime`、`quote-history`、`market-snapshot` 会先走 iFinD
- 如果 iFinD 查询失败，会自动回退到腾讯财经公开行情源
- 涨停数据查询会先走 iFinD，失败时自动回退到东方财富公开涨停池
- `fundamental-basic` 暂时没有公开源兜底

## 保留的原始薄封装

```bash
python3 {baseDir}/scripts/ifind_cli.py basic-data --payload '{"codes":"300750.SZ"}'
python3 {baseDir}/scripts/ifind_cli.py smart-pick --payload '{"conditions":[]}'
python3 {baseDir}/scripts/ifind_cli.py report-query --payload '{"codes":"300750.SZ"}'
python3 {baseDir}/scripts/ifind_cli.py date-sequence --payload '{"startdate":"2025-01-01","enddate":"2025-01-31"}'
```

## 失败回退规则

如果 `auth-login` 无法抓到 `access_token` 和 `refresh_token`，就停止浏览器流程，改为向客户索取双 token，然后执行 `auth-set-tokens`。

如果是行情类请求，而且 iFinD 查询失败：

1. skill 会自动尝试腾讯财经公开行情源
2. 返回结果里会标出 provider 为 `tencent_finance`
3. 不需要 Agent 再手写第二套命令
4. 如果连公开源也失败，再把失败结果返回给用户

如果 `smart-query` 返回需要手动查接口：

1. 先读 `references/routing.md`
2. 再看 `references/use-cases.md` 里是否已有类似问法
3. 再决定是否使用 `api-call`
4. 如果文档里也找不到合适接口，就明确告诉用户当前 skill 未覆盖该 iFinD 能力
