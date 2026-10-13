"""properties.py — G-PBT falsification battery for django__django-12304 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts a single modeled function over a PRIMITIVE input (an integer identity)
and leans on two ``@ContractOnly`` axioms (``base_class_creation``,
``resolved_in_template``) plus @Pure oracle machinery. This Lean bundle models
the SAME single purely-functional behavior — build the enumerated-choices class,
observed at exactly two touched components — but with NO opaque callee: the
value→label association enters as plain DATA and the engine's invoke decision is
modeled directly as the transparent boolean ``templateWouldCall``. The carrier
is therefore fully ``decide``-able and no ``opaque`` term blocks any witness.

DEFENDED SURFACE (one modeled behavior, one input binder ``memberValues``).
``buildChoicesClass`` returns a ``ChoicesClass`` pinned at every observable, so
``problem_spec_buildChoicesClass`` has two INDEPENDENT top-level clauses:

  * (C1 — FRAME/PASS-THROUGH) ``result.value2label = memberValues`` — the
    value→label association is exactly the one built from the supplied members,
    unchanged. This is the directive-5 frame clause: the component that the
    behavior does NOT touch equals its input.
  * (C2 — THE FIX) ``templateWouldCall true result.doNotCallInTemplates false =
    false`` — the produced class carries the "do not invoke" flag, so a template
    engine encountering it as a resolved value leaves it intact. Because such a
    class is callable and does not alter data, "would not be invoked" forces the
    flag to be set. This is the behavioural discriminator: the whole point of the
    fix is that the flag is set to TRUE unconditionally, and the pre-fix
    behavior (no flag / absent flag) is exactly the omit rival below.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS as a heap attack. Lean is
    referentially transparent: an input carries no fractional permission, there
    is no read-only half-permission to overwrite and no aliasing to exploit. The
    nagini justification (the modeled function takes no read-only object
    parameter) carries over: no substitute is fabricated. What DOES survive is
    the frame POSTCONDITION clause C1, which two rivals below attack directly by
    corrupting the passed-through component.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: both clauses
    are pinned to terms built only from the input (``memberValues``) and literals
    (``true``/``false``). There is no opaque answer key an implementation could
    echo — the nagini ``resolved_in_template`` @Pure oracle collapses here into
    the transparent ``templateWouldCall``. In its place the battery carries
    honest cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: omitting the flag (pre-patch), setting it
    false, hardcoding the pass-through component, and corrupting it by prepend.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``refine ⟨rfl, rfl⟩`` is tuned to the
frozen definitional form — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it by ``decide``. Each was
checked to HOLD of its rival and to FAIL on the frozen solution (a genuine
``decide`` refutation, not a syntax error), so it discriminates rather than
asserting a tautology. The carrier is fully concrete, so no witness needs to
condition on an opaque term.

BINDER / POINT SPREAD. The single input binder ``memberValues`` is moved across
the reject witnesses rather than fixed at one convenient point: the empty list
``[]``, a singleton ``[(1,"Diamond")]``, a two-member list
``[(5,"Club"),(6,"Heart")]``, and ``[(7,"X")]``. Both independent clauses are
attacked: C2 by the omit and false rivals, C1 by the hardcode and prepend
rivals. No two rivals share a refutation point.

AXIOM lane: EMPTY here. The nagini ``AXIOM_TESTS`` (soundness + containment for
``base_class_creation`` and ``resolved_in_template``) belong to G-AX, which this
gate ignores; this bundle moreover declares NO ``opaque``/``axiom`` callee at
all, so there is nothing for an axiom lane to probe. Dropped, per the porting
map.

OMITTED nagini cases and why (full accounting in the submit ``assessment``):
  * ``AXIOM_TESTS`` (4 cases) — G-AX lane, dropped.
  * the nagini frame-mutation reasoning — vacuous on this carrier (no heap
    permissions); the surviving frame POSTCONDITION clause C1 is attacked
    instead.
"""
from pathlib import Path

INSTANCE = "django__django-12304"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the admissibility
# positive that re-proves, the proof region) so same_spec stays byte-identical.

# The whole gold impl body (signature line onward), for structural reshapes.
_GOLD_IMPL = (
    "    (memberValues : List (Int × String)) : ChoicesClass := Id.run do\n"
    "  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }\n"
    "  -- The value→label association is built from the class's members.\n"
    "  cls := { cls with value2label := memberValues }\n"
    "  -- Flag the class so a template engine leaves it intact instead of invoking it.\n"
    "  cls := { cls with doNotCallInTemplates := true }\n"
    "  return cls"
)

# The final flag-set assignment plus the return (the C2 line).
_I_FLAG_AND_RETURN = (
    "  cls := { cls with doNotCallInTemplates := true }\n"
    "  return cls"
)

# The flag-set assignment alone (unique — the init line binds it to `false`).
_I_FLAG_SET = "  cls := { cls with doNotCallInTemplates := true }"

# The pass-through assignment of the touched-but-unchanged component (C1 line).
_I_VALUE_ASSIGN = "  cls := { cls with value2label := memberValues }"

# The frozen proof body (proof region).
_P_FROZEN = "  intro memberValues\n  refine ⟨rfl, rfl⟩"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem STATEMENT byte-identical; the reshapes preserve the
    # definitional form so the frozen `refine ⟨rfl, rfl⟩` still closes (no helper
    # lemma, no axiom, no assumption token introduced).
    # =====================================================================

    # Ports nagini `pos-direct-construct`: build the class DIRECTLY with the flag
    # already set, bypassing the mutable accumulator, rather than constructing a
    # default and mutating the flag. The observable abstraction is identical.
    {
        "id": "pos-direct-construct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    (memberValues : List (Int × String)) : ChoicesClass :=\n"
            "  { value2label := memberValues, doNotCallInTemplates := true }",
        ),
        "rationale": "a correct, structurally-different impl (direct construction "
                     "with the flag set, bypassing the mutable accumulator) must "
                     "satisfy C1 (value2label = memberValues) and C2 (flag set so "
                     "templateWouldCall = false). Must verify, else the "
                     "postcondition is SPEC-TOO-STRONG. Proof: the record literal "
                     "reduces definitionally, so the frozen `refine ⟨rfl, rfl⟩` "
                     "closes. Ports nagini's direct-construction positive.",
    },

    # Ports nagini `pos-local-flag`: reshape the gold impl by binding the flag to
    # a typed local before assigning it. Same operations, different executable
    # shape; every proof obligation is preserved.
    {
        "id": "pos-local-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    (memberValues : List (Int × String)) : ChoicesClass := Id.run do\n"
            "  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }\n"
            "  cls := { cls with value2label := memberValues }\n"
            "  let flag : Bool := true\n"
            "  cls := { cls with doNotCallInTemplates := flag }\n"
            "  return cls",
        ),
        "rationale": "a local-variable reshape of the gold impl (flag bound to a "
                     "typed local, then assigned) must still verify; it changes "
                     "only executable shape, keeping both clauses. If it fails, "
                     "SPEC-TOO-STRONG (proof fragility). Proof: the local "
                     "zeta-reduces, so the frozen `refine ⟨rfl, rfl⟩` closes. "
                     "Ports nagini's local-flag positive. Defends the same "
                     "obligation via a different region than the direct-construct "
                     "positive.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input. The frozen
    # theorem carries NO precondition hypothesis (the behavior is total), so the
    # nagini precondition-admission probe has no binder to attack; the honest
    # analogue discharges the spec predicate by evaluation at the concrete F2P
    # scenario (the Suit choices, DIAMOND=1) alongside the frozen obligation.
    # Ports nagini `admiss-f2p-diamond`.
    # =====================================================================
    {
        "id": "admiss-f2p-diamond",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_FROZEN,
            "  intro memberValues\n"
            "  have _ground : problem_spec_buildChoicesClass [(1, \"Diamond\"), (2, \"Spade\")]\n"
            "      (implementation_buildChoicesClass [(1, \"Diamond\"), (2, \"Spade\")]) := by\n"
            "    refine ⟨rfl, rfl⟩\n"
            "  refine ⟨rfl, rfl⟩",
        ),
        "rationale": "the obligation is discharged at the concrete F2P-shaped input "
                     "(the Suit choices [(1,\"Diamond\"),(2,\"Spade\")]) by "
                     "`refine ⟨rfl, rfl⟩`, then the frozen obligation is closed "
                     "verbatim. Verifies (else the behavior is unsatisfiable at "
                     "exactly the input the F2P exercises — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, and the ground "
                     "instance is a `have` inside the existing tactic body. Ports "
                     "nagini's DIAMOND admissibility probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying rival
    # would be a true verify-does-not-imply-resolve break rather than an artifact,
    # and (b) a refutation witness pinning the violation at one concrete input,
    # checked to hold of the rival and fail on gold.
    # =====================================================================

    # ---- the prepatch kill: omit the flag entirely (nagini `weak-omit-flag`) ----
    {
        "id": "weak-omit-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: do not set the "do not invoke" flag, leaving it at the
        # default (unflagged). This is exactly the empty-diff pre-patch source.
        "module": _swap(_BASE, _I_FLAG_AND_RETURN, "  return cls"),
        "refinement": "its faithful real patch is the empty diff (the pre-patch "
                      "source), leaving the produced class unflagged. A template "
                      "engine then INVOKES the class with no arguments; the "
                      "required value argument is missing, the call raises, and the "
                      "resolved lookup fails — so the F2P template renders the "
                      "invalid fallback instead of the expected member label/value. "
                      "Does NOT resolve.",
        "rationale": "REJECT from C2 (templateWouldCall true result.flag false = "
                     "false): with the flag left at its default the class WOULD be "
                     "invoked, so C2 fails. This is the model_prepatch kill "
                     "(G-DIFF). Moves memberValues to a singleton; attacks the fix "
                     "clause.",
        "witness": (
            "example : ¬ problem_spec_buildChoicesClass [(1, \"Diamond\")]\n"
            "    (implementation_buildChoicesClass [(1, \"Diamond\")]) := by\n"
            "  unfold problem_spec_buildChoicesClass implementation_buildChoicesClass\n"
            "  decide\n"
        ),
    },

    # ---- set the flag to the wrong literal False (nagini `weak-flag-false`) ----
    {
        "id": "weak-flag-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Set the "do not invoke" flag to False — a wrong literal.
        "module": _swap(
            _BASE, _I_FLAG_SET,
            "  cls := { cls with doNotCallInTemplates := false }",
        ),
        "refinement": "its faithful real patch sets the attribute to a falsy value. "
                      "The engine reads it as false, so the class is NOT protected "
                      "from invocation; the resolver takes the invoke arm, the "
                      "no-argument call raises, and the lookup fails to the invalid "
                      "fallback. The F2P template does not render the expected "
                      "output. Does NOT resolve.",
        "rationale": "REJECT from C2 (templateWouldCall true result.flag false = "
                     "false): with the flag false the decision evaluates to true "
                     "(the class WOULD be invoked), so C2 fails. Fully concrete, "
                     "decidable. Moves memberValues to a distinct two-member list; "
                     "attacks the fix clause at a point distinct from the omit "
                     "rival.",
        "witness": (
            "example : ¬ problem_spec_buildChoicesClass [(5, \"Club\"), (6, \"Heart\")]\n"
            "    (implementation_buildChoicesClass [(5, \"Club\"), (6, \"Heart\")]) := by\n"
            "  unfold problem_spec_buildChoicesClass implementation_buildChoicesClass\n"
            "  decide\n"
        ),
    },

    # ---- partial-domain: hardcode the pass-through component --------------------
    # Ports nagini `partial-fixed-identity`: correct only at one point of the
    # input domain. There the constant was the identity; here it is the
    # value→label association pinned to a fixed literal.
    {
        "id": "weak-hardcoded-value2label",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the class with the value→label association pinned to a fixed
        # literal, ignoring the supplied members (correct only when the input
        # happens to equal that literal).
        "module": _swap(
            _BASE, _I_VALUE_ASSIGN,
            "  cls := { cls with value2label := [(1, \"Diamond\")] }",
        ),
        "refinement": "a faithful real patch that fixed the value→label association "
                      "to a constant (rather than the members the class actually "
                      "defines) would expose the wrong value→label mapping for "
                      "every enumeration but the one that happens to match the "
                      "constant, so member/label lookups resolve to the wrong data. "
                      "The F2P and P2P tests exercise the mapping the class "
                      "actually defines, so the faithful patch would NOT resolve "
                      "in general.",
        "rationale": "REJECT from C1 (result.value2label = memberValues): the "
                     "constant [(1,\"Diamond\")] disagrees with the input on the "
                     "rest of the domain. Refuted at the empty list (where the "
                     "constant is non-empty), fully concrete and decidable. Moves "
                     "memberValues to [] and attacks the frame/pass-through clause "
                     "— the OTHER independent clause than the flag rivals.",
        "witness": (
            "example : ¬ problem_spec_buildChoicesClass []\n"
            "    (implementation_buildChoicesClass []) := by\n"
            "  unfold problem_spec_buildChoicesClass implementation_buildChoicesClass\n"
            "  decide\n"
        ),
    },

    # ---- supporting near-miss: corrupt the pass-through by prepending -----------
    # Ports nagini `weak-wrong-identity-obj` (the off-by-one near-miss): a rival
    # that returns a component RELATED to the input but not equal to it. Here it
    # prepends a spurious leading entry, so it agrees with the input on the tail
    # but not the head — a distinct discriminator point from the hardcode rival.
    {
        "id": "weak-prepend-value2label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_VALUE_ASSIGN,
            "  cls := { cls with value2label := (0, \"\") :: memberValues }",
        ),
        "refinement": "a faithful real patch that inserted a spurious leading "
                      "value→label entry would report an extra, non-existent member "
                      "mapping for every enumeration; member/label lookups against "
                      "the class would see a mapping the class never defined. The "
                      "tests assert the exact mapping the members produce, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from C1 (result.value2label = memberValues): "
                     "(0,\"\")::memberValues is strictly longer than the input, so "
                     "the equality fails on every input. Refuted at a singleton "
                     "input, distinct from the hardcode rival's empty-list point. "
                     "Fully concrete, decidable. A near-miss (agrees on the tail) "
                     "given its own discriminating point.",
        "witness": (
            "example : ¬ problem_spec_buildChoicesClass [(7, \"X\")]\n"
            "    (implementation_buildChoicesClass [(7, \"X\")]) := by\n"
            "  unfold problem_spec_buildChoicesClass implementation_buildChoicesClass\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: this bundle declares no `opaque`/`axiom` callee (the
# value→label association is plain data and the engine decision is the
# transparent `templateWouldCall`). The nagini AXIOM_TESTS belong to G-AX and are
# dropped, per the porting map.
AXIOM_TESTS = []
