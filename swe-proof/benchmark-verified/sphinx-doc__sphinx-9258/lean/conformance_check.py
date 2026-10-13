#!/usr/bin/env python3
"""G-CONF for sphinx-doc__sphinx-9258.

Differential test of the R/I legs of `implementation_splitTypeSpec`.

The changed op is the regex tokeniser in `PyXrefMixin.make_xrefs`
(`sphinx/domains/python.py`): `re.split(delims, target)` followed by a per-piece
`delims_re.match(...)` classification. The Lean bundle models this DEEPLY as the
`pure`-region tower (`spacesLen`/`delimLen`/`reSplit`/`classifySeg`/`tokenize`).

This script re-implements that Lean model in Python (`lean_reSplit`,
`lean_delim_len`, `lean_tokenize`) with byte-identical logic, and checks, over
>=1e5 fuzzed inputs:

  (a) lean_reSplit(pipe=True)  == re.split(NEW_delims, target)      [raw, incl. empties]
  (b) lean_reSplit(pipe=False) == re.split(OLD_delims, target)
  (c) lean_tokenize(target)    == real post-patch make_xrefs classification
                                  (filter(None, re.split) + delims_re.match)
  (d) lean_delim_len(piece, pipe).is_some == bool(delims_re.match(piece))
      for every survivor piece and both patterns.

stdlib-only; exit 0 iff zero disagreements.
"""
import json
import random
import re
import sys

# The OLD (pre-patch) and NEW (post-patch) delimiter alternations, verbatim from
# sphinx/domains/python.py line 307 (base_commit vs patched).
OLD_DELIMS = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\.\.\.)'
NEW_DELIMS = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'
OLD_RE = re.compile(OLD_DELIMS)
NEW_RE = re.compile(NEW_DELIMS)

CONF_SEED = 9258
# Alphabet: type-name chars + every separator trigger + whitespace, including
# the non-ASCII / non-obvious code points Python \s matches (\f, \v, NBSP,
# NEL, EM SPACE, IDEOGRAPHIC SPACE, and an information-separator control) so
# the Lean model's whitespace predicate is exercised beyond {' ','\t','\n','\r'}.
ALPHABET = "abc |[](),.or\t\n\f\x0b\xa0\x85 　\x1c"
# Exactly the code points Python re \s matches (verified by enumerating all of
# Unicode against re.compile(r'\s')); mirrors the Lean `isSp`.
WS = frozenset(
    chr(c) for c in
    list(range(0x9, 0xE)) + list(range(0x1C, 0x21)) + [0x85, 0xA0, 0x1680]
    + list(range(0x2000, 0x200B)) + [0x2028, 0x2029, 0x202F, 0x205F, 0x3000]
)
BR = set("[](),")


# ---- Python replica of the Lean `pure` region -----------------------------

def spaces_len(s, p):
    n = len(s); i = p
    while i < n and s[i] in WS:
        i += 1
    return i - p


def dots_len(s, p):
    return 3 if s[p:p + 3] == "..." else None


def pipe_or_dots(pipe, s, p):
    if pipe:
        k = spaces_len(s, p); i = p + k
        if i < len(s) and s[i] == '|':
            return (i + 1 - p) + spaces_len(s, i + 1)
        return dots_len(s, p)
    return dots_len(s, p)


def tail_delim(pipe, s, p):
    k = spaces_len(s, p); i = p + k
    if s[i:i + 2] == "or":
        tl = i + 2
        if k >= 1 and spaces_len(s, tl) >= 1:
            return (tl - p) + spaces_len(s, tl)
        return pipe_or_dots(pipe, s, p)
    return pipe_or_dots(pipe, s, p)


def delim_len(pipe, s, p=0):
    """Match the delimiter alternation as a prefix of s[p:]; return consumed
    length (>0) or None. Mirrors Lean `delimLen`."""
    n = len(s)
    k = spaces_len(s, p); i = p + k
    if i < n and s[i] in BR:
        b = i + 1
        k2 = spaces_len(s, b); j = b + k2
        if s[j:j + 2] == "or" and j + 2 < n and s[j + 2] in WS:
            return (j + 3 - p) + spaces_len(s, j + 3)
        return (b - p) + spaces_len(s, b)
    return tail_delim(pipe, s, p)


def lean_re_split(pipe, target):
    """Mirror Lean `reSplit`: interleaved text/sep pieces incl. empties."""
    res = []
    cur = ""
    s = target
    while True:
        if s == "":
            res.append(cur); break
        n = delim_len(pipe, s, 0)
        if n is not None and n > 0:
            res.append(cur)
            res.append(s[:n])
            cur = ""
            s = s[n:]
        else:
            cur += s[0]
            s = s[1:]
    return res


def lean_classify(piece):
    return ("sep", piece) if delim_len(True, piece, 0) is not None else ("name", piece)


def lean_tokenize(target):
    return [lean_classify(p) for p in lean_re_split(True, target) if p != ""]


# ---- Real post-patch make_xrefs classification ----------------------------

def real_tokenize(target):
    """Exactly the classification the post-patch make_xrefs performs:
    filter(None, re.split(NEW)) then tag by bool(NEW_RE.match(sub))."""
    out = []
    for sub in filter(None, NEW_RE.split(target)):
        out.append(("sep" if NEW_RE.match(sub) else "name", sub))
    return out


def main():
    rng = random.Random(CONF_SEED)
    N = 120_000
    disagreements = []
    for _ in range(N):
        L = rng.randint(0, 16)
        t = "".join(rng.choice(ALPHABET) for _ in range(L))

        # (a) raw split, NEW pattern
        if lean_re_split(True, t) != NEW_RE.split(t):
            disagreements.append(("reSplit-new", t, lean_re_split(True, t), NEW_RE.split(t)))
        # (b) raw split, OLD pattern
        if lean_re_split(False, t) != OLD_RE.split(t):
            disagreements.append(("reSplit-old", t, lean_re_split(False, t), OLD_RE.split(t)))
        # (c) full classification vs real make_xrefs
        if lean_tokenize(t) != real_tokenize(t):
            disagreements.append(("tokenize", t, lean_tokenize(t), real_tokenize(t)))
        # (d) delim_len.is_some == bool(delims_re.match) for each survivor
        for sub in filter(None, NEW_RE.split(t)):
            if (delim_len(True, sub, 0) is not None) != bool(NEW_RE.match(sub)):
                disagreements.append(("match-new", sub, delim_len(True, sub, 0), NEW_RE.match(sub)))
        for sub in filter(None, OLD_RE.split(t)):
            if (delim_len(False, sub, 0) is not None) != bool(OLD_RE.match(sub)):
                disagreements.append(("match-old", sub, delim_len(False, sub, 0), OLD_RE.match(sub)))

        if len(disagreements) > 20:
            break

    # sanity: the F2P scenario must split around the bar
    f2p = lean_tokenize("int | str")
    if f2p != [("name", "int"), ("sep", " | "), ("name", "str")]:
        disagreements.append(("f2p", "int | str", f2p, "expected int | str split"))

    status = "pass" if not disagreements else "fail"
    print(json.dumps({
        "gate": "G-CONF",
        "instance": "sphinx-doc__sphinx-9258",
        "status": status,
        "samples": N,
        "seed": CONF_SEED,
        "disagreements": disagreements[:20],
    }, indent=2))
    sys.exit(0 if status == "pass" else 1)


if __name__ == "__main__":
    main()
