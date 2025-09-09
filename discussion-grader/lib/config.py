"""
Configuration Manager for the Grading System
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """
    Manages configuration settings for the discussion grading system.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, use default.
        """
        self.config_path = config_path or os.path.join('config', 'config.json')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dictionary containing configuration settings
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key
            default: Default value if not found
            
        Returns:
            The configuration value or default if not found
        """
        try:
            return self.config[section][key]
        except (KeyError, TypeError):
            return default
    
    def update_value(self, section: str, key: str, value: Any) -> None:
        """
        Update a configuration value and save to file.
        
        Args:
            section: Configuration section name
            key: Configuration key
            value: New value to set
        """
        if section not in self.config:
            self.config[section] = {}
            
        self.config[section][key] = value
        self._save_config()
    
    def _save_config(self) -> None:
        """Save the current configuration to file."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
