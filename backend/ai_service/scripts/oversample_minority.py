# oversample_minority.py
import json, collections, random
from pathlib import Path

src = Path("backend/ai_service/datasets/clause_dataset/prepared/train_relabelled.jsonl")
if not src.exists():
    src = Path("backend/ai_service/datasets/clause_dataset/prepared/train_int.jsonl")
out = Path("backend/ai_service/datasets/clause_dataset/prepared/train_balanced.jsonl")

lines = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines()]
counts = collections.Counter([str(l["label"]) for l in lines])
max_count = max(counts.values())

print("Class counts before:", counts)
new = list(lines)
for label, cnt in counts.items():
    need = max_count - cnt
    if need <= 0:
        continue
    samples = [s for s in lines if str(s["label"]) == label]
    for i in range(need):
        new.append(random.choice(samples))

random.shuffle(new)
out.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in new), encoding="utf-8")
print("Wrote", out, "len:", len(new))
