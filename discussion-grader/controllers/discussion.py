"""
Discussion controller for the Discussion Grader.

This module provides controller functions to bridge between the CLI and
library layers for discussion operations.
"""

import os
import json
import csv
import io
from typing import Dict, List, Any, Optional, Union
from tabulate import tabulate
from lib.discussion import DiscussionManager, Discussion


class DiscussionController:
    """
    Controller for discussion operations.
    
    This class provides a bridge between the CLI and library layer,
    with additional formatting capabilities for different output types.
    """
    
    def __init__(self, base_dir: str = "discussions"):
        """
        Initialize the DiscussionController.
        
        Args:
            base_dir: Directory where discussions are stored
        """
        self.discussion_manager = DiscussionManager(base_dir)
    
    def create(self, title: str, points: int = 12, min_words: int = 300, 
               question_content: Optional[str] = None, format_type: str = 'text') -> str:
        """
        Create a new discussion.
        
        Args:
            title: Title of the discussion
            points: Total points for the discussion
            min_words: Minimum word count for submissions
            question_content: Optional content for the question file
            format_type: Output format (text, json, csv)
            
        Returns:
            Formatted output indicating the result of the operation
        """
        try:
            discussion_id = self.discussion_manager.create_discussion(
                title=title,
                points=points, 
                min_words=min_words,
                question_content=question_content
            )
            
            discussion = self.discussion_manager.get_discussion(discussion_id)
            
            if format_type.lower() == 'json':
                return self._format_as_json([discussion])
            elif format_type.lower() == 'csv':
                return self._format_as_csv([discussion])
            else:
                return f"Discussion created successfully with ID: {discussion_id}\n\n" + \
                       f"Title: {title}\n" + \
                       f"Points: {points}\n" + \
                       f"Minimum Words: {min_words}\n" + \
                       (f"Question file: Created with {len(question_content)} characters" if question_content else "Question file: Created (empty)")
        except Exception as e:
            return f"Error creating discussion: {str(e)}"
    
    def list(self, format_type: str = 'table') -> str:
        """
        List all discussions.
        
        Args:
            format_type: Output format (table, json, csv)
            
        Returns:
            Formatted list of discussions
        """
        try:
            discussions = self.discussion_manager.list_discussions()
            
            if not discussions:
                return "No discussions found."
            
            if format_type.lower() == 'json':
                return self._format_as_json(discussions)
            elif format_type.lower() == 'csv':
                return self._format_as_csv(discussions)
            else:  # default to table
                return self._format_as_table(discussions)
        except Exception as e:
            return f"Error listing discussions: {str(e)}"
    
    def show(self, discussion_id: int, format_type: str = 'text') -> str:
        """
        Show details for a specific discussion.
        
        Args:
            discussion_id: ID of the discussion to show
            format_type: Output format (text, json, csv)
            
        Returns:
            Formatted discussion details
        """
        try:
            discussion = self.discussion_manager.get_discussion(discussion_id)
            
            if format_type.lower() == 'json':
                return self._format_as_json([discussion])
            elif format_type.lower() == 'csv':
                return self._format_as_csv([discussion])
            else:
                # Format as text
                result = (
                    f"Discussion ID: {discussion.id}\n"
                    f"Title: {discussion.title}\n"
                    f"Points: {discussion.points}\n"
                    f"Minimum Words: {discussion.min_words}\n"
                    f"Created: {discussion.created_at}\n"
                    f"Updated: {discussion.updated_at}\n\n"
                    f"Question Content:\n{'-' * 40}\n{discussion.question_content}\n{'-' * 40}"
                )
                return result
        except FileNotFoundError:
            return f"Error: Discussion {discussion_id} not found."
        except Exception as e:
            return f"Error showing discussion: {str(e)}"
    
    def update(self, discussion_id: int, title: Optional[str] = None, 
               points: Optional[int] = None, min_words: Optional[int] = None,
               question_content: Optional[str] = None, format_type: str = 'text') -> str:
        """
        Update a discussion.
        
        Args:
            discussion_id: ID of the discussion to update
            title: New title (optional)
            points: New points (optional)
            min_words: New minimum words (optional)
            question_content: New question content (optional)
            format_type: Output format (text, json, csv)
            
        Returns:
            Formatted output indicating the result of the operation
        """
        try:
            # Prepare update kwargs
            update_kwargs = {}
            if title is not None:
                update_kwargs['title'] = title
            if points is not None:
                update_kwargs['points'] = points
            if min_words is not None:
                update_kwargs['min_words'] = min_words
            if question_content is not None:
                update_kwargs['question_content'] = question_content
            
            if not update_kwargs:
                return "Error: No update parameters provided."
            
            # Update the discussion
            updated = self.discussion_manager.update_discussion(
                discussion_id=discussion_id,
                **update_kwargs
            )
            
            if format_type.lower() == 'json':
                return self._format_as_json([updated])
            elif format_type.lower() == 'csv':
                return self._format_as_csv([updated])
            else:
                changes = []
                if 'title' in update_kwargs:
                    changes.append(f"Title → {title}")
                if 'points' in update_kwargs:
                    changes.append(f"Points → {points}")
                if 'min_words' in update_kwargs:
                    changes.append(f"Minimum Words → {min_words}")
                if 'question_content' in update_kwargs:
                    changes.append(f"Question Content → Updated ({len(question_content)} characters)")
                
                return f"Discussion {discussion_id} updated successfully.\n\n" + \
                       f"Changes:\n- " + "\n- ".join(changes)
        except FileNotFoundError:
            return f"Error: Discussion {discussion_id} not found."
        except Exception as e:
            return f"Error updating discussion: {str(e)}"
    
    def _format_as_table(self, discussions: List[Discussion]) -> str:
        """
        Format discussions as an ASCII table.
        
        Args:
            discussions: List of Discussion objects
            
        Returns:
            Table-formatted string
        """
        headers = ["ID", "Title", "Points", "Min Words", "Created", "Updated"]
        
        # Extract the data for tabulate
        rows = []
        for disc in discussions:
            # Format timestamps to be more readable
            created = disc.created_at.split('T')[0] if 'T' in disc.created_at else disc.created_at
            updated = disc.updated_at.split('T')[0] if 'T' in disc.updated_at else disc.updated_at
            
            rows.append([
                disc.id,
                disc.title,
                disc.points,
                disc.min_words,
                created,
                updated
            ])
        
        return tabulate(rows, headers=headers, tablefmt="grid")
    
    def _format_as_json(self, discussions: List[Discussion]) -> str:
        """
        Format discussions as JSON.
        
        Args:
            discussions: List of Discussion objects
            
        Returns:
            JSON-formatted string
        """
        # Convert each discussion to a dictionary
        result = [disc.to_dict() for disc in discussions]
        
        # Add question_content back if available
        for i, disc in enumerate(discussions):
            if hasattr(disc, 'question_content') and disc.question_content:
                result[i]['question_content'] = disc.question_content
        
        return json.dumps(result, indent=2)
    
    def _format_as_csv(self, discussions: List[Discussion]) -> str:
        """
        Format discussions as CSV.
        
        Args:
            discussions: List of Discussion objects
            
        Returns:
            CSV-formatted string
        """
        headers = ["id", "title", "points", "min_words", "created_at", "updated_at"]
        
        # Use StringIO for CSV writing
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        for disc in discussions:
            # Convert to dict but only include the fields we want in the CSV
            disc_dict = {
                "id": disc.id,
                "title": disc.title,
                "points": disc.points,
                "min_words": disc.min_words,
                "created_at": disc.created_at,
                "updated_at": disc.updated_at
            }
            writer.writerow(disc_dict)
        
        return output.getvalue()
