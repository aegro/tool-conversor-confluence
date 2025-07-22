#!/usr/bin/env python3
"""
Markdown Converter Module for Confluence Export Processing

This module provides functionality to convert HTML content to Markdown format,
with special handling for Confluence-specific elements and image processing.
"""

import logging
import os
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
from bs4 import BeautifulSoup, Tag
import base64
import re
from urllib.parse import unquote
from pathvalidate import sanitize_filename
import html


class MarkdownConverter:
    """
    Converts HTML content to Markdown format with support for Confluence-specific elements.
    
    This class handles the conversion of HTML content to Markdown, including:
    - Basic HTML to Markdown conversion
    - Image extraction and path management
    - Special handling for Confluence elements
    - Table and code block formatting
    """
    
    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """
        Initialize the Markdown converter with configuration.
        
        Args:
            config: Configuration dictionary with markdown settings
            logger: Optional logger instance
        """
        self.config = config.get('markdown', {})
        self.logger = logger or logging.getLogger(__name__)
        self._setup_defaults()
    
    def _setup_defaults(self) -> None:
        """Set up default configuration values if not provided."""
        defaults = {
            'enabled': False,
            'output_dir': 'markdown',
            'image_dir': 'images',
            'image_output': 'images',
            'extensions': ['tables', 'fenced_code', 'footnotes'],
            'code_style': 'github',
            'preserve_internal_links': True,
            'flatten_output': False
        }
        
        for key, value in defaults.items():
            self.config.setdefault(key, value)
    
    def convert(
        self,
        html_content: str,
        output_path: Union[str, Path],
        page_id: str = "",
        original_path: Optional[Path] = None
    ) -> str:
        """
        Convert HTML content to Markdown format.
        
        Args:
            html_content: HTML content to convert
            output_path: Base directory for output files
            page_id: Optional page ID for organizing output
            original_path: Path to the original HTML file (for resolving relative paths)
            
        Returns:
            str: Converted Markdown content
        """
        if not self.config.get('enabled', False):
            self.logger.warning("Markdown conversion is disabled in config")
            return html_content
            
        # Parse HTML
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Process images
        self._process_images(soup, output_path, page_id, original_path)
        
        # Convert to Markdown (basic implementation)
        markdown = self._html_to_markdown(soup)
        
        return markdown
    
    def _process_images(
        self,
        soup: BeautifulSoup,
        output_path: Union[str, Path],
        page_id: str,
        original_path: Optional[Path] = None
    ) -> None:
        """
        Process images in the HTML content.
        
        Args:
            soup: BeautifulSoup object containing the HTML
            output_path: Base output directory
            page_id: ID of the current page
            original_path: Path to the original HTML file
        """
        import base64
        import re
        
        output_path = Path(output_path)
        image_output_dir = output_path / self.config['image_output']
        
        if page_id and not self.config['flatten_output']:
            image_output_dir = image_output_dir / page_id
        
        # Create image output directory if it doesn't exist
        image_output_dir.mkdir(parents=True, exist_ok=True)
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if not src:
                continue
                
            # Process base64 data URIs
            if src.startswith('data:'):
                try:
                    # Extract base64 data
                    match = re.match(r'data:image/([^;]+);base64,(.+)', src)
                    if match:
                        image_format = match.group(1)
                        base64_data = match.group(2)
                        
                        # Decode base64 data
                        image_data = base64.b64decode(base64_data)
                        
                        # Generate filename using alt text or a hash
                        alt_text = img.get('alt', '')
                        if alt_text:
                            # Use alt text as filename (usually contains original filename)
                            filename = sanitize_filename(alt_text)
                            # Ensure proper extension
                            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')):
                                filename = f"{filename}.{image_format}"
                        else:
                            # Generate a filename from the data
                            import hashlib
                            data_hash = hashlib.md5(image_data).hexdigest()[:8]
                            filename = f"image_{data_hash}.{image_format}"
                        
                        # Save the image
                        dest_path = image_output_dir / filename
                        with open(dest_path, 'wb') as f:
                            f.write(image_data)
                        
                        # Update image source to relative path
                        rel_path = dest_path.relative_to(output_path)
                        img['src'] = str(rel_path)
                        
                        self.logger.debug(f"Extracted base64 image to: {dest_path}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing base64 image: {e}")
                    continue
                    
            # Process regular image URLs
            else:
                try:
                    # Generate a safe filename
                    filename = self._generate_image_filename(src, img)
                    dest_path = image_output_dir / filename
                    
                    # Update image source in HTML
                    rel_path = dest_path.relative_to(output_path)
                    img['src'] = str(rel_path)
                    
                    # TODO: Implement actual image file saving for non-base64 images
                    # This will be implemented in a later phase
                    
                except Exception as e:
                    self.logger.error(f"Error processing image {src}: {e}")
    
    def _generate_image_filename(self, src: str, img_tag: Tag) -> str:
        """
        Generate a safe filename for an image.
        
        Args:
            src: Original image source
            img_tag: The img tag element
            
        Returns:
            str: Safe filename with extension
        """
        # Extract filename from URL or path
        filename = Path(src).name.split('?')[0]  # Remove query params
        
        # Generate a hash of the original source for uniqueness
        src_hash = hashlib.md5(src.encode('utf-8')).hexdigest()[:8]
        
        # Get extension from original filename or use default
        ext = Path(filename).suffix.lower()
        if not ext or len(ext) > 5:  # Sanity check for extension
            ext = '.png'  # Default extension
            
        # Generate safe filename
        safe_name = f"{Path(filename).stem}_{src_hash}{ext}"
        return sanitize_filename(safe_name)
    
    def _html_to_markdown(self, soup: BeautifulSoup) -> str:
        """
        Convert HTML content to Markdown.
        
        Enhanced implementation with better HTML tag handling, improved formatting,
        and special element processing.
        
        Args:
            soup: BeautifulSoup object containing the HTML
            
        Returns:
            str: Markdown content
        """
        # Make a copy to avoid modifying the original
        soup = BeautifulSoup(str(soup), 'lxml')
        
        # Remove style and script tags completely
        for tag in soup.find_all(['style', 'script']):
            tag.decompose()
        
        # Remove br tags
        for br in soup.find_all('br'):
            br.replace_with('\n')
        
        # First, handle special Information boxes
        for div in soup.find_all('div'):
            # Check if this is an Information box
            text_content = div.get_text().strip()
            if text_content.startswith('Information'):
                info_text = text_content.replace('Information', '').strip()
                marker = f"__INFO_BOX_{len(getattr(self, '_info_boxes', {}))}__"
                div.replace_with(marker)
                if not hasattr(self, '_info_boxes'):
                    self._info_boxes = {}
                self._info_boxes[marker] = f"\n> **ℹ️ Informação**\n> \n> {info_text}\n"
        
        # First pass: Convert special elements to temporary markers
        # This prevents nested elements from being processed incorrectly
        
        # Handle code blocks first (to preserve content)
        for i, pre in enumerate(soup.find_all('pre')):
            code = pre.get_text().strip()
            marker = f"__CODE_BLOCK_{i}__"
            pre.replace_with(marker)
            # Store for later replacement
            if not hasattr(self, '_code_blocks'):
                self._code_blocks = {}
            self._code_blocks[marker] = f"```\n{code}\n```"
        
        # Handle inline code
        for i, code in enumerate(soup.find_all('code')):
            # Skip if it's inside a pre tag (already handled)
            if code.parent and code.parent.name == 'pre':
                continue
            text = code.get_text()
            marker = f"__INLINE_CODE_{i}__"
            code.replace_with(marker)
            if not hasattr(self, '_inline_codes'):
                self._inline_codes = {}
            self._inline_codes[marker] = f"`{text}`"
        
        # Handle links before other text processing
        for i, a in enumerate(soup.find_all('a', href=True)):
            text = a.get_text().strip().replace('\n', ' ').replace('  ', ' ')
            href = a['href']
            
            # Convert internal .html links to .md
            if href.endswith('.html') and not href.startswith(('http://', 'https://')):
                href = href.replace('.html', '.md')
            
            marker = f"__LINK_{i}__"
            a.replace_with(marker)
            if not hasattr(self, '_links'):
                self._links = {}
            self._links[marker] = f"[{text}]({href})"
        
        # Handle images with improved alt text
        for i, img in enumerate(soup.find_all('img', src=True)):
            alt = img.get('alt', '')
            src = img['src']
            
            # Improve alt text
            if alt == 'Embedded Image' or not alt:
                # Try to extract meaningful alt text from filename
                filename = Path(src).stem
                # Remove common prefixes/suffixes
                alt = filename.replace('image_', '').replace('image-', '')
                # Replace underscores and hyphens with spaces
                alt = alt.replace('_', ' ').replace('-', ' ')
                # If it's still not meaningful, use a generic description
                if alt.isdigit() or len(alt) < 3:
                    alt = 'Imagem'
            
            marker = f"__IMAGE_{i}__"
            img.replace_with(marker)
            if not hasattr(self, '_images'):
                self._images = {}
            self._images[marker] = f"![{alt}]({src})"
        
        # Handle strong/bold BEFORE processing paragraphs
        for strong in soup.find_all(['strong', 'b']):
            text = strong.get_text()
            strong.replace_with(f"**{text}**")
        
        # Handle emphasis/italic BEFORE processing paragraphs
        for em in soup.find_all(['em', 'i']):
            text = em.get_text()
            em.replace_with(f"*{text}*")
        
        # Handle lists (unordered) with proper HTML tag handling
        for ul in soup.find_all('ul'):
            items = []
            for li in ul.find_all('li', recursive=False):
                # Get the content and process nested HTML
                li_soup = BeautifulSoup(str(li), 'lxml')
                # Remove the li tags themselves
                if li_soup.li:
                    li_content = li_soup.li.decode_contents()
                else:
                    li_content = str(li)
                
                # Process any remaining p tags in list items
                li_content = re.sub(r'<p[^>]*>', '', li_content)
                li_content = re.sub(r'</p>', '', li_content)
                li_content = li_content.strip()
                
                items.append(f"- {li_content}")
            ul.replace_with("\n" + "\n".join(items) + "\n")
        
        # Handle lists (ordered) with proper HTML tag handling
        for ol in soup.find_all('ol'):
            items = []
            for idx, li in enumerate(ol.find_all('li', recursive=False), 1):
                # Get the content and process nested HTML
                li_soup = BeautifulSoup(str(li), 'lxml')
                # Remove the li tags themselves
                if li_soup.li:
                    li_content = li_soup.li.decode_contents()
                else:
                    li_content = str(li)
                
                # Process any remaining p tags in list items
                li_content = re.sub(r'<p[^>]*>', '', li_content)
                li_content = re.sub(r'</p>', '', li_content)
                li_content = li_content.strip()
                
                items.append(f"{idx}. {li_content}")
            ol.replace_with("\n" + "\n".join(items) + "\n")
        
        # Handle headings
        for i in range(6, 0, -1):
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text().strip()
                heading.replace_with(f"\n{'#' * i} {text}\n\n")
        
        # Handle paragraphs
        for p in soup.find_all('p'):
            # Get text content (which now includes processed bold/italic)
            content = p.decode_contents() if hasattr(p, 'decode_contents') else str(p)
            # Remove the p tags
            content = re.sub(r'^<p[^>]*>', '', content)
            content = re.sub(r'</p>$', '', content)
            content = content.strip()
            
            if content:  # Only add non-empty paragraphs
                p.replace_with(f"\n{content}\n\n")
            else:
                p.decompose()
        
        # Handle blockquotes
        for blockquote in soup.find_all('blockquote'):
            text = blockquote.get_text().strip()
            lines = text.split('\n')
            quoted_lines = ['> ' + line for line in lines if line.strip()]
            blockquote.replace_with("\n" + "\n".join(quoted_lines) + "\n\n")
        
        # Handle horizontal rules
        for hr in soup.find_all('hr'):
            hr.replace_with("\n---\n\n")
        
        # Remove any remaining HTML tags we don't specifically handle
        # This catches any stray tags
        text = str(soup)
        # Remove any remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Replace markers with actual content
        if hasattr(self, '_info_boxes'):
            for marker, content in self._info_boxes.items():
                text = text.replace(marker, content)
            del self._info_boxes
            
        if hasattr(self, '_code_blocks'):
            for marker, content in self._code_blocks.items():
                text = text.replace(marker, content)
            del self._code_blocks
        
        if hasattr(self, '_inline_codes'):
            for marker, content in self._inline_codes.items():
                text = text.replace(marker, content)
            del self._inline_codes
        
        if hasattr(self, '_links'):
            for marker, content in self._links.items():
                text = text.replace(marker, content)
            del self._links
        
        if hasattr(self, '_images'):
            for marker, content in self._images.items():
                text = text.replace(marker, content)
            del self._images
        
        # Clean up excessive whitespace FIRST
        text = re.sub(r'\n{3,}', '\n\n', text.strip())
        text = re.sub(r' +', ' ', text)  # Remove multiple spaces
        text = re.sub(r'\n +', '\n', text)  # Remove leading spaces on lines
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Fix broken bold formatting (multiple lines)
        text = re.sub(r'\*\*\s*\n\s*([^\n*]+?)\s*\n\s*\*\*', r'**\1**', text, flags=re.MULTILINE)
        # Fix cases where bold is split with just whitespace
        text = re.sub(r'\*\*\s+\*\*', '**', text)
        
        # Fix broken italic formatting (multiple lines)
        text = re.sub(r'\*\s*\n\s*([^\n*]+?)\s*\n\s*\*', r'*\1*', text, flags=re.MULTILINE)
        # Fix cases where italic is split with just whitespace  
        text = re.sub(r'\*\s+\*', '*', text)
        
        # Fix concatenated bold sections (e.g., **Editar:**text should be **Editar:** text)
        text = re.sub(r'(\*\*[^*]+:\*\*)([^\s])', r'\1 \2', text)
        
        # Separate concatenated bold sections with period separator
        text = re.sub(r'(\*\*[^*]+\*\*)\.(?=\*\*)', r'\1.\n\n', text)
        
        # Format "Ficou com dúvidas?" sections - handle multiple variations
        text = re.sub(
            r'\*\*(Ficou com dúvidas\?)\*\*\s*([^\n]*)',
            r'\n---\n\n### 💬 \1\n\n\2',
            text,
            flags=re.IGNORECASE
        )
        # Also handle non-bold version
        text = re.sub(
            r'(?<!\*)(?<!#)(Ficou com dúvidas\?)\s*([^\n]*)',
            r'\n---\n\n### 💬 \1\n\n\2',
            text,
            flags=re.IGNORECASE
        )
        
        # Final cleanup of spacing around markdown elements
        text = re.sub(r'\n\n+#', '\n\n#', text)  # Normalize heading spacing
        text = re.sub(r'\n\n+>', '\n\n>', text)  # Normalize blockquote spacing
        text = re.sub(r'\n\n+-', '\n\n-', text)  # Normalize list spacing
        text = re.sub(r'\n\n+\d+\.', '\n\n1.', text)  # Normalize ordered list spacing
        text = re.sub(r'\n\n+---', '\n\n---', text)  # Normalize horizontal rule spacing
        
        return text.strip()
    
    def _convert_tables(self, soup: BeautifulSoup) -> None:
        """Convert HTML tables to Markdown tables."""
        # Will be implemented in Phase 3
        pass
    
    def _convert_code_blocks(self, soup: BeautifulSoup) -> None:
        """Convert code blocks with syntax highlighting."""
        # Will be implemented in Phase 3
        pass
