import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pickle

load_dotenv()

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")


def init_driver(headless=False):
    """
    Initialize Chrome WebDriver with proper options.

    Args:
        headless (bool): If True, runs browser in headless mode (no visible window)
    """
    options = Options()

    if headless:
        # CORRECT headless syntax for newer Selenium versions
        options.add_argument("--headless=new")  # Use new headless mode
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")  # Set window size for headless
        print("🔇 Running in HEADLESS mode (no browser window)")
    else:
        options.add_argument("--start-maximized")
        print("🖥️  Running with VISIBLE browser window")

    # Additional options to avoid detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)

    # Remove webdriver property to avoid detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def login_to_linkedin(driver):
    """
    Log in to LinkedIn using credentials from .env file.
    Uses cookie persistence to avoid repeated logins.
    """
    cookies_file = "linkedin_cookies.pkl"

    # If cookies exist, try to use them
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
        else:
            print("[ℹ️] Cookies expired, proceeding with normal login...")

    # Normal login flow
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    try:
        driver.find_element("id", "username").send_keys(LINKEDIN_EMAIL)
        driver.find_element("id", "password").send_keys(LINKEDIN_PASSWORD)
        driver.find_element("xpath", "//button[@type='submit']").click()

        print("[⏳] Logging in... (waiting 10 seconds)")
        time.sleep(10)

        # Check if login was successful
        if "feed" in driver.current_url or "mynetwork" in driver.current_url:
            # Save cookies for future use
            with open(cookies_file, "wb") as f:
                pickle.dump(driver.get_cookies(), f)
            print("[✓] Login successful! Cookies saved for future sessions.")
        elif "checkpoint" in driver.current_url or "challenge" in driver.current_url:
            print("[!] ⚠️  VERIFICATION REQUIRED!")
            print("    LinkedIn is asking for verification (CAPTCHA or security check)")
            print("    Please complete the verification in the browser window...")
            print("    Waiting 60 seconds for you to complete it...")
            time.sleep(60)

            # Check again after waiting
            if "feed" in driver.current_url:
                with open(cookies_file, "wb") as f:
                    pickle.dump(driver.get_cookies(), f)
                print("[✓] Verification completed! Cookies saved.")
            else:
                print("[!] Still not logged in. The script will continue but may fail.")
        else:
            print("[!] Login status unclear. Current URL:", driver.current_url)
            print("    The script will continue but may encounter issues.")

    except Exception as e:
        print(f"[❌] Error during login: {e}")
        print("    Make sure LINKEDIN_EMAIL and LINKEDIN_PASSWORD are set in your .env file")