"""properties.py — G-PBT falsification battery for django__django-15037 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct qualifyReference`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

This battery is PORTED from the nagini sibling (design document), re-expressed
against this backend's carrier; see the footer for the case-by-case accounting.

DEFENDED SURFACE (one contracted method):

  qualifyReference (isUniqueRef : Bool) (refColumn : List Char)
                   (idKey : Option (List Char))
      return (out : Option (List Char))
    ensures out = targetQualifier isUniqueRef refColumn idKey

The method derives the explicit target-column qualifier a stored cross-row
reference must carry. The sole ensures pins ``out`` to the GROUNDED pure
decision ``targetQualifier``, a total structural function of the method's own
three inputs (the ``axioms`` region is empty; there is no opaque answer key to
echo). ``targetQualifier`` is:

    targetQualifier isUniqueRef refColumn idKey =
      if isUniqueRef then none
      else match idKey with
        | none   => none
        | some k => if k ≠ [] ∧ k ≠ refColumn then some refColumn else none

so the single post-image folds SEVERAL independent sub-decisions, each of which
a rival can get wrong while holding the rest right:

  * (U) the IDENTITY gate — an identity / one-to-one reference
        (``isUniqueRef = true``) NEVER carries a qualifier (out = none),
        regardless of the referenced column or the target's identity key.
  * (P) the KEY-PRESENCE gate — a plain link whose target exposes no identity
        key (``idKey = none``) carries no qualifier (out = none).
  * (E) the NON-EMPTY gate — a present-but-empty identity-key name
        (``some []``) is treated as "no key" (out = none).
  * (D) the DIFFERENCE gate — a plain link whose identity key EQUALS the
        referenced column (``some k`` with ``k = refColumn``) carries no
        qualifier (out = none); it is only when the key is present, non-empty
        and DIFFERENT that the qualifier is emitted.
  * (V) the VALUE — on the emit branch the qualifier names the REFERENCED
        column (``some refColumn``), never the identity key or any other value.

All THREE input binders are varied by the reject witnesses (there is no
``require`` clause; every input is free and the post-image must hold for every
value of each):
  * ``isUniqueRef`` — drives the identity gate (U).
  * ``refColumn``   — the emitted value (V) and the difference gate (D).
  * ``idKey``       — drives the presence / non-empty / difference gates
                      (P, E, D), and is taken to ``none``, ``some []`` and
                      ``some k`` both equal to and distinct from ``refColumn``.

ADVERSARIAL READ of the classes (mirrors the nagini sibling):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rival keeps the gold body verbatim then writes back into a
    read-only sequence input carrying only a fractional heap permission, and is
    rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: every parameter is an immutable value, this method declares no
    ``mut`` binder, there is no heap and no aliasing. There is no read-only input
    to overwrite and no permission system to trip, so the class is vacuous. No
    substitute is fabricated.
  * TERMINATION / NON-TERMINATION: INAPPLICABLE as a shipped reject case here,
    because the frozen impl is loop-free, and closed by the verifier in any case.
    Two claims in the earlier version of this bullet are withdrawn. There is no
    "corpus-default ``partial``" and no "corpus-wide divergence spec hole" to be
    outside of: all 500 velvet bundles set ``"total"`` and open
    ``TotalCorrectness``, so ``total`` here is the norm, not a local strengthening.
    And the class is not vacuous by inexpressibility, since a rival rewrites the
    whole impl region and may splice a loop that the frozen body does not have.
    What refuses it is the descent obligation: under ``total`` a postcondition is
    claimed of ALL runs, not only terminating ones, so every loop owes a decreasing
    measure AND its descent. The setting cannot drift from the file's
    ``open TotalCorrectness DemonicChoice``, because the ``set_option`` elaborator
    itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured on this cell with
    the proof reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` whose body
    is ``z := z + 1`` is REJECTED, ``case «decreasing_1: z»``, residual
    ``⊢ z + 1 < z``. The nagini sibling carries no ``diverge-*`` case regardless.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is ``targetQualifier``, a concrete ``def`` in the ``pure`` region computing
    the outcome from the method's own arguments; there is no opaque answer key to
    echo. The unique satisfier IS the grounded decision, so there is no wrong
    echo to build; the honest controls are the cheapest faithful reshapes (the
    ``pos-*`` cases).
  * CONTROL-FLOW-EFFECT — N/A. The method has no raise path and no side-effect
    channel distinct from the returned ``Option (List Char)`` value; the whole
    behaviour is captured by that value abstraction. Omitted (as in the sibling).
  * PARTIAL-DOMAIN / VALUE — the main class. Each rival is correct on part of the
    input domain and wrong on one sub-domain of ``targetQualifier``, refuted at a
    concrete input in that sub-domain.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``): ``qualifyReferenceTester
<isUniqueRef> <refColumn> <idKey> = false`` says the extracted program's result
violates the method postcondition at that concrete input. It is checked in a file
whose ``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. The frozen impl is a loop-free ``if`` / ``match`` ladder over fully
TRANSPARENT carriers (``Bool`` / ``List Char`` / ``Option (List Char)``), so
every witness ``decide``s at literal inputs: it ELABORATES against the
reshaped/wrong rival (a genuine counterexample) and, because the frozen solution
satisfies the spec at every input, ``decide`` proves ``… = false`` FALSE against
gold — the discrimination half. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness elaborates against its rival (exit 0)
and fails against the frozen solution (exit 1). No witness binds a hypothesis
(the carrier computes), so there is nothing to be inconsistent.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``; the only outside
callee (the identity-key lookup) is taken as the free input ``idKey`` (an
A-reference validated by axiom_check.py / G-AX), not a consumed contract. Nothing
in the proof rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15037"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block, so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- A one-to-one / identity link never carries an explicit qualifier.\n"
    "    if isUniqueRef then\n"
    "      return none\n"
    "    else\n"
    "      -- A plain many-to-one link: consult the target collection's identity key.\n"
    "      match idKey with\n"
    "      | none   => return none\n"
    "      | some k =>\n"
    "        -- Qualify only when the identity key is a present, non-empty column\n"
    "        -- that differs from the column actually referenced.\n"
    "        if k ≠ [] ∧ k ≠ refColumn then\n"
    "          return (some refColumn)\n"
    "        else\n"
    "          return none\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. All positive controls below keep it UNCHANGED
# (their reshaped/annotated bodies close under the same script); rivals leave it
# in place too (the gate strips it for the witness build, and the rejection is
# carried by the witness, not the tactic script).
_PROOF = ("prove_correct qualifyReference by\n"
          "  loom_solve <;> simp_all [targetQualifier]\n"
          "  all_goals tauto")

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced (proof kept)."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `qualifyReferenceTester <isUniqueRef> <refColumn> <idKey> = false` says
# ---- the extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped.
_TESTER = (
    "extract_program_for qualifyReference\n"
    "prove_precondition_decidable_for qualifyReference\n"
    "prove_postcondition_decidable_for qualifyReference\n"
    "derive_tester_for qualifyReference\n\n")


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct reshape cannot verify the
    # spec is SPEC-TOO-STRONG. Each keeps the whole decision value identical and
    # only reshapes the executable surface, so the frozen proof still closes.
    # =====================================================================
    {
        "id": "pos-conjunct-commute",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: commute the two conjuncts of the difference/non-empty guard
        # (`k ≠ refColumn ∧ k ≠ []` instead of `k ≠ [] ∧ k ≠ refColumn`). `∧` is
        # commutative, so the guard fires on exactly the same inputs and the
        # emitted value is unchanged; a distinct syntactic form of the frozen
        # ladder. The frozen proof closes.
        "module": _impl(
            "    if isUniqueRef then\n"
            "      return none\n"
            "    else\n"
            "      match idKey with\n"
            "      | none   => return none\n"
            "      | some k =>\n"
            "        if k ≠ refColumn ∧ k ≠ [] then\n"
            "          return (some refColumn)\n"
            "        else\n"
            "          return none"),
        "rationale": "commuting the two conjuncts of the present-non-empty-and-"
                     "different guard leaves the emit condition and the emitted "
                     "value identical on every input (`∧` is commutative), so "
                     "`out = targetQualifier isUniqueRef refColumn idKey` still "
                     "holds; a correct reshape must verify, else SPEC-TOO-STRONG "
                     "on guard-conjunct order. (Ports the sibling's reorder "
                     "positive to this straight-line carrier.)",
    },
    {
        "id": "pos-decision-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: on the plain-link / present-key branch, bind the qualifier
        # decision to a typed local before returning it, instead of returning
        # each `if`-arm directly. Same value flow; a distinct executable shape.
        "module": _impl(
            "    if isUniqueRef then\n"
            "      return none\n"
            "    else\n"
            "      match idKey with\n"
            "      | none   => return none\n"
            "      | some k =>\n"
            "        let q : Option (List Char) :=\n"
            "          if k ≠ [] ∧ k ≠ refColumn then some refColumn else none\n"
            "        return q"),
        "rationale": "binding the present-key qualifier decision to a typed local "
                     "and returning it (instead of returning each `if`-arm "
                     "directly) leaves the decision and the emitted value "
                     "identical, so `out = targetQualifier isUniqueRef refColumn "
                     "idKey` is unchanged; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on decision binding. Second positive this "
                     "carrier affords (the sibling's inline loop has no such "
                     "axis).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). The
    # residual admissibility risk on a total-domain spec is that the decision is
    # DEGENERATE at the interesting point — a qualifier gate that never actually
    # separated the emit-case from the suppress-case would read like a live one.
    # This case discharges an in-region assert pinning that the decision
    # genuinely forks on the F2P-shaped boundary: a plain link to a column that
    # DIFFERS from a present identity key emits the qualifier, while a plain link
    # to the identity-key column itself suppresses it. The impl and proof are
    # kept verbatim so the method's own obligation still discharges (the added
    # assert is a decidable literal fact the frozen script's `simp_all`/`tauto`
    # close alongside the ensures VC).
    # =====================================================================
    {
        "id": "admiss-decision-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `assert\n"
            "      (targetQualifier false ['a'] (some ['b']) = some ['a'] ∧\n"
            "       targetQualifier false ['a'] (some ['a']) = none))\n"
            "    if isUniqueRef then\n"
            "      return none\n"
            "    else\n"
            "      match idKey with\n"
            "      | none   => return none\n"
            "      | some k =>\n"
            "        if k ≠ [] ∧ k ≠ refColumn then\n"
            "          return (some refColumn)\n"
            "        else\n"
            "          return none"),
        "rationale": "the decision is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: a plain link (isUniqueRef=false) to a "
                     "column that DIFFERS from a present identity key emits the "
                     "qualifier (`targetQualifier false ['a'] (some ['b']) = some "
                     "['a']`), while a plain link to the identity-key column "
                     "itself SUPPRESSES it (`targetQualifier false ['a'] (some "
                     "['a']) = none`), so the difference gate really does fork on "
                     "that boundary. The in-region assert must discharge (else the "
                     "gate would be degenerate / the obligation vacuous); the impl "
                     "and proof are kept verbatim so the ensures still discharges "
                     "too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a loop-free ladder (its witness reduces
    # under `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-never-qualify",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: never emit the qualifier — return `none` on
        # every input. Correct on the identity sub-domain and on plain links whose
        # target has no distinct identity key; wrong exactly on the emit
        # sub-domain the fix introduces.
        "module": _impl(
            "    let _ := isUniqueRef\n"
            "    let _ := refColumn\n"
            "    let _ := idKey\n"
            "    return none"),
        "refinement": "this IS the pre-patch behaviour: the reference is emitted "
                      "without ever consulting the target's identity-key column, "
                      "so no explicit target-column qualifier is ever attached. On "
                      "the F2P case (a plain link pointing at a non-identity-key "
                      "column of the target) the generated description omits the "
                      "qualifier, so the F2P test — which asserts the description "
                      "carries the explicit target-column qualifier naming that "
                      "column — FAILS. It would NOT resolve; the precise change the "
                      "spec senses (G-DIFF).",
        "rationale": "REJECT from `out = targetQualifier isUniqueRef refColumn "
                     "idKey` on the emit branch (gates D+V): for a plain link to a "
                     "present, non-empty, DIFFERENT identity key the post-image "
                     "demands `some refColumn`, but the rival returns `none`. "
                     "Refuted at the F2P-shaped point (plain link, ref column "
                     "['a'], present distinct key ['b']) — the literal pre-patch "
                     "near-miss carrying the strongest refinement.",
        "witness": _witness("qualifyReferenceTester false ['a'] (some ['b'])"),
    },
    {
        "id": "weak-overemit-ignore-key",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: emit the qualifier for EVERY plain link, ignoring the
        # target's identity key entirely. Correct on the emit sub-domain and on
        # identity references, but over-emits whenever the target exposes no
        # identity key (idKey = none) — the key-presence gate (P).
        "module": _impl(
            "    if isUniqueRef then\n"
            "      return none\n"
            "    else\n"
            "      return (some refColumn)"),
        "refinement": "emitting the qualifier for EVERY plain link is what a real "
                      "patch that dropped the `if ref_pk_column` presence guard "
                      "would do: it attaches an explicit target-column qualifier "
                      "even when the target collection exposes NO identity key. On "
                      "the many plain links in the introspection suite whose target "
                      "has no such key, the generated description would carry a "
                      "spurious qualifier the expected output never has — breaking "
                      "the PASS_TO_PASS introspection tests. It would NOT resolve.",
        "rationale": "REJECT from `out = targetQualifier isUniqueRef refColumn "
                     "idKey` on the key-presence gate (P): when `idKey = none` the "
                     "post-image demands `none`, but the rival returns `some "
                     "refColumn`. Refuted at a plain link (ref column ['c']) whose "
                     "target has no identity key (`none`) — the sub-domain where "
                     "this rival is wrong and the others are not, and the only "
                     "witness moving the `idKey = none` binder value.",
        "witness": _witness("qualifyReferenceTester false ['c'] none"),
    },
    {
        "id": "weak-drop-difference-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the difference gate (D): keep the presence/non-empty guard
        # but DROP the `k ≠ refColumn` conjunct, so a plain link is qualified
        # whenever the target has a present, non-empty key — even when that key IS
        # the referenced column. Agrees with gold everywhere except that
        # sub-domain, so it carries its own separating input.
        "module": _impl(
            "    if isUniqueRef then\n"
            "      return none\n"
            "    else\n"
            "      match idKey with\n"
            "      | none   => return none\n"
            "      | some k =>\n"
            "        if k ≠ [] then\n"
            "          return (some refColumn)\n"
            "        else\n"
            "          return none"),
        "refinement": "dropping the `ref_pk_column != ref_db_column` difference "
                      "guard is what a real patch that qualified every plain link "
                      "with a present key would do — it attaches the qualifier even "
                      "when the referenced column IS the target's identity key, "
                      "producing a redundant explicit qualifier the expected output "
                      "omits on exactly those links. It breaks the PASS_TO_PASS "
                      "introspection tests (a plain link to the target's identity "
                      "key renders WITHOUT a qualifier) and is not the gold "
                      "behaviour. It would NOT resolve.",
        "rationale": "REJECT from `out = targetQualifier isUniqueRef refColumn "
                     "idKey` on the difference gate (D): when `idKey = some k` with "
                     "`k = refColumn` the post-image demands `none`, but the rival "
                     "returns `some refColumn`. Refuted at a plain link whose "
                     "present key EQUALS the referenced column (both ['a']) — the "
                     "sole sub-domain distinguishing this near-miss from gold, "
                     "which no other rival's witness probes.",
        "witness": _witness("qualifyReferenceTester false ['a'] (some ['a'])"),
    },
    {
        "id": "weak-wrong-column-value",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE rival (V): the emit DECISION is exactly right (the frozen gates
        # are kept), but on the emit branch it names the wrong column — the
        # identity key `k` instead of the referenced column `refColumn`.
        "module": _impl(
            "    if isUniqueRef then\n"
            "      return none\n"
            "    else\n"
            "      match idKey with\n"
            "      | none   => return none\n"
            "      | some k =>\n"
            "        if k ≠ [] ∧ k ≠ refColumn then\n"
            "          return (some k)\n"
            "        else\n"
            "          return none"),
        "refinement": "naming the target's identity-key column instead of the "
                      "actually-referenced column is what a real patch that wrote "
                      "the wrong local into the qualifier would do — the generated "
                      "description would carry an explicit qualifier naming the "
                      "target's identity key rather than the referenced column. The "
                      "F2P test asserts the qualifier names the REFERENCED column "
                      "exactly, so it FAILS on the value even though the emit "
                      "decision is right. It would NOT resolve.",
        "rationale": "REJECT from `out = targetQualifier isUniqueRef refColumn "
                     "idKey` on the emitted VALUE (V): on the emit branch the "
                     "post-image surfaces `some refColumn`, but the rival surfaces "
                     "`some k` (the identity key), which differs whenever the two "
                     "names differ. Refuted at a plain link where the referenced "
                     "column ['x'] and the present distinct key ['y'] differ — the "
                     "point that makes the post-image's dependence on `refColumn` "
                     "as the emitted value observable (every decision rival holds "
                     "this value correct or never reaches the emit branch).",
        "witness": _witness("qualifyReferenceTester false ['x'] (some ['y'])"),
    },
    {
        "id": "weak-drop-nonempty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the non-empty gate (E): keep the identity gate, the
        # key-presence match and the difference conjunct, but DROP the `k ≠ []`
        # conjunct, so a plain link is qualified whenever the target exposes a
        # key that differs from the referenced column — INCLUDING a present but
        # EMPTY key name, which the spec treats as "no key". Agrees with gold on
        # every other input, so it carries its own separating point (`some []`),
        # the one suppress sub-domain no other rival's witness reaches.
        "module": _impl(
            "    if isUniqueRef then\n"
            "      return none\n"
            "    else\n"
            "      match idKey with\n"
            "      | none   => return none\n"
            "      | some k =>\n"
            "        if k ≠ refColumn then\n"
            "          return (some refColumn)\n"
            "        else\n"
            "          return none"),
        "refinement": "dropping the presence half of the identity-key guard is "
                      "what a real patch that tested only 'the key differs from "
                      "the referenced column' — rather than 'a key is present AND "
                      "differs' — would do. A target collection that reports an "
                      "empty identity-key name is one that exposes no usable key, "
                      "and such a link must render WITHOUT a qualifier; this rival "
                      "attaches one (naming the referenced column) on exactly "
                      "those links, adding an explicit qualifier the expected "
                      "output never carries and breaking the PASS_TO_PASS "
                      "introspection tests. It would NOT resolve.",
        "rationale": "REJECT from `out = targetQualifier isUniqueRef refColumn "
                     "idKey` on the NON-EMPTY gate (E): when `idKey = some []` "
                     "the post-image demands `none` (an empty key name is "
                     "treated as no key), but the rival takes the emit branch — "
                     "`[] ≠ refColumn` holds for any non-empty `refColumn` — and "
                     "returns `some refColumn`. Refuted at a plain link whose "
                     "present key name is EMPTY while the referenced column is "
                     "['a'] — the sole suppress sub-domain distinguishing this "
                     "near-miss from gold, and the only witness driving `idKey` "
                     "to `some []`.",
        "witness": _witness(
            "qualifyReferenceTester false ['a'] (some ([] : List Char))"),
    },
    {
        "id": "weak-ignore-identity-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the identity gate (U): ignore `isUniqueRef` entirely
        # and run the plain-link decision for every reference. Correct on plain
        # links but WRONG on identity references, which must never carry a
        # qualifier. (The re-expression of the sibling's wrong-relation-kind
        # rival against the modeled clause.)
        "module": _impl(
            "    let _ := isUniqueRef\n"
            "    match idKey with\n"
            "    | none   => return none\n"
            "    | some k =>\n"
            "      if k ≠ [] ∧ k ≠ refColumn then\n"
            "        return (some refColumn)\n"
            "      else\n"
            "        return none"),
        "refinement": "ignoring the one-to-one / identity distinction is what a "
                      "real patch that ran the qualifier decision on BOTH relation "
                      "kinds would do — it would attach an explicit target-column "
                      "qualifier to an identity (one-to-one) reference, which the "
                      "expected output never carries. Every identity reference in "
                      "the introspection suite pointing at a distinct target key "
                      "would then render a spurious qualifier, breaking the "
                      "PASS_TO_PASS field-type / introspection tests. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = targetQualifier isUniqueRef refColumn "
                     "idKey` on the identity gate (U): when `isUniqueRef = true` "
                     "the post-image demands `none` regardless of the other "
                     "inputs, but the rival runs the plain-link decision and can "
                     "return `some refColumn`. Refuted at an identity reference "
                     "(isUniqueRef=true) with ref column ['a'] and a present "
                     "distinct key ['b'] — the only witness moving the "
                     "`isUniqueRef = true` binder value.",
        "witness": _witness("qualifyReferenceTester true ['a'] (some ['b'])"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness — one of which is the mandatory frame-
# mutation rival). Every one is accounted for below. The sibling models a richer
# surface: a `relation_field` returning a RelationField with FIVE postcondition
# clauses (is_one_to_one / rel_to_self / needs_qualifier / the qualifier-column
# value / the pinned-absent value) over READ-ONLY sequence inputs carrying
# fractional heap permissions, with an up-front copy loop. This backend narrows
# to the purely functional CORE the fix actually changes: the single decision of
# whether (and with which column) to attach the explicit target-column qualifier,
# modeled as `targetQualifier` over `(Bool, List Char, Option (List Char))` with
# NO loop, NO permission surface, and NO heap. The nagini clauses attached to
# behaviours this bundle does not model (the relation-KIND field `is_one_to_one`,
# the self/other TARGET field `rel_to_self`, the up-front copy loop's framing)
# have no counterpart here — that is carrier narrowing, not an omission of
# coverage, and chasing case-count parity would fabricate rivals for behaviours
# this bundle does not contract.
#
#   sibling case                       -> here                          disposition
#   -------------------------------------------------------------------------------
#   pos-echo-grounded-oracle           -> pos-decision-local            PORTED (grounded
#                                                                        decision, reshaped)
#   pos-reorder-decisions              -> pos-conjunct-commute          PORTED (reshaped
#                                                                        to straight-line)
#   admiss-precond-available           -> admiss-decision-nondegenerate RE-AIMED
#   frame-mutation-write-readonly-col  -> (none)                        VACUOUS
#   partial-domain-never-emit-qualifier-> weak-never-qualify            PORTED (the
#                                                                        literal prepatch)
#   partial-domain-overemit-qualifier  -> weak-overemit-ignore-key      PORTED (presence
#                                                                        gate P) + ...
#   partial-domain-overemit-qualifier  -> weak-drop-difference-guard    ... (difference
#                                                                        gate D near-miss)
#   absent-qualifier-value-smuggled    -> weak-drop-nonempty-guard      ... (non-empty
#                                                                        gate E near-miss)
#   wrong-qualifier-column-value       -> weak-wrong-column-value       PORTED (value V)
#   absent-qualifier-value-smuggled    -> (folded into the P/U/D gates) RE-EXPRESSED
#   wrong-relation-kind                -> weak-ignore-identity-gate     PORTED (re-aimed
#                                                                        at gate U)
#
# 2 positives ported, 1 admiss re-aimed, 6 uniqueness ported/re-expressed, 1
# vacuous. 9 velvet cases against the sibling's 8 — case counts are not a target
# either way; the sixth rival exists because the E gate is a real sub-domain of
# the post-image, not to match a count.
#
# VACUOUS (frame-mutation-write-readonly-col): the sibling's MANDATORY frame-
#   mutation rival keeps the gold body verbatim then writes back into a read-only
#   sequence input granted only at half permission, and must be rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent: every
#   parameter is an immutable value, the method declares no `mut` binder, there is
#   no heap and no aliasing. There is no read-only input to overwrite and no
#   permission system to trip, so the class is vacuous. No substitute is
#   fabricated.
# RE-EXPRESSED (absent-qualifier-value-smuggled): the sibling's clause-5 rival
#   smuggles a non-empty value into the qualifier field on the needs_qualifier ==
#   False branch, which the pre-repair spec (an Implies-only clause) admitted;
#   the repaired spec pins the absent case to the empty canonical value. Here the
#   "absent" outcome is `none`, and `targetQualifier` pins it structurally on
#   EVERY suppress sub-domain (identity U, no-key P, empty-key E, equal-key D).
#   There is no separate free channel to smuggle into — a rival that returns a
#   `some ...` where the post-image demands `none` is exactly what weak-overemit-
#   ignore-key (P), weak-drop-nonempty-guard (E), weak-drop-difference-guard (D)
#   and weak-ignore-identity-gate (U) already do, each refuted on its own
#   suppress sub-domain. Every suppress gate of the post-image now carries its
#   OWN rival: the empty-key gate (E) is attacked by weak-drop-nonempty-guard,
#   whose witness drives `idKey` to `some []` — the one binder value no other
#   witness reaches. (Added on audit: E was previously recorded as a residual
#   gap on the reasoning that no sibling rival targeted it, but the gate is
#   expressible and refutable on this carrier like any other, so the gap was
#   closed rather than documented.)
# RE-AIMED (admissibility): the sibling asserts the half-permission admits reading
#   a normal column/table/Optional-PK input. This backend's method has NO
#   precondition and no permission surface, so that probe is degenerate (every
#   input is in-domain). It is re-aimed at the residual total-domain risk — that
#   the decision is DEGENERATE at the interesting point — via an in-region assert
#   that the difference gate genuinely separates the emit-case (`... = some ['a']`)
#   from the suppress-case (`... = none`) on the F2P-shaped boundary.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the three input binders of
#   the sole ensures (pts = 6 distinct input points):
#     isUniqueRef — false (never-qualify, overemit, drop-difference, wrong-column,
#                   drop-nonempty) and true (ignore-identity-gate): BOTH truth
#                   values; the `true` value is what makes gate U observable.
#     refColumn   — ['a'] / ['c'] / ['a'] / ['x'] / ['a'] / ['a']: varied, and the
#                   value rival DEPENDS on it (`some refColumn` vs `some k`).
#     idKey       — some ['b'] / none / some ['a'] / some ['y'] / some [] /
#                   some ['b']: `none` (overemit's witness, the presence gate P),
#                   `some []` (drop-nonempty's witness, the non-empty gate E),
#                   `some k` with k = refColumn (drop-difference, gate D) and
#                   k ≠ refColumn (the emit sub-domain) — never held fixed, and
#                   each value flips the post-image's verdict, not just its
#                   spelling.
#   EVERY modeled suppress gate is attacked, each by its own rival refuted on its
#   own sub-domain: identity (U, ignore-identity-gate), key-presence (P,
#   overemit), non-empty (E, drop-nonempty), difference (D, drop-difference); the
#   emit VALUE (V, wrong-column); and the whole emit decision (never-qualify, the
#   prepatch). No residual suppress gate remains.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (the identity-key lookup is the free input `idKey`, an
# A-reference checked by axiom_check.py / G-CONF), and this gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
