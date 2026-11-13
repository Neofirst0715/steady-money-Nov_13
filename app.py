#!/usr/bin/env python3
"""Steady Money Progress Check: the same tool as run.py, in a browser.

    python3 app.py

Opens a page on this computer only (127.0.0.1). Files you choose are
copied into the 'runs' folder beside this file and read there. Nothing is
sent anywhere and no network is used.
"""
import base64
import datetime as dt
import json
import os
import re
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build   # noqa: E402
import render  # noqa: E402
import review  # noqa: E402
import rules   # noqa: E402
import run as cli  # noqa: E402

RUNS = os.path.join(HERE, "runs")
SAMPLES = {"cole_street": "Cole Street", "bayfield": "Bayfield"}
TYPES = {".html": "text/html; charset=utf-8", ".csv": "text/csv; charset=utf-8"}


def _safe(name):
    return re.sub(r"[^A-Za-z0-9 ._()\-]", "_", os.path.basename(name)) or "file"


def do_review(body):
    """Save one review action, then work everything out again."""
    folder = body.get("folder") or ""
    if not os.path.isdir(folder):
        return {"error": "The files for this run are no longer there. "
                         "Import them again."}
    try:
        model = build.assemble(folder)
    except build.CannotRead as e:
        return {"error": str(e)}
    rules.evaluate(model)
    review.apply(model)
    client = next((c for c in model["clients"]
                   if c["id"] == body.get("client_id")), None)
    item = next((i for i in model["review_items"]
                 if i["key"] == body.get("key")), None)
    if body.get("action") == "edit" and client is None:
        return {"error": "That client isn't in these files."}
    err = review.record(model["agency"], body.get("action"),
                        body.get("key") or "", body.get("by"),
                        body.get("note"), client, body.get("status"),
                        body.get("reach"), item["text"] if item else "")
    if err:
        return {"error": err}
    return do_run({"path": folder})


def _client(c, model):
    ch = c["contact"]
    return {
        "id": c["id"], "name": c["name"], "counsellor": c["counsellor"],
        "status": c["status"], "why": c["why"], "detail": c["detail"],
        "reach": c["reach"], "reach_detail": c["reach_detail"],
        "group": c["group"], "dnc": ch["dnc"],
        "decide": ch["by"] == "counsellor" or bool(c.get("reach_unsure")),
        "day_one": ch["by"] == "day one",
        "phone": c["phone"] if ch["channel"] in ("call", "text")
        and not ch["dnc"] else "",
        "last_seen": render._seen(c, model), "flags": c["flags"],
        "just_back": c.get("just_back", False),
        "tool_status": c["tool_status"], "tool_reach": c["tool_reach"],
        "edited": bool(c["edited"]),
    }


def do_run(body):
    extra_note = ""
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    n = 1
    while os.path.exists(os.path.join(RUNS, "%s-%d" % (stamp, n))):
        n += 1                       # every run gets its own empty folder
    stamp = "%s-%d" % (stamp, n)
    work = os.path.join(RUNS, stamp)
    os.makedirs(work)
    if body.get("sample") in SAMPLES:
        folder = os.path.join(HERE, "samples", body["sample"])
    elif body.get("path"):
        folder = os.path.expanduser(body["path"].strip().strip('"'))
        if os.path.isfile(folder) and folder.lower().endswith(".zip"):
            folder = cli.unzip(folder)
        if not os.path.isdir(folder):
            return {"stopped": "Folder or zip not found: %s" % folder}
    else:
        files = body.get("files") or []
        if not files:
            return {"stopped": "No files were chosen."}
        folder = os.path.join(work, "files")
        os.makedirs(folder, exist_ok=True)
        for f in files:
            with open(os.path.join(folder, _safe(f["name"])), "wb") as out:
                out.write(base64.b64decode(f["data"]))
        zips = [f for f in os.listdir(folder) if f.lower().endswith(".zip")]
        if len(zips) > 1:
            return {"stopped": "You chose %d zip files (%s). Each zip is one "
                               "agency, and the tool reads one agency at a "
                               "time. Choose just one zip and try again." %
                               (len(zips), ", ".join(sorted(zips)))}
        if len(zips) == 1:
            folder = cli.unzip(os.path.join(folder, zips[0]))
            others = [f["name"] for f in files
                      if not f["name"].lower().endswith(".zip")]
            if others:
                extra_note = ("Only the zip was read. These other files "
                              "you chose were left out: %s." %
                              ", ".join(others))
    try:
        model = build.assemble(folder)
    except build.CannotRead as e:
        return {"stopped": str(e)}
    if extra_note:
        model["issues"].insert(0, extra_note)
    rules.evaluate(model)
    review.apply(model)
    out = os.path.join(work, "out")
    made = render.write_all(model, out, dt.date.today())
    made.append(review.write_log(model, out))
    cs = model["clients"]
    s = dict(model["summary"])
    s["dist"] = sorted(s.get("dist", {}).items())
    s["line"] = rules.BETTER_OFF_MIN_POINTS
    s["line_confirmed"] = rules.BETTER_OFF_CONFIRMED
    ss = model["sessions"]
    n_next, d_next = render._next_session(model)
    return {
        "run": stamp, "agency": model["agency"], "clients_n": len(cs),
        "sessions": len(ss), "last_session": ss[-1]["n"],
        "first_date": render._fmt(ss[0]["date"]) if ss[0]["date"] else "",
        "last_date": render._fmt(ss[-1]["date"], True) if ss[-1]["date"]
        else "",
        "next_session": n_next,
        "next_date": render._fmt(d_next) if d_next else "",
        "money_check_next": n_next in render.MONEY_CHECK_SESSIONS,
        "clients": [_client(c, model) for c in cs],
        "summary": s, "log": model["log"], "issues": model["issues"],
        "items": model["review_items"], "review_log": model["review_log"],
        "files": [os.path.basename(p) for p in made],
        "folder": folder, "out": out,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ctype, data):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(HERE, "web", "index.html"), "rb") as f:
                return self._send(200, TYPES[".html"], f.read())
        m = re.fullmatch(r"/out/(\d{8}-\d{6}-\d+)/([A-Za-z0-9._\-]+)", path)
        if m:
            p = os.path.join(RUNS, m.group(1), "out", m.group(2))
            ext = os.path.splitext(p)[1]
            if os.path.isfile(p) and ext in TYPES:
                with open(p, "rb") as f:
                    return self._send(200, TYPES[ext], f.read())
        self._send(404, "text/plain", b"Not found")

    def do_POST(self):
        if self.path not in ("/run", "/review"):
            return self._send(404, "text/plain", b"Not found")
        n = int(self.headers.get("Content-Length") or 0)
        if n > 80 * 1024 * 1024:
            return self._send(413, "text/plain", b"Too large")
        try:
            body = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            res = do_review(body) if self.path == "/review" else do_run(body)
        except Exception as e:      # show the reason instead of hanging
            res = {"stopped": "The tool hit an error and wrote nothing: "
                              "%s: %s" % (type(e).__name__, e)}
        self._send(200, "application/json; charset=utf-8",
                   json.dumps(res).encode("utf-8"))


def main():
    nums = [a for a in sys.argv[1:] if a.isdigit()]
    port = int(nums[0]) if nums else 8765
    for p in range(port, port + 20):
        try:
            srv = HTTPServer(("127.0.0.1", p), Handler)
            break
        except OSError:
            continue
    else:
        sys.exit("No free port found near %d." % port)
    url = "http://127.0.0.1:%d/" % p
    print("Steady Money Progress Check is running at %s" % url)
    print("It only answers on this computer. Press Ctrl+C to stop.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
