import json

# original label map (your JSON)
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

# normalize both sides
normalized = {}

for k, v in orig_map.items():
    key = k.lower().replace(" ", "_").replace("/", "").replace("(", "").replace(")", "").replace("-", "")
    # remove double underscores
    key = key.replace("__", "_")
    normalized[key] = v

json.dump(normalized, open("backend/ai_service/datasets/normalized_label_map.json", "w"), indent=2)
print("✔ Saved normalized label map")
print(normalized)
