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

# Remote (BrowserStack) options
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from app.application import Application

# Load .env if present (never commit it)
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
    """Prefer behave -D key=..., then ENV (uppercased), else default."""
    ud = getattr(context.config, "userdata", {})
    return ud.get(key, os.getenv(key.upper(), default))


def before_all(context):
    """
    Supported flags/env:
      - provider: browserstack|bs|remote (default: local)
      - browser: chrome|firefox|safari|edge (default: chrome)
      - headless: true|false (local & BS)
      - os: Windows|OS X (BS only)
      - os_version: e.g., 11|Sonoma (BS only)
      - browser_version: e.g., latest (BS only)
      - BS_PROJECT / BS_BUILD (env) for naming
    """
    browser = _userdata(context, "browser", "chrome").lower()
    headless = _str2bool(_userdata(context, "headless"), default=False)
    provider = _userdata(context, "provider", "").lower()
    use_bs = provider in ("browserstack", "bs", "remote")

    if use_bs:
        # ---- Remote: BrowserStack ----
        username = os.getenv("BROWSERSTACK_USERNAME")
        access_key = os.getenv("BROWSERSTACK_ACCESS_KEY")
        assert username and access_key, "Set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY in your .env"

        os_name = _userdata(context, "os", "Windows")
        os_version = _userdata(context, "os_version", "11")
        browser_version = _userdata(context, "browser_version", "latest")
        project_name = os.getenv("BS_PROJECT", "Reelly QA")
        build_name = os.getenv("BS_BUILD", "Reelly QA – BrowserStack")
        session_name = "Behave Scenario"

        bstack_opts = {
            "os": os_name,
            "osVersion": os_version,
            "projectName": project_name,
            "buildName": build_name,
            "sessionName": session_name,
            "seleniumVersion": "4.20.0",
        }
        if headless:
            # BrowserStack supports headless for select browsers via this capability
            bstack_opts["browserstack.headless"] = True

        # Pick per-browser Options
        if browser == "firefox":
            options = FirefoxOptions()
            options.set_capability("browserName", "Firefox")
        elif browser == "safari":
            options = SafariOptions()
            options.set_capability("browserName", "Safari")
        elif browser == "edge":
            options = EdgeOptions()
            options.set_capability("browserName", "Edge")
        else:
            browser = "chrome"
            options = ChromeOptions()
            options.set_capability("browserName", "Chrome")

        options.set_capability("browserVersion", browser_version)
        options.set_capability("bstack:options", bstack_opts)

        hub = f"https://{username}:{access_key}@hub-cloud.browserstack.com/wd/hub"
        context.driver = webdriver.Remote(command_executor=hub, options=options)

    else:
        # ---- Local: Chrome / Firefox ----
        if browser == "firefox":
            options = FirefoxOptions()
            if headless:
                options.headless = True  # or options.add_argument("-headless")
            options.set_preference("layout.css.devPixelsPerPx", "1.0")
            service = FirefoxService(GeckoDriverManager().install())
            context.driver = webdriver.Firefox(service=service, options=options)
        else:
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--window-size=1366,900")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            service = ChromeService(ChromeDriverManager().install())
            context.driver = webdriver.Chrome(service=service, options=options)

    # Maximize may no-op in headless; ignore errors
    try:
        context.driver.maximize_window()
    except Exception:
        pass

    context.app = Application(context.driver)


def before_scenario(context, scenario):
    """Name BrowserStack sessions after the scenario (shows in BS dashboard)."""
    try:
        name = f"{scenario.feature.name} — {scenario.name}"
        context.driver.execute_script(
            'browserstack_executor: {"action": "setSessionName", "arguments": {"name":"%s"}}' % name
        )
    except Exception:
        pass


def after_step(context, step):
    """Mark BS session failed if any step fails (optional, helpful)."""
    try:
        if step.status == "failed":
            context.driver.execute_script(
                'browserstack_executor: {"action":"setSessionStatus", "arguments":{"status":"failed","reason":"Step failed"}}'
            )
    except Exception:
        pass


def after_all(context):
    try:
        context.driver.quit()
    except Exception:
        pass