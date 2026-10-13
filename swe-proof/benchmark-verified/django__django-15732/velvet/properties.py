"""properties.py — G-PBT falsification battery for django__django-15732 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the single
``-- impl-start`` / ``-- impl-end`` region, or the ``prove_correct`` tactic
body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct chooseTarget`` obligation
survives with a byte-identical statement) and swaps in a candidate impl. It is
checked by the real verifier: ``expect="verify"`` passes iff (in scope AND
verifies); ``expect="reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates — the witness must ELABORATE against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE. ONE contracted method — a decision that reduces a set of
candidate identifiers discovered for some target columns to the single one the
operation may act on, or reports that no single target exists:

  chooseTarget (names : List String) (uniqueSel allowMultiple : Bool)
      (canonical : String) return (out : Option String)
    ensures out = selectedTarget names uniqueSel allowMultiple canonical

where ``selectedTarget`` first NARROWS the candidate list to the canonical
identifier — but only when selection is by uniqueness AND the candidate set is
non-empty AND several co-located selectors are permitted at once AND the
canonical identifier is itself among the candidates — and then yields the sole
element of the narrowed list (``some``) when it is a singleton, else ``none``.
``narrowed``/``selectedTarget`` are total ``def``s over the method's own
arguments in the ``pure`` region; the ``axioms`` region is EMPTY (mapping.md
§3 — every helper result is consumed only as a value, nothing is axiomatized),
so there is no opaque answer-key a wrong impl could ECHO. The single ensures
clause carries three independently-attackable structural pieces:

  (C1) the narrowing GUARD ``uniqueSel = true ∧ names ≠ [] ∧ allowMultiple
       = true``. TWO of its three conjuncts are observably load-bearing and
       each carries its own rival (``weak-ignore-unique-sel``,
       ``weak-ignore-allow-multiple``). The third, ``names ≠ []``, is NOT:
       dropping it changes no output, because on ``names = []`` the narrowing
       would rewrite ``[]`` to ``[canonical]`` only if ``canonical ∈ []``,
       which is false, so the guard's non-emptiness test is subsumed by the
       membership test that follows it. That is a measured fact, not an
       assumption — the drop-it impl VERIFIES (exit 0), and it is carried
       below as the positive control ``pos-drop-vacuous-conjunct`` rather than
       as a rival. A rival attacking that conjunct is therefore impossible on
       this carrier, and claiming one would be a fabricated attack;
  (C1m) the guard's MEMBERSHIP test ``canonical ∈ names`` — narrowing applies
       only when the canonical identifier is itself among the candidates.
       Independent of the three conjuncts above and separately attackable
       (``weak-narrow-ignores-membership``);
  (C2) the narrowing TARGET: when the guard holds and the canonical identifier
       is a candidate, the set collapses to exactly ``[canonical]`` (not some
       other single element), and it collapses AT ALL
       (``weak-skip-narrowing``);
  (C3) the SINGLETON reduction: the result is the sole narrowed element
       (``some ns[0]``) iff the narrowed set is a singleton, else ``none`` —
       a non-singleton must NOT silently pick an arbitrary element.

CARRIER NARROWING vs the nagini sibling. Nagini contracts
``select_constraint_to_remove(candidates, default_name, unique, feature_on)
-> int`` and models BOTH selection directions in one value+exception carrier:
a NORMAL return (a chosen ``int``) and a REFUSAL (``AmbiguousConstraintSelection``
raised). This bundle re-sites the same decision onto ``Option String``:
``some n`` ↔ "act on identifier ``n``" (the nagini normal return),
``none`` ↔ "no single target ⇒ the operation cannot proceed" (the nagini
refusal). The nagini ``default_name`` maps to ``canonical``, ``unique`` to
``uniqueSel``, ``feature_on`` to ``allowMultiple``, ``candidates`` to
``names``; nagini's grounded ``disambiguates(unique, feature_on, n)`` helper
maps onto the ``narrowed`` guard (with the added ``canonical ∈ names`` member
test that nagini folded into its narrowing branch). See the module footer for
the full per-case port accounting.

INPUT BINDERS varied by the reject witnesses: ``names`` (length 1 vs 2),
``uniqueSel`` (true vs false), ``allowMultiple`` (true vs false), ``canonical``
("a" vs "b" vs "x", and both in-``names`` and out-of-``names``). No binder is
held at one value across all rivals, so each is demonstrably load-bearing
rather than assumed.

ADMISSIBILITY on a total, precondition-free carrier. ``chooseTarget`` has an
empty ``pre-conditions`` region, so "a normal input satisfies the precondition"
is vacuous — nothing could exclude an input. The residual PRECOND-TOO-STRONG
risk here is the obligation being UNSATISFIABLE or DEGENERATE at exactly the
interesting input: a post-image that no impl can meet, or one that collapses to
a constant, is indistinguishable from a spec that tests nothing.
``admiss-f2p-nondegenerate`` discharges that BY EVALUATION as an in-region
``assert`` at the shaped input the reject lane's rivals do not jointly pin, and
only then closes the frozen obligation with the frozen impl. The assert is
LIVE, not decoration: the identical case with its first conjunct changed to the
non-narrowing image leaves an unsolved goal (measured, exit 1).

FRAME / PERMISSION-MUTATION — VACUOUS on this backend. On nagini ``candidates``
carries a fractional read-only heap permission and a rival that WRITES it must
be rejected for insufficient permission (the sibling's MANDATORY #1 weakness
class). Lean and Velvet are referentially transparent: every method input is an
immutable value, there is no heap, no aliasing and no fractional permission, and
``chooseTarget`` declares no ``mut`` binder on any input. There is no read-only
input to overwrite and thus no discriminating witness could exist. Not
fabricated, not substituted — reported as vacuous.

CONTROL-FLOW-EFFECT — N/A, exactly as on nagini: the only observable difference
between branches is WHICH identifier is selected versus that selection yields
``none``, and the ``Option String`` value abstraction captures both directions.
There is no side-effect / capability channel invisible to the value model.

AXIOM lane: DROPPED. The axiom lane is G-AX's job; this bundle declares no
``axiom`` and axiomatizes no callee (mapping.md §3), so the nagini
``ax-ref-select-equals-gold`` A-reference probe has no counterpart. The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15732"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors — each lies wholly inside the impl region and is unique in the
# file (both facts asserted below). The frozen spec (method signature, ensures,
# the `pure`/`axioms` regions) is never touched, so `same_spec` holds and the
# `prove_correct chooseTarget` obligation survives byte-identically.
# ---------------------------------------------------------------------------
_IMPL = (
    "    let mut ns := names\n"
    "    if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then\n"
    "      if canonical ∈ ns then\n"
    "        ns := [canonical]\n"
    "    let result : Option String := if ns.length = 1 then ns[0]? else none\n"
    "    return result\n"
)
_GUARD = "    if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then\n"
_NARROW = "        ns := [canonical]\n"
_MEMBER = "      if canonical ∈ ns then\n        ns := [canonical]\n"
_RESULT = "    let result : Option String := if ns.length = 1 then ns[0]? else none\n"

# The frozen tactic body, verbatim. It lives in the region the consumer spec view
# elides, so a case may RETUNE it (a correct reshape legitimately reproves) while
# `same_spec` and the `prove_correct chooseTarget` header stay byte-identical.
# Only the two cases that need it touch this; every rival leaves it alone, so the
# rival module fails to build — and the `witness`, never the module build, is what
# attributes that rejection to the spec.
_PROOF = ("prove_correct chooseTarget by\n"
          "  loom_solve <;>\n"
          "    simp_all [narrowed, selectedTarget] <;>\n"
          "    split_ifs <;>\n"
          "    simp_all")

for _a in (_IMPL, _GUARD, _NARROW, _MEMBER, _RESULT, _PROOF):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery.
# ---- `chooseTargetTester args = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. The carrier is fully transparent (no opaque callee),
# ---- so every witness `decide`s in the kernel — no hypothesis-conditioning is
# ---- needed, hence no consistency obligation to satisfy.
_TESTER = (
    "extract_program_for chooseTarget\n"
    "prove_precondition_decidable_for chooseTarget\n"
    "prove_postcondition_decidable_for chooseTarget\n"
    "derive_tester_for chooseTarget\n\n"
)


def _wit(example):
    return _TESTER + example


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl of the modeled
    # decision cannot verify, the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-commute-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the narrowing guard's three independent conjuncts are
        # commuted (allowMultiple, non-empty, uniqueSel) — logically identical
        # to the frozen conjunction, so the narrowed set and the result are the
        # same on every input. The frozen tactic body closes it unchanged.
        "module": _swap(
            _BASE, _GUARD,
            "    if allowMultiple = true ∧ ns ≠ [] ∧ uniqueSel = true then\n"),
        "rationale": "the narrowing guard (C1) is a conjunction of three "
                     "independent conditions; commuting them leaves the guard's "
                     "truth value unchanged at every input, so the narrowed set "
                     "and the selected result are identical to gold and "
                     "`out = selectedTarget …` still discharges. If it FAILS => "
                     "SPEC-TOO-STRONG (the postcondition would be over-fit to the "
                     "conjunct ORDER).",
    },
    {
        "id": "pos-direct-select",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the `mut` accumulator and the nested `if`, computing the
        # narrowed set in one straight-line `let ... := if ... then ... else`
        # ladder that mirrors `narrowed` exactly, then the same singleton
        # reduction. Semantically identical to gold; the frozen tactic body
        # closes it.
        "module": _swap(
            _BASE, _IMPL,
            "    let ns : List String :=\n"
            "      if uniqueSel = true ∧ names ≠ [] ∧ allowMultiple = true then\n"
            "        if canonical ∈ names then [canonical] else names\n"
            "      else names\n"
            "    let result : Option String := if ns.length = 1 then ns[0]? else none\n"
            "    return result\n"),
        "rationale": "a straight-line reshape that computes the narrowed set in a "
                     "single `if/else` ladder (no `mut` accumulator, no nested "
                     "`if`) mirroring `narrowed` on the nose, then the same "
                     "singleton reduction. Same value for every input, so "
                     "`out = selectedTarget …` still discharges. If it FAILS => "
                     "SPEC-TOO-STRONG (the postcondition would be over-fit to the "
                     "mutable-accumulator SHAPE).",
    },
    {
        "id": "pos-match-singleton",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the singleton reduction is written as a PATTERN MATCH on the
        # narrowed list (`| [x] => some x | _ => none`) instead of a length test
        # plus `ns[0]?`. Observationally identical at every input, but no longer
        # definitionally equal to `selectedTarget`'s own `if ns.length = 1 then
        # ns[0]?` form, so the frozen tactic body does NOT close it (measured,
        # exit 1: `unsolved goals ... ⊢ (match names with | [x] => some x | x =>
        # none) = none`). It is reproven by case-splitting the list to arity two
        # in the elided tactic body — which is exactly what a legitimate reshape
        # is allowed to do, and what makes this the case that shows the spec is
        # about VALUES rather than about the frozen impl's decision syntax.
        "module": _swap(
            _swap(_BASE, _RESULT,
                  "    let result : Option String := match ns with\n"
                  "      | [x] => some x\n"
                  "      | _ => none\n"),
            _PROOF,
            "prove_correct chooseTarget by\n"
            "  loom_solve\n"
            "  all_goals (try simp_all [narrowed, selectedTarget])\n"
            "  all_goals (try split_ifs)\n"
            "  all_goals\n"
            "    match names with\n"
            "    | [] => simp_all\n"
            "    | [x] => simp_all\n"
            "    | x :: y :: r => simp_all\n"),
        "rationale": "the STRONGEST soundness control in the battery: the "
                     "singleton reduction (C3) is rewritten as a pattern match on "
                     "the narrowed list rather than a length test plus indexed "
                     "lookup. Unlike the other two positives this is NOT closed by "
                     "the frozen tactic body — the two forms are observationally "
                     "equal but not definitionally equal, so the reshape is only "
                     "admitted after being REPROVEN by a list case-split (the "
                     "tactic body is elided from the spec view; the obligation "
                     "header and `same_spec` are untouched). If it FAILED => "
                     "SPEC-TOO-STRONG: the spec would be pinning the frozen impl's "
                     "decision SYNTAX rather than its value.",
    },
    {
        "id": "pos-drop-vacuous-conjunct",
        "kind": "soundness",
        "expect": "verify",
        # The `names ≠ []` conjunct of the guard is dropped. This is a CORRECT
        # impl, not a rival, and that is the point: on `names = []` the narrowing
        # branch can only fire if `canonical ∈ []`, which is false, so the
        # non-emptiness test is subsumed by the membership test that follows and
        # dropping it changes no output at any input. Carried as a positive so the
        # header's C1 claim is bounded by a machine-checked fact instead of the
        # symmetric-sounding assumption that all three conjuncts are attackable.
        "module": _swap(
            _BASE, _GUARD,
            "    if uniqueSel = true ∧ allowMultiple = true then\n"),
        "rationale": "the guard's `names ≠ []` conjunct is REDUNDANT on this "
                     "carrier, and this case pins that as a measured fact: on the "
                     "empty candidate set the narrowing fires only when "
                     "`canonical ∈ []`, which is false, so the non-emptiness test "
                     "is subsumed by the membership test and the impl without it "
                     "is observationally identical to gold at every input. It "
                     "therefore MUST verify (it does, and the frozen tactic body "
                     "closes it unchanged). Its job is negative: it demonstrates "
                     "why no `weak-ignore-nonempty` rival exists, so the absence of "
                     "one is a carrier fact rather than a coverage gap. If it "
                     "FAILED => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — ported from the sibling's admiss-selfcall and RE-AIMED.
    # `chooseTarget` has no precondition, so "a normal input is admissible" is
    # vacuous; the residual PRECOND-TOO-STRONG risk on a total carrier is the
    # obligation being unsatisfiable / degenerate at exactly the interesting
    # input. Discharged by EVALUATION as an in-region `assert` before the frozen
    # obligation is closed verbatim with the frozen impl.
    # =====================================================================
    {
        "id": "admiss-f2p-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The shaped point: several co-located candidate identifiers discovered
        # for the target columns, one of them the canonical one, selection by
        # uniqueness, co-located selectors permitted. The assert pins the
        # post-image there to `some "c_t"` and pins it AWAY from both degenerate
        # collapses — `none` (the spec demanding refusal at the very input the
        # narrowing exists to resolve) and `some "c_a"` (the spec being satisfied
        # by picking the non-canonical candidate). A post-image that collapsed
        # either way would fail this. LIVE, not decoration: the identical case
        # with the first conjunct changed to `= some "c_a"` leaves an unsolved
        # goal (measured, exit 1). The impl is kept verbatim so the method's own
        # `ensures` still discharges; only the elided tactic body gains a `decide`
        # arm for the extra assert goal.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    assert (with_name_prefix `admiss\n"
                  "      (selectedTarget [\"c_a\", \"c_t\"] true true \"c_t\" = some \"c_t\"\n"
                  "        ∧ selectedTarget [\"c_a\", \"c_t\"] true true \"c_t\" ≠ none\n"
                  "        ∧ selectedTarget [\"c_a\", \"c_t\"] true true \"c_t\" ≠ some \"c_a\"))\n"
                  + _IMPL),
            _PROOF,
            "prove_correct chooseTarget by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (simp_all [narrowed, selectedTarget] <;> split_ifs <;> simp_all)"),
        "rationale": "ADMISSIBILITY on a precondition-free total carrier: the "
                     "obligation must be SATISFIABLE and non-degenerate at a "
                     "shaped input, else it is PRECOND-TOO-STRONG in the only "
                     "sense this backend can express (a post-image no impl can "
                     "meet is indistinguishable from one every impl meets). "
                     "Discharged by evaluation at `names=[\"c_a\",\"c_t\"], "
                     "uniqueSel=true, allowMultiple=true, canonical=\"c_t\"` — "
                     "several co-located candidates, one canonical — where the "
                     "assert pins the image to `some \"c_t\"` and away from both "
                     "collapses (`none`, i.e. refusal at the input the narrowing "
                     "exists to resolve; and `some \"c_a\"`, i.e. the "
                     "non-canonical candidate). This is also the only case in the "
                     "battery that pins the POSITIVE image at the narrowing point "
                     "rather than pinning a rival's wrong one. If it FAILS => "
                     "PRECOND-TOO-STRONG / degenerate obligation.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument for why its faithful real
    # counterpart would still leave the F2P failing.
    # =====================================================================
    {
        "id": "weak-arbitrary-on-multi",
        "kind": "uniqueness",
        "expect": "reject",
        # THE atk-hole the issue forbids (nagini's weak-arbitrary-on-multi): on
        # a non-resolvable candidate set (several names, no narrowing) the rival
        # returns the FIRST candidate (`some ns[0]`) rather than reporting no
        # single target. Right whenever the narrowed set is already a singleton;
        # wrong on any multi-candidate non-narrowed set.
        "module": _swap(
            _BASE, _RESULT,
            "    let result : Option String := ns[0]?\n"),
        "refinement": "this is exactly the silent-arbitrary-selection behaviour "
                      "the issue forbids: on a set of several discovered "
                      "identifiers with no narrowing applicable, it picks the "
                      "first and acts on it instead of refusing. A faithful patch "
                      "doing this would act on an arbitrary/independent "
                      "constraint rather than raising the 'wrong number of "
                      "constraints' error the repo raises here, so it would "
                      "target the wrong object and NOT resolve — a "
                      "verify-not-resolve break.",
        "rationale": "REJECT from clause C3 (the singleton reduction): with a "
                     "non-singleton narrowed set the spec demands `none`, but the "
                     "rival returns `some ns[0]`. PARTIAL-DOMAIN: correct only "
                     "when the narrowed set is already a singleton. Refuted at "
                     "`names=[\"a\",\"b\"], uniqueSel=false, allowMultiple=false, "
                     "canonical=\"x\"` (no narrowing, len 2): gold=none, "
                     "rival=some \"a\". If it VERIFIES => SPEC-TOO-WEAK "
                     "(the refusal path is not pinned).",
        "witness": _wit(
            'example : chooseTargetTester ["a", "b"] false false "x" = false := by\n'
            "  decide\n"),
    },
    {
        "id": "weak-wrong-narrow-pick",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks clause C2 (the narrowing TARGET). On the narrowing branch the
        # rival collapses the candidate set to its FIRST element (`ns.take 1`)
        # instead of to the canonical identifier. When the canonical identifier
        # is a candidate but NOT first, `ns.take 1` selects the wrong one.
        "module": _swap(
            _BASE, _NARROW,
            "        ns := ns.take 1\n"),
        "refinement": "narrowing to the first discovered identifier rather than "
                      "the canonical one is the wrong-target bug: in the F2P "
                      "scenario the discovered set contains an independent "
                      "single-column selector plus the canonical one, and picking "
                      "the first would act on the INDEPENDENT object instead of "
                      "the intended one. A faithful patch doing this fails the "
                      "F2P test (it removes the user's standalone constraint, not "
                      "the composed one) — verify-not-resolve.",
        "rationale": "REJECT from clause C2: on the narrowing branch the spec "
                     "collapses the set to `[canonical]`, but the rival collapses "
                     "it to `ns.take 1`, which equals `[canonical]` only when the "
                     "canonical identifier happens to be FIRST. Refuted at "
                     "`names=[\"a\",\"b\"], uniqueSel=true, allowMultiple=true, "
                     "canonical=\"b\"`: gold narrows to [\"b\"] => some \"b\"; "
                     "rival takes [\"a\"] => some \"a\". If it VERIFIES => "
                     "SPEC-TOO-WEAK (the narrowing target is not pinned).",
        "witness": _wit(
            'example : chooseTargetTester ["a", "b"] true true "b" = false := by\n'
            "  decide\n"),
    },
    {
        "id": "weak-invented-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks clause C3 / membership (nagini's weak-invented-name): on the
        # singleton path the rival returns `some canonical` instead of the sole
        # narrowed element. When the single discovered candidate is NOT the
        # canonical identifier, this targets an identifier that was never
        # discovered.
        "module": _swap(
            _BASE, _RESULT,
            "    let result : Option String := if ns.length = 1 then some canonical else none\n"),
        "refinement": "returning the canonical identifier on the sole-candidate "
                      "path targets a name that was never discovered for the "
                      "target columns when the single candidate is an independent "
                      "one whose name differs from the canonical scheme. A "
                      "faithful patch doing this would emit an operation against a "
                      "non-existent / wrong object and fail the migration tests — "
                      "verify-not-resolve.",
        "rationale": "REJECT from clause C3 (the singleton reduction selects the "
                     "sole NARROWED element `ns[0]`, which for a non-narrowed "
                     "singleton is the discovered candidate — a member of "
                     "`names`): the rival returns `some canonical`, which need "
                     "not be in `names`. Refuted at `names=[\"a\"], "
                     "uniqueSel=false, allowMultiple=false, canonical=\"b\"`: "
                     "gold=some \"a\", rival=some \"b\" (an undiscovered name). "
                     "If it VERIFIES => SPEC-TOO-WEAK (a selection could target an "
                     "undiscovered identifier).",
        "witness": _wit(
            'example : chooseTargetTester ["a"] false false "b" = false := by\n'
            "  decide\n"),
    },
    {
        "id": "weak-ignore-allow-multiple",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks clause C1 — specifically the `allowMultiple = true` conjunct of
        # the narrowing guard. The rival drops it, so it narrows even when
        # co-located selectors are NOT permitted. This is the binder the F2P is
        # guarded on (@skipUnlessDBFeature); a rival that ignores it would narrow
        # on a backend where it must not.
        "module": _swap(
            _BASE, _GUARD,
            "    if uniqueSel = true ∧ ns ≠ [] then\n"),
        "refinement": "narrowing without checking that the backend permits "
                      "several selectors on the same fields would apply the "
                      "narrowing on backends where it is unsafe — the exact "
                      "feature the change is guarded on. A faithful patch "
                      "dropping this guard narrows on a backend that does not "
                      "allow multiple constraints, changing behaviour outside the "
                      "intended envelope, so it would not be an equivalent, "
                      "resolving patch — verify-not-resolve.",
        "rationale": "REJECT from clause C1 (the `allowMultiple = true` conjunct "
                     "of the guard): with `allowMultiple=false` the spec must NOT "
                     "narrow, but the rival does. Refuted at `names=[\"a\",\"b\"], "
                     "uniqueSel=true, allowMultiple=false, canonical=\"a\"`: gold "
                     "leaves the len-2 set (=> none); rival narrows to [\"a\"] "
                     "(=> some \"a\"). This is the ONLY rival that varies "
                     "`allowMultiple` off `false`-blindness, so its dependence is "
                     "demonstrated. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _wit(
            'example : chooseTargetTester ["a", "b"] true false "a" = false := by\n'
            "  decide\n"),
    },
    {
        "id": "weak-ignore-unique-sel",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks clause C1 — specifically the `uniqueSel = true` conjunct. The
        # rival drops it, so it narrows even when selection is NOT by uniqueness.
        # This is the binder that distinguishes the unique_together-delete caller
        # from other callers of the same operation.
        "module": _swap(
            _BASE, _GUARD,
            "    if ns ≠ [] ∧ allowMultiple = true then\n"),
        "refinement": "narrowing when selection is not by uniqueness would apply "
                      "the canonical-name narrowing to callers it was never "
                      "intended for, changing behaviour outside the modeled "
                      "caller. A faithful patch dropping this conjunct would "
                      "narrow for the wrong caller class and is not an "
                      "equivalent, resolving patch — verify-not-resolve.",
        "rationale": "REJECT from clause C1 (the `uniqueSel = true` conjunct of "
                     "the guard): with `uniqueSel=false` the spec must NOT "
                     "narrow, but the rival does. Refuted at `names=[\"a\",\"b\"], "
                     "uniqueSel=false, allowMultiple=true, canonical=\"a\"`: gold "
                     "leaves the len-2 set (=> none); rival narrows to [\"a\"] "
                     "(=> some \"a\"). This is the ONLY rival that varies "
                     "`uniqueSel` off `true`, so its dependence is demonstrated. "
                     "If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _wit(
            'example : chooseTargetTester ["a", "b"] false true "a" = false := by\n'
            "  decide\n"),
    },
    {
        "id": "weak-skip-narrowing",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks clause C2 at its root: the rival performs NO narrowing at all —
        # the candidate set flows straight into the singleton reduction. This is
        # the behaviour the change replaces, and it is the one rival the ported
        # battery lacked: every other rival narrows and then gets some DETAIL of
        # the narrowing wrong, so a spec that demanded narrowing only weakly would
        # have gone undetected. Correct on every input where the candidate set is
        # already a singleton or where narrowing does not apply; wrong at exactly
        # the shaped point.
        "module": _swap(
            _BASE, _IMPL,
            "    let ns := names\n"
            "    let result : Option String := if ns.length = 1 then ns[0]? else none\n"
            "    return result\n"),
        "refinement": "an implementation that never narrows leaves the operation "
                      "unable to proceed whenever the target columns carry several "
                      "co-located selectors — which is precisely the situation the "
                      "F2P scenario constructs, and precisely the situation whose "
                      "failure the issue reports. A faithful patch that omits the "
                      "narrowing step is behaviourally the unpatched code: it still "
                      "reports 'wrong number of constraints' for the reported "
                      "input, so the F2P test still fails. It is not a "
                      "verify-not-resolve break but a NOT-EVEN-VERIFY one, which is "
                      "why the spec must reject it.",
        "rationale": "REJECT from clause C2 taken at its root (the narrowing "
                     "happens AT ALL): with the guard satisfied and the canonical "
                     "identifier among the candidates the spec collapses the set to "
                     "`[canonical]` and yields `some canonical`, but the rival "
                     "returns `none` because the un-narrowed set has length 2. "
                     "PARTIAL-DOMAIN: correct wherever narrowing is inapplicable. "
                     "Refuted at `names=[\"a\",\"b\"], uniqueSel=true, "
                     "allowMultiple=true, canonical=\"a\"`: gold=some \"a\", "
                     "rival=none. Note the OPPOSITE direction from every other "
                     "rival here: the others wrongly select where the spec refuses, "
                     "this one wrongly refuses where the spec selects, so both "
                     "directions of the decision are pinned. If it VERIFIES => "
                     "SPEC-TOO-WEAK (the narrowing step is not required at all, and "
                     "the spec would be satisfied by the pre-change behaviour).",
        "witness": _wit(
            'example : chooseTargetTester ["a", "b"] true true "a" = false := by\n'
            "  decide\n"),
    },
    {
        "id": "weak-narrow-ignores-membership",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks clause C1m — the guard's `canonical ∈ names` MEMBERSHIP test,
        # the one guard component with no rival in the ported battery (the port
        # attacked two of the three plain conjuncts and left the membership test
        # unprobed). The rival narrows unconditionally once the three conjuncts
        # hold, so when the canonical identifier was NOT among the discovered
        # candidates it fabricates a set containing only it.
        "module": _swap(
            _BASE, _MEMBER,
            "      ns := [canonical]\n"),
        "refinement": "narrowing to the canonical identifier without first "
                      "checking that it is among the identifiers actually "
                      "discovered for the target columns makes the operation act on "
                      "an object that does not exist on those columns whenever the "
                      "discovered set is composed of independent selectors under "
                      "other names. A faithful patch dropping that check emits an "
                      "operation against an absent object — it would fail the "
                      "migration tests rather than resolve them, so it is "
                      "verify-not-resolve.",
        "rationale": "REJECT from clause C1m (the guard's `canonical ∈ names` "
                     "member test): the spec narrows only when the canonical "
                     "identifier is itself a candidate, but the rival narrows "
                     "unconditionally, so it can yield an identifier that appears "
                     "nowhere in `names`. Refuted at `names=[\"a\",\"b\"], "
                     "uniqueSel=true, allowMultiple=true, canonical=\"x\"`: gold "
                     "leaves the len-2 set (=> none); rival narrows to [\"x\"] (=> "
                     "some \"x\", an identifier that was never discovered). This is "
                     "the ONLY rival that puts `canonical` OUTSIDE `names` on the "
                     "narrowing branch, so the member test's role is demonstrated "
                     "rather than assumed. If it VERIFIES => SPEC-TOO-WEAK (the "
                     "narrowing could target an undiscovered identifier).",
        "witness": _wit(
            'example : chooseTargetTester ["a", "b"] true true "x" = false := by\n'
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet port accounting. The nagini sibling has 7 SPEC cases
# (2 soundness positives + 1 admissibility + 4 uniqueness rivals, one of which
# is the mandatory frame-mutation rival) plus 1 AXIOM case. This bundle is a
# CARRIER NARROWING onto `Option String`: nagini's value+exception carrier
# (a chosen int OR AmbiguousConstraintSelection raised) becomes `some n` /
# `none`, and nagini's grounded `disambiguates(unique, feature_on, n)` maps onto
# the `narrowed` guard (extended with the `canonical ∈ names` member test).
#
#   sibling case               -> here                        disposition
#   -------------------------------------------------------------------------
#   pos-control-reorder        -> pos-commute-guard            PORTED (re-shaped:
#       the sibling reorders the two RETURN checks; the frozen impl here has no
#       two-return shape to reorder — the narrow-first/sole-count ordering is
#       fused into `selectedTarget` — so the cheapest faithful reshape that
#       exercises "not over-fit to a syntactic order" is commuting the guard's
#       independent conjuncts, which is order-invariance of the same kind)
#   pos-control-single-return  -> pos-direct-select            PORTED (the sibling
#       collapses two early returns + raise into one local; here the analogous
#       cheapest reshape drops the `mut` accumulator and nested `if` for a single
#       straight-line `if/else` ladder returning once)
#   admiss-selfcall            -> admiss-f2p-nondegenerate     PORTED, RE-AIMED
#       (the sibling probes that a fresh F2P-shaped input satisfies a fractional
#       -permission Requires; this method has no precondition at all, so the
#       analogue on a total carrier is the obligation being SATISFIABLE and
#       non-degenerate at that same shaped input, discharged by evaluation as an
#       in-region assert before the frozen obligation is closed verbatim)
#   frame-mutate-candidates    -> (none)                       VACUOUS (see below)
#   weak-arbitrary-on-multi    -> weak-arbitrary-on-multi      PORTED (the atk-hole:
#       silent arbitrary selection on a non-resolvable set; attacks C3)
#   weak-wrong-disambig-pick   -> weak-wrong-narrow-pick       PORTED (wrong element
#       chosen on the narrowing branch; attacks C2)
#   weak-invented-name         -> weak-invented-name           PORTED (a name never
#       discovered is selected on the singleton path; attacks C3/membership)
#
# ADDED (5, no direct sibling counterpart) for CLAUSE + BINDER coverage of the
#   guard, which on velvet is an explicit three-conjunct condition inside the
#   single ensures clause (nagini folded the analogous predicate into the opaque
#   @Pure `disambiguates`, so its individual conjuncts had no per-rival attack):
#     weak-ignore-allow-multiple — drops the `allowMultiple = true` conjunct of
#         C1; the ONLY rival that varies `allowMultiple`. This is the backend
#         feature the F2P is guarded on (@skipUnlessDBFeature), so its role in
#         the guard is load-bearing and needs its own rival.
#     weak-ignore-unique-sel — drops the `uniqueSel = true` conjunct of C1; the
#         ONLY rival that varies `uniqueSel`. This distinguishes the
#         unique-selection caller from other callers of the same operation.
#     weak-skip-narrowing — performs NO narrowing at all (clause C2 at its root).
#         The only rival that errs in the REFUSE-where-the-spec-SELECTS
#         direction; every other rival errs the other way, so without it one of
#         the two directions of the decision was unpinned and a spec that
#         required narrowing only weakly would have passed.
#     weak-narrow-ignores-membership — drops the guard's `canonical ∈ names`
#         member test (C1m). The only rival that places `canonical` OUTSIDE
#         `names` on the narrowing branch.
#   Plus two positives with no sibling counterpart: pos-match-singleton (a
#   reshape the frozen tactic body does NOT close, so it must be REPROVEN — the
#   only case here that shows the spec pins the value rather than the frozen
#   decision syntax) and pos-drop-vacuous-conjunct (see below).
#
# ONE C1 CONJUNCT IS NOT ATTACKABLE, and this is recorded as a measured fact
#   rather than a coverage gap. Dropping `names ≠ []` from the guard yields an
#   impl that VERIFIES (exit 0): on the empty candidate set the narrowing branch
#   fires only if `canonical ∈ []`, which is false, so the non-emptiness test is
#   subsumed by the membership test that follows it and the drop changes no
#   output at any input. There is consequently no discriminating witness and no
#   `weak-ignore-nonempty` rival can exist here; asserting one would be a
#   fabricated attack. The impl is carried instead as the POSITIVE
#   pos-drop-vacuous-conjunct, so the claim is machine-checked in the direction
#   it is actually true in. (This is a carrier fact about the frozen spec's
#   shape, not a spec defect: the conjunct is redundant, not wrong.)
#
# FRAME/PERMISSION-MUTATION (frame-mutate-candidates): VACUOUS on this backend,
#   for the reason the SPEC_GUIDE gives — Lean and Velvet are referentially
#   transparent, there is no heap, no aliasing and no fractional permission, and
#   this method declares no `mut` binder on any input. There is no read-only
#   input to overwrite and thus no discriminating witness could exist. The
#   sibling calls this its MANDATORY #1 weakness class; here it simply does not
#   exist. Not fabricated, not substituted — reported as vacuous.
#
# WITNESS DISTINCTNESS. No two rivals share a refutation point. Each is refuted
#   at a distinct (names, uniqueSel, allowMultiple, canonical) tuple:
#     weak-arbitrary-on-multi     (["a","b"], false, false, "x")
#     weak-wrong-narrow-pick      (["a","b"], true,  true,  "b")
#     weak-invented-name          (["a"],     false, false, "b")
#     weak-ignore-allow-multiple  (["a","b"], true,  false, "a")
#     weak-ignore-unique-sel      (["a","b"], false, true,  "a")
#     weak-skip-narrowing         (["a","b"], true,  true,  "a")
#     weak-narrow-ignores-membership (["a","b"], true, true, "x")
#   so `names` moves (length 1 vs 2), `uniqueSel` moves (true/false),
#   `allowMultiple` moves (true/false), and `canonical` moves ("a"/"b"/"x") both
#   inside and outside `names`. Every input binder of the spec predicate is
#   varied; no rival is a near-miss of another sharing a point it does not fail
#   at. The last two share the (true, true) guard-satisfied corner but at
#   opposite membership status of `canonical`, and they fail in opposite
#   directions (one refuses where the spec selects, the other selects where the
#   spec refuses), so neither subsumes the other.
#
# WITNESS EVIDENCE. Each reject case's witness was rebuilt on both sides
#   out-of-band: it ELABORATES against its rival (exit 0) and FAILS against the
#   frozen solution (exit 1) with a gold-side error that is a plain kernel
#   EVALUATION of the concrete claim — `Tactic decide proved that the
#   proposition chooseTargetTester … = false is false`, i.e. gold's tester
#   evaluates to `true` at that input. The exit code tracks the CLAIM and not the
#   file's shape: the flipped-claim forgery (`= true` at the same input) builds
#   CLEANLY against the frozen solution (exit 0) for every one of the seven, so a
#   witness asserting gold is correct there could not have been recorded as a
#   rejection. No case rests on a tactic mismatch, a missing identifier, an
#   unfolding failure or a stuck reduction; the carrier has no opaque callee and
#   no loop, so every tester reduces in the kernel.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
#   axiom and axiomatizes no callee (mapping.md §3), so the sibling's
#   ax-ref-select-equals-gold A-reference probe has no counterpart — the changed
#   decision is modeled DEEPLY as `narrowed`/`selectedTarget` rather than through
#   any axiomatized callee.
AXIOM_TESTS = []
