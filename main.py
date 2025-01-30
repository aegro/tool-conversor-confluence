# main.py

import os
import sys
import argparse
import logging
import time
from typing import Dict, Any
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

class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass

class HTMLProcessorCLI:
    """Command Line Interface for HTML Processor application."""
    
    def __init__(self):
        """Initialize the CLI application."""
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
        
        parser.add_argument(
            '--version',
            action='version',
            version='HTML Processor v1.0.0'
        )
        
        return parser.parse_args()

    def initialize_app(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Initialize application with configuration and logging.

        Args:
            args: Parsed command line arguments

        Returns:
            Dict[str, Any]: Application configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Load configuration
            config = load_config(args.config)

            # Override config with command line arguments
            if args.input_dir:
                config['input_directory'] = args.input_dir
            if args.output_dir:
                config['output_directory'] = args.output_dir
            if args.create_docx:
                config['create_docx'] = True
            if args.log_level:
                config['log_level'] = args.log_level

            # Setup logging
            setup_logging(config, args.log_file)

            # Validate required configuration
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