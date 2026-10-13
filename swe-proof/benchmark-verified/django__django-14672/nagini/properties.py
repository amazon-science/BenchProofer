# properties.py — PBT falsification battery for django__django-14672. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
#
# Defended surface (read from model.py + refinement.md + mapping.md + the gold patch):
#   identity_name_component(names: Optional[List[int]]) -> Value
#   Gold patch (django/db/models/fields/reverse_related.py:313): the through-fields
#   slot of ManyToManyRel.identity changes from `self.through_fields` to
#   `make_hashable(self.through_fields)`. The model is exactly the value that slot
#   contributes to the identity tuple. `names` (the intermediate-field-name
#   collection) is Optional[List[int]] (each name string is an int atom); the
#   produced runtime value is a tagged carrier Value(kind, items:PSeq[int]) whose
#   kind (ABSENT/MUTABLE/IMMUTABLE) faithfully reflects the runtime type and
#   determines hashability (is_hashable == kind != KIND_MUTABLE).
#
#   Precondition (ONE input, READ-ONLY):
#     (P1) Requires(Implies(names is not None, Acc(list_pred(names), 1/2)))
#          # HALF permission on the name collection => the impl may READ but not WRITE it.
#   Postcondition (five clauses):
#     (Q1) Ensures(Implies(names is not None, Acc(list_pred(names), 1/2)))  # returns read perm (frame)
#     (Q2) Ensures(Acc(Result().kind) and Acc(Result().items))             # output fields accessible
#     (Q3) Ensures(is_hashable(Result()))                                  # LOAD-BEARING: hashable slot
#          # is_hashable(v) == (v.kind != KIND_MUTABLE); this is the clause that
#          # separates the FIX (KIND_IMMUTABLE) from the PRE-PATCH (KIND_MUTABLE, the
#          # raw list) and models `hash(self.identity)` not raising TypeError.
#     (Q4) Ensures(Result().kind == canonical_names(names))                # kind pinned to grounded oracle
#          # canonical_names(None)==KIND_ABSENT(0); canonical_names(present)==KIND_IMMUTABLE(2).
#     (Q5) Ensures(Result().items == canonical_items(names))               # items pinned to grounded oracle
#          # canonical_items(None)==empty; canonical_items(present)==ToSeq(names) (order-preserving).
#
# FRAME-MUTATION lane is MANDATORY: `names` is Acc(list_pred(names), 1/2) (read-only).
#   A rival that WRITES to `names` must be rejected for INSUFFICIENT PERMISSION
#   (frame-mut). A byte-fuzzer never thinks to mutate the input; this is the
#   project's #1 weakness class. See frame-mut-append below.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q4/Q5 pin Result to
#   canonical_names(names) / canonical_items(names), which are @Pure functions
#   GROUNDED entirely in the input `names` and fully unfolded (None->ABSENT/empty;
#   present->IMMUTABLE/ToSeq(names)) — NOT an opaque answer-key or exact marker an
#   impl could echo without doing the work. There is no value an echo could carry
#   that satisfies Q4/Q5 yet is behaviourally wrong: the unique satisfier IS the
#   canonical form of the input. The honest grounded-oracle positive control is
#   therefore "produce the canonical form" (the pos controls below), not a wrong
#   echo. Q3 (is_hashable) is also grounded — but it is the load-bearing
#   discriminator, so the kind-mutable rival (= the pre-patch) is exercised
#   explicitly below as a uniqueness break. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A. identity_name_component is a pure value-returning
#   constructor with no raise/return-vs-fallthrough difference invisible to the
#   value abstraction. The only control-flow point (the None vs present branch) is
#   already pinned by Q4/Q5 (which differ between the two sub-domains) and exercised
#   by the partial-domain rivals below. No side effect, no capability token needed.
#
# AXIOM lane: meta.axioms == []. There is ONE deep_model_reference
#   (canonical_names/canonical_items/is_hashable over the Value carrier, an
#   A-reference modeling django.utils.hashable.make_hashable) but it is consumed by
#   NO axiom — the axioms region of model.py is empty (no make_hashable
#   @ContractOnly). The deep model is validated == the real make_hashable
#   out-of-band by axiom_check.py under G-AX (11 boundary + 20000 fuzz inputs).
#   Nothing in this bundle's model.py proof rests on a @ContractOnly axiom, so the
#   axiom lane has nothing to execute: AXIOM_TESTS = []. (The G-AX A-reference check
#   already lives in axiom_check.py and is re-run as its own gate.)
from pathlib import Path

INSTANCE = "django__django-14672"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`). Every spec variant _swap()s ONLY this
# block, so the edit never touches the spec (axioms/pure/pre-/post-conditions +
# the function signature). same_spec is computed over the spec_view, which elides
# every impl region, so swapping inside here is guaranteed same_spec.
_IMPL = """\
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    return Value(KIND_IMMUTABLE, ToSeq(names))"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-reordered-branches: structurally different (the PRESENT case is handled
# first via `if names is not None:` and the ABSENT case falls through to the end)
# but behaviourally identical to the gold. No loop, no fold, no induction lemma —
# just a branch reorder + a local-variable reshape (the kind is bound to a local
# `k` before constructing the Value). Keeps every obligation: the present branch
# still produces Value(KIND_IMMUTABLE, ToSeq(names)) (Q3/Q4/Q5) and the absent
# branch still produces Value(KIND_ABSENT, ToSeq(empty)). If it fails =>
# SPEC-TOO-STRONG (a faithful correct impl rejected).
_POS_REORDER = """\
    empty = []  # type: List[int]
    if names is not None:
        k = KIND_IMMUTABLE
        return Value(k, ToSeq(names))
    return Value(KIND_ABSENT, ToSeq(empty))"""

# admiss-reads: an admissibility positive control. The precondition is the
# conditional heap permission Acc(list_pred(names), 1/2) when names is present;
# this control confirms it ADMITS the reads a normal F2P-shaped input needs — for
# a present collection it reads len(names) and ToSeq(names) under the
# half-permission and asserts those reads succeed (and that the produced items
# equal canonical_items(names)) before running the gold body. If the
# half-permission did not admit a legitimate read of a normal through-fields list
# (the F2P passes ['event','invitee']), this would fail => PRECOND-TOO-STRONG. All
# asserts are over values readable under Acc(...,1/2); no write, so no proof gap
# and no permission demand beyond the spec.
_ADMISS = """\
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    # Admissibility: a normal (e.g. ['event','invitee']) through-fields list is
    # in-domain; the half-permission admits reading its length and its sequence.
    Assert(len(names) >= 0)
    Assert(ToSeq(names) == canonical_items(names))
    return Value(KIND_IMMUTABLE, ToSeq(names))"""


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — names is Acc(list_pred(names), 1/2) read-only).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-append: the rival keeps the gold body shape (absent branch verbatim,
# present branch still constructs Value(KIND_IMMUTABLE, ToSeq(names))) but, in the
# present branch, WRITES into the read-only input first: names.append(0). The
# store demands FULL write permission on list_pred(names), which the caller only
# granted at 1/2 (P1). The verifier must reject for INSUFFICIENT PERMISSION at the
# append site — before any value obligation is even reached. A byte-fuzzer never
# thinks to mutate the input; this is the project's #1 weakness class.
_FRAME_MUT = """\
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    # Frame violation: write into the read-only (Acc(...,1/2)) input.
    names.append(0)
    return Value(KIND_IMMUTABLE, ToSeq(names))"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly and changes only the function impl region.
# ---------------------------------------------------------------------------

# weak-prepatch-mutable: the FULL pre-patch behaviour reborn (== model_prepatch.py)
# — carry the raw mutable sequence straight into the identity, i.e. construct the
# present value with KIND_MUTABLE instead of KIND_IMMUTABLE. This is exactly the
# missing-make_hashable bug. Must be rejected by Q3 (is_hashable: KIND_MUTABLE is
# the one unhashable kind) AND by Q4 (canonical_names(present)==KIND_IMMUTABLE !=
# KIND_MUTABLE). The single-token discriminator the spec senses (G-DIFF).
_WEAK_MUTABLE = """\
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    return Value(KIND_MUTABLE, ToSeq(names))"""

# weak-absent-immutable: PARTIAL-DOMAIN on the ABSENT sub-domain. Correct on every
# present collection (KIND_IMMUTABLE, ToSeq(names)) but for names is None it
# returns Value(KIND_IMMUTABLE, ...) (an empty immutable) instead of KIND_ABSENT.
# is_hashable still holds (IMMUTABLE is hashable, so Q3 passes), but it diverges on
# Q4: canonical_names(None)==KIND_ABSENT(0) != KIND_IMMUTABLE(2). Targets the None
# boundary specifically.
_WEAK_ABSENT = """\
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_IMMUTABLE, ToSeq(empty))
    return Value(KIND_IMMUTABLE, ToSeq(names))"""

# weak-drop-items: PARTIAL-DOMAIN on the element sequence. Correct kind in both
# branches (Q4 and Q3 pass — the result IS hashable) but the present branch drops
# the names: it returns the EMPTY sequence instead of ToSeq(names). Correct only
# for the empty list; wrong for every non-empty through-fields collection (e.g.
# ['event','invitee']). Rejected by Q5 (Result().items == canonical_items(names)
# == ToSeq(names), which is non-empty). A make_hashable-replacement that returned a
# constant empty tuple would be hashable but would collapse all distinct
# through-fields to one identity.
_WEAK_DROP = """\
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    return Value(KIND_IMMUTABLE, ToSeq(empty))"""

# weak-truncate-first: PARTIAL-DOMAIN / off-by-one on the element sequence. Correct
# kind (Q3/Q4 pass); the present branch returns ToSeq(names).drop(1), dropping the
# FIRST name. Correct items only for the empty / single-element-equal degenerate
# case; wrong for the F2P ['event','invitee'] (yields ('invitee',)). Rejected by
# Q5 at the first element — the input that fails first. A byte-fuzzer would not
# isolate exactly the leading-element divergence.
_WEAK_TRUNC = """\
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    return Value(KIND_IMMUTABLE, ToSeq(names).drop(1))"""


SPEC_TESTS = [
    {
        "id": "pos-reordered-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different but correct: the PRESENT case is handled first "
            "(`if names is not None:`) with the kind bound to a local `k`, the "
            "ABSENT case falls through to the tail. No loop / fold / induction "
            "lemma is involved (just a branch reorder + local reshape), so the gold "
            "proof obligations are unchanged: present -> Value(KIND_IMMUTABLE, "
            "ToSeq(names)) (Q3/Q4/Q5), absent -> Value(KIND_ABSENT, empty). If it "
            "fails => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the conditional precondition Acc(list_pred(names), 1/2) (present case) "
            "must admit the reads a normal through-fields list needs (its length "
            "and its element sequence). The control reads len(names) and ToSeq(names) "
            "under the half-permission and asserts ToSeq(names)==canonical_items(names) "
            "before the gold construction. The F2P passes ['event','invitee']; if "
            "the half-permission rejected reading a legitimate input this would fail "
            "=> PRECOND-TOO-STRONG. No write, so no extra permission demand."
        ),
    },
    {
        "id": "frame-mut-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold patch reads the caller's through_fields and wraps it with "
            "make_hashable, which builds a NEW tuple (tuple(map(make_hashable, "
            "value))); it NEVER writes back into the caller's through_fields list. "
            "A faithful real patch that mutated the shared self.through_fields in "
            "place (e.g. appended/cleared it to force hashability) would corrupt the "
            "user's declared field list, change every later read of through_fields, "
            "and diverge from make_hashable's copy-not-mutate contract — it would "
            "not be the gold patch and would not faithfully resolve "
            "(test_two_m2m_through_same_model_with_different_through_fields and the "
            "retrieval/choices F2P tests depend on through_fields staying intact)."
        ),
        "rationale": (
            "REJECTED by the permission system: names is granted at "
            "Acc(list_pred(names), 1/2) (P1); the store names.append(0) demands "
            "FULL write permission on list_pred(names), which is not available, so "
            "the verifier rejects for INSUFFICIENT PERMISSION at the append site — "
            "before any value obligation. The gold construction is kept so the "
            "rejection is attributable solely to the write. If it verifies => the "
            "read-only frame is not enforced (frame-mutation, the #1 weakness class)."
        ),
    },
    {
        "id": "weak-prepatch-mutable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MUTABLE),
        "refinement": (
            "this is exactly the PRE-PATCH behaviour (model_prepatch.py): the raw "
            "mutable through_fields list carried straight into the identity tuple "
            "(no make_hashable). Its faithful real patch is the unpatched repo, "
            "where hash(self.identity) raises `TypeError: unhashable type: 'list'` "
            "whenever a proxy/inherited model with a list through_fields is placed "
            "in a set during the system checks — the exact failure of the F2P "
            "test_reverse_inherited_m2m_with_through_fields_list_hashable (and the "
            "model-check F2P cluster). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 (is_hashable(Result()): KIND_MUTABLE is the one kind "
            "is_hashable returns False for) AND by Q4 (canonical_names(present) == "
            "KIND_IMMUTABLE != KIND_MUTABLE). This is the single-token discriminator "
            "the spec senses (G-DIFF: KIND_IMMUTABLE -> KIND_MUTABLE). If it verifies "
            "=> SPEC-TOO-WEAK (the hashability fix would not be enforced)."
        ),
    },
    {
        "id": "weak-absent-immutable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ABSENT),
        "refinement": (
            "a real patch that wrapped through_fields with a normaliser that turned "
            "None into an empty tuple (e.g. make_hashable(self.through_fields or ()) "
            ") would change the identity of a relation declared WITHOUT "
            "through_fields from carrying None to carrying () — distinct from every "
            "other Django relation that genuinely has None there, breaking identity/"
            "hash equality with the unchanged super().identity siblings. It diverges "
            "from make_hashable(None) is None on the absent sub-domain, so it would "
            "not be the gold patch. Correct on every present collection, so a true "
            "PARTIAL-DOMAIN break on the None boundary. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q4 (Result().kind == canonical_names(names)): "
            "canonical_names(None) == KIND_ABSENT(0) but this returns "
            "KIND_IMMUTABLE(2). Q3 still holds (IMMUTABLE is hashable) — that is the "
            "point: the divergence is invisible to the hashability clause and is "
            "caught only by the grounded kind oracle on the None sub-domain. If it "
            "verifies => SPEC-TOO-WEAK on the absent sub-domain."
        ),
    },
    {
        "id": "weak-drop-items",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP),
        "refinement": (
            "a real patch whose canonicaliser produced a CONSTANT hashable value "
            "(e.g. always the empty tuple, `make_hashable(()) ` regardless of "
            "through_fields) would be hashable but would collapse every distinct "
            "through_fields collection to the same identity component — so two "
            "relations with different through_fields (the very thing "
            "test_two_m2m_through_same_model_with_different_through_fields "
            "distinguishes) would hash/compare equal. It would not preserve the "
            "names and would not be the gold patch. Correct only for the empty "
            "list. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q5 (Result().items == canonical_items(names) == "
            "ToSeq(names)): the present branch returns the empty sequence, which "
            "differs from ToSeq(names) for any non-empty collection (e.g. "
            "['event','invitee']). Q3/Q4 still hold (KIND_IMMUTABLE is hashable and "
            "is the right kind) — the divergence is confined to the element "
            "sequence, exactly where order-/element-preservation is pinned. If it "
            "verifies => SPEC-TOO-WEAK (names not preserved)."
        ),
    },
    {
        "id": "weak-truncate-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_TRUNC),
        "refinement": (
            "an off-by-one real patch that built the canonical tuple from "
            "through_fields[1:] would drop the first field name, yielding "
            "('invitee',) for ['event','invitee'] — a distinct identity component "
            "that breaks hash/identity equality with the correctly-canonicalised "
            "sibling relation in test_reverse_inherited_m2m_with_through_fields_list_"
            "hashable. Correct only on degenerate inputs (empty list); wrong for the "
            "F2P input. PARTIAL-DOMAIN attack on the leading element (the input that "
            "fails first). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q5 (Result().items == canonical_items(names) == "
            "ToSeq(names)): ToSeq(names).drop(1) differs from ToSeq(names) at the "
            "first element for any collection of length >= 1. Q3/Q4 hold (right "
            "kind, hashable). The divergence is the dropped leading name — a "
            "boundary a byte-fuzzer would not isolate. If it verifies => "
            "SPEC-TOO-WEAK on the first element."
        ),
    },
]

# No @ContractOnly axioms (meta.axioms == []) and no A-reference deep model
# CONSUMED by model.py's proof: the changed behaviour is modeled DIRECTLY over the
# Value carrier and pinned by Q3/Q4/Q5 (is_hashable / canonical_names /
# canonical_items, all @Pure functions of the input). The single
# deep_model_reference (the canonical_names/canonical_items/is_hashable deep model
# of django.utils.hashable.make_hashable) is consumed by NO axiom; it is validated
# == the real make_hashable out-of-band by axiom_check.py under G-AX (re-run as its
# own gate). Nothing in this bundle's proof rests on a @ContractOnly axiom, so the
# axiom lane has nothing to execute here.
AXIOM_TESTS = []
