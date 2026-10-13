# properties.py — PBT falsification battery for sympy__sympy-18199.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Every
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we edit
# ONLY the text inside the single `# impl-start` / `# impl-end` block (the
# nth_roots impl), so the frozen spec (axioms / pure / pre-/post-conditions, the
# signature) is byte-identical to model.py and `markers.same_spec` holds by
# construction.
#
# ---------------------------------------------------------------------------
# Defended surface (model.py / mapping.md / refinement.md)
# ---------------------------------------------------------------------------
#   nth_roots(a: int, n: int, p: int) -> List[int]
#     Requires  a >= 0, n > 2, p > 2,  is_prime(p) OR composite_validated(a,n,p)
#     Ensures   Acc(list_pred(Result()))
#     Ensures   SOUNDNESS — Forall k in [0,len): is_root(Result()[k], n, p, a)
#                 (every returned value is an in-range root; is_root unfolds to
#                  0<=x<p and power_mod(x,n,p)==a%p — GROUNDED in the real pow)
#     Ensures   COMPLETENESS, three load-bearing branch clauses pinning the
#               result EXACTLY to a grounded root set:
#                 (C-comp) not is_prime(p) and composite_validated(a,n,p)
#                            -> ToSeq(Result()) == composite_roots(a,n,p)
#                 (C-prime) is_prime(p) and a%p!=0 and is_nth_residue(a,n,p)
#                            -> ToSeq(Result()) == prime_roots(a,n,p)
#                 (C-zero)  is_prime(p) and a%p==0
#                            -> len(Result())==1 and Result()[0]==0
#
# ALL inputs are SCALAR ints (a, n, p). There is NO read-only list/object input
# (mapping.md §2: "there are no read-only list/object inputs ... directive-5
# fractional permission applies vacuously"). The only full-permission object is
# the RESULT list, which the impl creates. So the FRAME-MUTATION class is N/A —
# there is no Acc(...,1/2) parameter to overwrite. (See 'assessment'.)
#
# The oracle is GROUNDED, not an answer key: composite_roots/prime_roots are deep
# A-references (functions of the args, validated == real nthroot_mod by G-AX),
# and is_root unfolds to the real modular power. So the "ungrounded-oracle echo"
# class has no WRONG echo: echoing the grounded root set IS the correct value.
# It doubles as the cheapest-honest positive control (the take-loop copy of the
# PSeq into a List[int] is the cheapest impl — there is no scalar shortcut, the
# result must carry list_pred). See 'assessment'.
#
# ---------------------------------------------------------------------------
# The defended GAP this spec must close (where it would be hollow if weak):
# ---------------------------------------------------------------------------
# Soundness ALONE (returned values are roots) is satisfied VACUOUSLY by the empty
# list and by any SUBSET of the true root set — it never forces COMPLETENESS.
# The three completeness clauses are exactly what stop a root being dropped (the
# headline bug: the missing x=0 root; and the F2P bug: a declined composite
# modulus). The battery hammers precisely that gap from both sides:
#   * UNDER-keep (drop a root)  — drop-zero (prepatch), decline-composite
#     (prepatch_1), drop-last-composite-root; must fail a completeness `==`.
#   * OVER-keep (add a spurious entry) — duplicate-composite-root, two-zeros;
#     each keeps soundness (the extra entry is itself a root) but breaks the
#     exact sequence/singleton equality.
# Both prepatch skeletons are the proven G-DIFF failing rivals — reused here.
#
# AXIOM LANE: the bundle has 5 @ContractOnly axioms (power_mod, is_prime,
# is_squarefree, is_nth_residue) + 2 A-reference deep solvers (prime_roots,
# composite_roots). The probes RUN THE REAL sympy callee in Docker (never scrape
# source — pilot bug #4), open files utf-8 (#5), and are self-contained (#6):
#   * ax-sound-power_mod   — pow == power_mod incl. all 3 Ensures (range,
#                            zero-base, prime-field zero-divisor); boundary+fuzz.
#   * ax-sound-rootsets    — prime_roots/composite_roots == real
#                            nthroot_mod(...,all_roots=True) as a SET OF ROOTS,
#                            cross-checked vs an independent brute-force oracle,
#                            on the enumerated F2P/test inputs + squarefree fuzz.
#   * ax-sound-residue     — is_nthpow_residue True AND root 0 really exists when
#                            a%p==0 (the validated-but-dead Ensures, still true).
#   * ax-contain-composite — the KEY containment check: every composite input the
#                            MODEL can reach (Requires => composite_validated) is
#                            inside the regime where the real callee is EXACT, and
#                            the regime is LOAD-BEARING (gold returns non-roots
#                            OUTSIDE it). A reachable input outside the exact
#                            regime would be AXIOM-TOO-WEAK-FOR-CALLER.
# Mirrors the bundle's axiom_check.py (G-AX), which exits rc0 with the gold patch.

from pathlib import Path

INSTANCE = "sympy__sympy-18199"
FLOAT_ENCODING = None  # meta.json float_encoding is null (exact integer arithmetic)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: anchor not found: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen gold impl BODY (strictly between # impl-start / # impl-end).
# Every variant is produced by _swap-ing this single unique block for a new body
# whose markers/indentation match exactly. Editing only here keeps the spec view
# (and thus same_spec) byte-identical to model.py.
# ---------------------------------------------------------------------------
_GOLD_BODY = """    if not is_prime(p):
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr):
            # invariants-start
            Invariant(Acc(list_pred(res)))
            Invariant(0 <= i and i <= len(cr))
            Invariant(ToSeq(res) == cr.take(i))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
            Invariant(MustTerminate(len(cr) - i + 1))
            # invariants-end
            res.append(cr[i])
            i = i + 1
        Assert(cr.take(len(cr)) == cr)
        return res
    if a % p == 0:
        zero = [0]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        Invariant(MustTerminate(len(pr) - j + 1))
        # invariants-end
        out.append(pr[j])
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out"""


def _variant(body):
    """Replace ONLY the gold impl body; the spec view is preserved verbatim."""
    return _swap(_BASE, _GOLD_BODY, body)


# Sanity: the gold body must appear exactly once in the frozen model.
assert _BASE.count(_GOLD_BODY) == 1, "gold impl body drift vs model.py"


# ===========================================================================
# POSITIVE CONTROL 1 (soundness) — structurally-DIFFERENT but CORRECT.
# Reshape: bind the appended element to a typed local `v` before append in BOTH
# loops, and bind the prime-zero singleton via an intermediate. The loop
# DIRECTION is unchanged (forward, against the `cr.take(i)` invariant — flipping
# would need a take/drop fold lemma, pilot bug #3), and every gold invariant +
# framing Assert is KEPT verbatim (pilot bug #2). Only the executable shape
# changes (local binding). Must verify (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_RESHAPE = """    if not is_prime(p):
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr):
            # invariants-start
            Invariant(Acc(list_pred(res)))
            Invariant(0 <= i and i <= len(cr))
            Invariant(ToSeq(res) == cr.take(i))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
            Invariant(MustTerminate(len(cr) - i + 1))
            # invariants-end
            v = cr[i]
            res.append(v)
            i = i + 1
        Assert(cr.take(len(cr)) == cr)
        return res
    if a % p == 0:
        z = 0
        zero = [z]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        Invariant(MustTerminate(len(pr) - j + 1))
        # invariants-end
        w = pr[j]
        out.append(w)
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out"""


# ===========================================================================
# ADMISSIBILITY (verify) — the precondition admits a normal input AND each
# completeness branch is reachable (non-vacuous). Keep the gold impl verbatim;
# add entry Asserts (impl-region only) that re-derive the Requires disjunction
# and confirm the three completeness regimes are mutually consistent with a
# legitimate input. If the gold proof still discharges, the Requires accepts a
# normal F2P-shaped input (else PRECOND-TOO-STRONG).
# ===========================================================================
_ADMISS = """    # admissibility witnesses (impl-region only): the precondition holds and
    # is non-vacuous — it admits a prime modulus and a validated composite one,
    # and the three completeness regimes are reachable disjoint cases.
    Assert(is_prime(p) or composite_validated(a, n, p))
    Assert(a >= 0 and n > 2 and p > 2)
    Assert(Implies(is_prime(p) and a % p == 0, not (a % p != 0)))
    if not is_prime(p):
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr):
            # invariants-start
            Invariant(Acc(list_pred(res)))
            Invariant(0 <= i and i <= len(cr))
            Invariant(ToSeq(res) == cr.take(i))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
            Invariant(MustTerminate(len(cr) - i + 1))
            # invariants-end
            res.append(cr[i])
            i = i + 1
        Assert(cr.take(len(cr)) == cr)
        return res
    if a % p == 0:
        zero = [0]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        Invariant(MustTerminate(len(pr) - j + 1))
        # invariants-end
        out.append(pr[j])
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out"""


# ===========================================================================
# UNIQUENESS — DROP-ZERO (partial-domain on the prime zero-target sub-domain).
# This is verbatim the PRE-PATCH behaviour (model_prepatch.py): no `a%p==0->[0]`
# special case; the residue check runs first and the zero root x=0 is dropped
# (returns []). The empty list satisfies SOUNDNESS vacuously but FAILS the
# (C-zero) clause `len(Result())==1 and Result()[0]==0`. This is the headline
# fix of the issue (the missing x=0 mod p root). G-DIFF confirms model_prepatch
# is same_spec and fails exactly this postcondition.
# ===========================================================================
_DROP_ZERO = """    if not is_prime(p):
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr):
            # invariants-start
            Invariant(Acc(list_pred(res)))
            Invariant(0 <= i and i <= len(cr))
            Invariant(ToSeq(res) == cr.take(i))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
            Invariant(MustTerminate(len(cr) - i + 1))
            # invariants-end
            res.append(cr[i])
            i = i + 1
        Assert(cr.take(len(cr)) == cr)
        return res
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    if a % p == 0:
        dropped = []  # type: List[int]
        return dropped
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        Invariant(MustTerminate(len(pr) - j + 1))
        # invariants-end
        out.append(pr[j])
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out"""


# ===========================================================================
# UNIQUENESS — DECLINE-COMPOSITE (partial-domain on the non-prime sub-domain).
# Verbatim the PRE-PATCH behaviour (model_prepatch_1.py): a non-prime modulus is
# DECLINED (returns []), modelling the pre-patch `raise NotImplementedError`.
# The empty list is sound (vacuously) but FAILS the (C-comp) clause
# `ToSeq(Result()) == composite_roots(a,n,p)` whenever the root set is non-empty,
# e.g. the F2P x**3 = 1 (mod 8) = {1}. G-DIFF confirms model_prepatch_1 is
# same_spec and fails exactly this postcondition.
# ===========================================================================
_DECLINE_COMPOSITE = """    if not is_prime(p):
        declined = []  # type: List[int]
        return declined
    if a % p == 0:
        zero = [0]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        Invariant(MustTerminate(len(pr) - j + 1))
        # invariants-end
        out.append(pr[j])
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out"""


# ===========================================================================
# UNIQUENESS — DROP-LAST-COMPOSITE-ROOT (value-level double-mask / completeness).
# The composite copy loop stops one short (`while i < len(cr) - 1`), so it copies
# every composite root EXCEPT the last. EVERY returned value is still a genuine
# root, so SOUNDNESS holds — this is precisely the impl a soundness-only spec
# would wrongly admit. But `ToSeq(Result()) == cr.take(len(cr)-1) != cr` whenever
# the root set is non-empty, so it FAILS (C-comp). This is the strongest probe
# that completeness (not just soundness) is load-bearing: it drops a TRUE root
# while every element it keeps is valid.
# ===========================================================================
_DROP_LAST = """    if not is_prime(p):
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr) - 1:
            # invariants-start
            Invariant(Acc(list_pred(res)))
            Invariant(0 <= i and i <= len(cr))
            Invariant(ToSeq(res) == cr.take(i))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
            Invariant(MustTerminate(len(cr) - i + 1))
            # invariants-end
            res.append(cr[i])
            i = i + 1
        return res
    if a % p == 0:
        zero = [0]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        Invariant(MustTerminate(len(pr) - j + 1))
        # invariants-end
        out.append(pr[j])
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out"""


# ===========================================================================
# UNIQUENESS — DUPLICATE-COMPOSITE-ROOT (over-keep / completeness, the other
# side of the gap). After the gold copy loop, append the first root a SECOND
# time. The extra entry is itself a genuine root, so SOUNDNESS still holds — but
# `ToSeq(Result())` is now longer than `composite_roots(a,n,p)` (a trailing
# duplicate), so it FAILS (C-comp) `ToSeq(Result()) == composite_roots(...)`.
# This confirms the completeness clause pins the EXACT sequence (no over-count),
# not merely a superset of roots. (Guarded by len(cr) > 0 so the gold proof
# state is reached before the spurious append.)
# ===========================================================================
_DUP_FIRST = """    if not is_prime(p):
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr):
            # invariants-start
            Invariant(Acc(list_pred(res)))
            Invariant(0 <= i and i <= len(cr))
            Invariant(ToSeq(res) == cr.take(i))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
            Invariant(MustTerminate(len(cr) - i + 1))
            # invariants-end
            res.append(cr[i])
            i = i + 1
        Assert(cr.take(len(cr)) == cr)
        if len(cr) > 0:
            res.append(cr[0])
        return res
    if a % p == 0:
        zero = [0]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        Invariant(MustTerminate(len(pr) - j + 1))
        # invariants-end
        out.append(pr[j])
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out"""


# ===========================================================================
# UNIQUENESS — TWO-ZEROS (over-keep on the prime zero-target singleton).
# For the prime a%p==0 case return [0, 0]. Both entries are genuine roots
# (power_mod(0,n,p)==0==a%p), so SOUNDNESS holds — but the (C-zero) clause pins
# the result to the EXACT singleton `len(Result())==1 and Result()[0]==0`, which
# [0,0] (len 2) violates. This confirms the zero-target clause is an exact
# singleton, not "contains 0".
# ===========================================================================
_TWO_ZEROS = """    if not is_prime(p):
        cr = composite_roots(a, n, p)
        res = []  # type: List[int]
        i = 0
        while i < len(cr):
            # invariants-start
            Invariant(Acc(list_pred(res)))
            Invariant(0 <= i and i <= len(cr))
            Invariant(ToSeq(res) == cr.take(i))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(cr),
                0 <= cr[k] and cr[k] < p and power_mod(cr[k], n, p) == a % p))))
            Invariant(MustTerminate(len(cr) - i + 1))
            # invariants-end
            res.append(cr[i])
            i = i + 1
        Assert(cr.take(len(cr)) == cr)
        return res
    if a % p == 0:
        zero = [0, 0]  # type: List[int]
        return zero
    if not is_nth_residue(a, n, p):
        empty = []  # type: List[int]
        return empty
    pr = prime_roots(a, n, p)
    out = []  # type: List[int]
    j = 0
    while j < len(pr):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(pr))
        Invariant(ToSeq(out) == pr.take(j))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(pr),
            0 <= pr[k] and pr[k] < p and power_mod(pr[k], n, p) == a % p))))
        Invariant(MustTerminate(len(pr) - j + 1))
        # invariants-end
        out.append(pr[j])
        j = j + 1
    Assert(pr.take(len(pr)) == pr)
    return out"""


SPEC_TESTS = [
    {
        "id": "pos-reshape-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_RESHAPE),
        "rationale": "A structurally-different CORRECT impl: same forward copy "
                     "loops and same branch order, but each appended element is "
                     "bound to a typed local first (v=cr[i]; res.append(v)) and "
                     "the zero singleton via an intermediate (z=0; [z]). Loop "
                     "DIRECTION is unchanged (forward against cr.take(i) — a flip "
                     "would need a take/drop fold lemma, pilot bug #3) and every "
                     "gold Invariant + framing Assert is kept verbatim (pilot bug "
                     "#2). Must verify; if it cannot, the postcondition is "
                     "SPEC-TOO-STRONG. Also the cheapest-honest grounded-oracle "
                     "control: copying the grounded root set IS the correct value "
                     "(no scalar shortcut — the result must carry list_pred).",
    },
    {
        "id": "admiss-fshape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": "The Requires (a>=0, n>2, p>2, is_prime(p) OR "
                     "composite_validated) is satisfiable by every harness input "
                     "(prime moduli and the validated composite moduli 8, 9, 36, "
                     "100, 3249000). Entry Asserts re-derive the precondition "
                     "disjunction and confirm the three completeness regimes are "
                     "mutually consistent (the zero case excludes a%p!=0); the "
                     "gold proof still discharges, so the precondition admits a "
                     "normal input (else PRECOND-TOO-STRONG).",
    },
    {
        "id": "drop-zero-root",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_DROP_ZERO),
        "refinement": "This is the EXACT pre-patch sympy behaviour "
                      "(model_prepatch.py): the dispatch runs is_nthpow_residue "
                      "first and never special-cases a%p==0, so for a prime "
                      "modulus with a%p==0 the x=0 root is dropped (returns []). "
                      "That is precisely the bug the issue reports "
                      "(nthroot_mod(17*17,5,17) omitting 0). A patch shaped like "
                      "this IS the pre-patch code — it resolves nothing; the "
                      "issue's own example fails. G-DIFF: model_prepatch is "
                      "same_spec and fails exactly this postcondition.",
        "rationale": "REJECTION SOURCE = (C-zero) "
                     "Implies(is_prime(p) and a%p==0, len(Result())==1 and "
                     "Result()[0]==0). Returning [] is sound vacuously (no "
                     "elements to check) but len([])==0 != 1, so the zero-target "
                     "clause is unprovable. Soundness alone would admit this; "
                     "completeness is what rejects it.",
    },
    {
        "id": "decline-composite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_DECLINE_COMPOSITE),
        "refinement": "This is the EXACT pre-patch behaviour "
                      "(model_prepatch_1.py): a non-prime modulus is declined "
                      "(the pre-patch `raise NotImplementedError(\"Not "
                      "implemented for composite p\")`), modelled as returning []. "
                      "The sole FAIL_TO_PASS test_solve_modular reaches "
                      "nthroot_mod ONLY with composite moduli 8 and 9 (e.g. "
                      "x**3 = 1 (mod 8) -> {1}); a patch that declines composite "
                      "moduli raises/returns nothing there and FAILS the F2P. "
                      "G-DIFF: model_prepatch_1 is same_spec and fails exactly "
                      "this postcondition (the (1,3,8) guard is an enumerated "
                      "composite_validated triple, so it is not masked).",
        "rationale": "REJECTION SOURCE = (C-comp) "
                     "Implies(not is_prime(p) and composite_validated(a,n,p), "
                     "ToSeq(Result()) == composite_roots(a,n,p)). Returning [] is "
                     "sound vacuously but ToSeq([]) != composite_roots(a,n,p) "
                     "whenever the root set is non-empty (it is, on the F2P "
                     "shapes), so the composite completeness clause is unprovable.",
    },
    {
        "id": "drop-last-composite-root",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_DROP_LAST),
        "refinement": "A faithful real patch whose CRT recombination has an "
                      "off-by-one (drops the final assembled root) returns a "
                      "STRICT SUBSET of the true root set. On the F2P x**4 = 4 "
                      "(mod 9) the gold returns {4,5}; dropping the last yields "
                      "{4}, so test_solve_modular's expected solution set is wrong "
                      "and the F2P fails. Every value it DOES return is a real "
                      "root, so a soundness-only spec would wrongly accept it — "
                      "this is the canonical verify-but-not-resolve rival.",
        "rationale": "REJECTION SOURCE = (C-comp) ToSeq(Result()) == "
                     "composite_roots(a,n,p). Stopping the copy loop at "
                     "len(cr)-1 leaves ToSeq(res) == cr.take(len(cr)-1), which != "
                     "cr (== composite_roots) whenever len(cr) >= 1. SOUNDNESS "
                     "still holds (each kept element is a root), so this isolates "
                     "completeness as the load-bearing clause.",
    },
    {
        "id": "duplicate-composite-root",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_DUP_FIRST),
        "refinement": "A faithful real patch that double-counts a root (e.g. a "
                      "CRT product that revisits a prime-power residue) returns a "
                      "list with a duplicate. sympy's nthroot_mod(...,all_roots="
                      "True) returns a de-duplicated sorted list and "
                      "test_solve_modular compares the exact solution set; a "
                      "duplicated entry yields the wrong multiplicity/list and "
                      "the F2P fails. The extra entry is itself a real root, so "
                      "soundness holds — only the EXACT-sequence completeness "
                      "clause rejects it.",
        "rationale": "REJECTION SOURCE = (C-comp) ToSeq(Result()) == "
                     "composite_roots(a,n,p). After the gold loop "
                     "ToSeq(res)==cr; the spurious res.append(cr[0]) makes "
                     "ToSeq(res) == cr ++ [cr[0]], strictly longer than cr, so "
                     "the equality fails for any non-empty root set. This is the "
                     "OVER-keep side of the completeness gap (soundness holds; "
                     "the exact sequence does not).",
    },
    {
        "id": "two-zeros-prime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_TWO_ZEROS),
        "refinement": "A faithful real patch that emitted [0, 0] for the prime "
                      "zero-target case (e.g. failing to collapse the multiplicity "
                      "of x=0) would report a non-existent second solution. Over a "
                      "prime field x**n = 0 has the UNIQUE root x=0 (the field has "
                      "no zero divisors); the issue and gold both pin exactly [0]. "
                      "A [0,0] result is wrong (duplicate root) and would not "
                      "match the issue's expected single zero root.",
        "rationale": "REJECTION SOURCE = (C-zero) "
                     "Implies(is_prime(p) and a%p==0, len(Result())==1 and "
                     "Result()[0]==0). Both entries of [0,0] are genuine roots so "
                     "SOUNDNESS holds, but len([0,0])==2 != 1, so the exact "
                     "singleton clause is unprovable. This pins the zero-target "
                     "result to the EXACT singleton, not merely 'contains 0'.",
    },
]


# ===========================================================================
# AXIOM LANE — 5 @ContractOnly axioms + 2 A-reference deep solvers. Each probe
# RUNS THE REAL sympy callee inside the instance image with the gold patch
# applied (apply_gold=True), opens files utf-8, and is self-contained (no bundle
# file is mounted besides the probe). Mirrors axiom_check.py (G-AX, rc0).
# ===========================================================================

_PROBE_POWER_MOD = '''\
import random, sys
from sympy import isprime


def check_power_mod(x, n, p):
    """power_mod(x, n, p) == pow(x, n, p), plus all three model Ensures."""
    real = pow(x, n, p)
    assert 0 <= real < p, "pow out of range on (%r,%r,%r): %r" % (x, n, p, real)
    # Ensures: zero base, positive power -> 0.
    if x == 0 and n > 0:
        assert real == 0, "zero-base Ensures violated on (%r,%r,%r)" % (x, n, p)
    # Ensures: prime field has no zero divisors -> a positive power of an in-range
    # base is 0 only for the zero base.
    if isprime(p) and n > 0 and 0 <= x < p and real == 0:
        assert x == 0, (
            "prime-field zero-divisor Ensures violated: pow(%r,%r,%r)==0 but "
            "x != 0" % (x, n, p))


def main():
    checked = 0
    # boundary: moduli incl. composite F2P (8, 9, 36, 100) and primes; bases at
    # 0, 1, p-1, p, p+1, and exponents incl. n > 2 and the n=0/1/2 edges.
    for p in [2, 3, 4, 5, 8, 9, 17, 36, 37, 74, 100, 121, 1000, 3249000]:
        for x in [0, 1, 2, p - 1, p, p + 1, 2 * p + 3]:
            for n in [0, 1, 2, 3, 5, 7, 12, 31]:
                check_power_mod(x, n, p); checked += 1
                check_power_mod(x % p, n, p); checked += 1
    # fuzz over all moduli (pure modular arithmetic; the seed mirrors G-AX).
    rng = random.Random(18199)
    for _ in range(20000):
        m = rng.randint(2, 200)
        x = rng.randint(0, 2000)
        n = rng.randint(0, 40)
        check_power_mod(x, n, m); checked += 1
    print("ax-sound-power_mod OK: power_mod == pow incl. range, zero-base, and "
          "prime-field zero-divisor Ensures on %d inputs (boundary + 20000 fuzz)"
          % checked)
    return 0


sys.exit(main())
'''


_PROBE_ROOTSETS = '''\
import random, sys
from sympy.ntheory.residue_ntheory import nthroot_mod
from sympy import isprime, factorint


def real_root_set(a, n, m):
    """The REAL callee nthroot_mod(a,n,m,all_roots=True) as a set in [0,m).
    'No solution' (None or []) -> empty set. No re-filtering by any predicate."""
    res = nthroot_mod(a, n, m, all_roots=True)
    if res is None:
        return set()
    return {int(x) % m for x in res}


def brute_root_set(a, n, m):
    """Independent ground truth: residues r in [0,m) with r**n == a (mod m)."""
    amod = a % m
    return {r for r in range(m) if pow(r, n, m) == amod}


def is_squarefree(m):
    return all(e == 1 for e in factorint(m).values())


def check_root_set(a, n, m):
    """prime_roots/composite_roots == real nthroot_mod root set (both directions),
    and every returned residue is a true root (soundness)."""
    real = real_root_set(a, n, m)
    truth = brute_root_set(a, n, m)
    bad = {r for r in real if pow(r, n, m) != a % m}
    assert not bad, ("real nthroot_mod returned non-roots on x**%d = %d (mod %d): "
                     "%s" % (n, a, m, sorted(bad)))
    over = real - truth
    under = truth - real
    assert not over and not under, (
        "root-set mismatch on x**%d = %d (mod %d): real=%s truth=%s "
        "(real-only=%s, truth-only=%s)"
        % (n, a, m, sorted(real), sorted(truth), sorted(over), sorted(under)))


def main():
    # the ACTUAL test-suite inputs FIRST, unconditionally (no skip-guard; a
    # skipped F2P case would be a false pass). Both F2P moduli 8, 9 are here.
    tested_inputs = [
        (1, 3, 8), (4, 4, 9), (29, 31, 74), (16, 5, 36), (9, 16, 36),
        (4, 3, 3249000), (36010, 8, 87382), (0, 12, 37), (0, 7, 100),
        (17 * 17, 5, 17),
    ]
    for (a, n, m) in tested_inputs:
        check_root_set(a, n, m)
    # the headline issue: 0 is a solution when a%m==0 (prime modulus).
    assert 0 in real_root_set(17 * 17, 5, 17), "issue example: 0 missing"
    assert real_root_set(0, 12, 37) == {0}, "prime zero-target not {0}"

    # squarefree-regime fuzz (the regime the references are validated over).
    rng = random.Random(18199)
    checked = 0
    while checked < 4000:
        m = rng.randint(3, 120)
        if not is_squarefree(m):
            continue
        n = rng.randint(3, 18)
        a = rng.randint(0, 800)
        check_root_set(a, n, m)
        check_root_set((a // m) * m, n, m)   # a multiple of m -> zero-root path
        checked += 1
    print("ax-sound-rootsets OK: prime_roots/composite_roots == real "
          "nthroot_mod(a,n,m,all_roots=True) as a SET OF ROOTS on %d enumerated "
          "test inputs (both F2P 8,9 + zero/no-root cases) + %d squarefree fuzz, "
          "each cross-checked vs brute force, 0 violations"
          % (len(tested_inputs), checked))
    return 0


sys.exit(main())
'''


_PROBE_RESIDUE = '''\
import sys
from sympy.ntheory.residue_ntheory import is_nthpow_residue


def brute_root_set(a, n, m):
    amod = a % m
    return {r for r in range(m) if pow(r, n, m) == amod}


def check_residue_contract(a, n, p):
    """The model's is_nth_residue Ensures: a%p==0 -> a solution exists. Checked
    against BOTH the real predicate AND brute-force ground truth (root 0 exists)."""
    if a % p == 0:
        assert is_nthpow_residue(a, n, p), (
            "is_nthpow_residue(%r,%r,%r) should be True when a %% p == 0"
            % (a, n, p))
        assert 0 in brute_root_set(a, n, p), (
            "x == 0 should be a real root when a %% p == 0 (a=%r,n=%r,p=%r)"
            % (a, n, p))


def main():
    checked = 0
    for p in [2, 3, 4, 5, 8, 9, 36, 37, 74, 100, 121, 1000]:
        for n in [3, 4, 5, 7, 12]:
            check_residue_contract(0, n, p)      # a%p==0
            check_residue_contract(p, n, p)      # a multiple of p
            check_residue_contract(2 * p, n, p)
            checked += 3
    print("ax-sound-residue OK: is_nthpow_residue True AND root 0 really exists "
          "whenever a%%p==0, on %d inputs (the validated-but-dead Ensures, still "
          "a true over-approximation)" % checked)
    return 0


sys.exit(main())
'''


_PROBE_CONTAIN_COMPOSITE = '''\
import sys
from sympy.ntheory.residue_ntheory import nthroot_mod
from sympy import isprime, factorint


def real_root_set(a, n, m):
    res = nthroot_mod(a, n, m, all_roots=True)
    if res is None:
        return set()
    return {int(x) % m for x in res}


def brute_root_set(a, n, m):
    amod = a % m
    return {r for r in range(m) if pow(r, n, m) == amod}


def is_squarefree(m):
    return all(e == 1 for e in factorint(m).values())


# Mirror of model.py composite_validated: the regime nth_roots' Requires admits
# for a non-prime modulus (the ONLY composite inputs the model can reach).
ENUMERATED_NONSQFREE = {
    (1, 3, 8), (4, 4, 9), (16, 5, 36), (9, 16, 36),
    (4, 3, 3249000), (0, 7, 100),
}


def composite_validated(a, n, p):
    return is_squarefree(p) or (a, n, p) in ENUMERATED_NONSQFREE


def main():
    # CONTAINMENT: nth_roots' Requires(is_prime(p) or composite_validated(a,n,p))
    # means the ONLY non-prime inputs the model can reach are those with
    # composite_validated True. Assert the real callee is EXACT (sound AND
    # complete vs brute force) on every such reachable composite input within a
    # sampled box + the enumerated triples. A reachable input on which the
    # callee is NOT exact would be AXIOM-TOO-WEAK-FOR-CALLER.
    in_regime_checked = 0
    out_of_regime_nonroot_witnesses = 0
    for p in range(4, 80):
        if isprime(p):
            continue
        for n in range(3, 12):
            for a in range(0, p):
                in_regime = composite_validated(a, n, p)
                real = real_root_set(a, n, p)
                nonroots = {r for r in real if pow(r, n, p) != a % p}
                if in_regime:
                    # reachable by the model -> the callee MUST be exact here.
                    assert not nonroots and real == brute_root_set(a, n, p), (
                        "composite_validated admits reachable input (%r,%r,%r) "
                        "but the real callee is NOT exact there: real=%s truth=%s"
                        % (a, n, p, sorted(real), sorted(brute_root_set(a, n, p))))
                    in_regime_checked += 1
                elif nonroots:
                    # OUTSIDE the regime the gold genuinely returns non-roots:
                    # this is exactly why the composite_validated guard is
                    # LOAD-BEARING and cannot be widened to "all non-prime p".
                    out_of_regime_nonroot_witnesses += 1
    # every enumerated non-squarefree triple must be admitted (else a hole).
    for (a, n, p) in ENUMERATED_NONSQFREE:
        assert composite_validated(a, n, p), (
            "enumerated triple (%r,%r,%r) not admitted by composite_validated"
            % (a, n, p))
        real = real_root_set(a, n, p)
        truth = brute_root_set(a, n, p)
        assert real == truth, (
            "enumerated non-squarefree triple (%r,%r,%r): real=%s truth=%s"
            % (a, n, p, sorted(real), sorted(truth)))
    assert out_of_regime_nonroot_witnesses > 0, (
        "expected the gold to return non-roots on some non-squarefree modulus "
        "OUTSIDE the validated regime (the over-claim composite_validated "
        "prevents); found none -> the guard would be cosmetic, not load-bearing")
    print("ax-contain-composite OK: every model-reachable composite input "
          "(composite_validated True) is EXACT under the real callee "
          "(%d in-regime inputs + 6 enumerated triples, sound+complete vs brute "
          "force); the regime is LOAD-BEARING (%d out-of-regime non-root "
          "witnesses, so it cannot be widened)"
          % (in_regime_checked, out_of_regime_nonroot_witnesses))
    return 0


sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-power_mod",
        "axiom": "power_mod",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_POWER_MOD,
        "rationale": "Runs the REAL 3-arg pow and asserts all three model Ensures "
                     "(0<=pow<p; x==0,n>0 -> pow==0; isprime(p),n>0,0<=x<p,pow==0 "
                     "-> x==0) on boundary moduli incl. the composite F2P moduli "
                     "8,9,36,100 + 20000 fuzz. Any disagreement => AXIOM-UNSOUND. "
                     "Mirrors axiom_check.py check_power_mod.",
    },
    {
        "id": "ax-sound-rootsets",
        "axiom": "composite_roots",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_ROOTSETS,
        "rationale": "A-reference soundness+completeness for prime_roots AND "
                     "composite_roots: runs the REAL nthroot_mod(...,all_roots="
                     "True) and asserts its root set equals brute-force ground "
                     "truth (both directions) on the enumerated F2P/test inputs "
                     "(incl. composite 8,9 and the zero/no-root cases) + 4000 "
                     "squarefree fuzz. Any over-keep/under-keep => AXIOM-UNSOUND. "
                     "Validates the dispatch postconditions ToSeq(Result()) == "
                     "*_roots. Mirrors axiom_check.py check_root_set.",
    },
    {
        "id": "ax-sound-residue",
        "axiom": "is_nth_residue",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_RESIDUE,
        "rationale": "Asserts the real is_nthpow_residue returns True AND a real "
                     "root 0 exists whenever a%%p==0 (the model's single "
                     "is_nth_residue Ensures, validated-but-dead yet a true "
                     "over-approximation). Any violation => AXIOM-UNSOUND. "
                     "Mirrors axiom_check.py check_residue_contract.",
    },
    {
        "id": "ax-contain-composite",
        "axiom": "composite_roots",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAIN_COMPOSITE,
        "rationale": "Caller-domain containment for the composite A-reference: "
                     "nth_roots' Requires(is_prime(p) or composite_validated) "
                     "means the ONLY reachable composite inputs are those with "
                     "composite_validated True; asserts the real callee is EXACT "
                     "(sound+complete vs brute force) on every such reachable "
                     "input (sampled box + the 6 enumerated triples). A reachable "
                     "input on which the callee is non-exact => "
                     "AXIOM-TOO-WEAK-FOR-CALLER. Also confirms the regime is "
                     "LOAD-BEARING (gold returns non-roots OUTSIDE it, so it "
                     "cannot be widened — the directive-7/8 soundness boundary). "
                     "Mirrors axiom_check.py's regime two-way validation.",
    },
]
