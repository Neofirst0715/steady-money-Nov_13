#!/usr/bin/env python3
"""Steady Money: read one agency's files and write the results file, the
Friday sheets and the one-page halfway view.

    python3 run.py <agency folder or .zip>

Outputs go into an 'out' folder beside the agency's files, so client
names stay with the agency. Nothing is sent anywhere; no network is used.
"""
import argparse
import datetime as dt
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build   # noqa: E402
import render  # noqa: E402
import rules   # noqa: E402


def unzip(path):
    dest = os.path.splitext(os.path.abspath(path))[0]
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            name = info.filename
            if name.startswith("__MACOSX") or os.path.basename(
                    name).startswith("."):
                continue
            target = os.path.abspath(os.path.join(dest, name))
            if not target.startswith(dest + os.sep):
                continue                      # never write outside the folder
            if info.is_dir():
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(z.read(info))
    return dest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder", help="the agency's folder, or a .zip of it")
    ap.add_argument("--out", help="where to write (default: <folder>/out)")
    ap.add_argument("--name", help="agency name, if the file names lack one")
    ap.add_argument("--today", help="date to print, YYYY-MM-DD")
    ap.add_argument("--without-notes", action="store_true",
                    help="run even if no notes can be read (not advised)")
    a = ap.parse_args(argv)
    folder = a.folder
    if os.path.isfile(folder) and folder.lower().endswith(".zip"):
        folder = unzip(folder)
        print("Unzipped to: %s" % folder)
    if not os.path.isdir(folder):
        sys.exit("Folder not found: %s" % folder)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    try:
        model = build.assemble(folder, a.name, a.without_notes)
    except build.CannotRead as e:
        print("\nSTOPPED. No results were written.\n\n%s\n" % e)
        sys.exit(2)
    cs = model["clients"]
    print("\nAgency: %s" % model["agency"])
    print("Clients: %d" % len(cs))

    rules.evaluate(model)
    out = a.out or os.path.join(folder, "out")
    made = render.write_all(model, out, today)
    s = model["summary"]
    print("Sessions read: 1 to %d" % model["sessions"][-1]["n"])
    print("-" * 78)
    print("%-9s %-9s %-15s %s" % ("client_id", "status", "way_to_reach",
                                  "why"))
    for c in cs:
        print("%-9s %-9s %-15s %s" % (c["id"][:9], c["status"], c["reach"],
                                      c["why_short"]))
    print("-" * 78)
    stalled = sum(1 for c in cs if c["status"] == "stalled")
    print("On track: %d   Stalled: %d   Do not contact: %d" % (
        len(cs) - stalled, stalled, sum(1 for c in cs if c["contact"]["dnc"])))
    print("Started: %d   Took both Money Checks: %s   Improved (up %d or "
          "more): %s" % (s["started"], s.get("scored", "not known"),
                         rules.BETTER_OFF_MIN_POINTS,
                         s.get("better", "not known")))
    n_flags = sum(1 for c in cs if c["flags"]) + len(model["issues"])
    print("To check: %d item(s), listed in check-list.html" % n_flags)
    print("\nWritten:")
    for p in made:
        print("  " + p)


if __name__ == "__main__":
    main()
