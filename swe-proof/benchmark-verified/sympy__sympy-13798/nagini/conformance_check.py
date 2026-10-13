#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13798 (nagini).

SHADOW: the impl regions of model.py's `general_separator` and
`numeric_separator`, copied VERBATIM below with the contract calls
(Assert/Invariant) stripped. The @Pure helpers the impl consults
(`tok_dot`/`tok_times`/`tok_ldot`, `is_spacing_only`) copy over as plain
functions; `PSeq`/`ToSeq` become immutable-tuple shims (a small tuple subclass
carrying `.take`, which `is_spacing_only`'s empty-sequence literal uses). The
one @ContractOnly callee, `trimmed`, calls the REAL callee it models — the
builtin no-arg `str.strip()` — through the code-point bridge.

ORACLE: the REAL patched repo derivation per mapping.md — construct
`sympy.printing.latex.LatexPrinter({'mul_symbol': sym})` (the gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed) and read
the two derived settings `_settings['mul_symbol_latex']` (general separator)
and `_settings['mul_symbol_latex_numbers']` (between-numbers separator).

Type bridge (mapping.md section 2): the repo setting is `None` or a `str`;
the model carrier is `Optional[List[int]]` of Unicode code points. Strings
are generated first and converted via `[ord(ch) for ch in s]` for the shadow;
the oracle's `str` results are converted the same way for an exact
code-point-list comparison. No numeric abstraction is involved.

Input domain: exactly the model's Requires — `None`, or any list of Unicode
code points (i.e. any selector string). The fuzz mix deliberately
over-represents the interesting regimes: the recognised tokens, the seven
spacing-only tokens, whitespace-padded variants of both (built from the full
class of code points the real trim removes), all-whitespace tokens, and
arbitrary ASCII/astral strings.

>= 1e5 Requires-satisfying inputs: exhaustive over short strings from a
selector-relevant alphabet + hand-picked boundary cases + fuzz to a total of
100000+. Pinned fuzz seed: 137980.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from itertools import product
from typing import List, Optional

SEED = 137980
N_TOTAL = 100_000


# --- shims for the sequence carrier -------------------------------------------

class _Seq(tuple):
    """Immutable code-point sequence with the tiny slice API the pure helpers
    use."""
    def take(self, n):
        return _Seq(self[:n])

    def drop(self, n):
        return _Seq(self[n:])


def PSeq(*items):
    """Immutable sequence literal."""
    return _Seq(items)


def ToSeq(lst):
    """Immutable snapshot of a list's contents."""
    return _Seq(lst)


# --- the @ContractOnly callee: calls the REAL repo callee (builtin str.strip) --

def trimmed(s):
    """The real whitespace trim, bridged over code points: decode, call the
    builtin no-arg strip, re-encode."""
    return _Seq(ord(ch) for ch in "".join(chr(c) for c in s).strip())


# --- @Pure helpers from model.py the impl regions consult, contracts stripped --

def tok_ldot():
    # "ldot"
    return PSeq(108, 100, 111, 116)


def tok_dot():
    # "dot"
    return PSeq(100, 111, 116)


def tok_times():
    # "times"
    return PSeq(116, 105, 109, 101, 115)


def is_spacing_only(t):
    """A trimmed token that consists solely of LaTeX spacing: the empty token,
    a single space, or a bare spacing command."""
    return (t == PSeq(0).take(0)            # ""
            or t == PSeq(32)                # " "
            or t == PSeq(92)                # "\\"
            or t == PSeq(92, 44)            # "\\,"
            or t == PSeq(92, 58)            # "\\:"
            or t == PSeq(92, 59)            # "\\;"
            or t == PSeq(92, 113, 117, 97, 100))   # "\\quad"


# --- the impl regions of model.py, verbatim, contract calls stripped -----------

def general_separator(sym: Optional[List[int]]) -> List[int]:
    if sym is None:
        return [32]
    s = ToSeq(sym)
    if s == tok_dot():
        return [32, 92, 99, 100, 111, 116, 32]
    if s == tok_times():
        return [32, 92, 116, 105, 109, 101, 115, 32]
    if s == tok_ldot():
        return [32, 92, 44, 46, 92, 44, 32]
    res = []  # type: List[int]
    i = 0
    while i < len(sym):
        res = res + [sym[i]]
        i = i + 1
    return res


def numeric_separator(sym: Optional[List[int]]) -> List[int]:
    if sym is None:
        return [32, 92, 99, 100, 111, 116, 32]
    s = ToSeq(sym)
    if s == tok_dot():
        return [32, 92, 99, 100, 111, 116, 32]
    if s == tok_times():
        return [32, 92, 116, 105, 109, 101, 115, 32]
    if s == tok_ldot():
        return [32, 92, 44, 46, 92, 44, 32]
    t = trimmed(s)
    if is_spacing_only(t):
        return [32, 92, 99, 100, 111, 116, 32]
    res = []  # type: List[int]
    i = 0
    while i < len(sym):
        res = res + [sym[i]]
        i = i + 1
    return res


# --- differential driver --------------------------------------------------------

def check_case(LatexPrinter, sym_str):
    """Run shadow and oracle on one selector (None or a str); return an error
    string on disagreement, else None."""
    sym = None if sym_str is None else [ord(ch) for ch in sym_str]
    shadow_gen = general_separator(sym)
    shadow_num = numeric_separator(sym)
    try:
        p = LatexPrinter({'mul_symbol': sym_str})
        real_gen = [ord(ch) for ch in p._settings['mul_symbol_latex']]
        real_num = [ord(ch) for ch in p._settings['mul_symbol_latex_numbers']]
    except Exception as exc:  # in-domain input must not raise
        return ("DISAGREEMENT (oracle raised)\n  input: mul_symbol=%r"
                "\n  shadow general=%r numeric=%r\n  real raised %s: %s"
                % (sym_str, shadow_gen, shadow_num, type(exc).__name__, exc))
    if shadow_gen != real_gen or shadow_num != real_num:
        return ("DISAGREEMENT\n  input: mul_symbol=%r"
                "\n  shadow: general=%r numeric=%r"
                "\n  real:   general=%r numeric=%r"
                % (sym_str, shadow_gen, shadow_num, real_gen, real_num))
    return None


# The seven spacing-only tokens and the recognised selector tokens, as strings.
SPACING_ONLY = ["", " ", "\\", "\\,", "\\:", "\\;", "\\quad"]
RECOGNISED = [None, "dot", "times", "ldot"]


def boundary_cases(ws_chars):
    """Hand-picked in-domain corners: the unset selector, the recognised
    tokens, the spacing-only tokens, whitespace-padded variants of each
    (over the full class of code points the real trim removes), casing and
    near-miss variants of the recognised tokens, all-whitespace tokens, and
    ordinary custom selectors."""
    cases = []
    cases += RECOGNISED
    cases += SPACING_ONLY
    cases += ["\\cdot", "\\times", "\\,.\\,", " \\cdot ", " \\times ",
              " \\,.\\, ", "*", "x", "ab", "a b", "a\\,b", "Dot", "DOT",
              "dots", "do", "times2", "ldots", "l dot", "\\ ", "  ",
              "\\quads", "\\qquad", "\\;\\;", ",", ";", ":"]
    for core in SPACING_ONLY[1:] + ["dot", "times", "ldot", "x"]:
        for w in ws_chars[:10]:
            cases.append(w + core)
            cases.append(core + w)
            cases.append(w + core + w)
    cases += ws_chars                      # all-whitespace single chars
    cases += ["".join(ws_chars[:5]), "\t \t", "\n"]
    return cases


def main():
    # REAL patched derivation (mapping.md section 1) — importable from /testbed.
    from sympy.printing.latex import LatexPrinter

    # Code points the real trim removes from the ends, up to a generous bound
    # — used to build padded variants whose trimmed form hits each branch.
    ws_chars = [chr(c) for c in range(0x3001) if chr(c).strip() == ""]

    checked = 0

    # --- boundary inputs -------------------------------------------------------
    boundary = boundary_cases(ws_chars)
    for s in boundary:
        err = check_case(LatexPrinter, s)
        if err:
            print(err)
            return 1
        checked += 1

    # --- exhaustive short strings over a selector-relevant alphabet ------------
    # Every string of length <= 3 over an alphabet mixing the spacing-command
    # characters, a whitespace char, and ordinary letters: covers all short
    # recognised/spacing/near-miss shapes exhaustively.
    exhaustive = 0
    alpha = ["\\", ",", ":", ";", " ", "d", "o", "t", "x"]
    for n in range(0, 4):
        for tup in product(alpha, repeat=n):
            err = check_case(LatexPrinter, "".join(tup))
            if err:
                print(err)
                return 1
            exhaustive += 1
    checked += exhaustive

    # --- randomized fuzz to >= N_TOTAL ------------------------------------------
    rng = random.Random(SEED)
    ascii_printable = [chr(c) for c in range(33, 127)]
    fuzz_alpha = (["\\", ",", ":", ";", "d", "o", "t", "q", "u", "a", "x",
                   "*", "+", "(", ")", " "] + ws_chars[:8] + ascii_printable)
    n_fuzz = N_TOTAL - checked
    for k in range(n_fuzz):
        mode = k % 5
        if mode == 0:
            # a spacing-only or recognised core with random whitespace padding
            core = rng.choice(SPACING_ONLY + ["dot", "times", "ldot"])
            lead = "".join(rng.choice(ws_chars) for _ in range(rng.randint(0, 3)))
            tail = "".join(rng.choice(ws_chars) for _ in range(rng.randint(0, 3)))
            s = lead + core + tail
        elif mode == 1:
            # short strings over the selector-relevant alphabet
            s = "".join(rng.choice(fuzz_alpha) for _ in range(rng.randint(0, 8)))
        elif mode == 2:
            # arbitrary printable-ASCII custom selectors
            s = "".join(rng.choice(ascii_printable)
                        for _ in range(rng.randint(1, 12)))
        elif mode == 3:
            # high code points and astral plane (surrogates excluded)
            n = rng.randint(0, 6)
            s = ""
            while len(s) < n:
                c = rng.randint(0, 0x2FFFF)
                if 0xD800 <= c <= 0xDFFF:
                    continue
                s += chr(c)
        else:
            # occasionally the unset selector, else whitespace-heavy strings
            if rng.random() < 0.05:
                s = None
            else:
                s = "".join(rng.choice(ws_chars + [",", "\\"])
                            for _ in range(rng.randint(0, 6)))
        err = check_case(LatexPrinter, s)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched separator derivation on %d "
          "inputs (%d boundary + %d exhaustive len<=3 + %d fuzz, seed %d)."
          % (checked, len(boundary), exhaustive, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
