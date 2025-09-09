"""
Unit tests for the Discussion Controller.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from controllers.discussion import DiscussionController
from lib.discussion import Discussion


@pytest.fixture
def mock_discussion_manager():
    """Create a mock DiscussionManager for tests."""
    with patch('controllers.discussion.DiscussionManager') as mock:
        manager_instance = MagicMock()
        mock.return_value = manager_instance
        yield manager_instance


@pytest.fixture
def sample_discussion():
    """Create a sample discussion for tests."""
    return Discussion(
        id=1,
        title="Test Discussion",
        points=10,
        min_words=250,
        created_at="2025-01-01T12:00:00",
        updated_at="2025-01-01T12:00:00",
        question_content="This is a test question"
    )


class TestDiscussionController:
    """Tests for the DiscussionController class."""
    
    def test_init(self, mock_discussion_manager):
        """Test controller initialization."""
        controller = DiscussionController("test_dir")
        
        # Assert DiscussionManager was initialized correctly
        from controllers.discussion import DiscussionManager
        DiscussionManager.assert_called_once_with("test_dir")
    
    def test_create_success(self, mock_discussion_manager, sample_discussion):
        """Test creating a discussion successfully."""
        # Setup the mock
        mock_discussion_manager.create_discussion.return_value = 1
        mock_discussion_manager.get_discussion.return_value = sample_discussion
        
        # Create the controller
        controller = DiscussionController()
        
        # Test with default format (text)
        result = controller.create("Test Discussion", 10, 250, "Test question")
        
        # Verify the manager was called correctly
        mock_discussion_manager.create_discussion.assert_called_once_with(
            title="Test Discussion",
            points=10,
            min_words=250,
            question_content="Test question"
        )
        
        # Verify the result contains expected information
        assert "Discussion created successfully with ID: 1" in result, "Result should contain the discussion ID"
        assert "Title: Test Discussion" in result, "Result should display the discussion title"
        assert "Points: 10" in result, "Result should display the points value"
        assert "Minimum Words: 250" in result, "Result should display the minimum word count"
    
    
    def test_list_as_table(self, mock_discussion_manager, sample_discussion):
        """Test listing discussions as a table."""
        # Setup the mock
        mock_discussion_manager.list_discussions.return_value = [sample_discussion]
        
        # Create the controller
        controller = DiscussionController()
        
        # Test with table format
        result = controller.list()
        
        # Verify the result contains table formatting
        assert "ID" in result, "Table should contain 'ID' column header"
        assert "Title" in result, "Table should contain 'Title' column header"
        assert "Points" in result, "Table should contain 'Points' column header"
        assert "Min Words" in result, "Table should contain 'Min Words' column header"
        assert "Test Discussion" in result, "Table should contain the discussion title"
        assert "10" in result, "Table should contain the points value"
        assert "250" in result, "Table should contain the minimum words value"
    
    def test_list_as_json(self, mock_discussion_manager, sample_discussion):
        """Test listing discussions as JSON."""
        # Setup the mock
        mock_discussion_manager.list_discussions.return_value = [sample_discussion]
        
        # Create the controller
        controller = DiscussionController()
        
        # Test with JSON format
        result = controller.list(format_type="json")
        
        # Verify the result is valid JSON and contains expected data
        data = json.loads(result)
        assert isinstance(data, list), "Result should be a JSON array"
        assert len(data) == 1, "JSON array should contain exactly one discussion"
        assert data[0]["id"] == 1, "Discussion ID should be 1"
        assert data[0]["title"] == "Test Discussion", "Title should match the sample discussion"
    
    
    def test_list_no_discussions(self, mock_discussion_manager):
        """Test listing when no discussions exist."""
        # Setup the mock
        mock_discussion_manager.list_discussions.return_value = []
        
        # Create the controller
        controller = DiscussionController()
        
        # Test listing
        result = controller.list()
        
        # Verify the result
        assert "No discussions found." in result, "Message should indicate no discussions were found"
    
    def test_show_success(self, mock_discussion_manager, sample_discussion):
        """Test showing a discussion successfully."""
        # Setup the mock
        mock_discussion_manager.get_discussion.return_value = sample_discussion
        
        # Create the controller
        controller = DiscussionController()
        
        # Test showing discussion
        result = controller.show(1)
        
        # Verify the manager was called correctly
        mock_discussion_manager.get_discussion.assert_called_once_with(1)
        
        # Verify the result contains expected information
        assert "Discussion ID: 1" in result, "Result should contain the discussion ID"
        assert "Title: Test Discussion" in result, "Result should contain the discussion title"
        assert "Points: 10" in result, "Result should contain the points value"
        assert "Minimum Words: 250" in result, "Result should contain the minimum words value"
        assert "This is a test question" in result, "Result should contain the question content"
    
    def test_show_not_found(self, mock_discussion_manager):
        """Test showing a non-existent discussion."""
        # Setup the mock
        mock_discussion_manager.get_discussion.side_effect = FileNotFoundError("Discussion not found")
        
        # Create the controller
        controller = DiscussionController()
        
        # Test showing non-existent discussion
        result = controller.show(999)
        
        # Verify the result
        assert "Error: Discussion 999 not found." in result, "Error message should indicate the discussion was not found"
    
    def test_update_success(self, mock_discussion_manager, sample_discussion):
        """Test updating a discussion successfully."""
        # Setup the mock
        mock_discussion_manager.update_discussion.return_value = sample_discussion
        
        # Create the controller
        controller = DiscussionController()
        
        # Test updating with multiple fields
        result = controller.update(1, title="Updated Title", points=15)
        
        # Verify the manager was called correctly
        mock_discussion_manager.update_discussion.assert_called_once_with(
            discussion_id=1,
            title="Updated Title",
            points=15
        )
        
        # Verify the result contains expected information
        assert "Discussion 1 updated successfully" in result, "Result should indicate successful update"
        assert "Title → Updated Title" in result, "Result should show title was updated"
        assert "Points → 15" in result, "Result should show points were updated"
    
    def test_update_no_parameters(self, mock_discussion_manager):
        """Test updating with no parameters."""
        # Create the controller
        controller = DiscussionController()
        
        # Test updating with no parameters
        result = controller.update(1)
        
        # Verify the result
        assert "Error: No update parameters provided." in result, "Error message should indicate no parameters were provided"
        
        # Verify the manager was not called
        mock_discussion_manager.update_discussion.assert_not_called()
    
    def test_update_not_found(self, mock_discussion_manager):
        """Test updating a non-existent discussion."""
        # Setup the mock
        mock_discussion_manager.update_discussion.side_effect = FileNotFoundError("Discussion not found")
        
        # Create the controller
        controller = DiscussionController()
        
        # Test updating non-existent discussion
        result = controller.update(999, title="Updated Title")
        
        # Verify the result
        assert "Error: Discussion 999 not found." in result, "Error message should indicate the discussion was not found"
