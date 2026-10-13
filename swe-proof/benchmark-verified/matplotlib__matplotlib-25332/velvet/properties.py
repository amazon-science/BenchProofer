"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25332 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the two ``prove_correct`` obligations survive with byte-identical statements)
and swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — the witness must ELABORATE against the rival and FAIL against
the discriminating subject, which on this bundle is the ``witness_reference``
below rather than the frozen solution (see WITNESS SUBJECT).

DEFENDED SURFACE (TWO contracted methods, each a total pure transform over a
grouping registry's reference table, modeled as ``List (Ref × List Ref)`` — one
row is a representative reference paired with its group's member references):

  structure Ref where target : Int ; weak : Bool          -- (which object, live?)
  strongify r = { r with weak := false }                   -- one ref → serialisable
  weaken    r = { r with weak := true  }                   -- one ref → live
  strongifyEntry e = (strongify e.1, e.2.map strongify)    -- a whole row
  weakenEntry    e = (weaken e.1,    e.2.map weaken)
  strongifyMap / weakenMap : front-recursive fold over the rows

  snapshot (mapping) ensures out = strongifyMap mapping    -- THE load-bearing clause #1
  rebuild  (state)   ensures out = weakenMap state          -- THE load-bearing clause #2
                     ensures ∀ r, weaken (strongify r) = weaken r   -- round-trip identity

so each clause pins several independent sub-behaviours of the desired result
(the input is the registry's reference table; the output is its transformed
table):

  * WEAK-FLIP: every returned reference has its liveness flag flipped the right
    way (snapshot → all serialisable/``weak=false``; rebuild → all live/
    ``weak=true``) — the whole point of the transform;
  * TARGET-PRESERVED: each reference still points at the SAME object
    (``target`` unchanged) — the grouping must survive the transform;
  * EVERY-ROW / ORDER: one output row per input row, IN ORDER, no row skipped;
  * EVERY-MEMBER: the transform is applied to a row's representative AND to
    every member of its group (both ``e.1`` and ``e.2``), not just one of them.

``strongifyMap`` / ``weakenMap`` are GROUNDED in the input (total front-recursive
folds over the argument); the ``axioms`` region is empty (no opaque answer key to
echo — directive 8), so the ungrounded-oracle probe is replaced by honest
positive controls. The two INPUT BINDERS are ``mapping`` (snapshot) and ``state``
(rebuild); each binder's length, row order, representative field, group-member
list, and the ``target``/``weak`` fields of every reference all matter.

THE CARRIER IS TRANSPARENT (no opaque callee) and ``Ref`` derives ``DecidableEq``.
A witness reaches the impl through Velvet's extractor
(``extract_program_for snapshot`` gives ``snapshotExec m = NonDetT.run
(snapshot m)``) and states ``snapshotExec m ≠ DivM.res (strongifyMap m)`` at a
concrete ``m``. Each reject rival is a straight-line loop-free CLOSED FORM whose
extracted program DOES reduce; the residual literal (in)equality is closed by
``simp`` with the record injectivity lemma (``Ref.mk.injEq``) plus the
fold/entry/flip unfoldings.

WITNESS SUBJECT — why every reject case carries a ``witness_reference``.
The FROZEN impl carries a backward ``while`` loop whose extracted program does
NOT reduce under ``simp``: the ``forIn Lean.Loop.mk`` fixpoint (with its
invariant/done/decreasing gadgets) stays stuck, so the witness's build against
the frozen solution fails with ``unsolved goals`` over an UNREDUCED loop term.
That failure carries NO information about the spec, and it was MEASURED not
argued: the claim ``snapshotExec [(⟨0,true⟩, [])] = DivM.res (strongifyMap
[(⟨0,true⟩, [])])`` — which is TRUE of the frozen impl, the exact OPPOSITE of a
refutation — ALSO fails against the frozen solution (exit 1, same unreduced
``forIn`` residual), as does the trivially true claim at the empty table. So the
frozen loop-solution cannot serve as the discriminating subject: it rejects
every claim regardless of truth, and a witness refuted against it would attest
to a refutation the kernel never performed. (This is the stuck-reduction defect
the gate screens for on the ``decide`` path; it arrives here as a stuck ``simp``
residual instead, which that screen does not match — so the case must name the
subject explicitly rather than rely on it.)

The repair is the gate's own ``witness_reference`` mechanism: each reject case
names ``_LOOPFREE_REF``, the loop-free impl of BOTH methods (``return
strongifyMap mapping`` / ``return weakenMap state``). It is checked by the gate
rather than trusted — it must share the frozen spec and must VERIFY — and it
does both (measured: shares the spec, builds exit 0). Because it is loop-free
its extracted program REDUCES, so its exit code is informative: a claim TRUE of
it elaborates (exit 0 on both methods, measured), and each of the nine real
witnesses fails against it with the fully-reduced residual ``⊢ False`` — a
SEMANTIC refutation of the concrete claim, not a syntactic accident. That is
sound for the same reason gold was: an impl the verifier ACCEPTS cannot violate
its own spec, so a genuine "the spec is violated at this input" cannot hold of
it. All builds re-run out-of-band with ``scripts/lean_verify.sh``: rival exit 0,
reference exit 1 with ``⊢ False``, for EVERY reject case; every positive control
built to verify.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries two such
    rivals (``frame-mutation-capture`` / ``frame-mutation-ident``): they write to
    a carrier held at ``Acc(.,1/2)`` and are rejected by the PERMISSION SYSTEM,
    not by a postcondition. Lean/Velvet are referentially transparent: ``mapping``
    and ``state`` are immutable values, this bundle declares NO ``mut`` binder over
    any input, and there is no heap and no aliasing — so there is no read-only
    input to overwrite and no rejection to reproduce. No substitute probe is
    fabricated (per the porting map, this whole class is vacuous on Lean/Velvet).
  * DIVERGENCE / NON-TERMINATION - nothing to ship, and the class is CLOSED BY
    THE SEMANTICS rather than open. The nagini sibling ships no ``diverge-*`` /
    ``nonterm-*`` case, so there is none to port. RETRACTED IN FULL: the text that
    stood here said the bundle sets ``loom.semantics.termination "partial"``, that
    a non-terminating impl therefore satisfies every ``ensures`` VACUOUSLY and
    would verify, and that this is an already-escalated spec hole measured across
    a cohort of ``partial`` bundles in an internal findings doc. Every part of that
    is false. Line 4 reads ``"total"``, as it does in all 500 velvet bundles, and
    the option cannot drift from the file's ``open TotalCorrectness`` because the
    ``set_option`` elaborator ITSELF runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean``, lines 169-186). The cited cohort has
    no referent and the doc no longer exists. Under ``total`` a postcondition is
    claimed of ALL runs, not only terminating ones, so each of the two frozen
    loops and any loop a rival splices owes a descent obligation
    ``measure b' < measure b``. Measured on THIS bundle with real builds, proofs
    reduced to a bare ``loom_solve``: an unmeasured spun loop is refused at
    elaboration (``Decreasing annotations are required in total correctness
    semantics``), and the sharper shape that CARRIES a measure the body never
    shrinks (``while q > 0 / invariant 0 <= q / done_with q = 0 / decreasing q``,
    body ``q := q``) is REJECTED on the measure's own goal, ``case
    «decreasing_1: q»`` with residual ``q < q`` unsolved, in BOTH methods. So a
    diverging rival is rejected, not admitted. It is still not written as a reject
    case, but for the WITNESS contract rather than a spec weakness: the refusal
    fires at the ``method`` itself, ahead of any appended tester, so no witness can
    ELABORATE against such a rival and the gate would read it as
    ``witness-unproven``. See the footer entry, which already carries the corrected
    account.
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. Each nagini
    partial-domain rival re-expresses onto one sub-behaviour of one clause.
  * UNGROUNDED-ORACLE ECHO — N/A. Both post-images are total ``def``s over the
    method's own input; there is no answer key to echo. Replaced by the positive
    controls (a cheapest direct impl + a structurally different forward ``map``
    per method).

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; both transforms are concrete folds over the input, validated == the
real patched callees by conformance_check.py / G-CONF — not this gate's job, and
the gate ignores ``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25332"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (an impl body
# between -- impl-start / -- impl-end, or a prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and both prove_correct statements
# byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of `snapshot` (the backward per-row loop that
# prepends each strongified row and returns the accumulator).
_SNAP_IMPL = (
    "    let mut result : List (Ref × List Ref) := []\n"
    "    let mut i := mapping.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ mapping.length\n"
    "      invariant result = strongifyMap (mapping.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let e := mapping[i - 1]!\n"
    "      result := strongifyEntry e :: result\n"
    "      i := i - 1\n"
    "    return result"
)

# The WHOLE executable body of `rebuild` (same backward shape, weakening).
_REB_IMPL = (
    "    let mut result : List (Ref × List Ref) := []\n"
    "    let mut i := state.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ state.length\n"
    "      invariant result = weakenMap (state.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let e := state[i - 1]!\n"
    "      result := weakenEntry e :: result\n"
    "      i := i - 1\n"
    "    return result"
)

# The frozen prove_correct tactic bodies (each unique, elided from the spec view).
_SNAP_PROOF = (
    "prove_correct snapshot by\n"
    "  loom_solve\n"
    "  rw [strongifyMap_drop_step mapping i (by omega) (by omega)]\n"
    "  simp_all"
)
_REB_PROOF = (
    "prove_correct rebuild by\n"
    "  loom_solve\n"
    "  rw [weakenMap_drop_step state i (by omega) (by omega)]\n"
    "  simp_all"
)

for _anchor in (_SNAP_IMPL, _REB_IMPL, _SNAP_PROOF, _REB_PROOF):
    assert _BASE.count(_anchor) == 1, "Solution.lean drifted from expected region text"


def _snap_impl(body):
    """Variant with ONLY snapshot's impl body replaced (proof frozen)."""
    return _swap(_BASE, _SNAP_IMPL, body)


def _reb_impl(body):
    """Variant with ONLY rebuild's impl body replaced (proof frozen)."""
    return _swap(_BASE, _REB_IMPL, body)


def _snap_reproved(body, proof):
    return _swap(_swap(_BASE, _SNAP_IMPL, body), _SNAP_PROOF, proof)


def _reb_reproved(body, proof):
    return _swap(_swap(_BASE, _REB_IMPL, body), _REB_PROOF, proof)


# ---------------------------------------------------------------------------
# The witness-discrimination SUBJECT for every reject case (see WITNESS SUBJECT
# in the module docstring). The frozen backward `while` loop's extracted program
# does not reduce, so a witness build against the frozen solution fails with
# `unsolved goals` over an unreduced `forIn` fixpoint for EVERY claim — measured,
# including for claims that are TRUE of the frozen impl. This is the same
# loop-free spec-sharing impl as the two `-direct` positives, both methods at
# once: it shares the frozen spec (only impl regions + prove_correct bodies
# differ) and it VERIFIES, both of which the gate re-checks before using it. Its
# extracted program REDUCES, so each witness fails against it with the reduced
# residual `⊢ False` — a semantic refutation rather than a stuck term.
# ---------------------------------------------------------------------------
_LOOPFREE_REF = _swap(
    _swap(
        _swap(
            _swap(_BASE, _SNAP_IMPL, "    return strongifyMap mapping"),
            _REB_IMPL, "    return weakenMap state"),
        _SNAP_PROOF, "prove_correct snapshot by\n  loom_solve"),
    _REB_PROOF, "prove_correct rebuild by\n  loom_solve")


# ---- witness preamble. The spec is a `method` CONTRACT over a transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `snapshotExec m` is `NonDetT.run (snapshot m)`; `≠ DivM.res (strongifyMap
# ---- m)` says the impl's output contradicts the first ensures clause at that
# ---- concrete input. Checked in a file whose `prove_correct` blocks are
# ---- stripped, so no tactic script can mask the verdict. `Ref` derives
# ---- DecidableEq but the extracted loop fixpoint does not `decide`; the residual
# ---- literal (in)equality is closed by `simp` with the record injectivity lemma
# ---- + fold/entry/flip unfoldings. The loop-free rival reduces under this simp;
# ---- gold's loop stays stuck, so the same witness fails on gold — the required
# ---- discrimination. Verified out-of-band with two real builds per reject case.
def _wit_snap(inp: str) -> str:
    return ("extract_program_for snapshot\n\n"
            f"example : snapshotExec ({inp}) ≠ "
            f"DivM.res (strongifyMap ({inp})) := by\n"
            "  unfold snapshotExec snapshot\n"
            "  simp [NonDetT.run, pure, strongifyMap, strongifyEntry, strongify, "
            "List.map, Ref.mk.injEq]\n")


def _wit_reb(inp: str) -> str:
    return ("extract_program_for rebuild\n\n"
            f"example : rebuildExec ({inp}) ≠ "
            f"DivM.res (weakenMap ({inp})) := by\n"
            "  unfold rebuildExec rebuild\n"
            "  simp [NonDetT.run, pure, weakenMap, weakenEntry, weaken, "
            "List.map, Ref.mk.injEq]\n")


# Concrete Ref literals used in the witness inputs. `L` (live/weak) is a
# reference in the live-table form; `S` (strong/serialisable) is the snapshot
# form; `target` distinguishes which object each points at.
def _L(t):  # live weak reference to object `t`
    return f"{{ target := {t}, weak := true }}"


def _S(t):  # strong serialisable reference to object `t`
    return f"{{ target := {t}, weak := false }}"


def _row(rep, members="([] : List Ref)"):
    return f"({rep}, {members})"


# The admissibility probe's concrete input: a two-row table whose FIRST row
# carries a representative over a two-member group and whose second row has an
# empty group — the shape the failing round trip actually presents (a grouping
# registry holding a non-trivial group plus a singleton). `_ADM_LIVE` is that
# table in live form, `_ADM_STRONG` the same table in snapshot form.
_ADM_LIVE = (f"([{_row(_L(3), '[' + _L(4) + ', ' + _L(5) + ']')}, "
             f"{_row(_L(6))}] : List (Ref × List Ref))")
_ADM_STRONG = (f"([{_row(_S(3), '[' + _S(4) + ', ' + _S(5) + ']')}, "
               f"{_row(_S(6))}] : List (Ref × List Ref))")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness). Each obligation is defended twice: by the
    # cheapest GROUNDED direct impl and by a structurally DIFFERENT forward
    # `map` replacing the frozen BACKWARD accumulate loop. A faithful correct
    # impl MUST verify — else the clause is over-fit / SPEC-TOO-STRONG. All four
    # verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-snapshot-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest impl: return the grounded post-image directly. Loop
        # gone, so the residual goal closes under `loom_solve` alone.
        "module": _snap_reproved(
            "    return strongifyMap mapping",
            "prove_correct snapshot by\n  loom_solve"),
        "rationale": "the post-image `strongifyMap mapping` is GROUNDED in the "
                     "input (a total fold, no opaque answer key), so `return "
                     "strongifyMap mapping` is the honest cheapest CORRECT impl. It "
                     "MUST verify — the clause is literally `out = strongifyMap "
                     "mapping` — else clause #1 is SPEC-TOO-STRONG. Also shows the "
                     "spec is not echo-vulnerable: any wrong constant fails it.",
    },
    {
        "id": "pos-snapshot-map",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT impl: a FORWARD `map strongifyEntry`
        # over the rows, replacing the frozen backward accumulate loop. Same
        # values on every input (`(e :: es).map f = f e :: es.map f` is exactly
        # `strongifyMap`'s cons clause). Proof retuned in-region to a short
        # induction; the spec view is untouched.
        "module": _snap_reproved(
            "    return (mapping.map strongifyEntry)",
            "prove_correct snapshot by\n"
            "  loom_solve\n"
            "  induction mapping with\n"
            "  | nil => rfl\n"
            "  | cons e es ih => simp [strongifyMap_cons, ih]"),
        "rationale": "structurally different CORRECT impl: a FORWARD map "
                     "(`mapping.map strongifyEntry`) rather than the frozen "
                     "backward accumulate loop, observationally identical on every "
                     "input (the map's cons law IS strongifyMap's cons clause). A "
                     "faithful reshape MUST verify, else clause #1 is over-fit to "
                     "the backward-loop FORM => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-rebuild-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest impl for rebuild. `loom_solve` also discharges the
        # round-trip ensures (`weaken_strongify` is @[grind]).
        "module": _reb_reproved(
            "    return weakenMap state",
            "prove_correct rebuild by\n  loom_solve"),
        "rationale": "the post-image `weakenMap state` is GROUNDED in the input, so "
                     "`return weakenMap state` is the honest cheapest CORRECT impl; "
                     "it MUST verify against `out = weakenMap state` (the round-trip "
                     "clause is a `@[grind]` tautology loom_solve discharges) — else "
                     "clause #2 is SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-rebuild-map",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT impl: FORWARD `map weakenEntry`.
        "module": _reb_reproved(
            "    return (state.map weakenEntry)",
            "prove_correct rebuild by\n"
            "  loom_solve\n"
            "  induction state with\n"
            "  | nil => rfl\n"
            "  | cons e es ih => simp [weakenMap_cons, ih]"),
        "rationale": "structurally different CORRECT impl: a FORWARD map "
                     "(`state.map weakenEntry`) rather than the frozen backward "
                     "loop, identical on every input. A faithful reshape MUST "
                     "verify, else clause #2 is over-fit to the loop FORM => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY. On a total carrier the analogue of PRECOND-TOO-STRONG is the
    # obligation being UNSATISFIABLE (or degenerate) at exactly an F2P-shaped
    # input — a spec no impl can meet at the interesting point reads, to every
    # other lane, exactly like a spec every impl meets. The pre-conditions region
    # being empty is NOT a reason to skip this: it is a reason the risk moves from
    # the `require` to the `ensures`, where this case pins it by EVALUATION at a
    # concrete two-row table with a non-trivial group.
    #
    # The in-region `assert` discharges four facts before the frozen obligation is
    # closed verbatim: the snapshot's post-image at that input is the fully
    # strongified table (so clause #1 is satisfiable there, and by a value that
    # keeps every target and the group structure), the rebuild's post-image is the
    # fully live table, the two COMPOSE to the identity on the live table (the
    # round trip is loss-free at a real input, not just at `[]`), and the snapshot
    # is not the identity there (so the obligation is non-degenerate — it demands
    # actual work at this point rather than admitting the input unchanged).
    # =====================================================================
    {
        "id": "admiss-roundtrip-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _snap_reproved(
            "    assert (with_name_prefix `admiss\n"
            f"      (strongifyMap {_ADM_LIVE} = {_ADM_STRONG}\n"
            f"       ∧ weakenMap {_ADM_STRONG} = {_ADM_LIVE}\n"
            f"       ∧ weakenMap (strongifyMap {_ADM_LIVE}) = {_ADM_LIVE}\n"
            f"       ∧ strongifyMap {_ADM_LIVE} ≠ {_ADM_LIVE}))\n"
            + _SNAP_IMPL,
            "prove_correct snapshot by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [strongifyMap_drop_step mapping i (by omega) (by omega)]; "
            "simp_all)"),
        "rationale": "ADMISSIBILITY at an F2P-shaped input (a two-row table whose "
                     "first row holds a representative over a two-member group, "
                     "plus a singleton row): both obligations are SATISFIABLE "
                     "there and the pair is NON-DEGENERATE. The assert evaluates "
                     "that the snapshot's post-image is the fully serialisable "
                     "table (every target kept, group structure intact), the "
                     "rebuild's is the fully live one, the two COMPOSE to the "
                     "identity on the live table (so the round trip is loss-free "
                     "at a real input, not merely at the empty one), and the "
                     "snapshot is NOT the identity at that input (so the clause "
                     "demands real work there). If any of those failed, the "
                     "obligation would be unsatisfiable or vacuous at exactly the "
                     "point that matters and every other lane would still look "
                     "clean. The frozen impl and proof are kept verbatim after the "
                     "assert, so the method's own `ensures` still discharges; the "
                     "assert is LIVE — replacing the final `≠` with `=` (a false "
                     "claim at the same input) leaves an unsolved goal and the "
                     "case fails to build (measured).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the F2P (the figure pickle
    # round trip through the aligned-label grouping registry). Each keeps the
    # frozen loop proof (which cannot close the loop-free impl — the intended
    # rejection); the witness, not the tactic failure, attributes the rejection
    # to the spec.
    # =====================================================================

    # ---- snapshot WEAK-FLIP clause: no strong conversion at all (prepatch twin)
    {
        "id": "weak-snapshot-no-strongify",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch behaviour: the live table is handed to the serialiser
        # verbatim; every reference is left in its live (weak) form.
        "module": _snap_impl("    return mapping"),
        "refinement": "this is the pre-patch behaviour verbatim: no serialisable "
                      "snapshot is taken, so the table still carries a live "
                      "(non-serialisable) reference — exactly the reported bug. The "
                      "value serialiser then still raises on that reference and the "
                      "F2P figure pickle round trip does NOT resolve.",
        "rationale": "REJECT from `out = strongifyMap mapping` (WEAK-FLIP): "
                     "strongifyMap flips every reference to the serialisable form, "
                     "but the rival returns the input unchanged, so on any table "
                     "with a live reference the results differ. Refuted at a single "
                     f"live-reference row `[{_row(_L(0))}]`: gold flips it strong, "
                     "the rival leaves it weak. Varies `mapping` to one live row.",
        "witness": _wit_snap(f"[{_row(_L(0))}]"),
        "witness_reference": _LOOPFREE_REF,
    },

    # ---- snapshot EVERY-MEMBER clause: strongify the representative, not group
    {
        "id": "weak-snapshot-members-untouched",
        "kind": "uniqueness",
        "expect": "reject",
        # Strongify each row's representative but leave its group MEMBERS in
        # their input form — attacks the "and every member of its group"
        # sub-behaviour that the single-row rivals do not.
        "module": _snap_impl(
            "    return (mapping.map (fun e => (strongify e.1, e.2)))"),
        "refinement": "a counterpart that converted only each row's representative "
                      "and left the grouped members untouched would leave a live "
                      "reference among the group members; the serialiser still "
                      "raises on that member, so the F2P does NOT resolve. The fix "
                      "must convert the representative AND every member.",
        "rationale": "REJECT from `out = strongifyMap mapping` (EVERY-MEMBER): "
                     "strongifyEntry maps strongify over `e.2` too, but the rival "
                     "copies the group list through, so any row with a live member "
                     f"disagrees. Refuted at `[{_row(_S(0), '[' + _L(1) + ']')}]` "
                     "(a strong representative over a live member): gold flips the "
                     "member strong, the rival leaves it weak. Varies the "
                     "group-member list (the `e.2` field of a row).",
        "witness": _wit_snap(f"[{_row(_S(0), '[' + _L(1) + ']')}]"),
        "witness_reference": _LOOPFREE_REF,
    },

    # ---- snapshot TARGET-PRESERVED clause: flag flipped but object identity lost
    {
        "id": "weak-snapshot-target-lost",
        "kind": "uniqueness",
        "expect": "reject",
        # Produce a serialisable reference (weak=false, so the WEAK-FLIP half is
        # satisfied) but to the WRONG object (target reset to 0). Attacks the
        # identity-preservation sub-behaviour specifically.
        "module": _snap_impl(
            "    return (mapping.map (fun e => ((⟨0, false⟩ : Ref), e.2.map strongify)))"),
        "refinement": "a counterpart that produced serialisable references but "
                      "pointing at the wrong object would rebuild the grouping "
                      "around different members; the unpickled aligned-label groups "
                      "would not match the original, so the F2P (which relies on the "
                      "recovered grouping) does NOT resolve. Making a reference "
                      "strong is not enough — it must keep its object.",
        "rationale": "REJECT from `out = strongifyMap mapping` (TARGET-PRESERVED): "
                     "strongify keeps `target`, but the rival rewrites every "
                     "representative's target to 0, so any row whose representative "
                     f"points elsewhere disagrees. Refuted at `[{_row(_L(7))}]`: "
                     "gold keeps target 7, the rival returns target 0. Varies the "
                     "`target` field to a nonzero identity (the only rival that "
                     "abuses `target`).",
        "witness": _wit_snap(f"[{_row(_L(7))}]"),
        "witness_reference": _LOOPFREE_REF,
    },

    # ---- snapshot EVERY-ROW (position 0): leave the FIRST row unconverted ----
    {
        "id": "weak-snapshot-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Strongify every row EXCEPT the first, copied through unchanged. Correct
        # on the rest of the domain; diverges only on the first row.
        "module": _snap_impl(
            "    return (match mapping with | [] => [] | e :: rest => "
            "e :: rest.map strongifyEntry)"),
        "refinement": "a partial-domain counterpart that converted every row except "
                      "the first (e.g. iterating the tail only) would leave that "
                      "row's live reference in the snapshot; the serialiser still "
                      "raises, so the F2P does NOT resolve. Every row must convert, "
                      "not most rows.",
        "rationale": "REJECT from `out = strongifyMap mapping` (EVERY-ROW at "
                     "position 0): strongifyMap converts the first row like the "
                     "rest, but the rival copies it through, so the tables disagree "
                     "whenever the first row holds a live reference. Refuted at "
                     f"`[{_row(_L(0))}, {_row(_S(1))}]`: gold flips both strong, the "
                     "rival leaves the first row live. Discrimination comes from the "
                     "FIRST row of `mapping`.",
        "witness": _wit_snap(f"[{_row(_L(0))}, {_row(_S(1))}]"),
        "witness_reference": _LOOPFREE_REF,
    },

    # ---- snapshot EVERY-ROW (last position): leave the LAST row unconverted ----
    {
        "id": "weak-snapshot-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Convert every row EXCEPT the last, copied through unchanged. Correct on
        # all but the final row; diverges only there.
        "module": _snap_impl(
            "    return ((mapping.dropLast.map strongifyEntry) ++ "
            "mapping.drop (mapping.length - 1))"),
        "refinement": "a partial-domain counterpart that stopped one row short "
                      "would leave the final row's live reference in the snapshot; "
                      "the serialiser still raises, so the F2P does NOT resolve. A "
                      "single surviving live reference is enough to fail.",
        "rationale": "REJECT from `out = strongifyMap mapping` (EVERY-ROW at the "
                     "last position): strongifyMap converts the final row like the "
                     "rest, but the rival copies it through, so the tables disagree "
                     "whenever the last row holds a live reference. Refuted at "
                     f"`[{_row(_S(0))}, {_row(_L(1))}]`: gold flips both strong, the "
                     "rival leaves the last row live. Discrimination comes from the "
                     "LAST row (a distinct position from skip-first).",
        "witness": _wit_snap(f"[{_row(_S(0))}, {_row(_L(1))}]"),
        "witness_reference": _LOOPFREE_REF,
    },

    # ---- snapshot EVERY-ROW / length clause: drop the final row ----
    {
        "id": "weak-snapshot-short",
        "kind": "uniqueness",
        "expect": "reject",
        # Convert every row correctly but DROP the last one — one fewer output
        # row than input. Attacks the length/one-row-per-row half.
        "module": _snap_impl("    return (strongifyMap mapping).dropLast"),
        "refinement": "a counterpart that dropped a row would lose a member of the "
                      "grouping registry; the unpickled aligned-label groups would "
                      "have fewer entries than the original, so the recovered "
                      "grouping the F2P checks would not match — it does NOT "
                      "resolve. A dropped row is a lost group entry.",
        "rationale": "REJECT from `out = strongifyMap mapping` (EVERY-ROW / length): "
                     "strongifyMap returns one row per input row, but the rival "
                     "drops the last, so the result is one row short. Refuted at "
                     f"`[{_row(_L(5))}, {_row(_L(6))}]`: gold returns two strong "
                     "rows, the rival returns one. Varies `mapping` length (a "
                     "length-2 table) — the only rival that attacks row count.",
        "witness": _wit_snap(f"[{_row(_L(5))}, {_row(_L(6))}]"),
        "witness_reference": _LOOPFREE_REF,
    },

    # ---- rebuild WEAK-FLIP clause: no live conversion at all (prepatch twin) ----
    {
        "id": "weak-rebuild-no-weaken",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch behaviour: the stored (snapshot) table is adopted verbatim on
        # read-back, leaving every reference strong rather than restoring a live
        # one. This is the round-trip's "skip the rebuild" analogue.
        "module": _reb_impl("    return state"),
        "refinement": "this is the pre-patch read-back verbatim: no live conversion "
                      "runs, so the rebuilt registry holds strong references where "
                      "the live table demands live (weak) ones. Downstream registry "
                      "operations on the unpickled figure (which look references up "
                      "in their live form) then break, so the F2P does NOT resolve.",
        "rationale": "REJECT from `out = weakenMap state` (WEAK-FLIP): weakenMap "
                     "flips every reference to the live form, but the rival returns "
                     "the input unchanged, so on any table with a strong reference "
                     f"the results differ. Refuted at `[{_row(_S(0))}]`: gold flips "
                     "it live, the rival leaves it strong. Varies `state` to one "
                     "strong (snapshot-form) row.",
        "witness": _wit_reb(f"[{_row(_S(0))}]"),
        "witness_reference": _LOOPFREE_REF,
    },

    # ---- rebuild EVERY-MEMBER clause: weaken the representative, not group ----
    {
        "id": "weak-rebuild-members-untouched",
        "kind": "uniqueness",
        "expect": "reject",
        # Weaken each row's representative but leave its group MEMBERS strong —
        # attacks the group-member sub-behaviour on the rebuild side.
        "module": _reb_impl(
            "    return (state.map (fun e => (e.1, e.2.map weaken)))"),
        "refinement": "a counterpart that restored only the group members and left "
                      "each row's representative strong would leave a strong "
                      "reference where the live registry expects a live one; the "
                      "rebuilt registry's representative is malformed and downstream "
                      "grouping operations on the unpickled figure break, so the F2P "
                      "does NOT resolve. Both the representative and every member "
                      "must be restored.",
        "rationale": "REJECT from `out = weakenMap state` (EVERY-MEMBER, "
                     "representative): weakenEntry weakens `e.1` too, but the rival "
                     "copies the representative through, so any row with a strong "
                     f"representative disagrees. Refuted at "
                     f"`[{_row(_S(0), '[' + _S(1) + ']')}]`: gold weakens the "
                     "representative, the rival leaves it strong. Varies the "
                     "representative field (`e.1`) of a row.",
        "witness": _wit_reb(f"[{_row(_S(0), '[' + _S(1) + ']')}]"),
        "witness_reference": _LOOPFREE_REF,
    },

    # ---- rebuild EVERY-ROW (last position): leave the LAST row unconverted ----
    {
        "id": "weak-rebuild-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Restore every row EXCEPT the last, copied through unchanged.
        "module": _reb_impl(
            "    return ((state.dropLast.map weakenEntry) ++ "
            "state.drop (state.length - 1))"),
        "refinement": "a partial-domain counterpart that stopped one row short on "
                      "read-back would leave the final row's reference in the strong "
                      "(snapshot) form; the rebuilt registry then holds a strong "
                      "reference where a live one is required and downstream "
                      "operations on the unpickled figure break, so the F2P does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = weakenMap state` (EVERY-ROW at the last "
                     "position): weakenMap converts the final row like the rest, but "
                     "the rival copies it through, so the tables disagree whenever "
                     "the last row is strong. Refuted at "
                     f"`[{_row(_L(0))}, {_row(_S(1))}]`: gold weakens both, the rival "
                     "leaves the last row strong. Discrimination comes from the LAST "
                     "row of `state`.",
        "witness": _wit_reb(f"[{_row(_L(0))}, {_row(_S(1))}]"),
        "witness_reference": _LOOPFREE_REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 7 uniqueness rivals) plus a NON-EMPTY axiom lane
# (2 AXIOM_TESTS). Critically, the sibling models THREE functions over a mutable
# `List[int]` directness-flag carrier held at fractional permission:
# capture_state (all-DIRECT), restore_state (all-INDIRECT), roundtrip_weakness
# (composition). This velvet bundle narrows to the two purely-functional CHANGED
# transforms — the serialisable snapshot (`snapshot`) and the live-table rebuild
# (`rebuild`) — over the richer, HONEST carrier `List (Ref × List Ref)` (each
# reference is (which-object, live?), each row is representative + group). The
# nagini `List[int]` 0/1 flag is the abstraction this carrier REFINES: the
# value surface (which references flip, on which rows/members, keeping which
# object, in what order) carries across and is in fact RICHER here (the flag flip
# AND the target-identity AND the group structure are all modeled); the
# permission surface does not.
#
#   sibling case                       -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-capture-local-reshape  -> pos-snapshot-direct/-map      PORTED (re-expressed)
#   pos-control-restore-local-reshape  -> pos-rebuild-direct/-map       PORTED (re-expressed)
#   admissibility-restore-precondition -> admiss-roundtrip-nondegenerate PORTED (re-aimed)
#   partial-domain-capture-last        -> weak-snapshot-skip-last       PORTED
#   partial-domain-capture-first       -> weak-snapshot-skip-first      PORTED
#   partial-domain-capture-short       -> weak-snapshot-short           PORTED
#   partial-domain-restore-last        -> weak-rebuild-skip-last        PORTED
#   roundtrip-skip-restore             -> weak-rebuild-no-weaken        PORTED (re-expressed)
#   frame-mutation-capture             -> (none)                        VACUOUS
#   frame-mutation-ident               -> (none)                        VACUOUS
#   AXIOM_TESTS (A1, A2)               -> (none)                        DROPPED (G-AX/G-CONF)
#   (carrier-new)                      -> weak-snapshot-no-strongify    ADDED (whole-domain WEAK-FLIP, snapshot)
#   (carrier-new)                      -> weak-snapshot-members-untouched  ADDED (group-member sub-behaviour)
#   (carrier-new)                      -> weak-snapshot-target-lost     ADDED (identity-preservation sub-behaviour)
#   (carrier-new)                      -> weak-rebuild-members-untouched   ADDED (representative sub-behaviour)
#
# 5 sibling rivals ported directly + 1 re-expressed (roundtrip -> rebuild-no-weaken)
# + 2 positives ported (each doubled: direct + structural map) + 1 admissibility
# re-aimed onto the ensures + 4 carrier-new rivals the richer carrier exposes
# = 14 SPEC cases (4 soundness, 1 admissibility, 9 uniqueness).
# The extra rivals are NOT parity-padding: the nagini `List[int]` flag has no
# `target` field and no group/representative distinction, so its battery could
# not attack identity-preservation or the every-member sub-behaviour — this
# carrier can and must, so those clauses are defended.
#
# PORTED (4 positive controls): the sibling's two `local-reshape` positives keep
#   the flag loop but reshape it (typed local + Assert). Here the analogous
#   "same values, reshaped control flow" defence is, per method, the cheapest
#   grounded impl (`return strongifyMap/weakenMap ...`, loop removed, closes under
#   loom_solve) AND a structurally different FORWARD `map` replacing the backward
#   loop (proof retuned in-region to a short induction). Both methods defended
#   twice; all four verified to build.
# PORTED (5 partial-domain rivals): capture-last/-first/-short and restore-last
#   re-express directly as the snapshot/rebuild skip-last/skip-first/short probes;
#   roundtrip-skip-restore (return the captured all-direct state, skipping the
#   re-wrap) re-expresses as weak-rebuild-no-weaken (return the strong state,
#   skipping the live conversion) — the same "the composition ends in the wrong
#   form" defect on the modeled read-back half. Each carries a machine-checked
#   witness (two real builds).
# PORTED, re-aimed (admissibility-restore-precondition -> admiss-roundtrip-
#   nondegenerate): the sibling self-establishes that restore_state's `Requires`
#   (len match + all-direct) admits a normal input. This bundle declares no
#   `require` clause, but that does NOT make the lane vacuous — it moves the
#   PRECOND-TOO-STRONG analogue from the `require` to the `ensures`: the residual
#   risk on a total carrier is the obligation being unsatisfiable or DEGENERATE at
#   exactly an F2P-shaped input, which no other lane here can see (a spec no impl
#   can meet at the interesting point looks identical to one every impl meets).
#   "Both post-images are total `def`s, so satisfiability is free" is a fact about
#   TOTALITY, not about the obligation's content at a real input — it does not
#   establish that the round trip composes to the identity there, nor that the
#   clause demands any work there rather than admitting the input unchanged. The
#   case pins all four by EVALUATION at a two-row table with a non-trivial group,
#   as a `have`-style in-region assert discharged before the frozen obligation is
#   closed verbatim. Measured: it VERIFIES (exit 0), and the same case with the
#   final conjunct falsified FAILS (exit 1), so the assert is load-bearing.
# VACUOUS (frame-mutation-capture / frame-mutation-ident): the sibling rejects a
#   WRITE to a read-only carrier held at `Acc(.,1/2)` via the PERMISSION SYSTEM,
#   not via any postcondition. This backend is referentially transparent, declares
#   no `mut` binder over any input (`mapping`/`state` are immutable values with no
#   heap footprint), and has no aliasing — so there is no read-only input to
#   overwrite and no rejection to reproduce. Not fabricated (porting-map rule:
#   this class is vacuous on Lean/Velvet).
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
#   loop in the impl (2 loops here, measures ``i``). A rival that loops without
#   a measure is refused outright (``Decreasing annotations are required in
#   total correctness semantics``), and a rival that supplies a CONSTANT
#   measure to dodge that is refused on the measure's own goal (``case
#   «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
#   a real build. Divergence therefore does not discharge the ``ensures``
#   clauses vacuously. It is still not shipped as a G-PBT reject case, and the
#   reason is the witness contract rather than a spec weakness. A reject case
#   must carry a witness that ELABORATES against the rival, and neither diverging
#   shape gets past that. With NO measure the descent obligation fails at the
#   ``method`` itself, ahead of any appended tester, and the witness file retains
#   the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
#   module does not compile at all. With a measure that does not decrease the
#   refusal moves to the ``prove_correct`` site, which IS stripped, so that module
#   does elaborate; but the rival's post-image is then an unreduced
#   ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
#   ``decreasingGadget``, which the kernel will not normalise to a value a
#   concrete-input tester can decide. Either way the gate returns
#   ``witness-unproven``, an inconclusive outcome. Measured through the
#   gate's own ``_check_witness``, even ``example : True := trivial`` comes
#   back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
#   and would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# AXIOM_TESTS (A1 axiom-soundness, A2 axiom-containment): DROPPED. The sibling's
#   axiom lane validates a deep model of weakref/pickle primitives against the
#   real stdlib. This velvet bundle consumes no axiom `ensures` and declares no
#   deep-model reference (meta.json: axioms == [], deep_model_references == []) —
#   strongifyMap/weakenMap are concrete list arithmetic, validated == the real
#   patched callees by G-CONF. There is nothing for this gate to probe and it
#   ignores AXIOM_TESTS regardless (G-AX/G-CONF's job).
#
# BINDER / CLAUSE COVERAGE. Two input binders: `mapping : List (Ref × List Ref)`
#   (snapshot) and `state : List (Ref × List Ref)` (rebuild). Each obligation is
#   DEFENDED (two positives) and ATTACKED (>=1 reject). Every top-level clause is
#   attacked: snapshot's `out = strongifyMap mapping` by six rivals (whole-domain
#   WEAK-FLIP, every-member, target/identity, skip-first, skip-last, length);
#   rebuild's `out = weakenMap state` by three (whole-domain WEAK-FLIP,
#   representative-member, skip-last). The round-trip `∀ r, weaken (strongify r) =
#   weaken r` is a pure tautology over the deep models (no input binder, no wrong
#   impl can falsify a `def`-level identity), so it carries no rival — noted, not
#   omitted silently. The nine reject witnesses probe NINE DISTINCT input points,
#   genuinely varying BOTH binders in:
#     - length (1, 1, 1, 2, 2, 2 for snapshot; 1, 1, 2 for rebuild);
#     - row order (skip-first vs skip-last are the same shape at swapped rows);
#     - the `weak` field (a live row [L] vs a strong row [S] as the discriminating
#       point, on both the snapshot and rebuild sides);
#     - the `target` field (weak-snapshot-target-lost is the only rival that moves
#       target off 0 — target := 7);
#     - the representative (`e.1`) vs group-member (`e.2`) fields (the
#       members-untouched / target rivals put a distinct reference in `e.2`, which
#       every other witness holds empty).
#   Both fields of `Ref` (target, weak) AND both components of a row
#   (representative, group list) are abused by some rival. No two rivals share an
#   input point. pts = 9 distinct input points across 9 witnesses.
# WITNESS DISCRIMINATION (re-derived with real builds per reject case; see
#   WITNESS SUBJECT in the module docstring for the measurement that forced the
#   `witness_reference`): each witness ELABORATES against its loop-free rival
#   (exit 0 — the extracted program reduces and the record-injectivity `simp`
#   closes the inequality at the probed input) and FAILS against `_LOOPFREE_REF`
#   (exit 1, residual `⊢ False` — a REDUCED semantic refutation). The frozen
#   loop-solution is NOT the subject and must not be: its extracted `forIn`
#   fixpoint stays stuck under `simp`, so it fails every claim including claims
#   TRUE of it (measured), and its exit code discriminates nothing. No witness
#   binds a hypothesis (the carrier is transparent and decidable), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears in any witness or variant.
# SPEC-STRENGTH PROBES beyond the shipped cases (run at audit, not shipped as
#   cases): eight further WRONG impls were built against the frozen spec with its
#   friendliest proof attempts (`loom_solve`, then `all_goals grind`) — row
#   REVERSAL, the empty-list constant, rebuild-side target loss, rebuild-side
#   skip-first, rebuild-side length loss, and a double-flip `weakenMap` in the
#   snapshot slot. ALL EIGHT were rejected; no spec hole. Four further CORRECT
#   reshapes — `foldr` in place of the map/loop on both methods, and the entry
#   transform fully INLINED (bypassing strongifyEntry/weakenEntry) on both —
#   were all PROVEN to verify, so the spec is not over-fit to the loop or to the
#   entry helpers either.
#
# INDEPENDENT AUDIT (second pass, all builds re-run out-of-band; 47 witness/
# subject builds + 15 probe builds):
#   * WITNESS SUBJECT re-derived by the FORGERY test, which is what settles it.
#     For all nine reject cases: witness vs rival = exit 0; witness vs
#     `_LOOPFREE_REF` = exit 1 with a fully reduced `⊢ False`; and the FLIPPED
#     claim (`≠` -> `=`, i.e. asserting the reference is CORRECT there) vs
#     `_LOOPFREE_REF` = exit 0. The reference's exit code therefore TRACKS the
#     claim, which is what makes it evidence. Against the FROZEN solution the
#     witness and its own opposite BOTH fail (exit 1) with the same unreduced
#     `forIn Lean.Loop.mk` / `invariantGadget` residual — gold's exit code carries
#     no information about the claim, confirming it cannot be the subject and that
#     the `witness_reference` is a repair rather than an evasion.
#   * ATTACK C (is each rival actually WRONG?) re-derived independently over the
#     carrier semantics: all nine differ from the frozen post-image AT their own
#     witness input, and each differs somewhere on an exhaustive sweep of tables
#     up to length 2 over 6 distinct references. No vacuous / merely-reshaped
#     rival; nothing to drop.
#   * ATTACK D — six NEW wrong impls aimed where the shipped rivals do not reach:
#     duplicated rows (length too LONG — every shipped length rival is too short),
#     per-row last-MEMBER dropped, members flipped the WRONG way (rather than
#     copied through), target SHIFTED +1 (distinctness kept, identity lost),
#     rebuild-side group collapsed to the representative singleton, rebuild-side
#     row reversal. Each built with the friendliest proof attempts
#     (`loom_solve` / `all_goals grind` / `simp_all` / `decide`). ALL SIX rejected
#     (exit 1) => no spec hole found.
#   * ATTACK E — three NEW correct reshapes, all PROVEN to verify (exit 0): a
#     FORWARD `while` loop appending (control flow unlike both the frozen backward
#     loop and the shipped `map` positives), reverse/map/reverse on both methods.
#     Each initially failed on the AUDITOR's own tactic script and closed once the
#     `strongifyMap = map strongifyEntry` bridge (plus a `take_succ` step for the
#     forward loop) was supplied in-region — a proof gap, not a spec obstruction,
#     so no SPEC-TOO-STRONG hole.
AXIOM_TESTS = []
