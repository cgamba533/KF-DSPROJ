from utils.linkedin_login import init_driver, login_to_linkedin
from utils.scrape_jobs import search_jobs_for_company
import pandas as pd
import time
import os

COMPANIES = [
    "Royal Bank of Canada",
    "TCW",
    "Lincoln Financial",
    "Natixis",
    "AssetMark",
    "Aristotle",
    "Pathstone",
    "Fidelity",
    "Orion",
    "NEPC",
    "Invesco",
    "Janney Montgomery Scott LLC",
    "Northern Trust",
    "SEI",
    "Macquarie Asset Management",
    "BNY Mellon",
    "AllianceBernstein",
    "Russell Investments"
    ]

## Titles should be lowercase as data scrapped from linkedin is converted and read as lowercase text
TITLES = [
    "head of distribution",
    "head of",
    "regional director",
    "national accounts",
    "national account manager",
    "chief marketing officer",
    "head of",
    "vice president",
    "executive",
    "chief of",
    "cmo",
    "chief marketing officer",
    "chief",
    "director",
    "",
]

KEYWORDS = []


def main():
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    driver = init_driver(headless=False)    # Change to true to make headless scrapping

    # Log in to LinkedIn
    # login_to_linkedin(driver)

    all_jobs = []

    for company in COMPANIES:
        print(f"\n{'=' * 50}")
        print(f"Scraping jobs for {company}...")
        print(f"{'=' * 50}")

        jobs = search_jobs_for_company(driver, company, TITLES, KEYWORDS,
                                       use_ai_search=False, max_results=12, max_descriptions=8)  # Try regular search first - use_ai_search=False
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