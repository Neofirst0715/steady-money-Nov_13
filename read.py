"""Read an agency's folder.

Nothing here depends on file names or column headings. Each file is
recognised by what its cells contain, and anything that can't be
recognised is reported, never guessed.
"""
import csv
import datetime as dt
import io
import os
import re
import zipfile
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------- words

PRESENT = {"p", "present", "y", "yes", "x", "here", "attended", "came", "1",
           "in", "pres", "late", "l", "tardy", "arrived late", "\u2713",
           "\u2714", "attended (late)", "present (late)", "came late"}
LATE = {"late", "l", "tardy", "arrived late", "attended (late)",
        "present (late)", "came late"}
ABSENT = {"a", "absent", "no show", "noshow", "no-show", "ns", "n", "no",
          "dna", "missed", "0", "abs", "did not attend", "not here", "out",
          "\u2717", "\u2718", "no-show", "didn't come", "did not come",
          "not present", "unexcused"}
EXCUSED = {"excused", "ex", "away", "notice", "an", "absent (notice)",
           "away (notice)", "apologies", "absent with notice",
           "away with notice", "told us", "absent (excused)",
           "excused absence"}

TEXT = {"text", "texts", "sms", "txt", "message", "msg", "text message",
        "whatsapp"}
CALL = {"call", "calls", "phone", "tel", "telephone", "voice", "phone call",
        "ring", "mobile", "cell"}
PAPER = {"mail", "letter", "letters", "post", "paper", "by post", "postal",
         "note"}
EMAIL = {"email", "e-mail"}
NOCONTACT = {"none", "do not contact", "no contact", "dnc"}

YES = {"yes", "y", "true", "1", "in", "handed in", "returned", "done", "x",
       "\u2713", "\u2714", "back", "late", "handed in late"}
NO = {"no", "n", "false", "0", "not in", "none", "missing",
      "not handed in", "not returned", "\u2717", "\u2718", "not back"}

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct",
     "nov", "dec"], 1)}


def norm(v):
    return re.sub(r"\s+", " ", str(v or "")).strip()


def low(v):
    return norm(v).lower()


def channel_of(v):
    """Map a contact word to one of: text, call, paper, email, none, ''."""
    s = low(v)
    if s and len(s) <= 28 and s not in TEXT | CALL | PAPER | EMAIL | NOCONTACT:
        if re.search(r"do not|don't|no contact|none|nothing", s):
            return "do not contact"
        if re.search(r"e-?mail", s):
            return "email"
        if re.search(r"\b(text|sms|txt)", s):
            return "text"
        if re.search(r"\b(call|phone|ring|tel)", s):
            return "call"
        if re.search(r"\b(letter|mail|post|paper)", s):
            return "paper"
    if s in TEXT:
        return "text"
    if s in CALL:
        return "call"
    if s in PAPER:
        return "paper"
    if s in EMAIL:
        return "email"
    if s in NOCONTACT:
        return "do not contact"
    return ""


def attendance_of(v):
    """-> (state, late). state is present / absent / excused / '' (blank)
    or None when the word isn't understood."""
    s = low(v)
    if not s:
        return "", False
    if s in PRESENT:
        return "present", s in LATE
    if s in EXCUSED:
        return "excused", False
    if s in ABSENT:
        return "absent", False
    return None, False


def handed_of(v):
    s = low(v)
    if s in YES:
        return "yes"
    if s in NO:
        return "no"
    return "unknown"


# ---------------------------------------------------------------- dates

_DATE_RES = [
    (re.compile(r"\b(20\d\d)[-/.](\d{1,2})[-/.](\d{1,2})\b"), "ymd"),
    (re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.]((?:20)?\d\d)\b"), "xxy"),
    (re.compile(r"\b([A-Za-z]{3,9})\.?[ \-/](\d{1,2})(?:st|nd|rd|th)?,?[ \-/](20\d\d)\b"), "mdy_w"),
    (re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?[ \-/]([A-Za-z]{3,9})\.?,?[ \-/](20\d\d)\b"), "dmy_w"),
]
DAYFIRST = False   # set by build.assemble after looking at all the notes
_NUM_SHORT = re.compile(r"(?<![\d/.\-])(\d{1,2})[/.\-](\d{1,2})(?![\d/.\-])")

_SHORT_RES = [
    (re.compile(r"\b([A-Za-z]{3,9})\.?[ \-](\d{1,2})(?:st|nd|rd|th)?\b"), "md_w"),
    (re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?[ \-]([A-Za-z]{3,9})\b"), "dm_w"),
]


def _mk(y, m, d):
    try:
        return dt.date(int(y), int(m), int(d))
    except ValueError:
        return None


def find_dates(text, year=None):
    """All dates in a piece of text, as (date, start, end)."""
    out = []
    for rx, kind in _DATE_RES:
        for m in rx.finditer(text):
            g = m.groups()
            d = None
            if kind == "ymd":
                d = _mk(g[0], g[1], g[2])
            elif kind == "xxy":
                a, b = int(g[0]), int(g[1])
                y = int(g[2]) if int(g[2]) > 99 else 2000 + int(g[2])
                if a > 12 or (DAYFIRST and b <= 12):
                    d = _mk(y, b, a)
                else:
                    d = _mk(y, a, b)
            elif kind == "mdy_w" and g[0][:3].lower() in MONTHS:
                d = _mk(g[2], MONTHS[g[0][:3].lower()], g[1])
            elif kind == "dmy_w" and g[1][:3].lower() in MONTHS:
                d = _mk(g[2], MONTHS[g[1][:3].lower()], g[0])
            if d and not any(s <= m.start() < e for _, s, e in out):
                out.append((d, m.start(), m.end()))
    if year:
        for rx, kind in _SHORT_RES:
            for m in rx.finditer(text):
                if any(s <= m.start() < e or s < m.end() <= e
                       for _, s, e in out):
                    continue
                g = m.groups()
                d = None
                if kind == "md_w" and g[0][:3].lower() in MONTHS:
                    d = _mk(year, MONTHS[g[0][:3].lower()], g[1])
                elif kind == "dm_w" and g[1][:3].lower() in MONTHS:
                    d = _mk(year, MONTHS[g[1][:3].lower()], g[0])
                if d:
                    out.append((d, m.start(), m.end()))
        for m in _NUM_SHORT.finditer(text):
            if any(s <= m.start() < e or s < m.end() <= e for _, s, e in out):
                continue
            a, b = int(m.group(1)), int(m.group(2))
            d = _mk(year, b, a) if (a > 12 or (DAYFIRST and b <= 12)) \
                else _mk(year, a, b)
            if d:
                out.append((d, m.start(), m.end()))
    out.sort(key=lambda t: t[1])
    return out


# ---------------------------------------------------------------- tables

def _read_text(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeError:
            continue
    return raw.decode("latin-1", "replace")


def _rows_from_csv(path):
    text = _read_text(path)
    first = text.splitlines()[0] if text.strip() else ""
    delim = max([",", ";", "\t", "|"], key=first.count)
    return [[norm(c) for c in r] for r in csv.reader(io.StringIO(text),
                                                     delimiter=delim)]


def _rows_from_xlsx(path):
    """Small .xlsx reader (standard library only). One list of rows per
    sheet."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheets = []
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter(
                    "{%s}t" % ns["m"])))
        names = sorted(n for n in z.namelist()
                       if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        for n in names:
            root = ET.fromstring(z.read(n))
            rows = []
            for row in root.iter("{%s}row" % ns["m"]):
                cells = {}
                for c in row.findall("m:c", ns):
                    ref = c.get("r", "")
                    col = 0
                    for ch in re.sub(r"\d", "", ref):
                        col = col * 26 + (ord(ch.upper()) - 64)
                    v = c.find("m:v", ns)
                    val = v.text if v is not None else ""
                    if c.get("t") == "s" and val != "":
                        val = shared[int(val)]
                    elif c.get("t") == "inlineStr":
                        val = "".join(t.text or "" for t in c.iter(
                            "{%s}t" % ns["m"]))
                    elif re.fullmatch(r"-?\d+\.0+", val or ""):
                        val = val.split(".")[0]
                    cells[col] = norm(val)
                if cells:
                    width = max(cells)
                    rows.append([cells.get(i, "") for i in
                                 range(1, width + 1)])
            if rows:
                sheets.append(rows)
    return sheets


def _table(rows):
    """Drop blank rows, take the first row with 3+ filled cells as the
    header, pad the rest."""
    rows = [r for r in rows if any(c for c in r)]
    start = 0
    for i, r in enumerate(rows[:10]):
        if sum(1 for c in r if c) >= 3:
            start = i
            break
    rows = rows[start:]
    if len(rows) < 2:
        return None
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    return {"headers": rows[0], "rows": rows[1:]}


def _col(table, j):
    return [r[j] for r in table["rows"]]


def _frac(values, test):
    vals = [v for v in values if v]
    if not vals:
        return 0.0
    return sum(1 for v in vals if test(v)) / len(vals)


def _is_person(v):
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*\.?,?( [A-Za-z][A-Za-z'\-]*\.?){0,3}", v))


def _is_phone(v):
    return len(re.sub(r"\D", "", v)) >= 7 and bool(re.fullmatch(r"[\d\s().+\-x]+", v))


_INT = re.compile(r"(?:week|wk|w|session|sess|s|mtg|meeting)?\.?\s*#?(\d+)"
                  r"(?:\s*/\s*25)?", re.I)


def intval(v):
    """'14', '14/25', 'Week 3', 'wk3' -> 14, 14, 3, 3. Else None."""
    m = _INT.fullmatch(norm(v))
    return int(m.group(1)) if m else None


def _is_int(v, lo, hi):
    n = intval(v)
    return n is not None and lo <= n <= hi


def describe_columns(table):
    """Work out what each column holds from its values (headings are only
    used to break ties)."""
    cols = []
    n = len(table["rows"])
    for j, h in enumerate(table["headers"]):
        vals = _col(table, j)
        filled = [v for v in vals if v]
        distinct = len(set(low(v) for v in filled))
        hl = low(h)
        kind = "other"
        if not filled:
            kind = "empty"
        elif _frac(vals, lambda v: low(v) in ("stalled", "on track")) >= 0.6:
            kind = "marks"
        elif _frac(vals, _is_phone) >= 0.8:
            kind = "phone"
        elif _frac(vals, lambda v: attendance_of(v)[0] is not None) >= 0.8 \
                and distinct <= 8:
            kind = "attword"       # could be a session or a yes/no column
        elif _frac(vals, lambda v: channel_of(v) != "") >= 0.8:
            kind = "channel"
        elif _frac(vals, lambda v: _is_int(v, 0, 400)) >= 0.9:
            kind = "number"
        elif _frac(vals, lambda v: bool(find_dates(v))) >= 0.8:
            kind = "date"
        elif sum(len(v) for v in filled) / len(filled) > 40:
            kind = "longtext"
        elif _frac(vals, _is_person) >= 0.8:
            kind = "person"
        elif distinct == len(filled) and _frac(
                vals, lambda v: bool(re.search(r"\d", v)) and len(v) <= 14
                and " " not in v) >= 0.9:
            kind = "id"
        cols.append({"j": j, "header": h, "hl": hl, "kind": kind,
                     "distinct": distinct, "filled": len(filled), "n": n})
    return cols


ATT_HINT = re.compile(r"sess|mtg|meet|class|attend|visit|^s ?\d|wk ?\d|week ?\d")
DIARY_HINT = re.compile(r"diar|hw|homework|journal|log|handed|in\?|returned")
CHECK_HINT = re.compile(r"check|score|money|mc\b|mc_")


def classify_table(table, fname=""):
    """-> (kind, columns). kind is attendance / diary_long / diary_wide /
    notes / marks / other."""
    cols = describe_columns(table)
    kinds = [c["kind"] for c in cols]
    fl = fname.lower()
    if "marks" in kinds:
        return "marks", cols
    people = [c for c in cols if c["kind"] == "person"]
    attw = [c for c in cols if c["kind"] == "attword"]
    n = len(table["rows"])

    def unique_people():
        return [c for c in people if c["distinct"] >= 0.9 * c["filled"]
                and c["filled"] >= 0.9 * n]

    if "longtext" in kinds and ("date" in kinds or "number" in kinds) \
            and not (unique_people() and len(attw) >= 2):
        return "notes", cols
    # long diary: one row per person per week
    numbers = [c for c in cols if c["kind"] == "number"]
    repeated = [c for c in people if c["distinct"] < 0.9 * c["filled"]]
    repeated += [c for c in cols if c["kind"] == "other" and c["filled"] == n
                 and 1 < c["distinct"] < 0.9 * n and _frac(
                     _col(table, c["j"]), lambda v: bool(re.search(r"\d", v))
                     and len(v) <= 14) >= 0.9]
    weekcols = [c for c in numbers if c["distinct"] <= 12
                and c["filled"] == n and c["distinct"] < n]
    if attw and weekcols and repeated and not unique_people():
        return "diary_long", cols
    if not attw and weekcols and repeated and not unique_people() \
            and (DIARY_HINT.search(" ".join(c["hl"] for c in cols))
                 or "diar" in fl):
        return "diary_long", cols
    ids = [c for c in cols if c["kind"] == "id"]
    if not people and ids and attw and "channel" not in kinds and (
            DIARY_HINT.search(" ".join(c["hl"] for c in attw))
            or "diar" in fl or "homework" in fl):
        return "diary_wide", cols
    if unique_people() and len(attw) >= 1:
        heads = " ".join(c["hl"] for c in attw)
        diaryish = DIARY_HINT.search(heads) or ("diar" in fl and not
                                                ATT_HINT.search(heads))
        has_checks = any(c["kind"] == "number" for c in cols)
        if diaryish and not has_checks and "channel" not in kinds:
            return "diary_wide", cols
        return "attendance", cols
    return "other", cols


# ---------------------------------------------------------------- folder

def load_folder(folder):
    """-> dict(tables=[...], texts=[...], log=[...])"""
    tables, texts, log = [], [], []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d.lower() not in ("out", "output", "__pycache__")]
        for f in sorted(files):
            if f.startswith(".") or f.startswith("~$"):
                continue
            path = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            try:
                if ext in (".csv", ".tsv"):
                    t = _table(_rows_from_csv(path))
                    if t:
                        t["file"] = f
                        tables.append(t)
                    else:
                        log.append("%s: no rows found, not used" % f)
                elif ext in (".xlsx", ".xlsm"):
                    for i, rows in enumerate(_rows_from_xlsx(path), 1):
                        t = _table(rows)
                        if t:
                            t["file"] = "%s (sheet %d)" % (f, i)
                            tables.append(t)
                elif ext in (".txt", ".md", ".text"):
                    texts.append({"file": f, "text": _read_text(path)})
                else:
                    log.append("%s: file type not read (%s)" % (f, ext or
                                                                "no type"))
            except Exception as e:      # a bad file must not stop the run
                log.append("%s: could not be read (%s)" % (f, e))
    return {"tables": tables, "texts": texts, "log": log}
