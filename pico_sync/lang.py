"""Language support: UA/EN dictionaries, _() helper, settings persistence."""

import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "pico_sync")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")

UA = {
    # port
    "port_not_found": "❌ Не знайдено Pico у системі.",
    "opening_port": "🔌  Відкриваю порт: {port} @ {baud} baud",
    "waiting_data": "📡  Чекаю дані... (Ctrl+C для виходу)\n",
    "device_disconnected": "⚠️  Пристрій відключено, перепідключаюсь...",
    "pico_not_ready": "⏳  Pico не готовий — повтор через 1 сек...",
    "switching_port": "🔄  Перемикаюсь на новий порт: {port}",
    "available_ports": "\nДоступні серійні порти:\n",
    "no_serial_ports": "⚠️ Серійних портів не знайдено.",
    "select_port_prompt": "Оберіть номер порту (або Enter для скасування): ",
    "enter_number": "❌ Введіть номер.",
    "invalid_number": "❌ Невірний номер. Спробуйте ще раз.",

    # delta
    "ignore_patterns": "Ігнорую патерни: {patterns}",
    "delete_filter": "Фільтр видалення: {filter}",
    "skip_ignored": "[SKIP] {path}",
    "skip_same": "[SKIP same] {path}",
    "upload_new": "[UPLOAD new] {local} → {remote}",
    "upload_diff": "[UPLOAD diff] {local} → {remote}",
    "delete_file": "[DELETE] {path}",
    "sync_complete": "=== Синхронізацію завершено ===",
    "upload_from_edit": "[UPLOAD from edit] {path}",

    # config (init)
    "picoignore_created": ".picoignore створено",
    "picoignore_exists": ".picoignore вже існує",
    "meta_created": "meta/ створено",
    "config_created": "{file} створено",
    "config_exists": "{file} вже існує",
    "update_available": "⚠ Доступне оновлення:",
    "latest_version": "Остання версія : {version}",
    "current_version": "Поточна версія: {version}\n",
    "changelog": "Зміни: {text}",
    "download_url": "\n🔗 Завантажити: {url}\n",
    "already_latest": "✔ У вас вже остання версія ({version})",

    # config (general)
    "config_port_set": "Порт встановлено: {port} (збережено)",
    "config_src_change": "Поточна src: {root}\nНовий шлях src (Enter — залишити): ",
    "config_src_ok": "Src змінено на: {root}",
    "config_src_not_found": "Директорію не знайдено: {path}",
    "config_port_auto": "Порт з конфігу: {port}",
    "press_enter": "\nНатисніть Enter для продовження...",

    # pick (browser)
    "pico_empty": "⚠ Pico порожній або недоступний.",
    "pico_list_error": "⚠ Помилка читання файлів з Pico. Пристрій може бути недоступний.",
    "file_actions": " Esc=back  /=search   Дії з файлом",
    "back_to_files": "Повернутись до списку файлів",
    "cat_file": "Переглянути вміст файлу",
    "edit_file": "Редагувати файл",
    "edit_no_editor": "Редактор не знайдено. Файл збережено: {path}",
    "rm_file": "Видалити файл з Pico",
    "confirm_delete": "Видалити {name}? (y/N): ",
    "deleted_ok": "[DELETED] {name}",
    "find_header": " Esc=back  /=search   Всі файли на Pico",
    "refresh_files": "Оновити список файлів з Pico",

    # pick (device menu)
    "device_not_found": "❌ Не знайдено Pico. Спочатку обери порт у [config].",
    "device_header": " Esc=back  /=search",
    "device_sync": "Синхронізувати файли з Pico (із вибором фільтра)",
    "device_monitor": "Відкрити серійний монітор Pico",
    "device_reboot": "Перезавантажити Pico",
    "current_filter": " Поточний фільтр: {filter}",
    "filter_all": "Видалити всі файли на Pico і залити src/",
    "filter_py": "Тільки .py файли",
    "filter_py_plus": ".py, .txt, .json файли",
    "filter_nopy": "Все крім .py",
    "filter_custom": "Вказати власні розширення (через кому)",
    "filter_desc_all": "Всі файли (видаляє все на Pico перед заливкою)",
    "filter_desc_py": "Тільки .py файли",
    "filter_desc_py_plus": ".py, .txt, .json файли",
    "filter_desc_nopy": "Все крім .py",
    "filter_desc_custom": "Розширення: {ext}",
    "ext_prompt": "Extensions (comma-sep, e.g. .py,.txt): ",
    "rebooting": "Перезавантажую Pico...",

    # pick (config menu)
    "config_port": "Обрати COM-порт Pico (автовизначення)",
    "config_src": "Змінити вихідну теку для синхронізації",
    "config_check_update": "Перевірити наявність оновлень Pico Sync",
    "config_init": "Створити .picoignore, meta/, .picosyncconfig",
    "config_lang": "Змінити мову інтерфейсу",
    "back_to_main": "Повернутись до головного меню",
    "lang_select": " Оберіть мову / Select language",
    "lang_ua": "Українська",
    "lang_en": "English",
    "lang_set": "Мова змінена на: {lang}",

    # pick (project selector)
    "project_prompt": "Шлях до кореня проекту (Enter — поточна тека): ",
    "project_read_error": "Помилка читання вводу. Спробуйте ще раз.",
    "project_added": "Проект додано: {name}",
    "project_not_found": "Директорія не знайдена: {path}",
    "project_no_projects": "Немає проектів для видалення.",
    "project_removed": "Проект видалено: {name}",
    "project_not_found_remove": "Проект не знайдено: {name}",
    "project_selector_header": " Esc=back  /=search   Оберіть проект",
    "project_updated": "Проект оновлено: {name}",
    "project_empty": "Немає збережених проектів.",
    "project_list_header": "Збережені проекти:\n",

    # pick (info panel)
    "info_project": "Проект: {name}",
    "info_root": "Корінь: {path}",
    "info_source": "Джерело: {path}",
    "info_device": "Пристрій: {port}  {status}",
    "info_detected": "Виявлено:",
    "info_configured": " (налаштовано)",
    "info_filter": "Фільтр: {filter}",
    "info_connected": "підключено",
    "info_not_found": "не знайдено",
    "port_not_set": "не вказано",
    "info_read_only": "Інформація про проект (лише перегляд)",
    "info_back_hint": "Натисніть Enter щоб повернутись",

    # cli (main)
    "cancelled": "Скасовано.",
    "port_selected": "Вибрано порт: {port}\n",
    "rebooting_cli": "Перезавантажую Pico...",
    "exit_msg": "\n👋 Вихід.",
    "port_set_saved": "Порт встановлено: {port} (збережено)",
    "port_auto_config": "Порт з конфігу: {port}",
    "port_auto_detect": "Автоматично визначено порт: {port}",

    # preview hints
    "preview_add_project": "Додати новий проект до списку",
    "preview_remove_project": "Видалити проект зі списку",
    "preview_lang": "Мова інтерфейсу: {lang}\n\nДоступно: ua (Українська), en (English)",
    "preview_quit": "Вийти з pico_sync",
    "preview_back_projects": "Повернутись до списку проектів",
    "preview_browse_files": "Переглянути файли на Pico, читати/редагувати/видаляти",
    "preview_device_menu": "Синхронізувати файли, серійний монітор, перезавантажити Pico",
    "preview_config_menu": "Налаштування: порт, src-тека, перевірка оновлень, ініціалізація проекту",
}

EN = {
    # port
    "port_not_found": "❌ Pico not found.",
    "opening_port": "🔌  Opening port: {port} @ {baud} baud",
    "waiting_data": "📡  Waiting for data... (Ctrl+C to exit)\n",
    "device_disconnected": "⚠️  Device disconnected, reconnecting...",
    "pico_not_ready": "⏳  Pico not ready — retrying in 1 sec...",
    "switching_port": "🔄  Switching to new port: {port}",
    "available_ports": "\nAvailable serial ports:\n",
    "no_serial_ports": "⚠️ No serial ports found.",
    "select_port_prompt": "Select port number (or Enter to cancel): ",
    "enter_number": "❌ Enter a number.",
    "invalid_number": "❌ Invalid number. Try again.",

    # delta
    "ignore_patterns": "Ignore patterns: {patterns}",
    "delete_filter": "Delete filter: {filter}",
    "skip_ignored": "[SKIP] {path}",
    "skip_same": "[SKIP same] {path}",
    "upload_new": "[UPLOAD new] {local} → {remote}",
    "upload_diff": "[UPLOAD diff] {local} → {remote}",
    "delete_file": "[DELETE] {path}",
    "sync_complete": "=== Sync complete ===",
    "upload_from_edit": "[UPLOAD from edit] {path}",

    # config (init)
    "picoignore_created": ".picoignore created",
    "picoignore_exists": ".picoignore already exists",
    "meta_created": "meta/ created",
    "config_created": "{file} created",
    "config_exists": "{file} already exists",
    "update_available": "⚠ Update available:",
    "latest_version": "Latest version : {version}",
    "current_version": "Current version: {version}\n",
    "changelog": "Changes: {text}",
    "download_url": "\n🔗 Download: {url}\n",
    "already_latest": "✔ You already have the latest version ({version})",

    # config (general)
    "config_port_set": "Port set: {port} (saved)",
    "config_src_change": "Current src: {root}\nNew src path (Enter to keep): ",
    "config_src_ok": "Src changed to: {root}",
    "config_src_not_found": "Directory not found: {path}",
    "config_port_auto": "Port from config: {port}",
    "press_enter": "\nPress Enter to continue...",

    # pick (browser)
    "pico_empty": "⚠ Pico empty or not accessible.",
    "pico_list_error": "⚠ Error reading files from Pico. Device may not be accessible.",
    "file_actions": " Esc=back  /=search   File actions",
    "back_to_files": "Back to file list",
    "cat_file": "View file content",
    "edit_file": "Edit file",
    "edit_no_editor": "No editor found. File saved at: {path}",
    "rm_file": "Delete file from Pico",
    "confirm_delete": "Delete {name}? (y/N): ",
    "deleted_ok": "[DELETED] {name}",
    "find_header": " Esc=back  /=search   All files on Pico",
    "refresh_files": "Refresh file list from Pico",

    # pick (device menu)
    "device_not_found": "❌ No Pico found. Select port in [config] first.",
    "device_header": " Esc=back  /=search",
    "device_sync": "Sync files to Pico (with filter selection)",
    "device_monitor": "Open Pico serial monitor",
    "device_reboot": "Reboot Pico",
    "current_filter": " Current filter: {filter}",
    "filter_all": "Delete all files from Pico and upload src/",
    "filter_py": "Only .py files",
    "filter_py_plus": ".py, .txt, .json files",
    "filter_nopy": "Everything except .py",
    "filter_custom": "Specify custom extensions (comma-sep)",
    "filter_desc_all": "All files (deletes everything on Pico before upload)",
    "filter_desc_py": "Only .py files",
    "filter_desc_py_plus": ".py, .txt, .json files",
    "filter_desc_nopy": "Everything except .py",
    "filter_desc_custom": "Extensions: {ext}",
    "ext_prompt": "Extensions (comma-sep, e.g. .py,.txt): ",
    "rebooting": "Rebooting Pico...",

    # pick (config menu)
    "config_port": "Select Pico COM port (auto-detect)",
    "config_src": "Change source directory for sync",
    "config_check_update": "Check for Pico Sync updates",
    "config_init": "Create .picoignore, meta/, .picosyncconfig",
    "config_lang": "Change interface language",
    "back_to_main": "Back to main menu",
    "lang_select": " Select language / Оберіть мову",
    "lang_ua": "Українська",
    "lang_en": "English",
    "lang_set": "Language set to: {lang}",

    # pick (project selector)
    "project_prompt": "Path to project root (Enter — current directory): ",
    "project_read_error": "Input error. Please try again.",
    "project_added": "Project added: {name}",
    "project_not_found": "Directory not found: {path}",
    "project_no_projects": "No projects to remove.",
    "project_removed": "Project removed: {name}",
    "project_not_found_remove": "Project not found: {name}",
    "project_selector_header": " Esc=back  /=search   Select project",
    "project_updated": "Project updated: {name}",
    "project_empty": "No saved projects.",
    "project_list_header": "Saved projects:\n",

    # pick (info panel)
    "info_project": "Project: {name}",
    "info_root": "Root: {path}",
    "info_source": "Source: {path}",
    "info_device": "Device: {port}  {status}",
    "info_detected": "Detected:",
    "info_configured": " (configured)",
    "info_filter": "Filter: {filter}",
    "info_connected": "connected",
    "info_not_found": "not found",
    "port_not_set": "not set",
    "info_read_only": "Project Info (read-only)",
    "info_back_hint": "Press Enter to go back",

    # cli (main)
    "cancelled": "Cancelled.",
    "port_selected": "Selected port: {port}\n",
    "rebooting_cli": "Rebooting Pico...",
    "exit_msg": "\n👋 Exit.",
    "port_set_saved": "Port set: {port} (saved)",
    "port_auto_config": "Port from config: {port}",
    "port_auto_detect": "Auto-detected port: {port}",

    # preview hints
    "preview_add_project": "Add a new project to the list",
    "preview_remove_project": "Remove a project from the list",
    "preview_lang": "Interface language: {lang}\n\nOptions: ua (Українська), en (English)",
    "preview_quit": "Exit pico_sync",
    "preview_back_projects": "Back to project list",
    "preview_browse_files": "Browse Pico files, view/edit/delete",
    "preview_device_menu": "Sync files, serial monitor, reboot Pico",
    "preview_config_menu": "Settings: port, src directory, check updates, init project",
}

_LANG = "ua"


def _load_settings():
    """Load settings from ~/.config/pico_sync/settings.json."""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_settings(data):
    """Save settings to ~/.config/pico_sync/settings.json."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    existing = _load_settings()
    existing.update(data)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(existing, f, indent=2)
        f.write("\n")


def _detect_language():
    """Detect language from settings or $LANG. Fallback to 'ua'."""
    settings = _load_settings()
    if "language" in settings:
        return settings["language"]
    locale = os.environ.get("LANG", "en_US")
    return "ua" if locale.startswith("uk") else "en"


def set_language(lang):
    """Set language at runtime and persist to settings."""
    global _LANG
    _LANG = lang if lang in ("ua", "en") else "ua"
    _save_settings({"language": _LANG})


_LANG = _detect_language()


def _(key, **kwargs):
    """Translate key using current language. Format with kwargs if provided."""
    d = UA if _LANG == "ua" else EN
    val = d.get(key)
    if val is None:
        return key
    if kwargs:
        return val.format(**kwargs)
    return val


def get_language():
    """Return current language code ('ua' or 'en')."""
    return _LANG
