# Проблеми коду

## ✅ Нові можливості

### `--pick` — інтерактивний режим
- `pico_sync.py --pick` — запускає fzf-меню (або numbered fallback)
- Доступні дії: sync, ls, cat, nano, monitor, reboot, port, check_update
- Для sync: вибір filter (all/py/py+/nopy/custom)
- Автопошук порту, якщо не вибрано явно

### `--filter` для direct mode
- `pico_sync.py --sync --filter py` — sync, видаляти тільки .py
- `pico_sync.py --sync --filter nopy` — не чіпати .py
- `pico_sync.py --sync --filter .wav,.mpy` — тільки вказані розширення

## ✅ Структурні зміни

### Перехід на пакетну структуру
- `pico_sync.py` — обгортка (`from pico_sync.cli import main`)
- `pico_sync/cli.py` — основний код
- `pico_sync/__init__.py` — версія та експорт
- `pico_sync/__main__.py` — `python3 -m pico_sync`
- `pyproject.toml` — для PyPI (entry point: `picosync`)
- `MANIFEST.in` — для pip build
- `.gitignore` — `__pycache__`, `dist/`, `*.egg-info`, `.idea/`
- `requirements.txt` — для ручного `pip install -r`
- `meta/latest_version.json` — створено для `--check_update`

### Як використовувати
- `python3 pico_sync.py --sync` — GitHub style
- `picosync --sync` — PyPI style (після `pip install`)
- `python3 -m pico_sync --sync` — ще один спосіб

## ✅ Виправлено

### 🐛 Критичні баги (injection у f-рядках) — ВИПРАВЛЕНО

Всі f-рядки з підстановкою `'{path}'` переведено на `repr(path)`.
Виправлені місця: `:232`, `:249`, `:262`, `:350`, `:362`, `:377`, `:391-393`.

## 🐢 Продуктивність

### SHA — індивідуальні виклики
`sync_tree` викликає `pico_file_sha256()` для кожного файлу в циклі.
Підсумок: N+1 mpremote-запусків (1 на список файлів + N на SHA).
На клонах плат через повільний serial це дає відчутне гальмо.

### mkdir + write — два виклики замість одного
`mp_write_file()` спочатку виконує mpremote для створення директорій,
потім ще один для запису файлу. Можна об'єднати.

## ⚠️ Інші проблеми

### `or True` на :347 — ВИПРАВЛЕНО
Замінено на `_match_filter(filter, remote_file)`. Підтримує:
- `all` — видаляти все (було `or True`)
- `py` — тільки `.py`
- `py+` — `.py`, `.txt`, `.json`
- `nopy` — все крім `.py`
- `.py,.txt` — довільні розширення через кому

Додано `--filter` для CLI та вибір фільтра через `--pick`.

### Дублювання логіки монітора — ВИПРАВЛЕНО
`serial_monitor.py` видалено. Логіку перенесено в `pico_sync.py`.
При `--monitor` тепер працює автопошук порту замість сліпого `/dev/ttyACM0`.

### С代с використовується до означення
`check_for_updates()` (рядок 27) звертається до `C.YELLOW`, `C.RESET` тощо,
а `class C` означено лише на рядку 60. При виконанні не падає (виклик відкладений),
але код важче читати.

### Немає retry-логіки для mpremote
При втраті зв'язку з Pico під час sync — необроблений `subprocess.CalledProcessError`.
Для клонів, де serial менш стабільний, це часта проблема.
