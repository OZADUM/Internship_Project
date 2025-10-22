from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from app.application import Application


def before_all(context):
    options = Options()
    # options.add_argument("--headless=new")  # Enable for headless runs/CI if needed

    service = Service(ChromeDriverManager().install())
    context.driver = webdriver.Chrome(service=service, options=options)
    context.driver.maximize_window()

    context.app = Application(context.driver)


def after_all(context):
    context.driver.quit()
