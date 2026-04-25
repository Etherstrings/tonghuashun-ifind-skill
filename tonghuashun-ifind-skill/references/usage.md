# 使用说明

运行命令前，请先把 `{baseDir}` 替换成这个 skill 的目录。

如果要先判断“这件事到底能不能做、该走哪个入口”，先看：

- [能力矩阵](capability-matrix.md)

如果你要一份覆盖所有命令面的可抄完整例子，先看：

- [全面例子](full-examples.md)

## Skill 地址

- ClawHub / OpenClaw：
  `https://clawhub.ai/etherstrings/tonghuashun-ifind-skill`
- Hermes Agent GitHub skill 源：
  `https://github.com/Etherstrings/tonghuashun-ifind-skill/tree/main/tonghuashun-ifind-skill`

补充：

- 当前发布版本：`0.5.0`
- Hermes 侧直接使用 GitHub skill 源，不再指向历史分支 PR

## 必须先完成 iFinD 鉴权

这个版本强制所有数据来自同花顺 iFinD。

- 没有可用 token 时，查询命令返回 `auth_required`
- `refresh_token` 续期失败时，不再继续查其它来源
- iFinD API 返回错误、权限不足或账号无对应接口权限时，直接返回 iFinD 错误
- 不使用腾讯财经、东方财富或其它公开源补数据

官方鉴权主路径：

1. 用户登录 iFinD 超级命令客户端或网页版账号详情，复制 `refresh_token`
2. skill 调用 `/get_access_token` 换取 `access_token`
3. 数据接口请求头带 `access_token`

Agent 对用户的标准引导：

```text
请先打开同花顺 iFinD 超级命令客户端，进入账号详情，复制 refresh_token。
如果你用网页端，可以打开：
https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/super-command-web/index.html#/AccountDetails
登录后在账号详情里复制 refresh_token。复制后发给我，我会只用它换取 access_token 并缓存，不需要你的同花顺用户名或密码。
```

官方文档入口：

- iFinD HTTP 接口使用说明 / 鉴权说明：`https://quantapi.51ifind.com/gwstatic/static/ds_web/quantapi-web/help-center/deploy.html`
- iFinD Python HTTP 示例：`https://quantapi.51ifind.com/gwstatic/static/ds_web/quantapi-web/example.html`
- iFinD 网页版超级命令账号详情：`https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/super-command-web/index.html#/AccountDetails`

## 安装给 Agent 的最短路径

如果你是安装 Agent，执行：

```bash
bash scripts/install_skill.sh
```

安装目标必须是：

```text
~/.openclaw/workspace/skills/tonghuashun-ifind-skill
```

安装后不要先写 API payload，先让用户完成鉴权，然后用 `smart-query`。

## 官方 refresh_token 鉴权

用户提供 `refresh_token` 后，Agent 执行：

```bash
python3 {baseDir}/scripts/ifind_cli.py auth-set-refresh-token \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

## 手动注入双 token

```bash
python3 {baseDir}/scripts/ifind_cli.py auth-set-tokens \
  --access-token "$IFIND_ACCESS_TOKEN" \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

## 可选大模型路由

默认使用本地确定性路由。需要强化自然语言解析时，可以配置 OpenAI-compatible Chat Completions 服务：

```bash
export IFIND_ROUTE_LLM_ENABLED=1
export IFIND_ROUTE_LLM_API_KEY="$OPENAI_API_KEY"
export IFIND_ROUTE_LLM_MODEL="gpt-4o-mini"
```

可选变量：

- `IFIND_ROUTE_LLM_BASE_URL`
- `IFIND_ROUTE_LLM_TIMEOUT`
- `IFIND_ROUTE_LLM_MIN_CONFIDENCE`

大模型只负责输出 iFinD 路由计划；低置信度或模型调用失败时会回到本地规则。

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
- `a_share_common_query`
- `generic_smart_query`

然后再按名字调用：

```bash
python3 {baseDir}/scripts/ifind_cli.py endpoint-call \
  --name real_time_quote \
  --payload '{"codes":"600519.SH,000300.SH","indicators":"open,high,low,latest,changeRatio,change,preClose,volume,amount,turnoverRatio,volumeRatio,amplitude,pb"}'
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

python3 {baseDir}/scripts/ifind_cli.py smart-query \
  --query "筛一下新能源车产业链里市盈率低于30且近一个月放量的股票"
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

- `quote-realtime`、`quote-history`、`market-snapshot` 只走 iFinD
- 涨停数据和 A 股榜单只走 iFinD `/smart_stock_picking`
- `fundamental-basic`、个股画像、资金流查询只走 iFinD
- 复杂自然语言查询会透传到 iFinD `/smart_stock_picking`

## 保留的原始薄封装

```bash
python3 {baseDir}/scripts/ifind_cli.py basic-data --payload '{"codes":"300750.SZ"}'
python3 {baseDir}/scripts/ifind_cli.py smart-pick --payload '{"conditions":[]}'
python3 {baseDir}/scripts/ifind_cli.py report-query --payload '{"codes":"300750.SZ"}'
python3 {baseDir}/scripts/ifind_cli.py date-sequence --payload '{"startdate":"2025-01-01","enddate":"2025-01-31"}'
```

## 失败处理规则

如果没有官方 `refresh_token`，就让用户先登录 iFinD 超级命令客户端或网页版账号详情复制，不要尝试其它数据源。

如果查询命令返回 `auth_required`：

1. 先运行 `auth-set-refresh-token`
2. 如果用户已经有双 token，再运行 `auth-set-tokens`
3. 不要用公开源替代
4. 鉴权成功后重试原查询

如果 iFinD API 返回业务错误：

1. 保留返回里的 `errorcode` 和 `errmsg`
2. 告诉用户这是 iFinD 调用失败或权限问题
3. 不要自动切换到非同花顺数据源

如果 `smart-query` 返回需要手动查接口：

1. 先读 `references/routing.md`
2. 再看 `references/use-cases.md` 里是否已有类似问法
3. 再决定是否使用 `api-call`
4. 如果 `endpoint-list` 里已有合适名字，优先 `endpoint-call`
5. 如果文档里也找不到合适接口，就明确告诉用户当前 skill 未覆盖该 iFinD 能力
