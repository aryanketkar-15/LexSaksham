"""
train_classifier.py — Step G1: Data Preparation and Cleaning
Loads enriched clause data from PostgreSQL or CSV
Prepares a clean dataset for training the clause classification model
"""

import os
import pandas as pd
import psycopg2

# --- Database config ---
DB_CONFIG = {
    "dbname": "lexshaksham_db",
    "user": "postgres",           # ← your postgres username
    "password": "root",  # ← your postgres password
    "host": "localhost",
    "port": "5432"
}

# --- Output paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "..", "models", "prepared_data.csv")

# --- Option 1: Load from Database ---
def load_from_db():
    print("📦 Loading data from PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    query = """
        SELECT clause_id, clause_text, clause_type, confidence
        FROM clauses
        WHERE clause_type IS NOT NULL AND clause_text IS NOT NULL
          AND char_length(clause_text) > 40;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- Option 2: Load from CSV (if you prefer) ---
def load_from_csv():
    path = os.path.join(BASE_DIR, "..", "..", "extracted_clauses_enriched.csv")
    print(f"📂 Loading from CSV: {path}")
    return pd.read_csv(path)

# --- Data Cleaning ---
def clean_data(df):
    print("🧹 Cleaning and normalizing clause data...")
    df.dropna(subset=["clause_text", "clause_type"], inplace=True)
    df["clause_text"] = df["clause_text"].str.replace(r"\s+", " ", regex=True)
    df["clause_type"] = df["clause_type"].str.strip().str.title()
    df = df[df["clause_text"].str.len() > 50]
    print(f"✅ Cleaned dataset: {len(df)} usable clauses")
    return df

# --- Save prepared data ---
def save_prepared_data(df):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"💾 Saved prepared data → {OUTPUT_PATH}")

if __name__ == "__main__":
    try:
        df = load_from_db()
    except Exception as e:
        print(f"⚠️ DB load failed ({e}), falling back to CSV...")
        df = load_from_csv()
    df = clean_data(df)
    save_prepared_data(df)
    print("🎯 Step G1 — Data Preparation complete.")
