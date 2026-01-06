# convert_labels_file.py
# Usage:
# python backend/ai_service/scripts/convert_labels_file.py \
#   --in backend/ai_service/datasets/clause_dataset/prepared/train_balanced.jsonl \
#   --out backend/ai_service/datasets/clause_dataset/prepared/train_balanced_int.jsonl \
#   --map backend/ai_service/datasets/normalized_label_map.json

import json
import argparse
from pathlib import Path

def load_map(map_path):
    m = json.load(open(map_path, "r", encoding="utf-8"))
    # map keys may be either normalized keys or aliases -> ints.
    # ensure keys are normalized (lower, underscore)
    norm = {}
    for k, v in m.items():
        norm_key = str(k).strip().lower()
        norm[norm_key] = v
    return norm

def normalize_label_key(s):
    if s is None:
        return s
    s2 = str(s).strip().lower()
    s2 = s2.replace(" ", "_")
    s2 = s2.replace("-", "_")
    s2 = s2.replace("/", "_")
    s2 = s2.replace(".", "")
    return s2

def safe_int(s):
    try:
        return int(s)
    except:
        return None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="infile", required=True)
    p.add_argument("--out", dest="outfile", required=True)
    p.add_argument("--map", dest="mapfile", required=True)
    args = p.parse_args()

    mapd = load_map(args.mapfile)

    inf = Path(args.infile)
    outf = Path(args.outfile)
    assert inf.exists(), f"infile not found: {inf}"
    count = 0
    unmapped = {}
    with open(inf, "r", encoding="utf-8") as fin, open(outf, "w", encoding="utf-8") as fo:
        for line in fin:
            if not line.strip():
                continue
            obj = json.loads(line)
            lab = obj.get("label")
            # if already int (or string of digits), keep int
            lab_int = safe_int(lab)
            if lab_int is None:
                k = normalize_label_key(lab)
                mapped = mapd.get(k)
                if mapped is None:
                    # try direct lookup without normalization
                    mapped = mapd.get(str(lab).strip().lower())
                if mapped is None:
                    unmapped[k] = unmapped.get(k, 0) + 1
                    # fallback: if label is numeric string with stray chars, try to extract digits
                    digits = "".join(ch for ch in str(lab) if ch.isdigit())
                    if digits:
                        lab_int = int(digits)
                    else:
                        raise ValueError(f"Could not map label '{lab}'. Add alias to normalized map and re-run. Example unmapped: {k}")
                else:
                    lab_int = int(mapped)
            obj["label"] = lab_int
            fo.write(json.dumps(obj, ensure_ascii=False) + "\n")
            count += 1

    print(f"Wrote {count} lines to {outf}")
    if unmapped:
        print("Unmapped label examples (sample):")
        for k, v in list(unmapped.items())[:20]:
            print(k, v)
        # save unmapped for inspection
        open(Path(args.outfile).with_suffix(".unmapped.json"), "w", encoding="utf-8").write(json.dumps(unmapped, indent=2))

if __name__ == "__main__":
    main()
