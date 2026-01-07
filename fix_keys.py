import os
import json
from safetensors.torch import load_file, save_file

# PATHS
input_folder = r"C:\Users\conno\PycharmProjects\KF-DSPROJ-New\Fine-Tuning\Gemma3_Full_Fixed"
output_folder = r"C:\Users\conno\PycharmProjects\KF-DSPROJ-New\Fine-Tuning\Gemma3_Ready_For_GGUF"

os.makedirs(output_folder, exist_ok=True)

print(f"Reading from: {input_folder}")
print(f"Writing to:   {output_folder}")

# 1. FIX CONFIG
print("Fixing config.json...")
try:
    with open(os.path.join(input_folder, "config.json"), 'r') as f:
        config = json.load(f)

    # Force Gemma 2 Architecture
    config['architectures'] = ["Gemma2ForCausalLM"]
    config['model_type'] = "gemma2"

    # Save
    with open(os.path.join(output_folder, "config.json"), 'w') as f:
        json.dump(config, f, indent=2)
except Exception as e:
    print(f"Error processing config: {e}")

# 2. FIX INDEX FILE
print("Fixing model.safetensors.index.json...")
try:
    index_path = os.path.join(input_folder, "model.safetensors.index.json")
    with open(index_path, 'r') as f:
        index_data = json.load(f)

    new_weight_map = {}
    for key, filename in index_data['weight_map'].items():
        # --- FILTERS ---
        # 1. Remove Norm layers that Gemma 2 doesn't have
        if "k_norm" in key or "q_norm" in key:
            continue
        # 2. Remove Vision/Multimodal layers
        if "multi_modal_projector" in key or "vision_tower" in key:
            continue

        # --- RENAME ---
        new_key = key.replace("language_model.", "")
        new_weight_map[new_key] = filename

    index_data['weight_map'] = new_weight_map

    with open(os.path.join(output_folder, "model.safetensors.index.json"), 'w') as f:
        json.dump(index_data, f, indent=2)

    files_to_process = set(index_data['weight_map'].values())

except FileNotFoundError:
    print("No index file found, checking for single safetensors file...")
    files_to_process = ["model.safetensors"]

# 3. FIX WEIGHT FILES
for filename in files_to_process:
    src_file = os.path.join(input_folder, filename)
    dst_file = os.path.join(output_folder, filename)

    if os.path.exists(src_file):
        print(f"Processing weights: {filename} ...")

        state_dict = load_file(src_file)
        new_state_dict = {}

        for key, tensor in state_dict.items():
            # --- FILTERS ---
            if "k_norm" in key or "q_norm" in key:
                continue
            if "multi_modal_projector" in key or "vision_tower" in key:
                continue

            # --- RENAME ---
            new_key = key.replace("language_model.", "")
            new_state_dict[new_key] = tensor

        save_file(new_state_dict, dst_file, metadata={"format": "pt"})
    else:
        print(f"Warning: Could not find {src_file}")

# 4. COPY TOKENIZER FILES
import shutil

for file in ["tokenizer.model", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]:
    src = os.path.join(input_folder, file)
    if os.path.exists(src):
        shutil.copy(src, output_folder)

print("\nSUCCESS! created 'Gemma3_Ready_For_GGUF'.")