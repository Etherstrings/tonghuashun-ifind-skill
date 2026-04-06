from pathlib import Path
import sys


_RUNTIME_DIR = Path(__file__).resolve().parent / "runtime"
if _RUNTIME_DIR.is_dir():
    runtime_path = str(_RUNTIME_DIR)
    if runtime_path not in sys.path:
        sys.path.insert(0, runtime_path)


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
