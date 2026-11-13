"""Join an agency's files into one record per client."""
import collections
import datetime as dt
import os
import re

import read
from match import Roster, STOP


def _digits(h):
    m = re.search(r"(\d+)", h)
    return int(m.group(1)) if m else None


def _pick_attendance(tables, log):
    out = []
    for t in tables:
        kind, cols = read.classify_table(t, t["file"])
        t["kind"], t["cols"] = kind, cols
        if kind == "attendance":
            out.append(t)
    return out


def _clients_from(t, log, issues):
    cols = t["cols"]
    n = len(t["rows"])
    people = [c for c in cols if c["kind"] == "person"]
    name_c = max(people, key=lambda c: c["distinct"])
    # first name and surname may be in two columns
    first_c = last_c = None
    for c in people:
        if re.search(r"first|given|fore", c["hl"]):
            first_c = c
        elif re.search(r"last|sur|family", c["hl"]):
            last_c = c
    if not (first_c and last_c):
        first_c = last_c = None
        singles = [c for c in people if c["filled"] >= 0.9 * n
                   and c["distinct"] > max(4, n // 3) and all(
                       " " not in v for v in read._col(t, c["j"]))]
        if len(singles) == 2 and not any(
                " " in v for v in read._col(t, name_c["j"])):
            first_c, last_c = singles     # no hint in the headings: as written
    staff_cs = [c for c in people if c is not name_c
                and c not in (first_c, last_c)
                and c["distinct"] <= max(4, n // 3)]
    staff_c = staff_cs[0] if staff_cs else None
    id_cs = [c for c in cols if c["kind"] == "id"]
    phone_cs = [c for c in cols if c["kind"] == "phone"]
    chan_cs = [c for c in cols if c["kind"] == "channel"]
    sess_cs = [c for c in cols if c["kind"] == "attword"]
    check_cs = []
    for c in cols:
        if c["kind"] != "number":
            continue
        vals = [v for v in read._col(t, c["j"]) if v]
        if vals and all(5 <= read.intval(v) <= 25 for v in vals):
            check_cs.append(c)
    held = [c for c in sess_cs if c["filled"] > 0]

    log.append("%s: read as the attendance sheet (%d clients)" %
               (t["file"], n))
    if first_c:
        log.append("  client names: columns '%s' and '%s' joined" % (
            first_c["header"], last_c["header"]))
    else:
        log.append("  client names: column '%s'" % name_c["header"])
    log.append("  counsellor: %s" % ("column '%s'" % staff_c["header"]
                                     if staff_c else "no column found"))
    log.append("  client number: %s" % ("column '%s'" % id_cs[0]["header"]
                                        if id_cs else "none, row order used"))
    log.append("  first-day contact: %s" % (
        "column '%s'" % chan_cs[0]["header"] if chan_cs else "no column found"))
    log.append("  sessions: %s" % ", ".join("'%s'" % c["header"]
                                            for c in held))
    log.append("  Money Check scores: %s" % (", ".join(
        "'%s'" % c["header"] for c in check_cs) or "no columns found"))
    if not check_cs:
        issues.append("No Money Check columns were found, so the renewal "
                      "page can't show score changes.")
    if not chan_cs:
        issues.append("No first-day contact column was found.")

    nums = [_digits(c["header"]) for c in held]
    use_nums = all(x is not None for x in nums) and nums == sorted(set(nums))
    sessions = [{"n": (nums[i] if use_nums else i + 1), "header": c["header"],
                 "j": c["j"], "date": None} for i, c in enumerate(held)]
    checks = [{"header": c["header"], "n": _digits(c["header"]), "j": c["j"]}
              for c in check_cs]

    clients = []
    for ri, r in enumerate(t["rows"]):
        if first_c:
            name = ("%s %s" % (r[first_c["j"]], r[last_c["j"]])).strip()
        else:
            name = r[name_c["j"]]
            m = re.fullmatch(r"([^,]+),\s*(.+)", name)
            if m:                       # "SURNAME, First" -> "First Surname"
                name = "%s %s" % (m.group(2), m.group(1))
        if name.isupper() or re.search(r"\b[A-Z]{3,}\b", name):
            name = " ".join(w.capitalize() if w.isupper() else w
                            for w in name.split())
        if not name:
            continue
        c = {
            "id": r[id_cs[0]["j"]] if id_cs else "row %d" % (ri + 1),
            "name": name,
            "counsellor": r[staff_c["j"]] if staff_c else "",
            "phone": r[phone_cs[0]["j"]] if phone_cs else "",
            "day_one_raw": r[chan_cs[0]["j"]] if chan_cs else "",
            "att": {}, "checks": [], "notes": [], "diary": {}, "flags": [],
        }
        c["day_one"] = read.channel_of(c["day_one_raw"])
        if c["day_one_raw"] and not c["day_one"]:
            c["flags"].append("First-day contact '%s' isn't a word the tool "
                              "knows." % c["day_one_raw"])
        for s in sessions:
            raw = r[s["j"]]
            state, late = read.attendance_of(raw)
            if state is None:
                c["flags"].append("Attendance mark '%s' for %s isn't a word "
                                  "the tool knows; treated as no record." %
                                  (raw, s["header"]))
                state = ""
            c["att"][s["n"]] = {"state": state, "late": late, "raw": raw}
        for k in checks:
            v = r[k["j"]]
            c["checks"].append(read.intval(v) if v else None)
        clients.append(c)
    states = [a["state"] for c in clients for a in c["att"].values()]
    if "" in states and "absent" not in states and "excused" not in states:
        for c in clients:
            for a in c["att"].values():
                if a["state"] == "":
                    a["state"] = "absent"
        log.append("  the sheet never writes an absent mark, so a blank in a "
                   "session column is read as absent")
        issues.append("Blank attendance cells were read as absent, because "
                      "the sheet has no absent marks at all.")
    return clients, sessions, checks


# ------------------------------------------------------------- notes

_SEP = re.compile(r"\s[\-\u2013\u2014|]\s|\t|\s{3,}")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")
_SESS = re.compile(r"\b(?:s|sess|session|wk|week|mtg|meeting|class)\.?\s*#?"
                   r"(\d{1,2})\b", re.I)
_NUMDATE = re.compile(r"(?<![\d/.\-])(\d{1,2})[/.\-](\d{1,2})"
                      r"(?:[/.\-]((?:20)?\d\d))?(?![\d])")


def _mask(line, spans):
    chars = list(line)
    for _, s, e in spans:
        for i in range(s, e):
            chars[i] = "\x01"       # not a space: keeps separators intact
    return "".join(chars)


def _who(head, roster, ctx):
    """Find the counsellor and client named in a line's heading.
    -> (staff or None, client or None, how)"""
    return _who_full(head, roster, ctx)[:3]


def _who_full(head, roster, ctx):
    """As _who, plus the words in the heading that are not part of a name,
    a counsellor or a label. A real heading has none left over."""
    toks = _TOKEN.findall(head)
    words = [t for t in toks if re.fullmatch(r"[A-Za-z'\-]+", t)
             and t.lower() not in STOP]
    for t in toks:
        if t.lower() in roster.by_id:
            left = [w for w in words if w.lower() not in _LABELS
                    and w.lower() != t.lower() and not roster.staff_for(w)]
            return None, roster.by_id[t.lower()], "exact", left
    staff_hits = {}
    for w in words:
        s = roster.staff_for(w)
        if len(s) == 1:
            staff_hits[w] = s[0]
    staff = list(staff_hits.values())[0] if staff_hits else None

    def best(ws, need_plain=False):
        top, who, used = 0, {}, []
        for size in (2, 1):
            for i in range(len(ws) - size + 1):
                win = ws[i:i + size]
                if need_plain and all(w in staff_hits for w in win):
                    continue
                sc, cands = roster.candidates(" ".join(win))
                if sc > top:
                    top, who, used = sc, {c["id"]: c for c in cands}, win
                elif sc and sc == top:
                    who.update({c["id"]: c for c in cands})
        return top, list(who.values()), used

    top, who, used = best([w for w in words if w not in staff_hits])
    if not who and staff_hits:
        # a client's own name can look like a counsellor's ("Fraser, K.")
        top, who, used = best(words, need_plain=True)
    if len(who) > 1:
        want = set(staff_hits.values()) or (
            {ctx["counsellor"]} if ctx.get("counsellor") else set())
        narrowed = [c for c in who if c["counsellor"] in want]
        if narrowed:
            who = narrowed
    left = [w for w in words if w not in used and w not in staff_hits
            and w.lower() not in _LABELS]
    ctx["_cands"] = who
    if len(who) == 1:
        return staff, who[0], "exact", left
    return staff, None, ("several" if who else "none"), left


def _set_dayfirst(lines, log, issues):
    """Decide whether 03/04 means 3 April or March 4, from all the notes."""
    pairs = []
    for _, l in lines:
        if re.search(r"\b20\d\d[-/.]\d{1,2}[-/.]\d{1,2}\b", l):
            continue
        for m in _NUMDATE.finditer(l[:40]):
            pairs.append((int(m.group(1)), int(m.group(2))))
    read.DAYFIRST = False
    if not pairs:
        return
    if any(a > 12 for a, b in pairs):
        read.DAYFIRST = True
    elif any(b > 12 for a, b in pairs):
        read.DAYFIRST = False
    else:
        def weekly(dayfirst):
            ds = set()
            for a, b in pairs:
                try:
                    ds.add(dt.date(2001, a if not dayfirst else b,
                                   b if not dayfirst else a))
                except ValueError:
                    pass
            ds = sorted(ds)
            return sum(1 for x, y in zip(ds, ds[1:])
                       if (y - x).days % 7 == 0)
        read.DAYFIRST = weekly(True) > weekly(False)
        issues.append("Dates in the notes could be day-first or month-first. "
                      "They were read %s-first because that gives weekly "
                      "sessions." % ("day" if read.DAYFIRST else "month"))
    log.append("  dates in the notes read %s-first" %
               ("day" if read.DAYFIRST else "month"))


_LABELS = set("""client clients name participant member counsellor
counselor worker staff coach advisor adviser date session week notes note
when who with by""".split())


def _parse_note_lines(lines, roster, year, log, issues):
    """lines: list of (source, text). -> list of [client, when, text] and
    the number of lines that looked like notes but couldn't be used.
    'when' is a date, or a session number when the notes give no dates."""
    out, ctx, unused = [], {}, 0

    def when_in(text, spans, lo, hi):
        ds = [d for d, s, e in spans if lo <= s < hi]
        if ds:
            return ds[0]
        m = _SESS.search(text[lo:hi])
        return int(m.group(1)) if m else None

    def is_meta(line, masked, spans, lo, hi):
        """Is this piece only a date, a session number, names or a label?"""
        piece = masked[lo:hi]
        words = [w for w in _TOKEN.findall(piece)]
        if len(line[lo:hi].strip()) > 45 or len(words) > 6:
            return False
        if when_in(line, spans, lo, hi) is not None and len(words) <= 3:
            return True
        staff, client, how, left = _who_full(piece, roster, {})
        if left:
            return False            # ordinary words: this is text
        if client or how == "several" or staff:
            return True
        return bool(words) and when_in(line, spans, lo, hi) is not None

    def split(line, masked, spans):
        """-> (head_end, body_start) or 'header' or None."""
        seps = list(_SEP.finditer(masked))
        starts = [0] + [m.end() for m in seps]
        ends = [m.start() for m in seps] + [len(masked)]
        k = 0
        while k < len(starts) and is_meta(line, masked, spans, starts[k],
                                          ends[k]):
            k += 1
        if k == len(starts):
            return "header"
        # the first piece that isn't meta may still open "Name: text"
        j = masked.find(":", starts[k], ends[k])
        if j > 0 and (is_meta(line, masked, spans, starts[k], j) or
                      masked[starts[k]:j].strip().lower() in _LABELS):
            rest = line[j + 1:].strip()
            if masked[starts[k]:j].strip().lower() in _LABELS or (
                    len(rest) <= 45 and is_meta(
                        line, masked, spans, j + 1, len(masked))):
                return "header"
            return j, j + 1
        if k > 0:
            return starts[k], starts[k]
        return None

    for src, raw in lines:
        line = re.sub(r"^[\s\-*\u2022#>|]+", "", raw).rstrip(" |").strip()
        if not line or not re.search(r"[A-Za-z0-9]", line):
            continue
        spans = read.find_dates(line, year)
        masked = _mask(line, spans)
        cut = split(line, masked, spans)

        if cut == "header":
            staff, client, how = _who(masked, roster, ctx)
            when = when_in(line, spans, 0, len(line))
            if when is not None:
                ctx["when"] = when
            if staff:
                ctx["counsellor"] = staff
            if client:
                ctx["client"] = client
            ctx["open"] = bool(ctx.get("client") and
                               ctx.get("when") is not None)
            continue

        if cut is not None:
            head, body = masked[:cut[0]], line[cut[1]:].strip()
            staff, client, how = _who(head, roster, ctx)
            when = when_in(line, spans, 0, cut[0])
            if client is None and how == "none" and ctx.get("client"):
                client = ctx["client"]      # "13 Oct: text" under a heading
            if when is None:
                when = ctx.get("when")
            if client is None:
                unused += 1
                if how == "several" and rules_dnc(body or ""):
                    for cand in ctx.get("_cands", []):
                        cand["force_dnc"] = when or True
                        cand["flags"].append(
                            "A note asking for no contact fits more than "
                            "one client, so each is treated as do not "
                            "contact until someone checks: \"%s\"" %
                            raw.strip()[:90])
                if how == "none" and rules_dnc(body or ""):
                    issues.insert(0, "IMPORTANT: a note that asks for no "
                                  "contact couldn't be matched to any "
                                  "client. Find out who it is before using "
                                  "any Friday sheet: \"%s\"" %
                                  raw.strip()[:120])
                issues.append(
                    "A note couldn't be matched to one client (%s): "
                    "\"%s\"" % ("more than one fits" if how == "several"
                                 else "no name found", raw.strip()[:90]))
            elif when is None:
                unused += 1
                issues.append("A note for %s has no date and wasn't used: "
                              "\"%s\"" % (client["name"], raw.strip()[:90]))
            elif body:
                out.append([client, when, body])
                ctx["open"] = False
            continue

        # plain text with no heading: belongs to the heading above it
        if ctx.get("open"):
            out.append([ctx["client"], ctx["when"], line])
            ctx["open"] = False
        elif out and ctx.get("client") is out[-1][0]:
            out[-1][2] += " " + line
        elif out and not ctx.get("client"):
            out[-1][2] += " " + line
        else:
            unused += 1
    return out, unused


def _guess_year(texts):
    years = collections.Counter()
    for t in texts:
        for m in re.finditer(r"\b(20\d\d)\b", t):
            years[int(m.group(1))] += 1
    return years.most_common(1)[0][0] if years else dt.date.today().year


# ------------------------------------------------------------- diaries

def _who_cols(t, roster):
    """Which column names the client (by name or number) and which the
    counsellor: the ones whose cells resolve best."""
    best, name_c = -1, None
    for c in t["cols"]:
        if c["kind"] not in ("person", "id", "other"):
            continue
        vals = [v for v in read._col(t, c["j"]) if v]
        hit = sum(1 for v in vals if roster.find(v)[0] or
                  roster.find(v)[1] == "several")
        if vals and hit / float(len(vals)) > best:
            best, name_c = hit / float(len(vals)), c
    staff_c = None
    for c in t["cols"]:
        if c is name_c or c["kind"] != "person":
            continue
        vals = [v for v in read._col(t, c["j"]) if v]
        if vals and sum(1 for v in vals if roster.staff_for(v)) >= \
                0.8 * len(vals):
            staff_c = c
    return name_c, staff_c


def _diary_long(t, roster, log, issues):
    cols = t["cols"]
    n = len(t["rows"])
    name_c, staff_c = _who_cols(t, roster)
    numbers = [c for c in cols if c["kind"] == "number"]
    week_c = next(c for c in numbers if c["filled"] == n and c["distinct"] < n)
    attw = [c for c in cols if c["kind"] == "attword"]
    hand_c = attw[0] if attw else None
    days_c = None
    for c in numbers:
        if c is week_c:
            continue
        vals = [v for v in read._col(t, c["j"]) if v]
        if vals and all(0 <= read.intval(v) <= 7 for v in vals):
            days_c = c
            break
    log.append("%s: read as the diary sheet (%d rows)" % (t["file"], n))
    log.append("  client: '%s'; week: '%s'; handed in: %s; days filled: %s" % (
        name_c["header"], week_c["header"],
        "'%s'" % hand_c["header"] if hand_c else "not found",
        "'%s'" % days_c["header"] if days_c else "not found"))
    rows = []
    for r in t["rows"]:
        staff = None
        if staff_c:
            s = roster.staff_for(r[staff_c["j"]])
            staff = s[0] if len(s) == 1 else None
        days = r[days_c["j"]] if days_c else ""
        raw = r[hand_c["j"]] if hand_c else ""
        if hand_c:
            handed = read.handed_of(raw)
            if handed == "unknown" and not raw and days:
                handed = "yes" if int(days) > 0 else "no"
        else:
            handed = ("yes" if int(days) > 0 else "no") if days else "unknown"
        rows.append((r[name_c["j"]], staff, read.intval(r[week_c["j"]]), handed, raw,
                     days))
    return rows


def _diary_wide(t, roster, log, issues):
    cols = t["cols"]
    name_c, staff_c = _who_cols(t, roster)
    weeks = [c for c in cols if c["kind"] == "attword"]
    log.append("%s: read as the diary sheet, one column per week (%s)" % (
        t["file"], ", ".join("'%s'" % c["header"] for c in weeks)))
    rows = []
    for r in t["rows"]:
        staff = None
        if staff_c:
            s = roster.staff_for(r[staff_c["j"]])
            staff = s[0] if len(s) == 1 else None
        for i, c in enumerate(weeks):
            raw = r[c["j"]]
            wk = _digits(c["header"]) or i + 1
            rows.append((r[name_c["j"]], staff, wk, read.handed_of(raw), raw,
                         ""))
    return rows


# ------------------------------------------------------------- assemble

def rules_dnc(text):
    import rules
    return bool(rules.DNC.search(text.lower()))


class CannotRead(Exception):
    """Raised when the files can't be read well enough to trust results."""


_FILE_WORDS = set("""attendance register sheet sheets diary diaries spending
homework hw returns notes note counsellor counselor counsellors session
sessions log logs typed up client clients list marks csv txt md xlsx the of
and group money check scores file files export copy final v1 v2""".split())


def agency_name(files, folder):
    """The words every file name shares, e.g. 'cole-street-attendance.csv'
    and 'cole-street-diaries.csv' -> 'Cole Street'."""
    names = []
    for f in files:
        base = os.path.splitext(re.sub(r" \(sheet \d+\)$", "", f))[0]
        names.append([t for t in re.split(r"[\s_\-.]+", base) if t])
    if names:
        low = [[t.lower() for t in n] for n in names]
        shared = [t for t in names[0] if all(t.lower() in l for l in low)
                  and t.lower() not in _FILE_WORDS
                  and not re.fullmatch(r"\d+", t)]
        if not shared and len(names) == 1:
            shared = [t for t in names[0] if t.lower() not in _FILE_WORDS]
        if shared:
            return " ".join(w if w.isupper() else w.capitalize()
                            for w in shared)
    return re.sub(r"[_\-]+", " ", os.path.basename(
        os.path.abspath(folder))).strip().title()


def assemble(folder, name=None, allow_no_notes=False):
    data = read.load_folder(folder)
    log, issues = list(data["log"]), []

    att_tables = _pick_attendance(data["tables"], log)
    if not att_tables:
        raise CannotRead(
            "No attendance sheet was found. The tool looks for a table with "
            "one row per client and columns of marks such as P / Present / "
            "A / Absent.")
    clients, sessions, checks = [], None, None
    for t in att_tables:
        cs, ss, ks = _clients_from(t, log, issues)
        if sessions is None:
            sessions, checks = ss, ks
        elif [s["n"] for s in ss] != [s["n"] for s in sessions]:
            issues.append("%s has different session columns from the first "
                          "attendance sheet; only its matching sessions are "
                          "used." % t["file"])
        clients += cs
    roster = Roster(clients)

    # ---- notes
    lines, note_files = [], []
    for t in data["texts"]:
        lines += [(t["file"], l) for l in t["text"].splitlines()]
        note_files.append(t["file"])
        log.append("%s: read as notes (%d lines)" % (t["file"], len(
            [l for l in t["text"].splitlines() if l.strip()])))
    for t in data["tables"]:
        if t["kind"] == "notes":
            note_files.append(t["file"])
            log.append("%s: read as notes (%d rows)" % (t["file"],
                                                        len(t["rows"])))
            long_j = [c["j"] for c in t["cols"] if c["kind"] == "longtext"][0]
            for r in t["rows"]:
                head = " | ".join(r[c["j"]] for c in t["cols"]
                                  if c["j"] != long_j and r[c["j"]] and
                                  c["kind"] in ("date", "person", "id",
                                                "number", "other"))
                lines.append((t["file"], head + ": " + r[long_j]))
    _set_dayfirst(lines, log, issues)
    year = _guess_year([l for _, l in lines])
    notes, unused = _parse_note_lines(lines, roster, year, log, issues)

    attended = sum(1 for c in clients for a in c["att"].values()
                   if a["state"] == "present")
    log.append("  notes matched to a client: %d; lines that couldn't be "
               "used: %d; sessions attended on the sheet: %d" % (
                   len(notes), unused, attended))
    if not allow_no_notes:
        if not note_files:
            raise CannotRead(
                "No session notes were found in the folder. Without notes "
                "the tool can't tell who asked not to be contacted, so it "
                "has written nothing.")
        total = len(notes) + unused
        if not notes or len(notes) < 0.6 * total or \
                len(notes) < 0.25 * attended:
            raise CannotRead(
                "Most of the notes couldn't be read: %d note(s) matched to "
                "a client, %d line(s) not understood, against %d attended "
                "sessions on the sheet. Without the notes the tool can't "
                "tell who asked not to be contacted, so it has written "
                "nothing. First lines it couldn't use:\n  %s" % (
                    len(notes), unused, attended, "\n  ".join(
                        i for i in issues if i.startswith("A note"))[:600]
                    or "(none matched a client name)"))
    elif not notes:
        issues.append("No session notes were read. Contact details come "
                      "from the first-day column only.")

    # ---- session dates from the note dates
    dates = sorted({w for _, w, _ in notes if isinstance(w, dt.date)})
    if len(dates) >= 2:
        gaps = collections.Counter((b - a).days for a, b in
                                   zip(dates, dates[1:]))
        gap = gaps.most_common(1)[0][0] or 7
        by_idx = {}
        for d in dates:
            by_idx.setdefault(int(round((d - dates[0]).days / float(gap))), d)
        for i, s in enumerate(sessions):
            s["date"] = by_idx.get(i)
        if max(by_idx) + 1 != len(sessions):
            issues.append("The notes cover %d session dates but the "
                          "attendance sheet has %d sessions with marks. "
                          "Dates were lined up from the first session." %
                          (max(by_idx) + 1, len(sessions)))
    elif len(dates) == 1 and len(sessions) == 1:
        sessions[-1]["date"] = dates[0]
    date_of = {s["n"]: s["date"] for s in sessions}
    for client, when, text in notes:
        if isinstance(when, int) and date_of.get(when):
            when = date_of[when]
        client["notes"].append((when, text))
    n_of = {s["date"]: s["n"] for s in sessions if s["date"]}
    for c in clients:
        c["notes"].sort(key=lambda x: (n_of.get(x[0], x[0]) if not
                                       isinstance(x[0], int) else x[0])
                        if (isinstance(x[0], int) or x[0] in n_of) else 99)

    # ---- diaries
    drows, have_diary, used = [], False, [t["file"] for t in att_tables]
    used += note_files
    for t in data["tables"]:
        if t["kind"] == "diary_long":
            drows += _diary_long(t, roster, log, issues)
            have_diary = True
            used.append(t["file"])
        elif t["kind"] == "diary_wide":
            drows += _diary_wide(t, roster, log, issues)
            have_diary = True
            used.append(t["file"])
        elif t["kind"] == "marks":
            log.append("%s: looks like someone's marked-up list; not used "
                       "as input" % t["file"])
        elif t["kind"] == "other":
            log.append("%s: not recognised, not used" % t["file"])
    seen_bad = set()
    for name_, staff, wk, handed, raw, days in drows:
        c, how, cands = roster.find(name_, staff)
        if c is None:
            if name_ not in seen_bad:
                seen_bad.add(name_)
                issues.append("Diary rows for '%s' couldn't be matched to "
                              "one client (%s)." % (name_, "more than one "
                              "fits" if how == "several" else "no such name"))
            continue
        c["diary"][wk] = {"handed": handed, "raw": raw, "days": days}
    if not have_diary:
        issues.append("No diary sheet was found. Everyone is judged on "
                      "attendance only.")
    weeks = sorted({wk for _, _, wk, _, _, _ in drows if wk is not None})

    return {"agency": name or agency_name(used, folder), "clients": clients,
            "sessions": sessions, "checks": checks, "weeks": weeks,
            "have_diary": have_diary, "log": log, "issues": issues,
            "folder": folder, "year": year}
