"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7454 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical header) and swaps
in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over a single read-only sequence input).

  referenceForName (name : List Char) return (out : TypeReference)
        ensures out.domain = "py".toList
        ensures out.target = name
        ensures out.label  = name
        ensures out.kind   = desiredKind name
        ensures name = "None".toList → out.kind = .valueRef
        ensures name ≠ "None".toList → out.kind = .classRef
        ensures out.kind = .valueRef ↔ name = "None".toList

The method builds one resolution record for one name occurring in a type
annotation. The result record carries FOUR observable fields — a fixed domain,
the target name, the shown label, and the resolution kind — and the post-image
pins each of them. ``name`` is the SINGLE free input binder: the post-image must
hold for every value it takes, which is what makes the partial-domain rivals
below refutable at a concrete point. ``desiredKind`` is a fully unfolded ``def``
of the argument (a value/class split on ``name = "None".toList``); the kind is
therefore a total function of the input, not an opaque answer key — there is no
*wrong* echo an impl could return, and the cheapest faithful impl must still test
the name and copy it through.

CARRIER NOTE — FULLY DECIDABLE. Every field of ``TypeReference`` is a
``DecidableEq`` datum (a ``RefKind`` enum or a ``List Char``), ``desiredKind`` is
a concrete ``def`` over the input, and there is NO ``opaque`` leaf and NO consumed
``axiom`` anywhere in the spec. So every reject witness closes by ``decide`` at a
concrete literal input; conditioning on a carrier term is never needed here.

ADVERSARIAL READ of the classes (the nagini sibling reasoned over its own carrier;
each argument is carried over and re-mechanised for this backend):
  * FRAME-MUTATION — VACUOUS on this backend. The sibling writes a code point
    through the read-only ``text`` argument to trip INSUFFICIENT PERMISSION under
    a fractional list_pred. This backend is referentially transparent, has no
    heap and no aliasing, and this bundle declares no ``mut`` binder — there is no
    read-only input to overwrite and no substitute probe to fabricate. Instead the
    read-only frame is stated as postconditions (``out.target = name``,
    ``out.label = name``, ``out.domain = "py".toList``), and those clauses ARE
    attacked by transparent rivals below.
  * DIVERGENCE / NON-TERMINATION — NOTHING TO PORT. The nagini sibling carries no
    ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case, so there is no
    divergence rival to re-express and no ``partial``-semantics known-hole to
    record for this instance (the class only exists to port when the sibling
    ships one).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the method's own argument; there is no opaque answer key to echo.
    The positive controls are honest cheapest-reshape controls.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the ``name`` domain
    but diverging on a sub-domain (the ``None`` singleton for the kind split; the
    non-empty name for the dropped-last-element target; and the NEAR-MISS
    ``kind-widened-guard``, wrong on a single name further out that every other
    rival gets right).
  * FRAME PRESERVATION — APPLIES: the post-image echoes the input into two fields
    (target and label) and fixes a third (domain); a rival can get the kind right
    and still corrupt one of the framed fields, so each framed field is attacked
    on its own so its witness sits at a value the others do not probe.

WITNESS PLACEMENT. No two rivals share a refutation point. The seven reject
witnesses move the single binder ``name`` across ``"None"``, ``"int"``,
``"str"``, ``"Dict"``, ``"List"``, ``"x"`` and ``"NoneType"``: the kind rivals
are refuted on the two sides of the value/class split (``"None"`` and
``"int"``), each frame rival at a name distinct from those and from each other
so that framed field's dependence on ``name`` is observable at a fresh point,
and ``kind-widened-guard`` at the one point (``"NoneType"``) where every other
rival AGREES with the frozen impl — the near-miss, which is what stops the
battery from certifying only coarse rivals.

AXIOM lane: this bundle declares NO ``axiom`` and NO A-reference deep model — the
resolution kind is modeled deeply by ``desiredKind`` and the record fields are
constructors. There is no axiom-soundness obligation for this gate to probe, and
the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7454"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- surgery anchors: substrings lying wholly inside the impl region and
# ---- unique in the file (both facts asserted at load by _swap). ----

# The kind dispatch (the changed operation).
_KIND = (
    '    let kind : RefKind := if name = "None".toList then .valueRef else .classRef\n'
)
# The framed record fields.
_TARGET = "        target := name,\n"
_DOMAIN = '        domain := "py".toList,\n'
_LABEL = "        label  := name }\n"

# The frozen proof body (tactic script only; elided from the spec view, so the
# admissibility case that adds an in-region assert may retune it without touching
# the spec or the `prove_correct` header).
_PROOF = (
    "prove_correct referenceForName by\n"
    "  loom_solve\n"
    "  simp_all [desiredKind]"
)
for _a in (_KIND, _TARGET, _DOMAIN, _LABEL, _PROOF):
    assert _BASE.count(_a) == 1, f"anchor drift: {_a!r}"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester
# ---- machinery: `referenceForNameTester name = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. Every argument is a concrete literal
# ---- so `decide` reduces without touching any opaque term (there are none). ----
_TESTER = (
    "extract_program_for referenceForName\n"
    "prove_precondition_decidable_for referenceForName\n"
    "prove_postcondition_decidable_for referenceForName\n"
    "derive_tester_for referenceForName\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and the frozen proof
    # script (`simp_all [desiredKind]` closes each reshape).
    # =====================================================================
    {
        "id": "pos-kind-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: test the COMPLEMENT of the value name first, assigning the
        # class kind in the taken arm and the value kind in the else. Same
        # classification, different control shape.
        "module": _swap(
            _BASE, _KIND,
            '    let kind : RefKind := if name ≠ "None".toList then .classRef else .valueRef\n'),
        "rationale": "a correct but branch-reordered classifier must verify; "
                     "`out.kind = desiredKind name` and both directional clauses "
                     "are unchanged. If it fails => SPEC-TOO-STRONG on branch "
                     "order.",
    },
    {
        "id": "pos-kind-prebound",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: pre-bind the class kind to a local, overwrite to the value
        # kind only for the singleton value name, then use it. Different data
        # shape (one assignment path), provably equal value.
        "module": _swap(
            _BASE, _KIND,
            "    let base : RefKind := .classRef\n"
            '    let kind : RefKind := if name = "None".toList then .valueRef else base\n'),
        "rationale": "a correct impl that pre-binds the class kind to a local "
                     "before selecting must verify (structurally different data "
                     "shape, same value). If it fails => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-frame-reshaped",
        "kind": "soundness",
        "expect": "verify",
        # Both positives above reshape only the KIND dispatch, so the two
        # carry-through frame clauses were defended solely by impls that echo
        # `name` by a bare variable reference — which the frozen proof closes by
        # reflexivity. This positive carries the name through in a shape that is
        # NOT definitionally equal for a variable input: neither `name.map id`
        # nor `name ++ []` reduces to `name` without a lemma, so the frame
        # clauses must be genuinely reproven rather than closed by `rfl`. The
        # proof body is retuned accordingly (allowed — the tactic body is elided
        # from the spec view and the `prove_correct` header is byte-identical).
        "module": _swap(
            _swap(
                _swap(_BASE, _TARGET, "        target := name.map id,\n"),
                _LABEL, "        label  := name ++ [] }\n"),
            _PROOF,
            "prove_correct referenceForName by\n"
            "  loom_solve\n"
            "  all_goals simp_all [desiredKind, List.map_id_fun', id_eq]"),
        "rationale": "a correct impl that echoes the name into the two framed "
                     "fields through expressions that are provably but not "
                     "DEFINITIONALLY the name must verify. This is the only "
                     "positive that exercises `out.target = name` / `out.label = "
                     "name` against a non-reflexive witness, so without it the "
                     "two frame clauses are attacked but never non-trivially "
                     "defended. If it fails => SPEC-TOO-STRONG on the frame.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares NO `require` clause (the domain is
    # total), so the sibling's "a normal input satisfies the precondition"
    # probe is vacuous: nothing could exclude an F2P-shaped input. It is
    # re-aimed at the residual admissibility risk on a total domain — that the
    # post-image is UNSATISFIABLE / DEGENERATE at the interesting point. This
    # case discharges an in-region assert, at concrete inputs, that the kind
    # classification is NON-DEGENERATE: the kind chosen for the singleton value
    # name differs from the kind chosen for an ordinary type name. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof body is retuned only to clear the extra assert goal
    # by `decide` (allowed — the tactic body is elided from the spec view). The
    # assert is live: a false claim about the same point leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-kind-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _KIND,
                "    assert (with_name_prefix `admiss\n"
                '      (desiredKind "None".toList ≠ desiredKind "int".toList))\n'
                + _KIND),
            _PROOF,
            "prove_correct referenceForName by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [desiredKind]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at a "
                     "concrete F2P-shaped point: the resolution kind for the "
                     "singleton value name is distinct from the kind for an "
                     "ordinary type name, so the classification genuinely "
                     "distinguishes the cases the fix cares about. The in-region "
                     "assert must discharge (else an unsatisfiable/degenerate "
                     "obligation); the impl is kept verbatim so the ensures "
                     "clauses discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete literal input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test
    # (tests/test_domain_py.py::test_parse_annotation, which pins the resolution
    # kind, domain, target, and shown text for both an ordinary type name and
    # the singleton value name).
    # =====================================================================
    {
        "id": "kind-always-type",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: classify EVERY name as a class reference,
        # ignoring the value/class split. Correct on every name except the
        # singleton value name.
        "module": _swap(_BASE, _KIND, "    let kind : RefKind := .classRef\n"),
        "refinement": "this is the pre-patch classifier (every name resolved as a "
                      "class reference); for the singleton value name the failing "
                      "test wants the value kind but this yields the class kind, "
                      "so the faithful patch would NOT resolve.",
        "rationale": "REJECT from the value-side clause `name = \"None\".toList → "
                     "out.kind = .valueRef` (and `out.kind = desiredKind name`): "
                     "the singleton value name must get the value kind and this "
                     "impl gives the class kind. Refuted at name = \"None\", one "
                     "of the two split sides.",
        "witness": _TESTER +
                   'example : referenceForNameTester "None".toList = false := by\n'
                   "  decide\n",
    },
    {
        "id": "kind-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the classifier: the singleton value name -> class kind, every
        # other name -> value kind. Fails BOTH directional clauses and the
        # kind equality everywhere.
        "module": _swap(
            _BASE, _KIND,
            '    let kind : RefKind := if name = "None".toList then .classRef else .valueRef\n'),
        "refinement": "this reverses the rule (class kind for the singleton value "
                      "name, value kind for every ordinary type name). For an "
                      "ordinary type name the failing test wants the class kind "
                      "and this yields the value kind (and symmetrically for the "
                      "value name), so it would NOT resolve.",
        "rationale": "REJECT from the class-side clause `name ≠ \"None\".toList → "
                     "out.kind = .classRef`: an ordinary type name must get the "
                     "class kind and this impl gives the value kind. Refuted at "
                     "name = \"int\", the other split side from kind-always-type "
                     "(so the two kind rivals do not share a point).",
        "witness": _TESTER +
                   'example : referenceForNameTester "int".toList = false := by\n'
                   "  decide\n",
    },
    {
        "id": "target-echo-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Pin the target field to the constant singleton value name for EVERY
        # input, ignoring `name`. Correct only when the input IS that name; the
        # closest analogue of an "oracle echo" — but the target frame is
        # `out.target = name`, so a constant cannot satisfy it for any other name.
        "module": _swap(_BASE, _TARGET, '        target := "None".toList,\n'),
        "refinement": "a counterpart that hard-codes the target to the value name "
                      "regardless of the input points every name at the value "
                      "name's documentation, so the failing test — which pins the "
                      "target to the input name — still fails. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the frame clause `out.target = name`: the "
                     "constant value name differs from the input for every name "
                     "that is not that value name. Refuted at name = \"str\".",
        "witness": _TESTER +
                   'example : referenceForNameTester "str".toList = false := by\n'
                   "  decide\n",
    },
    {
        "id": "target-prefix-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # Carry the name through but DROP its last element into the target
        # field. Correct only for the empty name; diverges on every non-empty
        # name. Fails `out.target = name`.
        "module": _swap(_BASE, _TARGET, "        target := name.dropLast,\n"),
        "refinement": "a counterpart that drops the last character of the name in "
                      "the target field points at the wrong (truncated) name, so "
                      "the failing test — which pins the target to the full input "
                      "name — still fails. It would NOT resolve.",
        "rationale": "REJECT from the frame clause `out.target = name`: dropping "
                     "the last element cannot equal the name for any non-empty "
                     "name. Refuted at name = \"Dict\" (target reads the 3-char "
                     "prefix, not the whole name) — a point no other rival uses, "
                     "so this rival's refutation is not confounded with the kind "
                     "split that `\"None\"` also sits on.",
        "witness": _TESTER +
                   'example : referenceForNameTester "Dict".toList = false := by\n'
                   "  decide\n",
    },
    {
        "id": "kind-widened-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS. Every other rival here disagrees with the frozen impl at one
        # of the five points the battery already probes, so a rival that is right
        # on all of those and wrong only FURTHER OUT would have gone uncaught.
        # This one widens the value-side guard to a second name that merely
        # begins with the value name: it agrees with the frozen classifier at
        # "None", "int", "str", "List" and "x", and diverges only at the longer
        # name. It is the tightest wrong classifier this spec must still refuse.
        "module": _swap(
            _BASE, _KIND,
            '    let kind : RefKind := if name = "None".toList ∨ name = "NoneType".toList then .valueRef else .classRef\n'),
        "refinement": "a counterpart whose value-side test also fires for the "
                      "longer spelling resolves that longer name as a value "
                      "instead of a class, so it points that name at the wrong "
                      "kind of documentation entry. The failing test pins the "
                      "kind for an ordinary type name, and this impl is wrong on "
                      "a name of exactly that sort, so it would NOT resolve.",
        "rationale": "REJECT from the biconditional `out.kind = .valueRef ↔ name "
                     "= \"None\".toList` (and the class-side clause `name ≠ "
                     "\"None\".toList → out.kind = .classRef`): the value kind is "
                     "reserved for exactly ONE name, and this impl hands it to a "
                     "second one. Refuted at name = \"NoneType\", a point every "
                     "other rival agrees with the frozen impl on — which is what "
                     "makes this the near-miss control rather than a restatement.",
        "witness": _TESTER +
                   'example : referenceForNameTester "NoneType".toList = false := by\n'
                   "  decide\n",
    },
    {
        "id": "domain-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the wrong fixed domain. Fails the domain frame clause for every
        # input.
        "module": _swap(_BASE, _DOMAIN, '        domain := "js".toList,\n'),
        "refinement": "a counterpart that resolves the reference in the wrong "
                      "documentation domain links it against the wrong domain's "
                      "inventory, so the failing test — which pins the domain — "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from the frame clause `out.domain = \"py\".toList`: a "
                     "different constant domain never equals the fixed expected "
                     "domain. Refuted at name = \"List\" (an ordinary type name "
                     "distinct from the kind rivals' points).",
        "witness": _TESTER +
                   'example : referenceForNameTester "List".toList = false := by\n'
                   "  decide\n",
    },
    {
        "id": "label-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the shown label (emit the empty label) instead of echoing the
        # name. Fails the label frame clause `out.label = name` for every
        # non-empty name — the label frame is INDEPENDENT of the target frame,
        # so a rival can carry the target through and still corrupt the label.
        "module": _swap(_BASE, _LABEL, "        label  := [] }\n"),
        "refinement": "a counterpart that drops the shown text of the reference "
                      "renders an empty link label instead of the name, so the "
                      "failing test — which pins the reference's shown text to the "
                      "name — still fails. It would NOT resolve.",
        "rationale": "REJECT from the frame clause `out.label = name`: the empty "
                     "label never equals a non-empty name. Refuted at name = "
                     "\"x\", the only witness that moves the binder to this "
                     "single-character point and the only rival attacking the "
                     "label frame independently of the target frame.",
        "witness": _TESTER +
                   'example : referenceForNameTester "x".toList = false := by\n'
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. 11 cases here (3 soundness positives, 1
# admissibility, 7 uniqueness rivals). The sibling battery has 8 cases (2
# soundness positives, 1 admissibility, 5 uniqueness rivals) over a SINGLE contracted
# function `make_cross_reference(text)` modeled on `List[int]` code points. This
# bundle contracts a SINGLE method `referenceForName` over `List Char`, so the
# port is close to one-to-one on the modeled behaviour; the sibling's four-field
# result maps onto this bundle's four-field `TypeReference`.
#
#   sibling case            -> here                       disposition
#   ---------------------------------------------------------------------
#   pos-kind-reorder        -> pos-kind-reorder           PORTED
#   pos-kind-prebound       -> pos-kind-prebound          PORTED
#   admiss-self-call        -> admiss-kind-nondegenerate  RE-AIMED
#   frame-mutate-text       -> (none)                     VACUOUS
#   kind-always-type        -> kind-always-type           PORTED
#   target-prefix-drop      -> target-prefix-drop         PORTED
#   kind-swapped            -> kind-swapped               PORTED
#   target-echo-name        -> target-echo-name           PORTED
#
# 6 ported, 1 re-aimed, 1 vacuous, 4 added (2 carrier frame clauses + 2 controls
# an audit found missing; see ADDED below).
#
# RE-AIMED (admissibility): the sibling establishes that the read-only
#   half-permission input is usable and a normal return reachable via an
#   in-region caller. This backend has no permissions and no `require` clause, so
#   nothing could exclude a normal input — that probe is vacuous. It is re-aimed
#   at the residual admissibility risk on a total domain: that the post-image is
#   UNSATISFIABLE / DEGENERATE at the interesting point. The case discharges a
#   concrete in-region assert that the resolution kind for the singleton value
#   name differs from the kind for an ordinary type name (the classification is
#   non-degenerate).
# VACUOUS (frame-mutate-text): the sibling writes into a read-only
#   half-permission input to trip INSUFFICIENT PERMISSION. This backend is
#   referentially transparent, has no heap or aliasing, and this bundle declares
#   no `mut` binder — there is no read-only input to overwrite and no substitute
#   probe. The read-only frame is instead stated as the `out.target = name` /
#   `out.label = name` / `out.domain = "py".toList` postconditions, and those
#   clauses ARE attacked (target-echo-name, target-prefix-drop, label-drop,
#   domain-wrong). Not fabricated.
#
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
# ADDED (4, no sibling counterpart — velvet-carrier frame clauses the sibling's
#   `List[int]` model did not separate, plus two controls an audit of this
#   battery found missing):
#   * domain-wrong. The velvet result carries a fixed `domain` field the sibling
#     did not model; without this rival the domain frame clause
#     `out.domain = "py".toList` would be defended (the positives) but never
#     attacked. Its faithful counterpart resolves in the wrong documentation
#     domain and leaves the failing test failing.
#   * label-drop. The velvet result carries a `label` (shown text) field
#     INDEPENDENT of `target`; the sibling collapsed the shown text into the same
#     carry-through as the target. Without this rival the label frame clause
#     `out.label = name` would be unattacked and a rival corrupting only the
#     shown text would go uncaught. Its faithful counterpart renders an empty link
#     label and leaves the failing test failing.
#   * kind-widened-guard (NEAR-MISS control). Every rival above disagrees with the
#     frozen impl at one of the points the battery already probes, so the battery
#     attested only that the spec catches COARSE wrong classifiers. This rival
#     agrees with the frozen impl at all five of those points and is wrong only at
#     a longer name that merely begins with the value name, which the
#     biconditional clause refuses. Measured: rival build exit 0, gold build exit
#     1 with `decide` proving the claim FALSE at `"NoneType"`.
#   * pos-frame-reshaped (non-reflexive frame control). Both ported positives
#     reshape only the kind dispatch, echoing `name` into the two framed fields by
#     a bare variable that the frozen script closes by reflexivity — so the frame
#     clauses were attacked but never non-trivially DEFENDED. This positive echoes
#     the name as `name.map id` / `name ++ []`, neither definitionally equal to
#     `name` for a variable input, so the frame clauses must be genuinely
#     reproven. Confirms the frame is not merely syntactically pinned.
#
# COVERAGE. Single input binder `name`, moved by the reject witnesses across
#   {"None", "int", "str", "Dict", "List", "x", "NoneType"} — pts = 7 distinct
#   input points, one per reject case, none shared. Independent top-level clauses
#   of the post-image and their attackers:
#     out.domain = "py".toList                -> domain-wrong
#     out.target = name                       -> target-echo-name, target-prefix-drop
#     out.label  = name                       -> label-drop
#     out.kind = desiredKind name             -> kind-always-type, kind-swapped
#     name = "None" -> valueRef               -> kind-always-type (fails at "None")
#     name ≠ "None" -> classRef               -> kind-swapped (fails at "int"),
#                                                kind-widened-guard (at "NoneType")
#     kind = valueRef ↔ name = "None"         -> both kind rivals, kind-widened-guard
#   Every independent top-level clause is both defended (>=1 verify) and attacked
#   (>=1 reject). No clause is left unattacked. The two frame clauses are
#   additionally defended NON-REFLEXIVELY by pos-frame-reshaped, and the kind
#   split is attacked at a near-miss (kind-widened-guard) as well as coarsely.
#
# AXIOM_TESTS: dropped. This bundle declares no `axiom` and no A-reference deep
#   model (the resolution kind is a concrete `def`, the record fields are
#   constructors), so there is nothing here for this gate to probe; the axiom
#   lane is G-AX's job.
AXIOM_TESTS = []
