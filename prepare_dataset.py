import pandas as pd
import json
import os

# --- CONFIGURATION ---
# Updated to look inside the 'data' folder
INPUT_CSV = os.path.join("data", "Train_Data_Consolidated_Broader_demo.csv")

# Let's save the JSON into the 'data' folder too, to keep things organized
OUTPUT_JSON = os.path.join("data", "asset_management_broad_demo.json")

LABEL_COLUMN = "Good"


def prepare_data():
    print(f"🔄 Reading from {INPUT_CSV}...")

    # Check if file exists
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Error: {INPUT_CSV} not found.")
        print(f"   Current working directory is: {os.getcwd()}")
        return

    # Read the CSV
    try:
        df = pd.read_csv(INPUT_CSV)
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    # Basic cleanup: Drop rows where the label or description is missing
    initial_count = len(df)
    df = df.dropna(subset=['Description', LABEL_COLUMN])
    print(f"   Dropped {initial_count - len(df)} rows with missing values.")

    alpaca_data = []

    # The instruction matches your system prompt intent
    instruction_text = (
        "You are an executive recruiting assistant. "
        "Analyze the job title, company, and description and determine if it is a medium to high-level leadership role in finance, especially communications"
        "heavy areas including Asset Management, Wealth Management and sales areas. Other finance roles should also be considered if they are higer level "
        "leadership roles. "
        "Answer with 1 for yes, 0 for no."
    )

    for index, row in df.iterrows():
        # 1. Construct the Input (Truncated to 2000 chars for training efficiency)
        input_text = (
            f"Job Title: {row['Job Title']}\n"
            f"Company: {row['Company']}\n"
            f"Location: {row['Location']}\n"
            f"Description: {str(row['Description'])[:2000]}\n"
            f"Does this job fit my criteria?"
        )

        # 2. Construct the Output
        try:
            # Ensure we get a clean integer 1 or 0, then convert to string
            label = int(row[LABEL_COLUMN])
            output_text = str(label)
        except ValueError:
            print(f"   ⚠️ Skipping row {index}: Label '{row[LABEL_COLUMN]}' is invalid.")
            continue

        # 3. Build the Alpaca Entry
        entry = {
            "instruction": instruction_text,
            "input": input_text,
            "output": output_text
        }
        alpaca_data.append(entry)

    # Save to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(alpaca_data, f, indent=4)

    print(f"✅ Success! Converted {len(alpaca_data)} rows.")
    print(f"   Saved to: {OUTPUT_JSON}")
    print(f"   REMINDER: You must now move this file to your LLaMA Factory 'data' folder")
    print(f"             and register it in 'dataset_info.json'.")


if __name__ == "__main__":
    prepare_data()