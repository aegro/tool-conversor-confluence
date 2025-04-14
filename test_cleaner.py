#!/usr/bin/env python3
"""
Test script for running the HTMLCleaner on a test file
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.html_cleaner import HTMLCleaner

def main():
    """Main function to run the test"""
    
    # Define file paths
    input_file = Path("test_emoji_and_bullet.html")
    output_file = Path("test_output.html")
    output_dir = Path.cwd()
    
    print(f"Processing file: {input_file}")
    
    # Read the input file
    html_content = input_file.read_text(encoding="utf-8")
    
    # Create the HTML cleaner
    cleaner = HTMLCleaner(html_content, output_dir)
    
    # Process the HTML
    cleaned_html = cleaner.clean()
    
    # Write the output
    output_file.write_text(cleaned_html, encoding="utf-8")
    
    print(f"Processed file saved to: {output_file}")
    
if __name__ == "__main__":
    main() 