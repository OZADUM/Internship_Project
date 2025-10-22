from pages.base_page import BasePage

class Application:
    def __init__(self, driver):
        self.driver = driver
        # Register page objects here as you add them, e.g.:
        # self.main_page = MainPage(driver)

    def open(self, url: str):
        self.driver.get(url)