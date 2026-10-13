"""properties.py — G-PBT falsification battery for sympy__sympy-23824 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_prependLeading``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` HOLDS of the
rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models one function ``restore_leading(leading, tail)`` under fractional-
permission contracts, with the load-bearing postcondition
``ToSeq(Result()) == ToSeq(leading) + ToSeq(tail)`` — order-preserving
concatenation. This Lean bundle models the SAME behavior generalised to the
whole additive expansion: one total function attaching the leading block
(``labels.take leadCount``, in order) to the front of every term. The nagini
``leading``/``tail`` split becomes ``labels.take leadCount`` (the leading block)
applied uniformly to each element of ``terms``; the ORDER crux is identical. The
mapping of each nagini case to its Lean counterpart (or its principled omission)
is in the module ``assessment`` below.

DEFENDED SURFACE (one modeled behavior). The postcondition
``problem_spec_prependLeading`` pins ``result`` to a single grounded computation
over the inputs with two INDEPENDENT top-level clauses:

  * a LENGTH clause: ``result.length = terms.length`` — the number of terms is
    unchanged;
  * a per-element ORDER clause: for every ``i < terms.length``,
    ``result[i]! = labels.take leadCount ++ terms[i]!`` — each term is the
    leading block, IN ORDER, followed by the original term.

The BEHAVIOURAL DISCRIMINATOR (the fix): the leading block is attached in its
ORIGINAL left-to-right order, never reversed, and the whole block is attached
(none dropped), leaving each original term intact. The pre-fix behavior laid the
leading labels down one at a time at the front, which REVERSES the block; the
``rival-reverse-lead`` case below IS that behavior.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and DEMONSTRATED so rather than
    asserted. Lean is referentially transparent: an input carries no heap
    permission, there is no read-only half-permission to overwrite and no
    aliasing to exploit. The two nagini frame-mutation rivals
    (``frame-mutate-leading-append`` — append into the read-only ``leading``;
    ``frame-mutate-tail-index`` — in-place store into the read-only ``tail``)
    have no expressible instance here; no substitute is fabricated. The audit
    measured the collapse instead of arguing it: the nearest expressible
    analogue of a write to an input — a local ``let mut scratch := labels`` that
    is appended to before the gold value is computed — ELABORATES (exit 0), so
    there is no obligation such a rival could fail. ``labels`` is a value, the
    write rebinds a copy, and no clause of the spec can observe it. A rival built
    on that shape would be an ``expect="reject"`` case that verifies, i.e. a
    manifest defect, not a probe. See ``assessment``.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned to a term built only from the inputs (``labels.take leadCount`` and
    the elements of ``terms``). There is no opaque callee and no answer-key an
    implementation could echo (the carrier is fully transparent — every witness
    below is ``decide``-able). In its place the battery carries honest
    positive controls (soundness + admissibility) that must verify.

  * PARTIAL-DOMAIN / VALUE / ORDER — APPLIES. Rivals correct on part of the
    domain but diverging where the fix bites: reversing the leading block
    (THE bug), dropping the leading item of the block, reversing each term, and
    dropping a term (the length clause).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it by ``decide`` (the carrier is fully transparent).
Each was BUILT and checked to HOLD of its rival (elaborates) and to FAIL on the
frozen solution (``decide`` proves the negation false there), so it discriminates
rather than asserting a tautology. All six witnesses bind nothing (literal
inputs), so no consistency probe applies. The audit re-derived all of them
independently: every witness built against its rival at exit 0 and against the
frozen solution at exit 1, and each gold-side failure is the SEMANTIC one —
``Tactic `decide` proved that the proposition ¬(...) is false``, the spec
predicate fully reduced at the literal input — not a missing name, a type error,
an unfolding failure, or a timeout.

FORGERY CONTROL (the gold-side exit code carries information about the CLAIM).
A gold-side failure is admissible evidence only if it CHANGES when the claim
changes, so each witness was rebuilt with its claim FLIPPED (the leading ``¬``
dropped, asserting the spec HOLDS at that input) and built against both sides.
Every flipped claim inverted cleanly: exit 0 against the frozen solution (gold
does satisfy the spec there) and exit 1 against the rival. So no witness's
verdict is an artifact of a build that would have failed whatever it asserted;
each gold-side rejection tracks the concrete proposition, which is what makes
the rejection attributable to the spec.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
rather than fixing them at one point: ``leadCount`` takes 2, 3, 1, 1, 1, 1;
``labels`` ranges over ``[1,2]``, ``[1,2,3]``, ``[9]``, ``[9,7]``; ``terms``
ranges over the EMPTY list, a single term, two terms, and a term of length ≥2.
The six reject witnesses probe six DISTINCT inputs. Both independent top-level
clauses of the postcondition are attacked: the per-element ORDER clause by three
rivals (reverse-lead, drop-first-lead, reverse-tail) and the LENGTH clause in
BOTH directions — downward by ``rival-drop-term`` (result too short) and upward
by ``rival-extra-term`` (result too long). The upward direction is a separate
obligation, and the audit measured that rather than assuming it: under a spec
whose length clause is weakened from ``result.length = terms.length`` to
``terms.length ≤ result.length``, all five other rivals are STILL refuted at
their own witness points (machine-checked), while an extra-term rival satisfies
the weakened predicate at the very input that refutes it under the frozen ``=``.
So without ``rival-extra-term`` nothing in the battery attests that the length
clause is an equality rather than a lower bound. That rival also carries the
only witness at ``terms = []``, the boundary at which the whole per-element
clause is vacuous and the length clause is the sole remaining constraint.
The ``leadCount`` binder additionally gets a rival of its own
(``rival-ignore-leadcount``) at a point where ``labels`` is LONGER than the
leading block, which is the shape the modeled slice actually sees — the carrier
list is as long as the whole position vector while only its first ``leadCount``
entries form the block — and which the other four rivals never reach, since each
of them holds ``labels.length = leadCount``. Without it the prefix-SELECTION
half of ``labels.take leadCount`` is unattacked: every rival would still be
refuted if the spec said ``labels`` where it says ``labels.take leadCount``.

DIVERGENCE lane: VACUOUS on this carrier, and demonstrated rather than asserted.
The frozen bundle sets no ``loom.semantics.termination`` option — it is plain
Lean with no Loom termination pragma — so every ``def`` in it is already
total by elaboration: the modeled behavior is a single non-recursive ``for``
over a finite ``List``, and there is no loop for which a decreasing measure
could be missing. The one shape that expresses non-termination here is a
``partial def``, and the audit built it: making the implementation ``partial
def implementation_prependLeading ... := implementation_prependLeading ...``
elaborates the definition but the frozen obligation then fails at exit 1 with
``Tactic `unfold` failed to unfold `implementation_prependLeading``` — a
``partial def`` is compiled to an opaque constant with no equation lemmas, so
the postcondition is not vacuously satisfied but simply unreachable. That
rejection is a TOOLING artifact (the term cannot be unfolded), not a refutation
attributable to the spec, and no witness can discriminate it: the audit
confirmed this by building the impl-agnostic refutation
``example (v) (hne : v ≠ [[9,5]]) : ¬ problem_spec_prependLeading 1 [9] [[5]] v``
— it elaborates at exit 0 against the FROZEN solution, i.e. it is a tautology
over an unconstrained result and would "refute" gold too. So there is nothing
shippable in this lane on this carrier: no diverging rival can be given a
witness that tracks the spec. Recorded as vacuous, not as a hole in the spec.

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the modeled slice calls only concrete list ops — ``List.take`` /
``List.append`` — mapped identity from the Python builtins). The nagini
``AXIOM_TESTS`` were also empty; dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23824"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The gold impl BODY (strictly inside the impl region). Every rival swaps on
# this; the soundness variant swaps the wider anchor below.
_I_GOLD = (
    "  let lead := labels.take leadCount\n"
    "  let mut out : List (List Int) := []\n"
    "  for t in terms do\n"
    "    out := out ++ [lead ++ t]\n"
    "  return out"
)

# The gold impl body PLUS the `Id.run do` header line (impl region), so the
# soundness variant can drop the imperative shape for a pure `map`.
_I_GOLD_WITH_HEAD = (
    "    List (List Int) := Id.run do\n" + _I_GOLD
)

# The proof-region helper lemma (a proof helper the frozen bundle declares; the
# pure-map soundness variant no longer needs it). Removing an existing decl is
# in scope — only NEW theorems/lemmas are barred.
_P_HELPER = (
    "theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :\n"
    "    ∀ (init : List (List Int)),\n"
    "      Id.run (forIn terms init (fun t r =>\n"
    "        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by\n"
    "  induction terms with\n"
    "  | nil =>\n"
    "    intro init\n"
    "    show Id.run (pure init) = _\n"
    "    rw [Id.run_pure]; simp\n"
    "  | cons a as ih =>\n"
    "    intro init\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind, pure] at ih ⊢\n"
    "    rw [ih]\n"
    "    simp [List.append_assoc]\n\n"
)

# The frozen `correct_prependLeading` proof BODY (proof region). Statement is
# never touched; only this tactic body is edited.
_P_GOLD = (
    "  intro leadCount labels terms\n"
    "  unfold problem_spec_prependLeading implementation_prependLeading\n"
    "  simp only [Id.run, bind]\n"
    "  have h := helper_prependLeading (labels.take leadCount) terms []\n"
    "  simp only [Id.run] at h\n"
    "  rw [h]\n"
    "  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧\n"
    "      ∀ i, i < terms.length →\n"
    "        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!\n"
    "  refine ⟨by simp, ?_⟩\n"
    "  intro i hi\n"
    "  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]\n"
    "  rw [List.getElem?_map, List.getElem?_eq_getElem hi]\n"
    "  simp"
)

# The pure-map soundness proof (closes for the reshaped impl; no new lemma).
_P_MAP = (
    "  intro leadCount labels terms\n"
    "  unfold problem_spec_prependLeading implementation_prependLeading\n"
    "  refine ⟨by simp, ?_⟩\n"
    "  intro i hi\n"
    "  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]\n"
    "  rw [List.getElem?_map, List.getElem?_eq_getElem hi]\n"
    "  simp"
)


def _rival(impl_body):
    """A wrong impl: swap only the gold impl body inside the impl region."""
    return _swap(_BASE, _I_GOLD, impl_body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. The
    # theorem statement stays byte-identical; the proof is re-authored to close
    # for the new impl shape (no helper lemma, no axiom, no assumption token).
    #
    # Ports nagini case `pos-local-reshape`: the nagini positive kept the
    # forward two-phase append but renamed counters / cached bounds / reordered
    # invariant lines. Here the analogous structurally-different-but-correct
    # reshape drops the imperative accumulator loop entirely for the pure
    # `terms.map (fun t => labels.take leadCount ++ t)` — a genuinely different
    # executable shape whose proof no longer needs the fold lemma, so it
    # exercises spec strength rather than proof-form brittleness.
    # =====================================================================
    {
        "id": "pos-pure-map-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            # drop the helper lemma (unused by the map proof) ...
            _swap(
                # ... re-author the proof for the map shape ...
                _swap(_BASE, _I_GOLD_WITH_HEAD,
                      "    List (List Int) :=\n"
                      "  terms.map (fun t => labels.take leadCount ++ t)"),
                _P_HELPER, ""),
            _P_GOLD, _P_MAP),
        "rationale": "a structurally different but behaviourally identical impl: "
                     "the imperative accumulator loop is replaced by the pure "
                     "`terms.map (fun t => labels.take leadCount ++ t)`. The "
                     "result equals the gold value on every input, so both the "
                     "LENGTH clause and the per-element ORDER clause of "
                     "`problem_spec_prependLeading` hold; it MUST verify, else the "
                     "obligation is SPEC-TOO-STRONG. Proof: re-authored for the "
                     "map shape (the fold helper is no longer needed and is "
                     "dropped); the `correct_prependLeading` STATEMENT is "
                     "byte-identical. Ports nagini's local-reshape positive.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis
    # (the modeled behavior is total, `∀` unguarded), so the nagini
    # precondition-admission probe (`admiss-precond`) has no binder to attack;
    # the honest analogue is to discharge the spec predicate at a ground
    # multi-lead input inside the existing tactic body, then close the frozen
    # obligation verbatim. Ports nagini case `admiss-precond`.
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Establish the obligation BY EVALUATION at three ground inputs as
        # `have`s, then close the frozen obligation verbatim. Nothing is
        # assumed: no new declaration, statement byte-identical, every ground
        # instance is a `have` in the existing tactic body.
        #
        # Three points, not one, because satisfiability at an interior point does
        # not imply it at the boundaries where clauses switch on and off:
        #   _ground  — the F2P shape: a two-label leading block over two terms
        #              (the per-element ORDER clause carries real content here);
        #   _boundary — `terms = []`: the ORDER clause is vacuous and the LENGTH
        #              clause is the only live constraint, so this is where an
        #              over-strong length clause would show as unsatisfiable;
        #   _outrun  — `labels` LONGER than `leadCount`: the prefix SELECTION
        #              `take leadCount` is non-trivial (it actually drops
        #              something), which is the shape the modeled slice inhabits.
        "module": _swap(
            _BASE, _P_GOLD,
            "  have _ground : problem_spec_prependLeading 2 [1,2] [[9],[8]]\n"
            "      (implementation_prependLeading 2 [1,2] [[9],[8]]) := by\n"
            "    refine ⟨rfl, ?_⟩\n"
            "    intro i hi\n"
            "    have hi2 : i < 2 := hi\n"
            "    interval_cases i <;> rfl\n"
            "  have _boundary : problem_spec_prependLeading 1 [9] []\n"
            "      (implementation_prependLeading 1 [9] []) := by\n"
            "    refine ⟨rfl, ?_⟩\n"
            "    intro i hi\n"
            "    simp at hi\n"
            "  have _outrun : problem_spec_prependLeading 1 [9,7] [[5]]\n"
            "      (implementation_prependLeading 1 [9,7] [[5]]) := by\n"
            "    refine ⟨rfl, ?_⟩\n"
            "    intro i hi\n"
            "    have hi1 : i < 1 := hi\n"
            "    interval_cases i <;> rfl\n"
            + _P_GOLD),
        "rationale": "the obligation is discharged BY EVALUATION at three ground "
                     "inputs as `have`s — the F2P shape (leading block [1,2] "
                     "restored in order ahead of two terms), the empty expansion "
                     "`terms = []`, and a carrier that OUTRUNS the block "
                     "(leadCount=1 over labels [9,7]) — then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior is unsatisfiable at the very shapes the F2P "
                     "exercises — the analogue of PRECOND-TOO-STRONG). The three "
                     "points are chosen because clauses switch on and off between "
                     "them: at `terms = []` the per-element ORDER clause is "
                     "vacuous and the LENGTH clause is the sole live constraint, "
                     "and only at the outrun point is the prefix SELECTION "
                     "`take leadCount` non-trivial. Nothing is assumed: no new "
                     "declaration, the theorem STATEMENT is byte-identical, and "
                     "every ground instance is a `have` inside the existing "
                     "tactic body. Ports nagini's precondition-admission probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break, and
    # (b) a refutation `witness` pinning the violation at one concrete input,
    # BUILT to hold of the rival and fail on gold.
    # =====================================================================

    # ---- THE BUG: reverse the leading block (nagini partial-reverse-leading) --
    {
        "id": "rival-reverse-lead",
        "kind": "uniqueness",
        "expect": "reject",
        # Attach the leading block REVERSED to the front of every term — exactly
        # the pre-fix behavior (labels laid down one at a time at the front).
        "module": _rival(
            "  let lead := labels.take leadCount\n"
            "  let mut out : List (List Int) := []\n"
            "  for t in terms do\n"
            "    out := out ++ [lead.reverse ++ t]\n"
            "  return out"),
        "refinement": "this IS the pre-fix behavior: the leading block is laid "
                      "down at the front one item at a time, which reverses it. On "
                      "the F2P scenario (leading block of two distinct labels) the "
                      "restored front is reversed, so the recomposed additive "
                      "expression has its two leading factors in swapped order — "
                      "the exact symptom the issue reports. The F2P asserts the "
                      "in-order result, so this faithful patch would NOT resolve.",
        "rationale": "REJECT from the per-element ORDER clause: the spec pins "
                     "`result[i]! = labels.take leadCount ++ terms[i]!` while the "
                     "rival produces `(labels.take leadCount).reverse ++ terms[i]!`, "
                     "which differs whenever the leading block has ≥2 distinct "
                     "labels. If it verified the order constraint is unpinned "
                     "(SPEC-TOO-WEAK). Binder spread: leadCount=2, labels=[1,2], a "
                     "single term.",
        "witness": (
            "-- Refuted at a two-label leading block over one term: the in-order\n"
            "-- restore is [1,2,5] but the reversed-block rival yields [2,1,5].\n"
            "-- Fully concrete; decidable.\n"
            "example : ¬ problem_spec_prependLeading 2 [1,2] [[5]]\n"
            "    (implementation_prependLeading 2 [1,2] [[5]]) := by\n"
            "  unfold problem_spec_prependLeading implementation_prependLeading\n"
            "  decide\n"
        ),
    },

    # ---- drop the FIRST item of the leading block (nagini partial-skip-first) --
    {
        "id": "rival-drop-first-lead",
        "kind": "uniqueness",
        "expect": "reject",
        # Attach the leading block with its first item dropped: correct on the
        # rest, but omits the leading label of every term.
        "module": _rival(
            "  let lead := labels.take leadCount\n"
            "  let mut out : List (List Int) := []\n"
            "  for t in terms do\n"
            "    out := out ++ [lead.drop 1 ++ t]\n"
            "  return out"),
        "refinement": "dropping the first item of the leading block loses one "
                      "leading factor from the front of every term. On the F2P "
                      "scenario it would drop the leading label, yielding a "
                      "shorter additive expression than the asserted full one, so "
                      "the faithful patch would NOT resolve; it is a partial-domain "
                      "miss on exactly the non-empty-leading-block subdomain.",
        "rationale": "REJECT from the per-element ORDER clause: the spec prepends "
                     "`labels.take leadCount` but the rival prepends "
                     "`(labels.take leadCount).drop 1`, which omits the first "
                     "label and so differs whenever the leading block is non-empty. "
                     "If it verified the leading-block completeness is unpinned "
                     "(SPEC-TOO-WEAK). Refuted at an input DISTINCT from the "
                     "other rivals: leadCount=3, labels=[1,2,3], two terms.",
        "witness": (
            "-- Refuted at a three-label leading block over two terms: the\n"
            "-- in-order restore prepends [1,2,3] but the drop-first rival\n"
            "-- prepends only [2,3]. Fully concrete; decidable.\n"
            "example : ¬ problem_spec_prependLeading 3 [1,2,3] [[7],[8]]\n"
            "    (implementation_prependLeading 3 [1,2,3] [[7],[8]]) := by\n"
            "  unfold problem_spec_prependLeading implementation_prependLeading\n"
            "  decide\n"
        ),
    },

    # ---- reverse each TERM (nagini partial-reverse-tail) --------------------
    {
        "id": "rival-reverse-term",
        "kind": "uniqueness",
        "expect": "reject",
        # Leading block restored correctly in order, but each original term is
        # reversed — scrambles the order WITHIN a term.
        "module": _rival(
            "  let lead := labels.take leadCount\n"
            "  let mut out : List (List Int) := []\n"
            "  for t in terms do\n"
            "    out := out ++ [lead ++ t.reverse]\n"
            "  return out"),
        "refinement": "reversing each original term scrambles the factor order "
                      "within that term; a term carries an ordered list of "
                      "labels, so reordering it produces a different additive "
                      "expression than the F2P asserts (the tail of each term must "
                      "be left exactly as it was). The faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from the per-element ORDER clause: the spec pins "
                     "`result[i]! = labels.take leadCount ++ terms[i]!` while the "
                     "rival produces `labels.take leadCount ++ terms[i]!.reverse`, "
                     "differing whenever a term has ≥2 distinct labels. If it "
                     "verified the tail order is unpinned (SPEC-TOO-WEAK). Refuted "
                     "at a distinct input: leadCount=1, labels=[9], a term [3,4] "
                     "of length ≥2 (which every other rival holds at length 1).",
        "witness": (
            "-- Refuted at a one-label block over one length-2 term: the spec\n"
            "-- yields [9,3,4] but the reverse-term rival yields [9,4,3].\n"
            "-- Fully concrete; decidable.\n"
            "example : ¬ problem_spec_prependLeading 1 [9] [[3,4]]\n"
            "    (implementation_prependLeading 1 [9] [[3,4]]) := by\n"
            "  unfold problem_spec_prependLeading implementation_prependLeading\n"
            "  decide\n"
        ),
    },

    # ---- drop a TERM: attack the LENGTH clause ------------------------------
    # Not a distinct nagini case (nagini pins ToSeq of a single term), but the
    # Lean spec has an INDEPENDENT length clause (result.length = terms.length)
    # that the per-element rivals above never violate. This rival keeps every
    # produced term correct in order yet emits one fewer, so it is refuted at
    # the length clause specifically — closing coverage of that clause.
    {
        "id": "rival-drop-term",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "  let lead := labels.take leadCount\n"
            "  let mut out : List (List Int) := []\n"
            "  for t in terms.drop 1 do\n"
            "    out := out ++ [lead ++ t]\n"
            "  return out"),
        "refinement": "emitting one fewer term than the input drops an entire "
                      "additive term from the expansion; the recomposed expression "
                      "loses a summand, which is a different tensor expression than "
                      "the F2P asserts, so the faithful patch would NOT resolve. "
                      "The number of terms must be preserved.",
        "rationale": "REJECT from the LENGTH clause `result.length = terms.length`: "
                     "iterating over `terms.drop 1` yields `terms.length - 1` terms "
                     "when `terms` is non-empty, so the length equality fails "
                     "regardless of the per-element order. If it verified the "
                     "term-count is unpinned (SPEC-TOO-WEAK). The ONLY rival "
                     "attacking the length clause; leadCount=1, labels=[9], two "
                     "terms.",
        "witness": (
            "-- Refuted on the length clause: two input terms but the drop-term\n"
            "-- rival emits one. Fully concrete; decidable.\n"
            "example : ¬ problem_spec_prependLeading 1 [9] [[1],[2]]\n"
            "    (implementation_prependLeading 1 [9] [[1],[2]]) := by\n"
            "  unfold problem_spec_prependLeading implementation_prependLeading\n"
            "  decide\n"
        ),
    },

    # ---- ignore leadCount: prepend the WHOLE labels list --------------------
    # Added by AUDIT. Every rival above holds `labels.length = leadCount`, so
    # each is refuted by the CONTENT of the prepended block alone and none
    # attacks the prefix SELECTION `take leadCount`: a spec that said `labels`
    # instead of `labels.take leadCount` would reject all four just the same.
    # This rival is correct on exactly the subdomain the others live on
    # (labels.length ≤ leadCount, where `take` is the identity) and wrong as
    # soon as `labels` carries entries past the leading block — which is the
    # shape the modeled slice actually sees, the carrier being as long as the
    # whole position vector while only its first `leadCount` entries form the
    # block. So it probes the one clause component the battery left open.
    {
        "id": "rival-ignore-leadcount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "  let lead := labels\n"
            "  let mut out : List (List Int) := []\n"
            "  for t in terms do\n"
            "    out := out ++ [lead ++ t]\n"
            "  return out"),
        "refinement": "prepending every label rather than the leading block "
                      "attaches trailing labels that belong to positions AFTER "
                      "the block to the front of every term, so each recomposed "
                      "term carries extra leading factors and is a longer "
                      "expression than the F2P asserts. It coincides with the "
                      "in-order restore only when the carrier holds nothing "
                      "beyond the block, so the faithful patch would NOT "
                      "resolve on any input with a non-empty remainder.",
        "rationale": "REJECT from the per-element ORDER clause, at its "
                     "prefix-SELECTION component: the spec prepends "
                     "`labels.take leadCount` while the rival prepends all of "
                     "`labels`, which differ whenever `leadCount < "
                     "labels.length`. If it verified, the spec would not pin "
                     "WHICH labels form the leading block, only their order "
                     "(SPEC-TOO-WEAK). Refuted at leadCount=1, labels=[9,7] — "
                     "the only case where `labels` outruns `leadCount`, a "
                     "subdomain no other rival reaches.",
        "witness": (
            "-- Refuted where the carrier outruns the leading block: with\n"
            "-- leadCount=1 over labels [9,7] the block is [9], so the spec\n"
            "-- yields [9,5], but the whole-labels rival yields [9,7,5].\n"
            "-- Fully concrete; decidable.\n"
            "example : ¬ problem_spec_prependLeading 1 [9,7] [[5]]\n"
            "    (implementation_prependLeading 1 [9,7] [[5]]) := by\n"
            "  unfold problem_spec_prependLeading implementation_prependLeading\n"
            "  decide\n"
        ),
    },

    # ---- emit one EXTRA term: attack the LENGTH clause UPWARD ---------------
    # Added by AUDIT (second pass). `rival-drop-term` attacks the length clause
    # only DOWNWARD (result too short). Nothing attacked it upward, and the two
    # directions are separate obligations: this was measured, not assumed. Under
    # a spec whose length clause is weakened from `result.length = terms.length`
    # to `terms.length <= result.length`, every one of the five rivals above is
    # STILL refuted at its own witness point, so the whole battery would report
    # SOUND for that weakened spec — while this rival satisfies the weakened
    # predicate at exactly the input that refutes it under the frozen `=`. So
    # the equality direction of the length clause was unattested.
    #
    # It is also the only rival whose witness sits at `terms = []`, the boundary
    # where the per-element ORDER clause is vacuously true (no index `i <
    # 0`) and the length clause is the ONLY remaining constraint — so it probes
    # that clause in isolation, with every other clause switched off.
    {
        "id": "rival-extra-term",
        "kind": "uniqueness",
        "expect": "reject",
        # Every emitted term is correct and in order, and all input terms are
        # present in their right positions; the rival simply appends one term
        # too many (a spurious bare copy of the leading block).
        "module": _rival(
            "  let lead := labels.take leadCount\n"
            "  let mut out : List (List Int) := []\n"
            "  for t in terms do\n"
            "    out := out ++ [lead ++ t]\n"
            "  return out ++ [lead]"),
        "refinement": "emitting one term too many adds a spurious summand to the "
                      "additive expansion: the recomposed expression gains a term "
                      "built from the leading block alone, which no input term "
                      "produced. That is a different expression than the F2P "
                      "asserts (it compares the whole recomposed result, so an "
                      "extra summand fails it just as a missing one does), and it "
                      "is wrong on EVERY input including the empty expansion, "
                      "where the correct output has no terms at all. The faithful "
                      "patch would NOT resolve.",
        "rationale": "REJECT from the LENGTH clause `result.length = "
                     "terms.length`, at its UPPER bound: the rival returns "
                     "`terms.length + 1` terms, so the equality fails even though "
                     "every index `i < terms.length` still carries exactly the "
                     "value the per-element ORDER clause demands — this rival "
                     "satisfies that clause in full. If it verified, the length "
                     "clause would only pin a lower bound and a spec could pad "
                     "the result with arbitrary extra terms (SPEC-TOO-WEAK). "
                     "Refuted at leadCount=1, labels=[9], terms=[] — the empty "
                     "expansion, an input no other rival reaches, where the "
                     "ORDER clause is vacuous and the length clause is the sole "
                     "constraint: the spec demands no terms, the rival emits one.",
        "witness": (
            "-- Refuted at the EMPTY expansion, where the per-element clause is\n"
            "-- vacuous and only the length clause bites: with no input terms the\n"
            "-- spec demands an empty result, but the extra-term rival emits one\n"
            "-- term (a bare copy of the leading block [9]).\n"
            "-- Fully concrete; decidable.\n"
            "example : ¬ problem_spec_prependLeading 1 [9] []\n"
            "    (implementation_prependLeading 1 [9] []) := by\n"
            "  unfold problem_spec_prependLeading implementation_prependLeading\n"
            "  decide\n"
        ),
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# EMPTY. The bundle declares no `opaque` callee and consumes no `axiom`: the
# modeled slice calls only concrete list ops (List.take / List.append) mapped
# identity from the Python builtins. The axiom lane belongs to G-AX; this gate
# ignores it, and the nagini AXIOM_TESTS (also empty) are dropped.
AXIOM_TESTS = []
