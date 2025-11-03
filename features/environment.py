import os
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

# Load .env if exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _str2bool(v, default=False):
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _userdata(context, key, default=None):
    ud = getattr(context.config, "userdata", {})
    return ud.get(key, os.getenv(key.upper(), default))


def before_all(context):
    browser = _userdata(context, "browser", "chrome").lower()
    headless = _str2bool(_userdata(context, "headless"), default=False)
    provider = _userdata(context, "provider", "").lower()
    use_bs = provider in ("browserstack", "bs", "remote")

    if use_bs:
        username = os.getenv("BROWSERSTACK_USERNAME")
        access_key = os.getenv("BROWSERSTACK_ACCESS_KEY")
        assert username and access_key, "❌ Set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY in .env"

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

        # Select browser options
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

        else:  # default Chrome
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

    else:
        # -------- Local browsers --------
        if browser == "firefox":
            options = FirefoxOptions()
            if headless:
                options.headless = True
            service = FirefoxService(GeckoDriverManager().install())
            context.driver = webdriver.Firefox(service=service, options=options)

        else:  # default Chrome
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
    """Name BrowserStack sessions by scenario."""
    try:
        name = f"{scenario.feature.name} — {scenario.name}"
        context.driver.execute_script(
            'browserstack_executor: {"action": "setSessionName", "arguments": {"name":"%s"}}' % name
        )
    except Exception:
        pass


def after_step(context, step):
    """Mark session failed on step failure."""
    try:
        if step.status == "failed":
            context.driver.execute_script(
                'browserstack_executor: {"action":"setSessionStatus", '
                '"arguments":{"status":"failed","reason":"Step failed"}}'
            )
    except Exception:
        pass


def after_all(context):
    try:
        context.driver.quit()
    except Exception:
        pass