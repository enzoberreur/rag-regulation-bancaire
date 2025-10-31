import { Button } from './ui/button';
import { Copy, Download, Check } from 'lucide-react';
import { toast } from 'sonner@2.0.3';
import { useState } from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from './ui/tooltip';

interface Citation {
  id: string;
  text: string;
  source: string;
  url?: string;
}

interface ActionButtonsProps {
  content: string;
  citations?: Citation[];
}

export function ActionButtons({ content, citations }: ActionButtonsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    let textToCopy = content;
    
    if (citations && citations.length > 0) {
      textToCopy += '\n\nReferences:\n';
      citations.forEach((citation, index) => {
        textToCopy += `[${index + 1}] ${citation.text} - ${citation.source}\n`;
      });
    }

    // Use fallback method that works in all contexts
    const copyWithFallback = () => {
      const textArea = document.createElement('textarea');
      textArea.value = textToCopy;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      try {
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        return successful;
      } catch (err) {
        document.body.removeChild(textArea);
        throw err;
      }
    };

    try {
      // Try modern clipboard API first if available
      if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
          await navigator.clipboard.writeText(textToCopy);
        } catch (clipboardErr) {
          // If clipboard API fails (permissions/policy), use fallback
          console.log('Clipboard API blocked, using fallback method');
          if (!copyWithFallback()) {
            throw new Error('Fallback copy failed');
          }
        }
      } else {
        // Use fallback for older browsers
        if (!copyWithFallback()) {
          throw new Error('Copy method not supported');
        }
      }
      
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success('Analysis copied to clipboard');
    } catch (err) {
      console.error('Copy failed:', err);
      toast.error('Failed to copy. Please select text manually.');
    }
  };

  const handleDownload = () => {
    let textToDownload = 'HEXABANK REGULATORY COMPLIANCE ANALYSIS\n';
    textToDownload += '='.repeat(50) + '\n\n';
    textToDownload += content;
    
    if (citations && citations.length > 0) {
      textToDownload += '\n\n' + '='.repeat(50) + '\n';
      textToDownload += 'REFERENCES\n';
      textToDownload += '='.repeat(50) + '\n\n';
      citations.forEach((citation, index) => {
        textToDownload += `[${index + 1}] ${citation.text}\n    Source: ${citation.source}\n\n`;
      });
    }

    const blob = new Blob([textToDownload], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `compliance-analysis-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Analysis report downloaded');
  };

  return (
    <div className="flex gap-2">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleCopy}
            className="h-9 w-9 border border-neutral-200 hover:border-neutral-300 hover:bg-neutral-50 rounded-lg transition-smooth group"
            aria-label={copied ? 'Copied' : 'Copy Analysis'}
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-600" />
            ) : (
              <Copy className="w-4 h-4 text-neutral-600 group-hover:text-neutral-900" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>{copied ? 'Copied' : 'Copy Analysis'}</p>
        </TooltipContent>
      </Tooltip>

      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDownload}
            className="h-9 w-9 border border-neutral-200 hover:border-neutral-300 hover:bg-neutral-50 rounded-lg transition-smooth group"
            aria-label="Download Report"
          >
            <Download className="w-4 h-4 text-neutral-600 group-hover:text-neutral-900" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Download Report</p>
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
