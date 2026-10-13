"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-22871 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct offsetSelection`` tactic
body, is changed — both regions the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct offsetSelection`` obligation
survives with a byte-identical header) and swaps in a candidate implementation;
it is checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must ELABORATE against the
rival and FAIL, by a real verdict, against an impl known to satisfy the spec).

DEFENDED SURFACE (one contracted method, one top-level post-image clause, no
``require`` clause — the admitted domain is total):

  offsetSelection (initShow : Bool) (stats : List (Nat × List Int))
        return (out : Nat × Bool)
      ensures out = offsetDecision initShow stats                          (C1)

``offsetDecision`` is a fully transparent, front-recursive ``def`` over the
method's own two arguments (there is NO opaque answer-key oracle — the ``axioms``
region declares nothing, so C1 is grounded, not an echo). It scans the paired
per-component observations from the finest component to the coarsest and folds
several independent facets, each a distinct sub-domain a rival can get wrong:

  * LEVEL PINNING — the reported component number is the FIRST one that changes
    over the ticks, in the given finest→coarsest scan order. A rival scanning the
    other direction reports the wrong component when two components both change.
  * ALL-CONSTANT DEFAULT — when NO component changes over the ticks, the reported
    component is the FINEST default (number five — in the finest→coarsest scan
    order the component numbers run 5 down to 0, so five is the most precise one)
    and the offset keeps ``initShow``. A rival returning a different default
    number is wrong there, and so is one that reports the right default number
    with the wrong offset flag.
  * OFFSET SUPPRESSION — ``suppressOffset lvl col`` is the conjunction of two
    factors: the component is one of the two coarsest (its number is below two)
    AND its column includes the starting-boundary value one. The offset is hidden
    exactly on that conjunction; otherwise it keeps ``initShow``. Each factor is a
    separate sub-domain, and the load-bearing one is the value-one factor: the
    behavioural change under test adds precisely that conjunct, so the crux edge
    is a coarse component that varies but does NOT sit at its starting boundary
    (the offset must remain shown so the unchanging coarser part is surfaced).
  * ``initShow`` PASS-THROUGH — wherever suppression does NOT fire, the result's
    second field is exactly ``initShow``, never a constant. A rival that hardcodes
    it is wrong on the whole ``initShow = false`` half of the domain.

Both binders are read-only (neither is declared ``mut``). The reject witnesses
move ``initShow`` across both ``true`` and ``false`` and move ``stats`` across
coarse/fine components, columns with and without the value one, varying and
constant columns, and single- vs multi-component tables.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's MANDATORY
    ``frame-mutation-write-c1`` rival writes into a read-only column held at a
    fractional heap permission so that the value-one condition is forged rather
    than computed, and Viper rejects it for INSUFFICIENT PERMISSION. Lean and
    Velvet are referentially transparent: ``initShow`` / ``stats`` are immutable
    values, this bundle declares NO ``mut`` parameter, and there is no heap,
    aliasing, or permission system to trip. There is no read-only input to
    overwrite and no substitute probe to build, so the class is vacuous (per the
    porting map, legitimately dropped, not faked). Its ARGUMENT (a real patch
    mutating the tick table before deciding the offset corrupts the labels) has no
    value footprint the spec can force here — the method returns a fresh
    ``Nat × Bool`` and mutates nothing by construction.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. C1's post-image is
    ``offsetDecision initShow stats``, a transparent fold over the method's own
    arguments; there is no answer key to echo. The honest cheapest correct impl
    is carried as a POSITIVE control (``pos-control-direct-decision``), and any
    WRONG scan/suppression fails ``out = offsetDecision initShow stats``.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1: the exact
    pre-change defect (drop the value-one factor of the suppression), its
    complement (never suppress), the other factor of the suppression (drop the
    coarse-level guard), the wrong scan direction, the wrong all-constant
    default, and the hardcoded offset flag. Each is correct on part of the domain
    and wrong on a sub-domain, and each is refuted at a distinct concrete point.
  * DIVERGENCE — CLOSED, and closed by the frozen semantics rather than by a
    case. This bundle runs under ``set_option loom.semantics.termination "total"``
    with ``open TotalCorrectness`` and a ``decreasing (stats.length - i) +
    (if stopped then 0 else 1)`` clause on the scan, so a non-terminating impl no
    longer satisfies C1 vacuously: it is refused before its postcondition is
    considered. (An earlier version of this bullet said the bundle previously set
    ``"partial"``, under which a diverging impl DID verify, and filed that as a known
    spec hole against an internal findings doc. No velvet bundle is ``partial``: all
    500 set ``"total"``, and the ``set_option`` elaborator itself runs
    ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), so the option and the ``open``
    cannot disagree. Nothing here ever verified vacuously.) Measured on this carrier,
    not
    assumed: a loop spliced ahead of the frozen body with NO measure is refused
    with ``error: Decreasing annotations are required in total correctness
    semantics``, and a body that stalls the scan (never advances ``i``, never sets
    ``stopped``) leaves an unsolved ``decreasing_1`` descent goal. The nagini
    sibling carries NO ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case, so
    there is nothing to port and, the hole now being closed, nothing to report.

    One measured caveat, restated precisely, because the earlier wording here drew
    the wrong conclusion from a correct experiment. What was measured: a file that
    sets the option to ``"total"`` and then writes an EXPLICIT ``open
    PartialCorrectness`` AFTER it elaborates the ``decreasing`` clause as a
    well-typed no-op and generates no ``decreasing_1`` goal, so a stalled body and
    a blatantly increasing measure both verify at exit 0 there. That stands. What
    does NOT follow is the conclusion drawn from it, that ``the set_option alone is
    NOT sufficient`` and that ``the open line, not the set_option, is what carries
    this class``. The ``set_option`` is not inert: its own elaborator opens the
    matching scope (``Loom/MonadAlgebras/WP/Options.lean``, ``openScope``, where
    ``"total"`` opens ``TotalCorrectness``), and ``Velvet/Syntax.lean:386`` opens
    the same scope by default, so setting the option DOES put the file in the total
    scope. The experiment only shows that a LATER explicit re-open of the partial
    scope shadows it, which is ordinary Lean scoping and not a property of the
    option. This bundle contains no ``open PartialCorrectness`` at all: line 4 is
    the option at ``"total"`` and line 7 is ``open TotalCorrectness DemonicChoice``,
    in ``Solution.lean`` and ``Solution_prepatch.lean`` alike. So the class is
    carried here, and the caveat describes a configuration this bundle does not
    have.

WITNESS MECHANICS ON THIS BUNDLE — and why the FROZEN impl cannot be the witness
subject. C1's carrier is fully transparent, so each rival is written LOOP-FREE
and each witness extracts the executable program and refutes C1 DIRECTLY:

    (match offsetSelectionExec <initShow> <stats> with | DivM.res r => r
       | _ => (0, false))  ≠  offsetDecision <initShow> <stats>

i.e. the rival's own output DIFFERS from the transparent post-image at one
concrete input — a direct C1 violation the elaborator sees, and every witness
elaborates against its rival (exit 0, measured).

The frozen impl, however, keeps a ``while`` loop, and under
``set_option loom.semantics.choice "demonic"`` its extracted program elaborates
through ``Classical.choice``, which the kernel cannot unfold. So ``decide``
against gold is stuck for EVERY claim, and gold's exit code carries no
information. Measured here at ``initShow = true``, ``stats = [(1, [2,3])]``:

    claim                                       vs GOLD          vs REFERENCE
    ``…Exec … = offsetDecision …``  (TRUE)      fails, STUCK     exit 0
    ``…Exec … ≠ offsetDecision …``  (FALSE)     fails, STUCK     fails, real verdict

Both directions fail identically against gold (``did not reduce to `isTrue` or
`isFalse```), so a forged witness asserting the rival is CORRECT would clear both
halves. That is the ``witness-undecided`` defect, and it is exactly why every
reject case here carries ``witness_reference = _LOOPFREE``: a loop-free variant
that implements the frozen spec by returning the post-image directly. It shares
the frozen spec (region surgery), VERIFIES under the frozen proof unchanged
(measured, exit 0), and — the column that matters — DECIDES in both directions,
so its refusal of a witness is a real verdict rather than a stuck kernel. The
gate re-checks both of those properties itself before using it. It is also
shipped as the ``pos-control-direct-decision`` positive, so the battery records
that loop-freeness is not what any rival is being rejected for.

No witness binds a hypothesis (every input is a concrete literal that decides
C1), so no consistency probe is needed and no witness can be inconsistent. No
banned token (``sorry`` / ``admit`` / ``native_decide`` / ``axiom`` / ``opaque``).
Every case was checked out-of-band with ``scripts/lean_verify.sh``: each witness
ELABORATES against its rival (exit 0), FAILS by a real ``decide`` verdict against
the reference (exit 1, not stuck), each full rival module does NOT verify, and
every ``expect="verify"`` module does. Independently re-derived in the audit lane:
all 7 witnesses rebuilt three ways each (vs rival exit 0; vs ``_LOOPFREE`` exit 1
with ``Tactic `decide` proved that the proposition … is false``; vs the FROZEN
impl exit 1 but ``did not reduce to `isTrue` or `isFalse``` — confirming the
stuck-kernel table above and the need for ``witness_reference``), and the
non-impl, non-proof bytes of all 12 case modules diffed byte-for-byte against the
frozen file (identical, so no case reformats or weakens the ``ensures`` clause).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle declares no ``axiom`` and
no A-reference deep model (the whole decision is modeled directly by the pure
``offsetDecision`` / ``suppressOffset`` / ``colVaries`` / ``colHasOne`` defs; the
``axioms`` region is empty), so there is nothing here for this gate to probe. The
nagini sibling's axiom-soundness / containment probes over the real column
reductions are G-AX's job regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-22871"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the FROZEN impl body: everything strictly between the method's single
# ---- `-- impl-start` / `-- impl-end` markers. Every variant replaces exactly
# ---- this text, so each edit lies wholly inside the one impl region and
# ---- same_spec holds by construction (both facts asserted at load by _swap).
# ---- Includes the loop's `decreasing` clause: under `total` semantics the
# ---- measure is part of the frozen impl text, so every anchor that quotes the
# ---- loop down to its `do` carries it, and every case `module` that ships a
# ---- WHOLE rival loop needs a measure of its own -- else the rival is refused
# ---- for a MISSING ANNOTATION instead of for its behaviour, which would turn an
# ---- expect="verify" case into a spurious failure and an expect="reject" case
# ---- into a hollow pass. Checked: no rival module's log mentions `Decreasing
# ---- annotations are required`; all 7 are rejected on C1. ----
_IMPL = (
    "    -- impl-start\n"
    "    let mut showOffset := initShow\n"
    "    let mut chosenLevel : Nat := 5\n"
    "    let mut stopped := false\n"
    "    let mut i := 0\n"
    "    while i < stats.length ∧ stopped = false\n"
    "      invariant i ≤ stats.length\n"
    "      invariant if stopped then (chosenLevel, showOffset) = offsetDecision initShow stats\n"
    "                else showOffset = initShow ∧ chosenLevel = 5 ∧\n"
    "                     offsetDecision initShow stats = offsetDecision initShow (stats.drop i)\n"
    "      done_with stopped = true ∨ i = stats.length\n"
    "      decreasing (stats.length - i) + (if stopped then 0 else 1)\n"
    "    do\n"
    "      let lvl := (stats[i]!).1\n"
    "      let col := (stats[i]!).2\n"
    "      if colVaries col then\n"
    "        chosenLevel := lvl\n"
    "        if suppressOffset lvl col then\n"
    "          showOffset := false\n"
    "        stopped := true\n"
    "      else\n"
    "        i := i + 1\n"
    "    return (chosenLevel, showOffset)\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- the FROZEN proof body (tactic script only; elided from the spec view, so
# ---- the admissibility case that adds an in-region assert may retune it to
# ---- clear the extra goal without touching the spec or the `prove_correct`
# ---- header). Rivals and positives leave it as-is — the rejection is carried by
# ---- the witness, and each positive's reshape keeps the same residual goal. ----
_PROOF = (
    "prove_correct offsetSelection by\n"
    "  loom_solve\n"
    "  all_goals\n"
    "    rw [offsetDecision_step initShow stats i (by omega)] at invariant_2\n"
    "    simp_all"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _impl_reproved(body, new_proof):
    """Impl body replaced AND the proof retuned (for the admissibility case,
    whose in-region assert leaves an extra decidable goal)."""
    return _swap(_impl(body), _PROOF, new_proof)


# ---- THE WITNESS SUBJECT. The frozen impl's `while` loop elaborates through
# ---- `Classical.choice` under `loom.semantics.choice "demonic"`, so `decide`
# ---- against it is stuck for EVERY claim and its exit code discriminates
# ---- nothing (`witness-undecided`; see the module docstring's measured table).
# ---- This loop-free variant implements the SAME frozen spec by returning the
# ---- post-image directly: it shares the spec by region surgery, VERIFIES under
# ---- the frozen proof unchanged, and REDUCES under `decide` in both directions,
# ---- so its refusal of a witness is a real verdict. Shipped as a positive too
# ---- (`pos-control-direct-decision`), so loop-freeness is visibly not the
# ---- reason any rival is rejected. The gate re-verifies it before using it. ----
_LOOPFREE = _impl("    return offsetDecision initShow stats")


# ---- witness preamble + builder. Each witness extracts the executable program
# ---- and refutes C1 DIRECTLY on the TRANSPARENT `offsetDecision`, in a file
# ---- whose `prove_correct` block is stripped so no tactic script can mask the
# ---- verdict. Every input is a concrete literal: no hypothesis is bound, so no
# ---- witness can rest on contradictory assumptions. ----
_EXTRACT = "extract_program_for offsetSelection\n\n"


def _witness(init_show, stats):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match offsetSelectionExec {init_show} ({stats}) with "
        "| DivM.res r => r | _ => (0, false))\n"
        f"      ≠ offsetDecision {init_show} ({stats}) := by\n"
        "  decide\n"
    )


# ---- a loop-free rival that scans `stats` with `find?` (its `…Exec` reduces
# ---- under `decide`, so the witness elaborates against it). `some_ret` is the
# ---- return at the first varying component `p`; `none_ret` is the all-constant
# ---- fall-through. ----
def _find(some_ret, none_ret="(5, initShow)"):
    return _impl(
        "    match stats.find? (fun p => colVaries p.2) with\n"
        f"    | some p => return {some_ret}\n"
        f"    | none => return {none_ret}")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. The first two keep the `while` scan (so the frozen proof
    # closes unchanged) and reshape the offset decision at the chosen component;
    # the third drops the loop entirely and is also the witness subject.
    # =====================================================================
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the suppressed flag as an explicit conditional
        # assignment (`showOffset := if suppressOffset … then false else
        # showOffset`) instead of the guarded write. Observationally identical
        # (`showOffset` already holds `initShow` at the chosen component), so C1
        # still discharges and the frozen loop proof closes as-is.
        "module": _impl(
            "    let mut showOffset := initShow\n"
            "    let mut chosenLevel : Nat := 5\n"
            "    let mut stopped := false\n"
            "    let mut i := 0\n"
            "    while i < stats.length ∧ stopped = false\n"
            "      invariant i ≤ stats.length\n"
            "      invariant if stopped then (chosenLevel, showOffset) = offsetDecision initShow stats\n"
            "                else showOffset = initShow ∧ chosenLevel = 5 ∧\n"
            "                     offsetDecision initShow stats = offsetDecision initShow (stats.drop i)\n"
            "      done_with stopped = true ∨ i = stats.length\n"
            "      decreasing (stats.length - i) + (if stopped then 0 else 1)\n"
            "    do\n"
            "      let lvl := (stats[i]!).1\n"
            "      let col := (stats[i]!).2\n"
            "      if colVaries col then\n"
            "        chosenLevel := lvl\n"
            "        showOffset := if suppressOffset lvl col then false else showOffset\n"
            "        stopped := true\n"
            "      else\n"
            "        i := i + 1\n"
            "    return (chosenLevel, showOffset)"),
        "rationale": (
            "a correct impl computing the suppressed flag as a conditional "
            "assignment (`showOffset := if suppressOffset … then false else "
            "showOffset`) rather than a guarded write assembles the identical "
            "decision — `showOffset` already holds `initShow` at the chosen "
            "component — so `out = offsetDecision initShow stats` still discharges "
            "and the frozen loop proof closes unchanged. Ports the nagini "
            "pos-control-branch-reorder. Must verify, else SPEC-TOO-STRONG "
            "(over-fit to the guarded-write code form). Measured: verifies."
        ),
    },
    {
        "id": "pos-control-collapsed-coarse",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the suppression decision to a typed local `sup` before
        # the guard, then branch on it. Same value flow (`sup = suppressOffset lvl
        # col`), different code shape; cross-shape soundness control.
        "module": _impl(
            "    let mut showOffset := initShow\n"
            "    let mut chosenLevel : Nat := 5\n"
            "    let mut stopped := false\n"
            "    let mut i := 0\n"
            "    while i < stats.length ∧ stopped = false\n"
            "      invariant i ≤ stats.length\n"
            "      invariant if stopped then (chosenLevel, showOffset) = offsetDecision initShow stats\n"
            "                else showOffset = initShow ∧ chosenLevel = 5 ∧\n"
            "                     offsetDecision initShow stats = offsetDecision initShow (stats.drop i)\n"
            "      done_with stopped = true ∨ i = stats.length\n"
            "      decreasing (stats.length - i) + (if stopped then 0 else 1)\n"
            "    do\n"
            "      let lvl := (stats[i]!).1\n"
            "      let col := (stats[i]!).2\n"
            "      let sup := suppressOffset lvl col\n"
            "      if colVaries col then\n"
            "        chosenLevel := lvl\n"
            "        if sup then\n"
            "          showOffset := false\n"
            "        stopped := true\n"
            "      else\n"
            "        i := i + 1\n"
            "    return (chosenLevel, showOffset)"),
        "rationale": (
            "a correct impl that binds the suppression decision to a typed local "
            "`sup := suppressOffset lvl col` before the guard leaves the value "
            "flow unchanged, so C1 still discharges and the frozen loop proof "
            "closes as-is. Ports the nagini pos-control-collapsed-coarse. "
            "Independently correct, must verify (cross-shape soundness control). "
            "Measured: verifies."
        ),
    },
    {
        "id": "pos-control-direct-decision",
        "kind": "soundness",
        "expect": "verify",
        # The loop-free shape, and the subject every reject witness is refuted
        # against. Carried as its own positive so the battery RECORDS that
        # loop-freeness verifies against this spec — i.e. that no rival below is
        # being rejected merely for dropping the loop.
        "module": _LOOPFREE,
        "rationale": (
            "the maximally different correct shape: no loop, no invariant, no "
            "index — return the decision directly, so C1 discharges by "
            "reflexivity and the frozen proof closes unchanged. Two jobs. (1) A "
            "cross-shape soundness control: the spec must not be over-fit to the "
            "iterative scan, since the modeled behaviour is a value, not a "
            "traversal; if this cannot verify the spec is SPEC-TOO-STRONG. (2) It "
            "is the `witness_reference` every reject case below names, so shipping "
            "it here makes the battery attest that the witness subject VERIFIES "
            "against the frozen spec, and that loop-freeness is not the property "
            "any rival is rejected for. Measured: verifies (exit 0)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admissibility-read-first-element
    # case. That case established the read-only fractional-permission
    # precondition on an F2P-shaped input (read c0[0], assert the length
    # equalities). This method carries NO `require` clause (the pre-conditions
    # region is empty), so nothing could exclude a normal input and the classic
    # "a normal input is admitted" probe is vacuous. Re-aimed at the residual
    # admissibility risk on a total domain: that the post-image is DEGENERATE
    # (e.g. constant) so no rival could be distinguished. This case discharges an
    # in-region `assert`, at three concrete F2P-shaped points, that the decision
    # genuinely VARIES with the input — a coarse component that varies but is not
    # at its starting boundary keeps the offset SHOWN (the crux edge), a coarse
    # component that varies AND sits at its boundary HIDES it, and an all-constant
    # table reports the finest default. The impl is kept verbatim so C1
    # still discharges; the proof is retuned only to clear the extra decidable
    # goal (allowed — the tactic body is elided from the spec view). The assert is
    # live, not decoration: a false claim about the same point leaves an unsolved
    # goal (confirmed empirically).
    # =====================================================================
    {
        "id": "admiss-decision-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `adm\n"
            "      (offsetDecision true [(1, [2,3])] = (1, true) ∧\n"
            "       offsetDecision true [(1, [1,2])] = (1, false) ∧\n"
            "       offsetDecision false [(5, [7,7])] = (5, false)))\n"
            "    let mut showOffset := initShow\n"
            "    let mut chosenLevel : Nat := 5\n"
            "    let mut stopped := false\n"
            "    let mut i := 0\n"
            "    while i < stats.length ∧ stopped = false\n"
            "      invariant i ≤ stats.length\n"
            "      invariant if stopped then (chosenLevel, showOffset) = offsetDecision initShow stats\n"
            "                else showOffset = initShow ∧ chosenLevel = 5 ∧\n"
            "                     offsetDecision initShow stats = offsetDecision initShow (stats.drop i)\n"
            "      done_with stopped = true ∨ i = stats.length\n"
            "      decreasing (stats.length - i) + (if stopped then 0 else 1)\n"
            "    do\n"
            "      let lvl := (stats[i]!).1\n"
            "      let col := (stats[i]!).2\n"
            "      if colVaries col then\n"
            "        chosenLevel := lvl\n"
            "        if suppressOffset lvl col then\n"
            "          showOffset := false\n"
            "        stopped := true\n"
            "      else\n"
            "        i := i + 1\n"
            "    return (chosenLevel, showOffset)",
            "prove_correct offsetSelection by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [offsetDecision_step initShow stats i (by omega)] at invariant_2; simp_all)"),
        "rationale": (
            "the post-image is non-degenerate at three concrete F2P-shaped points: "
            "a coarse component that varies but is NOT at its starting boundary "
            "keeps the offset shown (`(1, true)` — the crux edge of the fix), a "
            "coarse component that varies AND sits at its boundary hides it "
            "(`(1, false)`), and an all-constant table reports the finest "
            "default (`(5, false)`). So the spec genuinely constrains the result "
            "rather than admitting a constant. The in-region assert must discharge "
            "(else the modeled behavior would be degenerate); the impl is kept "
            "verbatim so C1 still discharges. Re-aimed from the nagini "
            "admissibility-read-first-element, whose read-only-precondition half "
            "has no counterpart on this referentially-transparent, require-free "
            "carrier. If it cannot verify, PRECOND-TOO-STRONG / degenerate spec."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each keeping the frozen `prove_correct` block (which
    # no longer closes for the reshaped impl) and carrying a machine-checked
    # refutation witness at a DISTINCT concrete input plus the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P. All
    # attack C1 (`out = offsetDecision initShow stats`). Every witness names
    # `witness_reference = _LOOPFREE`, because gold's `while` loop cannot decide
    # anything and so cannot serve as the discriminating subject (docstring).
    # =====================================================================
    {
        "id": "rival-drop-value-one",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change defect: at a coarse component (number below two) suppress
        # the offset whenever that component varies, DROPPING the value-one factor
        # of the suppression. Correct wherever the coarse component's column
        # includes the value one; wrong when it varies but is NOT at its starting
        # boundary — where the offset must stay shown.
        "module": _find("(p.1, if decide (p.1 < 2) then false else initShow)"),
        "refinement": (
            "this is the exact pre-change behaviour: at a coarse labelling "
            "component the offset is suppressed whenever the component varies, "
            "ignoring whether that component ever sits at its starting boundary. "
            "On the failing scenario the ticks span a handful of consecutive "
            "months with the starting month absent, so the coarse component varies "
            "but never carries the boundary value — the offset is wrongly hidden "
            "and the unchanging coarser part of the date never shows anywhere. "
            "This is the reported bug; the faithful patch is the un-fixed code and "
            "does NOT resolve the failing test."
        ),
        "rationale": (
            "REJECT from C1 (`out = offsetDecision initShow stats`): "
            "`suppressOffset lvl col` requires BOTH the coarse-level guard AND "
            "`colHasOne col`; dropping the value-one factor suppresses the offset "
            "on a coarse varying component whose column omits the boundary value, "
            "where the post-image keeps `initShow`. Refuted at "
            "`initShow = true`, `stats = [(1, [2,3])]` (a coarse component that "
            "varies with no boundary value): the impl yields `(1, false)`, the "
            "post-image `(1, true)`. If it verified => SPEC-TOO-WEAK (admits the "
            "bug)."
        ),
        "witness": _witness("true", "[(1, [2,3])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "rival-never-suppress",
        "kind": "uniqueness",
        "expect": "reject",
        # The complement facet: never suppress the offset, even at a coarse
        # component that varies AND carries the boundary value one. Correct
        # wherever the offset should stay shown; wrong on exactly the sub-domain
        # the fix keeps suppressing.
        "module": _find("(p.1, initShow)"),
        "refinement": (
            "a counterpart that never suppresses the offset reintroduces the "
            "redundant coarser label the earlier fix removed: when a coarse "
            "component varies AND sits at its starting boundary, the offset should "
            "be hidden, and this shows it — so the concise-formatter cases that "
            "expect an empty offset regress. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1: the post-image hides the offset on the conjunction "
            "(coarse component AND boundary value present), and this impl keeps "
            "`initShow` there. Refuted at `initShow = true`, "
            "`stats = [(1, [1,2])]` (a coarse component that varies and includes "
            "the boundary value one): the impl yields `(1, true)`, the post-image "
            "`(1, false)` — the opposite sub-domain from rival-drop-value-one, so "
            "the value-one factor is attacked from both sides. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness("true", "[(1, [1,2])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "rival-drop-level-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # The OTHER factor of the suppression: suppress the offset whenever the
        # column carries the boundary value one, DROPPING the coarse-level guard.
        # Correct at coarse components; wrong at a FINE component that varies and
        # happens to carry the boundary value, where the offset must stay shown.
        "module": _find("(p.1, if colHasOne p.2 then false else initShow)"),
        "refinement": (
            "a counterpart that suppresses the offset at ANY component carrying "
            "the boundary value, ignoring how coarse the component is, hides the "
            "offset for a fine-grained axis (e.g. one spanning seconds) merely "
            "because a fine component happens to sit at its starting boundary — "
            "corrupting the offset on the fine-labelling cases the concise "
            "formatter P2P pins. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1: `suppressOffset` conjoins the coarse-level guard with "
            "`colHasOne`; dropping the level guard suppresses at a fine component "
            "whose number is not below two. Refuted at `initShow = true`, "
            "`stats = [(5, [1,2])]` (the FINEST component varies and carries the "
            "boundary value): the impl yields `(5, false)`, the post-image "
            "`(5, true)` — moving the chosen component to the fine range no other "
            "witness probes. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("true", "[(5, [1,2])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "rival-wrong-scan-direction",
        "kind": "uniqueness",
        "expect": "reject",
        # Scan the components in the REVERSED (coarsest-first) order, reporting the
        # coarsest varying component instead of the finest. On a table where both a
        # fine and a coarse component vary, this pins the wrong component number.
        "module": _impl(
            "    match (stats.reverse).find? (fun p => colVaries p.2) with\n"
            "    | some p => return (p.1, if suppressOffset p.1 p.2 then false else initShow)\n"
            "    | none => return (5, initShow)"),
        "refinement": (
            "the real scan runs from the finest component to the coarsest and "
            "stops at the FIRST that changes, selecting the finest varying "
            "component to index the tick format strings. Scanning coarsest-first "
            "selects the wrong component when both a fine and a coarse component "
            "vary, producing the wrong tick label granularity — the "
            "concise-formatter P2P assertions on the rendered labels would not "
            "resolve."
        ),
        "rationale": (
            "REJECT from C1: `offsetDecision` reports the first varying component "
            "in the given finest→coarsest order; reversing the scan reports the "
            "coarsest instead. Refuted at `initShow = false`, "
            "`stats = [(5, [2,3]), (0, [7,8])]` (both components vary): the "
            "post-image reports the finest, `(5, false)`, and the impl the "
            "coarsest, `(0, false)`. The only witness with a MULTI-component "
            "table, so it is also the only one that probes the scan order at all. "
            "Ports the nagini partial-domain-wrong-scan-direction. If it verified "
            "=> SPEC-TOO-WEAK."
        ),
        "witness": _witness("false", "[(5, [2,3]), (0, [7,8])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "rival-wrong-allconst-default",
        "kind": "uniqueness",
        "expect": "reject",
        # When NO component varies the spec reports the finest default
        # (number five); this rival reports number zero instead. Correct whenever
        # some component varies; wrong only on the all-constant table.
        "module": _find(
            "(p.1, if suppressOffset p.1 p.2 then false else initShow)",
            "(0, initShow)"),
        "refinement": (
            "the real scan, finding no component that changes over the ticks, "
            "resets to the finest default component (number five, the finest "
            "format) for a single-instant axis. Reporting number zero instead "
            "would index the coarsest format for a degenerate/constant range — the "
            "wrong label. The concise-formatter P2P cases with a constant range "
            "would not resolve."
        ),
        "rationale": (
            "REJECT from C1: on the all-constant table `offsetDecision` returns "
            "`(5, initShow)` and this impl returns `(0, initShow)`. Refuted at "
            "`initShow = false`, `stats = [(5, [7,7])]` (a single CONSTANT "
            "component — nothing varies, the only witness on that sub-domain): the "
            "post-image is `(5, false)`, the impl `(0, false)`. Ports the nagini "
            "partial-domain-allconst-wrong-level. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("false", "[(5, [7,7])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "rival-hardcode-offset-shown",
        "kind": "uniqueness",
        "expect": "reject",
        # The `initShow` PASS-THROUGH facet, which no other rival attacks: report
        # the offset as shown wherever suppression does not fire, instead of
        # returning the caller's incoming flag. Agrees with the post-image on the
        # whole `initShow = true` half of the domain, so it is a NEAR-MISS refuted
        # only at `initShow = false` — which is why it carries its own witness
        # rather than sharing one.
        "module": _find("(p.1, if suppressOffset p.1 p.2 then false else true)",
                        "(5, true)"),
        "refinement": (
            "the incoming flag is the caller's own decision about whether an "
            "offset is wanted at all, taken upstream of this scan; the scan may "
            "only ever CLEAR it, never set it. A counterpart that reports the "
            "offset as shown regardless would resurrect an offset the caller had "
            "already turned off, so an axis configured without an offset would "
            "start rendering one — a regression on the concise-formatter cases "
            "that pin an empty offset, and no help to the failing test (whose "
            "incoming flag is already set, which is exactly why this rival passes "
            "it while corrupting the other half of the domain). It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from C1: wherever `suppressOffset` does not fire the "
            "post-image's second field is `initShow`, not the constant `true`. "
            "Refuted at `initShow = false`, `stats = [(5, [2,3])]` (a varying fine "
            "component, no suppression): the impl yields `(5, true)`, the "
            "post-image `(5, false)`. ADDED beyond the nagini set, which never "
            "attacks the pass-through: nagini's six columns are the only inputs "
            "there, whereas this carrier takes the incoming flag as a separate "
            "binder that a rival can ignore outright. Without this case no witness "
            "would show that a rival mishandling ONLY that binder is caught — the "
            "battery's `initShow = false` points would all be ones where the "
            "reported component number is independently wrong. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness("false", "[(5, [2,3])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "rival-empty-table-default",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The nil arm of `offsetDecision` in isolation. Every
        # other rival routes the all-constant case through the same `none`
        # fall-through, so a rival wrong ONLY on the EMPTY table agrees with the
        # post-image at every point any other witness names — the narrowest
        # near-miss in the battery, and the only case pinning the nil equation.
        "module": _impl(
            "    match stats with\n"
            "    | [] => return (0, initShow)\n"
            "    | _ =>\n"
            "      match stats.find? (fun p => colVaries p.2) with\n"
            "      | some p => return (p.1, if suppressOffset p.1 p.2 then false else initShow)\n"
            "      | none => return (5, initShow)"),
        "refinement": (
            "a counterpart that special-cases the no-observations table and "
            "reports the coarsest component instead of the finest default would "
            "index the wrong format string for an axis with nothing to scan — a "
            "degenerate range renders against the coarsest rather than the most "
            "precise format. It agrees with the fixed behaviour everywhere else, "
            "so it does NOT resolve the failing test and regresses the "
            "degenerate-range formatter cases."
        ),
        "rationale": (
            "REJECT from C1 (`out = offsetDecision initShow stats`): the nil arm "
            "of `offsetDecision` returns `(5, initShow)`, and this impl returns "
            "`(0, initShow)` there. Refuted at `initShow = true`, `stats = []` — "
            "the EMPTY table, a sub-domain no other witness in this battery "
            "reaches (every other point has at least one component, so all of "
            "them route through the cons arm). ADDED BY AUDIT: without it the nil "
            "equation `offsetDecision s [] = (5, s)` is pinned only by positives, "
            "never attacked, and a rival wrong on exactly that arm would be "
            "caught by no witness here. Verified out-of-band: the rival module "
            "does NOT verify (exit 1), the witness ELABORATES against the rival "
            "(exit 0) and FAILS against `_LOOPFREE` by a real `decide` verdict "
            "(exit 1, `Tactic \\`decide\\` proved that the proposition … is "
            "false`). If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("true", "([] : List (Nat × List Int))"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "pos-control-find-scan",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT. The SHAPE every reject case above is written in — a
        # loop-free `stats.find?` scan — but CORRECT. This is the control that
        # makes the six rivals' rejections attributable to their WRONGNESS rather
        # than to their shape: without it the battery never shows that the
        # `find?` skeleton itself can satisfy the frozen spec. Needs real proof
        # work (the frozen script's `invariant_2` does not exist without the
        # loop), so the tactic body is retuned — allowed, the proof region is
        # elided from the spec view, and the `prove_correct offsetSelection`
        # header plus every `ensures` clause stay byte-identical. No `sorry`, no
        # new axiom, no added top-level lemma: the bridging equation is a `have`
        # local to the tactic body.
        "module": _impl_reproved(
            "    match stats.find? (fun p => colVaries p.2) with\n"
            "    | some p => return (p.1, if suppressOffset p.1 p.2 then false else initShow)\n"
            "    | none => return (5, initShow)",
            "prove_correct offsetSelection by\n"
            "  have key : ∀ (s : Bool) (xs : List (Nat × List Int)),\n"
            "      offsetDecision s xs =\n"
            "        (match xs.find? (fun p => colVaries p.2) with\n"
            "         | some p => (p.1, if suppressOffset p.1 p.2 then false else s)\n"
            "         | none => (5, s)) := by\n"
            "    intro s xs\n"
            "    induction xs with\n"
            "    | nil => rfl\n"
            "    | cons hd tl ih =>\n"
            "      rw [offsetDecision_cons', List.find?_cons]\n"
            "      by_cases hc : colVaries hd.2\n"
            "      · simp [hc]\n"
            "      · simp [hc, ih]\n"
            "  loom_solve\n"
            "  all_goals simp_all [key]"),
        "rationale": (
            "ADDED BY AUDIT, and the control the reject lane was missing. All six "
            "rivals are written as a loop-free `stats.find?` scan; this is that "
            "SAME skeleton, correct. It must verify, else the six rejections "
            "above would be confounded — a reader could not tell whether they "
            "were rejected for being WRONG or merely for abandoning the frozen "
            "`while` loop. (`pos-control-direct-decision` returns the post-image "
            "verbatim, so it discharges C1 by reflexivity and never exercises the "
            "scan skeleton at all.) It also independently probes the spec for "
            "over-fitting: the frozen post-image is front-recursive, this impl is "
            "a library `find?`, and the two are equal only up to an induction, so "
            "if this could NOT be proven the spec would be SPEC-TOO-STRONG "
            "against a faithful reshape. Measured: verifies (exit 0)."
        ),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING. The sibling battery has 9 SPEC cases (1 MANDATORY
# frame-mutation rival, 5 partial-domain uniqueness rivals, 2 soundness
# positives, 1 admissibility) and 2 AXIOM_TESTS. The sibling contracts one
# function `determine_level` over SIX permission-guarded columns c0..c5 with
# per-column if-branches; this bundle models the SAME decision deeply as
# `offsetDecision initShow stats` over `List (Nat × List Int)` — a faithful
# narrowing that unifies the six columns into one scanned list and the two
# coarse-level offset branches (month c1 / year c0) into one `suppressOffset lvl
# col = decide (lvl < 2) && colHasOne col`. Every sibling SPEC case is accounted
# for below.
#
#   nagini case                              -> here
#   -----------------------------------------------------------------------
#   frame-mutation-write-c1 (MANDATORY)      -> (none)                        VACUOUS
#   partial-domain-month-suppress-always     -> rival-drop-value-one          PORTED
#   partial-domain-year-suppress-always      -> rival-drop-value-one          MERGED
#   partial-domain-wrong-scan-direction      -> rival-wrong-scan-direction    PORTED
#   partial-domain-allconst-wrong-level      -> rival-wrong-allconst-default  PORTED
#   partial-domain-never-suppress            -> rival-never-suppress          PORTED
#   pos-control-branch-reorder               -> pos-control-branch-reorder    RE-SHAPED
#   pos-control-collapsed-coarse             -> pos-control-collapsed-coarse  RE-SHAPED
#   admissibility-read-first-element         -> admiss-decision-nondegenerate RE-AIMED
#   (no sibling counterpart)                 -> rival-drop-level-guard        ADDED
#   (no sibling counterpart)                 -> rival-hardcode-offset-shown   ADDED
#   (no sibling counterpart)                 -> pos-control-direct-decision   ADDED
#   (no sibling counterpart)                 -> rival-empty-table-default     ADDED (audit)
#   (no sibling counterpart)                 -> pos-control-find-scan         ADDED (audit)
#   AXIOM_TESTS (2)                          -> (none)                        DROPPED (G-AX lane)
#
# 4 ported, 1 merged, 2 re-shaped, 1 re-aimed, 5 added, 1 vacuous. 12 velvet SPEC
# cases (4 soundness, 1 admissibility, 7 uniqueness) vs 9 nagini SPEC cases.
#
# AUDIT ADDITIONS (independent adversarial re-derivation of this battery).
# ADDED (rival-empty-table-default): the nil arm of `offsetDecision` was pinned
#   only by positives. Every pre-audit witness names a table with at least one
#   component, so all six route through the cons arm and a rival wrong ONLY on
#   `stats = []` was refuted by nothing. Now attacked at `initShow = true`,
#   `stats = []`.
# ADDED (pos-control-find-scan): all six rivals share one loop-free `find?`
#   skeleton, and no pre-audit positive used it — `pos-control-direct-decision`
#   returns the post-image verbatim and discharges C1 by reflexivity. So nothing
#   in the battery showed that the SHAPE the rivals are written in can satisfy the
#   spec, leaving their rejections confounded between "wrong" and "reshaped".
#   This case is that skeleton, correct, and it verifies. It doubles as the
#   sharpest SPEC-TOO-STRONG probe here: the post-image is front-recursive and
#   this impl is a library `find?`, equal only up to an induction.
# AUDIT PROBES that found NOTHING (recorded so the next reader need not re-run
#   them). Six NEW wrong impls beyond the shipped rivals were each REJECTED by
#   the frozen spec, so no SPEC-TOO-WEAK hole was found: `colVaries` replaced by
#   `length > 1`; the coarse-level threshold widened to `lvl ≤ 2`; the boundary
#   value changed from one to zero; the all-constant arm hardcoding the offset
#   flag to `false`; `colVaries` weakened to "last differs from first" (refuted at
#   `[(3, [2,3,2])]`, a column that varies internally but whose ends agree); and
#   the empty-table rival now shipped above. Two correct reshapes were also
#   probed: the `find?` scan (now shipped as pos-control-find-scan) and an
#   explicit `match`-on-cons impl recursing through `offsetDecision` on the tail —
#   both VERIFY, so no SPEC-TOO-STRONG hole either.
# AUDIT re-derivation of the two dropped classes, per case:
#   frame-mutation-write-c1 — INEXPRESSIBLE, and now demonstrated rather than
#     asserted. An impl assigning to the read-only binder (`stats := []`) does not
#     reach the spec at all: Velvet refuses it at elaboration with "`stats` cannot
#     be mutated, only variables declared using `let mut` can be mutated", i.e. a
#     LANGUAGE error, not a postcondition violation, so no witness could attribute
#     the rejection to C1. The class's ARGUMENT was also probed as a value-level
#     substitute — an impl FORGING the boundary condition by prepending the value
#     one to the column (`colHasOne (1 :: p.2)`) rather than reading it. That is
#     expressible and is correctly rejected, but it is not a new case: prepending
#     one makes `colHasOne` unconditionally true, so the impl is EXTENSIONALLY
#     IDENTICAL to rival-drop-value-one (checked over 5102 inputs) and is refuted
#     at the same point. Shipping it would have been a duplicate, not coverage.
#   partial-domain-year-suppress-always — the MERGE above is sound and was
#     re-checked, not taken on trust: the level-0 (year) witness point
#     `initShow = true`, `stats = [(0, [2,3])]` was built against the
#     rival-drop-value-one impl and DOES discriminate (elaborates against the
#     rival, refuted against `_LOOPFREE` by a real `decide` verdict). It refutes
#     the SAME impl at a second point rather than testing a second clause, so it
#     stays merged.
# Nothing was dropped for being hard to prove: every positive here closes under
# the frozen proof (two of them verbatim), and no obligation was weakened, no
# helper lemma added, no `sorry`/`admit`/`native_decide`/`axiom` introduced.
#
# MERGED (partial-domain-year-suppress-always -> rival-drop-value-one): the
#   nagini file splits the pre-patch offset bug into two rivals — one at the month
#   column c1, one at the year column c0 — because those are two distinct
#   if-branches over two distinct columns. This bundle unifies them: the two
#   coarse-level branches collapse into the single modeled clause `suppressOffset
#   lvl col = decide (lvl < 2) && colHasOne col`, so the month and year variants
#   attack the SAME modeled clause. A second rival dropping the value-one factor
#   would be the same wrong impl refuted at a level-0 rather than level-1 point;
#   it is not shipped as a separate case (it would test the same clause), but note
#   `rival-drop-level-guard` DOES move the chosen component into the fine range and
#   `rival-wrong-scan-direction` uses a level-0 component, so the level binder
#   inside `stats` is exercised across coarse (1), fine (5), and year (0) values.
# RE-SHAPED (positives): both nagini positives reshape the coarse-level offset
#   decision (reorder the sub-branch / stage the flag in a typed local) while
#   keeping the returns. The velvet analogs reshape the offset write inside the
#   frozen `while` scan: pos-control-branch-reorder computes it as a conditional
#   assignment, pos-control-collapsed-coarse binds it to a typed local `sup`.
#   Both are observationally identical and verify under the frozen loop proof.
# RE-AIMED (admissibility): the nagini case reads c0[0] and asserts the length
#   equalities to attest the read-only fractional-permission precondition admits a
#   normal F2P-shaped input. This method has NO `require` clause and no heap
#   permission, so that probe is vacuous; re-aimed at proving the post-image is
#   NON-DEGENERATE (the decision genuinely varies with the input across the crux
#   shown/hidden edge and the all-constant default), discharged by an in-region
#   assert over three F2P-shaped points (decidable — the carrier computes).
# ADDED (rival-drop-level-guard): the nagini rivals attack the value-one factor
#   (month/year suppress-always, never-suppress) but NOT the coarse-level factor
#   of the suppression in isolation. `suppressOffset` conjoins TWO factors; without
#   this rival no witness would demonstrate that a rival mishandling only the
#   level guard (suppressing at a fine component) is caught, and it is the only
#   witness that moves the chosen component into the fine range with a boundary
#   value present.
# ADDED (rival-hardcode-offset-shown): this carrier takes the incoming offset flag
#   as a SEPARATE binder (`initShow`), which nagini's six-column surface does not
#   have — nagini's offset default is a literal in each return, not an input. So
#   the pass-through facet is reachable by a rival only here, and it is a NEAR-MISS
#   (it agrees with the post-image on the entire `initShow = true` half). It is the
#   case that stops `initShow` from being a binder whose false value only ever
#   appears alongside an independently wrong component number.
# ADDED (pos-control-direct-decision): the loop-free correct shape. Two jobs — a
#   cross-shape soundness control (the spec must not be over-fit to the iterative
#   scan) and the `witness_reference` subject every reject case names. Shipping it
#   as a case is what makes the battery record that the witness subject VERIFIES,
#   and that loop-freeness is not the property any rival is rejected for.
# VACUOUS (frame-mutation-write-c1, MANDATORY on nagini): the sibling writes a 1
#   into the read-only column c1 (held at a fractional heap permission) to FORGE
#   the value-one condition rather than compute it, tripping INSUFFICIENT
#   PERMISSION before the postcondition is considered. This backend is
#   referentially transparent: `initShow`/`stats` are immutable values, this bundle
#   declares NO `mut` binder, and there is no heap, aliasing, or permission system.
#   There is no read-only input to overwrite and no substitute probe to build, so
#   the class is vacuous (per the porting map, legitimately dropped, not
#   fabricated). Its ARGUMENT (a real patch mutating the tick table corrupts the
#   labels) has no value footprint the spec can force here — the method returns a
#   fresh `Nat × Bool` and mutates nothing by construction (directive 5, discharged
#   by the ABSENCE of a `mut` binder).
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness / containment probes
#   over the real column reductions are G-AX's job (mapping.md); the G-PBT gate
#   ignores AXIOM_TESTS regardless. This bundle consumes no `axiom` and declares no
#   A-reference deep model (the whole decision is a transparent pure `def`), so
#   there is nothing for this gate to probe. meta.json records G-AX as skipped for
#   exactly that reason.
#
# DIVERGENCE (CLOSED BY THE SEMANTICS; still not shipped as a case). CORRECTED:
#   an earlier version of this entry said the bundle previously ran under
#   `set_option loom.semantics.termination "partial"`, under which a
#   non-terminating impl satisfies C1 vacuously and verifies, and filed that as a
#   known spec hole shared by a `partial` cohort, citing an internal findings doc.
#   No velvet bundle is `partial`: all 500 set `"total"`, and the `set_option`
#   elaborator itself runs `openScope `TotalCorrectness`
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so the option and the `open`
#   cannot disagree and the cited cohort has no referent. The bundle runs under
#   `"total"` with `open TotalCorrectness` and a
#   `decreasing (stats.length - i) + (if stopped then 0 else 1)` clause on the
#   scan, so the hole is closed by the semantics: a diverging rival cannot be
#   written against this spec. There is still no CASE to ship, and the reason is
#   the same one that applies to every `total` bundle — a reject case needs a
#   witness that refutes the rival, and a rival refused at elaboration for a
#   missing/non-descending measure never reaches C1, so no witness can attribute
#   its rejection to the postcondition. The nagini sibling carries no
#   `diverge-*` / `nonterm-*` / `weak-diverge` case either, so nothing to port.
#
#   THE MEASURE, and why it is not the bare counter. The loop condition is
#   COMPOUND (`i < stats.length ∧ stopped = false`), so the loop has two exits and
#   the body has two paths: the else path advances `i`, but the `colVaries` path
#   sets `stopped := true` and leaves `i` UNCHANGED. `stats.length - i` therefore
#   does NOT fall on the stopping iteration, and Loom rejects it — measured, with
#   an unsolved `decreasing_1: stats.length - i` goal reducing to `⊢ False` on
#   both `suppressOffset` branches of that path. Adding `+ (if stopped then 0
#   else 1)` supplies the missing unit: the stopping path holds `stats.length - i`
#   fixed and drops the flag term 1 → 0, while the advancing path leaves the flag
#   term at 1 and decreases `stats.length - i` by one (`i < stats.length` on entry,
#   so the subtraction is not saturating). Every path the body can take strictly
#   decreases the sum, and it verifies (exit 0).
#
#   CAVEAT, restated precisely; the earlier wording overstated it. The descent
#   obligation comes from the `TotalCorrectness` WP instance, and a file that sets
#   `"total"` and then writes an EXPLICIT `open PartialCorrectness` AFTER it
#   elaborates the `decreasing` clause as a well-typed no-op and emits NO
#   `decreasing_1` goal: in that configuration a stalled body that never advances
#   `i` and never sets `stopped` VERIFIES (exit 0), and so does `decreasing i + 1`,
#   which increases; only the linter's presence check fires. That measurement
#   stands, but it does NOT show the obligation comes from the `open` rather than
#   the `set_option`. The option's own elaborator opens the matching scope
#   (`Loom/MonadAlgebras/WP/Options.lean`, `openScope`, where `"total"` opens
#   `TotalCorrectness`), and Velvet/Syntax.lean:386 opens it by default, so setting
#   the option puts the file in the total scope; what the experiment shows is only
#   that a LATER explicit re-open of the partial scope shadows it, which is
#   ordinary Lean scoping. This bundle has no `open PartialCorrectness`: line 4 is
#   `"total"` and line 7 is `open TotalCorrectness DemonicChoice`. The obligation
#   is live here, and the `decreasing_1` goals cited above are the proof of it.
#
# CLAUSE / BINDER / POINT COVERAGE. The only impl-constraining clause is C1
#   (`out = offsetDecision initShow stats`). Its independent facets are each
#   DEFENDED (by the three positives + the non-degeneracy admissibility case,
#   which pin the shown/hidden/default decisions on gold) and ATTACKED: level
#   pinning by rival-wrong-scan-direction, the all-constant default by
#   rival-wrong-allconst-default, BOTH factors of the suppression — the value-one
#   factor from both sides (rival-drop-value-one hides where it must show;
#   rival-never-suppress shows where it must hide) and the coarse-level factor
#   (rival-drop-level-guard suppresses at a fine component) — and the `initShow`
#   pass-through by rival-hardcode-offset-shown. Both input binders are varied by
#   the reject witnesses: `initShow` takes both `true` (rival-drop-value-one,
#   rival-never-suppress, rival-drop-level-guard) and `false`
#   (rival-wrong-scan-direction, rival-wrong-allconst-default,
#   rival-hardcode-offset-shown); `stats` takes six DISTINCT shapes —
#   `[(1,[2,3])]`, `[(1,[1,2])]`, `[(5,[1,2])]`, `[(5,[2,3]),(0,[7,8])]`,
#   `[(5,[7,7])]`, `[(5,[2,3])]`, and (audit) `[]` — spanning coarse (1)/fine
#   (5)/year (0) components, columns with and without the boundary value, varying
#   and constant columns, and empty/single/multi-component tables. Seven distinct
#   witness points, so pts=7 and no binder is held fixed by every witness. Both
#   ARMS of the post-image are now attacked: the cons arm by six rivals and the
#   nil arm by rival-empty-table-default. In particular the
#   `initShow = false` half is probed by a rival (rival-hardcode-offset-shown)
#   whose ONLY error is in that binder, so a rival mishandling just the incoming
#   flag cannot hide behind an independently wrong component number.
#
# WITNESS FORM, and why `witness_reference` is on every reject case. Each witness
#   extracts the executable program and refutes C1 directly against the
#   TRANSPARENT `offsetDecision` at a concrete literal input; each rival is
#   loop-free (`stats.find?` / `stats.reverse`) so its `…Exec` reduces and the
#   witness ELABORATES against it. The FROZEN impl cannot be the second subject:
#   its `while` loop elaborates through `Classical.choice` under
#   `loom.semantics.choice "demonic"`, so `decide` against gold is stuck for every
#   claim. Measured at `initShow = true`, `stats = [(1,[2,3])]`: the TRUE claim
#   (`…Exec … = offsetDecision …`) and the FALSE one (`… ≠ …`) BOTH fail against
#   gold with `did not reduce to `isTrue` or `isFalse``, so gold's exit code is
#   information-free and a forged witness asserting the rival is CORRECT would
#   clear both halves — the `witness-undecided` defect. Against `_LOOPFREE` the
#   same two claims come apart (true: exit 0; false: exit 1 with `Tactic `decide`
#   proved that the proposition … is false`), so its verdicts are real. Hence
#   every reject case names `witness_reference = _LOOPFREE`, which the gate
#   independently re-checks (shares the frozen spec, and VERIFIES) before using.
#   No witness binds a hypothesis, so none can rest on contradictory assumptions
#   and no consistency probe applies. All checked with scripts/lean_verify.sh:
#   7/7 witnesses exit 0 against their rival, 7/7 fail against `_LOOPFREE` by a
#   real `decide` verdict (not stuck), 7/7 rival modules do NOT verify, 5/5
#   `expect="verify"` modules DO verify, and the admissibility assert is live (a
#   false claim about the same point leaves an unsolved goal — re-confirmed in the
#   audit lane, where an assert claiming `offsetDecision true [(1, [2,3])] =
#   (1, false)` fails to discharge).
AXIOM_TESTS = []
