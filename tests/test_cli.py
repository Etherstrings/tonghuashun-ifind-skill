from pathlib import Path
import importlib.util


def test_ifind_cli_module_exists():
    cli_path = Path("tonghuashun-ifind/scripts/ifind_cli.py")
    assert cli_path.exists()
    spec = importlib.util.spec_from_file_location("ifind_cli", cli_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")
