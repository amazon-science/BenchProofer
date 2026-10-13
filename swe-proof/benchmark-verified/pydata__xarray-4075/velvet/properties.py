"""properties.py — G-PBT falsification battery for pydata__xarray-4075 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct sumOfWeights`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness ELABORATES against the rival and FAILS
against the frozen solution).

DEFENDED SURFACE (one contracted method over an aligned position carrier — the
data array as ``List (Option Int)`` (present ``some _`` / missing ``none``) and
the weights as ``List Int``):

  sumOfWeights (da : List (Option Int)) (weights : List Int)
      (weightsAreLogical : Bool) return (out : Option Int)
    ensures out = sumOfWeightsSpec da weights          -- THE load-bearing clause

There are NO ``require`` clauses: every list pair is in-domain (Lean indexing is
total; the reduction is defined front-recursively over whatever prefix the two
lists share). The method reduces the weights at the PRESENT data positions to
their arithmetic total, then reports a zero total as absent.

``sumOfWeightsSpec da weights`` is a total, fully-unfolded pure function of the
method's own inputs (``pure`` region):

    if arithDot (maskOf da) weights = 0 then none else some (arithDot (maskOf da) weights)

where ``maskOf da`` is the per-position presence pattern (``Option.isSome``) and
``arithDot`` is the position-wise numeric contraction ``Σ present_i · weight_i``.
The load-bearing fact the fix restores: the total is the NUMERIC contraction
regardless of how the weights are CARRIED — it counts the contributing weights,
it does not merely detect their presence (a logical carrier would collapse the
contraction to a 0/1 truth value, the exact defect the issue reports).

The clause has NO opaque answer key to echo (directive 8): ``sumOfWeightsSpec``
is a concrete ``def`` over the method's own arguments. The reduction callee it
delegates to (``reduceDot``) is modeled DEEPLY in the ``pure`` region (an
A-reference, validated == the real callee by G-AX), so it carries no consumed
axiom either. The clause decomposes into three independently-attackable
structural sub-behaviours:

  * COUNT      — the total is the arithmetic contraction (``arithDot``), a genuine
                 sum of the present positions' weights, NOT a truth-valued
                 collapse and NOT a constant;
  * PRESENCE   — only the PRESENT positions contribute (``maskOf`` = the
                 ``Option.isSome`` pattern); a missing datum contributes nothing;
  * ZERO-MASK  — a zero total is reported as ``none`` (absent), a nonzero total as
                 ``some total``.

METHOD BINDERS (three; the post-image pins the result for every value of each):
  * ``da``               — the data array's present/absent pattern (COUNT, PRESENCE);
  * ``weights``          — the aligned integer weights (COUNT, ZERO-MASK);
  * ``weightsAreLogical`` — the carrier-type tag. The post-image is INVARIANT to
                 it (the total is numeric either way), so it is the binder a
                 dtype-collapse rival abuses: a rival that reduces logically when
                 the tag is set agrees with gold on every ``false`` input and
                 diverges only when the tag is ``true`` and the true count ≥ 2.

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS here. The sibling makes this its
    MANDATORY lane (both ``mask`` and ``weights`` are held at half permission),
    but Lean/Velvet are referentially transparent: every input is an immutable
    value, the method declares no ``mut`` binder, there is no heap and no
    aliasing. There is no read-only cell to overwrite, so no substitute probe is
    fabricated (per the porting map, this class is legitimately dropped).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``sumOfWeightsSpec da weights`` — a concrete ``def`` over the
    method's own arguments (no consumed axiom; the reduction is a deep model).
    The only satisfier is the grounded assembly itself; there is nothing to echo.
  * PARTIAL-DOMAIN / VALUE — the central attack (the bug IS a sub-domain
    divergence). Each rival gets the SHAPE right (an ``Option Int`` result) and is
    correct on part of the domain, but diverges on one sub-behaviour above.
  * ADMISSIBILITY — CARRIED (``admiss-f2p-reachable``). The obligation has no
    ``require``, so PRECOND-TOO-STRONG cannot arrive as an unsatisfiable guard;
    the analogue on this total carrier is the obligation being UNSATISFIABLE at
    an F2P-shaped input, which a positive that discharges the method's own triple
    at that concrete input BY EVALUATION — as a ``have``, before closing the
    frozen obligation verbatim — tests directly. "No precondition" is NOT a
    reason to drop this lane.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
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

WITNESS MECHANICS. The frozen impl is LOOP-FREE (a mask map, one reduction, one
zero test), so its extracted tester reduces under ``decide``. Each reject rival
is likewise a loop-free expression, so its tester also ``decide``s. Each reject
rival therefore carries a machine-checked refutation ``witness`` — a Velvet
tester statement ``sumOfWeightsTester da weights weightsAreLogical = false`` at
ONE concrete input, checked in a file whose ``prove_correct`` block has been
stripped so no tactic script can mask the verdict. Both halves were checked
out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against its
rival (the tester ``decide``s to ``false`` — the rival's output violates the
postcondition there) and FAILS against the frozen solution (gold's tester
``decide``s to ``true``, so ``= false`` is refuted). There are no ``require``
clauses, so no witness is vacuously excluded.

AXIOM lane: DROPPED. ``meta.json`` declares no consumed axioms — the reduction
callee is a deep-model A-reference validated by G-AX (``axiom_check.py``), which
is G-AX's job, not this gate's. This gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4075"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end`. Every rival and reshape edits ONLY this block (and, for the
# positives, the elided `prove_correct` tactic body), so the spec view is
# untouched and same_spec holds by construction.
_IMPL = (
    "    let mask := maskOf da\n"
    "    -- Route logical-carrier weights through the numeric reduction (the carrier\n"
    "    -- that yields a count, not a truth value); other weights reduce directly.\n"
    "    let s : Int :=\n"
    "      if weightsAreLogical then reduceDot mask weights false\n"
    "      else reduceDot mask weights weightsAreLogical\n"
    "    let out := if s = 0 then none else some s\n"
    "    return out"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. Rivals leave it as-is, so the wrong impl leaves the
# postcondition goal unsolved and the rival MODULE fails to build — which is what
# expect="reject" needs; the witness, not the module build, attributes the
# rejection to the spec. A correct reshape may RETUNE this block (it is elided
# from the spec view) so its proof closes for the new impl shape.
_PROOF = (
    "prove_correct sumOfWeights by\n"
    "  loom_solve\n"
    "  cases weightsAreLogical <;> simp_all [reduceDot, sumOfWeightsSpec]"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


def _reproved(new_proof):
    """The FROZEN impl, verbatim, with only the elided proof body retuned.

    Used by the admissibility control: it must leave the impl untouched so its
    outcome is attributable to the obligation's SATISFIABILITY at the probed
    input and to nothing about a candidate impl.
    """
    return _swap(_BASE, _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `sumOfWeightsTester da weights weightsAreLogical = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict; both the rival and the frozen impl
# ---- are loop-free, so both testers reduce under `decide`.
def _witness(call):
    return ("extract_program_for sumOfWeights\n"
            "prove_precondition_decidable_for sumOfWeights\n"
            "prove_postcondition_decidable_for sumOfWeights\n"
            "derive_tester_for sumOfWeights\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Instead of computing the
    # mask/reduction/zero-mask by hand, it returns the pure model directly. The
    # ensures IS `out = sumOfWeightsSpec da weights`, so the body is
    # definitionally the RHS and the frozen `loom_solve` closes it (the extra
    # `cases`/`simp_all` line the frozen proof carries is unneeded here — the
    # proof is retuned to `loom_solve`, which is elided from the spec view).
    # Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-spec-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    let out := sumOfWeightsSpec da weights\n"
            "    return out",
            "prove_correct sumOfWeights by\n  loom_solve"),
        "rationale": "structurally different CORRECT impl: it returns the pure "
                     "model `sumOfWeightsSpec da weights` directly rather than "
                     "recomputing the mask, reduction and zero-mask by hand. "
                     "Observationally identical on every input, so "
                     "`out = sumOfWeightsSpec da weights` holds on the whole "
                     "domain and `loom_solve` closes the byte-identical "
                     "obligation. If it FAILS => SPEC-TOO-STRONG (the postcondition "
                     "would reject its own model's output).",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — a value-equivalent RESHAPE that unfolds
    # the carrier-routing branch. Because `reduceDot _ _ false = arithDot`
    # (`reduceDot_false`) and the gold routes BOTH tags to the `false` leg, the
    # whole `if weightsAreLogical then …` collapses to `arithDot mask weights`.
    # This impl computes that directly — a different control-flow shape, same
    # value on every input. The proof is retuned (`loom_solve; simp_all
    # [sumOfWeightsSpec]`) to close the new shape. Verified out-of-band.
    # =====================================================================
    {
        "id": "pos-arithdot-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    let mask := maskOf da\n"
            "    let s : Int := arithDot mask weights\n"
            "    let out := if s = 0 then none else some s\n"
            "    return out",
            "prove_correct sumOfWeights by\n  loom_solve\n  simp_all [sumOfWeightsSpec]"),
        "rationale": "branch-COLLAPSE positive control: the gold routes both "
                     "carrier tags to the numeric leg, and the numeric leg IS "
                     "`arithDot`, so the carrier-routing `if` is value-equivalent "
                     "to `arithDot mask weights` computed directly. Different "
                     "control-flow shape, identical value on every input; "
                     "`out = sumOfWeightsSpec da weights` still holds. Must verify, "
                     "else SPEC-TOO-STRONG on a trivial reshape.",
    },
    # =====================================================================
    # POSITIVE CONTROL 3 (soundness) — a correct reshape that computes the
    # contraction with a DIFFERENT recursion scheme: instead of the frozen
    # front-recursive `arithDot`, it zips the mask against the weights
    # position-wise and sums the resulting list. Same value on every input, but
    # the equality is NOT definitional — the frozen `simp_all` cannot see it, so
    # the retuned proof supplies the bridging induction as a local `have`. This
    # is the positive the other two do not give: both of those reduce to
    # `arithDot`/`sumOfWeightsSpec` by unfolding alone, so neither would detect a
    # spec that only accepted impls syntactically shaped like the frozen fold.
    # Verified with a real build (exit 0).
    # =====================================================================
    {
        "id": "pos-zipwith-sum",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    let s : Int :=\n"
            "      (List.zipWith (fun m w => if m then w else 0)\n"
            "        (maskOf da) weights).sum\n"
            "    let out := if s = 0 then none else some s\n"
            "    return out",
            "prove_correct sumOfWeights by\n"
            "  have key : ∀ (m : List Bool) (w : List Int),\n"
            "      (List.zipWith (fun a b => if a then b else 0) m w).sum"
            " = arithDot m w := by\n"
            "    intro m\n"
            "    induction m with\n"
            "    | nil => intro w; simp [arithDot]\n"
            "    | cons hd tl ih =>\n"
            "      intro w\n"
            "      match w with\n"
            "      | [] => simp [arithDot]\n"
            "      | c :: cs => simp [arithDot, ih]\n"
            "  loom_solve\n"
            "  simp_all [sumOfWeightsSpec, key]"),
        "rationale": "RECURSION-SCHEME reshape: the contraction is computed by "
                     "zipping the presence mask against the weights position-wise "
                     "and summing, rather than by the frozen front-recursive fold. "
                     "Equal in value on every input but NOT by unfolding — the "
                     "bridging identity needs a real induction, supplied as a local "
                     "`have` in the retuned (elided) proof body. This is the "
                     "positive that pins the spec's tolerance for a genuinely "
                     "different ALGORITHM producing the same total, not merely a "
                     "different spelling of the same one. If it FAILS => "
                     "SPEC-TOO-STRONG (the obligation would pin the shape of the "
                     "reduction rather than its value).",
    },

    # =====================================================================
    # ADMISSIBILITY (kind="admissibility", expect="verify"). The obligation
    # carries no `require`, so PRECOND-TOO-STRONG cannot arrive as an
    # unsatisfiable guard. Its analogue on a total carrier is the obligation
    # being UNSATISFIABLE at exactly an F2P-shaped input — a post-image no
    # computation can hit there — and that is what this control tests directly:
    # it keeps the frozen impl VERBATIM (only the elided proof body is retuned)
    # and discharges, as a `have` BY EVALUATION at the concrete F2P-shaped input
    # (a fully-present two-position array with two logical unit weights), the
    # method's own triple at that point, plus the spec-side value it must hit.
    # Then the frozen obligation is closed BYTE-IDENTICALLY afterwards, so
    # nothing is weakened and the case still fails if the real obligation breaks.
    #
    # It is a REAL test, not decoration: two negative controls were built.
    #   * the same `have` stated at the WRONG post-image (`out = some 1` — the
    #     truth-valued collapse the pre-fix carrier produces) FAILS, exit 1,
    #     `⊢ False` after the impl's own reduction;
    #   * `hpost` stated at the wrong spec value FAILS, exit 1, with `decide`
    #     reporting the proposition is false.
    # So the discharge tracks the claim; it cannot be satisfied by an
    # unsatisfiable or mis-stated obligation. Both the case and its two negative
    # controls were built out-of-band with the real verifier.
    # =====================================================================
    {
        "id": "admiss-f2p-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _reproved(
            "prove_correct sumOfWeights by\n"
            "  have hpost : sumOfWeightsSpec [some 1, some 1] [1, 1] = some 2 := by"
            " decide\n"
            "  have hreach : triple True (sumOfWeights [some 1, some 1] [1, 1] true)\n"
            "      (fun out => out = some 2) := by\n"
            "    simp only [sumOfWeights, triple]\n"
            "    intro _\n"
            "    rw [wp_pure]\n"
            "    simp [maskOf, arithDot, reduceDot]\n"
            "  loom_solve\n"
            "  cases weightsAreLogical <;> simp_all [reduceDot, sumOfWeightsSpec]"),
        "rationale": "ADMISSIBILITY on a total carrier: there is no `require` to be "
                     "too strong, so the analogue tested here is that the obligation "
                     "is SATISFIABLE at an F2P-shaped input — a fully-present "
                     "two-position data array with two logical unit weights, the "
                     "point where the load-bearing behaviour is observed. The case "
                     "keeps the frozen impl verbatim and discharges the method's own "
                     "triple at that concrete input BY EVALUATION as a `have` "
                     "(`out = some 2`), together with the spec-side value "
                     "`sumOfWeightsSpec [some 1, some 1] [1, 1] = some 2` by "
                     "`decide`, before closing the byte-identical frozen obligation. "
                     "If the post-image were unreachable at that input, or the spec "
                     "pinned a value no computation produces there, the `have` could "
                     "not be discharged => PRECOND-TOO-STRONG. Negative controls "
                     "confirm the discharge tracks the claim: the same `have` at the "
                     "truth-valued post-image (`out = some 1`) fails with `⊢ False`, "
                     "and `hpost` at a wrong spec value fails under `decide`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is a loop-free
    # expression so its extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-logical-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gold bug: reduce with the carrier tag passed straight through, so a
        # logical-carrier weight array collapses the contraction to a 0/1 truth
        # value. Correct on every non-logical (tag=false) input; diverges only
        # when the tag is TRUE and the true count >= 2.
        "module": _impl(
            "    let mask := maskOf da\n"
            "    let s : Int := reduceDot mask weights weightsAreLogical\n"
            "    let out := if s = 0 then none else some s\n"
            "    return out"),
        "refinement": "this IS the pre-fix behaviour: the weights are handed to "
                      "the reduction with their carrier unchanged, so a logical "
                      "carrier makes the reduction collapse to a presence "
                      "indicator (0/1) instead of the count. Its faithful real "
                      "counterpart is the unpatched repo, which on the F2P input "
                      "(present data, two logical unit weights) returns 1, not the "
                      "count 2 — the exact issue. It fails "
                      "test_weighted_sum_of_weights_bool (expects 2) and "
                      "test_weighted_mean_bool, so it does NOT resolve.",
        "rationale": "REJECT from `out = sumOfWeightsSpec da weights` via the COUNT "
                     "sub-behaviour: the spec's total is the numeric contraction "
                     "regardless of carrier, but with the tag TRUE the rival "
                     "collapses to the truth-valued reduction (<= 1). "
                     "PARTIAL-DOMAIN: correct on every tag=false input, wrong on the "
                     "logical-carrier sub-domain when the count >= 2. Refuted at "
                     "da=[some 1, some 1], weights=[1,1], weightsAreLogical=true: "
                     "gold's total is 2 (some 2), the rival's is 1 (some 1). "
                     "Discrimination comes from the `weightsAreLogical` binder "
                     "being true. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _witness("sumOfWeightsTester [some 1, some 1] [1, 1] true"),
    },
    {
        "id": "weak-always-logical",
        "kind": "uniqueness",
        "expect": "reject",
        # Forces the truth-valued reduction on EVERY input (tag ignored). Returns
        # a 0/1 presence indicator regardless of the true count -> wrong whenever
        # the count is >= 2, even for plain numeric weights.
        "module": _impl(
            "    let mask := maskOf da\n"
            "    let s : Int := reduceDot mask weights true\n"
            "    let out := if s = 0 then none else some s\n"
            "    return out"),
        "refinement": "an impl that always reduced logically — e.g. one that cast "
                      "the weight operand to a boolean carrier before the "
                      "reduction — returns a 0/1 presence indicator, never the "
                      "count, on ANY input with >= 2 present positive weights. It "
                      "fails test_weighted_sum_of_weights_bool (expects 2, gets 1) "
                      "and every numeric-weight count test, so it does NOT resolve.",
        "rationale": "REJECT from `out = sumOfWeightsSpec da weights` via the COUNT "
                     "sub-behaviour (the unconditional dual of "
                     "weak-logical-collapse): the truth-valued reduction is <= 1 on "
                     "every input, but the spec demands the numeric total. Refuted "
                     "at da=[some 5, some 3], weights=[2,3], weightsAreLogical=false: "
                     "gold's total is 5 (some 5), the rival's is 1 (some 1). "
                     "Discrimination comes from `weights` carrying values > 1 with "
                     "the tag FALSE (a point weak-logical-collapse does not reach). "
                     "If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _witness("sumOfWeightsTester [some 5, some 3] [2, 3] false"),
    },
    {
        "id": "weak-const-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Returns the constant `none` (total forced to 0). Correct ONLY on the
        # all-absent / all-zero-weight sub-domain (where the spec is `none` too);
        # wrong on any input with a present positive weight.
        "module": _impl(
            "    let mask := maskOf da\n"
            "    let s : Int := 0\n"
            "    let out := if s = 0 then none else some s\n"
            "    return out"),
        "refinement": "an impl that short-circuited the reduction to a zero total "
                      "would report every result as absent. It is correct only on "
                      "the all-absent / all-zero-weight sub-domain; on the F2P "
                      "input the count is 2, so sum_of_weights would be absent — "
                      "failing test_weighted_sum_of_weights_bool and dividing by "
                      "nothing in the mean. Does NOT resolve.",
        "rationale": "REJECT from `out = sumOfWeightsSpec da weights` via the COUNT "
                     "sub-behaviour: 0 (=> none) != the true total whenever any "
                     "present position carries a positive weight. PARTIAL-DOMAIN: "
                     "pins only the zero-total slice. Refuted at da=[some 1], "
                     "weights=[1], weightsAreLogical=false: gold's total is 1 "
                     "(some 1), the rival's is none. Discrimination comes from a "
                     "single present unit weight. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _witness("sumOfWeightsTester [some 1] [1] false"),
    },
    {
        "id": "weak-drop-zero-mask",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the ZERO-MASK sub-behaviour: reports the total as `some s` even
        # when s = 0, instead of `none`. Correct on every nonzero-total input;
        # diverges only when the total is exactly 0 (all absent / all-zero-weight).
        "module": _impl(
            "    let mask := maskOf da\n"
            "    let s : Int :=\n"
            "      if weightsAreLogical then reduceDot mask weights false\n"
            "      else reduceDot mask weights weightsAreLogical\n"
            "    let out := some s\n"
            "    return out"),
        "refinement": "an impl that omitted the zero-total masking would report a "
                      "zero sum of weights as a valid `0` rather than absent. A "
                      "zero total carries no usable normalization for the weighted "
                      "mean (it would divide by zero / propagate a bogus 0 weight); "
                      "the guard that replaces a zero total with an absent marker "
                      "is a real part of the behaviour, so dropping it diverges "
                      "from gold on the all-absent sub-domain and does NOT resolve.",
        "rationale": "REJECT from `out = sumOfWeightsSpec da weights` via the "
                     "ZERO-MASK sub-behaviour: the spec maps a zero total to "
                     "`none`, the rival to `some 0`. Refuted at da=[none], "
                     "weights=[1], weightsAreLogical=false: the datum is absent so "
                     "the total is 0; gold returns none, the rival some 0. "
                     "Discrimination comes from an ABSENT `da` position (total 0) — "
                     "the binder point no COUNT rival probes. If it VERIFIES => "
                     "SPEC-TOO-WEAK (the absent-marking is unpinned).",
        "witness": _witness("sumOfWeightsTester [none] [1] false"),
    },
    {
        "id": "weak-ignore-presence",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the PRESENCE sub-behaviour: treats EVERY position as present
        # (ignores the null pattern) instead of `maskOf da`. Correct whenever `da`
        # has no missing positions; diverges when a missing position carries a
        # nonzero weight (it wrongly counts that weight).
        "module": _impl(
            "    let mask := da.map (fun _ => true)\n"
            "    let s : Int :=\n"
            "      if weightsAreLogical then reduceDot mask weights false\n"
            "      else reduceDot mask weights weightsAreLogical\n"
            "    let out := if s = 0 then none else some s\n"
            "    return out"),
        "refinement": "an impl that summed ALL weights instead of masking to the "
                      "present positions would count the weights at missing data "
                      "positions too — the very error the masking exists to "
                      "prevent (the weights of NaN data must not enter the sum). "
                      "The failing/regression sum-of-weights-with-nan tests assert "
                      "those positions are excluded, so this does NOT resolve.",
        "rationale": "REJECT from `out = sumOfWeightsSpec da weights` via the "
                     "PRESENCE sub-behaviour: the spec masks with "
                     "`maskOf da = da.map Option.isSome`, the rival forces every "
                     "position present, so they disagree whenever a missing `da` "
                     "position carries a nonzero weight. Refuted at "
                     "da=[none, some 1], weights=[1,4], weightsAreLogical=false: "
                     "gold counts only the present position (some 4), the rival "
                     "counts both (some 5). Discrimination comes from a MISSING "
                     "`da` position with a nonzero weight. If it VERIFIES => "
                     "SPEC-TOO-WEAK (the presence mask is unpinned).",
        "witness": _witness("sumOfWeightsTester [none, some 1] [1, 4] false"),
    },
    {
        "id": "weak-zero-mask-by-any",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the ZERO-MASK sub-behaviour at its NEAR-MISS point, which
        # weak-drop-zero-mask does not reach. It keeps the absent-marking, but
        # keys it on the wrong predicate: absence when NO present position
        # carries a nonzero weight (the truth-valued reduction), instead of when
        # the arithmetic TOTAL is zero. The two predicates agree on every input
        # whose present weights do not CANCEL, so this rival is correct on the
        # whole all-same-sign domain and diverges only where a cancelling pair of
        # present weights sums to zero — the total is 0 (spec: absent) but some
        # present position is nonzero (rival: `some 0`).
        "module": _impl(
            "    let mask := maskOf da\n"
            "    let s : Int := arithDot mask weights\n"
            "    let out := if anyMasked mask weights = 0 then none else some s\n"
            "    return out"),
        "refinement": "an impl that decided absence by asking whether any "
                      "contributing position carries a weight at all, rather than "
                      "by testing the reduced TOTAL against zero, keeps the "
                      "absent-marking but keys it on presence instead of on the "
                      "sum. A zero total reached by cancellation is exactly as "
                      "unusable for normalizing a weighted mean as a zero total "
                      "reached by absence — it would divide by zero — and the "
                      "regression suite pins exactly that: for fully-present data "
                      "with a sign-mixed weight pair summing to zero, the expected "
                      "sum of weights is the ABSENT marker, not `0`. That case is "
                      "in the protected (must-keep-passing) set, so a real impl "
                      "keyed this way REGRESSES it and does NOT resolve.",
        "rationale": "REJECT from `out = sumOfWeightsSpec da weights` via the "
                     "ZERO-MASK sub-behaviour at its NEAR-MISS point: the spec's "
                     "guard is `arithDot ... = 0` (a property of the TOTAL); the "
                     "rival's is `anyMasked ... = 0` (a property of the presence "
                     "pattern). These agree unless the present weights CANCEL. "
                     "Refuted at da=[some 1, some 1], weights=[1,-1], "
                     "weightsAreLogical=false: both positions are present so "
                     "`anyMasked = 1` and the rival returns `some 0`, but the total "
                     "is 1 + (-1) = 0 so gold returns none. Discrimination comes "
                     "from a SIGN-MIXED `weights` pair summing to zero over present "
                     "data — a point no other rival's input reaches (every other "
                     "witness uses same-sign weights). If it VERIFIES => "
                     "SPEC-TOO-WEAK (the zero-total guard would be satisfiable by "
                     "any predicate agreeing with it on non-cancelling inputs).",
        "witness": _witness("sumOfWeightsTester [some 1, some 1] [1, -1] false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting (revised after an independent audit, which rebuilt
# every witness and its forgery pair, probed the spec with 7 new wrong impls and
# 3 new correct reshapes, and found the admissibility lane EXPRESSIBLE here after
# an earlier draft had recorded it vacuous). The sibling battery has 8 SPEC cases
# (2 soundness positives, 1 admissibility, 2 frame-mutation rivals, 3
# partial-domain rivals) plus a 2-case AXIOM lane. This bundle models the SAME purely-functional core —
# the masked numeric reduction of the weights, with a zero total reported as
# absent — over `List (Option Int)` / `List Int` instead of the sibling's
# List[int]-mask / List[int]-weights carrier with a `dot_reduce` @ContractOnly
# axiom. Two differences drive the port:
#   (a) NO permission surface: the sibling's MANDATORY frame-mutation lane
#       (mask/weights held at Acc(...,1/2)) is VACUOUS here — Lean/Velvet are
#       referentially transparent, no `mut` binder, no heap. The two frame
#       rivals port to NOTHING (not fabricated).
#   (b) EXTRA clause: this spec adds the ZERO-MASK step (`if total = 0 then none`)
#       modeling the `.where(sum != 0)` masking, which the sibling's flat int_dot
#       result did not carry. It gets its own rival (weak-drop-zero-mask), and
#       the PRESENCE mask (`maskOf`) — implicit in the sibling — gets one too
#       (weak-ignore-presence), so no top-level sub-behaviour is unattacked.
#
#   sibling case             -> here                       disposition
#   ----------------------------------------------------------------------------
#   pos-int-dot-direct        -> pos-spec-direct            PORTED (re-aimed)
#   pos-local-reshape         -> pos-arithdot-direct        PORTED (re-aimed)
#   (no sibling)              -> pos-zipwith-sum            ADDED (recursion scheme)
#   admiss-reads              -> admiss-f2p-reachable       PORTED (re-aimed)
#   frame-mut-mask            -> (none)                     VACUOUS (no permission)
#   frame-mut-weights         -> (none)                     VACUOUS (no permission)
#   weak-prepatch             -> weak-logical-collapse      PORTED
#   weak-bool-dot             -> weak-always-logical        PORTED
#   weak-zero                 -> weak-const-zero            PORTED
#   (no sibling)              -> weak-drop-zero-mask        ADDED (ZERO-MASK clause)
#   (no sibling)              -> weak-zero-mask-by-any      ADDED (ZERO-MASK near-miss)
#   (no sibling)              -> weak-ignore-presence       ADDED (PRESENCE clause)
#   AXIOM_TESTS (2)           -> (none)                     DROPPED (G-AX's job)
#
# PORTED (positives): pos-int-dot-direct returned the grounded fold directly —
#   here the grounded model is `sumOfWeightsSpec`, so the direct-return reshape is
#   `return sumOfWeightsSpec da weights`. pos-local-reshape hoisted the reduction
#   to locals with the same `boolean_dot=False` call — here the same numeric leg
#   is `arithDot`, so the reshape computes `arithDot mask weights` directly (the
#   gold routes both carrier tags to that leg). Both verified out-of-band with
#   real builds; each retunes only the elided proof body.
# PORTED (rivals): weak-prepatch (carrier passed straight through -> logical
#   collapse) -> weak-logical-collapse; weak-bool-dot (force the saturating
#   branch) -> weak-always-logical; weak-zero (constant 0) -> weak-const-zero.
#   Each carries a machine-checked witness that ELABORATES against the rival and
#   FAILS against gold (verified with two real builds per case), and its rival
#   MODULE fails to verify under the frozen proof.
# ADDED (weak-drop-zero-mask, weak-ignore-presence): the velvet spec pins two
#   sub-behaviours the sibling's flat-count spec did not model — the zero-total
#   masking to absent and the null-pattern presence mask. Each gets a rival so
#   every top-level structural sub-behaviour of `out = sumOfWeightsSpec ...` is
#   attacked and every non-invariant binder is abused.
# PORTED (admiss-reads -> admiss-f2p-reachable): the sibling's admissibility
#   control re-establishes that the two half-permission Acc clauses admit a normal
#   (mask, weights) pair. This spec has no `require`, so PRECOND-TOO-STRONG cannot
#   arrive here as an unsatisfiable guard — but that does NOT make the lane
#   vacuous, and an earlier draft of this accounting wrongly said it did. The
#   analogue on a total carrier is the obligation being UNSATISFIABLE at exactly
#   an F2P-shaped input (a post-image no computation can hit there), which
#   admiss-f2p-reachable tests directly: it keeps the frozen impl verbatim and
#   discharges the method's own triple at that concrete input BY EVALUATION as a
#   `have`, before closing the frozen obligation byte-identically. Demonstrated
#   expressible with real builds, and demonstrated non-vacuous by two negative
#   controls that FAIL (a wrong post-image reduces to `⊢ False`; a wrong
#   spec-side value is refuted by `decide`).
# VACUOUS (frame-mut-mask, frame-mut-weights): the sibling's #1 weakness class
#   rests on fractional permissions over mutable list carriers. This backend is
#   referentially transparent and declares no `mut` binder — every input is an
#   immutable value with no heap footprint — so there is no read-only field to
#   overwrite and no substitute probe. Not fabricated (porting map: vacuous here).
# DROPPED (AXIOM_TESTS): the reduction callee is modeled as a deep-model
#   A-reference (`reduceDot`, validated == the real callee by G-AX /
#   axiom_check.py), NOT a consumed axiom. meta.json declares no consumed axioms;
#   the axiom lane is G-AX's job and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 6 distinct input points):
#     da                — [some 1, some 1], [some 5, some 3], [some 1], [none],
#                         [none, some 1], [some 1, some 1]: present/absent PATTERN
#                         and length varied (a fully-present pair, a single
#                         present, a single absent, and a mixed present/absent
#                         pair).
#     weights           — [1,1], [2,3], [1], [1], [1,4], [1,-1]: values (incl. > 1
#                         and NEGATIVE, so the sign domain and cancellation are
#                         reached) and length varied.
#     weightsAreLogical — true (weak-logical-collapse), false (the other five): the
#                         carrier tag the post-image is invariant to is exercised
#                         at BOTH values, so the dtype-collapse rival is caught at
#                         the tag=true point where it alone diverges.
#   Every top-level structural sub-behaviour of `out = sumOfWeightsSpec ...` is
#   attacked: COUNT (weak-logical-collapse, weak-always-logical, weak-const-zero),
#   PRESENCE (weak-ignore-presence), ZERO-MASK twice — once by DROPPING the guard
#   (weak-drop-zero-mask, absent data) and once by keying it on the wrong
#   predicate at the cancellation near-miss (weak-zero-mask-by-any, sign-mixed
#   present weights summing to zero). No two rivals share an input tuple.
AXIOM_TESTS = []
