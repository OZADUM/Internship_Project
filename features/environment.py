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

# Remote cloud options (BrowserStack)
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from app.application import Application

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# ---------------- Helpers ----------------

def _str2bool(v, default=False):
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _userdata(context, key, default=None):
    ud = getattr(context.config, "userdata", {})
    # Prefer behave -D overrides, fall back to ENV (uppercase)
    return ud.get(key, os.getenv(key.upper(), default))


# ---------------- Hooks ----------------

def before_all(context):
    """
    Supported runtime flags (behave -D key=value):
      provider=[local|browserstack|bs|remote]
      browser=[chrome|firefox|safari|edge]
      headless=[true|false]
      # Local mobile emulation (Chrome only)
      mobile="iPhone 14 Pro"  (device name from Chrome DevTools list)

      # BrowserStack desktop:
      os=[Windows|OS X]   os_version=...
      browser_version=...

      # BrowserStack real mobile:
      device="iPhone 15 Pro" or "Samsung Galaxy S23"
      os_version=17 (iOS) or 13 (Android), real_mobile=true
    """
    browser = (_userdata(context, "browser", "chrome") or "chrome").lower()
    headless = _str2bool(_userdata(context, "headless"), default=False)
    provider = (_userdata(context, "provider", "") or "").lower()
    use_bs = provider in ("browserstack", "bs", "remote")

    # Local Chrome mobile emulation device name (e.g., "iPhone 14 Pro")
    mobile_emulation_name = _userdata(context, "mobile", "").strip()

    if use_bs:
        # ---- BrowserStack setup ----
        username = os.getenv("BROWSERSTACK_USERNAME")
        access_key = os.getenv("BROWSERSTACK_ACCESS_KEY")
        assert username and access_key, "❌ Set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY in .env"

        # Detect if this run is real mobile (preferred trigger: device or real_mobile)
        device = _userdata(context, "device", "").strip()
        real_mobile = _str2bool(_userdata(context, "real_mobile"), default=bool(device))
        os_version = _userdata(context, "os_version", "latest")
        browser_version = _userdata(context, "browser_version", "latest")

        project = os.getenv("BS_PROJECT", "Reelly QA")
        build = os.getenv("BS_BUILD", "Reelly QA – BrowserStack")

        bstack_opts = {
            "projectName": project,
            "buildName": build,
            "sessionName": "Behave Test",
            "seleniumVersion": "4.20.0",
        }

        # Real mobile capabilities (BrowserStack W3C)
        if real_mobile or device:
            # On real devices, BrowserStack uses: deviceName, realMobile, osVersion
            bstack_opts["deviceName"] = device or "iPhone 15 Pro"
            bstack_opts["realMobile"] = True
            bstack_opts["osVersion"] = os_version

            # Choose mobile browser: Safari on iOS, Chrome on Android
            # Heuristic: if "iPhone" or "iPad" in device -> Safari, else Chrome
            is_ios = any(k in bstack_opts["deviceName"].lower() for k in ("iphone", "ipad", "ios"))
            if is_ios:
                options = SafariOptions()
                options.set_capability("browserName", "safari")
            else:
                options = ChromeOptions()
                options.set_capability("browserName", "chrome")

            # Note: headless is not applicable on BrowserStack real devices
            options.set_capability("bstack:options", bstack_opts)

        else:
            # Desktop BrowserStack (Windows/Mac)
            os_name = _userdata(context, "os", "Windows")
            os_ver = _userdata(context, "os_version", "11")
            bstack_opts.update({
                "os": os_name,
                "osVersion": os_ver,
            })

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

            else:  # chrome
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
        # ---- Local browsers ----
        if browser == "firefox":
            options = FirefoxOptions()
            if headless:
                options.headless = True
            service = FirefoxService(GeckoDriverManager().install())
            context.driver = webdriver.Firefox(service=service, options=options)

        else:  # chrome (default)
            options = ChromeOptions()
            # Apply Chrome mobile emulation if requested
            if mobile_emulation_name:
                options.add_experimental_option("mobileEmulation", {"deviceName": mobile_emulation_name})

            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--window-size=1366,900")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            service = ChromeService(ChromeDriverManager().install())
            context.driver = webdriver.Chrome(service=service, options=options)

    # Try to maximize; may be ignored in headless / mobile emulation
    try:
        context.driver.maximize_window()
    except Exception:
        pass

    context.app = Application(context.driver)


def before_scenario(context, scenario):
    """Label BrowserStack sessions (shows on Automate dashboard)."""
    try:
        name = f"{scenario.feature.name} — {scenario.name}"
        context.driver.execute_script(
            'browserstack_executor: {"action": "setSessionName", "arguments": {"name":"%s"}}' % name
        )
    except Exception:
        pass


# ---- Screenshot on failure (+ attach to Allure if active) ----

SCREENSHOT_DIR = Path("screenshots")

def _ensure_screenshot_dir():
    try:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

def _take_screenshot(context, base_name: str = "failed-step"):
    _ensure_screenshot_dir()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in base_name)[:80]
    png_path = SCREENSHOT_DIR / f"{ts}-{safe}.png"
    try:
        context.driver.save_screenshot(str(png_path))
    except Exception:
        return
    # Allure attach (best-effort)
    try:
        from allure_commons.types import AttachmentType
        from allure_commons._allure import attach as allure_attach
        allure_attach.file(str(png_path), name=f"screenshot-{safe}", attachment_type=AttachmentType.PNG)
    except Exception:
        pass

def after_step(context, step):
    if step.status == "failed":
        _take_screenshot(context, step.name)
        # Mark BrowserStack session failed
        try:
            context.driver.execute_script(
                'browserstack_executor: {"action":"setSessionStatus",'
                '"arguments":{"status":"failed","reason":"Step failed"}}'
            )
        except Exception:
            pass


def after_all(context):
    try:
        context.driver.quit()
    except Exception:
        pass