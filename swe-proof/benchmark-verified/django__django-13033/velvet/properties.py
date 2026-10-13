"""properties.py — G-PBT falsification battery for django__django-13033 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct orderingExpansionDecision`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  orderingExpansionDecision (fieldIsRelation modelHasDefaultOrdering : Bool)
      (fieldAttr : Option (List Char)) (segments : List (List Char))
      (lookup : List Char) return (out : Bool)
    require segments ≠ []
    ensures out =
      appendRelatedDefaultOrdering fieldIsRelation modelHasDefaultOrdering
        fieldAttr segments lookup

The method decides whether a related model's own default ordering is appended
for an ordering lookup. The single load-bearing ``ensures`` pins ``out`` to the
deep, fully-unfolded ``appendRelatedDefaultOrdering`` (the ``axioms`` region is
empty — no opaque answer key to echo). That pure model is a FOUR-way conjunction
over the inputs, each conjunct independently attackable:

  * RELATION — the resolved field is a relation (``fieldIsRelation``);
  * DEFAULT-ORDERING — the pointed-to model declares a default ordering
    (``modelHasDefaultOrdering``);
  * TERMINAL-SEGMENT — the field's stored attribute name is NOT the attribute
    named by the TERMINAL segment of the lookup path
    (``fieldAttr != some (terminalSegment segments)``) — the load-bearing
    conjunct the fix reshapes, comparing against the terminal segment rather than
    the whole joined lookup;
  * PK-SHORTCUT — the lookup is not the primary-key shortcut
    (``lookup != "pk".toList``).

FIVE INPUT BINDERS: ``fieldIsRelation``, ``modelHasDefaultOrdering`` (the two
boolean guards), ``fieldAttr`` (``Option (List Char)`` — present/absent stored
attr), ``segments`` (``List (List Char)`` — the split lookup path, whose LAST
element is the terminal segment) and ``lookup`` (``List Char`` — the whole joined
lookup). All are load-bearing: the two booleans and the pk literal select the
branch; ``fieldAttr`` vs ``terminalSegment segments`` is the discriminating
comparison the fix corrects; ``lookup`` drives the pk-shortcut conjunct.

CARRIER NOTE — FULLY TRANSPARENT. Every binder is a concrete decidable value
(``Bool`` / ``Option (List Char)`` / ``List (List Char)`` / ``List Char``); there
is no opaque callee, so witnesses need no conditioning — each reject witness is
stated at CONCRETE literal inputs and closed by ``decide``. A witness reaches the
post-image through Velvet's tester machinery
(``orderingExpansionDecisionTester … = false`` says the extracted program's
result violates the postcondition at that input), checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict. Every reject rival is a single closed-form expression over the pure
helpers, so its extracted tester ``decide``s over the literal. Both halves were
checked with ``scripts/lean_verify.sh`` — every witness elaborates green against
its rival and fails against the frozen solution.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Three structurally different but
    behaviourally identical correct impls (a short-circuit guard ladder; the four
    conjuncts in REVERSED order; an inverted early-exit on the disqualifying
    disjunction) must verify, else the spec is SPEC-TOO-STRONG on the impl shape.
    Each is reproven honestly (statement byte-identical, no weakened obligation)
    and each is provably NOT definitionally equal to the frozen body, so none of
    them verifies by mere reduction. That last condition is load-bearing and is
    the reason a named-boolean-local reshape is NOT among them: binding the frozen
    expression to a `let` and returning it is DEFEQ to the frozen body on this
    carrier (`example : frozenBody = localBoolBody := rfl` elaborates), so it
    verifies under the frozen tactic script unchanged and attests nothing about
    impl shape. Each control here needs its own tactic body precisely because
    reduction does not identify it with the frozen impl.
  * ADMISSIBILITY — the sibling self-asserts an F2P-shaped input satisfies its
    fractional-permission precondition. This backend's only ``require`` is
    ``segments ≠ []`` (met by every split path — a split always yields ≥1
    element), and there is no permission surface, so that probe is degenerate;
    the residual risk is a DEGENERATE post-image. ``admiss-nondegenerate``
    discharges an in-region ``assert`` pinning the two contrasting reproducer
    shapes — a lookup ending at the field's stored attribute (``record__root_id``
    ⇒ FALSE, order the column directly) vs one ending at the relation itself
    (``record__root`` ⇒ TRUE, expand the related default ordering) — so the
    post-image is shown non-degenerate at exactly the F2P discriminator. The impl
    is kept verbatim so the method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries no such rival
    here (all its inputs are already immutable value types — PSeq / bool — with
    no ``Acc(x,1/2)`` heap input), and Lean/Velvet are referentially transparent
    regardless: the inputs are immutable values declared read-only (not ``mut``),
    there is no heap, no aliasing, no permission system. The class has no carrier
    analogue; NOT ported (fabricating a substitute would test nothing).
  * DIVERGENCE / NON-TERMINATION — the sibling ships no ``diverge-*`` /
    ``nonterm-*`` case for this instance, so there is nothing to port; the class
    is not exercised here.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to
    ``appendRelatedDefaultOrdering …``, a fully-unfolded ``def`` over the method's
    own arguments (``terminalSegment`` is a pure ``getLast!``, not an opaque
    oracle); there is no answer-key term a wrong impl could echo. The cheapest
    correct impl computes the conjunction honestly, which the positive controls
    cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets the
    conjunction right on most of the domain and flips the answer on one named
    sub-domain (the whole-path comparison; the leading-vs-terminal segment
    comparison; each of the three dropped conjuncts; the pk operand confusion;
    the two collapsed near-misses).
"""
from pathlib import Path

INSTANCE = "django__django-13033"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Every variant swaps on this block, so the spec
# ---- view (everything outside the markers, plus the prove_correct body) is
# ---- never touched and same_spec is GUARANTEED.
_IMPL = """    -- impl-start
    let endsAtStoredAttr := fieldAttr != some (terminalSegment segments)
    let notPkShortcut := lookup != "pk".toList
    return fieldIsRelation && modelHasDefaultOrdering &&
      endsAtStoredAttr && notPkShortcut
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view).
_PROOF_GOLD = """prove_correct orderingExpansionDecision by
  loom_solve
  simp [appendRelatedDefaultOrdering]"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


def _rewrite_impl(new_block, proof=_PROOF_GOLD):
    """Full variant: whole impl block replaced; proof optionally retuned."""
    src = _swap(_BASE, _IMPL, new_block)
    if proof is not _PROOF_GOLD:
        src = _swap(src, _PROOF_GOLD, proof)
    return src


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `orderingExpansionDecisionTester … = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped. Every argument is
# ---- a concrete literal so `decide` reduces the (loop-free) extracted rival.
def _tester(body):
    return ("\n"
            "extract_program_for orderingExpansionDecision\n"
            "prove_precondition_decidable_for orderingExpansionDecision\n"
            "prove_postcondition_decidable_for orderingExpansionDecision\n"
            "derive_tester_for orderingExpansionDecision\n\n" + body)


def _witness(rel, defo, attr, segs, lookup):
    """A concrete refutation witness at one input point."""
    return _tester(
        f"example : orderingExpansionDecisionTester {rel} {defo} {attr} "
        f"{segs} {lookup} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each computes the identical boolean function; each is
    # reproven honestly (statement byte-identical, no weakened obligation).
    # =====================================================================
    {
        "id": "pos-control-guard-ladder",
        "kind": "soundness",
        "expect": "verify",
        # Same boolean function expressed as a short-circuit guard ladder: each
        # conjunct is checked in turn and any failure returns `false` early; only
        # when all four hold does it return `true`. Maximally different control
        # flow from the frozen single-expression conjunction.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if fieldIsRelation = false then\n"
            "      return false\n"
            "    if modelHasDefaultOrdering = false then\n"
            "      return false\n"
            "    if fieldAttr = some (terminalSegment segments) then\n"
            "      return false\n"
            "    if lookup = \"pk\".toList then\n"
            "      return false\n"
            "    return true\n"
            "    -- impl-end",
            proof="prove_correct orderingExpansionDecision by\n"
                  "  loom_solve\n"
                  "  all_goals simp_all [appendRelatedDefaultOrdering]"),
        "rationale": (
            "a correct impl built from short-circuit guards (each conjunct as an "
            "early-return, the returns inverted) computes the identical boolean "
            "function, so `out = appendRelatedDefaultOrdering …` holds on the whole "
            "domain and must verify; else SPEC-TOO-STRONG (over-fit to the "
            "single-expression conjunction shape). Reproven honestly: the "
            "obligation statement is byte-identical, only the tactic body clears "
            "the per-branch goals. (Sibling: pos-control-nested-branches.)"),
    },
    {
        "id": "pos-control-reordered-conjuncts",
        "kind": "soundness",
        "expect": "verify",
        # The same boolean function with the four conjuncts in REVERSED order:
        # the pk guard first, the relation flag last. Correct (`&&` on Bool is
        # commutative and associative) but NOT definitionally equal to the frozen
        # body, so `rfl`-style reduction cannot close it — the equality needs a
        # genuine case analysis on the two Bools. That is what makes this a real
        # SPEC-TOO-STRONG probe rather than a restatement of the frozen impl.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (lookup != \"pk\".toList) &&\n"
            "      (fieldAttr != some (terminalSegment segments)) &&\n"
            "      modelHasDefaultOrdering && fieldIsRelation\n"
            "    -- impl-end",
            proof="prove_correct orderingExpansionDecision by\n"
                  "  loom_solve\n"
                  "  simp [appendRelatedDefaultOrdering, Bool.and_assoc, "
                  "Bool.and_comm]\n"
                  "  all_goals cases fieldIsRelation <;> "
                  "cases modelHasDefaultOrdering <;>\n"
                  "    simp_all [Bool.and_comm]"),
        "rationale": (
            "evaluating the four conjuncts in the reverse order computes the "
            "identical boolean function (`&&` is commutative/associative on Bool), "
            "so `out = appendRelatedDefaultOrdering …` holds on the whole domain "
            "and must verify; else SPEC-TOO-STRONG (over-fit to the frozen operand "
            "ORDER). Unlike a mere `let`-binding of the same expression, this body "
            "is provably NOT definitionally equal to the frozen one — reduction "
            "alone cannot identify `a && b && c && d` with `d && c && b && a`, so "
            "the obligation is genuinely re-proven (the tactic body does the case "
            "analysis on the two Bools that the frozen script never needed). "
            "(Sibling: pos-control-local-bool, RE-AIMED: the sibling's named-local "
            "reshape is definitionally equal to the frozen body on this carrier — "
            "`example : frozenBody = localBoolBody := rfl` elaborates — so it "
            "verifies under the FROZEN tactic script unchanged and probes nothing "
            "about impl shape. Reordering is the weakest reshape this carrier does "
            "NOT collapse.)"),
    },
    {
        "id": "pos-control-early-exit-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # A correct impl whose control flow is inverted: compute the DISJUNCTION
        # of the two disqualifying conditions, bail out early on it, and return
        # the remaining two-way conjunction. De Morgan's law across a branch.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let bad := (fieldAttr == some (terminalSegment segments)) ||\n"
            "      (lookup == \"pk\".toList)\n"
            "    if bad then\n"
            "      return false\n"
            "    return fieldIsRelation && modelHasDefaultOrdering\n"
            "    -- impl-end",
            proof="prove_correct orderingExpansionDecision by\n"
                  "  loom_solve\n"
                  "  all_goals simp only [appendRelatedDefaultOrdering, "
                  "Bool.or_eq_true,\n"
                  "    beq_iff_eq, ne_eq, not_or] at *\n"
                  "  · rcases if_pos with h | h <;> simp [h]\n"
                  "  · have e1 : (fieldAttr != some (terminalSegment segments)) "
                  "= true := by\n"
                  "      simp [if_neg.1]\n"
                  "    have e2 : (lookup != \"pk\".toList) = true := by\n"
                  "      have := if_neg.2; simp_all\n"
                  "    rw [e1, e2, Bool.and_true, Bool.and_true]"),
        "rationale": (
            "the two value-level conjuncts are negated into a single "
            "disqualifying DISJUNCTION, taken as an early exit, leaving only the "
            "two boolean flags to conjoin — De Morgan across a branch. Same "
            "function on the whole domain, so it must verify, else SPEC-TOO-STRONG "
            "on control-flow shape. The obligation is reproven from scratch: the "
            "frozen script does not close it (measured — the branch splits the "
            "goal into a positive and a negative arm, neither of which "
            "`simp [appendRelatedDefaultOrdering]` discharges), so the tactic body "
            "here derives both arms explicitly. Statement byte-identical."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method's only `require` (`segments ≠ []`) is met by
    # every F2P-shaped input (a split path always has ≥1 element), so the
    # sibling's "a normal input satisfies the precondition" probe is degenerate
    # here. The residual admissibility risk is that the post-image is DEGENERATE
    # at the interesting point. This case discharges an in-region `assert`, at
    # two fully concrete F2P-shaped inputs, that the post-image is NON-DEGENERATE
    # and turns on the discriminating conjunct: a lookup path ending at the
    # field's stored attribute yields FALSE (order the column directly) while an
    # otherwise-identical path ending at the relation itself yields TRUE (expand
    # the related default ordering). The impl is kept verbatim so the method's own
    # obligation still discharges; the proof gains a `decide` arm for the assert.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      appendRelatedDefaultOrdering true true (some \"root_id\".toList)\n"
                  "        [\"record\".toList, \"root_id\".toList] \"record__root_id\".toList = false ∧\n"
                  "      appendRelatedDefaultOrdering true true (some \"root_id\".toList)\n"
                  "        [\"record\".toList, \"root\".toList] \"record__root\".toList = true))\n"),
            _PROOF_GOLD,
            "prove_correct orderingExpansionDecision by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp [appendRelatedDefaultOrdering]\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs, and turns on the load-bearing conjunct: a two-segment lookup "
            "ending at the field's stored attribute (terminal == stored attr) must "
            "give FALSE, while the otherwise-identical lookup ending at the "
            "relation itself (terminal != stored attr) must give TRUE — the exact "
            "distinction the fix draws. The in-region assert must discharge (else "
            "the obligation is degenerate / the precondition too strong); the impl "
            "is kept verbatim so `out = appendRelatedDefaultOrdering …` still "
            "verifies. (Sibling: admiss-reproducer-caller, re-aimed from "
            "precondition admissibility to post-image non-degeneracy since this "
            "backend's only require is `segments ≠ []` and there is no permission "
            "surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Each rival is a single closed-form
    # expression over the pure helpers so its extracted tester `decide`s.
    # =====================================================================
    {
        "id": "rival-prepatch-operand-lookup",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: compare the stored attribute against the WHOLE joined
        # lookup instead of the TERMINAL segment. Diverges exactly on a
        # multi-segment lookup whose terminal segment IS the stored attribute
        # (`attr == terminal` but `attr != lookup`) — the F2P reproducer.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return fieldIsRelation && modelHasDefaultOrdering &&\n"
            "      (fieldAttr != some lookup) &&\n"
            "      (lookup != \"pk\".toList)\n"
            "    -- impl-end"),
        "refinement": (
            "this is the literal pre-patch operand: it compares the stored "
            "attribute name against the whole joined lookup rather than the "
            "terminal segment. On the F2P reproducer (a self-referential relation "
            "lookup ending at the relation's own stored attribute) the stored attr "
            "equals the terminal segment but differs from the whole joined path, so "
            "the third conjunct is wrongly TRUE and the related model's default "
            "ordering is expanded (an extra join, a descending sort) instead of "
            "ordering the named column directly — exactly the reported bug; the F2P "
            "test FAILS. A rival verifying here is verify⇏resolve."),
        "rationale": (
            "REJECT from `out = appendRelatedDefaultOrdering …` via the "
            "TERMINAL-SEGMENT conjunct: on a multi-segment lookup where the stored "
            "attribute equals the terminal segment but not the whole lookup, the "
            "spec's third conjunct is FALSE (⇒ out false) while this rival's is "
            "TRUE (⇒ out true). Verifying would be SPEC-TOO-WEAK (the "
            "terminal-vs-whole distinction unpinned). Refuted at the reproducer "
            "point: stored attr `root_id`, path `record__root_id` (terminal "
            "`root_id`)."),
        "witness": _witness(
            "true", "true", "(some \"root_id\".toList)",
            "[\"record\".toList, \"root_id\".toList]", "\"record__root_id\".toList"),
    },
    {
        "id": "rival-first-segment-not-terminal",
        "kind": "uniqueness",
        "expect": "reject",
        # A DIFFERENT way to get the terminal-segment conjunct wrong: compare the
        # stored attribute against the FIRST segment of the path instead of the
        # LAST. Agrees with the spec on every single-segment path (first == last),
        # and diverges on any multi-segment path whose leading segment is the
        # stored attribute while its terminal segment is not.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return fieldIsRelation && modelHasDefaultOrdering &&\n"
            "      (fieldAttr != some segments.head!) &&\n"
            "      (lookup != \"pk\".toList)\n"
            "    -- impl-end"),
        "refinement": (
            "reading the path's LEADING segment where the decision is about the "
            "attribute actually named at its END inverts the answer whenever the "
            "leading segment happens to coincide with the field's stored attribute: "
            "the related model's default ordering is then suppressed for a lookup "
            "that genuinely ends at the relation and should expand it, so ordering "
            "by that relation silently loses its default order. The P2P ordering "
            "behaviour breaks on exactly those paths; would not resolve."),
        "rationale": (
            "REJECT via the TERMINAL-SEGMENT conjunct, at its POSITION operand "
            "rather than its whole-vs-segment operand (which "
            "rival-prepatch-operand-lookup attacks): on the two-segment path "
            "`record__root` with stored attr `record`, the spec's third conjunct is "
            "TRUE (`record != root`, ⇒ out true) while this rival's is FALSE "
            "(`record == record`, ⇒ out false). Verifying would be SPEC-TOO-WEAK "
            "(the conjunct pinned only up to which end of the path it reads). "
            "Refuted at stored attr `record`, path `record__root` (terminal "
            "`root`, leading `record`) — a point NO other reject case in this "
            "battery visits, and the only one whose expected answer is TRUE on a "
            "present stored attribute."),
        "witness": _witness(
            "true", "true", "(some \"record\".toList)",
            "[\"record\".toList, \"root\".toList]", "\"record__root\".toList"),
    },
    {
        "id": "rival-drop-pk-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the pk-shortcut conjunct. Diverges on the sub-domain where the
        # lookup IS the primary-key shortcut but the other three hold.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return fieldIsRelation && modelHasDefaultOrdering &&\n"
            "      (fieldAttr != some (terminalSegment segments))\n"
            "    -- impl-end"),
        "refinement": (
            "dropping the primary-key-shortcut guard means ordering by the bare pk "
            "shortcut on a relation with a default ordering would wrongly expand "
            "the related model's ordering instead of sorting by the pk column "
            "directly — a real regression the pk guard prevents; would not resolve "
            "the suite (the pk-shortcut handling breaks)."),
        "rationale": (
            "REJECT via the PK-SHORTCUT conjunct: when the lookup is the pk "
            "shortcut and the first three conjuncts hold, the spec's fourth "
            "conjunct is FALSE (⇒ out false) but this rival omits it (⇒ out true). "
            "Refuted at lookup == the pk shortcut with stored attr absent and "
            "terminal != stored attr. (Sibling: rival-drop-pk-conjunct.)"),
        "witness": _witness(
            "true", "true", "none", "[\"pk\".toList]", "\"pk\".toList"),
    },
    {
        "id": "rival-drop-default-ordering-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the default-ordering conjunct. Diverges when the related model
        # declares NO default ordering but the other three hold.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return fieldIsRelation &&\n"
            "      (fieldAttr != some (terminalSegment segments)) &&\n"
            "      (lookup != \"pk\".toList)\n"
            "    -- impl-end"),
        "refinement": (
            "a relation whose pointed-to model declares NO default ordering must "
            "sort by the named column directly (out false); substituting a "
            "nonexistent default ordering (out true) is wrong — the guard requires "
            "the default-ordering flag truthy. Would not resolve."),
        "rationale": (
            "REJECT via the DEFAULT-ORDERING conjunct: with the default-ordering "
            "flag FALSE but the other three TRUE, the spec is out false while this "
            "rival returns true. Refuted at `modelHasDefaultOrdering = false` with "
            "the other three holding. (Sibling: rival-drop-default-ordering-conjunct.)"),
        "witness": _witness(
            "true", "false", "none", "[\"a\".toList]", "\"a\".toList"),
    },
    {
        "id": "rival-drop-relation-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the relation conjunct. Diverges when the target is NOT a relation
        # but the other three happen to hold.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return modelHasDefaultOrdering &&\n"
            "      (fieldAttr != some (terminalSegment segments)) &&\n"
            "      (lookup != \"pk\".toList)\n"
            "    -- impl-end"),
        "refinement": (
            "a non-relation target has no related model whose default ordering "
            "could be expanded; out true is meaningless/wrong there. The guard "
            "requires the field to be a relation. Would not resolve."),
        "rationale": (
            "REJECT via the RELATION conjunct: the relation flag FALSE with the "
            "other three TRUE yields spec out false but this rival returns true. "
            "Refuted at `fieldIsRelation = false` with the other three holding. "
            "(Sibling: rival-drop-relation-conjunct.)"),
        "witness": _witness(
            "false", "true", "none", "[\"a\".toList]", "\"a\".toList"),
    },
    {
        "id": "rival-pk-operand-confusion",
        "kind": "uniqueness",
        "expect": "reject",
        # Operand confusion on the pk conjunct: compare the stored attribute
        # against the pk literal instead of comparing the lookup against it.
        # Diverges when the lookup IS the pk shortcut but the stored attr is not
        # the pk literal (and the other conjuncts hold).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return fieldIsRelation && modelHasDefaultOrdering &&\n"
            "      (fieldAttr != some (terminalSegment segments)) &&\n"
            "      (fieldAttr != some \"pk\".toList)\n"
            "    -- impl-end"),
        "refinement": (
            "comparing the stored attribute against the pk literal instead of "
            "comparing the lookup against it mis-guards the pk shortcut: ordering "
            "by the pk shortcut on a relation whose stored attribute is not the pk "
            "literal would wrongly expand the default ordering. Would not resolve."),
        "rationale": (
            "REJECT via the PK-SHORTCUT conjunct: choose the lookup == the pk "
            "shortcut and the stored attr != the pk literal with the first three "
            "holding — the spec requires lookup != pk (FALSE ⇒ out false), but this "
            "rival tests the WRONG operand (stored attr != pk, TRUE ⇒ out true). "
            "Refuted at lookup == pk, stored attr some non-pk. (Sibling: "
            "rival-pk-operand-confusion.)"),
        "witness": _witness(
            "true", "true", "(some \"x\".toList)", "[\"pk\".toList]", "\"pk\".toList"),
    },
    {
        "id": "rival-relation-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Cheap supporting near-miss: collapse the 4-conjunction to just the
        # relation flag. Correct only where the other three always agree with it.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return fieldIsRelation\n"
            "    -- impl-end"),
        "refinement": (
            "expanding the related default ordering for EVERY relation field "
            "ignores the terminal-segment, pk and default-ordering guards — the "
            "exact over-substitution the issue reports; fails the F2P."),
        "rationale": (
            "REJECT via the biconditional on many sub-domains: at a relation whose "
            "stored attribute equals the terminal segment, the spec is out false "
            "(third conjunct FALSE) but this rival returns true. Refuted at a "
            "single-segment lookup where terminal == stored attr. (Sibling: "
            "rival-relation-only.)"),
        "witness": _witness(
            "true", "true", "(some \"a\".toList)", "[\"a\".toList]", "\"a\".toList"),
    },
    {
        "id": "rival-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Cheap supporting near-miss: never expand the default ordering.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return false\n"
            "    -- impl-end"),
        "refinement": (
            "always ordering the named column directly never expands ANY related "
            "model's default ordering — the original feature (ordering by a "
            "relation adopts its default order) breaks; the P2P ordering tests that "
            "rely on expansion fail. Would not resolve."),
        "rationale": (
            "REJECT via the biconditional whenever the 4-conjunction is TRUE: the "
            "spec requires out true but this rival returns false. Refuted at the "
            "reproducer-adjacent point where all four conjuncts hold (a relation "
            "with default ordering, terminal != stored attr, non-pk lookup). "
            "(Sibling: rival-always-zero.)"),
        "witness": _witness(
            "true", "true", "none",
            "[\"record\".toList, \"root_id\".toList]", "\"record__root_id\".toList"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 10 SPEC cases (2
# soundness positives, 1 admissibility, 7 uniqueness rivals) plus an EMPTY AXIOM
# lane (AXIOM_TESTS = []). This backend models the SAME pure boolean decision
# DEEPLY and CONCRETELY (`appendRelatedDefaultOrdering` over `Bool` /
# `Option (List Char)` / `List (List Char)` / `List Char`), with a fully
# transparent carrier — so every non-vacuous sibling case ports directly, and no
# rival is dropped for want of a discriminating witness.
#
#   sibling case                         kind          -> here                                disposition
#   ------------------------------------------------------------------------------------------------------
#   pos-control-nested-branches          soundness     -> pos-control-guard-ladder            PORTED
#   pos-control-local-bool               soundness     -> pos-control-reordered-conjuncts     RE-AIMED (defeq)
#   (no sibling)                         soundness     -> pos-control-early-exit-negated-guard ADDED
#   admiss-reproducer-caller             admissibility -> admiss-nondegenerate                RE-AIMED
#   (no sibling)                         uniqueness    -> rival-first-segment-not-terminal     ADDED
#   rival-prepatch-operand-name          uniqueness    -> rival-prepatch-operand-lookup       PORTED
#   rival-drop-pk-conjunct               uniqueness    -> rival-drop-pk-conjunct              PORTED
#   rival-drop-default-ordering-conjunct uniqueness    -> rival-drop-default-ordering-conjunct PORTED
#   rival-drop-relation-conjunct         uniqueness    -> rival-drop-relation-conjunct        PORTED
#   rival-pk-operand-confusion           uniqueness    -> rival-pk-operand-confusion          PORTED
#   rival-relation-only                  uniqueness    -> rival-relation-only                 PORTED
#   rival-always-zero                    uniqueness    -> rival-always-false                  PORTED
#   AXIOM_TESTS (none)                   axiom         -> (none)                              N/A (G-AX)
#
# 7 uniqueness ported + 1 added, 1 soundness ported + 1 re-aimed + 1 added, 1
# admissibility re-aimed; 0 dropped; 0 vacuous (the sibling ships no
# frame-mutation or divergence rival for this instance — its inputs were already
# immutable value types, and there is no non-terminating impl at issue). Axiom
# lane empty (nothing to port; this gate ignores AXIOM_TESTS regardless).
#
# RE-AIMED (pos-control-local-bool -> pos-control-reordered-conjuncts): the
#   sibling's named-boolean-local reshape is a REAL reshape in Python (a typed
#   local plus a branch) but collapses on this carrier: `let guard := <the frozen
#   expression>; return guard` is DEFINITIONALLY EQUAL to the frozen body, which
#   `example : frozenBody = localBoolBody := rfl` confirms mechanically. A defeq
#   positive verifies under the FROZEN tactic script byte-for-byte unchanged, so
#   it exercises no impl-shape freedom at all — an honest pass that tests
#   nothing. Re-aimed to the weakest reshape this carrier does NOT collapse
#   (conjunct order reversed: `&&` is commutative but not defeq-commutative, so
#   the equality needs a case analysis the frozen script does not perform), and a
#   second control added for control-flow shape (early exit on the negated
#   disjunction). Both were measured to FAIL under the frozen proof script and to
#   pass only with their own tactic bodies, statement byte-identical.
#
# ADDED (rival-first-segment-not-terminal): the ported rival set attacked the
#   terminal-segment conjunct only through its WHOLE-vs-SEGMENT operand
#   (comparing against the joined lookup). The conjunct's other degree of
#   freedom — WHICH END of the split path it reads — went unprobed, and no
#   witness in the battery visited a point whose expected answer is TRUE with a
#   PRESENT stored attribute. The added rival reads the leading segment instead
#   of the terminal one, and its witness sits at exactly that point.
#
# RE-AIMED (admiss-reproducer-caller -> admiss-nondegenerate): the sibling
#   self-calls the method on the reproducer-shaped input to show its Requires is
#   satisfiable. This backend's only `require` is `segments ≠ []` (met by every
#   split path) and there is no permission surface, so that probe is degenerate;
#   the sharper residual risk is a DEGENERATE post-image, so the case is re-aimed
#   to a live in-region assert pinning the two contrasting F2P reproducer shapes
#   (path ending at the stored attribute ⇒ FALSE vs path ending at the relation
#   ⇒ TRUE) — the exact distinction the fix turns on.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out =
#   appendRelatedDefaultOrdering fieldIsRelation modelHasDefaultOrdering fieldAttr
#   segments lookup` has FIVE binders and FOUR independent top-level conjuncts.
#   The eight reject witnesses probe eight DISTINCT input points (pts=8):
#     * rival-prepatch-operand-lookup       T T (some root_id) [record,root_id] record__root_id
#     * rival-first-segment-not-terminal    T T (some record)  [record,root]     record__root
#     * rival-drop-pk-conjunct              T T  none          [pk]              pk
#     * rival-drop-default-ordering-conjunct T F  none          [a]               a
#     * rival-drop-relation-conjunct        F T  none          [a]               a
#     * rival-pk-operand-confusion          T T (some x)       [pk]              pk
#     * rival-relation-only                 T T (some a)       [a]               a
#     * rival-always-false                  T T  none          [record,root_id] record__root_id
#   So `fieldIsRelation` ranges over {T,F} (drop-relation holds it F, the rest T),
#   `modelHasDefaultOrdering` over {T,F} (drop-default holds it F, the rest T),
#   `fieldAttr` over {some, none} (present in prepatch / first-segment /
#   pk-confusion / relation-only, absent elsewhere), `segments` over lengths {1,2}
#   (the multi-segment reproducer vs single-segment points) and its terminal over
#   {equal-to, differing-from the stored attr}, and `lookup` over {pk shortcut,
#   non-pk, whole joined path}. All FOUR conjuncts are attacked: RELATION
#   (drop-relation), DEFAULT-ORDERING (drop-default), TERMINAL-SEGMENT (prepatch,
#   on the whole-vs-segment operand; first-segment-not-terminal, on WHICH END of
#   the path is read; plus relation-only), and PK-SHORTCUT (drop-pk,
#   pk-operand-confusion); the always-false near-miss attacks the TRUE image of
#   the whole conjunction. No binder is pinned at a single value across the reject
#   set. The witnesses also split by EXPECTED ANSWER, which matters because a
#   battery whose every witness sits where the spec says FALSE probes only one
#   image: prepatch/drop-*/pk-confusion/relation-only refute at points where the
#   spec is FALSE and the rival TRUE, while first-segment-not-terminal and
#   always-false refute at points where the spec is TRUE and the rival FALSE.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3: the changed op
#   is modeled deeply and concretely; there is no A-reference deep model of an
#   outside callee); the sibling's AXIOM_TESTS is likewise empty. This gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
