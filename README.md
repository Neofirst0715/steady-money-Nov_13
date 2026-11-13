# Steady Money Progress Check

Reads one agency's files for the Steady Money six-session program and
writes:

- `results.csv`: one row per client: `client_id`, `status` (on track or
  stalled), `way_to_reach` (call, text, paper or do not contact), `why`.
- A Friday sheet for each counsellor: who to reach out to, who to talk to
  at the next session, and how to reach each person. Anyone who asked not
  to be contacted is left off.
- A one-page halfway view for the agency's renewal: how many started, how
  many took both Money Checks, how many improved. No client is named.
- A check list of everything the tool couldn't settle. It flags; it
  doesn't guess.

Built for Sprint 4 of Volta Anchor (November 9 to 13, 2026) by Zhenzhao
(Neo) Li. The client is simulated.

## Run it

Python 3.8 or newer. Nothing to install. No internet is used.

    python3 run.py "path/to/agency.zip"

A folder works too. The agency name (from the file names) and the client
count are printed first. Outputs go into an `out` folder beside the
agency's files. If most of the notes can't be read, the tool stops and
writes nothing.

In a browser, with the same logic and a review step:

    python3 app.py

Full steps are in [HOW-TO-RUN.md](HOW-TO-RUN.md).

## What it does not do

It sends no messages and contacts no one. It never changes the agency's
files. It does not prove the program works: it adds up self-rated scores
the agencies already hold. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Files

| File | What it is |
|---|---|
| `run.py` | The command-line run |
| `app.py`, `web/index.html` | The browser page |
| `read.py` | Recognises each file and column by what the cells contain |
| `match.py` | Matches a name in the notes or diaries to one client |
| `build.py` | Joins attendance, notes and diaries into one record per client |
| `rules.py` | The rules: stalled or on track, how to reach, the page totals |
| `render.py` | Writes the printable pages and `results.csv` |
| `review.py` | Confirm, edit or resolve a flag, with who and when (browser only) |
| `RULES.md` | Every rule in plain words, with who set it and when |
| `HOW-TO-RUN.md` | Steps to run it and what to do when it stops |
| `KNOWN_ISSUES.md` | Test results, judgment calls and limits |
| `HANDOFF.md` | Who looks after it, what it costs, what happens when it's wrong |
| `tests/` | `python3 tests/run_tests.py` runs 82 checks |
| `samples/` | Practice data: two sample agencies and three made-up ones |

## Test it

    python3 tests/run_tests.py

Every line should say `ok`. The tests cover the two sample agencies
against their marks, Cole Street rewritten into five other layouts, two
made-up agencies built to break the tool, the wording for "do not
contact", and the review step.

## Data

Everything in `samples/` is practice data for this sprint; the people are
not real. Don't post it anywhere public. The `runs/` and `reviews/`
folders are created when the browser page is used and hold client names:
keep them out of any repository (see `.gitignore`).
