import pandas as pd
import torch
from torch import nn
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer
import os

#  LOAD TRAIN AND TEST DATA
train_path = "/data/train_data.csv"
test_path = "/data/test_data.csv"

if not os.path.exists(train_path):
    raise FileNotFoundError("❌ train_data.csv not found at provided path.")
if not os.path.exists(test_path):
    raise FileNotFoundError("❌ test_data.csv not found at provided path.")

train_df = pd.read_csv(train_path)
test_df = pd.read_csv(test_path)

for df, name in [(train_df, "train"), (test_df, "test")]:
    if "Description" not in df.columns:
        raise KeyError(f"❌ {name}_data.csv must contain a 'Description' column.")
if "Good" not in test_df.columns:
    raise KeyError("❌ test_data.csv must contain a 'Good' column (1 = good, 0 = not good).")

# PREPARE TEXTS WITH TITLE REPEATED AND [SEP] TOKEN
SEP = " [SEP] "  # model-friendly separator
train_texts = ((train_df["Job Title"] + " ") * 5 + SEP + train_df["Description"]).astype(str).tolist()
test_texts = ((test_df["Job Title"] + " ") * 5 + SEP + test_df["Description"]).astype(str).tolist()
print(f"🧾 Loaded {len(train_texts)} train and {len(test_texts)} test job descriptions")

# ENCODE USING MiniLM

print("\n🔍 Generating embeddings with all-MiniLM-L6-v2...")
model = SentenceTransformer("all-MiniLM-L6-v2")
train_embeddings = model.encode(train_texts, batch_size=16, show_progress_bar=True)
test_embeddings = model.encode(test_texts, batch_size=16, show_progress_bar=True)

scaler = StandardScaler()
train_embeddings = scaler.fit_transform(train_embeddings)
test_embeddings = scaler.transform(test_embeddings)

# DEFINE AUTOENCODER
class Autoencoder(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32)
        )
        self.decoder = nn.Sequential(
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

autoencoder = Autoencoder(train_embeddings.shape[1])
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(autoencoder.parameters(), lr=0.001)

X_train = torch.tensor(train_embeddings, dtype=torch.float32)
X_test = torch.tensor(test_embeddings, dtype=torch.float32)

#  TRAIN AUTOENCODER

print("\n⚙️ Training autoencoder...")
epochs = 50
for epoch in range(epochs):
    optimizer.zero_grad()
    outputs = autoencoder(X_train)
    loss = criterion(outputs, X_train)
    loss.backward()
    optimizer.step()

    if (epoch + 1) % 10 == 0:
        print(f"Epoch [{epoch+1}/{epochs}] - Loss: {loss.item():.4f}")

print("\n✅ Training complete!")

# EVALUATE ON TEST DATA
autoencoder.eval()
with torch.no_grad():
    reconstructed = autoencoder(X_test)
    reconstruction_error = torch.mean((X_test - reconstructed) ** 2, dim=1).numpy()

test_df["Reconstruction_Error"] = reconstruction_error

# SORT SO THAT ALL GOOD==1 ARE AT THE TOP
test_df_sorted = test_df.sort_values(
    by=["Good", "Reconstruction_Error"],  # prioritize Good==1
    ascending=[False, True]              # 1s first, then lowest error
)

# SAVE RESULTS

os.makedirs("../data", exist_ok=True)
output_file = os.path.join("../data", "ranked_test_data.csv")
test_df_sorted.to_csv(output_file, index=False)

print(f"\n📊 Test data ranked and saved to: {output_file}")
print(test_df_sorted[["Job Title", "Company", "Good", "Reconstruction_Error"]].head(10))