# olink.yazi

Open [olink](https://github.com/hasansezertasan/olink) targets (PyPI, issues,
CI, download stats, ...) for the project you are browsing in
[yazi](https://yazi-rs.github.io/), without leaving it.

The plugin is a thin wrapper: it finds the project root, shows a key menu of
the targets `olink list` reports, and shells out to the `olink` binary. No URL
logic lives here, so new olink targets work without a plugin update.

## Requirements

- The `olink` CLI (0.3.0 or newer) on `PATH`.
- Yazi 26.9.1 or newer (verified there; `ya.which` is needed).

## Install

```sh
ya pkg add hasansezertasan/olink:olink
```

## Keymap

Add to `~/.config/yazi/keymap.toml`:

```toml
[[mgr.prepend_keymap]]
on = ["g", "o"]
run = "plugin olink"
desc = "Open project links with olink"

[[mgr.prepend_keymap]]
on = ["g", "O"]
run = "plugin olink -- --copy"
desc = "Copy project link URL with olink"
```

The `--` before `--copy` matters: yazi only forwards arguments after it.

Press `g o` to pick a target and confirm opening it, `g O` to copy the URL
instead.

## Source

This directory lives in the
[olink repository](https://github.com/hasansezertasan/olink/tree/main/olink.yazi),
where `main.lua` is tested against live `olink` output. Send changes there.

## License

MIT
