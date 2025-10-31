import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    # First, check if credentials are loaded
    print("\n" + "=" * 60)
    print("🔐 LINKEDIN LOGIN PROCESS")
    print("=" * 60)

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        print("❌ ERROR: LinkedIn credentials not found!")
        print("   Please create a .env file with:")
        print("   LINKEDIN_EMAIL=your.email@example.com")
        print("   LINKEDIN_PASSWORD=your_password")
        print("\n   Current values:")
        print(f"   LINKEDIN_EMAIL: {LINKEDIN_EMAIL}")
        print(f"   LINKEDIN_PASSWORD: {'*' * len(LINKEDIN_PASSWORD) if LINKEDIN_PASSWORD else 'None'}")
        return False

    print(f"✓ Credentials loaded:")
    print(f"  Email: {LINKEDIN_EMAIL}")
    print(f"  Password: {'*' * len(LINKEDIN_PASSWORD)}")

    cookies_file = "linkedin_cookies.pkl"

    # If cookies exist, try to use them
    if os.path.exists(cookies_file):
        print(f"\n🍪 Found existing cookies file: {cookies_file}")
        print("   Attempting to login with saved cookies...")

        driver.get("https://www.linkedin.com")
        time.sleep(2)

        try:
            with open(cookies_file, "rb") as f:
                cookies = pickle.load(f)

            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    pass

            driver.refresh()
            time.sleep(3)

            current_url = driver.current_url
            print(f"   Current URL after cookie login: {current_url}")

            if "feed" in current_url or "mynetwork" in current_url:
                print("✅ [SUCCESS] Logged in using saved cookies!")
                return True
            else:
                print("⚠️ Cookies expired or invalid, proceeding with normal login...")
                # Delete expired cookies
                try:
                    os.remove(cookies_file)
                    print(f"   Deleted expired cookies file")
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Error loading cookies: {e}")

    # Normal login flow
    print(f"\n🔑 Starting fresh login process...")
    print(f"   Navigating to: https://www.linkedin.com/login")

    driver.get("https://www.linkedin.com/login")
    time.sleep(3)

    try:
        print("   Locating username field...")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        print("   ✓ Username field found")

        print("   Entering email...")
        username_field.clear()
        username_field.send_keys(LINKEDIN_EMAIL)
        time.sleep(1)

        print("   Locating password field...")
        password_field = driver.find_element(By.ID, "password")
        print("   ✓ Password field found")

        print("   Entering password...")
        password_field.clear()
        password_field.send_keys(LINKEDIN_PASSWORD)
        time.sleep(1)

        print("   Locating submit button...")
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        print("   ✓ Submit button found")

        print("   Clicking login button...")
        submit_button.click()

        print("\n⏳ Waiting for login to complete (15 seconds)...")
        time.sleep(15)

        current_url = driver.current_url
        print(f"\n   Current URL: {current_url}")
        print(f"   Page title: {driver.title}")

        # Check if login was successful
        if "feed" in current_url or "mynetwork" in current_url:
            # Save cookies for future use
            with open(cookies_file, "wb") as f:
                pickle.dump(driver.get_cookies(), f)
            print("\n✅ [SUCCESS] Login successful! Cookies saved for future sessions.")
            return True

        elif "checkpoint" in current_url or "challenge" in current_url:
            print("\n⚠️ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("⚠️  VERIFICATION REQUIRED!")
            print("⚠️ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("   LinkedIn is asking for verification (CAPTCHA or security check)")
            print("   Please complete the verification in the browser window...")
            print("\n   👀 Look at your browser window and complete the challenge")
            print("   Waiting 60 seconds for you to complete it...")

            time.sleep(60)

            # Check again after waiting
            current_url = driver.current_url
            print(f"\n   Current URL after verification: {current_url}")

            if "feed" in current_url or "mynetwork" in current_url:
                with open(cookies_file, "wb") as f:
                    pickle.dump(driver.get_cookies(), f)
                print("✅ [SUCCESS] Verification completed! Cookies saved.")
                return True
            else:
                print("❌ Still not logged in after verification.")
                print("   You may need to complete the verification manually and restart the script.")
                return False

        elif "login" in current_url:
            print("\n❌ [ERROR] Still on login page!")
            print("   Possible reasons:")
            print("   1. Wrong email or password")
            print("   2. LinkedIn blocked the login (try from regular browser first)")
            print("   3. Account locked or suspended")

            # Try to find error messages
            try:
                error_elements = driver.find_elements(By.CSS_SELECTOR, ".alert-content, .form__label--error")
                if error_elements:
                    print("\n   Error messages found:")
                    for elem in error_elements:
                        error_text = elem.text.strip()
                        if error_text:
                            print(f"   - {error_text}")
            except:
                pass

            return False
        else:
            print(f"\n⚠️ Login status unclear. Current URL: {current_url}")
            print("   The script will continue but may encounter issues.")

            # Give it some more time
            print("   Waiting additional 10 seconds...")
            time.sleep(10)

            final_url = driver.current_url
            print(f"   Final URL: {final_url}")

            if "feed" in final_url or "mynetwork" in final_url:
                with open(cookies_file, "wb") as f:
                    pickle.dump(driver.get_cookies(), f)
                print("✅ [SUCCESS] Login successful after delay!")
                return True

            return False

    except Exception as e:
        print(f"\n❌ [ERROR] Exception during login: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Current URL: {driver.current_url}")
        print("\n   Troubleshooting:")
        print("   1. Make sure LINKEDIN_EMAIL and LINKEDIN_PASSWORD are set in .env")
        print("   2. Try logging in manually in a regular Chrome browser first")
        print("   3. Make sure your LinkedIn account is active")
        print("   4. Check if LinkedIn is blocking automated logins from your IP")
        return False