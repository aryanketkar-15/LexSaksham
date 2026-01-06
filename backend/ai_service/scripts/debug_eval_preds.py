# backend/ai_service/scripts/debug_eval_preds.py
import numpy as np, json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
logits_path = ROOT / "results" / "logits.npy"
labels_path = ROOT / "results" / "labels.npy"
model_dir = ROOT / "models" / "legalbert_clause_classifier"

if not logits_path.exists() or not labels_path.exists():
    print("Missing logits.npy or labels.npy at backend/ai_service/results/")
    raise SystemExit(1)

logits = np.load(logits_path)
labels = np.load(labels_path)

print("Logits shape:", logits.shape)
print("Labels shape:", labels.shape)
preds = logits.argmax(axis=1)
print("Unique ground-truth labels:", sorted(list(set(labels.tolist())))[:20])
print("Unique predicted labels (top 20 counts):", Counter(preds.tolist()).most_common(20))
# show top 10 most-predicted indices and their counts
print("Most predicted indices:", Counter(preds.tolist()).most_common(10))

# Print mismatch examples (first 20)
mismatch_count = 0
for i in range(min(len(preds), 200)):
    if preds[i] != labels[i]:
        mismatch_count += 1
        if mismatch_count <= 20:
            print(f"idx {i}: true={int(labels[i])}, pred={int(preds[i])}")
print("Total mismatches in shown slice:", mismatch_count)

# Compare distribution
from collections import defaultdict
dist = defaultdict(int)
for l in labels:
    dist[int(l)] += 1
print("Ground-truth distribution (sample):", sorted(dist.items(), key=lambda x:-x[1])[:10])

# check label mapping file if present
label_map_file = model_dir / "label_classes.json"
if label_map_file.exists():
    labels_map = json.load(open(label_map_file, "r", encoding="utf8"))
    print("label_classes.json length:", len(labels_map))
else:
    print("label_classes.json not found in model dir.")
