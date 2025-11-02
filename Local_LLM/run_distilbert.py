from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import torch
import pandas as pd

model_path = "./distilbert_jobs_model"
tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
model = DistilBertForSequenceClassification.from_pretrained(model_path)

# Load your test CSV (with blank Good column)
test_path = "data/distilbert_test_data.csv"
df = pd.read_csv(test_path)

# Combine Job Title + Description
df["text"] = (df["Job Title"].fillna('') + " " +
              df["Job Title"].fillna('') + " " +
              df["Job Title"].fillna('') + " " +
              df["Job Title"].fillna('') + " " +
              df["Job Title"].fillna('') + " [SEP] " +
              df["Description"].fillna(''))

def predict(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        return probs[:, 1].tolist()  # Probability of being "Good" (1)

# Run predictions
df["prob_good"] = predict(df["text"].tolist())
df["predicted_good"] = (df["prob_good"] > 0.5).astype(int)

# Save with predictions
df.to_csv("data/jobs_test_predictions.csv", index=False)
print("✅ Predictions saved to data/jobs_test_predictions.csv")
