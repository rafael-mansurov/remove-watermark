# remove_watermark.py

Локальный Python-скрипт для удаления белого текста и водяных знаков с фото через интерактивный редактор зоны.

## Сайт проекта

[https://rafael-mansurov.github.io/remove-watermark/](https://rafael-mansurov.github.io/remove-watermark/)

## Важно

Используйте скрипт только для изображений, которые принадлежат вам или для которых у вас есть явное разрешение на редактирование. Соблюдайте авторские права и условия использования контента.

## Возможности

- Пакетная обработка изображений в папке.
- Интерактивная настройка зоны удаления перед каждым фото.
- Настройка `Threshold` (яркость маски) и `Radius` (радиус inpainting) в реальном времени.
- Автосохранение результатов в папку `cleaned/`.
- Пропуск уже обработанных файлов (по умолчанию).

## Требования

- macOS
- Python 3.9+
- Пакеты из `requirements.txt`

## Установка

```bash
brew install python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Быстрый старт

```bash
python3 remove_watermark.py
```

После запуска откроется системный выбор папки (Finder).  
Выберите папку с фото, и скрипт начнет обработку.

Результаты сохраняются в:

```text
<выбранная_папка>/cleaned/
```

## Параметры CLI

```bash
python3 remove_watermark.py --help
```

Доступные аргументы:

- `-i, --input <path>` - путь к папке с изображениями.
- `--region X1 Y1 X2 Y2` - стартовая зона в долях от размера изображения (по умолчанию `0.45 0.88 1.0 1.0`).
- `--no-skip` - перезаписывать уже обработанные файлы.

Пример:

```bash
python3 remove_watermark.py -i ~/Pictures/cases --region 0.40 0.86 1.0 1.0
```

## Поддерживаемые форматы

`jpg`, `jpeg`, `png`, `bmp`, `tiff`, `tif`, `webp`

## Локальная разработка

```bash
git clone https://github.com/rafael-mansurov/remove-watermark.git
cd remove-watermark
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 remove_watermark.py
```

По умолчанию артефакты обработки (`cleaned/`) и служебные файлы Python исключены из git через `.gitignore`.

## Управление в редакторе

- Перетаскивание углов - изменение размера зоны.
- Перетаскивание внутри зоны - перемещение прямоугольника.
- `ENTER` или `SPACE` - обработать текущее фото.
- `S` или `N` - пропустить фото.
- `ESC` - завершить обработку.

## Как это работает

1. В выбранной зоне выделяются яркие пиксели (белый текст/водяной знак) через порог.
2. Маска расширяется (dilate), чтобы лучше захватить символы.
3. Применяется `cv2.inpaint(..., cv2.INPAINT_TELEA)` для восстановления фона.

## Ограничения

- Скрипт лучше всего работает для светлых/белых водяных знаков.
- Для сложных текстур иногда нужно вручную подбирать `Threshold` и `Radius`.
- Интерактивный выбор папки через Finder использует `osascript` (ориентировано на macOS).

## Автор

Rafael Mansurov  
Telegram: [@mansurov_rafael](https://t.me/mansurov_rafael)

## License

MIT — см. файл `LICENSE`.

