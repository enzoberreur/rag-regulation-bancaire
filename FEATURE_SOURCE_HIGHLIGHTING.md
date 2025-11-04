# Feature: Source Highlighting with Hover Tooltips

## Overview
This feature automatically highlights text segments in LLM responses that come from specific source documents, and displays detailed source information when you hover over the highlighted text.

## How It Works

### Backend (RAG Service)
The LLM is instructed to add `[SOURCE:N]` markers after every sentence that contains information from a source document:

```
Example: "Financial institutions must maintain a capital buffer of 2.5%[SOURCE:1]. The committee must consist of at least three independent members[SOURCE:2]."
```

Where:
- `N` is the source number (1, 2, 3, etc.) corresponding to the order of sources in the context
- The marker is placed immediately after the period, before the next sentence
- Format: `[SOURCE:N]` (capital letters, colon, number, no spaces)

### Frontend (ChatMessage Component)

1. **Parsing**: The `parseTextWithSources()` function detects `[SOURCE:N]` markers and splits the text into segments
2. **Mapping**: Each segment is mapped to its corresponding citation (source document)
3. **Rendering**: Text segments with sources are wrapped in the `SourceHighlight` component
4. **Highlighting**: Each source gets a different color (blue, green, yellow, purple, pink - cycling)
5. **Tooltip**: On hover, a tooltip appears with:
   - Source number badge
   - Document name
   - Text excerpt from the source (up to 300 characters)

## Visual Design

### Highlighting Colors
- **Source 1**: Blue background (`bg-blue-100`)
- **Source 2**: Green background (`bg-green-100`)
- **Source 3**: Yellow background (`bg-yellow-100`)
- **Source 4**: Purple background (`bg-purple-100`)
- **Source 5**: Pink background (`bg-pink-100`)
- Colors repeat for sources 6+

### Tooltip Styling
- Dark background (`bg-gray-900`)
- White text with source name in bold
- Scrollable excerpt area (max height: 128px)
- Positioned above the highlighted text
- Arrow pointer connecting to the text
- Appears on hover, disappears on mouse out

## User Experience

1. **Visual Cue**: Users immediately see which parts of the response come from specific sources through color-coded highlights
2. **Information on Demand**: Hovering reveals detailed source information without cluttering the interface
3. **Multiple Sources**: Different colors make it easy to distinguish between multiple sources in the same response
4. **Seamless Integration**: The highlighting works with all existing markdown formatting (bold, line breaks, lists)

## Technical Implementation

### Key Components

1. **SourceHighlight** (`ChatMessage.tsx`):
   - React component for rendering highlighted text with tooltip
   - Props: `children` (text content), `citation` (source info), `sourceNumber` (for color)

2. **parseTextWithSources** (`ChatMessage.tsx`):
   - Parses text to extract `[SOURCE:N]` markers
   - Returns array of text segments with optional source numbers
   - Intelligently splits at sentence boundaries

3. **renderMarkdownWithHighlights** (`ChatMessage.tsx`):
   - Main rendering function
   - Processes markdown formatting while preserving source highlights
   - Falls back to simple rendering if no citations exist

### Data Flow

```
Backend LLM Response with [SOURCE:N] markers
    ↓
ChatInterface receives and cleans (keeps markers)
    ↓
ChatMessage.renderMarkdownWithHighlights()
    ↓
parseTextWithSources() extracts segments
    ↓
Each segment rendered with SourceHighlight (if has source)
    ↓
User sees colored highlights with hover tooltips
```

## Configuration

### Prompt Engineering (Backend)
The system prompt in `backend/app/services/rag_service.py` contains specific instructions for the LLM:

```python
MANDATORY INLINE CITATIONS - THIS IS CRITICAL:
You MUST add [SOURCE:N] after EVERY sentence that contains specific information from a source document.
- N is the source number (1, 2, 3, etc.) as shown in the context below
- Place [SOURCE:N] immediately after the period, BEFORE the next sentence
- Use the exact format: [SOURCE:N] (capital letters, colon, number, no spaces)
```

### Styling Customization
To modify highlight colors, edit the `colors` array in the `SourceHighlight` component:

```typescript
const colors = [
  'bg-blue-100 hover:bg-blue-200 border-blue-400',
  'bg-green-100 hover:bg-green-200 border-green-400',
  // Add more colors as needed
];
```

## Testing

To test the feature:

1. Upload regulatory documents to the RAG system
2. Ask a question that will pull information from multiple sources
3. Observe the LLM response with highlighted segments
4. Hover over highlights to see source information
5. Verify that:
   - Different sources have different colors
   - Tooltips show correct source information
   - Highlighting doesn't break markdown formatting
   - Multiple sentences from the same source are grouped together

## Future Enhancements

Potential improvements:
- Click to jump to full source document
- Filter/search by source
- Show confidence scores in tooltips
- Customizable color schemes
- Mobile-friendly touch interactions
- Keyboard navigation for accessibility
