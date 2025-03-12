# Contributing to Tool Conversor Confluence

Thank you for your interest in contributing to the Tool Conversor Confluence project! This document provides guidelines and instructions for contributing to the codebase.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Structure](#code-structure)
3. [Coding Standards](#coding-standards)
4. [Documentation Guidelines](#documentation-guidelines)
5. [Testing](#testing)
6. [Pull Request Process](#pull-request-process)
7. [Issue Reporting](#issue-reporting)

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

### Setting Up Your Development Environment

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/tool-conversor-confluence.git
   cd tool-conversor-confluence
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Code Structure

The project is organized as follows:

- `main.py`: Application entry point and CLI implementation
- `core/`: Core functionality modules
  - `file_processor.py`: Handles file processing operations
  - `html_cleaner.py`: Cleans HTML content from Confluence exports
  - `document_tree.py`: Generates document tree representations
- `utils/`: Utility functions and helpers
- `config/`: Configuration files
- `io/`: Input/output directory for file processing
- `test_main.py`: Test suite

## Coding Standards

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for code style
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 88 characters
- Use meaningful variable and function names
- Use type hints for function parameters and return values

### Command-Line Interface Design

We follow these principles for command-line interfaces:

1. **Single Entry Point**: The primary CLI should be implemented in `main.py`, which serves as the main entry point for the application.

2. **Library vs. CLI Separation**:
   - Core modules should be designed as libraries without direct CLI functionality
   - If a module needs standalone CLI capabilities (like `document_tree.py`), it should:
     - Implement CLI code only in the `main()` function and under `if __name__ == "__main__"`
     - Include documentation to refer users to the main entry point

3. **Argument Consistency**: Command-line arguments should be consistent across the application:
   - Use the same argument names for the same functionality
   - Document all arguments in the README.md file
   - Group related arguments using `add_argument_group()`

4. **Unified Configuration**: The CLI should integrate with the configuration system:
   - Command-line arguments should override config file values
   - Document the relationship between arguments and configuration

5. **No Redundant Parse Calls**: Never call `parse_args()` from imported modules, as this will capture CLI arguments intended for the main script.

### Imports

- Group imports in the following order:
  1. Standard library imports
  2. Related third-party imports
  3. Local application imports
- Within each group, sort imports alphabetically

### Docstrings

- Use docstrings for all modules, classes, and functions
- Follow the Google docstring style:

```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description of the function.
    
    Detailed description of the function's purpose and behavior.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of what the function returns
        
    Raises:
        ExceptionType: When and why this exception is raised
    """
```

## Documentation Guidelines

### Code Documentation

1. **Module Documentation**: Every module should have a docstring at the top explaining its purpose and functionality.

2. **Class Documentation**: All classes should have docstrings explaining their purpose, attributes, and usage.

3. **Method Documentation**: All methods should have docstrings explaining parameters, return values, and raised exceptions.

4. **Inline Comments**: Use inline comments to explain complex logic or non-obvious decisions.

### External Documentation

1. **README.md**: Keep the README up-to-date with installation instructions, usage examples, and configuration options.

2. **CONTRIBUTING.md**: This file (which you're reading now) for contribution guidelines.

3. **Documentation in Code**: Ensure code examples in documentation are accurate and up-to-date.

## Testing

### Running Tests

To run all tests:

```bash
python -m unittest discover
```

Or with pytest:

```bash
pytest
```

### Writing New Tests

1. Add new test methods to the existing test classes in `test_main.py`
2. For new components, create new test classes
3. Ensure each test method tests a single functionality
4. Name test methods descriptively (e.g., `test_remove_confluence_classes`)
5. Use mocks for external dependencies

### Test Coverage

Aim for high test coverage, especially for core functionality:

```bash
pytest --cov=. --cov-report=term
```

## Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the coding standards
3. **Add or update tests** as needed
4. **Update documentation** for any changed functionality
5. **Ensure all tests pass**
6. **Submit a pull request** with a clear description of the changes

Your pull request should include:

- A reference to any related issues
- A summary of changes made
- Any additional information needed to understand the changes

## Issue Reporting

When reporting issues, please include:

1. A clear description of the issue
2. Steps to reproduce the problem
3. Expected behavior
4. Actual behavior
5. Environment information (OS, Python version)
6. If possible, a minimal example demonstrating the issue

## License

By contributing to this project, you agree that your contributions will be licensed under the project's license.

Thank you for contributing to Tool Conversor Confluence!
