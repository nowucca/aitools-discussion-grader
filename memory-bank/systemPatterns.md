# System Patterns: Multi-Discussion Grading System

## System Architecture

We are implementing a clean, layered architecture that separates concerns and promotes testability and maintainability.

```mermaid
graph TD
    CLI[CLI Layer] --> CONTROLLER[Controller Layer]
    CONTROLLER --> LIB[Library Layer]
    
    subgraph CLI Layer
        CMD_D[Discussion Commands]
        CMD_S[Submission Commands] 
        CMD_R[Report Commands]
        CMD_C[Config Commands]
    end
    
    subgraph Controller Layer
        CTRL_D[Discussion Controller]
        CTRL_S[Submission Controller]
        CTRL_R[Report Controller]
        CTRL_C[Config Controller]
    end
    
    subgraph Library Layer
        DISC[Discussion Manager]
        SUB[Submission Grader]
        REP[Report Generator]
        CONF[Configuration Manager]
        CLIP[Clipboard Utils]
        AI[AI Integration]
        MODELS[Domain Models]
    end
    
    CMD_D --> CTRL_D --> DISC
    CMD_S --> CTRL_S --> SUB
    CMD_R --> CTRL_R --> REP
    CMD_C --> CTRL_C --> CONF
    DISC --> MODELS
    SUB --> MODELS
```

### 1. CLI Layer (Presentation)
- Handles command-line parsing and user interaction
- Built with Click framework
- Follows noun-verb command pattern
- Responsible for formatting output for user consumption
- Passes commands to the Controller layer

### 2. Controller Layer (Application)
- Acts as a bridge between CLI and Library layers
- Transforms CLI options to library parameters
- Handles formatting and presentation logic
- Orchestrates calls to multiple library components when needed
- Not concerned with business logic details

### 3. Library Layer (Domain)
- Contains core business logic
- Independent of UI concerns
- Provides services for discussion management, grading, reporting
- Can be reused in different contexts (e.g., future GUI or API)
- Includes domain models that represent business entities

## Key Technical Decisions

### 1. Command Line Interface

We've adopted the **noun-verb pattern** for our CLI, which follows modern conventions for command-line tools:

```
grader <noun> <verb> [options] [arguments]
```

Examples:
- `grader discussion create --title "Week 1 Discussion"`
- `grader submission grade 3 student1.md --clipboard`
- `grader report generate 3 --min-grade=8`

We're using **Click** as our CLI framework because it provides:
- Intuitive decorator-based command definition
- Built-in help generation
- Nested command support
- Strong type validation
- Context object for sharing state between commands

### 2. File Organization

```
discussion-grader/
├── grader.py                # Main CLI entry point
├── config/                  # Configuration files
├── discussions/             # Discussion data storage
├── lib/                     # Library layer
├── controllers/             # Controller layer
└── tests/                   # Test suite
```

### 3. Dependency Management

- **Direct Injection**: We pass dependencies directly to classes and functions rather than using global state
- **Composition Over Inheritance**: We compose functionality through object composition rather than deep inheritance hierarchies

### 4. Error Handling

- **Layered Error Handling**: Each layer handles errors appropriate to its level of abstraction
- **CLI Layer**: User-friendly error messages
- **Controller Layer**: Transforms domain exceptions to user-appropriate messages
- **Library Layer**: Domain-specific exceptions

### 5. Domain Models

- **Rich Domain Objects**: Using Python dataclasses to create rich domain models rather than plain dictionaries
- **Serialization Methods**: Models include to_dict() and from_dict() methods for storage and retrieval
- **Type Safety**: Leveraging Python type hints for better code safety and IDE assistance
- **Default Values**: Models include sensible defaults to simplify object creation

## Design Patterns

### 1. Command Pattern
The noun-verb CLI structure essentially implements the command pattern, where each command encapsulates all the information needed to perform an action.

### 2. Controller Pattern
The controllers act as intermediaries between the CLI and library layers, handling the transformation of CLI input to domain operations.

### 3. Repository Pattern
The Discussion Manager and Submission Grader implement the repository pattern for storing and retrieving discussions and submissions.

### 4. Facade Pattern
Each major library component provides a simplified interface to a more complex subsystem (e.g., AI Grader encapsulates all the complexity of interacting with the Claude API).

### 5. Strategy Pattern
Different formatting strategies (table, JSON, CSV) can be selected at runtime.

### 6. Domain Model Pattern
We use rich domain models (e.g., Discussion class) that encapsulate both data and behavior, following Domain-Driven Design principles.

## Critical Implementation Paths

### 1. Discussion Management Flow

```mermaid
sequenceDiagram
    CLI->>Controller: create_discussion(title, points)
    Controller->>Library: create_discussion(title, points)
    Library->>Filesystem: Create directory structure
    Library->>Filesystem: Write metadata.json
    Library->>Filesystem: Create question template
    Library-->>Controller: Return discussion ID
    Controller-->>CLI: Return formatted result
```

### 2. Grading Flow

```mermaid
sequenceDiagram
    CLI->>Controller: grade_submission(disc_id, file_path)
    Controller->>Library: load_discussion(disc_id)
    Library-->>Controller: Return discussion data
    Controller->>Library: grade_submission(question, submission)
    Library->>AI Service: Send grading request
    AI Service-->>Library: Return grade and feedback
    Library->>Filesystem: Save grade report
    Library->>Filesystem: Save submission copy
    Library-->>Controller: Return grade data
    Controller->>Clipboard: [If requested] Copy to clipboard
    Controller-->>CLI: Return formatted grade report
```

### 3. Synthesis Flow

```mermaid
sequenceDiagram
    CLI->>Controller: generate_report(disc_id, min_grade)
    Controller->>Library: load_discussion(disc_id)
    Library-->>Controller: Return discussion data
    Controller->>Library: load_submissions(disc_id, min_grade)
    Library-->>Controller: Return filtered submissions
    Controller->>Library: generate_synthesis(question, submissions)
    Library->>AI Service: Send synthesis request
    AI Service-->>Library: Return synthesized content
    Library-->>Controller: Return synthesis
    Controller->>Clipboard: [If requested] Copy to clipboard
    Controller-->>CLI: Return formatted synthesis
```

## Domain Models

### Discussion Model

```mermaid
classDiagram
    class Discussion {
        +int id
        +string title
        +int points
        +int min_words
        +string created_at
        +string updated_at
        +string question_file
        +string question_content
        +to_dict()
        +from_dict()
    }

    class DiscussionManager {
        +create_discussion()
        +get_discussion()
        +list_discussions()
        +update_discussion()
    }

    DiscussionManager --> Discussion : manages
```

The Discussion model serves as the primary domain entity for discussion-related data:
- Implemented as a Python dataclass for clean, type-safe code
- Contains all discussion metadata (ID, title, points, etc.)
- Includes methods for serialization to/from dictionaries
- Used by the DiscussionManager for CRUD operations
- Provides a clear contract between layers of the application
