#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14365 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl regions transliterated
              to Python over the real repo types (`str` / list of `str`), via the
              mapping.md bijection (`List Char` ↔ `str`). Both modeled ops use the
              POST-PATCH flag `fold=True` (the value the verified `lineType` /
              `maskFlags` impls thread). There are NO A-tagged callees left as
              stubs here — both ops are deep models (A-references), so the shadow
              is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the GOLD-patched code path applied at
              base_commit. Site 1: `_line_type` with `re.compile(_type_re,
              re.IGNORECASE)` (the gold flag) + the real groupdict dispatch.
              Site 2: the gold `v.upper() == "NO"` masking test.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs stdlib-only (`re`); the `_type_re` regex and dispatch are reproduced
verbatim from qdp.py (default whitespace delimiter, the F2P code path). The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import re
import sys

SEED = 14365
N_FUZZ = 100_000

# ---------------------------------------------------------------------------
# ORACLE — patch.diff behaviour. The gold-patched _line_type (IGNORECASE) and
# the gold-patched masking test, reproduced verbatim from qdp.py.
# ---------------------------------------------------------------------------
_decimal_re = r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"
_command_re = r"READ [TS]ERR(\s+[0-9]+)+"
_sep = r"\s+"
_new_re = rf"NO({_sep}NO)+"
_data_re = rf"({_decimal_re}|NO|[-+]?nan)({_sep}({_decimal_re}|NO|[-+]?nan))*)"
_type_re = (
    rf"^\s*((?P<command>{_command_re})|(?P<new>{_new_re})|"
    rf"(?P<data>{_data_re})?\s*(\!(?P<comment>.*))?\s*$"
)
# gold post-patch: re.compile(_type_re, re.IGNORECASE)
_RX_GOLD = re.compile(_type_re, re.IGNORECASE)


def oracle_line_type(line):
    """Gold-patched _line_type dispatch (qdp.py:72-85), default delimiter.
    'reject' stands in for the raised ValueError (== LType.reject)."""
    line = line.strip()
    if not line:
        return "comment"
    match = _RX_GOLD.match(line)
    if match is None:
        return "reject"
    for type_, val in match.groupdict().items():
        if val is None:
            continue
        if type_ == "data":
            return "data,%d" % len(val.split())
        else:
            return type_
    return "reject"


def oracle_masked(v):
    """Gold-patched masking test (qdp.py:309 post): v.upper() == 'NO'."""
    return v.upper() == "NO"


# ---------------------------------------------------------------------------
# SHADOW — Solution.lean impl regions transliterated, fold=True (post-patch).
# classify / maskSeq, faithful to the Lean pure region.
# ---------------------------------------------------------------------------
_WS = set(" \t\n\r\x0c\x0b")


def _is_ws(c):
    return c in _WS


def strip_ws(s):
    return s.strip("".join(_WS))


def words(s):
    return [t for t in re.split(r"[ \t\n\r\x0c\x0b]", s) if t != ""]


def eq_fold(a, b):  # fold=True fixed
    return a.upper() == b.upper()


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


def is_marker_tok(t):  # fold=True
    return eq_fold(t, "NO")


def is_nan_tok(t):  # fold=True
    if not t:
        return False
    if t[0] in "+-":
        return eq_fold(t[1:], "nan")
    return eq_fold(t, "nan")


def is_data_tok(t):
    return is_decimal(t) or is_marker_tok(t) or is_nan_tok(t)


def is_directive(s):  # fold=True
    if not eq_fold(s[:4], "READ"):
        return False
    if s[4:5] != " ":
        return False
    if not (eq_fold(s[5:9], "SERR") or eq_fold(s[5:9], "TERR")):
        return False
    rest = s[9:]
    core = rest.split("!", 1)[0] if "!" in rest else rest
    ops = words(core)
    head_ws = bool(core) and _is_ws(core[0])
    return head_ws and len(ops) >= 1 and all(is_digits(o) for o in ops)


def shadow_line_type(line):
    """classify True line, transliterated (R/I shadow of lineType's impl)."""
    s = strip_ws(line)
    if s == "":
        return "comment"
    core = s.split("!", 1)[0] if "!" in s else s
    has_tail = "!" in s
    toks = words(core)
    if is_directive(s):
        return "command"
    if len(toks) >= 2 and all(is_marker_tok(t) for t in toks):
        return "new"
    if len(toks) == 0:
        return "comment" if has_tail else "reject"
    if all(is_data_tok(t) for t in toks):
        return "data,%d" % len(toks)
    return "reject"


def shadow_masked(v):
    """is_marker_tok True v, transliterated (R/I shadow of maskFlags' body)."""
    return is_marker_tok(v)


# ---------------------------------------------------------------------------
# fuzz generators (lines for site 1, cells for site 2)
# ---------------------------------------------------------------------------
def _rcase(rng, w):
    return "".join(c.upper() if rng.random() < 0.5 else c.lower() for c in w)


def _ws(rng):
    return rng.choice([" ", "  ", "   ", "\t", " \t ", " "])


def gen_line(rng):
    k = rng.random()
    if k < 0.30:
        n = rng.randint(0, 4)
        body = ("READ" + _ws(rng) + rng.choice(["SERR", "TERR", "XERR"])
                + "".join(_ws(rng) + str(rng.randint(0, 99)) for _ in range(n)))
        s = _rcase(rng, body)
    elif k < 0.50:
        s = _rcase(rng, _ws(rng).join(["NO"] * rng.randint(1, 5)))
    elif k < 0.80:
        toks = [rng.choice(["1", "-2.5", ".04", "1e-3", "2.", "+3.5E2", "NO",
                            "nan", "-nan", "abc", ".", "1.2.3", "12NO", "NAN", "No"])
                for _ in range(rng.randint(0, 5))]
        s = _rcase(rng, _ws(rng).join(toks))
        if rng.random() < 0.4:
            s += _ws(rng) + "!" + "".join(rng.choice("abc !12")
                                          for _ in range(rng.randint(0, 6)))
    else:
        s = "".join(rng.choice("READSERTNOnaeE0123456789 .+-!\t")
                    for _ in range(rng.randint(0, 18)))
    return rng.choice(["", "", " ", "\t"]) + s + rng.choice(["", "", " ", "\t"])


def gen_cell(rng):
    if rng.random() < 0.5:
        return _rcase(rng, "".join(rng.choice("NO") for _ in range(rng.randint(0, 4))))
    return "".join(rng.choice("NOno0123456789 ") for _ in range(rng.randint(0, 6)))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    # site 1 — classification
    for _ in range(N_FUZZ):
        line = gen_line(rng)
        count += 1
        sh, orc = shadow_line_type(line), oracle_line_type(line)
        if sh != orc:
            disagreements.append(("line", line, sh, orc))
            if len(disagreements) >= 5:
                break
    # site 2 — masking
    if not disagreements:
        for _ in range(N_FUZZ):
            cell = gen_cell(rng)
            count += 1
            sh, orc = shadow_masked(cell), oracle_masked(cell)
            if sh != orc:
                disagreements.append(("cell", cell, sh, orc))
                if len(disagreements) >= 5:
                    break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, inp, sh, orc in disagreements:
            print("  [%s] input=%r shadow=%r oracle=%r" % (kind, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of lineType + maskFlags agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
