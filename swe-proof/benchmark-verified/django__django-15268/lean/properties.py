"""G-PBT manifest for django__django-15268 (lean backend).

Ported from the nagini sibling's battery; the adversarial ARGUMENT is carried
over, the mechanics are restated against this backend's carrier.

DEFENDED SURFACE (frozen spec in Solution.lean; see refinement.md / mapping.md):

  problem_spec_canOptimizeAcross (selfKind : Kind) (selfName : String)
                                 (operation : Op) (result : Bool) : Prop
    result = true ↔
      (affectsModel operation selfName = false)                     -- clause A
      ∨ (isAlterTogether operation.ty = true                        -- clause B1
         ∧ operation.ty ≠ kindTag selfKind)                         -- clause B2

  obligation: theorem correct_canOptimizeAcross, universally quantified over
  selfKind / selfName / operation with NO precondition hypothesis.

The decision is a two-legged disjunction: a baseline leg that consults an
opaque per-operation predicate at this operation's own model name, and an
allowance leg that additionally permits a later grouped-option operation of the
OTHER flavour. The nagini sibling's uniqueness lane attacks the same three
places, so the port attacks them here: drop the allowance leg entirely
(pre-patch behavior), keep the allowance but drop the flavour-distinct guard,
grant the allowance to only ONE flavour, ignore the inputs outright, invert the
baseline leg, and feed the baseline leg the wrong name.

CARRIER NOTE — the opaque leg is attackable. `affectsModel` is `opaque`, so no
concrete input DECIDES the spec: `decide` gets stuck on the opaque term and a
rival's violation is not a closed theorem at any literal point. Every reject
witness below therefore CONDITIONS on the carrier rather than computing it —
it fixes `affectsModel <some operation> <some name>` by hypothesis and shows
that on that sub-domain the rival's answer contradicts the spec. Each such
witness carries exactly ONE hypothesis per distinct opaque application (two in
the one case that must separate two different name arguments), so the
assumptions are jointly satisfiable and the refuted input really exists.

Two witnesses condition at an application the SPEC does not itself make, because
the RIVAL is what reaches the predicate there: the wrong-name rival reads it at
the later operation's name, and the normalized-flavour rival reads it at a
rewritten record. In both the hypothesis must name the point the rival actually
consults, or the witness leaves the rival's own leg unconstrained and fails to
elaborate against it (measured: it does). This is a property of attacking an
ARGUMENT position rather than a result, and both were built both ways.

BINDER VARIATION. The seven reject witnesses probe seven distinct input points and
move every input binder of the spec predicate: `selfKind` over both flavours,
`operation.ty` over all three tags, `selfName` and `operation.name` over two
names each and at both equal and unequal to one another, and the opaque
baseline value over both true and false. No binder is held fixed across the
lane, so a rival that mishandled only one of them could not hide.

WHAT DID NOT PORT (carrier narrowing / vacuous classes) — see `assessment` in
the submitted payload for the full accounting:

  * The nagini sibling contracts a SECOND function (a three-operation
    collapse consequence) and carries two cases against it. This bundle models
    only the single decision above — one `theorem correct_*` — so those cases
    have no counterpart here and are omitted rather than fabricated.
  * The two frame/permission-mutation rivals lose their MECHANISM here but not
    their ARGUMENT, and the audit landed the argument as R7 below. The mechanism
    — a store through a read-only fractional reference, rejected for INSUFFICIENT
    PERMISSION rather than for a value mismatch — has no counterpart on this
    carrier: Lean is referentially transparent, the inputs are immutable
    structure values, and there is no permission system to violate. But what
    those rivals were ATTACKING is a value-level claim (normalize the later
    operation's flavour to this one's, so the allowance leg can never fire), and
    that is expressible by rebinding the argument locally. Recording the pair as
    wholly inexpressible understated the carrier; R7 carries the surviving half.
    The SECOND frame rival (on the second modeled function) remains omitted for
    the same reason its siblings are: this bundle models only one decision.
  * There is no divergence / non-termination case in the nagini sibling, and
    none is expressible here regardless: `implementation_canOptimizeAcross` is
    a total Lean `def`.
  * AXIOM_TESTS: dropped. The axiom lane is G-AX's business and this gate
    ignores it (and this bundle declares no consumed callee axiom anyway).

REGION SURGERY. Every variant is built by `_swap` on the frozen source, editing
ONLY text inside the `impl` region and, for the reshaped positives, the `proof`
region. The spec regions are never touched, so `same_spec` holds by
construction and the `theorem correct_canOptimizeAcross` STATEMENT is
byte-identical in every case; only tactic bodies differ. No variant introduces
an axiom, a helper lemma, `sorry`/`admit`/`native_decide`, or weakens the
obligation: each reshaped positive REPROVES the identical statement for its new
impl shape, and all three close with axioms `[propext]` only.
"""
from pathlib import Path

INSTANCE = "django__django-15268"

_DIR = Path(__file__).parent
_BASE = (_DIR / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors. Each lies ENTIRELY inside the region it names and occurs
# exactly once in the frozen source (asserted below, so the manifest breaks
# loudly if Solution.lean ever drifts).
# ---------------------------------------------------------------------------

# The full body of the impl region's `def` (impl region only).
_IMPL = (
    "  baseCanOptimizeAcross selfName operation ||\n"
    "    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))\n"
)

# The full frozen tactic body (proof region only; everything after the `:= by`).
_PROOF = (
    "  intro selfKind selfName operation\n"
    "  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross"
    " baseCanOptimizeAcross\n"
    "  simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq,\n"
    "    Bool.not_eq_eq_eq_not, Bool.not_true]\n"
)

for _a in (_IMPL, _PROOF):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


def _rival(impl):
    """A wrong impl, keeping the frozen tactic body untouched."""
    return _swap(_BASE, _IMPL, impl)


def _reshape(impl, proof):
    """A correct impl of a different shape, with its own closing proof."""
    return _swap(_swap(_BASE, _IMPL, impl), _PROOF, proof)


# ===========================================================================
# POSITIVE CONTROLS  (expect "verify")
# ===========================================================================

# (P1) Ports nagini's branch-reorder positive control. The frozen source folds
# both legs into one boolean disjunction; this variant splits the decision into
# an explicit branch on the baseline predicate, so the allowance leg is
# consulted only on the branch where the baseline leg does not already settle
# it. Observationally identical. Reproved for the new shape by case-splitting on
# the opaque baseline value; axioms [propext].
_POS_BRANCH = _reshape(
    "  if affectsModel operation selfName then\n"
    "    isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind)\n"
    "  else\n"
    "    true\n",
    "  intro selfKind selfName operation\n"
    "  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross\n"
    "  cases h : affectsModel operation selfName <;>\n"
    "    simp only [h, if_true, if_false, Bool.and_eq_true, decide_eq_true_eq,\n"
    "      Bool.false_eq_true, reduceCtorEq] <;> simp\n",
)

# (P2) Ports nagini's "cheapest honest impl" positive control. The
# postcondition's right-hand side is GROUNDED in the arguments (a decidable
# proposition over the two tags and the opaque predicate's boolean value), not
# an opaque answer-key, so transcribing it directly with `decide` is a correct
# fully-grounded implementation rather than an oracle echo. It must verify --
# the postcondition is literally that biconditional -- else the spec is over-fit
# to the disjunction's syntactic FORM (SPEC-TOO-STRONG). It also witnesses that
# there is no WRONG echo available to a rival: every rival below is refutable.
_POS_DIRECT = _reshape(
    "  decide ((affectsModel operation selfName = false) ∨\n"
    "    (isAlterTogether operation.ty = true ∧ operation.ty ≠ kindTag selfKind))\n",
    "  intro selfKind selfName operation\n"
    "  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross\n"
    "  simp only [decide_eq_true_eq]\n",
)

# (P3) ADMISSIBILITY. Ports the intent of nagini's self-call-on-a-fresh-F2P-input
# case. The input shape the reported behavior turns on is a grouped-option
# operation meeting a later grouped-option operation of the OTHER flavour on the
# same model; this variant lifts exactly those two cross-flavour combinations
# into their own match arms answering `true` outright, and routes everything else
# through the frozen decision. That is admissible only if the spec genuinely
# permits the cross-flavour pair UNCONDITIONALLY -- i.e. independently of the
# opaque baseline predicate's value at that point. If the obligation could not be
# closed for this shape, the spec would be rejecting the very input the reported
# behavior is about. Reproved by exhausting both flavours against all three tags;
# axioms [propext].
_POS_ADMISS = _reshape(
    "  match selfKind, operation.ty with\n"
    "  | .unique, .alterIndex => true\n"
    "  | .index, .alterUnique => true\n"
    "  | _, _ =>\n"
    "    baseCanOptimizeAcross selfName operation ||\n"
    "      (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))\n",
    "  intro selfKind selfName operation\n"
    "  obtain ⟨ty, name⟩ := operation\n"
    "  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross"
    " baseCanOptimizeAcross\n"
    "  cases selfKind <;> cases ty <;> simp <;> exact Or.inr ⟨rfl, by decide⟩\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (R1) Baseline leg only -- the pre-patch behavior (== Solution_prepatch.lean's
# decision). Drops clause B entirely.
_RIVAL_BASE_ONLY = _rival("  baseCanOptimizeAcross selfName operation\n")

# (R2) Allowance granted to ANY later grouped-option operation: keeps clause B1,
# drops the flavour-distinct guard B2.
_RIVAL_ANY_TOGETHER = _rival(
    "  baseCanOptimizeAcross selfName operation || isAlterTogether operation.ty\n")

# (R3) Constant `true` -- the maximal over-permission; ignores every binder.
_RIVAL_CONST_TRUE = _rival("  true\n")

# (R4) Half the allowance: clause B1 narrowed from "is a grouped-option
# operation of either flavour" to one specific tag, so the flavour-distinct
# guard survives but is reachable from only one side. A near-miss of R2 -- it
# agrees with the frozen decision on strictly more of the domain -- so it gets
# its own witness at the tag R2's witness cannot reach.
_RIVAL_ONE_FLAVOUR = _rival(
    "  baseCanOptimizeAcross selfName operation ||\n"
    "    (decide (operation.ty = OpType.alterUnique) &&\n"
    "      decide (operation.ty ≠ kindTag selfKind))\n")

# (R5) Wrong argument into the opaque leg: consults the later operation's own
# name instead of this operation's name, so clause A is evaluated at the wrong
# point. Attacks the `selfName` binder specifically.
_RIVAL_WRONG_NAME = _rival(
    "  !(affectsModel operation operation.name) ||\n"
    "    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))\n")

# (R6) Inverted baseline leg: clause A's polarity flipped, so the operation is
# permitted across a later operation exactly when that operation DOES affect the
# same model. Attacks clause A on the sub-domain where clause B cannot cover for
# it (a same-flavour later operation).
_RIVAL_INVERTED_BASE = _rival(
    "  affectsModel operation selfName ||\n"
    "    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))\n")

# (R7) NORMALIZED FLAVOUR. Added by the audit; carries the surviving half of the
# nagini sibling's frame-mutation rivals. Those wrote the later operation's
# flavour to this operation's before deciding, so the flavour-distinct guard B2
# could never fire and a baseline-only decision would look correct. The write
# itself is inexpressible here (immutable values, no permission system), but the
# ARGUMENT is not: rebinding `operation` to a copy whose tag is overwritten with
# this operation's own tag reproduces exactly the same collapse, purely at the
# value level. The decision text that follows is the frozen one CHARACTER FOR
# CHARACTER, so the rejection is attributable solely to the normalization --
# which is what made the nagini original a clean probe.
_RIVAL_NORMALIZED_FLAVOUR = _rival(
    "  let operation := { operation with ty := kindTag selfKind }\n"
    "  baseCanOptimizeAcross selfName operation ||\n"
    "    (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))\n")


# ---------------------------------------------------------------------------
# Refutation witnesses. Each states the spec predicate at ONE concrete input,
# conditioning on the opaque baseline predicate's value at that input (no
# literal input decides it, since the predicate is `opaque`). Every one was
# built both ways: it elaborates against its rival and FAILS on the frozen
# solution, and its hypotheses admit no derivation of `False`.
#
# THE SIMP SET MUST NAME `baseCanOptimizeAcross`, AND THIS IS LOAD-BEARING, NOT
# COSMETIC. Three witnesses below originally omitted it, on the reasoning that
# their RIVAL's impl text does not mention the helper so unfolding it is
# unnecessary. That is true of the rival side and false of the gold side, and it
# silently hollowed those three cases. The frozen impl DOES route clause A
# through `baseCanOptimizeAcross`, so without the unfold the term never reduces
# to `!(affectsModel ...)`, the hypothesis `h` cannot be rewritten into it, and
# `simp` leaves a residual `baseCanOptimizeAcross <name> <op> = <b>` that it
# cannot close FOR EITHER POLARITY. Gold's build then fails no matter what the
# witness claims, so its exit code carries no information about the claim and the
# gate's second half attests to nothing.
#
# Measured, per the audit's forgery test: with the helper omitted, the witness
# and a FORGERY differing from it only in DROPPING the `¬` -- i.e. asserting that
# gold IS correct at that input, which the frozen theorem proves -- both failed on
# gold with the same residual modulo `= true`/`= false`. With the helper named,
# the witness still fails on gold (residual `⊢ False` under a satisfiable
# hypothesis: `simp` reduced the claim and was left needing False) while the
# forgery SUCCEEDS on gold (exit 0). That flip is what makes gold's exit code
# evidence about the claim rather than about the unfold, so the four witnesses
# that always named the helper are genuine discriminators and the three that did
# not now are too. Do not "simplify" the simp set by dropping an argument the
# rival happens not to need.
# ---------------------------------------------------------------------------

# A same-model CROSS-flavour pair, which the allowance leg must permit.
_W_BASE_ONLY = """example (h : affectsModel { ty := OpType.alterUnique, name := "book" } "book" = true) :
    ¬ problem_spec_canOptimizeAcross Kind.index "book"
        { ty := OpType.alterUnique, name := "book" }
        (implementation_canOptimizeAcross Kind.index "book"
          { ty := OpType.alterUnique, name := "book" }) := by
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross
  simp [isAlterTogether, kindTag, baseCanOptimizeAcross, h]
"""

_W_ANY_TOGETHER = """example (h : affectsModel { ty := OpType.alterUnique, name := "book" } "book" = true) :
    ¬ problem_spec_canOptimizeAcross Kind.unique "book"
        { ty := OpType.alterUnique, name := "book" }
        (implementation_canOptimizeAcross Kind.unique "book"
          { ty := OpType.alterUnique, name := "book" }) := by
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross
  simp [isAlterTogether, kindTag, baseCanOptimizeAcross, h]
"""

_W_CONST_TRUE = """example (h : affectsModel { ty := OpType.other, name := "author" } "author" = true) :
    ¬ problem_spec_canOptimizeAcross Kind.index "author"
        { ty := OpType.other, name := "author" }
        (implementation_canOptimizeAcross Kind.index "author"
          { ty := OpType.other, name := "author" }) := by
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross
  simp [isAlterTogether, kindTag, baseCanOptimizeAcross, h]
"""

_W_ONE_FLAVOUR = """example (h : affectsModel { ty := OpType.alterIndex, name := "book" } "book" = true) :
    ¬ problem_spec_canOptimizeAcross Kind.unique "book"
        { ty := OpType.alterIndex, name := "book" }
        (implementation_canOptimizeAcross Kind.unique "book"
          { ty := OpType.alterIndex, name := "book" }) := by
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross
  simp [isAlterTogether, kindTag, baseCanOptimizeAcross, h]
"""

# Two hypotheses, but about two DISTINCT opaque applications: the same later
# operation weighed against two different names. They are jointly satisfiable
# (the predicate is free to answer differently at different names -- indeed that
# is what makes the argument position observable at all), and the gate's
# consistency probe confirms no `False` follows.
_W_WRONG_NAME = """example (h1 : affectsModel { ty := OpType.other, name := "author" } "book" = true)
    (h2 : affectsModel { ty := OpType.other, name := "author" } "author" = false) :
    ¬ problem_spec_canOptimizeAcross Kind.unique "book"
        { ty := OpType.other, name := "author" }
        (implementation_canOptimizeAcross Kind.unique "book"
          { ty := OpType.other, name := "author" }) := by
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross
  simp [isAlterTogether, kindTag, baseCanOptimizeAcross, h1, h2]
"""

# The one witness whose hypothesis is NOT about the operation the spec is stated
# at. The rival normalizes the tag before consulting the baseline leg, so the
# opaque application it actually reaches is at the REWRITTEN record
# (ty := alterUnique, this operation's own tag) while the spec's clause A reads
# the record as given (ty := alterIndex). Fixing the value at the rewritten point
# is what refutes the rival: there clause B holds for the spec (the later
# operation IS of the other flavour) so result=true is demanded, while the rival
# has destroyed the flavour distinction and returns the negated baseline value.
_W_NORMALIZED_FLAVOUR = """example (h : affectsModel { ty := OpType.alterUnique, name := "book" } "book" = true) :
    ¬ problem_spec_canOptimizeAcross Kind.unique "book"
        { ty := OpType.alterIndex, name := "book" }
        (implementation_canOptimizeAcross Kind.unique "book"
          { ty := OpType.alterIndex, name := "book" }) := by
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross
  simp [isAlterTogether, kindTag, baseCanOptimizeAcross, h]
"""

_W_INVERTED_BASE = """example (h : affectsModel { ty := OpType.alterIndex, name := "book" } "book" = false) :
    ¬ problem_spec_canOptimizeAcross Kind.index "book"
        { ty := OpType.alterIndex, name := "book" }
        (implementation_canOptimizeAcross Kind.index "book"
          { ty := OpType.alterIndex, name := "book" }) := by
  unfold problem_spec_canOptimizeAcross implementation_canOptimizeAcross
  simp [isAlterTogether, kindTag, baseCanOptimizeAcross, h]
"""


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-branch-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_BRANCH,
     "rationale": "structurally different but CORRECT impl: the frozen single "
                  "disjunction is split into an explicit branch on the opaque "
                  "baseline predicate, consulting the allowance leg only where the "
                  "baseline leg leaves the answer open. Same function of the same "
                  "binders, so it must satisfy the biconditional postcondition. "
                  "The obligation statement is byte-identical and is REPROVED for "
                  "the new shape (case split on the baseline value; axioms "
                  "[propext]) -- nothing is assumed and no helper lemma is added. "
                  "If this failed, the postcondition would be over-fit to the "
                  "disjunction's syntactic form => SPEC-TOO-STRONG."},
    {"id": "pos-direct-transcription", "kind": "soundness", "expect": "verify",
     "module": _POS_DIRECT,
     "rationale": "the cheapest HONEST impl: the postcondition's right-hand side "
                  "is grounded in the arguments (a decidable proposition over the "
                  "two tags and the opaque predicate's boolean value), NOT an "
                  "ungrounded answer-key, so transcribing it with `decide` is a "
                  "correct fully-grounded implementation and not an oracle echo. "
                  "Must verify, since the postcondition IS that biconditional; "
                  "else SPEC-TOO-STRONG. Reproved by `decide_eq_true_eq` with the "
                  "statement unchanged; axioms [propext]."},
    {"id": "admiss-cross-flavour-branch", "kind": "admissibility",
     "expect": "verify", "module": _POS_ADMISS,
     "rationale": "admissibility of the input shape the reported behavior turns "
                  "on. The obligation is universally quantified with no "
                  "precondition, so the analogue of nagini's fresh-input self-call "
                  "is to make that input a first-class branch: this variant answers "
                  "`true` outright for both cross-flavour combinations "
                  "(unique-vs-index-tagged and index-vs-unique-tagged) and routes "
                  "every other input through the frozen decision. Closing the "
                  "identical obligation for this shape shows the spec permits the "
                  "cross-flavour pair UNCONDITIONALLY -- independently of the opaque "
                  "baseline predicate's value there -- via clause B (B1 ∧ B2). If it "
                  "could not close, the spec would reject the very input the "
                  "reported behavior is about => PRECOND/SPEC-TOO-STRONG. Reproved "
                  "by exhausting both flavours against all three tags; axioms "
                  "[propext]."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "weak-baseline-leg-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BASE_ONLY,
     "witness": _W_BASE_ONLY,
     "refinement": "this is exactly the PRE-patch behavior (the decision recorded "
                   "in Solution_prepatch.lean): the baseline rule with no extra "
                   "allowance at all. A faithful real patch keeping only the "
                   "baseline rule never permits a grouped-option operation to be "
                   "optimized across a same-model later operation of the other "
                   "flavour, so the reported four-operation sequence is not reduced "
                   "to two and all three FAIL_TO_PASS autodetector assertions -- "
                   "which now expect the collapsed two-operation sequence and its "
                   "re-indexed attributes -- still fail. Verify-not-resolve.",
     "rationale": "rejection source: the postcondition's clause B. At a same-model "
                  "cross-flavour input (selfKind=index, operation.ty=alterUnique, "
                  "both names \"book\") with the baseline predicate answering true, "
                  "clause A is false and clause B is true, so the spec demands "
                  "result=true while this rival returns false. The witness fixes "
                  "the opaque baseline value by hypothesis at exactly that point "
                  "(the term is `opaque`, so no literal input decides it) and "
                  "derives the contradiction; it fails on the frozen solution. If "
                  "this verified => SPEC-TOO-WEAK (the cross-flavour allowance "
                  "would be unenforced)."},
    {"id": "weak-any-flavour-allowance", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ANY_TOGETHER,
     "witness": _W_ANY_TOGETHER,
     "refinement": "dropping the flavour-distinct guard lets a grouped-option "
                   "operation be optimized across a same-model later operation of "
                   "the SAME flavour. A faithful patch that omitted that guard "
                   "would reduce two successive same-flavour grouped-option "
                   "operations on one model past each other -- they are ordered "
                   "passes over the same option group, where the first clears the "
                   "group and the second sets it -- so the reduction would drop a "
                   "required intermediate state. The autodetector/optimizer "
                   "invariants in the PASS_TO_PASS set (which pin the exact "
                   "operation sequences produced for ordering, removal and rename "
                   "scenarios) break. Verify-not-resolve.",
     "rationale": "rejection source: the postcondition's clause B2 "
                  "(operation.ty ≠ kindTag selfKind). At a same-model SAME-flavour "
                  "input (selfKind=unique, operation.ty=alterUnique) with the "
                  "baseline predicate answering true, both clause A and clause B "
                  "are false, so the spec demands result=false while this rival "
                  "returns true. The witness conditions on the opaque baseline "
                  "value at that point; it fails on the frozen solution. Note this "
                  "is the mirror of the baseline-leg-only rival: same binder "
                  "values for the names, opposite selfKind, opposite error "
                  "direction. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-one-flavour-allowance", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ONE_FLAVOUR,
     "witness": _W_ONE_FLAVOUR,
     "refinement": "a NEAR-MISS of the any-flavour rival, wrong on strictly less of "
                   "the domain: the allowance is recognised for only one of the two "
                   "flavours of later operation. A faithful patch testing membership "
                   "in one concrete grouped-option flavour instead of the shared "
                   "grouped-option abstraction gets the reported sequence half "
                   "right -- the reduction fires in one direction and not the other "
                   "-- so the four-operation sequence collapses to three rather "
                   "than two and the FAIL_TO_PASS assertions on the exact operation "
                   "list and its re-indexed attributes still fail. "
                   "Verify-not-resolve.",
     "rationale": "rejection source: clause B1 (isAlterTogether operation.ty). "
                  "Because this rival agrees with the frozen decision wherever the "
                  "any-flavour rival's witness probes, it gets its OWN witness at "
                  "the tag that discriminates it: selfKind=unique with "
                  "operation.ty=alterIndex, same model name, baseline predicate "
                  "answering true. There the spec demands result=true (clause B "
                  "holds: the later operation IS grouped-option and of the other "
                  "flavour) while this rival returns false. Moves operation.ty to a "
                  "value no other reject witness holds it at. Fails on the frozen "
                  "solution. If it verified => SPEC-TOO-WEAK (clause B1 would only "
                  "be enforced on one flavour)."},
    {"id": "weak-wrong-name-argument", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_NAME,
     "witness": _W_WRONG_NAME,
     "refinement": "the baseline leg is evaluated at the wrong model name -- the "
                   "later operation's own name rather than this operation's. A "
                   "faithful patch that threaded the wrong name into the "
                   "affects-check would decide reducibility against an unrelated "
                   "model, permitting reductions across operations that really do "
                   "touch this model and forbidding them across operations that do "
                   "not. Both directions corrupt the emitted migration, so the "
                   "PASS_TO_PASS autodetector/optimizer sequence assertions break "
                   "and none of the three FAIL_TO_PASS assertions is reached with "
                   "the expected list. Verify-not-resolve.",
     "rationale": "rejection source: clause A's dependence on the `selfName` "
                  "binder. Attacks the ARGUMENT rather than the result: the "
                  "carrier is opaque, so no value of the predicate is computable, "
                  "but the two calls are separable by hypothesis. The witness pins "
                  "one later operation (ty=other, name=\"author\") against "
                  "selfName=\"book\": the predicate answers true at \"book\" and "
                  "false at \"author\". The spec then demands result=false (clause "
                  "A false since it is evaluated at selfName; clause B false since "
                  "the later operation is not grouped-option) while the rival, "
                  "reading at the wrong name, returns true. This is the ONLY "
                  "witness with selfName ≠ operation.name, which is what makes the "
                  "argument position observable at all. Two hypotheses, but about "
                  "two DISTINCT opaque applications and jointly satisfiable -- no "
                  "`False` follows from them. Fails on the frozen solution. If it "
                  "verified => SPEC-TOO-WEAK (the spec would not pin WHICH model "
                  "the baseline leg consults)."},
    {"id": "weak-inverted-baseline-leg", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERTED_BASE,
     "witness": _W_INVERTED_BASE,
     "refinement": "clause A's polarity is flipped, so the operation is permitted "
                   "across a later operation exactly when that operation DOES "
                   "affect the same model. A faithful patch with this polarity "
                   "error inverts reducibility for every non-grouped-option later "
                   "operation: unrelated operations block reduction and related "
                   "ones permit it, so the optimizer both fails to perform the "
                   "reductions the FAIL_TO_PASS assertions expect and performs "
                   "reductions the PASS_TO_PASS sequence assertions forbid. "
                   "Verify-not-resolve.",
     "rationale": "rejection source: clause A. This is the only reject witness "
                  "that holds the opaque baseline predicate FALSE, which is the "
                  "sub-domain where clause A alone decides the answer. At "
                  "selfKind=index with a same-flavour later operation "
                  "(ty=alterIndex, same name) the allowance leg B is false, so "
                  "with the predicate answering false the spec demands result=true "
                  "while this rival returns false. Varying the baseline value is "
                  "essential: every other witness holds it true, so without this "
                  "case a rival that mishandled only the not-affecting branch "
                  "would verify unnoticed. Fails on the frozen solution. If it "
                  "verified => SPEC-TOO-WEAK."},
    {"id": "weak-normalized-flavour", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NORMALIZED_FLAVOUR,
     "witness": _W_NORMALIZED_FLAVOUR,
     "refinement": "the later operation's flavour is overwritten with this "
                   "operation's own before the decision is taken, so the "
                   "flavour-distinct guard compares a value against itself and can "
                   "never fire -- the decision degenerates to the baseline rule "
                   "while still LOOKING like the full two-legged one. A faithful "
                   "patch that normalised the neighbour it is merely deciding "
                   "about (rather than reading its concrete flavour) would never "
                   "permit the cross-flavour reduction, so the reported "
                   "four-operation sequence is not collapsed to two and the "
                   "FAIL_TO_PASS assertions on the resulting operation list still "
                   "fail; it would additionally corrupt the operation it rewrote. "
                   "Verify-not-resolve.",
     "rationale": "rejection source: clause B2 read at the RIGHT operation. "
                  "Carries the surviving half of the nagini sibling's "
                  "frame-mutation rivals: their store through a read-only "
                  "reference has no counterpart on this carrier (immutable "
                  "values, no permission system), but their ARGUMENT -- normalize "
                  "the neighbour's flavour so the allowance leg cannot fire -- is "
                  "expressible as a local rebind and is exactly this rival. The "
                  "decision text after the rebind is the frozen one character for "
                  "character, so the rejection is attributable solely to the "
                  "normalization. This is the only witness whose hypothesis names "
                  "an opaque application the SPEC does not make: the rival reads "
                  "the predicate at the rewritten record, so the witness fixes it "
                  "there, and at that point the spec demands result=true via "
                  "clause B while the rival returns the negated baseline value. "
                  "One hypothesis, satisfiable. Fails on the frozen solution. If "
                  "it verified => SPEC-TOO-WEAK (the spec would not pin WHICH "
                  "operation's flavour the guard compares)."},
    {"id": "weak-constant-true", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CONST_TRUE,
     "witness": _W_CONST_TRUE,
     "refinement": "always-permit is the maximal over-reduction: a patch whose "
                   "decision unconditionally returns true would allow every "
                   "neighbouring operation pair to be reduced, including "
                   "same-flavour grouped-option pairs and the ordering-sensitive "
                   "sequences the FAIL_TO_PASS assertions pin (ordering changes, "
                   "field removal after the option update, and field rename before "
                   "it). The emitted operation lists would not match any of the "
                   "three expected sequences. Verify-not-resolve.",
     "rationale": "cheap supporting near-miss (ignores every binder). Rejection "
                  "source: the biconditional itself -- both clause A and clause B "
                  "false must force result=false. The witness uses a later "
                  "operation of NEITHER grouped-option flavour (ty=other) so "
                  "clause B is false outright, with the baseline predicate "
                  "answering true so clause A is false too; the spec demands "
                  "result=false and the rival returns true. Probes the `other` tag "
                  "and the \"author\" name, and is the only witness in which no "
                  "clause of the disjunction is satisfiable. Fails on the frozen "
                  "solution. If it verified => SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE -- dropped by design. The axiom lane belongs to G-AX and this gate
# ignores it; this bundle additionally declares no consumed callee axiom (the
# opaque baseline predicate is an A-reference whose boolean value the proof
# reasons about symbolically, with no `_prop` property).
# ===========================================================================

AXIOM_TESTS = []  # type: list
