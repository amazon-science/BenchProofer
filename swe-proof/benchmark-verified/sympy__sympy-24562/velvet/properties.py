"""properties.py — G-PBT falsification battery for sympy__sympy-24562 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct denominatorProduct`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it elaborates against the rival and FAILS against the
frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  denominatorProduct (pDen : Nat) (qDigits : List Nat) return (out : Nat)
    require pDen ≥ 1
    require ∀ d ∈ qDigits, d < 10
    ensures out = pDen * digitsValue qDigits

Two pieces are combined into a single whole-number result. ``pDen`` is a
positive factor already contributed by the first operand. ``qDigits`` is a
second operand supplied as a non-negative integer written in positional decimal
notation; ``digitsValue`` is the concrete, fully-unfolded ``def`` reading that
digit sequence to its numeric VALUE (most-significant-first). The single
load-bearing ``ensures`` clause pins the result to the arithmetic PRODUCT of the
factor and the operand's VALUE — not to any other reading of the digit sequence
(e.g. laying the sequence down repeatedly, dropping the factor, or shifting the
product off by one).

CARRIER NOTE (decisive for this port). Unlike bundles whose observable is an
opaque identity, ``digitsValue`` here is a concrete decidable ``Nat`` function
and the post-image is decidable arithmetic. So a rival's disagreement with the
spec is a DECIDABLE proposition at a concrete input: a refutation witness can be
built by ``decide`` and genuinely discriminates. That is why the uniqueness
class is LIVE on this carrier (contrast a bundle where every rival reduces to an
undecidable disequality of opaque terms — there the class collapses and rivals
are dropped; not so here).

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical assembly (the product formed directly, with the two
    factors commuted, or reached by repeated addition) must still verify, else the
    spec is SPEC-TOO-STRONG on the shape of the arithmetic. Three ``pos-*`` cases
    exercise this.
  * ADMISSIBILITY — RE-AIMED. Both preconditions (``pDen ≥ 1``; every digit
    ``< 10``) are trivially satisfiable for an F2P-shaped input, so the "a normal
    input meets the precondition" probe is not where the risk sits. The residual
    risk on this surface is that the post-image is UNSATISFIABLE / degenerate at
    the interesting point. ``admiss-product-grounded`` discharges a live in-region
    ``assert`` pinning the post-image's arithmetic value at the headline input.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — APPLY, and carry the discriminating
    content. Four rivals attack the value-product clause across four sub-domains
    — the digit-sequence-repeat reading (the modeled bug), dropping the factor, an
    off-by-one value corruption, and a partial-domain impl that is EXACT on
    single-digit operands and wrong beyond them — each with a machine-checked
    refutation witness at a distinct concrete input. The last is what attests that
    the clause binds on the whole domain rather than at sampled points; the other
    three are each wrong almost everywhere and so cannot show that on their own.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only heap input may carry a fractional permission an impl overwrites.
    Lean and Velvet are referentially transparent: every parameter is an
    immutable value (this bundle declares no ``mut`` binder on an input), there is
    no heap and no aliasing, so there is no read-only input to mutate and no
    substitute probe to build. Not fabricated. (See footer.)
  * UNGROUNDED-ORACLE ECHO — N/A. ``digitsValue`` is a concrete ``def`` in the
    ``pure`` region (the ``axioms`` region is empty — no opaque answer key to
    echo); the cheapest correct impl simply evaluates the product, which the
    positive controls cover honestly.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. The
four witnesses sit at four DISTINCT input points and vary BOTH input binders:
``pDen`` ranges over 2, 3, 1, 4 and ``qDigits`` over ``[1,0,0]``, ``[5]``,
``[7]``, ``[2,5]``. In particular the factor-dropping rival is refuted at
``pDen = 3`` (≠ 1) — the sub-domain on which ignoring ``pDen`` is observably
wrong — so the manifest genuinely demonstrates the post-image's dependence on
``pDen``, not merely its value at one pinned point. Every witness's gold-side
failure is SEMANTIC (`decide` reports the tester proposition is false at that
input), not a missing identifier or an elaboration gap, so each one discriminates
for the reason the class requires.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24562"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen assembly body, verbatim (the executable
# ---- lines strictly inside denominatorProduct's -- impl-start / -- impl-end).
# ---- Lies wholly inside the single impl region and is unique in the file (the
# ---- prepatch skeleton lives in a different file); both facts asserted at load
# ---- by _swap. Every variant _swap()s only this block (and, where the reshape
# ---- needs it, the proof body below), so the edit never touches the spec
# ---- regions (axioms/pure/pre/post + the method signature and the `ensures`).
_IMPL = (
    "    let mut acc : Nat := 1\n"
    "    let v := digitsValue qDigits\n"
    "    acc := acc * pDen\n"
    "    acc := acc * v\n"
    "    return acc"
)
assert _BASE.count(_IMPL) == 1, "denominatorProduct impl region drifted from expected text"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a case that introduces an in-region `assert` may
# ---- retune its script without touching the spec or dropping the obligation.
_PROOF = "prove_correct denominatorProduct by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY denominatorProduct's impl body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof_body):
    """Reshape the impl region AND retune the tactic body."""
    src = _swap(_BASE, _IMPL, new_impl)
    return _swap(src, _PROOF, "prove_correct denominatorProduct by\n" + new_proof_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `denominatorProductTester pDen qDigits = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("extract_program_for denominatorProduct\n"
            "prove_precondition_decidable_for denominatorProduct\n"
            "prove_postcondition_decidable_for denominatorProduct\n"
            "derive_tester_for denominatorProduct\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and only reshapes the
    # executable surface; the post-image is decidable arithmetic, so the reproof
    # stays a `loom_solve` away from the frozen script.
    # =====================================================================
    {
        "id": "pos-direct-product",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: form the product directly (read the operand value, multiply by
        # the factor) instead of accumulating in a fresh mutable counter. Same
        # value on the whole domain.
        "module": _impl(
            "    let v := digitsValue qDigits\n"
            "    return pDen * v"),
        "rationale": "reading the operand value and returning `pDen * v` directly "
                     "computes the identical value-product for every input, so "
                     "`out = pDen * digitsValue qDigits` still discharges; a "
                     "correct reshape must verify, else SPEC-TOO-STRONG on the "
                     "assembly's shape (the mutable-accumulator form is not "
                     "load-bearing).",
    },
    {
        "id": "pos-commuted-product",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: commute the two factors (`v * pDen` instead of `pDen * v`).
        # Multiplication on Nat is commutative, so the value is unchanged.
        "module": _impl(
            "    let v := digitsValue qDigits\n"
            "    return v * pDen"),
        "rationale": "commuting the factors (`v * pDen`) yields the same product by "
                     "commutativity of Nat multiplication, so the post-image holds; "
                     "must verify, else SPEC-TOO-STRONG against a correct commuted "
                     "form of the modeled arithmetic.",
    },
    {
        "id": "pos-repeated-addition",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the product as a REPEATED ADDITION — sum `pDen` copies
        # of the operand's value — instead of a single multiplication. Equal to
        # `pDen * v` on Nat, but by a different route: the reproof needs
        # `List.sum_replicate` rather than reducing to the frozen form, so this
        # exercises the spec against a correct impl whose shape is genuinely
        # further from the frozen one than a commutation is.
        "module": _impl_proof(
            "    let v := digitsValue qDigits\n"
            "    return (List.replicate pDen v).sum",
            "  loom_solve <;> simp [List.sum_replicate] <;> norm_cast"),
        "rationale": "summing `pDen` copies of the operand's value is the "
                     "repeated-addition form of the same product (`List.sum "
                     "(replicate n v) = n * v` on Nat), so `out = pDen * "
                     "digitsValue qDigits` still holds on the whole domain and it "
                     "must verify, else SPEC-TOO-STRONG against a correct impl "
                     "that reaches the product by accumulation rather than by a "
                     "single multiply. This is the reshape the port had EXCLUDED "
                     "as unlandable; the audit landed it (the obligation closes "
                     "once the tactic body is retuned, which the consumer spec "
                     "view elides), so it is shipped as the positive control it "
                     "always was rather than recorded as a dropped candidate.",
    },

    # =====================================================================
    # ADMISSIBILITY — both preconditions (`pDen ≥ 1`; every digit `< 10`) are
    # trivially satisfiable for any F2P-shaped input, so the "a normal input
    # meets the precondition" probe is vacuous. Re-aimed at the residual risk on
    # this surface: that the post-image is UNSATISFIABLE / degenerate at the
    # interesting point (a spec no impl can meet reads exactly like one every
    # impl meets). The in-region assert pins the post-image's arithmetic value at
    # the headline input (factor 2, operand digits [1,0,0] ↦ value 100, product
    # 200); the surrounding impl is kept verbatim so the method's own obligation
    # still discharges. The assert is live: a false claim in its place leaves an
    # unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-product-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (digitsValue [1,0,0] = 100 ∧ 2 * digitsValue [1,0,0] = 200))\n"
            + _IMPL,
            "  loom_solve <;> decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "headline F2P-shaped input: it demands the decimal operand be "
                     "read to its numeric value (digits [1,0,0] ↦ 100) and combined "
                     "with the factor as the arithmetic product (2 * 100 = 200). "
                     "The in-region assert must discharge (else the obligation is "
                     "unsatisfiable / PRECOND-TOO-STRONG); the impl is kept verbatim "
                     "so the method's own `ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # distinct concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-digit-repeat",
        "kind": "uniqueness",
        "expect": "reject",
        # The modeled bug: instead of reading the decimal operand for its VALUE
        # and multiplying, lay the digit sequence down `pDen` times end to end and
        # read the lengthened sequence. `[1,0,0]` twice is `[1,0,0,1,0,0]` (value
        # 100100), not the product 200.
        "module": _impl(
            "    let scaled := (List.replicate pDen qDigits).flatten\n"
            "    return digitsValue scaled"),
        "refinement": "a counterpart that combines the decimal operand by REPEATING "
                      "its digit sequence (the type-confusion where a still-textual "
                      "operand is laid down `pDen` times rather than read to its "
                      "value and multiplied) yields the lengthened-sequence value, "
                      "not the value-product — the exact misbehaviour the failing "
                      "test constructs (factor 2, operand `100` ↦ `100100` instead "
                      "of `200`). It would NOT resolve.",
        "rationale": "REJECT from `out = pDen * digitsValue qDigits`: reading the "
                     "`pDen`-fold repetition of the digit sequence gives "
                     "`digitsValue ((replicate pDen qDigits).flatten)`, which is "
                     "not the product `pDen * digitsValue qDigits` on any "
                     "non-degenerate input. Verifying would be SPEC-TOO-WEAK (it "
                     "would admit the digit-repeat reading). Refuted at the headline "
                     "input (pDen=2, qDigits=[1,0,0]).",
        "witness": _tester(
            "example : denominatorProductTester 2 [1,0,0] = false := by\n"
            "  decide"),
    },
    {
        "id": "weak-drops-factor",
        "kind": "uniqueness",
        "expect": "reject",
        # Return only the operand value, ignoring the factor pDen entirely.
        # Correct only when pDen = 1; wrong on every larger factor.
        "module": _impl(
            "    let v := digitsValue qDigits\n"
            "    return v"),
        "refinement": "a counterpart that returns only the operand's value and "
                      "drops the factor contributed by the first operand loses that "
                      "factor from the combined result, so a fractional first "
                      "operand's contribution vanishes; the combined result is wrong "
                      "on every input with a factor above one. It would NOT resolve.",
        "rationale": "REJECT from `out = pDen * digitsValue qDigits`: returning "
                     "`digitsValue qDigits` alone is not `pDen * digitsValue "
                     "qDigits` whenever `pDen ≠ 1`. Verifying would be "
                     "SPEC-TOO-WEAK on the `pDen` factor. Refuted at pDen=3 (≠ 1), "
                     "the sub-domain that makes the post-image's dependence on "
                     "`pDen` observable — no other rival's witness holds `pDen` "
                     "there.",
        "witness": _tester(
            "example : denominatorProductTester 3 [5] = false := by\n"
            "  decide"),
    },
    {
        "id": "weak-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss: the correct product shifted up by one. Right on
        # the whole domain except the +1, so it is refutable by the exact-value
        # post-image at any input.
        "module": _impl(
            "    let v := digitsValue qDigits\n"
            "    return pDen * v + 1"),
        "refinement": "a counterpart that returns the product plus one reports a "
                      "combined result one greater than the true value-product at "
                      "every input, a broken result that fails the test asserting "
                      "the exact combined value. It would NOT resolve.",
        "rationale": "REJECT from `out = pDen * digitsValue qDigits`: `pDen * v + 1` "
                     "is never equal to `pDen * v`, so the exact-value post-image "
                     "refutes it everywhere. Verifying would be SPEC-TOO-WEAK on the "
                     "exact combined value. Refuted at a third distinct input "
                     "(pDen=1, qDigits=[7]) varying both binders away from the "
                     "other rivals.",
        "witness": _tester(
            "example : denominatorProductTester 1 [7] = false := by\n"
            "  decide"),
    },
    {
        "id": "weak-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN rival: exactly right on single-digit operands (and on
        # the empty one), drops the factor on every longer operand. The three
        # rivals above are each wrong on essentially the WHOLE domain, so all of
        # them would still be rejected by a spec that only constrained the result
        # at some inputs. This one agrees with the frozen impl on a non-trivial
        # sub-domain and diverges only outside it, so its rejection is what
        # attests that the `ensures` binds at EVERY input rather than merely on a
        # sampled point — the sibling's partial-domain class, re-aimed onto the
        # binder this carrier actually has.
        "module": _impl(
            "    let v := digitsValue qDigits\n"
            "    if qDigits.length ≤ 1 then\n"
            "      return pDen * v\n"
            "    else\n"
            "      return v"),
        "refinement": "a counterpart correct only while the decimal operand is a "
                      "single digit — and dropping the factor as soon as the "
                      "operand is longer — passes any check that only ever "
                      "exercises short operands, yet the reported misbehaviour is "
                      "at a MULTI-digit operand, so the failing test still fails. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = pDen * digitsValue qDigits`: on the "
                     "`qDigits.length > 1` branch the impl returns `digitsValue "
                     "qDigits`, which is not `pDen * digitsValue qDigits` once "
                     "`pDen ≠ 1`. The verifier reports the unsolved goal under the "
                     "`if_neg : ¬qDigits.length ≤ 1` hypothesis, i.e. the "
                     "rejection is attributable to the clause on exactly the "
                     "sub-domain where the rival diverges. Verifying would be "
                     "SPEC-TOO-WEAK on TOTALITY — a spec pinned only at short "
                     "operands would admit this. Refuted at a fourth distinct "
                     "input (pDen=4, qDigits=[2,5]).",
        "witness": _tester(
            "example : denominatorProductTester 4 [2,5] = false := by\n"
            "  decide"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 6 SPEC cases (1
# soundness positive, 1 admissibility, 1 frame-mutation rival, 3 uniqueness
# rivals) plus 3 AXIOM_TESTS. The sibling contracts one function `combine_ratio`
# over a permission-bearing carrier that models the FULL (numerator, denominator)
# pair with four inputs (p_num, p_den, q_digits, q_den) and a @Pure/@ContractOnly
# `read_int` axiom. This bundle models only the purely-functional CORE — a single
# method `denominatorProduct` computing the combined DENOMINATOR from two inputs
# (`pDen`, `qDigits`) — over concrete decidable `Nat` carriers with a deep
# `digitsValue` def and no axioms. The denominator value surface carries across
# intact; the numerator branch, the `q_den` input, and the permission surface are
# not modeled here (carrier narrowing). Every sibling case is accounted for.
#
#   sibling case               kind          -> here
#   -------------------------------------------------------------------------
#   frame-mut-qdigits          uniqueness    -> (none)                  VACUOUS
#   partial-domain-numerator   uniqueness    -> weak-partial-domain     RE-AIMED
#   denominator-uses-qden      uniqueness    -> weak-digit-repeat       RE-EXPRESSED
#   denominator-drops-pden     uniqueness    -> weak-drops-factor       PORTED
#   pos-control-reorder        soundness     -> pos-commuted-product    PORTED
#                                              (+ pos-direct-product ADDED)
#                                              (+ pos-repeated-addition ADDED)
#   admiss-f2p-shaped          admissibility -> admiss-product-grounded RE-AIMED
#   ax-read-int-sound          axiom         -> (none)                  G-AX
#   ax-read-int-containment    axiom         -> (none)                  G-AX
#   ax-aux-value-sound         axiom         -> (none)                  G-AX
#
# PORTED / RE-EXPRESSED (2 reject + 1 soundness):
#   - denominator-drops-pden -> weak-drops-factor. Identical argument (the
#     combined denominator drops the dividend-denominator factor), re-expressed as
#     `return digitsValue qDigits` (drop `pDen`). Refuted at pDen=3.
#   - denominator-uses-qden's argument (the combined denominator uses a WRONG
#     reading of the divisor's textual operand rather than its numeric value)
#     re-expresses HERE as weak-digit-repeat: the sibling's `q_den`-vs-read_int
#     distinction has no `q_den` binder on this carrier, but the SAME failure —
#     combining the operand by a non-value reading of its digits — is exactly the
#     modeled type-confusion bug (repeat the digit sequence vs multiply its
#     value). This is the headline discriminator (Rational('0.5','100') ↦ 100100
#     not 200) and the literal pre-patch skeleton, refuted at pDen=2, [1,0,0].
#   - pos-control-reorder -> pos-commuted-product (multiplication commuted). A
#     second positive (pos-direct-product, the product formed directly without the
#     mutable accumulator) is ADDED so the reshape space is exercised by two
#     distinct correct forms rather than one.
# RE-AIMED (1): admiss-f2p-shaped relied on the sibling's non-trivial half-
#   permission precondition admitting a normal input. The preconditions here
#   (`pDen ≥ 1`; digits `< 10`) are trivially satisfiable for every F2P-shaped
#   input, so that probe is vacuous. Re-aimed at the total-domain admissibility
#   risk: the post-image being degenerate / unsatisfiable at the interesting
#   point. admiss-product-grounded discharges a live in-region assert pinning the
#   post-image's arithmetic value at the headline input (2 * 100 = 200).
# VACUOUS — frame/permission-mutation (1): frame-mut-qdigits rejects a no-op WRITE
#   to a read-only list input for insufficient fractional permission. This backend
#   is referentially transparent, has no heap and no aliasing, and this bundle
#   declares no `mut` input binder — there is no read-only input to overwrite and
#   no permission system to trip. The class does not exist on this carrier; no
#   substitute is fabricated (per the porting map).
# RE-AIMED (2) — partial-domain-numerator. The port had recorded this as NOT
#   MODELED on the ground that it attacks the NUMERATOR post-image, for which
#   this carrier has no `p_num`/`q_den` binder. The binder observation is true but
#   the disposition was wrong: what the sibling case TESTS is not the numerator
#   specifically, it is that the obligation binds on the WHOLE domain rather than
#   on the sub-domain a narrow spec had seen — and that IS expressible here, on
#   the binders this carrier does have. weak-partial-domain is that case: exact on
#   single-digit operands, factor-dropping on longer ones. Every other rival in
#   this battery is wrong almost everywhere, so before this case nothing in the
#   manifest distinguished "the spec pins the product at every input" from "the
#   spec pins it at the sampled points"; the audit added it and it rejects, with
#   the verifier naming the `¬qDigits.length ≤ 1` branch.
# EXCLUDED reject candidates (from the recorded G-EQ attack set), reported here
#   for completeness so the omission is auditable rather than silent:
#   - `return v * pDen` (atk_6): a CORRECT commuted echo — shipped as the
#     soundness positive pos-commuted-product, not as a reject.
#   - `return (List.replicate pDen v).sum` (sibling atk_7 family): likewise
#     CORRECT (the sum of `pDen` copies of `v` equals `pDen * v` on Nat), so it is
#     rightly not a reject. The port additionally claimed it could not be landed
#     as a POSITIVE either; that claim was false and the audit retired it. The
#     obligation closes once the tactic body is retuned (`simp
#     [List.sum_replicate]` then `norm_cast`, to clear the `↑pDen` the
#     `sum_replicate` rewrite leaves), and the tactic body is elided from the
#     consumer spec view, so retuning it costs the case nothing. Shipped as
#     pos-repeated-addition.
# AXIOM_TESTS (3): dropped. The axiom lane is G-AX's job (this bundle has no
#   axioms — meta.json G-AX status = "skip"), and this gate ignores AXIOM_TESTS.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause `out = pDen *
#   digitsValue qDigits` is attacked by four rivals across four sub-domains — the
#   digit-sequence-repeat reading (the modeled bug), the dropped `pDen` factor, an
#   off-by-one value corruption, and a partial-domain impl exact on short operands
#   — refuted at four DISTINCT input points. Both input binders are varied: `pDen`
#   over 2, 3, 1, 4 and `qDigits` over [1,0,0], [5], [7], [2,5]. The
#   factor-dropping rival is refuted at pDen=3 (≠ 1), which is what demonstrates
#   the post-image's dependence on `pDen`; the digit-repeat rival demonstrates its
#   dependence on the VALUE (not the byte-length) of `qDigits`; the partial-domain
#   rival is what demonstrates the clause binds at EVERY input and not only where
#   a narrow reading would sample it.
#
# AUDIT NOTE — spec strength probed beyond the shipped rivals. 11 further WRONG
#   impls were built against the frozen spec and every one was rejected: digit-sum
#   in place of the value, reversed digit order, base-16 place value, dropping the
#   last digit, operand length in place of its value, sum-seeded-at-one, a
#   `max`-clamp echo, `pDen + v` in place of the product, an unconditional
#   two-fold digit repeat, and an off-by-one on the FACTOR (`(pDen+1) * v`). No
#   spec hole was found. Four correct reshapes were also probed; three verify
#   (shipped as the three positives) and one — the imperative `while`/`forIn`
#   digit-accumulating loop — could not be closed here: the failure is a
#   loop-invariant proof burden (`Failed to prove assertion ... WPGen (forIn ...)`,
#   and `simp_all [digitsValue]` on the `take`-based invariant hits max recursion
#   depth), NOT a spec rejection, so it is recorded as UNCERTAIN rather than as a
#   soundness hole: the frozen spec's value-product clause is manifestly satisfied
#   by that impl and the gap is in the reproof, which is outside the spec view.
AXIOM_TESTS = []
