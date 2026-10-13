"""properties.py — G-PBT falsification battery for django__django-14534 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct labelIdentifier`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method reading the recorded label identifier of
a single rendered widget, over a per-code-point string carrier ``List Char``
lifted to ``String`` and an ordered association ``Attrs``):

  labelIdentifier (name : String) (index : String) (attrs : Attrs)
      return (out : Option String)
    ensures out = recordedId attrs                          -- the only clause

where ``Attrs = List (String × String)`` and ``recordedId attrs = attrs.lookup
"id"`` — a TRANSPARENT ``def`` spelled out over the input association
(directive 8), NOT an opaque answer-key: the whole clause reduces to a total
lookup of the literal key token ``"id"`` in the recorded attributes, present ⇒
``some`` its recorded value, absent ⇒ ``none``. ``decide`` computes it on any
concrete input, so no rival can "echo an oracle" — the only way to satisfy the
clause is to return exactly the recorded value.

WHAT THE SPEC DEFENDS. The modeled behavior reads the identifier the surrounding
rendering already RECORDED for this widget, rather than SYNTHESIZING one from the
widget's other recorded data. Two observable facets, both pinned by the single
whole-Option equality:
  * present ⇒ the recorded value VERBATIM (so a caller-chosen prefix survives —
    the recorded ``some "prefix_field_0"`` is returned, not a synthesized
    ``some "id_field_0"``);
  * absent ⇒ ``none`` (no fabrication — where no id was recorded the result is
    the absent value, not a synthesized non-``none`` string).

BINDER STRUCTURE (read before judging binder coverage). The signature has three
input binders — ``name``, ``index``, ``attrs`` — but the postcondition depends on
``attrs`` ALONE. ``name`` and ``index`` are carried read-only and are NOT
consulted (directive 5): the spec pins that the result is a function of the
recorded attributes only. The decisive class of rival is exactly the one that
consults ``name``/``index`` (synthesizes an identifier from them) instead of
reading ``attrs`` — every such rival diverges from ``recordedId attrs`` and is
refuted. The reject witnesses nonetheless VARY all three positions (``name`` over
{f, name, field, x, y}, ``index`` over {0..4}, ``attrs`` over five distinct
associations) so no position is pinned across the battery.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION (nagini's MANDATORY frame-mut-{dict,name} rivals)
    — VACUOUS here. The nagini sibling carries them because its inputs are held
    at a fractional heap permission (``Acc(dict_pred(ctx.attrs),1/2)`` /
    ``Acc(ctx.name,1/2)``) an impl can illegally overwrite. Lean/Velvet are
    referentially transparent: every input is an immutable value, this bundle
    declares NO ``mut`` binder, there is no heap and no aliasing — so there is no
    read-only input to mutate and no substitute probe to build. Not fabricated
    (porting map: this class is vacuous here).
  * ADMISSIBILITY (nagini's admiss-read-only-grants, which discharges the four
    ``1/2`` permission grants for an F2P-shaped input) — PORTED, not vacuous, as
    ``admiss-obligation-satisfiable-at-f2p``. The permission MECHANISM is absent
    (no ``require`` clause; the pre-conditions region is empty), but "there is no
    precondition" is NOT a reason to drop the lane: on a total carrier the
    analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE or
    DEGENERATE at exactly an F2P-shaped input, which the frozen
    ``prove_correct`` verifying does NOT rule out — it exhibits one impl for the
    universally-quantified clause and says nothing about the clause's value at
    the two concrete F2P shapes, nor whether those two values differ. The ported
    case discharges both by evaluation at those points before closing the frozen
    obligation verbatim.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image ``recordedId`` is a transparent
    ``def`` over the input association (a total lookup of the literal ``"id"``
    key), not an axiomatized oracle; the ``axioms`` region is empty.
  * AXIOM lane — the nagini sibling ships a 2-probe AXIOM lane, but this bundle's
    ``meta.json`` records ``G-AX = skip`` (no axioms; ``recordedId`` is a deep
    I-tag model, mechanically checked by G-CONF). DROPPED regardless — the axiom
    lane is not this gate's job.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``labelIdentifierTester name index attrs = false`` says the extracted program's
result violates the postcondition at that concrete input. It is checked in a file
whose ``prove_correct`` block has been stripped (so no tactic script can mask the
verdict) and there are no ``require`` clauses, so every input reaches the
postcondition. ``String`` and ``Attrs`` literals are fully concrete, so ``decide``
settles the whole ``Option String`` equality — no opaque term, no conditioning, no
head binders (hence no consistency obligation). Every witness below was confirmed
out-of-band with two real builds: it ELABORATES against its rival (tester = false)
and FAILS against the frozen solution (``decide proved … is false``).
"""
from pathlib import Path

INSTANCE = "django__django-14534"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the COMPLETE frozen impl body (one line). It lies
# ---- wholly inside the single `-- impl-start`/`-- impl-end` region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap), so every
# ---- surgery stays inside the elided region — the frozen spec (the `method`
# ---- header, `ensures out = recordedId attrs`, and the `pure` region defining
# ---- `Attrs`/`recordedId`) is never touched, and the `prove_correct
# ---- labelIdentifier` statement survives byte-identical. ----
_IMPL = '    return attrs.lookup "id"'

# ---- The `prove_correct labelIdentifier by loom_solve` TACTIC BODY is elided
# ---- from the consumer spec view (only the header survives), so a positive
# ---- control that reshapes the impl could retune its tactic script; here every
# ---- reshape still closes under the frozen `loom_solve`, so none is retuned and
# ---- only the impl region is edited. ----


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- The frozen tactic body, for the one case that must ADD a closing step.
# ---- It is elided from the consumer spec view (only the `prove_correct
# ---- labelIdentifier` header survives, byte-identical), so appending a tactic
# ---- keeps `markers.same_spec` and the obligation statement intact. ----
_TACTIC = "prove_correct labelIdentifier by\n  loom_solve"


def _with_impl_and_tactic(new_impl: str, new_tactic: str) -> str:
    """Impl body replaced AND the elided tactic body extended (spec untouched)."""
    return _swap(_with_impl(new_impl), _TACTIC, new_tactic)


# ---- witness preamble: reach the contract through Velvet's tester machinery. ----
_TESTER = (
    "extract_program_for labelIdentifier\n"
    "prove_precondition_decidable_for labelIdentifier\n"
    "prove_postcondition_decidable_for labelIdentifier\n"
    "derive_tester_for labelIdentifier\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both confirmed out-of-band with a
    # real build against the frozen `prove_correct … by loom_solve` script.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Ports the nagini `pos-control-reorder-early-return` ARGUMENT: instead of
        # returning the lookup directly, MATCH on it with the absent arm first and
        # rebuild the present arm. Semantically identical, different source.
        "module": _with_impl(
            '    match attrs.lookup "id" with\n'
            "    | none   => return none\n"
            "    | some v => return some v"),
        "rationale": "branch-reorder (absent arm handled first, present arm "
                     "rebuilt as `some v`) is observationally identical to gold on "
                     "both legs, so `out = recordedId attrs` still discharges. A "
                     "structurally-different faithful reshape MUST verify; if it "
                     "cannot, the postcondition is over-fit to one branch shape "
                     "(SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-return-recorded",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl satisfying the clause: return the transparent
        # post-image `recordedId attrs` directly. Because `recordedId` is a
        # spelled-out `def` (a total `List.lookup "id"`), this still does the real
        # lookup — there is no wrong echo that verifies. Re-expresses the nagini
        # admiss/no-echo SPIRIT (the precondition class is vacuous here).
        "module": _with_impl("    return recordedId attrs"),
        "rationale": "the cheapest impl satisfying the clause still performs the "
                     "real recorded-id lookup, because the post-image `recordedId` "
                     "is a transparent function of the input association — not an "
                     "axiomatized answer key. Demonstrates the spec is NOT "
                     "echo-vulnerable: there is no wrong echo that verifies (else "
                     "this would be a reject case). Must verify.",
    },
    {
        "id": "admiss-obligation-satisfiable-at-f2p",
        "kind": "admissibility",
        "expect": "verify",
        # ADMISSIBILITY on a TOTAL carrier. The pre-conditions region is empty, so
        # there is no `require` an input could violate — but that is NOT why the
        # lane would be vacuous, and it is not vacuous. The analogue here is the
        # obligation being UNSATISFIABLE (or degenerate) at exactly an F2P-shaped
        # input: a post-image that no result can meet, or one that collapses to a
        # constant, would let the whole battery pass while pinning nothing. So
        # discharge the post-image at the two F2P-shaped points BY EVALUATION, as
        # an in-region `assert`, and only then close the frozen obligation with the
        # impl verbatim. The assert states (a) at the caller-prefix configuration
        # the recorded id is the prefixed value, (b) at the no-id configuration the
        # result is the absent value, and (c) those two differ — so the obligation
        # is satisfiable at both F2P shapes AND non-degenerate between them.
        "module": _with_impl_and_tactic(
            "    assert (with_name_prefix `admiss\n"
            '      (recordedId [("id", "prefix_field_0")] = some "prefix_field_0"\n'
            "       ∧ recordedId [] = none\n"
            '       ∧ recordedId [("id", "prefix_field_0")] ≠ recordedId []))\n'
            '    return attrs.lookup "id"',
            _TACTIC + "\n  all_goals decide"),
        "rationale": "the sole obligation is SATISFIABLE and NON-DEGENERATE at "
                     "F2P-shaped inputs: the in-region `assert` discharges, by "
                     "evaluation, that the post-image is `some \"prefix_field_0\"` "
                     "at the caller-prefix configuration, `none` at the no-id "
                     "configuration, and that those two results DIFFER — so the "
                     "clause neither pins an unreachable result (which would make "
                     "every positive vacuous, the total-carrier analogue of "
                     "PRECOND-TOO-STRONG) nor collapses to a constant that both "
                     "F2P shapes could satisfy. The impl is kept verbatim so the "
                     "`ensures` still discharges; only the elided tactic body gains "
                     "`all_goals decide` to close the added assert. Must verify.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input (ELABORATES against the rival, FAILS against gold — both
    # halves confirmed out-of-band with real builds) and the refinement argument
    # for why its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "synthesize-from-name-index",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug (verbatim pre-patch shape): ignore the recorded
        # attributes entirely and synthesize an identifier from `name`/`index`.
        # Independent of `attrs`: wrong on BOTH facets (present: not the recorded
        # value; absent: a non-`none` synthesis). This is Solution_prepatch's
        # shape (G-DIFF already senses it); replicated here as the central rival.
        "module": _with_impl(
            '    return some ("id_" ++ name ++ "_" ++ index)'),
        "refinement": "synthesizes the identifier from the widget's field name and "
                      "position — the exact pre-fix behaviour. Where no id was "
                      "recorded its faithful real counterpart returns a fabricated "
                      "non-empty string instead of the absent value, so the failing "
                      "example that expects the absent result stays RED; and where a "
                      "caller prefix WAS recorded it returns the synthesized form "
                      "rather than the prefixed recorded id, so the failing example "
                      "that pins the prefixed id stays RED. It would NOT resolve — "
                      "this is the bug the fix removes.",
        "rationale": "REJECT from `out = recordedId attrs`: the rival's result is a "
                     "function of `name`/`index` alone and never reads `attrs`, so "
                     "it differs from `attrs.lookup \"id\"` on the absent sub-domain "
                     "(some vs none). Refuted at attrs=[] (no recorded id), where "
                     "the rival returns `some \"id_name_1\"` but the spec pins "
                     "`none`.",
        "witness": _witness('labelIdentifierTester "name" "1" []'),
    },
    {
        "id": "present-synthesizes",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain rival (ports nagini `partial-domain-present-fabricates`):
        # correct on the ABSENT sub-domain (returns `none`), but where an id IS
        # recorded it returns a value synthesized from `name`/`index` rather than
        # the recorded value. Attacks the present facet of the clause.
        "module": _with_impl(
            '    match attrs.lookup "id" with\n'
            '    | some _ => return some ("id_" ++ name ++ "_" ++ index)\n'
            "    | none   => return none"),
        "refinement": "ignores the recorded (prefix-honouring) identifier where one "
                      "exists and returns a name/index synthesis instead; on the "
                      "caller-prefix configuration the recorded id is the prefixed "
                      "form but this renders the synthesized form, so the failing "
                      "example pinning the prefixed identifier stays RED. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = recordedId attrs`: on the present "
                     "sub-domain the result must EQUAL the recorded value; the "
                     "rival returns the synthesized string instead. Correct on the "
                     "absent sub-domain, wrong on the present one (partial-domain). "
                     "Refuted at attrs=[(\"id\",\"prefix_field_2\")], where the "
                     "recorded id is `some \"prefix_field_2\"` but the rival returns "
                     "`some \"id_field_2\"`.",
        "witness": _witness(
            'labelIdentifierTester "field" "2" [("id", "prefix_field_2")]'),
    },
    {
        "id": "absent-synthesizes",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain rival (ports nagini `partial-domain-absence-fabricates`):
        # correct on the PRESENT sub-domain (returns the recorded value), but where
        # no id is recorded it synthesizes a non-`none` identifier from
        # `name`/`index` rather than returning the absent value. Attacks the absent
        # facet of the clause.
        "module": _with_impl(
            '    match attrs.lookup "id" with\n'
            "    | some v => return some v\n"
            '    | none   => return some ("id_" ++ name ++ "_" ++ index)'),
        "refinement": "fabricates a non-empty identifier from name/index where the "
                      "recorded attributes carry no id; on the no-id configuration "
                      "the real method must yield the absent result but this renders "
                      "a synthesized string, so the failing example expecting the "
                      "absent result stays RED. It would NOT resolve.",
        "rationale": "REJECT from `out = recordedId attrs`: on the absent "
                     "sub-domain the result must be `none`; the rival returns a "
                     "synthesized `some _`. Correct on the present sub-domain, wrong "
                     "on the absent one (partial-domain, dual to "
                     "present-synthesizes). Refuted at attrs=[] with a distinct "
                     "name/index (\"x\",\"3\"), where the spec pins `none` but the "
                     "rival returns `some \"id_x_3\"`.",
        "witness": _witness('labelIdentifierTester "x" "3" []'),
    },
    {
        "id": "always-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss (ports nagini `support-always-none`): always return the absent
        # value, dropping any recorded id. Correct ONLY where no id is recorded;
        # where an id IS recorded the result must equal it.
        "module": _with_impl("    return none"),
        "refinement": "drops the recorded identifier on every configuration; where "
                      "a caller prefix (or the default) recorded an id, the real "
                      "method returns that recorded id, not the absent value, so the "
                      "failing example pinning the recorded identifier stays RED. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = recordedId attrs`: on the present "
                     "sub-domain the result must equal the recorded value (and be "
                     "non-`none`); the rival returns `none` unconditionally. Refuted "
                     "at attrs=[(\"id\",\"prefix_field_0\")] with name/index "
                     "(\"f\",\"0\"), where the spec pins `some \"prefix_field_0\"` "
                     "but the rival returns `none`.",
        "witness": _witness(
            'labelIdentifierTester "f" "0" [("id", "prefix_field_0")]'),
    },
    {
        "id": "wrong-attribute-key",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no direct nagini counterpart): looks up the WRONG attribute key.
        # Reads `attrs` (so it is right whenever the two keys carry the same value
        # or both are absent) but consults `"name"` instead of the literal id key
        # token `"id"`. Pins that the specific key `"id"` is load-bearing.
        "module": _with_impl('    return attrs.lookup "name"'),
        "refinement": "reads a different recorded attribute than the identifier "
                      "one; on a widget whose recorded attributes carry both an id "
                      "and that other attribute with different values, the real "
                      "method returns the recorded id but this returns the other "
                      "attribute's value, so any example pinning the recorded "
                      "identifier stays RED. It would NOT resolve.",
        "rationale": "REJECT from `out = recordedId attrs`, whose post-image looks "
                     "up the literal key token `\"id\"`; the rival looks up a "
                     "different key. Refuted at attrs=[(\"id\",\"the_id\"),"
                     "(\"name\",\"other\")], where the spec pins `some \"the_id\"` "
                     "but the rival returns `some \"other\"` — demonstrating the "
                     "specific key `\"id\"` is pinned by the clause.",
        "witness": _witness(
            'labelIdentifierTester "y" "4" [("id", "the_id"), ("name", "other")]'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation, 4 uniqueness rivals) plus a
# 2-case AXIOM lane. This bundle models the SAME single functional core (read
# the recorded label identifier), over a TRANSPARENT computable carrier
# (`recordedId attrs = attrs.lookup "id"`), so the value-clause rivals port
# almost directly; the permission and precondition classes are vacuous on a
# referentially-transparent carrier.
#
#   sibling case (nagini)              -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder-early-return   -> pos-branch-reorder          PORTED
#   admiss-read-only-grants            -> admiss-obligation-satisfiable-at-f2p
#                                                                     PORTED
#   (extra correct positive)           -> pos-return-recorded          ADDED
#   frame-mutation-write-attrs         -> (none)                       VACUOUS
#   frame-mutation-write-name          -> (none)                       VACUOUS
#   partial-domain-absence-fabricates  -> absent-synthesizes           PORTED
#   partial-domain-present-fabricates  -> present-synthesizes          PORTED
#   support-prepatch-fabrication       -> synthesize-from-name-index   PORTED
#   support-always-none                -> always-absent                PORTED
#   (new — key coverage)               -> wrong-attribute-key          ADDED
#   AXIOM_TESTS (x2)                   -> (none)                        DROPPED
#
# PORTED (admiss-obligation-satisfiable-at-f2p): nagini's admissibility case
#   discharges the four `1/2` read-only permission grants for an F2P-shaped input.
#   The permission mechanism does not exist here, but the LANE does: on a total
#   carrier the PRECOND-TOO-STRONG analogue is an obligation unsatisfiable or
#   degenerate at an F2P-shaped input, and the frozen `prove_correct` verifying
#   does not rule that out. The case discharges the post-image by evaluation at
#   both F2P shapes (prefixed-id and no-id) and asserts the two results DIFFER,
#   then closes the frozen obligation with the impl verbatim.
# ADDED (pos-return-recorded): an extra correct positive — return the transparent
#   post-image directly. Because `recordedId` is a spelled-out lookup rather than
#   an oracle, this still performs the real lookup, demonstrating the spec is not
#   echo-vulnerable. This is a no-echo control, NOT the admissibility lane.
# VACUOUS (frame-mutation x2): this backend is referentially transparent, declares
#   no `mut` binder, and has no heap — there is no read-only input to overwrite
#   and no substitute probe. Not fabricated (porting map: vacuous here).
# ADDED (wrong-attribute-key): the nagini battery uses a fixed literal key token
#   `id_key()` (constant 1) and never varies which key is read, so there is no
#   sibling for a wrong-key rival; here the literal key `"id"` is pinned by the
#   clause, so a rival reading a different recorded attribute is refutable and
#   worth an explicit case — it also varies the `attrs` binder onto a two-entry
#   association.
#
# COVERAGE. The sole obligation (`prove_correct labelIdentifier`) is defended
# (pos-branch-reorder, pos-return-recorded, admiss-obligation-satisfiable-at-f2p)
# and attacked (five uniqueness
# rivals). The single postcondition clause `out = recordedId attrs` is attacked
# on BOTH facets: present ⇒ recorded value (present-synthesizes, always-absent,
# wrong-attribute-key, synthesize-from-name-index) and absent ⇒ none
# (absent-synthesizes, synthesize-from-name-index). The load-bearing binder
# `attrs` is varied across the five reject witnesses ([], [("id","...")] x2,
# [("id",...),("name",...)]), so pts=5. `name` (f/name/field/x/y) and `index`
# (0..4) are also moved across the witnesses even though the spec does not
# consult them — precisely BECAUSE the decisive rival class synthesizes from
# them, the battery exercises those positions while pinning the result to
# `recordedId attrs`. No binder is held fixed across the battery.
#
# AXIOM_TESTS: dropped. This bundle records `meta.json gates.G-AX = skip` (no
# axioms; `recordedId` is a deep I-tag model validated by G-CONF, not a callee
# axiom), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
