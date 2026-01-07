from utils_indeed.indeed_driver import init_driver
from utils_indeed.scrape_indeed_jobs import search_jobs_for_company
import pandas as pd
import time
import os
import datetime

# --- CONFIGURATION ---
COMPANIES = [
    "Royal Bank of Canada",
    "TCW",
    "Lincoln Financial",
    "Natixis",
    "AssetMark",
    "Aristotle Capital Management",
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

TITLES = [
    "head of distribution",
    "head of",
    "regional director",
    "national accounts",
    "national account manager",
    "chief marketing officer",
    "vice president",
    "executive",
    "chief of",
    "cmo",
    "chief",
    "director",
    "",
]

KEYWORDS = [
    "head of distribution OR regional director OR national accounts OR chief marketing officer OR vice president OR executive OR director OR managing director OR asset management"]

# Exclusion keywords
EXCLUDE_KEYWORDS = ["intern", "internship"]


def get_unique_filename(base_path="data"):
    """
    Generates a unique filename. If the file is open or exists,
    it adds a number (e.g., jobs_date_1.csv) to avoid overwriting or errors.
    """
    os.makedirs(base_path, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    base_name = f"indeed_jobs_{today}"
    extension = ".csv"

    counter = 0
    while True:
        if counter == 0:
            filename = os.path.join(base_path, f"{base_name}{extension}")
        else:
            filename = os.path.join(base_path, f"{base_name}_{counter}{extension}")

        # Check if file exists. If it does, try to open it in append mode to check for locks.
        if os.path.exists(filename):
            try:
                # If we can open it to append, it's not locked by Excel.
                # However, we might want a FRESH file for a new run, so we increment anyway.
                # Remove the next 2 lines if you prefer appending to the SAME file.
                counter += 1
                continue
            except PermissionError:
                print(f"⚠️  File {filename} is locked/open. Trying next number...")
                counter += 1
                continue

        # If we get here, the filename is free to use
        return filename


def save_batch_to_csv(jobs_list, filename):
    """
    Appends a list of jobs to the CSV file.
    """
    if not jobs_list:
        return

    df = pd.DataFrame(jobs_list)

    # Check if file exists to determine if we need to write the header
    file_exists = os.path.isfile(filename)

    try:
        df.to_csv(filename, mode='a', header=not file_exists, index=False)
        print(f"   💾 Saved batch of {len(jobs_list)} jobs to {filename}")
    except PermissionError:
        print(f"   ❌ CRITICAL: Could not save to {filename} (Permission Denied). Data held in memory.")


def main():
    driver = init_driver(headless=False)

    # 1. Get a safe filename immediately
    current_filename = get_unique_filename()
    print(f"\n📁 Data will be saved incrementally to: {current_filename}")

    total_jobs_found = 0

    try:
        for company in COMPANIES:
            print(f"\n{'=' * 50}")
            print(f"Scraping jobs for {company}...")
            print(f"{'=' * 50}")

            # 2. Scrape one company
            jobs = search_jobs_for_company(
                driver,
                company,
                TITLES,
                KEYWORDS,
                EXCLUDE_KEYWORDS,
                max_results=20,  # Increased slightly
                max_descriptions=20
            )

            # 3. Save immediately (Redundancy)
            if jobs:
                save_batch_to_csv(jobs, current_filename)
                total_jobs_found += len(jobs)

            print(f"Total jobs collected so far: {total_jobs_found}")

            # Short pause between companies
            time.sleep(3)

    except Exception as e:
        print(f"\n⚠️  An error occurred during the loop: {e}")
        print("Data collected so far is safe in the CSV file.")

    finally:
        print("\nClosing driver...")
        driver.quit()

    # Final Summary
    print(f"\n{'-' * 30}")
    print(f"🏁 SCRAPE COMPLETE")
    print(f"Total Companies: {len(COMPANIES)}")
    print(f"Total Jobs Saved: {total_jobs_found}")
    print(f"File Location: {current_filename}")
    print(f"{'-' * 30}")


if __name__ == "__main__":
    main()