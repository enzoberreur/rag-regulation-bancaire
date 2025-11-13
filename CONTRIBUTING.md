# Contributing to HexaBank Compliance Assistant

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Code of Conduct

This project is part of Albert School's educational program. We expect all contributors to:

- Be respectful and professional
- Provide constructive feedback
- Focus on learning and collaboration
- Help maintain code quality

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector
- Git
- OpenAI API key

### Local Setup

1. **Fork and Clone**
   ```bash
   gh repo fork enzoberreur/LLM_PRODUCT
   cd LLM_PRODUCT
   ```

2. **Install Backend Dependencies**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies**
   ```bash
   cd ..
   npm install
   ```

4. **Setup Environment**
   ```bash
   cp backend/env.example backend/.env
   # Edit .env with your credentials
   ```

5. **Initialize Database**
   ```bash
   cd backend
   python scripts/init_db.py
   ```

6. **Run Development Servers**
   ```bash
   # From project root
   ./run.sh
   ```

## Development Workflow

### Branch Strategy

We use a simplified Git Flow:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes

### Creating a Feature Branch

```bash
# Update your local main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature"

# Push to your fork
git push origin feature/your-feature-name
```

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(rag): add query reformulation with GPT-4o-mini
fix(citations): use chunk UUID instead of constructed ID
docs(readme): add deployment section
perf(embeddings): implement singleton pattern for model loading
```

## Code Style

### Python (Backend)

We use **Black** formatter and **isort** for imports:

```bash
# Format code
black backend/app
isort backend/app

# Check style
flake8 backend/app
mypy backend/app
```

**Style Guidelines:**
- Line length: 88 characters (Black default)
- Quotes: Double quotes for strings
- Type hints: Required for all functions
- Docstrings: Google style

**Example:**
```python
from typing import List, Optional

async def process_document(
    file_path: str,
    chunk_size: int = 800,
    overlap: int = 150
) -> List[DocumentChunk]:
    """
    Process a document into semantic chunks.
    
    Args:
        file_path: Path to the document file
        chunk_size: Maximum tokens per chunk
        overlap: Token overlap between chunks
        
    Returns:
        List of processed document chunks
        
    Raises:
        ValueError: If file_path is invalid
        IOError: If file cannot be read
    """
    pass
```

### TypeScript (Frontend)

We use **ESLint** and **Prettier**:

```bash
# Format code
npm run format

# Check style
npm run lint
```

**Style Guidelines:**
- Use TypeScript strict mode
- Prefer const over let
- Use arrow functions
- Interface over type for object shapes
- Named exports over default exports

**Example:**
```typescript
interface Citation {
  id: string;
  text: string;
  source: string;
  url?: string;
}

export const formatCitation = (citation: Citation): string => {
  const { source, url } = citation;
  return url ? `${source} (${url})` : source;
};
```

### Project-Specific Conventions

#### Logging
Use emojis for visual clarity:
```python
print("🔍 Query reformulée:", query)
print("🔄 Reranking de", len(chunks), "chunks...")
print("✅ Traitement terminé")
print("❌ Erreur:", error)
print("📊 Statistiques:", stats)
```

#### Error Handling
```python
# Backend
try:
    result = await process_query(query)
except ValueError as e:
    logger.error(f"❌ Invalid query: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"❌ Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

```typescript
// Frontend
try {
  const response = await fetch('/api/chat/stream');
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
} catch (error) {
  console.error('❌ Stream error:', error);
  setError(error instanceof Error ? error.message : 'Unknown error');
}
```

## Testing

### Backend Tests

We use **pytest**:

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_rag_service.py

# Run specific test
pytest tests/test_rag_service.py::test_query_reformulation
```

**Test Structure:**
```python
# tests/test_rag_service.py
import pytest
from app.services.rag_service import RAGService

@pytest.fixture
def rag_service(db_session):
    return RAGService(db_session)

def test_query_reformulation(rag_service):
    """Test that query reformulation adds relevant context"""
    original = "ratios de capital"
    reformed = await rag_service._reformulate_query(original)
    
    assert len(reformed) > len(original)
    assert "Bâle III" in reformed or "CRD4" in reformed
    assert "fonds propres" in reformed or "CET1" in reformed

@pytest.mark.asyncio
async def test_reranking(rag_service, sample_chunks):
    """Test that reranking improves relevance order"""
    query = "What are the capital requirements?"
    
    reranked = await rag_service.reranker.rerank(
        query, sample_chunks
    )
    
    # Top result should have higher relevance
    assert reranked[0].score > reranked[-1].score
```

### Frontend Tests

We use **Vitest** and **React Testing Library**:

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

**Test Example:**
```typescript
// src/components/__tests__/CitationChip.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { CitationChip } from '../CitationChip';

describe('CitationChip', () => {
  const mockCitation = {
    id: '123',
    text: 'Les établissements doivent...',
    source: 'ACPR Guide, p.23',
    url: '/documents/456'
  };

  it('renders citation badge', () => {
    render(<CitationChip citation={mockCitation} />);
    expect(screen.getByText('ACPR Guide, p.23')).toBeInTheDocument();
  });

  it('shows tooltip on hover', async () => {
    render(<CitationChip citation={mockCitation} />);
    const badge = screen.getByText('ACPR Guide, p.23');
    
    fireEvent.mouseEnter(badge);
    
    expect(await screen.findByText(/Les établissements/)).toBeInTheDocument();
  });

  it('opens document on click', () => {
    const mockOpen = vi.spyOn(window, 'open').mockImplementation();
    
    render(<CitationChip citation={mockCitation} />);
    fireEvent.click(screen.getByText('ACPR Guide, p.23'));
    
    expect(mockOpen).toHaveBeenCalledWith(
      expect.stringContaining('/documents/456'),
      '_blank'
    );
  });
});
```

### Integration Tests

Test the full RAG pipeline:

```bash
# Run integration tests
pytest tests/integration/

# Test with real OpenAI API (uses credits)
pytest tests/integration/ --use-real-api
```

## Pull Request Process

### Before Submitting

1. **Update your branch**
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run tests**
   ```bash
   # Backend
   cd backend
   pytest
   black --check app
   
   # Frontend
   cd ..
   npm test
   npm run lint
   ```

3. **Update documentation**
   - Update README.md if needed
   - Add CHANGELOG.md entry
   - Update API docs if endpoints changed

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] CHANGELOG.md updated

## Screenshots (if applicable)
Add screenshots for UI changes.

## Related Issues
Fixes #123
Related to #456
```

### Review Process

1. At least one approval required from maintainers
2. All CI checks must pass
3. No merge conflicts
4. Code coverage must not decrease

### After Merge

1. Delete your feature branch
2. Update your local repository
3. Celebrate! 🎉

## Project Structure

```
LLMOPS-product/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── chat.py       # Chat routes
│   │   │   ├── documents.py  # Document routes
│   │   │   └── health.py     # Health check
│   │   ├── core/             # Core functionality
│   │   │   ├── config.py     # Configuration
│   │   │   └── database.py   # DB connection
│   │   ├── models/           # SQLAlchemy models
│   │   │   └── document.py
│   │   ├── services/         # Business logic
│   │   │   ├── rag_service.py          # Main RAG
│   │   │   ├── embedding_service.py    # Embeddings
│   │   │   ├── reranker_service.py     # Reranking
│   │   │   ├── document_processor.py   # Chunking
│   │   │   └── text_extractor.py       # PDF extraction
│   │   └── main.py           # FastAPI app
│   ├── tests/                # Test files
│   ├── scripts/              # Utility scripts
│   └── requirements.txt      # Python deps
├── src/
│   ├── components/           # React components
│   ├── services/             # API client
│   └── hooks/                # Custom hooks
├── docs/                     # Documentation
├── README.md
├── CHANGELOG.md
└── CONTRIBUTING.md          # This file
```

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email [security@example.com]
- **Chat**: Join our Discord server (if applicable)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to HexaBank Compliance Assistant! 🎉
