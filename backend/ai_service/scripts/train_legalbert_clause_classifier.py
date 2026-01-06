"""
train_legalbert_clause_classifier.py  (Phase D2)
-----------------------------------------------------
Fine-tune LegalBERT to classify clause_text by clause_type
Aligned with unified clause taxonomy and consistent label mapping.
-----------------------------------------------------
"""

import os, json, sys, datetime, re, torch
import transformers; print("Transformers version:", transformers.__version__)
from pathlib import Path
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np
import inspect


# ============================================================
# Paths & Configuration
# ============================================================
BASE_DIR = Path(__file__).resolve().parents[1] / "datasets" / "clause_dataset"
DATA_DIR = BASE_DIR / "prepared"
OUT_DIR  = Path(__file__).resolve().parents[2] / "models" / "legalbert_clause_classifier"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = DATA_DIR / "train.jsonl"
VAL_FILE   = DATA_DIR / "validation.jsonl"
UNIFIED_MAP = OUT_DIR / "unified_label_mapping.json"

MODEL_NAME     = "nlpaueb/legal-bert-base-uncased"
EPOCHS         = 4
LEARNING_RATE  = 2e-5
WEIGHT_DECAY   = 0.02
BATCH_SIZE     = 8 if torch.cuda.is_available() else 4

# ============================================================
# Logging
# ============================================================
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE  = OUT_DIR / f"training_log_{timestamp}.txt"

class Tee:
    def __init__(self, name):
        self.file = open(name, "w", encoding="utf-8")
        self.stdout = sys.stdout
    def write(self, data):
        self.file.write(data); self.stdout.write(data)
    def flush(self):
        self.file.flush(); self.stdout.flush()

sys.stdout = Tee(LOG_FILE)
print(f"Training Log started: {LOG_FILE}")
print("="*70)

# ============================================================
# Load Dataset
# ============================================================
data_files = {"train": str(TRAIN_FILE), "validation": str(VAL_FILE)}
dataset = load_dataset("json", data_files=data_files)
print(f"Loaded train/validation from {DATA_DIR}")

# ============================================================
# Normalize Text
# ============================================================
def normalize_text(t):
    if not t: return ""
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\x00-\x7F]+", " ", t)
    return t.strip().lower()

dataset = dataset.map(lambda x: {"text": normalize_text(x["text"])})
print("Text normalized.")

# ============================================================
# Encode Labels (Unified Mapping)
# ============================================================
if UNIFIED_MAP.exists():
    with open(UNIFIED_MAP, "r", encoding="utf-8") as f:
        unified_map = json.load(f)
    id2label = {int(k): v for k, v in unified_map.items()}
    label2id = {v: int(k) for k, v in unified_map.items()}
    print(f"Using unified label mapping ({len(label2id)} labels).")
else:
    # fallback: infer from dataset
    labels = sorted(set(dataset["train"]["label"]))
    label_encoder = LabelEncoder()
    label_encoder.fit(labels)
    label2id = {label: int(idx) for idx, label in enumerate(label_encoder.classes_)}
    id2label = {v: k for k, v in label2id.items()}
    print(f"Generated fallback label map ({len(label2id)} labels).")

# persist mapping files
with open(OUT_DIR / "label_map.json", "w", encoding="utf-8") as f:
    json.dump(label2id, f, indent=2, ensure_ascii=False)
with open(OUT_DIR / "label_classes.json", "w", encoding="utf-8") as f:
    json.dump(id2label, f, indent=2, ensure_ascii=False)

def encode_labels(example):
    example["labels"] = label2id.get(example["label"], -1)
    return example

dataset = dataset.map(encode_labels)
print("Labels encoded.")

# ============================================================
# Tokenization
# ============================================================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=256)

tokenized = dataset.map(tokenize, batched=True)
tokenized.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
print("Tokenization complete.")

# ============================================================
# Model Setup
# ============================================================
print("Loading LegalBERT base model...")
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=len(label2id), id2label=id2label, label2id=label2id
)
print("Model initialized.")

# ============================================================
# Training Arguments (Robust Version)
# ============================================================
print("\nChecking TrainingArguments signature...")
sig = inspect.signature(TrainingArguments.__init__)
params = list(sig.parameters.keys())
print(f"Available parameters: {params[:15]}...")

# Build args dictionary dynamically
training_args_dict = {
    "output_dir": str(OUT_DIR),
    "learning_rate": LEARNING_RATE,
    "per_device_train_batch_size": BATCH_SIZE,
    "per_device_eval_batch_size": BATCH_SIZE,
    "num_train_epochs": EPOCHS,
    "weight_decay": WEIGHT_DECAY,
    "save_total_limit": 2,
    "load_best_model_at_end": True,
    "logging_dir": str(OUT_DIR / "logs"),
    "logging_steps": 200,
    "fp16": torch.cuda.is_available(),
}

# Add evaluation strategy with version compatibility
if "evaluation_strategy" in params:
    training_args_dict["evaluation_strategy"] = "epoch"
    training_args_dict["save_strategy"] = "epoch"
    print("Using 'evaluation_strategy'")
elif "eval_strategy" in params:
    training_args_dict["eval_strategy"] = "epoch"
    training_args_dict["save_strategy"] = "epoch"
    print("Using 'eval_strategy' (newer API)")
else:
    print("WARNING: No evaluation parameter found - will skip evaluation during training")

try:
    training_args = TrainingArguments(**training_args_dict)
    print("TrainingArguments initialized successfully.\n")
except TypeError as e:
    print(f"ERROR: Error creating TrainingArguments: {e}")
    print("Falling back to minimal configuration...\n")
    training_args = TrainingArguments(
        output_dir=str(OUT_DIR),
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        num_train_epochs=EPOCHS,
        logging_dir=str(OUT_DIR / "logs"),
    )

# ============================================================
# Compute Metrics
# ============================================================
def compute_metrics(pred):
    labels = pred.label_ids
    preds = np.argmax(pred.predictions, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="weighted", zero_division=0
    )
    acc = accuracy_score(labels, preds)
    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

# ============================================================
# Trainer
# ============================================================
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

print(f"Training started (epochs={EPOCHS}, batch={BATCH_SIZE})...")
print("="*70)
trainer.train()

# ============================================================
# Save Model & Evaluate
# ============================================================
print("\n" + "="*70)
print("Saving model & tokenizer...")
trainer.save_model(str(OUT_DIR))
tokenizer.save_pretrained(str(OUT_DIR))

print("Evaluating model...")
metrics = trainer.evaluate()
print(f"\nEvaluation metrics:")
for key, value in metrics.items():
    print(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")

with open(OUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print(f"\nSUCCESS: Model saved to {OUT_DIR}")
print(f"Label map saved ({len(label2id)} classes)")
print(f"Training log: {LOG_FILE}")
print("="*70)