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
    options = Options()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
    else:
        options.add_argument("--start-maximized")

    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)

    # Remove webdriver flag
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def login_to_linkedin(driver):
    """Login to LinkedIn with cookie persistence"""

    print("\n" + "=" * 70)
    print("🔐 LOGGING IN TO LINKEDIN")
    print("=" * 70)

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        print("❌ ERROR: LinkedIn credentials not found in .env file!")
        print("   Create a .env file with:")
        print("   LINKEDIN_EMAIL=your.email@example.com")
        print("   LINKEDIN_PASSWORD=your_password")
        return False

    print(f"✓ Email: {LINKEDIN_EMAIL}")
    print(f"✓ Password: {'*' * len(LINKEDIN_PASSWORD)}")

    cookies_file = "linkedin_cookies.pkl"

    # Try to use saved cookies first
    if os.path.exists(cookies_file):
        print(f"\n🍪 Found saved cookies, attempting login...")
        driver.get("https://www.linkedin.com")
        time.sleep(2)

        try:
            with open(cookies_file, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except:
                        pass

            driver.refresh()
            time.sleep(3)

            if "feed" in driver.current_url or "mynetwork" in driver.current_url:
                print("✅ Logged in successfully using cookies!")
                print("=" * 70 + "\n")
                return True
            else:
                print("⚠️ Cookies expired, proceeding with normal login...")
                os.remove(cookies_file)
        except Exception as e:
            print(f"⚠️ Cookie error: {e}")

    # Normal login flow
    print(f"\n🔑 Performing fresh login...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)

    try:
        # FIXED: Use By.ID instead of deprecated syntax
        print("   Entering email...")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_field.clear()
        username_field.send_keys(LINKEDIN_EMAIL)
        time.sleep(1)

        print("   Entering password...")
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(LINKEDIN_PASSWORD)
        time.sleep(1)

        print("   Clicking login button...")
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        print("   Waiting for login to complete...")
        time.sleep(10)

        current_url = driver.current_url

        # Check if login was successful
        if "feed" in current_url or "mynetwork" in current_url:
            # Save cookies
            with open(cookies_file, "wb") as f:
                pickle.dump(driver.get_cookies(), f)
            print("\n✅ Login successful! Cookies saved.")
            print("=" * 70 + "\n")
            return True

        elif "checkpoint" in current_url or "challenge" in current_url:
            print("\n⚠️ " + "=" * 66)
            print("⚠️  VERIFICATION REQUIRED!")
            print("⚠️ " + "=" * 66)
            print("   LinkedIn is asking for verification (CAPTCHA/security check)")
            print("   👀 Please complete it in the browser window...")
            print("   ⏳ Waiting 60 seconds...")

            time.sleep(60)

            # Check again
            if "feed" in driver.current_url or "mynetwork" in driver.current_url:
                with open(cookies_file, "wb") as f:
                    pickle.dump(driver.get_cookies(), f)
                print("\n✅ Verification completed! Cookies saved.")
                print("=" * 70 + "\n")
                return True
            else:
                print("❌ Still not logged in. You may need to restart.")
                return False

        elif "login" in current_url:
            print("\n❌ Login failed - still on login page!")
            print("   Possible reasons:")
            print("   1. Wrong email or password")
            print("   2. LinkedIn blocked the login")
            print("   3. Account locked")

            # Try to find error messages
            try:
                errors = driver.find_elements(By.CSS_SELECTOR, ".alert-content, .form__label--error")
                if errors:
                    print("\n   Error messages:")
                    for err in errors:
                        if err.text.strip():
                            print(f"   - {err.text.strip()}")
            except:
                pass

            return False

        else:
            print(f"\n⚠️ Unexpected URL: {current_url}")
            print("   Waiting 10 more seconds...")
            time.sleep(10)

            if "feed" in driver.current_url or "mynetwork" in driver.current_url:
                with open(cookies_file, "wb") as f:
                    pickle.dump(driver.get_cookies(), f)
                print("✅ Login successful after delay!")
                print("=" * 70 + "\n")
                return True

            return False

    except Exception as e:
        print(f"\n❌ Login exception: {e}")
        print(f"   Current URL: {driver.current_url}")
        return False