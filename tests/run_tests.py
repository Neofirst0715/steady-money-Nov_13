#!/usr/bin/env python3
"""Checks the tool against the answer tables and the hard cases.

    python3 tests/run_tests.py
"""
import csv
import datetime as dt
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import build, render, rules, make_third  # noqa: E402

TODAY = dt.date(2026, 11, 13)
passed, failed = 0, []


def check(name, ok, note=""):
    global passed
    if ok:
        passed += 1
        print("  ok    " + name)
    else:
        failed.append(name)
        print("  FAIL  " + name + ("  -> " + note if note else ""))


def run(folder):
    m = rules.evaluate(build.assemble(folder))
    out = tempfile.mkdtemp()
    files = render.write_all(m, out, TODAY)
    return m, {os.path.basename(f): open(f, encoding="utf-8").read()
               for f in files}


more_specific = []


def score(m, key):
    """Status and how to reach must match exactly. The reason must match
    too, except that where the key just says 'Coming and keeping up' the
    tool may give the agreed exception that keeps the person on track."""
    wrong = []
    for c in m["clients"]:
        k = key.get(c["id"]) or key.get(c["name"])
        got = (c["status"], c["why"], c["reach"])
        if k == got:
            continue
        if k and (k[0], k[2]) == (got[0], got[2]) and got[0] == "on track" \
                and k[1] == rules.WHY_OK:
            more_specific.append("%s: %s" % (c["name"], c["why"]))
            continue
        wrong.append("%s got %s, key %s" % (c["name"], got, k))
    return wrong


def load_key(path):
    out = {}
    for r in csv.DictReader(open(path)):
        out[r.get("client_id") or r["client_no"]] = (
            r.get("maya_says") or r["status"], r["why"],
                               r["how_to_reach"])
    return out


def text_of(page):
    page = re.sub(r"<style>.*?</style>", "", page, flags=re.S)
    return re.sub(r"<[^>]+>", " ", page)


agencies = {}
print("Answer tables")
for name, key in (("cole_street", load_key(os.path.join(
        HERE, "cole_street_marks.csv"))),
        ("bayfield", load_key(os.path.join(HERE, "bayfield_marks.csv")))):
    m, pages = run(os.path.join(ROOT, "samples", name))
    agencies[name] = (m, pages)
    wrong = score(m, key)
    check("%s: %d of %d clients match the marks" % (
        name, len(m["clients"]) - len(wrong), len(m["clients"])),
        not wrong, "; ".join(wrong))

third = tempfile.mkdtemp()
make_third.make(third)
m3, pages3 = run(third)
agencies["third_layout"] = (m3, pages3)
wrong = score(m3, make_third.KEY)
check("third layout: %d of %d clients match the key" % (
    len(m3["clients"]) - len(wrong), len(m3["clients"])), not wrong,
    "; ".join(wrong))

print("Must never happen")
for name, (m, pages) in agencies.items():
    sheets = " ".join(text_of(v) for k, v in pages.items()
                      if k.startswith("friday-sheet"))
    dnc = [c["name"] for c in m["clients"] if c["contact"]["dnc"]]
    check("%s: nobody who asked for no contact is on a Friday sheet (%d)" %
          (name, len(dnc)), dnc and not any(n in sheets for n in dnc))
    page = text_of(pages["renewal-page.html"])
    leaks = []
    for c in m["clients"]:
        parts = [c["name"]] + [p for p in c["name"].split() if len(p) >= 4]
        leaks += [p for p in parts if re.search(r"\b%s\b" % re.escape(p),
                                                page)]
        if c["phone"] and c["phone"] in page:
            leaks.append(c["phone"])
    for s in {c["counsellor"] for c in m["clients"]}:
        if s and s in page:
            leaks.append(s)
    check("%s: no name or phone number on the renewal page" % name,
          not leaks, ", ".join(leaks))
    s = m["summary"]
    check("%s: renewal page totals add up to everyone who started" % name,
          (s["stuck"] + s["stopped"] == s["started"]) and
          (s["scored"] + s["unknown"] == s["started"]))

print("Hard cases")
by = {c["name"]: c for c in agencies["cole_street"][0]["clients"]}
check("newest note beats the first-day column (mail -> call, evenings)",
      by["Nora Whynot"]["reach"] == "call" and "evenings only" in
      by["Nora Whynot"]["reach_detail"])
check("a preference that changed twice ends on the latest (text)",
      by["Anthony Comeau"]["reach"] == "text")
check("letter set after a dead number is marked not confirmed by client",
      "not confirmed by client" in by["Keith Fraser"]["reach_detail"])
check("letter asked for in person is the client's own",
      "not confirmed" not in by["Peter Wamboldt"]["reach_detail"])
check("first-day contact is labelled as not confirmed since",
      "not confirmed since" in by["Raymond Doucette"]["reach_detail"])
check("away with notice is not stalled", by["Sofia Reyes"]["status"] ==
      "on track")
check("diary on hold is not counted, and is flagged when it never ends",
      by["Bernard Sampson"]["status"] == "on track" and
      any("on hold" in f for f in by["Bernard Sampson"]["flags"]))
check("a week where homework wasn't set is not counted",
      by["Trevor Oickle"]["status"] == "on track")
check("two missed weeks need not be consecutive",
      by["Elizabeth Arsenault"]["status"] == "stalled")
check("two clients with the same first name are told apart by counsellor",
      by["Alex Corkum"]["missed"] == [2, 3] and
      by["Alex Theriault"]["missed"] == [1, 2, 3])
check("late counts as present", by["Aisha Rahman"]["last_seen"] == 4)
by = {c["name"]: c for c in agencies["bayfield"][0]["clients"]}
check("'not typed yet' is not counted as not handed in",
      by["Carol Ingram"]["status"] == "on track" and
      any("isn't entered yet" in f for f in by["Carol Ingram"]["flags"]))
by = {c["name"]: c for c in m3["clients"]}
check("a nickname in the notes finds the right client (Bill -> William)",
      by["William Carter"]["contact"]["channel"] == "email")
check("a first name that fits two clients is flagged, not guessed",
      by["Maria Santos"]["contact"]["by"] == "day one" and
      any("more than one fits" in i for i in m3["issues"]))
check("a dead number with no other way suggests nothing",
      by["Derek Shaw"].get("reach_unsure") and "Derek Shaw" in
      text_of(pages3["friday-sheet-priya-nair.html"]).split(
          "Your decision first")[1].split("Talk at the next session")[0])
check("contact wording the tool doesn't know is flagged",
      any("doesn't know" in f for f in by["Fiona Burke"]["flags"]))
check("a blank diary cell is 'not entered', not 'missed'",
      by["Colin Tate"]["missed"] == [])
check("a returned diary puts someone back on track, marked 'just back'",
      by["Yusuf Ali"]["status"] == "on track" and by["Yusuf Ali"]["just_back"])
check("one missed session is not stalled", by["Rita Gomez"]["status"] ==
      "on track")
check("'Excused' on the sheet counts as notice", by["Luis Mendes"]["status"]
      == "on track")
check("diary paused then back on: only weeks after it count",
      by["Tom Reid"]["missed"] == [3])

print("Same answers from other layouts (Cole Street rewritten)")
import make_variants  # noqa: E402
key = load_key(os.path.join(HERE, "cole_street_marks.csv"))
src = os.path.join(ROOT, "samples", "cole_street")
base = rules.evaluate(build.assemble(src))
for fn in make_variants.ALL:
    d = os.path.join(tempfile.mkdtemp(), "cole-street")
    fn(base, src, d)
    try:
        mv, _ = run(d)
        wrong = [w for w in score(mv, key)]
        check("%s: %d of %d" % (fn.__name__, len(mv["clients"]) - len(wrong),
                                len(mv["clients"])), not wrong,
              "; ".join(wrong[:4]))
        check("%s: agency name read from the file names" % fn.__name__,
              mv["agency"] == "Cole Street", mv["agency"])
    except build.CannotRead as ex:
        check("%s: could be read" % fn.__name__, False, str(ex)[:300])

print("Stops when it should")
d = os.path.join(tempfile.mkdtemp(), "x")
shutil.copytree(src, d, ignore=shutil.ignore_patterns("out", "*notes*"))
try:
    build.assemble(d)
    check("no notes file: stops and writes nothing", False)
except build.CannotRead:
    check("no notes file: stops and writes nothing", True)
open(os.path.join(d, "notes.txt"), "w").write("\n".join(
    "Entry %d ~ zq%d ~ saw the client and went over things" % (i, i)
    for i in range(150)))
try:
    build.assemble(d)
    check("notes it can't read: stops and writes nothing", False)
except build.CannotRead as ex:
    check("notes it can't read: stops and writes nothing",
          "couldn't be read" in str(ex))
import subprocess  # noqa: E402
z = os.path.join(tempfile.mkdtemp(), "bayfield-files")
shutil.make_archive(z, "zip", os.path.join(ROOT, "samples", "bayfield"),
                    ".", )
p = subprocess.run([sys.executable, os.path.join(ROOT, "run.py"), z + ".zip"],
                   capture_output=True, text=True)
lines = [l for l in p.stdout.splitlines() if l.strip()]
check("runs straight from a zip; prints agency and client count first",
      p.returncode == 0 and "Agency: Bayfield" in lines[1] and
      lines[2] == "Clients: 6", p.stdout[:200] + p.stderr[-300:])
res = open(os.path.join(z, "out", "results.csv")).read().splitlines()
check("results.csv has exactly the four asked-for columns",
      res[0] == "client_id,status,way_to_reach,why" and len(res) == 7)
allowed = {"call", "text", "paper", "do not contact"}
vals = set()
for name, (m, pages) in agencies.items():
    vals |= {c["reach"] for c in m["clients"]}
check("way_to_reach is always one of the four allowed values",
      vals <= allowed, str(vals))
page = text_of(agencies["bayfield"][1]["renewal-page.html"])
check("the one page says halfway view, started, took both checks, improved",
      all(w in page for w in ("halfway view", "Started", "Took both Money "
                              "Checks", "Improved", "points or more")))

print("No-contact wording")
for text in [
        "Asked us not to reach out at all between sessions.",
        "No calls, no texts, no mail. Will come in.",
        "Please do not contact between sessions.",
        "Doesn't want to be contacted at home.",
        "Wants no contact until the next session.",
        "Client asked me not to get in touch outside sessions.",
        "No calls, texts or letters please.",
        "Said to stop contacting her, she will come when she can.",
        "No follow-up between sessions, at their request."]:
    check("read as no contact: " + text, rules.read_note(text)["contact"]
          and rules.read_note(text)["contact"]["dnc"])
for text in ["No texts, call evenings OK.", "Own phone now. Text is fine.",
             "Good talk about the phone bill. She has a plan for it.",
             "Phone cut off. Letter only for now."]:
    k = rules.read_note(text)["contact"]
    check("not read as no contact: " + text, not (k and k["dnc"]))

print("Made-up agencies built to break it (tests/make_fake.py)")
import make_fake  # noqa: E402
for label, maker, fkey, judgment in (
        ("northgate", make_fake.make_northgate, make_fake.N_KEY,
         make_fake.N_JUDGMENT),
        ("harbour hill", make_fake.make_harbour, make_fake.H_KEY,
         make_fake.H_JUDGMENT)):
    d = os.path.join(tempfile.mkdtemp(), label.replace(" ", "-"))
    maker(d)
    try:
        mf, _ = run(d)
    except build.CannotRead as ex:
        check("%s: could be read" % label, False, str(ex)[:200])
        continue
    got = {c["id"]: (c["status"], c["reach"]) for c in mf["clients"]}
    clear = [k for k in fkey if k not in judgment]
    wrong = ["%s got %s, key %s" % (k, got.get(k), fkey[k][:2])
             for k in clear if got.get(k) != fkey[k][:2]]
    check("%s: %d of %d clear cases right (%d more are judgment calls)" % (
        label, len(clear) - len(wrong), len(clear), len(judgment)),
        not wrong, "; ".join(wrong))
    fatal = [k for k in fkey if fkey[k][1] == "do not contact"
             and got.get(k, ("", ""))[1] != "do not contact"]
    check("%s: every no-contact client comes out as do not contact" % label,
          not fatal, ", ".join(fatal))

print("Browser front end (app.py)")
import app  # noqa: E402
app.RUNS = tempfile.mkdtemp()
r1 = app.do_run({"sample": "bayfield"})
check("a sample run returns the agency, the clients and the six files",
      r1.get("agency") == "Bayfield" and r1["clients_n"] == 6 and
      "results.csv" in r1["files"] and "renewal-page.html" in r1["files"])
import base64  # noqa: E402
bad = app.do_run({"files": [{"name": "x.txt", "data": base64.b64encode(
    b"hello").decode()}]})
check("files it can't read: stopped, and nothing left over from the run "
      "before", "stopped" in bad and "clients" not in bad)
r2 = app.do_run({"path": os.path.join(ROOT, "samples", "cole_street")})
check("each run gets its own folder", r2["run"] != r1["run"] and
      r2["clients_n"] == 48)
check("no-contact clients carry no phone number to the page",
      all(not c["phone"] for c in r2["clients"] if c["dnc"]))

print("Review: confirm, edit, resolve (review.py)")
import review  # noqa: E402
review.STORE = tempfile.mkdtemp()
hd = os.path.join(tempfile.mkdtemp(), "harbour-hill")
make_fake.make_harbour(hd)
r0 = app.do_run({"path": hd})
it = next(i for i in r0["items"] if i["client_id"] == "H03")
no_name = app.do_review({"folder": hd, "action": "edit", "key": it["key"],
                         "client_id": "H03", "by": " ", "note": "x",
                         "status": "on track", "reach": "call"})
check("an edit with no reviewer name is refused", "error" in no_name)
no_note = app.do_review({"folder": hd, "action": "edit", "key": it["key"],
                         "client_id": "H03", "by": "Amy Stone", "note": "",
                         "status": "on track", "reach": "call"})
check("an edit with no note is refused", "error" in no_note)
r1 = app.do_review({"folder": hd, "action": "edit", "key": it["key"],
                    "client_id": "H03", "by": "Amy Stone",
                    "note": "Asked her: calls are fine.",
                    "status": "on track", "reach": "call"})
nina = next(c for c in r1["clients"] if c["id"] == "H03")
check("an edit changes the result and is worked out again",
      nina["reach"] == "call" and nina["edited"] and
      "Amy Stone" in nina["reach_detail"])
e = r1["review_log"][-1]
check("the record has who, when, before and after",
      e["by"] == "Amy Stone" and e["at"] and e["before"]["reach"] == "text"
      and e["after"]["reach"] == "call" and "review-log.csv" in r1["files"])
csv_text = open(os.path.join(r1["out"], "results.csv")).read()
check("the page's results.csv carries the correction",
      "H03,on track,call" in csv_text)
import subprocess as sp  # noqa: E402
cli_out = tempfile.mkdtemp()
sp.run([sys.executable, os.path.join(ROOT, "run.py"), hd, "--out", cli_out],
       capture_output=True, text=True)
check("the command-line run ignores corrections (files and rules only)",
      "H03,on track,text" in open(os.path.join(cli_out,
                                               "results.csv")).read())
r2 = app.do_review({"folder": hd, "action": "edit", "key": next(
    i["key"] for i in r1["items"] if i["client_id"] == "H16"),
    "client_id": "H16", "by": "Amy Stone", "note": "The note was Wendy's.",
    "status": "on track", "reach": "text"})
will = next(c for c in r2["clients"] if c["id"] == "H16")
sheet_txt = open(os.path.join(r2["out"], "friday-sheet-amy-stone.html")).read()
check("an edit can lift a wrongly placed do-not-contact, with a record",
      will["reach"] == "text" and not will["dnc"])
r3 = app.do_review({"folder": hd, "action": "reopen", "key": it["key"],
                    "client_id": "H03", "by": "Amy Stone"})
nina = next(c for c in r3["clients"] if c["id"] == "H03")
check("reopen puts the tool's own answer back and is recorded too",
      nina["reach"] == "text" and not nina["edited"] and
      r3["review_log"][-1]["action"] == "reopen")
k = next(i["key"] for i in r3["items"] if i["state"] == "open")
r4 = app.do_review({"folder": hd, "action": "confirm", "key": k,
                    "by": "Amy Stone"})
check("confirm takes an item off the open list without changing results",
      len([i for i in r4["items"] if i["state"] == "open"]) ==
      len([i for i in r3["items"] if i["state"] == "open"]) - 1)

print("Robustness")
tmp = tempfile.mkdtemp()
dst = os.path.join(tmp, "cole")
shutil.copytree(os.path.join(ROOT, "samples", "cole_street"), dst,
                ignore=shutil.ignore_patterns("out"))
shutil.copy(os.path.join(HERE, "cole_street_marks.csv"), dst)
open(os.path.join(dst, "readme.docx"), "w").write("x")
m, _ = run(dst)
check("a marked-up list and stray files in the folder are ignored",
      not score(m, load_key(os.path.join(HERE, "cole_street_marks.csv"))))
os.remove(os.path.join(dst, "cole-street-diaries.csv"))
m, _ = run(dst)
check("runs without a diary sheet and says so", any(
    "No diary sheet" in i for i in m["issues"]) and
    sum(1 for c in m["clients"] if c["status"] == "stalled") == 5)
a = run(os.path.join(ROOT, "samples", "bayfield"))[1]["results.csv"]
b = run(os.path.join(ROOT, "samples", "bayfield"))[1]["results.csv"]
check("two runs on the same files give the same results", a == b)

if more_specific:
    print("\nReason more specific than the marks (status and contact match):")
    for x in more_specific[:20]:
        print("  " + x)
print("\n%d passed, %d failed" % (passed, len(failed)))
sys.exit(1 if failed else 0)
