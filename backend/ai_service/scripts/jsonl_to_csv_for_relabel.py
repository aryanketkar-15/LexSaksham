import json, csv
from pathlib import Path

IN = Path("backend/ai_service/datasets/relabel_candidates.jsonl")
OUT = Path("backend/ai_service/datasets/relabel_candidates_for_relabeling.csv")

with open(IN, "r", encoding="utf8") as f, open(OUT, "w", newline='', encoding="utf8") as o:
    writer = csv.writer(o)
    writer.writerow(["example_id", "text", "original_label", "new_label"])

    for i, line in enumerate(f):
        obj = json.loads(line)
        text = obj.get("text") or obj.get("clause_text") or obj.get("clause") or ""
        text = text.replace("\n", " ").strip()

        original_label = obj.get("label", obj.get("labels", ""))

        writer.writerow([i, text, original_label, ""])  # new_label empty for you to fill

print("CSV ready:", OUT)
