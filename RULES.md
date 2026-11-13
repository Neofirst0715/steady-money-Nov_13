# Rules the tool follows

Every rule is here in plain words, with who set it and when. To change a
rule, change it here first, then in `rules.py`, then run
`python3 tests/run_tests.py`.

"Not confirmed" means the agency hasn't agreed to it yet. The tool still
gives an answer and says on the page that the rule is proposed.

## Who is stalled

| Rule | Set by | When |
|---|---|---|
| Stalled if the last two sessions were missed with no notice. | Maya's marks, all 48 | Nov 9 |
| Stalled if two weeks' diaries were set and not handed in. The two weeks need not be next to each other. | Maya's marks, all 48 | Nov 9 |
| One missed session on its own is not stalled. | Maya | Nov 10 |
| Away with notice is not stalled. It lasts for the dates the client gave. | Maya | Nov 9, 10 |
| Diary on hold is not counted. It ends only when a note says the diary is back on; until then it is flagged for the counsellor. | Maya | Nov 9, 10 |
| A week where the note says the diary was skipped or time ran out is not counted. | Maya | Nov 10 |
| A week where the note says nothing about the diary counts as set. Anyone whose place depends on such a week is flagged. | Maya | Nov 10 |
| Late counts as present. | Maya | Nov 10 |
| A diary that isn't entered yet (blank, "not typed yet") is not a missed diary. It is flagged. | Bayfield sample; Maya on entry | Nov 9 |
| Stalled on diaries, then a diary comes back: on track again, marked "just back" for the counsellor to look at. | Maya ("my gut, not a rule") | Nov 10, not confirmed |

## How to reach someone

| Rule | Set by | When |
|---|---|---|
| The newest note beats the first-day contact column. | Maya | Nov 9 |
| Anyone who asked for no contact between sessions never appears on a Friday sheet. | Maya | Nov 9 |
| A first-day contact with no newer note is shown as "first-day sheet, not confirmed since". | Maya | Nov 10 |
| "The client asked for it" and "it was all the counsellor had left" are kept apart. A letter set after a dead number on a day the client was absent is "not confirmed by client". | Maya | Nov 10 |
| Nothing is suggested for someone whose only way was not agreed by them. They go in "Your decision first". | Maya ("I'd rather hold off than guess") | Nov 10 |
| Limits are kept with the method: evenings only, daytime only, no texts, no voicemail. The reason is never printed. | Maya, Ray | Nov 9, 10 |
| The sheet shows no money details and nothing about home. | Ray, Maya | Nov 9 |
| At a Money Check session the sheet reminds the counsellor to ask each person privately how to reach them. | Ray | Nov 9 |
| Wording about contact that the tool doesn't know is flagged with the sentence. It is never guessed. | Dana, Maya | Nov 10, 11 |
| A "no" about contact that the tool can't read is treated as do not contact, and flagged. A wrong "do not contact" costs one call; a wrong call can do harm. | Proposed, from Maya's "I'd rather hold off than guess" | Nov 12 |
| A no-contact note that fits more than one client marks each of them do not contact until someone checks. | Proposed | Nov 12 |
| `results.csv` gives one of four ways: call, text, paper, do not contact. If the number is dead and nothing else is on file it says paper; the Friday sheet still suggests nothing and asks the counsellor to decide. | Friday's scoring note; proposed fallback | Nov 12 |

## The Friday sheet

| Rule | Set by | When |
|---|---|---|
| One sheet per counsellor. | Maya | Nov 9 |
| People who have stopped coming are in "Reach out this week". | Maya | Nov 10 |
| People who still come but haven't handed in diaries are in "Talk at the next session", with no call. | Maya | Nov 10 |
| Each line shows: who, last session attended, why, how to reach them, which note that came from and whether it's confirmed. | Maya | Nov 10 |
| The tool sends nothing. It only prints. | Ray, sprint scope | Nov 9 |

## The renewal page

| Rule | Set by | When |
|---|---|---|
| No names. Whole-group totals only. | Maya, Ray, intake form | Nov 9 |
| Started: everyone on the attendance sheet. | Friday's scoring note | Nov 12 |
| Took both Money Checks: has a score at the first and the latest check. | Friday's scoring note | Nov 12 |
| Stuck with it: has not missed the last two sessions without notice. Based on attendance, not diaries. | Maya gave the direction; wording proposed | Nov 10, not confirmed |
| Improved: Money Check up by 3 points or more. A rise of 1 or 2 is shown but not counted, because one point is too easy. | Dana and Ray on "too easy"; the line is Maya's to set | Nov 9, 11, not confirmed |
| Compare the first and the latest Money Check, chosen before looking at results. The page says which two. | Dana | Nov 11 |
| Someone with no latest score is "not known". An earlier score is never used in its place, and nobody is dropped from the totals. | Dana | Nov 11 |
| The full spread of score changes is printed, so the line can be checked. | Dana, Maya | Nov 9, 11 |
| The page says scores are self-rated, that it is a halfway view until session 6, and that it can't be compared with another agency. | Ray; Dana (no scoring guide) | Nov 9, 11 |
| Groups under 10 carry a warning that totals could point to a person. | Proposed, from Maya's "nothing small enough to point at anyone" | not confirmed |
| One folder is one group and one page. | Proposed | not confirmed |
| It is a draft until the director signs. Dana checks the arithmetic and calls the director first if unsure. | Maya, Dana | Nov 9, 11 |

## Matching names across files

| Rule | Set by | When |
|---|---|---|
| A name in the notes or diary sheet is matched by counsellor plus first name (and surname or initial if given). | Proposed | Nov 9 |
| Short forms are accepted (Ray/Raymond, Liz/Elizabeth, Bill/William). The list is in `match.py`. | Proposed | Nov 9 |
| If more than one client fits, or none, the line is listed on the check list and not used. | Maya, Dana | Nov 10, 11 |

## When the tool stops

| Rule | Set by | When |
|---|---|---|
| If no notes are found, or most of them can't be read, the tool stops and writes nothing. Without notes it can't know who asked for no contact. | Friday's scoring note | Nov 12 |
| "Most" means: fewer than 6 in 10 note lines matched to a client, or fewer notes than a quarter of the attended sessions. | Proposed | Nov 12 |
