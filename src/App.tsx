import { useState } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { SessionHistory } from './components/SessionHistory';
import { ObservabilityPanel } from './components/ObservabilityPanel';
import { Toaster } from './components/ui/sonner';

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
}

interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  uploadedAt: Date;
  type: 'regulation' | 'policy' | 'document';
}

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([
    {
      id: '1',
      title: 'ACPR Regulation 2024-15',
      timestamp: new Date(2025, 9, 30, 10, 30),
      preview: 'Analyze new capital requirements regulation...',
      messages: [
        {
          id: '1',
          role: 'user',
          content: 'Can you analyze the ACPR Regulation 2024-15 requirements on climate-related capital and check if our current Risk Management Policy RMP-2024-03 is compliant?',
          timestamp: new Date(2025, 9, 30, 10, 30)
        },
        {
          id: '2',
          role: 'assistant',
          content: "Based on the ACPR Regulation 2024-15, Article 12 requires enhanced capital requirements for climate-related exposures. Cross-referencing with HexaBank's Risk Management Policy (RMP-2024-03), Section 4.2, there appears to be a gap in the current climate risk assessment framework.\n\nKey Findings:\n\n1. COMPLIANCE GAP IDENTIFIED\nACPR Regulation 2024-15, Article 12 mandates quantitative climate exposure assessments with monthly reporting. Your current RMP-2024-03 Section 4.2 only addresses qualitative climate risk considerations without specific quantification methodologies.\n\n2. REGULATORY REQUIREMENTS\n• Article 12(3) requires monthly climate exposure reporting to supervisory authorities\n• Article 15 mandates establishment of a dedicated Climate Risk Committee at board level\n• Article 18 specifies minimum capital buffer of 2.5% for high climate risk exposures\n\n3. RECOMMENDED ACTIONS\n• Update RMP-2024-03 Section 4.2 to include climate exposure quantification methodology aligned with ACPR standards\n• Implement automated monthly reporting system for climate-related capital requirements\n• Establish Climate Risk Committee per Article 15 requirements\n• Conduct gap analysis for capital buffer requirements under Article 18\n\n4. TIMELINE\nCompliance deadline: December 31, 2025\nRecommended completion: Q3 2025 to allow for testing and validation\n\nThe analysis indicates medium-high priority action is required to achieve full compliance with ACPR 2024-15.",
          citations: [
            { id: '1', text: 'ACPR Regulation 2024-15, Article 12: Climate Capital Requirements', source: 'ACPR Official Journal', url: '/regulations/acpr-2024-15' },
            { id: '2', text: 'ACPR Regulation 2024-15, Article 15: Governance Requirements', source: 'ACPR Official Journal', url: '/regulations/acpr-2024-15' },
            { id: '3', text: 'ACPR Regulation 2024-15, Article 18: Capital Buffer Specifications', source: 'ACPR Official Journal', url: '/regulations/acpr-2024-15' },
            { id: '4', text: 'HexaBank RMP-2024-03, Section 4.2: Climate Risk Framework', source: 'Internal Policy Document', url: '/policies/rmp-2024-03' },
            { id: '5', text: 'Compliance Gap: Quantitative climate exposure methodology missing', source: 'Automated Analysis', url: '/analysis/gaps' }
          ],
          timestamp: new Date(2025, 9, 30, 10, 31)
        }
      ]
    }
  ]);

  const [currentSessionId, setCurrentSessionId] = useState<string>('1');
  const [metrics, setMetrics] = useState<ObservabilityMetrics>({
    latency: 245,
    errors: 0,
    cost: 0.0023,
    tokensUsed: 1247
  });
  
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);

  const handleNewSession = () => {
    const newSession: Session = {
      id: Date.now().toString(),
      title: 'New Analysis',
      timestamp: new Date(),
      preview: 'Start regulatory analysis...',
      messages: []
    };
    setSessions([newSession, ...sessions]);
    setCurrentSessionId(newSession.id);
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
                ? messages[0].content.slice(0, 50) + (messages[0].content.length > 50 ? '...' : '')
                : session.title,
              preview: messages.length > 0 && messages[0].role === 'user'
                ? messages[0].content.slice(0, 80) + (messages[0].content.length > 80 ? '...' : '')
                : session.preview
            }
          : session
      )
    );
  };

  const handleDeleteSession = (sessionId: string) => {
    // Don't allow deleting the last session
    if (sessions.length === 1) {
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
  
  const handleDocumentUpload = (doc: UploadedDocument) => {
    setDocuments(prev => [...prev, doc]);
  };

  return (
    <div className="flex h-screen bg-neutral-50 overflow-hidden">
      <SessionHistory
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
      />
      
      <div className="flex flex-col flex-1 min-w-0">
        {currentSession && (
          <ChatInterface
            sessionId={currentSessionId}
            messages={currentSession.messages}
            onUpdateMessages={(messages) => handleUpdateSessionMessages(currentSessionId, messages)}
            onUpdateMetrics={updateMetrics}
            documents={documents}
            onDocumentUpload={handleDocumentUpload}
          />
        )}
        
        <ObservabilityPanel metrics={metrics} />
      </div>
      
      <Toaster />
    </div>
  );
}
