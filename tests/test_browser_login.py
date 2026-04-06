from tonghuashun_ifind_skill.browser_login import extract_token_bundle


def test_extract_token_bundle_prefers_response_payload_over_storage():
    bundle = extract_token_bundle(
        response_candidates=[{"access_token": "access-a", "refresh_token": "refresh-a"}],
        request_header_candidates=[],
        storage_candidates=[{"access_token": "access-b", "refresh_token": "refresh-b"}],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-a"
    assert bundle.refresh_token == "refresh-a"


def test_extract_token_bundle_handles_nested_response_payload():
    bundle = extract_token_bundle(
        response_candidates=[
            {
                "data": {
                    "access_token": "access-nested",
                    "refresh_token": "refresh-nested",
                    "expires_in": 3600,
                }
            }
        ],
        request_header_candidates=[],
        storage_candidates=[],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-nested"
    assert bundle.refresh_token == "refresh-nested"
    assert bundle.expires_at is not None


def test_extract_token_bundle_combines_across_priority_buckets():
    bundle = extract_token_bundle(
        response_candidates=[{"access_token": "access-top"}],
        request_header_candidates=[],
        storage_candidates=[{"refresh_token": "refresh-lower"}],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-top"
    assert bundle.refresh_token == "refresh-lower"


def test_extract_token_bundle_parses_json_string_storage_values():
    bundle = extract_token_bundle(
        response_candidates=[],
        request_header_candidates=[],
        storage_candidates=[
            {
                "token_payload": (
                    '{"access_token": "access-json", "refresh_token": "refresh-json"}'
                )
            }
        ],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-json"
    assert bundle.refresh_token == "refresh-json"


def test_extract_token_bundle_carries_expiry_from_later_candidate():
    bundle = extract_token_bundle(
        response_candidates=[
            {"access_token": "access-early", "refresh_token": "refresh-early"},
            {"expires_in": 3600},
        ],
        request_header_candidates=[],
        storage_candidates=[],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-early"
    assert bundle.refresh_token == "refresh-early"
    assert bundle.expires_at is not None
