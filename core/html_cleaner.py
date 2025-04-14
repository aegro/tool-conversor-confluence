#!/usr/bin/env python3
"""
HTML Cleaner Module for Confluence Export Processing

This module provides functionality to clean and standardize HTML content exported from Confluence.
The main component is the HTMLCleaner class, which handles:

1. Removal of Confluence-specific classes, IDs, and scripts
2. Standardization of HTML structure and formatting
3. Processing of embedded resources (images, attachments)
4. Fixing relative links and paths
5. Injecting custom CSS styles for better rendering
6. Preparing HTML for potential DOCX conversion

The module applies best practices for HTML cleaning and normalization while preserving
the content and structure of the original document.

Usage:
    cleaner = HTMLCleaner(html_content, target_directory)
    cleaned_html = cleaner.clean()
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Optional, Set, List, Union, Tuple
from urllib.parse import urlparse, urljoin
import base64
from mimetypes import guess_type

from bs4 import BeautifulSoup, Comment, Tag
from utils.utilities import get_config


class HTMLCleaner:
    """
    Clean and standardize HTML content exported from Confluence.

    This class handles comprehensive cleaning of Confluence HTML exports, including:
    - Removing unnecessary elements and attributes
    - Standardizing classes and structure
    - Processing embedded resources like images
    - Fixing links and references
    - Applying custom styling

    Attributes:
        soup (BeautifulSoup): The parsed HTML document
        target_dir (Path): Directory for saving processed resources
        config (Dict): Configuration settings
        logger (logging.Logger): Logger instance
        title (str): Extracted document title
        confluence_classes (Set[str]): Confluence-specific classes to remove
        confluence_ids (Set[str]): Confluence-specific IDs to remove
    """

    def __init__(
        self, html_content: str, target_dir: Path, config: Optional[Dict] = None
    ):
        """
        Initialize HTMLCleaner with content and configuration.

        Args:
            html_content (str): Raw HTML content to clean
            target_dir (Path): Directory for saving processed resources
            config (Optional[Dict]): Configuration override. Defaults to None
        """
        # Parse HTML with lxml parser for better handling
        self.soup = BeautifulSoup(html_content, "lxml")
        self.target_dir = Path(target_dir)
        self.config = config or get_config()
        self.logger = logging.getLogger(__name__)

        # Extract standard classes from config
        self.standard_classes = self.config.get("standard_html_classes", {})

        # Extract title for later use
        self.title = self._extract_title()

        # Define Confluence-specific classes and IDs to remove
        # These are known Confluence classes that are not needed in the output
        self.confluence_classes = set(
            [
                # Classes to remove
                "theme-default",
                "aui-theme-default",
                "first",
                "pagetitle",
                "wiki-content",
                "group",
                "contentLayout2",
                "columnLayout",
                "fixed-width",
                "cell",
                "normal",
                "innerCell",
                "toc-macro",
                "toc-indentation",
                "confluenceTable",
                "confluenceTd",
                "emoticon",
                "emoticon-blue-star",
                "image-center-wrapper",
                "confluence-embedded-image",
                "image-center",
                "panel",
                "panelContent",
                "inline-task-list",
                "placeholder-inline-tasks",
                "confluence-userlink",
                "user-mention",
                "current-user-mention",
                "date-upcoming",
                "date-future",
                "confluenceTh",
                "confluence-information-macro",
                "confluence-information-macro-information",
                "aui-icon",
                "aui-icon-small",
                "aui-iconfont-info",
                "confluence-information-macro-icon",
                "confluence-information-macro-body",
                "confluence-embedded-file-wrapper",
                "expand-container",
                "expand-control",
                "expand-control-icon",
                "expand-control-image",
                "expand-control-text",
                "expand-content",
                "status-macro",
                "aui-lozenge",
                "aui-lozenge-progress",
                "aui-lozenge-complete",
                "table-wrapper",
                "task-blanket",
                "aui",
                "tasks-table-interactive",
                "tasks-report",
                "tablesorter-headerRow",
                "header-description",
                "tasks-table-column-unsortable",
                "header-duedate",
                "header-assignee",
                "header-location",
                "tasks-report-date",
                "tasks-report-assignee",
                "task-location",
                "greybox",
                "footer-body",
                "external-link",
                "url",
                "fn",
                "aui-page-panel",
                "view",
                "data-colorid",
                "expand-container",
                "expand-control",
                "expand-control-icon",
                "expand-control-image",
                "expand-control-text",
                "expand-content",
                "decision-list",
            ]
        )

        self.confluence_ids = set(
            [
                # IDs to remove
                "page",
                "main",
                "main-header",
                "breadcrumb-section",
                "breadcrumbs",
                "title-heading",
                "title-text",
                "content",
                "main-content",
                "attachments",
                "footer",
                "footer-logo",
                "data-inline-tasks-content-id",
            ]
        )

    def _inject_custom_styles(self) -> None:
        """
        Inject custom CSS styles into the HTML document.

        This method removes any existing style tags from the body (which might contain
        Confluence-specific styling) and adds our own custom CSS for better
        presentation in browsers and DOCX output.
        """
        # First, remove any existing style tags from the body
        for style_tag in self.soup.find_all("style"):
            if style_tag.parent.name != "head":
                style_tag.decompose()

        # Custom CSS styles that will be injected into the document head
        # These styles improve readability and presentation
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

            /* Code Block Styles */
            .code-block {
                margin: 1.5em 0;
                border-radius: 6px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
            }

            .code-language {
                background-color: #046062;
                color: white;
                font-size: 0.8em;
                padding: 4px 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .code-content {
                overflow-x: auto;
            }

            .code-content pre {
                margin: 0;
                padding: 16px;
                overflow-x: auto;
                background-color: #282c34;
                color: #f8f8f2;
                line-height: 1.5;
                font-size: 14px;
            }

            /* Language-specific syntax highlighting */
            .language-java .keyword,
            .language-javascript .keyword, 
            .language-python .keyword {
                color: #ff79c6;
            }

            .language-java .string,
            .language-javascript .string,
            .language-python .string {
                color: #f1fa8c;
            }

            .language-java .comment,
            .language-javascript .comment,
            .language-python .comment {
                color: #6272a4;
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
            head = self.soup.new_tag("head")
            if self.soup.html:
                self.soup.html.insert(0, head)

        # Add Google Fonts link for Code fonts
        fonts_link = self.soup.new_tag("link")
        fonts_link["rel"] = "stylesheet"
        fonts_link["href"] = (
            "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700&family=JetBrains+Mono:wght@400;700&family=Roboto:wght@400;700&display=swap"
        )
        head.append(fonts_link)

        # Add custom styles
        style_tag = self.soup.new_tag("style")
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
            self._process_code_blocks()
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
            return "<!DOCTYPE html>\n" + str(self.soup.html.prettify(formatter="html5"))

        except Exception as e:
            self.logger.error(f"Error cleaning HTML: {e}", exc_info=True)
            raise

    def _extract_title(self) -> str:
        """Extract and clean page title."""
        title_tag = self.soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        return "Untitled Document"

    def _remove_unnecessary_sections(self) -> None:
        """Remove unnecessary page sections."""
        # List of selectors for elements to remove
        selectors_to_remove = [
            # Remove Confluence footer and metadata
            "div#footer",
            "div.footer-body",
            "section.footer-body",
            'div[role="contentinfo"]',
            "div#footer-logo",
            "div.page-metadata",
            "div#breadcrumb-section",
            "script",
            # Remove Confluence-specific styles and links
            'link[rel="stylesheet"][href*="confluence"]',
            'meta[name*="confluence"]',
            'link[href="styles/site.css"]',
        ]

        for selector in selectors_to_remove:
            for element in self.soup.select(selector):
                element.decompose()

        # Additional specific footer text removal
        for p in self.soup.find_all("p"):
            if "Document generated by Confluence" in p.get_text():
                p.decompose()

        # Remove HTML comments
        for comment in self.soup.find_all(
            string=lambda text: isinstance(text, Comment)
        ):
            comment.extract()

    def _clean_metadata(self) -> None:
        """Clean and standardize metadata elements."""
        # Update page metadata
        metadata_div = self.soup.find("div", class_="page-metadata")
        if metadata_div:
            # Replace English metadata terms with Portuguese
            translations = {
                "Created by": "Criado por",
                "on": "em",
                "Last modified by": "Última modificação por",
                "at": "às",
            }

            for old_text, new_text in translations.items():
                for text in metadata_div.find_all(string=re.compile(old_text)):
                    text.replace_with(text.replace(old_text, new_text))

    def _clean_attributes_and_classes(self) -> None:
        """Clean and standardize HTML attributes and classes."""
        for tag in self.soup.find_all(True):
            # Skip image tags here as they are handled in _process_images
            if tag.name == "img":
                continue

            # Remove Confluence-specific IDs
            if "id" in tag.attrs:
                if tag["id"] in self.confluence_ids or tag["id"].startswith(
                    "expander-"
                ):
                    del tag["id"]

            # Remove Confluence-specific classes
            if "class" in tag.attrs:
                cleaned_classes = [
                    cls for cls in tag["class"] if cls not in self.confluence_classes
                ]
                if cleaned_classes:
                    tag["class"] = cleaned_classes
                else:
                    del tag["class"]

            # Remove all data-* attributes
            for attr in list(tag.attrs):
                if attr.startswith("data-"):
                    del tag[attr]
                elif attr == "style":
                    # Optionally, you can clean or keep styles
                    pass  # Keep styles unless they are Confluence-specific

    def _process_images(self) -> None:
        """
        Clean image elements and embed them using Base64 encoding.
        - Removes unnecessary attributes
        - Preserves essential attributes (alt, title, width, height)
        - Embeds image data directly into the src attribute.
        """
        for img in self.soup.find_all("img"):
            original_src = "N/A"
            try:
                # Handle Confluence icons and bullets (remove them completely)
                if img.get("src") and any(icon in img["src"] for icon in [
                    "bullet_blue.gif", 
                    "wait.gif", 
                    "grey_arrow_down.png",
                    # Add any other common icons/gifs to remove
                    "check.png",
                    "error.png", 
                    "help_16.png",
                ]):
                    self.logger.info(f"Removing Confluence icon/bullet image: {img.get('src')}")
                    img.decompose()
                    continue
                    
                if "src" not in img.attrs or not img.attrs["src"]:
                    self.logger.warning(
                        "Image tag found without 'src' attribute. Removing tag."
                    )
                    img.decompose()
                    continue

                original_src = img.attrs["src"]
                image_path = None

                # Clean the original_src by removing query parameters
                clean_src = (
                    original_src.split("?")[0] if "?" in original_src else original_src
                )
                self.logger.debug(
                    f"Original src: '{original_src}', Clean src (removed query params): '{clean_src}'"
                )

                # Check if src is already an absolute path (potentially set by previous logic)
                potential_abs_path = Path(clean_src)
                if potential_abs_path.is_absolute() and potential_abs_path.is_file():
                    image_path = potential_abs_path
                    self.logger.debug(
                        f"Strategy 1 (absolute path): Successfully resolved image path: {image_path}"
                    )
                # Check if src is a relative path that needs resolving
                elif not clean_src.startswith(("http://", "https://", "data:")):
                    self.logger.debug(
                        f"Starting image path resolution for: '{clean_src}' from '{self.target_dir}'"
                    )

                    # Strategy 1: Relative to the HTML file's directory (self.target_dir)
                    potential_path_1 = self.target_dir / clean_src
                    self.logger.debug(
                        f"Strategy 1: Trying path relative to HTML file: {potential_path_1}"
                    )
                    if potential_path_1.resolve().is_file():
                        image_path = potential_path_1.resolve()
                        self.logger.debug(
                            f"Strategy 1: Successfully resolved relative path: {image_path}"
                        )
                    else:
                        self.logger.debug(
                            f"Strategy 1: Failed to find image at: {potential_path_1}"
                        )

                        # Strategy 2: Relative to the *parent* directory if src is in 'attachments' or 'images'
                        # (Assumes HTML is in a subfolder, resources are one level up)
                        if (
                            "attachments/" in clean_src or "images/" in clean_src
                        ) and self.target_dir.parent:
                            resource_folder = (
                                "attachments"
                                if "attachments/" in clean_src
                                else "images"
                            )
                            # Get the part after 'attachments/' or 'images/'
                            relative_to_resource_folder = clean_src.split(
                                f"{resource_folder}/", 1
                            )[-1]
                            potential_path_2 = (
                                self.target_dir.parent
                                / resource_folder
                                / relative_to_resource_folder
                            )
                            self.logger.debug(
                                f"Strategy 2: Trying path one level up from HTML file: {potential_path_2}"
                            )
                            if potential_path_2.resolve().is_file():
                                image_path = potential_path_2.resolve()
                                self.logger.debug(
                                    f"Strategy 2: Successfully resolved relative path: {image_path}"
                                )
                            else:
                                self.logger.debug(
                                    f"Strategy 2: Failed to find image at: {potential_path_2}"
                                )

                                # Strategy 3: Recursive search upwards to find attachments or images folders
                                if resource_folder in ["attachments", "images"]:
                                    self.logger.debug(
                                        f"Strategy 3: Starting recursive search upwards to find {resource_folder} directory"
                                    )
                                    # Start from the directory containing the HTML file and go up
                                    current_dir = self.target_dir
                                    search_attempts = 0
                                    max_attempts = 10  # Prevent infinite loops by limiting search depth

                                    while (
                                        current_dir and search_attempts < max_attempts
                                    ):
                                        self.logger.debug(
                                            f"Strategy 3: Searching at level {search_attempts} in {current_dir}"
                                        )
                                        # Look for resource folder at this level
                                        resource_dir = current_dir / resource_folder
                                        potential_path_3 = (
                                            resource_dir / relative_to_resource_folder
                                        )
                                        self.logger.debug(
                                            f"Strategy 3: Checking for image at: {potential_path_3}"
                                        )

                                        if potential_path_3.resolve().is_file():
                                            image_path = potential_path_3.resolve()
                                            self.logger.debug(
                                                f"Strategy 3: Successfully resolved path at depth {search_attempts}: {image_path}"
                                            )
                                            break
                                        elif resource_dir.is_dir():
                                            self.logger.debug(
                                                f"Strategy 3: Found resource directory at {resource_dir} but image not found"
                                            )

                                        # Move up one level
                                        if (
                                            current_dir.parent == current_dir
                                        ):  # Reached root
                                            self.logger.debug(
                                                "Strategy 3: Reached filesystem root, stopping search"
                                            )
                                            break

                                        current_dir = current_dir.parent
                                        search_attempts += 1

                                    if (
                                        not image_path
                                        and search_attempts >= max_attempts
                                    ):
                                        self.logger.debug(
                                            f"Strategy 3: Reached max search depth ({max_attempts}), stopping search"
                                        )
                        else:
                            self.logger.debug(
                                f"Strategy 2/3: Resource folder pattern not found in path or no parent directory"
                            )

                    # Strategy 4: Fallback - Check if original_src string *itself* is a valid absolute path (maybe set previously)
                    if not image_path and potential_abs_path.is_file():
                        image_path = potential_abs_path
                        self.logger.debug(
                            f"Strategy 4 (fallback): Treating original src as absolute path: {image_path}"
                        )

                # --- Start Base64 Embedding ---
                if image_path and image_path.is_file():
                    try:
                        self.logger.debug(
                            f"Image found! Attempting to embed image from: {image_path}"
                        )
                        with open(image_path, "rb") as image_file:
                            image_data = image_file.read()

                        # Guess MIME type based on file extension
                        mime_type, _ = guess_type(image_path)
                        if mime_type is None:
                            mime_type = "application/octet-stream"  # Default if unknown
                        self.logger.debug(
                            f"Determined MIME type: {mime_type} for {image_path.name}"
                        )

                        # Encode image data in Base64
                        base64_data = base64.b64encode(image_data).decode("utf-8")
                        # Create the data URI
                        img["src"] = f"data:{mime_type};base64,{base64_data}"
                        self.logger.info(
                            f"Successfully embedded image {image_path.name} using Base64"
                        )

                    except FileNotFoundError:
                        self.logger.warning(
                            f"Image file not found during embedding attempt: {image_path}. Removing img tag."
                        )
                        img.decompose()
                        continue
                    except Exception as e:
                        self.logger.error(
                            f"Error reading or embedding image {image_path}: {e}. Removing img tag.",
                            exc_info=True,
                        )
                        img.decompose()
                        continue
                else:
                    # Handle cases where src is a URL or file doesn't exist/couldn't be resolved
                    if original_src.startswith(("http://", "https://")):
                        self.logger.warning(
                            f"Keeping external image URL: {original_src}. Google Drive might not fetch it."
                        )
                        # Optionally: Try to download and embed? Adds complexity. For now, keep URL.
                        pass  # Keep the original src
                    elif original_src.startswith("data:"):
                        # Already Base64 encoded, leave it alone
                        self.logger.info("Image already has data URI src. Skipping.")
                        pass  # Keep the original src
                    else:
                        self.logger.warning(
                            f"Local image path could not be resolved: '{original_src}'. Tried multiple strategies but failed to find the file. Removing img tag."
                        )
                        img.decompose()
                        continue
                # --- End Base64 Embedding ---

                # Keep only essential attributes after processing src
                # Ensure 'src' is preserved if it was successfully updated or kept
                if img.has_attr("src"):
                    allowed_attrs = {"src", "alt", "title", "width", "height", "style"}
                    current_attrs = set(img.attrs.keys())

                    # Remove unwanted attributes
                    for attr in current_attrs - allowed_attrs:
                        # Keep style attribute if it's not explicitly confluence related
                        if attr == "style" and "confluence" not in img.attrs.get(
                            "style", ""
                        ):
                            self.logger.debug(
                                f"Keeping non-confluence style attribute for image: {img.attrs['style']}"
                            )
                            continue
                        # Check if attribute still exists before deleting (might have been removed if tag decomposed)
                        if img.has_attr(attr):
                            self.logger.debug(
                                f"Removing attribute '{attr}' from image tag."
                            )
                            del img[attr]

                    # Ensure alt attribute exists if tag still exists
                    if not img.has_attr("alt"):
                        # Use filename stem if available, otherwise generic text
                        alt_text = (
                            image_path.stem
                            if image_path and image_path.is_file()
                            else "Embedded Image"
                        )
                        img["alt"] = alt_text
                        self.logger.debug(f"Added missing alt attribute: '{alt_text}'")

            except Exception as e:
                self.logger.error(
                    f"General error processing image tag with original src '{original_src}': {e}",
                    exc_info=True,
                )
                # Ensure tag is removed if any error occurs
                if img and img.parent:  # Check if tag still exists and has a parent
                    img.decompose()

    def _process_links(self) -> None:
        """Clean and process link elements."""
        for link in self.soup.find_all("a"):
            # Remove JavaScript events
            for attr in list(link.attrs):
                if attr.startswith("on"):
                    del link[attr]

            # Clean href attribute
            if "href" in link.attrs:
                href = link["href"]
                if href.startswith("javascript:"):
                    del link["href"]
                elif "confluence" in href and "people" in href:
                    # Convert user links to text
                    link.replace_with(link.get_text())
                elif "mailto:" in href:
                    # Keep mailto links
                    pass
                else:
                    # Adjust relative links if necessary
                    pass  # Implement any adjustments needed for your context

            # Remove Confluence-specific classes
            if "class" in link.attrs:
                cleaned_classes = [
                    cls for cls in link["class"] if cls not in self.confluence_classes
                ]
                if cleaned_classes:
                    link["class"] = cleaned_classes
                else:
                    del link["class"]

    def _clean_tables(self) -> None:
        """Clean and standardize table elements."""
        for table in self.soup.find_all("table"):
            # Remove Confluence-specific classes and IDs
            if "class" in table.attrs:
                cleaned_classes = [
                    cls for cls in table["class"] if cls not in self.confluence_classes
                ]
                if cleaned_classes:
                    table["class"] = cleaned_classes
                else:
                    del table["class"]

            # Add 'custom-table' class
            table_classes = table.get("class", [])
            table_classes.append("custom-table")
            table["class"] = table_classes

            # Remove deprecated attributes and inline styles
            for attr in ["border", "cellspacing", "cellpadding", "style"]:
                if attr in table.attrs:
                    del table[attr]

            # Clean table cells
            for cell in table.find_all(["td", "th"]):
                # Remove Confluence-specific classes
                if "class" in cell.attrs:
                    cleaned_classes = [
                        cls
                        for cls in cell["class"]
                        if cls not in self.confluence_classes
                    ]
                    if cleaned_classes:
                        cell["class"] = cleaned_classes
                    else:
                        del cell["class"]
                # Remove inline styles
                if "style" in cell.attrs:
                    del cell["style"]
                # Remove unwanted attributes
                allowed_cell_attrs = {"colspan", "rowspan", "class"}
                for attr in list(cell.attrs):
                    if attr not in allowed_cell_attrs:
                        del cell[attr]

    def _standardize_headings(self) -> None:
        """Standardize heading hierarchy and formatting."""
        heading_levels = ["h1", "h2", "h3", "h4", "h5", "h6"]
        current_level = 0

        for heading in self.soup.find_all(heading_levels):
            heading_level = int(heading.name[1])

            # Store the text content, removing any extra formatting but preserving the actual text
            text_content = heading.get_text(strip=True)

            # Create a new clean heading tag
            new_heading = self.soup.new_tag(f"h{heading_level}")
            new_heading.string = text_content

            # Replace the old heading with the clean one
            heading.replace_with(new_heading)

            # Update current level for hierarchy maintenance
            current_level = heading_level

    def _clean_lists(self) -> None:
        """Clean and standardize list elements."""
        # Regular list cleaning
        for list_tag in self.soup.find_all(["ul", "ol"]):
            # Clean list items
            for item in list_tag.find_all("li"):
                if "class" in item.attrs:
                    cleaned_classes = [
                        cls
                        for cls in item["class"]
                        if cls not in self.confluence_classes
                    ]
                    if cleaned_classes:
                        item["class"] = cleaned_classes
                    else:
                        del item["class"]

                # Remove unnecessary attributes
                for attr in list(item.attrs):
                    if attr not in {"class", "value"}:
                        del item[attr]

    def _remove_empty_elements(self) -> None:
        """Remove empty elements that serve no purpose."""
        # Elements that should be removed if empty
        tags_to_check = ["p", "div", "span", "strong", "em", "i", "b"]

        for tag in self.soup.find_all(tags_to_check):
            if not tag.get_text(strip=True) and not tag.find_all(["img", "br"]):
                tag.decompose()

    def _cleanup_whitespace(self) -> None:
        """Clean up excessive whitespace in HTML."""
        # Clean up text nodes while preserving spaces around inline elements
        inline_elements = {"strong", "em", "i", "b", "span", "a", "code"}

        for text in self.soup.find_all(string=True):
            if text.parent.name not in ["pre", "code"]:
                # Only collapse multiple spaces into single space
                cleaned_text = re.sub(r"\s+", " ", text.string)
                # Only strip if not adjacent to inline elements
                if text.parent.name not in inline_elements and not (
                    text.next_sibling
                    and getattr(text.next_sibling, "name", None) in inline_elements
                    or text.previous_sibling
                    and getattr(text.previous_sibling, "name", None) in inline_elements
                ):
                    cleaned_text = cleaned_text.strip()
                text.replace_with(cleaned_text)

    def _add_missing_title(self) -> None:
        """Add title element if missing."""
        if not self.soup.title:
            head = self.soup.head or self.soup.new_tag("head")
            if not self.soup.head:
                self.soup.html.insert(0, head)

            title = self.soup.new_tag("title")
            title.string = self.title
            head.append(title)

    def _ensure_meta_charset(self) -> None:
        """Ensure that the <meta charset="UTF-8"> tag is present."""
        if self.soup.head:
            if not self.soup.head.find("meta", charset=True):
                meta = self.soup.new_tag("meta", charset="UTF-8")
                self.soup.head.insert(0, meta)
        else:
            # Create head if missing
            head = self.soup.new_tag("head")
            meta = self.soup.new_tag("meta", charset="UTF-8")
            head.append(meta)
            self.soup.html.insert(0, head)

    def _process_emojis(self) -> None:
        """Convert Confluence emoji images to their Unicode equivalents."""
        emoji_elements = self.soup.find_all("img", class_="emoticon")

        for emoji in emoji_elements:
            # Get the emoji data
            emoji_fallback = emoji.get("data-emoji-fallback")

            if emoji_fallback:
                # Create a new text node with the Unicode emoji
                emoji_text = self.soup.new_string(emoji_fallback)
                # Replace the img tag with the text node
                emoji.replace_with(emoji_text)
                self.logger.debug(f"Replaced emoji image with Unicode character: {emoji_fallback}")
            else:
                # If no fallback is available, try to use the shortname or just remove it
                shortname = emoji.get("data-emoji-shortname")
                if shortname:
                    # Remove the colons from shortname if present
                    clean_shortname = shortname.strip(":")
                    emoji_text = self.soup.new_string(f":{clean_shortname}:")
                    emoji.replace_with(emoji_text)
                else:
                    # If no viable alternative, remove the emoji
                    emoji.decompose()

    def _remove_confluence_specific(self) -> None:
        """Remove Confluence-specific elements and unwrap their content."""
        # Remove Confluence macros and wrappers
        confluence_selectors = [
            "[data-macro-name]",
            ".confluence-information-macro",
            ".confluence-embedded-file-wrapper",
            ".hidden-section",
            ".toc-macro",
        ]

        for selector in confluence_selectors:
            for element in self.soup.select(selector):
                # Instead of unwrapping, decompose the TOC completely
                if element.name == "div" and "toc-macro" in element.get("class", []):
                    self.logger.info("Decomposing TOC macro.")
                    element.decompose()
                # Don't unwrap elements we process separately
                elif element.name == "div" and (
                    "expand-container" in element.get("class", [])
                    or "contentLayout2" in element.get("class", [])
                    or "columnLayout" in element.get("class", [])
                ):
                    self.logger.debug(
                        f"Skipping unwrap for element processed separately: {element.name}.{'.'.join(element.get('class',[]))}"
                    )
                    pass
                else:
                    # Unwrap other matched elements
                    self.logger.debug(
                        f"Unwrapping element matched by selector '{selector}': {element.name}"
                    )
                    element.unwrap()

        # Remove Confluence-specific styles and scripts that might remain
        for style_tag in self.soup.find_all("style"):
            # More robust check for Confluence-specific styles
            style_content = style_tag.get_text()
            if (
                "confluence" in style_content
                or "aui-" in style_content
                or ".wiki-content" in style_content
            ):
                self.logger.debug(f"Decomposing Confluence style tag.")
                style_tag.decompose()
        for script_tag in self.soup.find_all("script"):
            script_content = script_tag.get_text()
            if (
                "confluence" in script_content
                or "AJS" in script_content
                or "WRM" in script_content
            ):
                self.logger.debug(f"Decomposing Confluence script tag.")
                script_tag.decompose()

    def _convert_column_layouts(self) -> None:
        """
        Convert Confluence column layouts into divs with appropriate width classes.
        """
        # Find column layout sections
        for layout_section in self.soup.select("div.columnLayout"):
            cells = layout_section.find_all("div", class_="cell", recursive=False)
            num_cells = len(cells)

            if num_cells == 0:
                layout_section.unwrap()  # Remove empty layout wrapper
                continue

            # Determine column widths based on classes or number of cells
            width_classes = []
            layout_type = None
            possible_layouts = [
                "two-equal",
                "two-left-sidebar",
                "two-right-sidebar",
                "three-equal",
                "three-with-sidebars",
            ]
            for cls in layout_section.get("class", []):
                if cls in possible_layouts:
                    layout_type = cls
                    break

            if layout_type == "two-equal":
                width_classes = ["column-50", "column-50"]
            elif layout_type == "two-left-sidebar":  # Wider left column
                width_classes = [
                    "column-67",
                    "column-33",
                ]  # Example widths, adjust as needed
            elif layout_type == "two-right-sidebar":  # Wider right column
                width_classes = ["column-33", "column-67"]  # Example widths
            elif layout_type == "three-equal":
                width_classes = ["column-33", "column-33", "column-33"]
            elif layout_type == "three-with-sidebars":
                width_classes = ["column-25", "column-50", "column-25"]
            else:
                # Default if layout type class is missing or unknown - distribute equally
                if num_cells == 2:
                    width_classes = ["column-50", "column-50"]
                elif num_cells == 3:
                    width_classes = ["column-33", "column-33", "column-33"]
                else:
                    width_classes = ["column-100"]  # Fallback for single or > 3 cells

            # Ensure width_classes list matches num_cells
            if len(width_classes) != num_cells:
                self.logger.warning(
                    f"Column count ({num_cells}) mismatch with inferred layout '{layout_type}'. Defaulting to equal widths."
                )
                if num_cells == 2:
                    width_classes = ["column-50", "column-50"]
                elif num_cells == 3:
                    width_classes = ["column-33", "column-33", "column-33"]
                else:
                    width_classes = [
                        "column-100"
                    ] * num_cells  # Distribute as best we can

            # Create a new container div to replace the columnLayout section
            container_div = self.soup.new_tag(
                "div", attrs={"class": "column-container"}
            )

            for i, cell in enumerate(cells):
                # Create a new div for this column
                column_div = self.soup.new_tag("div")
                # Apply the calculated width class
                column_div["class"] = width_classes[i]
                # Move the content from the original cell div to the new column div
                column_div.extend(cell.contents)
                container_div.append(column_div)

            # Replace the original layout section with the new container div
            layout_section.replace_with(container_div)

    def _process_status_macros(self) -> None:
        """Process Confluence status macros and convert them to styled text."""
        status_class_mapping = {
            "aui-lozenge-success": "status-green",
            "aui-lozenge-error": "status-red",
            "aui-lozenge-current": "status-yellow",
            "aui-lozenge-complete": "status-blue",
            "aui-lozenge-progress": "status-purple",
            "aui-lozenge-moved": "status-teal",  # If needed
            "aui-lozenge": "status-gray",  # Default gray status
        }

        for span in self.soup.find_all("span", class_="status-macro"):
            classes = span.get("class", [])
            status_class = "status-gray"  # Default to gray

            # Check all classes and prioritize specific status classes over the default
            for cls in classes:
                if cls in status_class_mapping:
                    # The more specific classes (like aui-lozenge-progress) will override
                    # the default 'aui-lozenge' class
                    status_class = status_class_mapping[cls]

            # Get the text content
            text_content = span.get_text(strip=True)

            # Create new <strong> tag
            strong_tag = self.soup.new_tag("strong")
            strong_tag.string = text_content
            strong_tag["class"] = [status_class]

            # Wrap in <p> if not already in a paragraph
            parent = span.parent
            if parent.name != "p":
                p_tag = self.soup.new_tag("p")
                p_tag.append(strong_tag)
                span.replace_with(p_tag)
            else:
                # Replace the span with strong_tag
                span.replace_with(strong_tag)

    def _unwrap_table_wrappers(self) -> None:
        """Unwrap tables from div.table-wrap elements."""
        for wrapper in self.soup.find_all("div", class_="table-wrapper"):
            # Find direct table children
            direct_tables = wrapper.find_all("table", recursive=False)
            # Check if the wrapper contains only whitespace and the table(s)
            is_simple_wrapper = True
            for child in wrapper.contents:
                if isinstance(child, Tag) and child.name == "table":
                    continue  # Skip tables
                if isinstance(child, str) and child.strip() == "":
                    continue  # Skip whitespace
                # Found something else
                is_simple_wrapper = False
                break

            if direct_tables and is_simple_wrapper:
                self.logger.debug(f"Unwrapping simple table wrapper div.")
                wrapper.unwrap()
            else:
                self.logger.debug(
                    f"Keeping table wrapper div as it contains other elements."
                )
                # Optional: remove the 'table-wrapper' class if keeping the div
                if "class" in wrapper.attrs:
                    wrapper["class"] = [
                        c for c in wrapper["class"] if c != "table-wrapper"
                    ]
                    if not wrapper["class"]:
                        del wrapper["class"]

    def _process_expand_containers(self) -> None:
        """Process Confluence expand macros and convert them to styled containers."""
        for expand_div in self.soup.find_all("div", class_="expand-container"):
            # Create a new container div
            new_container = self.soup.new_tag("div")
            new_container["class"] = ["expand-box"]  # Class for styling

            # Process expand-control
            expand_control = expand_div.find("div", class_="expand-control")
            if expand_control:
                # Get the text from expand-control-text
                control_text_span = expand_control.find(
                    "span", class_="expand-control-text"
                )
                if control_text_span:
                    control_text = control_text_span.get_text(strip=True)

                    # Create an <em> element with the control text
                    em_tag = self.soup.new_tag("em")
                    em_tag.string = control_text

                    # Add the <em> to the new container
                    new_container.append(em_tag)

            # Process expand-content
            expand_content = expand_div.find("div", class_="expand-content")
            if expand_content:
                # Move all contents of expand-content into the new container
                content_elements = expand_content.contents[:]
                for element in content_elements:
                    new_container.append(element)

            # Replace the original expand-container with the new container
            expand_div.replace_with(new_container)

    def _process_decision_lists(self) -> None:
        """Process Confluence decision lists and convert them to styled boxes."""
        for decision_list in self.soup.find_all("ul", class_="decision-list"):
            # Create a new container div
            decision_box = self.soup.new_tag("div")
            decision_box["class"] = ["decision-box"]  # Class for styling

            # Create an <em> tag with the text "DECISÃO"
            em_tag = self.soup.new_tag("em")
            em_tag.string = "DECISÃO"
            decision_box.append(em_tag)

            # Process each <li> in the decision list
            for li in decision_list.find_all("li"):
                # Move the contents of <li> into the decision box
                li_contents = li.contents[:]
                for content in li_contents:
                    decision_box.append(content)

            # Replace the original decision list with the new decision box
            decision_list.replace_with(decision_box)

    def _process_code_blocks(self) -> None:
        """Process Confluence code blocks and convert them to beautifully styled code snippets."""
        for code_div in self.soup.find_all("div", class_="code"):
            try:
                # Find the pre tag with syntaxhighlighter class
                pre_tag = code_div.find("pre", class_="syntaxhighlighter-pre")

                if pre_tag:
                    # Extract language information if available
                    language = "text"  # Default language
                    params = pre_tag.get("data-syntaxhighlighter-params", "")
                    brush_match = re.search(r"brush:\s*(\w+)", params)

                    if brush_match:
                        language = brush_match.group(1).lower()

                    # Create a new code block container
                    code_container = self.soup.new_tag("div")
                    code_container["class"] = ["code-block"]

                    # Add language indicator if available
                    if language != "text":
                        lang_indicator = self.soup.new_tag("div")
                        lang_indicator["class"] = ["code-language"]
                        lang_indicator.string = language.capitalize()
                        code_container.append(lang_indicator)

                    # Create code content div
                    code_content = self.soup.new_tag("div")
                    code_content["class"] = ["code-content"]

                    # Clean and preserve the code
                    code_text = pre_tag.get_text()
                    # Unescape HTML entities if present
                    code_text = (
                        code_text.replace("&quot;", '"')
                        .replace("&lt;", "<")
                        .replace("&gt;", ">")
                    )

                    # Create pre and code tags
                    new_pre = self.soup.new_tag("pre")
                    new_code = self.soup.new_tag("code")

                    if language != "text":
                        new_code["class"] = [f"language-{language}"]

                    new_code.string = code_text
                    new_pre.append(new_code)
                    code_content.append(new_pre)
                    code_container.append(code_content)

                    # Replace the original code div with the new container
                    code_div.replace_with(code_container)

            except Exception as e:
                self.logger.error(f"Error processing code block: {e}", exc_info=True)
