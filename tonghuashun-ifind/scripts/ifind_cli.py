from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
import argparse
import json
from pathlib import Path
import sys


_RUNTIME_DIR = Path(__file__).resolve().parent / "runtime"
if _RUNTIME_DIR.is_dir():
    runtime_path = str(_RUNTIME_DIR)
    if runtime_path not in sys.path:
        sys.path.insert(0, runtime_path)


DEFAULT_BASE_URL = "https://quantapi.51ifind.com/api/v1"
DEFAULT_LOGIN_URL = (
    "https://upass.51ifind.com/login?act=loginByIframe&view=bilingual&isIframe=1&auto=0"
    "&main=9&detail=0&pannel=1&source=ifind_quantapi&lang=cn&redir=%2F%2Fquantapi"
    ".51ifind.com%2Fquantapi_upass%2Fapi%2Fapi_web_verify"
)
DEFAULT_USERNAME_SELECTOR = 'input[name="username"]'
DEFAULT_PASSWORD_SELECTOR = 'input[name="password"]'
DEFAULT_SUBMIT_SELECTOR = 'button[type="submit"]'
DEFAULT_BROWSER_EXECUTABLE = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main(argv: list[str] | None = None) -> int:
    result = run_command(sys.argv[1:] if argv is None else argv)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


def run_command(argv: list[str]) -> dict[str, object]:
    from tonghuashun_ifind_skill.client import build_envelope

    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return build_envelope(
            ok=False,
            endpoint="/cli",
            token_source="cli",
            error_type="invalid_request",
            error_message="invalid arguments",
        )

    state_path = (
        Path(args.state_path).expanduser()
        if args.state_path
        else _default_state_path()
    )

    try:
        if args.command == "auth-set-tokens":
            return _handle_auth_set_tokens(args, state_path)
        if args.command == "auth-login":
            return _handle_auth_login(args, state_path)
        if args.command in {
            "api-call",
            "basic-data",
            "smart-pick",
            "report-query",
            "date-sequence",
        }:
            return _handle_api_command(args, state_path)
    except Exception as exc:
        return build_envelope(
            ok=False,
            endpoint=_command_endpoint(args),
            token_source="cli",
            error_type="runtime_failed",
            error_message=_sanitize_exception(exc),
        )

    return build_envelope(
        ok=False,
        endpoint="/cli",
        token_source="cli",
        error_type="invalid_request",
        error_message="unknown command",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ifind-cli")
    parser.add_argument(
        "--state-path",
        default=None,
        help="Path to token state storage",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth_login = subparsers.add_parser("auth-login")
    auth_login.add_argument("--username", required=True)
    auth_login.add_argument("--password", required=True)
    auth_login.add_argument("--login-url", default=DEFAULT_LOGIN_URL)
    auth_login.add_argument("--username-selector", default=DEFAULT_USERNAME_SELECTOR)
    auth_login.add_argument("--password-selector", default=DEFAULT_PASSWORD_SELECTOR)
    auth_login.add_argument("--submit-selector", default=DEFAULT_SUBMIT_SELECTOR)
    auth_login.add_argument(
        "--browser-executable",
        default=DEFAULT_BROWSER_EXECUTABLE,
    )

    auth_set = subparsers.add_parser("auth-set-tokens")
    auth_set.add_argument("--access-token", required=True)
    auth_set.add_argument("--refresh-token", required=True)
    auth_set.add_argument("--expires-at", default=None)

    api_common = argparse.ArgumentParser(add_help=False)
    api_common.add_argument("--base-url", default=DEFAULT_BASE_URL)
    api_common.add_argument("--payload", default="{}")
    api_common.add_argument("--username", default=None)
    api_common.add_argument("--password", default=None)
    api_common.add_argument("--login-url", default=DEFAULT_LOGIN_URL)
    api_common.add_argument("--username-selector", default=DEFAULT_USERNAME_SELECTOR)
    api_common.add_argument("--password-selector", default=DEFAULT_PASSWORD_SELECTOR)
    api_common.add_argument("--submit-selector", default=DEFAULT_SUBMIT_SELECTOR)
    api_common.add_argument(
        "--browser-executable",
        default=DEFAULT_BROWSER_EXECUTABLE,
    )

    api_call = subparsers.add_parser("api-call", parents=[api_common])
    api_call.add_argument("--endpoint", required=True)

    subparsers.add_parser("basic-data", parents=[api_common])
    subparsers.add_parser("smart-pick", parents=[api_common])
    subparsers.add_parser("report-query", parents=[api_common])
    subparsers.add_parser("date-sequence", parents=[api_common])

    return parser


def _handle_auth_set_tokens(
    args: argparse.Namespace,
    state_path: Path,
) -> dict[str, object]:
    from tonghuashun_ifind_skill.client import build_envelope
    from tonghuashun_ifind_skill.models import TokenBundle
    from tonghuashun_ifind_skill.state import TokenStateStore

    expires_at = args.expires_at or _default_expiry()
    bundle = TokenBundle(
        access_token=args.access_token,
        refresh_token=args.refresh_token,
        expires_at=expires_at,
    )
    TokenStateStore(state_path).save(bundle)
    return build_envelope(
        ok=True,
        endpoint="/auth/set-tokens",
        token_source="manual",
        data={"stored": True, "expires_at": expires_at},
    )


def _handle_auth_login(
    args: argparse.Namespace,
    state_path: Path,
) -> dict[str, object]:
    from tonghuashun_ifind_skill.client import build_envelope

    auth = _build_auth_manager(
        state_path=state_path,
        username=args.username,
        password=args.password,
        login_url=args.login_url,
        username_selector=args.username_selector,
        password_selector=args.password_selector,
        submit_selector=args.submit_selector,
        browser_executable=args.browser_executable,
        base_url=DEFAULT_BASE_URL,
    )
    bundle, token_source = auth.login_with_browser()
    return build_envelope(
        ok=True,
        endpoint="/auth/login",
        token_source=token_source,
        data={"stored": True, "expires_at": bundle.expires_at},
    )


def _handle_api_command(
    args: argparse.Namespace,
    state_path: Path,
) -> dict[str, object]:
    from tonghuashun_ifind_skill.client import IFindClient
    from tonghuashun_ifind_skill.client import build_envelope

    payload = _parse_payload(args.payload)
    auth = _build_auth_manager(
        state_path=state_path,
        username=args.username,
        password=args.password,
        login_url=args.login_url,
        username_selector=args.username_selector,
        password_selector=args.password_selector,
        submit_selector=args.submit_selector,
        browser_executable=args.browser_executable,
        base_url=args.base_url,
    )
    bundle, token_source = auth.resolve_tokens()
    client = IFindClient(base_url=args.base_url)

    if args.command == "api-call":
        return client.api_call(
            args.endpoint,
            payload,
            bundle.access_token,
            token_source,
        )
    if args.command == "basic-data":
        return client.basic_data(payload, bundle.access_token, token_source)
    if args.command == "smart-pick":
        return client.smart_stock_picking(payload, bundle.access_token, token_source)
    if args.command == "report-query":
        return client.report_query(payload, bundle.access_token, token_source)
    if args.command == "date-sequence":
        return client.date_sequence(payload, bundle.access_token, token_source)

    return build_envelope(
        ok=False,
        endpoint=_command_endpoint(args),
        token_source="cli",
        error_type="invalid_request",
        error_message="unknown api command",
    )


def _build_auth_manager(
    *,
    state_path: Path,
    username: str | None,
    password: str | None,
    login_url: str,
    username_selector: str,
    password_selector: str,
    submit_selector: str,
    browser_executable: str | None,
    base_url: str,
) -> "AuthManager":
    from tonghuashun_ifind_skill.auth import AuthManager
    from tonghuashun_ifind_skill.browser_login import BrowserLoginRunner
    from tonghuashun_ifind_skill.browser_login import PlaywrightLoginAdapter
    from tonghuashun_ifind_skill.auth import exchange_refresh_token
    from tonghuashun_ifind_skill.models import TokenBundle

    def refresh_exchange(refresh_token: str) -> TokenBundle:
        return exchange_refresh_token(
            refresh_token,
            base_url=base_url,
        )

    def browser_login() -> TokenBundle:
        if not username or not password:
            raise RuntimeError("username/password required for browser login")
        adapter = PlaywrightLoginAdapter(
            login_url=login_url,
            username_selector=username_selector,
            password_selector=password_selector,
            submit_selector=submit_selector,
            browser_executable=browser_executable,
        )
        runner = BrowserLoginRunner(adapter)
        return runner.login_and_capture(username, password)

    return AuthManager.create(
        state_path=state_path,
        refresh_exchange=refresh_exchange,
        browser_login=browser_login,
    )


def _parse_payload(payload: str) -> dict[str, object]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("payload must be valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")
    return data


def _default_state_path() -> Path:
    return Path.home() / ".openclaw" / "tonghuashun-ifind" / "token_state.json"


def _default_expiry() -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    return expires_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sanitize_exception(exc: Exception) -> str:
    return f"request failed: {exc.__class__.__name__}"


def _command_endpoint(args: argparse.Namespace) -> str:
    if args.command == "auth-login":
        return "/auth/login"
    if args.command == "auth-set-tokens":
        return "/auth/set-tokens"
    if args.command == "api-call":
        endpoint = getattr(args, "endpoint", "")
        return endpoint if endpoint else "/"
    if args.command == "basic-data":
        return "/basic_data_service"
    if args.command == "smart-pick":
        return "/smart_stock_picking"
    if args.command == "report-query":
        return "/report_query"
    if args.command == "date-sequence":
        return "/date_sequence"
    return "/cli"


if __name__ == "__main__":
    raise SystemExit(main())
