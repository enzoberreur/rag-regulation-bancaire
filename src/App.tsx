import { useState, useEffect } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { SessionHistory } from './components/SessionHistory';
import { ObservabilityPanel } from './components/ObservabilityPanel';
import { LoginModal } from './components/LoginModal';
import { UserProfile } from './components/UserProfile';
import { OnboardingTour } from './components/OnboardingTour';
import { Toaster } from './components/ui/sonner';
import { getDocuments } from './services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
}

interface Citation {
  id: string;
  text: string;
  source: string;
  url?: string;
}

interface Session {
  id: string;
  title: string;
  timestamp: Date;
  preview: string;
  messages: Message[];
}

interface ObservabilityMetrics {
  latency: number;
  errors: number;
  cost: number;
  tokensUsed: number;
  citationsCount?: number;
  averageSimilarityScore?: number;
}

interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  uploadedAt: Date;
  type: 'regulation' | 'policy' | 'document';
}

export default function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Onboarding tour state
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Start with empty state - no mock data
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Helper function to get user-specific localStorage keys
  // Defined outside useEffect to avoid dependency issues
  const getUserStorageKey = (key: string) => {
    const userEmail = 'enzo.berreur@gmail.com';
    return `${key}_${userEmail}`;
  };

  // Check if user is already authenticated (from localStorage) and load sessions in one go
  useEffect(() => {
    const savedAuth = localStorage.getItem('isAuthenticated');
    const isAuth = savedAuth === 'true';
    
    if (isAuth) {
      // Load sessions from localStorage (user-specific)
      // First try user-specific key, then fallback to old key for migration
      let savedSessions = localStorage.getItem(getUserStorageKey('chatSessions'));
      let savedCurrentSessionId = localStorage.getItem(getUserStorageKey('currentSessionId'));
      
      // Migrate old sessions to user-specific key if they exist
      if (!savedSessions) {
        const oldSessions = localStorage.getItem('chatSessions');
        const oldSessionId = localStorage.getItem('currentSessionId');
        if (oldSessions) {
          localStorage.setItem(getUserStorageKey('chatSessions'), oldSessions);
          savedSessions = oldSessions;
          // Clean up old keys
          localStorage.removeItem('chatSessions');
        }
        if (oldSessionId) {
          localStorage.setItem(getUserStorageKey('currentSessionId'), oldSessionId);
          savedCurrentSessionId = oldSessionId;
          localStorage.removeItem('currentSessionId');
        }
      }
      
      if (savedSessions) {
        try {
          const parsedSessions: Session[] = JSON.parse(savedSessions).map((session: any) => ({
            ...session,
            timestamp: new Date(session.timestamp),
            messages: session.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
              citations: msg.citations || []
            }))
          }));
          setSessions(parsedSessions);
          
          if (savedCurrentSessionId && parsedSessions.find(s => s.id === savedCurrentSessionId)) {
            setCurrentSessionId(savedCurrentSessionId);
          } else if (parsedSessions.length > 0) {
            setCurrentSessionId(parsedSessions[0].id);
          }
        } catch (error) {
          console.error('Failed to load sessions from localStorage:', error);
        }
      }
    } else {
      // For blurred background, create a dummy session
      const newSession: Session = {
        id: Date.now().toString(),
        title: 'New Analysis',
        timestamp: new Date(),
        preview: 'Start regulatory analysis...',
        messages: []
      };
      setSessions([newSession]);
      setCurrentSessionId(newSession.id);
    }
    
    setIsAuthenticated(isAuth);
    setIsInitialized(true);
  }, []);

  // Load sessions when user logs in (after logout/login cycle)
  useEffect(() => {
    if (!isAuthenticated) return;
    
    // Skip if sessions are already loaded during initial mount (to avoid overwriting)
    if (sessions.length > 0 && isInitialized) return;
    
    // Load sessions from localStorage (user-specific)
    const savedSessions = localStorage.getItem(getUserStorageKey('chatSessions'));
    const savedCurrentSessionId = localStorage.getItem(getUserStorageKey('currentSessionId'));
    
    if (savedSessions) {
      try {
        const parsedSessions: Session[] = JSON.parse(savedSessions).map((session: any) => ({
          ...session,
          timestamp: new Date(session.timestamp),
          messages: session.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
            citations: msg.citations || []
          }))
        }));
        
        // This handles the case when user logs in after logout
        setSessions(parsedSessions);
        
        if (savedCurrentSessionId && parsedSessions.find(s => s.id === savedCurrentSessionId)) {
          setCurrentSessionId(savedCurrentSessionId);
        } else if (parsedSessions.length > 0) {
          setCurrentSessionId(parsedSessions[0].id);
        }
      } catch (error) {
        console.error('Failed to load sessions from localStorage:', error);
      }
    }
  }, [isAuthenticated]);

  const handleLogin = () => {
    setIsAuthenticated(true);
    localStorage.setItem('isAuthenticated', 'true');
    
    // TEMPORARILY REMOVE THE CHECK - always show tour for debugging
    console.log('Login - forcing onboarding tour');
    setTimeout(() => {
      console.log('Setting showOnboarding to true');
      setShowOnboarding(true);
    }, 500);
  };
  
  const handleCompleteOnboarding = () => {
    console.log('Completing onboarding');
    setShowOnboarding(false);
    localStorage.setItem('hasSeenOnboarding', 'true');
  };
  
  const handleRestartTour = () => {
    console.log('Restarting tour');
    setShowOnboarding(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('isAuthenticated');
    // Don't remove sessions - they are linked to the account and will persist
    setSessions([]);
    setCurrentSessionId(null);
    setIsInitialized(false);
  };

  // Save sessions to localStorage whenever they change (but skip on initial load)
  // Sessions are saved with user-specific key to persist across login/logout
  useEffect(() => {
    if (!isInitialized || !isAuthenticated) return;
    // Always save sessions, even if empty (to preserve state)
    localStorage.setItem(getUserStorageKey('chatSessions'), JSON.stringify(sessions));
  }, [sessions, isInitialized, isAuthenticated]);

  // Save current session ID to localStorage whenever it changes (but skip on initial load)
  // Session ID is saved with user-specific key to persist across login/logout
  useEffect(() => {
    if (!isInitialized || !isAuthenticated) return;
    if (currentSessionId) {
      localStorage.setItem(getUserStorageKey('currentSessionId'), currentSessionId);
    }
  }, [currentSessionId, isInitialized, isAuthenticated]);
  const [metrics, setMetrics] = useState<ObservabilityMetrics>({
    latency: 0,
    errors: 0,
    cost: 0,
    tokensUsed: 0,
    citationsCount: 0,
    averageSimilarityScore: 0
  });
  
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);

  // Load documents from backend on mount
  useEffect(() => {
    const loadDocuments = async () => {
      setDocumentsLoading(true);
      try {
        const apiDocs = await getDocuments();
        const convertedDocs: UploadedDocument[] = apiDocs.map(doc => ({
          id: doc.id,
          name: doc.name,
          size: doc.size,
          uploadedAt: new Date(doc.uploaded_at),
          type: doc.type,
        }));
        setDocuments(convertedDocs);
        console.log(`✅ Loaded ${convertedDocs.length} documents from backend`);
      } catch (error) {
        // Log error but don't block the app
        console.error('Failed to load documents from backend:', error);
        // Keep empty array - user can still use the app
        setDocuments([]);
      } finally {
        setDocumentsLoading(false);
      }
    };
    loadDocuments();
  }, []);

  // Create initial session if none exists after loading (only if authenticated and no sessions in localStorage)
  useEffect(() => {
    if (!isInitialized) return;
    if (!isAuthenticated) return;
    
    // Wait a bit to let the session loading useEffect complete first
    const timer = setTimeout(() => {
      // Only create new session if no sessions exist and no current session
      // This means no sessions were loaded from localStorage
      if (sessions.length === 0 && currentSessionId === null) {
        const savedSessions = localStorage.getItem(getUserStorageKey('chatSessions'));
        // Double check localStorage before creating new session
        if (!savedSessions || savedSessions === '[]') {
          const newSession: Session = {
            id: Date.now().toString(),
            title: 'New Analysis',
            timestamp: new Date(),
            preview: 'Start regulatory analysis...',
            messages: []
          };
          setSessions([newSession]);
          setCurrentSessionId(newSession.id);
        }
      }
    }, 100);
    
    return () => clearTimeout(timer);
  }, [isInitialized, isAuthenticated, sessions.length, currentSessionId]);

  const handleDocumentUpload = (doc: UploadedDocument) => {
    setDocuments(prev => [...prev, doc]);
  };

  const handleDocumentRemove = (docId: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== docId));
  };

  const handleNewSession = () => {
    const newSession: Session = {
      id: Date.now().toString(),
      title: 'New Analysis',
      timestamp: new Date(),
      preview: 'Start regulatory analysis...',
      messages: []
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  };

  // Helper function to truncate text at word boundary
  const truncateAtWord = (text: string, maxLength: number): string => {
    if (text.length <= maxLength) return text;
    
    // Find the last space before maxLength
    const truncated = text.slice(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    
    // If we found a space, cut there; otherwise cut at maxLength
    const cutPoint = lastSpace > 0 ? lastSpace : maxLength;
    return text.slice(0, cutPoint) + '...';
  };

  const handleUpdateSessionMessages = (sessionId: string, messages: Message[]) => {
    setSessions(prev => 
      prev.map(session => 
        session.id === sessionId 
          ? { 
              ...session, 
              messages,
              // Update title and preview based on first user message
              title: messages.length > 0 && messages[0].role === 'user' 
                ? truncateAtWord(messages[0].content, 50)
                : session.title,
              preview: messages.length > 0 && messages[0].role === 'user'
                ? truncateAtWord(messages[0].content, 80)
                : session.preview
            }
          : session
      )
    );
  };

  const handleDeleteSession = (sessionId: string) => {
    // Don't allow deleting the last session - create a new one instead
    if (sessions.length === 1) {
      handleNewSession();
      return;
    }

    // If deleting the current session, switch to another one
    if (sessionId === currentSessionId) {
      const currentIndex = sessions.findIndex(s => s.id === sessionId);
      const nextSession = sessions[currentIndex + 1] || sessions[currentIndex - 1];
      if (nextSession) {
        setCurrentSessionId(nextSession.id);
      }
    }

    // Remove the session
    setSessions(prev => prev.filter(s => s.id !== sessionId));
  };

  const currentSession = sessions.find(s => s.id === currentSessionId);

  const handleSelectSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
  };

  const updateMetrics = (newMetrics: Partial<ObservabilityMetrics>) => {
    setMetrics(prev => ({ ...prev, ...newMetrics }));
  };

  return (
    <>
      {!isAuthenticated ? (
        <div className="h-screen w-screen relative overflow-hidden">
          {/* Blurred background */}
          <div className="absolute inset-0 bg-neutral-50 backdrop-blur-md" style={{ filter: 'blur(8px)' }}>
            <div className="flex h-screen bg-neutral-50 overflow-hidden opacity-40">
              <SessionHistory
                sessions={sessions}
                currentSessionId={currentSessionId}
                onSelectSession={handleSelectSession}
                onNewSession={handleNewSession}
                onDeleteSession={handleDeleteSession}
                onLogout={handleLogout}
              />
              
              <div className="flex flex-col flex-1 min-w-0">
                {currentSession ? (
                  <ChatInterface
                    sessionId={currentSessionId!}
                    messages={currentSession.messages}
                    onUpdateMessages={(messages) => handleUpdateSessionMessages(currentSessionId!, messages)}
                    onUpdateMetrics={updateMetrics}
                    documents={documents}
                    onDocumentUpload={handleDocumentUpload}
                    onDocumentRemove={handleDocumentRemove}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <p className="text-neutral-500 mb-4">No session selected</p>
                      <button
                        onClick={handleNewSession}
                        className="px-4 py-2 bg-[#0066FF] text-white rounded-lg hover:bg-[#0052CC]"
                      >
                        Create New Session
                      </button>
                    </div>
                  </div>
                )}
                
                <ObservabilityPanel metrics={metrics} />
              </div>
            </div>
          </div>
          {/* Login Modal */}
          <LoginModal isOpen={true} onLogin={handleLogin} />
        </div>
      ) : (
        <div className="flex h-screen bg-neutral-50 overflow-hidden relative">
          <SessionHistory
            sessions={sessions}
            currentSessionId={currentSessionId}
            onSelectSession={handleSelectSession}
            onNewSession={handleNewSession}
            onDeleteSession={handleDeleteSession}
            onLogout={handleLogout}
            onRestartTour={handleRestartTour}
          />
          
          <div className="flex flex-col flex-1 min-w-0 relative">
            {currentSession ? (
              <ChatInterface
                sessionId={currentSessionId!}
                messages={currentSession.messages}
                onUpdateMessages={(messages) => handleUpdateSessionMessages(currentSessionId!, messages)}
                onUpdateMetrics={updateMetrics}
                documents={documents}
                onDocumentUpload={handleDocumentUpload}
                onDocumentRemove={handleDocumentRemove}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <p className="text-neutral-500 mb-4">No session selected</p>
                  <button
                    onClick={handleNewSession}
                    className="px-4 py-2 bg-[#0066FF] text-white rounded-lg hover:bg-[#0052CC]"
                  >
                    Create New Session
                  </button>
                </div>
              </div>
            )}
            
            <ObservabilityPanel metrics={metrics} />
          </div>
          <Toaster />
          <OnboardingTour isOpen={showOnboarding} onComplete={handleCompleteOnboarding} />
        </div>
      )}
    </>
  );
}
