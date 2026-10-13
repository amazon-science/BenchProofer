# properties.py — PBT falsification battery for django__django-15128.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant built by region-surgery that edits
# ONLY inside the `# impl-start` / `# impl-end` region of build_relabel_map, so
# the FROZEN spec (axioms/pure/pre/post-conditions + disjoint_by_floor lemma +
# signatures) is never touched and same_spec holds by construction.
#
# Defended surface of this instance (build_relabel_map(aliases, new_ns, excluded)):
#   * `aliases` is READ-ONLY: Requires(Acc(list_pred(aliases), 1/2)).  => the
#     frame-mutation probe is MANDATORY.
#   * Load-bearing postcondition clauses:
#       A6  (Result()[1][k]==1) == (aliases[k] != excluded)      [exclude filter]
#       A4b Result()[0][j] == fresh_alias(new_ns, j)             [per-ordinal value
#                                                                  => injective targets]
#       A7  aliases[k] != Result()[0][j]  for all k,j            [key/value disjoint]
#   * fresh_alias(new_ns, j) is a GROUNDED @Pure function of the args
#     (new_ns*BASE+j, fully unfolded) — NOT an opaque answer-key. There is no
#     "wrong echo" to build (an echo of fresh_alias just IS the gold value).
#     The ungrounded-oracle lane is therefore N/A; in its place we ship an honest
#     cheapest-impl positive control and several partial-domain rivals that try to
#     satisfy a subset of {A4b, A6, A7} while diverging on the rest. See assessment.
#
# This bundle has NO @ContractOnly axiom / A-consumed row (the relabel-map
# construction is modelled deeply; axioms region empty), so AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "django__django-15128"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Reusable impl-region fragments (verbatim slices of model.py's impl region).
# ---------------------------------------------------------------------------

# The gold per-position body (target append + is_source if/else + the two asserts).
_GOLD_BODY = (
    "        t = fresh_alias(new_ns, pos)\n"
    "        targets.append(t)\n"
    "        Assert(targets[pos] == t)\n"
    "        Assert(targets[pos] >= floor_of(new_ns))\n"
    "        if aliases[pos] != excluded:\n"
    "            is_source.append(1)\n"
    "        else:\n"
    "            is_source.append(0)\n"
    "        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))\n"
    "        pos = pos + 1\n"
)

# The opening of the impl region (unique anchor for inserting an admissibility
# assert without disturbing the spec).
_IMPL_OPEN = (
    "    # impl-start\n"
    "    targets = []  # type: List[int]\n"
)

# The gold source-flag loop invariant (inside the impl region's invariants
# block). Rivals whose bodies BREAK this invariant must also rewrite it to
# their own consistent shape — otherwise the verifier burns its budget on the
# unprovable invariant-preservation obligation (Z3 diverges; observed 900s+
# timeouts) instead of failing the POSTCONDITION. Same pattern the collapse
# case below already uses for the target invariant.
_FLAG_INV_GOLD = (
    "        # ...and the source flag records exactly \"not the kept alias\".\n"
    "        Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,\n"
    "                (is_source[k] == 1) == (aliases[k] != excluded))))\n"
)


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — structurally different, still CORRECT.
#    Reorder the is_source branch (test the EXCLUDED case first) and reshape
#    the target append into a typed local. Every gold proof obligation it still
#    needs (per-position target pin, floor pin, biconditional assert, the final
#    disjoint_by_floor call) is preserved verbatim. Must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_BODY = (
    "        new_target = fresh_alias(new_ns, pos)  # type: int\n"
    "        targets.append(new_target)\n"
    "        Assert(targets[pos] == new_target)\n"
    "        Assert(targets[pos] >= floor_of(new_ns))\n"
    "        if aliases[pos] == excluded:\n"
    "            is_source.append(0)\n"
    "        else:\n"
    "            is_source.append(1)\n"
    "        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))\n"
    "        pos = pos + 1\n"
)
POS_CONTROL = _swap(_BASE, _GOLD_BODY, _POS_BODY)


# ===========================================================================
# 2. ADMISSIBILITY — the precondition must admit a normal F2P-shaped input.
#    Insert, at the top of the impl region, asserts that the read-only grant on
#    `aliases` is actually held (Acc(...,1/2)) and that a length/well-formedness
#    fact derivable from the Requires is usable. If these cannot be established
#    the precondition is unusable for a legitimate input => PRECOND-TOO-STRONG.
#    (Edits only the impl region; the gold body is otherwise untouched, so it
#    still verifies the full postcondition.)
# ===========================================================================
_ADMISS_OPEN = (
    "    # impl-start\n"
    "    # admissibility: the read-only grant on `aliases` is held and the\n"
    "    # well-formedness facts of the precondition are usable for an F2P-shaped\n"
    "    # input (an ordered list of in-namespace aliases, one of them excluded).\n"
    "    Assert(Acc(list_pred(aliases), 1 / 2))\n"
    "    Assert(len(aliases) <= BASE())\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),\n"
    "                                           aliases[k] >= 0), [[aliases[k]]])))\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),\n"
    "                                           aliases[k] < floor_of(new_ns)),\n"
    "                                  [[aliases[k]]])))\n"
    "    targets = []  # type: List[int]\n"
)
ADMISS = _swap(_BASE, _IMPL_OPEN, _ADMISS_OPEN)


# ===========================================================================
# 3. FRAME-MUTATION (MANDATORY) — `aliases` is read-only (Acc(...,1/2)). A rival
#    that WRITES to `aliases` to make the postcondition hold vacuously must be
#    REJECTED for INSUFFICIENT PERMISSION. Here the rival overwrites the source
#    alias it is about to compare against (aliases[pos] = -1) so that the
#    biconditional/disjointness become trivial. With only 1/2 permission the
#    store `aliases[pos] = ...` cannot verify.
#    Gold invariants kept verbatim so the rejection is attributable to the WRITE.
# ===========================================================================
_FRAME_BODY = (
    "        t = fresh_alias(new_ns, pos)\n"
    "        targets.append(t)\n"
    "        Assert(targets[pos] == t)\n"
    "        Assert(targets[pos] >= floor_of(new_ns))\n"
    "        # ATTACK: overwrite the read-only input to trivialise the\n"
    "        # biconditional/disjointness. Only Acc(aliases,1/2) is held, so this\n"
    "        # store must be rejected for insufficient permission.\n"
    "        aliases[pos] = -1\n"
    "        if aliases[pos] != excluded:\n"
    "            is_source.append(1)\n"
    "        else:\n"
    "            is_source.append(0)\n"
    "        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))\n"
    "        pos = pos + 1\n"
)
FRAME_MUTATION = _swap(_BASE, _GOLD_BODY, _FRAME_BODY)


# ===========================================================================
# 4. PARTIAL-DOMAIN — exclude filter dropped (the PRE-PATCH behaviour). Mark
#    EVERY position a source (is_source.append(1) unconditionally), so the
#    excluded base alias is wrongly relabelled. Correct on every position whose
#    alias != excluded but diverges on the excluded one => violates A6
#    biconditional. This is exactly model_prepatch.py's bug. The matching loop
#    invariant is rewritten to the rival's own (consistent) shape so the
#    failure is the POSTCONDITION A6, not a stale invariant (which stalls Z3).
#    REFINEMENT: a real patch with no `exclude` filter relabels the shared base
#    alias too; in the F2P (test_conflicting_aliases_during_combine) that
#    re-introduces the conflicting change_map {T4:T5, T5:T6} the issue reports,
#    so change_aliases' isdisjoint assertion fires and qs1|qs2 raises — F2P FAILS.
# ===========================================================================
_PREPATCH_INV = (
    "        # ATTACK invariant (the rival's own, consistent with its body):\n"
    "        # every position so far is flagged a source, unconditionally.\n"
    "        Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,\n"
    "                is_source[k] == 1)))\n"
)
_PREPATCH_BODY = (
    "        t = fresh_alias(new_ns, pos)\n"
    "        targets.append(t)\n"
    "        Assert(targets[pos] == t)\n"
    "        Assert(targets[pos] >= floor_of(new_ns))\n"
    "        # ATTACK: pre-patch — no exclude filter; every alias is a source.\n"
    "        is_source.append(1)\n"
    "        Assert(is_source[pos] == 1)\n"
    "        pos = pos + 1\n"
)
PARTIAL_PREPATCH = _swap(_BASE, _FLAG_INV_GOLD, _PREPATCH_INV)
PARTIAL_PREPATCH = _swap(PARTIAL_PREPATCH, _GOLD_BODY, _PREPATCH_BODY)


# ===========================================================================
# 5. PARTIAL-DOMAIN — biconditional broken only on the FIRST position. The
#    excluded base alias is the initial (pos 0) alias in the real combine() call
#    (initial_alias = get_initial_alias() is the base table, first in alias_map).
#    This rival is correct for every pos >= 1 but flips the flag at pos 0: marks
#    position 0 a source unconditionally. If aliases[0] == excluded that violates
#    A6 exactly at the position the F2P exercises. The matching loop invariant
#    is rewritten to the rival's own (consistent) shape so the failure is the
#    POSTCONDITION A6, not a stale invariant (which stalls Z3).
#    REFINEMENT: a real patch whose `not in exclude` guard skipped the FIRST
#    enumerate position relabels the base alias (which IS first), re-introducing
#    the key/value intersection => F2P AssertionError on qs1|qs2. Diverges on the
#    very sub-domain the bug lives in.
# ===========================================================================
_FIRSTPOS_INV = (
    "        # ATTACK invariant (the rival's own, consistent with its body):\n"
    "        # position 0 is always flagged a source; positions >= 1 follow\n"
    "        # the gold rule.\n"
    "        Invariant(Implies(pos > 0, is_source[0] == 1))\n"
    "        Invariant(Forall(int, lambda k: Implies(1 <= k and k < pos,\n"
    "                (is_source[k] == 1) == (aliases[k] != excluded))))\n"
)
_FIRSTPOS_BODY = (
    "        t = fresh_alias(new_ns, pos)\n"
    "        targets.append(t)\n"
    "        Assert(targets[pos] == t)\n"
    "        Assert(targets[pos] >= floor_of(new_ns))\n"
    "        # ATTACK: special-case pos 0 to ALWAYS be a source, regardless of\n"
    "        # whether aliases[0] is the excluded base alias.\n"
    "        if pos == 0:\n"
    "            is_source.append(1)\n"
    "            Assert(is_source[pos] == 1)\n"
    "        elif aliases[pos] != excluded:\n"
    "            is_source.append(1)\n"
    "            Assert((is_source[pos] == 1) == (aliases[pos] != excluded))\n"
    "        else:\n"
    "            is_source.append(0)\n"
    "            Assert((is_source[pos] == 1) == (aliases[pos] != excluded))\n"
    "        pos = pos + 1\n"
)
PARTIAL_FIRSTPOS = _swap(_BASE, _FLAG_INV_GOLD, _FIRSTPOS_INV)
PARTIAL_FIRSTPOS = _swap(PARTIAL_FIRSTPOS, _GOLD_BODY, _FIRSTPOS_BODY)


# ===========================================================================
# 6. PARTIAL-DOMAIN / non-injective targets — collapse all targets onto the
#    namespace floor (the constant floor_of(new_ns)). This still satisfies A7
#    disjointness (every target >= floor > every source) but VIOLATES A4b's
#    per-ordinal value pin Result()[0][j] == fresh_alias(new_ns, j) for j>=1, so
#    distinct source aliases collapse onto ONE renamed value. The matching loop
#    invariant is rewritten to the rival's own (consistent) shape so the failure
#    is the POSTCONDITION A4b, not a stale invariant.
#    REFINEMENT: a real patch whose comprehension value did not depend on the
#    enumerate ordinal (e.g. a constant '<prefix>0') maps every alias to the SAME
#    new alias, silently merging distinct joins; qs1|qs2 and qs2|qs1 then no longer
#    yield the same rows (the F2P's exact observation) => F2P FAILS.
# ===========================================================================
_COLLAPSE_OLD = (
    "        # Each produced target so far is the fresh alias for its position...\n"
    "        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,\n"
    "                targets[j] == fresh_alias(new_ns, j))))\n"
    "        # ...hence lives in the fresh namespace...\n"
    "        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,\n"
    "                targets[j] >= floor_of(new_ns))))\n"
)
_COLLAPSE_NEW = (
    "        # ATTACK (non-injective): every target collapsed onto the floor.\n"
    "        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,\n"
    "                targets[j] == floor_of(new_ns))))\n"
    "        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,\n"
    "                targets[j] >= floor_of(new_ns))))\n"
)
_COLLAPSE_BODY_OLD = (
    "        t = fresh_alias(new_ns, pos)\n"
    "        targets.append(t)\n"
    "        Assert(targets[pos] == t)\n"
    "        Assert(targets[pos] >= floor_of(new_ns))\n"
)
_COLLAPSE_BODY_NEW = (
    "        t = floor_of(new_ns)  # ATTACK: constant target, not per-ordinal\n"
    "        targets.append(t)\n"
    "        Assert(targets[pos] == t)\n"
    "        Assert(targets[pos] >= floor_of(new_ns))\n"
)
PARTIAL_COLLAPSE = _swap(_BASE, _COLLAPSE_OLD, _COLLAPSE_NEW)
PARTIAL_COLLAPSE = _swap(PARTIAL_COLLAPSE, _COLLAPSE_BODY_OLD, _COLLAPSE_BODY_NEW)


# ===========================================================================
# 7. SUPPORTING near-miss (uniqueness) — invert the source-flag decision
#    everywhere (append 1 when excluded, 0 otherwise). A cheap mechanical
#    corruption that still carries a real refinement: it makes ONLY the base
#    alias a key and relabels nothing else, so the merge fails to disambiguate
#    every conflicting alias => the F2P still hits the isdisjoint assertion (or
#    silently drops joins). Violates A6 globally. Kept as a supporting case, not
#    a substitute for the reasoned attacks above.
# ===========================================================================
_INVERT_BODY = (
    "        t = fresh_alias(new_ns, pos)\n"
    "        targets.append(t)\n"
    "        Assert(targets[pos] == t)\n"
    "        Assert(targets[pos] >= floor_of(new_ns))\n"
    "        # ATTACK: inverted decision — only the excluded alias is a source.\n"
    "        if aliases[pos] == excluded:\n"
    "            is_source.append(1)\n"
    "        else:\n"
    "            is_source.append(0)\n"
    "        pos = pos + 1\n"
)
SUPPORT_INVERT = _swap(_BASE, _GOLD_BODY, _INVERT_BODY)


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CONTROL,
        "rationale": (
            "A structurally-different but CORRECT impl: the is_source branch is "
            "reordered to test the excluded case first and the target append is "
            "reshaped into a typed local; every gold proof obligation it still "
            "needs (per-position target pin, floor pin, biconditional assert, "
            "final disjoint_by_floor) is preserved verbatim. Must verify — else "
            "SPEC-TOO-STRONG (a faithful correct impl is rejected)."
        ),
    },
    {
        "id": "admiss-read-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": (
            "The precondition must admit a normal F2P-shaped input. Asserts at "
            "the top of the impl region that the read-only grant Acc(aliases,1/2) "
            "is held and the well-formedness facts (len<=BASE, each alias>=0 and "
            "< floor_of(new_ns)) are usable. If they cannot be established the "
            "precondition is unusable => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutation-overwrite-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_MUTATION,
        "refinement": (
            "Overwriting aliases[pos]=-1 to trivialise the biconditional has no "
            "faithful real patch: the gold relabel construction never mutates "
            "self.alias_map's KEYS (enumerate is read-only); a patch that did "
            "would corrupt the live alias_map and the resulting change_aliases "
            "would relabel garbage, so qs1|qs2 would not yield the rows qs2|qs1 "
            "does — the F2P (test_conflicting_aliases_during_combine) FAILS. The "
            "only reason this rival could verify is by abusing write permission "
            "it must not have."
        ),
        "rationale": (
            "MANDATORY frame-mutation probe: aliases is Requires(Acc(...,1/2)) "
            "(read-only). The store aliases[pos]=-1 needs full permission; with "
            "only 1/2 the verifier must REJECT for insufficient permission. If it "
            "verified, the read-only frame is unsound."
        ),
    },
    {
        "id": "partial-domain-prepatch-no-exclude",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_PREPATCH,
        "refinement": (
            "This is model_prepatch.py's behaviour (is_source.append(1) "
            "unconditionally). The faithful real patch is the PRE-PATCH bump_prefix "
            "with no `if alias not in exclude` guard: it relabels the shared base "
            "alias too, re-introducing the conflicting change_map {T4:T5, T5:T6} "
            "the issue reports. change_aliases' `assert set(change_map).isdisjoint("
            "change_map.values())` then fires and qs1|qs2 raises AssertionError — "
            "the F2P FAILS. (G-DIFF already confirms model_prepatch fails this spec.)"
        ),
        "rationale": (
            "Violates A6 ((Result()[1][k]==1) == (aliases[k]!=excluded)) at the "
            "excluded position: marks it a key when it must not be. The rival's "
            "loop invariant is rewritten to its own consistent shape (every flag "
            "== 1) so the failure is the POSTCONDITION A6, not an unprovable "
            "stale invariant that stalls Z3 (same pattern as the collapse case)."
        ),
    },
    {
        "id": "partial-domain-firstpos-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_FIRSTPOS,
        "refinement": (
            "Correct for every position >= 1 but special-cases pos 0 to always be "
            "a source. The excluded base alias is initial_alias = "
            "self.get_initial_alias(), which is FIRST in enumerate(self.alias_map). "
            "A real `not in exclude` guard that skipped the first enumerate position "
            "would relabel the base alias, re-creating the key/value intersection => "
            "F2P AssertionError on qs1|qs2. Diverges on the exact sub-domain the bug "
            "lives in."
        ),
        "rationale": (
            "Violates A6 at k==0 when aliases[0]==excluded. The rival's loop "
            "invariant is rewritten to its own consistent shape (pos 0 always "
            "flagged; gold rule for k>=1) so the failure is the POSTCONDITION "
            "A6's per-index Forall at position 0, not an unprovable stale "
            "invariant that stalls Z3 (same pattern as the collapse case)."
        ),
    },
    {
        "id": "partial-domain-noninjective-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_COLLAPSE,
        "refinement": (
            "Collapses every target onto floor_of(new_ns) — disjointness (A7) still "
            "holds but the per-ordinal value pin (A4b) is violated for j>=1, so "
            "distinct source aliases map onto ONE renamed value. The faithful real "
            "patch is a comprehension whose VALUE ignores the enumerate ordinal "
            "(e.g. a constant '<prefix>0'): it merges distinct joins, so qs1|qs2 and "
            "qs2|qs1 stop yielding the same rows — the F2P's exact observation FAILS. "
            "A4b is the load-bearing injectivity clause (refinement.md A4b / D)."
        ),
        "rationale": (
            "Violates A4b (Result()[0][j] == fresh_alias(new_ns, j)) for j>=1. The "
            "rival's invariant is rewritten consistently so the failure is the "
            "POSTCONDITION A4b, not a stale invariant. Rejection from the "
            "per-ordinal value clause."
        ),
    },
    {
        "id": "support-inverted-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SUPPORT_INVERT,
        "refinement": (
            "Supporting near-miss: inverts the source-flag decision everywhere "
            "(only the excluded alias becomes a key). A faithful real patch with an "
            "inverted membership guard (`if alias in exclude`) would relabel ONLY "
            "the base alias and leave every conflicting alias unchanged, so the "
            "merge never disambiguates them — qs1|qs2 still trips the isdisjoint "
            "assertion / drops joins => F2P FAILS. Carries a real refinement; a "
            "cheap support case, not a substitute for the reasoned attacks."
        ),
        "rationale": (
            "Violates A6 globally (every non-excluded position is wrongly flagged). "
            "Rejection from the post-condition biconditional."
        ),
    },
]


# No @ContractOnly axioms / A-consumed rows: the relabel-map construction is
# modelled deeply and validated == the real construction by axiom_check.py / G-AX
# (an A-reference, checked out of band, not consumed by the proof). Nothing for
# the in-Docker axiom lane to probe here.
AXIOM_TESTS = []
