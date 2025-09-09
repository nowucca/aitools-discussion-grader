"""
Unit tests for the ReportController class.
"""
import pytest
from unittest.mock import Mock, patch, mock_open

from controllers.reporting import ReportController
from lib.reporting import SynthesizedReport, ReportStats
from lib.submission import GradedSubmission


class TestReportController:
    
    @patch('lib.reporting.AIGrader')  
    @patch('lib.reporting.SubmissionGrader')  
    def test_init(self, mock_submission_grader, mock_ai_grader):
        """Test ReportController initialization."""
        controller = ReportController("test_dir")
        assert controller.report_generator is not None
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.SubmissionGrader')
    def test_generate_success(self, mock_submission_grader, mock_ai_grader):
        """Test successful report generation."""
        # Mock the submission grader to return test data in proper dictionary format
        mock_grader = mock_submission_grader.return_value
        mock_grader.list_submissions.return_value = [
            {
                "submission_id": 1,
                "discussion_id": 1,
                "grading": {
                    "score": 10.0,
                    "feedback": "Good work",
                    "word_count": 300,
                    "meets_word_count": True,
                    "improvement_suggestions": [],
                    "addressed_questions": {}
                },
                "created_at": "2023-01-01T00:00:00"
            }
        ]

        # Mock the AI grader and its methods comprehensively
        mock_ai_instance = Mock()
        mock_ai_grader.return_value = mock_ai_instance

        # Create properly configured mock response chain
        mock_content_item = Mock()
        mock_content_item.text = '{"summary": "Test summary", "key_themes": ["Theme"], "unique_insights": ["Insight"]}'
        
        mock_response = Mock()
        mock_response.content = [mock_content_item]
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_ai_instance._get_client.return_value = mock_client

        # Mock the file system operations for discussion metadata  
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value="Test question"), \
             patch('builtins.open', mock_open(read_data='{"id": 1, "title": "Test Discussion"}')):
            
            # Setup controller after mocking
            controller = ReportController()

            # Execute
            result = controller.generate(
                discussion_id=1,
                min_score=8.0,
                format_type="text"
            )

        # Verify
        assert "DISCUSSION REPORT - Discussion 1" in result, f"Expected discussion title in result, but got: {result}"
        assert "Test summary" in result, f"Expected 'Test summary' in result, but got: {result}"
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.SubmissionGrader')
    def test_generate_value_error(self, mock_submission_grader, mock_ai_grader):
        """Test report generation with ValueError."""
        controller = ReportController()
        
        # Mock empty submissions to trigger ValueError
        mock_grader = mock_submission_grader.return_value
        mock_grader.list_submissions.return_value = []
        
        result = controller.generate(discussion_id=1)
        
        assert result == "Error: No submissions found for discussion 1"
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.SubmissionGrader')
    def test_generate_file_not_found_error(self, mock_submission_grader, mock_ai_grader):
        """Test report generation with FileNotFoundError."""
        controller = ReportController()
        
        # This will naturally cause a FileNotFoundError when trying to read discussion metadata
        result = controller.generate(discussion_id=999)
        
        assert "Error:" in result
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.SubmissionGrader')
    def test_generate_unexpected_error(self, mock_submission_grader, mock_ai_grader):
        """Test report generation with unexpected error."""
        controller = ReportController()
        
        # Mock to cause an exception in the submission grader
        mock_grader = mock_submission_grader.return_value
        mock_grader.list_submissions.side_effect = Exception("Unexpected error")
        
        result = controller.generate(discussion_id=1)
        
        assert "Unexpected error generating report" in result
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.SubmissionGrader')
    def test_export_success(self, mock_submission_grader, mock_ai_grader, tmp_path):
        """Test successful report export."""
        controller = ReportController()
        
        # Mock report
        mock_stats = ReportStats(1, 10.0, 10.0, 10.0, 300)
        mock_report = SynthesizedReport(
            discussion_id=1,
            summary="Test summary",
            key_themes=[],
            unique_insights=[],
            statistics=mock_stats,
            filtered_submissions=[]
        )
        
        # Mock the submission grader to return test data in proper dictionary format
        mock_grader = mock_submission_grader.return_value
        mock_grader.list_submissions.return_value = [
            {
                "submission_id": 1,
                "discussion_id": 1,
                "grading": {
                    "score": 10.0,
                    "feedback": "Good work",
                    "word_count": 300,
                    "meets_word_count": True,
                    "improvement_suggestions": [],
                    "addressed_questions": {}
                },
                "created_at": "2023-01-01T00:00:00"
            }
        ]
        
        # Mock the AI grader synthesis method
        mock_ai_grader.return_value.synthesize_discussion.return_value = {
            "summary": "Test",
            "key_themes": [],
            "unique_insights": []
        }
        
        output_file = tmp_path / "report.txt"
        result = controller.export(
            discussion_id=1,
            output_file=str(output_file),
            format_type="json"
        )
        
        assert f"Report exported successfully to {output_file}" in result
        assert output_file.exists()
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.SubmissionGrader')
    def test_export_with_filters(self, mock_submission_grader, mock_ai_grader, tmp_path):
        """Test report export with filters."""
        controller = ReportController()
        
        mock_stats = ReportStats(1, 11.0, 11.0, 11.0, 350)
        mock_report = SynthesizedReport(
            discussion_id=1,
            summary="Filtered summary",
            key_themes=[],
            unique_insights=[],
            statistics=mock_stats,
            filtered_submissions=[]
        )
        
        # Mock the submission grader to return test data in proper dictionary format
        mock_grader = mock_submission_grader.return_value
        mock_grader.list_submissions.return_value = [
            {
                "submission_id": 1,
                "discussion_id": 1,
                "grading": {
                    "score": 11.0,
                    "feedback": "Great work",
                    "word_count": 350,
                    "meets_word_count": True,
                    "improvement_suggestions": [],
                    "addressed_questions": {}
                },
                "created_at": "2023-01-01T00:00:00"
            }
        ]
        
        # Mock the AI grader synthesis method
        mock_ai_grader.return_value.synthesize_discussion.return_value = {
            "summary": "Filtered",
            "key_themes": [],
            "unique_insights": []
        }
        
        output_file = tmp_path / "filtered_report.json"
        result = controller.export(
            discussion_id=1,
            output_file=str(output_file),
            min_score=10.0,
            max_score=12.0,
            grade_filter="A",
            format_type="json"
        )
        
        assert "Report exported successfully" in result
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.SubmissionGrader')
    def test_get_statistics_success(self, mock_submission_grader, mock_ai_grader):
        """Test successful statistics retrieval."""
        controller = ReportController()
        
        mock_stats = ReportStats(3, 9.5, 7.0, 12.0, 320)
        mock_report = SynthesizedReport(
            discussion_id=1,
            summary="Stats summary",
            key_themes=[],
            unique_insights=[],
            statistics=mock_stats,
            filtered_submissions=[]
        )
        
        # Mock submission data in proper dictionary format
        mock_grader = mock_submission_grader.return_value
        mock_grader.list_submissions.return_value = [
            {
                "submission_id": 1,
                "discussion_id": 1,
                "grading": {
                    "score": 12.0,
                    "feedback": "Excellent",
                    "word_count": 400,
                    "meets_word_count": True,
                    "improvement_suggestions": [],
                    "addressed_questions": {}
                },
                "created_at": "2023-01-01T00:00:00"
            },
            {
                "submission_id": 2,
                "discussion_id": 1,
                "grading": {
                    "score": 9.0,
                    "feedback": "Good",
                    "word_count": 300,
                    "meets_word_count": True,
                    "improvement_suggestions": [],
                    "addressed_questions": {}
                },
                "created_at": "2023-01-01T00:00:00"
            },
            {
                "submission_id": 3,
                "discussion_id": 1,
                "grading": {
                    "score": 7.0,
                    "feedback": "Fair",
                    "word_count": 260,
                    "meets_word_count": True,
                    "improvement_suggestions": [],
                    "addressed_questions": {}
                },
                "created_at": "2023-01-01T00:00:00"
            }
        ]
        
        # Mock the AI grader synthesis method
        mock_ai_grader.return_value.synthesize_discussion.return_value = {
            "summary": "Stats",
            "key_themes": [],
            "unique_insights": []
        }
        
        result = controller.get_statistics(discussion_id=1)
        
        assert "Discussion 1 Statistics:" in result
        assert "Total Submissions: 3" in result
        assert "Average Score: 9.3" in result  # (12+9+7)/3 = 9.33
        assert "Average Word Count: 320" in result  # (400+300+260)/3 = 320
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.SubmissionGrader')
    def test_get_statistics_error(self, mock_submission_grader, mock_ai_grader):
        """Test statistics retrieval with error."""
        controller = ReportController()
        
        # Mock empty submissions
        mock_grader = mock_submission_grader.return_value
        mock_grader.list_submissions.return_value = []
        
        result = controller.get_statistics(discussion_id=999)
        
        assert "Error:" in result
    

    @patch('lib.reporting.AIGrader')
    def test_list_available_discussions_empty(self, mock_ai_grader):
        """Test listing discussions when none have submissions."""
        controller = ReportController()
        
        with patch.object(controller.report_generator, 'base_dir') as mock_base_dir:
            mock_base_dir.exists.return_value = True
            mock_dir1 = Mock()
            mock_dir1.is_dir.return_value = True
            mock_dir1.name = "discussion_1"
            mock_base_dir.iterdir.return_value = [mock_dir1]
            
            with patch.object(controller.report_generator, 'submission_grader') as mock_grader:
                mock_grader.list_submissions.return_value = []
                
                result = controller.list_available_discussions()
                assert result == "No discussions with submissions found."
