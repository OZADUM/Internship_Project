import os
from datetime import datetime
from pathlib import Path
from selenium import webdriver

# Local Chrome
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

# Local Firefox
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager

# Remote (BrowserStack)
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from app.application import Application

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# ---------------- Helper functions ----------------

def _str2bool(v, default=False):
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _userdata(context, key, default=None):
    ud = getattr(context.config, "userdata", {})
    return ud.get(key, os.getenv(key.upper(), default))


# ---------------- Browser setup ----------------

def before_all(context):
    browser = _userdata(context, "browser", "chrome").lower()
    headless = _str2bool(_userdata(context, "headless"), default=False)
    provider = _userdata(context, "provider", "").lower()
    use_bs = provider in ("browserstack", "bs", "remote")

    if use_bs:
        username = os.getenv("BROWSERSTACK_USERNAME")
        access_key = os.getenv("BROWSERSTACK_ACCESS_KEY")
        assert username and access_key, "❌ Set BrowserStack credentials in .env"

        os_name = _userdata(context, "os", "Windows")
        os_version = _userdata(context, "os_version", "11")
        browser_version = _userdata(context, "browser_version", "latest")
        project = os.getenv("BS_PROJECT", "Reelly QA")
        build = os.getenv("BS_BUILD", "Reelly QA – BrowserStack")

        bstack_opts = {
            "os": os_name,
            "osVersion": os_version,
            "projectName": project,
            "buildName": build,
            "sessionName": "Behave Test",
            "seleniumVersion": "4.20.0",
        }

        if browser == "firefox":
            options = FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            options.set_capability("browserName", "Firefox")

        elif browser == "safari":
            options = SafariOptions()
            options.set_capability("browserName", "Safari")

        elif browser == "edge":
            options = EdgeOptions()
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1366,900")
            options.set_capability("browserName", "Edge")

        else:
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1366,900")
            options.set_capability("browserName", "Chrome")

        options.set_capability("browserVersion", browser_version)
        options.set_capability("bstack:options", bstack_opts)

        hub = f"https://{username}:{access_key}@hub-cloud.browserstack.com/wd/hub"
        context.driver = webdriver.Remote(command_executor=hub, options=options)

    else:  # Local browsers
        if browser == "firefox":
            options = FirefoxOptions()
            if headless:
                options.headless = True
            service = FirefoxService(GeckoDriverManager().install())
            context.driver = webdriver.Firefox(service=service, options=options)

        else:  # Chrome default
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--window-size=1366,900")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            service = ChromeService(ChromeDriverManager().install())
            context.driver = webdriver.Chrome(service=service, options=options)

    try:
        context.driver.maximize_window()
    except Exception:
        pass

    context.app = Application(context.driver)


def before_scenario(context, scenario):
    """Name BrowserStack session after the scenario."""
    try:
        name = f"{scenario.feature.name} — {scenario.name}"
        context.driver.execute_script(
            'browserstack_executor: {"action": "setSessionName", "arguments": {"name":"%s"}}' % name
        )
    except Exception:
        pass


# ---------------- Screenshot on Failure ----------------

SCREENSHOT_DIR = Path("screenshots")

def _ensure_screenshot_dir():
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def _take_screenshot(context, name="failed-step"):
    _ensure_screenshot_dir()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:80]
    path = SCREENSHOT_DIR / f"{ts}-{safe}.png"

    try:
        context.driver.save_screenshot(str(path))
    except Exception:
        return

    # Attach to Allure if available
    try:
        from allure_commons.types import AttachmentType
        from allure_commons._allure import attach as allure_attach
        allure_attach.file(str(path), name=f"screenshot-{safe}", attachment_type=AttachmentType.PNG)
    except Exception:
        pass


def after_step(context, step):
    if step.status == "failed":
        _take_screenshot(context, step.name)
        try:
            context.driver.execute_script(
                'browserstack_executor: {"action":"setSessionStatus","arguments":{"status":"failed","reason":"Step failed"}}'
            )
        except Exception:
            pass


def after_all(context):
    try:
        context.driver.quit()
    except Exception:
        pass