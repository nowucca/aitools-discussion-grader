"""
Grading criteria and related models for the grading system.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .discussion import Discussion


@dataclass
class GradingCriteria:
    """Model representing criteria for grading submissions."""
    
    # List of specific grading criteria (e.g., "Addressing all parts of the question")
    criteria_list: List[str] = field(default_factory=list)
    
    # Minimum word count requirement
    min_words: int = 300
    
    # Whether to check if specific questions were addressed
    check_addressed_questions: bool = False
    
    # Dictionary of question keys to look for in the submission
    question_keys: Dict[str, str] = field(default_factory=dict)
    
    # Total points available
    total_points: int = 12
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "criteria_list": self.criteria_list.copy(),
            "min_words": self.min_words,
            "check_addressed_questions": self.check_addressed_questions,
            "question_keys": self.question_keys.copy(),
            "total_points": self.total_points
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary representation."""
        return cls(
            criteria_list=data.get("criteria_list", []),
            min_words=data.get("min_words", 300),
            check_addressed_questions=data.get("check_addressed_questions", False),
            question_keys=data.get("question_keys", {}),
            total_points=data.get("total_points", 12)
        )
    
    @classmethod
    def from_discussion(cls, discussion: Discussion, 
                       criteria_list: Optional[List[str]] = None,
                       question_keys: Optional[Dict[str, str]] = None):
        """Create criteria from a Discussion object."""
        # Use default criteria if none provided
        if criteria_list is None:
            criteria_list = [
                "Understanding of the topic",
                "Clarity of explanation",
                "Use of specific examples",
                "Depth of analysis"
            ]
            
        # Create criteria from discussion metadata
        return cls(
            criteria_list=criteria_list,
            min_words=discussion.min_words,
            check_addressed_questions=bool(question_keys),
            question_keys=question_keys or {},
            total_points=discussion.points
        )
    
    @classmethod
    def default_criteria(cls):
        """Create default grading criteria."""
        return cls(
            criteria_list=[
                "Understanding of the topic",
                "Clarity of explanation",
                "Use of specific examples",
                "Depth of analysis"
            ],
            min_words=300,
            total_points=12
        )
