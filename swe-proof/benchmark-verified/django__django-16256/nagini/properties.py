"""PBT manifest for django__django-16256 — adversarial falsification battery.

NOT a Nagini module. A record of adversarial cases the runner
(`swebench_nagini.pbt`) executes: each SPEC case is a full model.py variant that
shares the FROZEN spec (only the impl region is edited, so `same_spec` holds) and
is checked by Nagini verify; AXIOM cases are real-callee probes (none here — the
bundle consumes no @ContractOnly axiom and pins no A-reference deep model against
a separate stdlib oracle; the one library fact `await sync_to_async(f)==f` is the
deferred-form equivalence already validated by axiom_check.py / G-AX).

Defended surface (read from model.py + refinement.md + the F2P tests):

  Six modelled functions in three operation families. The three "immediate"
  forms (`create`, `get_or_create`, `update_or_create`) perform the
  relation-specific work modelled DEEPLY as a list append on the related set
  `mgr.members` plus a write of the payload slot `mgr.payload`; the three
  "deferred" forms (`acreate`, `aget_or_create`, `aupdate_or_create`) each
  delegate to their SAME-named immediate form and must reproduce its result AND
  both of its effects EXACTLY. Two independent clause families are load-bearing:

    * MEMBERSHIP — the attach equality
        ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)
      (unconditional for create/acreate; guarded by `not exists` for the
      *_or_create family, with `Implies(exists, ToSeq(mgr.members)==Old(ToSeq(
      mgr.members)))` for the located branch);

    * PAYLOAD — what the delivered object ends up carrying. `create`/`acreate`:
      `mgr.payload == requested`. Locate-or-produce: `Implies(exists,
      mgr.payload == Old(mgr.payload))` and `Implies(exists, Result().payload ==
      Old(mgr.payload))` (an already-present object is handed back untouched),
      with `Implies(not exists, ... == requested)` on the produce branch.
      Refresh-or-produce: `mgr.payload == requested` and `Result().payload ==
      requested` UNCONDITIONALLY — an already-present object is refreshed.

  plus the value pins `Result()==obj` / `Result().obj==obj` /
  `Result().created==(not exists)`.

  The PRE-PATCH bug (the real defect the gold patch fixes) is precisely a
  deferred form that delivers the object but runs a bare produce that does NOT
  attach it to THIS related set — caught by the membership clause. A SECOND
  family of rivals keeps membership exactly right and gets the payload behaviour
  of the wrong operation (refresh-or-produce that leaves an already-present
  object untouched, locate-or-produce that overwrites one) — caught by the
  payload clauses, and observed by the F2P tests that assert the delivered
  object's field value after an operation that LOCATES an existing row (where
  membership and identity are both unchanged, so only the payload discriminates).
  Both families are exercised below, in both directions.

  NO read-only input: every `mgr.members` / `mgr.payload` is held at FULL
  permission (`Acc(...)`) because the immediate forms genuinely mutate them (the
  attach, the payload write). The frame-mutation-for-insufficient-permission
  probe (mandatory only when an input is read-only `Acc(...,1/2)`) is therefore
  N/A here — see 'frame_mutation' note below; instead the membership equality
  itself defends against spurious mutation (extra/missing/wrong appends),
  exercised by the uniqueness rivals, and the payload equalities defend against
  a spurious or missing payload write.

  VACUITY / non-termination: Nagini is a partial-correctness verifier, so a
  deferred form that diverges before returning satisfies every Ensures
  vacuously while its real counterpart never resolves the awaited coroutine —
  hanging every awaiting F2P test. The `MustTerminate` obligations carried in
  every precondition (deferred 3 -> immediate 2 -> carriers 1) pin totality;
  the diverge rival below exercises them (this was the audit's P1 witness
  class: an `Invariant(True)` loop that VERIFIED under the pre-fix contract).
"""
from pathlib import Path

INSTANCE = "django__django-16256"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Unique impl-region anchors (each lives ENTIRELY inside one # impl-start /
# # impl-end block, so a _swap touches only the impl — same_spec is preserved).
# NB: the DEFERRED bodies (`return create/get_or_create/update_or_create(...)`)
# are each unique on their own; the two immediate bodies are anchored on a
# larger block that runs up to the next `def` so the anchor text is unique even
# if the two bodies were ever to coincide again.
# ---------------------------------------------------------------------------

# acreate impl body (unique)
_ACREATE_GOLD = (
    "    # Run the SAME-named immediate form on this accessor (its result is then\n"
    "    # delivered to the awaiting caller). Because it is the related-set accessor's\n"
    "    # OWN immediate form, the produced object is attached to the related set.\n"
    "    return create(mgr, obj, requested)"
)

# aget_or_create impl body (unique)
_AGOC_GOLD = "    return get_or_create(mgr, obj, exists, requested)"

# aupdate_or_create impl body (unique)
_AUOC_GOLD = "    return update_or_create(mgr, obj, exists, requested)"

# get_or_create impl body, anchored through the following `def` line so the
# anchor text appears exactly once.
_GOC_GOLD = (
    "    # impl-start\n"
    "    if exists:\n"
    "        return Outcome(obj, False, mgr.payload)\n"
    "    mgr.members.append(obj)\n"
    "    mgr.payload = requested\n"
    "    return Outcome(obj, True, requested)\n"
    "    # impl-end\n"
    "\n"
    "\n"
    "def aget_or_create"
)

# update_or_create impl body, anchored the same way.
_UOC_GOLD = (
    "    # impl-start\n"
    "    if exists:\n"
    "        mgr.payload = requested\n"
    "        return Outcome(obj, False, requested)\n"
    "    mgr.members.append(obj)\n"
    "    mgr.payload = requested\n"
    "    return Outcome(obj, True, requested)\n"
    "    # impl-end\n"
    "\n"
    "\n"
    "def aupdate_or_create"
)


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl.
#    Reorder get_or_create so the PRODUCE branch is taken first under `not
#    exists`, the LOCATE branch falls through. Same effects, different shape,
#    no loop / no induction lemma needed => must verify (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_GOC = (
    "    # impl-start\n"
    "    if not exists:\n"
    "        mgr.members.append(obj)\n"
    "        mgr.payload = requested\n"
    "        return Outcome(obj, True, requested)\n"
    "    return Outcome(obj, False, mgr.payload)\n"
    "    # impl-end\n"
    "\n"
    "\n"
    "def aget_or_create"
)


# ===========================================================================
# 1b. POSITIVE CONTROL (soundness) — the refresh-or-produce form written with
#    the payload write HOISTED out of the branch (it happens on both paths, so
#    a single write before the split is the same behaviour). Must verify: the
#    payload clauses are unconditional for this operation, so a correct impl is
#    free to write the slot once.
# ===========================================================================
_POS_UOC = (
    "    # impl-start\n"
    "    mgr.payload = requested\n"
    "    if not exists:\n"
    "        mgr.members.append(obj)\n"
    "        return Outcome(obj, True, requested)\n"
    "    return Outcome(obj, False, requested)\n"
    "    # impl-end\n"
    "\n"
    "\n"
    "def aupdate_or_create"
)


# ===========================================================================
# 2. ADMISSIBILITY — inside acreate's impl, build a FRESH F2P-shaped accessor
#    (empty related set) and self-call create on it, asserting the pinned
#    post-state, before performing the gold delegation. If the call site cannot
#    establish create's Requires for this normal input => PRECOND-TOO-STRONG.
#    Stays entirely within acreate's impl region (mgr is untouched by the
#    witness; the gold `return create(mgr, obj, requested)` is preserved).
# ===========================================================================
_ADMISS_ACREATE = (
    "    # admissibility witness: a fresh F2P-shaped accessor with an empty related\n"
    "    # set satisfies create's Requires(list_pred(members)); the pinned attach and\n"
    "    # payload post-state holds for it. If Requires could not be established here,\n"
    "    # that would be PRECOND-TOO-STRONG.\n"
    "    witness_members = []  # type: List[int]\n"
    "    witness = RelatedAccessor(witness_members, requested)\n"
    "    # RelatedAccessor.__init__ consumes list_pred(members) in its Requires and\n"
    "    # returns only Acc(self.members) / Acc(self.payload), so\n"
    "    # list_pred(witness.members) is not held after construction. Re-seat the\n"
    "    # related set to a fresh empty list literal (which carries list_pred) to\n"
    "    # re-establish create's Requires — this is a pure proof-engineering step, not\n"
    "    # a precondition weakening: an empty related set is still exactly\n"
    "    # setUpTestData's starting shape.\n"
    "    witness.members = []  # type: ignore\n"
    "    produced = create(witness, obj, requested)\n"
    "    Assert(produced == obj)\n"
    "    Assert(ToSeq(witness.members) == PSeq(obj))\n"
    "    Assert(witness.payload == requested)\n"
    "    return create(mgr, obj, requested)"
)


# ===========================================================================
# 3. UNIQUENESS — the PRE-PATCH bug for acreate: deliver the object (with the
#    right payload) but DO NOT attach it. This is model_prepatch.py's exact
#    defect. expect=reject: the membership clause
#    `ToSeq(mgr.members)==Old(ToSeq(mgr.members))+PSeq(obj)` forces the append.
# ===========================================================================
_REJ_ACREATE_NOATTACH = (
    "    # PRE-PATCH BUG re-introduced: bare produce, never attaches to THIS set.\n"
    "    mgr.payload = requested\n"
    "    return obj"
)


# ===========================================================================
# 4. UNIQUENESS — aget_or_create delegates to a LOCAL no-attach get_or_create-
#    shaped impl (inline the bug at the deferred site without touching the
#    sibling spec): the delivered identity, flag and payload are all right, but
#    there is NO append on the produced branch. expect=reject: the `not exists`
#    membership clause forces the append.
# ===========================================================================
_REJ_AGOC_NOATTACH = (
    "    # PRE-PATCH BUG: deliver (obj, created, payload) but never attach a produced\n"
    "    # object.\n"
    "    if exists:\n"
    "        return Outcome(obj, False, mgr.payload)\n"
    "    mgr.payload = requested\n"
    "    return Outcome(obj, True, requested)"
)


# ===========================================================================
# 5. UNIQUENESS / PARTIAL-DOMAIN — get_or_create that attaches on EVERY branch
#    (also on the LOCATE branch where exists=True). Correct on the produce
#    sub-domain (exists=False) but WRONG on the locate sub-domain: the located
#    object must leave the set unchanged. expect=reject: the
#    `Implies(exists, ToSeq(mgr.members)==Old(ToSeq(mgr.members)))` clause is
#    violated when exists.
# ===========================================================================
_REJ_GOC_ALWAYS_ATTACH = (
    "    # impl-start\n"
    "    mgr.members.append(obj)\n"
    "    if exists:\n"
    "        return Outcome(obj, False, mgr.payload)\n"
    "    mgr.payload = requested\n"
    "    return Outcome(obj, True, requested)\n"
    "    # impl-end\n"
    "\n"
    "\n"
    "def aget_or_create"
)


# ===========================================================================
# 6. UNIQUENESS / VALUE-PIN — get_or_create with the created flag FLIPPED
#    (created==exists instead of created==(not exists)). The membership and
#    payload effects are still pinned correctly, but the produced/located flag
#    is wrong on every input. expect=reject: `Result().created==(not exists)`
#    is violated.
# ===========================================================================
_REJ_GOC_FLIP_FLAG = (
    "    # impl-start\n"
    "    if exists:\n"
    "        return Outcome(obj, True, mgr.payload)\n"
    "    mgr.members.append(obj)\n"
    "    mgr.payload = requested\n"
    "    return Outcome(obj, False, requested)\n"
    "    # impl-end\n"
    "\n"
    "\n"
    "def aget_or_create"
)


# ===========================================================================
# 7. UNIQUENESS / DOUBLE-ATTACH — acreate via the gold delegate PLUS an extra
#    append, so the produced object is attached TWICE. expect=reject: the exact
#    sequence equality pins a SINGLE append; a second append makes the post
#    sequence `Old + PSeq(obj) + PSeq(obj)`, which is not `Old + PSeq(obj)`.
# ===========================================================================
_REJ_ACREATE_DOUBLE = (
    "    # WRONG: attach twice (extra membership row), so the set is over-extended.\n"
    "    result = create(mgr, obj, requested)\n"
    "    mgr.members.append(obj)\n"
    "    return result"
)


# ===========================================================================
# 8. UNIQUENESS / VACUITY — acreate that spins forever before the gold tail.
#    Nagini verifies partial correctness by default: without a termination
#    obligation every Ensures holds vacuously on a diverging body, yet the
#    deferred form never resolves — the awaiting caller hangs. expect=reject:
#    the MustTerminate(3) obligation in acreate's precondition rejects the
#    measure-free loop ('Loop might not take all unsatisfied obligations from
#    the context'). This was the audit's P1 witness class (the pre-fix
#    G-PANEL-1 hole).
# ===========================================================================
_REJ_ACREATE_DIVERGE = (
    "    # WRONG (vacuous): spin forever before the correct tail. Every Ensures\n"
    "    # holds vacuously (no normal exit is ever reached), yet the deferred\n"
    "    # form never delivers the produced object to the awaiting caller.\n"
    "    b = True\n"
    "    while b:\n"
    "        Invariant(True)\n"
    "        b = True\n"
    "    return create(mgr, obj, requested)"
)


# ===========================================================================
# 9. UNIQUENESS / WRONG-SIBLING (payload family, direction 1) — the deferred
#    refresh-or-produce form delegates to the LOCATE-or-produce immediate form.
#    Identity, produced flag and membership are all exactly right; the only
#    difference is that an already-present object is handed back untouched
#    instead of refreshed. expect=reject: `mgr.payload == requested` /
#    `Result().payload == requested` are unconditional for this operation.
# ===========================================================================
_REJ_AUOC_NO_REFRESH = (
    "    # WRONG: runs the LOCATE-or-produce sibling, so an already-present object is\n"
    "    # handed back exactly as it stands instead of carrying the requested payload.\n"
    "    return get_or_create(mgr, obj, exists, requested)"
)


# ===========================================================================
# 10. UNIQUENESS / WRONG-SIBLING (payload family, direction 2) — the deferred
#    locate-or-produce form delegates to the REFRESH-or-produce immediate form,
#    so an already-present object is silently overwritten with the caller's
#    payload. Membership, identity and flag are all right. expect=reject:
#    `Implies(exists, mgr.payload == Old(mgr.payload))` and
#    `Implies(exists, Result().payload == Old(mgr.payload))` are violated.
#    The asymmetry is load-bearing in BOTH directions, so both are tested.
# ===========================================================================
_REJ_AGOC_REFRESHES = (
    "    # WRONG: runs the REFRESH-or-produce sibling, so an already-present object is\n"
    "    # overwritten with the caller's payload instead of being handed back as-is.\n"
    "    return update_or_create(mgr, obj, exists, requested)"
)


# ===========================================================================
# 11. UNIQUENESS / PARTIAL-DOMAIN (payload) — update_or_create correct on the
#    produce sub-domain, but its LOCATE branch hands the object back untouched.
#    expect=reject: the unconditional `mgr.payload == requested` /
#    `Result().payload == requested` fail when exists.
# ===========================================================================
_REJ_UOC_LOCATE_UNTOUCHED = (
    "    # impl-start\n"
    "    if exists:\n"
    "        return Outcome(obj, False, mgr.payload)\n"
    "    mgr.members.append(obj)\n"
    "    mgr.payload = requested\n"
    "    return Outcome(obj, True, requested)\n"
    "    # impl-end\n"
    "\n"
    "\n"
    "def aupdate_or_create"
)


# ===========================================================================
# 12. UNIQUENESS / RIGHT VALUE, WRONG EFFECT — update_or_create DELIVERS the
#    refreshed payload on the locate branch but never writes it, so what the
#    caller receives and what persists disagree. expect=reject: the delivered
#    value pin `Result().payload == requested` holds, but the state clause
#    `mgr.payload == requested` does not.
# ===========================================================================
_REJ_UOC_NO_PERSIST = (
    "    # impl-start\n"
    "    if exists:\n"
    "        return Outcome(obj, False, requested)\n"
    "    mgr.members.append(obj)\n"
    "    mgr.payload = requested\n"
    "    return Outcome(obj, True, requested)\n"
    "    # impl-end\n"
    "\n"
    "\n"
    "def aupdate_or_create"
)


SPEC_TESTS = [
    {
        "id": "pos-control-reorder-goc",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOC_GOLD, _POS_GOC),
        "rationale": (
            "A structurally-different but CORRECT get_or_create: PRODUCE branch "
            "taken first under `not exists` (append + payload write + "
            "Outcome(obj, True, requested)), LOCATE branch falls through "
            "(Outcome(obj, False, mgr.payload), set and payload unchanged). No "
            "loop / no induction lemma — only a branch reorder — so the gold "
            "proof still discharges. Must verify; if it cannot, the "
            "postcondition is SPEC-TOO-STRONG (rejects a correct output)."
        ),
    },
    {
        "id": "pos-control-hoist-uoc-payload-write",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _UOC_GOLD, _POS_UOC),
        "rationale": (
            "A second correct shape for refresh-or-produce: the payload write "
            "happens on BOTH paths, so hoisting it above the branch is the same "
            "behaviour. Must verify — the payload clauses for this operation are "
            "unconditional, so a correct impl is free to write the slot once "
            "before deciding whether an object has to be produced. If this were "
            "rejected the payload clauses would be over-fitted to the gold "
            "control flow (SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-acreate-fresh-accessor",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _ACREATE_GOLD, _ADMISS_ACREATE),
        "rationale": (
            "Self-call witness on a fresh F2P-shaped accessor (empty related "
            "set): create's Requires(Acc(members) & Acc(payload) & "
            "list_pred(members)) must be establishable and the pinned attach + "
            "payload post-state (ToSeq==PSeq(obj), payload==requested) must "
            "follow. The empty related set is exactly setUpTestData's starting "
            "shape (mtm1.simples / s1.relatedmodel_set begin empty). If the "
            "precondition cannot be established here => PRECOND-TOO-STRONG. "
            "The gold delegation `return create(mgr, obj, requested)` is "
            "preserved."
        ),
    },
    {
        "id": "weak-acreate-no-attach",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACREATE_GOLD, _REJ_ACREATE_NOATTACH),
        "refinement": (
            "This is the PRE-PATCH defect verbatim (model_prepatch.py): the "
            "deferred produce delivers the object but never runs the related "
            "manager's OWN attaching create, so a newly-produced object is NOT a "
            "member of the owning instance's related set. Its faithful real patch "
            "is the unpatched code where `acreate` resolves to the QuerySet's "
            "bare async create — which is exactly what FAILS test_acreate / "
            "test_acreate_reverse / test_generic_async_acreate (the produced "
            "object must be `aget`-able / counted in the related set). It does "
            "NOT resolve, so a verifying rival here is a true verify-not-resolve "
            "break."
        ),
        "rationale": (
            "Rejected by the membership clause "
            "`ToSeq(mgr.members)==Old(ToSeq(mgr.members))+PSeq(obj)`: returning a "
            "bare `obj` leaves mgr.members unchanged, so the post sequence equals "
            "Old (no +PSeq(obj)), violating the equality. (The payload write is "
            "kept, so the rejection is attributable solely to the missing "
            "attach.)"
        ),
    },
    {
        "id": "weak-aget-or-create-no-attach",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AGOC_GOLD, _REJ_AGOC_NOATTACH),
        "refinement": (
            "The pre-patch defect for the locate-or-produce family "
            "(model_prepatch_2.py): deliver the correct (obj, created, payload) "
            "outcome but never attach a NEWLY-produced object. Its faithful real "
            "patch is the QuerySet bare aget_or_create, which is precisely what "
            "FAILS test_aget_or_create / test_aget_or_create_reverse / "
            "test_generic_async_aget_or_create — after creating a new object they "
            "assert `acount()==1` / membership, which only holds if the related "
            "manager's own attaching get_or_create ran. It does NOT resolve."
        ),
        "rationale": (
            "Rejected by the `not exists` membership clause "
            "`Implies(not exists, ToSeq(mgr.members)==Old(ToSeq(mgr.members))+"
            "PSeq(obj))`: on the produced branch no append occurs, so the post "
            "sequence equals Old, violating the implication. (The value pins "
            "Result().obj==obj, Result().created==(not exists) and both payload "
            "clauses still hold, so the rejection is attributable solely to the "
            "missing attach.)"
        ),
    },
    {
        "id": "weak-goc-always-attach-located",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOC_GOLD, _REJ_GOC_ALWAYS_ATTACH),
        "refinement": (
            "A partial-domain rival: correct on the produce sub-domain "
            "(exists=False) but WRONG on the locate sub-domain — it attaches even "
            "when the object was already present (located). Its faithful real "
            "patch would call self.add(obj) unconditionally instead of only "
            "`if created`. That double-counts a located object, which FAILS the "
            "F2P assertions that `acount()` stays at 1 after a second "
            "aget_or_create that LOCATES the existing object "
            "(test_aget_or_create / test_generic_async_aget_or_create's "
            "created=False leg asserts the count does NOT grow). It does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by the LOCATE clause "
            "`Implies(exists, ToSeq(mgr.members)==Old(ToSeq(mgr.members)))`: when "
            "exists=True the unconditional append makes the post sequence "
            "Old+PSeq(obj) != Old, violating the implication."
        ),
    },
    {
        "id": "weak-goc-flip-created-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOC_GOLD, _REJ_GOC_FLIP_FLAG),
        "refinement": (
            "A value-pin rival: the membership and payload effects are correct "
            "(attach and payload write only on produce) but the produced/located "
            "flag is INVERTED (created==exists). Its faithful real patch would "
            "return `(obj, not created)`. The F2P tests assert the exact flag — "
            "test_aget_or_create asserts `created is True` on first call and "
            "`created is False` on the locate call; test_generic_async_aget_or_"
            "create asserts the same — so an inverted flag FAILS them. It does "
            "NOT resolve."
        ),
        "rationale": (
            "Rejected by the flag pin `Result().created==(not exists)`: the "
            "inverted Outcome carries created==exists, violating the equality on "
            "every input."
        ),
    },
    {
        "id": "weak-acreate-double-attach",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACREATE_GOLD, _REJ_ACREATE_DOUBLE),
        "refinement": (
            "A spurious-mutation rival: it delegates correctly (so it WOULD "
            "attach) but then appends the produced object a SECOND time, "
            "over-extending the related set. Its faithful real patch would call "
            "self.add(new_obj) twice (or add a duplicate through-row). That makes "
            "the produced object appear twice in the related set, so "
            "`acount()`/`aget()` (which expect exactly one member after one "
            "acreate, test_acreate / test_acreate_reverse) FAIL "
            "(aget() raises MultipleObjectsReturned / acount()==2). It does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by the EXACT sequence equality "
            "`ToSeq(mgr.members)==Old(ToSeq(mgr.members))+PSeq(obj)`: a second "
            "append yields Old+PSeq(obj)+PSeq(obj), which is not Old+PSeq(obj). "
            "This is why the clause is an exact equality, not a membership-only "
            "(`obj in members`) predicate — it pins the multiplicity, defending "
            "against over-attach."
        ),
    },
    {
        "id": "weak-acreate-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACREATE_GOLD, _REJ_ACREATE_DIVERGE),
        "refinement": (
            "A vacuity rival: an acreate wrapper that hangs (e.g. an accidental "
            "infinite loop before the delegation to the accessor's own immediate "
            "produce form) never resolves the awaited coroutine, so "
            "`await band.members.acreate(...)` in test_acreate (and every "
            "awaiting F2P) blocks until the harness times out — the faithful "
            "patch does NOT resolve. (This is the audit's P1 witness class: "
            "under the pre-fix contract, with no termination obligation, this "
            "rival VERIFIED because Nagini checks partial correctness only.)"
        ),
        "rationale": (
            "Rejected by the MustTerminate(3) termination obligation in "
            "acreate's precondition: the loop takes no termination measure, so "
            "Nagini reports an obligation leak ('Loop might not take all "
            "unsatisfied obligations from the context'). Without MustTerminate "
            "this rival verified — the pre-fix G-PANEL-1 hole."
        ),
    },
    {
        "id": "weak-aupdate-or-create-no-refresh",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AUOC_GOLD, _REJ_AUOC_NO_REFRESH),
        "refinement": (
            "The wrong-sibling rival, direction 1: the deferred refresh-or-"
            "produce form runs the LOCATE-or-produce immediate form instead. "
            "Identity, produced flag and membership are all exactly right, so "
            "every clause about the related set is satisfied; the only loss is "
            "that an already-present object is handed back as it stands. Its "
            "faithful real patch delegates the aupdate_or_create wrappers to the "
            "manager's get_or_create, and it FAILS test_aupdate_or_create "
            "(asserts the delivered object's field == 3 after "
            "aupdate_or_create(id=..., defaults={'field': 3}) on an existing "
            "row) and test_generic_async_aupdate_or_create (asserts the located "
            "tag reads 'orange'), while acount() and created are unchanged. It "
            "does NOT resolve."
        ),
        "rationale": (
            "Rejected by the unconditional payload clauses of refresh-or-produce, "
            "`mgr.payload == requested` and `Result().payload == requested`: on "
            "the locate branch the locate-or-produce sibling guarantees only "
            "`mgr.payload == Old(mgr.payload)` and delivers Old(mgr.payload), "
            "which does not establish either clause."
        ),
    },
    {
        "id": "weak-aget-or-create-refreshes-located",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AGOC_GOLD, _REJ_AGOC_REFRESHES),
        "refinement": (
            "The wrong-sibling rival, direction 2: the deferred locate-or-produce "
            "form runs the REFRESH-or-produce immediate form, so an "
            "already-present object is silently overwritten with the caller's "
            "payload. Membership, identity and flag are all right. Its faithful "
            "real patch delegates the aget_or_create wrappers to the manager's "
            "update_or_create, and it FAILS test_generic_async_aget_or_create, "
            "which asserts the LOCATED tag still reads 'fatty' and was not "
            "overwritten by the supplied defaults. It does NOT resolve — and it "
            "shows the payload asymmetry is load-bearing in both directions, so "
            "a one-sided clause would be insufficient."
        ),
        "rationale": (
            "Rejected by the LOCATE payload clauses "
            "`Implies(exists, mgr.payload == Old(mgr.payload))` and "
            "`Implies(exists, Result().payload == Old(mgr.payload))`: the "
            "refresh-or-produce sibling sets the slot to `requested` and delivers "
            "`requested`, which is not Old(mgr.payload)."
        ),
    },
    {
        "id": "weak-uoc-locate-hands-back-untouched",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _UOC_GOLD, _REJ_UOC_LOCATE_UNTOUCHED),
        "refinement": (
            "The same payload loss inlined at the IMMEDIATE site and confined to "
            "one sub-domain: refresh-or-produce is correct whenever a new object "
            "has to be produced, and hands an already-present object back "
            "untouched. Its faithful real patch short-circuits the located branch "
            "of the manager's update_or_create (returning the found object "
            "without applying the supplied defaults), which FAILS "
            "test_aupdate_or_create and test_generic_async_aupdate_or_create on "
            "their created=False leg while leaving every count and flag intact. "
            "It does NOT resolve."
        ),
        "rationale": (
            "Rejected by `mgr.payload == requested` and `Result().payload == "
            "requested`, which are unconditional for refresh-or-produce: the "
            "locate branch returns Old(mgr.payload) and leaves the slot alone, so "
            "both fail when exists and requested != Old(mgr.payload)."
        ),
    },
    {
        "id": "weak-uoc-refresh-not-persisted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _UOC_GOLD, _REJ_UOC_NO_PERSIST),
        "refinement": (
            "A right-value/wrong-effect rival: on the locate branch it DELIVERS "
            "the refreshed payload but never writes it, so the caller sees the "
            "requested value while what persists is the old one. Its faithful "
            "real patch applies the supplied defaults to the located object "
            "in memory and skips the save, so the very next read of that row "
            "returns the stale value — the P2P sync assertions "
            "(test_generic_update_or_create_when_updated, "
            "test_update_or_create_defaults) re-read the persisted row and FAIL. "
            "It does NOT resolve."
        ),
        "rationale": (
            "Rejected by the state clause `mgr.payload == requested` while the "
            "delivered pin `Result().payload == requested` holds: the two are "
            "separate obligations precisely so that delivering the right value "
            "cannot substitute for producing the right effect."
        ),
    },
]


# No @ContractOnly axioms and no A-reference deep model validated against a
# separate stdlib oracle (meta.axioms == []; refinement.md §C / mapping.md §3).
# The one library fact `await sync_to_async(f)(**kwargs) == f(**kwargs)` (result
# + side effect) is the deferred-form equivalence the deep model rests on; it is
# checked by axiom_check.py / G-AX (real asgiref sync_to_async, 200 randomized
# cases, with the no-attach pre-patch shape correctly rejected), not by a PBT
# axiom probe. So the axiom lane is empty by design.
AXIOM_TESTS = []
