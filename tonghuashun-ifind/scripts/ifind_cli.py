from __future__ import annotations

from datetime import date
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
        if args.command in {
            "smart-query",
            "quote-realtime",
            "quote-history",
            "market-snapshot",
            "fundamental-basic",
        }:
            return _handle_routed_query_command(args, state_path)
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

    smart_query = subparsers.add_parser("smart-query", parents=[api_common])
    smart_query.add_argument("--query", required=True)

    quote_realtime = subparsers.add_parser("quote-realtime", parents=[api_common])
    quote_realtime.add_argument("--symbol", required=True)

    quote_history = subparsers.add_parser("quote-history", parents=[api_common])
    quote_history.add_argument("--symbol", required=True)
    quote_history.add_argument("--start-date", default=None)
    quote_history.add_argument("--end-date", default=None)
    quote_history.add_argument("--days", type=int, default=30)

    market_snapshot = subparsers.add_parser("market-snapshot", parents=[api_common])
    market_snapshot.add_argument("--symbol", default=None)

    fundamental_basic = subparsers.add_parser("fundamental-basic", parents=[api_common])
    fundamental_basic.add_argument("--symbol", required=True)

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


def _handle_routed_query_command(
    args: argparse.Namespace,
    state_path: Path,
) -> dict[str, object]:
    from tonghuashun_ifind_skill.client import IFindClient
    from tonghuashun_ifind_skill.client import build_envelope
    from tonghuashun_ifind_skill.fallback import TencentStockFallbackClient
    from tonghuashun_ifind_skill.routing import build_fundamental_plan
    from tonghuashun_ifind_skill.routing import build_history_plan
    from tonghuashun_ifind_skill.routing import build_market_snapshot_plan
    from tonghuashun_ifind_skill.routing import build_realtime_plan
    from tonghuashun_ifind_skill.routing import build_route_plan
    from tonghuashun_ifind_skill.routing import extract_entity_from_search_payload
    from tonghuashun_ifind_skill.routing import resolve_common_index_entity

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
    client = IFindClient(base_url=args.base_url)
    fallback_client = TencentStockFallbackClient()
    auth_cache: dict[str, object] = {}

    def ensure_auth() -> tuple[object, str]:
        bundle = auth_cache.get("bundle")
        token_source = auth_cache.get("token_source")
        if bundle is not None and isinstance(token_source, str):
            return bundle, token_source
        resolved_bundle, resolved_token_source = auth.resolve_tokens()
        auth_cache["bundle"] = resolved_bundle
        auth_cache["token_source"] = resolved_token_source
        return resolved_bundle, resolved_token_source

    def entity_lookup(text: str):
        common_index = resolve_common_index_entity(text)
        if common_index is not None:
            return common_index
        try:
            bundle, token_source = ensure_auth()
        except Exception:
            return fallback_client.search_entity(text)
        payload = {
            "searchstring": f"{text} 股票代码 股票简称",
            "searchtype": "stock",
        }
        result = client.smart_stock_picking(payload, bundle.access_token, token_source)
        if not result.get("ok"):
            return fallback_client.search_entity(text)
        raw_payload = result.get("data")
        if not isinstance(raw_payload, dict):
            return fallback_client.search_entity(text)
        entity = extract_entity_from_search_payload(text, raw_payload)
        if entity is not None:
            return entity
        return fallback_client.search_entity(text)

    if args.command == "smart-query":
        plan = build_route_plan(
            args.query,
            entity_lookup=entity_lookup,
            today=date.today(),
        )
    elif args.command == "quote-realtime":
        plan = build_route_plan(
            f"{args.symbol} 最新价",
            entity_lookup=entity_lookup,
            today=date.today(),
        )
    elif args.command == "quote-history":
        plan = build_route_plan(
            f"{args.symbol} 近{args.days}天走势",
            entity_lookup=entity_lookup,
            today=date.today(),
        )
        if plan.intent == "quote_history" and plan.entity is not None:
            plan = build_history_plan(
                plan.entity,
                query=f"{args.symbol} 近{args.days}天走势",
                today=date.today(),
                start_date=args.start_date,
                end_date=args.end_date,
            )
    elif args.command == "market-snapshot":
        plan = build_market_snapshot_plan(args.symbol)
    elif args.command == "fundamental-basic":
        plan = build_route_plan(
            f"{args.symbol} 基本面",
            entity_lookup=entity_lookup,
            today=date.today(),
        )
    else:
        return build_envelope(
            ok=False,
            endpoint="/cli",
            token_source="cli",
            error_type="invalid_request",
            error_message="unknown routed command",
        )

    if plan.intent == "manual_lookup":
        return build_envelope(
            ok=False,
            endpoint="/manual_lookup",
            token_source="cli",
            error_type="manual_api_lookup_required",
            error_message=plan.note or "manual lookup required",
            data={
                "intent": plan.intent,
                "note": plan.note,
            },
        )

    try:
        bundle, token_source = ensure_auth()
    except Exception as exc:
        fallback_result = _execute_public_fallback(
            fallback_client=fallback_client,
            plan=plan,
            reason=_sanitize_exception(exc),
        )
        if fallback_result is not None:
            return fallback_result
        return build_envelope(
            ok=False,
            endpoint=plan.endpoint or "/cli",
            token_source="cli",
            error_type="runtime_failed",
            error_message=_sanitize_exception(exc),
        )

    if args.command == "fundamental-basic" or plan.intent == "fundamental_basic":
        return _execute_fundamental_plan(
            client=client,
            access_token=bundle.access_token,
            token_source=token_source,
            plan=plan,
        )

    result = client.api_call(
        plan.endpoint or "/",
        plan.payload or {},
        bundle.access_token,
        token_source,
    )
    if not result.get("ok"):
        fallback_result = _execute_public_fallback(
            fallback_client=fallback_client,
            plan=plan,
            reason=_result_error_message(result),
        )
        if fallback_result is not None:
            return fallback_result
    return _attach_route_metadata(result, plan)


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


def _attach_route_metadata(
    result: dict[str, object],
    plan,
    *,
    response_data: object | None = None,
    note: str | None = None,
    provider: dict[str, object] | None = None,
) -> dict[str, object]:
    effective_response = result.get("data") if response_data is None else response_data
    effective_provider = provider
    if effective_provider is None and isinstance(effective_response, dict):
        maybe_provider = effective_response.get("provider")
        if isinstance(maybe_provider, dict):
            effective_provider = maybe_provider
            effective_response = {
                key: value
                for key, value in effective_response.items()
                if key != "provider"
            }
    result["data"] = {
        "intent": plan.intent,
        "entity": None if plan.entity is None else {
            "raw": plan.entity.raw,
            "symbol": plan.entity.symbol,
            "name": plan.entity.name,
            "entity_type": plan.entity.entity_type,
        },
        "request": {"payload": plan.payload},
        "response": effective_response,
        "note": note if note is not None else plan.note,
    }
    if effective_provider is not None:
        result["data"]["provider"] = effective_provider
    return result


def _execute_fundamental_plan(
    *,
    client,
    access_token: str,
    token_source: str,
    plan,
) -> dict[str, object]:
    from tonghuashun_ifind_skill.client import build_envelope

    payload = plan.payload or {}
    searchstrings = payload.get("searchstrings")
    searchtype = payload.get("searchtype", "stock")
    if not isinstance(searchstrings, list) or not searchstrings:
        return build_envelope(
            ok=False,
            endpoint="/smart_stock_picking",
            token_source=token_source,
            error_type="invalid_request",
            error_message="missing searchstrings for fundamental route",
        )

    labels = ("financials", "valuation", "forecast")
    results: dict[str, object] = {}
    partial_failures: list[str] = []
    any_success = False
    errors: dict[str, object] = {}

    for label, searchstring in zip(labels, searchstrings):
        result = client.smart_stock_picking(
            {"searchstring": searchstring, "searchtype": searchtype},
            access_token,
            token_source,
        )
        if result.get("ok"):
            any_success = True
            results[label] = result.get("data")
        else:
            partial_failures.append(label)
            errors[label] = result.get("error")

    if not any_success:
        return build_envelope(
            ok=False,
            endpoint="/smart_stock_picking",
            token_source=token_source,
            error_type="api_failed",
            error_message="all fundamental queries failed",
            data={
                "intent": plan.intent,
                "entity": None if plan.entity is None else {
                    "raw": plan.entity.raw,
                    "symbol": plan.entity.symbol,
                    "name": plan.entity.name,
                    "entity_type": plan.entity.entity_type,
                },
                "request": {"payload": plan.payload},
                "partial_failures": partial_failures,
                "errors": errors,
            },
        )

    return build_envelope(
        ok=True,
        endpoint="/smart_stock_picking",
        token_source=token_source,
        data={
            "intent": plan.intent,
            "entity": None if plan.entity is None else {
                "raw": plan.entity.raw,
                "symbol": plan.entity.symbol,
                "name": plan.entity.name,
                "entity_type": plan.entity.entity_type,
            },
            "request": {"payload": plan.payload},
            "results": results,
            "partial_failures": partial_failures,
            "errors": errors,
        },
    )


def _execute_public_fallback(
    *,
    fallback_client,
    plan,
    reason: str,
) -> dict[str, object] | None:
    from tonghuashun_ifind_skill.client import build_envelope

    if plan.intent not in {"quote_realtime", "quote_history", "market_snapshot"}:
        return None
    try:
        fallback_data = fallback_client.execute_plan(plan)
    except Exception:
        return None
    result = build_envelope(
        ok=True,
        endpoint=plan.endpoint or "/fallback",
        token_source="fallback:tencent",
        data=None,
    )
    fallback_note = f"iFinD 查询失败，已回退到腾讯财经公开行情源。原因: {reason}"
    return _attach_route_metadata(
        result,
        plan,
        response_data=fallback_data,
        note=fallback_note,
    )


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
    if args.command == "smart-query":
        return "/smart_query"
    if args.command == "quote-realtime":
        return "/real_time_quotation"
    if args.command == "quote-history":
        return "/cmd_history_quotation"
    if args.command == "market-snapshot":
        return "/real_time_quotation"
    if args.command == "fundamental-basic":
        return "/smart_stock_picking"
    return "/cli"


def _result_error_message(result: dict[str, object]) -> str:
    error = result.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return "iFinD request failed"


if __name__ == "__main__":
    raise SystemExit(main())
