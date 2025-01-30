# file_processor.py

import logging
import shutil
from pathlib import Path
from typing import Union, Tuple, List, Optional, Dict, Any
import re

import requests
from bs4 import BeautifulSoup, NavigableString
from htmldocx import HtmlToDocx

from utils.utilities import get_config
from core.html_cleaner import HTMLCleaner

class FileProcessor:
    """
    Process HTML files exported from Confluence by organizing them according to breadcrumbs 
    and optionally converting them to DOCX format.
    """

    RESOURCE_FOLDERS = ["attachments", "images", "styles", "img"]
    SUPPORTED_EXTENSIONS = [".html", ".docx"]

    def __init__(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        create_docx: bool = False,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the FileProcessor.

        Args:
            input_dir (Union[str, Path]): Path to input directory containing HTML files
            output_dir (Union[str, Path]): Path where processed files will be saved
            create_docx (bool, optional): Whether to create DOCX versions. Defaults to False
            config (Optional[Dict[str, Any]], optional): Configuration override. Defaults to None
        
        Raises:
            FileNotFoundError: If input directory doesn't exist
            ValueError: If directory paths are invalid
        """
        # Initialize paths and settings
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.create_docx = create_docx
        
        # Load configuration
        self.config = config or get_config()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Validate directories
        self._validate_directories()
        
        # Initialize statistics
        self.stats = {
            'total_input_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'created_docx': 0,
            'errors': []
        }

    def _count_input_files(self) -> int:
        """
        Count total number of HTML files in input directory.

        Returns:
            int: Total number of HTML files found
        """
        count = sum(1 for _ in self.input_dir.rglob("*.html"))
        self.stats['total_input_files'] = count
        return count

    def _validate_directories(self) -> None:
        """
        Validate input and output directory paths.
        
        Raises:
            FileNotFoundError: If input directory doesn't exist
            ValueError: If directory paths are invalid
        """
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
        
        if not self.input_dir.is_dir():
            raise ValueError(f"Input path is not a directory: {self.input_dir}")
            
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def setup_directory_structure(self) -> Tuple[Path, str]:
        """
        Set up the output directory structure using the first breadcrumb as space name.
        If no breadcrumbs are found, uses the title text in parentheses.

        Returns:
            Tuple[Path, str]: (New base directory path, Space name)

        Raises:
            FileNotFoundError: If no HTML files are found
            ValueError: If no valid breadcrumbs or title are found
        """
        # Find first HTML file
        html_files = list(self.input_dir.glob("*.html"))
        if not html_files:
            raise FileNotFoundError(f"No HTML files found in {self.input_dir}")

        # Get first file and extract breadcrumbs
        first_file = html_files[0]
        soup = self._read_html_file(first_file)
        breadcrumbs = self._extract_breadcrumbs(soup)

        space_name = None
        if breadcrumbs:
            space_name = breadcrumbs[0]
        else:
            # Try to extract from title
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                # Extract text within parentheses
                match = re.search(r'\((.*?)\)', title_tag.string)
                if match:
                    space_name = match.group(1).strip()

        if not space_name:
            raise ValueError(f"No breadcrumbs or valid title found in {first_file}")

        new_base_dir = self.output_dir / self._sanitize_filename(space_name)

        # Clean and recreate directory
        if new_base_dir.exists():
            shutil.rmtree(new_base_dir)
        new_base_dir.mkdir(parents=True)

        # Copy resource folders
        self._copy_resource_folders(new_base_dir)

        return new_base_dir, space_name

    def process_files(self) -> Dict[str, Any]:
        """
        Process all HTML files in the input directory.

        Returns:
            Dict[str, Any]: Processing statistics and results
        """
        try:
            # Count total input files first
            total_files = self._count_input_files()
            self.logger.info(f"Found {total_files} HTML files to process")

            # Setup directory structure
            new_base_dir, space_name = self.setup_directory_structure()
            self.logger.info(f"Created directory structure at: {new_base_dir}")

            # Process all HTML files
            self._process_html_files(new_base_dir, space_name)
            
            # Organize duplicate named files
            self._organize_duplicates(new_base_dir)
            
            # Check for discrepancies
            processed_total = self.stats['processed_files'] + self.stats['failed_files']
            if processed_total != total_files:
                discrepancy = total_files - processed_total
                error_msg = f"Discrepancy found: {discrepancy} files were not processed"
                self.logger.error(error_msg)
                self.stats['errors'].append(error_msg)
            
            # Log final statistics
            self._log_processing_stats()
            
            return self.stats

        except Exception as e:
            self.logger.error(f"Failed to process files: {e}", exc_info=True)
            self.stats['errors'].append(str(e))
            raise

    def _process_html_files(self, base_dir: Path, space_name: str) -> None:
        """Process all HTML files in the input directory."""
        for html_file in self.input_dir.rglob("*.html"):
            try:
                success, result = self._process_html_file(html_file, base_dir, space_name)
                if success:
                    self.stats['processed_files'] += 1
                    self.logger.info(
                        f"Processed {html_file.relative_to(self.input_dir)} -> {result}"
                    )
                else:
                    self.stats['failed_files'] += 1
                    self.logger.error(
                        f"Failed to process {html_file.relative_to(self.input_dir)}: {result}"
                    )
            except Exception as e:
                self.stats['failed_files'] = self.stats.get('failed_files', 0) + 1
                error_msg = f"Error processing {html_file}: {str(e)}"
                if 'errors' not in self.stats:
                    self.stats['errors'] = []
                self.stats['errors'].append(error_msg)
                self.logger.error(error_msg, exc_info=True)

    def _process_html_file(
        self, file_path: Path, new_base_dir: Path, space_name: str
    ) -> Tuple[bool, str]:
        """
        Process a single HTML file.

        Args:
            file_path (Path): Path to HTML file
            new_base_dir (Path): Base output directory
            space_name (str): Name of the space

        Returns:
            Tuple[bool, str]: (Success status, Result message)
        """
        try:
            # Read and parse HTML
            soup = self._read_html_file(file_path)
            
            # Get sanitized filename
            new_filename = self._get_safe_filename(soup, file_path, space_name)
            
            # Extract and validate breadcrumbs
            breadcrumbs = self._extract_breadcrumbs(soup)
            if not breadcrumbs:
                return False, "No breadcrumbs found"

            # Create target directory structure
            target_dir = self._create_directory_path(new_base_dir, breadcrumbs[1:])
            
            # Clean HTML content
            cleaner = HTMLCleaner(str(soup), target_dir)
            cleaned_html = cleaner.clean()

            # Save cleaned HTML
            target_html_path = target_dir / new_filename
            self._save_html_file(target_html_path, cleaned_html)

            # Convert to DOCX if requested
            if self.create_docx:
                self._convert_to_docx(target_html_path, target_dir)
                self.stats['created_docx'] += 1
                return True, f"Processed HTML and created DOCX in {target_dir}"

            return True, f"Processed HTML in {target_dir}"

        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}", exc_info=True)
            return False, str(e)

    def _read_html_file(self, file_path: Path) -> BeautifulSoup:
        """Read and parse HTML file."""
        with file_path.open('r', encoding='utf-8') as f:
            return BeautifulSoup(f.read(), 'lxml')

    def _save_html_file(self, file_path: Path, content: str) -> None:
        """Save HTML content to file."""
        with file_path.open('w', encoding='utf-8') as f:
            f.write(content)

    def _extract_breadcrumbs(self, soup: BeautifulSoup) -> List[str]:
        """Extract and sanitize breadcrumbs from HTML."""
        breadcrumbs = []
        breadcrumb_section = soup.find('div', id='breadcrumb-section')
        
        if breadcrumb_section:
            for span in breadcrumb_section.find_all('span'):
                link = span.find('a')
                if link and isinstance(link.string, NavigableString):
                    breadcrumb = self._sanitize_filename(link.string.strip())
                    if breadcrumb:
                        breadcrumbs.append(breadcrumb)
        
        return breadcrumbs

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize string for use as filename."""
        if not filename:
            return "untitled"
            
        # Remove invalid characters
        cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace whitespace with hyphens
        cleaned = re.sub(r'\s+', '-', cleaned)
        # Remove leading/trailing hyphens
        cleaned = cleaned.strip('-')
        
        return cleaned or "untitled"

    def _get_safe_filename(self, soup: BeautifulSoup, file_path: Path, space_name: str) -> str:
        """Generate safe filename from HTML title or filepath."""
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            filename = self._sanitize_filename(title_tag.string.strip())
        else:
            filename = file_path.stem

        # Remove space name prefix if present
        filename = re.sub(f'^{re.escape(space_name)}-', '', filename)
        
        return f"{filename}.html"

    def _create_directory_path(self, base_path: Path, breadcrumbs: List[str]) -> Path:
        """Create nested directory structure from breadcrumbs."""
        current_path = base_path
        for crumb in breadcrumbs:
            current_path = current_path / crumb
            current_path.mkdir(parents=True, exist_ok=True)
        return current_path

    def _copy_resource_folders(self, new_base_dir: Path) -> None:
        """Copy resource folders to output directory."""
        for folder in self.RESOURCE_FOLDERS:
            source_folder = self.input_dir / folder
            if source_folder.exists():
                target_folder = new_base_dir / folder
                shutil.copytree(source_folder, target_folder, dirs_exist_ok=True)
                self.logger.debug(f"Copied resource folder: {folder}")

    def _convert_to_docx(self, html_path: Path, target_dir: Path) -> None:
        """Convert HTML file to DOCX format."""
        docx_path = target_dir / f"{html_path.stem}.docx"
        converter = HtmlToDocx()
        converter.parse_html_file(str(html_path), str(docx_path))

    def _organize_duplicates(self, base_dir: Path) -> None:
        """Organize files that have the same name as their parent folders."""
        for extension in self.SUPPORTED_EXTENSIONS:
            for file_path in base_dir.rglob(f"*{extension}"):
                try:
                    potential_folder = file_path.parent / file_path.stem
                    if potential_folder.is_dir():
                        new_path = potential_folder / file_path.name
                        file_path.rename(new_path)
                        self.logger.debug(f"Moved {file_path.name} to {new_path}")
                except Exception as e:
                    self.logger.error(f"Error organizing {file_path}: {e}")

    def _log_processing_stats(self) -> None:
        """Collect final processing statistics."""
        # Remove the logging statements and just update the stats dictionary
        self.stats.update({
            'files_not_processed': self.stats['total_input_files'] - (
                self.stats['processed_files'] + self.stats['failed_files']
            )
        })