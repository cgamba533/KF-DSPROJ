# setup_login.py
import time
from utils_indeed.indeed_driver import init_driver


def setup_session():
    print("🚀 Launching browser for manual setup...")
    print("⚠️  DO NOT CLOSE THIS TERMINAL.")

    # Initialize the driver with the persistent profile
    driver = init_driver(headless=False)

    try:
        print("\n" + "=" * 60)
        print("INSTRUCTIONS:")
        print("1. The browser is now open.")
        print("2. Go to https://www.indeed.com")
        print("3. LOG IN manually with your account.")
        print("4. Solve any CAPTCHAs or Cloudflare checks.")
        print("5. Once you are logged in and see the homepage, you can close the browser.")
        print("=" * 60 + "\n")

        # Keep the script running until you close the browser manually
        while True:
            time.sleep(1)
            # Check if browser is still open
            try:
                _ = driver.window_handles
            except:
                break

    except Exception as e:
        print(f"Browser closed or error: {e}")
    finally:
        print("✅ Session saved! You can now run your main scraper.")


if __name__ == "__main__":
    setup_session()