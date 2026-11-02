# Patch modules

[Русский](README_RU.md)

Each module's `apply(ctx, options)` edits only its selected resource/prototypes. Shared parsing/writing is in `common.py`; execution order and scope are described in [RESEARCH](../RESEARCH_EN.md). `unlock_all_levels` and `coins` imply the separate episode-access patch through the build router, not by calling another module. `logic_reference.lua` documents intent and is not compiled into the game.
