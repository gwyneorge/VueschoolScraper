from functools import wraps
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def do_in_new_window(func):
    @wraps(func)
    def wrapper(driver, lesson_url, *args, **kwargs):
        driver.switch_to.new_window("tab")
        driver.get(lesson_url)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
            )
        except Exception:
            print("Failed to load the lesson page in the new window.")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return "Page not loaded"

        try:
            return func(driver, lesson_url, *args, **kwargs)
        finally:
            # Close the tab and switch back to the main window
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    return wrapper