# generate_relabel_candidates_by_class.py
import json, numpy as np, argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path("backend/ai_service")
RESULTS_DIR = ROOT / "results"
DATA_PATH = ROOT / "datasets" / "test.jsonl"
OUT_DIR = ROOT / "datasets" / "relabel_by_class"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# load metrics to identify bad classes if not provided
metrics = json.load(open(RESULTS_DIR / "classifier_metrics_from_outputs.json", encoding="utf8"))
bad = [int(k) for k,v in metrics.items() if k.isdigit() and v.get("f1-score",1.0) < 0.20]

parser = argparse.ArgumentParser()
parser.add_argument("--classes", nargs="+", type=int, default=bad, help="classes to extract")
parser.add_argument("--per_class", type=int, default=200, help="examples per class")
parser.add_argument("--out_prefix", type=str, default="candidates", help="prefix")
args = parser.parse_args()

print("Target classes:", args.classes)
print("Reading test:", DATA_PATH)

lines = [json.loads(l) for l in open(DATA_PATH, encoding="utf8")]
labels = np.load(RESULTS_DIR / "labels.npy")

# collect by label
by_label = defaultdict(list)
for i, obj in enumerate(lines):
    lab = int(labels[i])
    by_label[lab].append((i, obj))

for cls in args.classes:
    arr = by_label.get(cls, [])
    if not arr:
        print(f"No examples found for class {cls}")
        continue
    take = arr[:args.per_class]
    out_path = OUT_DIR / f"{args.out_prefix}_class_{cls}.jsonl"
    with open(out_path, "w", encoding="utf8") as f:
        for idx, obj in take:
            # include original index for traceability
            obj["_orig_index"] = idx
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print("Wrote", len(take), "candidates to", out_path)
