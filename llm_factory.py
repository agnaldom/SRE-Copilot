#!/usr/bin/env python3
"""
SRE Copilot - LLM Factory
=========================

This module provides a factory for creating language model instances
supporting both OpenAI and Google Gemini Pro.
"""

import os
from typing import Optional, Union
from enum import Enum
from langchain.llms import OpenAI
from langchain_google_genai import GoogleGenerativeAI


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"


class LLMFactory:
    """Factory class for creating language model instances."""
    
    @staticmethod
    def create_llm(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> Union[OpenAI, GoogleGenerativeAI]:
        """
        Create a language model instance based on the specified provider.
        
        Args:
            provider: LLM provider ('openai' or 'gemini'). If None, uses DEFAULT_LLM_PROVIDER env var.
            model: Specific model name. If None, uses default for the provider.
            temperature: Temperature for generation (0.0 to 1.0).
            **kwargs: Additional arguments passed to the LLM constructor.
            
        Returns:
            Configured LLM instance.
            
        Raises:
            ValueError: If provider is not supported or required API keys are missing.
        """
        # Determine provider
        if provider is None:
            provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai").lower()
        
        provider = provider.lower()
        
        if provider == LLMProvider.OPENAI.value:
            return LLMFactory._create_openai_llm(model, temperature, **kwargs)
        elif provider == LLMProvider.GEMINI.value:
            return LLMFactory._create_gemini_llm(model, temperature, **kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {[p.value for p in LLMProvider]}")
    
    @staticmethod
    def _create_openai_llm(
        model: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> OpenAI:
        """Create OpenAI LLM instance."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI")
        
        # Default model for OpenAI
        if model is None:
            model = "gpt-3.5-turbo-instruct"  # Good balance of performance and cost for CrewAI
        
        return OpenAI(
            model_name=model,
            temperature=temperature,
            openai_api_key=api_key,
            **kwargs
        )
    
    @staticmethod
    def _create_gemini_llm(
        model: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> GoogleGenerativeAI:
        """Create Google Gemini Pro LLM instance."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini")
        
        # Default model for Gemini
        if model is None:
            model = "gemini-pro"  # Main Gemini Pro model
        
        return GoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
            **kwargs
        )
    
    @staticmethod
    def get_available_providers() -> list[str]:
        """
        Get list of available LLM providers based on configured API keys.
        
        Returns:
            List of available provider names.
        """
        available = []
        
        if os.getenv("OPENAI_API_KEY"):
            available.append(LLMProvider.OPENAI.value)
        
        if os.getenv("GOOGLE_API_KEY"):
            available.append(LLMProvider.GEMINI.value)
        
        return available
    
    @staticmethod
    def get_default_provider() -> str:
        """
        Get the default LLM provider.
        
        Returns:
            Default provider name, falling back to first available if not configured.
        """
        default = os.getenv("DEFAULT_LLM_PROVIDER", "").lower()
        available = LLMFactory.get_available_providers()
        
        if default in available:
            return default
        elif available:
            return available[0]  # Return first available
        else:
            raise ValueError("No LLM providers are configured. Please set OPENAI_API_KEY or GOOGLE_API_KEY.")


class LLMConfig:
    """Configuration class for LLM settings."""
    
    # Model configurations for different providers
    MODELS = {
        LLMProvider.OPENAI.value: {
            "default": "gpt-3.5-turbo-instruct",
            "fast": "gpt-3.5-turbo-instruct",
            "powerful": "gpt-4",
            "cost_effective": "gpt-3.5-turbo-instruct"
        },
        LLMProvider.GEMINI.value: {
            "default": "gemini-pro",
            "fast": "gemini-pro",
            "powerful": "gemini-pro",
            "cost_effective": "gemini-pro"
        }
    }
    
    # Temperature settings for different use cases
    TEMPERATURES = {
        "deterministic": 0.0,       # For consistent, factual responses
        "balanced": 0.1,            # Good balance for most tasks
        "creative": 0.3,            # For more creative responses
        "exploratory": 0.7          # For brainstorming and exploration
    }
    
    @classmethod
    def get_model(cls, provider: str, model_type: str = "default") -> str:
        """Get specific model for provider and type."""
        return cls.MODELS.get(provider, {}).get(model_type, cls.MODELS[provider]["default"])
    
    @classmethod
    def get_temperature(cls, temp_type: str = "balanced") -> float:
        """Get temperature value for specific use case."""
        return cls.TEMPERATURES.get(temp_type, cls.TEMPERATURES["balanced"])


def create_llm_for_agent_role(role: str, provider: Optional[str] = None) -> Union[OpenAI, GoogleGenerativeAI]:
    """
    Create LLM optimized for specific agent role.
    
    Args:
        role: Agent role (e.g., 'triage', 'investigation', 'analysis', 'notification')
        provider: LLM provider preference
        
    Returns:
        Configured LLM instance optimized for the role.
    """
    # Role-specific configurations
    role_configs = {
        "triage": {
            "model_type": "fast",
            "temp_type": "deterministic"
        },
        "investigation": {
            "model_type": "default", 
            "temp_type": "balanced"
        },
        "analysis": {
            "model_type": "powerful",
            "temp_type": "balanced"
        },
        "notification": {
            "model_type": "default",
            "temp_type": "deterministic"
        }
    }
    
    config = role_configs.get(role, {"model_type": "default", "temp_type": "balanced"})
    
    # Get provider
    if provider is None:
        provider = LLMFactory.get_default_provider()
    
    # Get model and temperature for this role
    model = LLMConfig.get_model(provider, config["model_type"])
    temperature = LLMConfig.get_temperature(config["temp_type"])
    
    return LLMFactory.create_llm(provider=provider, model=model, temperature=temperature)


if __name__ == "__main__":
    """Test the LLM factory functionality."""
    print("🧠 Testing LLM Factory...")
    
    # Show available providers
    available = LLMFactory.get_available_providers()
    print(f"Available providers: {available}")
    
    if available:
        default_provider = LLMFactory.get_default_provider()
        print(f"Default provider: {default_provider}")
        
        try:
            # Test creating LLM
            llm = LLMFactory.create_llm()
            print(f"✅ Successfully created {type(llm).__name__} instance")
            
            # Test role-specific LLM
            analysis_llm = create_llm_for_agent_role("analysis")
            print(f"✅ Created analysis LLM: {type(analysis_llm).__name__}")
            
        except Exception as e:
            print(f"❌ Error creating LLM: {e}")
    else:
        print("❌ No LLM providers configured. Please set API keys in environment.")
