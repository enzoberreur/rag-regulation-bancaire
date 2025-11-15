import { useState } from 'react';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner@2.0.3';
import { UserProfile } from './UserProfile';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';

interface Session {
  id: string;
  title: string;
  timestamp: Date;
  preview: string;
}

interface SessionHistoryProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  onLogout?: () => void;
  onRestartTour?: () => void;
}

export function SessionHistory({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onLogout,
  onRestartTour
}: SessionHistoryProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);

  // Helper function to truncate text at word boundary for display
  const truncateTitle = (text: string, maxLength: number = 40): string => {
    if (text.length <= maxLength) return text;
    
    // Find the last space before maxLength
    const truncated = text.slice(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    
    // If we found a space, cut there; otherwise cut at maxLength
    const cutPoint = lastSpace > 0 ? lastSpace : maxLength;
    return text.slice(0, cutPoint) + '...';
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const handleDeleteClick = (sessionId: string) => {
    setSessionToDelete(sessionId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (sessionToDelete) {
      const session = sessions.find(s => s.id === sessionToDelete);
      onDeleteSession(sessionToDelete);
      setDeleteDialogOpen(false);
      setSessionToDelete(null);
      toast.success('Conversation deleted', {
        description: session?.title || 'The conversation has been removed'
      });
    }
  };

  return (
    <div className="w-64 bg-white flex flex-col border-r border-neutral-200 flex-shrink-0" data-tour="sidebar">
      <div className="p-4 flex-shrink-0">
        <Button
          onClick={onNewSession}
          className="w-full bg-[#0066FF] hover:bg-[#0052CC] text-white transition-smooth h-9 text-sm group"
          data-tour="new-session"
        >
          <Plus className="w-4 h-4 mr-2 group-hover:rotate-90 transition-transform duration-300" />
          New
        </Button>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="px-2 pb-4 space-y-1">
          {sessions.map(session => (
            <div
              key={session.id}
              className={`relative rounded-lg transition-all group ${
                currentSessionId === session.id
                  ? 'bg-[#E6F0FF]'
                  : 'hover:bg-neutral-50'
              }`}
            >
              <button
                onClick={() => onSelectSession(session.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg transition-all relative ${
                  currentSessionId === session.id
                    ? 'text-[#0066FF]'
                    : 'text-neutral-700'
                }`}
              >
                {currentSessionId === session.id && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-[#0066FF] rounded-full"></div>
                )}
                <div className="flex items-center justify-between gap-2 mb-1">
                  <p className="text-sm flex-1 pr-8 overflow-hidden">
                    {truncateTitle(session.title, 40)}
                  </p>
                </div>
                <p className="text-xs text-neutral-400">
                  {formatDate(session.timestamp)}
                </p>
              </button>
              
              {sessions.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteClick(session.id);
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md opacity-0 group-hover:opacity-100 hover:bg-red-50 transition-all"
                  aria-label="Delete conversation"
                >
                  <Trash2 className="w-3.5 h-3.5 text-neutral-400 hover:text-red-600 transition-colors" />
                </button>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {onLogout && (
        <div className="p-4 border-t border-neutral-100 flex-shrink-0">
          <UserProfile onLogout={onLogout} onRestartTour={onRestartTour} />
        </div>
      )}

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete this conversation and all its messages.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
