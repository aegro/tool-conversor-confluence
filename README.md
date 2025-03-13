# Tool Conversor Confluence

[![GitHub Actions](https://github.com/yourusername/tool-conversor-confluence/actions/workflows/python-tests.yml/badge.svg)](https://github.com/yourusername/tool-conversor-confluence/actions/workflows/python-tests.yml)
[![PyPI version](https://badge.fury.io/py/tool-conversor-confluence.svg)](https://badge.fury.io/py/tool-conversor-confluence)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/tool-conversor-confluence.svg)](https://pypi.org/project/tool-conversor-confluence/)

A robust command-line tool for processing Confluence HTML exports—cleaning up the HTML, converting it to DOCX (optional), and organizing file structures based on breadcrumbs.

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

* Cleans Confluence-specific classes and scripts from exported HTML.  
* Organizes files based on breadcrumb hierarchy.  
* Converts HTML files to DOCX (optional).  
* Generates a markdown or CSV document tree representation of your Confluence exports.
* Handles image and attachment resources properly.
* Preserves document styling while removing Confluence-specific elements.

---

## Prerequisites

Make sure you have the following installed on your system:

* **Python 3.8+**  
* **pip** (Python package installer)

---

## Installation

### From Source (Recommended for Development)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/tool-conversor-confluence.git
   cd tool-conversor-confluence
   ```

2. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

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

The default configuration is stored in:

```yaml
# config/default_config.yaml
input_directory: 'io/SI'
output_directory: 'io'
create_docx: false
log_level: 'INFO'
log_file: 'html_processor.log'

document_tree:
  format: 'table'
  separator: ';'
  show_filenames: false
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
