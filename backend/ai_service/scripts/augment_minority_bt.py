# backend/ai_service/scripts/augment_minority_bt.py
import importlib.util
import json
import random
from pathlib import Path

# Path to translate utils in your repo
TRANSLATE_UTILS_PATH = Path("backend/ai_service/utils/translate_utils.py")

def load_translate_utils(path: Path):
    if not path.exists():
        print("translate_utils.py not found at", path)
        return None
    spec = importlib.util.spec_from_file_location("translate_utils", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

translate_mod = load_translate_utils(TRANSLATE_UTILS_PATH)

# Fallback wrappers if functions not present
def translate_to_en(text, src_hint=None):
    if translate_mod and hasattr(translate_mod, "translate_to_en"):
        return translate_mod.translate_to_en(text, src_hint=src_hint)
    return text

def translate_to_hi(text, src_hint=None):
    if translate_mod and hasattr(translate_mod, "translate_to_hi"):
        return translate_mod.translate_to_hi(text, src_hint=src_hint)
    return text

# Files (use train_relabelled if you created it)
SRC = Path("backend/ai_service/datasets/clause_dataset/prepared/train_relabelled.jsonl")
if not SRC.exists():
    SRC = Path("backend/ai_service/datasets/clause_dataset/prepared/train_int.jsonl")
OUT = Path("backend/ai_service/datasets/clause_dataset/prepared/train_aug_bt.jsonl")

print("Using source:", SRC)
lines = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines()]

# group by label
by_label = {}
for obj in lines:
    lbl = str(obj.get("label"))
    by_label.setdefault(lbl, []).append(obj)

augmented = []
for lbl, samples in by_label.items():
    # only augment rare classes (threshold tweakable)
    if len(samples) >= 300:
        continue
    n_aug_per_sample = 1  # how many new paraphrases per sample
    for s in samples:
        text = s.get("text", "")
        # Try a safe back-translation pair:
        try:
            en = translate_to_en(text, src_hint="auto")
            back = translate_to_hi(en)
            if back and back.strip() and back != text:
                new = dict(s)
                new["text"] = back
                augmented.append(new)
        except Exception as e:
            # skip if translation fails
            continue

print("Original:", len(lines), "Augmented extra:", len(augmented))
out_lines = lines + augmented
random.shuffle(out_lines)
OUT.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out_lines), encoding="utf-8")
print("Wrote", OUT, "len:", len(out_lines))
