import ollama
import pandas as pd

# cd .\Local_LLM then verify with dir
# To run model enter in terminal: ollama create baseModel -f Modelfile
# \bye will exit chat with model
# ollama will present options

client = ollama.Client()

df = pd.read_csv("jobs_2025-10-17-test_void.csv")

def classify_job(row):
    prompt = (
        f"Job Title: {row['Job Title']}\n"
        f"Company: {row['Company']}\n"
        f"Location: {row['Location']}\n"
        f"Description: {row['Description']}\n"
        f"Does this job fit my criteria? Answer with 1 for yes, 0 for no."
    )
    response = client.generate(model="gemma3-4b-finetune", prompt=prompt)
    return response["response"].strip()

df["Predicted"] = df.apply(classify_job, axis=1)
df.to_csv("classified_jobs.csv", index=False)
print("✅ Saved classified jobs to classified_jobs.csv")
