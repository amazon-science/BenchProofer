"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-22719 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
each ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. TWO independent contracted queries, each over one read-only
collection of per-element classification results (``List Bool``), each deciding
whether a one-time advisory notice is emitted:

  numericNoticeFires      (numlikeFlags : List Bool)
      ensures out = noticeFires numlikeFlags                               (C1)
  numericLabelNoticeFires (parsableFlags : List Bool)
      ensures out = noticeFires parsableFlags                              (C2)

``noticeFires`` (a concrete ``def`` in the ``pure`` region; the ``axioms`` region
declares nothing) is fully transparent and grounded in its sole input binder:

  noticeFires flags = (!flags.isEmpty && allTrue flags)

It folds TWO independent facets, each a distinct sub-domain a rival can get
wrong:

  * the NON-EMPTINESS guard ``!flags.isEmpty`` — the load-bearing conjunct: the
    notice must be WITHHELD on an empty collection even though the aggregate is
    vacuously affirmative there (``allTrue [] = true``). This is the crux of the
    fix; the discriminating sub-domain is the EMPTY collection.
  * the AGGREGATE ``allTrue flags`` — the notice fires only when EVERY element
    classifies affirmatively; a single non-affirmative element withholds it.

Both binders are read-only (neither is declared ``mut``), and the reject
witnesses vary the sole binder of each query across the empty collection ``[]``,
a single-element non-affirmative collection ``[false]``, and a mixed
affirmative/non-affirmative collection ``[true, false]``.

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    holds ``flags`` at a fractional heap permission (``Acc(list_pred(flags),
    1/2)``) and its MANDATORY frame rival overwrites that read-only input to trip
    INSUFFICIENT PERMISSION. Lean and Velvet are referentially transparent:
    ``numlikeFlags`` / ``parsableFlags`` are immutable values, this bundle
    declares NO ``mut`` parameter, and there is no heap, no aliasing, and no
    permission system to trip. There is no read-only input to overwrite and no
    substitute probe to fabricate, so the class is vacuous (per the porting map,
    legitimately dropped, not faked). Its ARGUMENT (a real patch mutating the
    caller's value array would corrupt downstream data) has no value footprint
    the spec can force here — each query returns a fresh ``Bool`` and mutates
    nothing by construction.
  * UNGROUNDED-ORACLE ECHO — N/A. C1/C2 are total functions of their sole input
    binder (``noticeFires`` is a concrete ``def``, not an axiomatized oracle);
    there is no opaque answer key a wrong impl could echo. The cheapest correct
    impl returns ``noticeFires flags`` directly, which the positive controls
    cover honestly.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: the
    pre-patch defect (dropping the non-emptiness guard, so the notice fires on
    empty input where ``allTrue [] = true``) plus a guard-only rival, a
    constant-true rival, and the same guard-drop on the second site. Each is
    correct on part of the domain and wrong on the interesting sub-domain, and
    each is refuted at a distinct concrete point.

WITNESS MECHANICS on this carrier. The spec here is a ``method`` CONTRACT, not a
bare predicate, so a witness reaches it through Velvet's own tester machinery:
``numericNoticeFiresTester <flags> = false`` says the extracted program's result
violates the method's postcondition at that concrete input. It is checked in a
file whose ``prove_correct`` blocks have been stripped, so no tactic script can
mask the verdict. Neither query has a ``require`` clause, so the precondition is
``True`` and decides trivially, and the whole carrier is decidable (``List Bool``
→ ``Bool``), so each tester ``decide``s at a concrete literal. No ``sorry`` /
``admit`` / ``native_decide`` / ``axiom``. Every witness binds only concrete
literals with NO hypotheses, so the consistency probe is trivially satisfiable
(no opaque-term conditioning is needed — the carrier is fully transparent).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-22719"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each is the gold return expression of one query; it
# ---- lies wholly inside that query's single `-- impl-start`/`-- impl-end`
# ---- region and is unique in Solution.lean (both facts asserted at load). ----
_RET_A = "    return !numlikeFlags.isEmpty && allTrue numlikeFlags"
_RET_B = "    return !parsableFlags.isEmpty && allTrue parsableFlags"
assert _BASE.count(_RET_A) == 1, "site-A impl anchor drifted"
assert _BASE.count(_RET_B) == 1, "site-B impl anchor drifted"


# ---- witness preambles. Reach each method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` blocks are stripped. ----
_TESTER_A = (
    "extract_program_for numericNoticeFires\n"
    "prove_precondition_decidable_for numericNoticeFires\n"
    "prove_postcondition_decidable_for numericNoticeFires\n"
    "derive_tester_for numericNoticeFires\n\n"
)
_TESTER_B = (
    "extract_program_for numericLabelNoticeFires\n"
    "prove_precondition_decidable_for numericLabelNoticeFires\n"
    "prove_postcondition_decidable_for numericLabelNoticeFires\n"
    "derive_tester_for numericLabelNoticeFires\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # ADMISSIBILITY (expect=verify). Neither query has a `require` clause, so
    # the nagini "the half-permission precondition admits a normal F2P-shaped
    # input" probe is vacuous on the total domain — nothing could exclude any
    # input. Re-aimed at the residual admissibility risk on a total domain: that
    # the post-image is DEGENERATE (e.g. constant) so no rival could be
    # distinguished. This case discharges an in-region `assert`, at the three
    # F2P-shaped points, that the emission decision genuinely VARIES with the
    # input — a non-empty all-affirmative collection emits (true), the empty
    # collection withholds (false, the crux edge), and a mixed collection
    # withholds (false). The gold return is kept verbatim so C1 still discharges;
    # the assert is live (a false claim leaves an unsolved goal — confirmed
    # empirically) and is discharged by the frozen proof's `loom_solve`.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _RET_A,
            "    assert (with_name_prefix `adm\n"
            "      (noticeFires ([true, true] : List Bool) = true ∧\n"
            "       noticeFires ([] : List Bool) = false ∧\n"
            "       noticeFires ([true, false] : List Bool) = false))\n"
            + _RET_A),
        "rationale": "the post-image is non-degenerate: the emission decision "
                     "genuinely varies with the input (a non-empty all-affirmative "
                     "collection emits, the empty collection withholds — the crux "
                     "edge — and a mixed collection withholds), so the spec actually "
                     "constrains the result rather than admitting a constant. The "
                     "in-region assert must discharge (else the modeled behavior "
                     "would be degenerate); the gold return is kept verbatim so C1 "
                     "still discharges too. If it cannot verify, PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. One control per site (cross-site coverage), mirroring the
    # nagini pos-reorder-f1 / pos-reorder-f2 pair.
    # =====================================================================
    {
        "id": "pos-commute-f1",
        "kind": "soundness",
        "expect": "verify",
        # Reshape site A: commute the two conjuncts of the emission decision
        # (`allTrue && !isEmpty`). Observationally identical (`&&` is commutative),
        # so C1 still holds and the frozen `loom_solve` discharges it.
        "module": _swap(
            _BASE, _RET_A,
            "    return allTrue numlikeFlags && !numlikeFlags.isEmpty"),
        "rationale": "commuting the emission decision's two conjuncts computes the "
                     "identical boolean, so `out = noticeFires numlikeFlags` still "
                     "discharges. Must verify, else the spec is over-fit to the "
                     "conjunct ORDER => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-ite-f2",
        "kind": "soundness",
        "expect": "verify",
        # Reshape site B: spell the emission decision as an explicit branch on
        # emptiness (empty -> withhold; non-empty -> the aggregate) instead of the
        # guard conjunction. Same behaviour, so C2 still discharges. Cross-site
        # soundness control.
        "module": _swap(
            _BASE, _RET_B,
            "    return (if parsableFlags.isEmpty then false else allTrue parsableFlags)"),
        "rationale": "an explicit empty/non-empty branch computes the identical "
                     "emission decision (empty -> withhold; non-empty -> the "
                     "affirmative aggregate), so `out = noticeFires parsableFlags` "
                     "still discharges. Independently correct, must verify "
                     "(cross-site soundness control).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each keeping the frozen `prove_correct` block (which
    # no longer closes for the reshaped impl) and carrying a machine-checked
    # refutation witness at a DISTINCT concrete input plus the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-drop-guard-f1",
        "kind": "uniqueness",
        "expect": "reject",
        # THE regressed shape at site A: drop the non-emptiness guard and emit on
        # the affirmative aggregate alone. Correct on any non-empty collection;
        # wrong on the empty collection, where the aggregate is vacuously
        # affirmative but the notice must be withheld.
        "module": _swap(_BASE, _RET_A, "    return allTrue numlikeFlags"),
        "refinement": "this is the pre-change behavior: emit whenever the aggregate "
                      "is affirmative, ignoring collection size. On an EMPTY "
                      "collection the aggregate is vacuously affirmative, so the "
                      "advisory fires on empty input — exactly the confusing "
                      "deprecation warning the issue reports (the empty-data smoke "
                      "test asserts NO advisory is emitted). It would NOT resolve.",
        "rationale": "REJECT from C1 (`out = noticeFires numlikeFlags`): dropping "
                     "the `!isEmpty` guard makes the impl return `allTrue`, which on "
                     "the empty collection is `true` where the post-image demands "
                     "`false`. Refuted at `numlikeFlags = []` — the crux empty edge "
                     "of the fix.",
        "witness": _TESTER_A +
                   "example : numericNoticeFiresTester [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-drop-guard-f2",
        "kind": "uniqueness",
        "expect": "reject",
        # Same guard-drop on site B (cross-site witness for the second query):
        # emit on the affirmative aggregate alone, so the advisory fires on empty
        # input where it must be withheld.
        "module": _swap(_BASE, _RET_B, "    return allTrue parsableFlags"),
        "refinement": "the pre-change behavior at the second site: emit whenever "
                      "every label is convertible, ignoring collection size. On an "
                      "EMPTY collection the aggregate is vacuously affirmative, so "
                      "the info advisory fires on empty input — the same "
                      "empty-data defect the fix removes. It would NOT resolve.",
        "rationale": "REJECT from C2 (`out = noticeFires parsableFlags`): dropping "
                     "the `!isEmpty` guard makes the impl return `allTrue`, which on "
                     "the empty collection is `true` where the post-image demands "
                     "`false`. Refuted at `parsableFlags = []` (site-B empty edge).",
        "witness": _TESTER_B +
                   "example : numericLabelNoticeFiresTester [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-guard-only-f2",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the AGGREGATE conjunct at site B: emit on non-emptiness alone,
        # ignoring whether the labels are convertible. Correct on the empty
        # collection; wrong on any non-empty collection with a non-convertible
        # label. Varies the site-B binder away from the empty-only witness.
        "module": _swap(_BASE, _RET_B, "    return !parsableFlags.isEmpty"),
        "refinement": "a counterpart that emits on any non-empty collection, "
                      "ignoring whether the labels are all parsable, would log the "
                      "all-parsable advisory for genuine string labels (where the "
                      "per-label test is False) — changing the update routine's "
                      "logging behaviour on non-convertible input. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C2 (`out = noticeFires parsableFlags`): dropping "
                     "the `allTrue` conjunct makes the impl return `!isEmpty`, which "
                     "on a non-empty non-affirmative collection is `true` where the "
                     "post-image demands `false`. Refuted at `parsableFlags = "
                     "[false]` — a non-affirmative element, moving the site-B binder "
                     "off the empty-only point.",
        "witness": _TESTER_B +
                   "example : numericLabelNoticeFiresTester [false] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-guard-only-f1",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the AGGREGATE conjunct instead: emit on non-emptiness alone,
        # ignoring the per-element classification. Correct on the empty collection
        # (and on an all-affirmative non-empty one); wrong on any non-empty
        # collection with a non-affirmative element.
        "module": _swap(_BASE, _RET_A, "    return !numlikeFlags.isEmpty"),
        "refinement": "a counterpart that emits on any non-empty collection, "
                      "ignoring whether the elements classify affirmatively, would "
                      "fire the numeric-passthrough advisory for genuine string "
                      "categories (where the per-element test is False) — changing "
                      "the converter's warning behaviour and breaking the "
                      "string-category convert P2P tests. It would NOT resolve.",
        "rationale": "REJECT from C1: dropping the `allTrue` conjunct makes the impl "
                     "return `!isEmpty`, which on a non-empty non-affirmative "
                     "collection is `true` where the post-image demands `false`. "
                     "Refuted at `numlikeFlags = [false]` — a single non-affirmative "
                     "element, the aggregate facet no guard-drop rival attacks.",
        "witness": _TESTER_A +
                   "example : numericNoticeFiresTester [false] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-const-true-f1",
        "kind": "uniqueness",
        "expect": "reject",
        # Cheapest wrong impl: ignore the input entirely, always emit. Diverges on
        # BOTH the empty collection and any non-affirmative collection. Supporting
        # case; refuted at a mixed collection distinct from the other points.
        "module": _swap(_BASE, _RET_A, "    return true"),
        "refinement": "unconditionally emitting the advisory (even on empty input "
                      "and on string categories) fires it on empty data and on "
                      "genuine string categories, failing both the empty-data smoke "
                      "test and the non-numeric convert P2P tests. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C1: a constant `true` violates the post-image "
                     "wherever `noticeFires` is `false`. Refuted at "
                     "`numlikeFlags = [true, false]`, a non-empty collection with a "
                     "non-affirmative element (`allTrue = false`) where the "
                     "post-image demands `false` — a mixed point distinct from the "
                     "empty and single-element points of the other rivals.",
        "witness": _TESTER_A +
                   "example : numericNoticeFiresTester [true, false] = false := by\n"
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1
# admissibility, 2 soundness positives, 1 MANDATORY frame-mutation rival, 4
# uniqueness rivals) and 0 AXIOM_TESTS. The sibling contracts two near-identical
# decision functions over a permission-guarded flag list; this bundle models the
# SAME two decisions deeply as `noticeFires flags = (!flags.isEmpty && allTrue
# flags)` over `List Bool` at both sites — a faithful narrowing (the per-element
# classification is UNCHANGED and observed only through its boolean result, which
# is the input carrier). Every sibling SPEC case is accounted for below.
#
#   sibling case (nagini)          -> here
#   ---------------------------------------------------------------------
#   admiss-gold-baseline            -> admiss-nondegenerate             RE-AIMED
#   pos-reorder-f1                  -> pos-commute-f1                    RE-SHAPED
#   pos-reorder-f2                  -> pos-ite-f2                        RE-SHAPED
#   frame-mutation-f1 (MANDATORY)   -> (none)                           VACUOUS
#   partial-empty-f1                -> weak-drop-guard-f1               PORTED
#   partial-empty-f2                -> weak-drop-guard-f2               PORTED
#   weak-len-only-f1                -> weak-guard-only-f1               PORTED
#   (no sibling counterpart)        -> weak-guard-only-f2               ADDED (site B)
#   weak-const-true-f1              -> weak-const-true-f1               PORTED
#
# 6 ported/re-aimed, 1 re-shaped pair, 1 added, 1 vacuous. 8 cases here vs 8
# nagini. The ADDED case (weak-guard-only-f2) is the aggregate-facet attack on
# the second site: without it the sole site-B reject witness would probe only the
# empty collection, so the battery would say nothing about C2's dependence on the
# aggregate — a binder every site-B rival held at the empty shape. It moves
# parsableFlags off the empty-only point to a non-affirmative element.
#
# RE-AIMED (admissibility): the sibling's admissibility case is the frozen gold
#   impl, verifying to attest the half-permission precondition admits a normal
#   F2P-shaped input (including the empty list). This bundle has NO `require`
#   clause, so nothing could exclude any input on the total domain — that probe
#   is vacuous. Re-aimed at proving the post-image is NON-DEGENERATE: the emission
#   decision genuinely varies with the input (emit on non-empty all-affirmative,
#   withhold on empty, withhold on mixed), discharged by an in-region assert over
#   the three F2P-shaped points (decidable — the carrier is `Bool`).
# RE-SHAPED (positives): the sibling's pos-reorder-f1/f2 rewrite `if c==0: every
#   = False` as the algebraic conjunction `every = every and (c != 0)` on each
#   site. The structural analogs here reshape each site's emission decision:
#   pos-commute-f1 commutes the two conjuncts (`allTrue && !isEmpty`);
#   pos-ite-f2 spells the guard as an explicit emptiness branch. Both are
#   observationally identical, cross-site, and verify under the frozen proof.
# VACUOUS (frame-mutation-f1, MANDATORY on nagini): the sibling writes to the
#   read-only input `flags[0]`, held at `Acc(list_pred(flags), 1/2)`, to trip
#   INSUFFICIENT PERMISSION before the postcondition is considered. This backend
#   is referentially transparent: `numlikeFlags`/`parsableFlags` are immutable
#   values, this bundle declares NO `mut` parameter, and there is no heap, no
#   aliasing, and no permission system. There is no read-only input to overwrite
#   and no substitute probe to build, so the class is vacuous (per the porting
#   map, legitimately dropped, not fabricated). Its ARGUMENT (a real patch
#   mutating the caller's value array would corrupt downstream data) has no value
#   footprint the spec can force here — each query returns a fresh `Bool` and
#   mutates nothing by construction (directive 5, discharged by the ABSENCE of a
#   `mut` binder).
#
# BINDER / CLAUSE COVERAGE. There are two spec predicates (C1 over `numlikeFlags`,
#   C2 over `parsableFlags`), each with a single top-level clause folding two
#   facets — the non-emptiness guard `!flags.isEmpty` and the aggregate
#   `allTrue flags`. Both obligations are DEFENDED (C1 by admiss-nondegenerate +
#   pos-commute-f1; C2 by pos-ite-f2) and ATTACKED (C1 by weak-drop-guard-f1 /
#   weak-guard-only-f1 / weak-const-true-f1; C2 by weak-drop-guard-f2). Both
#   facets are attacked: the guard facet by weak-drop-guard-f1/f2 (refuted on the
#   empty collection) and the aggregate facet by weak-guard-only-f1 (refuted on a
#   non-affirmative element). The sole binder of each query is varied across the
#   reject witnesses: numlikeFlags over `[]`, `[false]`, `[true, false]` (empty,
#   single non-affirmative, mixed) and parsableFlags over `[]`. Distinct witness
#   points: `[]` (site A), `[]` (site B), `[false]`, `[true, false]` — three
#   distinct collection shapes plus the cross-site empty probe, so no rival is
#   refuted at a single pinned shape and both facets of both obligations are
#   demonstrated.
#
# WITNESS FORM. The carrier is fully transparent (`List Bool` -> `Bool`, all
#   decidable), so no opaque-term conditioning is needed: each rival is a
#   straight-line impl and each witness reaches the method contract through
#   Velvet's tester machinery (`<method>Tester <flags> = false`), discharged by
#   `decide` at a concrete literal. Confirmed empirically: each witness ELABORATES
#   against its rival and FAILS against the frozen solution (the required
#   discrimination); each rival module does NOT verify; the admissibility assert
#   is live (a false length/emission claim leaves an unsolved goal).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this gate ignores it.
#   This bundle declares no `axiom` and no A-reference deep model (both decisions
#   are modeled directly by the pure `def noticeFires`/`allTrue`; the `axioms`
#   region is empty), so there is nothing here for this gate to probe.
AXIOM_TESTS = []
