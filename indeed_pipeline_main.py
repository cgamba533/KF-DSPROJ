import os
import time
import datetime
import pandas as pd
import ollama

# --- IMPORT YOUR UTILS ---
# Ensure 'utils_indeed' folder exists with __init__.py inside
from utils_indeed.indeed_driver import init_driver
from utils_indeed.scrape_indeed_jobs import search_jobs_for_company

# ==============================================================================
# CONFIGURATION
# ==============================================================================

COMPANIES = [
    "Royal Bank of Canada", "TCW", "Lincoln Financial", "Natixis",
    "AssetMark", "Aristotle Capital Management", "Pathstone", "Fidelity",
    "Orion", "NEPC", "Invesco", "Janney Montgomery Scott LLC",
    "Northern Trust", "SEI", "Macquarie Asset Management", "BNY Mellon",
    "AllianceBernstein", "Russell Investments"
]

TITLES = [
    "head of distribution", "head of", "regional director", "national accounts",
    "national account manager", "chief marketing officer", "vice president",
    "executive", "chief of", "cmo", "chief", "director", ""
]

KEYWORDS = [
    "head of distribution OR regional director OR national accounts OR "
    "chief marketing officer OR vice president OR executive OR director OR "
    "managing director OR asset management"
]

EXCLUDE_KEYWORDS = ["intern", "internship"]

MODEL_NAME = "gemma3-4b-finetune"  # gemma3-4b-finetune or baseModel_gemma (12b param)

def get_unique_filename(base_path="data", prefix="indeed_jobs"):
    """Generates a unique filename with a timestamp."""
    os.makedirs(base_path, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    extension = ".csv"

    counter = 0
    while True:
        suffix = "" if counter == 0 else f"_{counter}"
        filename = os.path.join(base_path, f"{prefix}_{today}{suffix}{extension}")

        if not os.path.exists(filename):
            return filename
        counter += 1


def save_batch_to_csv(jobs_list, filename):

    if not jobs_list:
        return

    df = pd.DataFrame(jobs_list)
    file_exists = os.path.isfile(filename)

    try:
        df.to_csv(filename, mode='a', header=not file_exists, index=False)
        print(f"   💾 Saved batch of {len(jobs_list)} jobs to {filename}")
    except PermissionError:
        print(f"   ❌ CRITICAL: Could not save to {filename} (Permission Denied).")


# ==============================================================================
# PHASE 1: SCRAPING
# ==============================================================================

def run_scraping_phase():
    """Runs the Indeed scraper and returns the path of the saved CSV."""
    print("\n" + "=" * 60)
    print("PHASE 1: INITIATING JOB SCRAPER")
    print("=" * 60)

    driver = init_driver(headless=False)
    csv_filename = get_unique_filename()
    print(f"📁 Target File: {csv_filename}")

    total_jobs_found = 0

    try:
        for company in COMPANIES:
            print(f"\n--- Scraping: {company} ---")

            jobs = search_jobs_for_company(
                driver,
                company,
                TITLES,
                KEYWORDS,
                EXCLUDE_KEYWORDS,
                max_results=20,
                max_descriptions=20
            )

            if jobs:
                save_batch_to_csv(jobs, csv_filename)
                total_jobs_found += len(jobs)

            time.sleep(3)  # Polite delay between companies

    except Exception as e:
        print(f"\n⚠️  Scraping interrupted: {e}")
    finally:
        print("\nClosing browser...")
        driver.quit()

    print(f"\n✅ SCRAPE COMPLETE. Collected {total_jobs_found} jobs.")
    return csv_filename


# ==============================================================================
# PHASE 2: CLASSIFICATION
# ==============================================================================

def classify_job_row(client, row):
    """Sends a single job row to Ollama for classification."""
    # Construct the prompt
    prompt = (
        f"Job Title: {row['Job Title']}\n"
        f"Company: {row['Company']}\n"
        f"Location: {row['Location']}\n"
        f"Description: {row['Description']}\n"
        f"Does this job fit my criteria? Answer with 1 for yes, 0 for no."
    )

    try:
        # Call the model
        response = client.generate(model=MODEL_NAME, prompt=prompt)
        return response["response"].strip()
    except Exception as e:
        print(f"   ⚠️ Model error on job '{row.get('Job Title', 'Unknown')}': {e}")
        return "Error"


def run_classification_phase(input_csv_path):
    """Loads the scraped CSV and runs the LLM classifier."""
    print("\n" + "=" * 60)
    print("PHASE 2: INITIATING AI CLASSIFICATION")
    print("=" * 60)

    if not os.path.exists(input_csv_path):
        print("❌ Error: Scraped file not found. Skipping classification.")
        return

    # Check if file has data
    try:
        df = pd.read_csv(input_csv_path)
        if df.empty:
            print("⚠️ Scraped CSV is empty. Nothing to classify.")
            return
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    print(f"🧠 Loading model: {MODEL_NAME}")
    print(f"📄 Processing {len(df)} jobs from: {input_csv_path}")

    # Initialize Ollama Client
    try:
        client = ollama.Client()
        # Quick health check (optional)
        # client.list()
    except Exception as e:
        print(f"❌ Could not connect to Ollama. Is it running? Error: {e}")
        return

    # Run Inference
    print("🚀 Starting classification... (This may take time depending on your GPU)")

    # Using progress bar if available, otherwise simple loop
    from tqdm import tqdm
    tqdm.pandas(desc="Classifying")

    # Run the classification
    try:
        # If tqdm is installed, this shows a nice progress bar
        df["Predicted"] = df.progress_apply(lambda row: classify_job_row(client, row), axis=1)
    except ImportError:
        # Fallback if tqdm not installed
        df["Predicted"] = df.apply(lambda row: classify_job_row(client, row), axis=1)

    print("\n🧹 Filtering for relevant jobs (Classified as '1')...")

    total_jobs = len(df)

    # We use .astype(str) and .contains('1') to be robust against "1", "1 ", "1\n", etc.
    df_filtered = df[df['Predicted'].astype(str).str.contains('1', na=False)].copy()

    kept_jobs = len(df_filtered)
    dropped_jobs = total_jobs - kept_jobs

    # Save Results
    # We create a new filename for the classified version
    base, ext = os.path.splitext(input_csv_path)
    output_filename = f"{base}_CLASSIFIED{ext}"

    df_filtered.to_csv(output_filename, index=False)

    print(f"\n✅ CLASSIFICATION COMPLETE")
    print(f"📉 Dropped {dropped_jobs} irrelevant jobs (labeled '0').")
    print(f"💾 Saved {kept_jobs} relevant jobs to: {output_filename}")

    # Print a quick preview of "Yes" (1) results
    yes_jobs = df[df['Predicted'].astype(str).str.contains('1', na=False)]
    print(f"\n🔍 Found {len(yes_jobs)} potential matches:")
    if not yes_jobs.empty:
        print(yes_jobs[['Job Title', 'Company', 'Predicted']].head().to_string())

    return output_filename


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # 1. Run the Scraper (Generates the RAW file)
    raw_file_path = run_scraping_phase()

    classified_file_path = None

    # 2. Run the Classifier (Generates the CLASSIFIED file)
    if raw_file_path and os.path.exists(raw_file_path):
        classified_file_path = run_classification_phase(raw_file_path)
    else:
        print("❌ Pipeline stopped after Phase 1 (No data generated).")

    # 3. Final Summary Report
    print("\n" + "=" * 60)
    print("🏁 PIPELINE EXECUTION SUMMARY")
    print("=" * 60)

    print("1️⃣  RAW SCRAPED DATA (Original):")
    print(f"    -> {raw_file_path}")

    if classified_file_path:
        print("\n2️⃣  AI CLASSIFIED DATA (With predictions):")
        print(f"    -> {classified_file_path}")
    else:
        print("\n2️⃣  AI CLASSIFIED DATA:")
        print("    -> (Skipped or Failed)")

    print("=" * 60)