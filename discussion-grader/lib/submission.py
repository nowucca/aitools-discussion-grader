"""
Submission models and handling for the grading system.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import os
from datetime import datetime


def read_file(file_path: str) -> str:
    """Read the content of a file."""
    try:
        # Open in binary mode first to handle potential encoding issues
        with open(file_path, 'rb') as file:
            content = file.read()
            
        # Try to decode with utf-8 first
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            # If utf-8 fails, try with latin-1 which can decode any byte sequence
            return content.decode('latin-1')
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")


@dataclass
class Submission:
    """Model representing a student submission to be graded."""
    
    # ID linking to the associated discussion
    discussion_id: int
    
    # The student's submission text
    submission_text: str
    
    # The discussion question text (populated by controller when retrieved)
    question_text: str = ""
    
    # Created timestamp
    submitted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Number of words in the submission (calculated)
    word_count: int = field(init=False)
    
    # Optional ID for the submission (useful for storage/retrieval)
    id: Optional[int] = None
    
    def __post_init__(self):
        """Calculate word count after initialization."""
        self.word_count = len(self.submission_text.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "discussion_id": self.discussion_id,
            "submission_text": self.submission_text,
            "question_text": self.question_text,
            "submitted_at": self.submitted_at,
            "word_count": self.word_count,
            "id": self.id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary representation."""
        return cls(
            discussion_id=data["discussion_id"],
            submission_text=data["submission_text"],
            question_text=data.get("question_text", ""),
            submitted_at=data.get("submitted_at", datetime.now().isoformat()),
            id=data.get("id")
        )
    
    @classmethod
    def from_file(cls, discussion_id: int, file_path: str, question_text: str = ""):
        """Create from a submission file."""
        submission_text = read_file(file_path)
        return cls(
            discussion_id=discussion_id, 
            submission_text=submission_text,
            question_text=question_text
        )


@dataclass
class GradedSubmission:
    """Model representing the result of grading a submission."""
    
    # Score awarded (out of total_points)
    score: float
    
    # Feedback for the student
    feedback: str
    
    # Specific improvement suggestions
    improvement_suggestions: List[str] = field(default_factory=list)
    
    # Which specific questions were addressed (if applicable)
    addressed_questions: Dict[str, bool] = field(default_factory=dict)
    
    # Word count of the submission
    word_count: int = 0
    
    # Whether the submission meets the minimum word count
    meets_word_count: bool = True
    
    # ID for the submission that was graded
    submission_id: Optional[int] = None
    
    # Created timestamp
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "score": self.score,
            "feedback": self.feedback,
            "improvement_suggestions": self.improvement_suggestions.copy(),
            "addressed_questions": self.addressed_questions.copy(),
            "word_count": self.word_count,
            "meets_word_count": self.meets_word_count,
            "submission_id": self.submission_id,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary representation."""
        return cls(
            score=data["score"],
            feedback=data["feedback"],
            improvement_suggestions=data.get("improvement_suggestions", []),
            addressed_questions=data.get("addressed_questions", {}),
            word_count=data.get("word_count", 0),
            meets_word_count=data.get("meets_word_count", True),
            submission_id=data.get("submission_id"),
            created_at=data.get("created_at", datetime.now().isoformat())
        )
    
    def format_report(self, total_points: int = 12) -> str:
        """Format a detailed grading report."""
        report = [
            f"GRADE: {self.score}/{total_points}\n",
            f"WORD COUNT: {self.word_count} words"
        ]
        
        if self.addressed_questions:
            report.append("\nQUESTIONS ADDRESSED:")
            for key, addressed in self.addressed_questions.items():
                report.append(f"- {key}: {'✓' if addressed else '✗'}")
        
        report.append("\nFEEDBACK:")
        report.append(self.feedback)
        
        if self.improvement_suggestions:
            report.append("\nSUGGESTIONS FOR IMPROVEMENT:")
            for suggestion in self.improvement_suggestions:
                report.append(f"- {suggestion}")
        
        return "\n".join(report)
