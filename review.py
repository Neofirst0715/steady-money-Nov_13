"""Review layer for the browser page: confirm, edit or resolve what the
tool flagged, with who did it and when.

It never changes the agency's files or the rules. Corrections are kept in
reviews/<agency>.json beside app.py and applied on top of what the tool
worked out. The command-line run (run.py) ignores them, so its output is
always exactly what the files and the rules give.
"""
import csv
import datetime as dt
import hashlib
import json
import os
import re

import rules

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "reviews")
STATUSES = ("on track", "stalled")
WAYS = ("call", "text", "paper", "do not contact")


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "agency"


def _path(agency):
    return os.path.join(STORE, _slug(agency) + ".json")


def load(agency):
    try:
        with open(_path(agency), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"agency": agency, "items": {}, "overrides": {}, "log": []}


def save(agency, store):
    os.makedirs(STORE, exist_ok=True)
    with open(_path(agency), "w", encoding="utf-8") as f:
        json.dump(store, f, indent=1)


def key_for(owner, text):
    return "%s|%s" % (owner, hashlib.md5(text.encode("utf-8")).hexdigest()[:10])


def record(agency, action, key, by, note="", client=None, status=None,
           reach=None, text=""):
    """Save one review action. -> error text, or '' when saved."""
    by, note = (by or "").strip(), (note or "").strip()
    if not by:
        return "Type your name in 'Reviewed by' first, so the record shows who did this."
    if action in ("edit", "resolve") and not note:
        return "Add a short note saying what you checked or why."
    store = load(agency)
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = {"at": now, "by": by, "action": action, "key": key,
             "note": note, "what": text,
             "client_id": client["id"] if client else "",
             "name": client["name"] if client else ""}
    if action == "edit":
        if status not in STATUSES or reach not in WAYS:
            return "Choose a status and a way to reach."
        before = {"status": client["tool_status"], "reach": client["tool_reach"]}
        after = {"status": status, "reach": reach}
        if before == after:
            return "Nothing was changed. Use Confirm if the tool's answer is right."
        entry.update(before=before, after=after)
        store["overrides"][client["id"]] = {
            "before": before, "after": after, "by": by, "at": now,
            "note": note}
        store["items"][key] = {"state": "edited", "by": by, "at": now,
                               "note": note}
    elif action == "confirm":
        store["items"][key] = {"state": "confirmed", "by": by, "at": now,
                               "note": note}
    elif action == "resolve":
        store["items"][key] = {"state": "resolved", "by": by, "at": now,
                               "note": note}
    elif action == "reopen":
        store["items"].pop(key, None)
        if client:
            store["overrides"].pop(client["id"], None)
    else:
        return "Unknown action."
    store["log"].append(entry)
    save(agency, store)
    return ""


def apply(model):
    """Apply saved corrections to a freshly evaluated model and build the
    list of check items with their review state."""
    store = load(model["agency"])
    items = []
    for c in model["clients"]:
        c["tool_status"], c["tool_reach"] = c["status"], c["reach"]
        c["edited"] = None
        ov = store["overrides"].get(c["id"])
        if ov:
            now = {"status": c["status"], "reach": c["reach"]}
            if now != ov["before"]:
                c["flags"].append(
                    "A correction by %s on %s was made when the tool said "
                    "'%s / %s'. The files now give '%s / %s', so the "
                    "correction was not applied. Please check again." % (
                        ov["by"], ov["at"], ov["before"]["status"],
                        ov["before"]["reach"], c["status"], c["reach"]))
            else:
                a = ov["after"]
                if a["status"] != c["status"]:
                    c["status"] = a["status"]
                    if a["status"] == "stalled":
                        order = [s["n"] for s in model["sessions"]]
                        gone = len(order) >= 2 and all(
                            c["state"][n] == "absent" for n in order[-2:])
                        c["group"] = "call" if gone else "next"
                        c["why"] = rules.WHY_ATT if gone else rules.WHY_DIARY
                    else:
                        c["group"], c["why"] = "", rules.WHY_OK
                    c["why_short"] = c["why"]
                if a["reach"] != c["reach"]:
                    c["reach"] = a["reach"]
                    ch = c["contact"]
                    ch["dnc"] = a["reach"] == "do not contact"
                    ch["channel"] = a["reach"] if not ch["dnc"] else ch["channel"]
                    ch["by"], ch["limits"] = "reviewer", []
                    c["reach_unsure"] = False
                    c["reach_detail"] = (
                        "Asked for no contact between sessions"
                        if ch["dnc"] else {"paper": "letter or paper note"}.get(
                            a["reach"], a["reach"])) + \
                        " (set by %s, %s)" % (ov["by"], ov["at"])
                c["detail"] = "Changed by %s on %s: %s" % (ov["by"], ov["at"],
                                                         ov["note"])
                c["edited"] = ov
        for f in c["flags"]:
            k = key_for(c["id"], f)
            st = store["items"].get(k, {})
            items.append({"key": k, "kind": "client", "client_id": c["id"],
                          "name": c["name"], "counsellor": c["counsellor"],
                          "text": f, "state": st.get("state", "open"),
                          "by": st.get("by", ""), "at": st.get("at", ""),
                          "note": st.get("note", "")})
    for i in model["issues"]:
        k = key_for("issue", i)
        st = store["items"].get(k, {})
        items.append({"key": k, "kind": "issue", "client_id": "", "name": "",
                      "counsellor": "", "text": i,
                      "state": st.get("state", "open"), "by": st.get("by", ""),
                      "at": st.get("at", ""), "note": st.get("note", "")})
    model["summary"] = rules.summarise(model)
    model["review_items"] = items
    model["review_log"] = store["log"]
    return model


def write_log(model, out_dir):
    path = os.path.join(out_dir, "review-log.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["when", "reviewed_by", "action", "client_id", "name",
                    "status_before", "way_before", "status_after",
                    "way_after", "note", "what_was_flagged"])
        for e in model["review_log"]:
            b, a = e.get("before", {}), e.get("after", {})
            w.writerow([e["at"], e["by"], e["action"], e["client_id"],
                        e["name"], b.get("status", ""), b.get("reach", ""),
                        a.get("status", ""), a.get("reach", ""), e["note"],
                        e.get("what", "")])
    return path
