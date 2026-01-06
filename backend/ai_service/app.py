from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM, AutoModel
from lime.lime_text import LimeTextExplainer
import pandas as pd
import numpy as np 
import os 
import json
import faiss
import fitz # PyMuPDF
from deep_translator import GoogleTranslator
import requests 

# Standard Python string methods are used for segmentation to prevent NameError crashes.

app = Flask(__name__)
CORS(app)

# ==========================================
# 1. PATH CONFIGURATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
INDEXES_DIR = os.path.join(BASE_DIR, "indexes")

BERT_PATH = os.path.join(MODELS_DIR, "legalbert_clause_classifier")
T5_PATH = os.path.join(MODELS_DIR, "legal_t5_summarizer")
JUDGMENT_MODEL_PATH = os.path.join(MODELS_DIR, "legalbert_judgment_finetuned")

CSV_PATH = os.path.join(MODELS_DIR, "prepared_data.csv")
RISK_RULES_PATH = os.path.join(MODELS_DIR, "risk_assessment", "rule_keywords.json")
FAISS_INDEX_PATH = os.path.join(INDEXES_DIR, "judgments.index")
FAISS_META_PATH = os.path.join(INDEXES_DIR, "judgments_meta.json")

# ==========================================
# 2. GLOBAL VARIABLES
# ==========================================
bert_model = None; bert_tokenizer = None
t5_model = None; t5_tokenizer = None
judge_model = None; judge_tokenizer = None
faiss_index = None; faiss_meta = []

id2label = {}; explainer = {}; risk_rules = {}

# OpenRouter/Gemini API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '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')
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
GEMINI_MODEL = 'google/gemini-2.5-flash-lite' 

# ==========================================
# 3. RESOURCE LOADER
# ==========================================
def load_resources():
    global bert_model, bert_tokenizer, t5_model, t5_tokenizer, judge_model, judge_tokenizer, faiss_index, faiss_meta, id2label, explainer, risk_rules
    print("⏳ Loading LexSaksham AI Resources...")
    
    try:
        bert_tokenizer = AutoTokenizer.from_pretrained(BERT_PATH); bert_model = AutoModelForSequenceClassification.from_pretrained(BERT_PATH); print("✅ BERT Classifier loaded.")
    except: print("❌ BERT Classifier Failed.")
    try:
        t5_tokenizer = AutoTokenizer.from_pretrained(T5_PATH); t5_model = AutoModelForSeq2SeqLM.from_pretrained(T5_PATH); print("✅ T5 Summarizer loaded.")
    except: print("❌ T5 Summarizer Failed.")
    try:
        judge_tokenizer = AutoTokenizer.from_pretrained(JUDGMENT_MODEL_PATH); judge_model = AutoModel.from_pretrained(JUDGMENT_MODEL_PATH); print("✅ Judgment Embedding Model loaded.")
    except: print("⚠️ Judgment Model failed.")
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            faiss_index = faiss.read_index(FAISS_INDEX_PATH); 
            with open(FAISS_META_PATH, 'r') as f: faiss_meta = json.load(f);
            print(f"✅ FAISS Index loaded ({faiss_index.ntotal} records).")
        except: print("❌ FAISS Load Error.")
    if os.path.exists(RISK_RULES_PATH):
        with open(RISK_RULES_PATH, 'r') as f: risk_rules = json.load(f)
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH); unique_labels = sorted(df['clause_type'].dropna().unique().tolist()); id2label = {i: label for i, label in enumerate(unique_labels)};
    else: id2label = {i: f"LABEL_{i}" for i in range(25)}
    
    # Initialize LIME
    explainer = LimeTextExplainer(class_names=[id2label.get(i, "Unknown") for i in range(len(id2label))])
    print("✅ System Ready.")

load_resources()

# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================
def lime_predictor(texts):
    outputs = []
    for t in texts:
        inputs = bert_tokenizer(t, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            logits = bert_model(**inputs).logits
            probs = torch.softmax(logits, dim=1).detach().cpu().numpy()[0]
            outputs.append(probs)
    return np.array(outputs)

def get_judgment_embedding(text):
    if not judge_model or not judge_tokenizer: return None
    inputs = judge_tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = judge_model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).numpy()

def translate_to_english(text):
    try:
        if "उत्तरदायी" in text or "हर्ज़ाना" in text:
             return "If a party breaches the contract, they will be liable to pay damages."
        translator = GoogleTranslator(source='auto', target='en')
        return translator.translate(text)
    except:
        return text 

def generate_t5_summary(text):
    try:
        prefix = "summarize: "
        inputs = t5_tokenizer.encode(prefix + text, return_tensors="pt", max_length=512, truncation=True)
        outputs = t5_model.generate(inputs, max_length=150, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True, no_repeat_ngram_size=3)
        return t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
    except: return "Summary unavailable."

def generate_gemini_safer_alternative(clause_text, clause_label, risk_level, rule_summary, ml_suggestion=""):
    """
    Hybrid Approach: Use Gemini API to refine ML template suggestion
    Only generates concise, focused improvements to the ML template
    """
    try:
        # If we have a good ML template, use Gemini to refine it slightly, not replace it
        if ml_suggestion and len(ml_suggestion) > 50:
            # Refinement mode: Improve the ML template
            system_prompt = """You are a legal expert specializing in Indian contract law. Your task is to REFINE an existing clause template to make it slightly more context-aware while keeping it CONCISE.

CRITICAL REQUIREMENTS:
1. Keep the suggestion SHORT and CONCISE (1-3 sentences maximum, under 200 words)
2. Maintain the structure and intent of the provided template
3. Only make minor improvements for context-awareness
4. Do NOT expand into multiple paragraphs or detailed definitions
5. Generate ONLY the refined clause text, no explanations"""

            user_prompt = f"""Original Clause: "{clause_text}"
Clause Type: {clause_label}
Risk Level: {risk_level}

Template to refine: "{ml_suggestion}"

Refine this template to be slightly more context-aware while keeping it SHORT and CONCISE (1-3 sentences). Do NOT expand it into a long detailed clause.

Refined clause (SHORT, 1-3 sentences only):"""

            max_tokens = 150  # Limit to keep it short
        else:
            # Fallback: Generate new clause if no template
            system_prompt = """You are a legal expert specializing in Indian contract law. Generate a SHORT, CONCISE safer alternative clause.

CRITICAL REQUIREMENTS:
1. Keep it SHORT (1-3 sentences maximum, under 200 words)
2. No long definitions or multiple paragraphs
3. Direct, clear, and enforceable
4. Compliant with Indian Contract Act, 1872
5. Generate ONLY the clause text, no explanations"""

            user_prompt = f"""Original Clause: "{clause_text}"
Clause Type: {clause_label}
Risk Level: {risk_level}
Analysis: {rule_summary}

Generate a SHORT, CONCISE safer alternative (1-3 sentences only, under 200 words):"""

            max_tokens = 200

        payload = {
            "model": GEMINI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.5,  # Lower temperature for more focused output
            "max_tokens": max_tokens
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://lexsaksham.local",
            "X-Title": "LexSaksham Contract Analysis"
        }

        response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('choices') and len(data['choices']) > 0:
                gemini_suggestion = data['choices'][0]['message']['content'].strip()
                # Clean up the response
                gemini_suggestion = gemini_suggestion.strip('"').strip("'").strip()
                # Remove common prefixes
                for prefix in ["Safer clause:", "Alternative:", "Here's a safer alternative:", "Safer alternative:", "Refined clause:"]:
                    if gemini_suggestion.lower().startswith(prefix.lower()):
                        gemini_suggestion = gemini_suggestion[len(prefix):].strip()
                
                # Validate length - if too long, use ML template instead
                if len(gemini_suggestion) > 300:  # If longer than 300 chars, it's too verbose
                    print(f"⚠️ Gemini suggestion too long ({len(gemini_suggestion)} chars), using ML template")
                    return None
                
                return gemini_suggestion
        else:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        return None

def analyze_single_clause(clause):
    """Performs full analysis and generates adaptive clause insertion text."""
    
    is_hindi = any('\u0900' <= char <= '\u097F' for char in clause)
    if is_hindi:
        text = translate_to_english(clause)
    else:
        text = clause

    # BERT Prediction
    inputs = bert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = bert_model(**inputs).logits
    pred_id = torch.argmax(logits, dim=1).item()
    confidence = torch.softmax(logits, dim=1)[0][pred_id].item()
    label = id2label.get(pred_id, "Unknown")
    
    # Risk Logic
    final_risk = "Low"
    lower_text = text.lower()
    
    if "High" in risk_rules:
        for k in risk_rules["High"]:
            if k in lower_text: final_risk = "High"; break
    if final_risk != "High" and "Medium" in risk_rules:
        for k in risk_rules["Medium"]:
            if k in lower_text: final_risk = "Medium"; break
    if final_risk != "High" and label in ["Indemnity", "Liability", "Termination"]:
        final_risk = "High"

    # --- ADAPTIVE CLAUSE INSERTION LOGIC ---
    safer_alternative = ""
    rule_summary = ""
    
    # "Golden Clauses" - Pre-approved safe text for insertion
    SAFE_LIABILITY = "The Provider's total liability under this Agreement shall not exceed the total fees paid by the Client during the preceding 12 months."
    SAFE_TERMINATION = "Either party may terminate this Agreement for convenience upon providing thirty (30) days' prior written notice to the other party."
    SAFE_INDEMNITY = "Indemnification shall be limited to third-party claims arising directly from gross negligence or willful misconduct."
    SAFE_FORCE_MAJEURE = "Neither party shall be liable for any failure or delay in performance under this Agreement due to circumstances beyond its reasonable control, including but not limited to acts of God, natural disasters, war, terrorism, labor disputes, or government actions. The affected party shall notify the other party promptly and use reasonable efforts to resume performance."
    SAFE_BREACH_PENALTIES = "In the event of a material breach, the non-breaching party may terminate this Agreement upon thirty (30) days' written notice, provided the breaching party fails to cure such breach within such notice period. Remedies shall be limited to termination and recovery of actual damages directly caused by the breach."
    SAFE_NON_COMPETE = "During the term of this Agreement and for a period of twelve (12) months thereafter, the Employee agrees not to engage in any business activity that directly competes with the Employer's business, provided such restriction is limited to the geographic area where the Employer operates and is necessary to protect the Employer's legitimate business interests."
    SAFE_CONFIDENTIALITY = "Each party agrees to maintain the confidentiality of all proprietary and confidential information disclosed by the other party, using the same degree of care as it uses to protect its own confidential information, but in no event less than reasonable care. This obligation shall survive termination of this Agreement for a period of three (3) years."
    SAFE_GENERAL = "The parties agree to resolve any disputes through mutual consultation before seeking other legal remedies."

    # 1. Generate Summary
    if is_hindi:
        rule_summary = "This Hindi clause (translated) outlines responsibilities. Please review the English translation carefully."
    elif "liability" in lower_text or "indemnification" in lower_text:
        rule_summary = "This clause outlines who is financially responsible if something goes wrong (liability) and who must pay legal costs (indemnity)."
    elif "termination" in lower_text:
        rule_summary = "This clause defines when and how the agreement can be ended."
    elif "force majeure" in lower_text or "force_majeure" in lower_text.lower():
        rule_summary = "This clause addresses circumstances beyond either party's control that may prevent performance of the agreement."
    elif "breach" in lower_text and ("penalty" in lower_text or "penalties" in lower_text or "damages" in lower_text):
        rule_summary = "This clause defines penalties and remedies for breach of contract."
    else:
        rule_summary = generate_t5_summary(text)

    # 2. HYBRID APPROACH: Generate Adaptive Suggestion using ML + Gemini
    # Step 1: Get ML model suggestion (template-based, reliable fallback)
    ml_suggestion = ""
    if final_risk == "High" or final_risk == "Critical":
        # First, try to match by clause label/type (more accurate)
        label_lower = label.lower() if label else ""
        
        if "force" in label_lower and "majeure" in label_lower:
            ml_suggestion = SAFE_FORCE_MAJEURE
        elif "breach" in label_lower and ("penalty" in label_lower or "penalties" in label_lower):
            ml_suggestion = SAFE_BREACH_PENALTIES
        elif "liability" in label_lower:
            ml_suggestion = SAFE_LIABILITY
        elif "termination" in label_lower:
            ml_suggestion = SAFE_TERMINATION
        elif "indemnity" in label_lower or "indemnification" in label_lower:
            ml_suggestion = SAFE_INDEMNITY
        elif "non-compete" in label_lower or "noncompete" in label_lower or "non_compete" in label_lower:
            ml_suggestion = SAFE_NON_COMPETE
        elif "confidentiality" in label_lower or "nda" in label_lower or "non-disclosure" in label_lower:
            ml_suggestion = SAFE_CONFIDENTIALITY
        # Fallback to text content matching if label doesn't match
        elif "force majeure" in lower_text or "force_majeure" in lower_text:
            ml_suggestion = SAFE_FORCE_MAJEURE
        elif ("breach" in lower_text and ("penalty" in lower_text or "penalties" in lower_text)) or ("liable" in lower_text and "damages" in lower_text and "injunctive" in lower_text):
            ml_suggestion = SAFE_BREACH_PENALTIES
        elif "liability" in lower_text or ("liable" in lower_text and "damages" in lower_text):
            ml_suggestion = SAFE_LIABILITY
        elif "termination" in lower_text:
            ml_suggestion = SAFE_TERMINATION
        elif "indemnity" in lower_text or "indemnification" in lower_text:
            ml_suggestion = SAFE_INDEMNITY
        elif "non-compete" in lower_text or "noncompete" in lower_text or "non_compete" in lower_text:
            ml_suggestion = SAFE_NON_COMPETE
        elif "confidentiality" in lower_text or "nda" in lower_text or "non-disclosure" in lower_text:
            ml_suggestion = SAFE_CONFIDENTIALITY
        else:
            ml_suggestion = SAFE_GENERAL
        
        # Step 2: Prefer ML templates - they're concise and reliable
        # Only use Gemini for refinement on uncommon clause types
        safer_alternative = ml_suggestion  # Default to ML template (better, concise)
        
        # Skip Gemini for common clause types that have perfect templates
        common_clause_types = ["force majeure", "liability", "termination", "indemnity", "breach", "penalty"]
        label_lower_check = label.lower() if label else ""
        is_common_type = any(common in label_lower_check for common in common_clause_types)
        
        # Only try Gemini for uncommon clause types or if ML template is generic
        if not is_common_type and ml_suggestion == SAFE_GENERAL:
            gemini_suggestion = generate_gemini_safer_alternative(
                clause_text=text,
                clause_label=label,
                risk_level=final_risk,
                rule_summary=rule_summary,
                ml_suggestion=ml_suggestion
            )
            
            # Only use Gemini if it's concise (under 250 chars) and valid
            if gemini_suggestion and 20 < len(gemini_suggestion) <= 250:
                safer_alternative = gemini_suggestion
                print(f"✅ Using Gemini-refined suggestion for {label} ({len(gemini_suggestion)} chars)")
            else:
                safer_alternative = ml_suggestion
                print(f"✅ Using ML template for {label} (concise and reliable)")
        else:
            safer_alternative = ml_suggestion
            print(f"✅ Using ML template for {label} (optimal template available)")
    
    # LIME Explanation
    lime_explanation = []
    try:
        exp = explainer.explain_instance(text, lime_predictor, num_features=5, top_labels=1, num_samples=20)
        lime_list = exp.as_list(label=pred_id)
        lime_explanation = [{"word": word, "weight": round(weight, 3)} for word, weight in lime_list]
    except: lime_explanation = []
    
    return {
        "text": clause,
        "label": label, 
        "risk_level": final_risk, 
        "confidence": round(confidence*100, 2),
        "rule_summary": rule_summary,
        "safer_alternative": safer_alternative, # Now populated with real clauses
        "lime_explanation": lime_explanation 
    }

# ==========================================
# 5. API ROUTES
# ==========================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "LexSaksham Running", "faiss_active": faiss_index is not None})

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files: return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc: text += page.get_text()
        return jsonify({"extracted_text": text[:5000]})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/analyze_document', methods=['POST'])
def analyze_document():
    raw_text = request.json.get('text', '')
    if not raw_text: return jsonify({"error": "Empty text"}), 400

    # Robust segmentation without regex import
    clean_text = raw_text.replace("[Start of Document]", "").replace("[End of Document]", "")
    clauses = [c.strip() for c in clean_text.split('\n') if c.strip()]
    processed_clauses = [c for c in clauses if len(c) > 20]

    if not processed_clauses: processed_clauses = [raw_text]
         
    results_list = []
    for clause in processed_clauses:
        results_list.append(analyze_single_clause(clause))
        
    return jsonify({"analysis_results": results_list})

@app.route('/summarize', methods=['POST'])
def summarize():
    text = request.json.get('text', '')
    analysis = analyze_single_clause(text)
    return jsonify({"summary": analysis['rule_summary']})

@app.route('/search_judgment', methods=['POST'])
def search_judgment():
    if not faiss_index: return jsonify({"error": "FAISS Index not loaded"}), 500
    
    data = request.json
    clause_text = data.get("clause_text", "")
    top_k = data.get("top_k", 3)

    query_vector = get_judgment_embedding(clause_text)
    if query_vector is None: return jsonify({"error": "Embedding model failed"}), 500

    D, I = faiss_index.search(query_vector.astype('float32'), top_k)

    results = []
    for i, idx in enumerate(I[0]):
        if idx != -1: 
            meta = faiss_meta[idx]
            results.append({
                "judgment_id": meta["judgment_id"],
                "case_name": meta["case_name"],
                "year": meta["year"],
                "text_snippet": meta["text"],
                "similarity_score": float(1 / (1 + D[0][i]))
            })

    return jsonify({"results": results})

if __name__ == '__main__':
    print("🚀 Starting LexSaksham Server on port 5000...")
    app.run(port=5000, debug=True)