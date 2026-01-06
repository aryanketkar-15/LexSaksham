import json
import csv
import glob
from pathlib import Path

BASE = Path("backend/ai_service/datasets")
TEST_IN = BASE / "test.jsonl"
TEST_OUT = BASE / "test_fixed.jsonl"
REPORT = BASE / "merge_many_report.json"
RELABEL_DIR = BASE / "relabel_by_class"

# Load test
data = [json.loads(l) for l in open(TEST_IN, "r", encoding="utf-8")]

# Build map from orig_index -> new_label
mapping = {}
csv_files = glob.glob(str(RELABEL_DIR / "*.csv"))

for f in csv_files:
    with open(f, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nl = row.get("new_label", "").strip()
            if not nl.isdigit():
                continue
            orig = row.get("orig_index", "").strip()
            if orig.isdigit():
                mapping[int(orig)] = int(nl)

replaced = 0

# apply mapping
for i, row in enumerate(data):
    idx = row.get("index", i)    # or "orig_index" depending on your dataset format
    if idx in mapping:
        row["label"] = mapping[idx]
        replaced += 1

with open(TEST_OUT, "w", encoding="utf-8") as out:
    for row in data:
        out.write(json.dumps(row) + "\n")

json.dump({
    "input_test_count": len(data),
    "mapped_total": len(mapping),
    "replaced_labels": replaced
}, open(REPORT, "w"), indent=2)

print("Merge complete:", replaced, "labels replaced")
print("Report saved:", REPORT)
print("New test:", TEST_OUT)
