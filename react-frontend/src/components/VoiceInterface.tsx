import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { toast } from 'sonner';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Play, 
  Pause, 
  RotateCcw,
  Languages,
  Settings,
  MessageSquare,
  Waveform,
  FileText,
  Search,
  Clock,
  User,
  Bot,
  Send,
  Type,
  Square
} from 'lucide-react';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { sendChatMessage } from '../services/openrouter';
import { detectLanguage, getSpeechRecognitionLang, getSpeechSynthesisLang } from '../utils/languageDetection';

const voiceCommands = [
  { command: "Search for employment contracts", category: "Search", example: true },
  { command: "Show high risk contracts", category: "Filter", example: true },
  { command: "Upload new contract", category: "Action", example: true },
  { command: "Analyze contract risk", category: "Analysis", example: true },
  { command: "Generate contract summary", category: "Summary", example: true },
  { command: "Export contract list", category: "Export", example: true },
  { command: "What are the compliance issues?", category: "Query", example: true },
  { command: "Schedule contract review", category: "Schedule", example: true }
];

const initialConversationHistory = [
  {
    id: 1,
    type: 'user',
    content: 'Show me all high-risk contracts from the last month',
    timestamp: '2 minutes ago',
    language: 'en'
  },
  {
    id: 2,
    type: 'assistant',
    content: 'I found 7 high-risk contracts uploaded in the last month. These contracts may have issues under the Indian Contract Act, 1872. Here are the details: Employment Agreement with excessive termination clauses (may violate Indian labor laws), Vendor Agreement with unclear liability terms (non-compliance with Indian commercial law), and 5 others. Would you like me to prioritize them by risk level as per Indian legal standards?',
    timestamp: '2 minutes ago',
    language: 'en',
    actions: ['View Contracts', 'Export List', 'Analyze Further']
  },
  {
    id: 3,
    type: 'user',
    content: 'Yes, prioritize by risk level',
    timestamp: '1 minute ago',
    language: 'en'
  },
  {
    id: 4,
    type: 'assistant',
    content: 'I\'ve sorted the contracts by risk level under Indian law. The highest priority is the Partnership Agreement with StartupXYZ (Critical Risk) due to unclear termination clauses that may violate the Indian Partnership Act, 1932, and excessive penalty terms that may be unenforceable under Section 74 of the Indian Contract Act. Shall I open this contract for detailed analysis with Indian legal context?',
    timestamp: '1 minute ago',
    language: 'en',
    actions: ['Open Contract', 'View Analysis', 'Next Contract']
  }
];

export default function VoiceInterface() {
  const navigate = useNavigate();
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const [conversationHistory, setConversationHistory] = useState(initialConversationHistory);
  const [textInput, setTextInput] = useState('');
  const [inputMode, setInputMode] = useState<'voice' | 'text'>('voice');

  // Initialize Web Speech API
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Load voices when available (for text-to-speech)
      const loadVoices = () => {
        if ('speechSynthesis' in window) {
          window.speechSynthesis.getVoices();
        }
      };
      
      // Chrome loads voices asynchronously
      if ('speechSynthesis' in window) {
        loadVoices();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
          window.speechSynthesis.onvoiceschanged = loadVoices;
        }
      }
      
      // Check for browser support
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        const recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = false;
        recognitionInstance.interimResults = true;
        // Support multilingual recognition - use appropriate language code
        recognitionInstance.lang = getSpeechRecognitionLang(selectedLanguage);
        
        recognitionInstance.onstart = () => {
          setIsListening(true);
          setCurrentTranscript('Listening...');
        };
        
        recognitionInstance.onresult = (event: any) => {
          let interimTranscript = '';
          let finalTranscript = '';
          
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalTranscript += transcript + ' ';
            } else {
              interimTranscript += transcript;
            }
          }
          
          setCurrentTranscript(finalTranscript || interimTranscript);
          
          if (finalTranscript) {
            setIsListening(false);
            setIsProcessing(true);
            processVoiceCommand(finalTranscript.trim());
          }
        };
        
        recognitionInstance.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
          setIsListening(false);
          
          if (event.error === 'no-speech') {
            toast.error('No speech detected. Please try again.');
          } else if (event.error === 'not-allowed') {
            toast.error('Microphone permission denied. Please enable microphone access.');
          } else {
            toast.error(`Speech recognition error: ${event.error}`);
          }
        };
        
        recognitionInstance.onend = () => {
          setIsListening(false);
        };
        
        setRecognition(recognitionInstance);
      } else {
        console.warn('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
      }
    }
    
    // Cleanup function
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [selectedLanguage]);
  
  // Cleanup recognition on unmount
  useEffect(() => {
    return () => {
      if (recognition) {
        recognition.stop();
      }
    };
  }, [recognition]);

  const startListening = () => {
    if (!voiceEnabled) {
      toast.error('Voice interface is disabled');
      return;
    }
    
    if (!recognition) {
      toast.error('Speech recognition not available. Please use a supported browser.');
      return;
    }
    
    try {
      setCurrentTranscript('');
      recognition.start();
    } catch (error) {
      console.error('Error starting recognition:', error);
      toast.error('Failed to start voice recognition');
    }
  };

  const stopListening = () => {
    if (recognition) {
      recognition.stop();
    }
    setIsListening(false);
    setCurrentTranscript('');
  };

  const handleStop = () => {
    // Stop voice recognition if listening
    if (isListening) {
      stopListening();
      toast.info('Voice recognition stopped');
    }
    
    // Stop text-to-speech if speaking
    if (isSpeaking && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      toast.info('Speech stopped');
    }
    
    // Note: Processing can't be stopped mid-request, but we can clear the transcript
    if (isProcessing) {
      setCurrentTranscript('');
      toast.info('Current operation will complete, but new commands are stopped');
    }
  };

  const processVoiceCommand = async (command: string) => {
    try {
      console.log('VoiceInterface: Processing command:', command);
      
      // Add user message to conversation
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: command,
        timestamp: 'Just now',
        language: selectedLanguage
      };
      
      // Update conversation history with user message
      const updatedHistory = [...conversationHistory, userMessage];
      setConversationHistory(updatedHistory);
      
      // Process command and generate response using Gemini AI
      // Pass the updated history (excluding the current command since sendChatMessage adds it)
      const response = await generateAIResponse(command, updatedHistory);
      
      console.log('VoiceInterface: Got response from AI:', response.text?.substring(0, 100));
      
      // Add assistant response to conversation
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.text,
        timestamp: 'Just now',
        language: selectedLanguage,
        actions: response.actions || []
      };
      
      setConversationHistory((prev: any[]) => [...prev, assistantMessage]);
      
      setIsProcessing(false);
      
      // Execute any actions ONLY if user explicitly requested navigation
      // Don't auto-navigate based on AI response content
      if (response.action && response.action.startsWith('navigate_')) {
        const lowerCommand = command.toLowerCase();
        // Only navigate if user explicitly asked to go somewhere
        const shouldNavigate = 
          lowerCommand.includes('go to') || 
          lowerCommand.includes('open') || 
          lowerCommand.includes('show me') ||
          lowerCommand.includes('navigate to') ||
          lowerCommand.includes('take me to') ||
          lowerCommand.includes('view') && (lowerCommand.includes('analytics') || lowerCommand.includes('dashboard') || lowerCommand.includes('contracts'));
        
        if (shouldNavigate) {
          executeAction(response.action);
        }
      }
      
      // Speak the response AFTER displaying it (with small delay for UI update)
      if (response.text && voiceEnabled) {
        setTimeout(() => {
          speak(response.text);
        }, 300);
      }
    } catch (error: any) {
      console.error('VoiceInterface: Error processing voice command:', error);
      setIsProcessing(false);
      
      const errorMessage = error.message || 'Failed to process command. Please try again.';
      toast.error(errorMessage);
      
      // Add error message to conversation with helpful info
      const errorResponse = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `I apologize, but I encountered an error: ${errorMessage}. This might be due to a network issue or API service problem. Please check your connection and try again.`,
        timestamp: 'Just now',
        language: selectedLanguage,
        actions: ['Try Again']
      };
      setConversationHistory((prev: any[]) => [...prev, errorResponse]);
    }
  };

  const generateAIResponse = async (command: string, currentHistory?: any[]): Promise<{text: string, actions?: string[], action?: string}> => {
    try {
      console.log('VoiceInterface: Generating AI response for command:', command);
      
      // Use provided history or fallback to conversationHistory state
      // Exclude the last message (current command) since sendChatMessage will add it
      const historyToUse = currentHistory || conversationHistory;
      const historyForAPI = historyToUse.slice(0, -1).map((msg: any) => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      // Detect language from user command
      const detectedLang = detectLanguage(command);
      console.log('VoiceInterface: Detected language:', detectedLang);
      console.log('VoiceInterface: Sending to Gemini with history:', historyForAPI.length, 'messages');

      // Use OpenRouter API to get AI response from Gemini with language detection
      const response = await sendChatMessage(command, historyForAPI, detectedLang);
      
      console.log('VoiceInterface: Received response from Gemini:', response.message?.substring(0, 100));
      
      if (!response || !response.message) {
        throw new Error('No response received from AI service');
      }
      
      // Extract actions ONLY from user's explicit command, NOT from AI response
      // This prevents unwanted navigation when AI mentions words like "analyze" in explanations
      const actions: string[] = [];
      let action: string | undefined;
      
      const lowerCommand = command.toLowerCase();
      
      // Only detect actions if the USER explicitly requested navigation
      // Use strict matching to avoid false positives
      if (lowerCommand.includes('upload') && (lowerCommand.includes('go to') || lowerCommand.includes('open') || lowerCommand.includes('show'))) {
        actions.push('Go to Upload');
        action = 'navigate_upload';
      } else if ((lowerCommand.includes('analytics') || lowerCommand.includes('analysis')) && 
                 (lowerCommand.includes('go to') || lowerCommand.includes('open') || lowerCommand.includes('show') || lowerCommand.includes('view'))) {
        actions.push('View Analytics');
        action = 'navigate_analytics';
      } else if (lowerCommand.includes('dashboard') && 
                 (lowerCommand.includes('go to') || lowerCommand.includes('open') || lowerCommand.includes('show') || lowerCommand.includes('main'))) {
        actions.push('Go to Dashboard');
        action = 'navigate_dashboard';
      } else if (lowerCommand.includes('contracts') && 
                 (lowerCommand.includes('list') || lowerCommand.includes('view') || lowerCommand.includes('show') || lowerCommand.includes('go to'))) {
        actions.push('View Contracts');
        action = 'navigate_contracts';
      } else if ((lowerCommand.includes('high risk') || lowerCommand.includes('risky')) && 
                 (lowerCommand.includes('show') || lowerCommand.includes('view') || lowerCommand.includes('filter'))) {
        actions.push('View High Risk Contracts');
        action = 'filter_high_risk';
      }
      
      // Return response with actions only if user explicitly requested navigation
      // This ensures no unwanted navigation happens
      return {
        text: response.message,
        actions: actions.length > 0 ? actions : undefined,
        action: action
      };
    } catch (error: any) {
      console.error('VoiceInterface: Error getting AI response from Gemini:', error);
      
      // Only show error message, don't return mock responses
      // The error will be caught in processVoiceCommand and shown to user
      throw new Error(
        error.message || 
        'Failed to connect to AI service. Please check your internet connection and try again.'
      );
    }
  };

  const speak = (text: string) => {
    if (!voiceEnabled) return;
    
    // Use Web Speech API for text-to-speech
    if ('speechSynthesis' in window) {
      // Stop any ongoing speech
      window.speechSynthesis.cancel();
      
      // Truncate very long text to prevent speech synthesis errors
      // Split into sentences and limit to first few sentences if too long
      let textToSpeak = text;
      if (text.length > 500) {
        const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
        textToSpeak = sentences.slice(0, 5).join(' '); // First 5 sentences
        if (text.length > textToSpeak.length) {
          textToSpeak += '...';
        }
      }
      
      // Detect language from text to speak in appropriate language
      const textLanguage = detectLanguage(textToSpeak);
      const speechLang = getSpeechSynthesisLang(textLanguage);
      
      // Small delay to ensure speech synthesis is ready
      setTimeout(() => {
        try {
          const utterance = new SpeechSynthesisUtterance(textToSpeak);
          utterance.lang = speechLang; // Use detected language (en-IN or hi-IN)
          utterance.rate = 0.9; // Slightly slower for clarity
          utterance.pitch = 1.0;
          utterance.volume = 1.0;
          
          utterance.onstart = () => {
            setIsSpeaking(true);
          };
          
          utterance.onend = () => {
            setIsSpeaking(false);
          };
          
          utterance.onerror = (event: any) => {
            console.error('Speech synthesis error:', event);
            setIsSpeaking(false);
            // Don't show error toast for common issues, just log
            if (event.error !== 'interrupted' && event.error !== 'canceled') {
              console.warn('Speech synthesis error:', event.error);
            }
          };
          
          // Get available voices and prefer language-specific voice
          const voices = window.speechSynthesis.getVoices();
          let preferredVoice = null;
          
          if (textLanguage === 'hi') {
            // Prefer Hindi voice
            preferredVoice = voices.find(voice => 
              voice.lang.includes('hi-IN') || 
              voice.lang.includes('hi') ||
              voice.name.toLowerCase().includes('hindi')
            );
          }
          
          if (!preferredVoice) {
            // Fallback to Indian English or any English voice
            preferredVoice = voices.find(voice => 
              voice.lang.includes('en-IN') || 
              voice.name.toLowerCase().includes('india') ||
              voice.name.toLowerCase().includes('indian')
            );
          }
          
          if (!preferredVoice && voices.length > 0) {
            // Final fallback to first available voice matching language
            preferredVoice = voices.find(voice => voice.lang.startsWith(textLanguage === 'hi' ? 'hi' : 'en')) || voices[0];
          }
          
          if (preferredVoice) {
            utterance.voice = preferredVoice;
          }
          
          window.speechSynthesis.speak(utterance);
        } catch (error) {
          console.error('Error creating speech utterance:', error);
          setIsSpeaking(false);
        }
      }, 100);
    } else {
      console.warn('Text-to-speech is not supported in your browser');
    }
  };

  const handleTextSubmit = () => {
    if (!textInput.trim() || isProcessing) return;
    
    const command = textInput.trim();
    setTextInput('');
    setCurrentTranscript(command);
    setIsProcessing(true);
    processVoiceCommand(command);
  };

  const executeAction = (action: string) => {
    // Handle navigation actions - use React Router instead of window.location
    if (action.startsWith('navigate_')) {
      const route = action.replace('navigate_', '');
      // Use React Router navigate to avoid page reload and auth issues
      if (route === 'upload') {
        navigate('/upload');
      } else if (route === 'analytics') {
        navigate('/analytics');
      } else if (route === 'dashboard') {
        navigate('/dashboard');
      } else if (route === 'contracts') {
        navigate('/contracts');
      } else {
        navigate(`/${route}`);
      }
      toast.success(`Navigating to ${route}`);
      return;
    }
    
    // Handle filter actions
    if (action.startsWith('filter_')) {
      toast.success(`Applying filter: ${action}`);
      // You can add actual filtering logic here
      return;
    }
    
    // Handle search actions
    if (action.startsWith('search_')) {
      const searchTerm = action.replace('search_', '');
      toast.success(`Searching for: ${searchTerm}`);
      // Navigate to contracts page with search
      navigate('/contracts', { state: { searchTerm } });
      return;
    }
    
    // Handle export actions
    if (action === 'export_contracts') {
      toast.success('Preparing contract export...');
      // You can add actual export logic here
      return;
    }
    
    toast.success(`Executing: ${action}`);
  };

  const getLanguageLabel = (code) => {
    const languages = {
      'en': 'English',
      'hi': 'à¤¹à¤¿à¤‚à¤¦à¥€ (Hindi)',
      'es': 'EspaÃ±ol',
      'fr': 'FranÃ§ais'
    };
    return languages[code] || code;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Voice Assistant (India)</h1>
          <p className="text-muted-foreground">
            Interact with your contracts using natural language commands - Specialized in Indian law and legal system
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Label htmlFor="voice-enabled">Voice Enabled</Label>
          <Switch 
            id="voice-enabled"
            checked={voiceEnabled}
            onCheckedChange={setVoiceEnabled}
          />
        </div>
      </div>

      {/* Voice Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Mic className="h-5 w-5" />
            <span>Voice Control (India)</span>
          </CardTitle>
          <CardDescription>
            Click the microphone to start voice interaction. I understand Indian legal context, Supreme Court of India judgments, and Indian contract law.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center space-y-6">
            {/* Microphone Button */}
            <motion.div
              animate={{ 
                scale: isListening ? [1, 1.1, 1] : 1,
                boxShadow: isListening ? '0 0 20px rgba(59, 130, 246, 0.5)' : '0 0 0px rgba(59, 130, 246, 0)'
              }}
              transition={{ 
                repeat: isListening ? Infinity : 0,
                duration: 1.5
              }}
            >
              <Button
                size="lg"
                className={`w-20 h-20 rounded-full ${
                  isListening 
                    ? 'bg-red-500 hover:bg-red-600' 
                    : 'bg-primary hover:bg-primary/90'
                }`}
                onClick={isListening ? stopListening : startListening}
                disabled={!voiceEnabled || isProcessing}
              >
                {isListening ? <MicOff className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
              </Button>
            </motion.div>

            {/* Stop Button - Show when listening, speaking, or processing */}
            {(isListening || isSpeaking || isProcessing) && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2 }}
              >
                <Button
                  size="lg"
                  variant="destructive"
                  onClick={handleStop}
                  className="flex items-center space-x-2"
                >
                  <Square className="h-5 w-5" />
                  <span>Stop</span>
                </Button>
              </motion.div>
            )}

            {/* Status */}
            <div className="text-center space-y-2">
              {isListening && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center space-x-2 text-red-600"
                >
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="font-medium">Listening...</span>
                </motion.div>
              )}
              
              {isProcessing && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center space-x-2 text-blue-600"
                >
                  <div className="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  <span className="font-medium">Processing...</span>
                </motion.div>
              )}
              
              {isSpeaking && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center space-x-2 text-green-600"
                >
                  <Volume2 className="h-4 w-4" />
                  <span className="font-medium">Speaking...</span>
                </motion.div>
              )}
              
              {!isListening && !isProcessing && !isSpeaking && (
                <span className="text-muted-foreground">
                  {voiceEnabled ? 'Ready to listen' : 'Voice interface disabled'}
                </span>
              )}
            </div>

            {/* Current Transcript */}
            {currentTranscript && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-muted rounded-lg max-w-md text-center"
              >
                <p className="text-sm text-muted-foreground">You said:</p>
                <p className="font-medium">{currentTranscript}</p>
              </motion.div>
            )}

            {/* Language Selection */}
            <div className="flex items-center space-x-4">
              <Languages className="h-4 w-4 text-muted-foreground" />
              <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="hi">à¤¹à¤¿à¤‚à¤¦à¥€ (Hindi)</SelectItem>
                  <SelectItem value="es">EspaÃ±ol</SelectItem>
                  <SelectItem value="fr">FranÃ§ais</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Input Mode Toggle */}
            <div className="flex items-center space-x-4 pt-4 border-t">
              <div className="flex items-center space-x-2">
                <Label>Input Mode:</Label>
                <div className="flex items-center space-x-2 border rounded-lg p-1">
                  <Button
                    variant={inputMode === 'voice' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setInputMode('voice')}
                    className="flex items-center space-x-1"
                  >
                    <Mic className="h-3 w-3" />
                    <span>Voice</span>
                  </Button>
                  <Button
                    variant={inputMode === 'text' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setInputMode('text')}
                    className="flex items-center space-x-1"
                  >
                    <Type className="h-3 w-3" />
                    <span>Text</span>
                  </Button>
                </div>
              </div>
            </div>

            {/* Text Input (when in text mode) */}
            {inputMode === 'text' && (
              <div className="pt-4 space-y-2 w-full max-w-md">
                <Textarea
                  placeholder="Type your command here..."
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleTextSubmit();
                    }
                  }}
                  rows={3}
                  className="resize-none"
                />
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">
                    Press Enter to send, Shift+Enter for new line
                  </p>
                  <Button
                    onClick={handleTextSubmit}
                    disabled={!textInput.trim() || isProcessing}
                    size="sm"
                    className="flex items-center space-x-1"
                  >
                    <Send className="h-3 w-3" />
                    <span>Send</span>
                  </Button>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Voice Commands & Conversation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Available Commands */}
        <Card>
          <CardHeader>
            <CardTitle>Available Voice Commands (India)</CardTitle>
            <CardDescription>
              Try these natural language commands. I understand Indian legal context, Indian Contract Act, and Supreme Court of India judgments.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {voiceCommands.map((cmd, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => processVoiceCommand(cmd.command)}
                >
                  <div>
                    <p className="font-medium text-sm">"{cmd.command}"</p>
                    <Badge variant="outline" className="text-xs mt-1">
                      {cmd.category}
                    </Badge>
                  </div>
                  <Button size="sm" variant="ghost">
                    Try
                  </Button>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Conversation History */}
        <Card>
          <CardHeader>
            <CardTitle>Conversation History</CardTitle>
            <CardDescription>
              Recent voice interactions with AI responses based on Indian law and legal precedents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              <div className="space-y-4">
                {conversationHistory.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[80%] p-3 rounded-lg ${
                      message.type === 'user' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'bg-muted'
                    }`}>
                      <div className="flex items-center space-x-2 mb-1">
                        {message.type === 'user' ? (
                          <User className="h-3 w-3" />
                        ) : (
                          <Bot className="h-3 w-3" />
                        )}
                        <span className="text-xs opacity-70">{message.timestamp}</span>
                      </div>
                      <p className="text-sm">{message.content}</p>
                      
                      {message.actions && (
                        <div className="flex flex-wrap gap-2 mt-3">
                          {message.actions.map((action, idx) => (
                            <Button
                              key={idx}
                              size="sm"
                              variant="outline"
                              className="text-xs"
                              onClick={() => executeAction(action)}
                            >
                              {action}
                            </Button>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Voice Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Voice Settings</CardTitle>
          <CardDescription>
            Configure voice recognition and text-to-speech preferences
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label>Speech Speed</Label>
              <Select defaultValue="normal">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="slow">Slow</SelectItem>
                  <SelectItem value="normal">Normal</SelectItem>
                  <SelectItem value="fast">Fast</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Voice</Label>
              <Select defaultValue="female">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="female">Female</SelectItem>
                  <SelectItem value="male">Male</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Sensitivity</Label>
              <Select defaultValue="medium">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <Separator className="my-6" />
          
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Auto-play responses</p>
              <p className="text-sm text-muted-foreground">Automatically speak AI responses</p>
            </div>
            <Switch defaultChecked />
          </div>
        </CardContent>
      </Card>

      {/* TTS Playback Control */}
      {isSpeaking && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-6 right-6 bg-card border rounded-lg shadow-lg p-4 min-w-64"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Volume2 className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium">Speaking...</span>
            </div>
            <Button size="sm" variant="ghost" onClick={() => setIsSpeaking(false)}>
              <VolumeX className="h-3 w-3" />
            </Button>
          </div>
          <div className="mt-2">
            <div className="flex space-x-1">
              {[...Array(5)].map((_, i) => (
                <motion.div
                  key={i}
                  className="w-1 bg-green-500 rounded-full"
                  animate={{
                    height: [4, 12, 4],
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 0.5,
                    delay: i * 0.1,
                  }}
                />
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

