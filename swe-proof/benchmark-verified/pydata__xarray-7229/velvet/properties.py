"""properties.py — G-PBT falsification battery for pydata__xarray-7229 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both elided from the consumer spec view, so ``markers.same_spec`` holds and the
``prove_correct rebuildAttrs`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it ELABORATES against the rival and FAILS against a
subject known to satisfy the spec). The frozen solution cannot be that subject
here — see WITNESS MECHANICS below — so each reject case names an explicit
``witness_reference``.

DEFENDED SURFACE (one contracted method over the binders promote, xName,
xGAttrs, xVars, xCoords, resVars, resCoords):

  rebuildAttrs (promote) (xName) (xGAttrs) (xVars) (xCoords) (resVars) (resCoords)
      return (out : Obj)
    ensures out.gattrs = rebuiltGlobal promote xGAttrs                       -- C-glob
    ensures out.vars.size   = resVars.size                                   -- C-vsz
    ensures out.coords.size = resCoords.size                                 -- C-csz
    ensures ∀ i, i < resVars.size   → out.vars[i]!   = rebuiltVar  … (resVars[i]!)   -- C-var
    ensures ∀ i, i < resCoords.size → out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!) -- C-crd

``rebuiltGlobal``/``rebuiltVar``/``rebuiltCoord``/``lookupAttrs`` are TRANSPARENT,
fully-unfolded ``def``s over the inputs (the ``axioms`` region is EMPTY — there
is no opaque answer key to echo, directive 8). The DISCRIMINATING content the
port defends: (a) coordinate levels ALWAYS take their by-name source coordinate
metadata (``rebuiltCoord`` / ``lookupAttrs``), independent of the global token —
this is the reported regression, where coordinate metadata was clobbered by the
single global token; (b) under promotion the global metadata is emptied while the
source-named variable receives the source's global metadata; (c) names preserved
and level counts unchanged. Each per-position ``ensures`` pins EVERY index
independently, which makes the partial-domain rivals refutable at a concrete
point.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this MANDATORY because
    its source lists are held at a fractional heap permission (``Acc(.,1/2)``) an
    impl can illegally overwrite, so a rival that writes ``x_coord_attrs[0]`` /
    appends to ``x_var_attrs`` is rejected for INSUFFICIENT PERMISSION. Lean and
    Velvet are referentially transparent: ``xVars``/``xCoords`` are immutable
    ``Array Lvl`` values, no parameter is declared ``mut``, there is no heap and
    no aliasing — so there is no read-only input to mutate and no substitute
    probe to build. Reported N/A in the footer; NOT fabricated. Re-derived by
    the audit rather than taken on trust: ``xCoords := xCoords.set! 0 default``
    and ``xVars := xVars.push default`` inside the impl region both fail to
    PARSE (``` `xCoords` cannot be mutated, only variables declared using `let
    mut` can be mutated ```), so the mutation cannot even be written, let alone
    rejected by a frame obligation. The nearest expressible analogue — copy the
    source into a ``let mut`` local, overwrite it, and compute correctly from the
    original — VERIFIES (exit 0), which is the right answer on a referentially
    transparent carrier: clobbering a private copy is not observable. There is no
    frame clause to attack.
  * DIVERGENCE / NON-TERMINATION: the nagini sibling ships none here, so there is
    nothing to port, but "VACUOUS on lean-family carriers" is withdrawn and so is
    "a total functional rebuild": the frozen impl of ``rebuildAttrs`` is TWO
    ``while`` loops (see WITNESS MECHANICS below, which says so), and a rival may
    also splice a fresh diverging loop. The class is closed by the verifier. This
    bundle sets ``loom.semantics.termination "total"``, under which a postcondition
    is claimed of ALL runs, not only terminating ones, so each loop owes a
    decreasing measure AND its descent, which is why the frozen body carries
    ``decreasing resVars.size - i`` and ``decreasing resCoords.size - k``. The
    option cannot drift from the file's ``open TotalCorrectness DemonicChoice``,
    because the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with each proof
    reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` whose body is
    ``z := z + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-images are transparent ``def``s over
    the method inputs (empty ``axioms`` region), so the cheapest correct impl
    just evaluates them — covered honestly by the positive controls, and no wrong
    echo verifies (else a positive would be a reject).
  * PARTIAL-DOMAIN / VALUE / REGIME — the main class, ported below.

WITNESS MECHANICS. The frozen impl of ``rebuildAttrs`` is two ``while`` loops.
Under ``loom.semantics.choice "demonic"`` those loops elaborate through
``Classical.choice``, which the kernel cannot unfold, so a ``decide`` against the
FROZEN extracted tester is STUCK — it reports ``did not reduce to `isTrue` or
`isFalse` `` for every claim regardless of truth. The frozen solution therefore
CANNOT serve as the second subject of the discrimination check: its exit code
carries no information.

  Measured (audit, 2026-08-12). For all seven reject cases the witness build
  against ``Solution.lean`` exits 1 with ``did not reduce to `isTrue` or
  `isFalse` ``, NOT with a refutation. Directly demonstrated to be
  non-discriminating: a FORGED witness asserting ``rebuildAttrsTester false 0 2
  #[] #[⟨5,2⟩] #[] #[⟨5,0⟩] = true`` — i.e. that ``coord-broadcast-global``
  SATISFIES the spec at an agreement point, the exact OPPOSITE of a refutation —
  elaborates against that rival (exit 0) and "fails" against the frozen solution
  (exit 1, same stuck reduction). Under a gold-side check it would be recorded as
  a refutation.

So every reject case below carries an explicit ``witness_reference``: ``_POS_MAP``,
the loop-free direct-map impl that is this battery's own first positive control.
It is loop-free, so its extracted program REDUCES and ``decide`` returns a real
verdict; and it VERIFIES against the frozen spec (checked by the gate via
``_reference_ok``, and independently re-built during the audit: exit 0). An impl
the verifier accepts cannot violate its own spec, so a genuine refutation must
still fail there — and it fails SEMANTICALLY: each of the seven builds reports
``Tactic `decide` proved that the proposition … is false``, a decided refutation
of the concrete claim rather than a stuck term, an unknown name, or a type error.
The forgery above is correctly caught on this subject (it elaborates, exit 0 =>
``witness-vacuous``).

Every reject rival is written LOOP-FREE (``Array.map`` / ``Array.mapIdx`` /
``.push`` / ``.pop``) so that half 1 also decides rather than getting stuck. Each
witness reaches the method contract through Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``); it is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. ``Nat``/``Bool``/``Array Lvl`` literals are fully concrete (``Lvl``
derives ``DecidableEq``), so ``decide`` settles the whole equality — no opaque
term, no conditioning, no head binders (hence no consistency obligation).

BINDER / CLAUSE COVERAGE. Every one of the five ``ensures`` clauses is attacked
by ≥1 rival and defended by the positives:
  C-glob → promo-top-leak;  C-vsz → var-drop-size;  C-csz → coord-extra-size;
  C-var  → var-first-slot, promo-matching-slot-drop;
  C-crd  → coord-broadcast, coord-first-slot.
The seven reject witnesses probe SEVEN distinct input points, moving every input
binder that is load-bearing: ``promote`` ∈ {true, false}; ``xGAttrs`` over
{1, 3, 8}; ``xName`` = 7 where the promotion match is exercised; ``xVars`` /
``xCoords`` / ``resVars`` / ``resCoords`` carry both empty and 1–2-element arrays
across the set. The two near-miss first-slot rivals are refuted at 2-element
inputs (wrong only at index 0, correct at index 1), so they claim exactly the
index-0 sub-domain they attack and do not share a point with the whole-domain
broadcast / size rivals.

AUDIT PROBES (2026-08-12), recorded so the next reader need not re-spend them.
Eight NEW impls the battery does not contain were built against the frozen spec.
  SPEC-TOO-WEAK direction — all five REJECTED (no hole found): the by-name
  selection falling back to the global token when the source has no equally-named
  level; by-name selection taking the LAST rather than the FIRST equally-named
  level (a duplicate-name sub-domain no shipped rival reaches); under promotion
  re-deriving a NON-source-named variable by name instead of leaving it as the
  combination produced it (the complement of promo-matching-slot-drop); the
  coordinate level's own NAME overwritten while its metadata stays correct; and
  coordinate metadata drawn from the source VARIABLE levels instead of the source
  COORDINATE levels.
  SPEC-TOO-STRONG direction — three correct reshapes, all provable, so no
  soundness hole: an ``Array.mapIdx`` re-index verifies under the FROZEN
  ``loom_solve`` (exit 0); a ``foldl``/``push`` accumulator and a fully INLINED
  variant that never calls ``rebuiltVar``/``rebuiltCoord``/``rebuiltGlobal`` at
  all each leave true residual goals under bare ``loom_solve`` but verify once the
  tactic body is retuned (``loom_solve`` then ``all_goals simp_all [rebuiltCoord,
  rebuiltVar, rebuiltGlobal]``, exit 0 both). That is a tactic-tuning cost, not
  spec over-fitting: the spec admits every faithful reshape tried.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the changed
behaviour is modelled deeply and its soundness against the real (patched) callee
is a G-CONF concern (mapping.md §3 — G-AX skips this bundle). The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-7229"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. `_IMPL` is the COMPLETE impl body (both `-- impl-*` markers
# retained inside it), lies wholly inside the single impl region, and is unique
# in Solution.lean (both facts asserted at load by _swap). `_PROOF` is the frozen
# tactic body (elided from the consumer spec view, so a case may retune it
# without touching the spec or dropping the obligation). Anchoring on whole
# regions keeps every surgery inside the elided text — the `method` header, the
# `ensures` clauses, and the `pure`/`structure` regions are never touched, so
# `same_spec` holds for every case.
# ---------------------------------------------------------------------------
_IMPL = (
    "    -- impl-start\n"
    "    -- variable levels: each named level takes the source's equally-named metadata\n"
    "    let mut outVars := resVars\n"
    "    let mut i := 0\n"
    "    while i < resVars.size\n"
    "      invariant i ≤ resVars.size\n"
    "      invariant outVars.size = resVars.size\n"
    "      invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)\n"
    "      done_with i = resVars.size\n"
    "      decreasing resVars.size - i\n"
    "    do\n"
    "      outVars[i] := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)\n"
    "      i := i + 1\n"
    "    -- coordinate levels: ALWAYS take the source's equally-named coordinate metadata\n"
    "    let mut outCoords := resCoords\n"
    "    let mut k := 0\n"
    "    while k < resCoords.size\n"
    "      invariant k ≤ resCoords.size\n"
    "      invariant outCoords.size = resCoords.size\n"
    "      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)\n"
    "      done_with k = resCoords.size\n"
    "      decreasing resCoords.size - k\n"
    "    do\n"
    "      outCoords[k] := rebuiltCoord xCoords (resCoords[k]!)\n"
    "      k := k + 1\n"
    "    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }\n"
    "    -- impl-end"
)
_PROOF = "prove_correct rebuildAttrs by\n  loom_solve"

for _s in (_IMPL, _PROOF):
    assert _BASE.count(_s) == 1, f"anchor drift / not unique: {_s[:40]!r}"


def _with_impl(body):
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _tester(call):
    """A refutation witness reaching the contract through Velvet's tester."""
    return ("extract_program_for rebuildAttrs\n"
            "prove_precondition_decidable_for rebuildAttrs\n"
            "prove_postcondition_decidable_for rebuildAttrs\n"
            "derive_tester_for rebuildAttrs\n\n"
            f"example : {call} = false := by\n  decide\n")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot verify, the spec is
# SPEC-TOO-STRONG. Both verified out-of-band with a real build.
# ===========================================================================

# Loop-free direct map: build each output level by mapping the modeled per-level
# function over the skeleton. Observationally identical to the accumulator loops
# on every input; the frozen `loom_solve` still closes.
_POS_MAP = _with_impl(
    "    let outVars := resVars.map (rebuiltVar promote xName xGAttrs xVars)\n"
    "    let outCoords := resCoords.map (rebuiltCoord xCoords)\n"
    "    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }")

# In-loop local-variable reshape: bind the rebuilt level into a fresh local and
# `.set!` it, keeping both backward-count loops and their invariants verbatim.
# The nagini positive control (hoist/reshape a local) transliterated to this
# carrier; the frozen proof still closes.
_POS_LOCAL = _with_impl(
    "    let mut outVars := resVars\n"
    "    let mut i := 0\n"
    "    while i < resVars.size\n"
    "      invariant i ≤ resVars.size\n"
    "      invariant outVars.size = resVars.size\n"
    "      invariant ∀ j, j < i → outVars[j]! = rebuiltVar promote xName xGAttrs xVars (resVars[j]!)\n"
    "      done_with i = resVars.size\n"
    "      decreasing resVars.size - i\n"
    "    do\n"
    "      let nv := rebuiltVar promote xName xGAttrs xVars (resVars[i]!)\n"
    "      outVars := outVars.set! i nv\n"
    "      i := i + 1\n"
    "    let mut outCoords := resCoords\n"
    "    let mut k := 0\n"
    "    while k < resCoords.size\n"
    "      invariant k ≤ resCoords.size\n"
    "      invariant outCoords.size = resCoords.size\n"
    "      invariant ∀ j, j < k → outCoords[j]! = rebuiltCoord xCoords (resCoords[j]!)\n"
    "      done_with k = resCoords.size\n"
    "      decreasing resCoords.size - k\n"
    "    do\n"
    "      let nc := rebuiltCoord xCoords (resCoords[k]!)\n"
    "      outCoords := outCoords.set! k nc\n"
    "      k := k + 1\n"
    "    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }")

# ===========================================================================
# ADMISSIBILITY (verify) — re-aimed from the nagini precondition-admission
# self-call. `rebuildAttrs` declares NO `require` clause (the pre-conditions
# region is empty), so no F2P-shaped input can be excluded and the sibling probe
# is vacuous. Re-aimed at the residual admissibility risk on a total domain: that
# the post-image is UNSATISFIABLE / DEGENERATE at the interesting point. An
# in-region assert pins the issue's worked shape — under promotion the global
# metadata empties (rebuiltGlobal true 0 = 0), a coordinate keeps its OWN
# by-name source metadata (rebuiltCoord picks 7, not the empty global), and the
# source-named variable receives the source global (rebuiltVar true 3 9 gives 9).
# The impl is kept verbatim so the method's own five obligations still discharge;
# an extra `decide` bullet discharges the assert. A false variant of the assert
# leaves an unsolved goal (verified out-of-band).
# ===========================================================================
_ADMISS = _swap(
    _swap(
        _BASE,
        "    -- impl-start\n    -- variable levels",
        "    -- impl-start\n"
        "    assert (with_name_prefix `assert\n"
        "      (rebuiltGlobal true 0 = 0 ∧ rebuiltCoord #[(⟨1,7⟩:Lvl)] (⟨1,0⟩:Lvl) = (⟨1,7⟩:Lvl)\n"
        "        ∧ rebuiltVar true 3 9 #[] (⟨3,0⟩:Lvl) = (⟨3,9⟩:Lvl)))\n"
        "    -- variable levels"),
    _PROOF,
    "prove_correct rebuildAttrs by\n  loom_solve\n  · decide")


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong loop-free impls sharing the frozen
# spec that MUST be rejected, each with a machine-checked refutation witness at a
# concrete input and the argument that its faithful real counterpart would NOT
# resolve the failing F2P test.
# ===========================================================================

# THE headline reported bug: each output coordinate takes the single GLOBAL
# metadata token instead of its OWN by-name source coordinate metadata.
_RIVAL_COORD_BROADCAST = _with_impl(
    "    let outVars := resVars.map (rebuiltVar promote xName xGAttrs xVars)\n"
    "    let outCoords := resCoords.map (fun c => (⟨c.name, xGAttrs⟩ : Lvl))\n"
    "    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }")

# Coord off-by-one: correct on every coordinate except index 0, left empty.
_RIVAL_COORD_FIRST = _with_impl(
    "    let outVars := resVars.map (rebuiltVar promote xName xGAttrs xVars)\n"
    "    let outCoords := resCoords.mapIdx (fun idx c => "
    "if idx = 0 then (⟨c.name, 0⟩ : Lvl) else rebuiltCoord xCoords c)\n"
    "    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }")

# Coord count wrong: append a spurious extra coordinate (C-csz).
_RIVAL_COORD_SIZE = _with_impl(
    "    let outVars := resVars.map (rebuiltVar promote xName xGAttrs xVars)\n"
    "    let outCoords := (resCoords.map (rebuiltCoord xCoords)).push default\n"
    "    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }")

# Var off-by-one (ordinary regime): correct on every data-var except index 0.
_RIVAL_VAR_FIRST = _with_impl(
    "    let outVars := resVars.mapIdx (fun idx v => "
    "if idx = 0 then (⟨v.name, 0⟩ : Lvl) else rebuiltVar promote xName xGAttrs xVars v)\n"
    "    let outCoords := resCoords.map (rebuiltCoord xCoords)\n"
    "    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }")

# Var count wrong: drop the last data-var (C-vsz).
_RIVAL_VAR_SIZE = _with_impl(
    "    let outVars := (resVars.map (rebuiltVar promote xName xGAttrs xVars)).pop\n"
    "    let outCoords := resCoords.map (rebuiltCoord xCoords)\n"
    "    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }")

# Promotion top-level leak: the global metadata is left as the source global
# token instead of being emptied under promotion (C-glob).
_RIVAL_PROMO_TOP = _with_impl(
    "    let outVars := resVars.map (rebuiltVar promote xName xGAttrs xVars)\n"
    "    let outCoords := resCoords.map (rebuiltCoord xCoords)\n"
    "    return { gattrs := xGAttrs, vars := outVars, coords := outCoords }")

# Promotion matching-slot drop: under promotion the source-named variable is
# written the empty mapping instead of the source global metadata (C-var).
_RIVAL_PROMO_SLOT = _with_impl(
    "    let outVars := resVars.map (fun v => if promote then "
    "(⟨v.name, if v.name = xName then 0 else v.attrs⟩ : Lvl) "
    "else rebuiltVar promote xName xGAttrs xVars v)\n"
    "    let outCoords := resCoords.map (rebuiltCoord xCoords)\n"
    "    return { gattrs := rebuiltGlobal promote xGAttrs, vars := outVars, coords := outCoords }")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-map-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MAP,
        "rationale": "a loop-free impl that builds each output level by mapping "
                     "the modeled per-level function (rebuiltVar / rebuiltCoord) "
                     "over the skeleton is observationally identical to the frozen "
                     "accumulator loops on every input, so all five ensures clauses "
                     "discharge; a correct reshape must verify (else the spec is "
                     "over-fit to the loop spelling => SPEC-TOO-STRONG). Proof: "
                     "frozen `loom_solve` retained.",
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCAL,
        "rationale": "binding each rebuilt level into a fresh local and `.set!`ing "
                     "it computes the same value as the frozen in-place update; the "
                     "two backward-count loops and their invariants are kept "
                     "verbatim, so every clause still holds and the frozen proof "
                     "closes. Transliterates the nagini local-reshape positive "
                     "control. Must verify.",
    },

    # ---- admissibility (must VERIFY; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-promotion-worked-example",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "issue's worked shape: under promotion the global metadata "
                     "empties (rebuiltGlobal true 0 = 0), a coordinate keeps its "
                     "OWN by-name source metadata rather than the global token "
                     "(rebuiltCoord picks 7), and the source-named variable "
                     "receives the source global (rebuiltVar true 3 9 = 9). The "
                     "in-region assert must discharge (else the modeled behaviour "
                     "is degenerate at exactly the interesting point => "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so all five "
                     "obligations discharge too. Nothing is assumed: no new "
                     "declaration, the obligation statement is unchanged, and the "
                     "assert is a live goal (a false variant leaves it unsolved).",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "coord-broadcast-global",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_COORD_BROADCAST,
        "refinement": "THE reported bug: every output coordinate's metadata is set "
                      "to the source's single global token instead of that "
                      "coordinate's OWN by-name source metadata. The failing test "
                      "uses a source whose coordinate metadata differs from its "
                      "global metadata; broadcasting the global token onto the "
                      "coordinate makes the identity comparison of the coordinate "
                      "level diverge, so the failing test still fails — it would "
                      "NOT resolve. This is exactly the pre-fix behaviour.",
        "rationale": "REJECT from C-crd (∀ i, out.coords[i]! = rebuiltCoord xCoords "
                     "(resCoords[i]!)): the global token is not provably equal to "
                     "the by-name source coordinate metadata, so the clause cannot "
                     "discharge. If it verified => SPEC-TOO-WEAK (admits the "
                     "coordinate-clobbering regression). Refuted at a source whose "
                     "coordinate metadata (2) differs from its global token (1).",
        # Gold cannot decide (frozen loops elaborate through Classical.choice,
        # so `decide` is STUCK there for any claim, true or false). Refute
        # against the loop-free direct-map positive instead: it VERIFIES
        # against the frozen spec and its extracted program REDUCES, so the
        # failure is a decided refutation rather than a stuck term.
        "witness_reference": _POS_MAP,
        "witness": _tester(
            "rebuildAttrsTester false 0 1 #[] #[(⟨5,2⟩:Lvl)] #[] #[(⟨5,0⟩:Lvl)]"),
    },
    {
        "id": "coord-first-slot-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_COORD_FIRST,
        "refinement": "correct on every coordinate except index 0, which is left "
                      "empty. A real patch skipping the first coordinate would "
                      "leave the leading coordinate's metadata empty instead of its "
                      "source value; the failing test asserts that coordinate, so "
                      "it would NOT resolve. A partial-domain near-miss of the "
                      "broadcast bug in the coordinate carrier.",
        "rationale": "REJECT from C-crd at index 0 (out.coords[0]! must equal "
                     "rebuiltCoord xCoords (resCoords[0]!), but the rival forces 0 "
                     "there). Refuted at a 2-coordinate input where the rival is "
                     "WRONG at index 0 and CORRECT at index 1, so it claims exactly "
                     "the index-0 sub-domain and does not share a point with the "
                     "whole-domain broadcast rival.",
        # Gold cannot decide (frozen loops elaborate through Classical.choice,
        # so `decide` is STUCK there for any claim, true or false). Refute
        # against the loop-free direct-map positive instead: it VERIFIES
        # against the frozen spec and its extracted program REDUCES, so the
        # failure is a decided refutation rather than a stuck term.
        "witness_reference": _POS_MAP,
        "witness": _tester(
            "rebuildAttrsTester false 0 8 #[] #[(⟨5,2⟩:Lvl),(⟨6,3⟩:Lvl)] "
            "#[] #[(⟨5,0⟩:Lvl),(⟨6,0⟩:Lvl)]"),
    },
    {
        "id": "coord-extra-size",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_COORD_SIZE,
        "refinement": "appends a spurious extra coordinate level to the output. A "
                      "real patch that added a phantom coordinate would produce a "
                      "result whose coordinate set differs from the aligned "
                      "skeleton, so the identity comparison fails — it would NOT "
                      "resolve.",
        "rationale": "REJECT from C-csz (out.coords.size = resCoords.size): pushing "
                     "an extra level makes the size one greater than resCoords.size. "
                     "If it verified => SPEC-TOO-WEAK (the count clause would be "
                     "unenforced). Refuted at empty resCoords, where the rival "
                     "returns one coordinate.",
        # Gold cannot decide (frozen loops elaborate through Classical.choice,
        # so `decide` is STUCK there for any claim, true or false). Refute
        # against the loop-free direct-map positive instead: it VERIFIES
        # against the frozen spec and its extracted program REDUCES, so the
        # failure is a decided refutation rather than a stuck term.
        "witness_reference": _POS_MAP,
        "witness": _tester("rebuildAttrsTester false 0 1 #[] #[] #[] #[]"),
    },
    {
        "id": "var-first-slot-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_VAR_FIRST,
        "refinement": "ordinary regime: every data-var takes its by-name source "
                      "metadata EXCEPT index 0, left empty. A real patch skipping "
                      "the first data-var would leave it with empty metadata; the "
                      "multi-variable failing scenario expects that data-var to "
                      "carry its source metadata, so it would NOT resolve. The "
                      "var-carrier mirror of coord-first-slot-empty.",
        "rationale": "REJECT from C-var at index 0 (out.vars[0]! must equal "
                     "rebuiltVar … (resVars[0]!), but the rival forces 0 there). "
                     "Refuted at a 2-variable input where the rival is WRONG at "
                     "index 0 and CORRECT at index 1, claiming exactly its index-0 "
                     "sub-domain.",
        # Gold cannot decide (frozen loops elaborate through Classical.choice,
        # so `decide` is STUCK there for any claim, true or false). Refute
        # against the loop-free direct-map positive instead: it VERIFIES
        # against the frozen spec and its extracted program REDUCES, so the
        # failure is a decided refutation rather than a stuck term.
        "witness_reference": _POS_MAP,
        "witness": _tester(
            "rebuildAttrsTester false 0 1 #[(⟨5,2⟩:Lvl),(⟨6,3⟩:Lvl)] #[] "
            "#[(⟨5,0⟩:Lvl),(⟨6,0⟩:Lvl)] #[]"),
    },
    {
        "id": "var-drop-size",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_VAR_SIZE,
        "refinement": "drops the last data-var from the output. A real patch that "
                      "lost a data-var would produce a result whose variable set "
                      "differs from the aligned skeleton, so the identity "
                      "comparison fails — it would NOT resolve.",
        "rationale": "REJECT from C-vsz (out.vars.size = resVars.size): popping the "
                     "last level makes the size one less than resVars.size. If it "
                     "verified => SPEC-TOO-WEAK (the count clause unenforced). "
                     "Refuted at a 1-variable input, where the rival returns none.",
        # Gold cannot decide (frozen loops elaborate through Classical.choice,
        # so `decide` is STUCK there for any claim, true or false). Refute
        # against the loop-free direct-map positive instead: it VERIFIES
        # against the frozen spec and its extracted program REDUCES, so the
        # failure is a decided refutation rather than a stuck term.
        "witness_reference": _POS_MAP,
        "witness": _tester(
            "rebuildAttrsTester false 0 1 #[] #[] #[(⟨5,0⟩:Lvl)] #[]"),
    },
    {
        "id": "promo-top-leak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PROMO_TOP,
        "refinement": "under promotion the output global metadata is left as the "
                      "source's global token instead of being emptied. The failing "
                      "promotion scenario asserts the promoted result has empty "
                      "global metadata; leaving the source token there makes the "
                      "identity comparison fail — it would NOT resolve. The "
                      "promotion half of the regression.",
        "rationale": "REJECT from C-glob (out.gattrs = rebuiltGlobal promote "
                     "xGAttrs): under promote the modeled global is 0, but the "
                     "rival returns xGAttrs, not provably 0. If it verified => "
                     "SPEC-TOO-WEAK on the promotion regime. Refuted at promote = "
                     "true, xGAttrs = 1 — the only rival with promote = true on "
                     "the global clause.",
        # Gold cannot decide (frozen loops elaborate through Classical.choice,
        # so `decide` is STUCK there for any claim, true or false). Refute
        # against the loop-free direct-map positive instead: it VERIFIES
        # against the frozen spec and its extracted program REDUCES, so the
        # failure is a decided refutation rather than a stuck term.
        "witness_reference": _POS_MAP,
        "witness": _tester("rebuildAttrsTester true 0 1 #[] #[] #[] #[]"),
    },
    {
        "id": "promo-matching-slot-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PROMO_SLOT,
        "refinement": "under promotion the source-named variable is written the "
                      "empty mapping instead of the source's global metadata. The "
                      "promotion scenario expects the promoted data-var to carry "
                      "the source's global metadata; emptying it makes the identity "
                      "comparison fail — it would NOT resolve.",
        "rationale": "REJECT from C-var at the promoted slot (rebuiltVar true xName "
                     "xGAttrs demands the source-named variable receive xGAttrs, "
                     "but the rival forces 0). Refuted at promote = true, xName = "
                     "7, xGAttrs = 3 with a data-var named 7 — varying xName and "
                     "the promotion branch of the variable clause, a point no other "
                     "rival probes.",
        # Gold cannot decide (frozen loops elaborate through Classical.choice,
        # so `decide` is STUCK there for any claim, true or false). Refute
        # against the loop-free direct-map positive instead: it VERIFIES
        # against the frozen spec and its extracted program REDUCES, so the
        # failure is a decided refutation rather than a stuck term.
        "witness_reference": _POS_MAP,
        "witness": _tester(
            "rebuildAttrsTester true 7 3 #[] #[] #[(⟨7,9⟩:Lvl)] #[]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 7 uniqueness rivals — 2 of which are the MANDATORY
# frame-mutation pair) plus AXIOM_TESTS = []. The Lean-family bundle models the
# purely functional per-level metadata rebuild as a SINGLE method (`rebuildAttrs`
# with one `prove_correct`), so the carrier narrows and the permission machinery
# falls away.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-hoist-top           -> pos-map-direct / pos-local-reshape  PORTED (2)
#   admiss-f2p-shaped-input         -> admiss-promotion-worked-example     RE-AIMED
#   frame-mut-write-coord           -> (none)                              OMITTED (vacuous)
#   frame-mut-append-var            -> (none)                              OMITTED (vacuous)
#   coord-broadcast-top             -> coord-broadcast-global              PORTED
#   coord-first-slot-empty          -> coord-first-slot-empty              PORTED
#   promo-top-leak                  -> promo-top-leak                      PORTED
#   promo-matching-slot-drop        -> promo-matching-slot-drop            PORTED
#   var-first-slot-empty            -> var-first-slot-empty                PORTED
#                                      (+ coord-extra-size, var-drop-size  ADDED)
#
# 5 rivals ported, 1 positive split into 2 structurally-distinct correct impls
# (a loop-free direct map AND an in-loop local reshape), 1 admissibility re-aimed,
# 2 size rivals added, 2 frame-mutation rivals omitted as vacuous = 10 SPEC cases.
#
# RE-AIMED (admissibility): the sibling injects a fresh F2P-shaped input inside
#   the impl and self-calls to establish the callee's `Requires`. `rebuildAttrs`
#   declares NO `require` clause, so there is no precondition to admit and the
#   probe is vacuous. It is re-aimed at the residual admissibility risk on a total
#   domain — that the post-image is DEGENERATE at the interesting point — via an
#   in-region assert pinning the promotion worked shape (global emptied, a
#   coordinate keeping its own by-name metadata, the source-named variable taking
#   the source global). The assert is live (a false variant leaves an unsolved
#   goal, verified).
# ADDED (2): coord-extra-size and var-drop-size. The velvet spec states the two
#   level-COUNT clauses (C-vsz, C-csz) as INDEPENDENT top-level `ensures`, where
#   nagini folded length into its P-coord clause. Coverage requires every
#   independent clause be attacked, so a count rival is added per carrier.
# OMITTED (2, both VACUOUS on this backend, not because they were hard):
#   * frame-mut-write-coord and frame-mut-append-var — the sibling writes /
#     appends to a source list held at a fractional heap permission (Acc(.,1/2))
#     and is rejected for INSUFFICIENT PERMISSION. Lean/Velvet are referentially
#     transparent: xVars/xCoords are immutable Array Lvl values, no parameter is
#     `mut`, there is no heap and no aliasing, so there is no read-only input to
#     mutate. No expressible instance; no substitute fabricated (per the porting
#     map, this class is genuinely vacuous here).
# DIVERGENCE / NON-TERMINATION lane: the sibling ships none, so nothing to port,
#   and nothing to record as a hole. The "genuinely vacuous / total functional
#   rebuild" reason is withdrawn: the frozen impl is two `while` loops, and a
#   rival may splice another. The class is closed by the verifier. Under
#   `loom.semantics.termination "total"` a postcondition is claimed of ALL runs,
#   so every loop owes a decreasing measure AND its descent (hence the frozen
#   `decreasing resVars.size - i` / `decreasing resCoords.size - k`). Measured
#   with the proofs reduced to `loom_solve`: a spliced `decreasing z` loop whose
#   body is `z := z + 1` is refused on `case «decreasing_1: z»`, residual
#   `z + 1 < z`.
# AXIOM_TESTS: dropped. The sibling's AXIOM lane is empty; the changed behaviour
#   is modelled deeply (empty `axioms` region) and its soundness against the real
#   patched callee is a G-CONF concern (mapping.md §3, G-AX skips). This gate
#   ignores AXIOM_TESTS regardless.
#
# WITNESSABILITY. Every ensures clause is over a fully transparent, DecidableEq
#   carrier (Nat / Array Lvl), so — unlike the opaque-frame scikit-learn sibling —
#   every rival is refutable by a concrete `decide` witness through the extracted
#   tester. No conditioning on an opaque term is needed, and no hypotheses appear
#   on any witness (so there is no consistency obligation). Each witness was
#   confirmed with two real builds: it ELABORATES against its rival (the loop-free
#   extracted program reduces) and FAILS against the frozen solution (the
#   loop-based extracted program does not reduce under `decide`).
AXIOM_TESTS = []
