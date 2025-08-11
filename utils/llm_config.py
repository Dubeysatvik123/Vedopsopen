import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LLMConfigManager:
    """Manages LLM configuration for VedOps agents"""
    
    def __init__(self, config_file: str = "config/llm_config.json"):
        self.config_file = config_file
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Ensure config directory exists"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save LLM configuration to file"""
        try:
            # Validate configuration
            if not self.validate_config(config):
                logger.error("Invalid configuration provided")
                return False
            
            # Add metadata
            config['saved_at'] = datetime.now().isoformat()
            config['version'] = "1.0"
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"LLM configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save LLM configuration: {e}")
            return False
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """Load LLM configuration from file"""
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"Configuration file {self.config_file} not found")
                return None
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Validate loaded configuration
            if not self.validate_config(config):
                logger.error("Loaded configuration is invalid")
                return None
            
            logger.info("LLM configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load LLM configuration: {e}")
            return None
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate LLM configuration"""
        required_fields = ['provider', 'model']
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Provider-specific validation
        provider = config['provider']

        api_key_required = {
            'OpenAI', 'Anthropic', 'Google', 'Groq', 'Mistral', 'Cohere',
            'Together AI', 'OpenRouter', 'Perplexity', 'Fireworks AI', 'xAI (Grok)',
            'DeepSeek'
        }

        if provider in api_key_required and not config.get('api_key'):
            logger.error(f"{provider} requires an API key")
            return False

        endpoint_required = {'Azure OpenAI', 'Custom API'}
        if provider in endpoint_required and not config.get('endpoint'):
            logger.error(f"{provider} requires an endpoint")
            return False
        
        return True
    
    def get_llm_client(self, config: Optional[Dict[str, Any]] = None):
        """Get configured LLM client"""
        if not config:
            config = self.load_config()
        
        if not config:
            raise ValueError("No LLM configuration available")
        
        provider = config['provider']
        
        try:
            if provider == "OpenAI":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    temperature=0.1
                )
            
            elif provider == "Anthropic":
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=config['model'],
                    api_key=config['api_key'],
                    temperature=0.1
                )
            
            elif provider == "Google":
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model=config['model'],
                    google_api_key=config['api_key'],
                    temperature=0.1
                )
            
            elif provider == "Ollama (Local)":
                from langchain_community.llms import Ollama
                return Ollama(
                    model=config['model'],
                    base_url=config.get('ollama_url', 'http://localhost:11434')
                )
            
            elif provider == "Azure OpenAI":
                from langchain_openai import AzureChatOpenAI
                return AzureChatOpenAI(
                    deployment_name=config['model'],
                    api_key=config['api_key'],
                    azure_endpoint=config['endpoint'],
                    api_version="2024-02-15-preview",
                    temperature=0.1
                )

            # OpenAI-compatible providers via base_url
            elif provider == "Groq":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    base_url=config.get('endpoint', 'https://api.groq.com/openai/v1'),
                    temperature=0.1
                )

            elif provider == "Mistral":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    base_url=config.get('endpoint', 'https://api.mistral.ai/v1'),
                    temperature=0.1
                )

            elif provider == "Together AI":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    base_url=config.get('endpoint', 'https://api.together.xyz/v1'),
                    temperature=0.1
                )

            elif provider == "OpenRouter":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    base_url=config.get('endpoint', 'https://openrouter.ai/api/v1'),
                    temperature=0.1
                )

            elif provider == "Perplexity":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    base_url=config.get('endpoint', 'https://api.perplexity.ai'),
                    temperature=0.1
                )

            elif provider == "Fireworks AI":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    base_url=config.get('endpoint', 'https://api.fireworks.ai/inference/v1'),
                    temperature=0.1
                )

            elif provider == "xAI (Grok)":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    base_url=config.get('endpoint', 'https://api.x.ai/v1'),
                    temperature=0.1
                )

            elif provider == "DeepSeek":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    base_url=config.get('endpoint', 'https://api.deepseek.com'),
                    temperature=0.1
                )
            
            else:  # Custom API (OpenAI-compatible)
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config['model'],
                    api_key=config['api_key'],
                    base_url=config['endpoint'],
                    temperature=0.1
                )
        
        except ImportError as e:
            logger.error(f"Required package not installed for {provider}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize {provider} client: {e}")
            raise
    
    def test_connection(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Test LLM connection"""
        try:
            client = self.get_llm_client(config)
            
            # Simple test query
            response = client.invoke("Hello, this is a connection test.")
            
            if response and hasattr(response, 'content'):
                logger.info("LLM connection test successful")
                return True
            else:
                logger.error("LLM connection test failed - no response")
                return False
                
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False
