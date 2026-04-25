from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import argparse
import json
from pathlib import Path
import re
import sys


_RUNTIME_DIR = Path(__file__).resolve().parent / "runtime"
if _RUNTIME_DIR.is_dir():
    runtime_path = str(_RUNTIME_DIR)
    if runtime_path not in sys.path:
        sys.path.insert(0, runtime_path)


DEFAULT_BASE_URL = "https://quantapi.51ifind.com/api/v1"


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
        if args.command == "auth-set-refresh-token":
            return _handle_auth_set_refresh_token(args, state_path)
        if args.command == "endpoint-list":
            return _handle_endpoint_list()
        if args.command in {
            "api-call",
            "endpoint-call",
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

    auth_set = subparsers.add_parser("auth-set-tokens")
    auth_set.add_argument("--access-token", required=True)
    auth_set.add_argument("--refresh-token", required=True)
    auth_set.add_argument("--expires-at", default=None)

    auth_refresh = subparsers.add_parser("auth-set-refresh-token")
    auth_refresh.add_argument("--refresh-token", required=True)
    auth_refresh.add_argument("--base-url", default=DEFAULT_BASE_URL)

    api_common = argparse.ArgumentParser(add_help=False)
    api_common.add_argument("--base-url", default=DEFAULT_BASE_URL)
    api_common.add_argument("--payload", default="{}")

    api_call = subparsers.add_parser("api-call", parents=[api_common])
    api_call.add_argument("--endpoint", required=True)

    subparsers.add_parser("endpoint-list")

    endpoint_call = subparsers.add_parser("endpoint-call", parents=[api_common])
    endpoint_call.add_argument("--name", required=True)

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


def _handle_auth_set_refresh_token(
    args: argparse.Namespace,
    state_path: Path,
) -> dict[str, object]:
    from tonghuashun_ifind_skill.auth import exchange_refresh_token
    from tonghuashun_ifind_skill.client import build_envelope
    from tonghuashun_ifind_skill.state import TokenStateStore

    bundle = exchange_refresh_token(
        args.refresh_token,
        base_url=args.base_url,
    )
    TokenStateStore(state_path).save(bundle)
    return build_envelope(
        ok=True,
        endpoint="/auth/set-refresh-token",
        token_source="refresh",
        data={"stored": True, "expires_at": bundle.expires_at},
    )


def _handle_api_command(
    args: argparse.Namespace,
    state_path: Path,
) -> dict[str, object]:
    from tonghuashun_ifind_skill.client import IFindClient
    from tonghuashun_ifind_skill.client import build_envelope
    from tonghuashun_ifind_skill.endpoint_catalog import get_endpoint_spec

    payload = _parse_payload(args.payload)
    if args.command == "endpoint-call":
        try:
            spec = get_endpoint_spec(args.name)
        except ValueError as exc:
            return build_envelope(
                ok=False,
                endpoint="/endpoint_catalog",
                token_source="cli",
                error_type="invalid_request",
                error_message=str(exc),
            )

    auth = _build_auth_manager(
        state_path=state_path,
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
    if args.command == "endpoint-call":
        return client.call_named_endpoint(
            spec.name,
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


def _handle_endpoint_list() -> dict[str, object]:
    from tonghuashun_ifind_skill.client import build_envelope
    from tonghuashun_ifind_skill.endpoint_catalog import list_endpoint_specs

    return build_envelope(
        ok=True,
        endpoint="/endpoint_catalog",
        token_source="cli",
        data={
            "endpoints": [spec.to_dict() for spec in list_endpoint_specs()],
        },
    )


def _handle_routed_query_command(
    args: argparse.Namespace,
    state_path: Path,
) -> dict[str, object]:
    from tonghuashun_ifind_skill.client import IFindClient
    from tonghuashun_ifind_skill.client import build_envelope
    from tonghuashun_ifind_skill.llm_routing import build_llm_route_plan
    from tonghuashun_ifind_skill.routing import build_history_plan
    from tonghuashun_ifind_skill.routing import build_market_snapshot_plan
    from tonghuashun_ifind_skill.routing import build_realtime_plan
    from tonghuashun_ifind_skill.routing import build_route_plan
    from tonghuashun_ifind_skill.routing import extract_entity_from_search_payload
    from tonghuashun_ifind_skill.routing import resolve_common_index_entity

    if args.command == "smart-query" and _is_blank_or_punctuation_query(args.query):
        return build_envelope(
            ok=False,
            endpoint="/manual_lookup",
            token_source="cli",
            error_type="manual_api_lookup_required",
            error_message="请输入明确的股票、指数、指标、日期或筛选条件；空白或纯标点无法路由到 iFinD。",
            data={
                "intent": "manual_lookup",
                "note": "blank_or_punctuation_query",
            },
        )

    auth = _build_auth_manager(
        state_path=state_path,
        base_url=args.base_url,
    )
    client = IFindClient(base_url=args.base_url)
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

    try:
        bundle, token_source = ensure_auth()
    except Exception as exc:
        return build_envelope(
            ok=False,
            endpoint=_command_endpoint(args),
            token_source="cli",
            error_type="auth_required",
            error_message=_auth_required_message(exc),
        )

    def entity_lookup(text: str):
        common_index = resolve_common_index_entity(text)
        if common_index is not None:
            return common_index
        payload = {
            "searchstring": f"{text} 股票代码 股票简称",
            "searchtype": "stock",
        }
        result = client.smart_stock_picking(payload, bundle.access_token, token_source)
        if not result.get("ok"):
            return None
        raw_payload = result.get("data")
        if not isinstance(raw_payload, dict):
            return None
        entity = extract_entity_from_search_payload(text, raw_payload)
        if entity is not None:
            return entity
        return None

    if args.command == "smart-query":
        plan = build_llm_route_plan(
            args.query,
            entity_lookup=entity_lookup,
            today=date.today(),
        )
        if plan is None:
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
    return _attach_route_metadata(result, plan)


def _build_auth_manager(
    *,
    state_path: Path,
    base_url: str,
) -> "AuthManager":
    from tonghuashun_ifind_skill.auth import AuthManager
    from tonghuashun_ifind_skill.auth import exchange_refresh_token
    from tonghuashun_ifind_skill.models import TokenBundle

    def refresh_exchange(refresh_token: str) -> TokenBundle:
        return exchange_refresh_token(
            refresh_token,
            base_url=base_url,
        )

    return AuthManager.create(
        state_path=state_path,
        refresh_exchange=refresh_exchange,
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
    return Path.home() / ".openclaw" / "tonghuashun-ifind-skill" / "token_state.json"


def _default_expiry() -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    return expires_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sanitize_exception(exc: Exception) -> str:
    return f"request failed: {exc.__class__.__name__}"


def _is_blank_or_punctuation_query(query: str) -> bool:
    return not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", query or "")


def _auth_required_message(exc: Exception) -> str:
    return (
        "iFinD authentication is required before querying data. "
        "Ask the user to open the iFinD Super Command client account details page, "
        "or open https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/"
        "super-command-web/index.html#/AccountDetails, log in, copy refresh_token, "
        "then run auth-set-refresh-token. Do not ask for the iFinD username or "
        "password. If the user already has both tokens, run auth-set-tokens. Detail: "
        f"{_sanitize_exception(exc)}"
    )


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


def _command_endpoint(args: argparse.Namespace) -> str:
    if args.command == "auth-set-refresh-token":
        return "/auth/set-refresh-token"
    if args.command == "auth-set-tokens":
        return "/auth/set-tokens"
    if args.command == "api-call":
        endpoint = getattr(args, "endpoint", "")
        return endpoint if endpoint else "/"
    if args.command == "endpoint-list":
        return "/endpoint_catalog"
    if args.command == "endpoint-call":
        return "/endpoint_catalog"
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


if __name__ == "__main__":
    raise SystemExit(main())
