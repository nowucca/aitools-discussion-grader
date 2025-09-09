"""
Submission Controller - Handles submission-related operations for the CLI.

This module provides the SubmissionController class that bridges between
the CLI and the submission grading library layer.
"""

import json
import csv
import os
import sys
import tempfile
import subprocess
from io import StringIO
from typing import Dict, Any, List, Optional
from tabulate import tabulate

from lib.submission_grader import SubmissionGrader
from lib.submission import GradedSubmission


class SubmissionController:
    """Controller for submission operations."""
    
    def __init__(self, base_dir: str = "discussions", api_key: Optional[str] = None):
        """
        Initialize the SubmissionController.
        
        Args:
            base_dir: Base directory for discussion storage
            api_key: Anthropic API key (optional, can use environment variable)
        """
        self.submission_grader = SubmissionGrader(base_dir, api_key)
    
    def grade(self, discussion_id: int, file_path: str, save: bool = True, 
              format_type: str = "text") -> str:
        """
        Grade a single submission file.
        
        Args:
            discussion_id: ID of the discussion
            file_path: Path to the submission file
            save: Whether to save the graded submission
            format_type: Output format ('text', 'json', 'csv')
            
        Returns:
            Formatted grading result
        """
        try:
            # Grade the submission
            graded_submission = self.submission_grader.grade_submission(
                discussion_id=discussion_id,
                file_path=file_path,
                save=save
            )
            
            # Get discussion info for total points
            discussion = self.submission_grader.discussion_manager.get_discussion(discussion_id)
            total_points = discussion.points if discussion else 12
            
            # Format the result based on requested format
            if format_type == "json":
                return self._format_grade_as_json(graded_submission, file_path, total_points)
            elif format_type == "csv":
                return self._format_grade_as_csv(graded_submission, file_path, total_points)
            else:  # text format
                return self.submission_grader.format_grade_report(
                    graded_submission, 
                    submission_file=file_path,
                    total_points=total_points
                )
                
        except Exception as e:
            error_msg = f"Error grading submission: {str(e)}"
            if format_type == "json":
                return json.dumps({"error": error_msg}, indent=2)
            elif format_type == "csv":
                return f"error,{error_msg}"
            else:
                return f"ERROR: {error_msg}"
    
    def grade_text(self, discussion_id: int, submission_text: str, save: bool = True,
                   format_type: str = "text") -> str:
        """
        Grade submission text directly.
        
        Args:
            discussion_id: ID of the discussion
            submission_text: The submission text to grade
            save: Whether to save the graded submission
            format_type: Output format ('text', 'json', 'csv')
            
        Returns:
            Formatted grading result
        """
        try:
            # Grade the submission
            graded_submission = self.submission_grader.grade_submission_text(
                discussion_id=discussion_id,
                submission_text=submission_text,
                save=save
            )
            
            # Get discussion info for total points
            discussion = self.submission_grader.discussion_manager.get_discussion(discussion_id)
            total_points = discussion.points if discussion else 12
            
            # Format the result based on requested format
            if format_type == "json":
                return self._format_grade_as_json(graded_submission, "text_submission", total_points)
            elif format_type == "csv":
                return self._format_grade_as_csv(graded_submission, "text_submission", total_points)
            else:  # text format
                return self.submission_grader.format_grade_report(
                    graded_submission, 
                    submission_file="",
                    total_points=total_points
                )
                
        except Exception as e:
            error_msg = f"Error grading submission: {str(e)}"
            if format_type == "json":
                return json.dumps({"error": error_msg}, indent=2)
            elif format_type == "csv":
                return f"error,{error_msg}"
            else:
                return f"ERROR: {error_msg}"
    
    def list_submissions(self, discussion_id: int, format_type: str = "table") -> str:
        """
        List all submissions for a discussion.
        
        Args:
            discussion_id: ID of the discussion
            format_type: Output format ('table', 'json', 'csv')
            
        Returns:
            Formatted list of submissions
        """
        try:
            submissions = self.submission_grader.list_submissions(discussion_id)
            
            if not submissions:
                if format_type == "json":
                    return json.dumps([], indent=2)
                elif format_type == "csv":
                    return "id,score,word_count,created_at"
                else:
                    return f"No submissions found for discussion {discussion_id}."
            
            if format_type == "json":
                return json.dumps(submissions, indent=2)
            elif format_type == "csv":
                return self._format_submissions_as_csv(submissions)
            else:  # table format
                return self._format_submissions_as_table(submissions)
                
        except Exception as e:
            error_msg = f"Error listing submissions: {str(e)}"
            if format_type == "json":
                return json.dumps({"error": error_msg}, indent=2)
            elif format_type == "csv":
                return f"error,{error_msg}"
            else:
                return f"ERROR: {error_msg}"
    
    def show_submission(self, discussion_id: int, submission_id: int, 
                       format_type: str = "text") -> str:
        """
        Show details for a specific submission.
        
        Args:
            discussion_id: ID of the discussion
            submission_id: ID of the submission
            format_type: Output format ('text', 'json', 'csv')
            
        Returns:
            Formatted submission details
        """
        try:
            submission_data = self.submission_grader.get_submission(discussion_id, submission_id)
            
            if not submission_data:
                error_msg = f"Submission {submission_id} not found in discussion {discussion_id}"
                if format_type == "json":
                    return json.dumps({"error": error_msg}, indent=2)
                elif format_type == "csv":
                    return f"error,{error_msg}"
                else:
                    return f"ERROR: {error_msg}"
            
            if format_type == "json":
                return json.dumps(submission_data, indent=2)
            elif format_type == "csv":
                return self._format_submission_details_as_csv(submission_data)
            else:  # text format
                return self._format_submission_details_as_text(submission_data)
                
        except Exception as e:
            error_msg = f"Error retrieving submission: {str(e)}"
            if format_type == "json":
                return json.dumps({"error": error_msg}, indent=2)
            elif format_type == "csv":
                return f"error,{error_msg}"
            else:
                return f"ERROR: {error_msg}"
    
    def _format_grade_as_json(self, graded_submission: GradedSubmission, 
                             file_name: str, total_points: int) -> str:
        """Format grading result as JSON."""
        result = {
            "file": file_name,
            "grade": {
                "score": graded_submission.score,
                "total_points": total_points,
                "percentage": round((graded_submission.score / total_points) * 100, 1)
            },
            "word_count": graded_submission.word_count,
            "meets_word_count": graded_submission.meets_word_count,
            "feedback": graded_submission.feedback,
            "improvement_suggestions": graded_submission.improvement_suggestions,
            "addressed_questions": graded_submission.addressed_questions,
            "submission_id": graded_submission.submission_id,
            "created_at": graded_submission.created_at
        }
        return json.dumps(result, indent=2)
    
    def _format_grade_as_csv(self, graded_submission: GradedSubmission, 
                            file_name: str, total_points: int) -> str:
        """Format grading result as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "file", "score", "total_points", "percentage", "word_count", 
            "meets_word_count", "feedback", "submission_id", "created_at"
        ])
        
        # Data
        percentage = round((graded_submission.score / total_points) * 100, 1)
        writer.writerow([
            file_name,
            graded_submission.score,
            total_points,
            percentage,
            graded_submission.word_count,
            graded_submission.meets_word_count,
            graded_submission.feedback.replace('\n', ' '),  # Remove newlines for CSV
            graded_submission.submission_id or "",
            graded_submission.created_at
        ])
        
        return output.getvalue().strip()
    
    def get_pasted_submission(self, student_num: int) -> Optional[str]:
        """Get a single submission pasted by the user via text editor."""
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
            return self.get_pasted_submission(student_num)
    
    def interactive_batch_grading(self, discussion_id: int, save: bool = True) -> str:
        """Run an interactive batch grading session."""
        student_count = 0
        successful = 0
        results = []
        
        print("\n=== Interactive Grading Session Started ===")
        print(f"Grading submissions for discussion {discussion_id}")
        print("You can grade multiple submissions one at a time.")
        print("After each submission is graded, you'll be prompted for the next one.")
        print("Leave a submission empty to end the session.")
        
        # Get discussion info
        try:
            discussion = self.submission_grader.discussion_manager.get_discussion(discussion_id)
            if not discussion:
                return f"ERROR: Discussion {discussion_id} not found."
            
            print(f"\nDiscussion: {discussion.title}")
            print(f"Points: {discussion.points}")
            print(f"Minimum words: {discussion.min_words}")
        except Exception as e:
            return f"ERROR: Could not load discussion {discussion_id}: {str(e)}"
        
        while True:
            student_count += 1
            submission = self.get_pasted_submission(student_count)
            
            if submission is None:
                break
            
            try:
                print(f"\nGrading submission #{student_count}...")
                
                # Grade the submission using the existing grade_text method
                result = self.grade_text(
                    discussion_id=discussion_id,
                    submission_text=submission,
                    save=save,
                    format_type="text"
                )
                
                print(result)
                successful += 1
                results.append(f"Student #{student_count}: SUCCESS")
                
            except Exception as e:
                error_msg = f"Error grading submission #{student_count}: {str(e)}"
                print(f"ERROR: {error_msg}")
                results.append(f"Student #{student_count}: FAILED - {str(e)}")
            
            print("\nReady for next submission...")
        
        # Session summary
        session_summary = f"""
=== Grading Session Complete ===
Successfully graded {successful}/{student_count-1} submissions.

Results:
{chr(10).join(results)}
"""
        
        print(session_summary)
        return session_summary

    def clipboard_batch_grading(self, discussion_id: int, save: bool = True) -> str:
        """Run a clipboard-based batch grading session."""
        student_count = 0
        successful = 0
        results = []
        
        print("\n=== Clipboard-Based Grading Session Started ===")
        print(f"Grading submissions for discussion {discussion_id}")
        print("INSTRUCTIONS:")
        print("1. Copy a student submission to your clipboard")
        print("2. Press Enter to grade the submission")
        print("3. Repeat for each student")
        print("4. Press Enter without copying anything (or type 'quit') to end the session")
        
        # Get discussion info
        try:
            discussion = self.submission_grader.discussion_manager.get_discussion(discussion_id)
            if not discussion:
                return f"ERROR: Discussion {discussion_id} not found."
            
            print(f"\nDiscussion: {discussion.title}")
            print(f"Points: {discussion.points}")
            print(f"Minimum words: {discussion.min_words}")
        except Exception as e:
            return f"ERROR: Could not load discussion {discussion_id}: {str(e)}"
        
        while True:
            student_count += 1
            print(f"\n=== Student #{student_count} ===")
            print("Copy the submission to your clipboard, then press Enter (or type 'quit' to exit)...")
            
            user_input = input().strip()
            if user_input.lower() in ['quit', 'q', 'exit']:
                break
            
            # Get submission from clipboard
            submission = self.get_clipboard_submission()
            
            if submission is None:
                print("No submission found in clipboard. Ending grading session.")
                break
            
            # Check if clipboard appears to be empty or just whitespace
            if not submission.strip():
                print("Clipboard appears to be empty. Ending grading session.")
                break
            
            try:
                print(f"\nGrading submission #{student_count} ({len(submission.split())} words)...")
                
                # Grade the submission using the existing grade_text method
                result = self.grade_text(
                    discussion_id=discussion_id,
                    submission_text=submission,
                    save=save,
                    format_type="text"
                )
                
                print(result)
                
                # Copy the result to clipboard for easy pasting into grading system
                try:
                    import pyperclip
                    pyperclip.copy(result)
                    print("\n✅ Grading result copied to clipboard - you can now paste it into your grading system!")
                except ImportError:
                    print("\n📋 Note: Install pyperclip to automatically copy results to clipboard")
                except Exception as e:
                    print(f"\n📋 Note: Could not copy to clipboard: {str(e)}")
                
                successful += 1
                results.append(f"Student #{student_count}: SUCCESS")
                
            except Exception as e:
                error_msg = f"Error grading submission #{student_count}: {str(e)}"
                print(f"ERROR: {error_msg}")
                results.append(f"Student #{student_count}: FAILED - {str(e)}")
            
            print(f"\nStudent #{student_count} complete. Ready for next submission...")
        
        # Session summary
        session_summary = f"""
=== Grading Session Complete ===
Successfully graded {successful}/{student_count-1} submissions.

Results:
{chr(10).join(results)}

TIP: You can also grade individual submissions with:
     python grader.py submission grade {discussion_id} --clipboard
"""
        
        print(session_summary)
        return session_summary

    def get_clipboard_submission(self) -> Optional[str]:
        """Get submission text from clipboard using pyperclip."""
        try:
            import pyperclip
            content = pyperclip.paste()
            
            if not content.strip():
                print("Clipboard is empty. Please copy a submission to your clipboard first.")
                return None
                
            return content
        except ImportError:
            print("Error: pyperclip not available. Please install with: pip install pyperclip")
            return None
        except Exception as e:
            print(f"Error reading from clipboard: {str(e)}")
            return None
    
    def grade_clipboard(self, discussion_id: int, save: bool = True, 
                       format_type: str = "text") -> str:
        """Grade submission text from clipboard."""
        submission_text = self.get_clipboard_submission()
        
        if submission_text is None:
            return "ERROR: Could not read submission from clipboard."
        
        print(f"Grading submission from clipboard ({len(submission_text.split())} words)...")
        
        return self.grade_text(
            discussion_id=discussion_id,
            submission_text=submission_text,
            save=save,
            format_type=format_type
        )
    
    def _format_submissions_as_table(self, submissions: List[Dict[str, Any]]) -> str:
        """Format submissions list as a table."""
        headers = ["ID", "Score", "Word Count", "Meets Min", "Created"]
        rows = []
        
        for submission in submissions:
            grading = submission.get("grading", {})
            rows.append([
                submission.get("submission_id", "N/A"),
                f"{grading.get('score', 0):.1f}",
                grading.get("word_count", 0),
                "✓" if grading.get("meets_word_count", False) else "✗",
                submission.get("created_at", "")[:10]  # Just the date part
            ])
        
        return tabulate(rows, headers=headers, tablefmt="grid")
    
    def _format_submissions_as_csv(self, submissions: List[Dict[str, Any]]) -> str:
        """Format submissions list as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["id", "score", "word_count", "meets_word_count", "created_at"])
        
        # Data
        for submission in submissions:
            grading = submission.get("grading", {})
            writer.writerow([
                submission.get("submission_id", ""),
                grading.get("score", 0),
                grading.get("word_count", 0),
                grading.get("meets_word_count", False),
                submission.get("created_at", "")
            ])
        
        return output.getvalue().strip()
    
    def _format_submission_details_as_text(self, submission_data: Dict[str, Any]) -> str:
        """Format submission details as text."""
        submission = submission_data.get("submission", {})
        grading = submission_data.get("grading", {})
        
        lines = [
            f"SUBMISSION DETAILS",
            "=" * 50,
            "",
            f"Submission ID: {submission_data.get('submission_id', 'N/A')}",
            f"Discussion ID: {submission_data.get('discussion_id', 'N/A')}",
            f"Created: {submission_data.get('created_at', 'N/A')}",
            "",
            f"GRADE: {grading.get('score', 0)}/{submission_data.get('total_points', 12)}",
            f"Word Count: {grading.get('word_count', 0)} words",
            f"Meets Word Count: {'Yes' if grading.get('meets_word_count', False) else 'No'}",
            "",
            "FEEDBACK:",
            grading.get("feedback", "No feedback available"),
            ""
        ]
        
        # Add improvement suggestions if available
        suggestions = grading.get("improvement_suggestions", [])
        if suggestions:
            lines.extend([
                "SUGGESTIONS FOR IMPROVEMENT:",
                *[f"- {suggestion}" for suggestion in suggestions],
                ""
            ])
        
        # Add addressed questions if available
        addressed = grading.get("addressed_questions", {})
        if addressed:
            lines.extend([
                "QUESTIONS ADDRESSED:",
                *[f"- {key.replace('_', ' ').title()}: {'✓' if value else '✗'}" 
                  for key, value in addressed.items()],
                ""
            ])
        
        lines.append("=" * 50)
        return "\n".join(lines)
    
    def _format_submission_details_as_csv(self, submission_data: Dict[str, Any]) -> str:
        """Format submission details as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        submission = submission_data.get("submission", {})
        grading = submission_data.get("grading", {})
        
        # Header
        writer.writerow([
            "submission_id", "discussion_id", "score", "word_count", 
            "meets_word_count", "feedback", "created_at"
        ])
        
        # Data
        writer.writerow([
            submission_data.get("submission_id", ""),
            submission_data.get("discussion_id", ""),
            grading.get("score", 0),
            grading.get("word_count", 0),
            grading.get("meets_word_count", False),
            grading.get("feedback", "").replace('\n', ' '),  # Remove newlines for CSV
            submission_data.get("created_at", "")
        ])
        
        return output.getvalue().strip()
