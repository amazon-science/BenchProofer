#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13798 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `resolveMulSeparators` impl
              region, transliterated to Python over the *real* repo types:
              resolve the general separator (the named-table value, else the
              symbol verbatim) and the numeric separator (the table value for the
              falling-back key `sym or 'dot'`, else the dot for a spacing-only
              trimmed symbol, else the symbol verbatim). The named-symbol table
              and the spacing whitelist are the REAL repo constants (copied from
              latex.py), so the lookup data is repo code, not an invented model.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched real
              `sympy.printing.latex.LatexPrinter`, instantiated with the given
              `mul_symbol`, reporting the two derived settings
              `(mul_symbol_latex, mul_symbol_latex_numbers)` (the real
              correctness oracle, G-RESOLVE — the harness applies patch.diff
              before this runs).

Both are classified into the `Except MulErr (String × String)` outcome domain: a
constructor raising ↔ ("error",); a completed constructor ↔ ("ok", (general,
numeric)). They must agree for every symbol. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Note (scope): every impl op is R/I — the resolution is computed entirely from
the supplied symbol and the routine's own inline recognized-name table and
spacing-form list; there is no unchanged external callee, hence no axiom and no
G-AX in this bundle. On the gold-patched oracle every symbol resolves (the
constructor is total), so the ("error",) outcome — the unresolved alternative
`MulErr` — is UNREACHABLE through the patched oracle; it is purely the modeling
vehicle the prepatch uses to reject an unrecognized symbol (its divergence from
the total spec is what G-DIFF observes). G-CONF here refutes the resolved-pair
R/I legs against the real patched printer over the full fuzz domain.

Runs in-container (the prebuilt SWE-Bench instance image), the sympy under test
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from sympy.printing.latex import LatexPrinter


SEED = 13798
N_FUZZ = 100_000


# --- the REAL repo constants (latex.py:152-157, post-patch 172-173) -----------
MUL_SYMBOL_TABLE = {
    None: r" ",
    "ldot": r" \,.\, ",
    "dot": r" \cdot ",
    "times": r" \times ",
}
SPACING_SYMS = ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']


def num_key(sym):
    """numKey: `sym or 'dot'`."""
    return sym or "dot"


def shadow(sym):
    """R/I transliteration of resolveMulSeparators. Resolution is total, so it
    always returns ('ok', (general, numeric)); the ('error',) leg is never
    produced (it is reachable only through the pre-patch bare index, G-AX)."""
    # general separator
    try:
        first = MUL_SYMBOL_TABLE[sym]
    except KeyError:
        first = sym
    # numeric separator
    try:
        numbers = MUL_SYMBOL_TABLE[num_key(sym)]
    except KeyError:
        if sym.strip() in SPACING_SYMS:
            numbers = MUL_SYMBOL_TABLE["dot"]
        else:
            numbers = sym
    return ("ok", (first, numbers))


def oracle(sym):
    """patch.diff's behaviour: the gold-patched real LatexPrinter. Returns
    ('error',) if the constructor raises, else ('ok', (general, numeric))."""
    try:
        p = LatexPrinter({"mul_symbol": sym})
    except Exception:
        return ("error",)
    return ("ok", (p._settings["mul_symbol_latex"],
                   p._settings["mul_symbol_latex_numbers"]))


def fuzz_inputs(n, rng):
    # --- boundary cases first (plan §4.1 step 4) -----------------------------
    # the default and the four recognized named symbols (backwards compat)
    yield None
    yield "dot"
    yield "ldot"
    yield "times"
    # the F2P symbol: a thin space -> general verbatim, numeric falls back to dot
    yield "\\,"
    # the other spacing-only forms (numeric -> dot)
    yield ""
    yield " "
    yield "\\"
    yield "\\:"
    yield "\\;"
    yield "\\quad"
    # arbitrary user symbols: used verbatim for both separators
    yield "x"
    yield "*"
    yield "\\ast"
    yield "\\star"
    yield " \\cdot "          # equals the dot value but supplied as an arbitrary str
    yield "  \\,  "           # spacing form with surrounding whitespace -> stripped to '\\,'
    yield "\\,\\,"            # not a spacing-only singleton -> verbatim
    yield "ldot "             # trailing space: not a table key -> verbatim
    # full str.strip() whitespace domain: symbols that strip to '' (or to a
    # whitelist form) via NON-ASCII / control whitespace. Python str.strip()
    # strips the entire Unicode str.isspace() set (incl. \x0b, \x0c, the
    # \x1c-\x1f separators, NEL, NBSP, U+1680, U+2000-200A, U+2028/29,
    # U+202F, U+205F, U+3000) -> numeric separator falls back to the dot.
    yield "\x0b"              # vertical tab
    yield "\x0c"              # form feed (the G-PANEL-2 diverging input)
    yield "\x1c"              # file separator
    yield "\x1d"              # group separator
    yield "\x1e"              # record separator
    yield "\x1f"              # unit separator
    yield "\x85"              # NEL
    yield "\xa0"              # no-break space
    yield "\u1680"            # ogham space mark
    yield "\u2000"            # en quad
    yield "\u2009"            # thin space character
    yield "\u200a"            # hair space
    yield "\u2028"            # line separator
    yield "\u2029"            # paragraph separator
    yield "\u202f"            # narrow no-break space
    yield "\u205f"            # medium mathematical space
    yield "\u3000"            # ideographic space
    yield "\u200b"            # ZWSP: NOT str.isspace() -> verbatim, no fallback
    yield "\u180e"            # Mongolian vowel separator: NOT whitespace -> verbatim
    yield "\x0c\\,\x0c"       # whitelist form wrapped in control whitespace -> dot
    yield "\xa0x\xa0"         # non-spacing core wrapped in NBSP -> verbatim

    # --- randomized fuzz -----------------------------------------------------
    named = [None, "dot", "ldot", "times"]
    spacing = ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']
    latex_cmds = ["\\ast", "\\bullet", "\\times", "\\cdot", "\\star", "\\circ",
                  "\\cdotp", "\\mathbin{*}"]
    plains = ["x", "*", "X", "·", "o", "..", "a b"]
    for _ in range(n):
        roll = rng.random()
        if roll < 0.20:
            yield rng.choice(named)
        elif roll < 0.45:
            # spacing form, sometimes wrapped in whitespace
            s = rng.choice(spacing)
            if rng.random() < 0.4:
                pad = " " * rng.randint(1, 3)
                s = pad + s + (" " * rng.randint(0, 2))
            yield s
        elif roll < 0.75:
            yield rng.choice(latex_cmds)
        else:
            yield rng.choice(plains)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for sym in fuzz_inputs(N_FUZZ, rng):
        count += 1
        try:
            sh = shadow(sym)
            orc = oracle(sym)
        except Exception as e:  # unexpected -> record and stop early
            disagreements.append((sym, "exc:%r" % e, None))
            if len(disagreements) >= 5:
                break
            continue
        if sh != orc:
            disagreements.append((sym, sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for sym, sh, orc in disagreements:
            print("  sym=%r shadow=%r oracle=%r" % (sym, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveMulSeparators agrees with patch.diff "
          "(gold-patched LatexPrinter) behaviour on %d symbols (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
