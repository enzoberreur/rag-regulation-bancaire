import { useState, useRef, useEffect, useCallback } from 'react';
import { ChatMessage } from './ChatMessage';
import { DocumentUpload } from './DocumentUpload';
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
}

const mockAssistantResponse = (query: string): { content: string; citations: Citation[] } => {
  const responses = {
    default: {
      content: "Based on the ACPR Regulation 2024-15, Article 12 requires enhanced capital requirements for climate-related exposures. Cross-referencing with HexaBank's Risk Management Policy (RMP-2024-03), Section 4.2, there appears to be a gap in the current climate risk assessment framework.\n\nRecommended actions:\n1. Update RMP-2024-03 Section 4.2 to include climate exposure quantification\n2. Implement monthly reporting requirements as specified in Article 12(3)\n3. Establish dedicated Climate Risk Committee per Article 15",
      citations: [
        { id: '1', text: 'ACPR Regulation 2024-15, Article 12: Climate Capital Requirements', source: 'ACPR Regulation', url: '/regulations/acpr-2024-15' },
        { id: '2', text: 'HexaBank RMP-2024-03, Section 4.2: Risk Assessment Framework', source: 'Internal Policy', url: '/policies/rmp-2024-03' },
        { id: '3', text: 'Non-conformity identified: Missing climate risk quantification', source: 'Analysis Result', url: '/analysis' }
      ]
    }
  };
  
  return responses.default;
};

// Simulate SSE streaming by progressively yielding chunks of text
async function* streamResponse(fullContent: string): AsyncGenerator<string, void, unknown> {
  const words = fullContent.split(' ');
  let currentChunk = '';
  
  for (let i = 0; i < words.length; i++) {
    currentChunk += (i > 0 ? ' ' : '') + words[i];
    
    // Yield chunks of 2-4 words at a time
    if (i % (2 + Math.floor(Math.random() * 3)) === 0 || i === words.length - 1) {
      yield currentChunk;
      // Simulate network delay (20-60ms per chunk)
      await new Promise(resolve => setTimeout(resolve, 20 + Math.random() * 40));
    }
  }
}

export function ChatInterface({ sessionId, messages, onUpdateMessages, onUpdateMetrics, documents, onDocumentUpload }: ChatInterfaceProps) {
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
    setInput('');
    setIsLoading(true);

    const startTime = Date.now();
    const { content, citations } = mockAssistantResponse(input);
    
    // Create a placeholder message for streaming
    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      citations,
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
      // Simulate initial connection delay
      await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 200));

      // Stream the response
      let streamedContent = '';
      for await (const chunk of streamResponse(content)) {
        if (abortControllerRef.current?.signal.aborted) break;
        
        streamedContent = chunk;
        onUpdateMessages([
          ...updatedMessages,
          { ...assistantMessage, content: chunk }
        ]);
      }

      const latency = Date.now() - startTime;
      
      setIsLoading(false);
      setStreamingMessageId(null);

      onUpdateMetrics({
        latency,
        errors: 0,
        cost: 0.0023 + (Math.random() * 0.002),
        tokensUsed: Math.floor(1000 + Math.random() * 500)
      });
    } catch (error) {
      console.error('Streaming error:', error);
      setIsLoading(false);
      setStreamingMessageId(null);
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
            <div className="flex flex-col items-center justify-center h-full text-center py-20">
              <div className="w-16 h-16 rounded-2xl bg-[#E6F0FF] flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-[#0066FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h2 className="text-neutral-900 mb-2">Start Regulatory Analysis</h2>
              <p className="text-sm text-neutral-500 max-w-md">
                Ask questions about ACPR regulations, ECB guidelines, EU AI Act compliance, or policy mapping
              </p>
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
            <div className="flex gap-3 items-center text-neutral-400">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-[#0066FF] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-[#0066FF] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-[#0066FF] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm text-neutral-500">Analyzing regulations...</span>
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-neutral-200 px-8 py-6 bg-neutral-50/50 backdrop-blur-sm relative flex-shrink-0">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#0066FF]/20 to-transparent"></div>
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
