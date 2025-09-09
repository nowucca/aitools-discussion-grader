# Canvas SpeedGrader Integration

This document describes how to use the Canvas SpeedGrader mode for JSON-based integration with Canvas LMS.

## Overview

The Canvas SpeedGrader mode (`canvas_speedgrader.py`) provides a JSON-in/JSON-out interface that integrates with Canvas LMS grading workflows. This mode processes student submission data via stdin and outputs grading results via stdout.

## Setup

### Prerequisites
- Python 3.11+ with uv package manager
- AI provider API key (Anthropic Claude or OpenAI)
- Canvas LMS integration script/wrapper

### Installation
```bash
# Install dependencies using uv
uv sync

# Activate virtual environment  
source .venv/bin/activate

# Set up AI provider
export ANTHROPIC_API_KEY="your-api-key"
# OR
export OPENAI_API_KEY="your-api-key"
```

## JSON Contract

### Input Format
The Canvas SpeedGrader expects JSON input via stdin with this structure:

```json
{
  "discussion": {
    "prompt": "Discussion question text",
    "points_possible": 8,
    "min_words": 100,
    "title": "Discussion Title (optional)"
  },
  "student": {
    "name": "Student Name"
  },
  "submission": {
    "message": "Student's submission text",
    "word_count": 150
  }
}
```

#### Input Fields
- **discussion.prompt**: The discussion question text (Canvas may also send this as 'message')
- **discussion.points_possible**: Maximum points for the assignment
- **discussion.min_words**: Minimum word count requirement
- **discussion.title**: Optional title (auto-generated from prompt if not provided)
- **student.name**: Student's name (used for personalized feedback)
- **submission.message**: The student's submission text
- **submission.word_count**: Word count (optional - auto-calculated if not provided)

**Note**: You do NOT need to provide internal discussion IDs. The system automatically creates or finds discussions based on content and returns the assigned IDs.

### Output Format
The grader outputs JSON results via stdout:

```json
{
  "grade": "7",
  "comment": "Hi Sarah,\nExcellent response! You demonstrate...",
  "points": 7,
  "word_count": 155,
  "meets_word_count": true,
  "addressed_questions": {
    "benefits": true,
    "challenges": true
  },
  "improvement_suggestions": [
    "Consider elaborating on...",
    "You might discuss..."
  ]
}
```

#### Output Fields
- **grade**: String representation of the score
- **comment**: Complete formatted feedback for the student
- **points**: Numeric score awarded
- **word_count**: Actual word count of submission
- **meets_word_count**: Boolean indicating if minimum word requirement is met
- **addressed_questions**: Object tracking which parts of multi-part questions were addressed
- **improvement_suggestions**: Array of specific improvement suggestions

## Usage

### Direct Command Line
```bash
# Using uv run for proper environment management
echo '{"discussion":{"prompt":"Discuss...","points_possible":8,"min_words":100},"student":{"name":"John"},"submission":{"message":"Student response..."}}' | uv run python discussion-grader/canvas_speedgrader.py
```

### From File
```bash
# Create input file
cat > input.json << EOF
{
  "discussion": {
    "prompt": "Discuss the concept of English as a Programming Language and how natural language programming could enhance software development usability and practicality. Consider both benefits and challenges.",
    "points_possible": 8,
    "min_words": 100
  },
  "student": {
    "name": "Sarah Johnson"
  },
  "submission": {
    "message": "The concept of English as a programming language is fascinating and represents a significant paradigm shift in software development. By allowing developers to write code using natural language constructs, we could dramatically reduce the learning curve for new programmers and make programming more accessible to non-technical users. However, there are significant challenges to consider. Natural language is inherently ambiguous, which could lead to unexpected behavior or bugs. Despite these challenges, I believe English-like programming languages could be valuable for educational purposes and rapid prototyping.",
    "word_count": 95
  }
}
EOF

# Process with Canvas SpeedGrader
uv run python discussion-grader/canvas_speedgrader.py < input.json
```

### Wrapper Script Integration
For Canvas LMS integration, create a wrapper script:

```bash
#!/bin/bash
# canvas_grade_wrapper.sh

# Set up environment
export ANTHROPIC_API_KEY="your-api-key-here"
cd /path/to/Discussion-General

# Process the grading request
uv run python discussion-grader/canvas_speedgrader.py
```

## Question Tracking

The Canvas SpeedGrader automatically detects multi-part questions and tracks whether students address all parts:

### Automatic Detection
The system detects multi-part questions by looking for keywords:
- **Benefits/Advantages**: "benefits", "advantages"
- **Challenges/Problems**: "challenges", "disadvantages", "problems", "limitations"

When both types are found in the discussion prompt, the system enables question tracking.

### Output Tracking
For multi-part questions, the `addressed_questions` field shows:
```json
{
  "addressed_questions": {
    "benefits": true,
    "challenges": false
  }
}
```

This helps instructors quickly identify submissions that may have missed part of the question.

## Error Handling

The Canvas SpeedGrader provides comprehensive error handling:

### Error Response Format
```json
{
  "error": "Error description",
  "grade": "0",
  "comment": "Grading error occurred. Please contact the instructor.",
  "points": 0,
  "word_count": 0,
  "meets_word_count": false
}
```

### Common Errors
- **Invalid JSON**: Malformed input JSON
- **Missing Fields**: Required fields not provided
- **AI API Errors**: Connection or authentication issues
- **Configuration Errors**: Missing API keys or invalid config

### Troubleshooting
```bash
# Test API connectivity
uv run python -c "from discussion_grader.lib.ai import AIGrader; print('API connection test passed')"

# Validate JSON input
cat input.json | python -m json.tool

# Check environment variables
echo "ANTHROPIC_API_KEY set: $([ -n "$ANTHROPIC_API_KEY" ] && echo "yes" || echo "no")"
echo "OPENAI_API_KEY set: $([ -n "$OPENAI_API_KEY" ] && echo "yes" || echo "no")"
```

## Configuration Options

### AI Provider Selection
```bash
# Use Anthropic Claude (default)
export ANTHROPIC_API_KEY="your-anthropic-key"

# Use OpenAI GPT-4
export OPENAI_API_KEY="your-openai-key"
export AI_PROVIDER="openai"

# Use custom OpenAI-compatible service
export OPENAI_API_KEY="your-key"  
export OPENAI_BASE_URL="http://your-service.com/v1"
export AI_PROVIDER="openai"
```

### Config File Override
Place configuration in `discussion-grader/config/config.json`:

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
  }
}
```

## Performance Considerations

### Response Times
- **Anthropic Claude**: ~2-5 seconds per submission
- **OpenAI GPT-4**: ~1-3 seconds per submission
- **Custom endpoints**: Varies by implementation

### Rate Limits
- **Anthropic**: Respects Claude API rate limits
- **OpenAI**: Respects OpenAI API rate limits
- **Custom**: Depends on your service configuration

### Batch Processing
For large numbers of submissions, consider:
- Processing in smaller batches
- Implementing retry logic for API failures
- Monitoring API usage and costs

## Integration Examples

### Canvas External Tool
Canvas can call the SpeedGrader via external tool integration:

```javascript
// Example Canvas external tool integration
const gradingData = {
  discussion: {
    prompt: assignment.description,
    points_possible: assignment.points_possible,
    min_words: assignment.min_words || 100
  },
  student: {
    name: student.name
  },
  submission: {
    message: submission.body,
    word_count: submission.word_count
  }
};

const response = await fetch('/grade-endpoint', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(gradingData)
});

const gradingResult = await response.json();
```

### Webhook Integration
Canvas webhooks can trigger grading:

```python
# Example webhook handler
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/canvas-webhook', methods=['POST'])
def handle_canvas_submission():
    canvas_data = request.json
    
    # Transform Canvas data to SpeedGrader format
    grading_input = transform_canvas_data(canvas_data)
    
    # Call SpeedGrader
    result = subprocess.run(
        ['uv', 'run', 'python', 'discussion-grader/canvas_speedgrader.py'],
        input=json.dumps(grading_input),
        text=True,
        capture_output=True,
        cwd='/path/to/Discussion-General'
    )
    
    if result.returncode == 0:
        return jsonify(json.loads(result.stdout))
    else:
        return jsonify(json.loads(result.stdout)), 400
```

## Security Considerations

### API Key Security
- Never embed API keys in client-side code
- Use environment variables for key storage
- Rotate API keys regularly
- Monitor API usage for anomalies

### Input Validation
The Canvas SpeedGrader validates:
- JSON structure and required fields
- Input length limits
- Content sanitization for AI processing

### Output Sanitization
- Feedback is sanitized for safe display
- No executable content in responses
- Appropriate encoding for text content

## Monitoring and Logging

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Monitor Performance
Track key metrics:
- Response times per submission
- API error rates
- Processing throughput
- Cost per grading operation

This Canvas SpeedGrader integration provides a robust, scalable solution for AI-powered grading within Canvas LMS workflows.
