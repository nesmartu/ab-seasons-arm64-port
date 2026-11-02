# SelectableFixes

[English](README.md) · [Основной проект](../README_RU.md) · [Устройство фиксов](RESEARCH_RU.md)

Независимый патчер JSON/Lua оригинальных Android APK Angry Birds Seasons 6.6.2 / 6620. Создаёт **ARM32** APK, сохраняет исходные пакет/названия/DEX/движки и подписывает включённым публичным PEM-ключом разработки. Нужны Python 3.11+, стандартный `lzma` и `cryptography==50.0.2`; Android SDK/NDK, Java, Gradle и компилятор Lua не нужны.

Из корня репозитория:

```bash
python -m pip install -r SelectableFixes/requirements.txt
python SelectableFixes/build.py --input input/game.apk --out-dir standalone-dist
python SelectableFixes/verify.py --input input/game.apk --dir standalone-dist
```

Замените `input/game.apk` на свой оригинал 6.6.2. Без входа в командной строке `build_config.toml` ожидает `SelectableFixes/input/AngryBirdsSeasons_v6.6.2.apk`. Пути выбранного конфига патчера отсчитываются от папки этого конфига; поэтому готовые конфиги используют `../input/`, `../signing/`, `../dist/`. Пути командной строки отсчитываются от текущей папки. `--config` выбирает конфигурацию из `SelectableFixes/configs/`.

Дефолтные фиксы совпадают с основным проектом: эпизоды, Ragnahog и подсказки квестов включены; монеты, косметика и все уровни выключены. [Параметры и область действия](../docs/SETTINGS_RU.md) описывают флаги и совместимые псевдонимы. `[options].coins_amount` патчера задаёт однократный минимум монет; `[build]` — вход, папку результата, суффикс имени и пути ключа/сертификата. Суффикс меняет только имя файла. Параметров пакета и рендера основного сборщика в отдельном патчере нет.

```bash
# Пять сочетаний из одного оригинала:
python SelectableFixes/build.py --matrix --input input/game.apk
python SelectableFixes/verify.py --input input/game.apk
python SelectableFixes/check_reproducible.py --input input/game.apk
# Без фиксов и с каждым отдельным флагом:
python SelectableFixes/check_builds.py --input input/game.apk
```

`verify.py` проверяет границы ресурсов, сохранность DEX/ресурсов/движков, выбранные прототипы Lua, CRC/выравнивание ZIP, хеши/CMS v1 (через OpenSSL CLI при наличии), подпись v2 и отклонение повреждённого APK. JSON-аудит записывается в `reports/` рядом с результатами. Тестам поведения укажите `SEASONS_TEST_APK`, как в основной [инструкции проверки](../docs/VERIFICATION_RU.md). Эти проверки не являются тестированием игрового процесса на устройстве.

Выключенные флаги не отменяют патчи и прогресс. Для удаления широкого патча соберите из оригинала; уже записанные открытия останутся. Неподдерживаемые структуры ресурсов и изменённые метаданные патча вызывают ошибку вместо частичного результата. Используйте только 6.6.2; списка разрешённых хешей всего APK нет. В исходниках нет входных/выходных APK. Архив отдельного патчера: `python SelectableFixes/make_source_archive.py --out-dir /path/outside/source`.
