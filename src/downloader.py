import os
import re
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from decouple import config
from html2text import html2text

from src.browser import do_in_new_window
from src.utils import check_exists_by_css_selector


def safe_name(text):
    return re.sub(r'[<>:"/\\|?*]', "_", text).strip()


def dismiss_popups(driver):
    driver.execute_script("""
        document.querySelectorAll(
            '#onesignal-slidedown-container, #onesignal-slidedown-dialog, .onesignal-slidedown-container'
        ).forEach(e => e.remove());
    """)


def http_download(driver, url, base_name, default_ext):
    download_path = config("DOWNLOAD_PATH")

    session = requests.Session()
    for c in driver.get_cookies():
        session.cookies.set(c["name"], c["value"], domain=c.get("domain"))
    session.headers["User-Agent"] = driver.execute_script("return navigator.userAgent")

    with session.get(url, stream=True, timeout=(15, 60), allow_redirects=True) as r:
        print(f"  HTTP {r.status_code} -> {r.url[:90]}")
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "")
        if "text/html" in ctype:
            raise RuntimeError(f"Got HTML instead of a file ({ctype})")

        ext = default_ext
        m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', r.headers.get("Content-Disposition", ""))
        if m:
            ext = os.path.splitext(m.group(1))[1] or default_ext

        path = os.path.join(download_path, safe_name(base_name) + ext)
        if os.path.exists(path):
            print(f"  Already exists, skipping: {path}")
            return path

        total = int(r.headers.get("Content-Length", 0))
        done, last = 0, -1
        with open(path + ".part", "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = done * 100 // total
                    if pct != last and pct % 10 == 0:
                        print(f"  {pct}% ({done // 1048576} MB)")
                        last = pct
        os.replace(path + ".part", path)
    return path
@do_in_new_window
def download_lesson_content(driver, lesson_url, lesson_index, course_title, choice):
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
    dismiss_popups(driver)

    lesson_title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
    print(f"Processing lesson: {lesson_title}")
    base = f"Vue School - {course_title} - {lesson_index} {lesson_title}"

    repo_elem_url = "Not Applicable"

    if choice in ["1", "3", "6"]:
        print(f"Downloading lesson video for {lesson_title}...")
        download_lesson(driver, base + " - HD")

    if choice in ["2", "3", "6"]:
        print(f"Downloading transcript for {lesson_title}...")
        download_transcript(driver, base + " - HD")

    if choice in ["4", "6"]:
        print(f"Getting source code link for {lesson_title}...")
        repo_elem_url = get_source_code_link(driver)

    if choice in ["5", "6"]:
        print(f"Downloading description for {lesson_title}...")
        download_description(driver, base + " - Description")

    return repo_elem_url


def download_lesson(driver, base_name):
    try:
        link = driver.find_element(By.CSS_SELECTOR, 'a[href*="/download/"][href$="/hd"]')
        path = http_download(driver, link.get_attribute("href"), base_name, ".mp4")
        print(f"Lesson video saved: {path}")
    except Exception as e:
        print(f"Failed to download the lesson: {e}")


def download_transcript(driver, base_name):
    css = 'a[href$="/download-transcript"]'
    if not check_exists_by_css_selector(driver, css):
        print("No transcript link found.")
        return False
    try:
        href = driver.find_element(By.CSS_SELECTOR, css).get_attribute("href")
        path = http_download(driver, href, base_name, ".vtt")
        print(f"Transcript saved: {path}")
        return True
    except Exception as e:
        print(f"Failed to download transcript: {e}")
        return False


def get_source_code_link(driver):
    els = driver.find_elements(By.CSS_SELECTOR, 'a[title^="Download the source code"]')
    return els[0].get_attribute("href") if els else "Not Found"


def download_description(driver, base_name):
    css = "div.prose"
    if not check_exists_by_css_selector(driver, css):
        print("No description found.")
        return
    html = driver.find_element(By.CSS_SELECTOR, css).get_attribute("innerHTML")
    path = os.path.join(config("DOWNLOAD_PATH"), safe_name(base_name) + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html2text(html))
    print(f"Description saved: {path}")