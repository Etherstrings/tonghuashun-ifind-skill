from pathlib import Path


def test_readme_contains_chinese_donation_section():
    source = Path("README.md").read_text(encoding="utf-8")
    assert '## <a id="donate"></a>赞助支持' in source
    assert "https://ifdian.net/a/etherstrings" in source
    assert "docs/assets/donate/alipay.jpg" in source
    assert "docs/assets/donate/wechat.jpg" in source


def test_donate_images_exist():
    assert Path("docs/assets/donate/alipay.jpg").is_file()
    assert Path("docs/assets/donate/wechat.jpg").is_file()


def test_skill_docs_are_written_in_chinese():
    skill_source = Path("tonghuashun-ifind-skill/SKILL.md").read_text(encoding="utf-8")
    matrix_source = Path("tonghuashun-ifind-skill/references/capability-matrix.md").read_text(encoding="utf-8")
    usage_source = Path("tonghuashun-ifind-skill/references/usage.md").read_text(encoding="utf-8")
    routing_source = Path("tonghuashun-ifind-skill/references/routing.md").read_text(encoding="utf-8")
    cases_source = Path("tonghuashun-ifind-skill/references/use-cases.md").read_text(encoding="utf-8")
    readme_source = Path("README.md").read_text(encoding="utf-8")

    assert "# tonghuashun-ifind-skill" in skill_source
    assert "# 能力矩阵" in matrix_source
    assert "## 常见查询主入口" in usage_source
    assert "smart-query" in skill_source
    assert "# 路由规则" in routing_source
    assert "# 常见 Use Cases" in cases_source
    assert "强制鉴权" in readme_source


def test_docs_explain_mandatory_ifind_auth_usage():
    readme_source = Path("README.md").read_text(encoding="utf-8")
    matrix_source = Path("tonghuashun-ifind-skill/references/capability-matrix.md").read_text(encoding="utf-8")
    usage_source = Path("tonghuashun-ifind-skill/references/usage.md").read_text(encoding="utf-8")
    skill_source = Path("tonghuashun-ifind-skill/SKILL.md").read_text(encoding="utf-8")
    agent_source = Path("tonghuashun-ifind-skill/agents/openai.yaml").read_text(encoding="utf-8")

    assert "强制鉴权" in readme_source
    assert "所有已支持能力都要求 iFinD 鉴权" in matrix_source
    assert "不接入公开免费源" in matrix_source
    assert "当前不要假装能做" in matrix_source
    assert "必须先完成 iFinD 鉴权" in usage_source
    assert "强制 iFinD 鉴权" in skill_source
    assert "没有可用 iFinD token 时不要继续查询" in agent_source
    assert "auth-set-refresh-token" in readme_source
    assert "auth-set-refresh-token" in usage_source
    assert "auth-set-refresh-token" in skill_source
    assert "quantapi.51ifind.com/gwstatic/static/ds_web/quantapi-web/help-center/deploy.html" in skill_source
    assert "https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/super-command-web/index.html#/AccountDetails" in skill_source
    assert "Agent 必须这样引导用户取 token" in skill_source
    assert "Agent 对用户的标准引导" in usage_source
    assert "复制 refresh_token" in readme_source
    assert "只接收用户提供的 token" in skill_source
    assert "不接收 iFinD 用户名密码" in skill_source


def test_docs_make_install_and_natural_language_first_obvious():
    readme_source = Path("README.md").read_text(encoding="utf-8")
    skill_source = Path("tonghuashun-ifind-skill/SKILL.md").read_text(encoding="utf-8")
    usage_source = Path("tonghuashun-ifind-skill/references/usage.md").read_text(encoding="utf-8")
    matrix_source = Path("tonghuashun-ifind-skill/references/capability-matrix.md").read_text(encoding="utf-8")

    assert "bash scripts/install_skill.sh" in readme_source
    assert "~/.openclaw/workspace/skills/tonghuashun-ifind-skill" in skill_source
    assert "查询时永远先用自然语言入口" in skill_source
    assert "安装给 Agent 的最短路径" in usage_source
    assert "generic_smart_query" in matrix_source


def test_docs_include_endpoint_catalog_commands():
    readme_source = Path("README.md").read_text(encoding="utf-8")
    usage_source = Path("tonghuashun-ifind-skill/references/usage.md").read_text(encoding="utf-8")
    examples_source = Path("tonghuashun-ifind-skill/references/full-examples.md").read_text(encoding="utf-8")
    skill_source = Path("tonghuashun-ifind-skill/SKILL.md").read_text(encoding="utf-8")

    assert "endpoint-list" in readme_source
    assert "endpoint-call" in readme_source
    assert "endpoint-list" in usage_source
    assert "endpoint-call" in usage_source
    assert "endpoint-list" in examples_source
    assert "endpoint-call" in examples_source
    assert "endpoint-list" in skill_source
