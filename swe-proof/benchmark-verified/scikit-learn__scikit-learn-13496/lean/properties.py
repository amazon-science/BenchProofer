"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13496 (lean).

NOT a Lean module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region — and, for the two positives whose assembly shape the
frozen ``rfl`` script cannot close, the ``-- proof-start`` / ``-- proof-end``
tactic BODY — is changed. The consumer spec view elides both regions, so
``markers.same_spec`` holds and the ``theorem correct_isolationForestInit``
statement survives byte-identically; rewriting a proof body is inside the
variant scope, which requires the STATEMENT to be preserved and bans only new
axioms / ``sorry`` / ``native_decide`` / new theorems) and swaps in a candidate
implementation; it
is then checked by the real verifier. ``expect:"verify"`` passes iff (in scope
AND verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND
its refutation ``witness`` discriminates: the witness must ELABORATE against the
rival and FAIL against the frozen solution).

CARRIER NARROWING — READ THIS FIRST. The nagini sibling models the DOWNSTREAM
fitting decision: three functions (``refit_to_size`` / ``reuse_and_extend`` /
``rebuild_all``) over a ``List[int]`` roster of member identities, with a
prefix-preserving reuse postcondition, a size pin, and read-only (fractional
permission) roster inputs. THIS bundle models a DIFFERENT, upstream surface: the
single constructor that assembles the stored configuration it hands to the base
ensemble machinery. The reuse-vs-rebuild roster algorithm lives in UNCHANGED
library code and is NOT re-modeled here (re-modeling unchanged library code as
the fix would be unfaithful). The change under spec is configuration plumbing:
the incremental-refit reuse flag becomes a settable constructor parameter and is
stored as the caller supplied it. So every nagini case attached to the roster
behaviour (the reuse-prefix postcondition, the size pin, the permission-write
rivals, the tail/threshold partial-domain rivals) has no counterpart on this
carrier at the level of its MECHANICS — what ports is the ARGUMENT each one
makes, re-aimed at the clause structure this bundle does carry. Full
nagini→lean accounting in the footer.

DEFENDED SURFACE (one obligation, ``correct_isolationForestInit``). The
postcondition is a twelve-way conjunction over ten inputs:

  C   the exposed incremental-refit flag is stored exactly as supplied   <- the fix
  F1  the sample-replacement flag is stored as supplied
  D1  the feature-subsampling flag is held at its default (off)
  D2  the out-of-bag-scoring flag is held at its default (off)
  F2  the member count is stored as supplied
  P1  the per-member sample budget is stored as supplied
  P2  the contamination value is stored as supplied
  P3  the per-member feature budget is stored as supplied
  P4  the parallelism handle is stored as supplied
  F3  the strategy string is stored as supplied
  P5  the state handle is stored as supplied
  F4  the verbosity level is stored as supplied

C is the DISCRIMINATING clause: pre-change the flag was not a settable
parameter, so the stored configuration always carried the base machinery's
inherited default and the iterative member-addition behaviour was unreachable.
The prepatch impl fails exactly C when the caller supplies the flag ON. C's
siblings are the FRAME, in the sense §0.5 of the spec guide gives that word on a
referentially-transparent carrier: exposing one new entry must not disturb any
entry already forwarded, nor silently move a never-exposed entry off its
default. A rival that stores the new flag correctly but corrupts one other entry
is equally wrong, so each of those clauses is separately impl-constraining and
separately attacked below.

WHAT IS ATTACKABLE, AND WHAT TYPING ALREADY SETTLES. Seven clauses (C, F1–F4,
D1, D2) range over ``Bool`` / ``Nat`` / ``String`` fields, so a wrong impl can
be written for each and refuted at a concrete input. The other five (P1–P5) pin
fields whose types are universally-quantified TYPE VARIABLES: the constructor
never inspects those five values, it only stores them, so they are modeled
polymorphically. In that context the ONLY inhabitant of each such type is the
corresponding argument itself — there is no constant, no coercion, and no
same-typed sibling field to substitute (the five variables are pairwise
distinct). So no COMPUTABLE well-typed implementation can violate P1–P5: those
clauses are enforced largely by PARAMETRICITY rather than by the postcondition
alone, and there is no ordinary rival to write for them. Their input binders are
nevertheless VARIED across the reject witnesses below, so no binder is held at
one value by the battery.

That claim used to be stated absolutely ("no well-typed implementation can
violate P1–P5"), and an audit MEASURED it to be too strong, so it is now stated
as above. The counterexample: mark the definition ``noncomputable`` and store
``Classical.choice (⟨maxSamples⟩ : Nonempty Sample)`` instead of ``maxSamples``.
That elaborates (exit 1 only at the proof, not at the assembly — with the
frozen definition it fails the code generator, and ``noncomputable`` removes
even that), and ``variant_scope`` admits it: ``Classical.choice`` is not a
banned assumption token, so the file is a well-formed in-scope variant whose
build fails. What it is NOT is a case this battery can honestly ship, and the
reason is specific rather than a matter of proof difficulty. ``Classical.choice``
on a ``Nonempty Sample`` witness is not REFUTABLE at the value level: the term
is opaque, so the equation ``Classical.choice ⟨v⟩ = v`` is neither provable nor
disprovable, and a value-level witness against it fails on BOTH sides (measured:
``simp_all`` leaves unsolved goals against the rival exactly as it does against
gold). A hypothesis-conditioned witness stating the refutation at a point
described by ``≠`` was also built and it elaborates against BOTH the rival and
the frozen solution (exit 0 / exit 0) — it discriminates nothing, because the
hypothesis it assumes is not satisfiable-in-fact for gold and not refutable for
the rival either. A rival whose rejection cannot be attributed to the spec by
any witness is exactly what the witness rule exists to exclude, so it is
reported here rather than shipped. It is also not a SPEC hole: the rival is
rejected, so the spec is not too weak at P1; the residue is only that P1–P5's
enforcement rests partly on computability rather than purely on typing.

CARRIER NOTE — THE DECIDABLE BOUNDARY. This carrier is fully TRANSPARENT: no
``opaque`` callee, no axiom, the impl is a finite record assembly, and every
concretely-instantiated field type (``Bool`` / ``Nat`` / ``String``) decides.
So each witness states the refutation directly — ``¬ problem_spec_… <literals>
(implementation_… <the same literals>)`` closed by ``decide`` — in a file whose
proof region has been emptied, so no tactic script can mask the verdict. The
five polymorphic parameters are instantiated at ``Nat`` literals by inference.
No witness needs to condition on an opaque term, so no witness declares a head
binder and no consistency probe applies. Both halves were confirmed with
``scripts/lean_verify.sh``: every witness elaborates against its rival (exit 0)
and fails against the frozen solution (exit 1, ``decide`` reporting the
proposition is false — a real verdict, never a stuck reduction). A second,
independent audit re-derived all THIRTEEN reject witnesses from scratch and
observed exactly those exit codes, with the gold-side error reading ``Tactic
`decide` proved that the proposition … is false`` in every case — a semantic
refutation, never a missing identifier, a type error, an unfolding failure or a
timeout.

That second audit also ran the FORGERY test on every one of the thirteen, which
is the check that distinguishes a gold-side exit code carrying information about
the CLAIM from one that would fire for any claim at all. For each case it built
a file differing from the witness only in dropping the ``¬`` — i.e. asserting
that the frozen solution IS correct at the witness point, the opposite of a
refutation — against the frozen solution. All thirteen forgeries elaborate (exit
0) where the witness itself fails (exit 1). So gold's verdict tracks the claim
rather than the file's shape, and none of these rejections rests on a stuck
reduction, a missing ``Decidable`` instance or a unification failure. Audit
repairs and the evidence for each are recorded inline at the cases they touch
and in the footer.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13496"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. Every anchor below lies STRICTLY inside the single
# `-- impl-start` / `-- impl-end` region and is unique in the file (both facts
# asserted at load by _swap / the asserts here), so each variant's edit is
# confined to the impl region and `same_spec` holds by construction. The
# theorem statement and its proof body are left untouched by every rival: the
# frozen script fails against a wrong impl, which is the rejection, and the
# witness is what attributes that rejection to the spec.
# ---------------------------------------------------------------------------

# the whole assembled value, including its signature tail (the positives that
# change the assembly SHAPE swap on this block).
_ASSEMBLY_HEAD = "    EnsembleConfig Sample Contam Feat Jobs Rand := Id.run do\n"
_BODY = """  -- forward the bagging parameters to the parent constructor, exposing the
  -- incremental-refit flag so it is stored as supplied
  let mut cfg : EnsembleConfig Sample Contam Feat Jobs Rand := {
    nEstimators := nEstimators,
    maxSamples := maxSamples,
    contamination := contamination,
    maxFeatures := maxFeatures,
    bootstrap := bootstrap,
    bootstrapFeatures := false,
    oobScore := false,
    warmStart := warmStart,
    nJobs := nJobs,
    behaviour := behaviour,
    randomState := randomState,
    verbose := verbose }
  return cfg"""
assert _BASE.count(_BODY) == 1, "impl-body anchor drift — re-sync _BODY"
assert _BASE.count(_ASSEMBLY_HEAD + _BODY) == 1, "impl anchor drift"

# per-entry anchors for the clause rivals. Corrupting exactly ONE stored entry
# leaves every other clause satisfied, so the rejection is attributable to that
# entry's clause alone.
_ENT = {
    "warmStart":         "    warmStart := warmStart,",
    "bootstrap":         "    bootstrap := bootstrap,",
    "bootstrapFeatures": "    bootstrapFeatures := false,",
    "oobScore":          "    oobScore := false,",
    "nEstimators":       "    nEstimators := nEstimators,",
    "behaviour":         "    behaviour := behaviour,",
    "verbose":           "    verbose := verbose }",
}
for _k, _v in _ENT.items():
    assert _BASE.count(_v) == 1, f"entry anchor drift for {_k}: {_v!r}"

# The frozen PROOF body, for the positives whose impl shape the frozen
# `refine ⟨rfl, …⟩` script cannot close. Rewriting a proof BODY is inside the
# variant scope (`variant_scope` requires the theorem's STATEMENT to survive
# byte-identically and bans only new axioms / sorry / native_decide / new
# theorems — the tactic body may differ, since a variant legitimately reproves);
# the swap is confined to text strictly inside the `-- proof-start` /
# `-- proof-end` region, which the consumer spec view elides alongside the impl,
# so `same_spec` still holds. A positive that needs this is STRONGER evidence
# than one the frozen script happens to close: the obligation is discharged
# again from the statement rather than inherited from the frozen assembly's form.
_PROOF = """  unfold problem_spec_isolationForestInit implementation_isolationForestInit
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩"""
# The admissibility proof: a concrete-input satisfiability `have`, discharged by
# EVALUATION, in front of the reproven general obligation. See the case.
_PROOF_ADMISS = """  -- ADMISSIBILITY, stated where it bites: the twelve-clause post-image is
  -- JOINTLY SATISFIABLE at the concrete input the failing scenario is shaped
  -- like (the exposed flag requested ON, together with sample replacement),
  -- discharged by EVALUATION before the general obligation is closed. On a
  -- total carrier this is the analogue of the precondition probe: if any clause
  -- were unsatisfiable at exactly that point, `decide` here would report the
  -- proposition false and the case would fail, which is precisely the
  -- PRECOND-TOO-STRONG direction. Note it cannot be closed by `rfl` or
  -- inherited from the frozen script — it is a separate obligation about a
  -- named point, not a restatement of the theorem.
  have hsat : problem_spec_isolationForestInit
      10 (20 : Nat) (1 : Nat) (2 : Nat) true (3 : Nat) "new" (4 : Nat) 0 true
      (implementation_isolationForestInit
        10 (20 : Nat) (1 : Nat) (2 : Nat) true (3 : Nat) "new" (4 : Nat) 0 true) := by
    unfold problem_spec_isolationForestInit implementation_isolationForestInit
    decide
  -- and now the obligation itself, reproven at the byte-identical statement
  -- over BOTH polarities of the discriminating binder
  unfold problem_spec_isolationForestInit implementation_isolationForestInit
  cases warmStart <;> simp"""
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"


# ---------------------------------------------------------------------------
# Witness builder. Argument order matches the spec predicate:
#   nEstimators maxSamples contamination maxFeatures bootstrap nJobs
#   behaviour randomState verbose warmStart
# The five polymorphic parameters are passed as `Nat` literals (inference
# instantiates Sample/Contam/Feat/Jobs/Rand at Nat); the concrete parameters as
# their own literals. Everything decides, so `decide` closes the negation
# against a rival and fails against the frozen solution.
# ---------------------------------------------------------------------------

def _b(x):
    return "true" if x else "false"


def _witness(nEst, maxS, contam, maxF, boot, nJobs, behaviour, rand, verbose, ws):
    args = ("%d (%d : Nat) (%d : Nat) (%d : Nat) %s (%d : Nat) %s (%d : Nat) %d %s"
            % (nEst, maxS, contam, maxF, _b(boot), nJobs,
               '"%s"' % behaviour, rand, verbose, _b(ws)))
    return (
        "example : ¬ problem_spec_isolationForestInit\n"
        "    %s\n"
        "    (implementation_isolationForestInit\n"
        "      %s) := by\n"
        "  unfold problem_spec_isolationForestInit implementation_isolationForestInit\n"
        "  decide\n" % (args, args))


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, each reproven inside the frozen `-- proof-start` /
    # `-- proof-end` region with the obligation's statement byte-identical. If a
    # faithful correct assembly cannot verify, the spec (or its proof
    # obligation) is over-fit to the frozen assembly form => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-reordered-entries",
        "kind": "soundness",
        "expect": "verify",
        # Assemble the same configuration with the entries written in REVERSE
        # textual order. A structure value does not depend on the order its
        # fields are supplied, so all twelve clauses still hold.
        "module": _swap(
            _BASE, _BODY,
            """  -- assemble the stored configuration, supplying the entries in a different
  -- textual order
  let mut cfg : EnsembleConfig Sample Contam Feat Jobs Rand := {
    verbose := verbose,
    randomState := randomState,
    behaviour := behaviour,
    nJobs := nJobs,
    warmStart := warmStart,
    oobScore := false,
    bootstrapFeatures := false,
    bootstrap := bootstrap,
    maxFeatures := maxFeatures,
    contamination := contamination,
    maxSamples := maxSamples,
    nEstimators := nEstimators }
  return cfg"""),
        "rationale": (
            "a CORRECT impl with a different assembly text: the twelve entries "
            "are supplied in reverse order. A structure value is independent of "
            "the order its fields are given, so every clause (C, F1–F4, D1, D2, "
            "P1–P5) still discharges and the frozen proof closes unchanged. "
            "Ports the nagini pos-dispatch-inverted-guard argument — a "
            "structurally-different but semantically identical impl of the "
            "modeled function must verify. If it fails => SPEC-TOO-STRONG "
            "(over-fit to the frozen assembly text)."
        ),
    },
    {
        "id": "pos-direct-value",
        "kind": "soundness",
        "expect": "verify",
        # A different CONTROL shape: drop the imperative staging entirely and
        # hand back the assembled value as a single expression.
        "module": _swap(
            _BASE, _ASSEMBLY_HEAD + _BODY,
            """    EnsembleConfig Sample Contam Feat Jobs Rand :=
  -- hand back the stored configuration directly, as a single value
  { nEstimators := nEstimators,
    maxSamples := maxSamples,
    contamination := contamination,
    maxFeatures := maxFeatures,
    bootstrap := bootstrap,
    bootstrapFeatures := false,
    oobScore := false,
    warmStart := warmStart,
    nJobs := nJobs,
    behaviour := behaviour,
    randomState := randomState,
    verbose := verbose }"""),
        "rationale": (
            "a CORRECT impl with a different control shape: the imperative "
            "staging is dropped and the configuration is returned as one value. "
            "Same observable result, so every clause discharges and the frozen "
            "proof closes as-is. Ports the nagini pos-reuse-lentest-loop "
            "argument (same observable output, different code shape) — on this "
            "carrier the modeled function has no loop to reshape, so the "
            "analogous reshape is the staging. If it fails => SPEC-TOO-STRONG "
            "(over-fit to the staged form)."
        ),
    },
    {
        "id": "pos-staged-then-store-flag",
        "kind": "soundness",
        "expect": "verify",
        # A different DATA-FLOW shape: stage every entry first with the exposed
        # flag at its default, then store the caller's flag by field update. The
        # observable result is identical; this is the shape most likely to break
        # a proof over-fit to a single record literal, which is why it is here.
        "module": _swap(
            _BASE, _BODY,
            """  -- stage the carried entries first, then store the exposed flag from the
  -- caller's argument
  let base : EnsembleConfig Sample Contam Feat Jobs Rand := {
    nEstimators := nEstimators,
    maxSamples := maxSamples,
    contamination := contamination,
    maxFeatures := maxFeatures,
    bootstrap := bootstrap,
    bootstrapFeatures := false,
    oobScore := false,
    warmStart := false,
    nJobs := nJobs,
    behaviour := behaviour,
    randomState := randomState,
    verbose := verbose }
  let mut cfg : EnsembleConfig Sample Contam Feat Jobs Rand :=
    { base with warmStart := warmStart }
  return cfg"""),
        "rationale": (
            "a CORRECT impl with a different DATA FLOW: the entries are staged "
            "with the exposed flag at its default and the caller's flag is then "
            "stored by field update, so the flag's value reaches the result "
            "through a second assignment rather than the initial literal. "
            "Observationally identical, so all twelve clauses discharge. This is "
            "the reshape most likely to expose a spec/proof over-fit to one "
            "record literal — if it fails => SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-strategy-append-empty",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (attack E). The three positives above are all closed by
        # the frozen `refine ⟨rfl, …⟩` script, i.e. each is DEFINITIONALLY equal
        # to the frozen assembly, so none of them can detect a spec or proof
        # over-fit to the frozen impl's syntactic form. This one is not: the
        # strategy string is stored as `behaviour ++ ""`, which is EQUAL to
        # `behaviour` but not by `rfl` (String append does not reduce on an
        # opaque argument), so clause F3 has to be discharged by a real
        # propositional step. Measured: the frozen script FAILS on this impl
        # (exit 1, `Application type mismatch` at the F3 conjunct), and with F3's
        # conjunct reproven by `simp` it verifies (exit 0).
        "module": _swap(
            _swap(_BASE, _ENT["behaviour"], '    behaviour := behaviour ++ "",'),
            _PROOF,
            """  unfold problem_spec_isolationForestInit implementation_isolationForestInit
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, ?_, rfl, rfl⟩
  simp"""),
        "rationale": (
            "a CORRECT impl whose stored strategy value is NOT syntactically "
            "the caller's argument: appending the empty string is the identity "
            "on strings, so clause F3 (`result.behaviour = behaviour`) still "
            "holds, but it does not hold by `rfl` — the frozen script cannot "
            "close it and the conjunct must be reproven propositionally. This "
            "is the strongest of the four soundness positives precisely because "
            "the other three are definitionally equal to the frozen assembly "
            "and are therefore closed by the frozen script unchanged; a spec "
            "(or a proof obligation) over-fit to the frozen impl's syntactic "
            "form would reject this one. It complements the shipped rival "
            "rival-strategy-decorated, which stores `behaviour ++ \"x\"`: the "
            "two differ only in whether the appended string is empty, so "
            "together they show F3 is refuting on the VALUE stored rather than "
            "on the syntactic shape of the expression that produces it. If it "
            "fails => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY. The obligation binds NO precondition hypothesis (the
    # pre-conditions region is absent and `correct_isolationForestInit` quantifies
    # over every argument unconditionally), so the nagini
    # admiss-self-call-warmstart probe — a self-call establishing a read-only
    # fractional-permission precondition on an F2P-shaped roster — has no
    # counterpart: there is no precondition to establish and no permission
    # surface. RE-AIMED at the residual total-domain risk, that the twelve-clause
    # post-image is jointly satisfiable on EVERY half of the domain the
    # discriminating binder cuts it into. MUST verify, else the spec is
    # unsatisfiable somewhere (a vacuously-strong spec no correct impl could
    # meet on that sub-domain).
    #
    # AUDIT REPAIR. This case previously shipped `"module": _BASE` — the frozen
    # file byte-for-byte. That verified honestly but tested NOTHING the G-VERIFY
    # lane does not already establish: it re-ran the frozen build, so its pass
    # was a restatement of "the frozen artifact verifies" rather than an
    # admissibility probe, and it would have kept passing under any spec change
    # the frozen proof still happened to close. Replaced with an impl that
    # assembles the configuration by CASE ANALYSIS on the discriminating binder,
    # so each polarity of the exposed flag is a separate branch that must
    # discharge all twelve clauses on its own half of the domain. Measured: the
    # frozen `refine ⟨rfl, …⟩` script does NOT close this impl (exit 1,
    # `Application type mismatch` — the branch is not syntactically the record
    # literal `rfl` needs), so the case genuinely reproves rather than reusing
    # the frozen proof; with the obligation's statement byte-identical and the
    # proof reproven as `cases warmStart <;> simp` it verifies (exit 0).
    # =====================================================================
    {
        "id": "admiss-total-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _BODY,
                """  -- both polarities of the exposed flag are separately in-domain: assemble
  -- the stored configuration by case analysis on the caller's flag, so each
  -- branch must discharge every clause on its own half of the domain
  let mut cfg : EnsembleConfig Sample Contam Feat Jobs Rand :=
    if warmStart then
      { nEstimators := nEstimators, maxSamples := maxSamples,
        contamination := contamination, maxFeatures := maxFeatures,
        bootstrap := bootstrap, bootstrapFeatures := false, oobScore := false,
        warmStart := true, nJobs := nJobs, behaviour := behaviour,
        randomState := randomState, verbose := verbose }
    else
      { nEstimators := nEstimators, maxSamples := maxSamples,
        contamination := contamination, maxFeatures := maxFeatures,
        bootstrap := bootstrap, bootstrapFeatures := false, oobScore := false,
        warmStart := false, nJobs := nJobs, behaviour := behaviour,
        randomState := randomState, verbose := verbose }
  return cfg"""),
            _PROOF, _PROOF_ADMISS),
        "rationale": (
            "the obligation carries no precondition hypothesis, so the modeled "
            "function is total over every argument tuple; the admissibility "
            "question that remains is whether the twelve-clause post-image is "
            "jointly satisfiable on each half of the domain the discriminating "
            "binder cuts, not merely on the domain as an undivided whole. This "
            "impl assembles the configuration by case analysis on the exposed "
            "flag, so BOTH polarities are separately in-domain and each branch "
            "discharges all twelve clauses by itself, with the five polymorphic "
            "parameters left arbitrary. The frozen proof script does not close "
            "it (the branch is not the record literal `rfl` needs), so the "
            "obligation is genuinely reproven at the byte-identical statement "
            "rather than inherited. IN ADDITION, and this is the part that "
            "makes it an admissibility probe rather than another soundness "
            "reshape, the proof first discharges the post-image AT THE CONCRETE "
            "INPUT the failing scenario is shaped like — the exposed flag "
            "requested ON with sample replacement — as a `have` closed by "
            "EVALUATION (`decide`), before closing the general obligation. That "
            "is the total-carrier analogue of the precondition probe the nagini "
            "sibling runs: an obligation can be vacuously strong by being "
            "UNSATISFIABLE at exactly the input the scenario needs, and a "
            "`decide` at that named point is what detects it (it would report "
            "the proposition false, failing the case). Re-aimed from the nagini "
            "admiss-self-call-warmstart, whose permission-establishing half has "
            "no counterpart here. If it fails => PRECOND-TOO-STRONG / "
            "SPEC-UNSATISFIABLE on a polarity of the domain."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input point and the refinement argument that its
    # faithful real counterpart would NOT resolve the instance. Each rival
    # corrupts exactly ONE stored entry (except the deliberate partial-domain
    # pair, which is stated as such), so its witness varies exactly the binder
    # its clause depends on and every other clause stays satisfied.
    # =====================================================================
    {
        "id": "rival-drop-exposed-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # THE DEFECT ITSELF (the prepatch impl verbatim): the exposed
        # incremental-refit flag is not stored from the caller's argument; the
        # configuration always carries the inherited default. Attacks C.
        "module": _swap(_BASE, _ENT["warmStart"], "    warmStart := false,"),
        "refinement": (
            "this is the pre-change behaviour: the incremental-refit reuse flag "
            "is not a settable parameter, so the stored configuration always "
            "carries the base machinery's inherited default (reuse off) no "
            "matter what the caller asks for, and the iterative "
            "member-addition path is unreachable. Its faithful real counterpart "
            "is the unchanged constructor. The failing test requests the flag "
            "ON, fits, remembers the first fitted member, raises the target "
            "member count, fits again, and asserts BOTH the enlarged member "
            "count and that the first member is the very same object as before. "
            "With the flag dropped the whole ensemble is rebuilt from scratch on "
            "the second fit, so the first member is a brand-new object and the "
            "identity assertion fails — it would NOT resolve. This is exactly "
            "the defect the change corrects."
        ),
        "rationale": (
            "REJECT from clause C (`result.warmStart = warmStart`): at "
            "an input where the caller supplies the flag ON the spec pins the "
            "stored flag to ON, but this rival hard-codes the default. Refuted "
            "at the flag-ON input (replacement also on, so the point is "
            "distinct from the sub-domain rival below, which is CORRECT at that "
            "point). If it verified => SPEC-TOO-WEAK: the spec would admit the "
            "very defect under repair."
        ),
        "witness": _witness(10, 20, 1, 2, True, 3, "new", 4, 0, True),
    },
    {
        "id": "rival-invert-exposed-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual: the exposed flag is stored INVERTED, so a caller who leaves
        # it off gets reuse forced on. Attacks C at the OTHER polarity, which the
        # drop rival cannot reach (it agrees with the spec whenever the flag is
        # off). Ports the nagini rival-always-reuse argument.
        "module": _swap(_BASE, _ENT["warmStart"], "    warmStart := !warmStart,"),
        "refinement": (
            "stores the exposed flag inverted. Its faithful real counterpart is "
            "wrong on both halves of the domain and so cannot resolve: with the "
            "flag requested ON it stores reuse-off and the failing test's "
            "member-identity assertion fails exactly as in the pre-change "
            "behaviour; with the flag left OFF it FORCES reuse, so a "
            "default-configured estimator that is fitted twice silently keeps "
            "its stale members instead of building a whole new ensemble, "
            "changing the fitted model and its scores for the existing suite "
            "(which constructs estimators without requesting reuse and expects a "
            "freshly built ensemble each fit). Either half alone means NOT "
            "resolved."
        ),
        "rationale": (
            "REJECT from clause C (`result.warmStart = warmStart`) at the flag-OFF "
            "polarity: the spec pins the "
            "stored flag to the supplied value, so at flag-OFF it must be off, "
            "and this rival stores on. Refuted at the flag-OFF input — a point "
            "where the drop rival above is ACCIDENTALLY correct, so this is a "
            "genuinely different discriminator and demonstrates C's dependence "
            "on the flag binder at both polarities, not just one. If it verified "
            "=> SPEC-TOO-WEAK (C constrains only one polarity)."
        ),
        "witness": _witness(11, 21, 2, 3, False, 4, "alt", 5, 1, False),
    },
    {
        "id": "rival-flag-conditioned-on-replacement",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the exposed flag: it is stored only when the
        # replacement flag is also set, so the rival agrees with the spec
        # everywhere except the (flag ON, replacement off) sub-domain. Ports the
        # nagini rival-partial-gt1-guard argument (a strengthened guard that is
        # correct except at one boundary).
        "module": _swap(_BASE, _ENT["warmStart"],
                        "    warmStart := warmStart && bootstrap,"),
        "refinement": (
            "stores the exposed flag only when the sample-replacement flag is "
            "also set, and the default otherwise. A faithful real counterpart "
            "that honoured the reuse request only for replacement-sampled "
            "ensembles would be correct for most callers and wrong on exactly "
            "the configuration the failing test uses — it requests reuse without "
            "requesting replacement, so on that path the ensemble is rebuilt, "
            "the first previously-fitted member is replaced by a new object, and "
            "the identity assertion fails. It would NOT resolve on that "
            "sub-domain."
        ),
        "rationale": (
            "REJECT from clause C (`result.warmStart = warmStart`) on a PROPER "
            "SUB-DOMAIN: C pins the stored flag "
            "to the supplied value for every replacement setting, but this rival "
            "conflates the two entries. Refuted at (flag ON, replacement OFF) — "
            "a NEAR-MISS relative to rival-drop-exposed-flag, so it gets its own "
            "witness at the point that distinguishes it (at that rival's witness "
            "point, replacement ON, this rival is correct). If it verified => "
            "SPEC-TOO-WEAK (C unconstrained on the no-replacement sub-domain)."
        ),
        "witness": _witness(12, 22, 3, 4, False, 5, "new", 6, 2, True),
    },
    {
        "id": "rival-invert-replacement-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the OTHER genuine boolean: the sample-replacement
        # flag is stored inverted while the new flag is stored correctly.
        # Attacks F1.
        "module": _swap(_BASE, _ENT["bootstrap"], "    bootstrap := !bootstrap,"),
        "refinement": (
            "stores the sample-replacement flag inverted while handling the "
            "newly exposed flag correctly. A faithful real counterpart would "
            "train every member under the opposite sampling regime from the one "
            "requested — subsets drawn with replacement where the caller asked "
            "for without, and conversely — changing every fitted model. The "
            "existing suite constructs estimators with a chosen replacement "
            "setting and observes it (both by reading the stored setting back "
            "and through the sampling behaviour it produces), so those tests "
            "fail; resolution requires the whole accompanying suite to pass, so "
            "it would NOT resolve."
        ),
        "rationale": (
            "REJECT from frame clause F1 (`result.bootstrap = bootstrap`): the spec "
            "pins the field to the caller's argument, this "
            "rival stores its negation. Refuted at replacement ON, varying the "
            "replacement binder. Exposing the new entry must not disturb an "
            "entry already carried; if it verified => SPEC-TOO-WEAK (the "
            "replacement entry unpinned)."
        ),
        "witness": _witness(13, 23, 4, 5, True, 6, "alt", 7, 3, False),
    },
    {
        "id": "rival-enable-feature-subsampling",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupts a DEFAULT PIN rather than a forwarded entry: a flag this
        # estimator never exposes is moved off its default. Attacks D1.
        "module": _swap(_BASE, _ENT["bootstrapFeatures"],
                        "    bootstrapFeatures := true,"),
        "refinement": (
            "moves a configuration flag this estimator never exposes — "
            "per-member feature subsampling — off its default and turns it on. A "
            "faithful real counterpart would hand the base machinery a "
            "subsampling request no caller made, so every member would be "
            "trained on a drawn subset of features instead of the configured "
            "budget, changing every fitted model and every score it produces. "
            "The existing suite covers the estimator's behaviour with and "
            "without a reduced feature budget and its numerical outputs, so "
            "those tests fail — it would NOT resolve. Exposing one new entry "
            "must not silently switch on another."
        ),
        "rationale": (
            "REJECT from default-pin clause D1 (`result.bootstrapFeatures = false`): "
            "the spec pins this field to a constant, and "
            "this rival stores the opposite constant. Violated at EVERY input, "
            "so its witness point is chosen to vary the remaining binders "
            "rather than to reach the violation. If it verified => "
            "SPEC-TOO-WEAK: a never-exposed entry would be left free, which is "
            "the referentially-transparent analogue of the unconstrained-output "
            "hole (spec_guide §0.5)."
        ),
        "witness": _witness(14, 24, 5, 6, False, 7, "new", 8, 4, True),
    },
    {
        "id": "rival-enable-oob-scoring",
        "kind": "uniqueness",
        "expect": "reject",
        # The second default pin: out-of-bag scoring switched on. Attacks D2.
        "module": _swap(_BASE, _ENT["oobScore"], "    oobScore := true,"),
        "refinement": (
            "moves the second never-exposed flag — out-of-bag scoring — off its "
            "default and turns it on. A faithful real counterpart would ask the "
            "base machinery to compute an out-of-bag estimate that this "
            "estimator's scoring path does not define, for every caller, so "
            "ordinary construction-and-fit would change behaviour (an "
            "out-of-bag score computed against a scoring function this estimator "
            "does not supply). The existing suite fits this estimator in many "
            "configurations, so those tests fail — it would NOT resolve."
        ),
        "rationale": (
            "REJECT from default-pin clause D2 (`result.oobScore = false`): pinned "
            "to a constant by the spec, stored as "
            "the opposite constant by this rival. Violated at every input; the "
            "witness point is chosen to vary the other binders. If it verified "
            "=> SPEC-TOO-WEAK (the second never-exposed entry left free)."
        ),
        "witness": _witness(15, 25, 6, 7, True, 8, "alt", 9, 5, False),
    },
    {
        "id": "rival-constant-member-count",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the member count: a constant instead of the
        # caller's argument. Attacks F2.
        "module": _swap(_BASE, _ENT["nEstimators"], "    nEstimators := 0,"),
        "refinement": (
            "stores a constant member count instead of the caller's argument. A "
            "faithful real counterpart would build an ensemble of the wrong size "
            "for every caller who asked for a different count — and the failing "
            "test itself configures a count, fits, RAISES the count, fits again "
            "and asserts the enlarged number of members exactly, so with the "
            "count pinned to a constant that assertion fails outright. It would "
            "NOT resolve, and this is the entry the failing test is most "
            "directly sensitive to besides the flag itself."
        ),
        "rationale": (
            "REJECT from frame clause F2 (`result.nEstimators = nEstimators`): the "
            "spec pins the field to the caller's argument, this "
            "rival returns a constant. Refuted at a non-zero count, varying the "
            "count binder. If it verified => SPEC-TOO-WEAK (the member-count "
            "entry unpinned)."
        ),
        "witness": _witness(16, 26, 7, 8, False, 9, "new", 10, 6, True),
    },
    {
        "id": "rival-constant-verbosity",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the verbosity level. Attacks F4.
        "module": _swap(_BASE, _ENT["verbose"], "    verbose := 0 }"),
        "refinement": (
            "stores a constant verbosity level instead of the caller's "
            "argument. A faithful real counterpart would ignore the level every "
            "caller chose, so the reporting behaviour during fitting would no "
            "longer follow the configuration; the existing suite constructs "
            "estimators with a chosen level and reads the stored configuration "
            "back, so those tests fail and the instance would NOT resolve. A "
            "carried entry the change must leave untouched."
        ),
        "rationale": (
            "REJECT from frame clause F4 (`result.verbose = verbose`): pinned to the "
            "argument by the spec, returned as a "
            "constant by this rival. Refuted at a non-zero level, varying the "
            "verbosity binder. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(17, 27, 8, 9, True, 10, "alt", 11, 7, False),
    },
    {
        "id": "rival-constant-strategy",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame corruption on the strategy string. Attacks F3 — the only
        # String-valued clause, so this is the entry no numeric or boolean rival
        # can reach.
        "module": _swap(_BASE, _ENT["behaviour"], '    behaviour := "",'),
        "refinement": (
            "stores a constant strategy string instead of the caller's "
            "argument. A faithful real counterpart would pin every estimator to "
            "one strategy regardless of what was requested, so the "
            "strategy-dependent scoring path and the transition warnings keyed "
            "to it would no longer follow the caller's choice; the existing "
            "suite constructs estimators with each strategy value, reads the "
            "stored value back and asserts on the strategy-dependent behaviour, "
            "so those tests fail — it would NOT resolve."
        ),
        "rationale": (
            "REJECT from frame clause F3 (`result.behaviour = behaviour`): pinned to "
            "the argument by the spec, returned as a "
            "constant by this rival. Refuted at a non-empty strategy string, "
            "varying the strategy binder — the only String-valued binder, which "
            "no boolean or numeric rival can discriminate. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(18, 28, 9, 10, False, 11, "new", 12, 8, True),
    },
    {
        "id": "rival-crossed-count-and-verbosity",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, two clauses at once: the two same-typed numeric
        # entries are stored into each other's slots. Agrees with the spec
        # exactly on the diagonal (count == verbosity) and is wrong everywhere
        # else — the shape of nagini's rival-partial-short-tail (accidentally
        # correct on a slice of the domain, wrong on the slice the failing test
        # uses).
        "module": _swap(
            _swap(_BASE, _ENT["nEstimators"], "    nEstimators := verbose,"),
            _ENT["verbose"], "    verbose := nEstimators }"),
        "refinement": (
            "stores the two same-typed numeric entries into each other's slots. "
            "A faithful real counterpart would be indistinguishable from correct "
            "whenever a caller happened to pass equal values, and wrong "
            "otherwise: it would build an ensemble whose member count is "
            "whatever the reporting level was set to. The failing test sets a "
            "member count and leaves the reporting level at its default, so the "
            "ensemble is built with the wrong number of members and the "
            "assertion on the enlarged member count fails; the existing suite's "
            "configuration read-backs fail too. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from frame clauses F2 (`result.nEstimators = nEstimators`) and "
            "F4 (`result.verbose = verbose`) jointly, on a PROPER "
            "SUB-DOMAIN: each entry is pinned to its OWN argument, so crossing "
            "them satisfies both clauses only where the two arguments are equal. "
            "Refuted at a point where they differ (count 19, verbosity 9) — "
            "distinct from the two constant-substitution rivals, which are "
            "wrong on all of their entry's domain rather than off a diagonal, so "
            "this witness demonstrates a sub-domain neither of theirs does. If "
            "it verified => SPEC-TOO-WEAK (the two numeric entries "
            "interchangeable)."
        ),
        "witness": _witness(19, 29, 10, 11, True, 12, "alt", 13, 9, False),
    },
    {
        "id": "rival-verbosity-nat-truncated",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). A CARRIER-SPECIFIC near-miss on F4 that no
        # existing rival reaches: `verbose - 1 + 1` is truncating subtraction on
        # `Nat`, so it is the identity for every level >= 1 and collapses to 1 at
        # level 0. Every constant/crossed rival above is wrong on a whole
        # entry-domain or off a diagonal; this one is wrong at EXACTLY ONE point
        # of the verbosity binder — the default level, which is the value the
        # failing scenario actually leaves it at. It also probes the carrier trap
        # the audit brief names (Nat truncation being definitionally invisible):
        # here it is observably NOT invisible, and the witness proves it.
        "module": _swap(_BASE, _ENT["verbose"], "    verbose := verbose - 1 + 1 }"),
        "refinement": (
            "stores the verbosity level through a round trip that is the "
            "identity everywhere except at the quietest setting, which it "
            "silently raises by one. A faithful real counterpart would be "
            "indistinguishable from correct for any caller who chose a non-zero "
            "level and wrong for every caller who left the level alone — i.e. "
            "for the default configuration the entire existing suite uses, which "
            "constructs estimators without naming a level and reads the stored "
            "configuration back. Those read-backs fail and the fitting path "
            "reports progress no caller asked for, so it would NOT resolve. A "
            "carried entry the change must leave untouched, broken only at its "
            "default value — the near-miss the blunter constant rival cannot "
            "express."
        ),
        "rationale": (
            "REJECT from frame clause F4 (`result.verbose = verbose`) at a "
            "SINGLE POINT of the verbosity binder: the spec pins the field to "
            "the caller's argument for every level, and truncating subtraction "
            "on the carrier's `Nat` makes this rival agree at every level >= 1 "
            "and disagree at 0. Refuted at level 0 — a point NO other rival "
            "witnesses (every other witness holds the verbosity binder at a "
            "non-zero value, where this rival is ACCIDENTALLY correct, so the "
            "sub-domain it demonstrates is genuinely its own). If it verified "
            "=> SPEC-TOO-WEAK (F4 unconstrained at the default level)."
        ),
        "witness": _witness(21, 31, 12, 13, False, 14, "new", 15, 0, True),
    },
    {
        "id": "rival-strategy-decorated",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). F3 was attacked only by substituting a
        # CONSTANT, which a spec pinning the field to any fixed-length or
        # non-empty property would still reject. This rival instead DERIVES the
        # stored value from the caller's argument — the shape an echo-style wrong
        # impl takes — so it is refuted only by the equality F3 actually states
        # rather than by any weaker property of the string.
        "module": _swap(_BASE, _ENT["behaviour"], '    behaviour := behaviour ++ "x",'),
        "refinement": (
            "stores a DECORATED copy of the strategy string rather than the "
            "caller's value: the argument still reaches the stored "
            "configuration, but not unchanged. A faithful real counterpart would "
            "hand the machinery a strategy name that matches none of the values "
            "the strategy-dependent scoring path dispatches on, so every "
            "estimator would fall through that dispatch regardless of what was "
            "requested, and the existing suite — which constructs estimators "
            "with each strategy value, reads the stored value back and asserts "
            "on the strategy-dependent behaviour and its transition warnings — "
            "fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from frame clause F3 (`result.behaviour = behaviour`) by a "
            "DERIVED value rather than a constant: the stored string is a "
            "function of the caller's argument, so it is non-empty whenever the "
            "argument is and it varies with the argument — it is refuted only by "
            "the EQUALITY F3 states, not by the weaker 'non-constant' or "
            "'non-empty' properties that already refute "
            "rival-constant-strategy. Refuted at a strategy string distinct "
            "from that rival's witness point. If it verified => SPEC-TOO-WEAK "
            "(F3 pinning only the shape of the strategy value, not its "
            "identity)."
        ),
        "witness": _witness(23, 33, 14, 15, True, 16, "old", 17, 5, False),
    },
    {
        "id": "rival-subsample-when-count-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). The two default-pin clauses D1/D2 were
        # attacked only by flipping the pin to the OPPOSITE CONSTANT, which is
        # wrong at EVERY input. So neither existing default-pin rival tests
        # whether the pin is constrained on a proper SUB-DOMAIN: a spec that
        # somehow pinned the field only for the inputs those rivals are checked
        # at would still reject both of them. This rival moves the pin off its
        # default on a proper sub-domain only — feature subsampling is switched
        # on exactly when the requested member count is zero — so it is
        # ACCIDENTALLY correct at every other count, including at every other
        # rival's witness point. The near-miss shape the default-pin lane was
        # missing, and the only rival in the battery refuted at count 0.
        "module": _swap(_BASE, _ENT["bootstrapFeatures"],
                        "    bootstrapFeatures := decide (nEstimators = 0),"),
        "refinement": (
            "switches a configuration flag this estimator never exposes — "
            "per-member feature subsampling — on for exactly the degenerate "
            "member count and leaves it at its default otherwise. A faithful "
            "real counterpart would look correct in ordinary use and would hand "
            "the base machinery a subsampling request no caller made on the "
            "degenerate configuration, so the never-exposed entry is no longer "
            "held at its default across the whole domain. The existing suite "
            "constructs this estimator across configurations and reads the "
            "stored configuration back, so a stored value that depends on the "
            "member count fails those read-backs; and because the entry feeds "
            "how each member is trained, the degenerate path changes behaviour "
            "rather than erroring cleanly. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from default-pin clause D1 "
            "(`result.bootstrapFeatures = false`) on a PROPER SUB-DOMAIN: the "
            "spec pins the field to a constant for EVERY input, and this rival "
            "makes it a function of the member-count binder, so the pin holds "
            "at every count except zero. Refuted at count 0 — a point NO other "
            "rival witnesses (every other witness holds the count binder at a "
            "non-zero value, where this rival is ACCIDENTALLY correct, so the "
            "sub-domain it demonstrates is genuinely its own). This is the "
            "shape rival-enable-feature-subsampling cannot express: that rival "
            "flips the pin to the opposite CONSTANT and is wrong everywhere, so "
            "it is also refuted by any weaker property than D1's equality, "
            "whereas this one is refuted only because D1 is required to hold at "
            "EVERY count. If it verified => SPEC-TOO-WEAK (a never-exposed "
            "entry left free on a sub-domain)."
        ),
        "witness": _witness(0, 35, 16, 17, False, 18, "alt", 19, 11, True),
    },
]


# ===========================================================================
# NAGINI -> LEAN ACCOUNTING.
#
# The two bundles model DIFFERENT surfaces (carrier narrowing, see header): the
# nagini file contracts the DOWNSTREAM fitting decision over a List[int] roster
# (refit_to_size / reuse_and_extend / rebuild_all, with fractional-permission
# read-only inputs); this bundle contracts the UPSTREAM constructor that
# assembles the stored configuration. So no nagini case ports MECHANICALLY;
# what ports is each one's argument, re-aimed at this clause structure.
#
#   nagini case                            -> here
#   -----------------------------------------------------------------------
#   pos-dispatch-inverted-guard            -> pos-reordered-entries          RE-EXPRESSED
#   pos-reuse-lentest-loop                 -> pos-direct-value               RE-EXPRESSED
#   (no sibling)                           -> pos-staged-then-store-flag     ADDED (data-flow reshape)
#   admiss-self-call-warmstart             -> admiss-total-domain            RE-AIMED
#   rival-always-rebuild                   -> rival-drop-exposed-flag        RE-EXPRESSED (same defect, this surface)
#   rival-always-reuse                     -> rival-invert-exposed-flag      RE-EXPRESSED (forces reuse where none was asked)
#   rival-partial-gt1-guard                -> rival-flag-conditioned-on-replacement  RE-EXPRESSED (guard strengthened, one boundary wrong)
#   rival-partial-short-tail               -> rival-crossed-count-and-verbosity      RE-EXPRESSED (accidentally correct on a diagonal)
#   rival-frame-mutate-existing-dispatch   -> (none)                         VACUOUS (no permission surface)
#   rival-frame-mutate-existing-reuse      -> (none)                         VACUOUS (no permission surface)
#   (no sibling)                           -> rival-invert-replacement-flag  ADDED (frame clause F1)
#   (no sibling)                           -> rival-enable-feature-subsampling ADDED (default pin D1)
#   (no sibling)                           -> rival-enable-oob-scoring       ADDED (default pin D2)
#   (no sibling)                           -> rival-constant-member-count    ADDED (frame clause F2)
#   (no sibling)                           -> rival-constant-verbosity       ADDED (frame clause F4)
#   (no sibling)                           -> rival-constant-strategy        ADDED (frame clause F3)
#   (no sibling)                           -> rival-verbosity-nat-truncated  ADDED BY AUDIT (F4 at its default point)
#   (no sibling)                           -> rival-strategy-decorated       ADDED BY AUDIT (F3 by a DERIVED value)
#   (no sibling)                           -> pos-strategy-append-empty      ADDED BY AUDIT-2 (the only positive the frozen script cannot close)
#   (no sibling)                           -> rival-subsample-when-count-zero ADDED BY AUDIT-2 (default pin D1 on a proper SUB-DOMAIN)
#   AXIOM_TESTS (empty upstream)           -> (none)                         DROPPED (G-AX lane)
#
# 18 lean SPEC cases: 4 soundness, 1 admissibility, 13 uniqueness.
#
# AUDIT RECORD (independent re-derivation; every claim below was rebuilt).
#   * Statement integrity (attack A): all 18 variants' `correct_isolationForestInit`
#     STATEMENT is byte-identical to the frozen file's and every variant's spec
#     view hashes equal to gold's. No case reformats or weakens a hypothesis, and
#     no case's module is the frozen file itself.
#   * Witness discrimination (attack B): every reject witness rebuilt twice by
#     hand — exit 0 against its rival, exit 1 against the frozen solution, the
#     gold-side error being `Tactic `decide` proved that the proposition … is
#     false` in all thirteen. Semantic refutations, no stuck reduction, no
#     missing identifier. No witness binds a hypothesis, so the consistency
#     probe does not apply (0 probes generated).
#   * FORGERY test (attack B'): run on all thirteen. For each, a file differing
#     from the witness ONLY in dropping the `¬` — asserting the frozen solution
#     is CORRECT at the witness point — was built against the frozen solution.
#     All thirteen forgeries ELABORATE (exit 0) where the witness itself FAILS
#     (exit 1). The gold-side exit code therefore carries information about the
#     CLAIM and not merely about the file's shape, which is what rules out the
#     hollow-rejection class (stuck reduction / missing `Decidable` instance /
#     unification failure on an unreduced term) that this corpus has been bitten
#     by elsewhere. Not one of these thirteen is in that class.
#   * Rival non-vacuity (attack C): the two SUB-DOMAIN claims were checked in the
#     direction that can falsify them, by refuting each rival's witness against
#     the OTHER rival's impl. rival-drop-exposed-flag SATISFIES the spec at
#     rival-invert-exposed-flag's flag-OFF point and vice versa (both builds exit
#     1, `decide` reporting the negation false, i.e. the spec HOLDS there), so the
#     two are not the same defect reshaped. rival-flag-conditioned-on-replacement
#     satisfies the spec at rival-drop-exposed-flag's replacement-ON point, and
#     rival-crossed-count-and-verbosity satisfies it on the diagonal
#     (count == verbosity == 7), so each near-miss's claimed sub-domain is real
#     and the witness point is the one that distinguishes it.
#   * PARAMETRICITY claim (P1–P5) demonstrated, and then CORRECTED by a second
#     audit — the absolute form of it was too strong. What holds: substituting a
#     sibling polymorphic field (`maxSamples := contamination`) fails to
#     elaborate with `Type mismatch`, and `maxSamples := (default : Sample)`
#     fails with `failed to synthesize`, both BEFORE the spec is consulted, so
#     no ordinary well-typed rival attacks those five clauses.
#     What does NOT hold: "no well-typed implementation can violate P1–P5".
#     Marking the definition `noncomputable` and storing
#     `Classical.choice (⟨maxSamples⟩ : Nonempty Sample)` elaborates and is
#     ADMITTED by variant_scope (`Classical.choice` is not a banned assumption
#     token) — measured, `variant_problems` returns []. It is nonetheless not
#     shippable, for a reason that is about witnessability rather than proof
#     difficulty: the term is opaque, so `Classical.choice ⟨v⟩ = v` is neither
#     provable nor refutable, a value-level witness fails against the rival
#     exactly as it fails against gold, and a hypothesis-conditioned witness
#     ELABORATES AGAINST BOTH (exit 0 / exit 0) — it discriminates nothing. A
#     rejection no witness can attribute to the spec is what the witness rule
#     exists to exclude, so it is reported, not shipped. Not a spec hole either:
#     the rival is rejected. See the header for the full statement. Their
#     binders are varied across the thirteen reject witnesses regardless.
#   * SPEC-TOO-WEAK probe (attack D): four new wrong impls beyond the shipped set
#     were tried against the frozen spec. None verified. Two were novel enough to
#     be worth shipping and are now cases above (the Nat-truncation near-miss and
#     the derived-string rival); the field-substitution probe is the parametricity
#     demonstration; a local rebinding of an argument before assembly (the closest
#     carrier analogue of a frame WRITE) is rejected too, and its rejection is
#     attributable — the constant-member-count witness elaborates against it.
#     No spec hole was found.
#     A second audit tried SIX more wrong impls, aimed at what the shipped set
#     left unattacked. Each was built twice: once under the frozen proof script
#     and once under a strong combinator (`refine ⟨?_ ×12⟩ <;> first | rfl |
#     simp_all | (cases warmStart <;> simp_all) | omega | decide`), so that a
#     rejection could not be blamed on the frozen script's syntactic tuning.
#     All twelve builds exit 1 — every one is genuinely WRONG, not merely
#     reshaped:
#       - `warmStart := bootstrap`         (C read off a SIBLING Bool argument)
#       - `nEstimators := max nEstimators 1` (F2 wrong at exactly count 0)
#       - `bootstrapFeatures := decide (nEstimators = 0)` (D1 on a sub-domain)
#       - `behaviour := if behaviour = "" then "new" else behaviour` (F3 at one value)
#       - `verbose := verbose % 1000`      (F4 wrong only for large levels)
#       - `oobScore := warmStart && bootstrap` (D2 pinned to a derived value)
#     One was novel enough to ship and is now rival-subsample-when-count-zero:
#     it is the only rival in the battery that breaks a DEFAULT PIN on a proper
#     SUB-DOMAIN rather than at every input, and the only one refuted at count 0.
#     Its sub-domain claim was checked in the falsifying direction — built
#     against a witness at a NON-zero count, exit 1, i.e. the spec HOLDS of it
#     there. No spec hole was found by any of the six.
#   * SPEC-TOO-STRONG probe (attack E): three new CORRECT reshapes were proven
#     against the frozen spec — arithmetic no-ops on two pinned numeric entries
#     (`0 + nEstimators`, `verbose + 0`), the exposed flag routed through a
#     conditional, and a default pin computed (`warmStart && !warmStart`) instead
#     of written as a literal. All three verify (exit 0), the last two needing
#     `cases warmStart <;> simp` because the frozen `rfl` script is tuned to the
#     literal form — which is evidence the spec accepts faithful reshapes and the
#     REJECTIONS above are not merely tactic mismatches. No soundness hole found.
#     A second audit added four more, all verifying: `behaviour ++ ""` (now
#     SHIPPED as pos-strategy-append-empty), `nEstimators.succ - 1`, the exposed
#     flag through a `match`, and `oobScore := bootstrap && !bootstrap`. The
#     `match` reshape is worth recording because it is the one that needed the
#     most work: the frozen script fails on it (`Application type mismatch`), a
#     `refine ⟨?_,…⟩ <;> first | rfl | simp_all | …` combinator ALSO left
#     unsolved goals, and it closes only with `cases warmStart <;> simp` or by
#     splitting the C conjunct out (`refine ⟨?_, rfl, …⟩; cases warmStart <;>
#     rfl`) — both measured at exit 0. So the spec accepts it; the difficulty was
#     the tactic, and it is recorded that way rather than as a hole.
#   * WHY A FOURTH POSITIVE WAS ADDED (the finding behind pos-strategy-append-empty).
#     A second audit measured that all THREE originally-shipped positives are
#     closed by the FROZEN `refine ⟨rfl, …⟩` script unchanged — meaning each is
#     definitionally equal to the frozen assembly, so none of them can detect a
#     spec or proof over-fit to the frozen impl's syntactic form. Before the
#     repair, exactly ONE case in the battery (the admissibility case) required a
#     reproof, and the soundness lane had none. `behaviour ++ ""` is the cheapest
#     reshape that is genuinely NOT definitional: measured, the frozen script
#     FAILS on it (exit 1, `Application type mismatch` at the F3 conjunct) and it
#     verifies once F3's conjunct is reproven by `simp` (exit 0). That pair is
#     what makes it informative where the other three are not.
# ===========================================================================
# AUDIT REPAIR — admiss-total-domain. As ported, this case's `module` was the
# frozen file BYTE-FOR-BYTE, so its pass restated "the frozen artifact verifies"
# (already G-VERIFY's job) rather than probing admissibility, and it would have
# survived any spec change the frozen proof still closed. Now it assembles the
# configuration by case analysis on the discriminating binder, making both
# polarities separately in-domain; measured, the frozen proof script does NOT
# close that shape (exit 1, `Application type mismatch`), so the obligation is
# genuinely reproven at a byte-identical statement (exit 0 with the reproven
# script). See the case for the full argument.
#
# AUDIT REPAIR 2 — admiss-total-domain, strengthened again. The by-cases repair
# above fixed the "module is the frozen file" defect, but what it then tested was
# joint satisfiability on each POLARITY, which is a reshape argument; on a total
# carrier the sharper admissibility question the brief names is whether the
# obligation is unsatisfiable at exactly an F2P-SHAPED INPUT. The case now
# discharges the post-image AT THAT CONCRETE POINT — the exposed flag requested
# ON with sample replacement — as a `have` closed by EVALUATION (`decide`),
# BEFORE closing the frozen obligation verbatim. That `have` is a separate
# obligation about a named point: it cannot be closed by `rfl` and cannot be
# inherited from the frozen script, and if any clause were unsatisfiable there
# `decide` would report the proposition false and the case would FAIL. Measured
# at exit 0 with the `have` in place; the case also still fails under the frozen
# proof body (exit 1), so it remains a genuine reproof rather than a free pass.
#
# RE-EXPRESSED (positives): nagini's positives are a De-Morgan-inverted dispatch
#   and a loop-shape change in the roster copy. The modeled function here is a
#   straight-line record assembly with no dispatch and no loop, so the analogous
#   structurally-different-but-correct reshapes are an entry reorder and the
#   removal of the imperative staging; a third (stage-then-update) was added
#   because it is the reshape most likely to break a proof over-fit to a single
#   record literal. Same argument: a faithful correct impl must verify.
# RE-AIMED (admissibility): nagini's case establishes a read-only fractional
#   permission plus a length precondition on an F2P-shaped roster. This
#   obligation binds NO precondition hypothesis and there is no heap permission,
#   so that probe is vacuous here; re-aimed at joint satisfiability of the
#   twelve-clause post-image on each polarity of the discriminating binder,
#   witnessed by an impl that branches on it and reproves the obligation.
# RE-EXPRESSED (the defect): nagini's #1 rival always rebuilds — the DOWNSTREAM
#   manifestation of "the reuse flag never reaches the fitting decision". Here
#   the same defect is upstream: the flag is never stored from the caller's
#   argument, so it never reaches the base machinery. Same refinement argument
#   (the failing test's member-identity assertion fails), stated at the modeled
#   surface and witnessed at the flag-ON input. Its dual (nagini's
#   rival-always-reuse) becomes the inverted-flag rival, which forces reuse on
#   callers who did not request it.
# RE-EXPRESSED (partial-domain class): nagini's two partial-domain rivals attack
#   a loop bound and a dispatch threshold, neither of which exists here. Their
#   CLASS does: a rival that is accidentally correct on a slice of the domain
#   and wrong on the slice the failing test uses. Two such rivals are shipped —
#   the flag conditioned on the replacement flag (wrong only where reuse is
#   requested without replacement, which is exactly the failing test's
#   configuration) and the two crossed numeric entries (correct only on the
#   diagonal). Each carries a witness at the point that distinguishes it from
#   the blunter constant/drop rivals, so no rival's rationale claims a
#   sub-domain the manifest does not demonstrate.
# FRAME-MUTATION (rival-frame-mutate-existing-dispatch / -reuse): VACUOUS on
#   this backend. Those two nagini rivals write through a half-permission
#   reference to the read-only roster and are rejected by the PERMISSION SYSTEM.
#   Lean is referentially transparent: the inputs are immutable values, there is
#   no heap, no aliasing and no fractional permission, so there is no read-only
#   input for a rival to overwrite and no permission judgement to violate. The
#   class has no carrier analogue and NO substitute was fabricated. (The frame
#   is still DEFENDED here — by the value clauses F1–F4 and the default pins
#   D1/D2 — and those are what the frame rivals above attack.)
# DIVERGENCE: genuinely VACUOUS on this backend, and there was nothing to port:
#   the nagini sibling carries no diverge-* / nonterm-* / weak-diverge case.
#   Independently, `implementation_isolationForestInit` is a total Lean `def`, so
#   a diverging implementation cannot be written at all — unlike velvet under
#   `loom.semantics.termination "partial"`, where a non-terminating impl
#   satisfies every clause vacuously and the frozen spec ADMITS the rival
#   (the corpus-wide termination-semantics finding). Not a known hole here; no reject case written,
#   none claimed dropped.
# UNGROUNDED-ORACLE ECHO: N/A, as upstream. Every clause pins a field either to
#   one of the function's own arguments or to a constant; there is no answer-key
#   term a wrong impl could echo, and the cheapest correct impl still has to
#   store each argument, which the positives cover.
# NOT ATTACKABLE (clauses P1–P5, the five polymorphic parameters): enforced by
#   PARAMETRICITY, not merely by the postcondition. Each of those fields has a
#   universally-quantified type whose only inhabitant in scope is the
#   corresponding argument — no constant, no coercion, no same-typed sibling
#   field (the five type variables are pairwise distinct) — so NO well-typed
#   implementation can violate them and there is no rival to write. Reported as a
#   carrier fact, not as a dropped case: writing one would require a banned
#   escape hatch. DEMONSTRATED, not merely asserted: substituting one of these
#   fields with a sibling polymorphic argument (`maxSamples := contamination`)
#   fails to ELABORATE with `Type mismatch`, i.e. it is rejected by the
#   type-checker before the spec is consulted at all, which is why it cannot be
#   shipped as a reject case (a case must be a well-formed variant that the
#   verifier rejects, not one Lean refuses to read). Their binders are still
#   VARIED across the reject witnesses so the battery holds no binder fixed.
#   NOTE for the coverage reporter: it lists clauses 5/6/7/8/10 (the P1–P5
#   conjuncts) as unreferenced by any reject rationale. That is correct as
#   measured and expected by construction — those are exactly the five clauses no
#   well-typed rival can violate, so the finding is advisory here, not a gap a
#   rival could close.
#
# CLAUSE / BINDER / POINT COVERAGE. Twelve independent conjuncts. The seven
#   attackable ones are each attacked: C by rival-drop-exposed-flag (flag ON),
#   rival-invert-exposed-flag (flag OFF) and rival-flag-conditioned-on-replacement
#   (the no-replacement sub-domain); F1 by rival-invert-replacement-flag; F2 and
#   F4 by rival-constant-member-count, rival-constant-verbosity, jointly by
#   rival-crossed-count-and-verbosity, and F4 again at its DEFAULT point by
#   rival-verbosity-nat-truncated; F3 by rival-constant-strategy (a constant) and
#   by rival-strategy-decorated (a value DERIVED from the argument, so F3's
#   equality is what refutes it rather than a weaker shape property); D1 by
#   rival-enable-feature-subsampling (the pin flipped to the opposite constant,
#   wrong everywhere) and again by rival-subsample-when-count-zero (the pin
#   broken on a proper SUB-DOMAIN, wrong only at count 0); D2 by
#   rival-enable-oob-scoring. P1–P5 are unattackable by any COMPUTABLE
#   well-typed impl (above, with the measured caveat). All TEN input binders take
#   at least two distinct values across the THIRTEEN reject witnesses, which
#   probe THIRTEEN DISTINCT input points, so no binder is held at one value by
#   the battery and no rival is refuted at another's point. The MEANINGFULNESS of
#   that variation was audited rather than counted: for the FIVE rivals whose
#   rationale claims a proper sub-domain, the complementary build was run and the
#   spec HOLDS of the rival at the other rivals' points (see AUDIT RECORD), so
#   the points are distinct in the spec's verdict and not merely distinct
#   spellings. The four positives plus the admissibility case defend all twelve
#   clauses jointly — and of those five, TWO now require a genuine reproof
#   (pos-strategy-append-empty and admiss-total-domain), so the verify lane is no
#   longer entirely inherited from the frozen assembly's form.
#
# WITNESS MECHANICS: the carrier is fully transparent (no opaque callee, no
#   axiom; Bool / Nat / String fields, and the polymorphic parameters
#   instantiated at Nat literals by inference), so each witness states the
#   refutation directly as `¬ problem_spec_… <literals> (implementation_…
#   <literals>)` and closes by `decide` in a file whose proof region has been
#   emptied. No witness binds a hypothesis, so no consistency probe applies and
#   there is no risk of a refutation resting on contradictory assumptions. Every
#   witness was checked with scripts/lean_verify.sh, and independently rebuilt
#   from scratch by two audits: exit 0 against its own rival, exit 1 against the
#   frozen solution with `decide` reporting the proposition false — a real
#   verdict on both sides, never a stuck reduction. Each witness's statement also
#   ANCHORS on `problem_spec_isolationForestInit` (not merely on
#   `implementation_…`), so what it asserts is a violation of the frozen spec
#   rather than a difference between two impls. And each was forgery-tested by
#   dropping its `¬` and rebuilding against the frozen solution: all thirteen
#   forgeries elaborate where the witness fails, so gold's exit code tracks the
#   claim.
# ===========================================================================
AXIOM_TESTS = []
