import { CitationChip } from './CitationChip';
import { ActionButtons } from './ActionButtons';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { Button } from './ui/button';

interface Citation {
  id: string;
  text: string;
  source: string;
  url?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

export function ChatMessage({ message, isStreaming = false }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const [isExpanded, setIsExpanded] = useState(false);
  
  const MAX_LINES = 4;
  const lines = message.content.split('\n');
  const shouldTruncate = !isUser && lines.length > MAX_LINES && !isStreaming;
  const displayContent = shouldTruncate && !isExpanded 
    ? lines.slice(0, MAX_LINES).join('\n')
    : message.content;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}>
      <div className="max-w-[75%]">
        <div
          className={`rounded-2xl px-4 py-3 transition-smooth ${
            isUser
              ? 'bg-[#0066FF] text-white shadow-electric'
              : 'bg-neutral-50 text-neutral-900 border border-neutral-200 group-hover:border-[#0066FF]/20 group-hover:shadow-electric'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap leading-relaxed">
            {displayContent}
            {isStreaming && (
              <span className="inline-block w-0.5 h-4 bg-[#0066FF] ml-0.5 animate-pulse"></span>
            )}
          </p>
          
          {shouldTruncate && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="mt-3 h-7 text-xs text-[#0066FF] hover:text-[#0052CC] hover:bg-[#E6F0FF] transition-smooth p-0 px-2"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-3.5 h-3.5 mr-1" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="w-3.5 h-3.5 mr-1" />
                  Show more
                </>
              )}
            </Button>
          )}
        </div>

        {!isUser && (
          <div className="mt-4 space-y-3 pl-1">
            {message.citations && message.citations.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {message.citations.map(citation => (
                  <CitationChip key={citation.id} citation={citation} />
                ))}
              </div>
            )}
            <ActionButtons content={message.content} citations={message.citations} />
          </div>
        )}

        <div className={`text-xs text-neutral-400 mt-2 px-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
