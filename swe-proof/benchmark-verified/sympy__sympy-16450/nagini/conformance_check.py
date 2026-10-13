#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16450 (nagini).

SHADOW  — the impl region of model.py copied VERBATIM (the model IS Python;
          the single impl statement contains no contract calls to strip —
          Requires/Ensures live outside the impl markers). The @ContractOnly
          axiom callee `resolve` is, per the contract, bound to the REAL
          repo callee it models (mapping.md §3.1: the unchanged sympy
          assumption-inference engine — build a Dummy from the base
          declaration plus positive=True and read back its `.assumptions0`)
          through the token bridge below. The @Pure token helpers POSITIVE /
          FINITE copy over as plain functions.

BRIDGE  — mapping.md §2 "Type abstraction": a symbol's assumption mapping
          (`dict[str, bool]`) is modelled as `Dict[int, bool]` from an
          assumption-name token to its truth value; each assumption name ↔ a
          distinct int token, with `POSITIVE()==0` ↔ 'positive' and
          `FINITE()==1` ↔ 'finite'. Realized here by a name↔token intern
          table seeded with those two pins. Only membership and per-key truth
          value are observed, exactly what the bijection licenses.

ORACLE  — the REAL patched repo function the model models (mapping.md §1:
          the per-symbol replacement `posify` builds for a free symbol whose
          sign is undecided). PYTHONPATH=/testbed with the gold patch applied
          by the gate before this script runs. For a symbol `s` with
          `s.is_positive is None`, the observable is
          `posify(s)[0].assumptions0` (the stand-in's effective assumptions),
          diffed against the shadow run on the bridged token map of the SAME
          `s.assumptions0`.

DOMAIN  — Requires-satisfying inputs are `stated = s.assumptions0` for a
          constructible symbol `s` with `s.is_positive is None` (such a map
          never contains 'positive', satisfying the precondition). When the
          base together with positive=True is an inconsistent declaration the
          engine raises, so the shadow raises; the oracle must raise in
          LOCK-STEP (mapping.md: the modelled operation is out of domain
          there and both sides raise identically) — asserted, and a
          raise/return mismatch is a disagreement.

INPUTS  — boundary cases (empty base; the issue's bounded/finite case; every
          single-fact base, both truth values; targeted multi-fact combos)
          plus fuzz over 0..4-fact assumption maps drawn from the full set of
          sympy assumption predicates until >= 1e5 Requires-satisfying inputs
          are diffed. Pinned seed: 164500. The shadow/oracle pair is a pure
          deterministic function of the base map, so observations are
          memoized per distinct base; every generated input is still
          individually counted and diffed.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random) + the repo under test.
"""
import random
import sys

SEED = 164500
N_INPUTS = 100_000

from sympy import Symbol, Dummy
from sympy.core.assumptions import _assume_rules
from sympy.simplify.simplify import posify


# ---------------------------------------------------------------------------
# Token bridge: assumption-name str <-> int token (mapping.md §2). POSITIVE
# and FINITE are the distinguished pins; every other name gets a fresh token.
# ---------------------------------------------------------------------------

_token_of = {"positive": 0, "finite": 1}
_name_of = {0: "positive", 1: "finite"}


def to_token(name):
    t = _token_of.get(name)
    if t is None:
        t = len(_token_of)
        _token_of[name] = t
        _name_of[t] = name
    return t


def to_token_map(str_map):
    return {to_token(k): v for k, v in str_map.items()}


# ---------------------------------------------------------------------------
# The @Pure token helpers, copied over as plain functions (pure region).
# ---------------------------------------------------------------------------

def POSITIVE() -> int:
    # token for the "greater than zero" declaration the replacement adds
    return 0


def FINITE() -> int:
    # token for the "bounded / not infinite" property the issue centres on
    return 1


# ---------------------------------------------------------------------------
# The @ContractOnly axiom callee `resolve`, bound to the REAL repo callee it
# models (mapping.md §3.1): the unchanged sympy assumption-inference engine,
# lifted through the token bridge. Raises whatever the engine raises on an
# inconsistent declaration (out of the modelled domain; lock-step below).
# ---------------------------------------------------------------------------

def resolve(base, add_positive):
    asm = {_name_of[t]: v for t, v in base.items()}
    if add_positive:
        asm["positive"] = True
    d = Dummy("x", **asm)                  # REAL repo engine
    return to_token_map(d.assumptions0)


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM (contract calls live outside the impl
# markers; nothing to strip).
# ---------------------------------------------------------------------------

def positive_standin_properties(stated):
    # The declaration for the stand-in is the original quantity's stated
    # properties (the base) together with the added "greater than zero".
    return resolve(stated, True)


# ---------------------------------------------------------------------------
# Differential check on one base assumption map. Returns True if the input
# was Requires-satisfying (counted), False if out of the modelled domain
# (skipped, not counted). Disagreements are appended to `disagreements`.
# Deterministic per base, so callers may memoize by base key.
# ---------------------------------------------------------------------------

def check_case(asm, disagreements):
    try:
        s = Symbol("x", **asm)
    except Exception:
        return False        # not a constructible symbol: no stated map exists
    if s.is_positive is not None:
        return False        # sign already decided: posify does not replace it
    stated = s.assumptions0
    assert "positive" not in stated, (
        "domain violation: replaced symbol states 'positive': %r" % (stated,))

    # shadow: the verbatim impl over the bridged token map
    shadow_exc = None
    shadow = None
    try:
        shadow = positive_standin_properties(to_token_map(stated))
    except Exception as exc:
        shadow_exc = exc

    # oracle: the REAL patched repo per-symbol replacement
    oracle_exc = None
    oracle = None
    try:
        eq, _reps = posify(s)
        oracle = eq.assumptions0
    except Exception as exc:
        oracle_exc = exc

    if (shadow_exc is None) != (oracle_exc is None):
        disagreements.append((stated, "shadow=%r" % (shadow_exc or shadow,),
                              "oracle=%r" % (oracle_exc or oracle,)))
        return True
    if shadow_exc is not None:
        # both raise on the inconsistent declaration: lock-step agreement
        return True
    if shadow != to_token_map(oracle):
        disagreements.append((stated, "shadow=%r" % (shadow,),
                              "oracle=%r (tokens %r)"
                              % (oracle, to_token_map(oracle))))
    return True


def boundary_bases():
    yield {}                               # a plain symbol, empty base
    yield {"finite": True}                 # the issue's bounded case
    # every single-fact base, both truth values
    for key in sorted(_assume_rules.defined_facts):
        yield {key: True}
        yield {key: False}
    # targeted multi-fact combos (stated facts the added positivity must not
    # discard, plus negative-truth-value facts)
    yield {"integer": True, "odd": True}
    yield {"rational": True, "even": True}
    yield {"finite": True, "integer": True}
    yield {"finite": False}
    yield {"zero": False}
    yield {"imaginary": False}
    yield {"real": True, "finite": True}
    yield {"complex": True, "algebraic": True}
    yield {"irrational": True, "finite": True}
    yield {"prime": True}                  # sign decided: out of domain (skip)
    yield {"commutative": False}
    yield {"hermitian": True, "finite": True}


def main():
    keys = sorted(_assume_rules.defined_facts)
    rng = random.Random(SEED)
    disagreements = []
    counted = 0

    for asm in boundary_bases():
        if check_case(asm, disagreements):
            counted += 1
        if disagreements:
            break

    # Fuzz over 0..4-fact assumption maps; memoized per distinct base key
    # (the check is deterministic per base), each drawn input still counted
    # and diffed.
    memo = {}   # key -> fired (Requires-satisfying)
    draws = 0
    while counted < N_INPUTS and not disagreements:
        draws += 1
        n = rng.randint(0, 4)
        picked = rng.sample(keys, n)
        asm = {k: rng.random() < 0.75 for k in picked}
        key = tuple(sorted(asm.items()))
        fired = memo.get(key)
        if fired is None:
            fired = check_case(asm, disagreements)
            memo[key] = fired
        if fired:
            counted += 1

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) after %d counted inputs "
              "(seed=%d):" % (len(disagreements), counted, SEED))
        for stated, sh, orc in disagreements[:10]:
            print("  stated=%r\n    shadow(impl region) %s\n"
                  "    real patched repo   %s" % (stated, sh, orc))
        return 1

    print("G-CONF OK: model.py impl shadow (real assumption-inference engine "
          "through the token bridge) agrees with the real patched repo "
          "per-symbol replacement on %d Requires-satisfying inputs "
          "(%d distinct fuzz bases, seed=%d), 0 disagreements."
          % (counted, len(memo), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
