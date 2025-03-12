#!/usr/bin/env python3
"""
Tool Conversor Confluence - Main Application Entry Point

This module serves as the main entry point for the Confluence HTML Export Processor tool.
It provides a command-line interface for cleaning and processing HTML files exported from 
Confluence, optionally converting them to DOCX format, and organizing them based on 
breadcrumb hierarchy.

The application follows this workflow:
1. Parse command-line arguments
2. Load and validate configuration
3. Initialize logging
4. Process HTML files (clean, organize, and optionally convert to DOCX)
5. Generate document tree (optional)
6. Output processing summary

Example usage:
    python main.py --input-dir /path/to/confluence_exports --output-dir /path/to/output --create-docx

For more information, see the README.md file or run:
    python main.py --help
"""

import os
import sys
import argparse
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import traceback

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Now import your modules
from utils.utilities import (
    load_config,
    setup_logging
)

from core.file_processor import FileProcessor
from core.document_tree import DocumentTreeBuilder

class ConfigurationError(Exception):
    """
    Custom exception for configuration-related errors.
    
    This exception is raised when there are issues with the application configuration,
    such as missing required values, invalid paths, or conflicting settings.
    """
    pass

class HTMLProcessorCLI:
    """
    Command Line Interface for HTML Processor application.
    
    This class handles the command-line interface for the HTML Processor application,
    including argument parsing, configuration loading, and orchestrating the processing
    workflow.
    
    Attributes:
        logger (logging.Logger): Logger instance for this class
        start_time (float): Time when processing started (used for performance tracking)
        stats (Dict[str, Any]): Statistics collected during processing
    """
    
    def __init__(self):
        """
        Initialize the CLI application.
        
        Sets up the logger, starts the performance timer, and initializes statistics
        collection.
        """
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        self.stats: Dict[str, Any] = {
            'files_processed': 0,
            'errors': [],
            'warnings': [],
            'docx_created': 0
        }

    def parse_arguments(self) -> argparse.Namespace:
        """
        Parse command line arguments.

        Defines and processes all command-line arguments for the application, providing
        sensible defaults and help messages.

        Returns:
            argparse.Namespace: Parsed command line arguments
        """
        parser = argparse.ArgumentParser(
            description='Process HTML files exported from Confluence.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        parser.add_argument(
            '-c', '--config',
            type=str,
            help='Path to configuration file'
        )
        
        parser.add_argument(
            '-i', '--input-dir',
            type=str,
            help='Input directory containing HTML files'
        )
        
        parser.add_argument(
            '-o', '--output-dir',
            type=str,
            help='Output directory for processed files'
        )
        
        parser.add_argument(
            '--create-docx',
            action='store_true',
            help='Convert HTML files to DOCX format'
        )
        
        parser.add_argument(
            '--log-file',
            type=str,
            help='Path to log file'
        )
        
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='Set the logging level'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        
        # Add document tree specific options
        doc_tree_group = parser.add_argument_group('Document Tree Options')
        
        doc_tree_group.add_argument(
            '--generate-tree',
            action='store_true',
            help='Generate a document tree representation of processed files'
        )
        
        doc_tree_group.add_argument(
            '--tree-format',
            choices=['tree', 'table'],
            default='table',
            help='Format for the document tree output'
        )
        
        doc_tree_group.add_argument(
            '--show-filenames',
            action='store_true',
            help='Show filenames in document tree output'
        )
        
        doc_tree_group.add_argument(
            '--hide-filenames',
            action='store_true',
            help='Hide filenames in document tree output'
        )
        
        doc_tree_group.add_argument(
            '--tree-separator',
            type=str,
            default=';',
            help='Separator for table format document tree'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version='HTML Processor v1.0.0'
        )
        
        return parser.parse_args()

    def initialize_app(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Initialize application with configuration and logging.

        Loads the configuration from the specified file or the default location,
        overrides values based on command-line arguments, sets up logging,
        and validates the resulting configuration.

        Args:
            args: Parsed command line arguments

        Returns:
            Dict[str, Any]: Final application configuration after merging defaults,
                            config file values, and command-line arguments

        Raises:
            ConfigurationError: If configuration is invalid or cannot be loaded
        """
        try:
            # Load configuration from file
            config = load_config(args.config)

            # Override config with command line arguments if provided
            if args.input_dir:
                config['input_directory'] = args.input_dir
            if args.output_dir:
                config['output_directory'] = args.output_dir
            if args.create_docx:
                config['create_docx'] = True
            if args.log_level:
                config['log_level'] = args.log_level

            # Add document tree configuration
            if 'document_tree' not in config:
                config['document_tree'] = {}
                
            if args.tree_format:
                config['document_tree']['format'] = args.tree_format
            if args.tree_separator:
                config['document_tree']['separator'] = args.tree_separator
                
            # Handle show/hide filenames options
            if args.show_filenames:
                config['document_tree']['show_filenames'] = True
            elif args.hide_filenames:
                config['document_tree']['show_filenames'] = False

            # Setup logging with the configured options
            setup_logging(config, args.log_file)

            # Validate required configuration values and paths
            self._validate_config(config)

            return config

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize application: {e}")

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration values.

        Args:
            config: Configuration dictionary

        Raises:
            ConfigurationError: If configuration is invalid
        """
        required_paths = {
            'input_directory': 'Input directory',
            'output_directory': 'Output directory'
        }

        for key, name in required_paths.items():
            if not config.get(key):
                raise ConfigurationError(f"{name} not specified")

            path = Path(config[key])
            if key == 'input_directory' and not path.exists():
                raise ConfigurationError(f"{name} does not exist: {path}")

    def process_files(self, args: argparse.Namespace, config: Dict[str, Any]) -> None:
        """
        Process HTML files according to configuration.

        Args:
            args: Command line arguments
            config: Application configuration
        """
        try:
            # Create processor instance
            processor = FileProcessor(
                input_dir=config['input_directory'],
                output_dir=config['output_directory'],
                create_docx=config.get('create_docx', False)
            )

            if args.dry_run:
                self.logger.info("Dry run - no changes will be made")
                processor.dry_run = True

            # Process files and collect statistics
            results = processor.process_files()
            
            # Update statistics
            self.stats['files_processed'] = results['processed_files']
            self.stats['errors'].extend(results['errors'])
            self.stats['docx_created'] = results['created_docx']

        except Exception as e:
            self.logger.error(f"Error processing files: {e}")
            self.stats['errors'].append(str(e))
            raise

    def generate_document_tree(self, args: argparse.Namespace, config: Dict[str, Any]) -> None:
        """
        Generate document tree representation of processed files.

        Args:
            args: Command line arguments
            config: Application configuration
        """
        try:
            self.logger.info("Generating document tree...")
            
            tree_builder = DocumentTreeBuilder(
                input_dir=config['output_directory'],
                output_dir=config['output_directory'],
                config=config
            )
            
            tree_builder.build_tree()
            output = tree_builder.export_markdown(args.dry_run)
            
            if args.dry_run:
                self.logger.info("Document tree preview (dry run):")
                self.logger.info("\n" + output)
            else:
                self.logger.info("Document tree generated successfully")

        except Exception as e:
            self.logger.error(f"Error generating document tree: {e}")
            self.stats['errors'].append(f"Document tree generation failed: {str(e)}")

    def print_summary(self) -> None:
        """Print processing summary and statistics."""
        duration = time.time() - self.start_time
        
        self.logger.info("\nProcessing Summary:")
        self.logger.info("-" * 40)
        self.logger.info(f"Total Input Files: {self.stats['files_processed'] + len(self.stats['errors'])}")
        self.logger.info(f"Files Processed Successfully: {self.stats['files_processed']}")
        self.logger.info(f"Files Failed: {len(self.stats['errors'])}")
        self.logger.info(f"DOCX Files Created: {self.stats['docx_created']}")
        self.logger.info(f"Files Not Processed: {self.stats.get('files_not_processed', 0)}")
        self.logger.info(f"Processing Time: {duration:.2f} seconds")
        
        if self.stats['errors']:
            self.logger.error("\nErrors:")
            for error in self.stats['errors']:
                self.logger.error(f"- {error}")

def main() -> int:
    """
    Main entry point for the HTML processor.

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    cli = HTMLProcessorCLI()
    
    try:
        # Parse command line arguments
        args = cli.parse_arguments()
        
        # Initialize application
        config = cli.initialize_app(args)
        
        # Log startup information
        cli.logger.info("Starting HTML Processor")
        cli.logger.debug(f"Configuration: {config}")
        
        # Process files
        cli.process_files(args, config)
        
        # Generate document tree if requested
        if args.generate_tree:
            cli.generate_document_tree(args, config)
        
        # Print summary only on successful completion
        cli.print_summary()
        return 0

    except KeyboardInterrupt:
        cli.logger.error("\nOperation cancelled by user")
        return 1
        
    except Exception as e:
        cli.logger.error("An unexpected error occurred:")
        cli.logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())