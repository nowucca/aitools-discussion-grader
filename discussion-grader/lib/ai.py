"""
AI Integration for the Grading System

This module provides the AI grading functionality used to evaluate student
submissions based on provided criteria. Now supports multiple AI providers
including Anthropic Claude and OpenAI API-compatible services.
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in the project root (two levels up from this file)
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not available, skip loading
    pass

# Import the models
from .submission import Submission, GradedSubmission
from .grading import GradingCriteria
from .ai_providers import (
    BaseAIProvider, 
    AIProviderConfig, 
    create_ai_provider,
    AIProviderError,
    AIProviderConnectionError,
    AIProviderResponseError
)


class AIError(Exception):
    """Base exception for AI-related errors."""
    pass


class AIConnectionError(AIError):
    """Raised when there is an error connecting to the AI API."""
    pass


class AIResponseError(AIError):
    """Raised when there is an error in the AI response."""
    pass


class AIGrader:
    """
    Handles interactions with AI providers for grading and synthesis.
    
    This class provides methods for grading student submissions using
    various AI providers (Anthropic, OpenAI, etc.) with robust error 
    handling and response parsing.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 provider_type: Optional[str] = None,
                 model: Optional[str] = None,
                 base_url: Optional[str] = None,
                 config_file: Optional[str] = None):
        """
        Initialize the AI grader with provider configuration.
        
        Args:
            api_key: API key for the provider. If None, read from environment.
            provider_type: AI provider type ("anthropic" or "openai"). 
                         If None, defaults to "anthropic" for backward compatibility.
            model: Model name to use. If None, uses provider defaults.
            base_url: Base URL for OpenAI-compatible APIs.
            config_file: Path to configuration file for AI settings.
        """
        # Load configuration from file if provided
        file_config = self._load_config_file(config_file) if config_file else {}
        ai_config = file_config.get('ai', {})
        
        # Determine provider type
        self.provider_type = (provider_type or 
                             ai_config.get('provider') or 
                             os.environ.get('AI_PROVIDER') or 
                             'anthropic')
        
        # Get provider-specific configuration
        provider_config = ai_config.get(self.provider_type, {})
        
        # Determine API key based on provider
        if not api_key:
            if self.provider_type == 'anthropic':
                api_key = os.environ.get('ANTHROPIC_API_KEY')
            elif self.provider_type == 'openai':
                api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            provider_env_var = f"{self.provider_type.upper()}_API_KEY"
            raise ValueError(f"{self.provider_type.title()} API key is required. "
                           f"Set the {provider_env_var} environment variable or pass api_key parameter.")
        
        # Create provider configuration
        config = AIProviderConfig(
            provider_type=self.provider_type,
            model=model or provider_config.get('model') or '',
            api_key=api_key,
            base_url=base_url or provider_config.get('base_url') or os.environ.get('OPENAI_BASE_URL'),
            temperature=provider_config.get('temperature', 0),
            max_tokens=provider_config.get('max_tokens', 4096)
        )
        
        # Create the AI provider
        try:
            self.provider = create_ai_provider(self.provider_type, config)
        except AIProviderError as e:
            raise AIError(f"Failed to initialize AI provider: {str(e)}")
    
    def _load_config_file(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise AIError(f"Failed to load configuration file {config_file}: {str(e)}")
    
    def grade_submission(self, submission: Submission, criteria: Optional[GradingCriteria] = None) -> GradedSubmission:
        """
        Grade a submission using the configured AI provider.
        
        Args:
            submission: The Submission object containing question and submission text
            criteria: Optional GradingCriteria to use (defaults to default criteria)
            
        Returns:
            GradedSubmission: A fully typed grading result
            
        Raises:
            AIConnectionError: When connection to API fails
            AIResponseError: When response cannot be parsed
        """
        try:
            # Use default criteria if none provided
            if criteria is None:
                criteria = GradingCriteria.default_criteria()
            
            # Delegate to the provider
            return self.provider.grade_submission(submission, criteria)
            
        except AIProviderConnectionError as e:
            raise AIConnectionError(str(e))
        except AIProviderResponseError as e:
            raise AIResponseError(str(e))
        except AIProviderError as e:
            raise AIError(str(e))
        except Exception as e:
            raise AIError(f"Error grading submission: {str(e)}")
    
    def synthesize_submissions(self, question: str, submissions: List[str], max_submissions: int = 50) -> str:
        """
        Synthesize multiple student submissions into a comprehensive response.
        
        Args:
            question: The discussion question
            submissions: List of student submission texts
            max_submissions: Maximum number of submissions to include
            
        Returns:
            Synthesized content as a string
        """
        # Placeholder for actual implementation
        # This would be implemented in a future phase
        return "Synthesis functionality not yet implemented"
