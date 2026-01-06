import json
from pathlib import Path

MAP_FILE = "backend/ai_service/datasets/normalized_label_map.json"
LABEL_MAP = json.load(open(MAP_FILE))

files = {
    "train": "backend/ai_service/datasets/clause_dataset/prepared/train.jsonl",
    "validation": "backend/ai_service/datasets/clause_dataset/prepared/validation.jsonl"
}

for split, path in files.items():
    out_path = path.replace(".jsonl", "_int.jsonl")
    print(f"Converting {path} → {out_path}")

    out = open(out_path, "w", encoding="utf-8")
    for line in open(path, "r", encoding="utf-8"):
        obj = json.loads(line)
        lbl = obj["label"].lower().strip()
        if lbl not in LABEL_MAP:
            print("❌ Missing label in map:", lbl)
            continue
        obj["label"] = LABEL_MAP[lbl]
        out.write(json.dumps(obj) + "\n")
    out.close()

print("✔ Conversion complete.")
