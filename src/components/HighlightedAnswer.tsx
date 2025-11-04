import React from 'react';

interface HighlightedAnswerProps {
  html: string;
}

export function HighlightedAnswer({ html }: HighlightedAnswerProps) {
  return (
    <>
      <style>{`
        .highlighted-answer mark {
          background-color: #dbeafe;
          cursor: help;
          position: relative;
          padding: 2px 4px;
          border-radius: 2px;
          transition: background-color 0.2s;
        }
        
        .highlighted-answer mark:hover {
          background-color: #bfdbfe;
        }
        
        .highlighted-answer mark::after {
          content: attr(data-source);
          visibility: hidden;
          opacity: 0;
          position: absolute;
          bottom: 125%;
          left: 50%;
          transform: translateX(-50%);
          background: #1f2937;
          color: #fff;
          font-size: 0.75rem;
          font-weight: 500;
          padding: 6px 10px;
          border-radius: 6px;
          white-space: nowrap;
          transition: opacity 0.2s, visibility 0.2s;
          pointer-events: none;
          z-index: 100;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        
        .highlighted-answer mark::before {
          content: '';
          visibility: hidden;
          opacity: 0;
          position: absolute;
          bottom: 100%;
          left: 50%;
          transform: translateX(-50%);
          border: 6px solid transparent;
          border-top-color: #1f2937;
          transition: opacity 0.2s, visibility 0.2s;
          pointer-events: none;
          z-index: 100;
        }
        
        .highlighted-answer mark:hover::after,
        .highlighted-answer mark:hover::before {
          visibility: visible;
          opacity: 1;
        }
        
        .highlighted-answer p {
          margin-bottom: 1rem;
          line-height: 1.7;
        }
        
        .highlighted-answer p:last-child {
          margin-bottom: 0;
        }
        
        .highlighted-answer strong {
          font-weight: 600;
          color: #111827;
        }
        
        .highlighted-answer h3 {
          font-size: 1.125rem;
          font-weight: 600;
          color: #111827;
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
        }
        
        .highlighted-answer h3:first-child {
          margin-top: 0;
        }
        
        .highlighted-answer h4 {
          font-size: 1rem;
          font-weight: 600;
          color: #374151;
          margin-top: 1rem;
          margin-bottom: 0.5rem;
        }
        
        .highlighted-answer ul, .highlighted-answer ol {
          margin-left: 1.5rem;
          margin-bottom: 1rem;
        }
        
        .highlighted-answer li {
          margin-bottom: 0.5rem;
          line-height: 1.7;
        }
      `}</style>
      <div 
        className="highlighted-answer prose max-w-none"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </>
  );
}
