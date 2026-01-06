# PDF Upload Troubleshooting Guide

## Issue: PDF Upload Does Nothing

If uploading a PDF doesn't do anything, follow these steps:

### Step 1: Check Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Try uploading a PDF
4. Look for error messages

### Step 2: Check Backend Connection
1. Make sure backend is running:
   ```bash
   cd backend/ai_service
   python app.py
   ```
2. Backend should show: `🚀 Starting LexSaksham Server on port 5000...`
3. Check if backend responds: Open `http://127.0.0.1:5000` in browser
   - Should see: `{"status": "LexSaksham Running", "faiss_active": true}`

### Step 3: Check File Requirements
- File must be PDF, DOC, or DOCX
- File size must be under 10MB
- File must be a valid document

### Step 4: Common Errors

**Error: "Cannot connect to backend"**
- Backend is not running
- Backend is on wrong port
- CORS issue (check backend has `CORS(app)`)

**Error: "No text extracted from PDF"**
- PDF might be scanned/image-based (needs OCR)
- PDF might be corrupted
- Backend PDF extraction failed

**Error: "Failed to analyze document"**
- Backend models not loaded properly
- Text is empty or too short
- Backend error (check backend console)

### Step 5: Debug Steps

1. **Check Console Logs**
   - Look for: "Files received:", "Valid files:", "Starting upload"
   - Check for any red error messages

2. **Check Network Tab**
   - Open DevTools → Network tab
   - Upload PDF
   - Look for request to `/upload_pdf`
   - Check response status and body

3. **Check Backend Logs**
   - Backend terminal should show:
     - `POST /upload_pdf 200 OK` (success)
     - Or error messages if failed

### Step 6: Test Backend Directly

Test if backend works:
```bash
curl -X POST http://127.0.0.1:5000/upload_pdf \
  -F "file=@your_file.pdf"
```

### Step 7: Check File State

After upload, check:
1. File should appear in "Uploaded Files" section
2. Progress bar should show
3. Status should change: pending → uploading → analyzed

### Quick Fixes

1. **Refresh page** (Ctrl+Shift+R)
2. **Clear browser cache**
3. **Restart backend**
4. **Check file format** (must be PDF/DOC/DOCX)
5. **Check file size** (must be < 10MB)

### Still Not Working?

Share these details:
1. Browser console errors (screenshot)
2. Network tab request/response (screenshot)
3. Backend terminal output
4. File details (name, size, type)


