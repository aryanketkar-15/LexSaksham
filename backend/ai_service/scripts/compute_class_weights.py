import os
import json
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from pathlib import Path

# IMPORTANT: use the *integer-labeled* dataset
train_file = "backend/ai_service/datasets/clause_dataset/prepared/train_int.jsonl"

if not Path(train_file).exists():
    raise FileNotFoundError("❌ Could not find train_int.jsonl at: " + train_file)

print("✔ Using train file:", train_file)

# Load numeric labels
labels = []
with open(train_file, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        label = obj["label"]

        # ensure numeric
        if isinstance(label, str):
            raise ValueError(f"❌ Found string label in {train_file}. Something is wrong: {label}")

        labels.append(label)

labels = np.array(labels)
classes = np.unique(labels)

# Compute balanced weights
weights = compute_class_weight(
    class_weight="balanced",
    classes=classes,
    y=labels
)

# Convert to int->float mapping
weights_out = {int(c): float(w) for c, w in zip(classes, weights)}

# Save
out_file = "backend/ai_service/results/class_weights.json"
json.dump(weights_out, open(out_file, "w"), indent=2)

print("✔ Saved class weights to:", out_file)
print(weights_out)
