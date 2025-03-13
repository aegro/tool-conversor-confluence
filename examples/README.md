# Examples

This directory contains example use cases and configurations for the Tool Conversor Confluence.

## Directory Structure

- `basic_export/` - Basic example of converting a Confluence export
- `custom_config.yaml` - Example custom configuration file
- `advanced_export/` - Advanced configuration with DOCX conversion
- `document_tree_examples/` - Examples of document tree outputs

## Basic Confluence Export Processing

To process a basic Confluence export, follow these steps:

1. Export your Confluence space using the following options:
   - Export Format: HTML
   - Export Type: Custom Export (select all pages)
   - Include Comments: Optional
   - Include Attachments: Yes

2. Extract the exported ZIP file to a directory.

3. Process using the default settings:
   ```bash
   python ../main.py -i ./my_export -o ./processed_output
   ```

## Custom Configuration

The `custom_config.yaml` file demonstrates various configuration options:

```bash
python ../main.py --config custom_config.yaml
```

## Advanced Export with DOCX Conversion

For converting HTML exports to DOCX format:

```bash
python ../main.py -i ./advanced_export -o ./docx_output --create-docx
```

## Document Tree Generation

To generate a document tree in different formats:

```bash
# Tree format (markdown)
python ../main.py -i ./my_export -o ./output --generate-tree --tree-format tree

# Table format (CSV)
python ../main.py -i ./my_export -o ./output --generate-tree --tree-format table --tree-separator ","
```

## Coming Soon

Additional examples that demonstrate:
- Custom styling templates
- Integration with other documentation systems
- Batch processing multiple exports 