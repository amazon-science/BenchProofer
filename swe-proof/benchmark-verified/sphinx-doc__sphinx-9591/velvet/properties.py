"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9591 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct propertyTypeNodes`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a rendered-annotation carrier,
``List DocNode`` where a ``DocNode`` is one of text / cross-reference / punct):

  propertyTypeNodes (typ : List Char) return (out : List DocNode)
    require isBareName typ
    ensures out = DocNode.text ": ".toList :: annotationNodes typ

The method builds the inline children of a documented value's rendered type
annotation on the domain this signature uses — a single bare type name. The
leading literal ": " is its OWN inert text node; the type name itself is handed
to the annotation parser, whose node follows the literal. On the bare-name
domain the parser renders the name as ONE cross-reference node (so the type can
be navigated to its definition), NOT as inert literal text — which is precisely
the behavioural change the issue asks for.

``annotationNodes typ`` is a total, fully-unfolded pure ``def`` of the method's
own input (``[DocNode.xref typ]``) in the ``pure`` region — the deep model of the
unchanged parser callee, validated == the real callee by axiom_check.py (G-AX).
The ``axioms`` region is EMPTY: there is no opaque answer key to echo (directive
8 — the post-image is grounded in the actual input ``typ``). The single
load-bearing ``ensures`` clause decomposes into six independently-attackable
structural sub-behaviours of the returned two-node list:

  * SEP-KIND  — node 0 is a ``DocNode.text`` (inert), NOT a cross-reference;
  * SEP-TEXT  — node 0's text is exactly ": " (both code points, colon+space);
  * TYPE-KIND — node 1 is a ``DocNode.xref`` (a cross-reference), NOT inert text
                — the load-bearing discriminator of the fix (pre-patch emitted
                the type as inert text, so no cross-reference could appear);
  * TYPE-TGT  — node 1's cross-reference target is the type name ``typ`` itself,
                not some other string;
  * ARITY     — the list has BOTH nodes: the separator is not dropped, so the
                rendered annotation is never the bare type with no ": " before
                it (added by audit: every other rival preserves length 2, so
                arity was the one top-level component of the post-image that no
                case constrained);
  * ORDER     — the two nodes appear separator-FIRST; a build that appends the
                separator after the parsed annotation carries exactly the same
                multiset of nodes and is wrong only in position (added by audit
                for the same reason).

ONE input binder, ``typ`` (a bare type name; the ``require isBareName typ``
precondition pins it nonempty and identifier-shaped). The reject witnesses vary
it across six distinct names ("str", "int", "bool", "Point", "float",
"Decimal") so no rival is refuted at a single fixed input.

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case accounting
in the footer):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-typ-write`` rival writes through a read-only (``Acc(list_pred(typ),
    1/2)``) reference to the type-name carrier and is rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: ``typ`` is an
    immutable value, this bundle declares no ``mut`` binder, and there is no
    heap, aliasing, or permission system to subvert. There is no read-only input
    to overwrite, so the class is vacuous. No substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. The post-image's variable part is
    ``annotationNodes typ`` — a transparent ``def`` over the method's own
    argument (empty ``axioms`` region; no opaque callee). There is no answer key
    to echo; the honest cheapest CORRECT impl that inlines that ``def`` directly
    (``[DocNode.xref typ]``) is carried as a POSITIVE control instead (it doubles
    as proof the spec is not echo-vulnerable, since any WRONG node fails the pin).
    This is the nagini POS-FAB positive control — a behaviourally-correct
    reimplementation, not a wrong echo.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all four rivals against
    the one ``ensures`` clause, one per structural sub-behaviour above.
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
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is LOOP-FREE (a single ``::``
onto the ``def``'s output), so its extracted tester reduces under ``decide`` —
the loop-free tester pattern, NOT the backward-loop pattern. Each reject rival is
likewise a loop-free expression, so its tester also ``decide``s. Each reject
rival therefore carries a machine-checked refutation ``witness`` — a Velvet
tester statement ``propertyTypeNodesTester <name> = false`` at ONE concrete input,
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (the
tester ``decide``s to ``false`` — the rival's output violates the postcondition
there) and FAILS against the frozen solution (gold's tester ``decide``s to
``true``, so ``= false`` is refuted with "Tactic `decide` proved that the
proposition ... is false"), so each rejection is a genuine spec refutation and
not mechanical tactic breakage. Every witness input is a bare name satisfying the
``require`` clause, so it is not vacuously excluded. No witness binds a
hypothesis (every input is a concrete literal that decides the tester), so no
consistency probe is needed. No banned token (sorry/admit/native_decide/axiom).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real ``_parse_annotation`` callee; that
is G-AX's job (axiom_check.py / mapping.md §3.1) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9591"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, everything strictly
# ---- BETWEEN the method's `-- impl-start` / `-- impl-end` (the comment lines
# ---- there also live inside the elided impl region). Every variant replaces
# ---- exactly this text, so each edit lies wholly inside the one
# ---- -- impl-start .. -- impl-end region and same_spec holds by construction
# ---- (both facts asserted at load by _swap).
_IMPL = (
    "    let annotations := annotationNodes typ\n"
    "    let result := DocNode.text \": \".toList :: annotations\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# elided from the spec view); rivals leave it as `loom_solve`, so the wrong impl
# leaves the postcondition goal unsolved and the rival MODULE fails to build —
# which is what expect="reject" requires. The witness, not the module build, is
# what attributes the rejection to the spec.
_PROOF = "prove_correct propertyTypeNodes by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes /
    admissibility, whose residual goal differs from the frozen one)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `propertyTypeNodesTester typ = false` says the extracted program's result
# ---- violates the postcondition at that concrete input (the tester
# ---- short-circuits to `true` when the `require` clause is false, so every
# ---- witness below uses a bare name that satisfies `isBareName`). Checked in a
# ---- file whose `prove_correct` block is stripped, so no tactic script can mask
# ---- the verdict; both the rival and the frozen impl are loop-free, so both
# ---- testers reduce under `decide`.
def _witness(call):
    return ("extract_program_for propertyTypeNodes\n"
            "prove_precondition_decidable_for propertyTypeNodes\n"
            "prove_postcondition_decidable_for propertyTypeNodes\n"
            "derive_tester_for propertyTypeNodes\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — DIRECT FABRICATION. A structurally
    # different but CORRECT impl that MUST verify, else SPEC-TOO-STRONG. Instead
    # of routing the type name through the parser model `annotationNodes`, it
    # builds the cross-reference node DIRECTLY as `[DocNode.xref typ]`. Since
    # `annotationNodes typ` IS `[DocNode.xref typ]` (the load-bearing clause is
    # grounded in the input, not an opaque answer key), this is exactly the node
    # the real parser yields for a bare name — a behaviourally-correct
    # reimplementation, so it MUST verify. Doubles as the honest positive control
    # for the no-ungrounded-oracle finding. The `def` is no longer syntactically
    # called, so the frozen proof is retuned by one `rfl` (elided from spec view).
    # Verified out-of-band with a real build. Ports nagini POS_FAB.
    # =====================================================================
    {
        "id": "pos-direct-fabrication",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    return (DocNode.text \": \".toList :: [DocNode.xref typ])",
            "prove_correct propertyTypeNodes by\n  loom_solve\n  rfl"),
        "rationale": (
            "structurally-different CORRECT impl: build the cross-reference node "
            "DIRECTLY as `[DocNode.xref typ]` instead of routing through the "
            "parser model. The clause is grounded in the input arg `typ` (empty "
            "axioms region, no opaque answer key), so this is exactly the node the "
            "real parser yields for a bare name (behaviourally correct). MUST "
            "verify, else SPEC-TOO-STRONG. Also the honest positive control for "
            "the no-ungrounded-oracle finding: any WRONG node fails the pin, so a "
            "wrong echo cannot verify. Ports nagini POS_FAB."
        ),
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — LOCAL REORDER. Build both nodes into
    # independent typed locals FIRST, then cons them in the spec-mandated order.
    # Identical values, different control shape; keeps the whole construction, so
    # the frozen `loom_solve` closes the byte-identical obligation. Verified
    # out-of-band with a real build. Ports nagini POS_REORDER.
    # =====================================================================
    {
        "id": "pos-local-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let sep := DocNode.text \": \".toList\n"
            "    let annotations := annotationNodes typ\n"
            "    return (sep :: annotations)"),
        "rationale": (
            "a correct impl with a DIFFERENT local structure: bind the leading "
            "separator node and the parsed annotation to independent locals, then "
            "cons them in the spec-mandated order. Value flow is unchanged, so the "
            "single `ensures` still discharges and the frozen proof closes as-is. "
            "Ports nagini POS_REORDER: if it fails => SPEC-TOO-STRONG (over-fit to "
            "the exact frozen local-binding form)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-type-str. That case established
    # the read-only fractional-permission precondition on the F2P-shaped `:type:
    # str` input. This method has no permission surface; its only precondition is
    # `isBareName typ`. The re-aimed probe asserts, via one in-region `assert` at
    # the F2P-shaped bare name "str", that (a) the `require` clause ADMITS a normal
    # property type name and (b) the post-image is NON-DEGENERATE there: it renders
    # the two-node list `[text ": ", xref "str"]` (both nodes present, the type as
    # a genuine cross-reference), so the obligation is neither unsatisfiable (else
    # PRECOND-TOO-STRONG) nor a collapse. The impl is kept verbatim so the method's
    # own `ensures` discharges too; the proof clears the extra assert goal with
    # `all_goals decide` (elided from the spec view). Verified out-of-band.
    # =====================================================================
    {
        "id": "admiss-type-str",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (isBareName \"str\".toList = true ∧\n"
            "       (DocNode.text \": \".toList :: annotationNodes \"str\".toList)\n"
            "         = [DocNode.text \": \".toList, DocNode.xref \"str\".toList]))\n"
            "    let annotations := annotationNodes typ\n"
            "    let result := DocNode.text \": \".toList :: annotations\n"
            "    return result",
            "prove_correct propertyTypeNodes by\n  loom_solve\n  all_goals decide"),
        "rationale": (
            "the `require isBareName typ` clause admits the F2P-shaped normal "
            "property type name \"str\" AND the post-image is non-degenerate there: "
            "it renders `[text \": \", xref \"str\"]` (both the inert separator and "
            "the type-as-cross-reference present), so the obligation is neither "
            "unsatisfiable (else PRECOND-TOO-STRONG) nor a collapse. The in-region "
            "assert must discharge; the impl is kept verbatim so the method's own "
            "`ensures` discharges too. Re-aimed from nagini admiss-type-str, whose "
            "read-only fractional-permission half has no counterpart on this "
            "referentially-transparent carrier."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Each rival is a loop-free expression
    # so its extracted tester `decide`s; the frozen spec is untouched. All four
    # attack the single `ensures` clause, one per structural sub-behaviour, and
    # the input binder `typ` is varied across four distinct bare names.
    # =====================================================================
    {
        "id": "separator-as-xref",
        "kind": "uniqueness",
        "expect": "reject",
        # Build the leading separator node as a cross-reference instead of inert
        # text. The text ": " is still correct, but node 0's KIND is wrong.
        "module": _impl("    return (DocNode.xref \": \".toList :: annotationNodes typ)"),
        "refinement": (
            "a faithful real patch emitting the separator as a cross-reference "
            "(routing the literal \": \" through the annotation parser instead of "
            "an inert text node) would make the F2P assertion — whose first child "
            "must be a plain text node, not a cross-reference — fail; the harness "
            "compares node kinds, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the SEP-KIND sub-behaviour of `out = DocNode.text \": "
            "\".toList :: annotationNodes typ`: node 0 MUST be a `DocNode.text` "
            "(inert), but the rival emits a `DocNode.xref`. The text still matches, "
            "so only the kind flag of node 0 diverges — the exact inert-vs-xref "
            "distinction a text-only proxy would miss. Refuted at typ=\"str\". If "
            "it verified => SPEC-TOO-WEAK. Ports nagini separator-as-xref."
        ),
        "witness": _witness('propertyTypeNodesTester "str".toList'),
    },
    {
        "id": "type-as-inert-text",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: render the type as an inert text node instead of a
        # cross-reference. Two nodes, correct separator, correct type TEXT, but the
        # type node's KIND is text, not xref — the load-bearing discriminator.
        "module": _impl("    return (DocNode.text \": \".toList :: [DocNode.text typ])"),
        "refinement": (
            "this IS the pre-patch shape — rendering the type as inert literal "
            "text instead of a cross-reference. The failing test now expects the "
            "type to be a cross-reference node; an inert text node fails the "
            "node-kind comparison. It is exactly the bug the gold patch fixes and "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from the TYPE-KIND sub-behaviour: `annotationNodes typ` pins "
            "node 1 to a `DocNode.xref` (a cross-reference), but the rival emits a "
            "`DocNode.text`. This is the load-bearing discriminator of the fix — "
            "the type must be navigable, not inert. Refuted at typ=\"int\". If it "
            "verified => SPEC-TOO-WEAK (admits the bug). Ports nagini "
            "type-as-inert-text."
        ),
        "witness": _witness('propertyTypeNodesTester "int".toList'),
    },
    {
        "id": "wrong-separator-text",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the separator as ":" (dropping the trailing space) instead of ": ".
        # Node 0's kind is correct (text), but its text is one code point short.
        "module": _impl("    return (DocNode.text \":\".toList :: annotationNodes typ)"),
        "refinement": (
            "a faithful real patch emitting the separator text as \":\" (dropping "
            "the trailing space) would render `:str` flush against the type "
            "instead of the expected `: str`; the failing test pins the leading "
            "child text to exactly \": \", so a one-character-short separator fails "
            "the comparison and would NOT resolve."
        ),
        "rationale": (
            "REJECT from the SEP-TEXT sub-behaviour: node 0's text MUST be the two "
            "code points \": \" (colon + space), but the rival drops the space. The "
            "kind is correct (text), so the rejection isolates the text clause. "
            "Refuted at typ=\"bool\". If it verified => SPEC-TOO-WEAK. Ports nagini "
            "wrong-separator-text."
        ),
        "witness": _witness('propertyTypeNodesTester "bool".toList'),
    },
    {
        "id": "wrong-type-text",
        "kind": "uniqueness",
        "expect": "reject",
        # Build the type node as a cross-reference (correct KIND) but carrying the
        # SEPARATOR text ": " as its target instead of the type name `typ`.
        "module": _impl("    return (DocNode.text \": \".toList :: [DocNode.xref \": \".toList])"),
        "refinement": (
            "a faithful real patch whose cross-reference carried the wrong target "
            "text (not the type name) would render a reference to the wrong "
            "target; the failing test asserts the cross-reference's text is exactly "
            "the type name, so a node carrying any other text fails and would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the TYPE-TGT sub-behaviour: `annotationNodes typ` pins "
            "node 1's cross-reference target to the type name `typ`, but the rival "
            "carries the constant \": \". The kind is correct (xref), so the "
            "rejection isolates the target clause. Note the nagini sibling called "
            "this rival \"correct only for the degenerate typ == ': '\"; on THIS "
            "carrier that sub-domain does not exist, since `isBareName \": \"` is "
            "`false` (checked: `example : isBareName \": \".toList = false := by "
            "decide` elaborates), so the precondition excludes the one input where "
            "the rival would have agreed with gold. The rival is therefore wrong "
            "EVERYWHERE in the admitted domain, not merely on part of it. Refuted "
            "at typ=\"Point\". If it verified => SPEC-TOO-WEAK. Ports nagini "
            "wrong-type-text."
        ),
        "witness": _witness('propertyTypeNodesTester "Point".toList'),
    },
    # ---------------------------------------------------------------------
    # ADDED BY AUDIT. The four ported rivals all perturb a FIELD of one of the
    # two nodes and therefore all return a length-2 list in the mandated order.
    # That left two top-level components of the post-image — how MANY nodes and
    # in WHICH order — unattacked by every case, so a spec that pinned only the
    # node contents and not the list shape would have passed the battery. These
    # two rivals close that gap. Both witnesses rebuilt against rival (exit 0)
    # and against the frozen solution (exit 1, `decide` proved the tester is
    # true — a semantic refutation, not a missing identifier).
    # ---------------------------------------------------------------------
    {
        "id": "missing-separator-node",
        "kind": "uniqueness",
        "expect": "reject",
        # Return ONLY the parsed annotation, dropping the leading separator
        # node. Node contents are individually correct; the list is one short.
        "module": _impl("    return (annotationNodes typ)"),
        "refinement": (
            "a faithful real patch that handed the type to the annotation parser "
            "but omitted the leading literal separator would render the type "
            "flush with no \": \" before it; the failing test pins the annotation's "
            "children to a leading plain-text \": \" FOLLOWED by the "
            "cross-reference, so a single-child annotation fails the comparison "
            "and would NOT resolve."
        ),
        "rationale": (
            "REJECT from the ARITY sub-behaviour: the post-image is a CONS — the "
            "separator node onto the parser's output — so the result must contain "
            "both nodes, but the rival returns only the parsed annotation. Every "
            "other rival keeps length 2, so this is the only case that constrains "
            "the list's length rather than its contents. Refuted at typ=\"float\". "
            "If it verified => SPEC-TOO-WEAK (the spec would pin node contents "
            "while admitting a dropped separator)."
        ),
        "witness": _witness('propertyTypeNodesTester "float".toList'),
    },
    {
        "id": "nodes-out-of-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Both nodes present and both individually correct, but appended in the
        # reverse order: the annotation first, the separator last.
        "module": _impl(
            "    return (annotationNodes typ ++ [DocNode.text \": \".toList])"),
        "refinement": (
            "a faithful real patch that appended the literal separator AFTER the "
            "parsed annotation would render the type first and the \": \" trailing "
            "it; the failing test pins the leading child to the plain-text \": \" "
            "and the following child to the cross-reference, so a transposed pair "
            "fails the ordered child comparison and would NOT resolve."
        ),
        "rationale": (
            "REJECT from the ORDER sub-behaviour: the post-image fixes the "
            "separator FIRST and the parsed annotation after it. This rival "
            "carries exactly the same two nodes, each individually satisfying its "
            "own kind and text clause, and is wrong ONLY in position — so it is "
            "the case that shows the spec constrains sequence and not just node "
            "membership. Refuted at typ=\"Decimal\". If it verified => "
            "SPEC-TOO-WEAK (a multiset-shaped spec would admit it)."
        ),
        "witness": _witness('propertyTypeNodesTester "Decimal".toList'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING. The nagini sibling has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus a 2-probe AXIOM lane.
# This bundle models the SAME purely-functional core — the two-node child list of
# the rendered property type annotation — over `List DocNode` instead of the
# nagini `List[Node]` carrier, and it models ONLY the `if typ:` (present) branch
# the fix touches, with the type name pinned via a transparent parser `def`
# instead of nagini's `@Pure` oracle + list-permission machinery.
#
#   nagini case              -> here                        disposition
#   -----------------------------------------------------------------------
#   pos-direct-fabrication   -> pos-direct-fabrication      PORTED
#   pos-local-reorder        -> pos-local-reorder           PORTED
#   admiss-type-str          -> admiss-type-str             PORTED (re-aimed)
#   frame-typ-write (W1)     -> (none)                      VACUOUS
#   separator-as-xref (W2)   -> separator-as-xref           PORTED
#   type-as-inert-text (W3)  -> type-as-inert-text          PORTED
#   wrong-separator-text(W4) -> wrong-separator-text        PORTED
#   wrong-type-text (W5)     -> wrong-type-text             PORTED
#   emit-when-absent (W6)    -> (none)                      NOT MODELED
#   AXIOM_TESTS (2)          -> (none)                      DROPPED (G-AX lane)
#   (no nagini source)       -> missing-separator-node      ADDED BY AUDIT
#   (no nagini source)       -> nodes-out-of-order          ADDED BY AUDIT
#
# 9 velvet SPEC cases: 2 soundness, 1 admissibility, 6 uniqueness. Every nagini
# case that attacks a clause THIS bundle models is ported, plus two rivals the
# audit added for post-image components no nagini case had a counterpart for.
#
# ADDED BY AUDIT (list-shape rivals). The four ported rivals each perturb a
#   FIELD of one of the two nodes, so all four return a length-2 list in the
#   mandated order: ARITY and ORDER — the two top-level components of the
#   post-image — were constrained by no case. `missing-separator-node` drops the
#   separator (length 1, contents individually correct) and `nodes-out-of-order`
#   transposes the pair (same two nodes, wrong positions). Both were landed with
#   real builds: module fails to verify, witness elaborates against the rival
#   (exit 0) and fails against the frozen solution (exit 1) with "`decide`
#   proved that the proposition ... is false" — gold's tester is true there, so
#   both are semantic refutations rather than tactic breakage.
#
# PORTED (positives): POS_FAB fabricated the cross-reference node directly rather
#   than routing through the parser callee — carried across intact as
#   `[DocNode.xref typ]` (definitionally the parser model's output on a bare
#   name), with the frozen proof retuned by one `rfl`. POS_REORDER staged the
#   nodes into locals before appending — carried across as two independent
#   `let`-bound locals consed in order. Both verified out-of-band with real builds.
# PORTED-RE-AIMED (admissibility): nagini admiss-type-str established the
#   read-only fractional-permission precondition (`Acc(list_pred(typ),1/2)` + the
#   guarded len>0 clause) on the F2P-shaped `:type: str` input. This backend has
#   no permission surface; its only precondition is `isBareName typ`. Re-aimed to
#   assert that clause admits "str" AND the post-image is non-degenerate there
#   (the full two-node `[text ": ", xref "str"]`).
# PORTED (rivals): the four nagini value-rivals port directly to the four
#   structural sub-behaviours of the single `ensures` clause:
#     W2 separator-as-xref  -> SEP-KIND  (node 0 kind: text vs xref)
#     W3 type-as-inert-text -> TYPE-KIND (node 1 kind: xref vs text — THE fix)
#     W4 wrong-separator-text -> SEP-TEXT (node 0 text: ": " vs ":")
#     W5 wrong-type-text    -> TYPE-TGT  (node 1 target: typ vs ": ")
#   Each carries a machine-checked tester witness that ELABORATES against the
#   rival (`= false` decides) and FAILS against gold (`= true`, so `= false` is
#   refuted) — two real builds per case, verified out-of-band.
# VACUOUS (W1 frame-typ-write): the nagini rival writes through a read-only (1/2)
#   reference to the type-name carrier and is rejected for insufficient
#   permission. Velvet is referentially transparent, `typ` is an immutable value,
#   no `mut` binder, no heap, no aliasing, no permission system. There is no
#   read-only input to overwrite. No substitute fabricated (porting map: vacuous).
# NOT MODELED (W6 emit-when-absent) — audit re-derivation, INEXPRESSIBLE here and
#   demonstrated, not asserted: the no-annotation case would have to be reached
#   at the empty type name, and `require isBareName typ` excludes it
#   (`isBareName [] = false` by the `[] => false` arm — checked with a real
#   build). The tester short-circuits to `true` whenever the require clause is
#   false, so a witness stated at the absent input cannot refute ANY rival: built
#   `propertyTypeNodesTester [] = false` against the most permissive rival
#   possible (`return []`) and it FAILED, exit 1, "`decide` proved that the
#   proposition propertyTypeNodesTester [] = false is false". No witness exists
#   at the only input that distinguishes the absent arm, so no reject case can be
#   written. The original narrative below (carrier narrowing) is the same
#   disposition reached by argument; the build is the evidence.
# NOT MODELED (W6 emit-when-absent): the nagini spec carries a `present: bool`
#   binder and a clause pinning `not present ⟹ len(Result())==0`. This velvet
#   bundle models ONLY the branch that fires when a type IS declared (the `if
#   typ:` true branch the fix touches); it has no `present` binder and no
#   empty-when-absent clause — the no-annotation arm is out of the modeled surface
#   (carrier narrowing). W6 attacks a clause this bundle does not model, so it has
#   no counterpart. This is a KNOWN GAP relative to nagini, not a spec defect on
#   the modeled surface: the F2P behaviour the fix changes is entirely inside the
#   declared-type branch, which every ported rival attacks.
# DROPPED (AXIOM_TESTS): the nagini file's two axiom-soundness / containment
#   probes over the real `_parse_annotation` callee are G-AX's job (axiom_check.py
#   / mapping.md §3.1); the G-PBT gate ignores AXIOM_TESTS regardless.
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
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# CLAUSE / BINDER / POINT COVERAGE. The single load-bearing `ensures` clause is
#   attacked on ALL SIX of its structural sub-behaviours (SEP-KIND, TYPE-KIND,
#   SEP-TEXT, TYPE-TGT, plus ARITY and ORDER added by the audit), so no top-level
#   component of the post-image — neither the contents of either node, nor how
#   many nodes there are, nor their sequence — is left unattacked. The sole input
#   binder `typ` is varied across six distinct bare names — "str", "int", "bool",
#   "Point", "float", "Decimal" — so pts=6 and no binder is held fixed by every
#   witness; the six names are meaningfully distinct rather than respellings,
#   since each rival's refutation is computed from the name it is refuted at
#   (TYPE-TGT and ORDER carry `typ` into the post-image directly). Both soundness
#   positives and the admissibility case defend the clause on gold-shaped
#   computations; the admissibility assert is load-bearing, not decorative —
#   falsifying its post-image claim (xref -> text) makes the module FAIL to
#   build ("`decide` proved that the proposition ... is false").
#
# WITNESS MECHANICS: the frozen impl and every rival are loop-free, so the
#   `derive_tester_for propertyTypeNodes` + `decide` path is LIVE (the tester
#   reduces). Every witness states `propertyTypeNodesTester <name> = false`,
#   checked in a file whose `prove_correct` block is stripped so no tactic script
#   masks the verdict. All SIX checked with scripts/lean_verify.sh: the rival
#   build elaborates (exit 0, tester decides to false), the gold build fails
#   (exit 1, "decide proved ... is false", i.e. gold's tester is true). Every
#   gold-side failure was READ, not just counted: each is that semantic message,
#   none is an unknown identifier, a type error, or a stuck reduction, so each
#   rejection is attributable to the spec. No witness binds a hypothesis, so no
#   consistency probe is needed.
#
# AUDIT SPEC PROBES (recorded so the next reader need not redo them). Neither
#   direction found a defect in the frozen spec:
#   * SPEC-TOO-WEAK: 7 further WRONG impls beyond the shipped rivals were built
#     and all 7 were REJECTED — drop-separator, swap-order, hardcode the
#     F2P-shaped answer `[text ": ", xref "str"]` (refuted at a DIFFERENT name,
#     so the spec is not satisfiable by pinning one literal), separator as
#     `punct` instead of `text`, an extra trailing `punct` node, empty result,
#     and an upper-cased xref target. No wrong impl verified.
#   * SPEC-TOO-STRONG: 4 CORRECT reshapes were all provable — an explicit
#     two-element list literal `[text ": ", xref typ]`, `[text ": "] ++
#     annotationNodes typ`, a `match` on the input's cons shape, and a
#     reverse-of-append build. Each needed only a retuned tactic body (`rfl`, or
#     the frozen `loom_solve` alone), which the elided proof region permits. The
#     spec rejects no faithful correct impl that was tried.
AXIOM_TESTS = []
