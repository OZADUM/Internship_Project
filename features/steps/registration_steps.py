from behave import when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DEFAULT_TIMEOUT = 15

# --------- Locators (with fallbacks) ----------
FULL_NAME_CANDS = [
    (By.ID, "Full-Name"),
    (By.CSS_SELECTOR, 'input[wizde="fullNameInput"]'),
    (By.CSS_SELECTOR, 'input[data-name="Full-Name"]'),
    (By.XPATH, '//input[contains(@placeholder, "Full") or contains(@aria-label, "Full")]'),
]

PHONE_CANDS = [
    (By.ID, "phone2"),
    (By.CSS_SELECTOR, 'input[wizde="phoneInput"]'),
    (By.XPATH, '//input[contains(@placeholder,"Phone")]'),
]

EMAIL_CANDS = [
    (By.ID, "Email-3"),
    (By.XPATH, '//input[contains(@type,"email") or contains(@placeholder,"Email")]'),
]

PASSWORD_CANDS = [
    (By.CSS_SELECTOR, 'input[wizde="passwordInput"]'),
    (By.ID, "field"),
    (By.CSS_SELECTOR, 'input[type="password"]'),
]

CREATE_ACCOUNT_LINK_CANDS = [
    (By.XPATH, '//a[contains(@href,"sign-up")]'),
    (By.XPATH, '//*[self::a or self::button][contains(normalize-space(.), "Create account")]'),
]

SIGNUP_LANDMARK_CANDS = FULL_NAME_CANDS  # use the name field as presence signal


# --------- Small wait helpers ----------
def _wait_any_visible(context, candidates, timeout=DEFAULT_TIMEOUT):
    d = context.driver
    last_err = None
    for by, sel in candidates:
        try:
            return WebDriverWait(d, timeout).until(EC.visibility_of_element_located((by, sel)))
        except Exception as e:
            last_err = e
    raise last_err or TimeoutError("No candidate locator became visible")


def _type(context, candidates, text, clear=True):
    el = _wait_any_visible(context, candidates)
    try:
        if clear:
            el.clear()
    except Exception:
        pass
    el.send_keys(text)


def _value(context, candidates):
    el = _wait_any_visible(context, candidates)
    return el.get_attribute("value") or ""


# --------- Navigation guard: ensure we are on /sign-up ----------
def _ensure_signup_page(context):
    d = context.driver
    url = d.current_url
    if "sign-in" in url:
        # Click "Create account" / go to sign-up
        for cand in CREATE_ACCOUNT_LINK_CANDS:
            try:
                WebDriverWait(d, DEFAULT_TIMEOUT).until(
                    EC.element_to_be_clickable(cand)
                ).click()
                break
            except Exception:
                continue
    # Wait for a sign-up landmark (full name field)
    _wait_any_visible(context, SIGNUP_LANDMARK_CANDS)


@when("I fill the registration form with valid test data")
def fill_form(context):
    _ensure_signup_page(context)

    _type(context, FULL_NAME_CANDS, "test+ozan careerist")
    _type(context, PHONE_CANDS, "+971555123456")
    _type(context, EMAIL_CANDS, "test.ozan.careerist+qa@example.com")
    _type(context, PASSWORD_CANDS, "TestPassword!123")


@then("Each registration field shows the entered value")
def verify_values(context):
    assert _value(context, FULL_NAME_CANDS) == "test+ozan careerist", "Full name mismatch"
    assert "+971" in _value(context, PHONE_CANDS), "Phone missing country code +971"
    assert _value(context, EMAIL_CANDS) == "test.ozan.careerist+qa@example.com", "Email mismatch"

    pwd_val = _value(context, PASSWORD_CANDS)
    assert pwd_val == "TestPassword!123" or len(pwd_val) == len("TestPassword!123"), "Password value mismatch"