[English](README_EN.md) · Русский
# Angry Birds Seasons — порт для ARM64
**Версии 6.6.2 и 4.1.1 · Android 8.0+ · ARM64**

Порт моей любимой игры из серии Angry Birds. Не нашёл ARM64-порт, поэтому решил ~~сделать~~ навайбкодить его сам, взяв за основу [порт AB: Star Wars II][star-wars-ii] и [порт Star Wars][star-wars] от MrEmpathy.

Здесь используется мост совместимости на базе [Dynarmic][dynarmic], который позволяет запускать оригинальный ARM32-движок игры на Android-устройствах с ARM64. Dynarmic перекомпилирует инструкции движка прямо во время работы, а мост обрабатывает нужные ему обращения к Android. Код и ресурсы игры берутся из исходного APK.

Большую часть сгенерированного ИИ-слопа я оставил как есть - пусть это будет как снимок того, как всё это заработало. Если хочется разобраться, то вся магия описана в Markdown-файлах здесь и в [репозитории порта SW II][star-wars-ii].

Ещё я попробовал тот же подход с одной из старых версий **4.1.1** - и, на удивление - это сработало. У данной версии мост слегка переделан, инструменты сборки и прочая информация об этом в папке 4.1.1.

Также, запилил несколько фиксов для игры (SelectedFixes) и применил их при сборке apk-файлов, такие как: открытие всех уровней эпизода Ragnahog и исправление квестов (подсказки в квестах теперь не требуют обязательного просмотра рекламы для их получения).

## Скачать

Смотрите [страницу релизов][releases-link] для скачивания.

**«Оригинал» означает версию без игровых модификаций.** Сам APK при этом всё равно адаптирован для ARM64.

| Вариант | Что включено | Скачать |
|---|---|---|
| **6.6.2 — Original** | Оригинальная игра, без изменений | [APK][apk-original-662]|
| **6.6.2 — Unlocked** | Открыты все эпизоды | [APK][apk-unlocked-662]|
| **6.6.2 — Unlocked + Coins** | Открыты все эпизоды + монеты на старте | [APK][apk-unlocked-coins-662]|
| **6.6.2 — Unlocked + Coins + Cosmetics** | Открыты все эпизоды + монеты на старте + открыты все косметические штучки | [APK][apk-unlocked-coins-cosmetics-662]|
| **4.1.1 — Original** | Оригинальная игра, без изменений | [APK][apk-original-411]|

## Источники APK
Для версии 6.6.2 я брал [этот APK с сайта archive.org][source-original-662], для 4.1.1 — [этот с uptodown][source-original-411].

### Скриншоты
Мне лень их добавлять, выглядит абсолютно так же:)

## Сборка
Для процесса сборки смотрите [гайд по сборке](BUILD_RU.md), подходит и для 4.1.1.

Инструменты сборки работают на **Linux x86_64** с **Python 3.11+** и **Java 17**.

## Благодарности
Огромное спасибо **[MrEmpathy][mrempathy]** за порты Star Wars и мост, на котором основан этот проект, а также **разработчикам [Dynarmic]** за рекомпилятор, благодаря которому такой подход вообще возможен.

Использованная здесь версия моста взята из [`angry-birds-star-wars-II-arm64`, коммит `18615db`][bridge-commit]. Полный список компонентов, версий и ссылок на исходники - в [PROVENANCE_RU.md](PROVENANCE_RU.md).

Пока занимался портом, наткнулся на еще один интересный проект - **[angry-birds-love2d][angry-birds-love2d]**. Если вам интересны порты Angry Birds или движок игры, загляните, он поддерживает Angry Birds Seasons и, вероятно, запускает его на компьютере!
На его основе я тоже сделал порт, но в процессе тестов словил несколько багов и пока отложил это дело. Возможно, выложу позже и эту версию.

Все права на игру принадлежат правообладателям.

Вроде всё.

[star-wars-ii]: https://github.com/MrEmpathy/angry-birds-star-wars-II-arm64
[star-wars]: https://github.com/MrEmpathy/angry-birds-starwars-hd-arm64
[dynarmic]: https://github.com/Vita3K/dynarmic
[releases-link]: https://github.com/nesmartu/ab-seasons-arm64-port/releases
[apk-original-662]: https://github.com/nesmartu/ab-seasons-arm64-port/releases
[apk-unlocked-662]: https://github.com/nesmartu/ab-seasons-arm64-port/releases
[apk-unlocked-coins-662]: https://github.com/nesmartu/ab-seasons-arm64-port/releases
[apk-unlocked-coins-cosmetics-662]: https://github.com/nesmartu/ab-seasons-arm64-port/releases
[apk-original-411]: https://github.com/nesmartu/ab-seasons-arm64-port/releases
[source-original-662]: https://archive.org/download/angry-birds-seasons-android_202605/Angry%20Birds%20Seasons%20v6.6.2.apk
[source-original-411]: https://angry-birds-seasons.en.uptodown.com/android/download/79023
[mrempathy]: https://github.com/MrEmpathy
[bridge-commit]: https://github.com/MrEmpathy/angry-birds-star-wars-II-arm64/commit/18615db1805fdf8ef3f93a8ba82608f1d206c1b7
[angry-birds-love2d]: https://github.com/romoney5/angry-birds-love2d
