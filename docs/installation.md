# Installation Guide

This guide provides detailed instructions for installing the Tool Conversor Confluence.

## Prerequisites

Before installation, ensure you have the following:

- Python 3.8 or higher
- pip (Python package installer)
- Git (for installation from source)

## Installation Methods

### Method 1: Install from PyPI (Recommended for Users)

The simplest way to install the tool is using pip:

```bash
pip install tool-conversor-confluence
```

This will install the package and its dependencies, and make the `confluence-converter` command available in your environment.

To upgrade to the latest version:

```bash
pip install --upgrade tool-conversor-confluence
```

### Method 2: Install from Source (Recommended for Developers)

1. Clone the repository:

```bash
git clone https://github.com/yourusername/tool-conversor-confluence.git
cd tool-conversor-confluence
```

2. Create and activate a virtual environment (optional but recommended):

```bash
# Create a virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

3. Install the package in development mode:

```bash
pip install -e .
```

This installs the package while allowing you to modify the code without reinstalling.

## Verifying Installation

To verify that the installation was successful, try running:

```bash
# If installed via pip
confluence-converter --help

# If installed from source
python main.py --help
```

You should see the help message with available command-line options.

## Troubleshooting Installation

### Common Issues

#### Missing Dependencies

If you encounter missing dependency errors when running the tool, ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

#### Permission Denied

If you encounter permission issues during installation:

```bash
# On Linux/macOS
pip install --user tool-conversor-confluence

# On Windows, run as administrator or use:
pip install --user tool-conversor-confluence
```

#### Python Version Incompatibility

If you receive an error about Python version requirements, ensure you're using Python 3.8 or higher:

```bash
python --version
```

If needed, upgrade your Python version or use a virtual environment with a compatible version.

## Next Steps

After installation, see the [Usage Guide](usage.md) for instructions on using the tool.
