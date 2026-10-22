from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from decouple import config
import re

# Import your custom modules
from src.auth import login
from src.utils import handle_params, save, choose_content, get_course_info
from src.downloader import download_lesson_content


def main(selected_course):
    driver = None
    try:
        print("Initiating a driver...")

        driver_path = config("CHROMEDRIVER")
        download_path = config("DOWNLOAD_PATH") + selected_course

        service = Service(driver_path)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-notifications")
        prefs = {
            "download.default_directory": download_path,
            "profile.default_content_setting_values.notifications": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Done!")

        # Login
        print("Logging in...")
        login(driver)
        print("Done!")

        # Get the lessons
        print("Getting the lessons...")
        course = config("COURSE_URL") + selected_course
        print(f"Course URL: {course}")

        course_info = get_course_info(driver, course)
        lessons = course_info["lessons"]
        print(lessons)
        course_title = re.sub(r'[<>:"/\\|?*]', "", course_info["title"]).strip()
        print(f"Course Title: {course_title}")

        if not lessons:
            print("No lessons found. Exiting.")
            return

        # Get lesson range from handle_params
        download_range = handle_params(len(lessons))
        lessons = lessons[(download_range["from"] - 1): download_range["to"]]

        # Ask the user which content to download
        # choice = choose_content()
        choice = "6"

        if choice == "7":
            print("Exiting the program.")
            return

        source_code_urls = []
        wait_time = int(config("WAIT_TIME", default=25))

        lesson_index = download_range["from"]
        for lesson_url in lessons:
            print(f"Downloading lesson No. {lesson_index}...")

            repo_url = download_lesson_content(
                driver, lesson_url, lesson_index, course_title, choice, download_path
            )

            if choice == "3" or choice == "5":
                if repo_url not in ("Not Applicable", "Not Found", "Page not loaded"):
                    source_code_urls.append(repo_url)

            if lesson_index % 2 == 0:
                sleep(wait_time)
            else:
                sleep(wait_time / 2)

            lesson_index += 1

        if choice == "3" or choice == "5":
            save("repo", source_code_urls, download_range["from"], download_range["to"])

        print(f"Done! '{selected_course}' saved to {download_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if driver:
            driver.quit()


COURSES = [
]

for c in COURSES:
    main(c)