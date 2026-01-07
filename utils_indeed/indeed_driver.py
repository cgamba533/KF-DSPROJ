"""
IMPORTANT: Install undetected-chromedriver first:
pip install undetected-chromedriver

This library is specifically designed to bypass Cloudflare and other bot detection.
"""

import os  # Added for path handling
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    print("⚠️  WARNING: undetected-chromedriver not installed!")
    print("Install it with: pip install undetected-chromedriver")
    print("Falling back to regular Selenium (may not work with Cloudflare)")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    UNDETECTED_AVAILABLE = False


def init_driver(headless=False):
    """
    Initialize Chrome WebDriver using undetected-chromedriver to bypass Cloudflare.
    Uses a persistent user profile to save login state and cookies.
    """

    # --- PERSISTENT PROFILE SETUP ---
    # This creates a folder to save your cookies/login session
    current_dir = os.getcwd()
    profile_path = os.path.join(current_dir, "indeed_chrome_profile")
    os.makedirs(profile_path, exist_ok=True)
    print(f"📂 Using Chrome profile at: {profile_path}")
    # --------------------------------

    if UNDETECTED_AVAILABLE:
        print("✓ Using undetected-chromedriver (Cloudflare bypass enabled)")

        options = uc.ChromeOptions()

        # Add the persistent profile argument
        options.add_argument(f"--user-data-dir={profile_path}")

        # Basic options
        if not headless:  # Headless mode is less reliable with Cloudflare
            options.add_argument("--start-maximized")

        # Additional stealth options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        # Create driver with undetected-chromedriver
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=None,  # Auto-detect Chrome version
            headless=headless
        )

        # Set a reasonable page load timeout
        driver.set_page_load_timeout(30)

        print("✓ Driver initialized successfully")
        return driver

    else:
        # Fallback to regular Selenium (will likely fail with Cloudflare)
        print("⚠️  Using regular Selenium (Cloudflare may block)")
        options = Options()

        # Add the persistent profile argument to fallback as well
        options.add_argument(f"user-data-dir={profile_path}")

        if headless:
            options.add_argument("--headless=new")

        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(options=options)

        # Anti-detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver


def wait_for_page_load(driver, timeout=20):
    """
    Wait for Indeed page to fully load, handling Cloudflare if present.

    Args:
        driver: Selenium/UC WebDriver instance
        timeout: Maximum time to wait (seconds)

    Returns:
        bool: True if page loaded successfully, False otherwise
    """
    print("⏳ Waiting for page to load...")

    start_time = time.time()

    # Success indicators (Indeed job search page elements)
    success_selectors = [
        "div.job_seen_beacon",
        "[data-jk]",
        ".jobsearch-ResultsList",
        "#mosaic-provider-jobcards",
        "h1.jobsearch-JobCountAndSortPane-jobCount"
    ]

    while time.time() - start_time < timeout:
        # Check if Cloudflare challenge is present
        if "Additional Verification Required" in driver.page_source:
            print("⚠️  Cloudflare challenge detected - waiting for automatic bypass...")
            time.sleep(3)
            continue

        # Check for successful page load
        for selector in success_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    print(f"✓ Page loaded successfully (found: {selector})")
                    time.sleep(2)  # Extra time for dynamic content
                    return True
            except:
                continue

        # Check if we're on an error page
        if "Page not found" in driver.page_source or "No results" in driver.page_source:
            print("⚠️  No results found or error page detected")
            return False

        time.sleep(1)

    print(f"⚠️  Page load timeout after {timeout} seconds")

    # Last check - if we're on indeed.com and don't see Cloudflare, assume success
    if "indeed.com" in driver.current_url and "challenge" not in driver.current_url.lower():
        print("ℹ️  Assuming page loaded (on Indeed domain)")
        return True

    return False


def test_indeed_access(driver):
    """
    Test if we can access Indeed without being blocked.
    Useful for debugging Cloudflare issues.
    """
    print("\n🧪 Testing Indeed access...")

    try:
        driver.get("https://www.indeed.com")
        time.sleep(5)  # Give Cloudflare time to load if present

        if "Additional Verification Required" in driver.page_source:
            print("❌ Cloudflare verification required")
            print("💡 With undetected-chromedriver, this should auto-bypass. Wait a moment...")
            time.sleep(10)  # Give more time for auto-bypass

            if "Additional Verification Required" in driver.page_source:
                print("❌ Still blocked. Try:")
                print("   1. Make sure undetected-chromedriver is installed")
                print("   2. Update Chrome to the latest version")
                print("   3. Run: pip install --upgrade undetected-chromedriver")
                return False
            else:
                print("✓ Auto-bypass successful!")
                return True
        else:
            print("✓ Access successful - no Cloudflare challenge")
            return True

    except Exception as e:
        print(f"❌ Error testing access: {e}")
        return False