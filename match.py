"""Match a name written in the notes or the diary sheet to one client on
the attendance sheet. A match is only made when exactly one client fits;
otherwise the line is flagged for the counsellor."""
import re

_GROUPS = """
william bill billy will liam willy
elizabeth liz beth lizzie eliza betty liza libby betsy
anthony tony ant
raymond ray
gordon gord gordie
ronald ron ronnie
terrence terry terence terrance
robert rob bob bobby robbie bert
richard rick dick rich ricky
margaret maggie meg peggy marg margie
katherine kate katie kathy kat catherine cathy kathryn cath
james jim jimmy jamie
john jack johnny
jonathan jon jonny
michael mike mick mikey
christopher chris kit
christine chris chrissy tina christina
patricia pat patty trish tricia
patrick pat paddy
thomas tom tommy
joseph joe joey
daniel dan danny
david dave davey
edward ed eddie ted ned
theodore theo ted teddy
alexander alex sandy xander
alexandra alex sandra lexi
nicholas nick nicky
samuel sam sammy
samantha sam
benjamin ben benny
matthew matt
andrew andy drew
stephen steve stevie steven
susan sue susie suzanne
deborah deb debbie debra
jennifer jen jenny
jessica jess jessie
rebecca becky becca
victoria vicky vic tori
charles charlie chuck chas
henry harry hank
lawrence larry laurence
leonard len lenny
gerald gerry jerry
jerome jerry
kenneth ken kenny
donald don donnie
douglas doug
gregory greg
jeffrey jeff geoff geoffrey
timothy tim timmy
frederick fred freddie
francis frank frankie
frances fran frannie
barbara barb
dorothy dot dottie
eleanor ellie nell
josephine jo josie
abigail abby
amanda mandy
cynthia cindy
pamela pam
teresa terri tess theresa
stanley stan
philip phil phillip
peter pete
walter walt wally
arthur art artie
albert al bert
alfred alf alfie
vincent vince vinny
zachary zach zack
nathan nate nathaniel nat
joshua josh
jacob jake
maxwell max
mohammed mo mohamed muhammad mohammad
lucille lucy lu
judith judy
bernard bernie
beatrice bea
carolyn carol caroline carrie
bethany beth
reginald reg reggie
randall randy
russell russ
wesley wes
clifford cliff
stuart stu stewart
curtis curt
trevor trev
darnell darn
"""
GROUPS = [set(line.split()) for line in _GROUPS.strip().splitlines()]


def _clean(s):
    return re.sub(r"[^a-z' \-]", " ", s.lower()).split()


def first_names_match(a, b):
    """-> 'exact', 'nickname' or ''."""
    if a == b:
        return "exact"
    for g in GROUPS:
        if a in g and b in g:
            return "nickname"
    short, long_ = sorted((a, b), key=len)
    if len(short) >= 3 and long_.startswith(short):
        return "nickname"
    return ""


STOP = set("""mr mrs ms miss dr mx session sess week wk mtg meeting notes
note with and client counsellor counselor worker staff the re mon tue tues
wed thu thur thurs fri sat sun monday tuesday wednesday thursday friday
saturday sunday group class by for of""".split())


def _score(toks, ct):
    """How well a written name fits a client's name. 0 = not at all."""
    f, l = ct[0], (ct[-1] if len(ct) > 1 else "")
    if len(toks) == 1:
        t = toks[0]
        how = first_names_match(t, f) if len(t) > 1 else ""
        if how == "exact":
            return 1.0
        if l and t == l and len(t) >= 3:
            return 1.0
        if how == "nickname":
            return 0.9
        if l and len(t) == 2 and t[0] == f[0] and t[1] == l[0]:
            return 0.5
        return 0
    best = 0
    for a, b in ((toks[0], toks[-1]), (toks[-1], toks[0])):
        how = first_names_match(a, f) if len(a) > 1 else ""
        if how and l and b == l:
            best = max(best, 4.0 if how == "exact" else 3.9)
        elif how and l and len(b) == 1 and l.startswith(b):
            best = max(best, 3.0 if how == "exact" else 2.9)
        elif len(a) == 1 and f.startswith(a) and l and b == l:
            best = max(best, 3.0)
    return best


class Roster:
    def __init__(self, clients):
        self.clients = clients
        self.staff = sorted({c["counsellor"] for c in clients
                             if c["counsellor"]})
        self.by_id = {c["id"].lower(): c for c in clients}

    def staff_for(self, token_or_name):
        """Counsellors a word or name could refer to."""
        t = _clean(token_or_name)
        if not t:
            return []
        out = []
        for s in self.staff:
            st = _clean(s)
            if t == st or (len(t) >= 2 and t[0] == st[0] and (
                    t[-1] == st[-1] or st[-1].startswith(t[-1]))):
                out.append(s)
            elif len(t) == 1 and (t[0] in (st[0], st[-1]) or (
                    len(st) > 1 and len(t[0]) == 2 and
                    t[0] == st[0][0] + st[-1][0])):
                out.append(s)
        return out

    def candidates(self, name, pool=None):
        """-> (score, [clients]) for the best-fitting clients."""
        toks = [t for t in _clean(name) if t not in STOP]
        if not toks:
            return 0, []
        best, who = 0, []
        for c in (pool if pool is not None else self.clients):
            ct = _clean(c["name"])
            if not ct:
                continue
            sc = _score(toks, ct)
            if sc > best:
                best, who = sc, [c]
            elif sc and sc == best:
                who.append(c)
        return best, who

    def find(self, name, counsellor=None):
        """-> (client or None, how, candidates). how is exact / nickname /
        none / several."""
        if name.strip().lower() in self.by_id:
            return self.by_id[name.strip().lower()], "exact", []
        sc, who = self.candidates(name)
        if len(who) > 1 and counsellor:
            narrowed = [c for c in who if c["counsellor"] == counsellor]
            if narrowed:
                who = narrowed
        if len(who) == 1:
            return who[0], ("exact" if sc in (1.0, 3.0, 4.0) else
                            "nickname"), who
        return None, ("several" if who else "none"), who
