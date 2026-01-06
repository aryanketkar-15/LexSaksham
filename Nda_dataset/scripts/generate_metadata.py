import os
import csv

# Folders
txt_folder = r"C:\Users\aryan\LexShaksham\LexShaksham\Nda_dataset\clauses_raw"
metadata_path = r"C:\Users\aryan\LexShaksham\LexShaksham\Nda_dataset\NDA_Metadata.csv"

# List all .txt files
files = [f for f in os.listdir(txt_folder) if f.endswith(".txt")]

# Create CSV
with open(metadata_path, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Contract_ID","Type","Language","Jurisdiction","Notes"])
    for f in files:
        contract_id = os.path.splitext(f)[0]  # e.g., nda_01
        writer.writerow([contract_id, "NDA", "English", "India", ""])

print(f"✅ NDA_Metadata.csv created at {metadata_path}")
