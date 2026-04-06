# 同花顺 iFinD OpenClaw Skill 设计说明

- 日期：2026-04-06
- 状态：已批准，进入计划编写前的设计冻结
- 主题：面向 OpenClaw / ClawHub 的同花顺 iFinD API 接入 skill

## 1. 产品定义

这个项目是一个单独的 OpenClaw skill，它只做三件事：

1. 优先通过无头 `Playwright` 自动登录并获取可用的 iFinD token；
2. 自动获取失败时，允许客户手动提供 `access_token` 和 `refresh_token`；
3. 为 OpenClaw 或其他 Agent 提供可直接调用的同花顺 iFinD OpenAPI 能力。

这个项目不是：

1. 通用证券数据平台；
2. 多数据源路由器；
3. 基于网页页面抓取数据的产品。

浏览器在 v1 中只用于登录和抓 token。  
数据查询平面是 `API-only`。

## 2. 目标

### 2.1 必做目标

1. 以标准 OpenClaw skill 形式交付。
2. 默认优先降低客户参与成本，先尝试无头自动登录。
3. 无头自动登录失败时，支持手动注入 `access_token` 和 `refresh_token`。
4. 让通用 iFinD API 调用成为 skill 的主合同。
5. 只补一层很薄的高频接口封装，不做重语义抽象。
6. 缓存并复用 token，避免每次调用都重新登录。
7. 本地验证通过后，独立发布到 GitHub 和 ClawHub / OpenClaw。

### 2.2 明确不做

1. 不做复杂的财经业务语义层。
2. 不做非 iFinD 数据源 fallback。
3. 不做 F10 页面抓取、网页内容提取等非 API 能力。
4. 不做常驻服务或额外网关。
5. 不承诺在 v1 就把全部 iFinD endpoint 都预封装完。通用 raw API 调用才是覆盖策略。

## 3. 用户体验

理想调用流程如下：

1. Agent 调用 skill。
2. skill 先检查本地是否已有可用 token。
3. 如果没有可用 token，skill 自动尝试无头 `Playwright` 登录。
4. 如果自动获取成功，skill 立刻发起 API 查询。
5. 如果自动获取失败，skill 明确要求客户手动提供 `access_token` 和 `refresh_token`。
6. 一旦 token 可用，后续相同环境下的查询应尽量复用，不再重复完整登录流程。

也就是说，客户默认不需要介入，只有自动化失败时才需要人工补 token。

## 4. 主能力模型

这个 skill 采用 `raw-first` 设计。

主调用合同是一个通用 API 调用入口，例如：

```json
{
  "endpoint": "/basic_data_service",
  "payload": {
    "codes": "300750.SZ",
    "indipara": []
  }
}
```

skill 负责：

1. 确保当前存在可用 token；
2. 自动附加 `access_token` 请求头；
3. 发起真实 iFinD API 请求；
4. 以统一返回结构将结果交还给调用方。

在此基础上，只附带少量薄封装：

1. `basic-data`
2. `smart-pick`
3. `report-query`
4. `date-sequence`

这些命令本质上都必须复用同一个通用 client，不允许形成多套独立调用栈。

## 5. Skill 对外能力面

v1 的 OpenClaw skill 命令面固定为：

1. `auth-login`
2. `auth-set-tokens`
3. `api-call`
4. `basic-data`
5. `smart-pick`
6. `report-query`
7. `date-sequence`

### 5.1 `auth-login`

执行无头 `Playwright` 登录，尝试获取 `access_token` 和 `refresh_token`。

### 5.2 `auth-set-tokens`

接收客户手动提供的 `access_token` 和 `refresh_token`，写入本地状态，并做一次轻量校验。

### 5.3 `api-call`

主通用入口。允许传任意 API endpoint 和 payload。

### 5.4 高频薄封装命令

`basic-data`、`smart-pick`、`report-query`、`date-sequence` 只做参数整理，再转发到 `api-call`。

## 6. 认证设计

认证状态机固定为：

1. 先尝试本地缓存的 `access_token`；
2. 如果 `access_token` 过期或被拒绝，再尝试 `refresh_token`；
3. 如果 refresh 失败或根本没有 refresh token，再尝试无头 `Playwright` 自动登录；
4. 如果自动登录失败，则要求客户手动提供 token。

### 6.1 自动登录

无头 `Playwright` 在 v1 中只用于登录和 token 发现。

自动化流程：

1. 打开登录页；
2. 自动填写账号密码；
3. 提交登录；
4. 观察网络请求、响应和浏览器存储变化；
5. 优先抓取 `refresh_token`；
6. 同时抓取可用的 `access_token`；
7. 用一个轻量 API 调用校验 token 是否真实可用。

### 6.2 Token 抓取优先级

token 抓取优先级固定为：

1. 登录相关接口的响应体；
2. 请求头；
3. `localStorage` / `sessionStorage`；
4. cookie。

### 6.3 存储规则

1. `refresh_token` 是长期凭证。
2. `access_token` 是短期缓存凭证，必须带过期元数据。
3. 用户名密码默认不长期落盘。
4. 日志中不得输出账号、密码或原始 token。

## 7. 数据流

### 7.1 `api-call` 数据流

1. 接收命令输入；
2. 认证层解析可用 token；
3. 通用 client 向指定 endpoint 发起请求；
4. 检查 HTTP 错误和 iFinD 业务错误；
5. 用统一 envelope 返回给调用方。

### 7.2 高频封装命令数据流

1. 封装命令接收较简化参数；
2. 命令内部构造标准 endpoint 和 payload；
3. 转发给 `api-call`；
4. 共享响应处理逻辑返回结果。

## 8. 返回合同

所有命令统一返回如下薄结构：

```json
{
  "ok": true,
  "endpoint": "/basic_data_service",
  "token_source": "cache|refresh|playwright|manual",
  "data": {},
  "error": null,
  "meta": {
    "timestamp": "2026-04-06T00:00:00Z"
  }
}
```

失败时：

```json
{
  "ok": false,
  "endpoint": "/basic_data_service",
  "token_source": "playwright",
  "data": null,
  "error": {
    "type": "auth_failed|token_invalid|api_failed|runtime_failed",
    "message": "..."
  },
  "meta": {
    "timestamp": "2026-04-06T00:00:00Z"
  }
}
```

如果 iFinD 自身返回 `errorcode` / `errmsg`，skill 必须尽量保留原始错误细节，而不是过度包装成模糊描述。

## 9. 错误处理

v1 只保留四类错误：

1. `auth_failed`
2. `token_invalid`
3. `api_failed`
4. `runtime_failed`

处理规则：

1. `access_token` 失败时，先尝试 refresh；
2. refresh 失败时，再尝试无头登录；
3. 无头登录失败后，再要求客户手动给 token；
4. iFinD 业务报错时，原样暴露业务错误信息；
5. Playwright、脚本、网络、解析异常归入 `runtime_failed`。

## 10. 项目结构

仓库结构尽量保持最小：

```text
tonghuashun-ifind-skill/
├── README.md
├── pyproject.toml
├── scripts/
│   ├── install_skill.sh
│   └── validate_skill.sh
└── tonghuashun-ifind/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── references/
    │   └── usage.md
    └── scripts/
        ├── ifind_cli.py
        └── runtime/
            └── tonghuashun_ifind_skill/
                ├── auth.py
                ├── browser_login.py
                ├── client.py
                ├── state.py
                └── models.py
```

其中：

1. 仓库根目录负责开发、验证、发布；
2. `tonghuashun-ifind/` 是真正被 OpenClaw 安装的 skill 包；
3. `runtime/` 是 skill 背后的 Python 实现。

## 11. 验证计划

验证范围必须直接服务于真实目标。

### 11.1 本地验证

1. `auth-login` 能执行无头登录尝试；
2. `auth-set-tokens` 能接受手动 token 并完成校验；
3. `api-call` 能调用任意指定 endpoint；
4. `basic-data` 至少成功一次；
5. `smart-pick` 至少成功一次；
6. `report-query` 至少成功一次；
7. `date-sequence` 至少成功一次。

### 11.2 OpenClaw 验证

1. OpenClaw 能识别并加载该 skill；
2. skill 的一次真实调用能完成登录路径和查询路径；
3. 重复调用时能复用缓存 token。

### 11.3 回退验证

1. 人为模拟自动登录失败；
2. 验证手动 token 注入后可以恢复正常查询。

## 12. 发布路径

发布顺序固定为：

1. 完成本地实现；
2. 本地验证通过；
3. 创建独立 GitHub 仓库；
4. 推送代码；
5. 安装到本机 OpenClaw 并再次验证；
6. 发布到 ClawHub / OpenClaw。

这样可以避免发布一个只能在源码里跑、却不能真正作为 skill 使用的仓库。

## 13. 验收标准

以下条件全部满足时，视为该设计完成：

1. OpenClaw 能识别该 skill；
2. 无头 `Playwright` 能尝试自动登录并抓 token；
3. 自动登录失败时，手动 token 注入可用；
4. `api-call` 能调用任意指定 iFinD endpoint；
5. `basic_data`、`smart_stock_picking`、`report_query`、`date_sequence` 四类高频接口都至少成功一次；
6. token 能缓存并复用；
7. 项目以独立 GitHub 仓库形式发布；
8. skill 成功发布到 ClawHub / OpenClaw。

## 14. 明确延后到 v1 之后的问题

以下事项不纳入 v1：

1. 继续预封装更多 iFinD endpoint；
2. F10 页面抓取等浏览器数据抽取能力；
3. 更重的 SDK 风格接口层；
4. 非 iFinD 数据源 fallback；
5. 建立 raw API 之上的复杂财经业务语义层。
