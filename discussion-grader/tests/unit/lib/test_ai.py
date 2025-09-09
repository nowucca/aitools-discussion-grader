"""
Unit tests for the AI grading functionality.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from lib.ai import AIGrader, AIConnectionError, AIResponseError
from lib.submission import Submission, GradedSubmission
from lib.grading import GradingCriteria


class TestAIGrader:
    """Test suite for the AIGrader class."""
    
    def test_init_with_api_key(self):
        """Test initialization with an API key."""
        grader = AIGrader(api_key="test_key")
        assert grader.api_key == "test_key"
    
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'env_test_key'})
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        grader = AIGrader()
        assert grader.api_key == "env_test_key"
    
    def test_init_missing_key(self):
        """Test initialization with no API key."""
        with patch.dict('os.environ', clear=True):
            with pytest.raises(ValueError, match="Anthropic API key is required"):
                AIGrader()
    
    @patch('anthropic.Anthropic')
    def test_grade_submission_success(self, mock_anthropic):
        """Test successful submission grading."""
        # Set up mock response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        mock_content = MagicMock()
        mock_content.text = json.dumps({
            "score": 10,
            "feedback": "Good work",
            "improvement_suggestions": ["Add more examples", "Discuss limitations"]
        })
        
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        
        mock_client.messages.create.return_value = mock_response
        
        # Create test data
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering is the application of engineering principles to software development.",
            question_text="What is software engineering?"
        )
        
        criteria = GradingCriteria.default_criteria()
        
        # Test grading
        grader = AIGrader(api_key="test_key")
        result = grader.grade_submission(submission, criteria)
        
        # Verify result
        assert isinstance(result, GradedSubmission)
        assert result.score == 10
        assert result.feedback == "Good work"
        assert "Add more examples" in result.improvement_suggestions
        assert result.word_count == submission.word_count
    
    @patch('anthropic.Anthropic')
    def test_grade_submission_api_error(self, mock_anthropic):
        """Test handling of API errors."""
        # Import here to avoid requiring the package for tests
        import anthropic
        
        # Set up mock to raise an error
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_request = MagicMock()
        mock_body = {"error": "something went wrong"}
        mock_client.messages.create.side_effect = anthropic.APIError("API connection error", request=mock_request, body=mock_body)
        
        # Test data
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering is the application of engineering principles to software development.",
            question_text="What is software engineering?"
        )
        
        # Test error handling
        grader = AIGrader(api_key="test_key")
        with pytest.raises(AIConnectionError, match="API error"):
            grader.grade_submission(submission)
    
    @patch('anthropic.Anthropic')
    def test_parse_response_invalid_json(self, mock_anthropic):
        """Test handling of invalid JSON responses."""
        # Set up mock with invalid JSON
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        mock_content = MagicMock()
        mock_content.text = "This is not valid JSON"
        
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        
        mock_client.messages.create.return_value = mock_response
        
        # Test data
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering is the application of engineering principles to software development.",
            question_text="What is software engineering?"
        )
        
        # Test error handling
        grader = AIGrader(api_key="test_key")
        with pytest.raises(AIResponseError, match="Could not find valid JSON"):
            grader.grade_submission(submission)
    
    @patch('anthropic.Anthropic')
    def test_parse_response_malformed_json(self, mock_anthropic):
        """Test handling of malformed JSON responses that need regex extraction."""
        # Set up mock with malformed JSON
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Malformed JSON that would fail normal parsing but should be extractable with regex
        mock_content = MagicMock()
        mock_content.text = """
        {
            "score": 8,
            "feedback": "Good work, but needs improvement",
            "improvement_suggestions": [
                "Add more examples",
                "Discuss limitations"
                "Fix grammar issues"  # Missing comma
            ]
        }
        """
        
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        
        mock_client.messages.create.return_value = mock_response
        
        # Test data
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering is the application of engineering principles to software development.",
            question_text="What is software engineering?"
        )
        
        # Test regex fallback
        grader = AIGrader(api_key="test_key")
        result = grader.grade_submission(submission)
        
        # Verify regex extraction worked
        assert isinstance(result, GradedSubmission)
        assert result.score == 8
        assert "Good work" in result.feedback
        assert len(result.improvement_suggestions) > 0
    
    @patch('anthropic.Anthropic')
    def test_grade_submission_with_addressed_questions(self, mock_anthropic):
        """Test grading with addressed questions."""
        # Set up mock response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        mock_content = MagicMock()
        mock_content.text = json.dumps({
            "score": 10,
            "feedback": "Good work",
            "improvement_suggestions": ["Add more examples"],
            "addressed_questions": {
                "question1": True,
                "question2": False
            }
        })
        
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        
        mock_client.messages.create.return_value = mock_response
        
        # Create test data
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering is the application of engineering principles to software development.",
            question_text="What is software engineering?"
        )
        
        criteria = GradingCriteria(
            criteria_list=["Understanding", "Clarity"],
            check_addressed_questions=True,
            question_keys={"question1": "First question", "question2": "Second question"}
        )
        
        # Test grading
        grader = AIGrader(api_key="test_key")
        result = grader.grade_submission(submission, criteria)
        
        # Verify result includes addressed questions
        assert isinstance(result, GradedSubmission)
        assert result.addressed_questions["question1"] is True
        assert result.addressed_questions["question2"] is False
    
    @patch('anthropic.Anthropic')
    def test_generate_prompts(self, mock_anthropic):
        """Test prompt generation."""
        # Set up mock to avoid actual API calls
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Set up test data
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering is the application of engineering principles to software development.",
            question_text="What is software engineering?"
        )
        
        criteria = GradingCriteria(
            criteria_list=["Understanding", "Clarity"],
            min_words=300,
            total_points=10
        )
        
        # Create grader and extract prompts using the protected method
        grader = AIGrader(api_key="test_key")
        system_prompt, user_prompt = grader._generate_prompts(submission, criteria)
        
        # Verify prompts
        assert "expert instructor" in system_prompt
        assert "Grade this student's discussion response" in user_prompt
        assert "What is software engineering?" in user_prompt
        assert "Understanding" in user_prompt
        assert "Clarity" in user_prompt
        assert "300 words" in user_prompt
        assert "10 points" in user_prompt
