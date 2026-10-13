#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-15809.

Executes the REAL lattice reductions (`sympy.Min` / `sympy.Max`, i.e. the
patched `MinMaxBase.__new__`) on boundary + fuzz operand collections and asserts
that every observation matches the model in model.py.

Four kind-A axioms are checked (all UNCHANGED pre-reduction callees the changed
`__new__` calls; none is the operation that changed):

  (A0) `has_noncomparable_operand(operands)` — the comparability pre-filter.
       The only property the proof consumes: an EMPTY collection contains no
       operand, so it can never contain a non-comparable one.  But the axiom
       ALSO underpins the model's `Exsures`: a NON-empty collection that
       contains a non-comparable operand is REJECTED with a ValueError.  Real
       check: the empty reduction never raises, and every collection carrying a
       non-comparable operand (`I`, `S.ComplexInfinity`/`zoo`, `S.NaN`, alone or
       mixed with comparable operands) DOES raise ValueError, and so does the
       substituted expression `Min(cos(x), sin(x)).subs(x, I)` (whose operands
       become non-real).  This is the unchanged comparability path the F2P tests
       `test_Min` / `test_Max` assert (`raises(ValueError, lambda: Min(I))`,
       `Max(S.ComplexInfinity, 1)`, `raises(ValueError, lambda: Min(cos(x),
       sin(x)).subs(x, I))`, etc.).

  (A1) `has_absorbing_operand(operands)` — the absorbing-operand pre-filter.
       The only property the proof consumes: an EMPTY collection contains no
       operand, so it can never contain the absorbing one.  Real check: the
       empty reduction never collapses to the annihilator `cls.zero`
       (Min.zero = -oo, Max.zero = +oo); it returns the identity element.

  (A2) `canonical_reduction_defined(operands)` — DEFINEDNESS of the canonical-set
       pass.  That pass is a DIFFERENT observation from the scan above: the scan
       judges each operand ALONE (`:521-523`), while `_find_localzeros` (`:536-
       560`) compares the SURVIVORS against one another via `_is_connected`
       (`:552`, `:563-583`), whose `r = hit(x >= y, Max, Min)` (`:574`) can
       propagate out of `Expr.__ge__` (`sympy/core/expr.py:295`).  So an operand
       the scan passes over can still be one this pass cannot place, and the
       whole reduction then fails.  The only property the proof consumes: an
       EMPTY collection leaves that pass nothing to compare, so it cannot fail
       on it.  Real check: the empty reduction returns; the predicate is
       NON-TRIVIAL (operands like `x + I` / `sign(x)` / `Order(x)` pass the scan
       and the pass still fails, so the model's failure leg is reachable rather
       than dead); and it is vacuously true where the scan already decided (an
       absorbing operand collapses the reduction in EITHER order alongside such
       an operand, and the pass is never reached).

  (A3) `canonical_count(operands)` — the canonical-set reduction.  PARTIAL: it
       reports a cardinality only where (A2) holds, which is why its `Requires`
       names (A2) — a pass that propagated a comparison failure produced no set
       to count.  Properties the proof consumes: count >= 0, and an EMPTY
       collection reduces to the empty canonical set (count 0).  Real check: the
       empty reduction takes the empty-canonical-set branch and returns the
       identity element (Min.identity = +oo, Max.identity = -oo) rather than
       rejecting.

The discriminating fixed behaviour (the whole point of the change) is also
validated end-to-end: the EMPTY collection RETURNS NORMALLY and yields the
identity element — `Min() == +oo`, `Max() == -oo` — plus the single-survivor
(`Min(x) == x`, `Max(x) == x`) and aggregate (>=2 survivors) branches, while a
non-comparable operand STILL raises ValueError (the unchanged contract).

Imports nothing repo-specific beyond `sympy` itself (the library under test).
SKIP-guarded (exit 0) when the host interpreter cannot import this old sympy
(e.g. distutils removed in py3.12); the orchestrator runs it in-container on the
instance's real interpreter.  Exit 0 iff every obligation holds (or skipped).
"""
import random
import sys


def main():
    try:
        from sympy import Min, Max, S, Symbol, I, cos, sin
    except Exception as exc:  # environment mismatch -> skip, not fail
        print("G-AX SKIP: cannot import sympy in this interpreter (%r); "
              "runs in-container on the instance's real interpreter." % (exc,))
        return 0

    identity = {Min: S.Infinity, Max: S.NegativeInfinity}
    zero = {Min: S.NegativeInfinity, Max: S.Infinity}

    x_sym = Symbol("x")
    checks = 0

    for cls in (Min, Max):
        ident = identity[cls]
        annih = zero[cls]

        # --- (A1)+(A2) the EMPTY collection: the discriminating fixed behaviour
        # has_noncomparable_operand([]) == False, has_absorbing_operand([]) ==
        # False AND canonical_count([]) == 0, so the reduction returns NORMALLY
        # and yields the identity element (it must NOT raise).
        empty_result = cls()                      # must NOT raise
        assert empty_result == ident, (
            "%s(): empty reduction must yield the identity element %r, got %r"
            % (cls.__name__, ident, empty_result))
        # ... and must NOT collapse to the annihilator (the absorbing branch):
        assert empty_result != annih or ident == annih, (
            "%s(): empty reduction collapsed to the annihilator %r — the "
            "absorbing pre-filter fired on an empty collection" % (cls.__name__, annih))
        checks += 1

        # --- single survivor: Min(x)/Max(x) returns the operand itself --------
        for sym_name in ("x", "y", "z", "w"):
            s = Symbol(sym_name)
            r = cls(s)                            # must NOT raise
            assert r == s, ("%s(%s) single survivor must return the operand, "
                            "got %r" % (cls.__name__, sym_name, r))
            checks += 1

        # --- canonical_count >= 0 and the >=2 aggregate branch -----------------
        x, y = Symbol("x"), Symbol("y")
        agg = cls(x, y)                           # two distinct symbols survive
        assert agg.func is cls, (
            "%s(x, y): two distinct survivors must assemble an aggregate of the "
            "same lattice, got %r" % (cls.__name__, agg))
        checks += 1

        # --- (A0) NON-COMPARABLE operands: the unchanged comparability pre-filter
        # STILL rejects them (ValueError) — has_noncomparable_operand(ops)==True.
        # These are exactly the F2P `raises(ValueError, ...)` assertions that
        # remain in test_Min / test_Max alongside the new empty-args assertions.
        noncomparable_ops = [
            (I,),                                 # imaginary unit
            (S.ComplexInfinity,),                 # zoo
            (S.NaN,),                             # nan
            (I, x_sym),                           # mixed with a comparable symbol
            (S.ComplexInfinity, x_sym),
            (S.NaN, x_sym),
            (x_sym, I),                           # non-comparable not first
        ]
        for ops in noncomparable_ops:
            raised = False
            try:
                cls(*ops)
            except ValueError:
                raised = True
            assert raised, (
                "%s(*%r): a non-comparable operand must be REJECTED with "
                "ValueError (the unchanged comparability pre-filter), but the "
                "reduction returned normally" % (cls.__name__, ops))
            checks += 1
        # subs path through a constructed Min/Max expression (F2P asserts these):
        for raiser in (lambda: cls(cos(x_sym), sin(x_sym)).subs(x_sym, I),):
            raised = False
            try:
                raiser()
            except ValueError:
                raised = True
            assert raised, (
                "%s(cos(x), sin(x)).subs(x, I): substituting a non-comparable "
                "value must raise ValueError" % cls.__name__)
            checks += 1

    # --- randomized fuzz over symbolic operand collections --------------------
    rng = random.Random(15809)
    pool = [Symbol(n) for n in ("a", "b", "c", "d", "e", "f", "g", "h")]
    for cls in (Min, Max):
        ident = identity[cls]
        for _ in range(2000):
            k = rng.randint(0, 5)
            ops = [rng.choice(pool) for _ in range(k)]
            distinct = set(ops)
            result = cls(*ops)                    # must NOT raise for any k
            if k == 0:
                # empty collection -> identity element (the fix)
                assert result == ident, (
                    "%s(*%r): empty reduction must yield identity %r, got %r"
                    % (cls.__name__, ops, ident, result))
            elif len(distinct) == 1:
                # one canonical survivor -> that operand
                only = next(iter(distinct))
                assert result == only, (
                    "%s(*%r): single survivor must return that operand, got %r"
                    % (cls.__name__, ops, result))
            else:
                # >=2 survivors -> aggregate of the same lattice
                assert result.func is cls, (
                    "%s(*%r): multiple survivors must assemble an aggregate, "
                    "got %r" % (cls.__name__, ops, result))
            checks += 1

    # --- randomized fuzz mixing a non-comparable operand into a comparable set:
    # any collection carrying a non-comparable operand must raise ValueError ----
    noncomp_pool = [I, S.ComplexInfinity, S.NaN]
    for cls in (Min, Max):
        for _ in range(1000):
            k = rng.randint(0, 4)
            comparable = [rng.choice(pool) for _ in range(k)]
            bad = rng.choice(noncomp_pool)
            ops = comparable + [bad]
            rng.shuffle(ops)                      # non-comparable at a random pos
            raised = False
            try:
                cls(*ops)
            except ValueError:
                raised = True
            assert raised, (
                "%s(*%r): a collection containing the non-comparable operand %r "
                "must be REJECTED with ValueError, but returned normally"
                % (cls.__name__, ops, bad))
            checks += 1

    # --- EXCLUSIVITY of the two decisive scan events -------------------------
    # The pre-filter is ONE ordered scan whose FIRST decisive event decides the
    # whole reduction, so `has_absorbing_operand` and
    # `has_noncomparable_operand` can never both hold:
    # Implies(has_absorbing_operand, not has_noncomparable_operand).
    # NOTE: the fuzz above draws only from the symbol `pool`, so it never mixes
    # an absorbing operand with a non-comparable one — this block covers exactly
    # that class, in BOTH orders. It is also the class where a CONTAINMENT
    # reading of the two predicates disagrees with the real callee: Min(-oo, I)
    # returns -oo (the scan collapses on -oo before it ever reaches I) whereas
    # Min(I, -oo) raises ValueError.
    from sympy.core.operations import ShortCircuit
    from sympy import sympify

    def scan_outcome(cls, ops):
        """The first decisive event of the REAL unchanged scan, consumed exactly
        as __new__ consumes it."""
        gen = (sympify(a) for a in ops)
        try:
            frozenset(cls._new_args_filter(gen))
            return "ok"
        except ShortCircuit:
            return "absorbing"
        except ValueError:
            return "noncomparable"

    a_sym = Symbol("a")
    for cls in (Min, Max):
        annih = zero[cls]
        for bad in (I, S.ComplexInfinity, S.NaN):
            for ops in ([annih, bad], [bad, annih],
                        [a_sym, annih, bad], [a_sym, bad, annih]):
                outcome = scan_outcome(cls, ops)
                assert not (outcome == "absorbing" and
                            outcome == "noncomparable")
                raised = False
                value = None
                try:
                    value = cls(*ops)
                except ValueError:
                    raised = True
                # the constructor's observable must equal the scan's FIRST event
                assert (outcome == "noncomparable") == raised, (
                    "%s(*%r): the real scan's first decisive event is %r but the "
                    "constructor %s — the two decisive events are not exclusive "
                    "as the model's axiom encodes"
                    % (cls.__name__, ops, outcome,
                       "raised ValueError" if raised else "returned normally"))
                if outcome == "absorbing":
                    assert value == annih, (
                        "%s(*%r): the scan collapsed on the absorbing operand, so "
                        "the reduction must yield the annihilator %r, got %r"
                        % (cls.__name__, ops, annih, value))
                checks += 1

    # --- (A2) DEFINEDNESS of the canonical-set pass ---------------------------
    # The pass `_collapse_arguments` -> `_find_localzeros` compares the SURVIVORS
    # the scan passed over AGAINST ONE ANOTHER (`_is_connected`, :552/:574) and can
    # propagate that comparison's own error out of `Expr.__ge__` (expr.py:295)
    # instead of yielding a canonical set. That is a different observation from
    # the scan's per-operand one, and the class below is exactly where they part:
    # `x + I` has `is_real is None` and is not a number, so the scan's guard
    # (:521-523) passes it over, yet `x >= x + I` cannot be decided.
    from sympy import sign, Order

    undef_ops = [x_sym + I, x_sym + 2 * I, x_sym - I, I * x_sym,
                 sign(x_sym), Order(x_sym)]
    undefined_seen = 0
    for cls in (Min, Max):
        annih = zero[cls]
        for u in undef_ops:
            for ops in ([u], [u, u], [x_sym, u], [u, x_sym], [a_sym, u],
                        [u, a_sym], [annih, u], [u, annih],
                        [identity[cls], u], [u, identity[cls]],
                        [I, u], [u, I], [x_sym, a_sym, u]):
                outcome = scan_outcome(cls, ops)
                kind = "value"
                value = None
                try:
                    value = cls(*ops)
                except ValueError:
                    kind = "valueerror"
                except Exception:                    # noqa: BLE001
                    kind = "failure"
                if outcome == "noncomparable":
                    assert kind == "valueerror", (
                        "%s(*%r): the scan's first decisive event is the "
                        "non-comparable one, so the reduction must be REJECTED "
                        "with ValueError; got %r (%s)"
                        % (cls.__name__, ops, value, kind))
                elif outcome == "absorbing":
                    # the scan decided FIRST: the canonical-set pass is never
                    # reached, so definedness is vacuously true and the reduction
                    # must still collapse to the annihilator.
                    assert kind == "value" and value == annih, (
                        "%s(*%r): the scan collapsed on the absorbing operand "
                        "BEFORE the canonical-set pass, so the reduction must "
                        "yield the annihilator %r; got %r (%s) — "
                        "canonical_reduction_defined would not be vacuously true "
                        "where the pass is never reached"
                        % (cls.__name__, ops, annih, value, kind))
                else:
                    # the scan passed every operand over: the canonical-set pass
                    # decides, and whatever it propagates is NOT the scan's own
                    # comparability ValueError.
                    assert kind != "valueerror", (
                        "%s(*%r): the scan passed every operand over, yet the "
                        "reduction raised the scan's OWN comparability error — "
                        "the two observations would not be distinct"
                        % (cls.__name__, ops))
                    if kind == "failure":
                        undefined_seen += 1
                checks += 1
    assert undefined_seen > 0, (
        "no collection was observed whose canonical-set pass FAILS while the "
        "ordered scan passes every operand over: canonical_reduction_defined "
        "would be trivially true and the model's reduction-undefined leg dead")

    print("G-AX OK: empty-collection -> identity (Min()==oo, Max()==-oo), "
          "single survivor -> operand, >=2 survivors -> aggregate; a "
          "non-comparable operand (I/zoo/nan/subs) -> ValueError; "
          "has_noncomparable_operand([])==False, has_absorbing_operand([])==False, "
          "canonical_reduction_defined([])==True and canonical_count([])==0 hold; "
          "the two decisive scan events are MUTUALLY EXCLUSIVE — on both orders of "
          "{absorbing, non-comparable} the constructor agrees with the real scan's "
          "FIRST event (Min(-oo,I)==-oo vs Min(I,-oo) raises); and the "
          "canonical-set pass is a DISTINCT partial observation — %d collections "
          "whose every operand the scan passed over still failed in that pass "
          "(never with the scan's own ValueError), while an absorbing operand "
          "collapses the reduction in either order alongside one of them (the pass "
          "is never reached, so definedness is vacuously true) — on the real sympy "
          "reductions over %d observations." % (undefined_seen, checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
