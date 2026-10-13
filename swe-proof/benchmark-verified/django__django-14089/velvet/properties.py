"""properties.py — G-PBT falsification battery for django__django-14089 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery (``_swap``) edits only text inside the
``-- impl-start`` / ``-- impl-end`` region or inside the ``prove_correct``
tactic body, both of which the consumer spec view elides. So
``markers.same_spec`` holds by construction and the ``prove_correct
reverseEnum`` header survives on every variant. No case declares an ``axiom``,
a new top-level ``theorem``/``lemma``, or reaches for
``sorry``/``admit``/``native_decide``: every positive reproves the SAME
obligation, and every rival is refused by the postcondition rather than by a
weakened goal.

DEFENDED SURFACE (one contracted method, TWO input binders, EIGHT clauses):

  reverseEnum (elements : List Int) (demand : Nat)
      return (out : Option Int × List Int × List Int × List Int
                    × Option Int × List Int × List Int × Nat)
    -- no `require`: the domain is every finite sequence and every demand
    ensures out.1             = (revSeq elements).head?                 -- (C0)
    ensures out.2.1           = List.take demand (revSeq elements).tail -- (C1)
    ensures out.2.2.1         = List.drop demand (revSeq elements).tail -- (C2)
    ensures out.2.2.2.1       = []                                      -- (C3)
    ensures out.2.2.2.2.1     = none                                    -- (C4)
    ensures out.2.2.2.2.2.1   = revSeq elements                         -- (C5)
    ensures out.2.2.2.2.2.2.1 = []                                      -- (C6)
    ensures out.2.2.2.2.2.2.2 = 1                                       -- (C7)

``elements`` is the forward enumeration of an insertion-ordered collection of
distinct element keys. The observable is the TRAVERSAL HANDLE the operation
hands back, interrogated by five independent consumers. The first obtains a
handle and puts a single-element request to the handle ITSELF, then draws
``demand`` further single elements from it, then asks that same handle twice in
a row for everything it has left (C0–C3). The second obtains its OWN fresh
handle from the same, unchanged collection and asks it for the element AT A
POSITION (C4). The third obtains a fresh handle and only asks it to yield
everything (C5). The fourth obtains a fresh handle and tries to collect its
elements BY POSITION — position 0, then 1, then 2, and so on until the handle
refuses (C6). The fifth obtains a fresh handle, asks it TWICE OVER to supply the
thing that is to be stepped, and counts how many DISTINCT things it is left
holding, the handle included (C7). ``revSeq`` is the front-recursive sequence
reversal (``revSeq (c :: cs) = revSeq cs ++ [c]``).

  * The eight clauses are INDEPENDENT and are attacked independently. C0 pins
    that the handle answers a single-element request BY ITSELF — with an
    element, and with the FIRST element of the backward enumeration — so the
    handle is the traversal rather than a container a traversal must first be
    derived from; C1 pins the further prefix drawn one element at a time, which
    RESUMES after the element the handle already gave; C2 pins that what the
    SAME handle yields afterwards is the REST — so the handle carries its own
    progress and nothing is repeated or skipped across the boundary; C3 pins
    that the spent handle yields nothing on a second ask, i.e. the traversal is
    one-shot rather than a re-readable snapshot; C4 pins that a positional read
    is REFUSED even on a handle holding every element it will ever give, so the
    only way to take an element is to advance the handle; C5 pins that a handle
    asked only to yield everything, WITHOUT first being advanced, yields the
    whole backward enumeration, so the handle is a traversal that has not
    started rather than one with nothing to give until it is stepped; C6 pins
    that collecting position by position — 0, then 1, then 2, until refused —
    yields NOTHING, so the refusal C4 observes is total rather than a property
    of the single position it asks about, and no element is reachable by
    position at all; C7 pins WHAT the handle nominates when a consumer asks it
    to supply the thing that is to be stepped — itself, both times it is asked,
    so the consumer holds exactly ONE distinct thing — which is the one fact
    C0–C6 cannot state, since every one of them reports which ELEMENTS emerged
    from which channel and an object that merely supplies a traversal produces
    the same element reports as the traversal itself. A rival can satisfy any
    seven and break the eighth, so each
    needs its own rival: ``weak-handle-refuses-single`` breaks C0 alone,
    ``weak-handle-rereadable`` breaks C3 alone, ``weak-handle-restarts`` breaks
    C2 alone, ``weak-handle-positional`` breaks C4 alone,
    ``weak-handle-unstarted`` breaks C5 alone,
    ``weak-handle-collectable-by-position`` breaks C6 alone and
    ``weak-handle-nominates-other`` breaks C7 alone; the
    order/length/identity rivals
    break C0, C1, C2 and C5 together, and ``weak-handle-swapped``,
    ``weak-fixed-draw`` and ``weak-demand-zero`` break C1 and C2 with C0, C3,
    C4 and C5 intact. Each of those attributions is READ OFF the
    ``case «ensures_N: ...»`` headers of that rival's own build, not assigned by
    hand.
  * Every clause is GROUNDED in the inputs. ``revSeq`` is a transparent ``def``
    over the method's own argument (the ``axioms`` region is EMPTY — no opaque
    leaf, no consumed contract), fully unfolded by the kernel, and
    ``take``/``drop`` are applied to the method's own ``demand``. There is no
    answer-key oracle a wrong impl could ECHO, so the UNGROUNDED-ORACLE-ECHO
    class is N/A; ``pos-direct-model`` is the honest cheapest-impl control that
    stands in for it, exactly as the sibling's ``pos-assert-reversal`` does.
  * Axes on which a wrong backward traversal can differ, and all are attacked:
    ORDER (hand back the forward order), LENGTH at both boundaries and at the
    floor, ELEMENT IDENTITY (right shape, wrong elements), PARTIAL ORDER (a
    permutation of the right multiset), HANDLE PROGRESS (C2/C3), WHO ANSWERS
    THE SINGLE-ELEMENT REQUEST (C0 — a handle that has to be turned into
    something else before one element can be taken from it), HOW AN ELEMENT CAN
    BE TAKEN AT ALL (C4 — a handle that also serves positional reads, so a
    consumer never has to advance it), WHETHER THE ENUMERATION EXISTS BEFORE THE
    HANDLE IS STEPPED (C5 — a handle that yields nothing to a consumer who only
    drains it), WHAT THE HANDLE NOMINATES AS THE THING TO BE STEPPED (C7 — a
    handle that nominates a separate walker built over it rather than itself, so
    the consumer ends up holding three distinct things instead of one), the
    ``demand`` binder itself (a rival wrong at ``demand = 0``
    only), and the UNIVERSAL QUANTIFICATION (a rival that agrees with gold at
    the failing test's own input and diverges only off it).

TWO INPUT BINDERS, and BOTH are varied by the reject witnesses. ``elements``
moves across lengths 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4 with negative
keys, non-monotone keys, and keys that are neither their own positions nor a
palindrome. ``demand`` moves across 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4
— including ``demand = 0`` (where the further prefix is empty and only C0, C2,
C3, C4 and C5 carry content), a ``demand`` EQUAL to the collection size, and a
``demand`` EXCEEDING what the handle has left after answering the single-element
request (the "asking past the end simply yields fewer" sub-domain — note the
further draws are measured against ``(revSeq elements).tail``, so a ``demand``
equal to the collection size already overshoots by one). A binder every witness
held at one value would be a binder no rival was built to abuse; neither is
pinned here.

CARRIER NOTE — WHY EVERY REJECT CASE NAMES A ``witness_reference``.
A witness reaches the post-image through Velvet's tester machinery
(``reverseEnumTester <elements> <demand> = false`` says the extracted program
violates the contract at that concrete input) and closes by ``decide``, checked
in a file whose ``prove_correct`` block has been stripped so no tactic script
can mask the verdict. ``decide`` reduces the extracted program by kernel
computation, and the FROZEN impl keeps THREE ``while`` loops: under
``loom.semantics.choice "demonic"`` their fixpoints elaborate through
``Classical.choice``, which the kernel cannot unfold. Measured with
``scripts/lean_verify.sh`` — the frozen side fails IDENTICALLY for a TRUE claim
and for its negation:

  example : reverseEnumTester [1, 2, 3] 2 = true  := by decide   -- exit 1
  example : reverseEnumTester [1, 2, 3] 2 = false := by decide   -- exit 1

both with ``reduction got stuck at the `Decidable` instance / match
reverseEnumTester [1, 2, 3] 2, ... with``. So the frozen side's exit code
carries NO information, and a forged witness asserting the rival is CORRECT
would clear that half too (the ``witness-undecided`` shape).

So every reject case names ``pos-stdlib-reversal`` as its
``witness_reference``: a LOOP-FREE impl of the frozen spec that the verifier
ACCEPTS and whose extracted tester DOES reduce. The gate checks (not trusts)
that the reference shares the frozen spec and verifies, then refutes each
witness against it. That is a real discrimination — an impl the verifier
accepts cannot violate its own spec.

DISCRIMINATION CONTROL (measured, not argued). For all FIFTEEN reject cases a
full 2x2 was built, 60 builds, 0 mismatches:

  honest witness  (``= false``) vs rival      -> exit 0  (elaborates)
  honest witness  (``= false``) vs reference  -> exit 1, ``Tactic `decide`
      proved that the proposition reverseEnumTester <point> = false is false``
      — a SEMANTIC refutation, not a stuck build
  FORGERY         (``= true``)  vs rival      -> exit 1
  FORGERY         (``= true``)  vs reference  -> exit 0

The forgery row is the point: the reference side's exit code tracks the CLAIM
and not the build, so the shipped points are not passing by construction. It
was additionally checked that ``weak-demand-zero`` — which is wrong ONLY at
``demand = 0`` — is CORRECT at an agreement point: ``reverseEnumTester [7, 2] 1
= true`` elaborates against that rival (exit 0, measured), so its shipped
witness is at the input that genuinely discriminates rather than at a point it
fails everywhere.

PROOF-SHAPE CONTROL — why each rejection is attributable to the IMPL.
A rival must not fail under a tactic body that would also fail for a CORRECT
impl of the same shape, or the rejection attests to a tactic mismatch rather
than to the spec. Every rival here is a loop-free ``return`` whose proof body is
reduced to a bare ``loom_solve``. ``pos-direct-model`` is that EXACT shape under
that EXACT body with the RIGHT expression, and it VERIFIES (exit 0). So a rival
failing under it fails for its expression — and the residual goal names that
expression, e.g. for the forward-order rival:

  error: unsolved goals
  case «ensures_1: out.2.2.2.2.2 = revSeq elements»
  ⊢ elements = revSeq elements

  case «ensures_4: out.2.2.1 = List.drop demand (revSeq elements).tail»
  ⊢ List.drop demand elements.tail = List.drop demand (revSeq elements).tail

  case «ensures_5: out.2.1 = List.take demand (revSeq elements).tail»
  ⊢ List.take demand elements.tail = List.take demand (revSeq elements).tail

  case «ensures_6: out.1 = (revSeq elements).head?»
  ⊢ elements.head? = (revSeq elements).head?

That is the attribution, and it was read off the build log for all fifteen.
NOTE the numbering: the verifier labels the ``ensures`` cases in the REVERSE of
their declaration order, so ``ensures_1`` is C5, ``ensures_2`` is C4, ...,
``ensures_6`` is C0. The clause attributions below are stated by clause TEXT,
which the header carries verbatim, so the numbering is never load-bearing.

ADVERSARIAL READ of the sibling's classes on this carrier:

  * SOUNDNESS — APPLIES, and four ship: the loop-free direct return of the
    grounded model (the honest no-echo control and the proof-shape control), the
    loop-free standard-library reversal bridged to the model by induction (a
    different algorithm for the same value, and the battery's witness
    reference), a loop-PRESERVING reshape that rewrites the guard, inlines the
    element binding and reorders two independent invariants under the FROZEN
    proof script verbatim, and a reshape of the CONTROL FLOW ITSELF — the first
    loop run in the opposite direction, prepending, under a ``take``-based
    invariant that makes both the frozen invariant and the frozen drop-step
    rewrite inapplicable.
  * ADMISSIBILITY — PORTED, re-aimed. The sibling self-calls on the F2P-shaped
    input to show a normal collection satisfies its read-only
    fractional-permission precondition. This method has NO ``require``, so
    nothing could exclude an input and that exact probe is degenerate. Per the
    brief the analogue of PRECOND-TOO-STRONG here is the obligation being
    UNSATISFIABLE at an F2P-shaped input, which a positive discharged AT that
    concrete input tests directly — so ``admiss-f2p-point`` dispatches on the
    literal F2P input and returns the literal expected 6-tuple (including the
    ``some``/``none`` answer to the single-element request, the refused
    positional read and the fresh handle's whole enumeration), forcing the
    verifier to discharge all six clauses at fully concrete values. Not omitted
    as a vacuous class.
  * FRAME / PERMISSION MUTATION — VACUOUS on this backend, and MEASURED rather
    than asserted. Lean and Velvet are referentially transparent: ``elements``
    is an immutable value, no input is ``mut`` (only the loop-locals are), there
    is no heap, no aliasing, no ``Old``, and no permission system. The nearest
    expressible analogue was BUILT and the carrier refuses it at ELABORATION
    with "`elements` cannot be mutated, only variables declared using `let mut`
    can be mutated" — a binder/parse refusal with no spec content and nothing
    for a witness to state. Not ported; no substitute fabricated.
  * DIVERGENCE / NON-TERMINATION — REJECTED BY THE SPEC, but NOT SHIPPABLE as a
    witnessed case, and the distinction matters. This bundle sets
    ``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``
    (the ``open`` is what actually selects the semantics — both namespaces define
    ``WPGen.forWithInvariantLoop`` and the later ``open`` wins), so the
    postcondition is claimed of ALL runs and the verifier emits a descent
    obligation per loop. Both diverging rivals were BUILT: dropping the measure
    is refused outright ("Decreasing annotations are required in total
    correctness semantics"), and a CONSTANT measure is refused on the measure's
    own goal (``case «decreasing_1: elements.length» ⊢ False``). So divergence
    does NOT discharge the clauses vacuously — this is not the ``partial``
    semantics hole. It is still not shipped, because the witness contract cannot
    be met: the constant-measure rival computes exactly gold's VALUES, so there
    is no input at which its output disagrees with the spec, and both
    ``reverseEnumTester [1,2,3] 2 = false`` and ``= true`` fail against it by
    stuck reduction (measured). Its rejection is a judgement of the termination
    obligation, not a postcondition violation at a point. Recorded as
    REJECTED-BY-SPEC-BUT-UNWITNESSABLE: neither a spec hole nor a battery gap.
  * CONTROL-FLOW-EFFECT (raise vs return) — N/A for EXCEPTIONS at this lane, as
    in the sibling: the modeled operation is total with one return path. But the
    capability that is not a sequence value — that what the operation hands back
    is a self-advancing one-shot traversal rather than a container a traversal
    must first be derived from — is NOT left to the axiom lane. It is BEHAVIOUR,
    and the frozen spec states it in four clauses that no sequence-valued
    observation of a single drained handle can supply: C0 says the single-element
    request put to the handle ITSELF is answered with an element (so the handle
    advances itself), C3 says the spent handle yields nothing on a second ask (so
    it is one-shot rather than a re-readable snapshot), C4 says a positional read
    is refused even where every element is still to come (so advancing is the
    ONLY way to take an element — no element access by index), and C5 says a
    handle that is only drained, never advanced, still yields the whole backward
    enumeration (so the enumeration is not a side effect of having been stepped).
    ``weak-handle-refuses-single`` attacks C0 alone,
    ``weak-handle-rereadable`` C3 alone, ``weak-handle-positional`` C4 alone and
    ``weak-handle-unstarted`` C5 alone. C4 and C5 are the two clauses that
    together rule out the impostor shapes a values-only spec admits: an object
    that supplies elements by index rather than by advancing, and one whose
    enumeration only comes into being once it has been advanced.
  * PARTIAL-DOMAIN / VALUE — carries most of the reject lane; each rival names
    its correct sub-domain in its rationale.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The bundle consumes no ``axiom`` (the
``axioms`` region is empty); the reversal is modeled DEEPLY and ``revSeq`` is an
A-reference validated ``==`` the real primitive by G-AX, not a consumed
contract. G-PBT ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14089"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. Every anchor lies WHOLLY inside the impl region or is the
# `prove_correct` tactic block, and every one is asserted present-and-unique at
# load, so the manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------

_IMPL_START = "    -- impl-start\n"
_IMPL_END = "    -- impl-end"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"
assert _BASE.count(_IMPL_END) == 1, "impl-end anchor drift"

# The whole gold impl BODY (between the markers, markers excluded): the three
# loops, the handle's own answer, and the return. Rivals and the loop-free
# positives swap on this.
_BODY = _BASE[_BASE.index(_IMPL_START) + len(_IMPL_START):_BASE.index(_IMPL_END)]
assert "while i > 0" in _BODY and _BASE.count(_BODY) == 1, "impl-body anchor drift"

# The frozen proof body (tactic script only — elided from the spec view; the
# `prove_correct reverseEnum` header is preserved by every variant).
_PROOF = """prove_correct reverseEnum by
  loom_solve
  · rw [revSeq_drop_step elements i (by omega) (by omega)]
    simp_all
  all_goals simp_all
  case _ =>
    rcases done_2 with h | h
    · subst h; rfl
    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
"""
assert _BASE.count(_PROOF) == 1, "proof anchor drift"

# The backward loop's guard and step, and the second loop's two INDEPENDENT
# invariants: the loop-preserving positive reshapes exactly these.
_GUARD = "    while i > 0\n"
_STEP = ("      let e := elements[i - 1]!\n"
         "      result := result ++ [e]\n")
_INV_J = ("      invariant j ≤ demand\n"
          "      invariant j ≤ remaining.length\n")
for _a in (_GUARD, _STEP, _INV_J):
    assert _BASE.count(_a) == 1, f"anchor drift: {_a!r}"

# The frozen backward-scan loop, replaced wholesale by the forward-direction
# positive. Lives inside _BODY, so this is impl-region surgery.
_LOOP_BACK = """    let mut result : List Int := []
    let mut i := elements.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ elements.length
      invariant result = revSeq (elements.drop i)
      done_with i = 0
      decreasing i
    do
      let e := elements[i - 1]!
      result := result ++ [e]
      i := i - 1
"""
assert _BASE.count(_LOOP_BACK) == 1, "backward-loop anchor drift"

# A bare `loom_solve`: the honest body for a loop-free impl (no loop, so no
# invariant to peel, no drop-step to rewrite, and no `done_2` to case on). It is
# honest precisely because `pos-direct-model` — the same shape with the RIGHT
# expression — VERIFIES under it, so a rival's failure under it is the
# expression's. Measured, exit 0.
_PROOF_FLAT = "prove_correct reverseEnum by\n  loom_solve\n"

# The body for the standard-library reversal: the same flat shape plus an
# in-body `have` bridging the library reversal to the spec's front-recursive
# model by induction. A `have` inside the tactic block is not a new top-level
# declaration, so the variant introduces no `theorem`/`lemma` beyond the frozen
# set and assumes nothing.
_PROOF_REV = """prove_correct reverseEnum by
  have hrev : ∀ l : List Int, l.reverse = revSeq l := by
    intro l
    induction l with
    | nil => rfl
    | cons c cs ih => rw [List.reverse_cons, ih, revSeq_cons]
  loom_solve
  all_goals simp_all [hrev elements]
"""


def _flat(body, proof=_PROOF_FLAT):
    """A loop-free variant: `body` as the whole impl region, under `proof`."""
    return _swap(_swap(_BASE, _BODY, body), _PROOF, proof)


def _handle(back, given=None, drawn=None, rest=None, again=None,
            positional=None, fresh=None, by_position=None, held_distinct=None):
    """A loop-free impl that materializes `back` and then answers the eight
    observations with `given` / `drawn` / `rest` / `again` / `positional` /
    `fresh` / `by_position` / `held_distinct`.

    `given` is what the handle answers when the single-element request is put to
    the handle ITSELF (C0); the next three are what it then yields to the
    `demand` further single draws (C1), to the drain (C2) and to the second
    drain (C3), all measured from what it has left after answering —
    `back.tail`. `positional` is what a FRESH handle answers to a request for the
    element at a position (C4: a refusal), `fresh` is what a FRESH handle
    yields to a consumer that only drains it, without advancing it first (C5: the
    whole backward enumeration), and `by_position` is what a consumer collects
    from a FRESH handle by taking the element at position 0, then 1, then 2, and
    so on until the handle refuses (C6: nothing at all, because the first
    position is already refused). `held_distinct` is how many DISTINCT things a
    consumer is left holding after asking a FRESH handle twice over to supply
    the thing that is to be stepped, the handle itself included (C7: exactly 1,
    because the handle nominates ITSELF both times). Defaulting `fresh` to
    `back` is deliberate: a rival that corrupts the enumeration corrupts what
    the fresh handle yields too, exactly as its real counterpart would."""
    return ("    let back := %s\n"
            "    return (%s, %s, %s, %s, %s, %s, %s, %s)\n"
            % (back,
               given if given is not None else "back.head?",
               drawn if drawn is not None else "List.take demand back.tail",
               rest if rest is not None else "List.drop demand back.tail",
               again if again is not None else "([] : List Int)",
               positional if positional is not None else "(none : Option Int)",
               fresh if fresh is not None else "back",
               by_position if by_position is not None else "([] : List Int)",
               held_distinct if held_distinct is not None else "(1 : Nat)"))


# ---------------------------------------------------------------------------
# Witness plumbing. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches the post-image through Velvet's own tester machinery:
# `reverseEnumTester <elements> <demand> = false` says the extracted program's
# result violates the contract at that concrete input. Checked in a file whose
# `prove_correct` block is stripped, so no tactic script can mask the verdict.
# Every argument is a concrete literal — no opaque term, so no hypothesis is
# bound and no consistency probe applies.
# ---------------------------------------------------------------------------

def _witness(elements, demand):
    return ("\n"
            "extract_program_for reverseEnum\n"
            "prove_precondition_decidable_for reverseEnum\n"
            "prove_postcondition_decidable_for reverseEnum\n"
            "derive_tester_for reverseEnum\n\n"
            f"example : reverseEnumTester {elements} {demand} = false := by\n"
            "  decide\n")


# THE WITNESS REFERENCE. The loop-free standard-library reversal: a
# machine-checked-correct impl of the frozen spec whose extracted tester
# REDUCES. Shipped as a positive control in its own right
# (`pos-stdlib-reversal`) and named by every reject case, because the FROZEN
# impl cannot serve as the witness's second subject on this bundle — its three
# `while` loops elaborate through `Classical.choice`, so `decide` against it is
# stuck for every claim regardless of truth. See the CARRIER NOTE.
#
# Deliberately `elements.reverse` and not `revSeq elements`: against the latter
# the tester's verdict would close by `rfl` on the spec term itself, a weaker
# second subject. Against the library reversal the kernel genuinely COMPUTES
# both sides and compares them.
_REFERENCE = _flat(_handle("elements.reverse"), _PROOF_REV)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to one source shape).
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        "module": _flat(_handle("revSeq elements")),
        "rationale": (
            "the cheapest honest correct impl materializes the grounded model "
            "`revSeq elements` directly and answers the handle's four "
            "questions from it — no loop at all, so the flat `loom_solve` body "
            "is the honest reproof. All six clauses hold on the whole domain. "
            "If this failed to verify the spec would be over-fit to the loop "
            "code shape (SPEC-TOO-STRONG). It is simultaneously the honest "
            "no-ungrounded-echo control the sibling's pos-assert-reversal "
            "stands in for: the model is a transparent def over the method's "
            "own argument and computing it IS the real reversal work, so a "
            "direct return is correct rather than a cheat — any WRONG "
            "expression fails a clause, which the fifteen rivals demonstrate. "
            "And it is the battery's PROOF-SHAPE CONTROL: the same shape and "
            "the same tactic body as every rival, so their rejections are "
            "attributable to their expressions and not to a script tuned to "
            "loops they no longer have (measured, exit 0)."),
    },
    {
        "id": "pos-stdlib-reversal",
        "kind": "soundness",
        "expect": "verify",
        "module": _REFERENCE,
        "rationale": (
            "the standard library's sequence reversal computes the same value "
            "by a different recursion than the spec's front-recursive model, so "
            "the clauses hold only via the bridge `l.reverse = revSeq l` (an "
            "induction inside the tactic body — no new top-level declaration, "
            "nothing assumed). A correct impl that reaches the pinned sequence "
            "by another route must verify, else the spec is SPEC-TOO-STRONG on "
            "the recursion shape rather than on the value. This case also "
            "carries the battery: it is the `witness_reference` every reject "
            "case names, because it is an impl the verifier ACCEPTS whose "
            "extracted tester REDUCES, which the frozen loops' does not. It is "
            "deliberately the library reversal and not the model term itself, "
            "so the tester's verdict on it is a genuine kernel computation of "
            "both sides rather than `rfl` on the spec term."),
    },
    {
        "id": "pos-loop-preserving",
        "kind": "soundness",
        "expect": "verify",
        # Keeps all three loops and the FROZEN proof script verbatim; rewrites
        # the backward guard to the equivalent comparison, inlines the element
        # binding into the append, and REORDERS the second loop's two
        # independent invariants. That last is the direct analogue of the
        # sibling's "reorder the two independent framing steps".
        "module": _swap(_swap(_swap(_BASE, _GUARD, "    while 0 < i\n"),
                              _STEP,
                              "      result := result ++ [elements[i - 1]!]\n"),
                        _INV_J,
                        "      invariant j ≤ remaining.length\n"
                        "      invariant j ≤ demand\n"),
        "rationale": (
            "rewriting the backward guard `i > 0` to `0 < i`, inlining the "
            "element binding into the append, and REORDERING the second loop's "
            "two independent invariants leaves the same three traversals "
            "computing the same values, so all six clauses still hold — and "
            "the FROZEN proof script closes them unchanged, which is the point: "
            "the frozen invariants, the drop-step rewrite and the `done_2` case "
            "analysis are not tied to the guard's spelling, to the temporary, or "
            "to the order in which independent invariants are listed. This is "
            "the closest port of the sibling's pos-assert-reorder, which "
            "likewise rewrote the loop guard and reordered two independent "
            "framing steps while keeping every gold proof obligation. NOTE ON "
            "STRENGTH, so this case is not over-read: `i > 0` and `0 < i` are "
            "the same term up to notation and inlining the binding is a "
            "let-reduction, so the guard/binding half is close to "
            "definitional; the invariant REORDER is the part that genuinely "
            "exercises the proof script's independence. `pos-forward-loop` is "
            "what carries the claim that the spec admits a different ALGORITHM."),
    },
    {
        "id": "pos-forward-loop",
        "kind": "soundness",
        "expect": "verify",
        # The strongest available SPEC-TOO-STRONG probe: the materializing loop
        # runs in the OPPOSITE DIRECTION (forward, i from 0 up) and PREPENDS, so
        # neither the frozen invariant (over `drop`) nor the frozen drop-step
        # rewrite applies — the reshape is the control flow itself. The sibling
        # explicitly DECLINED this reshape, on the ground that it needs an
        # `f(a ++ b)` homomorphism the verifier will not auto-discharge; the
        # lemma is supplied here as an in-body `have`, which is what turns that
        # PROOF gap into a landed positive. Measured: exit 0.
        "module": _swap(
            _swap(_BASE, _LOOP_BACK,
                  """    let mut result : List Int := []
    let mut i := 0
    while i < elements.length
      invariant 0 ≤ i ∧ i ≤ elements.length
      invariant result = revSeq (elements.take i)
      done_with i = elements.length
      decreasing elements.length - i
    do
      result := [elements[i]!] ++ result
      i := i + 1
"""),
            _PROOF,
            """prove_correct reverseEnum by
  have hsnoc : ∀ (l : List Int) (x : Int),
      revSeq (l ++ [x]) = x :: revSeq l := by
    intro l x
    induction l with
    | nil => simp [revSeq]
    | cons c cs ih => simp [revSeq_cons, ih]
  loom_solve
  · rw [List.take_succ_eq_append_getElem (by omega), hsnoc]
    simp_all [List.getElem!_eq_getElem?_getD,
      List.getElem?_eq_getElem (show i < elements.length by omega)]
  all_goals simp_all
  case _ =>
    rcases done_2 with h | h
    · subst h; rfl
    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
"""),
        "rationale": (
            "the same values computed by the opposite TRAVERSAL DIRECTION: a "
            "forward walk that prepends each element, under an invariant over "
            "`elements.take i` rather than `elements.drop i`. This is the "
            "deepest structural reshape of the code that still meets all six "
            "clauses on the whole domain — the frozen loop's invariant AND its "
            "drop-step rewrite are both inapplicable, so nothing of that half "
            "of the frozen proof survives except the obligation itself, which is "
            "reproven from the snoc homomorphism `revSeq (l ++ [x]) = x :: "
            "revSeq l` (an induction inside the tactic body: no new top-level "
            "declaration, nothing assumed). Where pos-loop-preserving only "
            "reshapes spelling and invariant order, this case is what actually "
            "shows the spec pins the VALUES and not the loop direction. If it "
            "failed to verify the spec would be SPEC-TOO-STRONG on the "
            "traversal order of the code."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require`, so the sibling's "a normal
    # collection satisfies the read-only precondition" probe is degenerate
    # (nothing could exclude any input, and there is no permission surface).
    # Per the brief, the analogue of PRECOND-TOO-STRONG on an unconstrained
    # domain is the obligation being UNSATISFIABLE at an F2P-shaped input, which
    # a positive discharged AT that concrete input tests directly.
    # =====================================================================
    {
        "id": "admiss-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        # Dispatches on the LITERAL F2P-shaped input and returns the LITERAL
        # expected tuple, so the verifier must discharge all seven clauses at
        # fully concrete values rather than schematically. The general arm keeps
        # a correct impl so the rest of the domain still verifies.
        "module": _flat(
            "    if elements = [1, 2, 3] ∧ demand = 2 then\n"
            "      return (some (3 : Int), [2, 1], ([] : List Int), ([] : List Int),\n"
            "        (none : Option Int), [3, 2, 1], ([] : List Int), (1 : Nat))\n"
            "    else\n"
            "      if elements = ([] : List Int) ∧ demand = 0 then\n"
            "        return ((none : Option Int), ([] : List Int), ([] : List Int),\n"
            "          ([] : List Int), (none : Option Int), ([] : List Int),\n"
            "          ([] : List Int), (1 : Nat))\n"
            "      else\n"
            "        let back := revSeq elements\n"
            "        return (back.head?, List.take demand back.tail,\n"
            "          List.drop demand back.tail, ([] : List Int),\n"
            "          (none : Option Int), back, ([] : List Int), (1 : Nat))\n",
            "prove_correct reverseEnum by\n"
            "  loom_solve\n"
            "  all_goals subst_vars\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all\n"),
        "rationale": (
            "the obligation must be SATISFIABLE at the failing test's own "
            "input, and this case makes the verifier show it at fully concrete "
            "values: on the literal three-key collection with a literal demand "
            "it returns the literal tuple (some 3, [2, 1], [], [], none, "
            "[3, 2, 1]) and all six "
            "clauses are discharged by `decide` on closed terms — the handle's "
            "own answer to the single-element request IS the last-inserted key, "
            "the drawn prefix IS the two elements that follow it, what the same "
            "handle yields afterwards IS nothing more, the second ask "
            "yields nothing, a fresh handle REFUSES a positional read, and a "
            "fresh handle that is only drained yields all three keys in the "
            "backward order. The empty collection at demand 0 is discharged the "
            "same way, with the handle answering that it has nothing to give "
            "and the fresh drain yielding the empty enumeration. "
            "If the obligation were unsatisfiable at an F2P-shaped "
            "input — a post-image no impl can hit — this case would fail while "
            "a schematic impl might not, which is the PRECOND-TOO-STRONG "
            "analogue on a domain with no `require`. Ports the sibling's "
            "admiss-f2p-shape (a probe at the exact F2P-shaped input [1,2,3]) "
            "re-aimed from fractional-permission admissibility, since this "
            "method has no `require` at all and this backend has no permission "
            "surface. Not omitted as vacuous: the concrete-point discharge is "
            "real content and it is what the sibling's case was for."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input, and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test.
    #
    # F2P scenario grounding every refinement: the failing test builds an
    # insertion-ordered collection of the three distinct keys 1, 2, 3, asks for
    # its backward traversal, and asserts BOTH that what it was handed is a
    # self-advancing one-shot traversal — it must answer a single-element
    # request itself (C0) and be spent once drained (C3) — AND that draining it
    # yields exactly the keys in the opposite order, 3 then 2 then 1 (C1/C2).
    #
    # Each rival is loop-free so its extracted tester `decide`s, under the bare
    # `loom_solve` body that `pos-direct-model` verifies under; each names
    # `pos-stdlib-reversal` as its `witness_reference` because the frozen loops
    # decide nothing. See the CARRIER NOTE and the PROOF-SHAPE CONTROL.
    # =====================================================================
    {
        "id": "weak-forward-order",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-CHANGE BEHAVIOUR, and the named adversary of C1/C2: hand back
        # the forward enumeration instead of reversing it. Correct exactly on
        # the palindromic sub-domain.
        "module": _flat(_handle("elements")),
        "refinement": (
            "this is the behaviour the change replaces: a backward traversal "
            "that PRESERVES the insertion order rather than reversing it — the "
            "sequence a forward traversal already produced. Its faithful real "
            "patch is a backward-traversal method that delegates to the FORWARD "
            "iterator, so the failing test's collection of keys 1, 2, 3 "
            "materializes as 1, 2, 3 where the test demands 3, 2, 1: the "
            "equality assertion fails and it does NOT resolve. Before the change "
            "no backward traversal existed at all, so this is also the shape a "
            "minimal-effort patch takes."),
        "rationale": (
            "REJECT from C0, C1, C2 and C5: the forward order is not the reversal of "
            "any collection with two or more distinct keys, so the element the "
            "handle answers with, the drawn prefix and the remainder are all "
            "wrong. Refuted at the F2P's own input, "
            "`[1, 2, 3]` with demand 2, where gold answers 3 and then leaves "
            "[2, 1] to be drawn while the rival answers 1 and leaves [2, 3] — "
            "the exact "
            "discrimination the failing test performs. The residual goals name "
            "the rival's own claim (`⊢ elements.head? = (revSeq elements).head?` "
            "and `⊢ List.take demand elements.tail = List.take "
            "demand (revSeq elements).tail`), which is the attribution. If it "
            "verified => SPEC-TOO-WEAK (the spec would admit forward order as a "
            "'reversal'). Ports the sibling forward-order."),
        "witness": _witness("[1, 2, 3]", 2),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        # LENGTH at the head boundary: reverse everything EXCEPT the
        # first-inserted key. Correct only on the empty collection.
        "module": _flat(_handle("revSeq (elements.drop 1)")),
        "refinement": (
            "corresponds to a backward-traversal patch that skips the "
            "first-inserted key — an off-by-one at the head of the sequence it "
            "walks. The failing test's collection of keys 1, 2, 3 would "
            "materialize as 3, 2 where the test demands 3, 2, 1, so the "
            "equality assertion fails on both the length and the final key and "
            "it does NOT resolve. Correct only on the empty collection."),
        "rationale": (
            "REJECT from C0, C1, C2 and C5 (measured: the residual goals name all "
            "four): dropping the first-inserted key makes the "
            "traversal the reversal of a PROPER SUFFIX, one element shorter "
            "than the reversal of the whole collection, so it differs on every "
            "non-empty input. Refuted at `[2, 5, 9]` with demand 3 — a demand "
            "past what the handle has left once it has answered, so the drawn "
            "prefix is everything that remains and the divergence lands squarely "
            "on C1: gold answers 9 and then draws [5, 2] while the rival answers "
            "9 and draws only [5]. If it verified => "
            "SPEC-TOO-WEAK (the reversal would not have to visit every "
            "element). Ports the sibling drop-first-element, whose loop stopped "
            "one step early; the loop-free form of the same divergence."),
        "witness": _witness("[2, 5, 9]", 3),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-last-element",
        "kind": "uniqueness",
        "expect": "reject",
        # LENGTH at the OTHER boundary. The sibling attacks only the head, so a
        # spec loose enough to miss a dropped TAIL element would not be caught.
        "module": _flat(_handle("revSeq elements.dropLast")),
        "refinement": (
            "corresponds to a backward-traversal patch that skips the "
            "last-inserted key — the off-by-one at the OTHER end of the "
            "sequence, the one a backward walk starting from the wrong bound "
            "produces. The failing test's collection of keys 1, 2, 3 would "
            "materialize as 2, 1: the test's FIRST expected key is missing "
            "entirely, so the equality assertion fails and it does NOT resolve. "
            "Correct only on the empty collection."),
        "rationale": (
            "REJECT from C0, C1, C2 and C5: dropping the last-inserted key makes the "
            "traversal the reversal of a proper PREFIX, missing the element the "
            "backward order must BEGIN with — so it is C0 that catches it first, "
            "the handle answering the single-element request with the wrong "
            "element entirely. Refuted at `[-3, 8]` with demand 2 "
            "— a two-key input with a NEGATIVE key, so the witness moves both "
            "the length and the key values off the positive-monotone shape the "
            "F2P point has; gold answers 8 and then draws [-3], while the rival "
            "answers -3 and has nothing left to draw. "
            "Added by this port: the sibling attacks only the HEAD boundary, so "
            "nothing there would notice a spec that let the traversal drop its "
            "first-yielded element. If it verified => SPEC-TOO-WEAK at the tail "
            "boundary."),
        "witness": _witness("[-3, 8]", 2),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-head-pinned-tail-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL ORDER — the NEAR-MISS. Right length, right multiset, tail
        # correctly reversed; only the first key stays pinned at the front.
        "module": _flat(_handle("elements.take 1 ++ revSeq (elements.drop 1)")),
        "refinement": (
            "corresponds to a backward-traversal patch that reverses only the "
            "tail of the sequence it walks and leaves the first-inserted key at "
            "the front — a partial reversal, the shape a patch takes when the "
            "walk is anchored one position off. The output has the RIGHT length "
            "and the right keys, so a length or membership check would pass; the "
            "failing test's collection of keys 1, 2, 3 would materialize as "
            "1, 3, 2 where the test demands 3, 2, 1, so the ORDER equality "
            "fails and it does NOT resolve. Correct on every collection of at "
            "most one key."),
        "rationale": (
            "REJECT from C0, C1, C2 and C5: a permutation of the right multiset in "
            "the wrong "
            "ORDER — the case that distinguishes a spec pinning the reversal "
            "from one pinning only length and membership. Refuted at "
            "`[2, 9, 4]` with demand 3, where gold answers 4 and then draws "
            "[9, 2] while the rival answers 2 — the first-inserted key, left "
            "pinned at the front — and draws [4, 9]. It is a NEAR-MISS that "
            "agrees with gold "
            "over strictly more of the domain than the length rivals do (right "
            "on length everywhere, and right on the whole empty and singleton "
            "sub-domain), so it carries its OWN point rather than sharing one: "
            "a three-key point is what shows the tail genuinely IS reversed "
            "while the whole is not, which is the sub-domain the rationale "
            "claims. Added by this port: every sibling rival is wrong about "
            "length or about the entire order, so a partial-order break was "
            "unattacked. If it verified => SPEC-TOO-WEAK (the pin would be a "
            "multiset/length pin, not an order pin)."),
        "witness": _witness("[2, 9, 4]", 3),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-positions-not-elements",
        "kind": "uniqueness",
        "expect": "reject",
        # ELEMENT IDENTITY. Right length, right ordering DIRECTION, but it
        # yields the POSITIONS walked instead of the keys found at them.
        "module": _flat(_handle(
            "(List.range elements.length).reverse.map (fun k => (k : Int))")),
        "refinement": (
            "corresponds to a backward-traversal patch that walks the right "
            "positions in the right direction but yields the position it is at "
            "instead of the key stored there — dereferencing omitted. The output "
            "has the right length and the right ordering direction, so a length "
            "check or an ordering check would pass; the failing test's "
            "collection of keys 1, 2, 3 would materialize as 2, 1, 0 where the "
            "test demands 3, 2, 1, so the equality assertion fails and it does "
            "NOT resolve. Correct exactly on the collections whose keys are "
            "their own positions."),
        "rationale": (
            "REJECT from C0, C1, C2 and C5: the traversal must yield the "
            "collection's "
            "own KEYS, not the indices at which they sit. This is the only "
            "rival whose divergence is about element IDENTITY rather than about "
            "length, order or handle progress — every other value rival returns "
            "a sub-sequence or a permutation of the input's own keys, so a spec "
            "pinning only the shape of the traversal (length plus "
            "descending-index order) would catch all of them and miss this one. "
            "Refuted at `[9, 4]` with demand 2, where gold answers 4 and then "
            "draws [9] while the rival answers 1 and draws [0] — the positions, "
            "not the keys; the point is chosen so no key coincides with "
            "its own position (at `[0, 1]` the rival would AGREE with gold, "
            "which is exactly the sub-domain the rationale concedes). Added by "
            "this port. If it verified => SPEC-TOO-WEAK (the pin would not tie "
            "the traversal to the input's contents)."),
        "witness": _witness("[9, 4]", 2),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # SUPPORTING coarse corruption: yield nothing at all. Pins the floor.
        "module": _flat(_handle("([] : List Int)")),
        "refinement": (
            "corresponds to a backward-traversal patch that yields an empty "
            "traversal for every collection. The failing test's collection of "
            "keys 1, 2, 3 would materialize as the empty sequence where the "
            "test demands 3, 2, 1, so the equality assertion fails and it does "
            "NOT resolve. Correct only on the empty collection."),
        "rationale": (
            "REJECT from C0, C1, C2 and C5: the empty sequence is not the reversal "
            "of any "
            "non-empty collection. Supporting case — a coarser corruption than "
            "the reasoned attacks — but it pins the floor: a spec admitting it "
            "would be pinning nothing about the traversal at all. Refuted at "
            "the SINGLETON `[5]` with demand 1, deliberately the smallest "
            "non-empty point, where the refutation rests on C0 and C5 (the "
            "further draws and both drains are empty for gold too, so an empty "
            "handle is caught there only by its inability to answer the "
            "single-element request with 5 and by the empty enumeration it "
            "hands a consumer who only drains a fresh handle). Ports the "
            "sibling always-empty."),
        "witness": _witness("[5]", 1),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-handle-refuses-single",
        "kind": "uniqueness",
        "expect": "reject",
        # C0 ALONE. Every sequence value is RIGHT: the further single draws, the
        # drain and the second drain all match gold exactly. The only error is
        # that the handle does not answer a single-element request PUT TO IT —
        # it reports having nothing to give, so a consumer that holds it cannot
        # take one element from it without first turning it into something else.
        # Correct on exactly the empty collection, where there is nothing to
        # give and `none` is the right answer.
        "module": _flat(_handle("revSeq elements",
                                given="(none : Option Int)")),
        "refinement": (
            "corresponds to a backward-traversal patch that hands back a "
            "container-like view over the reversed keys rather than a traversal: "
            "a consumer can enumerate it — and every key it then enumerates is "
            "correct, in the correct order — but the object itself does not "
            "answer a single-element request, so one element can be taken only "
            "after deriving a separate traversal from it. This is the shape a "
            "patch takes when the method wraps the keys in a helper object, or "
            "returns a materialized container, instead of handing back the "
            "traversal itself. The failing test does not merely materialize the "
            "handle: it FIRST asserts that what it was handed is a one-shot "
            "traversal that yields elements one at a time on its own, and a "
            "view that must be converted first is not, so that assertion fails "
            "and it does NOT resolve — measured on the real tree: the "
            "equality-of-values half passes (the keys come out 3, 2, 1) while "
            "the handle assertion fails, an ISOLATED failure of the F2P "
            "obligation with all 43 P2P tests still passing."),
        "rationale": (
            "REJECT from C0 (`out.1 = (revSeq elements).head?`) and from C0 "
            "ALONE — C1, C2, C3, C4 and C5 are satisfied exactly, which is what makes "
            "this rival the one that matters: it isolates the clause saying WHO "
            "answers the single-element request. A spec carrying only the three "
            "sequence clauses admits it, because a handle that has to be "
            "converted before it will give up one element can still be "
            "converted into one that yields exactly the right elements in "
            "exactly the right order — no sequence-valued observation "
            "distinguishes the two. Refuted at the SINGLETON `[-7]` with demand "
            "0, deliberately the point where every other clause is vacuous: the "
            "further prefix, the drain and the second drain are all empty for "
            "ANY impl there, so nothing but C0 can carry the refutation, and it "
            "does — gold answers the request with -7 and the rival answers that "
            "it has nothing to give. That point is also new to the battery (a "
            "one-key collection with a NEGATIVE key at demand 0). If it "
            "verified => SPEC-TOO-WEAK: the handle could be a container the "
            "consumer has to convert, which is exactly the wrong "
            "implementation this battery's spec was strengthened to reject."),
        "witness": _witness("[-7]", 0),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-handle-rereadable",
        "kind": "uniqueness",
        "expect": "reject",
        # C3 ALONE. The values are all RIGHT: the answer to the single-element
        # request, the drawn prefix and the remainder all match gold exactly.
        # The only error is that asking the spent handle a SECOND time hands
        # back the remainder AGAIN — a re-readable snapshot rather than a
        # one-shot traversal. Correct on exactly the sub-domain where the
        # remainder is already empty (demand >= the collection size - 1).
        "module": _flat(_handle("revSeq elements",
                                again="List.drop demand back.tail")),
        "refinement": (
            "corresponds to a backward-traversal patch that hands back a "
            "re-readable SNAPSHOT of the keys instead of a self-consuming "
            "traversal handle — the shape a patch takes when it materializes "
            "the reversed keys into a fresh container and returns that. Every "
            "value it yields on the first pass is correct, so an equality check "
            "on the first materialization passes; what fails is that the same "
            "handle can be drained twice. The failing test asserts the handle "
            "is a one-shot iterator BY TYPE, which a container is not, so the "
            "handle-type assertion fails and it does NOT resolve. Correct only "
            "where the remainder is already empty."),
        "rationale": (
            "REJECT from C3 (`out.2.2.2.1 = []`) and from C3 ALONE — C0, C1, C2, "
            "C4 and C5 are satisfied exactly, which is what makes this rival worth a "
            "build: it isolates the clause that says the traversal is ONE-SHOT "
            "rather than a re-readable snapshot, and no other rival in the "
            "battery attacks it. A spec carrying only the value clauses would "
            "admit this impl, and its faithful patch fails the failing test's "
            "own iterator-type assertion. The residual goal is exactly `⊢ "
            "List.drop demand (revSeq elements).tail = []`. Refuted at `[6, 1]` "
            "with demand 0, where what the handle has left after answering the "
            "single-element request is the non-empty `[6]`, so handing that "
            "same remainder back a second time is observably wrong; at a demand "
            "at or past the remainder's size the rival would agree with gold, "
            "which is the sub-domain conceded above. If it verified => "
            "SPEC-TOO-WEAK (the handle could be re-read)."),
        "witness": _witness("[6, 1]", 0),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-handle-restarts",
        "kind": "uniqueness",
        "expect": "reject",
        # C2 ALONE. The single-element answer is RIGHT, the drawn prefix is
        # RIGHT and the second ask is RIGHT; the error is that the handle does
        # not carry its progress — asked for what is left, it hands back the
        # WHOLE traversal from the start, so the element it already gave and the
        # elements already drawn are all repeated across the boundary.
        "module": _flat(_handle("revSeq elements", rest="back")),
        "refinement": (
            "corresponds to a backward-traversal patch whose handle does not "
            "advance: after the consumer has drawn some elements one at a time, "
            "asking the same handle for the rest restarts it from the beginning, "
            "so the drawn elements come back a second time. This is the shape a "
            "patch takes when each ask constructs a fresh traversal over the "
            "collection instead of resuming one. Materializing the handle after "
            "a partial draw therefore yields MORE keys than remain — the "
            "failing test's collection of keys 1, 2, 3 hands back 3, 2, 1 again "
            "after 3 has already been taken, so the equality assertion fails "
            "and it does NOT resolve. Correct only on the empty collection, "
            "where there is no progress to carry."),
        "rationale": (
            "REJECT from C2 (`out.2.2.1 = List.drop demand (revSeq "
            "elements).tail`) and "
            "from C2 ALONE — C0, C1, C3, C4 and C5 are satisfied exactly. This is the "
            "rival that isolates HANDLE PROGRESS: the clause says what the same "
            "handle yields afterwards is the REST, so the element it has already "
            "given and the elements already drawn "
            "are gone from it and nothing is repeated or skipped across the "
            "boundary between the two ways of asking. Nothing else in the "
            "battery attacks that independently, and a spec pinning only the "
            "drawn prefix and the one-shot emptiness would admit a handle that "
            "silently restarts. The residual goal is exactly `⊢ revSeq elements "
            "= List.drop demand (revSeq elements).tail`. Refuted at `[4, 7, 1]` "
            "with "
            "demand 1 — a non-monotone three-key input, where gold leaves [4] "
            "after the draw while the rival hands back the whole [1, 7, 4] "
            "including the key it had already given. If it verified => "
            "SPEC-TOO-WEAK (the handle need not "
            "carry its own position)."),
        "witness": _witness("[4, 7, 1]", 1),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-handle-positional",
        "kind": "uniqueness",
        "expect": "reject",
        # C4 ALONE. Every element observation is gold — the handle answers the
        # single-element request itself, advances by what was drawn, is spent
        # afterwards, and a fresh handle drained without advancing yields the
        # whole enumeration. The one difference is that a fresh handle ALSO
        # answers a positional read, with the element the backward enumeration
        # starts at: element access by INDEX, which a traversal does not have.
        # Correct on exactly the empty collection, where there is no element to
        # answer a positional read with either way.
        "module": _flat(_handle("revSeq elements", positional="back.head?")),
        "refinement": (
            "corresponds to a backward-traversal patch that hands back an object "
            "supplying its elements through the LEGACY SEQUENCE PROTOCOL — a "
            "`__next__` plus indexed element access, and no `__iter__` — instead "
            "of an iterator. Every key it yields is correct in the correct "
            "order, and it yields them to a consumer who only drains it, because "
            "`list()` falls back to reading index 0, 1, 2, ... until the object "
            "refuses. So the failing test's equality half PASSES: the keys come "
            "out 3, 2, 1. What fails is the test's FIRST assertion, that what it "
            "was handed is a `collections.abc.Iterator`: that check is "
            "`_check_methods(C, '__iter__', '__next__')`, and the indexed shape "
            "has no `__iter__`, so it is not an Iterator and the assertion fails "
            "— it does NOT resolve. MEASURED directly against CPython on the "
            "real class shape (`__next__` + `__getitem__`, no `__iter__`): the "
            "handle reproduces gold's element observations for every demand "
            "tried, and `isinstance(handle, collections.abc.Iterator)` is False "
            "where gold's is True. This rival is why C4 exists: without it the "
            "spec's element observations are ALL satisfiable by the indexed "
            "shape, so the spec would admit an implementation the failing test "
            "rejects."),
        "rationale": (
            "REJECT from C4 (`out.2.2.2.2.1 = none`) and from C4 ALONE — C0, C1, "
            "C2, C3 and C5 are satisfied exactly, which is what makes this rival "
            "the one that matters for the new clause: it isolates the clause "
            "saying a handle CANNOT be read at a position, so advancing it is the "
            "only way to take an element from it. A spec carrying only the five "
            "other clauses admits it, because supplying elements by index and "
            "supplying them by advancing produce the very same sequence "
            "observations — the difference is not a value, it is which protocol "
            "the object implements, and the failing test asserts the protocol. "
            "Refuted at `[-9, 2]` with demand 1, a two-key input with a negative "
            "key at a demand no other case uses: gold refuses the positional "
            "read while the rival answers it with 2, and every other observation "
            "agrees (answer 2; drawn [-9]; left []; second ask []; fresh drain "
            "[2, -9]). If it verified => SPEC-TOO-WEAK: the handle could be an "
            "indexable container that merely happens to enumerate correctly."),
        "witness": _witness("[-9, 2]", 1),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-handle-collectable-by-position",
        "kind": "uniqueness",
        "expect": "reject",
        # C6 ALONE. Every other observation is gold, INCLUDING the single
        # positional read of C4: asked for the element at one position, this
        # handle refuses, exactly as gold does. The one difference is that a
        # consumer who collects position by position — position 0, then 1, then
        # 2, until refused — walks away with the whole enumeration instead of
        # nothing. So the refusal is not a property of the handle, it is a
        # property of the single question C4 happens to ask, and element access
        # by position is in fact available. Correct on exactly the empty
        # collection, where there is nothing to collect by position either way.
        "module": _flat(_handle("revSeq elements", by_position="back")),
        "refinement": (
            "corresponds to a backward-traversal patch that hands back an object "
            "supplying its elements through the LEGACY SEQUENCE PROTOCOL — a "
            "`__next__` plus element access by position, and no `__iter__` — but "
            "one that DECLINES the isolated positional request while still "
            "serving a position-by-position collection. That combination is not "
            "exotic: an object whose positional access is answered relative to "
            "how far it has already been advanced, or which distinguishes the "
            "caller, refuses a bare read of one position and still serves the "
            "0, 1, 2, ... sequence that `list()` issues when there is no "
            "`__iter__`. Every key it yields is correct in the correct order, so "
            "the failing test's equality half PASSES: the keys come out 3, 2, 1. "
            "What fails is the test's FIRST assertion, that what it was handed "
            "is a `collections.abc.Iterator`: that check is "
            "`_check_methods(C, '__iter__', '__next__')`, and this shape has no "
            "`__iter__`, so the assertion fails — it does NOT resolve. MEASURED "
            "directly against CPython on such class shapes (`__next__` plus a "
            "positional accessor that refuses an isolated read, no `__iter__`): "
            "they reproduce gold's single-positional refusal AND all of gold's "
            "element observations for every demand tried, while "
            "`isinstance(handle, collections.abc.Iterator)` is False where "
            "gold's is True. This rival is why C6 exists: C4 asks about ONE "
            "position, and one refusal does not make the handle position-free, "
            "so without C6 the spec still admits an implementation the failing "
            "test rejects."),
        "rationale": (
            "REJECT from C6 (`out.2.2.2.2.2.2 = []`) and from C6 ALONE — C0, C1, "
            "C2, C3, C4 and C5 are all satisfied exactly, C4 included, which is "
            "what makes this rival the one that matters: it isolates the clause "
            "saying position-by-position collection yields NOTHING, i.e. that "
            "the handle serves no position at all rather than merely declining "
            "the one it was asked about. A spec carrying only the six other "
            "clauses admits it, because collecting by position and advancing "
            "produce the very same sequence observations — the difference is not "
            "a value, it is which protocol the object implements, and the "
            "failing test asserts the protocol. Refuted at `[5, -2, 8]` with "
            "demand 1, a three-key input with a negative key at a demand no "
            "other case pairs with it: gold's position-by-position collection "
            "is empty while the rival's is [8, -2, 5], and every other "
            "observation agrees (answer 8; drawn [-2]; left [5]; second ask []; "
            "isolated positional read refused; fresh drain [8, -2, 5]). If it "
            "verified => SPEC-TOO-WEAK: the handle could still be an object "
            "whose elements are reachable by position, which is exactly the "
            "shape that enumerates correctly and is not a traversal."),
        "witness": _witness("[5, -2, 8]", 1),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-handle-nominates-other",
        "kind": "uniqueness",
        "expect": "reject",
        # C7 ALONE. Every element observation is gold AND both positional
        # observations are gold: asked for the element at a position the handle
        # refuses, and a consumer collecting position by position walks away with
        # nothing. The one difference is WHAT the handle nominates when a
        # consumer asks it to supply the thing that is to be stepped: instead of
        # answering with ITSELF, it answers with a separate walker built over it,
        # and answers with a second, independent one when asked again — so the
        # consumer is left holding three distinct things where gold leaves it
        # holding one. Wrong at EVERY input, including the empty collection:
        # what is observed is which object comes back, not which elements it
        # would yield, so there is no sub-domain on which nominating another
        # object coincides with nominating itself.
        "module": _flat(_handle("revSeq elements", held_distinct="3")),
        "refinement": (
            "corresponds to a backward-traversal patch that hands back a "
            "REVERSIBLE CONTAINER over the keys rather than the traversal "
            "itself — the shape a patch takes when it materializes the reversed "
            "keys into a sequence, or wraps them in a small view class, and "
            "returns that. Such an object nominates a FRESH walker each time a "
            "consumer asks it to supply the thing to be stepped, so a consumer "
            "that asks twice holds two walkers plus the object: three distinct "
            "things. Every key it yields is correct in the correct order, and it "
            "yields them to a consumer that only drains it, and it serves no "
            "position at all — so the failing test's equality half PASSES (the "
            "keys come out 3, 2, 1) and BOTH positional observations agree with "
            "gold. What fails is the test's FIRST assertion, that what it was "
            "handed is a `collections.abc.Iterator`: that check is "
            "`_check_methods(C, '__iter__', '__next__')`, and it is satisfied "
            "only by an object that IS the traversal — an object which merely "
            "supplies one is a container, whose `__iter__` returns something "
            "else, so the assertion fails and it does NOT resolve. MEASURED "
            "directly against CPython on both realizations of this shape: an "
            "object with no `__iter__` at all, where the interpreter itself "
            "manufactures a fresh walker over its positional channel and the "
            "consumer ends up holding three distinct things; and an object whose "
            "`__iter__` returns an independent fresh walker over the same keys, "
            "which is likewise three. Both reproduce every one of gold's element "
            "and positional observations for every demand tried, while "
            "`isinstance(handle, collections.abc.Iterator)` is False where "
            "gold's is True. This rival is why C7 exists: C0–C6 report only "
            "WHICH ELEMENTS emerge from which channel, and both of these shapes "
            "reproduce all seven of those reports exactly, so without C7 the "
            "spec admits an implementation the failing test rejects."),
        "rationale": (
            "REJECT from C7 (`out.2.2.2.2.2.2.2 = 1`) and from C7 ALONE — C0, "
            "C1, C2, C3, C4, C5 and C6 are all satisfied exactly, the two "
            "positional clauses included, which is what makes this rival the one "
            "that matters: it isolates the clause saying the handle nominates "
            "ITSELF as the thing a consumer steps. Every other clause in the "
            "battery is a report about WHICH ELEMENTS came out of which channel, "
            "and an object that merely supplies a traversal produces the very "
            "same element reports as the traversal itself does — the difference "
            "is not a value in any sequence, it is which OBJECT the consumer is "
            "handed when it asks for the thing to step, and the failing test "
            "asserts exactly that. Note this clause is not a restatement of C4 "
            "or C6: a handle can decline every positional request and still "
            "nominate something other than itself (this rival), and both C4 and "
            "C6 are silent about object identity, which is why they cannot see "
            "it. Refuted at `[4, -6, 1]` with demand 2, a three-key input with "
            "a negative key at a demand no other case pairs with it: gold leaves "
            "the consumer holding 1 distinct thing while the rival leaves it "
            "holding 3, and every other observation agrees (answer 1; drawn "
            "[-6, 4]; left []; second ask []; isolated positional read refused; "
            "position-by-position collection empty; fresh drain [1, -6, 4]). "
            "Counting rather than comparing is deliberate and is what makes the "
            "clause unevadable by a handle that declines one of the two asks: "
            "the observation is a fact about which objects come back, so a "
            "handle that answers the first ask with itself and the second with a "
            "walker still counts 2, not 1. If it verified => SPEC-TOO-WEAK: the "
            "handle could be a container that a traversal is spun off from, "
            "which is exactly the shape that enumerates correctly, refuses every "
            "position, and is still not the traversal a consumer was handed."),
        "witness": _witness("[4, -6, 1]", 2),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-handle-unstarted",
        "kind": "uniqueness",
        "expect": "reject",
        # C5 ALONE. Every observation made through a handle that has been
        # advanced at least once is gold, and a positional read is refused; the
        # one difference is that a FRESH handle asked only to yield everything
        # yields nothing, as though its enumeration came into being only by being
        # stepped. Correct on exactly the empty collection.
        "module": _flat(_handle("revSeq elements", fresh="([] : List Int)")),
        "refinement": (
            "corresponds to a backward-traversal patch whose handle produces its "
            "enumeration only as a side effect of being advanced: it has both "
            "`__iter__` and `__next__`, so it IS an iterator, but the iterator "
            "`__iter__` hands to a consumer who has not yet stepped it is empty "
            "— the shape a patch takes when the handle populates itself lazily on "
            "the first `__next__` and `__iter__` exposes the not-yet-populated "
            "buffer. The failing test's FIRST assertion therefore passes (it is "
            "an Iterator by both methods), and the one that fails is the "
            "equality: `list(handle)` on the handle as handed back is `[]` where "
            "the test demands `[3, 2, 1]`, so it does NOT resolve. MEASURED "
            "directly against CPython on that class shape: it reproduces gold's "
            "single-element and drain observations for every demand tried while "
            "`list()` of a fresh handle is `[]`. This rival is why C5 exists: the "
            "other five clauses all observe a handle that has ALREADY been "
            "advanced at least once (C0 draws before C1, C2 and C3 look), so "
            "none of them can see this difference, and the spec would admit an "
            "implementation the failing test rejects."),
        "rationale": (
            "REJECT from C5 (`out.2.2.2.2.2 = revSeq elements`) and from C5 "
            "ALONE — C0, C1, C2, C3 and C4 are satisfied exactly. It isolates "
            "the clause that says the enumeration is ALREADY THERE to be had: a "
            "consumer who only drains the handle it was given, without first "
            "asking it to advance, gets the whole backward enumeration. That is "
            "the failing test's own call shape (`list(reversed(...))` with no "
            "prior draw), and it is unobservable to C0–C3 because those all "
            "look at a handle the single-element request has already stepped. "
            "Refuted at `[3, 9, 4, 1]` with demand 2 — the battery's second "
            "length-4 point, where gold's fresh drain is [1, 4, 9, 3] and the "
            "rival's is []; every other observation agrees (answer 1; drawn "
            "[4, 9]; left [3]; second ask []; positional refused). If it "
            "verified => SPEC-TOO-WEAK (the handle's enumeration could exist "
            "only for a consumer who steps it first)."),
        "witness": _witness("[3, 9, 4, 1]", 2),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-handle-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # C1 vs C2 CONFUSION: the two halves are produced but handed back the
        # wrong way round. Everything about the reversal is right, and the
        # handle's own answer to the single-element request is right; only which
        # part answers which of the LATER questions is wrong. Correct exactly on
        # the collections of at most one key, where what the handle has left
        # after answering is empty and the swap is invisible.
        "module": _flat(_handle("revSeq elements",
                                drawn="List.drop demand back.tail",
                                rest="List.take demand back.tail")),
        "refinement": (
            "corresponds to a backward-traversal patch that gets the split "
            "point right but attributes the pieces to the wrong asks: the "
            "consumer's single-element draws hand back the tail of the "
            "traversal while the subsequent drain hands back the elements that "
            "should have come out one at a time. The multiset of keys the "
            "consumer sees across both asks is complete and the reversal itself "
            "is correct, so a check on the concatenation would pass; the "
            "failing test materializes the handle and demands 3, 2, 1 in that "
            "order from it, which this does not deliver, so it does NOT "
            "resolve. Correct exactly on the collections of at most one key, "
            "where what the handle has left after answering the single-element "
            "request is empty and both halves collapse."),
        "rationale": (
            "REJECT from C1 and C2 SIMULTANEOUSLY (C0, C3, C4 and C5 hold), and it is "
            "the rival that "
            "shows those two clauses are not interchangeable: the spec does not "
            "merely require that the two answers PARTITION what the handle has "
            "left, it "
            "requires that the prefix answer the single-element draws and the "
            "suffix answer the drain. A spec that pinned only the concatenation "
            "`out.2.1 ++ out.2.2.1 = (revSeq elements).tail` would admit this "
            "impl. "
            "Refuted at `[1, 2, 3]` with demand 1, where gold answers 3, then "
            "draws [2] and leaves [1], while the rival answers 3, then draws [1] "
            "and leaves [2]. Note "
            "this uses the F2P collection at a DIFFERENT demand from "
            "weak-forward-order's, which is what makes it a distinct point. If "
            "it verified => SPEC-TOO-WEAK (the "
            "two ways of asking could be confused)."),
        "witness": _witness("[1, 2, 3]", 1),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-demand-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # THE `demand` BINDER, attacked alone. This rival is CORRECT at every
        # demand > 0 (measured: `reverseEnumTester [7, 2] 1 = true` elaborates
        # against it) and wrong ONLY at demand = 0, where it hands everything the
        # handle has left to the draw and leaves nothing. Without this case, a rival
        # that mishandled only the zero-demand boundary would verify and the
        # battery would never notice.
        "module": _flat(
            "    let back := revSeq elements\n"
            "    if demand = 0 then\n"
            "      return (back.head?, back.tail, ([] : List Int), ([] : List Int),\n"
            "        (none : Option Int), back, ([] : List Int), (1 : Nat))\n"
            "    else\n"
            "      return (back.head?, List.take demand back.tail,\n"
            "        List.drop demand back.tail, ([] : List Int),\n"
            "        (none : Option Int), back, ([] : List Int), (1 : Nat))\n"),
        "refinement": (
            "corresponds to a backward-traversal patch that special-cases the "
            "consumer who draws NO single elements before draining — handing "
            "that consumer everything through the draw channel and leaving the "
            "drain empty. It is right for every consumer who draws at least "
            "one element, so the failing test (which materializes the handle "
            "in one go) is unaffected in the drawn values; what it gets wrong "
            "is which channel a zero-draw consumer is served through, and a "
            "consumer that drains without drawing first sees an empty result "
            "where the whole reversal was due. That is a real behavioural "
            "difference from the change, and a patch shaped this way would "
            "hand an empty traversal to a consumer that materializes the handle "
            "without drawing from it first — the exact shape of the call the "
            "failing test makes — so it does NOT resolve."),
        "rationale": (
            "REJECT from C1 and C2 at the `demand = 0` boundary (C0, C3, C4 and C5 "
            "hold), and this case "
            "exists to VARY THE SECOND BINDER. Every other rival is wrong at "
            "many demands, so each of their witnesses would still discriminate "
            "if the clauses were weakened to hold only at positive demands; "
            "this one is wrong at exactly one value of `demand` and correct "
            "everywhere else, which was verified by evaluation — "
            "`reverseEnumTester [7, 2] 1 = true` ELABORATES against this rival "
            "(exit 0), so it genuinely agrees with gold off the boundary. "
            "Refuted at `[7, 2]` with demand 0, where gold answers 2, draws "
            "nothing and leaves [7], while the rival answers 2, draws [7] and "
            "leaves nothing. If it verified => "
            "SPEC-TOO-WEAK (the clauses would not constrain the zero-draw "
            "consumer, and `demand` would be a binder no rival could abuse)."),
        "witness": _witness("[7, 2]", 0),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-fixed-draw",
        "kind": "uniqueness",
        "expect": "reject",
        # `demand` IGNORED: the handle always advances exactly one further step
        # regardless of how many single elements the consumer asked for.
        # Correct at demand = 1, and on the collections of at most one key where
        # there is nothing left to advance through.
        "module": _flat(_handle("revSeq elements",
                                drawn="List.take 1 back.tail",
                                rest="List.drop 1 back.tail")),
        "refinement": (
            "corresponds to a backward-traversal patch whose handle advances by "
            "a FIXED step rather than by what the consumer actually drew — the "
            "shape a patch takes when the position is hardcoded instead of "
            "tracked. A consumer that draws three single elements gets one, and "
            "the drain then hands back the two it should already have consumed. "
            "The failing test's collection of keys 1, 2, 3 is not delivered as "
            "3, 2, 1 across the two asks, so it does NOT resolve. Correct at "
            "demand 1, and where there is nothing left to advance through."),
        "rationale": (
            "REJECT from C1 and C2 (C0, C3, C4 and C5 hold): both clauses are functions "
            "of `demand`, and "
            "this rival ignores it. Where weak-demand-zero attacks one boundary "
            "value of that binder, this attacks the binder's role entirely — "
            "the traversal must advance by what was drawn, not by a constant. "
            "Refuted at `[8, 2, 5]` with demand 3, a demand EQUAL to the "
            "collection size and so one past what the handle has left: gold "
            "answers 5 and draws [2, 8], leaving nothing, while the "
            "rival answers 5 and draws only [2], leaving [8]. Together with "
            "weak-demand-zero (demand 0), weak-handle-swapped (demand 1) and "
            "weak-f2p-gated (demand 4, past the size) this puts the second "
            "binder across the whole of its meaningful range. If it verified => "
            "SPEC-TOO-WEAK (`demand` would not have to be honoured)."),
        "witness": _witness("[8, 2, 5]", 3),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-f2p-gated",
        "kind": "uniqueness",
        "expect": "reject",
        # The one axis every other rival misses: this rival AGREES WITH GOLD AT
        # THE F2P'S OWN INPUT and diverges only off it, so it is the case that
        # attests the clauses are UNIVERSALLY quantified rather than an
        # F2P-shaped spot check.
        "module": _flat(_handle(
            "(if elements.length ≤ 3 then revSeq elements else elements)")),
        "refinement": (
            "corresponds to a backward-traversal patch that reverses only small "
            "collections and silently falls back to the forward iterator on "
            "larger ones — the shape a patch takes when the reversal is "
            "special-cased behind a size guard. The failing test's own "
            "collection of three keys materializes CORRECTLY as 3, 2, 1, so "
            "this rival's faithful patch DOES pass the failing test and would "
            "be scored as resolving. It is still wrong: any collection of four "
            "or more keys is handed back in insertion order, which is the very "
            "behaviour the change replaces. That combination — passes the F2P, "
            "wrong in general — is exactly what a full-functional spec is for, "
            "and it is why this case is worth a build."),
        "rationale": (
            "REJECT from C0, C1, C2 and C5: the clauses are quantified over EVERY "
            "finite sequence, so agreeing with the reversal on a bounded "
            "sub-domain is not enough. Refuted at `[1, 2, 3, 4]` with demand 4 "
            "— the only length-4 point in the battery and the only demand "
            "past 3, chosen because it is the smallest input off the rival's "
            "correct sub-domain: gold answers 4 and draws [3, 2, 1] while the "
            "rival answers 1 and draws [2, 3, 4]. Uniquely among these rivals it "
            "AGREES with gold at "
            "the F2P input, so it is the only case whose rejection attests to "
            "the universal quantification rather than to the F2P-shaped points: "
            "shrink the clauses to 'hold at collections of at most three keys' "
            "and every other witness in this battery still discriminates, while "
            "this one no longer does. If it verified => SPEC-TOO-WEAK (the pin "
            "would be an F2P-shaped spot check)."),
        "witness": _witness("[1, 2, 3, 4]", 4),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING
#
# The sibling battery ships 7 SPEC cases (2 soundness, 1 admissibility, 4
# uniqueness — one the MANDATORY frame-mutation rival) plus an AXIOM lane of 2
# probes. It contracts ONE function over ONE read-only sequence with the single
# pin that the result IS the front-recursive reversal of the input.
#
# This bundle models MORE than the sibling, not less: the observable here is the
# traversal HANDLE, so the same reversal is pinned through SIX independent
# clauses over TWO binders (`elements` and `demand`). So this is not a
# carrier-narrowing port — it is a carrier-WIDENING one, and the extra rivals
# below are not padding: C0, C2, C3, C4 and C5 are clauses the sibling's spec
# does not have, and each needs its own attacker.
#
#   sibling case              kind          -> here                            disposition
#   -----------------------------------------------------------------------------------------
#   pos-assert-reorder        soundness     -> pos-loop-preserving             PORTED
#   pos-assert-reversal       soundness     -> pos-direct-model                RE-EXPRESSED
#   (no sibling)              soundness     -> pos-stdlib-reversal             ADDED (carrier)
#   (no sibling)              soundness     -> pos-forward-loop                ADDED
#   admiss-f2p-shape          admissibility -> admiss-f2p-point                RE-AIMED
#   forward-order             uniqueness    -> weak-forward-order              PORTED
#   drop-first-element        uniqueness    -> weak-drop-first-element         PORTED
#   always-empty              uniqueness    -> weak-always-empty               PORTED
#   frame-mutate-elements     uniqueness    -> (none)                          VACUOUS (measured)
#   (no sibling)              uniqueness    -> weak-drop-last-element          ADDED
#   (no sibling)              uniqueness    -> weak-head-pinned-tail-reversed  ADDED
#   (no sibling)              uniqueness    -> weak-positions-not-elements     ADDED
#   (no sibling; C0)          uniqueness    -> weak-handle-refuses-single      ADDED (clause)
#   (no sibling; C3)          uniqueness    -> weak-handle-rereadable          ADDED (clause)
#   (no sibling; C2)          uniqueness    -> weak-handle-restarts            ADDED (clause)
#   (no sibling; C4)          uniqueness    -> weak-handle-positional          ADDED (clause)
#   (no sibling; C5)          uniqueness    -> weak-handle-unstarted           ADDED (clause)
#   (no sibling; C1 vs C2)    uniqueness    -> weak-handle-swapped             ADDED (clause)
#   (no sibling; `demand`)    uniqueness    -> weak-demand-zero                ADDED (binder)
#   (no sibling; `demand`)    uniqueness    -> weak-fixed-draw                 ADDED (binder)
#   (no sibling)              uniqueness    -> weak-f2p-gated                  ADDED
#   AXIOM_TESTS (2)           axiom         -> (none)                          DROPPED (G-AX lane)
#   (no sibling)              divergence    -> (none)  REJECTED-BY-SPEC, UNWITNESSABLE
#
# 20 velvet SPEC cases: 4 soundness, 1 admissibility, 15 uniqueness. (Reported
# by the gate as `lanes`: {'admissibility': 1, 'soundness': 4, 'uniqueness': 15}.)
#
# PORTED (pos-assert-reorder -> pos-loop-preserving): the sibling rewrites the
#   loop guard and reorders two independent framing steps, keeping the gold loop
#   shape so the front-recursive unfold still discharges. Here the guard rewrite
#   and the element-binding inline are near-definitional, so the case ALSO
#   reorders the second loop's two independent invariants — the true analogue of
#   "reorder the independent framing steps" — and the FROZEN proof script closes
#   it unchanged.
# RE-EXPRESSED (pos-assert-reversal -> pos-direct-model): the sibling asserts,
#   just before returning, that what the loop built equals the spec model, its
#   point being that no executable materialization of the model exists so the
#   cheapest impl still does the real work. On this carrier the model IS an
#   executable `def`, so the honest cheapest impl is to RETURN it, which makes
#   the same point more directly: if returning the model itself is correct (and
#   it is — grounded in the argument, not an answer key) then the pin is not
#   echo-vulnerable, and the fifteen rivals show every wrong expression failing
#   it. Doubles as the proof-shape control.
# ADDED (pos-stdlib-reversal): required by THIS carrier for two reasons. As a
#   positive it is the only case reaching the pinned sequence by a DIFFERENT
#   recursion than the spec's own, so it distinguishes "the spec pins the value"
#   from "the spec pins the model term". As infrastructure it is the battery's
#   `witness_reference`: the frozen loops cannot decide anything, so without a
#   verifying loop-free impl to refute against, all fifteen reject cases would
#   record `witness-undecided`.
# ADDED (pos-forward-loop): the sibling explicitly DECLINED the opposite-direction
#   reshape, on the ground that it needs an `f(a ++ b)` homomorphism the verifier
#   will not auto-discharge — correctly, for its carrier, since that would have
#   been a PROOF gap rather than a spec defect. Here the lemma is supplied as an
#   in-body `have` (no new top-level declaration, nothing assumed) and the case
#   VERIFIES, so the sibling's declined probe is landed rather than inherited as
#   an assumption.
# RE-AIMED (admiss-f2p-shape -> admiss-f2p-point): the sibling self-calls on the
#   F2P-shaped input [1,2,3] to show a normal collection satisfies its read-only
#   half-permission precondition. This method has NO `require`, so nothing could
#   exclude any input and that exact probe is degenerate; per the brief the
#   analogue here is the obligation being UNSATISFIABLE at an F2P-shaped input,
#   which this case tests directly by dispatching on the literal input and
#   returning the literal expected 6-tuple, forcing all six clauses to be
#   discharged at closed terms. NOT omitted as a vacuous class.
# PORTED (forward-order, drop-first-element, always-empty): all three carry
#   across with their refinement arguments intact — a traversal that preserves
#   rather than reverses the order, one that stops a step early, and one that
#   yields nothing all fail the same equality assertion in the same failing
#   test. Only the mechanics change: the sibling reshapes the loop (and for
#   forward-order must also swap the invariant to keep Viper from diverging on an
#   unbounded model unfold); here each is a loop-free `return`, which is what
#   makes its witness reduce.
# ADDED (drop-last-element, head-pinned-tail-reversed, positions-not-elements):
#   the three ported rivals attack the HEAD boundary, the whole ORDER, and the
#   whole OUTPUT, leaving three ways to be wrong unattacked — dropping the LAST
#   element, getting length and multiset right but the order only partly right,
#   and getting length and ordering direction right but yielding positions
#   instead of keys. The position rival in particular is refuted at `[9, 4]`
#   rather than `[0, 1]`, where it would agree with gold.
# ADDED FOR THE CLAUSES THE SIBLING'S SPEC DOES NOT HAVE (handle-refuses-single,
#   handle-rereadable, handle-restarts, handle-positional, handle-unstarted,
#   handle-swapped): C0, C2, C3, C4 and C5 are independent of C1 and of each
#   other, and the first five of these rivals satisfy the other five clauses
#   EXACTLY while breaking one (verified from the residual goals: each build
#   leaves exactly one `ensures` case open).
#   handle-refuses-single satisfies C1–C5 and breaks only C0 — the handle
#   will not answer a single-element request put to it, so a consumer must derive
#   a further traversal from it first, which is precisely what the failing test's
#   Iterator assertion refuses; handle-rereadable breaks only C3 (the handle is a
#   re-readable snapshot); handle-restarts breaks only C2 (the handle does not
#   carry its progress); handle-positional breaks only C4 (the handle also serves
#   element access by index, the legacy `__getitem__` sequence-protocol shape,
#   which enumerates correctly but is not an Iterator); handle-unstarted breaks
#   only C5 (the handle's enumeration exists only once it has been stepped, so a
#   consumer who merely drains it gets nothing);
#   handle-swapped gets the partition right but attributes the halves to the
#   wrong asks, so a spec pinning only `out.2.1 ++ out.2.2.1 = (revSeq
#   elements).tail` would admit it. Without these six, five of the spec's six
#   clauses would be defended but never attacked. C4 and C5 in particular were
#   added to this battery because both were MEASURED, in CPython, to be the only
#   observations that separate gold from an impostor reproducing every one of
#   C0–C3: an object with `__next__` + `__getitem__` and no `__iter__` (fails the
#   test's `assertIsInstance`), and an iterator whose `__iter__` is empty until it
#   has been advanced (fails the test's `assertEqual`).
# ADDED FOR THE SECOND BINDER (demand-zero, fixed-draw): `demand` is an input
#   binder, and a binder every witness holds at one value is a binder no rival
#   was built to abuse. demand-zero is wrong at demand = 0 ONLY — measured
#   correct at demand 1 against its own tester — so it is refuted at the one
#   value that discriminates it; fixed-draw ignores `demand` entirely and is
#   refuted at a demand equal to the collection size.
# VACUOUS (frame-mutate-elements): the sibling's MANDATORY #1 attack writes to an
#   input held at half permission and must be rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent: `elements` is an
#   immutable read-only value (no input is `mut`; only the loop-locals are), with
#   no heap, no aliasing, no `Old`, and no permission system. MEASURED, not
#   asserted: the nearest expressible analogue — assigning to `elements` inside
#   the impl region — was BUILT, and the carrier refuses it at ELABORATION,
#   "`elements` cannot be mutated, only variables declared using `let mut` can be
#   mutated". So a ported frame rival would reject for a binder/parse reason with
#   no spec content and nothing for a witness to state. Not ported; no substitute
#   fabricated. NOTE the asymmetry with the sibling's own reading: it argues no
#   faithful resolving patch corresponds to the frame rival either (a real
#   backward traversal does not overwrite the collection it walks), so nothing
#   behavioural is lost — only the permission-system probe, which has no
#   analogue. Note also that the read-only frame IS still pinned here, but by the
#   carrier rather than by a clause.
# DROPPED (AXIOM_TESTS, 2): the sibling's axiom-soundness and containment probes
#   execute the real underlying primitive and are G-AX's job here —
#   axiom_check.py / mapping.md §3.1, where `revSeq` is an A-reference deep model
#   rather than a consumed axiom. G-PBT ignores AXIOM_TESTS regardless. NOTE what
#   is NOT delegated there: the one-shot self-advancing traversal the failing test
#   asserts is BEHAVIOUR, and it is pinned by the frozen spec itself in C0, C3,
#   C4 and C5, attacked by weak-handle-refuses-single, weak-handle-rereadable,
#   weak-handle-positional and weak-handle-unstarted. The axiom
#   lane checks only that `revSeq` agrees with the real reversal value-for-value.
# DIVERGENCE — REJECTED BY THE SPEC, but NOT SHIPPABLE, and the two halves of
#   that are separate findings. The semantics half is GOOD NEWS: this bundle sets
#   `loom.semantics.termination "total"` AND carries `open TotalCorrectness`, and
#   both diverging rivals were BUILT and REFUSED — dropping the measure gives
#   "Decreasing annotations are required in total correctness semantics", and a
#   CONSTANT measure gives `case «decreasing_1: elements.length» ⊢ False`. So a
#   non-terminating impl does NOT satisfy the clauses vacuously; this is not the
#   `partial`-semantics hole and it is not a spec weakness. The witness half is
#   why it is not shipped: the constant-measure rival computes exactly GOLD'S
#   VALUES, so there is no input at which its output disagrees with the spec, and
#   measured against it BOTH `reverseEnumTester [1,2,3] 2 = false` AND `= true`
#   fail by stuck reduction. There is no discriminating witness because there is
#   no value-level divergence — the rejection is a judgement of the termination
#   obligation, not a postcondition violation at a point. Per the authoring
#   brief a rival with no witness the author has SEEN discriminate must not be
#   shipped, so it is recorded here instead. Neither a spec hole nor a battery
#   gap.
#
# CLAUSE / BINDER / POINT COVERAGE.
#   SIX `ensures` clauses, each DEFENDED and each ATTACKED (the per-rival counts
#   below are read off the `case «ensures_N: ...»` headers the builds leave open,
#   not assigned by hand — see the numbering note in the PROOF-SHAPE CONTROL):
#     C0 out.1         = (revSeq elements).head?
#        defended by all 4 positives + admiss; attacked by 8 rivals, and SOLELY
#        by weak-handle-refuses-single — the clause that says the handle answers
#        a single-element request BY ITSELF.
#     C1 out.2.1       = take demand (revSeq elements).tail
#        defended by all 4 positives + admiss; attacked by 10 rivals.
#     C2 out.2.2.1     = drop demand (revSeq elements).tail
#        defended by all 4 positives + admiss; attacked by 11 rivals, and
#        SOLELY by weak-handle-restarts.
#     C3 out.2.2.2.1   = []
#        defended by all 4 positives + admiss; attacked SOLELY by
#        weak-handle-rereadable — the clause that would otherwise be
#        defended-but-unattacked.
#     C4 out.2.2.2.2.1 = none
#        defended by all 4 positives + admiss; attacked SOLELY by
#        weak-handle-positional — the clause that refuses element access by
#        INDEX, so a consumer can only take elements by advancing the handle.
#     C5 out.2.2.2.2.2 = revSeq elements
#        defended by all 4 positives + admiss; attacked by 8 rivals, and SOLELY
#        by weak-handle-unstarted — the clause that says a handle which is only
#        drained, never advanced, still yields the whole backward enumeration.
#        This is the failing test's own call shape, `list(reversed(...))`.
#   BOTH input binders are moved by the reject witnesses (15 distinct
#   (elements, demand) points; no two cases share one):
#     weak-forward-order               [1, 2, 3]    2   the F2P point
#     weak-drop-first-element          [2, 5, 9]    3   demand past the remainder
#     weak-drop-last-element           [-3, 8]      2   a NEGATIVE key
#     weak-head-pinned-tail-reversed   [2, 9, 4]    3   non-monotone
#     weak-positions-not-elements      [9, 4]       2   keys != their positions
#     weak-always-empty                [5]          1   smallest non-empty
#     weak-handle-refuses-single       [-7]         0   singleton, negative key,
#                                                       where C1/C2/C3 are all
#                                                       vacuous so ONLY C0 can
#                                                       carry the refutation
#     weak-handle-rereadable           [6, 1]       0   remainder non-empty
#     weak-handle-restarts             [4, 7, 1]    1   0 < demand < size
#     weak-handle-positional           [-9, 2]      1   negative key; the only
#                                                       point where the sole
#                                                       divergence is a served
#                                                       positional read
#     weak-handle-unstarted            [3, 9, 4, 1] 2   second length-4 point;
#                                                       the sole divergence is
#                                                       the fresh drain
#     weak-handle-swapped              [1, 2, 3]    1   F2P keys, other demand
#     weak-demand-zero                 [7, 2]       0   the zero-draw consumer
#     weak-fixed-draw                  [8, 2, 5]    3   demand == size
#     weak-f2p-gated                   [1, 2, 3, 4] 4   demand PAST the size,
#                                                       and the only point off
#                                                       the F2P sub-domain
#   So `elements` ranges over lengths {1, 2, 3, 4}, over negative and positive
#   keys, over monotone and non-monotone orderings, and over keys that do and do
#   not coincide with their own positions; `demand` ranges over {0, 1, 2, 3, 4},
#   covering the empty draw, a partial draw, a draw equal to the size, and a
#   draw PAST the size (the "asking past the end simply yields fewer"
#   sub-domain). MEANINGFULNESS is value-for-value — gold vs rival at each point,
#   written (answer; drawn; left): (3;[2];[1]) vs (1;[2,3];[]);
#   (9;[5,2];[]) vs (9;[5];[]); (8;[-3];[]) vs (-3;[];[]);
#   (4;[9,2];[]) vs (2;[4,9];[]); (4;[9];[]) vs (1;[0];[]);
#   (5;[];[]) vs (none;[];[]); (-7;[];[]) vs (none;[];[]);
#   second ask [] vs [6]; left [4] vs [1,7,4];
#   positional read refused vs answered with 2; fresh drain [1,4,9,3] vs [];
#   (3;[2];[1]) vs (3;[1];[2]);
#   (2;[];[7]) vs (2;[7];[]); (5;[2,8];[]) vs (5;[2];[8]);
#   (4;[3,2,1];[]) vs (1;[2,3,4];[]).
#   Every witness states its refutation at concrete literals and binds no
#   hypothesis, so no consistency probe applies and none is needed.
#
# WITNESS MECHANICS, measured with scripts/lean_verify.sh (60 builds, the full
#   2x2 for every reject case, 0 mismatches; see the CARRIER NOTE for why the
#   reference and not gold is the second subject):
#     - ELABORATES against its rival: all fifteen exit 0.
#     - REFUTED against `pos-stdlib-reversal` (the `witness_reference`): all
#       fifteen exit 1 with `Tactic `decide` proved that the proposition
#       reverseEnumTester <point> = false is false` — a SEMANTIC refutation, not
#       a stuck build.
#     - FORGERY control (flip `= false` to `= true`, i.e. claim the rival is
#       CORRECT at that point): all fifteen invert exactly — exit 1 against the
#       rival, exit 0 against the reference. So the reference side's exit code
#       tracks the CLAIM and not the build.
#     - Against the FROZEN solution the witnesses fail by STUCK REDUCTION, and
#       so does a TRUE claim: `reverseEnumTester [1,2,3] 2 = true` and
#       `= false` both exit 1 with `reduction got stuck at the `Decidable`
#       instance`. That is precisely why the frozen impl cannot be the subject.
#     - Proof-shape control: `pos-direct-model` is the rivals' exact shape and
#       exact tactic body with the right expression and exits 0, so no rejection
#       here is a tactic artifact; each rival's residual goal was read off its
#       build log and names its own expression.
AXIOM_TESTS = []
