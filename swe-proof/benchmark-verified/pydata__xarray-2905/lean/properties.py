# properties.py — G-PBT falsification battery for pydata__xarray-2905 (lean lane).
# NOT a Lean module; a record of adversarial cases the gate elaborates against the
# frozen spec. Ported from the nagini sibling's properties.py, re-expressed
# against this backend's carrier.
#
# Defended surface (read from Solution.lean):
#   implementation_prepare (data : Obj) : Obj
#   A preparation step normalizing an incoming object before it is stored. The
#   postcondition is a pair of total-by-cases clauses over the object's single
#   observed decision trait, and it pins the result on BOTH branches:
#     (C1) data.isContainer = true  → result = data.payload.getD data
#          — a recognized wrapper container is replaced by the payload it
#            exposes (and, when it exposes none, kept unchanged).
#     (C2) data.isContainer = false → result = data
#          — every other object is stored unchanged, INCLUDING one that
#            incidentally exposes a payload. This arm is the load-bearing one.
#   Both arms are FULLY GROUNDED: `result` is pinned to the input `data` or to a
#   projection of it, with no opaque callee, no axiom, and no answer-key oracle.
#   So there is no "wrong echo that still verifies" to build, and every rival has
#   to be wrong about a VALUE at a concrete point — which is exactly what makes
#   the four reject witnesses below decidable by `simp` on literals.
#
# Carrier translation from the nagini sibling. Nagini modeled the incoming object
# as a record of four independent read-only fields — a recognized-ness flag, a
# separate ".exposes a payload" flag, and two opaque identity TAGS standing for
# the two possible answers. This bundle instead models the object as an inductive
# `Obj` carrying the flag and an `Option Obj` payload, so:
#   * nagini's two free answer tags (`identity` / `values_identity`) become the
#     input `data` itself and `data.payload.getD data` — projections rather than
#     independent atoms. A rival can therefore no longer be refuted by "two
#     distinct free tags are not provably equal"; it must be refuted at a
#     CONCRETE `Obj` where those two projections genuinely differ. Every witness
#     below is built that way, which is the real work of this port.
#   * nagini's separate `exposes_values` flag collapses into `payload = some _`
#     vs `none`, and its precondition invariant (recognized ⇒ exposes) has no
#     counterpart: the frozen obligation here is unconditional (`∀ data : Obj`),
#     with no hypothesis to satisfy. Consequence for the port, stated plainly
#     because it COSTS a case: nagini's `partial-domain-prepatch-exposes-values`
#     rival keyed on `exposes_values` instead of the recognized-ness flag, and
#     relied on the invariant to keep the discriminating point in-domain. On this
#     carrier that same rival IS `weak-always-unwrap` below (keying on "is a
#     payload exposed" and unwrapping whenever one is, which for the `getD`
#     formulation is literally the unconditional unwrap), so the two nagini cases
#     merge into one here rather than both being portable.
#
# Domain reachability — why two extra rivals were BUILT, SEEN to discriminate,
# and then DROPPED. mapping.md records that a recognized container always exposes
# a payload, so `isContainer = true` with `payload = none` never co-occurs in the
# modeled reality, and a real container's payload is a bare array that exposes no
# further payload of its own. Two rivals refutable only at such points were
# authored and their witnesses confirmed to discriminate (elaborate against the
# rival, fail on the frozen solution):
#   * a rival substituting a degenerate stand-in for the payload-absent case of
#     C1, refuted only at (isContainer = true, payload = none);
#   * a rival unwrapping TWICE on the recognized branch, refuted only at a
#     payload that itself exposes a payload.
# Both are omitted anyway, because their `refinement` argument would be false:
# their faithful real patches differ from the gold only on inputs the modeled
# step cannot receive, so they would still resolve the F2P, and
# shipping them would claim a verify-does-not-imply-resolve break that does not
# exist. Every witness retained below sits at a point the real function reaches
# (an object exposing a payload without being a recognized container — the F2P
# object itself; a recognized container; a plain object exposing nothing — the
# issue's `set()`), so each reject case's refinement claim is honest.
#
# Vacuous / dropped classes (stated per directive, not silently omitted):
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean, and it is the class the
#     nagini sibling calls MANDATORY (its two `frame-mutation-*` cases are its
#     headline attack: the incoming object's fields are held read-only, so a rival
#     that OVERWRITES the recognized-ness flag or the surviving identity to
#     launder a branch obligation is rejected by the permission system rather
#     than for a wrong value). Lean is referentially transparent: `data : Obj` is
#     an immutable value, there is no aliasable heap cell to write and no
#     fractional permission to lack, so neither rival can even be expressed.
#     DEMONSTRATED, not asserted: transcribing the nagini rival's move directly
#     (`data.isContainer := false` inside the `Id.run do` block) does not compile
#     — "`data.isContainer` cannot be mutated, only variables declared using
#     `let mut` can be mutated". The write is rejected by the ELABORATOR, before
#     any spec obligation exists to launder, so there is no verdict a case could
#     attribute to the spec. Nothing to port, and NO substitute is fabricated.
#   * DIVERGENCE / NON-TERMINATION lane — NOT SHIPPABLE, and the reason is
#     narrower than "inexpressible". The nagini sibling carries no such case. The
#     frozen file sets no `loom.semantics.termination`: it is plain Lean, where a
#     total `def` has its termination discharged by the elaborator. A diverging
#     rival CAN nonetheless be written — `partial def implementation_prepare
#     (data : Obj) : Obj := implementation_prepare data` clears variant_scope
#     (no new axiom, no sorry, statement byte-identical) — and it does NOT verify,
#     so the spec is not too weak here. But its rejection cannot be WITNESSED:
#     `partial def` is opaque, with no equation lemmas, so the refutation's own
#     build against the rival fails (`h2 : implementation_prepare (...) = ...`
#     survives `simp`, goal `False` unsolved) rather than closing. A reject case
#     needs a witness that holds of the rival, so there is nothing to ship — the
#     honest disposition is "no witnessable case", not "the class does not exist".
#     Distinct from the known spec hole velvet's `partial` termination semantics
#     opens, where a non-terminating impl VERIFIES vacuously (see
#     the corpus-wide termination-semantics finding); here it is rejected, just unattributably.
#   * ADMISSIBILITY, nagini's `admiss-self-call-in-domain` — ported in SPIRIT
#     only, as `admiss-in-domain-shape` below. Nagini discharged the precondition
#     by a self-call whose `Requires` (the half-permissions plus the
#     recognized ⇒ exposes invariant) had to be re-established at the call site.
#     This obligation has NO precondition to re-establish, so there is nothing to
#     discharge; what remains worth checking is that the postcondition is
#     satisfiable at an F2P-shaped input at all, which the case asserts in-body.
#   * AXIOM lane — DROPPED. No `axiom`/`opaque` declaration in the frozen file;
#     the changed decision is modeled deeply (a structural case split), so there
#     is no assumed callee contract to probe. The axiom lane is G-AX's job and
#     this gate ignores it. AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "pydata__xarray-2905"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly on drift.
# The impl region body and the proof TACTIC body (everything after the theorem
# statement's `:= by`) are the only regions a variant may edit. The spec view,
# the signatures, and the byte-identical `theorem correct_prepare` STATEMENT are
# never touched, so same_spec holds by construction.

_IMPL_OLD = """\
def implementation_prepare (data : Obj) : Obj := Id.run do
  let mut result := data
  if data.isContainer then
    result := data.payload.getD data
  return result"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

_PROOF_OLD = """\
  intro data
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [implementation_prepare, Id.run, h, if_true, bind_pure_comp,
      map_pure]
    rfl
  · simp only [implementation_prepare, Id.run, h, Bool.false_eq_true,
      if_false, bind_pure_comp, map_pure]
    rfl"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant. Replaces the impl body, and (for
    soundness positives whose reshaped impl needs a matching proof) the proof
    tactic body. The theorem STATEMENT and the whole spec view are untouched."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY. Each is a structurally different
# but behaviourally identical correct impl, shipped WITH a tactic body that
# closes for the new shape. The theorem statement is byte-identical; no new
# lemma, no new axiom, no sorry. Each was built and confirmed to elaborate.
# ---------------------------------------------------------------------------

# pos-guard-inverted-early-return: ports nagini's
# `pos-control-reordered-early-return` — the guard is negated so the
# store-unchanged case is handled FIRST, and the result local is dropped in
# favour of two early returns. Each return is reached exactly under its own
# clause's guard, so both C1 and C2 stay individually discharged.
_POS_EARLY = """\
def implementation_prepare (data : Obj) : Obj := Id.run do
  if !data.isContainer then
    return data
  return data.payload.getD data"""

_POS_EARLY_PROOF = """\
  intro data
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp [implementation_prepare, Id.run, h]
    rfl
  · simp [implementation_prepare, Id.run, h]
    rfl"""

# pos-conditional-expression: ports nagini's `pos-control-conditional-expression`
# — the same total-by-cases function as ONE conditional expression, with no
# `Id.run do`, no `let mut`, and no control-flow branch at all. Confirms the spec
# does not secretly depend on the imperative encoding the frozen impl uses.
_POS_COND = """\
def implementation_prepare (data : Obj) : Obj :=
  if data.isContainer then data.payload.getD data else data"""

_POS_COND_PROOF = """\
  intro data
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp [implementation_prepare, h]
  · simp [implementation_prepare, h]"""

# pos-structural-match: NO direct nagini counterpart — it is a shape nagini's
# flat-record carrier could not express. Instead of testing the trait with an
# `if`, this dispatches by pattern-matching the object's own structure, so the
# decision is read off the constructor rather than computed by the projection
# `Obj.isContainer`. It also reconstructs the unchanged result (`.node false p`)
# rather than returning the binder `data`. If either clause were satisfiable only
# via the projection's syntactic form, or demanded the result be literally the
# input TERM rather than a value equal to it, this would fail.
_POS_MATCH = """\
def implementation_prepare : Obj → Obj
  | .node true p => p.getD (.node true p)
  | .node false p => .node false p"""

_POS_MATCH_PROOF = """\
  intro data
  cases data with
  | node c p =>
    cases c <;>
      refine ⟨fun h => ?_, fun h => ?_⟩ <;>
        simp_all [implementation_prepare, Obj.isContainer, Obj.payload]"""

# admiss-in-domain-shape: the spirit-port of nagini's
# `admiss-self-call-in-domain` (see the header note — there is no precondition to
# re-establish on this carrier). It keeps the frozen impl body and the frozen
# proof script VERBATIM and only adds an in-body `have` asserting that the
# postcondition is satisfiable at an F2P-shaped input: an object that exposes a
# payload while NOT being a recognized container must be kept unchanged. Nagini
# used `Assert(...)`; the lean analogue is a `have` discharged by a tactic. The
# only thing this case can fail on is a spec-shape regression at that point.
_ADMISS = """\
def implementation_prepare (data : Obj) : Obj := Id.run do
  have _hInDomain : problem_spec_prepare
      (Obj.node false (some (Obj.node false none)))
      (Obj.node false (some (Obj.node false none))) := by
    refine ⟨fun h => ?_, fun _ => rfl⟩
    simp [Obj.isContainer] at h
  let mut result := data
  if data.isContainer then
    result := data.payload.getD data
  return result"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each edits ONLY the
# impl region; each ships a `witness` that was BUILT and SEEN to discriminate
# (elaborates against the rival, fails against the frozen solution). Every
# witness point is reachable by the real function — see the header note.
# ---------------------------------------------------------------------------

# weak-always-unwrap: replace the payload unconditionally, with no trait test at
# all. This is the pre-change behaviour, and it is also where nagini's two
# separate rivals (`partial-domain-always-unwrap` and the `exposes_values`-keyed
# `partial-domain-prepatch-exposes-values`) merge on this carrier: because the
# unwrap is formulated as `payload.getD data`, "unwrap whenever a payload is
# exposed" and "always unwrap" are the same function. Correct on the whole
# recognized sub-domain; wrong on exactly the discriminating one.
_WEAK_ALWAYS_UNWRAP = """\
def implementation_prepare (data : Obj) : Obj := Id.run do
  let mut result := data
  result := data.payload.getD data
  return result"""

# weak-never-unwrap: drop the replacement entirely and always store unchanged.
# Correct on the whole store-unchanged sub-domain; wrong on every recognized
# container. Ports nagini's `partial-domain-never-unwrap`.
_WEAK_NEVER_UNWRAP = """\
def implementation_prepare (data : Obj) : Obj := Id.run do
  let mut result := data
  return result"""

# weak-guard-mirrored: keep both behaviours but attach each to the WRONG trait
# value — replace the payload exactly when the object is NOT a recognized
# container, and store a recognized container unchanged. Wrong on BOTH
# sub-domains at once. Ports nagini's `partial-domain-swapped-results`; on this
# carrier the cheapest way to write "swap the two branch results" is to mirror
# the guard, since the two results are projections of one input rather than two
# independent tags.
_WEAK_MIRRORED = """\
def implementation_prepare (data : Obj) : Obj := Id.run do
  let mut result := data
  if !data.isContainer then
    result := data.payload.getD data
  return result"""

# weak-fallback-substituted: NO nagini counterpart — it attacks the `payload`
# binder at its `none` value, which nagini's carrier could not reach (its
# "exposes" flag and its two answer tags were independent atoms, so the
# absent-payload fallback was not a projection anyone could get wrong). This
# rival unwraps unconditionally AND, when nothing is exposed, substitutes a
# fabricated stand-in instead of keeping the object. Every other rival above
# holds `payload` at `some _` on its witness, so without this case the
# `payload = none` half of the carrier is a value no rival was built to abuse.
_WEAK_FALLBACK = """\
def implementation_prepare (data : Obj) : Obj := Id.run do
  let mut result := data
  result := data.payload.getD (Obj.node true none)
  return result"""


# --- Witness helper. Each reject case states the frozen spec predicate directly
# at a concrete, fully-literal input and derives False from its two clauses, so
# `simp` decides it with no opaque term and no hypothesis of its own (the head
# binds nothing, so there are no assumptions that could be inconsistent).
# Checked in a file with the frozen obligations removed, so no tactic script can
# interfere.
def _witness(arg):
    return f"""\
example : ¬ problem_spec_prepare {arg}
    (implementation_prepare {arg}) := by
  intro hspec
  obtain ⟨h1, h2⟩ := hspec
  simp [problem_spec_prepare, implementation_prepare, Obj.isContainer,
    Obj.payload] at h1 h2"""


# A payload as the real function actually presents one: a bare array — not itself
# a recognized container, and exposing nothing further.
_BARE = "(Obj.node false none)"

# The three reachable witness points, named for what they model.
#   _EXPOSING  — a plain object that incidentally exposes a payload. This is the
#                F2P object; it is the point the change is ABOUT.
#   _CONTAINER — a recognized wrapper container exposing its payload.
#   _PLAIN     — a plain object exposing nothing at all (the issue's `set()`).
_EXPOSING = f"(Obj.node false (some {_BARE}))"
_CONTAINER = f"(Obj.node true (some {_BARE}))"
_PLAIN = "(Obj.node false none)"


SPEC_TESTS = [
    {
        "id": "pos-guard-inverted-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_EARLY, _POS_EARLY_PROOF),
        "rationale": (
            "ports nagini pos-control-reordered-early-return: correct impl with "
            "the guard negated (store-unchanged case handled first) and the "
            "result local replaced by two early returns. Each return is reached "
            "exactly under its own clause's guard, so C1 and C2 are each still "
            "individually discharged — reproved for the new shape with the "
            "theorem statement byte-identical. If it cannot verify => "
            "SPEC-TOO-STRONG (the spec would be constraining the branch ORDER, "
            "which is not behaviour)."
        ),
    },
    {
        "id": "pos-conditional-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_COND, _POS_COND_PROOF),
        "rationale": (
            "ports nagini pos-control-conditional-expression: the same "
            "total-by-cases function as ONE conditional expression — no Id.run "
            "do, no mutable local, no control-flow branch. Confirms neither "
            "clause depends on the imperative encoding the frozen impl happens "
            "to use. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-structural-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_MATCH, _POS_MATCH_PROOF),
        "rationale": (
            "no nagini counterpart — a shape its flat-record carrier could not "
            "express. Dispatches by pattern-matching the object's own structure "
            "rather than testing the trait projection, and RECONSTRUCTS the "
            "unchanged result instead of returning the input binder. Verifying "
            "shows C1/C2 are pinned to the projections' VALUES: neither is "
            "satisfiable only via the projection's syntactic form, and C2 does "
            "not secretly demand the result be literally the input term rather "
            "than a value equal to it. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-in-domain-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "spirit-port of nagini admiss-self-call-in-domain. Nagini's version "
            "discharged the function's own Requires via a self-call; this "
            "obligation is unconditional (no precondition to re-establish), so "
            "what remains worth checking is that the postcondition is "
            "SATISFIABLE at an F2P-shaped input — an object exposing a payload "
            "while not being a recognized container, which must be stored "
            "unchanged. Asserted in-body (nagini Assert(...) -> lean `have`), "
            "with the impl body and frozen proof script otherwise verbatim, so "
            "the only thing this can fail on is a spec-shape regression at that "
            "point. If it fails => the spec is unsatisfiable in-domain."
        ),
    },
    {
        "id": "weak-always-unwrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_UNWRAP),
        "witness": _witness(_EXPOSING),
        "refinement": (
            "this IS the pre-change behaviour, and its faithful real patch is "
            "the unpatched code. An object that merely exposes a payload without "
            "being a recognized container — exactly the object the F2P test "
            "stores, and the one the issue reports — is replaced by that "
            "payload's contents instead of being stored intact, so the stored "
            "value is not the object that was handed in and the F2P assertion "
            "that it comes back unchanged fails. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C2 (isContainer = false => result = data): at an object "
            "that is not a recognized container but exposes a payload, the rival "
            "returns the payload rather than the object. Witness at "
            "(isContainer = false, payload = some bare) — built and seen to "
            "elaborate against the rival and fail on the frozen solution. This "
            "case carries BOTH nagini partial-domain-always-unwrap and the "
            "exposes_values-keyed partial-domain-prepatch-exposes-values, which "
            "coincide on this carrier (see header). If it verifies => "
            "SPEC-TOO-WEAK on the clause the change is about."
        ),
    },
    {
        "id": "weak-never-unwrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NEVER_UNWRAP),
        "witness": _witness(_CONTAINER),
        "refinement": (
            "ports nagini partial-domain-never-unwrap. Dropping the replacement "
            "entirely is a real patch that deletes the unwrap rather than "
            "narrowing it: a recognized wrapper container would then be stored "
            "as the container instead of as the payload it re-exposes, so the "
            "unchanged handling of those container inputs regresses and their "
            "PASS_TO_PASS coverage fails. A different, non-resolving program."
        ),
        "rationale": (
            "rejected by C1 (isContainer = true => result = payload.getD data): "
            "at a recognized container the rival returns the container itself. "
            "Witness at (isContainer = true, payload = some bare) — a point "
            "distinct from weak-always-unwrap's, and the one that varies the "
            "trait binder. Built and seen to discriminate. If it verifies => "
            "SPEC-TOO-WEAK on the replace branch."
        ),
    },
    {
        "id": "weak-guard-mirrored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MIRRORED),
        "witness": _witness(_CONTAINER),
        "refinement": (
            "ports nagini partial-domain-swapped-results: both behaviours are "
            "present but attached to the wrong trait value, which is the "
            "opposite of the intended narrowing rather than a weakening of it. "
            "A real patch inverting the test replaces the payload of exactly the "
            "objects that must be stored intact and stores intact exactly the "
            "containers that must be replaced, so it resolves neither the F2P "
            "nor the container-handling PASS_TO_PASS coverage."
        ),
        "rationale": (
            "rejected by BOTH clauses — C1 at a recognized container (returns "
            "the container, must return the payload) and C2 at a non-container "
            "exposing a payload (returns the payload, must return the object). "
            "Witness at (isContainer = true, payload = some bare), where C1 "
            "alone refutes it; it is a strictly wronger rival than "
            "weak-never-unwrap and fails there for the same C1 reason, which is "
            "why it shares that point. Built and seen to discriminate. If it "
            "verifies => SPEC-TOO-WEAK on both arms."
        ),
    },
    {
        "id": "weak-fallback-substituted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_FALLBACK),
        "witness": _witness(_PLAIN),
        "refinement": (
            "no nagini counterpart. A real patch that reaches for the exposed "
            "payload unconditionally and, finding none, substitutes a fabricated "
            "stand-in rather than keeping the object, discards a plain object "
            "that exposes nothing at all — the issue's own second example, the "
            "one whose current handling is already correct. The stored value is "
            "then neither the object nor anything derived from it, so both the "
            "F2P assertion and the existing coverage for plain object inputs "
            "fail. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C2 at the payload-ABSENT point (isContainer = false, "
            "payload = none => result = data, but the rival returns its "
            "fabricated stand-in). This is the only rival that varies the "
            "`payload` binder to `none`: every other witness holds it at "
            "`some _`, so without this case the absent-payload half of the "
            "carrier — and the `getD` fallback that is the whole reason the "
            "unwrap is total — is a value no rival was built to abuse. Built and "
            "seen to discriminate. If it verifies => SPEC-TOO-WEAK on the "
            "fallback."
        ),
    },
]

# No axiom or opaque declaration in the frozen file: the changed decision is
# modeled deeply as a structural case split, so there is no assumed callee
# contract for the axiom lane to execute. That lane is G-AX's job regardless.
AXIOM_TESTS = []
