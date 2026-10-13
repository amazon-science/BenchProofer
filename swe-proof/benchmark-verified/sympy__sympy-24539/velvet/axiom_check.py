#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-24539.

IMPORTANT — this check runs in the UNPATCHED base_commit container (G-AX does
not apply the gold patch; that is G-CONF's job). It therefore validates ONLY the
facts about the UNCHANGED callee that the bundle's `opaque exprFromDict` model
relies on — facts that hold REGARDLESS of the patch. It must NOT assert the
behaviour the patch CHANGES (a correctly-sized caller list being honored): that
is the operation under change (directive 7 forbids axiomatising it), and it is
validated against the patched oracle by G-CONF / G-DIFF / G-GOLD instead.

The single A-reference in this bundle is `exprFromDict` (Solution.lean), which
models the UNCHANGED renderer `sympy.polys.polyutils.expr_from_dict`. It is
modeled `opaque` with NO asserted `ensures`. For the refinement's A7 I-leg
(`return Except.ok (exprFromDict d chosen)` ↔ `return expr_from_dict(
self.as_expr_dict(), *chosen)`) to be sound, the modeled callee must be a
deterministic pure function of `(datum, gens)` that genuinely USES `gens` — so
the method's choice of name list is observable, not masked by a constant. Those
properties, plus the UNCHANGED default-name branch and the wrong-length
rejection, all hold at base_commit. This file checks exactly them:

  (determinism)  expr_from_dict(datum, *gens) == expr_from_dict(datum, *gens)
      — same (datum, gens) ⇒ equal Expr (the bijection mapping.md §2 relies on).
  (uses-gens / observable)  for distinct correctly-sized name lists, the renderer
      yields DISTINCT expressions (the polynomial mentions every generator) — so
      `exprFromDict d chosen` genuinely depends on `chosen`, i.e. the method's
      choice of list is observable.
  (default branch — UNCHANGED by the patch)  f.as_expr() == expr_from_dict(
      f.as_expr_dict(), *f.ring.symbols) — with no caller names the datum's own
      names are used; this branch is identical pre- and post-patch.
  (rejection)  f.as_expr(*wrong) raises ValueError for every non-empty
      wrong-length `wrong` — true at base_commit too (the message differs from
      the patched one, but the F2P test only asserts `raises(ValueError)`).

Imports only `sympy` — the same package the gold patch lives in. Exit 0 iff every
obligation holds.
"""
import random
import sys

from sympy import ring, ZZ, symbols
from sympy.polys.polyutils import expr_from_dict


# Candidate generator-name pool to draw caller-supplied lists from. Distinct
# from each ring's own names where it matters (so the observability case —
# supplied != ring.symbols but same length — is exercised).
_POOL = list(symbols("a b c d e f g h"))


def build_rings():
    """A spread of rings (varying ngens) each with a non-trivial polynomial that
    actually mentions every generator, so a name choice is observable."""
    cases = []

    R1, x = ring("x", ZZ)
    cases.append((R1, 5*x**3 - 2*x + 1))

    R2, x, y = ring("x,y", ZZ)
    cases.append((R2, 3*x**2*y - x*y + 7*y**3 + 1))

    R3, x, y, z = ring("x,y,z", ZZ)
    cases.append((R3, 3*x**2*y - x*y*z + 7*z**3 + 1))   # the issue's polynomial

    R4, x, y, z, t = ring("x,y,z,t", ZZ)
    cases.append((R4, x*y - z*t + 2*x**2*t - 5))

    return cases


def check_determinism(f):
    """expr_from_dict is a pure deterministic function of (datum, gens)."""
    ng = f.ring.ngens
    datum = f.as_expr_dict()
    own = tuple(f.ring.symbols)
    assert expr_from_dict(datum, *own) == expr_from_dict(datum, *own), (
        "expr_from_dict is non-deterministic on %r" % (f,))
    for _ in range(8):
        gens = tuple(random.sample(_POOL, ng))
        assert expr_from_dict(datum, *gens) == expr_from_dict(datum, *gens), (
            "expr_from_dict is non-deterministic for gens=%r on %r" % (gens, f))


def check_uses_gens(f):
    """The renderer USES its gens argument: distinct correctly-sized name lists
    give distinct expressions (the polynomial mentions every generator), so the
    modeled `exprFromDict d chosen` genuinely depends on `chosen` — the method's
    choice of list cannot be masked by a constant renderer."""
    ng = f.ring.ngens
    datum = f.as_expr_dict()
    own = tuple(f.ring.symbols)
    # a correctly-sized list of names disjoint from the ring's own
    disjoint = tuple(s for s in _POOL if s not in set(own))[:ng]
    assert len(disjoint) == ng
    e_own = expr_from_dict(datum, *own)
    e_alt = expr_from_dict(datum, *disjoint)
    assert e_own != e_alt, (
        "renderer ignores its gens argument for %r — choice not observable" % (f,))


def check_default_branch(f):
    """UNCHANGED default branch: no caller names ⇒ the datum's own names are
    used. Identical pre- and post-patch, so it holds at base_commit."""
    assert f.as_expr() == expr_from_dict(f.as_expr_dict(), *f.ring.symbols), (
        "default-name rendering diverges from expr_from_dict on %r" % (f,))


def check_rejection(f):
    """A non-empty wrong-length caller list raises ValueError (true at
    base_commit too; the patch only changes the message text)."""
    ng = f.ring.ngens
    wrong_lengths = [k for k in range(1, ng + 5) if k != ng]
    for k in wrong_lengths:
        if k <= len(_POOL):
            supplied = tuple(_POOL[:k])
        else:
            supplied = tuple(_POOL[i % len(_POOL)] for i in range(k))
        try:
            f.as_expr(*supplied)
        except ValueError:
            continue
        raise AssertionError(
            "as_expr accepted a wrong-length caller list (len=%d, ngens=%d) for %r"
            % (k, ng, f))


def main():
    random.seed(24539)
    cases = build_rings()
    n = 0
    for _, f in cases:
        check_determinism(f)
        check_uses_gens(f)
        check_default_branch(f)
        check_rejection(f)
        n += 1

    # randomized fuzz over the UNCHANGED-callee facts and the rejection branch.
    for _ in range(20000):
        _, f = random.choice(cases)
        ng = f.ring.ngens
        datum = f.as_expr_dict()
        k = random.randint(0, len(_POOL))
        supplied = tuple(random.sample(_POOL, k)) if k <= len(_POOL) else ()
        if k == 0:
            # default branch (unchanged): own names are used
            assert f.as_expr() == expr_from_dict(datum, *f.ring.symbols)
        elif k == ng:
            # uses-gens / determinism: the renderer is a pure fn of (datum, gens).
            # NB: we do NOT assert as_expr honors `supplied` here — that is the
            # patched behaviour (validated by G-CONF), false at base_commit.
            assert expr_from_dict(datum, *supplied) == expr_from_dict(datum, *supplied)
        else:
            # wrong length: rejected
            try:
                f.as_expr(*supplied)
                raise AssertionError(
                    "fuzz: wrong-length list accepted (k=%d ngens=%d)" % (k, ng))
            except ValueError:
                pass

    print("G-AX OK: the UNCHANGED renderer expr_from_dict is a deterministic pure "
          "function of (datum, gens) that uses its gens argument (choice "
          "observable); as_expr's unchanged default branch consults it with the "
          "datum's own names; wrong-length caller lists raise ValueError. "
          "Validated on %d rings (ngens 1..4) + 20000 fuzz draws at base_commit. "
          "(The patch's honor-a-correctly-sized-list discriminator is validated "
          "against the patched oracle by G-CONF, not here.)" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
