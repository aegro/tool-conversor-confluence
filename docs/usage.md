# Usage Guide

This guide provides detailed instructions for using the Tool Conversor Confluence to process Confluence HTML exports.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Command-Line Options](#command-line-options)
- [Example Workflows](#example-workflows)
- [Configuration Files](#configuration-files)
- [Document Tree Generation](#document-tree-generation)
- [Converting to DOCX](#converting-to-docx)
- [Advanced Options](#advanced-options)

## Basic Usage

The basic workflow for using the tool involves:

1. Exporting content from Confluence
2. Running the converter tool on the exported files
3. Using the processed HTML or DOCX files as needed

### Step 1: Export from Confluence

1. In Confluence, go to the space you want to export
2. Go to Space Tools > Export
3. Select "HTML" as the export format
4. Choose either "Normal Export" (current page and children) or "Custom Export" (select specific pages)
5. Check "Include Comments" if desired
6. Make sure "Include Attachments" is selected
7. Click "Export" and save the ZIP file

### Step 2: Extract the ZIP File

Extract the ZIP file to a directory on your system. This will be your input directory.

### Step 3: Run the Converter Tool

Basic command to process the exported HTML files:

```bash
# If installed via pip
confluence-converter --input-dir /path/to/extracted/files --output-dir /path/to/output

# If installed from source
python main.py --input-dir /path/to/extracted/files --output-dir /path/to/output
```

## Command-Line Options

The tool provides numerous command-line options for customization:

### Basic Options

| Option | Short | Description |
|--------|-------|-------------|
| `--input-dir` | `-i` | Directory containing HTML files to process |
| `--output-dir` | `-o` | Directory to save processed files |
| `--create-docx` | | Convert HTML to DOCX format |
| `--config` | | Path to custom configuration file |
| `--log-level` | | Set logging level (DEBUG, INFO, WARNING, ERROR) |
| `--log-file` | | Path to log file |
| `--dry-run` | | Show actions without modifying files |

### Document Tree Options

| Option | Description |
|--------|-------------|
| `--generate-tree` | Generate a document tree representation |
| `--tree-format` | Format for the tree ("tree" or "table") |
| `--show-filenames` | Show original filenames in the tree |
| `--hide-filenames` | Hide filenames (show only titles) |
| `--tree-separator` | Separator for table format (default: ";") |

## Example Workflows

### Basic HTML Cleaning

```bash
python main.py -i /path/to/confluence_export -o /path/to/output
```

### Convert HTML to DOCX

```bash
python main.py -i /path/to/confluence_export -o /path/to/output --create-docx
```

### Create Document Tree

```bash
python main.py -i /path/to/confluence_export -o /path/to/output --generate-tree
```

### Use Custom Configuration

```bash
python main.py --config my_config.yaml
```

### Dry Run (Preview Changes)

```bash
python main.py -i /path/to/confluence_export -o /path/to/output --dry-run
```

## Configuration Files

The tool supports YAML configuration files to customize processing behavior. Create a custom configuration file like this:

```yaml
input_directory: '/path/to/input'
output_directory: '/path/to/output'
create_docx: true
log_level: 'INFO'
log_file: 'converter.log'

document_tree:
  format: 'tree'
  separator: ';'
  show_filenames: false
```

See [example_config.yaml](../examples/custom_config.yaml) for a complete example with all available options.

## Document Tree Generation

The document tree feature creates a representation of your Confluence content hierarchy.

### Tree Format (Markdown)

```bash
python main.py -i /path/to/confluence_export -o /path/to/output --generate-tree --tree-format tree
```

Example output:

```
.
├── Home
│   ├── Development
│   │   ├── Coding Standards
│   │   └── Architecture
│   └── Operations
└── Knowledge Base
    ├── FAQs
    └── Troubleshooting
```

### Table Format (CSV)

```bash
python main.py -i /path/to/confluence_export -o /path/to/output --generate-tree --tree-format table
```

Example output:

```
Home;
Home;Development;
Home;Development;Coding Standards;
Home;Development;Architecture;
Home;Operations;
Home;Knowledge Base;
Home;Knowledge Base;FAQs;
Home;Knowledge Base;Troubleshooting;
```

## Converting to DOCX

To convert HTML files to DOCX format:

```bash
python main.py -i /path/to/confluence_export -o /path/to/output --create-docx
```

Note:

- DOCX conversion requires additional dependencies (htmldocx)
- The DOCX files will be saved in the output directory
- The original HTML files are preserved
- Images and formatting are included in the DOCX files
- Tables may require additional formatting in your word processor

## Advanced Options

### Processing Specific Files

To process only specific HTML files, you can use subdirectories:

```bash
python main.py -i /path/to/confluence_export/specific_subdir -o /path/to/output
```

### Changing Log Verbosity

For troubleshooting, increase the log level:

```bash
python main.py -i /path/to/input -o /path/to/output --log-level DEBUG
```

### Custom CSS Styling

The tool applies custom CSS styles by default. To modify the styles, edit the `_inject_custom_styles` method in `html_cleaner.py`.

For more examples, see the [examples directory](../examples/).
