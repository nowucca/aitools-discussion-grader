"""
Unit tests for the AI grading functionality.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open
from dataclasses import asdict

from lib.ai import AIGrader, AIConnectionError, AIResponseError, AIError
from lib.submission import Submission, GradedSubmission
from lib.grading import GradingCriteria
from lib.ai_providers import AIProviderError


class TestAIGraderInitialization:
    """Test suite for AIGrader initialization."""
    
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_init_anthropic_default(self):
        """Test initialization with Anthropic as default provider."""
        grader = AIGrader()
        assert grader.provider_type == "anthropic"
        assert grader.provider is not None
    
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_init_with_explicit_api_key(self):
        """Test initialization with explicit API key."""
        grader = AIGrader(api_key="explicit_key")
        assert grader.provider_type == "anthropic"
        assert grader.provider.config.api_key == "explicit_key"
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'openai_test_key'})
    def test_init_openai_provider(self):
        """Test initialization with OpenAI provider."""
        grader = AIGrader(provider_type="openai")
        assert grader.provider_type == "openai"
        assert grader.provider is not None
        assert grader.provider.config.api_key == "openai_test_key"
    
    @patch.dict('os.environ', {'AI_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test_key'})
    def test_init_provider_from_env(self):
        """Test initialization with provider type from environment."""
        grader = AIGrader()
        assert grader.provider_type == "openai"
    
    def test_init_missing_key(self):
        """Test initialization with no API key raises appropriate error."""
        with patch.dict('os.environ', clear=True):
            with pytest.raises(ValueError, match="Anthropic API key is required"):
                AIGrader()
    
    def test_init_missing_openai_key(self):
        """Test initialization with OpenAI but no API key."""
        with patch.dict('os.environ', clear=True):
            with pytest.raises(ValueError, match="Openai API key is required"):
                AIGrader(provider_type="openai")
    
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        grader = AIGrader(model="claude-3-sonnet-20240229")
        assert grader.provider.config.model == "claude-3-sonnet-20240229"
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL for OpenAI-compatible API."""
        grader = AIGrader(
            provider_type="openai",
            base_url="https://api.together.xyz/v1"
        )
        assert grader.provider.config.base_url == "https://api.together.xyz/v1"
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"ai": {"provider": "openai", "openai": {"model": "gpt-3.5-turbo"}}}')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_init_with_config_file(self, mock_file):
        """Test initialization with configuration file."""
        grader = AIGrader(config_file="test_config.json")
        assert grader.provider_type == "openai"
        assert grader.provider.config.model == "gpt-3.5-turbo"
    
    def test_init_invalid_config_file(self):
        """Test initialization with invalid config file."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(AIError, match="Failed to load configuration file"):
                AIGrader(config_file="nonexistent.json")
    
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_init_provider_creation_failure(self):
        """Test handling of provider creation failure."""
        with patch('lib.ai.create_ai_provider', side_effect=AIProviderError("Provider error")):
            with pytest.raises(AIError, match="Failed to initialize AI provider"):
                AIGrader()


class TestAIGraderGrading:
    """Test suite for AIGrader grading functionality."""
    
    @patch('lib.ai_providers.AnthropicProvider.grade_submission')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_grade_submission_success(self, mock_grade):
        """Test successful submission grading."""
        # Set up mock response
        expected_result = GradedSubmission(
            score=8.5,
            feedback="Good analysis of the topic",
            improvement_suggestions=["Add more examples", "Discuss edge cases"],
            addressed_questions={"main_concept": True},
            word_count=150,
            meets_word_count=True
        )
        mock_grade.return_value = expected_result
        
        # Create test data
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering is a systematic approach to software development.",
            question_text="What is software engineering?"
        )
        
        criteria = GradingCriteria.default_criteria()
        
        # Test grading
        grader = AIGrader()
        result = grader.grade_submission(submission, criteria)
        
        # Verify result
        assert result == expected_result
        mock_grade.assert_called_once_with(submission, criteria)
    
    @patch('lib.ai_providers.AnthropicProvider.grade_submission')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_grade_submission_with_default_criteria(self, mock_grade):
        """Test grading with default criteria when none provided."""
        expected_result = GradedSubmission(
            score=7.0,
            feedback="Solid work",
            improvement_suggestions=["More detail needed"],
            addressed_questions={},
            word_count=100,
            meets_word_count=True
        )
        mock_grade.return_value = expected_result
        
        submission = Submission(
            discussion_id=1,
            submission_text="Test submission",
            question_text="Test question?"
        )
        
        grader = AIGrader()
        result = grader.grade_submission(submission)  # No criteria provided
        
        # Verify default criteria was used
        mock_grade.assert_called_once()
        call_args = mock_grade.call_args
        assert call_args[0][0] == submission
        assert isinstance(call_args[0][1], GradingCriteria)  # Default criteria used
    
    @patch('lib.ai_providers.AnthropicProvider.grade_submission')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_grade_submission_provider_connection_error(self, mock_grade):
        """Test handling of provider connection errors."""
        from lib.ai_providers import AIProviderConnectionError
        
        mock_grade.side_effect = AIProviderConnectionError("Connection failed")
        
        submission = Submission(
            discussion_id=1,
            submission_text="Test submission",
            question_text="Test question?"
        )
        
        grader = AIGrader()
        with pytest.raises(AIConnectionError, match="Connection failed"):
            grader.grade_submission(submission)
    
    @patch('lib.ai_providers.AnthropicProvider.grade_submission')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_grade_submission_provider_response_error(self, mock_grade):
        """Test handling of provider response errors."""
        from lib.ai_providers import AIProviderResponseError
        
        mock_grade.side_effect = AIProviderResponseError("Invalid response")
        
        submission = Submission(
            discussion_id=1,
            submission_text="Test submission",
            question_text="Test question?"
        )
        
        grader = AIGrader()
        with pytest.raises(AIResponseError, match="Invalid response"):
            grader.grade_submission(submission)
    
    @patch('lib.ai_providers.AnthropicProvider.grade_submission')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_grade_submission_provider_generic_error(self, mock_grade):
        """Test handling of generic provider errors."""
        from lib.ai_providers import AIProviderError
        
        mock_grade.side_effect = AIProviderError("Generic provider error")
        
        submission = Submission(
            discussion_id=1,
            submission_text="Test submission",
            question_text="Test question?"
        )
        
        grader = AIGrader()
        with pytest.raises(AIError, match="Generic provider error"):
            grader.grade_submission(submission)
    
    @patch('lib.ai_providers.AnthropicProvider.grade_submission')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_grade_submission_unexpected_error(self, mock_grade):
        """Test handling of unexpected errors."""
        mock_grade.side_effect = Exception("Unexpected error")
        
        submission = Submission(
            discussion_id=1,
            submission_text="Test submission",
            question_text="Test question?"
        )
        
        grader = AIGrader()
        with pytest.raises(AIError, match="Error grading submission"):
            grader.grade_submission(submission)


class TestAIGraderProviderIntegration:
    """Test suite for AIGrader integration with different providers."""
    
    @patch('lib.ai_providers.AnthropicProvider.grade_submission')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_anthropic_provider_integration(self, mock_grade):
        """Test integration with Anthropic provider."""
        expected_result = GradedSubmission(
            score=9.0,
            feedback="Excellent work",
            improvement_suggestions=[],
            addressed_questions={},
            word_count=200,
            meets_word_count=True
        )
        mock_grade.return_value = expected_result
        
        grader = AIGrader(provider_type="anthropic")
        submission = Submission(
            discussion_id=1,
            submission_text="Excellent submission",
            question_text="Test question?"
        )
        
        result = grader.grade_submission(submission)
        assert result == expected_result
        assert grader.provider_type == "anthropic"
    
    @patch('lib.ai_providers.OpenAIProvider.grade_submission')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_openai_provider_integration(self, mock_grade):
        """Test integration with OpenAI provider."""
        expected_result = GradedSubmission(
            score=8.0,
            feedback="Good work",
            improvement_suggestions=["More examples"],
            addressed_questions={},
            word_count=150,
            meets_word_count=True
        )
        mock_grade.return_value = expected_result
        
        grader = AIGrader(provider_type="openai")
        submission = Submission(
            discussion_id=1,
            submission_text="Good submission",
            question_text="Test question?"
        )
        
        result = grader.grade_submission(submission)
        assert result == expected_result
        assert grader.provider_type == "openai"
    
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'anthropic_key', 'OPENAI_API_KEY': 'openai_key'})
    def test_provider_switching(self):
        """Test that different providers can be used with same interface."""
        # Test Anthropic
        grader_anthropic = AIGrader(provider_type="anthropic")
        assert grader_anthropic.provider_type == "anthropic"
        
        # Test OpenAI
        grader_openai = AIGrader(provider_type="openai")
        assert grader_openai.provider_type == "openai"
        
        # Both should have the same interface
        assert hasattr(grader_anthropic, 'grade_submission')
        assert hasattr(grader_openai, 'grade_submission')
        assert hasattr(grader_anthropic, 'synthesize_submissions')
        assert hasattr(grader_openai, 'synthesize_submissions')


class TestAIGraderBackwardCompatibility:
    """Test suite for backward compatibility."""
    
    @patch('lib.ai_providers.AnthropicProvider.grade_submission')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_legacy_initialization_still_works(self, mock_grade):
        """Test that legacy initialization patterns still work."""
        # This should still work for backward compatibility
        grader = AIGrader(api_key="test_key")
        assert grader.provider_type == "anthropic"
        assert grader.provider.config.api_key == "test_key"
    
    @patch('lib.ai_providers.AnthropicProvider.grade_submission')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_existing_interface_unchanged(self, mock_grade):
        """Test that existing public interface remains unchanged."""
        expected_result = GradedSubmission(
            score=7.5,
            feedback="Good understanding",
            improvement_suggestions=["Add examples"],
            addressed_questions={},
            word_count=120,
            meets_word_count=True
        )
        mock_grade.return_value = expected_result
        
        # Test existing usage pattern
        grader = AIGrader()
        submission = Submission(
            discussion_id=1,
            submission_text="Test submission",
            question_text="Test question?"
        )
        
        # This should work exactly as before
        result = grader.grade_submission(submission)
        assert isinstance(result, GradedSubmission)
        assert result.score == 7.5
    
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_synthesize_submissions_unchanged(self):
        """Test that synthesize_submissions method remains available."""
        grader = AIGrader()
        
        # Method should exist and return placeholder
        result = grader.synthesize_submissions("Test question", ["submission1", "submission2"])
        assert isinstance(result, str)
        assert "not yet implemented" in result
    
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
