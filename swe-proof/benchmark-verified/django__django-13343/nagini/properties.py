# properties.py — PBT falsification battery for django__django-13343.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py variant built by region-surgery — we swap
# text ONLY inside a `# impl-start` / `# impl-end` region, so the frozen spec
# (axioms / pure / pre / post-conditions, signatures) is BYTE-IDENTICAL to
# model.py and `same_spec` holds by construction. The runner checks each variant
# with the real Nagini verifier on the host.
#
# Defended surface (read from model.py):
#   configure(field, given, given_is_producer, evaluated) -> None
#     FULL write permission on field.{store,has_producer,producer_id}.
#     Load-bearing Ensures:
#       (c1) field.has_producer == given_is_producer
#       (c2) Implies(given_is_producer, field.producer_id == given)
#       (c2') Implies(not given_is_producer,
#                     field.producer_id == Old(field.producer_id))
#       (c3) field.store == (evaluated if given_is_producer else given)
#   describe_store(field) -> Optional[int]
#     READ-ONLY input: Acc(field.{store,has_producer,producer_id}, 1/2).
#     Load-bearing Ensures:
#       (d1) (field.store == default_store_id()) == (Result() is None)
#       (d2) Implies(store != default and has_producer,     Result() == producer_id)
#       (d3) Implies(store != default and not has_producer, Result() == store)
#
# The result oracle is GROUNDED: Result() is pinned to the actual input fields
# (producer_id / store), not to an opaque @Pure answer-key. There is therefore no
# "wrong echo that still verifies" — see ungrounded-oracle note in 'assessment';
# UNGROUNDED-ORACLE is covered by an honest cheapest-impl positive control.
#
# No @ContractOnly axioms in this bundle (meta.axioms == []); the two facts the
# model relies on are A-references validated by axiom_check.py / G-AX, not
# consumed obligations the verifier discharges. AXIOM_TESTS is therefore empty
# (the A-reference soundness lives in G-AX, re-run separately). See 'assessment'.

from pathlib import Path

INSTANCE = "django__django-13343"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact impl-region text in model.py (the ONLY editable spans).
# ---------------------------------------------------------------------------

# configure's impl region (between its # impl-start / # impl-end).
_CONFIGURE_IMPL = """    field.store = given
    if given_is_producer:
        # Record a reference to the original producer, then adopt the concrete
        # store it yields as the live store.
        field.has_producer = True
        field.producer_id = given
        field.store = evaluated
    else:
        field.has_producer = False"""

# describe_store's impl region.
_DESCRIBE_IMPL = """    if field.store == default_store_id():
        return None
    if field.has_producer:
        return field.producer_id
    return field.store"""


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -----------------------------------------------------------------------
    # (1) FRAME-MUTATION  (MANDATORY — describe_store input is read-only)
    # -----------------------------------------------------------------------
    # describe_store holds only Acc(field.store, 1/2): it may READ the field but
    # NOT write it. This rival overwrites field.store to satisfy the (d1) None/
    # not-None postcondition vacuously — collapse a producer/non-default store to
    # the default so that returning None type-checks. With half permission the
    # WRITE itself is illegal, so the verifier must reject this for INSUFFICIENT
    # PERMISSION before it ever reasons about the postcondition. The gold
    # postcondition clauses are kept verbatim (frozen by same_spec) so the
    # rejection is attributable to the mutation, not to a contract change.
    {
        "id": "frame-mutate-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DESCRIBE_IMPL,
            "    # FRAME VIOLATION: write to a read-only (1/2-permission) input.\n"
            "    field.store = default_store_id()\n"
            "    return None"),
        "refinement": (
            "A faithful real patch behaving this way would set "
            "self.storage = default_storage inside deconstruct() and always omit "
            "the storage kwarg. The F2P test_deconstruction asserts "
            "deconstruct()['storage'] is callable_storage — the key would be "
            "ABSENT, so the test fails: verify would not resolve. But it never "
            "even reaches that argument here; deconstruct must not mutate the "
            "field, which is exactly the 1/2-permission guard."),
        "rationale": (
            "Reject from the PERMISSION SYSTEM: Acc(field.store, 1/2) grants read "
            "only; `field.store = ...` needs full permission. Insufficient-"
            "permission error, not a postcondition failure."),
    },

    # Supporting frame-mutation: write producer_id (also 1/2). Same permission
    # wall; cheap corruption that still carries a refinement.
    {
        "id": "frame-mutate-producer-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DESCRIBE_IMPL,
            "    # FRAME VIOLATION: clobber a read-only (1/2-permission) field.\n"
            "    field.producer_id = field.store\n"
            "    if field.store == default_store_id():\n"
            "        return None\n"
            "    if field.has_producer:\n"
            "        return field.producer_id\n"
            "    return field.store"),
        "refinement": (
            "Rewriting _storage_callable inside deconstruct() to equal the "
            "evaluated store would re-introduce the original bug (emit the "
            "evaluated store, not the callable) and also mutate field state during "
            "a read-only query; F2P would fail. The verifier never gets there — "
            "the write to a 1/2-permission field is rejected first."),
        "rationale": (
            "Reject from the PERMISSION SYSTEM: producer_id is held at 1/2; the "
            "assignment requires full permission."),
    },

    # -----------------------------------------------------------------------
    # (2) PARTIAL-DOMAIN — describe_store, wrong on the NON-producer sub-domain
    # -----------------------------------------------------------------------
    # Correct on every producer input (returns producer_id when has_producer) and
    # on the default-store input (returns None), but on a non-default store with
    # NO producer it returns producer_id instead of store. Violates clause (d3).
    {
        "id": "partial-domain-nonproducer-returns-producer-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DESCRIBE_IMPL,
            "    if field.store == default_store_id():\n"
            "        return None\n"
            "    # WRONG on the non-producer sub-domain: emit producer_id even when\n"
            "    # no producer was recorded (clause d3 demands the live store).\n"
            "    return field.producer_id"),
        "refinement": (
            "Faithful patch: kwargs['storage'] = getattr(self, '_storage_callable', "
            "self.storage) but for a concrete (non-callable) store there is no "
            "_storage_callable; emitting producer_id (a stale/zero id) instead of "
            "self.storage breaks the concrete-store round-trip — P2P "
            "test_callable_*/concrete deconstruction asserts the storage kwarg is "
            "the supplied store, so it fails to resolve."),
        "rationale": (
            "Reject from postcondition clause (d3): Implies(store != default and "
            "not has_producer, Result() == field.store). Here Result()==producer_id "
            "!= store on that sub-domain."),
    },

    # -----------------------------------------------------------------------
    # (3) UNIQUENESS — describe_store SWAPS producer/store (the literal gold bug,
    #     restricted to the producer sub-domain so it is not the whole prepatch)
    # -----------------------------------------------------------------------
    # Returns the live store even when a producer was recorded: this is exactly
    # the bug the issue reports (deconstruct emits the evaluated store, not the
    # callable). Violates clause (d2). If it verified, the spec would be too weak
    # to sense the very bug it exists to catch.
    {
        "id": "uniqueness-producer-returns-evaluated-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DESCRIBE_IMPL,
            "    if field.store == default_store_id():\n"
            "        return None\n"
            "    # THE BUG: emit the live (evaluated) store even when a producer\n"
            "    # was recorded — freezes the one runtime store into the\n"
            "    # description (clause d2 demands the original producer_id).\n"
            "    return field.store"),
        "refinement": (
            "This is the gold pre-image kwargs['storage'] = self.storage. F2P "
            "test_deconstruction asserts deconstruct()['storage'] is "
            "callable_storage; self.storage is the EVALUATED store (a different "
            "object, model precondition evaluated != given), so assertIs fails: "
            "verify would NOT resolve. This is the exact verify-implies-resolve "
            "break the spec must block."),
        "rationale": (
            "Reject from postcondition clause (d2): Implies(store != default and "
            "has_producer, Result() == field.producer_id). With a producer, "
            "store == evaluated != producer_id == given (configure c2/c3 + "
            "precondition evaluated != given), so Result()==store violates it."),
    },

    # -----------------------------------------------------------------------
    # (4) UNIQUENESS — configure records the EVALUATED store as the producer id
    # -----------------------------------------------------------------------
    # has_producer is set correctly, store is set correctly, but producer_id is
    # set to `evaluated` rather than the original `given`. Round-trip would then
    # emit the evaluated store from describe_store — the same observable bug,
    # introduced at the configuration site. Violates clause (c2).
    {
        "id": "uniqueness-configure-records-evaluated-as-producer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _CONFIGURE_IMPL,
            "    field.store = given\n"
            "    if given_is_producer:\n"
            "        field.has_producer = True\n"
            "        # WRONG: record the EVALUATED store as the producer id\n"
            "        # instead of the original producer `given` (clause c2).\n"
            "        field.producer_id = evaluated\n"
            "        field.store = evaluated\n"
            "    else:\n"
            "        field.has_producer = False"),
        "refinement": (
            "Faithful patch: self._storage_callable = self.storage() (the "
            "evaluated store) instead of self.storage (the callable). deconstruct "
            "then emits the evaluated store, so F2P assertIs(storage, "
            "callable_storage) fails: verify would NOT resolve."),
        "rationale": (
            "Reject from postcondition clause (c2): Implies(given_is_producer, "
            "field.producer_id == given). Here producer_id == evaluated != given "
            "(precondition evaluated != given)."),
    },

    # -----------------------------------------------------------------------
    # (5) UNIQUENESS — configure sets has_producer for a NON-producer (off-by-one
    #     on the producer flag; partial-domain on configure's else branch)
    # -----------------------------------------------------------------------
    {
        "id": "uniqueness-configure-flag-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _CONFIGURE_IMPL,
            "    field.store = given\n"
            "    # WRONG: always claim a producer was recorded (clause c1 demands\n"
            "    # has_producer == given_is_producer).\n"
            "    field.has_producer = True\n"
            "    if given_is_producer:\n"
            "        field.producer_id = given\n"
            "        field.store = evaluated"),
        "refinement": (
            "Faithful patch: always set self._storage_callable even for a concrete "
            "(non-callable) store. deconstruct would then emit producer_id for a "
            "concrete store, breaking the concrete-store P2P round-trip; verify "
            "would NOT resolve."),
        "rationale": (
            "Reject from postcondition clause (c1): field.has_producer == "
            "given_is_producer. On the else branch has_producer==True != "
            "given_is_producer==False."),
    },

    # -----------------------------------------------------------------------
    # (5b) UNIQUENESS — configure scribbles on producer_id in the NON-producer
    #     branch (the exact audit counterexample atk_7: dead-state corruption
    #     the pre-(c2') spec admitted). A faithful realization writes a bogus
    #     _storage_callable-like record even when no callable was supplied —
    #     configuration with a concrete store must record NOTHING, so clause
    #     (c2') pins producer_id to its old value on that branch.
    # -----------------------------------------------------------------------
    {
        "id": "uniqueness-configure-scribbles-producer-id-nonproducer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _CONFIGURE_IMPL,
            "    field.store = given\n"
            "    if given_is_producer:\n"
            "        field.has_producer = True\n"
            "        field.producer_id = given\n"
            "        field.store = evaluated\n"
            "    else:\n"
            "        field.has_producer = False\n"
            "        # WRONG: writes a spurious producer record for a concrete\n"
            "        # store (clause c2' demands producer_id be left untouched).\n"
            "        field.producer_id = given + 1"),
        "refinement": (
            "Faithful patch: set self._storage_callable to some non-callable "
            "sentinel even when storage is a concrete Storage. deconstruct's "
            "getattr(self, '_storage_callable', self.storage) would then emit the "
            "sentinel instead of the supplied store for every concrete-store "
            "field, breaking the P2P concrete-store deconstruction round-trip: "
            "verify would NOT resolve."),
        "rationale": (
            "Reject from postcondition clause (c2'): Implies(not "
            "given_is_producer, producer_id == Old(producer_id)). Here "
            "producer_id == given + 1 != Old(producer_id) in general."),
    },

    # -----------------------------------------------------------------------
    # (6) POSITIVE CONTROL (soundness) — describe_store, structurally different
    #     but CORRECT. Branch-reorder: handle the producer case first via an
    #     early-return guarded by `field.store != default`, default last. Keeps
    #     every clause satisfiable; no framing lemma needed (straight-line, no
    #     loop). Must VERIFY (else SPEC-TOO-STRONG).
    # -----------------------------------------------------------------------
    {
        "id": "pos-control-describe-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _DESCRIBE_IMPL,
            "    # Structurally different but equivalent: test the producer flag\n"
            "    # first, guarded by non-default; default-store case handled last.\n"
            "    if field.store != default_store_id() and field.has_producer:\n"
            "        return field.producer_id\n"
            "    if field.store != default_store_id():\n"
            "        return field.store\n"
            "    return None"),
        "rationale": (
            "A correct, reordered straight-line impl must verify: it returns "
            "producer_id for a producer (d2), store for a non-producer non-default "
            "(d3), None for the default store (d1). No loop/lemma involved."),
    },

    # -----------------------------------------------------------------------
    # (7) POSITIVE CONTROL (soundness) — configure, structurally different but
    #     CORRECT. Set has_producer/producer_id/store via a single flat branch
    #     order (assign store=evaluated inside the producer branch, no leading
    #     `field.store = given`). Must VERIFY.
    # -----------------------------------------------------------------------
    {
        "id": "pos-control-configure-reshaped",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _CONFIGURE_IMPL,
            "    # Reshaped: set every field exactly once inside its branch.\n"
            "    if given_is_producer:\n"
            "        field.has_producer = True\n"
            "        field.producer_id = given\n"
            "        field.store = evaluated\n"
            "    else:\n"
            "        field.has_producer = False\n"
            "        field.store = given"),
        "rationale": (
            "Correct, reshaped impl: producer branch sets store=evaluated, "
            "producer_id=given, has_producer=True (c1/c2/c3); else branch sets "
            "store=given, has_producer=False (c1/c3) and leaves producer_id "
            "untouched (c2' pins it to its old value — no producer reference "
            "is written when no producer is supplied). Must verify."),
    },

    # -----------------------------------------------------------------------
    # (8) ADMISSIBILITY — a positive-control caller showing the preconditions
    #     admit a normal F2P-shaped input. We add a real CALL to configure on a
    #     fresh field with a producer (given=7, given_is_producer=True,
    #     evaluated=9): given != default(0), and evaluated(9) != given(7) and
    #     != default(0). If Requires were too strong this call would fail to
    #     verify (PRECOND-TOO-STRONG).
    #
    #     The probe is hosted in describe_store's impl region, NOT configure's.
    #     Since the spec now carries a termination obligation, an obligated
    #     caller must sit at a STRICTLY GREATER level than its callee, so
    #     configure can no longer call itself: at any single level the
    #     self-call reports `Obligation leak check failed. Callee configure
    #     might not take all unsatisfied obligations from the caller.`
    #     describe_store is at MustTerminate(10) > configure's 6, so it can
    #     legally call configure; AttachmentField.__init__ is at level 1, below
    #     both. The probe asserts the POST-state of the real call (the whole
    #     point of an admissibility witness) — asserting the preconditions
    #     instead would prove nothing about whether they are satisfiable.
    # -----------------------------------------------------------------------
    {
        "id": "admiss-configure-producer-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _DESCRIBE_IMPL,
            "    # ADMISSIBILITY: a normal F2P-shaped producer input satisfies the\n"
            "    # preconditions (given=7 != default 0; evaluated=9 != given and\n"
            "    # != default). If Requires were too strong this would not verify.\n"
            "    # Hosted here because describe_store's level (10) strictly exceeds\n"
            "    # configure's (6), which the termination obligation requires of\n"
            "    # any caller; configure cannot call itself under an obligation.\n"
            "    probe = AttachmentField()\n"
            "    configure(probe, 7, True, 9)\n"
            "    Assert(probe.has_producer)\n"
            "    Assert(probe.producer_id == 7)\n"
            "    Assert(probe.store == 9)\n"
            "    if field.store == default_store_id():\n"
            "        return None\n"
            "    if field.has_producer:\n"
            "        return field.producer_id\n"
            "    return field.store"),
        "rationale": (
            "The preconditions (given != default; Implies(producer, evaluated != "
            "given and != default)) admit a representative producer input; the "
            "call to configure and the post-call asserts on its resulting state "
            "must verify (else PRECOND-TOO-STRONG). Also witnesses that the "
            "termination levels compose: describe_store(10) > configure(6) > "
            "__init__(1), so neither the construction nor the call leaks an "
            "obligation."),
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# meta.json: "axioms": []. No @ContractOnly axiom is consumed; the proof
# discharges nothing about a real callee. The two facts the model relies on
# (producer evaluation yields a distinct real Storage; default-store identity)
# are A-references already validated executably by axiom_check.py under G-AX
# (re-run separately, host-side on the real Django). There is no axiom-soundness
# or axiom-containment obligation for the verifier to falsify here.
AXIOM_TESTS = []
