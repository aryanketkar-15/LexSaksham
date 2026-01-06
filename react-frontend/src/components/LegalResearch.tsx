import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import { 
  Search, 
  Scale, 
  FileText, 
  Calendar,
  BookOpen,
  ExternalLink,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { searchJudgment } from '../services/api';

export default function LegalResearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchText, setSearchText] = useState('');
  const [judgments, setJudgments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async () => {
    if (!searchText.trim()) {
      toast.error('Please enter a clause or legal text to search');
      return;
    }

    setIsLoading(true);
    setHasSearched(true);
    setSearchQuery(searchText);

    try {
      const result = await searchJudgment(searchText, 5);
      if (result.results && result.results.length > 0) {
        setJudgments(result.results);
        toast.success(`Found ${result.results.length} relevant judgment${result.results.length > 1 ? 's' : ''}`);
      } else {
        setJudgments([]);
        toast.info('No relevant judgments found. Try different keywords.');
      }
    } catch (error) {
      console.error('Search error:', error);
      toast.error(error.message || 'Failed to search judgments. Please try again.');
      setJudgments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Legal Research</h1>
          <p className="text-muted-foreground">
            Search Supreme Court judgments relevant to your legal clauses and cases
          </p>
        </div>
        <Badge variant="secondary" className="text-sm">
          <Scale className="h-3 w-3 mr-1" />
          Lawyer Access Only
        </Badge>
      </div>

      {/* Search Section */}
      <Card>
        <CardHeader>
          <CardTitle>Search Supreme Court Judgments</CardTitle>
          <CardDescription>
            Enter a clause, legal text, or case description to find relevant Supreme Court judgments
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Legal Text / Clause</label>
              <Textarea
                placeholder="Enter clause text, legal question, or case description... (e.g., 'non-compete clause', 'employment termination', 'contract breach')"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                onKeyPress={handleKeyPress}
                rows={4}
                className="resize-none"
              />
            </div>
            <Button 
              onClick={handleSearch} 
              disabled={isLoading || !searchText.trim()}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Search Judgments
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {hasSearched && (
        <Card>
          <CardHeader>
            <CardTitle>
              {isLoading ? 'Searching...' : `Search Results${searchQuery ? `: "${searchQuery}"` : ''}`}
            </CardTitle>
            <CardDescription>
              {judgments.length > 0 
                ? `Found ${judgments.length} relevant Supreme Court judgment${judgments.length > 1 ? 's' : ''}`
                : 'No judgments found for your search query'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : judgments.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">No judgments found</p>
                <p className="text-sm">Try different keywords or rephrase your search query</p>
              </div>
            ) : (
              <div className="space-y-4">
                {judgments.map((judgment, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="border rounded-lg p-6 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Scale className="h-5 w-5 text-primary" />
                          <h3 className="text-lg font-semibold">
                            {judgment.case_name || judgment.title || `Case ${index + 1}`}
                          </h3>
                          {judgment.year && (
                            <Badge variant="outline" className="ml-2">
                              <Calendar className="h-3 w-3 mr-1" />
                              {judgment.year}
                            </Badge>
                          )}
                        </div>
                        {judgment.court && (
                          <p className="text-sm text-muted-foreground mb-2">
                            {judgment.court}
                          </p>
                        )}
                      </div>
                    </div>

                    {judgment.summary && (
                      <div className="mb-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <BookOpen className="h-4 w-4 text-muted-foreground" />
                          <p className="text-sm font-medium text-muted-foreground">Summary</p>
                        </div>
                        <p className="text-sm leading-relaxed">{judgment.summary}</p>
                      </div>
                    )}

                    {judgment.relevance && (
                      <div className="mb-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <p className="text-sm font-medium text-muted-foreground">Relevance</p>
                        </div>
                        <p className="text-sm leading-relaxed text-muted-foreground">
                          {judgment.relevance}
                        </p>
                      </div>
                    )}

                    {judgment.text && (
                      <ScrollArea className="h-32 w-full border rounded p-3 bg-muted/20 mb-4">
                        <p className="text-xs leading-relaxed text-muted-foreground">
                          {judgment.text.substring(0, 500)}
                          {judgment.text.length > 500 ? '...' : ''}
                        </p>
                      </ScrollArea>
                    )}

                    {judgment.similarity_score && (
                      <div className="flex items-center justify-between pt-2 border-t">
                        <Badge variant="secondary">
                          Similarity: {(judgment.similarity_score * 100).toFixed(1)}%
                        </Badge>
                        {judgment.url && (
                          <Button variant="outline" size="sm" asChild>
                            <a href={judgment.url} target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-3 w-3 mr-1" />
                              View Full Judgment
                            </a>
                          </Button>
                        )}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Help Section */}
      {!hasSearched && (
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-blue-900">How to Use Legal Research</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm text-blue-800">
              <div className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5"></div>
                <p>Enter specific legal clauses or terms (e.g., "non-compete agreement", "employment termination")</p>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5"></div>
                <p>Search for case law related to contract disputes, employment law, or commercial agreements</p>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5"></div>
                <p>Review relevant Supreme Court judgments with summaries and relevance explanations</p>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5"></div>
                <p>Use the AI Chat to ask questions like "Show relevant Supreme Court judgments for this clause"</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}


