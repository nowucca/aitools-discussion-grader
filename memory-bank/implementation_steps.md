# Implementation Steps: Multi-Discussion Grading System

This document provides a detailed roadmap for implementing the Multi-Discussion Grading System. Each phase is broken down into specific steps with prerequisites, tasks, and expected outcomes to enable focused, incremental development.

## Phase 1: Core Architecture

### Step 1.1: Project Structure Setup ✅ (COMPLETED)

**Goal**: Create the basic directory structure and configuration for the project.

**Prerequisites**: None

**Tasks**:
1. Create the following directory structure:
   ```
   discussion-grader/
   ├── grader.py                # Main CLI entry point
   ├── config/                  # Configuration files
   │   └── config.json          # Global configuration
   ├── discussions/             # Discussion data storage
   ├── lib/                     # Library layer
   │   ├── __init__.py
   │   ├── discussion.py
   │   ├── submission.py
   │   ├── reporting.py
   │   ├── config.py
   │   └── ai.py
   ├── controllers/             # Controller layer
   │   ├── __init__.py
   │   ├── discussion.py
   │   ├── submission.py
   │   └── reporting.py
   └── tests/                   # Test suite
       ├── conftest.py
       ├── unit/
       │   ├── lib/
       │   └── controllers/
       └── integration/
   ```

2. Create initial `config.json` with basic settings:
   ```json
   {
     "synthesis": {
       "prompt": "You are synthesizing student responses to create a comprehensive instructor response. Extract key insights, identify common themes, and highlight unique perspectives.",
       "max_submissions": 50
     },
     "grading": {
       "default_points": 12,
       "default_min_words": 300
     }
   }
   ```

3. Set up initial requirements.txt:
   ```
   click>=8.0.0
   anthropic>=0.3.0
   pytest>=7.0.0
   pyperclip>=1.8.0
   ```

**Expected Outcome**:
- Complete directory structure ready for implementation ✅
- Basic configuration file in place ✅
- Initial dependencies defined ✅
- Basic framework code for config management and AI integration ✅

### Step 1.2: Library Layer - Discussion Manager ✅ (COMPLETED)

**Goal**: Implement the core Discussion Manager class that handles discussion creation, listing, and management.

**Prerequisites**: Step 1.1

**Tasks**:
1. Implement `lib/discussion.py` with the following:
   - `DiscussionManager` class with:
     - `create_discussion(title, points, min_words)`
     - `get_discussion(discussion_id)`
     - `list_discussions()`
     - `update_discussion(discussion_id, **kwargs)`
   - Helper functions for file operations
   
2. Create unit tests in `tests/unit/lib/test_discussion.py`
   - Test discussion creation
   - Test listing discussions
   - Test retrieving a discussion
   - Test updating a discussion

3. Extract and refactor relevant code from existing files:
   - Create a file storage system based on patterns from grade_discussion.py
   - Move utility functions like read_file() from grade_discussion.py to appropriate utility modules
   - Implement discussion metadata storage based on the existing question handling

**Expected Outcome**:
- Functioning Discussion Manager with file storage ✅
- Ability to create, retrieve, list, and update discussions ✅
- Successful migration of relevant functionality from existing codebase ✅
- Unit tests passing ✅
- Added Discussion model class using dataclasses for better code organization ✅

### Step 1.3: Library Layer - Initial AI Integration ✅ (COMPLETED)

**Goal**: Implement the AI service for grading submissions.

**Prerequisites**: Step 1.1

**Tasks**:
1. Implement `lib/ai.py` with:
   - `AIGrader` class with:
     - `grade_submission(question, submission, total_points)`
     - Proper error handling for API issues
     - JSON response parsing

2. Create unit tests in `tests/unit/lib/test_ai.py`:
   - Test grade_submission with mocked Anthropic responses
   - Test error handling

3. Migrate AI integration code from grade_discussion.py:
   - Refactor grade_with_claude() function into the AIGrader class
   - Preserve error handling and JSON response parsing logic
   - Adapt the Claude prompt to work with different discussion types

**Expected Outcome**:
- AI integration layer that handles Claude API interactions ✅
- Proper JSON response parsing ✅
- Error handling for API issues ✅
- Successful migration of Claude API interaction code ✅
- Unit tests with mocked responses ✅
- Data models (GradingCriteria, enhanced Submission, GradedSubmission) ✅
- Adaptable prompts for different discussion types ✅

### Step 1.4: Controller Layer - Discussion Controller ✅ (COMPLETED)

**Goal**: Create the controller that bridges between CLI and library for discussion operations.

**Prerequisites**: Steps 1.2

**Tasks**:
1. Implement `controllers/discussion.py` with:
   - `DiscussionController` class with:
     - `create(title, points, min_words)`
     - `list(format_type='table')`
     - `show(discussion_id)`
     - `update(discussion_id, **kwargs)`
   - Format conversion methods (table, JSON, CSV)

2. Create unit tests in `tests/unit/controllers/test_discussion_controller.py`:
   - Test controller with mocked library layer
   - Test format conversions

3. Adapt command-line argument handling from grade_discussion.py:
   - Migrate relevant argparse code to the appropriate Click commands
   - Ensure backward compatibility with existing CLI patterns

**Expected Outcome**:
- Controller that transforms CLI inputs to library calls ✅
- Different output format support ✅
- Preservation of existing CLI functionality ✅
- Unit tests with mocked library ✅

### Step 1.5: CLI Framework Setup ✅ (COMPLETED)

**Goal**: Create the main CLI entry point with Click framework.

**Prerequisites**: Steps 1.2, 1.4

**Tasks**:
1. Implement `grader.py` with:
   - Basic Click setup ✅
   - Command groups for 'discussion', 'submission', 'report' ✅
   - Discussion commands mapped to controller ✅
   - Submission commands mapped to controller ✅
   - Global options (--verbose, --quiet) ✅

2. Create functional tests:
   - Test CLI commands with mocked controllers ✅
   - Test help output ✅

3. Ensure compatibility with existing usage patterns:
   - Support the same options as the original scripts ✅
   - Maintain similar output formatting for consistency ✅
   - Create backward compatibility paths for existing script users ✅

**Expected Outcome**:
- Functioning CLI for discussion operations ✅
- Functioning CLI for submission operations ✅ 
- Command-line help and documentation ✅
- Smooth transition path for users of existing scripts ✅
- Working end-to-end for discussion and submission management ✅

## Phase 2: Enhanced Grading

### Step 2.1: Library Layer - Submission Grader

**Goal**: Implement the Submission Grader that handles grading and storing submissions.

**Prerequisites**: Step 1.3, 1.5

**Tasks**:
1. Implement `lib/submission.py` with:
   - `SubmissionGrader` class with:
     - `grade_submission(discussion_id, file_path)`
     - `save_submission(discussion_id, content, grade_data)`
     - `get_submission(discussion_id, submission_id)`
     - `list_submissions(discussion_id)`

2. Create unit tests in `tests/unit/lib/test_submission.py`

3. Migrate submission handling code:
   - Refactor count_words() function from grade_discussion.py
   - Adapt format_grade_report() into the SubmissionGrader class
   - Integrate format_improvement_suggestions() from batch_grade.py
   - Maintain the question-specific grading logic

**Expected Outcome**:
- Submission grading functionality
- Submission storage in discussion-specific folders
- Successful migration of submission formatting and handling code
- Comprehensive tests

### Step 2.2: Controller Layer - Submission Controller

**Goal**: Implement the controller for submission operations.

**Prerequisites**: Step 2.1

**Tasks**:
1. Implement `controllers/submission.py` with:
   - `SubmissionController` class
   - Methods for grading, listing, viewing submissions
   - Clipboard integration

2. Create unit tests

3. Migrate batch grading functionality:
   - Refactor interactive_grading_loop() from batch_grade.py
   - Adapt get_pasted_submission() to work with the new architecture
   - Preserve the format_grade_summary() functionality

**Expected Outcome**:
- Controller for submission operations
- Format handling for grade reports
- Clipboard support
- Successful migration of batch grading functionality

### Step 2.3: CLI - Submission Commands

**Goal**: Add submission-related commands to the CLI.

**Prerequisites**: Step 2.2

**Tasks**:
1. Update `grader.py` with submission commands:
   - `grader submission grade <disc-id> <file>`
   - `grader submission batch <disc-id>`
   - `grader submission list <disc-id>`

2. Add functional tests

3. Ensure backward compatibility with existing scripts:
   - Map original CLI patterns to new Click commands
   - Support the same output formats and options
   - Provide documentation on migrating from old to new commands

**Expected Outcome**:
- Complete submission grading from CLI
- Batch mode and file mode grading
- Smooth transition for users of existing scripts
- CLI tests for submission functionality

## Phase 3: Synthesis & Reporting

### Step 3.1: Library Layer - Report Generator

**Goal**: Implement the Report Generator for creating synthesized reports.

**Prerequisites**: Step 2.3

**Tasks**:
1. Implement `lib/reporting.py` with:
   - `ReportGenerator` class
   - Methods for synthesizing submissions
   - Filtering and grouping functionality

2. Create unit tests

3. Adapt existing formatting patterns:
   - Use the output formatting from grade_discussion.py as a template
   - Incorporate any reporting patterns from batch_grade.py
   - Ensure consistency with existing output formats

**Expected Outcome**:
- Report generation functionality
- Submission synthesis capabilities
- Filtering by grade or criteria
- Consistency with existing output formatting

### Step 3.2: Controller Layer - Report Controller

**Goal**: Implement the controller for report operations.

**Prerequisites**: Step 3.1

**Tasks**:
1. Implement `controllers/reporting.py` with:
   - `ReportController` class
   - Methods for generating different report types
   - Format conversion

2. Create unit tests

**Expected Outcome**:
- Controller for report operations
- Different output format support
- Unit tests

### Step 3.3: CLI - Report Commands

**Goal**: Add report-related commands to the CLI.

**Prerequisites**: Step 3.2

**Tasks**:
1. Update `grader.py` with report commands:
   - `grader report generate <disc-id>`
   - `grader report export <disc-id>`

2. Add functional tests

**Expected Outcome**:
- Complete report generation from CLI
- Export functionality
- CLI tests for reporting

## Testing Strategy

### Unit Testing

**For Library Layer**:
1. Use pytest fixtures for test setup
2. Mock filesystem operations with `tmp_path` or patch
3. Mock Anthropic API calls
4. Test each class method in isolation
5. Use parameterized tests for various scenarios

**Example Test Structure**:
```python
# tests/unit/lib/test_discussion.py
import pytest
from pathlib import Path
from lib.discussion import DiscussionManager

def test_create_discussion(tmp_path):
    # Arrange
    manager = DiscussionManager(base_dir=str(tmp_path))
    
    # Act
    disc_id = manager.create_discussion("Test", 10, 300)
    
    # Assert
    assert disc_id > 0
    assert (tmp_path / f"discussion_{disc_id}").exists()
    # More assertions...
```

### Integration Testing

1. Test multiple components working together
2. Use temporary directories for real file operations
3. Mock only external dependencies (Anthropic API)

### Functional Testing

1. Test CLI commands using Click's test runner
2. Verify correct command output
3. Test error handling and help text

## Implementation Approach

1. **Incremental Development**:
   - Complete one step before moving to the next
   - Ensure tests pass for each step

2. **Test First Approach**:
   - Write tests before or alongside implementation
   - Verify functionality with tests

3. **Documentation**:
   - Update memory bank as implementation progresses
   - Keep track of decisions and changes

4. **Review Points**:
   - After each major phase, review the implementation
   - Consider refactoring opportunities
