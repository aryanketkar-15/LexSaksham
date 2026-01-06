import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'motion/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { 
  Send, 
  Bot, 
  User, 
  Loader2,
  MessageSquare,
  Trash2,
  Sparkles
} from 'lucide-react';
import { sendChatMessage } from '../services/openrouter';
import { detectLanguage } from '../utils/languageDetection';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatBotProps {
  currentUser?: {
    role?: string;
    name?: string;
    email?: string;
  };
}

export default function ChatBot({ currentUser }: ChatBotProps) {
  const isLawyer = currentUser?.role === 'Lawyer';
  
  const initialMessage = isLawyer
    ? 'Namaste! I\'m your legal research assistant for LexSaksham, specialized in Indian law. I can help you with:\n\n• Understanding contracts under the Indian Contract Act, 1872\n• Analyzing risks and compliance with Indian laws\n• Finding relevant Supreme Court of India judgments\n• Explaining Indian case law and legal precedents\n• Providing legal research on Indian contract law\n• Compliance with Indian regulations (SEBI, RBI, GST, Companies Act)\n\nI specialize in Indian legal system, Supreme Court of India judgments, and Indian commercial law. How can I assist you today?'
    : 'Namaste! I\'m your legal assistant for LexSaksham, specialized in Indian law. I can help you:\n\n• Understand contracts under the Indian Contract Act, 1872\n• Analyze legal clauses as per Indian law\n• Assess risks and compliance with Indian regulations\n• Get guidance on contract management in Indian legal context\n• Understand Indian legal terminology and concepts\n\nI provide advice based on Indian laws, Supreme Court of India judgments, and Indian compliance requirements. How can I assist you today?';

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: initialMessage,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Convert messages to conversation history format
      const conversationHistory = messages.map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      // Detect language from user message
      const detectedLang = detectLanguage(userMessage.content);
      console.log('ChatBot: Detected language:', detectedLang);
      
      // Add India context
      if (isLawyer) {
        conversationHistory.unshift({
          role: 'system',
          content: 'lawyer_india'
        });
      } else {
        conversationHistory.unshift({
          role: 'system',
          content: 'user_india'
        });
      }

      // Send message with language detection
      const response = await sendChatMessage(userMessage.content, conversationHistory, detectedLang);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.message,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMsg = error.message || 'Failed to get response from AI. Please try again.';
      toast.error(errorMsg);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `I apologize, but I encountered an error: ${errorMsg}. Please check your API key, model availability, or try again later.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: '1',
        type: 'assistant',
        content: initialMessage,
        timestamp: new Date()
      }
    ]);
    toast.success('Chat cleared');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center space-x-2">
            <Sparkles className="h-8 w-8 text-primary" />
            <span>AI Legal Assistant</span>
          </h1>
          <p className="text-muted-foreground mt-1">
            Get instant help with contract analysis, risk assessment, and legal guidance
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={handleClearChat}
          className="flex items-center space-x-2"
        >
          <Trash2 className="h-4 w-4" />
          <span>Clear Chat</span>
        </Button>
      </div>

      {/* Chat Container */}
      <Card className="h-[calc(100vh-250px)] flex flex-col">
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <span>Chat</span>
            </CardTitle>
            <Badge variant="secondary" className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Online</span>
            </Badge>
          </div>
          <CardDescription>
            Powered by LexSaksham AI | Specialized in Indian Law & Legal System
          </CardDescription>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col p-0">
          {/* Messages Area */}
          <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
            <div className="space-y-4">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex items-start space-x-3 max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    {/* Avatar */}
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      message.type === 'user' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'bg-muted'
                    }`}>
                      {message.type === 'user' ? (
                        <User className="h-4 w-4" />
                      ) : (
                        <Bot className="h-4 w-4" />
                      )}
                    </div>
                    
                    {/* Message Content */}
                    <div className={`rounded-lg p-3 ${
                      message.type === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p className={`text-xs mt-1 ${
                        message.type === 'user' 
                          ? 'text-primary-foreground/70' 
                          : 'text-muted-foreground'
                      }`}>
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
              
              {/* Loading Indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-start space-x-3"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-muted rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">Thinking...</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t p-4">
            <div className="flex items-center space-x-2">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about contracts, legal clauses, or risk assessment..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button 
                onClick={handleSend} 
                disabled={!input.trim() || isLoading}
                size="icon"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

