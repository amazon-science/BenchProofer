"""properties.py — G-PBT falsification battery for sympy__sympy-13757 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct formExpressionTimesPolynomial`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  formExpressionTimesPolynomial
      (productValue : List Int) (factorsCombineIntoPolynomial : Bool)
      return (out : ProductResult)
    ensures out.form = (if factorsCombineIntoPolynomial
                        then ProductForm.carriedOut
                        else ProductForm.formalProduct)
    ensures factorsCombineIntoPolynomial = true → out.value = productValue

The operation forms the product of an ordinary expression (left) and a
polynomial (right) and reports the observable SHAPE of that product. Two
independent top-level clauses carry the whole obligation:

  * CLAUSE 1 (the form/flag equivalence) — the load-bearing discriminator. The
    product must be CARRIED OUT (a single evaluated value) exactly when the two
    factors combine into a single value (``factorsCombineIntoPolynomial = true``)
    and left as a FORMAL, unevaluated product otherwise. This is the modeled
    consequence the failing scenario observes: pre-fix the left-operand product
    is never carried out even when the factors combine.
  * CLAUSE 2 (value preservation) — when the product IS carried out the supplied
    combined value must survive into the result unchanged (directive 5:
    ``productValue`` is a read-only input the operation must preserve, not
    overwrite or recompute).

TWO INPUT BINDERS, both free: ``factorsCombineIntoPolynomial : Bool`` (the
combine/formal switch) and ``productValue : List Int`` (the supplied combined
value). The reject witnesses must move the boolean across BOTH truth values —
a rival that mishandled only the combine=true branch, or only the combine=false
branch, would slip past a battery that pinned the switch — and must drive
``productValue`` to a value the value-clause rival cannot echo (a non-empty list,
so a "drop the value" rival is caught).

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``formExpressionTimesPolynomialTester productValue
factorsCombineIntoPolynomial = false`` says the extracted program's result
violates the postcondition at that concrete input) and closes by ``decide``,
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. Every impl here is loop-free (a single ``if``/``let``
over the boolean and the returned record), so the extracted tester reduces to
``isTrue``/``isFalse`` under kernel computation and ``decide`` closes without
getting stuck. The concrete inputs are a small ``List Int`` literal and a boolean
literal — fully computable, no opaque term, so no conditioning is needed.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling's frame class
    exists because a by-value / read-only input may carry a fractional heap
    permission an impl could overwrite. This backend is referentially
    transparent: ``productValue`` and ``factorsCombineIntoPolynomial`` are
    immutable value parameters, this bundle declares no ``mut`` binder, and there
    is no heap or aliasing. There is no read-only input to overwrite and no
    permission system to trip, so the class is vacuous. The directive-5 concern
    it maps to here — that the supplied ``productValue`` survives unchanged — is
    instead a real VALUE clause (clause 2), and it is attacked by TWO reject
    rivals: ``reject-value-dropped`` (overwrites the supplied value outright) and
    ``reject-value-order-scrambled`` (keeps every coefficient but permutes them,
    so it is wrong only in order). No substitute permission probe is fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
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
  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the reject lane: clause 1 pins
    the form on EVERY input, so a rival that always returns one form (ignoring
    the switch) diverges at the branch it drops; clause 2 pins the carried value
    up to EQUALITY, so a rival that discards ``productValue`` diverges wherever the
    supplied value is non-empty, and a rival that merely permutes it diverges
    wherever the supplied value is not a palindrome.
  * UNGROUNDED-ORACLE ECHO — N/A. The postcondition is stated over the method's
    own inputs (the boolean switch and the free ``productValue``); the ``axioms``
    region is empty (no opaque answer key to echo). The only way to satisfy it is
    to branch on the switch and preserve the value, which the positive controls
    do honestly.

WITNESS PLACEMENT. The four reject witnesses sit at FOUR DISTINCT input points
and between them move ``factorsCombineIntoPolynomial`` across BOTH values
(``true`` for the form rival that always leaves formal and for both value rivals;
``false`` for the form rival that always carries out) and drive ``productValue``
across three shapes: a singleton the form rivals are pinned at, a DIFFERENT
singleton where the value-dropping rival's empty result is refutable, and a
non-palindromic two-element list where the order-scrambling rival is refutable
but a length/multiset-only reading of clause 2 would not be. Rivals share a
witness only when they fail there for the same reason — these four do not, so
each carries its own discriminating point.

Each reject witness point is also NECESSARY, not decorative, and this was
measured rather than argued: at ``productValue = []`` the value-dropping rival
AGREES with the frozen impl, and at the palindrome ``[1,1]`` the order-scrambling
rival does, so in each case the battery's own witness correctly FAILS to refute
that rival there (exit 1 on the rival side, audit-measured). A witness point that
could be replaced by an agreement point would be attesting to nothing.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13757"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (verbatim from Solution.lean) ----------------------

# The `let form := if … then carriedOut else formalProduct` block — the entire
# form-selection surface, lying wholly inside the impl region and unique in the
# file (both facts asserted at load by _swap). Form rivals reshape only this.
_FORM_BLOCK = (
    "    let form :=\n"
    "      if factorsCombineIntoPolynomial\n"
    "      then ProductForm.carriedOut\n"
    "      else ProductForm.formalProduct\n"
)
assert _BASE.count(_FORM_BLOCK) == 1, "form-block anchor drift — re-sync _FORM_BLOCK"

# The returned record. The value rival reshapes only the `value := …` field,
# leaving the form selection and the frozen proof script intact.
_RETURN_LINE = "    return { form := form, value := productValue }\n"
assert _BASE.count(_RETURN_LINE) == 1, "return-line anchor drift"

# The frozen proof script. Retuned ONLY by the admissibility case, which adds an
# in-region `assert` and so leaves one extra goal for the tail to clear; the
# `prove_correct` header (the obligation itself) is preserved either way, and the
# whole tactic body is elided from the consumer spec view.
_PROOF_BLOCK = "prove_correct formExpressionTimesPolynomial by\n  loom_solve\n"
assert _BASE.count(_PROOF_BLOCK) == 1, "proof-block anchor drift"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `formExpressionTimesPolynomialTester productValue factorsCombineIntoPolynomial
# ---- = false` says the extracted program's result violates the method's
# ---- postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block has been stripped. Every argument is a concrete
# ---- literal (a small `List Int`, a boolean) so `decide` reduces the loop-free
# ---- extracted program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for formExpressionTimesPolynomial\n"
            "prove_precondition_decidable_for formExpressionTimesPolynomial\n"
            "prove_postcondition_decidable_for formExpressionTimesPolynomial\n"
            "derive_tester_for formExpressionTimesPolynomial\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Guards on the NEGATION of the switch first (branch
    # reorder): logically identical to the frozen impl on every input, and the
    # frozen `loom_solve` proof still closes (verified during authoring).
    # =====================================================================
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _FORM_BLOCK,
            "    let form :=\n"
            "      if !factorsCombineIntoPolynomial\n"
            "      then ProductForm.formalProduct\n"
            "      else ProductForm.carriedOut\n"),
        "rationale": (
            "guarding on the negation of the switch first is a branch reorder that "
            "produces the same form for every value of factorsCombineIntoPolynomial, "
            "so clause 1 (out.form = if flag then carriedOut else formalProduct) "
            "still holds on the whole domain, and clause 2 is untouched (the "
            "returned value is unchanged). A correct reshape must verify, else the "
            "postcondition is SPEC-TOO-STRONG (over-pins the syntactic shape of the "
            "branch rather than the behavior)."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a second structurally-different correct
    # impl: select the form by `match` on the boolean instead of `if`. Same
    # observable behavior on both branches; the frozen proof still closes
    # (verified during authoring). A second correct shape guards against the
    # spec accidentally pinning the `if`-expression form.
    # =====================================================================
    {
        "id": "pos-control-match-on-switch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _FORM_BLOCK,
            "    let form :=\n"
            "      match factorsCombineIntoPolynomial with\n"
            "      | true => ProductForm.carriedOut\n"
            "      | false => ProductForm.formalProduct\n"),
        "rationale": (
            "selecting the form by `match` on the switch rather than `if` is "
            "observationally identical on both branches, so both clauses still "
            "hold; the frozen proof closes. Must verify (else SPEC-TOO-STRONG over "
            "the elaboration shape of the branch selector)."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is loop-free so
    # its extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================

    # --- CLAUSE 1, combine=true sub-domain: always leave the product FORMAL,
    # --- ignoring the switch. This is exactly the pre-fix bug shape (the
    # --- left-operand product is never carried out even when the factors
    # --- combine). Correct only where the factors do NOT combine; WRONG where
    # --- they do.
    {
        "id": "reject-always-formal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FORM_BLOCK,
                        "    let form := ProductForm.formalProduct\n"),
        "refinement": (
            "always leaving the product as a formal, unevaluated product — never "
            "carrying it out — is precisely the reported symptom: the left-operand "
            "product does not evaluate even when the two factors combine into a "
            "single value. On the combine=true sub-domain (the F2P scenario, where "
            "the product must become a single evaluated value) it reports a standing "
            "formal product, so the failing scenario still fails. A faithful real "
            "patch that never carried the product out would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 1 (out.form = if flag then carriedOut else "
            "formalProduct): on combine=true the spec demands carriedOut and this "
            "impl returns formalProduct. Verifying would mean clause 1 does not pin "
            "the carried-out branch (partial-domain SPEC-TOO-WEAK). Refuted at "
            "factorsCombineIntoPolynomial=true, productValue=[1] (the combine branch)."
        ),
        "witness": _tester(
            "example : formExpressionTimesPolynomialTester ([1] : List Int) true = false := by\n"
            "  decide\n"),
    },

    # --- CLAUSE 1, combine=false sub-domain: always CARRY OUT the product,
    # --- ignoring the switch. The dual near-miss — correct only where the
    # --- factors combine; WRONG where they do not (it would report a single
    # --- evaluated value for a product that genuinely cannot be merged, e.g. a
    # --- transcendental left operand). Needs its own discriminating input
    # --- because it AGREES with the always-formal rival nowhere and with gold on
    # --- the opposite half.
    {
        "id": "reject-always-carried-out",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FORM_BLOCK,
                        "    let form := ProductForm.carriedOut\n"),
        "refinement": (
            "always carrying the product out — even when the two factors do NOT "
            "combine into a single value — reports a single evaluated value for a "
            "product that must genuinely stay formal (e.g. a transcendental left "
            "operand that cannot be cast into the polynomial's ring). This flips "
            "the combine=false verdict the spec pins, so scenarios that require the "
            "formal outcome fail. A real patch that unconditionally evaluated the "
            "product would NOT resolve (it would break the formal cases the F2P/"
            "conformance boundary also exercises)."
        ),
        "rationale": (
            "REJECT from clause 1: on combine=false the spec demands formalProduct "
            "and this impl returns carriedOut. Verifying would leave the "
            "formal branch unpinned (partial-domain SPEC-TOO-WEAK). Refuted at "
            "factorsCombineIntoPolynomial=false, productValue=[1] (the formal branch "
            "— the opposite value of the switch from the always-formal rival, so the "
            "boolean binder is moved across both truth values)."
        ),
        "witness": _tester(
            "example : formExpressionTimesPolynomialTester ([1] : List Int) false = false := by\n"
            "  decide\n"),
    },

    # --- CLAUSE 2, value preservation: get the FORM right but DISCARD the
    # --- supplied product value (return the empty list). Correct on the form
    # --- clause everywhere and on the value clause only where the supplied value
    # --- happens to be empty; WRONG (and rejected) wherever the carried-out
    # --- product has a non-empty value. This is the directive-5 read-only-input
    # --- attack: the operation must PRESERVE the supplied value, not overwrite it.
    {
        "id": "reject-value-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RETURN_LINE,
                        "    return { form := form, value := [] }\n"),
        "refinement": (
            "computing the form correctly but discarding the supplied combined "
            "value — returning an empty value instead of the one the surrounding "
            "(unchanged) combination machinery produced — reports a carried-out "
            "product whose value is not the product's actual value. The F2P "
            "requires the carried-out product to be the correct single value (e.g. "
            "x*Poly(x) equals Poly(x**2)); a patch that evaluated the product but "
            "threw away its value would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 2 (factorsCombineIntoPolynomial = true → out.value = "
            "productValue): on combine=true with a non-empty productValue the spec "
            "demands the value be preserved and this impl returns []. Verifying would "
            "mean the supplied read-only value is not pinned into the result "
            "(directive-5 / value SPEC-TOO-WEAK). Refuted at "
            "factorsCombineIntoPolynomial=true, productValue=[7] (a non-empty value "
            "the empty-list rival cannot match — moving the productValue binder off "
            "the [1] the form rivals hold it at)."
        ),
        "witness": _tester(
            "example : formExpressionTimesPolynomialTester ([7] : List Int) true = false := by\n"
            "  decide\n"),
    },

    # --- CLAUSE 2, value preservation, ORDER sub-domain. Added by the adversarial
    # --- audit: `reject-value-dropped` replaces the value with a CONSTANT, so it
    # --- is refuted by nothing more than "the result is non-empty". That leaves
    # --- the ORDER content of clause 2 unattacked — an impl that returns exactly
    # --- the supplied multiset of coefficients, permuted, is a strictly closer
    # --- near-miss and no shipped rival excludes it. Measured during the audit:
    # --- this rival does NOT verify (exit 1, `unsolved goals`), its witness
    # --- elaborates against it (exit 0) and `decide` REFUTES that same witness on
    # --- the frozen solution (exit 1, "`decide` proved that the proposition ... is
    # --- false"). The witness point must be NON-PALINDROMIC: at productValue=[1,1]
    # --- the rival AGREES with the frozen impl and the same witness correctly
    # --- fails against it (exit 1, measured), which is what makes [1,2] the
    # --- load-bearing input rather than a second spelling of [7].
    {
        "id": "reject-value-order-scrambled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RETURN_LINE,
                        "    return { form := form, value := productValue.reverse }\n"),
        "refinement": (
            "computing the form correctly and carrying a value of the right size, "
            "drawn from the right coefficients, but in the WRONG ORDER, reports a "
            "carried-out product that is a different value from the one the "
            "surrounding (unchanged) combination machinery produced — the "
            "coefficients denote different powers once permuted, so the reported "
            "product is a different polynomial. The F2P demands the carried-out "
            "product equal the actual product (x*Poly(x) equals Poly(x**2), and "
            "-2*Poly(x) equals Poly(-2*x)); a patch that evaluated the product but "
            "reordered the coefficient vector it carried would NOT resolve. This is "
            "a strictly harder near-miss than dropping the value: it preserves "
            "length, membership and multiplicity, and is wrong only in order."
        ),
        "rationale": (
            "REJECT from clause 2 (factorsCombineIntoPolynomial = true → out.value = "
            "productValue): the clause pins the value up to EQUALITY, hence up to "
            "order, not merely up to non-emptiness or up to the multiset of "
            "coefficients. Verifying would mean clause 2 constrains only which "
            "coefficients appear and not which power each one belongs to (an "
            "order-blind SPEC-TOO-WEAK that the empty-list rival cannot detect, "
            "since ANY non-empty result refutes that one). Refuted at "
            "factorsCombineIntoPolynomial=true, productValue=[1,2] — necessarily a "
            "non-palindromic value, and the first witness point in this battery with "
            "length > 1, so it also moves the productValue binder off the singleton "
            "lists every other case holds it at."
        ),
        "witness": _tester(
            "example : formExpressionTimesPolynomialTester ([1,2] : List Int) true = false := by\n"
            "  decide\n"),
    },

    # =====================================================================
    # ADMISSIBILITY / NON-DEGENERACY — added by the adversarial audit, which
    # re-derived the dropped nagini `admiss-f2p-shaped-self-call` as EXPRESSIBLE
    # here rather than vacuous. The precondition half of that nagini case really
    # is vacuous (this method has no `require`, so nothing can exclude an input),
    # but its other half is not: it also asserts the post-image is NON-DEGENERATE
    # at the interesting point. That is expressible on this carrier as an
    # in-region `assert`, and it pins something no `expect="verify"` positive
    # does — a positive shows SOME impl satisfies the spec, not that the spec's
    # two prescribed outcomes are DISTINCT observations. If `carriedOut` and
    # `formalProduct` were identifiable, clause 1 would be satisfiable by a
    # constant and both form rivals would be attacking nothing.
    #
    # The assert is live, and both halves were measured during the audit: this
    # case verifies (exit 0), and the same case with one conjunct falsified fails
    # (exit 1, "`decide` proved that the proposition ... is false"), so the
    # `all_goals decide` tail is discharging a real goal rather than passing
    # trivially. The impl body is kept byte-identical; only the assert is added
    # and the proof retuned to clear the extra goal (both elided from the spec
    # view, so `markers.same_spec` and the frozen obligation survive).
    # =====================================================================
    {
        "id": "admiss-nondegenerate-post-image",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _RETURN_LINE,
                  "    assert (with_name_prefix `admiss\n"
                  "      (((({ form := ProductForm.carriedOut, value := [1,2] }\n"
                  "            : ProductResult))\n"
                  "          ≠ { form := ProductForm.formalProduct, value := [1,2] })\n"
                  "       ∧ ({ form := ProductForm.carriedOut, value := [1,2] }\n"
                  "            : ProductResult).value = ([1,2] : List Int)\n"
                  "       ∧ (if true then ProductForm.carriedOut\n"
                  "          else ProductForm.formalProduct) = ProductForm.carriedOut\n"
                  "       ∧ (if false then ProductForm.carriedOut\n"
                  "          else ProductForm.formalProduct)\n"
                  "           = ProductForm.formalProduct))\n"
                  + _RETURN_LINE),
            _PROOF_BLOCK,
            "prove_correct formExpressionTimesPolynomial by\n"
            "  loom_solve\n"
            "  all_goals decide\n"),
        "rationale": (
            "NON-DEGENERACY of the post-image, the half of the dropped nagini "
            "admissibility case that IS expressible here. Four conjuncts: (a) the "
            "two results the spec prescribes at the same supplied value are "
            "DISTINCT observations — so clause 1 is a real two-valued discriminator "
            "and cannot be satisfied by a constant form, which is what makes "
            "reject-always-formal and reject-always-carried-out non-vacuous; (b) a "
            "carried-out result can hold a non-degenerate multi-element value, so "
            "clause 2 is satisfiable at the point the value rivals are refuted at "
            "rather than only at the empty list; (c,d) the spec's own selector "
            "delivers carriedOut on the combine branch and formalProduct on the "
            "formal branch, so BOTH prescribed outcomes are reachable and neither "
            "branch of clause 1 is dead. Must verify: an unsatisfiable in-region "
            "assert on a method with no `require` would mean the modeled post-image "
            "is degenerate at the F2P-shaped point (the observables collapse), which "
            "would make the whole reject lane an artifact."
        ),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling contracts FIVE @Pure/method
# surfaces and attaches its cases to an operand-selection machinery: the
# load-bearing discriminator there is a strict numeric ORDER between the two
# operands' selection ranks, and its dispatch predicate selects the right operand
# when that operand offers a handler and its rank is strictly greater.
#
# This velvet bundle models only the PURELY FUNCTIONAL CORE of the observable fix
# (mapping.md §2-3): a single method `formExpressionTimesPolynomial` over ONE
# boolean — `factorsCombineIntoPolynomial` (whether the two factors combine into
# a single value, the UNCHANGED convertibility machinery) — plus a free
# `productValue`. The operand-selection comparison is NOT modeled, because in the
# desired behaviour it holds for EVERY such product regardless of the left factor
# and so cannot distinguish the carried-out cases from the genuinely-formal ones
# (mapping.md §2); the real carried-out/formal verdict is decided by whether the
# factors combine, which is what the spec observes. This is carrier narrowing,
# not omission-by-difficulty.
#
#   nagini case                            -> here
#   ---------------------------------------------------------------------
#   pos-control-product-branch-reorder     -> pos-control-branch-reorder    PORTED
#   pos-control-priority-different-value   -> pos-control-match-on-switch    RE-AIMED
#   admiss-f2p-shaped-self-call            -> admiss-nondegenerate-post-image RE-AIMED
#                                             (audit: half was expressible)
#   reject-priority-equals-default-prepatch-> reject-always-formal           RE-EXPRESSED
#   reject-priority-below-default          -> (folded into reject-always-formal) SUBSUMED
#   reject-product-always-self             -> reject-always-formal           PORTED
#   reject-product-always-other            -> reject-always-carried-out      PORTED
#   reject-product-relaxed-ge-on-tie       -> (none)                         VACUOUS
#   (directive-5 value preservation)       -> reject-value-dropped           NEW (clause 2)
#   (clause-2 ORDER sub-domain)            -> reject-value-order-scrambled   NEW (audit)
#   AXIOM_TESTS (ax-sound / ax-contain)    -> (none)                         DROPPED (G-AX lane)
#
# RE-AIMED (pos-control-priority-different-value): the nagini positive shows any
#   in-spec selection rank above the baseline is correct — a latitude specific to
#   the rank carrier, which this bundle does not model. It is re-aimed at the
#   corresponding latitude on THIS carrier: any correct impl of the form
#   selection must verify regardless of its syntactic shape (here `match` vs
#   `if`), else the spec over-pins elaboration form (SPEC-TOO-STRONG).
# RE-EXPRESSED / SUBSUMED (the two rank-value rivals): both nagini rivals set the
#   rank so that selection prefers the GENERIC left operand and the product is
#   never carried out — the pre-image state. On this carrier the rank is not
#   modeled; the SAME observable failure (the product is never carried out even
#   when the factors combine) is `reject-always-formal`. The two nagini rivals
#   differ only in HOW they push the rank the wrong way (an exact tie vs strictly
#   below); on the modeled boolean carrier they collapse to the single "always
#   leave formal" rival, so the below-baseline case is subsumed rather than a
#   separate point. `reject-always-carried-out` adds the dual (the
#   always-delegate-right nagini rival) so BOTH branches of the switch are
#   attacked.
# RE-AIMED (admiss-f2p-shaped-self-call) — the audit CORRECTED this entry, which
#   previously recorded the whole case as VACUOUS. Split it in two:
#   * the PRECONDITION half really is vacuous: this method has no `require`, so
#     there is no clause that could exclude an input and nothing for a
#     precondition-admits-input probe to discharge. Unchanged verdict.
#   * the NON-DEGENERACY half is EXPRESSIBLE here, and the old entry's reason for
#     dropping it ("there is no pure helper in the model to assert a
#     non-degenerate literal value over") was wrong: an in-region `assert` needs
#     no helper — the `pure` region's own constructors and the spec's own selector
#     expression are enough, and the frozen `ProductForm`/`ProductResult` are
#     `DecidableEq`, so `decide` discharges it. It is now shipped as
#     `admiss-nondegenerate-post-image`.
#   The old entry also claimed the two soundness positives already discharge this
#   risk. They do not: a positive shows some impl SATISFIES the spec, which is
#   consistent with the two prescribed outcomes being the SAME observation. If
#   `carriedOut` and `formalProduct` were identifiable, clause 1 would be
#   satisfiable by a constant form and both form rivals would be attacking
#   nothing — so the distinctness is exactly what the reject lane rests on and it
#   is worth pinning explicitly.
# VACUOUS (reject-product-relaxed-ge-on-tie): the nagini rival relaxes a STRICT
#   `>` in the rank comparison to `>=`, wrong on the equal-rank tie. That
#   comparison is not modeled on this carrier (mapping.md §2: in the desired
#   behaviour it does not decide carried-out vs formal), so there is no
#   strict-order boundary to relax and no tie sub-domain to abuse. The class is
#   vacuous here; no substitute is fabricated.
# DROPPED (AXIOM_TESTS): the nagini battery's two AXIOM_TESTS validate its
#   A-reference deep models against the real library. This bundle has NO axiom and
#   NO deep-model reference (meta.json axioms=[], deep_model_references=[];
#   mapping.md §3), so there is no axiom lane to mirror. The axiom lane is G-AX's
#   job and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Both independent clauses are attacked:
#   * clause 1 (form/switch equivalence) by reject-always-formal (combine=true)
#     and reject-always-carried-out (combine=false) — the switch binder moved
#     across BOTH truth values;
#   * clause 2 (value preservation) by reject-value-dropped (combine=true,
#     productValue=[7]) AND, on the ORDER sub-domain clause 2 also pins,
#     reject-value-order-scrambled (combine=true, productValue=[1,2]);
#     — the productValue binder moved off the [1] the form rivals hold it at,
#     first to a different non-empty singleton the empty-list rival cannot echo,
#     then to a non-palindromic list of length > 1 that a length-or-multiset-only
#     reading of clause 2 would not refute.
#   Both clauses are also DEFENDED by two verifying soundness positives, and the
#   non-degeneracy of the post-image they satisfy is pinned separately by
#   admiss-nondegenerate-post-image. The four rejects sit at four distinct input
#   points (pts=4); none shares a witness with another (they fail on disjoint
#   sub-domains), and each point was measured to be NECESSARY — at the
#   corresponding agreement point ([] for the dropped-value rival, the palindrome
#   [1,1] for the order rival) the same witness correctly fails to refute.
#
# WHAT THE AUDIT PROBED AND DID NOT FIND. Five further wrong impls were built
#   against the frozen spec looking for a SPEC-TOO-WEAK hole; four were correctly
#   rejected (value reversed, value truncated to its tail, value replaced by a
#   constant non-empty list, form decided by the emptiness of the value instead of
#   the switch). The fifth — form correct, value preserved on the combine branch
#   but emptied on the FORMAL branch — VERIFIES, and that is CORRECT rather than a
#   hole: clause 2 is deliberately one-directional (`combine = true → ...`) because
#   on the formal branch nothing is evaluated, so `value` has no referent there and
#   the modeled observable is unconstrained by design (Solution.lean's `pure`
#   region says so: "the value the product carries when it IS carried out"). A
#   rival exploiting that latitude has no faithful failing counterpart, so it is
#   not shipped as a reject case. Four further CORRECT reshapes were built and all
#   verified (`cond` selector; return-the-record-in-both-branches, restructuring
#   the data flow rather than just the selector; `productValue ++ []`, which is not
#   closed by `rfl` alone; double-negated switch), so no SPEC-TOO-STRONG evidence
#   either.
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (deep functional model with
#   no oracle); this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
