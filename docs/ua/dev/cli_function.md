# CLI режим — повний опис

## 1. Запуск та загальна структура

CLI-режим — одноразові команди без інтерактивного меню. Виконується в `main()` з `cli.py`.

Парсер аргументів будується в `build_parser()`. `--lang` витягується ДО `build_parser()` щоб перекласти допомогу.

Якщо жоден з флагів дії не передано — запускається інтерактивний режим.

---

## 2. `picosync --help` / `-h`

Повний вивід:
```
usage: picosync [-h] [--port PORT] [--sync] [--ls PATH]
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

---

## 3. `picosync --version`

Друк `PICO_SYNC_VERSION` (`"1.1.2"`) та вихід. Ніяких інших дій.

---

## 4. `picosync --sync`

### 4.1 Базова синхронізація

```bash
picosync --sync
```

Алгоритм повністю ідентичний sync в інтерактивному режимі (та сама функція `sync_tree()`):

1. Завантаження `.picoignore` з кореня проекту, компіляція regex
2. Друк активних патернів ігнору та фільтра (за замовчуванням `all`)
3. `pico_list_files()` — знімок всіх файлів на Pico
4. Walk локальної `src/`:
   - Пропуск директорій під ігнором
   - Пропуск `.piconame`
   - Пропуск файлів під ігнором
   - Збір `(remote_path, local_path, data)` + `remote_paths`
5. `pico_batch_sha256(remote_paths)` — SHA-256 всіх файлів на Pico за один `mpremote exec`
6. Для кожного локального файлу:
   - hash збігається → `skip_same` (жовтий)
   - немає на Pico → `upload_new` (зелений)
   - різний hash → `upload_diff` (зелений)
   - upload: base64 + `mpremote exec ubinascii.a2b_base64`
7. Для кожного файлу на Pico без локальної відповідності:
   - Пропуск `/.piconame`
   - `match_filter(filter, path)` — якщо підпадає → `delete_file` (червоний)
8. `delete_empty_dirs()`
9. Друк `sync_complete`

### 4.2 З фільтром

```bash
picosync --sync --filter py         # тільки .py
picosync --sync --filter .wav,.mpy  # конкретні розширення
picosync --sync --filter nopy       # все крім .py
```

Фільтр впливає на видалення. Значення:
- `all` — всі файли без локальної відповідності
- `py` — тільки `.py`
- `py+` — `.py`, `.txt`, `.json`
- `nopy` — все крім `.py`
- `.ext,.ext2` — конкретні розширення

### 4.3 З портом

```bash
picosync --port /dev/ttyACM0 --sync
```

Якщо порт не задано — авто-детект.

---

## 5. `picosync --ls PATH`

```bash
picosync --ls /
picosync --ls /spm
```

Викликає `pico_ls(path)`.

Алгоритм:
1. Функція формує Python-код для виконання на Pico:
```python
import os
p = "{path}"
for f in os.listdir(p):
    fp = p.rstrip('/') + '/' + f
    try:
        s = os.stat(fp)[0]
        if s & 0x4000:
            print('d ' + f)
        else:
            print('- ' + f)
    except:
        pass
```
2. Виконує через `mpremote exec`
3. Друкує результат: `"d <dirname>"` для директорій, `"- <filename>"` для файлів

Підтримує `--port` для вказання конкретного порту.

---

## 6. `picosync --cat FILE`

```bash
picosync --cat /main.py
```

Викликає `pico_cat(file_path)`.

Алгоритм:
1. `mpremote exec 'print(open("{path}").read())'`
2. Вивід вмісту файлу в stdout

Підтримує `--port`.

---

## 7. `picosync --edit FILE`

```bash
picosync --edit /config/settings.py
```

Викликає `pico_edit(file_path)`.

Алгоритм:
1. Читання файлу з Pico через `mpremote exec`
2. Запис у тимчасовий файл (suffix `.py`)
3. Пошук редактора:
   - **macOS:** `open -t` (TextEdit)
   - **Linux:** `nano` → `vim` → `vi` (перший знайдений)
   - **Windows:** `notepad`
4. Якщо не знайдено:
   - Друк `edit_no_editor` з шляхом до temp-файлу
   - Пауза, видалення temp, вихід
5. Запуск редактора як subprocess, очікування завершення
6. Читання зміненого файлу
7. Завантаження на Pico через `mp_write_file(path, data)` (base64 + mpremote exec)
8. Видалення temp-файлу

Підтримує `--port`.

---

## 8. `picosync --search_port`

```bash
picosync --search_port
```

Викликає `interactive_select_port()`.

Алгоритм:
1. `list_ports.comports()` — всі serial порти системи
2. `find_pico_ports()` — тільки Pico (VID 0x2E8A або ключові слова)
3. Якщо портів немає — `no_serial_ports`, вихід
4. Друк нумерованого списку:
   ```
   Available ports:
   0)  /dev/ttyACM0    USB Serial Device  ⭐ (Pico)
   1)  /dev/ttyUSB0    USB2.0-Serial
   ```
   Pico-порти позначені `"⭐"`
5. Запит: `"Select port number (or Enter to cancel): "`
6. Валідація:
   - Порожньо → вихід
   - Не цифра → `enter_number`
   - Поза діапазоном → `invalid_number`
7. При виборі:
   - Встановлює `MPREMOTE_PORT` в оточенні
   - Друк `config_port_set`

---

## 9. `picosync --check_update`

```bash
picosync --check_update
```

Викликає `check_for_updates()`.

Алгоритм:
1. HTTP GET `https://raw.githubusercontent.com/toldk98/pico_sync/main/meta/latest_version.json` (таймаут 2с)
2. Парсинг JSON:
   ```json
   {
     "version": "1.1.2",
     "changelog": "...",
     "url": "https://github.com/..."
   }
   ```
3. Порівняння з `PICO_SYNC_VERSION` (`"1.1.2"`):
   - **Відрізняється:** друк:
     - `update_available` (зелений)
     - `latest_version: X.Y.Z`
     - `current_version: 1.1.2`
     - changelog (якщо є)
     - `download_url: https://...`
   - **Однакова:** друк `already_latest` (зелений)
4. Будь-який exception (network error, JSON parse error) — мовчазний пропуск

---

## 10. `picosync --reboot`

```bash
picosync --reboot
```

1. Друк `rebooting` (синій)
2. `subprocess.run(["mpremote", "reset"])`
3. Програмний reset — еквівалент натискання RUN на платі

Підтримує `--port`.

---

## 11. `picosync --monitor`

```bash
picosync --monitor
```

Викликає `serial_monitor(port)`.

Алгоритм:
1. Якщо порт не задано — `find_pico_port_auto()`
2. Якщо не знайдено — `port_not_found`, вихід
3. Друк `opening_port` (шлях + 115200 baud)
4. Друк `waiting_data`

**Зовнішній цикл (авто-реконект):**
- `serial.Serial(port, 115200, timeout=0.5)`
- **Внутрішній цикл:**
  - `readline()` — читання рядка
  - Декодування UTF-8 з `replace` для некоректних символів
  - Вивід у stdout зеленим кольором (`\033[92m`)
  - `sleep(0.05)` якщо `len(data) == 0`
  - `SerialException` або `OSError` → друк `device_disconnected`, вихід до зовнішнього циклу
- На помилці відкриття: друк `pico_not_ready`, `sleep(1)`
- Після відключення: сканування нових Pico-портів
  - Якщо `new_port != port` → `switching_port`, оновлення `port`

Вихід: `Ctrl+C` → `KeyboardInterrupt` → завершення

Автоматичне перепідключення при:
- Перезавантаженні Pico
- Зміні USB-порту
- Тимчасовому відключенні

Підтримує `--port`.

---

## 12. `picosync --pick`

```bash
picosync --pick
```

Явний запуск інтерактивного режиму. Детально описано в `pick_function.md`.

Повністю еквівалентно `picosync` без аргументів.

---

## 13. `picosync --filter FILTER`

```bash
picosync --sync --filter py
picosync --sync --filter .wav,.mpy
```

Працює тільки в комбінації з `--sync`. Самостійно нічого не робить.

Значення:
- `all` — всі файли
- `py` — тільки `.py`
- `py+` — `.py`, `.txt`, `.json`
- `nopy` — все крім `.py`
- `.ext,.ext2` — власні розширення через кому (напр. `.bin,.hex`)

Логіка `match_filter(filter, path)`:
- `all` → завжди True
- `py` → path закінчується на `.py`
- `py+` → path закінчується на `.py` або `.txt` або `.json`
- `nopy` → True якщо НЕ закінчується на `.py`
- `.ext,.ext2` → True якщо закінчується на будь-яке з перелічених розширень

---

## 14. `picosync --init`

```bash
picosync --init
```

Викликає `init_project(os.getcwd())`.

Створює в поточній директорії:

| Файл | Вміст | Умова |
|------|-------|-------|
| `.picoignore` | Стандартні патерни | Якщо не існує |
| `.picosyncconfig` | `{"port": "", "filter": "all", "piconame": ""}` | Якщо не існує |

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

Друк: `created` (зелений) або `already exists` (жовтий) для кожного елемента.

---

## 15. `picosync --set-name NAME`

```bash
picosync --set-name my-pico
```

1. Пошук Pico (авто-детект або `--port`)
2. Якщо не знайдено — `port_not_found`, вихід
3. `mpremote exec 'with open("/.piconame", "w") as f: f.write("{name}")'`
4. Збереження `{"piconame": name}` в `.picosyncconfig` поточного проекту
5. Друк `piconame_set`

---

## 16. `picosync --lang {ua,en}`

```bash
picosync --lang ua
picosync --lang en
```

- Витягується ДО `build_parser()` (щоб перекласти help)
- Викликає `set_language(value)`
- Впливає на всі текстові повідомлення в поточному запуску
- Може комбінуватися з будь-якою іншою командою

Пріоритет визначення мови:
1. `--lang ua/en` (найвищий)
2. `~/.config/pico_sync/settings.json` → `language`
3. `$LANG` (якщо `uk*` → `ua`, інакше → `en`)

---

## 17. `picosync --port PORT`

```bash
picosync --port /dev/ttyACM0 --sync
picosync --port /dev/ttyACM48 --monitor
```

Задає COM-порт явно. Працює з будь-яким флагом дії:
- `--sync`
- `--ls`
- `--cat`
- `--edit`
- `--monitor`
- `--reboot`
- `--set-name`
- `--search_port` (встановлює `MPREMOTE_PORT` в оточенні)
- `--check_update` (не використовує порт, ігнорується)

Якщо не задано — авто-детект:
1. За `.piconame` з конфігу (якщо є)
2. За збереженим `port` з конфігу
3. Авто-детект першого Pico
4. Не знайдено → помилка

---

## 18. `picosync project`

Підкоманди для керування проектами.

### 18.1 `picosync project --help`

```
usage: picosync project [-h] {list,add,remove} ...

positional arguments:
  {list,add,remove}
    list      List all saved projects
    add       Add project directory
    remove    Remove project by name

options:
  -h, --help   show this help message and exit
```

### 18.2 `picosync project list`

```bash
picosync project list
```

Вивід: нумерований список всіх збережених проектів:
```
1) my-project  (/home/user/projects/my-project)
2) other-project  (/home/user/other)
```

Якщо проектів немає — `project_no_projects`.

### 18.3 `picosync project add PATH`

```bash
picosync project add /home/user/my-project
```

1. `os.path.abspath(os.path.expanduser(path))`
2. Якщо директорія існує:
   - `add_project(path)` — додає/оновлює в `~/.config/pico_sync/projects.json`
   - `project_added`
3. Якщо не існує: `project_not_found`

### 18.4 `picosync project remove NAME`

```bash
picosync project remove my-project
```

1. Пошук проекту за `name`
2. Якщо знайдено: `remove_project(name)`, `project_removed`
3. Якщо не знайдено: `project_not_found_remove`

---

## 19. `picosync project preview` (внутрішній, для fzf)

```bash
picosync project preview {line}
picosync project preview-main {item} {root}
```

Використовується тільки fzf preview-панеллю в інтерактивному режимі. Не призначено для прямого виклику.

### `project preview`

Парсить рядок з селектора проектів, витягує `root`, викликає `_print_project_preview()`.

### `project preview-main`

Парсить item та root з головного меню:
- `..` → `preview_back_projects`
- `[i] info` → `_print_project_preview()` з детальною інфою
- `[f] files` → `preview_browse_files`
- `[d] device` → `preview_device_menu`
- `[c] config` → `preview_config_menu`

---

## 20. Взаємодія --port та оточення

При використанні `--port`:
- Встановлюється `os.environ["MPREMOTE_PORT"] = port`
- mpremote автоматично використовує `MPREMOTE_PORT` для підключення
- Наступні виклики `mpremote` в рамках сесії використовують цей порт

При авто-детекті:
- `find_pico_by_name()` — перебирає всі Pico, читає `/.piconame`
- `find_pico_port_auto()` — перший Pico-порт
- `ensure_port()` — комбінує логіку: piconame → configured port → auto

---

## 21. Обробка помилок

| Ситуація | Поведінка | Код виходу |
|----------|-----------|------------|
| mpremote не знайдено (`FileNotFoundError`) | Друк `mpremote_not_found` | 1 |
| Pico не знайдено | Друк `device_not_found` або `port_not_found` | 1 |
| `CalledProcessError` при mpremote | Друк помилки, вихід з команди | 1 |
| Невідома помилка | Друк traceback | 1 |
| `--edit` без редактора | Друк `edit_no_editor` + temp-шлях | 0 |
| `--cat` файл не існує | Помилка mpremote → `CalledProcessError` | 1 |
| `--check_update` network error | Мовчазний пропуск | 0 |
| `project add` неіснуючий шлях | Друк `project_not_found` | 0 |
| `project remove` незнайдений | Друк `project_not_found_remove` | 0 |
