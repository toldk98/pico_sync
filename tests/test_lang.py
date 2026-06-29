import os
import tempfile

import pytest

from pico_sync.lang import _, set_language, get_language, CONFIG_DIR, SETTINGS_FILE, _load_settings, _save_settings


@pytest.fixture(autouse=True)
def isolate_settings():
    old_cfg = CONFIG_DIR, SETTINGS_FILE
    with tempfile.TemporaryDirectory() as td:
        import pico_sync.lang as lang_mod
        lang_mod.CONFIG_DIR = td
        lang_mod.SETTINGS_FILE = os.path.join(td, "settings.json")
        lang_mod._LANG = "ua"
        yield
    lang_mod.CONFIG_DIR, lang_mod.SETTINGS_FILE = old_cfg


class TestTranslate:
    def test_ua_default(self):
        assert get_language() == "ua"

    def test_en_switch(self):
        set_language("en")
        assert get_language() == "en"

    def test_unknown_fallback_to_ua(self):
        set_language("fr")
        assert get_language() == "ua"

    def test_translate_ua(self):
        set_language("ua")
        assert _("port_not_found") == "❌ Не знайдено Pico у системі."

    def test_translate_en(self):
        set_language("en")
        assert _("port_not_found") == "❌ Pico not found."

    def test_missing_key_returns_key(self):
        assert _("nonexistent_key_xyz") == "nonexistent_key_xyz"

    def test_format_kwargs(self):
        set_language("ua")
        result = _("info_project", name="MyProj")
        assert "MyProj" in result

    def test_all_keys_present_in_both(self):
        from pico_sync.lang import UA, EN
        missing_in_en = set(UA.keys()) - set(EN.keys())
        missing_in_ua = set(EN.keys()) - set(UA.keys())
        assert not missing_in_en, f"Keys missing in EN: {missing_in_en}"
        assert not missing_in_ua, f"Keys missing in UA: {missing_in_ua}"

    def test_persistence(self):
        set_language("en")
        import pico_sync.lang as lang_mod
        lang_mod._LANG = lang_mod._detect_language()
        assert get_language() == "en"

    def test_load_settings_missing(self):
        assert _load_settings() == {}

    def test_save_and_load_settings(self):
        _save_settings({"language": "en"})
        loaded = _load_settings()
        assert loaded.get("language") == "en"

    def test_transform_with_no_kwargs(self):
        result = _("port_not_found")
        assert "Pico" in result or "Не знайдено" in result


class TestDetectLanguage:
    def test_detect_from_settings(self, monkeypatch):
        monkeypatch.delenv("LANG", raising=False)
        set_language("en")
        import pico_sync.lang as lang_mod
        lang_mod._LANG = lang_mod._detect_language()
        assert get_language() == "en"

    def test_detect_from_locale_uk(self, monkeypatch):
        monkeypatch.setenv("LANG", "uk_UA.UTF-8")
        import pico_sync.lang as lang_mod
        lang_mod._LANG = lang_mod._detect_language()
        assert get_language() == "ua"

    def test_detect_from_locale_en(self, monkeypatch):
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        import pico_sync.lang as lang_mod
        lang_mod._LANG = lang_mod._detect_language()
        assert get_language() == "en"
