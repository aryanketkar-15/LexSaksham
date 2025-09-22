import os
import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import pytesseract
import tempfile
import pandas as pd
import json
import re

# -------------------------
# Base project path
# -------------------------
BASE_PATH = r"C:\Users\aryan\LexShaksham\Lexsham_2.0_AfterChetan\lexsaksham"

# Load taxonomy (common for all agreements)
with open(os.path.join(BASE_PATH, "config", "clause_taxonomy.json"), "r", encoding="utf-8") as f:
    CLAUSE_TAXONOMY = json.load(f)

print("✅ Loaded clause taxonomy for this project:")
for agreement_type, clauses in CLAUSE_TAXONOMY.items():
    print(f"{agreement_type.upper()} → {list(clauses.keys())}")

# -------------------------
# Folders
# -------------------------
raw_folder = os.path.join(BASE_PATH, "service_aggriment_dataset", "raw_docs")
txt_folder = os.path.join(BASE_PATH, "service_aggriment_dataset", "clauses_raw")
os.makedirs(txt_folder, exist_ok=True)

# -------------------------
# Tesseract path
# -------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -------------------------
# Step A/B: Convert PDFs/DOCX/TXT to text
# -------------------------
data_list = []   # 👈 now we define it

for file in os.listdir(raw_folder):
    file_path = os.path.join(raw_folder, file)
    txt_path = os.path.join(txt_folder, os.path.splitext(file)[0] + ".txt")

    try:
        full_text = ""

        if file.endswith(".pdf"):
            doc = fitz.open(file_path)
            for page in doc:
                text = page.get_text().replace("\xa0", " ")
                full_text += text + "\n"

            # If PDF has no text, use OCR
            if len(full_text.strip()) == 0:
                print(f"OCR scanning: {file}")
                for page_num in range(len(doc)):
                    pix = doc[page_num].get_pixmap()
                    img_data = pix.tobytes("ppm")
                    with tempfile.NamedTemporaryFile(suffix=".ppm") as tmp_img:
                        tmp_img.write(img_data)
                        tmp_img.flush()
                        text = pytesseract.image_to_string(Image.open(tmp_img))
                        full_text += text + "\n"

        elif file.endswith(".docx"):
            doc = Document(file_path)
            full_text = "\n".join([para.text for para in doc.paragraphs])

        elif file.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as src:
                full_text = src.read()

        # Save cleaned text
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        print(f"Converted: {file} → {txt_path}")

        # 👇 Collect for all_agreements.csv
        data_list.append({
            "file_name": file,
            "txt_path": txt_path,
            "text": full_text
        })

    except Exception as e:
        print(f"Error processing {file}: {e}")

print("✅ Conversion complete!")

# --- Save all text to a CSV ---
if data_list:
    df = pd.DataFrame(data_list)
    csv_path = os.path.join(txt_folder, "all_agreements.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"✅ All data saved to CSV: {csv_path}")

# -------------------------
# Step C: Clause extraction
# -------------------------
def find_clause_candidates(paragraph, taxonomy):
    matches = []
    para_lower = paragraph.lower()
    for agreement_type, clauses in taxonomy.items():
        for clause_type, keywords in clauses.items():
            for kw in keywords:
                if kw.lower() in para_lower:
                    matches.append((agreement_type, clause_type))
                    break
    return matches


def process_txt_files(clauses_raw_path, taxonomy):
    results = []
    for root, dirs, files in os.walk(clauses_raw_path):
        for file in files:
            if file.endswith(".txt") and file not in ["all_agreements.csv", "extracted_clauses_candidates.csv"]:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    text = f.read()

                # Split into paragraphs
                paragraphs = re.split(r"\n\s*\n|(?<=\.)\s+|(?<=\d\.)\s+", text)
                paragraphs = [p.strip() for p in paragraphs if p.strip()]

                if not paragraphs:
                    paragraphs = [text.strip()]

                print(f"[DEBUG] {file} → {len(paragraphs)} paragraphs found")

                for idx, para in enumerate(paragraphs):
                    matches = find_clause_candidates(para, taxonomy)
                    if matches:
                        print(f"[MATCH] {file} | Para {idx} | {matches}")
                        print(f"Text snippet: {para[:150]}...\n")
                    for agreement_type, clause_type in matches:
                        results.append({
                            "file_name": file,
                            "paragraph_index": idx,
                            "agreement_type": agreement_type,
                            "clause_type": clause_type,
                            "clause_text": para
                        })
    return results


# Run candidate extraction
results = process_txt_files(txt_folder, CLAUSE_TAXONOMY)

if results:
    df_clauses = pd.DataFrame(results)
    output_path = os.path.join(txt_folder, "extracted_clauses_candidates.csv")
    df_clauses.to_csv(output_path, index=False, encoding="utf-8")
    print(f"✅ Extracted clause candidates saved to: {output_path}")
else:
    print("⚠️ No candidate clauses found.")
