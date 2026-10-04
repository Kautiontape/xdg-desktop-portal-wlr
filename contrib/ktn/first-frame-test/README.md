# First-frame regression test

Checks that a client waiting for a *first* frame gets one from an idle source. This is the
case "screencast: deliver the first frame to consumers that start late" fixes. It uses
Electron's `desktopCapturer.getSources()`, which only resolves once Chromium has a thumbnail.

Run a throwaway xdpw with a chooser that answers without UI, then time `getSources`
against an **idle, visible** window. Before the fix, about 1 run in 3 timed out. After it,
every run resolves at Chromium's first one-second poll.

```sh
# 1. pick the target: a toplevel identifier (xdpw logs them at INFO) or "Monitor: NAME"
echo 5b39e25a4fb022da2b4170a9a7b02de8 > "$XDG_RUNTIME_DIR/xdpw-test-target"

# 2. replace the running xdpw with a test instance
printf '[screencast]\nchooser_type=dmenu\nchooser_cmd=%s\n' "$PWD/test-chooser.sh" > /tmp/xdpw-test.conf
systemctl --user stop xdg-desktop-portal-wlr
systemd-run --user --unit=xdpw-test -E XDPW_PERSIST_MODE=transient -E WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
    /path/to/build/xdg-desktop-portal-wlr -l TRACE -c /tmp/xdpw-test.conf -r

# 3. run it a few times; expect {"result":"OK","ms":~1000}
for i in $(seq 10); do FF_TYPES=window,screen FF_TIMEOUT_MS=5000 \
    electron --ozone-platform=wayland --use-gl=disabled . 2>/dev/null | grep '^{'; done

# 4. clean up
systemctl --user stop xdpw-test; rm "$XDG_RUNTIME_DIR/xdpw-test-target"
systemctl --user start xdg-desktop-portal-wlr
```

`gst-launch pipewiresrc` can't stand in for Electron here: xdpw's node has
`object.register=false`, so pipewiresrc cannot target it ("target not found").
