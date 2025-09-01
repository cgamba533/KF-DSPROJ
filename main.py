from utils.linkedin_login import init_driver, login_to_linkedin
from utils.scrape_jobs import search_jobs_for_company
import pandas as pd
import time
import os

COMPANIES = ["BlackRock", "Vanguard", "State Street", "Fidelity Investments", "Capital Group"]

## Titles should be lowercase as data scrapped from linkedin is converted and read as lowercase text
TITLES = [
    "director",
    "vp",
    "vice president",
    "managing director",
    "managing partner",
    "head of sales",
    "wholesaler",
    "analyst",
    "relationship management",
    "associate",
    "senior director",
    "executive director",
    "head of",
    "senior vp",
    "senior vice president",
    "consultant",
    "strategist",
    "trader",
    "sales",
    "advisor",
    "manager",
    "senior",
    "lead"
]

KEYWORDS = ["asset management"]


def main():
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    driver = init_driver()

    # Log in to LinkedIn
    login_to_linkedin(driver)

    all_jobs = []

    for company in COMPANIES:
        print(f"\n{'=' * 50}")
        print(f"Scraping jobs for {company}...")
        print(f"{'=' * 50}")

        jobs = search_jobs_for_company(driver, company, TITLES, KEYWORDS,
                                       use_ai_search=False)  # Try regular search first - use_ai_search=False
        all_jobs.extend(jobs)

        print(f"Total jobs found so far: {len(all_jobs)}")
        time.sleep(3)  # Delay time between searches

    driver.quit()

    if all_jobs:
        df = pd.DataFrame(all_jobs)
        today = pd.Timestamp.today().strftime("%Y-%m-%d")
        filename = f"data/jobs_{today}.csv"  # Fixed the typo here (was tocsv)
        df.to_csv(filename, index=False)
        print(f"\n[✓] SUCCESS! Saved {len(df)} jobs to {filename}")

        # Print summary
        print(f"\nSummary:")
        print(f"Companies searched: {len(COMPANIES)}")
        print(f"Jobs found: {len(all_jobs)}")
        if all_jobs:
            companies_found = df['Company'].nunique()
            print(f"Companies with matches: {companies_found}")
    else:
        print("\n[!] No jobs found matching your criteria.")
        print("Tips:")
        print("- Check your TITLES list matches job titles on LinkedIn")
        print("- Try broader/different KEYWORDS")
        print("- Make sure you're logged in successfully")


if __name__ == "__main__":
    main()