#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7324 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `evalBareIdent` impl region
              transliterated to Python over the real repo type (`str`), via the
              mapping.md bijection (`List Char` ↔ `str`, `['$']` ↔ "$",
              `List.drop prefix.length` ↔ `key[len(prefix):]`). The A-reference
              callee `compileName` is left as the *real* CPython
              compile-of-`Name` (G-CONF isolates the R/I legs; the A leg stays
              with G-AX), so the shadow runs the genuine compiler. The shadow's
              observable result is `Except CompileErr Bool`:
                ok b   -> the bare ident compiled and matched to b
                error  -> the compiler rejected the (prefixed) name.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `Expression.compile(ident).evaluate(matcher)` at base_commit (the
              real correctness oracle, G-RESOLVE). A ParseError/compile failure
              maps to `error`; a returned bool maps to `ok b`.

For a single bare identifier the modeled behaviour is `out = ok (matcher ident)`
and the patched pipeline must produce exactly that — for EVERY identifier,
including the three reserved spellings. They must agree on every input. Exit 0
iff zero disagreements; any disagreement is a mechanical R/I counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch.diff applied),
stdlib only. Fuzz seed pinned (mapping.md §4) for a deterministic verdict.
"""
import ast
import random
import re
import sys

SEED = 7324
N_FUZZ = 100_000

# match-ident grammar char class from expression.py lex: (\w|:|\+|-|\.|\[|\])+
# minus space/paren (those would split the token). Non-ASCII letters are \w too.
IDENT_CHARS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                   "0123456789_:+-.[]") + ["א", "ב", "ג", "é"]
# values that lex as OPERATORS, not a bare ident -> excluded from single-ident
# fuzz (the modeled slice is the bare-identifier path only).
OPERATOR_WORDS = {"and", "or", "not"}

# The exact lexer rule from expression.py: a candidate is a single bare IDENT
# iff this matches the whole string. The modeled slice (`evalBareIdent`) takes
# an already-lexed IDENT token, so the comparison is only meaningful for inputs
# that lex to exactly one IDENT (not an operator, not a multi-token string).
_LEX = re.compile(r"(:?\w|:|\+|-|\.|\[|\])+")


def is_single_ident(s):
    m = _LEX.match(s)
    return bool(s) and m is not None and m.group(0) == s and s not in OPERATOR_WORDS


# --- the R/I shadow: evalBareIdent, transliterated ---------------------------
def shadow_eval(ident, matcher):
    """R/I shadow of evalBareIdent's do block; compileName left as the real
    compile-of-Name callee (A-reference). Returns ('ok', bool) or ('error',)."""
    ident_prefix = "$"                                   # op1  (R)
    name = ident_prefix + ident                          # op2  (R)
    # op3 (A-reference): the real unchanged callee.
    try:
        node = ast.fix_missing_locations(
            ast.Expression(ast.Name(name, ast.Load())))
        compile(node, filename="<pytest match expression>", mode="eval")
    except ValueError:
        return ("error",)
    key = name[len(ident_prefix):]                        # op4  (R)
    return ("ok", bool(matcher(key)))                    # op5/6 (R/I)


# --- the oracle: patch.diff's behaviour --------------------------------------
def oracle_eval(ident, matcher):
    """Patched Expression.compile(ident).evaluate(matcher). ParseError or any
    compile failure -> ('error',); a returned bool -> ('ok', bool)."""
    from _pytest.mark.expression import Expression, ParseError
    try:
        result = Expression.compile(ident).evaluate(matcher)
    except ParseError:
        return ("error",)
    except ValueError:
        return ("error",)
    return ("ok", bool(result))


def make_matcher(true_set):
    return lambda key: key in true_set


def fuzz_idents(n, rng):
    # boundary: the three reserved spellings (the F2P cases) + near-misses
    forced = ["True", "False", "None", "true", "false", "none",
              "if", "else", "while", "1234", "a[bcd]", ".", "...", ":::",
              "אבגד", "not_and_or", "1234and", "notandor", "_", "x"]
    for s in forced:
        if is_single_ident(s):
            yield s
    produced = 0
    while produced < n:
        k = rng.randint(1, 16)
        s = "".join(rng.choice(IDENT_CHARS) for _ in range(k))
        if not is_single_ident(s):
            continue
        produced += 1
        yield s


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for ident in fuzz_idents(N_FUZZ, rng):
        # two matcher regimes: (a) matches exactly this ident (the test style),
        # (b) a fixed unrelated set -> exercises both matcher verdicts.
        for true_set in ({ident}, {"sentinel-no-match"}):
            count += 1
            matcher = make_matcher(true_set)
            shadow = shadow_eval(ident, matcher)
            oracle = oracle_eval(ident, matcher)
            if shadow != oracle:
                disagreements.append((ident, sorted(true_set), shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for ident, ts, sh, orc in disagreements:
            print("  ident=%r matcher_true=%r shadow=%r oracle=%r"
                  % (ident, ts, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of evalBareIdent agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
