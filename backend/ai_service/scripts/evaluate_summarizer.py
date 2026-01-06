"""
Evaluate Legal-T5 Summarizer
----------------------------
Loads the trained summarizer and computes ROUGE-1/2/L on a dataset.
Saves results to backend/ai_service/results/summarizer_metrics.json

Usage:
    python backend/ai_service/scripts/evaluate_summarizer.py --data <path_to_jsonl>

Expected dataset format (JSONL):
    {"text": "clause text", "reference": "gold summary"}
"""

import json
import argparse
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from rouge_score import rouge_scorer


BASE_AI = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_AI / "models"
RESULTS_DIR = BASE_AI / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SUMMARIZER_DIR = MODELS_DIR / "legal_t5_summarizer"


def load_dataset(path: Path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "text" in obj and "reference" in obj:
                    items.append(obj)
                elif "text" in obj and "label_idx" in obj:
                    # Map label_idx to a placeholder reference text
                    obj["reference"] = f"Reference text for label {obj['label_idx']}"
                    items.append(obj)
            except json.JSONDecodeError:
                continue
    return items


def process_in_batches(items, batch_size, model, tokenizer, scorer):
    scores = {"rouge1": [], "rouge2": [], "rougeL": []}
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        for ex in batch:
            text = ex["text"]
            ref = ex["reference"]
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=256)
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            with torch.no_grad():
                ids = model.generate(**inputs, max_length=64, num_beams=4, early_stopping=True)
            pred = tokenizer.decode(ids[0], skip_special_tokens=True)

            s = scorer.score(ref, pred)
            for k in scores.keys():
                scores[k].append(s[k].fmeasure)
    return scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default=str(Path(__file__).resolve().parents[3] / "datasets" / "summarization" / "validation.jsonl"),
                        help="Path to JSONL dataset with 'text' and 'reference'")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Dataset not found at {data_path}")
        return

    items = load_dataset(data_path)
    if not items:
        print("No valid samples found in dataset.")
        return

    tokenizer = AutoTokenizer.from_pretrained(SUMMARIZER_DIR)
    model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARIZER_DIR).to("cuda" if torch.cuda.is_available() else "cpu")
    model.eval()

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

    scores = process_in_batches(items, batch_size=8, model=model, tokenizer=tokenizer, scorer=scorer)

    avg_scores = {k: sum(v) / len(v) if v else 0.0 for k, v in scores.items()}

    out = {
        "count": len(items),
        "model": "legal_t5_summarizer",
        "rouge": avg_scores
    }

    out_path = RESULTS_DIR / "summarizer_metrics.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved ROUGE metrics to {out_path}")


if __name__ == "__main__":
    main()