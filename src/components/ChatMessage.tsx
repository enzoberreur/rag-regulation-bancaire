import React from 'react';
import { CitationChip } from './CitationChip';
import { ActionButtons } from './ActionButtons';
import { LoadingAnimation } from './LoadingAnimation';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { Button } from './ui/button';
import { HighlightedAnswer } from './HighlightedAnswer';

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

// Component to display text with a tooltip showing source information
interface SourceHighlightProps {
  children: React.ReactNode;
  citation: Citation;
  sourceNumber: number;
}

function SourceHighlight({ children, citation, sourceNumber }: SourceHighlightProps) {
  const colors = [
    'bg-blue-100 hover:bg-blue-200 border-blue-400',
    'bg-green-100 hover:bg-green-200 border-green-400',
    'bg-yellow-100 hover:bg-yellow-200 border-yellow-400',
    'bg-purple-100 hover:bg-purple-200 border-purple-400',
    'bg-pink-100 hover:bg-pink-200 border-pink-400',
  ];
  
  const colorClass = colors[(sourceNumber - 1) % colors.length];
  
  return (
    <span className={`${colorClass} border-b-2 cursor-help transition-colors relative group px-0.5 rounded-sm`}>
      {children}
      {/* Tooltip */}
      <span className="invisible group-hover:visible absolute bottom-full left-0 mb-2 w-80 p-4 bg-gray-900 text-white text-xs rounded-lg shadow-2xl z-50 pointer-events-none">
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-500 text-white font-semibold text-xs">
            {sourceNumber}
          </span>
          <div className="font-semibold text-sm">{citation.source}</div>
        </div>
        <div className="text-gray-300 max-h-32 overflow-y-auto leading-relaxed">
          {citation.text.substring(0, 300)}
          {citation.text.length > 300 ? '...' : ''}
        </div>
        {/* Arrow */}
        <div className="absolute top-full left-4 -mt-1 border-4 border-transparent border-t-gray-900"></div>
      </span>
    </span>
  );
}

// Parse text to find [SOURCE:N] markers and split text into segments
interface TextSegment {
  text: string;
  sourceNumber?: number;
}

function parseTextWithSources(text: string): TextSegment[] {
  const segments: TextSegment[] = [];
  
  // Split by sentence endings followed by [SOURCE:N]
  // Pattern: capture text ending with . or ! or ? followed by [SOURCE:N]
  const pattern = /([^.!?]+[.!?])\s*\[SOURCE:(\d+)\]/g;
  let lastIndex = 0;
  let match;
  
  while ((match = pattern.exec(text)) !== null) {
    // Add any text before this sentence (without source)
    if (match.index > lastIndex) {
      const textBefore = text.substring(lastIndex, match.index).trim();
      if (textBefore) {
        segments.push({ text: textBefore });
      }
    }
    
    // Add the sentence with its source number
    segments.push({
      text: match[1].trim(),
      sourceNumber: parseInt(match[2], 10)
    });
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text (without source)
  if (lastIndex < text.length) {
    const remaining = text.substring(lastIndex).trim();
    if (remaining) {
      segments.push({ text: remaining });
    }
  }
  
  return segments;
}

// Render text with source highlighting based on [SOURCE:N] markers
function renderMarkdownWithHighlights(text: string, citations?: Citation[]): React.ReactNode {
  if (!citations || citations.length === 0) {
    return renderMarkdown(text);
  }
  
  // Check if text contains [SOURCE:N] markers
  const hasSourceMarkers = /\[SOURCE:\d+\]/g.test(text);
  
  if (!hasSourceMarkers) {
    // Fallback to simple rendering if no markers found
    return renderMarkdown(text);
  }
  
  const segments = parseTextWithSources(text);
  
  // Build a citation map by source number (1-indexed)
  const citationMap = new Map<number, Citation>();
  citations.forEach((citation, index) => {
    citationMap.set(index + 1, citation);
  });
  
  const elements: React.ReactNode[] = [];
  let key = 0;
  
  segments.forEach((segment, segmentIndex) => {
    const citation = segment.sourceNumber ? citationMap.get(segment.sourceNumber) : null;
    
    // Process text for markdown (bold, line breaks)
    const processedText = processMarkdownText(segment.text, key);
    
    if (citation && segment.sourceNumber) {
      elements.push(
        <SourceHighlight key={`source-${key++}`} citation={citation} sourceNumber={segment.sourceNumber}>
          {processedText}
        </SourceHighlight>
      );
    } else {
      elements.push(<span key={`text-${key++}`}>{processedText}</span>);
    }
  });
  
  return <>{elements}</>;
}

// Process markdown formatting (bold, line breaks) for a text segment
function processMarkdownText(text: string, baseKey: number): React.ReactNode {
  const elements: React.ReactNode[] = [];
  let key = baseKey;
  
  const lines = text.split('\n');
  lines.forEach((line, lineIndex) => {
    if (lineIndex > 0) {
      elements.push(<br key={`br-${key++}`} />);
    }
    
    // Process bold in this line
    const boldRegex = /\*\*([^*]+)\*\*/g;
    let lastIdx = 0;
    let match;
    const lineParts: React.ReactNode[] = [];
    
    while ((match = boldRegex.exec(line)) !== null) {
      if (match.index > lastIdx) {
        lineParts.push(line.slice(lastIdx, match.index));
      }
      lineParts.push(<strong key={`bold-${key++}`} className="font-semibold">{match[1]}</strong>);
      lastIdx = match.index + match[0].length;
    }
    
    if (lastIdx < line.length) {
      lineParts.push(line.slice(lastIdx));
    }
    
    elements.push(...lineParts);
  });
  
  return <>{elements}</>;
}

// Keep simple version for backward compatibility
function renderMarkdown(text: string, citations?: Citation[]): React.ReactNode {
  // Use the new highlighting version if citations are available
  if (citations && citations.length > 0) {
    return renderMarkdownWithHighlights(text, citations);
  }
  
  // Fallback to simple rendering
  const elements: React.ReactNode[] = [];
  let key = 0;
  
  const lines = text.split('\n');
  lines.forEach((line, lineIndex) => {
    if (lineIndex > 0) {
      elements.push(<br key={`br-${key++}`} />);
    }
    
    const boldRegex = /\*\*([^*]+)\*\*/g;
    let lastIndex = 0;
    let match;
    const lineParts: React.ReactNode[] = [];
    
    while ((match = boldRegex.exec(line)) !== null) {
      if (match.index > lastIndex) {
        lineParts.push(line.slice(lastIndex, match.index));
      }
      lineParts.push(<strong key={`bold-${key++}`} className="font-semibold text-neutral-900">{match[1]}</strong>);
      lastIndex = match.index + match[0].length;
    }
    
    if (lastIndex < line.length) {
      lineParts.push(line.slice(lastIndex));
    }
    
    elements.push(...lineParts);
  });
  
  return <>{elements}</>;
}

// Keep old implementation for reference but not used
function renderMarkdown_OLD(text: string): React.ReactNode {
  let normalizedText = text;
  
  // Split by lines and process
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
    
    // Handle bullet points (•, -, *, or ▪)
    const bulletMatch = line.match(/^([•\-\*▪]\s+)(.+)$/);
    if (bulletMatch) {
      const [, bullet, content] = bulletMatch;
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
        <div key={i} className="mb-3 last:mb-0">
          <div className="flex items-start gap-3">
            <span className="text-neutral-600 mt-1 flex-shrink-0 min-w-[1rem]">•</span>
            <div className="flex-1 leading-relaxed text-neutral-800">
              {parts.length > 0 ? parts : content}
            </div>
          </div>
        </div>
      );
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
          <div className="flex items-start gap-3">
            <span className="font-medium text-neutral-700 mt-0.5 flex-shrink-0 min-w-[1.5rem]">{number}</span>
            <div className="flex-1 leading-relaxed text-neutral-800">
              {parts.length > 0 ? parts : content}
            </div>
          </div>
        </div>
      );
      i++;
      continue;
    }
    
    // Check if this is a section header (bold text followed by colon or dash)
    const sectionHeaderMatch = line.match(/^\*\*([^*]+)\*\*\s*[:\-]/);
    if (sectionHeaderMatch) {
      // Process as a section header with bold title
      const parts: React.ReactNode[] = [];
      let lastIndex = 0;
      const boldRegex = /\*\*([^*]+)\*\*/g;
      let match;
      let key = 0;
      
      while ((match = boldRegex.exec(line)) !== null) {
        if (match.index > lastIndex) {
          parts.push(line.slice(lastIndex, match.index));
        }
        parts.push(<strong key={key++} className="text-neutral-900 font-semibold">{match[1]}</strong>);
        lastIndex = match.index + match[0].length;
      }
      
      if (lastIndex < line.length) {
        parts.push(line.slice(lastIndex));
      }
      
      processedLines.push(
        <div key={i} className="mb-4 mt-6 first:mt-0">
          <div className="text-base leading-relaxed text-neutral-800">
            {parts.length > 0 ? parts : line}
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
    const nextIsList = nextLine && (nextLine.match(/^[0-9]+\.\s+/) || nextLine.match(/^[•\-\*▪]\s+/));
    const nextIsEmpty = nextLine && nextLine.trim() === '';
    
    // Add spacing: mb-4 for paragraphs before lists or empty lines, mb-3 for regular paragraphs
    const marginClass = isLastLine ? '' : (nextIsList || nextIsEmpty ? 'mb-4' : 'mb-3');
    
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
                {renderMarkdown(displayContent, message.citations)}
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
              <div className="text-sm leading-relaxed text-neutral-900">
                {/* Check if content looks like HTML (contains <p> or <mark>) */}
                {displayContent && (displayContent.includes('<p>') || displayContent.includes('<mark>')) ? (
                  <HighlightedAnswer html={
                    // Clean up potential markdown code blocks
                    displayContent
                      .replace(/```html\n?/g, '')
                      .replace(/```\n?/g, '')
                      .trim()
                  } />
                ) : (
                  <div className="whitespace-pre-wrap break-words overflow-wrap-anywhere" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere', lineHeight: '1.7' }}>
                    {renderMarkdown(displayContent, message.citations)}
                  </div>
                )}
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
