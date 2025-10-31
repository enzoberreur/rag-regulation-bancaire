import React from 'react';
import { CitationChip } from './CitationChip';
import { ActionButtons } from './ActionButtons';
import { LoadingAnimation } from './LoadingAnimation';
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

// Simple markdown renderer for basic formatting
function renderMarkdown(text: string): React.ReactNode {
  // Normalize multiple consecutive newlines to maximum 2 (for paragraph breaks)
  // This ensures consistent spacing while preserving intentional breaks
  let normalizedText = text.replace(/\n{3,}/g, '\n\n');
  
  // Split by lines to handle multiline content
  const lines = normalizedText.split('\n');
  
  // Process lines and group consecutive list items
  const processedLines: React.ReactNode[] = [];
  let i = 0;
  
  while (i < lines.length) {
    const line = lines[i];
    
    // Skip empty lines but preserve them for spacing (only one at a time)
    if (line.trim() === '') {
      processedLines.push(<br key={`empty-${i}`} />);
      i++;
      continue;
    }
    
    // Handle numbered lists (e.g., "1. Text" or "1. **Bold Text:** Description")
    const numberedListMatch = line.match(/^([0-9]+\.\s+)(.+)$/);
    if (numberedListMatch) {
      const [, number, content] = numberedListMatch;
      // Process content for bold text
      const parts: React.ReactNode[] = [];
      let lastIndex = 0;
      const boldRegex = /\*\*([^*]+)\*\*/g;
      let match;
      let key = 0;
      
      while ((match = boldRegex.exec(content)) !== null) {
        if (match.index > lastIndex) {
          parts.push(content.slice(lastIndex, match.index));
        }
        parts.push(<strong key={key++}>{match[1]}</strong>);
        lastIndex = match.index + match[0].length;
      }
      
      if (lastIndex < content.length) {
        parts.push(content.slice(lastIndex));
      }
      
      processedLines.push(
        <div key={i} className="mb-4 last:mb-0">
          <div className="flex items-start gap-2">
            <span className="font-medium text-neutral-700 mt-0.5 flex-shrink-0">{number}</span>
            <div className="flex-1 leading-relaxed">
              {parts.length > 0 ? parts : content}
            </div>
          </div>
        </div>
      );
      i++;
      continue;
    }
    
    // Handle regular lines with bold text
    let processedLine = line;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    
    // Match **text** patterns
    const boldRegex = /\*\*([^*]+)\*\*/g;
    let match;
    let key = 0;
    
    while ((match = boldRegex.exec(processedLine)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push(processedLine.slice(lastIndex, match.index));
      }
      // Add bold text
      parts.push(
        <strong key={key++}>{match[1]}</strong>
      );
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < processedLine.length) {
      parts.push(processedLine.slice(lastIndex));
    }
    
    // If no matches, use original line
    const content = parts.length > 0 ? parts : [line];
    
    // Check if next line is empty or a list item to determine spacing
    const nextLine = i + 1 < lines.length ? lines[i + 1] : null;
    const isLastLine = i === lines.length - 1;
    const nextIsList = nextLine && nextLine.match(/^[0-9]+\.\s+/);
    const nextIsEmpty = nextLine && nextLine.trim() === '';
    
    // Add spacing: mb-3 for regular paragraphs, mb-4 before lists
    const marginClass = isLastLine ? '' : (nextIsList ? 'mb-4' : 'mb-3');
    
    processedLines.push(
      <div key={i} className={marginClass}>
        {content}
      </div>
    );
    i++;
  }
  
  return <>{processedLines}</>;
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
      <div className={isUser ? 'max-w-[75%]' : 'w-full'}>
        {isUser ? (
          <div className="rounded-2xl px-4 py-3 bg-[#0066FF] text-white shadow-electric transition-smooth">
            {(displayContent || isStreaming) && (
              <div className="text-sm whitespace-pre-wrap break-words overflow-wrap-anywhere leading-relaxed" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                {renderMarkdown(displayContent)}
                {isStreaming && displayContent && (
                  <LoadingAnimation variant="cursor" color="#ffffff" />
                )}
              </div>
            )}
            
            {isStreaming && !displayContent && (
              <div className="flex items-center gap-2 py-1">
                <LoadingAnimation variant="dots" size="sm" color="#ffffff" />
              </div>
            )}
          </div>
        ) : (
          <>
            {(displayContent || isStreaming) && (
              <div className="text-sm whitespace-pre-wrap break-words overflow-wrap-anywhere leading-relaxed text-neutral-900" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                {renderMarkdown(displayContent)}
                {isStreaming && displayContent && (
                  <LoadingAnimation variant="cursor" color="#0066FF" />
                )}
              </div>
            )}
            
            {isStreaming && !displayContent && (
              <div className="flex items-center gap-2 py-1">
                <LoadingAnimation variant="dots" size="sm" color="#0066FF" />
              </div>
            )}
            
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
          </>
        )}

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-3">
            <div className="flex flex-wrap gap-2">
              {message.citations.map(citation => (
                <CitationChip key={citation.id} citation={citation} />
              ))}
            </div>
          </div>
        )}

        {!isUser && (
          <div className="mt-4 space-y-3 pl-1">
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
