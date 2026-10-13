"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25973 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, where a case
legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the single
``theorem correct_repeatedEvaluations`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff the variant is in scope AND the file elaborates
with the obligation closed (no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect="reject"`` passes iff the variant is
in scope AND does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a fresh design and
not a translation of its text. The nagini bundle contracts a routine over a
mutable ``SplitSource`` object plus an abstract, unforgeable capability predicate
(the sole grantor of which is a modeled materialiser) and an abstract per-draw
count function; its whole anti-echo design rests on that capability having no
value-level witness. THIS bundle models the same single purely-functional core —
a fixed number of independent evaluations that must each observe the COMPLETE
shared collection, even when the supplying source can only be traversed once —
over a ``List Nat`` collection carrier, with the postcondition GROUNDED directly
in the input collection. Every nagini rival that attacks a behaviour this carrier
still expresses is carried over as an attack on one of the two independent
top-level postcondition clauses; the nagini rivals that attacked object IDENTITY
or heap PERMISSION have no counterpart here and are recorded as such in the
port's ``assessment``, not fabricated.

DEFENDED SURFACE (one obligation, two independent top-level clauses).
``problem_spec_repeatedEvaluations folds oneShot numEvals result`` pins EXACTLY:

  * (C0 count)     ``result.length = numEvals`` — exactly one observation per
    evaluation, no evaluation silently contributing nothing and none contributing
    twice;
  * (C1 complete)  ``∀ s ∈ result, s = folds`` — every observation is the
    COMPLETE collection, element-for-element, in order.

THE BEHAVIOURAL DISCRIMINATOR. ``oneShot`` is an INPUT BINDER that is absent from
the right-hand side of both clauses. That absence is the load-bearing content of
the spec: the observations must be independent of whether the supplying source
can be traversed more than once, so an implementation that consults the source
per evaluation — and therefore observes nothing after the first traversal of a
single-traversal source — is refuted, while one that captures the collection once
up front satisfies both clauses at BOTH values of ``oneShot``. The obligation
carries NO precondition, so both polarities of ``oneShot``, the empty collection,
and ``numEvals = 0`` are all in the domain and all must be handled.

BINDER STRUCTURE (three input binders, all load-bearing, all varied by the reject
witnesses — see the point-spread block just above ``SPEC_TESTS``):

  * ``folds``    — the shared collection. Varied across seven distinct values, of
    three different lengths INCLUDING the empty collection, so no rival is
    refuted only at a fixed collection.
  * ``oneShot``  — the single-traversal flag. Varied over BOTH values: eight
    rivals are refuted at ``true`` (they mishandle a single-traversal source) and
    two at ``false`` (they mishandle a repeatedly-readable one). A battery that probed
    only ``true`` would miss a rival that broke the other polarity — and one such
    rival is shipped here precisely because that gap is otherwise invisible.
  * ``numEvals`` — the evaluation count. Varied over ``0``, ``2`` and ``3``; the
    last-evaluation and first-evaluation rivals need ``3`` to separate "the
    offending evaluation" from "every evaluation", and ``0`` is the domain edge
    the obligation admits (no precondition) which the original port's witnesses
    never evaluated at.

The ten reject witnesses probe NINE distinct input triples (``pts=9``, as the
coverage reporter records): ``weak-truncated-observation`` and
``weak-reversed-observation`` deliberately share the point
``folds=[3,8], oneShot=true, numEvals=2``, because they are refuted there by
DIFFERENT content of the same clause — one by an observation being short, the
other by an observation of the right length being mis-ordered — and holding the
input fixed is what makes those two failure modes comparable rather than
confounded with a change of input.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS here. The nagini sibling holds only
    half permission on its input object's fields, so a rival that WRITES to the
    read-only input to satisfy a postcondition vacuously is a mandatory probe
    there. Lean is referentially transparent: ``folds``/``oneShot``/``numEvals``
    are immutable values, there is no aliasing, no mutable input binder, and no
    read-only cell to overwrite. No substitute probe is fabricated.

  * UNGROUNDED-ORACLE ECHO / CAPABILITY LAUNDERING — VACUOUS here. Both nagini
    rivals of that family (never obtain the capability; obtain it on one object
    and report a value-equal COPY) turn on a token tied to an object REFERENCE
    rather than to a value. This carrier has no reference to launder and no
    opaque answer key to echo: the postcondition relates ``result`` structurally
    to the input collection, so producing each observation from the collection IS
    doing the work, and any implementation that "echoes" the collection into every
    observation is simply CORRECT. Those two rivals are therefore replaced by the
    honest positive controls below, which must verify.

  * DIVERGENCE / NON-TERMINATION — VACUOUS here. ``implementation_*`` is a total
    Lean ``def``, so a non-terminating implementation cannot be written at all
    (on velvet under partial termination semantics this class is a KNOWN SPEC
    HOLE instead; see ``the corpus-wide termination-semantics finding``). The nagini sibling ships
    no such case either.

  * PARTIAL-DOMAIN / COUNT / VALUE — APPLIES, and is where the whole port lands.
    Rivals correct on part of the domain and divergent exactly where the modeled
    behaviour bites: consulting the source per evaluation so a single-traversal
    source is drained (the pre-fix behaviour); the mirror-image polarity slip that
    drains a repeatedly-readable source instead; blanking the FINAL evaluation's
    observation; blanking the FIRST evaluation's observation; truncating every
    observation to a short but non-empty prefix; permuting every observation's
    ORDER while keeping its length and elements; and four count attacks —
    recording NO observation once the source has been consulted, recording one
    observation too MANY, and the two domain edges (``numEvals = 0`` and
    ``folds = []``) that the no-precondition obligation admits.

  * DIVERGENCE — re-derived by AUDIT rather than taken on the port's word, since
    this bundle sets no ``loom.semantics.termination`` option at all (it is a
    plain Lean file: ``import Mathlib`` and a total ``def``, no ``loom`` bundle
    semantics in play, so neither the ``"total"`` nor the ``"partial"``
    disposition applies verbatim). Measured with real builds rather than argued:
    a ``partial def`` self-call rival IS writable and stays in variant scope
    (``variant_problems`` clean), and it is REJECTED (exit 1) — but the rejection
    is not attributable to the spec and no witness can make it so. Two builds:
    the variant fails with ``Tactic `unfold` failed to unfold
    `implementation_repeatedEvaluations``` — a ``partial def`` is opaque to
    definitional unfolding, so the frozen script cannot reduce it — and a witness
    against that rival fails with ```simp` made no progress`` for exactly the same
    reason: nothing can compute the rival's output, so nothing can state a
    concrete refutation of it. A rival whose rejection rests on opacity rather
    than on a clause is precisely the vacuous case this battery's witness
    requirement exists to refuse, so none is shipped. Dropping the ``partial``
    keyword instead makes the self-call fail Lean's own termination check
    (``fail to show termination``), i.e. the carrier refuses to admit a diverging
    total ``def`` at all. That is a demonstrated carrier limit, not a hard
    argument about the spec, and it is recorded as such.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof reduces the frozen ranged ``for``
to ``List.replicate`` through a shape-specific ``rw``, and every rival changes
that shape — so a rejection on its own attributes nothing to the spec. Each
``expect="reject"`` case therefore carries a Lean snippet that unfolds the spec
predicate together with the rival's implementation at one ground input and hands
the resulting closed proposition to ``decide``. Every witness binds NOTHING in
its head — all three inputs are ground literals — so there are no hypotheses
whose joint satisfiability could be in question and no ``witness-inconsistent``
risk.

The witnesses deliberately state NO value equation, and that is a repair the
audit made rather than a stylistic choice: the port's original shape computed the
rival's output into a ``have himpl ... := by simp ...; rfl`` first, which made the
gold-side build fail at the ``rfl`` — on a difference between two implementations'
OUTPUT VALUES, decided before the spec was ever consulted. The forgery test
(attack B′) measured what that cost: the same witness with the ``¬`` DROPPED, i.e.
asserting the frozen solution SATISFIES the spec at the rival's output, failed on
gold with the byte-identical error and so would have been recorded as a
refutation. The shape shipped here fails on gold at the ``decide`` itself, with
``decide`` reporting that the negated spec ``is false`` — the kernel evaluated the
frozen implementation and both clauses and found the spec HOLDS — and the flipped
claim now ELABORATES against gold and FAILS against the rival. The exit code
therefore tracks the CLAIM. See the block above ``_w`` for the measured exit codes
and error lines on both sides.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Resolution requires the newly added regression test AND every previously passing
test in the touched test module. Each reject case's ``refinement`` argues which of
those its faithful real counterpart breaks: four of the six rivals make some
evaluation observe an EMPTY collection, and an evaluation with an empty
observation aggregates over an empty set of per-split results, which is exactly
the reported ``IndexError``; the polarity-slip rival keeps the newly added
configuration working but converts every previously-passing configuration into
that same empty-observation failure; and the truncation rival raises nothing at
all, instead changing the outcome every previously-passing configuration pins.
In no case would the faithful patch be reported ``resolved``.

AXIOM lane: DROPPED. The nagini sibling carries two ``AXIOM_TESTS`` probes (a
soundness probe and a containment probe for its modeled materialiser). This
bundle axiomatizes nothing — it declares no ``opaque`` callee and consumes no
``axiom``, because the behaviour is modeled deeply — and the axiom lane is G-AX's
job, which this gate ignores.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25973"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each is unique inside Solution.lean (asserted by _swap at
# import time, so the manifest breaks loudly if the frozen solution ever drifts)
# and lies ENTIRELY inside the region it is meant to edit.
# ---------------------------------------------------------------------------

# The whole executable BODY of the implementation, i.e. everything inside
# `-- impl-start`/`-- impl-end` below the signature line. Rivals that keep the
# `Id.run do` shape rewrite this and nothing else.
_I_BODY = """\
  -- Capture the collection into a reusable value once, before any evaluation
  -- runs, so that it can be consulted again regardless of whether its source
  -- supports only a single traversal. `oneShot` is therefore never consulted.
  let shared := folds
  let mut observed : List (List Nat) := []
  for _ in [0:numEvals] do
    observed := observed ++ [shared]
  return observed"""

# The signature line + body, for the one positive control that abandons the
# imperative shape entirely. Still wholly inside the impl region.
_I_SIG = ("    (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : "
          "List (List Nat) := Id.run do\n")
_I_FULL = _I_SIG + _I_BODY

# The whole frozen proof BODY (inside `-- proof-start`/`-- proof-end`), for the
# positive control whose reshaped implementation needs a genuinely different
# proof. The `theorem correct_repeatedEvaluations` STATEMENT is NOT part of this
# anchor, so it stays byte-identical.
_P_BODY = """\
  intro folds oneShot numEvals
  -- Helper: the desugared loop body, generalized over the accumulator, just
  -- appends one copy of `folds` per iteration, i.e. `replicate length folds`.
  have helper : ∀ (xs : List Nat) (acc : List (List Nat)),
      (forIn xs acc (fun _ r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [folds]))) : Id _)
        = acc ++ List.replicate xs.length folds := by
    intro xs
    induction xs with
    | nil => intro acc; show acc = acc ++ List.replicate 0 folds; simp
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn as (acc ++ [folds]) _ : Id _) = _
      rw [ih]
      simp [List.replicate_succ, List.append_assoc]
  -- The implementation reduces to `List.replicate numEvals folds`.
  have key : implementation_repeatedEvaluations folds oneShot numEvals
      = List.replicate numEvals folds := by
    unfold implementation_repeatedEvaluations
    simp only [Id.run, Std.Range.forIn_eq_forIn_range']
    rw [show (do
        let r ← forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [folds]))
        pure r : Id (List (List Nat))) = forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [folds])) from rfl]
    rw [helper]
    simp [Std.Range.size]
  rw [problem_spec_repeatedEvaluations, key]
  refine ⟨by simp, ?_⟩
  intro s hs
  exact List.eq_of_mem_replicate hs"""

# The frozen proof's `intro` line, so the admissibility case can PREPEND a ground
# `have` without touching the theorem statement, the spec view, or any later
# tactic.
_P_INTRO = "  intro folds oneShot numEvals"


# ---------------------------------------------------------------------------
# Witness scaffold. Unfold the spec predicate and the rival's implementation at
# a ground input and let `decide` settle the resulting closed proposition.
# Nothing is bound in the head, so there is no hypothesis to be inconsistent.
#
# WITNESS SHAPE, and why it is this one rather than the obvious one (AUDIT).
# The natural way to write these is to compute the rival's output into a
# `have himpl : implementation_... = <literal> := by simp ...; rfl`, rewrite with
# it, and `decide` the ground conjunction. Every such witness passes the gate's
# two builds here — it elaborates against its rival (exit 0) and fails against
# the frozen solution (exit 1). But the two builds were measured, and the FAILURE
# WAS IN THE WRONG PLACE. Against the frozen solution that shape dies inside the
# `have`, at the `rfl`:
#
#   error: Tactic `rfl` failed: The left-hand side
#     pure [[1], [1]]
#   is not definitionally equal to the right-hand side
#     [[1], []]
#
# i.e. the build fails because the frozen implementation's OUTPUT VALUE is not
# the rival's output value — a claim about a DIFFERENCE BETWEEN TWO IMPLS, which
# is decided before the spec predicate is ever consulted. The forgery test (attack
# B′) shows what that costs: taking that same witness and DROPPING THE `¬`, so it
# asserts the frozen solution SATISFIES the spec at the rival's output — the exact
# opposite of a refutation — fails on the frozen solution with the
# byte-identical `rfl` error (measured: exit 1, same first error line) while
# elaborating against the rival (exit 0). That forgery therefore clears both
# halves of the gate's check and would have been recorded as `rejected`. The
# gold-side exit code carried information about the output VALUE, not about the
# claim, and a value difference is not a violation.
#
# So the refutation is stated with NO value equation: unfold the spec predicate
# and the impl together and hand the whole closed proposition to `decide`. Then
# the only thing the build can fail on is the CLAIM. Measured on all rivals in
# this battery (12 builds): the witness elaborates against its rival (exit 0) and
# against the frozen solution fails at the `decide` itself, with
#
#   error: Tactic `decide` proved that the proposition
#     ¬((List.length do ... ) = 2 ∧ ...) is false
#
# — the kernel evaluated the frozen implementation, evaluated both clauses, and
# reports that the spec HOLDS there. That is a semantic refutation of the concrete
# claim. And the forgery now flips with the claim: dropping the `¬` ELABORATES
# against the frozen solution (exit 0, measured on all six) and FAILS against the
# rival (exit 1) — the exact mirror, so the exit code tracks the claim rather than
# a shape mismatch. No stuck-reduction screen is tripped on either side (no
# `did not reduce to isTrue`, no `Dependent elimination failed`, no missing
# `Decidable`, no `forIn Lean.Loop.mk` unification failure — checked in the logs),
# so `decide` really does reduce on this carrier and gold can serve as the second
# subject without a `witness_reference`.
# ---------------------------------------------------------------------------
def _w(folds, one_shot, num_evals, observed, clause):
    args = f"{folds} {one_shot} {num_evals}"
    return (
        f"-- Refutation of ({clause}) at folds={folds}, oneShot={one_shot}, "
        f"numEvals={num_evals}: the rival observes {observed} there, which the\n"
        "-- spec's two clauses reject. Stated with no value equation, so the only\n"
        "-- thing the build can fail on is the claim itself (see the block above).\n"
        f"example : ¬ problem_spec_repeatedEvaluations {args}\n"
        f"    (implementation_repeatedEvaluations {args}) := by\n"
        "  simp only [problem_spec_repeatedEvaluations,\n"
        "    implementation_repeatedEvaluations, Id.run,\n"
        "    Std.Range.forIn_eq_forIn_range', Std.Range.size]\n"
        "  decide\n")


# ---------------------------------------------------------------------------
# POINT SPREAD of the reject witnesses (pts=6, all three input binders varied):
#
#   id                          folds    oneShot  numEvals  clause attacked
#   --------------------------  -------  -------  --------  ---------------
#   weak-consult-per-eval       [1]      true     2         C1 (complete, empty)
#   weak-polarity-slip          [5, 7]   false    2         C1 (complete, empty)
#   weak-last-eval-blank        [4, 9]   false    3         C1 (complete, empty)
#   weak-first-eval-blank       [6]      true     3         C1 (complete, empty)
#   weak-truncated-observation  [3, 8]   true     2         C1 (complete, SHORT)
#   weak-skip-after-first       [2, 3]   true     2         C0 (count, UNDER)
#   weak-reversed-observation   [3, 8]   true     2         C1 (complete, ORDER)
#   weak-extra-observation      [7]      true     2         C0 (count, OVER)
#   weak-zero-evals-edge        [4]      true     0         C0 at numEvals = 0
#   weak-empty-collection-edge  []       true     2         C0 at folds = []
#
# `folds` takes seven distinct values over three lengths (including the EMPTY
# collection); `oneShot` takes BOTH values (8 rivals at `true`, 2 at `false`);
# `numEvals` takes 0, 2 and 3. No binder is held at a single value across the
# battery, so no rival that mishandled exactly one input could slip through
# unprobed.
#
# The C1 attackers are not interchangeable, and the last four were ADDED BY AUDIT
# because each closes a direction the original six left unattacked — every one of
# them was first written as a probe against the frozen spec (attack D) and rejected
# by it, so each is a measured rival and not a decorative one:
#
#   * four of the original C1 attackers are refuted by an observation being
#     EMPTY, so on their own they leave `∀ s ∈ result, s = folds`
#     indistinguishable from "no observation is empty".
#     `weak-truncated-observation` is refuted only by an observation being SHORT
#     but non-empty, which separates the clause from "non-empty".
#   * `weak-reversed-observation` is refuted only by ORDER: its observations are
#     non-empty and have the RIGHT LENGTH and the right multiset of elements, so
#     it survives every property the other five C1 attackers test. `s = folds` is
#     list equality, which is ordered, and nothing else in the battery pinned that.
#   * `weak-skip-after-first` attacks C0 only from BELOW (too few observations).
#     `weak-extra-observation` attacks it from ABOVE — one observation too many,
#     every one of them the complete collection, so C1 holds and only the count
#     is wrong. A spec asserting `result.length ≥ numEvals` would admit it, and
#     without it the battery's only C0 evidence is one-sided.
#   * `weak-zero-evals-edge` and `weak-empty-collection-edge` probe the two
#     DOMAIN EDGES the docstring claims are in scope (the obligation carries no
#     precondition, so `numEvals = 0` and `folds = []` must both be handled) but
#     which no original witness ever evaluated at: every original point had
#     numEvals ∈ {2,3} and a non-empty collection. Each rival is CORRECT
#     everywhere except its edge, so it is refuted only there.
# ---------------------------------------------------------------------------

SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_repeatedEvaluations` statement byte-identical and adds no
    # axiom, lemma or assumption token.
    # =====================================================================
    {
        "id": "pos-per-eval-local",
        "kind": "soundness",
        "expect": "verify",
        # Ports nagini's pos-control-local-reshape: compute the value to be
        # recorded into a typed local FIRST, then record it. Same values, one more
        # binding in the loop body. Definitionally the frozen body, so the frozen
        # proof still closes verbatim. (Checked: real build.)
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture the collection into a reusable value once, up front, then\n"
            "  -- bind the value each evaluation observes into a local before\n"
            "  -- recording it. `oneShot` is never consulted.\n"
            "  let shared := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  for _ in [0:numEvals] do\n"
            "    let seen : List Nat := shared\n"
            "    observed := observed ++ [seen]\n"
            "  return observed"),
        "rationale": "correct reshape: the value each evaluation observes is bound "
                     "into a typed local before being recorded, so the loop body "
                     "has a different shape but computes the SAME observation on "
                     "every input — C0 (count) and C1 (complete) both still hold at "
                     "both values of oneShot, so it must verify, else "
                     "SPEC-TOO-STRONG. Definitionally the frozen body, so the "
                     "frozen proof closes unchanged; statement byte-identical, no "
                     "new axiom/lemma. Ports nagini's pos-control-local-reshape "
                     "(there: compute the per-round count into a typed local "
                     "before appending).",
    },
    {
        "id": "pos-direct-construction",
        "kind": "soundness",
        "expect": "verify",
        # A genuinely DIFFERENT algorithmic shape: abandon the accumulator loop
        # and construct the whole observation sequence directly. Needs a real
        # re-proof, which is authored below inside the proof region only.
        # (Checked: real build.)
        "module": _swaps(
            _BASE,
            (_I_FULL,
             "    (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : "
             "List (List Nat) :=\n"
             "  -- Build the whole observation sequence at once: one copy of the\n"
             "  -- complete collection per evaluation. Nothing is consumed as the\n"
             "  -- evaluations proceed, so `oneShot` is never consulted.\n"
             "  List.replicate numEvals folds"),
            (_P_BODY,
             "  intro folds oneShot numEvals\n"
             "  unfold problem_spec_repeatedEvaluations "
             "implementation_repeatedEvaluations\n"
             "  refine ⟨by simp, ?_⟩\n"
             "  intro s hs\n"
             "  exact List.eq_of_mem_replicate hs"),
        ),
        "rationale": "a second, structurally DIFFERENT correct shape: the "
                     "observation sequence is constructed directly rather than "
                     "accumulated one evaluation at a time. Observationally equal "
                     "to the frozen implementation on every input, so C0 and C1 "
                     "both hold and it must verify, else SPEC-TOO-STRONG. The "
                     "proof region is re-authored honestly for the new shape (the "
                     "length clause by `simp`, the completeness clause from "
                     "membership in a constant sequence); the "
                     "`correct_repeatedEvaluations` STATEMENT is byte-identical "
                     "and no axiom, lemma or assumption token is added. Ports "
                     "nagini's pos-control-assert-shape (there: a second correct "
                     "shape adding discharged in-region assertions; here the "
                     "second shape is the non-accumulating construction, since "
                     "there is no assertion vocabulary on this carrier).",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE at a normal,
    # newly-tested-shaped input, else the modeled behaviour would be
    # unachievable there (the analogue of PRECOND-TOO-STRONG). The frozen
    # obligation carries no precondition, so the nagini
    # "construct a representative in-domain input and confirm the modeled
    # materialiser admits it" case re-expresses as: discharge the spec predicate
    # BY EVALUATION at that representative input as a `have`, then close the
    # frozen obligation verbatim.
    # =====================================================================
    {
        "id": "admiss-single-traversal-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  -- The obligation is satisfiable at a representative input of the\n"
            "  -- newly-tested shape: a two-item collection supplied by a\n"
            "  -- single-traversal source, consulted by three evaluations.\n"
            "  have _admissible : problem_spec_repeatedEvaluations [0, 1] true 3\n"
            "      (implementation_repeatedEvaluations [0, 1] true 3) := by\n"
            "    have himpl : implementation_repeatedEvaluations [0, 1] true 3\n"
            "        = [[0, 1], [0, 1], [0, 1]] := by\n"
            "      simp [implementation_repeatedEvaluations, Id.run,\n"
            "        Std.Range.forIn_eq_forIn_range', Std.Range.size]\n"
            "      rfl\n"
            "    rw [problem_spec_repeatedEvaluations, himpl]\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged BY EVALUATION at a "
                     "representative input of the newly-tested shape — a "
                     "two-item collection, a SINGLE-TRAVERSAL source "
                     "(oneShot = true, the reported configuration), and three "
                     "evaluations — as a `have`, after which the frozen "
                     "obligation is closed verbatim. It must verify: if the "
                     "conjunction of C0 and C1 were unsatisfiable at exactly a "
                     "normally-tested input the spec would be vacuous there, the "
                     "analogue of PRECOND-TOO-STRONG. Nothing is assumed: no new "
                     "declaration, the ground instance is a `have` prepended "
                     "inside the existing tactic body, and the theorem statement "
                     "is byte-identical. Ports nagini's admiss-oneshot-input "
                     "(there: build a representative single-traversal source and "
                     "confirm the modeled materialiser's domain admits it).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real counterpart would NOT be reported resolved, and
    # (b) a witness pinning the violation at one concrete input.
    # =====================================================================

    # ---- the modeled behaviour itself: consult the source per evaluation ----
    {
        "id": "weak-consult-per-eval",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behaviour: no up-front capture. The source is consulted
        # inside each evaluation, so a single-traversal source is drained by the
        # first one and every later evaluation observes nothing.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Consult the source inside each evaluation instead of capturing\n"
            "  -- the collection up front.\n"
            "  let mut remaining := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  for _ in [0:numEvals] do\n"
            "    observed := observed ++ [remaining]\n"
            "    if oneShot then\n"
            "      remaining := []\n"
            "  return observed"),
        "refinement": "this is exactly the behaviour the modeled routine is "
                      "required NOT to have: the collection is re-read from the "
                      "source once per evaluation, so a source that supports only "
                      "a single traversal yields the complete collection to the "
                      "first evaluation and nothing to any later one. A faithful "
                      "real counterpart therefore leaves every evaluation after "
                      "the first with an empty set of per-split results to "
                      "aggregate, which is the reported IndexError; the newly "
                      "added regression test — whose entire assertion is that the "
                      "call completes without raising — still FAILS, so the "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from C1 (complete): the spec pins every observation "
                     "to the whole collection `folds`, with `oneShot` absent from "
                     "the right-hand side, but this rival's observations after the "
                     "first are empty whenever `oneShot = true`. Refuted at "
                     "folds=[1], oneShot=true, numEvals=2, where the second "
                     "observation is `[]` and so violates the ∀-quantified "
                     "clause. Ports nagini's partial-domain-prepatch-oneshot "
                     "(correct at a single round, divergent from two rounds on).",
        "witness": _w("[1]", "true", 2, "[[1], []]", "C1 complete"),
    },

    # ---- the mirror-image polarity slip ----
    {
        "id": "weak-polarity-slip",
        "kind": "uniqueness",
        "expect": "reject",
        # Captures for a single-traversal source but converts a repeatedly-readable
        # source into a single-traversal one before the evaluations begin — the
        # exact opposite polarity. Correct on `oneShot = true`, wrong on `false`.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture only when the source is single-traversal; otherwise\n"
            "  -- consume the source as the evaluations proceed.\n"
            "  let mut remaining := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  for _ in [0:numEvals] do\n"
            "    observed := observed ++ [remaining]\n"
            "    if !oneShot then\n"
            "      remaining := []\n"
            "  return observed"),
        "refinement": "the faithful real counterpart handles the newly reported "
                      "configuration correctly while converting a "
                      "repeatedly-readable source into a single-traversal one "
                      "before the evaluations start. So the new regression test "
                      "would pass, but EVERY previously passing configuration in "
                      "the same test module supplies a repeatedly-readable source, "
                      "and each would then leave every evaluation after the first "
                      "with an empty set of per-split results to aggregate — the "
                      "same reported IndexError. Resolution requires the "
                      "previously passing tests to keep passing, so the faithful "
                      "patch does NOT resolve. This rival exists because "
                      "`oneShot = false` is otherwise never probed: the "
                      "obligation carries no precondition, so both polarities are "
                      "in the domain, and a battery that only ever refuted at "
                      "`true` would let this one through.",
        "rationale": "REJECT from C1 (complete) on the OTHER polarity of the "
                     "`oneShot` binder: the spec's right-hand side does not "
                     "mention `oneShot` at all, so the observations must be the "
                     "complete collection for `false` just as for `true`. Refuted "
                     "at folds=[5,7], oneShot=false, numEvals=2, where the second "
                     "observation is `[]`. No nagini counterpart — nagini's "
                     "modeled materialiser fixes the reusable facet to True, so "
                     "this sub-domain is not expressible there; it is added here "
                     "for `oneShot` binder coverage.",
        "witness": _w("[5, 7]", "false", 2, "[[5, 7], []]", "C1 complete"),
    },

    # ---- fence-post: the FINAL evaluation observes nothing ----
    {
        "id": "weak-last-eval-blank",
        "kind": "uniqueness",
        "expect": "reject",
        # Captures correctly and is right on every evaluation except the LAST,
        # whose observation is blanked.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture the collection up front, but record nothing for the\n"
            "  -- final evaluation.\n"
            "  let shared := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  for i in [0:numEvals] do\n"
            "    if i + 1 = numEvals then\n"
            "      observed := observed ++ [([] : List Nat)]\n"
            "    else\n"
            "      observed := observed ++ [shared]\n"
            "  return observed"),
        "refinement": "a fence-post slip in which the final evaluation is run "
                      "against an empty collection instead of the complete one. "
                      "Its faithful real counterpart aggregates over an empty set "
                      "of per-split results on that last evaluation, which is the "
                      "reported IndexError, and the newly added regression test "
                      "asserts precisely that the call completes without raising. "
                      "So the faithful patch does NOT resolve. Ports nagini's "
                      "partial-domain-last-round-zero.",
        "rationale": "REJECT from C1 (complete) on the sub-domain "
                     "`i = numEvals - 1`: the rival satisfies C0 (the count is "
                     "right) and agrees with the frozen implementation on every "
                     "earlier evaluation, so it is a NEAR-MISS and is refuted at "
                     "its own distinguishing point — numEvals=3, where two "
                     "observations are correct and only the third is blank "
                     "(folds=[4,9], oneShot=false). Ports nagini's "
                     "partial-domain-last-round-zero.",
        "witness": _w("[4, 9]", "false", 3, "[[4, 9], [4, 9], []]", "C1 complete"),
    },

    # ---- the FIRST evaluation observes nothing ----
    {
        "id": "weak-first-eval-blank",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror near-miss: correct on every evaluation except the FIRST.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture the collection up front, but record nothing for the\n"
            "  -- first evaluation.\n"
            "  let shared := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  for i in [0:numEvals] do\n"
            "    if i = 0 then\n"
            "      observed := observed ++ [([] : List Nat)]\n"
            "    else\n"
            "      observed := observed ++ [shared]\n"
            "  return observed"),
        "refinement": "the opposite fence-post: the collection is captured one "
                      "evaluation too late, so the first evaluation runs against "
                      "an empty collection. Its faithful real counterpart "
                      "aggregates over an empty set of per-split results on the "
                      "very first evaluation — the reported IndexError, raised "
                      "before any later evaluation can compensate — so the newly "
                      "added regression test still FAILS and the faithful patch "
                      "does NOT resolve.",
        "rationale": "REJECT from C1 (complete) on the sub-domain `i = 0`. This is "
                     "a DIFFERENT near-miss from weak-last-eval-blank — it agrees "
                     "with the frozen implementation on a different part of the "
                     "domain (all evaluations but the first, rather than all but "
                     "the last) — so it gets its own distinguishing witness: "
                     "folds=[6], oneShot=true, numEvals=3, where the FIRST "
                     "observation is blank and the last two are correct, the exact "
                     "mirror of the previous case's point. Ports nagini's "
                     "off-value-round0 (a first-round value slip), re-expressed as "
                     "a first-evaluation blank so that the refinement argument is "
                     "real rather than thin: over-observing has no faithful "
                     "counterpart that fails, while a blank first observation "
                     "reproduces the reported failure exactly.",
        "witness": _w("[6]", "true", 3, "[[], [6], [6]]", "C1 complete"),
    },

    # ---- C1 element-wise: a SHORT but NON-EMPTY observation ----
    {
        "id": "weak-truncated-observation",
        "kind": "uniqueness",
        "expect": "reject",
        # Every other C1 attacker blanks an observation to `[]`, so all four are
        # refuted by the observation being EMPTY. This rival keeps every
        # observation non-empty and merely SHORT, so it is refuted only by the
        # element-wise content of C1 — the part of the clause the rest of the
        # battery never separates from "non-empty".
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture the collection up front, but let each evaluation observe\n"
            "  -- only the leading part of it rather than the whole collection.\n"
            "  let shared := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  for _ in [0:numEvals] do\n"
            "    observed := observed ++ [shared.take 1]\n"
            "  return observed",
        ),
        "refinement": "the faithful real counterpart hands every evaluation a "
                      "strictly SMALLER part of the supplied collection instead of "
                      "all of it. Nothing raises — every observation is non-empty, "
                      "so the aggregation step always has something to aggregate, "
                      "and the newly added regression test (which asserts only that "
                      "the call completes) would PASS. But every previously passing "
                      "configuration in the same test module pins the selected "
                      "features and the scores that follow from aggregating over the "
                      "COMPLETE supplied collection, and aggregating over a proper "
                      "part of it changes those. Resolution requires those tests to "
                      "keep passing, so the faithful patch does NOT resolve. This is "
                      "the one rival whose real counterpart fails LOUDLY on the old "
                      "tests rather than on the new one.",
        "rationale": "REJECT from C1 (complete) on its ELEMENT-WISE content, not on "
                     "emptiness: `∀ s ∈ result, s = folds` pins each observation to "
                     "the whole collection element-for-element, and this rival "
                     "satisfies C0 (the count is exact) and keeps every observation "
                     "NON-EMPTY, so it survives every property the other four C1 "
                     "attackers actually test. Refuted at folds=[3,8], "
                     "oneShot=true, numEvals=2, where both observations are `[3]` — "
                     "a strict, non-empty prefix of `[3, 8]`. Added by audit: no "
                     "nagini counterpart (there the per-draw count is a scalar, so "
                     "'short but non-zero' and 'the wrong scalar' coincide), and "
                     "without it the battery's only evidence for C1 is that an "
                     "observation may not be empty.",
        "witness": _w("[3, 8]", "true", 2, "[[3], [3]]", "C1 complete"),
    },

    # ---- the only C0 attack: no observation recorded at all ----
    {
        "id": "weak-skip-after-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Rather than recording a short observation, this rival records NOTHING
        # once a single-traversal source has already been consulted, so the
        # observation sequence is SHORTER than the number of evaluations. Every
        # observation it does record is complete, so C1 holds and only C0 fails.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture the collection up front, but record an observation only\n"
            "  -- while a single-traversal source has not yet been consulted.\n"
            "  let shared := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  for _ in [0:numEvals] do\n"
            "    if !(oneShot && observed.length > 0) then\n"
            "      observed := observed ++ [shared]\n"
            "  return observed"),
        "refinement": "the faithful real counterpart skips the consultation "
                      "entirely for every evaluation after the first when the "
                      "source is single-traversal, so those evaluations produce no "
                      "result at all rather than a short one. The aggregation step "
                      "then runs over an empty collection of per-evaluation "
                      "results, which is the same reported IndexError, and the "
                      "candidate those evaluations were meant to score is never "
                      "scored — so the newly added regression test still FAILS and "
                      "the faithful patch does NOT resolve.",
        "rationale": "REJECT from C0 (count) — the ONLY rival in this battery that "
                     "attacks the length clause rather than the completeness "
                     "clause, which is why it is shipped even though C1 already "
                     "has five attackers: `result.length = numEvals` is an "
                     "INDEPENDENT top-level conjunct, and an implementation that "
                     "silently contributes nothing for some evaluations satisfies "
                     "C1 vacuously on the observations it does record. Refuted at "
                     "folds=[2,3], oneShot=true, numEvals=2, where the sequence "
                     "has length 1. Ports the count-carrying half of nagini's "
                     "(P6) len(counts) == n_iterations clause, which no nagini "
                     "reject case attacked directly.",
        "witness": _w("[2, 3]", "true", 2, "[[2, 3]]", "C0 count"),
    },

    # ---- C1 ORDER: right length, right elements, wrong order (ADDED BY AUDIT) ----
    {
        "id": "weak-reversed-observation",
        "kind": "uniqueness",
        "expect": "reject",
        # Every other C1 attacker is refuted by an observation being EMPTY or
        # SHORT, so all five leave the ORDER of an observation untested. This
        # rival's observations are non-empty, of the exact right LENGTH, and carry
        # exactly the right elements — only in reverse. It is refuted purely by
        # `s = folds` being ordered list equality.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture the collection up front, but let each evaluation observe\n"
            "  -- it in the opposite order.\n"
            "  let shared := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  for _ in [0:numEvals] do\n"
            "    observed := observed ++ [shared.reverse]\n"
            "  return observed"),
        "refinement": "the faithful real counterpart hands every evaluation the "
                      "complete supplied collection but traversed in the opposite "
                      "order. Nothing raises — every observation is non-empty and "
                      "full-length, so the aggregation step always has the right "
                      "number of things to aggregate, and the newly added "
                      "regression test (which asserts only that the call "
                      "completes) would PASS. But the previously passing "
                      "configurations in the same test module pin which candidate "
                      "is chosen, and that is decided by comparing scores "
                      "accumulated in a fixed traversal order over the supplied "
                      "collection; reversing it changes the ordering of the "
                      "per-evaluation results those tests pin. Resolution requires "
                      "the previously passing tests to keep passing, so the "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from C1 (complete) on its ORDER content specifically: "
                     "`∀ s ∈ result, s = folds` is LIST equality, which is "
                     "ordered, and this rival satisfies C0 exactly, keeps every "
                     "observation non-empty, and gets every observation's LENGTH "
                     "and element multiset exactly right — so it survives every "
                     "property the other five C1 attackers actually test "
                     "(emptiness, shortness, count). Refuted at folds=[3,8], "
                     "oneShot=true, numEvals=2, where both observations are `[8,3]` "
                     "rather than `[3,8]`. Added by audit: no nagini counterpart "
                     "(there the per-draw observable is a scalar COUNT, which has "
                     "no order to permute), and without it the spec's use of list "
                     "equality rather than multiset or set equality is unprobed.",
        "witness": _w("[3, 8]", "true", 2, "[[8, 3], [8, 3]]", "C1 complete"),
    },

    # ---- C0 from ABOVE: one observation too many (ADDED BY AUDIT) ----
    {
        "id": "weak-extra-observation",
        "kind": "uniqueness",
        "expect": "reject",
        # `weak-skip-after-first` attacks C0 only from below. This one attacks it
        # from above: the count is one too MANY and every observation is the
        # complete collection, so C1 holds and only C0 fails.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture the collection up front, but seed the observation\n"
            "  -- sequence with one entry before the evaluations begin.\n"
            "  let shared := folds\n"
            "  let mut observed : List (List Nat) := [shared]\n"
            "  for _ in [0:numEvals] do\n"
            "    observed := observed ++ [shared]\n"
            "  return observed"),
        "refinement": "the faithful real counterpart consults the shared "
                      "collection one extra time beyond the evaluations that were "
                      "asked for. Nothing raises and every observation is "
                      "complete, so the newly added regression test would PASS — "
                      "but the previously passing configurations in the same test "
                      "module pin how many times the scoring routine is consulted "
                      "and the aggregate that follows from exactly that many "
                      "per-evaluation results; an extra result changes the "
                      "aggregate and the selection it drives. Resolution requires "
                      "those tests to keep passing, so the faithful patch does "
                      "NOT resolve.",
        "rationale": "REJECT from C0 (count) in the OVER direction, which "
                     "`weak-skip-after-first` (the only other C0 attacker) does "
                     "not reach: that rival records too FEW observations, so "
                     "between them they pin `result.length = numEvals` as an "
                     "equality rather than as a lower or upper bound — a spec "
                     "written `result.length ≥ numEvals` would admit this rival "
                     "and be caught by nothing else in the battery. C1 holds here "
                     "(every observation IS the complete collection), so the "
                     "rejection is attributable to the count clause alone. Refuted "
                     "at folds=[7], oneShot=true, numEvals=2, where the sequence "
                     "has length 3. Added by audit.",
        "witness": _w("[7]", "true", 2, "[[7], [7], [7]]", "C0 count"),
    },

    # ---- DOMAIN EDGE: numEvals = 0 (ADDED BY AUDIT) ----
    {
        "id": "weak-zero-evals-edge",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct at every numEvals >= 1 and wrong ONLY at numEvals = 0, the
        # domain edge the obligation admits (no precondition) but which no other
        # witness in the battery evaluates at.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture the collection up front, but special-case a request for\n"
            "  -- no evaluations by recording one observation anyway.\n"
            "  let shared := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  if numEvals = 0 then\n"
            "    observed := [shared]\n"
            "  else\n"
            "    for _ in [0:numEvals] do\n"
            "      observed := observed ++ [shared]\n"
            "  return observed"),
        "refinement": "the faithful real counterpart is correct for every "
                      "positive number of evaluations and consults the collection "
                      "once anyway when zero evaluations are requested. The newly "
                      "added regression test would PASS (it requests several "
                      "evaluations), but a configuration that selects no features "
                      "performs no evaluation, and this counterpart would score "
                      "and record a candidate for it — changing the outcome the "
                      "previously passing tests in that module pin for the "
                      "degenerate configuration. Resolution requires those to keep "
                      "passing, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from C0 (count) at the DOMAIN EDGE `numEvals = 0`. "
                     "The obligation carries no precondition, so zero evaluations "
                     "is in the domain and `result.length = numEvals` must hold "
                     "there as an equality with 0 — but every other witness in "
                     "this battery evaluates at numEvals ∈ {2,3}, so the edge was "
                     "claimed by the docstring and demonstrated by nothing. This "
                     "rival agrees with the frozen implementation on ALL of "
                     "numEvals ≥ 1, so it is the narrowest near-miss in the "
                     "battery and is refuted only at its own point: folds=[4], "
                     "oneShot=true, numEvals=0, where the sequence has length 1 "
                     "instead of 0. Added by audit.",
        "witness": _w("[4]", "true", 0, "[[4]]", "C0 count"),
    },

    # ---- DOMAIN EDGE: folds = [] (ADDED BY AUDIT) ----
    {
        "id": "weak-empty-collection-edge",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct at every non-empty collection and wrong ONLY when the collection
        # is empty — the other domain edge the obligation admits but which no
        # other witness evaluates at (every other point uses a non-empty `folds`).
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Capture the collection up front, but record no observation at\n"
            "  -- all for an evaluation when the collection has no items.\n"
            "  let shared := folds\n"
            "  let mut observed : List (List Nat) := []\n"
            "  for _ in [0:numEvals] do\n"
            "    if shared.isEmpty then\n"
            "      observed := observed\n"
            "    else\n"
            "      observed := observed ++ [shared]\n"
            "  return observed"),
        "refinement": "the faithful real counterpart treats a supplied collection "
                      "with no items as nothing to do and records no result for "
                      "any evaluation, rather than recording each evaluation's "
                      "(empty) observation. The newly added regression test would "
                      "PASS, since it supplies a non-empty collection — but the "
                      "aggregation step then runs over an empty collection of "
                      "per-evaluation results for the degenerate configuration, "
                      "which is the same reported IndexError, and the "
                      "previously passing tests in that module cover it. "
                      "Resolution requires those to keep passing, so the faithful "
                      "patch does NOT resolve.",
        "rationale": "REJECT from C0 (count) at the DOMAIN EDGE `folds = []`. The "
                     "obligation carries no precondition, so the empty collection "
                     "is in the domain: the spec still demands one observation per "
                     "evaluation there, each equal to `[]`. Every other witness in "
                     "this battery uses a non-empty collection, so this edge was "
                     "claimed by the docstring and demonstrated by nothing — and "
                     "the distinction it pins is real, since `∀ s ∈ result, "
                     "s = folds` is satisfied VACUOUSLY by an empty result, making "
                     "C0 the only clause that catches this rival. It agrees with "
                     "the frozen implementation at every non-empty collection. "
                     "Refuted at folds=[], oneShot=true, numEvals=2, where the "
                     "sequence is empty instead of `[[], []]`. Added by audit.",
        "witness": _w("[]", "true", 2, "[]", "C0 count"),
    },
]
