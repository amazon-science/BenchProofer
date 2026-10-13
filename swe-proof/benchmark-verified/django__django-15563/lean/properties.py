"""properties.py — G-PBT falsification battery for django__django-15563 (lean).

NOT a Lean file; a record of the adversarial cases the G-PBT gate executes and
stamps RESULT. Each SPEC case is a full ``Solution.lean`` variant that shares
the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region — and, for a case that legitimately
re-proves, inside the ``-- proof-start`` / ``-- proof-end`` region — is changed,
so ``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over abstracted query inputs):

  relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
                   (rows : List (List Int)) : List (Nat × List Int)

  Each ancestor of a multi-parent inheritance tree must be targeted by the
  identifiers read from the ONE table column dedicated to it. The abstracted
  inputs are: the ancestors in encounter order (``ancestors``), a per-ancestor
  flag for whether the ancestor shares the model's primary key
  (``sharesPrimaryKey``), and the materialized table of identifier rows
  (``rows``). The result pairs each ancestor, in its original order, with the
  identifiers gathered from its column.

  Column assignment (``columnAssignment ... 1``), the grounded oracle the
  postcondition pins the result to:
    - an ancestor that shares the primary key reuses column ``0``;
    - an ancestor that does not is given the next dedicated column, numbered
      consecutively from ``1`` across the non-sharing ancestors.

  Load-bearing postcondition clauses (all in ``problem_spec_relatedTargetIds``):
    (P-order)  the result preserves ancestor order and pairs each ancestor with
               its own identifiers.
    (P-reuse)  a sharing ancestor reads column ``0`` (biconditional direction 1).
    (P-dense)  a NON-sharing ancestor reads its dedicated column, numbered
               CONSECUTIVELY from ``1`` — the k-th non-sharing ancestor reads
               column k, not a sparser or colliding column (biconditional
               direction 2 + the dense-index pin). A sparse or colliding
               assignment would over-run / mis-read the identifier row.

  The oracle ``columnAssignment`` is GROUNDED in the inputs — a front-recursive
  fold fully computable from ``ancestors``/``sharesPrimaryKey``, not an opaque
  answer key — so there is no wrong echo a rival can return; a rival must instead
  agree with the oracle on part of the domain while diverging on a discriminating
  sub-domain (a non-sharing ancestor placed in column 0; sparse columns 1,3,5,…;
  a colliding constant column; a sharing ancestor denied column-0 reuse).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the inputs carry no heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. The nagini frame-mutation rival (a
    store into the read-only ``chain`` input, rejected for insufficient
    permission) has NO expressible instance here; no substitute is fabricated.
    See 'assessment'.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded (above); the
    bundle declares no ``opaque``/``axiom``, so there is nothing to echo without
    doing the assignment. In its place the battery carries an honest structurally
    different POSITIVE CONTROL (``pos-direct``).

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the ancestor
    domain but diverging on a discriminating sub-domain, mapped one-to-one from
    the nagini uniqueness rivals: everyone reuses column 0 (``weak-all-column-0``
    == the pre-patch behaviour), sparse dedicated columns (``weak-sparse``),
    colliding constant column (``weak-const-column``), plus a same-spec-carrier
    dual, a sharing ancestor denied column-0 reuse (``weak-no-reuse``).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen loop
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating ``¬ (spec …
(impl …))`` at ``decide``-able literal inputs; each was checked to ELABORATE
against its rival (the rival provably violates the spec there) and to FAIL
against the frozen solution (so it discriminates rather than asserting a
tautology).

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` (the deep-model
identity-soundness probe) belong to G-AX, which the G-PBT spec lane ignores;
meta.json records the deep model separately.
"""
from pathlib import Path

INSTANCE = "django__django-15563"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (each present exactly once inside Solution.lean; the whole
# assignment loop is anchored so every reshape lands entirely inside the impl
# region and same_spec is preserved by construction).
# ---------------------------------------------------------------------------
_ASSIGN_LOOP = (
    "  let mut nextCol := 1\n"
    "  let mut assignment : List (Nat × Nat) := []\n"
    "  for ancestor in ancestors do\n"
    "    if sharesPrimaryKey ancestor then\n"
    "      assignment := assignment ++ [(ancestor, 0)]\n"
    "    else\n"
    "      assignment := assignment ++ [(ancestor, nextCol)]\n"
    "      nextCol := nextCol + 1\n"
)
_WIDTH_BUMP = "      nextCol := nextCol + 1\n"

# The full impl region body (for the closed-form positive control).
_IMPL_FULL = (
    "def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)\n"
    "    (rows : List (List Int)) : List (Nat × List Int) := Id.run do\n"
    "  -- Build, in one pass, the column each ancestor reads from: a shared ancestor\n"
    "  -- reuses column 0; each non-sharing ancestor claims the next dedicated column.\n"
    "  let mut nextCol := 1\n"
    "  let mut assignment : List (Nat × Nat) := []\n"
    "  for ancestor in ancestors do\n"
    "    if sharesPrimaryKey ancestor then\n"
    "      assignment := assignment ++ [(ancestor, 0)]\n"
    "    else\n"
    "      assignment := assignment ++ [(ancestor, nextCol)]\n"
    "      nextCol := nextCol + 1\n"
    "  -- Pair each ancestor with the identifiers gathered from its dedicated column.\n"
    "  let mut result : List (Nat × List Int) := []\n"
    "  for ac in assignment do\n"
    "    result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]\n"
    "  return result\n"
)
assert _BASE.count(_IMPL_FULL) == 1, "impl-full anchor drifted"

# The full proof region body, sliced between the markers (used to replace the
# frozen loop-bridge lemmas + obligation with a direct rfl proof for the
# closed-form positive, since those lemmas are tuned to the imperative loops).
_PS = "-- proof-start\n"
_PE = "-- proof-end\n"
_PROOF_BODY = _BASE[_BASE.index(_PS) + len(_PS): _BASE.index(_PE)]
assert "correct_relatedTargetIds" in _PROOF_BODY

# The frozen obligation's first two tactic lines — the injection point for the
# admissibility ground instance (prepended before the frozen body).
_PROOF_INTRO = (
    "  intro ancestors sharesPrimaryKey rows _ _\n"
    "  unfold problem_spec_relatedTargetIds\n"
)

for _a in (_ASSIGN_LOOP, _WIDTH_BUMP, _PROOF_INTRO):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROL / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (pos-direct) SOUNDNESS — a structurally different but CORRECT implementation:
# instead of two imperative accumulation loops, compose the grounded column
# assignment with the per-column read DIRECTLY (`columnAssignment … 1 |>.map …`).
# Same result on every input, so the postcondition must still hold; if it cannot,
# the postcondition is over-fit to the literal two-loop FORM => SPEC-TOO-STRONG.
# The frozen loop-bridge lemmas (loops_to_folds / assignFold / resultFold / …)
# are tuned to the imperative loops and would not elaborate against the
# closed form, so the whole proof region is replaced by the direct proof: after
# unfolding both defs the two sides are syntactically identical, so `rfl` closes.
# The `theorem correct_relatedTargetIds` STATEMENT is kept byte-identical; no new
# axiom / assumption token / theorem is introduced (the replacement only DROPS
# frozen helper lemmas, which the scope rules permit).
_DIRECT_IMPL = (
    "def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)\n"
    "    (rows : List (List Int)) : List (Nat × List Int) :=\n"
    "  -- Column assignment and the per-column read composed directly (no explicit\n"
    "  -- accumulation loops): assign each ancestor its column, then read that column\n"
    "  -- from every identifier row.\n"
    "  (columnAssignment sharesPrimaryKey ancestors 1).map\n"
    "    (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0)))\n"
)
_DIRECT_PROOF = (
    "theorem correct_relatedTargetIds : ∀ (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)\n"
    "    (rows : List (List Int)),\n"
    "    ancestors.Nodup →\n"
    "    (∀ r ∈ rows, r.length = 1 + (ancestors.filter (fun a => !sharesPrimaryKey a)).length) →\n"
    "    problem_spec_relatedTargetIds ancestors sharesPrimaryKey rows\n"
    "      (implementation_relatedTargetIds ancestors sharesPrimaryKey rows) := by\n"
    "  intro ancestors sharesPrimaryKey rows _ _\n"
    "  unfold problem_spec_relatedTargetIds implementation_relatedTargetIds\n"
    "  rfl\n"
)
POS_DIRECT = _swap(_swap(_BASE, _IMPL_FULL, _DIRECT_IMPL), _PROOF_BODY, _DIRECT_PROOF)

# (admiss) ADMISSIBILITY — the modeled behavior is satisfiable at an input shaped
# like the F2P scenario: a single ancestor that does NOT share the model's primary
# key (one dedicated column) over a one-row identifier table of the matching width.
# Both stated input requirements are re-derived in-region for it (distinct keys;
# every row carries exactly one column per gathered identifier), and the spec is
# discharged by `decide`, confirming the behavior is not unsatisfiable at the
# normal input — the analogue of PRECOND-TOO-STRONG. The ground instance is a
# `have` prepended before the frozen obligation, which is then closed verbatim;
# the `correct_` statement is byte-identical and nothing is assumed.
_ADMISS_BLOCK = (
    "  -- ADMISSIBILITY: the modeled behavior is satisfiable at an input shaped like\n"
    "  -- the F2P scenario — a single ancestor that does NOT share the model's primary\n"
    "  -- key (one dedicated column) over a one-row identifier table of matching width.\n"
    "  -- Both stated input requirements hold there.\n"
    "  have _pre_nodup : ([5] : List Nat).Nodup := by decide\n"
    "  have _pre_width : ∀ r ∈ ([[10, 20]] : List (List Int)),\n"
    "      r.length = 1 + (([5] : List Nat).filter (fun a => !(fun _ => false) a)).length := by decide\n"
    "  have _ground : problem_spec_relatedTargetIds [5] (fun _ => false) [[10, 20]]\n"
    "      (implementation_relatedTargetIds [5] (fun _ => false) [[10, 20]]) := by\n"
    "    unfold problem_spec_relatedTargetIds implementation_relatedTargetIds\n"
    "    decide\n"
    + _PROOF_INTRO
)
ADMISS = _swap(_BASE, _PROOF_INTRO, _ADMISS_BLOCK)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (weak-all-column-0) == the PRE-PATCH behaviour: every ancestor reuses column 0
# regardless of whether it actually shares the primary key. Correct only when
# every ancestor shares the key; wrong the instant any ancestor is non-sharing
# (it must read its OWN dedicated column, not column 0). Attacks (P-dense) /
# (P-reuse direction 2).
_RIVAL_ALL_ZERO = _swap(
    _BASE, _ASSIGN_LOOP,
    "  let mut assignment : List (Nat × Nat) := []\n"
    "  for ancestor in ancestors do\n"
    "    assignment := assignment ++ [(ancestor, 0)]\n",
)

# (weak-sparse) SPARSE dedicated columns (nextCol += 2): non-sharing ancestors get
# columns 1,3,5,… instead of the dense 1,2,3,…. Correct on ≤1 non-sharing ancestor
# (incl. both F2P scenarios), wrong with ≥2: the 2nd non-sharing ancestor reads
# column 3 of a width-3 row instead of column 2. Attacks (P-dense).
_RIVAL_SPARSE = _swap(_BASE, _WIDTH_BUMP, "      nextCol := nextCol + 2\n")

# (weak-const-column) COLLIDING constant dedicated column: every non-sharing
# ancestor gets column 1 (no advance). Correct on ≤1 non-sharing ancestor, wrong
# with ≥2: two distinct non-sharing ancestors collide on column 1 and the 2nd's
# column must be 2. Attacks (P-dense).
_RIVAL_CONST1 = _swap(
    _BASE, _ASSIGN_LOOP,
    "  let mut assignment : List (Nat × Nat) := []\n"
    "  for ancestor in ancestors do\n"
    "    if sharesPrimaryKey ancestor then\n"
    "      assignment := assignment ++ [(ancestor, 0)]\n"
    "    else\n"
    "      assignment := assignment ++ [(ancestor, 1)]\n",
)

# (weak-no-reuse) DUAL rival native to this carrier: a SHARING ancestor is denied
# column-0 reuse and instead consumes a dedicated column. Correct on any all-
# non-sharing chain, wrong the instant any ancestor shares the primary key (it
# must read column 0). Attacks (P-reuse direction 1) — the biconditional's other
# leg, which the value-side nagini rivals (all built over the non-sharing case)
# never probe from this side.
_RIVAL_NO_REUSE = _swap(
    _BASE, _ASSIGN_LOOP,
    "  let mut nextCol := 1\n"
    "  let mut assignment : List (Nat × Nat) := []\n"
    "  for ancestor in ancestors do\n"
    "    assignment := assignment ++ [(ancestor, nextCol)]\n"
    "    nextCol := nextCol + 1\n",
)


# ---- witnesses (each checked: elaborates vs rival, fails vs frozen) ----------
_P = "problem_spec_relatedTargetIds"
_I = "implementation_relatedTargetIds"


def _wit(ancestors, shares, rows):
    return (
        f"example : ¬ {_P}\n"
        f"    {ancestors} ({shares}) {rows}\n"
        f"    ({_I} {ancestors} ({shares}) {rows}) := by\n"
        f"  unfold {_P} {_I}\n"
        "  decide\n"
    )


# ancestors [7,8], ancestor 7 shares / 8 does not. gold: 7->col0, 8->col1;
# all-zero rival: 8->col0 too. Distinguishes at the non-sharing ancestor 8.
_WIT_ALL_ZERO = _wit("[7, 8]", "fun a => a == 7", "[[10, 20]]")

# ancestors [3,4] both non-sharing, width-3 rows. gold 2nd col=2; sparse 2nd col=3.
_WIT_SPARSE = _wit("[3, 4]", "fun _ => false", "[[10, 20, 30]]")

# ancestors [3,4] both non-sharing, width-3 rows (distinct row values from sparse).
# gold 2nd col=2; const rival 2nd col=1 (collides with the 1st).
_WIT_CONST1 = _wit("[3, 4]", "fun _ => false", "[[11, 22, 33]]")

# ancestor [9] shares the key. gold col=0; no-reuse rival col=1.
_WIT_NO_REUSE = _wit("[9]", "fun _ => true", "[[42]]")


SPEC_TESTS = [
    # ---- positive control / admissibility (must VERIFY) ----
    {
        "id": "pos-direct-composition",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_DIRECT,
        "rationale": "structurally-different CORRECT implementation: the two "
        "imperative accumulation loops are replaced by a direct composition of the "
        "grounded column assignment with the per-column read "
        "(`(columnAssignment … 1).map (fun ac => (ac.1, rows.map …))`). Same result "
        "on every input, so the postcondition (P-order/P-reuse/P-dense) still holds; "
        "must verify, else it is over-fit to the literal two-loop FORM => "
        "SPEC-TOO-STRONG. The frozen loop-bridge lemmas are tuned to the imperative "
        "loops and cannot elaborate against the closed form, so the proof region is "
        "replaced by a direct proof: after unfolding both defs the sides are "
        "syntactically identical and `rfl` closes. The `correct_` statement is kept "
        "byte-identical; no axiom / assumption token / new theorem is introduced (the "
        "replacement only DROPS frozen helper lemmas, which the scope rules permit).",
    },
    {
        "id": "admiss-single-nonsharing",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "the obligation is preceded by a ground instance at an input "
        "shaped like the F2P scenario — a single non-sharing ancestor over a one-row "
        "identifier table of matching width — with BOTH stated input requirements "
        "re-derived in-region (distinct keys `[5].Nodup`; every row carries exactly "
        "one column per gathered identifier) and the spec discharged by `decide`. "
        "Verifies (else the behavior is unsatisfiable at the normal input — the "
        "analogue of PRECOND-TOO-STRONG). A recursive self-instantiation is not "
        "needed and nothing is assumed: no new declaration, the `correct_` statement "
        "is byte-identical, and the ground instance is a `have` inside the existing "
        "tactic body followed by the frozen obligation verbatim.",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-all-column-0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ALL_ZERO,
        "refinement": "reusing column 0 for EVERY ancestor is exactly the pre-patch "
        "behaviour (only the model's own identifier column is gathered and reused). A "
        "faithful patch doing this leaves a non-sharing ancestor reading the child's "
        "identifiers instead of its own, so the ancestor's update filters the wrong "
        "rows and the update is lost — the exact F2P failure both tests assert "
        "against. So a verifying rival here would be a true verify-not-resolve break.",
        "rationale": "REJECT from (P-dense)/(P-reuse dir.2): a non-sharing ancestor "
        "(`sharesPrimaryKey a = false`) is assigned column 0, but the oracle demands "
        "its own dedicated column ≥1. partial-domain: correct only when every ancestor "
        "shares the key. If it verified => SPEC-TOO-WEAK.",
        "witness": _WIT_ALL_ZERO,
    },
    {
        "id": "weak-sparse-columns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SPARSE,
        "refinement": "advancing the dedicated column by 2 places non-sharing "
        "ancestors at columns 1,3,5,… while the materialized row has one column per "
        "non-sharing ancestor (contiguous). A faithful patch recording those indices "
        "then over-runs the row for the 2nd non-sharing ancestor (reads column 3 of a "
        "width-3 row) and errors at runtime, failing the F2P — verify-not-resolve.",
        "rationale": "REJECT from (P-dense): the k-th non-sharing ancestor must read "
        "column k, but after the first +2 the rival's column drifts above k (2nd "
        "reads column 3, oracle demands 2). partial-domain: correct on ≤1 non-sharing "
        "ancestor (incl. the F2P), wrong on ≥2. If it verified => SPEC-TOO-WEAK.",
        "witness": _WIT_SPARSE,
    },
    {
        "id": "weak-const-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CONST1,
        "refinement": "assigning the constant column 1 to every non-sharing ancestor "
        "(no advance) collides their columns: two distinct non-sharing ancestors both "
        "read column 1, so a faithful patch filters two different ancestor updates by "
        "the SAME column's identifiers — the second ancestor's rows are mis-updated on "
        "a ≥2-ancestor tree, failing an F2P-shaped assertion. Both shipped F2P "
        "scenarios reach exactly one non-sharing ancestor, so this rival is CORRECT on "
        "them yet wrong on the ≥2 sub-domain — verify-not-resolve.",
        "rationale": "REJECT from (P-dense): the 2nd non-sharing ancestor's column "
        "must be 2 but the rival returns 1 (colliding with the 1st). partial-domain: "
        "correct on ≤1 non-sharing ancestor, wrong on ≥2. If it verified => "
        "SPEC-TOO-WEAK (dense distinctness hollow).",
        "witness": _WIT_CONST1,
    },
    {
        "id": "weak-no-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NO_REUSE,
        "refinement": "denying column-0 reuse to a SHARING ancestor (giving it a "
        "dedicated column instead) is the biconditional's other leg. A faithful patch "
        "doing this would gather and record a dedicated column for an ancestor whose "
        "identifiers already live in column 0; the recorded index over-runs the "
        "actually-materialized row (which has NO dedicated column for a sharing "
        "ancestor), so the ancestor's update reads out of bounds and fails at runtime "
        "— verify-not-resolve. This carrier-native dual probes the (P-reuse dir.1) "
        "leg the value-side rivals never attack.",
        "rationale": "REJECT from (P-reuse dir.1): a sharing ancestor "
        "(`sharesPrimaryKey a = true`) must read column 0, but the rival gives it a "
        "dedicated column ≥1. partial-domain: correct on any all-non-sharing chain, "
        "wrong the instant an ancestor shares the key. If it verified => "
        "SPEC-TOO-WEAK.",
        "witness": _WIT_NO_REUSE,
    },
]
