# Pick (інтерактивний режим) — повний опис

## 1. Запуск

Інтерактивний режим запускається:
- `picosync` — без аргументів
- `picosync --pick` — явний запуск
- `picosync --lang ua` — тільки мова, без інших флагів дій
- Також коли жоден з флагів дії (`--sync`, `--ls`, `--cat`, `--edit`, `--search_port`, `--check_update`, `--reboot`, `--monitor`) не передано

При запуску викликається `_run_interactive(args)` який входить в нескінченний цикл:
```
while True:
    project, action = _pick_project_or_action()
    if action == "quit": exit(0)
    if project:
        projects.touch_project(project["root"])  # оновлює last_used
        root = project["root"]
    else:
        root = os.getcwd()
        projects.add_project(root)
    pick_mode(root, project=project)
```

Після виходу з `pick_mode()` (користувач вибрав `..`) цикл повторюється — знову показується список проектів.

### 1.1 Загальний принцип роботи меню (fzf vs numbered fallback)

Кожне меню в інтерактивному режимі проходить через функцію `_fzf_pick()` або `_uinput_pick()`.

**Якщо fzf встановлено** (`shutil.which("fzf") is not None`):
- Список елементів передається через stdin (newline-separated)
- fzf запускається з `--border`, `--prompt="> "`, `--header="..."`, `--preview` і `--preview-window right:50%:border`
- Користувач може фільтрувати список ввівши текст — fzf показує тільки збіги
- Навігація: `↑↓` або `Ctrl+N/Ctrl+P`
- Вибір: `Enter` → рядок вибору в stdout, код повернення 0
- Скасування: `Esc` або `Ctrl+C` → порожній stdout, код повернення 1 → інтерпретується як `None` (відміна)
- Якщо fzf вилітає з помилкою (напр. неправильна версія) — автоматичне падіння до numbered fallback

**Якщо fzf не встановлено (numbered fallback):**
- Елементи друкуються нумерованим списком у stdout: `0) item1`, `1) item2`, ...
- Header друкується над списком як звичайний текст
- Ввід через `_uinput()`:
  - Порожній рядок → `None` (відміна)
  - Не число → повторний запит
  - Число поза діапазоном → `invalid_number`, повторний запит
  - Валідне число → повертається відповідний елемент

---

## 2. Стартовий екран — вибір проекту

Функція `_pick_project_or_action()`.

### 2.1 Відображення

Список елементів:
```
<project_name>  (<project_root>)    — кожен збережений проект
[+] add project                      — додати новий проект
[-] remove project                   — видалити проект
[s] settings                         — глобальні налаштування
[q] quit                             — вихід
```

**Інтерфейс (fzf):** повноекранний список з header `" Esc=back  /=search   Select project"`. Справа preview-панель, яка викликає `pico_sync project preview {line}` — показує інфо про проект під курсором або опис спеціального пункту. `/` активує fuzzy-пошук. `Esc` або `Ctrl+C` → відміна (еквівалент `[q] quit`).

**Інтерфейс (без fzf):** нумерований список, header друкується окремо. Ввід номера для вибору, Enter без вводу = відміна.

Проекти відсортовані за `last_used` (спочатку найновіші). Якщо проектів немає — показується тільки `[+] add project` та `[q] quit`.

### 2.2 Пункт: вибір проекту

- Користувач вибирає рядок з назвою проекту
- Повертається `(project_dict, "select")`
- Далі `_run_interactive` викликає `pick_mode(root, project=project)`

### 2.3 Пункт: `[+] add project`

1. Запит: `"Path to project root (Enter — current directory): "`
2. Читання вводу через `_uinput()` — захист від `UnicodeDecodeError`
3. Якщо порожньо — береться `os.getcwd()`
4. `os.path.abspath(os.path.expanduser(path))`
5. Якщо шлях — існуюча директорія:
   - Викликає `projects.add_project(path)` — додає/оновлює в `~/.config/pico_sync/projects.json`
   - Друк `project_added`
6. Якщо не директорія: друк `project_not_found`
7. Повернення до списку проектів

### 2.4 Пункт: `[-] remove project`

1. Якщо проектів немає — друк `project_no_projects`, повернення
2. Показує під-меню зі списком проектів + `..` в кінці.
   **Інтерфейс (fzf):** header `" Esc=back  /=search"`, прев'ю як у головному селекторі.
   **Інтерфейс (без fzf):** нумерований список.
3. Якщо вибрано `..` або відміна (Esc/порожній ввід) — повернення
4. Якщо вибрано проект:
   - Викликає `projects.remove_project(name)`
   - Друк `project_removed` або `project_not_found_remove`
5. Повернення до списку проектів

### 2.5 Пункт: `[s] settings` — глобальні налаштування

Під-меню:
```
..              -> назад до списку проектів
[~] lang        -> вибір мови
[!] check update -> перевірка оновлень
```

**Інтерфейс (fzf):** header, preview‑панель показує опис пункту.
**Інтерфейс (без fzf):** нумерований список.
Відміна (Esc/порожній ввід) → назад до списку проектів.

### 2.5.1 `[~] lang`

Під-меню:
```
..   -> назад
ua   -> Українська
en   -> English
```

**Інтерфейс (fzf):** header, preview показує поточну мову.
**Інтерфейс (без fzf):** нумерований список.
Відміна → назад до settings.

- Вибір `ua` або `en`:
  - Виклик `set_language(code)` — оновлює `lang.py` та зберігає в `~/.config/pico_sync/settings.json`
  - Друк `lang_set`
  - Пауза `press_enter`
  - Повернення до меню settings

### 2.5.2 `[!] check update`

- Виклик `check_for_updates()`
- Пауза `press_enter`
- Повернення до меню settings

Детальніше про перевірку:
1. Fetch `https://raw.githubusercontent.com/toldk98/pico_sync/main/meta/latest_version.json` (таймаут 2с)
2. Парсинг JSON: `version`, `changelog`, `url`
3. Порівняння з `PICO_SYNC_VERSION` (`"1.1.2"`):
   - Відрізняється: друк `update_available`, `latest_version`, `current_version`, changelog, url
   - Однакова: друк `already_latest`
4. Будь-яка помилка — мовчазний пропуск

### 2.6 Пункт: `[q] quit`

- Повертає `(None, "quit")`
- `_run_interactive` викликає `exit(0)`

---

## 3. Головне меню проекту

Функція `pick_mode(root, project=None)`.

### 3.1 Відображення

```
..          -> назад до списку проектів
[i] info    -> інформація про проект (тільки перегляд)
[f] files   -> браузер файлів на Pico
[d] device  -> синхронізація, монітор, перезавантаження
[c] config  -> налаштування порту, src, piconame, init
```

**Інтерфейс (fzf):** header `" Esc=back  /=search"`. Preview-панель викликає `pico_sync project preview-main {item} {p_root}`:
- `..` → `preview_back_projects`
- `[i] info` → повна інформація про проект
- `[f] files` → `preview_browse_files`
- `[d] device` → `preview_device_menu`
- `[c] config` → `preview_config_menu`

**Інтерфейс (без fzf):** нумерований список, header друкується текстом. Відміна (порожній ввід) → назад до списку проектів.

### 3.2 Пункт: `..`

- Вихід з `pick_mode()`, повернення до списку проектів

### 3.3 Пункт: `[i] info` — інформація про проект

Функція `_show_project_info()`.

Збирає та показує:
1. **Назва проекту** та **коренева директорія**
3. **Налаштований пристрій**: якщо `piconame` встановлено — `find_pico_by_name(piconame)`; інакше `port` з конфігу або `"not set"`
4. **Знайдені пристрої**: `find_pico_ports()` — список всіх підключених Pico
5. **Іконка статусу**: `"⚡"` якщо налаштований пристрій знайдено, інакше `"✘"`
6. **Статус**: `"connected"` або `"not found"`
7. **Поточний фільтр**: `filter_description(current_filter)`
8. Якщо `piconame` встановлено, але пристрій не знайдено — жовте попередження `info_piconame_not_found`
9. Список всіх знайдених Pico-портів з `"⚡"` маркером; налаштований — з `" (configured)"`

Завершується `"Press Enter to go back"`. Читання Enter, повернення до головного меню.

### 3.4 Пункт: `[f] files` — браузер файлів

1. Виклик `ensure_port(port, piconame=piconame)`
2. Якщо порт не знайдено — друк `device_not_found`, пауза, повернення до головного меню
3. Якщо `files_cache is None` — завантаження списку файлів через `pico_list_files()`
4. Виклик `_pick_files_menu(files_cache)` → `_pick_ls_browser()`

#### 3.4.1 Відображення браузера

```
..              -> на рівень вище
[r] refresh     -> оновити список (тільки в корені "/")
[*] find        -> пошук (всі файли плоским списком)
d <dirname>/    -> увійти в директорію
- <filename>    -> дії з файлом
```

**Інтерфейс (fzf):** header `" Esc=back  /=search"`, preview-панель показує вміст файлу або список директорії.
**Інтерфейс (без fzf):** нумерований список.
Відміна → на рівень вище або вихід з браузера.

#### 3.4.2 `..` — вихід або на рівень вище
- Якщо не в корені — перехід до батьківської директорії
- Якщо в корені — вихід з браузера

#### 3.4.3 `[r] refresh` — оновлення
- Повертає сигнал `"refresh"`
- Зовнішній цикл перезавантажує всі файли, перебудовує дерево, заходить знову

#### 3.4.4 `[*] find` — пошук
- Показує плоский відсортований список всіх файлів на Pico (prefix `..` зверху)
- **Інтерфейс (fzf):** header `" Esc=back  /=search   All files on Pico"`, preview показує вміст файлу під курсором
- **Інтерфейс (без fzf):** нумерований список
- Вибір файлу → контекстне меню файлу
- Вибір `..` або відміна → повернення до браузера

#### 3.4.5 `d <dirname>/` — вхід в директорію
- Рекурсивний вхід в `_browse(node[dir_name], sub_path)`
- Якщо рекурсія повертає `"refresh"` — пропагація нагору

#### 3.4.6 `- <filename>` — контекстне меню файлу

Під-меню:
```
..     -> назад до списку файлів
cat    -> перегляд вмісту
edit   -> редагування
rm     -> видалення
```

**Інтерфейс (fzf):** header `" Esc=back  /=search   File actions"`, preview короткий опис дії.
**Інтерфейс (без fzf):** нумерований список.
Відміна → назад до списку файлів.

##### cat
- Виклик `pico_cat(file_path)` — `mpremote exec 'print(open("{path}").read())'`
- Друк вмісту
- Пауза `press_enter`

##### edit
- Виклик `pico_edit(file_path)`
- Алгоритм:
  1. Читання файлу з Pico через `mpremote exec`
  2. Запис у тимчасовий файл (suffix `.py`)
  3. Пошук редактора:
     - macOS: `open -t`
     - Linux: `nano` → `vim` → `vi`
     - Windows: `notepad`
  4. Якщо редактор не знайдено — друк `edit_no_editor` з шляхом до тимчасового файлу, пауза, видалення, вихід
  5. Запуск редактора, очікування закриття
  6. Читання зміненого файлу
  7. Завантаження на Pico через `mp_write_file(path, data)`
  8. Видалення тимчасового файлу
- Повернення до контекстного меню

##### rm
- Запит: `"Delete {name}? (y/N): "`
- Якщо `"y"` (маленька літера):
  - `mpremote exec 'import os; os.remove("{path}")'`
  - Друк `deleted_ok`
  - Видалення з дерева (якщо не з режиму find)
  - Вихід до батьківської директорії

### 3.5 Пункт: `[d] device` — меню пристрою

Функція `_pick_device_menu(port, piconame=None)`.

1. Виклик `ensure_port(port, piconame=piconame)` на вході
2. Якщо порт не знайдено — друк `device_not_found`, повернення `(port, False)`
3. Читання `current_filter` з конфігу

Відображення:
```
..       -> назад
sync     -> синхронізація
monitor  -> серійний монітор
reboot   -> перезавантаження
```

**Інтерфейс (fzf):** header, preview описує кожну дію.
**Інтерфейс (без fzf):** нумерований список.
Відміна → збереження фільтра, повернення до головного меню.

#### 3.5.1 `..` — назад
- Збереження `{"filter": current_filter}` в конфіг
- Повернення `(port, needs_refresh)`

#### 3.5.2 `sync` — синхронізація

**Крок 1: Вибір фільтра**

Під-меню:
```
all       -> всі файли (видаляє зайве на Pico)
py        -> тільки .py
py+       -> .py, .txt, .json
nopy      -> все крім .py
custom    -> власні розширення (через кому)
```

**Інтерфейс (fzf):** header `" Current filter: {filter}"`, preview описує фільтр.
**Інтерфейс (без fzf):** нумерований список з поточним фільтром у заголовку.
Відміна → назад до device menu.

- Відміна → назад до device menu
- `custom` → запит `"Extensions (comma-sep, e.g. .py,.txt): "`, порожньо = `"all"`
- Збереження `current_filter` в конфіг

**Крок 2: Виконання sync_tree**

1. Завантаження `.picoignore` з кореня проекту, компіляція regex
2. Друк активних патернів ігнору та фільтра
3. `pico_list_files()` — знімок всіх файлів на Pico
4. Walk локальної директорії `root` (авто-детект `src/` якщо існує):
   - Пропуск директорій, що підпадають під ігнор
   - Пропуск файлів `.piconame`
   - Пропуск файлів, що підпадають під ігнор (`skip_ignored`)
   - Збір `(remote_path, local_path, data)` для всіх файлів
   - Збір всіх `remote_paths` для SHA-256
5. `pico_batch_sha256(remote_paths)` — один `mpremote exec` рахує SHA-256 всіх файлів за один раз
6. Для кожного локального файлу:
   - `local_hash == remote_hash` → `skip_same` (жовтий)
   - `remote_hash is None` → `upload_new` (зелений)
   - `remote_hash != local_hash` → `upload_diff` (зелений)
   - Завантаження через `mp_write_file(remote, data)` — base64 + mpremote exec з авто-створенням директорій
7. Для кожного файлу на Pico, якого немає локально:
   - Пропуск `/.piconame`
   - Перевірка `match_filter(filter, remote_file)`
   - Якщо підпадає — `delete_file` (червоний), видалення через `mpremote exec os.remove`
8. `delete_empty_dirs()` — видалення порожніх директорій на Pico
9. Друк `sync_complete`
10. `needs_refresh = True`
11. Пауза `press_enter`

#### 3.5.3 `monitor` — серійний монітор

Функція `serial_monitor(port)`:

1. Якщо порт не задано — `find_pico_port_auto()`
2. Якщо досі немає — друк `port_not_found`, вихід
3. Друк `opening_port` з портом і BAUD (115200)
4. Друк `waiting_data`

**Зовнішній цикл (авто-перепідключення):**
- Спроба `serial.Serial(port, BAUD, timeout=0.5)`
- **Внутрішній цикл:**
  - `readline()` — читання рядків
  - Декодування UTF-8, друк зеленим
  - `sleep(0.05)` якщо даних немає
  - `SerialException` або `OSError` → друк `device_disconnected`, вихід до зовнішнього циклу
- На помилці відкриття → друк `pico_not_ready`, `sleep(1)`
- Після відключення: перевірка чи з'явився новий Pico-порт
  - Якщо `new_port != port` → друк `switching_port`, оновлення `port`, перепідключення

Вихід: `Ctrl+C` → `KeyboardInterrupt` → повернення до device menu

#### 3.5.4 `reboot` — перезавантаження

- Друк `rebooting` синім
- `subprocess.run(["mpremote", "reset"])`
- `needs_refresh = True`
- Повернення до device menu (без паузи)

### 3.6 Пункт: `[c] config` — меню налаштувань

Функція `_pick_config_menu(port)`.

Відображення:
```
..              -> назад до головного меню
port_settings   -> налаштування підключення Pico
init            -> створення .picoignore, .picosyncconfig
```

**Інтерфейс (fzf):** header, preview описує дію.
**Інтерфейс (без fzf):** нумерований список.
Відміна → повернення до головного меню.

#### 3.6.1 `..` — назад
- Повернення `port`

#### 3.6.2 `port_settings` — порт і piconame

Функція `_pick_port_settings_menu(port)`.

Відображення:
```
..         -> назад до config
port       -> вибір COM-порту вручну
piconame   -> авто-пошук по імені пристрою (.piconame)
```

**Інтерфейс (fzf):** header, preview.
**Інтерфейс (без fzf):** нумерований список.
Відміна → назад до config.

##### `port` — ручний вибір порту

1. Виклик `interactive_select_port()`:
   - Отримання всіх serial-портів через `list_ports.comports()`
   - Отримання Pico-портів через `find_pico_ports()`
   - Якщо портів немає — друк `no_serial_ports`
   - Друк: `available_ports` + нумерований список з `"⭐"` для Pico
   - Запит: `"Select port number (or Enter to cancel): "`
   - Валідація: порожньо → `None`, не цифра → `enter_number`, поза діапазоном → `invalid_number`
2. Якщо порт вибрано:
   - `port = chosen`
   - `os.environ["MPREMOTE_PORT"] = port`
   - Збереження `{"port": port}` в `.picosyncconfig`
   - Друк `config_port_set` зеленим
3. Пауза `press_enter`

##### `piconame` — керування іменем пристрою

Показує поточне ім'я (або `"Name not set"`).

Під-меню:
```
..       -> назад
detect   -> прочитати /.piconame з Pico і зберегти в конфіг
set      -> записати нове ім'я на Pico і зберегти
clear    -> видалити /.piconame з Pico і очистити конфіг
```

**Інтерфейс (fzf):** header показує `"Current name: {name}"`, preview.
**Інтерфейс (без fzf):** header друкується текстом, нумерований список.
Відміна → назад до port settings.

**detect:**
1. `ensure_port(config.get("port"))`. Якщо не вдалося — `find_pico_port_auto()`
2. Якщо порт не знайдено — друк `port_not_found`, пауза, вихід
3. `os.environ["MPREMOTE_PORT"] = p`
4. `_read_piconame_from_port(p)` — `mpremote exec 'import os; print(open("/.piconame").read().strip())'`
5. Якщо ім'я знайдено — збереження `{"piconame": name}` в конфіг, друк `piconame_detected` зеленим
6. Якщо не знайдено — друк `piconame_not_on_pico` жовтим
7. Пауза `press_enter`

**set:**
1. Запит: `"New name for Pico: "`
2. Якщо не порожньо:
   - `ensure_port(config.get("port"))`, при невдачі — `find_pico_port_auto()`
   - Якщо порт не знайдено — друк `port_not_found`, пауза, вихід
   - `os.environ["MPREMOTE_PORT"] = p`
   - `mpremote exec 'with open("/.piconame", "w") as f: f.write("{name}")'`
   - Збереження `{"piconame": new_name}` в конфіг
   - Друк `piconame_set` зеленим
3. Пауза `press_enter`

**clear:**
1. `ensure_port(config.get("port"))`, при невдачі — `find_pico_port_auto()`
2. Якщо порт знайдено:
   - `os.environ["MPREMOTE_PORT"] = p`
   - `mpremote exec 'import os; os.remove("/.piconame")'`
3. Збереження `{"piconame": ""}` в конфіг
4. Друк `piconame_cleared` зеленим
5. Пауза `press_enter`

#### 3.6.3 `init` — ініціалізація проекту

Функція `init_project(project_root)`.

Створює в корені проекту:

| Файл | Вміст | Умова |
|------|-------|-------|
| `.picoignore` | Стандартні патерни | Тільки якщо не існує |
| `.picosyncconfig` | `{"port": "", "filter": "all", "piconame": ""}` | Тільки якщо не існує |

Для кожного файлу/директорії друк `created` (зелений) або `already exists` (жовтий).

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

Пауза `press_enter`.

---

## 4. Файлова система Pico

### 4.1 `pico_list_files()`

Рекурсивний walk всіх файлів на Pico через один `mpremote exec`:
```python
import os
res = []
def walk(p):
    for f in os.listdir(p):
        fp = p + '/' + f if p != '/' else '/' + f
        try:
            st = os.stat(fp)[0]
            if st & 0x4000:
                walk(fp)
            else:
                res.append(fp)
        except:
            pass
walk('/')
print('\n'.join(res))
```
Повертає відсортований список шляхів.

### 4.2 `pico_ls(path)`

Список однієї директорії. Префікс `"d "` для директорій, `"- "` для файлів.

### 4.3 `pico_cat(path)`

`mpremote exec 'print(open("{path}").read())'` — вивід вмісту файлу.

### 4.4 `pico_batch_sha256(paths)`

Один `mpremote exec` для всіх шляхів:
```python
import ubinascii, uhashlib
paths = [...]
for p in paths:
    try:
        h = uhashlib.sha256()
        f = open(p, 'rb')
        while True:
            b = f.read(2048)
            if not b: break
            h.update(b)
        f.close()
        print('OK', ubinascii.hexlify(h.digest()).decode(), p)
    except OSError:
        print('--', p)
```
Повертає `{path: sha256_hex}` або `{path: None}` для відсутніх.

### 4.5 `mp_write_file(remote_path, data)`

1. Авто-створення батьківських директорій через `os.mkdir`
2. Base64-кодування даних
3. `mpremote exec 'ubinascii.a2b_base64(b"...")'` з такою самою структурою директорій

### 4.6 `delete_empty_dirs()`

Рекурсивний обхід Pico, видалення порожніх директорій. Друк `"RMDIR <path>"` для кожної.

---

## 5. Порти

### 5.1 `is_pico_port(port)`

Повертає True якщо:
- `port.vid == 0x2E8A` (Raspberry Pi)
- Або будь-яке з `("Pico", "RP2", "MicroPython", "USB Serial Device")` в `description + " " + product`

### 5.2 `find_pico_ports()`

Повертає список всіх COM-портів, що задовольняють `is_pico_port()`.

### 5.3 `find_pico_port_auto()`

Повертає `device` першого Pico-порту або `None`.

### 5.4 `find_pico_by_name(name)`

Перебирає всі Pico-порти, на кожному виконує `mpremote exec 'import os; print(open("/.piconame").read().strip())'` і порівнює з name. Повертає device шлях першого збігу або `None`.

### 5.5 `ensure_port(port, piconame=None)`

1. Якщо `piconame` задано — `find_pico_by_name(piconame)`. Якщо знайдено — встановлює `MPREMOTE_PORT` і повертає
2. Якщо `port` задано (не None) — повертає як є
3. Інакше — `find_pico_port_auto()`. Якщо знайдено — встановлює `MPREMOTE_PORT` і повертає

### 5.6 `interactive_select_port()`

1. `list_ports.comports()` — всі serial порти
2. `find_pico_ports()` — тільки Pico
3. Якщо портів немає — `no_serial_ports`, повернення `None`
4. Друк нумерованого списку, Pico позначені `"⭐"`
5. Ввід номера, валідація
6. Повернення `ports[idx].device` або `None`

---

## 6. Проекти

Зберігаються в `~/.config/pico_sync/projects.json`:
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

- `name` — basename кореневої директорії
- `root` — абсолютний шлях
- `last_used` — ISO 8601, оновлюється при кожному `touch_project`

Сортування в селекторі: за `last_used` спаданням.

---

## 7. Глобальні налаштування

`~/.config/pico_sync/settings.json`:
```json
{
  "language": "ua"
}
```

- `language` — `"ua"` або `"en"`. Авто-детект: спочатку з settings.json, потім з `$LANG` (якщо `uk*` → `"ua"`, інакше → `"en"`)

---

## 8. Конфігурація проекту

`<project_root>/.picosyncconfig` (JSON):
```json
{
  "port": "",
  "filter": "all",
  "piconame": ""
}
```

- `port` — збережений COM-порт
- `filter` — поточний фільтр синхронізації
- `piconame` — ім'я пристрою

---

## 9. Фільтри синхронізації

| Фільтр | Що видаляється з Pico |
|--------|----------------------|
| `all` | Всі файли, яких немає локально |
| `py` | Тільки `.py` |
| `py+` | `.py`, `.txt`, `.json` |
| `nopy` | Все крім `.py` |
| `.ext,.ext2` | Файли з вказаними розширеннями |

Фільтр впливає тільки на **видалення** зайвих файлів з Pico. Завантажуються всі файли незалежно від фільтра.

---

## 10. `_uinput()` — захищений ввід

Замінює `input()` в усіх місцях. Використовує `sys.stdin.readline()` замість `input()` щоб уникнути `UnicodeDecodeError` на Windows з деякими кодуваннями.

Застосовується в:
- Вибір номера в fallback-меню
- Введення шляху проекту
- Введення імені piconame
- Введення розширень для custom фільтра
- Вибір порту
- Підтвердження видалення (y/N)
- `press_enter`

---

## 11. ANSI кольори (C class)

| Атрибут | Код | Колір |
|---------|-----|-------|
| `C.GREEN` | `\033[92m` | Зелений |
| `C.YELLOW` | `\033[93m` | Жовтий |
| `C.RED` | `\033[91m` | Червоний |
| `C.BLUE` | `\033[94m` | Синій |
| `C.RESET` | `\033[0m` | Скидання |

На Windows: `os.system("")` активує ANSI-обробку в терміналі.

---

## 12. Обробка помилок

| Ситуація | Поведінка |
|----------|-----------|
| Pico не знайдено в `[f] files` | Друк `device_not_found`, пауза, повернення до головного меню |
| Pico не знайдено в `[d] device` | Друк `device_not_found`, повернення до device menu |
| Pico не знайдено при piconame detect/set/clear | Друк `port_not_found`, пауза, повернення |
| Немає serial-портів | Друк `no_serial_ports`, повернення `None` |
| Помилка списку файлів | Порожній список, друк `pico_list_error` |
| mpremote не встановлено | Друк `mpremote_not_found`, `sys.exit(1)` |
| Редактор не знайдено для edit | Друк `edit_no_editor` з temp-шляхом, очищення |
| Помилка upload під час sync | Друк помилки, вихід з sync |
| UnicodeDecodeError при вводі шляху проекту | Друк `project_read_error`, повторний запит |
| Помилка check_for_updates | Мовчазний пропуск |
