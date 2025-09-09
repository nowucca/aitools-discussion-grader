"""
Report generation functionality for synthesizing student submissions.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from .config import ConfigManager
from .ai import AIGrader
from .submission_grader import SubmissionGrader
from .submission import GradedSubmission


@dataclass
class ReportStats:
    """Statistics for a report."""
    total_submissions: int
    avg_score: float
    min_score: float
    max_score: float
    avg_word_count: int


@dataclass
class SynthesizedReport:
    """A synthesized report combining multiple submissions."""
    discussion_id: int
    summary: str
    key_themes: List[str]
    unique_insights: List[str]
    statistics: ReportStats
    filtered_submissions: List[GradedSubmission]
    
    
class ReportGenerator:
    """Generates synthesized reports from graded submissions."""
    
    def __init__(self, base_dir: str = "discussions", config_path: str = None):
        self.base_dir = Path(base_dir)
        self.config_manager = ConfigManager(config_path)
        self.ai_grader = AIGrader()
        self.submission_grader = SubmissionGrader(base_dir)
        
    def generate_report(
        self, 
        discussion_id: int, 
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        grade_filter: Optional[str] = None
    ) -> SynthesizedReport:
        """Generate a synthesized report for a discussion."""
        # Get all graded submissions (returns dicts)
        submission_dicts = self.submission_grader.list_submissions(discussion_id)
        
        if not submission_dicts:
            raise ValueError(f"No submissions found for discussion {discussion_id}")
        
        # Convert dictionaries to GradedSubmission objects
        submissions = []
        for sub_dict in submission_dicts:
            grading_data = sub_dict.get('grading', {})
            graded_sub = GradedSubmission(
                score=grading_data.get('score', 0),
                feedback=grading_data.get('feedback', ''),
                improvement_suggestions=grading_data.get('improvement_suggestions', []),
                addressed_questions=grading_data.get('addressed_questions', {}),
                word_count=grading_data.get('word_count', 0),
                meets_word_count=grading_data.get('meets_word_count', False),
                submission_id=sub_dict.get('submission_id'),
                created_at=grading_data.get('created_at', sub_dict.get('created_at', ''))
            )
            submissions.append(graded_sub)
            
        # Apply filters
        filtered_submissions = self._filter_submissions(
            submissions, min_score, max_score, grade_filter
        )
        
        if not filtered_submissions:
            raise ValueError("No submissions match the specified filters")
            
        # Generate statistics
        stats = self._calculate_statistics(filtered_submissions)
        
        # Synthesize content using AI
        synthesis_result = self._synthesize_submissions(discussion_id, filtered_submissions)
        
        return SynthesizedReport(
            discussion_id=discussion_id,
            summary=synthesis_result['summary'],
            key_themes=synthesis_result['key_themes'],
            unique_insights=synthesis_result['unique_insights'],
            statistics=stats,
            filtered_submissions=filtered_submissions
        )
    
    def export_report(
        self, 
        report: SynthesizedReport, 
        format_type: str = "text",
        output_file: Optional[str] = None
    ) -> str:
        """Export a report in the specified format."""
        if format_type == "json":
            content = self._format_json_report(report)
        elif format_type == "csv":
            content = self._format_csv_report(report)
        elif format_type == "table":
            content = self._format_table_report(report)
        else:  # default to text
            content = self._format_text_report(report)
            
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)
            
        return content
    
    def _filter_submissions(
        self, 
        submissions: List[GradedSubmission],
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        grade_filter: Optional[str] = None
    ) -> List[GradedSubmission]:
        """Filter submissions based on criteria."""
        filtered = submissions[:]
        
        if min_score is not None:
            filtered = [s for s in filtered if s.score >= min_score]
            
        if max_score is not None:
            filtered = [s for s in filtered if s.score <= max_score]
            
        # Note: grade_filter not supported with simple model
        if grade_filter:
            # For simple model, we can't filter by letter grade since it doesn't exist
            # Just log a warning and return all filtered submissions
            pass
            
        return filtered
    
    def _calculate_statistics(self, submissions: List[GradedSubmission]) -> ReportStats:
        """Calculate statistics for a list of submissions."""
        if not submissions:
            return ReportStats(0, 0.0, 0.0, 0.0, 0)
            
        scores = [s.score for s in submissions]
        word_counts = [s.word_count for s in submissions]
        
        return ReportStats(
            total_submissions=len(submissions),
            avg_score=sum(scores) / len(scores),
            min_score=min(scores),
            max_score=max(scores),
            avg_word_count=int(sum(word_counts) / len(word_counts))
        )
    
    def _synthesize_submissions(
        self, 
        discussion_id: int, 
        submissions: List[GradedSubmission]
    ) -> Dict[str, Any]:
        """Use AI to synthesize submissions into a coherent report."""
        # Get discussion metadata
        discussion_dir = self.base_dir / f"discussion_{discussion_id}"
        metadata_file = discussion_dir / "metadata.json"
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"Discussion {discussion_id} metadata not found")
            
        with open(metadata_file) as f:
            discussion_data = json.load(f)
        
        # Get question text
        question_file = discussion_dir / "question.md"
        question_text = question_file.read_text() if question_file.exists() else "No question available"
        
        # Prepare submission texts for synthesis
        submission_texts = []
        for i, submission in enumerate(submissions, 1):
            # Use feedback as proxy for content since we don't have original submission text
            submission_texts.append(f"Submission {i} (Score: {submission.score}/12, {submission.word_count} words):\nFeedback: {submission.feedback}")
        
        # Get synthesis prompt from config
        config = self.config_manager.config
        synthesis_prompt = config.get('synthesis', {}).get(
            'prompt', 
            "You are synthesizing student responses to create a comprehensive instructor response. Extract key insights, identify common themes, and highlight unique perspectives."
        )
        
        # Create the synthesis prompt
        prompt = f"""
{synthesis_prompt}

Discussion Question: {question_text}

Here are the student submissions to synthesize:

{chr(10).join(submission_texts)}

Please provide a synthesis in JSON format with the following structure:
{{
    "summary": "A comprehensive summary of all responses",
    "key_themes": ["theme1", "theme2", "theme3"],
    "unique_insights": ["insight1", "insight2", "insight3"]
}}

Focus on:
1. Common themes and patterns across responses
2. Unique perspectives that add value
3. Quality of reasoning and evidence
4. Areas where students showed deep understanding
"""

        try:
            # Use the AI grader's internal client 
            client = self.ai_grader._get_client()
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            response_text = response.content[0].text.strip()
            
            # Extract JSON from response if it's wrapped in code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                response_text = response_text[json_start:json_end].strip()
            
            # Clean control characters that can break JSON parsing
            import re
            response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)
            
            synthesis_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['summary', 'key_themes', 'unique_insights']
            for field in required_fields:
                if field not in synthesis_data:
                    if field == 'summary':
                        synthesis_data[field] = "Synthesis unavailable"
                    else:
                        synthesis_data[field] = []
                    
            return synthesis_data
            
        except Exception as e:
            # Fallback if AI synthesis fails
            return {
                "summary": f"Synthesis of {len(submissions)} submissions. Average score: {self._calculate_statistics(submissions).avg_score:.1f}",
                "key_themes": ["Theme extraction failed due to API error"],
                "unique_insights": [f"AI synthesis failed: {str(e)}"]
            }
    
    def _format_text_report(self, report: SynthesizedReport) -> str:
        """Format report as human-readable text."""
        lines = []
        lines.append(f"DISCUSSION REPORT - Discussion {report.discussion_id}")
        lines.append("=" * 50)
        lines.append("")
        
        # Statistics
        stats = report.statistics
        lines.append("STATISTICS:")
        lines.append(f"  Total Submissions: {stats.total_submissions}")
        lines.append(f"  Average Score: {stats.avg_score:.1f}")
        lines.append(f"  Score Range: {stats.min_score:.1f} - {stats.max_score:.1f}")
        lines.append(f"  Average Word Count: {stats.avg_word_count}")
        lines.append("")
        
        
        # Summary
        lines.append("SYNTHESIS SUMMARY:")
        lines.append(report.summary)
        lines.append("")
        
        # Key themes
        lines.append("KEY THEMES:")
        for i, theme in enumerate(report.key_themes, 1):
            lines.append(f"  {i}. {theme}")
        lines.append("")
        
        # Unique insights
        lines.append("UNIQUE INSIGHTS:")
        for i, insight in enumerate(report.unique_insights, 1):
            lines.append(f"  {i}. {insight}")
        lines.append("")
        
        
        return "\n".join(lines)
    
    def _format_json_report(self, report: SynthesizedReport) -> str:
        """Format report as JSON."""
        # Convert to dict, handling dataclass serialization
        report_dict = {
            "discussion_id": report.discussion_id,
            "summary": report.summary,
            "key_themes": report.key_themes,
            "unique_insights": report.unique_insights,
            "statistics": {
                "total_submissions": report.statistics.total_submissions,
                "avg_score": report.statistics.avg_score,
                "min_score": report.statistics.min_score,
                "max_score": report.statistics.max_score,
                "avg_word_count": report.statistics.avg_word_count
            },
            "filtered_submissions": [
                {
                    "submission_id": sub.submission_id,
                    "score": sub.score,
                    "word_count": sub.word_count,
                    "meets_word_count": sub.meets_word_count,
                    "feedback": sub.feedback,
                    "improvement_suggestions": sub.improvement_suggestions,
                    "addressed_questions": sub.addressed_questions,
                    "created_at": sub.created_at
                }
                for sub in report.filtered_submissions
            ]
        }
        
        return json.dumps(report_dict, indent=2)
    
    def _format_csv_report(self, report: SynthesizedReport) -> str:
        """Format report as CSV (focuses on submission data)."""
        lines = []
        lines.append("Submission ID,Score,Word Count,Meets Word Count,Feedback")
        
        for sub in report.filtered_submissions:
            # Escape commas in feedback
            feedback_clean = sub.feedback.replace('"', '""').replace('\n', ' ')
            lines.append(f'"{sub.submission_id}",{sub.score},{sub.word_count},"{sub.meets_word_count}","{feedback_clean}"')
        
        return "\n".join(lines)
    
    def _format_table_report(self, report: SynthesizedReport) -> str:
        """Format report as a table."""
        try:
            from tabulate import tabulate
            
            # Create table data
            headers = ["Submission ID", "Score", "Words", "Word Req Met", "Feedback Preview"]
            table_data = []
            
            for sub in report.filtered_submissions:
                feedback_preview = sub.feedback[:50] + "..." if len(sub.feedback) > 50 else sub.feedback
                table_data.append([
                    sub.submission_id or "N/A",
                    f"{sub.score}/12",
                    sub.word_count,
                    "✓" if sub.meets_word_count else "✗",
                    feedback_preview
                ])
            
            table_output = tabulate(table_data, headers=headers, tablefmt="grid")
            
            # Add summary information above the table
            stats = report.statistics
            summary_lines = [
                f"Discussion {report.discussion_id} Report",
                f"Total Submissions: {stats.total_submissions}, Avg Score: {stats.avg_score:.1f}",
                "",
                table_output
            ]
            
            return "\n".join(summary_lines)
            
        except ImportError:
            # Fallback to simple formatting
            return self._format_text_report(report)
