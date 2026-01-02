"""
Unit tests for config_loader.py
"""
import os
import unittest
from unittest.mock import patch


class TestGetApiKeys(unittest.TestCase):
    """Tests for get_api_keys function."""

    def setUp(self):
        # Clear cache before each test
        from config_loader import get_api_keys
        get_api_keys.cache_clear()

    @patch.dict(os.environ, {
        'GIBD_DEEPSEEK_API_KEY': 'test-deepseek-key',
        'GIBD_OPENAI_API_KEY': 'test-openai-key',
        'GIBD_DEEPSEEK_API_URL': 'https://test.deepseek.com'
    }, clear=True)
    def test_loads_api_keys_from_env(self):
        from config_loader import get_api_keys
        keys = get_api_keys()

        self.assertEqual(keys['deepseek'], 'test-deepseek-key')
        self.assertEqual(keys['openai'], 'test-openai-key')
        self.assertEqual(keys['deepseek_url'], 'https://test.deepseek.com')

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_none_for_missing_keys(self):
        from config_loader import get_api_keys
        keys = get_api_keys()

        self.assertIsNone(keys['deepseek'])
        self.assertIsNone(keys['openai'])

    @patch.dict(os.environ, {}, clear=True)
    def test_uses_default_deepseek_url(self):
        from config_loader import get_api_keys
        keys = get_api_keys()

        self.assertEqual(keys['deepseek_url'], 'https://api.deepseek.com')

    @patch.dict(os.environ, {'GIBD_DEEPSEEK_API_KEY': 'cached-key'}, clear=True)
    def test_caches_result(self):
        from config_loader import get_api_keys
        keys1 = get_api_keys()
        keys2 = get_api_keys()

        # Should return same object (cached)
        self.assertIs(keys1, keys2)


class TestGetEmailConfig(unittest.TestCase):
    """Tests for get_email_config function."""

    def setUp(self):
        from config_loader import get_email_config
        get_email_config.cache_clear()

    @patch.dict(os.environ, {
        'GIBD_EMAIL_SENDER': 'sender@example.com',
        'GIBD_EMAIL_PASSWORD': 'secret123',
        'GIBD_EMAIL_RECIPIENTS': 'user1@example.com,user2@example.com',
        'GIBD_EMAIL_ADMIN': 'admin@example.com'
    }, clear=True)
    def test_loads_email_config_from_env(self):
        from config_loader import get_email_config
        config = get_email_config()

        self.assertEqual(config['sender_email'], 'sender@example.com')
        self.assertEqual(config['sender_password'], 'secret123')
        self.assertEqual(config['recipient_emails'], ['user1@example.com', 'user2@example.com'])
        self.assertEqual(config['admin_email'], 'admin@example.com')

    @patch.dict(os.environ, {
        'SENDER_EMAIL_DEV': 'legacy@example.com',
        'EMAIL_PASSWORD_DEV': 'legacy123'
    }, clear=True)
    def test_supports_legacy_env_vars(self):
        from config_loader import get_email_config
        config = get_email_config()

        self.assertEqual(config['sender_email'], 'legacy@example.com')
        self.assertEqual(config['sender_password'], 'legacy123')

    @patch.dict(os.environ, {
        'GIBD_EMAIL_SENDER': 'new@example.com',
        'SENDER_EMAIL_DEV': 'legacy@example.com'
    }, clear=True)
    def test_prefers_new_vars_over_legacy(self):
        from config_loader import get_email_config
        config = get_email_config()

        self.assertEqual(config['sender_email'], 'new@example.com')

    @patch.dict(os.environ, {
        'GIBD_EMAIL_RECIPIENTS': 'user1@example.com'
    }, clear=True)
    def test_uses_first_recipient_as_admin_fallback(self):
        from config_loader import get_email_config
        config = get_email_config()

        self.assertEqual(config['admin_email'], 'user1@example.com')

    @patch.dict(os.environ, {
        'GIBD_EMAIL_RECIPIENTS': '  user1@example.com , user2@example.com  '
    }, clear=True)
    def test_strips_whitespace_from_recipients(self):
        from config_loader import get_email_config
        config = get_email_config()

        self.assertEqual(config['recipient_emails'], ['user1@example.com', 'user2@example.com'])


class TestValidateRequiredVars(unittest.TestCase):
    """Tests for validate_required_vars function."""

    @patch.dict(os.environ, {'VAR1': 'value1', 'VAR2': 'value2'}, clear=True)
    def test_passes_when_all_vars_present(self):
        from config_loader import validate_required_vars
        # Should not raise
        validate_required_vars(['VAR1', 'VAR2'], 'test')

    @patch.dict(os.environ, {'VAR1': 'value1'}, clear=True)
    def test_raises_when_vars_missing(self):
        from config_loader import validate_required_vars, ConfigurationError

        with self.assertRaises(ConfigurationError) as context:
            validate_required_vars(['VAR1', 'MISSING_VAR'], 'test')

        self.assertIn('MISSING_VAR', str(context.exception))
        self.assertIn('test', str(context.exception))


class TestValidateEmailConfig(unittest.TestCase):
    """Tests for validate_email_config function."""

    def setUp(self):
        from config_loader import get_email_config
        get_email_config.cache_clear()

    @patch.dict(os.environ, {
        'GIBD_EMAIL_SENDER': 'sender@example.com',
        'GIBD_EMAIL_PASSWORD': 'secret123'
    }, clear=True)
    def test_passes_with_valid_config(self):
        from config_loader import validate_email_config
        # Should not raise
        validate_email_config()

    @patch.dict(os.environ, {'GIBD_EMAIL_SENDER': 'sender@example.com'}, clear=True)
    def test_raises_when_password_missing(self):
        from config_loader import validate_email_config, ConfigurationError

        with self.assertRaises(ConfigurationError):
            validate_email_config()


class TestValidateLlmConfig(unittest.TestCase):
    """Tests for validate_llm_config function."""

    def setUp(self):
        from config_loader import get_api_keys
        get_api_keys.cache_clear()

    @patch.dict(os.environ, {
        'GIBD_LLM_PROVIDER': 'deepseek',
        'GIBD_DEEPSEEK_API_KEY': 'test-key'
    }, clear=True)
    def test_passes_with_deepseek_key(self):
        from config_loader import validate_llm_config
        # Should not raise
        validate_llm_config()

    @patch.dict(os.environ, {
        'GIBD_LLM_PROVIDER': 'openai',
        'GIBD_OPENAI_API_KEY': 'test-key'
    }, clear=True)
    def test_passes_with_openai_key(self):
        from config_loader import validate_llm_config
        # Should not raise
        validate_llm_config()

    @patch.dict(os.environ, {'GIBD_LLM_PROVIDER': 'deepseek'}, clear=True)
    def test_raises_when_deepseek_key_missing(self):
        from config_loader import validate_llm_config, ConfigurationError

        with self.assertRaises(ConfigurationError) as context:
            validate_llm_config()

        self.assertIn('DeepSeek', str(context.exception))


class TestClearCache(unittest.TestCase):
    """Tests for clear_cache function."""

    def test_clears_api_keys_cache(self):
        from config_loader import get_api_keys, clear_cache

        # Set first key
        with patch.dict(os.environ, {'GIBD_DEEPSEEK_API_KEY': 'key1'}, clear=False):
            clear_cache()  # Clear any previous cache
            keys1 = get_api_keys()
            self.assertEqual(keys1['deepseek'], 'key1')

        # Clear cache and change env
        clear_cache()

        with patch.dict(os.environ, {'GIBD_DEEPSEEK_API_KEY': 'key2'}, clear=False):
            keys2 = get_api_keys()
            self.assertEqual(keys2['deepseek'], 'key2')


if __name__ == '__main__':
    unittest.main()
