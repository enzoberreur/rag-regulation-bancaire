/**
 * SSE Streaming Utilities
 * 
 * This file contains utilities for integrating with real SSE (Server-Sent Events) streaming APIs
 * for LLM responses. Currently using a mock implementation, but can be easily swapped with real endpoints.
 */

/**
 * Example: Real SSE streaming implementation
 * 
 * To use with a real API endpoint (e.g., OpenAI, Anthropic, or custom LLM backend):
 * 
 * ```typescript
 * async function* streamLLMResponse(
 *   prompt: string,
 *   apiKey: string,
 *   endpoint: string = 'https://api.example.com/v1/chat/completions'
 * ): AsyncGenerator<string, void, unknown> {
 *   const response = await fetch(endpoint, {
 *     method: 'POST',
 *     headers: {
 *       'Content-Type': 'application/json',
 *       'Authorization': `Bearer ${apiKey}`,
 *     },
 *     body: JSON.stringify({
 *       model: 'gpt-4',
 *       messages: [{ role: 'user', content: prompt }],
 *       stream: true,
 *     }),
 *   });
 * 
 *   if (!response.body) {
 *     throw new Error('No response body');
 *   }
 * 
 *   const reader = response.body.getReader();
 *   const decoder = new TextDecoder();
 *   let buffer = '';
 * 
 *   while (true) {
 *     const { done, value } = await reader.read();
 *     if (done) break;
 * 
 *     buffer += decoder.decode(value, { stream: true });
 *     const lines = buffer.split('\n');
 *     buffer = lines.pop() || '';
 * 
 *     for (const line of lines) {
 *       if (line.startsWith('data: ')) {
 *         const data = line.slice(6);
 *         if (data === '[DONE]') return;
 * 
 *         try {
 *           const parsed = JSON.parse(data);
 *           const content = parsed.choices[0]?.delta?.content;
 *           if (content) {
 *             yield content;
 *           }
 *         } catch (e) {
 *           console.error('Error parsing SSE data:', e);
 *         }
 *       }
 *     }
 *   }
 * }
 * ```
 * 
 * Integration with ChatInterface:
 * 
 * Replace the mock `streamResponse` function with:
 * ```typescript
 * for await (const chunk of streamLLMResponse(input, 'YOUR_API_KEY')) {
 *   if (abortControllerRef.current?.signal.aborted) break;
 *   
 *   setMessages(prev => 
 *     prev.map(msg => 
 *       msg.id === assistantMessageId 
 *         ? { ...msg, content: (msg.content || '') + chunk }
 *         : msg
 *     )
 *   );
 * }
 * ```
 */

export interface StreamingConfig {
  endpoint: string;
  apiKey?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
}

/**
 * Generic SSE stream parser
 * Handles standard SSE format with "data: " prefix
 */
export async function* parseSSEStream(
  response: Response
): AsyncGenerator<string, void, unknown> {
  if (!response.body) {
    throw new Error('No response body available for streaming');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          
          // Common SSE termination signals
          if (data === '[DONE]' || data === '') continue;

          yield data;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Error handling for streaming requests
 */
export class StreamingError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: Response
  ) {
    super(message);
    this.name = 'StreamingError';
  }
}

/**
 * Abort controller wrapper for canceling streams
 */
export function createStreamController() {
  const controller = new AbortController();
  
  return {
    signal: controller.signal,
    abort: () => controller.abort(),
    isAborted: () => controller.signal.aborted,
  };
}
