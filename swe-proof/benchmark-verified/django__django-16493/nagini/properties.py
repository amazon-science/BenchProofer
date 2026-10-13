# properties.py — PBT falsification battery for django__django-16493.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a FULL model.py source built by region-surgery on the
# frozen model.py: we edit ONLY text inside the `# impl-start` / `# impl-end`
# region of `deconstruct_storage`, so the spec view (and therefore same_spec)
# is guaranteed identical to the frozen artifact. The runner verifies each
# variant with Nagini and compares the actual outcome to `expect`.
#
# Defended surface (the modeled changed function = FileField.deconstruct's
# storage-kwarg include/omit decision):
#   * Inputs are READ-ONLY: self.{store_id,has_producer,producer_id} are held at
#     Acc(...,1/2) in both Requires and Ensures, and each is pinned to its
#     Old(...) value. => FRAME-MUTATION attack is MANDATORY.
#   * The postcondition pins the result from a SINGLE grounded quantity:
#       Result()[1] == reported_value(has_producer, producer_id, store_id)
#       Result()[0] == (reported_value(...) != default_store_id())
#     plus two consequence clauses
#     Implies(has_producer and producer_id != default, Result()[0]) and
#     Implies(has_producer, Result()[1] == producer_id).
#     The spec is TOTAL (no domain-restricting precondition): Result() is
#     pinned on EVERY field configuration, so no wrong impl can hide on an
#     excluded corner.
#   * reported_value is a @Pure helper that is FULLY UNFOLDED
#     (producer_id if has_producer else store_id) — a function of the args, NOT
#     an opaque answer-key oracle. So there is NO "wrong echo": echoing it IS
#     doing the work. (Ungrounded-oracle echo is therefore N/A; we include an
#     honest cheapest-impl positive control instead — see assessment.)
#   * The fix is: the include/omit guard derives from the SAME reported value,
#     not from the already-evaluated store. The pre-patch differs exactly on the
#     producer-evaluates-to-default sub-domain (the F2P).
#
# No @ContractOnly axioms / A-reference deep models in this bundle (axioms[]
# empty; pure identity/decision logic modelled deeply) => AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-16493"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact, frozen impl region of `deconstruct_storage` (everything BETWEEN the
# markers). All variants replace ONLY this block, so same_spec is guaranteed.
_GOLD_IMPL = """    # Compute the value to report first (producer if present, else store),
    # then decide inclusion from that same value.
    if self.has_producer:
        value = self.producer_id
    else:
        value = self.store_id
    included = value != default_store_id()
    return (included, value)"""

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"


def _impl(body):
    """Build a full model.py variant by replacing the gold impl body."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY: inputs are read-only at Acc(...,1/2)).
#    A rival that WRITES to a read-only input (self.store_id) before computing.
#    The compute/return is the gold logic verbatim, so the rejection is
#    attributable ONLY to the write: at 1/2 permission a field-store is not
#    writable. Must fail for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------
_FRAME_MUTATION = """    # ATTACK: overwrite the read-only input store_id (held at Acc(...,1/2)).
    # The remaining logic is the gold logic verbatim; only the write is added,
    # so a rejection is attributable solely to the insufficient permission.
    self.store_id = default_store_id()
    if self.has_producer:
        value = self.producer_id
    else:
        value = self.store_id
    included = value != default_store_id()
    return (included, value)"""

# ---------------------------------------------------------------------------
# 2. PARTIAL-DOMAIN: the pre-patch buggy guard.
#    value is still the producer-or-store, but inclusion is decided from the
#    already-evaluated concrete store (self.store_id) rather than from `value`.
#    Correct on every configuration EXCEPT producer-evaluates-to-default.
#    This is byte-for-byte the pre-fix `if self.storage is not default_storage`.
# ---------------------------------------------------------------------------
_PREPATCH_GUARD = """    # ATTACK (= the pre-fix bug): decide inclusion from the evaluated store,
    # not from the reported value. Diverges exactly on producer-returns-default.
    if self.has_producer:
        value = self.producer_id
    else:
        value = self.store_id
    included = self.store_id != default_store_id()
    return (included, value)"""

# ---------------------------------------------------------------------------
# 3. PARTIAL-DOMAIN: always-include.
#    Reports the right value but ALWAYS includes (never omits). Correct on every
#    configuration whose reported value is non-default; diverges on the
#    no-producer/default-store case, which must be OMITTED.
# ---------------------------------------------------------------------------
_ALWAYS_INCLUDE = """    # ATTACK: always include the storage kwarg (never omit the default store).
    if self.has_producer:
        value = self.producer_id
    else:
        value = self.store_id
    included = True
    return (included, value)"""

# ---------------------------------------------------------------------------
# 4. DROP-PRODUCER-PREFERENCE: report the evaluated store, never the producer.
#    Violates the consequence clause Implies(has_producer, Result()[1] ==
#    producer_id) on any field built from a producer (the inclusion flag may
#    even still be right, but the REPORTED VALUE is wrong).
# ---------------------------------------------------------------------------
_DROP_PRODUCER = """    # ATTACK: always report the concrete store, dropping the producer preference.
    value = self.store_id
    included = value != default_store_id()
    return (included, value)"""

# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROL (soundness): a structurally-different but CORRECT impl.
#    Decide the reported value with a single conditional expression and decide
#    inclusion via an explicit if/else (the gold uses a statement-if for the
#    value and a direct boolean for inclusion). Same result on every input;
#    no new proof obligation (no loop/lemma) is introduced, so the gold proof
#    still discharges. Must VERIFY (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------
_POS_CONTROL = """    # CORRECT, structurally different: ternary for the value, explicit if/else
    # for inclusion. Logically identical to the gold; no new proof obligation.
    value = self.producer_id if self.has_producer else self.store_id
    if value != default_store_id():
        included = True
    else:
        included = False
    return (included, value)"""

# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY: the (total) spec admits a normal (incl. F2P-shaped) input.
#    The precondition is only the read-only fractional permissions — no field
#    configuration is excluded. Inside the impl region we Assert the exact F2P
#    consequence: under a producer whose identity is distinct from the default
#    (every real-world producer, incl. one that EVALUATES to the default store,
#    i.e. store_id may be default) the impl yields included == True with
#    value == producer_id. If the spec/permissions were contradictory or
#    over-strong these could not be established. The body remains the gold
#    logic so it MUST verify.
# ---------------------------------------------------------------------------
_ADMISSIBILITY = """    # ADMISSIBILITY: the spec is total (no domain-restricting precondition);
    # confirm it admits a producer-shaped field, incl. the F2P
    # producer-returns-default case, rather than excluding it.
    if self.has_producer:
        value = self.producer_id
    else:
        value = self.store_id
    included = value != default_store_id()
    # A real-world producer is a distinct object from the default store: for
    # every such field the reported value is the producer and it is included,
    # regardless of what the producer evaluates to (store_id may be default).
    Assert(Implies(self.has_producer and self.producer_id != default_store_id(),
                   included and value == self.producer_id))
    return (included, value)"""


SPEC_TESTS = [
    {
        "id": "frame-mutation-store-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUTATION),
        "refinement": (
            "FileField.deconstruct() is a pure reduction: it READS self.storage / "
            "_storage_callable and returns the (name, path, args, kwargs) tuple — it "
            "never reassigns self.storage. A faithful patch that overwrites self.storage "
            "would corrupt the live field object (every later use of the field sees the "
            "clobbered store), so it would break the broad deconstruct/migration P2P "
            "suite and would not be a faithful skeleton of the gold hunk. The model pins "
            "all three attributes to Old(...) at Acc(...,1/2); a write is rejected for "
            "insufficient permission."
        ),
        "rationale": (
            "Rejection from the permission system: self.store_id is held at Acc(...,1/2) "
            "(read-only) in Requires and Ensures; assigning to it requires full permission "
            "the function does not hold. Mechanical byte-fuzzers never mutate the input."
        ),
    },
    {
        "id": "partial-domain-prepatch-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_GUARD),
        "refinement": (
            "This is byte-for-byte the pre-fix `if self.storage is not default_storage:` "
            "(guard on the already-evaluated store, value still the producer). Its faithful "
            "real patch is exactly the pre-patch code, which OMITS the storage kwarg for a "
            "field built from a callable that returns default_storage. That fails the F2P "
            "test_deconstruction_storage_callable_default "
            "(`assertIs(kwargs['storage'], callable_default_storage)`) because the key is "
            "absent. It does NOT resolve."
        ),
        "rationale": (
            "Rejection from postcondition clause "
            "Result()[0] == (reported_value(has_producer,producer_id,store_id) != default). "
            "On has_producer=True, producer_id!=0, store_id==0 the spec demands included=True "
            "but this impl computes included = (store_id != 0) = False. Also fails "
            "Implies(has_producer and producer_id != default, Result()[0])."
        ),
    },
    {
        "id": "partial-domain-always-include",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_INCLUDE),
        "refinement": (
            "A faithful patch that always sets kwargs['storage'] (never omits the default "
            "store) would emit `storage=default_storage` in the deconstruct kwargs of every "
            "field that uses the default store. The existing deconstruction P2P tests assert "
            "the storage kwarg is ABSENT when the field uses default_storage (the canonical "
            "default is re-supplied automatically on rebuild); always-include breaks those. "
            "It does NOT resolve."
        ),
        "rationale": (
            "Rejection from postcondition clause "
            "Result()[0] == (reported_value(...) != default). On has_producer=False, "
            "store_id==0 the spec demands included=False (omit) but this impl returns True."
        ),
    },
    {
        "id": "drop-producer-preference",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_PRODUCER),
        "refinement": (
            "Reporting the evaluated concrete store instead of the held callable corresponds "
            "to `kwargs['storage'] = self.storage` rather than "
            "`getattr(self, '_storage_callable', self.storage)`. The rebuilt field would lose "
            "the deferred callable, so the existing test_deconstruction "
            "(`assertIs(storage, callable_storage)`) fails — the kwarg holds the evaluated "
            "store, not the callable. It does NOT resolve."
        ),
        "rationale": (
            "Rejection from consequence clause Implies(has_producer, Result()[1] == "
            "self.producer_id) (and Result()[1] == reported_value(...)). On has_producer=True, "
            "producer_id != store_id, this impl returns value == store_id != producer_id."
        ),
    },
    {
        "id": "pos-control-ternary-explicit-inclusion",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_CONTROL),
        "rationale": (
            "A correct impl with a different executable shape (ternary for the value, explicit "
            "if/else for the inclusion flag) computes the identical result on every input and "
            "introduces no new proof obligation (no loop/lemma). It must verify; otherwise the "
            "postcondition would be SPEC-TOO-STRONG (rejecting a faithful correct impl)."
        ),
    },
    {
        "id": "admissibility-producer-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISSIBILITY),
        "rationale": (
            "The precondition (read-only fractional permissions only — the spec is total, "
            "no field configuration excluded) must ADMIT a producer-shaped field, including "
            "the F2P producer-returns-default case. The in-region Assert (under a producer "
            "distinct from the default — every real-world producer — the impl yields "
            "included=True with value==producer_id even when store_id is default) verifies "
            "only if the spec/permissions are consistent and not over-strong; otherwise "
            "PRECOND-TOO-STRONG."
        ),
    },
]

# No @ContractOnly axioms and no A-reference deep models in this bundle
# (meta.json axioms == [], deep_model_references == []; the behaviour is pure
# identity/decision logic modelled deeply, G-AX vacuous). Nothing to probe.
AXIOM_TESTS = []
