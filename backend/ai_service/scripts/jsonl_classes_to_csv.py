# jsonl_classes_to_csv.py
import json, csv
from pathlib import Path

IN_DIR = Path("backend/ai_service/datasets/relabel_by_class")
OUT_DIR = IN_DIR
for p in sorted(IN_DIR.glob("*.jsonl")):
    out = p.with_suffix(".csv")
    with open(p, encoding="utf8") as fi, open(out, "w", newline='', encoding="utf8") as fo:
        writer = csv.writer(fo)
        writer.writerow(["example_id","orig_index","text","original_label","new_label","note"])
        for i, line in enumerate(fi):
            obj = json.loads(line)
            text = obj.get("text") or obj.get("clause_text") or obj.get("clause") or ""
            orig = obj.get("label", obj.get("labels",""))
            writer.writerow([i, obj.get("_orig_index", ""), text.replace("\n"," "), orig, "", ""])
    print("Wrote", out)
