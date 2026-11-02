# Device test plan

[Русский](DEVICE_TESTING_RU.md)

Back up existing saves and use a clean test profile to judge unlock boundaries. An installed variant with the same package/key is replaced; changing package does not migrate saves.

1. Install on an ARM64 Android device; check launch, rendering, audio, pause/resume, level entry/exit and saves after restart.
2. Compare the original preset's progression with the unmodified game.
3. With default fixes, check episode access and all 25 Ragnahog calendar levels offline, including an older save. Other episode progression and Ragnahog's three bonus/egg requirements must remain earned gates.
4. Check other Golden Eggs and star/feather thresholds before and after earning them.
5. In both quest interfaces, pressing the video-hint button should show the level prompt immediately. Ordinary quest objectives must still be required.
6. With coins, check one-time minimum top-up, preservation of higher balances, spending and restart. With cosmetics, equip Bird Wear and check unrelated quest progress.
7. With `alllevels`, verify local level/egg/bonus access; scores and stars should not be forged. Returning to a narrower build does not revoke saved grants.

Cloud downloads, online tournaments and unavailable server content are outside these fixes. Automated builds, mocked Lua tests and static audits do not replace these device checks.
