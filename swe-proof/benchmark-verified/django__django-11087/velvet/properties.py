"""properties.py — G-PBT falsification battery for django__django-11087 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct columnsToFetch`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over two column-id lists and three
boolean conditions):

  columnsToFetch (allColumns referencedColumns : List Nat)
                 (widenedFetch preDelete postDelete : Bool) return (out : List Nat)
    ensures out = columnsFetched allColumns referencedColumns
                                 widenedFetch preDelete postDelete
    ensures hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)

  where the pure model (all in the spec-visible `pure` region, fully GROUNDED —
  no opaque callee, no answer-key):
    hasExposingSubscriber pre post := pre || post
    mayNarrow w pre post           := !(w || hasExposingSubscriber pre post)
    columnsFetched all ref w pre post := if mayNarrow w pre post then ref else all

  The load-bearing clause is the first: the returned set is pinned BY FULL VALUE
  to one of the two input lists across the WHOLE guard partition — the narrowed
  set (`referencedColumns`) exactly when narrowing is permitted (no widened fetch
  AND no exposing subscriber), the full set (`allColumns`) otherwise. Because the
  post-image is a method INPUT selected by a transparent guard over the three
  booleans, there is no opaque oracle to echo (directive 8): a wrong impl must
  return the WRONG list on some concrete guard configuration, which a `List Nat`
  disequality refutes. The second clause merely restates the `hasExposingSubscriber`
  definition and is IMPL-INDEPENDENT (true for every impl, since the impl cannot
  redefine the pure `def`); it therefore has no attacking rival and needs none.

BINDER STRUCTURE (read before judging binder coverage). The load-bearing clause
depends on all five inputs. The two lists (`allColumns`, `referencedColumns`)
must DIFFER for any rival that confuses them to be observable, so every witness
holds them at distinct lists. The three booleans partition the guard:
`widenedFetch`, `preDelete`, `postDelete` each independently force the FULL
branch when set (the narrow decision is `!(w || pre || post)`). The reject
witnesses below toggle EACH of the three booleans to `true` in isolation (all
other booleans `false`) so that a rival mishandling ONLY one term is caught —
this is the exact failure mode the porting guide warns about (a battery whose
witnesses all pin a boolean at one value never notices a rival that abuses only
that binder):
    ignore-widened : widenedFetch=true,  pre=false, post=false
    drop-pre       : widenedFetch=false, pre=true,  post=false
    drop-post      : widenedFetch=false, pre=false, post=true
plus the two branch-selection rivals at the all-false narrow point (overfetch)
and the all-full point (always-narrow, pre=post=true).

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION (nagini's frame-mut-referenced / frame-mut-allfields,
    MANDATORY there) — VACUOUS here. The nagini sibling holds both list inputs at
    a fractional heap permission (``Acc(list_pred(.),1/2)``) an impl can illegally
    overwrite, and ships one rival per read-only list. Lean/Velvet are
    referentially transparent: every input is an immutable value, no binder is
    ``mut``, there is no heap and no aliasing — so there is no read-only field to
    mutate and no substitute probe to build. Not fabricated (porting map: this
    class is vacuous here).
  * ADMISSIBILITY (nagini's admiss-f2p-shaped-input) — PORTED, re-expressed for a
    TOTAL carrier. The nagini spec carries two subset ``Requires`` clauses (an
    F2P input might be excluded => PRECOND-TOO-STRONG); this method's
    `pre-conditions` region is EMPTY, so there is no `require` to over-constrain
    and the literal nagini probe does not transfer. That does NOT make the lane
    vacuous: the analogue on a total carrier is the OBLIGATION being unsatisfiable
    or degenerate at exactly an F2P-shaped input, which reads like a spec every
    impl meets while in fact no impl can meet it. `admiss-f2p-obligation-satisfiable`
    discharges that directly — an in-region `assert`, by evaluation, that at the
    F2P-shaped column configuration the load-bearing clause both HOLDS and
    DISCRIMINATES (the pinned set at the narrow configuration differs from the one
    at the exposed configuration), with the frozen impl kept verbatim after it so
    the method's own obligation still discharges.
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
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a method input selected by a
    transparent guard, not an axiomatized oracle; the `axioms` region is empty.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches the postcondition through Velvet's own tester machinery.
``columnsToFetchTester all ref w pre post = false`` says the extracted program's
result violates the postcondition at that concrete input. It is checked in a
file whose ``prove_correct`` block has been stripped, so no tactic script can
mask the verdict. Every input point uses small `Nat` literal lists and boolean
literals, so the tester kernel-reduces under ``decide``. Each reject witness was
run against both the rival (exit 0) and the frozen solution (exit 1) with two
real builds before shipping — the required two-build discrimination check.

AXIOM lane: EMPTY (the `axioms` region declares no `axiom`; the two boolean
subscriber observations are directive-7 free inputs, R-refinements validated by
conformance_check.py / G-CONF, not consumed contracts). The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11087"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single impl region (the guard
# ---- computation + branch) and is unique in Solution.lean (both facts asserted
# ---- at load by _swap). Anchoring on the whole block keeps the surgery within
# ---- the elided region. ----
_IMPL_OLD = """    -- impl-start
    -- Narrow to the referenced columns only when the fetch was not widened and
    -- no exposing subscriber is registered; otherwise keep the full column set.
    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))
    if narrow then
      return referencedColumns
    else
      return allColumns
    -- impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


def _impl(body: str) -> str:
    return "    -- impl-start\n" + body + "\n    -- impl-end"


def _with_impl(body: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL_OLD, _impl(body))


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery. `columnsToFetchTester all ref w pre post = false` says the
# ---- extracted program's result violates the postcondition at that input. The
# ---- method has no `require`, so no configuration is vacuously excluded. ----
_TESTER = (
    "extract_program_for columnsToFetch\n"
    "prove_precondition_decidable_for columnsToFetch\n"
    "prove_postcondition_decidable_for columnsToFetch\n"
    "derive_tester_for columnsToFetch\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the byte-identical two
    # `ensures` obligations and only reshapes the executable surface; the frozen
    # `loom_solve` proof discharges both (confirmed with real builds).
    # =====================================================================
    {
        "id": "pos-branch-reorder-exposed-first",
        "kind": "soundness",
        "expect": "verify",
        # The gold tests the NARROW guard first; this control tests the FULL
        # (exposed/widened) guard first and swaps the two return arms to match —
        # the same decision, branches reordered.
        "module": _with_impl(
            "    let expose : Bool := widenedFetch || (preDelete || postDelete)\n"
            "    if expose then\n"
            "      return allColumns\n"
            "    else\n"
            "      return referencedColumns"),
        "rationale": "structurally different CORRECT impl: the guard is negated and "
                     "the two return arms are swapped (full-branch first). Equal to "
                     "the frozen decision (`expose` is the negation of `narrow`), so "
                     "`out = columnsFetched ...` still holds on both branches. A "
                     "faithful correct reshape MUST verify, else SPEC-TOO-STRONG. "
                     "(Sibling: pos-control-fields-branch-reorder.)",
    },
    {
        "id": "pos-demorgan-narrow-guard",
        "kind": "soundness",
        "expect": "verify",
        # De Morgan-equal guard: `!(w || pre || post)` == `!w && !pre && !post`.
        "module": _with_impl(
            "    let narrow : Bool := (!widenedFetch) && ((!preDelete) && (!postDelete))\n"
            "    if narrow then\n"
            "      return referencedColumns\n"
            "    else\n"
            "      return allColumns"),
        "rationale": "De Morgan-equal correct impl: the narrowing guard "
                     "`!(w || pre || post)` is rewritten `!w && !pre && !post`, the "
                     "same predicate. Must satisfy `out = columnsFetched ...` on both "
                     "branches. If it cannot verify => SPEC-TOO-STRONG. (Sibling: "
                     "pos-control-bool-demorgan.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require`, so the literal nagini probe
    # ("a normal input satisfies the precondition") does not transfer: nothing
    # could exclude an F2P-shaped input. The residual admissibility risk on a
    # TOTAL domain is that the obligation is UNSATISFIABLE or DEGENERATE at the
    # interesting point — a spec no impl can meet reads exactly like a spec every
    # impl meets, and either way the gate's other two lanes cannot see it. This
    # case discharges an in-region `assert`, at the fully concrete F2P-shaped
    # column configuration, that the load-bearing clause (a) HOLDS there and (b)
    # DISCRIMINATES there (the set pinned at the narrow configuration is distinct
    # from the set pinned once a before-removal subscriber is present). The frozen
    # impl follows verbatim, so the method's own two `ensures` still discharge
    # under the untouched `loom_solve`.
    #
    # The assert is LIVE, not decoration, and this was measured rather than
    # asserted: two negative controls of the same shape with a FALSE claim at the
    # SAME point (claiming the narrow configuration yields the full list; claiming
    # the narrow and exposed configurations agree) each FAIL to build with
    # `unsolved goals ... case «admiss_1»`, exit 1. So a degenerate obligation
    # here would break this case rather than pass it.
    # =====================================================================
    {
        "id": "admiss-f2p-obligation-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(
            "    -- Admissibility at an F2P-shaped input: the load-bearing clause is\n"
            "    -- SATISFIABLE and NON-DEGENERATE at the concrete column\n"
            "    -- configuration the fix cares about (a full set of three column\n"
            "    -- ids, two of which are referenced).\n"
            "    assert (with_name_prefix `admiss\n"
            "      (columnsFetched [1,2,3] [1,2] false false false = [1,2]\n"
            "        /\\ columnsFetched [1,2,3] [1,2] false false false\n"
            "             ≠ columnsFetched [1,2,3] [1,2] false true false))\n"
            "    -- the frozen impl follows, verbatim\n"
            "    let narrow : Bool := !(widenedFetch || (preDelete || postDelete))\n"
            "    if narrow then\n"
            "      return referencedColumns\n"
            "    else\n"
            "      return allColumns"),
        "rationale": "PRECOND-TOO-STRONG lane, re-expressed for a carrier with no "
                     "`require`: the obligation is satisfiable AND non-degenerate at "
                     "the F2P-shaped configuration. At all=[1,2,3], ref=[1,2] with no "
                     "widened fetch and no subscriber the clause pins out=[1,2] (it is "
                     "MEETABLE there), and that pinned set is DISTINCT from the one "
                     "pinned at the same lists once preDelete is set (so the clause "
                     "genuinely constrains this configuration instead of being "
                     "trivially true). Both conjuncts discharge by evaluation; the "
                     "frozen impl is kept verbatim so the two `ensures` discharge too. "
                     "Liveness measured: the same shape with a false claim at the same "
                     "point fails with `unsolved goals ... case «admiss_1»`. If this "
                     "could not verify, the obligation would be unsatisfiable at a "
                     "legitimate input => PRECOND-TOO-STRONG. (Sibling: "
                     "admiss-f2p-shaped-input, whose subset `Requires` do not port.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a STRAIGHT-LINE / small-branch impl whose
    # extracted tester reduces under `decide`, refuted at a concrete input by a
    # witness that ELABORATES against the rival and FAILS against the frozen
    # solution. Each carries the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-overfetch-always-full",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack — the pre-patch behaviour: always fetch the full
        # column set, never narrow. Also subsumes the nagini
        # partial-bool-always-true (an always-exposing predicate forces full).
        "module": _with_impl("    return allColumns"),
        "refinement": "this IS the unoptimised prior behaviour (always fetch every "
                      "column, never narrow). The sole failing-to-passing test asserts, "
                      "in the no-subscriber case, that the cascade row fetch is narrowed "
                      "to the referenced columns only; returning the full column set "
                      "fails that equality check, so a faithful change that never "
                      "narrowed does NOT resolve it.",
        "rationale": "REJECT from `out = columnsFetched ...`: on the narrow "
                     "configuration (widenedFetch=pre=post=false) the spec pins "
                     "`out = referencedColumns`, but the rival returns `allColumns`, "
                     "which differs whenever the two lists differ. Refuted at "
                     "all=[1,2], ref=[1], w=false, pre=false, post=false. "
                     "(Siblings: partial-prepatch-overfetch, partial-bool-always-true.)",
        "witness": _witness("columnsToFetchTester [1,2] [1] false false false"),
    },
    {
        "id": "weak-always-narrow",
        "kind": "uniqueness",
        "expect": "reject",
        # The opposite near-miss: always narrow to the referenced set, ignoring
        # every full-fetch trigger. Correct on the whole no-signal/no-widen
        # sub-domain, wrong whenever any full-fetch condition is set.
        "module": _with_impl("    return referencedColumns"),
        "refinement": "always narrowing ignores the exposure/widening triggers: when "
                      "a change-notification subscriber IS registered the rows are "
                      "handed to user code, where any column may be read, so the full "
                      "set must be fetched. The failing-to-passing test's "
                      "subscriber-connected sub-cases assert that a column which is NOT "
                      "referenced is nonetheless fetched once a receiver is connected; "
                      "narrowing anyway drops it, that membership check fails, and the "
                      "faithful change does NOT resolve.",
        "rationale": "REJECT from `out = columnsFetched ...`: on the full "
                     "configuration (pre=post=true) the spec pins `out = allColumns`, "
                     "but the rival returns `referencedColumns`. Refuted at "
                     "all=[3,4], ref=[3], w=false, pre=true, post=true — a distinct "
                     "input point exercising the full branch. (Complements the "
                     "overfetch rival: this is wrong on the full branch, that on the "
                     "narrow branch.)",
        "witness": _witness("columnsToFetchTester [3,4] [3] false true true"),
    },
    {
        "id": "weak-ignore-widened",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `widenedFetch` term from the guard: narrow even when the fetch
        # was widened to also pull related rows. Correct whenever widenedFetch is
        # false; wrong on widenedFetch=true, no subscriber.
        "module": _with_impl(
            "    let narrow : Bool := !(preDelete || postDelete)\n"
            "    if narrow then\n"
            "      return referencedColumns\n"
            "    else\n"
            "      return allColumns"),
        "refinement": "dropping the widened-fetch term narrows even when the fetch "
                      "was widened to also pull in further related rows — the case "
                      "the desired guard deliberately excludes, because narrowing "
                      "the column set and widening the row set interact in ways that "
                      "are hard to get right together. A change that narrowed under a "
                      "widened fetch would re-introduce that interaction rather than "
                      "avoid it, so it would not be the resolving behaviour.",
        "rationale": "REJECT from `out = columnsFetched ...`: on the sub-domain "
                     "widenedFetch=true, pre=false, post=false the spec pins "
                     "`out = allColumns`, but the rival narrows to `referencedColumns`. "
                     "This is the ONLY reject witness with widenedFetch=true, so it is "
                     "what varies that binder. Refuted at all=[5,6], ref=[5], w=true, "
                     "pre=false, post=false. (Sibling: the nagini "
                     "partial-domain rival that drops the widening term.)",
        "witness": _witness("columnsToFetchTester [5,6] [5] true false false"),
    },
    {
        "id": "weak-drop-pre-term",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `preDelete` term: narrow even when a before-removal subscriber
        # is registered. Isolates the preDelete binder (only true here).
        "module": _with_impl(
            "    let narrow : Bool := !(widenedFetch || postDelete)\n"
            "    if narrow then\n"
            "      return referencedColumns\n"
            "    else\n"
            "      return allColumns"),
        "refinement": "dropping the before-removal subscriber term narrows the fetch "
                      "even when a before-removal receiver is connected; that receiver "
                      "is handed the about-to-be-removed rows, where any column may be "
                      "read, so the full set is required. The failing-to-passing "
                      "sub-case that connects a before-removal receiver asserts the "
                      "unreferenced column IS fetched; with this term dropped it is "
                      "narrowed away, that membership check fails, and the faithful "
                      "change does NOT resolve.",
        "rationale": "REJECT from `out = columnsFetched ...`: on pre=true (widened "
                     "and post both false) the spec pins `out = allColumns`, but the "
                     "rival narrows. This is the ONLY witness with preDelete=true in "
                     "isolation, so it varies that binder. Refuted at all=[7,8], "
                     "ref=[7], w=false, pre=true, post=false. (New; symmetric partner "
                     "of weak-drop-post-term, needed so preDelete is toggled alone.)",
        "witness": _witness("columnsToFetchTester [7,8] [7] false true false"),
    },
    {
        "id": "weak-drop-post-term",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `postDelete` term: narrow even when an after-removal subscriber
        # is registered. Isolates the postDelete binder (only true here).
        "module": _with_impl(
            "    let narrow : Bool := !(widenedFetch || preDelete)\n"
            "    if narrow then\n"
            "      return referencedColumns\n"
            "    else\n"
            "      return allColumns"),
        "refinement": "dropping the after-removal subscriber term keeps narrowing when "
                      "an after-removal receiver is connected; that receiver observes "
                      "the removed rows, so the full column set must be fetched. The "
                      "failing-to-passing sub-case that connects an after-removal "
                      "receiver asserts the unreferenced column IS fetched; with this "
                      "term dropped columns are narrowed, that membership check fails, "
                      "and the faithful one-term change does NOT resolve.",
        "rationale": "REJECT from `out = columnsFetched ...`: on post=true (widened "
                     "and pre both false) the spec pins `out = allColumns`, but the "
                     "rival narrows. This is the ONLY witness with postDelete=true in "
                     "isolation, so it varies that binder. Refuted at all=[9,10], "
                     "ref=[9], w=false, pre=false, post=true. (Sibling: "
                     "partial-bool-drop-post.)",
        "witness": _witness("columnsToFetchTester [9,10] [9] false false true"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation, 4 partial-domain/near-miss
# rivals) plus an EMPTY AXIOM lane. This battery carries 8 (2 soundness, 1
# admissibility, 5 uniqueness). This bundle models a NARROWER surface: nagini
# contracts a boolean helper `rows_exposed_to_observers` AND a list-building
# `select_cascade_fields` over fractional-permission list carriers; velvet folds
# BOTH decisions into one purely functional method `columnsToFetch` over
# immutable `List Nat` and `Bool`, with the boolean subscriber observations as
# free inputs. The accounting below records every sibling case.
#
#   sibling case (nagini)              -> here
#   ------------------------------------------------------------------------
#   pos-control-fields-branch-reorder  -> pos-branch-reorder-exposed-first  RE-EXPRESSED
#   pos-control-bool-demorgan          -> pos-demorgan-narrow-guard         PORTED
#   admiss-f2p-shaped-input            -> admiss-f2p-obligation-satisfiable RE-EXPRESSED
#   frame-mut-referenced-inplace       -> (none)                            VACUOUS (no heap/mut)
#   frame-mut-allfields-inplace        -> (none)                            VACUOUS (no heap/mut)
#   partial-prepatch-overfetch         -> weak-overfetch-always-full        PORTED (central)
#   partial-ignore-widening-term       -> weak-ignore-widened               PORTED
#   partial-bool-drop-post             -> weak-drop-post-term               PORTED
#   partial-bool-always-true           -> weak-overfetch-always-full        SUBSUMED
#   (new, no sibling)                  -> weak-drop-pre-term                ADDED (binder coverage)
#   (new, no sibling)                  -> weak-always-narrow                ADDED (full-branch attack)
#   AXIOM_TESTS (empty)                -> (none)                            DROPPED (G-AX)
#
# RE-EXPRESSED (pos-branch-reorder-exposed-first): nagini reorders the two guard
#   branches of the list builder (exposed-first) and swaps the loop bodies. Here
#   the same ARGUMENT is carried by negating the guard (`expose = !narrow`) and
#   swapping the two return arms; the frozen loom_solve proof discharges it.
# PORTED (pos-demorgan-narrow-guard): the De Morgan-equal boolean reshape ports
#   directly onto the inline narrowing guard.
# RE-EXPRESSED (admiss-f2p-shaped-input): the nagini spec carries subset `Requires`
#   clauses whose over-strength that case tests; this method's `pre-conditions`
#   region is EMPTY (no `require`), so the literal probe does not transfer. The
#   lane is NOT thereby vacuous — "the frozen obligation has no precondition" is
#   the wrong reason to drop it. On a total carrier the analogue is the obligation
#   being unsatisfiable or degenerate at exactly an F2P-shaped input, and
#   admiss-f2p-obligation-satisfiable tests that directly: it discharges the
#   load-bearing clause at the concrete F2P-shaped column configuration, by
#   evaluation, as an in-region `assert`, and additionally asserts the clause
#   DISCRIMINATES at that point (the pinned set differs from the one pinned once a
#   before-removal subscriber is present), before closing the frozen obligation
#   verbatim. Liveness measured with two negative controls: the same shape with a
#   false claim at the same point fails (`unsolved goals ... case «admiss_1»`,
#   exit 1), so the assert carries information.
# VACUOUS (frame-mut-*): nagini holds both list inputs at Acc(list_pred(.),1/2) an
#   impl can illegally write, and ships one rival per read-only list. This backend
#   is referentially transparent and declares no `mut` binder — every input is an
#   immutable value with no heap footprint — so there is no read-only field to
#   overwrite and no substitute probe. Not fabricated (porting map: vacuous here).
# PORTED / SUBSUMED (partial-domain rivals): the pre-patch always-full overfetch
#   ports as weak-overfetch-always-full (which also subsumes the always-True
#   exposure near-miss, since an always-exposing predicate == always full-fetch);
#   dropping the widened-fetch term ports as weak-ignore-widened; dropping the
#   after-removal subscriber term ports as weak-drop-post-term.
# ADDED (weak-drop-pre-term, weak-always-narrow): the folded model exposes TWO
#   independent subscriber terms (pre and post) plus a widened-fetch term; the
#   nagini boolean helper only carried a drop-post rival. weak-drop-pre-term is the
#   symmetric partner so preDelete is toggled true IN ISOLATION (otherwise no rival
#   would notice an impl mishandling only the before-removal term). weak-always-narrow
#   attacks the full branch generically (the mirror of overfetch).
#
#   The five reject witnesses probe five DISTINCT input tuples (pts=5). The two
#   list binders take distinct values on every witness. The three boolean binders
#   are each toggled `true` IN ISOLATION exactly once — widenedFetch by
#   weak-ignore-widened, preDelete by weak-drop-pre-term, postDelete by
#   weak-drop-post-term — and the branch-selection rivals cover the all-false
#   (overfetch) and all-full (always-narrow, pre=post=true) corners. Every
#   guard term is thereby attacked. Each witness was SEEN to discriminate: it
#   ELABORATES against the rival (small-literal tester reduces under `decide`) and
#   FAILS against the frozen solution (the guard disagrees at that point), verified
#   with two real builds each.
#
# SECOND ENSURES CLAUSE (`hasExposingSubscriber pre post = (pre || post)`): a
#   restatement of the pure `def`, true for EVERY impl (an impl cannot redefine the
#   spec-level `def`), hence not attackable and carrying no rival — there is nothing
#   for a wrong impl to get wrong about it.
#
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no axiom
#   (the two subscriber observations are directive-7 free inputs, R-refinements
#   validated by conformance_check.py), so there is nothing to probe and the gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
