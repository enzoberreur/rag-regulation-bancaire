import { useState, useRef, useEffect, useCallback } from 'react';
import { ChatMessage } from './ChatMessage';
import { DocumentUpload } from './DocumentUpload';
import { LoadingAnimation } from './LoadingAnimation';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Send, Paperclip } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from './ui/sheet';
import { Badge } from './ui/badge';
import { streamChatMessage, type ChatMessage as ApiChatMessage } from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
}

interface Citation {
  id: string;
  text: string;
  source: string;
  url?: string;
}

interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  uploadedAt: Date;
  type: 'regulation' | 'policy' | 'document';
}

interface ChatInterfaceProps {
  sessionId: string;
  messages: Message[];
  onUpdateMessages: (messages: Message[]) => void;
  onUpdateMetrics: (metrics: any) => void;
  documents: UploadedDocument[];
  onDocumentUpload: (doc: UploadedDocument) => void;
  onDocumentRemove?: (id: string) => void;
}


export function ChatInterface({ sessionId, messages, onUpdateMessages, onUpdateMetrics, documents, onDocumentUpload, onDocumentRemove }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    const updatedMessages = [...messages, userMessage];
    onUpdateMessages(updatedMessages);
    const userInput = input;
    setInput('');
    setIsLoading(true);

    const startTime = Date.now();
    
    // Create a placeholder message for streaming
    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      citations: [],
      timestamp: new Date()
    };

    onUpdateMessages([...updatedMessages, assistantMessage]);
    setStreamingMessageId(assistantMessageId);

    // Abort any ongoing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      // Convert messages to API format
      const chatHistory: ApiChatMessage[] = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
      }));

      // Stream the response from backend
      let streamedContent = '';
      let citations: Citation[] = [];
      let metricsReceived = false;
      
      for await (const chunk of streamChatMessage(
        {
          message: userInput,
          session_id: sessionId,
          history: chatHistory,
        },
        abortControllerRef.current?.signal
      )) {
        if (abortControllerRef.current?.signal.aborted) break;
        
        // Try to parse JSON chunks (citations or metrics)
        let isJsonChunk = false;
        try {
          // Clean chunk before parsing (remove any SSE prefix if present)
          let cleanChunkForParsing = chunk.trim();
          if (cleanChunkForParsing.startsWith('data: ')) {
            cleanChunkForParsing = cleanChunkForParsing.slice(6).trim();
          }
          
          const parsed = JSON.parse(cleanChunkForParsing);
          
          if (parsed.type === 'citations' && parsed.data) {
            citations = parsed.data.map((c: any) => ({
              id: c.id || String(Math.random()),
              text: c.text || c.source || 'Citation',
              source: c.source || 'Document',
              url: c.url,
            }));
            console.log('📚 Citations received:', citations);
            // Update message with citations
            onUpdateMessages([
              ...updatedMessages,
              { ...assistantMessage, content: streamedContent, citations }
            ]);
            isJsonChunk = true;
            continue;
          }
          
          if (parsed.type === 'metrics' && parsed.data) {
            // Update metrics with real values from backend
            const backendMetrics = parsed.data;
            const latency = Date.now() - startTime;
            const cost = typeof backendMetrics.cost === 'number' ? backendMetrics.cost : parseFloat(backendMetrics.cost) || 0;
            const tokensUsed = typeof backendMetrics.tokens_used === 'number' ? backendMetrics.tokens_used : parseInt(backendMetrics.tokens_used) || 0;
            const citationsCount = typeof backendMetrics.citations_count === 'number' ? backendMetrics.citations_count : parseInt(backendMetrics.citations_count) || 0;
            const averageSimilarityScore = typeof backendMetrics.average_similarity_score === 'number' ? backendMetrics.average_similarity_score : parseFloat(backendMetrics.average_similarity_score) || 0;
            
            console.log('💰 Metrics received:', {
              cost,
              tokensUsed,
              citationsCount,
              averageSimilarityScore,
              raw: backendMetrics
            });
            
            onUpdateMetrics({
              latency,
              errors: 0,
              cost,
              tokensUsed,
              citationsCount,
              averageSimilarityScore
            });
            metricsReceived = true;
            isJsonChunk = true;
            continue;
          }
        } catch (e) {
          // Not JSON, treat as text content
          // Only log if it looks like it might be JSON to avoid spam
          if (chunk.trim().startsWith('{')) {
            console.debug('Failed to parse as JSON:', chunk.substring(0, 100));
          }
        }
        
        // Skip JSON chunks (they should have been handled above)
        if (isJsonChunk) continue;
        
        // Skip chunks that look like JSON (citations or metrics that weren't parsed)
        // This handles partial JSON chunks that might leak through
        const trimmedChunk = chunk.trim();
        
        // Check for JSON patterns more thoroughly
        const looksLikeJson = trimmedChunk.startsWith('{') && (
          trimmedChunk.includes('"type"') || 
          trimmedChunk.includes('"citations"') || 
          trimmedChunk.includes('"metrics"') ||
          trimmedChunk.includes('"tokens_used"') ||
          trimmedChunk.includes('"cost"') ||
          trimmedChunk.includes('"data"') ||
          trimmedChunk.includes('"id"') ||
          trimmedChunk.includes('"source"')
        );
        
        if (looksLikeJson) {
          continue;
        }
        
        // Skip [DONE] marker
        if (trimmedChunk === '[DONE]') continue;
        
        // Backend sends formatted text with encoded newlines (to survive SSE chunking)
        let cleanChunk = chunk;
        
        // Remove SSE prefix if present
        if (cleanChunk.startsWith('data: ')) {
          cleanChunk = cleanChunk.slice(6);
        }
        
        // Skip truly empty chunks
        if (cleanChunk.trim() === '') continue;
        
        // Accumulate chunks (SSE splits the content into multiple pieces)
        streamedContent += cleanChunk;
        onUpdateMessages([
          ...updatedMessages,
          { ...assistantMessage, content: streamedContent, citations }
        ]);
      }
      
      // Apply final cleanup ONCE after streaming is complete
      // This ensures smooth streaming without visual jumps
      let finalContent = streamedContent;
      
      // More aggressive JSON removal - match any JSON-like structure
      // Remove citations JSON (can be multi-line or single line)
      finalContent = finalContent.replace(/\{"type":\s*"citations",\s*"data":\s*\[[^\]]*\]\}/gs, '');
      finalContent = finalContent.replace(/\{"type":\s*"metrics",\s*"data":\s*\{[^}]*\}\}/gs, '');
      // Remove any remaining JSON-like patterns
      finalContent = finalContent.replace(/\{[^{}]*"type"[^{}]*"citations"[^{}]*\}/gs, '');
      finalContent = finalContent.replace(/\{[^{}]*"type"[^{}]*"metrics"[^{}]*\}/gs, '');
      finalContent = finalContent.replace(/\[DONE\]/g, '');
      
      // Remove common source mention patterns (the frontend handles citations separately)
      finalContent = finalContent.replace(/\*\*Sources?\s*:\*\*/gi, '');
      finalContent = finalContent.replace(/Sources?\s*:\s*/gi, '');
      finalContent = finalContent.replace(/\(Source:\s*[^)]+\)/gi, '');
      finalContent = finalContent.replace(/Source:\s*[^\n]+/gi, '');
      
      // Remove ALL "data:" patterns aggressively
      // Decode the newline markers sent by backend
      // Backend encodes newlines to survive SSE chunking, we decode them here
      finalContent = finalContent.replace(/<<<BLANK_LINE>>>/g, '\n\n');
      finalContent = finalContent.replace(/<<<LINE_BREAK>>>/g, '\n');
      finalContent = finalContent.trim();
      
      // Final update with cleaned content and citations (only once at the end)
      onUpdateMessages([
        ...updatedMessages,
        { ...assistantMessage, content: finalContent, citations }
      ]);

      const latency = Date.now() - startTime;
      
      setIsLoading(false);
      setStreamingMessageId(null);

      // If metrics weren't received from backend, estimate them
      if (!metricsReceived) {
        const estimatedTokens = Math.floor(streamedContent.length / 4);
        const estimatedCost = (estimatedTokens / 1000) * 0.00015;
        onUpdateMetrics({
          latency,
          errors: 0,
          cost: estimatedCost,
          tokensUsed: estimatedTokens
        });
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setIsLoading(false);
      setStreamingMessageId(null);
      
      // Show error message to user
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content: error instanceof Error 
          ? `Sorry, an error occurred: ${error.message}. Please make sure the backend is running and try again.`
          : 'Sorry, an error occurred while processing your request. Please make sure the backend is running and try again.',
        timestamp: new Date()
      };
      onUpdateMessages([...updatedMessages, errorMessage]);
      
      // Update metrics with error
      onUpdateMetrics({
        latency: Date.now() - startTime,
        errors: 1,
        cost: 0,
        tokensUsed: 0
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col flex-1 bg-white relative overflow-hidden">
      <div className="flex-1 overflow-y-auto px-8" ref={scrollRef}>
        <div className="max-w-4xl mx-auto py-8 space-y-8">
          {messages.length === 0 ? (
            <div className="flex flex-col items-start justify-start h-full py-20">
              <div className="w-16 h-16 rounded-2xl bg-[#E6F0FF] flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-[#0066FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h2 className="text-neutral-900 mb-2 text-2xl font-semibold">Welcome to HexaBank Compliance Assistant</h2>
              <p className="text-sm text-neutral-500 max-w-2xl mb-6">
                Get instant answers about regulatory compliance, banking policies, and risk management guidelines. Upload your documents and ask questions to receive AI-powered analysis with relevant citations.
              </p>
              
              {/* Example prompts */}
              <div className="mt-4 max-w-2xl space-y-3">
                <div className="flex items-center gap-2 mb-3">
                  <svg className="w-4 h-4 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <span className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Try asking</span>
                </div>
                <div 
                  className="p-4 bg-white border border-neutral-200 rounded-lg hover:border-[#0066FF]/30 hover:shadow-sm transition-all cursor-pointer"
                  onClick={() => setInput("How do the Minimum Requirement for own funds and Eligible Liabilities (MREL) calibration and the capital buffer framework (Conservation Buffer, G-SIB buffer, Systemic Risk Buffer) interact for a French Global Systemically Important Bank (G-SIB)? Specifically, explain how a breach of the combined buffer requirement could impact the bank's ability to meet its MREL, including the M-MDA (Maximum Distributable Amount) restrictions.")}
                >
                  <p className="text-sm text-neutral-600 leading-relaxed">
                    How do the <span className="font-medium text-neutral-700">MREL calibration and capital buffer framework</span> interact for a French <span className="font-medium text-neutral-700">G-SIB</span>? Explain M-MDA restrictions impact.
                  </p>
                </div>
                <div 
                  className="p-4 bg-white border border-neutral-200 rounded-lg hover:border-[#0066FF]/30 hover:shadow-sm transition-all cursor-pointer"
                  onClick={() => setInput("Explain the complete methodology for calculating the Common Equity Tier 1 (CET1) ratio according to CRD4, including: (a) which capital instruments qualify as CET1 under Article 26 to 31, (b) the regulatory adjustments and deductions that must be applied (intangible assets, deferred tax assets, prudential filters), (c) how the ratio differs between individual and consolidated levels, and (d) the minimum CET1 ratio requirements including buffers for French banks.")}
                >
                  <p className="text-sm text-neutral-600 leading-relaxed">
                    Explain the <span className="font-medium text-neutral-700">CET1 ratio calculation</span> methodology including capital instruments, <span className="font-medium text-neutral-700">regulatory adjustments</span>, and minimum requirements.
                  </p>
                </div>
                <div 
                  className="p-4 bg-white border border-neutral-200 rounded-lg hover:border-[#0066FF]/30 hover:shadow-sm transition-all cursor-pointer"
                  onClick={() => setInput("Detail the Total Loss-Absorbing Capacity (TLAC) requirements for French G-SIBs under CRD4. Include: (a) the minimum TLAC ratio expressed as a percentage of risk-weighted assets (RWA) and leverage ratio exposure, (b) which liabilities qualify as TLAC-eligible (subordination requirements, remaining maturity, contractual features), (c) how TLAC interacts with MREL calibration, and (d) the transition timeline and exemptions for specific instruments.")}
                >
                  <p className="text-sm text-neutral-600 leading-relaxed">
                    Detail the <span className="font-medium text-neutral-700">TLAC requirements for French G-SIBs</span>, including eligible liabilities and <span className="font-medium text-neutral-700">TLAC/MREL interaction</span>.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            messages.map(message => (
              <ChatMessage 
                key={message.id} 
                message={message} 
                isStreaming={message.id === streamingMessageId}
              />
            ))
          )}
          
          {isLoading && !streamingMessageId && (
            <div className="flex gap-3 items-center">
              <LoadingAnimation variant="wave" size="md" color="#0066FF" />
              <span className="text-sm text-neutral-500 font-medium">Analyzing regulations...</span>
            </div>
          )}
        </div>
      </div>

      <div className="px-8 py-6 relative flex-shrink-0">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <Sheet>
              <SheetTrigger asChild>
                <Button 
                  variant="outline"
                  size="icon"
                  className="relative border-neutral-200 hover:border-[#0066FF] hover:bg-[#E6F0FF] transition-smooth group"
                >
                  <Paperclip className="w-4 h-4 text-neutral-600 group-hover:text-[#0066FF] transition-colors" />
                  {documents.length > 0 && (
                    <Badge className="absolute -top-1.5 -right-1.5 h-5 w-5 flex items-center justify-center p-0 bg-[#0066FF] text-white text-xs">
                      {documents.length}
                    </Badge>
                  )}
                </Button>
              </SheetTrigger>
              <SheetContent className="w-full sm:max-w-lg bg-white border-neutral-200">
                <SheetHeader>
                  <SheetTitle className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-[#E6F0FF] flex items-center justify-center">
                      <Paperclip className="w-4 h-4 text-[#0066FF]" />
                    </div>
                    Regulatory Documents
                  </SheetTitle>
                </SheetHeader>
                <div className="px-6 pb-6 flex-1 overflow-hidden">
                  <DocumentUpload
                    documents={documents}
                    onDocumentUpload={onDocumentUpload}
                    onDocumentRemove={onDocumentRemove}
                  />
                </div>
              </SheetContent>
            </Sheet>

            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about regulations, compliance gaps, or policy updates..."
              className="flex-1 border-neutral-200 focus-visible:ring-[#0066FF] focus-visible:border-[#0066FF] transition-smooth"
              disabled={isLoading}
            />
            <Button 
              onClick={handleSend} 
              disabled={isLoading || !input.trim()}
              className="bg-[#0066FF] hover:bg-[#0052CC] text-white shadow-electric transition-smooth relative overflow-hidden group"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-500"></div>
              <Send className="w-4 h-4 relative z-10" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
