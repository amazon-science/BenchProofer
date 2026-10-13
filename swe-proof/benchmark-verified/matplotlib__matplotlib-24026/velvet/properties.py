"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24026 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct selectLayerColors`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method that picks the per-area fill colours for
a stack of filled areas from a supplied, non-empty colour list, while leaving the
surrounding shared colour-cycle state untouched:

  selectLayerColors (mut sharedCycle : List String) (colors : List String)
      (layerCount : Nat)  return (out : List String)
    require colors.length > 0
    ensures sharedCycle = sharedCycleOld
    ensures out = cyclicColors colors layerCount

TWO independent, load-bearing top-level clauses:
  (C1) ``sharedCycle = sharedCycleOld`` — the shared colour-cycle state is
       read-only: whatever colour sequence the surrounding context would hand its
       OTHER consumers must be exactly the same afterwards as before. This is the
       directive-5 frame on the ONE mutable binder, and it is the reported defect
       itself: the request must not perturb the shared cycle.
  (C2) ``out = cyclicColors colors layerCount`` — the per-area colours are drawn
       solely from the supplied list, repeated cyclically: area ``i`` takes
       ``colors[i % colors.length]``, exactly ``layerCount`` of them in area
       order. ``cyclicColors`` is a total, fully-unfolded ``def`` of the method's
       own ``colors``/``layerCount`` arguments — there is no opaque answer key to
       echo (the ``axioms`` region is empty), so the ungrounded-oracle-echo class
       does not apply; it is replaced by an honest cheapest-reshape positive
       control plus an admissibility positive.

The free INPUT BINDERS are ``sharedCycle`` (C1's frame), ``colors`` and
``layerCount`` (C2's cyclic reading). The reject witnesses below vary all three:
``colors`` over lengths 1/3/2, ``layerCount`` over 1/3/2, and ``sharedCycle``
over distinct entry values (which C1's rival overwrites) — so no binder is pinned
across the battery and both clauses are attacked.

ADVERSARIAL READ of the sibling classes on THIS carrier:
  * FRAME-MUTATION on the shared cycle — APPLIES here, and is the headline rival.
    On nagini this was a fractional-permission write to a half-permission input.
    On this backend the shared cycle is modeled DIRECTLY as the ``mut sharedCycle``
    binder pinned to its entry value by ``ensures sharedCycle = sharedCycleOld``,
    so the reported bug (recording the supplied colours into the shared cycle) is
    EXPRESSIBLE: a body that writes ``sharedCycle := colors`` violates C1 whenever
    the supplied colours differ from the entry cycle. Ported as
    ``frame-mut-shared-cycle`` with a machine-checked witness.
  * FRAME-MUTATION on ``colors`` — VACUOUS on this backend. The sibling's
    supporting frame rival appends to the read-only ``colors`` input held at a
    fractional permission. Here ``colors`` is an immutable value (NOT a ``mut``
    binder); Lean and Velvet are referentially transparent, there is no heap and
    no aliasing, so there is no read-only input to overwrite and no substitute
    probe to build. Dropped, not fabricated (see footer).
  * PARTIAL-DOMAIN / VALUE — APPLIES: rivals that read the cyclic sequence at the
    wrong offset (off-by-one), mispaint only the first area (first-layer), or
    paint one area too few (short). Each attacks C2 on a distinct sub-domain and
    is refuted at a distinct concrete input.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``selectLayerColorsTester sharedCycle colors layerCount = false`` says the
extracted program's observable (the returned colour list AND the post-state of
the shared cycle) violates the method's postcondition at that concrete input. It
is checked in a file whose ``prove_correct`` block has been stripped, so no
tactic script can mask the verdict. The carriers are ``List String``/``Nat`` with
native ``DecidableEq``, so every witness closes by ``decide``.

AXIOM lane: DROPPED. The ``axioms`` region declares no ``axiom`` (the cyclic
colour reading is modeled deeply as an A-reference, validated == the real
finite cyclic iterator by axiom_check.py / G-AX, NOT consumed as a contract).
There is no axiom-soundness / axiom-containment obligation to probe in this
spec-lane manifest, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24026"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap) --------
_GOLD_IMPL = (
    "    let assigned := (List.range layerCount).map\n"
    "      (fun (i : Nat) => colors[i % colors.length]!)\n"
    "    return assigned"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- anchor for inserting an in-region admissibility assert (the first line of
# ---- the executable body; unique in the file). ----
_LETHEAD = "    let assigned := (List.range layerCount).map"

assert _BASE.count(_LETHEAD) == 1, "lethead anchor not unique"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header is kept), so a positive control that
# ---- reshapes the impl may retune its tactic script without touching the spec
# ---- statement or dropping the obligation. Unique in the file.
_GOLD_PROOF = (
    "prove_correct selectLayerColors by\n"
    "  loom_solve\n"
    "  simp [cyclicColors]"
)

assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped. The
# ---- carriers (`List String`, `Nat`) have native `DecidableEq`, so no instance
# ---- needs deriving, no assumption is introduced (`axiom`/`sorry`/
# ---- `native_decide` are absent), and the frozen solution rejects these
# ---- witnesses all the same.
def _tester(body):
    return (
        "extract_program_for selectLayerColors\n"
        "prove_precondition_decidable_for selectLayerColors\n"
        "prove_postcondition_decidable_for selectLayerColors\n"
        "derive_tester_for selectLayerColors\n\n" + body
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the post-image is SPEC-TOO-STRONG. The gold
    # body binds the per-area list to a `let` and returns it; this reshape drops
    # the intermediate binding and returns the cyclic reading directly. The value
    # flow is identical on every input, the shared cycle is still never written,
    # and no new proof obligation appears, so the frozen tactic script still
    # discharges both clauses (frame unchanged, out = cyclicColors).
    # =====================================================================
    {
        "id": "pos-control-inline-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    return (List.range layerCount).map "
            "(fun (i : Nat) => colors[i % colors.length]!)"),
        "rationale": (
            "a correct reshape (return the cyclic per-area reading directly "
            "instead of through an intermediate binding) yields an identical "
            "result on every input and never writes the shared cycle, so both "
            "clauses (C1 frame `sharedCycle = sharedCycleOld`, C2 "
            "`out = cyclicColors colors layerCount`) still discharge under the "
            "frozen script; if it failed to verify the spec would be "
            "SPEC-TOO-STRONG on impl shape."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries a `require colors.length > 0`, so the
    # sibling's "a normal F2P-shaped input satisfies the precondition" probe is
    # meaningful, AND the residual total-domain risk (the post-image degenerate /
    # unsatisfiable at the interesting point) applies. This case discharges an
    # in-region assert that (a) the guard admits a normal supplied colour list,
    # and (b) the cyclic reading is non-degenerate at the F2P corner: with as many
    # colours as areas it is the identity ordering, and with fewer colours than
    # areas it wraps around from the beginning. The assert is LIVE (replacing the
    # wrap conjunct with a false claim about the same point leaves an unsolved
    # goal — verified). The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the tactic body is retuned to also close the
    # assert.
    # =====================================================================
    {
        "id": "admiss-cyclic-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _LETHEAD,
                "    assert (with_name_prefix `assert\n"
                "      ((([\"C0\", \"C1\", \"C2\"] : List String).length > 0) ∧\n"
                "       cyclicColors [\"C0\", \"C1\", \"C2\"] 3 "
                "= [\"C0\", \"C1\", \"C2\"] ∧\n"
                "       cyclicColors [\"C0\", \"C1\"] 3 "
                "= [\"C0\", \"C1\", \"C0\"]))\n"
                + _LETHEAD),
            _GOLD_PROOF,
            "prove_correct selectLayerColors by\n"
            "  loom_solve <;> simp [cyclicColors] <;> decide"),
        "rationale": (
            "the admitted domain covers a normal F2P-shaped input AND the "
            "post-image is satisfiable and non-degenerate there: the guard admits "
            "a non-empty colour list, with as many colours as areas the cyclic "
            "reading is the identity ordering, and with fewer colours than areas "
            "it wraps around from the beginning. The in-region assert must "
            "discharge (else the obligation is unsatisfiable / PRECOND-TOO-STRONG); "
            "the impl is kept verbatim so `out = cyclicColors colors layerCount` "
            "still discharges too."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "frame-mut-shared-cycle",
        "kind": "uniqueness",
        "expect": "reject",
        # The reported bug itself: record the supplied colours into the shared
        # colour-cycle state before producing the per-area colours. C2 still holds
        # (the returned list is the correct cyclic reading); ONLY C1's frame is
        # violated whenever the supplied colours differ from the entry cycle.
        "module": _impl(
            "    sharedCycle := colors\n"
            "    return (List.range layerCount).map "
            "(fun (i : Nat) => colors[i % colors.length]!)"),
        "refinement": (
            "a faithful counterpart that pushes the supplied colours into the "
            "surrounding shared colour cycle (the pre-change behaviour) perturbs "
            "the sequence the shared cycle would hand its OTHER consumers, so a "
            "control consumer drawn on the same context receives a different "
            "colour than if the operation had not run. The failing test observes "
            "exactly that cross-consumer desynchronisation, so it still fails. It "
            "would NOT resolve (and, as the issue's own traceback shows, routing "
            "the supplied cycle-reference colours through the shared cycle's "
            "validator raises before any drawing happens)."
        ),
        "rationale": (
            "REJECT from C1 `sharedCycle = sharedCycleOld`: the body overwrites "
            "the shared cycle with the supplied colours, so whenever those differ "
            "from the entry value the post-state disagrees with the pinned frame. "
            "The returned per-area list is kept correct so the ONLY failing clause "
            "is the frame. Refuted at `sharedCycle = [\"x\"]`, `colors = [\"C0\"]` "
            "(entry cycle ≠ supplied colours, where the overwrite is observable)."
        ),
        "witness": _tester(
            "example : selectLayerColorsTester [\"x\"] [\"C0\"] 1 = false := by\n"
            "  decide\n"),
    },
    {
        "id": "partial-offbyone-cyclic",
        "kind": "uniqueness",
        "expect": "reject",
        # Read the cyclic sequence one step ahead: area i takes colors[(i+1) %
        # len] instead of colors[i % len]. Wrong on every area (a rotation).
        "module": _impl(
            "    return (List.range layerCount).map "
            "(fun (i : Nat) => colors[(i + 1) % colors.length]!)"),
        "refinement": (
            "a faithful counterpart that reads the cyclic colour sequence one "
            "step ahead (an extra advance of the private cyclic walk before the "
            "first area) paints the areas with a rotated colour assignment — for a "
            "three-colour, three-area case it produces the second, third, first "
            "colour instead of first, second, third — so the rendered figure "
            "differs from the intended one and the render-equality test fails. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from C2 `out = cyclicColors colors layerCount`: area 0 must "
            "take `colors[0]` and the impl yields `colors[1 % length]`, a rotation "
            "of the whole assignment. Refuted at `colors = [\"a\", \"b\", \"c\"]`, "
            "`layerCount = 3` (gold [a,b,c] vs rival [b,c,a])."
        ),
        "witness": _tester(
            "example : selectLayerColorsTester [\"y\"] [\"a\", \"b\", \"c\"] 3 "
            "= false := by\n  decide\n"),
    },
    {
        "id": "partial-first-layer",
        "kind": "uniqueness",
        "expect": "reject",
        # First-area-only divergence: correct on areas 1..n-1 but area 0 takes
        # colors[1 % len] instead of colors[0]. Refutable only when len >= 2.
        "module": _impl(
            "    return (List.range layerCount).map\n"
            "      (fun (i : Nat) => if i == 0 then colors[1 % colors.length]! "
            "else colors[i % colors.length]!)"),
        "refinement": (
            "a faithful counterpart that mishandles the dedicated first area "
            "(sourcing it from the wrong position of the cyclic sequence while the "
            "remaining areas are drawn from the loop) paints the first stacked "
            "area with the wrong colour, so the rendered figure differs from the "
            "intended one on that area and the render-equality test fails. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from C2 `out = cyclicColors colors layerCount`: area 0 must "
            "take `colors[0]` and the impl yields `colors[1 % length]`, wrong on "
            "the first area only. Refuted at `colors = [\"r\", \"g\", \"b\"]`, "
            "`layerCount = 3` (a distinct-head, length-3 colour list where "
            "`colors[1] ≠ colors[0]` makes the first-area divergence observable — "
            "a length axis the off-by-one witness does not pin at this point)."
        ),
        "witness": _tester(
            "example : selectLayerColorsTester [\"s\"] [\"r\", \"g\", \"b\"] 3 "
            "= false := by\n  decide\n"),
    },
    {
        "id": "uniq-short-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong length: paint one area too few (range (layerCount - 1)). Leaves
        # the last stacked area uncoloured whenever layerCount >= 1.
        "module": _impl(
            "    return (List.range (layerCount - 1)).map "
            "(fun (i : Nat) => colors[i % colors.length]!)"),
        "refinement": (
            "a faithful counterpart that under-counts the areas (drawing one fewer "
            "than there are stacked areas) leaves the last stacked area without a "
            "colour assignment, so the rendered figure is missing a filled area "
            "relative to the intended one and the render-equality test fails. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from C2 `out = cyclicColors colors layerCount`: the result "
            "must carry exactly `layerCount` colours and the impl produces "
            "`layerCount - 1`, so the returned list has the wrong length whenever "
            "`layerCount >= 1`. Refuted at `colors = [\"p\", \"q\"]`, "
            "`layerCount = 2` (gold length 2 [p,q] vs rival length 1 [p])."
        ),
        "witness": _tester(
            "example : selectLayerColorsTester [\"z\"] [\"p\", \"q\"] 2 = false "
            ":= by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals — two of them
# permission-frame). It also carries an AXIOM lane (2 A-reference probes); that
# lane is G-AX's job and this spec-lane gate ignores it (AXIOM_TESTS below is
# empty). Every SPEC case is accounted for here.
#
#   sibling case                   -> here
#   ---------------------------------------------------------------------
#   pos-control-inline-reorder      -> pos-control-inline-return    PORTED
#   admiss-f2p-shaped               -> admiss-cyclic-nondegenerate  PORTED (re-expressed)
#   frame-mut-axes-cycle            -> frame-mut-shared-cycle       PORTED (expressible!)
#   frame-mut-colors                -> (none)                       VACUOUS
#   partial-offbyone-cyc            -> partial-offbyone-cyclic      PORTED
#   partial-first-layer             -> partial-first-layer          PORTED
#   uniq-short-by-one               -> uniq-short-by-one            PORTED
#
# 6 ported, 1 vacuous, 0 added. AXIOM lane dropped (G-AX's job).
#
# PORTED (frame-mut-shared-cycle): the sibling rejects the reported bug via a
#   fractional-permission write to a half-permission input (INSUFFICIENT
#   PERMISSION). This backend does not have fractional permissions, but the
#   shared colour-cycle state is modeled DIRECTLY as the ONE `mut` binder
#   (`sharedCycle`) pinned to its entry value by `ensures sharedCycle =
#   sharedCycleOld` (directive 5). So the SAME rival — recording the supplied
#   colours into the shared cycle — is expressible and rejects on C1 rather than
#   on a permission error. This is NOT a vacuous frame class here: the frame lives
#   in a value-level postcondition, and the witness discriminates (the returned
#   per-area list is kept correct, so only C1 fails, and gold satisfies C1).
# RE-EXPRESSED (admissibility): the sibling asserts the precondition facts hold
#   for an F2P-shaped input. Here the assert additionally pins the cyclic reading
#   as non-degenerate at the F2P corner (identity ordering when colours == areas;
#   wrap-around when fewer colours than areas), covering the total-domain residual
#   as well as the `require colors.length > 0` admissibility. The assert is live.
# VACUOUS (frame-mut-colors): the sibling's supporting frame rival appends to the
#   read-only `colors` input held at a fractional permission. On this backend
#   `colors` is an IMMUTABLE value (not a `mut` binder); Lean and Velvet are
#   referentially transparent, with no heap and no aliasing, so there is no
#   read-only input to overwrite and no substitute probe to build. The one frame
#   obligation that DOES survive the carrier (the shared cycle) is already
#   attacked by frame-mut-shared-cycle. Dropped, not fabricated.
#
# CLAUSE / BINDER COVERAGE. Both independent top-level clauses are attacked:
#   C1 (`sharedCycle = sharedCycleOld`) by frame-mut-shared-cycle; C2
#   (`out = cyclicColors colors layerCount`) by partial-offbyone-cyclic,
#   partial-first-layer, and uniq-short-by-one on three distinct sub-domains
#   (offset rotation, first-area-only, wrong length). Both clauses are defended by
#   the positive control and the admissibility case. The four reject witnesses
#   probe four DISTINCT inputs (pts=4):
#     sharedCycle=["x"], colors=["C0"],          layerCount=1   frame-mut-shared-cycle
#     sharedCycle=["y"], colors=["a","b","c"],   layerCount=3   partial-offbyone-cyclic
#     sharedCycle=["s"], colors=["r","g","b"],   layerCount=3   partial-first-layer
#     sharedCycle=["z"], colors=["p","q"],       layerCount=2   uniq-short-by-one
#   so `sharedCycle` is varied over four distinct entry values (the value C1's
#   rival overwrites, and the value gold must preserve), `colors` over lengths
#   1/3/3/2, and `layerCount` over 1/3/3/2. No binder is pinned across the battery.
#   The two length-3 witnesses (off-by-one, first-layer) fail for DIFFERENT
#   reasons on different colour lists: off-by-one is wrong on every area (a
#   rotation), first-layer is wrong on area 0 only — so neither is a near-miss of
#   the other and each pins its own sub-domain.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   consumed axiom (the cyclic colour reading is a deep A-reference validated ==
#   the real finite cyclic iterator by axiom_check.py), so there is nothing here
#   to probe and the gate ignores it.
AXIOM_TESTS = []
