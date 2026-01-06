/**
 * API Service for LexSaksham Backend
 * Connects to backend at http://127.0.0.1:5000
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

/**
 * Check if backend is connected
 */
export const checkBackendConnection = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/`);
    const data = await response.json();
    return { connected: true, status: data.status, faiss_active: data.faiss_active };
  } catch (error) {
    return { connected: false, error: error.message };
  }
};

/**
 * Upload PDF file and extract text
 */
export const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  console.log('Uploading PDF to:', `${API_BASE_URL}/upload_pdf`);
  console.log('File details:', { name: file.name, size: file.size, type: file.type });

  try {
    const response = await fetch(`${API_BASE_URL}/upload_pdf`, {
      method: 'POST',
      body: formData,
    });

    console.log('Upload response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}: ${response.statusText}` }));
      console.error('Upload error:', errorData);
      throw new Error(errorData.error || `Failed to upload PDF: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Upload success, extracted text length:', data.extracted_text?.length || 0);
    return { success: true, extracted_text: data.extracted_text };
  } catch (error) {
    console.error('Upload PDF error:', error);
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      throw new Error('Cannot connect to backend. Make sure the backend server is running on http://127.0.0.1:5000');
    }
    throw new Error(error.message || 'Failed to upload PDF');
  }
};

/**
 * Analyze document text
 * @param {string} text - The contract text to analyze
 * @param {string} userMode - 'user' or 'lawyer'
 * @param {AbortSignal} signal - Optional abort signal for cancellation
 */
export const analyzeDocument = async (text, userMode = 'user', signal = null) => {
  console.log('Analyzing document, text length:', text?.length || 0);
  
  // Create timeout controller (10 minutes for large documents)
  const timeoutMs = 10 * 60 * 1000; // 10 minutes
  const timeoutController = new AbortController();
  let timeoutId = null;

  // Set up timeout
  timeoutId = setTimeout(() => {
    timeoutController.abort();
  }, timeoutMs);

  // Use provided signal or timeout signal
  const abortSignal = signal || timeoutController.signal;

  try {
    const response = await fetch(`${API_BASE_URL}/analyze_document`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, userMode }),
      signal: abortSignal,
    });

    if (timeoutId) clearTimeout(timeoutId);
    console.log('Analysis response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}: ${response.statusText}` }));
      console.error('Analysis error:', errorData);
      throw new Error(errorData.error || `Failed to analyze document: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Analysis success, results count:', data.analysis_results?.length || 0);
    return { success: true, analysis_results: data.analysis_results };
  } catch (error) {
    if (timeoutId) clearTimeout(timeoutId);
    console.error('Analyze document error:', error);
    
    if (error.name === 'AbortError') {
      if (timeoutController.signal.aborted) {
        throw new Error('Analysis timed out after 10 minutes. The document may be too large. Please try with a smaller document or contact support.');
      }
      throw new Error('Analysis was cancelled.');
    }
    
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      throw new Error('Cannot connect to backend. Make sure the backend server is running on http://127.0.0.1:5000');
    }
    throw new Error(error.message || 'Failed to analyze document');
  }
};

/**
 * Summarize clause text
 */
export const summarizeClause = async (text) => {
  try {
    const response = await fetch(`${API_BASE_URL}/summarize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to summarize clause');
    }

    const data = await response.json();
    return { success: true, summary: data.summary };
  } catch (error) {
    throw new Error(error.message || 'Failed to summarize clause');
  }
};

/**
 * Search for similar Supreme Court judgments
 * @param {string} clauseText - The clause text to search for
 * @param {number} topK - Number of results to return (default: 3)
 */
export const searchJudgment = async (clauseText, topK = 3) => {
  try {
    const response = await fetch(`${API_BASE_URL}/search_judgment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ clause_text: clauseText, top_k: topK }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to search judgments');
    }

    const data = await response.json();
    return { success: true, results: data.results || [] };
  } catch (error) {
    throw new Error(error.message || 'Failed to search judgments');
  }
};

/**
 * Complete workflow: Upload PDF -> Extract Text -> Analyze
 * @param {File} file - The PDF file to upload
 * @param {string} userMode - 'user' or 'lawyer'
 * @param {AbortSignal} signal - Optional abort signal for cancellation
 */
export const uploadAndAnalyze = async (file, userMode = 'user', signal = null) => {
  try {
    // Step 1: Upload PDF and extract text
    const uploadResult = await uploadPDF(file);
    
    if (!uploadResult.extracted_text) {
      throw new Error('No text extracted from PDF');
    }

    // Step 2: Analyze the extracted text (with timeout handling)
    const analysisResult = await analyzeDocument(uploadResult.extracted_text, userMode, signal);

    return {
      success: true,
      extracted_text: uploadResult.extracted_text,
      analysis_results: analysisResult.analysis_results,
    };
  } catch (error) {
    throw new Error(error.message || 'Failed to upload and analyze document');
  }
};

export default {
  checkBackendConnection,
  uploadPDF,
  analyzeDocument,
  summarizeClause,
  searchJudgment,
  uploadAndAnalyze,
};

