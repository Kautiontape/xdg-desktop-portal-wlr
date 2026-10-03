#!/usr/bin/env python3
"""Exercise screencast restore_data against xdpw directly, with no chooser.

Talks to xdpw's impl interface (not the xdg-desktop-portal frontend) and starts a
session from restore_data, the way a client's follow-up session would. If the target
restores, Start returns immediately with a PipeWire stream. If it doesn't (unknown
output or toplevel, or a closed window), xdpw falls back to its chooser, so a picker
will appear on screen.

usage: restore-test.py window <ext-foreign-toplevel identifier>
       restore-test.py monitor <output name>

Identifiers are in xdpw's log at INFO level ("capturable toplevel: <id> ...").

Note: the returned node is registered with object.register=false, so generic
consumers such as gst pipewiresrc cannot attach to it by id. Real clients go through
the portal's OpenPipeWireRemote. This script only checks session setup and restore.
"""
import sys
import time

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

BUS = "org.freedesktop.impl.portal.desktop.wlr"
PATH = "/org/freedesktop/portal/desktop"
IFACE = "org.freedesktop.impl.portal.ScreenCast"

if len(sys.argv) != 3 or sys.argv[1] not in ("window", "monitor"):
    sys.exit(__doc__)
kind, ident = sys.argv[1], sys.argv[2]

tok = str(int(time.time() * 1000))
session = f"/org/freedesktop/portal/desktop/session/1_ktn/s{tok}"
conn = Gio.bus_get_sync(Gio.BusType.SESSION)


def call(method, args, timeout_ms=120000):
    return conn.call_sync(BUS, PATH, IFACE, method, args, None,
                          Gio.DBusCallFlags.NONE, timeout_ms, None).unpack()


def req(n):
    return f"/org/freedesktop/portal/desktop/request/1_ktn/r{tok}{n}"


key = "toplevel_identifier" if kind == "window" else "output_name"
restore = GLib.Variant("(suv)", ("wlroots", 1,
                                 GLib.Variant("a{sv}", {key: GLib.Variant("s", ident)})))

try:
    call("CreateSession", GLib.Variant("(oosa{sv})", (req(1), session, "", {})))
    code, _ = call("SelectSources", GLib.Variant("(oosa{sv})", (req(2), session, "", {
        "types": GLib.Variant("u", 2 if kind == "window" else 1),
        "persist_mode": GLib.Variant("u", 1),
        "restore_data": restore,
    })))
    print("SelectSources:", "ok" if code == 0 else f"response {code} (chooser cancelled)")
    if code != 0:
        sys.exit(1)
    t0 = time.monotonic()
    code, results = call("Start", GLib.Variant("(oossa{sv})", (req(3), session, "", "", {})))
    took = (time.monotonic() - t0) * 1000
    if code != 0:
        print(f"Start: response {code}")
        sys.exit(1)
    node = results["streams"][0][0]
    rd = results.get("restore_data")
    print(f"Start: ok in {took:.0f} ms, PipeWire node {node}")
    print("re-issued restore_data:", rd if rd else "none (persist_mode not honoured?)")
finally:
    try:
        conn.call_sync(BUS, session, "org.freedesktop.impl.portal.Session", "Close",
                       None, None, Gio.DBusCallFlags.NONE, 5000, None)
    except GLib.Error:
        pass
