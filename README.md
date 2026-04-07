# tonghuashun-ifind-skill

一个面向 OpenClaw 和其他 Agent 的同花顺 iFinD 接入 skill。

这套 skill 的目标很直接：当用户要证券、财务、研报、日期序列、因子、选股或其他 iFinD 能回答的数据时，优先通过 iFinD OpenAPI 取数，而不是先去网页搜索或拼接别的数据源。

## 核心能力

- API 优先，浏览器只负责获取 token，不负责抓业务数据。
- 支持缓存 token 复用。
- 支持 `refresh_token` 自动续期。
- 支持客户手动提供 `access_token` 和 `refresh_token`。
- 支持通过本地无头 Chrome 半自动登录抓取 token。
- 提供通用 `api-call`，可以直接调用任意 iFinD OpenAPI endpoint。
- 保留 `basic-data`、`smart-pick`、`report-query`、`date-sequence` 这几个薄封装命令，方便常见场景直接调用。

## 适用范围

这一版是 API 版 skill，不做页面采集工作流。

- 浏览器自动化只用于拿 token。
- 真正的数据查询一律优先走 iFinD API。
- 如果 iFinD 能回答，Agent 应该优先使用这个 skill。

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

### 原始 API 调用

`api-call` 是主入口。只要知道 endpoint 和 payload，就可以直接调任意 iFinD API。

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py api-call \
  --endpoint /basic_data_service \
  --payload '{"codes":"300750.SZ","indicators":"ths_close_price_stock"}'
```

### 常见薄封装

```bash
uv run python tonghuashun-ifind/scripts/ifind_cli.py basic-data --payload '{"codes":"300750.SZ"}'
uv run python tonghuashun-ifind/scripts/ifind_cli.py smart-pick --payload '{"conditions":[]}'
uv run python tonghuashun-ifind/scripts/ifind_cli.py report-query --payload '{"codes":"300750.SZ"}'
uv run python tonghuashun-ifind/scripts/ifind_cli.py date-sequence --payload '{"startdate":"2025-01-01","enddate":"2025-01-31"}'
```

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
  --version 0.2.0 \
  --changelog "补齐 refresh_token 自动续期，文档切换为中文并增加捐赠说明"
```

## 项目结构

- `tonghuashun-ifind/SKILL.md`
- `tonghuashun-ifind/agents/openai.yaml`
- `tonghuashun-ifind/references/usage.md`
- `tonghuashun-ifind/scripts/ifind_cli.py`
- `scripts/install_skill.sh`
- `scripts/validate_skill.sh`

## <a id="donate"></a>赞助支持

如果这个项目对你有帮助，欢迎通过 GitHub Sponsors 支持后续维护与同花顺接口适配。

- GitHub Sponsors: https://github.com/sponsors/Etherstrings
- 如果你需要企业内部定制或私有化版本，也可以通过 GitHub Issues / Discussions 联系
