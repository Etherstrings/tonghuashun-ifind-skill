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
    skill_source = Path("tonghuashun-ifind/SKILL.md").read_text(encoding="utf-8")
    matrix_source = Path("tonghuashun-ifind/references/capability-matrix.md").read_text(encoding="utf-8")
    usage_source = Path("tonghuashun-ifind/references/usage.md").read_text(encoding="utf-8")
    routing_source = Path("tonghuashun-ifind/references/routing.md").read_text(encoding="utf-8")
    cases_source = Path("tonghuashun-ifind/references/use-cases.md").read_text(encoding="utf-8")
    readme_source = Path("README.md").read_text(encoding="utf-8")

    assert "# 同花顺 iFinD 接入 Skill" in skill_source
    assert "# 能力矩阵" in matrix_source
    assert "## 常见查询主入口" in usage_source
    assert "smart-query" in skill_source
    assert "# 路由规则" in routing_source
    assert "# 常见 Use Cases" in cases_source
    assert "腾讯财经" in readme_source


def test_docs_explain_supported_no_ifind_fallback_usage():
    readme_source = Path("README.md").read_text(encoding="utf-8")
    matrix_source = Path("tonghuashun-ifind/references/capability-matrix.md").read_text(encoding="utf-8")
    usage_source = Path("tonghuashun-ifind/references/usage.md").read_text(encoding="utf-8")
    skill_source = Path("tonghuashun-ifind/SKILL.md").read_text(encoding="utf-8")
    agent_source = Path("tonghuashun-ifind/agents/openai.yaml").read_text(encoding="utf-8")

    assert "没有 iFinD 账号时也能用什么" in readme_source
    assert "同花顺和免费源都能拿到" in matrix_source
    assert "只有 iFinD 稳定可用" in matrix_source
    assert "当前不要假装能做" in matrix_source
    assert "没有 iFinD 账号时怎么用" in usage_source
    assert "没有 iFinD 账号" in skill_source
    assert "没有 iFinD 账号或鉴权失败" in agent_source


def test_docs_include_endpoint_catalog_commands():
    readme_source = Path("README.md").read_text(encoding="utf-8")
    usage_source = Path("tonghuashun-ifind/references/usage.md").read_text(encoding="utf-8")
    examples_source = Path("tonghuashun-ifind/references/full-examples.md").read_text(encoding="utf-8")
    skill_source = Path("tonghuashun-ifind/SKILL.md").read_text(encoding="utf-8")

    assert "endpoint-list" in readme_source
    assert "endpoint-call" in readme_source
    assert "endpoint-list" in usage_source
    assert "endpoint-call" in usage_source
    assert "endpoint-list" in examples_source
    assert "endpoint-call" in examples_source
    assert "endpoint-list" in skill_source
