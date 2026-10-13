#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15875 (nagini).

SHADOW: the impl region of model.py's ``add_is_zero``, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The
@Pure helpers ``count_eq`` / ``has_eq`` copy over as plain functions on a
PSeq realized as an immutable tuple shim (the executable impl statements
themselves never touch PSeq — the in-loop Assert lines that did are contract
calls and are stripped). There are no @ContractOnly callees in this bundle
(the axioms region is empty).

ORACLE: the REAL patched repo routine the model models per mapping.md —
``Add._eval_is_zero`` (sympy/core/add.py). The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
package importable.

Type bridge (mapping.md section 2): a summand of a real ``Add`` maps to the
integer class tag 0..5 naming the branch the routine's scan takes for it
(real&zero / real&nonzero / real-undetermined / imaginary /
imaginary-or-zero / other), observed by the very same assumption queries the
routine issues; the three-valued zeroness of the sum of the real-nonzero
summands maps to ``sub_is_zero: Optional[bool]`` (True/False/None
identically). Inputs are therefore realized as genuine ``Add`` expressions;
for each one the pair (classes, sub_is_zero) is observed exactly as the
routine observes it — the class of each element of ``expr.args`` and the
``is_zero`` of ``expr.func(*real_nonzero_args)`` — in one consistent
evaluation, and the shadow verdict on that pair is diffed against the real
routine's verdict on the expression.

Requires bridging: class tags land in 0..5 by construction of the
observation; the model's linking precondition (no real-nonzero summand
implies the sub-expression is zero — the empty sum is the zero object, whose
zeroness is True) is checked per input and any violating observation is
skipped as out-of-domain (none are expected).

Input domain: boundary expressions covering every class combination and
every three-valued sub-expression zeroness (including unevaluated sums whose
real-nonzero part cancels, which realize the sub-is-zero-True branches with
imaginary classes present), plus randomized fuzz over a palette realizing
every summand class, with unevaluated construction mixed in so duplicate and
cancelling summands are exercised. >= 1e5 Requires-satisfying realized
inputs. Pinned fuzz seed: 15875.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the package under test only.
"""
import json
import random
import sys
import warnings

warnings.filterwarnings("ignore")

SEED = 15875
N_TARGET = 100_000


# --- PSeq shim: immutable sequence, the operations the pure helpers use ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- pure helpers from model.py, copied over as plain functions ---------------

def count_eq(s, c):
    if len(s) == 0:
        return 0
    return (1 if s[0] == c else 0) + count_eq(s.drop(1), c)


def has_eq(s, c):
    if len(s) == 0:
        return False
    return s[0] == c or has_eq(s.drop(1), c)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def add_is_zero(classes, sub_is_zero):
    z = 0
    nz = 0
    im = False
    im_or_z = False
    has2 = False
    has5 = False
    n = len(classes)
    i = n
    # backward scan: the suffix drop(i) aligns with the front-recursive folds,
    # so each step prepends classes[i-1] and unfolds count_eq/has_eq once.
    while i > 0:
        c = classes[i - 1]
        if c == 0:
            z = z + 1
        elif c == 1:
            nz = nz + 1
        elif c == 2:
            has2 = True
        elif c == 3:
            im = True
        elif c == 4:
            im_or_z = True
        else:
            has5 = True
        i = i - 1
    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False


# --- bridge: observe (classes, sub_is_zero) exactly as the routine does ------

def make_observers():
    from sympy import S

    def classify(a):
        """The class tag naming the branch the routine's scan takes for a."""
        if a.is_real:
            if a.is_zero:
                return 0           # real & known-zero
            if a.is_zero is False:
                return 1           # real & known-nonzero
            return 2               # real & undetermined
        elif a.is_imaginary:
            return 3               # imaginary
        elif (S.ImaginaryUnit * a).is_real:
            return 4               # imaginary-or-zero
        else:
            return 5               # other

    def observe(expr):
        classes = [classify(a) for a in expr.args]
        nz_args = [a for a, c in zip(expr.args, classes) if c == 1]
        sub_is_zero = expr.func(*nz_args).is_zero
        return classes, sub_is_zero

    return classify, observe


def check(expr, observe, stats):
    """Diff the shadow against the real routine on one Add; return an error
    string on disagreement, else None. Returns None (no count) for inputs
    that fall outside the modeled domain."""
    if not getattr(expr, "is_Add", False):
        return None  # auto-simplified away; not a realized input
    if expr.is_commutative is False:
        return None  # outside the modeled (commutative) domain
    classes, sub_is_zero = observe(expr)
    # Requires bridging: tags are 0..5 by construction; check the linking
    # precondition between the two observed inputs.
    if classes.count(1) == 0 and sub_is_zero is not True:
        return None  # out-of-domain observation (not expected to occur)
    real = expr._eval_is_zero()          # the REAL patched routine
    shadow = add_is_zero(classes, sub_is_zero)
    stats["checked"] += 1
    stats["sub_seen"][repr(sub_is_zero)] = stats["sub_seen"].get(
        repr(sub_is_zero), 0) + 1
    if shadow is not real:
        return ("DISAGREEMENT\n  expr=%r\n  classes=%r sub_is_zero=%r\n"
                "  shadow=%r\n  real=%r"
                % (expr, classes, sub_is_zero, shadow, real))
    # pure-helper self-consistency: the folds agree with list count/membership
    seq = PSeq(*classes)
    for tag in range(6):
        if count_eq(seq, tag) != classes.count(tag):
            return "PURE-HELPER MISMATCH count_eq on %r tag %d" % (classes, tag)
        if has_eq(seq, tag) != (tag in classes):
            return "PURE-HELPER MISMATCH has_eq on %r tag %d" % (classes, tag)
    return None


def boundary_exprs():
    from sympy import I, Symbol, Integer, Add, sqrt, Rational
    a1 = Symbol("ba", real=True, positive=True)
    a2 = Symbol("bb", real=True, positive=True)
    u1 = Symbol("bu", real=True, nonzero=True)
    u2 = Symbol("bv", real=True, nonzero=True)
    ru = Symbol("br", real=True)
    gen = Symbol("bg")
    m1 = Symbol("bm", imaginary=True)
    m2 = Symbol("bn", imaginary=True)
    w = Symbol("bw", real=True)
    exprs = [
        -2 * I + (1 + I) ** 2,        # the issue witness (all-imaginary classes)
        a1 + m1,                      # real-nonzero + imaginary
        a1 + a2,                      # every summand real-nonzero
        m1 + m2,                      # all imaginary, no real-nonzero summand
        a1 + a2 + m1,                 # mixed, sub provably nonzero
        a1 + w * I,                   # real-nonzero + imaginary-or-zero
        a1 + m1 + w * I,              # real-nonzero + both imaginary classes
        u1 - u2 + m1,                 # sub-expression zeroness undecided
        u1 + u2 + m1,                 # sub-expression zeroness undecided
        a1 + ru,                      # real-undetermined present
        a1 + gen,                     # unclassified summand present
        Integer(0) + a1 + m1,         # known-zero + real-nonzero + imaginary
        sqrt(2) + Rational(7, 3) + m1,
        2 * I + 3 * I + a1,
        # unevaluated sums whose real-nonzero part cancels: these realize a
        # zero sub-expression together with each imaginary-class combination
        Add(u1, -u1, m1, evaluate=False),
        Add(u1, -u1, w * I, evaluate=False),
        Add(u1, -u1, m1, w * I, evaluate=False),
        Add(u1, -u1, gen, evaluate=False),
        Add(u1, -u1, ru, evaluate=False),
        Add(u1, -u1, Integer(0), m1, evaluate=False),
        Add(u1, -u1, evaluate=False),           # every summand real-nonzero
        Add(Integer(0), Integer(0), evaluate=False),   # all known-zero
        Add(u1, u1, m1, evaluate=False),        # duplicate summands
        Add(m1, m1, evaluate=False),
    ]
    return exprs


def main():
    # REAL patched package (PYTHONPATH=/testbed; the gate applied the patch).
    from sympy import I, Symbol, Integer, Add, sqrt, Rational

    classify, observe = make_observers()
    stats = {"checked": 0, "sub_seen": {}}

    n_boundary = 0
    for expr in boundary_exprs():
        before = stats["checked"]
        err = check(expr, observe, stats)
        if err:
            print(err)
            return 1
        n_boundary += stats["checked"] - before

    # randomized fuzz: a fixed palette realizing every summand class, sampled
    # into small sums; a slice is built unevaluated so cancelling/duplicate
    # summands (and thus a zero sub-expression with imaginary classes) occur.
    rng = random.Random(SEED)
    pool = []
    for k in range(8):
        pool.append(Symbol("u%d" % k, real=True, nonzero=True))       # class 1
        pool.append(Symbol("q%d" % k, real=True, positive=True))      # class 1
    for k in range(4):
        pool.append(Symbol("r%d" % k, real=True))                     # class 2
        pool.append(Symbol("g%d" % k))                                # class 5
        pool.append(Symbol("m%d" % k, imaginary=True))                # class 3
        pool.append(Symbol("w%d" % k, real=True) * I)                 # class 4
    pool += [Integer(0), Integer(2) * I, Integer(3) * I, sqrt(2),
             Rational(7, 3), (1 + I) ** 2, -2 * I]

    attempts = 0
    max_attempts = 8 * N_TARGET
    while stats["checked"] < N_TARGET + n_boundary and attempts < max_attempts:
        attempts += 1
        k = rng.randint(1, 5)
        summ = []
        for _ in range(k):
            base = rng.choice(pool)
            if rng.random() < 0.25:
                base = -base
            summ.append(base)
        if rng.random() < 0.4 and len(summ) >= 2:
            # unevaluated: keeps duplicates and cancelling pairs as summands
            if rng.random() < 0.5:
                cancel = rng.choice(pool)
                summ = summ[:-1] + [cancel, -cancel]
            expr = Add(*summ, evaluate=False)
        else:
            expr = Add(*summ)
        err = check(expr, observe, stats)
        if err:
            print(err)
            return 1

    n_fuzz = stats["checked"] - n_boundary
    if stats["checked"] < N_TARGET:
        print("FAIL: only %d realized inputs (target %d)"
              % (stats["checked"], N_TARGET))
        return 1
    if not all(stats["sub_seen"].get(v, 0) > 0 for v in ("True", "False", "None")):
        print("FAIL: fuzz did not exercise all sub-expression zeroness values: %r"
              % stats["sub_seen"])
        return 1

    print("G-CONF OK: shadow impl == real patched routine on %d realized Add "
          "inputs (%d boundary + %d fuzz, seed %d); sub-zeroness distribution %r"
          % (stats["checked"], n_boundary, n_fuzz, SEED, stats["sub_seen"]))
    print(json.dumps({"checked": stats["checked"], "disagreements": 0,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
