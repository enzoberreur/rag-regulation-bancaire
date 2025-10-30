# SSE Streaming Implementation

## Overview

The HexaBank Compliance Assistant now features **real-time SSE (Server-Sent Events) streaming** for LLM responses, providing a natural, progressive chat experience similar to ChatGPT and other modern AI interfaces.

## Features

✅ **Real-time streaming**: Responses appear progressively as they're generated  
✅ **Visual feedback**: Animated cursor indicator shows when streaming is active  
✅ **Smooth UX**: No blocking waits - users see content immediately  
✅ **Abort support**: Can cancel ongoing streams if needed  
✅ **Mock implementation**: Works out-of-the-box with simulated streaming  
✅ **Easy integration**: Ready to swap with real API endpoints  

## How It Works

### Current Implementation (Mock)

The application currently uses a **mock streaming function** that simulates SSE behavior:

```typescript
async function* streamResponse(fullContent: string) {
  const words = fullContent.split(' ');
  let currentChunk = '';
  
  for (let i = 0; i < words.length; i++) {
    currentChunk += (i > 0 ? ' ' : '') + words[i];
    
    // Yield chunks of 2-4 words at a time
    if (i % (2 + Math.floor(Math.random() * 3)) === 0 || i === words.length - 1) {
      yield currentChunk;
      // Simulate network delay (20-60ms per chunk)
      await new Promise(resolve => setTimeout(resolve, 20 + Math.random() * 40));
    }
  }
}
```

### Visual Indicators

1. **Loading state**: Bouncing dots appear while connecting to the stream
2. **Streaming cursor**: A pulsing blue cursor (`|`) appears at the end of streaming text
3. **Progressive rendering**: Text appears word-by-word in real-time

### State Management

The implementation tracks streaming state through:

- `isLoading`: General loading state (initial connection)
- `streamingMessageId`: Identifies which message is currently streaming
- `abortControllerRef`: Allows canceling ongoing streams

## Integration with Real APIs

To connect to a real LLM streaming endpoint:

### 1. OpenAI-Compatible API

```typescript
async function* streamLLMResponse(prompt: string, apiKey: string) {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'gpt-4',
      messages: [{ role: 'user', content: prompt }],
      stream: true,
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices[0]?.delta?.content;
          if (content) {
            yield content;
          }
        } catch (e) {
          console.error('Error parsing SSE data:', e);
        }
      }
    }
  }
}
```

### 2. Update ChatInterface.tsx

Replace the mock `streamResponse` call with your real streaming function:

```typescript
// In handleSend function, replace:
for await (const chunk of streamResponse(content)) {

// With:
for await (const chunk of streamLLMResponse(input, 'YOUR_API_KEY')) {
  if (abortControllerRef.current?.signal.aborted) break;
  
  setMessages(prev => 
    prev.map(msg => 
      msg.id === assistantMessageId 
        ? { ...msg, content: (msg.content || '') + chunk }  // Append chunks
        : msg
    )
  );
}
```

### 3. Custom Backend

For a custom backend, ensure it follows SSE format:

```
data: {"content": "Hello", "type": "token"}
data: {"content": " world", "type": "token"}
data: [DONE]
```

## Files Modified

- **`/components/ChatInterface.tsx`**: Main streaming logic
- **`/components/ChatMessage.tsx`**: Streaming cursor indicator
- **`/components/sseStreamingUtils.ts`**: Utility functions and integration examples

## Performance Considerations

- **Chunk size**: Currently 2-4 words per chunk for natural reading pace
- **Delay**: 20-60ms between chunks to simulate network latency
- **Memory**: Messages update immutably, React handles efficient re-renders
- **Abort**: Streams can be canceled via AbortController

## User Experience

The streaming implementation provides:

1. **Immediate feedback**: Users see the response start within ~300-500ms
2. **Natural reading pace**: Text appears at a comfortable reading speed
3. **Professional feel**: Matches expectations from modern AI chat interfaces
4. **No blocking**: UI remains responsive during streaming

## Future Enhancements

Potential improvements:

- [ ] Retry logic for failed streams
- [ ] Token counting during streaming
- [ ] Cost estimation in real-time
- [ ] Stream quality metrics (latency per token)
- [ ] Citation extraction during streaming
- [ ] Multi-turn conversation context

## Troubleshooting

**Stream not working?**
- Check browser console for errors
- Verify API endpoint is accessible
- Ensure CORS is configured on backend
- Check API key is valid

**Stream too fast/slow?**
- Adjust delay in `streamResponse`: `setTimeout(resolve, YOUR_DELAY_MS)`
- Modify chunk size: `i % YOUR_CHUNK_SIZE`

**Citations not appearing?**
- Citations are added with the initial message
- They don't stream separately (by design)
- Ensure `citations` array is passed when creating the message

## Security Notes

⚠️ **Never expose API keys in frontend code**  
⚠️ **Use environment variables or secure backend proxy**  
⚠️ **Implement rate limiting to prevent abuse**  
⚠️ **Validate and sanitize all user inputs**  

## References

- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [OpenAI Streaming API](https://platform.openai.com/docs/api-reference/streaming)
- [React Async Generators](https://react.dev/learn/you-might-not-need-an-effect#subscribing-to-an-external-store)
