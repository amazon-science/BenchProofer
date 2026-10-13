"""properties.py — G-PBT falsification manifest for django__django-14011 (lean).

NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
executes over the frozen `Solution.lean` and stamps with a recorded verdict.
Every case is built by region surgery (`_swap`) and edits ONLY the
implementation region and, where a reshaped impl or a grounding `have` needs it,
the proof BODY. The spec view (pure / post-conditions) is byte-identical and
each `theorem correct_<name>` STATEMENT is preserved verbatim, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition (or, for the admissibility case, to the
precondition hypotheses), never to a tampered spec. No case introduces
`sorry` / `admit` / `native_decide` / an `axiom` / a new `theorem` or `lemma`.

DEFENDED SURFACE
----------------
The bundle models two independent value-level behaviors on a keyed registry of
managed resources (`List Resource`, keyed by `.name`, at most one entry per key):

  (A) `implementation_bindResources (reg provided : List Resource) : List Resource`
      pinned by `problem_spec_bindResources`, whose TWO independent top-level
      clauses are

        (A1) `result.Pairwise (fun a b => a.name ≠ b.name)`
             — the result carries no duplicate key, i.e. no stale shadow entry
               survives for a key the provided collection mentions;
        (A2) `∀ key, lookupRes result key = match lookupRes provided key with
                      | some r => some r | none => lookupRes reg key`
             — the result's lookup function is TOTALLY determined: every key the
               provided collection mentions resolves to the PROVIDED value, and
               every other key keeps exactly what the registry held before.

      Obligation: `theorem correct_bindResources`, guarded by two precondition
      hypotheses (`reg` and `provided` each have distinct keys).

  (B) `implementation_releaseResources (reg : List Resource) : List Resource`
      pinned by `problem_spec_releaseResources`, whose TWO independent top-level
      clauses are

        (B1) `result.map (·.name) = reg.map (·.name)`
             — the key sequence is preserved EXACTLY: same keys, same order,
               none added, none dropped;
        (B2) `∀ r ∈ result, r.isOpen = false`
             — every resulting resource is released.

      Obligation: `theorem correct_releaseResources`, unconditional.

The carrier is FULLY TRANSPARENT: `lookupRes`, `setRes` and `releaseRes` are
concrete deep models over a `List` of a `DecidableEq` structure, and the bundle
declares no `opaque` callee and consumes no axiom. So no witness needs to
condition on the carrier — every rival below is refuted by `decide` at a
concrete literal registry, and no witness binds a hypothesis (hence no
consistency probe is even reachable).

Clause coverage: (A1) is attacked by `dup-key-shadow`; (A2) by `no-install`,
`partial-install`, `fresh-registry`, `append-shadow` and `clobber-untouched`;
(B1) by `drop-released` (membership), `reverse-order` (ordering) and
`release-drop-last` (membership at the TAIL); (B2) by `no-release` and
`partial-release`. `partial-release` attacks B2 ONLY: it carries the last entry
over unreleased but still emits every key in order, so it SATISFIES B1 exactly
(checked by evaluation at the empty, two-entry and three-entry registries), and
its witness accordingly negates B2. Binder coverage: the reject witnesses
move `reg` across empty / one-entry / two-entry / three-entry registries and
across both settings of `isOpen`, and `provided` across empty-effect /
one-entry / two-entry collections, with the key sets overlapping `reg` in some
witnesses and disjoint from it in others — so neither binder is held at a fixed
value by the battery, and a rival that mishandled only one of them could not
slip through.

PORTING NOTES — which nagini cases carried over, which did not
--------------------------------------------------------------
The nagini sibling contracts two functions over an INDEX-ALIGNED triple of
lists (`tokens` / `has_override` / `override_tokens`, and `closed` / `tokens` /
`request`) plus an unforgeable capability predicate. This bundle models the same
two behaviors on a KEYED registry carrier, so the arguments port but the
mechanics are re-expressed:

  * `rival-partial-install-serve` -> `partial-install` (domain-completeness on
    the bind facet: the last provided entry is skipped).
  * `rival-clobber-noverride-serve` -> `clobber-untouched` (attacks the `none`
    arm of clause A2 — the keys the provided collection does NOT mention). On
    nagini this was an unguarded write over an index-aligned pin; here the
    keyed carrier makes it a payload reset of the co-resident untouched key.
    Its near-miss sibling `fresh-registry` (which DROPS those keys outright
    rather than resetting them) is given its own witness point, so each of the
    two rationales names a sub-domain the manifest actually demonstrates.
  * `rival-no-close-teardown` -> `no-release` (attacks clause B2 directly; this
    is the modeled counterpart of the shipped `Solution_prepatch.lean`).
  * `rival-partial-close-teardown` -> `partial-release` (domain-completeness on
    the release facet: the last registry entry is left live).
  * `rival-omit-handoff` -> `no-install`, which is the modeled counterpart of
    the shipped `Solution_prepatch_2.lean`. The nagini version rejected via an
    abstract capability predicate whose sole producer was a configuration call;
    this bundle has no capability carrier (mapping.md records that the
    configuration step carries no value-level output behavior and is not
    separately modeled), so the attack lands instead on the clause the
    capability existed to protect: with no install performed, a provided key
    does not resolve to its provided value.
  * `rival-handoff-wrong-server` has NO counterpart and is OMITTED. It laundered
    a capability from one server object to another; there is no server object
    and no capability predicate on this carrier, so there is nothing to launder
    and no wrong impl to write. This is carrier narrowing, not a dropped case.
  * `frame-mutate-override-serve` and `frame-mutate-tokens-teardown` are
    VACUOUS here. They wrote through a read-only fractional-permission
    reference and were rejected by the permission system; Lean is referentially
    transparent, with no aliasing and no fractional permission to subvert, so
    no counterpart rival exists. The frame obligation is instead discharged
    STRUCTURALLY by the specs themselves — clause A2's `none` arm pins every
    unmentioned key to its prior value and clause B1 pins the whole key
    sequence — and those two structural pins are what `clobber-untouched`,
    `fresh-registry`, `drop-released` and `reverse-order` attack in their place.
    No substitute is fabricated for the permission mechanics themselves.
  * There is no `diverge-*` / `nonterm-*` / `weak-diverge` case in the nagini
    sibling, and the class is genuinely vacuous on this backend regardless:
    both `implementation_*` are total Lean `def`s, so a diverging impl cannot
    be written at all.
  * `admiss-serve` / `admiss-teardown` -> ONE case, `admiss-ground-bind`.
    `correct_releaseResources` is unconditional (`∀ reg`, no hypothesis), so
    there is no precondition to prove usable and the teardown admissibility
    case has no counterpart. `correct_bindResources` DOES carry two hypotheses,
    so the surviving case exhibits a concrete registry-shaped input at which
    both hypotheses hold and the postcondition is then established.
  * `AXIOM_TESTS` are dropped: the axiom lane is G-AX's job and this gate
    ignores them (and this bundle consumes no axiom — G-AX is a skip stub).

Every reject case carries a `witness`: a Lean snippet negating one clause of the
spec predicate at one concrete literal input. It is checked in a file with the
frozen obligations removed and must (1) ELABORATE against the rival and (2)
FAIL against the frozen solution. All eleven were built both ways with
scripts/lean_verify.sh before shipping; none was accepted on inspection alone.
On every gold-side build the failure is a SEMANTIC refutation — `decide` reduces
the claim fully and reports the negation false — not a missing identifier, a
type error or a stuck reduction, so each witness is a real discriminator rather
than an artifact of the surgery.
"""
from pathlib import Path

INSTANCE = "django__django-14011"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl/proof-region substring; assert
    it actually matched so silent drift (Solution.lean edited) fails loudly at
    manifest load rather than producing a case that tests nothing."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — each lies ENTIRELY inside an impl region or a proof BODY of
# the frozen Solution.lean, and each is unique in the file.
# ---------------------------------------------------------------------------

# (A) the bind impl: its body, and the whole declaration (for the pure reshape).
_BIND_BODY = """  let mut r := reg
  for c in provided do
    r := setRes r c
  return r"""
_BIND_DECL = """def implementation_bindResources
    (reg provided : List Resource) : List Resource := Id.run do
""" + _BIND_BODY

# (A) the one step of correct_bindResources' proof body that names the impl, and
# the `intro` that opens it (the grounding `have` is spliced in front).
_BIND_HIMPL = """  have himpl : implementation_bindResources reg provided = provided.foldl setRes reg := by
    simp [implementation_bindResources, Id.run]
    rfl"""
_BIND_INTRO = "  intro reg provided hreg hprov\n"

# (B) the release impl: its body, and the whole declaration.
_REL_BODY = """  let mut out := []
  for c in reg do
    out := out ++ [releaseRes c]
  return out"""
_REL_DECL = """def implementation_releaseResources (reg : List Resource) : List Resource := Id.run do
""" + _REL_BODY

# (B) the one step of correct_releaseResources' proof body that names the impl.
_REL_HAVE = """  have h : implementation_releaseResources reg = reg.map releaseRes := by
    simp only [implementation_releaseResources, Id.run]
    suffices hg : ∀ (init : List Resource),
        (forIn reg init fun c r => (pure (ForInStep.yield (r ++ [releaseRes c])) : Id _))
          = init ++ reg.map releaseRes by
      have := hg []
      simpa using this
    intro init
    induction reg generalizing init with
    | nil => simp; rfl
    | cons a as ih =>
        rw [List.forIn_cons]
        show forIn as (init ++ [releaseRes a]) _ = _
        rw [ih]
        simp"""


# ===========================================================================
# POSITIVE CONTROLS — expect "verify"
# ===========================================================================

# (pos-bind-fold) Structurally DIFFERENT but CORRECT: the accumulator loop is
# replaced by a pure left fold over the provided collection — no `Id.run do`, no
# `let mut`, no `for`. Same per-entry transition, same traversal order. The proof
# is re-closed for the new shape by a single `unfold`+`rfl` in place of the
# `simp [.., Id.run]` reduction of the monadic body; everything downstream (the
# lookup lemma, the key-preservation lemma and the induction) is kept VERBATIM,
# so a failure here could only mean the spec is over-fit to the imperative code
# form => SPEC-TOO-STRONG. Confirmed by a real build.
_POS_BIND_FOLD = _swap(
    _swap(_BASE, _BIND_DECL,
          "def implementation_bindResources\n"
          "    (reg provided : List Resource) : List Resource :=\n"
          "  provided.foldl (fun acc c => setRes acc c) reg"),
    _BIND_HIMPL,
    "  have himpl : implementation_bindResources reg provided = provided.foldl setRes reg := by\n"
    "    unfold implementation_bindResources\n"
    "    rfl")

# (pos-release-map) Structurally DIFFERENT but CORRECT: the append-accumulator
# loop is replaced by a pure `List.map` — again no `Id.run do` / `let mut` /
# `for`, and the whole `forIn` induction the frozen proof needed to reassociate
# the accumulator disappears with it. Same result at every input. If a faithful
# correct impl in a different shape cannot satisfy the two release clauses, the
# spec over-constrains the code form => SPEC-TOO-STRONG. Confirmed by a real build.
_POS_RELEASE_MAP = _swap(
    _swap(_BASE, _REL_DECL,
          "def implementation_releaseResources (reg : List Resource) : List Resource :=\n"
          "  reg.map (fun c => releaseRes c)"),
    _REL_HAVE,
    "  have h : implementation_releaseResources reg = reg.map releaseRes := by\n"
    "    unfold implementation_releaseResources\n"
    "    rfl")

# (admiss-ground-bind) ADMISSIBILITY for the only obligation that HAS
# preconditions. `correct_bindResources` is guarded by two hypotheses (the
# registry has distinct keys; the provided collection has distinct keys), so the
# question "are they jointly satisfiable on a normal input, and is the
# postcondition then reachable?" is meaningful. The case splices a grounding
# `have` in front of the frozen proof: at a two-entry registry and a two-entry
# provided collection that OVERLAP in one key (the shape the modeled behavior
# actually sees — one key rebound, one left alone, one newly added), both
# hypotheses are discharged by `decide` and the postcondition is then obtained
# from the frozen proof's own key lemma. The frozen obligation is closed
# verbatim afterwards. If this fails, the precondition is unsatisfiable at a
# normal input or the postcondition unreachable from it => PRECOND-TOO-STRONG.
# Confirmed by a real build.
#
# The grounded postcondition names `implementation_bindResources` at that input,
# NOT the `List.foldl setRes` the frozen proof rewrites to. Grounding at the fold
# would be a weaker case: the fold is the frozen proof's own normal form, so such
# a `have` would witness only that the key lemma applies to its own argument and
# would still hold if the impl no longer reduced to that fold at all. Naming the
# impl forces the case to carry the reduction step too, so it grounds the
# precondition for the obligation as stated.
_ADMISS_GROUND = _swap(
    _BASE, _BIND_INTRO,
    """  have _admissible :
      ([{ name := "default", isOpen := true }, { name := "other", isOpen := true }]
        : List Resource).Pairwise (fun a b => a.name ≠ b.name) ∧
      ([{ name := "default", isOpen := false }, { name := "extra", isOpen := true }]
        : List Resource).Pairwise (fun a b => a.name ≠ b.name) ∧
      problem_spec_bindResources
        [{ name := "default", isOpen := true }, { name := "other", isOpen := true }]
        [{ name := "default", isOpen := false }, { name := "extra", isOpen := true }]
        (implementation_bindResources
          [{ name := "default", isOpen := true }, { name := "other", isOpen := true }]
          [{ name := "default", isOpen := false }, { name := "extra", isOpen := true }]) := by
    refine ⟨by decide, by decide, ?_⟩
    have hgi : implementation_bindResources
        [{ name := "default", isOpen := true }, { name := "other", isOpen := true }]
        [{ name := "default", isOpen := false }, { name := "extra", isOpen := true }]
      = List.foldl setRes
          [{ name := "default", isOpen := true }, { name := "other", isOpen := true }]
          [{ name := "default", isOpen := false }, { name := "extra", isOpen := true }] := by
      simp [implementation_bindResources, Id.run]
      rfl
    rw [hgi]
    exact key_lemma _ _ (by decide) (by decide)
""" + _BIND_INTRO)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (A) --- rivals against problem_spec_bindResources -------------------------

# (no-install) The provided collection is walked but nothing is installed: the
# registry is returned exactly as it was found. Attacks clause A2's `some` arm.
_RIVAL_NO_INSTALL = _swap(_BASE, _BIND_BODY, """  let mut r := reg
  for _ in provided do
    r := r
  return r""")

# (partial-install) Installs every provided entry EXCEPT the last one. Correct
# on every input whose provided collection is empty or whose last provided key
# is absent from the registry and never queried; wrong on the rest.
_RIVAL_PARTIAL_INSTALL = _swap(_BASE, _BIND_BODY, """  let mut r := reg
  for c in provided.dropLast do
    r := setRes r c
  return r""")

# (fresh-registry) Installs the provided entries into an EMPTY registry, so
# every key the provided collection does not mention is lost outright. Attacks
# clause A2's `none` arm by DROPPING those keys.
_RIVAL_FRESH_REGISTRY = _swap(_BASE, _BIND_BODY, """  let mut r := []
  for c in provided do
    r := setRes r c
  return r""")

# (append-shadow) Appends each provided entry instead of replacing the entry
# that already holds its key, so a rebound key ends up with TWO entries and the
# first-match lookup still returns the stale one. Attacks clause A2 (and A1).
_RIVAL_APPEND_SHADOW = _swap(_BASE, _BIND_BODY, """  let mut r := reg
  for c in provided do
    r := r ++ [c]
  return r""")

# (dup-key-shadow) PREPENDS each provided entry instead of replacing in place.
# This is the sharpest probe of clause A1 specifically: prepending makes the
# first-match LOOKUP correct for every key (clause A2 is satisfied), so the only
# thing wrong with it is the stale duplicate entry left behind for a rebound key
# — exactly what A1 forbids. Its witness therefore negates A1, not A2.
_RIVAL_DUP_KEY = _swap(_BASE, _BIND_BODY, """  let mut r := reg
  for c in provided do
    r := [c] ++ r
  return r""")

# (clobber-untouched) Keeps every key but RESETS the payload of the entries the
# provided collection never mentions, before installing the provided ones. The
# near-miss to `fresh-registry`: it agrees with the frozen behavior on the key
# SET (so it satisfies A1 and A2's `some` arm) and is wrong only on A2's `none`
# arm, and only in the payload. Refuted at a registry where a mentioned and an
# unmentioned key are CO-RESIDENT, which is the sub-domain its rationale claims
# and which `fresh-registry`'s single-entry witness point does not reach.
_RIVAL_CLOBBER = _swap(_BASE, _BIND_BODY,
                       """  let mut r := reg.map (fun d => { d with isOpen := false })
  for c in provided do
    r := setRes r c
  return r""")

# (B) --- rivals against problem_spec_releaseResources ----------------------

# (no-release) The registry is walked and rebuilt entry-for-entry, but no entry
# is actually released: every resource is carried over as found. Attacks clause
# B2 (and satisfies B1 exactly, so the witness must negate B2).
_RIVAL_NO_RELEASE = _swap(_BASE, _REL_BODY, """  let mut out := []
  for c in reg do
    out := out ++ [c]
  return out""")

# (partial-release) Releases every entry EXCEPT the last, which is carried over
# still live. Domain-completeness on the release facet: correct exactly on the
# inputs whose last entry was already released (or which are empty).
_RIVAL_PARTIAL_RELEASE = _swap(_BASE, _REL_BODY, """  let mut out := []
  for c in reg.dropLast do
    out := out ++ [releaseRes c]
  for c in reg.drop (reg.length - 1) do
    out := out ++ [c]
  return out""")

# (drop-released) Releases correctly but OMITS from the result every entry that
# was already released on entry, so the registry silently loses those keys.
# Satisfies clause B2 vacuously for them; attacks clause B1.
_RIVAL_DROP_RELEASED = _swap(_BASE, _REL_BODY, """  let mut out := []
  for c in reg do
    if c.isOpen then
      out := out ++ [releaseRes c]
  return out""")

# (reverse-order) Releases every entry — B2 fully satisfied — but rebuilds the
# registry in REVERSE order, so the key sequence is permuted. Attacks the
# ORDERING half of clause B1, which no other rival touches, and is refuted at a
# three-entry registry (a two-entry point would not distinguish a reversal from
# a swap of the pair).
_RIVAL_REVERSE_ORDER = _swap(_BASE, _REL_BODY, """  let mut out := []
  for c in reg do
    out := [releaseRes c] ++ out
  return out""")

# (release-drop-last) Releases every entry it emits, but DROPS the last one
# outright. Closes the gap `drop-released` leaves on clause B1: that rival only
# drops entries whose resource was ALREADY released, so an impl that loses a key
# whose resource is LIVE (the ordinary case) is unattacked by it, and
# `partial-release` — the other tail-shaped rival — keeps the key and only fails
# to release it. This one is domain-completeness on B1's membership half at the
# TAIL, and it is the counterpart of `partial-install` on the release facet.
_RIVAL_RELEASE_DROP_LAST = _swap(_BASE, _REL_BODY, """  let mut out := []
  for c in reg.dropLast do
    out := out ++ [releaseRes c]
  return out""")


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ----------------
    {"id": "pos-bind-fold", "kind": "soundness", "expect": "verify",
     "module": _POS_BIND_FOLD,
     "rationale": "structurally-different but CORRECT bind: the mutable accumulator loop is "
                  "replaced by a pure left fold (no do-block, no `let mut`, no `for`), with the "
                  "same per-entry transition and traversal order. Only the one proof step that "
                  "reduces the monadic body is re-closed; the lookup lemma, the key lemma and the "
                  "induction are kept verbatim, and the `theorem correct_bindResources` statement "
                  "is byte-identical. Both clauses (A1 no duplicate key, A2 the full lookup "
                  "characterization) must still hold. If it fails => SPEC-TOO-STRONG (the spec is "
                  "over-fit to the imperative code form rather than to the behavior)."},
    {"id": "pos-release-map", "kind": "soundness", "expect": "verify",
     "module": _POS_RELEASE_MAP,
     "rationale": "structurally-different but CORRECT release: the append-accumulator loop is "
                  "replaced by a pure map, which also removes the need for the accumulator "
                  "reassociation induction the frozen proof carries. Same result at every input, so "
                  "both clauses (B1 exact key sequence, B2 every resource released) must still "
                  "hold, with the `theorem correct_releaseResources` statement unchanged. If it "
                  "fails => SPEC-TOO-STRONG."},
    {"id": "admiss-ground-bind", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_GROUND,
     "rationale": "the only obligation with preconditions is `correct_bindResources` (both inputs "
                  "must have distinct keys). This case grounds them at a normal input for the "
                  "modeled behavior — a two-entry registry and a two-entry provided collection "
                  "overlapping in one key, so one key is rebound, one is left alone and one is "
                  "newly added — discharging both hypotheses by evaluation and then obtaining the "
                  "postcondition at that very input. It proves the precondition is jointly "
                  "satisfiable on a realistic shape AND that the postcondition is reachable from "
                  "it. If it fails => PRECOND-TOO-STRONG."},

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {"id": "no-install", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_INSTALL,
     "refinement": "this is the modeled shape of the shipped pre-patch variant for the bind "
                   "behavior: the request-handling thread never installs the provided collection "
                   "and runs against whatever registry it happened to start with. Its faithful "
                   "real patch performs no binding at all, so the thread serving each request uses "
                   "a fresh per-thread connection rather than the one handed to the server — the "
                   "F2P cases that require data written through the test's own connection to be "
                   "visible to the served view, and fixtures loaded by the test to be visible to "
                   "it, both fail. Would NOT resolve.",
     "rationale": "attacks clause A2's `some` arm: `∀ key, lookupRes result key = ...` requires a "
                  "key the provided collection mentions to resolve to the PROVIDED value. With no "
                  "install performed it resolves to whatever the registry held (here: nothing). "
                  "Witness negates that clause at a one-entry registry and a disjoint one-entry "
                  "provided collection. If it verified => SPEC-TOO-WEAK (the spec would admit an "
                  "impl that ignores the provided collection entirely).",
     "witness": """
example : ¬ problem_spec_bindResources
    [{ name := "alpha", isOpen := true }] [{ name := "beta", isOpen := true }]
    (implementation_bindResources
      [{ name := "alpha", isOpen := true }] [{ name := "beta", isOpen := true }]) := by
  intro h
  have hk := h.2 "beta"
  revert hk
  unfold implementation_bindResources lookupRes
  decide
"""},
    {"id": "partial-install", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_INSTALL,
     "refinement": "installs every provided entry except the last one. A faithful real patch of "
                   "this shape (a bind loop that stops one short) leaves the last provided "
                   "connection uninstalled, so a request touching that alias operates on a fresh "
                   "empty per-thread connection instead of the one the test supplied — the same "
                   "F2P visibility failures as a total omission, on the sub-domain where that "
                   "alias is the one exercised. Would NOT resolve.",
     "rationale": "domain-completeness on the bind facet. Clause A2 is universally quantified over "
                  "keys, so it pins the LAST provided entry exactly as it pins the first; the rival "
                  "pins only the sub-domain whose final provided key is never queried. Witness "
                  "negates A2 at an EMPTY registry with a two-entry provided collection, so it "
                  "isolates the skipped final entry (and varies both binders away from the "
                  "one-entry points the other rivals use). If it verified => SPEC-TOO-WEAK "
                  "(domain-incomplete on the bind facet).",
     "witness": """
example : ¬ problem_spec_bindResources
    [] [{ name := "one", isOpen := true }, { name := "two", isOpen := false }]
    (implementation_bindResources
      [] [{ name := "one", isOpen := true }, { name := "two", isOpen := false }]) := by
  intro h
  have hk := h.2 "two"
  revert hk
  unfold implementation_bindResources lookupRes
  decide
"""},
    {"id": "fresh-registry", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRESH_REGISTRY,
     "refinement": "binds the provided entries into an empty registry, discarding every key the "
                   "provided collection does not mention. A faithful real patch of this shape "
                   "(replacing the registry wholesale rather than binding into it) would leave the "
                   "request-handling thread with no connection at all for any alias the test did "
                   "not supply, so a view touching such an alias has nothing to run against. Would "
                   "NOT resolve.",
     "rationale": "attacks clause A2's `none` arm: an unmentioned key must keep exactly what the "
                  "registry held before, and here it resolves to nothing instead. Witness negates "
                  "A2 at the unmentioned key of a one-entry registry with a disjoint provided "
                  "collection. Distinct from `clobber-untouched`, which keeps that key and only "
                  "resets its payload — this rival loses the key entirely. If it verified => "
                  "SPEC-TOO-WEAK (unmentioned keys unconstrained).",
     "witness": """
example : ¬ problem_spec_bindResources
    [{ name := "kept", isOpen := true }] [{ name := "given", isOpen := true }]
    (implementation_bindResources
      [{ name := "kept", isOpen := true }] [{ name := "given", isOpen := true }]) := by
  intro h
  have hk := h.2 "kept"
  revert hk
  unfold implementation_bindResources lookupRes
  decide
"""},
    {"id": "append-shadow", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_APPEND_SHADOW,
     "refinement": "appends each provided entry rather than replacing the entry already holding "
                   "its key, so a key present in both collections keeps its OLD value under "
                   "lookup. A faithful real patch of this shape registers the provided connection "
                   "without displacing the one already registered for that alias, so the thread "
                   "keeps using the connection it started with — the provided one is present but "
                   "never reached, which is observationally the same failure as never binding it. "
                   "Would NOT resolve.",
     "rationale": "attacks clause A2's `some` arm on the OVERLAPPING sub-domain the other bind "
                  "rivals do not reach: the key IS mentioned and IS installed, yet resolves to the "
                  "registry's prior value because a stale entry precedes it. Witness negates A2 at "
                  "a registry and a provided collection sharing one key with DIFFERENT payloads "
                  "(varying `isOpen` across the two binders, which the disjoint-key witnesses hold "
                  "equal). If it verified => SPEC-TOO-WEAK (the spec would not force the provided "
                  "value to actually win).",
     "witness": """
example : ¬ problem_spec_bindResources
    [{ name := "same", isOpen := true }] [{ name := "same", isOpen := false }]
    (implementation_bindResources
      [{ name := "same", isOpen := true }] [{ name := "same", isOpen := false }]) := by
  intro h
  have hk := h.2 "same"
  revert hk
  unfold implementation_bindResources lookupRes
  decide
"""},
    {"id": "dup-key-shadow", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DUP_KEY,
     "refinement": "prepends each provided entry instead of replacing in place, leaving a stale "
                   "second entry behind for every rebound key. A faithful real patch of this shape "
                   "registers the provided connection in a way that shadows rather than replaces "
                   "the previous registration for that alias, so the registry holds two "
                   "registrations for one alias: the subsequent teardown walk releases whichever "
                   "one it reaches and the other is left live, reproducing the very "
                   "connection-leak the issue reports at the end of the run. Would NOT resolve.",
     "rationale": "the sharpest probe of clause A1 (`result.Pairwise (·.name ≠ ·.name)`) "
                  "SPECIFICALLY: because the stale entry is prepended AFTER the fresh one, "
                  "first-match lookup is correct for every key, so this rival satisfies clause A2 "
                  "in full and the ONLY thing wrong with it is the duplicate key. Its witness "
                  "therefore negates A1 rather than A2 — the one reject case in the battery that "
                  "does. If it verified => SPEC-TOO-WEAK (A1 would be doing no work and the "
                  "list-as-keyed-registry frame hole would be open).",
     "witness": """
example : ¬ problem_spec_bindResources
    [{ name := "dup", isOpen := true }] [{ name := "dup", isOpen := false }]
    (implementation_bindResources
      [{ name := "dup", isOpen := true }] [{ name := "dup", isOpen := false }]) := by
  intro h
  have hk := h.1
  revert hk
  unfold implementation_bindResources
  decide
"""},
    {"id": "clobber-untouched", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CLOBBER,
     "refinement": "keeps every key but resets the state of the entries the provided collection "
                   "never mentions. A faithful real patch of this shape touches every alias in the "
                   "registry rather than only the supplied ones, so a live connection the test did "
                   "not supply is torn down underneath the thread that is about to use it; a view "
                   "reading through such an alias then fails. Would NOT resolve.",
     "rationale": "attacks clause A2's `none` arm in its PAYLOAD, not its key set — the near-miss "
                  "to `fresh-registry`, which drops those keys outright. Because it agrees with the "
                  "frozen behavior on clause A1 and on A2's `some` arm, its witness is placed at "
                  "the input that its rationale actually claims: a registry where a MENTIONED and "
                  "an UNMENTIONED key are co-resident, which `fresh-registry`'s single-entry point "
                  "does not reach. If it verified => SPEC-TOO-WEAK (unmentioned keys would be "
                  "pinned only by name, not by value).",
     "witness": """
example : ¬ problem_spec_bindResources
    [{ name := "given", isOpen := false }, { name := "untouched", isOpen := true }]
    [{ name := "given", isOpen := true }]
    (implementation_bindResources
      [{ name := "given", isOpen := false }, { name := "untouched", isOpen := true }]
      [{ name := "given", isOpen := true }]) := by
  intro h
  have hk := h.2 "untouched"
  revert hk
  unfold implementation_bindResources lookupRes
  decide
"""},
    {"id": "no-release", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_RELEASE,
     "refinement": "this is the modeled shape of the shipped pre-patch variant for the release "
                   "behavior: the registry is walked but nothing is released. Its faithful real "
                   "patch omits the post-request release step entirely, which is precisely the "
                   "reported defect — connections accumulate live across served requests and the "
                   "run ends with the database still in use by other users. Would NOT resolve.",
     "rationale": "attacks clause B2 (`∀ r ∈ result, r.isOpen = false`) directly. Note the rival "
                  "satisfies clause B1 exactly (same keys, same order), so the witness must negate "
                  "B2 specifically — it does, at a one-entry registry holding a LIVE resource. If "
                  "it verified => SPEC-TOO-WEAK (the spec would admit the leaking behavior the "
                  "issue is about).",
     "witness": """
example : ¬ problem_spec_releaseResources
    [{ name := "live", isOpen := true }]
    (implementation_releaseResources [{ name := "live", isOpen := true }]) := by
  intro h
  have hk := h.2
  revert hk
  unfold implementation_releaseResources
  decide
"""},
    {"id": "partial-release", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_RELEASE,
     "refinement": "releases every entry except the last, which is carried over still live. A "
                   "faithful real patch of this shape leaves one connection open after every "
                   "served request, so they still accumulate — the same leak the fix addresses, "
                   "merely slower. Would NOT resolve.",
     "rationale": "domain-completeness on the release facet: clause B2 is quantified over ALL "
                  "result entries, so the last one is pinned exactly as the first; the rival pins "
                  "only registries that are empty or whose last entry was already released. "
                  "Witness negates B2 at a TWO-entry registry (the smallest input that separates "
                  "'the last entry' from 'the only entry', and so from `no-release`'s point). If it "
                  "verified => SPEC-TOO-WEAK (domain-incomplete on the release facet).",
     "witness": """
example : ¬ problem_spec_releaseResources
    [{ name := "first", isOpen := true }, { name := "last", isOpen := true }]
    (implementation_releaseResources
      [{ name := "first", isOpen := true }, { name := "last", isOpen := true }]) := by
  intro h
  have hk := h.2
  revert hk
  unfold implementation_releaseResources
  decide
"""},
    {"id": "drop-released", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_RELEASED,
     "refinement": "releases correctly but omits from the resulting registry every entry that was "
                   "already released on entry. A faithful real patch of this shape drops the "
                   "registration for any alias whose connection happened to be idle at teardown, "
                   "so the next request finds no registration for it and the alias the test relies "
                   "on has silently vanished from the registry. Would NOT resolve.",
     "rationale": "attacks clause B1 (`result.map (·.name) = reg.map (·.name)`) on its "
                  "membership half: no key may be dropped, even one whose resource is already "
                  "released. The rival satisfies clause B2 vacuously for the entries it drops, so "
                  "the witness must negate B1 — it does, at a one-entry registry whose sole "
                  "resource is ALREADY released, which is the only setting of `isOpen` that "
                  "triggers the drop and is the opposite of the setting every other release "
                  "witness uses. If it verified => SPEC-TOO-WEAK (an impl could shrink the "
                  "registry while every surviving entry is dutifully released).",
     "witness": """
example : ¬ problem_spec_releaseResources
    [{ name := "already", isOpen := false }]
    (implementation_releaseResources [{ name := "already", isOpen := false }]) := by
  intro h
  have hk := h.1
  revert hk
  unfold implementation_releaseResources
  decide
"""},
    {"id": "reverse-order", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_REVERSE_ORDER,
     "refinement": "releases every entry but rebuilds the registry in reverse order. A faithful "
                   "real patch of this shape reorders the registrations while releasing them; "
                   "since the release walk and every later lookup are driven by that same "
                   "ordering, a registry whose order no longer matches the one the server was "
                   "handed hands the wrong connection to the wrong alias on the next request. "
                   "Would NOT resolve.",
     "rationale": "attacks the ORDERING half of clause B1 — `result.map (·.name) = reg.map (·.name)` "
                  "is a list equality, not a set equality — which no other rival touches: this one "
                  "satisfies clause B2 in full and preserves the key SET exactly. Witness negates "
                  "B1 at a THREE-entry registry, since a two-entry point cannot distinguish a "
                  "reversal from a permutation of the pair and would leave the ordering claim "
                  "undemonstrated; the point also mixes both settings of `isOpen`. If it verified "
                  "=> SPEC-TOO-WEAK (B1 would only be pinning the multiset of keys).",
     "witness": """
example : ¬ problem_spec_releaseResources
    [{ name := "aa", isOpen := true }, { name := "bb", isOpen := false },
      { name := "cc", isOpen := true }]
    (implementation_releaseResources
      [{ name := "aa", isOpen := true }, { name := "bb", isOpen := false },
        { name := "cc", isOpen := true }]) := by
  intro h
  have hk := h.1
  revert hk
  unfold implementation_releaseResources
  decide
"""},
    {"id": "release-drop-last", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RELEASE_DROP_LAST,
     "refinement": "releases every entry it keeps but drops the last registry entry outright, so "
                   "that key is gone from the registry the next request sees. A faithful real patch "
                   "of this shape rebuilds the registry one entry short while releasing, so the "
                   "alias that happened to sit last is silently deregistered: a later request "
                   "reading through it finds no registration at all, and the resource it dropped is "
                   "released but no longer tracked. Would NOT resolve.",
     "rationale": "domain-completeness on clause B1's MEMBERSHIP half at the tail, which neither "
                  "existing B1 rival reaches: `drop-released` only drops entries whose resource was "
                  "already released, so it leaves the ordinary live-resource case unattacked, and "
                  "`partial-release` keeps the last key (failing B2 instead). This rival satisfies "
                  "B2 in full — every entry it emits IS released — so the witness must negate B1, "
                  "and it does at a two-entry registry of LIVE resources, the smallest point that "
                  "separates 'the last entry' from 'the only entry'. If it verified => "
                  "SPEC-TOO-WEAK (an impl could shrink the registry at the tail while dutifully "
                  "releasing everything it kept).",
     "witness": """
example : ¬ problem_spec_releaseResources
    [{ name := "x", isOpen := true }, { name := "y", isOpen := true }]
    (implementation_releaseResources
      [{ name := "x", isOpen := true }, { name := "y", isOpen := true }]) := by
  intro h
  have hk := h.1
  revert hk
  unfold implementation_releaseResources
  decide
"""},
]
