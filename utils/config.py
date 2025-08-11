"""
Configuration management for VedOps platform
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
import logging

class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'execution_mode': 'local',
            'local_models': {
                'default': 'llama2',
                'available': ['llama2', 'codellama', 'mistral', 'neural-chat']
            },
            'cloud_providers': {
                'aws': {'enabled': False, 'region': 'us-east-1'},
                'azure': {'enabled': False, 'region': 'eastus'},
                'gcp': {'enabled': False, 'region': 'us-central1'}
            },
            'security': {
                'auto_patch': True,
                'strict_compliance': False,
                'audit_logging': True
            },
            'agents': {
                'varuna': {'enabled': True, 'timeout': 300},
                'agni': {'enabled': True, 'timeout': 600},
                'yama': {'enabled': True, 'timeout': 900},
                'vayu': {'enabled': True, 'timeout': 1200},
                'hanuman': {'enabled': True, 'timeout': 1800},
                'krishna': {'enabled': True, 'timeout': 300}
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config()
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

def load_config() -> Config:
    """Load global configuration"""
    return Config()
