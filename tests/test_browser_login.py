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
