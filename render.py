"""Write the printable pages. Plain HTML that prints from any browser."""
import csv
import datetime as dt
import html
import os
import re

import rules

PROGRAM_SESSIONS = 6
MONEY_CHECK_SESSIONS = (1, 4, 6)

CSS = """
body{font:11pt/1.4 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;
 color:#111;margin:24px auto;max-width:820px;padding:0 16px}
h1{font-size:17pt;margin:0 0 2px} h2{font-size:12.5pt;margin:20px 0 6px;
 border-bottom:1.5px solid #111;padding-bottom:2px}
.sub{color:#444;margin:0 0 10px} .small{font-size:9.5pt;color:#444}
table{border-collapse:collapse;width:100%;margin:4px 0 8px}
th,td{border:1px solid #999;padding:5px 7px;text-align:left;
 vertical-align:top} th{background:#eee;font-size:9.5pt}
.box{border:1.5px solid #111;padding:8px 12px;margin:10px 0}
.warn{border:2px solid #111;background:#f3f3f3;padding:8px 12px;margin:10px 0}
.big{display:flex;gap:12px;margin:12px 0}
.big div{flex:1;border:1.5px solid #111;padding:10px 12px}
.big b{display:block;font-size:22pt;line-height:1.1}
.tick{width:22px} .none{color:#555;font-style:italic}
ul{margin:4px 0 8px 18px;padding:0} li{margin:2px 0}
.sign{margin-top:26px;display:flex;gap:30px}
.sign div{flex:1;border-top:1px solid #111;padding-top:3px;font-size:9.5pt}
@media print{body{margin:0;max-width:none} h2{break-after:avoid}
 tr{break-inside:avoid}}
"""


def e(s):
    return html.escape(str(s if s is not None else ""))


def _fmt(d, year=False):
    if not d:
        return "date not known"
    return "%d %s%s" % (d.day, d.strftime("%b"), d.strftime(" %Y") if year
                        else "")


def _page(title, body):
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<title>%s</title><style>%s</style></head><body>%s</body></html>"
            % (e(title), CSS, body))


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "counsellor"


def _next_session(model):
    ss = model["sessions"]
    last = ss[-1]
    n = last["n"] + 1
    dates = [s["date"] for s in ss if s["date"]]
    nxt = None
    if len(dates) >= 2 and last["date"]:
        nxt = last["date"] + (dates[-1] - dates[-2])
    return (n if n <= PROGRAM_SESSIONS else None), nxt


def _seen(c, model):
    if c["last_seen"] is None:
        return "never"
    d = {s["n"]: s["date"] for s in model["sessions"]}[c["last_seen"]]
    return "Session %d (%s)" % (c["last_seen"], _fmt(d))


def _row(c, model, phone=True):
    ph = ""
    if phone and c["phone"] and c["contact"]["channel"] in ("call", "text"):
        ph = "<br><span class='small'>%s</span>" % e(c["phone"])
    why = e(c["why"]) + ("<br><span class='small'>%s</span>" % e(c["detail"])
                         if c["detail"] else "")
    return ("<tr><td class='tick'>&#9744;</td><td><b>%s</b></td><td>%s</td>"
            "<td>%s</td><td>%s%s</td></tr>" % (
                e(c["name"]), e(_seen(c, model)), why, e(c["reach_detail"]),
                ph))


HEAD = ("<tr><th></th><th>Who</th><th>Last at a session</th>"
        "<th>Why they're here</th><th>How to reach them (newest in the "
        "notes)</th></tr>")


def sheet(model, counsellor, today):
    mine = [c for c in model["clients"] if c["counsellor"] == counsellor
            and not c["contact"]["dnc"]]
    sure = lambda c: c["contact"]["by"] != "counsellor" and \
        not c.get("reach_unsure")
    call = sorted([c for c in mine if c["group"] == "call" and sure(c)],
                  key=lambda c: (c["last_seen"] or 0, c["name"]))
    decide = sorted([c for c in mine if c["group"] == "call" and not sure(c)],
                    key=lambda c: (c["last_seen"] or 0, c["name"]))
    nxt = sorted([c for c in mine if c["group"] == "next"],
                 key=lambda c: c["name"])
    n_next, d_next = _next_session(model)
    last = model["sessions"][-1]
    b = ["<h1>Friday sheet: %s</h1>" % e(counsellor or "all clients"),
         "<p class='sub'>%s &middot; printed %s &middot; records up to "
         "session %d (%s)%s</p>" % (
             e(model["agency"]), _fmt(today, True), last["n"],
             _fmt(last["date"]),
             " &middot; next session: %d%s" % (
                 n_next, " (%s)" % _fmt(d_next) if d_next else "")
             if n_next else ""),
         "<p class='small'>For the counsellor only. Keep with client files. "
         "Anyone who asked not to be contacted between sessions is left off "
         "this sheet.</p>"]

    b.append("<h2>1. Reach out this week: may be drifting away (%d)</h2>"
             % len(call))
    if call:
        b.append("<table>%s%s</table>" % (HEAD, "".join(
            _row(c, model) for c in call)))
    else:
        b.append("<p class='none'>Nobody this week.</p>")

    if decide:
        b.append("<h2>2. Your decision first: no way confirmed by the "
                 "client (%d)</h2>" % len(decide))
        b.append("<p class='small'>These people have stopped coming and the "
                 "only way on file was not agreed by them. Nothing is "
                 "suggested until you decide.</p>")
        b.append("<table>%s%s</table>" % (HEAD, "".join(
            _row(c, model, phone=False) for c in decide)))

    b.append("<h2>%d. Talk at the next session, no call needed (%d)</h2>" %
             (3 if decide else 2, len(nxt)))
    b.append("<p class='small'>They are coming but the diary hasn't come "
             "back. A quiet word about what goes where on the page, and "
             "what the diary is for, at the session.</p>")
    if nxt:
        b.append("<table>%s%s</table>" % (HEAD, "".join(
            _row(c, model, phone=False) for c in nxt)))
    else:
        b.append("<p class='none'>Nobody this week.</p>")

    flagged = [c for c in mine if c["flags"]]
    b.append("<h2>%d. Please check (%d)</h2>" % (4 if decide else 3,
                                                 len(flagged)))
    if flagged:
        b.append("<ul>%s</ul>" % "".join(
            "<li><b>%s</b>: %s</li>" % (e(c["name"]), e(" ".join(c["flags"])))
            for c in sorted(flagged, key=lambda c: c["name"])))
    else:
        b.append("<p class='none'>Nothing to check.</p>")
    if n_next in MONEY_CHECK_SESSIONS:
        b.append("<div class='box'><b>Session %d is a Money Check session."
                 "</b> While you are sitting down one-to-one, ask each "
                 "person privately how they want to be reached now (call, "
                 "text, letter, voicemail or none) and write it in your "
                 "notes. The first-day sheet goes out of date.</div>" %
                 n_next)
    b.append("<p class='small'>How people were placed: stalled means the "
             "last two sessions were missed with no notice, or two weeks' "
             "diaries were set and not handed in. Away with notice and "
             "diary on hold are not counted. A week where the note doesn't "
             "mention the diary counts as set. This sheet never sends "
             "anything; you decide every contact.</p>")
    return _page("Friday sheet - %s" % counsellor, "".join(b))


def renewal(model, today):
    s = model["summary"]
    ss = model["sessions"]
    held = len(ss)
    d0, d1 = ss[0]["date"], ss[-1]["date"]
    small = s["started"] < 10
    has_scores = s["checks"] >= 2
    final = has_scores and s.get("last_n") == PROGRAM_SESSIONS

    def lab(n, header, word):
        return "session %d" % n if n else "the %s check ('%s')" % (word,
                                                                    header)

    b = ["<h1>%s: Steady Money results for this group</h1>" %
         e(model["agency"]),
         "<p class='sub'>%s &middot; sessions 1 to %d of %d%s &middot; "
         "prepared %s</p>" % (
             "Final results" if final else
             "<b>A halfway view:</b> the group has not finished",
             held, PROGRAM_SESSIONS,
             ", %s to %s" % (_fmt(d0), _fmt(d1, True)) if d0 and d1 else "",
             _fmt(today, True)),
         "<div class='warn'><b>Draft.</b> For the director to check and "
         "sign before it goes to anyone. No client is named on this page. "
         "Whole-group totals only.</div>"]
    if small:
        b.append("<div class='warn'><b>Small group (%d people).</b> Totals "
                 "this small could point to an individual. Check with the "
                 "director before sharing outside the agency.</div>" %
                 s["started"])

    b.append("<div class='big'><div>Started<b>%d</b><span class='small'>"
             "everyone on the attendance sheet</span></div>"
             "<div>Took both Money Checks<b>%s</b><span class='small'>of "
             "%d who started</span></div>"
             "<div>Improved<b>%s</b><span class='small'>score up %d points "
             "or more%s</span></div></div>" % (
                 s["started"], s["scored"] if has_scores else "not known",
                 s["started"], s["better"] if has_scores else "not known",
                 rules.BETTER_OFF_MIN_POINTS,
                 "" if rules.BETTER_OFF_CONFIRMED else " (proposed line)"))

    b.append("<h2>Everyone who started (%d)</h2><table>"
             "<tr><th>Where they are now</th><th>People</th></tr>"
             "<tr><td>Still coming (stuck with it so far: %d)</td>"
             "<td>%d</td></tr>"
             "<tr><td>Away with notice, expected back</td><td>%d</td></tr>"
             "<tr><td>Missed the last two sessions with no notice</td>"
             "<td>%d</td></tr><tr><th>Total</th><th>%d</th></tr></table>" % (
                 s["started"], s["stuck"], s["stuck"] - s["away"], s["away"],
                 s["stopped"], s["started"]))
    if s["never"]:
        b.append("<p class='small'>%d of these are on the sheet with no "
                 "session marked as attended.</p>" % s["never"])

    if has_scores:
        a = lab(s["first_n"], s["first_label"], "first")
        z = lab(s["last_n"], s["last_label"], "latest")
        line = rules.BETTER_OFF_MIN_POINTS
        mid = s["up_by"][1] - s["better"]
        b.append("<h2>Money Check: %s compared with %s</h2>" % (e(a), e(z)))
        b.append("<p class='small'>Five questions the client answers with "
                 "their counsellor, each 1 to 5, total out of 25. Higher is "
                 "better.</p>")
        b.append("<table><tr><th>Change in score</th><th>People</th></tr>"
                 "<tr><td>Up %d points or more (counted as improved)</td>"
                 "<td>%d</td></tr>"
                 "<tr><td>Up 1 to %d points</td><td>%d</td></tr>"
                 "<tr><td>No change</td><td>%d</td></tr>"
                 "<tr><td>Down</td><td>%d</td></tr>"
                 "<tr><td>Not known: did not take both checks (no score at "
                 "%s)</td><td>%d</td></tr>"
                 "<tr><th>Total</th><th>%d</th></tr></table>" % (
                     line, s["better"], line - 1, mid, s["same"], s["down"],
                     e(z), s["unknown"], s["started"]))
        spread = ", ".join("%s%d: %d" % ("+" if k > 0 else "", k, v)
                           for k, v in sorted(s["dist"].items()))
        b.append("<p class='small'>Full spread of changes (points: people): "
                 "%s. If the line were 1 point, %d would count; at 2 points, "
                 "%d; at 3, %d; at 5, %d.</p>" % (
                     e(spread), s["up_by"][1], s["up_by"][2], s["up_by"][3],
                     s["up_by"][5]))
    else:
        b.append("<h2>Money Check</h2><p>Fewer than two Money Check columns "
                 "were found, so no change can be shown.</p>")

    b.append("<h2>How we counted</h2><ul>"
             "<li><b>Started:</b> everyone on the attendance sheet.</li>"
             "<li><b>Took both Money Checks:</b> has a score at both checks "
             "named above.</li>"
             "<li><b>Stuck with it:</b> has not missed the last two sessions "
             "without telling the counsellor ahead. Arriving late counts as "
             "attending. Diaries are not part of this count.</li>")
    if has_scores:
        b.append("<li><b>Improved:</b> the Money Check rose by %d points "
                 "or more between the two checks named above. A rise of 1 "
                 "or 2 points is shown but not counted, because it could be "
                 "one good day. %s Nobody without a latest score is counted "
                 "as improved, and nobody is left out of the totals.</li>" % (
                     rules.BETTER_OFF_MIN_POINTS,
                     "" if rules.BETTER_OFF_CONFIRMED else
                     "This line is proposed and has not yet been confirmed "
                     "by the counsellors."))
    b.append("<li>The two checks to compare were chosen before the numbers "
             "were seen: the first and the latest.</li></ul>")
    b.append("<h2>What this page can't tell you</h2><ul>"
             "<li>Scores are the client's own rating, given face to face "
             "with their counsellor.</li>")
    if not final:
        b.append("<li>This is a halfway view. The final Money Check is at "
                 "session %d.</li>" % PROGRAM_SESSIONS)
    b.append("<li>There is no written scoring guide, so these numbers should "
             "not be compared with another agency's.</li>"
             "<li>It covers this one group only.</li></ul>")
    b.append("<div class='sign'><div>Checked against the records by</div>"
             "<div>Director</div><div>Date</div></div>")
    return _page("%s - renewal page" % model["agency"], "".join(b))


def checklist(model, today):
    b = ["<h1>Check list: %s</h1>" % e(model["agency"]),
         "<p class='sub'>Run on %s. For staff only: this page has client "
         "names.</p>" % _fmt(today, True),
         "<h2>How each file was read</h2><ul>%s</ul>" % "".join(
             "<li>%s</li>" % e(l) for l in model["log"])]
    b.append("<h2>Things the tool couldn't settle (%d)</h2>" %
             len(model["issues"]))
    b.append("<ul>%s</ul>" % "".join("<li>%s</li>" % e(i) for i in
                                     model["issues"]) if model["issues"]
             else "<p class='none'>None.</p>")
    flagged = [c for c in model["clients"] if c["flags"]]
    b.append("<h2>Clients to check (%d)</h2>" % len(flagged))
    if flagged:
        b.append("<table><tr><th>Client</th><th>Counsellor</th>"
                 "<th>What to check</th></tr>%s</table>" % "".join(
                     "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                         e(c["name"]), e(c["counsellor"]),
                         e(" ".join(c["flags"]))) for c in flagged))
    else:
        b.append("<p class='none'>None.</p>")
    dnc = [c for c in model["clients"] if c["contact"]["dnc"]]
    b.append("<h2>Left off every Friday sheet at their own request (%d)"
             "</h2>" % len(dnc))
    b.append("<ul>%s</ul>" % "".join(
        "<li>%s (%s): %s</li>" % (e(c["name"]), e(c["counsellor"]),
                                  e(c["reach_detail"])) for c in dnc)
        if dnc else "<p class='none'>Nobody.</p>")
    return _page("Check list", "".join(b))


def write_all(model, out_dir, today=None):
    today = today or dt.date.today()
    os.makedirs(out_dir, exist_ok=True)
    made = []

    def put(name, text):
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        made.append(path)

    for staff in sorted({c["counsellor"] for c in model["clients"]}):
        put("friday-sheet-%s.html" % _slug(staff or "all"),
            sheet(model, staff, today))
    put("renewal-page.html", renewal(model, today))
    put("check-list.html", checklist(model, today))
    path = os.path.join(out_dir, "results.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["client_id", "status", "way_to_reach", "why"])
        for c in model["clients"]:
            w.writerow([c["id"], c["status"], c["reach"], c["why_short"]])
    made.append(path)
    path = os.path.join(out_dir, "results-detail.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["client_id", "name", "counsellor", "status",
                    "way_to_reach", "why", "detail", "contact_detail",
                    "on_friday_sheet", "to_check"])
        for c in model["clients"]:
            where = "left off (no contact)" if c["contact"]["dnc"] else \
                {"call": "reach out", "next": "talk at next session"}.get(
                    c["group"], "no")
            w.writerow([c["id"], c["name"], c["counsellor"], c["status"],
                        c["reach"], c["why"], c["detail"], c["reach_detail"],
                        where, " ".join(c["flags"])])
    made.append(path)
    return made
