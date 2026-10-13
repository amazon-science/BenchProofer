"""properties.py — G-PBT falsification battery for django__django-15252 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct recordStoreGate`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method — the preparation phase of a step):

  recordStoreGate (hasWork : Bool) (storePresent : Bool) return (r : GateOutcome)
    ensures r.ensured   = hasWork                          -- (E1)
    ensures r.earlyExit = (!hasWork && !storePresent)      -- (E2)

The step consults two facts — ``hasWork`` (there is at least one item to record
this step) and ``storePresent`` (the bookkeeping store already exists) — and
governs two observable effects, each pinned by one top-level ``ensures``:

  * (E1) ``ensured = hasWork`` — the store-materialising WRITE effect runs
    EXACTLY when there is work to record. Dropping the condition (running it
    unconditionally) is the pre-change behaviour: the store is materialised even
    when nothing would be recorded.
  * (E2) ``earlyExit = (!hasWork && !storePresent)`` — the step short-circuits
    EXACTLY on the no-work-and-no-store case, where nothing would be recorded
    and nothing must be created on its behalf. This is the added behaviour: the
    query/read path is skipped on precisely that one sub-domain and taken on
    every other. The F2P (has_table mocked absent, empty plan) rides on this
    clause: it asserts the store-materialising effect does NOT fire on that path.

Both binders are load-bearing. ``hasWork`` drives (E1) directly and gates half of
(E2); ``storePresent`` is observable only through (E2) — it distinguishes the
short-circuit sub-domain (no store) from the read-through sub-domain (store
present), and a rival that ignores it verifies (E1) yet mishandles (E2). There is
no opaque answer-key: ``ensured`` and ``earlyExit`` are pinned to fully-unfolded
boolean functions of the two arguments (the ``axioms`` region is empty), so the
post-image is grounded, not an echo.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts the whole ``migrate(executor, pending)`` procedure over a mutable
``Executor`` object held under fractional permissions, with FOUR postcondition
clauses: (T) the table-presence field is read-only/unchanged, (1) the write flag
tracks ``not no_pending_records``, (2) the read flag tracks ``not (no_pending and
not old_table_present)``, and (3) ``not records_read -> not schema_ensured``.
This bundle models only the purely-functional control-flow decision the fix turns
on — the two effect TRIGGERS as boolean functions of the two boolean facts
(mapping.md §1). Under that refinement:

  * nagini clause (1) ``schema_ensured == not no_pending_records`` folds to (E1)
    ``ensured = hasWork`` (``hasWork`` ↔ ``not no_pending_records``: there is
    work iff the plan is non-empty).
  * nagini clauses (2) ``records_read == not (no_pending and not
    old_table_present)`` and (3) ``not records_read -> schema_ensured is False``
    together pin exactly the ONE sub-domain on which the step short-circuits —
    the no-work + no-store path — which is (E2) ``earlyExit = (!hasWork &&
    !storePresent)``. (The velvet ``earlyExit`` is the COMPLEMENT of nagini's
    ``records_read`` on the modeled domain: the step short-circuits exactly when
    it does NOT reach the read path.)

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally-different but
    behaviourally identical impl (straight-line compute, or branch-reorder) must
    verify under the frozen ``loom_solve``, else the spec is SPEC-TOO-STRONG on
    the shape of the impl.
  * ADMISSIBILITY — the method has NO ``require`` clause (both inputs are total
    ``Bool``), so the sibling's "a normal input satisfies the precondition" probe
    is degenerate. The residual risk on a total domain is a DEGENERATE post-image;
    ``admiss-nondegenerate`` discharges an in-region ``assert`` that binds the two
    ``ensures`` right-hand sides to the values the gold body actually computes and
    pins three genuinely distinct outcomes (write-fires, short-circuit,
    read-through) at F2P/P2P-shaped inputs, kept alongside the verbatim gold body
    so the method's own obligation still discharges.
  * FRAME-MUTATION (nagini's two MANDATORY rivals, which WRITE the read-only
    table-presence field held at ``Acc(...,1/2)``) — VACUOUS on this carrier.
    Lean/Velvet are referentially transparent: the table-presence fact enters as
    the immutable value input ``storePresent : Bool`` (not ``mut``), there is no
    heap, no aliasing, no fractional permission, and no ``Old``. There is no
    read-only input to overwrite and no permission to under-hold, so the class has
    no carrier analogue. NOT ported; no substitute fabricated (porting map: this
    class is vacuous on a referentially-transparent backend). See the footer.
  * UNGROUNDED-ORACLE ECHO — N/A. (E1)/(E2) are unfolded boolean functions of the
    method's own arguments; the ``axioms`` region is empty. There is no
    answer-key to echo; the cheapest correct impl computes the two effects
    honestly, which the positives cover.
  * PARTIAL-DOMAIN / VALUE / CONTROL-FLOW-EFFECT — carries the reject lane. The
    nagini "read-vs-no-read" and "write-vs-no-write" control-flow effects are
    observable here as the two boolean fields of the returned ``GateOutcome``, so
    each is attacked by a reject rival at the sub-domain where it diverges.

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` / ``if`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the changed
decision is modeled deeply as the two boolean effect-functions). There is no
axiom-soundness obligation to probe, and the gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15252"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl body (between, but not including, the markers): a
# ---- single anchor lying wholly inside the `-- impl-start`/`-- impl-end` region
# ---- and unique in the file (both facts asserted at load). Every variant swaps
# ---- on this block, so the spec and the region markers are untouched.
_IMPL = """    let mut ensured   : Bool := false
    let mut earlyExit : Bool := false
    if !hasWork then
      if !storePresent then
        earlyExit := true
    else
      ensured := true
    return ⟨ensured, earlyExit⟩"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced (the frozen
    `loom_solve` proof and every marker are kept)."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `recordStoreGateTester hasWork storePresent = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. Both arguments are concrete Bool
# ---- literals, so `decide` reduces the extracted program without getting stuck.
def _witness(hasWork, storePresent):
    def b(x):
        return "true" if x else "false"
    return (
        "extract_program_for recordStoreGate\n"
        "prove_precondition_decidable_for recordStoreGate\n"
        "prove_postcondition_decidable_for recordStoreGate\n"
        "derive_tester_for recordStoreGate\n\n"
        f"example : recordStoreGateTester {b(hasWork)} {b(storePresent)} = false := by\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify under the frozen `loom_solve`. If a faithful correct impl
    # cannot verify, the spec is SPEC-TOO-STRONG. The post-image is point-wise
    # over two booleans, so no induction is needed and each reshape stays within
    # the frozen proof script.
    # =====================================================================
    {
        "id": "pos-control-flat",
        "kind": "soundness",
        "expect": "verify",
        # Straight-line compute: return the two effects directly as the same
        # boolean functions of the inputs the gold branches encode. No nested
        # `if`, no mutable staging — a completely different control shape, same
        # 4-case truth table; the read-only fact `storePresent` is only READ.
        "module": _impl("    return ⟨hasWork, !hasWork && !storePresent⟩"),
        "rationale": (
            "structurally-different CORRECT impl: return the two effects "
            "straight-line as `⟨hasWork, !hasWork && !storePresent⟩`, the same "
            "boolean functions the gold nested branches encode. Identical 4-case "
            "truth table, so both (E1) `ensured = hasWork` and (E2) `earlyExit = "
            "(!hasWork && !storePresent)` discharge; the frozen `loom_solve` "
            "closes. If a faithful correct impl cannot verify => SPEC-TOO-STRONG. "
            "(Nagini sibling: pos-control-flat — compute-up-front reshape.)"),
    },
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch-reorder: handle the write (hasWork) case FIRST, then within the
        # no-work case split on store presence, short-circuiting when the store is
        # absent. Behaviourally identical to the gold (same 4-case truth table); a
        # control-shape reshape, not a different algorithm.
        "module": _impl(
            "    let mut ensured   : Bool := false\n"
            "    let mut earlyExit : Bool := false\n"
            "    if hasWork then\n"
            "      ensured := true\n"
            "    else\n"
            "      if !storePresent then\n"
            "        earlyExit := true\n"
            "    return ⟨ensured, earlyExit⟩"),
        "rationale": (
            "branch-reorder: handle the write case (`hasWork`) first, then split "
            "the no-work case on store presence (short-circuit when the store is "
            "absent). Same decision as the gold on all 4 cases, so (E1) and (E2) "
            "both discharge under the frozen `loom_solve`; a control-shape reshape, "
            "not a different algorithm. Must verify (else SPEC-TOO-STRONG). "
            "(Nagini sibling: pos-control-reorder.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require` clause (both inputs are total
    # `Bool`), so the sibling's "a normal input satisfies the precondition" probe
    # is degenerate. The residual admissibility risk on a total domain is a
    # DEGENERATE post-image — a spec no impl distinguishes reads exactly like one
    # every impl meets. This case discharges an in-region `assert`, placed AFTER
    # the gold body has computed its two effects, that ties the post-image to the
    # ACTUAL computed values (`ensured` / `earlyExit`) and then pins the three
    # genuinely distinct outcomes at concrete F2P/P2P-shaped inputs. The gold body
    # is kept verbatim so the method's own obligation still discharges.
    #
    # AUDIT NOTE (repair). The assert this case shipped with was a CLOSED
    # tautology: `((true : Bool) = true) ∧ ((!false && !false : Bool) = true) ∧
    # ((!false && !true : Bool) = false)` mentions neither binder nor either
    # effect variable, so it reduced to `True` by `decide` no matter what the
    # impl computed — it would have discharged over an impl that returned
    # `⟨false, false⟩` on every input, i.e. over a maximally degenerate
    # post-image, which is precisely the risk the case claims to retire. It was
    # not, however, ignored: an in-region assert does have teeth here (an assert
    # of `((true : Bool) = false)` fails the build with `unsolved goals ...
    # ⊢ true = false`), so the fix is to make the assert SAY something. The two
    # leading conjuncts now name the computed staging variables against the two
    # `ensures` right-hand sides, which is what makes the discharge contingent on
    # the impl and hence on a non-degenerate post-image.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    let mut ensured   : Bool := false\n"
            "    let mut earlyExit : Bool := false\n"
            "    if !hasWork then\n"
            "      if !storePresent then\n"
            "        earlyExit := true\n"
            "    else\n"
            "      ensured := true\n"
            "    assert (with_name_prefix `admiss (\n"
            "      (ensured = hasWork) ∧\n"
            "      (earlyExit = (!hasWork && !storePresent)) ∧\n"
            "      ((!false && !false : Bool) = true) ∧\n"
            "      ((!false && !true : Bool) = false)))\n"
            "    return ⟨ensured, earlyExit⟩"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate, asserted IN-REGION "
            "over the values the gold body actually computes: `ensured = hasWork` "
            "and `earlyExit = (!hasWork && !storePresent)` hold of the staged "
            "variables at the point of return (so the assert is contingent on the "
            "impl — an impl returning a constant `⟨false, false⟩` fails it), and "
            "the two literal conjuncts pin the short-circuit trigger (E2) TRUE on "
            "the no-work + no-store path (the F2P shape `!false && !false`) and "
            "FALSE on the no-work + store-present read-through path "
            "(`!false && !true`) — three distinct outcomes over the two clauses. "
            "The in-region assert must discharge (else the obligation would be "
            "degenerate); the gold body is kept verbatim so (E1)/(E2) still "
            "verify. (Nagini sibling: admiss-f2p-shaped-input, re-aimed from "
            "fractional-permission admissibility — this backend has no `require` "
            "and no permission surface — to post-image non-degeneracy.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "uniq-unconditional-ensure",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch behaviour: perform the store-materialising effect
        # UNCONDITIONALLY (and never short-circuit). Correct where there IS work;
        # diverges on the no-work case, where it materialises the store anyway.
        "module": _impl(
            "    let mut ensured   : Bool := true\n"
            "    let mut earlyExit : Bool := false\n"
            "    return ⟨ensured, earlyExit⟩"),
        "refinement": (
            "this is the pre-change behaviour: the store-materialising effect ran "
            "on every step, first, regardless of whether anything would be "
            "recorded. The F2P mocks the store absent and drives an empty work-list "
            "and asserts the store-materialising effect is NOT performed (a "
            "zero-query assertion); with the effect unconditional it fires and the "
            "assertion fails. Its faithful real patch is the unpatched code — "
            "exactly what does NOT resolve."),
        "rationale": (
            "REJECT from (E1) `ensured = hasWork`: on `hasWork = false` the spec "
            "requires `ensured = false`, but this rival returns `ensured = true`. "
            "Refuted at (hasWork=false, storePresent=true) — the store-present "
            "no-work sub-domain, where (E1) is the only violated clause (earlyExit "
            "is correctly false there). Verifying would be SPEC-TOO-WEAK (the "
            "unconditional-write regression would go unnoticed). (Nagini sibling: "
            "uniq-unconditional-schema.)"),
        "witness": _witness(False, True),
    },
    {
        "id": "uniq-never-short-circuit",
        "kind": "uniqueness",
        "expect": "reject",
        # Gate the write correctly (E1 holds) but NEVER short-circuit — i.e. always
        # take the read-through path, even on the no-work + no-store sub-domain the
        # fix short-circuits. Correct on (E1) and on every path except the one the
        # fix adds.
        "module": _impl(
            "    let mut ensured   : Bool := false\n"
            "    let mut earlyExit : Bool := false\n"
            "    if hasWork then\n"
            "      ensured := true\n"
            "    return ⟨ensured, earlyExit⟩"),
        "refinement": (
            "gates the store-materialising effect correctly (E1 holds) but never "
            "short-circuits — a patch that made the write conditional yet did NOT "
            "add the no-work + no-store early return. On the F2P shape (no work, "
            "store absent) it still runs the remainder of the procedure and issues "
            "the record-reading queries, failing the zero-query assertion even "
            "though the store-materialising effect is not performed. This is the "
            "load-bearing partial fix the sibling's refinement was written to "
            "catch; it does NOT resolve."),
        "rationale": (
            "REJECT from (E2) `earlyExit = (!hasWork && !storePresent)`: on "
            "(hasWork=false, storePresent=false) the spec requires `earlyExit = "
            "true`, but this rival leaves it false. This is the sub-domain the fix "
            "adds — the load-bearing short-circuit discriminator. Verifying would "
            "be SPEC-TOO-WEAK. (Nagini sibling: uniq-always-read.)"),
        "witness": _witness(False, False),
    },
    {
        "id": "uniq-ignore-store",
        "kind": "uniqueness",
        "expect": "reject",
        # Short-circuit on the no-work case REGARDLESS of store presence — i.e.
        # skip the read even when the store is already present. Correct on the
        # no-work + no-store path, but on no-work + store-present it short-circuits
        # where the spec requires the read-through (earlyExit false).
        "module": _impl(
            "    let mut ensured   : Bool := false\n"
            "    let mut earlyExit : Bool := false\n"
            "    if !hasWork then\n"
            "      earlyExit := true\n"
            "    else\n"
            "      ensured := true\n"
            "    return ⟨ensured, earlyExit⟩"),
        "refinement": (
            "short-circuits on the no-work case REGARDLESS of store presence — a "
            "patch that added the early return but WITHOUT the inner store-absent "
            "guard. On the no-work case with the store ALREADY present, the gold "
            "code falls through and runs the record-reading path, but this rival "
            "short-circuits and skips it. Dropping the store-presence guard changes "
            "behaviour on the store-present no-work sub-domain — the existing-store "
            "migration paths that must read applied-record state would see it "
            "skipped; it does NOT resolve."),
        "rationale": (
            "REJECT from (E2) `earlyExit = (!hasWork && !storePresent)`: on "
            "(hasWork=false, storePresent=true) `!hasWork && !storePresent` is "
            "false, so the spec requires `earlyExit = false`, but this rival "
            "short-circuits and returns `earlyExit = true`. This isolates the "
            "`storePresent` binder on (E2): it holds `hasWork=false` fixed and "
            "flips only `storePresent` relative to the never-short-circuit rival, "
            "so the two do NOT share a witness and the manifest demonstrates (E2)'s "
            "dependence on `storePresent`. Verifying would be SPEC-TOO-WEAK. "
            "(Nagini sibling: uniq-ignore-table.)"),
        "witness": _witness(False, True),
    },
    {
        "id": "uniq-write-on-notouch",
        "kind": "uniqueness",
        "expect": "reject",
        # On the no-touch path (no work, no store) ALSO perform the
        # store-materialising effect before short-circuiting. Correct short-circuit
        # flag, but it materialises the store where nothing is recorded.
        "module": _impl(
            "    let mut ensured   : Bool := false\n"
            "    let mut earlyExit : Bool := false\n"
            "    if !hasWork then\n"
            "      if !storePresent then\n"
            "        ensured := true\n"
            "        earlyExit := true\n"
            "    else\n"
            "      ensured := true\n"
            "    return ⟨ensured, earlyExit⟩"),
        "refinement": (
            "on the no-work + no-store path it ALSO performs the "
            "store-materialising effect before short-circuiting — a patch that "
            "created the store on a connection with nothing to record and no store, "
            "the exact side effect the fix removes. The F2P asserts the effect is "
            "NOT performed on this path; this rival performs it. It does NOT "
            "resolve."),
        "rationale": (
            "REJECT from (E1) `ensured = hasWork`: on (hasWork=false, "
            "storePresent=false) the spec requires `ensured = false`, but this "
            "rival returns `ensured = true` while short-circuiting. Refuted on the "
            "no-touch sub-domain — the sub-domain the unconditional-ensure rival "
            "shares gold's short-circuit flag differently, distinguishing the two. "
            "Verifying would be SPEC-TOO-WEAK. (Nagini sibling: "
            "uniq-write-on-notouch, whose clause-(3) `not records_read -> "
            "schema_ensured is False` folds into (E1) on this carrier — the "
            "short-circuit path must leave the write-effect off.)"),
        "witness": _witness(False, False),
    },
    {
        "id": "uniq-skip-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Do nothing: never perform the write, never short-circuit. Correct only on
        # the no-work + store-present read-through path; wrong wherever a write is
        # required (there is work) and on the short-circuit path.
        "module": _impl(
            "    let mut ensured   : Bool := false\n"
            "    let mut earlyExit : Bool := false\n"
            "    return ⟨ensured, earlyExit⟩"),
        "refinement": (
            "a do-nothing prologue (neither the store-materialising effect nor the "
            "short-circuit on any path) corresponds to a patch that removed BOTH "
            "the store creation AND the early-return short-circuit: the store would "
            "never be materialised even when there IS work to record. It is correct "
            "only on the store-present no-work read-through path and wrong wherever "
            "a write is required; it resolves nothing. Supporting near-miss."),
        "rationale": (
            "REJECT from (E1) `ensured = hasWork`: on `hasWork = true` the spec "
            "requires `ensured = true`, but this rival leaves it false. Refuted at "
            "(hasWork=true, storePresent=false) — the ONLY reject witness with "
            "`hasWork = true`, so it is what exercises (E1)'s work-present direction "
            "(the other E1 rivals attack the work-absent direction). Verifying "
            "would be SPEC-TOO-WEAK. (Nagini sibling: uniq-skip-all.)"),
        "witness": _witness(True, False),
    },

    # =====================================================================
    # AUDIT ADDITIONS — the work-present + store-present corner. The battery as
    # ported stationed no rival at (hasWork=true, storePresent=true) and the
    # footer justified that by claiming the corner "carries no additional
    # discriminating obligation" because `hasWork=true` collapses (E2) to
    # `false` independent of `storePresent`. The second half is true; the
    # CONCLUSION is false, and both rivals below are the counterexample. (E2)
    # collapsing to a CONSTANT on that corner is exactly what makes it
    # attackable: an impl may set `earlyExit` there, and (E1) may be gated on
    # `storePresent` there — neither is refutable at any of the three points the
    # ported witnesses occupy, because every one of those points has
    # `hasWork=false`. Both were built and measured: rival build exit 1
    # (`unsolved goals` on the named `ensures`), witness exit 0 against the
    # rival, exit 1 against the frozen solution with `decide` reducing the claim
    # and reporting it false.
    # =====================================================================
    {
        "id": "uniq-ensure-only-when-store-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Gate the WRITE on store-absence as well as on work: perform the
        # store-materialising effect only when there is work AND the store is
        # missing. Agrees with gold on all three `hasWork=false` points and on
        # (work, no store); diverges ONLY at (work, store present), where it
        # skips the write the spec requires.
        "module": _impl(
            "    let mut ensured   : Bool := false\n"
            "    let mut earlyExit : Bool := false\n"
            "    if !hasWork then\n"
            "      if !storePresent then\n"
            "        earlyExit := true\n"
            "    else\n"
            "      if !storePresent then\n"
            "        ensured := true\n"
            "    return ⟨ensured, earlyExit⟩"),
        "refinement": (
            "conflates 'there is work to record' with 'the store still has to be "
            "created': it performs the store-materialising effect only when the "
            "store is absent, so on the ordinary path where work exists and the "
            "store is ALREADY there the effect is skipped. A patch shaped this way "
            "makes the effect idempotent-by-guard rather than work-gated, so the "
            "step stops performing it on the overwhelmingly common steady-state "
            "path; it does NOT resolve, and unlike the other E1 rivals it is "
            "invisible on every no-work input."),
        "rationale": (
            "REJECT from (E1) `ensured = hasWork`: on (hasWork=true, "
            "storePresent=true) the spec requires `ensured = true`, but this rival "
            "leaves it false. Refuted at the work-present + store-present corner — "
            "the point NO ported witness occupies (all three ported points have "
            "`hasWork=false`), so this is the case that makes `storePresent` "
            "load-bearing on (E1) as well as on (E2). Verifying would be "
            "SPEC-TOO-WEAK. (No nagini sibling: added by audit to close the "
            "corner the port left unattacked.)"),
        "witness": _witness(True, True),
    },
    {
        "id": "uniq-short-circuit-on-work-with-store",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct (E1), and correct (E2) on every no-work point, but ALSO
        # short-circuits when there IS work and the store is present — the one
        # corner no ported witness occupies.
        "module": _impl(
            "    let mut ensured   : Bool := false\n"
            "    let mut earlyExit : Bool := false\n"
            "    if !hasWork then\n"
            "      if !storePresent then\n"
            "        earlyExit := true\n"
            "    else\n"
            "      ensured := true\n"
            "      if storePresent then\n"
            "        earlyExit := true\n"
            "    return ⟨ensured, earlyExit⟩"),
        "refinement": (
            "short-circuits on the work-present + store-present path: it performs "
            "the store-materialising effect and then returns without running the "
            "remainder of the procedure, so the items it just prepared to record "
            "are never processed. A patch that widened the early-return guard this "
            "way would silently skip the actual work on the most common path while "
            "still passing every no-work assertion; it does NOT resolve."),
        "rationale": (
            "REJECT from (E2) `earlyExit = (!hasWork && !storePresent)`: on "
            "(hasWork=true, storePresent=true) `!hasWork && !storePresent` is "
            "false, so the spec requires `earlyExit = false`, but this rival "
            "returns true. This is the (E2) direction the ported set could not "
            "reach: `uniq-ignore-store` attacks a wrongly-TRUE `earlyExit` only at "
            "`hasWork=false`, so a rival that short-circuits on the work-present "
            "corner survives it. Verifying would be SPEC-TOO-WEAK. (No nagini "
            "sibling: added by audit.)"),
        "witness": _witness(True, True),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 10 SPEC cases (2
# soundness positives, 1 admissibility, 2 MANDATORY frame-mutation rivals, 5
# uniqueness rivals) plus an EMPTY axiom lane (AXIOM_TESTS = []). It contracts the
# whole `migrate(executor, pending)` procedure over a mutable `Executor` held
# under fractional permissions, with FOUR postcondition clauses: (T) the
# table-presence field is read-only, (1) the write flag == `not
# no_pending_records`, (2) the read flag == `not (no_pending and not
# old_table_present)`, and (3) `not records_read -> schema_ensured is False`.
#
# THIS bundle models only the purely-functional control-flow decision the fix
# turns on — the two effect TRIGGERS as boolean functions of the two boolean
# facts `hasWork` / `storePresent` (mapping.md §1) — with TWO clauses:
#   (E1) `ensured   = hasWork`                        <- nagini (1)
#   (E2) `earlyExit = (!hasWork && !storePresent)`    <- nagini (2)&(3) folded
#        (velvet `earlyExit` is the COMPLEMENT of nagini `records_read` on the
#         modeled domain: the step short-circuits exactly when it does NOT reach
#         the read path, and clause (3) forces the write off on that path).
# The mutable `Executor`, the fractional permissions, and the read-only frame
# clause (T) do not exist on this referentially-transparent carrier: the
# table-presence fact is the immutable value input `storePresent`.
#
#   nagini case                     kind          -> here                     disposition
#   -------------------------------------------------------------------------------------
#   pos-control-flat                soundness     -> pos-control-flat          PORTED
#   pos-control-reorder             soundness     -> pos-control-reorder       PORTED
#   admiss-f2p-shaped-input         admissibility -> admiss-nondegenerate      RE-AIMED
#   frame-mutate-readonly-table     uniqueness    -> (none)                    VACUOUS
#   frame-flip-readonly-table       uniqueness    -> (none)                    VACUOUS
#   uniq-unconditional-schema       uniqueness    -> uniq-unconditional-ensure PORTED
#   uniq-always-read                uniqueness    -> uniq-never-short-circuit  PORTED
#   uniq-ignore-table               uniqueness    -> uniq-ignore-store         PORTED
#   uniq-write-on-notouch           uniqueness    -> uniq-write-on-notouch     PORTED
#   uniq-skip-all                   uniqueness    -> uniq-skip-all             PORTED
#   AXIOM_TESTS (none)              axiom         -> (none)                    N/A (G-AX)
#   (no sibling)                    uniqueness    -> uniq-ensure-only-when-    AUDIT-ADDED
#                                                    store-absent
#   (no sibling)                    uniqueness    -> uniq-short-circuit-on-    AUDIT-ADDED
#                                                    work-with-store
#
# 5 uniqueness ported + 2 AUDIT-ADDED, 2 soundness ported, 1 admissibility
# re-aimed (its assert repaired by audit); 2 frame-mutation vacuous; axiom lane
# empty (nothing to port).
#
# PORTED (2 soundness): pos-control-flat (compute both effects straight-line) and
#   pos-control-reorder (handle the write case first) carry across intact — only
#   the carrier changes from mutating an `Executor`'s two flags to returning the
#   two `GateOutcome` fields. Both keep the gold 4-case truth table and verify
#   under the frozen `loom_solve`.
# RE-AIMED (admiss-f2p-shaped-input -> admiss-nondegenerate): the sibling asserts
#   an F2P-shaped `Executor(False)` satisfies `migrate`'s fractional-permission
#   Requires. This backend has NO `require` (both inputs are total `Bool`) and no
#   permission surface, so that probe is degenerate; the case is re-aimed at the
#   residual total-domain risk — a DEGENERATE post-image — by an in-region assert
#   pinning three distinct outcomes (write-fires / short-circuit / read-through)
#   at F2P/P2P-shaped inputs.
# PORTED (5 uniqueness): uniq-unconditional-schema -> uniq-unconditional-ensure
#   (perform the write unconditionally; the pre-patch bug; refuted on the
#   work-absent sub-domain via E1). uniq-always-read -> uniq-never-short-circuit
#   (gate the write but never short-circuit; refuted on the no-work+no-store F2P
#   sub-domain via E2). uniq-ignore-table -> uniq-ignore-store (short-circuit
#   regardless of store presence; refuted on the store-present no-work sub-domain
#   via E2 — the witness that isolates `storePresent`). uniq-write-on-notouch ->
#   uniq-write-on-notouch (perform the write on the no-touch path; refuted via
#   E1, into which nagini clause (3) folds). uniq-skip-all -> uniq-skip-all (do
#   nothing; refuted on the work-present sub-domain via E1).
# VACUOUS (2, frame-mutation): frame-mutate-readonly-table and
#   frame-flip-readonly-table both WRITE the read-only table-presence field held
#   at `Acc(...,1/2)`, rejected by the nagini PERMISSION SYSTEM for insufficient
#   permission (they never even reach value reasoning). This backend is
#   referentially transparent: the table-presence fact enters as the immutable
#   value input `storePresent : Bool` (not `mut`); there is no heap, no aliasing,
#   no fractional permission, no `Old`, and no read-only frame clause to violate.
#   The class has NO carrier analogue — omitted as a genuine carrier fact, NOT
#   fabricated (porting map: frame/permission-mutation is vacuous on a
#   referentially-transparent backend).
#
#   AUDIT re-derivation (measured, not argued). Both sibling rivals were written
#   out on this carrier as the literal analogue — the gold body prefixed with
#   `storePresent := storePresent` (mutate) and `storePresent := !storePresent`
#   (flip) — and built. Both fail, but for a reason that is not about the spec:
#   `error: `storePresent` cannot be mutated, only variables declared using `let
#   mut` can be mutated`, followed by `Failed to parse an assertion without
#   names: WPGen sorry`. That is the ELABORATOR refusing to form the program at
#   all, so there is no post-image to state a refutation over and no witness can
#   discriminate: the rejection is attributable to the carrier's syntax, not to
#   (E1)/(E2). A frame-mutation case here would therefore be a witness-less
#   reject — exactly what the witness requirement exists to refuse. Confirmed
#   inexpressible; the omission stands.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# BINDER / CLAUSE / POINT COVERAGE. Two `ensures` clauses over two `Bool` binders.
#   The seven reject witnesses probe ALL FOUR input points (pts=4):
#     * uniq-unconditional-ensure          (hasWork=false, storePresent=true)   E1
#     * uniq-never-short-circuit           (hasWork=false, storePresent=false)  E2
#     * uniq-ignore-store                  (hasWork=false, storePresent=true)   E2
#     * uniq-write-on-notouch              (hasWork=false, storePresent=false)  E1
#     * uniq-skip-all                      (hasWork=true,  storePresent=false)  E1
#     * uniq-ensure-only-when-store-absent (hasWork=true,  storePresent=true)   E1
#     * uniq-short-circuit-on-work-with-store (hasWork=true, storePresent=true) E2
#   Both clauses are attacked from both directions at BOTH values of `hasWork`.
#   (E1) `ensured = hasWork`: work-absent-but-writes (uniq-unconditional-ensure,
#   uniq-write-on-notouch) and work-present-but-skips (uniq-skip-all at no-store,
#   uniq-ensure-only-when-store-absent at store-present). (E2) `earlyExit =
#   (!hasWork && !storePresent)`: should-short-circuit-but-doesnt
#   (uniq-never-short-circuit) and shouldnt-short-circuit-but-does
#   (uniq-ignore-store at no-work, uniq-short-circuit-on-work-with-store at
#   work-present). Both binders are varied and both are DEMONSTRATED load-bearing
#   on both clauses; no binder is pinned at a single value across the reject set.
#
#   AUDIT CORRECTION. This block previously recorded pts=3 and justified the
#   missing (hasWork=true, storePresent=true) corner by claiming that
#   "`hasWork=true` collapses (E2) to `false` independent of `storePresent`: the
#   store-present true-work corner carries no additional discriminating
#   obligation, so no rival is stationed there." The premise is true and the
#   conclusion does not follow — a clause collapsing to a CONSTANT on a corner
#   still obliges an impl to produce that constant there. The two audit-added
#   rivals are wrong ONLY at that corner and are consequently invisible to all
#   five ported witnesses (every one of which sits at `hasWork=false`): one skips
#   the required write there (E1), the other short-circuits where the spec forbids
#   it (E2). Both are rejected by the frozen spec and both witnesses discriminate
#   at (true, true) — measured, not argued.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3: the changed
#   decision is modeled deeply as the two boolean effect-functions, validated by
#   G-CONF, so G-AX is vacuous); the sibling's AXIOM_TESTS is likewise empty. This
#   gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
