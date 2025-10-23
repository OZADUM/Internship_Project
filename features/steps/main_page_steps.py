# features/steps/main_page_steps.py
from behave import given, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

def _base(context) -> str:
    return (
        context.config.userdata.get("reelly_base")
        or os.environ.get("REELLY_BASE")
        or "https://soft.reelly.io"
    ).rstrip("/")


def _title_contains_any_ci(driver, fragments):
    title_l = (driver.title or "").lower()
    return any(f.lower() in title_l for f in fragments)


def _looks_404(driver) -> bool:
    t = (driver.title or "").lower()
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    except Exception:
        body_text = ""
    signs = ["404", "not found", "doesn’t exist", "does not exist", "page not found"]
    return any(s in t for s in signs) or any(s in body_text for s in signs)


@given("I open the Reelly sign-up page")
def open_reelly_signup(context):
    d = context.driver
    base = _base(context)

    # Try direct auth routes first (common patterns)
    directs = [
        f"{base}/auth/sign-up",
        f"{base}/sign-up",
        f"{base}/signup",
        f"{base}/register",
        f"{base}/auth/register",
        f"{base}/#/auth/sign-up",  # hash router variant
    ]
    for url in directs:
        d.get(url)
        WebDriverWait(d, 5).until(lambda x: True)
        if not _looks_404(d) and _title_contains_any_ci(d, ["reelly", "sign", "log in", "auth"]):
            return

    # Fallback: open home and click a link
    d.get(base)
    WebDriverWait(d, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    link_texts = ["Sign up", "Create account", "Register", "Get started", "Join now", "Sign Up"]
    for text in link_texts:
        try:
            el = d.find_element(By.PARTIAL_LINK_TEXT, text)
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            WebDriverWait(d, 5).until(EC.element_to_be_clickable(el)).click()
            WebDriverWait(d, 5).until(lambda x: _title_contains_any_ci(d, ["reelly", "sign", "log in", "auth"]))
            return
        except Exception:
            continue

    # Still nothing? Be explicit about base
    raise AssertionError(
        "Could not reach Reelly auth/sign-up page.\n"
        f"Base tried: {base}\n"
        "Tip: run with the correct base, e.g.\n"
        '  python -m behave -D reelly_base="https://app.reelly.io"\n'
        "or set env REELLY_BASE."
    )


@then('The page title should contain "Reelly"')
def title_should_contain_reelly(context):
    ok = _title_contains_any_ci(context.driver, ["reelly", "sign", "log in", "auth"])
    assert ok, f"Unexpected title: {context.driver.title}"