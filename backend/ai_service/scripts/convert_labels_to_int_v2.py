# backend/ai_service/scripts/convert_labels_to_int_v2.py
import json
from pathlib import Path
from difflib import get_close_matches

MAP_FILE = Path("backend/ai_service/datasets/normalized_label_map.json")
assert MAP_FILE.exists(), "Normalized map missing. Run create_normalized_label_map_v2.py first."

LABEL_MAP = json.load(open(MAP_FILE, "r"))

# convert string keys in LABEL_MAP if read as strings
# LABEL_MAP maps label_string -> numeric id (some entries may be None if unresolved)
# Build reverse: normalized_key -> id (already the values)
# We'll also allow fuzzy match against LABEL_MAP keys.
all_keys = list(LABEL_MAP.keys())

files = {
    "train": Path("backend/ai_service/datasets/clause_dataset/prepared/train.jsonl"),
    "validation": Path("backend/ai_service/datasets/clause_dataset/prepared/validation.jsonl")
}

unknowns = set()
for split, path in files.items():
    out_path = path.with_name(path.stem + "_int.jsonl")
    print(f"Converting {path} -> {out_path}")
    out_lines = 0
    with open(path, "r", encoding="utf-8") as fin, open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            obj = json.loads(line)
            raw_lbl = str(obj.get("label", "")).lower().strip()
            if raw_lbl == "":
                unknowns.add(("empty", split))
                continue

            # direct match
            if raw_lbl in LABEL_MAP and LABEL_MAP[raw_lbl] is not None:
                obj["label"] = LABEL_MAP[raw_lbl]
                fout.write(json.dumps(obj) + "\n")
                out_lines += 1
                continue

            # sometimes labels contain spaces or slashes
            candidate = raw_lbl.replace(" ", "_").replace("-", "_").replace("/", "_")
            if candidate in LABEL_MAP and LABEL_MAP[candidate] is not None:
                obj["label"] = LABEL_MAP[candidate]
                fout.write(json.dumps(obj) + "\n")
                out_lines += 1
                continue

            # fuzzy match to suggest best key
            matches = get_close_matches(raw_lbl, all_keys, n=1, cutoff=0.7)
            if matches:
                matched = matches[0]
                if LABEL_MAP.get(matched) is not None:
                    obj["label"] = LABEL_MAP[matched]
                    fout.write(json.dumps(obj) + "\n")
                    out_lines += 1
                    continue

            # last resort: try splitting on nonalpha and check parts
            parts = [p for p in raw_lbl.replace("/", " ").replace("-", " ").split() if p]
            mapped = False
            for p in parts:
                if p in LABEL_MAP and LABEL_MAP[p] is not None:
                    obj["label"] = LABEL_MAP[p]
                    fout.write(json.dumps(obj) + "\n")
                    out_lines += 1
                    mapped = True
                    break
            if mapped:
                continue

            # could not map
            unknowns.add((raw_lbl, split))

    print(f" -> wrote {out_lines} lines to {out_path}")

# write unknowns for manual inspection
unknown_file = Path("backend/ai_service/datasets/unmapped_labels.json")
json.dump(sorted(list(unknowns)), open(unknown_file, "w"), indent=2)
print("Done. Unmapped label examples saved to", unknown_file)
print("If unmapped list is non-empty, open that JSON and add aliases to normalized map, then re-run this script.")
