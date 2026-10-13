#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-16450.

Executes the REAL sympy property-inference engine (the unchanged callee the
fixed construction composes: `Dummy(name, positive=True, **base)` followed by
reading `.assumptions0`) and asserts that every observation matches the model,
as encoded in model.py.

Two obligations:

  (A-consumed) the `resolve` axiom (model.py axioms region). For a base
      declaration `base` (a symbol's stated assumptions, which never contains
      `positive` because the symbol is replaced precisely when its sign is
      undecided), the engine `Dummy(name, positive=True, **base)`:
        * never discards a fact in `base` -- every key of `base` is derived in
          the resulting `.assumptions0` with the SAME truth value;
        * derives `positive=True` (the added "greater than zero").
      This is asserted on every input where the declaration is CONSISTENT
      (i.e. the engine returns rather than raising InconsistentAssumptions).
      When the declaration is inconsistent the real engine raises; the modeled
      construction is simply not the operation specified there, and the gold
      patch raises identically (so the two remain equivalent out of domain).

  (model fidelity / A-reference) the modeled `posify_replacement(base)` ==
      the REAL `posify(symbol)` assumption transformation: for a symbol `s`
      with `is_positive is None`, `posify(s)[0].assumptions0` equals the engine
      result `Dummy(s.name, positive=True, **s.assumptions0).assumptions0`, and
      in particular preserves every stated fact (incl. the issue's `finite`).
      The pre-patch construction `Dummy(s.name, positive=True)` (dropping
      `**s.assumptions0`) is also checked to be DETECTABLY wrong whenever the
      base carries a fact the bare `positive=True` does not imply (e.g.
      `finite=True`), confirming the spec discriminates.

Imports only sympy (the repo under test, whose assumption engine IS the real
callee) and the standard library. Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import Symbol, Dummy
from sympy.core.assumptions import _assume_rules
from sympy.simplify.simplify import posify


# All single-fact assumption predicate names sympy understands.
ASSUMPTION_KEYS = sorted(_assume_rules.defined_facts)


def engine(base, add_positive=True):
    """The REAL property-inference engine: build the stand-in Dummy from the
    base declaration (+ optionally `positive=True`) and read its effective
    assumptions. Returns None if the declaration is inconsistent (the engine
    raises), which is out of the modeled operation's domain.
    Mirrors model.py `resolve(base, add_positive)`."""
    asm = dict(base)
    if add_positive:
        asm["positive"] = True
    try:
        d = Dummy("x", **asm)
    except Exception:
        return None
    return d.assumptions0


# Counters: cases that exercise each obligation (printed for evidence).
STATS = {"consistent": 0, "inconsistent_lockstep": 0}


def check_resolve_axiom(s):
    """A-consumed: the engine never drops a base fact, derives positive, and its
    output IS exactly the engine's effective-property map (the model's
    `Result() is derived(base, True)` totality clause). Lock-step on the raise
    path: a base whose declaration is inconsistent with `positive=True` makes
    BOTH the engine and the real `posify` raise -- this is asserted here, not
    silently skipped, so the implicit-totality region of the `resolve` axiom is
    pinned (G-AX defect 2 fix).

    `s` must be a *replaced* symbol (`is_positive is None`), whose stated
    assumptions (`s.assumptions0`) by construction never contain `positive`."""
    base = s.assumptions0
    assert "positive" not in base, (
        "not a replaced symbol's base (sign already decided): %r" % (base,))
    derived = engine(base, add_positive=True)
    if derived is None:
        # Inconsistent declaration: the model leaves this out of domain via the
        # absence of an `Exsures` -- which is sound ONLY because the gold patch
        # (real posify) raises in LOCK-STEP. Assert that, rather than skipping.
        raised = False
        try:
            posify(s)
        except Exception:
            raised = True
        assert raised, (
            "resolve axiom unsound: engine raises (inconsistent %r) but real "
            "posify did NOT raise -- the no-Exsures totality region is not "
            "covered in lock-step" % (base,))
        STATS["inconsistent_lockstep"] += 1
        return
    STATS["consistent"] += 1
    # every base fact preserved with the same truth value
    for k, v in base.items():
        assert k in derived and derived[k] == v, (
            "resolve axiom unsound: base fact %r=%r not preserved in %r"
            % (k, v, derived))
    # positive derived True
    assert derived.get("positive") is True, (
        "resolve axiom unsound: positive not derived from %r -> %r"
        % (base, derived))


def check_posify_fidelity(s):
    """Model fidelity: real posify's transformation == the engine result, and
    the pre-patch (dropping **assumptions0) is detectably wrong when the base
    carries a non-positive-implied fact."""
    if s.is_positive is not None:
        return  # not a replaced symbol
    base = s.assumptions0
    derived = engine(base, add_positive=True)

    # real posify of the single symbol
    try:
        eq, _rep = posify(s)
        real = eq.assumptions0
    except Exception:
        # inconsistent base: gold posify raises; engine must agree (None)
        assert derived is None, (
            "posify raised but engine returned for base %r" % (base,))
        return

    assert derived is not None, (
        "engine returned None but posify succeeded for base %r" % (base,))
    assert real == derived, (
        "posify fidelity broken for symbol with base %r: posify=%r engine=%r"
        % (base, real, derived))
    # every stated fact preserved by the real posify (the fix's guarantee)
    for k, v in base.items():
        assert real.get(k) == v, (
            "posify dropped stated fact %r=%r (got %r)" % (k, v, real))

    # pre-patch detection: dropping **base loses any fact bare positive=True
    # does not imply.
    bare = engine({}, add_positive=True)
    for k, v in base.items():
        if bare.get(k) != v:
            assert real.get(k) == v and bare.get(k) != v, (
                "spec does not discriminate on base fact %r=%r" % (k, v))


def main():
    # --- the issue's exact example -----------------------------------------
    # The issue-16438 regression: posify(Symbol('k', finite=True)) must retain
    # the finiteness fact (and never None it). We assert the version-stable
    # behavioural property rather than the exact assumptions0 dict (whose extra
    # derived keys vary across sympy releases); the F2P test owns the exact dict.
    k = Symbol("k", finite=True)
    eq, _ = posify(k)
    assert eq.is_finite is True, (
        "issue-16438 regression: posify(Symbol('k', finite=True)).is_finite=%r"
        % (eq.is_finite,))
    assert eq.is_positive is True, (
        "posify must make the stand-in positive: is_positive=%r"
        % (eq.is_positive,))
    assert eq.assumptions0.get("finite") is True and \
        eq.assumptions0.get("positive") is True, eq.assumptions0
    check_posify_fidelity(k)
    check_resolve_axiom(k)

    # --- boundary single-fact bases ----------------------------------------
    single_true = ["finite", "integer", "rational", "even", "odd", "prime",
                   "real", "complex", "commutative", "hermitian", "algebraic",
                   "nonzero", "irrational", "transcendental", "composite"]
    for key in single_true:
        try:
            s = Symbol("x", **{key: True})
        except Exception:
            continue
        if s.is_positive is None:
            check_resolve_axiom(s)
        check_posify_fidelity(s)
    # empty base (a plain symbol)
    check_resolve_axiom(Symbol("x"))
    check_posify_fidelity(Symbol("x"))

    # --- randomized fuzz over real consistent symbols ----------------------
    rng = random.Random(16450)
    checked = 0
    for _ in range(20000):
        n = rng.randint(0, 4)
        keys = rng.sample(ASSUMPTION_KEYS, n)
        asm = {kk: rng.choice([True, False]) for kk in keys}
        try:
            s = Symbol("x", **asm)
        except Exception:
            continue  # inconsistent stated assumptions: not a real symbol
        if s.is_positive is None:
            check_resolve_axiom(s)
        check_posify_fidelity(s)
        checked += 1

    print("G-AX OK: resolve axiom (A-consumed) sound + posify fidelity "
          "(A-reference) == real engine on the issue example + %d single-fact "
          "+ %d fuzz consistent symbols. resolve obligations exercised on %d "
          "consistent bases; the no-Exsures totality region was checked in "
          "LOCK-STEP (engine-raises <=> real-posify-raises) on %d inconsistent "
          "base+positive declarations (none silently skipped)."
          % (len(single_true), checked, STATS["consistent"],
             STATS["inconsistent_lockstep"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
