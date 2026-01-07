import time
import random  # Added for human-like delays
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from utils_indeed.indeed_driver import wait_for_page_load


def extract_job_description(driver, job_url):
    """
    Opens a job posting in a new tab and extracts the job description and posting date.
    Returns tuple: (description_text, posted_date)
    """
    description_text = ""
    posted_date = "N/A"

    # Store the original window handle (the job list) to ensure we can return
    original_window = driver.current_window_handle

    try:
        # Open a new tab safely using Selenium's native method
        driver.switch_to.new_window('tab')
        driver.get(job_url)

        # RANDOMIZED DELAY: Wait 3 to 6 seconds (like a human reading the page load)
        time.sleep(random.uniform(3, 6))

        # Indeed job description selectors
        description_selectors = [
            "#jobDescriptionText",
            ".jobsearch-jobDescriptionText",
            "[id*='jobDescriptionText']",
            ".job-description",
            "[class*='jobDescriptionText']"
        ]

        description_elem = None
        for selector in description_selectors:
            try:
                description_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if description_elem:
                    print(f"   ✓ Found description using selector: {selector}")
                    break
            except TimeoutException:
                continue

        if description_elem:
            description_text = description_elem.text.strip()
            if description_text:
                print(f"   ✓ Extracted description ({len(description_text)} characters)")
                # RANDOMIZED DELAY: Wait 1 to 3 seconds (simulating reading/scanning)
                time.sleep(random.uniform(1, 3))
            else:
                try:
                    description_text = driver.execute_script("return arguments[0].innerText;", description_elem)
                except:
                    pass

        # Extract posting date from Indeed
        date_selectors = [
            ".jobsearch-JobMetadataFooter",
            "[class*='metadata'] span",
            ".jobsearch-JobMetadataHeader-item",
            "[data-testid='jobsearch-JobMetadataHeader-item']"
        ]

        for date_sel in date_selectors:
            try:
                date_elems = driver.find_elements(By.CSS_SELECTOR, date_sel)
                for elem in date_elems:
                    date_text = elem.text.strip()
                    if any(word in date_text.lower() for word in
                           ['ago', 'today', 'yesterday', 'hour', 'day', 'month', 'posted']):
                        posted_date = date_text
                        print(f"   ✓ Found posting date: {posted_date}")
                        break
                if posted_date != "N/A":
                    break
            except:
                continue

    except Exception as e:
        print(f"   ✗ Error extracting job description: {e}")

    finally:
        # ROBUST TAB CLEANUP
        try:
            # If we are on a different tab than the original, close it
            if driver.current_window_handle != original_window:
                driver.close()

            # Switch back to the original window
            driver.switch_to.window(original_window)
            time.sleep(0.5)

        except Exception as e:
            print(f"   ⚠️ Critical error returning to main list: {e}")
            # Emergency fallback: try to switch to the first handle available
            if len(driver.window_handles) > 0:
                driver.switch_to.window(driver.window_handles[0])

    return description_text, posted_date


def scroll_and_load_jobs(driver, target_jobs=15, max_scroll_attempts=10):
    """
    Scroll through Indeed's job listings to load more results.
    Indeed uses infinite scroll for job loading.
    """
    print(f"\n🔄 Starting scroll to load {target_jobs} jobs...")

    def count_visible_jobs():
        """Count currently visible job cards"""
        try:
            job_cards = driver.find_elements(By.CSS_SELECTOR,
                                             "div.job_seen_beacon, .jobsearch-ResultsList > li, [data-jk], .slider_item")
            return len(job_cards)
        except:
            return 0

    # Wait for initial load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_seen_beacon, [data-jk]"))
        )
        time.sleep(2)
    except TimeoutException:
        print("   ⚠️ Initial job load timeout")

    previous_count = count_visible_jobs()
    print(f"   Initial jobs loaded: {previous_count}")

    stagnant_count = 0

    for attempt in range(max_scroll_attempts):
        # Scroll down
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # RANDOMIZED DELAY: 2 to 4 seconds between scrolls
            time.sleep(random.uniform(2, 4))

            # Also scroll the job list container if it exists
            try:
                job_list = driver.find_element(By.CSS_SELECTOR, ".jobsearch-ResultsList, #mosaic-provider-jobcards")
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", job_list)
            except:
                pass
        except:
            break

        time.sleep(1)  # Small buffer

        current_count = count_visible_jobs()
        new_jobs = current_count - previous_count

        print(f"   Scroll #{attempt + 1}: {current_count} jobs visible (+{new_jobs} new)")

        if current_count >= target_jobs:
            print(f"\n✅ Target reached! {current_count} jobs loaded")
            return current_count

        if current_count == previous_count:
            stagnant_count += 1
            if stagnant_count >= 3:
                print(f"   ⚠️ No new jobs loaded after {stagnant_count} attempts, stopping")
                break
        else:
            stagnant_count = 0

        previous_count = current_count

    final_count = count_visible_jobs()
    print(f"\n📊 Scroll complete: {final_count} jobs loaded (target was {target_jobs})")
    return final_count


def search_jobs_for_company(driver, company, titles, keywords, exclude_keywords,
                            max_results=15, max_descriptions=10, location="United States"):
    """
    Search for jobs at a specific company on Indeed and filter by titles.
    """
    # Build Indeed search query
    search_terms = f'{company} {" ".join(keywords)}'

    # URL encode the parameters
    encoded_query = urllib.parse.quote(search_terms)
    encoded_location = urllib.parse.quote(location)

    search_url = f"https://www.indeed.com/jobs?q={encoded_query}&l={encoded_location}"

    print(f"Searching: {search_url}")
    print(f"Location: {location}")
    print(f"Company: {company}")

    driver.get(search_url)

    # Wait for page to load and handle Cloudflare automatically
    if not wait_for_page_load(driver, timeout=30):
        print("❌ Page failed to load properly. Skipping this company.")
        return []

    time.sleep(random.uniform(2, 4))  # Randomized initial buffer

    # Scroll to load more jobs
    scroll_and_load_jobs(driver, target_jobs=max_results, max_scroll_attempts=10)

    # Get all job cards
    job_card_selectors = [
        "div.job_seen_beacon",
        ".jobsearch-ResultsList > li",
        "[data-jk]",
        ".slider_item"
    ]

    job_cards = []
    for selector in job_card_selectors:
        job_cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if job_cards:
            print(f"Found {len(job_cards)} job cards using selector: {selector}")
            break

    if not job_cards:
        print("✗ No job cards found.")
        return []

    # Limit to max_results
    job_cards = job_cards[:max_results]
    print(f"Processing {len(job_cards)} job cards (limited to max_results={max_results})\n")

    results = []
    descriptions_extracted = 0

    for i, card in enumerate(job_cards):
        try:
            # Check if driver is still alive before processing
            if not driver.window_handles:
                print("💥 CRITICAL: Browser session lost. Stopping search.")
                break

            # Extract job title
            title_text = ""
            title_selectors = [
                "h2.jobTitle span[title]",
                ".jobTitle a span",
                "h2.jobTitle",
                "[data-jk] h2"
            ]

            for title_sel in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, title_sel)
                    title_text = title_elem.text.strip()
                    if title_text:
                        break
                except:
                    continue

            if not title_text:
                continue

            # Check exclusion keywords first
            title_lower = title_text.lower()
            if any(exclude_word.lower() in title_lower for exclude_word in exclude_keywords):
                print(f"   ✗ Excluded by keyword: '{title_text}'")
                continue

            # Title matching logic
            title_match = False
            if "" in titles or any(not t.strip() for t in titles):
                title_match = True
                print(f"   ✓ Match all mode enabled - accepting: '{title_text}'")
            else:
                for target_title in titles:
                    target_title_clean = target_title.strip().lower()
                    if target_title_clean and target_title_clean in title_lower:
                        title_match = True
                        print(f"   ✓ Title match found: '{target_title}' in '{title_text}'")
                        break

            if not title_match:
                print(f"   ✗ No title match for: '{title_text}'")
                continue

            # Extract company name
            company_text = "N/A"
            company_selectors = [
                "[data-testid='company-name']",
                ".companyName",
                "span.companyName",
                "[class*='companyName']"
            ]

            for company_sel in company_selectors:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, company_sel)
                    company_text = company_elem.text.strip()
                    if company_text:
                        print(f"   ✓ Found company: {company_text}")
                        break
                except:
                    continue

            if company_text == "N/A":
                company_text = company

            # Extract location
            location_text = "N/A"
            location_selectors = [
                "[data-testid='text-location']",
                ".companyLocation",
                "div.companyLocation",
                "[class*='companyLocation']"
            ]

            for loc_sel in location_selectors:
                try:
                    loc_elem = card.find_element(By.CSS_SELECTOR, loc_sel)
                    location_text = loc_elem.text.strip()
                    if location_text:
                        print(f"   ✓ Found location: {location_text}")
                        break
                except:
                    continue

            # Extract job URL
            job_url = "N/A"
            try:
                # Get the job ID from data-jk attribute
                job_id = card.get_attribute("data-jk")
                if job_id:
                    job_url = f"https://www.indeed.com/viewjob?jk={job_id}"
                else:
                    # Try to find the link
                    link_elem = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a, a[data-jk]")
                    job_url = link_elem.get_attribute("href")
            except:
                pass

            # Extract Job Description and Date
            description_text = ""
            posted_text = "N/A"
            should_extract_description = (max_descriptions is None) or (descriptions_extracted < max_descriptions)

            if should_extract_description and job_url and job_url != "N/A":
                print(f"   📄 Job #{len(results) + 1}: {title_text}")
                print(f"   🔗 Opening: {job_url}")
                description_text, posted_text = extract_job_description(driver, job_url)
                descriptions_extracted += 1

                # RANDOMIZED DELAY: Wait 2-5 seconds between jobs (like a human deciding to click the next one)
                time.sleep(random.uniform(2, 5))

            elif not should_extract_description:
                print(f"   ⏭️ Skipping description extraction (limit reached: {max_descriptions})")

            # Try to get posted date from card if not extracted from detail page
            if posted_text == "N/A":
                try:
                    date_elem = card.find_element(By.CSS_SELECTOR, ".date, [class*='date']")
                    posted_text = date_elem.text.strip()
                except:
                    pass

            # Save job data
            job_data = {
                "Job Title": title_text,
                "Company": company_text,
                "Location": location_text,
                "Posted Date": posted_text,
                "Job URL": job_url,
                "Description": description_text
            }

            results.append(job_data)
            print(f"✓ Added job #{len(results)}: {title_text} at {company_text}\n")

        except Exception as e:
            print(f"✗ Error processing job card {i + 1}: {e}")
            continue

    print(f"\n📊 SUMMARY for {company}:")
    print(f"   - Total job cards processed: {len(job_cards)}")
    print(f"   - Jobs matching title criteria: {len(results)}")
    print(f"   - Jobs with descriptions: {sum(1 for j in results if j.get('Description'))}")

    return results