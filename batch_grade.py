#!/usr/bin/env python3
"""
Interactive Grading Script for Discussion Submissions

This script provides an interactive REPL (Read-Eval-Print Loop) for grading
student submissions one at a time. It allows the user to paste a submission,
immediately grades it, and provides detailed feedback before prompting for
the next submission.

Usage:
    python batch_grade.py [--api-key API_KEY] [--output-dir OUTPUT_DIR]
"""

import os
import sys
import argparse
import anthropic
import json
from pathlib import Path
from grade_discussion import grade_with_claude, read_file, count_words

def get_pasted_submission(student_num):
    """Get a single submission pasted by the user."""
    import tempfile
    import subprocess
    
    print(f"\n=== Student Submission #{student_num} ===")
    print("Instructions:")
    print("1. We'll open a temporary file in your default text editor.")
    print("2. Paste your submission into the editor and save the file.")
    print("3. Close the editor when done to continue grading.")
    print("4. To exit the grading session, leave the file empty and save it.")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
        temp_path = temp.name
        # Write instructions to the file
        temp.write(b"""# Student Submission
# Paste your submission below this line
# Save the file and close the editor when done
# Leave the file empty to exit the grading session

""")
    
    # Open the file in the default text editor
    print(f"\nOpening temporary file for submission #{student_num}...")
    if sys.platform == 'win32':
        os.startfile(temp_path)
    elif sys.platform == 'darwin':  # macOS
        subprocess.call(['open', temp_path])
    else:  # Linux and other Unix-like
        subprocess.call(['xdg-open', temp_path])
    
    # Wait for the user to edit and close the file
    input("Press Enter when you've saved and closed the editor...")
    
    # Read the content from the temporary file
    try:
        with open(temp_path, 'rb') as file:
            content = file.read().decode('utf-8', errors='replace')
        
        # Remove the instructions
        content = content.split("# Leave the file empty to exit the grading session\n\n", 1)[-1]
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        # Check if the user wants to exit (empty file)
        if not content.strip():
            print("Empty submission. Exiting grading session.")
            return None
        
        return content
    except Exception as e:
        print(f"Error reading submission: {e}")
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except:
            pass
        return get_pasted_submission(student_num)

def format_improvement_suggestions(result):
    """Format improvement suggestions based on the grading results."""
    suggestions = []
    addressed = result.get("addressed_questions", {})
    
    # Check word count
    if result.get("word_count", 0) < 300:
        suggestions.append("- Expand your response to meet the minimum word count of 300 words.")
    
    # Check if all questions were addressed
    if not addressed.get("other_systems", True):
        suggestions.append("- Include examples of other similar automated software engineering systems.")
    
    if not addressed.get("threat_or_boost", True):
        suggestions.append("- Discuss whether these systems pose a threat or boost to the field of software engineering and explain why.")
    
    if not addressed.get("additional_capabilities", True):
        suggestions.append("- Suggest additional capabilities that could enhance these automated systems.")
    
    if not addressed.get("current_shortfalls", True):
        suggestions.append("- Analyze the current shortfalls or limitations of this technology.")
    
    # Add general improvement suggestions based on score
    if result.get("grade", 0) < 9:
        suggestions.append("- Provide more specific examples to support your claims.")
        suggestions.append("- Deepen your analysis with more thoughtful reasoning.")
    
    return suggestions

def format_grade_summary(result, student_id):
    """Format a concise grade summary with improvement suggestions."""
    addressed = result.get("addressed_questions", {})
    
    # Generate improvement suggestions
    suggestions = format_improvement_suggestions(result)
    
    summary = f"""
GRADE SUMMARY FOR: {student_id}
==================================================

GRADE: {result['grade']}/{12}

WORD COUNT: {result.get('word_count', 'N/A')} words (minimum required: 300)

QUESTIONS ADDRESSED:
- Other similar systems: {'✓' if addressed.get('other_systems', False) else '✗'}
- Threat or boost to software engineering: {'✓' if addressed.get('threat_or_boost', False) else '✗'}
- Ideas for additional capabilities: {'✓' if addressed.get('additional_capabilities', False) else '✗'}
- Current shortfalls with the technology: {'✓' if addressed.get('current_shortfalls', False) else '✗'}

FEEDBACK FOR STUDENT:
{result['feedback']}

GRADING REASONING:
{result['reasoning']}

IMPROVEMENT SUGGESTIONS:
{"No specific improvements needed." if not suggestions else "\n".join(suggestions)}
==================================================
"""
    return summary

def grade_submission(content, question, api_key, student_id, output_dir=None):
    """Grade a single submission using the grade_with_claude function."""
    print(f"\nGrading submission #{student_id}...")
    
    try:
        # Grade with Claude
        result = grade_with_claude(api_key, question, content)
        
        # Ensure we have a valid result
        if result is None:
            print(f"Error: Received None result from grade_with_claude for submission #{student_id}")
            return False
        
        # Add word count if not already included
        if 'word_count' not in result:
            result['word_count'] = count_words(content)
        
        # Ensure addressed_questions exists
        if 'addressed_questions' not in result:
            result['addressed_questions'] = {
                "other_systems": False,
                "threat_or_boost": False,
                "additional_capabilities": False,
                "current_shortfalls": False
            }
        
        # Format the summary
        summary = format_grade_summary(result, f"Student #{student_id}")
        
        # Output the full report if output_dir is specified
        if output_dir:
            # Create a detailed report
            full_report = f"""
DETAILED GRADING REPORT FOR: Student #{student_id}
==================================================

GRADE: {result['grade']}/12

WORD COUNT: {result.get('word_count', 'N/A')} words (minimum required: 300)

QUESTIONS ADDRESSED:
- Other similar systems: {'✓' if result.get('addressed_questions', {}).get('other_systems', False) else '✗'}
- Threat or boost to software engineering: {'✓' if result.get('addressed_questions', {}).get('threat_or_boost', False) else '✗'}
- Ideas for additional capabilities: {'✓' if result.get('addressed_questions', {}).get('additional_capabilities', False) else '✗'}
- Current shortfalls with the technology: {'✓' if result.get('addressed_questions', {}).get('current_shortfalls', False) else '✗'}

FEEDBACK FOR STUDENT:
{result.get('feedback', 'Error: No feedback available')}

GRADING REASONING:
{result.get('reasoning', 'Error: No reasoning available')}

IMPROVEMENT SUGGESTIONS:
{"\n".join(format_improvement_suggestions(result)) or "No specific improvements needed."}

ORIGINAL SUBMISSION:
{content}
==================================================
"""
            output_file = Path(output_dir) / f"student_{student_id}_grade.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_report)
            print(f"Detailed grade report saved to {output_file}")
        
        # Print the summary to the console
        print(summary)
        
        return True
    except Exception as e:
        print(f"Error grading submission #{student_id}: {str(e)}")
        return False

def interactive_grading_loop(question, api_key, output_dir=None):
    """Run an interactive grading loop for submissions."""
    student_count = 0
    successful = 0
    
    print("\n=== Interactive Grading Session Started ===")
    print("You can grade multiple submissions one at a time.")
    print("After each submission is graded, you'll be prompted for the next one.")
    print("Type 'exit' or 'quit' at the submission prompt to end the session.")
    
    while True:
        student_count += 1
        submission = get_pasted_submission(student_count)
        
        if submission is None:
            break
        
        if grade_submission(submission, question, api_key, student_count, output_dir):
            successful += 1
        
        print("\nReady for next submission...")
    
    print(f"\nGrading session complete. Successfully graded {successful}/{student_count-1} submissions.")
    
    if output_dir:
        print(f"Detailed grade reports saved to: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Interactive grading for discussion submissions.')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY environment variable)')
    parser.add_argument('--output-dir', help='Directory to save detailed grade reports (optional)')
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: Anthropic API key is required. Provide it with --api-key or set ANTHROPIC_API_KEY environment variable.")
        sys.exit(1)
    
    # Create output directory if specified and doesn't exist
    if args.output_dir and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"Created output directory: {args.output_dir}")
    
    # Read question
    question_file = "question.md"
    try:
        question = read_file(question_file)
    except Exception as e:
        print(f"Error reading question file: {str(e)}")
        sys.exit(1)
    
    # Start interactive grading loop
    interactive_grading_loop(question, api_key, args.output_dir)

if __name__ == "__main__":
    main()
