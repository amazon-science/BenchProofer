# properties.py — G-PBT falsification battery for django__django-7530 (lean lane).
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
#   implementation_consistency_pairs : List App → List (String × String)
#   The full enumeration of (application label, model name) pairs contributed by a
#   list of applications. The single postcondition pins the result to be EXACTLY
#   `pairsSpec apps`, a total, transparent front-recursive fold that, for each
#   application in turn, emits each of THAT application's OWN models tagged with
#   THAT application's label, in application order and then model order. The
#   load-bearing content, three independent aspects of that one equality:
#     (A) ATTRIBUTION — each model is paired ONLY with the application that owns it
#         (no foreign-application model offered under another label, and none of an
#         application's own models omitted);
#     (B) IDENTITY — the label and the model name of each pair are exactly the
#         carrier's own `App.label` / `App.models` element (not a perturbed name);
#     (C) ORDER — application order first, then model order within each application.
#   The oracle `pairsSpec` is a total transparent fold over the carrier (no opaque
#   callee, no answer-key), so `decide` computes it at any literal input — witnesses
#   need no conditioning on the carrier.
#
# CARRIER NOTE: the nagini sibling abstracted a SINGLE-group filter over two aligned
# `List[int]` roster streams behind fractional read permission — `gathered(owner,
# member, target)` keeps `member[k]` iff `owner[k] == target`. This backend models
# the WHOLE pairing across every application at once (`pairsSpec` over `List App`),
# because the modeled behavior is the full `(app_label, model_name)` enumeration the
# consistency pre-check feeds `allow_migrate`. The nagini rivals that attack the
# per-position attribution guard (drop it → gather everything; invert it → gather the
# complement; perturb the gathered identity) have direct counterparts here; the
# ordering aspect the lean spec makes explicit gets its own rivals. Carrier narrowing
# is expected — this is not a case-count port (see 'assessment').
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's #1 class: `owner` / `member` were Acc(.,1/2)
#     read-only roster streams, and the rivals wrote back into them to satisfy the
#     postcondition vacuously). Lean is referentially transparent — no aliasing, no
#     fractional permission — so a "store into a read-only input" rival is not
#     expressible and the whole lane (frame-mutate-owner, frame-mutate-member) is
#     VACUOUS here. See 'assessment'.
#   * DIVERGENCE / non-termination. This bundle sets no
#     `set_option loom.semantics.termination`, and the obligation is over a total
#     Lean `def`, so a non-terminating impl is only expressible as a `partial def`
#     (or an `unsafe`/`extern` term), whose body the kernel refuses to unfold. A
#     `decide` witness against such a rival is then STUCK rather than refuting —
#     MEASURED, not assumed: a `partial def spinForever apps := spinForever apps`
#     rival builds exit 1 (so the gate would record `rejected`), but its witness
#     build also exits 1 with "reduction got stuck at the `Decidable` instance
#     (Id.run (spinForever …)).hasDecEq", i.e. `witness-undecided`. So the class is
#     not shippable as a reject case here — recorded as a KNOWN HOLE (the diverging
#     impl is neither provably rejected by the spec nor refutable by a witness on
#     this carrier), not as a vacuous class. See 'assessment'.
#
# LANE THAT DOES PORT AND IS NOW CARRIED (was previously dropped as "N/A"):
#   * ADMISSIBILITY — see `admiss-ground-registry` below. The earlier reading, that
#     an obligation with no precondition hypothesis has nothing that could be
#     PRECOND-TOO-STRONG, mis-states the lane: on a TOTAL carrier the analogue of a
#     too-strong precondition is the obligation being UNSATISFIABLE at an
#     F2P-shaped input, and a positive that discharges the spec predicate at that
#     concrete input by evaluation — as a `have`, before closing the frozen
#     obligation verbatim — tests it directly.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. The pairing
#     is modeled DEEPLY over the carrier (`appPairs` / `pairsSpec`), so there is no
#     consumed axiom anyway.
#
# See ``assessment`` at the bottom of this file for the per-nagini-case disposition
# of every dropped case, including the two that DO port and are now carried.
from pathlib import Path

INSTANCE = "django__django-7530"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). ------------------------------------------------------------

# The frozen impl body after `:= Id.run do` (the accumulator + nested loop). Used by
# rivals that reshape the whole body and by the direct/flatMap positives.
_IMPL_TAIL = (
    "  let mut acc : List (String × String) := []\n"
    "  for a in apps do\n"
    "    for m in a.models do\n"
    "      acc := acc ++ [(a.label, m)]\n"
    "  return acc"
)
assert _BASE.count(_IMPL_TAIL) == 1, "impl tail anchor drifted"

# The pair the inner loop appends (attacked by the identity rivals).
_PAIR = "      acc := acc ++ [(a.label, m)]\n"
assert _BASE.count(_PAIR) == 1, "pair anchor drifted"

# The inner and outer loop headers (attacked by the order rivals).
_INNER = "    for m in a.models do\n"
_OUTER = "  for a in apps do\n"
assert _BASE.count(_INNER) == 1, "inner-loop anchor drifted"
assert _BASE.count(_OUTER) == 1, "outer-loop anchor drifted"

# The frozen proof body (tactic lines inside proof-start/proof-end).
_PROOF = (
    "  intro apps\n"
    "  unfold problem_spec_consistency_pairs implementation_consistency_pairs\n"
    "  have h := outer_helper_consistency_pairs apps []\n"
    "  simp only [Id.run, bind_pure, List.nil_append] at h ⊢\n"
    "  exact h"
)
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-flatmap: a structurally-DIFFERENT but CORRECT impl. The imperative nested-loop
# accumulator is replaced by a single pure `apps.flatMap appPairs` — the same
# front-recursive fold `pairsSpec` denotes, expressed as a library combinator instead
# of a mutable loop. This is the shape a faithful patch could equally take (a
# comprehension rather than an accumulating loop). The frozen loop-reasoning proof no
# longer applies, so the proof body is honestly re-closed by a short induction (NO new
# axiom/lemma/sorry; the `theorem correct_consistency_pairs` STATEMENT is byte-
# identical). If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to the loop form).
_POS_FLATMAP = _swap(
    _swap(_BASE, _IMPL_TAIL, "  apps.flatMap appPairs"),
    _PROOF,
    "  intro apps\n"
    "  unfold problem_spec_consistency_pairs implementation_consistency_pairs\n"
    "  simp only [Id.run]\n"
    "  induction apps with\n"
    "  | nil => rfl\n"
    "  | cons a rest ih => rw [List.flatMap_cons, pairsSpec, ih]",
)

# pos-direct: the cheapest HONEST impl. The postcondition oracle `pairsSpec` is
# GROUNDED in the argument (a total transparent fold over the carrier), so directly
# returning it is a fully-grounded correct implementation, not an ungrounded-oracle
# echo — there is no WRONG constant/echo to build here (a wrong result fails the
# postcondition). The proof collapses to `rfl` after unfolding. MUST verify (the
# postcondition is literally `result = pairsSpec apps`); else SPEC-TOO-STRONG. Also
# shows the spec is not echo-vulnerable: any WRONG constant fails the postcondition.
_POS_DIRECT = _swap(
    _swap(_BASE, _IMPL_TAIL, "  pairsSpec apps"),
    _PROOF,
    "  intro apps\n"
    "  unfold problem_spec_consistency_pairs implementation_consistency_pairs\n"
    "  rfl",
)

# ===========================================================================
# ADMISSIBILITY — the obligation must be SATISFIABLE (non-vacuous) at a concrete
# F2P-shaped input. On this TOTAL carrier the obligation carries no precondition
# hypothesis, so the nagini precondition-admission self-call re-expresses as:
# discharge the spec predicate BY EVALUATION at a registry of the F2P shape (two
# applications with DISJOINT model sets, one owning two models — the multi-app
# configuration the modeled enumeration is fed) as a `have`, then close the frozen
# obligation verbatim. Nothing is assumed: no new declaration, no axiom, the
# `theorem correct_consistency_pairs` statement is byte-identical, and the frozen
# tactic body is kept intact after the prepended `have`. If the `have` fails, the
# obligation is unsatisfiable at a normal input (the total-carrier analogue of
# PRECOND-TOO-STRONG) => the spec is vacuous exactly where the behaviour lives.
_ADMISS_LIT = (
    '[{ label := "alpha", models := ["AlphaOne", "AlphaTwo"] }, '
    '{ label := "beta", models := ["BetaOne"] }]'
)
_POS_ADMISS = _swap(
    _BASE, _PROOF,
    f"  have _ground : problem_spec_consistency_pairs {_ADMISS_LIT}\n"
    f"      (implementation_consistency_pairs {_ADMISS_LIT}) := by\n"
    "    unfold problem_spec_consistency_pairs implementation_consistency_pairs\n"
    "    decide\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness that
# ELABORATES against the rival and FAILS on the frozen solution. The frozen proof
# body is left in place (it will not close for the reshaped impl, but the gate reads
# the witness, checked in a file with the obligation removed).
# ===========================================================================

# THE BUG ITSELF (ports nagini rival-prepatch-allmembers / model_prepatch.py). The
# per-application attribution is dropped: instead of pairing each application with
# only ITS OWN models, the whole project's model list is gathered first and every
# application label is paired with EVERY model (the full cross-product). This is the
# pre-patch behaviour verbatim (Solution_prepatch.lean's impl). Attacks clause (A),
# attribution.
_RIV_CROSSPRODUCT = _swap(
    _BASE, _IMPL_TAIL,
    "  let mut allModels : List String := []\n"
    "  for a in apps do\n"
    "    allModels := allModels ++ a.models\n"
    "  let mut acc : List (String × String) := []\n"
    "  for a in apps do\n"
    "    for m in allModels do\n"
    "      acc := acc ++ [(a.label, m)]\n"
    "  return acc",
)

# COMPLEMENT (ports nagini rival-complement-filter). The attribution polarity is
# INVERTED: each application is paired with the models it does NOT own (the foreign
# models) instead of its own. Attacks clause (A), attribution polarity.
_RIV_COMPLEMENT = _swap(
    _BASE, _IMPL_TAIL,
    "  let allModels : List String := apps.flatMap (fun a => a.models)\n"
    "  let mut acc : List (String × String) := []\n"
    "  for a in apps do\n"
    "    for m in allModels do\n"
    "      if m ∉ a.models then\n"
    "        acc := acc ++ [(a.label, m)]\n"
    "  return acc",
)

# WRONG MODEL IDENTITY (ports nagini rival-wrong-member-value / `m + 1`). The correct
# application/model SELECTION is kept, but each gathered model name is PERTURBED
# (a marker character appended). Attacks clause (B), the model-name component.
_RIV_WRONG_MODEL = _swap(
    _BASE, _PAIR,
    '      acc := acc ++ [(a.label, m ++ "!")]\n',
)

# WRONG LABEL IDENTITY (a lean-transparent attribution rival with no direct nagini
# twin — nagini's single-group carrier had no label component to perturb). The pair's
# FIRST component is set to the model name instead of the owning application's label,
# so each model is attributed to itself rather than to its application. Attacks
# clause (B), the label component (and clause (A) attribution).
_RIV_WRONG_LABEL = _swap(
    _BASE, _PAIR,
    "      acc := acc ++ [(m, m)]\n",
)

# REVERSED MODEL ORDER. Correct selection and identities, but each application's own
# models are emitted in REVERSE order. Attacks clause (C), model order (the "then
# model order" the spec pins).
_RIV_REV_MODELS = _swap(_BASE, _INNER, "    for m in a.models.reverse do\n")

# PARTIAL-DOMAIN (ports nagini rival-partial-first, which the first draft of this
# battery dropped without recording it — see 'assessment'). Only the FIRST of each
# application's own models is emitted. Every pair it produces is correctly
# attributed and correctly ordered, so it is OBSERVATIONALLY CORRECT on the whole
# sub-domain where no application owns more than one model, and diverges only on
# the >=2-models-per-application sub-domain. This is the domain-incompleteness
# shape nagini probed (correct on a sub-domain, wrong off it) rather than a
# uniformly-wrong rival: the other five rivals are all wrong at their first
# emitted pair, so none of them tests whether the spec constrains the enumeration
# past a single model per application.
_RIV_TAKE_FIRST = _swap(_BASE, _INNER, "    for m in (a.models.take 1) do\n")

# TRANSPOSED PAIR. Both components of each pair are the CORRECT strings, and the
# selection and both orderings are correct — only the pair's ORIENTATION is
# swapped, so the model name is offered where the application label belongs and
# vice versa. Distinct from the wrong-label rival, which destroys a component
# (`(m, m)` loses the label entirely); here the component multiset is exactly
# right, which is the closest near-miss the carrier admits.
_RIV_TRANSPOSE = _swap(_BASE, _PAIR, "      acc := acc ++ [(m, a.label)]\n")

# REVERSED APPLICATION ORDER. Correct selection and identities, but the applications
# are visited in REVERSE order. Attacks clause (C), application order (the "in
# application order" the spec pins) — a DIFFERENT binder than the model-order rival.
_RIV_REV_APPS = _swap(_BASE, _OUTER, "  for a in apps.reverse do\n")


def _wit(apps_lit, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal input, closed by `decide`. `apps_lit` is the Lean `List App` literal.
    Elaborates against a rival that diverges from `pairsSpec` there, and fails on gold
    (which satisfies the spec at every input)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_consistency_pairs {apps_lit}\n"
        f"    (implementation_consistency_pairs {apps_lit}) := by\n"
        f"  unfold problem_spec_consistency_pairs implementation_consistency_pairs\n"
        f"  decide"
    )


# Concrete carrier literals used by the witnesses (chosen to distinguish each rival):
#   _TWO_DISJOINT — two applications with DISJOINT single-model sets: the config that
#     exposes attribution bugs (a model of one app must never appear under the other).
#   _ONE_ONE      — one application, one model: the minimal identity probe.
#   _ONE_TWO      — one application, two DISTINCT models: needed to see an order flip.
_TWO_DISJOINT = '[{ label := "a", models := ["x"] }, { label := "b", models := ["y"] }]'
_ONE_ONE = '[{ label := "a", models := ["x"] }]'
_ONE_TWO = '[{ label := "a", models := ["x", "y"] }]'


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-flatmap",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLATMAP,
        "rationale": (
            "structurally-different but CORRECT impl: the imperative nested-loop "
            "accumulator is replaced by the pure combinator `apps.flatMap appPairs`, "
            "the same front-recursive fold `pairsSpec` denotes. Only the executable "
            "form changes; the result is identical on every input. The frozen "
            "`theorem correct_consistency_pairs` STATEMENT is kept byte-identical and "
            "the proof body is honestly re-closed by a short structural induction (no "
            "new axiom/lemma/sorry). If it FAILS => SPEC-TOO-STRONG (postcondition "
            "over-fit to the accumulating-loop form)."
        ),
    },
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the postcondition oracle `pairsSpec` is GROUNDED in the argument (a total "
            "transparent fold over the carrier), so `implementation := pairsSpec apps` "
            "is the honest cheapest CORRECT impl, not an ungrounded echo; the proof "
            "collapses to `rfl`. Must verify (postcondition is literally result = "
            "pairsSpec apps); else SPEC-TOO-STRONG. Also shows the spec is not echo-"
            "vulnerable: any WRONG constant fails the postcondition."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-ground-registry",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "the obligation must be SATISFIABLE at a concrete F2P-shaped input, not "
            "merely closable in the abstract. The spec predicate is discharged BY "
            "EVALUATION (`decide`) at a registry of the shape the modeled "
            "enumeration is actually fed — two applications with DISJOINT model "
            "sets, the first owning TWO models — prepended as a `have` before the "
            "frozen tactic body runs verbatim. Statement byte-identical, no new "
            "declaration/axiom/sorry. On this total carrier the obligation carries "
            "no precondition hypothesis, so this is the analogue of nagini's "
            "admiss-self-call: if the ground instance does NOT discharge, the "
            "obligation is unsatisfiable exactly where the behaviour lives (the "
            "total-carrier form of PRECOND-TOO-STRONG) and the whole battery's "
            "rejections would be attesting to a vacuous spec."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "rival-crossproduct-allmodels",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CROSSPRODUCT,
        "refinement": (
            "this is the PRE-PATCH behaviour verbatim (Solution_prepatch.lean's impl): "
            "the per-application attribution is dropped and every application label is "
            "paired with the WHOLE project's model list — exactly the pre-change "
            "enumeration that pairs each label with all models rather than its own. Its "
            "faithful real patch is the unchanged pre-change enumeration, which feeds "
            "the migration-consistency pre-check (application, model) pairs for models "
            "that do not belong to that application — precisely what FAILS the F2P test "
            "— so it would NOT resolve. A verifying rival here is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "the DISCRIMINATING bug this change fixes. REJECTED by the postcondition, "
            "which pins the result to `pairsSpec apps` (each model paired ONLY with its "
            "own application); the cross-product includes foreign-application pairs on "
            "any registry with two applications owning disjoint models. Attacks clause "
            "(A), attribution; varies the `apps`/`App.models` binders. If it VERIFIES "
            "=> SPEC-TOO-WEAK (admits the very bug)."
        ),
        # two disjoint apps: gold => [(a,x),(b,y)]; rival => full 2×2 cross-product.
        "witness": _wit(_TWO_DISJOINT,
                        "cross-product: gold pairs each label with its own model, "
                        "rival adds the foreign-application pairs"),
    },
    {
        "id": "rival-complement-attribution",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_COMPLEMENT,
        "refinement": (
            "the attribution polarity is INVERTED: each application is paired with the "
            "models it does NOT own. Its faithful real patch would enumerate every "
            "OTHER application's models under each label — the exact opposite of the "
            "fix — feeding the consistency pre-check none of the correct pairs and only "
            "foreign ones; it would NOT resolve. Verify-does-not-imply-resolve."
        ),
        "rationale": (
            "attribution-inversion rival. REJECTED by the postcondition — `pairsSpec` "
            "keeps exactly the owning-application pairs, and the complement disagrees on "
            "any registry with two applications owning disjoint models. Attacks clause "
            "(A), attribution polarity; varies the `apps`/`App.models` binders. If it "
            "VERIFIES => SPEC-TOO-WEAK (attribution polarity unconstrained)."
        ),
        # two disjoint apps: gold => [(a,x),(b,y)]; rival => [(a,y),(b,x)].
        "witness": _wit(_TWO_DISJOINT,
                        "complement: gold pairs each label with its own model, "
                        "rival pairs it with the foreign model"),
    },
    {
        "id": "rival-wrong-model-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_MODEL,
        "refinement": (
            "applies the correct selection but emits the WRONG model name (a marker "
            "character appended). A real patch yielding a perturbed model identity "
            "would feed the consistency pre-check a model name that names no real "
            "model, breaking the check; it would NOT resolve. "
            "Verify-does-not-imply-resolve."
        ),
        "rationale": (
            "value-level near-miss. REJECTED by the postcondition — `pairsSpec` pairs "
            "each application's label with its model name EXACTLY, so a perturbed name "
            "is not provably equal (the selection is right but every model identity is "
            "off). Attacks clause (B), the model-name component; the single-app single-"
            "model input isolates it. If it VERIFIES => SPEC-TOO-WEAK (gathered model "
            "identities unconstrained)."
        ),
        # one app one model: gold => [(a,x)]; rival => [(a,x!)].
        "witness": _wit(_ONE_ONE,
                        "wrong model identity: gold emits the carrier's model name, "
                        "rival emits a perturbed name"),
    },
    {
        "id": "rival-wrong-label-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_LABEL,
        "refinement": (
            "the pair's FIRST component is set to the model name instead of the owning "
            "application's label, attributing each model to itself. A real patch that "
            "passed the wrong `app_label` to the consistency pre-check would query the "
            "router about (model_name, model_name) pairs that name no application, "
            "breaking the check; it would NOT resolve. Verify-does-not-imply-resolve."
        ),
        "rationale": (
            "label-component near-miss (no direct nagini twin — its single-group "
            "carrier had no label component). REJECTED by the postcondition — "
            "`pairsSpec` tags each model with its OWNING application's label, so "
            "`(m, m)` is not provably equal. Attacks clause (B) the label component "
            "(and clause (A) attribution); the single-app single-model input isolates "
            "it. If it VERIFIES => SPEC-TOO-WEAK (the label component unconstrained)."
        ),
        # one app one model: gold => [(a,x)]; rival => [(x,x)].
        "witness": _wit(_ONE_ONE,
                        "wrong label identity: gold tags the model with its app's "
                        "label, rival tags it with the model name"),
    },
    {
        "id": "rival-reversed-model-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REV_MODELS,
        "refinement": (
            "correct selection and identities, but each application's own models are "
            "emitted in REVERSE order. A real patch that reversed the per-application "
            "model iteration would drive the consistency pre-check in the wrong order; "
            "while every pair is individually valid, the spec (and the F2P behaviour it "
            "models) pins the enumeration ORDER, so a reordering rival is a genuine "
            "verify-does-not-imply-resolve probe of the order clause."
        ),
        "rationale": (
            "order rival (within-application). REJECTED by the postcondition — "
            "`pairsSpec` emits each application's models in `App.models` order, so a "
            "reversal is not provably equal whenever an application owns >=2 distinct "
            "models. Attacks clause (C), model order; the single-app TWO-model input "
            "isolates it from the application-order rival. If it VERIFIES => "
            "SPEC-TOO-WEAK (model order unconstrained)."
        ),
        # one app, two distinct models: gold => [(a,x),(a,y)]; rival => [(a,y),(a,x)].
        "witness": _wit(_ONE_TWO,
                        "reversed model order: gold emits models in carrier order, "
                        "rival reverses them"),
    },
    {
        "id": "rival-reversed-app-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REV_APPS,
        "refinement": (
            "correct selection and identities, but the applications are visited in "
            "REVERSE order. A real patch that reversed the outer application iteration "
            "would produce the same pairs in a different block order; the spec pins "
            "application order, so this probes the order clause on a DIFFERENT binder "
            "(the `apps` list) than the model-order rival. Verify-does-not-imply-"
            "resolve on the order clause."
        ),
        "rationale": (
            "order rival (across applications). REJECTED by the postcondition — "
            "`pairsSpec` folds `apps` front-to-back, so reversing the application order "
            "is not provably equal whenever there are >=2 applications contributing "
            "distinct pairs. Attacks clause (C), application order; varies the `apps` "
            "binder (list order) distinctly from the model-order rival. If it VERIFIES "
            "=> SPEC-TOO-WEAK (application order unconstrained)."
        ),
        # two apps: gold => [(a,x),(b,y)]; rival => [(b,y),(a,x)].
        "witness": _wit(_TWO_DISJOINT,
                        "reversed application order: gold folds apps front-to-back, "
                        "rival reverses the application order"),
    },
    {
        "id": "rival-take-first-model",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TAKE_FIRST,
        "refinement": (
            "emits only the FIRST of each application's own models. Every pair it "
            "produces is correctly attributed and correctly ordered — it is a strict "
            "PREFIX-per-application truncation, not a mis-attribution. Its faithful real "
            "patch would consult the router about only one model per application, so an "
            "application owning several models would have most of its models never "
            "checked at all: the pre-check silently passes combinations it never "
            "examined. That under-enumeration is a different failure from the "
            "mis-attribution the change fixes, and it would NOT resolve. "
            "Verify-does-not-imply-resolve on the completeness half of the clause."
        ),
        "rationale": (
            "PARTIAL-DOMAIN rival (ports nagini rival-partial-first). Correct on the "
            "entire sub-domain where no application owns more than one model — every "
            "such input agrees with `pairsSpec` exactly — and diverges only where some "
            "application owns >=2 models. REJECTED by the postcondition, which pins the "
            "result to ALL of `pairsSpec apps`, so dropping an application's later "
            "models is not provably equal. Attacks clause (A)'s omission half (none of "
            "an application's own models omitted), which the five uniformly-wrong "
            "rivals leave unprobed: each of them is already wrong at its first emitted "
            "pair, so none of them tests whether the spec constrains the enumeration "
            "past one model per application. If it VERIFIES => SPEC-TOO-WEAK "
            "(domain-incomplete: the per-application model tail escapes the spec)."
        ),
        # one app, two models: gold => [(a,x),(a,y)]; rival => [(a,x)] only.
        "witness": _wit(_ONE_TWO,
                        "take-first: gold emits both of the application's models, "
                        "rival drops every model after the first"),
    },
    {
        "id": "rival-transposed-pair",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRANSPOSE,
        "refinement": (
            "the pair's two components are swapped: the correct label and the correct "
            "model name are both present, in the wrong POSITIONS. A real patch that "
            "transposed the two arguments would pass the model name where the "
            "application label is expected and vice versa, so every lookup would name "
            "an application that does not exist; it would NOT resolve. "
            "Verify-does-not-imply-resolve."
        ),
        "rationale": (
            "the tightest near-miss on clause (B) the carrier admits: unlike the "
            "wrong-label rival, which DESTROYS the label component (`(m, m)` drops it "
            "entirely), this rival's component multiset is exactly right and the "
            "selection and both orderings are correct — only the orientation is wrong. "
            "REJECTED by the postcondition, because `pairsSpec` fixes which component "
            "is the label and which is the model name, and `(m, a.label)` is not "
            "provably equal whenever a label differs from the model name it is paired "
            "with. If it VERIFIES => SPEC-TOO-WEAK (pair orientation unconstrained, "
            "i.e. the spec pins only the component SET and not the projection)."
        ),
        # one app one model: gold => [(a,x)]; rival => [(x,a)].
        "witness": _wit(_ONE_ONE,
                        "transposed pair: gold puts the application label first, "
                        "rival puts the model name first"),
    },
]


# No @ContractOnly axioms and no opaque callees: the (application, model) pairing is
# modeled DEEPLY over the transparent carrier (`appPairs` / `pairsSpec`), so the axiom
# lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []


assessment = """\
Per-nagini-case disposition. Every case in the nagini battery is accounted for
here; the four lane-level exclusions are argued in the header comment.

  nagini case                 disposition
  --------------------------  ------------------------------------------------
  pos-explicit-else           PORTED as pos-flatmap (+ pos-direct). Nagini's
                              reshape was a branch rewrite; the lean carrier has
                              no guard to rewrite, so the equivalent
                              "same logic, different executable shape" move is
                              loop-accumulator -> pure combinator.
  admiss-self-call            PORTED as admiss-ground-registry. EXPRESSIBLE, and
                              the first draft dropped it as "N/A" on the reading
                              that an obligation with no precondition hypothesis
                              cannot be PRECOND-TOO-STRONG — an audit repair, not
                              a design choice. On a total carrier the analogue is
                              the obligation being UNSATISFIABLE at an F2P-shaped
                              input, which a ground `have` discharged BY
                              EVALUATION at a concrete two-application registry
                              tests directly. (Measured: real build, exit 0.)
  frame-mutate-owner          VACUOUS. Referential transparency: no aliasing and
  frame-mutate-member         no fractional permission, so "store into a
                              read-only input" is not expressible.
  rival-prepatch-allmembers   PORTED as rival-crossproduct-allmodels. Checked:
                              its impl region is byte-identical to
                              Solution_prepatch.lean's once comments are
                              stripped.
  rival-complement-filter     PORTED as rival-complement-attribution.
  rival-wrong-member-value    PORTED as rival-wrong-model-identity.
  rival-partial-first         PORTED as rival-take-first-model. EXPRESSIBLE, and
                              the first draft of this battery dropped it without
                              recording it — an audit repair, not a design
                              choice. Nagini's version gathered roster position 0
                              unconditionally, i.e. correct on one sub-domain and
                              wrong off it; the lean carrier expresses the same
                              domain-incompleteness as a per-application prefix
                              truncation (`a.models.take 1`), correct wherever no
                              application owns >=2 models. Nothing about the
                              carrier collapses this distinction.
  ax-gathered-sound           G-AX's lane; this gate ignores AXIOM_TESTS, and the
  ax-gathered-containment     pairing is modeled deeply so no axiom is consumed.

Added beyond the nagini battery, because the lean spec makes ORDER and the pair
PROJECTION explicit where nagini's single-group carrier had neither:
  rival-reversed-model-order, rival-reversed-app-order  -- clause (C), two
      distinct binders.
  rival-wrong-label-identity  -- the label component, which nagini had no
      counterpart for.
  rival-transposed-pair       -- the tightest near-miss on clause (B): both
      components correct, orientation swapped, so the spec is shown to pin the
      projection and not merely the component set.

Probed and NOT found (all figures below are real builds, re-measured in an
independent audit pass; the earlier draft of this paragraph asserted them without
recording the exit codes):

  SPEC-TOO-WEAK probes — five further wrong impls NOT in the battery, aimed where
  the carried rivals leave the spec unattacked, each with a `decide` witness at a
  literal input: per-application dedup of a repeated model name (`eraseDups`, at
  one app owning ["x","x"]); every pair emitted twice; first-application-only;
  per-LABEL grouping (pairs each app with the models of every app SHARING its
  label, at two apps that share label "a" — the near-miss the attribution rivals
  do not reach, since they all use distinct labels); and per-application
  `dropLast` (the mirror of take-first: drops the LAST model rather than the
  tail). Each rival built exit 1, and for each the witness built exit 0 against
  the rival and exit 1 against gold. No wrong impl verified.

  SPEC-TOO-STRONG probes — correct reshapes proven against the frozen spec, each
  exit 0: `foldr (appPairs a ++ ·) []` (with an explicit result-type annotation,
  else `++` chases the `Id` monad and the file does not elaborate — a tooling
  detail, not a spec property), `(apps.map appPairs).flatten`, an inlined
  `flatMap` that re-spells `appPairs` at the call site, and a filter that skips
  model-less applications (proven by cases on `a.models`). NOT closed: a
  reverse-accumulating loop that visits `apps.reverse` / `a.models.reverse` and
  PREPENDS. It computes the same list on every input, but its proof needs a
  reverse-recursion lemma the frozen helpers do not provide, and the audit did not
  close one. That is a PROOF-EFFORT gap on a reshape whose faithfulness is not in
  doubt, recorded as UNCERTAIN rather than claimed as a hole in either direction.

  Witness discrimination, re-derived independently for all eight reject cases:
  each witness built exit 0 against its rival and exit 1 against gold, and the
  gold-side error is a plain `decide` EVALUATION in every case ("Tactic `decide`
  proved that the proposition ¬(… ) = pairsSpec … is false") — the kernel computed
  both sides, so gold's exit code is a semantic refutation, never a stuck
  reduction or a missing identifier. The FORGERY check confirms the exit codes
  carry information about the CLAIM and not about the impl's shape: flipping each
  witness's claim (dropping the `¬`) INVERTS both builds — the flipped claim is
  exit 0 on gold and exit 1 on the rival, for all eight. No witness binds any
  hypothesis, so none rests on an assumption that could be inconsistent.

So the spec is neither too weak nor too strong on the surface reachable from this
carrier, with the one reshape above left uncertain.
"""
