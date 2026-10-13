#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14365.

This bundle consumes NO axioms: both changed operations are modeled DEEPLY and
validated == the real code here (A-references, refinement.md §C). G-AX checks:

  (A-reference #1) `classify(fold, line)` (the Solution.lean deep model of the
      `_line_type` classifier) == the REAL `_line_type` dispatch, for BOTH flag
      values:
        classify(True,  line) == real _line_type compiled with re.IGNORECASE   (post-patch)
        classify(False, line) == real _line_type compiled with NO flag         (pre-patch)
      The real `_type_re` regex is rebuilt VERBATIM from qdp.py:62-70 (default
      whitespace delimiter, the F2P code path) and driven through the genuine
      groupdict dispatch of qdp.py:78-85.

  (A-reference #2) `is_decimal(tok)` (the Solution.lean numeric DFA, decRun/decStep)
      == re.fullmatch(_decimal_re, tok), the literal sub-pattern of _type_re.

  (A-reference #3) `mask_seq(fold, tokens)` (the Solution.lean masking model)
      == the real per-cell test: v == "NO" (fold False) / v.upper() == "NO"
      (fold True), qdp.py:309.

Imports only the Python standard library `re` (the same module qdp.py uses). The
checks are over boundary cases plus >10^6 randomized fuzz inputs. Exit 0 iff every
obligation holds.
"""
import random
import re
import sys

# ============================================================================
# THE REAL CODE — _type_re rebuilt verbatim from qdp.py:62-70 (default sep) and
# the real groupdict dispatch from qdp.py:72-85. This is the ORACLE.
# ============================================================================
_decimal_re = r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"
_command_re = r"READ [TS]ERR(\s+[0-9]+)+"
_sep = r"\s+"  # delimiter is None -> sep = r"\s+"
_new_re = rf"NO({_sep}NO)+"
_data_re = rf"({_decimal_re}|NO|[-+]?nan)({_sep}({_decimal_re}|NO|[-+]?nan))*)"
_type_re = (
    rf"^\s*((?P<command>{_command_re})|(?P<new>{_new_re})|"
    rf"(?P<data>{_data_re})?\s*(\!(?P<comment>.*))?\s*$"
)
_RX_POST = re.compile(_type_re, re.IGNORECASE)   # gold post-patch compile
_RX_PRE = re.compile(_type_re)                   # pre-patch compile
_DEC_FULL = re.compile(_decimal_re)


def real_line_type(rx, line):
    """The genuine _line_type dispatch (qdp.py:72-85), default delimiter.
    Returns an LType-shaped string: 'comment' | 'command' | 'new' | 'data,N' |
    'reject' (instead of raising, to compare against classify's `reject`)."""
    line = line.strip()
    if not line:
        return "comment"
    match = rx.match(line)
    if match is None:
        return "reject"
    for type_, val in match.groupdict().items():
        if val is None:
            continue
        if type_ == "data":
            return "data,%d" % len(val.split())  # delimiter=None -> split()
        else:
            return type_
    return "reject"  # unreachable in practice


def real_masked(fold, v):
    """The genuine masking test (qdp.py:309): v.upper()=='NO' post / v=='NO' pre."""
    return (v.upper() == "NO") if fold else (v == "NO")


# ============================================================================
# THE DEEP MODEL — faithful transliteration of Solution.lean's pure region.
# (classify / maskSeq / isDecimal, with the `fold` flag = the changed re flag.)
# ============================================================================
_WS = set(" \t\n\r\x0c\x0b")


def _is_ws(c):
    return c in _WS


def strip_ws(s):
    return s.strip("".join(_WS))


def words(s):
    # splitOnP isWs then drop empties == Python str.split() on whitespace.
    return [t for t in re.split(r"[ \t\n\r\x0c\x0b]", s) if t != ""]


def eq_fold(fold, a, b):
    return (a.upper() == b.upper()) if fold else (a == b)


def _isdig(c):
    return "0" <= c <= "9"


def is_digits(s):
    return s != "" and all(_isdig(c) for c in s)


def _dec_step(st, c):
    if st == 0:
        return 1 if c in "+-" else 2 if _isdig(c) else 4 if c == "." else 9
    if st == 1:
        return 2 if _isdig(c) else 4 if c == "." else 9
    if st == 2:
        return 2 if _isdig(c) else 3 if c == "." else 6 if c in "eE" else 9
    if st == 3:
        return 3 if _isdig(c) else 6 if c in "eE" else 9
    if st == 4:
        return 5 if _isdig(c) else 9
    if st == 5:
        return 5 if _isdig(c) else 6 if c in "eE" else 9
    if st == 6:
        return 7 if c in "+-" else 8 if _isdig(c) else 9
    if st == 7:
        return 8 if _isdig(c) else 9
    if st == 8:
        return 8 if _isdig(c) else 9
    return 9


def is_decimal(tok):
    st = 0
    for c in tok:
        st = _dec_step(st, c)
    return st in (2, 3, 5, 8)


def is_marker_tok(fold, t):
    return eq_fold(fold, t, "NO")


def is_nan_tok(fold, t):
    if not t:
        return False
    if t[0] in "+-":
        return eq_fold(fold, t[1:], "nan")
    return eq_fold(fold, t, "nan")


def is_data_tok(fold, t):
    return is_decimal(t) or is_marker_tok(fold, t) or is_nan_tok(fold, t)


def is_directive(fold, s):
    if not eq_fold(fold, s[:4], "READ"):
        return False
    if s[4:5] != " ":
        return False
    if not (eq_fold(fold, s[5:9], "SERR") or eq_fold(fold, s[5:9], "TERR")):
        return False
    rest = s[9:]
    core = rest.split("!", 1)[0] if "!" in rest else rest
    ops = words(core)
    head_ws = bool(core) and _is_ws(core[0])
    return head_ws and len(ops) >= 1 and all(is_digits(o) for o in ops)


def classify(fold, line):
    s = strip_ws(line)
    if s == "":
        return "comment"
    core = s.split("!", 1)[0] if "!" in s else s
    has_tail = "!" in s
    toks = words(core)
    if is_directive(fold, s):
        return "command"
    if len(toks) >= 2 and all(is_marker_tok(fold, t) for t in toks):
        return "new"
    if len(toks) == 0:
        return "comment" if has_tail else "reject"
    if all(is_data_tok(fold, t) for t in toks):
        return "data,%d" % len(toks)
    return "reject"


def mask_seq(fold, tokens):
    return [is_marker_tok(fold, t) for t in tokens]


# ============================================================================
# THE CHECKS
# ============================================================================
def _gen_chars(rng, alphabet, maxlen):
    n = rng.randint(0, maxlen)
    return "".join(rng.choice(alphabet) for _ in range(n))


def _rcase(rng, w):
    return "".join(c.upper() if rng.random() < 0.5 else c.lower() for c in w)


def _ws(rng):
    return rng.choice([" ", "  ", "   ", "\t", " \t ", " "])


def _gen_structured(rng):
    k = rng.random()
    if k < 0.30:
        n = rng.randint(0, 4)
        body = ("READ" + _ws(rng) + rng.choice(["SERR", "TERR", "XERR"])
                + "".join(_ws(rng) + str(rng.randint(0, 99)) for _ in range(n)))
        s = _rcase(rng, body)
    elif k < 0.50:
        s = _rcase(rng, _ws(rng).join(["NO"] * rng.randint(1, 5)))
    elif k < 0.85:
        toks = [rng.choice(["1", "-2.5", ".04", "1e-3", "2.", "+3.5E2", "NO",
                            "nan", "-nan", "abc", ".", "1.2.3", "12NO", "NAN", "No"])
                for _ in range(rng.randint(0, 5))]
        s = _rcase(rng, _ws(rng).join(toks))
        if rng.random() < 0.4:
            s += _ws(rng) + "!" + "".join(rng.choice("abc !12")
                                          for _ in range(rng.randint(0, 6)))
    else:
        s = "".join(rng.choice("READSNO0-+.enN !\t")
                    for _ in range(rng.randint(0, 14)))
    return rng.choice(["", "", " ", "\t"]) + s + rng.choice(["", "", " ", "\t"])


def check_classify():
    rng = random.Random(14365)
    n = 0
    boundary = [
        "READ SERR 1 2", "read serr 1 2", "Read Serr 1 2", "READ TERR 3",
        "read terr 1 2 ! c", "READ  SERR 1 2", "READSERR 1", "READ SERR",
        "NO NO NO", "no no no", "No nO", "NO NO 5", "1 2 3", "no", "NO",
        "nan -nan NAN", "1e-3 .04 +5.", "! just a comment", "   ", "",
        "1 2 ! tail", "read serr 1 2", "1.2.3", "garbage here",
    ]
    for fold, rx, tag in ((True, _RX_POST, "IGNORECASE/post"),
                          (False, _RX_PRE, "no-flag/pre")):
        for line in boundary:
            n += 1
            got, exp = classify(fold, line), real_line_type(rx, line)
            assert got == exp, (
                "classify(%s) boundary mismatch on %r: model=%r real=%r"
                % (tag, line, got, exp))
        for _ in range(300_000):
            line = _gen_chars(rng, "READSERTNOnaeE0123456789 .+-!\t", 18)
            n += 1
            got, exp = classify(fold, line), real_line_type(rx, line)
            assert got == exp, (
                "classify(%s) char-fuzz mismatch on %r: model=%r real=%r"
                % (tag, line, got, exp))
        for _ in range(300_000):
            line = _gen_structured(rng)
            n += 1
            got, exp = classify(fold, line), real_line_type(rx, line)
            assert got == exp, (
                "classify(%s) struct-fuzz mismatch on %r: model=%r real=%r"
                % (tag, line, got, exp))
    return n


def check_decimal():
    rng = random.Random(7)
    n = 0
    for tok in ["", "1", "-1", "+1", ".5", "1.", "1.5", "1e3", "1E-3", "+.5e+2",
                "1.2.3", "e3", ".", "nan", "1e", "1e+", "--1", "0012", "5.5E10"]:
        n += 1
        assert is_decimal(tok) == (_DEC_FULL.fullmatch(tok) is not None), (
            "is_decimal boundary mismatch on %r" % tok)
    for _ in range(600_000):
        tok = _gen_chars(rng, "0123456789.eE+- ", 10)
        n += 1
        assert is_decimal(tok) == (_DEC_FULL.fullmatch(tok) is not None), (
            "is_decimal fuzz mismatch on %r: model=%r real=%r"
            % (tok, is_decimal(tok), _DEC_FULL.fullmatch(tok) is not None))
    return n


def check_mask():
    rng = random.Random(99)
    n = 0
    for v in ["NO", "no", "No", "nO", "NONO", " NO", "NOO", "n", "", "1", "nan",
              "N O", "NO ", "0NO"]:
        for fold in (True, False):
            n += 1
            assert is_marker_tok(fold, v) == real_masked(fold, v), (
                "mask boundary mismatch on (%s, %r)" % (fold, v))
    for _ in range(200_000):
        v = _gen_chars(rng, "NOno0123456789 ", 6)
        for fold in (True, False):
            n += 1
            assert is_marker_tok(fold, v) == real_masked(fold, v), (
                "mask fuzz mismatch on (%s, %r): model=%r real=%r"
                % (fold, v, is_marker_tok(fold, v), real_masked(fold, v)))
    # also exercise mask_seq over rows
    for _ in range(20_000):
        row = [_gen_chars(rng, "NOno12 ", 4) for _ in range(rng.randint(0, 5))]
        for fold in (True, False):
            n += 1
            assert mask_seq(fold, row) == [real_masked(fold, v) for v in row], (
                "mask_seq mismatch on (%s, %r)" % (fold, row))
    return n


def main():
    nc = check_classify()
    nd = check_decimal()
    nm = check_mask()
    print("G-AX OK: classify deep model == real _line_type for BOTH flags "
          "(IGNORECASE/post + no-flag/pre) on %d lines; is_decimal DFA == "
          "re.fullmatch(_decimal_re) on %d tokens; mask deep model == "
          "v[.upper()]=='NO' on %d cells. No consumed axioms; all A-references "
          "sound." % (nc, nd, nm))
    return 0


if __name__ == "__main__":
    sys.exit(main())
