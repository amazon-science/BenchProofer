"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13496 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct configureEnsemble`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

CARRIER NARROWING — READ THIS FIRST. The nagini sibling models the DOWNSTREAM
fitting decision: three functions (``refit_to_size`` / ``reuse_and_extend`` /
``rebuild_all``) over a ``List[int]`` roster of sub-estimator identities, with a
prefix-preserving reuse postcondition and a size pin. THIS bundle models a
DIFFERENT, upstream surface: the single constructor that assembles the keyword
configuration it forwards to its base ensemble machinery. The reuse-vs-rebuild
roster algorithm lives in UNCHANGED library code (the parent ensemble's fit) and
is NOT re-modeled here (that would be re-modeling unchanged library code as the
fix). The patch is config PLUMBING: it exposes the incremental-fit reuse flag as
a constructor argument and forwards it. So every nagini case attached to the
roster behaviour (the reuse-prefix postcondition, the size pin, the frame-write
on the read-only roster, the partial-domain tail/guard rivals) has NO
counterpart on this carrier — they attack a function this bundle does not model.
What this bundle DOES model, and therefore what the battery covers, is the
forwarding contract. Full nagini→velvet accounting in the footer.

DEFENDED SURFACE (one contracted method):

  configureEnsemble (nEstimators maxSamples maxFeatures : Param)
      (bootstrap : Bool) (nJobs randomState verbose : Param)
      (warmStart : Bool) return (cfg : EnsembleConfig)
    ensures cfg.nEstimators = nEstimators        -- F1 frame
    ensures cfg.maxSamples  = maxSamples          -- F2 frame
    ensures cfg.maxFeatures = maxFeatures         -- F3 frame
    ensures cfg.bootstrap   = bootstrap           -- F4 frame
    ensures cfg.nJobs       = nJobs               -- F5 frame
    ensures cfg.randomState = randomState         -- F6 frame
    ensures cfg.verbose     = verbose             -- F7 frame
    ensures cfg.warmStart   = warmStart           -- C  the newly-forwarded flag

The method assembles ``EnsembleConfig`` — the configuration handed to the base
ensemble machinery — as a total function of its eight arguments, copying each
argument into the corresponding field. ``EnsembleConfig`` derives
``DecidableEq`` and every field is a concrete ``Bool`` or ``Param`` (= ``Int``)
handle: the whole post-image is TRANSPARENT, there is no opaque answer-key term.

WHICH CLAUSE CONSTRAINS THE IMPL, AND WHY EIGHT. Each ``ensures`` pins one field
to its own argument; the eight are independent, and every one is
impl-constraining (a rival that mishandles field X while copying the rest still
violates clause X). C (``cfg.warmStart = warmStart``) is the DISCRIMINATING
clause the fix adds — the newly-forwarded incremental-fit reuse flag — and the
prepatch (which hands the base machinery its inherited default, ignoring the
caller's argument) fails exactly C when the caller requests the flag ON. F1–F7
are the FRAME: the desired behaviour requires that exposing the new flag NOT
disturb any entry already forwarded, so a rival that corrupts a frame field
while forwarding the flag correctly is equally wrong. Every rival targets one
clause; the eleven rivals attack all eight, with C attacked three ways (dropped
to a constant, forced to a constant, and honoured except on a coupled slice) so
that it is pinned at BOTH flag values rather than merely against one constant,
and F1 attacked twice (constant substitution and an off-by-one with no
accidentally-correct point). The eleven reject witnesses drive the eight
arguments to NINE distinct input points (two pairs share a point — the
bootstrap-ON tuple and the nEstimators=1 tuple each refute two different rivals,
which is fine: what must differ is the IMPL each point refutes, not the point),
so no binder is held fixed by every witness, and one point varies two binders
jointly.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery: ``configureEnsembleTester <args> = false`` says the
extracted program's result violates the method's postcondition at that concrete
input, closed by ``decide`` in a file whose ``prove_correct`` block has been
stripped so no tactic script can mask the verdict. This carrier is FULLY
TRANSPARENT — the impl is a finite record assembly, so the extracted program
reduces to ``isTrue``/``isFalse`` under the kernel for every concrete literal
tuple, both against a rival (postcondition violated → tester ``false`` → ``=
false`` elaborates by ``decide``) and against the frozen solution (postcondition
holds → tester ``true`` → ``= false`` fails by ``decide``, the required
FAIL-on-gold half). ``Param`` is ``Int`` and the ``Bool`` fields decide
directly, so small integer / boolean literals are enough; no conditioning on an
opaque term is needed and no witness declares any head binder (so no consistency
probe applies). Both halves of the discrimination were confirmed with
``scripts/lean_verify.sh`` during authoring — every witness elaborates green
against its rival (exit 0) and fails (``decide`` "proved ... is false") against
the frozen solution (exit 1).

ADVERSARIAL READ of the sibling's classes on this carrier (full accounting in
the footer):
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical assembly (fields written in a different textual
    order; the configuration staged through a typed local before return) must
    verify, else the spec is SPEC-TOO-STRONG on the shape of the assembly.
  * ADMISSIBILITY — the method declares no ``require`` clause (the
    pre-conditions region is empty), so the sibling's "a normal input satisfies
    the precondition" probe is vacuous. Re-aimed at the residual total-domain
    risk (the eight-clause post-image is jointly SATISFIABLE by a gold-shaped
    computation) — witnessed by the frozen impl discharging all eight ensures.
  * FRAME-MUTATION — VACUOUS on this backend, DEMONSTRATED not asserted. The
    sibling carries mandatory frame-mutation rivals because its read-only roster
    is held at a fractional heap permission an impl can illegally overwrite.
    Lean/Velvet are referentially transparent: the eight inputs are immutable
    values (none ``mut``), there is no heap, no aliasing, no permission system,
    so there is no read-only input to overwrite. Measured: an impl body that
    attempts ``nEstimators := 0`` (or ``warmStart := true``) before the gold
    return is rejected by the ELABORATOR, not by the spec —
    ``error: `nEstimators` cannot be mutated, only variables declared using
    `let mut` can be mutated`` — so a frame-write rival is not merely
    uninteresting here, it is not a well-formed program. A rejection whose text
    is a parse/elaboration complaint attributes nothing to the postcondition, so
    the class has no carrier analogue; NOT ported (fabricating a substitute
    would test nothing). NOTE the frame is
    still DEFENDED here — but by the value contract (F1–F7 pin every un-touched
    field to its argument), not by a permission system; frame-corruption rivals
    below attack that value contract.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line a single ``return`` over immutable values,
    no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image pins each field to one of the
    method's own arguments (identity forwarding); there is no answer-key term a
    wrong impl could echo. The cheapest correct impl copies each argument
    honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: the prepatch drops the new
    flag (fails C), and each frame rival corrupts exactly one forwarded field
    (constant-substitution or boolean-negation) while forwarding the rest.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13496"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl body (the two comment lines + the record literal),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`.
# ---- A single anchor lying wholly inside the impl region and unique in the
# ---- file (both facts asserted at load). Every reshaped positive swaps on this
# ---- block, so its edit is confined to the impl region and same_spec holds.
_IMPL = (
    "    -- Forward every carried entry verbatim, INCLUDING the incremental-fit reuse\n"
    "    -- flag taken from the caller's argument.\n"
    "    return { nEstimators := nEstimators, maxSamples := maxSamples,\n"
    "             maxFeatures := maxFeatures, bootstrap := bootstrap,\n"
    "             warmStart := warmStart, nJobs := nJobs,\n"
    "             randomState := randomState, verbose := verbose }"
)
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- per-field anchors for the frame/flag rivals. Each substring lies wholly
# ---- inside the impl region and is unique in the file (asserted at load), so a
# ---- swap on it is confined to the impl region and same_spec holds. Corrupting
# ---- exactly ONE field's forwarded value keeps every other clause satisfied, so
# ---- the rejection is attributable to that field's ensures alone.
_FLD = {
    "nEstimators": "return { nEstimators := nEstimators,",
    "maxSamples":  "maxSamples := maxSamples,",
    "maxFeatures": "maxFeatures := maxFeatures,",
    "bootstrap":   "bootstrap := bootstrap,",
    "warmStart":   "warmStart := warmStart,",
    "nJobs":       "nJobs := nJobs,",
    "randomState": "randomState := randomState,",
    "verbose":     "verbose := verbose }",
}
for _k, _v in _FLD.items():
    assert _BASE.count(_v) == 1, f"field anchor drift for {_k}: {_v!r}"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `configureEnsembleTester <args> = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped. Every argument
# ---- is a concrete literal (Param = Int handle, or a Bool), so `decide` reduces
# ---- the extracted program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for configureEnsemble\n"
            "prove_precondition_decidable_for configureEnsemble\n"
            "prove_postcondition_decidable_for configureEnsemble\n"
            "derive_tester_for configureEnsemble\n\n" + body)


def _b(x):
    return "true" if x else "false"


# argument order: nEstimators maxSamples maxFeatures bootstrap
#                 nJobs randomState verbose warmStart
def _witness(nEst, maxS, maxF, boot, nJ, rs, vb, ws):
    return _tester(
        "example : configureEnsembleTester %d %d %d %s %d %d %d %s = false := by\n"
        "  decide\n"
        % (nEst, maxS, maxF, _b(boot), nJ, rs, vb, _b(ws)))


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct assembly cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen assembly form).
    # =====================================================================
    {
        "id": "pos-control-reordered-fields",
        "kind": "soundness",
        "expect": "verify",
        # Assemble the same configuration with the record fields written in a
        # DIFFERENT textual order. A structure value is independent of the order
        # its fields are supplied, so every ensures still holds; a maximally
        # different assembly text.
        "module": _swap(
            _BASE, _IMPL,
            "    -- Assemble the configuration; the fields are supplied in a different\n"
            "    -- textual order (a record value is independent of assignment order).\n"
            "    return { warmStart := warmStart, verbose := verbose,\n"
            "             randomState := randomState, nJobs := nJobs,\n"
            "             bootstrap := bootstrap, maxFeatures := maxFeatures,\n"
            "             maxSamples := maxSamples, nEstimators := nEstimators }"),
        "rationale": (
            "a correct assembly with the record fields in a DIFFERENT textual "
            "order; a structure value does not depend on assignment order, so "
            "every ensures (F1–F7 and C) still discharges and the frozen "
            "`loom_solve` proof closes unchanged. Ports the nagini "
            "pos-dispatch-inverted-guard idea (a structurally-different but "
            "semantically identical impl of the modeled function). If it fails to "
            "verify the spec is over-fit to the frozen assembly form "
            "(SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "pos-control-staged-local",
        "kind": "soundness",
        "expect": "verify",
        # Bind the assembled configuration to a typed local `cfg` first, then
        # return it. Same value flow, a different control shape.
        "module": _swap(
            _BASE, _IMPL,
            "    -- Assemble the configuration into a typed local first, then hand it back.\n"
            "    let cfg : EnsembleConfig :=\n"
            "      { nEstimators := nEstimators, maxSamples := maxSamples,\n"
            "        maxFeatures := maxFeatures, bootstrap := bootstrap,\n"
            "        warmStart := warmStart, nJobs := nJobs,\n"
            "        randomState := randomState, verbose := verbose }\n"
            "    return cfg"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape: stage the configuration "
            "into a typed local `cfg` and return it. The value flow is unchanged so "
            "every clause still discharges and the frozen proof closes as-is. Ports "
            "the nagini pos-reuse-lentest-loop idea (same observable result, "
            "different code shape). If it fails to verify => SPEC-TOO-STRONG "
            "(over-fit to the inline-return form)."
        ),
    },

    {
        "id": "pos-control-value-identities",
        "kind": "soundness",
        "expect": "verify",
        # The two positives above reshape only the SYNTAX around the forwarded
        # terms: each field is still the bare argument name, so the assembled
        # record is DEFINITIONALLY the frozen one and `loom_solve` closes it by
        # reduction alone. That makes them weak SPEC-TOO-STRONG probes — they
        # cannot detect a spec over-fit to the argument-name form. This positive
        # forwards each entry through a value-level IDENTITY instead (`+ 0` on
        # the Int handles, a double negation / idempotent `||` on the booleans),
        # so no field is syntactically its argument and every clause needs an
        # arithmetic/boolean simplification rather than `rfl`. Still forwards
        # exactly the caller's eight values, so it MUST verify.
        "module": _swap(
            _BASE, _IMPL,
            "    -- Assemble the configuration forwarding each entry through a value-level\n"
            "    -- IDENTITY rather than by naming the argument directly: `+ 0` on the\n"
            "    -- handles, double negation / idempotent `||` on the booleans. Every\n"
            "    -- forwarded value is unchanged; no field is syntactically its argument.\n"
            "    return { nEstimators := nEstimators + 0, maxSamples := maxSamples + 0,\n"
            "             maxFeatures := maxFeatures + 0, bootstrap := !(!bootstrap),\n"
            "             warmStart := !(!warmStart), nJobs := nJobs + 0,\n"
            "             randomState := randomState + 0, verbose := 0 + verbose }"),
        "rationale": (
            "a correct impl that is NOT definitionally the frozen assembly: each "
            "entry is forwarded through a value-level identity (`x + 0` on the "
            "`Param`/`Int` handles, `!(!b)` on the booleans), so no field is "
            "syntactically the argument it must equal and each of the eight "
            "clauses requires a simplification step rather than pure reduction. "
            "This is the load-bearing SPEC-TOO-STRONG probe: the other two "
            "positives keep every field as the bare argument name, so they are "
            "defeq to gold and would verify even if the spec were over-fit to "
            "the argument-name form. If THIS fails to verify, the spec (or the "
            "frozen `loom_solve`) is over-fit to the syntactic shape of the "
            "forwarded terms => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require`, so the sibling's
    # admiss-self-call-warmstart (which established the read-only fractional
    # precondition on an F2P-shaped roster) has no counterpart: there is no
    # precondition to satisfy and no permission surface. Re-aimed at the residual
    # total-domain risk — that the eight-clause post-image is jointly SATISFIABLE
    # by a gold-shaped computation. The frozen impl discharging all eight ensures
    # IS that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the constructor is total over every "
            "argument tuple; the gold impl discharging all eight ensures is the "
            "admissibility witness that the post-image (F1–F7 frame plus C, the "
            "newly-forwarded flag) is jointly satisfiable. Near-trivial precisely "
            "because the precondition is empty. Re-aimed from the nagini "
            "admiss-self-call-warmstart, whose read-only-precondition half has no "
            "counterpart on this referentially-transparent carrier. Else "
            "SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. The frozen spec is untouched; each
    # rival keeps the frozen `loom_solve` proof (which, for a wrong impl, simply
    # fails to close — the rejection), and the witness attributes that rejection
    # to the spec. Each rival corrupts exactly ONE forwarded field, so its
    # witness varies exactly the binder that field's clause depends on.
    # =====================================================================
    {
        "id": "rival-drop-warmstart-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG ITSELF: the incremental-fit reuse flag is NOT forwarded; the
        # configuration receives the base machinery's default (reuse OFF),
        # ignoring the caller's argument. This is the prepatch behaviour verbatim
        # and attacks clause C.
        "module": _swap(_BASE, _FLD["warmStart"],
                        "warmStart := false,"),
        "refinement": (
            "this is the pre-change behaviour: the incremental-fit reuse flag is "
            "not among the entries the constructor forwards, so the configuration "
            "always receives the base machinery's inherited default (reuse OFF) "
            "regardless of the caller's argument. Its faithful real patch is the "
            "unpatched constructor, which does not accept or forward the flag, so a "
            "caller requesting the flag ON gets a fresh-built ensemble on every "
            "fit. The failing test requests the flag ON, fits, enlarges the target "
            "count, fits again, and asserts the previously-built members were "
            "reused (kept, not rebuilt); with the flag dropped they are rebuilt, so "
            "it would NOT resolve. This is exactly the defect the fix corrects."
        ),
        "rationale": (
            "REJECT from clause C (`cfg.warmStart = warmStart`): when the caller "
            "supplies the flag ON the spec pins `cfg.warmStart = true`, but this "
            "rival hard-codes `false`. Refuted at the flag-ON input "
            "(`warmStart` true, every frame arg 0/false). If it verified => "
            "SPEC-TOO-WEAK (admits the very bug — the new flag unpinned)."
        ),
        "witness": _witness(0, 0, 0, False, 0, 0, 0, True),
    },
    {
        "id": "rival-force-warmstart-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # DUAL of the bug: the flag is hard-coded ON instead of forwarded, so a
        # caller who did NOT request incremental reuse gets it anyway. Attacks
        # clause C from the opposite side to rival-drop-warmstart-flag, whose
        # witness only ever drives warmStart=true; without this, nothing checks
        # that C constrains the impl on the flag-OFF half of the domain (the
        # default, and the state every non-incremental caller is in).
        "module": _swap(_BASE, _FLD["warmStart"],
                        "warmStart := true,"),
        "refinement": (
            "hard-codes the incremental-fit reuse flag ON, ignoring the caller's "
            "argument. Its faithful real patch would force every estimator into "
            "incremental mode: a caller who never asked for reuse — the default, "
            "and what the whole existing suite constructs — would silently keep the "
            "previously-built members on a refit instead of building a fresh "
            "ensemble, changing the fitted model and its predictions. The suite's "
            "many non-incremental construct-fit-refit tests would see stale members "
            "carried over, so it would NOT resolve. Distinct from the drop rival: "
            "that one is wrong when the caller asks for the flag ON, this one is "
            "wrong when the caller leaves it OFF."
        ),
        "rationale": (
            "REJECT from clause C (`cfg.warmStart = warmStart`) on the OPPOSITE "
            "half of the flag domain from rival-drop-warmstart-flag: when the "
            "caller supplies the flag OFF the spec pins `cfg.warmStart = false`, "
            "but this rival hard-codes `true`. Refuted at the flag-OFF input "
            "(`warmStart` false, every frame arg 0/false) — so C is now shown to "
            "constrain the impl at BOTH flag values, not just at true. If it "
            "verified => SPEC-TOO-WEAK (C satisfiable by a constant)."
        ),
        "witness": _witness(0, 0, 0, False, 0, 0, 0, False),
    },
    {
        "id": "rival-partial-warmstart-slice",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on clause C: the flag is forwarded honestly EXCEPT on a
        # narrow slice of the argument space (when the replacement flag is set,
        # the reuse flag is forced ON). Correct on most inputs, wrong on that
        # slice — the near-miss class the two constant rivals cannot express,
        # since a constant is wrong on half the domain and trivial to catch.
        "module": _swap(
            _BASE, _FLD["warmStart"],
            "warmStart := (if bootstrap then true else warmStart),"),
        "refinement": (
            "forwards the incremental-fit reuse flag correctly EXCEPT when the "
            "caller also sets the replacement flag, in which case reuse is forced "
            "ON. Its faithful real patch would couple two independent constructor "
            "options, so a caller who asked for replacement sampling but NOT "
            "incremental reuse would silently get incremental refits and keep stale "
            "members; a caller who set neither is unaffected, which is why such a "
            "defect survives a coarse test. The suite constructs estimators with "
            "the replacement flag set and a default reuse flag and expects a fresh "
            "ensemble per fit — it would NOT resolve on that slice."
        ),
        "rationale": (
            "REJECT from clause C (`cfg.warmStart = warmStart`) on a PARTIAL "
            "sub-domain: the rival agrees with the spec everywhere the replacement "
            "flag is clear and diverges only where it is set, so it is a NEAR-MISS "
            "rather than a constant. Refuted at (`bootstrap` true, `warmStart` "
            "false) — an input point no other witness visits, and one that varies "
            "the `bootstrap` and `warmStart` binders JOINTLY, which every other "
            "witness holds independent. Demonstrates C is pinned pointwise over "
            "the whole argument space, not just on the two all-constant tuples. If "
            "it verified => SPEC-TOO-WEAK (C unconstrained on the coupled slice)."
        ),
        "witness": _witness(0, 0, 0, True, 0, 0, 0, False),
    },
    {
        "id": "rival-offbyone-nestimators",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the targeted estimator count by ARITHMETIC
        # PERTURBATION rather than constant substitution: `+ 1`. The constant
        # rival below is accidentally CORRECT at the argument value 0, so it
        # cannot be refuted there; this one is wrong at EVERY input, which is a
        # strictly stronger attack on F1 and the near-miss shape a real off-by-one
        # patch would have.
        "module": _swap(_BASE, _FLD["nEstimators"],
                        "return { nEstimators := nEstimators + 1,"),
        "refinement": (
            "forwards the targeted estimator count off by one. A faithful real "
            "patch that added one to the requested count would build an ensemble "
            "one member larger than every caller asked for; the suite that "
            "constructs an estimator with a chosen count and reads the built "
            "membership back would see one too many — it would NOT resolve. Unlike "
            "the constant-substitution frame rival this is wrong at EVERY argument "
            "value, including the 0 point where a constant rival happens to agree."
        ),
        "rationale": (
            "REJECT from frame clause F1 (`cfg.nEstimators = nEstimators`) by "
            "arithmetic perturbation rather than constant substitution. Strictly "
            "stronger than rival-corrupt-nestimators, which returns 0 and is "
            "therefore accidentally CORRECT at `nEstimators = 0` — a rival with a "
            "correct point cannot be refuted there, and its witness must avoid it. "
            "This rival has no correct point, so F1 is shown to pin the field "
            "pointwise rather than merely to forbid one constant. Refuted at "
            "`nEstimators = 1`. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(1, 0, 0, False, 0, 0, 0, False),
    },
    {
        "id": "rival-corrupt-nestimators",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the targeted estimator count: substitute a constant
        # instead of forwarding the argument. Attacks F1.
        "module": _swap(_BASE, _FLD["nEstimators"],
                        "return { nEstimators := 0,"),
        "refinement": (
            "forwards a constant estimator count instead of the caller's argument. "
            "A faithful real patch that pinned the targeted number of base "
            "estimators to a constant would build an ensemble of the wrong size for "
            "every caller who requested a different count; the suite that "
            "constructs estimators with a chosen count and reads it back would see "
            "the constant instead — it would NOT resolve. Corrupting an "
            "already-forwarded entry is exactly what the desired behaviour forbids "
            "(exposing the new flag must not disturb the existing frame)."
        ),
        "rationale": (
            "REJECT from frame clause F1 (`cfg.nEstimators = nEstimators`): the "
            "spec pins the field to the caller's argument, but this rival returns a "
            "constant. Refuted at `nEstimators = 1` (distinct from 0), so the "
            "witness varies the `nEstimators` binder. If it verified => "
            "SPEC-TOO-WEAK (the estimator-count frame unpinned)."
        ),
        "witness": _witness(1, 0, 0, False, 0, 0, 0, False),
    },
    {
        "id": "rival-corrupt-maxsamples",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the per-estimator sample budget. Attacks F2.
        "module": _swap(_BASE, _FLD["maxSamples"],
                        "maxSamples := 0,"),
        "refinement": (
            "forwards a constant sample budget instead of the caller's argument. A "
            "faithful real patch pinning the per-estimator sample budget to a "
            "constant would ignore the caller's chosen budget on every "
            "construction; the suite that sets a sample budget and reads it back "
            "would see the constant — it would NOT resolve. A frame entry the fix "
            "must leave untouched."
        ),
        "rationale": (
            "REJECT from frame clause F2 (`cfg.maxSamples = maxSamples`): pinned to "
            "the argument, but this rival returns a constant. Refuted at "
            "`maxSamples = 1` — the sole binder distinguishing this witness, so it "
            "varies the `maxSamples` binder. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(0, 1, 0, False, 0, 0, 0, False),
    },
    {
        "id": "rival-corrupt-maxfeatures",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the per-estimator feature budget. Attacks F3.
        "module": _swap(_BASE, _FLD["maxFeatures"],
                        "maxFeatures := 0,"),
        "refinement": (
            "forwards a constant feature budget instead of the caller's argument. A "
            "faithful real patch pinning the per-estimator feature budget to a "
            "constant would ignore the caller's chosen budget; the suite that sets "
            "a feature budget and reads it back would see the constant — it would "
            "NOT resolve. A frame entry the fix must leave untouched."
        ),
        "rationale": (
            "REJECT from frame clause F3 (`cfg.maxFeatures = maxFeatures`): pinned "
            "to the argument, but this rival returns a constant. Refuted at "
            "`maxFeatures = 1` — the sole binder distinguishing this witness, "
            "varying the `maxFeatures` binder. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(0, 0, 1, False, 0, 0, 0, False),
    },
    {
        "id": "rival-negate-bootstrap",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the replacement flag: forward its negation. Attacks
        # F4 — the OTHER genuine boolean, distinct from the new flag C.
        "module": _swap(_BASE, _FLD["bootstrap"],
                        "bootstrap := !bootstrap,"),
        "refinement": (
            "forwards the negation of the replacement flag. A faithful real patch "
            "that flipped whether per-estimator subsets are drawn with replacement "
            "would train every estimator under the opposite sampling regime from "
            "what the caller requested; the suite that sets the replacement flag "
            "and reads it back (or observes its sampling effect) would see the "
            "opposite — it would NOT resolve. A frame entry the fix must leave "
            "untouched."
        ),
        "rationale": (
            "REJECT from frame clause F4 (`cfg.bootstrap = bootstrap`): pinned to "
            "the argument, but this rival negates it. Refuted at `bootstrap = true` "
            "(so the returned field is `false != true`) — the sole binder "
            "distinguishing this witness, varying the `bootstrap` binder (a second "
            "genuine boolean, separate from the new flag). If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(0, 0, 0, True, 0, 0, 0, False),
    },
    {
        "id": "rival-corrupt-njobs",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the parallelism handle. Attacks F5.
        "module": _swap(_BASE, _FLD["nJobs"],
                        "nJobs := 0,"),
        "refinement": (
            "forwards a constant parallelism handle instead of the caller's "
            "argument. A faithful real patch pinning the parallelism handle to a "
            "constant would ignore the caller's chosen setting; the suite that sets "
            "it and reads it back would see the constant — it would NOT resolve. A "
            "frame entry the fix must leave untouched."
        ),
        "rationale": (
            "REJECT from frame clause F5 (`cfg.nJobs = nJobs`): pinned to the "
            "argument, but this rival returns a constant. Refuted at `nJobs = 1` — "
            "the sole binder distinguishing this witness, varying the `nJobs` "
            "binder. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(0, 0, 0, False, 1, 0, 0, False),
    },
    {
        "id": "rival-corrupt-randomstate",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the randomness handle. Attacks F6.
        "module": _swap(_BASE, _FLD["randomState"],
                        "randomState := 0,"),
        "refinement": (
            "forwards a constant randomness handle instead of the caller's "
            "argument. A faithful real patch pinning the randomness handle to a "
            "constant would fix the seed regardless of what the caller supplied, "
            "changing the fitted model for every caller who passed a different "
            "source; the suite that sets it and reads it back would see the "
            "constant — it would NOT resolve. A frame entry the fix must leave "
            "untouched."
        ),
        "rationale": (
            "REJECT from frame clause F6 (`cfg.randomState = randomState`): pinned "
            "to the argument, but this rival returns a constant. Refuted at "
            "`randomState = 1` — the sole binder distinguishing this witness, "
            "varying the `randomState` binder. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(0, 0, 0, False, 0, 1, 0, False),
    },
    {
        "id": "rival-corrupt-verbose",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the verbosity handle. Attacks F7 — the eighth and
        # last forwarded entry, so every clause is attacked by some rival.
        "module": _swap(_BASE, _FLD["verbose"],
                        "verbose := 0 }"),
        "refinement": (
            "forwards a constant verbosity handle instead of the caller's argument. "
            "A faithful real patch pinning the verbosity handle to a constant would "
            "ignore the caller's chosen level; the suite that sets it and reads it "
            "back would see the constant — it would NOT resolve. A frame entry the "
            "fix must leave untouched."
        ),
        "rationale": (
            "REJECT from frame clause F7 (`cfg.verbose = verbose`): pinned to the "
            "argument, but this rival returns a constant. Refuted at `verbose = 1` "
            "— the sole binder distinguishing this witness, varying the `verbose` "
            "binder, the eighth and last forwarded entry so every clause "
            "(F1–F7 and C) is attacked by some rival. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(0, 0, 0, False, 0, 0, 1, False),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The two bundles model DIFFERENT surfaces (carrier narrowing, see header): the
# nagini file contracts the downstream fitting decision over a List[int] roster
# (refit_to_size / reuse_and_extend / rebuild_all); this bundle contracts the
# UPSTREAM constructor that forwards the keyword configuration. So most nagini
# cases attack a function this bundle does not model and have NO counterpart —
# that is the expected shape of a correctly-narrowed port, not an omission gap.
#
#   nagini case                            -> here
#   -----------------------------------------------------------------------
#   pos-dispatch-inverted-guard            -> pos-control-reordered-fields  RE-EXPRESSED
#   pos-reuse-lentest-loop                 -> pos-control-staged-local      RE-EXPRESSED
#   (no sibling)                           -> pos-control-value-identities  ADDED (non-defeq positive)
#   admiss-self-call-warmstart             -> admiss-gold-total             RE-AIMED
#   rival-always-rebuild                   -> rival-drop-warmstart-flag     RE-EXPRESSED (same bug, this carrier)
#   rival-always-reuse                     -> rival-force-warmstart-flag    RE-EXPRESSED (dual bug at the forwarding surface)
#   rival-frame-mutate-existing-dispatch   -> (none)                        VACUOUS (not a well-formed program; measured)
#   rival-frame-mutate-existing-reuse      -> (none)                        VACUOUS (not a well-formed program; measured)
#   rival-partial-short-tail               -> rival-offbyone-nestimators    RE-EXPRESSED (off-by-one on the forwarded count)
#   rival-partial-gt1-guard                -> rival-partial-warmstart-slice RE-EXPRESSED (near-miss slice on clause C)
#   (no sibling)                           -> rival-corrupt-nestimators     ADDED (frame clause F1)
#   (no sibling)                           -> rival-corrupt-maxsamples      ADDED (frame clause F2)
#   (no sibling)                           -> rival-corrupt-maxfeatures     ADDED (frame clause F3)
#   (no sibling)                           -> rival-negate-bootstrap        ADDED (frame clause F4)
#   (no sibling)                           -> rival-corrupt-njobs           ADDED (frame clause F5)
#   (no sibling)                           -> rival-corrupt-randomstate     ADDED (frame clause F6)
#   (no sibling)                           -> rival-corrupt-verbose         ADDED (frame clause F7)
#   AXIOM_TESTS (empty upstream)           -> (none)                        DROPPED (G-AX lane; empty here too)
#
# 15 velvet SPEC cases: 3 soundness, 1 admissibility, 11 uniqueness.
#
# AUDIT REVISION. An independent audit re-derived each "NO COUNTERPART" claim
# above with real builds and found three of them WRONG: the nagini case attacked
# a roster property this bundle does not model, but its ADVERSARIAL CLASS (a dual
# bug, a near-miss partial sub-domain, an off-by-one) does have a form on the
# forwarding surface, and the port had conflated the two. Landed as
# rival-force-warmstart-flag, rival-partial-warmstart-slice and
# rival-offbyone-nestimators; each was confirmed to elaborate its witness against
# its rival and to be refuted by `decide` against the frozen solution. The audit
# also found both original positives DEFEQ to the frozen assembly (every field
# still the bare argument name), which makes them weak SPEC-TOO-STRONG probes;
# pos-control-value-identities was added as a non-defeq positive. No spec hole:
# six further tuned wrong impls (a pairwise field swap, the flag echoing another
# argument, the flag negated, the flag conjoined with another argument, the flag
# sliced on a handle value, a count off-by-one) were all REJECTED against the
# frozen spec, and five further correct reshapes (`with`-update from `default`,
# per-field `let` bindings, arithmetic identities, boolean identities, the
# anonymous constructor `⟨...⟩`) all VERIFIED.
#
# RE-EXPRESSED (positives): the nagini positives are a De-Morgan-inverted
#   dispatch and a loop-shape-changed reuse copy over the roster functions. On
#   this carrier the modeled function is a straight-line record assembly with no
#   dispatch and no loop, so those exact reshapes have no impl-region form; the
#   ANALOGUE structurally-different-but-correct reshapes are a field reorder and a
#   let-staged assembly, carrying the same argument (a faithful correct impl of
#   the modeled function must verify, else SPEC-TOO-STRONG).
# RE-AIMED (admiss): the nagini admissibility case establishes the read-only
#   fractional-permission precondition on an F2P-shaped roster. This method has no
#   `require` and no heap permission, so that probe is vacuous; re-aimed at
#   total-domain post-image joint satisfiability, witnessed by the frozen impl.
# RE-EXPRESSED (the bug, rival-always-rebuild -> rival-drop-warmstart-flag):
#   nagini's #1 rival is the prepatch that ALWAYS rebuilds — the DOWNSTREAM
#   manifestation of "the reuse flag never reaches the fit". On this carrier the
#   SAME bug is upstream: the constructor never forwards the flag, so it never
#   reaches the base machinery. Same defect, same refinement argument (the F2P
#   warm-refit reuse assertion fails), expressed at the modeled surface and
#   witnessed at the flag-ON input.
# RE-EXPRESSED (rival-always-reuse, rival-partial-short-tail,
#   rival-partial-gt1-guard): the port originally recorded these as NO
#   COUNTERPART on the grounds that they attack the roster dispatch guard, the
#   size pin and the reuse threshold — downstream properties this bundle does not
#   model. The first half of that is true and the CONCLUSION was wrong: what has
#   no counterpart is the roster MECHANISM, but each case's adversarial CLASS is
#   expressible at the forwarding surface, and that class is what a battery ports.
#     - rival-always-reuse is the DUAL of the bug (force the behaviour on instead
#       of dropping it) -> rival-force-warmstart-flag hard-codes the flag ON,
#       attacking clause C on the flag-OFF half of the domain that the drop rival
#       leaves untested.
#     - rival-partial-gt1-guard is a NEAR-MISS on a narrow sub-domain (correct
#       except at one boundary) -> rival-partial-warmstart-slice forwards the flag
#       honestly except when the replacement flag is set.
#     - rival-partial-short-tail is an OFF-BY-ONE on a forwarded quantity ->
#       rival-offbyone-nestimators forwards the count `+ 1`, which unlike the
#       constant rival is wrong at every input.
#   All three were landed with machine-checked witnesses, so none is omitted.
# FRAME-MUTATION (rival-frame-mutate-existing-*): VACUOUS, and demonstrated. The
#   nagini rivals write through a read-only (1/2) reference to the roster and are
#   rejected for insufficient permission. Velvet is referentially transparent; the
#   inputs are immutable values, no `mut` binder, no heap, no aliasing, no
#   permission system. Measured rather than argued: an impl body attempting
#   `nEstimators := 0` (or `warmStart := true`) fails in the ELABORATOR with
#   "`nEstimators` cannot be mutated, only variables declared using `let mut` can
#   be mutated", i.e. the rival is not a well-formed program and its rejection
#   says nothing about the postcondition — the one thing a reject case must not
#   be. No substitute fabricated. (The frame is still DEFENDED, but by the value
#   contract F1–F7, which the frame-corruption rivals above attack.)
# ADDED (7 frame rivals): the nagini file has a single forwarded output (the
#   roster) so it has no per-field frame clauses to attack individually. This
#   carrier forwards EIGHT independent entries, so each frame clause F1–F7 (plus
#   C) is a distinct impl-constraining obligation; a rival corrupting exactly one
#   forwarded field is a real, witnessable SPEC-TOO-WEAK probe for that clause.
#   These complete coverage of every forwarding clause. Real divergences with
#   machine-checked witnesses, not fabricated wrongness.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
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
# DROPPED (AXIOM_TESTS): the nagini axiom lane is empty (no @ContractOnly axiom —
#   the model is deep); this bundle likewise axiomatizes no callee. The G-PBT gate
#   ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The eight independent `ensures` (F1–F7 frame
#   + C the new flag) are each impl-constraining. C is attacked by THREE rivals
#   from three directions — dropped to a constant `false`
#   (rival-drop-warmstart-flag, refuted at flag ON), forced to a constant `true`
#   (rival-force-warmstart-flag, refuted at flag OFF), and honoured everywhere
#   except a coupled slice (rival-partial-warmstart-slice, refuted at bootstrap
#   ON / flag OFF) — so C is shown to be pinned at BOTH flag values and pointwise
#   across the slice, not merely to forbid one constant. F1 is attacked twice, by
#   constant substitution and by arithmetic perturbation
#   (rival-offbyone-nestimators), the latter having no accidentally-correct point.
#   F2–F7 by the remaining frame-corruption rivals; so every top-level clause is
#   attacked by some rival. The eleven witnesses span NINE distinct input points:
#   the bootstrap-ON tuple is shared by rival-partial-warmstart-slice and
#   rival-negate-bootstrap, and the nEstimators=1 tuple by
#   rival-offbyone-nestimators and rival-corrupt-nestimators — a shared point is
#   not a redundancy, since each of those pairs refutes a DIFFERENT impl there
#   (that is precisely how the off-by-one is shown to be a strictly stronger
#   attack than the constant at the same input). The bootstrap-ON point is the
#   only one where two binders move together (bootstrap and warmStart), which the
#   all-constant tuples cannot express. All three
#   positives and the admissibility case defend all eight clauses jointly on gold,
#   and pos-control-value-identities does so through terms that are NOT
#   definitionally the frozen ones.
#
# WITNESS MECHANICS: the carrier is fully transparent (EnsembleConfig derives
#   DecidableEq; Param = Int; Bool fields). Each witness reaches the post-image via
#   `configureEnsembleTester <args> = false` and closes by `decide`, checked in a
#   file whose `prove_correct` block is stripped. Every argument is a concrete
#   literal so the extracted program reduces under the kernel — the tester is
#   `false` for the rival (postcondition violated) and `true` for gold (so `=
#   false` fails), giving elaborate-on-rival / fail-on-gold. No witness binds a
#   hypothesis, so no consistency probe is needed. All checked with
#   scripts/lean_verify.sh: rival exit 0, gold build fails (`decide` proved the
#   proposition is false).
AXIOM_TESTS = []
