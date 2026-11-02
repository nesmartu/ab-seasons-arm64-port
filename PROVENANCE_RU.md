# Компоненты и лицензионное происхождение

[English](PROVENANCE_EN.md)

| Компонент | Зафиксированный источник/версия | Расположение |
|---|---|---|
| Основа моста | [MrEmpathy/angry-birds-star-wars-II-arm64](https://github.com/MrEmpathy/angry-birds-star-wars-II-arm64), коммит `18615db1805fdf8ef3f93a8ba82608f1d206c1b7` | `bridge/`, адаптированные runtime/shims/JNI; отдельная адаптация в `4.1.1/` |
| Dynarmic | [Vita3K/dynarmic](https://github.com/Vita3K/dynarmic), коммит `c9298d3d39323032420e77ddda4d4266e758fa5e` | `third_party/dynarmic/`; локальные патчи в обоих `tools/patch_dynarmic.py`, защита SMT в build.py |
| Boost | 1.86.0, [архив проекта](https://archives.boost.io/release/1.86.0/source/boost_1_86_0.tar.gz) | `third_party/boost/`; Boost Software License 1.0 |
| Зависимости Dynarmic | fmt 10.1.0, mcl 0.1.12, oaknut 2.0.2, robin-map 0.6.2, xbyak 7.05, Zydis 4.0.0.0, Zycore 1.4.0.0, biscuit 0.14.0, Catch2 3.5.0 | `third_party/dynarmic/externals/`; уведомления сохранены |
| Вспомогательные исходники моста | dlmalloc 2.8.6; stb_sprintf 1.10 | `bridge/third_party/` и `4.1.1/bridge/third_party/`; уведомления внутри исходников |
| Android-инструменты | NDK r27d / 27.3.13750724; Build Tools 36.0.0 | скачиваются при подготовке; URL/SHA-256 в setup и `VERSIONS.lock.json` |
| Wheels инструментов | CMake 3.30.5; пакет Ninja 1.11.1.1 | `tools/wheels/`; включённые уведомления сохранены |
| Зависимость Python | cryptography 50.0.2 | закреплена в requirements; устанавливается отдельно |

Отдельные коммиты вложенных зависимостей не зафиксированы; содержимое закрепляет список хешей архива. Не все вложенные компоненты используются при ARM64-сборке. В документации основы моста также указан [angry-birds-starwars-hd-arm64](https://github.com/MrEmpathy/angry-birds-starwars-hd-arm64); его точный ранний коммит не зафиксирован.

В данных о происхождении исходников нет общей лицензии моста. Новая общая лицензия объединённому репозиторию не назначается. Сохраняйте лицензии компонентов и выясните недостающие разрешения перед распространением или сменой лицензии этих исходников. Игровой движок и ресурсы принадлежат соответствующим правообладателям; APK и готовые мосты со встроенным игровым движком не входят в исходный архив.

Мост транслирует ARMv7-код через Dynarmic и предоставляет Android/JNI/GLES/libc-обвязки. ARM32 runtime использует softfp/NEON, ARM64-часть — API 26/C++20/static libc++; аудит проверяет выравнивание сегментов ELF на 16 КиБ. Метки времени ZIP и SOURCE_DATE_EPOCH фиксируются скриптами; побайтовая повторяемость также зависит от инструментов и библиотек сжатия.

Включён публичный ключ разработки PKCS12/RSA-2048: alias `abs662`, пароль `abs662-experiment`; подписи v2/v3 включены, v1/v4 выключены. Это не закрытый производственный ключ. Отдельный ARM32-патчер использует другой публичный PEM-ключ/сертификат и подписи v1/v2. Ни один из них не является исходным ключом Rovio. См. `signing/README_RU.md`.

SelectableFixes меняет закодированные JSON/Lua-ресурсы без импорта чужого профиля и без подмены DEX/нативного движка. Вспомогательные инструменты исследования содержат парсеры Lua/DEX и ограниченную VM с подставными службами. Описание форматов: [Lua 5.1](https://www.lua.org/manual/5.1/manual.html), [DEX](https://source.android.com/docs/core/runtime/dalvik-bytecode), [APK v2](https://source.android.com/docs/security/features/apksigning/v2). Источник сведений о ключах ресурсов: [Angry_Birds_Decompilation](https://github.com/jooapa/Angry_Birds_Decompilation). Это ссылки о происхождении, а не скачиваемые зависимости сборки.
