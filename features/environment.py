cat > features/environment.py <<'EOF'
import os
from selenium import webdriver

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager

from app.application import Application


def _str2bool(v, default=False):
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def before_all(context):
    # Allow both behave -D and environment variables
    userdata = getattr(context.config, "userdata", {})
    browser = userdata.get("browser", os.getenv("BROWSER", "chrome")).lower()
    headless = _str2bool(userdata.get("headless", os.getenv("HEADLESS")), default=False)

    if browser == "firefox":
        options = FirefoxOptions()
        if headless:
            options.headless = True  # or options.add_argument("-headless")
        # Helpful for headless UIs to render consistently
        options.set_preference("layout.css.devPixelsPerPx", "1.0")

        service = FirefoxService(GeckoDriverManager().install())
        context.driver = webdriver.Firefox(service=service, options=options)
    else:
        # default: chrome
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        # Make headless runs act like a real window
        options.add_argument("--window-size=1366,900")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = ChromeService(ChromeDriverManager().install())
        context.driver = webdriver.Chrome(service=service, options=options)

    context.driver.maximize_window()
    context.app = Application(context.driver)


def after_all(context):
    context.driver.quit()
EOF
