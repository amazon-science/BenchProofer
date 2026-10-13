#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9230.

Executes the REAL stdlib callee (`str.rsplit(None, 1)`) on inputs (boundary
cases plus randomized fuzzing) and asserts that every observation matches the
deep model `severTail` from Solution.lean's `pure` region.

The single kind-A check:

  (A-reference) the deep model `sever_tail` (== Solution.lean `severTail`) ==
      the real `str.rsplit(None, 1)`, re-expressed as the 2-tuple-or-ValueError
      outcome the patched `transform` consumes:
        rsplit yields [t, a]  <->  sever_tail(s) == (t, a)
        rsplit yields <2 parts (ValueError on 2-unpack)  <->  sever_tail(s) is None

  Plus the classifier soundness: `is_ws(cp)` (the wsCodes membership test from
  Solution.lean) == "does chr(cp) act as split-whitespace for str.split()",
  over the whole BMP. A wrong classifier would silently desync the deep model
  from the real callee, so it is checked directly.

Imports nothing repo-specific: `str.rsplit` is a builtin and `html` is unused.
Exit 0 iff every obligation holds.
"""
import random
import sys

# --- Solution.lean reference encodings (kept in lock-step with the model) ----

# wsCodes: the code points Solution.lean's `isWs` classifies as whitespace.
WS_CODES = [0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x85, 0xa0,
            0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006,
            0x2007, 0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f,
            0x3000]
WS = set(WS_CODES)


def is_ws(ch):
    return ord(ch) in WS


def rstrip_ws(s):
    i = len(s)
    while i > 0 and is_ws(s[i - 1]):
        i -= 1
    return s[:i]


def tail_word(s):
    i = len(s)
    while i > 0 and not is_ws(s[i - 1]):
        i -= 1
    return s[i:]


def before_tail_word(s):
    i = len(s)
    while i > 0 and not is_ws(s[i - 1]):
        i -= 1
    return s[:i]


def sever_tail(s):
    """Reference of Solution.lean's `severTail`: separate on the LAST whitespace
    run after ignoring trailing whitespace; None iff fewer than two
    whitespace-separated non-empty parts."""
    s2 = rstrip_ws(s)
    nm = tail_word(s2)
    lead = rstrip_ws(before_tail_word(s2))
    if lead == "":
        return None
    return (lead, nm)


# --- the checks --------------------------------------------------------------

def real_outcome(fieldarg):
    """The 2-tuple-or-None outcome the patched `transform` consumes from the
    REAL `str.rsplit(None, 1)`."""
    try:
        argtype, argname = fieldarg.rsplit(None, 1)   # real callee
    except ValueError:
        return None
    return (argtype, argname)


def check_sever_reference(s):
    """Assert the deep model sever_tail(s) == the REAL str.rsplit(None,1)."""
    observed = real_outcome(s)                         # real callee
    expected = sever_tail(s)                           # deep model
    assert observed == expected, (
        "severTail deep model unsound on %r: rsplit(None,1) gave %r, "
        "deep model gives %r" % (s, observed, expected))


def check_classifier():
    """Assert wsCodes == Python's split-whitespace classifier over the BMP."""
    for cp in range(0x10000):
        ch = chr(cp)
        # chr(cp) is split-whitespace iff it separates "a<ch>b" into ["a","b"].
        splits = (("a" + ch + "b").split() == ["a", "b"])
        model = cp in WS
        assert splits == model, (
            "wsCodes classifier wrong at U+%04X: Python split-ws=%r, "
            "model=%r" % (cp, splits, model))


def main():
    check_classifier()

    # --- severTail deep model (A-reference): boundary cases ----------------
    boundary = [
        "",                          # empty            -> None
        "   ",                       # all whitespace   -> None
        "opc_meta",                  # single word      -> None
        "int age",                   # simple two-word  -> ("int","age")
        "Tuple[str, ...] items",     # bracketed type w/ interior ws
        "dict(str, str) opc_meta",   # the issue's case -> ("dict(str, str)","opc_meta")
        "  a  b  c  ",               # leading/trailing/interior ws
        "  x   y  ",
        "\ta\tb\t",                  # tabs
        "type name extra",
        "a b",
        "  leadingonly",             # leading ws, single word -> None
        "trailingonly   ",           # trailing ws, single word -> None
        "a b",                  # non-breaking space (split-ws)
        "a b",                  # em space
        "a　b",                  # ideographic space
    ]
    for s in boundary:
        check_sever_reference(s)

    # --- severTail deep model (A-reference): randomized fuzz ---------------
    rng = random.Random(9230)
    ws_chars = [chr(c) for c in WS_CODES]
    ordinary = list("ab(),[]._:dictstrZ0") + ["é", "•"]
    alphabet = ws_chars + ordinary
    n_fuzz = 50000
    for _ in range(n_fuzz):
        n = rng.randint(0, 20)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_sever_reference(s)

    print("G-AX OK: severTail deep model (== str.rsplit(None,1)) sound on "
          "%d boundary + %d fuzz inputs; wsCodes classifier matches Python "
          "split-whitespace over the full BMP." % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
