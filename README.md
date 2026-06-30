# Pico Sync Tool

**Pico Sync** — компактний CLI-інструмент для зручної роботи з Raspberry Pi Pico / Pico W під MicroPython.
Надає команди для синхронізації файлів, перегляду файлової системи, базових операцій з файлами на пристрої,
моніторингу логів та перезавантаження плати.

Працює поверх `mpremote`. Підтримує інтерактивний режим з меню, fzf, вибір мови (UA/EN).

Мета інструмента — зробити розробку на MicroPython максимально схожою на роботу з локальним проєктом.

**Можливості:**

- 🔄 **Синхронізація** — завантаження файлів на Pico (src/ або корінь)
- 🧠 **SHA-синхронізація** — оновлюються лише змінені файли (SHA-256)
- 🗑 **Автовидалення зайвих файлів** — файли на Pico, яких немає локально, видаляються
- 🧼 **Очищення порожніх директорій** — після синхронізації
- ⛔ **`.picoignore`** — ігнорування файлів (як `.gitignore`)
- 📂 **Перегляд та редагування файлів** — інтерактивний браузер (pick) або `--ls`/`--cat`/`--edit` (CLI)
- 🔍 **Авто-детект порту** — пошук Pico серед serial-портів: спочатку за іменем пристрою (якщо задано `.piconame`), потім за збереженим портом, інакше — перший-ліпший Pico
- 🔌 **Серійний монітор** — живий перегляд логів з Pico
- 🔁 **Перезавантаження** — програмний reset плати
- 🌐 **Мова інтерфейсу** — Українська / English
- 📦 **Менеджмент проектів** — збереження проектів з налаштуваннями

🌐 [English version](https://github.com/toldk98/pico_sync/blob/main/README_EN.md)

📖 **Докладніше:** [інтерактивний режим (pick)](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_pick.md) · [CLI режим](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_cli.md)

[![PyPI version](https://img.shields.io/pypi/v/pico-sync)](https://pypi.org/project/pico-sync/)
[![CI](https://github.com/toldk98/pico_sync/actions/workflows/ci.yml/badge.svg)](https://github.com/toldk98/pico_sync/actions/workflows/ci.yml)

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

### Додаткові залежності (опціонально, для інтерактивного режиму)

- **[fzf](https://github.com/junegunn/fzf)** — зручний вибір у меню. Якщо не встановлено — використовується нумерований вибір.

## Використання

### Запуск

- **Pick:** `picosync` або `picosync --pick`. Відкриває меню з fzf (або нумерований вибір). [→ докладніше](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_pick.md)
- **CLI:** `picosync <options>`. Флаги дії без інтерактиву. [→ докладніше](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_cli.md)

### Стартовий екран / Довідка

- **Pick:** список збережених проектів + `[+] add project`, `[-] remove project`, `[s] settings`, `[q] quit`. Вибір проекту → головне меню.
- **CLI:** `picosync --help` — всі опції; `picosync project --help` — керування проектами.

### Синхронізація

- **Pick:** `[d] device → sync` → вибір фільтра з меню (all/py/py+/nopy/custom).
- **CLI:** `picosync --sync [--filter py|py+|nopy|.ext,.ext2]`.

Алгоритм (спільний для обох режимів):
1. Завантажує `.picoignore` з кореня проекту
2. Робить знімок всіх файлів на Pico
3. Проходить локальною директорією (src/ або корінь), збирає файли для синхронізації (пропускає ігноровані та `.piconame`)
4. Виконує SHA-256 всіх файлів на Pico одним запитом
5. Порівнює хеші: збіг → пропускає, відсутній → завантажує, різний → оновлює
6. Видаляє з Pico файли без локальної відповідності (з урахуванням фільтра)
7. Очищує порожні директорії

### Файли (перегляд, редагування, видалення)

- **Pick:** `[f] files` — браузер з навігацією теками, `[*] find` — пошук по всіх файлах; cat/edit/rm у контекстному меню файлу. Редактор: nano/vim (Linux), TextEdit (macOS), notepad (Windows). [→ докладніше](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_pick.md)
- **CLI:** `picosync --ls /` — список кореня; `picosync --ls /spm` — список директорії; `picosync --cat /main.py` — вміст; `picosync --edit /config.py` — редагування. [→ докладніше](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_cli.md)

### Серійний монітор

- **Pick:** `[d] device → monitor`
- **CLI:** `picosync --monitor`

Вихід: `Ctrl+C`. Авто-перепідключення при reboot/зміні порту.

### Перезавантаження

- **Pick:** `[d] device → reboot`
- **CLI:** `picosync --reboot`

Програмний reset через `mpremote reset`.

### Ім'я пристрою (piconame)

- **Pick:** `[c] config → port_settings → piconame` → detect (прочитати з Pico), set (записати нове), clear (видалити + очистити конфіг).
- **CLI:** `picosync --set-name <name>` — записує `/.piconame` на Pico та зберігає в конфіг.

### Налаштування проекту

- **Pick:** `[c] config` → port_settings/baud/piconame/init.
- **CLI:** `picosync --port /dev/ttyACM0 --sync`, `picosync --init`, `picosync --search_port`.

### Керування проектами

- **Pick:** стартовий екран — `[+] add project` (ввести шлях), `[-] remove project` (вибрати зі списку). [→ докладніше](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_pick.md)
- **CLI:** `picosync project list`, `picosync project add /path`, `picosync project remove <name>`. [→ докладніше](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_cli.md)

### Глобальні налаштування

- **Pick:** `[s] settings` → `[~] lang` (перемикання UA/EN), `[!] check update` (перевірка оновлень). [→ докладніше](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_pick.md)
- **CLI:** `picosync --lang ua/en`, `picosync --check_update`, `LANG=ua` / `LANG=en` — змінна середовища. [→ докладніше](https://github.com/toldk98/pico_sync/blob/main/docs/ua/users/readme_cli.md)

## Конфігурація

### Глобальні налаштування

Файл: `~/.config/pico_sync/settings.json`

```json
{
  "language": "ua"
}
```

- **language** — мова інтерфейсу: `"ua"` або `"en"`. Визначається автоматично: спочатку з файлу, потім з `$LANG` (якщо `uk*` → `"ua"`, інакше → `"en"`). Змінюється:
  - **Pick:** `[s] settings → [~] lang`
  - **CLI:** `--lang ua/en`
  - **Спільне:** `LANG=ua` / `LANG=en`

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
- `last_used` — дата останнього використання (ISO 8601)

Проекти сортуються за `last_used` спаданням.

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

Створюється:
- **Pick:** `[c] config → init`
- **CLI:** `picosync --init`

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
4. Якщо нічого не знайдено:
   - **Pick:** `[c] config → port_settings → port` для ручного вибору
   - **CLI:** `picosync --search_port` для ручного вибору

### Piconame

Опціональне ім'я пристрою, що зберігається у файлі `/.piconame` на Pico. Дозволяє ідентифікувати конкретну плату, коли підключено кілька Pico.

Керування:
- **Pick:** `[c] config → port_settings → piconame` з пунктами detect (прочитати з Pico), set (записати нове), clear (видалити з Pico та очистити конфіг)
- **CLI:** `picosync --set-name <name>` — записати ім'я на Pico та зберегти в конфіг

`.piconame` автоматично виключається з синхронізації (не видаляється, не завантажується).

### Фільтри синхронізації

Впливають тільки на **видалення** зайвих файлів з Pico. Завантажуються всі файли незалежно від фільтра.

| Фільтр | Опис |
|--------|------|
| `all` | Всі файли (видаляє зайве на Pico) |
| `py` | Тільки `.py` |
| `py+` | `.py`, `.txt`, `.json` |
| `nopy` | Все крім `.py` |
| `.ext,.ext2` | Власні розширення через кому |

## Поширені питання (FAQ)

### Pico не знайдено / порт не визначено

Переконайтеся що Pico підключено USB-кабелем (не тільки живлення). Якщо авто-детект не спрацював:

- **Pick:** `[c] config → port_settings → port` для ручного вибору з переліку serial-портів
- **CLI:** `picosync --search_port` для інтерактивного вибору з переліку serial-портів

### Два Pico підключено одночасно

Авто-детект візьме перший знайдений. Щоб працювати з конкретним пристроєм:

- **Pick:** `[c] config → port_settings → piconame → set`, задайте унікальне ім'я
- **CLI:** `picosync --set-name <name>`, задайте унікальне ім'я

### Як встановити fzf?

`fzf` — опціональний інструмент для зручної навігації в інтерактивному режимі. Без нього працює звичайний ввід номерів. Для CLI-режиму fzf не потрібен.

- **Linux:** `sudo apt install fzf` (або `pacman -S fzf`, `dnf install fzf`)
- **macOS:** `brew install fzf`
- **Windows:** завантажити binary з https://github.com/junegunn/fzf/releases

### Файли не синхронізуються

Перевірте `.picoignore` — можливо файл підпадає під правило ігнорування. Якщо в корені є `src/` — синхронізується вона, інакше корінь.

### Помилка "No module named 'pyserial' / 'mpremote'"

Встановіть залежності: `pip install pyserial mpremote` (актуально тільки для portable-версії без встановлення пакета).

### Як оновити Pico Sync?

**Перевірка наявності оновлень:** `[s] settings → [!] check update` (pick) або `picosync --check_update` (CLI). Показує новішу версію, changelog та посилання, але не оновлює автоматично.

**Встановлення оновлення:**
- **Через pipx:** `pipx upgrade pico_sync`
- **Через pip:** `pip install --upgrade pico_sync`

### Як отримати повну довідку?

**CLI:** `picosync --help`, `picosync project --help`

У pick-режимі всі доступні дії показуються в меню.

## Ліцензія

[AGPL-3.0](https://github.com/toldk98/pico_sync/blob/main/LICENSE)
