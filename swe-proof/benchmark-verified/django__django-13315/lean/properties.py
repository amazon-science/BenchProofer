"""properties.py — G-PBT falsification battery for django__django-13315 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region is
changed, so ``markers.same_spec`` holds and the ``theorem
correct_applyChoiceLimit`` STATEMENT stays byte-identical). Every case here
leaves the ``-- proof-start`` / ``-- proof-end`` body frozen: the positives
close under it unchanged, and the reject rivals are judged by their machine-
checked ``witness``, not by whether the frozen tactic script happens to break.
``expect="verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's ``witness`` holds of the rival while FAILING on the frozen
solution).

DEFENDED SURFACE (one modeled behavior; one spec predicate).  A candidate
collection is narrowed by an optional constraint, governed by two gates:

  problem_spec_applyChoiceLimit applicable constraintActive base result : Prop
    result = (if applicable && constraintActive then base.filter qualifies else base)

with ``qualifies c := c.matchRows != 0``. The single equality clause folds four
independent observables the rivals attack:

  * the ``applicable`` gate — when false, the collection is returned UNCHANGED;
  * the ``constraintActive`` gate — when false, the collection is UNCHANGED;
  * the MEMBERSHIP test ``qualifies`` — a candidate is kept iff at least one
    related row satisfies the constraint (``matchRows != 0``);
  * the AT-MOST-ONCE cardinality — a kept candidate appears exactly as often as
    it occurs in the input, NEVER once per satisfying related row.

There is NO opaque answer key: the result is grounded in the input fields
(``base``, ``matchRows``), so ``result = …`` is dischargeable only by the real
computation (spec_guide directive 8). The carrier is FULLY TRANSPARENT — ``Bool``
gates, ``List Candidate`` with ``Nat`` fields — so every reject witness states
the spec predicate at a ground input and refutes it by ``List.length`` (a
``decide``-able ``Nat`` inequality; ``Candidate`` has no ``DecidableEq`` but its
length under the two impls does).

BINDER STRUCTURE (read before judging coverage). The postcondition's INPUT
binders are ``applicable``, ``constraintActive``, and ``base`` (whose elements
carry ``matchRows``). ``Candidate.id`` is a free identity carrier the modeled
behavior never inspects (``qualifies`` reads only ``matchRows``); it is present
so distinct candidates are expressible, and it is deliberately irrelevant to the
narrowing — see ``assessment``. The reject witnesses vary ``applicable``
({true,false}), ``constraintActive`` ({true,false}) and ``matchRows``
({0,1,2}), so no gate binder is pinned and each is shown load-bearing by a rival
that mishandles it.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds the raw
    matching stream at half-permission (``Acc(list_pred(matches), 1/2)``) and
    makes its MANDATORY frame-mutation rival WRITE to it. Lean is referentially
    transparent: ``base`` is an immutable value with no heap footprint, no
    aliasing, no read-only field to overwrite. NOT fabricated (per the porting
    map this class is vacuous here); see ``assessment``.

  * ADMISSIBILITY — PORTED, not vacuous (corrected by audit). The nagini
    sibling self-calls ``offered_options`` on an F2P-shaped stream to prove its
    ``Requires`` admits a normal input. This bundle's
    ``correct_applyChoiceLimit`` carries no precondition hypothesis (the ``∀``
    is unguarded — the behavior is total), and an earlier revision of this file
    concluded from that alone that the lane was vacuous. That reasoning is
    WRONG: "the frozen obligation has no precondition" is not a demonstration
    of vacuity. The analogue on a TOTAL carrier is the obligation being
    UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
    discharges the obligation at that concrete input — by evaluation, as a
    ``have``, before closing the frozen obligation verbatim — tests directly.
    ``admiss-f2p-shaped-narrowing`` is that case, and its ``have``s are
    measured load-bearing against the pre-patch impl (see the case comment).

  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a filter over input fields,
    not an axiomatized oracle; the ``axioms`` region declares no
    ``opaque``/``axiom``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl — the frozen ``cases … <;> rfl`` is tuned to the frozen
``Id.run do`` shape — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each was checked with two real
``lake env lean`` builds to ELABORATE against its rival and to FAIL against the
frozen solution (so it discriminates rather than asserting a tautology). The
five witnesses probe five DISTINCT input tuples (see the accounting block).

INDEPENDENT PROBES run by the audit and NOT shipped as cases (recorded so the
next reader need not re-derive them). Wrong impls beyond the five rivals, each
built for real against the frozen spec: reversing the narrowed collection's
ORDER; collapsing the narrowed collection by ``id`` (``pwFilter``); offering only
the FIRST qualifying candidate (``take 1``); and thresholding membership at
``matchRows ≥ 2`` instead of ``≠ 0``. All four FAILED to verify (exit 1, the
frozen ``rfl``), so the single equality clause is not too weak in the order,
per-occurrence-cardinality, count or threshold directions. Correct reshapes,
also built: ``filterMap (fun c => if qualifies c then some c else none)`` — NOT
definitionally the frozen ``filter``, so it genuinely re-proves via a
``filterMap``/``filter`` induction — and an explicit structurally-recursive
``narrowRec`` helper in the impl region with an induction lemma in the proof
region. BOTH VERIFIED (exit 0), so the spec admits faithful reshapes whose proof
is not the frozen ``rfl``, and it is not too strong.

AXIOM lane: EMPTY. meta.json ``axioms == []`` and ``deep_model_references == []``
— the modeled narrowing is a total filter over input fields, so there is no
axiom-soundness obligation here (that lane is G-AX's). ``AXIOM_TESTS`` is empty.
"""
from pathlib import Path

INSTANCE = "django__django-13315"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchor. The whole impl `def` is the load-bearing shape of the
# ---- impl region; every reshape lands entirely inside `-- impl-start` /
# ---- `-- impl-end`. The `-- proof` region is left frozen by every case. ----
_IMPL = (
    "def implementation_applyChoiceLimit\n"
    "    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=\n"
    "  Id.run do\n"
    "    let mut queryset := base\n"
    "    if applicable then\n"
    "      if constraintActive then\n"
    "        queryset := queryset.filter qualifies\n"
    "    return queryset"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof view intact)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- proof-region anchor. The frozen tactic body, verbatim. The admissibility
# ---- positive PREPENDS ground `have`s to it and closes the frozen obligation
# ---- unchanged afterwards, so the `theorem correct_applyChoiceLimit` STATEMENT
# ---- stays byte-identical and no new declaration/axiom/assumption token is
# ---- introduced (variant_scope-clean). The spec view elides the whole proof
# ---- region, so same_spec is untouched. ----
_PROOF = (
    "  intro applicable constraintActive base\n"
    "  unfold problem_spec_applyChoiceLimit implementation_applyChoiceLimit\n"
    "  cases applicable <;> cases constraintActive <;> rfl"
)


def _with_proof_prefix(prefix: str) -> str:
    """Solution.lean with `prefix` prepended to the FROZEN tactic body."""
    return _swap(_BASE, _PROOF, prefix + _PROOF)


# ---- witness scaffold. The spec is a bare predicate, so a witness states it
# ---- directly at a ground input: `¬ problem_spec_applyChoiceLimit a b base
# ---- (implementation_applyChoiceLimit a b base)`. Checked in a file whose
# ---- frozen obligation is elided by the gate, so no tactic script can mask the
# ---- verdict. `Candidate` has no `DecidableEq`, but the two impls' results
# ---- differ in LENGTH, a `decide`-able `Nat` inequality; `congrArg
# ---- List.length` reduces the spec (in)equality to it. Against gold the same
# ---- `decide` faces two equal lengths and fails — the discrimination half. ----
def _witness(app: str, active: str, base: str) -> str:
    call = f"{app} {active} {base}"
    return (
        f"example : ¬ problem_spec_applyChoiceLimit {call}\n"
        f"    (implementation_applyChoiceLimit {call}) := by\n"
        "  intro h\n"
        "  exact absurd (congrArg List.length h) (by decide)\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_applyChoiceLimit` statement AND the frozen proof body
    # byte-identical (the frozen `cases … <;> rfl` still closes — verified with
    # a real build). No proof authoring, no helper lemma, no assumption token.
    # =====================================================================
    {
        "id": "pos-direct-forward",
        "kind": "soundness",
        "expect": "verify",
        # Functional reshape: drop the `Id.run do`/`let mut` scaffold and express
        # the narrowing directly as a conditional over the two gates.
        # Definitionally identical, so the frozen `cases … <;> rfl` still closes.
        "module": _with_impl(
            "def implementation_applyChoiceLimit\n"
            "    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=\n"
            "  if applicable && constraintActive then base.filter qualifies else base"),
        "rationale": "correct reshape of the mutable-do narrowing into a direct "
                     "conditional; it computes the same value on every input, so it "
                     "must satisfy `result = (if applicable && constraintActive then "
                     "base.filter qualifies else base)` — else SPEC-TOO-STRONG. "
                     "Proof: the frozen `cases applicable <;> cases constraintActive "
                     "<;> rfl` still closes (both branches are now definitionally the "
                     "spec's branches).",
    },
    {
        "id": "pos-reorder-gates",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: test the two gates in the OTHER
        # nesting order (constraintActive outer, applicable inner). `&&` is
        # commutative, so the decision collapses to the same value on all four
        # gate combinations; the frozen `cases … <;> rfl` closes it.
        "module": _with_impl(
            "def implementation_applyChoiceLimit\n"
            "    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=\n"
            "  Id.run do\n"
            "    let mut queryset := base\n"
            "    if constraintActive then\n"
            "      if applicable then\n"
            "        queryset := queryset.filter qualifies\n"
            "    return queryset"),
        "rationale": "structurally different CORRECT reshape: the two gates are "
                     "nested in the opposite order. Both gates must hold for the "
                     "narrowing to fire, and conjunction is commutative, so "
                     "`result = (if applicable && constraintActive then base.filter "
                     "qualifies else base)` holds on every gate combination — a "
                     "faithful reshape MUST verify, else SPEC-TOO-STRONG. Proof: the "
                     "frozen `cases … <;> rfl` closes all four collapsed branches; no "
                     "new axiom/lemma, statement unchanged.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). The frozen obligation carries no
    # precondition hypothesis (the `∀` is unguarded — the behavior is total), so
    # there is no `Requires` to admit in the nagini sense. The analogue on a
    # TOTAL carrier is the obligation being UNSATISFIABLE at exactly an
    # F2P-shaped input, which this positive tests directly: it discharges the
    # spec predicate BY EVALUATION, as ground `have`s, at the concrete
    # F2P-shaped input — several candidates each satisfying the constraint
    # through MORE THAN ONE related row — and only then closes the frozen
    # obligation verbatim. If the obligation could not be discharged at that
    # input, this case would fail while the two generic positives above still
    # passed, which is precisely the direction they cannot test.
    #
    # The three `have`s are load-bearing, not decoration. Measured against the
    # PRE-PATCH impl (same three `have`s, frozen proof body, real builds): the
    # baseline prepatch file fails ONLY in the frozen `rfl` (1 error), whereas
    # each `have` ADDED ALONE fails at its OWN line — `_ground` and `_offered`
    # with `rfl has type ?m = ?m but is expected to have type <the concrete
    # claim>`, `_atMostOnce` likewise on the length. So each `have` pins the
    # at-most-once narrowing at this input rather than restating something any
    # impl satisfies. Against the frozen impl all three close by `rfl`.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-narrowing",
        "kind": "admissibility",
        "expect": "verify",
        # Prepended to the FROZEN tactic body; the frozen obligation is then
        # closed verbatim. No new declaration, no lemma, no assumption token,
        # statement byte-identical.
        "module": _with_proof_prefix(
            "  -- The obligation is satisfiable at an F2P-shaped input: two distinct\n"
            "  -- candidates, EACH satisfying the constraint through several related\n"
            "  -- rows (matchRows = 3 and 2), with both gates open. Discharged by\n"
            "  -- evaluation (`rfl`), so the admission is pinned to this input.\n"
            "  have _ground : problem_spec_applyChoiceLimit true true [⟨101,3⟩, ⟨102,2⟩]\n"
            "      (implementation_applyChoiceLimit true true [⟨101,3⟩, ⟨102,2⟩]) := rfl\n"
            "  -- ...and the narrowing OFFERS each of them, exactly once each: the\n"
            "  -- result is the collection itself, not a per-related-row expansion.\n"
            "  have _offered : implementation_applyChoiceLimit true true [⟨101,3⟩, ⟨102,2⟩]\n"
            "      = [⟨101,3⟩, ⟨102,2⟩] := rfl\n"
            "  have _atMostOnce :\n"
            "      (implementation_applyChoiceLimit true true [⟨101,3⟩, ⟨102,2⟩]).length = 2 := rfl\n"),
        "rationale": "ADMISSIBILITY on a total carrier. The frozen `∀` is "
                     "unguarded, so there is no precondition to admit; the "
                     "PRECOND-TOO-STRONG analogue here is the obligation being "
                     "unsatisfiable at an F2P-shaped input, and this case "
                     "discharges it at exactly such an input BY EVALUATION "
                     "before closing the frozen obligation verbatim. The input "
                     "is the F2P shape: several distinct candidates, each "
                     "satisfying the constraint through MORE THAN ONE related "
                     "row (matchRows = 3, 2), both gates open — the sub-domain "
                     "where a per-related-row expansion would offer duplicates. "
                     "The `have`s pin that each candidate is offered EXACTLY "
                     "ONCE (result = the collection itself; length 2, not 5). "
                     "Non-vacuity measured with real builds against the "
                     "pre-patch impl: the baseline fails only in the frozen "
                     "`rfl`, while each `have` added alone fails at its own "
                     "line, so none of them is a restatement that any impl "
                     "satisfies. Must verify, else PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing F2P test. The five witnesses
    # probe the four folded observables (both gates, membership, cardinality).
    # =====================================================================
    {
        "id": "join-multiplicity",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-patch behaviour: when both gates hold, list each
        # qualifying candidate ONCE PER satisfying related row (the join's
        # per-related-row multiplicity) instead of at most once. This is exactly
        # Solution_prepatch.lean's do-block. Attacks the AT-MOST-ONCE clause.
        "module": _with_impl(
            "def implementation_applyChoiceLimit\n"
            "    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=\n"
            "  Id.run do\n"
            "    let mut queryset := base\n"
            "    if applicable then\n"
            "      if constraintActive then\n"
            "        queryset := queryset.flatMap (fun c => List.replicate c.matchRows c)\n"
            "    return queryset"),
        "refinement": "this is the LITERAL pre-patch behaviour — narrowing across a "
                      "multi-valued relation lists a candidate once per satisfying "
                      "related row (no at-most-once collapse). On the F2P shape a "
                      "candidate satisfies the constraint through several related "
                      "rows, so the field would offer it MULTIPLE times; the F2P "
                      "asserts each eligible candidate appears exactly once and would "
                      "FAIL — it does NOT resolve (it IS the duplicate-options defect "
                      "the fix removes).",
        "rationale": "REJECT from the AT-MOST-ONCE cardinality of `result = "
                     "base.filter qualifies` (both gates true). Refuted at "
                     "`base=[⟨7,2⟩]` (a candidate matching through 2 related rows): "
                     "the rival returns length 2, the spec length 1. Discrimination "
                     "comes from `matchRows ≥ 2` — the exact sub-domain no other "
                     "rival probes.",
        "witness": _witness("true", "true", "[⟨7,2⟩]"),
    },
    {
        "id": "invert-membership",
        "kind": "uniqueness",
        "expect": "reject",
        # Inverted membership: when both gates hold, keep a candidate iff it does
        # NOT qualify — drop the genuinely-matching candidates and keep the
        # non-matching ones. Attacks the `qualifies` membership clause.
        "module": _with_impl(
            "def implementation_applyChoiceLimit\n"
            "    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=\n"
            "  Id.run do\n"
            "    let mut queryset := base\n"
            "    if applicable then\n"
            "      if constraintActive then\n"
            "        queryset := queryset.filter (fun c => !qualifies c)\n"
            "    return queryset"),
        "refinement": "a faithful real patch that kept a candidate only when it did "
                      "NOT satisfy the constraint would DROP the genuinely-eligible "
                      "candidates and OFFER the ineligible ones — the F2P asserts the "
                      "eligible candidates are present and would FAIL; it does NOT "
                      "resolve (it inverts the very membership the field is meant to "
                      "expose).",
        "rationale": "REJECT from the membership clause of `result = base.filter "
                     "qualifies` (both gates true). Refuted at `base=[⟨7,1⟩]` (a "
                     "qualifying candidate): the spec keeps it (length 1), the rival "
                     "drops it (length 0). Discrimination comes from `qualifies` "
                     "being negated on a matching candidate.",
        "witness": _witness("true", "true", "[⟨7,1⟩]"),
    },
    {
        "id": "ignore-applicable-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Narrow whenever the constraint is present, IGNORING the applicable
        # gate. Correct whenever `applicable` is true; wrong when `applicable`
        # is false and the constraint would otherwise narrow. Attacks the
        # `applicable` gate binder.
        "module": _with_impl(
            "def implementation_applyChoiceLimit\n"
            "    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=\n"
            "  Id.run do\n"
            "    let mut queryset := base\n"
            "    if constraintActive then\n"
            "      queryset := queryset.filter qualifies\n"
            "    return queryset"),
        "refinement": "a faithful real patch that narrowed by the constraint even "
                      "when the field does not expose an applicable candidate "
                      "collection would filter a collection that must be returned "
                      "untouched — dropping candidates a non-applicable field is "
                      "required to keep; the guarded-untouched behavior the "
                      "PASS_TO_PASS suite relies on would break, so it does NOT "
                      "resolve.",
        "rationale": "REJECT from the `applicable` gate: the spec returns `base` "
                     "unchanged when `applicable=false`, but the rival still filters. "
                     "Refuted at `applicable=false, constraintActive=true, "
                     "base=[⟨7,0⟩]` (a non-qualifying candidate): the spec keeps it "
                     "(length 1), the rival drops it (length 0). Isolates the "
                     "`applicable=false` sub-domain no other rival probes.",
        "witness": _witness("false", "true", "[⟨7,0⟩]"),
    },
    {
        "id": "ignore-constraint-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Narrow whenever the field is applicable, IGNORING the constraint-present
        # gate. Correct whenever `constraintActive` is true; wrong when it is
        # false and the collection must be returned unchanged. Attacks the
        # `constraintActive` gate binder.
        "module": _with_impl(
            "def implementation_applyChoiceLimit\n"
            "    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=\n"
            "  Id.run do\n"
            "    let mut queryset := base\n"
            "    if applicable then\n"
            "      queryset := queryset.filter qualifies\n"
            "    return queryset"),
        "refinement": "a faithful real patch that narrowed even when no constraint is "
                      "present would filter a collection that must be returned "
                      "unchanged, dropping candidates the field is required to offer "
                      "when there is nothing to narrow by; the no-constraint behavior "
                      "the PASS_TO_PASS suite relies on would break, so it does NOT "
                      "resolve.",
        "rationale": "REJECT from the `constraintActive` gate: the spec returns "
                     "`base` unchanged when `constraintActive=false`, but the rival "
                     "still filters. Refuted at `applicable=true, "
                     "constraintActive=false, base=[⟨7,0⟩]` (a non-qualifying "
                     "candidate): the spec keeps it (length 1), the rival drops it "
                     "(length 0). Isolates the `constraintActive=false` sub-domain.",
        "witness": _witness("true", "false", "[⟨7,0⟩]"),
    },
    {
        "id": "keep-head-unconditionally",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain near-miss: when both gates hold, filter the TAIL but keep
        # the head candidate unconditionally. Correct whenever the head qualifies
        # (or the collection is empty); wrong when the head is non-qualifying —
        # it re-introduces an ineligible candidate. A membership near-miss the
        # invert rival does not subsume, so it carries its own input.
        "module": _with_impl(
            "def implementation_applyChoiceLimit\n"
            "    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=\n"
            "  Id.run do\n"
            "    let mut queryset := base\n"
            "    if applicable then\n"
            "      if constraintActive then\n"
            "        queryset := match queryset with\n"
            "          | [] => []\n"
            "          | h :: t => h :: t.filter qualifies\n"
            "    return queryset"),
        "refinement": "a faithful real patch that special-cased the first candidate "
                      "(offering it even when it does not satisfy the constraint) "
                      "would OFFER an ineligible candidate whenever the leading "
                      "candidate fails the constraint; the F2P asserts only eligible "
                      "candidates appear and would FAIL — it does NOT resolve.",
        "rationale": "partial-domain: correct on every input whose head qualifies "
                     "(or is empty), WRONG when the head is non-qualifying. REJECT "
                     "from the membership clause of `result = base.filter qualifies` "
                     "(both gates true). Refuted at `base=[⟨7,0⟩]` (a non-qualifying "
                     "head): the spec drops it (length 0), the rival keeps it "
                     "(length 1). A near-miss the invert rival (which drops matching "
                     "candidates) does not subsume, so it carries its own input.",
        "witness": _witness("true", "true", "[⟨7,0⟩]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 3 value/uniqueness rivals) plus
# a 2-case AXIOM lane. The nagini sibling models a SINGLE function
# `offered_options(matches: List[int])` whose whole job is duplicate elimination
# over one input list; this lean bundle models the SAME observable behavior but
# with its two GATES made explicit (`applicable`, `constraintActive`) and the
# duplicate-collapse expressed as a `List.filter` over a per-candidate match
# count. Every sibling case is recorded below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-reorder                     -> pos-reorder-gates          RE-EXPRESSED
#   pos-reshape                     -> pos-direct-forward         RE-EXPRESSED
#   admiss-stream                   -> admiss-f2p-shaped-narrowing PORTED
#   frame-write-matches             -> (none)                     VACUOUS (no heap)
#   keep-all-raw-stream             -> join-multiplicity          PORTED
#   invert-guard-drop-singletons    -> invert-membership          PORTED
#   partial-keep-first              -> keep-head-unconditionally   PORTED
#   (n/a in nagini — no gate inputs) -> ignore-applicable-gate    ADDED
#   (n/a in nagini — no gate inputs) -> ignore-constraint-gate    ADDED
#   AXIOM_TESTS (2)                 -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (positives): the sibling's two positives reshape ONE input's
#   dedup loop (branch reorder; hoist the membership test into a local). Here the
#   ARGUMENT ("a structurally different but faithful impl must verify") is carried
#   by (a) collapsing the mutable-do narrowing into a direct conditional
#   (pos-direct-forward) and (b) nesting the two gates in the opposite order
#   (pos-reorder-gates). Both keep the frozen `cases … <;> rfl` proof and verify.
# PORTED (admissibility) — was recorded VACUOUS here, corrected by audit. The
#   sibling self-calls to prove its `Requires` admits an F2P-shaped input.
#   `correct_applyChoiceLimit` has no precondition hypothesis (the `∀` is
#   unguarded — the behavior is total), and the earlier revision inferred vacuity
#   from that alone. That is not a demonstration: on a total carrier the lane's
#   question becomes "is the obligation SATISFIABLE at an F2P-shaped input", which
#   `admiss-f2p-shaped-narrowing` answers by discharging the spec predicate by
#   evaluation at several candidates each matching through more than one related
#   row, then closing the frozen obligation verbatim. Real builds: it VERIFIES
#   against the frozen impl, and each of its three ground `have`s FAILS on its own
#   line against the pre-patch impl (whose baseline fails only in the frozen
#   `rfl`), so the lane is neither vacuous nor decorative.
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because `matches`
#   is held at Acc(.,1/2) an impl can illegally write. This backend is
#   referentially transparent — `base` is an immutable value with no heap
#   footprint or aliasing — so there is no read-only input to overwrite. Not
#   fabricated (porting map: vacuous here).
# PORTED (value rivals): keep-all-raw-stream (return the raw duplicate-laden
#   stream) ports as join-multiplicity — on this carrier "keep every duplicate"
#   is exactly listing a candidate once per satisfying related row
#   (`flatMap (List.replicate matchRows)`), the literal pre-patch impl.
#   invert-guard-drop-singletons ports as invert-membership (keep iff NOT
#   qualifying). partial-keep-first ports as keep-head-unconditionally (filter the
#   tail, keep the head regardless).
# ADDED (gate rivals): the nagini surface has NO gate inputs (its single function
#   always dedups its one argument), so it has no counterpart for attacking the
#   two gates this bundle models explicitly. ignore-applicable-gate and
#   ignore-constraint-gate attack the `applicable=false` / `constraintActive=false`
#   sub-domains respectively — coverage of the surface THIS bundle models, per the
#   porting guidance (cover what this carrier models, not nagini parity).
#
#   The five witnesses probe five DISTINCT input tuples; across them `applicable`
#   takes {true,false}, `constraintActive` takes {true,false}, and `matchRows`
#   takes {0,1,2}. Every gate binder is varied (so none is pinned) and shown
#   load-bearing by a rival that mishandles it; the membership and at-most-once
#   sub-clauses of the single equality clause are each attacked. `Candidate.id`
#   is held constant (7): the modeled behavior never inspects it (`qualifies`
#   reads only `matchRows`), so it is a genuinely irrelevant identity carrier, not
#   an untested binder (see the DEFENDED-SURFACE note).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the narrowing is a directive-8-grounded filter over input fields, not an
# oracle), so there is nothing to probe and the gate ignores AXIOM_TESTS anyway.
AXIOM_TESTS = []
