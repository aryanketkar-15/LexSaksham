# Real Data Integration - Complete Guide

## ✅ What Was Done

Your React frontend is now fully connected to the backend and uses **REAL DATA** from:
- **Legal-BERT** - Clause extraction & risk scoring
- **ShapLIME** - Explainable AI highlighting
- **Legal T5** - Clause rewriting & simplified explanations
- **Supreme Court Dataset** - Judgment retrieval & similarity matching

## 🔧 Changes Made

### 1. Created Contracts Context (`src/context/ContractsContext.jsx`)
- Manages all contracts in one place
- Saves to localStorage automatically
- Provides stats calculation
- Functions: `addContract`, `updateContract`, `deleteContract`, `getContract`, `getStats`

### 2. Updated ContractUpload Component
- ✅ Uploads PDF → Extracts text → Analyzes with Legal-BERT
- ✅ Saves real analysis results to context
- ✅ Shows real risk levels, clause counts, issues detected
- ✅ Navigates to contract details after analysis

### 3. Updated ContractList Component
- ✅ Loads real contracts from context (no more mock data)
- ✅ Shows real contract types from Legal-BERT labels
- ✅ Displays real risk levels from analysis
- ✅ Shows actual clause counts
- ✅ Delete functionality works

### 4. Updated ContractDetails Component
- ✅ Displays real contract text from PDF extraction
- ✅ Shows real clauses extracted by Legal-BERT
- ✅ Displays risk levels (Low/Medium/High/Critical)
- ✅ Shows Legal T5 summaries (`rule_summary`)
- ✅ Shows safer alternatives (`safer_alternative`)
- ✅ Includes ShapLIME explanations (`lime_explanation`)
- ✅ Can search Supreme Court judgments (for lawyers)

### 5. Updated Dashboard Component
- ✅ Shows real total contracts count
- ✅ Shows real high-risk contracts count
- ✅ Shows real clauses flagged count
- ✅ Calculates real compliance score
- ✅ Displays real contract types distribution
- ✅ Shows recent activity from actual contracts

## 📊 Backend Data Structure

When you upload a contract, the backend returns:

```javascript
{
  analysis_results: [
    {
      text: "Clause text...",
      label: "Liability",              // From Legal-BERT
      risk_level: "High",              // Risk scoring
      confidence: 95.5,                // Legal-BERT confidence
      rule_summary: "Simplified explanation...",  // From Legal T5
      safer_alternative: "Safer clause text...", // Suggested rewrite
      lime_explanation: [              // From ShapLIME
        { word: "liable", weight: 0.8 },
        { word: "damages", weight: 0.6 }
      ]
    }
  ]
}
```

## 🚀 How to Use

1. **Start Backend**:
   ```bash
   cd backend/ai_service
   python app.py
   ```

2. **Start Frontend**:
   ```bash
   cd react-frontend
   npm run dev
   ```

3. **Upload a Contract**:
   - Go to Upload page
   - Drag & drop a PDF
   - Backend extracts text → Analyzes with Legal-BERT → Returns results
   - Contract saved automatically

4. **View Analysis**:
   - Go to Contracts list → See all your contracts
   - Click a contract → See detailed analysis
   - View clauses, risk levels, explanations, suggestions

5. **Dashboard**:
   - See real stats from your contracts
   - View risk distribution
   - See contract types

## 🎯 Features Now Working

✅ **Real Clause Extraction** - Legal-BERT identifies clause types
✅ **Real Risk Scoring** - Backend calculates risk levels
✅ **Real Explanations** - Legal T5 provides simplified explanations
✅ **Real Suggestions** - Backend suggests safer alternatives
✅ **ShapLIME Highlights** - Word-level explanations available
✅ **Supreme Court Search** - Can search judgments (lawyer mode)
✅ **Data Persistence** - Contracts saved to localStorage
✅ **Real Statistics** - Dashboard shows actual data

## 📝 Notes

- All contracts are saved in browser localStorage
- Analysis happens in real-time when you upload
- Backend must be running for upload/analysis to work
- UI gracefully handles missing data
- Mock data only shows if no real contracts exist

## 🔍 Next Steps (Optional Enhancements)

1. Add ShapLIME word highlighting visualization in ContractDetails
2. Add Supreme Court judgment display panel for lawyers
3. Add export functionality for analysis results
4. Add contract comparison feature
5. Add search/filter by clause type

## 🐛 Troubleshooting

**No contracts showing?**
- Upload a contract first
- Check browser console for errors
- Verify backend is running

**Analysis not working?**
- Check backend is running on port 5000
- Check browser console for API errors
- Verify PDF is valid and readable

**Data not persisting?**
- Check browser localStorage is enabled
- Clear localStorage: `localStorage.clear()` in console


