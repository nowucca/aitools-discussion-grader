#!/usr/bin/env python3
"""
Canvas SpeedGrader Mode for AI Discussion Grader

This script provides a JSON-in/JSON-out interface for Canvas SpeedGrader integration.
It reads submission data from stdin and outputs grading results to stdout.

Enhanced version that creates/updates discussions and saves submissions in the
standard CLI format for compatibility with reporting system.

Input: JSON submission data via stdin
Output: JSON grading result via stdout

Expected JSON contract:
Input:
{
  "discussion": {
    "prompt": "Discussion question text",
    "points_possible": 8,
    "min_words": 100,
    "title": "Discussion Title (optional)",
    "id": 1 (optional - will create/update if not provided)
  },
  "student": {
    "name": "Student Name"
  },
  "submission": {
    "message": "Student's submission text",
    "word_count": 150
  }
}

Output:
{
  "grade": "7",
  "comment": "Feedback text",
  "points": 7,
  "word_count": 150,
  "meets_word_count": true,
  "discussion_id": 1,
  "submission_id": 3
}
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from lib.discussion import DiscussionManager
from lib.submission_grader import SubmissionGrader


def create_or_update_discussion(discussion_data: Dict[str, Any], discussion_manager: DiscussionManager) -> int:
    """
    Create or update a discussion based on Canvas data.
    
    Args:
        discussion_data: Canvas discussion data
        discussion_manager: DiscussionManager instance
        
    Returns:
        Discussion ID
    """
    # Canvas may send 'message' instead of 'prompt' - handle both
    prompt = discussion_data.get('prompt', '') or discussion_data.get('message', '')
    points_possible = discussion_data.get('points_possible', 8)
    min_words = discussion_data.get('min_words', 100)
    title = discussion_data.get('title', '')
    discussion_id = discussion_data.get('id')
    
    # Generate a default title if not provided
    if not title:
        # Create a title from the first 50 characters of the prompt
        title = prompt[:50].strip()
        if len(prompt) > 50:
            title += "..."
        if not title:
            title = "Canvas Discussion"
    
    # If discussion_id is provided, try to update existing discussion
    if discussion_id:
        try:
            existing_discussion = discussion_manager.get_discussion(discussion_id)
            # Update the discussion with new data
            updated_discussion = discussion_manager.update_discussion(
                discussion_id,
                title=title,
                points=points_possible,
                min_words=min_words,
                question_content=prompt
            )
            return discussion_id
        except FileNotFoundError:
            # Discussion doesn't exist, create a new one with the specified ID
            pass
    
    # Check if a discussion with similar content already exists
    existing_discussions = discussion_manager.list_discussions()
    
    # Create a simple hash of the prompt to check for similar discussions
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
    
    for existing in existing_discussions:
        try:
            existing_full = discussion_manager.get_discussion(existing.id)
            existing_hash = hashlib.md5(existing_full.question_content.encode()).hexdigest()[:8]
            
            # If we find a discussion with the same prompt, update it
            if existing_hash == prompt_hash:
                discussion_manager.update_discussion(
                    existing.id,
                    title=title,
                    points=points_possible,
                    min_words=min_words,
                    question_content=prompt
                )
                return existing.id
        except Exception:
            continue
    
    # Create a new discussion
    if discussion_id:
        # Try to create with specific ID (may require manual directory creation)
        try:
            # Create the discussion directory manually if needed
            discussion_dir = discussion_manager.base_dir / f"discussion_{discussion_id}"
            submissions_dir = discussion_dir / "submissions"
            discussion_dir.mkdir(parents=True, exist_ok=True)
            submissions_dir.mkdir(parents=True, exist_ok=True)
            
            # Create discussion with metadata
            from lib.discussion import Discussion
            from datetime import datetime
            
            discussion = Discussion(
                id=discussion_id,
                title=title,
                points=points_possible,
                min_words=min_words,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                question_file="question.md"
            )
            
            # Write metadata and question
            with open(discussion_dir / "metadata.json", 'w') as f:
                json.dump(discussion.to_dict(), f, indent=2)
            
            with open(discussion_dir / "question.md", 'w') as f:
                f.write(prompt)
                
            return discussion_id
        except Exception:
            # Fall back to auto-generated ID
            pass
    
    # Create with auto-generated ID
    return discussion_manager.create_discussion(
        title=title,
        points=points_possible,
        min_words=min_words,
        question_content=prompt
    )


def format_canvas_response(graded_submission, student_name: str = "", 
                          discussion_id: int = 1, submission_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Convert our grading result to Canvas SpeedGrader format.
    
    Args:
        graded_submission: Our GradedSubmission object
        student_name: Student's name for personalized feedback
        discussion_id: ID of the discussion
        submission_id: ID of the saved submission
        
    Returns:
        Dictionary in Canvas SpeedGrader format
    """
    # Get first name for personalized greeting
    first_name = student_name.split()[0] if student_name else "Student"
    
    # Format the comment with greeting
    comment_parts = [f"Hi {first_name},"]
    comment_parts.append(graded_submission.feedback)
    
    if graded_submission.improvement_suggestions:
        comment_parts.append("\nSuggestions for improvement:")
        for suggestion in graded_submission.improvement_suggestions:
            comment_parts.append(f"• {suggestion}")
    
    if not graded_submission.meets_word_count:
        # Try to get min_words from the graded submission or use a default
        min_words = getattr(graded_submission, 'min_words', 100)
        comment_parts.append(f"\nNote: This submission has {graded_submission.word_count} words but should have at least {min_words} words.")
    
    comment = "\n".join(comment_parts)
    
    # Convert score to integer for cleaner display
    score = int(graded_submission.score)
    
    result = {
        "grade": str(score),
        "comment": comment,
        "points": score,
        "word_count": graded_submission.word_count,
        "meets_word_count": graded_submission.meets_word_count,
        "addressed_questions": graded_submission.addressed_questions,
        "improvement_suggestions": graded_submission.improvement_suggestions,
        "discussion_id": discussion_id
    }
    
    if submission_id is not None:
        result["submission_id"] = submission_id
    
    return result


def main():
    """Main grading function for Canvas SpeedGrader integration."""
    try:
        # Read submission data from stdin
        input_data = sys.stdin.read().strip()
        if not input_data:
            raise ValueError("No input data received from stdin")
        
        # Parse JSON input
        try:
            canvas_data = json.loads(input_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON input: {str(e)}")
        
        # Validate required fields
        required_fields = ['discussion', 'submission']
        for field in required_fields:
            if field not in canvas_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Initialize managers - use the parent directory structure
        base_dir = str(Path(__file__).parent.parent / "discussions")
        discussion_manager = DiscussionManager(base_dir)
        submission_grader = SubmissionGrader(base_dir)
        
        # Create or update the discussion
        discussion_data = canvas_data['discussion']
        discussion_id = create_or_update_discussion(discussion_data, discussion_manager)
        
        # Extract submission data
        submission_data = canvas_data.get('submission', {})
        message = submission_data.get('message', '')
        
        if not message.strip():
            raise ValueError("Submission message cannot be empty")
        
        # Grade the submission using the standard grading system
        graded_submission = submission_grader.grade_submission_text(
            discussion_id=discussion_id,
            submission_text=message,
            save=True  # Save in standard format
        )
        
        # Get student name for personalized feedback
        student_name = canvas_data.get('student', {}).get('name', '')
        
        # Format response for Canvas
        result = format_canvas_response(
            graded_submission, 
            student_name, 
            discussion_id,
            graded_submission.submission_id
        )
        
        # Output result as JSON to stdout
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        # Output error in JSON format so the main script can handle it
        error_result = {
            "error": str(e),
            "grade": "0",
            "comment": f"Grading error: {str(e)}. Please contact the instructor.",
            "points": 0,
            "word_count": 0,
            "meets_word_count": False
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
