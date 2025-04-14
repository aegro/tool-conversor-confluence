#!/usr/bin/env python3
"""
Test Suite for HTMLCleaner

This module contains basic tests for the HTMLCleaner class.
"""

import unittest
from pathlib import Path
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.html_cleaner import HTMLCleaner


class TestHTMLCleaner(unittest.TestCase):
    """Test suite for HTMLCleaner class."""

    def setUp(self):
        """Set up test fixtures."""
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
                </div>
            </body>
        </html>
        """

    def test_html_cleaner_initialization(self):
        """Test that HTMLCleaner can be initialized."""
        cleaner = HTMLCleaner(self.sample_html, Path("test_output"))
        self.assertIsNotNone(cleaner)
        self.assertIsInstance(cleaner.soup, BeautifulSoup)


if __name__ == "__main__":
    unittest.main()
