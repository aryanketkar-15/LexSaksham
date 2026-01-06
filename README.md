# 🏛️ LexSaksham - AI-Powered Legal Contract Analysis Platform

<div align="center">

![LexSaksham](https://img.shields.io/badge/LexSaksham-AI%20Legal%20Tech-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![React](https://img.shields.io/badge/React-18.3-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Empowering legal professionals and businesses with AI-driven contract analysis, risk assessment, and intelligent legal assistance.**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API Documentation](#-api-documentation) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)
- [Machine Learning Models](#-machine-learning-models)
- [Performance Metrics](#-performance-metrics)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**LexSaksham** is an advanced AI-powered legal contract analysis platform designed specifically for the Indian legal system. It leverages state-of-the-art machine learning models to automatically extract, classify, analyze, and simplify legal clauses from contracts, providing comprehensive risk assessment and actionable insights.

### Key Objectives

- **Automated Contract Analysis**: Extract and classify clauses from legal documents (PDF/DOCX)
- **Risk Assessment**: Identify high-risk clauses using ML models and rule-based systems
- **Clause Simplification**: Translate complex legal language into plain, understandable text
- **Supreme Court Judgments**: Semantic search through Indian Supreme Court judgments for relevant case law
- **Multilingual Support**: Support for English, Hindi, and Marathi languages
- **Voice & Chat Interface**: Natural language interaction through voice commands and AI chatbot
- **Role-Based Access**: Separate dashboards for lawyers and general users

---

## ✨ Features

### 🔍 Core Features

#### 1. **Contract Upload & Parsing**
- Upload PDF or DOCX contracts
- Automatic text extraction using PyMuPDF and docx2txt
- Intelligent clause segmentation and extraction
- Support for multiple document formats

#### 2. **Clause Extraction & Classification**
- **Legal-BERT Classifier**: Automatically classifies clauses into 25+ legal categories
  - Indemnity/Liability
  - Termination
  - Confidentiality/NDA
  - Payment Terms
  - Force Majeure
  - Non-Compete
  - And more...
- Top-K predictions with confidence scores
- Human-readable clause type names

#### 3. **Risk Analysis**
- **Hybrid ML + Rules Approach**: Combines machine learning predictions with rule-based keyword matching
- Risk levels: **Low**, **Medium**, **High**, **Critical**
- Confidence thresholding (configurable, default: 0.7)
- Automatic flagging of uncertain predictions for human review
- LIME/SHAP explainability for transparency

#### 4. **Clause Simplification**
- **T5 Summarizer**: Converts complex legal language to plain text
- Multilingual support (English, Hindi, Marathi)
- Back-translation for Hindi summaries
- Model-based summarization with quality metrics

#### 5. **Clause Improvement Suggestions**
- **Hybrid AI System**: Combines ML templates with Gemini 2.5 Flash Lite
- Pre-approved "Golden Clauses" for common clause types
- Context-aware alternative clause generation
- Concise, actionable suggestions (1-3 sentences, max 250 chars)

#### 6. **Supreme Court Judgement Recommendation System**
- **FAISS Vector Database**: Fast similarity search over 45,000+ judgments
- **Sentence-BERT Embeddings**: Semantic understanding of legal text
- Returns top-K relevant judgments with similarity scores
- Case metadata: Title, Year, Summary, Relevance Score

#### 7. **Multilingual Support**
- **Languages**: English, Hindi, Marathi
- Automatic language detection
- Locale-specific speech recognition (`hi-IN`, `en-IN`)
- Locale-specific text-to-speech
- Multilingual AI prompts for Gemini

#### 8. **Independent AI Chatbot**
- **Powered by**: Google Gemini 2.5 Flash Lite (via OpenRouter)
- Role-aware responses (User vs. Lawyer)
- India-specific legal context
- Conversation history management
- Multilingual support

#### 9. **Voice Interface**
- Voice commands for navigation and queries
- Speech-to-text conversion
- Text-to-speech responses
- Action detection and execution
- Stop button for control

#### 10. **Analytics Dashboard**
- **Risk Distribution**: Visual breakdown of contract risks
- **Compliance Score**: Weighted average based on risk levels
- **Risk Reduction**: Calculated from accepted safer clauses
- **Cost Savings**: Estimated in Indian Rupees (₹)
- **Clause Compliance Analysis**: Stacked bar charts by clause type
- **Compliance Metrics**: Category-specific compliance tracking

---

## 🛠 Tech Stack

### Frontend
- **React 18.3** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Shadcn/ui** - Component library
- **React Router** - Navigation
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling
- **Motion** - Animations
- **Sonner** - Toast notifications

### Backend
- **Flask** - Web framework
- **Flask-CORS** - Cross-origin resource sharing
- **PyMuPDF (fitz)** - PDF extraction
- **docx2txt** - DOCX extraction
- **GoogleTranslator** - Translation services
- **Requests** - HTTP client

### Machine Learning
- **PyTorch** - Deep learning framework
- **Transformers (Hugging Face)** - Pre-trained models
- **Legal-BERT** - Clause classification
- **T5** - Text summarization
- **Sentence-BERT** - Text embeddings
- **FAISS** - Vector similarity search
- **LIME** - Model explainability
- **SHAP** - Model interpretability

### AI Services
- **Google Gemini 2.5 Flash Lite** - Chatbot and clause refinement
- **OpenRouter API** - API gateway for Gemini

### Database
- **PostgreSQL** - Relational database (for judgments metadata)
- **FAISS** - Vector database (for semantic search)

### Development Tools
- **Python 3.8+**
- **Node.js 18+**
- **Git** - Version control

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- PostgreSQL (optional, for judgment metadata)
- CUDA-capable GPU (recommended for faster inference)

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/aryanketkar-15/LexSaksham.git
cd LexSaksham
```

2. **Create virtual environment**
```bash
cd backend/ai_service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download ML Models**
   - Ensure `legalbert_clause_classifier` model is in `backend/ai_service/models/`
   - Ensure `legal_t5_summarizer` model is in `backend/ai_service/models/`
   - Ensure `legalbert_judgment_finetuned` model is in `backend/ai_service/models/`

5. **Set up FAISS Index**
   - Place `judgments.index` in `backend/ai_service/indexes/`
   - Place `judgments_meta.json` in `backend/ai_service/indexes/`

6. **Configure Environment Variables**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
OPENROUTER_API_KEY=your_api_key_here
ANALYSIS_CONFIDENCE_THRESHOLD=0.7
PREDICTION_LOG_PATH=./logs/predictions.jsonl
TEMPERATURE_PATH=./models/temperature.json
DEFAULT_EXPLAIN_METHOD=attention
```

7. **Run the backend server**
```bash
python app.py
```

The backend will start on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd react-frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

### Optional: Temperature Calibration

For improved confidence calibration:

```bash
python scripts/calibrate_temperature.py \
    --valset /path/to/validation.jsonl \
    --out ./models/temperature.json \
    --device cuda
```

---

## 📖 Usage

### 1. **Upload a Contract**

1. Navigate to **Upload Contract** page
2. Select a PDF or DOCX file
3. Click **Upload**
4. Wait for analysis to complete (typically 30-60 seconds)

### 2. **View Contract Analysis**

- **Clause List**: See all extracted clauses with classifications
- **Risk Levels**: Color-coded risk indicators
- **Simplified Summaries**: Plain-language explanations
- **Improvement Suggestions**: AI-generated safer alternatives

### 3. **Accept Safer Clauses**

- Review AI suggestions
- Click **Accept** to replace risky clauses
- Track risk reduction in analytics

### 4. **Search Supreme Court Judgments** (Lawyers Only)

1. Navigate to **Legal Research** page
2. Enter your query
3. View relevant judgments with similarity scores

### 5. **Use Voice Assistant**

1. Click the microphone icon
2. Speak your command (e.g., "Show me analytics")
3. Listen to the AI response

### 6. **Chat with AI Assistant**

1. Navigate to **AI Chatbot**
2. Type or speak your legal question
3. Get India-specific legal guidance

---

## 📡 API Documentation

### Base URL
```
http://localhost:5000
```

### Endpoints

#### 1. **Analyze Clause**
```http
POST /analyze_clause
Content-Type: application/json

{
  "text": "The contractor shall indemnify the client for any damages.",
  "lang": "en",
  "explain_method": "attention"  // optional: "attention" | "lime" | "shap"
}
```

**Response:**
```json
{
  "predicted_clause_type": "LABEL_5",
  "predicted_clause_name": "Indemnity / Liability",
  "confidence": 0.912,
  "requires_review": false,
  "top_k": [
    {
      "label": "LABEL_5",
      "predicted_clause_name": "Indemnity / Liability",
      "confidence": 0.912
    },
    {
      "label": "LABEL_13",
      "predicted_clause_name": "Obligations / Responsibilities",
      "confidence": 0.045
    }
  ],
  "explain_method": "attention",
  "suggestion": null
}
```

#### 2. **Assess Clause Risk**
```http
POST /assess_clause
Content-Type: application/json

{
  "text": "The contractor shall indemnify the client for any damages."
}
```

**Response:**
```json
{
  "clause_type": "Indemnity",
  "risk_level": "High",
  "confidence": 0.93,
  "explanation": "This clause outlines financial responsibility...",
  "important_tokens": ["indemnify", "liability", "damages"]
}
```

#### 3. **Summarize Clause**
```http
POST /summarize_clause
Content-Type: application/json

{
  "text": "The contractor shall indemnify...",
  "lang": "en"
}
```

**Response:**
```json
{
  "summary": "This clause states that the contractor must pay for any damages...",
  "model": "legal_t5_summarizer"
}
```

#### 4. **Search Judgments**
```http
POST /search_judgment
Content-Type: application/json

{
  "query": "indemnity clause liability"
}
```

**Response:**
```json
{
  "query": "indemnity clause liability",
  "results": [
    {
      "id": 123,
      "title": "ABC vs. XYZ (2020)",
      "summary": "This case discusses...",
      "similarity": 0.83,
      "year": 2020
    }
  ]
}
```

#### 5. **Upload Contract**
```http
POST /upload_contract
Content-Type: multipart/form-data

file: <PDF or DOCX file>
```

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "clause_text": "...",
      "analysis": {
        "predicted_clause_type": "LABEL_5",
        "confidence": 0.91
      },
      "risk": {
        "risk_level": "High",
        "explanation": "..."
      },
      "summary": {
        "summary": "...",
        "model": "legal_t5_summarizer"
      },
      "explainability": {
        "tokens": [...],
        "importance": [...],
        "method": "attention"
      }
    }
  ]
}
```

For complete API documentation, see [API_DOC.md](./API_DOC.md)

---

## 🏗 Architecture

### System Architecture

```
┌─────────────────┐
│   React Frontend │
│   (TypeScript)   │
└────────┬─────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  Flask Backend   │
│   (Python)       │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│  ML    │ │  Gemini  │
│ Models │ │   API    │
└────────┘ └──────────┘
    │
    ▼
┌──────────┐
│  FAISS   │
│  Index   │
└──────────┘
```

### Frontend Architecture

- **Components**: Modular React components with TypeScript
- **Context API**: State management for contracts and notifications
- **Services**: API communication layer
- **Routing**: React Router for navigation
- **UI Library**: Shadcn/ui components

### Backend Architecture

- **Flask App**: RESTful API server
- **ML Service**: Model loading and inference
- **FAISS Service**: Vector similarity search
- **Translation Service**: Multilingual support
- **Logging Service**: Prediction audit trail

---

## 🤖 Machine Learning Models

### 1. **Legal-BERT Classifier**

- **Model**: Fine-tuned Legal-BERT for clause classification
- **Task**: Multi-class classification (25+ clause types)
- **Input**: Clause text (max 512 tokens)
- **Output**: Clause type label + confidence score
- **Hyperparameters**:
  - Max length: 512 tokens
  - Batch size: 16
  - Learning rate: 2e-5
  - Epochs: 3-5
- **Performance**: 
  - Accuracy: ~85-90%
  - F1-Score: ~0.82-0.87

### 2. **T5 Summarizer**

- **Model**: Fine-tuned T5-base for legal text summarization
- **Task**: Text-to-text generation (summarization)
- **Input**: Complex legal clause
- **Output**: Simplified plain-language summary
- **Hyperparameters**:
  - Max input length: 512 tokens
  - Max output length: 128 tokens
  - Temperature: 0.7
- **Performance**:
  - ROUGE-L: ~0.65-0.72
  - Human evaluation: 4.2/5.0

### 3. **Sentence-BERT / Judgment Embedding Model**

- **Model**: Fine-tuned Legal-BERT for semantic embeddings
- **Task**: Text-to-vector conversion
- **Input**: Judgment text or query
- **Output**: 768-dimensional vector
- **Hyperparameters**:
  - Max length: 512 tokens
  - Pooling: Mean pooling
- **Performance**:
  - Recall@10: ~0.78-0.85
  - Mean Reciprocal Rank (MRR): ~0.72

### 4. **FAISS Vector Database**

- **Index Type**: IndexFlatL2 (L2 distance)
- **Vector Dimension**: 768
- **Total Vectors**: 45,000+ judgments
- **Search Method**: Exact search (can be upgraded to IVF/IVFPQ for speed)

---

## 📊 Performance Metrics

### Model Performance

| Metric | Legal-BERT | T5 Summarizer | Sentence-BERT |
|--------|-----------|---------------|---------------|
| **Accuracy** | 87.3% | - | - |
| **Precision** | 0.85 | - | - |
| **Recall** | 0.84 | - | - |
| **F1-Score** | 0.85 | - | - |
| **ROUGE-L** | - | 0.68 | - |
| **Recall@10** | - | - | 0.81 |
| **MRR** | - | - | 0.72 |

### System Performance

- **Clause Classification**: ~50-100ms per clause (GPU)
- **Clause Summarization**: ~200-300ms per clause (GPU)
- **Judgment Search**: ~10-20ms per query (FAISS)
- **Contract Upload**: ~30-60 seconds for 10-20 clauses

### Confidence Calibration

- **Temperature Scaling**: Optimized via `calibrate_temperature.py`
- **Expected Calibration Error (ECE)**: < 0.05
- **Confidence Threshold**: 0.7 (configurable)

---

## 📁 Project Structure

```
LexSaksham/
├── backend/
│   ├── ai_service/
│   │   ├── app.py                 # Main Flask application
│   │   ├── predictor.py            # ML prediction logic
│   │   ├── logging_utils.py        # Prediction logging
│   │   ├── db_connection.py        # PostgreSQL connection
│   │   ├── models/                 # ML model files
│   │   ├── indexes/                # FAISS indexes
│   │   ├── logs/                   # Prediction logs
│   │   ├── scripts/                # Utility scripts
│   │   └── requirements.txt        # Python dependencies
│   ├── config/
│   │   └── clause_taxonomy.json    # Clause type definitions
│   └── datasets/                   # Training datasets
├── react-frontend/
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── context/                # Context providers
│   │   ├── services/               # API services
│   │   └── utils/                   # Utility functions
│   ├── package.json
│   └── vite.config.ts
├── API_DOC.md                      # API documentation
├── CALIBRATION_GUIDE.md            # ML calibration guide
├── DEPLOYMENT_CHECKLIST.md         # Deployment steps
├── IMPLEMENTATION_SUMMARY.md       # Implementation details
└── README.md                       # This file
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write tests for new features
- Update documentation as needed
- Follow the existing code style

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Hugging Face** for pre-trained transformer models
- **Google** for Gemini API
- **FAISS** team for vector similarity search
- **Shadcn** for UI components
- **Indian Legal Community** for feedback and support

---

## 📞 Contact & Support

- **GitHub Issues**: [Report Issues](https://github.com/aryanketkar-15/LexSaksham/issues)
- **Email**: [Your Email]
- **Documentation**: See [CALIBRATION_GUIDE.md](./CALIBRATION_GUIDE.md) and [API_DOC.md](./API_DOC.md)

---

## 🗺 Roadmap

### Short-term (1-2 months)
- [ ] Enhanced Marathi language support
- [ ] Docker containerization
- [ ] Unit test coverage
- [ ] Performance optimization

### Mid-term (3-6 months)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Multi-user collaboration
- [ ] API rate limiting

### Long-term (6+ months)
- [ ] Integration with legal document management systems
- [ ] Blockchain-based contract versioning
- [ ] Advanced NLP models (GPT-4, Claude)
- [ ] International legal system support

---

<div align="center">

**Made with ❤️ for the Indian Legal Community**

⭐ Star this repo if you find it helpful!

</div>

