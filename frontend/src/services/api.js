import axios from 'axios';

const API_URL = 'http://127.0.0.1:5000';

export const uploadPdf = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(`${API_URL}/upload_pdf`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const analyzeDocument = async (text) => {
  const response = await axios.post(`${API_URL}/analyze_document`, { text });
  return response.data;
};

export const searchJudgment = async (clauseText) => {
  const response = await axios.post(`${API_URL}/search_judgment`, {
    clause_text: clauseText,
    top_k: 3,
  });
  return response.data;
};

export const summarizeText = async (text) => {
  const response = await axios.post(`${API_URL}/summarize`, { text });
  return response.data;
};