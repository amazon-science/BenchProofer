"""properties.py — G-PBT falsification battery for django__django-13346 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_inClauseSql`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one behavior, a pure per-character string build):

  inClauseSql  (vendor : Vendor) (n : Nat) : List Char
               result = buildClause (slotFor vendor) n

  The rendered membership clause over ``n ≥ 1`` value slots is the
  parenthesised, comma-separated list of ``n`` copies of the per-backend value
  slot: the bare bound-value placeholder on a backend WITH a native JSON column
  type, otherwise that backend's value-extraction wrapper. The single
  postcondition pins the slot count to ``n`` and every slot to ``vendor``;
  nothing in the clause is left unconstrained.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the two inputs (``vendor``, ``n``) are passed by value, there is no read-only
    heap half-permission to overwrite and no aliasing to exploit. The nagini
    sibling already recorded this class as N/A (its sole input was a by-value
    ``int``); it has no expressible instance here and no substitute is
    fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is an equality against
    a term (``buildClause (slotFor vendor) n``) built ONLY from the inputs and
    fixed character constants — a fully-unfolded computation, not an opaque
    answer key. The bundle declares no ``opaque``/``axiom`` (its per-backend
    wrapper is modeled deeply, not axiomatized), so there is nothing an
    implementation could echo without doing the work. In its place the battery
    carries honest positive controls (``pos-*``) that must verify.

  * CONTROL-FLOW-EFFECT — VACUOUS. The behavior returns a value with no
    raise/no-raise decision and no side-effect invisible to the value
    abstraction (the whole output list IS the abstraction).

  * PARTIAL-DOMAIN / VALUE — the real attacks. The postcondition rejects any
    rival that renders even one slot wrongly on any point of the
    (vendor, n) domain: the pre-fix all-bare rendering, a partial fix that is
    right on one slot-count sub-domain but wrong on the other, a fix that uses
    the wrong backend's wrapper, and a fix that ignores the native-column-type
    flag and wraps a native-JSON backend that must be left bare.

CASE-COUNT vs NAGINI. The nagini sibling modeled a single SQLite-only string
builder over one by-value count input; this bundle's carrier ADDS the backend
dimension (``vendor``) that the fix actually turns on. So the four nagini
uniqueness rivals port directly (all-bare baseline, the single-value-bare and
multi-value-bare partial-domain splits, and the wrong-backend-wrapper
near-miss), and ONE rival with no nagini counterpart is added to exercise the
new binder: a fix that ignores whether the backend has a native JSON column
type and wraps every backend, wrong precisely on the native-JSON backend the
nagini carrier never modeled. The two nagini positives (a structural reshape and
the in-domain admissibility control) port; a second reshape positive is added.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate at one concrete,
``decide``-able input; each was checked to ELABORATE against its rival (the
rival provably contradicts the spec there) and to FAIL against the frozen
solution (so it discriminates rather than asserting a tautology). The witnesses
are spread across the domain: ``vendor`` is moved over all four backends
(mariadb, sqlite, mysql, postgresql) and ``n`` over {1, 2, 3}, so no binder is
pinned to one value across the battery and no two rivals share a probe point
unless they truly fail there for the same reason.

AXIOM lane: EMPTY. meta.json axioms == [] and the single deep_model_reference
(the per-backend value-extraction wrapper) is validated == the real callee by
G-AX, not trusted by the proof; there is no axiom-soundness obligation to probe
here (that lane belongs to G-AX in any case).
"""
from pathlib import Path

INSTANCE = "django__django-13346"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body (the `implementation_inClauseSql` def) and the FULL
# proof-region tactic body. Every replacement lands entirely inside the region
# it means to edit, so `same_spec` holds and the theorem STATEMENT is untouched.
_IMPL = (
    "def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do\n"
    "  -- start from the base membership placeholder: one bare value slot per element\n"
    "  let mut rhs := buildClause \"%s\".toList n\n"
    "  if !hasNativeJson vendor then\n"
    "    -- backend has no native JSON column type: wrap each value slot in its\n"
    "    -- value-extraction function\n"
    "    rhs := buildClause (valueExtractor vendor) n\n"
    "  return rhs"
)
_PROOF = (
    "  intro vendor n _\n"
    "  unfold problem_spec_inClauseSql implementation_inClauseSql slotFor\n"
    "  cases vendor <;> rfl"
)

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different
    # but CORRECT implementations that MUST verify. If a faithful correct
    # implementation cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Each keeps the theorem STATEMENT byte-identical; none
    # introduces a helper lemma, an axiom, or an assumption token.
    # =====================================================================
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: the two branches are reordered — the native-JSON
        # case is handled first with an early return and the wrapper case falls
        # through — instead of the base-then-conditionally-rewrap shape. Same
        # value on every input; the frozen tactic body still closes.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do\n"
            "  if hasNativeJson vendor then\n"
            "    return buildClause \"%s\".toList n\n"
            "  return buildClause (valueExtractor vendor) n",
        ),
        "rationale": "a correct reshape (branches reordered, native-JSON case "
                     "returned early, wrapper case fallen through) computes "
                     "`buildClause (slotFor vendor) n` on every input, so it must "
                     "satisfy the sole postcondition clause `result = buildClause "
                     "(slotFor vendor) n`; if it cannot, the inClauseSql "
                     "postcondition is SPEC-TOO-STRONG. Proof: frozen tactic body "
                     "retained (`cases vendor <;> rfl` still closes each branch).",
    },
    {
        "id": "pos-slot-let",
        "kind": "soundness",
        "expect": "verify",
        # Functional reshape: choose the per-slot text into a local up front and
        # build the clause once, instead of building bare then conditionally
        # rebuilding. Same value; the frozen tactic body still closes.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char :=\n"
            "  let slot := if hasNativeJson vendor then \"%s\".toList else valueExtractor vendor\n"
            "  buildClause slot n",
        ),
        "rationale": "selecting the per-slot text into a local and building the "
                     "clause once equals `buildClause (slotFor vendor) n` "
                     "pointwise (the local mirrors `slotFor`), so a correct "
                     "reshape must verify (else SPEC-TOO-STRONG). Proof: frozen "
                     "tactic body retained (`cases vendor <;> rfl`).",
    },
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen theorem's only precondition is 1 ≤ n; there is no other
        # binder to admit, so the honest analogue of the nagini
        # precondition-admission probe is to discharge the spec at a ground,
        # F2P-shaped input (a non-native-JSON backend at the single-value count
        # the issue is about) by evaluation, alongside the frozen obligation.
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : problem_spec_inClauseSql Vendor.sqlite 1\n"
            "      (implementation_inClauseSql Vendor.sqlite 1) := by\n"
            "    unfold problem_spec_inClauseSql implementation_inClauseSql slotFor\n"
            "    decide\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at a ground F2P-shaped input "
                     "(a non-native-JSON backend, single value — the exact case "
                     "the issue reports) by `decide`, then the frozen obligation "
                     "is closed verbatim. Verifies (else the spec is unsatisfiable "
                     "at the normal input, the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, the theorem "
                     "statement is byte-identical, the ground instance is a `have` "
                     "inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete input.
    # =====================================================================
    {
        "id": "weak-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix baseline: every slot is left as the bare bound-value
        # placeholder on every backend; the value-extraction wrapping is never
        # applied. (== Solution_prepatch.lean's impl.)
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do\n"
            "  let rhs := buildClause \"%s\".toList n\n"
            "  return rhs",
        ),
        "refinement": "leaving every slot bare on a backend without a native JSON "
                      "column type is exactly the pre-fix behavior: the "
                      "membership lookup compares the bound value against the raw "
                      "stored text instead of the extracted scalar, so the F2P "
                      "key-membership test selects the wrong/empty set. It would "
                      "NOT resolve — this is the leg's prepatch.",
        "rationale": "REJECT from `result = buildClause (slotFor vendor) n`: on a "
                     "non-native-JSON backend every slot must be the wrapper, but "
                     "the rival emits the bare placeholder. Refuted at "
                     "(mariadb, 3), moving `vendor` to the third backend and `n` "
                     "to 3 so this rival's probe point is its own.",
        "witness": (
            "example : ¬ problem_spec_inClauseSql Vendor.mariadb 3\n"
            "    (implementation_inClauseSql Vendor.mariadb 3) := by\n"
            "  unfold problem_spec_inClauseSql implementation_inClauseSql\n"
            "  decide\n"
        ),
    },
    {
        "id": "partial-single-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct wrapping on the multi-value sub-domain, but leaves the clause
        # bare when there is exactly one value (n == 1) — the single-value
        # sub-domain the issue is specifically about.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do\n"
            "  let mut rhs := buildClause \"%s\".toList n\n"
            "  if !hasNativeJson vendor then\n"
            "    if n == 1 then\n"
            "      rhs := buildClause \"%s\".toList n\n"
            "    else\n"
            "      rhs := buildClause (valueExtractor vendor) n\n"
            "  return rhs",
        ),
        "refinement": "wrapping only when there is more than one value emits the "
                      "bare placeholder for a single-value membership — the EXACT "
                      "case the issue reports (a one-element list must match the "
                      "scalar key lookup). The single-value legs of the F2P test "
                      "would still select the wrong/empty set, so it would NOT "
                      "resolve.",
        "rationale": "Partial-domain (single-value sub-domain). REJECT from "
                     "`result = buildClause (slotFor vendor) n`: at n = 1 on a "
                     "non-native-JSON backend the slot must be the wrapper, but "
                     "the rival emits the bare placeholder. Refuted at "
                     "(mysql, 1), moving `vendor` to a distinct backend and "
                     "pinning the boundary n = 1.",
        "witness": (
            "example : ¬ problem_spec_inClauseSql Vendor.mysql 1\n"
            "    (implementation_inClauseSql Vendor.mysql 1) := by\n"
            "  unfold problem_spec_inClauseSql implementation_inClauseSql\n"
            "  decide\n"
        ),
    },
    {
        "id": "partial-multi-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # Complementary split: correct on the single-value sub-domain (n == 1
        # wraps) but leaves the clause bare for two or more values.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do\n"
            "  let mut rhs := buildClause \"%s\".toList n\n"
            "  if !hasNativeJson vendor then\n"
            "    if n == 1 then\n"
            "      rhs := buildClause (valueExtractor vendor) n\n"
            "    else\n"
            "      rhs := buildClause \"%s\".toList n\n"
            "  return rhs",
        ),
        "refinement": "wrapping only the single-value case emits bare "
                      "placeholders for a membership over two or more values, so "
                      "the multi-value legs of the F2P test compare bound values "
                      "against the raw stored text and select the wrong set. It "
                      "would NOT resolve. This is the complement of "
                      "partial-single-bare and diverges on the OTHER sub-domain, "
                      "so its probe point is genuinely distinct.",
        "rationale": "Partial-domain (multi-value sub-domain). REJECT from "
                     "`result = buildClause (slotFor vendor) n`: at n ≥ 2 on a "
                     "non-native-JSON backend the slots must be the wrapper, but "
                     "the rival emits bare placeholders. Refuted at (sqlite, 2), "
                     "the smallest multi-value count, distinct from every other "
                     "rival's point.",
        "witness": (
            "example : ¬ problem_spec_inClauseSql Vendor.sqlite 2\n"
            "    (implementation_inClauseSql Vendor.sqlite 2) := by\n"
            "  unfold problem_spec_inClauseSql implementation_inClauseSql\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-wrong-wrapper",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: wraps every non-native-JSON backend, but with a fixed wrapper
        # belonging to a DIFFERENT backend family (the one that additionally
        # un-quotes) rather than the wrapper the target backend requires.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do\n"
            "  let mut rhs := buildClause \"%s\".toList n\n"
            "  if !hasNativeJson vendor then\n"
            "    rhs := buildClause (valueExtractor Vendor.mariadb) n\n"
            "  return rhs",
        ),
        "refinement": "using one backend family's value-extraction wrapper for a "
                      "different backend renders SQL the target backend does not "
                      "accept for the comparison; the F2P test runs on the "
                      "eval backend whose wrapper this is NOT, so the rendered "
                      "clause is wrong there and it would NOT resolve. This is a "
                      "near-miss: it applies A wrapper (right branch, right slot "
                      "count) but the WRONG one, and diverges only on backends "
                      "whose required wrapper differs.",
        "rationale": "REJECT from `result = buildClause (slotFor vendor) n`: on a "
                     "backend whose required wrapper differs from the one used, "
                     "each slot is the wrong constant. Refuted at (sqlite, 1) — "
                     "sqlite's wrapper is not the un-quoting one — pinning the "
                     "single-value boundary on the eval backend, a point no "
                     "other rival probes.",
        "witness": (
            "example : ¬ problem_spec_inClauseSql Vendor.sqlite 1\n"
            "    (implementation_inClauseSql Vendor.sqlite 1) := by\n"
            "  unfold problem_spec_inClauseSql implementation_inClauseSql\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-ignores-native",
        "kind": "uniqueness",
        "expect": "reject",
        # No nagini counterpart: the nagini carrier had no backend dimension.
        # This rival ignores whether the backend has a native JSON column type
        # and applies the extraction wrapper to EVERY backend — wrong precisely
        # on a native-JSON backend, which must be left bare.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do\n"
            "  let rhs := buildClause (valueExtractor Vendor.sqlite) n\n"
            "  return rhs",
        ),
        "refinement": "wrapping a backend that has a native JSON column type "
                      "double-wraps a value that is already a comparable JSON "
                      "scalar, rendering a clause that no longer matches the "
                      "native path's stored representation; the native-JSON "
                      "backend's membership lookups would break, so it would NOT "
                      "resolve. This attacks the native-column-type binder the "
                      "nagini sibling never modeled.",
        "rationale": "REJECT from `result = buildClause (slotFor vendor) n`: on a "
                     "native-JSON backend `slotFor` is the bare placeholder, but "
                     "the rival applies the wrapper. Refuted at (postgresql, 1), "
                     "the ONLY witness that moves `vendor` onto the native-JSON "
                     "backend — the binder value no other rival exercises.",
        "witness": (
            "example : ¬ problem_spec_inClauseSql Vendor.postgresql 1\n"
            "    (implementation_inClauseSql Vendor.postgresql 1) := by\n"
            "  unfold problem_spec_inClauseSql implementation_inClauseSql\n"
            "  decide\n"
        ),
    },
]
