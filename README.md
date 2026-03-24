# remove_watermark

Проект для работы с фото в браузере и офлайн-утилитами:

- **Удаление белого текста и водяных знаков** — веб (`index.html`) и Python CLI (`remove_watermark.py`).
- **Конвертация в WebP** — веб (`compress-webp.html`) и скрипты для macOS / Windows (контекстное меню).

## Сайт

[rafael-mansurov.github.io/remove-watermark/](https://rafael-mansurov.github.io/remove-watermark/)

- Главная (водяные знаки): [`index.html`](index.html)
- Сжатие в WebP: [`compress-webp.html`](compress-webp.html)

## Важно

Используйте инструмент только для изображений, которые принадлежат вам или для которых у вас есть явное разрешение на редактирование. Соблюдайте авторские права.

## Что в репозитории

| Файл / папка | Назначение |
|--------------|------------|
| `index.html` | Удаление водяных знаков в браузере (OpenCV.js, локально на клиенте). |
| `compress-webp.html` | Конвертация в WebP в браузере (canvas, локально). |
| `styles.css` | Общие стили для страниц. |
| `footer.js` | Общий футер для обеих HTML-страниц. |
| `favicon.svg`, `og.webp` | Иконка и превью для соцсетей. |
| `robots.txt`, `sitemap.xml` | Для публикации на GitHub Pages. |
| `remove_watermark.py` | CLI: пакетная обработка с интерактивной зоной. |
| `requirements.txt` | Зависимости Python. |
| `Convert-to-WebP.workflow/` | Quick Action для macOS (Finder) — платный артефакт; в репозитории может быть превью/оболочка. |
| `windows/` | PowerShell: установка пункта «Convert to WebP» в контекстное меню Windows (`install.ps1`, `ConvertToWebP.ps1`, `uninstall.ps1`). |

## Веб: водяные знаки (`index.html`)

- Настройка порога и радиуса inpainting, зоны на canvas.
- Пакет нескольких файлов, HEIC через heic2any (CDN).
- Модель OpenCV подгружается с CDN.

## Веб: WebP (`compress-webp.html`)

- Загрузка, предпросмотр, ползунок качества, пакетное сжатие с общим качеством.
- Инструкции для macOS (workflow) и Windows (одна команда `irm … install.ps1 | iex`).

## Windows: контекстное меню

После деплоя на GitHub (ветка `main`):

```powershell
irm "https://raw.githubusercontent.com/rafael-mansurov/remove-watermark/main/windows/install.ps1" | iex
```

Скрипт кладёт файлы в `%LOCALAPPDATA%\WebP-ContextMenu`, добавляет пункт меню, при необходимости предлагает поставить `cwebp` через `winget`. Удаление: `uninstall.ps1` в той же папке (см. вывод `install.ps1`).

## Быстрый старт (локально)

```bash
python3 -m http.server 8080
```

Открой [http://localhost:8080](http://localhost:8080).

## Python CLI (водяные знаки)

### Требования

- macOS (выбор папки через `osascript`)
- Python 3.9+
- `pip install -r requirements.txt`

### Запуск

```bash
python3 remove_watermark.py
```

Результаты по умолчанию: `<папка>/cleaned/`.

### Параметры

```bash
python3 remove_watermark.py --help
```

- `-i, --input` — папка с изображениями  
- `--region X1 Y1 X2 Y2` — стартовая зона (доли кадра)  
- `--no-skip` — не пропускать уже обработанные  

### Управление в редакторе

- Углы зоны — размер, перетаскивание внутри — сдвиг.  
- `ENTER` / `SPACE` — обработать, `S` / `N` — пропустить, `ESC` — выход.

## Поддерживаемые форматы (Python)

`jpg`, `jpeg`, `png`, `bmp`, `tiff`, `tif`, `webp`

## Как это работает (водяные знаки)

1. В зоне по порогу выделяются светлые пиксели.  
2. Маска расширяется (`dilate`).  
3. `cv2.inpaint(..., INPAINT_TELEA)` восстанавливает фон.

## Локальная разработка

```bash
git clone https://github.com/rafael-mansurov/remove-watermark.git
cd remove-watermark
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Автор

Rafael Mansurov  
Telegram: [@mansurov_rafael](https://t.me/mansurov_rafael)

## License

MIT — см. [`LICENSE`](LICENSE).
