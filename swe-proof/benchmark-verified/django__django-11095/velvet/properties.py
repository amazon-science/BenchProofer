"""properties.py — G-PBT falsification battery for django__django-11095 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside a
``-- impl-start`` / ``-- impl-end`` region, or inside a ``prove_correct`` tactic
body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and every ``prove_correct <name>`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (two cooperating read-only operations over a sequence of
registration identities, ``List InlineClass``, parametric in a per-entry
admissibility predicate):

  getInlines (declared : List InlineClass) return (out : List InlineClass)
    ensures out = declared

  getInlineInstances (selected : List InlineClass) (declared : List InlineClass)
                     (admissible : InlineClass → Bool) return (result : List InlineClass)
    ensures result = kept admissible selected

``kept admissible xs`` is a total, fully-unfolded pure fold: it keeps, IN
ORDER, exactly those entries of ``xs`` for which ``admissible`` holds. It is
NOT an opaque answer key — the post-image is GROUNDED in the method inputs
(directive 8): ``getInlines`` pins the result to its input ``declared``, and
``getInlineInstances`` pins the result to the admissible-sublist of its input
``selected``. So the cheapest honest impl that satisfies each obligation IS the
correct one; there is no ungrounded-oracle echo to exploit (the ``axioms``
region is empty).

THE CENTRAL DIFFERENTIAL. The load-bearing clause is
``result = kept admissible selected``: the built list is materialised from the
per-request/per-object SELECTION (``selected``, the value the selection hook
yields), NOT from the statically declared set (``declared``). When the two
differ (exactly the sub-domain the failing test exercises: the hook is
overridden to yield ``[]`` / a sublist / a reordering / classes outside
``declared``), an impl that iterates ``declared`` diverges and must be rejected.
That is the pre-image behaviour the fix removes.

BINDER STRUCTURE (read before judging binder coverage). ``getInlineInstances``
has three input binders. ``selected`` and ``admissible`` are both load-bearing:
the result depends on the selection sequence AND on which of its entries pass
the admissibility test. ``declared`` is DELIBERATELY free in this obligation —
it is the statically declared set the pre-image iterated; it exists in the
surface only so the central pre-image rival (materialise from ``declared``) is
expressible while the spec stays byte-identical. No rival can be wrong in a way
distinguished ONLY by ``declared``: an impl that returns ``kept admissible
selected`` for every ``declared`` VERIFIES (correctly — the spec is independent
of it), and one that lets ``declared`` leak into the result is caught by the
clause whenever ``selected ≠ declared``. The reject witnesses below vary
``selected``, ``declared`` and ``admissible`` across their concrete input points
(varying an input is free and keeps the coverage tool from flagging a pinned
binder), while the DISCRIMINATION comes from the result diverging from
``kept admissible selected`` (or, for the ``getInlines`` rival, from
``declared``).

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY, and they must not all be cheap. A
    structurally different but behaviourally identical impl must still verify,
    else the spec is SPEC-TOO-STRONG on the shape of the impl. Note (audit) that
    the two minimal reshapes — the loop collapsed to the closed form the
    post-image names, and an identity ``let`` rebinding for the selection hook —
    are honest but WEAK: the first is the post-image verbatim (closes at
    reflexivity) and the second is definitionally the frozen body. They are kept
    as controls, and each obligation additionally carries a positive whose
    equality to the post-image is a THEOREM: ``pos-materialize-filter``
    (``List.filter``, needing a bridging induction), ``pos-materialize-forward-
    loop`` (opposite iteration order, opposite accumulation side, ``take``-based
    invariant, needing an append/split lemma), and ``pos-select-branch`` (a live
    branch on the declared set). For each of those three, a bare ``loom_solve``
    was observed to leave the obligation OPEN, which is what makes them
    load-bearing rather than decorative.
  * ADMISSIBILITY — neither method carries a ``require`` clause, so the "a
    normal input satisfies the precondition" probe is not where the risk sits.
    The residual risk is that the post-image is DEGENERATE at the interesting
    point — that ``kept`` does not actually distinguish an all-admissible
    non-empty selection from a fully-filtered one, nor keep the empty selection
    empty. ``admiss-grounded`` discharges an in-region assert pinning all three
    at concrete inputs; the surrounding impl is kept verbatim so the method's
    own obligation still discharges. Note (second audit) that all three of those
    points use a CONSTANT mask and a selection that never diverges from the
    declared set, so none of them is F2P-shaped: the analogue of
    PRECOND-TOO-STRONG on a total carrier is the obligation being unsatisfiable
    at exactly the override input, which ``admiss-f2p-shaped-point`` discharges
    by evaluation at a narrowed selection under a non-constant mask. The lane is
    two cases, not one, and NOT dropped — 97 velvet ports drop it entirely.
  * FRAME-MUTATION (nagini's mandatory read-only-write rivals) — INEXPRESSIBLE
    here, and DEMONSTRATED so rather than asserted. The nagini sibling holds each
    collection at a fractional heap permission (``Acc(.,1/2)``) an impl can
    illegally overwrite, and carries two rivals that mutate the read-only inputs.
    On this carrier ``selected``, ``declared`` and ``admissible`` are immutable
    values (none declared ``mut``), there is no heap and no aliasing. The
    counterpart rival was actually attempted (audit): assigning to an input
    inside the impl region (``selected := []``) does not produce a wrong-but-
    well-formed rival, it produces a file the front-end refuses —
    ``` `selected` cannot be mutated, only variables declared using `let mut`
    can be mutated ``` followed by ``Failed to parse an assertion without names:
    WPGen sorry``. So the class is not merely judged vacuous by argument: the
    mutation a nagini rival performs is not writable in this fragment, and any
    attempt is a malformed case rather than a rival the spec could reject. Not
    fabricated, and not dropped for difficulty.
  * DIVERGENCE / NON-TERMINATION - nothing to ship, and the reason has now been
    corrected TWICE. The first revision claimed a non-terminating body "cannot be
    written as a counterpart here" because the methods are total over immutable
    values; that is false, since a ``while`` prefix is in scope and can be
    spliced. The second revision then claimed this bundle sets
    ``loom.semantics.termination "partial"`` and that such a spliced rival
    VERIFIES vacuously, a spec hole. THAT IS ALSO FALSE and is withdrawn here.
    The frozen file sets ``termination "total"`` and its only correctness
    ``open`` is ``open TotalCorrectness DemonicChoice``; the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), so the option and the
    ``open`` cannot disagree. Under that scope a postcondition is claimed of ALL
    runs, the verifier demands a DECREASING measure on every loop, and a
    diverging rival is REJECTED. Measured on this cell: a spliced
    ``while 0 < 1`` / ``invariant True`` / ``done_with 1 < 0`` /
    ``decreasing (0 : Nat)`` prefix, with every proof reduced to a bare
    ``loom_solve``, is rejected at ``case «decreasing_1: (0 : Nat)»`` with the
    residual goal ``⊢ 0 < 0``; dropping the measure instead of faking it is
    refused even earlier, at elaboration (``Decreasing annotations are required
    in total correctness semantics``). The measure-carrying form is the sharper
    one, since it cannot be dismissed as merely missing the annotation.
    The disposition (nothing to ship) is unchanged, but the reason is now the
    WITNESS CONTRACT rather than a verifying rival: a reject case needs a witness
    that ELABORATES against the rival, and a rejected rival's module does not
    compile at all, so no witness can. No ``diverge-*`` nagini sibling exists to
    port either way.
  * UNGROUNDED-ORACLE ECHO — N/A: both post-images are method inputs / an
    input-grounded fold, not an axiomatized oracle; the ``axioms`` region is
    empty.

WITNESS MECHANICS (specific to this carrier). Each obligation is a ``method``
CONTRACT, not a bare predicate, so a witness reaches it through Velvet's own
tester machinery: ``getInlineInstancesTester selected declared admissible =
false`` (resp. ``getInlinesTester declared = false``) says the extracted
program's result violates the postcondition at that concrete input, checked in a
file whose ``prove_correct`` blocks have been stripped (no tactic script can
mask the verdict). ``derive_tester_for`` builds
``if decide pre then (match <name>Exec args with | DivM.res r => decide post
| _ => false) else true``, so ``Tester = false`` has TWO possible causes: a
postcondition violation, or the extracted program landing outside ``DivM.res``.
The free predicate ``admissible`` is instantiated at a concrete decidable
lambda in each witness, so the tester reduces to a ground boolean.

THE ASYMMETRY, STATED HONESTLY (this is what an earlier revision of this file
got wrong, and the correction is the reason each ``getInlineInstances`` witness
below now carries three parts). The frozen ``getInlineInstances`` program is a
``while`` loop whose fixpoint does NOT kernel-reduce: ``getInlineInstancesExec``
depends on ``Classical.choice``, and a ``decide`` on its tester gets stuck for
EVERY input — measured, including at inputs where the frozen program is RIGHT
(``getInlineInstancesTester [] [⟨0⟩] (fun _ => true) = true``, a true claim
about gold, also fails to elaborate: ``did not reduce to isTrue or isFalse``).
So for a rival reshaped into a loop-free closed form, the RAW two-build check
(the witness must FAIL on the frozen solution) is satisfied by NON-REDUCTION
rather than by refutation, and that exit code attests nothing on its own.
Measured directly: the deliberately hollow witness
``getInlineInstancesExec [] [] (fun _ => true) = DivM.res []`` — a claim that is
TRUE of the frozen solution and discriminates nothing — elaborates against a
loop-free rival (exit 0) and fails on gold (exit 1).

CORRECTION (THIRD audit — the second audit's own correction was itself wrong,
and this one is measured through the gate's own code path). The second revision
claimed the gate screens the stuck gold-side build and therefore catches a
hollow witness as ``witness-vacuous``. Run through ``_check_witness`` directly,
that is FALSE: with no ``witness_reference``, the hollow witness
``getInlineInstancesExec [] [] (fun _ => true) = DivM.res []`` — a claim TRUE of
the frozen solution, discriminating nothing — is recorded as
``rejected (witness refutes the rival)`` with
``witness_subject: "the frozen solution"``. The reason is that the stuck screen
matches on the ERROR TEXT, and that witness's gold-side build fails with a plain
``Tactic `rfl` failed`` (the loop simply is not definitionally equal to the
value) which no stuck screen matches. So the screen never fires, and gold's
exit 1 is accepted as a refutation the kernel never performed.

Worse, whether the screen fires at all depended on LEG ORDERING, not on
anything structural. Measured on ``weak-materialize-from-declared``: the shipped
three-leg witness puts a ``decide`` on the tester in leg (c), whose gold-side
failure DOES emit ``did not reduce to `isTrue` or `isFalse``` — so the screen
fires and the gate re-refutes against a positive. Strip leg (c) and keep only
(a)+(b), and gold fails with ``rfl failed`` alone: no stuck message, screen
silent, subject recorded as "the frozen solution". Identical spec, identical
rival, and the attestation's substance turned on which leg happened to error
first.

REPAIR (this audit, and it is why the five ``getInlineInstances`` cases now
carry ``witness_reference``). Naming the subject explicitly removes the
dependence on that accident: each of those witnesses is refuted against
``_GII_WITNESS_REF``, a LOOP-FREE impl of the byte-identical frozen spec which
the gate independently checks shares the spec and VERIFIES before using. Re-run:
all five record ``witness_subject: "the reference impl"``, and the hollow
witness above is now correctly returned as ``witness-vacuous`` (inconclusive —
it FAILS the battery) instead of passing. The gold-side leg now carries
information about the claim regardless of leg ordering.
The ``getInlines`` obligation needs no reference and is given none: its frozen
body is already loop-free ``return declared``, so its rivals' witnesses fail on
GOLD as a genuine SEMANTIC refutation (``decide`` proved the proposition false),
confirmed by forgery (``= true`` BUILDS on gold where ``= false`` fails).

The (a)+(b) legs below are kept regardless. They do not depend on which impl the
gate picks as the second subject, and their FORGERY behaviour was measured
directly (see WHAT THE SECOND AUDIT FOUND).

WHAT CLOSES IT. Each ``getInlineInstances`` reject witness states its refutation
in three machine-checked parts, so its force does not rest on the gold-side
stall:

  (a) ``<name>Exec <input> = DivM.res <concrete wrong value>`` by ``rfl`` — pins
      the value the rival's extracted program actually returns, which also rules
      out the ``| _ => false`` arm as the source of ``Tester = false``;
  (b) ``<concrete wrong value> ≠ kept <mask> <selection>`` by ``decide`` — that
      value is wrong per the SPEC'S OWN post-image at that input, decided on
      ground data with no reference to any impl;
  (c) the ``Tester = false`` claim the gate's protocol consumes.

(a)+(b) together are a self-contained counterexample: the rival returns X, and
the spec's post-image at that input is not X. Independently cross-checked
(recorded, not gate-visible): every witness below was also built against a
CORRECT loop-free impl (``return kept admissible selected``), and each FAILED
there — the (a) leg with ``rfl failed: not definitionally equal``, the (c) leg
with ``decide proved that the proposition ... is false``. That is the check the
gate structurally cannot run, and it is what shows these rivals are refuted for
being WRONG rather than for being loop-free. Every leg's exit code below was
observed on a real build.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
per-entry access-control decision is the free input ``admissible`` (an
A-reference the R/I legs differential-test — G-CONF's job), and every other
callee the build loop invokes is unchanged and folded into it (mapping.md §3),
so there is no consumed contract to probe in this lane. The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11095"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside an impl region (between -- impl-start and
# -- impl-end) or inside a prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load by _swap. Editing only these
# keeps markers.same_spec True and every prove_correct statement byte-identical
# (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of getInlines: the default selection hook returns
# the statically declared set unchanged.
_GI_IMPL = """    -- impl-start
    return declared
    -- impl-end"""

# The WHOLE executable body of getInlineInstances: the backward accumulating
# loop over the SELECTION, keeping each admissible entry in order. Reject rivals
# replace this with a loop-free closed form (so their tester reduces under
# `decide`); the loop-free positive control does too.
_GII_IMPL = """    -- impl-start
    let mut acc : List InlineClass := []
    let mut i := selected.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ selected.length
      invariant acc = kept admissible (selected.drop i)
      done_with i = 0
      decreasing i
    do
      let c := selected[i - 1]!
      acc := (if admissible c then [c] else []) ++ acc
      i := i - 1
    return acc
    -- impl-end"""

# The FULL frozen getInlineInstances proof body (everything after the
# `prove_correct getInlineInstances by` header). A positive control that
# collapses the loop to the closed form the post-image names retunes this; the
# tactic body is elided from the spec view, so this is a proof reshape, not a
# spec change.
_GII_PROOF = """prove_correct getInlineInstances by
  loom_solve
  rw [kept_drop_step admissible selected i (by omega) (by omega)]
  simp_all"""

# The first executable line of the getInlineInstances impl region; an in-region
# assert prepended here is discharged by the (retuned) proof without disturbing
# the method's own obligation.
_GII_TOP = "    let mut acc : List InlineClass := []"


# ---- The WITNESS REFERENCE for every `getInlineInstances` reject case.
#
# WHY IT IS HERE (third audit, measured — this replaces a claim that was FALSE).
# The frozen `getInlineInstances` program is a `while` loop whose fixpoint does
# not kernel-reduce, so the gold-side half of the witness protocol cannot decide
# anything at ANY input (see WITNESS MECHANICS). The gate handles that by
# screening the stuck build and re-refuting against one of the battery's own
# verifying positives — but that screen fires on the message, so WHICH leg of a
# witness happens to produce gold's first stuck error decides whether the screen
# engages at all. Measured directly on this cell:
#
#   * the shipped 3-leg witness       -> gold log contains the stuck `decide`,
#                                        screen fires, subject = a positive;
#   * the SAME witness minus leg (c)  -> gold fails only with `rfl failed`,
#                                        NO stuck message, screen does NOT fire,
#                                        and the gate accepts gold's exit 1 as a
#                                        refutation it never performed.
#
# So the protection was incidental to leg ordering, not structural. And the
# earlier revision's "CORRECTION" — that a hollow witness is caught as
# `witness-vacuous` — was measured FALSE as written: run through the gate's own
# `_check_witness` with no reference, the hollow witness
# `getInlineInstancesExec [] [] (fun _ => true) = DivM.res []` (TRUE of gold,
# discriminating nothing) is recorded as `rejected (witness refutes the rival)`,
# subject "the frozen solution", because its gold-side failure is a plain
# `rfl failed` that no stuck screen matches.
#
# Naming this reference explicitly removes the dependence on that accident. It is
# a LOOP-FREE impl of the byte-identical frozen spec, so the gate checks it
# shares the spec and VERIFIES before using it (`_reference_ok`), and every
# witness is then refuted against a subject that actually reduces. Re-measured
# with the reference in place: all five cases attest against "the reference
# impl", and the hollow witness above is now correctly rejected as
# `witness-vacuous` (an inconclusive outcome that FAILS the battery) instead of
# passing. That is the whole point of the change — the gold-side leg now carries
# information about the claim regardless of which leg errors first.
_GII_WITNESS_REF = _swap(
    _swap(_BASE, _GII_IMPL,
          "    -- impl-start\n"
          "    return kept admissible selected\n"
          "    -- impl-end"),
    _GII_PROOF,
    "prove_correct getInlineInstances by\n"
    "  loom_solve")


# ---- witness preambles. Reach each method contract through Velvet's tester
# ---- machinery: `<name>Tester <args> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input.
def _gii_tester(body):
    return ("extract_program_for getInlineInstances\n"
            "prove_precondition_decidable_for getInlineInstances\n"
            "prove_postcondition_decidable_for getInlineInstances\n"
            "derive_tester_for getInlineInstances\n\n" + body)


def _gi_tester(body):
    return ("extract_program_for getInlines\n"
            "prove_precondition_decidable_for getInlines\n"
            "prove_postcondition_decidable_for getInlines\n"
            "derive_tester_for getInlines\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps its byte-identical `ensures`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-materialize-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same materialisation; the loop-specific
        # proof is retuned since the impl now matches the post-image
        # syntactically (loom_solve closes it outright).
        #
        # HONEST STRENGTH (audited): this positive is real but CHEAP — the impl
        # is syntactically the post-image, so the obligation closes at `rfl`
        # strength and it cannot detect a spec that is too strong about anything
        # except the presence of a loop. It is kept as the minimal-shape control
        # and is no longer the only positive on this obligation:
        # `pos-materialize-filter` and `pos-materialize-forward-loop` below
        # defend the SAME clause from impls whose equality to the post-image is
        # a theorem rather than a reflexivity.
        "module": _swap(
            _swap(_BASE, _GII_IMPL,
                  "    -- impl-start\n"
                  "    return kept admissible selected\n"
                  "    -- impl-end"),
            _GII_PROOF,
            "prove_correct getInlineInstances by\n"
            "  loom_solve"),
        "rationale": "a loop-free impl that returns the admissible-sublist "
                     "directly must satisfy `result = kept admissible selected`; "
                     "a correct reshape of the modeled behaviour verifying is "
                     "exactly what SPEC-TOO-STRONG would deny. Exercises the "
                     "load-bearing obligation from a maximally different "
                     "(loop-free) control-flow shape. NOTE (audit): closes at "
                     "reflexivity strength, so it is the WEAKEST of the three "
                     "positives on this clause; see pos-materialize-filter and "
                     "pos-materialize-forward-loop. (Sibling: "
                     "pos-materialize-reshape.)",
    },
    {
        "id": "pos-materialize-filter",
        "kind": "soundness",
        "expect": "verify",
        # A correct impl expressed with a DIFFERENT library function
        # (`List.filter`) whose equality to the post-image fold is a genuine
        # theorem, not a reflexivity: with a bare `loom_solve` the obligation
        # is left open at
        #   `List.filter admissible selected = kept admissible selected`
        # (measured). The bridging induction is discharged inside the tactic
        # body as a `have`, so no new top-level lemma is introduced and the
        # variant stays in scope.
        "module": _swap(
            _swap(_BASE, _GII_IMPL,
                  "    -- impl-start\n"
                  "    return selected.filter admissible\n"
                  "    -- impl-end"),
            _GII_PROOF,
            "prove_correct getInlineInstances by\n"
            "  have hfil : ∀ (f : InlineClass → Bool) (xs : List InlineClass),\n"
            "      kept f xs = xs.filter f := by\n"
            "    intro f xs\n"
            "    induction xs with\n"
            "    | nil => rfl\n"
            "    | cons c cs ih =>\n"
            "      rw [kept_cons, List.filter_cons, ih]\n"
            "      by_cases h : f c <;> simp [h]\n"
            "  loom_solve <;> simp [hfil]"),
        "rationale": "a faithful correct impl written with the standard "
                     "list-filter primitive rather than the spec's own fold "
                     "must verify. Unlike pos-materialize-closed-form this is "
                     "NOT reflexivity: a bare `loom_solve` leaves "
                     "`List.filter admissible selected = kept admissible "
                     "selected` unsolved (observed), so the case shows the "
                     "clause admits any impl PROVABLY equal to the post-image, "
                     "not merely one spelled like it. If the spec rejected it, "
                     "it would be SPEC-TOO-STRONG on the spelling of the "
                     "materialisation. (Added by audit: the shipped positives "
                     "were all rfl-strength.)",
    },
    {
        "id": "pos-materialize-forward-loop",
        "kind": "soundness",
        "expect": "verify",
        # The sharpest correct reshape available here: keep a LOOP (so the impl
        # is not the post-image in disguise) but run it the other way round —
        # forward over the selection, appending each admissible entry to the
        # END of the accumulator, with a `take`-based invariant instead of the
        # frozen `drop`-based one. Equality to the front-recursive fold now
        # needs a real append/split argument (`kept f (xs ++ ys) = kept f xs ++
        # kept f ys` plus a take-step); with a bare `loom_solve` the loop-body
        # goal is left open (measured). Both lemmas are inlined as `have`s to
        # stay in variant scope.
        "module": _swap(
            _swap(_BASE, _GII_IMPL,
                  "    -- impl-start\n"
                  "    let mut acc : List InlineClass := []\n"
                  "    let mut i := 0\n"
                  "    while i < selected.length\n"
                  "      invariant i ≤ selected.length\n"
                  "      invariant acc = kept admissible (selected.take i)\n"
                  "      done_with i = selected.length\n"
                  "      decreasing selected.length - i\n"
                  "    do\n"
                  "      let c := selected[i]!\n"
                  "      acc := acc ++ (if admissible c then [c] else [])\n"
                  "      i := i + 1\n"
                  "    return acc\n"
                  "    -- impl-end"),
            _GII_PROOF,
            "prove_correct getInlineInstances by\n"
            "  have happ : ∀ (f : InlineClass → Bool) (xs ys : List InlineClass),\n"
            "      kept f (xs ++ ys) = kept f xs ++ kept f ys := by\n"
            "    intro f xs ys\n"
            "    induction xs with\n"
            "    | nil => simp [kept_nil]\n"
            "    | cons c cs ih =>\n"
            "      rw [List.cons_append, kept_cons, kept_cons, ih, List.append_assoc]\n"
            "  have hstep : ∀ (f : InlineClass → Bool) (xs : List InlineClass) (i : Nat),\n"
            "      i < xs.length →\n"
            "      kept f (xs.take (i + 1)) = kept f (xs.take i) "
            "++ (if f xs[i]! then [xs[i]!] else []) := by\n"
            "    intro f xs i hi\n"
            "    have h : xs.take (i + 1) = xs.take i ++ [xs[i]!] := by\n"
            "      rw [List.getElem!_eq_getElem?_getD, "
            "List.getElem?_eq_getElem hi, Option.getD_some]\n"
            "      exact List.take_succ_eq_append_getElem hi\n"
            "    rw [h, happ]\n"
            "    simp [kept_cons, kept_nil]\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | (rw [hstep admissible selected i (by omega)]; simp_all)\n"
            "    | simp_all"),
        "rationale": "the opposite iteration order with the opposite "
                     "accumulation side and a `take`-based (not `drop`-based) "
                     "invariant: a correct impl maximally far from the frozen "
                     "one that still carries a loop. Its obligation is NOT "
                     "closed by `loom_solve` alone — the residual goal "
                     "`(acc ++ if admissible selected[i]! then [selected[i]!] "
                     "else []) = kept admissible (selected.take (i+1))` was "
                     "observed — so verifying here shows the clause pins the "
                     "RESULT VALUE and not the frozen loop's shape or "
                     "invariant style. A spec that rejected this would be "
                     "SPEC-TOO-STRONG on the direction of iteration. (Added by "
                     "audit.)",
    },
    {
        "id": "pos-select-rebind",
        "kind": "soundness",
        "expect": "verify",
        # The default selection hook reshaped: bind the declared set to a local
        # and return it. Same value flow; the obligation `out = declared` still
        # holds and loom_solve closes it unchanged. Defends the getInlines
        # obligation from a (mildly) different shape.
        "module": _swap(
            _BASE, _GI_IMPL,
            "    -- impl-start\n"
            "    let out := declared\n"
            "    return out\n"
            "    -- impl-end"),
        "rationale": "rebinding the declared set through a local computes the "
                     "same value, so `out = declared` still holds and loom_solve "
                     "closes untouched; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG on the selection hook's shape). NOTE "
                     "(audit): a `let` rebinding is DEFINITIONALLY the frozen "
                     "body, so this case is near-vacuous as a soundness probe — "
                     "kept only as the minimal control. The real defence of the "
                     "`out = declared` clause is pos-select-branch below, whose "
                     "impl is not definitionally the frozen one. (Sibling: "
                     "pos-select-reshape.)",
    },
    {
        "id": "pos-select-branch",
        "kind": "soundness",
        "expect": "verify",
        # A correct default hook that is NOT definitionally `return declared`:
        # it branches on whether the declared set is empty and returns `[]` in
        # that case. Behaviourally identical (on an empty list, `[] = declared`)
        # but the impl is an `if` over a decidable test on the input, so the
        # obligation has to reason through the branch rather than match the
        # post-image syntactically.
        "module": _swap(
            _BASE, _GI_IMPL,
            "    -- impl-start\n"
            "    let out := if declared.isEmpty then ([] : List InlineClass) "
            "else declared\n"
            "    return out\n"
            "    -- impl-end"),
        "rationale": "a correct default hook whose body is a live branch on the "
                     "declared set (returning `[]` exactly when the declared set "
                     "IS empty) must verify: both arms yield `declared`. Unlike "
                     "pos-select-rebind, the impl is not definitionally the "
                     "frozen body, so the case shows `out = declared` admits any "
                     "impl that computes the declared set rather than only one "
                     "spelled as `return declared`. Rejecting it would be "
                     "SPEC-TOO-STRONG. (Added by audit; no nagini sibling.)",
    },

    # =====================================================================
    # ADMISSIBILITY — neither method has a `require` clause, so the "a normal
    # input satisfies the precondition" probe is not where the risk sits. The
    # residual risk is a DEGENERATE post-image (a spec no impl can meet reads
    # like a spec every impl meets). This case discharges an in-region assert at
    # concrete inputs, establishing that `kept` really does KEEP an all-
    # admissible non-empty selection, DROP a fully-filtered one, and keep the
    # empty selection empty. The surrounding impl is kept verbatim so the
    # method's own obligation still discharges; the assert is live (a false claim
    # about the same points leaves an unsolved goal), and the proof gains one
    # `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GII_TOP,
                  "    assert (with_name_prefix `adm\n"
                  "      (kept (fun _ => true) [({id := 0} : InlineClass)] "
                  "= [({id := 0} : InlineClass)] ∧\n"
                  "       kept (fun _ => false) [({id := 0} : InlineClass)] = [] ∧\n"
                  "       kept (fun _ => true) ([] : List InlineClass) = []))\n"
                  "    let mut acc : List InlineClass := []"),
            _GII_PROOF,
            "prove_correct getInlineInstances by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [kept_drop_step admissible selected i (by omega) (by omega)];\n"
            "       simp_all)\n"
            "    | simp_all"),
        "rationale": "the post-image is non-degenerate at the F2P-shaped points: "
                     "`kept` KEEPS a non-empty all-admissible selection, DROPS a "
                     "fully-filtered one, and keeps the empty selection empty. The "
                     "in-region assert must discharge (else the obligation is "
                     "degenerate / PRECOND-TOO-STRONG); the impl is kept verbatim "
                     "so `result = kept admissible selected` still verifies. "
                     "(Sibling: admiss-fresh-view, re-aimed.)",
    },
    {
        "id": "admiss-f2p-shaped-point",
        "kind": "admissibility",
        "expect": "verify",
        # The lane the FIRST audit left half-aimed. `admiss-grounded` pins `kept`
        # at three CONSTANT-mask points, all of which are degenerate in the one
        # dimension that matters here: none of them has a selection that DIFFERS
        # from the declared set, so none of them is F2P-shaped. On a total carrier
        # the analogue of PRECOND-TOO-STRONG is the obligation being unsatisfiable
        # at exactly an F2P-shaped input, so this case discharges the obligation
        # BY EVALUATION at that concrete point, as an in-region `assert`, before
        # closing the frozen obligation verbatim:
        #   * a NARROWED selection under a MIXED mask keeps exactly the admissible
        #     prefix entry (the override sub-domain, with a non-constant mask);
        #   * a selection carrying an entry the declared set does not (id 1) still
        #     materialises it (the spec really is independent of `declared`);
        #   * the empty selection is DISTINGUISHED from a 2-entry one, so the
        #     post-image is not collapsing the override point into the default.
        # Liveness measured, not asserted: flipping the third conjunct's `≠` to
        # `=` leaves an unsolved goal (`simp_all made no progress`, exit 1), so
        # the assert is load-bearing rather than decorative.
        "module": _swap(
            _swap(_BASE, _GII_TOP,
                  "    assert (with_name_prefix `f2p\n"
                  "      (kept (fun c => c.id == 0) "
                  "[({id := 0} : InlineClass), ({id := 1} : InlineClass)]\n"
                  "         = [({id := 0} : InlineClass)] ∧\n"
                  "       kept (fun _ => true) [({id := 1} : InlineClass)] "
                  "= [({id := 1} : InlineClass)] ∧\n"
                  "       kept (fun _ => true) ([] : List InlineClass)\n"
                  "         ≠ kept (fun _ => true) "
                  "[({id := 0} : InlineClass), ({id := 1} : InlineClass)]))\n"
                  "    let mut acc : List InlineClass := []"),
            _GII_PROOF,
            "prove_correct getInlineInstances by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [kept_drop_step admissible selected i (by omega) (by omega)];\n"
            "       simp_all)\n"
            "    | simp_all"),
        "rationale": "the obligation is SATISFIABLE at an F2P-SHAPED input, which "
                     "is the analogue of PRECOND-TOO-STRONG on a carrier whose "
                     "methods carry no `require` clause: if the post-image were "
                     "unsatisfiable at exactly the override point, the spec would "
                     "read like a spec every impl meets while no faithful impl "
                     "could. Discharged by evaluation at a NARROWED selection "
                     "under a NON-CONSTANT mask (the point the failing scenario "
                     "drives the hook to), at a selection carrying an entry the "
                     "declared set lacks, and at the empty-vs-2-entry pair the "
                     "post-image must keep distinct; the impl is kept verbatim so "
                     "`result = kept admissible selected` still verifies. Sharper "
                     "than admiss-grounded, whose three points are all CONSTANT "
                     "masks with no selection/declared divergence. (Added by the "
                     "second audit; the lane it completes is the one 97 velvet "
                     "ports drop entirely.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-materialize-from-declared",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central differential (the pre-image bug): materialise from the
        # statically DECLARED set, ignoring the selection hook. Correct iff
        # selected == declared; diverges on exactly the override sub-domain the
        # failing test exercises.
        "module": _swap(
            _BASE, _GII_IMPL,
            "    -- impl-start\n"
            "    return kept admissible declared\n"
            "    -- impl-end"),
        "refinement": "this IS the pre-image behaviour: the build iterates the "
                      "statically declared registration set and ignores the "
                      "per-request/per-object selection the hook yields. The "
                      "failing test overrides the hook to yield an empty / "
                      "narrowed / reordered selection differing from the declared "
                      "set, and asserts the built instances track the OVERRIDE; a "
                      "counterpart iterating the declared set builds the wrong "
                      "instances there and the test FAILS — it would NOT resolve.",
        "rationale": "REJECT from `result = kept admissible selected`: the rival "
                     "returns `kept admissible declared`, which differs whenever "
                     "`selected ≠ declared`. The spec pins the result to the "
                     "SELECTION regardless of the declared set, so a differing "
                     "pair refutes it. If it verified, the spec would admit the "
                     "pre-image bug => SPEC-TOO-WEAK. Refuted at selected=[], "
                     "declared=[⟨0⟩], admissible=(fun _ => true): the rival's "
                     "extracted program returns [⟨0⟩] (pinned by `rfl`), and "
                     "`kept (fun _ => true) [] = []` decides that [⟨0⟩] is NOT the "
                     "value the post-image names there. Cross-checked against a "
                     "CORRECT loop-free impl: the same witness FAILS there (`rfl "
                     "failed`; `decide proved ... is false`), so the refutation "
                     "tracks WRONGNESS, not loop-freeness. (Sibling: "
                     "partial-materialize-from-configured.)",
        # Refuted against a subject that REDUCES, named explicitly rather than
        # left to the gate's stuck-screen fallback; see _GII_WITNESS_REF.
        "witness_reference": _GII_WITNESS_REF,
        "witness": _gii_tester(
            "-- (a) the value the rival's extracted program actually returns\n"
            "example : getInlineInstancesExec [] [({id := 0} : InlineClass)] "
            "(fun _ => true)\n"
            "    = DivM.res [({id := 0} : InlineClass)] := by rfl\n\n"
            "-- (b) that value is NOT the one the spec's post-image names here\n"
            "example : ([({id := 0} : InlineClass)] : List InlineClass)\n"
            "    ≠ kept (fun _ => true) ([] : List InlineClass) := by decide\n\n"
            "-- (c) hence the contract is violated at this input\n"
            "example : getInlineInstancesTester [] "
            "[({id := 0} : InlineClass)] (fun _ => true) = false := by\n  decide\n"),
    },
    {
        "id": "weak-materialize-no-filter",
        "kind": "uniqueness",
        "expect": "reject",
        # Iterate the selection but DROP the admissibility filter — return the
        # whole selection. Correct only when every entry is admissible; diverges
        # whenever some entry fails the access-control test.
        "module": _swap(
            _BASE, _GII_IMPL,
            "    -- impl-start\n"
            "    return selected\n"
            "    -- impl-end"),
        "refinement": "dropping the per-entry access-control keep decision "
                      "materialises inline editors a request must NOT see; a "
                      "counterpart that removed the admissibility guard would "
                      "expose unauthorised inlines and fail the permission "
                      "PASS_TO_PASS behaviour — it does not faithfully resolve.",
        "rationale": "REJECT from `result = kept admissible selected`: `kept` "
                     "drops entries where `admissible` is false, so returning the "
                     "whole selection diverges whenever some entry is "
                     "inadmissible. Refuted at selected=[⟨0⟩], declared=[], "
                     "admissible=(fun _ => false): gold builds [], the rival "
                     "builds [⟨0⟩] — a distinct input point from the central "
                     "rival, and one that varies the `admissible` binder. "
                     "(Sibling: partial-materialize-no-filter.)",
        # Refuted against a subject that REDUCES, named explicitly rather than
        # left to the gate's stuck-screen fallback; see _GII_WITNESS_REF.
        "witness_reference": _GII_WITNESS_REF,
        "witness": _gii_tester(
            "-- (a) the value the rival's extracted program actually returns\n"
            "example : getInlineInstancesExec [({id := 0} : InlineClass)] [] "
            "(fun _ => false)\n"
            "    = DivM.res [({id := 0} : InlineClass)] := by rfl\n\n"
            "-- (b) that value is NOT the one the spec's post-image names here\n"
            "example : ([({id := 0} : InlineClass)] : List InlineClass)\n"
            "    \u2260 kept (fun _ => false) [({id := 0} : InlineClass)] := by decide\n\n"
            "-- (c) hence the contract is violated at this input\n"
            "example : getInlineInstancesTester [({id := 0} : InlineClass)] "
            "[] (fun _ => false) = false := by\n  decide\n"),
    },
    {
        "id": "weak-materialize-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS: materialise the admissible entries in REVERSED order. Equals
        # `kept admissible selected` only when the kept list is a palindrome (e.g.
        # a single entry); diverges on any selection with >=2 distinct admissible
        # entries. Forces the spec to pin ORDER, not just membership/length.
        "module": _swap(
            _BASE, _GII_IMPL,
            "    -- impl-start\n"
            "    return (kept admissible selected).reverse\n"
            "    -- impl-end"),
        "refinement": "materialising the admissible editors in reversed order "
                      "renders inline editors out of their declared/selection "
                      "order; the failing test observes `type(instances[0])`, so "
                      "a reversed multi-entry selection presents the wrong first "
                      "editor and any order-observing admin behaviour diverges — "
                      "it does not faithfully resolve.",
        "rationale": "REJECT from `result = kept admissible selected` (element-"
                     "wise, ordered `List` equality): the reversal equals the "
                     "fold only when the kept list is symmetric; it diverges on "
                     "any selection with >=2 distinct admissible entries. A spec "
                     "pinning only membership or length would MISS this => "
                     "SPEC-TOO-WEAK. Refuted at selected=[⟨0⟩,⟨1⟩], declared=[], "
                     "admissible=(fun _ => true): gold builds [⟨0⟩,⟨1⟩], the rival "
                     "builds [⟨1⟩,⟨0⟩] — its own distinguishing point (the "
                     "single-entry rivals do not exercise order). (Sibling: "
                     "nearmiss-reverse-order.)",
        # Refuted against a subject that REDUCES, named explicitly rather than
        # left to the gate's stuck-screen fallback; see _GII_WITNESS_REF.
        "witness_reference": _GII_WITNESS_REF,
        "witness": _gii_tester(
            "-- (a) the value the rival's extracted program actually returns\n"
            "example : getInlineInstancesExec "
            "[({id := 0} : InlineClass), ({id := 1} : InlineClass)] []\n"
            "    (fun _ => true) "
            "= DivM.res [({id := 1} : InlineClass), ({id := 0} : InlineClass)] "
            ":= by rfl\n\n"
            "-- (b) that ORDER is NOT the one the spec's post-image names here\n"
            "example : ([({id := 1} : InlineClass), ({id := 0} : InlineClass)] "
            ": List InlineClass)\n"
            "    \u2260 kept (fun _ => true) "
            "[({id := 0} : InlineClass), ({id := 1} : InlineClass)] := by decide\n\n"
            "-- (c) hence the contract is violated at this input\n"
            "example : getInlineInstancesTester "
            "[({id := 0} : InlineClass), ({id := 1} : InlineClass)] "
            "[] (fun _ => true) = false := by\n  decide\n"),
    },
    {
        "id": "weak-nearmiss-empty-selection-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # THE SHARPEST near-miss available on this clause, and the one the
        # shipped rivals left unattacked: correct on EVERY input except the
        # empty selection, where it silently falls back to the declared set.
        # `weak-materialize-from-declared` is wrong on the whole
        # `selected != declared` sub-domain; this one is wrong on a single
        # point of it, so it survives any spec that pins the clause only for
        # non-empty selections. That point is exactly the sub-domain the
        # failing test drives the hook to.
        "module": _swap(
            _BASE, _GII_IMPL,
            "    -- impl-start\n"
            "    let r := if selected.isEmpty then kept admissible declared "
            "else kept admissible selected\n"
            "    return r\n"
            "    -- impl-end"),
        "refinement": "a build that special-cases the empty selection and falls "
                      "back to the statically declared registrations reproduces "
                      "the pre-image behaviour on precisely the input the "
                      "failing test drives the selection hook to: the hook is "
                      "overridden to yield NO registrations and the test asserts "
                      "that NO inline editors are built. A counterpart with this "
                      "fallback builds the full declared set there, so the test "
                      "still FAILS — it would NOT resolve, while being "
                      "indistinguishable from correct on every other input.",
        "rationale": "REJECT from `result = kept admissible selected`: the clause "
                     "is universally quantified over `selected`, so being right "
                     "everywhere except one point is still wrong. Refuted at "
                     "selected=[], declared=[\u27e87\u27e9], "
                     "admissible=(fun _ => true): the rival's extracted program "
                     "returns [\u27e87\u27e9] (pinned by `rfl`) where the "
                     "post-image names []. A spec pinning the clause only for "
                     "non-empty selections would MISS this => SPEC-TOO-WEAK. "
                     "Cross-checked against a CORRECT loop-free impl: the witness "
                     "FAILS there, so it discriminates wrongness. Uses a fresh "
                     "`declared` point (id 7) distinct from every other case. "
                     "(Added by audit; no nagini sibling.)",
        # Refuted against a subject that REDUCES, named explicitly rather than
        # left to the gate's stuck-screen fallback; see _GII_WITNESS_REF.
        "witness_reference": _GII_WITNESS_REF,
        "witness": _gii_tester(
            "-- (a) the value the rival's extracted program actually returns\n"
            "example : getInlineInstancesExec ([] : List InlineClass)\n"
            "    [({id := 7} : InlineClass)] (fun _ => true) "
            "= DivM.res [({id := 7} : InlineClass)] := by rfl\n\n"
            "-- (b) that value is NOT the one the spec's post-image names here\n"
            "example : ([({id := 7} : InlineClass)] : List InlineClass)\n"
            "    \u2260 kept (fun _ => true) ([] : List InlineClass) := by decide\n\n"
            "-- (c) hence the contract is violated at this input\n"
            "example : getInlineInstancesTester [] [({id := 7} : InlineClass)] "
            "(fun _ => true) = false := by\n  decide\n"),
    },
    {
        "id": "weak-materialize-global-mask",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gap the first audit's own coverage note did not see: every shipped
        # witness instantiates `admissible` at a CONSTANT lambda
        # (`fun _ => true` / `fun _ => false`), so no case distinguishes a
        # PER-ENTRY admissibility decision from a decision taken ONCE. This rival
        # consults `admissible` on the head of the selection only and applies that
        # single verdict to every entry. It is therefore EXACTLY equal to gold at
        # every constant mask — i.e. at all five input tuples the rest of the
        # battery probes — and wrong only at a MIXED one, which is what makes it
        # the sharpest survivor of the shipped set.
        "module": _swap(
            _BASE, _GII_IMPL,
            "    -- impl-start\n"
            "    let keepAll := match selected with\n"
            "      | []     => true\n"
            "      | c :: _ => admissible c\n"
            "    let r := if keepAll then selected else ([] : List InlineClass)\n"
            "    return r\n"
            "    -- impl-end"),
        "refinement": "taking the access-control decision ONCE, from the first "
                      "selected registration, and applying it to all the others is "
                      "an all-or-nothing permission check: a request permitted to "
                      "see the first inline editor is handed every other one too, "
                      "regardless of its own per-inline access-control result. A "
                      "counterpart built this way exposes unauthorised inlines "
                      "whenever the per-entry decisions DIFFER and so fails the "
                      "permission PASS_TO_PASS behaviour, while passing every "
                      "all-permitted and all-denied scenario — it does not "
                      "faithfully resolve.",
        "rationale": "REJECT from `result = kept admissible selected`: `kept` "
                     "applies `admissible` to EVERY entry independently, so hoisting "
                     "one entry's verdict over the whole selection diverges as soon "
                     "as two entries disagree. Refuted at "
                     "selected=[⟨0⟩,⟨1⟩], declared=[⟨0⟩], "
                     "admissible=(fun c => c.id == 0): the post-image names [⟨0⟩], "
                     "the rival returns [⟨0⟩,⟨1⟩] (pinned by `rfl`). This is the "
                     "FIRST case in the battery to instantiate `admissible` at a "
                     "NON-CONSTANT lambda; a spec that pinned the mask only at "
                     "constant masks would MISS it => SPEC-TOO-WEAK, and so would "
                     "every other rival here (all of which agree with this one at "
                     "every constant mask). Cross-checked against a CORRECT "
                     "loop-free impl: the witness FAILS there (`rfl failed`; "
                     "`decide proved ... is false`), so the refutation tracks "
                     "wrongness. (Added by the second audit; no nagini sibling — "
                     "the sibling's per-entry flag is an explicit granted LIST, so "
                     "this collapse is not expressible there.)",
        # Refuted against a subject that REDUCES, named explicitly rather than
        # left to the gate's stuck-screen fallback; see _GII_WITNESS_REF.
        "witness_reference": _GII_WITNESS_REF,
        "witness": _gii_tester(
            "-- (a) the value the rival's extracted program actually returns\n"
            "example : getInlineInstancesExec "
            "[({id := 0} : InlineClass), ({id := 1} : InlineClass)]\n"
            "    [({id := 0} : InlineClass)] (fun c => c.id == 0)\n"
            "    = DivM.res [({id := 0} : InlineClass), ({id := 1} : InlineClass)] "
            ":= by rfl\n\n"
            "-- (b) that value is NOT the one the spec's post-image names here\n"
            "example : ([({id := 0} : InlineClass), ({id := 1} : InlineClass)] "
            ": List InlineClass)\n"
            "    ≠ kept (fun c => c.id == 0) "
            "[({id := 0} : InlineClass), ({id := 1} : InlineClass)] := by decide\n\n"
            "-- (c) hence the contract is violated at this input\n"
            "example : getInlineInstancesTester "
            "[({id := 0} : InlineClass), ({id := 1} : InlineClass)] "
            "[({id := 0} : InlineClass)] (fun c => c.id == 0) = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-select-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # A partial-domain rival on the SELECTION HOOK: the default selection
        # drops the first declared entry (yields declared.drop 1). Correct only
        # for an empty declared set; diverges on every non-empty one. The default-
        # hook obligation `out = declared` must reject it.
        "module": _swap(
            _BASE, _GI_IMPL,
            "    -- impl-start\n"
            "    return declared.drop 1\n"
            "    -- impl-end"),
        "refinement": "a default selection hook that dropped the first declared "
                      "registration would omit the first configured inline from "
                      "every default admin, breaking the existing non-override "
                      "behaviour (the PASS_TO_PASS views that render all declared "
                      "inlines); it does not resolve.",
        "rationale": "REJECT from `out = declared`: the default hook must yield "
                     "the declared set unchanged; narrowing it to `declared.drop "
                     "1` diverges on every non-empty declared set. Refuted at "
                     "declared=[⟨0⟩]: gold yields [⟨0⟩], the rival yields [] — a "
                     "distinct obligation (getInlines) and a distinct input point "
                     "from the getInlineInstances rivals. (Sibling: "
                     "partial-select-drop-first.)",
        "witness": _gi_tester(
            "example : getInlinesTester [({id := 0} : InlineClass)] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-select-constant-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # A second SELECTION-HOOK rival at a distinct `declared` point: the
        # default hook yields the empty selection unconditionally. Correct only
        # for an already-empty declared set; diverges on every non-empty one.
        # Varies the `declared` binder so the getInlines clause is probed at more
        # than one point.
        "module": _swap(
            _BASE, _GI_IMPL,
            "    -- impl-start\n"
            "    return []\n"
            "    -- impl-end"),
        "refinement": "a default selection hook that yielded the empty selection "
                      "would build NO inline editors for any default admin, "
                      "removing every configured inline from the existing "
                      "non-override behaviour (the PASS_TO_PASS views that render "
                      "the declared inlines); it does not resolve.",
        "rationale": "REJECT from `out = declared`: the default hook must yield "
                     "the declared set unchanged; the constant empty selection "
                     "diverges on every non-empty declared set. Refuted at "
                     "declared=[⟨0⟩,⟨1⟩]: gold yields [⟨0⟩,⟨1⟩], the rival yields "
                     "[] — a DIFFERENT `declared` point from weak-select-drop-"
                     "first, so the getInlines clause is probed at two distinct "
                     "inputs. (No direct nagini sibling; added to vary the free "
                     "`declared` binder of the getInlines obligation.)",
        "witness": _gi_tester(
            "example : getInlinesTester "
            "[({id := 0} : InlineClass), ({id := 1} : InlineClass)] "
            "= false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (2
# soundness positives, 1 admissibility, 2 frame-mutation rivals, 4
# uniqueness/near-miss rivals) plus 1 AXIOM_TESTS entry. The sibling contracts
# TWO operations over an AdminView whose three collections (configured,
# reported, granted) each carry a fractional heap permission, with the
# per-entry keep decision an explicit granted-flag list. This bundle models the
# SAME two operations — the default selection hook (`getInlines`) and the
# instance builder (`getInlineInstances`) — over the referentially-transparent
# carrier `List InlineClass`, folding the unchanged per-entry access-control
# decision into the free predicate `admissible`. The value/differential surface
# carries across intact; the permission surface does not exist here.
#
#   sibling case (nagini)              kind          -> here                            disposition
#   -------------------------------------------------------------------------------------------------
#   pos-materialize-reshape            soundness     -> pos-materialize-closed-form     RE-EXPRESSED
#   pos-select-reshape                 soundness     -> pos-select-rebind               RE-EXPRESSED
#   admiss-fresh-view                  admissibility -> admiss-grounded                 RE-AIMED
#   frame-write-reported               uniqueness    -> (none)                          INEXPRESSIBLE (shown)
#   frame-write-configured             uniqueness    -> (none)                          INEXPRESSIBLE (shown)
#   partial-materialize-from-configured uniqueness   -> weak-materialize-from-declared  PORTED (central)
#   partial-materialize-no-filter      uniqueness    -> weak-materialize-no-filter      PORTED
#   partial-select-drop-first          uniqueness    -> weak-select-drop-first          PORTED
#   nearmiss-reverse-order             uniqueness    -> weak-materialize-reversed       PORTED
#   (new, no sibling)                  uniqueness    -> weak-select-constant-empty      ADDED
#   ax-aref-deepmodels-sound           axiom         -> (none)                          DROPPED (G-AX)
#
#   Added by the independent audit of this port (no nagini sibling for any of
#   them; each was built and its outcome observed before being written down):
#   (audit)                            soundness     -> pos-materialize-filter          ADDED
#   (audit)                            soundness     -> pos-materialize-forward-loop    ADDED
#   (audit)                            soundness     -> pos-select-branch               ADDED
#   (audit)                            uniqueness    -> weak-nearmiss-empty-selection-fallback ADDED
#
#   Added by the SECOND (independent) audit of this port:
#   (audit2)                           uniqueness    -> weak-materialize-global-mask     ADDED
#   (audit2)                           admissibility -> admiss-f2p-shaped-point          ADDED
#
# WHAT THE AUDIT FOUND (recorded so the next reader does not have to re-derive
# it). The port's outcomes were all genuine — every rival really is wrong and
# every positive really does verify — but two claims it rested on were not:
#   1. The gold-side leg of the witness protocol does NOT discriminate for the
#      `getInlineInstances` obligation. The frozen impl's `while` fixpoint never
#      kernel-reduces (`getInlineInstancesExec` depends on `Classical.choice`),
#      so a `decide`-based witness fails on gold by STALLING, at every input,
#      including inputs where gold is right. A deliberately hollow witness that
#      is TRUE of gold was confirmed to pass both gate halves. Each such witness
#      now carries an `Exec = DivM.res <value>` (`rfl`) leg plus a
#      `<value> != kept <mask> <selection>` (`decide`) leg, which together are a
#      self-contained counterexample, and each was additionally cross-checked
#      against a CORRECT loop-free impl, where it fails. The two `getInlines`
#      witnesses were unaffected: gold's hook is loop-free, so they refute
#      semantically (`decide proved that the proposition ... is false`).
#   2. Both shipped positives were rfl-strength (the closed form IS the
#      post-image; a `let` rebinding IS definitionally the frozen body), so
#      neither could have detected a spec too strong about anything but the
#      presence of a loop. Three positives whose obligation a bare `loom_solve`
#      leaves OPEN were added, one of which keeps a loop and runs it the other
#      way round.
# WHAT THE SECOND AUDIT FOUND (independent re-derivation, all builds real).
# Every one of the 12 shipped cases earned its recorded outcome: 6/6 reject
# witnesses re-built with rival exit 0 and gold exit 1, and the two prose claims
# the first audit rested its witness design on were re-checked by the FORGERY
# experiment rather than by reading the errors. Results:
#   * The four `getInlineInstances` witnesses are NOT hollow, and the forgery pair
#     is what shows it. Flipping each witness's claim to assert the OPPOSITE (the
#     value a CORRECT impl returns, and `Tester = true`) changes the exit code on
#     the fallback subject the gate actually uses — forgery exit 0 where the real
#     witness exits 1 — so that subject's verdict tracks the claim. Against GOLD
#     both the witness and its forgery fail (`rfl failed` on (a), stuck `decide`
#     on (c)), which confirms gold's own exit code carries no information here,
#     exactly as the WITNESS MECHANICS section says. The gate screens that stall
#     and re-refutes against a verifying positive; see the CORRECTION there.
#   * The two `getInlines` witnesses refute against GOLD semantically, and the
#     forgery confirms it: `getInlinesTester [...] = true` BUILDS against gold
#     (exit 0) where `= false` fails, so the claim is what moves the exit code.
#   * `admiss-grounded`'s assert is LIVE: two independent falsifications of it
#     (claiming a fully-filtered singleton is KEPT; claiming an all-admissible
#     singleton is DROPPED) both leave an unsolved goal (exit 1).
#   * The three load-bearing positives' "a bare loom_solve leaves the obligation
#     OPEN" claims are TRUE, re-measured: pos-materialize-filter leaves
#     `List.filter admissible selected = kept admissible selected`, and
#     pos-materialize-forward-loop leaves the take-step invariant goal
#     `(acc ++ if admissible selected[i]! ...) = kept admissible (take (i+1) ...)`.
#   * The frame-mutation inexpressibility claim is TRUE, rebuilt on BOTH methods:
#     `selected := []` and `declared := []` each produce the front-end refusal
#     "`selected`/`declared` cannot be mutated, only variables declared using
#     `let mut` can be mutated", then "Failed to parse an assertion without
#     names: WPGen sorry". Not a rival the spec declines to reject.
# Two claims were FALSE and are corrected in place above:
#   1. DIVERGENCE was recorded as "vacuous — a non-terminating body cannot be
#      written as a counterpart here". It can: a `while true` prefix is in scope.
#      This round then claimed such a prefix VERIFIES (exit 0) under `partial`
#      semantics, which a LATER round measured false as well: the bundle is
#      total and the rival is REJECTED (`⊢ 0 < 0` on its own measure).
#      Disposition (nothing to ship) survives under both corrections, because a
#      rival whose module does not compile admits no elaborating witness. See the
#      DIVERGENCE entry above for the current account.
#   2. The claim that a hollow witness "passes BOTH gate halves" was false as a
#      statement about this gate — re-run through `_check_witness` it returns
#      `witness-vacuous` via the stuck-reduction fallback. See the CORRECTION in
#      WITNESS MECHANICS. (THIRD AUDIT: this "correction" was ITSELF wrong; the
#      hollow witness is recorded as `rejected` against "the frozen solution".
#      See below.)
#
# WHAT THE THIRD AUDIT FOUND (independent re-derivation; every exit code below
# was observed on a real build, and the gate-behaviour claims were measured by
# calling `_check_witness` rather than by reading errors).
# Confirmed, so a later reader need not redo them:
#   * Attack A is clean on all 14 cases: the consumer spec view, both `method`
#     signature lines, both `ensures` clauses, the whole `kept` pure region and
#     both `prove_correct` headers are BYTE-IDENTICAL to the frozen file. No
#     reformatted-statement hiding place.
#   * All 7 reject witnesses re-built: rival exit 0, gold exit 1, in every case.
#   * The FORGERY pair (attack B') re-run on all 7. For the five
#     `getInlineInstances` cases the forgery (asserting the value a CORRECT impl
#     returns, and `Tester = true`) fails on gold with the SAME `rfl failed`
#     shape as the real witness — i.e. gold's exit code carries no information —
#     but flips to exit 0 against a reducible correct subject, where the real
#     witness exits 1. For the two `getInlines` cases the forgery BUILDS on gold
#     (exit 0) where the witness fails, so gold's own verdict tracks the claim.
#   * Both admissibility asserts are LIVE: all SIX conjuncts across the two
#     cases were independently falsified and each falsification leaves an
#     unsolved goal (exit 1) — `simp_all made no progress` / `unsolved goals`.
#   * The three load-bearing positives' "bare `loom_solve` leaves it OPEN"
#     claims re-measured TRUE (filter: `List.filter admissible selected = kept
#     admissible selected`; forward loop: the take-step invariant goal), and
#     `pos-materialize-closed-form` re-measured as closing under bare
#     `loom_solve` — i.e. the file's own admission that it is the weakest of the
#     three is accurate.
#   * `pos-select-branch` really is NOT definitionally the frozen body: the
#     probe `(if declared.isEmpty then [] else declared) = declared := by rfl`
#     FAILS (`not definitionally equal`), while the `pos-select-rebind` analogue
#     succeeds. So the file's own ranking of its two hook positives is right.
#   * `weak-materialize-global-mask`'s central claim is machine-checked: its
#     closed form agrees with `kept` at all seven constant-mask points the rest
#     of the battery probes, and diverges at the mixed mask it is refuted at.
#   * Frame-mutation inexpressibility rebuilt on BOTH methods: `selected := []`
#     and `declared := []` each yield "cannot be mutated, only variables
#     declared using `let mut` can be mutated" + "WPGen sorry". Not a rival.
#   * Attack D, 23 further NEW wrong impls (loop off-by-one terminating at i>1;
#     head-denied-drops-all; truncate at length>=4; a neighbour-consulting mask;
#     a mask overridden at one id; keep-all-when-none-admissible; dedup; the
#     kept list duplicated / reversed-selection / with a fabricated entry
#     appended / with its last or all-but-first entries dropped; intersected
#     with and unioned with `declared`; a length==3 fallback; plus hook rivals
#     reversing, duplicating, deduping, truncating, appending to, and
#     id-filtering the declared set) were ALL rejected. NO spec hole.
#   * Attack E, 8 further correct reshapes (`foldr`, `flatMap`, `filterMap`,
#     reverse-filter-reverse, a two-pass map/filter/map, and `declared ++ []` /
#     `declared.take declared.length` / `declared.reverse.reverse` on the hook)
#     were ALL provable (exit 0). NO soundness hole.
# And one real DEFECT was found and FIXED: the gold-side leg of the five
# `getInlineInstances` witnesses was protected only by an accident of leg
# ordering — the stuck screen fires on the error TEXT, so a witness whose gold
# build happens to fail with a bare `rfl failed` is accepted as a refutation the
# kernel never performed (demonstrated: the hollow witness, and the shipped
# witness with leg (c) removed, both land on "the frozen solution"). Each of
# those five cases now names `_GII_WITNESS_REF` explicitly, which makes the
# subject deterministic and restores the hollow witness's correct
# `witness-vacuous` verdict. See the CORRECTION in WITNESS MECHANICS.
# The divergence lane was re-measured after this round and came out CLOSED, not a
# hole: under the file's total semantics a diverging rival is rejected on its own
# descent goal, so the conditional variant this round reported as verifying (an
# impl that hangs only at the empty selection) does not verify either. See the
# DIVERGENCE entry in the docstring for the goals; nothing is escalated.
# And one real GAP was found and closed: every shipped witness instantiated
# `admissible` at a CONSTANT lambda, so nothing distinguished a per-entry
# access-control decision from one taken once and hoisted. The rival that does
# exactly that (`weak-materialize-global-mask`) agrees with gold at every
# constant mask and therefore survived the entire shipped battery; it is now a
# case, refuted at a non-constant mask. The admissibility lane was likewise
# aimed only at constant-mask points with no selection/declared divergence, so
# `admiss-f2p-shaped-point` adds an F2P-shaped one.
# Second-audit attack D (13 further wrong impls, all REJECTED, no spec hole):
# dedup of the kept list, the correct answer with declared-side entries appended,
# selection intersected with the declared set, the inverted admissibility mask,
# the last kept entry dropped, only the first kept entry retained, a
# length>=2 fallback to the declared set, an all-keep fallback when nothing is
# admissible, the mask evaluated on the declared set's head, plus a
# de-duplicating / order-reversing / length>=2-reversing default hook. Attack E
# (5 further correct reshapes): `foldr`, `flatMap`, and reverse-filter-reverse on
# the materialiser all PROVABLE (exit 0), as was `declared ++ []` on the hook, so
# NO soundness hole. `declared.map (fun c => c)` needed one extra `simp` beyond a
# bare `loom_solve` (residual goal `List.map (fun c => c) declared = declared`)
# and then verified — a tactic-tuning gap, not a spec hole.
# Attack D (8 new wrong impls: selection intersected with the declared set,
# de-duplication, the correct answer with declared-side entries appended, the
# inverted admissibility mask, the last kept entry dropped, the empty-selection
# fallback, and a de-duplicating / order-reversing default hook) found NO spec
# hole: all 8 were rejected. The sharpest of them was kept as a case. Attack E
# (3 correct reshapes: filter, foldr, forward loop) found NO soundness hole:
# all 3 were provable, and two are now shipped as positives.
#
# RE-EXPRESSED (pos-materialize-reshape -> pos-materialize-closed-form): the
#   sibling reshapes the backward front-prepend loop (regrouped framing asserts,
#   renamed counter). On this carrier the sharpest correct reshape is to COLLAPSE
#   the loop into the closed form the post-image names (`kept admissible
#   selected`), a maximally different loop-free control-flow shape; loom_solve
#   closes it once the impl matches the post-image syntactically. RE-EXPRESSED
#   (pos-select-reshape -> pos-select-rebind): the sibling reshapes the default
#   copy loop; here the frozen default hook is already `return declared`, so the
#   faithful reshape rebinds it through a local. Both keep their byte-identical
#   obligation and were verified to build. AUDIT CORRECTION: both of these
#   re-expressions are weaker than the sibling they replace. The nagini
#   originals keep gold's loop and reshape its framing asserts, so Viper has to
#   re-derive the invariant; the velvet closed form IS the post-image (rfl) and
#   the `let` rebinding IS gold's body definitionally. The three added positives
#   restore the lost strength, `pos-materialize-forward-loop` most directly (it
#   keeps a loop, reverses its direction, and needs its own append/split lemma).
# RE-AIMED (admiss-fresh-view -> admiss-grounded): the sibling self-calls
#   materialize_editors on a fresh AdminView to prove the precondition (all
#   collections at 1/2, len(reported)==len(granted)) admits an F2P-shaped input —
#   a permission/length fact with no analogue on a referentially-transparent
#   carrier whose methods carry NO require clause. Re-aimed to the sharper
#   residual risk here: a degenerate post-image. The case discharges a live
#   in-region assert pinning KEEP (non-empty all-admissible), DROP (fully
#   filtered), and empty-stays-empty at concrete inputs; impl kept verbatim,
#   proof gains one `decide` arm.
# INEXPRESSIBLE (frame-write-reported, frame-write-configured): the sibling
#   carries these MANDATORY because each collection is held at Acc(.,1/2) an impl
#   can illegally write, and it ships one rival per read-only input. This backend
#   is referentially transparent and declares NO `mut` binder — every input is an
#   immutable value with no heap footprint — so there is no read-only field to
#   overwrite and no permission system to trip. The audit did not take this on
#   argument: it BUILT the counterpart (`selected := []` spliced into the impl
#   region, the only region surgery may touch) and the front-end refused the file
#   — "`selected` cannot be mutated, only variables declared using `let mut` can
#   be mutated", then "Failed to parse an assertion without names: WPGen sorry".
#   A rival that cannot be written is not a rival the spec declines to reject, so
#   the omission stands as inexpressible, NOT as a dropped-because-hard case.
# PORTED (the four uniqueness rivals): partial-materialize-from-configured ports
#   directly to weak-materialize-from-declared (the central pre-image bug:
#   materialise from the declared set, refuted where selected != declared);
#   partial-materialize-no-filter ports to weak-materialize-no-filter (drop the
#   admissibility guard, refuted where an entry is inadmissible);
#   partial-select-drop-first ports to weak-select-drop-first (the default hook
#   narrows the declared set, refuted against `out = declared` on a non-empty
#   declared set); nearmiss-reverse-order ports to weak-materialize-reversed (the
#   order attack, refuted on a >=2-distinct-entry selection). ADDED
#   (weak-select-constant-empty): a second getInlines rival (the constant empty
#   selection) at a DIFFERENT `declared` point, so the getInlines clause is probed
#   at more than one input (coverage). ADDED by audit
#   (weak-nearmiss-empty-selection-fallback): a rival correct on every input but
#   ONE — the empty selection, where it falls back to the declared set — which is
#   the sharpest near-miss on this clause and the point the failing test drives
#   the hook to. Each rival is a loop-free closed form whose tester
#   kernel-reduces; each witness was SEEN to hold of its rival (exit 0) and to
#   fail on gold (exit 1) with real builds. Read the WITNESS MECHANICS section
#   before treating that gold-side exit 1 as evidence: for the three
#   `getInlineInstances` rivals it is a STALL, not a refutation, which is why
#   those witnesses carry the value-pinning and post-image legs as well.
# DROPPED (ax-aref-deepmodels-sound): the axiom lane is G-AX's job. Here the
#   per-entry access-control decision is not an axiomatized oracle but the FREE
#   input `admissible` (an A-reference the R/I legs differential-test), and every
#   other build-loop callee is unchanged and folded into it (mapping.md §3), so
#   there is no consumed contract to probe in this lane. meta.json gates.G-AX =
#   skip. The gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Two obligations, two independent top-level clauses:
#   `getInlines.out = declared` and `getInlineInstances.result = kept admissible
#   selected`. The getInlines clause is defended TWICE (pos-select-rebind, the
#   definitional control; pos-select-branch, a live branch the obligation must
#   reason through) and attacked twice (weak-select-drop-first,
#   weak-select-constant-empty, at two distinct `declared` points). The
#   getInlineInstances clause is defended THREE times (pos-materialize-closed-form
#   at rfl strength; pos-materialize-filter, needing a filter/fold bridge;
#   pos-materialize-forward-loop, needing an append/split lemma) and attacked from
#   FIVE independent sub-domains: the SELECTION binder
#   (weak-materialize-from-declared, selected != declared), the ADMISSIBLE binder
#   (weak-materialize-no-filter, an inadmissible entry), ORDER within the kept
#   sublist (weak-materialize-reversed), a SINGLE-POINT near-miss
#   (weak-nearmiss-empty-selection-fallback, wrong only on the empty selection),
#   and the PER-ENTRY-ness of the admissibility decision
#   (weak-materialize-global-mask, wrong only at a non-constant mask).
#   The reject witnesses probe six DISTINCT input tuples: selected over
#   {[], [⟨0⟩], [⟨0⟩,⟨1⟩]} and n/a-for-getInlines, declared over
#   {[⟨0⟩], [], [⟨7⟩], [⟨0⟩,⟨1⟩]},
#   admissible over {(fun _ => true), (fun _ => false), (fun c => c.id == 0)}.
#   That last one matters and is the second audit's addition: with only CONSTANT
#   masks, `admissible` varies in spelling but not in the dimension that
#   distinguishes a per-entry decision from a hoisted one, so a binder the
#   coverage tool reported as "varying" was in fact probed at two points of the
#   same degenerate kind. The load-bearing binders `selected` and `admissible`
#   are now both varied MEANINGFULLY and both independently attacked. The free
#   binder `declared` is varied too (though, per the DEFENDED-SURFACE note, the
#   getInlineInstances clause is genuinely independent of it). So no rival that
#   mishandled only a fixed selection shape, a constant admissibility mask, or
#   the ordering could slip through.
#
# AXIOM_TESTS: dropped (see above); the gate ignores it regardless.
AXIOM_TESTS = []
