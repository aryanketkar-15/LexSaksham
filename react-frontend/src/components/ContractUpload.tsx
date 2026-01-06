import React, { useState, useRef } from 'react';
import { motion } from 'motion/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Download,
  FileIcon,
  Trash2
} from 'lucide-react';
import { uploadAndAnalyze, checkBackendConnection } from '../services/api';
import { useContracts } from '../context/ContractsContext';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

const allowedFileTypes = ['.pdf', '.docx', '.doc'];
const maxFileSize = 10 * 1024 * 1024; // 10MB

export default function ContractUpload() {
  const { addContract } = useContracts();
  const navigate = useNavigate();
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);
  const fileInputRef = useRef(null);

  // Check backend connection on mount
  useEffect(() => {
    const checkConnection = async () => {
      const status = await checkBackendConnection();
      setBackendConnected(status.connected);
      if (!status.connected) {
        toast.error('Backend server is not connected. Please start the backend server.');
      }
    };
    checkConnection();
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    handleFiles(files);
  };

  const handleFiles = (files) => {
    const validFiles = files.filter(file => {
      const isValidType = allowedFileTypes.some(type => 
        file.name.toLowerCase().endsWith(type)
      );
      const isValidSize = file.size <= maxFileSize;
      
      if (!isValidType) {
        toast.error(`${file.name} is not a supported file type`);
        return false;
      }
      if (!isValidSize) {
        toast.error(`${file.name} is too large (max 10MB)`);
        return false;
      }
      return true;
    });

    const newFiles = validFiles.map(file => ({
      id: Date.now() + Math.random(),
      file,
      name: file.name,
      size: file.size,
      status: 'pending',
      progress: 0,
      type: getFileType(file.name),
      uploadedAt: new Date()
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);
    
    // Start uploading
    newFiles.forEach(fileData => uploadFile(fileData));
  };

  const getFileType = (filename) => {
    if (filename.toLowerCase().endsWith('.pdf')) return 'PDF';
    if (filename.toLowerCase().endsWith('.docx')) return 'DOCX';
    if (filename.toLowerCase().endsWith('.doc')) return 'DOC';
    return 'Unknown';
  };

  const uploadFile = async (fileData) => {
    setIsUploading(true);
    
    // Update progress for upload
    const updateProgress = (progress) => {
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === fileData.id 
            ? { ...f, progress, status: progress === 100 ? 'completed' : 'uploading' }
            : f
        )
      );
    };

    try {
      // Update status to uploading
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === fileData.id 
            ? { ...f, progress: 0, status: 'uploading' }
            : f
        )
      );

      // Simulate progress during upload (0-40%)
      const uploadProgressInterval = setInterval(() => {
        setUploadedFiles(prev => {
          const currentFile = prev.find(f => f.id === fileData.id);
          if (currentFile && currentFile.progress < 40 && currentFile.status === 'uploading') {
            return prev.map(f => 
              f.id === fileData.id 
                ? { ...f, progress: Math.min(f.progress + 5, 40), status: 'uploading' }
                : f
            );
          }
          return prev;
        });
      }, 300);

      // Upload and analyze
      console.log('Starting upload and analysis for:', fileData.name);
      
      // Update to analyzing status (40-90%)
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === fileData.id 
            ? { ...f, progress: 40, status: 'analyzing' }
            : f
        )
      );

      // Simulate progress during analysis (40-90%)
      const analysisProgressInterval = setInterval(() => {
        setUploadedFiles(prev => {
          const currentFile = prev.find(f => f.id === fileData.id);
          if (currentFile && currentFile.progress < 90 && currentFile.status === 'analyzing') {
            return prev.map(f => 
              f.id === fileData.id 
                ? { ...f, progress: Math.min(f.progress + 2, 90) }
                : f
            );
          }
          return prev;
        });
      }, 500);

      const result = await uploadAndAnalyze(fileData.file, 'user');
      console.log('Upload and analysis result:', result);
      
      // Clear progress intervals
      clearInterval(uploadProgressInterval);
      clearInterval(analysisProgressInterval);

      // Process analysis results
      const analysisResults = result.analysis_results || [];
      console.log('Analysis results received:', analysisResults.length, 'clauses');
      
      const riskLevels = analysisResults.map(r => r.risk_level?.toLowerCase() || 'low');
      const highestRisk = riskLevels.includes('critical') ? 'critical' :
                         riskLevels.includes('high') ? 'high' :
                         riskLevels.includes('medium') ? 'medium' : 'low';
      
      console.log('Highest risk level:', highestRisk);
      
      // Save contract to context/storage FIRST
      const contractId = addContract({
        name: fileData.name,
        type: fileData.type,
        risk: highestRisk,
        analysis_results: analysisResults,
        extracted_text: result.extracted_text,
        fileSize: fileData.size,
        uploadedAt: fileData.uploadedAt
      });
      
      console.log('Contract saved with ID:', contractId);

      // Update file state with analysis results AND contract ID in ONE update
      setUploadedFiles(prev => {
        const fileIndex = prev.findIndex(f => f.id === fileData.id);
        if (fileIndex === -1) {
          console.error('File not found in state:', fileData.id);
          return prev;
        }
        
        const updated = [...prev];
        updated[fileIndex] = {
          ...updated[fileIndex],
          status: 'analyzed',
          progress: 100,
          contractId: contractId,
          analysis: {
            riskLevel: highestRisk,
            clauses: analysisResults.length,
            issues: analysisResults.filter(r => 
              r.risk_level?.toLowerCase() === 'high' || 
              r.risk_level?.toLowerCase() === 'critical'
            ).length,
            results: analysisResults,
            extractedText: result.extracted_text
          }
        };
        
        console.log('✅ File updated to analyzed state:', {
          id: updated[fileIndex].id,
          name: updated[fileIndex].name,
          status: updated[fileIndex].status,
          progress: updated[fileIndex].progress,
          hasAnalysis: !!updated[fileIndex].analysis,
          contractId: updated[fileIndex].contractId,
          clauses: updated[fileIndex].analysis?.clauses
        });
        return updated;
      });

      toast.success(`${fileData.name} uploaded and analyzed successfully!`);
    } catch (error) {
      console.error('Upload/Analysis error:', error);
      const errorMessage = error.message || 'Unknown error occurred';
      toast.error(`Failed to analyze ${fileData.name}: ${errorMessage}`);
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === fileData.id 
            ? { ...f, status: 'error', progress: 0, error: errorMessage }
            : f
        )
      );
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const exportResults = (format) => {
    toast.success(`Exporting results as ${format}...`);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Upload Contracts</h1>
          <p className="text-muted-foreground">
            Upload your contract documents for AI-powered analysis and risk assessment
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={() => exportResults('PDF')}>
            <Download className="h-4 w-4 mr-2" />
            Export PDF
          </Button>
          <Button variant="outline" onClick={() => exportResults('CSV')}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Drag and drop your contract files here, or click to browse. Supports PDF, DOC, and DOCX files up to 10MB.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              isDragOver 
                ? 'border-primary bg-primary/5' 
                : 'border-muted-foreground/25 hover:border-primary/50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="flex flex-col items-center space-y-4 cursor-pointer">
              <div className={`p-4 rounded-full ${isDragOver ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                <Upload className="h-8 w-8" />
              </div>
              <div>
                <h3 className="text-lg font-medium">Drop files here or click to browse</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Supported formats: PDF, DOC, DOCX (Max 10MB per file)
                </p>
              </div>
              <Button variant={isDragOver ? 'secondary' : 'outline'}>
                Choose Files
              </Button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        </CardContent>
      </Card>

      {/* File Type Validation */}
      <Card>
        <CardHeader>
          <CardTitle>File Requirements</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="font-medium text-green-800">Supported Formats</p>
                <p className="text-sm text-green-600">PDF, DOC, DOCX</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
              <FileIcon className="h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium text-blue-800">Maximum Size</p>
                <p className="text-sm text-blue-600">10MB per file</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
              <AlertCircle className="h-5 w-5 text-purple-600" />
              <div>
                <p className="font-medium text-purple-800">Processing Time</p>
                <p className="text-sm text-purple-600">~30 seconds per file</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Uploaded Files ({uploadedFiles.length})</CardTitle>
            <CardDescription>
              Track the upload progress and analysis results for your documents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {uploadedFiles.map((fileData) => (
                <motion.div
                  key={fileData.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className="border rounded-lg p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className="p-2 bg-muted rounded">
                        <FileText className="h-6 w-6" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <h4 className="font-medium truncate">{fileData.name}</h4>
                          <Badge variant="outline">{fileData.type}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {formatFileSize(fileData.size)} â€¢ Uploaded {fileData.uploadedAt.toLocaleTimeString()}
                        </p>
                        
                        {/* Progress Bar */}
                        {(fileData.status === 'uploading' || fileData.status === 'analyzing') && (
                          <div className="mt-2">
                            <div className="flex items-center justify-between text-sm">
                              <span>
                                {fileData.status === 'uploading' 
                                  ? 'Uploading document...' 
                                  : 'Analyzing document (this may take a few minutes for large files)...'}
                              </span>
                              <span>{fileData.progress}%</span>
                            </div>
                            <Progress value={fileData.progress} className="mt-1" />
                          </div>
                        )}
                        
                        {/* Error Display */}
                        {fileData.status === 'error' && (
                          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                            <AlertCircle className="h-4 w-4 inline mr-1" />
                            Error: {fileData.error || 'Upload failed'}
                          </div>
                        )}
                        
                        {/* Pending Status */}
                        {fileData.status === 'pending' && (
                          <div className="mt-2 text-sm text-muted-foreground">
                            Waiting to start upload...
                          </div>
                        )}
                        
                        {/* Analysis Results */}
                        {fileData.status === 'analyzed' && fileData.analysis && (
                          <div className="mt-3 grid grid-cols-3 gap-4">
                            <div className="text-center">
                              <p className="text-xs text-muted-foreground">Risk Level</p>
                              <Badge className={getRiskColor(fileData.analysis.riskLevel)}>
                                {fileData.analysis.riskLevel}
                              </Badge>
                            </div>
                            <div className="text-center">
                              <p className="text-xs text-muted-foreground">Clauses Found</p>
                              <p className="text-sm font-medium">{fileData.analysis.clauses}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-xs text-muted-foreground">Issues Detected</p>
                              <p className="text-sm font-medium">{fileData.analysis.issues}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-4">
                      {fileData.status === 'completed' && (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      )}
                      {fileData.status === 'analyzed' && fileData.contractId && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => navigate(`/contracts/${fileData.contractId}`)}
                        >
                          View Details
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        onClick={() => removeFile(fileData.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload Success/Failure Notifications */}
      {uploadedFiles.some(f => f.status === 'analyzed') && (
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <p className="text-green-800 font-medium">Upload and Analysis Complete</p>
            </div>
            <p className="text-green-700 text-sm mt-1">
              All files have been successfully processed and are ready for review.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

