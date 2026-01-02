"""
Centralized configuration loader with environment variable validation.
Provides secure loading of secrets and configuration with backward compatibility.
"""
import os
import sys
from typing import Dict, List, Optional, Any
from functools import lru_cache

# Try to load python-dotenv if available
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


def _get_env_with_fallback(primary: str, fallback: str = None, default: str = None) -> Optional[str]:
    """Get environment variable with optional fallback to legacy variable name."""
    value = os.getenv(primary)
    if value is None and fallback:
        value = os.getenv(fallback)
    return value if value is not None else default


@lru_cache(maxsize=1)
def get_api_keys() -> Dict[str, Optional[str]]:
    """
    Load API keys from environment variables.

    Returns:
        dict with 'openai', 'deepseek', 'deepseek_url' keys
    """
    return {
        'openai': os.getenv('GIBD_OPENAI_API_KEY'),
        'deepseek': os.getenv('GIBD_DEEPSEEK_API_KEY'),
        'deepseek_url': os.getenv('GIBD_DEEPSEEK_API_URL', 'https://api.deepseek.com'),
    }


@lru_cache(maxsize=1)
def get_email_config() -> Dict[str, Any]:
    """
    Load email configuration from environment variables.
    Supports legacy SENDER_EMAIL_DEV/EMAIL_PASSWORD_DEV for backward compatibility.

    Returns:
        dict with sender_email, sender_password, recipient_emails, admin_email keys
    """
    sender = _get_env_with_fallback('GIBD_EMAIL_SENDER', 'SENDER_EMAIL_DEV')
    password = _get_env_with_fallback('GIBD_EMAIL_PASSWORD', 'EMAIL_PASSWORD_DEV')
    recipients_str = os.getenv('GIBD_EMAIL_RECIPIENTS', '')
    admin_email = os.getenv('GIBD_EMAIL_ADMIN', '')

    # Parse comma-separated recipients
    recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]

    # Use first recipient as admin if admin not specified
    if not admin_email and recipients:
        admin_email = recipients[0]

    return {
        'sender_email': sender,
        'sender_password': password,
        'receiver_email': admin_email,  # For backward compatibility
        'recipient_emails': recipients,
        'admin_email': admin_email,
    }


def get_api_base_urls() -> Dict[str, str]:
    """
    Get base URLs for internal APIs.

    Returns:
        dict with 'news_service' and 'trades_service' keys
    """
    return {
        'news_service': os.getenv('GIBD_API_BASE_URL', 'http://localhost:8080/GIBD-NEWS-SERVICE'),
        'trades_service': os.getenv('GIBD_TRADES_API_BASE_URL', 'http://localhost:8080/GIBD-TRADES'),
    }


def get_ollama_config() -> Dict[str, str]:
    """
    Get Ollama LLM configuration.

    Returns:
        dict with 'url' and 'model' keys
    """
    return {
        'url': os.getenv('GIBD_OLLAMA_URL', 'http://localhost:11434'),
        'model': os.getenv('GIBD_OLLAMA_MODEL', 'llama3:8b'),
    }


def get_llm_provider() -> str:
    """Get configured LLM provider."""
    return os.getenv('GIBD_LLM_PROVIDER', 'deepseek').lower()


def validate_required_vars(required: List[str], context: str = "application") -> None:
    """
    Validate that required environment variables are set.

    Args:
        required: List of required environment variable names
        context: Description of the context for error messages

    Raises:
        ConfigurationError: If any required variables are missing
    """
    missing = []
    for var in required:
        if os.getenv(var) is None:
            missing.append(var)

    if missing:
        raise ConfigurationError(
            f"Missing required environment variables for {context}: {', '.join(missing)}\n"
            f"Please set these in your .env file or environment."
        )


def validate_email_config() -> None:
    """
    Validate email configuration is complete.

    Raises:
        ConfigurationError: If email configuration is incomplete
    """
    config = get_email_config()
    if not config['sender_email'] or not config['sender_password']:
        raise ConfigurationError(
            "Email configuration incomplete. Set GIBD_EMAIL_SENDER and GIBD_EMAIL_PASSWORD "
            "(or legacy SENDER_EMAIL_DEV and EMAIL_PASSWORD_DEV)."
        )


def validate_llm_config() -> None:
    """
    Validate LLM API configuration based on selected provider.

    Raises:
        ConfigurationError: If LLM configuration is incomplete for the selected provider
    """
    provider = get_llm_provider()
    keys = get_api_keys()

    if provider == 'deepseek' and not keys['deepseek']:
        raise ConfigurationError(
            "DeepSeek API key not configured. Set GIBD_DEEPSEEK_API_KEY."
        )
    elif provider == 'openai' and not keys['openai']:
        raise ConfigurationError(
            "OpenAI API key not configured. Set GIBD_OPENAI_API_KEY."
        )


def validate_startup(script_name: str = None) -> None:
    """
    Run all validations appropriate for the given script.
    Call this at the start of main scripts to fail fast on configuration issues.

    Args:
        script_name: Name of the script being run (without .py extension)
    """
    scripts_requiring_email = ['news_summarizer', 'fetch_dse_daily_stock_data']
    scripts_requiring_llm = ['news_summarizer', 'update_sentiment_scores']

    if script_name in scripts_requiring_email:
        validate_email_config()

    if script_name in scripts_requiring_llm:
        # Only validate DeepSeek for news_summarizer, Ollama for sentiment
        if script_name == 'news_summarizer':
            validate_llm_config()
        # update_sentiment_scores uses Ollama which doesn't require API key validation


def clear_cache() -> None:
    """Clear all cached configuration. Useful for testing."""
    get_api_keys.cache_clear()
    get_email_config.cache_clear()
