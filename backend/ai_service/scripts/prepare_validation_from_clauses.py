"""Create a small validation JSONL from the existing clauses dataset.

This helper attempts to map `clause_type` values in
`datasets/clause_dataset/clauses_dataset.jsonl` to the label indices
used by the classifier (`models/legalbert_clause_classifier/label_classes.json`).

Usage:
    python prepare_validation_from_clauses.py \
      --in datasets/clause_dataset/clauses_dataset.jsonl \
      --out datasets/validation.jsonl \
      --max 500

The script will only include examples for which it can determine a
label index. Inspect the produced file before running calibration.
"""
import argparse
import json
from pathlib import Path
from collections import defaultdict
import logging

# Determine base ai_service directory so defaults resolve correctly when
# script is run from repo root or other working directories.
BASE_DIR = Path(__file__).resolve().parents[1]


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_label_map(label_path: Path):
    with open(label_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_simple_type_map():
    # Map common clause_type tokens to label indices (best-effort)
    return {
        'scope_of_work': 19,
        'scope': 19,
        'warranties': 24,
        'warranty': 24,
        'termination': 23,
        'notice_period': 12,
        'payment_terms': 14,
        'payment': 14,
        'force_majeure': 3,
        'force majeure': 3,
        'obligations': 13,
        'obligation': 13,
        'leave_policy': 7,
        'probation_period': 15,
        'rent_terms': 17,
        'rent': 17,
        'indemnity': 5,
        'liability': 5,
        'confidentiality': 0,
        'intellectual_property': 6,
        'ip': 6,
        'payment_terms': 14,
    }


def prepare(in_path: Path, out_path: Path, label_map_path: Path, max_examples: int = 500):
    if not in_path.exists():
        logger.error(f"Input dataset not found: {in_path}")
        return 1

    if not label_map_path.exists():
        logger.error(f"Label classes file not found: {label_map_path}")
        return 1

    type_map = build_simple_type_map()
    examples_written = 0
    skipped = 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(in_path, 'r', encoding='utf-8') as fin, open(out_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            txt = obj.get('clause_text') or obj.get('text') or obj.get('content')
            ctype = (obj.get('clause_type') or '').lower()
            if not txt or not ctype:
                skipped += 1
                continue

            label_idx = type_map.get(ctype)
            if label_idx is None:
                # try simple contains matching
                for k, v in type_map.items():
                    if k in ctype:
                        label_idx = v
                        break

            if label_idx is None:
                skipped += 1
                continue

            out_obj = {"text": txt, "label_idx": int(label_idx)}
            fout.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            examples_written += 1
            if examples_written >= max_examples:
                break

    logger.info(f"Wrote {examples_written} examples to {out_path} (skipped {skipped})")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='in_path', required=False,
                        default=str(BASE_DIR / 'datasets' / 'clause_dataset' / 'clauses_dataset.jsonl'))
    parser.add_argument('--out', dest='out_path', required=False,
                        default=str(BASE_DIR / 'datasets' / 'validation.jsonl'))
    parser.add_argument('--label-classes', dest='label_classes', required=False,
                        default=str(BASE_DIR / 'models' / 'legalbert_clause_classifier' / 'label_classes.json'))
    parser.add_argument('--max', dest='max_examples', type=int, default=500)

    args = parser.parse_args()
    in_path = Path(args.in_path)
    out_path = Path(args.out_path)
    label_map_path = Path(args.label_classes)

    # If provided paths are relative and do not exist, resolve relative to BASE_DIR
    def resolve(p: Path) -> Path:
        if p.exists():
            return p
        alt = (BASE_DIR / p)
        if alt.exists():
            return alt
        return p

    in_path = resolve(in_path)
    out_path = resolve(out_path)
    label_map_path = resolve(label_map_path)

    return prepare(in_path, out_path, label_map_path, args.max_examples)


if __name__ == '__main__':
    raise SystemExit(main())
