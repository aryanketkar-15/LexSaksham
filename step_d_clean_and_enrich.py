"""
step_d_clean_and_enrich.py

Input:  <dataset>/clauses_raw/extracted_clauses_candidates.csv
Output: <dataset>/clauses_raw/extracted_clauses_enriched.csv
Also saves review CSVs:
  - low_confidence_for_review.csv  (to prioritize human labeling)
  - top_duplicates.csv             (optional duplicates summary)
"""

import os
import json
import re
import uuid
import pandas as pd

# ---------- CONFIG ----------
BASE_PATH = r"C:\Users\aryan\LexShaksham\Lexsham_2.0_AfterChetan\lexsaksham"
DATASET = "service_aggriment_dataset"   # change per run: employment_dataset / Nda_dataset / rental-dataset / service_aggriment_dataset
CLAUSES_RAW = os.path.join(BASE_PATH, DATASET, "clauses_raw")
INPUT_CSV = os.path.join(CLAUSES_RAW, "extracted_clauses_candidates.csv")
OUTPUT_CSV = os.path.join(CLAUSES_RAW, "extracted_clauses_enriched.csv")
REVIEW_LOW_CONF = os.path.join(CLAUSES_RAW, "low_confidence_for_review.csv")
DUPES_SUMMARY = os.path.join(CLAUSES_RAW, "top_duplicates.csv")
TAXONOMY_PATH = os.path.join(BASE_PATH, "config", "clause_taxonomy.json")

# thresholds / params
MIN_CHARS = 30            # drop clauses shorter than this (likely noise)
MIN_TOKENS = 4            # alternative token-based filter
CONF_HIGH = 0.6           # score >= CONF_HIGH => high confidence
CONF_LOW = 0.25           # score <= CONF_LOW => low confidence -> send for review
USE_WORD_BOUNDARY = True  # use \b regex match to avoid substring false positives
NORMALIZE_NUMBERING = True

# ---------- helpers ----------
def load_taxonomy(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def normalize_clause_text(text):
    if pd.isna(text):
        return ""
    s = str(text)
    # remove multiple spaces/newlines
    s = re.sub(r"\r\n", "\n", s)
    s = re.sub(r"\s+", " ", s).strip()
    # optional: remove leading numbering like "1." or "(a)"
    if NORMALIZE_NUMBERING:
        s = re.sub(r"^\s*\(?\d+\)?[\.\)]\s*", "", s)
        s = re.sub(r"^\s*\(?[a-zA-Z]\)?[\.\)]\s*", "", s)
    return s

def find_keywords_for_clause(text, keywords):
    """
    Return list of matched keywords (from keywords list).
    Uses word-boundary matching for short keywords to avoid partial hits.
    """
    t = text.lower()
    found = []
    for kw in keywords:
        kw_l = kw.lower().strip()
        if not kw_l:
            continue
        if USE_WORD_BOUNDARY and re.match(r"^[A-Za-z0-9_]{1,20}$", kw_l):
            # alphanumeric short token: use word-boundary regex
            pattern = r"\b" + re.escape(kw_l) + r"\b"
            if re.search(pattern, t):
                found.append(kw)
        else:
            # phrase or contains special char: substring search
            if kw_l in t:
                found.append(kw)
    return found

def compute_match_score(match_count, total_keywords):
    # simple normalized score: fraction of clause keywords matched
    if total_keywords <= 0:
        return 0.0
    return match_count / total_keywords

# ---------- main ----------
if not os.path.exists(INPUT_CSV):
    raise SystemExit(f"Input not found: {INPUT_CSV}")

tax = load_taxonomy(TAXONOMY_PATH)
df = pd.read_csv(INPUT_CSV)

# ensure columns exist
expected = ["file_name", "paragraph_index", "agreement_type", "clause_type", "clause_text"]
for c in expected:
    if c not in df.columns:
        raise SystemExit(f"Expected column missing in input CSV: {c}")

# normalize clause text
df["clause_text"] = df["clause_text"].apply(normalize_clause_text)
df["char_len"] = df["clause_text"].str.len()
df["token_count"] = df["clause_text"].str.split().apply(lambda x: len(x) if isinstance(x, list) else 0)

# enrich: matched keywords and match_count, match_score
matched_keywords_list = []
match_counts = []
match_scores = []

for idx, row in df.iterrows():
    agreement_type = str(row["agreement_type"])
    clause_type = str(row["clause_type"])
    text = row["clause_text"]

    # get the keyword list from taxonomy; taxonomy structure: top-level agreement types -> clause types -> keywords list
    keywords = []
    if agreement_type in tax and clause_type in tax[agreement_type]:
        keywords = tax[agreement_type][clause_type]
    else:
        # fallback: try across full taxonomy (in case clause_type was assigned generically)
        if clause_type in (k for at in tax.values() for k in at.keys()):
            # find which top-level it belongs to
            for atype, clauses in tax.items():
                if clause_type in clauses:
                    keywords = clauses[clause_type]
                    break
        else:
            # try all keywords across taxonomy (rare)
            keywords = []
            for atype, clauses in tax.items():
                for ct, kwlist in clauses.items():
                    keywords.extend(kwlist)

    matched = find_keywords_for_clause(text, keywords)
    matched_keywords_list.append(";".join(sorted(set(matched))))
    match_counts.append(len(matched))
    match_scores.append(compute_match_score(len(matched), len(keywords) if len(keywords)>0 else 1))

df["matched_keywords"] = matched_keywords_list
df["match_count"] = match_counts
df["match_score"] = match_scores

# Add confidence label
def confidence_label(score):
    if score >= CONF_HIGH:
        return "high"
    if score <= CONF_LOW:
        return "low"
    return "medium"

df["confidence"] = df["match_score"].apply(confidence_label)

# Remove duplicates (file + clause_text + clause_type)
before = len(df)
df = df.drop_duplicates(subset=["file_name", "clause_type", "clause_text"])
after = len(df)

# Filter short / low substance clauses
df = df[ (df["char_len"] >= MIN_CHARS) & (df["token_count"] >= MIN_TOKENS) ].copy()

# Add unique id
df["clause_id"] = df.apply(lambda _: str(uuid.uuid4()), axis=1)

# Reorder columns for convenience
cols = ["clause_id", "file_name", "paragraph_index", "agreement_type", "clause_type",
        "matched_keywords", "match_count", "match_score", "confidence",
        "char_len", "token_count", "clause_text"]
df = df[cols]

# Save enriched file
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
print(f"Saved enriched clauses to: {OUTPUT_CSV} ({len(df)} rows, dupes removed: {before-after})")

# Save low-confidence set for reviewer
low_conf_df = df[df["confidence"] == "low"].sort_values("match_score")
low_conf_df.to_csv(REVIEW_LOW_CONF, index=False, encoding="utf-8")
print(f"Saved low-confidence items to: {REVIEW_LOW_CONF} ({len(low_conf_df)} rows)")

# Optional duplicates summary (top repeated clause_text across files)
dupes = df.groupby("clause_text").size().reset_index(name="count").sort_values("count", ascending=False)
dupes.to_csv(DUPES_SUMMARY, index=False, encoding="utf-8")
print(f"Saved duplicates summary to: {DUPES_SUMMARY}")
