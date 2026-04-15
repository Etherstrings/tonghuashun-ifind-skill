from pathlib import Path


def test_readme_contains_chinese_donation_section():
    source = Path("README.md").read_text(encoding="utf-8")
    assert '## <a id="donate"></a>赞助支持' in source
    assert "GitHub Sponsors" in source


def test_skill_docs_are_written_in_chinese():
    skill_source = Path("tonghuashun-ifind/SKILL.md").read_text(encoding="utf-8")
    usage_source = Path("tonghuashun-ifind/references/usage.md").read_text(encoding="utf-8")
    routing_source = Path("tonghuashun-ifind/references/routing.md").read_text(encoding="utf-8")
    cases_source = Path("tonghuashun-ifind/references/use-cases.md").read_text(encoding="utf-8")

    assert "# 同花顺 iFinD 接入 Skill" in skill_source
    assert "## 常见查询主入口" in usage_source
    assert "smart-query" in skill_source
    assert "# 路由规则" in routing_source
    assert "# 常见 Use Cases" in cases_source
