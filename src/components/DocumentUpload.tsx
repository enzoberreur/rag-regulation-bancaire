import { useState, useRef } from 'react';
import { Button } from './ui/button';
import { FileText, Upload, X, File, FolderOpen, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner@2.0.3';
import { Separator } from './ui/separator';
import { uploadDocument, deleteDocument, type UploadedDocument as ApiUploadedDocument } from '../services/api';

interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  uploadedAt: Date;
  type: 'regulation' | 'policy' | 'document';
}

interface DocumentUploadProps {
  documents: UploadedDocument[];
  onDocumentUpload: (doc: UploadedDocument) => void;
  onDocumentRemove?: (id: string) => void;
}

export function DocumentUpload({ documents, onDocumentUpload, onDocumentRemove }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleFileSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    for (const file of Array.from(files)) {
      try {
        // Show loading toast
        const loadingToast = toast.loading(`Uploading ${file.name}...`);
        
        // Upload to backend
        const uploadedDoc = await uploadDocument(file);
        
        // Convert API format to frontend format
        const doc: UploadedDocument = {
          id: uploadedDoc.id,
          name: uploadedDoc.name,
          size: uploadedDoc.size,
          uploadedAt: new Date(uploadedDoc.uploaded_at),
          type: uploadedDoc.type,
        };
        
        // Update UI
        onDocumentUpload(doc);
        
        // Update toast
        toast.success(`${file.name} uploaded`, {
          id: loadingToast,
          description: 'Processing for RAG...',
        });
      } catch (error) {
        toast.error(`Failed to upload ${file.name}`, {
          description: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleRemove = async (id: string, name: string) => {
    try {
      // Delete from backend
      await deleteDocument(id);
      
      // Update UI
      if (onDocumentRemove) {
        onDocumentRemove(id);
      }
      
      toast.success('Document removed', {
        description: name,
      });
    } catch (error) {
      toast.error(`Failed to remove ${name}`, {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const getDocumentIcon = () => {
    return <File className="w-4 h-4 text-neutral-600" />;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header Stats */}
      {documents.length > 0 && (
        <div className="mb-6">
          <div className="bg-gradient-to-br from-[#E6F0FF] to-[#F0F7FF] rounded-xl p-4 border border-[#0066FF]/10">
            <div className="flex items-center gap-2 mb-1">
              <File className="w-4 h-4 text-[#0066FF]" />
              <span className="text-xs text-neutral-600">Total Documents</span>
            </div>
            <div className="text-2xl text-[#0066FF]">{documents.length}</div>
          </div>
        </div>
      )}

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-12 transition-all relative overflow-hidden group ${
          isDragging
            ? 'border-[#0066FF] bg-[#E6F0FF]/30 shadow-lg scale-[1.02]'
            : 'border-neutral-200 hover:border-[#0066FF]/40 hover:bg-neutral-50/50'
        }`}
      >
        {isDragging && (
          <div className="absolute inset-0 bg-gradient-to-br from-[#0066FF]/5 to-[#00D4FF]/5 animate-pulse"></div>
        )}
        
        <div className="flex flex-col items-center justify-center text-center relative z-10">
          <div className={`relative mb-5 transition-all duration-300 ${isDragging ? 'scale-110' : 'group-hover:scale-105'}`}>
            <div className={`w-20 h-20 rounded-2xl flex items-center justify-center transition-all shadow-lg ${
              isDragging 
                ? 'bg-[#0066FF] shadow-electric rotate-3' 
                : 'bg-gradient-to-br from-[#E6F0FF] to-[#F0F7FF] group-hover:shadow-xl'
            }`}>
              <Upload className={`w-9 h-9 transition-all ${
                isDragging ? 'text-white animate-bounce' : 'text-[#0066FF] group-hover:translate-y-[-2px]'
              }`} />
            </div>
            {!isDragging && (
              <div className="absolute -bottom-1 -right-1 w-7 h-7 bg-white rounded-full flex items-center justify-center shadow-md border-2 border-[#E6F0FF] group-hover:scale-110 transition-transform">
                <FolderOpen className="w-3.5 h-3.5 text-[#0066FF]" />
              </div>
            )}
          </div>
          
          <p className="text-neutral-900 mb-2">
            {isDragging ? 'Drop your files here' : 'Drag & drop documents'}
          </p>
          <p className="text-neutral-500 text-sm mb-6">
            or click below to browse • PDF, DOCX, TXT • Max 50MB
          </p>
          
          <Button
            onClick={() => fileInputRef.current?.click()}
            className="bg-[#0066FF] hover:bg-[#0052CC] text-white shadow-md hover:shadow-lg transition-all relative overflow-hidden group/btn"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-500"></div>
            <FileText className="w-4 h-4 mr-2 relative z-10" />
            <span className="relative z-10">Browse Files</span>
          </Button>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.doc,.docx,.txt"
          multiple
          onChange={(e) => handleFileSelect(e.target.files)}
        />
      </div>

      {/* Documents List */}
      {documents.length > 0 && (
        <>
          <Separator className="my-6" />
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {documents.map(doc => (
              <DocumentItem key={doc.id} doc={doc} onRemove={handleRemove} getIcon={getDocumentIcon} formatSize={formatFileSize} />
            ))}
          </div>
        </>
      )}

      {documents.length === 0 && (
        <div className="mt-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neutral-100 text-neutral-500 text-sm">
            <FolderOpen className="w-4 h-4" />
            <span>No documents uploaded yet</span>
          </div>
        </div>
      )}
    </div>
  );
}

function DocumentItem({ 
  doc, 
  onRemove, 
  getIcon, 
  formatSize 
}: { 
  doc: UploadedDocument; 
  onRemove: (id: string, name: string) => void;
  getIcon: () => JSX.Element;
  formatSize: (bytes: number) => string;
}) {
  return (
    <div className="border border-neutral-200 rounded-xl p-3.5 flex items-center justify-between group hover:border-[#0066FF]/30 hover:bg-gradient-to-r hover:from-neutral-50/50 hover:to-transparent transition-all hover:shadow-sm">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-neutral-50 to-neutral-100 group-hover:from-white group-hover:to-neutral-50 flex items-center justify-center flex-shrink-0 transition-all shadow-sm">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm truncate text-neutral-900">{doc.name}</p>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 opacity-60" />
          </div>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xs text-neutral-500">{formatSize(doc.size)}</p>
            <span className="text-neutral-300">•</span>
            <p className="text-xs text-neutral-400">{doc.uploadedAt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</p>
          </div>
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onRemove(doc.id, doc.name)}
        className="ml-3 opacity-0 group-hover:opacity-100 transition-all h-8 w-8 p-0 hover:bg-red-50 hover:text-red-600 flex-shrink-0"
      >
        <X className="w-4 h-4" />
      </Button>
    </div>
  );
}
