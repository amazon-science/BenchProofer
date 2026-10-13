#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-18199 (nagini).

SHADOW  — the `# impl-start` / `# impl-end` region of `model.py` copied
          VERBATIM below (function `nth_roots`), with only the contract
          statements removed (`Requires`, `Ensures`, `Invariant`, `Assert`,
          `MustTerminate` and the `# invariants-start/-end` markers).  The
          model IS Python, so there is no transliteration step: the dispatch
          order (`not is_prime(p)` -> composite; `a % p == 0` -> `[0]`;
          `not is_nth_residue` -> `[]`; else the prime-field copy loop) and
          both copy loops are the model's own statements.
          Its `@Pure` dependencies are copied the same way:
            * `composite_roots(a, n, p)` -> `roots_below(p, a, n, p)` (body
              verbatim), `roots_below` (the structural recursive fold over the
              candidate residues), `is_root`, `composite_validated`.
          The `@ContractOnly` callees have no body to copy, so each one CALLS
          THE REAL REPO FUNCTION it axiomatizes (mapping.md §1/§3), which is
          what makes the axioms exercised rather than assumed:
            * `power_mod(x, n, p)`      -> the real three-argument `pow`
              builtin used throughout `nthroot_mod` (§3.1);
            * `is_prime(p)`             -> `sympy.ntheory.primetest.isprime`
              (§3.2), the predicate the gold's new dispatch branches on;
            * `is_nth_residue(a, n, p)` -> `is_nthpow_residue`
              (`sympy/ntheory/residue_ntheory.py:620`) (§3.3);
            * `is_squarefree(p)`        -> "all `factorint(p)` exponents == 1"
              (§3.2 row), used only inside `composite_validated`;
            * `prime_roots(a, n, p)`    -> the unchanged prime-field body of
              `nthroot_mod` reached by calling
              `nthroot_mod(a, n, p, all_roots=True)` on a prime `p` with
              `a % p != 0` (§3.5) — the exact callee the A-reference names.
          So the shadow's composite branch is the DEEP model (the complete
          brute-force root set the spec pins), while the prime branch defers to
          the real prime-field solver exactly as the axiom says it may.

ORACLE  — the REAL PATCHED repo function, CALLED, not transliterated:
          `nthroot_mod(a, n, p, all_roots=True)` in
          `sympy/ntheory/residue_ntheory.py:746` (mapping.md §1), imported from
          /testbed with the gold patch already applied by the gate.  Nothing
          about it needs re-implementing (the inputs are three integers), so
          there is no transliteration anywhere in this file.  A pre-patch
          import is detected and reported as an ERROR (exit 2) rather than
          being diffed, so an unpatched container can never read as a pass.

BRIDGE  — mapping.md §2, inverted.  The integer carriers are the identity
          (`int` <-> repo `int`/`mpz`, `as_int` is the identity on them), so
          the only real bridging is on the result: the model returns
          `List[int]`, the real callee returns a list of `int`/`mpz` OR `None`
          for "no solution", so the oracle side maps `None -> []` and each
          element through `int(...)`.  `PSeq` (the model's immutable sequence
          carrier for the two root sets) is the small tuple shim below, and
          `ToSeq(list)` materializes one; the copy loops are compared through
          it exactly as written.  Lists are compared ORDER-SENSITIVELY
          (stricter than mapping.md §2, which leaves order an unconstrained
          R-detail) — the deep fold emits ascending residues and the patched
          composite routine returns `sorted(set(...))`, so the stronger
          comparison is the one that can still fail.

INPUT DOMAIN — every generated triple satisfies `nth_roots`'s `Requires`:
          `a >= 0`, `n > 2`, `p > 2`, and `is_prime(p) or
          composite_validated(a, n, p)`, checked by an assertion on the shadow
          side (`requires_ok`) so a stray out-of-domain input aborts instead of
          being silently compared.  The `composite_validated` filter is the
          MODEL'S OWN precondition, copied verbatim from the frozen artifact,
          not a domain weakened to dodge a disagreement: mapping.md §3.4 and
          axiom_check.py record that outside it the gold patch's prime-power
          lifting genuinely diverges from the complete root set (a documented
          gold defect), which is why the frozen spec refuses to claim anything
          there.  Inside the domain every impl branch is exercised and the
          per-branch counters are asserted non-zero, so a run that quietly
          missed the branch the gold patch changed (the composite dispatch, and
          the prime `a % p == 0 -> [0]` case the gold added) fails loudly.

Boundary cases first: all six `composite_validated` triples (including the two
FAIL_TO_PASS `test_solve_modular` shapes `x**3 = 1 (mod 8)` and
`x**4 = 4 (mod 9)`, the no-root `(4, 3, 3249000)` and the zero-target composite
`(0, 7, 100)`), the gold's `test_residue` additions, the issue's own
`nthroot_mod(17*17, 5, 17)` example, and the small-modulus/zero-target/large-`a`
edges.  Then seeded fuzz to >= 100000 total comparisons.  Pinned seed: 18199
(recorded in mapping.md §G-CONF).

`roots_below` is structurally recursive with depth `p`, so it is evaluated
directly (verbatim) for every modulus with `p <= 1500` and by an unrolled
evaluation of the SAME recurrence for the two larger enumerated moduli (87382,
3249000), where a Python recursion of that depth cannot run.  The unrolled form
is cross-checked against the verbatim recursion on every input where the
recursion is evaluable (i.e. on all ~1e5 in-regime inputs but those two), so it
is validated, not assumed.

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit code is 1.  stdlib + the repo under test only.
"""
import random
import sys
from typing import List  # noqa: F401  (the copied `# type: List[int]` comments)

SEED = 18199
N_TOTAL = 100000          # >= 1e5 Requires-satisfying comparisons
RECURSION_SAFE_P = 1500   # verbatim recursive fold evaluable up to this p

sys.setrecursionlimit(6000)


# ---------------------------------------------------------------------------
# PSeq / ToSeq shim: model.py's immutable pure sequence carrier (mapping.md §2)
# as a plain tuple wrapper (take / drop / + / len / [] / ==).
# ---------------------------------------------------------------------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *elems):
        self._t = tuple(elems)

    @classmethod
    def _of(cls, iterable):
        s = cls()
        s._t = tuple(iterable)
        return s

    def take(self, n):
        return PSeq._of(self._t[:n])

    def drop(self, n):
        return PSeq._of(self._t[n:])

    def __add__(self, other):
        return PSeq._of(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._of(lst)


# ---------------------------------------------------------------------------
# model.py `axioms` region: @ContractOnly callees have no body, so each one
# calls the REAL repo function it axiomatizes (mapping.md §1/§3).
# ---------------------------------------------------------------------------

def power_mod(x, n, p):
    """mapping.md §3.1: the unchanged three-argument `pow` builtin used
    pervasively inside `nthroot_mod`/`_nthroot_mod_composite`."""
    return pow(x, n, p)


def is_prime(p):
    """mapping.md §3.2: `sympy.ntheory.primetest.isprime`, the predicate the
    gold's new `if not isprime(p)` dispatch branches on."""
    from sympy import isprime
    return bool(isprime(p))


def is_squarefree(p):
    """mapping.md §1/§3.2: "p has no repeated prime factor", i.e. every
    `factorint(p)` exponent is 1 (the real factorisation callee)."""
    from sympy import factorint
    return all(e == 1 for e in factorint(p).values())


def is_nth_residue(a, n, p):
    """mapping.md §3.3: the unchanged `is_nthpow_residue(a, n, p)`
    (`sympy/ntheory/residue_ntheory.py:620`)."""
    from sympy.ntheory.residue_ntheory import is_nthpow_residue
    return bool(is_nthpow_residue(a, n, p))


def prime_roots(a, n, p):
    """mapping.md §3.5: the unchanged prime-field body of `nthroot_mod` for a
    prime modulus with a non-zero target, reached by calling the real function
    (`(p-1)%n`/gcd reductions + `_nthroot_mod1`/`sqrt_mod`).  Returned as the
    model's PSeq[int] carrier; the real callee's `None` ("no solution") is the
    empty sequence per the mapping.md §2 bridge."""
    from sympy.ntheory.residue_ntheory import nthroot_mod
    res = nthroot_mod(a, n, p, all_roots=True)
    if res is None:
        return PSeq()
    if isinstance(res, int):
        return PSeq(int(res))
    return PSeq._of(int(x) for x in res)


# ---------------------------------------------------------------------------
# model.py `pure` region, copied VERBATIM minus the contract statements.
# ---------------------------------------------------------------------------

def is_root(x, n, p, a):
    return 0 <= x and x < p and power_mod(x, n, p) == a % p


def roots_below(k, a, n, p):
    if k == 0:
        return PSeq(0).take(0)
    if is_root(k - 1, n, p, a):
        return roots_below(k - 1, a, n, p) + PSeq(k - 1)
    return roots_below(k - 1, a, n, p)


def roots_below_unrolled(k, a, n, p):
    """The same recurrence as `roots_below`, evaluated bottom-up so that moduli
    beyond Python's recursion depth (the enumerated 87382 / 3249000) can be
    checked at all.  Cross-checked against the verbatim recursion on every
    input where the recursion is evaluable (see `deep_root_seq`)."""
    acc = PSeq(0).take(0)
    r = 0
    while r < k:
        if is_root(r, n, p, a):
            acc = acc + PSeq(r)
        r = r + 1
    return acc


def composite_validated(a, n, p):
    return (is_squarefree(p)
            or (a == 1 and n == 3 and p == 8)
            or (a == 4 and n == 4 and p == 9)
            or (a == 16 and n == 5 and p == 36)
            or (a == 9 and n == 16 and p == 36)
            or (a == 4 and n == 3 and p == 3249000)
            or (a == 0 and n == 7 and p == 100))


def deep_root_seq(k, a, n, p):
    """`roots_below(k, a, n, p)`: the verbatim recursion when its depth is
    runnable, else the unrolled evaluation of the same recurrence.  When both
    are runnable they are compared, so the unrolled form is validated."""
    unrolled = roots_below_unrolled(k, a, n, p)
    if k <= RECURSION_SAFE_P:
        recursive = roots_below(k, a, n, p)
        if recursive != unrolled:
            raise AssertionError(
                "roots_below recursion/unrolling mismatch on "
                "(k=%r,a=%r,n=%r,p=%r): %r vs %r"
                % (k, a, n, p, recursive, unrolled))
    return unrolled


def composite_roots(a, n, p):
    """Body verbatim: `return roots_below(p, a, n, p)`."""
    return deep_root_seq(p, a, n, p)


# ---------------------------------------------------------------------------
# model.py impl region (`# impl-start` .. `# impl-end`), VERBATIM with the
# contract statements (Requires/Ensures/Invariant/Assert/MustTerminate) and the
# `# invariants-start/-end` markers removed.
# ---------------------------------------------------------------------------

BRANCHES = {"composite": 0, "prime_zero": 0, "prime_nonresidue": 0,
            "prime_roots": 0}


def nth_roots(a, n, p):
    # impl-start
    if not is_prime(p):
        BRANCHES["composite"] += 1                      # branch counter only
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr):
            res.append(cr[i])
            i = i + 1
        return res
    if a % p == 0:
        BRANCHES["prime_zero"] += 1                     # branch counter only
        zero = [0]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        BRANCHES["prime_nonresidue"] += 1               # branch counter only
        empty = []  # type: List[int]
        return empty
    BRANCHES["prime_roots"] += 1                        # branch counter only
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        out.append(pr[j])
        j = j + 1
    return out
    # impl-end


# ---------------------------------------------------------------------------
# Requires of `nth_roots`, as a domain guard on the generated inputs.
# ---------------------------------------------------------------------------

def requires_ok(a, n, p):
    return (a >= 0 and n > 2 and p > 2
            and (is_prime(p) or composite_validated(a, n, p)))


# ---------------------------------------------------------------------------
# Oracle: the REAL patched `nthroot_mod(a, n, p, all_roots=True)`.
# ---------------------------------------------------------------------------

def oracle(a, n, p):
    from sympy.ntheory.residue_ntheory import nthroot_mod
    res = nthroot_mod(a, n, p, all_roots=True)
    if res is None:                     # mapping.md §2: None <-> []
        return []
    if isinstance(res, int):
        return [int(res)]
    return [int(x) for x in res]


def require_post_patch():
    """The gate applies patch.diff before this script runs.  Refuse to diff
    against a pre-patch module: there the composite dispatch raises
    NotImplementedError and the prime zero-target case is missing, so every
    disagreement would be an environment error masquerading as a finding."""
    from sympy.ntheory.residue_ntheory import nthroot_mod
    try:
        composite = nthroot_mod(1, 3, 8, all_roots=True)
    except NotImplementedError:
        composite = None
    zero_target = nthroot_mod(17 * 17, 5, 17, all_roots=True)
    if composite is None or zero_target is None or 0 not in list(zero_target):
        print("G-CONF ERROR: imported nthroot_mod behaves pre-patch "
              "(composite=%r, zero-target=%r); the gate must apply patch.diff "
              "before this script runs" % (composite, zero_target))
        sys.exit(2)


# ---------------------------------------------------------------------------
# Input generation: boundary first, then seeded fuzz over the Requires domain.
# ---------------------------------------------------------------------------

# The six triples of the model's `composite_validated` enumeration (the
# non-squarefree moduli the test suite actually reaches) plus the gold's other
# `test_residue` assertions, the FAIL_TO_PASS shapes and the issue example.
BOUNDARY = [
    (1, 3, 8),          # F2P  solveset(Mod(x**3, 8) - 1)   -> {1}     (2**3)
    (4, 4, 9),          # F2P  solveset(Mod(x**4, 9) - 4)   -> {4, 5}  (3**2)
    (16, 5, 36),        # test_residue, non-squarefree 36
    (9, 16, 36),        # test_residue, non-squarefree 36
    (0, 7, 100),        # test_residue, zero target, non-squarefree 100
    (4, 3, 3249000),    # test_residue, no roots, non-squarefree
    (29, 31, 74),       # test_residue, squarefree composite 74 = 2*37
    (36010, 8, 87382),  # test_residue, squarefree composite 2*43691
    (0, 12, 37),        # test_residue, PRIME modulus, zero target -> [0]
    (17 * 17, 5, 17),   # the issue's own example (prime, a % p == 0)
    # small-modulus / zero-target / large-target / minimal-n edges
    (0, 3, 3), (1, 3, 3), (2, 3, 3), (3, 3, 3), (12, 3, 3),
    (0, 3, 6), (1, 3, 6), (5, 3, 6), (6, 3, 6), (36, 3, 6),
    (0, 3, 5), (1, 3, 5), (2, 3, 5), (5, 3, 5), (10, 4, 5),
    (0, 4, 15), (1, 4, 15), (7, 5, 15), (15, 3, 15), (225, 3, 15),
    (0, 3, 7), (2, 3, 7), (3, 3, 7), (6, 3, 7), (49, 3, 7),
    (1, 3, 2 * 3 * 5 * 7), (0, 5, 2 * 3 * 5 * 7), (209, 9, 2 * 3 * 5 * 7),
    (10 ** 6, 3, 11), (10 ** 6, 3, 30), (10 ** 6 + 1, 17, 101),
    (0, 30, 3), (1, 29, 6), (5, 23, 13),
]

PRIME_POOL = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59,
              61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127,
              131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191,
              193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257,
              263, 269, 271, 277, 281, 283, 293]

# squarefree composites (products of distinct primes) -> in the validated
# regime for every (a, n), so the composite branch is genuinely fuzzed.
SQUAREFREE_COMPOSITES = [6, 10, 14, 15, 21, 22, 26, 30, 33, 34, 35, 38, 39,
                         42, 46, 51, 55, 57, 58, 62, 65, 66, 69, 70, 74, 77,
                         78, 82, 85, 86, 87, 91, 93, 94, 95, 102, 105, 106,
                         110, 111, 114, 115, 118, 119, 122, 123, 129, 130,
                         133, 138, 141, 142, 143, 145, 146, 154, 155, 158,
                         159, 161, 165, 170, 174, 177, 178, 182, 183, 185,
                         186, 187, 190, 195, 201, 202, 203, 205, 206, 209,
                         210, 213, 214, 215, 217, 218, 219, 221, 222, 226,
                         230, 231, 235, 238, 246, 247, 253, 255, 258, 259,
                         262, 265, 266, 267, 273, 274, 285, 286, 290, 291]

# the enumerated non-squarefree triples are validated only at those exact
# (a, n, p), so they are fuzzed as whole triples.
ENUM_TRIPLES = [(1, 3, 8), (4, 4, 9), (16, 5, 36), (9, 16, 36), (0, 7, 100)]


def fuzz_triple(rng):
    kind = rng.random()
    if kind < 0.06:
        return rng.choice(ENUM_TRIPLES)
    if kind < 0.53:
        p = rng.choice(SQUAREFREE_COMPOSITES)
    else:
        p = rng.choice(PRIME_POOL)
    n = rng.randint(3, 30)
    at = rng.random()
    if at < 0.12:
        a = 0                                    # zero target
    elif at < 0.24:
        a = p * rng.randint(1, 40)               # a % p == 0, a >= p
    elif at < 0.72:
        a = rng.randrange(0, p)                  # reduced target
    else:
        a = rng.randrange(0, 10 ** rng.randint(1, 7))   # unreduced target
    return (a, n, p)


# ---------------------------------------------------------------------------
# Differential loop.
# ---------------------------------------------------------------------------

def main():
    try:
        import sympy  # noqa: F401
        from sympy.ntheory.residue_ntheory import nthroot_mod  # noqa: F401
    except Exception as e:
        print("G-CONF ERROR: repo import failed: %r" % (e,))
        return 2
    require_post_patch()

    rng = random.Random(SEED)
    disagreements = []
    checked = 0
    skipped_out_of_domain = 0

    def compare(a, n, p):
        nonlocal checked, skipped_out_of_domain
        if not requires_ok(a, n, p):
            # only reachable for a fuzz draw that lands outside the model's
            # Requires (a non-squarefree modulus that is not an enumerated
            # triple); it is never compared, and the count is reported.
            skipped_out_of_domain += 1
            return True
        shadow = nth_roots(a, n, p)
        try:
            real = oracle(a, n, p)
        except Exception as e:            # a raise IS a disagreement: the
            real = "EXCEPTION %r" % (e,)  # spec claims a total function here
        checked += 1
        if shadow != real:
            disagreements.append((a, n, p, shadow, real))
        return len(disagreements) < 10

    for (a, n, p) in BOUNDARY:
        assert requires_ok(a, n, p), (
            "boundary input (%r,%r,%r) violates nth_roots' Requires" % (a, n, p))
        if not compare(a, n, p):
            break

    while checked < N_TOTAL and not disagreements:
        a, n, p = fuzz_triple(rng)
        if not compare(a, n, p):
            break

    missing = [k for k, v in BRANCHES.items() if v == 0]
    if missing and not disagreements:
        print("G-CONF FAIL: impl branch(es) never exercised: %s "
              "(a green run that skips the branch under specification "
              "certifies nothing)" % ", ".join(sorted(missing)))
        return 1

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d comparisons (seed=%d):"
              % (len(disagreements), checked, SEED))
        for a, n, p, shadow, real in disagreements:
            print("  (a,n,p)=(%r,%r,%r) shadow=%r real_patched=%r"
                  % (a, n, p, shadow, real))
        print('{"status": "fail", "checked": %d, "seed": %d, '
              '"disagreements": %d}' % (checked, SEED, len(disagreements)))
        return 1

    print("G-CONF OK: model.py impl shadow of nth_roots (deep composite fold + "
          "real prime-field/primality/residue callees) agrees with the real "
          "patched nthroot_mod(a,n,p,all_roots=True) on %d Requires-satisfying "
          "inputs (seed=%d), branches %s, 0 disagreements."
          % (checked, SEED, BRANCHES))
    print('{"status": "pass", "checked": %d, "seed": %d, "disagreements": 0, '
          '"branches": {"composite": %d, "prime_zero": %d, '
          '"prime_nonresidue": %d, "prime_roots": %d}, '
          '"out_of_domain_draws_skipped": %d, '
          '"oracle": "sympy.ntheory.residue_ntheory.nthroot_mod(a,n,p,'
          'all_roots=True) [patched, called]"}'
          % (checked, SEED, BRANCHES["composite"], BRANCHES["prime_zero"],
             BRANCHES["prime_nonresidue"], BRANCHES["prime_roots"],
             skipped_out_of_domain))
    return 0


if __name__ == "__main__":
    sys.exit(main())
