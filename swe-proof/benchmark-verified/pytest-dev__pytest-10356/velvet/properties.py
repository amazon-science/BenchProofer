"""properties.py — G-PBT falsification battery for pytest-dev__pytest-10356 (velvet).

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
ELABORATE against the rival and FAIL against a subject that SATISFIES the spec;
here that subject is a declared ``witness_reference`` rather than the frozen
solution, for the reason set out under WITNESS MECHANICS).

DEFENDED SURFACE (two cooperating read-only operations over a sequence of
per-source RAW element lists, ``List (List Item)``):

  collectMarks (lineage : List (List Item)) (wholeLineage : Bool)
               return (out : Outcome)
    ensures out =
      canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))

  attachMark (lineage : List (List Item)) (mark : Mark) return (out : Outcome)
    ensures out = withMark (canonicalize (lineage.headD [])) mark

THE CARRIER IS THE POINT, so read it before the cases. A source's attached list
does NOT hold canonical annotations; it holds whatever was put there. ``Item``
names the three shapes the operation actually distinguishes: ``canonical m``
(already an annotation), ``wrapped m`` (an applicator object carrying the
annotation ``m`` inside it, the ordinary hand-written shape), and ``foreign n``
(an element that is no annotation and carries none — ``n`` is its own identity
token). ``markOf`` is the annotation an element makes available (``none`` exactly
for ``foreign``); ``nameOf`` is the token an element is known by. ``Outcome`` is
what a collection yields: ``collected ms`` (a canonical annotation sequence) or
``refused n`` (no sequence at all, naming the offending element). So the element
domain is WIDER than the canonical one and the refusal is an OBSERVABLE result,
not an assumption about the inputs; ``canonicalize`` is a total function on the
whole widened domain and there is no ``require`` clause anywhere excluding the
foreign elements. That matters because the interesting sub-domain — a source
holding an element that is not an annotation — is exactly where the
type-checking step of the real collection earns its keep, and a model that
silently assumed it away would license an impl that deletes that step.

``flattenSeq`` is a total, fully-unfolded front-recursive fold (in the
spec-visible ``pure`` region): the in-order concatenation of every element of its
argument, skipping the empty ones without ending the assembly. ``canonicalize``
is likewise fully unfolded: it walks the assembled elements FROM THE FRONT,
replacing each by the annotation it makes available, and on the first element
that makes none it yields ``refused`` naming that element. Neither is an opaque
answer key — both post-images are GROUNDED in the method inputs (directive 8):
``collectMarks`` pins the result to the canonicalization of the concatenation of
a selection of its input ``lineage`` (the whole sequence, or just the first
element), and ``attachMark`` pins it to the canonicalization of the FIRST element
of its input ``lineage`` extended with the new ``mark``. So the cheapest honest
impl that satisfies each obligation IS the correct one; there is no
ungrounded-oracle echo to exploit (the ``axioms`` region is empty).

THE CENTRAL DIFFERENTIALS. There are two, and both are load-bearing.

  (1) BREADTH. When ``wholeLineage`` is true the ``collectMarks`` clause pins the
      result to the assembly of EVERY source in the lineage, not just the first.
      When the lineage has two-or-more non-empty sources (exactly the sub-domain
      the failing test exercises: a class inheriting from two independently-
      annotated base classes, so its resolution order carries several non-empty
      own lists), an impl that returns only the first source's annotations
      diverges and must be rejected. This is the behaviour the change
      establishes.

  (2) THE CANONICALIZING GATE. Every clause is stated through ``canonicalize``,
      so the outcome on an assembly containing an element that makes no
      annotation available is pinned to ``refused``, naming the FIRST such
      element. An impl that instead SKIPS such an element, or SUBSTITUTES some
      annotation for it, or reports an anonymous/last-offender refusal, or
      applies the gate to the wrong sub-assembly, computes a different
      ``Outcome`` and is rejected. This differential exists because the earlier
      revision of this spec did not have it: it modeled the canonicalizing step
      as the IDENTITY on canonical annotation lists, which made the type-checking
      gate INVISIBLE — an impl (and a refinement of it) that dropped the gate
      entirely satisfied the spec while breaking the existing behaviour that a
      source holding a non-annotation is refused rather than silently accepted.
      Widening the element domain and making the refusal an observable outcome is
      what closes that; note it is a WIDENING, not a new precondition — nothing
      was excluded from the domain to make the obligation easier.

BINDER STRUCTURE (read before judging binder coverage).
  * ``collectMarks`` depends on ``lineage`` and ``wholeLineage``. The reject
    witnesses vary ``lineage`` across lengths 1/2/3, across all-canonical,
    wrapped-bearing, and foreign-bearing element shapes, and with an interior
    EMPTY source; ``wholeLineage`` is varied across BOTH ``true`` (most rivals)
    and ``false`` (the flag-swap rival and the wrong-sub-assembly rival), so a
    rival mishandling only one flag value is caught.
  * ``attachMark`` depends on ``lineage`` (only its FIRST element is
    load-bearing) and ``mark``. One rival absorbs the whole lineage (isolating
    the head-only dependence), one drops the new ``mark`` entirely (isolating the
    ``mark`` dependence), one is wrong only when the first element is EMPTY (the
    sub-domain the other two agree with the spec on), one skips a foreign element
    in the own list, and one records the new annotation ON TOP of a refusal; the
    witnesses hold ``mark`` at distinct values.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Structurally different but correct
    impls (the accumulating backward loop collapsed to the closed form the
    post-image names; the loop body inlined; the outcome destructured and
    rebuilt case by case; the recording operation's delegation to the collection
    removed entirely; the recording operation branching explicitly on the two
    outcome shapes) that MUST still verify, else the spec is SPEC-TOO-STRONG on
    the shape of the impl. Each keeps a shape whose frozen ``loom_solve`` script
    (or a bare ``loom_solve`` for the loop-free collapse) still closes.
  * ADMISSIBILITY — neither method carries a ``require`` clause (both
    ``pre-conditions`` regions are empty), so the nagini "a normal input
    satisfies the precondition" probe has no precondition to over-constrain. The
    residual risk is a DEGENERATE post-image — a spec no impl can meet reads like
    a spec every impl meets. ``admiss-grounded`` discharges an in-region assert
    pinning ``flattenSeq`` AND ``canonicalize`` at concrete inputs (a two-source
    lineage concatenates BOTH sources; an all-annotation assembly canonicalizes
    to the annotations; an assembly with a foreign element is REFUSED naming it;
    a refusal at one element differs from a refusal at another; a refusal differs
    from any collected sequence), establishing that both halves of the post-image
    are non-degenerate and that the two outcome constructors are genuinely
    distinguishable. The surrounding impl and the byte-identical clause are kept
    verbatim so the method's own obligation still discharges; the assert is LIVE
    (a false claim about the same points leaves an unsolved goal — measured).
  * FRAME / PERMISSION-MUTATION — VACUOUS here. The nagini sibling passes both
    inputs as pure mathematical VALUE types (an immutable Seq and a scalar) with
    NO heap reference and NO fractional permission anywhere, and explicitly notes
    the canonical half-permission frame-mutation probe cannot even be expressed.
    Lean/Velvet are referentially transparent: every input is an immutable value,
    no binder is ``mut``, there is no heap and no aliasing — so there is likewise
    no read-only field to overwrite and no substitute probe to build. Not
    fabricated (porting map: this class is vacuous here).
  * DIVERGENCE / NON-TERMINATION: nothing to port, and CLOSED BY THE VERIFIER
    rather than genuinely vacuous. The nagini sibling carries NO
    ``diverge-*``/``nonterm-*``/``weak-diverge`` rival for this instance (its two
    inputs are value types with no ``MustTerminate`` divergence rival), so nothing
    is dropped in the port. The "genuinely vacuous" reason is withdrawn: a rival
    owns the whole impl region, and ``collectMarks``'s frozen body is itself a
    loop, so a non-terminating body IS writable here. It is REJECTED when it is.
    This bundle sets ``loom.semantics.termination "total"``, under which a
    postcondition is claimed of ALL runs, not only terminating ones, so the
    verifier demands a decreasing measure on every loop AND discharges its descent;
    the option cannot drift from the file's ``open TotalCorrectness DemonicChoice``,
    because the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with each proof
    reduced to a bare ``loom_solve``: a spliced loop with NO measure is refused at
    the ``method`` declaration
    (``Decreasing annotations are required in total correctness semantics``), and a
    loop CARRYING a non-decreasing measure
    (``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z``, body
    ``z := z + 1``) is refused on the measure's own goal:
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. There is also no velvet
    ``partial``-semantics known-hole to contrast with: all 500 velvet bundles set
    ``"total"`` and open ``TotalCorrectness``.
  * UNGROUNDED-ORACLE ECHO — N/A: both post-images are input-grounded (the
    canonicalization of a fold of a selection of the input, resp. of the input's
    head, extended with the new element), not an axiomatized oracle; the
    ``axioms`` region is empty. The one place an echo could hide is the
    canonicalizing step, and it is written out in full in the ``pure`` region
    (``markOf`` / ``consMark`` / ``canonicalize``, each a total recursive
    definition with ``@[grind]`` unfolding lemmas), not consumed as an opaque
    reference.

WITNESS MECHANICS (specific to this carrier). Each obligation is a ``method``
CONTRACT, not a bare predicate, so a witness reaches it through Velvet's own
tester machinery: ``collectMarksTester lineage wholeLineage = false`` (resp.
``attachMarkTester lineage mark = false``) says the extracted program's result
violates the postcondition at that concrete input, checked in a file whose
``prove_correct`` blocks have been stripped (no tactic script can mask the
verdict). Every input uses small ``Item``/``Int`` literals and boolean literals
over types that ``deriving DecidableEq`` (``Item``, ``Outcome``), so a LOOP-FREE
tester kernel-reduces under ``decide``.

THE FROZEN SOLUTION CANNOT SERVE AS THE SECOND SUBJECT, and this is the load-
bearing fact about every reject case here. The frozen ``collectMarks`` program
contains a ``while`` loop, which under ``loom.semantics.choice "demonic"``
elaborates through ``Classical.choice``; the kernel cannot unfold that, so
``decide`` on ``collectMarksTester ...`` is STUCK against the frozen solution for
EVERY claim, true or false. The frozen ``attachMark`` delegates to that same
loop-bearing callee, so ``attachMarkTester ...`` is stuck against gold too. A
gold-side exit 1 of that shape carries NO information: it is the
``witness-undecided`` defect class, not a refutation. Measured (real builds) with
the shape

    Tactic `decide` failed for proposition <tester ...> = false
    ... did not reduce to `isTrue` or `isFalse`.

So every reject case names an explicit ``witness_reference``: ``_CM_CLOSED_FORM``,
the loop-free closed-form impl of this same frozen spec (the module of
``pos-cm-closed-form``, which the battery independently requires to VERIFY, and
which the gate re-checks shares the frozen spec and verifies before using). Its
``collectMarks`` is loop-free and its ``attachMark`` delegates only to that
loop-free callee, so BOTH testers kernel-reduce against it. An impl the verifier
accepts cannot violate its own spec, so a genuine witness must still fail there —
and it fails by DECIDING, which is the refutation the record is supposed to
attest. Measured for every reject case: the reference-side build reports

    Tactic `decide` proved that the proposition <tester ...> = false is false

i.e. the tester is TRUE (the postcondition holds) at that input on a correct
impl, while it is FALSE on the rival. Exit codes seen with real builds: rival 0,
reference 1 (by refutation), frozen solution 1 (by stuck reduction — which is
why it is not the subject).

ONE CONSEQUENCE FOR ``attachMark`` RIVALS. A rival that keeps the delegation
``let own ← collectMarks lineage false`` inherits the callee's loop, so ITS
tester is stuck too and the case would attest nothing. Measured on
``uniq-am-record-over-refusal``: with the frozen looping ``collectMarks`` the
rival-side build failed with the same ``did not reduce to `isTrue` or `isFalse```
shape. Such a rival is therefore built on top of ``_CM_CLOSED_FORM`` — the
loop-free but CORRECT ``collectMarks`` — with only its ``attachMark`` body wrong,
so the delegation is preserved, the deviation is the attachMark one, and the
tester reduces. (Rebuilt that way: rival exit 0, and the variant still FAILS to
verify with the attachMark goal
``(match x with | Outcome.refused offending => Outcome.collected [mark] | ...) =
withMark (canonicalize (lineage.headD [])) mark`` unsolved.)

The witnesses are input-specific, not tautologies: refuting a rival at a point
where it AGREES with the spec was built and FAILS (exit 1, ``decide`` proved the
claim false), e.g. ``collectMarksTester [[Item.canonical 1]] true`` against
``uniq-class-only-prepatch`` (a single-source lineage, where returning the first
source IS the whole assembly) and ``attachMarkTester [[Item.canonical 7]] 3``
against ``uniq-am-absorb-lineage``. No witness binds a hypothesis (the carrier is
fully transparent — all inputs are concrete literals), so there is no
joint-satisfiability obligation.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``, and — unlike the
earlier revision of this bundle — nothing is folded away as a convenience either.
The canonicalizing step is modeled DEEPLY (``markOf`` / ``consMark`` /
``canonicalize`` in the ``pure`` region, including the refusal), as is the
assembly it is applied to (``flattenSeq`` + the verified backward fold). Both
deep models are validated against the real sub-computations out of band
(axiom_check.py / G-AX for the element-by-element canonicalization and its
refusal; conformance_check.py / G-CONF for the R/I assembly and selection legs).
Nothing in either proof rests on an axiom, and this gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-10356"
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

# The WHOLE executable body of collectMarks: select the contributing sources
# (the whole lineage, or only the first), concatenate them via a backward
# accumulating loop that prepends each source's raw elements, then canonicalize
# the assembly. Reject rivals replace this with a loop-free closed form (so their
# tester reduces under `decide`); the loop-free positive control does too.
_CM_IMPL = """    -- impl-start
    -- Select which sources contribute: the whole lineage, or only the class's
    -- own list; then concatenate the selected sources in order. The fold runs
    -- from the back, prepending each source's elements before those already
    -- gathered, yielding their in-order concatenation. The assembled elements
    -- are canonicalized before they leave.
    let selected : List (List Item) :=
      if wholeLineage then lineage else [lineage.headD []]
    let mut gathered : List Item := []
    let mut i := selected.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ selected.length
      invariant gathered = flattenSeq (selected.drop i)
      done_with i = 0
      decreasing i
    do
      let g := selected[i - 1]!
      gathered := g ++ gathered
      i := i - 1
    return canonicalize gathered
    -- impl-end"""
assert _BASE.count(_CM_IMPL) == 1, "frozen collectMarks impl region drifted"

# The FULL frozen collectMarks proof body (everything after the
# `prove_correct collectMarks by` header). A positive control that collapses the
# loop to the closed form the post-image names retunes this; the tactic body is
# elided from the spec view, so this is a proof reshape, not a spec change.
_CM_PROOF = """prove_correct collectMarks by
  loom_solve
  rw [flattenSeq_drop_step
        (if wholeLineage = true then lineage else [lineage.headD []]) i
        (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_CM_PROOF) == 1, "frozen collectMarks proof body drifted"

_CM_PROOF_BARE = "prove_correct collectMarks by\n  loom_solve"

# The first executable line of the collectMarks impl region; an in-region assert
# prepended here is discharged by the (retuned) proof without disturbing the
# method's own obligation.
_CM_TOP = "    let selected : List (List Item) :="
assert _BASE.count(_CM_TOP) == 1, "collectMarks impl-top anchor drift"

# The WHOLE executable body of attachMark: collect the class's OWN raw elements
# (without the lineage) and extend the resulting outcome with the new annotation.
_AM_IMPL = """    -- impl-start
    let own ← collectMarks lineage false
    return withMark own mark
    -- impl-end"""
assert _BASE.count(_AM_IMPL) == 1, "frozen attachMark impl region drifted"

# The shared first two lines of every rival that keeps the source selection.
_SEL = ("    let selected : List (List Item) :=\n"
        "      if wholeLineage then lineage else [lineage.headD []]\n")


def _cm(body):
    """collectMarks variant (impl body replaced, frozen proof kept)."""
    return _swap(_BASE, _CM_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _cm_bareproof(body):
    """collectMarks variant with a loop-free impl and a bare loom_solve proof
    (the loop-specific drop-step rewrite has no goal to close once the impl is
    loop-free)."""
    return _swap(_swap(_BASE, _CM_IMPL,
                       "    -- impl-start\n" + body + "\n    -- impl-end"),
                 _CM_PROOF, _CM_PROOF_BARE)


def _am(body):
    """attachMark variant (impl body replaced, frozen proof kept)."""
    return _swap(_BASE, _AM_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


# The WITNESS SUBJECT for every reject case: the loop-free closed-form impl of
# this same frozen spec (also shipped as the `pos-cm-closed-form` positive, so the
# battery independently asserts it verifies). The frozen solution cannot be the
# subject — its `while` loop elaborates through `Classical.choice`, so `decide` on
# its tester is stuck for every claim and its exit code discriminates nothing (see
# WITNESS MECHANICS). This impl's collectMarks is loop-free and its attachMark
# delegates only to that loop-free callee, so BOTH testers kernel-reduce here.
_CM_CLOSED_FORM = _cm_bareproof(
    "    return canonicalize (flattenSeq (if wholeLineage then lineage "
    "else [lineage.headD []]))")


def _am_on_closed_form(body):
    """An attachMark rival that KEEPS the delegation to collectMarks. Built on
    the loop-free-but-correct collectMarks so the attachMark tester reduces (with
    the frozen looping callee it is stuck and attests nothing — measured). Only
    the attachMark body deviates."""
    return _swap(_CM_CLOSED_FORM, _AM_IMPL,
                 "    -- impl-start\n" + body + "\n    -- impl-end")


# ---- witness preambles. Reach each method contract through Velvet's tester
# ---- machinery: `<name>Tester <args> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. No
# ---- axiom/sorry/native_decide; every witness `decide`s on small literals over
# ---- `deriving DecidableEq` types.
def _cm_wit(call):
    return ("extract_program_for collectMarks\n"
            "prove_precondition_decidable_for collectMarks\n"
            "prove_postcondition_decidable_for collectMarks\n"
            "derive_tester_for collectMarks\n\n"
            f"example : {call} = false := by\n  decide\n")


def _am_wit(call):
    return ("extract_program_for attachMark\n"
            "prove_precondition_decidable_for attachMark\n"
            "prove_postcondition_decidable_for attachMark\n"
            "derive_tester_for attachMark\n\n"
            f"example : {call} = false := by\n  decide\n")


# A proof that ALSO clears an in-region decidable `assert` VC, keeping the loop's
# drop-step arm for the method obligation. Used by admissibility.
_CM_PROOF_ADM = (
    "prove_correct collectMarks by\n"
    "  loom_solve <;>\n"
    "    first\n"
    "    | decide\n"
    "    | (rw [flattenSeq_drop_step\n"
    "          (if wholeLineage = true then lineage else [lineage.headD []]) i\n"
    "          (by omega) (by omega)]; simp_all)\n"
    "    | simp_all")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG on the impl shape. Each keeps its byte-identical `ensures`
    # obligation and only reshapes the executable surface (verified with real
    # builds).
    # =====================================================================
    {
        "id": "pos-cm-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating backward loop into the closed form the
        # post-image names directly. A maximally different control-flow shape (no
        # loop, no accumulator); the loop-specific drop-step rewrite has no goal
        # left, so the proof is retuned to a bare loom_solve.
        "module": _CM_CLOSED_FORM,
        "rationale": "a loop-free impl that canonicalizes the selected-source "
                     "assembly directly must satisfy `out = canonicalize "
                     "(flattenSeq (if wholeLineage then lineage else "
                     "[lineage.headD []]))`; a correct reshape of the modeled "
                     "behaviour verifying is exactly what SPEC-TOO-STRONG would "
                     "deny. Exercises the load-bearing obligation, including the "
                     "canonicalizing gate, from a loop-free shape. (Sibling: "
                     "pos-control-direct.)",
    },
    {
        "id": "pos-cm-loop-inline",
        "kind": "soundness",
        "expect": "verify",
        # Keep the gold BACKWARD loop and its invariants verbatim (the
        # front-recursive fold discharges with one unfold per step, so the frozen
        # proof stays valid — no forward-append lemma needed) but inline the
        # per-step source binding: prepend `selected[i-1]!` directly instead of
        # binding it to `g` first. Same value flow; the frozen script still
        # discharges.
        "module": _cm(
            _SEL +
            "    let mut gathered : List Item := []\n"
            "    let mut i := selected.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ selected.length\n"
            "      invariant gathered = flattenSeq (selected.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      gathered := selected[i - 1]! ++ gathered\n"
            "      i := i - 1\n"
            "    return canonicalize gathered"),
        "rationale": "a structural reshape of the gold backward loop that inlines "
                     "the per-step source (prepend `selected[i-1]!` directly) "
                     "while keeping the gold direction and the gold invariants "
                     "verbatim, so the loop invariant still proves and the frozen "
                     "loom_solve + drop-step script still closes. A faithful "
                     "reshape MUST verify, else the clause is over-fit to the "
                     "`let g := ...` FORM => SPEC-TOO-STRONG. (Sibling: "
                     "pos-control-reshape.)",
    },
    {
        "id": "pos-cm-rebuild-outcome",
        "kind": "soundness",
        "expect": "verify",
        # Destructure the canonicalization's OUTCOME and rebuild it constructor by
        # constructor (refusal -> the same refusal with the same offending token;
        # collected -> the same sequence). Value-identical, but it forces the
        # obligation to be discharged through a case split on `Outcome` rather
        # than by a single rewrite: if the clause were somehow only pinning one
        # constructor, this control would still verify while a real reshape of the
        # other one could not. (A do-block `match` on a COMPOUND scrutinee is not
        # supported by the WP generator here — measured: `Failed to parse an
        # assertion without names: WPGen (match canonicalize (...) with ...)` — so
        # the match is bound as a pure term first and the bound value returned.)
        "module": _cm_bareproof(
            _SEL +
            "    let rebuilt : Outcome :=\n"
            "      match canonicalize (flattenSeq selected) with\n"
            "      | Outcome.refused n    => Outcome.refused n\n"
            "      | Outcome.collected ms => Outcome.collected ms\n"
            "    return rebuilt"),
        "rationale": "an impl that takes the canonicalization apart and puts it "
                     "back together unchanged — preserving BOTH the refusal (with "
                     "its offending token) and the collected sequence — computes "
                     "the same `Outcome` and must verify. If it could not, the "
                     "clause would be over-fit to the un-destructured FORM of the "
                     "outcome => SPEC-TOO-STRONG, and the two-constructor carrier "
                     "the repair introduced would be unusable by any honest impl. "
                     "(New: defends the Outcome carrier itself.)",
    },
    {
        "id": "pos-am-direct",
        "kind": "soundness",
        "expect": "verify",
        # attachMark reshaped to DROP the delegation entirely: canonicalize the
        # class's own existing list inline (the first lineage element) and extend
        # with the new annotation, with no call to the collection at all. A real
        # shape change — the frozen body reaches its own list THROUGH the own-only
        # branch of the collection, so the frozen proof must apply the generated
        # collectMarks_correct; here there is no callee obligation to apply and the
        # value equality has to close directly.
        "module": _am("    return withMark (canonicalize (lineage.headD [])) mark"),
        "rationale": "canonicalizing the class's own existing list INLINE (the "
                     "first lineage element) instead of obtaining it from the "
                     "own-only branch of the collection yields the same outcome, "
                     "so `out = withMark (canonicalize (lineage.headD [])) mark` "
                     "still holds and loom_solve closes it with no callee "
                     "obligation to apply. A correct impl that does not delegate "
                     "must verify, else the clause is over-fit to the DELEGATING "
                     "shape => SPEC-TOO-STRONG. (New: defends the attachMark "
                     "obligation, which the nagini sibling did not model as a "
                     "separate contract.)",
    },
    {
        "id": "pos-am-explicit-cases",
        "kind": "soundness",
        "expect": "verify",
        # attachMark keeping the delegation but branching EXPLICITLY on the two
        # outcome shapes instead of using withMark: a refusal is propagated
        # unchanged (same offending token), a collected sequence is extended. This
        # is the shape a real implementer writes when the failure is an exception
        # rather than a value, so it must verify.
        "module": _am(
            "    let own ← collectMarks lineage false\n"
            "    match own with\n"
            "    | Outcome.refused n    => return Outcome.refused n\n"
            "    | Outcome.collected ms => return Outcome.collected (ms ++ [mark])"),
        "rationale": "propagating a refusal unchanged and extending a collected "
                     "sequence is exactly `withMark`, so the clause still holds. "
                     "It must verify: an honest impl that handles the refusal path "
                     "by an explicit case split rather than by the helper cannot "
                     "be refused => otherwise SPEC-TOO-STRONG on the refusal "
                     "handling, which is the very content the repair added. (New: "
                     "defends the refusal-propagation clause from the impl side.)",
    },

    # =====================================================================
    # ADMISSIBILITY — neither method has a `require` clause, so the "a normal
    # input satisfies the precondition" probe is not where the risk sits. The
    # residual risk is a DEGENERATE post-image (a spec no impl can meet reads like
    # a spec every impl meets). This case discharges an in-region assert at
    # concrete inputs establishing that `flattenSeq` really CONCATENATES both
    # sources of a two-source lineage, that `canonicalize` really extracts the
    # annotations of an all-annotation assembly, that it REFUSES naming the first
    # offender when an element makes no annotation available, and that the
    # resulting outcomes are pairwise distinct. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the assert is live
    # (a false claim about the same points leaves an unsolved goal — measured),
    # and the proof gains one `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _CM_TOP,
                  "    assert (with_name_prefix `adm\n"
                  "      (flattenSeq [[Item.canonical 1], [Item.wrapped 2]]\n"
                  "         = [Item.canonical 1, Item.wrapped 2] ∧\n"
                  "       canonicalize [Item.canonical 1, Item.wrapped 2] "
                  "= Outcome.collected [1, 2] ∧\n"
                  "       canonicalize [Item.canonical 1, Item.foreign 9] "
                  "= Outcome.refused 9 ∧\n"
                  "       canonicalize [Item.foreign 8, Item.foreign 9] "
                  "= Outcome.refused 8 ∧\n"
                  "       (Outcome.collected [1, 2]) ≠ Outcome.refused 9 ∧\n"
                  "       (Outcome.refused 8) ≠ Outcome.refused 9))\n"
                  + _CM_TOP),
            _CM_PROOF, _CM_PROOF_ADM),
        "rationale": "the post-image is non-degenerate at every interesting point: "
                     "`flattenSeq` CONCATENATES both sources of a two-source "
                     "lineage; `canonicalize` takes the annotation OUT of each "
                     "element (both the already-canonical and the wrapped shape) "
                     "and yields the annotation sequence [1,2]; on an assembly "
                     "holding an element that makes no annotation available it "
                     "REFUSES naming that element (9), and with two such elements "
                     "it names the FIRST (8, not 9); a collected outcome differs "
                     "from a refusal, and refusals naming different elements "
                     "differ. So both outcome constructors are inhabited and "
                     "distinguishable and the refusal carries real information — "
                     "without this the whole canonicalizing differential could be "
                     "degenerate. The in-region assert must discharge (else the "
                     "obligation is degenerate / PRECOND-TOO-STRONG at the point "
                     "that matters); the impl is kept verbatim so the clause still "
                     "verifies. (Sibling: admiss-f2p-shaped-input, re-aimed — no "
                     "precondition exists to over-constrain on this carrier.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart would
    # NOT resolve (either the target test, or an existing behaviour it must not
    # break).
    #
    # GROUP 1 — the BREADTH differential (which sources contribute).
    # =====================================================================
    {
        "id": "uniq-class-only-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE FIRST CENTRAL RIVAL. Canonicalize only the class's own list (the
        # first source) in BOTH branches — even when the whole lineage is
        # considered. This is the pre-image single-source read.
        "module": _cm_bareproof("    return canonicalize (lineage.headD [])"),
        "refinement": "this IS the pre-image behaviour: the collection read a "
                      "single resolution-order-nearest source and returned only "
                      "ONE source's annotations. The failing test builds a class "
                      "inheriting from two independently-annotated base classes "
                      "and asserts the collected annotations include BOTH "
                      "ancestors', in resolution order; returning only the first "
                      "source's annotations yields just one and the assertion "
                      "fails. Its faithful real counterpart (the un-patched "
                      "single-source read) is exactly what does NOT resolve.",
        "rationale": "REJECT from `out = canonicalize (flattenSeq (if wholeLineage "
                     "then lineage else [lineage.headD []]))`: on wholeLineage=true "
                     "the spec pins the canonicalization of the FULL assembly, but "
                     "the rival canonicalizes only the first source, which differs "
                     "whenever a later source is non-empty. If it verified the spec "
                     "would admit the pre-image behaviour => SPEC-TOO-WEAK. "
                     "Refuted at lineage=[[canonical 1],[canonical 2]], "
                     "wholeLineage=true: a correct impl collects [1,2], the rival "
                     "collects [1].",
        "witness": _cm_wit(
            "collectMarksTester [[Item.canonical 1], [Item.canonical 2]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: on the whole-lineage branch, assemble only the
        # ANCESTORS (drop the first source). Correct on the own-only branch and on
        # the ancestor suffix, wrong on the first source.
        "module": _cm_bareproof(
            "    let selected : List (List Item) :=\n"
            "      if wholeLineage then lineage.tail else [lineage.headD []]\n"
            "    return canonicalize (flattenSeq selected)"),
        "refinement": "drops the class's OWN annotations, returning only the "
                      "ancestors' assembly (the tail of the resolution order). A "
                      "counterpart that collected the ancestors while skipping the "
                      "class itself would lose the directly-applied annotations; "
                      "on the failing test's shape the collected list would omit "
                      "the class's own annotation and the ordered-equality "
                      "assertion fails — it does NOT resolve.",
        "rationale": "REJECT from the collectMarks clause: on wholeLineage=true "
                     "the rival canonicalizes `flattenSeq lineage.tail`, which "
                     "differs from `flattenSeq lineage` whenever the first source "
                     "is non-empty. Partial-domain: correct on the ancestor "
                     "suffix, wrong on the first source. Refuted at "
                     "lineage=[[canonical 3],[canonical 4],[canonical 5]], "
                     "wholeLineage=true: correct [3,4,5], rival [4,5] — a distinct "
                     "(length-3) input point. (Sibling: uniq-drop-first.)",
        "witness": _cm_wit("collectMarksTester [[Item.canonical 3], "
                           "[Item.canonical 4], [Item.canonical 5]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: on the whole-lineage branch, assemble every source
        # EXCEPT the deepest (drop the last element). Correct on the prefix, wrong
        # on the final source.
        "module": _cm_bareproof(
            "    return canonicalize (flattenSeq (if wholeLineage then "
            "lineage.dropLast else [lineage.headD []]))"),
        "refinement": "drops the DEEPEST source's annotations (the last entry of "
                      "the resolution order). A counterpart that iterated the "
                      "resolution order but skipped its last entry would lose the "
                      "final ancestor's annotations; on a lineage whose deepest "
                      "source carries annotations the collected list is missing "
                      "them and the ordered-equality assertion fails — it does "
                      "NOT resolve.",
        "rationale": "REJECT from the collectMarks clause: on wholeLineage=true "
                     "the rival omits the last source, so it differs whenever that "
                     "source is non-empty. Partial-domain: correct on the prefix, "
                     "wrong on the final source. Refuted at "
                     "lineage=[[canonical 8],[canonical 9]], wholeLineage=true: "
                     "correct [8,9], rival [8]. (Sibling: uniq-drop-last.)",
        "witness": _cm_wit(
            "collectMarksTester [[Item.canonical 8], [Item.canonical 9]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-swap-branches",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow: swap the two flag branches — assemble the whole lineage
        # when it is NOT to be considered, and only the first source when it IS.
        # Wrong on BOTH flag values; refuted here on the wholeLineage=FALSE branch.
        "module": _cm_bareproof(
            "    return canonicalize (flattenSeq (if wholeLineage then "
            "[lineage.headD []] else lineage))"),
        "refinement": "swaps the two branches — the whole-lineage flag is routed "
                      "backwards. When the whole lineage should be considered it "
                      "returns only the first source (the failing test's primary "
                      "assertion fails), and when only the class's own annotations "
                      "should be returned it returns the whole lineage — so the "
                      "operation that records a freshly-applied annotation would "
                      "absorb the ancestors' annotations into the class's own "
                      "list, double-counting. It does NOT resolve.",
        "rationale": "control-flow-effect: REJECT from the collectMarks clause on "
                     "BOTH flag values. Refuted on the OWN-ONLY branch "
                     "(wholeLineage=false): the spec pins the canonicalization of "
                     "`flattenSeq [lineage.headD []]` (the first source) but the "
                     "rival canonicalizes the whole lineage. One of only two "
                     "witnesses with wholeLineage=false, so it is part of what "
                     "varies that binder — a rival mishandling only the own-only "
                     "branch would otherwise slip through. Refuted at "
                     "lineage=[[canonical 1],[canonical 2]], wholeLineage=false: "
                     "correct [1], rival [1,2]. (Sibling: uniq-swap-branches.)",
        "witness": _cm_wit(
            "collectMarksTester [[Item.canonical 1], [Item.canonical 2]] false"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-reorder",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-level ordering attack: on the whole-lineage branch build the same
        # multiset of elements in the WRONG order — the ancestors first, the
        # class's own source appended last. Same tokens, reversed groups.
        "module": _cm_bareproof(
            _SEL +
            "    return canonicalize (flattenSeq selected.tail ++ "
            "(selected.headD []))"),
        "refinement": "produces the same annotations in the WRONG order — the "
                      "ancestors' annotations first, the class's own appended "
                      "last. A counterpart that assembled the ancestor lists "
                      "before the class's own list would yield the collected "
                      "annotations in ancestors-first order, but the failing test "
                      "asserts the class's own annotation comes FIRST (resolution "
                      "order, class first); the ordered-list equality fails — it "
                      "does NOT resolve.",
        "rationale": "value-level ordering attack: REJECT from the collectMarks "
                     "clause (element-wise, ordered equality inside "
                     "`Outcome.collected`). The rival contains the same tokens as "
                     "the correct assembly but in reversed-group order, so it "
                     "diverges whenever the first and later sources are distinct "
                     "and non-empty. A spec pinning only membership/multiset/"
                     "length would MISS this => SPEC-TOO-WEAK. Refuted at "
                     "lineage=[[canonical 5],[canonical 6]], wholeLineage=true: "
                     "correct [5,6], rival [6,5]. (Sibling: uniq-reorder.)",
        "witness": _cm_wit(
            "collectMarksTester [[Item.canonical 5], [Item.canonical 6]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-len1-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting partial-domain near-miss: return the assembly only when >1
        # source is selected, else an empty collection. Correct on multi-source
        # lineages, wrong on the length-1 sub-domain (a class with no annotated
        # ancestors, just its own annotations).
        "module": _cm_bareproof(
            _SEL +
            "    if selected.length > 1 then\n"
            "      return canonicalize (flattenSeq selected)\n"
            "    else\n"
            "      return Outcome.collected []"),
        "refinement": "short-circuits a single-source lineage to an empty "
                      "collection: a lone annotated class with no annotated "
                      "ancestors would collect NO annotations instead of its own. "
                      "That breaks the accumulation the operation recording a "
                      "freshly-applied annotation relies on (a standalone "
                      "annotated class loses its annotation), so the existing "
                      "single-class behaviour regresses — it does NOT resolve.",
        "rationale": "REJECT from the collectMarks clause on the length-1 "
                     "sub-domain: for a single-source selection the spec pins the "
                     "canonicalization of that source (non-empty when the class "
                     "carries its own annotation), but the rival returns an empty "
                     "collection. Partial-domain: the failing input is the "
                     "smallest legitimate one (a length-1 lineage). Refuted at "
                     "lineage=[[canonical 4]], wholeLineage=true: correct [4], "
                     "rival []. (Sibling: uniq-len1-empty.)",
        "witness": _cm_wit("collectMarksTester [[Item.canonical 4]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-stop-at-empty-source",
        "kind": "uniqueness",
        "expect": "reject",
        # Assemble the selected sources only up to the FIRST source that
        # contributes nothing, then stop. Agrees with the spec on every lineage
        # whose sources are all non-empty — i.e. on the input point of most other
        # rivals here — and diverges only when an empty source sits before a
        # non-empty one.
        "module": _cm_bareproof(
            "    return canonicalize (flattenSeq ((if wholeLineage then lineage "
            "else [lineage.headD []]).takeWhile (fun g => !g.isEmpty)))"),
        "refinement": "stops the assembly at the first source that contributes "
                      "nothing instead of skipping it. A counterpart that broke "
                      "out of the resolution-order walk on the first "
                      "un-annotated entry would silently lose every annotation "
                      "beyond it — and an un-annotated intermediate entry is the "
                      "common case, since most entries in a resolution order "
                      "carry no annotations at all. On the failing test's shape "
                      "the collected list would be truncated at the first plain "
                      "entry and the ordered-equality assertion fails — it does "
                      "NOT resolve.",
        "rationale": "REJECT from the collectMarks clause on a sub-domain most "
                     "other rivals leave untouched: the clause SKIPS an empty "
                     "source without ending the assembly, so it is pinned to the "
                     "full assembly even when an interior source is empty. This "
                     "rival truncates there. Partial-domain, and a strictly "
                     "sharper near-miss than uniq-drop-last: it agrees with the "
                     "spec on EVERY all-non-empty lineage. Refuted at "
                     "lineage=[[canonical 1],[],[canonical 2]], wholeLineage=true: "
                     "correct [1,2], rival [1].",
        "witness": _cm_wit("collectMarksTester [[Item.canonical 1], [], "
                           "[Item.canonical 2]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },

    # =====================================================================
    # GROUP 2 — the CANONICALIZING GATE differential. Every rival here is
    # BREADTH-correct: it assembles exactly the right sources in exactly the right
    # order, and would satisfy the earlier revision of this spec, which modeled
    # the canonicalizing step as the identity. Each mishandles an element that
    # makes no annotation available, and each must be rejected.
    # =====================================================================
    {
        "id": "uniq-skip-foreign",
        "kind": "uniqueness",
        "expect": "reject",
        # THE SECOND CENTRAL RIVAL. Drop the canonicalizing gate: keep only the
        # elements that make an annotation available and collect those, so an
        # element that makes none is silently skipped instead of refusing the
        # collection. Correct on every all-annotation assembly.
        "module": _cm_bareproof(
            _SEL +
            "    return Outcome.collected ((flattenSeq selected).filterMap markOf)"),
        "refinement": "this is the behaviour a counterpart gets by deleting the "
                      "canonicalizing step from the collection's exit and "
                      "returning the assembled list as it stands (or by filtering "
                      "it): an element that is not an annotation and carries none "
                      "is silently accepted/dropped rather than refused. An "
                      "existing test asserts precisely the opposite — a source "
                      "whose attached list holds such an element must make the "
                      "collection FAIL, with the offending element named — so a "
                      "counterpart doing this breaks that test. It resolves the "
                      "target test (breadth is untouched) and regresses an "
                      "existing one, so it does NOT resolve the instance.",
        "rationale": "REJECT from `out = canonicalize (flattenSeq ...)`: "
                     "`canonicalize` yields `Outcome.refused (nameOf it)` on the "
                     "first element with `markOf it = none`, while the rival yields "
                     "`Outcome.collected` of the surviving annotations. This is the "
                     "differential the repair added: under the earlier revision "
                     "(canonicalization folded as the identity) this rival "
                     "VERIFIED and its refinement broke an existing test, which is "
                     "exactly SPEC-TOO-WEAK. Refuted at "
                     "lineage=[[foreign 7]], wholeLineage=true: the spec demands "
                     "refused 7, the rival collects [].",
        "witness": _cm_wit("collectMarksTester [[Item.foreign 7]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-substitute-for-foreign",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-approximation: instead of refusing, SUBSTITUTE a default annotation
        # for any element that makes none available, keeping the length and
        # positions of the assembly.
        "module": _cm_bareproof(
            _SEL +
            "    return Outcome.collected ((flattenSeq selected).map "
            "(fun it => (markOf it).getD 0))"),
        "refinement": "fabricates an annotation for an element that carries none "
                      "instead of refusing. A counterpart that coerced every "
                      "assembled element into some annotation would accept a "
                      "source holding an arbitrary object and report a "
                      "meaningless annotation for it, so the existing behaviour "
                      "that such a source makes the collection fail is lost, and "
                      "downstream every consumer sees an annotation that was never "
                      "applied. It does NOT resolve.",
        "rationale": "REJECT from the collectMarks clause: the spec pins `refused`, "
                     "the rival pins a `collected` sequence of the same length as "
                     "the assembly with a fabricated entry. A near-miss that keeps "
                     "positions and length — so a spec pinning only length or only "
                     "the annotation POSITIONS would MISS it => SPEC-TOO-WEAK. "
                     "Refuted at lineage=[[foreign 7],[canonical 2]], "
                     "wholeLineage=true: the spec demands refused 7, the rival "
                     "collects [0,2].",
        "witness": _cm_wit("collectMarksTester [[Item.foreign 7], "
                           "[Item.canonical 2]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-check-head-source-only",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN GUARD: apply the canonicalizing gate, but only look for
        # offending elements in the FIRST source; if the first source is clean,
        # skip offenders coming from the ancestors. Correct whenever the offender
        # is in the class's own list.
        "module": _cm_bareproof(
            _SEL +
            "    if (selected.headD []).any (fun it => (markOf it).isNone) then\n"
            "      return canonicalize (flattenSeq selected)\n"
            "    else\n"
            "      return Outcome.collected ((flattenSeq selected).filterMap markOf)"),
        "refinement": "checks only the class's own list and lets an offending "
                      "element inherited from an ancestor through. A counterpart "
                      "that canonicalized the class's own contribution but "
                      "concatenated the ancestors' contributions unchecked would "
                      "accept a base class whose attached list holds a "
                      "non-annotation — the existing failure disappears exactly "
                      "when the offender is inherited, which is the harder case to "
                      "notice. It does NOT resolve.",
        "rationale": "REJECT from the collectMarks clause: the clause applies "
                     "`canonicalize` to the WHOLE assembly, not to its first "
                     "source. A partial-domain guard — indistinguishable from the "
                     "spec whenever the first source contains the offender (and on "
                     "every all-annotation input), so only a witness whose "
                     "offender is in a LATER source can catch it. Refuted at "
                     "lineage=[[canonical 1],[foreign 7]], wholeLineage=true: the "
                     "spec demands refused 7, the rival collects [1].",
        "witness": _cm_wit("collectMarksTester [[Item.canonical 1], "
                           "[Item.foreign 7]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-check-whole-lineage",
        "kind": "uniqueness",
        "expect": "reject",
        # The MIRROR partial-domain error: canonicalize the right assembly, but
        # look for offending elements across the WHOLE lineage even on the
        # own-only branch, so a source that does not contribute can refuse a
        # collection it takes no part in. Correct on the whole-lineage branch.
        "module": _cm_bareproof(
            "    let res : Outcome :=\n"
            "      match (flattenSeq lineage).find? (fun it => (markOf it).isNone) with\n"
            "      | some it => Outcome.refused (nameOf it)\n"
            "      | none    => canonicalize (flattenSeq (if wholeLineage then "
            "lineage else [lineage.headD []]))\n"
            "    return res",
        ),
        "refinement": "applies the check to sources that do not contribute. A "
                      "counterpart that validated the entire resolution order "
                      "before returning only the class's own annotations would "
                      "make recording a new annotation on a class fail because "
                      "some unrelated ANCESTOR's attached list holds a "
                      "non-annotation — a class that was previously decorable "
                      "stops being decorable. It does NOT resolve.",
        "rationale": "REJECT from the collectMarks clause on the own-only branch: "
                     "the clause canonicalizes only the SELECTED assembly, so "
                     "elements of non-contributing sources cannot influence the "
                     "outcome. Over-approximation in the refusal direction (the "
                     "opposite error to uniq-check-head-source-only), and the "
                     "second of the two witnesses that move wholeLineage to false. "
                     "Refuted at lineage=[[canonical 1],[foreign 7]], "
                     "wholeLineage=false: the spec demands collected [1], the "
                     "rival refuses with 7.",
        "witness": _cm_wit("collectMarksTester [[Item.canonical 1], "
                           "[Item.foreign 7]] false"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-wrapped-as-foreign",
        "kind": "uniqueness",
        "expect": "reject",
        # BOUNDARY TOKEN SWAP: refuse anything that is not ALREADY a canonical
        # annotation — i.e. treat an applicator object carrying an annotation
        # inside it as an offender instead of taking the annotation out of it.
        # Correct on assemblies of already-canonical elements and on genuine
        # offenders; wrong exactly on the boundary shape.
        "module": _cm_bareproof(
            _SEL +
            "    let flat : List Item := flattenSeq selected\n"
            "    let res : Outcome :=\n"
            "      match flat.find? (fun it => it != Item.canonical (nameOf it)) with\n"
            "      | some it => Outcome.refused (nameOf it)\n"
            "      | none    => canonicalize flat\n"
            "    return res"),
        "refinement": "refuses the ordinary hand-written shape. A counterpart that "
                      "demanded every assembled element ALREADY be a canonical "
                      "annotation — instead of taking the annotation out of an "
                      "applicator object that carries one — would reject the most "
                      "common way a source's attached list is written by hand, so "
                      "collections that work today start failing. It does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = canonicalize (...)`: `markOf` makes an "
                     "annotation available for BOTH the already-canonical and the "
                     "wrapped shape (`markOf (Item.wrapped m) = some m`), so only "
                     "`foreign` may refuse. The rival's predicate is the boundary "
                     "swap `markOf it = none` -> `it ≠ canonical (nameOf it)`, "
                     "which agrees with the spec on every assembly with no wrapped "
                     "element. Refuted at lineage=[[wrapped 4]], "
                     "wholeLineage=true: the spec demands collected [4], the rival "
                     "refuses with 4.",
        "witness": _cm_wit("collectMarksTester [[Item.wrapped 4]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-empty-assembly-refused",
        "kind": "uniqueness",
        "expect": "reject",
        # Boundary: refuse the EMPTY assembly rather than collecting nothing.
        # Correct on every non-empty assembly, i.e. at the input point of every
        # other rival here.
        "module": _cm_bareproof(
            _SEL +
            "    if (flattenSeq selected).isEmpty then\n"
            "      return Outcome.refused 0\n"
            "    else\n"
            "      return canonicalize (flattenSeq selected)"),
        "refinement": "refuses a class with no annotations at all. A counterpart "
                      "that treated an empty assembly as an error would make "
                      "every un-annotated class fail collection — the "
                      "overwhelmingly common case — so essentially everything "
                      "breaks. It does NOT resolve.",
        "rationale": "REJECT from the collectMarks clause at the empty boundary: "
                     "`canonicalize [] = Outcome.collected []`, an EMPTY "
                     "COLLECTION, which is not a refusal. Pins that the refusal is "
                     "caused by an offending element and by nothing else — a spec "
                     "that only said 'refuses when something is wrong' would admit "
                     "this. Refuted at lineage=[[]], wholeLineage=true: the spec "
                     "demands collected [], the rival refuses with 0.",
        "witness": _cm_wit("collectMarksTester [[]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },

    # =====================================================================
    # GROUP 3 — the freedom the repair itself leaves. The refusal carries a
    # PAYLOAD (which element is named). These two rivals refuse exactly when the
    # spec refuses and collect exactly what the spec collects; they differ only in
    # WHICH offender the refusal names. If the spec left the payload
    # unconstrained, both would verify — so these are the cases that attest the
    # repair did not just move the hole one level down.
    # =====================================================================
    {
        "id": "uniq-refusal-names-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _cm_bareproof(
            _SEL +
            "    let flat : List Item := flattenSeq selected\n"
            "    let res : Outcome :=\n"
            "      match flat.reverse.find? (fun it => (markOf it).isNone) with\n"
            "      | some it => Outcome.refused (nameOf it)\n"
            "      | none    => canonicalize flat\n"
            "    return res"),
        "refinement": "names the LAST offending element instead of the first. A "
                      "counterpart that scanned the assembled list to completion "
                      "and reported the final offender would have to canonicalize "
                      "the whole assembly before failing; the existing behaviour "
                      "is that the walk stops at the first offender and reports "
                      "THAT one, and the existing test reads the reported "
                      "identity out of the failure. Reporting a different element "
                      "changes the observable failure, so it does NOT resolve.",
        "rationale": "REJECT from `out = canonicalize (...)`: `canonicalize` is "
                     "front-recursive and yields `refused (nameOf it)` for the "
                     "FIRST element with no annotation available, so the payload "
                     "is pinned, not merely the fact of refusal. Exploits the only "
                     "freedom the repair leaves (the refusal payload); agrees with "
                     "the spec on every assembly with at most one offender, hence "
                     "at the input point of every other gate rival here. Refuted "
                     "at lineage=[[foreign 7, foreign 8]], wholeLineage=true: the "
                     "spec demands refused 7, the rival refuses with 8.",
        "witness": _cm_wit(
            "collectMarksTester [[Item.foreign 7, Item.foreign 8]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-refusal-anonymous",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _cm_bareproof(
            _SEL +
            "    let res : Outcome :=\n"
            "      match canonicalize (flattenSeq selected) with\n"
            "      | Outcome.refused _ => Outcome.refused 0\n"
            "      | o                 => o\n"
            "    return res"),
        "refinement": "refuses at exactly the right times but reports no useful "
                      "identity — an anonymous failure. A counterpart that failed "
                      "without saying WHICH element was at fault would leave the "
                      "existing test's inspection of the failure with nothing to "
                      "match; the existing behaviour reports the offending object "
                      "itself. It does NOT resolve.",
        "rationale": "REJECT from the collectMarks clause: the refusal's payload is "
                     "`nameOf it` for the offending element, not a constant. This "
                     "is the ORACLE-ECHO-shaped attack on the repair — it computes "
                     "the correct refusal decision by calling the spec's own "
                     "canonicalization and then discards the one piece of "
                     "information the clause pins, so a spec that had merely said "
                     "`∃ n, out = refused n` would admit it. Refuted at "
                     "lineage=[[foreign 7]], wholeLineage=true: the spec demands "
                     "refused 7, the rival refuses with 0.",
        "witness": _cm_wit("collectMarksTester [[Item.foreign 7]] true"),
        "witness_reference": _CM_CLOSED_FORM,
    },

    # =====================================================================
    # GROUP 4 — the recording operation (attachMark).
    # =====================================================================
    {
        "id": "uniq-am-absorb-lineage",
        "kind": "uniqueness",
        "expect": "reject",
        # Record the freshly-applied annotation on top of the WHOLE lineage's
        # annotations instead of only the class's own. Loop-free (does not
        # delegate) so the tester reduces. Correct only when the lineage has a
        # single source.
        "module": _am(
            "    return withMark (canonicalize (flattenSeq lineage)) mark"),
        "refinement": "records the freshly-applied annotation on top of the WHOLE "
                      "lineage's annotations rather than only the class's own "
                      "existing ones. A counterpart that collected across the "
                      "resolution order before extending would absorb the "
                      "ancestors' annotations into the class's own stored list; "
                      "every subsequent collection would then double-count the "
                      "ancestors, so the resolution-order behaviour the change "
                      "establishes regresses — it does NOT resolve.",
        "rationale": "REJECT from `out = withMark (canonicalize (lineage.headD [])) "
                     "mark`: only the FIRST source (the class's own list) may "
                     "precede the new annotation, but the rival canonicalizes the "
                     "whole-lineage assembly, which differs whenever a later "
                     "source is non-empty. Isolates the head-only dependence of "
                     "the attachMark clause. Refuted at "
                     "lineage=[[canonical 1],[canonical 2]], mark=9: correct "
                     "[1,9], rival [1,2,9].",
        "witness": _am_wit(
            "attachMarkTester [[Item.canonical 1], [Item.canonical 2]] 9"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-am-drop-mark",
        "kind": "uniqueness",
        "expect": "reject",
        # Return only the class's own annotations, DROPPING the freshly-applied
        # one. Isolates the `mark` binder.
        "module": _am("    return canonicalize (lineage.headD [])"),
        "refinement": "returns only the class's existing own annotations and DROPS "
                      "the freshly-applied one. A counterpart that recomputed the "
                      "own annotations but forgot to extend with the new one would "
                      "never actually record it, so the annotation would be "
                      "silently lost and any behaviour depending on it regresses "
                      "— it does NOT resolve.",
        "rationale": "REJECT from the attachMark clause: the new annotation must be "
                     "appended, but the rival omits it. Isolates the `mark` binder. "
                     "Refuted at lineage=[[canonical 7]], mark=3: correct [7,3], "
                     "rival [7] — a distinct input point from "
                     "uniq-am-absorb-lineage, varying both `lineage` and `mark`.",
        "witness": _am_wit("attachMarkTester [[Item.canonical 7]] 3"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-am-empty-head",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong ONLY when the class has no own annotations yet: return an empty
        # collection instead of the singleton [mark].
        "module": _am(
            "    return (if (lineage.headD []).isEmpty then Outcome.collected [] "
            "else withMark (canonicalize (lineage.headD [])) mark)"),
        "refinement": "records nothing when the class has no own annotations yet, "
                      "returning an empty collection instead of the single new "
                      "annotation. A counterpart that short-circuited the "
                      "not-yet-annotated case would drop the FIRST annotation "
                      "applied to any class — the overwhelmingly common path, "
                      "since a class starts with no own annotations — so nothing "
                      "would ever be recorded on a fresh class and every "
                      "collection over it comes back empty. It does NOT resolve.",
        "rationale": "REJECT from the attachMark clause: for an empty first element "
                     "the clause pins `withMark (collected []) mark = collected "
                     "[mark]`, but the rival returns `collected []`. Partial-domain "
                     "on the empty-own-list sub-domain, which the other attachMark "
                     "rivals agree with the spec on (their witness points have "
                     "non-empty heads). Refuted at lineage=[[]], mark=5: correct "
                     "[5], rival [].",
        "witness": _am_wit("attachMarkTester [[]] 5"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-am-skip-foreign",
        "kind": "uniqueness",
        "expect": "reject",
        # The canonicalizing-gate attack aimed at the RECORDING site: drop the
        # gate when reading the class's own existing list, so an offending element
        # already sitting there is skipped and the new annotation is recorded on
        # top of a truncated list.
        "module": _am(
            "    return withMark (Outcome.collected ((lineage.headD []).filterMap "
            "markOf)) mark"),
        "refinement": "reads the class's own existing list WITHOUT the "
                      "canonicalizing gate, so an element there that is not an "
                      "annotation is silently dropped and the new annotation is "
                      "recorded on top of the remainder. This is the recording-site "
                      "half of the same deletion as uniq-skip-foreign: the "
                      "existing behaviour is that decorating such a class FAILS "
                      "and names the offending element, and an existing test "
                      "asserts exactly that. Silently rewriting the class's stored "
                      "list instead both hides the error and destroys data. It "
                      "does NOT resolve.",
        "rationale": "REJECT from `out = withMark (canonicalize (lineage.headD [])) "
                     "mark`: when the class's own list holds an element making no "
                     "annotation available the clause pins a REFUSAL (withMark "
                     "propagates it unchanged), but the rival collects the "
                     "survivors and appends. Attacks the gate at the second "
                     "obligation, which a rival could otherwise leave unguarded "
                     "even with collectMarks fully pinned. Refuted at "
                     "lineage=[[foreign 7]], mark=5: the spec demands refused 7, "
                     "the rival collects [5].",
        "witness": _am_wit("attachMarkTester [[Item.foreign 7]] 5"),
        "witness_reference": _CM_CLOSED_FORM,
    },
    {
        "id": "uniq-am-record-over-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps the delegation and the gate, but RECOVERS from the refusal:
        # records the new annotation as the class's only one instead of
        # propagating the failure. Built on the loop-free-but-correct collectMarks
        # so the attachMark tester reduces (see WITNESS MECHANICS).
        "module": _am_on_closed_form(
            "    let own ← collectMarks lineage false\n"
            "    let res : Outcome :=\n"
            "      match own with\n"
            "      | Outcome.refused _    => Outcome.collected [mark]\n"
            "      | Outcome.collected ms => Outcome.collected (ms ++ [mark])\n"
            "    return res"),
        "refinement": "swallows the refusal and overwrites the class's own list "
                      "with just the new annotation. A counterpart that caught the "
                      "failure while reading the existing list and started over "
                      "would turn a loud, existing, test-asserted failure into a "
                      "silent data loss: the offending element disappears from the "
                      "class's stored list and nothing is reported. It does NOT "
                      "resolve.",
        "rationale": "REJECT from the attachMark clause: `withMark` propagates a "
                     "refusal UNCHANGED (`withMark_refused`), so the clause "
                     "forbids recovering from it. Exploits the freedom a spec "
                     "would leave if it only pinned the collected case of the "
                     "recording operation; note it is BREADTH-correct, "
                     "GATE-correct and even correct on the whole collected "
                     "sub-domain, differing only on the refusal path. Refuted at "
                     "lineage=[[foreign 6]], mark=5: the spec demands refused 6, "
                     "the rival collects [5].",
        "witness": _am_wit("attachMarkTester [[Item.foreign 6]] 5"),
        "witness_reference": _CM_CLOSED_FORM,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness/partial-domain rivals) plus an EMPTY
# AXIOM lane, contracting ONE function (`unpacked_tokens` = the annotation
# collection) over pure VALUE inputs (an immutable Seq of Seqs + a bool) with no
# heap and no fractional permission. THIS bundle models a WIDER purely-functional
# surface — BOTH the collection (`collectMarks`) AND the operation that records a
# freshly-applied annotation (`attachMark`), which delegates to the collection —
# over the referentially-transparent carrier `List (List Item)` with the
# two-constructor result `Outcome`. So the six nagini collection rivals port
# directly to `collectMarks`, the second contracted function gets its own defence
# + attacks, and the canonicalizing gate (which the nagini sibling folded away as
# an identity, as this bundle's own earlier revision did) gets a full group.
#
#   sibling case (nagini)          -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-direct             -> pos-cm-closed-form            PORTED
#   pos-control-reshape            -> pos-cm-loop-inline            PORTED
#   admiss-f2p-shaped-input        -> admiss-grounded               RE-AIMED
#   uniq-class-only-prepatch       -> uniq-class-only-prepatch      PORTED (central 1)
#   uniq-drop-first                -> uniq-drop-first               PORTED
#   uniq-drop-last                 -> uniq-drop-last                PORTED
#   uniq-swap-branches             -> uniq-swap-branches            PORTED
#   uniq-reorder                   -> uniq-reorder                  PORTED
#   uniq-len1-empty                -> uniq-len1-empty               PORTED
#   AXIOM_TESTS (empty)            -> (none)                        DROPPED (G-AX)
#   (new, no sibling)              -> pos-cm-rebuild-outcome        ADDED (Outcome carrier)
#   (new, no sibling)              -> pos-am-direct                 ADDED (2nd obligation)
#   (new, no sibling)              -> pos-am-explicit-cases         ADDED (refusal path)
#   (new, no sibling)              -> uniq-am-absorb-lineage        ADDED (2nd obligation)
#   (new, no sibling)              -> uniq-am-drop-mark             ADDED (mark binder)
#   (new, no sibling)              -> uniq-stop-at-empty-source     ADDED (empty source)
#   (new, no sibling)              -> uniq-am-empty-head            ADDED (empty own list)
#   (new, no sibling)              -> uniq-skip-foreign             ADDED (central 2: the gate)
#   (new, no sibling)              -> uniq-substitute-for-foreign   ADDED (gate: substitution)
#   (new, no sibling)              -> uniq-check-head-source-only   ADDED (gate: partial domain)
#   (new, no sibling)              -> uniq-check-whole-lineage      ADDED (gate: over-approx)
#   (new, no sibling)              -> uniq-wrapped-as-foreign       ADDED (gate: token swap)
#   (new, no sibling)              -> uniq-empty-assembly-refused   ADDED (gate: empty boundary)
#   (new, no sibling)              -> uniq-refusal-names-last       ADDED (payload: first/last)
#   (new, no sibling)              -> uniq-refusal-anonymous        ADDED (payload: echo)
#   (new, no sibling)              -> uniq-am-skip-foreign          ADDED (gate at site B)
#   (new, no sibling)              -> uniq-am-record-over-refusal   ADDED (refusal recovery)
#
# WHY THE GATE GROUP EXISTS (the repair this battery is written against). The
# earlier revision of this bundle carried `abbrev Mark := Int` as the ELEMENT
# type, so a source's attached list could only hold canonical annotations, and the
# canonicalizing step the collection ends with was folded into the model as the
# IDENTITY. Two consequences, both bad: (i) the step's real content — every
# assembled element must make an annotation available, and the collection is
# refused naming the first that does not — was UNOBSERVABLE in the spec, and
# (ii) an impl (and a refinement of it) that deleted the step entirely satisfied
# the frozen spec. That was measured, not hypothesised: a rival identical to
# `uniq-skip-foreign` VERIFIED against the earlier spec, and its faithful
# counterpart broke an existing test that asserts a source holding a
# non-annotation makes the collection fail with the offending object named. The
# repair WIDENS the element domain (`Item` = already-canonical | wrapped |
# foreign) and makes the result a two-constructor `Outcome` (collected | refused
# with the offending token), then states both clauses through `canonicalize`. No
# precondition was added and nothing was narrowed — the previously-modeled inputs
# are exactly the all-`canonical` sub-domain, on which every clause says what it
# said before. GROUP 2 attacks the gate itself, GROUP 3 attacks the freedom the
# gate's payload leaves, and GROUP 4's last two cases attack the gate at the
# recording site.
#
# PORTED (pos-cm-closed-form): the nagini "cheapest honest impl" (return the fold
#   directly) ports as the loop-free closed form; the loop-specific drop-step
#   rewrite has no goal left, so the proof is retuned to a bare loom_solve. This
#   module doubles as `_CM_CLOSED_FORM`, the witness subject every reject case
#   names (see WITNESS MECHANICS).
# PORTED (pos-cm-loop-inline): the nagini reshape reseeds the accumulator and
#   reorders the framing asserts. The velvet loop has no framing asserts, so that
#   half has no analogue; the case is kept in its inlining form, which changes the
#   loop BODY rather than a value that is definitionally `[]`. The gold backward
#   direction and invariants are kept verbatim (the front-recursive fold
#   discharges with one unfold per step; a forward append would need an
#   f(a++b)=f(a)++f(b) lemma the frozen script lacks, so it is avoided).
# RE-AIMED (admiss-f2p-shaped-input -> admiss-grounded): the nagini case injects an
#   in-impl Assert that the F2P-shaped input satisfies the (len >= 1) precondition.
#   collectMarks carries NO `require` clause (its `pre-conditions` region is empty),
#   so there is no precondition to over-constrain and the nagini probe has no
#   analogue. Re-aimed to the sharper residual risk here: a degenerate post-image.
#   The case discharges a LIVE in-region assert pinning both halves of the
#   post-image (the assembly AND the canonicalization, including the refusal and
#   its payload) at concrete points; impl kept verbatim, proof gains one `decide`
#   arm. Liveness is re-measured rather than taken on trust: falsifying one
#   conjunct FAILS (exit 1) with `error: unsolved goals ... case «adm_1 ...»`, so
#   the assert is genuinely discharged and not swallowed by the
#   `first | decide | ...` combinator.
# PORTED (the six uniqueness rivals): uniq-class-only-prepatch (return only the
#   first source — the pre-image single-source read, the first central attack),
#   uniq-drop-first (ancestors only), uniq-drop-last (drop the deepest source),
#   uniq-swap-branches (route the flag backwards — refuted on the wholeLineage=false
#   branch), uniq-reorder (same tokens, reversed groups — the ordering attack),
#   uniq-len1-empty (single-source lineage short-circuited to empty). Each is a
#   loop-free closed form whose tester kernel-reduces.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job. This bundle declares NO
#   consumed axiom AND folds nothing away: the canonicalizing step is modeled
#   deeply (`markOf`/`consMark`/`canonicalize`, refusal included) and validated
#   against the real sub-computation by axiom_check.py, and the assembly/selection
#   is modeled deeply as `flattenSeq` + the verified backward fold and checked by
#   G-CONF. So there is nothing to probe in this lane and the gate ignores
#   AXIOM_TESTS regardless.
# DIVERGENCE, for the record - the class is CLOSED BY THE SEMANTICS here, and a
#   diverging rival is REJECTED rather than admitted. This bundle sets
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
#   correctness semantics``), and a rival that supplies a NON-DECREASING measure
#   to dodge that is refused on the measure's own goal (``case «decreasing_1: z»
#   ... ⊢ z + 1 < z``), re-measured on THIS revision of the bundle with real
#   builds (both exit 1).
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
# BINDER / CLAUSE COVERAGE. Two obligations, two independent top-level clauses:
#   `collectMarks.out = canonicalize (flattenSeq (if wholeLineage then lineage
#   else [lineage.headD []]))` and `attachMark.out = withMark (canonicalize
#   (lineage.headD [])) mark`. Each clause has THREE separable pieces of content —
#   the SELECTION (which sources), the ASSEMBLY (in-order concatenation), and the
#   CANONICALIZATION (element-wise annotation extraction with a first-offender
#   refusal) — plus, for attachMark, the EXTENSION by the new annotation and the
#   propagation of a refusal. Every piece is DEFENDED and ATTACKED:
#   * selection: defended by pos-cm-closed-form / pos-cm-loop-inline; attacked by
#     uniq-class-only-prepatch, uniq-drop-first, uniq-drop-last,
#     uniq-swap-branches, uniq-len1-empty.
#   * assembly: defended by the same positives + admiss-grounded; attacked by
#     uniq-reorder (order), uniq-stop-at-empty-source (empty source).
#   * canonicalization: defended by pos-cm-closed-form, pos-cm-rebuild-outcome and
#     admiss-grounded; attacked by uniq-skip-foreign, uniq-substitute-for-foreign,
#     uniq-check-head-source-only, uniq-check-whole-lineage,
#     uniq-wrapped-as-foreign, uniq-empty-assembly-refused,
#     uniq-refusal-names-last, uniq-refusal-anonymous.
#   * extension / refusal propagation: defended by pos-am-direct and
#     pos-am-explicit-cases; attacked by uniq-am-absorb-lineage,
#     uniq-am-drop-mark, uniq-am-empty-head, uniq-am-skip-foreign,
#     uniq-am-record-over-refusal.
#   * collectMarks.wholeLineage is varied across BOTH true (thirteen rivals) and
#     false (uniq-swap-branches, uniq-check-whole-lineage) — no rival mishandling
#     only one flag value slips through, in EITHER the selection or the gate.
#   * collectMarks.lineage is varied over lengths 1/2/3, over element shapes
#     {canonical, wrapped, foreign}, with an interior EMPTY source, with an empty
#     assembly, and with TWO offenders in one source (the first/last payload
#     discriminator).
#   * attachMark.lineage over {[[canonical 1],[canonical 2]], [[canonical 7]],
#     [[]], [[foreign 7]], [[foreign 6]]} — including an EMPTY own list and an
#     own list holding an offender — and attachMark.mark over {9, 3, 5}.
#   The twenty reject witnesses probe twenty DISTINCT input points (pts=20):
#     collectMarksTester [[canonical 1],[canonical 2]] true          class-only-prepatch
#     collectMarksTester [[canonical 3],[canonical 4],[canonical 5]] true  drop-first (len3)
#     collectMarksTester [[canonical 8],[canonical 9]] true          drop-last
#     collectMarksTester [[canonical 1],[canonical 2]] false         swap-branches (own-only)
#     collectMarksTester [[canonical 5],[canonical 6]] true          reorder (ordering)
#     collectMarksTester [[canonical 4]] true                        len1-empty (len1)
#     collectMarksTester [[canonical 1],[],[canonical 2]] true       stop-at-empty-source
#     collectMarksTester [[foreign 7]] true                          skip-foreign (the gate)
#     collectMarksTester [[foreign 7],[canonical 2]] true            substitute-for-foreign
#     collectMarksTester [[canonical 1],[foreign 7]] true            check-head-source-only
#     collectMarksTester [[canonical 1],[foreign 7]] false           check-whole-lineage
#     collectMarksTester [[wrapped 4]] true                          wrapped-as-foreign
#     collectMarksTester [[]] true                                   empty-assembly-refused
#     collectMarksTester [[foreign 7, foreign 8]] true               refusal-names-last
#     collectMarksTester [[foreign 7]] true                          refusal-anonymous
#     attachMarkTester [[canonical 1],[canonical 2]] 9                am-absorb-lineage
#     attachMarkTester [[canonical 7]] 3                              am-drop-mark
#     attachMarkTester [[]] 5                                         am-empty-head
#     attachMarkTester [[foreign 7]] 5                                am-skip-foreign
#     attachMarkTester [[foreign 6]] 5                                am-record-over-refusal
#   (uniq-skip-foreign and uniq-refusal-anonymous share the input point but attack
#   different content — presence vs payload of the refusal — and each is refuted
#   there; the two attachMark foreign points differ in the offender's token so the
#   payload is exercised on that obligation too.)
#   Each witness was SEEN to discriminate with real builds: it ELABORATES against
#   the rival (its loop-free tester reduces under `decide`, exit 0) and FAILS
#   against the declared `witness_reference` (exit 1, and by DECIDING — the log
#   reads ``decide` proved that the proposition ... is false`, i.e. the tester is
#   true there, so the refutation was actually performed). Against the frozen
#   solution every one of them fails by STUCK REDUCTION instead, which attests
#   nothing; that is why the reference is named rather than gold. Vacuity was
#   probed the other way too: witnesses aimed at points where a rival AGREES with
#   the spec (`collectMarksTester [[Item.canonical 1]] true` vs
#   uniq-class-only-prepatch, `attachMarkTester [[Item.canonical 7]] 3` vs
#   uniq-am-absorb-lineage) FAIL against the rival, so these witnesses
#   discriminate on the INPUT and are not tautologies. No witness binds a
#   hypothesis (the carrier is fully transparent — all inputs are concrete
#   literals over `deriving DecidableEq` types), so there is no joint-
#   satisfiability obligation, and no `sorry`/`admit`/`native_decide`/`axiom`
#   appears in any witness.
AXIOM_TESTS = []
