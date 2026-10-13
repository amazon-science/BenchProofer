"""properties.py — G-PBT falsification battery for pytest-dev__pytest-6197 (lean).

NOT a Lean file; a manifest of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant sharing the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and the single ``theorem correct_packageCollect`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect="reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` holds of the rival while FAILING
on the frozen solution).

PORT NOTE. This PORTS the nagini falsification battery (``../nagini/properties.py``)
onto this backend's carrier. The two carriers differ substantially, and the
translation — not the case count — is the work.

The nagini bundle models a two-phase MUTABLE state machine: a container carrying
``loaded``/``load_count`` fields, threaded through two separate contracted
procedures (an access phase that performs at most one lazy load, and a discovery
phase that must perform none), with the guarantees stated as before/after
relations on the mutated fields. This Lean bundle models the SINGLE purely
functional core of the same behavior: one total function from the observable
inputs (whether the package's own initialization file matches the configured
pattern, that file's collector, and the enumerated directory entries) to the pair
(produced collector sequence, did-enumeration-import-the-own-init-file).

So nagini's TWO obligations collapse to ONE here, and nagini's *state-transition*
clauses become *value* clauses. Concretely: nagini's discovery-phase pair
(``load_count == Old(load_count)`` ∧ ``loaded == Old(loaded)``) — "enumerating
performs no load and changes no status" — is exactly this bundle's
``result.2 = false`` clause, since a referentially transparent carrier records the
side effect as a returned observation rather than as a field it declines to
mutate. Nagini's access-phase clauses (loaded ends true; exactly one load when
fresh, none when already loaded) have NO counterpart here: this bundle does not
model the access phase at all, only enumeration. Their omission is carrier
narrowing — the modeled surface is narrower than nagini's, not weaker on what it
models — and it is itemised per nagini case in the ADVERSARIAL READ section
below rather than in any external document. (An earlier draft of this note
pointed at an ``assessment`` field; no such field exists in this bundle's
``meta.json``, so the pointer is removed rather than left dangling.)

DEFENDED SURFACE (one modeled behavior, two independent top-level clauses over
three input binders).

  * ``result.2 = false`` — the LOAD-BEARING clause. Enumerating a package's
    contents is a directory-structure operation and must NOT import the package's
    own initialization file as a side effect. This is the behavior the F2P tests
    observe, and the clause the pre-patch skeleton violates on every input.
  * ``result.1 = (if initMatches then [initNode] else []) ++ walkEntries entries``
    — the produced sequence is pinned to one grounded computation over the
    inputs: the own-initialization-file collector FIRST when (and only when) that
    file matches the configured pattern, then, in enumeration order, the child
    collectors of every non-boundary regular file, and nothing from a boundary
    path or a non-file path.

The second clause is not decoration. It is the frame guarantee in the sense of
the spec guide: without it an implementation could report the correct absence of
the import side effect while producing an arbitrary collector sequence — the
analogue of leaving an output component unconstrained. It decomposes into
independently attackable sub-behaviors (the conditional own-init prefix, its
ORDER relative to the walk, the boundary skip, the regular-file guard, and the
per-entry concatenation order), and the rivals below attack each.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's frame rival
    (write into the container during discovery) exploits fractional permissions
    over a mutable heap. Lean is referentially transparent: an input carries no
    permission, there is no read-only half-permission to overwrite and no
    aliasing to exploit, so that rival has no expressible instance. Note this is
    a claim about the PERMISSION mechanism only — the nagini case's *value*
    content (discovery must not perform a load) is NOT vacuous and is ported in
    full as ``u1``/``u2`` below. No substitute is fabricated for the permission
    half.

  * DIVERGENCE / NON-TERMINATION — nothing to ship, and the reason matters.
    The nagini sibling carries ``enum-diverge-loop``: a discovery body that never
    returns satisfies every partial-correctness ``ensures`` vacuously, and nagini
    needs an explicit termination obligation to reject it.

    AUDIT CORRECTION. The claim originally recorded here — "a diverging
    implementation cannot be WRITTEN at all, so the rival is unexpressible" — is
    FALSE and was measured false. A non-terminating implementation IS writable on
    this carrier as ``partial def implementation_packageCollect ... :=
    implementation_packageCollect ...``, and that variant is admissible scope
    (``variant_problems`` returns ``[]``). What actually happens is better for the
    artifact than the false claim was: the rival does NOT verify, because
    ``partial def`` is compiled to an opaque constant, so the frozen script's
    ``unfold implementation_packageCollect`` fails (measured, exit 1: ``Tactic
    `unfold` failed to unfold `implementation_packageCollect```). So the class is
    correctly absent from the reject lane — but as an UNLANDABLE case, not an
    unexpressible one: the same opacity that stops it verifying also stops any
    witness discriminating it, since a witness must ``unfold`` the impl to decide
    anything and hits the identical error (measured, rival-side exit 1). A reject
    case here would land as ``witness-unproven``, an inconclusive outcome, so it
    is deliberately not carried.

    Not the known partial-semantics spec hole either: on velvet under
    ``set_option loom.semantics.termination "partial"`` such a rival VERIFIES
    vacuously while its faithful patch hangs the F2P run, which is recorded in
    ``the corpus-wide termination-semantics finding``. Here it does not verify, so there is nothing
    to ship on this class from this backend; the dispositions coincide and the
    reasons do not.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is fully GROUNDED:
    ``result`` is pinned to a term built only from the inputs, and the bundle
    declares no ``opaque`` callee and consumes no ``axiom``. There is no answer
    key an implementation could echo, and equally no opaque term blocking
    refutation — so every witness below states the spec predicate at CONCRETE
    literal inputs and closes by evaluation. No witness needs to condition on the
    carrier, hence none binds a hypothesis and none can be
    ``witness-inconsistent``.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the battery.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. Each was built against its rival (must elaborate)
and against the frozen solution (must fail), and each was SEEN to discriminate
before shipping.

BINDER / POINT SPREAD. The nine reject witnesses probe nine DISTINCT inputs, and
each of the three binders is moved rather than held at one convenient value:

  * ``initMatches`` takes both settings — ``true`` in u1/u4/u8/u9, ``false`` in
    u2/u3/u5/u6/u7. This matters specifically because the two clauses interact:
    a rival that mishandles the own-init prefix is invisible at whichever setting
    masks it, so u3 (unconditional prefix) is refuted at ``false`` and u4
    (dropped prefix) at ``true``.
  * ``initNode`` takes distinct values (7, 5, 8, 9, 4) at the points where it is
    observable, and the entry payloads are chosen disjoint from it so a rival
    confusing the prefix with a walk contribution cannot coincide by accident.
  * ``entries`` ranges over the empty list, a boundary entry, a non-boundary
    regular file, a non-boundary NON-file, and a two-element list whose two
    payloads differ (the only shape in which a concatenation-order defect is
    observable at all).

The own-init prefix is attacked along all THREE of its independent dimensions,
which is what keeps a near-miss from slipping between the rivals: presence at the
wrong setting (u3 emits it when the pattern does not match, u4 omits it when it
does), POSITION relative to the walk (u8 emits it last), and MULTIPLICITY (u9
emits it twice). u9 was added by audit: every other prefix rival emits at most one
copy, so before it a rival producing the right element in the right place one time
too many was admitted by every witness point in the battery.

No two rivals share a witness. u1 and u2 both attack ``result.2`` but are refuted
at different points on purpose: u1 is wrong on every input, whereas u2 agrees with
the spec whenever enumeration visits nothing, so it is refuted at a NON-empty
enumeration — the sub-domain where it actually differs — rather than at u1's
point, which would not distinguish it from the constant rival.

POSITIVES: DEFEQ DISCIPLINE. A positive that is definitionally the frozen impl
verifies honestly and tests nothing, so each of the three is required to be a
distinct TERM and not merely a distinct spelling. Checked with the real verifier
by asking whether ``rfl`` closes ``@implFrozen = @implVariant``: it FAILS for all
three shipped positives (the conditional accumulator seed, the folded import
observation, and the combined walk guard), which is the machine-checked statement
that none of them zeta/iota-reduces to the frozen term. One earlier positive did
NOT survive that check and was replaced; see ``pos-import-flag-folded``.

PER-NAGINI-CASE LEDGER (added by audit; the port carried no explicit one, so
which of the nine source cases survived was not recoverable from the artifact):

  * ``admiss-fresh-container``   -> ported as ``admiss-ground-enumeration``.
  * ``pos-access-reshape``       -> re-aimed as ``pos-init-as-accumulator-seed``.
  * ``pos-enum-readonly``        -> re-aimed as ``pos-import-flag-folded``
                                    (originally ``pos-import-flag-inlined``,
                                    replaced by audit: that variant was
                                    definitionally the frozen impl).
  * ``enum-frame-write``         -> value content ported as ``u1``; the
                                    PERMISSION half is inexpressible (no heap,
                                    no fractional permission on this carrier).
  * ``enum-status-flip``         -> ported as ``u5`` (the subtler "touches what
                                    it must not" defect, re-aimed at the walk's
                                    boundary skip, which is this bundle's
                                    analogue of the second frame clause).
  * ``access-partial-fresh-noop``-> ported as ``u4``.
  * ``access-double-load``       -> ported as ``u3``.
  * ``access-plus-two``          -> WAS DROPPED, and the drop was not recorded.
                                    Restored by audit as ``u9``: the off-by-one
                                    over-count is expressible here as prefix
                                    MULTIPLICITY, and it was the one dimension
                                    of the own-init prefix no witness probed.
  * ``enum-diverge-loop``        -> not carried, as an UNLANDABLE case rather
                                    than an unexpressible one; see the
                                    DIVERGENCE entry above for the measured
                                    reason (the original "cannot be written"
                                    claim was false).

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (per-file resolution and the boundary observation enter as plain input
data, per ``refinement.md`` — every row is a type refinement). The nagini
``AXIOM_TESTS`` was empty for the same reason and is dropped; the axiom lane
belongs to G-AX, which this gate ignores.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-6197"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl region (the proof anchor
# inside the proof region) and is unique in Solution.lean — both asserted by
# _swap at import, so the manifest breaks loudly if the frozen solution drifts.
# ---------------------------------------------------------------------------

# The import-side-effect observation (impl region).
_I_FLAG = "  let importsOwnInit := false\n"

# The accumulator seed + the conditional own-init prefix (impl region).
_I_INIT = (
    "  let mut collected : List α := []\n"
    "  if initMatches then\n"
    "    collected := collected ++ [initNode]\n"
)

# The boundary skip of the walk (impl region).
_I_BOUNDARY = (
    "    if e.boundary then\n"
    "      -- the path is on this package's enumeration boundary: contribute nothing\n"
    "      continue\n"
)

# The regular-file contribution of the walk (impl region).
_I_ISFILE = (
    "    if e.isFile then\n"
    "      collected := collected ++ e.yields\n"
)

# The return of the two modeled outputs (impl region).
_I_RETURN = "  return (collected, importsOwnInit)\n"

# The frozen proof body (proof region).
_P_FROZEN = (
    "  unfold problem_spec_packageCollect implementation_packageCollect\n"
    "  simp only [Id.run, bind, pure]\n"
    "  have hh := packageCollect_forIn entries\n"
    "  simp only [Id.run] at hh\n"
    "  refine ⟨?_, ?_⟩\n"
    "  · split <;> rfl\n"
    "  · split <;> simp [hh]\n"
)

# The frozen proof region in full (helper lemma + obligation), for the one
# positive whose reshaped loop needs the helper restated in the new form. The
# lemma keeps its frozen NAME (no new theorem/lemma is declared) and the
# obligation statement stays byte-identical; only the two tactic bodies move.
_P_REGION_FROZEN = (
    "/-- The cleaned `forIn` loop accumulating child collectors equals the prefix\n"
    "`init` followed by `walkEntries`, generalized over the accumulator. -/\n"
    "private theorem packageCollect_forIn {α : Type}\n"
    "    (entries : List (PkgEntry α)) (init : List α) :\n"
    "    Id.run (forIn entries init (fun e r =>\n"
    "        if e.boundary = true then ForInStep.yield r\n"
    "        else if e.isFile = true then ForInStep.yield (r ++ e.yields)\n"
    "        else ForInStep.yield r))\n"
    "      = init ++ walkEntries entries := by\n"
)


SPEC_TESTS = [

    # =======================================================================
    # SOUNDNESS POSITIVES (expect verify) — structurally DIFFERENT but CORRECT
    # implementations that must satisfy the frozen obligation. If a faithful
    # correct implementation cannot, the spec is SPEC-TOO-STRONG. Each keeps the
    # theorem statement byte-identical and re-proves honestly inside the proof
    # region: no helper lemma is added, no axiom, no assumption token, no
    # weakened obligation.
    #
    # Each is additionally required to be a distinct TERM, not just a distinct
    # spelling: `rfl` must NOT close `@implFrozen = @implVariant`. A positive that
    # is definitionally the frozen impl verifies for no reason connected to the
    # spec. All three below fail that probe (i.e. are genuine reshapes).
    #
    # These port nagini's two positive controls (pos-access-reshape,
    # pos-enum-readonly). Nagini's pair attacked its two separate procedures;
    # since both collapse onto the single modeled function here, the pair is
    # re-aimed at the two independent clauses of THIS obligation instead: one
    # reshapes the sequence-producing clause, one reshapes the import-observation
    # clause. p4 adds a third at the walk itself, which is where nagini's
    # discovery-phase positive was pointed.
    # =======================================================================
    {
        "id": "pos-init-as-accumulator-seed",
        "kind": "soundness",
        "expect": "verify",
        # Seed the accumulator with the conditional own-init prefix instead of
        # starting empty and appending it. Same sequence on every input; the
        # control flow is reshaped (a conditional initializer in place of a
        # guarded append).
        "module": _swap(
            _swap(
                _BASE, _I_INIT,
                "  -- structurally-different correct impl: seed the accumulator with\n"
                "  -- the conditional own-initialization-file prefix rather than\n"
                "  -- starting empty and appending it under a guard.\n"
                "  let mut collected : List α := if initMatches then [initNode] else []\n",
            ),
            _P_FROZEN,
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  have hh := packageCollect_forIn entries\n"
            "  simp only [Id.run] at hh\n"
            "  refine ⟨trivial, ?_⟩\n"
            "  split <;> simp [hh]\n",
        ),
        "rationale": "defends the sequence clause. The prefix is produced by a "
                     "conditional accumulator seed instead of a guarded append; "
                     "the produced sequence is identical on every input, so "
                     "`result.1 = (if initMatches then [initNode] else []) ++ "
                     "walkEntries entries` still holds, and the import "
                     "observation is untouched. Must verify, else the sequence "
                     "clause is SPEC-TOO-STRONG (it would be pinning the "
                     "accumulation SHAPE rather than the sequence). Proof: the "
                     "seeded form discharges the first conjunct outright "
                     "(`trivial`) and the walk conjunct closes from the frozen "
                     "helper lemma exactly as before — no new declaration, "
                     "statement byte-identical.",
    },
    {
        "id": "pos-import-flag-folded",
        "kind": "soundness",
        "expect": "verify",
        # Compute the import observation by FOLDING over the enumerated paths —
        # none of them imports the package's own initialization file — instead of
        # writing the absent observation as a literal. Same pair on every input,
        # but the value now has to be REDUCED from the input rather than read off,
        # so the first conjunct is no longer closed by `rfl`.
        #
        # AUDIT NOTE (why this replaced `pos-import-flag-inlined`). The case
        # originally here dropped the named local and wrote `false` at the return
        # instead. That is not a reshape: `let x := false ... return (c, x)` and
        # `return (c, false)` are DEFINITIONALLY EQUAL after zeta-reduction, so
        # the variant was the frozen implementation under a different spelling and
        # verified for that reason rather than for any property of the spec.
        # Measured with the real verifier: `example : @implFrozen = @implInlined
        # := rfl` ELABORATES (exit 0), which is the machine-checked statement that
        # the two impls are the same term. The same probe against the impl below
        # FAILS (exit 1, `Type mismatch ... @implFrozen = @implFolded`), so this
        # one is a genuinely distinct implementation of the clause.
        "module": _swap(
            _swap(
                _BASE, _I_FLAG,
                "  -- structurally-different correct impl: the absent import side\n"
                "  -- effect is DERIVED from the enumerated paths (no visited path\n"
                "  -- imports the package's own initialization file) rather than\n"
                "  -- written down as a literal.\n"
                "  let importsOwnInit := entries.any (fun _ => false)\n",
            ),
            "  · split <;> rfl\n",
            "  · split <;> simp\n",
        ),
        "rationale": "defends the LOAD-BEARING import-observation clause. The "
                     "observation is COMPUTED over the enumerated paths — every "
                     "visited path contributes no import — rather than written as "
                     "a literal; the returned pair is identical on every input, so "
                     "`result.2 = false` still holds. Must verify, else that "
                     "clause is SPEC-TOO-STRONG in the direction that matters: it "
                     "would be pinning the SYNTAX of the observation rather than "
                     "its value. Proof: the first conjunct no longer closes by "
                     "`rfl` (the fold must be reduced first) so that one tactic "
                     "moves to `simp`; the walk conjunct is closed by the frozen "
                     "script unchanged, from the frozen helper lemma. No new "
                     "declaration, statement byte-identical.",
    },
    {
        "id": "pos-single-combined-guard",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the walk's two sequential guards (skip a boundary path; then
        # contribute if it is a regular file) into one combined condition. Same
        # contribution per entry, so the same sequence — but the loop body is a
        # genuinely different shape, which is why the helper lemma must be
        # restated in that shape and re-proved.
        "module": _swap(
            _swap(
                _swap(_BASE, _I_BOUNDARY, ""),
                _I_ISFILE,
                "    -- structurally-different correct impl: one combined guard in\n"
                "    -- place of the boundary skip followed by the regular-file test.\n"
                "    if !e.boundary && e.isFile then\n"
                "      collected := collected ++ e.yields\n",
            ),
            _P_REGION_FROZEN,
            "/-- The cleaned `forIn` loop accumulating child collectors equals the prefix\n"
            "`init` followed by `walkEntries`, generalized over the accumulator. -/\n"
            "private theorem packageCollect_forIn {α : Type}\n"
            "    (entries : List (PkgEntry α)) (init : List α) :\n"
            "    Id.run (forIn entries init (fun e r =>\n"
            "        if e.boundary = false ∧ e.isFile = true then ForInStep.yield (r ++ e.yields)\n"
            "        else ForInStep.yield r))\n"
            "      = init ++ walkEntries entries := by\n",
        ),
        "rationale": "defends the walk sub-behavior of the sequence clause with a "
                     "reshape of the LOOP itself: the boundary skip and the "
                     "regular-file test become one combined guard. Every entry "
                     "contributes exactly what it did (a boundary path and a "
                     "non-file path both contribute nothing), so the sequence is "
                     "unchanged and `result` is identical on every input. Must "
                     "verify, else the spec is pinning the walk's branch "
                     "STRUCTURE rather than its contribution — SPEC-TOO-STRONG. "
                     "Proof: the frozen helper lemma is restated in the reshaped "
                     "loop's form under its OWN name (no new declaration) and "
                     "re-proved by the same induction; the obligation statement "
                     "is byte-identical and its tactic body unchanged. This is "
                     "the port of nagini's discovery-phase positive control, "
                     "which likewise reshaped the discovery body while "
                     "contributing nothing.",
    },

    # =======================================================================
    # ADMISSIBILITY (expect verify) — the frozen obligation carries NO
    # precondition hypothesis (the modeled behavior is total, so the `∀` is
    # unguarded), so nagini's precondition-admission probe has no binder to
    # attack here. The honest analogue: show the obligation is SATISFIABLE at a
    # concrete F2P-shaped input by evaluation, not merely closable in the
    # abstract — a spec that no ground instance can discharge would be
    # unsatisfiable at exactly the input the F2P exercises. Ports nagini's
    # admiss-fresh-container.
    # =======================================================================
    {
        "id": "admiss-ground-enumeration",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the spec predicate at a ground F2P-shaped enumeration (an
        # own-initialization file that does NOT match the configured pattern, one
        # boundary path contributing nothing, one regular file contributing a
        # child) by evaluation, then close the frozen obligation verbatim.
        # Nothing is assumed: no new declaration, statement byte-identical, the
        # ground instance is a `have` inside the existing tactic body.
        "module": _swap(
            _BASE, _P_FROZEN,
            "  have _ground : problem_spec_packageCollect false 0\n"
            "      [{ boundary := true, isFile := true, yields := [] },\n"
            "       { boundary := false, isFile := true, yields := [1] }]\n"
            "      (implementation_packageCollect false 0\n"
            "        [{ boundary := true, isFile := true, yields := [] },\n"
            "         { boundary := false, isFile := true, yields := [1] }]) := by\n"
            "    unfold problem_spec_packageCollect implementation_packageCollect\n"
            "    simp only [Id.run, bind, pure]\n"
            "    decide\n"
            + _P_FROZEN,
        ),
        "rationale": "the obligation is discharged BY EVALUATION at a ground "
                     "F2P-shaped enumeration — a package whose own "
                     "initialization file does not match the configured pattern, "
                     "one boundary path, one contributing regular file — and "
                     "then the frozen obligation is closed verbatim. Verifies, "
                     "else the modeled behavior is unsatisfiable at exactly the "
                     "input shape the F2P tests exercise (the analogue of "
                     "PRECOND-TOO-STRONG for an unguarded obligation). Nothing "
                     "is assumed: no new declaration, no assumption token, the "
                     "theorem statement is byte-identical.",
    },

    # =======================================================================
    # UNIQUENESS RIVALS (expect reject) — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # VERIFYING rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input, seen to hold of the rival and to fail on the frozen
    # solution.
    # =======================================================================

    # ---- the LOAD-BEARING clause: enumeration imports the own init file ----
    # This is the port of nagini's enum-frame-write (its value content: the
    # discovery phase performs a load). On nagini that was a WRITE into the
    # container during discovery; here the same defect is the returned
    # observation, because the carrier records the side effect as a value.
    {
        "id": "u1-imports-own-init",
        "kind": "uniqueness",
        "expect": "reject",
        # ADVERSARIAL: report that enumerating the package DID import the
        # package's own initialization file. This is the pre-patch behavior.
        "module": _swap(_BASE, _I_FLAG, "  let importsOwnInit := true\n"),
        "refinement": "this is the pre-patch behavior itself: enumerating a "
                      "package's contents imports the package's own "
                      "initialization file before examining any path. Its "
                      "faithful real patch keeps that eager import, so the F2P "
                      "scenario in which a package's initialization file fails "
                      "at import time errors during enumeration instead of "
                      "completing cleanly, and the run does not exit OK. The "
                      "companion F2P (a package directory that must remain "
                      "non-importable) fails the same way. It does NOT resolve — "
                      "`Solution_prepatch.lean` is this exact skeleton.",
        "rationale": "REJECT from the load-bearing clause `result.2 = false`: the "
                     "spec pins the import observation to absent "
                     "unconditionally, and this rival reports it present on "
                     "EVERY input. Refuted at the minimal point (nothing "
                     "enumerated, own-init file matching) precisely because the "
                     "defect is input-independent — the empty enumeration is the "
                     "smallest input that exhibits it, and stating it there is "
                     "what distinguishes this constant rival from u2, which is "
                     "wrong only on non-empty enumerations.",
        "witness": (
            "-- Refuted at the minimal input: the own-initialization file matches\n"
            "-- the configured pattern and nothing is enumerated. The spec pins the\n"
            "-- import observation to absent; the rival reports it present. Fully\n"
            "-- concrete, so plain evaluation decides it.\n"
            "example : ¬ problem_spec_packageCollect true 7 []\n"
            "    (implementation_packageCollect true 7 []) := by\n"
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },

    # ---- the same clause, as a NEAR-MISS that agrees with gold more widely ----
    {
        "id": "u2-imports-when-anything-enumerated",
        "kind": "uniqueness",
        "expect": "reject",
        # ADVERSARIAL (near-miss): report the import as absent only when nothing
        # was enumerated, and as present as soon as any path is visited. Agrees
        # with the spec on the empty enumeration — the sub-domain where u1 is
        # already refuted — so it needs its own, non-empty point.
        "module": _swap(
            _BASE, _I_FLAG,
            "  let importsOwnInit := !entries.isEmpty\n",
        ),
        "refinement": "a faithful real patch that deferred the eager import of "
                      "the package's own initialization file until the first "
                      "path was visited, rather than removing it, would still "
                      "import that file for every package whose directory is "
                      "non-empty — which is every package the F2P scenarios "
                      "build. The failing initialization file is reached and "
                      "raises during enumeration exactly as before, so the run "
                      "does not exit OK. It does NOT resolve; the guard narrows "
                      "the defect's domain without removing it.",
        "rationale": "REJECT from `result.2 = false`: the spec pins the import "
                     "observation to absent for EVERY input, including a "
                     "non-empty enumeration, while this rival reports it "
                     "present there. Given its own witness point (a single "
                     "contributing regular file, own-init file NOT matching) "
                     "rather than sharing u1's, because it agrees with the spec "
                     "at u1's point: refuting it there is impossible, and "
                     "refuting it here is what demonstrates the sub-domain its "
                     "rationale claims. Also the only witness moving `entries` "
                     "from empty to non-empty against this clause.",
        "witness": (
            "-- Refuted where this rival and u1's constant rival differ: a\n"
            "-- non-empty enumeration (one non-boundary regular file). The\n"
            "-- own-initialization file does not match the configured pattern here,\n"
            "-- so the point is distinct from u1's in every binder.\n"
            "example : ¬ problem_spec_packageCollect false 0 "
            "[{ boundary := false, isFile := true, yields := [2] }]\n"
            "    (implementation_packageCollect false 0 "
            "[{ boundary := false, isFile := true, yields := [2] }]) := by\n"
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },

    # ---- the conditional own-init prefix: produced unconditionally ----
    # Ports nagini's access-double-load (act even when the guard says not to) to
    # the clause this bundle actually models.
    {
        "id": "u3-init-collector-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # ADVERSARIAL: always produce the collector for the package's own
        # initialization file, ignoring whether that file matches the configured
        # test-file pattern.
        "module": _swap(
            _BASE, _I_INIT,
            "  -- ADVERSARIAL: produce the own-initialization-file collector\n"
            "  -- unconditionally, ignoring the configured-pattern test.\n"
            "  let mut collected : List α := [initNode]\n",
        ),
        "refinement": "a faithful real patch that dropped the configured-pattern "
                      "test and always produced a collector for the package's "
                      "own initialization file would collect that file as a test "
                      "module in every package, including packages whose "
                      "initialization file the configuration deliberately "
                      "excludes. Collecting it means importing it when the "
                      "collector is realized, so the F2P scenario whose "
                      "initialization file fails at import time fails again — "
                      "one step later in the run, but the run still does not "
                      "exit OK — and the established behavior that only "
                      "pattern-matching files are collected breaks for the P2P "
                      "suite. It does NOT resolve.",
        "rationale": "REJECT from the sequence clause: the spec prefixes "
                     "`[initNode]` only when `initMatches` holds, so at "
                     "`initMatches = false` the spec's sequence is the bare walk "
                     "while the rival's carries the extra leading element. "
                     "Refuted at `initMatches = false` — the sub-domain where "
                     "this rival is wrong and the ONLY setting at which the "
                     "defect is observable at all, since at `true` it agrees "
                     "with gold exactly. The entry payload is chosen distinct "
                     "from `initNode` so the extra element cannot coincide with "
                     "a walk contribution.",
        "witness": (
            "-- Refuted at the setting where the configured-pattern test bites:\n"
            "-- the own-initialization file does NOT match, so the spec's sequence\n"
            "-- is the bare walk while the rival prefixes the own-init collector.\n"
            "-- The entry's payload (6) differs from `initNode` (5) so the spurious\n"
            "-- element cannot be mistaken for a walk contribution.\n"
            "example : ¬ problem_spec_packageCollect false 5 "
            "[{ boundary := false, isFile := true, yields := [6] }]\n"
            "    (implementation_packageCollect false 5 "
            "[{ boundary := false, isFile := true, yields := [6] }]) := by\n"
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },

    # ---- the conditional own-init prefix: never produced ----
    # Ports nagini's access-partial-fresh-noop (never act, even when the guard
    # says to) — the mirror partial-domain miss of u3.
    {
        "id": "u4-init-collector-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # ADVERSARIAL: never produce the collector for the package's own
        # initialization file, even when that file matches the configured pattern.
        "module": _swap(
            _BASE, _I_INIT,
            "  -- ADVERSARIAL: never produce the own-initialization-file\n"
            "  -- collector, even when the configured pattern matches.\n"
            "  let mut collected : List α := []\n",
        ),
        "refinement": "a faithful real patch that never produced a collector for "
                      "the package's own initialization file would SILENTLY DROP "
                      "the tests defined in that file for every package whose "
                      "initialization file the configuration does select. That "
                      "is the deferral-becomes-a-drop failure: the file is not "
                      "imported eagerly (so the eager-collection F2P would pass) "
                      "but it is never collected either, so the established "
                      "behavior that a matching initialization file contributes "
                      "its tests breaks and the P2P collection suite fails. It "
                      "does NOT resolve — and it is the rival most worth "
                      "carrying, because it passes the very test the fix is "
                      "about while breaking the surrounding contract.",
        "rationale": "REJECT from the sequence clause: at `initMatches = true` "
                     "the spec's sequence begins with `initNode` and the rival's "
                     "omits it. Refuted at `initMatches = true` — the mirror "
                     "sub-domain to u3, which is why the two rivals take "
                     "opposite settings of that binder rather than sharing a "
                     "point: each is refuted exactly where it is wrong, and "
                     "between them the binder is demonstrated live at both "
                     "values. The enumeration here is a lone BOUNDARY entry, so "
                     "the walk contributes nothing and the missing prefix is the "
                     "sole difference.",
        "witness": (
            "-- Refuted at the mirror setting to u3: the own-initialization file\n"
            "-- DOES match the configured pattern, so the spec's sequence begins\n"
            "-- with it and the rival's is empty. The lone entry is a boundary path\n"
            "-- (contributes nothing), isolating the missing prefix.\n"
            "example : ¬ problem_spec_packageCollect true 8 "
            "[{ boundary := true, isFile := false, yields := [] }]\n"
            "    (implementation_packageCollect true 8 "
            "[{ boundary := true, isFile := false, yields := [] }]) := by\n"
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },

    # ---- the boundary skip of the walk ----
    # Ports nagini's enum-status-flip: a discovery body that does something
    # subtler than the full eager load but still touches what it must not.
    {
        "id": "u5-boundary-not-skipped",
        "kind": "uniqueness",
        "expect": "reject",
        # ADVERSARIAL: drop the boundary skip, so a path on the package's own
        # enumeration boundary contributes its collectors like any other file.
        "module": _swap(
            _BASE, _I_BOUNDARY,
            "    -- ADVERSARIAL: no boundary skip — a path on this package's own\n"
            "    -- enumeration boundary contributes like any other path.\n",
        ),
        "refinement": "a faithful real patch that dropped the boundary skip "
                      "would collect the package's own initialization file a "
                      "SECOND time as an ordinary visited path, and would also "
                      "re-collect every path already accounted for by a nested "
                      "sub-package. The duplicate collection of the "
                      "initialization file means importing it during "
                      "enumeration by the ordinary file route — so the F2P "
                      "scenario whose initialization file fails at import time "
                      "fails again — and the duplicate child collectors break "
                      "the established collection identities the P2P suite "
                      "asserts. It does NOT resolve.",
        "rationale": "REJECT from the sequence clause via `walkEntries`, which "
                     "pins a boundary path to contribute NOTHING (`if e.boundary "
                     "|| !e.isFile then []`): the rival lets a boundary regular "
                     "file contribute its payload, so the sequence gains an "
                     "element the spec excludes. Refuted at the one entry shape "
                     "that isolates this — boundary AND a regular file with a "
                     "non-empty payload — which no other witness uses, since a "
                     "boundary path with an empty payload (u4's) cannot exhibit "
                     "the defect.",
        "witness": (
            "-- Refuted at the entry shape that isolates the boundary skip: a\n"
            "-- boundary path that IS a regular file and DOES resolve to a child.\n"
            "-- The spec has it contribute nothing; the rival contributes its\n"
            "-- payload. (u4's boundary entry has an empty payload and could not\n"
            "-- exhibit this.)\n"
            "example : ¬ problem_spec_packageCollect false 0 "
            "[{ boundary := true, isFile := true, yields := [3] }]\n"
            "    (implementation_packageCollect false 0 "
            "[{ boundary := true, isFile := true, yields := [3] }]) := by\n"
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },

    # ---- the regular-file guard of the walk ----
    {
        "id": "u6-nonfile-contributes",
        "kind": "uniqueness",
        "expect": "reject",
        # ADVERSARIAL: drop the regular-file test, so a non-boundary path that is
        # NOT a regular file contributes collectors too.
        "module": _swap(
            _BASE, _I_ISFILE,
            "    -- ADVERSARIAL: no regular-file test — a non-boundary path\n"
            "    -- contributes whatever it resolves to even if it is not a file.\n"
            "    collected := collected ++ e.yields\n",
        ),
        "refinement": "a faithful real patch that dropped the regular-file test "
                      "would run the per-file resolution on DIRECTORY paths as "
                      "well. Directories are traversed for their contents, not "
                      "collected as files; resolving one as a file yields "
                      "collectors that do not correspond to any test module, so "
                      "the enumerated sequence acquires spurious entries and the "
                      "established collection results the P2P suite asserts "
                      "break. It does NOT resolve.",
        "rationale": "REJECT from the sequence clause via `walkEntries`, whose "
                     "`|| !e.isFile` arm pins a non-file path to contribute "
                     "NOTHING: the rival contributes its payload. Refuted at a "
                     "non-boundary NON-file entry with a non-empty payload — a "
                     "shape distinct from every other witness, and the "
                     "complementary half of the `walkEntries` guard that u5 "
                     "attacks (u5 moves `boundary`, u6 moves `isFile`), so "
                     "neither sub-condition is left unprobed.",
        "witness": (
            "-- Refuted at the complementary half of the walk guard to u5: a\n"
            "-- non-boundary path that is NOT a regular file yet resolves to a\n"
            "-- child. The spec has it contribute nothing; the rival contributes.\n"
            "example : ¬ problem_spec_packageCollect false 0 "
            "[{ boundary := false, isFile := false, yields := [4] }]\n"
            "    (implementation_packageCollect false 0 "
            "[{ boundary := false, isFile := false, yields := [4] }]) := by\n"
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },

    # ---- the ORDER of the walk's per-entry concatenation ----
    {
        "id": "u7-walk-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # ADVERSARIAL: prepend each contributing entry's collectors instead of
        # appending them, reversing the enumeration order of the produced
        # sequence (and moving the own-init prefix off the front).
        "module": _swap(
            _BASE, _I_ISFILE,
            "    -- ADVERSARIAL: prepend rather than append each contribution,\n"
            "    -- reversing the order in which enumerated paths are reported.\n"
            "    if e.isFile then\n"
            "      collected := e.yields ++ collected\n",
        ),
        "refinement": "a faithful real patch that reported each path's child "
                      "collectors before those of the paths enumerated earlier "
                      "would invert the collection order of a package's "
                      "contents. Collection order is observable: it determines "
                      "reported test order and the node identities the P2P "
                      "collection suite asserts (the ordering tests among them), "
                      "so the established behavior breaks. It does NOT resolve.",
        "rationale": "REJECT from the ORDER of the sequence clause: `walkEntries` "
                     "is front-recursive (`e.yields ++ walkEntries es`), pinning "
                     "each entry's contribution BEFORE those of later entries, "
                     "while the rival emits them after. Requires the only "
                     "two-element enumeration in the battery, with DISTINCT "
                     "payloads — the order defect is invisible at every "
                     "single-entry point the other witnesses use, and invisible "
                     "even at two entries if their payloads coincide. This is "
                     "the only witness that varies the LENGTH of `entries` "
                     "beyond one.",
        "witness": (
            "-- Refuted at the only shape an order defect is observable in: two\n"
            "-- contributing entries with DISTINCT payloads. The spec pins the\n"
            "-- earlier path's child first; the rival reports it last.\n"
            "example : ¬ problem_spec_packageCollect false 0 "
            "[{ boundary := false, isFile := true, yields := [1] }, "
            "{ boundary := false, isFile := true, yields := [2] }]\n"
            "    (implementation_packageCollect false 0 "
            "[{ boundary := false, isFile := true, yields := [1] }, "
            "{ boundary := false, isFile := true, yields := [2] }]) := by\n"
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },

    # ---- the ORDER of the own-init prefix relative to the walk ----
    {
        "id": "u8-init-collector-last",
        "kind": "uniqueness",
        "expect": "reject",
        # ADVERSARIAL: produce the own-initialization-file collector AFTER the
        # walk instead of first. The right elements, the wrong position — the
        # near-miss of u3/u4, which get the position right and the presence wrong.
        "module": _swap(
            _swap(
                _BASE, _I_INIT,
                "  let mut collected : List α := []\n",
            ),
            _I_RETURN,
            "  -- ADVERSARIAL: append the own-initialization-file collector after\n"
            "  -- the walk rather than producing it first.\n"
            "  if initMatches then\n"
            "    collected := collected ++ [initNode]\n"
            "  return (collected, importsOwnInit)\n",
        ),
        "refinement": "a faithful real patch that produced the collector for the "
                      "package's own initialization file after walking the "
                      "directory, rather than before, would report the "
                      "initialization file's tests after those of every other "
                      "path in the package. Collection order is observable in "
                      "reported test order and node identities, so the "
                      "established ordering behavior the P2P collection suite "
                      "asserts breaks. It does NOT resolve.",
        "rationale": "REJECT from the ORDER of the sequence clause: the spec "
                     "fixes the prefix `(if initMatches then [initNode] else []) "
                     "++ walkEntries entries`, so the own-init collector precedes "
                     "every walk contribution; the rival emits it last. This "
                     "rival produces exactly the right MULTISET of collectors, so "
                     "it is refutable only by a witness where the position is "
                     "observable: `initMatches = true` AND a non-empty walk whose "
                     "payload (1) differs from `initNode` (9). No other witness "
                     "has that combination — u4 has the matching prefix but a "
                     "non-contributing walk, and u7 has a contributing walk but "
                     "no prefix — which is why this near-miss gets its own point "
                     "rather than sharing one.",
        "witness": (
            "-- Refuted where the prefix POSITION is observable: the own-init file\n"
            "-- matches (so the prefix exists) and the walk contributes a distinct\n"
            "-- payload (so the two are tellable apart). The spec puts the own-init\n"
            "-- collector first; the rival puts it last.\n"
            "example : ¬ problem_spec_packageCollect true 9 "
            "[{ boundary := false, isFile := true, yields := [1] }]\n"
            "    (implementation_packageCollect true 9 "
            "[{ boundary := false, isFile := true, yields := [1] }]) := by\n"
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },

    # ---- the MULTIPLICITY of the own-init prefix ----
    # ADDED BY AUDIT. This is the port of nagini's ``access-plus-two``: the
    # off-by-one over-count near-miss (act the right number of times, not once
    # too many). The port dropped it without recording it, leaving the
    # multiplicity of the own-init prefix unprobed: u3 attacks its presence at
    # the wrong setting, u4 its absence, u8 its position — but every one of them
    # produces AT MOST one copy, so a rival emitting the right element in the
    # right place TWICE was admitted by every existing witness point.
    {
        "id": "u9-init-collector-duplicated",
        "kind": "uniqueness",
        "expect": "reject",
        # ADVERSARIAL: produce the collector for the package's own initialization
        # file TWICE when that file matches the configured pattern. Right element,
        # right position, one copy too many.
        "module": _swap(
            _BASE, _I_INIT,
            "  -- ADVERSARIAL: produce the own-initialization-file collector TWICE\n"
            "  -- when the configured pattern matches (one collector too many).\n"
            "  let mut collected : List α := []\n"
            "  if initMatches then\n"
            "    collected := collected ++ [initNode, initNode]\n",
        ),
        "refinement": "a faithful real patch that produced a collector for the "
                      "package's own initialization file twice would collect that "
                      "file as two separate test modules. The duplicate is "
                      "realized like any other collector, so the initialization "
                      "file is imported during the run and the F2P scenario whose "
                      "initialization file fails at import time fails again; the "
                      "duplicated collection identities also break the "
                      "established collection results the P2P suite asserts "
                      "(every test in that file would be reported twice). It "
                      "does NOT resolve.",
        "rationale": "REJECT from the sequence clause: the spec prefixes exactly "
                     "`[initNode]` — a ONE-element list — when `initMatches` "
                     "holds, and this rival prefixes two. Refuted at "
                     "`initMatches = true` with a contributing walk whose payload "
                     "(2) differs from `initNode` (4), so the duplicate cannot be "
                     "mistaken for a walk contribution. This is the only witness "
                     "in the battery that moves the MULTIPLICITY of the prefix "
                     "rather than its presence (u3/u4) or its position (u8): each "
                     "of those rivals emits at most one copy, so none of their "
                     "points refutes this one.",
        "witness": (
            "-- Refuted where the prefix MULTIPLICITY is observable: the own-init\n"
            "-- file matches (so the prefix exists) and the walk contributes a\n"
            "-- distinct payload (so the copies are tellable apart from it). The\n"
            "-- spec pins the prefix to exactly one `initNode`; the rival emits two.\n"
            "example : ¬ problem_spec_packageCollect true 4 "
            "[{ boundary := false, isFile := true, yields := [2] }]\n"
            "    (implementation_packageCollect true 4 "
            "[{ boundary := false, isFile := true, yields := [2] }]) := by\n"
            "  unfold problem_spec_packageCollect implementation_packageCollect\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },
]


# The axiom lane is EMPTY here and belongs to G-AX regardless. This bundle
# declares no `opaque` callee and consumes no `axiom`: the per-path resolution to
# child collectors and the boundary observation enter as plain input data (every
# refinement.md row is a type refinement), so there is no axiom domain to fuzz or
# contain at the spec layer. The nagini AXIOM_TESTS was empty for the same
# reason.
AXIOM_TESTS = []
