#!/bin/bash
# Test chooser for xdpw (dmenu type): pick the stdin line containing the target in
# $XDG_RUNTIME_DIR/xdpw-test-target (a window identifier or "Monitor: NAME"). No target or
# no match -> print nothing, which xdpw treats as cancel. Never opens a UI.
list=$(cat)
target_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/xdpw-test-target"
[ -f "$target_file" ] || exit 0
target=$(cat "$target_file")
printf '%s\n' "$list" | grep -F -- "$target" | head -1
