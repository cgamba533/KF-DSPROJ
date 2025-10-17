import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


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


def debug_scroll_state(driver):
    """
    Debug function to see what elements are scrollable on the page.
    """
    print("\n🔍 DEBUG - Checking scrollable elements:")

    script = """
    var elements = document.querySelectorAll('ul, div[class*="list"], div[class*="scaffold"]');
    var info = [];
    elements.forEach(function(el) {
        if (el.scrollHeight > el.clientHeight) {
            info.push({
                tag: el.tagName,
                classes: el.className.substring(0, 50),
                scrollHeight: el.scrollHeight,
                clientHeight: el.clientHeight,
                scrollTop: el.scrollTop
            });
        }
    });
    return info;
    """

    try:
        scrollable = driver.execute_script(script)
        print(f"   Found {len(scrollable)} scrollable elements:")
        for i, el in enumerate(scrollable[:5]):  # Show first 5
            print(f"   [{i + 1}] {el['tag']}.{el['classes'][:30]}...")
            print(f"       ScrollHeight: {el['scrollHeight']}, ClientHeight: {el['clientHeight']}")
    except Exception as e:
        print(f"   ❌ Debug error: {e}")

    # Check job count
    job_count = len(driver.find_elements(By.CSS_SELECTOR, "[data-job-id]"))
    print(f"   Current job cards visible: {job_count}\n")


def scroll_and_load_all_jobs(driver, max_jobs=30, max_attempts=12):
    """
    Aggressively scroll the job list to load as many jobs as possible BEFORE processing any.

    Args:
        max_jobs: Stop when this many jobs are loaded (default: 30)
        max_attempts: Stop after this many failed scroll attempts (default: 12)

    Returns:
        Number of job cards loaded
    """
    print(f"\n🔄 Starting aggressive scroll to load up to {max_jobs} job cards...")
    print(f"   Will stop after {max_attempts} consecutive scrolls with no new jobs\n")

    consecutive_no_change = 0
    scroll_count = 0

    # Wait for initial jobs to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-job-id]"))
        )
        time.sleep(2)
    except:
        print("   ⚠️  Initial job load timeout")

    # Run debug to understand page structure
    debug_scroll_state(driver)

    while consecutive_no_change < max_attempts:
        # Count current jobs
        job_cards_before = driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
        count_before = len(job_cards_before)

        scroll_success = False

        # Strategy 1: Find and scroll the UL container (most reliable for LinkedIn)
        try:
            # Target the actual job list container
            ul_selectors = [
                "ul.scaffold-layout__list-container",
                "ul[class*='jobs-search-results']",
                "ul.jobs-search-results__list",
                "div.jobs-search-results-list"
            ]

            for selector in ul_selectors:
                containers = driver.find_elements(By.CSS_SELECTOR, selector)

                for container in containers:
                    try:
                        # Check if element is actually scrollable
                        scroll_height = driver.execute_script("return arguments[0].scrollHeight;", container)
                        client_height = driver.execute_script("return arguments[0].clientHeight;", container)

                        if scroll_height > client_height:
                            # Get current scroll position
                            current_scroll = driver.execute_script("return arguments[0].scrollTop;", container)

                            # Scroll down by a large amount (2000px)
                            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + 2000;", container)
                            time.sleep(1.5)

                            # Check if scroll actually happened
                            new_scroll = driver.execute_script("return arguments[0].scrollTop;", container)

                            if new_scroll > current_scroll:
                                scroll_success = True
                                scroll_count += 1
                                print(
                                    f"   Scroll #{scroll_count}: Scrolled {selector} by {new_scroll - current_scroll}px (total: {new_scroll}px)")
                                break
                    except Exception as e:
                        continue

                if scroll_success:
                    break

            if scroll_success:
                # Wait longer for LinkedIn to load new content
                time.sleep(3)

        except Exception as e:
            print(f"   ⚠️  Strategy 1 (UL scroll) failed: {e}")

        # Strategy 2: Scroll to last visible job card
        if not scroll_success and job_cards_before:
            try:
                # Get the last job card
                last_card = job_cards_before[-1]

                # Scroll the card into view
                driver.execute_script("""
                    arguments[0].scrollIntoView({behavior: 'auto', block: 'end'});
                """, last_card)

                scroll_success = True
                scroll_count += 1
                print(f"   Scroll #{scroll_count}: Scrolled to last job card (Strategy 2)")
                time.sleep(2.5)

            except Exception as e:
                print(f"   ⚠️  Strategy 2 (scroll to card) failed: {e}")

        # Strategy 3: Use JavaScript to scroll ANY scrollable container
        if not scroll_success:
            try:
                # Try to find ANY scrollable parent
                driver.execute_script("""
                    var scrolled = false;
                    var selectors = [
                        '.scaffold-layout__list',
                        '.jobs-search-results-list',
                        'ul.scaffold-layout__list-container',
                        '[role="main"]'
                    ];

                    for (var i = 0; i < selectors.length; i++) {
                        var elements = document.querySelectorAll(selectors[i]);
                        for (var j = 0; j < elements.length; j++) {
                            var elem = elements[j];
                            if (elem.scrollHeight > elem.clientHeight) {
                                elem.scrollTop += 2000;
                                scrolled = true;
                                break;
                            }
                        }
                        if (scrolled) break;
                    }
                    return scrolled;
                """)

                scroll_success = True
                scroll_count += 1
                print(f"   Scroll #{scroll_count}: JavaScript generic scroll (Strategy 3)")
                time.sleep(2.5)

            except Exception as e:
                print(f"   ⚠️  Strategy 3 (JS scroll) failed: {e}")

        # Strategy 4: Window scroll as last resort
        if not scroll_success:
            try:
                current_y = driver.execute_script("return window.pageYOffset;")
                driver.execute_script("window.scrollBy(0, 1500);")
                new_y = driver.execute_script("return window.pageYOffset;")

                if new_y > current_y:
                    scroll_count += 1
                    print(
                        f"   Scroll #{scroll_count}: Window scroll by {new_y - current_y}px (Strategy 4 - last resort)")
                    time.sleep(2)
                else:
                    print(f"   ⚠️  Window scroll didn't move")
            except Exception as e:
                print(f"   ⚠️  Strategy 4 (window scroll) failed: {e}")

        # Wait a bit more for content to load
        time.sleep(2)

        # Count jobs after scroll
        job_cards_after = driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
        count_after = len(job_cards_after)

        # Check if we loaded new jobs
        new_jobs = count_after - count_before

        if new_jobs > 0:
            print(f"   ✓ Loaded {new_jobs} new job cards! Total: {count_after}")
            consecutive_no_change = 0
        else:
            consecutive_no_change += 1
            print(f"   ⚠️  No new jobs loaded (attempt {consecutive_no_change}/{max_attempts}). Total: {count_after}")

        # Check if we've reached our target
        if count_after >= max_jobs:
            print(f"\n   🎯 Target reached! Loaded {count_after} job cards (target was {max_jobs})")
            break

        # If we're stuck, try debug again
        if consecutive_no_change == 3:
            print("\n   🔍 Stuck loading jobs, running debug...")
            debug_scroll_state(driver)

    final_count = len(driver.find_elements(By.CSS_SELECTOR, "[data-job-id]"))

    if consecutive_no_change >= max_attempts:
        print(f"\n   ⛔ Stopped scrolling after {max_attempts} attempts with no new jobs")

    print(f"\n✅ Scrolling complete! Total job cards available: {final_count}\n")
    return final_count


def scroll_with_interaction(driver, max_jobs=30, max_attempts=12):
    """
    Alternative scrolling method that simulates more human-like behavior.
    Clicks on jobs to trigger LinkedIn's lazy loading mechanism.

    Args:
        max_jobs: Stop when this many jobs are loaded (default: 30)
        max_attempts: Stop after this many failed scroll attempts (default: 12)

    Returns:
        Number of job cards loaded
    """
    print(f"\n🔄 Starting INTERACTIVE scroll to load up to {max_jobs} job cards...")
    print(f"   This method clicks jobs to trigger loading\n")

    consecutive_no_change = 0
    scroll_count = 0

    # Wait for initial jobs
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-job-id]"))
        )
        time.sleep(2)
    except:
        print("   ⚠️  Initial job load timeout")

    while consecutive_no_change < max_attempts:
        job_cards_before = driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
        count_before = len(job_cards_before)

        if job_cards_before:
            try:
                # Click on the last visible job to trigger loading
                last_card = job_cards_before[-1]
                driver.execute_script("arguments[0].click();", last_card)
                time.sleep(1)

                # Then scroll the container
                driver.execute_script("""
                    var containers = document.querySelectorAll('ul.scaffold-layout__list-container, div.jobs-search-results-list');
                    for (var i = 0; i < containers.length; i++) {
                        if (containers[i].scrollHeight > containers[i].clientHeight) {
                            containers[i].scrollTop += 1500;
                            break;
                        }
                    }
                """)

                time.sleep(2.5)
                scroll_count += 1

            except Exception as e:
                print(f"   ⚠️  Interaction scroll error: {e}")

        # Check progress
        time.sleep(2)
        job_cards_after = driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
        count_after = len(job_cards_after)
        new_jobs = count_after - count_before

        if new_jobs > 0:
            print(f"   ✓ Scroll #{scroll_count}: Loaded {new_jobs} new jobs! Total: {count_after}")
            consecutive_no_change = 0
        else:
            consecutive_no_change += 1
            print(f"   ⚠️  No new jobs (attempt {consecutive_no_change}/{max_attempts})")

        if count_after >= max_jobs:
            print(f"\n   🎯 Target reached: {count_after} jobs")
            break

    final_count = len(driver.find_elements(By.CSS_SELECTOR, "[data-job-id]"))
    print(f"\n✅ Interactive scroll complete! Loaded {final_count} total job cards\n")
    return final_count


def search_jobs_for_company(driver, company, titles, keywords, max_results=30, use_ai_search=False, max_descriptions=10,
                            location="United States", use_interactive_scroll=False):
    """
    Search for jobs at a specific company and filter by titles

    Args:
        driver: Selenium WebDriver instance
        company: Company name to search for
        titles: List of job titles to filter by
        keywords: Additional keywords for search
        max_results: Maximum number of job cards to process (default: 30)
        use_ai_search: Use LinkedIn AI search mode (default: False)
        max_descriptions: Maximum number of job descriptions to extract (default: 10)
                         Set to None to extract all descriptions
        location: Location filter for job search (default: "United States")
        use_interactive_scroll: Use interactive scroll method instead of default (default: False)

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
    print(f"Scroll method: {'Interactive' if use_interactive_scroll else 'Standard'}")
    driver.get(search_url)

    # Wait for page to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-job-id]"))
        )
    except:
        print("Page load timeout, continuing anyway...")

    time.sleep(3)

    # STEP 1: SCROLL TO LOAD ALL JOBS FIRST (before processing any)
    if use_interactive_scroll:
        total_loaded = scroll_with_interaction(driver, max_jobs=max_results, max_attempts=12)
    else:
        total_loaded = scroll_and_load_all_jobs(driver, max_jobs=max_results, max_attempts=12)

    # STEP 2: NOW get all the job cards
    selectors = [
        "[data-job-id]",
        ".jobs-search-results__list-item",
        ".base-card",
        ".job-card-container",
        "li[data-occludable-job-id]",
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