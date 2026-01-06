"""
Evaluate FAISS Judgment Retrieval
---------------------------------
Computes Recall@K on a query set against the existing FAISS index.
Saves results to backend/ai_service/results/faiss_metrics.json

Usage:
    python backend/ai_service/scripts/evaluate_faiss.py --data <path_to_jsonl> --k 5

Expected dataset format (JSONL):
    {"query": "text", "relevant_ids": [123, 456]}
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict

import numpy as np
import torch
import faiss
from transformers import AutoTokenizer, AutoModel


BASE_AI = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_AI / "models"
RESULTS_DIR = BASE_AI / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

INDEX_DIR = BASE_AI / "indexes"
FAISS_INDEX_PATH = INDEX_DIR / "supreme_judgment_index.faiss"
FAISS_METADATA_PATH = INDEX_DIR / "judgment_metadata.npy"

JUDGMENT_MODEL_DIR = MODELS_DIR / "legalbert_judgment_finetuned"


def load_dataset(path: Path) -> List[Dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "query" in obj and "relevant_ids" in obj:
                    items.append(obj)
            except json.JSONDecodeError:
                continue
    return items


def embed_text(model, tokenizer, text: str):
    with torch.no_grad():
        tokens = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = model(**tokens)
        return outputs.last_hidden_state.mean(dim=1).squeeze(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default=str(Path(__file__).resolve().parents[3] / "datasets" / "judgments" / "queries.jsonl"),
                        help="Path to JSONL dataset with 'query' and 'relevant_ids' (list)")
    parser.add_argument("--k", type=int, default=5, help="Top-K for recall computation")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Dataset not found at {data_path}")
        return

    items = load_dataset(data_path)
    if not items:
        print("No valid samples found in dataset.")
        return

    # Load index and metadata
    if not FAISS_INDEX_PATH.exists() or not FAISS_METADATA_PATH.exists():
        print("FAISS index or metadata not found.")
        return
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    metadata = np.load(FAISS_METADATA_PATH, allow_pickle=True)

    # Load embedding model
    tokenizer = AutoTokenizer.from_pretrained(JUDGMENT_MODEL_DIR)
    model = AutoModel.from_pretrained(JUDGMENT_MODEL_DIR)
    model.eval()

    correct = 0
    total = len(items)

    for ex in items:
        q = ex["query"]
        relevant = set(int(x) for x in ex.get("relevant_ids", []))
        q_emb = embed_text(model, tokenizer, q).detach().cpu().numpy().astype("float32").reshape(1, -1)
        distances, indices = index.search(q_emb, args.k)
        retrieved_ids = []
        for i in indices[0]:
            if i < len(metadata):
                jid, _ = metadata[i]
                retrieved_ids.append(int(jid))
        if any(r in relevant for r in retrieved_ids):
            correct += 1

    recall = correct / total if total else 0.0
    out = {"recall@k": recall, "k": args.k, "count": total}
    out_path = RESULTS_DIR / "faiss_metrics.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved FAISS metrics to {out_path}")


if __name__ == "__main__":
    main()