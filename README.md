# Discussion Grader

An AI-powered CLI tool for creating discussion questions and grading student submissions interactively. Built for teaching assistants and instructors who want to streamline their discussion grading workflow using clipboard-based batch processing.

## Quick Start

### Prerequisites

- Python 3.11+ 
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

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

4. **Set up your Anthropic API key:**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```
   
   Or add it to your shell profile (`.bashrc`, `.zshrc`, etc.):
   ```bash
   echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
   ```

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
# Test your API key
python -c "import os; print('API Key set:', bool(os.environ.get('ANTHROPIC_API_KEY')))"
```

### Permission Errors
```bash
# Make sure you're in the virtual environment
which python  # Should show .venv path
```

## Development

### Running Tests
```bash
uv run pytest discussion-grader/tests/
```

### Adding Dependencies
```bash
uv add package-name
```

The system uses Claude AI for grading and provides detailed feedback to help students improve their discussion contributions while saving instructors significant time.
