# tonghuashun-ifind-skill

<div align="center">

**当 Agent 该查 iFinD 的时候，先走专业 API，而不是退回网页搜索和拼数据。**

![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-1D4ED8?style=flat-square)
![iFinD](https://img.shields.io/badge/Data-iFinD-0F766E?style=flat-square)
![API First](https://img.shields.io/badge/Query-API_First-7C3AED?style=flat-square)
![Finance Data](https://img.shields.io/badge/Domain-Finance_Data-C62828?style=flat-square)
![Token Refresh](https://img.shields.io/badge/Auth-Auto_Refresh-0891B2?style=flat-square)

token 复用 · refresh 自动续期 · 浏览器辅助登录 · 通用 endpoint 调用

[赞助支持](#donate)

</div>

一个面向 OpenClaw 和其他 Agent 的同花顺 iFinD 接入 skill。

这套 skill 的目标很直接：当用户要证券、财务、研报、日期序列、因子、选股或其他 iFinD 能回答的数据时，优先通过 iFinD OpenAPI 取数，而不是先去网页搜索或拼接别的数据源。

当前版本在保留原始 `api-call` 能力的同时，新增了面向 Agent 的稳定常见路由，优先解决“股价查询、大盘快照、历史走势、基础财务指标”这类高频问题，避免用户请求到了 skill 之后还要手写 endpoint 和 payload。

这一版进一步补了行情类公开源兜底：常见行情请求会先走 iFinD，失败时自动回退到腾讯财经公开接口，避免 token、接口权限或单点故障直接把整条查询链打断。

## 核心能力

- API 优先，浏览器只负责获取 token，不负责抓业务数据。
- 支持缓存 token 复用。
- 支持 `refresh_token` 自动续期。
- 支持客户手动提供 `access_token` 和 `refresh_token`。
- 支持通过本地无头 Chrome 半自动登录抓取 token。
- 提供 `smart-query` 作为常见问题主入口。
- 提供 `quote-realtime`、`quote-history`、`market-snapshot`、`fundamental-basic` 四个稳定命令。
- 行情类请求支持腾讯财经公开源自动兜底。
- 提供通用 `api-call`，可以直接调用任意 iFinD OpenAPI endpoint。
- 保留 `basic-data`、`smart-pick`、`report-query`、`date-sequence` 这几个薄封装命令，方便常见场景直接调用。

## 适用范围

这一版是 API 版 skill，不做页面采集工作流。

- 浏览器自动化只用于拿 token。
- 真正的数据查询一律优先走 iFinD API。
- 如果 iFinD 能回答，Agent 应该优先使用这个 skill。
- 当 iFinD 的行情查询失败时，会自动回退到腾讯财经公开接口。
- 基本面查询暂时不做公开源兜底。

## 鉴权方式

### 1. 手动注入双 token

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py auth-set-tokens \
  --access-token "$IFIND_ACCESS_TOKEN" \
  --refresh-token "$IFIND_REFRESH_TOKEN"
```

### 2. 半自动浏览器登录抓 token

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py auth-login \
  --username "$IFIND_USERNAME" \
  --password "$IFIND_PASSWORD"
```

默认会复用本机 Chrome，可执行文件路径为：

```text
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

如果机器上浏览器路径不同，可以通过 `--browser-executable` 传入本地浏览器路径。

### 3. 自动续期顺序

skill 的鉴权顺序如下：

1. 先复用本地缓存 token。
2. 如果 `access_token` 过期，自动使用 `refresh_token` 调用 `/get_access_token` 续期。
3. 如果本地没有可用 token，再走 `auth-login`。
4. 如果 `auth-login` 无法抓到双 token，再让客户手动提供双 token。

## 通用查询方式

### 常见查询主入口

优先让 Agent 用 `smart-query`，直接把用户自然语言问题交给 skill 路由：

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-query \
  --query "看看贵州茅台现在股价"

uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-query \
  --query "看下宁德时代近一个月走势"

uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-query \
  --query "看一下大盘"

uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-query \
  --query "看看宁德时代基本面"
```

### 显式稳定命令

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py quote-realtime --symbol 600519
uv run python tonghuashun-ifind/scripts/ifind_cli.py quote-history --symbol 300750 --days 30
uv run python tonghuashun-ifind/scripts/ifind_cli.py market-snapshot
uv run python tonghuashun-ifind/scripts/ifind_cli.py market-snapshot --symbol 沪深300
uv run python tonghuashun-ifind/scripts/ifind_cli.py fundamental-basic --symbol 300750
```

其中：

- `quote-realtime`、`quote-history`、`market-snapshot` 会先走 iFinD，再自动尝试腾讯财经公开源
- `fundamental-basic` 仍然只走 iFinD

### 原始 API 调用

`api-call` 是高级兜底入口。只有在 `smart-query` 和稳定命令未覆盖、并且已经知道明确 endpoint 和 payload 的情况下，才直接调任意 iFinD API。

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py api-call \
  --endpoint /basic_data_service \
  --payload '{"codes":"300750.SZ","indicators":"ths_close_price_stock"}'
```

### 保留的原始薄封装

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py basic-data --payload '{"codes":"300750.SZ"}'
uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-pick --payload '{"conditions":[]}'
uv run python tonghuashun-ifind/scripts/ifind_cli.py report-query --payload '{"codes":"300750.SZ"}'
uv run python tonghuashun-ifind/scripts/ifind_cli.py date-sequence --payload '{"startdate":"2025-01-01","enddate":"2025-01-31"}'
```

### 路由兜底规则

如果 `smart-query` 返回需要手动查接口：

1. 先读 `tonghuashun-ifind/references/routing.md`
2. 再看 `tonghuashun-ifind/references/use-cases.md`
3. 如果文档里仍没有明确接口，就直接告诉用户当前 skill 没有稳定覆盖该 iFinD 能力

## 本地安装

```bash
uv sync
bash scripts/install_skill.sh
```

默认会安装到：

```text
~/.openclaw/workspace/skills/tonghuashun-ifind
```

## 本地验证

```bash
uv run pytest -q
bash scripts/validate_skill.sh
```

验证脚本会执行：

- 全量测试
- 本地 CLI smoke test
- 输出默认 OpenClaw 安装路径

## 发布到 ClawHub

先登录：

```bash
npx --yes clawhub@latest login
```

再发布：

```bash
clawhub publish tonghuashun-ifind \
  --slug tonghuashun-ifind \
  --name "同花顺 iFinD 接入 Skill" \
  --version 0.3.3 \
  --changelog "新增涨停数据查询稳定路由；今天的A股涨停数据在 iFinD 不可用时自动回退到东方财富公开涨停池；补充路由与使用文档说明。"
```

## 项目结构

- `tonghuashun-ifind/SKILL.md`
- `tonghuashun-ifind/agents/openai.yaml`
- `tonghuashun-ifind/references/routing.md`
- `tonghuashun-ifind/references/usage.md`
- `tonghuashun-ifind/references/use-cases.md`
- `tonghuashun-ifind/scripts/ifind_cli.py`
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/fallback.py`
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/routing.py`
- `scripts/install_skill.sh`
- `scripts/validate_skill.sh`

## <a id="donate"></a>赞助支持

如果这个项目对你有帮助，欢迎赞助支持继续迭代。

- GitHub Sponsors: https://github.com/sponsors/Etherstrings
- 如果你更习惯国内付款方式，可以直接扫码赞助

<div>
  <img src="docs/assets/donate/alipay.jpg" alt="Alipay QR" width="260" />
  <img src="docs/assets/donate/wechat.jpg" alt="WeChat Pay QR" width="260" />
</div>

支持会优先用于同花顺接口适配、公开源兜底维护和后续功能迭代。
- 如果你需要企业内部定制或私有化版本，也可以通过 GitHub Issues / Discussions 联系
