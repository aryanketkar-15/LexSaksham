# generate_relabel_candidates.py (robust path resolution)
import json, numpy as np, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent   # .../backend/ai_service/scripts
# repo root should be 3 levels up from scripts: scripts -> ai_service -> backend -> repo_root
# but to be defensive, try several fallbacks
def find_repo_root(script_dir: Path):
    # preferred: 3 parents up
    try:
        cand = script_dir.parents[3]
        # sanity: repo root should contain "backend" folder
        if (cand / "backend").exists():
            return cand
    except Exception:
        pass
    # fallback: climb until we see backend/ai_service/results
    cur = script_dir
    for _ in range(6):
        if (cur / "backend" / "ai_service" / "results").exists():
            return cur
        cur = cur.parent
    # final fallback: two levels up (old behavior)
    return script_dir.parents[2]

PROJECT_ROOT = find_repo_root(SCRIPT_DIR)
AI_SERVICE = PROJECT_ROOT / "backend" / "ai_service"
RESULTS_DIR = AI_SERVICE / "results"
DATA_PATH = AI_SERVICE / "datasets" / "test.jsonl"
OUT_PATH = AI_SERVICE / "datasets" / "relabel_candidates.jsonl"

print("SCRIPT_DIR =", SCRIPT_DIR)
print("PROJECT_ROOT =", PROJECT_ROOT)
print("AI_SERVICE dir =", AI_SERVICE)
print("RESULTS_DIR =", RESULTS_DIR)
print("Looking for metrics at:", RESULTS_DIR / "classifier_metrics_from_outputs.json")

metrics_file = RESULTS_DIR / "classifier_metrics_from_outputs.json"
if not metrics_file.exists():
    # As a last resort, try to find any classifier_metrics file under repo
    found = list(PROJECT_ROOT.rglob("classifier_metrics_from_outputs.json"))
    if found:
        metrics_file = found[0]
        print("Found metrics at:", metrics_file)
    else:
        raise FileNotFoundError(f"Metrics file not found: {RESULTS_DIR / 'classifier_metrics_from_outputs.json'}")

metrics = json.load(open(metrics_file, encoding="utf8"))

# find classes with f1 < 0.2
bad_classes = [int(k) for k, v in metrics.items() if k.isdigit() and v.get("f1-score", 1.0) < 0.20]
print("Low-F1 classes:", bad_classes)

# Load logits/labels (from RESULTS_DIR or found location)
logits_file = RESULTS_DIR / "logits.npy"
labels_file = RESULTS_DIR / "labels.npy"
if not logits_file.exists() or not labels_file.exists():
    # try to find them under repo
    found_logits = list(PROJECT_ROOT.rglob("logits.npy"))
    found_labels = list(PROJECT_ROOT.rglob("labels.npy"))
    if found_logits and found_labels:
        logits_file = found_logits[0]
        labels_file = found_labels[0]
        print("Found logits/labels at:", logits_file, labels_file)
    else:
        raise FileNotFoundError("Could not find logits.npy and/or labels.npy in expected locations.")

logits = np.load(str(logits_file))
labels = np.load(str(labels_file)).astype(int)

# Load test dataset
if not DATA_PATH.exists():
    # search for test.jsonl
    found = list(PROJECT_ROOT.rglob("test.jsonl"))
    if not found:
        raise FileNotFoundError("Could not find test.jsonl under project.")
    DATA_PATH = found[0]
    print("Found test.jsonl at:", DATA_PATH)

lines = [json.loads(l) for l in open(DATA_PATH, encoding="utf8")]

# Collect candidates
candidates = []
for i, sample in enumerate(lines):
    if int(labels[i]) in bad_classes:
        candidates.append(sample)
    if len(candidates) >= 500:
        break

# Save
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf8") as f:
    for c in candidates:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"Saved {len(candidates)} relabel candidates to {OUT_PATH}")
