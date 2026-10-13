#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9230 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` <-> `str`). This is `resolveParam` built on
              the hand-transliterated deep model `sever_tail` (== severTail) and
              the ParsedParam (name, optional type) construction. The deep model
              is exercised here as R/I content, NOT substituted by a builtin.

  * ORACLE  — `patch.diff`'s behaviour: the patched separation statement
              `argtype, argname = fieldarg.rsplit(None, 1)` (inside the
              try/except/else of DocFieldTransformer.transform), reproduced
              faithfully against the REAL builtin `str.rsplit`. The changed
              `transform` op is a local statement requiring a full docutils
              field_list to invoke in situ; the oracle reproduces exactly that
              statement's effect, calling the genuine patched callee.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample (e.g. a wrong wsCodes alphabet or a
first-vs-last separation bug in the transliterated sever_tail).

Runs stdlib-only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

SEED = 9230
N_FUZZ = 100_000

# wsCodes from Solution.lean (the R/I whitespace alphabet, transliterated).
WS_CODES = [0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x85, 0xa0,
            0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006,
            0x2007, 0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f,
            0x3000]
WS = set(WS_CODES)


# --- the R/I shadow: Solution.lean severTail/resolveParam, transliterated ----

def _is_ws(ch):
    return ord(ch) in WS


def _rstrip_ws(s):
    i = len(s)
    while i > 0 and _is_ws(s[i - 1]):
        i -= 1
    return s[:i]


def _tail_word(s):
    i = len(s)
    while i > 0 and not _is_ws(s[i - 1]):
        i -= 1
    return s[i:]


def _before_tail_word(s):
    i = len(s)
    while i > 0 and not _is_ws(s[i - 1]):
        i -= 1
    return s[:i]


def sever_tail(s):
    """severTail (Solution.lean pure region), transliterated."""
    s2 = _rstrip_ws(s)
    nm = _tail_word(s2)
    lead = _rstrip_ws(_before_tail_word(s2))
    if lead == "":
        return None
    return (lead, nm)


def shadow_resolve(descriptor, may_carry_type):
    """resolveParam (descriptor, mayCarryType) transliterated to str.
    Returns (name, type_or_None)."""
    if may_carry_type:
        r = sever_tail(descriptor)
        if r is None:
            return (descriptor, None)
        typ, nm = r
        return (nm, typ)
    return (descriptor, None)


# --- the oracle: patch.diff's behaviour (real str.rsplit) --------------------

def oracle_resolve(descriptor, may_carry_type):
    """The patched DocFieldTransformer.transform separation statement,
    reproduced faithfully:  argtype, argname = fieldarg.rsplit(None, 1)
    in a try/except/else, gated by `if typedesc.is_typed:`. Calls the genuine
    builtin str.rsplit. Returns (name, type_or_None)."""
    if not may_carry_type:
        return (descriptor, None)
    try:
        argtype, argname = descriptor.rsplit(None, 1)   # patched callee
    except ValueError:
        return (descriptor, None)
    else:
        return (argname, argtype)


def fuzz_inputs(n, rng):
    ws_chars = [chr(c) for c in WS_CODES]
    ordinary = list("ab(),[]._:dictstrZ0") + ["é", "•"]
    alphabet = ws_chars + ordinary
    # boundary cases first (plan §4.1 step 4)
    boundary = [
        "", "   ", "opc_meta", "int age", "Tuple[str, ...] items",
        "dict(str, str) opc_meta", "  a  b  c  ", "  x   y  ", "\ta\tb\t",
        "type name extra", "a b", "  leadingonly", "trailingonly   ",
        "a b", "a b", "a　b",
    ]
    for s in boundary:
        yield s
    for _ in range(n):
        k = rng.randint(0, 20)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        for flag in (True, False):
            count += 1
            shadow = shadow_resolve(s, flag)
            oracle = oracle_resolve(s, flag)
            if shadow != oracle:
                disagreements.append((s, flag, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, flag, sh, orc in disagreements:
            print("  input=%r may_carry_type=%r shadow=%r oracle=%r"
                  % (s, flag, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveParamMethod agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
