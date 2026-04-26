---
name: tonghuashun-ifind-skill
description: Use when the user needs Tonghuashun iFinD market, report, factor, screening, calendar, or other financial data, and all data must come from iFinD after successful authentication.
metadata:
  openclaw:
    requires:
      bins: ["python3"]
---

# tonghuashun-ifind-skill

当 OpenClaw、Hermes、Codex 或其他 Agent 需要给同花顺 iFinD 用户做金融数据查询时，优先使用这个 skill。

这个 skill 的产品定位只有一句话：给已经有同花顺 iFinD 账号的用户，一个能听懂自然语言的查询入口。

## 给安装 Agent 的最短指令

如果你是负责安装这个 skill 的 Agent，照下面做，不要发明其它路径：

```bash
bash scripts/install_skill.sh
```

安装结果必须是：

```text
~/.openclaw/workspace/skills/tonghuashun-ifind-skill
```

安装后先按同花顺 iFinD 官方方式完成鉴权：用户登录 iFinD 超级命令客户端或网页版账号详情，复制 `refresh_token`，再让 skill 换取并缓存 `access_token`。

Agent 必须这样引导用户取 token：

```text
请先打开同花顺 iFinD 超级命令客户端，进入账号详情，复制 refresh_token。
如果你用网页端，可以打开：
https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/super-command-web/index.html#/AccountDetails
登录后在账号详情里复制 refresh_token。复制后发给我，我会只用它换取 access_token 并缓存，不会要求你的同花顺用户名或密码。
```

```bash
python3 tonghuashun-ifind-skill/scripts/ifind_cli.py auth-set-refresh-token \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

如果用户已经给了双 token，才直接注入：

```bash
python3 tonghuashun-ifind-skill/scripts/ifind_cli.py auth-set-tokens \
  --access-token "$IFIND_ACCESS_TOKEN" \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

查询时永远先用自然语言入口：

```bash
python3 tonghuashun-ifind-skill/scripts/ifind_cli.py smart-query \
  --query "查一下贵州茅台近三年营收和毛利率"
```

## 核心规则

1. 强制 iFinD 鉴权：查询前必须有可用 `access_token`，或可用 `refresh_token` 能续期。
2. 所有数据只来自同花顺 iFinD API；不要使用腾讯财经、东方财富或其它公开源补数据。
3. 自然语言查询是第一入口：常见问题首选 `smart-query`，由 skill 负责把用户原话路由到 iFinD。
4. `quote-realtime`、`quote-history`、`market-snapshot`、`fundamental-basic` 是明确场景下的稳定命令。
5. 用户给正式中文股票名时，先用 iFinD `/smart_stock_picking` 查询股票代码和简称，再用解析出的代码调用行情/历史等稳定接口；不要维护全量本地股票表。
6. 用户给高频口语简称或昵称时，例如“茅台、宁王、招行、东财、工行、中芯、迈瑞、药明、平安”，允许用内置小型别名纠偏，避免 iFinD 把口语词误识别成无关股票；行情、财务、研报等实际数据仍必须来自 iFinD。
7. 涨停、A 股榜单、个股画像、资金流、公告、研报、龙虎榜、两融、北向、股东、持仓、分红、解禁、停复牌、概念板块和新股等 A 股常见查询，主要通过 `/smart_stock_picking` 走 iFinD；交易日 / 休市日走 `/date_sequence`。
8. 本地规则没看懂的自然语言问题，会默认交给 iFinD `/smart_stock_picking`，不要让 Agent 先手写 endpoint。
9. `api-call` 只用于高级兜底：`smart-query`、iFinD 自然语言透传和 `endpoint-list` / `endpoint-call` 都不够时再用。
10. 官方鉴权主路径是 `refresh_token -> /get_access_token -> access_token`；不要替用户完成浏览器登录。
11. 不要向用户回显 `access_token` 或 `refresh_token`。
12. 没有可用 iFinD token 时不要继续查询；先用上面的固定话术引导用户去 iFinD 超级命令账号详情复制 `refresh_token`，再执行 `auth-set-refresh-token`。
13. iFinD 返回错误、权限不足、账号无对应接口权限、名称歧义或无法识别证券名称时，直接说明 iFinD 调用失败或需要用户补充更精确名称/代码，不要切换到非同花顺数据源。

## 鉴权顺序

1. 先复用 `~/.openclaw/tonghuashun-ifind-skill/token_state.json` 里的缓存 token。
2. 如果 `access_token` 过期，自动使用 `refresh_token` 调用 `/get_access_token` 续期。
3. 如果没有可用 token，要求用户登录 iFinD 超级命令客户端或网页版账号详情，复制官方 `refresh_token`。
4. 拿到 `refresh_token` 后执行 `auth-set-refresh-token`，skill 会调用 `/get_access_token` 并保存双 token。
5. 只有用户已经明确提供 `access_token` 和 `refresh_token` 时，才执行 `auth-set-tokens`。
6. 只接收用户提供的 token，不替用户完成浏览器登录，不接收 iFinD 用户名密码。

用户问“token 在哪拿”时，直接回答：

1. 打开同花顺 iFinD 超级命令客户端，进入账号详情，复制 `refresh_token`。
2. 或打开网页版账号详情：`https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/super-command-web/index.html#/AccountDetails`。
3. 登录后找到并复制 `refresh_token`，只把这个 token 提供给 Agent。
4. Agent 执行 `auth-set-refresh-token --refresh-token "$IFIND_REFRESH_TOKEN"`。
5. 不要让用户提供同花顺用户名或密码，不要回显 token。

官方文档入口：

- iFinD HTTP 接口使用说明 / 鉴权说明：`https://quantapi.51ifind.com/gwstatic/static/ds_web/quantapi-web/help-center/deploy.html`
- iFinD Python HTTP 示例：`https://quantapi.51ifind.com/gwstatic/static/ds_web/quantapi-web/example.html`
- iFinD 网页版超级命令账号详情：`https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/super-command-web/index.html#/AccountDetails`

## 命令面

- `auth-set-refresh-token`
- `auth-set-tokens`
- `smart-query`
- `quote-realtime`
- `quote-history`
- `market-snapshot`
- `fundamental-basic`
- `endpoint-list`
- `endpoint-call`
- `api-call`
- `basic-data`
- `smart-pick`
- `report-query`
- `date-sequence`

## 调用建议

- 个股最新价、历史走势、大盘快照、基础财务指标、涨停数据、A 股榜单、个股画像、资金流、公告、研报、龙虎榜、两融、北向、股东、持仓、分红、解禁、停复牌、概念板块、新股、交易日、复杂筛选和行业/主题查询，优先用 `smart-query`。
- 用户输入正式中文股票名时，`smart-query` 会用 iFinD 自身能力解析证券代码；用户输入常见口语简称或昵称时，`smart-query` 会先做小型别名纠偏，再把请求发到 iFinD；如果名称仍有歧义，就让用户补充完整简称或 6 位代码。
- A 股常见问法只要不是明确的行情/历史行情/交易日稳定命令，就交给 iFinD；多数问题保留用户原话，少数“有啥/怎么样/啥消息”等口语会改写成 iFinD 更稳定的“最近公告/分红记录/研报”等正式词，不要把“分红/龙虎榜/公告/北向持股”等误路由成实时股价。
- 如果用户请求已经非常明确，也可以直接用稳定命令：`quote-realtime`、`quote-history`、`market-snapshot`、`fundamental-basic`。
- 如果没有可用 iFinD token，先用官方 `refresh_token` 鉴权，不要尝试其它数据源。
- 常见路由没命中时，`smart-query` 会把用户原话交给 iFinD `/smart_stock_picking`；只有 iFinD 也无法处理时，才看 `endpoint-list`。
- 只有在自然语言入口和命名接口目录都不够时，才去读 [references/routing.md](references/routing.md) 和 [references/use-cases.md](references/use-cases.md)，然后决定是否使用 `api-call`。
- payload 保持 iFinD 原始 JSON 对象，不要把 iFinD 查询语义二次改写成别的结构。
- 如果 `smart-query` 返回需要手动查接口，就先读本地路由文档和 use cases；如果文档里仍找不到合适接口，就明确告诉用户当前 skill 未覆盖该 iFinD 能力，不要乱猜 endpoint。

## 可选大模型路由

默认使用本地确定性路由。需要强化复杂自然语言解析时，可以启用 OpenAI-compatible Chat Completions 路由器：

```bash
export IFIND_ROUTE_LLM_ENABLED=1
export IFIND_ROUTE_LLM_API_KEY="$OPENAI_API_KEY"
export IFIND_ROUTE_LLM_MODEL="gpt-4o-mini"
```

可选变量：

- `IFIND_ROUTE_LLM_BASE_URL`
- `IFIND_ROUTE_LLM_TIMEOUT`
- `IFIND_ROUTE_LLM_MIN_CONFIDENCE`

大模型只允许输出 iFinD 路由计划。低置信度、无效返回或模型调用失败时，skill 会回到本地确定性路由。

## 外部页面

- ClawHub / OpenClaw: `https://clawhub.ai/etherstrings/tonghuashun-ifind`
- Hermes Agent GitHub skill 源: `https://github.com/Etherstrings/tonghuashun-ifind-skill/tree/main/tonghuashun-ifind-skill`

详细示例见 [references/usage.md](references/usage.md)，能力边界先看 [references/capability-matrix.md](references/capability-matrix.md)，路由规则见 [references/routing.md](references/routing.md)，常见用户问法示例见 [references/use-cases.md](references/use-cases.md)。如果要查看当前已封装的命名接口，直接运行 `endpoint-list`。
