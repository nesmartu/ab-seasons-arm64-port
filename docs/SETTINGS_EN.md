# Build settings

[Русский](SETTINGS_RU.md) · [Build](../BUILD_EN.md)

`build_config.toml` is the default. `--config` selects another file. Main/4.1.1 icon paths resolve from their respective project roots, even when a config is elsewhere. The standalone patcher's paths resolve from the chosen config's directory. CLI paths resolve from the working directory. Boolean values must be TOML `true`/`false`.

| Key | Default / behavior |
|---|---|
| `app.preserve_original_package` | `false`; `true` takes the manifest package and overrides all custom/automatic suffixes |
| `app.package` | `com.rovio.angrybirdsseasons.port`; exact custom ID when preservation is off |
| `app.package_mode` | `version`; only used with preservation off and an empty custom package; alternative `base` |
| `app.package_base` | `com.rovio.seasonsport.unofficial`; automatic version digits go before `.unofficial` |
| `app.preserve_original_name` | `true`; preserve application/activity labels, including localized resources |
| `app.name` | `Angry Birds Seasons`; used only when name preservation is off |
| `icons.custom`, `icons.directory` | `false`, `icons`; [PNG layout](../icons/README_EN.md) |
| `bridge.render_height` | `1080`, range 0..8192; 0 uses device height |
| `bridge.max_fps` | `60`, range 0..1000; 0 disables the cap |
| `bridge.allow_network` | `false`; remove INTERNET, `true` retains it |
| `selectable_fixes.enabled` | `true`; tested only on 6.6.2; disable for other compatible engines |
| `selectable_fixes.append_fixed` | `false`; suffix only for automatic IDs, with enabled selected fixes |
| `selectable_fixes.coins_amount` | `1000000`, range 1..16000000 |
| `fixes.unlock_all_episodes` | `true`; episode access only |
| `fixes.unlock_ragnahog_levels` | `true`; 25 regular calendar levels, original egg/bonus gates |
| `fixes.quest_video` | `true`; button immediately reveals a quest level hint |
| `fixes.unlock_all_levels` | `false`; all shipped local level/egg/bonus gates, implies episode access |
| `fixes.unlocked_all_with_coins` | `false`; episode access + one-time minimum coin balance |
| `fixes.cosmetics` | `false`; all 108 shipped Bird Wear entries |

`unlocked_all_with_coins` does not enable full level unlock. Higher existing balances are kept; the saved grant marker prevents repeated grants, and spending remains normal. Quest objectives and other rewarded videos are not bypassed. False flags preserve existing input patches and saved grants. `enabled=false` or all flags false skips the patcher.

Per-file `[variants."game.apk"]` sections override only `[app]` keys and match the complete original filename. Package selection never infers unlock/money status from filenames. For separate installs, set explicit distinct IDs. `preserve_original_package=true` may conflict with an installed Rovio-signed APK because the port uses a different certificate. Saves are not automatically migrated between packages.

Compatibility aliases: `ragnahog` means `unlock_ragnahog_levels`; `unlocked_all=true` enables broad `unlock_all_levels`. Conflicting alias/canonical keys fail. Prefer the explicit canonical names. Alias handling exists for config compatibility, not as a default preset.

The `4.1.1/` config has no selectable-fix section, uses `.port411`, and defaults to render height 0. Other common options keep the meanings above.
