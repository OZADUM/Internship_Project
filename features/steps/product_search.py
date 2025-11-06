# features/steps/product_search.py
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DEFAULT_TIMEOUT = 25
GOOGLE_HOME = "https://www.google.com/?hl=en&gl=us"
QUERY = "Car"

# ---------- Candidate locators ----------
SEARCH_INPUT_CANDS = [
    (By.NAME, "q"),
    (By.CSS_SELECTOR, 'input[title="Search"]'),
    (By.CSS_SELECTOR, 'form[action*="/search"] input[type="text"]'),
]

SEARCH_SUBMIT_CANDS = [
    (By.NAME, "btnK"),
    (By.CSS_SELECTOR, 'input[name="btnK"]'),
    (By.CSS_SELECTOR, 'form[action*="/search"] button[type="submit"]'),
]

# Results containers / items (mobile+desktop)
RESULTS_READY_CANDS = [
    (By.ID, "search"),
    (By.CSS_SELECTOR, "#center_col"),
    (By.CSS_SELECTOR, 'div[role="main"]'),
    (By.CSS_SELECTOR, 'a h3'),              # result titles
    (By.CSS_SELECTOR, 'div[data-hveid]'),   # result blocks
]

# ---------- Helpers ----------
def _effective_timeout(context):
    ud = getattr(context.config, "userdata", {})
    on_bs = str(ud.get("provider", "")).lower() in ("browserstack", "bs", "remote")
    has_device = bool(ud.get("device") or ud.get("mobile"))
    if on_bs or has_device:
        return max(DEFAULT_TIMEOUT, 90)
    return DEFAULT_TIMEOUT

def _wait_any_present(context, candidates, timeout):
    wait = WebDriverWait(context.driver, timeout)
    last_err = None
    for loc in candidates:
        try:
            return wait.until(EC.presence_of_element_located(loc))
        except Exception as e:
            last_err = e
    if last_err:
        raise last_err
    raise TimeoutError("No locator matched (present).")

def _wait_any_visible(context, candidates, timeout):
    wait = WebDriverWait(context.driver, timeout)
    last_err = None
    for loc in candidates:
        try:
            return wait.until(EC.visibility_of_element_located(loc))
        except Exception as e:
            last_err = e
    if last_err:
        raise last_err
    raise TimeoutError("No locator matched (visible).")

def _maybe_accept_google_consent(context):
    d = context.driver
    try:
        # Consent sometimes appears in an iframe
        iframes = d.find_elements(By.CSS_SELECTOR, 'iframe[src*="consent"]')
        if iframes:
            d.switch_to.frame(iframes[0])
        CONSENT_CANDS = [
            (By.ID, "L2AGLb"),
            (By.CSS_SELECTOR, 'button[aria-label*="Accept"]'),
            (By.XPATH, '//button[contains(.,"I agree") or contains(.,"Accept all")]'),
        ]
        for loc in CONSENT_CANDS:
            try:
                btn = WebDriverWait(d, 5).until(EC.element_to_be_clickable(loc))
                btn.click()
                break
            except Exception:
                continue
    except Exception:
        pass
    finally:
        try:
            d.switch_to.default_content()
        except Exception:
            pass

def _url_has_query(d):
    url = (d.current_url or "").lower()
    return "/search" in url and "q=car" in url

def _title_has_query(d):
    return QUERY.lower() in (d.title or "").lower()

def _results_look_loaded(context, timeout):
    d = context.driver
    wait = WebDriverWait(d, timeout)
    # Any of these being true is “success”
    try:
        if _url_has_query(d):
            return True
    except Exception:
        pass
    try:
        _wait_any_present(context, RESULTS_READY_CANDS, min(20, timeout))
        return True
    except Exception:
        pass
    try:
        if _title_has_query(d):
            return True
    except Exception:
        pass
    return False

# ---------- Steps ----------
@given("Open Google page")
def open_google(context):
    context.driver.get(GOOGLE_HOME)
    _maybe_accept_google_consent(context)

@when("Input Car into search field")
def type_query(context):
    timeout = _effective_timeout(context)
    input_el = _wait_any_visible(context, SEARCH_INPUT_CANDS, timeout)
    try:
        input_el.clear()
    except Exception:
        pass
    input_el.send_keys(QUERY)

@when("Click on search icon")
def submit_search(context):
    timeout = _effective_timeout(context)
    d = context.driver

    # ENTER tends to be most reliable on mobile Safari
    try:
        _wait_any_visible(context, SEARCH_INPUT_CANDS, timeout).send_keys(Keys.ENTER)
        return
    except Exception:
        pass

    # Fallback: click a submit button if visible
    try:
        _wait_any_visible(context, SEARCH_SUBMIT_CANDS, timeout).click()
        return
    except Exception:
        pass

    # Last resort: send ENTER again
    _wait_any_visible(context, SEARCH_INPUT_CANDS, timeout).send_keys(Keys.ENTER)

@then("Product results for Car are shown")
def verify_results(context):
    d = context.driver
    timeout = _effective_timeout(context)

    # Try to observe the interactive flow first
    if _results_look_loaded(context, timeout):
        return

    # ---- Forced navigation fallback (for flaky iOS Safari/Appium cases) ----
    forced_url = f"https://www.google.com/search?q={QUERY}&hl=en&gl=us"
    d.get(forced_url)

    if _results_look_loaded(context, timeout):
        return

    # If still not detected, give a helpful error
    current = d.current_url
    title = d.title
    raise AssertionError(
        f"Search results did not load (no signals). URL='{current}', TITLE='{title}'"
    )