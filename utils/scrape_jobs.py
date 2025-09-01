import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def search_jobs_for_company(driver, company, titles, keywords, max_results=30, use_ai_search=False):
    """
    Search for jobs at a specific company and filter by titles
    """
    search_query = f"{company} {' '.join(keywords)}"
    encoded_query = search_query.replace(' ', '%20')

    if use_ai_search:
        search_url = f"https://www.linkedin.com/jobs/search-results/?keywords={encoded_query}&origin=SEMANTIC_SEARCH_MODE_FROM_CLASSIC"
    else:
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}"

    print(f"Searching: {search_url}")
    print(f"Using {'AI' if use_ai_search else 'Regular'} search mode")
    driver.get(search_url)

    # Wait for page to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-job-id]"))
        )
    except:
        print("Page load timeout, continuing anyway...")

    time.sleep(3)

    # Try multiple selectors for job cards - different selectors for AI vs regular search
    job_cards = []
    if use_ai_search:
        # AI search might use different selectors
        selectors = [
            "[data-job-id]",
            ".jobs-search-results__list-item",
            ".job-card-list__item",
            ".artdeco-entity-lockup",
            "li[data-occludable-job-id]",
            ".jobs-search-results-list .jobs-search-results-list__item-wrapper"
        ]
    else:
        # Regular search selectors
        selectors = [
            "[data-job-id]",
            ".jobs-search-results__list-item",
            ".base-card",
            ".job-card-container",
            "li[data-occludable-job-id]"
        ]

    for selector in selectors:
        job_cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if job_cards:
            print(f"Found {len(job_cards)} job cards using selector: {selector}")
            break

    if not job_cards:
        print("No job cards found with any selector")
        # Debug: Let's see what the page actually contains
        print("Page title:", driver.title)
        print("Current URL:", driver.current_url)

        # Check if we hit a different page or need to handle a popup
        if "challenge" in driver.current_url or "login" in driver.current_url:
            print("❌ Appears we're not logged in properly or hit a challenge page")
            return []

        return []

    # Limit results
    job_cards = job_cards[:max_results]
    results = []

    for i, card in enumerate(job_cards):
        try:
            # Try multiple ways to get job title - updated selectors for 2025
            title_text = ""
            title_selectors = [
                "h3.base-search-card__title a span[aria-hidden='true']",  # Most common current format
                "h3 a span[title]",  # Alternative with title attribute
                ".base-search-card__title a",
                ".job-card-list__title a",
                "[data-job-id] h3 a",
                "h3 a span:first-child",
                ".jobs-unified-top-card__job-title",
                "a[data-tracking-control-name='public_jobs_jserp-result_search-card'] span[aria-hidden='true']"
            ]

            for j, title_sel in enumerate(title_selectors):
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, title_sel)
                    title_text = title_elem.text.strip()
                    if title_text:
                        print(f"   ✓ Found title using selector #{j + 1}: '{title_text}'")
                        break
                except Exception as e:
                    continue

            # If still no title, try parsing from the full card text
            if not title_text:
                try:
                    # Get all text from the job card and try to extract title
                    card_text = card.text.strip()
                    print(f"   Debug - Full card text for job {i + 1}:")
                    print(f"   {card_text[:200]}...")

                    # The title is usually the first line of text
                    lines = card_text.split('\n')
                    if lines:
                        # First line is usually the job title
                        potential_title = lines[0].strip()

                        # Remove common suffixes that LinkedIn adds
                        potential_title = potential_title.replace(" with verification", "")

                        # Make sure it's not empty and seems like a job title
                        if potential_title and len(potential_title) > 3:
                            title_text = potential_title
                            print(f"   ✓ Extracted title from card text: '{title_text}'")

                    # Backup: Try to get the title attribute from any link
                    if not title_text:
                        links = card.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            title_attr = link.get_attribute("title")
                            if title_attr and len(title_attr) > 5 and not title_attr.startswith("http"):
                                title_text = title_attr
                                print(f"   ✓ Found title from link title attribute: '{title_text}'")
                                break

                except Exception as e:
                    print(f"   Error getting card text: {e}")

            if not title_text:
                print(f"   ❌ Could not extract title for job {i + 1} with any method")
                continue

            # Convert to lowercase for comparison
            title_lower = title_text.lower()

            # Check if any of our target titles are in the job title
            # More robust matching - handle variations and word boundaries
            title_match = False
            matched_title = None

            for target_title in titles:
                target_lower = target_title.lower().strip()

                # Direct substring match (your original approach)
                if target_lower in title_lower:
                    title_match = True
                    matched_title = target_title
                    break

                # Also try word boundary matching for single words
                if len(target_lower.split()) == 1:
                    import re
                    pattern = r'\b' + re.escape(target_lower) + r'\b'
                    if re.search(pattern, title_lower):
                        title_match = True
                        matched_title = target_title
                        break

            if not title_match:
                print(f"Skipping job: '{title_text}' (no title match)")
                continue

            print(f"✓ Found matching job: '{title_text}' (matched: '{matched_title}')")

            # Extract other job details - FIXED parsing logic
            company_text = company  # Default to search company
            location_text = "N/A"
            posted_text = "N/A"
            job_url = "N/A"

            # Parse additional details from card text - FIXED parsing logic
            try:
                card_lines = [line.strip() for line in card.text.split('\n') if line.strip()]

                # Debug: show the card structure
                print(f"   Card structure for job {i + 1}:")
                for idx, line in enumerate(card_lines[:6]):  # Show first 6 lines
                    print(f"     Line {idx}: '{line}'")

                # LinkedIn card structure is typically:
                # Line 0: Job Title
                # Line 1: Job Title (repeated with verification badge)
                # Line 2: Company Name
                # Line 3: Location
                # Line 4: Posted date or salary info
                # Line 5+: Other info

                if len(card_lines) >= 3:
                    # Company is usually line 2 (after title and title repeat)
                    company_text = card_lines[2].replace(" with verification", "").strip()

                if len(card_lines) >= 4:
                    # Location is usually line 3
                    potential_location = card_lines[3].strip()
                    # Make sure it's not a date or salary
                    if not any(
                            word in potential_location.lower() for word in ['ago', 'month', 'week', 'day', '$', '/yr']):
                        location_text = potential_location

                if len(card_lines) >= 5:
                    # Posted date might be line 4 or 5
                    for line_idx in range(4, min(len(card_lines), 7)):
                        potential_date = card_lines[line_idx].strip()
                        if any(word in potential_date.lower() for word in ['ago', 'month', 'week', 'day', 'viewed']):
                            posted_text = potential_date
                            break

                print(f"   Extracted - Company: '{company_text}', Location: '{location_text}', Posted: '{posted_text}'")

            except Exception as e:
                print(f"   Error parsing card structure: {e}")

            # Try to get job URL
            link_selectors = [
                "a[href*='/jobs/view/']",
                ".base-card__full-link",
                "[data-job-id] a"
            ]

            for link_sel in link_selectors:
                try:
                    link_elem = card.find_element(By.CSS_SELECTOR, link_sel)
                    job_url = link_elem.get_attribute("href")
                    if job_url:
                        break
                except:
                    continue

            # Add the job to results
            job_data = {
                "Job Title": title_text,
                "Company": company_text,
                "Location": location_text,
                "Posted Date": posted_text,
                "Job URL": job_url,
                "Description": ""
            }

            results.append(job_data)
            print(f"Added job #{len(results)}: {title_text} at {company_text}")

        except Exception as e:
            print(f"Error processing job card {i + 1}: {e}")
            continue

    print(f"\n📊 SUMMARY for {company}:")
    print(f"   - Total job cards processed: {len(job_cards)}")
    print(f"   - Jobs matching title criteria: {len(results)}")
    print(f"   - Target titles: {titles}")

    return results