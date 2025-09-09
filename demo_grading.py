#!/usr/bin/env python3
"""
Demo script to show grading functionality without requiring API key.
This simulates what the grading system would produce.
"""

import sys
import os
sys.path.append('discussion-grader')

from lib.submission import GradedSubmission
from controllers.submission import SubmissionController

def create_mock_graded_submission(submission_file: str, score: float, feedback: str, 
                                 word_count: int, suggestions: list = None, 
                                 addressed_questions: dict = None):
    """Create a mock graded submission for demonstration."""
    return GradedSubmission(
        score=score,
        feedback=feedback,
        improvement_suggestions=suggestions or [],
        addressed_questions=addressed_questions or {},
        word_count=word_count,
        meets_word_count=word_count >= 300,
        submission_id=None,  # Not saved in demo
        created_at="2025-01-15T10:30:00"
    )

def demo_submission_grading():
    """Demonstrate the submission grading system."""
    print("=" * 80)
    print("MULTI-DISCUSSION GRADING SYSTEM - DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Demo submission 1 - High quality
    print("GRADING SUBMISSION 1 (High Quality)")
    print("-" * 50)
    
    submission1_grade = create_mock_graded_submission(
        submission_file="submission1.txt",
        score=10.5,
        feedback="Excellent comprehensive analysis of AI tools in software development. You demonstrate strong understanding of the topic with specific examples like GitHub Copilot, Testim, and Applitools. Your discussion of both benefits and challenges shows critical thinking. The structure is clear and the conclusion effectively summarizes your key points.",
        word_count=267,
        suggestions=[
            "Consider adding more specific metrics or studies to support your productivity claims",
            "Could expand on the security implications of AI-generated code"
        ],
        addressed_questions={
            "ai_tools_impact": True,
            "specific_examples": True,
            "benefits_challenges": True,
            "future_implications": True
        }
    )
    
    controller = SubmissionController()
    report1 = controller.submission_grader.format_grade_report(
        submission1_grade, 
        submission_file="submission1.txt",
        total_points=12
    )
    print(report1)
    print()
    
    # Demo submission 2 - Lower quality
    print("GRADING SUBMISSION 2 (Needs Improvement)")
    print("-" * 50)
    
    submission2_grade = create_mock_graded_submission(
        submission_file="submission2.txt",
        score=6.5,
        feedback="Your response addresses the basic topic but lacks depth and specific examples. While you mention GitHub Copilot and testing tools, you don't provide detailed analysis of their impact. The response is also quite brief and could benefit from more thorough exploration of the topic.",
        word_count=142,
        suggestions=[
            "Expand your analysis with more specific examples and details",
            "Meet the minimum word count requirement (300 words)",
            "Provide more concrete examples of AI tools and their specific impacts",
            "Develop your arguments with more supporting evidence"
        ],
        addressed_questions={
            "ai_tools_impact": True,
            "specific_examples": False,
            "benefits_challenges": True,
            "future_implications": False
        }
    )
    
    report2 = controller.submission_grader.format_grade_report(
        submission2_grade,
        submission_file="submission2.txt", 
        total_points=12
    )
    print(report2)
    print()
    
    # Demo submission 3 - Exceptional quality
    print("GRADING SUBMISSION 3 (Exceptional Quality)")
    print("-" * 50)
    
    submission3_grade = create_mock_graded_submission(
        submission_file="submission3.txt",
        score=11.5,
        feedback="Outstanding comprehensive analysis that demonstrates exceptional depth of understanding. Your discussion covers the entire software development lifecycle, provides specific tool examples, and thoughtfully addresses both opportunities and challenges. The writing is sophisticated, well-structured, and shows excellent critical thinking about the evolving role of software engineers.",
        word_count=623,
        suggestions=[
            "Consider adding a brief discussion of regulatory or compliance considerations",
            "Could mention specific metrics from the studies you reference"
        ],
        addressed_questions={
            "ai_tools_impact": True,
            "specific_examples": True,
            "benefits_challenges": True,
            "future_implications": True,
            "detailed_analysis": True
        }
    )
    
    report3 = controller.submission_grader.format_grade_report(
        submission3_grade,
        submission_file="submission3.txt",
        total_points=12
    )
    print(report3)
    print()
    
    # Demo different output formats
    print("DEMONSTRATION OF OUTPUT FORMATS")
    print("-" * 50)
    
    print("JSON Format:")
    json_output = controller._format_grade_as_json(submission1_grade, "submission1.txt", 12)
    print(json_output)
    print()
    
    print("CSV Format:")
    csv_output = controller._format_grade_as_csv(submission1_grade, "submission1.txt", 12)
    print(csv_output)
    print()
    
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("This demonstration shows:")
    print("✅ AI-powered grading with detailed feedback")
    print("✅ Multiple output formats (text, JSON, CSV)")
    print("✅ Word count validation")
    print("✅ Improvement suggestions")
    print("✅ Question addressing analysis")
    print("✅ Professional grade report formatting")
    print()
    print("The actual system integrates with Claude AI for real grading.")

if __name__ == "__main__":
    demo_submission_grading()
