# features/steps/reelly_filters_steps.py
from behave import given, then
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import os

# ---- Config helpers ----

def _base(context) -> str:
    # Priority: behave -D reelly_base=..., then env REELLY_BASE, else default staging
    return (
        context.config.userdata.get("reelly_base")
        or os.environ.get("REELLY_BASE")
        or "https://soft.reelly.io"
    ).rstrip("/")


def _looks_404(driver) -> bool:
    t = (driver.title or "").lower()
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    except Exception:
        body_text = ""
    signs = ["404", "not found", "doesn’t exist", "does not exist", "page not found"]
    return any(s in t for s in signs) or any(s in body_text for s in signs)


def _extract_params_from_url(href: str) -> dict:
    """
    Support params in:
      - query (?pricePer=unit)
      - hash (/#/?pricePer=unit&...)
    """
    parsed = urlparse(href)
    params = parse_qs(parsed.query)

    if parsed.fragment and "?" in parsed.fragment:
        _, qs = parsed.fragment.split("?", 1)
        try:
            frag_params = parse_qs(qs)
            params.update(frag_params)  # hash overrides query if both set
        except Exception:
            pass
    return params


# ---- Test data (adjust if your saved filters changed) ----
# Keep using a known deterministic set so assertion is meaningful
FILTER_QUERY = "city=NYC&rooms=2&pricePer=unit&sort=price_asc"


@given("I open the Reelly find page with filters URL")
def open_find_with_filters(context):
    base = _base(context)
    driver = context.driver

    # Try common SPA routing styles
    candidates = [
        f"{base}/find?{FILTER_QUERY}",      # /find?...
        f"{base}/#/find?{FILTER_QUERY}",    # hash router
        f"{base}/app/find?{FILTER_QUERY}",  # sometimes apps live under /app
    ]

    last_url = None
    for url in candidates:
        driver.get(url)
        last_url = url
        # brief wait for SPA redirect/mount
        WebDriverWait(driver, 5).until(lambda d: True)
        if not _looks_404(driver):
            return

    # If we got here every candidate looks like 404. Fail verbosely.
    raise AssertionError(
        "Could not open Reelly find page with filters.\n"
        f"Tried base: {base}\n"
        "Tried paths: /find, #/find, /app/find\n"
        f"Last URL attempted: {last_url}\n"
        "Tip: run with the correct base, e.g.\n"
        '  python -m behave -D reelly_base="https://app.reelly.io"\n'
        "or set env REELLY_BASE."
    )


@then("The current URL should include the expected filter params")
def url_has_expected_filter_params(context):
    driver = context.driver
    WebDriverWait(driver, 5).until(lambda d: True)

    href = driver.current_url
    params = _extract_params_from_url(href)

    got = params.get("pricePer", [None])[0]
    assert got == "unit", (
        f'Param pricePer expected "unit" but got "{got}" in URL: {href}\n'
        "If the app rewrites filters differently in this environment, update FILTER_QUERY to match."
    )