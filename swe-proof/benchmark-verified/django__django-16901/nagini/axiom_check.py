#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16901.

This bundle axiomatizes NO callee: the operation the gold patch changes is
purely integer/boolean arithmetic (a per-operand 1/0 choice, a sum, a modulo,
an equality and a disjunction), modelled DEEPLY in model.py with native Nagini
arithmetic. There is therefore no `@ContractOnly` axiom to validate against a
real library callee.

What this script validates is the single soundness link that lives outside
Nagini: that the model's predicate `xor_holds` over a 0/1 operand assignment
equals the truth value the gold-patch-constructed SQL predicate evaluates to,

    (a OR b OR ...) AND ( MOD(sum, 2) == 1   if  #operands > 2
                          sum == 1           otherwise )

and that this in turn equals "an ODD number of operands are true" (the issue's
behavioural demand and the F2P oracle). It exhaustively enumerates every
assignment of up to 12 operands, then fuzzes larger ones, checking three
things agree on every assignment:

  (1) the model's `xor_holds` (re-implemented here exactly as in model.py),
  (2) the SQL the gold patch builds, evaluated arithmetically, and
  (3) parity: an odd number of operands are true.

It also confirms the `len <= 2` coincidence the spec relies on
(`count == 1` <=> `count % 2 == 1`) and that, for `len > 2`, the OLD fallback
(`sum == 1`, no Mod) DISAGREES with parity on at least the issue's witnesses
(3 and 5 true operands), i.e. the change is observable.

Imports only the standard library. Exit 0 iff every obligation holds.
"""
import itertools
import random
import sys


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def count_true(s):
    """model.py count_true: number of true operands (entry == 1 -> 1, else 0)."""
    return sum(1 if c == 1 else 0 for c in s)


def any_true(s):
    """model.py any_true: at least one operand true."""
    return any(c == 1 for c in s)


def derived_count(s):
    """model.py derived_count: parity for >2 operands, raw count otherwise."""
    if len(s) > 2:
        return count_true(s) % 2
    return count_true(s)


def xor_holds(s):
    """model.py xor_holds: (OR of operands) AND (derived count == 1)."""
    return any_true(s) and derived_count(s) == 1


# --- the gold-patch-constructed SQL predicate, evaluated arithmetically ------

def sql_predicate(s):
    """Truth value of the predicate the GOLD patch constructs, evaluated for
    this operand assignment:
        lhs = OR of children
        rhs_sum = sum( Case(When(c, then=1), default=0) for c in children )
        if len(children) > 2: rhs_sum = Mod(rhs_sum, 2)
        rhs = Exact(1, rhs_sum)            # i.e. rhs_sum == 1
        result = lhs AND rhs
    """
    lhs = any(c == 1 for c in s)                       # OR of children
    rhs_sum = sum(1 if c == 1 else 0 for c in s)       # Case/When + reduce(add)
    if len(s) > 2:
        rhs_sum = rhs_sum % 2                           # Mod(rhs_sum, 2)
    rhs = (rhs_sum == 1)                                # Exact(1, rhs_sum)
    return lhs and rhs                                  # AND


def old_sql_predicate(s):
    """The PRE-patch fallback (no Mod): (OR ...) AND (sum == 1) — 'exactly
    one'. Used only to confirm the change is observable for >2 operands."""
    lhs = any(c == 1 for c in s)
    rhs_sum = sum(1 if c == 1 else 0 for c in s)
    return lhs and (rhs_sum == 1)


def parity_odd(s):
    """The issue's behavioural demand: an ODD number of operands are true."""
    return (sum(1 if c == 1 else 0 for c in s) % 2) == 1


# --- the checks --------------------------------------------------------------

def check_assignment(s):
    model = xor_holds(s)
    sql = sql_predicate(s)
    odd = parity_odd(s)
    assert model == sql, (
        "model xor_holds disagrees with gold SQL predicate on %r: "
        "model=%r sql=%r" % (s, model, sql))
    assert model == odd, (
        "model xor_holds disagrees with odd-count semantics on %r: "
        "model=%r odd=%r" % (s, model, odd))


def main():
    # (1) exhaustive over every 0/1 assignment of 0..12 operands
    total = 0
    for n in range(0, 13):
        for combo in itertools.product((0, 1), repeat=n):
            check_assignment(list(combo))
            total += 1

    # (2) randomized fuzz on larger operand counts (incl. non-0/1 entries,
    #     which model.py treats as "false" — contribute 0 — exactly like the
    #     SQL Case default)
    rng = random.Random(16901)
    for _ in range(200000):
        n = rng.randint(0, 40)
        s = [rng.choice((0, 1, 0, 1, 2, -1, 7)) for _ in range(n)]
        check_assignment(s)
        total += 1

    # (3) the len <= 2 coincidence the spec relies on: count == 1 <=> count%2==1
    for n in range(0, 3):
        for combo in itertools.product((0, 1), repeat=n):
            c = count_true(list(combo))
            assert (c == 1) == (c % 2 == 1), (
                "len<=2 coincidence broken on %r (count=%d)" % (combo, c))

    # (4) the change is observable for >2 operands: the OLD fallback disagrees
    #     with parity on the issue's witnesses (3 and 5 true operands).
    for n_true in (3, 5):
        s = [1] * n_true
        assert old_sql_predicate(s) != parity_odd(s), (
            "expected old fallback to disagree with parity on %d true operands"
            % n_true)
        assert sql_predicate(s) == parity_odd(s), (
            "gold predicate must agree with parity on %d true operands" % n_true)

    print("G-AX OK: model xor_holds == gold SQL predicate == odd-count over "
          "%d assignments (exhaustive 0..12 operands + 200000 fuzz); len<=2 "
          "coincidence holds; change observable for 3 and 5 true operands." % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
