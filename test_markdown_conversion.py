#!/usr/bin/env python
"""
Test script for Markdown conversion pipeline
Tests the conversion of Confluence HTML exports to Markdown format
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{message:^60}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}\n")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")

def clean_output_directory(output_dir):
    """Clean the output directory if it exists"""
    if output_dir.exists():
        print_info(f"Cleaning existing output directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

def run_conversion(input_dir, output_dir, enable_markdown=True):
    """Run the conversion process"""
    cmd = [
        sys.executable,
        "main.py",
        "--input", str(input_dir),
        "--output", str(output_dir)
    ]
    
    if enable_markdown:
        cmd.append("--markdown")
    
    print_info(f"Running command: {' '.join(cmd)}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    return result, end_time - start_time

def verify_output_structure(output_dir):
    """Verify the expected output directory structure"""
    errors = []
    
    # Check if output directory exists
    if not output_dir.exists():
        errors.append("Output directory does not exist")
        return errors
    
    # Look for any space directory (cleaned HTML) - could be "SA" or "Suporte Aegro"
    space_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name not in ["markdown", "test_output"]]
    if not space_dirs:
        errors.append("No space directory (cleaned HTML) found")
    else:
        # Return the first found space directory name for later use
        errors.append(f"SPACE_NAME:{space_dirs[0].name}")
    
    # Check for markdown directory
    markdown_dir = output_dir / "markdown"
    if not markdown_dir.exists():
        errors.append("Markdown directory not found")
    else:
        # Check for markdown space subdirectory
        markdown_space_dirs = [d for d in markdown_dir.iterdir() if d.is_dir()]
        if not markdown_space_dirs:
            errors.append("No space directory found in markdown output")
    
    return errors

def count_files(directory, extension):
    """Count files with specific extension in directory"""
    if not directory.exists():
        return 0
    return len(list(directory.rglob(f"*{extension}")))

def analyze_output(output_dir, space_name=None):
    """Analyze the conversion output"""
    stats = {}
    
    # Auto-detect space name if not provided
    if not space_name:
        space_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name not in ["markdown", "test_output"]]
        space_name = space_dirs[0].name if space_dirs else "SA"
    
    # Count HTML files
    space_dir = output_dir / space_name
    stats['html_files'] = count_files(space_dir, ".html")
    
    # Count Markdown files
    markdown_dir = output_dir / "markdown" / space_name
    stats['markdown_files'] = count_files(markdown_dir, ".md")
    
    # Count image directories
    image_dirs = list(markdown_dir.rglob("images")) if markdown_dir.exists() else []
    stats['image_directories'] = len(image_dirs)
    
    # Count total images
    total_images = 0
    for img_dir in image_dirs:
        total_images += len(list(img_dir.iterdir()))
    stats['total_images'] = total_images
    
    return stats

def sample_markdown_files(markdown_dir, space_name=None, count=3):
    """Get a sample of markdown files for inspection"""
    if not markdown_dir.exists():
        return []
    
    # If space_name provided, look in that subdirectory
    if space_name:
        search_dir = markdown_dir / space_name
    else:
        search_dir = markdown_dir
    
    md_files = list(search_dir.rglob("*.md")) if search_dir.exists() else []
    return md_files[:count]

def validate_markdown_content(file_path):
    """Check if file contains actual markdown content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read(500)  # Read first 500 chars
        
    # Check for common HTML patterns that shouldn't be in markdown
    html_patterns = ['<!DOCTYPE', '<html', '<head>', '<body>', '<meta', '<style>']
    is_html = any(pattern in content for pattern in html_patterns)
    
    # Check for common markdown patterns
    markdown_patterns = ['# ', '## ', '**', '* ', '- ', '[', '](']
    has_markdown = any(pattern in content for pattern in markdown_patterns)
    
    return not is_html, has_markdown

def main():
    """Main test function"""
    print_header("Confluence to Markdown Conversion Test")
    
    # Setup paths
    project_root = Path(__file__).parent
    input_dir = project_root / "input" / "SA"
    output_dir = project_root / "test_output"
    
    # Verify input directory exists
    if not input_dir.exists():
        print_error(f"Input directory not found: {input_dir}")
        return 1
    
    # Count input files
    input_files = list(input_dir.glob("*.html"))
    print_info(f"Found {len(input_files)} HTML files in input directory")
    
    # Clean output directory
    clean_output_directory(output_dir)
    
    # Run conversion
    print_header("Running Conversion")
    result, duration = run_conversion(input_dir, output_dir, enable_markdown=True)
    
    if result.returncode != 0:
        print_error("Conversion failed!")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        return 1
    
    print_success(f"Conversion completed in {duration:.2f} seconds")
    
    # Verify output structure
    print_header("Verifying Output Structure")
    errors = verify_output_structure(output_dir)
    
    # Extract space name from errors if found
    space_name = None
    real_errors = []
    for error in errors:
        if error.startswith("SPACE_NAME:"):
            space_name = error.split(":", 1)[1]
            print_info(f"Found space directory: {space_name}")
        else:
            real_errors.append(error)
    
    if real_errors:
        for error in real_errors:
            print_error(error)
        return 1
    else:
        print_success("Output directory structure is correct")
    
    # Analyze output
    print_header("Output Analysis")
    stats = analyze_output(output_dir, space_name)
    
    print(f"HTML files (cleaned): {stats['html_files']}")
    print(f"Markdown files: {stats['markdown_files']}")
    print(f"Image directories: {stats['image_directories']}")
    print(f"Total images extracted: {stats['total_images']}")
    
    # Check conversion rate
    if stats['html_files'] > 0:
        conversion_rate = (stats['markdown_files'] / stats['html_files']) * 100
        print(f"\nConversion rate: {conversion_rate:.1f}%")
        
        if conversion_rate < 90:
            print_error(f"Low conversion rate detected ({conversion_rate:.1f}%)")
    
    # Sample some markdown files
    print_header("Sample Markdown Files")
    markdown_dir = output_dir / "markdown"
    sample_files = sample_markdown_files(markdown_dir, space_name, count=3)
    
    validation_errors = 0
    for md_file in sample_files:
        print(f"\n{Colors.BOLD}File: {md_file.name}{Colors.RESET}")
        print(f"Path: {md_file.relative_to(output_dir)}")
        
        # Validate content
        is_not_html, has_markdown = validate_markdown_content(md_file)
        if not is_not_html:
            print_error("File contains HTML instead of Markdown!")
            validation_errors += 1
        elif not has_markdown:
            print_error("File does not contain recognizable Markdown patterns")
            validation_errors += 1
        else:
            print_success("File contains valid Markdown content")
        
        # Show first few lines
        with open(md_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:10]
            print(f"First {len(lines)} lines:")
            for line in lines:
                print(f"  {line.rstrip()}")
    
    if validation_errors > 0:
        print_header("Test Completed with Issues")
        print_error(f"Found {validation_errors} markdown files with invalid content")
        return 1
    else:
        print_header("Test Completed Successfully")
        print_success("All tests passed!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
