# Known issues and limits

## Test results (Nov 12)

A client is right when `status` and `way_to_reach` both match.

- Cole Street: 48 of 48 match Maya's marks. Best case: the rules were
  written from these files and her marks.
- Bayfield: 6 of 6 match the official marks, received after the rules
  were written. The reasons match too.
- Cole Street rewritten into five other layouts (client blocks with
  day-first dates, dashes with "Doucette, R." and counsellor initials,
  session numbers with client numbers, date headings with the note on the
  next line, different sheets): 48 of 48 each. Two of these failed on the
  first try: "Counsellor: Joan Fraser" was read as client Keith Fraser,
  and "Phone bill" was read as a client called Bill. Both are fixed and
  now tested.
- Made-up third agency: 16 of 16. I wrote it myself, so it only tests
  what I thought of.
- Two made-up agencies built to break it (`tests/make_fake.py`, files in
  `samples/fake_northgate` and `samples/fake_harbour_hill`). On the first
  run the tool STOPPED on both and wrote nothing: one kept first name and
  surname in two columns, the other wrote "SURNAME, First" and kept notes
  in a table by session number. After fixes:
  - Northgate (15 clients, Friday-like): 15 of 15.
  - Harbour Hill (20 hard cases): 13 of 13 clear cases; 4 of the 7
    judgment calls match my reading. No no-contact client comes out with
    a way to reach them. Before the fixes two did ("DNC" written as an
    abbreviation, and "no more calls, texts or letters").
  I wrote these files and then fixed the tool against them, so they are
  now a regression test, not a blind test.
- 73 checks pass in `tests/run_tests.py`.

No agency's files written by someone else, in a layout I haven't seen,
have been run yet. Friday's is the first.

## Not confirmed by the agency

- "Better off" at 3 points. Maya sets the line.
- The wording of "started" and "stuck with it".
- Joan has not checked her 24. The tool matches Maya's marks for them,
  and Maya said her marks aren't the last word on Joan's half.
- A returned diary putting someone back on track ("my gut, not a rule").
- Whether Keith agreed to letters. Shown as not confirmed by client.

## Judgment calls the tool makes (Harbour Hill)

- Initials that fit two clients on a no-contact note: both are marked do
  not contact until someone checks. One of them is wrong by design.
- The register says absent but a note reads as if they came: the register
  is used and the conflict is flagged.
- Missed the last two sessions but rang ahead for one: not stalled.
- "On hold for one week" with no note that it's back on: still on hold,
  flagged.
- A first-day contact of "Email": `way_to_reach` falls back to call,
  flagged, because the results file allows only four values.

## Review in the browser page

- Confirm, Edit, Resolve and Reopen work, with the reviewer's name and the
  time recorded. Anyone can type any name: there are no logins.
- An edit is kept per client. If the files later change so the tool gives
  a different answer, the old edit is not applied and the client is
  flagged again.
- Edits change status and way to reach only. They can't correct a name
  match, an attendance mark or a score; for those, fix the agency's own
  record and run again.
- No second-person sign-off, and no versions of the rules or of each
  import.

## What it can't do

- It can't know a preference nobody wrote down. Ray's first-day "text" is
  still what the records say; Maya will ask him and write it in her notes.
- It reads contact wording by fixed patterns. New wording is flagged with
  the sentence, not understood. An ordinary sentence that happens to use
  a word like "letter" can be flagged too.
- A "no" about contact that it can't read is treated as do not contact.
  That can mark someone do not contact who only said "did not call the
  bank". It is flagged so a person can undo it.
- If a no-contact note can't be matched to any client, the tool can only
  warn at the top of the check list. It can't know who it was.
- A notes layout it has never seen may still defeat it. Then it stops and
  writes nothing, which scores zero on Friday but suggests no wrong call.
- Notes with no date, or a first name that fits two clients of the same
  counsellor, are listed and not used.
- Dates like 03/04 are read day-first or month-first, whichever gives
  weekly sessions; if neither does, month first. The check list says so.
- It doesn't read PDF, Word or paper. `.xlsx` reading is written but has
  not been tested on a real file.
- If the notes start later than session 1, session dates may line up
  wrongly. The check list says when the counts differ.
- It doesn't yet show "last week's calls: how many came back". That needs
  last week's sheet to be kept.
- One folder is one group. It doesn't add groups together for a year.
- It has been run with Python 3.10 and 3.13 on Linux. It has not been run
  on an agency's office computer.
