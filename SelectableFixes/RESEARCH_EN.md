# Patch implementation

[Русский](RESEARCH_RU.md)

Modules operate on the original game's encoded JSON and Lua 5.1 bytecode. `tools/codec.py` handles the AES/custom LZMA wrapper; `tools/lua_chunk.py` parses and writes Lua chunks. `fixes/common.py` shares one parsed context so multiple edits are encoded together.

| Flag | Actual scope |
|---|---|
| `unlock_all_episodes` | Only `scripts/settingsWrapper.lua/root.273` (`isEpisodeUnlocked`) |
| `unlock_ragnahog_levels` | Only `episodeRagnahog.manual_level_progression=false` and its first page's `all_levels_open=true` in `episodesLatest.json` |
| `unlock_all_levels` | Broad level/layout/access predicates; episode patch implied |
| `unlocked_all_with_coins` | Episode patch + one-time saved minimum coin balance |
| `quest_video` | Click paths in QuestLogFrame and QuestLog, immediately selecting the hint target |
| `cosmetics` | Bird Wear completion/access records for the 108 shipped catalogue items |

Ragnahog's `LSXmas2016Layout.isLevelOpen` (`seasons_layouts.lua/root.43`) checks `isGoldenEggUnlocked` before ordinary `LSXmasLayout` (`root.21`). Keeping these predicates intact preserves the three-star egg and two hidden eggs while opening 25 regular calendar levels. Without `unlock_all_levels`, ordinary `gamelogic.lua/root.158` and star/feather predicates remain original. Coins/cosmetics do not replace these gates.

Apply order: Ragnahog → quest → episodes → full levels → cosmetics → coins. `assets/seasons_selectable_fixes.json` stores patch metadata/hashes; conflicting resource changes or coin amounts are rejected. Compatible alias/metadata readers are retained; false flags preserve installed patches. Modules do not import another saved profile, DEX or native engine.

`research/lua_vm_check.py` and `lua51.py` support limited mocked behavior tests. `dex_reader.py` and `dex_semantic_diff.py` support optional APK comparisons. To regenerate before/after disassembly and original-entry fingerprints:

```bash
python SelectableFixes/research/reproduce.py --original input/game.apk
```

Optional `--unlocked`/`--money` inputs enable read-only comparisons; they are not required for builds. Generated `research/evidence/` describes all patches, including full level unlock, and is excluded from source archives. `fixes/logic_reference.lua` is explanatory; the Python modules produce the actual bytecode edits. See [verification](../docs/VERIFICATION_EN.md), [provenance](../PROVENANCE_EN.md) and the [device plan](../docs/DEVICE_TESTING_EN.md).
