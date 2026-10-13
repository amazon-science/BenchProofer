# properties.py — G-PBT falsification battery for sympy__sympy-20590 (lean).
#
# NOT a Lean file; a manifest the runner parses. Each SPEC_TESTS case is a full
# Solution.lean variant built by region-surgery: only text inside the
# # impl-start/# impl-end region (and, for a soundness positive, the
# proof region) is edited, so the frozen spec view is byte-identical and
# markers.same_spec holds for every case by construction.
#
# === The defended surface (adversarial read) ===
# ONE modeled function. Its obligation `correct_immutableInstances` pins a single
# top-level clause:
#     problem_spec_immutableInstances otherLayers result := result = allPin otherLayers
# where `allPin layers = layers.all (fun b => b)` is a plain conjunction-fold over
# the input list, fully GROUNDED in `otherLayers` (not an opaque oracle the impl
# could echo). The one INPUT BINDER is `otherLayers : List Bool`; the result must
# be `true` exactly when every element is `true`.
#
# === Carrier narrowing vs the nagini sibling ===
# The nagini battery contracts FOUR functions (bind_undeclared_attribute,
# trait_pins_closed_layout, plus the core_expression_* proof scaffolds) over a
# `PSeq[bool]` carrier and a raise/return control split. This Lean bundle models
# only the purely functional core: the single boolean fold that decides whether an
# instance stays immutable. So the nagini cases attached to the raise/return
# machinery collapse onto the one clause here, and the nagini exception/normal
# split has no counterpart — a total Lean `def` returns a `Bool`, it does not
# raise. The per-case porting ledger is PORTING_LEDGER below (this comment
# previously pointed at an 'assessment' key that does not exist in this file —
# corrected under audit, along with the ledger's two wrong entries).
#
# Frame/permission class: VACUOUS here. Nagini's inputs are immutable pure value
# sequences with no read-only heap permission, so there was no frame-mutation
# surface even there; Lean is referentially transparent, so the class stays empty.
#
# Divergence class: EXPRESSIBLE AND REJECTED, but not shippable as a reject case.
# Corrected under audit; the earlier disposition ("a diverging body cannot be
# written at all") was measured FALSE and is retained here only as the thing that
# was wrong. Nagini's reject-diverge-* rivals spin an Invariant(True) loop to
# exploit partial-correctness vacuity. The lean analogue IS writable — a
# `partial def` body, either self-recursive outright or diverging only at the
# empty boundary via a `partial` helper — and both pass variant_scope cleanly
# (variant_problems == [] for each, checked). So the class is neither vacuous nor
# inexpressible.
#
# What closes it is that both rivals are REJECTED (build exit 1 each): a
# `partial def` is opaque, generating no equation lemmas, so the frozen
# obligation's `unfold implementation_immutableInstances` fails outright
# ("Tactic `unfold` failed to unfold `implementation_immutableInstances`") and the
# obligation cannot be discharged at all, vacuously or otherwise. There is no
# termination `set_option` to read on this carrier: Lean's own elaborator demands
# a measure for every total `def`, and the only escape hatch — `partial` — buys
# divergence at the price of the definitional unfolding any proof of the
# obligation needs. Hence NO spec hole.
#
# It is nonetheless not shippable as an `expect="reject"` case, because the same
# opacity that rejects the rival also blocks every witness, in both directions
# (four builds, all re-run under audit):
#   * the decidable witness (`¬ problem_spec … := by unfold …; decide`) FAILS
#     against the rival (exit 1, same `unfold` failure) — so the witness does not
#     hold of the rival, which the gate reads as `witness-unproven`;
#   * a hypothesis-conditioned witness (the technique that makes an opaque
#     carrier attackable) elaborates against the rival (exit 0) but ALSO against
#     the frozen solution (exit 0) — `witness-vacuous`, a tautology — and its
#     consistency probe derives `False` from its own hypothesis, since `simp_all`
#     reduces the frozen impl at the literal and clashes with the assumed value.
# A `witness_reference` cannot help: it substitutes the GOLD-side subject, and
# the failure here is on the RIVAL side. So the honest disposition is a KNOWN
# GAP in the battery (not in the spec): the verifier does reject the class, and
# the gate's witness contract cannot attest to that rejection.
# the corpus-wide termination-semantics finding's measured scope is the 401 velvet `partial`
# bundles; its "lean unaffected" row is consistent with the exit codes above, but
# the "cannot be written" gloss this file previously drew from it was not.

# === PORTING_LEDGER — per nagini case, what became of it here ================
# Rewritten under audit; every verdict below was re-derived with real builds
# rather than inherited from the port.
#
#   nagini reject-invert-branch   -> PORTED as reject-invert. The raise/return
#       split collapses onto the boolean, so the inverted branch becomes the
#       pointwise negation `any (not pins)`.
#   nagini reject-always-true     -> PORTED as reject-always-true.
#   nagini reject-always-raise    -> PORTED as reject-always-false. "Always
#       refuse" is "always report mutable" once the exception channel collapses
#       onto the result boolean.
#   nagini reject-empty-domain    -> PORTED as reject-empty-boundary.
#   nagini reject-trait-false     -> PORTED as reject-seed-open (LANDED UNDER
#       AUDIT; the port had dropped it). See that case's comment: the flipped
#       layer is the accumulator seed here, not an input, so it is expressible
#       and observably distinct from always-false in shape.
#   nagini reject-diverge-bind    -> NOT SHIPPABLE, but EXPRESSIBLE and rejected.
#   nagini reject-diverge-trait   -> Same. Both collapse onto one class here
#       (one modeled function, so there is no bind/trait split): a `partial def`
#       rival. It is writable, in-scope, and rejected — but no witness can
#       attest to that rejection, in either direction. See the divergence-class
#       note in the header for the four exit codes. Known battery gap, NOT a
#       spec hole, and NOT a vacuous class.
#   nagini pos-control-bind       -> PORTED, and widened: pos-control-all and
#       pos-control-demorgan are two independently-shaped correct impls.
#   nagini admiss-open-chain      -> PORTED as admiss-f2p-inputs.
#   nagini AXIOM_TESTS (ax-sound-slots-rule, ax-cover-slots-rule)
#                                 -> OUT OF LANE, not omitted: meta.json carries
#       axioms == [] and deep_model_references == [], and G-PBT does not run an
#       axiom lane on this backend (G-AX does, and it is recorded skip). The
#       layout rule is modeled deeply as `allPin`, with no opaque callee to fuzz.

from pathlib import Path

INSTANCE = "sympy__sympy-20590"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl region (the whole imperative body, from the `def` line to the
# final `return`; all of it lies inside # impl-start/# impl-end). Editing here
# keeps same_spec by construction.
_GOLD_IMPL = (
    "def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do\n"
    "  -- The layer under fix now pins its instance memory layout to a fixed attribute\n"
    "  -- set, so it contributes no per-instance attribute dictionary.\n"
    "  let mut immutable : Bool := true\n"
    "  -- Fold the conjunction over every remaining ancestry layer: a single layer that\n"
    "  -- leaves its layout open reopens the attribute dictionary for the instance.\n"
    "  for pins in otherLayers do\n"
    "    immutable := immutable && pins\n"
    "  return immutable"
)

# The gold proof body (whole tactic block between the theorem header and
# `-- proof-end`). Only touched by soundness positives, which reprove the
# reshaped impl while keeping the `theorem correct_*` STATEMENT byte-identical.
_GOLD_PROOF = (
    "  intro otherLayers\n"
    "  unfold problem_spec_immutableInstances implementation_immutableInstances allPin\n"
    "  -- Helper: the cleaned `forIn` loop equals a `List.foldl` conjunction (Route B).\n"
    "  have helper : ∀ (xs : List LayerPins) (init : Bool),\n"
    "      Id.run (forIn xs init (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)))\n"
    "        = xs.foldl (fun r pins => r && pins) init := by\n"
    "    intro xs\n"
    "    induction xs with\n"
    "    | nil => intro init; rfl\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl\n"
    "  -- Helper: the fold over the conjunction equals `init && all`.\n"
    "  have foldl_all : ∀ (xs : List LayerPins) (init : Bool),\n"
    "      xs.foldl (fun r pins => r && pins) init = (init && xs.all (fun b => b)) := by\n"
    "    intro xs\n"
    "    induction xs with\n"
    "    | nil => intro init; simp\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      rw [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]\n"
    "  -- Bridge the desugared loop body to the cleaned one (definitional).\n"
    "  show Id.run (forIn otherLayers true\n"
    "      (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))) = _\n"
    "  have hbody : (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))\n"
    "      = (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)) := rfl\n"
    "  rw [hbody, helper, foldl_all, Bool.true_and]"
)


# === REJECT 1 — always-true (the reported regression) =======================
# Mirrors the prepatch bug: the instance is reported immutable regardless of the
# ancestry layers. On any chain containing an open layer (a `false`) this returns
# `true` where the spec demands `false`. Faithful real patch: the mixin layer
# keeps its layout open, so downstream instances still carry a per-instance
# attribute dictionary and the F2P (which asserts the instance has NO such dict)
# fails — verify would not imply resolve.
_REJECT_ALWAYS_TRUE = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_immutableInstances (otherLayers : List LayerPins) : Bool :=\n"
    "  true",
)

# === REJECT 2 — always-false (over-restriction) =============================
# The dual constant: reports every instance mutable, even when every ancestry
# layer pins its layout. On the all-pinned chain the spec demands `true`; this
# returns `false`. A faithful real patch behaving this way would classify the
# already-correct all-pinned types as mutable, breaking PASS_TO_PASS behaviour
# that relies on the immutable classification — not a correct fix.
_REJECT_ALWAYS_FALSE = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_immutableInstances (otherLayers : List LayerPins) : Bool :=\n"
    "  false",
)

# === REJECT 3 — inverted decision ===========================================
# Flips the whole-domain decision: reports immutable exactly when SOME layer
# leaves its layout open (`any (not pins)`), the negation of the correct rule.
# Since `any (not pins) = not (all pins)`, this is the exact pointwise negation of
# the correct rule, so it is wrong on EVERY input with no coincidence point; on a
# singleton all-pinned chain it returns `false` for a spec value of `true`. A faithful real
# patch with an inverted layout test resolves nothing — it makes the pinned case
# mutable and the open case immutable, the opposite of the required behaviour.
_REJECT_INVERT = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_immutableInstances (otherLayers : List LayerPins) : Bool :=\n"
    "  otherLayers.any (fun b => !b)",
)

# === REJECT 4 — empty-chain boundary miss ===================================
# Correct on every NON-empty chain but wrong on the degenerate empty one: an
# empty ancestry list should be immutable (`allPin [] = true`, the vacuous
# conjunction), but this returns `false` there. The partial-domain attack: a
# rival that diverges only on the boundary input class. Its faithful real patch
# would misclassify the object-only / fully-pinned layout (no contributing
# ancestor layers) as mutable, contradicting the immutability the F2P pins on
# that layout.
_REJECT_EMPTY = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_immutableInstances (otherLayers : List LayerPins) : Bool :=\n"
    "  if otherLayers.isEmpty then false else otherLayers.all (fun b => b)",
)


# === REJECT 5 — position-sensitive: skips the FIRST layer ====================
# Folds the conjunction over `otherLayers.tail`, ignoring the head layer
# entirely. Correct whenever the head pins its layout, wrong exactly when the
# head is the layer that leaves it open — so it is the only rival here whose
# verdict depends on WHERE in the ancestry the open layer sits.
#
# Its witness probes `[false, true]`, NOT `[false]`. The `[false]` claim this case
# previously carried was corrected under audit: it asserted that no other rival
# refutes there, and two of them do — the always-true rival and the inverted
# rival both have witnesses at `[false]` that elaborate (exit 0 each, re-run), so
# `[false]` is not a point unique to this rival and the uniqueness claim was
# false as written. What IS unique to this rival is ORDER sensitivity, and
# `[false, true]` is the point that demonstrates it: this rival's verdict CHANGES
# across the permutation `[true, false] ↦ [false, true]` (it agrees with the spec
# at the former — that positive claim builds, exit 0 — and disagrees at the
# latter), while every other rival here is permutation-blind and returns the same
# answer at both. The spec value is `false` at both points, so a permutation-blind
# rival cannot distinguish them; only one that reads position can.
_ORDER_PROBE = "[false, true]"
_REJECT_DROP_HEAD = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_immutableInstances (otherLayers : List LayerPins) : Bool :=\n"
    "  otherLayers.tail.all (fun b => b)",
)


# === VERIFY 1 — positive control: functional `.all` shape ====================
# Structurally different but CORRECT: replaces the imperative accumulator loop
# with the direct library fold `otherLayers.all id`, which is definitionally the
# spec's `allPin`. Reproves with a one-line `rfl` (statement unchanged). Must
# verify, else SPEC-TOO-STRONG.
_VERIFY_POS_ALL = _swap(
    _swap(
        _BASE, _GOLD_IMPL,
        "def implementation_immutableInstances (otherLayers : List LayerPins) : Bool :=\n"
        "  otherLayers.all (fun b => b)",
    ),
    _GOLD_PROOF,
    "  intro otherLayers\n"
    "  unfold problem_spec_immutableInstances implementation_immutableInstances allPin\n"
    "  rfl",
)

# === VERIFY 2 — positive control: De Morgan reformulation ====================
# A second correct shape whose executable form differs materially: the immutable
# flag is `not (some layer leaves its layout open)`, i.e. `!(any (not pins))`.
# Logically identical to the conjunction-fold but computed the dual way; the
# proof closes via the De Morgan lemma relating `all` and `any`. Guards against a
# spec that only accepts the literal `all`-shaped answer.
_VERIFY_POS_DEMORGAN = _swap(
    _swap(
        _BASE, _GOLD_IMPL,
        "def implementation_immutableInstances (otherLayers : List LayerPins) : Bool :=\n"
        "  !(otherLayers.any (fun b => !b))",
    ),
    _GOLD_PROOF,
    "  intro otherLayers\n"
    "  unfold problem_spec_immutableInstances implementation_immutableInstances allPin\n"
    "  simp [List.all_eq_not_any_not]",
)


# === VERIFY 3 — admissibility: the obligation is LIVE at F2P-shaped inputs ===
# The PRECOND-TOO-STRONG direction. `problem_spec_immutableInstances` is a total
# obligation with no explicit precondition, so the analogue on this carrier is
# whether the obligation is actually SATISFIABLE at the concrete inputs the F2P
# observes — rather than being a clause no input reaches. This case discharges it
# by EVALUATION at both F2P-shaped ancestries as `have`s, and only then closes the
# frozen obligation verbatim (the gold tactic block is appended unchanged, so the
# general obligation is still fully reproven — the `have`s add liveness evidence,
# they do not replace the proof).
#
# The two points are the fully-pinned ancestry (every layer pins its layout, spec
# value `true`) and the same ancestry with one layer left open (spec value
# `false`). The third `have` shows those two observations actually DIFFER, which
# is what makes the pair a liveness demonstration and not two restatements of one
# point: if the obligation were satisfiable only vacuously, or if the spec
# collapsed both ancestries onto one answer, that inequality could not be closed
# by evaluation.
_VERIFY_ADMISS_F2P = _swap(
    _BASE, _GOLD_PROOF,
    "  -- Admissibility / liveness: discharge the obligation at the CONCRETE\n"
    "  -- F2P-shaped inputs by evaluation BEFORE proving the general statement.\n"
    "  have f2p_all_pinned : problem_spec_immutableInstances [true, true, true]\n"
    "      (implementation_immutableInstances [true, true, true]) := by\n"
    "    unfold problem_spec_immutableInstances implementation_immutableInstances allPin\n"
    "    decide\n"
    "  have f2p_one_open : problem_spec_immutableInstances [true, true, false]\n"
    "      (implementation_immutableInstances [true, true, false]) := by\n"
    "    unfold problem_spec_immutableInstances implementation_immutableInstances allPin\n"
    "    decide\n"
    "  -- The two observations are DISTINCT (true vs false), so the obligation is\n"
    "  -- live at both and does not collapse the pinned and open ancestries.\n"
    "  have f2p_discriminates :\n"
    "      implementation_immutableInstances [true, true, true]\n"
    "        ≠ implementation_immutableInstances [true, true, false] := by\n"
    "    unfold implementation_immutableInstances\n"
    "    decide\n"
    + _GOLD_PROOF,
)


# === REJECT 6 — the fixed layer itself leaves its layout open ================
# Added under audit to close a real omission. The nagini sibling's
# reject-trait-false flips the ONE layer the fix is about — the layer whose
# layout-pinning declaration the patch supplies — rather than one of the
# `otherLayers` the impl folds over. That layer is not an input on this carrier;
# it is the accumulator's INITIAL value, which the frozen impl seeds `true`
# precisely because that layer now pins its layout. Seeding it `false` is the
# faithful port, and it is observably distinct from REJECT 2 (always-false) even
# though both answer `false` everywhere: this one keeps the fold, so it attacks
# the initial value of the conjunction rather than replacing the computation. The
# port had dropped it as collapsed onto always-false; the collapse is on the
# extension, not on the shape under test, and the case is cheap, so it is landed
# rather than argued. Witness probes the all-pinned chain [true, true], where the
# spec demands `true` and a `false`-seeded fold returns `false`.
_REJECT_SEED_OPEN = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do\n"
    "  let mut immutable : Bool := false\n"
    "  for pins in otherLayers do\n"
    "    immutable := immutable && pins\n"
    "  return immutable",
)


def _witness(inp):
    """A refutation stated at a concrete list input: the rival's result differs
    from the spec value there. Decidable at literals — no conditioning needed,
    so the head binds nothing and the consistency probe is a no-op."""
    return (
        f"example : ¬ problem_spec_immutableInstances {inp}\n"
        f"    (implementation_immutableInstances {inp}) := by\n"
        f"  unfold problem_spec_immutableInstances implementation_immutableInstances allPin\n"
        f"  decide"
    )


SPEC_TESTS = [
    {
        "id": "reject-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_ALWAYS_TRUE,
        "rationale": (
            "Attacks the sole clause result = allPin otherLayers. On a chain with "
            "an open layer allPin is false, so a constant true return is "
            "inadmissible. Witness probes [true, false] (an open layer present)."
        ),
        "refinement": (
            "This is the reported regression: the mixin layer stays open, so "
            "downstream instances keep a per-instance attribute dictionary. A "
            "faithful real patch leaving the layout open lets the target instance "
            "still carry that dictionary, so the F2P assertion that it has none "
            "fails — the rival verifying would be a true verify-does-not-resolve "
            "break, not an artifact."
        ),
        "witness": _witness("[true, false]"),
    },
    {
        "id": "reject-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_ALWAYS_FALSE,
        "rationale": (
            "Attacks the sole clause from the other side: on an all-pinned chain "
            "allPin is true, so a constant false return is inadmissible. Witness "
            "probes [true, true] (every layer pins)."
        ),
        "refinement": (
            "A faithful real patch that classifies every layout as open would mark "
            "the already-correct all-pinned types as mutable, regressing "
            "PASS_TO_PASS behaviour that depends on the immutable classification — "
            "so it does not resolve the task."
        ),
        "witness": _witness("[true, true]"),
    },
    {
        "id": "reject-invert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_INVERT,
        "rationale": (
            "Inverts the decision (any-open instead of all-pinned). Because "
            "any (not pins) is the pointwise negation of all pins, the rival "
            "disagrees with the clause result = allPin otherLayers at EVERY input. "
            "On the singleton pinned chain [true] the spec value is true and the "
            "rival returns false. Witness probes [true] — the minimal non-empty "
            "point distinguishing the inverted rule from the correct one."
        ),
        "refinement": (
            "An inverted layout test resolves nothing: it makes the pinned layout "
            "report mutable and the open layout report immutable, the opposite of "
            "the behaviour the issue and F2P require."
        ),
        "witness": _witness("[true]"),
    },
    {
        "id": "reject-empty-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_EMPTY,
        "rationale": (
            "Partial-domain miss: correct on non-empty chains, wrong on the empty "
            "one. allPin [] is the vacuous conjunction true; the rival returns "
            "false. Witness probes the empty list — the binder's length-0 point, "
            "which no other witness exercises."
        ),
        "refinement": (
            "A faithful real patch misbehaving only on the empty ancestry (an "
            "object-only / fully-pinned layout with no contributing layers) would "
            "misclassify that immutable layout as mutable, contradicting the "
            "immutability the F2P pins on it — so it does not resolve the boundary."
        ),
        "witness": _witness("([] : List LayerPins)"),
    },
    {
        "id": "reject-drop-head",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_DROP_HEAD,
        "rationale": (
            "Order-sensitivity probe: folds over otherLayers.tail, so the FIRST "
            "ancestry layer's flag is ignored. Attacks the sole clause result = "
            "allPin otherLayers at [false, true], where allPin is false and this "
            "rival returns true (the tail [true] pins). The claim this case makes is "
            "ORDER sensitivity, not a uniquely-refuting input: this rival is the only "
            "one here whose verdict changes across the permutation [true, false] -> "
            "[false, true] (it agrees with the spec at the first and disagrees at the "
            "second), while the other four are permutation-blind and answer both "
            "points alike. The spec value is false at both, so only a rival that "
            "reads position can tell them apart."
        ),
        "refinement": (
            "A faithful real patch that consults every ancestry layer EXCEPT the "
            "first would miss exactly the case where the layer that leaves its "
            "layout open is the first one consulted — reporting the instance "
            "immutable while it still carries a per-instance attribute dictionary, "
            "so the F2P assertion that it has none fails. Verify would not imply "
            "resolve."
        ),
        "witness": _witness(_ORDER_PROBE),
    },
    {
        "id": "reject-seed-open",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_SEED_OPEN,
        "rationale": (
            "Attacks the conjunction's INITIAL value rather than the fold: the layer "
            "the fix is about is not one of the input otherLayers, it is the "
            "accumulator seed, which must be true because that layer pins its "
            "layout. Seeded false, the fold returns false even on an all-pinned "
            "chain, where the clause result = allPin otherLayers demands true. "
            "Witness probes [true, true]. Distinct in shape from the always-false "
            "rival — the fold is retained, only its seed is wrong — which is the "
            "sub-domain the other rivals leave unattacked."
        ),
        "refinement": (
            "A faithful real patch in which the layer under fix still leaves its "
            "memory layout open reports every instance mutable regardless of the "
            "remaining ancestry, so the F2P assertion that the target instance "
            "carries no per-instance attribute dictionary fails on exactly the "
            "all-pinned ancestry the fix is meant to produce — verify would not "
            "imply resolve."
        ),
        "witness": _witness("[true, true]"),
    },
    {
        "id": "pos-control-all",
        "kind": "soundness",
        "expect": "verify",
        "module": _VERIFY_POS_ALL,
        "rationale": (
            "Structurally-different but CORRECT impl: the direct library fold "
            "otherLayers.all id in place of the imperative accumulator loop, "
            "definitionally equal to allPin. Reproves with rfl, statement "
            "unchanged. Must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-demorgan",
        "kind": "soundness",
        "expect": "verify",
        "module": _VERIFY_POS_DEMORGAN,
        "rationale": (
            "A second correct shape computed the dual way: !(any layer leaves its "
            "layout open). Logically identical to the conjunction-fold; proof "
            "closes via the all/any De Morgan lemma. Guards against a spec that "
            "only admits the literal all-shaped answer."
        ),
    },
    {
        "id": "admiss-f2p-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _VERIFY_ADMISS_F2P,
        "rationale": (
            "PRECOND-TOO-STRONG direction. The obligation is total (no explicit "
            "precondition), so the analogue here is satisfiability at an F2P-shaped "
            "input: this case discharges the obligation by evaluation at the "
            "fully-pinned ancestry [true, true, true] (spec value true) and at the "
            "same ancestry with one layer left open [true, true, false] (spec value "
            "false), as `have`s, and only then closes the frozen obligation "
            "verbatim. A third `have` shows the two observations differ, so the "
            "clause is live at both points rather than vacuously true or collapsing "
            "them onto one answer. If this could not verify, the obligation would be "
            "unsatisfiable exactly where the F2P observes it."
        ),
    },
]
