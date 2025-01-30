# Tool Conversor Confluence

A command-line application for processing Confluence HTML exports—cleaning up the HTML, optionally converting it to DOCX, and organizing file structures based on breadcrumbs.

## Table of Contents

1. [Features](#features)  
2. [Prerequisites](#prerequisites)  
3. [Installation](#installation)  
4. [Configuration](#configuration)  
5. [Usage](#usage)  
6. [Running the Document Tree Generator](#running-the-document-tree-generator)  
7. [Testing](#testing)  
8. [Troubleshooting](#troubleshooting)

---

## Features

* Cleans Confluence-specific classes and scripts from exported HTML.  
* Organizes files based on breadcrumb hierarchy.  
* Converts HTML files to DOCX (optional).  
* Generates a markdown or CSV document tree representation of your Confluence exports.

---

## Prerequisites

Make sure you have the following installed on your system:

* **Python 3.8+**  
* **pip** (Python package installer)

---

## Installation

1. **Clone the repository** or download the source code.  
2. *(Optional but recommended)* Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

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
               [--config <PATH_TO_YOUR_CONFIG>]
```

### Command-Line Options

* **--input-dir** (or **-i**): The directory containing your exported HTML files.  
* **--output-dir** (or **-o**): The directory where cleaned (and optionally DOCX) files will be saved.  
* **--create-docx**: Converts cleaned HTML to DOCX.  
* **--log-level**: Sets the verbosity of the log output. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`.  
* **--log-file**: Appends log entries to a specified file.  
* **--dry-run**: Prints the actions that would be taken but does not modify files.  
* **--config**: Points to your own custom YAML configuration file.

**Example**:

```bash
python main.py -i /path/to/confluence_exports -o /path/to/output --create-docx
```

---

## Running the Document Tree Generator

A separate script, located in `core/document_tree.py`, builds a document tree from your cleaned HTML. You can run it directly:

```bash
python core/document_tree.py \
  --input-dir /path/to/cleaned_html \
  --output-dir /path/to/output/tree \
  --format table \
  --show-filenames
```

This generates either a Markdown file or CSV (depending on the `--format`) that outlines the hierarchy of your Confluence content.

---

## Testing

We use **pytest** for unit tests. To run the tests:

```bash
pytest
```

Additionally, there are some integration tests in `test_main.py` to ensure the main workflow executes properly.

---

## Troubleshooting

* If you encounter permission issues, ensure your Python environment has the right privileges.  
* Verify all required Python packages are installed by checking `requirements.txt` or re-running `pip install -r requirements.txt`.  
* Use `--log-level DEBUG` to output additional logs for troubleshooting complex issues.

---

Happy coding!