# properties.py — PBT falsification battery for sympy__sympy-18698.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant built by region-surgery that edits ONLY
# inside a `# impl-start` / `# impl-end` block (so the frozen spec — axioms,
# pure helpers, pre/post-conditions, signatures — is byte-identical and
# same_spec holds). The runner stamps each with verify(host, Nagini) + same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (the spec this battery attacks)
# ---------------------------------------------------------------------------
# Two contracted+implemented functions:
#
#   occurs_in(xs: List[int], k: int) -> bool
#     READ-ONLY input: Requires/Ensures Acc(list_pred(xs), 1/2).
#     Post: Result() == occurs(ToSeq(xs), k) — value membership grounded in xs.
#
#   consolidate_by_multiplicity(factors: List[int], mults: List[int]) -> List[int]
#     READ-ONLY inputs: factors / mults each at Acc(list_pred(.), 1/2), held
#     verbatim in the Ensures; len(factors)==len(mults).
#     The result is built FRESH at full permission: Acc(list_pred(Result())).
#     The load-bearing postcondition pins BOTH dimensions of the consolidation:
#       (1) len(Result()) == len(dedup(ToSeq(mults)))           [consolidation]
#       (2) Forall j: 0<=j<len(Result()) ->
#               Result()[j] == prod_k(ToSeq(factors), ToSeq(mults),
#                                     dedup(ToSeq(mults))[j], len(mults))  [value]
#     dedup = distinct multiplicities kept once at first occurrence (a fold over
#     ToSeq(mults)); prod_k = product of EXACTLY the contributions of a given
#     multiplicity over the first n axes (a fold over ToSeq(factors)/ToSeq(mults)).
#     The DISCRIMINATING content is two-dimensional: which multiplicities are
#     reported (dimension 1) AND the merged-factor VALUE recorded for each
#     (dimension 2), which is the value the F2P test_factor_terms grades
#     (sqf_list(x*(x+y)) == (1, [(x**2 + x*y, 1)]) — the two multiplicity-1
#     factors merge to their product).
#
# Ungrounded-oracle-echo class — DOES NOT APPLY (honest positive control instead):
#   dedup and prod_k are @Pure, but they are NOT opaque answer-key oracles. Each
#   is a fully spelled-out structural fold that reads ONLY the input carriers
#   (ToSeq(mults) / ToSeq(factors)); the postcondition unfolds them. An impl that
#   "echoes" prod_k/dedup is the CORRECT gold answer (the gold phase-2 loop
#   literally constructs acc == prod_k(...) and proves Result()[j] == prod_k(...)),
#   not a cheat — there is no WRONG value to echo. The discriminating content lives
#   entirely inside dedup/prod_k, which are grounded in the inputs. So instead of a
#   wrong-echo rival we supply structurally-different CORRECT positive controls
#   (local-variable reshapes that keep the gold proof) plus the partial-domain /
#   value-corruption rivals below, each of which writes a value != prod_k(...) on a
#   subdomain and so must be rejected by dimension (2). (See assessment.)
#
# Control-flow-effect class — DOES NOT APPLY:
#   Neither function has a raise / early-return / side-effect branch. occurs_in is
#   a single total membership scan; consolidate_by_multiplicity is two total
#   forward loops producing one fresh list. The whole observable is the returned
#   value, already pinned per element by the postcondition; there is no exceptional
#   path or hidden effect a capability-token rival could discriminate. Omitted.
#
# Axiom lane — NO @ContractOnly axioms are consumed (AXIOM_TESTS still present):
#   meta.axioms == []. Both consolidation dimensions are modelled deeply (dedup,
#   prod_k) and discharged by the verified loops. The one kind-A relationship is an
#   A-REFERENCE: that integer multiplication of the distinct factor tokens
#   faithfully models the SymPy Mul monoid, so prod_k over the tokens stands for
#   reduce(operator.mul, group) over the real Exprs. The axiom probes below mirror
#   axiom_check.py / G-AX: they run the REAL operator.mul / functools.reduce (and
#   sympy when present) in the instance image to validate that A-reference and the
#   dedup==set(distinct multiplicities) correspondence. (Run as axiom-soundness /
#   axiom-containment so a violation maps to AXIOM-UNSOUND / -TOO-WEAK-FOR-CALLER.)

from pathlib import Path

INSTANCE = "sympy__sympy-18698"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# The exact gold impl-region body of consolidate_by_multiplicity (everything
# between its # impl-start and # impl-end, markers exclusive). Every
# consolidate-variant is produced by _swap on _BASE touching ONLY text inside
# this block (or, for the gold-impl swap, replacing the whole block). Kept
# verbatim so a same_spec violation is impossible and any rejection is
# attributable to the edited executable text, never to a touched contract.
# ===========================================================================
_GOLD_IMPL = """    ms = ToSeq(mults)  # type: PSeq[int]
    fs = ToSeq(factors)  # type: PSeq[int]
    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
    dmults = []  # type: List[int]
    i = 0
    while i < len(mults):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(mults), 1 / 2))
        Invariant(len(factors) == len(mults))
        Invariant(0 <= i and i <= len(mults))
        Invariant(Acc(list_pred(dmults)))
        Invariant(fs == ToSeq(factors))
        Invariant(ms == ToSeq(mults))
        Invariant(ToSeq(dmults) == dedup(ms.take(i)))
        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
        # + 1 covers the last pass, which has 0 iterations left). `mults` is
        # only read here, so len(mults) is fixed across the loop.
        Invariant(MustTerminate(len(mults) - i + 1))
        # invariants-end
        m = mults[i]  # type: int
        Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
        Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
        if not present:
            dmults = dmults + [m]
        i = i + 1
    Assert(ms.take(len(mults)) == ms)
    Assert(ToSeq(dmults) == dedup(ms))

    # Phase 2: the merged factor of each reported multiplicity is the product of
    # exactly the contributions of that multiplicity (mirrors the gold's
    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
    out = []  # type: List[int]
    p = 0
    while p < len(dmults):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(mults), 1 / 2))
        Invariant(len(factors) == len(mults))
        Invariant(Acc(list_pred(dmults), 1 / 2))
        Invariant(fs == ToSeq(factors))
        Invariant(ms == ToSeq(mults))
        Invariant(ToSeq(dmults) == dedup(ms))
        Invariant(0 <= p and p <= len(dmults))
        Invariant(Acc(list_pred(out)))
        Invariant(len(out) == p)
        Invariant(Forall(int, lambda j: (
            Implies(0 <= j and j < p,
                    ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
        # exactly one per pass and the guard keeps p < len(dmults), so
        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
        # counter `n`, which is reset to 0 on every outer pass and so does not
        # descend across passes.
        Invariant(MustTerminate(len(dmults) - p + 1))
        # invariants-end
        kk = dmults[p]  # type: int
        # inner product over exactly the group of multiplicity kk
        acc = 1
        n = 0
        while n < len(mults):
            # invariants-start
            Invariant(Acc(list_pred(factors), 1 / 2))
            Invariant(Acc(list_pred(mults), 1 / 2))
            Invariant(len(factors) == len(mults))
            Invariant(fs == ToSeq(factors))
            Invariant(ms == ToSeq(mults))
            Invariant(0 <= n and n <= len(mults))
            Invariant(acc == prod_k(fs, ms, kk, n))
            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
            # to 0 just before this loop and rises by exactly one per pass, and
            # the guard keeps n < len(mults), so len(mults) - n strictly falls
            # and stays >= 1. The bound is the contribution count, which does not
            # depend on the outer counter `p` (every group is scanned over the
            # whole contribution sequence), so nothing about `p` is needed here.
            Invariant(MustTerminate(len(mults) - n + 1))
            # invariants-end
            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
            if mults[n] == kk:
                acc = acc * factors[n]
            n = n + 1
        Assert(acc == prod_k(fs, ms, kk, len(mults)))
        out = out + [acc]
        p = p + 1
    Assert(len(out) == len(dmults))
    Assert(len(dmults) == len(dedup(ms)))
    return out
"""

# Sanity: the gold impl text must appear verbatim and uniquely in _BASE.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drift — re-sync _GOLD_IMPL"


# ---------------------------------------------------------------------------
# Sub-blocks the rivals perturb. Each is unique inside _GOLD_IMPL; the framing
# invariants/asserts AROUND a perturbed block are kept verbatim so a rejection is
# attributable to the changed value (Result()[j] != prod_k / len != dedup) or to
# the permission system, never to a deleted proof obligation.
# ---------------------------------------------------------------------------

# The whole phase-2 accumulation+append block (the `acc` local lives only here).
_PHASE2_ACC_BLOCK = """        acc = 1
        n = 0
        while n < len(mults):
            # invariants-start
            Invariant(Acc(list_pred(factors), 1 / 2))
            Invariant(Acc(list_pred(mults), 1 / 2))
            Invariant(len(factors) == len(mults))
            Invariant(fs == ToSeq(factors))
            Invariant(ms == ToSeq(mults))
            Invariant(0 <= n and n <= len(mults))
            Invariant(acc == prod_k(fs, ms, kk, n))
            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
            # to 0 just before this loop and rises by exactly one per pass, and
            # the guard keeps n < len(mults), so len(mults) - n strictly falls
            # and stays >= 1. The bound is the contribution count, which does not
            # depend on the outer counter `p` (every group is scanned over the
            # whole contribution sequence), so nothing about `p` is needed here.
            Invariant(MustTerminate(len(mults) - n + 1))
            # invariants-end
            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
            if mults[n] == kk:
                acc = acc * factors[n]
            n = n + 1
        Assert(acc == prod_k(fs, ms, kk, len(mults)))
        out = out + [acc]"""

# The single executable line that writes the merged factor of group p to out.
_APPEND_PRODUCT = "        out = out + [acc]\n"

# The inner accumulation step (extends the running product by factors[n]).
_INNER_STEP = "            if mults[n] == kk:\n                acc = acc * factors[n]\n"

# The opening of the impl body (where a frame-write would be inserted).
_IMPL_HEAD = ("    ms = ToSeq(mults)  # type: PSeq[int]\n"
              "    fs = ToSeq(factors)  # type: PSeq[int]\n")


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
#    Pure LOCAL-VARIABLE reshape: rename the inner accumulator `acc` to
#    `prodacc` consistently (declaration, the inner-loop invariant, the
#    accumulation step, the post-loop Assert, and the append). A faithful
#    behaviour-preserving rename: it keeps the FORWARD phase-2 loop, the
#    prefix-recursive prod_k pairing, the lemma_prod_unfold trigger, and every
#    gold framing invariant/assert (only the local's name changes), so the gold
#    proof obligations discharge unchanged. MUST verify — else SPEC-TOO-STRONG.
_POS1_BLOCK = """        prodacc = 1
        n = 0
        while n < len(mults):
            # invariants-start
            Invariant(Acc(list_pred(factors), 1 / 2))
            Invariant(Acc(list_pred(mults), 1 / 2))
            Invariant(len(factors) == len(mults))
            Invariant(fs == ToSeq(factors))
            Invariant(ms == ToSeq(mults))
            Invariant(0 <= n and n <= len(mults))
            Invariant(prodacc == prod_k(fs, ms, kk, n))
            # PHASE-2 INNER measure, unchanged by the rename: `n` is reset to 0
            # before this loop and rises by one per pass under the guard
            # n < len(mults), so len(mults) - n strictly falls and stays >= 1.
            Invariant(MustTerminate(len(mults) - n + 1))
            # invariants-end
            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
            if mults[n] == kk:
                prodacc = prodacc * factors[n]
            n = n + 1
        Assert(prodacc == prod_k(fs, ms, kk, len(mults)))
        out = out + [prodacc]"""
_POS1_IMPL = _swap(_GOLD_IMPL, _PHASE2_ACC_BLOCK, _POS1_BLOCK)


# ===========================================================================
# 2. POSITIVE CONTROL #2 (soundness) — a DIFFERENT local reshape: swap the order
#    of the two terminal book-keeping asserts (len(out)==len(dmults) and
#    len(dmults)==len(dedup(ms))). They are independent, side-effect-free facts
#    already established by the phase-2 invariant + the phase-1 closing assert, so
#    asserting them in the opposite order is a faithful structural variant that
#    keeps every other obligation verbatim. MUST verify — else SPEC-TOO-STRONG.
_POS2_IMPL = _swap(
    _GOLD_IMPL,
    "    Assert(len(out) == len(dmults))\n    Assert(len(dmults) == len(dedup(ms)))\n    return out\n",
    "    Assert(len(dmults) == len(dedup(ms)))\n    Assert(len(out) == len(dmults))\n    return out\n",
)


# ===========================================================================
# 3. ADMISSIBILITY — the precondition must ACCEPT a normal F2P-shaped input. The
#    Requires is permission (Acc(list_pred,1/2) on each of factors/mults) + the
#    length match len(factors)==len(mults). The F2P witness is sqf_list(x*(x+y)):
#    two contributions [x_token, xy_token] / mults [1, 1] — equal length, in-
#    domain. Keep the full gold impl and add at the TOP of impl derivable
#    assertions confirming the precondition facts the model relies on are
#    establishable: a 1/4 read share is obtainable from the 1/2 held on each
#    input, and the length match holds. If this fails to verify => PRECOND-TOO-
#    STRONG (the precondition would be rejecting a normal sqf contribution list).
_ADMISS_IMPL = (
    "    Assert(Acc(list_pred(factors), 1 / 4))\n"
    "    Assert(Acc(list_pred(mults), 1 / 4))\n"
    "    Assert(len(factors) == len(mults))\n"
) + _GOLD_IMPL


# ===========================================================================
# 4. FRAME-MUTATION on `factors` (MANDATORY — read-only input). A rival that
#    WRITES into the read-only input `factors` before the loops. factors holds
#    only Acc(list_pred(factors), 1/2); the assignment factors[0] = 0 needs FULL
#    permission and MUST be rejected for insufficient permission. Every gold
#    invariant/assert is kept verbatim so the rejection is attributable to the
#    WRITE, not a proof gap. expect=reject.
_FRAME_FACTORS_IMPL = _swap(
    _GOLD_IMPL,
    _IMPL_HEAD,
    _IMPL_HEAD + "    if len(factors) > 0:\n        factors[0] = 0\n",
)


# ===========================================================================
# 5. FRAME-MUTATION on `mults` (read-only input). Symmetric to #4 but writes the
#    other read-only carrier: mults[0] = 0. mults holds only
#    Acc(list_pred(mults), 1/2); the write needs full permission and MUST be
#    rejected. Gold invariants/asserts kept verbatim. expect=reject.
_FRAME_MULTS_IMPL = _swap(
    _GOLD_IMPL,
    _IMPL_HEAD,
    _IMPL_HEAD + "    if len(mults) > 0:\n        mults[0] = 0\n",
)


# ===========================================================================
# 6. VALUE — record the MULTIPLICITY instead of the group product. The phase-2
#    loop still computes acc == prod_k(...) (every gold invariant/assert kept
#    verbatim, so acc is provably the correct product), but the appended value is
#    `kk` (the multiplicity) instead of `acc`. The merged factor recorded for
#    group p is then the exponent, not the product of the group. expect=reject.
_VAL_MULT_IMPL = _swap(_GOLD_IMPL, _APPEND_PRODUCT, "        out = out + [kk]\n")


# ===========================================================================
# 7. VALUE — off-by-product near-miss. Append acc + 1 instead of acc: the merged
#    factor is the correct group product shifted by one. Correct nowhere (the
#    product is never equal to product+1), so it fails the prod_k postcondition on
#    every reported multiplicity. Every gold invariant/assert kept verbatim, so
#    the rejection is attributable to the value, not a proof gap. expect=reject.
_VAL_OFFBY_IMPL = _swap(_GOLD_IMPL, _APPEND_PRODUCT, "        out = out + [acc + 1]\n")


# ===========================================================================
# 8. PARTIAL-DOMAIN (drop a group member) — the inner accumulation skips one
#    contribution of the group: it multiplies factors[n] only when mults[n]==kk
#    AND n > 0, so a multiplicity-kk contribution at axis 0 is dropped from the
#    product. The inner-loop invariant acc == prod_k(...) is kept verbatim, so the
#    loop fails to re-establish it whenever the first axis belongs to a group
#    (i.e. acc diverges from prod_k by exactly the dropped factor). expect=reject.
#    A genuine product-corruption rooted in prod_k.
_DROP_MEMBER_IMPL = _swap(
    _GOLD_IMPL,
    _INNER_STEP,
    "            if mults[n] == kk and n > 0:\n                acc = acc * factors[n]\n",
)


# ===========================================================================
# 9. PARTIAL-DOMAIN / PREPATCH — NO CONSOLIDATION (== model_prepatch.py shape).
#    Replace the whole gold impl with the pre-fix skeleton: copy EVERY
#    contribution into out (one entry per contribution, each the lone factor), no
#    dedup-by-multiplicity and no per-group product. len(out)==len(factors), so it
#    fails dimension (1) len(Result())==len(dedup(mults)) whenever a multiplicity
#    repeats, and dimension (2) prod_k whenever a group has >1 member. This is the
#    exact reported bug. expect=reject.
_PREPATCH_IMPL = """    ms = ToSeq(mults)  # type: PSeq[int]
    fs = ToSeq(factors)  # type: PSeq[int]
    out = []  # type: List[int]
    i = 0
    while i < len(factors):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(mults), 1 / 2))
        Invariant(len(factors) == len(mults))
        Invariant(0 <= i and i <= len(factors))
        Invariant(Acc(list_pred(out)))
        Invariant(fs == ToSeq(factors))
        Invariant(ms == ToSeq(mults))
        Invariant(ToSeq(out) == fs.take(i))
        # This loop consumes the caller's obligation on the strictly decreasing,
        # bounded-below measure len(factors) - i: `i` rises by exactly one per
        # pass and the guard keeps i < len(factors), so the remaining-iteration
        # bound falls by one and stays >= 1 (`factors` is only read, so
        # len(factors) is fixed across the loop).
        Invariant(MustTerminate(len(factors) - i + 1))
        # invariants-end
        f = factors[i]  # type: int
        Assert(fs.take(i + 1) == fs.take(i) + PSeq(f))
        out = out + [f]
        i = i + 1
    Assert(fs.take(len(factors)) == fs)
    return out
"""


# ===========================================================================
# 10. FRAME-MUTATION on `occurs_in`'s read-only input `xs`. occurs_in holds only
#     Acc(list_pred(xs), 1/2); a write xs[0] = k before the scan needs FULL
#     permission and MUST be rejected for insufficient permission. The gold
#     occurs_in invariants/asserts are kept verbatim. This guards the SECOND
#     function's read-only frame. expect=reject.
_OCCURS_GOLD_IMPL = """    n = len(xs)
    found = False
    j = n
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(0 <= j and j <= n and n == len(xs))
        Invariant(found == occurs(ToSeq(xs).drop(j), k))
        # This down-counting scan consumes the caller's obligation on the
        # strictly decreasing, bounded-below measure `j`: `j` falls by exactly
        # one per pass and the guard keeps j > 0, so the remaining-iteration
        # bound j + 1 falls by one and stays >= 1 (the + 1 matters -- the last
        # pass has 0 iterations left and MustTerminate(0) is unsatisfiable).
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(xs).drop(j - 1) == PSeq(ToSeq(xs)[j - 1]) + ToSeq(xs).drop(j))
        if xs[j - 1] == k:
            found = True
        j = j - 1
    Assert(ToSeq(xs).drop(0) == ToSeq(xs))
    return found
"""
assert _BASE.count(_OCCURS_GOLD_IMPL) == 1, "occurs_in gold impl drift — re-sync"
_OCCURS_FRAME_IMPL = _swap(
    _OCCURS_GOLD_IMPL,
    "    n = len(xs)\n    found = False\n",
    "    n = len(xs)\n    if n > 0:\n        xs[0] = k\n    found = False\n",
)


SPEC_TESTS = [
    {
        "id": "pos-control-rename-acc",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS1_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: a pure local-variable "
            "rename of the inner accumulator acc -> prodacc (declaration, the "
            "inner-loop invariant prodacc==prod_k(...), the accumulation step, "
            "the post-loop Assert, and the append). Keeps the forward phase-2 "
            "loop, the prefix-recursive prod_k pairing, the lemma_prod_unfold "
            "trigger, and every gold framing invariant/assert; only the local's "
            "name changes. Must verify; if it cannot, the postcondition is "
            "SPEC-TOO-STRONG (rejecting a faithful rename)."
        ),
    },
    {
        "id": "pos-control-reorder-tail-asserts",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS2_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: the two terminal "
            "book-keeping asserts (len(out)==len(dmults) and "
            "len(dmults)==len(dedup(ms))) are independent side-effect-free facts "
            "already established by the phase-2 invariant + the phase-1 closing "
            "assert; asserting them in the opposite order is a faithful reshape "
            "that keeps every other obligation verbatim. Must verify; if it "
            "cannot, SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
        "rationale": (
            "the precondition is permission (Acc(list_pred,1/2) on factors and "
            "mults) + len(factors)==len(mults). The F2P witness sqf_list(x*(x+y)) "
            "is two contributions of equal length — in-domain. Added top-of-impl "
            "assertions confirm a 1/4 read share is derivable from the 1/2 held "
            "on each input and the length match holds. Must verify; if it cannot, "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutate-readonly-factors",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_FACTORS_IMPL),
        "refinement": (
            "the gold patch builds a FRESH list "
            "[(reduce(mul, (f for f, _ in factors if _ == k)), k) for k in "
            "set(...)] — it only READS the local `factors` pair list and never "
            "writes into it. A faithful patch cannot mutate the source factor "
            "list. One that zeroed factors[0] before consolidating would corrupt "
            "the first contribution's factor: on sqf_list(x*(x+y)) the x token "
            "would become 0, so the merged multiplicity-1 factor would be "
            "0*(x+y)=0 instead of x*(x+y)=x**2+x*y; sqf_list would not equal "
            "(1, [(x**2 + x*y, 1)]) — F2P test_factor_terms FAILS. A verifying "
            "mutator is a true verify-not-resolve break."
        ),
        "rationale": (
            "REJECT must come from the PERMISSION SYSTEM: factors holds only "
            "Acc(list_pred(factors), 1/2); the write factors[0]=0 needs full "
            "permission and is rejected for insufficient permission. Every gold "
            "invariant/assert is kept verbatim so the failure is attributable to "
            "the write, not a proof gap. If it verifies, the read-only frame on "
            "factors is unguarded (FRAME-MUTATION SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "frame-mutate-readonly-mults",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MULTS_IMPL),
        "refinement": (
            "the gold patch reads the multiplicities `k` (the `_` / `i` of the "
            "comprehension) but never reassigns them on the source list. A patch "
            "that zeroed mults[0] would change which multiplicity the first "
            "contribution carries: on sqf_list(x*(x+y)) (mults [1,1]) it would "
            "become [0,1], splitting the single multiplicity-1 group into a "
            "multiplicity-0 group (x) and a multiplicity-1 group (x+y) — two "
            "reported entries instead of the merged (x**2+x*y, 1); F2P "
            "test_factor_terms FAILS. A verifying mutator is a true "
            "verify-not-resolve break."
        ),
        "rationale": (
            "REJECT must come from the PERMISSION SYSTEM: mults holds only "
            "Acc(list_pred(mults), 1/2); the write mults[0]=0 needs full "
            "permission and is rejected for insufficient permission. Gold "
            "invariants/asserts kept verbatim so the failure is attributable to "
            "the write. If it verifies, the read-only frame on mults is unguarded "
            "(FRAME-MUTATION SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "value-record-multiplicity-not-product",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _VAL_MULT_IMPL),
        "refinement": (
            "records the multiplicity kk as the merged factor instead of the "
            "group product. A patch returning [(k, k) for k in set(...)] (the "
            "exponent in the factor slot) would make sqf_list(x*(x+y)) return "
            "(1, [(1, 1)]) — the literal multiplicity 1 in the factor position — "
            "not (1, [(x**2 + x*y, 1)]); F2P test_factor_terms FAILS. A faithful "
            "patch that put the multiplicity where the product belongs would not "
            "resolve."
        ),
        "rationale": (
            "REJECT comes from postcondition dimension (2) Result()[j] == "
            "prod_k(...): the appended value kk equals the multiplicity, but "
            "prod_k(...) is the group product (acc, still provably correct via "
            "the kept inner-loop invariant). The outer invariant "
            "ToSeq(out)[j]==prod_k(...) and the postcondition fail at the append "
            "whenever the group product != its multiplicity. If it verifies, the "
            "merged-factor value is unpinned (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "value-offby-product",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _VAL_OFFBY_IMPL),
        "refinement": (
            "off-by-one in the merged factor: records acc+1 (group product + 1) "
            "instead of the product. A patch that returned the group product plus "
            "one in the factor slot would make sqf_list(x*(x+y)) report "
            "(x**2 + x*y) + 1 instead of x**2 + x*y; sqf_list != "
            "(1, [(x**2 + x*y, 1)]); F2P test_factor_terms FAILS. A real "
            "off-by-one in the merged factor would not resolve."
        ),
        "rationale": (
            "REJECT comes from postcondition dimension (2) Result()[j] == "
            "prod_k(...): acc is provably the group product (kept inner-loop "
            "invariant), so acc+1 != prod_k(...) for every reported multiplicity; "
            "the outer invariant / postcondition fails at the append. If it "
            "verifies, the merged-factor value is unpinned to within +/-1 "
            "(SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-drop-group-member",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DROP_MEMBER_IMPL),
        "refinement": (
            "the per-group product drops the contribution at axis 0 (multiplies "
            "factors[n] only when mults[n]==kk AND n>0). A patch whose group "
            "product skipped the first contribution would, on sqf_list(x*(x+y)) "
            "(both at multiplicity 1, x at axis 0), drop the x token from the "
            "product and report just (x+y, 1) instead of the merged "
            "(x**2 + x*y, 1); F2P test_factor_terms FAILS. A faithful patch that "
            "omitted a group member from reduce(mul, group) would not resolve."
        ),
        "rationale": (
            "REJECT comes from dimension (2) via prod_k: the inner-loop invariant "
            "acc==prod_k(fs,ms,kk,n) is kept verbatim, but the n>0 guard drops a "
            "multiplicity-kk factor at axis 0, so the loop cannot re-establish "
            "acc==prod_k(...) once a group has a member at axis 0 (acc diverges "
            "from the fold by exactly the dropped factor). If it verifies, prod_k "
            "does not pin the WHOLE group (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "prepatch-no-consolidation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PREPATCH_IMPL),
        "refinement": (
            "the LITERAL pre-fix behaviour (== model_prepatch.py): copy every "
            "(factor, multiplicity) contribution as its own entry, no "
            "consolidation. This is exactly the reported bug — sqf_list(x*(x+y)) "
            "returned the un-merged (1, [(x, 1), (x + y, 1)]) (two multiplicity-1 "
            "entries) instead of (1, [(x**2 + x*y, 1)]), and "
            "sqf_list((x**2+1)(x-1)^2(x-2)^3(x-3)^3) returned two multiplicity-3 "
            "entries. F2P test_factor_terms FAILS. The canonical "
            "verify-not-resolve rival."
        ),
        "rationale": (
            "REJECT comes from BOTH postcondition dimensions: len(out) == "
            "len(factors) != len(dedup(ToSeq(mults))) whenever a multiplicity "
            "repeats (dimension 1 fails), and each kept entry is the lone factor, "
            "not prod_k(...) of its group (dimension 2 fails). If it verifies, the "
            "spec does not pin the consolidation (SPEC-TOO-WEAK). Shares the "
            "frozen spec byte-identically with model_prepatch.py (G-DIFF)."
        ),
    },
    {
        "id": "frame-mutate-readonly-occurs-xs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _OCCURS_GOLD_IMPL, _OCCURS_FRAME_IMPL),
        "refinement": (
            "occurs_in is a read-only membership scan mirroring `v not in seen`; "
            "the gold de-duplication never writes into the list it scans. A "
            "helper that wrote xs[0]=k before scanning would always report "
            "membership (found==True) regardless of the real contents — the "
            "phase-1 dedup would then keep NO new distinct multiplicity after the "
            "first, collapsing the reported list; the downstream consolidation "
            "would be wrong and F2P test_factor_terms FAILS. A faithful membership "
            "helper cannot mutate its argument."
        ),
        "rationale": (
            "REJECT must come from the PERMISSION SYSTEM: occurs_in holds only "
            "Acc(list_pred(xs), 1/2); the write xs[0]=k needs full permission and "
            "is rejected for insufficient permission. The gold occurs_in "
            "invariants/asserts are kept verbatim so the failure is attributable "
            "to the write. Guards the SECOND function's read-only frame; if it "
            "verifies, occurs_in's frame is unguarded (FRAME-MUTATION "
            "SPEC-TOO-WEAK)."
        ),
    },
]


# ===========================================================================
# AXIOM lane — no @ContractOnly axioms are consumed (meta.axioms == []); the one
# kind-A relationship is an A-REFERENCE (the token-* monoid faithfully models the
# SymPy Mul monoid, so prod_k over the integer tokens stands for
# reduce(operator.mul, group) over the real Exprs). These probes mirror
# axiom_check.py / G-AX and run the REAL operator.mul / functools.reduce (and
# sympy when present) in the instance image:
#
#   ax-product-monoid-soundness (axiom-soundness): for every multiplicity k the
#     real patch comprehension's merged factor equals reduce(operator.mul,
#     [the group of multiplicity k], in contribution order), and the product is
#     order-independent (commutative/associative) — symbolically over the issue's
#     own sympy examples when sympy imports, and structurally over integer-token
#     groups otherwise. If the real product != the per-group fold prod_k models,
#     the A-reference is UNSOUND.
#
#   ax-dedup-distinct-containment (axiom-containment): the model's reported
#     multiplicities (dedup, keep-first) are EXACTLY the distinct contribution
#     multiplicities the real comprehension reports (set(i for _, i in factors)),
#     each once — so every multiplicity the model can reach is inside the
#     distinct-keying the real callee performs (nothing dropped/added). A
#     reachable multiplicity the dedup model could not account for would be
#     AXIOM-TOO-WEAK-FOR-CALLER.
#
# Both probes import ONLY the stdlib callees the patch uses (operator, functools,
# random) plus an OPTIONAL sympy leg (skipped if absent); they open nothing on
# disk and exit 0 iff the obligation holds. (The runner mounts ONLY the probe
# script in the instance image, so the probes are self-contained.)

_PRODUCT_MONOID_SOUNDNESS_PROBE = r'''
import operator
import random
import sys
from functools import reduce


def real_post_loop(factors_pairs):
    """Re-execution of the gold patch's `method == 'sqf'` post-processing:
        factors = [(reduce(mul, (f for f, _ in factors if _ == k)), k)
                   for k in set(i for _, i in factors)]
    `mul` is the real operator.mul, exactly as the patch imports it."""
    mul = operator.mul
    return [(reduce(mul, (f for f, _ in factors_pairs if _ == k)), k)
            for k in set(i for _, i in factors_pairs)]


def check_merged_factor_is_group_product(factors_pairs):
    real = dict((k, f) for f, k in real_post_loop(factors_pairs))
    for k in set(m for _, m in factors_pairs):
        group = [f for f, m in factors_pairs if m == k]
        if not group:
            print("AXIOM-UNSOUND: empty group for present multiplicity %r" % (k,))
            sys.exit(1)
        expected = reduce(operator.mul, group)   # prod_k models exactly this
        if real[k] != expected:
            print("AXIOM-UNSOUND: merged factor for mult %r on %r: real=%r, "
                  "product of group %r = %r" % (k, factors_pairs, real[k], group, expected))
            sys.exit(1)
    if len(real) != len(set(m for _, m in factors_pairs)):
        print("AXIOM-UNSOUND: not one entry per multiplicity on %r" % (factors_pairs,))
        sys.exit(1)


def check_product_assoc_comm(group):
    if not group:
        return
    base = reduce(operator.mul, group)
    rng = random.Random(hash(tuple(group)) & 0xFFFF)
    for _ in range(8):
        perm = list(group)
        rng.shuffle(perm)
        if reduce(operator.mul, perm) != base:
            print("AXIOM-UNSOUND: product not order-independent on %r (perm %r)"
                  % (group, perm))
            sys.exit(1)


def try_symbolic():
    try:
        import sympy
        from sympy.abc import x, y
    except Exception:
        return -1
    cases = [
        [(x - 1, 2), (x - 3, 3), (x - 2, 3), (x ** 2 + 1, 1)],   # the issue example
        [(x, 1), (x + y, 1)],                                    # x*(x+y) -> x**2+x*y
        [(x - 2, 1), (x ** 2 - 1, 2)],                           # singletons untouched
        [(x, 2), (x + 1, 2), (x + 2, 2)],                        # three sharing a mult
    ]
    checked = 0
    for pairs in cases:
        real = dict((k, f) for f, k in real_post_loop(pairs))
        for k in set(m for _, m in pairs):
            group = [f for f, m in pairs if m == k]
            expected = reduce(operator.mul, group)
            if sympy.expand(real[k] - expected) != 0:
                print("AXIOM-UNSOUND (symbolic): mult %r: %r vs %r"
                      % (k, real[k], expected))
                sys.exit(1)
            checked += 1
    return checked


# boundary integer-token groups (distinct primes -> faithful commutative monoid)
boundary_pairs = [
    [(2, 1)],
    [(2, 1), (3, 1)],                 # both mult 1 -> merge to 6
    [(2, 3), (3, 3)],                 # the bug's case: both mult 3 -> 6
    [(2, 1), (3, 2), (5, 3)],         # all distinct mults -> untouched
    [(2, 2), (3, 2), (5, 2)],         # three at mult 2 -> 30
    [(2, 1), (3, 1), (5, 2), (7, 2)],
    [(11, 5), (13, 5), (17, 5), (19, 1)],
]
for pairs in boundary_pairs:
    check_merged_factor_is_group_product(pairs)
    for k in set(m for _, m in pairs):
        check_product_assoc_comm([f for f, m in pairs if m == k])

primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
rng = random.Random(18698)
for _ in range(20000):
    n = rng.randint(0, 8)
    mults = [rng.randint(1, 5) for _ in range(n)]
    tokens = (rng.sample(primes, n) if n <= len(primes)
              else [primes[i % len(primes)] for i in range(n)])
    pairs = list(zip(tokens, mults))
    if pairs:
        check_merged_factor_is_group_product(pairs)
        for k in set(m for _, m in pairs):
            check_product_assoc_comm([f for f, m in pairs if m == k])

sym = try_symbolic()
print("AXIOM-SOUND: real reduce(operator.mul, group) == per-group product (prod_k) "
      "and order-independent over %d boundary + 20000 fuzz cases%s"
      % (len(boundary_pairs),
         ("" if sym < 0 else " + %d symbolic sympy obligations" % sym)))
sys.exit(0)
'''


_DEDUP_CONTAINMENT_PROBE = r'''
import operator
import random
import sys
from functools import reduce


def dedup(seq):
    """Reference of model.py dedup: distinct values, kept at first occurrence."""
    out = []
    for v in seq:
        if v not in out:
            out.append(v)
    return out


def real_distinct_multiplicities(factors_pairs):
    """The distinct multiplicities the gold comprehension keys on:
        for k in set(i for _, i in factors)."""
    return set(i for _, i in factors_pairs)


def check_containment(mults):
    """Every multiplicity the model's dedup reports is exactly one the real
    callee's set(...) keying reports, and vice versa (no value the model can
    reach lies outside the distinct-keying the real comprehension performs)."""
    model_reported = dedup(mults)
    # distinctness (each kept once)
    if len(model_reported) != len(set(model_reported)):
        print("AXIOM-TOO-WEAK-FOR-CALLER: model dedup not distinct on %r: %r"
              % (mults, model_reported))
        sys.exit(1)
    pairs = [(1, m) for m in mults]   # tokens irrelevant to the keying
    real_keys = real_distinct_multiplicities(pairs)
    if set(model_reported) != real_keys:
        print("AXIOM-TOO-WEAK-FOR-CALLER: model-reachable multiplicities %r != "
              "real comprehension keys %r on %r"
              % (sorted(set(model_reported)), sorted(real_keys), mults))
        sys.exit(1)


boundary_mults = [
    [],
    [1],
    [1, 1],                       # duplicate -> one reported entry
    [3, 3],                       # the bug's case
    [1, 2, 3],
    [2, 1, 2],                    # first-occurrence order
    [1, 2, 1, 2, 1],
    [3, 3, 3, 3],
    [5, 4, 3, 2, 1],
    [1, 1, 2, 2, 3, 3],
]
for mults in boundary_mults:
    check_containment(mults)

rng = random.Random(186980)
for _ in range(20000):
    n = rng.randint(0, 8)
    mults = [rng.randint(1, 6) for _ in range(n)]
    check_containment(mults)

print("AXIOM-COVERED: model dedup (keep-first distinct multiplicities) == the real "
      "set(i for _, i in factors) keying over %d boundary + 20000 fuzz mult lists; "
      "every model-reachable multiplicity is inside the real distinct-keying"
      % len(boundary_mults))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-product-monoid-soundness",
        "axiom": "factor-token product monoid (token * <-> reduce(operator.mul, group))",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PRODUCT_MONOID_SOUNDNESS_PROBE,
        "rationale": (
            "the A-reference: prod_k over the integer factor tokens faithfully "
            "models reduce(operator.mul, group) over the real Exprs. Runs the REAL "
            "operator.mul / functools.reduce (the very callees the patch imports) "
            "and asserts, on boundary + 20000 fuzz integer-token groups (and "
            "symbolically on the issue's own sympy examples when sympy imports), "
            "that the merged factor for each multiplicity k equals the product of "
            "EXACTLY that group, and that the product is order-independent "
            "(commutative/associative monoid). If the real product != the per-group "
            "fold prod_k models, the A-reference is AXIOM-UNSOUND. Mirrors "
            "axiom_check.py's merged-factor + assoc/comm checks."
        ),
    },
    {
        "id": "ax-dedup-distinct-containment",
        "axiom": "dedup (reported multiplicities) vs set(i for _, i in factors)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _DEDUP_CONTAINMENT_PROBE,
        "rationale": (
            "containment of the reported-multiplicities dimension: the model's "
            "dedup (keep-first distinct multiplicities) must be EXACTLY the "
            "distinct multiplicities the real comprehension keys on "
            "(set(i for _, i in factors)) — each once, nothing dropped or added. "
            "Runs over boundary + 20000 fuzz multiplicity lists; every "
            "model-reachable multiplicity lies inside the real distinct-keying. A "
            "reachable multiplicity the dedup model could not account for would be "
            "AXIOM-TOO-WEAK-FOR-CALLER. Mirrors axiom_check.py's "
            "check_reported_multiplicities."
        ),
    },
]
