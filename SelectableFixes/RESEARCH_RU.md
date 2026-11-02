# Реализация фиксов

[English](RESEARCH_EN.md)

Модули работают с закодированными JSON и байткодом Lua 5.1 оригинальной игры. `tools/codec.py` обрабатывает AES/нестандартную LZMA-обёртку; `tools/lua_chunk.py` читает и записывает чанки Lua. `fixes/common.py` использует общий разобранный контекст и кодирует несколько правок вместе.

| Флаг | Фактическая область |
|---|---|
| `unlock_all_episodes` | Только `scripts/settingsWrapper.lua/root.273` (`isEpisodeUnlocked`) |
| `unlock_ragnahog_levels` | Только `episodeRagnahog.manual_level_progression=false` и `all_levels_open=true` первой страницы в `episodesLatest.json` |
| `unlock_all_levels` | Широкие проверки доступа к уровням/раскладкам; включает патч эпизодов |
| `unlocked_all_with_coins` | Патч эпизодов + однократный минимум монет с маркером в сохранении |
| `quest_video` | Обработка нажатия в QuestLogFrame и QuestLog с немедленным выбором цели подсказки |
| `cosmetics` | Записи выполнения/доступа Bird Wear для 108 включённых предметов |

`LSXmas2016Layout.isLevelOpen` Ragnahog (`seasons_layouts.lua/root.43`) проверяет `isGoldenEggUnlocked` перед обычной проверкой `LSXmasLayout` (`root.21`). Сохранение этих функций оставляет условия яйца за три звезды и двух скрытых яиц при открытых 25 календарных уровнях. Без `unlock_all_levels` обычная `gamelogic.lua/root.158` и проверки звёзд/перьев остаются исходными. Монеты/косметика эти ограничения не подменяют.

Порядок: Ragnahog → квесты → эпизоды → все уровни → косметика → монеты. `assets/seasons_selectable_fixes.json` хранит метаданные и хеши патча; конфликтующие изменения ресурсов или суммы монет отклоняются. Сохранено чтение совместимых псевдонимов/метаданных; выключенные флаги оставляют существующие патчи. Модули не импортируют чужое сохранение, DEX или движок.

`research/lua_vm_check.py` и `lua51.py` обеспечивают ограниченные тесты с подставными службами. `dex_reader.py` и `dex_semantic_diff.py` нужны для необязательных сравнений APK. Повторное получение дизассемблирования до/после и хешей исходных записей:

```bash
python SelectableFixes/research/reproduce.py --original input/game.apk
```

Необязательные `--unlocked`/`--money` включают сравнение без изменений входов; для сборки не нужны. Генерируемая `research/evidence/` описывает все патчи, включая полное открытие, и не входит в архивы исходников. `fixes/logic_reference.lua` служит пояснением; фактические правки байткода создают Python-модули. См. [проверки](../docs/VERIFICATION_RU.md), [происхождение](../PROVENANCE_RU.md) и [план устройства](../docs/DEVICE_TESTING_RU.md).
