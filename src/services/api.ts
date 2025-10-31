/**
 * API client for backend communication
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  uploaded_at: string;
  type: 'regulation' | 'policy' | 'document';
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  history?: ChatMessage[];
}

export interface Citation {
  id: string;
  text: string;
  source: string;
  url?: string;
}

export interface ChatResponse {
  content: string;
  citations: Citation[];
}

/**
 * Upload a document to the backend
 */
export async function uploadDocument(
  file: File
): Promise<UploadedDocument> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload document');
  }

  const data = await response.json();
  return {
    id: data.id,
    name: data.name,
    size: data.size,
    uploaded_at: data.uploaded_at,
    type: data.type,
  };
}

/**
 * Get all uploaded documents
 */
export async function getDocuments(): Promise<UploadedDocument[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = 'Failed to fetch documents';
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  
  // Ensure we return an array
  if (!Array.isArray(data)) {
    console.warn('Expected array from getDocuments, got:', typeof data);
    return [];
  }
  
  return data.map((doc: any) => ({
    id: doc.id,
    name: doc.name,
    size: doc.size,
    uploaded_at: doc.uploaded_at,
    type: doc.type || 'document', // Default to 'document' if not specified
  }));
}

/**
 * Delete a document
 */
export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete document');
  }
}

/**
 * Send a chat message (non-streaming)
 */
export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to send message');
  }

  return await response.json();
}

/**
 * Send a chat message with streaming (SSE)
 */
export async function* streamChatMessage(
  request: ChatRequest,
  signal?: AbortSignal
): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to stream message');
  }

  if (!response.body) {
    throw new Error('No response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        // Process remaining buffer
        if (buffer.trim()) {
          // Handle remaining buffer that might contain incomplete SSE data
          const lines = buffer.split('\n');
          for (const line of lines) {
            if (!line.trim()) continue; // Skip empty lines
            
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // Don't trim - preserve formatting!
              if (data.trim() && data.trim() !== '[DONE]') {
                yield data; // Preserve formatting
              }
            } else if (line.trim() === '[DONE]') {
              return;
            }
          }
        }
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      
      // Process complete lines
      while (buffer.includes('\n')) {
        const newlineIndex = buffer.indexOf('\n');
        const line = buffer.slice(0, newlineIndex);
        buffer = buffer.slice(newlineIndex + 1);

        // Skip empty lines (only whitespace)
        if (!line.trim()) continue;
        
        // Handle SSE data lines
        if (line.startsWith('data: ')) {
          // Remove 'data: ' prefix and trim only trailing whitespace/newlines
          // Keep leading spaces and internal formatting
          let data = line.slice(6);
          // Remove trailing whitespace/newlines added by SSE format, but preserve internal content
          data = data.replace(/[\r\n]+$/, '');
          
          if (data.trim() === '[DONE]') return;

          // Try to parse as JSON (for citations or metrics)
          try {
            const parsed = JSON.parse(data.trim()); // Only trim for JSON parsing
            if (parsed.type === 'citations' || parsed.type === 'metrics' || parsed.type === 'usage_info') {
              yield data.trim(); // Yield trimmed JSON string for parsing
              continue;
            }
          } catch {
            // Not JSON, treat as text content - preserve formatting but remove trailing newlines
          }
          
          // Yield text content (preserve spaces, but remove trailing newlines from SSE format)
          if (data.trim()) {
            yield data; // Content without trailing SSE newlines
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

