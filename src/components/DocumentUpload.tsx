import { useState, useRef } from 'react';
import { Button } from './ui/button';
import { FileText, Upload, X, File, ShieldCheck, BookOpen, FolderOpen, CheckCircle2 } from 'lucide-react';
import { Badge } from './ui/badge';
import { toast } from 'sonner@2.0.3';
import { Separator } from './ui/separator';

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
  const [selectedType, setSelectedType] = useState<'regulation' | 'policy' | 'document'>('regulation');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return;

    Array.from(files).forEach(file => {
      const doc: UploadedDocument = {
        id: Date.now().toString() + Math.random(),
        name: file.name,
        size: file.size,
        uploadedAt: new Date(),
        type: selectedType
      };
      onDocumentUpload(doc);
      toast.success(`${file.name} uploaded`, {
        description: `Classified as ${selectedType}`
      });
    });

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

  const handleRemove = (id: string, name: string) => {
    if (onDocumentRemove) {
      onDocumentRemove(id);
    }
    toast.success('Document removed', {
      description: name
    });
  };

  const getDocumentIcon = (type: string) => {
    switch (type) {
      case 'regulation':
        return <ShieldCheck className="w-4 h-4 text-[#0066FF]" />;
      case 'policy':
        return <BookOpen className="w-4 h-4 text-emerald-600" />;
      default:
        return <File className="w-4 h-4 text-neutral-600" />;
    }
  };

  const getDocumentBadge = (type: string) => {
    switch (type) {
      case 'regulation':
        return <Badge variant="outline" className="bg-[#E6F0FF] text-[#0066FF] border-[#0066FF]/20 text-xs">Regulation</Badge>;
      case 'policy':
        return <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 text-xs">Policy</Badge>;
      default:
        return <Badge variant="outline" className="bg-neutral-50 text-neutral-600 border-neutral-200 text-xs">Document</Badge>;
    }
  };

  const regulations = documents.filter(d => d.type === 'regulation');
  const policies = documents.filter(d => d.type === 'policy');
  const otherDocs = documents.filter(d => d.type === 'document');

  return (
    <div className="flex flex-col h-full">
      {/* Header Stats */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-gradient-to-br from-[#E6F0FF] to-[#F0F7FF] rounded-xl p-4 border border-[#0066FF]/10">
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="w-4 h-4 text-[#0066FF]" />
            <span className="text-xs text-neutral-600">Regulations</span>
          </div>
          <div className="text-2xl text-[#0066FF]">{regulations.length}</div>
        </div>
        <div className="bg-gradient-to-br from-emerald-50 to-emerald-50/30 rounded-xl p-4 border border-emerald-200/50">
          <div className="flex items-center gap-2 mb-1">
            <BookOpen className="w-4 h-4 text-emerald-600" />
            <span className="text-xs text-neutral-600">Policies</span>
          </div>
          <div className="text-2xl text-emerald-600">{policies.length}</div>
        </div>
        <div className="bg-gradient-to-br from-neutral-50 to-neutral-50/30 rounded-xl p-4 border border-neutral-200">
          <div className="flex items-center gap-2 mb-1">
            <File className="w-4 h-4 text-neutral-600" />
            <span className="text-xs text-neutral-600">Other</span>
          </div>
          <div className="text-2xl text-neutral-700">{otherDocs.length}</div>
        </div>
      </div>

      {/* Document Type Selection */}
      <div className="mb-6">
        <label className="text-sm text-neutral-700 mb-3 block flex items-center gap-2">
          <div className="w-1 h-4 bg-[#0066FF] rounded-full"></div>
          Classification Type
        </label>
        <div className="grid grid-cols-3 gap-2 p-1 bg-neutral-100 rounded-lg">
          <button
            onClick={() => setSelectedType('regulation')}
            className={`px-4 py-2.5 rounded-md text-sm transition-all relative overflow-hidden group ${
              selectedType === 'regulation'
                ? 'bg-[#0066FF] text-white shadow-md'
                : 'text-neutral-700 hover:bg-white hover:shadow-sm'
            }`}
          >
            {selectedType === 'regulation' && (
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
            )}
            <div className="flex items-center gap-2 justify-center relative z-10">
              <ShieldCheck className="w-4 h-4" />
              <span>Regulation</span>
            </div>
          </button>
          <button
            onClick={() => setSelectedType('policy')}
            className={`px-4 py-2.5 rounded-md text-sm transition-all relative overflow-hidden group ${
              selectedType === 'policy'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-neutral-700 hover:bg-white hover:shadow-sm'
            }`}
          >
            {selectedType === 'policy' && (
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
            )}
            <div className="flex items-center gap-2 justify-center relative z-10">
              <BookOpen className="w-4 h-4" />
              <span>Policy</span>
            </div>
          </button>
          <button
            onClick={() => setSelectedType('document')}
            className={`px-4 py-2.5 rounded-md text-sm transition-all relative overflow-hidden group ${
              selectedType === 'document'
                ? 'bg-neutral-700 text-white shadow-md'
                : 'text-neutral-700 hover:bg-white hover:shadow-sm'
            }`}
          >
            {selectedType === 'document' && (
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
            )}
            <div className="flex items-center gap-2 justify-center relative z-10">
              <File className="w-4 h-4" />
              <span>Document</span>
            </div>
          </button>
        </div>
      </div>

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
            {isDragging ? 'Drop your files here' : 'Drag & drop regulatory documents'}
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
          <div className="flex-1 overflow-y-auto space-y-6 pr-1">
            {regulations.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3 sticky top-0 bg-white py-2 z-10">
                  <div className="w-1.5 h-5 bg-gradient-to-b from-[#0066FF] to-[#00D4FF] rounded-full shadow-sm"></div>
                  <h4 className="text-sm text-neutral-700">Regulations</h4>
                  <Badge variant="secondary" className="ml-auto bg-[#E6F0FF] text-[#0066FF] border-none">
                    {regulations.length}
                  </Badge>
                </div>
                <div className="space-y-2">
                  {regulations.map(doc => (
                    <DocumentItem key={doc.id} doc={doc} onRemove={handleRemove} getIcon={getDocumentIcon} getBadge={getDocumentBadge} formatSize={formatFileSize} />
                  ))}
                </div>
              </div>
            )}

            {policies.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3 sticky top-0 bg-white py-2 z-10">
                  <div className="w-1.5 h-5 bg-gradient-to-b from-emerald-500 to-emerald-600 rounded-full shadow-sm"></div>
                  <h4 className="text-sm text-neutral-700">Internal Policies</h4>
                  <Badge variant="secondary" className="ml-auto bg-emerald-50 text-emerald-700 border-none">
                    {policies.length}
                  </Badge>
                </div>
                <div className="space-y-2">
                  {policies.map(doc => (
                    <DocumentItem key={doc.id} doc={doc} onRemove={handleRemove} getIcon={getDocumentIcon} getBadge={getDocumentBadge} formatSize={formatFileSize} />
                  ))}
                </div>
              </div>
            )}

            {otherDocs.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3 sticky top-0 bg-white py-2 z-10">
                  <div className="w-1.5 h-5 bg-gradient-to-b from-neutral-400 to-neutral-500 rounded-full shadow-sm"></div>
                  <h4 className="text-sm text-neutral-700">Other Documents</h4>
                  <Badge variant="secondary" className="ml-auto bg-neutral-100 text-neutral-700 border-none">
                    {otherDocs.length}
                  </Badge>
                </div>
                <div className="space-y-2">
                  {otherDocs.map(doc => (
                    <DocumentItem key={doc.id} doc={doc} onRemove={handleRemove} getIcon={getDocumentIcon} getBadge={getDocumentBadge} formatSize={formatFileSize} />
                  ))}
                </div>
              </div>
            )}
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
  getBadge, 
  formatSize 
}: { 
  doc: UploadedDocument; 
  onRemove: (id: string, name: string) => void;
  getIcon: (type: string) => JSX.Element;
  getBadge: (type: string) => JSX.Element;
  formatSize: (bytes: number) => string;
}) {
  return (
    <div className="border border-neutral-200 rounded-xl p-3.5 flex items-center justify-between group hover:border-[#0066FF]/30 hover:bg-gradient-to-r hover:from-neutral-50/50 hover:to-transparent transition-all hover:shadow-sm">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-neutral-50 to-neutral-100 group-hover:from-white group-hover:to-neutral-50 flex items-center justify-center flex-shrink-0 transition-all shadow-sm">
          {getIcon(doc.type)}
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
        <div className="flex-shrink-0">
          {getBadge(doc.type)}
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
