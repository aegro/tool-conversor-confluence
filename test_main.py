#!/usr/bin/env python3
"""
Test Suite for Confluence HTML Export Processor

This module contains comprehensive unit tests for the Confluence HTML Export Processor
application. The tests cover:

1. HTML cleaning functionality (removing Confluence-specific elements)
2. Breadcrumb extraction and processing
3. File and directory operations
4. Table and image processing
5. Various utility functions

Each test class focuses on a specific aspect of the application, and test methods
are named to clearly indicate what functionality they're testing.

To run these tests:
    python -m unittest test_main.py
    
Or with pytest:
    pytest test_main.py
"""

import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from unittest.mock import patch, Mock, mock_open
import shutil
import sys
import os
import requests

# Add parent directory to path to import main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import (clean_confluence_html, extract_breadcrumbs, create_directory_path,
                 process_html_file, setup_directory_structure, clean_attributes_and_classes,
                 remove_meta_elements, convert_user_links_to_strong, remove_all_scripts,
                 remove_all_styles, remove_all_links, replace_created_by_text,
                 remove_empty_divs_and_spans, remove_onclick_and_javascript_attributes,
                 clean_tables, remove_unnecessary_nested_divs, copy_image_to_local,
                 clean_images, remove_comments, remove_empty_attributes, clean_whitespace,
                 simplify_document_structure, add_h1_heading, clean_roles,
                 remove_footer_section, remove_breadcrumb_section, organize_duplicate_named_files)

class TestConfluenceHtmlCleaner(unittest.TestCase):
    """
    Test suite for HTML cleaning functions in the Confluence HTML Export Processor.
    
    This test class covers all aspects of HTML cleaning, including:
    - Removing Confluence-specific elements and attributes
    - Cleaning up HTML structure
    - Processing images and tables
    - Handling breadcrumbs and navigation elements
    """
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        
        This method creates a sample HTML document with various Confluence-specific
        elements that will be used by individual test methods.
        """
        self.sample_html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="test" content="test">
                <script>alert('test');</script>
                <style>.test{color:red;}</style>
                <link rel="stylesheet" href="test.css">
            </head>
            <body>
                <div id="breadcrumb-section">
                    <span><a href="#">Space</a></span>
                    <span><a href="#">Parent</a></span>
                </div>
                <div class="confluence-class test-macro container">
                    <span class="bold custom-class">Test</span>
                    <p>Created by <a href="https://example.com/people/user123">John Doe</a> on 2023-12-28</p>
                    <table width="100%">
                        <colgroup><col style="width: 50%;"><col style="width: 50%;"></colgroup>
                        <tr class="odd"><td>Test</td><td width="100">Another Test</td></tr>
                    </table>
                    <img src="attachments/image.png" data-test="test" class="confluence-image" loading="lazy"/>
                </div>
                <div><span>Text</span></div>
                <div>      </div>
                <section class="footer-body">Footer content</section>
            </body>
        </html>
        """
        self.soup = BeautifulSoup(self.sample_html, 'html.parser')

    def test_remove_meta_elements(self):
        soup = remove_meta_elements(self.soup)
        self.assertEqual(len(soup.find_all('meta')), 0)

    def test_convert_user_links_to_strong(self):
        soup = convert_user_links_to_strong(self.soup)
        user_link = soup.find('a', href=lambda x: x and 'people' in x and 'confluence' in x)
        self.assertIsNone(user_link)
        self.assertEqual(soup.find('strong').text, 'John Doe')

    def test_remove_all_scripts(self):
        soup = remove_all_scripts(self.soup)
        self.assertEqual(len(soup.find_all('script')), 0)

    def test_remove_all_styles(self):
        soup = remove_all_styles(self.soup)
        self.assertEqual(len(soup.find_all('style')), 0)

    def test_remove_all_links(self):
        soup = remove_all_links(self.soup)
        self.assertEqual(len(soup.find_all('link')), 0)

    def test_replace_created_by_text(self):
        soup = replace_created_by_text(self.soup)
        metadata_text = soup.find('p').get_text()
        self.assertEqual(metadata_text, 'Criado por John Doe em 2023-12-28')

    def test_clean_attributes_and_classes(self):
        soup = clean_attributes_and_classes(self.soup)
        div = soup.find('div', class_='container')
        span = soup.find('span', class_='bold')
        self.assertEqual(div['class'], ['container'])
        self.assertEqual(span['class'], ['bold'])
        self.assertNotIn('data-test', soup.find('img').attrs)

    def test_remove_empty_divs_and_spans(self):
        soup = remove_empty_divs_and_spans(self.soup)
        self.assertEqual(len(soup.find_all('div')), 4) 

    def test_remove_onclick_and_javascript_attributes(self):
        # Add a test tag with onclick and href="javascript:..."
        test_tag = self.soup.new_tag('a', href='javascript:void(0);', onclick="alert('test')")
        self.soup.body.append(test_tag)
        soup = remove_onclick_and_javascript_attributes(self.soup)
        self.assertNotIn('onclick', test_tag.attrs)
        self.assertNotIn('href', test_tag.attrs)

    def test_clean_tables(self):
        soup = clean_tables(self.soup)
        table = soup.find('table')
        self.assertNotIn('width', table.attrs)
        self.assertIn('border', table.attrs)
        self.assertEqual(table['border'], '1')
        self.assertNotIn('colgroup', str(soup))

    def test_remove_unnecessary_nested_divs(self):
        # Create a nested div structure
        nested_div = self.soup.new_tag('div')
        nested_div.append(self.soup.new_tag('div'))
        self.soup.body.append(nested_div)
        soup = remove_unnecessary_nested_divs(self.soup)
        # After cleaning, there should be no more nested divs
        self.assertEqual(len(soup.find_all('div', recursive=True)), 5)

    @patch('requests.get')
    def test_copy_image_to_local(self, mock_get):
        # Mock the response for requests.get
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'test image data']
        mock_get.return_value = mock_response

        # Test with a URL
        img_src = 'https://example.com/image.jpg'
        target_dir = Path('test_output')
        new_src = copy_image_to_local(img_src, target_dir)
        self.assertEqual(new_src, 'img/image.jpg')
        self.assertTrue((target_dir / 'img' / 'image.jpg').exists())

        # Clean up
        shutil.rmtree(target_dir)

    @patch('main.copy_image_to_local')
    def test_clean_images(self, mock_copy_image):
        mock_copy_image.return_value = 'img/image.png'
        soup = clean_images(self.soup, Path('test_output'))
        img = soup.find('img')
        self.assertEqual(img['src'], 'img/image.png')
        self.assertNotIn('class', img.attrs)
        self.assertNotIn('loading', img.attrs)
        self.assertIn('style', img.attrs)

    def test_remove_comments(self):
        comment = Comment('This is a comment')
        self.soup.body.append(comment)
        soup = remove_comments(self.soup)
        self.assertNotIn(comment, soup.body)

    def test_remove_empty_attributes(self):
        tag = self.soup.find('img')
        tag['data-empty'] = ''
        soup = remove_empty_attributes(self.soup)
        self.assertNotIn('data-empty', tag.attrs)

    def test_clean_whitespace(self):
        tag = self.soup.find('span')
        tag['class'] = ' bold '
        soup = clean_whitespace(self.soup)
        self.assertEqual(tag['class'], 'bold')

    def test_simplify_document_structure(self):
        soup = simplify_document_structure(self.soup)
        # The div with just text content should be removed
        self.assertEqual(len(soup.find_all('div')), 4)

    def test_add_h1_heading(self):
        soup = add_h1_heading(self.soup, 'Test Page')
        self.assertEqual(soup.find('h1').text, 'Test Page')

    def test_clean_roles(self):
        tag = self.soup.find('div')
        tag['role'] = 'test-role'
        soup = clean_roles(self.soup)
        self.assertNotIn('role', tag.attrs)

    def test_remove_footer_section(self):
        soup = remove_footer_section(self.soup)
        self.assertIsNone(soup.find('section', class_='footer-body'))

    def test_clean_confluence_html(self):
        cleaned_html = clean_confluence_html(self.sample_html)
        soup = BeautifulSoup(cleaned_html, 'html.parser')
        self.assertNotIn('confluence-class', cleaned_html)
        self.assertNotIn('test-macro', cleaned_html)
        self.assertIn('container', cleaned_html)
        self.assertNotIn('data-test', cleaned_html)
        self.assertNotIn('Created by', cleaned_html)
        self.assertIn('Criado por', cleaned_html)
        self.assertIn('border="1"', cleaned_html)
        self.assertNotIn('colgroup', cleaned_html)

    def test_extract_breadcrumbs(self):
        breadcrumbs = extract_breadcrumbs(self.soup)
        self.assertEqual(len(breadcrumbs), 2)
        self.assertEqual(breadcrumbs[0], 'Space')
        self.assertEqual(breadcrumbs[1], 'Parent')

    @patch('pathlib.Path.mkdir')
    def test_create_directory_path(self, mock_mkdir):
        base_path = Path('/test/base')
        breadcrumbs = ['Space', 'Parent', 'Child']
        result = create_directory_path(base_path, breadcrumbs)
        self.assertEqual(str(result), str(Path('/test/base/Space/Parent/Child')))
        self.assertEqual(mock_mkdir.call_count, 3)

    def test_remove_breadcrumb_section(self):
        soup = remove_breadcrumb_section(self.soup)
        self.assertIsNone(soup.find('div', id='breadcrumb-section'))

    @patch('main.create_directory_path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_process_html_file(self, mock_exists, mock_file, mock_create_dir):
        mock_exists.return_value = True
        mock_create_dir.return_value = Path('/test/output/Space/Parent')
        mock_file.return_value.__enter__.return_value.read.return_value = self.sample_html
        file_path = Path('test.html')
        new_base_dir = Path('/test/output')
        space_name = 'Space'
        success, message = process_html_file(file_path, new_base_dir, create_docx=False, space_name=space_name)
        self.assertTrue(success)
        self.assertIn('Copied to', message)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @patch('shutil.rmtree')
    @patch('shutil.copytree')
    @patch('builtins.open')
    def test_setup_directory_structure(self, mock_file, mock_copytree, mock_rmtree, 
                                     mock_glob, mock_exists):
        mock_exists.return_value = True
        mock_file.return_value.__enter__.return_value.read.return_value = self.sample_html
        mock_glob.return_value = iter([Path('test.html')])
        io_dir = Path('io/SA')
        new_base_dir, space_name = setup_directory_structure(io_dir)
        self.assertIsInstance(new_base_dir, Path)
        self.assertIsInstance(space_name, str)
        mock_copytree.assert_called()

    def test_organize_duplicate_named_files(self):
        base_dir = Path('test_output')
        (base_dir / 'folder1').mkdir(parents=True, exist_ok=True)
        (base_dir / 'folder1' / 'file1.txt').touch()
        (base_dir / 'folder2').mkdir(parents=True, exist_ok=True)
        (base_dir / 'folder2' / 'folder2.txt').touch()
        organize_duplicate_named_files(base_dir)
        self.assertTrue((base_dir / 'folder1' / 'file1.txt').exists())
        self.assertTrue((base_dir / 'folder2' / 'folder2.txt').exists())

if __name__ == '__main__':
    unittest.main()
