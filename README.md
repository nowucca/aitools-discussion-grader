# Discussion Grader

An AI-powered CLI tool for creating discussion questions and grading student submissions interactively. Built for teaching assistants and instructors who want to streamline their discussion grading workflow using clipboard-based batch processing.

## Quick Start

### Prerequisites

- Python 3.11+ 
- [uv](https://docs.astral.sh/uv/) package manager
- API key for either:
  - **Anthropic Claude** (recommended)
  - **OpenAI GPT** or OpenAI-compatible service

### Setup

1. **Clone and enter the repository:**
   ```bash
   git clone <repository-url>
   cd Discussion-General
   ```

2. **Install dependencies with uv:**
   ```bash
   uv sync
   ```

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

4. **Set up your AI provider:**

   **Option A: Anthropic Claude (Default)**
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
   ```
   
   **Option B: OpenAI GPT**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   export AI_PROVIDER="openai"  # Optional: auto-detected if OPENAI_API_KEY is set
   ```
   
   **Option C: OpenAI-Compatible Service (e.g., Local LLM)**
   ```bash
   export OPENAI_API_KEY="your-api-key"
   export OPENAI_BASE_URL="http://localhost:8080/v1"  # Your custom endpoint
   export AI_PROVIDER="openai"
   ```
   
   Or add to your shell profile (`.bashrc`, `.zshrc`, etc.):
   ```bash
   echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
   # OR
   echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.zshrc
   ```

## AI Provider Configuration

The system supports multiple AI providers with automatic detection:

### Environment Variables
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `OPENAI_API_KEY` - Your OpenAI API key  
- `AI_PROVIDER` - Force specific provider: "anthropic" or "openai" (optional)
- `OPENAI_BASE_URL` - Custom OpenAI-compatible endpoint (optional)

### Provider Selection Priority
1. **Explicit**: If `AI_PROVIDER` is set, uses that provider
2. **Auto-detect**: If `ANTHROPIC_API_KEY` exists, uses Anthropic
3. **Auto-detect**: If `OPENAI_API_KEY` exists, uses OpenAI
4. **Fallback**: Defaults to Anthropic (requires API key)

### Configuration File
You can also configure providers in `discussion-grader/config/config.json`:

```json
{
  "ai": {
    "provider": "openai",
    "anthropic": {
      "model": "claude-3-sonnet-20240229",
      "max_tokens": 1000,
      "temperature": 0.3
    },
    "openai": {
      "model": "gpt-4",
      "max_tokens": 1000,
      "temperature": 0.3,
      "base_url": "https://api.openai.com/v1"
    }
  }
}
```

**Note**: Environment variables take precedence over configuration file settings.

## Creating Your First Discussion

### Step 1: Create a Discussion

```bash
cd discussion-grader
python grader.py discussion create \
  --title "English as a Programming Language" \
  --points 8 \
  --min-words 100 \
  --question "Discuss how programming languages could benefit from incorporating more natural language elements. What are the trade-offs between readability and precision?"
```

This creates:
- A new discussion with ID 1
- Point value: 8 points
- Minimum word requirement: 100 words
- The discussion question stored in `discussions/discussion_1/question.md`

### Step 2: Verify Your Discussion

```bash
python grader.py discussion show 1
```

You should see your discussion details including the question content.

## Clipboard-Based Grading Workflow

The most efficient way to grade submissions is using **clipboard batch grading mode**:

### Step 3: Start Interactive Grading

```bash
python grader.py submission batch 1
```

This starts a clipboard-based session where:

1. **Copy** a student's submission to your clipboard (Ctrl+C/Cmd+C)
2. **Press Enter** in the terminal
3. **AI grades it automatically** and copies the result to your clipboard
4. **Paste the result** (Ctrl+V/Cmd+V) into your grading system
5. **Repeat** for the next student, or type 'quit' to finish

### Example Interactive Session

```
=== Clipboard-Based Grading Session Started ===
Grading submissions for discussion 1

INSTRUCTIONS:
1. Copy a student submission to your clipboard
2. Press Enter to grade the submission
3. Repeat for each student
4. Press Enter without copying anything (or type 'quit') to end the session

Discussion: English as a Programming Language
Points: 8
Minimum words: 100

=== Student #1 ===
Copy the submission to your clipboard, then press Enter (or type 'quit' to exit)...

Grading submission #1 (145 words)...

GRADING RESULTS:
Score: 7/8 (87.5%)
Word Count: 145 words (✓ meets minimum)

Feedback:
Your discussion demonstrates a solid understanding of natural language elements in programming. You provided good examples with Python's readability philosophy and SQL's English-like syntax. The trade-off analysis between readability and precision shows critical thinking.

Areas for improvement:
- Consider discussing potential performance implications
- Could benefit from more specific examples of how NLP could be integrated

✅ Grading result copied to clipboard - you can now paste it into your grading system!

Student #1 complete. Ready for next submission...

=== Student #2 ===
Copy the submission to your clipboard, then press Enter (or type 'quit' to exit)...
[Process continues...]

=== Grading Session Complete ===
Successfully graded 3/3 submissions
Time saved: Approximately 45 minutes
```

## Single Submission Grading

For grading individual submissions, you can also grade directly from your clipboard:

```bash
python grader.py submission grade-clipboard 1
```

This will:
1. Read the submission from your clipboard
2. Grade it using the AI
3. Display the results in the terminal
4. Copy the grading result back to your clipboard

## Viewing Results

### List All Submissions
```bash
python grader.py submission list 1
```

### View Specific Submission
```bash
python grader.py submission show 1 2  # Discussion 1, Submission 2
```

### Export Results
```bash
python grader.py submission list 1 --format csv > grades.csv
```

## Advanced Features

### Generate Discussion Reports

Create AI-synthesized reports from all submissions:

```bash
python grader.py report generate 1 --min-score 6.0
```

This creates a summary report highlighting:
- Common themes across submissions
- Unique insights from students  
- Overall class understanding
- Key discussion points

### Manage Multiple Discussions

```bash
# List all discussions
python grader.py discussion list

# Update discussion settings
python grader.py discussion update 1 --points 10

# Create another discussion
python grader.py discussion create --title "AI Ethics in Education" --points 12
```

## File Structure

After creating discussions and grading submissions:

```
Discussion-General/
├── discussions/
│   └── discussion_1/
│       ├── metadata.json          # Discussion settings
│       ├── question.md            # The discussion question
│       └── submissions/
│           ├── submission_1.json  # Graded submission
│           ├── submission_2.json
│           └── ...
├── discussion-grader/
│   ├── grader.py                 # Main CLI tool
│   ├── lib/                      # Core grading logic
│   └── controllers/              # CLI command handlers
└── pyproject.toml               # uv configuration
```

## Tips for Efficient Grading

1. **Use clipboard batch mode** for fastest workflow
2. **Grade in dedicated sessions** for consistent pacing
3. **Review AI feedback** before pasting - you can always modify it
4. **Export to CSV** for grade book integration
5. **Generate reports** to identify class-wide patterns

## Troubleshooting

### API Key Issues
```bash
# Test your Anthropic API key
python -c "import os; print('Anthropic API Key set:', bool(os.environ.get('ANTHROPIC_API_KEY')))"

# Test your OpenAI API key
python -c "import os; print('OpenAI API Key set:', bool(os.environ.get('OPENAI_API_KEY')))"

# Check which provider will be used
python -c "
import os
if os.environ.get('AI_PROVIDER'):
    print(f'Forced provider: {os.environ.get(\"AI_PROVIDER\")}')
elif os.environ.get('ANTHROPIC_API_KEY'):
    print('Will use: Anthropic (auto-detected)')
elif os.environ.get('OPENAI_API_KEY'):
    print('Will use: OpenAI (auto-detected)')
else:
    print('No API keys found - will default to Anthropic')
"
```

### Permission Errors
```bash
# Make sure you're in the virtual environment
which python  # Should show .venv path
```

### Provider-Specific Issues
- **Anthropic**: Ensure your API key has sufficient credits and proper permissions
- **OpenAI**: Check your API key and organization settings
- **Custom OpenAI-compatible**: Verify your `OPENAI_BASE_URL` is accessible and supports the OpenAI API format

## Development

### Running Tests
```bash
# Run tests using uv for proper environment management
uv run pytest discussion-grader/tests/

# Run specific test files
uv run pytest discussion-grader/tests/unit/lib/test_ai.py

# Run tests with coverage
uv run pytest discussion-grader/tests/ --cov=discussion-grader/lib/
```

### Adding Dependencies
```bash
uv add package-name
```

The system uses AI for grading (supporting both Anthropic Claude and OpenAI GPT/compatible providers) and provides detailed feedback to help students improve their discussion contributions while saving instructors significant time.
