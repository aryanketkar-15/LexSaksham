import os
import re
import pandas as pd

# --- Step 2a: Define sub-project folders ---
sub_projects = {
    "employment": r"C:\Users\aryan\LexShaksham\Lexsham_2.0_AfterChetan\lexsaksham\employment_dataset\clauses_raw",
    "nda": r"C:\Users\aryan\LexShaksham\Lexsham_2.0_AfterChetan\lexsaksham\Nda_dataset\clauses_raw",
    "rental": r"C:\Users\aryan\LexShaksham\Lexsham_2.0_AfterChetan\lexsaksham\rental-dataset\clauses_raw",
    "service": r"C:\Users\aryan\LexShaksham\Lexsham_2.0_AfterChetan\lexsaksham\service_aggriment_dataset\clauses_raw"
}

# --- Step 2b: Define regex patterns ---
date_pattern = r"\b(?:\d{1,2}[-/th|st|nd|rd\s]*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/,\s]*\d{2,4}\b"
amount_pattern = r"₹?\s?[\d,]+(?:\.\d{1,2})?"
party_pattern = r"(Landlord|Tenant|Employer|Employee)[:\s]+([A-Za-z\s]+)"
email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
phone_pattern = r"\+?\d{10,13}"

# --- Step 2c: Store extracted data ---
data_list = []

# --- Step 2d: Loop through sub-projects and files ---
for project_name, folder_path in sub_projects.items():
    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}, skipping...")
        continue
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".txt"):
            file_path = os.path.join(folder_path, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                # Extract structured fields using regex
                dates = re.findall(date_pattern, text)
                amounts = re.findall(amount_pattern, text)
                parties = re.findall(party_pattern, text)
                emails = re.findall(email_pattern, text)
                phones = re.findall(phone_pattern, text)
                
                # Add extracted data to list
                data_list.append({
                    "sub_project": project_name,
                    "file_name": file_name,
                    "dates": dates,
                    "amounts": amounts,
                    "parties": parties,
                    "emails": emails,
                    "phones": phones
                })
            
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

# --- Step 2e: Convert list to DataFrame and save CSV ---
df = pd.DataFrame(data_list)

# Save CSV in main folder
csv_path = r"C:\Users\aryan\LexShaksham\Lexsham_2.0_AfterChetan\lexsaksham\structured_fields_all_projects.csv"
df.to_csv(csv_path, index=False, encoding="utf-8")

print(f"✅ Structured fields extracted and saved to: {csv_path}")
