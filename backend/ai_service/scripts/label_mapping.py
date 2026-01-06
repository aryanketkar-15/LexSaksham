"""
Label mapping utilities to convert between dataset label formats and model label format.
Dataset uses lowercase underscore-separated labels like 'payment_terms'.
Model uses readable label format like 'Payment Terms'.
"""

import json
from pathlib import Path

# Mapping from dataset labels to model-friendly labels
DATASET_TO_MODEL = {
    "confidentiality": "Confidentiality",
    "confidentiality_duration": "Confidentiality Duration",
    "dispute_resolution": "Dispute Resolution",
    "force_majeure": "Force Majeure",
    "governing_law": "Governing Law and Jurisdiction",
    "indemnity": "Indemnity / Liability",
    "intellectual_property": "Intellectual Property Rights",
    "leave_policy": "Leave Policy / Severance",
    "limitation_of_liability": "Limitation of Liability",
    "maintenance": "Maintenance and Utilities",
    "nda_exclusions": "NDA Exclusions",
    "non_compete": "Non-Compete / Restrictive Covenants",
    "notice_period": "Notice Period",
    "obligations": "Obligations / Responsibilities",
    "payment_terms": "Payment Terms",
    "probation_period": "Probation Period",
    "property_usage": "Property Usage Restrictions",
    "rent_terms": "Rent and Lease Terms",
    "return_of_materials": "Return or Destruction of Materials",
    "scope_of_work": "Scope of Work / Services",
    "security_deposit": "Security Deposit",
    "service_levels": "Service Levels (SLA)",
    "severance": "Severance and Exit Benefits",
    "termination": "Termination or Expiry",
    "warranties": "Warranties and Representations"
}

def normalize_dataset_label(label: str) -> str:
    """Convert dataset label format to model label format."""
    if isinstance(label, str):
        # Remove extra spaces and convert to lowercase
        label = label.strip().lower().replace(" ", "_")
    
    # Try direct mapping first
    if label in DATASET_TO_MODEL:
        return DATASET_TO_MODEL[label]
    
    # Try fuzzy matching
    for dataset_lbl, model_lbl in DATASET_TO_MODEL.items():
        if dataset_lbl.replace("_", "") == label.replace("_", ""):
            return model_lbl
    
    print(f"⚠️ Warning: Could not map label '{label}' — using as-is")
    return label

def get_model_labels():
    """Load model label mapping from label_classes.json."""
    base = Path(__file__).resolve().parents[1]
    label_path = base / "models" / "legalbert_clause_classifier" / "label_classes.json"
    if label_path.exists():
        with open(label_path, "r") as f:
            id2label = json.load(f)
            return {int(k): v for k, v in id2label.items()}
    return {}

if __name__ == "__main__":
    # Test mapping
    test_labels = [
        "confidentiality",
        "payment_terms",
        "obligations",
        "indemnity",
        "termination"
    ]
    print("Testing label mapping:")
    for lbl in test_labels:
        mapped = normalize_dataset_label(lbl)
        print(f"  {lbl:30} -> {mapped}")
