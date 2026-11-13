# How to run it

You need Python 3 (3.8 or newer). Nothing to install. No internet is used.

## Each time

1. Save the agency's zip (or folder) somewhere. Don't open or change the
   files. File names and column headings don't matter. `.csv`, `.xlsx`,
   `.txt` and `.md` are read.
2. Open Terminal, go to this folder, and run one line:

       python3 run.py "path/to/agency.zip"

   A folder works too: `python3 run.py "path/to/the agency folder"`.
   A zip is unpacked into a folder of the same name beside it.
3. The first lines printed are the agency name (taken from the file names)
   and the number of clients, then one line per client.
4. Open the new `out` folder inside the agency's folder:
   - `results.csv`: one row per client with exactly four columns:
     `client_id`, `status`, `way_to_reach`, `why`.
   - `friday-sheet-<counsellor>.html`: one per counsellor. Open and print.
   - `renewal-page.html`: the one page with no names. A draft until the
     director signs it.
   - `check-list.html`: how each file was read and what needs a person to
     look at. Read this first.
   - `results-detail.csv`: the same with names, the note each contact
     came from, and what to check. For staff only.

To print a page: open it in any browser, then File > Print.

## In a browser instead

    python3 app.py

A page opens at http://127.0.0.1:8765/. Choose the agency's zip or files
(or a sample), and the page shows the agency name and client count, the
results, each counsellor's Friday sheet, the one page and the check list.
It is the same tool as `run.py`: the page only displays what the Python
files work out. It answers on this computer only, and uses no internet.
Chosen files are copied into a `runs` folder beside `app.py`; delete that
folder when you are done, because it holds client names. Press Ctrl+C in
Terminal to stop.

### Checking what the tool flagged

The Check list view lists everything the tool couldn't settle. Type your
name in "Reviewed by", then for each item:

- **Confirm**: the tool's answer is right.
- **Edit**: change the status or the way to reach, with a note saying what
  you checked. Results, Friday sheets and the one page are worked out
  again straight away.
- **Resolve**: dealt with, nothing to change (a note is needed).
- **Reopen**: undo any of the above.

Every action is kept with who did it and when, and can be downloaded as
`review-log.csv`. Corrections are stored in a `reviews` folder beside
`app.py`. The agency's own files are never changed. `run.py` on the
command line ignores corrections: it always gives exactly what the files
and the rules say.

## If something looks wrong

- "STOPPED. No results were written": the tool couldn't find the
  attendance sheet, or couldn't read most of the notes. It says which.
  It stops on purpose: without the notes it can't know who asked not to
  be contacted. Nothing is written until that is fixed.
- A client is missing from a Friday sheet: check `check-list.html`. They
  may have asked for no contact, which keeps them off every sheet.
- A note wasn't used: the check list shows the line and why (no name
  found, or more than one client fits).
- A rule is wrong: see `RULES.md`.

## To check the tool itself

    python3 tests/run_tests.py

It runs the two sample agencies and a made-up third one against their
answer tables, rewrites Cole Street into five other layouts and expects
the same 48 answers, and checks the hard cases. All lines should say `ok`.

## What stays where

The pages with names are written inside the agency's own folder. Only
`renewal-page.html` is meant to leave the agency, and only after the
director signs it. The sample files in `samples/` are practice data:
don't post them anywhere public.
