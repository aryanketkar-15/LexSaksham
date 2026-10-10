import React, { useState, useEffect } from 'react';
import { UploadCloud, Search, RefreshCw, Bell, Scale } from 'lucide-react';
import AnalysisCard from '../components/AnalysisCard';
import * as api from '../services/api';

const ContractAnalyzer = ({ role }) => {
  const [text, setText] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [judgments, setJudgments] = useState([]);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  
  // --- VOICE HOOK LOGIC (Simplified for modularity) ---
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window)) return;
    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setText(prev => prev + ' ' + transcript);
        setIsListening(false);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    if (isListening) recognition.start();
    else recognition.stop();

    return () => recognition.abort();
  }, [isListening]);


  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setAnalysisResults(null);
    setJudgments([]);

    try {
      const res = await api.analyzeDocument(text);
      const results = res.analysis_results;
      setAnalysisResults(results);

      const highRiskClause = results.find(r => r.risk_level === 'High');
      if (highRiskClause) {
          const searchRes = await api.searchJudgment(highRiskClause.text);
          setJudgments(searchRes.results);
      } else if (results.length > 0) {
           const searchRes = await api.searchJudgment(results[0].text);
           setJudgments(searchRes.results);
      }
    } catch (err) {
      alert("Analysis failed. Is the backend running?");
      console.error(err);
    }
    setLoading(false);
  };

  const handlePdfUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setPdfLoading(true);
    try {
      const res = await api.uploadPdf(file);
      setText(res.extracted_text || '');
      alert('PDF Extracted!');
    } catch (err) {
      alert("PDF Upload failed");
    }
    setPdfLoading(false);
  };

  const handleReplace = (original, replacement) => {
    if(!text.includes(original)) {
      alert("Could not find exact text match.");
      return;
    }
    setText(text.replace(original, replacement));
    alert("Clause Replaced Successfully!");
  };

  const downloadReport = () => {
      if (!analysisResults) return;
      let content = "LEXSAKSHAM REPORT\n\n";
      analysisResults.forEach((a, i) => {
          content += `CLAUSE ${i+1}: ${a.label} (${a.risk_level} Risk)\n${a.text}\nSummary: ${a.rule_summary}\n\n`;
      });
      const element = document.createElement("a");
      const file = new Blob([content], {type: 'text/plain'});
      element.href = URL.createObjectURL(file);
      element.download = "report.txt";
      document.body.appendChild(element);
      element.click();
  };

  return (
    <div className="h-full flex flex-col">
      {/* HEADER */}
      <div className="flex justify-between items-center mb-6">
        <div>
            <h2 className="text-2xl font-bold text-gray-800">Analysis Studio</h2>
            <p className="text-gray-500 text-sm">AI-powered contract review</p>
        </div>
        <div className="flex gap-3">
             {/* Buttons */}
            <label className="cursor-pointer bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-sm transition">
                <UploadCloud size={18} />
                {pdfLoading ? "Scanning..." : "Upload PDF"}
                <input type="file" accept=".pdf" className="hidden" onChange={handlePdfUpload} />
            </label>
            
            <button 
                onClick={() => setIsListening(!isListening)}
                className={`px-4 py-2 rounded-lg font-medium border flex items-center gap-2 ${isListening ? 'bg-red-50 text-red-600 border-red-200 animate-pulse' : 'bg-white text-gray-700 border-gray-300'}`}
            >
                {isListening ? 'Listening...' : 'Mic Input'}
            </button>

            <button 
                onClick={handleAnalyze}
                disabled={loading || !text}
                className="bg-[#1F3C88] hover:bg-blue-800 text-white px-6 py-2 rounded-lg font-bold shadow-md flex items-center gap-2 disabled:opacity-50"
            >
                {loading ? <RefreshCw className="animate-spin" size={18}/> : <Search size={18}/>}
                Analyze
            </button>
            
            {analysisResults && (
                <button onClick={downloadReport} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-bold shadow-md">
                    Export
                </button>
            )}
        </div>
      </div>

      {/* WORKSPACE */}
      <div className="flex-1 flex gap-6 overflow-hidden">
        <div className="w-1/2 flex flex-col bg-white rounded-xl shadow-sm border border-gray-200">
            <textarea 
                className="flex-1 p-6 resize-none outline-none text-gray-700 font-mono text-sm"
                placeholder="Paste contract text..."
                value={text}
                onChange={(e) => setText(e.target.value)}
            />
        </div>

        <div className="w-1/2 flex flex-col gap-4 overflow-y-auto pr-2 pb-20">
            {analysisResults && analysisResults.map((item, idx) => (
                <AnalysisCard key={idx} analysis={item} userMode={role} onReplace={handleReplace} />
            ))}
            
            {/* CASE LAW CARD */}
            {judgments.length > 0 && (
                <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
                    <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
                    <span className="mr-2">⚖️</span> Relevant Case Law
                    </h3>
                    <div className="space-y-4">
                        {judgments.map((judge, idx) => (
                        <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <div className="flex justify-between items-center mb-2">
                            <h4 className="font-bold text-blue-800 text-md">{judge.case_name}</h4>
                            <span className="text-xs bg-gray-200 px-2 py-1 rounded text-gray-600">{judge.year}</span>
                            </div>
                            <p className="text-sm text-gray-700 italic">"{judge.text_snippet}"</p>
                        </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
      </div>
    </div>
  );
};

export default ContractAnalyzer;