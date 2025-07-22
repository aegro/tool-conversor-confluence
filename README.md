# Tool Conversor Confluence

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A comprehensive command-line tool for processing Confluence HTML exports—cleaning up the HTML, converting it to DOCX, and organizing file structures based on breadcrumbs. This tool is designed to help migrate content from Confluence while maintaining document structure and formatting.

## Table of Contents

1. [Why This Tool?](#why-this-tool)
2. [Features](#features)  
3. [Prerequisites](#prerequisites)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Usage](#usage)  
7. [Running the Document Tree Generator](#running-the-document-tree-generator)  
8. [Testing](#testing)  
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)
11. [License](#license)

---

## Why This Tool?

Migrating documentation from Confluence can be challenging due to Confluence's specific HTML markup and structure. This tool addresses several common migration challenges:

- **Cleaning up Confluence-specific code**: Removes Confluence-specific classes, scripts, and unnecessary elements.
- **Standardizing HTML**: Produces clean, standardized HTML that can be easily converted to other formats.
- **Preserving document structure**: Maintains document hierarchy through breadcrumb-based organization.
- **Resource handling**: Properly processes and relocates images and attachments.
- **Document hierarchy visualization**: Generates a tree view or tabular representation of your documentation structure.

If you're looking to migrate from Confluence while maintaining document quality and structure, this tool provides an automated solution to streamline the process.

---

## Features

* **HTML to Markdown Conversion**
  - Convert Confluence HTML to clean Markdown
  - Preserve document structure and formatting
  - Handle images and attachments as separate files
  - Support for tables, code blocks, and other Markdown elements
  - Configurable output options

* **HTML Cleaning**
  - Removes Confluence-specific classes, scripts, and elements
  - Standardizes HTML structure and formatting
  - Preserves document structure and styling
  - Handles tables, lists, and other complex elements

* **Document Organization**
  - Organizes files based on breadcrumb hierarchy
  - Preserves document relationships and structure
  - Handles duplicate filenames intelligently

* **Format Conversion**
  - Converts cleaned HTML to well-formatted DOCX documents
  - Maintains document structure in the output
  - Preserves images and other embedded content

* **Resource Management**
  - Processes and relocates images and attachments
  - Handles both local and remote resources
  - Maintains proper file references

* **Documentation Tools**
  - Generates document tree in multiple formats (table, tree)
  - Supports custom separators and formatting
  - Can include or exclude filenames from the tree view

---

## Prerequisites

Make sure you have the following installed on your system:

* **Python 3.8+**  
* **pip** (Python package installer)
* **libxml2** and **libxslt** development packages (required for lxml)
  - On macOS: `brew install libxml2 libxslt`
  - On Ubuntu/Debian: `sudo apt-get install libxml2-dev libxslt1-dev`
  - On CentOS/RHEL: `sudo yum install libxml2-devel libxslt-devel`

---

## Installation

### From Source (Recommended for Development)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/tool-conversor-confluence.git
   cd tool-conversor-confluence
   ```

2. **Run the setup script** (creates venv and installs dependencies):

   ```bash
   ./prep_python_virtualev.sh
   ```
   
   This will:
   - Create a Python virtual environment
   - Activate the environment
   - Install all required dependencies
   - Set up the project for development

### Using pip (For End Users)

```bash
pip install tool-conversor-confluence
```

### Quick Start

After installation, you can verify the tool is working correctly by running:

```bash
python main.py --help
```

This should display the available command-line options and their descriptions.

---

## Configuration

Create a `config.yaml` file in your project directory or modify the default configuration in `config/default_config.yaml`. The following settings are available:

### Basic Settings

```yaml
# Basic settings
input_directory: 'input/REL'  # Input directory containing Confluence HTML exports
output_directory: 'output/'   # Base output directory
create_docx: false           # Set to true to enable DOCX conversion
log_level: 'INFO'            # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_file: 'html_processor.log'  # Log file path

# Markdown Conversion
markdown:
  enabled: true              # Enable Markdown output
  output_dir: 'markdown'     # Subdirectory for markdown output
  image_dir: 'images'        # Subdirectory for images (relative to markdown file)
  image_output: 'images'     # Where to store images (relative to output_dir)
  extensions:                # Markdown extensions to enable
    - tables
    - fenced_code
    - footnotes
  code_style: 'github'      # Code block style (github, fenced, etc.)
  preserve_internal_links: true  # Convert internal links to markdown links
  flatten_output: false     # Output all markdown files in a single directory
```

### HTML Cleaning Settings

```yaml
# HTML cleaning settings
standard_html_classes:
  # Define standard classes to preserve during cleaning
  table: ['sortable']
  td: ['selected', 'header']
  # ... other element classes

image_settings:
  border_color: '#00c65e'  # Border color for images
  border_width: '1px'      # Border width for images
  allowed_attrs: ['src', 'alt', 'width', 'height', 'title', 'style']

# Filename processing
filename_settings:
  preserve_spaces: true     # Preserve spaces in filenames
  replace_character: '-'    # Character to replace spaces with if not preserved
  sanitize_characters: true # Remove special characters from filenames
  url_safe_filenames: true  # Ensure filenames are URL-safe

# HTTP settings for external resources
http_settings:
  timeout: 30               # Request timeout in seconds
  max_retries: 3            # Maximum retry attempts
  user_agent: 'HTML Processor Bot/1.0'  # User agent for HTTP requests

# Document tree generation
document_tree:
  format: 'table'          # 'table' or 'tree'
  separator: ';'           # Separator for table format
  show_filenames: false    # Whether to show filenames in the tree
```

* Adjust paths (e.g., `input_directory`, `output_directory`) as needed.  
* If you need a custom configuration file, create your own YAML file and pass its path with the `--config` option.

### Custom Configuration Example

Create a file `my_config.yaml`:

```yaml
input_directory: '/path/to/my/confluence_exports'
output_directory: '/path/to/my/clean_output'
create_docx: true
log_level: 'DEBUG'

document_tree:
  format: 'tree'
  show_filenames: true
```

Then use it with:

```bash
python main.py --config my_config.yaml
```

---

## Usage

Below are some common command-line options for processing Confluence HTML exports:

```bash
python main.py --input-dir <PATH_TO_HTML_FILES> \
               --output-dir <OUTPUT_PATH> \
               [--create-docx] \
               [--log-level {DEBUG,INFO,WARNING,ERROR}] \
               [--log-file <LOG_FILE_PATH>] \
               [--dry-run] \
               [--config <PATH_TO_YOUR_CONFIG>] \
               [--generate-tree] \
               [--tree-format {tree,table}] \
               [--show-filenames | --hide-filenames] \
               [--tree-separator <SEPARATOR>]
```

### Command-Line Options

#### Basic Options

* **--input-dir** (or **-i**): The directory containing your exported HTML files.  
* **--output-dir** (or **-o**): The directory where cleaned (and optionally DOCX) files will be saved.  
* **--create-docx**: Converts cleaned HTML to DOCX.  
* **--log-level**: Sets the verbosity of the log output. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`.  
* **--log-file**: Appends log entries to a specified file.  
* **--dry-run**: Prints the actions that would be taken but does not modify files.  
* **--config**: Points to your own custom YAML configuration file.

#### Document Tree Options

* **--generate-tree**: Generate a document tree representation after processing files.
* **--tree-format**: Format for the document tree (`tree` or `table`). Default is `table`.
* **--show-filenames**: Show original filenames in the document tree.
* **--hide-filenames**: Hide original filenames in the document tree (show only document titles).
* **--tree-separator**: Separator for `table` format output. Default is `;`.

### Common Usage Examples

**Basic HTML Cleaning**:
```bash
python main.py -i /path/to/confluence_exports -o /path/to/output
```

**Clean HTML and Convert to DOCX**:
```bash
python main.py -i /path/to/confluence_exports -o /path/to/output --create-docx
```

**Process HTML and Generate a Document Tree**:
```bash
python main.py -i /path/to/confluence_exports -o /path/to/output --generate-tree --tree-format tree
```

**Run in Debug Mode with Custom Configuration**:
```bash
python main.py --config my_config.yaml --log-level DEBUG
```

**Test Run Without Modifying Files**:
```bash
python main.py -i /path/to/confluence_exports -o /path/to/output --dry-run
```

---

## Running the Document Tree Generator

You can generate a document tree representation of your Confluence content in two ways:

### 1. Using the main script (recommended)

Use the main application with the `--generate-tree` option:

```bash
python main.py --input-dir /path/to/confluence_exports \
               --output-dir /path/to/output \
               --generate-tree \
               --tree-format tree \
               --show-filenames
```

This approach has the advantage of integrating with the rest of the application workflow and using the same configuration.

### 2. Using the standalone document tree module

For generating a document tree without processing files, you can use the document tree module directly:

```bash
python -m core.document_tree \
  --input-dir /path/to/cleaned_html \
  --output-dir /path/to/output/tree \
  --format table \
  --show-filenames
```

### Document Tree Output Examples

**Tree Format Sample**:
```
.
├── Space Home
│   ├── Product Documentation
│   │   ├── User Guide
│   │   │   ├── Getting Started
│   │   │   └── Advanced Features
│   │   └── API Reference
│   └── Technical Specs
└── Knowledge Base
    ├── FAQs
    └── Troubleshooting
```

**Table Format Sample**:
```
Space Home;
Space Home;Product Documentation;
Space Home;Product Documentation;User Guide;
Space Home;Product Documentation;User Guide;Getting Started;
Space Home;Product Documentation;User Guide;Advanced Features;
Space Home;Product Documentation;API Reference;
Space Home;Technical Specs;
Space Home;Knowledge Base;
Space Home;Knowledge Base;FAQs;
Space Home;Knowledge Base;Troubleshooting;
```

---

## Testing

We use **pytest** for unit tests. To run the tests:

```bash
pytest
```

For more detailed test output:

```bash
pytest -v
```

To run tests with coverage reporting:

```bash
pytest --cov=core --cov=utils --cov-report=term-missing
```

---

## Troubleshooting

### Common Issues

#### Permission Errors
* **Issue**: You encounter permission issues when writing to output directories.
* **Solution**: Ensure your Python environment has write access to the specified output directory.

#### Missing Dependencies
* **Issue**: Import errors when running the tool.
* **Solution**: Verify all required Python packages are installed by running `pip install -r requirements.txt`.

#### HTML Processing Errors
* **Issue**: HTML files are not processed correctly.
* **Solution**: Run with `--log-level DEBUG` to get detailed information about the processing steps.

#### Image Path Problems
* **Issue**: Images are not displayed correctly in processed HTML.
* **Solution**: Check that the image paths in the original HTML are correct and that the `--output-dir` is correctly specified.

### Getting Help

If you encounter issues not covered here, please:
1. Check the existing issues on GitHub
2. Open a new issue with detailed information about your problem

---

## Contributing

We welcome contributions to improve the tool! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to the project.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Happy migrating from Confluence!
