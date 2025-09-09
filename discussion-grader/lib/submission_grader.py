"""
Submission Grader - Core grading functionality for student submissions.

This module provides the SubmissionGrader class that handles:
- Grading individual submissions using AI
- Storing graded submissions with metadata
- Managing submission files within discussions
- Retrieving and listing submissions
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from .ai import AIGrader
from .discussion import DiscussionManager
from .submission import Submission, GradedSubmission
from .grading import GradingCriteria


class SubmissionGrader:
    """Handles grading and storage of student submissions."""
    
    def __init__(self, base_dir: str = "discussions", api_key: Optional[str] = None):
        """
        Initialize the SubmissionGrader.
        
        Args:
            base_dir: Base directory for discussion storage
            api_key: Anthropic API key (optional, can use environment variable)
        """
        self.base_dir = Path(base_dir)
        self.discussion_manager = DiscussionManager(base_dir)
        self.ai_grader = AIGrader(api_key)
    
    def grade_submission(self, discussion_id: int, file_path: str, 
                        save: bool = True) -> GradedSubmission:
        """
        Grade a single submission file.
        
        Args:
            discussion_id: ID of the discussion
            file_path: Path to the submission file
            save: Whether to save the graded submission
            
        Returns:
            GradedSubmission object with grading results
            
        Raises:
            FileNotFoundError: If discussion or submission file doesn't exist
            ValueError: If discussion_id is invalid
        """
        # Get the discussion to validate it exists and get question
        discussion = self.discussion_manager.get_discussion(discussion_id)
        if not discussion:
            raise ValueError(f"Discussion {discussion_id} not found")
        
        # Create submission object from file
        submission = Submission.from_file(
            discussion_id=discussion_id,
            file_path=file_path,
            question_text=discussion.question_content
        )
        
        # Create grading criteria from discussion
        criteria = GradingCriteria.from_discussion(discussion)
        
        # Grade the submission using AI
        graded_submission = self.ai_grader.grade_submission(
            submission=submission,
            criteria=criteria
        )
        
        # Save the graded submission if requested
        if save:
            submission_id = self._save_submission(discussion_id, submission, graded_submission)
            graded_submission.submission_id = submission_id
        
        return graded_submission
    
    def grade_submission_text(self, discussion_id: int, submission_text: str,
                             save: bool = True) -> GradedSubmission:
        """
        Grade submission text directly (useful for batch grading).
        
        Args:
            discussion_id: ID of the discussion
            submission_text: The submission text to grade
            save: Whether to save the graded submission
            
        Returns:
            GradedSubmission object with grading results
        """
        # Get the discussion to validate it exists and get question
        discussion = self.discussion_manager.get_discussion(discussion_id)
        if not discussion:
            raise ValueError(f"Discussion {discussion_id} not found")
        
        # Create submission object from text
        submission = Submission(
            discussion_id=discussion_id,
            submission_text=submission_text,
            question_text=discussion.question_content
        )
        
        # Create grading criteria from discussion
        criteria = GradingCriteria.from_discussion(discussion)
        
        # Grade the submission using AI
        graded_submission = self.ai_grader.grade_submission(
            submission=submission,
            criteria=criteria
        )
        
        # Save the graded submission if requested
        if save:
            submission_id = self._save_submission(discussion_id, submission, graded_submission)
            graded_submission.submission_id = submission_id
        
        return graded_submission
    
    def get_submission(self, discussion_id: int, submission_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific graded submission.
        
        Args:
            discussion_id: ID of the discussion
            submission_id: ID of the submission
            
        Returns:
            Dictionary containing submission and grading data, or None if not found
        """
        submission_dir = self.base_dir / f"discussion_{discussion_id}" / "submissions"
        submission_file = submission_dir / f"submission_{submission_id}.json"
        
        if not submission_file.exists():
            return None
        
        try:
            with open(submission_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading submission {submission_id}: {e}")
            return None
    
    def list_submissions(self, discussion_id: int) -> List[Dict[str, Any]]:
        """
        List all submissions for a discussion.
        
        Args:
            discussion_id: ID of the discussion
            
        Returns:
            List of submission dictionaries with metadata
        """
        submission_dir = self.base_dir / f"discussion_{discussion_id}" / "submissions"
        
        if not submission_dir.exists():
            return []
        
        submissions = []
        for submission_file in submission_dir.glob("submission_*.json"):
            try:
                with open(submission_file, 'r', encoding='utf-8') as f:
                    submission_data = json.load(f)
                    # Add file info for listing
                    submission_data['file_name'] = submission_file.name
                    submissions.append(submission_data)
            except Exception as e:
                print(f"Error reading {submission_file}: {e}")
                continue
        
        # Sort by submission ID
        submissions.sort(key=lambda x: x.get('submission_id', 0))
        return submissions
    
    def _save_submission(self, discussion_id: int, submission: Submission, 
                        graded_submission: GradedSubmission) -> int:
        """
        Save a graded submission to disk.
        
        Args:
            discussion_id: ID of the discussion
            submission: The original submission
            graded_submission: The grading results
            
        Returns:
            The assigned submission ID
        """
        submission_dir = self.base_dir / f"discussion_{discussion_id}" / "submissions"
        submission_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate submission ID
        submission_id = self._get_next_submission_id(submission_dir)
        
        # Prepare submission data
        submission_data = {
            "submission_id": submission_id,
            "discussion_id": discussion_id,
            "submission": submission.to_dict(),
            "grading": graded_submission.to_dict(),
            "created_at": datetime.now().isoformat()
        }
        
        # Save to file
        submission_file = submission_dir / f"submission_{submission_id}.json"
        with open(submission_file, 'w', encoding='utf-8') as f:
            json.dump(submission_data, f, indent=2, ensure_ascii=False)
        
        return submission_id
    
    def _get_next_submission_id(self, submission_dir: Path) -> int:
        """
        Get the next available submission ID.
        
        Args:
            submission_dir: Directory containing submissions
            
        Returns:
            Next available submission ID
        """
        if not submission_dir.exists():
            return 1
        
        max_id = 0
        for submission_file in submission_dir.glob("submission_*.json"):
            try:
                # Extract ID from filename
                id_str = submission_file.stem.split('_')[1]
                submission_id = int(id_str)
                max_id = max(max_id, submission_id)
            except (IndexError, ValueError):
                continue
        
        return max_id + 1
    
    def count_words(self, text: str) -> int:
        """
        Count the number of words in a text.
        
        Args:
            text: Text to count words in
            
        Returns:
            Number of words
        """
        return len(text.split())
    
    def format_grade_report(self, graded_submission: GradedSubmission, 
                           submission_file: str = "", total_points: int = 12) -> str:
        """
        Format a grading report for display.
        
        Args:
            graded_submission: The graded submission
            submission_file: Name of the submission file (optional)
            total_points: Total points possible
            
        Returns:
            Formatted report string
        """
        report_lines = []
        
        if submission_file:
            report_lines.extend([
                f"GRADING REPORT FOR: {submission_file}",
                "=" * 50,
                ""
            ])
        
        report_lines.extend([
            f"GRADE: {graded_submission.score}/{total_points}",
            "",
            f"WORD COUNT: {graded_submission.word_count} words"
        ])
        
        if not graded_submission.meets_word_count:
            report_lines.append("⚠️  WARNING: Below minimum word count")
        
        if graded_submission.addressed_questions:
            report_lines.extend([
                "",
                "QUESTIONS ADDRESSED:"
            ])
            for question, addressed in graded_submission.addressed_questions.items():
                status = "✓" if addressed else "✗"
                # Format question key for display
                display_key = question.replace("_", " ").title()
                report_lines.append(f"- {display_key}: {status}")
        
        report_lines.extend([
            "",
            "FEEDBACK:",
            graded_submission.feedback
        ])
        
        if graded_submission.improvement_suggestions:
            report_lines.extend([
                "",
                "SUGGESTIONS FOR IMPROVEMENT:"
            ])
            for suggestion in graded_submission.improvement_suggestions:
                report_lines.append(f"- {suggestion}")
        
        if submission_file:
            report_lines.append("=" * 50)
        
        return "\n".join(report_lines)
