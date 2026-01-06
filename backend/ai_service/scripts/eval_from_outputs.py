# backend/ai_service/scripts/eval_from_outputs.py
import numpy as np, json
from pathlib import Path
from sklearn.metrics import classification_report, accuracy_score

resdir = Path("backend/ai_service/results")
logits = np.load(resdir/"logits.npy")
labels = np.load(resdir/"labels.npy")
preds = logits.argmax(axis=1)

print("Accuracy:", accuracy_score(labels, preds))
print("Classification report:")
print(classification_report(labels, preds, zero_division=0))
# save a json
report = classification_report(labels, preds, zero_division=0, output_dict=True)
with open(resdir/"classifier_metrics_from_outputs.json","w",encoding="utf8") as f:
    json.dump(report,f,indent=2)
print("Wrote classifier_metrics_from_outputs.json")
