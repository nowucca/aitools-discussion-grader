"""
AI Integration for the Grading System

This module provides the AI grading functionality used to evaluate student
submissions based on provided criteria.
"""

import os
import json
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple

# Import the models
from .submission import Submission, GradedSubmission
from .grading import GradingCriteria


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
    Handles interactions with the Claude API for grading and synthesis.
    
    This class provides methods for grading student submissions using the
    Anthropic Claude API, with robust error handling and response parsing.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI grader.
        
        Args:
            api_key: Anthropic API key. If None, read from environment.
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set the ANTHROPIC_API_KEY environment variable.")
    
    def grade_submission(self, submission: Submission, criteria: Optional[GradingCriteria] = None) -> GradedSubmission:
        """
        Grade a submission using the Claude API with strong type checking.
        
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
            # Import here to avoid requiring the package for non-AI operations
            import anthropic
            
            # Use default criteria if none provided
            if criteria is None:
                criteria = GradingCriteria.default_criteria()
            
            # Create the client
            client = self._get_client()
            
            # Generate prompts
            system_prompt, user_prompt = self._generate_prompts(
                submission=submission,
                criteria=criteria
            )
            
            # Call the API
            response = self._call_api(client, system_prompt, user_prompt)
            
            # Parse the response
            result = self._parse_response(response)
            
            # Create and return GradedSubmission
            return GradedSubmission(
                score=float(result.get("score", 0)),
                feedback=result.get("feedback", "No feedback provided"),
                improvement_suggestions=result.get("improvement_suggestions", []),
                addressed_questions=result.get("addressed_questions", {}),
                word_count=submission.word_count,
                meets_word_count=submission.word_count >= criteria.min_words
            )
                
        except anthropic.APIError as e:
            raise AIConnectionError(f"API error: {str(e)}")
        except json.JSONDecodeError as e:
            raise AIResponseError(f"Failed to parse response JSON: {str(e)}")
        except AIResponseError:
            # Re-raise AIResponseError directly to preserve the specific error type
            raise
        except Exception as e:
            raise AIError(f"Error grading submission: {str(e)}")

    def _get_client(self):
        """Create and return an Anthropic client."""
        import anthropic
        return anthropic.Anthropic(api_key=self.api_key)
    
    def _generate_prompts(self, submission: Submission, criteria: GradingCriteria) -> Tuple[str, str]:
        """
        Generate system and user prompts for grading.
        
        Args:
            submission: The Submission object containing question_text and submission_text
            criteria: The GradingCriteria object
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # System prompt with clear instructions - adapted from grade_with_claude() in grade_discussion.py
        system_prompt = (
            "You are an expert instructor grading computer science discussions. "
            "Write feedback and grading reasoning directly to the student in a clear, "
            "professional tone. Be concise but constructive. Grade fairly and provide "
            "specific feedback without being overly verbose. Avoid using phrases like "
            "'the student' and prefer to use 'you' instead. The feedback should be "
            "constructive and actionable, helping the student understand how to improve."
        )
        
        # Build criteria string
        criteria_str = "\n".join(f"- {criterion}" for criterion in criteria.criteria_list)
        
        # Build addressed_questions JSON if needed
        addressed_questions_json = ""
        if criteria.check_addressed_questions and criteria.question_keys:
            addressed_questions_json = """
            "addressed_questions": {
            """
            
            for key, description in criteria.question_keys.items():
                addressed_questions_json += f'    "{key}": true/false, // {description}\n'
            
            addressed_questions_json += """
            },"""
        
        # Determine if this is likely a software engineering question based on keywords
        is_software_eng = any(keyword in submission.question_text.lower() 
                             for keyword in ["software engineering", "software development", 
                                           "coding practices", "programming paradigm"])
        
        # User prompt with all requirements - adapted from grade_with_claude() in grade_discussion.py
        user_prompt = f"""
        Grade this student's discussion response:
        
        Question:
        {submission.question_text}
        
        Student Submission:
        {submission.submission_text}
        
        Please grade this submission out of {criteria.total_points} points.
        Evaluate based on these criteria:
        {criteria_str}
        
        The submission should be at least {criteria.min_words} words. Current word count: {submission.word_count} words.
        Consider this in your grading.
        
        {"Please pay special attention to the student's understanding of software engineering concepts and their ability to apply these concepts to practical scenarios." if is_software_eng else ""}
        
        IMPORTANT GRADING REQUIREMENT: If you deduct any points (giving less than {criteria.total_points} points), you MUST clearly justify the deduction in your feedback. Explain specifically what was missing, insufficient, or incorrect that led to the point reduction. Be constructive and specific about what the student needs to improve.
        
        Provide your response in JSON format like this:
        {{
            "score": [numeric score out of {criteria.total_points}],
            "feedback": "[1-2 paragraph summary of strengths and weaknesses, with clear justification for any point deductions]",
            "improvement_suggestions": [
                "specific suggestion 1",
                "specific suggestion 2",
                "specific suggestion 3"
            ],{addressed_questions_json}
            "word_count": {submission.word_count}
        }}
        
        ONLY return the JSON, no other text.
        """
        
        return system_prompt, user_prompt
    
    def _call_api(self, client, system_prompt: str, user_prompt: str) -> Any:
        """
        Call the Claude API and return the response.
        
        Args:
            client: Anthropic client
            system_prompt: System prompt string
            user_prompt: User prompt string
            
        Returns:
            API response object
        """
        return client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """
        Parse the API response with robust error handling.
        
        Args:
            response: API response object
            
        Returns:
            Dict containing parsed response
            
        Raises:
            AIResponseError: When response cannot be parsed
        """
        response_text = response.content[0].text
        
        # Find JSON in the response (it might be wrapped in markdown code blocks)
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                # First try to load the JSON as is
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try multiple fallback strategies
                try:
                    # Clean control characters
                    cleaned_json = re.sub(r'[\x00-\x1F]', lambda m: f"\\u{ord(m.group(0)):04x}", json_str)
                    return json.loads(cleaned_json)
                except json.JSONDecodeError:
                    # Try regex extraction as a last resort
                    return self._extract_fields_with_regex(json_str)
        
        raise AIResponseError("Could not find valid JSON in the API response")
    
    def _extract_fields_with_regex(self, json_str: str) -> Dict[str, Any]:
        """
        Extract JSON fields using regex as a last resort.
        
        Args:
            json_str: JSON string that failed to parse
            
        Returns:
            Dict containing extracted fields
        """
        try:
            # Extract score
            score_match = re.search(r'"score"\s*:\s*(\d+(?:\.\d+)?)', json_str)
            score = float(score_match.group(1)) if score_match else 0
            
            # Extract feedback
            feedback_match = re.search(r'"feedback"\s*:\s*"([^"]*(?:"[^"]*"[^"]*)*)"', json_str)
            feedback = feedback_match.group(1) if feedback_match else "Error extracting feedback"
            
            # Extract improvement suggestions
            suggestions = []
            suggestions_match = re.search(r'"improvement_suggestions"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
            if suggestions_match:
                suggestions_str = suggestions_match.group(1)
                # Extract quoted strings from the array
                suggestion_matches = re.finditer(r'"(.*?)"', suggestions_str)
                suggestions = [m.group(1) for m in suggestion_matches]
            
            # Extract addressed questions if present
            addressed = {}
            for key in json_str.split('"addressed_questions"')[1:]:
                key_matches = re.finditer(r'"([^"]+)"\s*:\s*(true|false)', key)
                for m in key_matches:
                    addressed[m.group(1)] = m.group(2).lower() == "true"
            
            return {
                "score": score,
                "feedback": feedback,
                "improvement_suggestions": suggestions,
                "addressed_questions": addressed
            }
        except Exception as e:
            raise AIResponseError(f"Failed to extract fields with regex: {str(e)}")
    
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
