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

## 常见薄封装

```bash
python3 {baseDir}/scripts/ifind_cli.py basic-data --payload '{"codes":"300750.SZ"}'
python3 {baseDir}/scripts/ifind_cli.py smart-pick --payload '{"conditions":[]}'
python3 {baseDir}/scripts/ifind_cli.py report-query --payload '{"codes":"300750.SZ"}'
python3 {baseDir}/scripts/ifind_cli.py date-sequence --payload '{"startdate":"2025-01-01","enddate":"2025-01-31"}'
```

## 失败回退规则

如果 `auth-login` 无法抓到 `access_token` 和 `refresh_token`，就停止浏览器流程，改为向客户索取双 token，然后执行 `auth-set-tokens`。
