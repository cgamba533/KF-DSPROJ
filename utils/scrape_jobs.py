import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random


def extract_job_description(driver, job_url):
    """
    Opens a job posting in a new tab and extracts the 'About the job' text and posting date.
    Returns tuple: (description_text, posted_date)
    """
    description_text = ""
    posted_date = "N/A"
    original_window = driver.current_window_handle
    new_window = None

    try:
        # Open job in new tab
        driver.execute_script("window.open(arguments[0]);", job_url)
        time.sleep(2)

        # Switch to the new tab
        new_window = driver.window_handles[-1]
        driver.switch_to.window(new_window)
        time.sleep(3)

        # Try multiple selectors for the description
        description_selectors = [
            ".show-more-less-html__markup",
            ".jobs-description__content",
            ".jobs-box__html-content",
            "[class*='description']",
            ".jobs-description",
            "#job-details"
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

        if not description_elem:
            print(f"   ⚠️ No description element found with any selector")
            return description_text, posted_date

        # Try to click "Show more" button if it exists
        try:
            show_more_buttons = [
                "button.show-more-less-html__button",
                "button[aria-label*='Show more']",
                "button[aria-label*='show more']",
                ".show-more-less-html__button--more"
            ]

            for button_selector in show_more_buttons:
                try:
                    show_more = driver.find_element(By.CSS_SELECTOR, button_selector)
                    if show_more.is_displayed():
                        driver.execute_script("arguments[0].click();", show_more)
                        print(f"   ✓ Clicked 'Show more' button")
                        time.sleep(1)
                        break
                except (NoSuchElementException, Exception):
                    continue
        except Exception as e:
            print(f"   ℹ️ No 'Show more' button found (this is okay)")

        # Extract the description text
        description_text = description_elem.text.strip()

        if description_text:
            print(f"   ✓ Extracted description ({len(description_text)} characters)")
        else:
            print(f"   ⚠️ Description element found but text is empty")
            try:
                description_text = driver.execute_script("return arguments[0].innerText;", description_elem)
            except:
                pass

        # Extract posting date
        date_selectors = [
            ".jobs-unified-top-card__posted-date",
            ".job-details-jobs-unified-top-card__posted-date",
            "span.jobs-unified-top-card__subtitle-primary-grouping span:last-child",
            ".jobs-details__main-content span[class*='posted']",
        ]

        for date_sel in date_selectors:
            try:
                date_elem = driver.find_element(By.CSS_SELECTOR, date_sel)
                date_text = date_elem.text.strip()
                if any(word in date_text.lower() for word in ['ago', 'reposted', 'hour', 'day', 'week', 'month']):
                    posted_date = date_text
                    print(f"   ✓ Found posting date: {posted_date}")
                    break
            except:
                continue

        if posted_date == "N/A":
            try:
                top_card = driver.find_element(By.CSS_SELECTOR, ".jobs-unified-top-card")
                top_card_text = top_card.text
                lines = [line.strip() for line in top_card_text.split('\n') if line.strip()]
                for line in lines:
                    if any(word in line.lower() for word in ['ago', 'reposted', 'hour', 'day', 'week', 'month']):
                        posted_date = line
                        print(f"   ✓ Found posting date in top card: {posted_date}")
                        break
            except:
                pass

    except Exception as e:
        print(f"   ❌ Error extracting job description: {e}")
    finally:
        # CRITICAL: Always ensure we're back on the original tab
        try:
            # Close the new tab if it exists
            if new_window and new_window in driver.window_handles:
                driver.switch_to.window(new_window)
                driver.close()

            # Switch back to original window
            if original_window in driver.window_handles:
                driver.switch_to.window(original_window)
            else:
                # Fallback: switch to first available window
                driver.switch_to.window(driver.window_handles[0])

            time.sleep(0.5)

        except Exception as e:
            print(f"   ⚠️ Error managing tabs: {e}")
            try:
                if len(driver.window_handles) > 0:
                    driver.switch_to.window(driver.window_handles[0])
            except:
                pass

    return description_text, posted_date


def improved_scroll_and_load(driver, target_jobs=15, max_scroll_attempts=20):
    """
    IMPROVED: Aggressive scrolling with job clicking to trigger LinkedIn's lazy loading.
    This is the most reliable method for LinkedIn's current implementation.

    Args:
        target_jobs: Number of jobs we want to load (default: 15)
        max_scroll_attempts: Maximum scroll iterations (default: 20)
    """
    print(f"\n🔄 Starting IMPROVED scroll to load {target_jobs} jobs...")

    def count_visible_jobs():
        """Count currently visible job cards"""
        return len(
            driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id], .job-card-container, [data-job-id]"))

    # Wait for initial load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-occludable-job-id], [data-job-id]"))
        )
        time.sleep(2)
    except TimeoutException:
        print("   ⚠️ Initial job load timeout")

    previous_count = count_visible_jobs()
    print(f"   Initial jobs loaded: {previous_count}")

    stagnant_count = 0

    for attempt in range(max_scroll_attempts):
        # Strategy 1: Click on the last visible job (triggers loading)
        try:
            job_cards = driver.find_elements(By.CSS_SELECTOR,
                                             "li[data-occludable-job-id], .job-card-container, [data-job-id]")
            if job_cards:
                last_job = job_cards[-1]
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", last_job)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", last_job)
                print(f"   ✓ Clicked job {len(job_cards)}")
                time.sleep(2)
        except Exception as e:
            print(f"   ⚠️ Could not click job: {e}")

        # Strategy 2: Scroll the jobs list container
        scroll_script = """
        // Find the scrollable container
        let containers = document.querySelectorAll(
            'div.jobs-search-results-list, ' +
            'ul.scaffold-layout__list-container, ' +
            'div.scaffold-layout__list-container, ' +
            'div[class*="jobs-search-results"]'
        );

        let scrolled = false;
        for (let container of containers) {
            if (container.scrollHeight > container.clientHeight) {
                container.scrollBy(0, 800);
                scrolled = true;
                break;
            }
        }

        // Fallback: scroll window
        if (!scrolled) {
            window.scrollBy(0, 800);
        }

        return scrolled;
        """

        try:
            container_scrolled = driver.execute_script(scroll_script)
            if container_scrolled:
                print(f"   ✓ Scrolled container")
            else:
                print(f"   ✓ Scrolled window (fallback)")
        except Exception as e:
            print(f"   ⚠️ Scroll error: {e}")

        # Wait for LinkedIn to load more jobs
        time.sleep(3)

        # Check progress
        current_count = count_visible_jobs()
        new_jobs = current_count - previous_count

        print(f"   Scroll #{attempt + 1}: {current_count} jobs visible (+{new_jobs} new)")

        # Check if we've reached target
        if current_count >= target_jobs:
            print(f"\n✅ Target reached! {current_count} jobs loaded")
            return current_count

        # Check if we're stuck
        if current_count == previous_count:
            stagnant_count += 1

            if stagnant_count >= 3:
                # Try aggressive recovery
                print(f"   ⚠️ No progress after {stagnant_count} attempts, trying recovery...")

                # Try scrolling to top then bottom
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

                # Check again
                recovery_count = count_visible_jobs()
                if recovery_count > current_count:
                    print(f"   ✓ Recovery successful! Now at {recovery_count} jobs")
                    current_count = recovery_count
                    stagnant_count = 0
                elif stagnant_count >= 5:
                    print(f"   ⚠️ Stuck at {current_count} jobs, stopping scroll")
                    break
        else:
            stagnant_count = 0

        previous_count = current_count

    final_count = count_visible_jobs()
    print(f"\n📊 Scroll complete: {final_count} jobs loaded (target was {target_jobs})")
    return final_count


def search_jobs_for_company(driver, company, titles, keywords, max_results=15, use_ai_search=False, max_descriptions=10,
                            location="United States", use_interactive_scroll=False):
    """
    Search for jobs at a specific company and filter by titles

    Args:
        driver: Selenium WebDriver instance
        company: Company name to search for
        titles: List of job titles to filter by
        keywords: Additional keywords for search
        max_results: Maximum number of job cards to process (default: 15)
        use_ai_search: Use LinkedIn AI search mode (default: False)
        max_descriptions: Maximum number of job descriptions to extract (default: 10)
                         Set to None to extract all descriptions
        location: Location filter for job search (default: "United States")
        use_interactive_scroll: DEPRECATED - now uses improved scroll by default

    Returns:
        List of job dictionaries with job information
    """
    search_query = f"{company} {' '.join(keywords)}"
    encoded_query = search_query.replace(' ', '%20')
    encoded_location = location.replace(' ', '%20').replace(',', '%2C')

    if use_ai_search:
        search_url = f"https://www.linkedin.com/jobs/search-results/?keywords={encoded_query}&location={encoded_location}&origin=SEMANTIC_SEARCH_MODE_FROM_CLASSIC"
    else:
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}&location={encoded_location}"

    print(f"Searching: {search_url}")
    print(f"Location: {location}")
    print(f"Using {'AI' if use_ai_search else 'Regular'} search mode")
    driver.get(search_url)

    # Wait for page to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-job-id], li[data-occludable-job-id]"))
        )
    except:
        print("Page load timeout, continuing anyway...")

    time.sleep(3)

    # STEP 1: SCROLL TO LOAD JOBS (using improved method)
    total_loaded = improved_scroll_and_load(driver, target_jobs=max_results, max_scroll_attempts=20)

    # STEP 2: NOW get all the job cards
    selectors = [
        "li[data-occludable-job-id]",
        "[data-job-id]",
        ".jobs-search-results__list-item",
        ".base-card",
        ".job-card-container",
    ]

    job_cards = []
    for selector in selectors:
        job_cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if job_cards:
            print(f"Found {len(job_cards)} job cards using selector: {selector}")
            break

    if not job_cards:
        print("❌ No job cards found.")
        return []

    # Limit to max_results
    job_cards = job_cards[:max_results]
    print(f"Processing {len(job_cards)} job cards (limited to max_results={max_results})\n")

    results = []
    descriptions_extracted = 0

    # STEP 3: Process all loaded job cards
    for i, card in enumerate(job_cards):
        try:
            # Extract job title
            title_text = ""
            title_selectors = [
                "h3.base-search-card__title a span[aria-hidden='true']",
                "h3 a span[title]",
                ".base-search-card__title a",
                ".job-card-list__title a",
                "h3 a span:first-child",
                ".jobs-unified-top-card__job-title",
                "a[data-tracking-control-name='public_jobs_jserp-result_search-card'] span[aria-hidden='true']"
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
                card_text = card.text.strip()
                if card_text:
                    title_text = card_text.split('\n')[0]

            if not title_text:
                continue

            # Title matching logic
            title_lower = title_text.lower()
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

            # Extract job details
            company_text = company
            location_text = "N/A"
            posted_text = "N/A"
            job_url = "N/A"

            try:
                card_lines = [line.strip() for line in card.text.split('\n') if line.strip()]

                for idx, line in enumerate(card_lines[1:4], start=1):
                    if line and line != title_text and 'verification' not in line.lower():
                        if not any(word in line.lower() for word in
                                   ['viewed', 'ago', 'hour', 'day', 'week', 'month', '$', 'applicant']):
                            if ',' in line:
                                location_text = line
                                break
                            elif idx == 1 and line != company:
                                company_text = line
            except:
                pass

            # Extract job URL
            for link_sel in [
                "a[href*='/jobs/view/']",
                ".base-card__full-link",
                "[data-job-id] a"
            ]:
                try:
                    link_elem = card.find_element(By.CSS_SELECTOR, link_sel)
                    job_url = link_elem.get_attribute("href")
                    if job_url:
                        break
                except:
                    continue

            # Extract Job Description and Date
            description_text = ""
            should_extract_description = (max_descriptions is None) or (descriptions_extracted < max_descriptions)

            if should_extract_description and job_url and job_url != "N/A":
                print(f"   📄 Job #{len(results) + 1}: {title_text}")
                print(f"   🔗 Opening: {job_url}")
                description_text, posted_text = extract_job_description(driver, job_url)
                descriptions_extracted += 1
                time.sleep(2)
            elif not should_extract_description:
                print(f"   ⏭️  Skipping description extraction (limit reached: {max_descriptions})")

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
            print(f"❌ Error processing job card {i + 1}: {e}")
            continue

    print(f"\n📊 SUMMARY for {company}:")
    print(f"   - Total job cards processed: {len(job_cards)}")
    print(f"   - Jobs matching title criteria: {len(results)}")
    print(f"   - Jobs with descriptions: {sum(1 for j in results if j.get('Description'))}")

    return results