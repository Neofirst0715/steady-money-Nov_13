"""The rules. Each one is written out in RULES.md with who set it.

Nothing here reads a name, a column heading or a file name: the rules
work on the joined record for each client.
"""
import re

import read

# Proposed line for "better off": the Money Check must rise by at least
# this many points. NOT yet confirmed by the agency. Change it here and in
# RULES.md together.
BETTER_OFF_MIN_POINTS = 3
BETTER_OFF_CONFIRMED = False

WHY_OK = "Coming and keeping up"
WHY_ATT = "Missed the last two sessions"
WHY_DIARY = "Nothing handed in for two homework weeks"

# ------------------------------------------------------------ note words

HOLD = re.compile(r"\bon hold\b|\bpaused?\b.*\b(diary|hw|homework)|"
                  r"\b(diary|hw|homework)\b.*\bpaused?\b")
RESUME = re.compile(r"\bback on\b|\bresum|\bhold (is )?(over|ended|lifted)|"
                    r"\boff hold\b|\brestart")
NOTSET = re.compile(
    r"\bnot set\b|did(n't| not) set|no homework|no hw\b|"
    r"never got to (the )?(diary|homework|hw)|"
    r"(skipped|skip) (the )?(diary|homework|hw)|(diary|homework|hw) skipped|"
    r"forgot to (hand out|give|set)|(diary|homework|hw)[^.]{0,12}not "
    r"(given|handed out|assigned|sent)|no (diary|diaries) (handed out|given|"
    r"set|sent)|did(n't| not) hand out|no time for (the )?(diary|homework|"
    r"hw)|"
    r"did(n't| not) (get to|give|assign)")
SET = re.compile(r"\b(diary|hw|homework)\b[^.]{0,20}\b(set|given|assigned|"
                 r"went home|sent home)\b|\bset (the )?(diary|hw|homework)")
AWAY = re.compile(r"\baway\b|out of town|travel+ing|on holiday|on vacation|"
                  r"will miss|can('|no)t make|won't be (here|in|able)|"
                  r"will be (out|gone)")
NOTICE = re.compile(r"told (us|me)|ahead|gave notice|let (us|me) know|"
                    r"with notice|in advance|called (ahead|in|to say)|"
                    r"phoned (ahead|in|to say)|sent word|apolog|rang to say|"
                    r"messaged to say")
BACK_S = re.compile(r"back (for|by|at|in) (s|session|wk|week|mtg|meeting) ?(\d)")

DNC = re.compile(
    r"no calls?,? (and |or )?no texts?,? (and |or )?no (mail|letters?|post)|"
    r"no (calls?|texts?|letters?|mail)(, | or | and )+(calls?|texts?)"
    r"(, | or | and )+(letters?|mail|post)|"
    r"not to (reach out|contact|be contacted|call or text|get in touch)|"
    r"(do not|don't|doesn't want (us|me) to|does not want (us|me) to|"
    r"please don't|never|stop) (contact|reach out|get in touch|contacting|"
    r"reaching out)|"
    r"no (contact|outreach|reaching out|follow-?ups?)\b|"
    r"(doesn't|does not|didn't|did not|don't|do not) want (any )?"
    r"(contact|to be contacted|to hear from us|calls,? texts,? or)|"
    r"wants? no contact|not (to )?be contacted|"
    r"asked (us|me)? ?not to (reach|contact|call|get in touch)|"
    r"\bdnc\b|"
    r"not (to )?(reach out|get in touch) at all|leave (him|her|them) "
    r"(alone|be)|opt(ed|s)? out of (contact|reminders|follow)")
NEG_CONTACT = re.compile(
    r"\b(no|not|don't|do not|doesn't want|does not want|never|stop|"
    r"won't take|refus\w+)\b(\W+\w+){0,3}?\W+(contact|contacted|contacting|"
    r"call|calls|called|calling|text|texts|texted|phone|phoned|letter|"
    r"letters|mail|message|messages|reach|reached|email|voicemail)\b")
DEAD = re.compile(r"out of service|cut off|disconnected|not in service|"
                  r"no longer (works|in service)|number (is )?(dead|gone)|"
                  r"lost (his|her|their|the) phone|has no phone|"
                  r"phone (is )?(off|broken|gone)|not recogni[sz]ed|"
                  r"number (is |was )?(not|no longer) (working|in use|valid)|"
                  r"unobtainable|(number|phone) (doesn't|does not) work|"
                  r"wrong number")
PAPER_ONLY = re.compile(r"\b(letters?|mail|paper|post)\b[^.]{0,12}\bonly\b|"
                        r"\bonly\b[^.]{0,12}\b(letters?|mail|post)\b|"
                        r"paper note|by (letter|mail|post)\b|"
                        r"will write to (him|her|them)|write to (him|her|"
                        r"them) instead|send(ing)? (him|her|them)? ?a letter|"
                        r"(letters?|post) instead")
TEXT_OK = re.compile(
    r"own (phone|mobile|cell|number)|"
    r"texts? (is|are|now)? ?(fine|ok|okay|good|best|preferred)|"
    r"txts? (is|are)? ?(fine|ok|okay)|happy with (texts?|txts?)|"
    r"(fine|ok|okay|happy) (with|to get|for) (a )?(texts?|txts?)|"
    r"\btexts? only\b|"
    r"text(ing)? (fine|ok|okay|preferred)|prefers? (a )?texts?|"
    r"(can|ok to|okay to|happy to) text|text is fine")
NO_TEXT = re.compile(r"no texts?\b|not texted|don't text|do not text|"
                     r"no sms|no messages")
NO_CALL = re.compile(r"no calls?\b|don't call|do not call|not (be )?called|"
                     r"not phoned")
CALL_OK = re.compile(r"\b(call|calls|calling|called|phoned|phone call|ring|"
                     r"ringing|phone (him|her|them|me))\b")
EMAIL_OK = re.compile(r"\be-?mail\b")
SHARED = re.compile(r"shared phone|phone is shared|shares? (a|the) phone|"
                    r"family phone|partner's phone|someone else's phone")
NO_VM = re.compile(r"no voice ?mail|don't leave (a )?(message|voice ?mail)|"
                   r"no messages? left")
CONTACT_WORD = re.compile(
    r"\b(text|texts|texted|texting|call|calls|called|calling|phone|phoned|"
    r"ring|letter|letters|mail|email|e-mail|contact|contacted|reach|"
    r"reached|number|voicemail|voice mail|sms|message|messages|contacting|"
    r"in touch|reach out|reaching out|follow-?ups?|follow up|hear from|"
    r"outreach)\b")
NOT_CONTACT = re.compile(r"phone bill|phone plan|phone contract|mail-in|"
                         r"number of|a number\b|call cent")

_NOUNS = (r"phone calls?|calls?|calling|ringing|ring|phoning|phoned|called|"
          r"texts?|txts?|texting|texted|sms|messages?|letters?|mail|post|"
          r"voicemails?|contact")
NEG_LIST = re.compile(
    r"\b(no|not|don't|do not|doesn't|does not|never|stop|without)\b"
    r"(?:\s+(?:more|further|any|to|be|us|me|want|wants|wish|wishes|like|"
    r"likes))*\s+(" + _NOUNS + r")"
    r"((?:\s*(?:,|or|and|nor)\s*(?:any |more |no )?"
    r"(?:phone calls|calls|texts|txts|messages|letters|mail|post|"
    r"voicemails|contact))*)")


def _family(word):
    if re.match(r"call|ring|phon", word):
        return "call"
    if re.match(r"text|txt|sms|messag", word):
        return "text"
    if re.match(r"letter|mail|post", word):
        return "paper"
    return ""


LIMITS = [
    (re.compile(r"evening"), "evenings only"),
    (re.compile(r"daytime|during the day|on (his|her|their|a) break|"
                r"lunch ?(time|break)|at work"), "daytime only"),
    (re.compile(r"morning"), "mornings only"),
    (re.compile(r"weekend"), "weekends only"),
    (re.compile(r"after (\d{1,2}) ?(pm|p\.m\.)?"), None),
]


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?;])\s+", text) if s.strip()]


def read_note(text):
    """What one note says about homework, absence and contact."""
    t = text.lower()
    out = {"hold": bool(HOLD.search(t)), "resume": False, "notset": False,
           "set": False, "away": False, "notice": bool(NOTICE.search(t)),
           "back_s": None, "contact": None, "odd": []}
    if RESUME.search(t) and re.search(r"diary|hw|homework|hold", t) \
            and not re.search(r"still on hold", t):
        out["resume"] = not out["hold"] or bool(re.search(r"back on", t))
        if out["resume"]:
            out["hold"] = False
    out["notset"] = bool(NOTSET.search(t))
    out["set"] = bool(SET.search(t)) and not out["notset"]
    if not out["set"] and re.search(r"ran out of time|ran long|ran over", t) \
            and re.search(r"diary|hw|homework", t):
        out["notset"] = True
    out["away"] = bool(AWAY.search(t))
    m = BACK_S.search(t)
    if m:
        out["back_s"] = int(m.group(3))

    c = {"dnc": False, "unsure_dnc": False, "dead": False, "paper": False,
         "text_ok": False, "no_text": False, "no_call": False,
         "call_ok": False, "email": False, "limits": []}
    hit = False
    for s in _sentences(t):
        s2 = NOT_CONTACT.sub(" ", s)
        if not (CONTACT_WORD.search(s2) or SHARED.search(s2)
                or DEAD.search(s2) or DNC.search(s2)):
            continue
        found = False
        # which ways does this sentence say no to? ("no more calls, texts
        # or letters" says no to all three)
        negated, rest = set(), s2
        for m in NEG_LIST.finditer(s2):
            for word in re.findall(r"[a-z]+", m.group(2) + " " +
                                   (m.group(3) or "")):
                fam = _family(word)
                if fam:
                    negated.add(fam)
            rest = rest.replace(m.group(0), " ")
        if NO_TEXT.search(s2):
            negated.add("text")
            rest = NO_TEXT.sub(" ", rest)
        if NO_CALL.search(s2):
            negated.add("call")
            rest = NO_CALL.sub(" ", rest)
        if DNC.search(s2):
            c["dnc"] = found = True
        if DEAD.search(s2):
            c["dead"] = found = True
        if PAPER_ONLY.search(rest):
            c["paper"] = found = True
        if SHARED.search(s2):
            found = True
        if NO_VM.search(s2):
            c["limits"].append("no voicemail")
            found = True
        if not c["dnc"]:
            text_ok = bool(TEXT_OK.search(rest))
            call_ok = bool(CALL_OK.search(rest)) and not DEAD.search(s2)
            paper_ok = c["paper"] or bool(re.search(
                r"\b(letters?|mail|post)\b[^.]{0,15}\b(fine|ok|okay)\b", rest))
            if len(negated) >= 2 and not (text_ok or call_ok or paper_ok):
                # says no to two or more ways and yes to none
                c["dnc"] = found = True
                if negated != {"call", "text", "paper"}:
                    c["unsure_dnc"] = True
            else:
                if "text" in negated:
                    c["no_text"] = found = True
                elif text_ok:
                    c["text_ok"] = found = True
                if "call" in negated:
                    c["no_call"] = found = True
                elif call_ok:
                    c["call_ok"] = found = True
                if "paper" in negated:
                    c["limits"].append("no letters")
                    found = True
                if EMAIL_OK.search(rest):
                    c["email"] = found = True
                if found:
                    for rx, label in LIMITS:
                        m = rx.search(s2)
                        if m and (c["call_ok"] or c["text_ok"]):
                            lab = label or "after %s" % m.group(1)
                            if lab not in c["limits"]:
                                c["limits"].append(lab)
        if found:
            hit = True
        else:
            out["odd"].append(s)
            if NEG_CONTACT.search(s2):
                # A "no ..." about contact that the tool can't read. Wrongly
                # suggesting contact is the worst mistake, so hold back.
                c["dnc"] = c["unsure_dnc"] = hit = True
    if hit:
        out["contact"] = c
    return out


# ------------------------------------------------------------ per client

def _fmt(d):
    if isinstance(d, int):
        return "session %d" % d
    return "%d %s" % (d.day, d.strftime("%b")) if d else "date unknown"


def evaluate_client(c, model):
    sessions = model["sessions"]
    order = [s["n"] for s in sessions]
    date_of = {s["n"]: s["date"] for s in sessions}
    n_of_date = {s["date"]: s["n"] for s in sessions if s["date"]}
    flags = c["flags"]

    def session_of(d):
        return d if isinstance(d, int) else n_of_date.get(d)

    notes_at = {}
    for d, text in c["notes"]:
        n = session_of(d)
        if n is None:
            flags.append("A note dated %s doesn't line up with a session and "
                         "was read for contact details only." % _fmt(d))
        notes_at.setdefault(n, []).append((d, read_note(text), text))

    # ---- absences with notice
    excused = set(n for n in order if c["att"][n]["state"] == "excused")
    for n in order:
        for d, info, text in notes_at.get(n, []):
            later = [m for m in order if m > n]
            if info["away"]:
                named = set()
                for dd, _, _ in read.find_dates(text, model["year"]):
                    if dd in n_of_date and n_of_date[dd] > n:
                        named.add(n_of_date[dd])
                if info["back_s"]:
                    named |= set(m for m in later if m < info["back_s"])
                if re.search(r"next (two|2) (weeks|sessions)|x ?2 ?w", text.lower()):
                    named |= set(later[:2])
                elif re.search(r"next (week|session)", text.lower()):
                    named |= set(later[:1])
                if not named and later:
                    named = set(later[:1])
                    flags.append("A note on %s says they'd be away but the "
                                 "dates aren't clear; the next session was "
                                 "treated as away with notice." % _fmt(d))
                c.setdefault("away_note", (d, info["back_s"]))
                excused |= named
            if info["notice"] and c["att"][n]["state"] == "absent":
                excused.add(n)
    for n in order:
        if c["att"][n]["state"] == "absent" and notes_at.get(n):
            text = " ".join(t for _, _, t in notes_at[n]).lower()
            if not re.search(r"no show|not here|did(n't| not) (attend|come|"
                             r"show)|absent|no answer|tried|rang|called|"
                             r"away|missed|apolog", text):
                flags.append("The attendance sheet says absent for session "
                             "%d, but there is a note for that day that "
                             "reads as if they came. The sheet was used. "
                             "Please check." % n)
    state = {}
    for n in order:
        st = c["att"][n]["state"]
        if st in ("absent", "") and n in excused:
            st = "excused"
        state[n] = st
    c["state"] = state

    # ---- homework, week by week
    hw, hold, hold_since, hold_last = {}, False, None, None
    for n in order:
        infos = [i for _, i, _ in notes_at.get(n, [])]
        if any(i["resume"] for i in infos):
            hold = False
        if any(i["hold"] for i in infos):
            if not hold:
                hold_since = date_of[n]
            hold, hold_last = True, n
        if hold:
            hw[n] = "hold"
        elif state[n] == "excused":
            hw[n] = "away"
        elif state[n] == "absent":
            hw[n] = "absent"
        elif any(i["notset"] for i in infos):
            hw[n] = "notset"
        elif any(i["set"] for i in infos):
            hw[n] = "set"
        elif state[n] == "present":
            hw[n] = "assumed"
        else:
            hw[n] = "norecord"
    c["hw"] = hw
    if hold and hold_last is not None and hold_last != order[-1]:
        flags.append("Diary on hold since %s. The notes don't say it's back "
                     "on, so it still isn't counted. Please confirm." %
                     _fmt(hold_since))

    # ---- diary weeks
    missed, missed_assumed, not_entered, countable = [], [], [], []
    if model["have_diary"]:
        for wk in model["weeks"]:
            if wk not in hw:
                continue
            row = c["diary"].get(wk)
            if hw[wk] not in ("set", "assumed"):
                continue
            if row is None or row["handed"] == "unknown":
                not_entered.append(wk)
                continue
            countable.append((wk, row))
            if row["handed"] == "no":
                missed.append(wk)
                if hw[wk] == "assumed":
                    missed_assumed.append(wk)
        if not_entered:
            raw = ", ".join(sorted({(c["diary"].get(w) or {}).get("raw") or
                                    "blank" for w in not_entered}))
            flags.append("Diary for week %s isn't entered yet (%s). It is "
                         "not counted as missed." % (
                             ", ".join(str(w) for w in not_entered), raw))

    # ---- status
    held = [n for n in order if any(k["att"][n]["state"] for k in
                                    model["clients"])]
    last_two = held[-2:]
    att_stall = len(last_two) == 2 and all(state[n] == "absent"
                                           for n in last_two)
    diary_stall = len(missed) >= 2
    just_back = False
    if diary_stall and countable and countable[-1][1]["handed"] == "yes":
        diary_stall, just_back = False, True
        days = countable[-1][1]["days"]
        flags.append("Just back: missed weeks %s, then handed in week %d%s. "
                     "Counted as on track; please check." % (
                         ", ".join(str(w) for w in missed), countable[-1][0],
                         " (%s days filled)" % days if days else ""))
    present = [n for n in order if state[n] == "present"]
    last_seen = present[-1] if present else None

    if att_stall:
        status, why, group = "stalled", WHY_ATT, "call"
        detail = "Absent at session %d (%s) and session %d (%s); no notice " \
                 "in the notes." % (last_two[0], _fmt(date_of[last_two[0]]),
                                    last_two[1], _fmt(date_of[last_two[1]]))
    elif diary_stall:
        status, why, group = "stalled", WHY_DIARY, "next"
        detail = "Diary set in weeks %s; none handed in." % " and ".join(
            str(w) for w in missed) if len(missed) == 2 else \
            "Diary set in weeks %s; none handed in." % ", ".join(
                str(w) for w in missed)
        if len(missed) - len(missed_assumed) < 2:
            flags.append("Stalled depends on week %s, where the note doesn't "
                         "say whether the diary was set (counted as set)." %
                         ", ".join(str(w) for w in missed_assumed))
    else:
        status, why, group = "on track", WHY_OK, ""
        # If only an agreed exception keeps them on track, say which one.
        raw_no = [w for w in model["weeks"] if w in hw and
                  (c["diary"].get(w) or {}).get("handed") == "no"]
        spared = [w for w in raw_no if w not in missed]
        if len(last_two) == 2 and all(state[n] in ("absent", "excused")
                                      for n in last_two):
            why = "Away with notice, so the missed sessions don't count"
        elif len(raw_no) >= 2 and spared and not just_back:
            held_w = [w for w in spared if hw[w] == "hold"]
            skip_w = [w for w in spared if hw[w] == "notset"]
            if held_w:
                why = "Diary on hold, so the blank%s count" % (
                    " doesn't" if len(held_w) == 1 else "s don't")
            elif skip_w == [max(model["weeks"])]:
                why = "Homework wasn't set last week, so the blank " \
                      "doesn't count"
            elif skip_w:
                why = "Homework wasn't set in week%s %s, so the blank%s " \
                      "count" % ("s" if len(skip_w) > 1 else "",
                                 " and ".join(str(w) for w in skip_w),
                                 "s don't" if len(skip_w) > 1 else " doesn't")
            else:
                why = "Away those weeks, so the blank diaries don't count"
        bits = []
        ex = [n for n in order if state[n] == "excused"]
        if ex:
            bits.append("Away with notice for session%s %s" % (
                "s" if len(ex) > 1 else "", ", ".join(str(n) for n in ex)))
        if hold:
            bits.append("Diary on hold since %s" % _fmt(hold_since))
        if just_back:
            bits.append("Just back with the diary")
        ab = [n for n in order if state[n] == "absent"]
        if ab:
            bits.append("Missed session%s %s" % ("s" if len(ab) > 1 else "",
                                                ", ".join(str(n) for n in ab)))
        if len(missed) == 1:
            bits.append("One diary week missed (week %d)" % missed[0])
        detail = "; ".join(bits) + ("." if bits else "")
    short = why
    c.update(status=status, why=why, why_short=short, detail=detail,
             group=group,
             last_seen=last_seen, just_back=just_back, missed=missed)

    # ---- contact: the newest note wins over the first-day column
    ch = {"channel": c["day_one"], "limits": [], "date": None,
          "by": "day one", "dnc": c["day_one"] == "do not contact"}
    for d, text in c["notes"]:
        info = read_note(text)
        for s in info["odd"]:
            flags.append("A note on %s mentions contact in words the tool "
                         "doesn't know: \"%s\"" % (_fmt(d), s[:80]))
        k = info["contact"]
        if not k:
            continue
        n = session_of(d)
        here = n is not None and state.get(n) == "present"
        by = "client" if here else "counsellor"
        if k["unsure_dnc"]:
            flags.append("A note on %s says no to some kind of contact in "
                         "words the tool doesn't know. To be safe they are "
                         "treated as do not contact. Please check." % _fmt(d))
        if k["dnc"]:
            ch = {"channel": ch["channel"], "limits": [], "date": d,
                  "by": "client", "dnc": True}
            continue
        new = None
        if k["dead"] or k["paper"]:
            if k["paper"]:
                new = "paper"
            else:
                new = "none"
                flags.append("The number stopped working (%s) and the notes "
                             "give no other way to reach them." % _fmt(d))
        elif k["text_ok"] and not k["no_text"]:
            new = "text"
        elif k["call_ok"] and not k["no_call"]:
            new = "call"
        elif k["email"]:
            new = "email"
        elif k["no_text"]:
            if ch["channel"] == "text":
                new = "call"
                flags.append("A note on %s says no texts but gives no other "
                             "way; shown as call. Please confirm." % _fmt(d))
            else:
                new = ch["channel"]
        elif k["no_call"]:
            new = ch["channel"] if ch["channel"] != "call" else "text"
            flags.append("A note on %s says no calls; please confirm how to "
                         "reach them." % _fmt(d))
        if new is None:
            if k["limits"]:
                ch["limits"] = sorted(set(ch["limits"]) | set(k["limits"]))
            continue
        limits = list(k["limits"])
        if k["no_text"] and new != "text":
            limits.append("no texts")
        if k["no_call"]:
            limits.append("no calls")
        ch = {"channel": new, "limits": limits, "date": d, "by": by,
              "dnc": False}
        if k["dead"] and not here:
            ch["by"] = "counsellor"
    if c.get("force_dnc"):
        ch["dnc"] = True
        ch["date"] = ch["date"] or c["force_dnc"]
    c["contact"] = ch
    if ch["dnc"]:
        reach = "do not contact"
        cdetail = "Asked for no contact between sessions (note of %s)." % \
            _fmt(ch["date"])
    else:
        reach = ch["channel"] or "not known"
        word = {"paper": "letter or paper note", "none": "no working way"}.get(
            ch["channel"], ch["channel"] or "not recorded")
        if ch["limits"]:
            word += ", " + ", ".join(ch["limits"])
        if ch["by"] == "day one":
            cdetail = "%s (first-day sheet, not confirmed since)" % word
        elif ch["by"] == "client":
            cdetail = "%s (note of %s)" % (word, _fmt(ch["date"]))
        else:
            cdetail = "%s (note of %s, set by counsellor; not confirmed by " \
                      "client)" % (word, _fmt(ch["date"]))
        if reach == "none":
            reach = "not known"
    if reach not in ("call", "text", "paper", "do not contact"):
        was = reach
        if ch["channel"] == "none":
            reach = "paper"
            note = "the number no longer works"
        elif c["day_one"] in ("call", "text", "paper"):
            reach = c["day_one"]
            note = "'%s' isn't one of the four ways the results file allows" \
                % was
        else:
            reach = "call"
            note = "no way to reach them is recorded"
        flags.append("way_to_reach is shown as '%s' only because the "
                     "results file needs one of four values (%s). Nothing "
                     "is suggested on the Friday sheet." % (reach, note))
        c["reach_unsure"] = True
    c["reach"], c["reach_detail"] = reach, cdetail
    return c


# ------------------------------------------------------------ whole group

def summarise(model):
    cs = model["clients"]
    order = [s["n"] for s in model["sessions"]]
    out = {"listed": len(cs)}
    started = list(cs)          # everyone on the attendance sheet
    out["started"] = len(started)
    out["never"] = sum(1 for c in cs if not any(
        c["state"][n] == "present" for n in order))
    gone = [c for c in started if c["why"] == WHY_ATT]
    away = [c for c in started if c not in gone and order
            and c["state"][order[-1]] == "excused"]
    out["stopped"] = len(gone)
    out["away"] = len(away)
    out["stuck"] = len(started) - len(gone)

    checks = model["checks"]
    out["checks"] = len(checks)
    if len(checks) >= 2:
        first, last = 0, len(checks) - 1
        both, unknown, dist = [], 0, {}
        for c in started:
            a, b = c["checks"][first], c["checks"][last]
            if a is None or b is None:
                unknown += 1
                continue
            both.append(b - a)
            dist[b - a] = dist.get(b - a, 0) + 1
        out.update(first_label=checks[first]["header"],
                   last_label=checks[last]["header"],
                   first_n=checks[first]["n"], last_n=checks[last]["n"],
                   scored=len(both), unknown=unknown, dist=dist,
                   up_by={k: sum(1 for x in both if x >= k)
                          for k in (1, 2, 3, 4, 5)},
                   same=sum(1 for x in both if x == 0),
                   down=sum(1 for x in both if x < 0),
                   better=sum(1 for x in both
                              if x >= BETTER_OFF_MIN_POINTS))
    return out


def evaluate(model):
    for c in model["clients"]:
        evaluate_client(c, model)
    model["summary"] = summarise(model)
    return model
