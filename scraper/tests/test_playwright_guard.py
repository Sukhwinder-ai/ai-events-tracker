from aiscraper.playwright_guard import is_request_allowed, FORBIDDEN_METHODS


def test_get_requests_allowed():
    assert is_request_allowed("GET") is True


def test_mutating_methods_blocked():
    for method in ["POST", "PUT", "DELETE", "PATCH"]:
        assert method in FORBIDDEN_METHODS
        assert is_request_allowed(method) is False


def test_method_check_is_case_insensitive():
    assert is_request_allowed("get") is True
    assert is_request_allowed("post") is False
