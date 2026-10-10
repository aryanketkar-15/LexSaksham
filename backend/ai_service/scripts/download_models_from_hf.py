"""
Download fine-tuned LexSaksham models from Hugging Face Hub into local directory.
"""

import os
from huggingface_hub import snapshot_download

MODELS = [
    {
        "repo_id": "aryanketkar02/lexsaksham-legalbert-clause-classifier",
        "local_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/legalbert_clause_classifier"))
    },
    {
        "repo_id": "aryanketkar02/lexsaksham-legal-t5-summarizer",
        "local_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/legal_t5_summarizer"))
    },
    {
        "repo_id": "aryanketkar02/lexsaksham-legalbert-judgment-finetuned",
        "local_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/legalbert_judgment_finetuned"))
    }
]

def main():
    print("Downloading LexSaksham models from Hugging Face...")
    for m in MODELS:
        print(f"\nFetching {m['repo_id']} -> {m['local_dir']}")
        os.makedirs(m["local_dir"], exist_ok=True)
        snapshot_download(
            repo_id=m["repo_id"],
            local_dir=m["local_dir"],
            local_dir_use_symlinks=False
        )
        print(f"Successfully downloaded {m['repo_id']}")

    print("\nAll models downloaded and ready for use in backend/ai_service/models/!")

if __name__ == "__main__":
    main()
