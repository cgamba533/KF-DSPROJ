import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from huggingface_hub import login
import os

# 1. LOGIN
# (Your token is likely still cached, but keep this if needed)
login(token="insert-token")

# 2. CONFIGURATION
device = "cpu"
base_model_id = "google/gemma-3-4b-it"

# --- CHANGE IS HERE ---
# Use the short path to avoid Windows errors
adapter_path = r"C:\gemma_adapter"
# ----------------------

save_path = r"C:\Users\conno\PycharmProjects\KF-DSPROJ-New\Fine-Tuning\Gemma3_Full_Fixed"

print(f"Loading base model: {base_model_id}...")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype=torch.bfloat16,
    device_map=device,
    trust_remote_code=True
)

print(f"Loading adapter from: {adapter_path}...")
# Verify the file exists before crashing
if not os.path.exists(os.path.join(adapter_path, "adapter_model.safetensors")):
    print(f"ERROR: adapter_model.safetensors NOT FOUND in {adapter_path}")
    exit(1)

model = PeftModel.from_pretrained(base_model, adapter_path)

print("Merging adapter into base model...")
model = model.merge_and_unload()

print(f"Saving full model to: {save_path}...")
model.save_pretrained(save_path)

tokenizer = AutoTokenizer.from_pretrained(base_model_id)
tokenizer.save_pretrained(save_path)

print("SUCCESS! Model merged and saved.")