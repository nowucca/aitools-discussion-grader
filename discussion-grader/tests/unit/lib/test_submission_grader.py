"""
Unit tests for the SubmissionGrader class.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from lib.submission_grader import SubmissionGrader
from lib.submission import Submission, GradedSubmission
from lib.grading import GradingCriteria
from lib.discussion import Discussion


class TestSubmissionGrader:
    """Test cases for SubmissionGrader class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
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
    def mock_graded_submission(self):
        """Create a mock graded submission for testing."""
        return GradedSubmission(
            score=10.0,
            feedback="Good analysis with clear examples.",
            improvement_suggestions=["Consider more examples", "Expand on implications"],
            addressed_questions={"ai_impact": True, "future_trends": False},
            word_count=350,
            meets_word_count=True
        )
    
    @pytest.fixture
    def submission_grader(self, temp_dir):
        """Create a SubmissionGrader instance for testing."""
        with patch('lib.submission_grader.AIGrader') as mock_ai_grader:
            grader = SubmissionGrader(base_dir=temp_dir, api_key="test-key")
            grader.ai_grader = mock_ai_grader.return_value
            return grader
    
    def test_init(self, temp_dir):
        """Test SubmissionGrader initialization."""
        with patch('lib.submission_grader.AIGrader') as mock_ai_grader:
            grader = SubmissionGrader(base_dir=temp_dir, api_key="test-key")
            
            assert grader.base_dir == Path(temp_dir)
            assert grader.discussion_manager is not None
            mock_ai_grader.assert_called_once_with("test-key")
    
    def test_grade_submission_file_success(self, submission_grader, mock_discussion, mock_graded_submission, temp_dir):
        """Test successful grading of a submission file."""
        # Mock the discussion manager
        submission_grader.discussion_manager.get_discussion = Mock(return_value=mock_discussion)
        
        # Mock the AI grader
        submission_grader.ai_grader.grade_submission = Mock(return_value=mock_graded_submission)
        
        # Create a test submission file
        test_file = Path(temp_dir) / "test_submission.txt"
        test_file.write_text("This is a test submission with enough words to meet requirements.")
        
        # Mock the save method
        submission_grader._save_submission = Mock(return_value=1)
        
        # Grade the submission
        result = submission_grader.grade_submission(
            discussion_id=1,
            file_path=str(test_file),
            save=True
        )
        
        # Verify results
        assert result == mock_graded_submission
        assert result.submission_id == 1
        submission_grader.discussion_manager.get_discussion.assert_called_once_with(1)
        submission_grader.ai_grader.grade_submission.assert_called_once()
        submission_grader._save_submission.assert_called_once()
    
    def test_grade_submission_file_discussion_not_found(self, submission_grader):
        """Test grading when discussion doesn't exist."""
        submission_grader.discussion_manager.get_discussion = Mock(return_value=None)
        
        with pytest.raises(ValueError, match="Discussion 1 not found"):
            submission_grader.grade_submission(
                discussion_id=1,
                file_path="/nonexistent/file.txt"
            )
    
    def test_grade_submission_text_success(self, submission_grader, mock_discussion, mock_graded_submission):
        """Test successful grading of submission text."""
        # Mock the discussion manager
        submission_grader.discussion_manager.get_discussion = Mock(return_value=mock_discussion)
        
        # Mock the AI grader
        submission_grader.ai_grader.grade_submission = Mock(return_value=mock_graded_submission)
        
        # Mock the save method
        submission_grader._save_submission = Mock(return_value=2)
        
        # Grade the submission
        result = submission_grader.grade_submission_text(
            discussion_id=1,
            submission_text="This is a test submission with enough words to meet requirements.",
            save=True
        )
        
        # Verify results
        assert result == mock_graded_submission
        assert result.submission_id == 2
        submission_grader.discussion_manager.get_discussion.assert_called_once_with(1)
        submission_grader.ai_grader.grade_submission.assert_called_once()
        submission_grader._save_submission.assert_called_once()
    
    def test_grade_submission_text_no_save(self, submission_grader, mock_discussion, mock_graded_submission):
        """Test grading submission text without saving."""
        # Mock the discussion manager
        submission_grader.discussion_manager.get_discussion = Mock(return_value=mock_discussion)
        
        # Mock the AI grader
        submission_grader.ai_grader.grade_submission = Mock(return_value=mock_graded_submission)
        
        # Grade the submission without saving
        result = submission_grader.grade_submission_text(
            discussion_id=1,
            submission_text="This is a test submission.",
            save=False
        )
        
        # Verify results
        assert result == mock_graded_submission
        assert result.submission_id is None  # Should not be set when not saving
        submission_grader.discussion_manager.get_discussion.assert_called_once_with(1)
        submission_grader.ai_grader.grade_submission.assert_called_once()
    
    def test_get_submission_success(self, submission_grader, temp_dir):
        """Test successful retrieval of a submission."""
        # Create submission directory and file
        submission_dir = Path(temp_dir) / "discussion_1" / "submissions"
        submission_dir.mkdir(parents=True)
        
        submission_data = {
            "submission_id": 1,
            "discussion_id": 1,
            "submission": {"text": "Test submission"},
            "grading": {"score": 10, "feedback": "Good work"}
        }
        
        submission_file = submission_dir / "submission_1.json"
        with open(submission_file, 'w') as f:
            json.dump(submission_data, f)
        
        # Retrieve the submission
        result = submission_grader.get_submission(discussion_id=1, submission_id=1)
        
        # Verify results
        assert result == submission_data
    
    def test_get_submission_not_found(self, submission_grader):
        """Test retrieval of non-existent submission."""
        result = submission_grader.get_submission(discussion_id=1, submission_id=999)
        assert result is None
    
    def test_list_submissions_success(self, submission_grader, temp_dir):
        """Test successful listing of submissions."""
        # Create submission directory and files
        submission_dir = Path(temp_dir) / "discussion_1" / "submissions"
        submission_dir.mkdir(parents=True)
        
        # Create multiple submission files
        for i in range(1, 4):
            submission_data = {
                "submission_id": i,
                "discussion_id": 1,
                "submission": {"text": f"Test submission {i}"},
                "grading": {"score": 8 + i, "feedback": f"Feedback {i}"}
            }
            
            submission_file = submission_dir / f"submission_{i}.json"
            with open(submission_file, 'w') as f:
                json.dump(submission_data, f)
        
        # List submissions
        result = submission_grader.list_submissions(discussion_id=1)
        
        # Verify results
        assert len(result) == 3
        assert all('file_name' in submission for submission in result)
        assert result[0]['submission_id'] == 1
        assert result[2]['submission_id'] == 3
    
    def test_list_submissions_empty(self, submission_grader):
        """Test listing submissions when none exist."""
        result = submission_grader.list_submissions(discussion_id=1)
        assert result == []
    
    def test_save_submission(self, submission_grader, temp_dir, mock_graded_submission):
        """Test saving a graded submission."""
        # Create a test submission
        submission = Submission(
            discussion_id=1,
            submission_text="Test submission text",
            question_text="Test question"
        )
        
        # Save the submission
        submission_id = submission_grader._save_submission(1, submission, mock_graded_submission)
        
        # Verify the submission was saved
        assert submission_id == 1
        
        submission_dir = Path(temp_dir) / "discussion_1" / "submissions"
        submission_file = submission_dir / "submission_1.json"
        assert submission_file.exists()
        
        # Verify file contents
        with open(submission_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['submission_id'] == 1
        assert saved_data['discussion_id'] == 1
        assert 'submission' in saved_data
        assert 'grading' in saved_data
        assert 'created_at' in saved_data
    
    def test_get_next_submission_id_empty_dir(self, submission_grader, temp_dir):
        """Test getting next submission ID when directory is empty."""
        submission_dir = Path(temp_dir) / "discussion_1" / "submissions"
        submission_id = submission_grader._get_next_submission_id(submission_dir)
        assert submission_id == 1
    
    def test_get_next_submission_id_with_existing(self, submission_grader, temp_dir):
        """Test getting next submission ID with existing submissions."""
        submission_dir = Path(temp_dir) / "discussion_1" / "submissions"
        submission_dir.mkdir(parents=True)
        
        # Create some existing submission files
        for i in [1, 3, 5]:
            submission_file = submission_dir / f"submission_{i}.json"
            submission_file.write_text("{}")
        
        submission_id = submission_grader._get_next_submission_id(submission_dir)
        assert submission_id == 6
    
    def test_count_words(self, submission_grader):
        """Test word counting functionality."""
        text = "This is a test with five words"
        assert submission_grader.count_words(text) == 7
        
        # Test empty text
        assert submission_grader.count_words("") == 0
        
        # Test text with extra spaces
        assert submission_grader.count_words("  word1   word2  word3  ") == 3
    
    def test_format_grade_report_basic(self, submission_grader, mock_graded_submission):
        """Test basic grade report formatting."""
        report = submission_grader.format_grade_report(
            mock_graded_submission,
            submission_file="test.txt",
            total_points=12
        )
        
        assert "GRADING REPORT FOR: test.txt" in report
        assert "GRADE: 10.0/12" in report
        assert "WORD COUNT: 350 words" in report
        assert "FEEDBACK:" in report
        assert "Good analysis with clear examples." in report
        assert "SUGGESTIONS FOR IMPROVEMENT:" in report
        assert "Consider more examples" in report
    
    def test_format_grade_report_with_questions(self, submission_grader):
        """Test grade report formatting with addressed questions."""
        graded_submission = GradedSubmission(
            score=8.5,
            feedback="Good work overall.",
            addressed_questions={
                "ai_impact": True,
                "future_trends": False,
                "ethical_concerns": True
            },
            word_count=280,
            meets_word_count=False
        )
        
        report = submission_grader.format_grade_report(graded_submission, total_points=12)
        
        assert "GRADE: 8.5/12" in report
        assert "⚠️  WARNING: Below minimum word count" in report
        assert "QUESTIONS ADDRESSED:" in report
        assert "- Ai Impact: ✓" in report
        assert "- Future Trends: ✗" in report
        assert "- Ethical Concerns: ✓" in report
    
    def test_format_grade_report_minimal(self, submission_grader):
        """Test grade report formatting with minimal data."""
        graded_submission = GradedSubmission(
            score=6.0,
            feedback="Needs improvement.",
            word_count=150,
            meets_word_count=False
        )
        
        report = submission_grader.format_grade_report(graded_submission)
        
        assert "GRADE: 6.0/12" in report
        assert "WORD COUNT: 150 words" in report
        assert "⚠️  WARNING: Below minimum word count" in report
        assert "FEEDBACK:" in report
        assert "Needs improvement." in report
        # Should not contain sections for empty data
        assert "QUESTIONS ADDRESSED:" not in report
        assert "SUGGESTIONS FOR IMPROVEMENT:" not in report
