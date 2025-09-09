#!/usr/bin/env python3
"""
Discussion Grading System - Main CLI Entry Point
"""

import click
import os
import sys

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-essential output')
@click.pass_context
def cli(ctx, verbose, quiet):
    """Multi-Discussion Grading System

    A comprehensive tool for managing and grading student discussions.
    """
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['QUIET'] = quiet

@cli.group()
@click.pass_context
def discussion(ctx):
    """Manage discussion questions and settings."""
    pass

@discussion.command()
@click.argument('title')
@click.option('--points', '-p', default=12, help='Total points for the discussion')
@click.option('--min-words', '-w', default=300, help='Minimum word count for submissions')
@click.option('--question-file', '-q', type=click.File('r'), help='File containing the discussion question')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'csv']), default='text', help='Output format')
@click.pass_context
def create(ctx, title, points, min_words, question_file, format):
    """Create a new discussion."""
    from controllers.discussion import DiscussionController
    
    # Read question file content if provided
    question_content = None
    if question_file:
        question_content = question_file.read()
    
    controller = DiscussionController()
    result = controller.create(
        title=title,
        points=points,
        min_words=min_words,
        question_content=question_content,
        format_type=format
    )
    
    click.echo(result)

@discussion.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.pass_context
def list(ctx, format):
    """List all discussions."""
    from controllers.discussion import DiscussionController
    
    controller = DiscussionController()
    result = controller.list(format_type=format)
    
    click.echo(result)

@discussion.command()
@click.argument('discussion_id', type=int)
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'csv']), default='text', help='Output format')
@click.pass_context
def show(ctx, discussion_id, format):
    """Show details for a specific discussion."""
    from controllers.discussion import DiscussionController
    
    controller = DiscussionController()
    result = controller.show(discussion_id=discussion_id, format_type=format)
    
    click.echo(result)

@discussion.command()
@click.argument('discussion_id', type=int)
@click.option('--title', '-t', help='New title for the discussion')
@click.option('--points', '-p', type=int, help='New point value for the discussion')
@click.option('--min-words', '-w', type=int, help='New minimum word count for submissions')
@click.option('--question-file', '-q', type=click.File('r'), help='File containing the new discussion question')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'csv']), default='text', help='Output format')
@click.pass_context
def update(ctx, discussion_id, title, points, min_words, question_file, format):
    """Update an existing discussion."""
    from controllers.discussion import DiscussionController
    
    # Read question file content if provided
    question_content = None
    if question_file:
        question_content = question_file.read()
    
    controller = DiscussionController()
    result = controller.update(
        discussion_id=discussion_id,
        title=title,
        points=points,
        min_words=min_words,
        question_content=question_content,
        format_type=format
    )
    
    click.echo(result)

@cli.group()
@click.pass_context
def submission(ctx):
    """Grade and manage student submissions."""
    pass

@submission.command()
@click.argument('discussion_id', type=int)
@click.argument('file_path', type=click.Path(exists=True), required=False)
@click.option('--clipboard', is_flag=True, help='Grade submission from clipboard instead of file')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'csv']), default='text', help='Output format')
@click.option('--save/--no-save', default=True, help='Save the graded submission')
@click.pass_context
def grade(ctx, discussion_id, file_path, clipboard, format, save):
    """Grade a single submission file or clipboard content."""
    from controllers.submission import SubmissionController
    
    controller = SubmissionController()
    
    if clipboard:
        result = controller.grade_clipboard(
            discussion_id=discussion_id,
            save=save,
            format_type=format
        )
    elif file_path:
        result = controller.grade(
            discussion_id=discussion_id,
            file_path=file_path,
            save=save,
            format_type=format
        )
    else:
        click.echo("ERROR: Either provide a file path or use --clipboard flag")
        return
    
    click.echo(result)

@submission.command()
@click.argument('discussion_id', type=int)
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.pass_context
def list(ctx, discussion_id, format):
    """List all submissions for a discussion."""
    from controllers.submission import SubmissionController
    
    controller = SubmissionController()
    result = controller.list_submissions(
        discussion_id=discussion_id,
        format_type=format
    )
    
    click.echo(result)

@submission.command()
@click.argument('discussion_id', type=int)
@click.argument('submission_id', type=int)
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'csv']), default='text', help='Output format')
@click.pass_context
def show(ctx, discussion_id, submission_id, format):
    """Show details for a specific submission."""
    from controllers.submission import SubmissionController
    
    controller = SubmissionController()
    result = controller.show_submission(
        discussion_id=discussion_id,
        submission_id=submission_id,
        format_type=format
    )
    
    click.echo(result)

@submission.command()
@click.argument('discussion_id', type=int)
@click.option('--save/--no-save', default=True, help='Save the graded submissions')
@click.pass_context
def batch(ctx, discussion_id, save):
    """Grade submissions in interactive clipboard-based batch mode."""
    from controllers.submission import SubmissionController
    
    controller = SubmissionController()
    result = controller.clipboard_batch_grading(
        discussion_id=discussion_id,
        save=save
    )
    
    click.echo(result)


@cli.group()
@click.pass_context
def report(ctx):
    """Generate reports and synthesized content."""
    pass

@report.command()
@click.argument('discussion_id', type=int)
@click.option('--min-score', '-s', type=float, help='Minimum score threshold for inclusion')
@click.option('--max-score', '-m', type=float, help='Maximum score threshold for inclusion')
@click.option('--grade-filter', '-g', help='Filter by letter grade (A, B, C, etc.)')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'csv', 'table']), default='text', help='Output format')
@click.pass_context
def generate(ctx, discussion_id, min_score, max_score, grade_filter, format):
    """Generate a synthesized report from submissions."""
    from controllers.reporting import ReportController
    
    controller = ReportController()
    result = controller.generate(
        discussion_id=discussion_id,
        min_score=min_score,
        max_score=max_score,
        grade_filter=grade_filter,
        format_type=format
    )
    
    click.echo(result)

@report.command()
@click.argument('discussion_id', type=int)
@click.argument('output_file', type=click.Path())
@click.option('--min-score', '-s', type=float, help='Minimum score threshold for inclusion')
@click.option('--max-score', '-m', type=float, help='Maximum score threshold for inclusion')
@click.option('--grade-filter', '-g', help='Filter by letter grade (A, B, C, etc.)')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'csv', 'table']), default='text', help='Export format')
@click.pass_context
def export(ctx, discussion_id, output_file, min_score, max_score, grade_filter, format):
    """Export a synthesized report to a file."""
    from controllers.reporting import ReportController
    
    controller = ReportController()
    result = controller.export(
        discussion_id=discussion_id,
        output_file=output_file,
        min_score=min_score,
        max_score=max_score,
        grade_filter=grade_filter,
        format_type=format
    )
    
    click.echo(result)

@report.command()
@click.argument('discussion_id', type=int)
@click.pass_context
def stats(ctx, discussion_id):
    """Show statistics for a discussion."""
    from controllers.reporting import ReportController
    
    controller = ReportController()
    result = controller.get_statistics(discussion_id)
    
    click.echo(result)

@report.command()
@click.pass_context
def list(ctx):
    """List discussions available for reporting."""
    from controllers.reporting import ReportController
    
    controller = ReportController()
    result = controller.list_available_discussions()
    
    click.echo(result)

if __name__ == '__main__':
    cli(obj={})
