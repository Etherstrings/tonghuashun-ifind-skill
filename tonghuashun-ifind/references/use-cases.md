# 常见 Use Cases

这份文件是给 Agent 看的快速案例库。

原则：

- 先找和用户问题最接近的案例
- 能用 `smart-query` 时不要先手写 `api-call`
- 如果案例和当前请求明显不匹配，就回到 `routing.md`

## 1. 个股最新价

用户问法：

- `看看贵州茅台现在股价`
- `宁德时代最新价`
- `查一下 600519 行情`

建议调用：

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query --query "看看贵州茅台现在股价"
```

预期路由：

- intent: `quote_realtime`
- endpoint: `/real_time_quotation`
- if iFinD fail: 自动回退到腾讯财经公开行情源

## 2. 个股近一段时间走势

用户问法：

- `看下宁德时代近一个月走势`
- `贵州茅台最近一周表现`
- `看 300750 历史行情`

建议调用：

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query --query "看下宁德时代近一个月走势"
```

预期路由：

- intent: `quote_history`
- endpoint: `/cmd_history_quotation`
- if iFinD fail: 自动回退到腾讯财经公开行情源

## 3. 大盘或指数快照

用户问法：

- `看一下大盘`
- `看看指数`
- `沪深300现在怎么样`

建议调用：

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query --query "看一下大盘"
```

预期路由：

- intent: `market_snapshot`
- endpoint: `/real_time_quotation`
- if iFinD fail: 自动回退到腾讯财经公开行情源

默认指数包：

- 上证指数
- 深证成指
- 创业板指
- 沪深300

## 4. 基础财务指标

用户问法：

- `看看宁德时代基本面`
- `贵州茅台估值怎么样`
- `看下 300750 的财务和市盈率`

建议调用：

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query --query "看看宁德时代基本面"
```

预期路由：

- intent: `fundamental_basic`
- endpoint: `/smart_stock_picking`
- if iFinD fail: 直接告知当前 skill 没有稳定覆盖公开源基本面能力

## 5. 不要乱猜的请求

## 5. 涨停数据

用户问法：

- `今天的A股涨停数据`
- `今日涨停`
- `涨停板`

建议调用：

```bash
python3 {baseDir}/scripts/ifind_cli.py smart-query --query "今天的A股涨停数据"
```

预期路由：

- intent: `limit_up_screen`
- endpoint: `/smart_stock_picking`
- if iFinD fail: 自动回退到东方财富公开涨停池

## 6. 不要乱猜的请求

用户问法：

- `帮我找贵州茅台公告PDF下载链接并按日期排序`
- `把所有年报原文下载地址列出来`
- `找公告附件全文`

处理方式：

1. 先运行 `smart-query`
2. 如果返回 `manual_api_lookup_required`，就读 `routing.md`
3. 如果仍没有明确接口，就直接告诉用户：

`当前 tonghuashun-ifind skill 没有稳定覆盖这个 iFinD 能力。`
