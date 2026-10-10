import React, { useState, useEffect } from 'react';
import axios from 'axios';

// --- CONFIGURATION ---
const API_URL = 'http://127.0.0.1:5000';

// --- VOICE INPUT HOOK ---
const useSpeechRecognition = () => {
  const [text, setText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState(null);

  let recognition = null;

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.lang = 'en-US'; 
      recognition.interimResults = false;
  }

  const startListening = () => {
    setText('');
    setIsListening(true);
    setError(null);
    if (recognition) {
        recognition.start();
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            setText(transcript);
            setIsListening(false);
        };
        recognition.onerror = (event) => {
            setError('Speech recognition error: ' + event.error);
            setIsListening(false);
        };
        recognition.onend = () => {
            setIsListening(false);
        };
    } else {
        setError("Browser does not support Speech Recognition.");
        setIsListening(false);
    }
  };

  const stopListening = () => {
      if (recognition) {
          recognition.stop();
          setIsListening(false);
      }
  }

  return { text, isListening, error, startListening, stopListening };
};


// Component to render a single analysis card
const AnalysisCard = ({ analysis, userMode, onReplace }) => { 
    
    const { text, label, risk_level, confidence, rule_summary, safer_alternative, lime_explanation } = analysis;
    const isLawyer = userMode === 'lawyer';

    // --- ADAPTIVE CLAUSE GENERATOR ---
    // If backend returns no suggestion, generate a standard safe clause based on category
    const getSuggestion = () => {
        if (safer_alternative) return safer_alternative;
        
        // Standard Safe Clauses for Common Risks
        const standardClauses = {
            "Indemnity": "The Provider's total liability for indemnification shall be limited to the total fees paid under this Agreement.",
            "Liability": "Except for fraud or willful misconduct, neither party's liability shall exceed the total contract value.",
            "Termination": "Either party may terminate this Agreement for convenience with thirty (30) days' prior written notice.",
            "Jurisdiction": "This Agreement shall be governed by the laws of India, and disputes resolved by arbitration in New Delhi.",
            "Payment_Terms": "Payment shall be made within 30 days of receipt of a valid invoice. Late payments typically incur 1.5% interest.",
            "Confidentiality": "Confidential Information shall be protected for a period of two (2) years following termination.",
            "Force_Majeure": "Neither party is liable for failure to perform due to causes beyond its reasonable control (Force Majeure).",
            "Intellectual_Property": "Client retains all ownership rights to pre-existing IP. Work product is 'Work Made for Hire'."
        };

        // Return standard clause if risk is High/Medium, otherwise generic advice
        if (risk_level !== 'Low') {
            return standardClauses[label] || "Consider adding a liability cap or mutual indemnification clause here.";
        }
        return null;
    };

    const finalSuggestion = getSuggestion();

    return (
        <div className={`rounded-xl shadow-md border-l-8 overflow-hidden bg-white mb-6 transition-all
            ${risk_level === 'High' ? 'border-red-500' : 
              risk_level === 'Medium' ? 'border-yellow-500' : 'border-green-500'}`}>
            <div className="p-6">
                
                {/* Clause Text */}
                <p className="text-gray-800 italic mb-4 p-3 bg-gray-50 rounded text-sm border border-gray-100">
                    "{text}"
                </p>

                {/* Risk and Category */}
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h4 className="text-xl font-bold text-gray-800">
                            Category: <span className="text-blue-600">{label}</span>
                        </h4>
                        {/* Only Lawyers need to see the raw confidence score */}
                        {isLawyer && (
                            <p className="text-gray-500 text-xs mt-1 font-mono">AI Confidence: {confidence}%</p>
                        )}
                    </div>
                    <div className={`px-4 py-2 rounded-full text-white font-bold text-sm uppercase tracking-wide shadow-sm ${risk_level === 'High' ? 'bg-red-500' : risk_level === 'Medium' ? 'bg-yellow-500' : 'bg-green-500'}`}>
                        {risk_level} Risk
                    </div>
                </div>

                {/* Explainable AI (LIME) - Hidden for Clients to reduce clutter */}
                {isLawyer && (
                    <>
                        <hr className="my-3 border-gray-100" />
                        <h3 className="font-bold text-gray-700 mb-3 text-xs uppercase tracking-wider">Explainable AI (Factors)</h3>
                        
                        {lime_explanation && lime_explanation.length > 0 ? (
                            <div className="flex flex-wrap gap-2 mb-4">
                            {lime_explanation.map((item, index) => {
                                const word = item.word || (Array.isArray(item) ? item[0] : "");
                                const score = item.weight || (Array.isArray(item) ? item[1] : 0);
                                return (
                                <div key={index} className={`flex flex-col items-center p-2 rounded border ${score > 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                                    <span className="font-bold text-gray-800 text-xs">{word}</span>
                                    <span className="text-[10px] text-gray-500">{Number(score).toFixed(2)}</span>
                                </div>
                                );
                            })}
                            </div>
                        ) : (
                            <div className="text-gray-400 text-xs italic mb-4">
                                No specific keyword drivers detected.
                            </div>
                        )}
                    </>
                )}

                {/* SAFER ALTERNATIVE - Useful for everyone */}
                {finalSuggestion && (
                    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4 rounded-r-lg mt-4 shadow-sm">
                        <p className="text-sm font-bold text-yellow-800 mb-1">💡 Negotiation Suggestion:</p>
                        <p className="text-sm text-yellow-800 opacity-90 mb-2">{finalSuggestion}</p>
                        
                        <div className="flex gap-2 mt-3">
                            <button 
                                onClick={() => {
                                    navigator.clipboard.writeText(finalSuggestion);
                                    alert("Suggestion copied to clipboard!");
                                }}
                                className="text-xs bg-white border border-yellow-300 hover:bg-yellow-100 text-yellow-800 px-3 py-1.5 rounded transition-colors font-medium flex items-center"
                            >
                                📋 Copy
                            </button>
                            
                            {/* REPLACE BUTTON (ADAPTIVE CLAUSE INSERTION) */}
                            <button 
                                onClick={() => onReplace(text, finalSuggestion)}
                                className="text-xs bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1.5 rounded transition-colors font-medium flex items-center shadow-sm"
                            >
                                🔄 Replace in Doc
                            </button>
                        </div>
                    </div>
                )}
                
                {/* SIMPLIFICATION - Priority for Clients */}
                <hr className="my-3 border-gray-100" />
                <h4 className="text-sm font-bold mb-2 text-gray-700">Plain English Summary</h4>
                
                {rule_summary ? (
                     <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg mt-2">
                        <p className="text-gray-800 text-sm leading-relaxed">
                            {rule_summary} 
                        </p>
                    </div>
                ) : (
                    <div className="text-gray-400 text-sm italic">No summary available.</div>
                )}
                
            </div>
        </div>
    );
};

// --- MAIN APP COMPONENT ---
function App() {
  const [text, setText] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null); 
  const [judgments, setJudgments] = useState([]); 
  const [loading, setLoading] = useState(false);
  const [searchingLaw, setSearchingLaw] = useState(false); 
  const [error, setError] = useState('');
  const [pdfLoading, setPdfLoading] = useState(false); 
  const [currentSearchClause, setCurrentSearchClause] = useState(''); 
  
  // NEW: User Role Toggle
  const [userMode, setUserMode] = useState('lawyer'); // 'lawyer' | 'client'

  // Voice Hook
  const { text: voiceText, isListening, error: voiceError, startListening, stopListening } = useSpeechRecognition();

  useEffect(() => {
      if (voiceText) {
          setText(prev => prev + ' ' + voiceText);
      }
  }, [voiceText]);

  // NEW: Handle Clause Replacement Logic
  const handleReplaceClause = (originalClause, newClause) => {
      // Basic safety check to ensure we replace the right text
      if (!text.includes(originalClause)) {
          alert("Could not find the exact original clause text. It might have been modified already.");
          return;
      }
      
      // Replace the first occurrence
      const newText = text.replace(originalClause, newClause);
      setText(newText);
      
      // Clear analysis as it is now outdated (or you could re-run it automatically)
      setAnalysisResults(null);
      setJudgments([]);
      alert("Clause replaced successfully! Document updated.");
  };


  const handlePdfUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || file.type !== 'application/pdf') {
      alert('Please select a valid PDF file.');
      return;
    }

    setPdfLoading(true); setError('');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/upload_pdf`, formData, { headers: { 'Content-Type': 'multipart/form-data' }});
      const extractedText = response.data.extracted_text || '';
      setText(extractedText);
      alert('PDF text extracted successfully! Please review and click Analyze Document.');
    } catch (err) {
      setError('Failed to process PDF. Ensure PyMuPDF is installed correctly on the backend.');
    }
    setPdfLoading(false);
  };

  const searchCaseLaw = async (clauseText) => {
    setSearchingLaw(true);
    setCurrentSearchClause(clauseText);
    try {
      const res = await axios.post(`${API_URL}/search_judgment`, { 
        clause_text: clauseText,
        top_k: 3 
      });
      setJudgments(res.data.results);
    } catch (err) {
      console.error("Case law search failed", err);
    }
    setSearchingLaw(false);
  };

  const analyzeDocument = async () => {
    if (!text.trim()) return;
    setLoading(true); setError(''); setAnalysisResults(null); setJudgments([]); setCurrentSearchClause('');

    try {
      const response = await axios.post(`${API_URL}/analyze_document`, { text: text });
      
      const results = response.data.analysis_results;
      setAnalysisResults(results);
      
      const highRiskClause = results.find(r => r.risk_level === 'High');
      
      if (highRiskClause) {
          searchCaseLaw(highRiskClause.text);
      } else if (results.length > 0) {
          searchCaseLaw(results[0].text);
      }

    } catch (err) {
      setError('Error analyzing document. Check console for details.');
    }
    setLoading(false);
  };
  
  // NEW: Export Report Function
  const downloadReport = () => {
      if (!analysisResults) return;
      
      let reportContent = "LEXSAKSHAM LEGAL ANALYSIS REPORT\n";
      reportContent += "================================\n\n";
      
      analysisResults.forEach((a, i) => {
          reportContent += `CLAUSE ${i+1}: ${a.label}\n`;
          reportContent += `RISK LEVEL: ${a.risk_level}\n`;
          reportContent += `TEXT: ${a.text}\n`;
          reportContent += `SUMMARY: ${a.rule_summary}\n`;
          if (a.safer_alternative) reportContent += `SUGGESTION: ${a.safer_alternative}\n`;
          reportContent += "--------------------------------\n\n";
      });
      
      if (judgments.length > 0) {
          reportContent += "RELEVANT CASE LAW:\n";
          judgments.forEach(j => {
              reportContent += `- ${j.case_name} (${j.year})\n`;
          });
      }
      
      const element = document.createElement("a");
      const file = new Blob([reportContent], {type: 'text/plain'});
      element.href = URL.createObjectURL(file);
      element.download = "lexsaksham_report.txt";
      document.body.appendChild(element);
      element.click();
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10 px-4 font-sans">
      <div className="max-w-3xl w-full text-center mb-8">
        <h1 className="text-4xl font-extrabold text-blue-900 mb-2 tracking-tight">LexSaksham</h1>
        <p className="text-gray-600 mb-4">AI-Powered Legal Contract Assistant</p>
        
        {/* ROLE TOGGLE */}
        <div className="inline-flex bg-gray-200 rounded-lg p-1 shadow-inner">
            <button 
                onClick={() => setUserMode('client')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${userMode === 'client' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-800'}`}
            >
                Client View
            </button>
            <button 
                onClick={() => setUserMode('lawyer')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${userMode === 'lawyer' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-800'}`}
            >
                Lawyer View
            </button>
        </div>
      </div>

      <div className="max-w-3xl w-full bg-white rounded-xl shadow-lg p-8 border border-gray-200">
        <label className="block text-gray-700 text-sm font-bold mb-2">Contract Clause / Full Document</label>
        
        <div className="flex flex-wrap justify-between items-center mb-4 gap-3">
             {/* PDF UPLOAD */}
            <div className="flex items-center space-x-4">
                <input type="file" accept=".pdf" id="pdf-upload" onChange={handlePdfUpload} disabled={pdfLoading} className="hidden"/>
                <label htmlFor="pdf-upload" className={`px-4 py-2 rounded-lg text-sm font-semibold cursor-pointer transition-colors ${pdfLoading ? 'bg-gray-200 text-gray-500' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'} border border-gray-300`}>
                    {pdfLoading ? 'Extracting...' : '📄 Upload PDF'}
                </label>
            </div>

            {/* VOICE INPUT */}
            <button 
                onClick={isListening ? stopListening : startListening}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center border ${isListening ? 'bg-red-50 border-red-200 text-red-600 animate-pulse' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
            >
                {isListening ? (
                    <><span className="mr-2">🔴</span> Listening...</>
                ) : (
                    <><span className="mr-2">🎤</span> Voice Input</>
                )}
            </button>
        </div>

        <textarea
          className="w-full p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition h-40 text-lg"
          placeholder="Paste a clause (e.g., 'The provider shall have unlimited liability...') or upload a PDF above."
          value={text} onChange={(e) => setText(e.target.value)}
        ></textarea>
        
        {error && <div className="mt-6 p-3 bg-red-100 text-red-700 rounded border border-red-200">{error}</div>}
        {voiceError && <div className="mt-2 text-xs text-red-500">{voiceError}</div>}
        
        <div className="mt-6 flex justify-end space-x-3">
          {/* Export Button (Only shows after analysis) */}
          {analysisResults && (
              <button onClick={downloadReport} className="px-6 py-3 rounded-lg text-blue-600 font-bold text-lg border-2 border-blue-600 hover:bg-blue-50 transition-all">
                  ⬇ Export Report
              </button>
          )}
          
          <button onClick={() => analyzeDocument()} disabled={loading || !text} className={`px-8 py-3 rounded-lg text-white font-bold text-lg shadow-md transition-all ${loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}>
            {loading ? 'Analyzing...' : 'Analyze Document'}
          </button>
        </div>
      </div>

      {analysisResults && analysisResults.length > 0 && (
        <div className="max-w-3xl w-full mt-8 animate-fade-in-up space-y-6">
            
            <div className="flex justify-between items-end">
                <h2 className="text-2xl font-extrabold text-gray-800">
                    Analysis Results
                </h2>
                <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                    {analysisResults.length} Clause{analysisResults.length !== 1 && 's'} Detected
                </span>
            </div>
            
            {/* Clause-by-Clause Results */}
            {analysisResults.map((analysis, index) => (
                <AnalysisCard key={index} analysis={analysis} userMode={userMode} onReplace={handleReplaceClause} />
            ))}

          {/* CASE LAW CARD - Hide for clients unless necessary, or keep simplified */}
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
              <span className="mr-2">⚖️</span> Relevant Case Law (Supreme Court)
            </h3>
            
            {searchingLaw ? (
              <p className="text-gray-500 italic flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Searching precedents based on the most critical clause...
              </p>
            ) : judgments.length > 0 ? (
              <div className="space-y-4">
                {judgments.map((judge, idx) => (
                  <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-bold text-blue-800 text-md">{judge.case_name}</h4>
                      <span className="text-xs bg-gray-200 px-2 py-1 rounded text-gray-600">{judge.year}</span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2 italic line-clamp-3">"{judge.text_snippet}"</p>
                    {userMode === 'lawyer' && (
                        <p className="text-xs font-bold" style={{ color: judge.similarity_score > 0.9 ? 'green' : 'orange' }}>
                        Vector Similarity: {(judge.similarity_score * 100).toFixed(1)}%
                        </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400">No highly relevant case law found for this document.</p>
            )}
          </div>

        </div>
      )}
    </div>
  );
}

export default App;