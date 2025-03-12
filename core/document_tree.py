#!/usr/bin/env python3
"""
Document Tree Generator for Confluence HTML Exports

This module provides functionality to generate a hierarchical tree representation
of Confluence HTML exports. The document tree can be exported in various formats:
- Markdown table format
- CSV format
- Plain text indented format

The module extracts breadcrumbs from HTML files to determine the hierarchical 
structure of the documents, and can generate different visual representations
of this structure.

Key features:
- Extracts breadcrumbs from HTML files
- Builds a hierarchical tree structure
- Supports multiple output formats
- Can include/exclude filenames from output
- Handles sorting and indentation of the tree

Usage:
    tree_builder = DocumentTreeBuilder(input_dir, output_dir)
    tree_builder.build_tree()
    tree_builder.export_tree(format='table', separator=';')
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup
import csv  # For CSV export functionality

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.html_cleaner import HTMLCleaner
from core.file_processor import FileProcessor
from utils.utilities import load_config, setup_logging

@dataclass
class TreeNode:
    """
    Represents a node in the document tree.
    
    This class is used to build the hierarchical document tree, where each node
    can have children nodes, representing the breadcrumb hierarchy from Confluence.
    
    Attributes:
        name (str): The name of the node (document title or breadcrumb segment)
        path (Optional[Path]): Path to the document file (None for intermediate nodes)
        children (Dict[str, 'TreeNode']): Dictionary of child nodes, keyed by name
    """
    name: str
    path: Optional[Path] = None
    children: Dict[str, 'TreeNode'] = None
    
    def __post_init__(self):
        """Initialize children dictionary if None."""
        if self.children is None:
            self.children = {}

class DocumentTreeBuilder:
    """
    Builds and exports a hierarchical tree structure from HTML documents.
    
    This class scans HTML files, extracts breadcrumbs to determine their
    hierarchical structure, builds a tree representation, and exports
    it in various formats.
    
    Attributes:
        input_dir (Path): Directory containing processed HTML files
        output_dir (Path): Directory for saving the document tree output
        config (dict): Configuration settings
        logger (logging.Logger): Logger instance
        root (TreeNode): Root node of the document tree
    """
    
    def __init__(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        config: Optional[dict] = None
    ):
        """
        Initialize the DocumentTreeBuilder.
        
        Args:
            input_dir (Union[str, Path]): Path to directory with HTML files
            output_dir (Union[str, Path]): Path to save the document tree output
            config (Optional[dict]): Configuration override. Defaults to None
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.config = config or load_config()
        self.logger = logging.getLogger(__name__)
        self.root = TreeNode(name="root")
        
        # Get tree format configuration
        tree_config = self.config.get('document_tree', {})
        self.format = tree_config.get('format', 'tree')
        self.separator = tree_config.get('separator', ' - ')
        self.show_filenames = tree_config.get('show_filenames', True)
        
        self.logger.info(f"Using document tree format: {self.format}")
        self.logger.info(f"Show filenames: {self.show_filenames}")

    def extract_breadcrumbs(self, html_file: Path) -> Tuple[List[str], str]:
        """Extract breadcrumbs and title from HTML file."""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            cleaner = HTMLCleaner(content, self.output_dir, self.config)
            soup = cleaner.soup
            
            breadcrumb_div = soup.find('div', id='breadcrumb-section')
            if not breadcrumb_div:
                return [], cleaner.title
                
            breadcrumbs = [
                link.text.strip() 
                for link in breadcrumb_div.find_all('a')
                if link.text.strip()
            ]
            
            return breadcrumbs, cleaner.title
            
        except Exception as e:
            self.logger.error(f"Error processing {html_file}: {str(e)}")
            return [], html_file.stem

    def add_to_tree(
        self,
        breadcrumbs: List[str],
        title: str,
        file_path: Path
    ) -> None:
        """Add a document to the tree structure based on its breadcrumbs."""
        current = self.root
        
        # Navigate through breadcrumbs
        for crumb in breadcrumbs:
            if crumb not in current.children:
                current.children[crumb] = TreeNode(name=crumb)
            current = current.children[crumb]
            
        # Add the actual document
        current.children[title] = TreeNode(
            name=title,
            path=file_path.relative_to(self.input_dir)
        )

    def format_link(self, name: str, path: Path) -> str:
        """
        Format a document link based on configuration.
        
        Args:
            name: Document name
            path: Path to document
            
        Returns:
            Formatted link string
        """
        if self.show_filenames:
            return f"[{name}]({path})"
        return name

    def generate_table_format(self, node: TreeNode, parent_path: List[str] = None) -> List[List[str]]:
        """Generate table-like format where each line contains full path."""
        if parent_path is None:
            parent_path = []
            
        rows = []
        current_path = parent_path + [node.name] if node.name != "root" else []
        
        # If this is not the root node, add a line for the current path
        if node.name != "root" and not node.path:
            rows.append([name for name in current_path])
        
        # Sort children by name
        sorted_children = sorted(
            node.children.items(),
            key=lambda x: (not bool(x[1].children), x[0].lower())
        )
        
        # Process children
        for name, child in sorted_children:
            if child.path:
                # This is a document node
                doc_name = f"{name} ({child.path})" if self.show_filenames else name
                doc_path = current_path + [doc_name]
                rows.append(doc_path)
            else:
                # This is a directory node
                rows.extend(self.generate_table_format(child, current_path))
                
        return rows

    def generate_tree_format(self, node: TreeNode, level: int = 0) -> str:
        """Generate traditional tree format."""
        if not node.children and not node.path:
            return ""
            
        markdown = []
        indent = "  " * level
        
        sorted_children = sorted(
            node.children.items(),
            key=lambda x: (not bool(x[1].children), x[0].lower())
        )
        
        for name, child in sorted_children:
            if child.path:
                if self.show_filenames:
                    markdown.append(f"{indent}- [{name}]({child.path})")
                else:
                    markdown.append(f"{indent}- {name}")
            else:
                markdown.append(f"{indent}- **{name}**")
                child_content = self.generate_tree_format(child, level + 1)
                if child_content:
                    markdown.append(child_content)
                    
        return "\n".join(markdown)

    def generate_markdown(self, node: TreeNode, level: int = 0) -> str:
        """Generate markdown representation based on configured format."""
        self.logger.debug(f"Generating markdown in {self.format} format")
        
        if self.format == 'table':
            lines = self.generate_table_format(node)
            return "# Document Structure\n\n" + "\n".join(lines)
        else:
            return "# Document Structure\n\n" + self.generate_tree_format(node, level)

    def build_tree(self) -> None:
        """Build the document tree from HTML files."""
        try:
            html_files = list(self.input_dir.rglob("*.html"))
            self.logger.info(f"Found {len(html_files)} HTML files")
            
            for file_path in html_files:
                breadcrumbs, title = self.extract_breadcrumbs(file_path)
                self.add_to_tree(breadcrumbs, title, file_path)
                
        except Exception as e:
            self.logger.error(f"Error building tree: {str(e)}")
            raise

    def export_markdown(self, dry_run: bool = False) -> str:
        """
        Export the tree structure as markdown or CSV.
        
        Args:
            dry_run: If True, return content without saving
            
        Returns:
            Generated content
        """
        if self.format == 'table':
            # Generate table rows
            rows = self.generate_table_format(self.root)
            
            if not dry_run:
                # Save as CSV
                output_file = self.output_dir / "document_table.csv"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f, delimiter=self.separator)
                    writer.writerows(rows)
                    
                self.logger.info(f"CSV table exported to {output_file}")
                
            # For dry run or return value, convert to string with separator
            return "\n".join(self.separator.join(row) for row in rows)
        else:
            # Original markdown tree format
            markdown_content = self.generate_markdown(self.root)
            
            if not dry_run:
                output_file = self.output_dir / "document_tree.md"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                    
                self.logger.info(f"Markdown tree exported to {output_file}")
                
            return markdown_content

def main():
    """Main entry point for the document tree generator."""
    parser = argparse.ArgumentParser(
        description="Generate a document tree structure from Confluence HTML exports"
    )
    
    parser.add_argument(
        '-i', '--input-dir',
        type=str,
        help='Input directory containing HTML files'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        help='Output directory for markdown file'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config/default_config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--format',
        choices=['tree', 'table'],
        help='Output format (tree or table)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview markdown output without saving'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set the logging level'
    )
    
    parser.add_argument(
        '--show-filenames',
        action='store_true',
        help='Show original filenames in output'
    )
    
    parser.add_argument(
        '--hide-filenames',
        action='store_true',
        help='Hide original filenames in output'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Ensure document_tree section exists
    if 'document_tree' not in config:
        config['document_tree'] = {}
    
    # Set format from command line or ensure default
    if args.format:
        config['document_tree']['format'] = args.format
    elif 'format' not in config['document_tree']:
        config['document_tree']['format'] = 'table'  # Make table the default
    
    # Override show_filenames if specified in command line
    if args.show_filenames:
        config['document_tree']['show_filenames'] = True
    elif args.hide_filenames:
        config['document_tree']['show_filenames'] = False
    
    logging.info(f"Configuration format: {config['document_tree'].get('format')}")
    
    # Update logging configuration
    config.update({
        'log_level': args.log_level,
        'log_file': config.get('log_file', 'document_tree.log')
    })
    
    # Setup logging
    setup_logging(config)
    
    # Get directories from config
    input_dir = args.input_dir or config.get('input_directory')
    output_dir = args.output_dir or config.get('output_directory')
    
    if not input_dir or not output_dir:
        parser.error(
            "Input and output directories must be provided either through "
            "command line arguments or configuration file"
        )
        
    try:
        tree_builder = DocumentTreeBuilder(input_dir, output_dir, config)
        tree_builder.build_tree()
        markdown_content = tree_builder.export_markdown(args.dry_run)
        
        if args.dry_run:
            print(markdown_content)
            
    except Exception as e:
        logging.error(f"Error generating document tree: {str(e)}")
        raise

if __name__ == "__main__":
    main()