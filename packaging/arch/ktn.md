---
package: xdg-desktop-portal-wlr-ktn
summary: Screen sharing on sway and other wlroots compositors that asks once, even for single windows, and starts without waiting for the window to change
upstream: https://github.com/emersion/xdg-desktop-portal-wlr
retire_when: An upstream release restores window shares from restore_data (toplevel_identifier) and delivers the first frame to late-starting consumers; checked by hand. Both patches to be offered upstream (the first against issue #170).
---
## What it is

The standard xdg-desktop-portal backend for wlroots compositors such as sway, with two fixes:

- it remembers which **window** you chose to share, the same way it already remembers monitors;
- the **first frame** of a share actually reaches the app, even when the window is idle.

## Why it exists

Chromium and Electron apps (Discord clients like Vesktop, browsers, Slack) open a second portal
session when a share actually starts, and another whenever the stream's quality changes. They pass
a restore token from the first session so you aren't asked again. Stock xdpw only issues those
tokens for monitors. Sharing a single window therefore pops the source picker two or three times,
and backing out of any of them kills the share.

Separately, xdpw sends the first frame the instant a share starts, before the app's side of the
PipeWire connection is necessarily ready, and then waits for the window to change before sending
anything else. With an idle window, the app sits waiting: Vesktop's Go Live dialog doesn't appear
until you touch the shared window. In testing this happened about one share in three.

## How it differs from upstream

- Restore tokens carry a `toplevel_identifier` for window shares, alongside the existing
  `output_name` for monitors. Restored sessions re-issue it, so capture restarts chain-restore.
- A window is only restored when the app asked for windows. A closed or hidden window falls back to
  the picker.
- After a share starts, PipeWire's processing cycle is re-run a few times over about half a second,
  so a first frame that arrived before the app was ready still gets delivered. Measured: 5 of 15
  idle-window shares missed it before, 0 of 15 after.
- Fixes a crash: a token without `output_name` made stock xdpw `strcmp` a NULL pointer.
- Ships `/usr/lib/systemd/user/xdg-desktop-portal-wlr.service.d/ktn-persist.conf`, which sets
  `XDPW_PERSIST_MODE=transient`. Without it xdpw issues no restore tokens at all. Transient means a
  token only lives as long as the app that's sharing.
