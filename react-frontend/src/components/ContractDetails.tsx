import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Textarea } from './ui/textarea';
import { Separator } from './ui/separator';
import { ScrollArea } from './ui/scroll-area';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  Download, 
  Edit, 
  MessageSquare, 
  History, 
  AlertTriangle,
  CheckCircle,
  Eye,
  ThumbsUp,
  ThumbsDown,
  Lightbulb,
  Clock,
  User,
  Building,
  FileText,
  ChevronDown,
  ChevronUp,
  Scale
} from 'lucide-react';
import { analyzeDocument, searchJudgment } from '../services/api';
import { useContracts } from '../context/ContractsContext';

// Default clauses for fallback when no analysis results are available
const extractedClausesDefault = [
  {
    id: 1,
    title: "Compensation Clause",
    content: "Employee shall receive an annual salary of $120,000, payable in accordance with Company's standard payroll practices.",
    risk: "low",
    explanation: "Standard compensation clause with clearly defined salary amount.",
    suggestion: "Consider adding performance-based bonuses for better alignment."
  },
  {
    id: 2,
    title: "Non-Compete Clause",
    content: "Employee agrees not to engage in any business that directly competes with the Company during employment and for 6 months after termination.",
    risk: "medium",
    explanation: "Non-compete duration may be enforceable but should be reviewed for reasonableness.",
    suggestion: "Consider reducing the non-compete period to 3 months to ensure enforceability."
  },
  {
    id: 3,
    title: "Termination Clause",
    content: "Either party may terminate this Agreement with thirty (30) days written notice.",
    risk: "low",
    explanation: "Reasonable notice period for termination by either party.",
    suggestion: "Consider adding specific termination procedures and severance terms."
  },
  {
    id: 4,
    title: "Confidentiality Clause",
    content: "Employee acknowledges that they may have access to confidential information and agrees to maintain strict confidentiality.",
    risk: "medium",
    explanation: "Confidentiality clause lacks specific definition of confidential information.",
    suggestion: "Add detailed definition of what constitutes confidential information."
  }
];

// Version history is now loaded from contract data dynamically

// Comments are now loaded from contract data

const getRiskColor = (risk) => {
  switch (risk) {
    case 'low': return 'bg-green-100 text-green-800 border-green-200';
    case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'critical': return 'bg-red-100 text-red-800 border-red-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getRiskIcon = (risk) => {
  switch (risk) {
    case 'low': return <CheckCircle className="h-4 w-4" />;
    case 'medium': return <AlertTriangle className="h-4 w-4" />;
    case 'high': return <AlertTriangle className="h-4 w-4" />;
    case 'critical': return <AlertTriangle className="h-4 w-4" />;
    default: return <Eye className="h-4 w-4" />;
  }
};

export default function ContractDetails({ currentUser }) {
  const { id } = useParams();
  const { getContract, updateContract } = useContracts();
  const contract = getContract(id);
  const [newComment, setNewComment] = useState('');
  const [selectedClause, setSelectedClause] = useState(null);
  const [extractedClauses, setExtractedClauses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [judgments, setJudgments] = useState({});
  const [versionHistory, setVersionHistory] = useState([]);
  const [acceptedClauses, setAcceptedClauses] = useState(new Set());
  const [expandedVersions, setExpandedVersions] = useState(new Set());
  const [comments, setComments] = useState([]);
  const isLawyer = currentUser?.role === 'Lawyer';

  useEffect(() => {
    // Load contract data if available
    if (contract) {
      // Load version history
      if (contract.versionHistory && contract.versionHistory.length > 0) {
        setVersionHistory(contract.versionHistory);
      } else {
        // Initialize with original version
        const initialVersion = {
          id: 1,
          version: "1.0",
          date: contract.uploadedOn || contract.uploadedAt || new Date().toISOString(),
          author: "System",
          changes: "Original contract uploaded",
          status: "current",
          contractText: contract.extracted_text || contract.content || "",
          changedClause: null
        };
        setVersionHistory([initialVersion]);
      }

      // Load accepted clauses
      if (contract.acceptedClauses) {
        setAcceptedClauses(new Set(contract.acceptedClauses));
      }

      // Load comments
      if (contract.comments && Array.isArray(contract.comments)) {
        setComments(contract.comments);
      } else {
        setComments([]); // Initialize empty if no comments
      }

      if (contract.analysis_results && contract.analysis_results.length > 0) {
        // Use real analysis results from backend
        const clauses = contract.analysis_results.map((item, index) => {
          const clauseId = `clause-${index + 1}`;
          const isAccepted = acceptedClauses.has(clauseId) || item.accepted;
          
          // Determine original content: prioritize saved original_text
          let originalContent;
          if (item.original_text) {
            // Use saved original text (this is the correct original)
            originalContent = item.original_text;
          } else if (item.accepted && item.safer_alternative) {
            // If accepted but no original_text saved (legacy data or bug)
            // item.text is already the safer alternative, so we CANNOT use it as original
            // This is a data integrity issue - we should have saved original_text when accepting
            // Since we can't determine the original, we'll show the safer alternative as a fallback
            // but log a warning. In production, this should never happen if we save original_text correctly
            console.warn(`Clause ${index + 1} was accepted but original_text not saved. Cannot show true original.`);
            // Unfortunately, we can't recover the original text - this is a data loss scenario
            // We'll use the safer alternative text as fallback (not ideal, but better than nothing)
            originalContent = item.safer_alternative; // Use safer alternative as fallback (not ideal)
          } else {
            // Not accepted yet, so current text IS the original
            originalContent = item.text;
          }
          
          return {
            id: clauseId,
            originalId: index + 1,
            title: item.label || `Clause ${index + 1}`,
            content: isAccepted && item.safer_alternative ? item.safer_alternative : item.text,
            originalContent: originalContent,
            risk: item.risk_level?.toLowerCase() || 'low',
            explanation: item.rule_summary || 'No explanation available',
            suggestion: item.safer_alternative || null,
            saferAlternative: item.safer_alternative || null,
            confidence: item.confidence || 0,
            lime_explanation: item.lime_explanation || [],
            isAccepted: isAccepted
          };
        });
        setExtractedClauses(clauses);
      } else {
        // Fallback to default if no analysis
        setExtractedClauses(extractedClausesDefault);
      }
    } else {
      // No contract found, use default
      setExtractedClauses(extractedClausesDefault);
    }
  }, [id, contract]);

  const loadAnalysis = async () => {
    if (!contract?.extracted_text) {
      toast.error('No contract text available for analysis');
      return;
    }
    
    setLoading(true);
    try {
      const result = await analyzeDocument(contract.extracted_text, 'user');
      if (result.analysis_results) {
        const clauses = result.analysis_results.map((item, index) => {
          const clauseId = `clause-${index + 1}`;
          const isAccepted = acceptedClauses.has(clauseId);
          
          return {
            id: clauseId,
            originalId: index + 1,
            title: item.label || `Clause ${index + 1}`,
            content: isAccepted && item.safer_alternative ? item.safer_alternative : item.text,
            originalContent: item.original_text || item.text, // Use original_text if saved, otherwise use current text as original
            risk: item.risk_level?.toLowerCase() || 'low',
            explanation: item.rule_summary || 'No explanation available',
            suggestion: item.safer_alternative || null,
            saferAlternative: item.safer_alternative || null,
            confidence: item.confidence || 0,
            lime_explanation: item.lime_explanation || [],
            isAccepted: isAccepted
          };
        });
        setExtractedClauses(clauses);
        toast.success('Contract analyzed successfully!');
      }
    } catch (error) {
      toast.error(`Failed to analyze contract: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadJudgments = async (clauseText) => {
    if (judgments[clauseText]) return; // Already loaded
    
    try {
      const result = await searchJudgment(clauseText, 3);
      setJudgments(prev => ({
        ...prev,
        [clauseText]: result.results || []
      }));
    } catch (error) {
      console.error('Failed to load judgments:', error);
    }
  };

  const handleAddComment = () => {
    if (newComment.trim() && contract) {
      const newCommentObj = {
        id: Date.now(),
        author: "You",
        avatar: "U",
        content: newComment,
        timestamp: "Just now",
        type: "note"
      };
      
      const updatedComments = [newCommentObj, ...comments];
      setComments(updatedComments);
      
      // Save to contract
      updateContract(contract.id, {
        comments: updatedComments
      });
      
      toast.success('Comment added successfully');
      setNewComment('');
    }
  };

  const handleDownload = () => {
    if (!contract) {
      toast.error('No contract data available to download');
      return;
    }

    try {
      // Get the latest contract data (including any updates)
      const latestContract = getContract(id);
      const currentClauses = extractedClauses.length > 0 ? extractedClauses : 
        (latestContract?.analysis_results || []).map((item, index) => ({
          id: `clause-${index + 1}`,
          title: item.label || `Clause ${index + 1}`,
          content: item.accepted && item.safer_alternative ? item.safer_alternative : item.text,
          risk: item.risk_level?.toLowerCase() || 'low',
          explanation: item.rule_summary || 'No explanation available',
          suggestion: item.safer_alternative || null,
          isAccepted: item.accepted || false
        }));

      // Calculate current statistics
      const riskCounts = currentClauses.reduce((acc, clause) => {
        const risk = clause.risk?.toLowerCase() || 'low';
        acc[risk] = (acc[risk] || 0) + 1;
        return acc;
      }, { low: 0, medium: 0, high: 0, critical: 0 });

      const highestRisk = riskCounts.critical > 0 ? 'Critical' :
                          riskCounts.high > 0 ? 'High' :
                          riskCounts.medium > 0 ? 'Medium' : 'Low';

      // Get current version
      const currentVersion = versionHistory.find(v => v.status === 'current') || versionHistory[versionHistory.length - 1] || { version: '1.0' };

      // Generate report content
      const reportContent = `LEXSAKSHAM - CONTRACT ANALYSIS REPORT
Generated: ${new Date().toLocaleString()}
================================================================================

CONTRACT INFORMATION
--------------------------------------------------------------------------------
File Name: ${latestContract?.name || 'Unknown'}
Contract Type: ${latestContract?.type || 'PDF'}
Uploaded On: ${latestContract?.uploadedOn || latestContract?.uploadedAt || 'Unknown'}
File Size: ${latestContract?.fileSize ? (latestContract.fileSize / 1024).toFixed(2) + ' KB' : 'Unknown'}
Total Clauses: ${currentClauses.length}
Current Version: ${currentVersion.version}
Overall Risk Level: ${highestRisk.toUpperCase()}

RISK DISTRIBUTION
--------------------------------------------------------------------------------
Low Risk:     ${riskCounts.low}
Medium Risk:  ${riskCounts.medium}
High Risk:    ${riskCounts.high}
Critical Risk: ${riskCounts.critical}

================================================================================
CLAUSE ANALYSIS (LATEST VERSION)
================================================================================

${currentClauses.map((clause, index) => {
  const riskLabel = clause.risk?.toUpperCase() || 'LOW';
  const statusLabel = clause.isAccepted ? '[UPDATED - Safer Alternative Accepted]' : '[ORIGINAL]';
  
  return `
CLAUSE ${index + 1}: ${clause.title}
${'='.repeat(80)}
Risk Level: ${riskLabel} ${statusLabel}
${'-'.repeat(80)}

Clause Text:
${clause.content}

${clause.explanation ? `AI Explanation:
${clause.explanation}
` : ''}

${clause.suggestion && !clause.isAccepted ? `Suggested Safer Alternative:
${clause.suggestion}
` : ''}

${clause.isAccepted ? `✓ This clause has been updated with a safer alternative.
Original text has been replaced with the suggested improvement.
` : ''}

`;
}).join('\n')}

================================================================================
VERSION HISTORY SUMMARY
================================================================================

${versionHistory.map(v => {
  const date = new Date(v.date).toLocaleDateString();
  return `Version ${v.version} ${v.status === 'current' ? '(CURRENT)' : '(ARCHIVED)'}
  Date: ${date}
  Author: ${v.author}
  Changes: ${v.changes}
`;
}).join('\n')}

${comments.length > 0 ? `
================================================================================
COMMENTS & NOTES
================================================================================

${comments.map(c => `[${c.timestamp}] ${c.author}: ${c.content}`).join('\n\n')}
` : ''}

================================================================================
END OF REPORT
================================================================================

This report reflects the latest state of the contract analysis, including any
clause updates and safer alternatives that have been accepted.

Generated by LexSaksham Contract Analysis Platform
`;

      // Create and download the file
      const blob = new Blob([reportContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${latestContract?.name?.replace(/\.[^/.]+$/, '') || 'contract'}_analysis_report_${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast.success('Analysis report downloaded successfully');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to generate report. Please try again.');
    }
  };

  const handleDownloadVersion = (version) => {
    if (!version || !version.contractText) {
      toast.error('No contract text available for this version');
      return;
    }

    try {
      // Get contract info
      const latestContract = getContract(id);
      const versionDate = new Date(version.date).toLocaleDateString();
      
      // Generate version-specific content
      const versionContent = `LEXSAKSHAM - CONTRACT VERSION ${version.version}
Generated: ${new Date().toLocaleString()}
================================================================================

CONTRACT INFORMATION
--------------------------------------------------------------------------------
File Name: ${latestContract?.name || 'Unknown'}
Contract Type: ${latestContract?.type || 'PDF'}
Version: ${version.version}
Status: ${version.status === 'current' ? 'CURRENT' : 'ARCHIVED'}
Date: ${versionDate}
Author: ${version.author}
Changes: ${version.changes}

${version.changedClause ? `
CHANGED CLAUSE DETAILS
--------------------------------------------------------------------------------
Clause Title: ${version.changedClause.title}

Original Text:
${version.changedClause.originalText}

Updated Text:
${version.changedClause.newText}
` : ''}

================================================================================
FULL CONTRACT TEXT (VERSION ${version.version})
================================================================================

${version.contractText}

================================================================================
END OF CONTRACT
================================================================================

Generated by LexSaksham Contract Analysis Platform
`;

      // Create and download the file
      const blob = new Blob([versionContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const fileName = `${latestContract?.name?.replace(/\.[^/.]+$/, '') || 'contract'}_v${version.version}_${new Date(version.date).toISOString().split('T')[0]}.txt`;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast.success(`Version ${version.version} downloaded successfully`);
    } catch (error) {
      console.error('Download version error:', error);
      toast.error('Failed to download version. Please try again.');
    }
  };

  const handleClauseAction = async (action, clauseId) => {
    const clause = extractedClauses.find(c => c.id === clauseId);
    if (!clause) return;

    if (action === 'Accept suggestion') {
      if (!clause.saferAlternative) {
        toast.error('No safer alternative available for this clause');
        return;
      }

      // CRITICAL: Capture originalContent BEFORE any updates
      // originalContent should be the text BEFORE acceptance
      const originalText = clause.originalContent || clause.content;

      // Update the clause content - NEVER change originalContent
      const updatedClauses = extractedClauses.map(c => {
        if (c.id === clauseId) {
          return { 
            ...c, 
            content: c.saferAlternative, 
            originalContent: originalText, // Use the captured original - never change it
            isAccepted: true 
          };
        }
        return c;
      });
      setExtractedClauses(updatedClauses);

      // Mark as accepted
      const newAcceptedClauses = new Set(acceptedClauses);
      newAcceptedClauses.add(clauseId);
      setAcceptedClauses(newAcceptedClauses);

      // Update the contract's extracted text with the safer alternative
      if (contract && contract.extracted_text) {
        // Use the originalContent that we're preserving, not the current content
        const originalTextToReplace = clause.originalContent || clause.content;
        const updatedText = contract.extracted_text.replace(
          originalTextToReplace,
          clause.saferAlternative
        );

        // Create new version history entry
        const currentVersion = versionHistory.find(v => v.status === 'current');
        const currentVersionNum = currentVersion ? parseFloat(currentVersion.version) : 1.0;
        const newVersionNum = (currentVersionNum + 0.1).toFixed(1);
        
        const newVersion = {
          id: Date.now(),
          version: newVersionNum,
          date: new Date().toISOString(),
          author: "User",
          changes: `Accepted safer alternative for clause: ${clause.title}`,
          status: "current",
          contractText: updatedText, // Store full contract text for this version
          changedClause: {
            title: clause.title,
            originalText: clause.originalContent,
            newText: clause.saferAlternative,
            clauseId: clause.id
          }
        };

        // Mark previous version as archived
        const updatedHistory = versionHistory.map(v => 
          v.status === 'current' ? { ...v, status: 'archived' } : v
        );
        const finalHistory = [...updatedHistory, newVersion];
        setVersionHistory(finalHistory);

        // Update contract in context
        const clauseOriginalIndex = extractedClauses.findIndex(c => c.id === clauseId);
        updateContract(contract.id, {
          extracted_text: updatedText,
          versionHistory: finalHistory,
          acceptedClauses: Array.from(newAcceptedClauses),
          analysis_results: contract.analysis_results.map((item, idx) => {
            if (idx === clause.originalId - 1) {
              // CRITICAL: Use the originalText we captured above (from clause.originalContent)
              // This ensures we save the TRUE original text, not the updated one
              return { 
                ...item, 
                text: clause.saferAlternative, 
                original_text: originalText, // Use the captured original text
                accepted: true 
              };
            }
            return item;
          })
        });

        toast.success(`Safer clause accepted for "${clause.title}"`);
      }
    } else if (action === 'Reject suggestion') {
      toast.info('Suggestion rejected');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link to="/contracts">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Contracts
            </Link>
          </Button>
          <div>
            <h1>{contract?.name || 'Contract Details'}</h1>
            <div className="flex items-center space-x-2 mt-1">
              {contract?.type && (
                <Badge variant="outline">{contract.type}</Badge>
              )}
              {contract?.risk && (
                <Badge className={getRiskColor(contract.risk)}>
                  {contract.risk.toLowerCase()} risk
                </Badge>
              )}
              {contract?.status && (
                <Badge variant="secondary">{contract.status}</Badge>
              )}
              {!contract && (
                <Badge variant="outline" className="text-yellow-600">
                  Contract not found
                </Badge>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
          <Button variant="outline" size="sm">
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Button>
        </div>
      </div>

      {/* Contract Info */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">File Name</p>
              <p className="font-medium">{contract?.name || 'Unknown'}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Contract Type</p>
              <p className="font-medium">{contract?.type || 'Not specified'}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Uploaded On</p>
              <p className="font-medium">
                {contract?.uploadedOn 
                  ? new Date(contract.uploadedOn).toLocaleDateString() 
                  : contract?.uploadedAt
                  ? new Date(contract.uploadedAt).toLocaleDateString()
                  : 'Unknown'}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">File Size</p>
              <p className="font-medium">
                {contract?.fileSize 
                  ? `${(contract.fileSize / 1024).toFixed(2)} KB`
                  : 'Unknown'}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Clauses Extracted</p>
              <p className="font-medium">{contract?.analysis_results?.length || extractedClauses.length || 0}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Risk Level</p>
              <Badge className={getRiskColor(contract?.risk || 'low')}>
                {(contract?.risk || 'low').toUpperCase()}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Contract Content & Analysis */}
        <div className="lg:col-span-2 space-y-6">
          <Tabs defaultValue="content" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="content">Contract Text</TabsTrigger>
              <TabsTrigger value="clauses">AI Analysis</TabsTrigger>
              <TabsTrigger value="history">Version History</TabsTrigger>
            </TabsList>

            <TabsContent value="content" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Original Contract Text</CardTitle>
                  <CardDescription>
                    Full text of the uploaded contract document
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-96 w-full">
                    <div className="whitespace-pre-line text-sm leading-relaxed">
                      {(() => {
                        // Use updated text if clauses have been accepted
                        let displayText = contract?.extracted_text || contract?.content || 'No contract text available. Please upload a contract to view its content.';
                        
                        // Apply accepted clause changes to display
                        extractedClauses.forEach(clause => {
                          if (clause.isAccepted && clause.saferAlternative && clause.originalContent) {
                            displayText = displayText.replace(clause.originalContent, clause.content);
                          }
                        });
                        
                        return displayText;
                      })()}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="clauses" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Extracted Clauses</CardTitle>
                  <CardDescription>
                    AI-identified contract clauses with risk assessment and suggestions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="text-center py-8">
                      <p className="text-muted-foreground">Analyzing contract...</p>
                    </div>
                  ) : extractedClauses.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-muted-foreground">No clauses extracted yet.</p>
                      {contract?.extracted_text && (
                        <Button onClick={loadAnalysis} className="mt-4">
                          Analyze with AI (Legal-BERT + T5)
                        </Button>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {extractedClauses.map((clause) => (
                      <motion.div
                        key={clause.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                          selectedClause === clause.id ? 'bg-muted/50 border-primary' : 'hover:bg-muted/20'
                        }`}
                        onClick={() => setSelectedClause(selectedClause === clause.id ? null : clause.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <Badge className={getRiskColor(clause.risk)}>
                                {getRiskIcon(clause.risk)}
                                <span className="ml-1">{clause.risk} risk</span>
                              </Badge>
                              <h4 className="font-medium">{clause.title}</h4>
                            </div>
                            <div className="mb-2">
                              {clause.isAccepted && clause.saferAlternative ? (
                                <div>
                                  <p className="text-xs text-green-600 mb-1 font-medium flex items-center">
                                    <CheckCircle className="h-3 w-3 mr-1" />
                                    Updated with safer clause:
                                  </p>
                                  <p className="text-sm text-gray-800 italic">"{clause.content}"</p>
                                  <details className="mt-2">
                                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">Show original clause</summary>
                                    <p className="text-sm text-gray-400 italic mt-1">"{clause.originalContent}"</p>
                                  </details>
                                </div>
                              ) : (
                                <p className="text-sm text-muted-foreground italic">"{clause.content}"</p>
                              )}
                            </div>
                            {selectedClause === clause.id && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                transition={{ duration: 0.2 }}
                                className="space-y-3"
                              >
                                <div className="bg-blue-50 p-3 rounded">
                                  <div className="flex items-start space-x-2">
                                    <Eye className="h-4 w-4 text-blue-600 mt-0.5" />
                                    <div>
                                      <p className="text-sm font-medium text-blue-800">Analysis</p>
                                      <p className="text-sm text-blue-700">{clause.explanation}</p>
                                    </div>
                                  </div>
                                </div>
                                
                                {/* Supreme Court Judgments - Only for Lawyers */}
                                {isLawyer && (
                                  <div className="bg-purple-50 p-3 rounded border border-purple-200">
                                    <div className="flex items-start space-x-2">
                                      <Scale className="h-4 w-4 text-purple-600 mt-0.5" />
                                      <div className="flex-1">
                                        <p className="text-sm font-medium text-purple-800 mb-2">Supreme Court Judgments</p>
                                        {judgments[clause.content] ? (
                                          <div className="space-y-2">
                                            {judgments[clause.content].length > 0 ? (
                                              judgments[clause.content].slice(0, 2).map((judgment, idx) => (
                                                <div key={idx} className="bg-white p-2 rounded border border-purple-200">
                                                  <p className="text-xs font-medium text-purple-900">
                                                    {judgment.case_name || judgment.title || `Case ${idx + 1}`}
                                                    {judgment.year && ` (${judgment.year})`}
                                                  </p>
                                                  {judgment.summary && (
                                                    <p className="text-xs text-purple-700 mt-1 line-clamp-2">
                                                      {judgment.summary}
                                                    </p>
                                                  )}
                                                </div>
                                              ))
                                            ) : (
                                              <p className="text-xs text-purple-600">No relevant judgments found</p>
                                            )}
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              className="w-full text-xs"
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                loadJudgments(clause.content);
                                              }}
                                            >
                                              View All Judgments
                                            </Button>
                                          </div>
                                        ) : (
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            className="text-xs"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              loadJudgments(clause.content);
                                            }}
                                          >
                                            Search Relevant Judgments
                                          </Button>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                )}
                                
                                {/* AI Suggestion Section */}
                                <div className="bg-green-50 p-3 rounded">
                                  <div className="flex items-start space-x-2">
                                    <Lightbulb className="h-4 w-4 text-green-600 mt-0.5" />
                                    <div className="flex-1">
                                      <p className="text-sm font-medium text-green-800">AI Suggestion</p>
                                      {clause.saferAlternative ? (
                                        <>
                                          <p className="text-sm text-green-700 mb-2 mt-1">
                                            A safer alternative clause is available:
                                          </p>
                                          <div className="bg-white p-2 rounded border border-green-300 mt-2">
                                            <p className="text-sm text-gray-800 whitespace-pre-wrap">{clause.saferAlternative}</p>
                                          </div>
                                        </>
                                      ) : (
                                        <p className="text-sm text-green-700 mt-1">{clause.suggestion || 'No specific suggestion available for this clause.'}</p>
                                      )}
                                    </div>
                                  </div>
                                </div>

                                {/* Accept/Reject Buttons - Always visible below AI Suggestion */}
                                {clause.isAccepted && clause.saferAlternative ? (
                                  <div className="bg-blue-50 p-2 rounded border border-blue-200">
                                    <div className="flex items-center space-x-2">
                                      <CheckCircle className="h-4 w-4 text-blue-600" />
                                      <p className="text-sm text-blue-800">Safer clause has been accepted and applied.</p>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="flex space-x-2">
                                    <Button 
                                      size="sm" 
                                      className={clause.saferAlternative ? "bg-green-600 hover:bg-green-700 text-white" : "bg-gray-300 text-gray-600 cursor-not-allowed"}
                                      disabled={!clause.saferAlternative}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        if (clause.saferAlternative) {
                                          handleClauseAction('Accept suggestion', clause.id);
                                        } else {
                                          toast.info('No safer alternative available for this clause');
                                        }
                                      }}
                                    >
                                      <ThumbsUp className="h-3 w-3 mr-1" />
                                      Accept
                                    </Button>
                                    <Button 
                                      size="sm" 
                                      variant="outline"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleClauseAction('Reject suggestion', clause.id);
                                      }}
                                    >
                                      <ThumbsDown className="h-3 w-3 mr-1" />
                                      Reject
                                    </Button>
                                  </div>
                                )}
                              </motion.div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="history" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Version History</CardTitle>
                  <CardDescription>
                    Track changes and revisions to this contract
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {versionHistory.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>No version history available yet.</p>
                      <p className="text-sm mt-2">Changes will be tracked here when you accept clause suggestions.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {versionHistory.map((version, index) => {
                        const isExpanded = expandedVersions.has(version.id);
                        return (
                        <div key={version.id} className="border rounded-lg p-4">
                          <div className="flex items-start space-x-4">
                            <div className="flex flex-col items-center">
                              <div className={`w-3 h-3 rounded-full ${
                                version.status === 'current' ? 'bg-green-500' : 'bg-gray-300'
                              }`}></div>
                              {index < versionHistory.length - 1 && (
                                <div className="w-px h-8 bg-gray-300 mt-2"></div>
                              )}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <div>
                                  <div className="flex items-center space-x-2">
                                    <span className="font-medium">Version {version.version}</span>
                                    {version.status === 'current' && (
                                      <Badge variant="secondary">Current</Badge>
                                    )}
                                  </div>
                                  <p className="text-sm text-muted-foreground mt-1">{version.changes}</p>
                                  <div className="flex items-center space-x-4 text-xs text-muted-foreground mt-1">
                                    <span className="flex items-center space-x-1">
                                      <User className="h-3 w-3" />
                                      <span>{version.author}</span>
                                    </span>
                                    <span className="flex items-center space-x-1">
                                      <Clock className="h-3 w-3" />
                                      <span>{new Date(version.date).toLocaleDateString()}</span>
                                    </span>
                                  </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                  {version.status === 'current' && version.contractText && (
                                    <Button
                                      variant="default"
                                      size="sm"
                                      onClick={() => handleDownloadVersion(version)}
                                      className="bg-primary hover:bg-primary/90"
                                    >
                                      <Download className="h-4 w-4 mr-1" />
                                      Download Latest Version
                                    </Button>
                                  )}
                                  {version.contractText && (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => {
                                        const newExpanded = new Set(expandedVersions);
                                        if (isExpanded) {
                                          newExpanded.delete(version.id);
                                        } else {
                                          newExpanded.add(version.id);
                                        }
                                        setExpandedVersions(newExpanded);
                                      }}
                                    >
                                      {isExpanded ? (
                                        <>
                                          <ChevronUp className="h-4 w-4 mr-1" />
                                          Hide Contract
                                        </>
                                      ) : (
                                        <>
                                          <ChevronDown className="h-4 w-4 mr-1" />
                                          View Contract
                                        </>
                                      )}
                                    </Button>
                                  )}
                                </div>
                              </div>

                              {/* Changed Clause Details */}
                              {version.changedClause && (
                                <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200">
                                  <p className="text-sm font-medium text-blue-800 mb-2">
                                    Changed Clause: {version.changedClause.title}
                                  </p>
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    <div>
                                      <p className="text-xs font-medium text-gray-600 mb-1">Original:</p>
                                      <div className="bg-white p-2 rounded border border-red-200">
                                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{version.changedClause.originalText}</p>
                                      </div>
                                    </div>
                                    <div>
                                      <p className="text-xs font-medium text-gray-600 mb-1">Updated:</p>
                                      <div className="bg-white p-2 rounded border border-green-200">
                                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{version.changedClause.newText}</p>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* Full Contract Text */}
                              {isExpanded && version.contractText && (
                                <div className="mt-4">
                                  <div className="flex items-center space-x-2 mb-2">
                                    <FileText className="h-4 w-4 text-muted-foreground" />
                                    <p className="text-sm font-medium">Full Contract Text (Version {version.version})</p>
                                  </div>
                                  <ScrollArea className="h-96 w-full border rounded p-4 bg-muted/20">
                                    <div className="whitespace-pre-line text-sm leading-relaxed">
                                      {version.changedClause ? (
                                        // Highlight the changed clause in the text
                                        (() => {
                                          const parts = version.contractText.split(version.changedClause.newText);
                                          return parts.map((part, idx) => (
                                            <React.Fragment key={idx}>
                                              {part}
                                              {idx < parts.length - 1 && (
                                                <mark className="bg-green-200 border border-green-400 rounded px-1 font-medium">
                                                  {version.changedClause.newText}
                                                </mark>
                                              )}
                                            </React.Fragment>
                                          ));
                                        })()
                                      ) : (
                                        version.contractText
                                      )}
                                    </div>
                                  </ScrollArea>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Comments & Notes */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Comments & Notes</CardTitle>
              <CardDescription>
                Collaborate with your team on contract review
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                {comments.map((comment) => (
                  <div key={comment.id} className="flex space-x-3">
                    <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-xs font-medium">
                      {comment.avatar}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-sm">{comment.author}</span>
                        <span className="text-xs text-muted-foreground">{comment.timestamp}</span>
                      </div>
                      <p className="text-sm mt-1">{comment.content}</p>
                    </div>
                  </div>
                ))}
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <Textarea
                  placeholder="Add a comment or note..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  rows={3}
                />
                <Button size="sm" onClick={handleAddComment}>
                  <MessageSquare className="h-3 w-3 mr-1" />
                  Add Comment
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

