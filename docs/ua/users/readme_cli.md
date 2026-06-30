# Pico Sync Tool — CLI режим

**Pico Sync** — компактний CLI-інструмент для зручної роботи з Raspberry Pi Pico / Pico W під MicroPython.
Надає команди для синхронізації файлів, перегляду файлової системи, базових операцій з файлами на пристрої,
моніторингу логів та перезавантаження плати.

Працює поверх `mpremote`. Підтримує інтерактивний режим з меню, fzf, вибір мови (UA/EN) — див. `readme_pick.md`.

Мета інструмента — зробити розробку на MicroPython максимально схожою на роботу з локальним проєктом.

**Можливості:**

- 🔄 **Синхронізація** — завантаження файлів на Pico (src/ або корінь)
- 🧠 **SHA-синхронізація** — оновлюються лише змінені файли (SHA-256)
- 🗑 **Автовидалення зайвих файлів** — файли на Pico, яких немає локально, видаляються
- 🧼 **Очищення порожніх директорій** — після синхронізації
- ⛔ **`.picoignore`** — ігнорування файлів (як `.gitignore`)
- 📂 **CLI перегляд файлів** — `--ls`, `--cat`, `--edit` для файлів на Pico
- 🔍 **Авто-детект порту** — пошук Pico серед serial-портів та за іменем
- 🔌 **Серійний монітор** — живий перегляд логів з Pico
- 🔁 **Перезавантаження** — програмний reset плати
- 🌐 **Мова інтерфейсу** — Українська / English
- 📦 **Менеджмент проектів** — CLI-команди `project list/add/remove`

Інструмент займає <1 МБ, розбитий на модулі для зручності супроводу та тестування.

🌐 [English version](README_EN.md)

---

## Зміст

- [Встановлення](#встановлення)
- [Використання](#використання)
- [Конфігурація](#конфігурація)
- [Поширені питання (FAQ)](#поширені-питання-faq)
- [Ліцензія](#ліцензія)

---

## Встановлення

### Linux

**Рекомендовано (pipx):**
```bash
pipx install pico_sync
```
Ізоляція в окремому середовищі, не засмічує систему.

**Альтернатива (pip):**
```bash
pip install pico_sync
```
Можна з `--user`:
```bash
pip install --user pico_sync
```

### Windows

**Через pip:**
```powershell
pip install pico_sync
```
Потрібен Python 3.7+ встановлений і доданий у PATH.

**Через pipx:**
```powershell
pipx install pico_sync
```

### macOS

**Через pip:**
```bash
pip3 install pico_sync
```

**Через pipx:**
```bash
pipx install pico_sync
```

### З GitHub (будь-яка ОС)

```bash
git clone https://github.com/toldk98/pico_sync.git
cd pico_sync
pip install .
```

### Portable-версія (без встановлення)

```bash
git clone https://github.com/toldk98/pico_sync.git
cd pico_sync
pip install pyserial mpremote
python pico_sync_portable.py
```

### Залежності

- Python 3.7+
- `pyserial` — робота з serial-портами
- `mpremote` — виконання команд на Pico

---

## Використання

### Загальний синтаксис

```bash
picosync [options] [project <command>]
python -m pico_sync [options] [project <command>]
```

Без аргументів запускається інтерактивний режим. Для CLI-команд передаються флаги дії. Обидва варіанти (`picosync` та `python -m pico_sync`) еквівалентні.

### Довідка

```bash
picosync --help
```

```
usage: picosync [-h] [--port PORT] [--baud BAUD] [--sync] [--ls PATH]
                [--cat FILE] [--edit FILE] [--search_port] [--check_update]
                [--reboot] [--monitor] [--pick] [--filter FILTER] [--init]
                [--set-name NAME] [--lang {ua,en}] [--version]
                {project} ...

Pico Sync Tool — sync/ls/cat/edit for Raspberry Pi Pico

positional arguments:
  {project}
    project        Manage projects

options:
  -h, --help       show this help message and exit
  --port PORT      Pico COM port (auto-detect if omitted)
  --baud BAUD      Port baud rate (default 115200)
  --sync           Synchronize project → Pico
  --ls PATH        List directory on Pico
  --cat FILE       Output file content from Pico
  --edit FILE      Edit file on Pico
  --search_port    Interactively search serial ports and choose Pico port
  --check_update   Check for newer version of Pico Sync Tool
  --reboot         Reboot Pico (software reset)
  --monitor        Live serial log monitor for Pico
  --pick           Interactive pick mode
  --filter FILTER  Delete filter: all, py, py+, nopy, or .ext,.ext2
  --init           Create default .picoignore and .picosyncconfig
  --set-name NAME  Write NAME to /.piconame on Pico and save to config
  --lang {ua,en}   Interface language (ua/en)
  --version        Show version and exit
```

### Версія

```bash
picosync --version
```

Показує поточну версію інструмента.

### Перевірка оновлень

```bash
picosync --check_update
```

Завантажує `meta/latest_version.json` з GitHub (`toldk98/pico_sync`), порівнює версію з поточною. Якщо доступна новіша — показує версію, changelog, посилання на PyPI та GitHub, а також команду `pip install --upgrade pico_sync`.

### Мова

```bash
picosync --lang ua
picosync --lang en
```

Встановлює мову для поточного запуску. Також можна задати через `LANG=ua` / `LANG=en`.

### Синхронізація

```bash
picosync --sync                          # всі файли
picosync --sync --filter py              # тільки .py
picosync --sync --filter .wav,.mpy       # вказані розширення
picosync --port /dev/ttyACM0 --sync      # вказати порт
```

Алгоритм:
1. Завантажує `.picoignore` з кореня проекту
2. Робить знімок всіх файлів на Pico
3. Проходить локальною директорією (src/ або корінь), збирає файли для синхронізації (пропускає ігноровані та `.piconame`)
4. Виконує SHA-256 всіх файлів на Pico одним запитом
5. Порівнює хеші: збіг → пропускає, відсутній → завантажує, різний → оновлює
6. Видаляє з Pico файли без локальної відповідності (з урахуванням фільтра)
7. Очищує порожні директорії

### Перегляд файлів

```bash
picosync --ls /                 # список кореневої директорії
picosync --ls /spm              # список директорії
picosync --cat /main.py         # вивести вміст файлу
```

### Редагування файлів

```bash
picosync --edit /config/settings.py
```

Файл завантажується з Pico в тимчасовий файл, відкривається в системному редакторі:
- **macOS:** `open -t` (TextEdit)
- **Linux:** `nano` → `vim` → `vi` (перший знайдений)
- **Windows:** `notepad`

Після збереження файл автоматично завантажується назад на Pico.

### Пошук порту

```bash
picosync --search_port
```

Показує нумерований список всіх serial-портів (Pico позначені ⭐). Виберіть номер для використання.

### Серійний монітор

```bash
picosync --monitor
```

Відкриває прямий перегляд логів з Pico (115200 бод). Автоматично перепідключається при:
- перезавантаженні Pico
- зміні USB-порту
- тимчасовому відключенні

Вихід: `Ctrl+C`.

### Перезавантаження

```bash
picosync --reboot
```

Програмний reset Pico через `mpremote reset`.

### Ім'я пристрою

```bash
picosync --set-name my-pico
```

Записує `/.piconame` на Pico та зберігає в конфіг проекту.

### Ініціалізація проекту

```bash
picosync --init
```

Створює в поточній директорії:
- `.picoignore` — стандартні патерни
- `.picosyncconfig` — конфігурація проекту

### Порт

```bash
picosync --port /dev/ttyACM0 --sync
picosync --port COM3 --monitor
```

Задає COM-порт явно. Працює з усіма флагами дії. Якщо не задано — авто-детект.

### Швидкість (baud)

```bash
picosync --baud 9600 --monitor
picosync --baud 115200 --monitor
```

Задає швидкість serial-порту для монітора. За замовчуванням — 115200. Якщо MicroPython на Pico налаштовано на іншу швидкість, монітор не працюватиме без правильно вказаного `--baud`.

### Фільтр

```bash
picosync --sync --filter py
picosync --sync --filter .wav,.mpy
```

Значення: `all`, `py`, `py+`, `nopy`, `.ext,.ext2`. Впливає тільки на видалення зайвих файлів.

### Керування проектами

```bash
picosync project list                        # список всіх проектів
picosync project add /home/user/my-project   # додати проект
picosync project remove my-project           # видалити проект
```

Проекти зберігаються в `~/.config/pico_sync/projects.json`.

---

## Структура проєкту

```
project_root/
│
├── .picoignore           # правила ігнорування
├── .picosyncconfig       # конфігурація проекту (порт, фільтр, baud)
│
└── ...                   # файли проекту (синхронізуються з Pico)
```

⚠️ **Важливо:**
1. `.picoignore` працює для всіх файлів у корені проекту
2. Якщо присутня теку `src/` — синхронізується вона (зворотна сумісність), інакше — корінь проекту

## Конфігурація

### Глобальні налаштування

Файл: `~/.config/pico_sync/settings.json`

```json
{
  "language": "ua"
}
```

- **language** — мова інтерфейсу: `"ua"` або `"en"`. Визначається автоматично: спочатку з файлу, потім з `$LANG` (якщо `uk*` → `"ua"`, інакше → `"en"`). Змінюється через `--lang ua/en` або `LANG=ua`/`LANG=en`, а також в інтерактивному режимі.

### Система проектів

Файл: `~/.config/pico_sync/projects.json`

```json
{
  "projects": [
    {
      "name": "my-project",
      "root": "/home/user/projects/my-project",
      "last_used": "2026-06-29T12:00:00"
    }
  ]
}
```

Кожен проект містить:
- `name` — назва (basename кореневої директорії)
- `root` — абсолютний шлях до кореня
- `last_used` — дата останнього використання

### Проєктний файл `.picosyncconfig`

Файл: `<project_root>/.picosyncconfig`

```json
{
  "port": "",
  "filter": "all",
  "piconame": ""
}
```

| Поле | Тип | Опис |
|------|-----|------|
| `port` | `str` | Порт Pico (напр. `/dev/ttyACM0`). Порожньо = авто-детект |
| `filter` | `str` | Фільтр синхронізації: all, py, py+, nopy, .ext,.ext2 |
| `piconame` | `str` | Ім'я пристрою для пошуку за іменем. Порожньо = не використовується |

Створюється через `picosync --init`.

### `.picoignore`

Працює за принципом `.gitignore`. Приклади:

```gitignore
# ігнорувати secret.py
secret.py

# ігнорувати всю теку
data/

# ігнорувати за розширенням
*.mpy
```

Підтримує:
- `*` — будь-яка кількість символів
- `?` — один символ
- `[abc]` — символ з набору
- `**` — будь-яка вкладеність
- `!` — інверсія (не ігнорувати)
- Рядки без `/` застосовуються до всіх рівнів; з `/` — до конкретного шляху

Стандартний `.picoignore`:
```
__pycache__/
*.pyc
.git/
.DS_Store
Thumbs.db
dist/
*.egg-info/
build/
.idea/
*.swp
*.swo
```

### Порт

Інструмент шукає Pico в такому порядку:
1. За **.piconame** (якщо задано) — перебирає всі Pico-порти, читає `/.piconame` з кожного
2. За **port** з конфігу — використовує збережений порт
3. **Авто-детект** — знаходить перший пристрій з USB ID Raspberry Pi (0x2E8A)
4. Якщо нічого не знайдено — використайте `--search_port` для ручного вибору

Знайдений порт записується в `os.environ["MPREMOTE_PORT"]` — це змінна середовища, яку читає `mpremote`. Вона існує лише в межах поточного запуску pico_sync і автоматично використовується всіма наступними викликами `mpremote` без повторного пошуку. Після завершення програми змінна зникає.

### Piconame

Опціональне ім'я пристрою, що зберігається у файлі `/.piconame` на Pico. Дозволяє ідентифікувати конкретну плату, коли підключено кілька Pico.

Керування через `--set-name <name>` або в інтерактивному режимі.

`.piconame` автоматично виключається з синхронізації.

### Фільтри синхронізації

Впливають тільки на **видалення** зайвих файлів з Pico. Завантажуються всі файли незалежно від фільтра.

| Фільтр | Опис |
|--------|------|
| `all` | Всі файли (видаляє зайве на Pico) |
| `py` | Тільки `.py` |
| `py+` | `.py`, `.txt`, `.json` |
| `nopy` | Все крім `.py` |
| `.ext,.ext2` | Власні розширення через кому |

---

## Поширені питання (FAQ)

### Pico не знайдено / порт не визначено

Переконайтеся що Pico підключено USB-кабелем (не тільки живлення). Якщо авто-детект не спрацював — використайте `picosync --search_port` для ручного вибору.

### Два Pico підключено одночасно

Авто-детект візьме перший знайдений. Щоб працювати з конкретним пристроєм — налаштуйте `.piconame` через `picosync --set-name <name>`.

### Файли не синхронізуються

Перевірте `.picoignore` — можливо файл підпадає під правило ігнорування. Якщо в корені є `src/` — синхронізується вона, інакше корінь.

### Помилка "No module named 'pyserial' / 'mpremote'"

Встановіть залежності: `pip install pyserial mpremote` (актуально тільки для portable-версії).

### Як оновити Pico Sync?

Перевірка завантажує `meta/latest_version.json` з GitHub і порівнює версії — доступна через `picosync --check_update`.

- **Через pipx:** `pipx upgrade pico_sync`
- **Через pip:** `pip install --upgrade pico_sync`

### Як отримати повну довідку?

```bash
picosync --help
picosync project --help     # довідка по підкомандах project
```

---

## Ліцензія

AGPL-3.0
