"""properties.py — G-PBT falsification battery for django__django-11815 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a per-character string carrier):

  serializeEnum
      (module className name payload : List Char) : List Char
      result = module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']

  where ``quoted s = ['\\''] ++ s ++ ['\\'']``. Strings are modeled per-character
  as ``List Char`` (mapping.md). The rendered reference text is the qualifying
  module path, a dot, the type name, then the member selected by its
  *identifier* written as a quoted subscript — an opening bracket, the
  single-quoted identifier, a closing bracket. The single top-level clause folds
  several inseparable structural sub-decisions, each pinned to a distinct part of
  the input:

    * WHICH SOURCE keys the selection — the member ``name`` (identifier), NOT the
      stored ``payload``. A rival keyed by ``payload`` diverges wherever the
      payload and the identifier differ (the observable the F2P exercises).
    * WHICH DELIMITERS wrap the selection — a subscript ``[`` ``]``, not a
      positional call ``(`` ``)``.
    * HOW THE IDENTIFIER IS RENDERED — wrapped by ``quoted`` (single quotes on
      each side), not bare.
    * WHICH COMPONENTS AND ORDER — ``module`` ``.`` ``className`` before the
      subscript; dropping or reordering a component violates the clause.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because the modeled inputs are held at
    fractional (read-only) permission, and a rival that overwrites one is
    rejected for insufficient permission. Lean is referentially transparent: the
    four inputs are plain immutable ``List Char`` values, there is no
    half-permission to violate and no aliasing to exploit, so this class has NO
    expressible instance here. No substitute is fabricated for it.

  * NONTERMINATION / TOTAL-CORRECTNESS — VACUOUS. The nagini sibling carries a
    termination obligation and a diverge-before-return rival because Viper proves
    only partial correctness. On this backend the modeled behavior is a TOTAL
    function that must elaborate; a definition that fails to terminate does not
    typecheck, so there is no partial-correctness hole to regress against and no
    expressible rival. Not fabricated.

  * IMPORT-SET TAMPER — NO COUNTERPART. The nagini sibling additionally pins the
    returned import set. This bundle models ONLY the rendered reference text (the
    ``[0]`` element the F2P tests assert on); the import-set component is a set,
    orthogonal to the text fix, and is not modeled (mapping.md scope note). With
    no import binder in the spec there is nothing to attack, so this rival has no
    counterpart here.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term built only from the inputs (concatenation with literal
    punctuation plus the fully-unfolded ``quoted`` helper). The bundle declares
    no ``opaque``/``axiom`` (meta.json axioms == [], deep_model_references == []),
    so there is no answer key an implementation could echo without doing the
    work. The honest analogue is the cheapest-correct POSITIVE CONTROL below.

  * PAYLOAD-KEYED (the pre-patch bug) — APPLIES, and is the load-bearing rival.
    The pre-fix rendered the member by its stored payload as a positional call
    argument. It disagrees with the spec on every input (payload source AND
    delimiters differ), and is refuted at a concrete point.

  * WRONG-DELIMITER / UNQUOTED-NAME / DROPPED-COMPONENT — APPLY. Near-miss rivals
    that key by the correct identifier but mis-render one structural sub-part
    (call delimiters instead of the subscript, a bare identifier instead of the
    quoted one, or an omitted type-name component). Each violates the one clause
    and is refuted with a witness at a distinct input.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a ``decide``-able concrete input; each was checked to HOLD
of its rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology).

BINDER COVERAGE. The spec predicate ``problem_spec_serializeEnum`` binds three
input strings — ``module``, ``className``, ``name`` (``payload`` is an
implementation-only input the modeled behavior deliberately ignores). All three
are varied across the reject witnesses so the battery exercises the spec's
dependence on each rather than probing one point repeatedly:
  * ``module`` — 'm', "xy", 'p', 'q' across the four rivals.
  * ``className`` — 'C', 'E', 'D', 'F'; and the DROPPED-COMPONENT rival actively
    abuses this binder (omits it), so it is attacked, not merely varied.
  * ``name`` — 'A', 'B', 'Z', 'Y'; the UNQUOTED-NAME rival abuses its rendering.
``pts`` = 4 distinct input points.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
rendered text is modeled directly as an order-preserving concatenation over the
inputs, so there is no in-model axiom-soundness / axiom-containment obligation
for the PBT axiom lane to re-discharge (that lane belongs to G-AX in any case).
AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-11815"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_serializeEnum\n"
    "    (module className name payload : List Char) : List Char := Id.run do\n"
    "  -- The member's stored payload is no longer consulted when forming the text;\n"
    "  -- the member is referenced by its identifier as a quoted subscript.\n"
    "  let _ := payload\n"
    "  return module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']\n"
)

_PROOF_BODY = (
    "  intro module className name payload\n"
    "  unfold problem_spec_serializeEnum implementation_serializeEnum\n"
    "  rfl\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival / reshape impl bodies (each is a full impl region; only the impl changes
# unless noted, so the spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# plain functional expression (no `Id.run do` / `return`), same association as
# the spec RHS. Same value on every input; the frozen `rfl` still applies to the
# reduced form, so the obligation is re-proved with a byte-identical statement,
# no new lemma/axiom.
_POS_CONTROL = (
    "def implementation_serializeEnum\n"
    "    (module className name payload : List Char) : List Char :=\n"
    "  -- Reshaped: a direct functional concatenation instead of a `do` block.\n"
    "  let _ := payload\n"
    "  module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']\n"
)
_POS_PROOF = (
    "  intro module className name payload\n"
    "  unfold problem_spec_serializeEnum implementation_serializeEnum\n"
    "  rfl\n"
)

# PAYLOAD-KEYED (= the pre-fix bug): render the member by its stored payload as a
# positional call argument, ignoring the identifier `name`. Disagrees with the
# spec on the keying source AND the delimiters.
_PAYLOAD_KEYED = (
    "def implementation_serializeEnum\n"
    "    (module className name payload : List Char) : List Char := Id.run do\n"
    "  let _ := name\n"
    "  return module ++ ['.'] ++ className ++ ['('] ++ payload ++ [')']\n"
)

# WRONG-DELIMITER: keyed by the correct identifier but wrapped in call
# parentheses instead of the subscript brackets.
_WRONG_DELIM = (
    "def implementation_serializeEnum\n"
    "    (module className name payload : List Char) : List Char := Id.run do\n"
    "  let _ := payload\n"
    "  return module ++ ['.'] ++ className ++ ['('] ++ quoted name ++ [')']\n"
)

# UNQUOTED-NAME: correct subscript brackets but the identifier is emitted bare,
# without the single-quote wrapping `quoted` supplies.
_UNQUOTED = (
    "def implementation_serializeEnum\n"
    "    (module className name payload : List Char) : List Char := Id.run do\n"
    "  let _ := payload\n"
    "  return module ++ ['.'] ++ className ++ ['['] ++ name ++ [']']\n"
)

# DROPPED-COMPONENT: omit the type-name component entirely (abuses `className`).
_DROP_CLASSNAME = (
    "def implementation_serializeEnum\n"
    "    (module className name payload : List Char) : List Char := Id.run do\n"
    "  let _ := payload\n"
    "  let _ := className\n"
    "  return module ++ ['.'] ++ ['['] ++ quoted name ++ [']']\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_serializeEnum`
    # STATEMENT is byte-identical; the tactic body is re-proved for the reshaped
    # form. No helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_CONTROL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the `Id.run do`/`return` block and "
            "spells the rendering as one functional concatenation with the SAME "
            "association as the spec RHS (`module ++ ['.'] ++ className ++ ['['] "
            "++ quoted name ++ [']']`) must satisfy the sole clause `result = "
            "module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']`; if it "
            "cannot, the spec is SPEC-TOO-STRONG. Proof: after `unfold` both sides "
            "reduce to the same concatenation term, so the goal closes by `rfl` — "
            "no new declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the
    # behavior is total, so the ∀ is unguarded), so nagini's precondition-
    # admission probe has no binder to attack; the honest analogue is to discharge
    # the spec predicate at a concrete F2P-shaped input inside the proof region,
    # alongside the frozen obligation. If that ground instance could not be
    # discharged, the modeled behavior would be unsatisfiable at exactly the input
    # the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_serializeEnum ['m'] ['C'] ['A']\n"
            "      (implementation_serializeEnum ['m'] ['C'] ['A'] ['v']) := by\n"
            "    unfold problem_spec_serializeEnum implementation_serializeEnum\n"
            "    decide\n"
            + _PROOF_BODY,
        ),
        "rationale": (
            "the obligation is discharged at a concrete F2P-shaped input "
            "(`module=['m']`, `className=['C']`, `name=['A']`, `payload=['v']`), "
            "where the spec requires the rendered text be the identifier-keyed "
            "subscript `m.C['A']` rather than any payload-based form, by `decide`; "
            "then the frozen obligation is closed verbatim. Verifies (else the "
            "spec is unsatisfiable at the normal input, the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: the theorem STATEMENT is "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body, and no new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would be
    # a true verify-does-not-imply-resolve break rather than an artifact, and (b)
    # a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-payload-keyed-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PAYLOAD_KEYED),
        "refinement": (
            "this IS the pre-fix behavior: render the member by its stored payload "
            "as a positional call argument (`module.className(payload)`) instead of "
            "by its identifier as a quoted subscript (`module.className['name']`). "
            "Its faithful real patch is exactly the pre-patch code the fix removes; "
            "the F2P tests assert the identifier-keyed subscript form verbatim and "
            "compare the rendered string exactly, so the payload-keyed call form "
            "fails them. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the sole clause `result = module ++ ['.'] ++ className ++ "
            "['['] ++ quoted name ++ [']']`: the rival emits `module ++ ['.'] ++ "
            "className ++ ['('] ++ payload ++ [')']`, which differs from the spec at "
            "the delimiter position AND uses `payload` where the spec uses `quoted "
            "name`. Refuted at `module=['m']`, `className=['C']`, `name=['A']`, "
            "`payload=['v']` (identifier and payload distinct)."
        ),
        "witness": (
            "-- Refuted where the stored payload ('v') differs from the identifier\n"
            "-- ('A'): the text must key on the identifier as a quoted subscript,\n"
            "-- not on the payload as a call argument.\n"
            "example : ¬ problem_spec_serializeEnum ['m'] ['C'] ['A']\n"
            "    (implementation_serializeEnum ['m'] ['C'] ['A'] ['v']) := by\n"
            "  unfold problem_spec_serializeEnum implementation_serializeEnum\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-wrong-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_DELIM),
        "refinement": (
            "keyed by the correct identifier but wrapped in call parentheses "
            "instead of the subscript brackets, rendering `module.className('name')` "
            "rather than `module.className['name']`. A faithful real patch emitting "
            "the parenthesised call form produces a value the F2P tests do NOT "
            "assert (they pin the subscript form) and the string comparison is "
            "exact, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the sole clause at the delimiter positions: the rival "
            "emits `['(']`/`[')']` where the spec requires `['[']`/`[']']`, so "
            "`result != module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ "
            "[']']` for every input. Refuted at `module=['x','y']`, "
            "`className=['E']`, `name=['B']`, varying `module` off the single-"
            "character value the other rivals use."
        ),
        "witness": (
            "-- Refuted anywhere: the subscript delimiters '[' ']' are required, so\n"
            "-- the call form '(' ')' disagrees regardless of the identifier.\n"
            "example : ¬ problem_spec_serializeEnum ['x','y'] ['E'] ['B']\n"
            "    (implementation_serializeEnum ['x','y'] ['E'] ['B'] ['w']) := by\n"
            "  unfold problem_spec_serializeEnum implementation_serializeEnum\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-unquoted-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNQUOTED),
        "refinement": (
            "correct subscript brackets but the identifier is emitted BARE, without "
            "the single-quote wrapping. A faithful real patch dropping the quoting "
            "renders `module.className[name]` (an unquoted subscript) rather than "
            "`module.className['name']`; the F2P tests assert the quoted form "
            "verbatim, so the unquoted form does NOT resolve."
        ),
        "rationale": (
            "REJECT from the sole clause at the identifier-rendering position: the "
            "rival emits `name` where the spec requires `quoted name` (= `['\\''] "
            "++ name ++ ['\\'']`), so it is missing the two quote characters. "
            "Refuted at `module=['p']`, `className=['D']`, `name=['Z']`, exercising "
            "`name` at a value distinct from the other rivals'."
        ),
        "witness": (
            "-- Refuted anywhere the identifier is non-empty: the spec wraps it in\n"
            "-- single quotes, so a bare identifier is two characters short.\n"
            "example : ¬ problem_spec_serializeEnum ['p'] ['D'] ['Z']\n"
            "    (implementation_serializeEnum ['p'] ['D'] ['Z'] ['q']) := by\n"
            "  unfold problem_spec_serializeEnum implementation_serializeEnum\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-dropped-component",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_CLASSNAME),
        "refinement": (
            "omits the type-name component entirely, rendering `module.['name']` "
            "instead of `module.className['name']`. A faithful real patch dropping "
            "the class name produces text missing the type, which the F2P tests — "
            "asserting the fully-qualified `module.ClassName['NAME']` string — "
            "reject. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the sole clause: the rival emits `module ++ ['.'] ++ ['['] "
            "++ quoted name ++ [']']`, dropping the `className` component the spec "
            "requires between the dot and the opening bracket. This rival actively "
            "abuses the `className` binder — refuted at `module=['q']`, "
            "`className=['F']`, `name=['Y']` (a non-empty className is elided)."
        ),
        "witness": (
            "-- Refuted whenever className is non-empty: dropping it removes\n"
            "-- required characters between the dot and the opening bracket.\n"
            "example : ¬ problem_spec_serializeEnum ['q'] ['F'] ['Y']\n"
            "    (implementation_serializeEnum ['q'] ['F'] ['Y'] ['r']) := by\n"
            "  unfold problem_spec_serializeEnum implementation_serializeEnum\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the rendered text is modeled
# directly as a concatenation over the inputs, so there is no in-model axiom
# obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
