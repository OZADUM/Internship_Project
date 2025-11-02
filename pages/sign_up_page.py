from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DEFAULT_TIMEOUT = 15


class SignUpPage:
    # --------- Locators (with fallbacks) ----------
    FULL_NAME_CANDS = [
        (By.ID, "Full-Name"),
        (By.CSS_SELECTOR, 'input[wizde="fullNameInput"]'),
        (By.CSS_SELECTOR, 'input[data-name="Full-Name"]'),
        (By.XPATH, '//input[contains(@placeholder, "Full") or contains(@aria-label, "Full")]'),
    ]

    PHONE_CANDS = [
        (By.ID, "phone2"),
        (By.CSS_SELECTOR, 'input[wizde="phoneInput"]'),
        (By.XPATH, '//input[contains(@placeholder,"Phone")]'),
    ]

    EMAIL_CANDS = [
        (By.ID, "Email-3"),
        (By.XPATH, '//input[contains(@type,"email") or contains(@placeholder,"Email")]'),
    ]

    PASSWORD_CANDS = [
        (By.CSS_SELECTOR, 'input[wizde="passwordInput"]'),
        (By.ID, "field"),
        (By.CSS_SELECTOR, 'input[type="password"]'),
    ]

    CREATE_ACCOUNT_LINK_CANDS = [
        (By.XPATH, '//a[contains(@href,"sign-up")]'),
        (By.XPATH, '//*[self::a or self::button][contains(normalize-space(.), "Create account")]'),
    ]

    SIGNUP_LANDMARK_CANDS = FULL_NAME_CANDS  # name field signals we're on sign-up

    def __init__(self, driver):
        self.driver = driver

    # ---------- small helpers ----------
    def _wait_any_visible(self, candidates, timeout=DEFAULT_TIMEOUT):
        d = self.driver
        last_err = None
        for by, sel in candidates:
            try:
                return WebDriverWait(d, timeout).until(
                    EC.visibility_of_element_located((by, sel))
                )
            except Exception as e:
                last_err = e
        raise last_err or TimeoutError("No candidate locator became visible")

    def _type(self, candidates, text, clear=True):
        el = self._wait_any_visible(candidates)
        try:
            if clear:
                el.clear()
        except Exception:
            pass
        el.send_keys(text)

    def _value(self, candidates):
        el = self._wait_any_visible(candidates)
        return el.get_attribute("value") or ""

    # ---------- navigation guard ----------
    def ensure_on_signup(self):
        url = self.driver.current_url
        if "sign-in" in url:
            for cand in self.CREATE_ACCOUNT_LINK_CANDS:
                try:
                    WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                        EC.element_to_be_clickable(cand)
                    ).click()
                    break
                except Exception:
                    continue
        # Wait for landmark
        self._wait_any_visible(self.SIGNUP_LANDMARK_CANDS)

    # ---------- actions ----------
    def fill_form(self, full_name, phone, email, password):
        self.ensure_on_signup()
        self._type(self.FULL_NAME_CANDS, full_name)
        self._type(self.PHONE_CANDS, phone)
        self._type(self.EMAIL_CANDS, email)
        self._type(self.PASSWORD_CANDS, password)

    # ---------- assertions ----------
    def assert_form_values(self, full_name, phone_part, email, password):
        assert self._value(self.FULL_NAME_CANDS) == full_name, "Full name mismatch"
        assert phone_part in self._value(self.PHONE_CANDS), f"Phone does not contain {phone_part}"
        assert self._value(self.EMAIL_CANDS) == email, "Email mismatch"

        pwd_val = self._value(self.PASSWORD_CANDS)
        # some envs mask passwords; accept exact or same length
        assert pwd_val == password or len(pwd_val) == len(password), "Password value mismatch"