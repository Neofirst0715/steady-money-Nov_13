"""Rewrites the Cole Street sample into other layouts, so the same 48
answers must come out whatever the files look like."""
import csv
import os
import shutil

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _copy(src, dst, skip=()):
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        if f.endswith((".csv", ".txt")) and not any(s in f for s in skip):
            shutil.copy(os.path.join(src, f), dst)


def _entries(model):
    out = []
    for c in model["clients"]:
        for d, text in c["notes"]:
            out.append((d, c, text))
    out.sort(key=lambda x: (x[0], x[1]["id"]))
    return out


def labels_dayfirst(model, src, dst):
    """Client blocks with 'Client:' labels and 13/10/2026 dates."""
    _copy(src, dst, skip=("notes",))
    with open(os.path.join(dst, "cole-street-case-notes.txt"), "w") as f:
        f.write("CASE NOTES\n\n")
        for c in model["clients"]:
            f.write("Client: %s\nCounsellor: %s\n" % (c["name"],
                                                      c["counsellor"]))
            for d, text in c["notes"]:
                f.write("%s: %s\n" % (d.strftime("%d/%m/%Y"), text))
            f.write("\n")


def dashes_initials(model, src, dst):
    """'Tue 13 Oct — Doucette, R. — MO — text', no year on the dates."""
    _copy(src, dst, skip=("notes",))
    with open(os.path.join(dst, "cole-street-notes.md"), "w") as f:
        f.write("# Session notes, fall 2026 group\n\n")
        for d, c, text in _entries(model):
            first, last = c["name"].split()[0], c["name"].split()[-1]
            ini = "".join(w[0] for w in c["counsellor"].split())
            f.write("- %s %d %s — %s, %s. — %s — %s\n" % (
                DAYS[d.weekday()], d.day, d.strftime("%b"), last, first[0],
                ini, text))


def session_ids(model, src, dst):
    """'S1 | C-1100 | text': session numbers and client numbers only."""
    _copy(src, dst, skip=("notes",))
    n_of = {s["date"]: s["n"] for s in model["sessions"]}
    with open(os.path.join(dst, "cole-street-notes.txt"), "w") as f:
        for d, c, text in _entries(model):
            f.write("S%d | %s | %s\n" % (n_of[d], c["id"], text))


def date_blocks(model, src, dst):
    """A date heading, then 'Raymond D. (Maya)' on one line and the note
    on the next."""
    _copy(src, dst, skip=("notes",))
    with open(os.path.join(dst, "cole-street-notes.txt"), "w") as f:
        last = None
        for d, c, text in _entries(model):
            if d != last:
                f.write("\n=== %s ===\n" % d.strftime("%B %d, %Y"))
                last = d
            f.write("%s %s. (%s)\n    %s\n" % (
                c["name"].split()[0], c["name"].split()[-1][0],
                c["counsellor"].split()[0], text))


def other_sheets(model, src, dst):
    """Different marks, headings, score and contact wording; diaries keyed
    by client number with 'Week 1' labels."""
    _copy(src, dst, skip=("attendance", "diaries"))
    att = list(csv.reader(open(os.path.join(
        src, "cole-street-attendance.csv"))))
    word = {"text": "Text message", "sms": "Text message", "call":
            "Phone call", "phone": "Phone call", "mail": "Letter",
            "letter": "Letter"}
    with open(os.path.join(dst, "cole-street-register.csv"), "w",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ref", "Participant name", "Worker", "Mobile",
                    "Reach me by", "Wk 1", "Wk 2", "Wk 3", "Wk 4",
                    "MC start", "MC mid"])
        for r in att[1:]:
            marks = []
            for v in r[5:9]:
                v = v.lower()
                marks.append("Late" if v == "late" else "Yes" if v in (
                    "p", "present") else "No")
            w.writerow(r[:4] + [word[r[4].lower()]] + marks +
                       ["%s/25" % x if x else "" for x in r[9:11]])
    by_name = {}
    for c in model["clients"]:
        key = "%s %s." % (c["name"].split()[0], c["name"].split()[-1][0])
        by_name[(key, c["counsellor"])] = c["id"]
    rows = list(csv.DictReader(open(os.path.join(
        src, "cole-street-diaries.csv"))))
    with open(os.path.join(dst, "cole-street-homework.csv"), "w",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ref", "Week", "Returned?", "Days"])
        for r in rows:
            w.writerow([by_name[(r["client"], r["counsellor"])],
                        "Week %s" % r["week"],
                        "Y" if r["handed_in"] == "yes" else "N",
                        r["days_filled"]])


ALL = [labels_dayfirst, dashes_initials, session_ids, date_blocks,
       other_sheets]
