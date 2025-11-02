from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
import pandas as pd

# Load and prepare your labeled data
train_path = "data/distilbert_train_data.csv"
df = pd.read_csv(train_path)

# Drop rows with missing values in key columns
df = df.dropna(subset=["Description", "Good"])

# Convert 'Good' to integer labels (0 or 1)
df["Good"] = df["Good"].astype(int)

# Combine Job Title + Description for better context, give title weight
df["text"] = (df["Job Title"].fillna('') + " " +
              df["Job Title"].fillna('') + " " +
              df["Job Title"].fillna('') + " " +
              df["Job Title"].fillna('') + " " +
              df["Job Title"].fillna('') + " [SEP] " +
              df["Description"].fillna(''))

# Rename columns for Hugging Face format
df = df.rename(columns={"Good": "labels"})

# Convert to Hugging Face Dataset
dataset = Dataset.from_pandas(df)

# Load tokenizer
tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

def tokenize(batch):
    return tokenizer(batch["text"], padding="max_length", truncation=True)

dataset = dataset.map(tokenize, batched=True)
dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

# Load model
model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)

# Training setup
training_args = TrainingArguments(
    output_dir="./results",
    #do_eval=True,    #don't need eval
    num_train_epochs=10,
    per_device_train_batch_size=8,
    save_strategy="epoch",
    logging_dir="./logs",
    learning_rate=5e-6,
    weight_decay=0.01,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

trainer.train()

# Save trained model and tokenizer
model.save_pretrained("./distilbert_jobs_model")
tokenizer.save_pretrained("./distilbert_jobs_model")

print("✅ Model and tokenizer saved to ./distilbert_jobs_model")