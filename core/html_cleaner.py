# html_cleaner.py

import os
import re
import logging
from pathlib import Path
from typing import Dict, Optional, Set
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment
from utils.utilities import get_config
from urllib.parse import urljoin, urlparse

import argparse

parser = argparse.ArgumentParser(description="Processador de HTML")
parser.add_argument('--input-dir', required=True, help="Diretório de entrada")
parser.add_argument('--output-dir', required=True, help="Diretório de saída")
parser.add_argument('--create-docx', action='store_true', help="Se deseja criar um DOCX")
args = parser.parse_args()



class HTMLCleaner:
    """
    Clean and standardize HTML content exported from Confluence.
    Handles removal of unnecessary elements, standardization of classes,
    and processing of embedded resources like images.
    """

    def __init__(self, html_content: str, target_dir: Path, config: Optional[Dict] = None):
        """
        Initialize HTMLCleaner with content and configuration.

        Args:
            html_content (str): Raw HTML content to clean
            target_dir (Path): Directory for saving processed resources
            config (Optional[Dict]): Configuration override. Defaults to None
        """
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.target_dir = Path(target_dir)
        self.config = config or get_config()
        self.logger = logging.getLogger(__name__)

        # Extract standard classes from config
        self.standard_classes = self.config.get('standard_html_classes', {})
        
        # Extract title for later use
        self.title = self._extract_title()

        # Define Confluence-specific classes and IDs to remove
        self.confluence_classes = set([
            # Classes to remove
            'theme-default', 'aui-theme-default', 'first', 'pagetitle', 'wiki-content', 'group',
            'contentLayout2', 'columnLayout', 'fixed-width', 'cell', 'normal', 'innerCell',
            'toc-macro', 'toc-indentation', 'confluenceTable', 'confluenceTd', 'emoticon',
            'emoticon-blue-star', 'image-center-wrapper', 'confluence-embedded-image', 'image-center',
            'panel', 'panelContent', 'inline-task-list', 'placeholder-inline-tasks', 'confluence-userlink',
            'user-mention', 'current-user-mention', 'date-upcoming', 'date-future', 'confluenceTh',
            'confluence-information-macro', 'confluence-information-macro-information', 'aui-icon',
            'aui-icon-small', 'aui-iconfont-info', 'confluence-information-macro-icon',
            'confluence-information-macro-body', 'confluence-embedded-file-wrapper', 'expand-container',
            'expand-control', 'expand-control-icon', 'expand-control-image', 'expand-control-text',
            'expand-content', 'status-macro', 'aui-lozenge', 'aui-lozenge-progress', 'aui-lozenge-complete',
            'table-wrapper', 'task-blanket', 'aui', 'tasks-table-interactive', 'tasks-report',
            'tablesorter-headerRow', 'header-description', 'tasks-table-column-unsortable', 'header-duedate',
            'header-assignee', 'header-location', 'tasks-report-date', 'tasks-report-assignee',
            'task-location', 'greybox', 'footer-body', 'external-link', 'url', 'fn','aui-page-panel','view',
            'data-colorid','expand-container', 'expand-control', 'expand-control-icon', 'expand-control-image', 
            'expand-control-text', 'expand-content', 'decision-list',
        ])
        
        self.confluence_ids = set([
            # IDs to remove
            'page', 'main', 'main-header', 'breadcrumb-section', 'breadcrumbs', 'title-heading',
            'title-text', 'content', 'main-content', 'attachments', 'footer', 'footer-logo','data-inline-tasks-content-id'
        ])

    def _inject_custom_styles(self) -> None:
        """Inject custom CSS styles into the HTML document."""
        # First, remove any existing style tags from the body
        for style_tag in self.soup.find_all('style'):
            if style_tag.parent.name != 'head':
                style_tag.decompose()

        custom_css = """
            body {
                font-family: 'DM Sans', sans-serif;
                color: #404040;
                line-height: 1.5;
                margin: 20px;
            }

            h1 {
                font-family: 'Roboto', sans-serif;
                color: #00c65e;
            }

            h2, h3, h4, h5, h6 {
                font-family: 'Roboto', sans-serif;
                color: #046062;
            }

            p {
                margin-bottom: 1.5em;
            }

            strong {
                font-weight: bold;
            }

            em {
                color: #00c65e;
                font-style: italic;
            }

            a {
                color: #00c65e;
                text-decoration: none;
            }

            a:hover {
                text-decoration: underline;
            }

            ul {
                margin-bottom: 1.5em;
            }

            li {
                margin-left: 20px;
                list-style-type: disc;
            }

            img {
                border: 1px solid #00c65e; 
            }

            /* Table Styles */
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 1.5em;
            }

            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
                vertical-align: top;
            }

            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }

            tr:nth-child(even) {
                background-color: #fafafa;
            }

            tr:hover {
                background-color: #f5f5f5;
            }

            /* Column Width Classes */
            .column-25 { width: 25%; }
            .column-33 { width: 33.333%; }
            .column-50 { width: 50%; }
            .column-67 { width: 66.666%; }
            .column-75 { width: 75%; }
            .column-100 { width: 100%; }

            /* Status Styles */
            .status-gray {
                background-color: #7A869A;
                color: #FFFFFF;
                padding: 2px 6px;
                border-radius: 3px;
            }
            .status-green {
                background-color: #36B37E;
                color: #FFFFFF;
                padding: 2px 6px;
                border-radius: 3px;
            }
            .status-red {
                background-color: #FF5630;
                color: #FFFFFF;
                padding: 2px 6px;
                border-radius: 3px;
            }
            .status-yellow {
                background-color: #FFAB00;
                color: #000000;
                padding: 2px 6px;
                border-radius: 3px;
            }
            .status-blue {
                background-color: #0065FF;
                color: #FFFFFF;
                padding: 2px 6px;
                border-radius: 3px;
            }
            .status-purple {
                background-color: #6554C0;
                color: #FFFFFF;
                padding: 2px 6px;
                border-radius: 3px;
            }
            .status-teal {
                background-color: #00B8D9;
                color: #FFFFFF;
                padding: 2px 6px;
                border-radius: 3px;
            }
            /* Expand Box Styles */
            .expand-box {
                border: 1px solid #ccc;
                padding: 10px;
                margin-bottom: 1.5em;
                background-color: #f9f9f9;
            }

            .expand-box em {
                display: block;
                font-style: italic;
                margin-bottom: 0.5em;
            }
            /* Decision Box Styles */
            .decision-box {
                border: 1px solid #00c65e;
                padding: 10px;
                margin-bottom: 1.5em;
                background-color: #e6f9ee;
            }

            .decision-box em {
                display: block;
                font-style: italic;
                color: #00c65e;
                margin-bottom: 0.5em;
            }
        """
        # Find or create head element
        head = self.soup.head
        if not head:
            head = self.soup.new_tag('head')
            if self.soup.html:
                self.soup.html.insert(0, head)
        
        # Add Google Fonts link
        fonts_link = self.soup.new_tag('link')
        fonts_link['rel'] = 'stylesheet'
        fonts_link['href'] = 'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700&family=Roboto:wght@400;700&display=swap'
        head.append(fonts_link)
        
        # Add custom styles
        style_tag = self.soup.new_tag('style')
        style_tag.string = custom_css
        head.append(style_tag)

        
    def clean(self) -> str:
        """
        Perform all cleaning operations on the HTML content.

        Returns:
            str: Cleaned HTML content
        """
        try:
            # First process resources to ensure they're cleaned
            self._process_emojis()
            self._process_images()
            self._process_links()
            self._process_status_macros()
            self._process_expand_containers()
            self._process_decision_lists()
            self._convert_column_layouts()
            
            # Unwrap table wrappers
            self._unwrap_table_wrappers()            

            # Then clean structure and content
            self._remove_unnecessary_sections()
            self._clean_metadata()
            self._remove_confluence_specific()
            self._clean_attributes_and_classes()
            
            # Layout and formatting
            self._clean_tables()
            self._standardize_headings()
            self._clean_lists()
            
            # Final cleanup
            self._remove_empty_elements()
            self._cleanup_whitespace()
            self._add_missing_title()

            # Ensure the <meta charset> tag is present
            self._ensure_meta_charset()

            # Inject custom styles
            self._inject_custom_styles()

            # Return with explicit doctype
            return "<!DOCTYPE html>\n" + str(self.soup.html.prettify(formatter='html5'))

        except Exception as e:
            self.logger.error(f"Error cleaning HTML: {e}", exc_info=True)
            raise

    def _extract_title(self) -> str:
        """Extract and clean page title."""
        title_tag = self.soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        return "Untitled Document"

    def _remove_unnecessary_sections(self) -> None:
        """Remove unnecessary page sections."""
        # List of selectors for elements to remove
        selectors_to_remove = [
            # Remove Confluence footer and metadata
            'div#footer',
            'div.footer-body',
            'section.footer-body',
            'div[role="contentinfo"]',
            'div#footer-logo',
            'div.page-metadata',
            'div#breadcrumb-section',
            'script',
            # Remove Confluence-specific styles and links
            'link[rel="stylesheet"][href*="confluence"]',
            'meta[name*="confluence"]',
            'link[href="styles/site.css"]',
        ]

        for selector in selectors_to_remove:
            for element in self.soup.select(selector):
                element.decompose()

        # Additional specific footer text removal
        for p in self.soup.find_all('p'):
            if 'Document generated by Confluence' in p.get_text():
                p.decompose()

        # Remove HTML comments
        for comment in self.soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

    def _clean_metadata(self) -> None:
        """Clean and standardize metadata elements."""
        # Update page metadata
        metadata_div = self.soup.find('div', class_='page-metadata')
        if metadata_div:
            # Replace English metadata terms with Portuguese
            translations = {
                'Created by': 'Criado por',
                'on': 'em',
                'Last modified by': 'Última modificação por',
                'at': 'às'
            }
            
            for old_text, new_text in translations.items():
                for text in metadata_div.find_all(string=re.compile(old_text)):
                    text.replace_with(text.replace(old_text, new_text))

    def _clean_attributes_and_classes(self) -> None:
        """Clean and standardize HTML attributes and classes."""
        for tag in self.soup.find_all(True):
            # Remove Confluence-specific IDs
            if 'id' in tag.attrs:
                if tag['id'] in self.confluence_ids or tag['id'].startswith('expander-'):
                    del tag['id']

            # Remove Confluence-specific classes
            if 'class' in tag.attrs:
                cleaned_classes = [
                    cls for cls in tag['class'] if cls not in self.confluence_classes
                ]
                if cleaned_classes:
                    tag['class'] = cleaned_classes
                else:
                    del tag['class']

            # Remove all data-* attributes
            for attr in list(tag.attrs):
                if attr.startswith('data-'):
                    del tag[attr]
                elif attr == 'style':
                    # Optionally, you can clean or keep styles
                    pass  # Keep styles unless they are Confluence-specific


    def _process_images(self) -> None:
        """
        Clean and standardize image elements.
        - Removes unnecessary attributes
        - Preserves essential attributes (src, alt, title, width, height)
        """
        input_dirhtml = args.input_dir
        base_url = getattr(self.soup, 'base_url', None)
        for img in self.soup.find_all('img'):
            try:
                # Keep only essential attributes
                allowed_attrs = {'src', 'alt', 'title', 'width', 'height', 'style'}
                current_attrs = set(img.attrs.keys())
                
                # Remove unwanted attributes
                for attr in current_attrs - allowed_attrs:
                    del img[attr]
                
                # Ensure alt attribute exists
                if 'alt' not in img.attrs:
                    img['alt'] = ''
                
                # Clean the src attribute
                if 'src' in img.attrs and img['src']:
                    src = img['src']
                    # Remove qualquer query string do src
                    src = urlparse(src).path
                    # If necessary, adjust the src to remove Confluence-specific parts
                    # For now, we'll keep the src as it is
                    if not src.startswith(('http://', 'https://', 'file://', '/')):
                        if base_url:
                            # Usa urljoin se o base_url estiver presente
                            img['src'] = urljoin(base_url, src)
                            self.logger.info(f"Updated src to absolute path: {img['src']}")
                        else:
                            # Caso base_url não esteja disponível, use o diretório atual
                            base_dir = os.getcwd()
                            absolute_path = os.path.join(base_dir, input_dirhtml, src)
                            img['src'] = f"{absolute_path}"
                            self.logger.info(f"Updated src to absolute path: {img['src']}")
                
                # Retain style attribute if not Confluence-specific
                if 'style' in img.attrs and 'confluence' in img['style']:
                    del img['style']

            except Exception as e:
                self.logger.error(f"Error processing image: {e}", exc_info=True)
        #Debug HTML
        #print(self.soup.prettify())

    def _process_links(self) -> None:
        """Clean and process link elements."""
        for link in self.soup.find_all('a'):
            # Remove JavaScript events
            for attr in list(link.attrs):
                if attr.startswith('on'):
                    del link[attr]

            # Clean href attribute
            if 'href' in link.attrs:
                href = link['href']
                if href.startswith('javascript:'):
                    del link['href']
                elif 'confluence' in href and 'people' in href:
                    # Convert user links to text
                    link.replace_with(link.get_text())
                elif 'mailto:' in href:
                    # Keep mailto links
                    pass
                else:
                    # Adjust relative links if necessary
                    pass  # Implement any adjustments needed for your context

            # Remove Confluence-specific classes
            if 'class' in link.attrs:
                cleaned_classes = [
                    cls for cls in link['class'] if cls not in self.confluence_classes
                ]
                if cleaned_classes:
                    link['class'] = cleaned_classes
                else:
                    del link['class']

    def _clean_tables(self) -> None:
        """Clean and standardize table elements."""
        for table in self.soup.find_all('table'):
            # Remove Confluence-specific classes and IDs
            if 'class' in table.attrs:
                cleaned_classes = [
                    cls for cls in table['class'] if cls not in self.confluence_classes
                ]
                if cleaned_classes:
                    table['class'] = cleaned_classes
                else:
                    del table['class']

            # Add 'custom-table' class
            table_classes = table.get('class', [])
            table_classes.append('custom-table')
            table['class'] = table_classes

            # Remove deprecated attributes and inline styles
            for attr in ['border', 'cellspacing', 'cellpadding', 'style']:
                if attr in table.attrs:
                    del table[attr]

            # Clean table cells
            for cell in table.find_all(['td', 'th']):
                # Remove Confluence-specific classes
                if 'class' in cell.attrs:
                    cleaned_classes = [
                        cls for cls in cell['class'] if cls not in self.confluence_classes
                    ]
                    if cleaned_classes:
                        cell['class'] = cleaned_classes
                    else:
                        del cell['class']
                # Remove inline styles
                if 'style' in cell.attrs:
                    del cell['style']
                # Remove unwanted attributes
                allowed_cell_attrs = {'colspan', 'rowspan', 'class'}
                for attr in list(cell.attrs):
                    if attr not in allowed_cell_attrs:
                        del cell[attr]


    def _standardize_headings(self) -> None:
        """Standardize heading hierarchy and formatting."""
        heading_levels = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        current_level = 0
        
        for heading in self.soup.find_all(heading_levels):
            heading_level = int(heading.name[1])
            
            # Store the text content, removing any extra formatting but preserving the actual text
            text_content = heading.get_text(strip=True)
            
            # Create a new clean heading tag
            new_heading = self.soup.new_tag(f'h{heading_level}')
            new_heading.string = text_content
            
            # Replace the old heading with the clean one
            heading.replace_with(new_heading)
            
            # Update current level for hierarchy maintenance
            current_level = heading_level

    def _clean_lists(self) -> None:
        """Clean and standardize list elements."""
        # Regular list cleaning
        for list_tag in self.soup.find_all(['ul', 'ol']):
            # Clean list items
            for item in list_tag.find_all('li'):
                if 'class' in item.attrs:
                    cleaned_classes = [
                        cls for cls in item['class'] if cls not in self.confluence_classes
                    ]
                    if cleaned_classes:
                        item['class'] = cleaned_classes
                    else:
                        del item['class']
                        
                # Remove unnecessary attributes
                for attr in list(item.attrs):
                    if attr not in {'class', 'value'}:
                        del item[attr]


    def _remove_empty_elements(self) -> None:
        """Remove empty elements that serve no purpose."""
        # Elements that should be removed if empty
        tags_to_check = ['p', 'div', 'span', 'strong', 'em', 'i', 'b']
        
        for tag in self.soup.find_all(tags_to_check):
            if not tag.get_text(strip=True) and not tag.find_all(['img', 'br']):
                tag.decompose()

    def _cleanup_whitespace(self) -> None:
        """Clean up excessive whitespace in HTML."""
        # Clean up text nodes while preserving spaces around inline elements
        inline_elements = {'strong', 'em', 'i', 'b', 'span', 'a', 'code'}
        
        for text in self.soup.find_all(string=True):
            if text.parent.name not in ['pre', 'code']:
                # Only collapse multiple spaces into single space
                cleaned_text = re.sub(r'\s+', ' ', text.string)
                # Only strip if not adjacent to inline elements
                if text.parent.name not in inline_elements and not (
                    text.next_sibling and getattr(text.next_sibling, 'name', None) in inline_elements or
                    text.previous_sibling and getattr(text.previous_sibling, 'name', None) in inline_elements
                ):
                    cleaned_text = cleaned_text.strip()
                text.replace_with(cleaned_text)

    def _add_missing_title(self) -> None:
        """Add title element if missing."""
        if not self.soup.title:
            head = self.soup.head or self.soup.new_tag('head')
            if not self.soup.head:
                self.soup.html.insert(0, head)
            
            title = self.soup.new_tag('title')
            title.string = self.title
            head.append(title)

    def _ensure_meta_charset(self) -> None:
        """Ensure that the <meta charset="UTF-8"> tag is present."""
        if self.soup.head:
            if not self.soup.head.find('meta', charset=True):
                meta = self.soup.new_tag('meta', charset='UTF-8')
                self.soup.head.insert(0, meta)
        else:
            # Create head if missing
            head = self.soup.new_tag('head')
            meta = self.soup.new_tag('meta', charset='UTF-8')
            head.append(meta)
            self.soup.html.insert(0, head)

    def _process_emojis(self) -> None:
        """Convert Confluence emoji images to their Unicode equivalents."""
        emoji_elements = self.soup.find_all('img', class_='emoticon')
        
        for emoji in emoji_elements:
        # Get the emoji data
            emoji_fallback = emoji.get('data-emoji-fallback')
            
            if emoji_fallback:
                # Create a new text node with the Unicode emoji
                emoji_text = self.soup.new_string(emoji_fallback)
                # Replace the img tag with the text node
                emoji.replace_with(emoji_text)
            else:
                # If no fallback is available, try to use the shortname or just remove it
                shortname = emoji.get('data-emoji-shortname')
                if shortname:
                    # Remove the colons from shortname if present
                    clean_shortname = shortname.strip(':')
                    emoji_text = self.soup.new_string(f":{clean_shortname}:")
                    emoji.replace_with(emoji_text)
                else:
                    # If no viable alternative, remove the emoji
                    emoji.decompose()


    def _remove_confluence_specific(self) -> None:
        """Remove Confluence-specific elements and unwrap their content."""
        # Remove Confluence macros and wrappers
        confluence_selectors = [
            '[data-macro-name]',
            '.confluence-information-macro',
            '.expand-container',
            '.confluence-embedded-file-wrapper',
            '.contentLayout2',
            '.columnLayout',
            '.hidden-section',
            '.toc-macro',
        ]

        for selector in confluence_selectors:
            for element in self.soup.select(selector):
                # Instead of unwrapping, decompose the TOC completely
                if 'toc-macro' in element.get('class', []):
                    element.decompose()
                else:
                    element.unwrap()

        # Remove Confluence-specific styles and scripts
        for style_tag in self.soup.find_all('style'):
            if 'confluence' in style_tag.get_text():
                style_tag.decompose()
        for script_tag in self.soup.find_all('script'):
            if 'confluence' in script_tag.get_text():
                script_tag.decompose()

    def _convert_column_layouts(self) -> None:
        """
        Convert Confluence column layouts into HTML tables.
        """
        # Define the list of layout types
        layout_types = ['two-equal', 'two-right-sidebar', 'two-left-sidebar', 'three-equal', 'three-with-sidebars']

        # Build a selector that matches divs with class 'columnLayout' and any of the layout types
        layout_selectors = [f"div.columnLayout.{layout}" for layout in layout_types]

        # Mapping of width percentages to class names
        width_class_mapping = {
            '25%': 'column-25',
            '33%': 'column-33',
            '50%': 'column-50',
            '67%': 'column-67',
            '75%': 'column-75',
            '100%': 'column-100',
        }

        # Find all matching divs
        for selector in layout_selectors:
            for layout_div in self.soup.select(selector):
                try:
                    # Get the layout type from the class or data-layout attribute
                    layout_type = layout_div.get('data-layout', None)
                    if not layout_type:
                        # If data-layout is not set, try to extract from class
                        layout_classes = layout_div.get('class', [])
                        for cls in layout_classes:
                            if cls in layout_types:
                                layout_type = cls
                                break

                    if not layout_type:
                        continue  # Skip if layout type is not identified

                    # Get the cells
                    cells = layout_div.find_all('div', class_='cell', recursive=False)
                    num_cells = len(cells)

                    # Determine column widths based on layout type
                    if layout_type == 'two-equal':
                        col_widths = ['50%', '50%']
                    elif layout_type == 'two-right-sidebar':
                        col_widths = ['33%', '67%']
                    elif layout_type == 'two-left-sidebar':
                        col_widths = ['67%', '33%']
                    elif layout_type == 'three-equal':
                        col_widths = ['33%', '33%', '33%']
                    elif layout_type == 'three-with-sidebars':
                        col_widths = ['25%', '50%', '25%']
                    else:
                        # Default widths
                        col_widths = ['100%'] * num_cells

                    # Create the table
                    table = self.soup.new_tag('table')
                    table_row = self.soup.new_tag('tr')
                    table.append(table_row)

                    # Populate the table cells
                    for idx, cell_div in enumerate(cells):
                        # Create table cell
                        td = self.soup.new_tag('td')

                        # Assign width class
                        width_class = width_class_mapping.get(col_widths[idx], '')
                        if width_class:
                            td['class'] = [width_class]

                        # Move the content from the cell's innerCell div
                        inner_cell = cell_div.find('div', class_='innerCell')
                        if inner_cell:
                            inner_contents = inner_cell.contents[:]
                            for content in inner_contents:
                                td.append(content)
                        else:
                            cell_contents = cell_div.contents[:]
                            for content in cell_contents:
                                td.append(content)

                        table_row.append(td)

                    # Replace the original layout div with the table
                    layout_div.replace_with(table)

                except Exception as e:
                    self.logger.error(f"Error converting column layout: {e}", exc_info=True)

    def _process_status_macros(self) -> None:
        """Process Confluence status macros and convert them to styled text."""
        status_class_mapping = {
            'aui-lozenge-success': 'status-green',
            'aui-lozenge-error': 'status-red',
            'aui-lozenge-current': 'status-yellow',
            'aui-lozenge-complete': 'status-blue',
            'aui-lozenge-progress': 'status-purple',
            'aui-lozenge-moved': 'status-teal',  # If needed
            'aui-lozenge': 'status-gray',  # Default gray status
        }
        
        for span in self.soup.find_all('span', class_='status-macro'):
            classes = span.get('class', [])
            status_class = 'status-gray'  # Default to gray

            # Check all classes and prioritize specific status classes over the default
            for cls in classes:
                if cls in status_class_mapping:
                    # The more specific classes (like aui-lozenge-progress) will override 
                    # the default 'aui-lozenge' class
                    status_class = status_class_mapping[cls]

            # Get the text content
            text_content = span.get_text(strip=True)

            # Create new <strong> tag
            strong_tag = self.soup.new_tag('strong')
            strong_tag.string = text_content
            strong_tag['class'] = [status_class]

            # Wrap in <p> if not already in a paragraph
            parent = span.parent
            if parent.name != 'p':
                p_tag = self.soup.new_tag('p')
                p_tag.append(strong_tag)
                span.replace_with(p_tag)
            else:
                # Replace the span with strong_tag
                span.replace_with(strong_tag)
    
    def _unwrap_table_wrappers(self) -> None:
        """Unwrap tables from div.table-wrap elements."""
        for wrapper in self.soup.find_all('div', class_='table-wrap'):
            # Replace the wrapper div with its table content
            table = wrapper.find('table')
            if table:
                wrapper.replace_with(table)
            else:
                # If no table found, unwrap the div
                wrapper.unwrap()

    def _process_expand_containers(self) -> None:
        """Process Confluence expand macros and convert them to styled containers."""
        for expand_div in self.soup.find_all('div', class_='expand-container'):
            # Create a new container div
            new_container = self.soup.new_tag('div')
            new_container['class'] = ['expand-box']  # Class for styling
            
            # Process expand-control
            expand_control = expand_div.find('div', class_='expand-control')
            if expand_control:
                # Get the text from expand-control-text
                control_text_span = expand_control.find('span', class_='expand-control-text')
                if control_text_span:
                    control_text = control_text_span.get_text(strip=True)
                    
                    # Create an <em> element with the control text
                    em_tag = self.soup.new_tag('em')
                    em_tag.string = control_text
                    
                    # Add the <em> to the new container
                    new_container.append(em_tag)
                    
            # Process expand-content
            expand_content = expand_div.find('div', class_='expand-content')
            if expand_content:
                # Move all contents of expand-content into the new container
                content_elements = expand_content.contents[:]
                for element in content_elements:
                    new_container.append(element)
            
            # Replace the original expand-container with the new container
            expand_div.replace_with(new_container)

    def _process_decision_lists(self) -> None:
        """Process Confluence decision lists and convert them to styled boxes."""
        for decision_list in self.soup.find_all('ul', class_='decision-list'):
            # Create a new container div
            decision_box = self.soup.new_tag('div')
            decision_box['class'] = ['decision-box']  # Class for styling
            
            # Create an <em> tag with the text "DECISÃO"
            em_tag = self.soup.new_tag('em')
            em_tag.string = 'DECISÃO'
            decision_box.append(em_tag)
            
            # Process each <li> in the decision list
            for li in decision_list.find_all('li'):
                # Move the contents of <li> into the decision box
                li_contents = li.contents[:]
                for content in li_contents:
                    decision_box.append(content)
            
            # Replace the original decision list with the new decision box
            decision_list.replace_with(decision_box)
