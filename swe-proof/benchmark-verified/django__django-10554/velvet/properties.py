"""properties.py — G-PBT falsification battery for django__django-10554 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct resolveOrderingTerm`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  resolveOrderingTerm (candidates : List Candidate) (querySelectLen : Nat)
      return (out : Disposition)
    require candidates ≠ []
    ensures out = disposition candidates querySelectLen

The method binds ONE ordering term against an ordered sequence of result-set
``candidates``: it walks them in order and binds the term to the first candidate
it lines up with; if none lines up, the trailing candidate's label decides
whether the term is REJECTED (labelled) or its source is APPENDED to the query's
select sequence and bound to ``querySelectLen + 1`` (unlabelled). The single
load-bearing ``ensures`` pins ``out`` to the deep, fully-unfolded ``disposition``
(the ``axioms`` region is empty — no opaque answer key to echo). ``disposition``
composes three independently-attackable top-level outcomes:

  * POSITION — a matched term takes the 1-based position of the FIRST candidate
    it lines up with (``(firstAligned …).map (· + 1)``).
  * APPENDED — no candidate lines up and the trailing candidate is UNLABELLED:
    the term binds to ``querySelectLen + 1`` (one past the pre-append length of
    the SEPARATE query-select sequence, whose length is the ``querySelectLen``
    binder — NOT ``candidates.length``).
  * REJECTED — no candidate lines up and the trailing candidate is LABELLED: the
    term cannot be placed.

TWO INPUT BINDERS: ``candidates`` (each element carries ``labelled`` and
``aligns``) and ``querySelectLen`` (the pre-append length of the query's select
sequence, observable only through the appended position). Both are load-bearing:
``candidates`` selects the branch (via the first alignment and the trailing
label) and the matched position; ``querySelectLen`` is the returned position on
the appended branch. The reject witnesses drive them to FOUR distinct input
points so the manifest demonstrates the post-image's dependence on which
candidate aligns, on the trailing label, on the matched position, and on
``querySelectLen`` — not on a single pinned shape (pts = 4).

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``resolveOrderingTermTester candidates querySelectLen
= false`` says the extracted program's result violates the postcondition at that
concrete input) and closes by ``decide``, checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict. ``decide`` reduces the extracted program by kernel computation; the
frozen program is a ``while`` loop over the candidate stream and its fixpoint is
opaque to the kernel, so a witness applied to the frozen solution gets STUCK (it
does not reduce to ``isTrue``/``isFalse``) — which is the required FAIL-on-gold
half. Each reject rival is therefore expressed as a LOOP-FREE impl that computes
its (wrong) disposition directly from the pure helpers, so its extracted tester
``decide``s over the concrete literal. This is a witnessing convenience, not a
weakening: the frozen spec is untouched and each rival's divergence from
``disposition`` is real at the witnessed input (both halves were checked with
``scripts/lean_verify.sh`` — every witness elaborates green against its rival and
gets stuck / fails against the frozen loop-based solution).

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (return the grounded model directly; name the
    exposed candidate in a local while keeping the loop and the frozen proof)
    must verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the sibling self-asserts that an F2P-shaped input satisfies
    its fractional-permission precondition. This backend's only ``require`` is
    ``candidates ≠ []`` (met by every non-empty input) and there is no permission
    surface, so that probe is degenerate; the residual risk on this domain is a
    DEGENERATE post-image. ``admiss-nondegenerate`` discharges an in-region
    ``assert`` pinning all THREE outcomes (position / appended / rejected) at
    F2P-shaped inputs; the impl is kept verbatim so the method's own obligation
    still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries this because a
    read-only sequence input is held at a fractional heap permission
    (``Acc(.,1/2)``) an impl can illegally overwrite. Lean/Velvet are
    referentially transparent: ``candidates`` is an immutable ``List Candidate``
    value declared read-only (not ``mut``), there is no heap and no aliasing, so
    there is no read-only input to overwrite and no permission system to trip.
    The class has no carrier analogue; NOT ported (fabricating a substitute would
    test nothing). See the footer for the case-by-case accounting.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``disposition
    candidates querySelectLen``, a fully-unfolded ``def`` over the method's own
    arguments; there is no answer-key term a wrong impl could echo. The cheapest
    correct impl computes the disposition honestly, which the positive controls
    cover.
  * CONTROL-FLOW-EFFECT (raise vs return) — the sibling's REJECT case is a raised
    exception where the other outcomes return. On this carrier that difference is
    modeled as a tagged value (``Disposition.rejected``), so it IS observable in
    the returned disposition and is attacked by the reject rivals below rather
    than being a control-flow effect invisible to the value abstraction.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (a matched position off by one,
    an unmatched-plain term rejected instead of appended, an unmatched-plain term
    bound to the wrong position, or an unmatched-labelled term appended instead
    of rejected).
"""
from pathlib import Path

INSTANCE = "django__django-10554"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Reject rivals that reshape the executable surface
# ---- into a loop-free closed form swap on this block.
_IMPL = """    -- impl-start
    let mut i := 0
    let mut res : Option Nat := none
    while i < candidates.length ∧ res = none
      invariant i ≤ candidates.length
      invariant match res with
                | some p => (firstAligned candidates).map (· + 1) = some p
                | none   => (firstAligned candidates).map (· + 1)
                              = (firstAligned (candidates.drop i)).map (· + (i + 1))
      done_with res ≠ none ∨ i = candidates.length
      decreasing (candidates.length - i) + (if res = none then 1 else 0)
    do
      if (candidates[i]!).aligns then
        res := some (i + 1)
      else
        i := i + 1
    match res with
    | some p => return Disposition.position p
    | none =>
      if lastLabelled candidates then
        return Disposition.rejected
      else
        return Disposition.appended (querySelectLen + 1)
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the loop-body lines, wholly inside the impl region and unique. The
# ---- loop-preserving positive reshapes only these (naming the exposed candidate
# ---- in a local `let`), leaving the loop, invariants and frozen proof intact.
_LOOP_BODY = """    do
      if (candidates[i]!).aligns then
        res := some (i + 1)
      else
        i := i + 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival that reshapes the impl into a single expression, or the
# ---- admissibility case that adds an in-region assert, retunes it without
# ---- touching the spec or dropping the `prove_correct resolveOrderingTerm`
# ---- obligation.
_PROOF_GOLD = """prove_correct resolveOrderingTerm by
  loom_solve
  all_goals (
    try (rw [firstAligned_shift candidates i (by omega)] at invariant_2)
    simp_all [disposition, lastLabelled, firstAligned_nil, Option.map])"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the impl is a single expression there is no
# ---- loop invariant to peel, so `loom_solve` alone discharges the equality (for
# ---- a correct reshape) or leaves it unsolved (for the reject rivals, which is
# ---- the point). Reject rivals retune the proof to this shape so the rejection
# ---- is attributable to the spec (via the witness), not to a proof script tuned
# ---- to a loop that no longer exists.
_PROOF_FLAT = "prove_correct resolveOrderingTerm by\n  loom_solve"


def _rewrite_impl(new_block, proof=_PROOF_FLAT):
    """Full variant: whole impl block replaced, proof retuned to the flat shape."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `resolveOrderingTermTester candidates querySelectLen = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped. Every argument is a concrete literal so `decide` reduces the
# ---- (loop-free) extracted rival program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for resolveOrderingTerm\n"
            "prove_precondition_decidable_for resolveOrderingTerm\n"
            "prove_postcondition_decidable_for resolveOrderingTerm\n"
            "derive_tester_for resolveOrderingTerm\n\n" + body)


def _C(labelled, aligns):
    """A concrete Candidate literal for a witness input point."""
    def b(x):
        return "true" if x else "false"
    return "{labelled := %s, aligns := %s}" % (b(labelled), b(aligns))


def _witness(candidates_literal, qsl):
    return _tester(
        f"example : resolveOrderingTermTester {candidates_literal} {qsl} "
        "= false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no loop at all — maximally structurally different from the gold forward
        # scan. `out` IS `disposition candidates querySelectLen`, so the ensures
        # holds trivially; the reproof is a bare `loom_solve` (no loop invariant
        # to peel).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return disposition candidates querySelectLen\n"
            "    -- impl-end"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`disposition candidates querySelectLen` directly (no loop). `out` IS "
            "that model, so the ensures holds on the whole domain; the reproof is "
            "`loom_solve`. If this fails to verify the spec is over-fit to the scan "
            "code shape (SPEC-TOO-STRONG). Also the honest no-ungrounded-echo "
            "control: the model is the real work, so a direct return is correct, "
            "not a cheat. (Sibling: pos-reorder — a structurally-different correct "
            "impl.)"),
    },
    {
        "id": "pos-control-named-candidate",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole loop, the invariants and the frozen proof script; only
        # names the exposed candidate in a local `let` before testing its
        # alignment. Observationally identical for every input.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "    do\n"
            "      let c := candidates[i]!\n"
            "      if c.aligns then\n"
            "        res := some (i + 1)\n"
            "      else\n"
            "        i := i + 1"),
        "rationale": (
            "naming the exposed candidate in a local `let c` before testing "
            "`c.aligns` scans the same stream with the same step, so `out = "
            "disposition candidates querySelectLen` still holds on the whole "
            "domain; the loop, invariants and frozen proof script are untouched. "
            "A correct reshape must verify, else the postcondition is "
            "SPEC-TOO-STRONG (rejects a faithful impl over the shape of the loop "
            "body). (Sibling: pos-reorder, reshaped to a loop-preserving form.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the method's only `require` (`candidates ≠ []`) is met by
    # every F2P-shaped input, so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here. The residual admissibility risk on
    # this domain is that the post-image is DEGENERATE at the interesting point —
    # a spec no impl distinguishes reads exactly like one every impl meets. This
    # case discharges an in-region `assert`, at three fully concrete F2P-shaped
    # inputs, that the post-image is NON-DEGENERATE: an aligning candidate yields
    # POSITION 1, an unmatched-unlabelled candidate at querySelectLen 3 yields
    # APPENDED 4 (the querySelectLen-driven position — the new behaviour), and an
    # unmatched-labelled candidate yields REJECTED — three genuinely distinct
    # outcomes. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the proof gains a `decide` arm to clear the
    # assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      disposition [" + _C(False, True) + "] 0 = Disposition.position 1 ∧\n"
                  "      disposition [" + _C(False, False) + "] 3 = Disposition.appended 4 ∧\n"
                  "      disposition [" + _C(True, False) + "] 3 = Disposition.rejected))\n"),
            _PROOF_GOLD,
            "prove_correct resolveOrderingTerm by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (try (rw [firstAligned_shift candidates i (by omega)] at invariant_2)\n"
            "       simp_all [disposition, lastLabelled, firstAligned_nil, Option.map])\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs: an aligning candidate must give POSITION 1, an "
            "unmatched-unlabelled candidate at querySelectLen 3 must give APPENDED "
            "4 (one past the query-select length — the appended-position behaviour "
            "the fix adds), and an unmatched-labelled candidate must give REJECTED "
            "— three distinct outcomes. The in-region assert must discharge (else "
            "the obligation is degenerate / the precondition too strong); the impl "
            "is kept verbatim so `out = disposition …` still verifies. (Sibling: "
            "admiss-match, re-aimed from precondition admissibility to post-image "
            "non-degeneracy since this backend's only require is `candidates ≠ []` "
            "and there is no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a LOOP-FREE
    # closed form (single expression over the pure helpers) so its extracted
    # tester `decide`s (see the CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-append-unmatched-labelled",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling w5-aliased-append: drop the reject outcome entirely, so
        # an unmatched term is ALWAYS appended — even when the trailing candidate
        # is labelled, where the spec pins REJECTED. Correct on POSITION and on
        # unmatched-unlabelled (APPENDED); diverges only on the unmatched-labelled
        # sub-domain.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (match (firstAligned candidates).map (· + 1) with\n"
            "      | some p => Disposition.position p\n"
            "      | none   => Disposition.appended (querySelectLen + 1))\n"
            "    -- impl-end"),
        "refinement": (
            "this is the shape whose faithful counterpart drops the guard that "
            "keeps an unmatched term whose trailing candidate is labelled from "
            "being placed: such a term would be silently appended and bound to a "
            "position instead of being refused. The failing scenario that pins an "
            "unmatched labelled term to REJECTION would then get a placed position "
            "instead of the refusal it asserts — it would NOT resolve. Correct on "
            "every matched term and on every unmatched-unlabelled term (a true "
            "partial-domain break)."),
        "rationale": (
            "REJECT from `out = disposition …` via the REJECTED outcome: when no "
            "candidate lines up and the trailing candidate is labelled the spec "
            "requires `Disposition.rejected`, but this returns `Disposition.appended "
            "(querySelectLen + 1)`. Verifying would be SPEC-TOO-WEAK (the "
            "labelled-no-match refusal unpinned). Refuted on the unmatched-labelled "
            "sub-domain. (Sibling: w5-aliased-append.)"),
        "witness": _witness("[" + _C(True, False) + "]", 0),
    },
    {
        "id": "weak-offby1-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling offby1-match: on a matched term, return one PAST the
        # first aligning candidate's position. Correct on APPENDED/REJECTED and
        # even on which branch fires; wrong on every matched position by one.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (match (firstAligned candidates).map (· + 1) with\n"
            "      | some p => Disposition.position (p + 1)\n"
            "      | none   => if lastLabelled candidates then Disposition.rejected\n"
            "                  else Disposition.appended (querySelectLen + 1))\n"
            "    -- impl-end"),
        "refinement": (
            "a faithful counterpart that pointed a matched ordering term one place "
            "past the candidate it lines up with would bind the term to the WRONG "
            "result-set column for every matched term; the scenarios that read the "
            "ordered rows back would get the wrong rows — it would NOT resolve. "
            "Correct on every unmatched term (a matched-position-only break)."),
        "rationale": (
            "REJECT from `out = disposition …` via the POSITION outcome: the spec "
            "pins a matched term to `(firstAligned …).map (· + 1)`, this rival adds "
            "one. Verifying would be SPEC-TOO-WEAK (the matched position unpinned). "
            "Refuted at a TWO-element list whose SECOND candidate aligns (so gold "
            "gives position 2, the rival 3) — this drives `aligns` to true, moves "
            "`candidates.length` beyond one, and exercises the first-alignment "
            "index, none of which the other rivals do. (Sibling: offby1-match.)"),
        "witness": _witness("[" + _C(False, False) + ", " + _C(False, True) + "]", 0),
    },
    {
        "id": "weak-append-wrong-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling append-wrong-pos: on the appended branch, bind to
        # `querySelectLen` (the PRE-append length) instead of `querySelectLen + 1`
        # (the new last position). Correct on POSITION/REJECTED and picks the right
        # branch; wrong only on the returned appended position, and diverges from
        # gold precisely in how `querySelectLen` maps to the position.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (match (firstAligned candidates).map (· + 1) with\n"
            "      | some p => Disposition.position p\n"
            "      | none   => if lastLabelled candidates then Disposition.rejected\n"
            "                  else Disposition.appended querySelectLen)\n"
            "    -- impl-end"),
        "refinement": (
            "a faithful counterpart that bound the appended term to the query "
            "select sequence's PRE-append length rather than its new last position "
            "would point the rewritten term at the column BEFORE the freshly added "
            "one; the union scenarios that assert specific ordered rows would get "
            "the wrong column — it would NOT resolve. Correct on every matched and "
            "every rejected term (an appended-position-only break)."),
        "rationale": (
            "REJECT from `out = disposition …` via the APPENDED position: the spec "
            "pins it to `querySelectLen + 1`, this rival returns `querySelectLen`. "
            "This is the sub-domain that proves `querySelectLen` is LOAD-BEARING — "
            "the witness fixes the candidate at unmatched-unlabelled and varies "
            "only `querySelectLen` (= 1, so gold gives APPENDED 2, the rival "
            "APPENDED 1); a rival mishandling only that binder is caught by no "
            "other witness. Verifying would be SPEC-TOO-WEAK (the appended position "
            "unpinned). (Sibling: append-wrong-pos.)"),
        "witness": _witness("[" + _C(False, False) + "]", 1),
    },
    {
        "id": "weak-reject-unmatched-plain",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling reject-all (the pre-patch shape): on any no-match, return
        # REJECTED unconditionally — dropping the appended outcome. Correct on
        # POSITION and on the unmatched-LABELLED sub-domain (where the spec also
        # rejects); diverges on the unmatched-unlabelled sub-domain, the whole
        # point of the change.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (match (firstAligned candidates).map (· + 1) with\n"
            "      | some p => Disposition.position p\n"
            "      | none   => Disposition.rejected)\n"
            "    -- impl-end"),
        "refinement": (
            "this is the pre-change behaviour: an unmatched term is ALWAYS refused, "
            "even when the trailing candidate is unlabelled and the term's source "
            "should instead be appended to the query's select sequence and bound to "
            "a fresh position. The union-by-plain-column scenarios that must return "
            "ordered rows would be refused outright — this is exactly the bug the "
            "change fixes, so it does NOT resolve. Correct on every matched term "
            "and on every unmatched-labelled term."),
        "rationale": (
            "REJECT from `out = disposition …` via the APPENDED outcome: when no "
            "candidate lines up and the trailing candidate is UNLABELLED the spec "
            "requires `Disposition.appended (querySelectLen + 1)`, but this returns "
            "`Disposition.rejected`. Verifying would be SPEC-TOO-WEAK (the "
            "unmatched-unlabelled append unenforced). Refuted on the "
            "unmatched-unlabelled sub-domain (`labelled` false) — the sub-domain "
            "the append-unmatched-labelled rival agrees with gold on, so the two do "
            "NOT share a witness. (Sibling: reject-all.)"),
        "witness": _witness("[" + _C(False, False) + "]", 0),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (1
# soundness positive, 1 admissibility, 6 uniqueness rivals — one of which is a
# mandatory frame-mutation rival) plus an EMPTY AXIOM lane (AXIOM_TESTS = []).
# The sibling contracts `relabel_order_term` over a full-permission mutable
# `List[int]` of column identities, where the APPEND path genuinely MUTATES that
# list (grows it by `src`) and the returned position is a 1-based ordinal. This
# backend models the SAME per-term binding DEEPLY and CONCRETELY (`firstAligned`
# / `lastLabelled` / `disposition` over the `Candidate` / `Disposition`
# carriers), but the returned `Disposition` observes only WHICH outcome fires and
# WHICH position — NOT the identity of any appended column (the appended-into
# sequence is refined to its LENGTH, `querySelectLen`, per mapping.md §1). That
# refinement narrows two sibling rivals away and makes the frame class vacuous.
#
#   sibling case              kind          -> here                          disposition
#   -------------------------------------------------------------------------------------
#   pos-reorder               soundness     -> pos-control-direct-model      RE-SHAPED
#                                              (+ pos-control-named-candidate ADDED)
#   admiss-match              admissibility -> admiss-nondegenerate          RE-AIMED
#   w5-aliased-append         uniqueness    -> weak-append-unmatched-labelled  PORTED
#   frame-match-write         uniqueness    -> (none)                        VACUOUS
#   offby1-match              uniqueness    -> weak-offby1-position          PORTED
#   append-wrong-pos          uniqueness    -> weak-append-wrong-position    PORTED
#   append-wrong-val          uniqueness    -> (none)                        VACUOUS (carrier)
#   reject-all                uniqueness    -> weak-reject-unmatched-plain   PORTED
#   AXIOM_TESTS (none)        axiom         -> (none)                        N/A (G-AX)
#
# 4 uniqueness ported, 1 admissibility re-aimed, 1 soundness re-shaped + 1 added;
# 2 uniqueness vacuous; axiom lane empty (nothing to port).
#
# RE-SHAPED (pos-reorder -> pos-control-direct-model): the sibling's positive is a
#   branch reorder (handle the no-match case first). On this carrier the
#   maximally-different correct impl is a loop-free direct return of the grounded
#   model `disposition …`; a second, loop-PRESERVING correct reshape
#   (pos-control-named-candidate) is ADDED so the soundness surface is defended
#   both from a completely different control-flow shape AND from a minimal edit
#   inside the frozen loop (which keeps the frozen proof intact).
# RE-AIMED (admiss-match -> admiss-nondegenerate): the sibling asserts an
#   F2P-shaped input satisfies its half-permission Requires. This backend's only
#   `require` is `candidates ≠ []` (met by every F2P input) and there is no
#   permission surface, so that probe is degenerate; the sharper residual risk is
#   a DEGENERATE post-image, so the case is re-aimed to a live in-region assert
#   pinning all THREE outcomes (position / appended / rejected) at F2P-shaped
#   inputs, including the querySelectLen-driven appended position the fix adds.
# PORTED (the four value/branch rivals): w5-aliased-append ports directly to
#   weak-append-unmatched-labelled (drop the reject outcome; refuted on the
#   unmatched-labelled sub-domain — the P2P `raises_on_non_selected_column`
#   analogue). offby1-match ports to weak-offby1-position (matched position off by
#   one; refuted at a length-2 list whose second candidate aligns).
#   append-wrong-pos ports to weak-append-wrong-position (appended position off by
#   one; refuted at querySelectLen 1, the witness that makes querySelectLen
#   load-bearing). reject-all ports to weak-reject-unmatched-plain (the literal
#   pre-patch shape; refuted on the unmatched-unlabelled sub-domain — the F2P
#   discriminator).
# VACUOUS (frame-match-write): the sibling's MANDATORY frame-mutation rival writes
#   to the full-permission `cols` list on the MATCH path (which the spec pins
#   unchanged there), and is rejected by the MATCH frame postcondition
#   `ToSeq(cols) == Old(ToSeq(cols))`. This backend is referentially transparent:
#   `candidates` is an immutable value declared read-only (not `mut`), there is no
#   heap, no aliasing, no `Old`, and no permission system. There is no read-only
#   input to overwrite and no frame clause to violate, so the class has no carrier
#   analogue. Omitted as a genuine carrier fact, NOT fabricated (porting map: this
#   class is vacuous on a referentially-transparent backend).
# VACUOUS-BY-CARRIER (append-wrong-val): the sibling's rival appends a DIFFERENT
#   column identity (`src + 1`) to the mutable list while returning the right
#   position, rejected by the sibling's APPEND value clause
#   `ToSeq(cols) == Old(ToSeq(cols)) + PSeq(src)`. On this carrier the appended
#   column's IDENTITY is not observable: `Disposition.appended n` carries only the
#   1-based POSITION, and the appended-into sequence is refined to its LENGTH
#   `querySelectLen` (mapping.md §1 — only the length determines the emitted
#   ordinal). There is no value in the returned disposition that records WHICH
#   source was appended, so a rival appending a different identity is
#   indistinguishable from gold on this carrier — it has no discriminating witness
#   and is DROPPED rather than faked (per the porting map: an abstraction the
#   sibling kept but this carrier collapses). The appended POSITION (the observable
#   half of that path) is instead attacked by weak-append-wrong-position.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = disposition
#   candidates querySelectLen` has TWO binders — `candidates : List Candidate`
#   (elements carry `labelled`, `aligns`) and `querySelectLen : Nat` — and
#   `disposition` has THREE independent top-level outcomes (position / appended /
#   rejected). The four reject witnesses probe four DISTINCT input points (pts=4):
#     * weak-append-unmatched-labelled  [C(labelled=T, aligns=F)] qsl 0
#     * weak-offby1-position            [C(F,F), C(F,T)]          qsl 0   (len 2)
#     * weak-append-wrong-position      [C(F,F)]                  qsl 1
#     * weak-reject-unmatched-plain     [C(F,F)]                  qsl 0
#   So `aligns` ranges over {T,F} (offby1's second element aligns; every other
#   point does not), `labelled` ranges over {T,F} (append-unmatched-labelled holds
#   it true, the rest false — and it is demonstrated load-bearing: it is the sole
#   binder distinguishing the append-unmatched-labelled and reject-unmatched-plain
#   witnesses, which sit at the SAME candidate shape but opposite labels),
#   `querySelectLen` ranges over {0,1} (append-wrong-position holds the candidate
#   fixed and varies ONLY querySelectLen, proving it load-bearing on the appended
#   branch), and `candidates.length` ranges over {1,2}. All THREE outcomes are
#   attacked: POSITION (weak-offby1-position), APPENDED — both which-branch
#   (weak-reject-unmatched-plain: rejected instead of appended) and the value
#   (weak-append-wrong-position: wrong appended position) — and REJECTED
#   (weak-append-unmatched-labelled: appended instead of rejected). No binder is
#   pinned at a single value across the reject set.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3: the changed op
#   is modeled deeply and concretely, validated by G-CONF, so G-AX is vacuous);
#   the sibling's AXIOM_TESTS is likewise empty. This gate ignores AXIOM_TESTS
#   regardless.
AXIOM_TESTS = []
