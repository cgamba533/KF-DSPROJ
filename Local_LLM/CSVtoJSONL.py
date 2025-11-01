import pandas as pd
import json

df = pd.read_csv("C:/Users/conno/gitHub/KF-Linkedln_Scrapper/data/jobs_train1.csv")

records = []
for _, row in df.iterrows():
    prompt = (
        f"Job title: {row['Job Title']}\n"
        f"Company: {row['Company']}\n"
        f"Location: {row['Location']}\n"
        f"Description: {row['Description']}\n"
        f"Does this job fit my criteria? Answer with 1 for yes, 0 for no."
    )
    completion = str(int(row["Good"]))  # make sure it's a string
    records.append({"prompt": prompt, "completion": completion})

with open("../data/training_data.jsonl", "w") as f:
    for record in records:
        f.write(json.dumps(record) + "\n")

print("Success: Saved training_data.jsonl")