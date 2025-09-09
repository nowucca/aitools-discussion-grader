# Technical Context: Multi-Discussion Grading System

## Technologies Used

### Core Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Primary programming language | 3.11+ |
| uv | Modern Python package manager | Latest |
| Click | Command-line interface framework | 8.0+ |
| Anthropic Claude API | AI for grading and synthesis | Claude 3 Opus |
| OpenAI API | Alternative AI provider | GPT-4 |
| pytest | Testing framework | 8.0+ |
| pyperclip | Clipboard integration | 1.8+ |
| tabulate | Table formatting for CLI output | 0.9+ |

### Python Libraries

| Library | Purpose |
|---------|---------|
| **anthropic** | Client for Claude API |
| **openai** | Client for OpenAI API and compatible services |
| **python-dotenv** | Environment variable management |
| **json** | JSON parsing and serialization |
| **os / pathlib** | Filesystem operations |
| **dataclasses** | Structured data objects |
| **typing** | Type hints for better code quality |
| **click** | CLI framework |
| **pytest** | Testing framework |
| **unittest.mock** | Mocking for tests |
| **pyperclip** | System clipboard access |
| **tabulate** | Table formatting |
| **hashlib** | Content hashing for duplicate detection |

## Development Setup

### Modern Environment Setup (uv package manager)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies (creates .venv automatically)
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run commands with uv (alternative to activation)
uv run python discussion-grader/grader.py discussion list
```

### Legacy Environment Setup (pip)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix/MacOS:
source .venv/bin/activate

# Install dependencies
pip install -r discussion-grader/requirements.txt
```

### Required Environment Variables

- **AI Provider Configuration**:
  - `ANTHROPIC_API_KEY`: For Claude API access
  - `OPENAI_API_KEY`: For OpenAI API access
  - `AI_PROVIDER`: Default provider selection (`anthropic` or `openai`)
  - `OPENAI_BASE_URL`: Custom API endpoints for OpenAI-compatible services

### Configuration Files

- **Project Configuration**: `pyproject.toml`
  ```toml
  [build-system]
  requires = ["setuptools>=45", "wheel"]
  build-backend = "setuptools.build_meta"
  
  [project]
  name = "discussion-grader"
  version = "1.0.0"
  dependencies = [
      "anthropic>=0.25.0",
      "openai>=1.30.0",
      "python-dotenv>=1.0.0",
      "click>=8.1.0",
      "pytest>=8.0.0",
      "pyperclip>=1.8.0",
      "tabulate>=0.9.0",
  ]
  ```

- **System Configuration**: `discussion-grader/config/config.json`
  ```json
  {
    "ai": {
      "provider": "anthropic",
      "anthropic": {
        "model": "claude-3-opus-20240229",
        "temperature": 0,
        "max_tokens": 4096
      },
      "openai": {
        "model": "gpt-4",
        "base_url": "https://api.openai.com/v1",
        "temperature": 0,
        "max_tokens": 4096
      }
    },
    "synthesis": {
      "prompt": "You are synthesizing student responses...",
      "max_submissions": 50
    },
    "grading": {
      "default_points": 8,
      "default_min_words": 100
    }
  }
  ```

- **Environment Variables**: `.env` (optional)
  ```env
  ANTHROPIC_API_KEY=your-claude-api-key
  OPENAI_API_KEY=your-openai-api-key
  AI_PROVIDER=anthropic
  ```

## Technical Constraints

### 1. API Limitations

- **Rate Limits**: Claude API has rate limits that may affect batch processing of large numbers of submissions
- **Token Limits**: Maximum context window size limits the length of submissions and number of submissions that can be synthesized at once
- **Latency**: API calls introduce latency that must be handled gracefully

### 2. File System Constraints

- **Permissions**: The application needs read/write access to its directories
- **Storage**: Storing all submissions and grades requires adequate disk space
- **Concurrency**: No built-in locking mechanisms for concurrent access

### 3. Clipboard Constraints

- **OS Integration**: Clipboard functionality is OS-dependent
- **Size Limits**: Large content may not copy correctly to clipboard
- **Formatting**: Plain text limitations for clipboard content

## Tool Usage Patterns

### 1. Anthropic API Usage

```python
import anthropic

def grade_submission(api_key, question, submission, total_points=12):
    """Grade a submission using Claude API."""
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""
    You are an instructor grading a student's discussion response. The question is:

    {question}

    The student's submission is:

    {submission}

    Please grade this submission out of {total_points} points based on...
    """
    
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        temperature=0,
        system="You are an expert instructor grading computer science discussions...",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract JSON from response
    response_text = response.content[0].text
    # Process response...
    
    return result
```

### 2. Click CLI Pattern

```python
import click

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Discussion grading system for multiple class discussions."""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose

@cli.group()
@click.pass_context
def discussion(ctx):
    """Manage discussion questions."""
    # Initialize controller...

@discussion.command('create')
@click.option('--title', '-t', required=True, help='Discussion title')
@click.option('--points', '-p', default=12, help='Total points')
@click.pass_context
def discussion_create(ctx, title, points):
    """Create a new discussion."""
    # Call controller...

if __name__ == '__main__':
    cli(obj={})
```

### 3. Filesystem Operations Pattern

```python
from pathlib import Path
import json
import os

def save_discussion_metadata(discussion_id, metadata, base_dir="discussions"):
    """Save discussion metadata to the filesystem."""
    discussion_dir = Path(base_dir) / f"discussion_{discussion_id}"
    os.makedirs(discussion_dir, exist_ok=True)
    
    metadata_path = discussion_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

def load_discussion_metadata(discussion_id, base_dir="discussions"):
    """Load discussion metadata from the filesystem."""
    metadata_path = Path(base_dir) / f"discussion_{discussion_id}" / "metadata.json"
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"Discussion {discussion_id} not found")
    
    with open(metadata_path, "r") as f:
        return json.load(f)
```

## Testing Approach

We use pytest for testing with a focus on:

1. **Unit Testing**: Testing individual components in isolation
   - Mock external dependencies (filesystem, API)
   - Test each library class thoroughly
   - Parameterized tests for various scenarios

2. **Integration Testing**: Testing components working together
   - Test controllers with library classes
   - Mock only external systems (API)
   - Test file operations with temporary directories

3. **Functional Testing**: Testing complete workflows
   - Use Click's testing utilities for CLI testing
   - Test end-to-end scenarios with temporary files
   - Mock API responses but test real file operations

### Example Test Setup

```python
import pytest
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

@pytest.fixture
def mock_anthropic():
    """Fixture for mocking the Anthropic client."""
    with patch('anthropic.Anthropic') as mock_client:
        # Configure mock...
        yield mock_client

@pytest.fixture
def temp_discussion_dir():
    """Fixture for creating a temporary discussion directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up test discussions...
        yield Path(tmpdir)
