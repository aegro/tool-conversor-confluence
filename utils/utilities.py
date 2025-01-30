# utilities.py

import logging
import sys
import re
import yaml
import requests
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache

# Type aliases
PathLike = Union[str, Path]
ConfigDict = Dict[str, Any]

@dataclass
class HttpConfig:
    """HTTP configuration settings."""
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = 'HTML Processor/1.0'
    verify_ssl: bool = True
    allow_redirects: bool = True

class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass

class ConfigurationManager:
    """
    Manages application configuration with support for default values,
    environment variables, and user overrides.
    """
    
    _instance = None
    _config: Optional[ConfigDict] = None
    
    DEFAULT_CONFIG = {
        'input_directory': 'input',
        'output_directory': 'output',
        'create_docx': False,
        'log_level': 'INFO',
        'log_format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        'log_date_format': '%Y-%m-%d %H:%M:%S',
        'http': {
            'timeout': 30,
            'max_retries': 3,
            'user_agent': 'HTML Processor/1.0',
            'verify_ssl': True,
            'allow_redirects': True
        },
        'standard_html_classes': {
            'table': ['sortable', 'data-table'],
            'td': ['selected', 'header'],
            'tr': ['odd', 'even'],
            'div': ['container', 'row', 'column'],
            'span': ['bold', 'italic', 'underline'],
            'ul': ['list', 'navigation'],
            'li': ['active', 'current'],
            'img': ['thumbnail', 'responsive'],
            'a': ['active', 'visited', 'external']
        }
    }
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize ConfigurationManager."""
        self.logger = logging.getLogger(__name__)

    def load_config(self, config_file: Optional[PathLike] = None) -> ConfigDict:
        """
        Load configuration from default values and optional config file.
        
        Args:
            config_file: Optional path to YAML configuration file
            
        Returns:
            Dict containing merged configuration
            
        Raises:
            ConfigurationError: If config file is invalid or cannot be read
        """
        if self._config is not None:
            return self._config
            
        config = self.DEFAULT_CONFIG.copy()
        
        # Try to load default config first
        default_config_path = Path(__file__).parent.parent / 'config' / 'default_config.yaml'
        if default_config_path.exists():
            try:
                default_user_config = self._load_yaml_config(default_config_path)
                config = deep_merge_dicts(config, default_user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load default config file: {e}")
        
        # Load user-specified config if provided
        if config_file:
            try:
                user_config = self._load_yaml_config(config_file)
                config = deep_merge_dicts(config, user_config)
            except Exception as e:
                raise ConfigurationError(f"Failed to load config file: {e}")
                
        self._config = config
        return config
        
    @staticmethod
    def _load_yaml_config(config_file: PathLike) -> ConfigDict:
        """Load configuration from YAML file."""
        config_path = Path(config_file)
        if not config_path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")
            
        try:
            with config_path.open('r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading config file: {e}")
            
    def get_config(self) -> ConfigDict:
        """Get current configuration, loading defaults if not initialized."""
        if self._config is None:
            self.load_config()
        return self._config

    def get_http_config(self) -> HttpConfig:
        """Get HTTP-specific configuration as dataclass."""
        config = self.get_config()
        return HttpConfig(**config.get('http', {}))

class LoggingManager:
    """
    Centralizes logging configuration and provides logging utilities.
    """
    
    @staticmethod
    def setup_logging(
        config: ConfigDict,
        log_file: Optional[PathLike] = None,
        module_name: Optional[str] = None
    ) -> None:
        """
        Configure logging based on configuration settings.
        
        Args:
            config: Configuration dictionary
            log_file: Optional path to log file
            module_name: Optional module name for logger
        """
        log_level = config.get('log_level', 'INFO')
        log_format = config.get('log_format',
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        date_format = config.get('log_date_format', '%Y-%m-%d %H:%M:%S')
        
        # Convert string log level to constant
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ConfigurationError(f"Invalid log level: {log_level}")
            
        # Create formatter
        formatter = logging.Formatter(log_format, date_format)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Always add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                raise ConfigurationError(f"Failed to setup log file: {e}")

class RequestsManager:
    """
    Manages HTTP requests with configurable settings and retries.
    """
    
    def __init__(self, config: Optional[HttpConfig] = None):
        """Initialize with optional config override."""
        self.config = config or ConfigurationManager().get_http_config()
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create and configure requests session."""
        session = requests.Session()
        
        # Configure retries
        adapter = requests.adapters.HTTPAdapter(max_retries=self.config.max_retries)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': self.config.user_agent
        })
        
        return session
        
    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Perform GET request with configured settings.
        
        Args:
            url: Target URL
            **kwargs: Additional arguments passed to requests.get()
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails
        """
        # Merge default settings with provided kwargs
        settings = {
            'timeout': self.config.timeout,
            'verify': self.config.verify_ssl,
            'allow_redirects': self.config.allow_redirects
        }
        settings.update(kwargs)
        
        return self.session.get(url, **settings)

class FileProcessor:
    """
    Utility functions for file and path processing.
    """
    
    INVALID_CHARS = r'[<>:"/\\|?*]'
    WHITESPACE = r'\s+'
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Convert string to safe filename.
        
        Args:
            filename: Input string
            
        Returns:
            Sanitized filename string
            
        Raises:
            ValueError: If filename is empty after sanitization
        """
        if not filename or not isinstance(filename, str):
            raise ValueError("Filename must be a non-empty string")
            
        # Remove invalid characters
        safe_name = re.sub(FileProcessor.INVALID_CHARS, '', filename)
        # Replace whitespace with hyphens
        safe_name = re.sub(FileProcessor.WHITESPACE, '-', safe_name)
        # Remove leading/trailing hyphens
        safe_name = safe_name.strip('-')
        
        if not safe_name:
            raise ValueError("Sanitized filename is empty")
            
        return safe_name
        
    @staticmethod
    def create_directory_path(base_path: Path, segments: list[str]) -> Path:
        """
        Create nested directory structure.
        
        Args:
            base_path: Base directory path
            segments: List of directory names
            
        Returns:
            Path to created directory
            
        Raises:
            OSError: If directory creation fails
        """
        current_path = Path(base_path)
        
        try:
            for segment in segments:
                current_path = current_path / FileProcessor.sanitize_filename(segment)
                current_path.mkdir(parents=True, exist_ok=True)
            return current_path
            
        except Exception as e:
            raise OSError(f"Failed to create directory structure: {e}")

def deep_merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Recursively merge two dictionaries.
    
    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if (
            key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)
        ):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
            
    return result

@lru_cache(maxsize=128)
def get_mime_type(file_path: str) -> str:
    """
    Get MIME type for file extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        MIME type string
    """
    extension = Path(file_path).suffix.lower()
    mime_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.xml': 'application/xml',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    return mime_types.get(extension, 'application/octet-stream')

# Convenience functions
def load_config(config_file: Optional[PathLike] = None) -> ConfigDict:
    """Load configuration (convenience function)."""
    config_manager = ConfigurationManager()
    return config_manager.load_config(config_file)

def setup_logging(config: ConfigDict, log_file: Optional[PathLike] = None) -> None:
    """Setup logging (convenience function)."""
    LoggingManager.setup_logging(config, log_file)

def get_config() -> ConfigDict:
    """Get current configuration (convenience function)."""
    return ConfigurationManager().get_config()