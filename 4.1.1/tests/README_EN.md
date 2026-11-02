# Configuration tests

[Русский](README_RU.md)

Run `python -m unittest discover -s tests -v` from this project's root. Tests cover config validation, original/custom labels and packages, per-file overrides and release artifact selection. Main project tests also cover fix defaults and `.fixed`. Fixtures are small binary manifests, not complete game APKs. See the repository's `docs/VERIFICATION_EN.md` for behavior and build checks.
