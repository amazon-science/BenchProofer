"""properties.py — G-PBT falsification battery for django__django-16116 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside the ``-- impl-start``
/ ``-- impl-end`` region — which the consumer spec view elides — is changed, and
for the reproved soundness positive the elided ``prove_correct`` tactic body, so
``markers.same_spec`` holds and the ``prove_correct runCheckedWrite`` obligation
survives with a byte-identical STATEMENT) and swaps in a candidate
implementation, checked by the real verifier. ``expect="verify"`` passes iff
(in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: the witness must ELABORATE
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method, two read-only mode-flag binders):

  runCheckedWrite (checkOnly : Bool) (update : Bool) return (out : StepOutcome)
    ensures out = stepOutcome checkOnly update                 [C1, whole result]
    ensures checkOnly = true → out.written = WriteKind.noWrite [C2, no-artifact]
    ensures out.exited = checkOnly                             [C3, abort==query]

  The step models a migration-management branch that has already detected a
  non-empty set of pending changes and must decide, from two independent mode
  flags, WHAT to emit and WHETHER to abort. The desired behaviour is the
  TRANSPARENT total function ``stepOutcome`` of the two flags:

    stepOutcome checkOnly update =
      if checkOnly then { written := noWrite, exited := true }
      else { written := (if update then latest else standard), exited := false }

  Both observable effects — the emitted-artifact kind (``WriteKind``:
  ``noWrite``/``latest``/``standard``) and whether the process aborted with a
  non-zero status (``exited : Bool``) — are recorded together in
  ``StepOutcome``, which derives ``DecidableEq``. The post-image is grounded
  entirely in the two inputs (``stepOutcome`` is a plain ``def`` over two
  ``Bool``s; the ``axioms`` region is empty), so a wrong impl cannot verify by
  echoing an opaque answer-key — it must reproduce the decision.

WHICH CLAUSE CONSTRAINS THE IMPL, AND HOW THE THREE INTERLOCK.
  * C1 pins the WHOLE result to ``stepOutcome checkOnly update`` at every input —
    it alone senses every wrong decision (wrong artifact kind, wrong abort flag,
    wrong branch).
  * C2 is the DISCRIMINATING guarantee of the fix: a check-only run must emit NO
    artifact. It projects C1's ``written`` field on the ``checkOnly = true``
    sub-domain. This is the clause the pre-change control flow violates — it
    emitted an artifact FIRST and aborted afterwards, so a check-only query left
    a migration artifact behind (``written`` was ``latest``/``standard``, never
    ``noWrite``). The behavioural delta of the gold patch is exactly restoring
    ``checkOnly ⇒ written = noWrite``, which the F2P (a ``--check`` run must
    produce no migration file) keys on.
  * C3 pins the abort observable to the query flag: the process aborts iff it is
    a check-only query. This is the control-flow-effect defence — raise-vs-return
    is invisible to the artifact value alone, so C3 forbids both "silently
    report success in check mode" (return without aborting) and "abort on a
    normal emit run".

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts ONE function ``produce_changes_or_report(store, check_mode,
update_variant)`` whose observables are spread across a MUTABLE ``store`` (a
produced-file token list at FULL permission) and a control-flow effect
(normal-return vs a ``CheckFailureExit`` raise), pinned by a GROWTH bound
(``len(store) >= len(Old)+1``), a PREFIX-preservation conjunct, an
``Ensures(not check_mode)`` normal-return guard, and an EXIT-FIRST Exsures
conjunct (``ToSeq(store) == Old(ToSeq(store))``). This bundle models the SAME
branch, but its two observable effects are folded into a single returned value:
the unbounded ``store`` growth collapses to the finite ``WriteKind`` (which
artifact was emitted, or none), and the raise-vs-return effect to the ``exited``
``Bool``. Every nagini clause has a counterpart on this finite carrier:

    nagini clause                              -> velvet clause
    ----------------------------------------------------------------------------
    Exsures ToSeq(store)==Old (EXIT-FIRST)     -> C2  (checkOnly ⇒ written=noWrite)
    Ensures(not check_mode) (normal-return)    -> C3  (out.exited = checkOnly)
    len(store) >= len(Old)+1 (GROWTH pin)      -> C1  (written ≠ noWrite off-check)
    PREFIX / ToSeq structure                   -> subsumed by C1 (whole-result pin)

The unbounded-store machinery (a token list, its length, its old value) has no
finite counterpart, but the DECISION it witnessed — did a writer run before the
abort? did the normal path reach a writer? — is pinned exactly by C1/C2/C3 over
the finite ``WriteKind``. So this is carrier narrowing (the abstraction is
coarser), not a coverage gap in what IS modeled; the footer accounts for every
nagini case.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS, and the nagini sibling ITSELF records
    the class as inapplicable: its ``store`` is held at FULL permission (there is
    no read-only input to overwrite), so the Acc(.,1/2) frame-mutation class does
    not apply even there. Lean/Velvet are referentially transparent:
    ``checkOnly`` and ``update`` are immutable values (neither ``mut``), there is
    no heap, aliasing or permission system. No substitute probe is fabricated.
  * VALUE-LEVEL STORE ATTACK — the nagini ``mutate-then-exit-in-check`` rival
    (append a token, THEN raise in check mode) does have a counterpart here, but
    it COINCIDES with the write-then-exit rival: on this carrier "emit an
    artifact before aborting in check mode" is precisely an ``exited=true`` run
    whose ``written ≠ noWrite``, i.e. a C2 violation identical to
    rival-write-then-exit. It is not a distinct point (both refute at
    ``(checkOnly=true, update=false)`` for the same C2 reason), so it is merged,
    not fabricated as a separate case (footer).
  * ADMISSIBILITY — the method carries NO ``require`` clause (precondition ≡
    True), so the nagini admiss-self-call's "a normal in-domain input satisfies
    the precondition" probe is vacuous. Re-aimed at the residual total-domain
    risk: that the three-clause post-image is jointly SATISFIABLE by a gold-shaped
    computation (else SPEC-UNSATISFIABLE) — witnessed by the frozen impl
    discharging all three ensures.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent total function
    of the two inputs (``stepOutcome``), not an axiomatized oracle; the
    ``axioms`` region is empty. The cheapest correct impls are carried as
    positive controls.

CARRIER NOTE — why this port refutes at CONCRETE literals (no conditioning).
The carrier is fully transparent and finite: ``Bool`` inputs, ``StepOutcome`` a
two-field structure over a three-constructor ``WriteKind``, all deriving
``DecidableEq``. So every reject witness reaches the method's contract through
Velvet's own tester machinery (``runCheckedWriteTester checkOnly update``) at a
concrete literal pair and closes by ``decide`` — no hypothesis about an opaque
term is needed, so no witness binds anything and the gate's consistency probe
has nothing to check. The frozen solution is STRAIGHT-LINE and also reduces
under ``decide``; the witness fails against gold purely because gold SATISFIES
the spec at that input (the tester returns ``true``, so ``... = false`` is
provably false — the verifier reports ``decide proved ... is false``), which is
the required discriminator. Checked in a file whose ``prove_correct`` block is
stripped, so no tactic script can mask the verdict. Every reject witness below
was run against both the rival (elaborates, exit 0) and the frozen solution
(fails, exit 1) with two real builds.

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

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries three
axiom-soundness/containment probes over the real ``Command.write_migration_files``
/ ``write_to_last_migration_files`` writers; that is G-AX's job (axiom_check.py /
mapping.md §3 — the abort primitive is an A-reference, no consumed axiom) and the
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16116"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole frozen impl body (text strictly between
# ---- -- impl-start and -- impl-end, comments included). Lies wholly inside the
# ---- single impl region and is unique in Solution.lean (both facts asserted at
# ---- load by _swap), so every variant's edit is confined to the elided impl
# ---- region and same_spec holds by construction.
_IMPL = (
    "    if checkOnly then\n"
    "      -- Query mode: abort with a non-zero status before any artifact is emitted.\n"
    "      return { written := WriteKind.noWrite, exited := true }\n"
    "    else\n"
    "      -- Emit mode: fold into the most recent migration on update, else emit a\n"
    "      -- fresh migration; do not abort.\n"
    "      let wk := if update then WriteKind.latest else WriteKind.standard\n"
    "      return { written := wk, exited := false }"
)

assert _BASE.count(_IMPL) == 1, "frozen impl region drifted; update _IMPL"

# ---- the frozen proof, verbatim. It is generic over the impl shape and closes
# ---- for the nested-else reshape and for every reject rival unchanged (the
# ---- rejection is carried by the witness, not by whether the frozen tactic
# ---- happens to break on the reshape). The branch-reorder positive flips the
# ---- `update` polarity, whose residual `if` no longer reduces under `simp_all`
# ---- alone, so THAT positive (and only it) retunes the elided tactic body — a
# ---- change confined to the proof region, obligation STATEMENT byte-identical.
_PROOF = (
    "prove_correct runCheckedWrite by\n"
    "  loom_solve <;> simp_all [stepOutcome]"
)

assert _BASE.count(_PROOF) == 1, "frozen proof region drifted; update _PROOF"


def _impl(body):
    """Full Solution.lean variant with only the impl body replaced (spec view and
    frozen proof untouched)."""
    return _swap(_BASE, _IMPL, body)


def _impl_reproved(body, new_proof):
    """Impl body replaced AND the elided proof tactic retuned (obligation
    statement byte-identical). For a correct reshape whose residual goal the
    frozen tactic no longer closes."""
    return _swap(_impl(body), _PROOF, new_proof)


# ---- witness builder. Reaches the method contract through Velvet's tester
# ---- machinery: `runCheckedWriteTester co u = false` says the extracted
# ---- program's result violates the postcondition at the concrete input (co, u).
# ---- Checked in a file whose `prove_correct` block is stripped; closes by
# ---- `decide` on the transparent finite carrier. Binds nothing (literal
# ---- inputs), so the gate's consistency probe is a no-op.
def _witness(call):
    return (
        "extract_program_for runCheckedWrite\n"
        "prove_precondition_decidable_for runCheckedWrite\n"
        "prove_postcondition_decidable_for runCheckedWrite\n"
        "derive_tester_for runCheckedWrite\n\n"
        f"example : {call} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the clause is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-reorder-branches",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the check-only abort FIRST, but rewrite the emit-mode
        # dispatch in the OPPOSITE branch order (test `!update` first, fresh
        # migration in the then-branch, fold-into-latest in the else-branch).
        # Semantically identical (both `WriteKind`s satisfy the same C1), a
        # different control-flow source. The `update` polarity flip leaves a
        # residual `if` the frozen `simp_all` does not reduce, so the elided proof
        # tactic is retuned (case-split `update` first) — obligation STATEMENT
        # byte-identical. If it fails to verify, C1 is over-fit to one
        # emit-branch order => SPEC-TOO-STRONG.
        "module": _impl_reproved(
            "    if checkOnly then\n"
            "      return { written := WriteKind.noWrite, exited := true }\n"
            "    else\n"
            "      let wk := if !update then WriteKind.standard else WriteKind.latest\n"
            "      return { written := wk, exited := false }",
            "prove_correct runCheckedWrite by\n"
            "  loom_solve <;> (try cases update) <;> simp_all [stepOutcome]"),
        "rationale": (
            "structurally-different but semantically identical: check-only abort "
            "kept FIRST, emit-mode dispatch rewritten in the opposite branch order "
            "(`!update` first). Both WriteKinds satisfy the same C1, so C1/C2/C3 "
            "still hold. Ports the nagini pos-control-reorder-writers. The `update` "
            "polarity flip leaves a residual `if` the frozen `simp_all` alone does "
            "not close, so the elided proof body is retuned (case-split `update`), "
            "obligation statement unchanged. Must verify, else the postcondition is "
            "over-fit to one emit-branch order => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-nested-else",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the check-only abort guard, but nest the emit-mode writer
        # dispatch as an explicit if/else on `update` returning a full record in
        # each branch, instead of binding a `WriteKind` local. Same semantics, a
        # different block structure; the frozen proof closes unchanged.
        "module": _impl(
            "    if checkOnly then\n"
            "      return { written := WriteKind.noWrite, exited := true }\n"
            "    else\n"
            "      if update then\n"
            "        return { written := WriteKind.latest, exited := false }\n"
            "      else\n"
            "        return { written := WriteKind.standard, exited := false }"),
        "rationale": (
            "a correct impl with a DIFFERENT block structure (emit-mode dispatch "
            "nested as an explicit if/else returning a full record per branch "
            "instead of binding a WriteKind local); same semantics. Ports the "
            "nagini pos-control-nested-else. The frozen `prove_correct` body closes "
            "unchanged. If it fails to verify the spec is over-fit to the "
            "local-binding code form => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-self-call. That case
    # established that the precondition admits an F2P-shaped in-domain input. This
    # method carries NO `require` clause (precondition ≡ True), so nothing could
    # exclude a normal input and the classic probe is vacuous. Re-aimed at the
    # residual total-domain risk: that the three-clause post-image is jointly
    # SATISFIABLE by a gold-shaped computation. The frozen impl discharging all
    # three ensures IS that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the step is total over both mode "
            "flags; the gold impl discharging all three ensures is the "
            "admissibility witness that the post-image (C1 whole-result plus the "
            "C2 no-artifact projection and the C3 abort==query pin) is jointly "
            "satisfiable across the whole flag domain. Near-trivial precisely "
            "because the precondition is empty. Re-aimed from the nagini "
            "admiss-self-call, whose precondition-admits-a-normal-input half has no "
            "counterpart on this referentially-transparent carrier with no require "
            "clause. Else SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary BOTH input
    # binders across all four (checkOnly, update) points (pts=4); no point is
    # pinned across the battery.
    # =====================================================================
    {
        "id": "rival-write-then-exit",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating bug (pre-change statement order): emit the artifact
        # FIRST, then set the abort flag in check mode. So in check mode the
        # artifact was already emitted before the abort — written ≠ noWrite while
        # exited = true. Correct on every non-check input. Also subsumes the
        # nagini value-level mutate-then-exit-in-check rival (any artifact emitted
        # before the check-mode abort is the same C2 violation).
        "module": _impl(
            "    let wk := if update then WriteKind.latest else WriteKind.standard\n"
            "    if checkOnly then\n"
            "      return { written := wk, exited := true }\n"
            "    else\n"
            "      return { written := wk, exited := false }"),
        "refinement": (
            "this is the pre-change statement order verbatim (emit the artifact "
            "first, then abort in check mode). Its faithful real patch is the "
            "unpatched command, which in a check-only run WRITES the migration "
            "artifact and THEN aborts non-zero. The failing test asserts a "
            "check-only run produces NO migration artifact on disk — the pre-change "
            "order leaves the file behind — so the faithful real patch FAILS the "
            "F2P and does NOT resolve. This is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C2 (`checkOnly = true → written = noWrite`), also C1: for "
            "a check-only run the impl emits an artifact (written = latest/standard) "
            "before aborting, so written ≠ noWrite while C2 forces noWrite. Refuted "
            "at (checkOnly=true, update=false) — written = standard ≠ noWrite. "
            "Subsumes the nagini mutate-then-exit-in-check rival on this carrier. "
            "If it verified => SPEC-TOO-WEAK (admits the very bug the patch fixes)."
        ),
        "witness": _witness("runCheckedWriteTester true false"),
    },
    {
        "id": "rival-no-raise-in-check",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow-effect rival: in check mode emit no artifact (correct
        # there) but DO NOT abort — return with exited = false. The artifact
        # observable is right; only the abort flag is wrong.
        "module": _impl(
            "    if checkOnly then\n"
            "      return { written := WriteKind.noWrite, exited := false }\n"
            "    else\n"
            "      let wk := if update then WriteKind.latest else WriteKind.standard\n"
            "      return { written := wk, exited := false }"),
        "refinement": (
            "drops the check-mode abort: a check-only run emits no artifact but "
            "returns a zero/normal status. A faithful real patch that removed the "
            "non-zero exit would make a check-only run report success even when "
            "migrations are missing — the failing test asserts a NON-ZERO exit on "
            "pending changes (the whole point of the check flag), so the faithful "
            "real patch FAILS the F2P and does NOT resolve."
        ),
        "rationale": (
            "REJECT from C3 (`out.exited = checkOnly`): a check-only run returns "
            "exited = false while C3 forces exited = true. The artifact observable "
            "is correct here, so ONLY C3 senses the defect — the control-flow-effect "
            "clause. Refuted at (checkOnly=true, update=true) — a DISTINCT point "
            "from rival-write-then-exit, varying `update` on the check sub-domain. "
            "If it verified => SPEC-TOO-WEAK (the abort effect unconstrained, the "
            "'silently report success' cheat admitted)."
        ),
        "witness": _witness("runCheckedWriteTester true true"),
    },
    {
        "id": "rival-check-returns-normally",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow-effect rival, leaner: ignore checkOnly entirely — ALWAYS
        # emit the artifact and never abort, even in check mode. Distinct shape
        # from rival-no-raise-in-check (single dispatch, no check-mode branch).
        "module": _impl(
            "    let wk := if update then WriteKind.latest else WriteKind.standard\n"
            "    return { written := wk, exited := false }"),
        "refinement": (
            "omits the check-mode guard entirely: ALWAYS emits an artifact and "
            "returns normally, even in a check-only run. Faithful real patch = the "
            "command with the check-mode abort deleted: a check-only run writes the "
            "migration and exits zero, failing both the non-zero-exit and the "
            "no-artifact assertions of the failing test — does NOT resolve."
        ),
        "rationale": (
            "REJECT from C2 and C3 (and C1): in a check-only run it emits an "
            "artifact (written ≠ noWrite, violating C2) and returns exited = false "
            "(violating C3). Refuted at (checkOnly=true, update=false) — written = "
            "standard ≠ noWrite. Leaner single-dispatch shape than "
            "rival-no-raise-in-check. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("runCheckedWriteTester true false"),
    },
    {
        "id": "rival-skip-writer",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip the writer on the normal (non-check) path: abort correctly in check
        # mode, but outside check mode emit NO artifact (written = noWrite) and do
        # not abort. The abort observable is correct everywhere; only the emit
        # observable is wrong, on the non-check sub-domain.
        "module": _impl(
            "    if checkOnly then\n"
            "      return { written := WriteKind.noWrite, exited := true }\n"
            "    else\n"
            "      return { written := WriteKind.noWrite, exited := false }"),
        "refinement": (
            "aborts correctly in a check-only run but on the normal (non-check) "
            "path emits NO artifact — never reaches a writer. A faithful real patch "
            "that skipped the writer dispatch would make an ordinary (non-check) "
            "run produce no migration file, failing the command's core "
            "artifact-writing behaviour (a P2P: the command must actually write "
            "migrations) — would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = stepOutcome checkOnly update`): the normal path "
            "must emit an artifact (written = standard/latest), but this impl emits "
            "noWrite. The C3 abort flag is correct (exited = false = checkOnly), so "
            "ONLY C1's written field senses the defect. Refuted at (checkOnly=false, "
            "update=false) — written = noWrite ≠ standard. A DISTINCT point on the "
            "non-check sub-domain, varying `checkOnly` to false. If it verified => "
            "SPEC-TOO-WEAK (artifact-production on the normal path not enforced)."
        ),
        "witness": _witness("runCheckedWriteTester false false"),
    },
    {
        "id": "rival-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain rival: gate the check-only abort on `update` too
        # (`checkOnly && update`). Correct on (check & update) and every non-check
        # input, but for (checkOnly=true, update=false) it falls through to the
        # emit branch, emits a FRESH artifact and returns exited = false — the
        # pre-change bug on exactly the fresh-writer check sub-case.
        "module": _impl(
            "    if checkOnly && update then\n"
            "      return { written := WriteKind.noWrite, exited := true }\n"
            "    else\n"
            "      let wk := if update then WriteKind.latest else WriteKind.standard\n"
            "      return { written := wk, exited := false }"),
        "refinement": (
            "gates the check-only abort on `update` too. Correct on (check & "
            "update) and all non-check inputs, but for (checkOnly=true, "
            "update=false) it falls through, emits a FRESH migration, and returns a "
            "normal status — i.e. a check-only run WITHOUT the update flag writes a "
            "file and exits zero. That is the pre-change bug on the fresh-writer "
            "sub-domain (the exact failing-test configuration: a plain check-only "
            "run), so a faithful real patch of this shape does NOT resolve."
        ),
        "rationale": (
            "partial-domain rival: correct on most of the flag domain, wrong on the "
            "(check, not-update) sub-domain. REJECT from C2 and C3: for "
            "(checkOnly=true, update=false) it emits written = standard ≠ noWrite "
            "(C2) and returns exited = false ≠ true (C3). Ports the nagini "
            "rival-partial-domain-update-gated-exit. Refuted at (checkOnly=true, "
            "update=false). If it verified => SPEC-TOO-WEAK (domain-incomplete on "
            "the check-only abort)."
        ),
        "witness": _witness("runCheckedWriteTester true false"),
    },
    {
        "id": "rival-abort-on-emit",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (no nagini sibling; closes an unattacked HALF of C3).
        # Every other rival that gets `exited` wrong does so on the CHECK
        # sub-domain (checkOnly=true), i.e. it fails to abort when it should.
        # The OPPOSITE direction — aborting when it must NOT — was asserted by
        # the C3 docstring but demonstrated by no case. This rival emits the
        # correct artifact on every input and aborts in check mode correctly,
        # but ALSO aborts on the normal emit path: exited = true everywhere.
        # So `written` is right at all four points and only C3's off-check
        # direction senses it.
        "module": _impl(
            "    if checkOnly then\n"
            "      return { written := WriteKind.noWrite, exited := true }\n"
            "    else\n"
            "      let wk := if update then WriteKind.latest else WriteKind.standard\n"
            "      return { written := wk, exited := true }"),
        "refinement": (
            "aborts with a non-zero status on the ORDINARY (non-check) path as "
            "well as the query path, while emitting exactly the right artifact "
            "everywhere. A faithful real patch of this shape would make an "
            "ordinary run terminate with a non-zero status after correctly "
            "emitting its migration — so every ordinary-run test (the P2P set "
            "that invokes the command without the check flag and requires it to "
            "succeed, including the update-flag and default-verbosity cases) "
            "fails on the exit status. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from C3 (`out.exited = checkOnly`) in the direction no other "
            "rival exercises: C3 is an EQUALITY, so it forbids aborting on a "
            "normal emit run just as it forbids not aborting on a query. Refuted "
            "at (checkOnly=false, update=false) — exited = true while C3 forces "
            "false. The artifact observable is correct at all four points, so "
            "ONLY C3 senses the defect, and only off-check. Every other "
            "exited-wrong rival (no-raise-in-check, check-returns-normally, "
            "partial-domain) diverges on the checkOnly=true sub-domain, so "
            "without this case the off-check half of C3 was claimed but never "
            "demonstrated. If it verified => SPEC-TOO-WEAK (a spurious abort on "
            "the ordinary path unconstrained)."
        ),
        "witness": _witness("runCheckedWriteTester false false"),
    },
    {
        "id": "rival-ignore-update",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no direct nagini sibling — its store model does not distinguish
        # WHICH writer ran, only THAT one ran). Emit a FRESH migration regardless
        # of `update`: on the emit path always written = standard, ignoring the
        # fold-into-latest request. Correct on (not-check, not-update) and every
        # check input; wrong only when update is requested off-check. Exists to
        # VARY the `update` binder on the non-check sub-domain — otherwise no rival
        # senses the `latest`-vs-`standard` distinction and a rival mishandling
        # only that field would verify.
        "module": _impl(
            "    if checkOnly then\n"
            "      return { written := WriteKind.noWrite, exited := true }\n"
            "    else\n"
            "      return { written := WriteKind.standard, exited := false }"),
        "refinement": (
            "ignores the update flag on the emit path: always emits a fresh "
            "migration, never folding detected changes into the most recent "
            "existing migration. A faithful real patch that always emitted a fresh "
            "migration would make an update-requested run produce a new migration "
            "instead of folding — the update-flag tests (test_makemigrations_update "
            "and its siblings, all P2P here) assert the changes are folded into the "
            "latest migration, so the faithful real patch FAILS them and does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = stepOutcome checkOnly update`): on the emit "
            "path C1 pins written = latest when update is true, but this impl emits "
            "standard, ignoring the update binder. The abort flag and the check "
            "sub-domain are correct, so ONLY C1's dependence on `update` senses the "
            "defect. Refuted at (checkOnly=false, update=true) — written = standard "
            "≠ latest — the ONLY point that varies `update` to true off-check, so "
            "the battery is not silent on the fold-into-latest observable. If it "
            "verified => SPEC-TOO-WEAK (the artifact kind's dependence on `update` "
            "unconstrained)."
        ),
        "witness": _witness("runCheckedWriteTester false true"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus a 3-entry AXIOM lane,
# over ONE function whose observables are a MUTABLE token-list `store` (FULL
# permission) and a normal-return-vs-raise control-flow effect, pinned by a
# GROWTH bound + PREFIX conjunct + `Ensures(not check_mode)` + an EXIT-FIRST
# Exsures conjunct. THIS bundle models the SAME branch but folds those observables
# into a single returned `StepOutcome` over the finite `WriteKind` (which
# artifact, or none) and `exited : Bool` (aborted?), pinned by C1 (whole result =
# `stepOutcome`), C2 (`checkOnly ⇒ written = noWrite`) and C3 (`out.exited =
# checkOnly`). Every nagini clause has a finite counterpart (docstring table), so
# every nagini SPEC case ports; the store's unbounded length has no finite image
# but the DECISION it witnessed is pinned by C1/C2/C3. Every nagini case is
# accounted for below.
#
#   nagini case                             -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder-writers             -> pos-control-reorder-branches  PORTED (proof retuned)
#   pos-control-nested-else                 -> pos-control-nested-else       PORTED
#   admiss-self-call                        -> admiss-gold-total             RE-AIMED
#   rival-write-then-exit                   -> rival-write-then-exit         PORTED (THE bug-delta)
#   rival-no-raise-in-check                 -> rival-no-raise-in-check       PORTED
#   rival-check-returns-normally            -> rival-check-returns-normally  PORTED
#   rival-skip-writer                       -> rival-skip-writer             PORTED
#   rival-partial-domain-update-gated-exit  -> rival-partial-domain          PORTED
#   rival-mutate-then-exit-in-check         -> (merged into write-then-exit) MERGED
#   (new, no sibling)                       -> rival-ignore-update           ADDED (binder coverage)
#   (new, no sibling)                       -> rival-abort-on-emit           ADDED BY AUDIT (C3 off-check half)
#   AXIOM_TESTS (3 entries)                 -> (none)                        DROPPED (G-AX lane)
#
# 10 velvet SPEC cases: 2 soundness, 1 admissibility, 7 uniqueness.
#
# PORTED (5 rivals + 2 positives): every nagini case attacking a modeled clause
#   carries across; only the carrier changes (a `List[int]` store fold to a finite
#   `StepOutcome` return). rival-write-then-exit (the pre-change order, THE
#   discriminating bug; C2), rival-no-raise-in-check (returns normally in check
#   mode; C3), rival-check-returns-normally (leaner, ignores check; C2+C3),
#   rival-skip-writer (normal path emits nothing; C1), rival-partial-domain
#   (update-gated abort, wrong on the (check, not-update) sub-case; C2+C3). Each
#   keeps its nagini refinement argument, now backed by a machine-checked witness.
#   The two positives (reorder-branches, nested-else) reshape the impl and verify;
#   the reorder positive retunes the elided proof tactic (`update` polarity flip)
#   with a byte-identical obligation statement.
# RE-AIMED (admiss-self-call -> admiss-gold-total): the nagini case established
#   the precondition admits an in-domain input. This method has no `require`, so
#   that probe is vacuous; re-aimed at the residual total-domain risk (three-clause
#   post-image joint satisfiability), witnessed by the frozen impl.
# MERGED (rival-mutate-then-exit-in-check -> rival-write-then-exit): the nagini
#   value-level attack appends a store token then raises in check mode. On this
#   finite carrier "emit an artifact before aborting in check mode" IS an
#   `exited=true` run with `written ≠ noWrite` — the identical C2 violation at the
#   identical point (checkOnly=true, update=false) as rival-write-then-exit. Not a
#   distinct case; folded in rather than fabricated as a duplicate.
# ADDED (rival-ignore-update): no direct nagini sibling — the nagini store model
#   records only THAT a writer ran, not WHICH, so it cannot distinguish
#   fold-into-latest from fresh-emit. This carrier's `WriteKind` does, and C1 pins
#   the artifact kind to `update`. This rival ignores `update` (always emits
#   standard); a real divergence with a machine-checked witness at (checkOnly=false,
#   update=true), grounded by the update-flag P2P tests. It exists to VARY the
#   `update` binder on the non-check sub-domain so the battery is not silent on the
#   `latest`-vs-`standard` observable — not fabricated wrongness.
# ADDED BY AUDIT (rival-abort-on-emit): C3 is an EQUALITY (`out.exited =
#   checkOnly`), so it has two failure directions. Enumerating every rival's
#   behaviour at all four points showed that all three exited-wrong rivals
#   (no-raise-in-check, check-returns-normally, partial-domain) diverge only on
#   the checkOnly=true sub-domain — none of them ever aborts when it must not.
#   The C3 docstring nonetheless claimed the clause forbids "abort on a normal
#   emit run", a half the battery never demonstrated: a rival that spuriously
#   aborted off-check was unattacked. This case supplies it (correct artifact at
#   all four points, exited = true everywhere), machine-checked: rival build
#   exit 0, gold build exit 1 with `decide proved runCheckedWriteTester false
#   false = false is false`. Its own variant build is rejected on the
#   `ensures_1: out.exited = checkOnly` goal, i.e. by C3 alone.
# FRAME-MUTATION: VACUOUS, and the nagini sibling itself omits it (its store is
#   FULL permission — no read-only input to overwrite — so the Acc(.,1/2) class
#   is inapplicable even there). Velvet is referentially transparent; the two mode
#   flags are immutable values, no `mut` binder, no heap, no permission system. No
#   substitute fabricated.
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
# DROPPED (AXIOM_TESTS, 3): the nagini file's axiom-soundness/containment probes
#   over the real migration writers are G-AX's job (axiom_check.py / mapping.md);
#   the G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. Every top-level clause is attacked: C1
#   (whole-result pin) by rival-skip-writer and rival-ignore-update; C2 (check ⇒
#   no artifact — the fix's discriminator) by rival-write-then-exit,
#   rival-check-returns-normally and rival-partial-domain; C3 (abort == query) by
#   rival-no-raise-in-check, rival-check-returns-normally and rival-partial-domain
#   on the checkOnly=true side (failing to abort on a query) and by
#   rival-abort-on-emit on the checkOnly=false side (aborting on an ordinary
#   run). BOTH directions of the C3 equality are therefore demonstrated, not just
#   claimed; the off-check half was added by the audit.
#   Both input binders are varied: `checkOnly` ∈ {true, false} and `update` ∈
#   {true, false}, across all FOUR (checkOnly, update) points — (true,false),
#   (true,true), (false,false), (false,true) — so pts=4 and no binder is held
#   fixed by every witness. Both positives and the admissibility case defend all
#   three clauses on gold.
#
# WITNESS MECHANICS: the carrier is fully transparent and finite (Bool inputs,
#   StepOutcome/WriteKind deriving DecidableEq), so every witness reaches the
#   contract through Velvet's tester machinery (`runCheckedWriteTester co u`) at a
#   concrete literal pair and closes by `decide`. No witness binds a hypothesis,
#   so the gate's consistency probe is a no-op. The frozen solution is
#   straight-line and reduces under `decide` too; each witness fails against gold
#   because gold SATISFIES the spec at that input (tester returns true, so
#   `... = false` is provably false). All seven checked with scripts/lean_verify.sh:
#   rival build exit 0 (elaborates), gold build exit 1 (`decide proved ... is
#   false`).
AXIOM_TESTS = []
