# properties.py — PBT falsification battery for django__django-12273.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions untouched — invariants live INSIDE the impl
# region and are elided from the spec view, so a variant may reshape them) and
# swaps ONLY text inside the # impl-start/# impl-end region; the runner checks
# each with Nagini verify + markers.same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py + refinement.md + mapping.md + meta.json)
# ---------------------------------------------------------------------------
#   assign_identity(store, target, active, pk_idx, value) -> None
#     models Model._set_pk_val after the gold patch (the pk-property setter that
#     now cascades the assigned identity to every active parent-link target slot).
#
#   PERMISSIONS (load-bearing):
#     store : Acc(list_pred(store))         FULL  — the genuinely-mutated object.
#     target: Acc(list_pred(target), 1/2)   READ-ONLY metadata (parent-link slots)
#     active: Acc(list_pred(active), 1/2)   READ-ONLY metadata (the patch guard)
#   => any rival that WRITES to target or active must REJECT for INSUFFICIENT
#      PERMISSION (the #1 weakness class). FRAME-MUTATION is MANDATORY here.
#
#   Three load-bearing postcondition clauses pin the whole behaviour:
#     (P1) store[pk_idx] == value                       — identity slot written
#     (P2) Forall j: active[j]==1 => store[target[j]]==value   — the CASCADE
#     (P3) Forall i: (no active link targets i and i!=pk_idx) => store[i] unchanged
#                                                          — the FRAME (no spillover)
#   plus len(store) == Old(len(store)).
#
#   There is NO @Pure answer-key oracle and NO @ContractOnly axiom (axioms region
#   empty). The postcondition is fully GROUNDED in `value` and the read-only
#   metadata (target/active/pk_idx), so there is no opaque marker to echo
#   (ungrounded-oracle-echo class N/A — see AXIOM_TESTS + assessment). The
#   metadata's fidelity to the real _meta is an A-REFERENCE checked by G-AX /
#   axiom_check.py in Docker; this manifest re-runs that check as the axiom lane.
#
# F2P (model_inheritance_regress.tests.ModelInheritanceTest):
#   test_create_new_instance_with_pk_equals_none            (single inheritance:
#       Profile(User); pk=None must cascade to user_ptr_id so save() inserts a NEW
#       row instead of overwriting the parent's)
#   test_create_new_instance_with_pk_equals_none_multi_inheritance  (multi
#       inheritance: Congressman(Person, Politician); the promoted-pk parent link
#       is excluded by the guard, the distinct one cascades)
# prepatch (meta.json): impl is just `store[pk_idx] = value` (no loop) — fails P2.

from pathlib import Path

INSTANCE = "django__django-12273"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The verbatim gold impl body (everything between # impl-start and # impl-end,
# markers exclusive). Every variant is produced by _swap on this anchor, so the
# frozen spec (signature + pre/post-conditions) is NEVER touched => same_spec.
# ---------------------------------------------------------------------------
_GOLD = """    k = 0
    n = len(target)
    while k < n:
        # invariants-start
        Invariant(Acc(list_pred(store)))
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(active), 1 / 2))
        Invariant(len(active) == len(target))
        Invariant(n == len(target))
        Invariant(0 <= k and k <= n)
        Invariant(len(store) == Old(len(store)))
        Invariant(0 <= pk_idx and pk_idx < len(store))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                 0 <= target[j] and target[j] < len(store)),
                                          [[target[j]]])))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                 Implies(active[j] == 1, target[j] != pk_idx)),
                                          [[target[j]]])))
        # slots written so far hold `value`
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                 Implies(active[j] == 1, store[target[j]] == value)),
                                          [[target[j]]])))
        # slots not (yet) targeted by an active link keep their entry value
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                 Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                Implies(active[j] == 1, target[j] != i)))),
                                                 store[i] == Old(store[i])),
                                          [[store[i]]])))
        Invariant(MustTerminate(n - k + 1))
        # invariants-end
        if active[k] == 1:
            store[target[k]] = value
        k = k + 1
    store[pk_idx] = value"""

assert _BASE.count(_GOLD) == 1, "gold impl-body anchor drift"

# The verbatim invariant block (reused so reject-variants that keep the gold loop
# shape can preserve every framing invariant — only the executable line changes).
_INV = """        # invariants-start
        Invariant(Acc(list_pred(store)))
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(active), 1 / 2))
        Invariant(len(active) == len(target))
        Invariant(n == len(target))
        Invariant(0 <= k and k <= n)
        Invariant(len(store) == Old(len(store)))
        Invariant(0 <= pk_idx and pk_idx < len(store))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                 0 <= target[j] and target[j] < len(store)),
                                          [[target[j]]])))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                 Implies(active[j] == 1, target[j] != pk_idx)),
                                          [[target[j]]])))
        # slots written so far hold `value`
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                 Implies(active[j] == 1, store[target[j]] == value)),
                                          [[target[j]]])))
        # slots not (yet) targeted by an active link keep their entry value
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                 Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                Implies(active[j] == 1, target[j] != i)))),
                                                 store[i] == Old(store[i])),
                                          [[store[i]]])))
        Invariant(MustTerminate(n - k + 1))
        # invariants-end"""

assert _GOLD.count(_INV) == 1, "invariant-block anchor drift"


# ===========================================================================
# POSITIVE CONTROL (soundness) — structurally-different but CORRECT impl.
# ===========================================================================
# Local-variable reshape: read active[k] and target[k] into typed locals before
# the guarded write. Same executable meaning, same data/control flow, every gold
# invariant kept VERBATIM (the prefix-write invariant still triggers on the same
# quantified target[j]/store[i]). NOT a loop-direction flip and NOT a
# forward-append against a fold, so no auto-undischargeable lemma is needed
# (directive-2/3 safe). Must verify, else SPEC-TOO-STRONG.
_POS = _swap(
    _GOLD,
    """        if active[k] == 1:
            store[target[k]] = value
        k = k + 1""",
    """        a = active[k]
        t = target[k]
        if a == 1:
            store[t] = value
        k = k + 1""",
)
POS_LOCALS = _swap(_BASE, _GOLD, _POS)


# ===========================================================================
# ADMISSIBILITY — a self-call confirming the Requires admits an F2P-shaped input.
# ===========================================================================
# The probe lives INSIDE the impl region (a module-level caller would enter the
# spec signature and break same_spec). It builds the SINGLE-INHERITANCE F2P shape
# (Profile(User) twin): store has 3 slots, exactly one active parent link whose
# target slot is distinct from the pk slot, and ESTABLISHES every Requires clause
# on that concrete in-domain input (list_pred predicates + the two quantified
# Requires + the bounds). It does NOT self-call assign_identity: a self-call would
# be recursion needing a Decreases measure the spec does not carry, which fails as
# a PROOF gap (mislabeled PRECOND-TOO-STRONG) — the django-10554 caution. If any
# Requires predicate could not be established for this normal input the block
# would fail => PRECOND-TOO-STRONG. The gold body follows verbatim so all
# obligations remain.
_ADMISS_BODY = """    # ADMISSIBILITY PROBE (single-inheritance F2P shape: store=[pk, link, other],
    # one active link at index 0 targeting slot 1 (distinct from pk slot 2)).
    # Establish the Requires predicates on this concrete in-domain input.
    s = [7, 0, 9]      # type: List[int]
    tg = [1]           # type: List[int]
    ac = [1]           # type: List[int]
    Assert(list_pred(s))
    Assert(list_pred(tg))
    Assert(list_pred(ac))
    Assert(len(ac) == len(tg))               # len(active) == len(target)
    Assert(0 <= 2 and 2 < len(s))            # 0 <= pk_idx < len(store)
    # each linked slot indexes a real store slot (0 <= target[j] < len(store))
    Assert(Forall(int, lambda j: (Implies(0 <= j and j < len(tg),
                                          0 <= tg[j] and tg[j] < len(s)),
                                   [[tg[j]]])))
    # an active linked slot is distinct from the identity slot (pk_idx == 2)
    Assert(Forall(int, lambda j: (Implies(0 <= j and j < len(tg),
                                          Implies(ac[j] == 1, tg[j] != 2)),
                                   [[tg[j]]])))
""" + _GOLD
ADMISS = _swap(_BASE, _GOLD, _ADMISS_BODY)


# ===========================================================================
# FRAME-MUTATION (MANDATORY) — target / active are read-only at Acc(...,1/2).
# ===========================================================================
# (F1) Overwrite the read-only `target` list. A rival might think it can "repair"
# a linked slot index by writing into target; at half permission this is illegal.
# Must REJECT for INSUFFICIENT PERMISSION (target.append needs full list_pred),
# NOT for a value mismatch — the gold body & every postcondition are kept
# verbatim so the rejection is attributable to the write.
# refinement: a faithful real patch that MUTATED self._meta.parents (the shared,
# process-wide model metadata dict) instead of only reading it would corrupt the
# parent-link table for EVERY instance of the model class — not the gold fix
# (which only reads parents.values()/target_field) and would break unrelated P2P
# inheritance tests (e.g. test_model_inheritance), so it would NOT resolve.
_F1_BODY = """    target.append(pk_idx)
""" + _GOLD
FRAME_WRITE_TARGET = _swap(_BASE, _GOLD, _F1_BODY)

# (F2) Overwrite the read-only `active` guard list inside the loop (flip a guard
# to 0 so the cascade is skipped "cheaply"). At half permission the store-slot
# read is fine but the write `active[k] = 0` is illegal. Must REJECT for
# INSUFFICIENT PERMISSION.
# refinement: a faithful real patch writing into self._meta (e.g. reassigning the
# parent_link entries to None to silence the cascade) would mutate shared model
# metadata and silently disable parent-link propagation for all instances — the
# opposite of the fix; F2P cascade tests would fail, so it would NOT resolve.
_F2_BODY = _swap(
    _GOLD,
    """        if active[k] == 1:
            store[target[k]] = value
        k = k + 1""",
    """        active[k] = 0
        if active[k] == 1:
            store[target[k]] = value
        k = k + 1""",
)
FRAME_WRITE_ACTIVE = _swap(_BASE, _GOLD, _F2_BODY)


# ===========================================================================
# PARTIAL-DOMAIN rivals (correct on most inputs, diverge on a sub-domain).
# ===========================================================================

# (D1) PREPATCH shape: only write the pk slot; no cascade loop at all. This is
# meta.json's model_prepatch.py exactly — the literal pre-patch bug.
# refinement: == the pre-patch `return setattr(self, self._meta.pk.attname,
# value)` with no loop over parents.values(). On a child with a distinct active
# parent link (Profile.user_ptr_id), pk=None leaves user_ptr_id pointing at the
# original parent row, so save() OVERWRITES it instead of inserting a new row —
# exactly the reported bug; F2P test_create_new_instance_with_pk_equals_none
# fails. It does NOT resolve.
# rejection source: P2 (the cascade) — an active link's target slot is not written.
_D1_BODY = "    store[pk_idx] = value"
PARTIAL_PREPATCH = _swap(_BASE, _GOLD, _D1_BODY)

# (D2) DROP-LAST active link: loop stops one short (k < n-1), so the cascade to
# the final parent link is skipped.
# refinement: a faithful real patch iterating `list(parents.values())[:-1]` would
# skip the last ancestor's target_field — in a multi-level chain the deepest
# linked slot keeps pointing at the original row, so pk=None fails to fully
# reset; the F2P new-instance test fails for that chain. NOT resolve.
# rejection source: P2 when the last active link's slot is left unwritten.
_D2_BODY = _swap(
    _GOLD,
    "    while k < n:",
    "    while k < n - 1:",
).replace("    n = len(target)\n", "    n = len(target)\n    Assert(n >= 0)\n", 1)
# (the extra Assert is just to keep the body distinct & parseable; it does not
#  rescue the dropped-last cascade.)
PARTIAL_DROP_LAST = _swap(_BASE, _GOLD, _D2_BODY)

# (D3) DROP-FIRST active link: start the loop at k=1, skipping the first parent
# link's cascade.
# refinement: a faithful real patch iterating `list(parents.values())[1:]` skips
# the first ancestor's target_field; for a child whose first parent link is the
# distinct active one (single inheritance Profile(User)), user_ptr_id is never
# reset, so save() overwrites the parent row — F2P fails. NOT resolve.
# rejection source: P2 when index-0 active link's slot is left unwritten.
_D3_BODY = _swap(
    _GOLD,
    "    k = 0\n    n = len(target)",
    "    k = 1\n    n = len(target)",
)
PARTIAL_DROP_FIRST = _swap(_BASE, _GOLD, _D3_BODY)

# (D4) WRONG CASCADE VALUE: write value+1 (not value) into the cascade slots, but
# the pk slot correctly takes value.
# refinement: a faithful real patch computing a derived value for the target_field
# (e.g. value+1, or copying the wrong field) would set user_ptr_id to a value
# DIFFERENT from the new pk; the parent FK no longer agrees with the child pk, so
# save() writes an inconsistent row / wrong join — F2P assertions on the parent
# row (Person.name == 'John') fail. NOT resolve.
# rejection source: P2 — the active slot must hold exactly `value`, not value+1.
_D4_BODY = _swap(
    _GOLD,
    "            store[target[k]] = value",
    "            store[target[k]] = value + 1",
)
PARTIAL_WRONG_VALUE = _swap(_BASE, _GOLD, _D4_BODY)

# (D5) DROP THE PK WRITE: perform the cascade loop correctly but omit the final
# identity-slot write.
# refinement: a faithful real patch dropping `setattr(self, self._meta.pk.attname,
# value)` would cascade to the parent links yet leave the child's own pk attname
# at its old value — `instance.pk = None` would not clear the child's id, so the
# identity is internally inconsistent and save() misbehaves; both F2P tests assert
# the pk/id were cleared. NOT resolve.
# rejection source: P1 — store[pk_idx] must equal value.
_D5_BODY = _swap(
    _GOLD,
    "        k = k + 1\n    store[pk_idx] = value",
    "        k = k + 1",
)
PARTIAL_DROP_PK = _swap(_BASE, _GOLD, _D5_BODY)

# (D6) INVERTED GUARD: write the cascade when active[k] != 1 (i.e. to the
# INACTIVE links) and skip the active ones; the pk write stays.
# refinement: a faithful real patch with the guard polarity flipped
# (`if not (parent_link and parent_link != pk)`) would cascade to the promoted-pk
# parent link / None entries and SKIP the genuine distinct parent link — the
# multi-inheritance F2P (Congressman) fails because the real active linked slot
# (politician_ptr_id) is never reset while an excluded slot is wrongly touched.
# NOT resolve.
# rejection source: P2 (active slots unwritten) AND P3 (an inactive link's target
# slot, which no active link reaches, is changed => unrelated-slot spillover).
_D6_BODY = _swap(
    _GOLD,
    """        if active[k] == 1:
            store[target[k]] = value
        k = k + 1""",
    """        if active[k] != 1:
            store[target[k]] = value
        k = k + 1""",
)
PARTIAL_INVERT_GUARD = _swap(_BASE, _GOLD, _D6_BODY)

# (D7) OVER-CASCADE (drop the guard): write `value` to EVERY parent-link target
# slot regardless of active, plus the pk slot.
# refinement: a faithful real patch dropping the `parent_link != self._meta.pk`
# half of the guard would re-target the promoted-pk's own parent attname through
# itself (the multi-inheritance case the PR author hit — "doesn't work for child
# models that inherit from multiple models ... created other test failures"); a
# slot that should stay untouched is overwritten, breaking PASS_TO_PASS
# inheritance behaviour. NOT resolve.
# rejection source: P3 — an inactive link's target slot (reachable when
# active[k]!=1 and that slot is targeted by no active link and != pk_idx) is
# changed, violating the unchanged-unrelated-slot clause.
_D7_BODY = _swap(
    _GOLD,
    """        if active[k] == 1:
            store[target[k]] = value
        k = k + 1""",
    """        store[target[k]] = value
        k = k + 1""",
)
PARTIAL_OVER_CASCADE = _swap(_BASE, _GOLD, _D7_BODY)


SPEC_TESTS = [
    # ---------------- soundness / admissibility positive controls ----------
    {
        "id": "pos-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_LOCALS,
        "rationale": "Structurally-different but CORRECT impl: active[k]/target[k] "
        "hoisted into typed locals before the guarded write. Same data/control "
        "flow, every gold invariant kept verbatim (the prefix-write invariant "
        "still triggers on the quantified target[j]/store[i]). A local-variable "
        "reshape (directive-2/3 safe), not a loop-direction flip — must verify, "
        "else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-single-inheritance",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "An admissibility caller on the single-inheritance F2P shape "
        "(store=[7,0,9], one active link at index 0 targeting slot 1, pk slot 2) "
        "establishes every Requires clause (list_pred predicates, len equality, "
        "the pk bound, and BOTH quantified preconditions) on a concrete in-domain "
        "input. If the precondition could not be established for this normal input "
        "the block fails => PRECOND-TOO-STRONG. No self-call (recursion would need "
        "a Decreases measure the spec lacks => proof-gap, mislabeled).",
    },

    # ---------------- frame-mutation (MANDATORY: target/active read-only) ----
    {
        "id": "frame-write-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE_TARGET,
        "refinement": "Faithful real patch that MUTATED self._meta.parents (shared, "
        "process-wide model metadata) instead of only reading parents.values()/"
        "target_field would corrupt the parent-link table for every instance of "
        "the class — not the gold read-only fix; unrelated inheritance P2P tests "
        "(e.g. test_model_inheritance) would break, so it would NOT resolve.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: target is "
        "Acc(list_pred(target),1/2); target.append needs full list_pred. The gold "
        "body and all postconditions are kept verbatim, so the rejection is "
        "attributable to the write, not a value mismatch. This is the #1 weakness "
        "class and the central probe for this read-only-input instance.",
    },
    {
        "id": "frame-write-active",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE_ACTIVE,
        "refinement": "Faithful real patch writing into self._meta (e.g. nulling "
        "parent_link entries to silence the cascade) would mutate shared model "
        "metadata and disable parent-link propagation for all instances — the "
        "opposite of the fix; F2P cascade tests fail. NOT resolve.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: active is "
        "Acc(list_pred(active),1/2); the in-loop write active[k]=0 needs full "
        "permission. Attributable to the write — gold postconditions kept verbatim.",
    },

    # ---------------- partial-domain rivals --------------------------------
    {
        "id": "partial-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_PREPATCH,
        "refinement": "== meta.json model_prepatch.py: the literal pre-patch "
        "`return setattr(self, self._meta.pk.attname, value)` with NO cascade "
        "loop. On Profile(User), pk=None leaves user_ptr_id pointing at the "
        "original parent row so save() overwrites it — the exact reported bug; "
        "F2P test_create_new_instance_with_pk_equals_none fails. NOT resolve.",
        "rationale": "Rejected by P2 (the cascade clause "
        "Forall j: active[j]==1 => store[target[j]]==value): an active link's "
        "target slot is never written. Cheap supporting near-miss carrying the "
        "real pre-patch refinement.",
    },
    {
        "id": "partial-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_DROP_LAST,
        "refinement": "Faithful real patch iterating list(parents.values())[:-1] "
        "skips the last ancestor's target_field; in a multi-level chain the "
        "deepest linked slot keeps pointing at the original row so pk=None does "
        "not fully reset — the F2P new-instance test fails for that chain. NOT "
        "resolve.",
        "rationale": "Rejected by P2 when the final active link's slot is left "
        "unwritten (loop bound k < n-1 drops the last parent link).",
    },
    {
        "id": "partial-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_DROP_FIRST,
        "refinement": "Faithful real patch iterating list(parents.values())[1:] "
        "skips the first parent link; for single inheritance Profile(User) (the "
        "first link IS the distinct active one) user_ptr_id is never reset so "
        "save() overwrites the parent row — F2P fails. NOT resolve.",
        "rationale": "Rejected by P2 when the index-0 active link's slot is left "
        "unwritten (loop starts at k=1).",
    },
    {
        "id": "partial-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_WRONG_VALUE,
        "refinement": "Faithful real patch setting the target_field to a derived "
        "value (value+1 / a wrong field) makes user_ptr_id disagree with the new "
        "child pk; the parent FK no longer matches, so save() writes an "
        "inconsistent row — F2P parent-row assertions (Person.name=='John') fail. "
        "NOT resolve.",
        "rationale": "Rejected by P2: the active slot must hold exactly `value`, "
        "not value+1.",
    },
    {
        "id": "partial-drop-pk",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_DROP_PK,
        "refinement": "Faithful real patch dropping `setattr(self, "
        "self._meta.pk.attname, value)` cascades to the parent links but leaves "
        "the child's own pk attname at its old value — instance.pk = None would "
        "not clear the child id; both F2P tests assert pk/id were cleared. NOT "
        "resolve.",
        "rationale": "Rejected by P1: store[pk_idx] must equal value, but the final "
        "identity write is omitted.",
    },
    {
        "id": "partial-invert-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_INVERT_GUARD,
        "refinement": "Faithful real patch with flipped guard polarity (cascade to "
        "the None / promoted-pk links, skip the genuine distinct one) fails the "
        "multi-inheritance F2P (Congressman): the real active linked slot "
        "(politician_ptr_id) is never reset while an excluded slot is wrongly "
        "touched. NOT resolve.",
        "rationale": "Rejected by P2 (active slots unwritten) AND P3 (an inactive "
        "link's target slot, reached by no active link and != pk_idx, is changed — "
        "unrelated-slot spillover).",
    },
    {
        "id": "partial-over-cascade",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_OVER_CASCADE,
        "refinement": "Faithful real patch dropping the `parent_link != "
        "self._meta.pk` half of the guard re-targets the promoted-pk's own parent "
        "attname through itself — exactly the multi-inheritance breakage the PR "
        "author reported ('doesn't work for child models that inherit from "
        "multiple models ... created other test failures'); a slot that must stay "
        "untouched is overwritten. NOT resolve.",
        "rationale": "Rejected by P3: an inactive link's target slot (reachable "
        "when active[k]!=1, targeted by no active link, and != pk_idx) is changed, "
        "violating the unchanged-unrelated-slot clause. The guard is load-bearing.",
    },
]


# ===========================================================================
# AXIOM LANE — the A-reference deep model (G-AX), re-run in Docker.
# ===========================================================================
# meta.json has axioms == [] (no consumed @ContractOnly axiom), but ONE
# deep_model_references[] entry of kind "A-reference": assign_identity's impl +
# its target/active/pk_idx metadata model the real patched Model._set_pk_val
# reading _meta.parents / target_field.attname / pk.attname. The trust point is
# that the deep model EQUALS the real callee on every caller-reachable input —
# exactly what axiom_check.py validates. We re-run that here as two probes:
#   (1) axiom-soundness   — drive the real patched pk setter on single- and
#       multi-inheritance twins over a value sweep; assert the three obligations
#       (P1/P2/P3) hold slot-for-slot. A disagreement => AXIOM-UNSOUND.
#   (2) axiom-containment — assert every callee-input the MODEL can reach lies in
#       the model's Requires domain: each active linked target slot is a real,
#       in-bounds attname slot AND is DISTINCT from the pk slot (the precondition
#       `active[j]==1 => target[j] != pk_idx`). A reachable input outside that
#       domain => AXIOM-TOO-WEAK-FOR-CALLER.
# The runner mounts ONLY the probe at /work, so the axiom_check.py oracle is read
# on the HOST now and embedded into each probe verbatim (pilot bug #6). Probes
# import only Django (the patched module) + stdlib, open nothing, exit(0) iff the
# obligation holds. apply_gold=True (the deep model describes POST-gold behaviour).

_AXSRC = (Path(__file__).parent / "axiom_check.py").read_text()

# axiom-soundness probe: reuse axiom_check.py's exact oracle (it already drives
# the real patched setter and asserts P1/P2/P3 over a value sweep across both
# inheritance shapes). The embedded source ends with its own
# `if __name__ == "__main__": sys.exit(main())`, so running this probe as the
# main script runs main() and exits 0 iff every obligation holds (a failed
# assertion raises => non-zero rc => AXIOM-UNSOUND). The oracle is read on the
# HOST now and embedded verbatim (the runner mounts ONLY the probe at /work).
_PROBE_SOUND = (
    "# axiom-soundness: deep model assign_identity == real patched _set_pk_val.\n"
    "# Embedded axiom_check.py oracle (read on host; /work mounts only this probe).\n"
    + _AXSRC
)

# axiom-containment probe: build the SAME structural twins and assert that every
# callee-input the model can reach is inside the model's Requires domain. The
# model abstracts active linked slots as `target[k]` with the precondition that
# each is in-bounds (0 <= target[k] < len(store)) AND, when active, distinct from
# pk_idx. We verify the real _meta cannot hand the model an active target that is
# the pk slot or an unknown attname — i.e. the abstraction never reaches outside
# its Requires.
_PROBE_CONTAIN = """# axiom-containment: every callee-input the MODEL reaches is in its Requires
# domain (active target slots are real, in-bounds, and distinct from the pk slot).
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "axcheck"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def main():
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - env guard
        print("CONTAINMENT SKIP: Django not configurable: %r" % (exc,))
        return 0

    from django.db import connection, models

    class Ancestor(models.Model):
        username = models.CharField(max_length=30)

        class Meta:
            app_label = "axcheck"

    class Child(Ancestor):
        child_id = models.AutoField(primary_key=True)
        extra = models.CharField(max_length=30, blank=True)

        class Meta:
            app_label = "axcheck"

    class LeftParent(models.Model):
        name = models.CharField(max_length=100)

        class Meta:
            app_label = "axcheck"

    class RightParent(models.Model):
        right_id = models.AutoField(primary_key=True)
        title = models.CharField(max_length=50)

        class Meta:
            app_label = "axcheck"

    class MultiChild(LeftParent, RightParent):
        state = models.CharField(max_length=2)

        class Meta:
            app_label = "axcheck"

    for M in (Ancestor, Child, LeftParent, RightParent, MultiChild):
        with connection.schema_editor() as editor:
            editor.create_model(M)

    checked = 0
    for M in (Child, MultiChild):
        inst = M.objects.create(**(
            {"username": "u", "extra": "x"} if M is Child
            else {"name": "n", "title": "t", "state": "PA"}))
        meta = inst._meta
        # The model's slot layout: the set of concrete attnames the operation can
        # read/write (mapping.md: store indexed by attname).
        attnames = sorted({f.attname for f in meta.concrete_fields})
        slot = {a: i for i, a in enumerate(attnames)}
        pk_attname = meta.pk.attname
        assert pk_attname in slot, "pk attname %r not a known slot" % (pk_attname,)
        pk_idx = slot[pk_attname]

        # Exactly the model's `active` / `target` derivation (the patch guard).
        for parent_link in meta.parents.values():
            if not (parent_link and parent_link != meta.pk):
                continue  # active[k] == 0: the model never writes this slot
            tgt_attname = parent_link.target_field.attname
            # CONTAINMENT obligation 1: the active target is a real in-bounds slot
            # (0 <= target[k] < len(store)).
            assert tgt_attname in slot, (
                "AXIOM-TOO-WEAK-FOR-CALLER: active target attname %r is not a "
                "modeled store slot (out of the in-bounds Requires domain)"
                % (tgt_attname,))
            t_idx = slot[tgt_attname]
            assert 0 <= t_idx < len(attnames), (
                "AXIOM-TOO-WEAK-FOR-CALLER: target slot %d out of [0,%d)"
                % (t_idx, len(attnames)))
            # CONTAINMENT obligation 2: an ACTIVE linked slot is distinct from the
            # pk slot (precondition `active[j]==1 => target[j] != pk_idx`).
            assert t_idx != pk_idx, (
                "AXIOM-TOO-WEAK-FOR-CALLER: active target slot %d equals the pk "
                "slot %d on %s — the model's Requires forbids this and the deep "
                "model would never reach it" % (t_idx, pk_idx, M.__name__))
            checked += 1

    assert checked > 0, ("no active parent links exercised on either twin; the "
                         "containment check is vacuous")
    print("axiom-containment OK: every active linked target the model reaches is "
          "a real in-bounds store slot distinct from the pk slot (%d active links "
          "across single- and multi-inheritance twins)." % (checked,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

AXIOM_TESTS = [
    {
        "id": "ax-sound-set-pk-val",
        "axiom": "assign_identity (A-reference deep model of Model._set_pk_val)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUND,
        "rationale": "Drives the REAL patched Model._set_pk_val (via the pk "
        "property setter) on single- and multi-inheritance structural twins of the "
        "F2P models over a value sweep (None + ints, large/negative) and asserts "
        "the three contract obligations slot-for-slot: pk attname == value, every "
        "active parent-link target attname == value (the cascade), every other "
        "attname unchanged, and that the promoted-pk parent link is excluded by the "
        "guard. If the real callee disagrees with the deep model on any "
        "observation => AXIOM-UNSOUND. (Reuses axiom_check.py / G-AX verbatim.)",
    },
    {
        "id": "ax-contain-active-targets",
        "axiom": "assign_identity (A-reference deep model of Model._set_pk_val)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAIN,
        "rationale": "Enumerates exactly the callee-inputs the MODEL can reach — "
        "the active parent-link target slots derived from the real _meta by the "
        "patch guard — and asserts each lies in the model's Requires domain: a "
        "real in-bounds store slot (0 <= target[k] < len(store)) that is DISTINCT "
        "from the pk slot (the precondition active[j]==1 => target[j] != pk_idx). A "
        "reachable input outside that domain => AXIOM-TOO-WEAK-FOR-CALLER. Covering "
        "MORE (e.g. the excluded promoted-pk link) would be sound, not a defect.",
    },
]
