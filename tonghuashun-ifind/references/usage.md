# 使用说明

运行命令前，请先把 `{baseDir}` 替换成这个 skill 的目录。

如果你要先判断“这件事到底能不能做、免费源有没有、没有 iFinD 账号时该不该继续”，先看：

- [能力矩阵](capability-matrix.md)

如果你要一份覆盖所有命令面的可抄完整例子，先看：

- [全面例子](full-examples.md)

## Skill 地址

如果需要查看这个 skill 在不同 Agent / Hub 上的外部入口，当前以这两个地址为准：

- ClawHub / OpenClaw：
  `https://clawhub.ai/etherstrings/tonghuashun-ifind`
- Hermes Agent GitHub skill 源：
  `https://github.com/Etherstrings/tonghuashun-ifind-skill/tree/main/tonghuashun-ifind`

补充：

- 当前发布版本：`0.4.5`
- Hermes 侧直接使用 GitHub skill 源，不再指向历史分支 PR

## 没有 iFinD 账号时怎么用

没有 iFinD 账号或本地没有 token，不代表这个 skill 不能用。

- `quote-realtime`、`quote-history`、`market-snapshot` 会自动回退到腾讯财经免费接口
- 涨停数据和 A 股榜单会自动回退到东方财富免费接口
- 只有 `fundamental-basic`、个股画像、资金流这类当前没有稳定公开源的问题，才应该明确告诉用户未覆盖

实测样例：

- `600004.SH` 在 `2026-04-21` 的免费历史源可返回开盘 `8.88`、收盘 `8.89`
- `600004.SH` 的免费实时源名称可返回 `白云机场`
- `600004.SH` 的免费单股快照可返回量比 `1.30`

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

## 命名接口目录

如果你不想让 Agent 直接手写 endpoint 字符串，先看当前已封装目录：

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-list
```

当前目录会返回一组带说明和样例 payload 的名字，例如：

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

然后再按名字调用：

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call \
  --name real_time_quote \
  --payload '{"codes":"600519.SH,000300.SH"}'
```

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call \
  --name history_quote \
  --payload '{"codes":"600004.SH","indicators":"open,close,high,low,volume","startdate":"2026-04-21","enddate":"2026-04-21"}'
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

python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "A股成交额榜前十"

python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "贵州茅台主营业务是什么"

python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "今天主力资金流入前十"
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
- A 股榜单查询会先走 iFinD，失败时自动回退到东方财富公开排行榜
- `fundamental-basic`、个股画像、资金流查询暂时没有公开源兜底

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

如果是涨停或榜单类请求，而且 iFinD 查询失败：

1. skill 会自动尝试东方财富公开接口
2. 返回结果里会标出 provider 为 `eastmoney`
3. 不需要 Agent 再手写第二套命令

如果 `smart-query` 返回需要手动查接口：

1. 先读 `references/routing.md`
2. 再看 `references/use-cases.md` 里是否已有类似问法
3. 再决定是否使用 `api-call`
4. 如果 `endpoint-list` 里已有合适名字，优先 `endpoint-call`
5. 如果文档里也找不到合适接口，就明确告诉用户当前 skill 未覆盖该 iFinD 能力
