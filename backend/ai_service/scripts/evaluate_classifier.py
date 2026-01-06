"""
Evaluate LegalBERT Clause Classifier
------------------------------------
Loads the trained classifier and computes Accuracy, F1 (macro), and per-class metrics.
Saves results to backend/ai_service/results/classifier_metrics.json

Usage:
    python backend/ai_service/scripts/evaluate_classifier.py --data <path_to_jsonl> --out <output_path>

Expected dataset format (JSONL):
    {"text": "clause text", "label": "payment_terms"}  (dataset format with lowercase underscore labels)
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix
import numpy as np

from label_mapping import normalize_dataset_label


BASE_AI = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_AI / "models"
RESULTS_DIR = BASE_AI / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLAUSE_MODEL_DIR = MODELS_DIR / "legalbert_clause_classifier"
LABEL_MAP_PATH = CLAUSE_MODEL_DIR / "label_classes.json"


def load_dataset(path: Path) -> List[Dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "text" in obj and "label" in obj:
                    items.append(obj)
            except json.JSONDecodeError:
                continue
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default=str(Path(__file__).resolve().parents[3] / "datasets" / "clause_dataset" / "prepared" / "test.jsonl"),
                        help="Path to JSONL dataset with 'text' and 'label'")
    parser.add_argument("--out", type=str, default=str(RESULTS_DIR / "classifier_metrics.json"),
                        help="Output JSON file path")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Dataset not found at {data_path}")
        return

    dataset = load_dataset(data_path)
    if not dataset:
        print("No valid samples found in dataset.")
        return

    print(f"📊 Loaded {len(dataset)} samples from {data_path.name}")

    tokenizer = AutoTokenizer.from_pretrained(CLAUSE_MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(CLAUSE_MODEL_DIR)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    id2label = model.config.id2label
    label2id = {v: k for k, v in id2label.items()}
    # Load human-readable label mapping saved during training
    label_classes_path = CLAUSE_MODEL_DIR / "label_classes.json"
    if label_classes_path.exists():
        with open(label_classes_path, "r", encoding="utf-8") as f:
            # label_classes.json maps string indices to human label names
            label_classes = json.load(f)
    else:
        label_classes = {}

    true = []
    pred = []
    logits = []  # Ensure logits are collected during evaluation
    labels = []  # Ensure labels are collected during evaluation

    for i, item in enumerate(dataset):
        if (i + 1) % 100 == 0:
            print(f"  Processing {i + 1}/{len(dataset)}...")
        
        text = item["text"]
        y_true_raw = item["label"]
        
        # Normalize dataset label to model label format
        y_true = normalize_dataset_label(y_true_raw)
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=256)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            logits_batch = model(**inputs).logits
            probs = torch.nn.functional.softmax(logits_batch, dim=-1)
            y_pred_id = int(torch.argmax(probs, dim=-1).item())
        
        # Map predicted id to human-readable label if available
        y_pred = label_classes.get(str(y_pred_id), id2label.get(y_pred_id, str(y_pred_id)))

        true.append(y_true)
        pred.append(y_pred)

        # Collect logits and labels for calibration
        logits.append(logits_batch.cpu().numpy())
        labels.append(y_true)

    # After evaluation loop, save logits and labels
    np.save("../results/logits.npy", logits)
    np.save("../results/labels.npy", labels)
    print("Saved logits and labels for calibration.")

    # Compute metrics
    report = classification_report(true, pred, output_dict=True, zero_division=0)
    acc = accuracy_score(true, pred)
    f1 = f1_score(true, pred, average="macro", zero_division=0)
    cm = confusion_matrix(true, pred, labels=sorted(set(true + pred)))

    out = {
        "accuracy": float(acc),
        "f1_macro": float(f1),
        "f1_weighted": float(f1_score(true, pred, average="weighted", zero_division=0)),
        "classification_report": report,
        "count": len(dataset),
        "model": "legalbert_clause_classifier",
        "device": device,
        "test_file": str(data_path)
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"✅ Saved metrics to {out_path}")
    print(f"   Accuracy: {acc:.4f}")
    print(f"   F1 (macro): {f1:.4f}")


if __name__ == "__main__":
    main()