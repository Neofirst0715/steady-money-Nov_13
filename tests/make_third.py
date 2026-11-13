"""Writes a made-up third agency in a different layout: no client numbers,
Y/N marks, notes in a spreadsheet, diaries one column per week,
month-first dates. Every hard case from the interviews is in it."""
import csv, os, sys

D = ["01/05/2027", "01/12/2027", "01/19/2027", "01/26/2027", "02/02/2027"]
P, S = "Priya Nair", "Sam Okafor"
# name, worker, tel, best way, 5 marks, mc first, mc mid, diaries wk1-3
ROWS = [
 ("Hannah Fox", P, "902-555-7001", "Text", "Y Y Y Y Y", 12, 16, "yes yes yes"),
 ("Imran Qureshi", P, "902-555-7002", "Phone", "Y Y Y Y Y", 10, 11, "no no no"),
 ("Olga Petrov", S, "902-555-7003", "Phone", "Y Y Y N N", 14, "", "yes no no"),
 ("Luis Mendes", S, "902-555-7004", "Text", "Y Y Y Excused Excused", 9, "", "yes yes no"),
 ("Grace Li", P, "902-555-7005", "Post", "Y Y Y N N", 15, "", "yes yes no"),
 ("Tom Reid", P, "902-555-7006", "Text", "Y Y Y Y Y", 11, 15, "no no no"),
 ("Nadia Haddad", S, "902-555-7007", "Phone", "Y Y Y Y Y", 13, 13, "no no yes"),
 ("Pete Walsh", S, "902-555-7008", "Text", "Y Y Y Late Late", 16, 19, "yes yes yes"),
 ("William Carter", P, "902-555-7009", "Phone", "Y Y Y Y Y", 8, 12, "yes yes yes"),
 ("Maria Santos", S, "902-555-7010", "Text", "Y Y Y Y Y", 12, 12, "yes yes yes"),
 ("Maria Lopez", S, "902-555-7011", "Phone", "Y Y Y Y Y", 10, 14, "yes yes yes"),
 ("Derek Shaw", P, "902-555-7012", "Phone", "Y Y Y N N", 9, "", "yes yes no"),
 ("Yusuf Ali", S, "902-555-7013", "Text", "Y Y Y Y Y", 14, 13, "no no yes"),
 ("Fiona Burke", P, "902-555-7014", "Phone", "Y Y Y Y Y", 11, 17, "yes yes yes"),
 ("Colin Tate", S, "902-555-7015", "Post", "Y Y Y Y Y", 15, 18, "yes  "),
 ("Rita Gomez", P, "902-555-7016", "Text", "Y Y N Y Y", 12, 15, "yes no yes"),
]
STD = "Went through the month's bills together and set the diary for next week."
NOTES = [
 (0, "Imran", P, STD), (1, "Imran", P, STD), (2, "Imran", P, STD),
 (3, "Imran Qureshi", P, "Reviewed the debt list. Asked us not to contact him between sessions, he will just come in."),
 (2, "Grace", P, "Sorted statements. Will be away the next two weeks for work, let us know today."),
 (0, "Tom", P, "New job starting soon. Diary paused while he changes jobs, agreed together."),
 (1, "Tom", P, "Looked at the pay schedule for the new job. Nothing else to report this week."),
 (2, "Tom", P, "Settled into the new job now. Diary back on from this week, page explained again."),
 (0, "Nadia", S, STD),
 (1, "Nadia", S, "Long session on rent arrears with the landlord letter, didn't get to homework this week."),
 (2, "Nadia", S, STD),
 (2, "Bill", P, "Good session on the grocery budget and receipts. Prefers email now, checks it every day."),
 (1, "Maria", S, "Went through the bank statements line by line. Text is fine for reminders."),
 (3, "Maria Lopez", S, "Built the bill calendar for the next three months. No texts, call after 6."),
 (4, "Derek", P, "Did not come today. Tried him this afternoon, no answer and the number is disconnected."),
 (1, "Fiona", P, "Talked about the car repair bill and options. Best to reach her through her sister for now."),
 (0, "Hannah", P, STD), (1, "Hannah", P, STD), (2, "Hannah", P, STD), (3, "Hannah", P, STD), (4, "Hannah", P, STD),
 (0, "Olga", S, STD), (1, "Olga", S, STD), (2, "Olga", S, STD),
 (0, "Yusuf", S, STD), (1, "Yusuf", S, STD), (2, "Yusuf", S, STD),
 (0, "Rita", P, STD), (1, "Rita", P, STD), (3, "Rita", P, STD),
 (0, "Derek", P, STD), (1, "Derek", P, STD), (2, "Derek", P, STD),
 (0, "Luis", S, STD), (1, "Luis", S, STD), (2, "Luis", S, STD),
]
# status, why, how_to_reach
KEY = {
 "Hannah Fox": ("on track", "Coming and keeping up", "text"),
 "Imran Qureshi": ("stalled", "Nothing handed in for two homework weeks", "do not contact"),
 "Olga Petrov": ("stalled", "Missed the last two sessions", "call"),
 "Luis Mendes": ("on track", "Coming and keeping up", "text"),
 "Grace Li": ("on track", "Coming and keeping up", "paper"),
 "Tom Reid": ("on track", "Coming and keeping up", "text"),
 "Nadia Haddad": ("on track", "Coming and keeping up", "call"),
 "Pete Walsh": ("on track", "Coming and keeping up", "text"),
 "William Carter": ("on track", "Coming and keeping up", "call"),
 "Maria Santos": ("on track", "Coming and keeping up", "text"),
 "Maria Lopez": ("on track", "Coming and keeping up", "call"),
 "Derek Shaw": ("stalled", "Missed the last two sessions", "paper"),
 "Yusuf Ali": ("on track", "Coming and keeping up", "text"),
 "Fiona Burke": ("on track", "Coming and keeping up", "call"),
 "Colin Tate": ("on track", "Coming and keeping up", "paper"),
 "Rita Gomez": ("on track", "Coming and keeping up", "text"),
}


def make(folder):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "Register winter group.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Participant", "Worker", "Tel", "Best way", "Week1", "Week2",
                    "Week3", "Week4", "Week5", "MC first", "MC mid"])
        for n, wk, tel, way, marks, a, b, _ in ROWS:
            w.writerow([n, wk, tel, way] + marks.split(" ") + [a, b])
    with open(os.path.join(folder, "Session log.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Participant", "Worker", "What we did"])
        for i, who, wk, text in NOTES:
            w.writerow([D[i], who, wk, text])
    with open(os.path.join(folder, "Homework returns.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Participant", "Diary wk1", "Diary wk2", "Diary wk3"])
        for n, _, _, _, _, _, _, d in ROWS:
            w.writerow([n] + d.split(" "))


if __name__ == "__main__":
    make(sys.argv[1] if len(sys.argv) > 1 else "samples/third_layout")
