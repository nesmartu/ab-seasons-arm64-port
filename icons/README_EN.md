# Custom PNG icons

[Русский](README_RU.md)

`icons.custom=false` keeps original icons. With `true`, supply `icon.png` here as a common replacement, or mirror existing resource paths such as `res/drawable-hdpi/icon.png`. Exact overrides win over the common PNG. Only existing drawable/mipmap paths ending in `/icon.png` can be replaced; unknown paths fail. No new IDs or adaptive XML icons are created. `icons.directory` is relative to the corresponding project's root, or absolute.
