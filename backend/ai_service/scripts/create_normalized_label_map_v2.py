# backend/ai_service/scripts/create_normalized_label_map_v2.py
import json
from pathlib import Path

# Official human-readable label → numeric ID
orig_map = {
  "Confidentiality": 0,
  "Confidentiality Duration": 1,
  "Dispute Resolution": 2,
  "Force Majeure": 3,
  "Governing Law and Jurisdiction": 4,
  "Indemnity / Liability": 5,
  "Intellectual Property Rights": 6,
  "Leave Policy / Severance": 7,
  "Limitation of Liability": 8,
  "Maintenance and Utilities": 9,
  "NDA Exclusions": 10,
  "Non-Compete / Restrictive Covenants": 11,
  "Notice Period": 12,
  "Obligations / Responsibilities": 13,
  "Payment Terms": 14,
  "Probation Period": 15,
  "Property Usage Restrictions": 16,
  "Rent and Lease Terms": 17,
  "Return or Destruction of Materials": 18,
  "Scope of Work / Services": 19,
  "Security Deposit": 20,
  "Service Levels (SLA)": 21,
  "Severance and Exit Benefits": 22,
  "Termination or Expiry": 23,
  "Warranties and Representations": 24
}

def normalize_key(label: str):
    """Normalize a label into a lowercase snake-case key."""
    x = label.lower().strip()
    x = x.replace("/", " ").replace("(", " ").replace(")", " ").replace("-", " ")
    x = "_".join(x.split())
    return x

# Step 1 — Build normalized canonical map from orig_map
base_normalized = {normalize_key(k): v for k, v in orig_map.items()}

# Step 2 — Add aliases (handles all your dataset label variants)
aliases = {
    # Canonical groups
    "confidentiality": "confidentiality",
    "confidentiality_duration": "confidentiality_duration",

    "dispute_resolution": "dispute_resolution",
    "force_majeure": "force_majeure",

    "governing_law": "governing_law_and_jurisdiction",
    "governing_law_and_jurisdiction": "governing_law_and_jurisdiction",

    "indemnity": "indemnity_liability",
    "indemnity_liability": "indemnity_liability",

    "intellectual_property": "intellectual_property_rights",
    "intellectual_property_rights": "intellectual_property_rights",
    "ip": "intellectual_property_rights",

    "leave_policy": "leave_policy_severance",
    "leave_policy_severance": "leave_policy_severance",
    "severance": "severance_and_exit_benefits",
    "severance_and_exit_benefits": "severance_and_exit_benefits",

    "limitation": "limitation_of_liability",
    "limitation_of_liability": "limitation_of_liability",
    "liability": "limitation_of_liability",

    "maintenance": "maintenance_and_utilities",
    "maintenance_and_utilities": "maintenance_and_utilities",

    "nda": "nda_exclusions",
    "nda_exclusions": "nda_exclusions",

    # **IMPORTANT FIX**
    "non_compete": "non_compete_restrictive_covenants",
    "noncompete": "non_compete_restrictive_covenants",
    "non_compete_restrictive_covenants": "non_compete_restrictive_covenants",

    "notice": "notice_period",
    "notice_period": "notice_period",

    "obligations": "obligations_responsibilities",
    "obligations_responsibilities": "obligations_responsibilities",

    "payment_terms": "payment_terms",

    "probation": "probation_period",
    "probation_period": "probation_period",

    "property_usage": "property_usage_restrictions",
    "property_usage_restrictions": "property_usage_restrictions",

    "rent_terms": "rent_and_lease_terms",
    "rent_and_lease_terms": "rent_and_lease_terms",
    "rent_and_lease": "rent_and_lease_terms",

    "return_of_materials": "return_or_destruction_of_materials",
    "return_or_destruction_of_materials": "return_or_destruction_of_materials",

    "scope_of_work": "scope_of_work_services",
    "scope_of_work_services": "scope_of_work_services",
    "scope": "scope_of_work_services",

    "security_deposit": "security_deposit",

    "service_levels": "service_levels_sla",
    "service_level": "service_levels_sla",
    "service_levels_sla": "service_levels_sla",

    "termination": "termination_or_expiry",
    "termination_or_expiry": "termination_or_expiry",

    "warranties": "warranties_and_representations",
    "warranties_and_representations": "warranties_and_representations",
}

# Step 3 — Resolve aliases to numeric IDs
final_map = dict(base_normalized)  # start from canonical

for alias, target in aliases.items():
    if target in base_normalized:
        final_map[alias] = base_normalized[target]
    else:
        # Should not happen; if it does, leave unmapped so we can catch it
        final_map[alias] = None

# Step 4 — Write to file
out_path = Path("backend/ai_service/datasets/normalized_label_map.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
json.dump(final_map, open(out_path, "w"), indent=2)

print("✔ Wrote normalized label map with aliases to:", out_path)
print(json.dumps(final_map, indent=2))
