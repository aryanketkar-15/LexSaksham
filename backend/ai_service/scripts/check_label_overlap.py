import json
from pathlib import Path
import sys

# Ensure scripts dir is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from label_mapping import normalize_dataset_label

from transformers import AutoModelForSequenceClassification

BASE = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE / "models" / "legalbert_clause_classifier"
DATA_PATH = BASE / "datasets" / "clause_dataset" / "prepared" / "test.jsonl"

print(f"Model dir: {MODEL_DIR}")
print(f"Data path: {DATA_PATH}")

if not MODEL_DIR.exists():
    print("ERROR: Model dir not found")
    sys.exit(1)
if not DATA_PATH.exists():
    print("ERROR: Data file not found")
    sys.exit(1)

# Load model config only (avoid heavy weights if possible)
try:
    model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR), low_cpu_mem_usage=True)
    id2label = {int(k): v for k, v in model.config.id2label.items()}
    model_labels = set(id2label.values())
    print(f"Loaded model with {len(model_labels)} labels")
except Exception as e:
    print("Failed to load model:", e)
    sys.exit(1)

# Read dataset and normalize labels
dataset_labels = set()
raw_labels = set()
with open(DATA_PATH, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if not line.strip():
            continue
        obj = json.loads(line)
        lbl = obj.get("label")
        raw_labels.add(str(lbl))
        mapped = normalize_dataset_label(lbl)
        dataset_labels.add(mapped)

print(f"Unique raw labels in dataset: {len(raw_labels)}")
print(sorted(list(raw_labels))[:30])
print(f"Unique normalized labels: {len(dataset_labels)}")
print(sorted(list(dataset_labels))[:30])

# Overlap
overlap = dataset_labels & model_labels
missing = dataset_labels - model_labels
extra = model_labels - dataset_labels
print(f"Overlap count: {len(overlap)}")
print("Missing labels (in dataset but not in model):", sorted(list(missing)))
print("Extra model labels not present in dataset sample:", sorted(list(extra))[:20])

# Show a mapping example for missing labels
if missing:
    print("\nExample mappings for missing labels:")
    for m in missing:
        print(" -", m)

print("Done")
