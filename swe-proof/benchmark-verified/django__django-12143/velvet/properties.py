"""properties.py — G-PBT falsification battery for django__django-12143 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct editedObjectPks`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method: the in-order selection over the
request items):

    editedObjectPks (pfx pkname : List Char)
                    (items : List (List Char × List Char)) return (out : List (List Char))
      ensures out = editedPks pfx pkname items

``editedPks pfx pkname items`` is a total, fully-unfolded pure function: walk
the ``(key, value)`` items in order and keep the VALUE of every item whose key
``matchesKey pfx pkname``. The per-key decision ``matchesKey`` — decompose the
key as the exact characters of ``pfx``, a ``'-'`` separator, a NON-EMPTY run of
decimal digits, a ``'-'`` separator, then the exact characters of ``pkname``,
ending the key — is a GROUNDED pure function of the inputs, spelled out in the
spec-view ``pure`` region (``matchesKey`` / ``stripPrefix`` / ``takeDigits`` /
``atEnd``). It is NOT an opaque answer key: it computes over the actual input
carrier, and the crucial property is that ``pfx`` and ``pkname`` are matched as
EXACT character sequences (no code point is treated as having a distinguished
regex meaning). The single load-bearing ``ensures`` clause pins the WHOLE result
list — its length, its element order, its per-item projection (value not key),
and the per-key acceptance decision — to ``editedPks pfx pkname items``.

The three inputs ``pfx`` / ``pkname`` / ``items`` are all FREE: the ``ensures``
holds for EVERY value of each. There is no ``require`` clause. Under
``set_option loom.semantics.termination "total"`` the selection must terminate,
so a diverging body cannot discharge the postcondition vacuously.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Structurally different but
    behaviourally identical impls (the accumulating loop collapsed to the
    closed form the post-image names; the per-item selection expressed as a
    ``filterMap``; a ``let``-bound reshape of the loop body) must still verify,
    else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method carries no ``require`` clause, so the "a normal
    input satisfies the precondition" probe is not where the risk sits. The
    residual risk is that the post-image is DEGENERATE at the interesting point.
    ``admiss-grounded`` discharges an in-region assert pinning, at concrete
    inputs, that the post-image ACCEPTS a matching key (keeping its value),
    REJECTS a non-matching key (keeping nothing), AND — the load-bearing point —
    accepts a matching key whose ``pfx`` carries a regex metacharacter (``'$'``),
    which the exact-sequence matcher treats literally. The impl and proof
    survive so the method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling holds its list
    inputs at a fractional heap permission (``Acc(., 1/2)`` / ``Acc(., 1/4)``)
    an impl can illegally overwrite, and ships rivals that mutate the read-only
    inputs (append to ``key`` / ``prefix`` / the helper ``lit``). Lean and Velvet
    are referentially transparent: ``pfx`` / ``pkname`` / ``items`` are immutable
    values (none declared ``mut``), there is no heap and no aliasing, so there is
    no read-only input to mutate and no substitute probe. Not fabricated —
    reported as an omission in the footer.
  * DIVERGENCE / non-termination - the class is CLOSED BY THE SEMANTICS here,
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
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired selection on some sub-domain and MUST be rejected:
    the headline pre-patch bug (a ``pfx`` carrying the end-of-input metacharacter
    ``'$'`` treated specially so a matching row is silently dropped — the exact
    data-loss the gold escape fix repairs), the matcher IGNORED (keep every
    value), the wrong projection (emit the key instead of the value), and the
    empty selection (contribute nothing). Three further rivals INLINE their own
    per-key decision over the frozen sub-helpers and weaken exactly ONE conjunct
    of it — the non-empty index run, the second ``'-'`` separator, and the
    end-of-input tolerance (this last in the too-STRICT direction, dropping a
    value the spec keeps) — each refuted at a near-miss key satisfying every
    other conjunct. Each is a loop-free closed form (so its tester
    kernel-reduces) with a machine-checked refutation witness.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method``
CONTRACT, not a bare predicate, so a witness reaches it through Velvet's own
tester machinery: ``editedObjectPksTester pfx pkname items = false`` says the
extracted program's result violates the postcondition at that concrete input,
checked in a file whose ``prove_correct`` block has been stripped (no tactic
script can mask the verdict). The frozen program contains a ``while`` loop,
whose fixpoint does not reduce under the kernel's ``decide``; every reject rival
is reshaped into a LOOP-FREE closed form, so ITS tester ``decide``s while the
SAME witness applied to the loop-bearing frozen solution cannot reduce and so
fails to elaborate. ``matchesKey`` and ``editedPks`` are structurally recursive
and reduce on the small concrete literal keys the witnesses use, so the tester
evaluates to a ground boolean.

READ THE GOLD-SIDE FAILURE HONESTLY. The gate's required FAIL-on-gold is
therefore a STUCK REDUCTION, not a semantic refutation: the frozen program's
``while`` fixpoint leaves ``decide`` unable to reduce the ``Decidable`` instance
to ``isTrue``/``isFalse``. Read alone that is a weak signal — a witness could
fail on gold for that reason while asserting something FALSE about the rival's
behaviour too, and the gate could not tell. What closes the gap is a third
build the gate does not run, so it is recorded here: every witness below was
additionally built against a CORRECT LOOP-FREE impl (``return editedPks pfx
pkname items``, the ``pos-closed-form`` shape), which reduces exactly as the
rivals do and is observationally the frozen program. On that control every
witness fails with ``decide`` PROVING the proposition FALSE — i.e. the tester is
``true`` there, the postcondition HOLDS at that input, and the refutation is
specific to the rival's wrong value rather than to the loop's opacity. That
control, not the stuck build on gold, is what makes each rejection attributable
to the spec. Measured exit codes: rival 0, gold 1 (stuck), correct-loop-free
control 1 (``decide`` proved false) for all seven reject cases.

WITNESS PLACEMENT. The seven rejects probe seven DISTINCT input points, so all
three binders are genuinely varied rather than pinned: ``pfx`` ranges over
``['f','$'] / ['f'] / ['g'] / ['f']``, ``pkname`` over ``['a'] / ['b'] / ['a']
/ ['i','d']``, and ``items`` over a matching ``'$'``-prefixed key / a
non-matching key / a matching key / a matching multi-char-``pkname`` key / three
NEAR-MISS keys (an absent index run, a non-``'-'`` second separator, and an
accepted key carrying one trailing line terminator). The variation is meaningful
rather than two spellings of one point: each near-miss key satisfies every
conjunct of the frozen decision EXCEPT the one its rival weakens, so it is the
only kind of input that separates an impl applying the full decision from one
missing a single clause. A rival that mishandled only a fixed prefix, name, or
item shape would still be caught.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the per-key
matcher is modeled deeply (an A-reference the R/I legs differential-test —
G-CONF's job — against the real ``re.escape``-fixed compiled pattern), not a
consumed contract. The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12143"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating loop over
# the request items. Reject rivals replace this with a loop-free closed form (so
# their tester reduces under `decide`); some positive controls do too.
_IMPL = """    -- impl-start
    let mut result : List (List Char) := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant result = editedPks pfx pkname (items.drop i)
      done_with i = 0
      decreasing i
    do
      let kv := items[i - 1]!
      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
      i := i - 1
    return result
    -- impl-end"""

# The three per-iteration loop lines; a positive control may reshape them while
# keeping the loop and the invariant, so the frozen proof still closes.
_LOOP_BODY = """      let kv := items[i - 1]!
      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
      i := i - 1"""

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by a retuned proof without disturbing the method's
# obligation.
_IMPL_TOP = "    let mut result : List (List Char) := []"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A positive control that collapses the loop to the closed form the
# post-image names retunes this; the tactic body is elided from the spec view,
# so this is a proof reshape, not a spec change.
_PROOF = """prove_correct editedObjectPks by
  loom_solve
  rw [editedPks_drop_step pfx pkname items i (by omega) (by omega)]
  simp_all"""

# sanity: the anchors appear verbatim & uniquely in the frozen solution.
assert _BASE.count(_IMPL) == 1, "IMPL anchor drift"
assert _BASE.count(_LOOP_BODY) == 1, "LOOP_BODY anchor drift"
assert _BASE.count(_IMPL_TOP) == 1, "IMPL_TOP anchor drift"
assert _BASE.count(_PROOF) == 1, "PROOF anchor drift"


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


def _with_impl(body: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `editedObjectPksTester pfx pkname items = false` says the
# ---- extracted program's result violates `out = editedPks pfx pkname items` at
# ---- that concrete input. No `require` clause, so every literal input below is
# ---- admissible and nothing is vacuously excluded.
def _tester(call: str) -> str:
    return ("extract_program_for editedObjectPks\n"
            "prove_precondition_decidable_for editedObjectPks\n"
            "prove_postcondition_decidable_for editedObjectPks\n"
            "derive_tester_for editedObjectPks\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = editedPks pfx
    # pkname items` obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same selection; the loop-specific proof is
        # retuned since the impl now matches the post-image syntactically.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return editedPks pfx pkname items\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct editedObjectPks by\n"
            "  loom_solve"),
        "rationale": "a loop-free impl that returns the selection directly must "
                     "satisfy `out = editedPks pfx pkname items`; a correct reshape "
                     "of the modeled behaviour verifying is exactly what "
                     "SPEC-TOO-STRONG would deny. Exercises the obligation from a "
                     "maximally different (loop-free) control-flow shape. Because "
                     "`editedPks` is a GROUNDED pure function of the inputs (fully "
                     "unfolded in the spec view), returning it directly is the "
                     "cheapest CORRECT impl, not a wrong echo of an opaque oracle. "
                     "(Nagini sibling: pos-control-echo-grounded.)",
    },
    {
        "id": "pos-filtermap",
        "kind": "soundness",
        "expect": "verify",
        # Express the per-item selection as a forward `filterMap` instead of the
        # backward accumulating loop: keep `some kv.2` exactly when the key
        # matches, drop otherwise. Same value-for-value selection, order
        # preserved, a maximally different traversal; the proof is retuned by
        # induction on the items list.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return items.filterMap (fun kv =>\n"
            "      if matchesKey pfx pkname kv.1 then some kv.2 else none)\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct editedObjectPks by\n"
            "  loom_solve\n"
            "  induction items with\n"
            "  | nil => simp [editedPks]\n"
            "  | cons hd tl ih => simp [editedPks, List.filterMap_cons]; split <;> simp_all"),
        "rationale": "a forward `filterMap` selection computes the same in-order "
                     "list of matching values as the backward accumulating loop, so "
                     "`out = editedPks pfx pkname items` still holds. A correct "
                     "reshape with a different traversal direction MUST verify (else "
                     "SPEC-TOO-STRONG on the loop shape). (Nagini sibling: "
                     "pos-control-reshape.)",
    },
    {
        "id": "pos-let-bound-match",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the loop body: bind the per-item acceptance decision to a local
        # `matched` before the selection. Same value flow; the loop and the
        # front-recursive invariant are unchanged, so the frozen proof closes
        # untouched.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let kv := items[i - 1]!\n"
            "      let matched : Bool := matchesKey pfx pkname kv.1\n"
            "      result := (if matched then [kv.2] else []) ++ result\n"
            "      i := i - 1"),
        "rationale": "binding the per-item decision to a local computes the same "
                     "accumulator value-for-value with the loop and invariant "
                     "unchanged, so `out = editedPks pfx pkname items` still holds "
                     "and the frozen proof closes; a correct reshape must verify "
                     "(else SPEC-TOO-STRONG on the impl shape). (Nagini sibling: "
                     "pos-control-reshape, second shape.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries no `require` clause, so the "a normal
    # input satisfies the precondition" probe is not where the risk sits. The
    # residual risk is that the post-image is UNSATISFIABLE / DEGENERATE at the
    # interesting point. This case discharges an in-region assert at concrete
    # inputs, establishing that the post-image really does KEEP the value of a
    # matching key, KEEP NOTHING for a non-matching key, and — the load-bearing
    # point — KEEP the value of a matching key whose `pfx` carries the regex
    # end-of-input metacharacter `'$'` (which the exact-sequence matcher treats
    # literally). The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the assert is live (a false claim about the
    # same points leaves an unsolved goal), and the proof's alternation gains one
    # `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _IMPL_TOP,
            "    assert (with_name_prefix `adm\n"
            "      (editedPks ['f'] ['a'] [(['f','-','0','-','a'], ['v'])] = [['v']] ∧\n"
            "       editedPks ['f'] ['a'] [(['x'], ['w'])] = [] ∧\n"
            "       editedPks ['f','$'] ['a'] [(['f','$','-','0','-','a'], ['v'])] = [['v']]))\n"
            "    let mut result : List (List Char) := []",
            _PROOF,
            "prove_correct editedObjectPks by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [editedPks_drop_step pfx pkname items i (by omega) (by omega)];\n"
            "       simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: it KEEPS the value of a matching key, KEEPS "
                     "NOTHING for a non-matching key, and KEEPS the value of a "
                     "matching key whose prefix carries the end-of-input "
                     "metacharacter (matched literally by the exact-sequence "
                     "matcher — the load-bearing behavior of the fix). The in-region "
                     "assert must discharge (else the obligation is degenerate); the "
                     "impl is kept verbatim so `out = editedPks pfx pkname items` "
                     "still verifies. (Nagini sibling: admissibility-f2p.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-dollar-anchor-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # THE headline pre-patch bug. When the prefix carries the regex
        # end-of-input metacharacter '$', the whole selection is voided (returns
        # []): a data-loss when a '$'-bearing prefix names a real edited row.
        # This re-expresses, at the selection level, the pre-fix behaviour where
        # the un-escaped '$' in `r'{prefix}-\\d+-{name}$'` is honoured as an
        # anchor rather than a literal, so the matching key is not recognised and
        # its value is dropped. Correct on every prefix without '$'; diverges on
        # the '$'-prefix sub-domain, where the exact-sequence matcher (which the
        # gold fix realises via re.escape) DOES recognise the key.
        "module": _with_impl(
            "    return (if pfx.contains '$' then [] else\n"
            "      items.filterMap (fun kv => if matchesKey pfx pkname kv.1 then some kv.2 else none))"),
        "refinement": "this is the pre-image behaviour: a prefix carrying the "
                      "end-of-input metacharacter voids the selection instead of "
                      "matching the prefix literally. Its faithful real counterpart "
                      "is the UNCHANGED buggy pattern (no re.escape), which on the "
                      "F2P input — a prefix carrying that metacharacter naming a real "
                      "edited row — drops the row (queryset count 0 != 1), so the "
                      "failing test still fails: it would NOT resolve. This is the "
                      "headline weakness the spec must reject. (Nagini sibling: "
                      "real-bug-dollar-anchor.)",
        "rationale": "REJECT from `out = editedPks pfx pkname items`: at a prefix "
                     "carrying '$' over an item whose key matches literally, "
                     "`editedPks` keeps the value (the matcher treats '$' as an "
                     "ordinary literal code point) while the rival returns []. "
                     "Refuted at pfx=['f','$'], pkname=['a'], one matching "
                     "'$'-prefixed key — the load-bearing sub-domain of the fix.",
        "witness": _tester(
            "editedObjectPksTester ['f','$'] ['a'] [(['f','$','-','0','-','a'], ['v'])]"),
    },
    {
        "id": "weak-ignore-matcher",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the value of EVERY item, ignoring the per-key matcher entirely.
        # The selection filter is dropped: any request key is treated as naming
        # an edited row. Diverges on every non-matching key (recognises rows that
        # are not real formset keys).
        "module": _with_impl("    return items.map (fun kv => kv.2)"),
        "refinement": "dropping the per-key match test keeps the value of every "
                      "request item, so unrelated POST fields are miscounted as "
                      "edited rows. Its faithful real counterpart is a pattern that "
                      "matches everything (or no pattern at all), which selects "
                      "values from keys that are not `prefix-<int>-name` formset "
                      "keys — the queryset would contain wrong/extra rows and the "
                      "failing test would NOT resolve.",
        "rationale": "REJECT from `out = editedPks pfx pkname items`: `editedPks` "
                     "keeps ONLY matching keys' values, so on a non-matching key it "
                     "keeps nothing while the rival keeps the value. Refuted at "
                     "pfx=['f'], pkname=['b'], items=[(['x'],['w'])] (a single "
                     "non-matching key): editedPks = [], rival = [['w']]. A distinct "
                     "input point and clause (the acceptance filter) from the other "
                     "rivals.",
        "witness": _tester(
            "editedObjectPksTester ['f'] ['b'] [(['x'], ['w'])]"),
    },
    {
        "id": "weak-wrong-projection",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the matching item's KEY instead of its VALUE. The acceptance
        # decision is correct; the projection is wrong. Diverges on every
        # matching item whose key differs from its value (the normal case: the
        # POST key is a formset field name, the value is the primary key).
        "module": _with_impl(
            "    return items.filterMap (fun kv =>\n"
            "      if matchesKey pfx pkname kv.1 then some kv.1 else none)"),
        "refinement": "emitting the matched KEY rather than the VALUE returns the "
                      "formset field names instead of the submitted primary-key "
                      "values. Its faithful real counterpart selects the wrong "
                      "component of each matched item, so the edited-object primary "
                      "keys are never gathered — the queryset is built from the "
                      "wrong data and the failing test would NOT resolve.",
        "rationale": "REJECT from `out = editedPks pfx pkname items`: `editedPks` "
                     "projects each matching item to its VALUE (`kv.2`), so on a "
                     "matching item whose key != value the rival's KEY projection "
                     "diverges. Refuted at pfx=['g'], pkname=['a'], one matching "
                     "key ['g','-','5','-','a'] with value ['v']: editedPks = "
                     "[['v']], rival = [['g','-','5','-','a']]. Attacks the "
                     "projection clause, a distinct sub-domain and input point.",
        "witness": _tester(
            "editedObjectPksTester ['g'] ['a'] [(['g','-','5','-','a'], ['v'])]"),
    },
    {
        "id": "weak-empty-selection",
        "kind": "uniqueness",
        "expect": "reject",
        # Select NOTHING: always return the empty list. The generic
        # partial-domain floor — no edited row is ever gathered. Diverges on
        # every input with at least one matching key.
        "module": _with_impl("    return []"),
        "refinement": "returning the empty selection gathers no edited-object "
                      "primary keys at all: the changeform view would save no "
                      "edits. Its faithful real counterpart matches nothing, so the "
                      "queryset is empty even when an edited row is present — the "
                      "failing test (which expects exactly one edited row) would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = editedPks pfx pkname items`: `editedPks` "
                     "keeps a matching key's value, so on any input with a matching "
                     "key the rival's [] diverges. Refuted at pfx=['f'], "
                     "pkname=['i','d'] (a MULTI-character identifier name), one "
                     "matching key ['f','-','0','-','i','d'] with value ['v']: "
                     "editedPks = [['v']], rival = []. A fourth distinct input point "
                     "that also varies pkname to a multi-char name.",
        "witness": _tester(
            "editedObjectPksTester ['f'] ['i','d'] [(['f','-','0','-','i','d'], ['v'])]"),
    },

    # =====================================================================
    # UNIQUENESS, second tier: rivals that RE-IMPLEMENT the per-key decision
    # and weaken exactly ONE of its internal conjuncts. The frozen `matchesKey`
    # lives in the spec-view `pure` region and cannot be edited, but an impl is
    # free to INLINE its own decision over the same frozen sub-helpers
    # (`stripPrefix` / `takeDigits` / `atEnd`) and drop one requirement. So each
    # conjunct is separately attackable at the selection level, at a key that
    # satisfies every OTHER conjunct — a near-miss the coarse
    # `weak-ignore-matcher` rival (which keeps every value) does not reach.
    # =====================================================================
    {
        "id": "weak-empty-digit-run",
        "kind": "uniqueness",
        "expect": "reject",
        # Weaken ONLY the non-emptiness of the digit run: the decision keeps the
        # `pfx`, both '-' separators, the `pkname` and the end-of-input check,
        # but drops `!dp.1.isEmpty`, so a key with NO index between the two
        # separators is accepted. Diverges only on that near-miss.
        "module": _with_impl(
            "    return items.filterMap (fun kv =>\n"
            "      match stripPrefix pfx kv.1 with\n"
            "      | none    => none\n"
            "      | some r1 =>\n"
            "        match r1 with\n"
            "        | '-' :: r2 =>\n"
            "            let dp := takeDigits r2\n"
            "            (match dp.2 with\n"
            "             | '-' :: r3 =>\n"
            "                 (match stripPrefix pkname r3 with\n"
            "                  | some tail => if atEnd tail then some kv.2 else none\n"
            "                  | none      => none)\n"
            "             | _ => none)\n"
            "        | _ => none)"),
        "refinement": "the index run between the two separators is required to be "
                      "NON-EMPTY; this rival accepts an absent index. Its faithful "
                      "real counterpart weakens the one-or-more index quantifier to "
                      "zero-or-more, which selects values from request items that "
                      "carry no row index at all — they name no edited row, so the "
                      "gathered set is wrong and the failing test would NOT resolve. "
                      "(Nagini sibling: partial-drop-digits — NOT subsumed here.)",
        "rationale": "REJECT from `out = editedPks pfx pkname items`: at "
                     "pfx=['f'], pkname=['a'], items=[(['f','-','-','a'],['v'])] "
                     "the key satisfies every conjunct EXCEPT the non-empty index "
                     "run, so `editedPks` = [] while the rival = [['v']]. A "
                     "near-miss input point no other rival reaches: "
                     "weak-ignore-matcher keeps every value and so is refuted by a "
                     "key that matches nothing, whereas this one is refuted only by "
                     "the single dropped conjunct.",
        "witness": _tester(
            "editedObjectPksTester ['f'] ['a'] [(['f','-','-','a'], ['v'])]"),
    },
    {
        "id": "weak-any-second-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Weaken ONLY the second separator: accept ANY single character where
        # the frozen decision demands '-'. Every other conjunct is kept.
        "module": _with_impl(
            "    return items.filterMap (fun kv =>\n"
            "      match stripPrefix pfx kv.1 with\n"
            "      | none    => none\n"
            "      | some r1 =>\n"
            "        match r1 with\n"
            "        | '-' :: r2 =>\n"
            "            let dp := takeDigits r2\n"
            "            (if dp.1.isEmpty then none else\n"
            "             match dp.2 with\n"
            "             | _ :: r3 =>\n"
            "                 (match stripPrefix pkname r3 with\n"
            "                  | some tail => if atEnd tail then some kv.2 else none\n"
            "                  | none      => none)\n"
            "             | _ => none)\n"
            "        | _ => none)",),
        "refinement": "the separator between the index and the identifier name is "
                      "the literal '-'; this rival accepts any single character "
                      "there. Its faithful real counterpart replaces that literal "
                      "with a wildcard, which selects values from request items "
                      "whose key is not a row/field key under this prefix and name, "
                      "so extra unrelated values are gathered and the failing test "
                      "would NOT resolve. (Nagini sibling: partial-drop-hyphen2 — "
                      "NOT subsumed here.)",
        "rationale": "REJECT from `out = editedPks pfx pkname items`: at "
                     "pfx=['f'], pkname=['a'], "
                     "items=[(['f','-','0','x','a'],['v'])] the key satisfies every "
                     "conjunct EXCEPT the second separator being '-', so "
                     "`editedPks` = [] while the rival = [['v']]. A distinct "
                     "near-miss point; separates the separator clause from the "
                     "index-run clause attacked by weak-empty-digit-run.",
        "witness": _tester(
            "editedObjectPksTester ['f'] ['a'] [(['f','-','0','x','a'], ['v'])]"),
    },
    {
        "id": "weak-strict-end-of-input",
        "kind": "uniqueness",
        "expect": "reject",
        # Weaken the END-OF-INPUT clause in the OTHER direction: demand nothing
        # remains (`tail.isEmpty`) where the frozen `atEnd` also tolerates a
        # single trailing line terminator. Too STRICT rather than too lax, so it
        # DROPS a value the spec keeps — the only rival in the battery whose
        # error is an omission at a key the matcher accepts.
        "module": _with_impl(
            "    return items.filterMap (fun kv =>\n"
            "      match stripPrefix pfx kv.1 with\n"
            "      | none    => none\n"
            "      | some r1 =>\n"
            "        match r1 with\n"
            "        | '-' :: r2 =>\n"
            "            let dp := takeDigits r2\n"
            "            (if dp.1.isEmpty then none else\n"
            "             match dp.2 with\n"
            "             | '-' :: r3 =>\n"
            "                 (match stripPrefix pkname r3 with\n"
            "                  | some tail => if tail.isEmpty then some kv.2 else none\n"
            "                  | none      => none)\n"
            "             | _ => none)\n"
            "        | _ => none)"),
        "refinement": "the end-of-input position tolerates a single trailing line "
                      "terminator (the modeled engine's documented behaviour at that "
                      "anchor, recorded in mapping.md §2.1 and differentially tested "
                      "by G-CONF). This rival demands the key end exactly, so a "
                      "submitted key carrying one trailing terminator is DROPPED and "
                      "its row is silently lost — the same class of data loss as the "
                      "headline case, on a different clause, so the failing test "
                      "would NOT resolve on such input.",
        "rationale": "REJECT from `out = editedPks pfx pkname items`: at "
                     "pfx=['f'], pkname=['a'], "
                     "items=[(['f','-','7','-','a','\\n'],['v'])] `atEnd ['\\n']` "
                     "holds so `editedPks` = [['v']], while the rival's "
                     "`tail.isEmpty` fails and it returns []. Attacks the end-of-"
                     "input clause in the TOO-STRICT direction — the only rival "
                     "here that drops a value the spec keeps, and the only one "
                     "probing the trailing-terminator tolerance.",
        "witness": _tester(
            "editedObjectPksTester ['f'] ['a'] [(['f','-','7','-','a','\\n'], ['v'])]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 10 SPEC cases (1
# soundness positive `pos-control-reshape`, 1 grounded-echo positive
# `pos-control-echo-grounded`, 1 admissibility, 3 frame-mutation rivals
# [frame-mutation-key, frame-mutation-prefix, helper-frame-mutation], 4
# value/uniqueness rivals) plus 2 AXIOM_TESTS. The sibling contracts the per-key
# DECISION `is_edited_pk_key` and two verified helpers `match_literal` /
# `run_is_digits` over `List[int]` carriers holding fractional heap permissions,
# with `recognises` a grounded @Pure decision. This velvet bundle models a
# DIFFERENT (broader) slice: the whole in-order SELECTION `editedObjectPks` over
# the request items, with the per-key decision `matchesKey` (and its
# sub-decisions stripPrefix/takeDigits/atEnd) frozen DEEPLY in the spec-view
# `pure` region rather than being the contracted surface. So the nagini decision
# rivals re-express here as SELECTION rivals: a rival that mishandles the per-key
# decision shows up as a wrong selection, refutable at the selection level.
#
#   sibling case (nagini)          kind          -> here                        disposition
#   --------------------------------------------------------------------------------------------
#   pos-control-reshape            soundness     -> pos-let-bound-match /        PORTED (two shapes:
#                                                    pos-filtermap                 loop-body reshape +
#                                                                                  forward filterMap)
#   pos-control-echo-grounded      soundness     -> pos-closed-form              PORTED
#   admissibility-f2p              admissibility -> admiss-grounded              RE-AIMED
#   frame-mutation-key             uniqueness    -> (none)                       VACUOUS (no heap)
#   frame-mutation-prefix          uniqueness    -> (none)                       VACUOUS (no heap)
#   helper-frame-mutation          uniqueness    -> (none)                       VACUOUS (no heap)
#   real-bug-dollar-anchor         uniqueness    -> weak-dollar-anchor-dropped   PORTED (headline)
#   partial-drop-label             uniqueness    -> weak-ignore-matcher          RE-EXPRESSED
#   partial-drop-digits            uniqueness    -> (subsumed)                    SUBSUMED
#   partial-drop-hyphen2           uniqueness    -> (subsumed)                    SUBSUMED
#   (new, no sibling)              uniqueness    -> weak-wrong-projection         ADDED
#   (new, no sibling)              uniqueness    -> weak-empty-selection          ADDED
#   ax-sound-recognises            axiom         -> (none)                        G-AX / G-CONF
#   ax-contain-recognises          axiom         -> (none)                        G-AX / G-CONF
#
# PORTED (real-bug-dollar-anchor -> weak-dollar-anchor-dropped): the nagini rival
#   forces `ok_label=False` when the label ends in '$', reproducing the pre-fix
#   anchor-honouring bug. Here the contracted surface is the selection, and the
#   matcher `matchesKey` is FROZEN and already treats '$' as a literal (the gold
#   escape fix realised in the deep model). So the rival re-expresses as: void the
#   selection whenever the prefix carries '$'. Same data-loss on the same F2P
#   sub-domain (a '$'-bearing prefix naming a real edited row), refuted where
#   editedPks keeps the value and the rival drops it. This is the single
#   discriminating delta of the gold patch and the headline weakness.
# RE-EXPRESSED (partial-drop-label -> weak-ignore-matcher): the nagini rival drops
#   the literal-label conjunct, accepting keys with a wrong prefix. Here the whole
#   per-key decision is frozen inside `matchesKey`, so the closest selection-level
#   attack is to drop the match test entirely (keep every value), which likewise
#   accepts keys that do not name an edited row under this prefix/name. Refuted on a
#   non-matching key.
# PORTED (partial-drop-digits -> weak-empty-digit-run; partial-drop-hyphen2 ->
#   weak-any-second-separator): on nagini these attack INTERNAL conjuncts of the
#   per-key decision, because the DECISION is the contracted surface there. Here
#   the decision lives in the frozen spec-view `pure` region, so a variant cannot
#   EDIT `matchesKey` — but it does not need to. An impl is free to INLINE its own
#   per-key decision over the same frozen sub-helpers (`stripPrefix` /
#   `takeDigits` / `atEnd`) and drop exactly one requirement, which keeps
#   `markers.same_spec` (the whole change sits in the impl region) while diverging
#   from `editedPks` only at the near-miss key that clause guards. Both conjuncts
#   are therefore separately attackable at the selection level and are now ported
#   as first-class rivals with their own witnesses, at keys satisfying every OTHER
#   conjunct: an absent index run (['f','-','-','a']) and a non-'-' second
#   separator (['f','-','0','x','a']).
#
#   An earlier revision of this manifest recorded both as SUBSUMED under
#   weak-ignore-matcher, on the reasoning that a rival keeping EVERY value is a
#   generalisation of one that keeps too many. That reasoning was WRONG and is
#   corrected here: weak-ignore-matcher is refuted at a key matching NOTHING
#   (['x']), which attests only that some filter is applied — it cannot
#   distinguish an impl applying the full frozen decision from one applying a
#   decision missing a single conjunct, because both reject ['x']. The near-miss
#   points above are the only inputs that separate them, and no other case in the
#   battery reaches them. Verified with real builds: each new rival's witness
#   elaborates against the rival (exit 0) and fails against a CORRECT loop-free
#   impl with `decide` PROVING the tester true (i.e. a semantic refutation, not a
#   stuck reduction).
# ADDED (weak-strict-end-of-input): no nagini sibling. The end-of-input clause
#   tolerates one trailing line terminator; this rival demands the key end exactly
#   and so DROPS a value the spec KEEPS. It is the only rival whose error is an
#   omission at an ACCEPTED key rather than an over-acceptance, and the only probe
#   of the trailing-terminator tolerance that mapping.md §2.1 documents.
# VACUOUS (frame-mutation-key, frame-mutation-prefix, helper-frame-mutation): the
#   nagini frame-mutation rivals overwrite a fractional-permission read-only list
#   (append to key / prefix / the helper lit), rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent and declares no `mut`
#   parameter — every input is an immutable value with no heap footprint — so there
#   is no read-only field to overwrite and no permission system to trip, and the
#   verified helpers have no counterpart (the matcher is a pure `def`, not a
#   contracted method). Omitted as vacuous, NOT fabricated (per the porting map,
#   this class is legitimately dropped rather than replaced).
# ADDED (weak-wrong-projection, weak-empty-selection): two selection-level rivals
#   with no direct nagini sibling. wrong-projection attacks the value-vs-key
#   projection clause (the nagini decision surface has no projection to get wrong,
#   since it returns a Bool); empty-selection is the partial-domain floor and also
#   varies pkname to a multi-character identifier. Both give distinct witness
#   points and attack distinct clauses of the post-image.
# AXIOM_TESTS (2, ax-sound-recognises / ax-contain-recognises): dropped. The axiom
#   lane is G-AX's job; here the matcher is modeled DEEPLY (an A-reference the R/I
#   legs differential-test against the real re.escape-fixed compiled pattern via
#   G-CONF), not a consumed contract, so there is nothing to probe in this lane and
#   the gate ignores AXIOM_TESTS regardless.
#
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
#
# BINDER / CLAUSE COVERAGE. The obligation has three input binders — `pfx`,
#   `pkname`, `items` — and one top-level clause, `out = editedPks pfx pkname
#   items`, which internally conjoins the per-key acceptance decision, the
#   in-order traversal, and the value (not key) projection. The four reject
#   witnesses probe SEVEN DISTINCT input tuples: pfx over
#   {['f','$'],['f'],['g'],['f']}, pkname over {['a'],['b'],['a'],['i','d']}, and
#   items over {a matching '$'-prefixed key, a non-matching key, a matching key, a
#   matching multi-char-pkname key, an absent-index near-miss, a wrong-second-
#   separator near-miss, a matching key with one trailing line terminator} — no
#   binder held fixed. The acceptance decision is now attacked clause by clause:
#   the '$'-anchor delta specifically (weak-dollar-anchor-dropped), the matcher
#   ignored entirely (weak-ignore-matcher), the non-empty index run
#   (weak-empty-digit-run), the second separator (weak-any-second-separator), and
#   the end-of-input tolerance (weak-strict-end-of-input, in the too-STRICT
#   direction — it drops a value the spec keeps). The value/key projection is
#   attacked by wrong-projection and the "keep a matching value at all" floor by
#   empty-selection. The admissibility case pins the keep/drop/'$'-literal
#   branches at concrete inputs. Every clause of the frozen decision that an impl
#   can weaken now has a rival refuted at a key that satisfies all the OTHERS, so
#   no rival that mishandled only a fixed prefix, name, item shape, or single
#   clause could slip through.
#
# ATTACKS THAT FOUND NO HOLE (recorded so the next audit need not re-run them;
#   each was built against the frozen spec and REJECTED, as it must be):
#   order-reversed selection; only-the-first-match kept; the trailing-terminator
#   tolerance removed; the two literal binders pfx/pkname swapped; duplicate
#   values collapsed. And two CORRECT reshapes the spec must ADMIT, both of which
#   verified (exit 0), so the spec is not too strong on impl shape: a `foldr`
#   accumulation, and `filter`-then-`map` as two passes instead of `filterMap`.
AXIOM_TESTS = []
