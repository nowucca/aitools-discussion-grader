"""
Unit tests for the SubmissionController class.
"""

import pytest
import json
from unittest.mock import Mock, patch

from controllers.submission import SubmissionController
from lib.submission import GradedSubmission
from lib.discussion import Discussion


class TestSubmissionController:
    """Test cases for SubmissionController class."""
    
    @pytest.fixture
    def mock_graded_submission(self):
        """Create a mock graded submission for testing."""
        return GradedSubmission(
            score=9.5,
            feedback="Excellent analysis with clear examples and good structure.",
            improvement_suggestions=["Consider adding more recent examples", "Expand on future implications"],
            addressed_questions={"main_topic": True, "examples": True, "analysis": False},
            word_count=425,
            meets_word_count=True,
            submission_id=1,
            created_at="2025-01-15T10:30:00"
        )
    
    @pytest.fixture
    def mock_discussion(self):
        """Create a mock discussion for testing."""
        return Discussion(
            id=1,
            title="Test Discussion",
            question_content="What are your thoughts on AI?",
            points=12,
            min_words=300,
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00"
        )
    
    @pytest.fixture
    def submission_controller(self):
        """Create a SubmissionController instance for testing."""
        with patch('controllers.submission.SubmissionGrader') as mock_grader:
            controller = SubmissionController(base_dir="test_dir", api_key="test-key")
            controller.submission_grader = mock_grader.return_value
            return controller
    
    def test_init(self):
        """Test SubmissionController initialization."""
        with patch('controllers.submission.SubmissionGrader') as mock_grader:
            controller = SubmissionController(base_dir="test_dir", api_key="test-key")
            
            mock_grader.assert_called_once_with("test_dir", "test-key")
            assert controller.submission_grader is not None
    
    def test_grade_file_success_text_format(self, submission_controller, mock_graded_submission, mock_discussion):
        """Test successful grading of a file with text format."""
        # Mock the submission grader
        submission_controller.submission_grader.grade_submission = Mock(return_value=mock_graded_submission)
        submission_controller.submission_grader.discussion_manager.get_discussion = Mock(return_value=mock_discussion)
        submission_controller.submission_grader.format_grade_report = Mock(return_value="Formatted report")
        
        # Grade the submission
        result = submission_controller.grade(
            discussion_id=1,
            file_path="/path/to/submission.txt",
            save=True,
            format_type="text"
        )
        
        # Verify results
        assert result == "Formatted report"
        submission_controller.submission_grader.grade_submission.assert_called_once_with(
            discussion_id=1,
            file_path="/path/to/submission.txt",
            save=True
        )
        submission_controller.submission_grader.format_grade_report.assert_called_once_with(
            mock_graded_submission,
            submission_file="/path/to/submission.txt",
            total_points=12
        )
    
    
    def test_grade_file_error_handling(self, submission_controller):
        """Test error handling when grading fails."""
        # Mock the submission grader to raise an exception
        submission_controller.submission_grader.grade_submission = Mock(
            side_effect=Exception("Grading failed")
        )
        
        # Test text format error
        result = submission_controller.grade(
            discussion_id=1,
            file_path="/path/to/submission.txt",
            format_type="text"
        )
        assert "ERROR: Error grading submission: Grading failed" in result
        
        # Test JSON format error
        result = submission_controller.grade(
            discussion_id=1,
            file_path="/path/to/submission.txt",
            format_type="json"
        )
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Grading failed" in result_data["error"]
        
        # Test CSV format error
        result = submission_controller.grade(
            discussion_id=1,
            file_path="/path/to/submission.txt",
            format_type="csv"
        )
        assert "error,Error grading submission: Grading failed" in result
    
    def test_grade_text_success(self, submission_controller, mock_graded_submission, mock_discussion):
        """Test successful grading of text submission."""
        # Mock the submission grader
        submission_controller.submission_grader.grade_submission_text = Mock(return_value=mock_graded_submission)
        submission_controller.submission_grader.discussion_manager.get_discussion = Mock(return_value=mock_discussion)
        submission_controller.submission_grader.format_grade_report = Mock(return_value="Formatted report")
        
        # Grade the submission
        result = submission_controller.grade_text(
            discussion_id=1,
            submission_text="This is a test submission text.",
            save=True,
            format_type="text"
        )
        
        # Verify results
        assert result == "Formatted report"
        submission_controller.submission_grader.grade_submission_text.assert_called_once_with(
            discussion_id=1,
            submission_text="This is a test submission text.",
            save=True
        )
    
    def test_list_submissions_success_table_format(self, submission_controller):
        """Test successful listing of submissions with table format."""
        # Mock submission data
        mock_submissions = [
            {
                "submission_id": 1,
                "grading": {"score": 9.5, "word_count": 425, "meets_word_count": True},
                "created_at": "2025-01-15T10:30:00"
            },
            {
                "submission_id": 2,
                "grading": {"score": 7.0, "word_count": 280, "meets_word_count": False},
                "created_at": "2025-01-16T14:20:00"
            }
        ]
        
        submission_controller.submission_grader.list_submissions = Mock(return_value=mock_submissions)
        
        # List submissions
        result = submission_controller.list_submissions(discussion_id=1, format_type="table")
        
        # Verify results
        assert "ID" in result
        assert "Score" in result
        assert "Word Count" in result
        assert "9.5" in result
        assert "7" in result  # Could be "7" or "7.0" depending on formatting
        assert "✓" in result  # For meets word count
        assert "✗" in result  # For doesn't meet word count
    
    def test_list_submissions_success_json_format(self, submission_controller):
        """Test successful listing of submissions with JSON format."""
        # Mock submission data
        mock_submissions = [
            {
                "submission_id": 1,
                "grading": {"score": 9.5, "word_count": 425},
                "created_at": "2025-01-15T10:30:00"
            }
        ]
        
        submission_controller.submission_grader.list_submissions = Mock(return_value=mock_submissions)
        
        # List submissions
        result = submission_controller.list_submissions(discussion_id=1, format_type="json")
        
        # Verify results
        result_data = json.loads(result)
        assert len(result_data) == 1
        assert result_data[0]["submission_id"] == 1
        assert result_data[0]["grading"]["score"] == 9.5
    
    def test_list_submissions_empty(self, submission_controller):
        """Test listing submissions when none exist."""
        submission_controller.submission_grader.list_submissions = Mock(return_value=[])
        
        # Test table format
        result = submission_controller.list_submissions(discussion_id=1, format_type="table")
        assert "No submissions found for discussion 1" in result
        
        # Test JSON format
        result = submission_controller.list_submissions(discussion_id=1, format_type="json")
        result_data = json.loads(result)
        assert result_data == []
        
        # Test CSV format
        result = submission_controller.list_submissions(discussion_id=1, format_type="csv")
        assert result == "id,score,word_count,created_at"
    
    def test_list_submissions_error_handling(self, submission_controller):
        """Test error handling when listing submissions fails."""
        submission_controller.submission_grader.list_submissions = Mock(
            side_effect=Exception("List failed")
        )
        
        # Test text format error
        result = submission_controller.list_submissions(discussion_id=1, format_type="table")
        assert "ERROR: Error listing submissions: List failed" in result
        
        # Test JSON format error
        result = submission_controller.list_submissions(discussion_id=1, format_type="json")
        result_data = json.loads(result)
        assert "error" in result_data
        assert "List failed" in result_data["error"]
    
    def test_show_submission_success_text_format(self, submission_controller):
        """Test successful showing of submission details with text format."""
        # Mock submission data
        mock_submission_data = {
            "submission_id": 1,
            "discussion_id": 1,
            "grading": {
                "score": 9.5,
                "word_count": 425,
                "meets_word_count": True,
                "feedback": "Great work!",
                "improvement_suggestions": ["Add more examples"],
                "addressed_questions": {"main_topic": True}
            },
            "created_at": "2025-01-15T10:30:00"
        }
        
        submission_controller.submission_grader.get_submission = Mock(return_value=mock_submission_data)
        
        # Show submission
        result = submission_controller.show_submission(
            discussion_id=1,
            submission_id=1,
            format_type="text"
        )
        
        # Verify results
        assert "SUBMISSION DETAILS" in result
        assert "Submission ID: 1" in result
        assert "GRADE: 9.5/12" in result
        assert "Word Count: 425 words" in result
        assert "Great work!" in result
        assert "Add more examples" in result
    
    def test_show_submission_success_json_format(self, submission_controller):
        """Test successful showing of submission details with JSON format."""
        # Mock submission data
        mock_submission_data = {
            "submission_id": 1,
            "discussion_id": 1,
            "grading": {"score": 9.5, "word_count": 425},
            "created_at": "2025-01-15T10:30:00"
        }
        
        submission_controller.submission_grader.get_submission = Mock(return_value=mock_submission_data)
        
        # Show submission
        result = submission_controller.show_submission(
            discussion_id=1,
            submission_id=1,
            format_type="json"
        )
        
        # Verify results
        result_data = json.loads(result)
        assert result_data["submission_id"] == 1
        assert result_data["grading"]["score"] == 9.5
    
    def test_show_submission_not_found(self, submission_controller):
        """Test showing submission when it doesn't exist."""
        submission_controller.submission_grader.get_submission = Mock(return_value=None)
        
        # Test text format
        result = submission_controller.show_submission(
            discussion_id=1,
            submission_id=999,
            format_type="text"
        )
        assert "ERROR: Submission 999 not found in discussion 1" in result
        
        # Test JSON format
        result = submission_controller.show_submission(
            discussion_id=1,
            submission_id=999,
            format_type="json"
        )
        result_data = json.loads(result)
        assert "error" in result_data
        assert "not found" in result_data["error"]
    
    def test_show_submission_error_handling(self, submission_controller):
        """Test error handling when showing submission fails."""
        submission_controller.submission_grader.get_submission = Mock(
            side_effect=Exception("Retrieval failed")
        )
        
        # Test text format error
        result = submission_controller.show_submission(
            discussion_id=1,
            submission_id=1,
            format_type="text"
        )
        assert "ERROR: Error retrieving submission: Retrieval failed" in result
        
        # Test JSON format error
        result = submission_controller.show_submission(
            discussion_id=1,
            submission_id=1,
            format_type="json"
        )
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Retrieval failed" in result_data["error"]
    
    
    def test_grade_clipboard_success(self, submission_controller, mock_graded_submission, mock_discussion):
        """Test successful grading from clipboard."""
        # Mock clipboard functionality
        with patch('pyperclip.paste', return_value="Test submission from clipboard"):
            submission_controller.submission_grader.grade_submission_text = Mock(return_value=mock_graded_submission)
            submission_controller.submission_grader.discussion_manager.get_discussion = Mock(return_value=mock_discussion)
            submission_controller.submission_grader.format_grade_report = Mock(return_value="Formatted report")
            
            result = submission_controller.grade_clipboard(
                discussion_id=1,
                save=True,
                format_type="text"
            )
            
            assert result == "Formatted report"
            submission_controller.submission_grader.grade_submission_text.assert_called_once_with(
                discussion_id=1,
                submission_text="Test submission from clipboard",
                save=True
            )
    
    def test_grade_clipboard_empty(self, submission_controller):
        """Test grading from clipboard when clipboard is empty."""
        with patch('pyperclip.paste', return_value=""):
            result = submission_controller.grade_clipboard(discussion_id=1)
            assert "ERROR: Could not read submission from clipboard" in result
    
    def test_get_pasted_submission_success(self, submission_controller):
        """Test getting pasted submission successfully."""
        test_content = "Student submission content here"
        
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
             patch('controllers.submission.subprocess.call') as mock_subprocess, \
             patch('builtins.open', create=True) as mock_open, \
             patch('builtins.input') as mock_input, \
             patch('controllers.submission.os.unlink') as mock_unlink:
            
            # Mock temporary file
            mock_file = Mock()
            mock_file.name = '/tmp/test_submission.txt'
            mock_tempfile.return_value.__enter__.return_value = mock_file
            
            # Mock subprocess call (text editor)
            mock_subprocess.return_value = 0
            
            # Mock file reading - need to decode bytes
            mock_open.return_value.__enter__.return_value.read.return_value = test_content.encode('utf-8')
            
            # Mock user pressing enter
            mock_input.return_value = ""
            
            result = submission_controller.get_pasted_submission(student_num=1)
            
            assert result == test_content, f"Expected '{test_content}' but got '{result}'"
            mock_tempfile.assert_called_once()
            mock_subprocess.assert_called_once()
            mock_unlink.assert_called_once_with('/tmp/test_submission.txt')
    
    def test_get_pasted_submission_editor_cancelled(self, submission_controller):
        """Test getting pasted submission when editor is cancelled."""
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
             patch('controllers.submission.subprocess.call') as mock_subprocess, \
             patch('builtins.input') as mock_input, \
             patch('builtins.open', create=True) as mock_open, \
             patch('controllers.submission.os.unlink') as mock_unlink:
            
            # Mock temporary file
            mock_file = Mock()
            mock_file.name = '/tmp/test_submission.txt'
            mock_tempfile.return_value.__enter__.return_value = mock_file
            
            # Mock subprocess call returning non-zero (cancelled)
            mock_subprocess.return_value = 0
            
            # Mock empty file content (user left it empty to exit)
            mock_open.return_value.__enter__.return_value.read.return_value = b""
            
            # Mock user input
            mock_input.return_value = ""
            
            result = submission_controller.get_pasted_submission(student_num=1)
            
            assert result is None, "Expected None when submission is empty"
    
    def test_interactive_batch_grading_complete_session(self, submission_controller, mock_graded_submission, mock_discussion):
        """Test complete interactive batch grading session."""
        # Mock submission content
        test_submissions = [
            "First student submission content",
            "Second student submission content",
            None  # End the session
        ]
        
        with patch.object(submission_controller, 'get_pasted_submission', side_effect=test_submissions):
            submission_controller.submission_grader.grade_submission_text = Mock(return_value=mock_graded_submission)
            submission_controller.submission_grader.discussion_manager.get_discussion = Mock(return_value=mock_discussion)
            submission_controller.submission_grader.format_grade_report = Mock(return_value="Grade: 9.5/12")
            
            # Mock the grade_text method to avoid calling the real implementation
            with patch.object(submission_controller, 'grade_text', return_value="Grade: 9.5/12"):
                result = submission_controller.interactive_batch_grading(discussion_id=1, save=True)
            
            # Should process 2 submissions
            assert "Successfully graded 2/2 submissions" in result, f"Expected success message in result: {result}"
    
    def test_interactive_batch_grading_quit_immediately(self, submission_controller, mock_discussion):
        """Test interactive batch grading when user quits immediately."""
        
        with patch.object(submission_controller, 'get_pasted_submission', return_value=None):
            submission_controller.submission_grader.discussion_manager.get_discussion = Mock(return_value=mock_discussion)
            
            result = submission_controller.interactive_batch_grading(discussion_id=1)
            
            assert "Successfully graded 0/0 submissions" in result, f"Expected quit message in result: {result}"
    
    def test_interactive_batch_grading_error_handling(self, submission_controller, mock_discussion):
        """Test error handling in interactive batch grading."""
        
        with patch.object(submission_controller, 'get_pasted_submission', side_effect=["test content", None]):
            submission_controller.submission_grader.discussion_manager.get_discussion = Mock(return_value=mock_discussion)
            
            # Mock grade_text to raise an exception
            with patch.object(submission_controller, 'grade_text', side_effect=Exception("Grading error")):
                result = submission_controller.interactive_batch_grading(discussion_id=1)
                
                assert "Student #1: FAILED - Grading error" in result, f"Expected error message in result: {result}"
                assert "Successfully graded 0/1 submissions" in result, f"Expected failure count in result: {result}"
