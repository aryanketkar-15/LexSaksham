# apply_relabels_to_train.py
import csv, json
from pathlib import Path

# paths (adjust if needed)
relabel_csv_dir = Path("backend/ai_service/datasets/relabel_by_class")
train_file = Path("backend/ai_service/datasets/clause_dataset/prepared/train.jsonl")
out_train = Path("backend/ai_service/datasets/clause_dataset/prepared/train_relabelled.jsonl")

# read all per-class CSVs
mapping = {}
for p in relabel_csv_dir.glob("*.csv"):
    with p.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            # expected columns: orig_index (or example_id), original_label, new_label
            key = row.get("orig_index") or row.get("example_id") or row.get("id")
            if not key:
                continue
            try:
                idx = int(key)
            except:
                idx = key
            new = row.get("new_label", "").strip()
            if new:
                mapping[str(idx)] = new

# apply mapping to train.jsonl by matching index or id
out_lines = []
with train_file.open(encoding="utf-8") as f:
    for i, line in enumerate(f):
        obj = json.loads(line)
        # try match by numeric index first, then by id
        key1 = str(i)
        key2 = str(obj.get("orig_index", obj.get("index", "")))
        key3 = str(obj.get("id",""))
        if key1 in mapping:
            obj["label"] = mapping[key1]
        elif key2 in mapping:
            obj["label"] = mapping[key2]
        elif key3 in mapping:
            obj["label"] = mapping[key3]
        out_lines.append(json.dumps(obj, ensure_ascii=False))

out_train.write_text("\n".join(out_lines), encoding="utf-8")
print("Wrote", out_train, "with", len(out_lines), "lines. Applied", sum(1 for k in mapping), "mappings.")
