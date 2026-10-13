# properties.py — G-PBT falsification battery for django__django-14752 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   get (render defaultRender : Obj → String → E) (objects : List Obj)
#       (fieldKey : String) (hasMore : Bool) : Resp E
#   A lookup handler assembles a response with two parts. The single
#   postcondition `problem_spec_get` pins BOTH independent components:
#     (C1) RESULTS: `result.results = objects.map (fun o => render o fieldKey)` —
#          the per-item rendering applied to EACH selected object, in order, with
#          the field key threaded through. No entry may be added, dropped,
#          reordered, or produced by anything other than `render` applied to the
#          matching object with `fieldKey`.
#     (C2) FLAG: `result.more = hasMore` — the has-more flag reported verbatim.
#   `render`, `defaultRender`, and the carriers `Obj`/`E` are all universally
#   quantified — the handler never inspects an object except through `render` and
#   never inspects an entry at all. So there is NO opaque answer-key to echo: the
#   only way to satisfy C1 is to route the loop through the DISPATCHED `render`
#   (not the hardwired `defaultRender`), which is exactly the fix.
#
# CARRIER NOTE / relation to the nagini sibling. Nagini modeled TWO functions —
# `build_results` (the queryset -> entry-list loop) and `default_record_entry` (the
# per-item conversion) — behind fractional read permissions, plus an opaque
# `record_entry` dispatch pin. This backend models only the purely functional core
# `get`, collapsing the queryset loop and the dispatch into the single clause C1
# (`objects.map (render · fieldKey)`) and the per-item conversion into the abstract
# `render`. So:
#   * nagini `weak-inline-default` (build_results inlines the DEFAULT instead of
#     deferring to the late-bound step — the literal pre-patch bug) ports to
#     `weak-dispatch-drop`: the rival routes the loop through `defaultRender`
#     (the hardwired inline entry) instead of the dispatched `render`.
#   * nagini `weak-partial-firstrow-inline` ports to `weak-firstrow-default`.
#   * nagini `weak-skip-last-record` (length/alignment) ports to
#     `weak-skip-last`.
#   * nagini `default_record_entry`'s field-level rivals (`weak-default-swap-
#     fields`, the id_val/text_val transpose) have NO counterpart: `E` is an
#     abstract entry type here, so the entry's INTERNAL id/text structure is not
#     modeled and a field transpose is not expressible. Omitted — see 'assessment'.
#     What IS modeled and additionally attackable is the ARGUMENT threaded into
#     `render` (the `fieldKey` binder) and the second top-level clause C2 (the
#     `more` flag) — neither had a nagini build_results counterpart. Rivals
#     `weak-wrong-fieldkey` and `weak-flag-constant` exercise those binders.
#   * AUDIT ADDITION. C1 as stated above claims four independent things — which
#     function is applied, with which argument, how MANY entries, and in what
#     ORDER — and the ported set demonstrated only the first three:
#     dispatch-drop/firstrow attack the function, wrong-fieldkey its argument,
#     skip-last the length from below. Nothing varied the PERMUTATION, and nothing
#     added an entry (a spec pinning only the multiset, or bounding the list only
#     from below, would have passed the whole ported set). `weak-reverse-order`
#     and `weak-duplicate-entry` close those two; both were machine-checked to
#     refute their rival and to be REFUTED BY gold before being added.
#   Every reject witness probes a DISTINCT (objects, fieldKey, hasMore) point so
#   every input binder of the spec predicate is varied.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY `reject-frame-mutation-rec` /
#     `reject-frame-mutation-list-elem`: the record fields were held at fractional
#     read permission and the rival WROTE them back). Lean is referentially
#     transparent — no aliasing, no fractional permission — so a "store into a
#     read-only input" rival is not expressible and the whole lane is VACUOUS here.
#     See 'assessment'.
#   * ADMISSIBILITY (nagini's `admiss-default-precond-admits` defended the
#     half-permission Requires). AUDIT CORRECTION: the port recorded this lane as
#     N/A because the lean obligation `∀ (render defaultRender) (objects)
#     (fieldKey) (hasMore), problem_spec_get … (implementation_get …)` carries no
#     precondition hypothesis. That reason is WRONG — "no precondition binder to
#     attack" is not "nothing to test". The analogue on a total carrier is the
#     obligation being UNSATISFIABLE at a concrete F2P-shaped input: a spec whose
#     ∀-statement holds only abstractly (or is contradictory once the carriers and
#     both rendering parameters are instantiated at ground values) would still
#     stamp a green obligation while admitting no real responder. Case
#     `admiss-f2p-shaped-instance` tests that directly and is now LANDED, so the
#     lane is exercised rather than dropped. See 'assessment'.
#     AUDIT NOTE: this reason was independently re-derived and CONFIRMED. Lean's
#     `Solution.lean` here has no `partial`/`opaque` term and no aliasing carrier,
#     so a rival cannot express a write-back to a read-only input; the nagini
#     rivals' rejection came from the PERMISSION SYSTEM, which has no analogue.
#     What that lane defended — that no output component is left free for a rival
#     to fabricate — is covered on this carrier by C1+C2 pinning BOTH fields of
#     `Resp`, exercised by the rivals below.
#   * DIVERGENCE / NON-TERMINATION. `implementation_get` is a total Lean `def`; a
#     non-terminating implementation cannot be written at all, so the class is
#     genuinely VACUOUS here. This is the vanilla-lean backend with no
#     `loom.semantics.termination "partial"` option in play, so the measured
#     partial-bundle spec hole recorded in the corpus-wide termination-semantics finding does not
#     apply to this cell; nothing to ship either way.
#     (The nagini sibling carries no diverge-* case anyway.) See 'assessment'.
#   * AXIOM_TESTS (nagini's `ax-default-reference` / `ax-dispatch-honoured`). The
#     axiom lane is G-AX's job; this gate ignores them. `render`/`defaultRender`
#     are universally quantified with no consumed axiom, so the lane is vacuous
#     here regardless.
from pathlib import Path

INSTANCE = "django__django-14752"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the loop-shape positive) swaps THIS block.
_IMPL = (
    "def implementation_get {Obj E : Type}\n"
    "    (render _defaultRender : Obj → String → E)\n"
    "    (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do\n"
    "  -- Build the results list by applying the per-item rendering to each selected\n"
    "  -- object in turn. The per-item rendering used is `render` — the dispatched,\n"
    "  -- hence overridable, step — applied uniformly to every selected object.\n"
    "  let mut results : List E := []\n"
    "  for o in objects do\n"
    "    results := results ++ [render o fieldKey]\n"
    "  -- Report the has-more flag verbatim.\n"
    "  return { results := results, more := hasMore }"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the pure-map-expression positive, whose different impl shape needs an (equally
# cheap, honest) reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro render defaultRender objects fieldKey hasMore\n"
    "  -- Helper: the cleaned `forIn` accumulation appends the per-item renderings.\n"
    "  have helper : ∀ (os : List Obj) (init : List E),\n"
    "      Id.run (forIn os init (fun o r => pure (ForInStep.yield (r ++ [render o fieldKey]))))\n"
    "        = init ++ os.map (fun o => render o fieldKey) := by\n"
    "    intro os\n"
    "    induction os with\n"
    "    | nil => intro init; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl\n"
    "    | cons a as ih =>\n"
    "        intro init; rw [List.forIn_cons]\n"
    "        simp only [Id.run, bind] at ih ⊢; rw [ih]; simp\n"
    "  refine ⟨?_, rfl⟩\n"
    "  show (implementation_get render defaultRender objects fieldKey hasMore).results = _\n"
    "  unfold implementation_get\n"
    "  simp only [Id.run, bind]\n"
    "  have := helper objects []\n"
    "  simp only [Id.run] at this\n"
    "  rw [this]\n"
    "  rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


def _impl(sig_default, body):
    """A full impl block with the given defaultRender binder name and body lines."""
    return (
        "def implementation_get {Obj E : Type}\n"
        f"    (render {sig_default} : Obj → String → E)\n"
        "    (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do\n"
        + body
    )


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-let-bound-entry: structurally-DIFFERENT but behaviourally identical. The
# per-item rendering is bound to a local `e` before the append; every other line
# (and the result) is unchanged, so the output equals the frozen impl's on every
# input. The frozen `theorem correct_get` statement is kept byte-identical AND the
# frozen proof body still closes (the `let` binding is definitionally transparent).
# No reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG. VERIFIED to
# build (proof closes) before shipping.
_POS_LET = _swap(
    _BASE, _IMPL,
    _impl("_defaultRender",
          "  let mut results : List E := []\n"
          "  for o in objects do\n"
          "    let e := render o fieldKey\n"
          "    results := results ++ [e]\n"
          "  return { results := results, more := hasMore }"),
)

# pos-pure-map: a structurally different CORRECT impl written as a pure record
# literal (no `Id.run do` monad, no `for`/`mut` loop), the results built directly by
# `objects.map`. Semantics identical on every input. The theorem STATEMENT is
# byte-identical; its proof is reproven honestly (`exact ⟨rfl, rfl⟩`) inside
# proof-start/proof-end — no new axiom/lemma/sorry, just the cheapest tactic for the
# new shape. If it FAILS => SPEC-TOO-STRONG (the postcondition is bound to the
# monadic impl shape). VERIFIED to build before shipping.
_POS_PURE = _swap(
    _swap(
        _BASE, _IMPL,
        "def implementation_get {Obj E : Type}\n"
        "    (render _defaultRender : Obj → String → E)\n"
        "    (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E :=\n"
        "  { results := objects.map (fun o => render o fieldKey), more := hasMore }",
    ),
    _PROOF,
    "  intro render defaultRender objects fieldKey hasMore\n"
    "  unfold problem_spec_get implementation_get\n"
    "  exact ⟨rfl, rfl⟩",
)


# ===========================================================================
# ADMISSIBILITY (audit-added) — the obligation must be SATISFIABLE at a concrete,
# normal-use-shaped input, not merely provable in the abstract. The frozen theorem
# has no precondition hypothesis, so there is no Requires to attack as nagini's
# case did; the analogue on this total carrier is to discharge the spec predicate
# BY EVALUATION at a ground point of the F2P's shape — two selected objects, a
# NON-EMPTY field key, the has-more flag false — with the abstract carriers
# instantiated (Obj := Nat, E := Nat) and BOTH rendering parameters given concrete
# and mutually DISTINCT values. The frozen impl is kept verbatim and the frozen
# obligation is closed verbatim after the `have`, so verification is attributable
# to the ground instance and nothing else. If the spec predicate were
# unsatisfiable at that shape (a clause contradictory once instantiated, an
# over-constrained conjunction) the `decide` would fail => PRECOND-TOO-STRONG.
# Nothing is assumed: no new declaration, no axiom/lemma/sorry, statement
# byte-identical. VERIFIED to build before shipping.
_ADM_F2P = _swap(
    _BASE, _PROOF,
    "  -- Discharge the postcondition BY EVALUATION at one concrete input of the "
    "shape\n"
    "  -- normal use takes (two selected objects, a non-empty field key, the "
    "has-more\n"
    "  -- flag reported false), with the abstract carriers and BOTH rendering "
    "steps\n"
    "  -- instantiated at distinct concrete functions — so the obligation is "
    "shown\n"
    "  -- satisfiable at a ground point, not only in the abstract. Then close the\n"
    "  -- frozen obligation verbatim.\n"
    "  have _f2p_shaped :\n"
    "      problem_spec_get (fun (o : Nat) (k : String) => o + k.length) [1, 2] "
    "\"pk\" false\n"
    "        (implementation_get (fun (o : Nat) (k : String) => o + k.length)\n"
    "          (fun (o : Nat) (_ : String) => o) [1, 2] \"pk\" false) := by\n"
    "    unfold problem_spec_get implementation_get\n"
    "    simp only [Id.run, List.forIn_cons, List.forIn_nil, bind, pure]\n"
    "    decide\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-dispatch-drop: the DEFERRAL DEFEAT / dispatch-drop — routes the loop through
# `defaultRender` (the hardwired inline entry) instead of the dispatched `render`.
# This is exactly the PRE-PATCH bug: correct ONLY for a responder whose conversion
# equals the default, wrong for any override. Attacks clause C1.
_RIV_DISPATCH = _swap(
    _BASE, _IMPL,
    _impl("defaultRender",
          "  let mut results : List E := []\n"
          "  for o in objects do\n"
          "    results := results ++ [defaultRender o fieldKey]\n"
          "  return { results := results, more := hasMore }"),
)

# weak-firstrow-default: PARTIAL-DOMAIN. Defers to `render` for every object EXCEPT
# the first, where it inlines `defaultRender`. Correct on all but index 0. Attacks
# clause C1 at the first element.
_RIV_FIRSTROW = _swap(
    _BASE, _IMPL,
    _impl("defaultRender",
          "  let mut results : List E := []\n"
          "  let mut i : Nat := 0\n"
          "  for o in objects do\n"
          "    if i = 0 then\n"
          "      results := results ++ [defaultRender o fieldKey]\n"
          "    else\n"
          "      results := results ++ [render o fieldKey]\n"
          "    i := i + 1\n"
          "  return { results := results, more := hasMore }"),
)

# weak-skip-last: LENGTH / ALIGNMENT. Drops the final selected object
# (`objects.dropLast`), so `results` is one entry short. Attacks clause C1 (the
# results list no longer equals the full `objects.map …`).
_RIV_SKIPLAST = _swap(
    _BASE, _IMPL,
    _impl("_defaultRender",
          "  let mut results : List E := []\n"
          "  for o in objects.dropLast do\n"
          "    results := results ++ [render o fieldKey]\n"
          "  return { results := results, more := hasMore }"),
)

# weak-wrong-fieldkey: routes the loop through the DISPATCHED `render` (so the
# dispatch is honoured) but threads the WRONG argument — a constant empty string
# instead of the supplied `fieldKey`. Attacks clause C1 via the `fieldKey` binder:
# a rival that renders each object with the wrong field key.
_RIV_KEY = _swap(
    _BASE, _IMPL,
    _impl("_defaultRender",
          "  let mut results : List E := []\n"
          "  for o in objects do\n"
          "    results := results ++ [render o \"\"]\n"
          "  return { results := results, more := hasMore }"),
)

# weak-reverse-order: ORDER. Routes every entry through the DISPATCHED `render` with
# the RIGHT key, and emits exactly one entry per selected object — so the dispatch,
# the argument threading and the multiplicity are all honoured — but walks the
# selection in reverse, so the entries come out in the wrong ORDER. Attacks the
# "in the same order as the selected objects" half of clause C1, which the other
# rivals leave undemonstrated: skip-last attacks length, dispatch-drop/first-row
# attack which function is applied, wrong-fieldkey attacks its argument, and none
# of them varies the PERMUTATION. Added by audit (order was a claimed but never
# exercised clause).
_RIV_REVERSE = _swap(
    _BASE, _IMPL,
    _impl("_defaultRender",
          "  let mut results : List E := []\n"
          "  for o in objects.reverse do\n"
          "    results := results ++ [render o fieldKey]\n"
          "  return { results := results, more := hasMore }"),
)

# weak-duplicate-entry: MULTIPLICITY / ADDED ENTRY. The mirror image of
# weak-skip-last: instead of dropping an entry it ADDS one, appending the (correct,
# dispatched, correctly-keyed) rendering TWICE per selected object. Attacks the "no
# entry may be added" half of clause C1 — every existing length rival is short, so
# a spec that only bounded the results list from below would pass them all and fail
# only here. Added by audit.
_RIV_DUPLICATE = _swap(
    _BASE, _IMPL,
    _impl("_defaultRender",
          "  let mut results : List E := []\n"
          "  for o in objects do\n"
          "    results := results ++ [render o fieldKey, render o fieldKey]\n"
          "  return { results := results, more := hasMore }"),
)

# weak-flag-constant: builds the results list correctly (clause C1 holds) but
# hardwires the has-more flag to `true` instead of reporting `hasMore` verbatim.
# Attacks clause C2 via the `hasMore` binder — the second independent top-level
# clause of the postcondition.
_RIV_FLAG = _swap(
    _BASE, _IMPL,
    _impl("_defaultRender",
          "  let mut results : List E := []\n"
          "  for o in objects do\n"
          "    results := results ++ [render o fieldKey]\n"
          "  return { results := results, more := true }"),
)


# --- witnesses --------------------------------------------------------------------
# Each refutation states `¬ problem_spec_get render objects fieldKey hasMore
# (implementation_get render defaultRender objects fieldKey hasMore)` at a CONCRETE
# instantiation. The abstract carriers are instantiated Obj := Nat, E := Nat, and
# the (universally-quantified) `render`/`defaultRender` by concrete functions. The
# `render` binder (the spec's core function binder) is VARIED across the reject
# witnesses — six distinct renderings over seven cases — so no rival that mishandled
# one particular rendering could slip through, and the coverage check flags a `render`
# pinned across all witnesses. (`weak-firstrow-default` and `weak-reverse-order` share
# the rendering `o * 2`; they discriminate at different points regardless — the former
# needs `defaultRender` to differ from `render`, the latter needs two objects whose
# renderings are distinct — and injectivity, not novelty, is what each requires of it.)
# Where a rival's defect is a
# wrong dispatch, `defaultRender` is chosen to differ from `render` everywhere; where
# the argument (`fieldKey`) is attacked, `render` is chosen to depend on the key.
# `simp only [Id.run, List.forIn_*, List.dropLast, bind, pure]` reduces the loop to a
# concrete list and `decide` closes the (dis)equality. SEEN to discriminate both
# ways: each ELABORATES against its rival and FAILS on the frozen solution. Binders
# are jointly satisfiable (no hypotheses at all — pure literal instantiation).
_D0 = "(fun (_ : Nat) (_ : String) => 0)"


def _wit(render_fn, default_fn, objects, key, more, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_get {render_fn} {objects} {key} {more}\n"
        f"    (implementation_get {render_fn} {default_fn} {objects} {key} {more}) := by\n"
        f"  unfold problem_spec_get implementation_get\n"
        f"  simp only [Id.run, List.forIn_cons, List.forIn_nil, List.dropLast, bind, pure]\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-let-bound-entry",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": (
            "structurally-different but CORRECT impl: the per-item rendering is bound "
            "to a local `e` before the append, keeping the loop and the result, so the "
            "output equals the frozen impl's on every input. The theorem statement is "
            "byte-identical and the FROZEN proof body still closes (the let binding is "
            "definitionally transparent) — a faithful restructure with no reproof and no "
            "new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to one syntactic impl shape). Ports nagini pos-control-localvar."
        ),
    },
    {
        "id": "pos-pure-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure record literal (no "
            "`Id.run do`, no `for`/`mut` loop), the results built directly by "
            "`objects.map (render · fieldKey)`. Semantics identical on every input. The "
            "theorem STATEMENT is byte-identical; its proof is reproven honestly with "
            "`exact ⟨rfl, rfl⟩` — no new axiom/lemma/sorry, just the cheapest tactic for "
            "the new shape. If it FAILS => SPEC-TOO-STRONG (the postcondition is bound to "
            "the monadic impl shape rather than the behaviour)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-f2p-shaped-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_F2P,
        "rationale": (
            "the obligation must be SATISFIABLE at a concrete input of the shape "
            "normal use takes, not merely provable in the abstract. The frozen "
            "theorem carries no precondition hypothesis, so nagini's Requires-"
            "admission probe has no binder to attack here; the analogue on this "
            "total carrier is to discharge `problem_spec_get` BY EVALUATION at a "
            "ground point — two selected objects, a NON-EMPTY field key, the "
            "has-more flag false, the abstract carriers instantiated (Obj := Nat, "
            "E := Nat) and BOTH rendering parameters given distinct concrete "
            "values — as a `have`, before closing the frozen obligation verbatim. "
            "The frozen impl is unchanged, so verification is attributable to the "
            "ground instance alone. If the spec predicate were unsatisfiable at "
            "that shape (a clause contradictory once instantiated, or an over-"
            "constrained conjunction) the `decide` would fail => PRECOND-TOO-"
            "STRONG. Audit-added: the port recorded this whole lane as N/A on the "
            "reason 'the frozen obligation has no precondition', which is not a "
            "demonstration that the lane is vacuous."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-dispatch-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DISPATCH,
        "refinement": (
            "routing every entry through the hardwired inline conversion instead of the "
            "dispatched, subclass-overridable step is EXACTLY the pre-patch behaviour. Its "
            "faithful real patch is the unchanged repo, which IGNORES a subclass override; "
            "the F2P test overrides the per-item conversion to add an extra field and "
            "asserts every result entry carries it, so a dispatch-dropping impl fails it. "
            "A verifying rival is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause C1. The spec demands `results = objects.map (render · "
            "fieldKey)`, but the rival produces `objects.map (defaultRender · fieldKey)`. "
            "Witness instantiates render and defaultRender to differ everywhere on a "
            "single-object list; the two result lists differ. If it VERIFIES => "
            "SPEC-TOO-WEAK (the dispatch is unpinned)."
        ),
        # render 7 "a" = 8; defaultRender 7 "a" = 9 -> lists [8] vs [9] differ.
        "witness": _wit("(fun (o : Nat) (k : String) => o + k.length)",
                        "(fun (o : Nat) (k : String) => o + k.length + 1)",
                        "[7]", "\"a\"", "true",
                        "dispatch-drop: gold renders via `render`, rival via `defaultRender`"),
    },
    {
        "id": "weak-firstrow-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRSTROW,
        "refinement": (
            "a faithful patch that special-cases the FIRST selected object to the inline "
            "default but defers the rest would, for the first entry, ignore the subclass "
            "override. The F2P orders the results and asserts the extra field on EVERY "
            "entry including the first; the first entry would lack it => F2P fails. A "
            "genuine PARTIAL-DOMAIN break a byte-fuzzer never builds. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 at index 0: the inlined `defaultRender` entry for the "
            "first object is not `render` of it, so the mapped-results equality fails at "
            "the head. Witness uses a TWO-object list (so the tail matches gold and only "
            "the head discriminates), distinguishing this near-miss from weak-dispatch-drop "
            "(which is wrong at every index). If it VERIFIES => SPEC-TOO-WEAK on the first "
            "element."
        ),
        # objects [3,9]: head render (3*2)=6 vs default (3*2+5)=11 -> [11,18] vs [6,18].
        "witness": _wit("(fun (o : Nat) (_ : String) => o * 2)",
                        "(fun (o : Nat) (_ : String) => o * 2 + 5)",
                        "[3, 9]", "\"\"", "false",
                        "first-row default: head via `defaultRender`, tail via `render`; "
                        "gold renders all via `render`"),
    },
    {
        "id": "weak-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SKIPLAST,
        "refinement": (
            "a builder that drops the final selected object returns one fewer entry than "
            "there are objects. The F2P asserts the results list equals one entry per "
            "selected object (two objects); a missing last entry => the asserted list "
            "mismatches => F2P fails. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (length/alignment): `objects.dropLast .map …` is shorter "
            "than `objects.map …`, so the results equality fails. Witness uses a "
            "single-object list, where dropLast yields the empty list — [] vs [render …]. "
            "If it VERIFIES => SPEC-TOO-WEAK (the one-entry-per-object alignment is unpinned)."
        ),
        # objects [5]: gold [render 5 ""]=[105], rival [] -> differ.
        "witness": _wit("(fun (o : Nat) (_ : String) => o + 100)", _D0,
                        "[5]", "\"\"", "true",
                        "skip-last: rival drops the only object; gold keeps it"),
    },
    {
        "id": "weak-wrong-fieldkey",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KEY,
        "refinement": (
            "a faithful patch that HONOURS the dispatch but passes the wrong lookup key to "
            "the per-item conversion (e.g. a constant instead of the request's to-field "
            "name) emits the wrong id for every entry. The F2P asserts each entry's id "
            "derives from the correct field; a wrong key => the asserted dict mismatches => "
            "F2P fails. Does NOT resolve. Attacks the ARGUMENT of the opaque render (route "
            "3), separable because render depends on the key."
        ),
        "rationale": (
            "REJECTED by clause C1 via the `fieldKey` binder: the spec demands `render o "
            "fieldKey`, but the rival computes `render o \"\"`. Witness varies the "
            "`fieldKey` binder to a NON-empty string on a single object, so the two renders "
            "differ. This binder has no nagini build_results counterpart. If it VERIFIES => "
            "SPEC-TOO-WEAK (the field key is not threaded)."
        ),
        # fieldKey "a": render 0 "a" = 3 vs render 0 "" = 0 -> [3] vs [0].
        "witness": _wit("(fun (o : Nat) (k : String) => o + k.length * 3)", _D0,
                        "[0]", "\"a\"", "false",
                        "wrong field key: rival renders with the empty key, gold with `fieldKey`"),
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE,
        "refinement": (
            "a faithful patch that assembles the entry list by walking the selection "
            "backwards (or prepends each entry to the accumulator instead of appending) "
            "emits a correctly-rendered entry per object but in reversed order. The F2P "
            "asserts the response's results list equals the entries of the two selected "
            "objects taken in a SPECIFIC order; a reversed list is a list mismatch => F2P "
            "fails. Does NOT resolve. An ordering break is a classic accumulator slip and "
            "no byte-fuzzer produces it."
        ),
        "rationale": (
            "REJECTED by clause C1's ORDER half: `objects.reverse.map (render · fieldKey)` "
            "is a PERMUTATION of `objects.map (render · fieldKey)`, so the two lists agree "
            "as multisets and differ as lists. Witness uses a two-object list whose two "
            "renderings are distinct (so the reversal is observable — on a one-object list "
            "or on constant `render` it would not be) and leaves the dispatch, the key and "
            "the flag correct, isolating order. If it VERIFIES => SPEC-TOO-WEAK (the spec "
            "pins only the multiset of entries, not their sequence). Audit-added: order was "
            "claimed by C1 but exercised by no case."
        ),
        # objects [1,4]: gold [2,8], rival [8,2] -> differ as lists, agree as multisets.
        "witness": _wit("(fun (o : Nat) (_ : String) => o * 2)", _D0,
                        "[1, 4]", "\"\"", "true",
                        "reverse order: rival emits the same entries in reversed order; "
                        "gold emits them in selection order"),
    },
    {
        "id": "weak-duplicate-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DUPLICATE,
        "refinement": (
            "a faithful patch that appends the per-item entry twice per selected object "
            "(a duplicated append, or an inner loop that runs one iteration too many) "
            "returns twice as many entries as there are objects. The F2P asserts the "
            "results list equals exactly one entry per selected object; a doubled list "
            "mismatches => F2P fails. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (multiplicity): the rival's results list has length "
            "`2 * objects.length`, not `objects.length`, so the mapped-results equality "
            "fails. The mirror of weak-skip-last — that rival is one entry SHORT, this one "
            "is one entry LONG — so together they pin the length from both sides. Witness "
            "uses a single-object list: gold [render o fieldKey] vs rival the same entry "
            "twice. If it VERIFIES => SPEC-TOO-WEAK (the spec bounds the results list only "
            "from below). Audit-added: no existing rival added an entry."
        ),
        # objects [1]: gold [2], rival [2,2] -> differ in length.
        "witness": _wit("(fun (o : Nat) (_ : String) => o + 1)", _D0,
                        "[1]", "\"\"", "true",
                        "duplicate entry: rival emits each rendering twice; gold once"),
    },
    {
        "id": "weak-flag-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FLAG,
        "refinement": (
            "a faithful patch that hardwires the has-more pagination flag to true (rather "
            "than reporting the paginator's actual has-next) mislabels pagination on the "
            "final page. Any test asserting `pagination.more == false` on a single-page "
            "response fails. Does NOT resolve. Attacks the second observable component."
        ),
        "rationale": (
            "REJECTED by clause C2 (the flag) via the `hasMore` binder: the spec demands "
            "`result.more = hasMore`, but the rival returns the constant `true`. Witness "
            "sets the `hasMore` binder to false (an empty object list isolates C2 — the "
            "results clause holds trivially), so the flags differ. This is the only rival "
            "attacking C2. If it VERIFIES => SPEC-TOO-WEAK (the flag is unpinned)."
        ),
        # hasMore false, rival more=true -> false = true is False. objects=[] isolates C2.
        "witness": _wit("(fun (o : Nat) (_ : String) => o + 42)", _D0,
                        "[]", "\"\"", "false",
                        "flag constant: rival reports more=true; gold reports hasMore=false"),
    },
]


# No @ContractOnly axioms and no opaque callees: `render`/`defaultRender` are
# universally-quantified function parameters with no consumed axiom, and the whole
# behaviour (map + flag) is modeled DEEPLY over transparent carriers. The axiom lane
# is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
