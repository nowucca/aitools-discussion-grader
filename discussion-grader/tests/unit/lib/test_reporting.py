"""
Unit tests for the ReportGenerator class.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from lib.reporting import ReportGenerator, ReportStats, SynthesizedReport
from lib.submission import GradedSubmission


class TestReportGenerator:
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_init(self, mock_submission_grader, mock_config_manager, mock_ai_grader, tmp_path):
        """Test ReportGenerator initialization."""
        # Mock config manager to avoid config file issues
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator(str(tmp_path))
        assert generator.base_dir == tmp_path
        assert generator.config_manager is not None
        assert generator.ai_grader is not None
        assert generator.submission_grader is not None
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_generate_report_success(self, mock_submission_grader_class, mock_config_manager, mock_ai_grader, tmp_path):
        """Test successful report generation."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        # Setup
        generator = ReportGenerator(str(tmp_path))
        
        # Mock submissions as dictionaries (what SubmissionGrader returns)
        mock_submissions = [
            {
                'submission_id': '1',
                'created_at': '2023-01-01',
                'grading': {
                    'score': 11.0,
                    'feedback': "Excellent work",
                    'word_count': 350,
                    'improvement_suggestions': ["Great job overall"],
                    'addressed_questions': {"main": True},
                    'meets_word_count': True,
                    'created_at': '2023-01-01'
                }
            },
            {
                'submission_id': '2',
                'created_at': '2023-01-02',
                'grading': {
                    'score': 9.5,
                    'feedback': "Good effort",
                    'word_count': 280,
                    'improvement_suggestions': ["Add more depth"],
                    'addressed_questions': {"main": True},
                    'meets_word_count': False,
                    'created_at': '2023-01-02'
                }
            }
        ]
        
        mock_submission_grader = mock_submission_grader_class.return_value
        mock_submission_grader.list_submissions.return_value = mock_submissions
        
        # Setup discussion files
        discussion_dir = tmp_path / "discussion_1"
        discussion_dir.mkdir()
        
        metadata = {
            "id": 1,
            "title": "Test Discussion",
            "points": 12,
            "min_words": 300
        }
        (discussion_dir / "metadata.json").write_text(json.dumps(metadata))
        (discussion_dir / "question.md").write_text("What are your thoughts on this topic?")
        
        # Mock AI response
        with patch.object(generator.ai_grader, '_get_client') as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = '''
            {
                "summary": "Students showed good understanding with varied perspectives.",
                "key_themes": ["Understanding", "Analysis", "Examples"],
                "unique_insights": ["Novel perspective on topic", "Creative examples"]
            }
            '''
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            # Execute
            report = generator.generate_report(discussion_id=1)
            
            # Verify
            assert isinstance(report, SynthesizedReport)
            assert report.discussion_id == 1
            assert report.summary == "Students showed good understanding with varied perspectives."
            assert "Understanding" in report.key_themes
            assert len(report.filtered_submissions) == 2
            assert report.statistics.total_submissions == 2
            assert report.statistics.avg_score == 10.25
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_generate_report_no_submissions(self, mock_submission_grader, mock_config_manager, mock_ai_grader, tmp_path):
        """Test report generation with no submissions."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator(str(tmp_path))
        
        with patch.object(generator.submission_grader, 'list_submissions', return_value=[]):
            with pytest.raises(ValueError, match="No submissions found"):
                generator.generate_report(discussion_id=1)
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_init(self, mock_submission_grader, mock_config_manager, mock_ai_grader):
        """Test ReportGenerator initialization."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance

        generator = ReportGenerator()
        
        submissions = [
            GradedSubmission(score=11.0, feedback="feedback1", word_count=300, submission_id=1),
            GradedSubmission(score=8.0, feedback="feedback2", word_count=280, submission_id=2),
            GradedSubmission(score=6.0, feedback="feedback3", word_count=250, submission_id=3)
        ]
        
        filtered = generator._filter_submissions(submissions, min_score=9.0)
        
        assert len(filtered) == 1
        assert filtered[0].submission_id == 1
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_filter_submissions_max_score(self, mock_submission_grader, mock_config_manager, mock_ai_grader):
        """Test filtering submissions by maximum score."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator()
        
        submissions = [
            GradedSubmission(score=11.0, feedback="feedback1", word_count=300, submission_id=1),
            GradedSubmission(score=8.0, feedback="feedback2", word_count=280, submission_id=2),
            GradedSubmission(score=6.0, feedback="feedback3", word_count=250, submission_id=3)
        ]
        
        filtered = generator._filter_submissions(submissions, max_score=8.0)
        
        assert len(filtered) == 2
        assert filtered[0].submission_id == 2
        assert filtered[1].submission_id == 3
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_filter_submissions_grade_filter(self, mock_submission_grader, mock_config_manager, mock_ai_grader):
        """Test filtering submissions by letter grade (not supported in simple model)."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator()
        
        submissions = [
            GradedSubmission(score=11.0, feedback="feedback1", word_count=300, submission_id=1),
            GradedSubmission(score=8.0, feedback="feedback2", word_count=280, submission_id=2),
            GradedSubmission(score=6.0, feedback="feedback3", word_count=250, submission_id=3)
        ]
        
        # Grade filter is ignored in simple model, should return all submissions
        filtered = generator._filter_submissions(submissions, grade_filter="B")
        
        assert len(filtered) == 3  # All submissions returned since grade filter is not supported
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_filter_submissions_no_matches(self, mock_submission_grader, mock_config_manager, mock_ai_grader):
        """Test filtering with criteria that match nothing."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator()
        
        submissions = [
            GradedSubmission(score=8.0, feedback="feedback1", word_count=300, submission_id=1)
        ]
        
        filtered = generator._filter_submissions(submissions, min_score=10.0)
        
        assert len(filtered) == 0
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_calculate_statistics(self, mock_submission_grader, mock_config_manager, mock_ai_grader):
        """Test statistics calculation."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator()
        
        submissions = [
            GradedSubmission(score=11.0, feedback="feedback1", word_count=350, submission_id=1),
            GradedSubmission(score=9.0, feedback="feedback2", word_count=280, submission_id=2),
            GradedSubmission(score=7.0, feedback="feedback3", word_count=250, submission_id=3)
        ]
        
        stats = generator._calculate_statistics(submissions)
        
        assert isinstance(stats, ReportStats)
        assert stats.total_submissions == 3
        assert stats.avg_score == 9.0
        assert stats.min_score == 7.0
        assert stats.max_score == 11.0
        assert stats.avg_word_count == 293  # (350 + 280 + 250) / 3
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_calculate_statistics_empty(self, mock_submission_grader, mock_config_manager, mock_ai_grader):
        """Test statistics calculation with empty submissions."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator()
        
        stats = generator._calculate_statistics([])
        
        assert stats.total_submissions == 0
        assert stats.avg_score == 0.0
        assert stats.min_score == 0.0
        assert stats.max_score == 0.0
        assert stats.avg_word_count == 0
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_format_text_report(self, mock_submission_grader, mock_config_manager, mock_ai_grader):
        """Test text report formatting."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator()
        
        stats = ReportStats(
            total_submissions=2,
            avg_score=10.0,
            min_score=9.0,
            max_score=11.0,
            avg_word_count=300
        )
        
        report = SynthesizedReport(
            discussion_id=1,
            summary="Test summary",
            key_themes=["Theme 1", "Theme 2"],
            unique_insights=["Insight 1"],
            statistics=stats,
            filtered_submissions=[]
        )
        
        text_output = generator._format_text_report(report)
        
        assert "DISCUSSION REPORT - Discussion 1" in text_output
        assert "Total Submissions: 2" in text_output
        assert "Average Score: 10.0" in text_output
        assert "Test summary" in text_output
        assert "Theme 1" in text_output
        assert "Insight 1" in text_output
        # Ensure no sample_response section exists
        assert "SAMPLE RESPONSE:" not in text_output
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_format_json_report(self, mock_submission_grader, mock_config_manager, mock_ai_grader):
        """Test JSON report formatting."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator()
        
        stats = ReportStats(
            total_submissions=1,
            avg_score=10.5,
            min_score=10.5,
            max_score=10.5,
            avg_word_count=300
        )
        
        submission = GradedSubmission(score=10.5, feedback="feedback", word_count=300, submission_id=1)
        
        report = SynthesizedReport(
            discussion_id=1,
            summary="Test summary",
            key_themes=["Theme 1"],
            unique_insights=["Insight 1"],
            statistics=stats,
            filtered_submissions=[submission]
        )
        
        json_output = generator._format_json_report(report)
        parsed = json.loads(json_output)
        
        assert parsed["discussion_id"] == 1
        assert parsed["summary"] == "Test summary"
        assert parsed["key_themes"] == ["Theme 1"]
        assert parsed["statistics"]["total_submissions"] == 1
        assert len(parsed["filtered_submissions"]) == 1
        assert parsed["filtered_submissions"][0]["submission_id"] == 1
        # Ensure no sample_response in JSON output
        assert "sample_response" not in parsed
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_format_csv_report(self, mock_submission_grader, mock_config_manager, mock_ai_grader):
        """Test CSV report formatting."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator()
        
        submission = GradedSubmission(score=10.5, feedback="Great work!", word_count=300, submission_id=1)
        
        report = SynthesizedReport(
            discussion_id=1,
            summary="Test summary",
            key_themes=[],
            unique_insights=[],
            statistics=ReportStats(1, 10.5, 10.5, 10.5, 300),
            filtered_submissions=[submission]
        )
        
        csv_output = generator._format_csv_report(report)
        lines = csv_output.strip().split('\n')
        
        assert len(lines) == 2  # header + 1 data row
        assert "Submission ID,Score,Word Count,Meets Word Count,Feedback" in lines[0]
        assert '"1",10.5,300,"True","Great work!"' in lines[1]
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_export_report_with_file(self, mock_submission_grader, mock_config_manager, mock_ai_grader, tmp_path):
        """Test exporting report to a file."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator()
        
        report = SynthesizedReport(
            discussion_id=1,
            summary="Test summary",
            key_themes=["Theme 1"],
            unique_insights=["Insight 1"],
            statistics=ReportStats(1, 10.0, 10.0, 10.0, 300),
            filtered_submissions=[]
        )
        
        output_file = tmp_path / "test_report.txt"
        content = generator.export_report(report, format_type="text", output_file=str(output_file))
        
        assert output_file.exists()
        file_content = output_file.read_text()
        assert "DISCUSSION REPORT - Discussion 1" in file_content
        assert "Test summary" in file_content
    
    @patch('lib.reporting.AIGrader')
    @patch('lib.reporting.ConfigManager')
    @patch('lib.reporting.SubmissionGrader')
    def test_ai_synthesis_fallback(self, mock_submission_grader, mock_config_manager, mock_ai_grader, tmp_path):
        """Test AI synthesis with fallback on error."""
        # Mock config manager
        mock_config_instance = Mock()
        mock_config_instance.config = {"synthesis": {"prompt": "test prompt"}}
        mock_config_manager.return_value = mock_config_instance
        
        generator = ReportGenerator(str(tmp_path))
        
        # Setup discussion files
        discussion_dir = tmp_path / "discussion_1"
        discussion_dir.mkdir()
        
        metadata = {"id": 1, "title": "Test Discussion", "points": 12}
        (discussion_dir / "metadata.json").write_text(json.dumps(metadata))
        (discussion_dir / "question.md").write_text("Test question")
        
        submissions = [
            GradedSubmission(score=10.0, feedback="feedback", word_count=300, submission_id=1)
        ]
        
        # Mock AI failure
        with patch.object(generator.ai_grader, '_get_client') as mock_get_client:
            mock_client = Mock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_get_client.return_value = mock_client
            
            result = generator._synthesize_submissions(1, submissions)
            
            # Should fallback gracefully
            assert "AI synthesis failed" in result["unique_insights"][0]
            assert "Synthesis of 1 submissions" in result["summary"]
            assert isinstance(result["key_themes"], list)
