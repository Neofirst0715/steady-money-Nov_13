# Hand-off plan: Steady Money Progress Check

Zhenzhao (Neo) Li, November 13, 2026

## Who looks after it

| Who | What they do | Time |
|---|---|---|
| Counsellors at each agency (Maya and Joan at Cole Street) | Keep their own sheets as now. On Friday: run the tool, read the check list, print their sheet. They decide every contact; the tool sends nothing. | About 10 minutes a week each, on top of the 10 minutes of diary entry they already planned |
| The agency's director | Checks the one page against `results-detail.csv` and signs it before it leaves the agency. | About 15 minutes a group |
| Dana | Checks the arithmetic on each page. Calls the director first if the numbers look soft or she isn't sure. Owns `RULES.md` with Maya: what counts as "improved" and "stuck with it". | A 5-minute call a page |
| Tess | Sits with an agency for its first run. Collects what the check lists couldn't read. | Her 1 hour a month, no code |
| Nobody yet | Changing a rule or adding new wording means editing a Python file. Dana won't hire a developer, so this is unfilled. Until it is filled, the tool keeps working but doesn't learn new wording. | A few hours a quarter |

Names stay at the agency: the tool runs on the agency's own computer and uses no internet. Only the one page leaves, after the director signs.

## What it costs to run

$0 a month. No subscription, no AI service, no hosting. That is inside Dana's limit of $150 a month across all agencies, with no charge to agencies. One-off: Python 3 must be on the office computer. I have not seen an agency's computer, so that is unchecked.

## When it gets one wrong

| What happens | What to do |
|---|---|
| It isn't sure (most cases) | The item is on the check list. The counsellor confirms, edits or resolves it; the page records who and when, and works the results out again. |
| It can't read the files | It stops and writes nothing. Send the message on screen to Tess. Do not rename or retype the files to make it run. |
| It is wrong without saying so | The sheet shows which note each contact came from, so the counsellor can see it. Edit it in the check list, and tell Tess so the wording can be added. |
| A number on the one page is wrong | The director's check and Dana's check come before the page goes anywhere. |

The mistake that matters most is suggesting contact with someone who asked for none. A "no" about contact that the tool can't read is treated as do not contact and flagged. That can hold back a call that would have been fine.

## What it can't fix

- A preference nobody wrote down. One client's first-day "text" is out of date and isn't in the notes. The sheet prompts a private check at Money Check sessions.
- The diary page. One client said he doesn't know what goes where and nobody told him what it is for. That needs Dana and Tess to change the material.
- Whether the program works. The page adds up self-rated scores with no comparison group. I have not seen any funder's own wording.
- The halfway view. Session 6 is November 17; the final page needs those scores entered.
- Agencies on paper, layouts it hasn't seen, and an agency with nobody who can run one command. It has no logins: a reviewer's name is typed in.

## First steps after today

1. Maya and Joan each check their 24 clients against the results. Joan hasn't seen hers.
2. Maya sets the line for "improved". It is 3 points now, marked as proposed.
3. Cole Street's director reads the client notice: who sees this (your counsellor), where your name goes (nowhere), and whether anything will message you (no).
4. After session 6, Cole Street runs the final page. Dana checks it before her board meets on December 3.
5. A second agency's records need that agency's sign-off before Dana shows them to anyone.
