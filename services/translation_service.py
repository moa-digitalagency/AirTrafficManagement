import json
import os

class TranslationService:
    def __init__(self, locales_dir='locales'):
        self.locales_dir = locales_dir
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        """Loads all JSON files from the locales directory."""
        self.translations = {}
        if not os.path.exists(self.locales_dir):
            return

        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                locale = filename[:-5]  # remove .json
                try:
                    with open(os.path.join(self.locales_dir, filename), 'r', encoding='utf-8') as f:
                        self.translations[locale] = json.load(f)
                except Exception as e:
                    print(f"Error loading translations for {locale}: {e}")

    def reload(self):
        self.load_translations()

    def get_available_locales(self):
        return list(self.translations.keys())

    def get_translation(self, key, locale='fr'):
        """
        Retrieves a translation for a given dotted key and locale.
        Example: 'nav.dashboard'
        """
        if locale not in self.translations:
            # Fallback to 'fr' if locale not found, or 'en' if 'fr' missing
            locale = 'fr' if 'fr' in self.translations else 'en'

        parts = key.split('.')
        current = self.translations.get(locale, {})

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return key  # Return key if not found

        return current

# Global instance
translation_service = TranslationService()

def t(key, locale=None):
    """
    Helper function to be used in templates and code.
    The locale should be passed from the context (e.g., session).
    """
    if locale is None:
        from flask import session
        locale = session.get('lang', 'fr')

    return translation_service.get_translation(key, locale)
