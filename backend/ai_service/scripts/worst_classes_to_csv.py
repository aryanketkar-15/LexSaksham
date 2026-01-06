# save as backend/ai_service/scripts/worst_classes_to_csv.py
import json, csv, sys
from pathlib import Path
metrics_file = Path("backend/ai_service/results/classifier_metrics_from_outputs.json")
test_file = Path("backend/ai_service/datasets/test_fixed.jsonl")
out_dir = Path("backend/ai_service/datasets/worst_by_class")
out_dir.mkdir(parents=True, exist_ok=True)

m = json.load(open(metrics_file))
# pick classes with lowest f1 (exclude 'micro'/'macro' rows)
pairs = [(k, v.get("f1-score", 0)) for k,v in m.items() if isinstance(v, dict) and "f1-score" in v]
pairs = sorted(pairs, key=lambda x: x[1])
k = 8
bottom = [int(x[0]) for x in pairs[:k]]
print("Bottom classes:", bottom)

# load test lines
lines = [json.loads(l) for l in open(test_file, "r", encoding="utf-8")]
# create CSV per class
for cls in bottom:
    fname = out_dir / f"candidates_class_{cls}.csv"
    with open(fname, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["example_id","orig_index","text","original_label","new_label","note"])
        cnt = 0
        for i, obj in enumerate(lines):
            if obj.get("label") == cls:
                writer.writerow([cnt, i, obj.get("text","").replace("\n"," "), obj.get("label"), "", ""])
                cnt += 1
    print("Wrote", fname, "rows:", cnt)

print("Done. Edit CSVs and fill new_label column, then run merge_many_fixed_labels.py")
