"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-22865 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct selectSegM`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method that selects a contiguous positional
sub-run of an ordered candidate list, keyed on three booleans:

  selectSegM (segs : List Seg) (drawEdges : Bool) (extLow : Bool) (extUp : Bool)
      return (out : List Seg)
    ensures out = selectSeg segs drawEdges extLow extUp

where ``selectSeg`` (a fully transparent ``def`` over the input carrier, NOT an
opaque oracle) is

  if drawEdges then
    (segs.drop (startIdx extLow)).take (endIdx extUp segs.length - startIdx extLow)
  else []

with ``startIdx extLow = if extLow then 0 else 1`` and ``endIdx extUp n =
if extUp then n else n - 1``. ``Seg = List Float`` — each element is opaque to
the selection (only positions matter). There is no ``require`` clause, so the
admitted domain is total.

The single top-level ``ensures`` clause folds together what the sibling battery
split into a LENGTH pin (``len(result) == endIdx - startIdx``) and an ELEMENT
pin (``result[k] == segs[startIdx + k]``): a positional slice pins both the
length and the identity/order of every kept element at once. Its behavior
depends on all FOUR input binders — ``segs``, ``drawEdges``, ``extLow``,
``extUp`` — and each is abused by some reject rival below.

WITNESS PLACEMENT — why the tester machinery is NOT usable here, and what
replaces it. Velvet's ``derive_tester_for`` needs a DECIDABLE postcondition, and
the postcondition is an equality on ``List Seg = List (List Float)``. ``Float``
has no ``DecidableEq`` instance (IEEE-754 equality is not propositional
equality), so ``prove_postcondition_decidable_for selectSegM`` cannot be
discharged and ``selectSegMTester`` cannot be derived — the sibling velvet
bundles' ``…Tester x = false`` route is unavailable on this carrier.

Instead each reject witness ``extract_program_for``s the rival (which needs no
decidability — it just names the extracted executable ``selectSegMExec``) and
states, at a concrete input, that the rival's RESULT differs from the spec's:

  selectSegMExec segs d eL eU ≠ DivM.res (selectSeg segs d eL eU)

The discriminator is proved through the observables of ``List Seg`` that ARE
decidable without ``Float`` equality, reached by ``congrArg`` over a projection
into ``Nat``/``List Nat`` and closed by ``simp``. Two projections are used:

* ``List.length`` — the number of dividers kept. Refutes any rival that selects
  a run of the WRONG SIZE at its witness input (five of the eight rivals
  below, plus the both-ends-closed rival that empties the run entirely).
* ``List.map List.length`` — the sequence of per-entry element counts, i.e. a
  positional fingerprint of WHICH dividers were kept and in WHAT ORDER, over a
  ``segs`` whose entries have pairwise distinct sizes. This refutes rivals that
  keep the right COUNT and the wrong CONTENT — a reversed run, or a window
  offset by one — which ``List.length`` provably cannot see. The last two
  rivals below are of exactly that kind, and each was checked against the plain
  ``List.length`` claim as well, which fails to refute them.

So the battery attacks BOTH halves of what a positional slice pins: how many
dividers are kept, and which ones. Checked in a file whose ``prove_correct`` block
has been stripped, so no tactic script can mask the verdict; each witness
elaborates against its rival and FAILS against the frozen ``selectSeg`` (which
satisfies the spec at every input).

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the selection is
modeled directly over the carrier and calls no axiomatized callee). The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-22865"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap. -----------
_GOLD_S = "    let s : Nat := if extLow then 0 else 1"
_GOLD_E = "    let e : Nat := if extUp then segs.length else segs.length - 1"
_GOLD_SLICE = "    let selected : List Seg := (segs.drop s).take (e - s)"
_GOLD_OUT = "    let out : List Seg := if drawEdges then selected else []"

for _anchor in (_GOLD_S, _GOLD_E, _GOLD_SLICE, _GOLD_OUT):
    assert _BASE.count(_anchor) == 1, f"frozen impl region drifted: {_anchor!r}"

# ---- proof-body anchor. The `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case may retune it without touching the spec
# ---- statement or dropping the obligation. Unique in the file.
_GOLD_PROOF = ("prove_correct selectSegM by\n"
               "  loom_solve\n"
               "  simp [selectSeg, startIdx, endIdx]")
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted; update _GOLD_PROOF"


# ---- witness preamble. Reaches the rival's IMPL (which differs from gold; the
# ---- spec `selectSeg` is byte-identical in both) through Velvet's program
# ---- extraction, which — unlike the tester — needs no DecidableEq. Checked in
# ---- a file whose `prove_correct` block is stripped. No `axiom`/`sorry`/
# ---- `native_decide`; the frozen solution rejects these witnesses all the same.
def _witness(segs, draw, ext_low, ext_up):
    args = f"{segs} {draw} {ext_low} {ext_up}"
    return (
        "extract_program_for selectSegM\n\n"
        "example :\n"
        f"    selectSegMExec {args}\n"
        f"      ≠ DivM.res (selectSeg {args}) := by\n"
        "  unfold selectSegMExec selectSegM selectSeg startIdx endIdx\n"
        "  simp only [NonDetT.run]\n"
        "  intro h\n"
        "  have h3 := congrArg List.length (DivM.res.inj h)\n"
        "  simp at h3\n"
    )


# ---- ORDER-SENSITIVE witness preamble. Identical to `_witness` except for the
# ---- projection it pushes the equation through: `List.map List.length` instead
# ---- of `List.length`. `Float` has no DecidableEq, but the LENGTH OF EACH
# ---- ELEMENT is a `Nat`, so mapping element-length over the result yields a
# ---- decidable `List Nat` equation that records WHICH element sits at each
# ---- position, not merely how many there are. Used against rivals that keep the
# ---- right COUNT and the wrong CONTENT/ORDER, which plain `List.length` cannot
# ---- see: verified by building the same claim under `List.length`, which fails
# ---- against the rival (the count matches, so no contradiction is derivable).
# ---- Requires a `segs` whose entries have PAIRWISE DISTINCT lengths.
def _witness_ordered(segs, draw, ext_low, ext_up):
    args = f"{segs} {draw} {ext_low} {ext_up}"
    return (
        "extract_program_for selectSegM\n\n"
        "example :\n"
        f"    selectSegMExec {args}\n"
        f"      ≠ DivM.res (selectSeg {args}) := by\n"
        "  unfold selectSegMExec selectSegM selectSeg startIdx endIdx\n"
        "  simp only [NonDetT.run]\n"
        "  intro h\n"
        "  have h3 := congrArg (List.map List.length) (DivM.res.inj h)\n"
        "  simp at h3\n"
    )


# Concrete candidate lists. Content is opaque to the selection; only length and
# position matter, so distinct singleton `Float` lists suffice to make the
# candidate list non-degenerate at each witness input.
_S3 = "[[0.0],[1.0],[2.0]]"       # 3 candidates (F2P `both`/`min`/`max` shape)
_S4 = "[[0.0],[1.0],[2.0],[3.0]]"  # 4 candidates (a distinct `segs`)
# A 3-candidate list whose entries have PAIRWISE DISTINCT element counts (1/2/3),
# making `List.map List.length` an injective-on-these-entries positional
# fingerprint: any permutation or offset of the kept run changes it.
_S3V = "[[0.0],[1.0,1.0],[2.0,2.0,2.0]]"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the postcondition is SPEC-TOO-STRONG on
    # impl shape. The slice is expressed as take-then-drop
    # `(segs.take e).drop s` instead of the frozen drop-then-take
    # `(segs.drop s).take (e - s)`. These denote the same sub-run (a
    # `List.drop_take` identity), so all clauses still hold; the proof body is
    # retuned by adding `List.drop_take` to the frozen `simp` set — the
    # obligation statement is untouched.
    # =====================================================================
    {
        "id": "pos-control-take-then-drop",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_SLICE,
                  "    let selected : List Seg := (segs.take e).drop s"),
            _GOLD_PROOF,
            "prove_correct selectSegM by\n"
            "  loom_solve\n"
            "  simp [selectSeg, startIdx, endIdx, List.drop_take]"),
        "rationale": "a correct reshape: the contiguous run is taken as "
                     "take-then-drop rather than drop-then-take. The two denote "
                     "the same sub-list (a standard list identity), so the single "
                     "`ensures out = selectSeg …` clause still holds for every "
                     "input; the proof only adds that identity to the frozen simp "
                     "set. If it failed to verify the spec would be "
                     "SPEC-TOO-STRONG on impl shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous (nothing could exclude any
    # input on a total domain). Re-aimed at the residual admissibility risk:
    # that the post-image is DEGENERATE (e.g. always empty, or constant length)
    # so that no rival could ever be distinguished. This case discharges an
    # in-region `assert` pinning the SPEC's own output — by EVALUATION, at three
    # F2P-shaped concrete inputs, before the frozen obligation is closed
    # verbatim: all three candidates kept with both ends open, only the middle
    # one kept with both ends closed, none kept with drawing disabled. Pinned as
    # full VALUE equations rather than lengths, so the assert witnesses which
    # dividers survive and not merely how many — a length-only pin is satisfied
    # by any permutation, which is exactly the weakness the order rivals below
    # exist to attack. The impl is kept verbatim so the method's own obligation
    # still discharges; the assert is LIVE, confirmed by perturbing one claim to
    # a false value and observing the build fail with an unsolved `adm_1` goal
    # rather than pass silently.
    # =====================================================================
    {
        "id": "admiss-f2p-obligation-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_S,
                  "    assert (with_name_prefix `adm\n"
                  "      (selectSeg [[0.0],[1.0],[2.0]] true true true\n"
                  "         = [[0.0],[1.0],[2.0]] ∧\n"
                  "       selectSeg [[0.0],[1.0],[2.0]] true false false = [[1.0]] ∧\n"
                  "       selectSeg [[0.0],[1.0],[2.0]] false true true = []))\n"
                  + _GOLD_S),
            _GOLD_PROOF,
            "prove_correct selectSegM by\n"
            "  loom_solve\n"
            "  all_goals simp [selectSeg, startIdx, endIdx]"),
        "rationale": "the obligation is SATISFIABLE at exactly the F2P-shaped "
                     "inputs, discharged by evaluation at concrete literals as a "
                     "`have`-style in-region assert before the frozen obligation "
                     "closes verbatim — the total-carrier analogue of the "
                     "sibling's precondition-admits-a-normal-input probe, which "
                     "is what detects PRECOND-TOO-STRONG. It also shows the "
                     "post-image is non-degenerate: the selection VALUE varies "
                     "with the flags (all three candidates with both ends open, "
                     "just the middle one with both closed, none with drawing "
                     "disabled), so the spec constrains the result rather than "
                     "admitting a constant. If any of the three could not be "
                     "evaluated to the stated value the obligation would be "
                     "unsatisfiable at an F2P input; the impl is kept verbatim so "
                     "the method's own `ensures` still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input (proved via the result's LENGTH, the one decidable
    # observable of `List Float`) and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test. Witnesses vary all
    # FOUR binders across the battery (see footer for the coverage table).
    # =====================================================================
    {
        "id": "weak-unconditional-inner-slice",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores BOTH end flags: always start=1, end=n-1 (the legacy
        # unconditional inner slice). Correct only when both ends are closed;
        # for both-open it drops both end boundaries.
        "module": _swap(
            _swap(_BASE, _GOLD_S, "    let s : Nat := 1"),
            _GOLD_E, "    let e : Nat := segs.length - 1"),
        "refinement": "this is the pre-change behavior: an unconditional inner "
                      "slice that drops the boundary at each end regardless of "
                      "whether that end is open. When both ends are open the "
                      "failing test observes that the two end boundaries are "
                      "missing from the drawn set — exactly the reported defect — "
                      "so a faithful counterpart still fails. It would NOT resolve.",
        "rationale": "REJECT from the single `ensures` clause: at both ends open "
                     "the spec keeps all n boundaries but this keeps only the "
                     "inner n-2, so the results differ in LENGTH. If it verified "
                     "the spec would be SPEC-TOO-WEAK (it would readmit the legacy "
                     "behavior). Refuted at segs of length 3, both flags open.",
        "witness": _witness(_S3, "true", "true", "true"),
    },
    {
        "id": "weak-ignore-lower-open-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Computes the upper bound correctly but always starts at 0 (ignores the
        # lower-open flag). Correct when the lower end is open; wrong when it is
        # closed (should start at 1, dropping the lower end boundary).
        "module": _swap(_BASE, _GOLD_S, "    let s : Nat := 0"),
        "refinement": "a counterpart that keeps the lower end boundary even when "
                      "the lower end is NOT open retains a divider that should be "
                      "dropped at the closed lower end. The failing test drives a "
                      "configuration whose lower end is closed and observes the "
                      "extra boundary, so it still fails. It would NOT resolve.",
        "rationale": "REJECT from the `ensures` clause via the lower-index "
                     "dependence on `extLow`: with the lower end closed the spec "
                     "starts one in (length n-1) but this starts at 0 (length n), "
                     "so the results differ in LENGTH. Refuted at segs of length "
                     "3, lower flag CLOSED (extLow=false), upper open.",
        "witness": _witness(_S3, "true", "false", "true"),
    },
    {
        "id": "weak-ignore-upper-open-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Computes the lower bound correctly but always ends at n (ignores the
        # upper-open flag). Correct when the upper end is open; wrong when it is
        # closed (should end at n-1, dropping the upper end boundary).
        "module": _swap(_BASE, _GOLD_E, "    let e : Nat := segs.length"),
        "refinement": "a counterpart that keeps the upper end boundary even when "
                      "the upper end is NOT open retains a divider that should be "
                      "dropped at the closed upper end. The failing test drives a "
                      "configuration whose upper end is closed and observes the "
                      "extra boundary, so it still fails. It would NOT resolve.",
        "rationale": "REJECT from the `ensures` clause via the upper-index "
                     "dependence on `extUp`: with the upper end closed the spec "
                     "stops one short (length n-1-startIdx) but this runs to n "
                     "(length n-startIdx), so the results differ in LENGTH. "
                     "Refuted at segs of length 3, lower open, upper flag CLOSED "
                     "(extUp=false).",
        "witness": _witness(_S3, "true", "true", "false"),
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
            "    let e : Nat := (if extUp then segs.length else segs.length - 1) - 1"),
        "refinement": "a counterpart that stops the kept run one boundary short "
                      "emits one fewer divider than intended. For a both-open "
                      "configuration the failing test expects every boundary drawn "
                      "but observes the last one missing, so it still fails. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the `ensures` clause: the kept run is one "
                     "element shorter than the spec's slice whenever that slice is "
                     "non-empty, so the results differ in LENGTH. Refuted at segs "
                     "of length 4 (a distinct `segs`), both flags open.",
        "witness": _witness(_S4, "true", "true", "true"),
    },
    {
        "id": "weak-ignore-drawedges",
        "kind": "uniqueness",
        "expect": "reject",
        # Bounds correct, but returns the slice UNCONDITIONALLY — ignores the
        # enable flag, so a disabled selection still emits boundaries.
        "module": _swap(_BASE, _GOLD_OUT, "    let out : List Seg := selected"),
        "refinement": "a counterpart that draws boundaries even when drawing is "
                      "disabled produces dividers where none were requested. A "
                      "configuration with drawing off expects an empty set but "
                      "observes drawn boundaries, so it still fails. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the `ensures` clause via the `drawEdges` "
                     "dependence: with drawing disabled the spec returns the empty "
                     "list (length 0) but this returns the non-empty slice, so the "
                     "results differ in LENGTH. Refuted at segs of length 3, "
                     "drawEdges=false.",
        "witness": _witness(_S3, "false", "true", "true"),
    },

    # =====================================================================
    # ORDER / IDENTITY rivals. The five rivals above all change the selected
    # COUNT, so a `List.length` discriminator refutes each. That leaves the
    # other half of what a positional slice pins UNATTACKED: the IDENTITY and
    # ORDER of the kept elements. A rival keeping the right number of the wrong
    # dividers, or the right dividers in the wrong order, satisfies every
    # length-based witness above while still violating the `ensures` clause.
    # These two close that gap, discriminating through `List.map List.length`
    # (see `_witness_ordered`) over `_S3V`, whose entries have distinct element
    # counts. Confirmed necessary: the same claim stated with plain
    # `List.length` does NOT refute either rival.
    # =====================================================================
    {
        "id": "weak-reversed-run",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct bounds and correct COUNT, but the kept run is emitted in
        # reverse order, so each drawn divider sits at the wrong position.
        "module": _swap(
            _BASE, _GOLD_SLICE,
            "    let selected : List Seg := ((segs.drop s).take (e - s)).reverse"),
        "refinement": "a counterpart that emits the kept dividers end-to-start "
                      "associates each drawn line with the wrong cell boundary. "
                      "The failing test reads the drawn set positionally and "
                      "observes the entries transposed, so it still fails. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the `ensures` clause via ELEMENT IDENTITY, not "
                     "length: the slice is a positional sub-run, so reversing it "
                     "keeps the count and breaks the order. Length cannot see "
                     "this (`List.reverse` is length-preserving), so the witness "
                     "projects element-lengths instead. Refuted at a 3-candidate "
                     "`segs` with distinct entry sizes, both flags open.",
        "witness": _witness_ordered(_S3V, "true", "true", "true"),
    },
    {
        "id": "weak-shifted-window",
        "kind": "uniqueness",
        "expect": "reject",
        # Both bounds shifted up by one: the run has the correct LENGTH but
        # starts one boundary too far in, so it selects the wrong dividers.
        "module": _swap(
            _swap(_BASE, _GOLD_S, "    let s : Nat := if extLow then 1 else 2"),
            _GOLD_E,
            "    let e : Nat := "
            "(if extUp then segs.length else segs.length - 1) + 1"),
        "refinement": "a counterpart whose kept window is offset by one boundary "
                      "draws a line at each wrong internal position while drawing "
                      "the right NUMBER of them. The failing test checks which "
                      "boundaries carry lines, not just how many, so it still "
                      "fails. It would NOT resolve.",
        "rationale": "REJECT from the `ensures` clause via the slice OFFSET: "
                     "shifting both bounds by one preserves the count "
                     "(`e - s` is unchanged) but selects a different sub-run, so "
                     "no length-based witness could refute it. Refuted at a "
                     "3-candidate `segs` with distinct entry sizes, lower open "
                     "and upper CLOSED.",
        "witness": _witness_ordered(_S3V, "true", "true", "false"),
    },

    # =====================================================================
    # BOTH-ENDS-CLOSED rival. The seven rivals above are each refuted at an
    # input with at least one end OPEN: over their witness points the pair
    # (extLow, extUp) takes only (T,T), (F,T) and (T,F) — the fourth corner
    # (F,F), where BOTH end boundaries are dropped, is never the point of
    # refutation. Each flag is individually varied, which a per-binder
    # coverage table reads as complete, but the JOINT corner is not, and a
    # rival keyed on the conjunction slips through the whole battery.
    # This rival returns the empty selection at exactly that corner and is
    # correct everywhere else. Confirmed necessary by construction: the seven
    # witnesses above were each rebuilt against THIS rival and every one of
    # them fails to refute it (all seven elaborate against gold-equivalent
    # behavior at their own input, because this rival agrees with the spec
    # there), so without this case the corner is untested.
    # =====================================================================
    {
        "id": "weak-both-closed-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct bounds, but the selection is dropped entirely when BOTH ends
        # are closed — the one flag combination no other rival is refuted at.
        "module": _swap(
            _BASE, _GOLD_SLICE,
            "    let selected : List Seg := "
            "if (!extLow && !extUp) then [] else (segs.drop s).take (e - s)"),
        "refinement": "a counterpart that emits no dividers at all when neither "
                      "end of the scale is open draws nothing in the fully-closed "
                      "configuration, where the intended behavior still keeps the "
                      "inner boundaries. A configuration with both ends closed "
                      "expects the inner run and observes an empty set, so it "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from the single `ensures` clause at the JOINT corner "
                     "extLow=false ∧ extUp=false: the spec keeps the inner run "
                     "(length n-1-1) but this returns the empty list (length 0), "
                     "so the results differ in LENGTH. Every other rival is "
                     "refuted at a point with at least one end open, so this is "
                     "the only case that exercises the both-closed corner. "
                     "Refuted at segs of length 3, both flags CLOSED.",
        "witness": _witness(_S3, "true", "false", "false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals) contracting one function
# `drawn_separators(segments, lower_open, upper_open)` over a permission-bearing
# read-only list with a LENGTH pin and an ELEMENT pin. This bundle models the
# same positional selection over the purely-functional carrier
# `List (List Float)` plus three booleans, and folds the sibling's two pins into
# one `ensures out = selectSeg …` clause (a positional slice pins length AND the
# identity/order of every kept element at once). It also makes `drawEdges` an
# explicit input the sibling carried implicitly (its Requires already excluded
# the disabled case), enabling one extra rival. Every sibling case is accounted
# for below.
#
#   sibling case                              -> here
#   ---------------------------------------------------------------------
#   pos-control-offset-loop                    -> pos-control-take-then-drop   PORTED
#   admissibility-f2p-shape                    -> admiss-f2p-obligation-satisfiable RE-AIMED
#   frame-mutation-write-segments (MANDATORY)  -> (none)                       VACUOUS
#   partial-domain-prepatch-unconditional-1-to-n1 -> weak-unconditional-inner-slice PORTED
#   partial-domain-ignore-lower-open           -> weak-ignore-lower-open-flag   PORTED
#   partial-domain-ignore-upper-open           -> weak-ignore-upper-open-flag   PORTED
#   partial-domain-short-run-drop-last         -> weak-short-run-drop-last      PORTED
#   (no sibling counterpart)                   -> weak-ignore-drawedges         ADDED
#   (no sibling counterpart)                   -> weak-reversed-run             ADDED
#   (no sibling counterpart)                   -> weak-shifted-window           ADDED
#   (no sibling counterpart)                   -> weak-both-closed-empty        ADDED
#
# 6 ported/re-aimed, 1 vacuous, 4 added.
#
# ADDED (weak-reversed-run, weak-shifted-window): the sibling pins the result
#   with a LENGTH assertion and a separate ELEMENT assertion, and this bundle
#   folds both into one `ensures out = selectSeg …`. Folding them means a rival
#   only needs to break EITHER to be wrong, so the battery must attack both; the
#   five ported/added rivals above all break the length. These two break element
#   identity while preserving length (a reversed run, and a window offset by
#   one), which is the sibling's ELEMENT pin attacked directly. They exist
#   because a `List.length` witness demonstrably cannot refute them.
#
# RE-AIMED (admissibility): the sibling Asserts the precondition yields a
#   well-formed slice (start_index<=end_index) for an F2P-shaped input under its
#   Requires (len>=2). There is no `require` clause here, so the "a normal input
#   satisfies the precondition" reading is vacuous ON ITS LITERAL READING — but
#   the lane itself is NOT vacuous, and dropping it would remove the only probe
#   for PRECOND-TOO-STRONG. Its analogue on a total carrier is the obligation
#   being SATISFIABLE at an F2P-shaped input, which this case tests directly: it
#   discharges the obligation at three concrete F2P inputs by EVALUATION, as an
#   in-region assert, before closing the frozen obligation verbatim. The pins are
#   full VALUE equations (not lengths), so they also establish the post-image is
#   non-degenerate — the selection varies with the flags across the F2P corners —
#   which a length-only pin would leave open to any permutation. Liveness is
#   measured, not assumed: perturbing one claim to a false value fails the build
#   with an unsolved `adm_1` goal.
# VACUOUS (frame-mutation-write-segments): the sibling's MANDATORY frame rival
#   writes into a read-only input held at Acc(list_pred(segments), 1/2) and is
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `segs` is an immutable value, NOT a `mut` binder (mapping.md §2:
#   no parameter is `mut`; the mut-frame obligation is vacuous). There is no heap,
#   no aliasing, and no permission system to trip — no read-only input to
#   overwrite and no substitute probe to build. Reported vacuous, not fabricated.
# ADDED (weak-ignore-drawedges): the enable flag `drawEdges` is an explicit input
#   here (the sibling's Requires implicitly excluded the disabled case). The spec
#   returns `[]` when drawing is disabled; a rival that ignores the flag and draws
#   anyway is refuted directly, exercising the `drawEdges` binder that no ported
#   rival abuses.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause is DEFENDED by the
# positive control and the admissibility case and ATTACKED by all eight rivals.
# Its behavior depends on all four input binders, and the eight reject witnesses
# probe eight DISTINCT inputs:
#     segs=len3,  draw=true,  extLow=true,  extUp=true   weak-unconditional-inner-slice
#     segs=len3,  draw=true,  extLow=false, extUp=true   weak-ignore-lower-open-flag
#     segs=len3,  draw=true,  extLow=true,  extUp=false  weak-ignore-upper-open-flag
#     segs=len4,  draw=true,  extLow=true,  extUp=true   weak-short-run-drop-last
#     segs=len3,  draw=false, extLow=true,  extUp=true   weak-ignore-drawedges
#     segs=len3V, draw=true,  extLow=true,  extUp=true   weak-reversed-run
#     segs=len3V, draw=true,  extLow=true,  extUp=false  weak-shifted-window
#     segs=len3,  draw=true,  extLow=false, extUp=false  weak-both-closed-empty
#   so `drawEdges` is varied over true/false, `extLow` over true/false, `extUp`
#   over true/false, and `segs` over three distinct shapes (len 3 uniform, len 4
#   uniform, len 3 with distinct entry sizes).
#
#   JOINT vs PER-BINDER coverage. Varying each flag individually is NOT the same
#   as covering the flag pairs, and the difference is load-bearing here. The
#   first seven witness points realize only three of the four (extLow, extUp)
#   corners — (T,T), (F,T), (T,F) — leaving (F,F), the fully-closed scale where
#   both end boundaries are dropped, unprobed. A rival keyed on that conjunction
#   is wrong nowhere else and so is refuted by NO length- or order-based witness
#   above; this was measured, not reasoned about, by rebuilding all seven
#   witnesses against such a rival (every one fails to refute it).
#   `weak-both-closed-empty` supplies that corner, so the four flag pairs are
#   now all realized and a rival that mishandles any single flag COMBINATION —
#   not merely any single flag — is caught.
#
#   Both FAILURE DIRECTIONS of the folded clause are attacked, which is the
#   coverage axis a binder table does not show: six rivals keep the wrong NUMBER
#   of dividers, two keep the right number of the WRONG ones.
#
#   WITNESS METHOD NOTE. Two decidable projections carry the refutations, and
#   the split is what makes the battery cover both halves of the slice:
#     `List.length`           -> the 5 size-changing rivals (count is wrong)
#     `List.map List.length`  -> weak-reversed-run, weak-shifted-window
#   `Float` itself has no DecidableEq, so a discriminator may not compare
#   element CONTENT directly. It does not need to: each element is a `List
#   Float`, whose LENGTH is a `Nat`, so mapping element-length over the result
#   gives a decidable `List Nat` that distinguishes WHICH entries were kept and
#   in WHAT ORDER whenever the candidate entries have distinct sizes (`_S3V`).
#   An order-only or offset-only rival is therefore fully expressible here with
#   a machine-checked witness, and two are shipped above; the necessity of the
#   finer projection was confirmed by rebuilding both of those claims under
#   plain `List.length`, which does not refute either rival. The one distinction
#   this carrier cannot express is between two entries of the SAME size holding
#   different `Float` values — and that limit is MEASURED, not assumed. `Float`
#   has no `DecidableEq` instance (`infer_instance` fails), and every route to a
#   concrete Float verdict was tried and is unavailable: on `(1.0 : Float) == 0.0`
#   both `decide` and `decide +kernel` report the `Decidable` instance does not
#   reduce, `simp` makes no progress, and `native_decide` is banned from a
#   witness (it would hold of gold too). Pushing the equation through Float's
#   `BEq` — `congrArg (List.map (List.map (· == 0.0)))` — does reduce the
#   surrounding list structure but leaves a residual conjunction of opaque
#   comparisons (`(1.0 == 0.0) = (0.0 == 0.0) ∧ …`) with no tactic to close it,
#   so a content-only rival (e.g. one that reverses each entry's coordinates
#   in place, preserving all sizes) cannot carry a machine-checked witness here.
#   That costs the battery nothing: the modeled selection is purely positional
#   and never inspects, reorders within, or rebuilds an entry, so no faithful
#   counterpart of this operation can differ in entry CONTENT while agreeing on
#   which positions are kept. Recorded as a carrier limit with the builds that
#   establish it, so the next reader need not re-derive it.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
#   axiom (the selection is modeled directly; `selectSeg`/`startIdx`/`endIdx` are
#   pure `def`s, not axioms), so there is nothing there to probe.
AXIOM_TESTS = []
