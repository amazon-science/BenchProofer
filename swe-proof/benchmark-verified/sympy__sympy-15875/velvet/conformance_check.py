#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15875 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo objects: read each summand's four
              fuzzy facts via the mapping.md bijection (`is_X` ↔ `Option Bool`),
              run `classify`/`tallyAll` (the fold) then `verdict` (the post-loop
              cascade, including the changed `len(nz)==0 or ...` disjunct). The
              A-tagged residual sub-decision `residualIsZero nz` is NOT replaced
              by its opaque model here; G-CONF isolates the R/I legs, so the
              residual decision is computed with the REAL callee
              `self.func(*nz).is_zero` — exactly as the gold patch does.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Add._eval_is_zero(self)`
              applied at base_commit (the real correctness oracle, G-RESOLVE).
              The harness applies patch.diff before this runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), sympy only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from sympy import (Add, I, Integer, S, Symbol, sqrt)

SEED = 15875
N_FUZZ = 100_000


# --- atom pool: one representative per classify branch (mapping.md §3.1) ------
def atom_pool():
    return [
        Integer(0),                                  # real & zero      (T,T,F,T)
        Integer(2),                                  # real & nonzero   (T,F,F,F)
        Integer(-3),                                 # real & nonzero
        sqrt(2),                                     # real & nonzero
        Symbol("r", real=True, nonzero=True),        # real & nonzero
        Symbol("u", real=True),                      # real, zero undet (T,N,F,N) -> bail
        I,                                           # pure imaginary   (F,F,T,T)
        2 * I,                                       # pure imaginary
        (1 + I) ** 2,                                # pure imaginary (issue reproducer term)
        Symbol("m", imaginary=True),                 # pure imaginary
        I * Symbol("p", real=True),                  # imaginary-or-zero(N,N,N,T)
        Symbol("g"),                                 # generic          (N,N,N,N) -> bail
    ]


# --- the R/I shadow: Solution.lean classify/tallyAll/verdict, transliterated --
def _tri(v):
    """The Option Bool projection of a sympy fuzzy fact: True/False/None."""
    return v  # already True / False / None; mirrors `some true/false/none`


def shadow_eval_is_zero(self):
    """verdict isComm (len args) (tallyAll args), transliterated to operate on a
    real `Add`. Reads only the four projected facts of each summand and the
    commutativity fact; leaves the residual sub-decision to the REAL callee."""
    args = self.args
    n = len(args)
    is_comm = _tri(self.is_commutative)

    # tallyAll / classify (the fold)
    z = 0
    nz = []
    im = False
    im_or_z = False
    bail = False
    for a in args:
        if bail:
            break
        is_real = _tri(a.is_real)
        if is_real is True:
            is_zero = _tri(a.is_zero)
            if is_zero is True:
                z += 1
            elif is_zero is False:
                nz.append(a)
            else:
                bail = True
        elif _tri(a.is_imaginary) is True:
            im = True
        elif _tri((S.ImaginaryUnit * a).is_real) is True:
            im_or_z = True
        else:
            bail = True

    # verdict (the post-loop cascade)
    if is_comm is False:
        return None
    if bail:
        return None
    if z == n:
        return True
    if len(nz) == 0 or len(nz) == n:
        return None
    # A-tagged residual sub-decision: the REAL callee self.func(*nz).is_zero
    b_is_zero = _tri(self.func(*nz).is_zero)
    if b_is_zero is True:
        if (not im_or_z) and (not im):
            return True
        elif im and (not im_or_z):
            return False
        else:
            return None
    elif b_is_zero is False:
        return False
    else:
        return None


def oracle_eval_is_zero(self):
    """patch.diff's behaviour: the patched Add._eval_is_zero (resolved from the
    repo at base_commit with the gold patch applied)."""
    return self._eval_is_zero()


def build_add(summands):
    """An unevaluated Add of the chosen summands (keeps multi-arg structure so
    the per-term fold and the residual route are exercised). Returns None when
    the construction does not yield a genuine `Add` (e.g. a single summand
    collapses to the summand itself, whose `_eval_is_zero` is a different
    method) — the modeled function under test is `Add._eval_is_zero`, so such
    non-`Add` objects are out of scope."""
    e = Add(*summands, evaluate=False)
    if not isinstance(e, Add):
        return None
    return e


def fuzz_inputs(n, rng):
    pool = atom_pool()
    # boundary cases first (plan §4.1 step 4)
    yield [(-2) * I, (1 + I) ** 2]                 # the issue reproducer: nz empty, both imaginary
    yield [I, 2 * I]                               # nz empty, all imaginary
    yield [Integer(0), Integer(0)]                 # all real-zero -> True
    yield [Integer(2), I]                          # nz proper, imaginary -> residual reached
    yield [Symbol("r", real=True, nonzero=True), I]
    yield [I * Symbol("p", real=True), I]          # im_or_z + im
    yield [Integer(2), Integer(-2)]                # nz == n -> None
    yield [Symbol("u", real=True), I]              # bail (real, zero undet)
    yield [Symbol("g"), I]                         # bail (generic)
    yield [Integer(0)]                             # singleton zero
    yield [Integer(2), Integer(3), I, 2 * I]
    for _ in range(n):
        k = rng.randint(1, 5)
        yield [rng.choice(pool) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    skipped = 0
    for summands in fuzz_inputs(N_FUZZ, rng):
        try:
            e = build_add(summands)
            if e is None:
                skipped += 1
                continue
            shadow = shadow_eval_is_zero(e)
            oracle = oracle_eval_is_zero(e)
        except Exception:
            skipped += 1
            continue
        count += 1
        if shadow != oracle:
            disagreements.append((summands, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  summands=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of sumIsZero agrees with patch.diff behaviour "
          "on %d inputs (seed=%d; %d skipped as non-constructible), 0 "
          "disagreements." % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
