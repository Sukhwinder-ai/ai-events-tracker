"""Read-only Playwright contract (fallback, used only if a source needs JS).

The scraper only ever READS public pages. This guard enforces that:
- only GET requests are allowed through; everything else is aborted
- callers get read helpers only (navigate + read text); no click/fill/etc.
"""

FORBIDDEN_METHODS = {"POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


def is_request_allowed(method: str) -> bool:
    return method.upper() == "GET"


def install_readonly_guard(page) -> None:
    """Route a Playwright page so only GET requests proceed. All others abort.

    Usage (only when a JS-rendered source requires it):
        install_readonly_guard(page)
        page.goto(url)               # allowed
        html = page.content()        # allowed (read)
        # page.click(...) etc. are simply never called by our code
    """
    def _route(route):
        if is_request_allowed(route.request.method):
            route.continue_()
        else:
            route.abort()

    page.route("**/*", _route)


def read_text(page, url: str) -> str:
    """Navigate (GET) and return page HTML. Read-only."""
    page.goto(url, wait_until="domcontentloaded")
    return page.content()
