"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13328 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a FULL
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the single
``theorem correct_prepareInput`` STATEMENT stays byte-identical). An
``expect="verify"`` case passes iff the variant is in scope AND the file
elaborates with the obligation genuinely closed (no ``sorry``/``admit``/
``native_decide``, no new ``axiom``/``theorem``/``lemma``); an
``expect="reject"`` case passes iff the variant is in scope AND does NOT verify
AND its refutation ``witness`` holds of the rival while FAILING on the frozen
solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini sibling
models a much WIDER surface: a multi-step routine over a mutable row collection,
whose contract is carried by two body-less capability tokens (an evidence token
for "the array really has this element representation" and one for "the signed
arithmetic step actually ran, on exactly these rows"). Eight of its TWELVE spec
cases attack that token/effect machinery or its permission discipline. This Lean
bundle models only the purely functional CORE that the tokens were built to
protect — the element-type normalization itself, a total function from the input
array's original element type to its normalized one — so the token cases have no
counterpart here and are recorded as omissions below rather than fabricated. What
DOES port is the reasoning about the normalization decision, and that is where
this battery's four rivals live. Case-count parity with nagini is NOT the target;
coverage of the surface this bundle models is.

DEFENDED SURFACE (one obligation, two independent top-level clauses).
``problem_spec_prepareInput orig result`` pins EXACTLY:

  * (C1 preserve / frame) ``orig ∈ acceptedKinds → result = orig`` — an input
    whose element type is already one of the accepted floating types is left
    UNCHANGED. This is the frame half: the normalization is not licensed to
    rewrite an input it does not need to touch.
  * (C2 convert)          ``orig ∉ acceptedKinds → result = defaultKind`` — any
    other element type, INCLUDING a boolean storage kind, becomes the default
    double-precision floating type. This is the load-bearing half: it is what
    makes subsequent signed arithmetic well defined for a boolean input.

Both clauses are GROUNDED in the input binder — each arm is an equation between
``result`` and a term built from ``orig`` and the accepted set — so there is no
opaque answer key an implementation could echo without doing the work. There is
no opaque callee anywhere in the carrier, so every refutation here is stated at a
CONCRETE literal input and closed by ``decide``; conditioning on the carrier is
not needed.

BINDER STRUCTURE. The spec predicate has exactly ONE input binder, ``orig``
(the input array's original element type, an ``NpKind``), and the whole modeled
behavior is a case analysis on it. So the coverage question is entirely "do the
rivals move ``orig`` across the interesting cases", and they do: the four reject
witnesses probe FOUR DISTINCT points — ``NpKind.bool`` (the reported input, the
non-accepted kind the sole F2P exercises), ``NpKind.int64`` (a second
non-accepted numeric kind), ``NpKind.object`` (the one non-accepted kind the
pre-patch behavior DID convert, which is what separates the two "no conversion"
rivals from each other), and ``NpKind.float32`` (an accepted kind — the only
place C1 can be violated without also violating C2). ``pts=4`` on a one-binder
spec whose domain has five constructors, covering both clauses and both sides of
the accepted/non-accepted split.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's
    ``frame-mutation-append`` writes to an input held at half permission. Lean is
    referentially transparent: ``orig`` is an immutable value of an inductive
    type, there is no aliasing, no permission, and no read-only cell to
    overwrite. No substitute probe is fabricated. Note that this bundle's spec
    still carries a frame OBLIGATION in the value world — C1, "an already-accepted
    input is returned unchanged" — and that clause IS attacked (see
    ``weak-inverted-guard``); it is the permission machinery, not the frame idea,
    that is vacuous here.

  * CAPABILITY TOKEN / CONTROL-FLOW EFFECT — NO COUNTERPART (carrier narrowing).
    Six nagini rivals (``cfe-inline-no-token``, ``forge-token-const-rep``,
    ``fabricated-const-floating-tag``, ``stale-tag-after-no-floating``,
    ``launder-token-dummy-rows``, ``launder-token-copied-rows``) all produce the
    RIGHT value and are rejected only because the effect-evidence token is
    missing, fabricated, mislabelled, or earned on a stand-in collection. That
    entire discriminator needs a carrier with an effect to witness and a
    reference identity to bind. Here the modeled function is a total
    ``NpKind → NpKind`` with no effect and no collection argument, so "produced
    the right value without doing the work" is not a distinguishable state and
    those rivals collapse onto impls that are simply correct. They are OMITTED,
    not re-expressed with an invented substitute.

  * DIVERGENCE / NON-TERMINATION — EXPRESSIBLE but UNWITNESSABLE; recorded as a
    known hole, NOT as vacuity. The nagini sibling carries no
    ``diverge-*``/``nonterm-*``/``weak-diverge`` case, so there is nothing to
    port. The stronger claim that the class cannot be written here at all is
    FALSE and was corrected by audit measurement: replacing the frozen ``def``
    with ``partial def implementation_prepareInput (orig : NpKind) : NpKind :=
    implementation_prepareInput orig`` is a self-recursive impl with no
    decreasing measure, it lies wholly inside ``-- impl-start``/``-- impl-end``,
    and ``variant_scope.variant_problems`` returns ``[]`` for it — so it IS an
    in-scope variant on this carrier. What blocks SHIPPING it is the witness
    requirement, not expressibility, and both directions were built:

      - the rival module is rejected (exit 1), but a ``partial def`` has no
        equation lemmas, so the refutation cannot reduce: the ground witness of
        the shape used by every case below fails against the RIVAL too (exit 1,
        ``Tactic `unfold` failed to unfold `implementation_prepareInput```),
        which the gate records as ``witness-unproven`` — an inconclusive
        outcome, not a pass;
      - a hypothesis-CONDITIONED witness (``example (h :
        implementation_prepareInput NpKind.bool ≠ defaultKind) : ¬ ...``) does
        elaborate against the rival (exit 0), but it ALSO elaborates against the
        frozen solution (exit 0) — gold sends the boolean kind to
        ``defaultKind``, so ``h`` is false there and the conclusion is vacuous.
        The gate records ``witness-vacuous``; equivalently its consistency probe
        discharges ``False`` from ``h`` on gold.

    So no witness discriminates a diverging impl on this carrier, and the class
    is unshippable for that measured reason. It is NOT a spec hole: the frozen
    spec does not admit the rival (the variant fails to verify). Note also that
    this bundle's ``Solution.lean`` carries no
    ``set_option loom.semantics.termination`` line at all — that option, and the
    ``partial``-semantics spec hole documented in ``the corpus-wide termination-semantics finding``,
    are velvet phenomena and neither governs this lean cell.

  * VALUE / PARTIAL-DOMAIN — APPLIES, and is the whole battery. Four rivals:
    the pre-patch decision (convert only the one kind the generic request
    converted); the tightest near-miss (correct everywhere EXCEPT the boolean
    kind — exactly the reported input); no normalization at all; and a rival that
    inverts the guard, so an already-accepted input is rewritten while
    non-accepted ones are left alone.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. (Measured on these very
rivals: three of the four break the frozen proof with ``simp made no progress``
and the fourth with a ``rfl`` type mismatch, which is what a merely-RESHAPED
correct impl would also produce.) Every reject case therefore carries a Lean
snippet that states the spec predicate directly at one concrete element type and
closes by ``decide``. Each witness binds NOTHING in its head — every input is a
ground ``NpKind`` constructor — so there are no hypotheses whose joint
satisfiability could be in question. All four were checked with two real
``lake env lean`` builds each: they ELABORATE against their rival and FAIL on the
frozen solution (``decide`` reports that gold satisfies the spec at that point),
so they discriminate rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-does-not-imply-resolve
break). Every rival's faithful real counterpart leaves a boolean input's element
type unconverted on at least the boolean sub-domain, so the signed arithmetic the
routine performs downstream is still undefined for it and the sole F2P — the
regression test that fits the model on boolean predictors — still raises. Each
case's ``refinement`` states this for its own shape.

A NOTE ON TWO RIVALS DELIBERATELY NOT SHIPPED. Clause C2 pins the conversion
TARGET (``defaultKind``) and clause C1 pins preservation of ``float32``. Two
tempting rivals move exactly those and nothing else: convert non-accepted kinds
to single- rather than double-precision, and convert EVERY input (including an
accepted single-precision one) to the double-precision default. Both are
correctly REJECTED by this spec — it faithfully models the frozen behavior — but
neither can carry an honest ``refinement``: their faithful real patches both
yield a floating element type for a boolean input, so the F2P would pass and the
harness would resolve. Shipping them would put a non-resolution claim in the
manifest that the F2P set does not support, so they are omitted on purpose; see
``assessment``.

AXIOM lane: EMPTY. This bundle declares no ``opaque`` callee and consumes no
``axiom`` (the normalization is modeled deeply as an A-reference), and the nagini
``AXIOM_TESTS`` belong to G-AX, which this gate ignores. Dropped.

SPEC STRENGTH IS EXACT (audit-added, machine-checked). The carrier is small
enough that the usual sampling arguments for SPEC-TOO-WEAK / SPEC-TOO-STRONG can
be replaced by a proof over the WHOLE function space, and they were. With
``refImpl o := if o ∈ acceptedKinds then o else defaultKind`` (pointwise equal to
the frozen impl — checked by ``cases o <;> rfl``), both directions elaborate
(one file, exit 0):

  * ``spec_pins_uniquely (f : NpKind → NpKind) (o : NpKind)
    (hf : problem_spec_prepareInput o (f o)) : f o = refImpl o`` — satisfying the
    spec at an input FORCES the frozen function's value there. So NO wrong impl,
    of any shape, can satisfy the spec anywhere it differs from gold: there is no
    SPEC-TOO-WEAK hole to find, and the four rivals below are not a sample of a
    larger unexplored space but instances of a closed result.
  * ``agree_implies_spec (f : NpKind → NpKind) (o : NpKind)
    (hf : f o = refImpl o) : problem_spec_prepareInput o (f o)`` — agreeing with
    gold SUFFICES. So no faithful correct reshape can be rejected: there is no
    SPEC-TOO-STRONG hole either.

Together these say the spec pins exactly the graph of the modeled function, no
more and no less. Six further wrong impls beyond the four shipped (swap the two
accepted kinds; send everything to the default; retarget conversion to
single-precision; violate C1 at the double-precision point only; a constant; a
boolean pass-through) were each built under BOTH the frozen tactic body and a
generic ``cases orig <;> decide`` re-proof: all twelve builds exit 1, every one
with ``decide`` refuting the obligation semantically rather than a tactic
mismatch. Four further correct reshapes (explicit disjunction guard; the
``isFloating`` Bool form negated; the non-accepted kinds enumerated; a
non-monadic pure ``def``) all verify, exit 0.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13328"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; checked at load) ----
# The frozen implementation body: the whole `do` block inside
# `-- impl-start`/`-- impl-end`. Every value-level reshape swaps exactly this.
_I_BODY = """  let mut dt := orig
  if orig ∈ acceptedKinds then
    dt := orig
  else
    dt := defaultKind
  return dt"""

# The frozen implementation DECLARATION plus its body — used by the positive
# control that abandons the imperative shape entirely for a pattern match. Lies
# wholly inside `-- impl-start`/`-- impl-end`.
_I_DECL = (
    "def implementation_prepareInput (orig : NpKind) : NpKind := Id.run do\n"
    + _I_BODY)

# The frozen tactic body, wholly inside `-- proof-start`/`-- proof-end`. Swapped
# only by cases that legitimately re-prove for a reshaped implementation, or that
# prepend a ground instance; the `theorem correct_prepareInput` STATEMENT above
# it is never touched.
_P_BODY = """  intro orig
  unfold problem_spec_prepareInput implementation_prepareInput
  simp only [Id.run]
  by_cases h : orig ∈ acceptedKinds
  · simp only [if_pos h]
    exact ⟨fun _ => rfl, fun hc => absurd h hc⟩
  · simp only [if_neg h]
    exact ⟨fun hc => absurd hc h, fun _ => rfl⟩"""

# A re-proof that works for any variant whose implementation reduces by case
# analysis on the (finite, DecidableEq) input type. No new declaration, no
# assumption token; the obligation statement is untouched.
_P_CASES = """  intro orig
  unfold problem_spec_prepareInput implementation_prepareInput
  cases orig <;> decide"""


def _variant(*pairs):
    src = _BASE
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


def _witness(kind):
    """Refute the spec at one concrete element type.

    States the frozen predicate directly at ``NpKind.<kind>`` applied to the
    variant's own implementation and closes by ``decide`` — the carrier is a
    five-constructor inductive with ``DecidableEq``, so the whole proposition
    decides. Binds nothing, so there are no hypotheses to be inconsistent.
    """
    return (
        f"example : ¬ problem_spec_prepareInput NpKind.{kind}\n"
        f"    (implementation_prepareInput NpKind.{kind}) := by\n"
        "  unfold problem_spec_prepareInput implementation_prepareInput\n"
        "  decide\n")


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else the spec is SPEC-TOO-STRONG.
    # Each keeps the `theorem correct_prepareInput` statement byte-identical
    # and re-proves honestly inside the proof region.
    # =====================================================================
    {
        "id": "pos-default-first",
        "kind": "soundness",
        "expect": "verify",
        # Mirror image of the frozen shape: START from the conversion target and
        # override only when the input's element type is already accepted, using
        # the `pure`-region membership helper instead of the membership test
        # directly. Same function, opposite branch polarity, one-armed `if`.
        # Re-proved by case analysis on the finite input type. (Verified: real
        # build, exit 0.)
        "module": _variant(
            (_I_BODY,
             "  let mut dt := defaultKind\n"
             "  if isFloating orig then\n"
             "    dt := orig\n"
             "  return dt"),
            (_P_BODY, _P_CASES),
        ),
        "rationale": "a correct, structurally-different implementation must "
                     "verify or the spec is SPEC-TOO-STRONG. This one inverts the "
                     "branch polarity (initialize to the conversion target, "
                     "override only for an already-accepted element type) and "
                     "routes the test through the spec-view membership helper, so "
                     "it is a different control flow computing the same function: "
                     "C1 holds on the override arm, C2 on the fall-through. "
                     "Re-proved by case analysis on the finite element-type "
                     "carrier — statement byte-identical, no new axiom/lemma, no "
                     "assumption token. Ports the nagini pos-control-branch "
                     "positive (there: an explicit branch reshape around the same "
                     "normalization request).",
    },
    {
        "id": "pos-explicit-match",
        "kind": "soundness",
        "expect": "verify",
        # Abandons the imperative shape entirely: a total pattern match that
        # enumerates the accepted element types and sends everything else to the
        # default. No `Id.run do`, no `let mut`, no membership test at all — the
        # accepted set is spelled out constructor by constructor. Maximally
        # different syntactic form for the same function. (Verified: real build,
        # exit 0.)
        "module": _variant(
            (_I_DECL,
             "def implementation_prepareInput (orig : NpKind) : NpKind :=\n"
             "  match orig with\n"
             "  | NpKind.float64 => NpKind.float64\n"
             "  | NpKind.float32 => NpKind.float32\n"
             "  | _ => defaultKind"),
            (_P_BODY, _P_CASES),
        ),
        "rationale": "a second, more aggressive correct reshape: the imperative "
                     "block is replaced by a total pattern match that enumerates "
                     "the accepted element types explicitly and defaults the rest, "
                     "with no membership test and no mutable local. It agrees with "
                     "the frozen function at every one of the five element types, "
                     "so both C1 and C2 hold; it must verify, else SPEC-TOO-STRONG "
                     "(a spec that accepted only the frozen SYNTAX would be "
                     "attesting to the implementation, not the behavior). Re-proved "
                     "by case analysis; statement byte-identical, no new "
                     "axiom/lemma.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at the very input the sole
    # F2P supplies. The frozen theorem carries NO precondition hypothesis (the
    # element-type carrier is closed, so every constructor is in domain), so
    # the nagini precondition-admission case re-expresses as: discharge the
    # postcondition by evaluation at the boolean storage kind as a ground
    # `have`, then close the frozen obligation verbatim. Nothing is assumed.
    # =====================================================================
    {
        "id": "admiss-bool-input",
        "kind": "admissibility",
        "expect": "verify",
        # Gold implementation untouched; the proof region prepends a ground
        # instance of the spec at the boolean element type before the frozen
        # tactic body (kept verbatim). A `have` inside a tactic block is not a
        # top-level declaration, so no new theorem/lemma is introduced.
        # (Verified: real build, exit 0.)
        "module": _variant(
            (_P_BODY,
             "  have _f2p : problem_spec_prepareInput NpKind.bool\n"
             "      (implementation_prepareInput NpKind.bool) := by\n"
             "    unfold problem_spec_prepareInput implementation_prepareInput\n"
             "    decide\n"
             + _P_BODY),
        ),
        "rationale": "the modeled behavior must be satisfiable at exactly the "
                     "input the sole F2P supplies — an array stored with the "
                     "boolean element kind. This case discharges "
                     "problem_spec_prepareInput at NpKind.bool by evaluation as a "
                     "ground `have` (so C2's conversion arm is shown to be "
                     "achievable there, not merely required), then closes the "
                     "frozen obligation with its own tactic body verbatim. If it "
                     "failed, the spec would be unsatisfiable at a normal F2P "
                     "input — the analogue of nagini's PRECOND-TOO-STRONG, which "
                     "its admiss-logical-input case guards. Statement "
                     "byte-identical, no new declaration, no assumption token.",
    },

    # =====================================================================
    # UNIQUENESS — wrong implementations of the SAME modeled behavior. Each is
    # rejected by a named clause at a named input, and each carries a witness
    # SEEN to hold of the rival and to FAIL on the frozen solution.
    # =====================================================================
    {
        "id": "weak-object-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-PATCH DECISION. Converts only the single non-accepted element
        # kind that the generic pre-fix request converted, and leaves every other
        # non-accepted kind (boolean, integer) with its original element type.
        # This is byte-for-byte the behavior of Solution_prepatch.lean's impl, so
        # it is the G-DIFF discriminator restated as a G-PBT rival.
        "module": _variant(
            (_I_BODY,
             "  let mut dt := orig\n"
             "  if orig = NpKind.object then\n"
             "    dt := defaultKind\n"
             "  return dt"),
        ),
        "rationale": "violates C2 (orig ∉ acceptedKinds → result = defaultKind) on "
                     "every non-accepted element kind except the one it special-"
                     "cases: at orig = NpKind.int64 it returns int64 where the "
                     "clause demands defaultKind. The witness refutes it there; it "
                     "is equally refutable at NpKind.bool, but that point is "
                     "carried by the tighter near-miss below, so this witness "
                     "probes int64 instead and the two cases discriminate distinct "
                     "inputs. C1 is untouched (accepted kinds fall through "
                     "unchanged), which is what makes this a partial-domain rival "
                     "rather than a blunt one.",
        "refinement": "this IS the pre-fix behavior: a generic normalization "
                      "request that converts only the untyped-object storage kind "
                      "and performs no conversion for any other non-accepted kind. "
                      "A boolean input therefore keeps its boolean element type, "
                      "the downstream signed arithmetic on it is undefined, and the "
                      "sole F2P — the regression test that fits on boolean "
                      "predictors — still raises. It does NOT resolve, so a "
                      "verifying version of this rival would be a genuine "
                      "verify-does-not-imply-resolve break.",
        "witness": _witness("int64"),
    },
    {
        "id": "weak-skip-bool",
        "kind": "uniqueness",
        "expect": "reject",
        # THE TIGHTEST NEAR-MISS. Correct on FOUR of the five element types:
        # accepted kinds are preserved, integer and object kinds are converted —
        # only the boolean kind is exempted from conversion. Agrees with the
        # frozen function everywhere except the single input the reported failure
        # uses, so it is the rival a battery probing only "some non-float input"
        # would miss.
        "module": _variant(
            (_I_BODY,
             "  let mut dt := orig\n"
             "  if orig ∈ acceptedKinds ∨ orig = NpKind.bool then\n"
             "    dt := orig\n"
             "  else\n"
             "    dt := defaultKind\n"
             "  return dt"),
        ),
        "rationale": "violates C2 at exactly ONE point: orig = NpKind.bool, where "
                     "it returns bool and the clause demands defaultKind. Every "
                     "other element type is handled correctly (C1 holds, and C2 "
                     "holds for the integer and object kinds), so this is the "
                     "near-miss that agrees with gold over the largest part of the "
                     "domain — it gets its own witness at the boolean kind, the one "
                     "input that distinguishes it, rather than sharing the "
                     "pre-patch rival's. Ports nagini's partial-skip-logical "
                     "(correct except on the boolean sub-domain).",
        "refinement": "the faithful counterpart normalizes the element type for "
                      "every input EXCEPT a boolean-stored one, which it passes "
                      "through unconverted. That is precisely the sub-domain the "
                      "sole F2P exercises: the boolean array reaches the numerical "
                      "kernel with its boolean element type and the signed "
                      "arithmetic there is undefined, so the test still raises and "
                      "the instance does not resolve — while every other input "
                      "behaves exactly like gold, which is what makes it dangerous.",
        "witness": _witness("bool"),
    },
    {
        "id": "weak-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # NO NORMALIZATION AT ALL: hand back the input's own element type
        # unconditionally. Satisfies C1 trivially and violates C2 at every
        # non-accepted kind — including the untyped-object kind, which the
        # pre-patch rival above DOES convert, so this rival and that one are
        # separated by their witness points.
        "module": _variant(
            (_I_BODY,
             "  let mut dt := orig\n"
             "  dt := orig\n"
             "  return dt"),
        ),
        "rationale": "violates C2 at every non-accepted element type; the witness "
                     "refutes it at orig = NpKind.object, where it returns object "
                     "and the clause demands defaultKind. That point is chosen "
                     "deliberately: object is the one non-accepted kind the "
                     "pre-patch rival converts correctly, so refuting HERE at "
                     "object and THERE at int64 shows the two rivals are distinct "
                     "wrongs rather than one wrong probed twice. C1 is satisfied "
                     "(an accepted kind is returned unchanged), so the rejection is "
                     "attributable to C2 alone. Ports nagini's identity-unnegated "
                     "cheap supporting near-miss (there: return the rows without "
                     "the arithmetic step).",
        "refinement": "the faithful counterpart performs no element-type "
                      "normalization whatsoever — the input array's storage kind "
                      "reaches the numerical kernel untouched. A boolean input then "
                      "hits undefined signed arithmetic exactly as before the fix, "
                      "so the sole F2P still raises and the instance does not "
                      "resolve.",
        "witness": _witness("object"),
    },
    {
        "id": "weak-inverted-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # ATTACKS THE FRAME CLAUSE (C1). The guard is inverted: an input whose
        # element type is ALREADY accepted gets rewritten to the default, while a
        # non-accepted one is passed through unconverted. No nagini rival targets
        # this clause — nagini's value obligation is a single arithmetic fold with
        # no preserve-half to attack — so this is the one case ADDED to cover a
        # load-bearing clause of the SAME modeled spec.
        "module": _variant(
            (_I_BODY,
             "  let mut dt := orig\n"
             "  if orig ∈ acceptedKinds then\n"
             "    dt := defaultKind\n"
             "  else\n"
             "    dt := orig\n"
             "  return dt"),
        ),
        "rationale": "violates C1 (orig ∈ acceptedKinds → result = orig), the frame "
                     "half: at orig = NpKind.float32 — an accepted single-precision "
                     "kind — it returns defaultKind where the clause demands "
                     "float32 unchanged. The witness refutes it at exactly that "
                     "point. C1 is isolable at EITHER accepted kind (at an accepted "
                     "input C2's hypothesis is false, so C2 is vacuous there and "
                     "only C1 can fail); float32 is the accepted point THIS rival "
                     "moves, since it happens to map float64 to defaultKind = "
                     "float64 and so agrees with gold there. The same rival also "
                     "violates C2 on the non-accepted kinds, but the witness is "
                     "placed on the C1 point because C1 is otherwise unattacked. "
                     "ADDED relative to nagini (see the module docstring): its "
                     "frame discipline lives in the permission system, which is "
                     "vacuous here, while this spec's frame content is a value "
                     "clause and is attackable.",
        "refinement": "the faithful counterpart requests the wrong side of the "
                      "decision: it rewrites the element type of inputs that are "
                      "already floating and leaves non-accepted kinds — a boolean "
                      "array among them — unconverted. The boolean sub-domain is "
                      "therefore still broken and the sole F2P still raises, so it "
                      "does not resolve. The non-resolution rests on the boolean "
                      "sub-domain ALONE: every currently-passing regression test in "
                      "this instance's P2P set feeds a double-precision input, "
                      "which this shape maps to the double-precision default and so "
                      "leaves observationally unchanged, so no claim is made about "
                      "the single-precision rewrite breaking a P2P test.",
        "witness": _witness("float32"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 12 SPEC cases (1 soundness
# positive, 1 admissibility, 10 uniqueness rivals) plus 3 AXIOM_TESTS. This
# bundle models a NARROWER surface — the purely functional element-type
# normalization, with no effect to witness and no mutable input — so seven of the
# ten rivals have no counterpart. Every sibling case is accounted for: the table
# below names all 12 sibling SPEC cases and the 3 AXIOM_TESTS, plus 2 extra rows
# for the cases ADDED here that have no sibling.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------------
#   pos-control-branch              -> pos-default-first          RE-EXPRESSED
#   (none)                          -> pos-explicit-match         ADDED positive
#   admiss-logical-input            -> admiss-bool-input          RE-EXPRESSED
#   prepatch-no-floating            -> weak-object-only           PORTED
#   partial-skip-logical            -> weak-skip-bool             PORTED
#   identity-unnegated              -> weak-identity              PORTED
#   (none)                          -> weak-inverted-guard        ADDED (C1)
#   frame-mutation-append           -> (none)   VACUOUS (referential transparency)
#   cfe-inline-no-token             -> (none)   NO COUNTERPART (no effect carrier)
#   forge-token-const-rep           -> (none)   NO COUNTERPART (no effect carrier)
#   fabricated-const-floating-tag   -> (none)   NO COUNTERPART (no effect carrier)
#   stale-tag-after-no-floating     -> (none)   NO COUNTERPART (no effect carrier)
#   launder-token-dummy-rows        -> (none)   NO COUNTERPART (no reference identity)
#   launder-token-copied-rows       -> (none)   NO COUNTERPART (no reference identity)
#   AXIOM_TESTS (3)                 -> (none)   DROPPED (G-AX's lane)
#
# RE-EXPRESSED (pos-default-first): the sibling's positive reshapes the branch
#   around the normalization REQUEST (both arms request the floating form). This
#   carrier has no request argument — the decision itself is the modeled function
#   — so the analogous reshape inverts the branch polarity: initialize to the
#   conversion target and override only for an already-accepted element type.
# RE-EXPRESSED (admiss-bool-input): the sibling asserts its numeric precondition
#   admits the boolean input tag. This bundle's obligation carries NO precondition
#   (the element-type carrier is a closed inductive, so every constructor is in
#   domain), which makes precondition admission trivially true and uninteresting.
#   The honest analogue is to show the POSTCONDITION is satisfiable at the same
#   F2P input, discharged by evaluation at the boolean kind as a ground `have`.
# ADDED (pos-explicit-match): a second positive with a much larger syntactic
#   delta (pattern match, no imperative block, accepted set enumerated), so the
#   defended half of the obligation is not carried by a single near-frozen shape.
# ADDED (weak-inverted-guard): the spec has TWO independent top-level clauses and
#   the three ported rivals all attack C2 only. C1 — "an already-accepted element
#   type is returned unchanged" — is load-bearing and was unattacked, so a rival
#   that inverts the guard is added to cover it. It is not fabricated for an
#   unmodeled behavior: it attacks a real clause of the SAME modeled spec, and its
#   faithful patch still fails the F2P.
# NO COUNTERPART (the six token rivals): all six produce the correct VALUE and are
#   rejected only for the effect-evidence token — missing, fabricated, labelled
#   with a constant instead of the genuine input, or earned on a stand-in/copied
#   collection. That discriminator requires an effect to witness and a reference
#   identity to bind to; this bundle models a total NpKind -> NpKind function with
#   neither, so each of those rivals degenerates to an implementation that is
#   simply correct. Omitted rather than substituted. This is the carrier narrowing
#   the port note describes, and it is the honest reading of the sibling's own
#   claim that "no value-level postcondition can witness" the control-flow effect.
# VACUOUS (frame-mutation-append): no mutable input, no aliasing, no permission.
#   The frame IDEA survives as clause C1 and is attacked by weak-inverted-guard.
# DIVERGENCE: the sibling carries no diverge-*/nonterm-*/weak-diverge case, so
#   there is nothing to port. The class is EXPRESSIBLE here, contrary to an
#   earlier note in this file (`partial def` self-recursion is in scope:
#   variant_problems == []), but it is UNWITNESSABLE — the ground witness shape
#   fails on the rival too (no equation lemmas for a `partial def`) and a
#   conditioned witness also holds of gold. Recorded as a known hole in the
#   witness lane, not as vacuity and not as a spec hole; see the module
#   docstring for the four exit codes.
#
# NOT SHIPPED ON PURPOSE (rivals with no honest refinement). A rival converting
# non-accepted kinds to the single- instead of double-precision default; a rival
# converting EVERY input to the double-precision default; a rival that swaps the
# two accepted kinds; and a rival that violates C1 at the DOUBLE-precision
# accepted point only (mapping float64 to float32 and otherwise behaving like
# gold). Each violates a real clause and each was CONFIRMED rejected by a real
# build, the last one together with a witness at NpKind.float64 that elaborates
# against it (exit 0) and is refuted by `decide` on the frozen solution (exit 1).
# But every one of them sends a boolean input to a floating element type, so the
# sole F2P would PASS and the harness would resolve. Their `refinement` field
# would have to assert a non-resolution the F2P set does not support, so they are
# omitted; the clause coverage they would have provided is supplied by
# weak-inverted-guard (C1) and the three C2 rivals, whose refinements are sound.
# This is a deliberate, documented coverage limit and not an oversight: the four
# SHIPPED rivals are exactly the wrong shapes that both violate a clause AND
# leave the boolean sub-domain broken, which is what a refinement may claim here.
#
# POINT SPREAD. Four reject witnesses, FOUR DISTINCT input points (pts=4) on a
# one-binder spec over a five-constructor carrier:
#   orig = NpKind.int64     weak-object-only      C2  (non-accepted, numeric)
#   orig = NpKind.bool      weak-skip-bool        C2  (the reported F2P input)
#   orig = NpKind.object    weak-identity         C2  (the kind pre-patch converts)
#   orig = NpKind.float32   weak-inverted-guard   C1  (accepted; isolates C1)
# The single input binder is therefore moved across both sides of the
# accepted/non-accepted split and across three distinct non-accepted kinds; no
# binder is held fixed anywhere.
AXIOM_TESTS = []
