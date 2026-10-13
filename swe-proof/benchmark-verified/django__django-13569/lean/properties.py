"""properties.py — G-PBT falsification battery for django__django-13569 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models TWO functions with fractional-permission contracts (a leaf that reports
the grouping columns a single non-deterministic ordering term offers, and a
front-fold that gathers, in order, every term's contribution while skipping
reference terms). This Lean bundle models only the SINGLE purely-functional
leaf: a total function over the observable inputs (the non-deterministic
ordering expression and an optional output alias) returning the list of grouping
columns it contributes. The load-bearing obligation is that this list is empty
for every input. The nagini cases attached to the gathering fold (its own
positive control, its admissibility probe, its include-the-term and drop-last
partial-domain rivals, and its frame-mutation rival) have NO counterpart on this
carrier — that behavior is not modeled here — so they are principled omissions;
their adversarial ARGUMENT (a non-deterministic term must contribute nothing, so
its column must never enter the grouping) is carried over onto the single
modeled leaf. The per-case mapping is in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior). Asked which grouping columns it
contributes, a non-deterministic ordering expression must answer with the empty
collection, for any expression and any output alias. The postcondition pins the
result to a single grounded value — the empty list — so it has ONE independent
top-level clause: ``result = []``. The result does not branch on either input
(neither the expression nor the alias), which is itself load-bearing: the fix
must return empty on every backend (the random function's SQL name differs per
backend) and whether or not the compiler supplies an output alias.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival (write
    into a read-only input carrier) has no expressible instance here; no
    substitute is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: the result
    is pinned to the empty list, a value built from nothing an implementation
    could not also just write down. There is no opaque answer key to echo. In
    its place the battery carries honest cheapest-implementation POSITIVE
    CONTROLS that must verify.

  * VALUE / PARTIAL-DOMAIN — APPLIES. Rivals that emit a non-empty contribution:
    the pre-patch inherited default (contribute the term ITSELF); a leak keyed on
    the alias binder (contribute the aliased column whenever an alias is present);
    and a single-backend partial fix (return empty only for one DB's random
    function name, leaking on every other backend). Each targets the sole clause
    ``result = []`` from a different binder.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. Each was checked to HOLD of its rival and to FAIL
on the frozen solution, so it discriminates rather than asserting a tautology.
The carrier is fully transparent (the result is a concrete list of concrete
strings), so every witness closes by ``decide`` — no conditioning on an opaque
term is needed.

BINDER / POINT SPREAD. The reject witnesses move both input binders of the spec
rather than fixing them at one convenient point: the expression's SQL function
name ranges over ``"RAND"``, ``"RANDOM"`` and ``"DBMS_RANDOM.VALUE"`` (the three
backend random-function names), and the output alias takes both ``none`` and
``some``. No two witnesses share a point; the three reject witnesses probe three
distinct inputs.

AXIOM lane: EMPTY here. The modeled leaf calls nothing and consumes no ``axiom``;
the axiom lane belongs to G-AX. The nagini ``AXIOM_TESTS`` (also empty there) are
dropped.
"""
from pathlib import Path

INSTANCE = "django__django-13569"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the cases that
# legitimately re-prove, the proof region) so same_spec stays byte-identical.

# The whole gold impl body (impl region).
_IMPL = (
    "def randomGroupingColumns\n"
    "    (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=\n"
    "  Id.run do\n"
    "    return []"
)

# The frozen proof body (proof region).
_PROOF = (
    "  intro self outAlias\n"
    "  rfl"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Keeps
    # the theorem STATEMENT byte-identical; the proof is honestly re-closed for
    # the new (branching) shape — no helper lemma, no axiom, no `sorry`.
    #
    # Ports the nagini leaf positive control (which branched on the input and
    # built the empty result in both arms): here the analogue branches on the
    # optional output alias and returns the empty collection in both arms.
    # =====================================================================
    {
        "id": "pos-branch-on-alias",
        "kind": "soundness",
        "expect": "verify",
        # Branch on the optional output alias; return the empty collection in
        # both arms. Same value on every input, so `result = []` still holds.
        # The branch makes the frozen `rfl` no longer reduce, so the proof is
        # re-closed by case-splitting the alias (each arm is `rfl`).
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "def randomGroupingColumns\n"
                "    (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=\n"
                "  Id.run do\n"
                "    match outAlias with\n"
                "    | none => return []\n"
                "    | some _ => return []",
            ),
            _PROOF,
            "  intro self outAlias\n"
            "  cases outAlias <;> rfl",
        ),
        "rationale": "structurally-different CORRECT impl: branch on the optional "
                     "output alias and return the empty collection in both arms. "
                     "The contributed list is empty on every input, so the clause "
                     "`result = []` holds. Must verify, else SPEC-TOO-STRONG. "
                     "Proof honestly re-closed (`cases outAlias <;> rfl`); the "
                     "theorem statement is byte-identical. Ports the nagini leaf "
                     "positive control (branch on input, build empty both ways).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis
    # (the modeled behavior is total, so `∀` is unguarded), so the nagini
    # precondition-admission probe has no binder to attack here; the honest
    # analogue discharges the spec predicate by evaluation at a ground F2P-shaped
    # input (a genuine non-deterministic ordering term, no alias) alongside the
    # frozen obligation. Ports the nagini leaf admissibility probe.
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P-shaped input (a random-value
        # ordering term, no alias) by `rfl` in a `have`, then close the frozen
        # obligation verbatim. Nothing is assumed: no new declaration, statement
        # byte-identical, the ground instance is a `have` inside the tactic body.
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : problem_spec_randomGroupingColumns "
            "{ function := \"RANDOM\" } none\n"
            "      (randomGroupingColumns { function := \"RANDOM\" } none) := rfl\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at a ground F2P-shaped input "
                     "(a genuine non-deterministic ordering term, no output "
                     "alias) by `rfl`, then the frozen obligation is closed "
                     "verbatim. Verifies (else the modeled behavior is "
                     "unsatisfiable at exactly the input the F2P exercises — the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, and "
                     "the ground instance is a `have` inside the existing tactic "
                     "body. Ports the nagini admissibility probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input, checked to hold of the rival and fail on the frozen
    # solution.
    # =====================================================================

    # ---- the bug itself: the term contributes ITSELF (nagini leaf prepatch) ----
    {
        "id": "weak-contribute-self",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch behavior: a non-deterministic term contributes ITSELF (the
        # inherited default), i.e. the single grouping column named by its own
        # SQL function fragment. Length 1, not 0.
        "module": _swap(
            _BASE, _IMPL,
            "def randomGroupingColumns\n"
            "    (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=\n"
            "  Id.run do\n"
            "    return [self.function]",
        ),
        "refinement": "this IS the pre-patch behavior: with no override the "
                      "non-deterministic term inherits the default that "
                      "contributes the term itself as a single grouping column. "
                      "The faithful real patch (no override) lets that column "
                      "enter the grouping of a randomly-ordered aggregate, so the "
                      "rows are not grouped and the FAIL_TO_PASS scenario (an "
                      "aggregate ordered by a random term) FAILS -> would NOT "
                      "resolve.",
        "rationale": "REJECT from the sole clause `result = []`: a length-1 "
                     "contribution violates it. Binder spread: the expression's "
                     "function name is `\"RAND\"` (a backend random name distinct "
                     "from the other rivals' points), no output alias. If it "
                     "verified, SPEC-TOO-WEAK.",
        "witness": (
            "example : ¬ problem_spec_randomGroupingColumns { function := \"RAND\" } none\n"
            "    (randomGroupingColumns { function := \"RAND\" } none) := by\n"
            "  unfold problem_spec_randomGroupingColumns randomGroupingColumns\n"
            "  decide\n"
        ),
    },

    # ---- leak keyed on the alias binder ----
    {
        "id": "weak-alias-leak",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the empty collection when no alias is present, but leak the
        # aliased column whenever the compiler supplies an output alias.
        "module": _swap(
            _BASE, _IMPL,
            "def randomGroupingColumns\n"
            "    (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=\n"
            "  Id.run do\n"
            "    match outAlias with\n"
            "    | none => return []\n"
            "    | some a => return [a]",
        ),
        "refinement": "a faithful real patch that returned empty only when no "
                      "output alias is supplied, but contributed the aliased "
                      "column whenever the compiler passes an alias, would still "
                      "leak a grouping column for a randomly-ordered aggregate in "
                      "exactly the aliased case the compiler produces -> the rows "
                      "are not grouped and the FAIL_TO_PASS scenario FAILS -> "
                      "would NOT resolve. The no-alias case still passes, so it is "
                      "a partial-domain miss keyed on the alias binder.",
        "rationale": "REJECT from `result = []`: with an output alias present the "
                     "spec still pins the contribution to empty while the rival "
                     "returns a length-1 list. Moves the alias binder to `some` "
                     "(the only rival that does), function name `\"RANDOM\"`. If "
                     "it verified, SPEC-TOO-WEAK.",
        "witness": (
            "example : ¬ problem_spec_randomGroupingColumns { function := \"RANDOM\" } (some \"x\")\n"
            "    (randomGroupingColumns { function := \"RANDOM\" } (some \"x\")) := by\n"
            "  unfold problem_spec_randomGroupingColumns randomGroupingColumns\n"
            "  decide\n"
        ),
    },

    # ---- single-backend partial fix (near-miss on the function-name binder) ----
    {
        "id": "weak-single-backend",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the empty collection only for the default backend's random
        # function name; on every other backend fall back to the pre-patch
        # inherited default (contribute the term itself).
        "module": _swap(
            _BASE, _IMPL,
            "def randomGroupingColumns\n"
            "    (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=\n"
            "  Id.run do\n"
            "    if self.function == \"RANDOM\" then\n"
            "      return []\n"
            "    else\n"
            "      return [self.function]",
        ),
        "refinement": "a faithful real patch that returned empty only for one "
                      "database's random-function name (guarding on the SQL name "
                      "instead of returning empty unconditionally) would resolve "
                      "the scenario only on that backend; on every other backend, "
                      "whose random term compiles to a different function name, "
                      "the term still contributes its own column, the rows are not "
                      "grouped, and that backend's aggregation tests FAIL -> would "
                      "NOT resolve. Since the contribution must be empty on EVERY "
                      "backend, this is a partial-domain miss on the "
                      "function-name binder.",
        "rationale": "REJECT from `result = []`: for a non-default random-function "
                     "name the rival contributes a length-1 list while the spec "
                     "pins empty. Refuted at function name "
                     "`\"DBMS_RANDOM.VALUE\"` — a THIRD distinct function-name "
                     "point, no alias — so the function-name binder is "
                     "demonstrated at three values across the reject witnesses. If "
                     "it verified, SPEC-TOO-WEAK.",
        "witness": (
            "example : ¬ problem_spec_randomGroupingColumns { function := \"DBMS_RANDOM.VALUE\" } none\n"
            "    (randomGroupingColumns { function := \"DBMS_RANDOM.VALUE\" } none) := by\n"
            "  unfold problem_spec_randomGroupingColumns randomGroupingColumns\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the modeled leaf calls nothing and consumes no `axiom`.
# The axiom lane belongs to G-AX; the nagini AXIOM_TESTS were also empty and are
# dropped.
AXIOM_TESTS = []
