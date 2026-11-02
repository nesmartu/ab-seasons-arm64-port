# Public ARM32 development key

[Русский](README_RU.md)

`test-key.pem` and `test-cert.pem` are an intentionally public RSA development pair for standalone patch outputs. They are separate from the final ARM64 port key and are not Rovio's certificate. Select another key/certificate via standalone `[build].key`/`cert` for private releases; do not commit private credentials. Patcher outputs retain the original package, so installing over a differently signed original APK is not an in-place update.
