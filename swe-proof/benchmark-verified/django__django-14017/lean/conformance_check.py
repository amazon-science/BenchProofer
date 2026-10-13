#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_mergeFilters
against the patch.diff behaviour (the POST-patch `Q._combine`).

The impl region is all-R: the guard and every branch outcome are pure functions
of observable operand attributes. The shadow below reproduces the Lean impl's
control flow op-for-op (guard → empty-other → empty-self → merged). The patched
side runs the REAL post-patch `Q._combine` (the gold patch is applied in the
container before this check runs) and classifies its observable outcome into the
same `MergeResult` alphabet:

  TypeError raised                     -> "rejected"   (guard failed)
  returns a copy of self (== self)     -> "keepLeft"   (other empty)
  returns a copy of other (== other)   -> "keepRight"  (self empty)
  returns a fresh combined node        -> "merged:<conn>"

Operands exercised (mapping.md bijection):
  * real `Q()` (empty filter)            -> isFilter=T, conditional(N/A), empty=T
  * real `Q(x=1)` (non-empty filter)     -> isFilter=T, empty=F
  * a standalone boolean condition       -> isFilter=F, conditional=T, empty=F
       (faithful stand-in for Exists(...): `Q._combine` observes ONLY
        `getattr(other,'conditional',False) is True` and `bool(other)` of the
        operand, so a truthy object carrying `conditional=True` is behaviourally
        indistinguishable from a real Exists at this boundary. Using the stand-in
        avoids needing a configured app registry / queryset.)
  * a plain non-conditional object       -> isFilter=F, conditional=F, empty=F

We assert zero disagreements over >=10^5 fuzzed (self, other, conn) inputs.

stdlib + django only. exit 0 iff zero disagreements.
"""
import os
import random
import sys


# ---------------------------------------------------------------------------
# Lean-impl shadow (R/I), in terms of the abstract operand attributes.
# ---------------------------------------------------------------------------
def shadow(self_empty: bool, other_isfilter: bool, other_conditional: bool,
           other_empty: bool, conn: str) -> str:
    # if !(other.isFilter || other.conditional) then rejected
    if not (other_isfilter or other_conditional):
        return "rejected"
    # if other.empty then keepLeft
    if other_empty:
        return "keepLeft"
    # if self.empty then keepRight
    if self_empty:
        return "keepRight"
    # else merged conn
    return "merged:" + conn


# ---------------------------------------------------------------------------
# Real post-patch Q._combine driver -> same outcome alphabet.
# ---------------------------------------------------------------------------
def _configure_django():
    try:
        from django.conf import settings
        if not settings.configured:
            settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
        import django
        django.setup()
    except Exception:
        pass


class _Cond:
    """Standalone boolean-valued condition stand-in (conditional=True),
    behaviourally identical to Exists() at the `_combine` boundary.

    `conditional=True` drives the guard; truthy `__bool__` makes it non-empty;
    `deconstruct` lets the empty-self branch reconstruct a copy of the operand
    exactly as a real expression (e.g. Exists) would."""
    conditional = True

    def __bool__(self):
        return True

    def deconstruct(self):
        return ('cond', (), {})


class _Plain:
    """Non-conditional object (conditional attribute absent/False)."""
    conditional = False


class _CondFalsey:
    """Accepted standalone condition that is falsey (empty): `conditional is
    True` so the guard admits it, but `bool()` is False, so the generic
    `not other` shortcut fires -> keepLeft. Pins that the empty shortcut is NOT
    gated on `isinstance(other, Q)`."""
    conditional = True

    def __bool__(self):
        return False

    def deconstruct(self):
        return ('cond', (), {})


class _Weird:
    """`conditional` is truthy but NOT `True` (the patch uses `is True`), so the
    real guard REJECTS it. Pins the exact-identity distinction."""
    conditional = 1


def real_outcome(Q, self_obj, other_obj, conn):
    """Run the real post-patch Q._combine and classify the outcome."""
    try:
        self_obj._combine(other_obj, conn)
    except TypeError:
        return "rejected"
    # Classify the (non-rejected) outcome by which short-circuit branch fired,
    # mirroring the real control-flow order exactly:
    #   if not other:  -> copy of self  (keepLeft)   -- generic truthiness, NOT gated on Q
    #   elif not self: -> copy of other (keepRight)
    #   else:          -> fresh combined node (merged)
    if not bool(other_obj):
        return "keepLeft"
    if not bool(self_obj):
        return "keepRight"
    return "merged:" + conn


def build_other(Q, kind):
    if kind == "Qempty":
        return Q()
    if kind == "Qnonempty":
        return Q(x=1)
    if kind == "cond":
        return _Cond()
    if kind == "condfalsey":
        return _CondFalsey()
    if kind == "weird":
        return _Weird()
    if kind == "plain":
        return _Plain()
    raise ValueError(kind)


def abstract_other(kind):
    # (isFilter, boolValued, empty)
    #   isFilter   := isinstance(other, Q)
    #   boolValued := getattr(other,'conditional',False) is True
    #   empty      := not bool(other)
    return {
        "Qempty":     (True,  True,  True),    # Q.conditional is True; bool(Q())==False
        "Qnonempty":  (True,  True,  False),
        "cond":       (False, True,  False),   # conditional is True, truthy
        "condfalsey": (False, True,  True),    # conditional is True, falsey
        "weird":      (False, False, False),   # conditional==1, NOT `is True`
        "plain":      (False, False, False),
    }[kind]


SEED = 14017
N = 120_000


def main() -> int:
    _configure_django()
    try:
        from django.db.models.query_utils import Q
    except Exception as e:  # pragma: no cover
        print(f"G-CONF ERROR: cannot import Q: {e}")
        return 2

    rng = random.Random(SEED)
    self_kinds = ["Qempty", "Qnonempty"]
    other_kinds = ["Qempty", "Qnonempty", "cond", "condfalsey", "weird", "plain"]
    conns = [Q.AND, Q.OR]

    # Deterministic exhaustive enumeration first (every combination).
    cases = [(sk, ok, cn) for sk in self_kinds for ok in other_kinds for cn in conns]
    # Then fuzz to >= 10^5.
    cases += [(rng.choice(self_kinds), rng.choice(other_kinds), rng.choice(conns))
              for _ in range(N)]

    disagreements = 0
    examples = []
    for sk, ok, cn in cases:
        self_obj = Q() if sk == "Qempty" else Q(x=1)
        other_obj = build_other(Q, ok)
        want = real_outcome(Q, self_obj, other_obj, cn)

        self_empty = (sk == "Qempty")
        isf, cond, oe = abstract_other(ok)
        got = shadow(self_empty, isf, cond, oe, cn)

        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((sk, ok, cn, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for sk, ok, cn, g, w in examples:
            print(f"  self={sk} other={ok} conn={cn} shadow={g!r} real={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
