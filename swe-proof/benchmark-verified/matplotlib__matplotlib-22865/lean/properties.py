"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-22865 (lean).

NOT a Lean module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``-- proof-start`` / ``-- proof-end``
tactic body, is changed — both of which the consumer spec view elides — so
``markers.same_spec`` holds and the ``theorem correct_colorbarEdgeSegments``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation. It is checked by the real verifier: ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — the witness elaborates
against the rival and FAILS against the frozen solution).

DEFENDED SURFACE. One contracted function that selects a contiguous positional
sub-run of an ordered candidate list, keyed on three booleans:

  colorbarEdgeSegments (drawEdges openLower openUpper : Bool) (segs : List α)
      -> (result : List α)
    result = if drawEdges then
               (segs.take (if openUpper then segs.length else segs.length - 1)).drop
                 (if openLower then 0 else 1)
             else []

The single top-level equality clause folds together what the nagini sibling
split into a LENGTH pin (``len == end_index - start_index``) and an ELEMENT pin
(``result[k] == segments[start_index + k]``): a positional slice pins both the
length and the identity/order of every kept element at once. Both halves of that
folding are attacked separately below — five rivals change the selected LENGTH,
one changes only the ORDER — so the fold is demonstrated, not merely asserted.
The clause's behavior depends on all FOUR input binders — ``drawEdges``,
``openLower``, ``openUpper``, ``segs`` — and each is abused by some reject rival,
with the two end flags abused at all four of their JOINT settings.

CARRIER. Fully TRANSPARENT: ``segs`` is a generic ``List α`` and the selection
is ``take``/``drop``, with no opaque callee and no axiom. So a witness needs no
conditioning: it instantiates ``α := Nat`` at a small concrete list and closes by
``decide``. The witness states the spec predicate directly at a concrete input,
in a file where the frozen obligation has been stripped, and is checked BOTH
ways — it elaborates against the rival (the rival provably contradicts the spec
at that input) and FAILS against the frozen solution (so it is a real
discriminator, not a tautology). No ``sorry``/``admit``/``native_decide``.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the selection is
modeled directly over the carrier). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-22865"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap. ------------
_GOLD_GUARD = "  if !drawEdges then\n    return []\n"
_GOLD_S = "  let startIdx := if openLower then 0 else 1"
_GOLD_E = "  let endIdx := if openUpper then segs.length else segs.length - 1"
_GOLD_RET = "  return (segs.take endIdx).drop startIdx"

# ---- proof-body anchor. The proof region is elided from the consumer spec view,
# ---- so a soundness case may retune it without touching the spec statement or
# ---- dropping the obligation. Unique in the file.
_GOLD_PROOF = "  cases drawEdges <;> rfl"

for _anchor in (_GOLD_GUARD, _GOLD_S, _GOLD_E, _GOLD_RET, _GOLD_PROOF):
    assert _BASE.count(_anchor) == 1, f"frozen region drifted: {_anchor!r}"


# ---- witness preamble. States the frozen spec predicate directly at a concrete
# ---- input over `α := Nat`; the carrier is transparent so `decide` closes it.
# ---- Checked in a file whose obligation has been stripped. No `sorry`/`admit`/
# ---- `native_decide`; the frozen solution rejects these witnesses all the same.
def _witness(args):
    return (
        "example : ¬ problem_spec_colorbarEdgeSegments\n"
        f"    {args}\n"
        f"    (implementation_colorbarEdgeSegments {args}) := by\n"
        "  unfold problem_spec_colorbarEdgeSegments implementation_colorbarEdgeSegments\n"
        "  decide\n"
    )


# Concrete candidate lists. Content is opaque to the selection; only length and
# position matter, so distinct `Nat` elements suffice to make the list
# non-degenerate at each witness input.
_L3 = "([0, 1, 2] : List Nat)"        # 3 candidates (F2P both/min/max shape)
_L4 = "([0, 1, 2, 3] : List Nat)"     # 4 candidates (a distinct `segs`)


# ---- admissibility body. An `example` placed INSIDE the impl region, which the
# ---- consumer spec view elides and `variant_scope` admits: rule 3 bans a new
# ---- top-level `theorem`/`lemma` (those are what could shadow or pad the frozen
# ---- obligation set), and an anonymous `example` is neither — it declares no
# ---- name at all. So the sibling's admissibility lane IS expressible here,
# ---- re-aimed from "the precondition is consistent" (vacuous: the lean
# ---- obligation quantifies over ALL inputs under no hypothesis, so there is no
# ---- precondition to admit) at the claim that still has content on a total
# ---- domain: the spec is SATISFIABLE at concrete inputs and its post-image is
# ---- non-degenerate and flag-sensitive. All five conjuncts are decided at
# ---- literal inputs, so nothing here is assumed.
_ADMISS = (
    "\n"
    "-- Admissibility: the relation is satisfiable at concrete inputs and its\n"
    "-- post-image is non-degenerate and varies with every flag — five distinct\n"
    "-- selections (lengths 3, 2, 2, 1, 0) over the four flag settings.\n"
    "example : problem_spec_colorbarEdgeSegments true true true ([0, 1, 2] : List Nat) [0, 1, 2]\n"
    "    ∧ problem_spec_colorbarEdgeSegments true false true ([0, 1, 2] : List Nat) [1, 2]\n"
    "    ∧ problem_spec_colorbarEdgeSegments true true false ([0, 1, 2] : List Nat) [0, 1]\n"
    "    ∧ problem_spec_colorbarEdgeSegments true false false ([0, 1, 2] : List Nat) [1]\n"
    "    ∧ problem_spec_colorbarEdgeSegments false true true ([0, 1, 2] : List Nat) [] := by\n"
    "  unfold problem_spec_colorbarEdgeSegments\n"
    "  refine ⟨by decide, by decide, by decide, by decide, by decide⟩\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the postcondition is SPEC-TOO-STRONG on
    # impl shape. The slice is expressed as drop-then-take
    # `(segs.drop startIdx).take (endIdx - startIdx)` instead of the frozen
    # take-then-drop `(segs.take endIdx).drop startIdx`. These denote the same
    # sub-run (a standard `List.drop_take` identity), so the single equality
    # clause still holds for every input; the proof body is retuned by adding
    # that identity to the simp set — the obligation statement is untouched.
    # =====================================================================
    {
        "id": "pos-control-drop-then-take",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_RET,
                  "  return (segs.drop startIdx).take (endIdx - startIdx)"),
            _GOLD_PROOF,
            "  cases drawEdges <;> simp [Id.run, List.drop_take, bind, pure]"),
        "rationale": (
            "a correct reshape: the contiguous run is taken as drop-then-take "
            "rather than take-then-drop. The two denote the same sub-list (a "
            "standard list identity), so the single `result = ...` clause still "
            "holds for every input; the proof only adds that identity to the simp "
            "set and keeps the theorem statement byte-identical. If it failed to "
            "verify the spec would be SPEC-TOO-STRONG on impl shape."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input (the transparent carrier lets `decide` close it) and the
    # refinement argument that its faithful real counterpart would NOT resolve
    # the failing test. Witnesses vary all FOUR binders across the battery.
    # =====================================================================
    {
        "id": "weak-unconditional-inner-slice",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores BOTH end flags: always start=1, end=n-1 (the legacy
        # unconditional inner slice). Correct only when both ends are closed;
        # for both-open it drops both end boundaries.
        "module": _swap(
            _swap(_BASE, _GOLD_S, "  let startIdx := 1"),
            _GOLD_E, "  let endIdx := segs.length - 1"),
        "refinement": (
            "this is the pre-change behavior: an unconditional inner slice that "
            "drops the boundary at each end regardless of whether that end is "
            "open. When both ends are open the failing test observes that the two "
            "end boundaries are missing from the drawn set — exactly the reported "
            "defect — so a faithful counterpart still fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the single equality clause: at both ends open the spec "
            "keeps all n boundaries but this keeps only the inner n-2, so the "
            "results differ in LENGTH. If it verified the spec would be "
            "SPEC-TOO-WEAK (it would readmit the legacy behavior). Refuted at segs "
            "of length 3, both flags open."
        ),
        "witness": _witness(f"true true true {_L3}"),
    },
    {
        "id": "weak-ignore-lower-open-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Computes the upper bound correctly but always starts at 0 (ignores the
        # lower-open flag). Correct when the lower end is open; wrong when it is
        # closed (should start at 1, dropping the lower end boundary).
        "module": _swap(_BASE, _GOLD_S, "  let startIdx := 0"),
        "refinement": (
            "a counterpart that keeps the lower end boundary even when the lower "
            "end is NOT open retains a divider that should be dropped at the "
            "closed lower end. The failing test drives a configuration whose lower "
            "end is closed and observes the extra boundary, so it still fails. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from the equality clause via the lower-index dependence on "
            "`openLower`: with the lower end closed the spec starts one in (length "
            "n-1) but this starts at 0 (length n), so the results differ in "
            "LENGTH. Refuted at segs of length 3, lower flag CLOSED "
            "(openLower=false), upper open."
        ),
        "witness": _witness(f"true false true {_L3}"),
    },
    {
        "id": "weak-ignore-upper-open-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Computes the lower bound correctly but always ends at n (ignores the
        # upper-open flag). Correct when the upper end is open; wrong when it is
        # closed (should end at n-1, dropping the upper end boundary).
        "module": _swap(_BASE, _GOLD_E, "  let endIdx := segs.length"),
        "refinement": (
            "a counterpart that keeps the upper end boundary even when the upper "
            "end is NOT open retains a divider that should be dropped at the "
            "closed upper end. The failing test drives a configuration whose upper "
            "end is closed and observes the extra boundary, so it still fails. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from the equality clause via the upper-index dependence on "
            "`openUpper`: with the upper end closed the spec stops one short "
            "(length n-1-startIdx) but this runs to n (length n-startIdx), so the "
            "results differ in LENGTH. Refuted at segs of length 3, lower open, "
            "upper flag CLOSED (openUpper=false)."
        ),
        "witness": _witness(f"true true false {_L3}"),
    },
    {
        "id": "weak-short-run-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Bounds keyed on the flags correctly, but the upper bound is one short
        # (end := correct - 1), so one fewer boundary than the slice demands is
        # emitted on every input where the run is non-empty.
        "module": _swap(
            _BASE, _GOLD_E,
            "  let endIdx := (if openUpper then segs.length else segs.length - 1) - 1"),
        "refinement": (
            "a counterpart that stops the kept run one boundary short emits one "
            "fewer divider than intended. For a both-open configuration the "
            "failing test expects every boundary drawn but observes the last one "
            "missing, so it still fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the equality clause: the kept run is one element shorter "
            "than the spec's slice whenever that slice is non-empty, so the "
            "results differ in LENGTH. Refuted at segs of length 4 (a distinct "
            "`segs`), both flags open."
        ),
        "witness": _witness(f"true true true {_L4}"),
    },
    {
        "id": "weak-ignore-drawedges",
        "kind": "uniqueness",
        "expect": "reject",
        # Bounds correct, but returns the slice UNCONDITIONALLY — drops the
        # enable-flag guard, so a disabled selection still emits boundaries.
        "module": _swap(_BASE, _GOLD_GUARD, ""),
        "refinement": (
            "a counterpart that draws boundaries even when drawing is disabled "
            "produces dividers where none were requested. A configuration with "
            "drawing off expects an empty set but observes drawn boundaries, so it "
            "still fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the equality clause via the `drawEdges` dependence: with "
            "drawing disabled the spec returns the empty list (length 0) but this "
            "returns the non-empty slice, so the results differ in LENGTH. Refuted "
            "at segs of length 3, drawEdges=false."
        ),
        "witness": _witness(f"false true true {_L3}"),
    },
    {
        "id": "weak-both-ends-closed-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # Bounds keyed on the flags correctly, but short-circuits the one flag
        # combination NO other rival's witness reaches: when BOTH ends are
        # closed it returns the whole candidate list instead of the inner run.
        # Correct on all three configurations the shipped witnesses probe
        # (both-open, lower-closed/upper-open, lower-open/upper-closed), so it
        # is refutable ONLY at the fourth corner — which is why it is here.
        "module": _swap(
            _BASE, _GOLD_RET,
            "  if !openLower && !openUpper then\n"
            "    return segs\n" + _GOLD_RET),
        "refinement": (
            "a counterpart that emits every candidate row when NEITHER end is "
            "open keeps both terminal separators at two closed ends, where the "
            "intended selection keeps only the interior ones. The retained "
            "configuration whose two ends are both closed expects the single "
            "interior separator but observes all three, so it still fails. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from the equality clause at the ONE flag corner the other "
            "rivals leave unprobed: with both ends closed the spec keeps the "
            "inner n-2 rows but this keeps all n, so the results differ in "
            "LENGTH. Its wrongness is invisible at every other corner, so "
            "without this case the joint setting openLower=openUpper=false is "
            "attested by no witness at all. Refuted at segs of length 3, both "
            "flags CLOSED."
        ),
        "witness": _witness(f"true false false {_L3}"),
    },
    {
        "id": "weak-reversed-selection-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Selects the RIGHT rows by the right bounds, then emits them in
        # reversed order. The only rival whose selection has the correct LENGTH
        # at its witness input: it attacks the identity/ORDER half of the folded
        # equality clause, which every length-changing rival above leaves
        # untested.
        "module": _swap(
            _BASE, _GOLD_RET,
            "  return ((segs.take endIdx).drop startIdx).reverse"),
        "refinement": (
            "a counterpart that emits the kept separator rows back-to-front "
            "draws the right NUMBER of dividers at the right positions overall, "
            "but hands them over in the wrong order. The failing test compares "
            "the emitted rows against an ordered expected sequence row by row, "
            "so a reversed sequence mismatches wherever two or more rows are "
            "kept, and it still fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the ORDER/IDENTITY half of the equality clause, which "
            "no other rival probes: `result = (segs.take ...).drop ...` pins not "
            "just how many rows are kept but WHICH row sits at each position. "
            "This rival's selection has the correct length at every input, so a "
            "length-only spec would readmit it — the case is what shows the "
            "folded clause is strictly stronger than the sibling's LENGTH pin "
            "alone. Refuted at segs of length 3, both flags open, where the "
            "spec keeps [0,1,2] and this yields [2,1,0]."
        ),
        "witness": _witness(f"true true true {_L3}"),
    },
    # =====================================================================
    # ADMISSIBILITY — re-derived from the sibling's admissibility case, which
    # the port had recorded as inexpressible. It is expressible: the probe is
    # an `example` in the impl region (elided from the spec view, and not a
    # `theorem`/`lemma`, so it is inside the admissible variant scope). See
    # `_ADMISS` for what it claims and why the sibling's original reading had
    # to be re-aimed. Verified NON-decorative: mutating any conjunct to a
    # wrong selection makes the case fail to elaborate.
    # =====================================================================
    {
        "id": "admissibility-post-image-flag-sensitive",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_RET, _GOLD_RET + "\n" + _ADMISS),
        "rationale": (
            "the frozen relation is SATISFIABLE and its post-image is "
            "non-degenerate: five concrete instances of `problem_spec_...` are "
            "decided at literal inputs, exhibiting selections of lengths 3, 2, "
            "2, 1 and 0 across all four flag settings. If it failed to verify "
            "the relation would be unsatisfiable somewhere on its domain "
            "(PRECOND-TOO-STRONG on a total domain: an input the spec admits no "
            "result for). It is not decoration — swapping any conjunct's "
            "expected selection for a wrong one makes the module fail."
        ),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 MANDATORY frame-mutation rival, 4 partial-domain
# uniqueness rivals) contracting one function
# `drawn_separators(segments, lower_open, upper_open)` over a permission-bearing
# read-only list with a LENGTH pin and an ELEMENT pin. This bundle models the
# same positional selection over the purely-functional carrier `List α` plus
# three booleans, and folds the sibling's two pins into one `result = ...`
# equality clause (a positional slice pins length AND the identity/order of every
# kept element at once). It also makes `drawEdges` an explicit input the sibling
# carried implicitly (its Requires already excluded the disabled case), enabling
# one extra rival.
#
#   sibling case                                   -> here
#   ---------------------------------------------------------------------
#   pos-control-offset-loop                         -> pos-control-drop-then-take   PORTED
#   admissibility-f2p-shape                         -> admissibility-post-image-flag-sensitive
#                                                                                   PORTED (re-aimed)
#   frame-mutation-write-segments (MANDATORY)       -> (none)                       VACUOUS
#   partial-domain-prepatch-unconditional-1-to-n1   -> weak-unconditional-inner-slice PORTED
#   partial-domain-ignore-lower-open                -> weak-ignore-lower-open-flag  PORTED
#   partial-domain-ignore-upper-open                -> weak-ignore-upper-open-flag  PORTED
#   partial-domain-short-run-drop-last              -> weak-short-run-drop-last     PORTED
#   (no sibling counterpart)                        -> weak-ignore-drawedges        ADDED
#   (no sibling counterpart)                        -> weak-both-ends-closed-passthrough ADDED
#
# 6 ported, 1 vacuous, 2 added.
#
# PORTED, RE-AIMED (admissibility-f2p-shape): the sibling Asserts that its
#   precondition (Requires len(segments)>=2) yields a well-formed slice
#   (start_index <= end_index). That exact reading IS vacuous here — the lean
#   obligation has NO precondition, `correct_*` quantifies over ALL inputs under
#   no hypothesis, so there is no precondition to admit. But the lane itself is
#   expressible: the probe is an anonymous `example` inside the impl region,
#   which the consumer spec view elides and which rule 3 permits (it bans a new
#   top-level `theorem`/`lemma` — declarations that could shadow or pad the
#   frozen obligation set — and an `example` declares no name). So the case is
#   re-aimed at what still has content on a total domain: the relation is
#   satisfiable and its post-image is non-degenerate and flag-sensitive. Five
#   conjuncts, all `decide`d at literal inputs, exhibiting selections of lengths
#   3, 2, 2, 1 and 0 over all four flag settings.
# VACUOUS (frame-mutation-write-segments): the sibling's MANDATORY frame rival
#   writes into a read-only input held at Acc(list_pred(segments), 1/2) and is
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `segs` is an immutable value, not a mutable/aliasable binder.
#   There is no heap, no aliasing, and no permission system to trip — no
#   read-only input to overwrite and no substitute probe to build. Reported
#   vacuous, not fabricated (frame/permission-mutation class is VACUOUS on Lean).
# ADDED (weak-ignore-drawedges): the enable flag `drawEdges` is an explicit input
#   here (the sibling's Requires implicitly excluded the disabled case). The spec
#   returns `[]` when drawing is disabled; a rival that ignores the flag and draws
#   anyway is refuted directly, exercising the `drawEdges` binder that no ported
#   rival abuses.
# ADDED (weak-both-ends-closed-passthrough): the five cases above vary each flag
#   MARGINALLY but leave one JOINT setting — openLower=openUpper=false, both ends
#   closed — witnessed by nothing. That corner is not redundant: it is the only
#   one where the selection drops a separator at BOTH ends at once, and a rival
#   can be wrong there while agreeing with the spec at all three other corners
#   (this one is). Marginal coverage of each flag is therefore not joint
#   coverage, and the added rival closes the gap.
#
# BINDER / CLAUSE COVERAGE. The single equality clause is DEFENDED by the
# positive control and by the admissibility case, and ATTACKED by all six
# rivals. Its behavior depends on all four input binders, and the six reject
# witnesses probe six DISTINCT inputs covering ALL FOUR flag corners:
#     drawEdges=true,  openLower=true,  openUpper=true,  segs=len3  weak-unconditional-inner-slice
#     drawEdges=true,  openLower=false, openUpper=true,  segs=len3  weak-ignore-lower-open-flag
#     drawEdges=true,  openLower=true,  openUpper=false, segs=len3  weak-ignore-upper-open-flag
#     drawEdges=true,  openLower=true,  openUpper=true,  segs=len4  weak-short-run-drop-last
#     drawEdges=false, openLower=true,  openUpper=true,  segs=len3  weak-ignore-drawedges
#     drawEdges=true,  openLower=false, openUpper=false, segs=len3  weak-both-ends-closed-passthrough
#   so `drawEdges` is varied over true/false, `openLower` over true/false,
#   `openUpper` over true/false (and the two end flags over all FOUR joint
#   settings), and `segs` over lengths 3 and 4. No binder is pinned across the
#   battery: a rival that mishandled any single input is caught.
#
#   WITNESS METHOD NOTE: the carrier is transparent, so every witness closes by
#   `decide` at a concrete `List Nat`; no conditioning on an opaque term is
#   needed. Each witness elaborates against its rival and FAILS against the frozen
#   solution (verified with scripts/lean_verify.sh in both directions before
#   shipping). A pure reorder-only rival (right length, wrong order) is not only
#   expressible on this carrier (`List Nat` has DecidableEq) but SHIPPED, as
#   weak-reversed-selection-order. It is the case that earns the folding of the
#   sibling's two pins into one: every other rival changes the selected LENGTH at
#   its witness input, so a length-only spec would still reject them all, and
#   without a reorder rival the ELEMENT/ORDER half of the equality clause is
#   attested by nothing. Its faithfulness as a counterpart does not rest on the
#   modeled adjustment permuting anything — a counterpart only has to be a wrong
#   impl whose real analogue fails the test, and an ordered row-by-row comparison
#   fails on a reversed sequence.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
#   axiom (the selection is modeled directly; there are no `opaque` callees), so
#   there is nothing there to probe.
AXIOM_TESTS = []
