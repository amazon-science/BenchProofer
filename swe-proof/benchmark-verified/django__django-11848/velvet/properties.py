"""properties.py — G-PBT falsification battery for django__django-11848 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct resolveAbbreviatedYear`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method that resolves a two-digit calendar year
``yy`` (0..99) into a full year relative to a reference calendar year ``cur``:

  resolveAbbreviatedYear (yy : Int) (cur : Int) return (out : Int)
    require 0 ≤ yy ∧ yy ≤ 99
    require 0 ≤ cur
    ensures out = resolvedFullYear yy cur                 -- clause 1
    ensures (out - yy) % 100 = 0                          -- clause 2
    ensures cur - 100 < out ∧ out ≤ cur + 50              -- clause 3

``resolvedFullYear`` is a total, fully-unfolded pure function of the method's own
two inputs (the ``axioms`` region declares nothing — no opaque answer key): it is
plain integer arithmetic (``%``, ``+``, ``-`` and one comparison on ``yy`` and
``cur``). It is NOT an ungrounded oracle: an impl that returns
``resolvedFullYear yy cur`` is literally performing the modeled arithmetic, so
there is no wrong echo to build — the cheapest honest positive control returns it
directly.

The load-bearing discriminations, each independently attackable:
  * clause 1 pins the whole reference-relative resolution: the in-century
    candidate ``yy + century`` is pulled back one century exactly when its offset
    from the reference's last two digits STRICTLY exceeds fifty. The whole point
    of the fix is that the threshold is RELATIVE to ``cur``, not a constant
    last-two-digits cutoff. Rivals: the pre-image fixed cutoff, the boundary
    off-by-one (``≥ 50`` / ``> 49``), the dropped-rollback.
  * clause 2 pins the last-two-digits invariant (the result differs from ``yy``
    by a whole number of centuries). A rival that adds the reference year's own
    last two digits into the base breaks it. Rival: the century-not-cleared.
  * clause 3 pins the recency window ``(cur - 100, cur + 50]``, and it is a
    CONJUNCTION whose two halves fail independently. A rival that never rolls
    back a more-than-fifty-ahead candidate exceeds the ``cur + 50`` bound
    (rival: the dropped-rollback); a rival that rolls back too FAR undershoots
    the ``cur - 100 <`` bound while still satisfying clause 2, since a
    whole-century overshoot preserves the last two digits (rival: the
    overshoot-200). Both halves are separately attacked.

The TWO input binders ``yy`` and ``cur`` are both free and the post-image must
hold for every value of each; the reject witnesses below vary both (footer
coverage table): ``yy`` over {5, 69, 70, 94, 99}, ``cur`` over {2019, 2020,
2048, 2150}. In particular the reference year is genuinely varied — a rival that
mishandled only ``cur`` (which is exactly what the pre-image did) is refuted at
four distinct reference years, and crucially at reference years in TWO DIFFERENT
CENTURIES (2xxx and 21xx): a rival that hardcodes the century constant rather
than deriving it from ``cur`` agrees with the spec at every reference year in
the 2000s, so it is refuted only by a point outside that century.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; footer accounts for
each case):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. Both inputs are bare
    scalar ``Int`` values, there is no read-only object/pointer input and no
    fractional-permission surface. Neither parameter is ``mut``; there is no heap
    and no aliasing. There is nothing to overwrite and no permission system to
    trip, so the class is vacuous. No substitute is fabricated (per the porting
    map). This exactly matches the sibling's own note ("there is NO read-only
    object/pointer input … the FRAME-MUTATION class does not apply here").
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
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``resolvedFullYear`` of the method's own inputs, a concrete
    ``def`` in the ``pure`` region grounded entirely in ``yy``/``cur``. There is
    no value an echo could carry that satisfies the ensures yet is behaviourally
    wrong.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. The resolution has sub-domains a
    rival can get right on most inputs yet diverge on one: the boundary input
    ``yy - cur%100 == 50`` (off-by-one family), the more-than-fifty-ahead
    subdomain (dropped rollback), and the century-base computation (clause 2).

WITNESS MECHANICS on this carrier. The spec is a ``method`` CONTRACT, not a bare
predicate, so a witness reaches it through Velvet's tester machinery:
``resolveAbbreviatedYearTester yy cur = false`` says the precondition holds at
``(yy, cur)`` AND the extracted program's result violates the postcondition
there. Each reject witness states this at a concrete in-precondition point
(``0 ≤ yy ≤ 99``, ``0 ≤ cur``) where ``decide`` settles the arithmetic (measured:
``decide`` computes this ``Int`` arithmetic directly). Both halves were checked
out-of-band with ``scripts/lean_verify.sh`` for every reject case: the witness
ELABORATES against its rival (the rival provably violates the spec there) and
FAILS against the frozen solution (gold satisfies the spec at that input, so the
witness is a real discriminator, not a tautology). No ``sorry`` / ``admit`` /
``native_decide`` / ``axiom``, and no conditioning binders (every witness is at
literal inputs, so there are no assumptions to be inconsistent).

AXIOM lane: EMPTY. ``meta.json`` / ``mapping.md`` declare no consumed ``axiom``
and no A-reference deep model (the resolution is modeled deeply in the ``pure``
region; the reference year is a free input about which nothing is assumed beyond
``0 ≤ cur``). The nagini sibling's ``AXIOM_TESTS`` (an A-reference validation of
``resolved_year`` == the real patch arithmetic) belong to the G-AX lane, which
this bundle skips (no ``axiom_check.py``); this gate ignores ``AXIOM_TESTS``
regardless. Dropped — footer.
"""
from pathlib import Path

INSTANCE = "django__django-11848"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole executable body (compute cc / century, then
# ---- branch on the reference-relative threshold). Lies wholly inside the one
# ---- impl region and is unique in Solution.lean; both facts are asserted by
# ---- _swap. Every variant replaces this block, so any drift of the frozen impl
# ---- breaks the manifest loudly. ----
_GOLD_IMPL = """    -- impl-start
    let cc := cur % 100
    let century := cur - cc
    let out := if yy - cc > 50 then yy + century - 100 else yy + century
    return out
    -- impl-end"""

assert _BASE.count(_GOLD_IMPL) == 1, "method impl region drifted from expected text"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a correct reshape may retune its script without
# ---- touching the spec or dropping the obligation. Reject rivals leave it
# ---- as-is (their rejection is carried by the witness, not the tactic script).
_GOLD_PROOF = """prove_correct resolveAbbreviatedYear by
  loom_solve
  all_goals simp only [resolvedFullYear]"""

assert _BASE.count(_GOLD_PROOF) == 1, "proof region drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _impl_reproved(body, proof):
    """Impl body replaced AND the proof retuned (for correct reshapes / asserts)."""
    return _swap(_impl(body), _GOLD_PROOF, proof)


# A retuned proof that also closes the reshaped `if`/arithmetic goals a correct
# variant emits (`split <;> omega` after unfolding the pure model). Kept close to
# the frozen script (`loom_solve` + unfold) — no new lemma, no induction.
_RESHAPE_PROOF = """prove_correct resolveAbbreviatedYear by
  loom_solve
  all_goals simp only [resolvedFullYear]
  all_goals (split <;> omega)"""

# A retuned proof that additionally discharges an in-region admissibility assert
# by `decide` on its concrete arithmetic goal.
_ASSERT_PROOF = """prove_correct resolveAbbreviatedYear by
  loom_solve
  all_goals simp only [resolvedFullYear]
  all_goals decide"""


# ---- witness preamble. The spec is a `method` CONTRACT, so a witness reaches it
# ---- through Velvet's tester machinery: `resolveAbbreviatedYearTester yy cur =
# ---- false` says the precondition holds and the extracted program's result
# ---- violates the postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script can mask the
# ---- verdict. ----
_TESTER = ("extract_program_for resolveAbbreviatedYear\n"
           "prove_precondition_decidable_for resolveAbbreviatedYear\n"
           "prove_postcondition_decidable_for resolveAbbreviatedYear\n"
           "derive_tester_for resolveAbbreviatedYear\n\n")


def _witness(yy, cur):
    return _TESTER + (f"example : resolveAbbreviatedYearTester {yy} {cur} = false "
                      ":= by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the identical obligation statement;
    # only the executable surface and the tactic script move.
    # =====================================================================
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest grounded impl: return the deep model directly. Since
        # `resolvedFullYear` is fully unfolded in the two Int args, this IS the
        # modeled arithmetic (no opaque oracle to echo). Clause 1 holds
        # definitionally; clauses 2/3 need the unfold + `split <;> omega`.
        "module": _impl_reproved(
            "    let out := resolvedFullYear yy cur\n"
            "    return out",
            _RESHAPE_PROOF),
        "rationale": "returning the modeled resolution directly satisfies clause 1 "
                     "(`out = resolvedFullYear yy cur`) definitionally; clauses 2/3 "
                     "discharge after unfolding the pure model. A grounded correct "
                     "impl MUST verify, else the postcondition is unsatisfiable "
                     "(SPEC-TOO-STRONG). Proof retuned (`split <;> omega` after the "
                     "frozen unfold) since the loop-free body needs the arithmetic "
                     "goals closed; no new lemma, no induction.",
    },
    {
        "id": "pos-reshaped",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but CORRECT: test the SAME-CENTURY case first via
        # a negated guard (`≤ 50`, else-first), computing the identical arithmetic.
        # Reordered control flow, same values.
        "module": _impl_reproved(
            "    let cc := cur % 100\n"
            "    let century := cur - cc\n"
            "    let out := if yy - cc ≤ 50 then yy + century else yy + century - 100\n"
            "    return out",
            _RESHAPE_PROOF),
        "rationale": "a correct impl with the branch reordered (negated guard "
                     "`≤ 50`, else-first) computes the SAME value on every input, "
                     "so all three clauses discharge after the frozen unfold plus "
                     "`split <;> omega`. If a faithful reshape could not verify the "
                     "spec would be SPEC-TOO-STRONG on the exact branch form. No "
                     "loop / induction lemma needed.",
    },

    # =====================================================================
    # ADMISSIBILITY. The precondition (0 ≤ yy ≤ 99, 0 ≤ cur) must admit the
    # F2P-shaped inputs AND the post-image must be non-degenerate there. One
    # in-region assert pins that `resolvedFullYear` produces exactly the value
    # each F2P matrix row demands on a legitimate in-domain input — including
    # BOTH branches of the >50 rule (roll-forward and roll-back). The impl is
    # kept verbatim so the method's own obligation still discharges; the proof
    # is retuned only to clear the extra `assert` goal (`decide`), which is
    # elided from the spec view. The assert is LIVE (a false claim leaves an
    # unsolved `decide` goal — verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (resolvedFullYear 69 2019 = 2069 ∧\n"
            "       resolvedFullYear 70 2020 = 2070 ∧\n"
            "       resolvedFullYear 99 2048 = 1999 ∧\n"
            "       resolvedFullYear 70 2019 = 1970))\n"
            "    let cc := cur % 100\n"
            "    let century := cur - cc\n"
            "    let out := if yy - cc > 50 then yy + century - 100 else yy + century\n"
            "    return out",
            _ASSERT_PROOF),
        "rationale": "the precondition admits the F2P-shaped inputs (a two-digit "
                     "year in 0..99, a four-digit reference year) and the resolution "
                     "is non-degenerate there: it produces exactly the value each "
                     "F2P matrix row pins, exercising BOTH branches — roll-forward "
                     "(69/2019→2069, 70/2020→2070) and roll-back (99/2048→1999, "
                     "70/2019→1970). The in-region assert must discharge (else the "
                     "domain would be vacuous / the resolution constant → "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so the "
                     "method's own ensures discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete in-precondition input and the refinement argument that its
    # faithful real counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-prepatch-fixed-cutoff",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image (buggy) skeleton: a FIXED cutoff at 70 that ignores the
        # reference year entirely (0..69 → 2000s, 70..99 → 1900s). This is exactly
        # the behaviour the gold patch removes.
        "module": _impl(
            "    let out := if yy < 70 then yy + 2000 else yy + 1900\n"
            "    return out"),
        "refinement": "this IS the reverted pre-image decision: a constant "
                      "last-two-digits cutoff at 70, independent of the reference "
                      "year. Its faithful real counterpart is the unpatched code, "
                      "which the F2P tests fail. Decisive break: at reference year "
                      "2020 a two-digit year 70 must resolve to 2070 (the F2P "
                      "matrix pins it), but the fixed cutoff sends 70 to 1970. So "
                      "its faithful patch does NOT resolve test_parsing_rfc850.",
        "rationale": "REJECT from clause 1 (`out = resolvedFullYear yy cur`): for "
                     "any reference year whose last two digits differ enough from "
                     "the cutoff, the constant rule disagrees with the "
                     "reference-relative resolution. At (yy=70, cur=2020) the spec "
                     "gives 2070 but the rival gives 1970. Verifying would be "
                     "SPEC-TOO-WEAK. Witness moves cur to 2020.",
        "witness": _witness(70, 2020),
    },
    {
        "id": "weak-boundary-ge50",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one at the rollback THRESHOLD: `≥ 50` instead of `> 50`. Correct
        # everywhere except the exact boundary input `yy - cur%100 == 50`, where
        # it wrongly rolls back a century.
        "module": _impl(
            "    let cc := cur % 100\n"
            "    let century := cur - cc\n"
            "    let out := if yy - cc ≥ 50 then yy + century - 100 else yy + century\n"
            "    return out"),
        "refinement": "diverges only at `yy - cur%100 == 50`. The F2P matrix at "
                      "reference year 2019 pins a two-digit year 69 (69 - 19 == 50) "
                      "to 2069: gold keeps the reference century (2069), this rival "
                      "rolls back to 1969. So its faithful real patch fails "
                      "test_parsing_rfc850 and does NOT resolve.",
        "rationale": "REJECT from clause 1 at the boundary `yy - cur%100 == 50`: "
                     "the spec uses a STRICT `> 50` and keeps the reference century, "
                     "but the rival rolls back, giving a result 100 less than "
                     "`resolvedFullYear`. Witness at (yy=69, cur=2019).",
        "witness": _witness(69, 2019),
    },
    {
        "id": "weak-threshold-49",
        "kind": "uniqueness",
        "expect": "reject",
        # SUPPORTING near-miss from the threshold family: `> 49` (rolls back one
        # input too early). Observationally identical to the `≥ 50` rival on
        # integers, reached from the other side of the comparison; diverges at the
        # same boundary `yy - cur%100 == 50`.
        "module": _impl(
            "    let cc := cur % 100\n"
            "    let century := cur - cc\n"
            "    let out := if yy - cc > 49 then yy + century - 100 else yy + century\n"
            "    return out"),
        "refinement": "identical observable effect to weak-boundary-ge50 (`> 49` "
                      "≡ `≥ 50` on integers): rolls back at `yy - cur%100 == 50`. "
                      "Faithful patch fails the same F2P case (reference year 2019, "
                      "two-digit year 69 → gold 2069, rival 1969); does NOT resolve. "
                      "A cheap supporting case for the threshold family.",
        "rationale": "REJECT from clause 1 at the boundary input "
                     "`yy - cur%100 == 50`, same as weak-boundary-ge50. Witness at "
                     "(yy=69, cur=2019).",
        "witness": _witness(69, 2019),
    },
    {
        "id": "weak-no-rollback",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the future-rollback rule entirely: always stays in the reference
        # century. Correct on the near half of the domain but wrong on every input
        # more than fifty years ahead.
        "module": _impl(
            "    let cc := cur % 100\n"
            "    let century := cur - cc\n"
            "    let out := yy + century\n"
            "    return out"),
        "refinement": "never rolls back. The F2P matrix at reference year 2019 "
                      "pins a two-digit year 70 (70 - 19 == 51 > 50) to 1970: gold "
                      "rolls back to 1970, this rival gives 2070. Its faithful real "
                      "patch fails test_parsing_rfc850 and does NOT resolve.",
        "rationale": "REJECT from clause 1 on the more-than-fifty-ahead subdomain "
                     "AND clause 3 (`out ≤ cur + 50`): for `yy - cur%100 > 50` the "
                     "spec subtracts 100 but this impl does not, so the result is "
                     "100 too large and exceeds the `cur + 50` bound (2070 > 2069). "
                     "Witness at (yy=70, cur=2019).",
        "witness": _witness(70, 2019),
    },
    {
        "id": "weak-century-noclear",
        "kind": "uniqueness",
        "expect": "reject",
        # Mis-computes the century start: uses the reference year ITSELF as the
        # base instead of the reference year with its last two digits cleared.
        # The last-two-digits clause then fails for most inputs.
        "module": _impl(
            "    let century := cur\n"
            "    let out := if yy - (cur % 100) > 50 then yy + century - 100 else yy + century\n"
            "    return out"),
        "refinement": "uses the reference year (not its century start) as the base, "
                      "so the result carries the reference year's own last two "
                      "digits added in. At reference year 2019, a two-digit year 94 "
                      "(94 - 19 == 75 > 50, the roll-back branch) must resolve to "
                      "1994 (the F2P matrix pins it), but this rival gives "
                      "94 + 2019 - 100 = 2013. Faithful patch fails "
                      "test_parsing_rfc850; does NOT resolve.",
        "rationale": "REJECT from clause 2 (`(out - yy) % 100 = 0`): adding the "
                     "full reference year instead of its century start makes the "
                     "last two digits wrong whenever `cur % 100 ≠ 0` "
                     "((2013 - 94) % 100 = 19 ≠ 0), and clause 1 also fails. "
                     "Witness at (yy=94, cur=2019).",
        "witness": _witness(94, 2019),
    },
    {
        # ADDED BY AUDIT (a6). The five ported rivals all move `cur` inside a
        # SINGLE century (2019/2020), so none of them discriminates the century
        # base from the constant 2000: this rival agrees with the spec at every
        # reference year in the 2000s and was measured to survive all four
        # pre-existing witness points (each exits 1 against it). It closes the
        # `cur`-binder gap the coverage table previously overstated.
        "id": "weak-century-hardcoded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let cc := cur % 100\n"
            "    let century := 2000\n"
            "    let out := if yy - cc > 50 then yy + century - 100 else yy + century\n"
            "    return out"),
        "refinement": "takes the century base as the CONSTANT 2000 instead of "
                      "deriving it from the reference year, keeping the correct "
                      "reference-relative threshold. Its faithful real counterpart "
                      "resolves every abbreviated year into the 1900s/2000s no "
                      "matter how far the reference year has moved, which is the "
                      "same class of defect as the pre-image: a constant baked in "
                      "where the reference year belongs. It happens to agree with "
                      "the spec on every reference year in the 2000s, so it passes "
                      "the F2P matrix rows as written and is caught only off that "
                      "century — which is precisely why the battery needs a "
                      "reference year outside it.",
        "rationale": "REJECT from clause 1 (`out = resolvedFullYear yy cur`) and "
                     "clause 3 (`cur - 100 < out`): at (yy=5, cur=2150) the "
                     "spec's century base is 2100, giving 2105, but the constant "
                     "base gives 2005 — 145 years below the reference, outside the "
                     "recency window. Witness moves `cur` into a different century "
                     "(2150), the one axis every other rival leaves fixed.",
        "witness": _witness(5, 2150),
    },
    {
        # ADDED BY AUDIT (a6). Clause 3 is a conjunction and only its UPPER half
        # (`out ≤ cur + 50`, via weak-no-rollback) was attacked. A whole-century
        # overshoot leaves clause 2 intact — `(1899 - 99) % 100 = 0` holds — so
        # this rival isolates the LOWER half `cur - 100 < out`, which no ported
        # case reached.
        "id": "weak-rollback-overshoot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let cc := cur % 100\n"
            "    let century := cur - cc\n"
            "    let out := if yy - cc > 50 then yy + century - 200 else yy + century\n"
            "    return out"),
        "refinement": "rolls back TWO centuries instead of one on exactly the "
                      "more-than-fifty-ahead subdomain, so it reads such a "
                      "timestamp as a full century older than the resolution "
                      "demands. The F2P matrix pins a two-digit year 99 at "
                      "reference year 2048 to 1999 (99 - 48 == 51 > 50, the "
                      "roll-back branch), but this rival gives 1899. Its faithful "
                      "real patch fails that row and does NOT resolve.",
        "rationale": "REJECT from clause 1 and from the LOWER half of clause 3 "
                     "(`cur - 100 < out`): at (yy=99, cur=2048) the rival returns "
                     "1899, which is 149 years before the reference and so below "
                     "the window floor. Note clause 2 SURVIVES this rival "
                     "((1899 - 99) % 100 = 0 — a whole-century overshoot keeps the "
                     "last two digits), so the case genuinely isolates clause 3's "
                     "lower bound rather than re-testing the digits invariant. "
                     "Witness at (yy=99, cur=2048).",
        "witness": _witness(99, 2048),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness — no frame-mutation case, no
# divergence case) plus a 2-case AXIOM lane. This bundle models the SAME exact
# integer resolution (`resolvedFullYear` ≡ the sibling's @Pure `resolved_year`)
# over the SAME two scalar `Int` inputs (`yy`/`cur` ≡ `two_digit_year`/
# `reference_year`), with the same three postcondition clauses. The carrier is a
# 1:1 narrowing — no widening — so every sibling SPEC case has a direct
# counterpart and all are ported.
#
#   sibling case                   -> here                              disposition
#   -----------------------------------------------------------------------------
#   pos-cheapest                   -> pos-cheapest                      PORTED
#   pos-reshaped                   -> pos-reshaped                      PORTED (reshaped + reproved)
#   admiss-f2p-shape               -> admiss-f2p-shape                  PORTED (in-region assert)
#   weak-prepatch-fixed-cutoff     -> weak-prepatch-fixed-cutoff        PORTED (+ witness)
#   weak-boundary-ge50             -> weak-boundary-ge50                PORTED (+ witness)
#   weak-threshold-49              -> weak-threshold-49                 PORTED (+ witness)
#   weak-no-rollback               -> weak-no-rollback                  PORTED (+ witness)
#   weak-century-noclear           -> weak-century-noclear              PORTED (+ witness)
#   (none)                         -> weak-century-hardcoded            ADDED BY AUDIT (a6)
#   (none)                         -> weak-rollback-overshoot           ADDED BY AUDIT (a6)
#   (frame-mutation)               -> (none)                            VACUOUS (no such sibling case; scalar inputs)
#   (divergence)                   -> (none)                            N/A (no such sibling case; total arithmetic)
#   AX-* (2 cases)                 -> (none)                            DROPPED (G-AX lane)
#
# 8 ported (2 soundness + 1 admissibility + 5 uniqueness); 2 ADDED by audit, for
# 10 cases total. Both added rivals were measured with the real verifier before
# landing (rival build fails; witness elaborates against the rival and fails on
# the frozen solution; the flipped-claim forgery of the same witness BUILDS
# against the frozen solution, so the gold-side exit code tracks the claim):
#   * weak-century-hardcoded — the five ported rivals move `cur` only WITHIN one
#     century (2019/2020), so a rival taking the century base as the constant
#     2000 agrees with the spec at every witnessed point. Measured: it survives
#     all four pre-existing witness points (each exits 1 against it, i.e. none of
#     them refutes it) and is refuted only at a reference year in another century.
#   * weak-rollback-overshoot — clause 3 is a conjunction and only its UPPER half
#     (`out ≤ cur + 50`) was attacked. A two-century roll-back undershoots the
#     LOWER half (`cur - 100 < out`) while leaving clause 2 intact, so it
#     isolates a clause half no ported case reached.
#
# VACUOUS (frame-mutation): the sibling explicitly records that this class does
#   NOT apply — both inputs are bare scalar ints, there is no read-only
#   object/pointer input and no fractional permission to trip. On this backend the
#   same holds structurally: every parameter is an immutable value, the method
#   declares no `mut` binder, there is no heap and no aliasing. No substitute
#   fabricated.
# N/A (divergence): the sibling ships NO diverge-*/nonterm-*/weak-diverge case
#   (the operation is exact, total integer arithmetic), so there is no divergence
#   lane to port — neither a reject case (none exists) nor a known-hole note (the
#   sibling flags no hole). This is distinct from a partial-semantics bundle whose
#   sibling DOES carry a divergence case: here there is simply nothing in the
#   design document to carry over.
# DROPPED (AXIOM_TESTS): the sibling's two-case axiom lane validates its
#   A-reference deep model (`resolved_year` == the real patch arithmetic). This
#   bundle declares NO consumed axiom and NO A-reference (mapping.md §3: the
#   resolution is modeled deeply; the reference year is a free input, not an
#   axiomatized callee), ships no `axiom_check.py`, and G-AX is skip. The axiom
#   lane is G-AX's job and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the TWO input binders of
#   the postcondition (pts = 6 distinct input points: (70,2020), (69,2019),
#   (70,2019), (94,2019), (5,2150), (99,2048)):
#     yy   — 5 (hardcoded), 69 (ge50, gt49), 70 (prepatch, no-rollback),
#            94 (noclear), 99 (overshoot): varied across the boundary, the
#            just-past-boundary, a deep roll-back and both domain ends.
#     cur  — 2019 (ge50, gt49, no-rollback, noclear), 2020 (prepatch),
#            2048 (overshoot), 2150 (hardcoded): varied, and varied ACROSS
#            CENTURIES, which is the part that carries weight. Moving `cur` only
#            2019→2020 leaves the century base unprobed: a rival that hardcodes
#            it as the constant 2000 was MEASURED to survive all four
#            single-century witness points and is refuted only at 2150. So the
#            battery now demonstrates the spec's dependence on the whole of
#            `cur`, not merely on its last two digits.
#   Every independent top-level clause — and both halves of the one conjunction —
#   is attacked:
#     clause 1 (out = resolvedFullYear)      — all seven rivals.
#     clause 2 ((out - yy) % 100 = 0)        — weak-century-noclear (last two
#                                              digits wrong: (2013-94)%100 = 19).
#     clause 3 upper (out ≤ cur + 50)        — weak-no-rollback (2070 > 2069).
#     clause 3 lower (cur - 100 < out)       — weak-rollback-overshoot (1899 is
#                                              149 below the reference 2048; note
#                                              clause 2 SURVIVES there, since
#                                              (1899-99)%100 = 0, so the case
#                                              isolates this half rather than
#                                              re-testing the digits invariant).
#   weak-threshold-49 shares its witness (69,2019) with weak-boundary-ge50
#   because the two rivals are observationally IDENTICAL on integers (`> 49` ≡
#   `≥ 50`) and fail at the same boundary input for the same reason (the sibling
#   ships both as a threshold-family pair); it is a genuine syntactic near-miss,
#   not a distinct sub-domain, so no more-discriminating input exists to move it
#   to.
AXIOM_TESTS = []
