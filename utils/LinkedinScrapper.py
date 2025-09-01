import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Your company list and filters
COMPANIES = ["BlackRock", "Vanguard", "State Street", "Fidelity Investments", "Capital Group"]
KEYWORDS = ["asset management", "institutional sales"]
TITLES = ["director", "vp", "managing director", "managing partner", "head of sales", "wholesaler"]

def init_driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # Uncomment to run headlessly
    return webdriver.Chrome(options=options)

def scrape_jobs(company, driver):
    search_query = f"{company} {' '.join(KEYWORDS)}"
    url = f"https://www.linkedin.com/jobs/search/?keywords={search_query.replace(' ', '%20')}"
    driver.get(url)
    time.sleep(3)

    jobs = []
    job_cards = driver.find_elements(By.CLASS_NAME, "base-card")[:10]

    for card in job_cards:
        try:
            title = card.find_element(By.CLASS_NAME, "base-search-card__title").text.lower()
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            location = card.find_element(By.CLASS_NAME, "job-search-card__location").text
            posted = card.find_element(By.CLASS_NAME, "job-search-card__listdate").text
            company_name = company

            if any(t in title for t in TITLES):
                jobs.append({
                    "Job Title": title.title(),
                    "Company": company_name,
                    "Location": location,
                    "Posted Date": posted,
                    "Job URL": link,
                    "Description": ""  # We'll add this in phase 2
                })
        except Exception as e:
            print("Error reading card:", e)

    return jobs

def main():
    driver = init_driver()
    all_jobs = []

    for company in COMPANIES:
        print(f"Scraping jobs for {company}...")
        jobs = scrape_jobs(company, driver)
        all_jobs.extend(jobs)
        time.sleep(2)

    driver.quit()

    if all_jobs:
        df = pd.DataFrame(all_jobs)
        today = pd.Timestamp.today().strftime("%Y-%m-%d")
        df.to_csv(f"jobs_{today}.csv", index=False)
        print(f"\nSaved {len(df)} jobs to jobs_{today}.csv")
    else:
        print("\nNo jobs found matching criteria.")

if __name__ == "__main__":
    main()
