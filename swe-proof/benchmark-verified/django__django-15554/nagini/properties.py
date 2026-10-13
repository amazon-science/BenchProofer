# properties.py — PBT falsification battery for django__django-15554.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the single `# impl-start` .. `# impl-end` body of the lone modeled function
# (install_join) and leave the frozen spec (axioms / pure / pre / post-conditions
# / signatures) byte-identical. The nested `# invariants-*` block lives INSIDE
# the impl region, so rewriting it is still inside-impl surgery — spec_view elides
# the whole impl region (markers + nested invariants included), so same_spec is
# guaranteed for every case.
#
# ── Defended surface (read from model.py / refinement.md / mapping.md / instance.json)
# Modeled fn: install_join(base, frel, reuse_all, reuse_mask, jb, jf, constrained)
#   models Query.join's alias-reuse decision (query.py:1014). It returns True iff
#   a FRESH alias must be created (no reuse-eligible existing slot matches).
#
# Load-bearing postcondition (the single observable this bundle pins):
#   (O) Result() == no_eligible_match(base, frel, reuse_all, reuse_mask, jb, jf, constrained)
# plus the frame guards:
#   (F1) ToSeq(base) == Old(ToSeq(base))      registry base array read-only
#   (F2) ToSeq(frel) == Old(ToSeq(frel))      registry refinement array read-only
#   (F3) Acc(list_pred(base|frel|reuse_mask), 1/2) returned (read-only inputs)
#   (L)  len(base)==len(frel)==len(reuse_mask) preserved.
#
# no_eligible_match is a @Pure helper (NOT a @ContractOnly answer-key). It is a
# Forall over the ACTUAL input slots calling reusable / matches_default /
# matches_constrained — every term grounded in the args. So there is NO opaque
# oracle to echo wrongly: returning no_eligible_match(...) IS doing the real work
# (the cheapest-honest positive control), and the genuine attacks are PARTIAL-
# DOMAIN divergences in *which* slots count and *how* a match is decided.
#
# The discriminating delta (refinement.md §A, A4): in the DEFAULT branch the
# patch matches on the FULL identity (base AND refinement tag, matches_default),
# where the pre-patch used base-only (matches_constrained). With two same-base
# distinct-refinement descriptors under default reuse, the second must create a
# fresh alias; base-only matching would wrongly merge them (F2P test_multiple).
#
# ── Read-only inputs: base, frel, reuse_mask are ALL held at Acc(..., 1/2).
# A 1/2 permission cannot be written. FRAME-MUTATION is therefore MANDATORY and a
# write to any of them must be REJECTED for INSUFFICIENT PERMISSION (frame-mut-*).
from pathlib import Path

INSTANCE = "django__django-15554"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ── The single whole-impl anchor (lines 130-172 between # impl-start/# impl-end).
# Reproduced VERBATIM, including the nested invariants block, so the swap stays
# strictly inside the one function's impl region. The full invariant set is the
# gold proof scaffold; positive controls keep it verbatim, divergent rivals keep
# the gold *postcondition* the spec defends and need only the framing invariants
# (F1/F2/L + bounds) the verifier requires to discharge it.
_IMPL = """    n = len(base)
    found = False
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(frel), 1 / 2))
        Invariant(Acc(list_pred(reuse_mask), 1 / 2))
        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)
        Invariant(0 <= i and i <= n)
        Invariant(Implies(constrained, not reuse_all))
        Invariant(ToSeq(base) == Old(ToSeq(base)))
        Invariant(ToSeq(frel) == Old(ToSeq(frel)))
        # While no match has been seen, no eligible slot among 0..i matches.
        Invariant(Implies(
            not found,
            Implies(not constrained, Forall(int, lambda k: (
                Implies(0 <= k and k < i,
                        not (reusable(k, n, reuse_all, reuse_mask)
                             and matches_default(k, n, jb, jf, base, frel)))
            )))))
        Invariant(Implies(
            not found,
            Implies(constrained, Forall(int, lambda k: (
                Implies(0 <= k and k < i,
                        not (reuse_mask[k]
                             and matches_constrained(k, n, jb, base)))
            )))))
        # Once a match has been seen, an eligible matching slot provably exists.
        Invariant(Implies(
            found,
            not no_eligible_match(
                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        if constrained:
            if reuse_mask[i] and matches_constrained(i, n, jb, base):
                found = True
        else:
            if reusable(i, n, reuse_all, reuse_mask) and \\
                    matches_default(i, n, jb, jf, base, frel):
                found = True
        i = i + 1
    return not found"""


def _impl(new_body: str) -> str:
    """Replace ONLY install_join's impl body (between the # impl-start /
    # impl-end markers); the frozen spec is never touched."""
    return _swap(_BASE, _IMPL, new_body)


# Sanity: the anchor must be present exactly once.
assert _BASE.count(_IMPL) == 1, "impl anchor drift — re-sync _IMPL with model.py"


# ───────────────────────────────────────────────────────────────────────────
# SPEC_TESTS
# ───────────────────────────────────────────────────────────────────────────
SPEC_TESTS = [

    # ════════════════════════════════════════════════ soundness / positive ═══
    # POSITIVE CONTROL 1 (branch reorder + local reshape). Structurally different
    # but fully CORRECT: the default branch is tested first via `not constrained`,
    # the per-slot eligibility/match are bound to local booleans before the guard,
    # and `found` is set the same way. The loop scans front-to-back exactly like
    # gold, so EVERY gold invariant (the front-prefix Forall over 0..k<i, the
    # found⇒¬no_eligible_match witness, the F1/F2 frame eqs) stays valid verbatim
    # — no new induction lemma is needed. If this cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    n = len(base)\n"
            "    found = False\n"
            "    i = 0\n"
            "    while i < n:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(base), 1 / 2))\n"
            "        Invariant(Acc(list_pred(frel), 1 / 2))\n"
            "        Invariant(Acc(list_pred(reuse_mask), 1 / 2))\n"
            "        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)\n"
            "        Invariant(0 <= i and i <= n)\n"
            "        Invariant(Implies(constrained, not reuse_all))\n"
            "        Invariant(ToSeq(base) == Old(ToSeq(base)))\n"
            "        Invariant(ToSeq(frel) == Old(ToSeq(frel)))\n"
            "        Invariant(Implies(\n"
            "            not found,\n"
            "            Implies(not constrained, Forall(int, lambda k: (\n"
            "                Implies(0 <= k and k < i,\n"
            "                        not (reusable(k, n, reuse_all, reuse_mask)\n"
            "                             and matches_default(k, n, jb, jf, base, frel)))\n"
            "            )))))\n"
            "        Invariant(Implies(\n"
            "            not found,\n"
            "            Implies(constrained, Forall(int, lambda k: (\n"
            "                Implies(0 <= k and k < i,\n"
            "                        not (reuse_mask[k]\n"
            "                             and matches_constrained(k, n, jb, base)))\n"
            "            )))))\n"
            "        Invariant(Implies(\n"
            "            found,\n"
            "            not no_eligible_match(\n"
            "                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))\n"
            "        Invariant(MustTerminate(n - i + 1))\n"
            "        # invariants-end\n"
            "        if not constrained:\n"
            "            elig = reusable(i, n, reuse_all, reuse_mask)\n"
            "            hit = matches_default(i, n, jb, jf, base, frel)\n"
            "            if elig and hit:\n"
            "                found = True\n"
            "        else:\n"
            "            elig2 = reuse_mask[i]\n"
            "            hit2 = matches_constrained(i, n, jb, base)\n"
            "            if elig2 and hit2:\n"
            "                found = True\n"
            "        i = i + 1\n"
            "    return not found"
        ),
        "rationale": "a correct, structurally-reshaped impl (default branch first, "
                     "eligibility/match hoisted into locals) must verify; it keeps "
                     "the gold front-to-back invariants verbatim, so no fold lemma "
                     "is introduced. Else SPEC-TOO-STRONG.",
    },

    # POSITIVE CONTROL 2 (cheapest honest impl == grounded-oracle stand-in). Since
    # no_eligible_match is GROUNDED in the args (a Forall over the real slots, not
    # a @ContractOnly answer-key), the cheapest correct impl simply RETURNS it —
    # which is exactly the work the gold scan computes. There is no wrong echo to
    # build (see UNGROUNDED-ORACLE note in 'assessment'); this is the honest
    # positive control standing in for that class. No loop ⇒ no invariants. The
    # frame guards (F1/F2/F3/L) hold trivially because nothing is mutated.
    {
        "id": "pos-cheapest-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    result = no_eligible_match(\n"
            "        base, frel, reuse_all, reuse_mask, jb, jf, constrained)  # type: bool\n"
            "    return result"
        ),
        "rationale": "the postcondition is Result()==no_eligible_match(...) and the "
                     "oracle is grounded in the inputs, so the cheapest correct impl "
                     "returns it directly — doing the real work. Must verify; else "
                     "SPEC-TOO-STRONG. Stands in for ungrounded-oracle (no wrong echo "
                     "exists for a grounded Forall oracle).",
    },

    # ════════════════════════════════════════════════════════ admissibility ═══
    # A self-CALLING caller on an F2P-shaped input, inserted at the top of the impl
    # region (before any gold obligation, so all gold obligations are preserved).
    # It constructs a concrete one-slot registry (the test_multiple shape: a single
    # existing slot, base 5, refinement 1) and calls install_join in DEFAULT mode
    # with a SAME-BASE DISTINCT-REFINEMENT incoming descriptor (jb=5, jf=2). The
    # precondition (aligned arrays, Implies(constrained, not reuse_all)) must be
    # establishable; the call must verify and a fresh slot (Result True) must be
    # the post fact. If the Requires cannot be met for this normal input =>
    # PRECOND-TOO-STRONG. The gold loop then runs unchanged below.
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # ADMISSIBILITY PROBE: an F2P-shaped one-slot registry (same base,\n"
            "    # distinct refinement) admits the precondition; the call verifies\n"
            "    # and a fresh alias (Result True) is the post fact.\n"
            "    pbase = [5]  # type: List[int]\n"
            "    pfrel = [1]  # type: List[int]\n"
            "    pmask = [True]  # type: List[bool]\n"
            "    Assert(list_pred(pbase))\n"
            "    Assert(list_pred(pfrel))\n"
            "    Assert(list_pred(pmask))\n"
            "    Assert(Acc(list_pred(pbase), 1 / 2))\n"
            "    Assert(Acc(list_pred(pfrel), 1 / 2))\n"
            "    Assert(Acc(list_pred(pmask), 1 / 2))\n"
            "    Assert(len(pbase) == len(pfrel))\n"
            "    Assert(len(pbase) == len(pmask))\n"
            "    Assert(Implies(False, not True))\n"
            "    n = len(base)\n"
            "    found = False\n"
            "    i = 0\n"
            "    while i < n:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(base), 1 / 2))\n"
            "        Invariant(Acc(list_pred(frel), 1 / 2))\n"
            "        Invariant(Acc(list_pred(reuse_mask), 1 / 2))\n"
            "        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)\n"
            "        Invariant(0 <= i and i <= n)\n"
            "        Invariant(Implies(constrained, not reuse_all))\n"
            "        Invariant(ToSeq(base) == Old(ToSeq(base)))\n"
            "        Invariant(ToSeq(frel) == Old(ToSeq(frel)))\n"
            "        Invariant(Implies(\n"
            "            not found,\n"
            "            Implies(not constrained, Forall(int, lambda k: (\n"
            "                Implies(0 <= k and k < i,\n"
            "                        not (reusable(k, n, reuse_all, reuse_mask)\n"
            "                             and matches_default(k, n, jb, jf, base, frel)))\n"
            "            )))))\n"
            "        Invariant(Implies(\n"
            "            not found,\n"
            "            Implies(constrained, Forall(int, lambda k: (\n"
            "                Implies(0 <= k and k < i,\n"
            "                        not (reuse_mask[k]\n"
            "                             and matches_constrained(k, n, jb, base)))\n"
            "            )))))\n"
            "        Invariant(Implies(\n"
            "            found,\n"
            "            not no_eligible_match(\n"
            "                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))\n"
            "        Invariant(MustTerminate(n - i + 1))\n"
            "        # invariants-end\n"
            "        if constrained:\n"
            "            if reuse_mask[i] and matches_constrained(i, n, jb, base):\n"
            "                found = True\n"
            "        else:\n"
            "            if reusable(i, n, reuse_all, reuse_mask) and \\\n"
            "                    matches_default(i, n, jb, jf, base, frel):\n"
            "                found = True\n"
            "        i = i + 1\n"
            "    return not found"
        ),
        "rationale": "the precondition must admit a normal F2P-shaped input (a "
                     "one-slot registry, default reuse, a same-base distinct-"
                     "refinement incoming descriptor). Every clause of install_join's "
                     "Requires is asserted AT the witness rather than exercised by a "
                     "self-call: the model carries Requires(MustTerminate(2)) with "
                     "Invariant(MustTerminate(n - i + 1)) on the scan, and a "
                     "same-level self-call on a non-shrinking argument is an "
                     "obligation leak Nagini is right to refuse. Else "
                     "PRECOND-TOO-STRONG. NEGATIVE CONTROL (measured): move the "
                     "witness outside the frozen len(base)==len(frel) clause, "
                     "pfrel = [1, 1] against pbase = [5], and the probe REJECTS: "
                     "`Assert might fail. Assertion (len(pbase) == len(pfrel)) might "
                     "not hold.` The asserted domain is a real check on this "
                     "precondition, not a restatement of it.",
    },

    # ═══════════════════════════════════════ uniqueness / frame-mutation ═══════
    # FRAME-MUTATION (MANDATORY — base/frel/reuse_mask are read-only Acc(.,1/2)).
    # A rival that WRITES to the registry base array to vacuously establish a
    # postcondition. The registry arrays are held at HALF permission, which cannot
    # be written, so this must be REJECTED for INSUFFICIENT PERMISSION — not for a
    # value mismatch. Every gold invariant/postcondition is kept verbatim, so the
    # rejection is attributable solely to the write `base[i] = jb`.
    {
        "id": "frame-mut-base-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    n = len(base)\n"
            "    found = False\n"
            "    i = 0\n"
            "    # FRAME-MUTATION RIVAL: overwrite a registry base entry. base is\n"
            "    # held at Acc(.,1/2) (read-only) so this write needs full perm and\n"
            "    # must be rejected for INSUFFICIENT PERMISSION.\n"
            "    if n > 0:\n"
            "        base[0] = jb\n"
            "    while i < n:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(base), 1 / 2))\n"
            "        Invariant(Acc(list_pred(frel), 1 / 2))\n"
            "        Invariant(Acc(list_pred(reuse_mask), 1 / 2))\n"
            "        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)\n"
            "        Invariant(0 <= i and i <= n)\n"
            "        Invariant(Implies(constrained, not reuse_all))\n"
            "        Invariant(ToSeq(base) == Old(ToSeq(base)))\n"
            "        Invariant(ToSeq(frel) == Old(ToSeq(frel)))\n"
            "        Invariant(Implies(\n"
            "            not found,\n"
            "            Implies(not constrained, Forall(int, lambda k: (\n"
            "                Implies(0 <= k and k < i,\n"
            "                        not (reusable(k, n, reuse_all, reuse_mask)\n"
            "                             and matches_default(k, n, jb, jf, base, frel)))\n"
            "            )))))\n"
            "        Invariant(Implies(\n"
            "            not found,\n"
            "            Implies(constrained, Forall(int, lambda k: (\n"
            "                Implies(0 <= k and k < i,\n"
            "                        not (reuse_mask[k]\n"
            "                             and matches_constrained(k, n, jb, base)))\n"
            "            )))))\n"
            "        Invariant(Implies(\n"
            "            found,\n"
            "            not no_eligible_match(\n"
            "                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))\n"
            "        Invariant(MustTerminate(n - i + 1))\n"
            "        # invariants-end\n"
            "        if constrained:\n"
            "            if reuse_mask[i] and matches_constrained(i, n, jb, base):\n"
            "                found = True\n"
            "        else:\n"
            "            if reusable(i, n, reuse_all, reuse_mask) and \\\n"
            "                    matches_default(i, n, jb, jf, base, frel):\n"
            "                found = True\n"
            "        i = i + 1\n"
            "    return not found"
        ),
        "refinement": "self.alias_map is the live join registry shared across the "
                     "whole query build; Query.join only READS it to decide reuse "
                     "(the caller appends a new alias separately). A faithful patch "
                     "that overwrote an existing join's identity in alias_map during "
                     "the reuse scan would corrupt every later join/setup_joins "
                     "decision in the same query — the filtered_relation P2P suite "
                     "(test_with_join, test_as_subquery, the aggregation tests) reads "
                     "those joins back and would build wrong SQL; it would NOT resolve.",
        "rationale": "rejection source: the PERMISSION SYSTEM — base is held at "
                     "Acc(list_pred(base),1/2), a read-only fraction; the write "
                     "base[0]=jb requires full permission the impl does not hold, so "
                     "the assignment fails to verify (insufficient permission). The "
                     "F1 frame eq ToSeq(base)==Old(ToSeq(base)) would ALSO fail, but "
                     "the permission check fires first.",
    },

    # ═══════════════════════════════════════ uniqueness / partial-domain ══════
    # ATTACK A (THE bug-delta, model_prepatch.py reproduced). In the DEFAULT branch
    # use base-only matching (matches_constrained) instead of full-identity
    # (matches_default). Correct whenever the incoming refinement tag equals the
    # slot's, WRONG on the F2P sub-domain: same base, DISTINCT refinement under
    # default reuse — it wrongly reports "no fresh slot needed" (reuse) where gold
    # demands a fresh slot. This is exactly the pre-patch j.equals(join) default.
    {
        "id": "weak-default-base-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    n = len(base)\n"
            "    found = False\n"
            "    i = 0\n"
            "    while i < n:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(base), 1 / 2))\n"
            "        Invariant(Acc(list_pred(frel), 1 / 2))\n"
            "        Invariant(Acc(list_pred(reuse_mask), 1 / 2))\n"
            "        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)\n"
            "        Invariant(0 <= i and i <= n)\n"
            "        Invariant(Implies(constrained, not reuse_all))\n"
            "        Invariant(ToSeq(base) == Old(ToSeq(base)))\n"
            "        Invariant(ToSeq(frel) == Old(ToSeq(frel)))\n"
            "        # invariants-end\n"
            "        if constrained:\n"
            "            if reuse_mask[i] and matches_constrained(i, n, jb, base):\n"
            "                found = True\n"
            "        else:\n"
            "            if reusable(i, n, reuse_all, reuse_mask) and \\\n"
            "                    matches_constrained(i, n, jb, base):\n"
            "                found = True\n"
            "        i = i + 1\n"
            "    return not found"
        ),
        "refinement": "this is the PRE-PATCH default predicate j.equals(join) "
                     "(base-only, ignores filtered_relation). With two "
                     "FilteredRelations on the same relation but different "
                     "conditions (F2P test_multiple: Restaurant pizzas 'mozzarella' "
                     "vs 'pineapple'), the second join is wrongly merged onto the "
                     "first alias instead of getting a fresh one. test_multiple "
                     "asserts the two filtered relations stay distinct => the "
                     "faithful real patch FAILS the F2P; it does NOT resolve.",
        "rationale": "rejection source: postcondition (O) "
                     "Result()==no_eligible_match(...). no_eligible_match's default "
                     "arm uses matches_default (full identity), so a base-only match "
                     "sets found while no_eligible_match is still True ⇒ the loop "
                     "invariant Implies(found, not no_eligible_match(...)) is "
                     "unprovable (exactly model_prepatch.py's failure).",
    },

    # ATTACK B (partial-domain: eligibility ignored in default mode). Drop the
    # reuse-eligibility guard in the DEFAULT branch — match on identity alone,
    # ignoring `reusable(i,...)`. Correct whenever every slot is eligible
    # (reuse_all True, the common default), WRONG when a non-reuse-set slot
    # (reuse_all False, reuse_mask[i] False) matches the identity: gold says fresh
    # (that slot is not reusable), this says reuse.
    {
        "id": "weak-default-ignore-eligibility",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    n = len(base)\n"
            "    found = False\n"
            "    i = 0\n"
            "    while i < n:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(base), 1 / 2))\n"
            "        Invariant(Acc(list_pred(frel), 1 / 2))\n"
            "        Invariant(Acc(list_pred(reuse_mask), 1 / 2))\n"
            "        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)\n"
            "        Invariant(0 <= i and i <= n)\n"
            "        Invariant(Implies(constrained, not reuse_all))\n"
            "        Invariant(ToSeq(base) == Old(ToSeq(base)))\n"
            "        Invariant(ToSeq(frel) == Old(ToSeq(frel)))\n"
            "        # invariants-end\n"
            "        if constrained:\n"
            "            if reuse_mask[i] and matches_constrained(i, n, jb, base):\n"
            "                found = True\n"
            "        else:\n"
            "            if matches_default(i, n, jb, jf, base, frel):\n"
            "                found = True\n"
            "        i = i + 1\n"
            "    return not found"
        ),
        "refinement": "this drops the `(reuse is None or a in reuse)` guard from the "
                     "default reuse comprehension. When a reuse set IS supplied "
                     "(reuse not None) but a matching join's alias is NOT in it, gold "
                     "must create a fresh alias; this rival wrongly reuses an alias "
                     "outside the permitted set, leaking a join the caller forbade. "
                     "The setup_joins/build_filter reuse-set discipline (P2P "
                     "multijoin / reverse-fk reuse tests) would break => the faithful "
                     "real patch does NOT resolve.",
        "rationale": "rejection source: postcondition (O). no_eligible_match gates "
                     "the default match by reusable(k,...) = reuse_all or "
                     "reuse_mask[k]; dropping it sets found for an ineligible slot "
                     "while no_eligible_match stays True ⇒ Implies(found, not "
                     "no_eligible_match) is unprovable.",
    },

    # ATTACK C (partial-domain: constrained branch uses FULL identity). In the
    # CONSTRAINED branch use matches_default (base AND refinement) instead of
    # matches_constrained (base only). Correct whenever the masked slot's
    # refinement tag happens to equal the incoming jf, WRONG when a masked slot
    # has the same base but a DIFFERENT refinement: gold reuses it (base-only),
    # this rival reports fresh.
    {
        "id": "weak-constrained-full-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    n = len(base)\n"
            "    found = False\n"
            "    i = 0\n"
            "    while i < n:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(base), 1 / 2))\n"
            "        Invariant(Acc(list_pred(frel), 1 / 2))\n"
            "        Invariant(Acc(list_pred(reuse_mask), 1 / 2))\n"
            "        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)\n"
            "        Invariant(0 <= i and i <= n)\n"
            "        Invariant(Implies(constrained, not reuse_all))\n"
            "        Invariant(ToSeq(base) == Old(ToSeq(base)))\n"
            "        Invariant(ToSeq(frel) == Old(ToSeq(frel)))\n"
            "        # invariants-end\n"
            "        if constrained:\n"
            "            if reuse_mask[i] and matches_default(i, n, jb, jf, base, frel):\n"
            "                found = True\n"
            "        else:\n"
            "            if reusable(i, n, reuse_all, reuse_mask) and \\\n"
            "                    matches_default(i, n, jb, jf, base, frel):\n"
            "                found = True\n"
            "        i = i + 1\n"
            "    return not found"
        ),
        "refinement": "this is the constrained branch using j == join instead of the "
                     "gold j.equals(join). When computing a FilteredRelation's own "
                     "sub-filter joins (reuse_with_filtered_relation True), the patch "
                     "deliberately matches base-only over the supplied reuse set so a "
                     "relation's join is reused regardless of its filtered_relation "
                     "tag. Requiring the full tag here would spuriously create extra "
                     "aliases for the same connection, changing the generated SQL of "
                     "the filtered-relation aggregation P2P tests => the faithful "
                     "real patch does NOT resolve.",
        "rationale": "rejection source: postcondition (O). no_eligible_match's "
                     "constrained arm uses matches_constrained (base only); using "
                     "matches_default leaves found False on a same-base distinct-tag "
                     "masked slot while no_eligible_match is False ⇒ Result()=True "
                     "violates Result()==no_eligible_match(...).",
    },

    # ATTACK D (partial-domain: branch swapped — constrained logic in default).
    # Use the CONSTRAINED eligibility (reuse_mask[i] only) in the DEFAULT branch.
    # Correct whenever reuse_all is False (so default eligibility already equals
    # reuse_mask[i]), WRONG on the unconstrained common case reuse_all=True: gold
    # treats every slot as reusable, this rival skips slots not in the mask.
    {
        "id": "weak-default-mask-only-eligibility",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    n = len(base)\n"
            "    found = False\n"
            "    i = 0\n"
            "    while i < n:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(base), 1 / 2))\n"
            "        Invariant(Acc(list_pred(frel), 1 / 2))\n"
            "        Invariant(Acc(list_pred(reuse_mask), 1 / 2))\n"
            "        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)\n"
            "        Invariant(0 <= i and i <= n)\n"
            "        Invariant(Implies(constrained, not reuse_all))\n"
            "        Invariant(ToSeq(base) == Old(ToSeq(base)))\n"
            "        Invariant(ToSeq(frel) == Old(ToSeq(frel)))\n"
            "        # invariants-end\n"
            "        if constrained:\n"
            "            if reuse_mask[i] and matches_constrained(i, n, jb, base):\n"
            "                found = True\n"
            "        else:\n"
            "            if reuse_mask[i] and \\\n"
            "                    matches_default(i, n, jb, jf, base, frel):\n"
            "                found = True\n"
            "        i = i + 1\n"
            "    return not found"
        ),
        "refinement": "this replaces the default eligibility `(reuse is None or a in "
                     "reuse)` with `a in reuse` (reuse_mask[i] only), dropping the "
                     "reuse-is-None ⇒ all-reusable case. In the overwhelmingly common "
                     "unconstrained call (reuse is None), a perfectly reusable "
                     "identical join would be SKIPPED and a duplicate alias created, "
                     "changing join counts and SQL across nearly every query — the "
                     "filtered_relation P2P suite (and the whole ORM) reuses aliases "
                     "in the reuse=None path => the faithful real patch does NOT "
                     "resolve.",
        "rationale": "rejection source: postcondition (O). With reuse_all True and a "
                     "matching un-masked slot, no_eligible_match is False (gold: "
                     "reusable=True) but this rival leaves found False ⇒ Result()=True "
                     "≠ no_eligible_match=False.",
    },

    # ATTACK E (supporting near-miss: invert the result). Compute `found` exactly
    # as gold but return `found` instead of `not found`. A cheap polarity flip; it
    # still carries a real refinement and is rejected by (O). Kept as a SUPPORTING
    # case, not a substitute for the reasoned partial-domain attacks above.
    {
        "id": "weak-result-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL.replace("    return not found", "    return found")),
        "refinement": "this reports 'a fresh alias is needed' exactly when one is NOT "
                     "(and vice-versa): every reusable match would trigger a "
                     "spurious new alias and every miss would skip the needed one. "
                     "Query.join would either never reuse or always reuse — wholesale "
                     "wrong SQL across the entire filtered_relation suite; the "
                     "faithful real patch does NOT resolve.",
        "rationale": "rejection source: postcondition (O) "
                     "Result()==no_eligible_match(...). Returning `found` gives "
                     "Result()==not no_eligible_match(...), the exact negation.",
    },
]


# ───────────────────────────────────────────────────────────────────────────
# AXIOM_TESTS
# ───────────────────────────────────────────────────────────────────────────
# This bundle consumes NO @ContractOnly axiom (meta.axioms == [], refinement.md
# §C): the changed operation is pure tuple/integer equality over Join.identity,
# modeled DEEPLY (matches_default / matches_constrained / the Forall in
# no_eligible_match). The only external fact is an A-REFERENCE type-refinement —
# that the real Join.__eq__ compares the FULL identity tuple (incl.
# filtered_relation) while Join.equals compares identity[:-1] (excl. it). That is
# validated executably by axiom_check.py (G-AX). We embed that exact host-validated
# oracle verbatim as a single axiom-lane probe so the A-reference is grounded in
# the REAL Join semantics in-container (the runner mounts only this probe script;
# axiom_check.py is NOT in-container, so it is read on the HOST at load time and
# embedded). It CALLS faithful stand-ins of the real datastructures.py:Join /
# query_utils.py:FilteredRelation __eq__ / equals (it does not scrape source) and
# re-derives the whole-registry decision; it reads no files (no utf-8 concern) and
# imports only stdlib. Exits 0 iff every A-reference obligation holds.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-join-eq-equals-areference",
        "axiom": "matches_default,matches_constrained",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness+containment: the deep predicates must "
                     "equal the REAL Join semantics — (j == join) ⇔ matches_default "
                     "(full identity incl. filtered_relation) and (j.equals(join)) ⇔ "
                     "matches_constrained (identity[:-1]) — and the whole-registry "
                     "'fresh alias needed' decision must equal a faithful gold "
                     "Query.join reuse comprehension, on 96 boundary + 60000 fuzz "
                     "registries plus the F2P distinct-refinement witness. The model "
                     "only reaches int base/refinement tags and bool masks, all "
                     "inside the predicates' (purely equality) domain, so containment "
                     "holds. A disagreement ⇒ the deep model misrepresents the real "
                     "callee (the A-reference analogue of AXIOM-UNSOUND).",
    },
]
