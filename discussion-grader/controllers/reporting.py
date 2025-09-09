"""
Report controller for handling report generation and export operations.
"""
from typing import Optional
from lib.reporting import ReportGenerator, SynthesizedReport


class ReportController:
    """Controller for report operations."""
    
    def __init__(self, base_dir: str = "discussions"):
        # Determine if we're running from top level or inside discussion-grader
        import os
        if os.path.exists("discussion-grader/config/config.json"):
            # Running from top level
            config_path = "discussion-grader/config/config.json"
        else:
            # Running from inside discussion-grader
            config_path = "config/config.json"
        
        self.report_generator = ReportGenerator(base_dir, config_path)
    
    def generate(
        self, 
        discussion_id: int,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        grade_filter: Optional[str] = None,
        format_type: str = "text"
    ) -> str:
        """Generate a synthesized report for a discussion."""
        try:
            # Generate the report
            report = self.report_generator.generate_report(
                discussion_id=discussion_id,
                min_score=min_score,
                max_score=max_score,
                grade_filter=grade_filter
            )
            
            # Export in the requested format
            content = self.report_generator.export_report(report, format_type)
            
            return content
            
        except ValueError as e:
            return f"Error: {str(e)}"
        except FileNotFoundError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error generating report: {str(e)}"
    
    def export(
        self, 
        discussion_id: int,
        output_file: str,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        grade_filter: Optional[str] = None,
        format_type: str = "text"
    ) -> str:
        """Generate and export a report to a file."""
        try:
            # Generate the report
            report = self.report_generator.generate_report(
                discussion_id=discussion_id,
                min_score=min_score,
                max_score=max_score,
                grade_filter=grade_filter
            )
            
            # Export to file
            content = self.report_generator.export_report(
                report, 
                format_type=format_type,
                output_file=output_file
            )
            
            return f"Report exported successfully to {output_file}"
            
        except ValueError as e:
            return f"Error: {str(e)}"
        except FileNotFoundError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error exporting report: {str(e)}"
    
    def get_statistics(self, discussion_id: int) -> str:
        """Get basic statistics for a discussion."""
        try:
            # Generate report to get statistics
            report = self.report_generator.generate_report(discussion_id)
            
            stats = report.statistics
            lines = []
            lines.append(f"Discussion {discussion_id} Statistics:")
            lines.append(f"  Total Submissions: {stats.total_submissions}")
            lines.append(f"  Average Score: {stats.avg_score:.1f}")
            lines.append(f"  Score Range: {stats.min_score:.1f} - {stats.max_score:.1f}")
            lines.append(f"  Average Word Count: {stats.avg_word_count}")
            
            return "\n".join(lines)
            
        except ValueError as e:
            return f"Error: {str(e)}"
        except FileNotFoundError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error getting statistics: {str(e)}"
    
    def list_available_discussions(self) -> str:
        """List discussions that have submissions available for reporting."""
        try:
            # Use the submission grader to find discussions with submissions
            from lib.submission_grader import SubmissionGrader
            
            submission_grader = SubmissionGrader(str(self.report_generator.base_dir))
            
            # Get all discussion directories
            discussion_dirs = []
            base_path = self.report_generator.base_dir
            
            if not base_path.exists():
                return "No discussions directory found."
            
            for item in base_path.iterdir():
                if item.is_dir() and item.name.startswith("discussion_"):
                    try:
                        discussion_id = int(item.name.split("_")[1])
                        submissions = submission_grader.list_submissions(discussion_id)
                        if submissions:  # Only include discussions with submissions
                            discussion_dirs.append((discussion_id, len(submissions)))
                    except (ValueError, IndexError):
                        continue
            
            if not discussion_dirs:
                return "No discussions with submissions found."
            
            lines = []
            lines.append("Discussions with submissions available for reporting:")
            lines.append("")
            
            for discussion_id, submission_count in sorted(discussion_dirs):
                lines.append(f"  Discussion {discussion_id}: {submission_count} submissions")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error listing discussions: {str(e)}"
