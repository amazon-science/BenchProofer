"""properties.py — G-PBT falsification battery for pydata__xarray-6744 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no sorry/admit); ``expect:"reject"``
passes iff (in scope AND it does NOT verify AND the case's refutation
``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over an integer sequence carrier).
Modeled: the per-position moving-window slice of a length-``n`` sequence, given
a window length and an alignment flag. The result is the list of slices, one
per position, each the contiguous sub-range that position covers:

  rollingWindows (xs : List Int) (window : Nat) (center : Bool)
      : List (List Int)
    result = (range xs.length).map (windowAt xs window center)

  windowAt pins each slice via a per-position forward OFFSET:
    offset = ceil(window / 2)  when alignment is requested, else 1
    stop   = offset + i
    start  = clamp-to-start(offset + i - window)      (leading positions)

The DISCRIMINATING clause is the alignment-dependence of ``offset``: when
alignment is requested the forward shift must be ``(window + 1) / 2`` (the
ceiling), not the constant ``1`` the non-aligned branch uses. This is exactly
what the F2P cases (manual per-position iteration must equal the aligned
reduction) assert.

CARRIER NOTE — this backend UNIFIES the two nagini sites. Nagini modeled the
``stops`` site and the ``starts`` site as two separate functions
(``block_ends`` / ``block_begins``), each with its own copy of every rival
(ignore-alignment on ends AND on begins, etc.). Here a SINGLE function computes
both ``stop`` and ``start`` from one shared ``offset``, so each nagini rival and
its mirror collapse to ONE rival on this carrier (an offset defect corrupts both
``stop`` and ``start`` simultaneously). The ends/begins duplication is therefore
not omitted content — it is the same defect expressed once.

ADVERSARIAL READ of the classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    inputs are values (an integer sequence, a Nat, a Bool), there is no
    read-only half-permission to overwrite and no aliasing. This class has no
    expressible instance here and no substitute is fabricated. (Nagini stated
    the same: all inputs are primitives passed by value.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term built only from the inputs (``(range xs.length).map
    (windowAt xs window center)``), fully unfolded; the bundle declares no
    ``opaque``/``axiom`` (axiom_check.py is a skip stub), so there is no answer
    key an implementation could echo without doing the work. In its place the
    battery carries honest cheapest-implementation POSITIVE CONTROLS (``pos-*``)
    that must verify.

  * VALUE / OFFSET DEFECT — APPLIES. Five rivals attack the alignment-dependent
    offset: the pre-fix constant (alignment ignored), a floor instead of a
    ceiling (agrees only on even windows, diverges on the odd F2P windows), a
    uniform off-by-one (wrong slice on both alignment settings), the two
    alignment arms EXCHANGED (each arm's own formula is present, only the flag
    that selects it is inverted), and a constant-2 shift on the NON-aligned arm
    only (correct wherever alignment is requested, wrong everywhere it is not).

  * SLICE-WIDTH DEFECT — APPLIES. One rival keeps the offset arithmetic exactly
    right and corrupts only how much of the sequence is taken from ``start``:
    the full window length instead of the ``stop - start`` the position actually
    covers. Independent of the offset rivals: it is wrong precisely on the
    leading positions, where the clamp makes the covered range SHORTER than the
    window, and agrees with the frozen behavior on every later position.

  * CONTROL-FLOW-EFFECT — DOES NOT APPLY. The behavior is total over its domain
    (``1 ≤ window``): it always returns a length-``n`` list of slices, never
    raises, has no side effect. The value abstraction (the returned slice list)
    fully captures the behavior, so there is no raise/no-raise discriminator.

BINDER VARIATION (why the reject witnesses sit where they do). ``windowAt``'s
three inputs are ``xs``, ``window`` and ``center``, and a rival that mishandled
only ONE of them would be invisible to a battery whose witnesses all sit at a
single input point — the spec's dependence on that input would go undemonstrated
however many rivals were shipped. So the six reject witnesses spread over six
DISTINCT input points, and every binder moves across them:

  * ``center`` — three witnesses at ``true`` (``weak-ignore-alignment``,
    ``weak-floor-shift``, ``weak-full-window-width``) and three at ``false``
    (``weak-offbyone``, ``weak-swap-alignment-arms``,
    ``weak-unaligned-shift-two``). The flag is not varied merely for form:
    ``weak-unaligned-shift-two`` is CORRECT on the entire aligned sub-domain, so
    NO witness at ``center = true`` could refute it, and
    ``weak-swap-alignment-arms`` keeps both correct formulas and inverts only
    the selection, so it is refutable on either setting but is pinned at
    ``false`` to demonstrate the non-aligned arm's own content. Together they
    are the two rivals an all-aligned witness set would have missed.
  * ``window`` — probed at 2, 3 and 7. The odd values are the F2P windows and
    are where the ceiling and the floor part company; 2 is the EVEN window where
    those two agree, so it isolates defects (the uniform shift, the extent
    defect) that an odd-window witness cannot separate from a ceiling/floor
    confusion.
  * ``xs`` — four different sequences over three different lengths (2, 3 and 5),
    so no witness rests on one fixed sequence. Length is load-bearing on this
    carrier: the number of positions IS ``xs.length``, and the leading-position
    clamp only bites while ``i + offset < window``, so a short sequence probes
    only clamped positions while a longer one straddles the clamp boundary. The
    element VALUES differ too (``[0,1,2]``, ``[3,4]``, ``[5,6,7]``,
    ``[0,1,2,3,4]``), so no witness could be satisfied by an implementation
    keyed to a particular literal.

OMITTED nagini cases (legitimate, carrier-driven — NOT omitted for difficulty):

  * The nagini ``drop-the-clamp`` rival (``block_begins`` prepends the raw
    ``offset + i - window`` without ``max(0, .)``) has NO discriminating
    counterpart here and is DROPPED. On this carrier ``start`` is a Nat, and
    truncated Nat subtraction makes the clamp VACUOUS:
    ``if i + offset < window then 0 else (offset + i) - window`` equals
    ``(offset + i) - window`` for every Nat (both are ``0`` on the leading
    positions). A rival that "drops the clamp" is thus definitionally the frozen
    impl — there is no input at which it violates the spec, so no discriminating
    witness exists. Nagini kept this distinction because its ``starts`` were
    signed ints (a negative index reindexes from the tail); the Nat abstraction
    collapses it. Reported, not silently skipped.

  * The nagini ends/begins DUPLICATION (two ignore-alignment rivals, etc.)
    collapses to one rival each here, per the CARRIER NOTE above.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``simp only [...]`` tuned to
the frozen ``for`` body) breaks on any reshape, wrong or right — so a rejection
alone attributes nothing to the spec. Every ``expect="reject"`` case therefore
carries a Lean snippet proving the rival CONTRADICTS the spec at one concrete,
``decide``-able input. Each was checked to (1) elaborate against its rival and
(2) FAIL on the frozen solution, so it discriminates rather than asserting a
tautology. (Because ``decide`` cannot reduce the ``Id.run do``/``for`` loop on
its own, each witness first drives the loop to a concrete list via the same
``simp only [Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size]`` /
``norm_num`` / ``rw [← List.range_eq_range']`` opener the frozen proof uses,
then closes by ``decide``.)

AXIOM lane: EMPTY here. axiom_check.py is a skip stub (the window arithmetic is
modeled deeply as list ``drop``/``take``, an R leg validated by G-CONF, not by
an axiom); meta.json axioms == [] and deep_model_references == []. The axiom
lane is G-AX's job and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6744"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The offset init is the single load-bearing line the offset-defect rivals edit.
_I_OFFSET = "  let offset := if center then (window + 1) / 2 else 1\n"
# The per-position clamp expression (inside the impl loop).
_I_CLAMP = "    let start := if i + offset < window then 0 else stop - window\n"
# The slice push (inside the impl loop). Also the anchor for the slice-WIDTH
# rival, which leaves the offset arithmetic untouched and edits only the `take`.
_I_PUSH = "    out := out.push ((xs.drop start).take (stop - start))\n"
# The `stop` binding (inside the impl loop).
_I_STOP = "    let stop := offset + i\n"
# The final tactic line of the frozen proof.
_P_TAIL = "  simp only [windowAt, winOffset, winStart]\n"
# The intro line of the frozen proof (admissibility hooks a ground `have` after).
_P_INTRO = "  intro xs window center _\n"


# The witness opener/closer that drives the `Id.run do`/`for` loop to a concrete
# list and then decides the (dis)equality. Shared by every reject witness; the
# INPUT POINT is a parameter, and each reject case picks a point that isolates
# its own rival (see BINDER VARIATION above) rather than a shared one.
def _witness(xs, window, center):
    return (
        f"example : ¬ problem_spec_rollingWindows {xs} {window} {center}\n"
        f"    (implementation_rollingWindows {xs} {window} {center}) := by\n"
        "  unfold problem_spec_rollingWindows implementation_rollingWindows\n"
        "  simp only [Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size]\n"
        "  norm_num\n"
        "  rw [← List.range_eq_range']\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_rollingWindows` statement byte-identical; a
    # reshape whose value flow is unchanged retains the frozen tactic body,
    # and the one reshape that changes the clamp SPELLING re-proves it (with a
    # local `have`, no new top-level declaration, no axiom, no sorry).
    # =====================================================================
    {
        "id": "pos-stop-local",
        "kind": "soundness",
        "expect": "verify",
        # Bind the per-position right edge into a fresh local `e`, then use it.
        # Same value flows into stop/start/slice, so the frozen proof closes.
        "module": _swap(
            _BASE, _I_STOP,
            "    let e := offset + i\n    let stop := e\n",
        ),
        "rationale": "a correct reshape that binds the per-position right edge to "
                     "a fresh local before use computes the identical slice list, "
                     "so `result = (range xs.length).map (windowAt xs window "
                     "center)` still holds; must verify (else the postcondition is "
                     "over-fit to the inlined spelling => SPEC-TOO-STRONG). Proof: "
                     "the frozen tactic body is retained (the local is "
                     "zeta-reduced by the loop-normalizing simp).",
    },
    {
        "id": "pos-slice-local",
        "kind": "soundness",
        "expect": "verify",
        # Bind the slice into a local before pushing it. Same element pushed each
        # iteration, so the result and the frozen proof are unchanged.
        "module": _swap(
            _BASE, _I_PUSH,
            "    let w := (xs.drop start).take (stop - start)\n"
            "    out := out.push w\n",
        ),
        "rationale": "binding the per-position slice to a local before appending "
                     "it pushes the identical element each iteration, so the "
                     "result equals `(range xs.length).map (windowAt xs window "
                     "center)`; a correct reshape must verify. Proof: frozen "
                     "tactic body retained (the local is zeta-reduced).",
    },
    {
        "id": "pos-clamp-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the clamp behind a negated guard: handle the clamped arm first.
        # Same value on every position (both arms equal the truncated
        # subtraction), but the `if` SPELLING changes, so the frozen tail no
        # longer closes; re-proved by normalizing both clamp forms with a local
        # `have` (no new declaration).
        "module": _swap(
            _swap(_BASE, _I_CLAMP,
                  "    let start := if window ≤ i + offset then stop - window else 0\n"),
            _P_TAIL,
            "  simp only [windowAt, winOffset, winStart]\n"
            "  have e : ∀ o : Nat, (if window ≤ i + o then o + i - window else 0)\n"
            "      = (if i + o < window then 0 else o + i - window) := by\n"
            "    intro o; split <;> split <;> omega\n"
            "  rw [e]\n",
        ),
        "rationale": "reordering the leading-position clamp behind a negated guard "
                     "yields the same start on every position (both arms equal the "
                     "truncated subtraction), so `result = (range xs.length).map "
                     "(windowAt xs window center)` still holds; must verify (else "
                     "SPEC-TOO-STRONG on the clamp spelling). Re-proved because the "
                     "frozen tail is tuned to the frozen `if` order: a local `have` "
                     "normalizes the reordered clamp back to the frozen form (no "
                     "new top-level declaration, no axiom).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped aligned input rather
    # than only provable in the abstract. The frozen theorem's only
    # precondition is `1 ≤ window`; the honest analogue of nagini's
    # precondition-admission probe is to discharge the spec predicate at a
    # ground aligned input (odd window, alignment requested) by evaluation,
    # inside the proof region, alongside the frozen obligation. If that ground
    # instance could not be discharged, the modeled behavior would be
    # unsatisfiable at exactly the input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            _P_INTRO
            + "  have _ground : problem_spec_rollingWindows [0,1,2] 3 true\n"
              "      (implementation_rollingWindows [0,1,2] 3 true) := by\n"
              "    unfold problem_spec_rollingWindows implementation_rollingWindows\n"
              "    simp only [Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size]\n"
              "    norm_num\n"
              "    rw [← List.range_eq_range']\n"
              "    decide\n",
        ),
        "rationale": "the obligation is discharged at a ground aligned input (an "
                     "odd window with alignment requested — an F2P shape) by "
                     "evaluation, then the frozen obligation is closed verbatim. "
                     "Verifies (else the spec is unsatisfiable at the normal "
                     "input, the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, the theorem statement is "
                     "byte-identical, and the ground instance is a `have` inside "
                     "the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break
    # rather than a tactic-breakage artifact, and (b) a refutation witness
    # pinning the violation at one concrete input (checked to hold of the
    # rival and to FAIL on the frozen solution).
    #
    # The six witnesses sit at six DISTINCT input points, chosen so that every
    # spec input (`xs`, `window`, `center`) varies across them — see BINDER
    # VARIATION in the module docstring. Two of these rivals are refutable ONLY
    # at `center = false`; they exist precisely because a spec that pinned the
    # aligned arm alone would admit them.
    # =====================================================================
    {
        "id": "weak-ignore-alignment",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behavior: the forward offset is the constant 1, ignoring
        # the alignment flag. Unifies nagini's two ignore-alignment rivals (ends
        # and begins) — here one offset drives both stop and start.
        "module": _swap(_BASE, _I_OFFSET, "  let offset := 1\n"),
        "refinement": "fixing the forward offset to the constant 1 is exactly the "
                      "pre-fix behavior: an aligned window is placed as if "
                      "unaligned. The F2P tests assert that manual per-position "
                      "iteration over an ALIGNED window equals the aligned "
                      "reduction; with a constant offset the aligned slices are "
                      "mis-placed (e.g. window 3 aligned over [0,1,2]: position 0 "
                      "sees just [0] instead of [0,1]), so the reduction "
                      "disagrees and the test FAILS. It would NOT resolve — this "
                      "is the leg's prepatch.",
        "rationale": "REJECT from `result = (range xs.length).map (windowAt xs "
                     "window center)`: the offset defect makes the produced slice "
                     "list differ from the spec's windowAt-mapped list on aligned "
                     "windows. If it verified => SPEC-TOO-WEAK (admits the "
                     "alignment-ignoring prepatch).",
        "witness": _witness("[0,1,2]", 3, "true"),
    },
    {
        "id": "weak-floor-shift",
        "kind": "uniqueness",
        "expect": "reject",
        # Floor instead of ceiling: offset = window / 2 when aligned. Agrees with
        # the ceiling only for EVEN windows; diverges for ODD windows (3, 7 —
        # exactly the F2P windows). Non-aligned branch (1) unchanged.
        # Witness at window 7 (the OTHER F2P odd window) over a length-5
        # sequence, so this rival is refuted at a different (xs, window) point
        # than the ignore-alignment rival above: the two are near-misses of each
        # other (they coincide on every odd window whose ceiling is 1, i.e.
        # window 1), and refuting both at one shared point would leave the
        # sub-domain each `rationale` claims undemonstrated.
        "module": _swap(
            _BASE, _I_OFFSET, "  let offset := if center then window / 2 else 1\n"),
        "refinement": "using the floor `window / 2` instead of the ceiling agrees "
                      "with the correct offset only for even windows and diverges "
                      "on ODD windows — which are exactly two of the F2P windows "
                      "(3, 7). For an aligned window of 3 the floor gives offset 1 "
                      "(the buggy pre-fix value), so the aligned slices are "
                      "mis-placed and the F2P per-position-iteration test FAILS; "
                      "for 7 it gives 3 instead of 4, again mis-placing the "
                      "window. It would NOT resolve.",
        "rationale": "REJECT from `result = (range xs.length).map (windowAt xs "
                     "window center)`: on an aligned odd window the floor offset "
                     "produces a slice list differing from the windowAt-mapped "
                     "list. If it verified => SPEC-TOO-WEAK on the odd-window "
                     "aligned sub-domain.",
        "witness": _witness("[0,1,2,3,4]", 7, "true"),
    },
    {
        "id": "weak-offbyone",
        "kind": "uniqueness",
        "expect": "reject",
        # Uniform off-by-one: offset shifted forward by one on BOTH alignment
        # settings. Every position reads a slice ending one step too far.
        # Witness deliberately at center = FALSE and window 2 (an EVEN window):
        # this rival is the only offset rival that is wrong on the NON-aligned
        # arm as well, and pinning it at an aligned odd window would make its
        # witness indistinguishable from the two rivals above — the manifest
        # would then claim a both-settings defect it never demonstrates.
        "module": _swap(
            _BASE, _I_OFFSET,
            "  let offset := (if center then (window + 1) / 2 else 1) + 1\n"),
        "refinement": "adding one to the forward offset shifts every window one "
                      "position too far on BOTH alignment settings, so every "
                      "per-position iteration — aligned or not — reads the wrong "
                      "contiguous slice; the manual reduction disagrees with the "
                      "reference and the closeness assertion FAILS on the F2P "
                      "aligned cases and on the non-aligned ones alike. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `result = (range xs.length).map (windowAt xs "
                     "window center)`: the uniformly-shifted offset produces a "
                     "slice list differing from the windowAt-mapped list at every "
                     "position. If it verified => SPEC-TOO-WEAK (admits a "
                     "uniformly-shifted window). Refuted at the NON-aligned, "
                     "even-window corner, which is where it differs from the two "
                     "aligned-only rivals above.",
        "witness": _witness("[0,1,2]", 2, "false"),
    },
    {
        "id": "weak-swap-alignment-arms",
        "kind": "uniqueness",
        "expect": "reject",
        # The two alignment arms EXCHANGED: the ceiling shift is applied when
        # alignment is NOT requested and the constant 1 when it IS. Both correct
        # formulas are present; only the flag that selects them is inverted. This
        # is the sharpest test of the spec's dependence on `center`: an
        # alignment-blind spec (one that only demanded "the offset is one of the
        # two formulas") would admit it, and no witness at a single setting of
        # the flag could rule it out — it is wrong on BOTH settings, for opposite
        # reasons, so the flag must genuinely SELECT.
        "module": _swap(
            _BASE, _I_OFFSET,
            "  let offset := if center then 1 else (window + 1) / 2\n"),
        "refinement": "exchanging the two arms makes an aligned window be placed "
                      "as if unaligned AND an unaligned window be placed as if "
                      "aligned. The aligned direction is the leg's own prepatch "
                      "behavior, so the F2P per-position-iteration cases (aligned, "
                      "windows 3 and 7) FAIL outright; the unaligned direction "
                      "additionally breaks the already-passing non-aligned cases "
                      "at every window above 1. It resolves nothing and regresses "
                      "more than it started with.",
        "rationale": "REJECT from `result = (range xs.length).map (windowAt xs "
                     "window center)`: `windowAt` fixes WHICH formula each setting "
                     "of the alignment flag selects, so the exchanged assignment "
                     "produces a slice list differing from the windowAt-mapped "
                     "list on both settings (for window > 1; at window 1 the two "
                     "arms coincide, so the exchange is invisible there and the "
                     "witness must use a larger window). Witnessed at "
                     "center = FALSE and window 3, so the point is shared with no "
                     "other case. If it "
                     "verified => SPEC-TOO-WEAK: the spec would constrain the SET "
                     "of admissible offsets without constraining which flag value "
                     "selects which.",
        "witness": _witness("[0,1,2]", 3, "false"),
    },
    {
        "id": "weak-unaligned-shift-two",
        "kind": "uniqueness",
        "expect": "reject",
        # Defect confined to the NON-ALIGNED arm: shift 2 instead of 1, with the
        # aligned arm left exactly right. Correct on the ENTIRE aligned
        # sub-domain, so no aligned witness can refute it — this is precisely the
        # rival the previous all-aligned witness set would have missed.
        "module": _swap(
            _BASE, _I_OFFSET,
            "  let offset := if center then (window + 1) / 2 else 2\n"),
        "refinement": "shifting only the NON-aligned arm forward by one leaves the "
                      "aligned behavior untouched, so it does not restore the "
                      "aligned per-position iteration the F2P cases assert: those "
                      "cases still FAIL exactly as before (this rival is the "
                      "prepatch behavior on the aligned arm, since it edits the "
                      "other arm only). It also breaks the non-aligned cases that "
                      "already passed, so it strictly regresses. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `result = (range xs.length).map (windowAt xs "
                     "window center)`: on the non-aligned arm `winOffset` is "
                     "pinned to 1, so a shift of 2 produces a slice list "
                     "differing from the windowAt-mapped list at every position. "
                     "This rival AGREES with the frozen behavior on the whole "
                     "aligned sub-domain, so it is refutable ONLY at "
                     "center = false — the direct demonstration that the spec's "
                     "non-aligned arm carries real content and is not just "
                     "along for the ride. If it verified => SPEC-TOO-WEAK on the "
                     "non-aligned sub-domain.",
        "witness": _witness("[3,4]", 2, "false"),
    },
    {
        "id": "weak-full-window-width",
        "kind": "uniqueness",
        "expect": "reject",
        # Slice-WIDTH defect, offset arithmetic untouched: take the full window
        # length from `start` instead of the `stop - start` the position covers.
        # Attacks a different part of the spec's right-hand side than every
        # offset rival (the `take` argument of windowAt, not winOffset/winStart),
        # and is wrong exactly on the leading positions where the clamp makes the
        # covered range shorter than the window.
        "module": _swap(
            _BASE, _I_PUSH,
            "    out := out.push ((xs.drop start).take window)\n"),
        "refinement": "taking a fixed window length from each start ignores that "
                      "the leading positions cover a SHORTER range (the start is "
                      "clamped to the beginning of the sequence while the right "
                      "edge has not yet advanced). Those leading positions are "
                      "exactly the ones the F2P cases pin: for an aligned window "
                      "of 3 the first position must cover two elements, not three, "
                      "so its reduction disagrees with the reference and the F2P "
                      "closeness assertion FAILS; the non-aligned cases that "
                      "already passed break the same way. It would NOT resolve.",
        "rationale": "REJECT from `result = (range xs.length).map (windowAt xs "
                     "window center)`: `windowAt` takes `stop - start` elements, "
                     "which is smaller than `window` on every clamped leading "
                     "position, so the produced slice list differs from the "
                     "windowAt-mapped list there. Independent of the offset "
                     "rivals — this one leaves `winOffset`/`winStart` exactly "
                     "right and corrupts only the extent, so it also probes the "
                     "`window` binder in its own right (the extent is where the "
                     "window length enters the result directly). Witnessed at "
                     "window 2 over a length-3 sequence, aligned. If it verified "
                     "=> SPEC-TOO-WEAK (admits an over-long leading slice).",
        "witness": _witness("[5,6,7]", 2, "true"),
    },
]
