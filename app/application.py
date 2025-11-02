from pages.base_page import BasePage
from pages.sign_up_page import SignUpPage   # ✅ import your SignUp POM

class Application:
    def __init__(self, driver):
        self.driver = driver

        # ✅ Register page objects here
        self.sign_up_page = SignUpPage(driver)

        # Example placeholder for future pages:
        # self.main_page = MainPage(driver)
        # self.login_page = LoginPage(driver)

    def open(self, url: str):
        self.driver.get(url)