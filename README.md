English · [Русский](README_RU.md)
# Angry Birds Seasons ARM64 Port
**Versions 6.6.2 and 4.1.1 · Android 8.0+ · ARM64**

A port of my favorite game in the Angry Birds series. I couldn't find an ARM64 port, so I decided to ~~make~~ vibecode one myself, on the base of MrEmpathy's [AB: Star Wars II][star-wars-ii] and [AB: Star Wars] [star-wars] ports.

The port uses a compatibility bridge built around [Dynarmic][dynarmic] to run the original game's ARM32 engine on ARM64 Android devices. Dynarmic recompiles the engine's instructions at runtime, while the bridge handles the calls it needs to make to Android. The game code and resources come from the original APK.

I've left most of the AI-generated slop in place as a snapshot of how this thing came together. If you want to see how it works, the Markdown files in this repo and the [info in SW II Port repo][star-wars-ii] explain all the magic.

I tried the same approach with **4.1.1** - and, surprisingly, that worked too. It has its own bridge and build tools in 4.1.1 folder.

Also, I made some fixes for the game (SelectedFixes) and applied it to built apks, such as: unlocking Ragnarhog's episode levels and quest fix (hints in the quests shows immediately without watching the ads).

## Downloads
Check [releases page][releases-link] for downloads.

**“Original” means no gameplay mods.** The APK itself is still adapted for ARM64.

| Version | What's included | Downloads |
|---|---|---|
| **6.6.2 — Original** | Original game content, no gameplay mods | [APK][apk-original-662]|
| **6.6.2 — Unlocked** | All episodes unlocked | [APK][apk-unlocked-662]|
| **6.6.2 — Unlocked + Coins** | All episodes unlocked, plus extra coins | [APK][apk-unlocked-coins-662]|
| **6.6.2 — Unlocked + Coins + Cosmetics** | All episodes unlocked, plus extra coins, plus unlocked cosmetics | [APK][apk-unlocked-coins-cosmetics-662]|
| **4.1.1 — Original** | Original game content, no gameplay mods | [APK][apk-original-411]|

## Sources APK's
For the 6.6.2 version I used [this APK from archive.org][source-original-662], for 4.1.1 — [this from uptodown][source-original-411].

### Screenshots
I'm too lazy :P

## Building
For the full process, check the [build guide](BUILD_EN.md), same for 4.1.1.

The build tools run on **Linux x86_64** with **Python 3.11+** and **Java 17**.

## Thanks
A huge thanks to **[MrEmpathy][mrempathy]** for the Star Wars ports and the bridge this project builds on, and to the **[Dynarmic] developers** for the recompiler that makes this approach possible.

The bridge snapshot used here comes from [`angry-birds-star-wars-II-arm64` at commit `18615db`][bridge-commit]. For the full list of components, versions and source links, see [PROVENANCE_EN.md](PROVENANCE_EN.md).

While doing this, I came across **[angry-birds-love2d][angry-birds-love2d]** project. If you're interested in Angry Birds ports or its engine, give it a look: it supports Angry Birds Seasons and I guess it's possible to run it on the desktop!
I also made an Android port based on that project too, but ran into a few bugs and put it on hold, might upload it later.

All rights to the game belong to the rights holders.

That's all, birds!

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
