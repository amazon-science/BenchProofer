"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8638 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct renderFieldEntry`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over two identifier carriers,
``List Char``):

  renderFieldEntry (name typ : List Char) return (out : FieldEntry)
    require name ≠ []
    require ∀ c ∈ name, isIdentChar c
    require typ ≠ []
    require ∀ c ∈ typ, isIdentChar c
    require typ ≠ "None".toList
    ensures out.nameNode = RefNode.text name                    -- (E1)
    ensures out.typeNode = RefNode.xref "class".toList typ       -- (E2)

The method renders one entry of an info field documenting a named item together
with its declared type. It produces two inline nodes: the node for the item
NAME and the node for its TYPE. The desired behaviour is fully pinned by the two
``ensures`` clauses over the method's own inputs:

  * (E1) the NAME node is a PLAIN text node carrying ``name`` verbatim — NO
         cross-reference, so documenting an item inside a class never emits a
         spurious navigation link to an unrelated identically-named item;
  * (E2) the TYPE node is a cross-reference of reference kind ``"class"`` to
         ``typ`` — the declared type stays navigable.

``crossRefOrText refrole target`` (the per-argument rendering rule) is a TOTAL,
fully-unfolded pure ``def`` in the ``pure`` region — an ``Option (List Char)``
role and a ``List Char`` target in, a ``RefNode`` out. The ``axioms`` region is
empty; there is NO opaque answer-key oracle in either load-bearing clause
(directive 8 — the post-image is grounded in the actual inputs). ``RefNode`` and
``FieldEntry`` both derive ``DecidableEq``, so the whole postcondition is
decidable and the tester+``decide`` witness path is live (see WITNESS MECHANICS).

WHICH CLAUSE CONSTRAINS THE IMPL, AND WHICH BINDER. Both E1 and E2 constrain the
impl, and each is a function of a DIFFERENT input binder:
  * E1 pins the NAME node from the ``name`` binder — its NODE KIND (text, not
    xref) and its CONTENT (``name``);
  * E2 pins the TYPE node from the ``typ`` binder — its NODE KIND (xref), its
    REFERENCE KIND (``"class"``), and its TARGET (``typ``).
Every uniqueness rival targets one of these; the reject witnesses vary BOTH
``name`` and ``typ`` and attack both clauses (see the footer's binder/point map).

ADVERSARIAL READ of the nagini classes on THIS carrier (case-by-case in the
footer):
  * FRAME/PERMISSION-MUTATION — VACUOUS in its PERMISSION half only. The nagini
    sibling records the class as N/A (``has_readonly_input = False``):
    ``role``/``type_role`` are bare ints passed by value, and the only heap
    permissions are on the freshly-built result the postcondition hands out in
    full. That half does carry over: there is no heap, aliasing, or permission
    system here, and ``name``/``typ`` are immutable value parameters, so no
    caller-owned input can be clobbered. But the RESULT-mutation half is NOT
    vacuous, and this file previously claimed it was. A ``let mut`` local plus a
    record update (``out := { out with .. }``) is in-fragment and lives entirely
    inside the impl region, so an impl CAN build the right entry and then
    overwrite a slot before returning — the final-state-vs-transient distinction
    the nagini U6 case probes exists on this carrier. Carried as
    ``rival-result-overwrite`` (measured: rejected, witness discriminates).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the sibling records.
    E1/E2 are pinned to explicit functions of the inputs (``RefNode.text name``,
    ``RefNode.xref "class".toList typ``), not to an opaque answer key — there is
    nothing to echo. The honest cheapest CORRECT impl (``pos-direct``) is carried
    as a positive control instead; any WRONG rendering fails E1 or E2.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. A rival can get the shape
    right but the NAME-node kind wrong (link a role-less name — the exact
    pre-patch bug), drop the TYPE link, swap the two nodes, pin the wrong
    reference kind, feed the wrong content/target string to an otherwise correct
    node, overwrite a correct slot after the fact, or get the rendering right on
    only PART of the modeled domain (``rival-partial-name-fix``: the
    incomplete-fix shape, where E1 holds for short names and fails for the rest).
    The genuinely partial-domain rival matters on its own: the other rivals are
    each wrong at EVERY admissible input, so none of them probes whether E1 is
    pinned across its whole domain rather than at one input shape.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
    rather than faking it is refused even earlier, by the elaborator's own
    check (``Decreasing annotations are required in total correctness
    semantics``). So divergence neither applies to this impl nor discharges the
    ``ensures`` clauses vacuously if a rival introduces it.

WITNESS MECHANICS ON THIS BUNDLE. The whole postcondition is DECIDABLE (E1/E2
are equalities on ``FieldEntry``/``RefNode``, both ``DecidableEq``; the only
callee, ``crossRefOrText``, is a transparent ``def``). So the tester+``decide``
path is live: each rival's extracted program reduces under ``decide`` at a
concrete input, and ``renderFieldEntryTester name typ = false`` says the
extracted program's result VIOLATES the postcondition there. Each reject rival
therefore carries a machine-checked ``witness`` at ONE concrete input, checked in
a file whose ``prove_correct`` block has been stripped so no tactic script can
mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (the
tester ``decide``s to ``false`` — the rival violates E1/E2 there) and FAILS
against the frozen solution (gold's tester ``decide``s to ``true``, so ``=
false`` is refuted by ``decide``), so each rejection is a genuine spec refutation
and not mechanical tactic breakage. Every witness input is a non-empty
identifier (``isIdentChar`` throughout) and ``typ`` is never the literal
``"None"``, so no witness is vacuously excluded by a ``require`` clause, and no
witness binds a hypothesis, so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file's axiom-soundness
lane is empty by design there too (the two deep models are validated by
axiom_check.py / G-AX); this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8638"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- Frozen impl body, verbatim — everything strictly BETWEEN the method's
# ---- `-- impl-start` and `-- impl-end` (both markers and the comment lines live
# ---- inside the elided impl region). Every variant edits ONLY this block (and,
# ---- for correct reshapes/admissibility, the elided `prove_correct` tactic
# ---- body), so the spec view is untouched and same_spec holds by construction.
_IMPL = (
    "    -- The item NAME carries no reference role: it is rendered as plain text and\n"
    "    -- never becomes a cross-reference.\n"
    "    let nameRole : Option (List Char) := none\n"
    "    -- The declared TYPE keeps its class reference role (unchanged), so it stays\n"
    "    -- a navigable cross-reference to a class.\n"
    "    let typeRole : Option (List Char) := some \"class\".toList\n"
    "    let nameNode := crossRefOrText nameRole name\n"
    "    let typeNode := crossRefOrText typeRole typ\n"
    "    return { nameNode := nameNode, typeNode := typeNode }"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (elided
# from the spec view); rivals leave it as-is — the rejection is carried by the
# witness, not the tactic script.
_PROOF = "prove_correct renderFieldEntry by\n  loom_solve <;> simp [crossRefOrText]"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- Fine-grained anchors, each unique in the file and strictly inside the impl
# ---- region, so a single-line rival edits nothing but the impl.
_NAME_ROLE_ABSENT = "let nameRole : Option (List Char) := none"
_TYPE_ROLE_CLASS = 'let typeRole : Option (List Char) := some "class".toList'
_NAME_NODE_BUILD = "let nameNode := crossRefOrText nameRole name"
_TYPE_NODE_BUILD = "let typeNode := crossRefOrText typeRole typ"
_RETURN_ENTRY = "return { nameNode := nameNode, typeNode := typeNode }"


# ---- witness builder. The postcondition is DECIDABLE (E1/E2 are equalities on
# ---- DecidableEq types; `crossRefOrText` is a transparent def), so a witness
# ---- reaches the post-image through Velvet's tester machinery:
# ---- `renderFieldEntryTester name typ = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block is stripped, so no tactic script can mask
# ---- the verdict; both the rival and gold are loop-free, so both testers
# ---- reduce under `decide`.
def _witness(name_lit, typ_lit):
    return ("extract_program_for renderFieldEntry\n"
            "prove_precondition_decidable_for renderFieldEntry\n"
            "prove_postcondition_decidable_for renderFieldEntry\n"
            "derive_tester_for renderFieldEntry\n\n"
            f"example : renderFieldEntryTester {name_lit} {typ_lit} = false := by\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the two nodes DIRECTLY as the post-image demands
        # (`RefNode.text name` / `RefNode.xref "class" typ`), bypassing the
        # per-argument rendering rule entirely. E1/E2 are literally these two
        # equalities, so this is the cheapest HONEST correct impl — and since the
        # post-image is grounded in the inputs (not an opaque answer key), it
        # doubles as proof the spec is not echo-vulnerable (any wrong rendering
        # fails E1 or E2). Loop-free straight line, so the residual goal closes
        # under `loom_solve` alone.
        "module": _impl_reproved(
            "    return { nameNode := RefNode.text name, "
            "typeNode := RefNode.xref \"class\".toList typ }",
            "prove_correct renderFieldEntry by\n  loom_solve"),
        "rationale": (
            "the post-image (E1 `out.nameNode = RefNode.text name`, E2 "
            "`out.typeNode = RefNode.xref \"class\" typ`) is GROUNDED in the "
            "inputs, so building the two nodes directly is the honest cheapest "
            "CORRECT impl; it MUST verify, else E1/E2 are SPEC-TOO-STRONG. Ports "
            "the nagini make-xref/echo-honest control expressed on this carrier: "
            "shows the spec is not echo-vulnerable (any wrong node fails E1/E2)."
        ),
    },
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the two intermediate `nameRole`/`typeRole` locals and pass
        # the roles inline to the per-argument rendering rule. Same value flow
        # (a role of `none` for the name, `some "class"` for the type), different
        # control shape. The frozen proof closes it unchanged.
        "module": _impl(
            "    let nameNode := crossRefOrText (none : Option (List Char)) name\n"
            "    let typeNode := crossRefOrText (some \"class\".toList) typ\n"
            "    return { nameNode := nameNode, typeNode := typeNode }"),
        "rationale": (
            "a correct impl with a DIFFERENT shape (drop the role locals, pass the "
            "roles inline to the per-argument rendering rule) must verify; the "
            "value flow is unchanged so E1/E2 still discharge and the frozen proof "
            "closes as-is. Ports the nagini pos-bvfe-reshape (drop the name_role "
            "local, build directly). If it fails => SPEC-TOO-STRONG (over-fit to "
            "the role-local code form)."
        ),
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind and build the TYPE node before the NAME node, then
        # assemble the same entry. Identical values, reordered statements. Ports
        # the nagini pos-makexref-reorder (branch reorder) argument to this
        # backend's statement sequence.
        "module": _impl(
            "    let typeRole : Option (List Char) := some \"class\".toList\n"
            "    let nameRole : Option (List Char) := none\n"
            "    let typeNode := crossRefOrText typeRole typ\n"
            "    let nameNode := crossRefOrText nameRole name\n"
            "    return { nameNode := nameNode, typeNode := typeNode }"),
        "rationale": (
            "statement-REORDER positive control: bind/build the type node first "
            "and the name node second, then assemble the same entry. Identical "
            "values, different control-flow shape, so E1/E2 still hold and the "
            "frozen proof closes. Ports the nagini pos-makexref-reorder. Must "
            "verify, else SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini admiss-bvfe-selfcall established the precondition
    # admits a normal F2P-shaped input and asserted the postcondition on it. Here
    # the five `require` clauses (non-empty, all-ident, typ ≠ "None") are pinned
    # by ONE in-region assert at the exact F2P input (name="attr", typ="int"):
    # that input SATISFIES every `require`, AND the post-image is non-degenerate
    # there (a plain "attr" text node and a "class" cross-reference to "int"). If
    # the preconditions could not admit that input, PRECOND-TOO-STRONG; the impl
    # is kept verbatim so the method's own ensures discharges too. The assert is
    # live — a false claim leaves an unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      ((\"attr\".toList ≠ ([] : List Char)) ∧\n"
            "       (∀ c ∈ \"attr\".toList, isIdentChar c) ∧\n"
            "       (\"int\".toList ≠ ([] : List Char)) ∧\n"
            "       (∀ c ∈ \"int\".toList, isIdentChar c) ∧\n"
            "       (\"int\".toList ≠ \"None\".toList) ∧\n"
            "       crossRefOrText (none : Option (List Char)) \"attr\".toList\n"
            "         = RefNode.text \"attr\".toList ∧\n"
            "       crossRefOrText (some \"class\".toList) \"int\".toList\n"
            "         = RefNode.xref \"class\".toList \"int\".toList))\n"
            "    let nameRole : Option (List Char) := none\n"
            "    let typeRole : Option (List Char) := some \"class\".toList\n"
            "    let nameNode := crossRefOrText nameRole name\n"
            "    let typeNode := crossRefOrText typeRole typ\n"
            "    return { nameNode := nameNode, typeNode := typeNode }",
            "prove_correct renderFieldEntry by\n"
            "  loom_solve <;> simp [crossRefOrText] <;> decide"),
        "rationale": (
            "the five `require` clauses admit the exact F2P input "
            "(name=\"attr\", typ=\"int\"): it is non-empty, all-ident, and typ is "
            "not \"None\"; AND the post-image is non-degenerate there (a plain "
            "\"attr\" text node and a \"class\" cross-reference to \"int\"), so the "
            "obligation is neither unsatisfiable (else PRECOND-TOO-STRONG) nor a "
            "collapse. The in-region assert must discharge; the impl is kept "
            "verbatim so the method's own ensures discharges too. Ports the nagini "
            "admiss-bvfe-selfcall re-aimed at this backend's require clauses."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P test (test_info_field_list_var). Each
    # rival edits only the impl region; the frozen spec and proof statement are
    # untouched. The reject witnesses vary BOTH `name` and `typ` and attack both
    # E1 (name-node) and E2 (type-node).
    # =====================================================================
    {
        "id": "rival-name-links",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack — the pre-patch bug. The NAME argument is built under
        # a PRESENT reference role, so its node becomes a cross-reference instead
        # of plain text, violating E1. Every other clause holds.
        "module": _swap(
            _BASE, _NAME_ROLE_ABSENT,
            'let nameRole : Option (List Char) := some "obj".toList'),
        "refinement": (
            "configuring a present role for the NAME argument IS the pre-patch "
            "behaviour (the field carried a reference role for its name token). "
            "Its faithful real patch is the unpatched config, under which the "
            "item-name token renders as a navigable cross-reference instead of a "
            "plain strong text node. The F2P test_info_field_list_var asserts the "
            "name token is a plain strong node (not a pending cross-reference), so "
            "it FAILS — the exact defect the fix corrects; would NOT resolve."
        ),
        "rationale": (
            "REJECT from E1 (`out.nameNode = RefNode.text name`) — the "
            "discriminating no-auto-link clause: a present name role makes "
            "`crossRefOrText` emit an `xref`, so `nameNode ≠ RefNode.text name`. "
            "Refuted at name=\"attr\", typ=\"int\" (the F2P input). If it verified "
            "=> SPEC-TOO-WEAK (admits the bug)."
        ),
        "witness": _witness('"attr".toList', '"int".toList'),
    },
    {
        "id": "rival-drop-type-link",
        "kind": "uniqueness",
        "expect": "reject",
        # The TYPE argument is built under an ABSENT role, collapsing its node to
        # plain text instead of a cross-reference, violating E2. E1 still holds.
        "module": _swap(
            _BASE, _TYPE_ROLE_CLASS,
            "let typeRole : Option (List Char) := none"),
        "refinement": (
            "building the TYPE token under no role corresponds to a real patch "
            "that also dropped the type's class reference role; the declared type "
            "would render as a plain text node instead of a navigable "
            "cross-reference. The F2P asserts the type token is a cross-reference "
            "of reference kind 'class' to the type string, which a plain node is "
            "not, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from E2 (`out.typeNode = RefNode.xref \"class\" typ`) — the "
            "companion clause pinning the UNCHANGED type cross-reference: an "
            "absent type role makes `crossRefOrText` emit `text`, so `typeNode ≠ "
            "RefNode.xref \"class\" typ`. Refuted at name=\"var\", typ=\"str\" — a "
            "distinct input from rival-name-links, varying both binders. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness('"var".toList', '"str".toList'),
    },
    {
        "id": "rival-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the two nodes swapped: the (linking) type node in the name slot
        # and the (plain) name node in the type slot. Violates BOTH E1 and E2.
        "module": _swap(
            _BASE, _RETURN_ENTRY,
            "return { nameNode := typeNode, typeNode := nameNode }"),
        "refinement": (
            "emitting the type node where the name node belongs (and vice-versa) "
            "corresponds to a renderer that placed the parenthesised type token "
            "before the name token. The F2P pins the exact child sequence (the "
            "plain name node first, the type cross-reference second), so a swapped "
            "order FAILS — would NOT resolve."
        ),
        "rationale": (
            "REJECT from the positional clauses E1 (name slot must be a plain text "
            "node) and E2 (type slot must be a cross-reference): the swap puts the "
            "`xref` in the name slot and the `text` in the type slot, violating "
            "both. Refuted at name=\"nm\", typ=\"ty\" — a distinct input. Ports "
            "the nagini rival-order-swap. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness('"nm".toList', '"ty".toList'),
    },
    {
        "id": "rival-wrong-refkind",
        "kind": "uniqueness",
        "expect": "reject",
        # The type node links (correct kind) but carries the WRONG reference kind
        # ("obj" instead of "class"), violating E2's reference-kind pin. E1 holds.
        "module": _swap(
            _BASE, _TYPE_ROLE_CLASS,
            'let typeRole : Option (List Char) := some "obj".toList'),
        "refinement": (
            "the type token cross-references but with the wrong reference kind; a "
            "real renderer building the type reference with a non-'class' kind "
            "would propagate as the type token's reference kind ≠ 'class'. The "
            "F2P pins the type cross-reference's reference kind to 'class', so a "
            "wrong kind FAILS — would NOT resolve."
        ),
        "rationale": (
            "REJECT from E2 (`out.typeNode = RefNode.xref \"class\" typ`) — the "
            "reference-kind pin: the type node links but with kind \"obj\", so "
            "`typeNode ≠ RefNode.xref \"class\" typ`. Refuted at name=\"item\", "
            "typ=\"cls\" — a distinct input. Ports the nagini "
            "rival-makexref-reftype-mask, re-aimed at the type argument (the only "
            "place a reference kind is observable on this carrier). If it verified "
            "=> SPEC-TOO-WEAK."
        ),
        "witness": _witness('"item".toList', '"cls".toList'),
    },
    {
        "id": "rival-name-content",
        "kind": "uniqueness",
        "expect": "reject",
        # The name node is plain text (correct kind) but carries the WRONG content
        # (`typ` instead of `name`), violating E1's content pin. ADDED — the
        # velvet RefNode carries content, which the nagini FieldNode did not model,
        # so E1 pins more than the node kind; this rival attacks that extra pin.
        "module": _swap(
            _BASE, _NAME_NODE_BUILD,
            "let nameNode := crossRefOrText nameRole typ"),
        "refinement": (
            "rendering the name node's content from the type string instead of "
            "the name string corresponds to a renderer that mislabeled the item "
            "name. The F2P pins the name token's text to the documented item's "
            "own name, so a name node carrying the type text FAILS — would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from E1 (`out.nameNode = RefNode.text name`) — the CONTENT "
            "pin (as opposed to the node-kind pin rival-name-links attacks): the "
            "node kind is right but the content is `typ`, so `nameNode ≠ "
            "RefNode.text name` whenever name ≠ typ. Refuted at name=\"foo\", "
            "typ=\"bar\" (distinct strings, distinct input). ADDED because the "
            "velvet RefNode carries content the nagini FieldNode did not model. If "
            "it verified => SPEC-TOO-WEAK (E1 unpinned on content)."
        ),
        "witness": _witness('"foo".toList', '"bar".toList'),
    },
    {
        "id": "rival-result-overwrite",
        "kind": "uniqueness",
        "expect": "reject",
        # The entry is built CORRECTLY and then the name slot is OVERWRITTEN,
        # after the fact, with a linking node, through a `mut` local and a record
        # update. Confirms the spec pins the FINAL returned value, not a transient
        # that was correct at some point during the block. ADDED BY AUDIT: this
        # lane was previously recorded as inexpressible on a "referentially
        # transparent carrier with no `mut` binder", which is measurably wrong —
        # a `let mut` local plus `{ e with .. }` is in-fragment, stays inside the
        # impl region, is REJECTED, and its witness discriminates.
        "module": _swap(
            _BASE, _RETURN_ENTRY,
            "let entry : FieldEntry := { nameNode := nameNode, "
            "typeNode := typeNode }\n"
            "    let mut out : FieldEntry := entry\n"
            "    out := { out with nameNode := "
            "crossRefOrText (some \"obj\".toList) name }\n"
            "    return out"),
        "refinement": (
            "an entry whose name node ends up linking — by ANY route, a "
            "post-construction overwrite included — renders the item name as a "
            "navigable cross-reference. The F2P asserts the name token is a plain "
            "strong node, and it observes the FINAL rendered tree, so a correct "
            "intermediate that is overwritten before emission FAILS just the same "
            "— would NOT resolve."
        ),
        "rationale": (
            "REJECT from E1 (`out.nameNode = RefNode.text name`) evaluated on the "
            "RETURNED value's final field values rather than on a transient: the "
            "block builds the plain name node, then overwrites the name slot with "
            "an `xref`. Refuted at name=\"fld\", typ=\"dict\" — a distinct input. "
            "Ports the nagini rival-result-mutate (U6), which the port had "
            "recorded as vacuous here; `let mut` + record update is in-fragment, "
            "so the final-state-vs-transient distinction the nagini case probes "
            "DOES exist on this carrier. If it verified => SPEC-TOO-WEAK (the "
            "spec would pin only an intermediate)."
        ),
        "witness": _witness('"fld".toList', '"dict".toList'),
    },
    {
        "id": "rival-partial-name-fix",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN rival: the name role is dropped only for very short
        # names, so the name node is plain on part of the modeled domain and
        # still links on the rest. ADDED BY AUDIT: every other rival here is
        # wrong at EVERY input, so a spec that only pinned E1 on some sub-domain
        # (e.g. via a length side-condition) would have gone undetected. This is
        # the incomplete-fix shape, and it must be rejected too.
        "module": _swap(
            _BASE, _NAME_ROLE_ABSENT,
            "let nameRole : Option (List Char) :=\n"
            "      if name.length ≤ 2 then none else some \"obj\".toList"),
        "refinement": (
            "an entry rendering that suppresses the name's reference role only "
            "for some names is an INCOMPLETE fix: names above the cut-off still "
            "render as navigable cross-references, which is the very defect the "
            "desired behaviour rules out. The F2P documents an item whose name is "
            "longer than the cut-off, so its name token would still be a pending "
            "cross-reference and the assertion FAILS — would NOT resolve."
        ),
        "rationale": (
            "REJECT from E1 quantified over the WHOLE modeled domain: E1 must "
            "hold for every admissible `name`, so an impl that emits a plain "
            "text node only when `name.length ≤ 2` violates it at every longer "
            "name. Refuted at name=\"value\", typ=\"num\" — a distinct input, and "
            "the first witness in this battery that lands at a point where the "
            "rival is wrong while ANOTHER admissible point exists where it is "
            "right. ADDED BY AUDIT: the six original rivals are each wrong at "
            "every input, so none of them probes whether E1 is pinned across the "
            "domain rather than at a single shape. If it verified => "
            "SPEC-TOO-WEAK (E1 unpinned on part of its own domain)."
        ),
        "witness": _witness('"value".toList', '"num".toList'),
    },
    {
        "id": "rival-type-target",
        "kind": "uniqueness",
        "expect": "reject",
        # The type node is a "class" cross-reference (correct kind) but to the
        # WRONG target (`name` instead of `typ`), violating E2's target pin.
        # ADDED — the velvet RefNode carries a target, which the nagini FieldNode
        # did not model, so E2 pins more than the reference kind.
        "module": _swap(
            _BASE, _TYPE_NODE_BUILD,
            "let typeNode := crossRefOrText typeRole name"),
        "refinement": (
            "building the type cross-reference to the item name instead of the "
            "type string corresponds to a renderer that pointed the type link at "
            "the wrong target. The F2P pins the type cross-reference's target to "
            "the type string, so a link to the name FAILS — would NOT resolve."
        ),
        "rationale": (
            "REJECT from E2 (`out.typeNode = RefNode.xref \"class\" typ`) — the "
            "TARGET pin (as opposed to the reference-kind pin rival-wrong-refkind "
            "attacks): the kind is right but the target is `name`, so `typeNode ≠ "
            "RefNode.xref \"class\" typ` whenever name ≠ typ. Refuted at "
            "name=\"a1\", typ=\"b2\" (distinct strings, distinct input). ADDED "
            "because the velvet RefNode carries a target the nagini FieldNode did "
            "not model. If it verified => SPEC-TOO-WEAK (E2 unpinned on target)."
        ),
        "witness": _witness('"a1".toList', '"b2".toList'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The nagini sibling has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus an EMPTY AXIOM lane. It
# contracts TWO functions — the per-token node-kind renderer `make_xref` and the
# field-entry builder `build_variable_field_entry`. THIS bundle models only the
# purely-functional CORE as a single contracted method `renderFieldEntry`: the
# per-token rule `make_xref` is the frozen `pure`-region `def crossRefOrText`
# (NOT a separately-contracted method), so the two nagini rivals internal to
# `make_xref` cannot mutate it — they are re-expressed as wrong ARGUMENTS passed
# by `renderFieldEntry`, exactly what a same-spec impl-region edit can do. This
# is carrier narrowing, not a coverage gap.
#
#   nagini case                    -> here                       disposition
#   -------------------------------------------------------------------------
#   pos-makexref-reorder           -> pos-reorder                 PORTED (re-shaped)
#   pos-bvfe-reshape               -> pos-reshape                 PORTED
#   (echo-honest, implicit)        -> pos-direct                  RE-EXPRESSED
#   admiss-bvfe-selfcall           -> admiss-f2p-input            PORTED (re-aimed)
#   rival-prepatch-namerole (U1)   -> rival-name-links            PORTED
#   rival-drop-type-link (U2)      -> rival-drop-type-link         PORTED
#   rival-order-swap (U3)          -> rival-order-swap             PORTED
#   rival-makexref-invert (U4)     -> (folded into rival-name-links) SUBSUMED
#   rival-makexref-reftype-mask(U5)-> rival-wrong-refkind          PORTED (re-aimed)
#   rival-result-mutate (U6)       -> rival-result-overwrite        PORTED (audit)
#   (no sibling)                   -> rival-name-content           ADDED
#   (no sibling)                   -> rival-type-target            ADDED
#   (no sibling)                   -> rival-partial-name-fix       ADDED (audit)
#   AXIOM_TESTS ([])               -> (none)                       DROPPED (G-AX lane)
#   frame-mutation (permission half)-> (none)                      VACUOUS
#
# 12 velvet SPEC cases: 3 soundness, 1 admissibility, 8 uniqueness.
#
# PORTED (positives): pos-bvfe-reshape (drop the role local, build directly) ->
#   pos-reshape (drop the two role locals, pass roles inline). pos-makexref-reorder
#   (branch reorder inside make_xref) -> pos-reorder: make_xref is now a pure def
#   with no impl-region branch to reorder, so the reorder is re-shaped to the
#   statement sequence inside renderFieldEntry (build the type node before the
#   name node). Both verified out-of-band with real builds. pos-direct RE-EXPRESSES
#   the nagini honest-echo control: the post-image is grounded, so the cheapest
#   honest impl builds the two nodes directly; it proves the spec is not
#   echo-vulnerable.
# PORTED-RE-AIMED (admissibility): admiss-bvfe-selfcall established the
#   precondition on an F2P-shaped input. This method's precondition is five
#   `require` clauses (not a fractional-permission Requires); the re-aimed probe
#   asserts all five admit the exact F2P input (name="attr", typ="int") AND the
#   post-image is non-degenerate there.
# PORTED (rivals U1/U2/U3): rival-prepatch-namerole -> rival-name-links (present
#   name role; the pre-patch bug, THE central attack, refuted at the F2P input);
#   rival-drop-type-link -> rival-drop-type-link (absent type role); rival-order-swap
#   -> rival-order-swap (swap the two nodes). Each carries a machine-checked witness
#   that ELABORATES against the rival and FAILS against gold (two real builds each).
# PORTED-RE-AIMED (U5): rival-makexref-reftype-mask attacked make_xref's reftype
#   pin. make_xref is now a pure def, so the reftype is only observable where
#   renderFieldEntry passes a role — the type argument. rival-wrong-refkind passes
#   the type argument under kind "obj" instead of "class", violating E2's
#   reference-kind pin. Same argument, re-aimed at the type node.
# SUBSUMED (U4 rival-makexref-invert): the nagini invert flips make_xref's
#   node-kind decision (present role -> plain, absent role -> xref). make_xref is
#   now a pure def that cannot be mutated by an impl-region edit; the OBSERVABLE
#   half of the inversion on this carrier — a role-less name that nonetheless
#   links — is exactly rival-name-links (present name role -> the name node links
#   when it must be plain). The other half (un-linking the class-role type) is
#   rival-drop-type-link. So U4's observable content is covered by the two
#   argument rivals; no separate case is written, and none is claimed dropped for
#   difficulty.
# ADDED (rival-name-content, rival-type-target): the velvet RefNode carries the
#   node's CONTENT and, for an xref, its TARGET — structure the nagini FieldNode
#   (is_xref + reftype only) did not model. So E1 pins the name node's content and
#   E2 pins the type node's target, beyond kind/reftype. Two rivals feed the wrong
#   string (name/type swapped as content/target) to an otherwise-correct node,
#   attacking those extra pins. Real divergences with machine-checked witnesses,
#   completing coverage of every observable field of both nodes.
# PORTED-BY-AUDIT (U6 rival-result-mutate -> rival-result-overwrite): the nagini
#   result-mutation sanity case overwrites a built list element after the fact.
#   This file previously recorded the case as VACUOUS on the grounds that Velvet
#   is "referentially transparent — no heap, no in-place mutation, no `mut`
#   binder — so the returned FieldEntry is a pure value with no post-construction
#   write path". That reason was WRONG, and an audit measured it: `let mut out :
#   FieldEntry := entry` followed by `out := { out with nameNode := ... }` is
#   in-fragment, needs nothing outside the impl region, and is rejected by E1
#   with a discriminating witness. The absence of a HEAP does not imply the
#   absence of a post-construction write path; a mutable local is one. The
#   permission half of the frame lane is still genuinely vacuous (no aliasing, no
#   fractional permissions, and both value parameters are immutable), so only the
#   result-mutation half is carried.
# ADDED-BY-AUDIT (rival-partial-name-fix): the six original rivals are each wrong
#   at EVERY admissible input, which leaves the incomplete-fix shape unprobed —
#   an impl correct on part of the modeled domain and wrong on the rest. A spec
#   that pinned E1 only at some input shape (rather than universally over `name`)
#   would have passed the original battery. This rival suppresses the name's
#   reference role only for `name.length ≤ 2`, so E1 holds for short names and
#   fails for every longer one; refuted at name="value".
# DROPPED (AXIOM_TESTS): empty in the nagini file too; the axiom lane is G-AX's
#   job (axiom_check.py validates crossRefOrText == the real per-token renderer),
#   and this gate ignores AXIOM_TESTS regardless.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
#   rather than faking it is refused even earlier, by the elaborator's own
#   check (``Decreasing annotations are required in total correctness
#   semantics``). So divergence neither applies to this impl nor discharges the
#   ``ensures`` clauses vacuously if a rival introduces it.
#
# CLAUSE / BINDER / POINT COVERAGE of the reject witnesses (pts = 8 distinct
# input points, no two rivals sharing an input tuple):
#   E1 (name node): rival-name-links (node KIND) + rival-name-content (CONTENT)
#                   + rival-result-overwrite (KIND, established post-construction)
#                   + rival-partial-name-fix (KIND, on PART of the domain).
#   E2 (type node): rival-drop-type-link (KIND) + rival-wrong-refkind (reference
#                   KIND) + rival-type-target (TARGET).
#   Both E1 and E2 (positional): rival-order-swap.
#   Binder `name` varied: "attr", "var", "nm", "item", "foo", "a1", "fld", "value".
#   Binder `typ`  varied: "int", "str", "ty", "cls", "bar", "b2", "dict", "num".
#   Every observable field of both RefNodes is attacked; both input binders are
#   varied across all eight witnesses; both positives and the admissibility case
#   defend E1 and E2 on gold-shaped inputs. Three DISTINCT failure ROUTES to the
#   same clause are covered for E1 — a wrong argument, a post-construction
#   overwrite, and a domain-restricted fix — so E1's rejection cannot be an
#   artifact of one impl shape.
#
# WHY THE WITNESS POINTS CANNOT BE FORGED OUT-OF-DOMAIN (measured by audit). The
# derived tester HONOURS the `require` clauses: at an input the precondition
# excludes it reports satisfaction regardless of what the impl does there. Two
# builds confirm it — `renderFieldEntryTester [] "int"` and
# `renderFieldEntryTester "attr" "None"` both decide to `true` (so `= false` is
# refuted) even against an impl deliberately WRONG at `typ = "None"`. So a
# witness can only land at an input the spec actually constrains, and no reject
# case here can be satisfied by an excluded input.
#
# WITNESS MECHANICS: the postcondition is DECIDABLE (E1/E2 equalities on
#   DecidableEq types; crossRefOrText transparent), so the tester+`decide` path is
#   live. Every witness extracts the program and asserts `renderFieldEntryTester
#   name typ = false`: the rival's tester decides to `false` (postcondition
#   violated there) so the witness elaborates; gold's tester decides to `true` so
#   `= false` is refuted and the witness FAILS on gold. No witness binds a
#   hypothesis, so no consistency probe is needed. All eight checked with
#   scripts/lean_verify.sh: rival exit 0, gold exit 1. The gold-side failure is a
#   SEMANTIC refutation in every case, not mechanical breakage — the error reads
#   "Tactic `decide` proved that the proposition renderFieldEntryTester <name>
#   <typ> = false is false", i.e. the kernel fully reduced the claim and found it
#   false. No stuck reduction, no unknown identifier, no type error, no timeout.
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT RECORD (adversarial re-derivation of this battery; every
# claim below is a build that was actually run, not an argument). Two defects
# were found and repaired above: the U6 result-mutation lane was recorded as
# inexpressible on a false premise, and no rival probed the partial-domain
# (incomplete-fix) shape. Everything else earned its outcome.
#
# SPEC-TOO-WEAK probes (attack D) — NEW wrong impls not in the battery, all of
# which the frozen spec must REJECT. Every one did (exit 1), so no spec hole:
#   * ignore both inputs and hardcode the F2P answer pair          -> rejected
#   * name node plain but content = `name.reverse`                 -> rejected
#   * type node links with refkind taken from the TYPE string      -> rejected
#   * refkind differing from "class" only in CASE ("Class")        -> rejected
#   * both nodes plain (every role dropped)                        -> rejected
#   * name node links with the same "class" kind the type uses     -> rejected
#   * correct in-domain, wrong only OUTSIDE it (`typ = "None"`)    -> rejected,
#     which is the stronger result: E2 is pinned for every admissible `typ`, so
#     an impl cannot buy itself slack by special-casing near the domain edge.
#   * oracle-ECHO evasion (`let out :| <the two ensures>`) — does not even
#     elaborate ("failed to synthesize Findable"), so the post-image cannot be
#     assumed rather than computed. E1/E2 must be produced, not restated.
# SPEC-TOO-STRONG probes (attack E) — NEW correct reshapes, all of which the
# frozen spec must ACCEPT. Every one did (exit 0), so no soundness hole:
#   * name role = `some []` (an EMPTY role string, which the carrier bijection
#     treats as "no role") -> verifies under the frozen proof unchanged. This is
#     the reshape most likely to be definitionally distinguished, and it is not.
#   * assemble into an intermediate `FieldEntry` local, then project both fields
#   * the faithful `typ = "None" -> "obj"` domain guard (the real special case,
#     correct here BECAUSE `require typ ≠ "None"` excludes the branch) — verifies
#     with `simp_all [crossRefOrText]`, confirming the require clause is a real
#     domain restriction and not a hidden strengthening.
# ADMISSIBILITY LIVENESS (the one case whose evidence is an in-region assert, so
# a dead assert would make it a free pass): re-run with ONE conjunct replaced by
# a FALSE claim (`crossRefOrText none "attr" = RefNode.xref "class" "attr"`). The
# build FAILS ("Tactic `decide` proved that the proposition False is false"), so
# the assert is load-bearing and admiss-f2p-input is not vacuously verifying.
# STATEMENT INTEGRITY: the consumer spec view of all 12 variants is byte-identical
# to the frozen file's (sha256 2e27c039e43c2f6dfc20f08781d64fc886da39a374bd4a6
# ead57452124591be7), so no case reformats or weakens the obligation; the U4
# in-place inversion of `crossRefOrText` itself is correctly NOT attempted here,
# because that def lives in the `pure` region and editing it fails same_spec
# (measured: "spec view differs"). Its OBSERVABLE content is covered by the
# argument rivals, and additionally by a combined name-links-plus-type-unlinked
# variant that was built and rejected.
AXIOM_TESTS = []
