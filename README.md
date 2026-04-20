# tonghuashun-ifind-skill

<div align="center">

**让 Agent 在该查同花顺 iFinD 的时候，先走专业 API，再按能力回退到稳定公开源。**

![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-1D4ED8?style=flat-square)
![ClawHub](https://img.shields.io/badge/Registry-ClawHub-0F766E?style=flat-square)
![Hermes](https://img.shields.io/badge/Agent-Hermes-7C3AED?style=flat-square)
![iFinD](https://img.shields.io/badge/Data-iFinD-C62828?style=flat-square)
![API First](https://img.shields.io/badge/Query-API_First-0891B2?style=flat-square)

token 复用 · refresh 自动续期 · 自然语言路由 · A 股公开源兜底

[安装使用](tonghuashun-ifind/references/usage.md) · [全面例子](tonghuashun-ifind/references/full-examples.md) · [路由规则](tonghuashun-ifind/references/routing.md) · [常见问法](tonghuashun-ifind/references/use-cases.md) · [Skill 地址](#skill-links) · [赞助支持](#donate)

</div>

## <a id="donate"></a>赞助支持

如果这个项目对你有帮助，欢迎赞助支持继续迭代。

- GitHub Sponsors: https://github.com/sponsors/Etherstrings
- 如果你更习惯国内付款方式，可以直接扫码赞助

<div>
  <img src="docs/assets/donate/alipay.jpg" alt="Alipay QR" width="260" />
  <img src="docs/assets/donate/wechat.jpg" alt="WeChat Pay QR" width="260" />
</div>

支持会优先用于同花顺接口适配、公开源兜底维护和后续功能迭代。

## 1. 能力简介

`tonghuashun-ifind-skill` 是一个面向 OpenClaw、Hermes Agent 和其它终端 Agent 的同花顺 iFinD 接入仓库。

目标很直接：

- 当用户问的是证券、财务、筛选、日期序列、研报等 iFinD 明显更适合回答的数据时，优先走 iFinD OpenAPI
- 当用户问的是常见 A 股问题时，不让 Agent 先手写 endpoint 和 payload，而是优先走稳定自然语言路由
- 当 iFinD 不可用时，对能公开兜底的问题自动切到稳定免费接口，避免整条链路直接断掉

当前稳定覆盖：

- 个股实时行情
- 个股历史走势
- 大盘 / 指数快照
- 基础财务指标
- 涨停数据
- A 股榜单
- 个股画像 / 主营业务
- 资金流相关问法

相关文档：

- [使用说明](tonghuashun-ifind/references/usage.md)
- [全面例子](tonghuashun-ifind/references/full-examples.md)
- [路由规则](tonghuashun-ifind/references/routing.md)
- [常见 Use Cases](tonghuashun-ifind/references/use-cases.md)
- [Skill 定义](tonghuashun-ifind/SKILL.md)

---

## 2. 路由与兜底

主入口：

- `smart-query`

显式稳定命令：

- `quote-realtime`
- `quote-history`
- `market-snapshot`
- `fundamental-basic`

默认策略：

1. 优先走 iFinD
2. 如果是行情类请求，失败时自动回退到腾讯财经公开行情源
3. 如果是涨停或 A 股榜单请求，失败时自动回退到东方财富公开接口
4. 如果是基本面、个股画像、资金流且当前没有稳定公开源，就明确返回未覆盖，而不是乱猜接口

当前公开源回退方向：

| 能力 | iFinD 路由 | 免费回退 |
|------|------------|----------|
| 实时行情 | `/real_time_quotation` | 腾讯财经 |
| 历史走势 | `/cmd_history_quotation` | 腾讯财经 |
| 大盘快照 | `/real_time_quotation` | 腾讯财经 |
| 涨停数据 | `/smart_stock_picking` | 东方财富涨停池 |
| A 股榜单 | `/smart_stock_picking` | 东方财富排行榜 |

---

## 3. Skill 地址

<a id="skill-links"></a>

当前两个外部 skill 入口已经固定下来：

- ClawHub / OpenClaw 页面：
  `https://clawhub.ai/etherstrings/tonghuashun-ifind`
- Hermes Agent GitHub skill 源：
  `https://github.com/Etherstrings/tonghuashun-ifind-skill/tree/add-skill-tonghuashun-ifind/skills/tonghuashun-ifind`

补充说明：

- Hermes 当前对应的发布 PR：
  `https://github.com/Etherstrings/tonghuashun-ifind-skill/pull/1`
- 当前准备发布版本：`0.4.1`
- 当前 Hermes 分支镜像目标版本：`0.4.1`

---

## 4. 安装与鉴权

### 4.1 本地安装

```bash
uv sync
bash scripts/install_skill.sh
```

默认会安装到：

```text
~/.openclaw/workspace/skills/tonghuashun-ifind
```

### 4.2 手动注入双 token

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py auth-set-tokens \
  --access-token "$IFIND_ACCESS_TOKEN" \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

### 4.3 半自动浏览器登录

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py auth-login \
  --username "$IFIND_USERNAME" \
  --password "$IFIND_PASSWORD"
```

默认浏览器路径：

```text
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

鉴权顺序：

1. 优先复用本地缓存 token
2. `access_token` 过期时自动用 `refresh_token` 续期
3. 没有可用 token 时才走 `auth-login`
4. 浏览器抓不到双 token 时，再改为手动注入

---

## 5. 使用方式

### 5.1 常见查询主入口

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-query \
  --query "看看贵州茅台现在股价"

uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-query \
  --query "今天的A股涨停数据"

uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-query \
  --query "A股成交额榜前十"

uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-query \
  --query "贵州茅台主营业务是什么"

uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-query \
  --query "今天主力资金流入前十"
```

### 5.2 显式稳定命令

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py quote-realtime --symbol 600519
uv run python tonghuashun-ifind/scripts/ifind_cli.py quote-history --symbol 300750 --days 30
uv run python tonghuashun-ifind/scripts/ifind_cli.py market-snapshot
uv run python tonghuashun-ifind/scripts/ifind_cli.py fundamental-basic --symbol 300750
```

### 5.3 原始 API 调用

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py api-call \
  --endpoint /basic_data_service \
  --payload '{"codes":"300750.SZ","indicators":"ths_close_price_stock"}'
```

---

## 6. 验证与发布

### 6.1 本地验证

```bash
uv run pytest -q
bash scripts/validate_skill.sh
```

### 6.2 发布到 ClawHub

```bash
npx --yes clawhub@latest login

clawhub publish tonghuashun-ifind \
  --slug tonghuashun-ifind \
  --name "同花顺 iFinD 接入 Skill" \
  --version 0.4.1 \
  --changelog "补充全面例子文档；统一 README、usage 和 skill 外部地址说明；完善所有命令面的真实 A 股示例。"
```

---

## 7. 项目结构

- `tonghuashun-ifind/SKILL.md`
- `tonghuashun-ifind/agents/openai.yaml`
- `tonghuashun-ifind/references/routing.md`
- `tonghuashun-ifind/references/usage.md`
- `tonghuashun-ifind/references/use-cases.md`
- `tonghuashun-ifind/scripts/ifind_cli.py`
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/routing.py`
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/fallback.py`
- `scripts/install_skill.sh`
- `scripts/validate_skill.sh`
