import React from 'react';
import { Copy, RefreshCw } from 'lucide-react';

const AnalysisCard = ({ analysis, userMode, onReplace }) => { 
    
    const { text, label, risk_level, confidence, rule_summary, safer_alternative, lime_explanation } = analysis;
    const isLawyer = userMode === 'lawyer';

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
                        {isLawyer && (
                            <p className="text-gray-500 text-xs mt-1 font-mono">AI Confidence: {confidence}%</p>
                        )}
                    </div>
                    <div className={`px-4 py-2 rounded-full text-white font-bold text-sm uppercase tracking-wide shadow-sm ${risk_level === 'High' ? 'bg-red-500' : risk_level === 'Medium' ? 'bg-yellow-500' : 'bg-green-500'}`}>
                        {risk_level} Risk
                    </div>
                </div>

                {/* Explainable AI (LIME) */}
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

                {/* SAFER ALTERNATIVE */}
                {(safer_alternative && risk_level !== 'Low') && (
                    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4 rounded-r-lg mt-4 shadow-sm">
                        <p className="text-sm font-bold text-yellow-800 mb-1">💡 Negotiation Suggestion:</p>
                        <p className="text-sm text-yellow-800 opacity-90 mb-2">{safer_alternative}</p>
                        
                        <div className="flex gap-2 mt-3">
                            <button 
                                onClick={() => {
                                    navigator.clipboard.writeText(safer_alternative);
                                    alert("Suggestion copied to clipboard!");
                                }}
                                className="text-xs bg-white border border-yellow-300 hover:bg-yellow-100 text-yellow-800 px-3 py-1.5 rounded transition-colors font-medium flex items-center gap-1"
                            >
                                <Copy size={14} /> Copy
                            </button>
                            
                            <button 
                                onClick={() => onReplace(text, safer_alternative)}
                                className="text-xs bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1.5 rounded transition-colors font-medium flex items-center shadow-sm gap-1"
                            >
                                <RefreshCw size={14} /> Replace in Doc
                            </button>
                        </div>
                    </div>
                )}
                
                {/* SIMPLIFICATION */}
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

export default AnalysisCard;