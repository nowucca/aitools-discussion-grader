"""
Unit tests for DiscussionManager in lib/discussion.py.
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime
from lib.discussion import DiscussionManager, Discussion

class TestDiscussionManager:
    """Tests for the DiscussionManager class."""
    
    @pytest.fixture
    def discussion_manager(self, tmp_path):
        """Create a discussion manager with a temporary base directory."""
        return DiscussionManager(base_dir=str(tmp_path))
    
    def test_create_discussion(self, discussion_manager, tmp_path):
        """Test creating a new discussion."""
        # Create a discussion
        discussion_id = discussion_manager.create_discussion(
            title="Test Discussion",
            points=10,
            min_words=200,
            question_content="What is the meaning of life?"
        )
        
        # Check that the ID is returned
        assert isinstance(discussion_id, int), "Discussion ID should be an integer"
        assert discussion_id > 0, "Discussion ID should be greater than 0"
        
        # Check that the directory structure was created
        discussion_dir = tmp_path / f"discussion_{discussion_id}"
        assert discussion_dir.exists(), f"Discussion directory {discussion_dir} should exist"
        assert (discussion_dir / "metadata.json").exists(), "metadata.json file should exist"
        assert (discussion_dir / "question.md").exists(), "question.md file should exist"
        assert (discussion_dir / "submissions").exists(), "submissions directory should exist"
        
        # Check metadata content
        with open(discussion_dir / "metadata.json", "r") as f:
            metadata = json.load(f)
        
        assert metadata["id"] == discussion_id, "Discussion ID in metadata should match"
        assert metadata["title"] == "Test Discussion", "Discussion title in metadata should match"
        assert metadata["points"] == 10, "Points value in metadata should match"
        assert metadata["min_words"] == 200, "Min words value in metadata should match"
        assert metadata["question_file"] == "question.md", "Question file path in metadata should be correct"
        assert "created_at" in metadata, "Metadata should include created_at timestamp"
        assert "updated_at" in metadata, "Metadata should include updated_at timestamp"
        
        # Check question content
        with open(discussion_dir / "question.md", "r") as f:
            content = f.read()
        assert content == "What is the meaning of life?", "Question content should match what was provided"
    
    def test_get_discussion(self, discussion_manager):
        """Test retrieving a discussion."""
        # Create a discussion
        discussion_id = discussion_manager.create_discussion(
            title="Test Discussion",
            question_content="Test Question"
        )
        
        # Get the discussion
        discussion = discussion_manager.get_discussion(discussion_id)
        
        # Check the returned data
        assert isinstance(discussion, Discussion), "get_discussion should return a Discussion object"
        assert discussion.id == discussion_id, "Discussion ID should match what was created"
        assert discussion.title == "Test Discussion", "Discussion title should match what was provided"
        assert discussion.question_content == "Test Question", "Question content should match what was provided"
        assert discussion.points == 12, "Points should have default value when not specified"
        assert discussion.min_words == 300, "Min words should have default value when not specified"
    
    def test_get_nonexistent_discussion(self, discussion_manager):
        """Test retrieving a discussion that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            discussion_manager.get_discussion(999)
    
    def test_list_discussions_empty(self, discussion_manager):
        """Test listing discussions when none exist."""
        discussions = discussion_manager.list_discussions()
        assert isinstance(discussions, list), "list_discussions should return a list"
        assert len(discussions) == 0, "Empty manager should return empty list of discussions"
    
    def test_list_discussions(self, discussion_manager):
        """Test listing multiple discussions."""
        # Create a few discussions
        id1 = discussion_manager.create_discussion(title="Discussion 1")
        id2 = discussion_manager.create_discussion(title="Discussion 2")
        id3 = discussion_manager.create_discussion(title="Discussion 3")
        
        # List discussions
        discussions = discussion_manager.list_discussions()
        
        # Check the result
        assert len(discussions) == 3, "Should return all 3 created discussions"
        assert isinstance(discussions[0], Discussion), "Should return Discussion objects"
        assert discussions[0].id == id1, "First discussion ID should match first created ID"
        assert discussions[1].id == id2, "Second discussion ID should match second created ID"
        assert discussions[2].id == id3, "Third discussion ID should match third created ID"
        assert discussions[0].title == "Discussion 1", "First discussion title should match"
        assert discussions[1].title == "Discussion 2", "Second discussion title should match"
        assert discussions[2].title == "Discussion 3", "Third discussion title should match"
        
        # Check that question_content is empty for efficiency
        assert discussions[0].question_content == "", "Question content should be empty for efficiency in list results"
    
    def test_update_discussion(self, discussion_manager):
        """Test updating a discussion."""
        # Create a discussion
        discussion_id = discussion_manager.create_discussion(
            title="Old Title",
            points=10,
            question_content="Old question"
        )
        
        # Update the discussion
        updated = discussion_manager.update_discussion(
            discussion_id,
            title="New Title",
            points=15,
            question_content="New question"
        )
        
        # Check that the update was successful
        assert isinstance(updated, Discussion), "update_discussion should return a Discussion object"
        assert updated.id == discussion_id, "Updated discussion ID should not change"
        assert updated.title == "New Title", "Discussion title should be updated"
        assert updated.points == 15, "Points value should be updated"
        assert updated.question_content == "New question", "Question content should be updated"
        
        # Verify by getting the discussion directly
        discussion = discussion_manager.get_discussion(discussion_id)
        assert discussion.title == "New Title", "Title update should persist"
        assert discussion.points == 15, "Points update should persist"
        assert discussion.question_content == "New question", "Question content update should persist"
    
    def test_update_nonexistent_discussion(self, discussion_manager):
        """Test updating a discussion that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            discussion_manager.update_discussion(999, title="New Title")
    
    def test_id_generation(self, discussion_manager):
        """Test that IDs are generated sequentially."""
        id1 = discussion_manager.create_discussion(title="Discussion 1")
        id2 = discussion_manager.create_discussion(title="Discussion 2")
        id3 = discussion_manager.create_discussion(title="Discussion 3")
        
        assert id2 == id1 + 1, "Discussion IDs should be sequential"
        assert id3 == id2 + 1, "Discussion IDs should be sequential"
    
    def test_create_discussion_without_question(self, discussion_manager, tmp_path):
        """Test creating a discussion without providing question content."""
        discussion_id = discussion_manager.create_discussion(title="No Question Discussion")
        
        # Check that an empty question file was created
        discussion_dir = tmp_path / f"discussion_{discussion_id}"
        with open(discussion_dir / "question.md", "r") as f:
            content = f.read()
        assert content == "", "Question file should be empty when no content is provided"
        
        # Check via get_discussion
        discussion = discussion_manager.get_discussion(discussion_id)
        assert discussion.question_content == "", "Question content should be empty when none provided"
    
    def test_discussion_model(self):
        """Test the Discussion model class."""
        # Create a Discussion object
        discussion = Discussion(
            id=1,
            title="Test Title",
            points=15,
            min_words=250
        )
        
        # Check attributes
        assert discussion.id == 1, "ID should be set correctly in the constructor"
        assert discussion.title == "Test Title", "Title should be set correctly in the constructor"
        assert discussion.points == 15, "Points should be set correctly in the constructor"
        assert discussion.min_words == 250, "Min words should be set correctly in the constructor"
        assert discussion.question_content == "", "Question content should default to empty string"
        
        # Test to_dict method
        data = discussion.to_dict()
        assert "id" in data, "to_dict() result should include id"
        assert "title" in data, "to_dict() result should include title"
        assert "points" in data, "to_dict() result should include points"
        assert "question_content" not in data, "to_dict() should exclude question_content"
        
        # Test from_dict method
        discussion2 = Discussion.from_dict({
            "id": 2,
            "title": "Another Title",
            "question_content": "Some content"
        })
        assert discussion2.id == 2, "from_dict() should set id from dictionary"
        assert discussion2.title == "Another Title", "from_dict() should set title from dictionary"
        assert discussion2.question_content == "Some content", "from_dict() should set question_content from dictionary"
        assert discussion2.points == 12, "from_dict() should use default values for missing fields"
