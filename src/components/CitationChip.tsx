import { Badge } from './ui/badge';
import { FileText, ExternalLink, AlertTriangle, Shield } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';
import { getDocumentViewUrl } from '../services/api';

interface Citation {
  id: string;
  text: string;
  source: string;
  url?: string;
}

interface CitationChipProps {
  citation: Citation;
}

export function CitationChip({ citation }: CitationChipProps) {
  const handleClick = () => {
    if (citation.url) {
      // Extract document ID from URL (format: /documents/{id})
      const match = citation.url.match(/\/documents\/([^/]+)/);
      if (match) {
        const documentId = match[1];
        // Open document in new tab using the backend view endpoint
        const viewUrl = getDocumentViewUrl(documentId);
        window.open(viewUrl, '_blank');
      }
    }
  };

  const isNonConformity = citation.source.toLowerCase().includes('non-conformity') || 
                          citation.source.toLowerCase().includes('analysis result');
  const isRegulation = citation.source.toLowerCase().includes('acpr') || 
                       citation.source.toLowerCase().includes('ecb') || 
                       citation.source.toLowerCase().includes('regulation');
  const isPolicy = citation.source.toLowerCase().includes('policy');

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            className={`cursor-pointer transition-all gap-2 py-2 px-3.5 hover:scale-105 ${
              isNonConformity 
                ? 'border-amber-300 bg-amber-50 text-amber-900 hover:bg-amber-100 hover:shadow-lg hover:shadow-amber-200/50' 
                : isRegulation 
                ? 'border-[#0066FF]/30 bg-[#E6F0FF] text-[#0066FF] hover:bg-[#0066FF] hover:text-white hover:shadow-electric'
                : 'border-green-300 bg-green-50 text-green-900 hover:bg-green-100 hover:shadow-lg hover:shadow-green-200/50'
            }`}
            onClick={handleClick}
          >
            {isNonConformity ? (
              <AlertTriangle className="w-3.5 h-3.5" />
            ) : isRegulation ? (
              <Shield className="w-3.5 h-3.5" />
            ) : (
              <FileText className="w-3.5 h-3.5" />
            )}
            <span className="text-xs">{citation.source}</span>
            {citation.url && <ExternalLink className="w-3 h-3 opacity-60" />}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-sm border-[#0066FF]/20">
          <p className="text-sm">{citation.text}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
