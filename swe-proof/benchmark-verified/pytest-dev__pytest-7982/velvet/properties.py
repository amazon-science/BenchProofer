"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7982 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct descendableEntries`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is judged by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates).

DEFENDED SURFACE (one contracted method over one read-only sequence input):

  descendableEntries (entries : List DirChild) return (out : List DirChild)
    ensures out = descendableSeq entries

where each child is observed through three read-only booleans — ``isDirectory``
(the entry denotes a directory once symbolic links ARE resolved),
``isDirectoryNoFollow`` (denotes a directory when links are NOT resolved), and
``shouldRecurse`` (the walk's recursion predicate accepts it) — and

  descendableSeq  keeps each child the guard ``descend`` accepts, IN ORDER;
  descend e   ==  e.isDirectory && e.shouldRecurse.

The single top-level post-image clause is a list EQUALITY, so it carries three
independent obligations that a rival can attack separately:

  (a) MEMBERSHIP — which children are kept: exactly those whose guard holds,
      where the guard is a grounded function of the child's own two load-bearing
      observations (``isDirectory``, ``shouldRecurse``);
  (b) ORDER — the kept children appear in their original encounter order;
  (c) MULTIPLICITY — each kept child appears exactly once. A set-plus-order
      reading of the clause would miss this, so it carries its own rival
      (``reject-duplicate-kept``), correct on both (a) and (b).

The discriminating observation for (a) is the link-to-directory child,
``isDirectory = true`` while ``isDirectoryNoFollow = false``: the desired
behaviour keeps it; the pre-image skeleton (which reads the non-resolving
observation) drops it. The failing scenario requires a selected
link-to-directory to be descended into, so any rival that routes the guard
through the wrong observation fails it. Note ``isDirectoryNoFollow`` is INERT in
the post-image — the spec never reads it — which is precisely why a rival CAN
route the guard through it, and why the battery must probe that.

CARRIER NOTE — WHY EVERY REJECT CASE CARRIES A ``witness_reference``.
The carrier itself is fully transparent: three ``Bool`` fields, no opaque callee,
no arithmetic, so every refutation is a concrete ``decide`` and no
conditioning-on-the-carrier is needed. The obstacle is on the GOLD side, not the
rival side. The frozen impl builds its result with a backward ``while`` loop, and
under ``loom.semantics.choice "demonic"`` the loop's fixpoint elaborates through
``Classical.choice``, which the kernel cannot unfold. Measured: a witness built
against the frozen solution fails with

    Tactic `decide` failed ... because its `Decidable` instance
      ... did not reduce to `isTrue` or `isFalse`

which is the SAME error a TRUE claim about that impl produces. So the frozen
side's exit code discriminates nothing, and a battery that read it as "gold
satisfies the spec here" would be attesting to a refutation never performed.
(That is exactly the ``witness-undecided`` outcome this cell recorded before.)

The repair is the sanctioned one: every reject case names ``_LOOPFREE`` as its
``witness_reference`` — a loop-free variant that implements the frozen spec
CORRECTLY (a straight ``List.filter`` with a reproved obligation) and therefore
DOES reduce. Measured against it, the same witness fails with

    Tactic `decide` proved that the proposition ... is false

a real refutation verdict. The reference is not trusted: the gate independently
checks that it shares the frozen spec and VERIFIES before using it. It is also
shipped as the ``pos-loopfree-filter`` positive control, so the battery itself
records that loop-freeness is not what any rival is being rejected for — the
reject rivals and the reference differ only in the GUARD, never in loop-shape.

ADVERSARIAL READ of the sibling's classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling notes its own inputs
    are pure values carrying no heap permission, so even there the
    overwrite-a-read-only-input attack is N/A. Here the point is structural: the
    carrier is an immutable ``List DirChild``, this bundle declares no ``mut``
    parameter, there is no heap and no aliasing. Nothing to overwrite and no
    permission system to trip. No substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the method's own argument (``descendableSeq`` and ``descend`` are
    concrete ``def``s in the ``pure`` region; the ``axioms`` region declares no
    ``axiom`` and no opaque callee). There is no answer-key term a wrong impl
    could echo.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the membership reject surface.
  * ORDER — an attack surface this carrier has and the sibling's did NOT (its
    per-index post-image pinned position implicitly). Attacked explicitly.

WITNESS PLACEMENT. Rivals share no refutation point; the seven reject witnesses
sit at SEVEN distinct input points and between them move every binder off any
fixed value. ``isDirectory``: both true and false. ``shouldRecurse``: both true
and false. ``isDirectoryNoFollow`` — the INERT field — both true and false, and
crucially at a point where it DISAGREES with ``isDirectory`` (the
link-to-directory child), which is the only place a guard routed through the
wrong observation is visible. List length: 1 and 2, and at length 2 the
descendable child is placed first (``partial-first``), second
(``duplicate-kept``) and in both positions (``order-reversed``). A rival that
mishandled only one of these could not survive all seven.

ADMISSIBILITY lane: shipped, as ``admiss-postimage-satisfiable``. The frozen
obligation carries no ``require``, but that is not a reason to drop the lane: the
analogue on this total carrier is the post-image being UNSATISFIABLE at an input
the defended behaviour turns on, which the uniqueness cases (each compares a
rival against the clause) and the soundness cases (each reshapes an impl that
already satisfies it) structurally cannot detect. The case discharges the
post-image BY EVALUATION at the three load-bearing points — the kept
link-to-directory child, a skipped non-directory child, and a two-child level
pinning encounter order — then ``clear``s those facts before closing the frozen
obligation verbatim, so it can only fail if one of the three is unreachable.

AXIOM lane: this bundle consumes no ``axiom`` and declares no opaque callee (the
``axioms`` region is a comment only). There is no axiom-soundness obligation for
this gate to probe, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7982"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. All lie wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region and are unique in Solution.lean (both facts asserted
# ---- by _swap at import). ----

# The whole frozen backward-fold loop (the impl region interior). Replaced
# wholesale by the loop-free reference and by each reject rival, so that the
# variant's extracted program reduces under `decide` (see CARRIER NOTE).
_IMPL = (
    "    let mut result : List DirChild := []\n"
    "    let mut i := entries.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ entries.length\n"
    "      invariant result = descendableSeq (entries.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let e := entries[i - 1]!\n"
    "      result := (if e.isDirectory && e.shouldRecurse then [e] else []) ++ result\n"
    "      i := i - 1\n"
    "    return result"
)

# The single guard line (loop body) — the loop-keeping positives reshape only it.
_GUARD = (
    "      result := (if e.isDirectory && e.shouldRecurse then [e] else []) ++ result"
)

# The read-and-guard pair (the positive that binds a local).
_READ_GUARD = (
    "      let e := entries[i - 1]!\n"
    "      result := (if e.isDirectory && e.shouldRecurse then [e] else []) ++ result\n"
    "      i := i - 1"
)

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen
# ---- backward-fold loop (it discharges the loop-body goal via the drop-step
# ---- lemma). A variant that reshapes the impl leaves a different residual, so
# ---- the tactic body is retuned. The impl region and the `prove_correct` body
# ---- are both elided from the spec view, so same_spec still holds and the
# ---- obligation survives with an identical header. Unique in the file. ----
_PROOF = (
    "prove_correct descendableEntries by\n"
    "  loom_solve\n"
    "  rw [descendableSeq_drop_step entries i (by omega) (by omega)]\n"
    "  simp_all"
)

for _anchor, _what in ((_IMPL, "impl region"), (_GUARD, "guard"),
                       (_READ_GUARD, "read+guard"), (_PROOF, "proof region")):
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"drift: {_what} anchor is not unique in Solution.lean")


# ---------------------------------------------------------------------------
# The loop-free CORRECT reference. Shared by the whole battery: it is the
# `witness_reference` every reject case is refuted against (because the frozen
# loop cannot decide anything — CARRIER NOTE), and it is also shipped as an
# `expect="verify"` positive so the battery records that loop-freeness is not
# what any rival is rejected for. The guard is the frozen one, unchanged; only
# the loop-shape differs, and the obligation is REPROVEN for the new shape by a
# list induction (no helper lemma, no weakening — the `prove_correct
# descendableEntries` header is byte-identical). Verified by hand before
# shipping; the gate re-verifies it independently.
# ---------------------------------------------------------------------------
_LOOPFREE_PROOF = (
    "prove_correct descendableEntries by\n"
    "  loom_solve\n"
    "  induction entries with\n"
    "  | nil => rfl\n"
    "  | cons e es ih =>\n"
    "    simp only [descendableSeq_cons, descend, List.filter_cons, ih]\n"
    "    split <;> simp"
)

_LOOPFREE = _swap(
    _swap(_BASE, _IMPL,
          "    return entries.filter (fun e => e.isDirectory && e.shouldRecurse)"),
    _PROOF, _LOOPFREE_PROOF)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester
# ---- machinery: `descendableEntriesTester entries = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped,
# ---- so no tactic script can mask the verdict. Every argument is a concrete
# ---- list of Bool-triple literals, so `decide` reduces it outright and the
# ---- witness binds nothing (no hypotheses, hence no satisfiability question).
def _tester(body):
    return ("extract_program_for descendableEntries\n"
            "prove_precondition_decidable_for descendableEntries\n"
            "prove_postcondition_decidable_for descendableEntries\n"
            "derive_tester_for descendableEntries\n\n" + body)


def _child(is_dir, no_follow, recurse):
    def b(x):
        return "true" if x else "false"
    return ("{ isDirectory := %s, isDirectoryNoFollow := %s, shouldRecurse := %s }"
            % (b(is_dir), b(no_follow), b(recurse)))


def _refuted_at(children):
    """`descendableEntriesTester <list> = false` — the post-image is violated here."""
    return _tester("example : descendableEntriesTester [%s] = false := by\n  decide\n"
                   % ", ".join(children))


def _rival(impl_line):
    """A reject variant: straight-line impl, bare `loom_solve` proof body.

    The frozen tactic tail names the drop-step lemma for a loop that is no longer
    there, so it is dropped rather than retuned: a rival may rewrite the proof
    body freely (only the `prove_correct` header must survive), and leaving a
    tail that fails for a SHAPE reason would confuse the record. The rejection
    these cases are judged on is the witness's, not the tactic's.
    """
    return _swap(_swap(_BASE, _IMPL, impl_line), _PROOF,
                 "prove_correct descendableEntries by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. The first three keep the frozen backward-fold loop and
    # reshape only the executable form of the per-child guard, retuning the
    # tactic body where `simp_all` needs a hint; the fourth changes the
    # loop-shape outright and reproves the obligation.
    # =====================================================================
    {
        "id": "pos-operand-swap",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: commute the guard conjunction. `shouldRecurse && isDirectory`
        # is value-equal to `isDirectory && shouldRecurse`, so the same children
        # are kept in the same order; the post-image is unchanged.
        "module": _swap(
            _swap(_BASE, _GUARD,
                  "      result := (if e.shouldRecurse && e.isDirectory then [e] else []) ++ result"),
            _PROOF,
            "prove_correct descendableEntries by\n"
            "  loom_solve\n"
            "  rw [descendableSeq_drop_step entries i (by omega) (by omega)]\n"
            "  simp_all [Bool.and_comm]"),
        "rationale": "commuting the guard conjunction keeps exactly the same children "
                     "in the same order, so `out = descendableSeq entries` still holds "
                     "under both its membership and its order reading; a correct reorder "
                     "MUST verify (else SPEC-TOO-STRONG on conjunction order). The "
                     "tactic body clears the residual with `Bool.and_comm`.",
    },
    {
        "id": "pos-inline-descend",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: write the guard as the named `descend e` rather than its
        # inlined body. Definitionally equal, so the same children are kept.
        "module": _swap(
            _swap(_BASE, _GUARD,
                  "      result := (if descend e then [e] else []) ++ result"),
            _PROOF,
            "prove_correct descendableEntries by\n"
            "  loom_solve\n"
            "  rw [descendableSeq_drop_step entries i (by omega) (by omega)]\n"
            "  simp_all [descend]"),
        "rationale": "spelling the guard as the named `descend e` (which unfolds to the "
                     "same conjunction) is a different surface syntax of the same value, "
                     "so the post-image is unchanged and a correct reshape MUST verify. "
                     "The tactic body unfolds the named guard.",
    },
    {
        "id": "pos-local-isdir",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the directory observation to a local before conjoining.
        # Only the executable shape of computing the guard changes; the frozen
        # loop, invariants and proof stay intact.
        "module": _swap(
            _BASE, _READ_GUARD,
            "      let e := entries[i - 1]!\n"
            "      let entryIsDir := e.isDirectory\n"
            "      result := (if entryIsDir && e.shouldRecurse then [e] else []) ++ result\n"
            "      i := i - 1"),
        "rationale": "binding the directory observation to a local then conjoining with "
                     "the recursion predicate keeps every frozen invariant and the frozen "
                     "proof verbatim; only the executable shape of the guard changes, so "
                     "it MUST verify (the safe local-variable reshape).",
    },
    {
        "id": "pos-loopfree-filter",
        "kind": "soundness",
        "expect": "verify",
        # A genuinely different LOOP SHAPE for the same guard: an
        # order-preserving filter in one step instead of a backward fold. The
        # obligation is reproven for the new shape by list induction — same
        # `prove_correct` header, no helper lemma, nothing assumed.
        #
        # This is also the battery's shared `witness_reference` (CARRIER NOTE).
        # Shipping it as a positive is what makes the reject lane honest: the
        # rivals below differ from THIS impl only in the guard, so their
        # rejection cannot be blamed on loop-freeness.
        "module": _LOOPFREE,
        "rationale": "an order-preserving one-step filter with the frozen guard computes "
                     "the same list as the frozen backward fold, so `out = descendableSeq "
                     "entries` holds and it MUST verify (else SPEC-TOO-STRONG on "
                     "loop-shape). The obligation is REPROVEN for the new shape by "
                     "induction on the input list; the `prove_correct` header is "
                     "byte-identical and no lemma is added. It doubles as the shared "
                     "`witness_reference`, so the battery records on its own that "
                     "loop-freeness is not what any rival is rejected for.",
    },
    {
        "id": "pos-partition-fst",
        "kind": "soundness",
        "expect": "verify",
        # A THIRD loop-shape for the same guard: a single order-preserving
        # two-way split, taking the accepted component. Unlike the filter
        # positive this one computes BOTH components and discards one, so the
        # kept list is produced by a different library primitive with a
        # different reduction behaviour; the obligation is reproven for it by
        # induction after rewriting the split into its filter pair.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    return (entries.partition "
                  "(fun e => e.isDirectory && e.shouldRecurse)).1"),
            _PROOF,
            "prove_correct descendableEntries by\n"
            "  loom_solve\n"
            "  rw [List.partition_eq_filter_filter]\n"
            "  induction entries with\n"
            "  | nil => rfl\n"
            "  | cons e es ih =>\n"
            "    simp only [List.filter_cons] at ih ⊢\n"
            "    rw [descendableSeq_cons]\n"
            "    simp only [descend]\n"
            "    split <;> simp_all"),
        "rationale": "an order-preserving two-way split with the frozen guard, keeping "
                     "the accepted component, computes the same list as the frozen "
                     "backward fold, so `out = descendableSeq entries` holds under both "
                     "its membership and its order reading and it MUST verify (else "
                     "SPEC-TOO-STRONG on loop-shape). Distinct from "
                     "`pos-loopfree-filter`: the split evaluates the rejected component "
                     "too, so the clause is shown reprovable at a shape that is not a "
                     "syntactic reduct of the frozen return NOR of the filter positive. "
                     "The obligation is REPROVEN by induction; the `prove_correct` "
                     "header is byte-identical and no top-level lemma is added.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). The frozen obligation carries no
    # `require`, so there is no precondition to be over-strong in the literal
    # sense — but the lane is NOT vacuous here, and the analogue on a total
    # carrier is what this case tests: the post-image must be SATISFIABLE at the
    # concrete inputs that matter, not merely dischargeable somewhere. If
    # `descendableSeq` demanded an unreachable list at a failing-scenario-shaped
    # input, the obligation would be vacuously unprovable exactly there and no
    # faithful impl could exist — the spec would be unsatisfiable rather than
    # strong, and every other case in this battery would still pass.
    #
    # The three `have`s discharge the post-image BY EVALUATION at the three
    # load-bearing points: the link-to-directory child that the desired
    # behaviour KEEPS (the discriminating observation), the non-directory child
    # it SKIPS, and a two-child level where the demanded ORDER is the encounter
    # order. They are `clear`ed before `loom_solve`, so they cannot contribute to
    # the main goal: the case FAILS if any of those three post-images is
    # unsatisfiable, and proves nothing extra if all three hold. The impl region
    # is the frozen one verbatim and the frozen tactic tail closes the
    # obligation, so nothing but the elided tactic body differs.
    # =====================================================================
    {
        "id": "admiss-postimage-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct descendableEntries by\n"
            "  have hKeepLinkedDir : descendableSeq\n"
            "      [{ isDirectory := true, isDirectoryNoFollow := false,\n"
            "         shouldRecurse := true }]\n"
            "      = [{ isDirectory := true, isDirectoryNoFollow := false,\n"
            "           shouldRecurse := true }] := by\n"
            "    decide\n"
            "  have hSkipNonDir : descendableSeq\n"
            "      [{ isDirectory := false, isDirectoryNoFollow := false,\n"
            "         shouldRecurse := true }] = [] := by\n"
            "    decide\n"
            "  have hOrderKept : descendableSeq\n"
            "      [{ isDirectory := true, isDirectoryNoFollow := true,\n"
            "         shouldRecurse := true },\n"
            "       { isDirectory := true, isDirectoryNoFollow := false,\n"
            "         shouldRecurse := true }]\n"
            "      = [{ isDirectory := true, isDirectoryNoFollow := true,\n"
            "           shouldRecurse := true },\n"
            "         { isDirectory := true, isDirectoryNoFollow := false,\n"
            "           shouldRecurse := true }] := by\n"
            "    decide\n"
            "  clear hKeepLinkedDir hSkipNonDir hOrderKept\n"
            "  loom_solve\n"
            "  rw [descendableSeq_drop_step entries i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": "PASS SOURCE = the post-image is jointly SATISFIABLE at the inputs "
                     "the defended behaviour turns on, so the obligation is non-vacuous "
                     "exactly where it matters. Three `have`s evaluate "
                     "`descendableSeq` at the discriminating link-to-directory child "
                     "(kept), at a non-directory child the predicate accepts (skipped), "
                     "and at a two-child level where the demanded order is the encounter "
                     "order; each `decide`s, so none of those post-images is "
                     "unreachable. They are `clear`ed before the frozen obligation is "
                     "closed verbatim, so they cannot strengthen the main proof — the "
                     "case can only fail by one of the three being unsatisfiable. If it "
                     "did NOT verify => PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE: the "
                     "clause would pin an outcome no faithful impl could produce at a "
                     "failing-scenario-shaped input, which no uniqueness or soundness "
                     "case in this battery would detect.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input, and the refinement argument that its faithful
    # counterpart would NOT resolve the failing/unchanged tests. Each is refuted
    # against `_LOOPFREE` rather than the frozen loop, which cannot decide
    # anything (CARRIER NOTE); each differs from `_LOOPFREE` in the GUARD alone.
    # =====================================================================
    {
        "id": "reject-nofollow-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image classification: route the guard through the observation
        # that does NOT resolve symbolic links. Correct on every child except a
        # link-to-directory (isDirectory true, isDirectoryNoFollow false), which
        # it wrongly drops. The regression itself, and the near-miss that agrees
        # with the desired behaviour over the most of the domain.
        "module": _rival(
            "    return entries.filter (fun e => e.isDirectoryNoFollow && e.shouldRecurse)"),
        "refinement": "this is the pre-image classification — the directory test that does "
                      "NOT resolve symbolic links. Its faithful counterpart keeps that "
                      "non-resolving test, so a SELECTED link-to-directory is never "
                      "descended into: exactly the reported regression. The failing "
                      "scenario (a symlinked directory must be collected) still fails, so "
                      "it does NOT resolve.",
        "rationale": "REJECT from `out = descendableSeq entries` (membership): at a "
                     "link-to-directory child (`isDirectory = true`, "
                     "`isDirectoryNoFollow = false`, `shouldRecurse = true`) the desired "
                     "filter keeps it and the rival drops it. If it verified => "
                     "SPEC-TOO-WEAK — the spec would not sense the regression. Refuted at "
                     "the ONLY point where the inert `isDirectoryNoFollow` disagrees with "
                     "`isDirectory`, which is the sub-domain no other rival isolates and "
                     "the only place a guard routed through the wrong observation shows.",
        "witness": _refuted_at([_child(True, False, True)]),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-overbroad-nondir",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-broad: drop the directory observation entirely, descending into
        # any child the predicate accepts. Correct wherever `isDirectory` is
        # already true; diverges on a non-directory child the predicate accepts.
        "module": _rival("    return entries.filter (fun e => e.shouldRecurse)"),
        "refinement": "a counterpart that dropped the directory test from the guard would "
                      "descend into non-directory children (a plain file, or a link whose "
                      "target is not a directory) that the recursion predicate accepts, "
                      "walking a non-directory target and over-collecting — breaking the "
                      "unchanged collection behaviour, which admits no extra outcomes. It "
                      "does NOT resolve.",
        "rationale": "REJECT from `out = descendableSeq entries` (membership): at a "
                     "non-directory child the predicate accepts (`isDirectory = false`, "
                     "`shouldRecurse = true`) the desired filter skips it and the rival "
                     "keeps it. If it verified => SPEC-TOO-WEAK on the over-descend "
                     "sub-domain (the directory conjunct unconstrained). Refuted at the "
                     "witness that moves `isDirectory` to false.",
        "witness": _refuted_at([_child(False, False, True)]),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-drop-predicate",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the recursion predicate: descend into every directory child
        # regardless of whether the predicate accepts it. Diverges wherever a
        # directory child is rejected by the predicate.
        "module": _rival("    return entries.filter (fun e => e.isDirectory)"),
        "refinement": "dropping the recursion-predicate conjunct descends into every "
                      "directory child, including the ones the predicate excludes (the "
                      "conventionally skipped and virtual-environment directories). The "
                      "unchanged tests that pin those exclusions would fail, so it does "
                      "NOT resolve.",
        "rationale": "REJECT from `out = descendableSeq entries` (membership): at a "
                     "directory child the predicate rejects (`isDirectory = true`, "
                     "`shouldRecurse = false`) the desired filter skips it and the rival "
                     "keeps it. If it verified => SPEC-TOO-WEAK (the predicate conjunct "
                     "unconstrained). Refuted at the witness that moves `shouldRecurse` "
                     "to false.",
        "witness": _refuted_at([_child(True, True, False)]),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the ORDER half of the post-image, which no membership rival
        # touches: keep EXACTLY the right children, but hand them back in
        # reverse encounter order. A rival the sibling's per-index post-image
        # could not express, and the reason the post-image is a list equality
        # rather than a set/membership claim.
        "module": _rival(
            "    return (entries.filter (fun e => e.isDirectory && e.shouldRecurse)).reverse"),
        "refinement": "a counterpart that walked the selected children in reverse "
                      "encounter order keeps the right set but emits the deeper levels in "
                      "the wrong sequence. Collection order is observable and pinned by "
                      "the unchanged ordering test over a level's subdirectories, which "
                      "would fail, so it does NOT resolve.",
        "rationale": "REJECT from `out = descendableSeq entries` (ORDER): membership is "
                     "exactly right, so this rival is invisible to every membership "
                     "witness above — it is caught only because the post-image is a list "
                     "EQUALITY. Refuted at a two-child list whose children are both "
                     "descendable but distinguishable, where the desired order and the "
                     "reversal differ. If it verified => SPEC-TOO-WEAK on ordering (the "
                     "clause would only pin the selected set).",
        "witness": _refuted_at([_child(True, True, True), _child(True, False, True)]),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-partial-domain-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: correct on every child except the first, which is
        # sliced off before filtering. Pins all-but-one of the domain; the
        # post-image covers the first child too.
        "module": _rival(
            "    return (entries.drop 1).filter (fun e => e.isDirectory && e.shouldRecurse)"),
        "refinement": "a counterpart that special-cased the first child — skipping it "
                      "before applying the guard — would omit a selected directory that "
                      "happens to be encountered first, mis-collecting on any level whose "
                      "first child is descendable. It does NOT resolve in general.",
        "rationale": "REJECT from `out = descendableSeq entries`: when the first child is "
                     "descendable the desired filter keeps it and the rival drops it. A "
                     "partial-domain rival that pins all-but-the-first child must reject "
                     "(else SPEC-TOO-WEAK on the first-child sub-domain). Refuted at a "
                     "two-child list whose FIRST child is descendable and whose second is "
                     "not — distinct from the order rival's point (there both children are "
                     "descendable, so a slice would be invisible and a reversal visible; "
                     "here the reverse).",
        "witness": _refuted_at([_child(True, True, True), _child(False, False, False)]),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-constant-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The trivial too-weak baseline: descend into nothing. Meets the
        # post-image only when no child is descendable. A cheap supporting
        # near-miss, with a genuine refinement.
        "module": _rival("    return []"),
        "refinement": "never descending is what a counterpart that never recursed would "
                      "do: it descends into no subdirectory at any level, collecting "
                      "nothing past the top — essentially every collection test, including "
                      "the failing scenario, would fail. It does NOT resolve.",
        "rationale": "REJECT from `out = descendableSeq entries`: on any list with a "
                     "descendable child the desired filter is non-empty and the rival is "
                     "empty. If it verified => SPEC-TOO-WEAK (the clause would pin "
                     "nothing at all). Refuted at a single plainly descendable child.",
        "witness": _refuted_at([_child(True, True, True)]),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-duplicate-kept",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the MULTIPLICITY obligation of the list equality, which no
        # other rival touches: this impl selects exactly the right children AND
        # in exactly the right encounter order, but emits each of them twice.
        # `reject-order-reversed` pins the SEQUENCE of the kept children and the
        # membership rivals pin WHICH children are kept; a list equality also
        # pins HOW MANY TIMES each appears, and a set-plus-order reading of the
        # clause would admit this rival. Added by audit: the shipped six leave
        # this third reading of the same clause unprobed.
        "module": _rival(
            "    return entries.filter (fun e => e.isDirectory && e.shouldRecurse)\n"
            "             ++ entries.filter (fun e => e.isDirectory && e.shouldRecurse)"),
        "refinement": "a counterpart that descended into each selected child twice would "
                      "walk every subdirectory of a level a second time, yielding each "
                      "item beneath it twice. The unchanged collection behaviour admits "
                      "no duplicated outcomes and the ordering test over a level's "
                      "subdirectories pins the sequence, so both would fail; and the "
                      "failing scenario would report the symlinked directory's test twice "
                      "rather than once. It does NOT resolve.",
        "rationale": "REJECT from `out = descendableSeq entries` (MULTIPLICITY): the kept "
                     "SET is exactly right and so is the relative ORDER, so this rival is "
                     "invisible to every membership witness AND to the order witness — it "
                     "is caught only because the post-image is a list EQUALITY, which "
                     "pins each child's number of occurrences too. If it verified => "
                     "SPEC-TOO-WEAK on multiplicity (the clause would only pin the "
                     "selected set and its order). Refuted at a two-child level whose "
                     "first child is skipped with the inert `isDirectoryNoFollow` TRUE "
                     "and whose second is the link-to-directory child — a point no other "
                     "rival is refuted at.",
        "witness": _refuted_at([_child(False, True, False), _child(True, False, True)]),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Sibling -> velvet accounting.
#
# The sibling battery has 8 SPEC cases (3 soundness positives, 5 uniqueness
# rivals) plus an empty AXIOM_TESTS, over ONE contracted function on a pure
# sequence carrier. This bundle contracts a SINGLE method `descendableEntries`
# over `List DirChild` — the same purely-functional per-level selection — so the
# carrier narrows barely at all and the port is near-parity, plus one case the
# sibling's carrier could not express.
#
#   sibling case                  -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-operand-swap              -> pos-operand-swap               PORTED
#   pos-unfold-resolves           -> pos-inline-descend             RE-EXPRESSED
#   pos-local-isdir               -> pos-local-isdir                PORTED
#   (none)                        -> pos-loopfree-filter             ADDED
#   (none)                        -> pos-partition-fst               ADDED
#   (none)               -> admiss-postimage-satisfiable             ADDED
#   reject-nofollow-prepatch      -> reject-nofollow-prepatch        PORTED
#   reject-overbroad-code3        -> reject-overbroad-nondir        RE-EXPRESSED
#   reject-drop-predicate         -> reject-drop-predicate           PORTED
#   reject-partial-domain-first   -> reject-partial-domain-first     PORTED
#   reject-constant-false         -> reject-constant-empty           PORTED
#   (none)                        -> reject-order-reversed            ADDED
#   (none)                        -> reject-duplicate-kept            ADDED
#   (frame-mutation)              -> (none)                         VACUOUS
#   (divergence)                  -> (none)                       SPEC-CLOSED
#   AXIOM_TESTS = []              -> AXIOM_TESTS = []               DROPPED
#
# RE-EXPRESSED (pos-unfold-resolves): the sibling unfolds its directory
#   classification to an integer-code disjunction. On this carrier the
#   observation is already a `Bool`, with no code to unfold; the equivalent
#   "different surface syntax of the same value" reshape is to write the guard
#   as the named `descend e`. Same intent.
# RE-EXPRESSED (reject-overbroad-code3): the sibling's over-broad rival promotes
#   a third integer code to "directory". This carrier has no integer code; the
#   faithful over-broad analog drops the directory observation from the guard, so
#   a non-directory child the predicate accepts is descended into. Same
#   divergence class (over-descend).
# ADDED (pos-loopfree-filter / reject-order-reversed): see CARRIER NOTE for the
#   first (it is the shared `witness_reference` AND a loop-shape positive). The
#   second attacks the ORDER half of the list-equality post-image — an
#   obligation this carrier has and the sibling's per-index post-image pinned
#   only implicitly, so it had no rival there.
# ADDED (pos-partition-fst): a THIRD loop-shape for the frozen guard, reproven by
#   induction. The two other loop-shape positives are the frozen backward fold
#   and a one-step filter; a two-way split that computes the rejected component
#   as well is neither a syntactic reduct of the frozen return nor of the filter,
#   so it widens the SPEC-TOO-STRONG probe past "reducts of what gold wrote".
# ADDED (admiss-postimage-satisfiable): the ADMISSIBILITY lane, which the port
#   omitted with no recorded reason. It is NOT vacuous merely because the frozen
#   obligation has no `require`: on a total carrier the analogue of a
#   contradictory precondition is a post-image that is UNSATISFIABLE at an
#   input the defended behaviour turns on, which no uniqueness case (they all
#   compare a rival against the clause) and no soundness case (they all reshape
#   an impl that already satisfies it) can detect. The case evaluates the
#   post-image at the discriminating link-to-directory child, at a skipped
#   non-directory child, and at a two-child level pinning encounter order, then
#   `clear`s those facts and closes the frozen obligation verbatim, so it fails
#   iff one of the three is unreachable.
# VACUOUS (frame-mutation): the sibling already records this as N/A — its inputs
#   carry no heap permission, so there is nothing to overwrite. Here it is
#   structural: an immutable `List DirChild`, no `mut` parameter, no heap, no
#   aliasing. No substitute is fabricated.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# BINDER / CLAUSE COVERAGE. One input binder (`entries`); one top-level
#   post-image clause `out = descendableSeq entries` carrying THREE independent
#   obligations (membership, order, multiplicity), ALL attacked. Element
#   observations: `isDirectory` and `shouldRecurse` are load-bearing,
#   `isDirectoryNoFollow` is inert in the post-image (which is exactly why a
#   rival can route the guard through it). The seven reject witnesses sit at
#   seven DISTINCT input points:
#     nofollow-prepatch   [(T,F,T)]           isDirectory != isDirectoryNoFollow
#     overbroad-nondir    [(F,F,T)]           isDirectory = false
#     drop-predicate      [(T,T,F)]           shouldRecurse = false
#     order-reversed      [(T,T,T),(T,F,T)]   length 2, both descendable
#     partial-first       [(T,T,T),(F,F,F)]   length 2, only first descendable
#     constant-empty      [(T,T,T)]           the plain descendable child
#     duplicate-kept      [(F,T,F),(T,F,T)]   length 2, only SECOND descendable
#   Every field moves across both booleans; the list length moves across 1 and 2;
#   and no two rivals are refuted at the same point. The three readings of the
#   single clause are separated by construction: a rival correct on membership
#   AND order is still caught (duplicate-kept), and a rival correct on membership
#   AND multiplicity is still caught (order-reversed), so no two of the three
#   obligations are tested only jointly.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (skipped for this bundle,
#   which consumes no `axiom` and declares no opaque callee), and this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
