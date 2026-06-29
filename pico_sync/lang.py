"""Language support: UA/EN dictionaries, _() helper, settings persistence."""

import os

from .settings import _load_settings, _save_settings

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
    "config_port_settings": "Налаштування підключення Pico",
    "config_src": "Змінити вихідну теку для синхронізації",
    "config_check_update": "Перевірити наявність оновлень Pico Sync",
    "config_init": "Створити .picoignore, meta/, .picosyncconfig",
    "config_lang": "Змінити мову інтерфейсу",
    "back_to_main": "Повернутись до головного меню",
    "back_to_config": "Повернутись до налаштувань",
    "back_to_settings": "Повернутись до налаштувань",
    "config_settings": "Глобальні налаштування",
    "port_settings_port": "Вибрати COM-порт вручну",
    "port_settings_piconame": "Авто-пошук за іменем (.piconame) — для кількох Pico",
    "piconame_current": "Поточне ім'я: {name}",
    "piconame_not_set": "Ім'я не налаштовано (використовується перший-ліпший Pico)",
    "piconame_detect": "Прочитати /.piconame з Pico і зберегти в конфіг",
    "piconame_set": "Записати нове ім'я на Pico і зберегти в конфіг",
    "piconame_clear": "Очистити ім'я з конфігу (повернутись до авто-детекту)",
    "piconame_detected": "Виявлено ім'я пристрою: {name}",
    "piconame_not_on_pico": "На Pico не знайдено /.piconame",
    "piconame_cleared": "Ім'я пристрою очищено",
    "piconame_prompt": "Нове ім'я для Pico: ",
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
    "info_piconame": "Ім'я пристрою: {name}",
    "info_piconame_not_found": "⚠ Pico з таким іменем не знайдено серед підключених пристроїв",

    # cli (main)
    "cli_desc": "Pico Sync Tool — синхронізація/перегляд/редагування для Raspberry Pi Pico",
    "cli_port_help": "COM-порт Pico (авто-детект якщо не вказано)",
    "cli_src_help": "Директорія для синхронізації",
    "cli_sync_help": "Синхронізувати src → Pico",
    "cli_ls_help": "Список файлів у директорії на Pico",
    "cli_cat_help": "Вивести вміст файлу з Pico",
    "cli_edit_help": "Редагувати файл на Pico",
    "cli_search_port_help": "Інтерактивний пошук serial-портів Pico",
    "cli_check_update_help": "Перевірити наявність оновлень Pico Sync",
    "cli_reboot_help": "Перезавантажити Pico (програмний reset)",
    "cli_monitor_help": "Серійний монітор Pico",
    "cli_pick_help": "Інтерактивний режим",
    "cli_filter_help": "Фільтр видалення: all, py, py+, nopy, або .ext,.ext2",
    "cli_init_help": "Створити .picoignore та meta/ в поточній директорії",
    "cli_set_name_help": "Записати NAME в /.piconame на Pico та зберегти в конфіг",
    "cli_lang_help": "Мова інтерфейсу (ua/en)",
    "cli_version_help": "Показати версію та вийти",
    "cli_project_help": "Керування проектами",
    "cli_project_add_help": "Додати теку проекту",
    "cli_project_add_path_help": "Шлях до кореня проекту",
    "cli_project_list_help": "Список збережених проектів",
    "cli_project_remove_help": "Видалити проект зі списку",
    "cli_project_remove_name_help": "Ім'я або шлях проекту",
    "cli_project_preview_help": "Показати інформацію про проект",
    "cli_project_preview_line_help": "Рядок зі списку проектів",
    "cli_project_preview_main_help": "Показати preview для головного меню (для fzf)",
    "cli_project_preview_main_item_help": "Вибраний пункт меню",
    "cli_project_preview_main_root_help": "Корінь проекту",
    "cancelled": "Скасовано.",
    "port_selected": "Вибрано порт: {port}\n",
    "rebooting_cli": "Перезавантажую Pico...",
    "exit_msg": "\n👋 Вихід.",
    "port_set_saved": "Порт встановлено: {port} (збережено)",
    "port_auto_config": "Порт з конфігу: {port}",
    "port_auto_detect": "Автоматично визначено порт: {port}",

    # preview hints
    "fzf_not_found": "⚠️ fzf не знайдено. Для зручної навігації встановіть:\n   {cmd}\n   або завантажте: {url}\n",
    "preview_add_project": "Додати новий проект до списку",
    "preview_remove_project": "Видалити проект зі списку",
    "preview_lang": "Мова інтерфейсу: {lang}\n\nДоступно: ua (Українська), en (English)",
    "preview_quit": "Вийти з pico_sync",
    "preview_back_projects": "Повернутись до списку проектів",
    "preview_browse_files": "Переглянути файли на Pico, читати/редагувати/видаляти",
    "preview_device_menu": "Синхронізувати файли, серійний монітор, перезавантажити Pico",
    "preview_config_menu": "Налаштування: порт, src-тека, ім'я пристрою, перевірка оновлень, ініціалізація проекту",
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
    "config_port_settings": "Pico connection settings",
    "config_src": "Change source directory for sync",
    "config_check_update": "Check for Pico Sync updates",
    "config_init": "Create .picoignore, meta/, .picosyncconfig",
    "config_lang": "Change interface language",
    "back_to_main": "Back to main menu",
    "back_to_config": "Back to settings",
    "back_to_settings": "Back to settings",
    "config_settings": "Global settings",
    "port_settings_port": "Select COM port manually",
    "port_settings_piconame": "Auto-find by device name (.piconame) — for multiple Picos",
    "piconame_current": "Current name: {name}",
    "piconame_not_set": "Name not set (first Pico found will be used)",
    "piconame_detect": "Read /.piconame from Pico and save to config",
    "piconame_set": "Write new name to Pico and save to config",
    "piconame_clear": "Clear name from config (revert to auto-detect)",
    "piconame_detected": "Detected device name: {name}",
    "piconame_not_on_pico": "No /.piconame found on Pico",
    "piconame_cleared": "Device name cleared",
    "piconame_prompt": "New name for Pico: ",
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
    "info_piconame": "Device name: {name}",
    "info_piconame_not_found": "⚠ No Pico with this name found among connected devices",

    # cli (main)
    "cli_desc": "Pico Sync Tool — sync/ls/cat/edit for Raspberry Pi Pico",
    "cli_port_help": "Pico COM port (auto-detect if omitted)",
    "cli_src_help": "Source directory to sync",
    "cli_sync_help": "Synchronize src → Pico",
    "cli_ls_help": "List directory on Pico",
    "cli_cat_help": "Output file content from Pico",
    "cli_edit_help": "Edit file on Pico",
    "cli_search_port_help": "Interactively search serial ports and choose Pico port",
    "cli_check_update_help": "Check for newer version of Pico Sync Tool",
    "cli_reboot_help": "Reboot Pico (software reset)",
    "cli_monitor_help": "Live serial log monitor for Pico",
    "cli_pick_help": "Interactive pick mode",
    "cli_filter_help": "Delete filter: all, py, py+, nopy, or .ext,.ext2",
    "cli_init_help": "Create default .picoignore and meta/ in current directory",
    "cli_set_name_help": "Write NAME to /.piconame on Pico and save to project config",
    "cli_lang_help": "Interface language (ua/en)",
    "cli_version_help": "Show version and exit",
    "cli_project_help": "Manage projects",
    "cli_project_add_help": "Add project directory",
    "cli_project_add_path_help": "Path to project root",
    "cli_project_list_help": "List saved projects",
    "cli_project_remove_help": "Remove project from list",
    "cli_project_remove_name_help": "Project name or path",
    "cli_project_preview_help": "Show project info",
    "cli_project_preview_line_help": "Line from project list",
    "cli_project_preview_main_help": "Show preview for main menu (for fzf)",
    "cli_project_preview_main_item_help": "Selected menu item",
    "cli_project_preview_main_root_help": "Project root",
    "cancelled": "Cancelled.",
    "port_selected": "Selected port: {port}\n",
    "rebooting_cli": "Rebooting Pico...",
    "exit_msg": "\n👋 Exit.",
    "port_set_saved": "Port set: {port} (saved)",
    "port_auto_config": "Port from config: {port}",
    "port_auto_detect": "Auto-detected port: {port}",

    # preview hints
    "fzf_not_found": "⚠️ fzf not found. For better navigation install:\n   {cmd}\n   or download: {url}\n",
    "preview_add_project": "Add a new project to the list",
    "preview_remove_project": "Remove a project from the list",
    "preview_lang": "Interface language: {lang}\n\nOptions: ua (Українська), en (English)",
    "preview_quit": "Exit pico_sync",
    "preview_back_projects": "Back to project list",
    "preview_browse_files": "Browse Pico files, view/edit/delete",
    "preview_device_menu": "Sync files, serial monitor, reboot Pico",
    "preview_config_menu": "Settings: port, src directory, device name, check updates, init project",
}

_LANG = "ua"


def _detect_language() -> str:
    """Detect language from settings or $LANG. Fallback to 'ua'."""
    settings = _load_settings()
    if "language" in settings:
        return settings["language"]
    locale = os.environ.get("LANG", "en_US")
    return "ua" if locale.startswith("uk") else "en"


def set_language(lang: str) -> None:
    """Set language at runtime and persist to settings."""
    global _LANG
    _LANG = lang if lang in ("ua", "en") else "ua"
    _save_settings({"language": _LANG})


_LANG = _detect_language()


def _(key: str, **kwargs: str) -> str:
    """Translate key using current language. Format with kwargs if provided."""
    d = UA if _LANG == "ua" else EN
    val = d.get(key)
    if val is None:
        return key
    if kwargs:
        return val.format(**kwargs)
    return val


def get_language() -> str:
    """Return current language code ('ua' or 'en')."""
    return _LANG
