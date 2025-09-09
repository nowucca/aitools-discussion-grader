"""
Discussion management module for the Discussion Grader.

This module provides functionality to create, retrieve, list, and update
discussions within the system.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict


@dataclass
class Discussion:
    """
    Represents a discussion in the system.
    
    This class encapsulates all discussion metadata and content.
    """
    id: int
    title: str
    points: int = 12
    min_words: int = 300
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    question_file: str = "question.md"
    question_content: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Discussion object to a dictionary.
        
        Returns:
            Dict: Dictionary representation of the discussion
        """
        # Create a copy to avoid modifying the original
        result = asdict(self)
        
        # Remove question_content from serialization to metadata file
        if "question_content" in result:
            del result["question_content"]
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Discussion':
        """
        Create a Discussion object from a dictionary.
        
        Args:
            data: Dictionary containing discussion data
            
        Returns:
            Discussion: New Discussion object
        """
        # Make a copy to avoid modifying the original
        data_copy = data.copy()
        
        # Handle question_content if it's not in the data
        if "question_content" not in data_copy:
            data_copy["question_content"] = ""
            
        return cls(**data_copy)


class DiscussionManager:
    """
    Manages discussions for the Discussion Grader system.
    
    This class handles all operations related to discussions, including
    creation, retrieval, listing, and updates.
    """
    
    def __init__(self, base_dir: str = "discussions"):
        """
        Initialize the DiscussionManager.
        
        Args:
            base_dir: Directory where discussions are stored
        """
        self.base_dir = Path(base_dir)
        # Ensure the base directory exists
        os.makedirs(self.base_dir, exist_ok=True)
    
    def create_discussion(self, title: str, points: int = 12, min_words: int = 300, 
                          question_content: Optional[str] = None) -> int:
        """
        Create a new discussion.
        
        Args:
            title: Title of the discussion
            points: Total points for the discussion
            min_words: Minimum word count for submissions
            question_content: Optional content for the question file
            
        Returns:
            int: The ID of the newly created discussion
        """
        # Generate a new discussion ID
        discussion_id = self._generate_id()
        
        # Create directory for the discussion
        discussion_dir = self.base_dir / f"discussion_{discussion_id}"
        submissions_dir = discussion_dir / "submissions"
        
        os.makedirs(discussion_dir, exist_ok=True)
        os.makedirs(submissions_dir, exist_ok=True)
        
        # Create discussion object
        discussion = Discussion(
            id=discussion_id,
            title=title,
            points=points,
            min_words=min_words,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            question_file="question.md"
        )
        
        # Write metadata
        self._write_file(
            discussion_dir / "metadata.json", 
            json.dumps(discussion.to_dict(), indent=2)
        )
        
        # Write question file if provided
        if question_content:
            self._write_file(discussion_dir / "question.md", question_content)
        else:
            # Create an empty question file as a placeholder
            self._write_file(discussion_dir / "question.md", "")
        
        return discussion_id
    
    def get_discussion(self, discussion_id: int) -> Discussion:
        """
        Get a discussion by ID.
        
        Args:
            discussion_id: The ID of the discussion to retrieve
            
        Returns:
            Discussion: The discussion object
            
        Raises:
            FileNotFoundError: If the discussion doesn't exist
        """
        discussion_dir = self.base_dir / f"discussion_{discussion_id}"
        
        if not discussion_dir.exists():
            raise FileNotFoundError(f"Discussion {discussion_id} not found")
        
        # Read metadata
        metadata = json.loads(self._read_file(discussion_dir / "metadata.json"))
        
        # Get question content
        question_file = discussion_dir / metadata["question_file"]
        question_content = ""
        if question_file.exists():
            question_content = self._read_file(question_file)
            
        # Add question content to metadata and create Discussion object
        metadata["question_content"] = question_content
        
        return Discussion.from_dict(metadata)
    
    def list_discussions(self) -> List[Discussion]:
        """
        List all discussions.
        
        Returns:
            List[Discussion]: List of discussion objects
        """
        discussions = []
        
        # Find all discussion directories
        for item in self.base_dir.glob("discussion_*"):
            if item.is_dir():
                try:
                    # Extract discussion ID from directory name
                    discussion_id = int(item.name.split("_")[1])
                    
                    # Get metadata (without full question content for efficiency)
                    metadata = json.loads(self._read_file(item / "metadata.json"))
                    discussions.append(Discussion.from_dict(metadata))
                except (ValueError, FileNotFoundError, json.JSONDecodeError):
                    # Skip directories with invalid format or missing metadata
                    continue
        
        # Sort by ID
        discussions.sort(key=lambda x: x.id)
        return discussions
    
    def update_discussion(self, discussion_id: int, **kwargs) -> Discussion:
        """
        Update a discussion.
        
        Args:
            discussion_id: The ID of the discussion to update
            **kwargs: Fields to update
            
        Returns:
            Discussion: The updated discussion object
            
        Raises:
            FileNotFoundError: If the discussion doesn't exist
        """
        discussion_dir = self.base_dir / f"discussion_{discussion_id}"
        
        if not discussion_dir.exists():
            raise FileNotFoundError(f"Discussion {discussion_id} not found")
        
        # Get existing discussion
        discussion = self.get_discussion(discussion_id)
        
        # Special handling for question_content
        question_content = kwargs.pop("question_content", None)
        
        # Update discussion attributes
        if kwargs:
            for key, value in kwargs.items():
                if hasattr(discussion, key):
                    setattr(discussion, key, value)
            
            # Update timestamp
            discussion.updated_at = datetime.now().isoformat()
            
            # Write updated metadata
            metadata_file = discussion_dir / "metadata.json"
            self._write_file(metadata_file, json.dumps(discussion.to_dict(), indent=2))
        
        # Update question content if provided
        if question_content is not None:
            question_file = discussion_dir / discussion.question_file
            self._write_file(question_file, question_content)
        
        # Return updated discussion
        return self.get_discussion(discussion_id)
    
    def _generate_id(self) -> int:
        """
        Generate a new unique discussion ID.
        
        Returns:
            int: A new unique ID
        """
        # List existing discussions
        existing_ids = set()
        for item in self.base_dir.glob("discussion_*"):
            try:
                existing_ids.add(int(item.name.split("_")[1]))
            except (ValueError, IndexError):
                continue
        
        # Find the next available ID
        if not existing_ids:
            return 1
        
        return max(existing_ids) + 1
    
    def _read_file(self, file_path: Union[str, Path]) -> str:
        """
        Read the content of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Content of the file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
            
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
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
    
    def _write_file(self, file_path: Union[str, Path], content: str) -> None:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            
        Raises:
            IOError: If there's an error writing to the file
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
            
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
        except Exception as e:
            raise IOError(f"Error writing to file {file_path}: {e}")
