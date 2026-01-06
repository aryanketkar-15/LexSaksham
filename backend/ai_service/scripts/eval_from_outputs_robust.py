# backend/ai_service/scripts/eval_from_outputs_robust.py
import numpy as np, json, argparse
from pathlib import Path
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# NEW: Add argument parsing to choose the folder
parser = argparse.ArgumentParser()
parser.add_argument("--dir", default="backend/ai_service/results", help="Directory containing logits.npy and labels.npy")
args = parser.parse_args()

resdir = Path(args.dir)
print(f"Reading metrics from: {resdir}")

logits_path = resdir/"logits.npy"
labels_path = resdir/"labels.npy"

if not logits_path.exists() or not labels_path.exists():
    raise SystemExit(f"Error: Could not find logits.npy or labels.npy in {resdir}")

logits = np.load(logits_path, allow_pickle=True)
labels = np.load(labels_path, allow_pickle=True)

print("Raw logits shape:", logits.shape, "raw labels shape:", labels.shape)

# Ensure labels are 1D ints. If labels are one-hot / multi-hot, convert via argmax
if labels.ndim > 1:
    if labels.shape[1] == logits.shape[1]:
        print("Detected labels as one-hot; converting to argmax.")
        labels = labels.argmax(axis=1)
    else:
        # try to flatten
        labels = labels.reshape(-1)
labels = labels.astype(int)

preds = logits.argmax(axis=1)

print("Preds / labels length:", len(preds), len(labels))
if len(preds) != len(labels):
    raise SystemExit("Length mismatch between preds and labels")

acc = accuracy_score(labels, preds)
print(f"Accuracy: {acc:.4f}")

report = classification_report(labels, preds, zero_division=0, output_dict=True)
with open(resdir/"classifier_metrics_from_outputs.json","w",encoding="utf8") as f:
    json.dump(report, f, indent=2)
print("Wrote classifier_metrics_from_outputs.json")

# Produce confusion matrix plot (optional)
cm = confusion_matrix(labels, preds)
plt.figure(figsize=(10,8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.tight_layout()
plt.savefig(resdir/"confusion_matrix.png")
print("Saved confusion_matrix.png")