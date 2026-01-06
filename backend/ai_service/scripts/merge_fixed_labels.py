"""
merge_fixed_labels.py

Purpose:
- Read relabeled CSV (relabel_fixed.csv) created after you relabeled
  backend/ai_service/datasets/relabel_candidates_for_relabeling.csv
- Match candidate clauses back into original test.jsonl by text + original_label (first unmatched occurrence)
- Replace label with new_label (if new_label != -1)
- Write new test file: backend/ai_service/datasets/test_fixed.jsonl
- Produce a small report of how many replacements made and remaining unmatched rows.
"""
import csv, json
from pathlib import Path
from collections import defaultdict

ROOT = Path("backend/ai_service")
CAND_IN = ROOT / "datasets" / "relabel_candidates.jsonl"
CSV_IN = ROOT / "datasets" / "relabel_fixed.csv"   # upload this (or relabeled CSV)
TEST_IN = ROOT / "datasets" / "test.jsonl"
TEST_OUT = ROOT / "datasets" / "test_fixed.jsonl"
REPORT_OUT = ROOT / "datasets" / "merge_report.json"

# Load the relabeled CSV
if not CSV_IN.exists():
    raise FileNotFoundError(f"Relabeled CSV not found: {CSV_IN}. Make sure you exported relabel_fixed.csv")

# Build list of candidate objects (order matches relabel_candidates.jsonl)
candidates = [json.loads(line) for line in open(CAND_IN, encoding="utf8")]

# Load csv mapping of example_id -> new_label
mapping = {}
with open(CSV_IN, encoding="utf8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            idx = int(row["example_id"])
        except:
            continue
        new_label = row.get("new_label", "").strip()
        if new_label == "":
            continue
        # keep numeric label; allow -1 for skip
        try:
            new_label_i = int(new_label)
        except:
            new_label_i = None
        mapping[idx] = new_label_i

print(f"Loaded {len(mapping)} relabeled rows from {CSV_IN}")

# Build a lookup: (text, original_label) -> list of candidate indices
lookup = defaultdict(list)
for i, cand in enumerate(candidates):
    text = (cand.get("text") or cand.get("clause_text") or cand.get("clause") or "").strip()
    orig_label = cand.get("label", cand.get("labels", cand.get("original_label", None)))
    # normalize orig_label to int if possible
    if isinstance(orig_label, str) and orig_label.isdigit():
        orig_label = int(orig_label)
    lookup[(text, str(orig_label))].append(i)

# Track used candidate indices so duplicates match to next occurrence
used_candidate_idx = set()

# Now read original test and apply replacements
total = 0
replaced = 0
unmatched = []

out_lines = []
for i, line in enumerate(open(TEST_IN, encoding="utf8")):
    obj = json.loads(line)
    total += 1
    text = (obj.get("text") or obj.get("clause_text") or obj.get("clause") or "").strip()
    label = obj.get("label", obj.get("labels", obj.get("original_label", None)))
    key = (text, str(label))
    if key in lookup and lookup[key]:
        # iterate through candidate indices to find first that has relabel mapping
        found = False
        for cand_idx in lookup[key]:
            if cand_idx in used_candidate_idx:
                continue
            # if this candidate was relabeled
            if cand_idx in mapping:
                new_label = mapping[cand_idx]
                used_candidate_idx.add(cand_idx)
                # apply new label if not -1
                if new_label is not None and new_label != -1:
                    obj["label"] = new_label
                    obj["labels"] = new_label
                    replaced += 1
                found = True
                break
        if not found:
            # no mapping for available candidate idxs, leave unchanged
            out_lines.append(obj)
            continue
    out_lines.append(obj)

# Write out
with open(TEST_OUT, "w", encoding="utf8") as f:
    for o in out_lines:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")

# Report
report = {
    "input_test_count": total,
    "replaced_labels": replaced,
    "mapped_candidates_total": len(mapping),
    "used_candidates": len(used_candidate_idx)
}
open(REPORT_OUT, "w", encoding="utf8").write(json.dumps(report, indent=2))
print("Merge complete:", report)
print("Wrote new test file to:", TEST_OUT)
print("Report saved to:", REPORT_OUT)
