"""PBT falsification battery for matplotlib__matplotlib-26466 (lean backend).

Ported from the nagini sibling's spec lane. NOT a Lean module: a record of
adversarial cases the G-PBT gate executes. Each SPEC_TESTS case is a full
Solution.lean variant that shares the frozen spec byte-for-byte (only the impl
region, and where a positive legitimately reproves, the proof body, differ), and
`expect` records whether the frozen spec must accept or refute it.

Defended surface (TWO obligations: correct_freezeOffsetOrigin, correct_freezeAnchorPoint)
-----------------------------------------------------------------------------------------
Each models one construction site that captures a 2D coordinate handed in by the
caller. Signature per site

  implementation_<site> (initial : Rat × Rat) : StoredCoord

with the single load-bearing postcondition clause

  (P) problem_spec_<site> initial out  :=  ∀ later : Rat × Rat, observe out later = initial

`StoredCoord` has exactly two inhabitants-of-interest: `snapshot x y` (detached —
`observe` ignores `later`) and `reference` (bound to the source — `observe`
returns `later`). (P) is a SINGLE top-level clause but it does real double duty,
and the two halves are attacked separately below:

  (P-detach)  the universally-quantified `later` forces detachment. A `reference`
              out satisfies `observe out later = initial` only at the single point
              later = initial, so ∀ later refutes it. This is the alias->copy
              heart of the change.
  (P-value)   the right-hand side is `initial` ITSELF, so the captured components
              must be exactly the two input components, in order, untransformed.
              A detached-but-wrong snapshot (transposed, duplicated, rounded)
              satisfies detachment and still fails (P).

Input binders of the spec predicate: `initial` (the construction-time coordinate)
and, inside (P), the quantified `later` (the source's contents at read time). The
reject witnesses below vary BOTH: `initial` ranges over integral asymmetric
points, an integral symmetric point, and the fractional (1/2, 1/2); `later`
ranges over points equal to, differing from, above and below `initial`. A witness
that held `later` fixed would say nothing about the ∀ that carries (P-detach).

Lanes present, and the two classes that are genuinely vacuous here
------------------------------------------------------------------
soundness / admissibility / uniqueness are all represented. Two nagini classes
have no shippable counterpart on this carrier, each for a demonstrated reason:

* FRAME-MUTATION (nagini's `frame-mutation-*`, rejected by writing a container
  held at half permission). Lean is referentially transparent: there is no
  container to write and no permission to lack. The clause those cases defended —
  the operation does not take ownership of the caller's container — is what
  (P-detach) states directly. The frame hole they guard against is an
  UNCONSTRAINED OUTPUT SLOT, and this spec has none: (P) pins `out` uniquely, not
  merely partially. Machine-checked, not argued — this elaborates against the
  frozen spec:
      ∀ initial out, problem_spec_freezeOffsetOrigin initial out →
        out = StoredCoord.snapshot initial.1 initial.2
  With `out` categorically determined there is no slot a rival could fill freely,
  so the class cannot be non-vacuously instantiated.

* NON-TERMINATION (nagini's `weak-diverge-no-terminate-*`, rejected by
  MustTerminate). This is vanilla Lean 4 + Mathlib, NOT the Velvet carrier: the
  frozen file sets no `loom.semantics.termination` (the sibling velvet bundle
  does; this one has no `set_option` at all), because vanilla Lean has no such
  knob — every `def` must be shown terminating to elaborate at all. Measured, in
  both directions:
    - a self-recursive impl does NOT elaborate: `fail to show termination ...
      no parameters suitable for structural recursion`. It is rejected, but by
      the ELABORATOR before any spec is consulted, so its rejection attributes
      nothing to the spec and it is not a uniqueness case.
    - `partial def` makes it elaborate, and the impl is then genuinely opaque:
      the frozen obligation fails, but so does any witness — `decide` reports
      `reduction got stuck` on the irreducible term, the gate's own
      `witness-undecided` screen, so no discriminator exists.
    - the one shape that DOES elaborate and verify — an unbounded `while n >= 0`
      loop over a `Nat` counter followed by the correct capture — is not a
      counterexample: `Nat` never goes negative, so the loop is not what makes it
      pass. Its diverging prefix is DISCARDED rather than believed. Two probes
      show the postcondition is not vacuous under it: the same loop with the
      reference tail fails (`⊢ later = initial`) and with a transposed tail fails
      (`⊢ (initial.2, initial.1) = initial`), and `#eval` on it returns
      `StoredCoord.snapshot 1 2` promptly, i.e. it does not diverge as an
      executable either. So it is a correct impl carrying dead code, not a
      verified-but-hanging one.
  There is therefore no diverging impl this carrier both admits and can refute.

Carrier narrowing vs. the nagini sibling
----------------------------------------
The nagini carrier models the RETENTION MECHANISM through fractional list_pred
permissions over an `List[object]` container; this bundle models the retention's
OBSERVABLE CONSEQUENCE (`StoredCoord` + `observe` under every `later`) over
`Rat × Rat`. So the nagini permission clauses (P1)/(P3) — the caller keeps its
read share, the retained pair is freshly owned — have no counterpart as
permissions here; their content is carried by (P-detach) instead, which is what
those clauses were there to enforce. The identity pins (P5)/(P6) over nagini's
opaque component carrier become value equality on the `Rat` components, i.e.
(P-value). See the assessment in the port payload for the case-by-case
disposition, including the classes that are genuinely vacuous on this carrier.

Construction discipline (guarantees same_spec)
----------------------------------------------
The two sites are byte-identical in their impl region, so a bare impl-body string
is NOT unique in the file. Every variant is therefore built by `_swap` on the
WHOLE `def implementation_<site> ... ` block (header + body), which is unique
because the site name is in the header. The spec regions (docstrings,
`problem_spec_*`, `StoredCoord`, `observe`) are never touched, so `same_spec`
holds mechanically; the `theorem correct_<site>` STATEMENTS are reproduced
verbatim and only tactic bodies change, so the obligations survive.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26466"
# meta.json float_encoding is null: the two components are only stored and read
# back verbatim, so exact Rat stands in for the float coordinate and no float
# arithmetic is modeled.
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


_SITES = ("freezeOffsetOrigin", "freezeAnchorPoint")


def _impl(site, body):
    """The whole frozen `def implementation_<site>` block with `body` as its
    body. The header carries the site name, so the anchor is unique in the file
    and lies entirely inside the impl region."""
    return (f"def implementation_{site}\n"
            f"    (initial : Rat × Rat) : StoredCoord := Id.run do\n" + body)


# The frozen impl body, VERBATIM (comments included), shared by both sites.
_GOLD_BODY = (
    "  -- Read the two components of the construction-time coordinate and store them as\n"
    "  -- a detached snapshot; a later mutation of the source is irrelevant to it.\n"
    "  let x := initial.1\n"
    "  let y := initial.2\n"
    "  return StoredCoord.snapshot x y\n")


def _proof(site, body):
    """The whole frozen `theorem correct_<site>` block. The STATEMENT is
    reproduced byte-identically; only `body` (the tactic script) varies."""
    return (f"theorem correct_{site} :\n"
            f"    ∀ (initial : Rat × Rat),\n"
            f"      problem_spec_{site} initial\n"
            f"        (implementation_{site} initial) := by\n" + body)


_GOLD_PROOF = ("  intro initial later\n"
               "  unfold implementation_{site} observe\n"
               "  simp\n")


# ADMISSIBILITY proof body: discharge the obligation at the concrete F2P-shaped
# coordinate FIRST, as two `have`s, then close the frozen obligation verbatim.
#
# The frozen obligation carries no precondition, so PRECOND-TOO-STRONG has no
# hypothesis to be unsatisfiable at. Its analogue on a total carrier is the
# OBLIGATION ITSELF being unsatisfiable at an F2P-shaped input — a spec whose ∀
# `later` clause could not be met at the half-unit coordinate the F2P actually
# uses would be vacuously unprovable there, and no uniqueness rival would show
# it, because a rival's rejection looks the same either way.
#
# `hF2P` instantiates (P) at that coordinate; `hMut` evaluates the retained
# coordinate at a later state that DIFFERS from it, i.e. the source-was-edited
# read, and pins the result to the construction-time value. Both are proven, not
# assumed: no new declaration, no axiom, statement byte-identical, and the frozen
# tactic script still closes the obligation afterwards.
#
# Measured load-bearing rather than decorative: transplanting these same two
# `have`s onto the reference rival fails with `⊢ later = (2⁻¹, 2⁻¹)` and onto the
# rounding rival with `⊢ ↑⌊2⁻¹⌋ = 2⁻¹`, so they are discharged only by an impl
# that really does freeze that coordinate. Stated with `simp` rather than
# `decide`: `decide` gets stuck on this coordinate (the `Rat` inverse does not
# reduce in the kernel — measured `reduction got stuck ... Rat.inv`), which is a
# carrier fact worth recording here, since it is the same wall the rounding
# witnesses route around.
_ADMISS_PROOF = (
    "  have hF2P : problem_spec_{site} ((1/2 : Rat), (1/2 : Rat))\n"
    "      (implementation_{site} ((1/2 : Rat), (1/2 : Rat))) := by\n"
    "    intro later\n"
    "    unfold implementation_{site} observe\n"
    "    simp\n"
    "  have hMut : observe (implementation_{site} ((1/2 : Rat), (1/2 : Rat))) (1, 1)\n"
    "      = ((1/2 : Rat), (1/2 : Rat)) := by\n"
    "    unfold implementation_{site} observe\n"
    "    simp\n"
    "  intro initial later\n"
    "  unfold implementation_{site} observe\n"
    "  simp\n")


def _variant(bodies, proofs=None):
    """Solution.lean with the given per-site impl bodies (and optionally per-site
    tactic bodies) substituted. Sites absent from `bodies` keep the frozen impl."""
    src = _BASE
    for site in _SITES:
        if site in bodies:
            src = _swap(src, _impl(site, _GOLD_BODY), _impl(site, bodies[site]))
        if proofs and site in proofs:
            src = _swap(src, _proof(site, _GOLD_PROOF.format(site=site)),
                        _proof(site, proofs[site]))
    return src


# ---------------------------------------------------------------------------
# CORRECT impl bodies (soundness positives). Each is structurally different from
# the frozen impl but observationally identical, so (P) still holds and the
# obligation must still close — with a proof written for the NEW shape.
# ---------------------------------------------------------------------------

# Reads component 1 BEFORE component 0 (frozen reads 0 then 1) and renames the
# locals. Same fresh detached snapshot. The frozen tactic script still closes it.
_POS_REORDER = ("  let second := initial.2\n"
                "  let first := initial.1\n"
                "  return StoredCoord.snapshot first second\n")

# Routes the capture through a transposed intermediate and reads it back
# transposed, so the composition is the identity. This is the CORRECT
# near-neighbour of the transposition rival below: it exercises the same
# component-ordering machinery and must still verify, which is what makes the
# rival's rejection attributable to the value clause rather than to "any impl
# that mentions .2 before .1".
_POS_DOUBLE_TRANSPOSE = ("  let q : Rat × Rat := (initial.2, initial.1)\n"
                         "  return StoredCoord.snapshot q.2 q.1\n")

# A CORRECT reshape that is NOT definitionally equal to the frozen impl, and the
# only positive here that is not. Measured: both bodies above reduce to the
# frozen one by `rfl` (an `example : probe = implementation_<site> := rfl`
# elaborates for each), so they close under the frozen tactic script by
# CONVERSION and demonstrate nothing about reproving the obligation for a new
# shape — they are honest but weak. This body BRANCHES on whether the two
# components coincide and stores the first component into both slots on the
# diagonal arm, which is observationally the identity (on that arm the two
# components are equal) but reduces differently: `rfl` against the frozen impl
# FAILS for it, and the frozen `unfold; simp` script does NOT close it. Its proof
# therefore has to case-split and use the branch hypothesis, which is what a
# soundness positive is supposed to exercise. Must verify; else SPEC-TOO-STRONG
# (the spec would be pinning the impl's REDUCTION BEHAVIOUR rather than the
# captured coordinate).
_POS_BRANCH_DIAGONAL = ("  let x := initial.1\n"
                        "  let y := initial.2\n"
                        "  if x = y then\n"
                        "    return StoredCoord.snapshot x x\n"
                        "  return StoredCoord.snapshot x y\n")

# The tactic script for the branching positive: the frozen one does not close it.
_POS_BRANCH_PROOF = ("  intro initial later\n"
                     "  unfold implementation_{site} observe\n"
                     "  by_cases hxy : initial.1 = initial.2 <;> "
                     "simp [hxy, Prod.ext_iff]\n")

# ---------------------------------------------------------------------------
# WRONG impl bodies (uniqueness rivals).
# ---------------------------------------------------------------------------

# (alias) retain the source itself rather than a detached copy -- the PRE-PATCH
# behaviour verbatim (Solution_prepatch_1 / _2). Attacks (P-detach).
_RIVAL_REFERENCE = "  return StoredCoord.reference\n"

# (round) detached and fresh, but each component is floored on the way in. Over
# INTEGRAL coordinates this is the identity, so it agrees with the frozen impl on
# a whole sub-domain and is refutable only at a non-integral point. Attacks
# (P-value) on the value-lossy-transform axis.
_RIVAL_TRUNCATE = ("  let x := initial.1\n"
                   "  let y := initial.2\n"
                   "  return StoredCoord.snapshot ((⌊x⌋ : Rat)) ((⌊y⌋ : Rat))\n")

# (transpose) detached and fresh, components swapped. Identity on the diagonal,
# wrong off it. Attacks (P-value) on the component-ORDER axis.
_RIVAL_TRANSPOSE = ("  let x := initial.1\n"
                    "  let y := initial.2\n"
                    "  return StoredCoord.snapshot y x\n")

# (dup-first) detached and fresh, but the second component is dropped and the
# first duplicated. Attacks (P-value) on the "component 1 is read at all" axis.
_RIVAL_DUP_FIRST = "  let x := initial.1\n  return StoredCoord.snapshot x x\n"

# (dup-second) the mirror: the first component is dropped and the second
# duplicated. Attacks (P-value) on the "component 0 is read at all" axis. Both
# duplication rivals are needed because each leaves the OTHER component correct,
# so neither alone shows the spec pins both slots.
_RIVAL_DUP_SECOND = "  let y := initial.2\n  return StoredCoord.snapshot y y\n"

# (conditional alias) detaches on MOST inputs and keeps the source bound only
# where the two components coincide. Added by an audit pass: every rival above
# is unconditional, so each is wrong on a whole half-space and the battery never
# probed a rival that agrees with the required behaviour on all of the OFF-diagonal
# domain. That leaves the sharpest partial-domain attack on (P-detach) untested —
# a capture that snapshots whenever it can tell the two components apart and
# falls back to holding the source when it cannot. Its faithful real patch is a
# capture guarded by a same-value check that skips the copy on the degenerate
# input, which is the diagonal coordinate the F2P actually uses, so the later
# in-place edit of the source still moves the stored coordinate and the F2P does
# NOT resolve. Refutable ONLY at a symmetric `initial`, which is why the witness
# sits there and why every existing case's asymmetric points would certify it.
_RIVAL_ALIAS_ON_DIAGONAL = ("  let x := initial.1\n"
                            "  let y := initial.2\n"
                            "  if x = y then\n"
                            "    return StoredCoord.reference\n"
                            "  return StoredCoord.snapshot x y\n")


# Shared prose for the two alias rivals' refinement: the same real-world bug at
# two independently-changed sites.
_ALIAS_REFINEMENT_TAIL = (
    "Its faithful real patch is the base-commit behaviour itself: the object "
    "keeps the caller's mutable container instead of a by-value snapshot, so a "
    "later in-place edit of that container moves the coordinate already stored. "
    "That is exactly the reproduction in the problem statement and exactly what "
    "the F2P test observes: it edits the source container in place after "
    "construction and compares the two rendered figures, which then differ. The "
    "F2P does not resolve, so a rival verifying here would be a true "
    "verify-does-not-imply-resolve break."
)

# Shared prose for the value rivals: they are fresh AND detached, so the
# retention half of the contract is satisfied and only the value half catches
# them. On the nagini carrier this class was invisible to the permission system
# for the same reason.
_VALUE_REFINEMENT_HEAD = (
    "This rival captures by VALUE and is fully detached from the source, so the "
    "later-mutation symptom is gone and the retention half of the requirement "
    "holds; what it gets wrong is WHICH values it captures. "
)


SPEC_TESTS = [
    # ---- SOUNDNESS POSITIVES ------------------------------------------------
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant({s: _POS_REORDER for s in _SITES}),
        "rationale": "structurally-different CORRECT impl at BOTH sites: read "
        "component 1 before component 0 and rename the locals, then store the "
        "same detached snapshot of both components. (P) holds for every `later` "
        "because the stored pair is still `(initial.1, initial.2)`, so the "
        "obligation closes with the frozen tactic shape. Straight-line, no "
        "recursion, so no induction lemma is needed. Must verify; else "
        "SPEC-TOO-STRONG (the spec would be pinning the READ ORDER, which is "
        "not observable, rather than the captured value).",
    },
    {
        "id": "pos-double-transpose",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant({s: _POS_DOUBLE_TRANSPOSE for s in _SITES}),
        "rationale": "a second CORRECT shape at both sites: build a transposed "
        "intermediate pair and read it back transposed, so the net capture is "
        "the identity on both components. This is the correct near-neighbour of "
        "weak-transpose-b below — it touches the same component-ordering "
        "machinery and reaches the same snapshot — so its verifying is what "
        "shows that rival's rejection comes from the captured VALUE and not "
        "merely from mentioning the components out of order. Must verify; else "
        "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-branch-diagonal",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant({s: _POS_BRANCH_DIAGONAL for s in _SITES},
                           {s: _POS_BRANCH_PROOF.format(site=s)
                            for s in _SITES}),
        "rationale": "the only positive here that is NOT definitionally equal to "
        "the frozen impl, and it is why it exists. Both other positives reduce to "
        "the frozen body by `rfl` (measured: an `example : probe = "
        "implementation_<site> := rfl` elaborates for each), so they close under "
        "the frozen tactic script by CONVERSION and never exercise reproving. "
        "This impl BRANCHES on whether the two components coincide and stores "
        "the first into both slots on the diagonal arm — observationally the "
        "identity, since the components are equal exactly there, but a different "
        "reduction: `rfl` against the frozen impl FAILS and the frozen `unfold; "
        "simp` script does NOT close it, so the obligation must be REPROVEN by "
        "case-split on the branch hypothesis. Must verify; else SPEC-TOO-STRONG "
        "(the spec would be pinning the impl's reduction behaviour rather than "
        "the captured coordinate). Note this shape is the CORRECT near-neighbour "
        "of alias-on-diagonal-a below, which branches the same way and differs "
        "only in what the diagonal arm retains — so the pair localises that "
        "rival's rejection to the retention and not to the branch.",
    },
    # ---- ADMISSIBILITY ------------------------------------------------------
    {
        "id": "admiss-ground-f2p-coordinate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant({}, {s: _ADMISS_PROOF.format(site=s)
                                for s in _SITES}),
        "rationale": "the frozen obligation is SATISFIABLE at the concrete "
        "F2P-shaped input, discharged at both sites before the frozen obligation "
        "is closed verbatim. The frozen obligation has no precondition, so the "
        "nagini analogue (a Requires unmeetable by a normal caller) has no "
        "counterpart; the analogue that DOES exist on a total carrier is the "
        "obligation being unsatisfiable at an F2P-shaped input, which no "
        "uniqueness rival can reveal because a rejection looks identical either "
        "way. `hF2P` instantiates (P) at the half-unit coordinate the F2P hands "
        "both sites; `hMut` evaluates the retained coordinate at a LATER state "
        "differing from it — the source-was-edited read — and pins it to the "
        "construction-time value, so the admission is tied to the reading the "
        "F2P actually performs rather than to a point where every retention "
        "agrees. Both are proven, not assumed. Measured load-bearing: the same "
        "two `have`s transplanted onto the reference rival fail with `later = "
        "(2⁻¹, 2⁻¹)` and onto the rounding rival with `↑⌊2⁻¹⌋ = 2⁻¹`. Must "
        "verify; else PRECOND-TOO-STRONG.",
    },
    # ---- UNIQUENESS: (P-detach), the alias->copy heart ----------------------
    {
        "id": "alias-retain-source-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant({"freezeOffsetOrigin": _RIVAL_REFERENCE}),
        "refinement": "The first of the two independently-changed construction "
        "sites. " + _ALIAS_REFINEMENT_TAIL + " Solution_prepatch_1.lean is this "
        "same skeleton and fails verification (G-DIFF).",
        "rationale": "refuted by (P-detach): with `out = reference`, `observe "
        "out later = later`, so `∀ later, observe out later = initial` would "
        "force `later = initial` for EVERY later — false as soon as one later "
        "differs from the construction-time value. The witness instantiates the "
        "∀ at a `later` unequal to `initial`, which is precisely the "
        "edit-the-source-afterwards scenario. Note the rejection is attributed "
        "to the quantified binder `later`, not to `initial`.",
        "witness": r'''example : ¬ problem_spec_freezeOffsetOrigin (5, 6)
    (implementation_freezeOffsetOrigin (5, 6)) := by
  intro h
  exact absurd (h (7, 8)) (by decide)''',
    },
    {
        "id": "alias-retain-source-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant({"freezeAnchorPoint": _RIVAL_REFERENCE}),
        "refinement": "The same attack at the SECOND construction site, modeled "
        "separately because the two sites are changed independently (the bundle "
        "ships one failing prepatch per site). " + _ALIAS_REFINEMENT_TAIL +
        " Solution_prepatch_2.lean is this same skeleton and fails verification.",
        "rationale": "refuted by (P-detach) at the second obligation, same shape "
        "as alias-retain-source-a: `observe reference later = later ≠ initial`. "
        "The witness probes a DIFFERENT input point than its sibling (an "
        "asymmetric `initial` with a symmetric `later` below it, rather than an "
        "asymmetric `later` above), so the two cases do not stand on one point.",
        "witness": r'''example : ¬ problem_spec_freezeAnchorPoint (7, 3)
    (implementation_freezeAnchorPoint (7, 3)) := by
  intro h
  exact absurd (h (1, 1)) (by decide)''',
    },
    {
        "id": "alias-on-diagonal-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant({"freezeOffsetOrigin": _RIVAL_ALIAS_ON_DIAGONAL}),
        "refinement": "A PARTIAL-DOMAIN alias, added by an audit pass that found "
        "every other rival here unconditional and therefore wrong on a whole "
        "half-space. Its faithful real patch guards the copy with a same-value "
        "check and skips it on the degenerate input, keeping the caller's "
        "container in that one case. So the coordinate is correctly frozen "
        "whenever the two components differ, and still moves with a later "
        "in-place edit of the source exactly when they coincide — which is the "
        "symmetric coordinate the F2P hands both sites, so the rendered figures "
        "differ and the F2P does NOT resolve, while every PASS_TO_PASS test at an "
        "asymmetric coordinate keeps passing. That is the sharpest form of this "
        "bug: it survives any battery whose detachment probes sit off the "
        "diagonal, which is where both shipped alias witnesses sit.",
        "rationale": "refuted by (P-detach) at a SYMMETRIC `initial`, the one "
        "point class no other case probes: on the diagonal arm `out = reference`, "
        "so `observe out later = later`, and `∀ later` forces `later = initial` "
        "for every later. The witness sits at (5, 5) and instantiates the ∀ at an "
        "asymmetric later; the rival's OFF-diagonal behaviour is identical to the "
        "required one, so the refutation is attributable to the guard rather than "
        "to the capture. Its correct near-neighbour pos-branch-diagonal branches "
        "identically and verifies, which is what shows this rejection comes from "
        "what the diagonal arm RETAINS and not from the branch itself.",
        "witness": r'''example : ¬ problem_spec_freezeOffsetOrigin ((5 : Rat), (5 : Rat))
    (implementation_freezeOffsetOrigin ((5 : Rat), (5 : Rat))) := by
  intro h
  exact absurd (h (7, 8)) (by decide)''',
    },
    # ---- UNIQUENESS: (P-value), value-lossy transform ----------------------
    {
        "id": "weak-round-components-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant({"freezeOffsetOrigin": _RIVAL_TRUNCATE}),
        "refinement": _VALUE_REFINEMENT_HEAD + "Its faithful real patch reads "
        "the two components but coerces each to a whole number on the way into "
        "the stored pair. The coordinate the F2P test hands the first site is "
        "fractional — a half-unit point — so both components collapse to zero "
        "and the annotation is placed at the wrong location; the rendered "
        "figures differ and the F2P does NOT resolve. This is the class that "
        "makes the value clause load-bearing rather than decorative: over "
        "whole-number coordinates the rival is INDISTINGUISHABLE from the "
        "required behaviour, and several PASS_TO_PASS annotation tests use "
        "exactly such whole-number coordinates, so a battery that probed only "
        "integral points would certify it.",
        "rationale": "refuted by (P-value): the stored snapshot holds the "
        "floored components, so `observe out later = (0, 0) ≠ (1/2, 1/2) = "
        "initial` regardless of `later`. The witness must sit at a NON-INTEGRAL "
        "`initial` — this is the one case whose refutation depends on the "
        "fractional part of the binder `initial`, and it is stated at the "
        "half-unit point the F2P actually uses. `decide` gets stuck reducing the "
        "Rat inverse here, so the witness unfolds the operation for `simp` and "
        "finishes the arithmetic with `norm_num` instead.",
        "witness": r'''example : ¬ problem_spec_freezeOffsetOrigin ((1/2 : Rat), (1/2 : Rat))
    (implementation_freezeOffsetOrigin ((1/2 : Rat), (1/2 : Rat))) := by
  intro h
  have h1 := h (0, 0)
  simp [implementation_freezeOffsetOrigin, observe, Prod.ext_iff] at h1
  norm_num at h1''',
    },
    {
        "id": "weak-round-components-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant({"freezeAnchorPoint": _RIVAL_TRUNCATE}),
        "refinement": _VALUE_REFINEMENT_HEAD + "The same whole-number coercion "
        "at the second construction site, which the F2P exercises with the same "
        "fractional half-unit coordinate: the anchor point moves to the origin, "
        "the figures differ, the F2P does NOT resolve. Modeled separately from "
        "the first site because the two are changed independently — a patch "
        "could coerce at one site and not the other.",
        "rationale": "refuted by (P-value) at the second obligation. The witness "
        "instantiates the ∀ at a `later` ABOVE `initial` (rather than below, as "
        "its sibling does) to confirm the refutation does not depend on the "
        "direction of the later mutation: the floored snapshot is wrong at every "
        "`later`, since the failure is in the captured value and not in the "
        "retention.",
        "witness": r'''example : ¬ problem_spec_freezeAnchorPoint ((1/2 : Rat), (1/2 : Rat))
    (implementation_freezeAnchorPoint ((1/2 : Rat), (1/2 : Rat))) := by
  intro h
  have h1 := h (2, 2)
  simp [implementation_freezeAnchorPoint, observe, Prod.ext_iff] at h1
  norm_num at h1''',
    },
    # ---- UNIQUENESS: (P-value), component order ---------------------------
    {
        "id": "weak-transpose-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant({"freezeAnchorPoint": _RIVAL_TRANSPOSE}),
        "refinement": _VALUE_REFINEMENT_HEAD + "Its faithful real patch stores "
        "the two components in the opposite order. The stored anchor point is "
        "then the transposition of the requested one, so the annotation and its "
        "arrow land somewhere else entirely whenever the coordinate is off the "
        "diagonal. Several PASS_TO_PASS annotation tests place anchors at "
        "asymmetric coordinates and compare rendered images, so they break; the "
        "suite does NOT come out green. Worth noting the F2P's own coordinate is "
        "ON the diagonal, where this rival is the identity — so the F2P alone "
        "would not catch it, and the spec being strictly stronger than the F2P "
        "here is a property of the spec, not an artifact of the witness.",
        "rationale": "refuted by (P-value): the stored snapshot is "
        "`(initial.2, initial.1)`, so `observe out later ≠ initial` for every "
        "`later` as soon as the two components differ. The witness sits at an "
        "asymmetric `initial` — a point ON the diagonal would make this rival "
        "correct, so this binder's asymmetry is exactly what the case "
        "demonstrates. Distinct from the duplication rivals below: it drops "
        "neither component, only their order.",
        "witness": r'''example : ¬ problem_spec_freezeAnchorPoint (30, 20)
    (implementation_freezeAnchorPoint (30, 20)) := by
  intro h
  exact absurd (h (0, 0)) (by decide)''',
    },
    # ---- UNIQUENESS: (P-value), each component slot pinned ----------------
    {
        "id": "weak-dup-first-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant({"freezeAnchorPoint": _RIVAL_DUP_FIRST}),
        "refinement": _VALUE_REFINEMENT_HEAD + "Its faithful real patch reads "
        "the first component and stores it in BOTH slots, never reading the "
        "second. The stored anchor point is on the diagonal wherever the "
        "requested one was not, so its second coordinate is wrong and the "
        "annotation is misplaced along that axis; the PASS_TO_PASS annotation "
        "image comparisons at asymmetric anchors FAIL. Fresh and detached, so "
        "the retention half of the requirement is untouched — only the value "
        "clause catches it.",
        "rationale": "refuted by (P-value): the stored snapshot is "
        "`(initial.1, initial.1)`, whose SECOND slot differs from `initial.2` "
        "whenever the components differ. Paired with weak-dup-second-b to show "
        "the spec pins BOTH slots: this case leaves slot 0 correct, so on its "
        "own it would be consistent with a spec that constrained only slot 0. "
        "The witness probes an `initial` distinct from every other case's.",
        "witness": r'''example : ¬ problem_spec_freezeAnchorPoint (3, 4)
    (implementation_freezeAnchorPoint (3, 4)) := by
  intro h
  exact absurd (h (0, 0)) (by decide)''',
    },
    {
        "id": "weak-dup-second-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant({"freezeAnchorPoint": _RIVAL_DUP_SECOND}),
        "refinement": _VALUE_REFINEMENT_HEAD + "The mirror real patch: read the "
        "second component and store it in both slots, never reading the first. "
        "The first coordinate of the stored anchor is wrong, the annotation is "
        "misplaced along the other axis, and the same PASS_TO_PASS image "
        "comparisons FAIL. Shipped alongside weak-dup-first-b because a patch "
        "that drops one component is not caught by a battery that only tested "
        "dropping the other.",
        "rationale": "refuted by (P-value): the stored snapshot is "
        "`(initial.2, initial.2)`, whose FIRST slot differs from `initial.1` "
        "whenever the components differ. This is the case that shows slot 0 is "
        "pinned; its sibling shows slot 1 is. Given a separate witness rather "
        "than sharing one, because the two rivals fail at different slots and a "
        "shared witness would let each claim a sub-domain the manifest never "
        "demonstrated for it.",
        "witness": r'''example : ¬ problem_spec_freezeAnchorPoint (9, 2)
    (implementation_freezeAnchorPoint (9, 2)) := by
  intro h
  exact absurd (h (0, 0)) (by decide)''',
    },
]

# The axiom lane is G-AX's job and this gate ignores AXIOM_TESTS. This bundle has
# no `axiom`/`opaque` callee at all (meta.json axioms == [], and the axioms region
# says so explicitly), so there is no callee contract to fuzz either way.
AXIOM_TESTS = []
