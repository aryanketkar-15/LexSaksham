"""
One-click script to download all LexSaksham models from Hugging Face Hub.
Can be executed from project root or anywhere.
"""

import os
from huggingface_hub import snapshot_download

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "backend", "ai_service", "models")

MODELS = [
    {
        "repo_id": "aryanketkar02/lexsaksham-legalbert-clause-classifier",
        "local_dir": os.path.join(MODELS_DIR, "legalbert_clause_classifier")
    },
    {
        "repo_id": "aryanketkar02/lexsaksham-legal-t5-summarizer",
        "local_dir": os.path.join(MODELS_DIR, "legal_t5_summarizer")
    },
    {
        "repo_id": "aryanketkar02/lexsaksham-legalbert-judgment-finetuned",
        "local_dir": os.path.join(MODELS_DIR, "legalbert_judgment_finetuned")
    }
]

def main():
    print("🚀 Downloading LexSaksham models from Hugging Face Hub...")
    for m in MODELS:
        print(f"\n📦 Fetching {m['repo_id']} -> {m['local_dir']}")
        os.makedirs(m["local_dir"], exist_ok=True)
        snapshot_download(
            repo_id=m["repo_id"],
            local_dir=m["local_dir"],
            local_dir_use_symlinks=False
        )
        print(f"✅ Successfully downloaded {m['repo_id']}")

    print("\n🎉 All 3 models downloaded and ready in backend/ai_service/models/!")

if __name__ == "__main__":
    main()
