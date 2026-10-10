"""
Script to upload LexSaksham models to Hugging Face Hub.
Directly uploads only root inference model files (weights + configs + tokenizers).
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from huggingface_hub import HfApi, login

MODELS = [
    {
        "name": "lexsaksham-legalbert-clause-classifier",
        "path": os.path.abspath("backend/ai_service/models/legalbert_clause_classifier"),
        "desc": "Fine-tuned Legal-BERT classifier for Indian legal contract clauses (20+ categories)."
    },
    {
        "name": "lexsaksham-legal-t5-summarizer",
        "path": os.path.abspath("backend/ai_service/models/legal_t5_summarizer"),
        "desc": "Fine-tuned Legal-T5 model for simplifying legal contract clauses into plain English."
    },
    {
        "name": "lexsaksham-legalbert-judgment-finetuned",
        "path": os.path.abspath("backend/ai_service/models/legalbert_judgment_finetuned"),
        "desc": "Fine-tuned Legal-BERT embedding model for semantic Indian Supreme Court judgment retrieval."
    }
]

def main():
    token = os.getenv("HF_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1]
    
    if token:
        login(token=token)
    
    api = HfApi()
    user = api.whoami()
    username = user["name"]
    print(f"Logged in as Hugging Face user: {username}")
    
    for m in MODELS:
        repo_id = f"{username}/{m['name']}"
        print(f"\n==========================================")
        print(f"Repository: https://huggingface.co/{repo_id}")
        print(f"Source: {m['path']}")
        print(f"==========================================")
        
        api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True, private=False)
        
        # Get all top-level files in model directory (skipping checkpoint directories)
        files = [f for f in os.listdir(m["path"]) if os.path.isfile(os.path.join(m["path"], f))]
        
        # Sort so config and tokenizers upload first, safetensors last
        files.sort(key=lambda x: 1 if x.endswith(".safetensors") else 0)
        
        for f in files:
            file_path = os.path.join(m["path"], f)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"  Uploading {f} ({size_mb:.2f} MB)...")
            api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=f,
                repo_id=repo_id,
                repo_type="model"
            )
            print(f"  Done {f}")

        # Add a clean README model card
        readme_content = f"""---
license: mit
pipeline_tag: {"text-classification" if "classifier" in m["name"] else "summarization" if "t5" in m["name"] else "feature-extraction"}
tags:
- legal
- legalbert
- india
- contracts
---

# {m['name']}

{m['desc']}

Part of the **LexSaksham** AI-powered legal contract analysis platform.

## Usage

```python
from transformers import AutoTokenizer, AutoModel

model_id = "{repo_id}"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModel.from_pretrained(model_id)
```
"""
        api.upload_file(
            path_or_fileobj=readme_content.encode("utf-8"),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="model"
        )
        print(f"Repository ready: https://huggingface.co/{repo_id}")

    print("\nAll 3 LexSaksham models uploaded to Hugging Face successfully!")

if __name__ == "__main__":
    main()
