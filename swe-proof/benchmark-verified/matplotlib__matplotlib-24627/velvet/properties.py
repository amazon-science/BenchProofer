"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24627 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct clearAxes`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against a subject known to satisfy the spec. Here that subject is NOT the frozen
solution but a declared ``witness_reference`` (see ``_REFERENCE``): the frozen
impl's ``while`` loop extracts to a fixpoint the witness's ``simp`` cannot
reduce, so a build against gold fails for every claim regardless of truth and its
exit code discriminates nothing. AUDIT-REPAIRED; see the ``_witness`` preamble for
the three builds that measured this.)

DEFENDED SURFACE (one contracted method over a single sequence of items, each
viewed through the two boolean links the issue names):

  clearAxes (children : List Artist) return (out : List Artist)
    ensures out = deparentAll children      -- THE load-bearing (and only) clause

with the carrier and post-image fully unfolded in the ``pure`` region:

  structure Artist where hasAxes : Bool ; hasFigure : Bool
  deparent (_a) = { hasAxes := false, hasFigure := false }   -- BOTH links unset
  deparentAll []        = []
  deparentAll (a :: cs) = deparent a :: deparentAll cs        -- element-wise, in order

so the single clause pins THREE independent sub-behaviours of the desired
result (the input is the sequence of items that were attached before the clear;
the output is what each becomes):

  * FIRST-LINK: every returned item has its first link unset (``hasAxes = false``);
  * SECOND-LINK: every returned item has its second link unset (``hasFigure = false``)
    — unsetting only one link is NOT enough (``deparent`` clears BOTH);
  * EVERY-ITEM / ORDER: the result is one item per input item, IN ORDER, each
    independently deparented — no item is skipped and none is left attached.

``deparentAll`` is GROUNDED in the input (a total front-recursive fold over
``children``); the ``axioms`` region is empty (there is no opaque answer key to
echo — directive 8: the post-image is a concrete ``def`` over the method's own
argument), so there is no wrong-echo rival and the ungrounded-oracle probe is
replaced by two honest positive controls. The sole INPUT BINDER is ``children``,
whose length, contents (both fields), and element order all matter.

THE CARRIER IS TRANSPARENT (no opaque callee). A witness reaches the impl
through Velvet's extractor (``extract_program_for clearAxes`` gives
``clearAxesExec c = NonDetT.run (clearAxes c)``) and states ``clearAxesExec c ≠
DivM.res (deparentAll c)`` at a concrete ``c``. ``Artist`` derives only
``Inhabited, Repr`` (it is FROZEN, in the spec view — a variant may not add
``DecidableEq``), so a ``List Artist`` (in)equality does not go through
``decide``; the residual literal is closed by ``simp`` with the record
constructor-injectivity lemma (``Artist.mk.injEq``) plus the fold/``deparent``
unfoldings instead. The FROZEN impl carries a backward ``while`` loop whose
extracted program does NOT reduce under ``simp`` (the loop fixpoint stays stuck),
so each reject rival is a straight-line loop-free CLOSED FORM whose extracted
program DOES reduce.

That asymmetry is precisely why the frozen solution CANNOT serve as the
discriminating subject: "gold fails" is then a statement about tactic power, not
about the spec. An earlier revision of this battery relied on it, and an
anti-refutation forgery (asserting the rival AGREES with the spec at a point
where it does) cleared both halves — rival exit 0, gold exit 1 — and was recorded
as a refutation. Every reject case now declares a ``witness_reference``, and each
witness was re-derived with real builds: it leaves ``⊢ False`` against that
loop-free VERIFYING reference (exit 1 — the claim was evaluated against a correct
impl and found false), elaborates against its own rival (exit 0), and the same
forgery is now caught as ``witness-vacuous``.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this class
    (its per-member back-references are FULL-permission WRITE inputs and the
    surviving old members are handed back at half permission), but explicitly
    records ``has_readonly_input == False`` — there is no read-only half-permission
    INPUT to overwrite, so even on nagini the write-to-a-1/2-input weakness does
    not apply. Lean/Velvet are referentially transparent a fortiori: ``children``
    is an immutable value, this bundle declares NO ``mut`` binder over any input,
    and there is no heap and no aliasing. No substitute probe is fabricated (per
    the porting map: this class is vacuous on Lean/Velvet).
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. Each nagini
    partial-domain rival re-expresses directly onto one sub-behaviour of
    ``out = deparentAll children``.
  * UNGROUNDED-ORACLE ECHO — N/A. ``deparentAll`` is a total ``def`` over the
    method's own input; there is no answer key to echo. Replaced by the honest
    positive controls (the cheapest direct impl + a structurally different map).
  * ADMISSIBILITY / PRECOND-TOO-STRONG — APPLIES, and is CARRIED (a second audit
    landed it; the first revision wrongly recorded it vacuous "because there is no
    ``require``"). On a total carrier the analogue is the obligation being
    unsatisfiable or DEGENERATE at exactly an F2P-shaped input, which having no
    precondition does not rule out; see
    ``admiss-obligation-satisfiable-at-attached``.

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; the whole computation is a concrete fold over the input, validated
== the real patched clear routine by conformance_check.py / G-CONF — that is not
this gate's job, and the gate ignores ``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24627"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct clearAxes statement
# byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the backward per-item loop that
# prepends each deparented item and returns the accumulator). Reject rivals
# replace it with a loop-free closed form (so their extracted program reduces
# under simp); the positive controls replace it with an equivalent shape.
_IMPL = (
    "    let mut result : List Artist := []\n"
    "    let mut i := children.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ children.length\n"
    "      invariant result = deparentAll (children.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let a := children[i - 1]!\n"
    "      result := deparent a :: result\n"
    "      i := i - 1\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen prove_correct tactic body (the whole block, unique in the file and
# elided from the spec view). A CORRECT reshape may retune this block; every
# reject rival keeps it as-is (it fails to close the wrong loop-free impl, which
# is exactly the intended rejection, but the witness — not the tactic failure —
# is what the gate scores).
_PROOF = (
    "prove_correct clearAxes by\n"
    "  loom_solve\n"
    "  rw [deparentAll_drop_step children i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced (proof frozen)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


def _proof_only(new_proof):
    """Frozen impl kept verbatim; ONLY the elided tactic body replaced."""
    return _swap(_BASE, _PROOF, new_proof)


# The ADMISSIBILITY probe's in-region preamble (see the `admiss-*` case). It
# discharges, BEFORE the frozen obligation is closed verbatim, that the method's
# own Hoare triple is SATISFIABLE at one concrete F2P-shaped input — the shape the
# real failing test drives: several formerly-attached items, every link set. Each
# `have` is machine-checked LIVE (a same-shaped FALSE claim fails to elaborate;
# the measurements are in the case's rationale), so this is not decoration.
_ATT_L = "{ hasAxes := true, hasFigure := true }"
_DEP_L = "{ hasAxes := false, hasFigure := false }"
_ADMISS_PROOF = (
    "prove_correct clearAxes by\n"
    f"  have hreach : triple True (clearAxes [{_ATT_L}, {_ATT_L}])\n"
    f"      (fun out => out = deparentAll [{_ATT_L}, {_ATT_L}]) := by\n"
    "    unfold clearAxes\n"
    "    loom_solve\n"
    "    rw [deparentAll_drop_step _ i (by omega) (by omega)]\n"
    "    simp_all\n"
    f"  have hpost : deparentAll [{_ATT_L}, {_ATT_L}] = [{_DEP_L}, {_DEP_L}] := rfl\n"
    f"  have hnondeg : deparentAll [{_ATT_L}, {_ATT_L}] ≠ [{_ATT_L}, {_ATT_L}] := by\n"
    "    simp [deparentAll, deparent]\n"
    "  loom_solve\n"
    "  rw [deparentAll_drop_step children i (by omega) (by omega)]\n"
    "  simp_all")


# The SUBJECT every reject witness is refuted against, in place of the frozen
# solution. It is the same source as the `pos-control-direct` positive: a
# loop-free CORRECT impl of the frozen spec (`return deparentAll children`),
# which the gate re-verifies before use. Loop-free is the whole point — its
# extracted program reduces under the witness's `simp`, so a witness that fails
# here fails because the claim was EVALUATED and found false of a correct impl,
# not because a `forIn` fixpoint blocked the tactic. Machine-checked: each
# shipped witness leaves `⊢ False` against this reference (exit 1, a real
# refutation), whereas against gold it leaves the unreduced loop term.
_REFERENCE = _impl_reproved(
    "    return deparentAll children",
    "prove_correct clearAxes by\n  loom_solve")


# ---- witness preamble. The spec is a `method` CONTRACT over a transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `clearAxesExec c` is `NonDetT.run (clearAxes c)`; `≠ DivM.res
# ---- (deparentAll c)` says the impl's output contradicts the postcondition at
# ---- that concrete input. Checked in a file whose `prove_correct` block is
# ---- stripped, so no tactic script can mask the verdict. `Artist` has no
# ---- DecidableEq (it is frozen), so the residual List-Artist inequality is
# ---- closed by `simp` with the record injectivity lemma + fold unfoldings, NOT
# ---- `decide`.
# ----
# ---- THE SECOND SUBJECT IS NOT THE FROZEN SOLUTION — see `_REFERENCE` below.
# ---- The frozen impl's `while` loop extracts to a `forIn Lean.Loop.mk ...`
# ---- fixpoint wrapped in `invariantGadget`/`onDoneGadget`, which this `simp`
# ---- cannot reduce, so a build against gold leaves the goal with the loop term
# ---- still unevaluated and fails for EVERY claim regardless of truth. Measured
# ---- with three real builds: the shipped refutation, the exact OPPOSITE claim
# ---- (`clearAxesExec [dep] = DivM.res (deparentAll [dep])`, i.e. the rival
# ---- AGREES with the spec — an anti-refutation), and a true equation about
# ---- gold all fail against gold identically with `unsolved goals` over the
# ---- unreduced `forIn`. So gold's nonzero exit attests to nothing here, and the
# ---- anti-refutation forgery cleared both halves (rival exit 0, gold exit 1)
# ---- and was recorded as `rejected`. Every reject case therefore names a
# ---- `witness_reference`: a loop-free impl that VERIFIES against the frozen
# ---- spec and DOES reduce, so the refutation is checked by actually evaluating
# ---- a correct impl at the probed input. The gate independently re-checks that
# ---- the reference shares the frozen spec and verifies before trusting it, and
# ---- with the reference in place the same forgery is caught (`witness-vacuous`).
def _witness(inp: str) -> str:
    return ("extract_program_for clearAxes\n\n"
            f"example : clearAxesExec ({inp}) ≠ "
            f"DivM.res (deparentAll ({inp})) := by\n"
            "  unfold clearAxesExec clearAxes\n"
            "  simp [NonDetT.run, pure, deparentAll, deparent, "
            "Artist.mk.injEq, List.map]\n")


# Concrete Artist literals used by the witnesses.
_ATT = "{ hasAxes := true, hasFigure := true }"    # attached (both links set)
_DEP = "{ hasAxes := false, hasFigure := false }"  # deparented (both unset)
_FIGONLY = "{ hasAxes := false, hasFigure := true }"  # only second link set


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). `deparentAll children` is GROUNDED in the argument
    # (a total fold), so `return deparentAll children` is a correct fully-grounded
    # implementation, not an ungrounded-oracle echo — and it doubles as proof the
    # spec is not echo-vulnerable: any WRONG constant/echo fails
    # `out = deparentAll children`. The loop is gone, so the frozen proof's loop
    # reasoning is unneeded and the residual goal closes under `loom_solve` alone.
    # Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    return deparentAll children",
            "prove_correct clearAxes by\n  loom_solve"),
        "rationale": "the post-image `deparentAll children` is GROUNDED in the "
                     "input (a total fold, no opaque answer key), so "
                     "`return deparentAll children` is the honest cheapest CORRECT "
                     "impl. It MUST verify — the clause is literally "
                     "`out = deparentAll children` — else the single postcondition "
                     "clause is SPEC-TOO-STRONG. Also shows the spec is not "
                     "echo-vulnerable: any wrong constant/echo would fail the "
                     "clause.",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — a structurally DIFFERENT but CORRECT impl:
    # a FORWARD `.map deparent` over the whole sequence, replacing the frozen
    # BACKWARD accumulate-and-prepend loop. Same values on every input
    # (`(a :: cs).map deparent = deparent a :: cs.map deparent`, which is exactly
    # `deparentAll`'s cons clause), different control-flow shape and traversal
    # direction. The loop is gone, so the frozen proof is retuned to a short
    # structural induction closing `children.map deparent = deparentAll children`
    # (in-region only; the spec view is untouched). A faithful correct reshape
    # that could NOT verify would mean the postcondition is over-fit to the
    # backward-loop FORM => SPEC-TOO-STRONG. Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-control-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    return (children.map deparent)",
            "prove_correct clearAxes by\n"
            "  loom_solve\n"
            "  induction children with\n"
            "  | nil => rfl\n"
            "  | cons a rest ih => simp [deparentAll_cons, ih]"),
        "rationale": "structurally different CORRECT impl: a FORWARD map "
                     "(`children.map deparent`) rather than the frozen backward "
                     "accumulate loop. Observationally identical on every input "
                     "(the map's cons law is `deparentAll`'s cons clause), so "
                     "`out = deparentAll children` holds on the whole domain. The "
                     "proof is retuned in-region to a short induction. A faithful "
                     "reshape MUST verify, else the clause is over-fit to the "
                     "backward-loop FORM => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — LANDED UNDER AUDIT. The earlier
    # revision recorded this lane VACUOUS on the grounds that the bundle declares
    # no `require`, so "there is no precondition to admit". That reason is wrong:
    # on a total carrier the analogue is the OBLIGATION being unsatisfiable at
    # exactly an F2P-shaped input, which the absence of a `require` does not rule
    # out. This case tests that direction directly: the frozen impl is kept
    # BYTE-FOR-BYTE (only the elided tactic body changes) and the proof first
    # discharges, at one concrete F2P-shaped input, that the method's own triple
    # is SATISFIABLE there — several formerly-attached items, every link set,
    # which is the shape the real failing test drives.
    #
    # Each `have` is LIVE, measured out-of-band with real builds:
    #   * `hreach` at the same input with the post-image literal changed to a
    #     THREE-element list (identical syntactic shape, false claim) FAILS to
    #     elaborate (exit 1), while the true form elaborates (exit 0);
    #   * a projection pair over the same triple confirms the same asymmetry —
    #     `out.length = 2` elaborates (exit 0), `out.length = 3` does not (exit 1);
    #   * `hpost` with the claimed result changed to `[att, dep]` FAILS (exit 1,
    #     `Type mismatch`), so `rfl` is really evaluating the fold, not accepting
    #     anything;
    #   * `hnondeg` flipped to an EQUALITY fails (exit 1, `unsolved goals`).
    # So had the obligation been unsatisfiable at this F2P-shaped point, or its
    # post-image degenerate there (equal to the untouched input), this case would
    # FAIL rather than pass quietly. The frozen `require`/`ensures` are untouched
    # and the frozen tactic script still closes the real obligation afterwards, so
    # nothing is weakened.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-attached",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof_only(_ADMISS_PROOF),
        "rationale": "PASS SOURCE = the method's own Hoare triple is SATISFIABLE "
                     "at a concrete F2P-shaped input (two items, BOTH links set on "
                     "each — the state the real failing test sets up before the "
                     "clear). `hreach` EVALUATES the method there and closes the "
                     "postcondition; `hpost` computes the post-image at that input "
                     f"to `[{_DEP_L}, {_DEP_L}]` by `rfl`; `hnondeg` shows the "
                     "post-image is NON-DEGENERATE there (it differs from the "
                     "untouched input, so the clause is not satisfied by doing "
                     "nothing). If the obligation admitted no F2P-shaped input, or "
                     "were degenerate at one, this case would FAIL => "
                     "PRECOND-TOO-STRONG. The impl is the frozen one verbatim and "
                     "only the elided tactic body changes, so the spec is untouched "
                     "and the real obligation is still closed by the frozen script. "
                     "Each `have` is machine-checked live: the same `hreach` shape "
                     "claiming a three-element post-image fails (exit 1) where the "
                     "true one elaborates (exit 0), `out.length = 2` elaborates "
                     "where `out.length = 3` fails, a wrong `hpost` literal fails, "
                     "and a flipped `hnondeg` fails.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test. Each rival
    # keeps the frozen backward-loop proof (which cannot close the loop-free impl,
    # the intended rejection); the witness is what attributes the rejection to the
    # spec, not the tactic failure.
    # =====================================================================

    # ---- SECOND-LINK clause: unset only the first link, leave the second set ----
    {
        "id": "weak-first-link-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct shape (one item per item, in order) and correct on the first
        # link, but leaves each item's SECOND link at its input value — so an item
        # that was attached comes back with its second link still set.
        "module": _impl(
            "    return (children.map (fun a => "
            "{ hasAxes := false, hasFigure := a.hasFigure }))"),
        "refinement": "its faithful real counterpart unsets only the first link "
                      "and leaves the second link untouched — so after the clear "
                      "every formerly-attached item still reports its second link "
                      "as set. The failing test asserts BOTH links are unset on "
                      "every former item, so this counterpart would NOT resolve.",
        "rationale": "REJECT from `out = deparentAll children` (SECOND-LINK half): "
                     "`deparent` unsets BOTH links, but the rival copies the second "
                     "link through, so on any item whose second link is set the "
                     f"result disagrees. Refuted at `[{_ATT}]`: gold returns "
                     f"`[{_DEP}]`, the rival `[{_FIGONLY}]`. Varies `children` to a "
                     "single attached item (both links set).",
        "witness": _witness(f"[{_ATT}]"),
        "witness_reference": _REFERENCE,
    },

    # ---- FIRST-LINK clause: unset only the second link, leave the first set ----
    {
        "id": "weak-second-link-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of the previous: unset only the second link, leave the first at
        # its input value. Correct shape; each formerly-attached item comes back
        # with its FIRST link still set.
        "module": _impl(
            "    return (children.map (fun a => "
            "{ hasAxes := a.hasAxes, hasFigure := false }))"),
        "refinement": "its faithful real counterpart unsets only the second link "
                      "and leaves the first link untouched — the exact defect the "
                      "issue reports (after the clear the first link still points "
                      "back at the container). The failing test asserts the first "
                      "link is unset on every former item, so this would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = deparentAll children` (FIRST-LINK half): "
                     "`deparent` unsets BOTH links, but the rival copies the first "
                     "link through, so on any item whose first link is set the "
                     f"result disagrees. Refuted at `[{_ATT}, {_ATT}]`: gold "
                     f"returns `[{_DEP}, {_DEP}]`, the rival two first-link-set "
                     "items. Varies `children` to a length-2 all-attached list (a "
                     "distinct point from every other rival).",
        "witness": _witness(f"[{_ATT}, {_ATT}]"),
        "witness_reference": _REFERENCE,
    },

    # ---- EVERY-ITEM clause (position 0): leave the FIRST item attached ----
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Deparent every item EXCEPT the first, which is copied through unchanged.
        # Correct shape and correct on the rest of the domain; diverges only on the
        # single first item whenever it was attached.
        "module": _impl(
            "    return (match children with "
            "| [] => [] | a :: rest => a :: rest.map deparent)"),
        "refinement": "a partial-domain counterpart that deparented every item "
                      "except the first (e.g. iterating the tail only) would leave "
                      "that one former item still fully attached. The failing test "
                      "checks EVERY former item — the first among them — so this "
                      "would NOT resolve. Tests that the clause pins every item, "
                      "not most items.",
        "rationale": "REJECT from `out = deparentAll children` (EVERY-ITEM at "
                     "position 0): `deparentAll` deparents the first item like the "
                     "rest, but the rival copies it through, so the lists disagree "
                     f"whenever the first item was attached. Refuted at "
                     f"`[{_ATT}, {_DEP}]`: gold returns `[{_DEP}, {_DEP}]`, the "
                     "rival leaves the first item attached. Discrimination comes "
                     "from the FIRST element of `children`.",
        "witness": _witness(f"[{_ATT}, {_DEP}]"),
        "witness_reference": _REFERENCE,
    },

    # ---- EVERY-ITEM clause (last position): leave the LAST item attached ----
    {
        "id": "weak-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Deparent every item EXCEPT the last, which is copied through unchanged.
        # Correct shape and correct on all but the final item; diverges only on the
        # last item whenever it was attached.
        "module": _impl(
            "    return ((children.dropLast.map deparent) ++ "
            "children.drop (children.length - 1))"),
        "refinement": "a partial-domain counterpart that stopped one short of the "
                      "end (e.g. iterating all but the last item) would leave the "
                      "final former item fully attached. The failing test attaches "
                      "several items and checks EVERY one — the last among them — "
                      "so this would NOT resolve.",
        "rationale": "REJECT from `out = deparentAll children` (EVERY-ITEM at the "
                     "last position): `deparentAll` deparents the final item like "
                     "the rest, but the rival copies it through, so the lists "
                     f"disagree whenever the last item was attached. Refuted at "
                     f"`[{_DEP}, {_ATT}]`: gold returns `[{_DEP}, {_DEP}]`, the "
                     "rival leaves the last item attached. Discrimination comes "
                     "from the LAST element of `children` (a near-miss the "
                     "skip-first rival does not subsume — distinct position).",
        "witness": _witness(f"[{_DEP}, {_ATT}]"),
        "witness_reference": _REFERENCE,
    },

    # ---- prepatch twin: deparent NOTHING, return the sequence unchanged ----
    {
        "id": "weak-no-deparent",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: the container's own reference to its items is
        # dropped elsewhere, but no item is deparented — each keeps both links. The
        # returned sequence is the input verbatim.
        "module": _impl("    return children"),
        "refinement": "this is the pre-patch behaviour verbatim: the routine "
                      "emptied the container's own collection but never touched the "
                      "items that had been in it, so each keeps BOTH links pointing "
                      "back — observable as the reported bug (after the clear the "
                      "link still reads as the container). The failing test asserts "
                      "both links are unset on every former item, so this does NOT "
                      "resolve (it is exactly the state the fix removes).",
        "rationale": "REJECT from `out = deparentAll children`: `deparentAll` "
                     "unsets both links of every item, but the rival returns the "
                     "input unchanged, so on any item with a link set the lists "
                     f"disagree. Refuted at `[{_FIGONLY}]`: gold returns `[{_DEP}]`, "
                     "the rival returns the item with its second link still set. "
                     "Varies `children` to a single item with the second link set "
                     "and the first already unset (a mixed-link point the "
                     "single-link rivals do not probe).",
        "witness": _witness(f"[{_FIGONLY}]"),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus an EMPTY AXIOM lane. This
# bundle models the SAME purely-functional core — the deparenting of every
# formerly-attached item (unset BOTH links, in order) — over `List Artist`
# instead of the sibling's mutable `Container.members` carrier with fractional
# permissions. The value surface (which links are unset, on which items, in what
# order) carries across intact; the permission surface does not.
#
#   sibling case              -> here                        disposition
#   ---------------------------------------------------------------------------
#   pos-rebind-after          -> pos-control-map             PORTED (re-expressed)
#   pos-swap-fields           -> pos-control-direct          PORTED (re-expressed)
#   admiss-readable-fields    -> admiss-obligation-satisfiable-at-attached
#                                                            RE-AIMED (audit)
#   weak-host-only            -> weak-second-link-only       PORTED
#   weak-canvas-only          -> weak-first-link-only        PORTED
#   weak-skip-first           -> weak-skip-first             PORTED
#   weak-skip-last            -> weak-skip-last              PORTED
#   weak-no-deparent          -> weak-no-deparent            PORTED
#   weak-no-empty             -> (none)                      NOT MODELED (see below)
#   AXIOM_TESTS ([])          -> (none)                      DROPPED (G-AX/G-CONF)
#   frame-mutation            -> (none)                      VACUOUS
#
# 5 rivals ported, 2 positives ported (re-expressed), 1 rival not modeled, 1
# admissibility RE-AIMED and landed, frame vacuous, axiom lane dropped = 8 SPEC
# cases (2 soundness, 1 admissibility, 5 uniqueness).
#
# PORTED (2 positive controls): the sibling's pos-swap-fields is a field-write
#   REORDER (clear the second link before the first) — order-independent, both
#   writes land. Here `deparent` unsets both links in one record literal, so the
#   analogous "both links still land, reshaped control flow" positive is the
#   cheapest grounded impl `return deparentAll children` (loop removed, residual
#   goal closes under `loom_solve` alone). The sibling's pos-rebind-after keeps
#   the de-parenting loop but reshapes its control flow (rebind the collection
#   AFTER the loop rather than before); here the analogous structural reshape is a
#   FORWARD `children.map deparent` replacing the BACKWARD accumulate loop —
#   different traversal direction, identical values, proof retuned in-region to a
#   short induction. Both verified to build.
# PORTED (5 partial-domain rivals): the two single-field sibling rivals
#   (weak-host-only / weak-canvas-only) re-express onto the two link sub-behaviours
#   of `deparent` (SECOND-LINK / FIRST-LINK — note the naming swap is only because
#   the sibling's "host"/"canvas" fields have no fixed order on this carrier; each
#   attacks one link). weak-skip-first / weak-skip-last port DIRECTLY as the
#   position-0 and last-position EVERY-ITEM probes. weak-no-deparent ports as the
#   return-input-unchanged prepatch twin. Each carries a machine-checked witness
#   that ELABORATES against its loop-free rival and FAILS — by reducing to `False`,
#   not by a stuck term — against the loop-free VERIFYING `_REFERENCE`.
# NOT MODELED (weak-no-empty): the sibling's clause (1) is `len(self.members) ==
#   0` — the container must EMPTY its own collection. On this carrier the modeled
#   result is the sequence of formerly-attached items with each DEPARENTED; the
#   container's own post-clear collection (the analogue of `self._children = []`)
#   is NOT part of the modeled output (mapping.md §2/§3.2: "the order-irrelevant
#   collection rebuild is not modeled" — only the set/unset status of each former
#   item's two links is). So there is no spec binder for "the collection is empty"
#   and no rival can attack it here: a rival that forgot to empty the collection is
#   indistinguishable on the modeled surface. This is carrier narrowing, NOT a
#   dropped-because-hard case — the F2P test the model targets asserts the link
#   status, and clause (1) is exercised by a separate observable the Lean-family
#   bundle does not model. Reported here as a known narrowing gap, not omitted
#   silently.
# RE-AIMED (admiss-readable-fields -> admiss-obligation-satisfiable-at-attached):
#   LANDED UNDER AUDIT; the previous revision recorded this lane VACUOUS and that
#   was a DEFECT, not a carrier fact. Its reason was "this bundle declares no
#   `require`, so there is no precondition to admit". That is exactly the reason
#   the porting map rejects: on a total carrier the analogue of PRECOND-TOO-STRONG
#   is the OBLIGATION being unsatisfiable (or degenerate) at exactly an F2P-shaped
#   input, which the absence of a `require` does not rule out. The rest of the old
#   argument was circular as well — "the gold impl and the positive controls
#   witness satisfiability" is the observation that G-VERIFY passed, which cannot
#   fail unless the bundle is already broken, so the PRECOND-TOO-STRONG direction
#   went untested. The sibling's probe re-aims cleanly: where it READS a member's
#   fields to show the permission is really granted, this one EVALUATES the
#   method's own triple at a concrete F2P-shaped input (two items, both links set)
#   as a `have`, before closing the frozen obligation verbatim, and additionally
#   shows the post-image is non-degenerate there. Every `have` was measured live
#   against a same-shaped false claim; see the case's rationale.
# VACUOUS (frame-mutation): the sibling itself records `has_readonly_input ==
#   False` — its per-member back-references are FULL-permission WRITE inputs, so
#   even on nagini the write-to-a-half-permission-input weakness does not apply.
#   This backend is referentially transparent and declares no `mut` binder —
#   `children` is an immutable value with no heap footprint — so there is no
#   read-only input to overwrite and no substitute probe. Not fabricated.
# DIVERGENCE lane - the class is CLOSED BY THE SEMANTICS here, and a diverging
#   rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   axiom `ensures` and declares no deep-model reference (`deparentAll` is
#   concrete list arithmetic, validated == the real patched clear by G-CONF), so
#   there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has a single input binder,
#   `children : List Artist`, and a single top-level clause,
#   `out = deparentAll children`, with three independent sub-behaviours
#   (first-link, second-link, every-item/order). The five reject witnesses probe
#   FIVE DISTINCT input points:
#     [att]                -> SECOND-LINK  (len 1; second link set)
#     [att, att]           -> FIRST-LINK   (len 2; first links set)
#     [att, dep]           -> EVERY-ITEM pos 0 (first item attached)
#     [dep, att]           -> EVERY-ITEM last  (last item attached)
#     [figonly]            -> prepatch twin (len 1; mixed links: first unset,
#                             second set — the one input the others never probe)
#   so `children` is genuinely varied in length (1, 2, 2, 2, 1), in element order
#   (skip-first vs skip-last are the same shape at swapped positions), and in the
#   contents of BOTH fields (first link: set in [att]/[att,att]/[att,dep],
#   already-unset in [figonly]; second link: set in [att]/[att,att]/[figonly],
#   unset in [dep]-carrying points). Both fields of `Artist` are abused by some
#   rival, and each sub-behaviour is attacked by at least one rival. The two
#   positive controls defend the whole obligation. No two rivals share an input
#   point. pts = 5 distinct input points across 5 witnesses.
# WITNESS DISCRIMINATION (re-derived under audit with real builds per reject
#   case): each witness ELABORATES against its loop-free rival (exit 0 — the
#   extracted program reduces, and the record-injectivity `simp` closes the
#   inequality at the probed input) and FAILS against the loop-free VERIFYING
#   `_REFERENCE` (exit 1, residual `⊢ False`) — the claim is EVALUATED against a
#   correct impl and found false there, which is what makes the refutation
#   attributable to the spec.
#
#   It is deliberately NOT refuted against the frozen solution. Gold's `while`
#   extracts to a `forIn Lean.Loop.mk` fixpoint under `invariantGadget`/
#   `onDoneGadget` that this `simp` cannot reduce, so a gold build fails with
#   `unsolved goals` over the unreduced loop for EVERY claim regardless of truth —
#   measured on the shipped refutation, on a TRUE equation about gold, and on an
#   anti-refutation forgery alike. Gold's exit code therefore carries no
#   information about discrimination, and the forgery was recorded as a refutation
#   before this repair; with `witness_reference` in place it is caught
#   (`witness-vacuous`). Note the gate's own stuck-reduction screen does not fire
#   here: it matches `decide`'s "did not reduce to isTrue/isFalse", whereas this
#   failure arrives as `simp` leaving `unsolved goals`.
#
#   No witness binds a hypothesis (the carrier is transparent), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears.
#
# SPEC PROBES RUN UNDER THE SECOND, INDEPENDENT AUDIT (no spec defect found;
#   nothing shipped from these). Re-derived from scratch rather than trusting the
#   first audit's numbers, and the first round of them was WRONG in an instructive
#   way: 3 of my own CORRECT reshapes (`(children.reverse.map deparent).reverse`,
#   a `foldl`-append accumulator, a `map` through a vacuous `if`) came back
#   rejected under a script I had called "deliberately strong", which would have
#   read as a SPEC-TOO-STRONG hole. It was my script: the residual goal is
#   `<shape> = deparentAll children`, needing a real structural induction, and all
#   3 VERIFY (exit 0) once the induction is supplied. The lesson is the one the
#   playbook states — a D-probe rejection means nothing without a control proving
#   the same script closes a correct impl — so every D rejection below was re-run
#   under the induction script that provably closes those reshapes.
#   SPEC-TOO-WEAK (attack D, 6 NEW wrong impls beyond both the 5 shipped rivals
#   and the first audit's 9, aimed at what those leave unattacked): NEGATE the
#   second link rather than copying it; a length-preserving all-first-link-SET
#   constant; DUPLICATE the first item (length off by one at the front); replace
#   the last item with `default` rather than skipping it; wrong ONLY on the empty
#   list (`[]` — the one input no shipped witness probes); and wrong only at
#   length ≥ 3 (a deeper sub-domain evasion than any shipped rival). All 6
#   REJECTED (exit 1) under the induction script whose controls — `children.map
#   deparent` and `(children.reverse.map deparent).reverse` — both VERIFY (exit 0)
#   under that same script. So the rejections are the clause, not the tactic.
#   SPEC-TOO-STRONG (attack E, 4 NEW correct reshapes): the double-reverse map,
#   an append-accumulating `foldl`, a `map` through a vacuous `if` on the first
#   link, and a `foldr` cons-accumulator all VERIFY (exit 0) with in-region proofs
#   only. A fifth, `(children.map deparent).reverse`, is the sharpest one here —
#   the deparented list is constant-valued, so reversing it is faithful even
#   though it scrambles traversal order — and it too VERIFIES (exit 0) once proven
#   through a `List.replicate` bridge plus `List.reverse_replicate`. It is worth
#   recording that it FAILS (exit 1) under a naive induction script, i.e. this
#   clause is shape-agnostic but not effortlessly so.
#   CARRIER NOTE (why no reject rival attacks `[]`): `deparentAll [] = []` and
#   every wrong impl that is wrong ONLY at `[]` must return a non-empty list
#   there, which the clause rejects — confirmed by the `D3_emptyevade` probe
#   above. So the empty list is defended by the clause, but no INEQUALITY witness
#   can be stated at it (`[] ≠ []` is false), which is why the reject lane's five
#   input points are all non-empty. That is a carrier fact, not a coverage gap.
# FIRST-AUDIT PROBES (re-reported for continuity, not re-run here).
#   SPEC-TOO-WEAK: 9 NEW wrong impls beyond the 5 shipped rivals — all-items-
#   second-link-set, return [], drop one item, SWAP the two links, deparent only
#   when length ≥ 2, an extra appended item, deparent only when non-empty,
#   deparent the first item only, and a length-preserving all-first-link-set
#   constant — were each given a deliberately STRONG proof script (map/replicate
#   bridging lemmas + `grind`); a control carrying the frozen impl under that same
#   script verifies (exit 0), and all 9 rivals were REJECTED (exit 1). The clause
#   admits no wrong impl these reach.
#   SPEC-TOO-STRONG: 4 NEW correct reshapes — `(children.map deparent).reverse`,
#   `List.replicate children.length {false,false}`, a `foldr` cons-accumulator,
#   and `children.map (fun _ => default)` — were each PROVEN against the frozen
#   spec (exit 0) with in-region proofs only. The clause is shape-agnostic: it
#   rejects nothing faithful, so it is not over-fit to the backward-loop form.
AXIOM_TESTS = []
