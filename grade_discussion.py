#!/usr/bin/env python3
"""
Discussion Grader for Software Engineers Question

This program reads a student submission, sends it to Claude for grading,
and outputs a grade and feedback based on the question requirements.

Usage:
    python grade_discussion.py <submission_file>
"""

import sys
import os
import json
import argparse
import anthropic
from typing import Dict, Any, Tuple

# Constants
TOTAL_POINTS = 12
QUESTION_FILE = "question.md"
MIN_WORD_COUNT = 300

def read_file(file_path: str) -> str:
    """Read the content of a file."""
    try:
        # Open in binary mode first to handle potential encoding issues
        with open(file_path, 'rb') as file:
            content = file.read()
            
        # Try to decode with utf-8 first
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            # If utf-8 fails, try with latin-1 which can decode any byte sequence
            return content.decode('latin-1')
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)

def count_words(text: str) -> int:
    """Count the number of words in a text."""
    return len(text.split())

def grade_with_claude(api_key: str, question: str, submission: str) -> Dict[str, Any]:
    """
    Use Claude to grade the submission.
    
    Returns a dictionary with:
    - grade: int (0-12)
    - feedback: str
    - reasoning: str
    """
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""
    You are an instructor grading a student's discussion response. The question is:

    {question}

    The student's submission is:

    {submission}

    Please grade this submission out of {TOTAL_POINTS} points based on the following criteria:
    
    1. Word count: The submission should be at least {MIN_WORD_COUNT} words. Deduct points if it's significantly shorter.
    2. Addressing all questions: The student should address all the questions in the prompt.
    3. Quality of analysis: The student should provide thoughtful analysis and reasoning.
    4. Examples and evidence: The student should provide examples or evidence to support their claims.
    
    Provide your grade (0-{TOTAL_POINTS}), concise but constructive feedback for the student, and your reasoning for the grade.
    
    You MUST Write both your feedback and reasoning directly to the student in a clear, professional instructor tone. Be specific but not overly verbose.
    Avoid using phrases like "the student" and prefer to use "you" instead.
    The feedback should be constructive and actionable, helping the student understand how to improve.
    The reasoning should explain how you arrived at the grade, including any specific points that were strong or weak.

    
    Format your response as a JSON object with the following fields:
    {{
        "grade": int,
        "feedback": "string with feedback for the student (as an instructor)",
        "reasoning": "string explaining your grading reasoning (as an instructor)",
        "addressed_questions": {{
            "other_systems": bool,
            "threat_or_boost": bool,
            "additional_capabilities": bool,
            "current_shortfalls": bool
        }},
        "word_count": int
    }}
    """
    
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,  # Doubled from 2000 to 4000 to handle larger submissions
            temperature=0,
            system="You are an expert instructor grading computer science discussions. Write feedback and grading reasoning directly to the student in a clear, professional tone. Be concise but constructive. Grade fairly and provide specific feedback without being overly verbose.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the JSON from the response
        response_text = response.content[0].text
        # Find JSON in the response (it might be wrapped in markdown code blocks)
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                # First try to load the JSON as is
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error: {e}")
                
                # Try multiple cleaning approaches
                
                # 1. Try to clean control characters
                import re
                cleaned_json = re.sub(r'[\x00-\x1F]', lambda m: f"\\u{ord(m.group(0)):04x}", json_str)
                
                try:
                    return json.loads(cleaned_json)
                except json.JSONDecodeError:
                    pass  # Try next approach
                
                # 2. Try to manually extract values using regex
                try:
                    # Extract grade
                    grade_match = re.search(r'"grade"\s*:\s*(\d+)', json_str)
                    grade = int(grade_match.group(1)) if grade_match else 0
                    
                    # Extract feedback
                    feedback_match = re.search(r'"feedback"\s*:\s*"([^"]*(?:"[^"]*"[^"]*)*)"', json_str)
                    feedback = feedback_match.group(1) if feedback_match else "Error extracting feedback"
                    
                    # Extract reasoning
                    reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]*(?:"[^"]*"[^"]*)*)"', json_str)
                    reasoning = reasoning_match.group(1) if reasoning_match else "Error extracting reasoning"
                    
                    # Extract addressed questions
                    other_systems = "true" in json_str.lower().split('"other_systems"')[1].split(',')[0] if '"other_systems"' in json_str else False
                    threat_or_boost = "true" in json_str.lower().split('"threat_or_boost"')[1].split(',')[0] if '"threat_or_boost"' in json_str else False
                    additional_capabilities = "true" in json_str.lower().split('"additional_capabilities"')[1].split(',')[0] if '"additional_capabilities"' in json_str else False
                    current_shortfalls = "true" in json_str.lower().split('"current_shortfalls"')[1].split(',')[0] if '"current_shortfalls"' in json_str else False
                    
                    # Create a valid dictionary
                    return {
                        "grade": grade,
                        "feedback": feedback,
                        "reasoning": reasoning,
                        "addressed_questions": {
                            "other_systems": other_systems,
                            "threat_or_boost": threat_or_boost,
                            "additional_capabilities": additional_capabilities,
                            "current_shortfalls": current_shortfalls
                        },
                        "word_count": count_words(submission)
                    }
                except Exception as e3:
                    print(f"Error extracting values with regex: {e3}")
                    
                # 3. If all else fails, return default dictionary
                print(f"Error: Failed to parse JSON even after cleaning: {e}")
                print(f"JSON content (first 100 chars): {json_str[:100]}...")
                return {
                    "grade": 0,
                    "feedback": "Error processing grade: Invalid JSON response from Claude",
                    "reasoning": "Error processing grade: Invalid JSON response from Claude",
                    "addressed_questions": {
                        "other_systems": False,
                        "threat_or_boost": False,
                        "additional_capabilities": False,
                        "current_shortfalls": False
                    },
                    "word_count": count_words(submission)
                }
        else:
            print("Error: Could not find JSON in Claude's response")
            print(f"Response: {response_text}")
            return {
                "grade": 0,
                "feedback": "Error processing grade",
                "reasoning": "Error processing grade",
                "addressed_questions": {
                    "other_systems": False,
                    "threat_or_boost": False,
                    "additional_capabilities": False,
                    "current_shortfalls": False
                },
                "word_count": count_words(submission)
            }
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return {
            "grade": 0,
            "feedback": f"Error: {str(e)}",
            "reasoning": f"Error: {str(e)}",
            "addressed_questions": {
                "other_systems": False,
                "threat_or_boost": False,
                "additional_capabilities": False,
                "current_shortfalls": False
            },
            "word_count": count_words(submission)
        }

def format_grade_report(result: Dict[str, Any], submission_file: str) -> str:
    """Format the grading results into a readable report."""
    addressed = result.get("addressed_questions", {})
    
    report = f"""
GRADING REPORT FOR: {submission_file}
==================================================

GRADE: {result['grade']}/{TOTAL_POINTS}

WORD COUNT: {result.get('word_count', 'N/A')} words (minimum required: {MIN_WORD_COUNT})

QUESTIONS ADDRESSED:
- Other similar systems: {'✓' if addressed.get('other_systems', False) else '✗'}
- Threat or boost to software engineering: {'✓' if addressed.get('threat_or_boost', False) else '✗'}
- Ideas for additional capabilities: {'✓' if addressed.get('additional_capabilities', False) else '✗'}
- Current shortfalls with the technology: {'✓' if addressed.get('current_shortfalls', False) else '✗'}

FEEDBACK FOR STUDENT:
{result['feedback']}

GRADING REASONING:
{result['reasoning']}
==================================================
"""
    return report

def main():
    parser = argparse.ArgumentParser(description='Grade a student discussion submission using Claude.')
    parser.add_argument('submission_file', help='Path to the student submission file')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY environment variable)')
    parser.add_argument('--output', help='Output file for the grade report (default: stdout)')
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: Anthropic API key is required. Provide it with --api-key or set ANTHROPIC_API_KEY environment variable.")
        sys.exit(1)
    
    # Read question and submission
    question = read_file(QUESTION_FILE)
    submission = read_file(args.submission_file)
    
    # Count words in submission
    word_count = count_words(submission)
    print(f"Submission word count: {word_count} words")
    
    # Grade with Claude
    print("Grading submission with Claude...")
    result = grade_with_claude(api_key, question, submission)
    
    # Add word count if not already included
    if 'word_count' not in result:
        result['word_count'] = word_count
    
    # Format the report
    report = format_grade_report(result, args.submission_file)
    
    # Output the report
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Grade report written to {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()
