#!/usr/bin/env python3
"""
setup.py for tool-conversor-confluence
"""

from setuptools import setup, find_packages
import os

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith('#')]

setup(
    name="tool-conversor-confluence",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for processing Confluence HTML exports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tool-conversor-confluence",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Office/Business",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "confluence-converter=main:main",
        ],
    },
    include_package_data=True,
) 