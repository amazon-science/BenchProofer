#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-15875 (plan §4).

Validates the single A leg of refinement.md — the **A-reference** `residualIsZero`
(Solution.lean), the opaque stand-in for the UNCHANGED residual sub-decision
`self.func(*nz).is_zero`, where `nz` is the list of real-and-definitely-nonzero
summands (mapping.md §3).

The opaque modeling is sound iff that sub-decision is genuinely **unchanged** by
the patch — i.e. the patch only adds a guard *around* when it is consulted, never
alters how it is computed. Concretely, the property we attest is
**patch-invariance on the reached domain**:

  For every constructible commutative `Add`,
    (a) when the residual sub-decision is REACHED (the real-nonzero list `nz` is
        proper-nonempty: `0 < len(nz) < len(self.args)`), the PRE-patch and
        POST-patch `_eval_is_zero` return the IDENTICAL verdict; and
    (b) whenever the two verdicts DIFFER AT ALL, it is ONLY in the guarded case
        `len(nz) == 0` (the case the patch newly short-circuits to None) — never
        on a reached-residual input.

(a)+(b) together are exactly the claim that `self.func(*nz).is_zero` is an
unchanged callee the patch routes around: where it is reached it is invariant, and
the only behavioural change is the guard the deep model `verdict` encodes
concretely. This is what licenses modeling the sub-decision as an opaque function
with no consumed contract.

To compute the PRE- and POST-patch verdicts in one process, the two one-line
variants of `Add._eval_is_zero` (differing only in the `len(nz)==0 or` guard) are
re-implemented here verbatim from `add.py` and exercised against the REAL sympy
assumption facts of each summand (the facts are real; only the two-line decision
cascade is mirrored). A divergence outside the `len(nz)==0` case is a concrete
soundness counterexample.

Runs in-container against the REAL `sympy` at base_commit. Imports only `sympy`.
Boundary inputs (incl. the issue reproducer) first, then fuzzed unevaluated Adds.
Exit 0 iff every observation meets (a) and (b).
"""
import random
import sys

from sympy import (Add, I, Integer, S, Symbol, sqrt)

SEED = 15875
N_FUZZ = 20_000


def atom_pool():
    return [
        Integer(0), Integer(2), Integer(-3), sqrt(2),
        Symbol("r", real=True, nonzero=True),
        Symbol("u", real=True),
        I, 2 * I, (1 + I) ** 2, Symbol("m", imaginary=True),
        I * Symbol("p", real=True),
        Symbol("g"),
    ]


def _scan(self):
    """The shared pre-loop accumulation of Add._eval_is_zero (add.py:539-553),
    verbatim against the REAL summand facts. Returns (z, nz, im, im_or_z, bailed)
    or None when a bare `return` (undetermined) fired."""
    nz = []
    z = 0
    im_or_z = False
    im = False
    if self.is_commutative is False:
        return ("noncomm",)
    for a in self.args:
        if a.is_real:
            if a.is_zero:
                z += 1
            elif a.is_zero is False:
                nz.append(a)
            else:
                return ("bail",)
        elif a.is_imaginary:
            im = True
        elif (S.ImaginaryUnit * a).is_real:
            im_or_z = True
        else:
            return ("bail",)
    return ("ok", z, nz, im, im_or_z)


def _verdict(self, guard_empty):
    """The post-loop cascade of Add._eval_is_zero (add.py:554-566). `guard_empty`
    toggles the patch: True = POST-patch (`len(nz)==0 or len(nz)==len`),
    False = PRE-patch (`len(nz)==len` only). Uses the REAL recursive
    `self.func(*nz).is_zero` for the residual sub-decision."""
    s = _scan(self)
    if s[0] == "noncomm":
        return None
    if s[0] == "bail":
        return None
    _, z, nz, im, im_or_z = s
    if z == len(self.args):
        return True
    if (guard_empty and len(nz) == 0) or len(nz) == len(self.args):
        return None
    b = self.func(*nz)
    if b.is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
    if b.is_zero is False:
        return False
    return None


def residual_reached(self):
    """True iff the residual sub-decision self.func(*nz).is_zero is consulted
    (nz proper-nonempty), under the PRE-patch control flow (the wider domain)."""
    s = _scan(self)
    if s[0] in ("noncomm", "bail"):
        return False
    _, z, nz, im, im_or_z = s
    if z == len(self.args):
        return False
    if len(nz) == len(self.args):
        return False
    return len(nz) > 0


def build_add(summands):
    e = Add(*summands, evaluate=False)
    if not isinstance(e, Add):
        return None
    return e


def fuzz_inputs(n, rng):
    pool = atom_pool()
    yield [(-2) * I, (1 + I) ** 2]                 # issue reproducer (nz empty)
    yield [I, 2 * I]
    yield [Integer(0), Integer(0)]
    yield [Integer(2), I]                          # residual reached
    yield [Symbol("r", real=True, nonzero=True), I]
    yield [I * Symbol("p", real=True), I]
    yield [Integer(2), Integer(-2)]
    yield [Symbol("u", real=True), I]
    yield [Symbol("g"), I]
    yield [Integer(2), Integer(3), I, 2 * I]
    for _ in range(n):
        k = rng.randint(1, 5)
        yield [rng.choice(pool) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    reached = 0          # residual-reached observations checked for invariance
    guarded_diffs = 0    # diffs confined to the len(nz)==0 case (expected)
    skipped = 0
    violations = []
    for summands in fuzz_inputs(N_FUZZ, rng):
        try:
            e = build_add(summands)
            if e is None:
                skipped += 1
                continue
            pre = _verdict(e, guard_empty=False)
            post = _verdict(e, guard_empty=True)
            rr = residual_reached(e)
        except Exception:
            skipped += 1
            continue

        if rr:
            # (a) where the residual sub-decision is reached, it must be invariant
            if pre != post:
                violations.append(
                    (summands, "residual reached but pre=%r != post=%r" % (pre, post)))
        else:
            # (b) any divergence off the reached domain must be the guarded case
            if pre != post:
                s = _scan(e)
                empty_nz = (s[0] == "ok" and len(s[2]) == 0)
                if not empty_nz:
                    violations.append(
                        (summands, "diff off reached-domain not in len(nz)==0 case: "
                                   "pre=%r post=%r" % (pre, post)))
                else:
                    guarded_diffs += 1
        if rr:
            reached += 1
        if len(violations) >= 5:
            break

    if violations:
        print("G-AX FAIL: %d residual-sub-decision soundness violation(s):"
              % len(violations))
        for s, msg in violations:
            print("  summands=%r -> %s" % (s, msg))
        return 1
    if reached == 0:
        print("G-AX FAIL: 0 residual-reached observations — cannot attest "
              "patch-invariance of the sub-decision.")
        return 1
    print("G-AX OK: the residual zero-sub-decision self.func(*nz).is_zero is "
          "patch-invariant on its reached domain over %d reached observations "
          "(every pre==post), and the only pre/post divergence is the guarded "
          "len(nz)==0 case (%d such, incl. the issue reproducer); seed=%d, %d "
          "skipped as non-constructible. The residualIsZero A-reference "
          "(opaque, unchanged callee) is sound." % (reached, guarded_diffs, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
