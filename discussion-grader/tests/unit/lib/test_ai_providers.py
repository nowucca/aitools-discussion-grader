"""
Unit tests for the AI provider system.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from lib.ai_providers import (
    BaseAIProvider,
    AnthropicProvider,
    OpenAIProvider,
    AIProviderConfig,
    create_ai_provider,
    AIProviderError,
    AIProviderConnectionError,
    AIProviderResponseError
)
from lib.submission import Submission, GradedSubmission
from lib.grading import GradingCriteria


class TestAIProviderConfig:
    """Test suite for AIProviderConfig."""
    
    def test_config_creation(self):
        """Test basic configuration creation."""
        config = AIProviderConfig(
            provider_type="anthropic",
            model="claude-3-opus-20240229",
            api_key="test-key",
            temperature=0.5,
            max_tokens=2048
        )
        
        assert config.provider_type == "anthropic"
        assert config.model == "claude-3-opus-20240229"
        assert config.api_key == "test-key"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.base_url is None
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        config = AIProviderConfig(
            provider_type="openai",
            model="gpt-4"
        )
        
        assert config.provider_type == "openai"
        assert config.model == "gpt-4"
        assert config.api_key is None
        assert config.base_url is None
        assert config.temperature == 0
        assert config.max_tokens == 4096


class TestAnthropicProvider:
    """Test suite for AnthropicProvider."""
    
    def test_init_success(self):
        """Test successful initialization."""
        config = AIProviderConfig(
            provider_type="anthropic",
            model="claude-3-opus-20240229",
            api_key="test-key"
        )
        
        provider = AnthropicProvider(config)
        assert provider.config == config
        assert provider.config.model == "claude-3-opus-20240229"
    
    def test_init_missing_api_key(self):
        """Test initialization with missing API key."""
        config = AIProviderConfig(
            provider_type="anthropic",
            model="claude-3-opus-20240229"
        )
        
        with pytest.raises(AIProviderError, match="Anthropic API key is required"):
            AnthropicProvider(config)
    
    def test_init_missing_model_uses_default(self):
        """Test initialization without model uses default."""
        config = AIProviderConfig(
            provider_type="anthropic",
            model="",
            api_key="test-key"
        )
        
        provider = AnthropicProvider(config)
        assert provider.config.model == "claude-3-opus-20240229"
    
    @patch('anthropic.Anthropic')
    def test_grade_submission_success(self, mock_anthropic):
        """Test successful submission grading."""
        # Set up mock response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        mock_content = MagicMock()
        mock_content.text = json.dumps({
            "score": 8,
            "feedback": "Good work with clear explanations",
            "improvement_suggestions": ["Add more examples", "Discuss limitations"],
            "addressed_questions": {"q1": True, "q2": False},
            "word_count": 150
        })
        
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        
        # Create test data
        config = AIProviderConfig(
            provider_type="anthropic",
            model="claude-3-opus-20240229",
            api_key="test-key"
        )
        
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering involves applying engineering principles to software development.",
            question_text="What is software engineering?"
        )
        
        criteria = GradingCriteria.default_criteria()
        
        # Test grading
        provider = AnthropicProvider(config)
        result = provider.grade_submission(submission, criteria)
        
        # Verify result
        assert isinstance(result, GradedSubmission)
        assert result.score == 8
        assert result.feedback == "Good work with clear explanations"
        assert "Add more examples" in result.improvement_suggestions
        assert result.addressed_questions["q1"] is True
        assert result.addressed_questions["q2"] is False
        assert result.word_count == submission.word_count
        
        # Verify API call was made correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args[1]['model'] == "claude-3-opus-20240229"
        assert call_args[1]['temperature'] == 0
        assert call_args[1]['max_tokens'] == 4096
    
    @patch('anthropic.Anthropic')
    def test_grade_submission_api_error(self, mock_anthropic):
        """Test handling of API errors."""
        import anthropic
        
        # Set up mock to raise an error
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_request = MagicMock()
        mock_body = {"error": "rate limit exceeded"}
        mock_client.messages.create.side_effect = anthropic.APIError(
            "Rate limit exceeded", 
            request=mock_request, 
            body=mock_body
        )
        
        # Test data
        config = AIProviderConfig(
            provider_type="anthropic",
            model="claude-3-opus-20240229",
            api_key="test-key"
        )
        
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering test submission.",
            question_text="What is software engineering?"
        )
        
        criteria = GradingCriteria.default_criteria()
        
        # Test error handling
        provider = AnthropicProvider(config)
        with pytest.raises(AIProviderConnectionError, match="Anthropic API error"):
            provider.grade_submission(submission, criteria)


class TestOpenAIProvider:
    """Test suite for OpenAIProvider."""
    
    def test_init_success(self):
        """Test successful initialization."""
        config = AIProviderConfig(
            provider_type="openai",
            model="gpt-4",
            api_key="test-key",
            base_url="https://api.openai.com/v1"
        )
        
        provider = OpenAIProvider(config)
        assert provider.config == config
        assert provider.config.model == "gpt-4"
        assert provider.config.base_url == "https://api.openai.com/v1"
    
    def test_init_missing_api_key(self):
        """Test initialization with missing API key."""
        config = AIProviderConfig(
            provider_type="openai",
            model="gpt-4"
        )
        
        with pytest.raises(AIProviderError, match="OpenAI API key is required"):
            OpenAIProvider(config)
    
    def test_init_defaults(self):
        """Test initialization with defaults."""
        config = AIProviderConfig(
            provider_type="openai",
            model="",
            api_key="test-key"
        )
        
        provider = OpenAIProvider(config)
        assert provider.config.model == "gpt-4"
        assert provider.config.base_url == "https://api.openai.com/v1"
    
    @patch('openai.OpenAI')
    def test_grade_submission_success(self, mock_openai):
        """Test successful submission grading."""
        # Set up mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "score": 7,
            "feedback": "Solid understanding demonstrated",
            "improvement_suggestions": ["Include more examples", "Discuss trade-offs"],
            "word_count": 120
        })
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create test data
        config = AIProviderConfig(
            provider_type="openai",
            model="gpt-4",
            api_key="test-key",
            base_url="https://api.openai.com/v1"
        )
        
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering involves systematic approaches to software development.",
            question_text="What is software engineering?"
        )
        
        criteria = GradingCriteria.default_criteria()
        
        # Test grading
        provider = OpenAIProvider(config)
        result = provider.grade_submission(submission, criteria)
        
        # Verify result
        assert isinstance(result, GradedSubmission)
        assert result.score == 7
        assert result.feedback == "Solid understanding demonstrated"
        assert "Include more examples" in result.improvement_suggestions
        assert result.word_count == submission.word_count
        
        # Verify API call was made correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4"
        assert call_args[1]['temperature'] == 0
        assert call_args[1]['max_tokens'] == 4096
    
    @patch('openai.OpenAI')
    def test_grade_submission_with_custom_base_url(self, mock_openai):
        """Test grading with custom base URL."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Set up mock response to avoid actual grading logic
        mock_message = MagicMock()
        mock_message.content = '{"score": 8, "feedback": "Good work", "improvement_suggestions": []}'
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        config = AIProviderConfig(
            provider_type="openai",
            model="llama-3",
            api_key="test-key",
            base_url="https://api.together.xyz/v1"
        )
        
        provider = OpenAIProvider(config)
        
        # Create a test submission to trigger client creation
        submission = Submission(
            discussion_id=1,
            submission_text="Test submission",
            question_text="Test question?"
        )
        
        criteria = GradingCriteria.default_criteria()
        
        # Call grade_submission to trigger client creation
        provider.grade_submission(submission, criteria)
        
        # Verify client was created with custom base_url
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.together.xyz/v1"
        )
    
    @patch('openai.OpenAI')
    def test_grade_submission_api_error(self, mock_openai):
        """Test handling of API errors."""
        import openai
        
        # Set up mock to raise an error
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create a proper APIError with required parameters
        mock_request = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APIError(
            "Invalid request", 
            request=mock_request, 
            body=None
        )
        
        # Test data
        config = AIProviderConfig(
            provider_type="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        submission = Submission(
            discussion_id=1,
            submission_text="Test submission.",
            question_text="Test question?"
        )
        
        criteria = GradingCriteria.default_criteria()
        
        # Test error handling
        provider = OpenAIProvider(config)
        with pytest.raises(AIProviderConnectionError, match="OpenAI API error"):
            provider.grade_submission(submission, criteria)


class TestCreateAIProvider:
    """Test suite for the provider factory function."""
    
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        config = AIProviderConfig(
            provider_type="anthropic",
            model="claude-3-opus-20240229",
            api_key="test-key"
        )
        
        provider = create_ai_provider("anthropic", config)
        assert isinstance(provider, AnthropicProvider)
        assert provider.config == config
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        config = AIProviderConfig(
            provider_type="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        provider = create_ai_provider("openai", config)
        assert isinstance(provider, OpenAIProvider)
        assert provider.config == config
    
    def test_create_provider_case_insensitive(self):
        """Test provider creation is case insensitive."""
        config = AIProviderConfig(
            provider_type="ANTHROPIC",
            model="claude-3-opus-20240229",
            api_key="test-key"
        )
        
        provider = create_ai_provider("ANTHROPIC", config)
        assert isinstance(provider, AnthropicProvider)
    
    def test_create_unsupported_provider(self):
        """Test creating unsupported provider type."""
        config = AIProviderConfig(
            provider_type="unsupported",
            model="test-model",
            api_key="test-key"
        )
        
        with pytest.raises(AIProviderError, match="Unsupported provider type: unsupported"):
            create_ai_provider("unsupported", config)


class TestBaseProviderSharedFunctionality:
    """Test shared functionality across providers."""
    
    @patch('anthropic.Anthropic')
    def test_prompt_generation_consistent(self, mock_anthropic):
        """Test that prompt generation is consistent across providers."""
        # Set up mock to avoid actual API calls
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Test data
        submission = Submission(
            discussion_id=1,
            submission_text="Software engineering is important for building reliable systems.",
            question_text="Discuss the importance of software engineering."
        )
        
        criteria = GradingCriteria(
            criteria_list=["Understanding", "Clarity", "Examples"],
            min_words=100,
            total_points=10
        )
        
        # Test Anthropic provider prompt generation
        config = AIProviderConfig(
            provider_type="anthropic",
            model="claude-3-opus-20240229",
            api_key="test-key"
        )
        
        provider = AnthropicProvider(config)
        system_prompt, user_prompt = provider._generate_prompts(submission, criteria)
        
        # Verify prompt content
        assert "expert instructor" in system_prompt
        assert "Grade this student's discussion response" in user_prompt
        assert "Discuss the importance of software engineering." in user_prompt
        assert "Understanding" in user_prompt
        assert "Clarity" in user_prompt
        assert "Examples" in user_prompt
        assert "100 words" in user_prompt
        assert "10 points" in user_prompt
    
    @pytest.mark.parametrize("provider_class,config_type", [
        (AnthropicProvider, "anthropic"),
        (OpenAIProvider, "openai")
    ])
    def test_json_parsing_consistent(self, provider_class, config_type):
        """Test that JSON parsing works consistently across providers."""
        config = AIProviderConfig(
            provider_type=config_type,
            model="test-model",
            api_key="test-key"
        )
        
        provider = provider_class(config)
        
        # Test valid JSON
        valid_json = '{"score": 8, "feedback": "Good work", "improvement_suggestions": ["More examples"]}'
        result = provider._parse_response_json(valid_json)
        
        assert result["score"] == 8
        assert result["feedback"] == "Good work"
        assert result["improvement_suggestions"] == ["More examples"]
        
        # Test malformed JSON that should trigger regex fallback
        malformed_json = '{"score": 7, "feedback": "Needs work", "improvement_suggestions": ["Fix errors", "Add details"]}'
        result = provider._parse_response_json(malformed_json)
        
        assert result["score"] == 7
        assert "Needs work" in result["feedback"]
