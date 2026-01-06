import os
import csv
import glob

BASE = "backend/ai_service/datasets/relabel_by_class"

files = glob.glob(os.path.join(BASE, "*.csv"))

total = 0
empty = 0
invalid = 0
counts = {}

for f in files:
    print(f"\nChecking:", f)
    with open(f, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            total += 1
            nl = row.get("new_label", "").strip()

            if nl == "":
                empty += 1
                continue

            if not nl.isdigit():
                invalid += 1
                print("Invalid entry:", nl)
                continue

            counts[nl] = counts.get(nl, 0) + 1

print("\n--- SUMMARY ---")
print("Total rows:", total)
print("Empty new_label:", empty)
print("Invalid entries:", invalid)
print("Counts per label:", counts)
