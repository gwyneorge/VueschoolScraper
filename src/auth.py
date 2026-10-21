from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from decouple import config


def login(driver):
    wait = WebDriverWait(driver, 20)
    driver.get("https://vueschool.io/login")

    email = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'form input[type="email"]')))
    password = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'form input[type="password"]')))

    # let Nuxt hydrate so typed values aren't wiped
    wait.until(lambda d: d.execute_script("return !!document.querySelector('#__nuxt').__vue_app__"))

    email.clear()
    email.send_keys(config("EMAIL"))
    password.clear()
    password.send_keys(config("PASSWORD"))

    wait.until(EC.element_to_be_clickable((By.XPATH, '//form//button[contains(., "Sign In")]'))).click()

    try:
        wait.until(lambda d: "/login" not in d.current_url)
        print("Logged in successfully:", driver.current_url)
    except Exception:
        driver.save_screenshot("login_fail.png")
        print("Login failed. URL:", driver.current_url)
        raise