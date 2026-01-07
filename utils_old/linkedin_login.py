import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pickle

load_dotenv()  # Load from .env file

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

def init_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)

def login_to_linkedin(driver):
    cookies_file = "linkedin_cookies.pkl"

    # If cookies exist, load them
    if os.path.exists(cookies_file):
        driver.get("https://www.linkedin.com")
        with open(cookies_file, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(2)
        if "feed" in driver.current_url:
            print("[✓] Logged in using saved cookies.")
            return

    # Otherwise, do normal login
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    driver.find_element("id", "username").send_keys(LINKEDIN_EMAIL)
    driver.find_element("id", "password").send_keys(LINKEDIN_PASSWORD)
    driver.find_element("xpath", "//button[@type='submit']").click()
    time.sleep(10)

    # Save cookies for next time
    with open(cookies_file, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

    if "feed" in driver.current_url:
        print("[✓] Login successful, cookies saved.")
    else:
        print("[!] Login failed or verification required.")
