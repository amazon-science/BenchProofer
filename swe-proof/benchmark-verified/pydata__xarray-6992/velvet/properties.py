"""properties.py — G-PBT falsification battery for pydata__xarray-6992 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant produced by region surgery on the
FROZEN solution: only text inside the ``-- impl-start`` / ``-- impl-end`` region,
or inside the ``prove_correct dropIndexNameSets`` tactic body, is changed. Both
regions are elided from the consumer spec view, so ``markers.same_spec`` holds by
construction and the ``prove_correct dropIndexNameSets`` header survives; a
rejection is attributable to the ``ensures`` clause, never to a tampered spec. No
case adds an ``axiom``, a helper lemma, a ``sorry``/``admit``, or
``native_decide``.

``expect:"verify"`` passes iff (in scope AND the variant verifies with the
obligation genuinely discharged). ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (ONE contracted method; SEVEN input binders)

  dropIndexNameSets (isMulti : Bool) (dim : String) (levels : List String)
      (R : List String) (V : List String) (C : List String) (dropF : Bool)
      return (out : NameSets)
    ensures out = computeNameSets isMulti dim levels R V C dropF

  A labelled-array container is observed through three name collections: the
  stored variable names ``V``, the coordinate names ``C`` (a sub-collection of
  ``V``), and the names keying a lookup index. The modeled operation releases one
  lookup index — described abstractly by its dimension name ``dim``, whether it is
  multi-level (``isMulti``), and its level coordinate names (``levels``) — and
  recomputes all three collections. ``R`` is the set of requested names; ``dropF``
  selects discard (throw the de-indexed coordinates away) versus retain (keep them
  as ordinary stored variables, no longer coordinates).

  There is NO ``require`` clause: the obligation is unconditional over all seven
  binders. The single ``ensures`` clause is FULLY PINNED and grounded
  (directive 8) in the method's own arguments: ``computeNameSets`` is a total
  ``def`` in the ``pure`` region, spelled out as a nested-if over the branch
  structure, with no opaque callee and no axiomatized answer key to echo
  (``meta.json`` declares no consumed axiom).

  Though it is ONE top-level equality, it decomposes into independently
  attackable sub-behaviours, each of which some rival below violates while the
  others hold:

    S1 COORD-SHRINK   the drop-set is subtracted from ``C`` as well as ``V``
                      (``coords := filterOut dv C``) — the load-bearing content,
                      and what keeps ``coords ⊆ vars`` intact (``subsetPreserved``)
    S2 VAR-SHRINK     the drop-set is subtracted from ``V`` (``filterOut dv V``)
    S3 CHANNEL        ``dropF`` routes each de-indexed name to the drop-set OR to
                      the fresh-variable set, never to both and never
                      unconditionally
    S4 RENAME         a reduction to exactly one kept level emits the DIMENSION
                      name as the fresh coordinate, retires the old kept-level
                      name, and keys the surviving index on the dimension
    S5 IDX-RELEASE    the released index really leaves the index collection (the
                      whole-index-goes branch emits NO surviving index)
    S6 NON-IDENTITY   something is actually removed / added; the operation is not
                      a no-op
    S7 BRANCH-SELECT  the guard that routes an input to the rebuild arm versus the
                      whole-index-goes arm reads BOTH conditions — whether the
                      dimension itself was requested AND whether any level
                      survives (added by audit: every other rival edits an
                      assignment inside a branch, so the selector itself was
                      unattacked)

PORTING THE NAGINI ARGUMENT ONTO THIS CARRIER

The nagini sibling contracts TWO functions over an immutable set carrier —
``promote_to_index`` and ``teardown_index`` — each pinning FOUR output collections
(stored variables, coordinate names, live indexes, and a fourth recording which
names are held in the index-backed representation), plus a ``well_formed``
conjunct chaining the inclusions, and each threading THREE removal channels
(discarded / retained-but-converted / displaced).

This bundle models a NARROWER surface, declared in mapping.md: ONE obligation,
THREE collections, and the discard/retain split collapsed into the boolean
``dropF``. Case-count parity would require fabricating rivals for a collection and
a promotion behaviour that do not exist here, so it is not the target. What IS
carried over is each nagini case's adversarial ARGUMENT, re-expressed where a
counterpart exists:

  * nagini ``reject-prepatch-coordnames`` (the base-commit shape: the coordinate
    collection is rebuilt from the ORIGINAL, only ever grown) ->
    ``reject-coords-never-shrink`` below, verbatim in argument and in effect. This
    is the discriminating clause; ``Solution_prepatch.lean`` is this rival.
  * nagini ``reject-convert-as-drop`` (treat a RETAINED coordinate as if
    discarded) -> ``reject-retain-as-discard``. Same attack: the nagini rival
    subtracts the retained channel from the variable/coordinate collections
    although a retained coordinate keeps its stored array; here ``dropF`` IS the
    channel selector, so the rival fills the drop-set unconditionally.
  * nagini ``reject-identity-teardown`` (partial-domain: remove nothing) ->
    ``reject-identity``.
  * nagini ``reject-teardown-overkeep-indexes`` (a released name keeps its live
    index) -> ``reject-index-stays-live``.
  * nagini ``reject-promote-no-readd`` (the base-commit sibling shape that skips
    the re-add/convert step) -> ``reject-no-rename`` below. The nagini rival
    attacks the promotion function's re-add channel; this bundle does not model
    promotion, but the same patch's structural rule reappears here as S4 (a
    reduced single level is renamed to its dimension), so the argument is ported
    onto the behaviour this carrier DOES state rather than onto a fabricated
    promotion surface.
  * nagini ``pos-teardown-combined`` / ``pos-promote-reorder`` (structurally
    different but CORRECT restructurings) -> the two soundness positives below.
  * nagini ``admiss-teardown`` (the precondition admits a normal input) ->
    ``admiss-f2p-grid``, adapted: the frozen obligation carries NO ``require``, so
    there is no precondition to establish. The surviving admissibility content is
    that the pinned relation is SATISFIABLE and NON-DEGENERATE at a realistic
    input, discharged as an in-region ground instance.

  * ``reject-vars-never-shrink`` below has no nagini counterpart: it is the S2
    attack this carrier makes available (a discarded name leaves the coordinate
    collection but keeps its stored variable — the MIRROR of the pre-patch drift,
    the same invariant broken in the other direction).

NAGINI CASES DELIBERATELY NOT PORTED (repeated in the submitted ``assessment``)

  * ``reject-no-convert-repr``. It attacks the FOURTH collection (which names are
    held in the index-backed representation) and the ``well_formed`` inclusion
    tying it to the live-index collection. This bundle models THREE collections;
    per mapping.md §2 the index-backed-vs-plain distinction is a variable's TYPE,
    not its name, and the name-set bookkeeping this bundle models is unaffected by
    it. There is no fourth collection to leave a name in, so the rival is not
    wrong on this carrier — it is inexpressible.
  * The ``promote_to_index`` half as a SURFACE. That is a second modeled function
    in nagini and is not a method here, so ``pos-promote-reorder`` has no
    counterpart. Its reject sibling's ARGUMENT is ported onto S4 as noted above;
    no substitute promotion rival is fabricated.
  * FRAME / PERMISSION-MUTATION — VACUOUS, exactly as the nagini docstring already
    concludes for its own carrier (its inputs are immutable set values carrying no
    heap permission). A fortiori here: Lean/Velvet are referentially transparent,
    every input is an immutable value, the method declares no ``mut`` binder over
    a parameter, and there is no heap and no aliasing. No substitute fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A, same reasoning the nagini sibling records: the
    post-image is pinned to ``computeNameSets`` over the method's own arguments,
    a total ``def`` with no opaque leaf. Nothing to echo.
  * DIVERGENCE / NON-TERMINATION — VACUOUS here, and for a MEASURED reason: this
    bundle sets ``loom.semantics.termination "total"``. Under total-correctness
    semantics a looping impl must carry a decreasing measure, so a diverging
    rival is refused by the verifier itself rather than satisfying the ``ensures``
    vacuously. Re-measured during the audit on a spliced non-terminating rival
    (``while spin == 0 do``, gold's obligation otherwise untouched): exit 1,
    ``error: Decreasing annotations are required in total correctness semantics``
    and the sharper shape, which cannot be dismissed as merely missing the
    annotation, is refused too: a loop CARRYING a measure that does not decrease
    (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``, body
    ``q := q``) is REJECTED on the measure's own goal - ``case «decreasing_1: q»``,
    residual ``⊢ q < q``. So the class is not a spec hole on THIS bundle and there is
    nothing to ship. Two earlier claims in this slot are retracted: that the bundle
    was ``partial`` and therefore carried a known hole (false against the frozen
    ``set_option``, which reads ``"total"``, and against the file's only correctness
    ``open``, ``TotalCorrectness``), and the corpus census that set 99 ``total``
    bundles against 401 ``partial`` ones (withdrawn: all 500 velvet bundles set
    ``"total"``).
  * ``AXIOM_TESTS`` — DROPPED. The axiom lane is G-AX's job and this gate ignores
    it; the bundle's single deep-model reference (the index-footprint neighbour)
    is validated there.

WITNESS MECHANICS. The ``ensures`` is a ``method`` contract, not a bare
predicate, so each witness reaches it through Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``) and states
``dropIndexNameSetsTester <args> = false`` at ONE concrete input — the extracted
program's result violates the postcondition there. Checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. The carrier is FULLY TRANSPARENT (``String`` has ``DecidableEq``,
``NameSets`` derives it, ``filterOut``/``List.filter`` compute), so the frozen
impl's tester and every rival's tester both reduce under ``decide`` at literal
inputs; no witness needs to condition on the carrier, so no witness binds a
hypothesis and the gate's joint-satisfiability probe has nothing to check
(``consistency_probe`` returns None for a head that binds nothing). Both halves
of every witness below were checked out-of-band with ``scripts/lean_verify.sh``:
the witness ELABORATES against its rival (exit 0) and FAILS against the frozen
solution with ``decide`` reporting the proposition FALSE (i.e. gold's tester is
``true`` there — a satisfied spec, not an unknown name or a stuck term).

BINDER COVERAGE. The spec binds ``isMulti``, ``dim``, ``levels``, ``R``, ``V``,
``C``, ``dropF``. The seven reject witnesses probe SEVEN DISTINCT input points and
every binder that the modeled behaviour depends on is MOVED across them:

  * ``dropF`` — ``true`` (reject-coords-never-shrink, reject-vars-never-shrink,
    reject-identity, reject-index-stays-live,
    reject-branch-guard-ignores-dim) AND ``false``
    (reject-retain-as-discard, reject-no-rename). The two rivals attacking the
    channel are refuted precisely on the side where they diverge from gold.
  * ``isMulti`` — ``false`` (reject-coords-never-shrink, the plain single-index
    shape the issue's own example reduces to) AND ``true`` (the other five), so
    the battery does not pin the flag.
  * ``R`` — a one-name list, a two-name list (reject-identity,
    reject-index-stays-live), and a request naming a LEVEL vs one naming the
    DIMENSION itself, which is what selects between the rebuild branch and the
    whole-index-goes branch. Both branches are probed.
  * ``levels`` — empty (the non-multi witness) and a two-name list (the rest),
    exercising both the degenerate and the multi-level footprint.
  * ``V`` / ``C`` — varied in shape: witnesses where ``V`` strictly exceeds ``C``
    (an extra non-coordinate stored name that must survive), and where the
    released name is not the only coordinate, so a drift between the two
    collections is observable in both directions.
  * ``dim`` — moved across witnesses (``"x"`` and ``"z"``), so no rival is
    refuted only at a single dimension literal.

SUB-BEHAVIOUR COVERAGE. S1 is attacked by reject-coords-never-shrink and
reject-identity; S2 by reject-vars-never-shrink, reject-retain-as-discard and
reject-identity; S3 by reject-retain-as-discard; S4 by reject-no-rename; S5 by
reject-index-stays-live and reject-identity; S6 by reject-identity; S7 by
reject-branch-guard-ignores-dim. No sub-behaviour is left unattacked, and the
obligation is defended by two soundness positives plus the admissibility ground
instance.

AUDIT RECORD (independent re-derivation, real builds, not the port's self-report)

  * STATEMENT INTEGRITY. Every case's module was reduced to its spec view (impl
    region and ``prove_correct`` body elided) and compared to the frozen file:
    all of them byte-identical (the nine cases as ported, and the tenth the audit
    added). No case reformats, weakens or restates the obligation.
  * WITNESS DISCRIMINATION, RE-DERIVED. All seven reject witnesses were rebuilt
    on both sides: rival exit 0, frozen solution exit 1, every gold-side failure
    a plain ``Tactic `decide` proved that the proposition … is false`` naming the
    witness's own concrete input. No unknown identifier, type error, stuck
    reduction or timeout anywhere in the lane.
  * FORGERY TEST (B'). For each witness a second file differing ONLY in the claim
    (``= false`` flipped to ``= true``) was built on both sides. Every pair
    inverted exactly — rival exit 1, gold exit 0 — so each exit code tracks the
    CLAIM and not the file. No hollow case in the lane.
  * ADMISSIBILITY LIVENESS. The ground instance was re-probed twice: replacing
    the asserted coordinate set with a false value fails (``decide`` proves the
    conjunction false, exit 1), and deleting the ``all_goals decide`` tail leaves
    the assert as an unsolved goal (exit 1). The assert is doing work, not
    riding along.
  * SPEC-TOO-WEAK PROBE. Eight NEW wrong impls the battery did not contain were
    built against the frozen spec: an ``||`` branch guard, the dim conjunct
    dropped, the surviving-index order flipped, the reduction threshold moved to
    2, the dimension variable left unreleased, a live index emitted on the
    non-multi retain path, the old kept-level name left in place under the
    rename, and the reset levels routed to BOTH channels at once. All eight were
    REJECTED (exit 1). No spec hole found. The second of them turned out to be
    refutable by a witness that discriminates, so it was landed as
    reject-branch-guard-ignores-dim above rather than merely reported.
  * SPEC-TOO-STRONG PROBE. Four NEW correct reshapes were built: de Morgan on the
    branch guard, the reduction branch's assignments fused, the filter predicates
    respelled via ``== true``/``== false``, and ``== 1`` weakened to ``<= 1``
    (equivalent under the enclosing non-empty guard). The first three VERIFY
    under the frozen proof body unchanged. The fourth needs the proof retuned —
    the frozen ``simp_all`` leaves a residual ``¬(… .length = 1)`` goal, and
    appending ``<;> grind`` closes it (exit 0). So the spec accepts it too and
    there is no soundness hole; the frozen TACTIC is merely shape-tuned, which is
    the documented reason reject cases carry witnesses at all.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6992"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. `_IMPL` is the entire text strictly between `-- impl-start`
# and `-- impl-end`; `_PROOF` is the whole `prove_correct` block. Both are
# unique in `_BASE` and lie WHOLLY inside a region the spec view elides, so
# every `_swap` below edits only that region and the manifest breaks loudly (an
# AssertionError at import) if the frozen solution ever drifts.
# ---------------------------------------------------------------------------
_IMPL = """    let mut dropVars : List String := []
    let mut newVars : List String := []
    let mut newIdx : List String := []
    if isMulti then
      let keepLevels := levels.filter (fun k => !R.contains k)
      if (!R.contains dim) && !keepLevels.isEmpty then
        let resetLevels := levels.filter (fun k => R.contains k)
        if keepLevels.length == 1 then
          dropVars := keepLevels
          newVars := [dim]
          newIdx := [dim]
          if dropF then
            dropVars := dropVars ++ resetLevels
          else
            newVars := newVars ++ resetLevels
        else
          newVars := keepLevels
          newIdx := keepLevels ++ [dim]
          if dropF then
            dropVars := resetLevels
          else
            newVars := newVars ++ resetLevels
      else
        dropVars := [dim]
        if dropF then
          dropVars := dropVars ++ levels
        else
          newVars := levels
    else
      if dropF then
        dropVars := [dim]
      else
        newVars := [dim]
    let variables2 := filterOut dropVars V ++ newVars
    let coord2 := filterOut dropVars C
    return { vars := variables2, coords := coord2, idxs := newIdx }"""
assert _BASE.count(_IMPL) == 1, "impl region drift"

_PROOF = ("prove_correct dropIndexNameSets by\n"
          "  loom_solve <;> simp_all [computeNameSets]")
assert _BASE.count(_PROOF) == 1, "proof region drift"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, body)


def _impl_reproved(body, proof):
    """Impl body replaced AND the proof retuned (the `prove_correct` header is
    preserved; only its tactic body changes)."""
    return _swap(_impl(body), _PROOF, proof)


def _sub(body, pairs):
    """Apply an ordered list of unique (old, new) substitutions to `body`."""
    for old, new in pairs:
        if body.count(old) != 1:
            raise AssertionError(f"impl sub not unique: {old[:60]!r}")
        body = body.replace(old, new, 1)
    return body


# ---------------------------------------------------------------------------
# The witness preamble. The spec is a `method` CONTRACT, so a witness reaches
# the post-image through Velvet's tester machinery: `dropIndexNameSetsTester
# <args> = false` says the extracted program's result VIOLATES the postcondition
# at that concrete input. There is no `require` clause on this method, so no
# witness input can be vacuously excluded by a false precondition. Checked in a
# file whose `prove_correct` block has been stripped so no tactic script can
# mask the verdict; both the frozen impl and every rival are branch-and-filter
# expressions over decidable literals, so both testers reduce under `decide`.
# ---------------------------------------------------------------------------
def _witness(call):
    return ("extract_program_for dropIndexNameSets\n"
            "prove_precondition_decidable_for dropIndexNameSets\n"
            "prove_postcondition_decidable_for dropIndexNameSets\n"
            "derive_tester_for dropIndexNameSets\n\n"
            f"example : {call} = false := by\n  decide\n")


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # ================= POSITIVE CONTROLS (soundness) ========================

    # -- pos-model-direct: the relation, computed without the accumulators -----
    # The frozen impl threads THREE mutable accumulators through a nested-if
    # ladder and then applies the two removals. This variant discards the whole
    # imperative shape and returns the pure model directly. Observationally
    # identical on every input (the `ensures` IS this equality), a completely
    # different executable shape. The frozen `loom_solve <;> simp_all` still
    # closes the byte-identical obligation. Must VERIFY, else the postcondition
    # over-constrains the COMPUTATION rather than the relation => SPEC-TOO-STRONG.
    # BUILT out-of-band: exit 0.
    {
        "id": "pos-model-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    return computeNameSets isMulti dim levels R V C dropF"),
        "rationale": "a structurally DIFFERENT but CORRECT implementation: the "
                     "three mutable accumulators and the whole nested-if ladder "
                     "are eliminated and the pure name-set model is returned "
                     "directly. Extensionally identical on the entire domain, so "
                     "the single `ensures` equality holds and the frozen proof "
                     "still discharges it. If this were rejected the "
                     "postcondition would be pinned to the gold body's "
                     "particular accumulator SHAPE rather than to the "
                     "input->output relation => SPEC-TOO-STRONG.",
    },

    # -- pos-guard-inverted: every branch polarity flipped, assembly reordered --
    # Invert all four `if dropF then A else B` into `if !dropF then B else A`
    # (so the retain path is now the THEN branch everywhere) and bind the
    # coordinate collection BEFORE the variable collection. Same set algebra,
    # different control flow and different statement order. This is the port of
    # nagini's `pos-teardown-combined` / `pos-promote-reorder` pair: a correct
    # restructuring that must still verify. Must VERIFY.
    # BUILT out-of-band: exit 0 (frozen proof body unchanged, obligation closed).
    {
        "id": "pos-guard-inverted",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_sub(_IMPL, [
            ("          if dropF then\n"
             "            dropVars := dropVars ++ resetLevels\n"
             "          else\n"
             "            newVars := newVars ++ resetLevels\n",
             "          if !dropF then\n"
             "            newVars := newVars ++ resetLevels\n"
             "          else\n"
             "            dropVars := dropVars ++ resetLevels\n"),
            ("          if dropF then\n"
             "            dropVars := resetLevels\n"
             "          else\n"
             "            newVars := newVars ++ resetLevels\n",
             "          if !dropF then\n"
             "            newVars := newVars ++ resetLevels\n"
             "          else\n"
             "            dropVars := resetLevels\n"),
            ("        if dropF then\n"
             "          dropVars := dropVars ++ levels\n"
             "        else\n"
             "          newVars := levels\n",
             "        if !dropF then\n"
             "          newVars := levels\n"
             "        else\n"
             "          dropVars := dropVars ++ levels\n"),
            ("      if dropF then\n"
             "        dropVars := [dim]\n"
             "      else\n"
             "        newVars := [dim]\n",
             "      if !dropF then\n"
             "        newVars := [dim]\n"
             "      else\n"
             "        dropVars := [dim]\n"),
            ("    let variables2 := filterOut dropVars V ++ newVars\n"
             "    let coord2 := filterOut dropVars C\n",
             "    let coord2 := filterOut dropVars C\n"
             "    let variables2 := filterOut dropVars V ++ newVars\n"),
        ])),
        "rationale": "a CORRECT restructuring: all four channel guards are "
                     "inverted so the retain path becomes the THEN branch "
                     "everywhere, and the coordinate collection is bound before "
                     "the variable collection. Identical values by every branch, "
                     "different control flow and statement order, so the single "
                     "`ensures` equality still holds on the whole domain and the "
                     "frozen proof body still closes it. This is the port of the "
                     "sibling's reorder/combined positive controls. If rejected "
                     "=> SPEC-TOO-STRONG (the spec would be pinned to the gold "
                     "branch polarity rather than to the relation).",
    },

    # ================= ADMISSIBILITY ========================================

    # -- admiss-f2p-grid: the relation is satisfiable AND non-degenerate -------
    # The nagini sibling's `admiss-teardown` Asserts its `Requires` inside the
    # body to show the PRECONDITION admits a normal input. The frozen method here
    # has NO `require` clause (the obligation is unconditional over all seven
    # binders), so that mechanic has no counterpart. The surviving admissibility
    # question is whether the pinned relation is SATISFIABLE and NON-DEGENERATE at
    # a realistic input — a relation contradictory at every input would make the
    # obligation unprovable, the same failure one level up. So: keep the gold impl
    # VERBATIM and add one in-region `assert` naming the exact expected name-sets
    # at an F2P-shaped input (a two-level index on `foo`/`bar` over dimension `x`,
    # request `foo`, retain — the row that exercises the single-level reduction
    # AND the rename AND a surviving index), discharged by `decide`. The assert is
    # LIVE: authoring confirmed that substituting a false expected value leaves an
    # unsolved goal and the build fails.
    # BUILT out-of-band: exit 0.
    {
        "id": "admiss-f2p-grid",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (computeNameSets true \"x\" [\"foo\", \"bar\"] [\"foo\"] "
            "[\"x\", \"foo\", \"bar\", \"d\"]\n"
            "         [\"x\", \"foo\", \"bar\"] false\n"
            "        = { vars := [\"x\", \"foo\", \"d\", \"x\", \"foo\"], "
            "coords := [\"x\", \"foo\"],\n"
            "            idxs := [\"x\"] }))\n" + _IMPL,
            _PROOF + "\n  all_goals decide"),
        "rationale": "the pinned relation must be SATISFIABLE and NON-DEGENERATE "
                     "at a realistic release input, not vacuous: the gold impl is "
                     "kept verbatim (so the method's own `ensures` still "
                     "discharges) and an in-region assert names the exact three "
                     "recomputed name-sets at a shape drawn from the failing "
                     "grid — a two-level index over dimension `x` with one level "
                     "requested and the de-indexed coordinate RETAINED. That "
                     "input exercises the single-kept-level reduction, the rename "
                     "to the dimension name, the retained-coordinate channel, and "
                     "a surviving index simultaneously, and the asserted result "
                     "is neither empty nor a copy of the inputs. The frozen "
                     "method has no `require` clause, so the sibling's "
                     "Assert(Requires) mechanic has no counterpart; this is the "
                     "surviving admissibility content. If the assert could not "
                     "discharge, the relation would be unsatisfiable in the "
                     "modeled domain => PRECOND-TOO-STRONG.",
    },

    # ================= UNIQUENESS / REJECT ==================================

    # -- reject-coords-never-shrink: THE discriminating sub-behaviour (S1) ------
    # Rebuild the coordinate collection from the ORIGINAL one, only ever GROWN by
    # the fresh names, while the variable collection IS shrunk. This is the
    # base-commit shape the bundle's own Solution_prepatch.lean carries, and the
    # nagini sibling's `reject-prepatch-coordnames` verbatim in argument. A
    # released coordinate then leaves the stored variables but LINGERS among the
    # coordinate names, so the two collections drift and the `coords ⊆ vars`
    # invariant breaks.
    # WITNESS at the PLAIN single-index shape (isMulti=false, levels=[], R=["x"],
    # V=["x","d"], C=["x"], dropF=true): the relation demands the coordinate
    # collection become [] while the rival returns ["x"].
    # BUILT out-of-band: rival exit 0, gold exit 1 (`decide` proves it FALSE).
    {
        "id": "reject-coords-never-shrink",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_sub(_IMPL, [
            ("    let coord2 := filterOut dropVars C\n",
             "    let coord2 := C ++ newVars\n"),
        ])),
        "witness": _witness(
            'dropIndexNameSetsTester false "x" [] ["x"] ["x", "d"] ["x"] true'),
        "refinement": "the faithful real counterpart of this rival is the "
                      "BASE-COMMIT assembly: the coordinate collection is "
                      "recomputed as the original one unioned with the freshly "
                      "built names, so a released coordinate is never taken out "
                      "of it. That is precisely the reported defect — the "
                      "coordinate names then OUTNUMBER the stored variable names, "
                      "the derived count of non-coordinate variables goes "
                      "NEGATIVE, and the container raises the `ValueError: "
                      "__len__() should return >= 0` quoted in the issue on repr "
                      "and on the length of the data-variable view. The failing "
                      "suite pins exactly this: the drop=True arms of the "
                      "parametrized release grid assert each discarded name is "
                      "absent from the resulting container's variables, the "
                      "dimension-count check asserts the released dimension is "
                      "gone, and the grouping regression reaches the same site. "
                      "G-DIFF: Solution_prepatch.lean CONTAINS this revert (its "
                      "coordinate collection is likewise only ever grown) and "
                      "fails to verify — it is the base-commit assembly entire, "
                      "so it reverts the rename and the release channel as well "
                      "and is a strict superset of this one-clause rival rather "
                      "than the same file. So a verifying rival here would be a "
                      "genuine verify-does-not-imply-resolve break.",
        "rationale": "refuted by the `ensures` equality via sub-behaviour S1 "
                     "(`coords := filterOut dv C`) at the plain single-index "
                     "binder point isMulti=false / levels=[] / R=[\"x\"] / "
                     "dropF=true — the shape the issue's own example reduces to. "
                     "With the flag set the drop-set is [\"x\"], so the relation "
                     "demands the coordinate collection [\"x\"] become [], while "
                     "the rival returns it grown instead of shrunk. The rival "
                     "leaves S2 (the variable shrink) and S5 (index release) "
                     "intact, so it is refutable ONLY because the coordinate "
                     "collection is pinned in the same equality; that is the "
                     "load-bearing content. The witness states the tester false "
                     "at exactly that input and `decide` closes it; on the frozen "
                     "solution `decide` proves the same proposition FALSE, so it "
                     "is a seen discriminator.",
    },

    # -- reject-vars-never-shrink: the S2 mirror of the pre-patch drift --------
    # Shrink the coordinate collection but NOT the variable collection. A
    # discarded name keeps its stored array while ceasing to be a coordinate — the
    # same two-collection drift as the base-commit bug, in the opposite direction.
    # No nagini counterpart: available here because the two shrinks share one
    # drop-set yet are pinned by the same equality independently, so each is
    # refutable while the other holds.
    # WITNESS at (isMulti=true, dim="x", levels=["foo","bar"], R=["foo"],
    # V=["x","foo","bar","d"], C=["x","foo","bar"], dropF=true): the relation
    # demands the discarded level leave the stored names; the rival keeps it.
    # BUILT out-of-band: rival exit 0, gold exit 1.
    {
        "id": "reject-vars-never-shrink",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_sub(_IMPL, [
            ("    let variables2 := filterOut dropVars V ++ newVars\n",
             "    let variables2 := V ++ newVars\n"),
        ])),
        "witness": _witness(
            'dropIndexNameSetsTester true "x" ["foo", "bar"] ["foo"] '
            '["x", "foo", "bar", "d"] ["x", "foo", "bar"] true'),
        "refinement": "the faithful real counterpart takes the discarded name out "
                      "of the coordinate collection but never deletes its stored "
                      "array. The array then lingers as an ordinary "
                      "(non-coordinate) stored variable, so a discarding release "
                      "silently PROMOTES the released coordinate into a data "
                      "variable instead of removing it — and it inflates the very "
                      "data-variable count the issue is about, in the opposite "
                      "direction. The failing suite asserts the discarded name is "
                      "absent from the container ALTOGETHER after a discarding "
                      "release: every drop=True arm of the parametrized grid "
                      "checks the resulting variable collection for each dropped "
                      "name, and the dimension-count check asserts the container "
                      "has no dimensions left. Both fail on it, so the faithful "
                      "counterpart does NOT resolve.",
        "rationale": "refuted by the `ensures` equality via sub-behaviour S2 "
                     "(`vars := filterOut dv V ++ nv`) at the binder point "
                     "isMulti=true / dropF=true with a LEVEL requested, and with "
                     "the stored names strictly exceeding the coordinate names "
                     "(an extra name `d` that must survive either way). The "
                     "relation demands the discarded level leave the stored "
                     "collection; the rival returns it unchanged. S1 still holds "
                     "for this rival, so it is refutable ONLY because both "
                     "shrinks are pinned even though they share one derived "
                     "drop-set — the mirror of reject-coords-never-shrink, and "
                     "the reason both directions need their own case. `decide` "
                     "closes the witness against the rival; the frozen solution "
                     "reports the same proposition FALSE.",
    },

    # -- reject-retain-as-discard: the retained coordinate treated as discarded -
    # Route every de-indexed name to the drop-set UNCONDITIONALLY, ignoring the
    # flag. A RETAINED coordinate then vanishes from both collections although it
    # was supposed to survive as an ordinary stored variable. This is nagini's
    # `reject-convert-as-drop` on this carrier: there the retained channel is a
    # separate input subtracted where it must not be; here the flag IS the channel
    # selector.
    # NEAR-MISS NOTE: this rival agrees with gold across the WHOLE dropF=true half
    # of the domain, so its witness must sit on the dropF=false side — which is
    # why it shares no input point with any other case.
    # WITNESS at (isMulti=true, dim="x", levels=["foo","bar"], R=["x"],
    # V=["x","foo","bar","d"], C=["x","foo","bar"], dropF=false).
    # BUILT out-of-band: rival exit 0, gold exit 1.
    {
        "id": "reject-retain-as-discard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_sub(_IMPL, [
            ("          if dropF then\n"
             "            dropVars := dropVars ++ resetLevels\n"
             "          else\n"
             "            newVars := newVars ++ resetLevels\n",
             "          dropVars := dropVars ++ resetLevels\n"),
            ("          if dropF then\n"
             "            dropVars := resetLevels\n"
             "          else\n"
             "            newVars := newVars ++ resetLevels\n",
             "          dropVars := resetLevels\n"),
            ("        if dropF then\n"
             "          dropVars := dropVars ++ levels\n"
             "        else\n"
             "          newVars := levels\n",
             "        dropVars := dropVars ++ levels\n"),
            ("      if dropF then\n"
             "        dropVars := [dim]\n"
             "      else\n"
             "        newVars := [dim]\n",
             "      dropVars := [dim]\n"),
        ])),
        "witness": _witness(
            'dropIndexNameSetsTester true "x" ["foo", "bar"] ["x"] '
            '["x", "foo", "bar", "d"] ["x", "foo", "bar"] false'),
        "refinement": "the faithful real counterpart routes the RETAINED "
                      "(non-discarding) names through the discard channel instead "
                      "of re-storing them as ordinary variables, which DELETES "
                      "the retained coordinate's array. The failing suite's "
                      "non-discarding arms assert the released name's variable "
                      "SURVIVES in its plain, non-index-backed form — the "
                      "drop=False arms of the parametrized grid read that "
                      "variable back out of the result and compare it against the "
                      "prior one converted to its plain form. Deleting it makes "
                      "the name missing entirely, so those arms fail with a "
                      "lookup error rather than a comparison mismatch. The "
                      "faithful counterpart does NOT resolve.",
        "rationale": "refuted by the `ensures` equality via sub-behaviour S3 (the "
                     "flag routes each de-indexed name to the drop-set OR to the "
                     "fresh-variable set) at the binder point dropF=false with "
                     "the DIMENSION itself requested, so the whole index goes and "
                     "its levels must be retained. The relation demands those "
                     "levels stay among the stored names and leave the coordinate "
                     "names; the rival discards them from both. This is a "
                     "NEAR-MISS that agrees with gold across the entire "
                     "dropF=true half of the domain, so the witness is placed on "
                     "the dropF=false side where it actually diverges — it shares "
                     "no input point with any other case. `decide` closes it "
                     "against the rival; the frozen solution reports it FALSE.",
    },

    # -- reject-no-rename: the reduced single level keeps its own name (S4) -----
    # In the reduction-to-one-kept-level branch, key the surviving index on the
    # OLD kept-level name and emit no fresh dimension coordinate: skip the rename
    # entirely. This is the port of nagini's `reject-promote-no-readd` argument —
    # that rival attacks the sibling function's re-add/convert step, which this
    # bundle does not model; the same patch's structural rule surfaces here as the
    # rename of a reduced single level, so the argument is carried onto the
    # behaviour this carrier DOES state.
    # WITNESS at (isMulti=true, dim="z", levels=["p","q"], R=["p"],
    # V=["z","p","q"], C=["z","p","q"], dropF=false).
    # BUILT out-of-band: rival exit 0, gold exit 1.
    {
        "id": "reject-no-rename",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_sub(_IMPL, [
            ("        if keepLevels.length == 1 then\n"
             "          dropVars := keepLevels\n"
             "          newVars := [dim]\n"
             "          newIdx := [dim]\n"
             "          if dropF then\n"
             "            dropVars := dropVars ++ resetLevels\n"
             "          else\n"
             "            newVars := newVars ++ resetLevels\n",
             "        if keepLevels.length == 1 then\n"
             "          newIdx := keepLevels\n"
             "          if dropF then\n"
             "            dropVars := resetLevels\n"
             "          else\n"
             "            newVars := resetLevels\n"),
        ])),
        "witness": _witness(
            'dropIndexNameSetsTester true "z" ["p", "q"] ["p"] '
            '["z", "p", "q"] ["z", "p", "q"] false'),
        "refinement": "the faithful real counterpart rebuilds the reduced index "
                      "on the surviving level WITHOUT renaming it to the "
                      "dimension: the lone remaining level keeps its own name as "
                      "the index key and no fresh dimension coordinate is "
                      "produced, so the old level name is never retired. The "
                      "failing suite pins the rename directly — the parametrized "
                      "grid's rename column asserts that after reducing a "
                      "two-level index by one level the prior kept-level variable "
                      "is readable under the DIMENSION name in the result, and "
                      "the container-level release test asserts the surviving "
                      "index is keyed on the dimension and is a plain "
                      "single-level index rather than the old level name. Both "
                      "arms fail on it, so the faithful counterpart does NOT "
                      "resolve.",
        "rationale": "refuted by the `ensures` equality via sub-behaviour S4 at "
                     "the binder point isMulti=true / dropF=false with exactly "
                     "one level requested out of two, which is what selects the "
                     "reduction branch. The relation demands the fresh coordinate "
                     "be the DIMENSION name, the old kept-level name be retired "
                     "from both collections, and the surviving index be keyed on "
                     "the dimension; the rival keeps the level name in all three "
                     "places. Note the witness moves `dim` off the value every "
                     "other witness uses, so this sub-behaviour is not probed at "
                     "a single dimension literal. `decide` closes it against the "
                     "rival; the frozen solution reports it FALSE.",
    },

    # -- reject-branch-guard-ignores-dim: the BRANCH SELECTOR itself (S7) ------
    # Drop the `(!R.contains dim) &&` conjunct from the branch guard, so the
    # rebuild-on-kept-levels branch is entered on the strength of "some level
    # survives" ALONE. When the DIMENSION is the requested name, the whole index
    # must go and the dimension variable must be released; this rival instead
    # rebuilds an index on the untouched levels and never releases the dimension.
    # Added by audit: every other rival in this battery edits an ASSIGNMENT
    # inside a branch and so probes the branches' CONTENTS while taking the
    # branch SELECTOR for granted. The selector is its own load-bearing content
    # here (it is what routes "the dimension itself was requested" to the
    # whole-index-goes arm), and a rival that mis-selects the branch was
    # previously unattacked.
    # WITNESS at (isMulti=true, dim="x", levels=["foo","bar"], R=["x"],
    # V=["x","foo","bar","d"], C=["x","foo","bar"], dropF=true) — the dimension
    # requested WITH discarding, so gold releases dim and both levels while the
    # rival releases nothing and keeps a live index.
    # BUILT by the audit: rival exit 0, gold exit 1 (`decide` proves it FALSE);
    # the flipped-claim forgery inverts both (rival 1, gold 0).
    {
        "id": "reject-branch-guard-ignores-dim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_sub(_IMPL, [
            ("      if (!R.contains dim) && !keepLevels.isEmpty then\n",
             "      if !keepLevels.isEmpty then\n"),
        ])),
        "witness": _witness(
            'dropIndexNameSetsTester true "x" ["foo", "bar"] ["x"] '
            '["x", "foo", "bar", "d"] ["x", "foo", "bar"] true'),
        "refinement": "the faithful real counterpart decides whether the index "
                      "survives by looking ONLY at whether some level was left "
                      "unrequested, ignoring whether the request named the "
                      "DIMENSION itself. Asking to release a whole multi-level "
                      "index by its dimension name then rebuilds an index on the "
                      "levels instead of releasing it: the dimension keeps its "
                      "stored array and its coordinate name, and the index stays "
                      "live. The failing suite pins this arm directly — the "
                      "release-by-dimension rows of the parametrized grid assert "
                      "the dimension name is gone from the resulting container "
                      "and that its index mapping is empty, and the "
                      "dimension-count check asserts no dimension survives a "
                      "discarding release. Both fail on it, so the faithful "
                      "counterpart does NOT resolve.",
        "rationale": "refuted by the `ensures` equality via the BRANCH SELECTOR "
                     "(the `(!R.contains dim) &&` conjunct of the rebuild "
                     "guard) at the binder point isMulti=true / dropF=true with "
                     "the DIMENSION requested and a level left unrequested — the "
                     "one request shape that makes the two guards disagree. The "
                     "relation demands the whole-index-goes arm (dimension and "
                     "both levels released from both collections, index "
                     "collection empty); the rival takes the rebuild arm and "
                     "releases nothing. Every other rival here edits an "
                     "assignment INSIDE a branch, so this is the only case that "
                     "attacks which branch is chosen rather than what it "
                     "computes; the rival agrees with gold on the whole "
                     "dim-not-requested half of the domain, which is why the "
                     "witness sits where the dimension IS requested. `decide` "
                     "closes it against the rival; the frozen solution reports "
                     "the same proposition FALSE, and the flipped-claim forgery "
                     "inverts both exit codes.",
    },

    # -- reject-index-stays-live: the released index survives (S5) -------------
    # In the whole-index-goes branch, emit the dimension as a SURVIVING index key.
    # The released index then stays live even though its coordinates are gone.
    # This is nagini's `reject-teardown-overkeep-indexes` on this carrier.
    # WITNESS at (isMulti=true, dim="x", levels=["foo","bar"], R=["foo","x"],
    # V=["x","foo","bar","d"], C=["x","foo","bar"], dropF=true) — the grid row
    # that requests a level AND the dimension together with discarding.
    # BUILT out-of-band: rival exit 0, gold exit 1.
    {
        "id": "reject-index-stays-live",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_sub(_IMPL, [
            ("      else\n"
             "        dropVars := [dim]\n"
             "        if dropF then\n",
             "      else\n"
             "        dropVars := [dim]\n"
             "        newIdx := [dim]\n"
             "        if dropF then\n"),
        ])),
        "witness": _witness(
            'dropIndexNameSetsTester true "x" ["foo", "bar"] ["foo", "x"] '
            '["x", "foo", "bar", "d"] ["x", "foo", "bar"] true'),
        "refinement": "the faithful real counterpart removes the released names "
                      "from the variable and coordinate collections but leaves "
                      "the index entry itself in the container's index mapping — "
                      "a stale index keyed on a dimension whose coordinate no "
                      "longer exists, which is the dangling index-backed state "
                      "behind the issue's broken-repr symptom class. The failing "
                      "suite checks the index mapping directly: the "
                      "container-level release tests assert the mapping is EMPTY "
                      "after releasing the index, and the dimension-count check "
                      "asserts no dimension survives a discarding release. A "
                      "stale entry fails those assertions, so the faithful "
                      "counterpart does NOT resolve.",
        "rationale": "refuted by the `ensures` equality via sub-behaviour S5 (the "
                     "whole-index-goes branch emits NO surviving index) at the "
                     "binder point isMulti=true / dropF=true with a TWO-name "
                     "request naming both a level and the dimension itself — the "
                     "request shape that forces that branch. The relation demands "
                     "the index collection be empty; the rival returns the "
                     "dimension still keyed. Sub-behaviours S1 and S2 hold for "
                     "this rival (both collections shrink correctly), so it is "
                     "refutable only because the index collection is pinned too. "
                     "`decide` closes it against the rival; the frozen solution "
                     "reports it FALSE.",
    },

    # -- reject-identity: PARTIAL-DOMAIN — release nothing ---------------------
    # Return the two input collections untouched with no surviving index. Correct
    # ONLY on the degenerate sub-domain where nothing is dropped and nothing is
    # added; wrong on every input that actually releases a name. This is nagini's
    # `reject-identity-teardown`.
    # WITNESS at (isMulti=true, dim="x", levels=["foo","bar"], R=["foo","bar"],
    # V=["x","foo","bar","d"], C=["x","foo","bar"], dropF=true) — the grid row
    # that requests BOTH levels with discarding, so all of S1/S2/S5 demand a
    # removal and the rival makes none.
    # BUILT out-of-band: rival exit 0, gold exit 1.
    {
        "id": "reject-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return { vars := V, coords := C, idxs := [] }"),
        "witness": _witness(
            'dropIndexNameSetsTester true "x" ["foo", "bar"] ["foo", "bar"] '
            '["x", "foo", "bar", "d"] ["x", "foo", "bar"] true'),
        "refinement": "the faithful real counterpart is a no-op release: it "
                      "computes the released names and then rebuilds the "
                      "container from the ORIGINAL collections, so nothing is "
                      "ever removed and no coordinate is ever converted. "
                      "Releasing an index would leave that index's coordinates in "
                      "place, which is the very thing the operation exists to "
                      "undo. Every arm of the failing suite checks at least one "
                      "removal: the container-level release tests compare against "
                      "an expected container from which the released names are "
                      "absent, the dimension-count check asserts no dimension "
                      "survives, and each arm of the parametrized grid asserts "
                      "its dropped names are gone or its retained names were "
                      "converted. All fail, so the faithful counterpart does NOT "
                      "resolve.",
        "rationale": "refuted by the `ensures` equality via S6, and via S1, S2 "
                     "and S5 simultaneously, at the binder point isMulti=true / "
                     "dropF=true with BOTH levels requested — the request shape "
                     "that leaves no level kept, so the whole index goes and the "
                     "dimension plus both levels must be discarded from both "
                     "collections. The relation demands three removals and an "
                     "empty index collection; the rival makes none. It is correct "
                     "only on the degenerate no-op sub-domain, which is the "
                     "partial-domain shape the sibling's identity rival attacks. "
                     "`decide` closes the witness against the rival; the frozen "
                     "solution reports it FALSE.",
    },
]
