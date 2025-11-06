from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

GOOGLE_URL = "https://www.google.com"
SEARCH_INPUT = (By.NAME, "q")
RESULTS_READY_CANDS = [
    (By.ID, "search"),  # desktop/mobile main results container
    (By.ID, "rso"),     # older container id
    (By.CSS_SELECTOR, "#main"),  # fallback
]

DEFAULT_TIMEOUT = 15


def _wait_visible(context, locator, timeout=DEFAULT_TIMEOUT):
    return WebDriverWait(context.driver, timeout).until(
        EC.visibility_of_element_located(locator)
    )


def _wait_any_present(context, locators, timeout=DEFAULT_TIMEOUT):
    wait = WebDriverWait(context.driver, timeout)
    last_err = None
    for loc in locators:
        try:
            return wait.until(EC.presence_of_element_located(loc))
        except Exception as e:
            last_err = e
    if last_err:
        raise last_err


@given("Open Google page")
def open_google(context):
    context.driver.get(GOOGLE_URL)
    _wait_visible(context, SEARCH_INPUT)


@when('Input {term} into search field')
def input_term(context, term):
    box = _wait_visible(context, SEARCH_INPUT)
    box.clear()
    box.send_keys(term)


@when("Click on search icon")
def submit_search(context):
    # On mobile, the search button may be hidden; press ENTER instead.
    box = _wait_visible(context, SEARCH_INPUT)
    box.send_keys(Keys.ENTER)


@then('Product results for {term} are shown')
def verify_results(context, term):
    _wait_any_present(context, RESULTS_READY_CANDS)
    # Title contains query on both desktop & mobile
    WebDriverWait(context.driver, DEFAULT_TIMEOUT).until(
        EC.title_contains(term)
    )