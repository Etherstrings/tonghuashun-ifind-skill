from pathlib import Path
import importlib.util
import sys

SCRIPT_DIR = Path("tonghuashun-ifind/scripts").resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ifind_cli import main


def test_ifind_cli_module_exists():
    cli_path = Path("tonghuashun-ifind/scripts/ifind_cli.py")
    assert cli_path.exists()
    spec = importlib.util.spec_from_file_location("ifind_cli", cli_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_cli_basic_data_command_routes_to_client(monkeypatch, capsys):
    monkeypatch.setattr(
        "ifind_cli.run_command",
        lambda argv: {
            "ok": True,
            "endpoint": "/basic_data_service",
            "token_source": "manual",
            "data": {},
            "error": None,
            "meta": {},
        },
    )
    exit_code = main(["basic-data", "--payload", '{"codes":"300750.SZ"}'])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"ok": true' in captured.out.lower()
