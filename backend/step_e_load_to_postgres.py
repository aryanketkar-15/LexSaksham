"""
step_e_load_to_postgres.py

Loads enriched clause CSVs into PostgreSQL.
"""

import os
import json
import psycopg2
import pandas as pd
import numpy as np
from psycopg2.extras import execute_values

# ---------- CONFIG ----------
BASE_PATH = r"C:\Users\Chetan\lexsaksham"

# choose dataset here (run per dataset)
DATASET = "service_aggriment_dataset"  
# options: employment_dataset / Nda_dataset / rental-dataset / service_aggriment_dataset / external_datasets/Indian_Legal_Documents_LuRA

CLAUSES_RAW = os.path.join(BASE_PATH, DATASET, "clauses_raw")
INPUT_CSV = os.path.join(CLAUSES_RAW, "extracted_clauses_enriched.csv")

# database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "lexshaksham_db",
    "user": "postgres",
    "password": "Cc25@hetan",   
}

TABLE_NAME = "clauses"

# ---------- HELPERS ----------
def convert_types(val):
    """Ensure values are plain Python types for psycopg2."""
    if isinstance(val, (np.int64, np.int32)):
        return int(val)
    if isinstance(val, (np.float64, np.float32)):
        return float(val)
    if pd.isna(val):  # handle NaN
        return None
    return val

# ---------- MAIN ----------
if not os.path.exists(INPUT_CSV):
    raise SystemExit(f"❌ Input CSV not found: {INPUT_CSV}")

print(f"📂 Loading CSV: {INPUT_CSV}")
df = pd.read_csv(INPUT_CSV)

print(f"✅ Loaded {len(df)} rows from {INPUT_CSV}")

# Connect to Postgres
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Create table if not exists
create_table_query = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    clause_id UUID PRIMARY KEY,
    file_name TEXT,
    paragraph_index INT,
    agreement_type TEXT,
    clause_type TEXT,
    matched_keywords TEXT,
    match_count INT,
    match_score FLOAT,
    confidence TEXT,
    char_len INT,
    token_count INT,
    clause_text TEXT
);
"""
cur.execute(create_table_query)
conn.commit()
print(f"✅ Table ready: {TABLE_NAME}")

# Prepare insert query
insert_query = f"""
INSERT INTO {TABLE_NAME} (
    clause_id, file_name, paragraph_index, agreement_type, clause_type,
    matched_keywords, match_count, match_score, confidence,
    char_len, token_count, clause_text
) VALUES %s
"""

# Convert numpy types → Python types
values = [
    tuple(convert_types(v) for v in row)
    for row in df.to_numpy()
]

# Bulk insert
print(f"⬆️ Inserting {len(values)} rows...")
execute_values(cur, insert_query, values, page_size=1000)
conn.commit()

print(f"✅ Insert complete: {len(values)} rows inserted into {TABLE_NAME}")

# Close connection
cur.close()
conn.close()
print("🔒 Connection closed")
