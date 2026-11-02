# Public development signing key

[Русский](README_RU.md)

`experiment1.p12` is an intentionally public development key, not a production secret. Alias: `abs662`; store/key password: `abs662-experiment`. The packager signs v2/v3 with this key and generates it if absent. Preserve it to update existing builds that use the same certificate. For a private release, configure your own key in `tools/package_apk.py` and keep it outside version control. This key is not Rovio's key.
