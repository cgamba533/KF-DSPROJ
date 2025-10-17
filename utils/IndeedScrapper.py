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
    # Build company job page URL
    base_company = company.replace(" ", "-")
    url = f"https://www.indeed.com/cmp/{base_company}/jobs"
    driver.get(url)
    time.sleep(3)

    jobs = []

    # Find all job cards on the page
    job_cards = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='job-link']")

    for card in job_cards[:10]:  # limit to first 10 jobs per company
        try:
            title = card.find_element(By.CSS_SELECTOR, "span.jobTitle").text.lower()
            link = card.get_attribute("href")

            # Sometimes location/post date are in sibling elements
            location = ""
            posted = ""
            try:
                location_elem = card.find_element(By.CSS_SELECTOR, "div[data-testid='job-location']")
                location = location_elem.text.strip()
            except:
                pass

            try:
                posted_elem = card.find_element(By.CSS_SELECTOR, "span[data-testid='job-age']")
                posted = posted_elem.text.strip()
            except:
                pass

            company_name = company

            # Filter by titles
            if any(t in title for t in TITLES):
                jobs.append({
                    "Job Title": title.title(),
                    "Company": company_name,
                    "Location": location,
                    "Posted Date": posted,
                    "Job URL": link,
                    "Description": ""
                })

        except Exception as e:
            print(f"Error reading card for {company}: {e}")

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
        df.to_csv(f"indeed_jobs_{today}.csv", index=False)
        print(f"\n✅ Saved {len(df)} jobs to indeed_jobs_{today}.csv")
    else:
        print("\n⚠️ No jobs found matching criteria.")

if __name__ == "__main__":
    main()
