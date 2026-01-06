# Backend Connection Guide

This guide explains how the React Frontend connects to the Python Backend.

## Architecture Overview

- **Backend**: Python Flask server running on `http://127.0.0.1:5000`
- **Frontend**: React app running on `http://localhost:3000` (or port specified in vite.config.ts)

## API Service

The API service is located at `src/services/api.js` and provides the following functions:

### Available Functions

1. **`checkBackendConnection()`**
   - Checks if backend is running
   - Returns: `{ connected: boolean, status: string, faiss_active: boolean }`

2. **`uploadPDF(file)`**
   - Uploads a PDF file to extract text
   - Returns: `{ success: boolean, extracted_text: string }`

3. **`analyzeDocument(text, userMode)`**
   - Analyzes contract text using Legal-BERT and T5 models
   - Parameters:
     - `text`: Contract text to analyze
     - `userMode`: 'user' or 'lawyer' (default: 'user')
   - Returns: `{ success: boolean, analysis_results: Array }`

4. **`summarizeClause(text)`**
   - Summarizes a clause using T5 model
   - Returns: `{ success: boolean, summary: string }`

5. **`searchJudgment(clauseText, topK)`**
   - Searches for similar Supreme Court judgments
   - Parameters:
     - `clauseText`: Text to search for
     - `topK`: Number of results (default: 3)
   - Returns: `{ success: boolean, results: Array }`

6. **`uploadAndAnalyze(file, userMode)`**
   - Complete workflow: Upload PDF → Extract Text → Analyze
   - Returns: `{ success: boolean, extracted_text: string, analysis_results: Array }`

## Backend Endpoints

The backend (`backend/ai_service/app.py`) provides these endpoints:

- `GET /` - Health check
- `POST /upload_pdf` - Upload and extract text from PDF
- `POST /analyze_document` - Analyze contract text
- `POST /summarize` - Summarize clause text
- `POST /search_judgment` - Search Supreme Court judgments

## Usage Example

```javascript
import { uploadAndAnalyze, searchJudgment } from './services/api';

// Upload and analyze a contract
const file = document.querySelector('input[type="file"]').files[0];
const result = await uploadAndAnalyze(file, 'user');

// Search for judgments
const judgments = await searchJudgment('termination clause', 5);
```

## Environment Variables

You can set the backend URL using environment variables:

Create a `.env` file in the `react-frontend` folder:

```env
VITE_API_BASE_URL=http://127.0.0.1:5000
```

## Running the Application

1. **Start Backend** (Terminal 1):
   ```bash
   cd backend/ai_service
   python app.py
   ```
   Backend will run on `http://127.0.0.1:5000`

2. **Start Frontend** (Terminal 2):
   ```bash
   cd react-frontend
   npm install  # First time only
   npm run dev
   ```
   Frontend will run on `http://localhost:3000` (or port in vite.config.ts)

## CORS Configuration

The backend has CORS enabled (`CORS(app)` in `app.py`), which allows the frontend to make requests.

If you see CORS errors:
- Make sure backend is running
- Check that `CORS(app)` is enabled in `app.py`
- Verify backend URL matches `VITE_API_BASE_URL`

## Components Using API

- **ContractUpload**: Uses `uploadAndAnalyze()` to upload and analyze contracts
- **ContractDetails**: Uses `analyzeDocument()` and `searchJudgment()` for analysis
- **Dashboard**: Can use `checkBackendConnection()` to show backend status

## Error Handling

All API functions throw errors that should be caught:

```javascript
try {
  const result = await uploadAndAnalyze(file);
  // Handle success
} catch (error) {
  console.error('API Error:', error.message);
  // Show error to user
}
```

## Testing Backend Connection

You can test the connection in the browser console:

```javascript
import { checkBackendConnection } from './services/api';
checkBackendConnection().then(console.log);
```

Expected output when connected:
```javascript
{
  connected: true,
  status: "LexSaksham Running",
  faiss_active: true
}
```


