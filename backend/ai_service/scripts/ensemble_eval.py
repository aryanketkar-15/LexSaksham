# save as backend/ai_service/scripts/ensemble_eval.py
import numpy as np, json, os, argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument("--logit_dirs", nargs="+", required=True)
parser.add_argument("--outdir", default="backend/ai_service/results/ensemble")
args=parser.parse_args()
out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)

logits_list=[]
labels=None
for d in args.logit_dirs:
    lfile = Path(d)/"logits.npy"
    la = Path(d)/"labels.npy"
    assert lfile.exists(), lfile
    logits_list.append(np.load(lfile))
    if labels is None:
        labels = np.load(la)
    else:
        assert np.array_equal(labels, np.load(la))
# average
avg = np.mean(np.stack(logits_list,axis=0), axis=0)
np.save(out/"logits.npy", avg)
np.save(out/"labels.npy", labels)
print("Saved ensemble logits and labels to", out)
print("Now run: python backend/ai_service/scripts/eval_from_outputs_robust.py (it will pick up results from backend/ai_service/results by default).")
