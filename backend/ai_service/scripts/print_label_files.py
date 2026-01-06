# backend/ai_service/scripts/print_label_files.py
import json
from pathlib import Path
MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "legalbert_clause_classifier"

for fname in ["label_classes.json", "label_map.json", "unified_label_mapping.json"]:
    p = MODEL_DIR / fname
    print("\nFILE:", p)
    if p.exists():
        try:
            print(json.dumps(json.load(open(p, "r", encoding="utf8")), indent=2)[:2000])
        except Exception as e:
            print("Failed to read JSON:", e)
    else:
        print("Not present.")
