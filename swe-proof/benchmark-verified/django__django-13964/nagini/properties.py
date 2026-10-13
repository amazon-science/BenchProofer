# properties.py — PBT falsification battery for django__django-13964.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (docstring + imports + axioms/pure regions + SaveTarget + pre/post-conditions
# untouched) and swaps ONLY text inside the # impl-start/# impl-end region; the
# runner checks each with Nagini verify + markers.same_spec. The spec_view elides
# the whole impl region (markers + nested invariants), so editing anything there
# — including the loop invariants — preserves same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   adopt_referenced_key_if_unset(target: SaveTarget, related_key: List[int]) -> None
#   models the gold one-line widening `getattr(self, field.attname) is None`
#   -> `... in field.empty_values` in Model._prepare_related_fields_for_save:
#   when the local FK attribute holds an EMPTY PLACEHOLDER, adopt the referenced
#   object's stored key into it; otherwise leave a deliberate key untouched.
#
#   target.fk : Optional[List[int]]   None=absent numeric marker, []=empty string
#                                     '', non-empty=concrete textual key.
#   related_key : List[int]           obj.pk, the saved referenced key; non-empty
#                                     (len>0) — held READ-ONLY at Acc(.,1/2).
#
#   Load-bearing postcondition clauses (the defended surface):
#     (post-a) target.fk is not None  AND  Acc(list_pred(target.fk))  AND
#              len(target.fk) > 0                       [always ends non-empty]
#     (post-1) Implies(Old(is_empty_placeholder(target.fk)),
#                      stored_seq(target.fk) == ToSeq(related_key))
#              [if it WAS an empty placeholder (None OR []), it now holds the
#               referenced key's EXACT contents — the crux the patch adds for []]
#     (post-2) Implies(not Old(is_empty_placeholder(target.fk)),
#                      target.fk is Old(target.fk) and
#                      stored_seq(target.fk) == Old(stored_seq(target.fk)))
#              [a deliberate non-empty key preserved, same object + same contents]
#     (frame)  Requires/Ensures Acc(list_pred(related_key), 1/2) — related_key is
#              READ-ONLY; any write to it must fail for INSUFFICIENT PERMISSION.
#
#   is_empty_placeholder / stored_seq are GROUNDED @Pure helpers over the args
#   (value is None or len(value)==0 ; ToSeq(value)) — NOT an opaque answer-key
#   oracle. So there is no "wrong echo" to build; see 'assessment'. The positive
#   control is the honest cheapest correct impl.
#
# F2P: test_save_fk_after_parent_with_non_numeric_pk_set_on_child — child with a
#      textual-PK FK, parent saved after assignment; child.parent_id must end
#      'jeff', not '' (the empty-string adoption the patch adds).
# Key P2P: test_save_nullable_fk_after_parent_with_to_field (a deliberate key is
#      left as-is) and the numeric absent-marker adoption (pre-existing behaviour).

from pathlib import Path

INSTANCE = "django__django-13964"
FLOAT_ENCODING = None  # meta.json float_encoding == null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen GOLD impl region (lines 107-125 of model.py): the only text any
# rival edits. The loop builds a fresh copy `adopted` of `related_key`'s contents
# (front-recursive ToSeq(...).take(i) invariant), then assigns it to target.fk —
# but ONLY when the attribute held an empty placeholder.
# ---------------------------------------------------------------------------
_GOLD_BODY = """    if is_empty_placeholder(target.fk):
        # Adopt the referenced object's stored key into the local attribute.
        adopted = []  # type: List[int]
        i = 0
        while i < len(related_key):
            # invariants-start
            Invariant(Acc(list_pred(related_key), 1 / 2))
            Invariant(Acc(list_pred(adopted)))
            Invariant(len(related_key) > 0)
            Invariant(0 <= i and i <= len(related_key))
            Invariant(len(adopted) == i)
            Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
            Invariant(MustTerminate(len(related_key) - i + 1))
            # invariants-end
            adopted.append(related_key[i])
            i = i + 1
        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
        target.fk = adopted"""


# === POSITIVE CONTROL (soundness, expect verify) ===========================
# Branch-reorder: handle the "deliberate non-empty key" case FIRST (do nothing,
# fall through), and build/adopt in the else. Same executable meaning; every gold
# invariant + the final framing Assert kept verbatim. This is a guard inversion /
# branch reorder (directive-3 safe): it does NOT flip the loop direction or use
# forward-append against a front-recursive fold, so no auto-undischargeable lemma
# is needed — the same forward-build proof carries unchanged. If a faithful
# correct impl like this cannot verify -> SPEC-TOO-STRONG.
_POS_BODY = """    if not is_empty_placeholder(target.fk):
        # A deliberately-set, non-empty stored key: leave it untouched.
        pass
    else:
        # Adopt the referenced object's stored key into the local attribute.
        adopted = []  # type: List[int]
        i = 0
        while i < len(related_key):
            # invariants-start
            Invariant(Acc(list_pred(related_key), 1 / 2))
            Invariant(Acc(list_pred(adopted)))
            Invariant(len(related_key) > 0)
            Invariant(0 <= i and i <= len(related_key))
            Invariant(len(adopted) == i)
            Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
            Invariant(MustTerminate(len(related_key) - i + 1))
            # invariants-end
            adopted.append(related_key[i])
            i = i + 1
        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
        target.fk = adopted"""

POS_REORDER = _swap(_BASE, _GOLD_BODY, _POS_BODY)


# === ADMISSIBILITY (expect verify) =========================================
# A separate top-level caller would break same_spec (spec_view only elides the
# impl region — any module-level decl enters the spec signature). So the
# admissibility check lives INSIDE the impl region, inserted right after
# `# impl-start`, before any gold obligation. It constructs F2P-shaped inputs and
# asserts every Requires clause is establishable on them: a non-empty referenced
# key (len>0, list_pred) and an empty-string-placeholder local attribute ([],
# list_pred, is_empty_placeholder True). A self-call is avoided (it would need a
# Decreases/framing the spec doesn't carry — a proof gap, not a spec defect). If
# this block cannot verify, the precondition is unsatisfiable for a normal input
# -> PRECOND-TOO-STRONG. Everything after is the gold body verbatim.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: an F2P-shaped input establishes every Requires clause.
    # related_key: a non-empty referenced key ('j' = 106) — Requires(len>0) +
    # Acc(list_pred(.,1/2)); local attribute: the empty-string placeholder [] —
    # Acc(list_pred) + is_empty_placeholder True (the case the patch fills).
    probe_rk = [106]  # type: List[int]
    Assert(list_pred(probe_rk))
    Assert(len(probe_rk) > 0)
    probe_fk = []  # type: List[int]
    Assert(list_pred(probe_fk))
    Assert(is_empty_placeholder(probe_fk))
    Assert(not is_empty_placeholder(probe_rk))"""

ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === FRAME-MUTATION (uniqueness, expect reject — INSUFFICIENT PERMISSION) ===
# related_key is held READ-ONLY at Acc(list_pred(related_key), 1/2) (required AND
# ensured). This rival WRITES to it (appends a sentinel) while otherwise running
# the gold body. With only half permission the write cannot verify; the rejection
# is attributable to INSUFFICIENT PERMISSION on related_key, not to a value
# postcondition. The gold invariants/asserts are kept verbatim so the failure is
# isolated to the illegal write. (The #1 weakness class; mandatory because the
# input is read-only.)
# refinement: a faithful real patch that mutated obj.pk (the referenced object's
# saved primary key) during the child's save — e.g. obj.pk.append(...) / rewrote
# obj's stored key — would corrupt the ALREADY-SAVED parent's identity in memory.
# The F2P/P2P tests assert child.parent_id adopts the parent's key while the
# parent row's key is unchanged (parent.save() already wrote 'jeff'); mutating
# obj.pk would change the parent's pk under the relation and break those
# assertions (and any later read of the parent) — it would NOT resolve.
# rejection source: the permission system (Acc(list_pred(related_key), 1/2) is
# read-only; .append requires full list_pred permission).
_FRAME_BODY = _swap(
    _GOLD_BODY,
    "        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))\n        target.fk = adopted",
    "        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))\n"
    "        # FRAME-MUTATION RIVAL: write to the READ-ONLY related_key (Acc(.,1/2)).\n"
    "        # Must fail for INSUFFICIENT PERMISSION (append needs full list_pred).\n"
    "        related_key.append(0)\n"
    "        target.fk = adopted",
)
FRAME_WRITE = _swap(_BASE, _GOLD_BODY, _FRAME_BODY)


# === PARTIAL-DOMAIN: None-only (uniqueness, expect reject) =================
# This is the PRE-PATCH behaviour re-expressed: treat ONLY the absent marker None
# as unset (`if target.fk is None:`), leaving the empty-string placeholder []
# untouched. Correct on the None sub-domain (numeric absent marker) and on the
# deliberate-key sub-domain; DIVERGES exactly on the empty-string [] sub-domain —
# the case the patch adds. On that input the attribute stays [] so it does not end
# non-empty.
# refinement: this is literally the buggy pre-patch code (`getattr(self,
# field.attname) is None`). The F2P test
# test_save_fk_after_parent_with_non_numeric_pk_set_on_child sets a textual-PK FK
# whose attname starts as '' (empty string); pre-patch leaves it '' instead of
# adopting 'jeff' -> child.parent_id == '' != 'jeff' -> the test FAILS, it is the
# exact bug the patch fixes, so it does NOT resolve.
# rejection source: post-a Ensures(len(target.fk) > 0) (the [] case leaves it
# empty) AND post-1 stored_seq(target.fk)==ToSeq(related_key) (the [] placeholder
# is not filled). This is the model_prepatch.py G-DIFF failure.
_NONE_ONLY_BODY = _swap(
    _GOLD_BODY,
    "    if is_empty_placeholder(target.fk):",
    "    if target.fk is None:",
)
NONE_ONLY = _swap(_BASE, _GOLD_BODY, _NONE_ONLY_BODY)


# === PARTIAL-DOMAIN: drop-last-element (uniqueness, expect reject) =========
# Adopt the referenced key but stop ONE short (`while i < len(related_key) - 1`),
# so the adopted key is a proper prefix missing its last code point. Correct in
# control flow (fires on every placeholder) and ends non-empty for keys of length
# >= 2, but the CONTENTS are wrong by the last character. This attacks whether
# post-1 pins the EXACT contents, not merely non-emptiness. The front-recursive
# invariant ToSeq(adopted)==ToSeq(related_key).take(i) still holds during the
# (shorter) loop; the gold framing Assert is a tautology and is kept verbatim.
# refinement: a faithful patch doing `setattr(self, field.attname, obj.pk[:-1])`
# (a stray slice) would store a truncated key — child.parent_id == 'jef' not
# 'jeff'; the F2P assertEqual(child.parent_id, 'jeff') would FAIL -> NOT resolve.
# rejection source: post-1 Ensures(stored_seq(target.fk) == ToSeq(related_key))
# — take(len-1) != the full sequence (and for a length-1 key, post-a len>0 too).
_DROP_LAST_BODY = _swap(
    _GOLD_BODY,
    "        while i < len(related_key):",
    "        while i < len(related_key) - 1:",
)
DROP_LAST = _swap(_BASE, _GOLD_BODY, _DROP_LAST_BODY)


# === VALUE DOUBLE-MASK: ignore the input, store a plausible non-empty key ===
# (uniqueness, expect reject). On the empty-placeholder path, store a FIXED
# non-empty key [0] instead of related_key's contents. This satisfies post-a
# (non-None, len>0) and never touches related_key — the cheapest impl that fakes
# "ended non-empty" without doing the adoption. It must be rejected by post-1's
# exact-contents pin, proving the oracle is grounded in related_key (not just a
# non-emptiness check that a constant could echo).
# refinement: a faithful patch doing `setattr(self, field.attname, <some constant
# / a different field's value>)` instead of obj.pk would store the WRONG key;
# child.parent_id would not equal the parent's pk 'jeff' — the F2P
# assertEqual(child.parent_id, parent.name) FAILS -> NOT resolve.
# rejection source: post-1 Ensures(stored_seq(target.fk) == ToSeq(related_key))
# — [0] != ToSeq(related_key) for an arbitrary non-empty referenced key.
_DOUBLE_MASK_BODY = _swap(
    _GOLD_BODY,
    """    if is_empty_placeholder(target.fk):
        # Adopt the referenced object's stored key into the local attribute.
        adopted = []  # type: List[int]
        i = 0
        while i < len(related_key):
            # invariants-start
            Invariant(Acc(list_pred(related_key), 1 / 2))
            Invariant(Acc(list_pred(adopted)))
            Invariant(len(related_key) > 0)
            Invariant(0 <= i and i <= len(related_key))
            Invariant(len(adopted) == i)
            Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
            Invariant(MustTerminate(len(related_key) - i + 1))
            # invariants-end
            adopted.append(related_key[i])
            i = i + 1
        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
        target.fk = adopted""",
    """    if is_empty_placeholder(target.fk):
        # VALUE DOUBLE-MASK RIVAL: store a fixed plausible non-empty key, ignoring
        # related_key. Satisfies len>0 / non-None but not the exact-contents pin.
        adopted = [0]  # type: List[int]
        target.fk = adopted""",
)
DOUBLE_MASK = _swap(_BASE, _GOLD_BODY, _DOUBLE_MASK_BODY)


# === CLOBBER: overwrite a deliberate non-empty key (uniqueness, expect reject) =
# Drop the guard entirely and ALWAYS adopt related_key. Correct on both empty
# placeholders (None and []); DIVERGES on the deliberate-non-empty sub-domain,
# where it clobbers an existing concrete key with the referenced one. This
# attacks the faithfulness clause post-2.
# refinement: a faithful patch that dropped the `elif ...:` guard and
# unconditionally ran `setattr(self, field.attname, obj.pk)` would overwrite a
# deliberately-assigned foreign key. test_save_nullable_fk_after_parent_with_to_field
# (P2P) sets child.parent_id deliberately and asserts it is preserved after save;
# unconditional adoption would replace it -> the P2P test FAILS -> NOT resolve.
# rejection source: post-2 Ensures(Implies(not Old(is_empty_placeholder(...)),
# target.fk is Old(target.fk) and stored_seq unchanged)) — a fresh adopted list is
# NOT Old(target.fk), and its contents differ from the deliberate key in general.
_CLOBBER_BODY = _swap(
    _GOLD_BODY,
    "    if is_empty_placeholder(target.fk):\n        # Adopt the referenced object's stored key into the local attribute.\n",
    "    if True:  # CLOBBER RIVAL: drop the guard, always adopt (overwrites a key)\n        # Adopt the referenced object's stored key into the local attribute.\n",
)
CLOBBER = _swap(_BASE, _GOLD_BODY, _CLOBBER_BODY)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl (guard inverted: handle "
        "the deliberate-key case first via `if not is_empty_placeholder: pass` and "
        "adopt in the else), every gold invariant + framing Assert kept verbatim — "
        "must verify, else SPEC-TOO-STRONG. Branch reorder only (directive-2/3 "
        "safe: same forward-build proof, no dropped lemma).",
    },
    {
        "id": "admiss-empty-string",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "an F2P-shaped input (related_key=[106] non-empty, local "
        "attribute=[] the empty-string placeholder) establishes every Requires "
        "clause: len(related_key)>0, Acc(list_pred) on both, is_empty_placeholder "
        "True on []. The precondition must admit this normal input, else "
        "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-write-related-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE,
        "refinement": "a faithful patch that mutated obj.pk (the already-saved "
        "referenced object's primary key) during the child's save would corrupt "
        "the parent's in-memory identity; the F2P/P2P tests read the parent's key "
        "back (and assert child.parent_id == parent.name with the parent's key "
        "intact) and would break — it would NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: related_key is read-only at "
        "Acc(list_pred(related_key), 1/2) (required AND ensured); .append needs full "
        "list_pred permission, so the write fails for INSUFFICIENT PERMISSION. The "
        "mandatory frame-mutation probe (read-only input).",
    },
    {
        "id": "partial-none-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": NONE_ONLY,
        "refinement": "this is the buggy PRE-PATCH code (`is None` instead of `in "
        "field.empty_values`). The F2P test "
        "test_save_fk_after_parent_with_non_numeric_pk_set_on_child starts a "
        "textual-PK FK as '' and pre-patch leaves it '' -> child.parent_id == '' "
        "!= 'jeff' -> the test FAILS; it is the exact bug the patch fixes, so it "
        "does NOT resolve (= the model_prepatch.py G-DIFF failure).",
        "rationale": "rejected by post-a Ensures(len(target.fk) > 0) and post-1 "
        "stored_seq(target.fk)==ToSeq(related_key): the empty-string [] sub-domain "
        "is left untouched, so the attribute does not end non-empty / filled. "
        "Partial-domain (diverges on the [] placeholder).",
    },
    {
        "id": "partial-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_LAST,
        "refinement": "a faithful patch storing a truncated key (e.g. "
        "`setattr(self, field.attname, obj.pk[:-1])`) would write 'jef' not 'jeff'; "
        "the F2P assertEqual(child.parent_id, 'jeff') would FAIL -> NOT resolve.",
        "rationale": "rejected by post-1 Ensures(stored_seq(target.fk) == "
        "ToSeq(related_key)): the adopted prefix take(len-1) != the full referenced "
        "key (and for a length-1 key, post-a len>0 also fails). Partial-domain on "
        "CONTENTS — confirms post-1 pins exact contents, not just non-emptiness.",
    },
    {
        "id": "value-double-mask",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DOUBLE_MASK,
        "refinement": "a faithful patch storing a fixed/wrong value instead of "
        "obj.pk (e.g. a constant or a different field) would set child.parent_id to "
        "the wrong key; the F2P assertEqual(child.parent_id, parent.name) FAILS -> "
        "NOT resolve.",
        "rationale": "rejected by post-1 Ensures(stored_seq(target.fk) == "
        "ToSeq(related_key)): a fixed [0] satisfies len>0 / non-None but is not the "
        "referenced key's contents for an arbitrary non-empty related_key. Proves "
        "the oracle is GROUNDED in related_key — no non-emptiness echo verifies.",
    },
    {
        "id": "clobber-deliberate-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": CLOBBER,
        "refinement": "a faithful patch that dropped the `elif` guard and "
        "unconditionally ran `setattr(self, field.attname, obj.pk)` would overwrite "
        "a deliberately-assigned FK; test_save_nullable_fk_after_parent_with_to_field "
        "(P2P) sets the key deliberately and asserts it is preserved — the patch "
        "would FAIL it -> NOT resolve.",
        "rationale": "rejected by the faithfulness clause post-2 Ensures(Implies(not "
        "Old(is_empty_placeholder(target.fk)), target.fk is Old(target.fk) and "
        "stored_seq unchanged)): a fresh adopted list is NOT the Old object and its "
        "contents differ from the deliberate key. Partial-domain (diverges on the "
        "deliberate-non-empty sub-domain).",
    },
]


# No @ContractOnly axioms (axioms region empty; meta.json axioms == []), but the
# bundle rests on ONE A-reference deep model: `is_empty_placeholder` stands in for
# the real `getattr(self, field.attname) in field.empty_values` membership. The
# axiom lane runs the existing G-AX soundness/containment check (axiom_check.py)
# in the instance Docker image: it (a) reads the REAL field.empty_values and
# asserts its membership == is_empty_placeholder on {None, '', 'foo', '0', 'jeff'}
# for each FK field (A-reference soundness), and (b) drives the REAL changed method
# end-to-end (textual-key adoption, numeric absent-marker adoption, non-empty-key
# preservation). The probe embeds axiom_check.py's source read on the HOST at
# load time (the runner mounts only the probe at /work; model.py/axiom_check.py
# are NOT in-container), opens any file with encoding="utf-8", calls the REAL
# callee (never scrapes source), and exits 0 iff every obligation holds.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# Containment note (axiom-containment): the model's local FK attribute can reach
# exactly None (absent marker), [] (empty string ''), or a non-empty List[int]
# (a concrete textual key). The A-reference's domain (field.empty_values
# membership) is defined on ALL Python values; {None, '', concrete key} is a
# strict subset, so every caller-reachable value lies inside the A-reference's
# domain — covered. axiom_check.py exercises exactly these reachable carriers
# ({None, '', 'foo', '0', 'jeff'}), so the soundness probe doubles as the
# containment witness. Covering MORE values ([], (), {}) than the scalar FK
# attribute can reach is SOUND, not a defect.
_AX_PROBE = (
    "# Embedded axiom_check.py (A-reference: is_empty_placeholder == real "
    "field.empty_values\n"
    "# membership; end-to-end real-method adoption). Runs in the instance Docker "
    "image.\n"
    "import sys\n"
    + _AXIOM_CHECK_SRC
    + "\n\nif __name__ != '__main__':\n    pass\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-empty-values-membership",
        "axiom": "is_empty_placeholder",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "A-reference soundness + containment: runs the REAL callee in "
        "the instance image — reads the REAL field.empty_values and asserts its "
        "membership equals is_empty_placeholder on every value the local FK "
        "attribute can hold ({None, '', 'foo', '0', 'jeff'}), and drives the REAL "
        "Model._prepare_related_fields_for_save end-to-end (textual-key adoption, "
        "numeric absent-marker adoption, deliberate-key preservation). If the real "
        "membership disagrees with the deep model on any reachable value -> "
        "AXIOM-UNSOUND; a reachable value outside the covered set -> "
        "AXIOM-TOO-WEAK-FOR-CALLER. The reachable carriers are exactly the sampled "
        "set, so soundness doubles as the containment witness. flag-independent: "
        "field.empty_values is a model-level constant identical across DB backends "
        "(default sqlite3 exercised).",
    },
]
