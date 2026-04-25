# tonghuashun-ifind-skill

<div align="center">

**让 Agent 在该查同花顺 iFinD 的时候，清晰引导用户提供 token，所有数据只走 iFinD API。**

![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-1D4ED8?style=flat-square)
![ClawHub](https://img.shields.io/badge/Registry-ClawHub-0F766E?style=flat-square)
![Hermes](https://img.shields.io/badge/Agent-Hermes-7C3AED?style=flat-square)
![iFinD](https://img.shields.io/badge/Data-iFinD-C62828?style=flat-square)
![API First](https://img.shields.io/badge/Query-API_First-0891B2?style=flat-square)

强制鉴权 · token 复用 · refresh 自动续期 · 自然语言路由 · 可选大模型路由增强

[安装使用](tonghuashun-ifind-skill/references/usage.md) · [能力矩阵](tonghuashun-ifind-skill/references/capability-matrix.md) · [全面例子](tonghuashun-ifind-skill/references/full-examples.md) · [路由规则](tonghuashun-ifind-skill/references/routing.md) · [常见问法](tonghuashun-ifind-skill/references/use-cases.md) · [Skill 地址](#skill-links) · [赞助支持](#donate)

</div>

## <a id="donate"></a>赞助支持

如果这个项目对你有帮助，欢迎赞助支持继续迭代。

- 爱发电主页: https://ifdian.net/a/etherstrings
- 直接打赏: 使用下方你自己的支付宝 / 微信收款码

<div>
  <img src="docs/assets/donate/alipay.jpg" alt="Alipay QR" width="260" />
  <img src="docs/assets/donate/wechat.jpg" alt="WeChat Pay QR" width="260" />
</div>

支持会优先用于同花顺接口适配、自然语言路由维护和后续功能迭代。

## 1. Agent 快速安装

如果你是负责安装和调用的 Agent，按下面顺序执行，不要改名字，也不要猜路径：

```bash
bash scripts/install_skill.sh
```

安装后 skill 目录应是：

```text
~/.openclaw/workspace/skills/tonghuashun-ifind-skill
```

然后先按 iFinD 官方方式鉴权：用户登录 iFinD 超级命令客户端或网页版账号详情，复制 `refresh_token`，再让 skill 换取并缓存 `access_token`。

Agent 可以直接这样提示用户：

```text
请先打开同花顺 iFinD 超级命令客户端，进入账号详情，复制 refresh_token。
如果你用网页端，可以打开：
https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/super-command-web/index.html#/AccountDetails
登录后在账号详情里复制 refresh_token。复制后发给我，我会只用它换取 access_token 并缓存，不需要你的同花顺用户名或密码。
```

```bash
python3 tonghuashun-ifind-skill/scripts/ifind_cli.py auth-set-refresh-token \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

如果用户已经给了双 token：

```bash
python3 tonghuashun-ifind-skill/scripts/ifind_cli.py auth-set-tokens \
  --access-token "$IFIND_ACCESS_TOKEN" \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

查询时优先自然语言：

```bash
python3 tonghuashun-ifind-skill/scripts/ifind_cli.py smart-query \
  --query "查一下贵州茅台近三年营收和毛利率"
```

## 2. 能力简介

`tonghuashun-ifind-skill` 是一个面向同花顺 iFinD 用户和终端 Agent 的自然语言金融查询 skill。

目标很直接：

- 当用户问的是证券、财务、筛选、日期序列、研报等 iFinD 明显更适合回答的数据时，优先走 iFinD OpenAPI
- 当用户问的是常见 A 股问题时，不让 Agent 先手写 endpoint 和 payload，而是优先走 `smart-query`
- 当用户输入正式中文股票名时，先用 iFinD 自己的自然语言能力查股票代码/简称，再把代码用于行情、历史等稳定接口
- 当用户用“茅台、宁王、招行、东财、工行、中芯、迈瑞、药明、平安”这类口语简称时，用小型别名纠偏避免误识别；实际行情、财务、研报和筛选数据仍只从 iFinD 获取
- 本地规则没覆盖的复杂筛选、行业主题、财务组合问法，会透传给 iFinD `/smart_stock_picking`
- 所有数据查询都要求先完成 iFinD 鉴权；没有可用 token 时不再回退到公开免费源
- 可选启用大模型路由器，辅助把复杂自然语言问法映射到稳定 iFinD endpoint 和 payload

官方鉴权文档入口：

- iFinD HTTP 接口使用说明 / 鉴权说明：`https://quantapi.51ifind.com/gwstatic/static/ds_web/quantapi-web/help-center/deploy.html`
- iFinD Python HTTP 示例：`https://quantapi.51ifind.com/gwstatic/static/ds_web/quantapi-web/example.html`
- iFinD 网页版超级命令账号详情：`https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/super-command-web/index.html#/AccountDetails`

用户取 token 的最短路径：

1. 打开同花顺 iFinD 超级命令客户端，进入账号详情。
2. 或打开网页版账号详情：`https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/super-command-web/index.html#/AccountDetails`。
3. 登录后复制 `refresh_token`。
4. 把 `refresh_token` 提供给 Agent，Agent 执行 `auth-set-refresh-token`。
5. 不需要提供同花顺用户名或密码。

当前稳定覆盖：

- 个股实时行情
- 个股历史走势
- 大盘 / 指数快照
- 基础财务指标
- 涨停数据
- A 股榜单
- 个股画像 / 主营业务
- 资金流相关问法
- 公告 / 研报 / 评级
- 龙虎榜 / 大宗交易 / 异动
- 融资融券 / 北向资金 / 股东持仓
- 分红派息 / 解禁 / 停复牌
- 概念板块 / 新股申购 / 交易日

相关文档：

- [使用说明](tonghuashun-ifind-skill/references/usage.md)
- [能力矩阵](tonghuashun-ifind-skill/references/capability-matrix.md)
- [全面例子](tonghuashun-ifind-skill/references/full-examples.md)
- [路由规则](tonghuashun-ifind-skill/references/routing.md)
- [常见 Use Cases](tonghuashun-ifind-skill/references/use-cases.md)
- [Skill 定义](tonghuashun-ifind-skill/SKILL.md)

---

## 3. 强制鉴权与路由

主入口：

- `smart-query`

显式稳定命令：

- `quote-realtime`
- `quote-history`
- `market-snapshot`
- `fundamental-basic`
- `endpoint-list`
- `endpoint-call`

默认策略：

1. 查询前必须先拿到可用 iFinD token
2. 所有行情、历史、榜单、画像、资金流、研报和日期序列数据都只从 iFinD 获取
3. iFinD 鉴权失败、接口失败或权限不足时直接返回 iFinD 错误，不再切换公开源
4. 高频问法优先走 `smart-query`；常见路由不够时再看 `endpoint-list` / `endpoint-call`
5. 自然语言没被本地规则稳定命中时，默认进入 iFinD `/smart_stock_picking`
6. 可选 LLM 路由器只负责生成 iFinD 调用计划，不允许规划其它数据源

当前 iFinD 路由方向：

| 能力 | iFinD 路由 | 说明 |
|------|------------|------|
| 实时行情 | `/real_time_quotation` | 必须鉴权 |
| 历史走势 | `/cmd_history_quotation` | 必须鉴权 |
| 大盘快照 | `/real_time_quotation` | 必须鉴权 |
| 涨停数据 | `/smart_stock_picking` | 必须鉴权 |
| A 股榜单 | `/smart_stock_picking` | 必须鉴权 |
| 基础财务 / 画像 / 资金流 | `/smart_stock_picking` | 必须鉴权 |
| 公告、研报、龙虎榜、两融、北向、股东、持仓、分红、解禁、停复牌、概念板块、新股 | `/smart_stock_picking` | 默认保留自然语言原话；少数口语会改写成 iFinD 更稳定的正式词 |
| 交易日 / 休市日 | `/date_sequence` | 返回的 `time` 字段为 iFinD 交易日序列 |
| 复杂自然语言筛选 | `/smart_stock_picking` | 本地规则未命中时透传 |

中文股票名解析：

- `smart-query --query "请问贵州茅台最近股价怎么样"` 会先向 iFinD 查询股票代码/简称。
- iFinD 返回 `600519.SH` 后，再调用 `/real_time_quotation`。
- `smart-query --query "宁王今天咋样"` 这类口语昵称会先纠偏到 `宁德时代 300750.SZ`，再调用 iFinD 行情接口。
- 如果名称歧义或 iFinD 未识别，Agent 应要求用户补充完整简称或 6 位代码。

### 3.1 没有 iFinD 账号时

如果没有 iFinD 账号，或者本地没有可用 token，这个 skill 会返回 `auth_required`，并提示先执行 `auth-set-refresh-token`，或在已有双 token 时执行 `auth-set-tokens`。

这个版本不接入公开免费源，因此不会再用腾讯财经、东方财富或其它非同花顺来源补数据。

### 3.2 可选大模型路由增强

默认路由仍然是本地确定性规则。需要增强复杂自然语言解析时，可以配置 OpenAI-compatible Chat Completions 服务：

```bash
export IFIND_ROUTE_LLM_ENABLED=1
export IFIND_ROUTE_LLM_API_KEY="$OPENAI_API_KEY"
export IFIND_ROUTE_LLM_MODEL="gpt-4o-mini"
```

可选配置：

- `IFIND_ROUTE_LLM_BASE_URL`：默认 `https://api.openai.com/v1`
- `IFIND_ROUTE_LLM_TIMEOUT`：默认 `12`
- `IFIND_ROUTE_LLM_MIN_CONFIDENCE`：默认 `0.65`

LLM 只输出 iFinD 路由计划；低置信度、无效 JSON 或模型调用失败时，会自动回到本地确定性路由。

---

## 4. Skill 地址

<a id="skill-links"></a>

当前两个外部 skill 入口已经固定下来：

- ClawHub / OpenClaw 页面：
  `https://clawhub.ai/etherstrings/tonghuashun-ifind-skill`
- Hermes Agent GitHub skill 源：
  `https://github.com/Etherstrings/tonghuashun-ifind-skill/tree/main/tonghuashun-ifind-skill`

补充说明：

- 当前准备发布版本：`0.5.0`
- Hermes 侧直接使用 GitHub skill 源，不再指向历史分支 PR

---

## 5. 安装与鉴权

### 5.1 本地安装

```bash
uv sync
bash scripts/install_skill.sh
```

默认会安装到：

```text
~/.openclaw/workspace/skills/tonghuashun-ifind-skill
```

### 5.2 官方 refresh_token 鉴权

```bash
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py auth-set-refresh-token \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

### 5.3 手动注入双 token

```bash
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py auth-set-tokens \
  --access-token "$IFIND_ACCESS_TOKEN" \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

鉴权顺序：

1. 查询命令先复用本地缓存 token
2. `access_token` 过期时自动用 `refresh_token` 请求 `/get_access_token` 续期
3. 没有可用 token 时，查询命令会要求先用官方 `refresh_token` 鉴权
4. 不替用户完成浏览器登录，不接收 iFinD 用户名密码

---

## 6. 使用方式

### 6.1 常见查询主入口

```bash
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py smart-query \
  --query "看看贵州茅台现在股价"

uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py smart-query \
  --query "今天的A股涨停数据"

uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py smart-query \
  --query "A股成交额榜前十"

uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py smart-query \
  --query "贵州茅台主营业务是什么"

uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py smart-query \
  --query "今天主力资金流入前十"
```

### 6.2 显式稳定命令

```bash
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py quote-realtime --symbol 600519
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py quote-history --symbol 300750 --days 30
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py market-snapshot
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py fundamental-basic --symbol 300750
```

### 6.3 原始 API 调用

```bash
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py api-call \
  --endpoint /basic_data_service \
  --payload '{"codes":"300750.SZ","indicators":"ths_close_price_stock"}'
```

### 6.4 命名接口目录

如果 Agent 不想手写 endpoint 字符串，先列出当前已封装目录：

```bash
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py endpoint-list
```

当前会返回一组带说明和样例 payload 的名字，例如：

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

然后按名字调用：

```bash
uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py endpoint-call \
  --name history_quote \
  --payload '{"codes":"600004.SH","indicators":"open,close,high,low,volume","startdate":"2026-04-21","enddate":"2026-04-21"}'
```

推荐顺序：

1. 高频问法先用 `smart-query`
2. 已知稳定路由时用 `quote-realtime`、`quote-history`、`market-snapshot`、`fundamental-basic`
3. 需要更多已封装接口时先看 `endpoint-list`，再用 `endpoint-call`
4. 只有这些都不够时才直接写 `api-call`

---

## 7. 验证与发布

### 7.1 本地验证

```bash
uv run pytest -q
bash scripts/validate_skill.sh
```

### 7.2 发布到 ClawHub

```bash
npx --yes clawhub@latest login

clawhub publish tonghuashun-ifind-skill \
  --slug tonghuashun-ifind-skill \
  --name "tonghuashun-ifind-skill" \
  --version 0.5.0 \
  --changelog "改为强制 iFinD 鉴权，移除公开免费源兜底，并新增可选 LLM 自然语言路由增强。"
```

---

## 8. 项目结构

- `tonghuashun-ifind-skill/SKILL.md`
- `tonghuashun-ifind-skill/agents/openai.yaml`
- `tonghuashun-ifind-skill/references/routing.md`
- `tonghuashun-ifind-skill/references/usage.md`
- `tonghuashun-ifind-skill/references/use-cases.md`
- `tonghuashun-ifind-skill/scripts/ifind_cli.py`
- `tonghuashun-ifind-skill/scripts/runtime/tonghuashun_ifind_skill/routing.py`
- `tonghuashun-ifind-skill/scripts/runtime/tonghuashun_ifind_skill/llm_routing.py`
- `scripts/install_skill.sh`
- `scripts/validate_skill.sh`
