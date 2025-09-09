# Technical Context: Multi-Discussion Grading System

## Technologies Used

### Core Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Primary programming language | 3.7+ |
| Click | Command-line interface framework | 8.0+ |
| Anthropic Claude API | AI for grading and synthesis | Claude 3 Opus |
| pytest | Testing framework | 7.0+ |
| pyperclip | Clipboard integration | 1.8+ |

### Python Libraries

| Library | Purpose |
|---------|---------|
| **anthropic** | Client for Claude API |
| **json** | JSON parsing and serialization |
| **os / pathlib** | Filesystem operations |
| **dataclasses** | Structured data objects |
| **typing** | Type hints for better code quality |
| **click** | CLI framework |
| **pytest** | Testing |
| **unittest.mock** | Mocking for tests |
| **pyperclip** | System clipboard access |

## Development Setup

### Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix/MacOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Required Environment Variables

- `ANTHROPIC_API_KEY`: Required for AI grading functionality

### Configuration Files

- `config/config.json`: Global configuration settings
  ```json
  {
    "synthesis": {
      "prompt": "You are synthesizing student responses...",
      "max_submissions": 50
    },
    "grading": {
      "default_points": 12,
      "default_min_words": 300
    }
  }
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
