"""Two made-up agencies for testing. Nobody here is real.

northgate  15 clients. The same kinds of event as Cole Street and
           Bayfield, but a new layout and a third person's wording.
           This is the nearest thing to Friday's files.
harbour    20 clients. Edge cases chosen to break the tool. Some have
           no single right answer; those are marked "judgment".

Each KEY row: client id -> (status, way_to_reach, what the case tests).
"""
import csv
import os
import sys

# ------------------------------------------------------------ Northgate
N_DATES = ["Tuesday 6 October 2026", "Tuesday 13 October 2026",
           "Tuesday 20 October 2026", "Tuesday 27 October 2026"]
DR, HA = "Devon Ross", "Hana Aziz"
STD = "Went through the month's outgoings. Diary given out."
# ref, last, first, advisor, tel, contact by, marks, mc1, mc2, diary wk1-3
N_ROWS = [
 ("N01", "Nasser", "Farah", DR, "902-555-6001", "Text", "Y Y Y Y", 11, 15, "Y Y Y"),
 ("N02", "Bell", "Marcus", DR, "902-555-6002", "Phone", "Y Y Y Y", 12, 12, "Y N N"),
 ("N03", "Okafor", "Grace", HA, "902-555-6003", "Text", "Y Y N N", 14, "", "Y N "),
 ("N04", "Whitby", "Tom", HA, "902-555-6004", "Phone", "Y Y N N", 10, "", "Y N "),
 ("N05", "Haddad", "Lina", DR, "902-555-6005", "Text", "Y Y Y Y", 9, 13, "Y N N"),
 ("N06", "Cho", "Peter", DR, "902-555-6006", "Post", "Y Y Y Y", 15, 16, "N N N"),
 ("N07", "Mills", "Sandra", HA, "902-555-6007", "Text", "Y Y Y Y", 13, 17, "Y Y Y"),
 ("N08", "Yusuf", "Ahmed", HA, "902-555-6008", "Text", "Y Y Y Y", 12, 13, "Y N N"),
 ("N09", "Kowalski", "Rita", DR, "902-555-6009", "Phone", "Y Y N N", 11, "", "Y N "),
 ("N10", "Marsh", "Joe", DR, "902-555-6010", "Text", "Y Y Y Y", 10, 14, "Y Y Y"),
 ("N11", "Fraser", "Bill", HA, "902-555-6011", "Phone", "Y Y Y Y", 16, 18, "Y Y N"),
 ("N12", "Santos", "Maria", DR, "902-555-6012", "Text", "Y Y Y Y", 12, 16, "Y Y Y"),
 ("N13", "Silva", "Maria", DR, "902-555-6013", "Phone", "Y Y Y Late", 13, 13, "Y Y N"),
 ("N14", "Mensah", "Kofi", HA, "902-555-6014", "Phone", "Y N Y Y", 8, 12, "Y  Y"),
 ("N15", "Price", "Dawn", HA, "902-555-6015", "Text", "Y Y Y Y", 14, 19, "Y N not entered"),
]
# (session index, "Last, First" as written, advisor, text[, extra line])
N_NOTES = [
 (0, "Nasser, Farah", DR, STD), (1, "Nasser, Farah", DR, STD), (2, "Nasser, Farah", DR, STD), (3, "Nasser, Farah", DR, "Money Check done."),
 (0, "Bell, Marcus", DR, STD),
 (1, "Bell, Marcus", DR, "Talked about the grace period on his phone bill. Diary given out.", "Grace period ends Friday, he will ring them himself."),
 (2, "Bell, Marcus", DR, STD), (3, "Bell, Marcus", DR, "Money Check done. Bill payment plan agreed."),
 (0, "Okafor, Grace", HA, STD), (1, "Okafor, Grace", HA, STD),
 (0, "Whitby, Tom", HA, STD),
 (1, "Whitby, Tom", HA, "Said he'll be away the next two Tuesdays for work and let me know in advance. Diary paused till he's back."),
 (0, "Haddad, Lina", DR, STD),
 (1, "Haddad, Lina", DR, "Ran over time on the rent arrears letter so no diary handed out."),
 (2, "Haddad, Lina", DR, STD), (3, "Haddad, Lina", DR, "Money Check done."),
 (0, "Cho, Peter", DR, "Diary on hold while he's in hospital for tests, agreed."),
 (1, "Cho, Peter", DR, "Short session. Diary still on hold."),
 (2, "Cho, Peter", DR, "Feeling better. Diary restarted this week."), (3, "Cho, Peter", DR, "Money Check done."),
 (0, "Mills, Sandra", HA, STD), (1, "Mills, Sandra", HA, STD),
 (2, "Mills, Sandra", HA, "Told me she shares the mobile with her partner. Please don't text. Ringing after 6pm is fine. Diary given out."),
 (3, "Mills, Sandra", HA, "Money Check done."),
 (0, "Yusuf, Ahmed", HA, STD), (1, "Yusuf, Ahmed", HA, STD), (2, "Yusuf, Ahmed", HA, STD),
 (3, "Yusuf, Ahmed", HA, "Money Check done. Has asked that we don't contact him at all between sessions - he'll come in."),
 (0, "Kowalski, Rita", DR, STD), (1, "Kowalski, Rita", DR, STD),
 (3, "Kowalski, Rita", DR, "Didn't attend. Tried her phone - number not recognised. Will write to her instead."),
 (0, "Marsh, Joe", DR, STD),
 (1, "Marsh, Joe", DR, "Shared phone at home - no texts, evening calls OK. Diary given out."),
 (2, "Marsh, Joe", DR, STD),
 (3, "Marsh, Joe", DR, "Money Check done. Got his own mobile now, happy with texts."),
 (0, "Fraser, Bill", HA, STD), (1, "Fraser, Bill", HA, STD), (2, "Fraser, Bill", HA, STD), (3, "Fraser, Bill", HA, "Money Check done."),
 (0, "Santos, Maria", DR, STD), (1, "Maria S.", DR, "Budget sheet done. Diary given out."),
 (2, "Santos, Maria", DR, STD), (3, "Santos, Maria", DR, "Money Check done."),
 (0, "Silva, Maria", DR, STD), (1, "Silva, Maria", DR, STD), (2, "Silva, Maria", DR, STD),
 (3, "Silva, Maria", DR, "Arrived late. Money Check done."),
 (0, "Mensah, Kofi", HA, STD), (2, "Mensah, Kofi", HA, STD),
 (3, "Mensah, Kofi", HA, "Money Check done. Phone's been cut off; letters only for the time being."),
 (0, "Price, Dawn", HA, STD), (1, "Price, Dawn", HA, STD),
 (2, "Price, Dawn", HA, "Would rather a call than a text from now on. Diary given out."),
 (3, "Price, Dawn", HA, "Money Check done."),
]
N_KEY = {
 "N01": ("on track", "text", "plain case"),
 "N02": ("stalled", "call", "two diary weeks; 'Grace period' and 'Bill payment' in his notes are not clients"),
 "N03": ("stalled", "text", "missed last two, no notice"),
 "N04": ("on track", "call", "away 'the next two Tuesdays', told in advance; diary 'paused'"),
 "N05": ("on track", "text", "'no diary handed out' = homework not set"),
 "N06": ("on track", "paper", "diary on hold, then 'restarted': only week 3 counts"),
 "N07": ("on track", "call", "'shares the mobile', 'please don't text', 'ringing after 6pm'"),
 "N08": ("stalled", "do not contact", "'asked that we don't contact him at all'"),
 "N09": ("stalled", "paper", "'number not recognised', 'will write to her instead'"),
 "N10": ("on track", "text", "shared phone, then 'own mobile now, happy with texts'"),
 "N11": ("on track", "call", "a client called Bill while other notes say 'phone bill'"),
 "N12": ("on track", "text", "'Maria S.' fits two clients: must not be guessed"),
 "N13": ("on track", "call", "Late counts as present"),
 "N14": ("on track", "paper", "one missed session; blank diary cell; 'phone's been cut off; letters only'"),
 "N15": ("on track", "call", "'not entered' diary; 'would rather a call than a text'"),
}
N_JUDGMENT = set()

# ------------------------------------------------------------ Harbour Hill
JT, AS = "Jordan Tate", "Amy Stone"
H_STD = "Looked at the bills due this month and agreed next steps. Homework set."
# ref, "SURNAME, First", worker, tel, contact, 4 marks, mc a, mc b, diary
H_ROWS = [
 ("H01", "ADAMS, Ruth", JT, "902-555-8001", "SMS", "✓ ✓ ✓ ✓", 12, 14, "✓ ✓ ✓"),
 ("H02", "BAKER, Leon", JT, "902-555-8002", "Call", "✓ ✓ ✓ ✓", 10, 13, "✓ ✓ ✓"),
 ("H03", "CLARKE, Nina", AS, "902-555-8003", "SMS", "✓ ✓ ✓ ✓", 13, 13, "✓ ✓ ✓"),
 ("H04", "DIAZ, Elena", AS, "902-555-8004", "SMS", "✓ ✓ ✓ ✓", 9, 15, "✓ ✓ ✓"),
 ("H05", "EVANS, Carys", JT, "902-555-8005", "Call", "✓ ✓ ✓ ✓", 15, 16, "✓ ✓ ✓"),
 ("H06", "FORD, Dean", JT, "902-555-8006", "Letter", "✓ ✓ ✓ ✓", 11, 16, "✓ ✓ ✓"),
 ("H07", "GREEN, Priya", AS, "902-555-8007", "Call", "✓ ✓ ✓ ✓", 12, 12, "✓ ✓ ✓"),
 ("H08", "HALL, Simone", AS, "902-555-8008", "Call", "✓ ✓ ✓ ✓", 14, 18, "✓ ✓ ✓"),
 ("H09", "IBRAHIM, Sami", JT, "902-555-8009", "SMS", "✓ ✓ ✓ ✓", 8, 11, "✓ ✓ ✓"),
 ("H10", "JONES, Megan", JT, "", "Email", "✓ ✓ ✓ ✓", 13, 17, "✓ ✓ ✓"),
 ("H11", "KHAN, Tariq", AS, "902-555-8011", "Call", "✓ ✓ ✗ ✗", 10, "", "✓ ✗ "),
 ("H12", "LEWIS, Hope", AS, "902-555-8012", "Call", "✓ ✗ ✗ ✗", 9, "", "  "),
 ("H13", "MOORE, Faith", JT, "902-555-8013", "SMS", "✓ ✓ ✓ ✓", 12, 15, "✗ ✗ ✓"),
 ("H14", "NOLAN, Rory", JT, "902-555-8014", "SMS", "✓ ✓ ✓ ✓", 11, 11, "✗ ✗ ✗"),
 ("H15", "OWENS, Mark", AS, "902-555-8015", "Call", "✓ ✓ ✓ ✓", 14, 16, "✗ ✗ ✓"),
 ("H16", "GRANT, Will", AS, "902-555-8016", "SMS", "✓ ✓ ✓ ✓", 13, 14, "✓ ✓ ✓"),
 ("H17", "GALE, Wendy", AS, "902-555-8017", "Call", "✓ ✓ ✓ ✓", 12, 17, "✓ ✓ ✓"),
 ("H18", "PIKE, Jordan", JT, "902-555-8018", "Call", "✓ ✓ ✓ ✓", 10, 14, "✓ ✗ ✗"),
 ("H19", "QUINN, Amy", JT, "902-555-8019", "No contact", "✓ ✓ ✓ ✓", 15, 15, "✓ ✓ ✓"),
 ("H20", "REID, Stone", AS, "902-555-8020", "SMS", "✓ ✓ ✗ ✗", 11, "", "✓ ✗ "),
]
# when (session number, or a between-session date), who as written, by, note
H_NOTES = [
 (1, "Ruth A.", "JT", H_STD), (2, "Ruth A.", "JT", H_STD), (3, "Ruth A.", "JT", H_STD),
 (4, "Ruth A.", "JT", "Money Check. DNC between sessions (her request)."),
 (1, "Leon B.", "JT", H_STD), (2, "Leon B.", "JT", H_STD),
 (3, "Leon B.", "JT", "Homework set. Prefers we leave him be until he's next in."),
 (1, "Nina C.", "AS", H_STD),
 (2, "Nina C.", "AS", "Has not called the bank about the overdraft yet. Homework set."),
 (3, "Nina C.", "AS", H_STD),
 (1, "Elena D.", "AS", H_STD),
 (2, "Elena D.", "AS", "No contact between sessions please. Homework set."),
 (3, "Elena D.", "AS", H_STD),
 (4, "Elena D.", "AS", "Money Check. Says it's fine to ring her again now."),
 (1, "Carys E.", "JT", H_STD), (2, "Carys E.", "JT", H_STD),
 ("Thu 15 Oct", "Carys E.", "JT", "Rang in: please no more calls, texts or letters. Will come when she can."),
 (3, "Carys E.", "JT", H_STD),
 (1, "Dean F.", "JT", H_STD),
 (2, "Dean F.", "JT", "Txt is fine now, has his own phone. Homework set."),
 (3, "Dean F.", "JT", H_STD),
 (1, "Priya G.", "AS", H_STD),
 (2, "Priya G.", "AS", "Do not ring - text only. Homework set."),
 (3, "Priya G.", "AS", H_STD),
 (1, "Simone H.", "AS", H_STD),
 (2, "Simone H.", "AS", "OK to leave a voicemail on the landline; the mobile is her son's. Homework set."),
 (3, "Simone H.", "AS", H_STD),
 (1, "Sami I.", "JT", "Shares a phone; calls in the evening only, no texts. Homework set."),
 (2, "Sami I.", "JT", "Own phone now, text is fine. Homework set."),
 (3, "Sami I.", "JT", H_STD),
 (4, "Sami I.", "JT", "Money Check. Phone disconnected. Letter only."),
 (1, "Megan J.", "JT", H_STD), (2, "Megan J.", "JT", H_STD), (3, "Megan J.", "JT", H_STD),
 (1, "Tariq K.", "AS", H_STD), (2, "Tariq K.", "AS", H_STD),
 (3, "Tariq K.", "AS", "Absent. Rang ahead - child off sick."),
 (1, "Hope L.", "AS", H_STD),
 (1, "Faith M.", "JT", H_STD), (2, "Faith M.", "JT", H_STD), (3, "Faith M.", "JT", H_STD),
 (1, "Rory N.", "JT", "Diary on hold for one week (exams)."),
 (2, "Rory N.", "JT", H_STD), (3, "Rory N.", "JT", H_STD),
 (1, "Mark O.", "AS", "Forgot to hand out the diary sheet."),
 (2, "Mark O.", "AS", "HW not given, ran over."),
 (3, "Mark O.", "AS", H_STD),
 (1, "WG", "AS", H_STD), (2, "Will G.", "AS", H_STD), (3, "Wendy G.", "AS", H_STD),
 (4, "WG", "AS", "Money Check. Asked for no calls, no texts, no mail between sessions."),
 (1, "Jordan P.", "JT", H_STD),
 (2, "Jordan P.", "AS", "Covering for JT today. Homework set."),
 (3, "Jordan P.", "JT", H_STD),
 (1, "Amy Q.", "JT", H_STD), (2, "Amy Q.", "JT", H_STD), (3, "Amy Q.", "JT", H_STD),
 (1, "Stone R.", "AS", H_STD), (2, "Stone R.", "AS", H_STD),
 (4, "Stone R.", "AS", "Came 40 minutes late, did the Money Check. Register not updated."),
]
H_KEY = {
 "H01": ("on track", "do not contact", "'DNC' as an abbreviation"),
 "H02": ("on track", "do not contact", "'prefers we leave him be'"),
 "H03": ("on track", "text", "'has not called the bank' is about her, not about us contacting her"),
 "H04": ("on track", "call", "no contact, later lifted: 'fine to ring her again now'"),
 "H05": ("on track", "do not contact", "no-contact request made by phone on a day with no session"),
 "H06": ("on track", "text", "'Txt is fine now, has his own phone' (was Letter)"),
 "H07": ("on track", "text", "'Do not ring - text only'"),
 "H08": ("on track", "call", "voicemail OK on landline; nothing changes the method"),
 "H09": ("on track", "paper", "three changes: shared phone, own phone, then disconnected"),
 "H10": ("on track", "call", "first-day 'Email' is not one of the four values"),
 "H11": ("on track", "call", "missed last two, but rang ahead for one of them"),
 "H12": ("stalled", "call", "came once, then three absences and no notes"),
 "H13": ("on track", "text", "two missed diaries, then one handed in"),
 "H14": ("on track", "text", "'on hold for one week', never marked as back on"),
 "H15": ("on track", "call", "'forgot to hand out the diary', 'HW not given'"),
 "H16": ("on track", "text", "initials 'WG' fit two clients; the no-contact note can't be placed"),
 "H17": ("on track", "call", "same: 'WG'"),
 "H18": ("stalled", "call", "client Jordan, counsellor Jordan; a note written by the other counsellor"),
 "H19": ("on track", "do not contact", "first-day column itself says 'No contact'"),
 "H20": ("on track", "text", "register says absent, the note says she came"),
}
H_JUDGMENT = {"H10", "H11", "H13", "H14", "H16", "H17", "H20"}


def make_northgate(folder):
    os.makedirs(folder, exist_ok=True)
    p = lambda n: os.path.join(folder, n)
    with open(p("Northgate_Neighbours_register.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ref", "Last name", "First name", "Advisor", "Tel",
                    "Contact by", "Wk1 06-Oct", "Wk2 13-Oct", "Wk3 20-Oct",
                    "Wk4 27-Oct", "Money Check 1", "Money Check 2"])
        for ref, last, first, adv, tel, way, marks, a, b, _ in N_ROWS:
            w.writerow([ref, last, first, adv, tel, way] + marks.split(" ")
                       + [a, b])
    with open(p("Northgate_Neighbours_session_log.txt"), "w") as f:
        f.write("NORTHGATE NEIGHBOURS - STEADY MONEY SESSION LOG\n")
        for i, d in enumerate(N_DATES):
            f.write("\n%s\n" % d)
            for adv in (DR, HA):
                f.write("Advisor: %s\n" % adv)
                for n in N_NOTES:
                    if n[0] == i and n[2] == adv:
                        f.write("  %s — %s\n" % (n[1], n[3]))
                        if len(n) > 4:
                            f.write("      %s\n" % n[4])
    with open(p("Northgate_Neighbours_diary_returns.csv"), "w",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ref", "Wk", "Diary back?", "Days"])
        for row in N_ROWS:
            cells = row[9].split(" ", 2)
            for wk, v in enumerate(cells, 1):
                w.writerow([row[0], wk, v, "4" if v == "Y" else ""])


def make_harbour(folder):
    os.makedirs(folder, exist_ok=True)
    p = lambda n: os.path.join(folder, n)
    with open(p("harbour-hill attendance.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["#", "Client (SURNAME, First)", "Worker", "Phone",
                    "How to reach", "S1", "S2", "S3", "S4", "Check A",
                    "Check B"])
        for ref, name, wk, tel, way, marks, a, b, _ in H_ROWS:
            w.writerow([ref, name, wk, tel, way] + marks.split(" ") + [a, b])
    with open(p("harbour-hill notes.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["When", "Who", "By", "Note"])
        for when, who, by, text in H_NOTES:
            w.writerow(["Session %d" % when if isinstance(when, int)
                        else when, who, by, text])
    with open(p("harbour-hill diaries.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["#", "Diary 1", "Diary 2", "Diary 3"])
        for row in H_ROWS:
            w.writerow([row[0]] + row[8].split(" ", 2))


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "samples"
    make_northgate(os.path.join(base, "fake_northgate"))
    make_harbour(os.path.join(base, "fake_harbour_hill"))
