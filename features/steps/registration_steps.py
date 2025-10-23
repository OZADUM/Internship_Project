from behave import when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===== Stable locators from DevTools screenshots =====
FULL_NAME = (By.ID, "Full-Name")
PHONE     = (By.ID, "phone2")
EMAIL     = (By.ID, "Email-3")
# Password: primary by wizde, fallback by id="field"
PASSWORD  = (By.CSS_SELECTOR, 'input[wizde="passwordInput"], input#field')

DEFAULT_TIMEOUT = 12

def _wait_visible(context, locator):
    return WebDriverWait(context.driver, DEFAULT_TIMEOUT).until(
        EC.visibility_of_element_located(locator)
    )

def _type(context, locator, text, clear=True):
    el = _wait_visible(context, locator)
    if clear:
        try:
            el.clear()
        except Exception:
            pass
    el.send_keys(text)

@when("I fill the registration form with valid test data")
def fill_form(context):
    # Follow Careerist/Reelly test-data guidelines (no submit needed for this ticket)
    _type(context, FULL_NAME, "test+ozan careerist")
    _type(context, PHONE, "+971555123456")
    _type(context, EMAIL, "test.ozan.careerist+qa@example.com")
    _type(context, PASSWORD, "TestPassword!123")

@then("Each registration field shows the entered value")
def verify_values(context):
    def val(loc):
        return _wait_visible(context, loc).get_attribute("value")

    assert val(FULL_NAME) == "test+ozan careerist", "Full name mismatch"
    assert "+971" in val(PHONE), "Phone missing country code +971"
    assert val(EMAIL) == "test.ozan.careerist+qa@example.com", "Email mismatch"
    # Some browsers mask password visually; but value attribute should reflect input
    assert val(PASSWORD) == "TestPassword!123", "Password value mismatch"
