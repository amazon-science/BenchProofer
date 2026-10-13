# properties.py — G-PBT falsification battery for django__django-12663 (lean lane).
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
#   outputType : List Selection → List AnnExpr → Option FieldId
#   The type descriptor reported for a query's overall output, fully pinned to the two
#   input lists by a single postcondition equality:
#     result = (if selections.length = 1 then some (baseOrDeclared selections.headI)
#               else if annotations.length = 1 then some annotations.headI.outputField
#               else none)
#   Although stated as one equality, this pins several INDEPENDENT sub-behaviours a
#   rival can attack one at a time. The whole carrier is TRANSPARENT — `baseOrDeclared`
#   is a total `Option.getD` fold over Nat identities, there is no opaque callee and no
#   answer-key — so `decide` computes the spec at any literal input and witnesses need
#   no conditioning on the carrier.
#
# The independent sub-clauses:
#   (P) single-column PREFERENCE: with exactly one column, the result prefers that
#       column's underlying referenced attribute (`base`) when present. This is the
#       load-bearing behaviour the F2P demands — returning the declared type instead
#       is the pre-patch bug.
#   (D) single-column FALLBACK: with exactly one column whose `base` is absent, the
#       result is the declared type (`baseOrDeclared` = `getD declared`), and it is a
#       PRESENT descriptor (`some`), never a raw optional.
#   (A) single-ANNOTATION branch: no column but exactly one annotation ⇒ that
#       annotation's declared output type, wrapped `some`.
#   (N) NONE branch: neither exactly-one-column nor exactly-one-annotation ⇒ `none`
#       (the output type is undetermined), never a spurious descriptor.
#
# CARRIER NOTE: the nagini sibling abstracted the SAME single-column decision to an
# int chooser `output_field_identity(sel)` over two int identities (sel.source == the
# underlying attribute with sentinel 0 == "no usable source", sel.field == the declared
# type) behind fractional read permission, and modeled ONLY that single-column branch.
# This backend models the richer surface directly: the whole property over two lists,
# with the length guards and the annotation / none branches transparent as well. So
# nagini's `S1` (prefer source) rival maps onto clause (P) here, its `S2` (else field)
# rival onto clause (D), and the extra structure (annotation branch, none branch, the
# length guards) is additionally attackable — clauses (A) and (N) have no nagini
# counterpart because nagini did not model those branches.
#
# Two further clauses are reachable here that no single-branch rival can touch, and the
# audit added a rival for each: the branch ORDER (`weak-branch-priority`) and the two
# exactly-one length GUARDS themselves (`weak-loose-selection-guard`,
# `weak-loose-annotation-guard`, which move a guard from `= 1` to `≥ 1` and so probe list
# lengths of 2 — a point no other witness in the battery reaches).
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY `frame-mutate-*`: sel.source/sel.field were
#     held at Acc(.., 1/2) read-only, and the rival WROTE a field back to satisfy a
#     clause vacuously, rejected for INSUFFICIENT-PERMISSION). Lean is referentially
#     transparent — no aliasing, no fractional permission — so a "store into a
#     read-only input" rival is not expressible and the whole lane is VACUOUS here.
#     The frame obligation itself is discharged structurally: the spec pins the result
#     to the inputs and reads nothing else. See 'assessment'.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. The choice is
#     modeled DEEPLY (baseOrDeclared), so there is no consumed axiom anyway.
#
# ADMISSIBILITY DOES PORT (this was corrected by audit). Nagini's
# `admiss-fresh-selection` defended a half-permission Requires + field != 0, and the
# lean obligation carries NO precondition hypothesis — but "no precondition" is NOT a
# reason to drop the lane. The analogue on a TOTAL carrier is the obligation being
# unsatisfiable at exactly an F2P-shaped input, which a positive that discharges the
# spec predicate AT that concrete input — by evaluation, as a `have`, before closing
# the frozen obligation verbatim — tests directly. `admiss-ground-f2p-selection`
# below is that positive; it was built and confirmed to verify against the real
# checker, so the lane is neither vacuous nor inexpressible here.
from pathlib import Path

INSTANCE = "django__django-12663"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# Each anchor lies ENTIRELY inside the impl-start/impl-end region and is unique in the
# file. Line-level rivals edit one of these; the two structural positives swap the
# whole impl body (and, for the functional positive, the proof body).

# The single-column branch's returned expression.
_SEL_RET = "      return some (baseOrDeclared select)"
assert _BASE.count(_SEL_RET) == 1, "single-column return anchor drifted"

# The annotation branch's returned expression.
_ANN_RET = "      return some annotations.headI.outputField"
assert _BASE.count(_ANN_RET) == 1, "annotation return anchor drifted"

# The single-column length GUARD (with its `Id.run do` lead-in, which is what makes it
# unique — the annotation guard has the same `= 1` shape).
_SEL_GUARD = "  Id.run do\n    if selections.length = 1 then"
assert _BASE.count(_SEL_GUARD) == 1, "single-column guard anchor drifted"

# The annotation length GUARD (paired with its own return, for uniqueness).
_ANN_GUARD = (
    "    else if annotations.length = 1 then\n"
    "      return some annotations.headI.outputField"
)
assert _BASE.count(_ANN_GUARD) == 1, "annotation guard anchor drifted"

# The otherwise (fall-through) return.
_OTHER_RET = "    return none"
assert _BASE.count(_OTHER_RET) == 1, "otherwise return anchor drifted"

# The full impl body (used by the functional/direct positive, which drops Id.run).
_FULL_IMPL = (
    "def implementation_outputType\n"
    "    (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=\n"
    "  Id.run do\n"
    "    if selections.length = 1 then\n"
    "      let select := selections.headI\n"
    "      return some (baseOrDeclared select)\n"
    "    else if annotations.length = 1 then\n"
    "      return some annotations.headI.outputField\n"
    "    return none"
)
assert _BASE.count(_FULL_IMPL) == 1, "full impl anchor drifted"

# The frozen proof body (tactic lines inside proof-start/proof-end). Only the
# functional positive swaps it — its `rfl`-shaped impl closes with a shorter honest
# reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro selections annotations\n"
    "  unfold problem_spec_outputType implementation_outputType\n"
    "  by_cases h1 : selections.length = 1\n"
    "  · simp only [Id.run, h1, if_true]; rfl\n"
    "  · by_cases h2 : annotations.length = 1 <;> "
    "simp only [Id.run, h1, h2, if_true, if_false] <;> rfl"
)
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# A 3-branch chooser needs no loop/lemma, so a functional restructure or an
# inlining keeps every obligation discharged.
# ===========================================================================

# pos-inline-getd: keeps the imperative Id.run shape but inlines `baseOrDeclared` to
# its definition `select.base.getD select.declared`. Definitionally identical, so the
# byte-identical frozen theorem statement AND the frozen proof body still close (the
# unfold + rfl sees through the definitional equality). Faithful restructure, no
# reproof, no new axiom/lemma/sorry. FAILS => SPEC-TOO-STRONG.
_POS_INLINE = _swap(
    _BASE,
    _SEL_RET,
    "      return some (select.base.getD select.declared)",
)

# pos-direct-functional: the cheapest HONEST impl — a pure functional chooser whose
# body is definitionally the postcondition RHS. Grounded entirely in the inputs (no
# oracle to echo; a wrong constant would fail the equality). The proof collapses to
# `rfl` after unfolding, reproving the identical theorem statement. Must VERIFY; else
# SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _swap(
        _BASE,
        _FULL_IMPL,
        "def implementation_outputType\n"
        "    (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=\n"
        "  if selections.length = 1 then\n"
        "    some (baseOrDeclared selections.headI)\n"
        "  else if annotations.length = 1 then\n"
        "    some annotations.headI.outputField\n"
        "  else\n"
        "    none",
    ),
    _PROOF,
    "  intro selections annotations\n"
    "  unfold problem_spec_outputType implementation_outputType\n"
    "  rfl",
)

# pos-reorder-fallback-first: the direct port of nagini's `pos-reorder-source-zero-first`
# (branch-reorder: test the FALLBACK leg first). Instead of calling `baseOrDeclared`, it
# case-splits the optional and takes the declared type on the `none` leg, the attribute
# on the `some` leg — the same value choice with the two legs mirrored. This is NOT
# definitionally equal to the frozen `Option.getD` spelling (the frozen `rfl` proof does
# NOT close it: `match select.base with …` is not defeq to `baseOrDeclared select` with
# `select.base` still a variable), so the case REPROVES the byte-identical statement by
# splitting on the optional. That makes it the strongest positive in the battery: the
# only one whose impl the frozen tactic script genuinely rejects. Audit-added, after
# confirming with real builds that the frozen proof body FAILS on it and this reproof
# closes it. FAILS => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _swap(
        _BASE,
        _SEL_RET,
        "      match select.base with\n"
        "      | none => return some select.declared\n"
        "      | some b => return some b",
    ),
    _PROOF,
    "  intro selections annotations\n"
    "  unfold problem_spec_outputType implementation_outputType baseOrDeclared\n"
    "  by_cases h1 : selections.length = 1\n"
    "  · simp only [Id.run, h1, if_true]\n"
    "    cases selections.headI.base <;> rfl\n"
    "  · by_cases h2 : annotations.length = 1 <;>\n"
    "      simp only [Id.run, h1, h2, if_true, if_false] <;> rfl",
)

# admiss-ground-f2p-selection: the ADMISSIBILITY positive. Discharges the spec predicate
# at a concrete F2P-shaped input — exactly one selected column whose underlying
# referenced attribute is PRESENT and DIFFERS from its declared output type, the shape
# the F2P turns on — by evaluation, as a `have`, and only then closes the frozen
# obligation verbatim. Nothing is assumed: no new declaration, no axiom/sorry, the
# theorem statement stays byte-identical, and the ground instance is a `have` prepended
# to the existing tactic body. Audit-added; the port had dropped the lane on the
# (incorrect) ground that a total obligation with no precondition hypothesis cannot be
# PRECOND-TOO-STRONG.
_ADM_GROUND = _swap(
    _BASE,
    _PROOF,
    "  have _ground : problem_spec_outputType [{ base := some 1, declared := 2 }] []\n"
    "      (implementation_outputType [{ base := some 1, declared := 2 }] []) := by\n"
    "    unfold problem_spec_outputType implementation_outputType\n"
    "    decide\n" + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# ignore-base (the PRE-PATCH bug): with exactly one column, returns the declared type,
# ignoring a present underlying attribute. Correct only on the sub-domain where they
# coincide (base absent, or base == declared).
_RIV_IGNORE_BASE = _swap(_BASE, _SEL_RET, "      return some select.declared")

# drop-fallback: with exactly one column, returns the underlying attribute RAW (the
# Option itself), losing the fallback to the declared type when the attribute is
# absent. Correct only where the attribute is present.
_RIV_DROP_FALLBACK = _swap(_BASE, _SEL_RET, "      return select.base")

# ann-none: with no column but exactly one annotation, reports `none` instead of the
# annotation's declared output type. Correct only on inputs that never enter the
# annotation branch.
_RIV_ANN_NONE = _swap(_BASE, _ANN_RET, "      return none")

# otherwise-some: on the undetermined case (neither exactly-one-column nor
# exactly-one-annotation) reports a spurious descriptor instead of `none`. Correct only
# where one of the two length guards fires.
_RIV_OTHER_SOME = _swap(_BASE, _OTHER_RET, "    return some 0")

# equal-only-pin (the port of nagini's `weak-equal-only-pin`): prefers the underlying
# attribute only when it ALREADY equals the declared type — i.e. never actually prefers
# it, since the two legs return the same thing. Correct exactly on the coinciding
# sub-domain and wrong on the DISCRIMINATING one. This is the value-proxy rival the port
# dropped; audit-added, because it is the near-miss `ignore-base` does not cover:
# `ignore-base` is a blunt "always declared", whereas this one LOOKS like it consults the
# attribute and still reverts to the bug wherever the two descriptors diverge.
_RIV_EQUAL_ONLY = _swap(
    _BASE,
    _SEL_RET,
    "      if select.base = some select.declared then\n"
    "        return some select.declared\n"
    "      else\n"
    "        return some select.declared",
)

# branch-priority: tests the ANNOTATION guard FIRST, so with exactly one column AND
# exactly one annotation it reports the annotation's type instead of the column's.
# Attacks the clause the four original rivals leave untouched — the spec's branch
# ORDER — which no rival editing a single branch's payload can reach.
_RIV_PRIORITY = _swap(
    _BASE,
    _FULL_IMPL,
    "def implementation_outputType\n"
    "    (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=\n"
    "  Id.run do\n"
    "    if annotations.length = 1 then\n"
    "      return some annotations.headI.outputField\n"
    "    else if selections.length = 1 then\n"
    "      let select := selections.headI\n"
    "      return some (baseOrDeclared select)\n"
    "    return none",
)

# loose-selection-guard: weakens the EXACTLY-one-column guard to at-least-one, so a
# multi-column query reports the first column's descriptor instead of `none`. Attacks the
# length guard itself (the `= 1` binder), which every other rival holds fixed.
_RIV_LOOSE_SEL = _swap(
    _BASE, _SEL_GUARD, "  Id.run do\n    if selections.length ≥ 1 then")

# loose-annotation-guard: weakens the EXACTLY-one-annotation guard to at-least-one, so a
# multi-annotation query with no single column reports the first annotation's type
# instead of `none`. The annotation-side counterpart of the guard attack above.
_RIV_LOOSE_ANN = _swap(
    _BASE, _ANN_GUARD,
    "    else if annotations.length ≥ 1 then\n"
    "      return some annotations.headI.outputField")


def _wit(sels, anns, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal input, closed by `decide`. `sels`/`anns` are the Lean list literals.
    Elaborates against a rival that diverges from the spec there, and fails on gold
    (which satisfies the spec at every input)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_outputType {sels} {anns}\n"
        f"    (implementation_outputType {sels} {anns}) := by\n"
        f"  unfold problem_spec_outputType implementation_outputType\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-inline-getd",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INLINE,
        "rationale": (
            "structurally-different but CORRECT impl: keeps the imperative Id.run shape "
            "and inlines the single-column chooser to its definition "
            "(select.base.getD select.declared), which is definitionally equal to "
            "baseOrDeclared. The frozen `theorem correct_outputType` statement is "
            "byte-identical and the frozen proof body still closes (unfold + rfl see "
            "through the definitional equality) — a faithful restructure with no reproof "
            "and no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition "
            "over-fit to the exact `baseOrDeclared` spelling)."
        ),
    },
    {
        "id": "pos-direct-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the cheapest HONEST impl: a pure functional 3-branch chooser whose body is "
            "definitionally the postcondition RHS, grounded entirely in the two input "
            "lists (no oracle to echo — a wrong constant would fail the equality). Drops "
            "the Id.run shape entirely and reproves the identical theorem statement, "
            "collapsing to `rfl` after unfolding. Must verify (the postcondition IS this "
            "equality); else SPEC-TOO-STRONG. Also witnesses that the spec is not "
            "echo-vulnerable — the four rivals show wrong constants/branches fail it."
        ),
    },

    {
        "id": "pos-reorder-fallback-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "the port of nagini's pos-reorder-source-zero-first: branch-reorder, testing "
            "the FALLBACK leg first. Case-splits the optional underlying attribute and "
            "returns the declared type on the absent leg, the attribute on the present "
            "leg — the same value choice with the two legs mirrored. Unlike the other two "
            "positives this is NOT definitionally equal to the frozen `Option.getD` "
            "spelling: the frozen tactic body genuinely FAILS on it (`Tactic rfl failed: "
            "match selections.headI.base with … is not definitionally equal to some "
            "(baseOrDeclared selections.headI)`, observed on a real build), so this case "
            "REPROVES the byte-identical statement by splitting on the optional. That is "
            "what makes it a real soundness probe rather than a restatement — it "
            "demonstrates the postcondition admits a faithful impl the frozen PROOF does "
            "not. If it FAILS => SPEC-TOO-STRONG (the postcondition over-fits the exact "
            "`baseOrDeclared` spelling rather than the value choice)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-ground-f2p-selection",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_GROUND,
        "rationale": (
            "the obligation is SATISFIABLE, non-vacuously, at a concrete F2P-shaped "
            "input: exactly one selected column whose underlying referenced attribute is "
            "PRESENT and DIFFERS from its declared output type (base = some 1, declared = "
            "2) — the discriminating shape clause (P) turns on. The spec predicate is "
            "discharged there by EVALUATION as a `have`, and only then is the frozen "
            "obligation closed verbatim. On this total carrier that is the analogue of "
            "nagini's PRECOND-TOO-STRONG probe (nagini's admiss-fresh-selection defended "
            "the half-permission Requires): if the modeled behaviour were unsatisfiable "
            "at exactly a normal F2P input, this `have` could not close, and the ∀-"
            "obligation's own pass would be attesting to a spec no real input reaches. "
            "Nothing is assumed — no new declaration, statement byte-identical, the "
            "ground instance is a `have` inside the existing tactic body."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-ignore-base-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_BASE,
        "refinement": (
            "returning the declared output type for the single-column case, ignoring the "
            "underlying referenced attribute, is exactly the PRE-PATCH behaviour. On the "
            "F2P case — a nested-subquery column whose underlying attribute differs from "
            "its declared type — it reports the relation-unaware declared type, so the "
            "lazily-evaluated related-object value cannot be coerced against the right "
            "attribute and the lookup raises the same TypeError the issue reports. A "
            "faithful patch of this shape does NOT resolve; a verifying rival is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the single-column PREFERENCE clause (P): with exactly one column "
            "whose base is present and differs from declared, the result must be the base. "
            "Witness fires the selections.length = 1 guard, sets base = some 1 present and "
            "distinct from declared = 2. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # [{base:=some 1, declared:=2}] [] : gold = some 1, rival = some 2.
        "witness": _wit("[{ base := some 1, declared := 2 }]", "[]",
                        "present attribute distinct from declared: gold prefers the "
                        "attribute, rival reports the declared type"),
    },
    {
        "id": "weak-drop-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_FALLBACK,
        "refinement": (
            "returning the underlying attribute WITHOUT the fallback to the declared type "
            "drops the `or select.field` leg: for a single column with no underlying "
            "attribute it reports the empty/absent optional instead of a present "
            "descriptor. Its faithful counterpart returns a non-descriptor for ordinary "
            "columns that have no target, so single-column queries over plain expressions "
            "yield a bad output field and the PASS_TO_PASS suite over such expressions "
            "breaks. Does NOT resolve (the fallback is load-bearing)."
        ),
        "rationale": (
            "REJECTED by the single-column FALLBACK clause (D): with exactly one column "
            "whose base is ABSENT, the result must be `some declared`, never the raw "
            "optional. Witness fires selections.length = 1 with base = none, so the spec "
            "demands some 5 while the rival yields none. Varies the base binder to `none` "
            "(the other single-column witness holds it `some`). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # [{base:=none, declared:=5}] [] : gold = some 5, rival = none.
        "witness": _wit("[{ base := none, declared := 5 }]", "[]",
                        "absent attribute: gold falls back to the declared type, rival "
                        "returns the empty optional"),
    },
    {
        "id": "weak-annotation-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ANN_NONE,
        "refinement": (
            "reporting `none` for the single-annotation case discards the annotation "
            "branch entirely. Its faithful counterpart would drop the "
            "`elif len(annotation_select) == 1: return …output_field` leg, so a query "
            "selecting exactly one annotation reports an undetermined output type and "
            "annotation-based lookups break — the PASS_TO_PASS annotation/output-field "
            "tests fail. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the ANNOTATION clause (A): with no column but exactly one "
            "annotation, the result must be `some` of that annotation's output type. "
            "Witness leaves selections empty (length ≠ 1) so the annotation guard fires, "
            "and sets the annotation's outputField = 7; the spec demands some 7 while the "
            "rival yields none. This is the only rival exercising the annotation branch — "
            "it varies both the selections binder (empty) and the annotations binder "
            "(singleton). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # [] [{outputField:=7}] : gold = some 7, rival = none.
        "witness": _wit("[]", "[{ outputField := 7 }]",
                        "single annotation, no column: gold reports the annotation's "
                        "output type, rival reports nothing"),
    },
    {
        "id": "weak-otherwise-some",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OTHER_SOME,
        "refinement": (
            "reporting a spurious descriptor on the undetermined case (neither "
            "exactly-one-column nor exactly-one-annotation) fabricates an output type "
            "where the property returns None. Its faithful counterpart would return a "
            "field object for multi-column / multi-annotation / empty selections, so "
            "downstream code that relies on the None sentinel to detect an undetermined "
            "output type mis-behaves and the PASS_TO_PASS suite over such queries breaks. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the NONE clause (N): with neither length guard satisfied the "
            "result must be `none`. Witness leaves both lists empty (both lengths = 0), so "
            "the spec demands none while the rival yields some 0. Varies both list binders "
            "to the empty run — the point disjoint from every other witness. If it "
            "VERIFIES => SPEC-TOO-WEAK (a hollow non-none constant would pass)."
        ),
        # [] [] : gold = none, rival = some 0.
        "witness": _wit("[]", "[]",
                        "neither branch fires: gold reports nothing, rival fabricates a "
                        "descriptor"),
    },
    {
        "id": "weak-equal-only-pin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EQUAL_ONLY,
        "refinement": (
            "consulting the underlying referenced attribute only when it ALREADY agrees "
            "with the declared output type is a no-op dressed as a fix: both legs return "
            "the declared type, so the reported descriptor is identical to the pre-patch "
            "one everywhere. It preserves the right answer exactly on the coinciding "
            "sub-domain (an ordinary freshly-built column, where the two descriptors are "
            "the same object) and reverts to the pre-patch answer on the divergent one, "
            "so the lazily-evaluated related-object value is still coerced against the "
            "wrong descriptor and the F2P still fails. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the single-column PREFERENCE clause (P), at the same witness "
            "point as the pre-patch rival but for a distinct reason: this rival is the "
            "NEAR-MISS the blunt `ignore-base` does not cover — it appears to consult the "
            "attribute (it branches on it) yet returns the declared type on both legs, so "
            "it agrees with gold on the whole coinciding sub-domain and diverges only "
            "where base ≠ declared. Witness holds base = some 1 against declared = 2, "
            "where the spec demands some 1 and the rival yields some 2 (confirmed by "
            "evaluation). Ports nagini's weak-equal-only-pin, which this battery had "
            "dropped. If it VERIFIES => SPEC-TOO-WEAK (the spec would admit a patch that "
            "changes nothing observable)."
        ),
        # [{base:=some 1, declared:=2}] [] : gold = some 1, rival = some 2.
        "witness": _wit("[{ base := some 1, declared := 2 }]", "[]",
                        "attribute present and distinct: the rival branches on the "
                        "attribute but returns the declared type either way"),
    },
    {
        "id": "weak-branch-priority",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PRIORITY,
        "refinement": (
            "checking the single-annotation case BEFORE the single-column case inverts the "
            "property's branch order. A query that selects exactly one column and also "
            "carries exactly one annotation then reports the annotation's declared output "
            "type instead of the column's descriptor, so the column-side coercion never "
            "happens on precisely the nested-annotation shape the F2P exercises, and "
            "single-column queries that happen to carry one annotation silently change "
            "their reported type. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the branch ORDER the postcondition's nested if-then-else pins: "
            "the column guard is the OUTER test, so wherever both guards would fire the "
            "result must be the column's descriptor. No rival that edits a single branch's "
            "payload can reach this clause — all four original rivals hold the order "
            "fixed — so this is the clause the battery left unattacked. Witness fires BOTH "
            "guards at once (one selection with base = some 1, declared = 2; one "
            "annotation with outputField = 9): the spec demands some 1 while the rival "
            "yields some 9 (confirmed by evaluation). It is also the only witness in the "
            "battery with a NON-EMPTY annotations list alongside a singleton selections "
            "list. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # [{base:=some 1, declared:=2}] [{outputField:=9}] : gold = some 1, rival = some 9.
        "witness": _wit("[{ base := some 1, declared := 2 }]", "[{ outputField := 9 }]",
                        "both guards fire: gold takes the column branch, rival takes the "
                        "annotation branch"),
    },
    {
        "id": "weak-loose-selection-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LOOSE_SEL,
        "refinement": (
            "weakening the EXACTLY-one-column guard to at-least-one makes a "
            "multiple-column query report its first column's descriptor instead of leaving "
            "the output type undetermined. Downstream code relies on the undetermined "
            "sentinel to know the query has no single output column; fabricating one "
            "descriptor for a multi-column query mis-coerces values against an unrelated "
            "column, so the PASS_TO_PASS suite over multi-column queries breaks. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the exactly-one length GUARD in clause (P)/(N): the spec's "
            "condition is `selections.length = 1`, not `≥ 1`, so with two columns and no "
            "single annotation the result must be `none`. This attacks the GUARD binder "
            "itself, which every original rival holds fixed at the frozen `= 1` while "
            "editing only branch payloads. Witness uses a TWO-element selections list "
            "(length 2 — a length no other witness in the battery reaches) with an empty "
            "annotations list: the spec demands none while the rival yields some 1 "
            "(confirmed by evaluation). If it VERIFIES => SPEC-TOO-WEAK (the guard would "
            "be unpinned above 1)."
        ),
        # two selections, no annotations : gold = none, rival = some 1.
        "witness": _wit(
            "[{ base := some 1, declared := 1 }, { base := some 2, declared := 2 }]", "[]",
            "two columns: gold leaves the output type undetermined, rival reports the "
            "first column's descriptor"),
    },
    {
        "id": "weak-loose-annotation-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LOOSE_ANN,
        "refinement": (
            "weakening the EXACTLY-one-annotation guard to at-least-one makes a query with "
            "several selected annotations and no single column report the first "
            "annotation's declared output type instead of leaving the output type "
            "undetermined — an arbitrary pick among several equally eligible annotations. "
            "Consumers that branch on the undetermined sentinel then take the wrong path "
            "for multi-annotation queries and the PASS_TO_PASS suite over them breaks. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the exactly-one length GUARD in clause (A)/(N), the "
            "annotation-side counterpart of the selection-guard attack: the spec's second "
            "condition is `annotations.length = 1`, not `≥ 1`, so with no single column "
            "and TWO annotations the result must be `none`. Witness uses an empty "
            "selections list with a TWO-element annotations list (the only witness in the "
            "battery reaching annotations.length = 2): the spec demands none while the "
            "rival yields some 3 (confirmed by evaluation). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # no selections, two annotations : gold = none, rival = some 3.
        "witness": _wit("[]", "[{ outputField := 3 }, { outputField := 4 }]",
                        "two annotations: gold leaves the output type undetermined, rival "
                        "reports the first annotation's type"),
    },
]

# AUDIT NOTE — a rival deliberately NOT shipped, recorded so the reason survives.
# `return some (baseOrDeclared selections.getLastI)` (take the LAST selected column
# rather than the first) reads like a genuine off-by-one attack and is VACUOUS on this
# carrier: the branch it sits in is guarded by `selections.length = 1`, where `getLastI`
# and `headI` are the same element, so the rival is observably identical to the frozen
# impl at every reachable input. Confirmed by real builds — a witness at
# `[{base := some 1, declared := 2}] []` fails against the RIVAL (exit 1, `decide`
# proving the negation false) exactly as it fails against gold, i.e. there is no input
# to discriminate at. Shipping it would have been a case whose rejection attested to a
# tactic mismatch and nothing else.


# No consumed axioms and no opaque callees: the single-column choice (underlying
# attribute else declared type), the annotation branch, the none branch, and the length
# guards are all modeled DEEPLY over the transparent List Selection / List AnnExpr
# carrier, so the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
