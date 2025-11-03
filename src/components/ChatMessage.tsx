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

// Find text segments that match source citations for highlighting
function findSourceMatches(text: string, citations?: Citation[]): Array<{start: number, end: number, citation: Citation}> {
  if (!citations || citations.length === 0) return [];
  
  const matches: Array<{start: number, end: number, citation: Citation}> = [];
  
  // For each citation, try to find matching segments in the text
  citations.forEach(citation => {
    // Extract meaningful phrases from citation text (sentences with >20 chars)
    const sentences = citation.text.split(/[.!?]+/).filter(s => s.trim().length > 20);
    
    sentences.forEach(sentence => {
      const cleanSentence = sentence.trim().toLowerCase();
      const cleanText = text.toLowerCase();
      
      // Look for this sentence in the response text
      let index = cleanText.indexOf(cleanSentence);
      if (index !== -1) {
        matches.push({
          start: index,
          end: index + cleanSentence.length,
          citation: citation
        });
      } else {
        // Try finding partial matches (at least 30 chars)
        const words = cleanSentence.split(/\s+/);
        if (words.length >= 5) {
          // Try matching chunks of 5+ words
          for (let i = 0; i <= words.length - 5; i++) {
            const chunk = words.slice(i, i + 5).join(' ');
            if (chunk.length >= 30) {
              index = cleanText.indexOf(chunk);
              if (index !== -1) {
                matches.push({
                  start: index,
                  end: index + chunk.length,
                  citation: citation
                });
                break;
              }
            }
          }
        }
      }
    });
  });
  
  // Sort by position and remove overlaps (keep first match)
  matches.sort((a, b) => a.start - b.start);
  const filtered: typeof matches = [];
  matches.forEach(match => {
    if (filtered.length === 0 || match.start >= filtered[filtered.length - 1].end) {
      filtered.push(match);
    }
  });
  
  return filtered;
}

// Render text with automatic source highlighting
function renderMarkdownWithHighlights(text: string, citations?: Citation[]): React.ReactNode {
  const elements: React.ReactNode[] = [];
  let key = 0;
  
  // Find source matches in the text
  const sourceMatches = findSourceMatches(text, citations);
  
  // Build a map of character positions to citations
  const positionToCitation = new Map<number, Citation>();
  sourceMatches.forEach(match => {
    for (let i = match.start; i < match.end; i++) {
      positionToCitation.set(i, match.citation);
    }
  });
  
  // Process text character by character, grouping into segments
  let currentSegment = '';
  let currentCitation: Citation | null = null;
  let textIndex = 0;
  
  const flushSegment = () => {
    if (currentSegment) {
      const segment = currentSegment;
      const citation = currentCitation;
      
      if (citation) {
        // Highlighted segment with tooltip
        elements.push(
          <span
            key={`seg-${key++}`}
            className="bg-blue-50 hover:bg-blue-100 border-b-2 border-blue-300 cursor-help transition-colors relative group px-0.5"
            title={citation.source}
          >
            {segment}
            {/* Tooltip */}
            <span className="invisible group-hover:visible absolute bottom-full left-0 mb-2 w-72 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl z-50 pointer-events-none">
              <div className="font-semibold mb-1 text-sm">{citation.source}</div>
              <div className="text-gray-300 max-h-24 overflow-y-auto">{citation.text.substring(0, 200)}...</div>
              <div className="absolute top-full left-4 -mt-1 border-4 border-transparent border-t-gray-900"></div>
            </span>
          </span>
        );
      } else {
        // Regular text
        elements.push(<span key={`seg-${key++}`}>{segment}</span>);
      }
      
      currentSegment = '';
      currentCitation = null;
    }
  };
  
  // Process each character
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const citation = positionToCitation.get(i);
    
    // If citation changes, flush current segment
    if (citation !== currentCitation) {
      flushSegment();
      currentCitation = citation || null;
    }
    
    currentSegment += char;
  }
  
  // Flush remaining segment
  flushSegment();
  
  // Now process for line breaks and bold
  const finalElements: React.ReactNode[] = [];
  let segmentKey = 0;
  
  elements.forEach(element => {
    if (typeof element === 'object' && element && 'props' in element) {
      const content = element.props.children;
      if (typeof content === 'string') {
        // Split by newlines and bold
        const lines = content.split('\n');
        lines.forEach((line, lineIdx) => {
          if (lineIdx > 0) {
            finalElements.push(<br key={`br-${segmentKey++}`} />);
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
            lineParts.push(<strong key={`bold-${segmentKey++}`} className="font-semibold">{match[1]}</strong>);
            lastIdx = match.index + match[0].length;
          }
          
          if (lastIdx < line.length) {
            lineParts.push(line.slice(lastIdx));
          }
          
          if (lineParts.length > 0) {
            // Wrap in the same span type as original (highlighted or not)
            const newElement = React.cloneElement(element as React.ReactElement, {
              key: `wrap-${segmentKey++}`,
              children: lineParts
            });
            finalElements.push(newElement);
          }
        });
      } else {
        finalElements.push(element);
      }
    }
  });
  
  return <>{finalElements}</>;
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
              <div className="text-sm whitespace-pre-wrap break-words overflow-wrap-anywhere leading-relaxed text-neutral-900" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere', lineHeight: '1.7' }}>
                {renderMarkdown(displayContent, message.citations)}
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
