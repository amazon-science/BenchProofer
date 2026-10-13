"""properties.py — G-PBT falsification battery for django__django-14999 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. Read the module
``assessment`` in the submission for the case-by-case correspondence and the
principled omissions. The essential carrier difference driving the whole port:
the nagini contract pinned only ``len(Result())`` (``==0`` on the two no-op
branches, ``>0`` on the proceed branch), so nagini's oracle was a length. This
Lean bundle models the emitted schedule as the ORDERED ``List SchemaOp`` and
pins ``result`` to a single GROUNDED term over the inputs
(``SchemaOp.renameTable oldDbTable newDbTable :: tailOps`` on the proceed
branch, ``[]`` on the two no-op branches). The spec is therefore strictly
STRONGER here than in nagini, and that has two consequences for the port:

  * nagini's ``pos-control-different-witness`` positive — emit a DIFFERENT
    non-empty schedule on the proceed branch — is a genuinely WRONG
    implementation on this carrier (it violates the exact-value clause), so it
    does not port as a positive; its adversarial content reappears, sharpened,
    as the reject rivals ``weak-drop-tail`` / ``weak-swap-names`` /
    ``weak-tail-order`` that each perturb one part of the pinned term;
  * two attackable surfaces exist here that nagini's length-only oracle never
    had: the applicability guard (``allowMigrate``, clause 1) and the exact
    dependent-follow-up passthrough (the tail of the pinned cons, clause 3),
    both defended by dedicated rivals below.

DEFENDED SURFACE (one modeled behavior). The emitted schedule is pinned in
every case by three independent top-level clauses of the postcondition, each
selected by the inputs:

  * NOT-APPLICABLE no-op — when the applicability guard is off, nothing is
    emitted (clause 1);
  * UNCHANGED-NAME no-op — when the stored table name is unchanged by the
    rename, nothing is emitted (clause 2, the behavioural change the fix
    introduces);
  * PROCEED — otherwise the main table rename is emitted FIRST, with the two
    stored names in that order, FOLLOWED by exactly the dependent follow-up
    operations, unchanged and in order (clause 3).

The BEHAVIOURAL DISCRIMINATOR (the fix) is the UNCHANGED-NAME no-op: the pre-fix
code emitted the main move (and the dependent follow-ups) whenever the operation
was applicable, so an applicable rename with a stored name that does not change
issued schema work where none is wanted. The F2P scenario is exactly that
applicable-but-unchanged input; the ``weak-*`` rivals that attack clause 2 ARE
the pre-fix behavior.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival (write
    into the read-only ``relations`` input) has no expressible instance here —
    ``tailOps`` is an immutable value threaded structurally — so no substitute
    is fabricated. (nagini case ``frame-mutation-write-relations``.)

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_renameModel``
    is a total Lean ``def``; a diverging implementation cannot be written at all,
    so there is no partial-correctness hole to probe. (The nagini sibling carries
    no divergence case either.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs (a cons of the two
    stored names into a ``renameTable`` op, followed by the ``tailOps`` input).
    There is no opaque answer key an implementation could echo, and no ``opaque``
    callee or consumed ``axiom`` anywhere in the bundle. In its place the battery
    carries honest cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the battery: rivals
    correct on part of the domain but diverging where a clause bites — dropping
    the unchanged-name guard, gating only the main move on the unchanged-name
    test while the follow-up work still runs, dropping the applicability guard,
    never emitting, dropping the dependent tail, swapping the two names,
    emitting the wrong op KIND as the head, reordering main-vs-tail, and
    mis-classifying one genuinely-changed pair as unchanged.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it. This carrier is fully
transparent (``Bool`` / ``String`` / ``List SchemaOp`` with ``DecidableEq``), so
every witness closes by ``decide`` at concrete literal inputs — no opaque term
to condition on, no arithmetic normaliser needed. Each was checked to HOLD of
its rival and to FAIL on the frozen solution (``decide`` proves the spec TRUE
there, so ``¬spec`` cannot close), so it discriminates rather than asserting a
tautology.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
rather than fixing them at one convenient point. ``allowMigrate`` takes both
settings (the applicability rival probes ``false``; the rest probe ``true``);
the stored-name pair is EQUAL at the unchanged-name no-op point and DISTINCT
elsewhere, and distinct rivals use distinct distinct-pairs
(``"a"/"b"``, ``"c"/"d"``, ``"e"/"f"``, ``"m"/"n"``, ``"g"/"h"``, ``"p"/"q"``,
``"x"/"y"``, and ``"t"/"t"`` for the equal-name point) so no two share a
refutation point unless they fail there for the same reason;
``tailOps`` ranges over empty and a non-empty singleton (the drop-tail and
tail-order rivals require a non-empty tail to bite, so that binder is
demonstrated live rather than held at ``[]``).

AXIOM lane: EMPTY. The bundle consumes no ``axiom`` and declares no ``opaque``
callee (``meta`` axioms == []). The axiom lane belongs to G-AX; this gate
ignores it, and the nagini ``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-14999"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The frozen gold impl body (the entire text inside -- impl-start / -- impl-end).
# Every reject rival is a _swap of this exact block, so nothing outside the impl
# region is touched and same_spec holds by construction.
_GOLD_IMPL = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if !allowMigrate then
    return []
  if oldDbTable == newDbTable then
    return []
  let mut acc : List SchemaOp := []
  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
  acc := acc ++ tailOps
  return acc"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from Solution.lean"

# The frozen gold proof body (the tactic block inside -- proof-start / --
# proof-end, after the theorem statement). Positive controls that reshape the
# impl re-prove inside this region while keeping the theorem STATEMENT identical.
_GOLD_PROOF = """  intro allowMigrate oldDbTable newDbTable tailOps
  unfold problem_spec_renameModel implementation_renameModel
  refine ⟨?_, ?_, ?_⟩
  · intro hm
    simp only [hm, Bool.not_false, Id.run, ite_true]
    rfl
  · intro hm heq
    subst hm
    simp only [Id.run, heq, beq_self_eq_true, ite_true, Bool.not_true,
      if_false, Bool.false_eq_true]
    rfl
  · intro hm hne
    subst hm
    have hbeq : (oldDbTable == newDbTable) = false := by
      simpa using hne
    simp only [Id.run, hbeq, Bool.not_true, if_false, Bool.false_eq_true]
    rfl"""

assert _GOLD_PROOF in _BASE, "gold proof block drifted from Solution.lean"

# The unique start of the frozen proof body — anchor for the admissibility case,
# which prepends a ground `have` and then keeps the frozen tactic verbatim.
_PROOF_HEAD = "  intro allowMigrate oldDbTable newDbTable tailOps\n"
assert _BASE.count(_PROOF_HEAD) == 1, "proof-head anchor not unique"


def _impl(body: str) -> str:
    """A full Solution.lean variant swapping only the impl region body."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_and_proof(impl_body: str, proof_body: str) -> str:
    """A full variant swapping the impl region AND re-proving inside the proof
    region (statement byte-identical). Used only by positive controls."""
    return _swap(_swap(_BASE, _GOLD_IMPL, impl_body), _GOLD_PROOF, proof_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-control-branch-reorder: structurally different but CORRECT. The gold tests
# the applicability guard first, then the unchanged-name guard; this reorders to
# test the unchanged-name guard FIRST (still returning [] on either no-op path)
# and emits the SAME pinned term on the proceed branch. The reshape needs a fresh
# proof (a `by_cases` on the name equality inside the first no-op arm), which is
# supplied — no helper lemma, no axiom, no `sorry`. Ports nagini's
# `pos-control-branch-reorder` (which reordered the equal/proceed branches).
_POS_REORDER_IMPL = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if oldDbTable == newDbTable then
    return []
  if !allowMigrate then
    return []
  return SchemaOp.renameTable oldDbTable newDbTable :: tailOps"""

_POS_REORDER_PROOF = """  intro allowMigrate oldDbTable newDbTable tailOps
  unfold problem_spec_renameModel implementation_renameModel
  refine ⟨?_, ?_, ?_⟩
  · intro hm; subst hm
    by_cases h : oldDbTable == newDbTable <;> simp only [Id.run, h] <;> rfl
  · intro hm heq; subst hm; subst heq
    simp only [Id.run, beq_self_eq_true, ite_true]; rfl
  · intro hm hne; subst hm
    have hb : (oldDbTable == newDbTable) = false := by simpa using hne
    simp only [Id.run, hb]; rfl"""

# pos-control-functional-form: an equivalent NON-imperative shape — a single
# `if allowMigrate && oldDbTable != newDbTable then <pinned term> else []`,
# collapsing the two guards into one conjunction. Emits the identical schedule on
# every input; re-proved from scratch. This is the closest correct analogue of
# nagini's `pos-control-different-witness` intent (a structurally different
# correct impl), reshaped to respect the exact-value clause this carrier pins.
_POS_FUNC_IMPL = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp :=
  if allowMigrate && oldDbTable != newDbTable then
    SchemaOp.renameTable oldDbTable newDbTable :: tailOps
  else []"""

_POS_FUNC_PROOF = """  intro allowMigrate oldDbTable newDbTable tailOps
  unfold problem_spec_renameModel implementation_renameModel
  refine ⟨?_, ?_, ?_⟩
  · intro hm; subst hm; simp
  · intro hm heq; subst hm; subst heq; simp
  · intro hm hne; subst hm
    have hb : (oldDbTable == newDbTable) = false := by simpa using hne
    simp only [Bool.true_and, bne, hb, Bool.not_false, if_true]"""

# admiss-noop-fk-input: discharge the obligation at the F2P-shaped input (the
# applicable, stored-name-unchanged scenario: allowMigrate=true, equal names, one
# dependent follow-up present) by evaluation inside a `have`, then close the
# frozen obligation verbatim. Nothing is assumed: no new declaration, statement
# byte-identical, ground instance is a `have` inside the existing tactic body.
# Ports nagini's `admiss-noop-fk-input`.
_ADMISS_PROOF = _PROOF_HEAD + (
    '  have _ground : problem_spec_renameModel true "rider" "rider" [SchemaOp.other 0]\n'
    '      (implementation_renameModel true "rider" "rider" [SchemaOp.other 0]) := by\n'
    "    unfold problem_spec_renameModel implementation_renameModel\n"
    "    simp only [Id.run]; decide\n"
)


# ---------------------------------------------------------------------------
# UNIQUENESS / falsification (SPEC-TOO-WEAK probes) — must be REJECTED.
# Each carries a refinement (why its faithful real patch would NOT resolve the
# F2P) and a witness (the concrete-input refutation, checked to hold of the
# rival and fail on gold).
# ---------------------------------------------------------------------------

# weak-drop-noop-guard: THE pre-fix defect in its COARSEST form. Drop the
# unchanged-name guard entirely, keep only the applicability guard. On an
# applicable rename whose stored name is unchanged it emits the main move +
# dependent follow-ups. Rejected by clause 2. (`weak-tail-on-noop` below is the
# finer sibling — guard present but covering only the main move — and is the
# closer analogue of nagini's `weak-prepatch-bug`; both are carried because a
# spec could reject one and admit the other.)
_WEAK_DROP_NOOP = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if !allowMigrate then
    return []
  let mut acc : List SchemaOp := []
  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
  acc := acc ++ tailOps
  return acc"""

# weak-tail-on-noop: the FINER pre-fix shape, and the direct lean analogue of
# nagini's `weak-prepatch-bug`. Unlike weak-drop-noop-guard (which has no
# unchanged-name guard at all), this rival DOES suppress the main table move on
# the unchanged-name branch but still emits the dependent follow-ups there. So
# the guard is present and merely INCOMPLETE — it covers the main move only,
# leaving the follow-up work ungated. Rejected by clause 2 whenever the tail is
# non-empty. This is a strictly harder case than weak-drop-noop-guard: a spec
# that pinned only "the main move is suppressed on the no-op branch" rather than
# "NOTHING is emitted" would reject that rival and admit this one.
_WEAK_TAIL_ON_NOOP = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if !allowMigrate then
    return []
  if oldDbTable == newDbTable then
    return tailOps
  return SchemaOp.renameTable oldDbTable newDbTable :: tailOps"""

# weak-always-empty: never emit anything. Satisfies both no-op clauses but
# violates the proceed clause (3): a genuine rename issues no schema work.
_WEAK_EMPTY = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  return []"""

# weak-drop-applicability: drop the applicability guard, keep the unchanged-name
# guard. On a NOT-applicable rename with distinct names it emits schema work.
# Rejected by clause 1.
_WEAK_DROP_APPLIC = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if oldDbTable == newDbTable then
    return []
  let mut acc : List SchemaOp := []
  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
  acc := acc ++ tailOps
  return acc"""

# weak-drop-tail: on the proceed branch emit ONLY the main move, dropping the
# dependent follow-ups. Rejected by the passthrough part of clause 3 whenever
# tailOps is non-empty.
_WEAK_DROP_TAIL = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if !allowMigrate then
    return []
  if oldDbTable == newDbTable then
    return []
  return [SchemaOp.renameTable oldDbTable newDbTable]"""

# weak-swap-names: emit the main move with the two stored names in the WRONG
# order. Rejected by the name-order part of clause 3 whenever the names differ.
_WEAK_SWAP_NAMES = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if !allowMigrate then
    return []
  if oldDbTable == newDbTable then
    return []
  let mut acc : List SchemaOp := []
  acc := acc ++ [SchemaOp.renameTable newDbTable oldDbTable]
  acc := acc ++ tailOps
  return acc"""

# weak-tail-order: emit the dependent follow-ups FIRST, then the main move.
# Rejected by the ordering part of clause 3 whenever tailOps is non-empty.
_WEAK_TAIL_ORDER = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if !allowMigrate then
    return []
  if oldDbTable == newDbTable then
    return []
  let mut acc : List SchemaOp := []
  acc := acc ++ tailOps
  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
  return acc"""

# weak-wrong-constructor: on the proceed branch emit an op of the WRONG KIND as
# the head — some other emitted operation instead of the main table move — with
# the dependent follow-ups passed through correctly. Rejected by the head-op
# IDENTITY part of clause 3. Distinct from weak-swap-names, which keeps the
# `renameTable` constructor and perturbs only its two arguments: this rival is
# the only one pinning that the head op is a table rename AT ALL.
_WEAK_WRONG_CTOR = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if !allowMigrate then
    return []
  if oldDbTable == newDbTable then
    return []
  return SchemaOp.other 0 :: tailOps"""

# weak-partial-domain: correct on the whole domain EXCEPT one distinct-name pair,
# which it mis-classifies as unchanged and treats as a no-op. Rejected by clause
# 3 on exactly that pair; correct elsewhere.
_WEAK_PARTIAL = """def implementation_renameModel
    (allowMigrate : Bool) (oldDbTable newDbTable : String)
    (tailOps : List SchemaOp) : List SchemaOp := Id.run do
  if !allowMigrate then
    return []
  if oldDbTable == newDbTable then
    return []
  if oldDbTable == "p" && newDbTable == "q" then
    return []
  let mut acc : List SchemaOp := []
  acc := acc ++ [SchemaOp.renameTable oldDbTable newDbTable]
  acc := acc ++ tailOps
  return acc"""


def _wit(head: str) -> str:
    """A witness stating `¬ problem_spec … (implementation …)` at a concrete
    input, closed by `decide`. `head` is the argument list shared by the spec
    and impl applications."""
    return (
        f"example : ¬ problem_spec_renameModel {head}\n"
        f"    (implementation_renameModel {head}) := by\n"
        "  unfold problem_spec_renameModel implementation_renameModel\n"
        "  simp only [Id.run]\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS
    # =====================================================================
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_and_proof(_POS_REORDER_IMPL, _POS_REORDER_PROOF),
        "rationale": (
            "a structurally-different but CORRECT impl (the unchanged-name no-op "
            "tested FIRST, then the applicability no-op, then the same pinned "
            "term on the proceed branch) must verify; all three clauses still "
            "hold. If it cannot verify => SPEC-TOO-STRONG. The theorem STATEMENT "
            "is byte-identical; the proof region is re-proved honestly (a "
            "`by_cases` on the name equality inside the first no-op arm) — no "
            "helper lemma, no axiom, no sorry. Ports nagini's "
            "pos-control-branch-reorder."),
    },
    {
        "id": "pos-control-functional-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_and_proof(_POS_FUNC_IMPL, _POS_FUNC_PROOF),
        "rationale": (
            "an equivalent NON-imperative shape collapsing both guards into a "
            "single `allowMigrate && oldDbTable != newDbTable` conjunction, "
            "emitting the identical schedule on every input. Must verify; "
            "confirms the spec pins the observable schedule, not a particular "
            "control-flow shape. Re-proved from scratch (statement identical). "
            "This is the exact-value-respecting analogue of nagini's "
            "pos-control-different-witness, which does not port as a positive on "
            "this carrier because the spec pins the schedule value exactly."),
    },
    {
        "id": "admiss-noop-fk-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_HEAD, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P-shaped input (applicable, "
            "stored name unchanged, one dependent follow-up present — the "
            "Pony.rider no-op scenario) by evaluation inside a `have`, then the "
            "frozen obligation is closed verbatim. Verifies (else the modeled "
            "behavior is unsatisfiable at exactly the input the F2P exercises — "
            "the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
            "declaration, the theorem statement is byte-identical, the ground "
            "instance is a `have` inside the existing tactic body. Ports "
            "nagini's admiss-noop-fk-input."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals
    # =====================================================================
    {
        "id": "weak-drop-noop-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_NOOP),
        "refinement": (
            "this IS the pre-fix defect: no guard for an unchanged stored table "
            "name, so an applicable rename whose stored name does not change "
            "still emits the main move and the dependent follow-ups — the "
            "schema work the issue reports (Postgres drops/recreates the FK "
            "constraints; sqlite recreates the table). Its faithful real patch "
            "(the body with the unchanged-name early-return removed) issues "
            "queries on that input, so the F2P assertNumQueries(0) fails and it "
            "does NOT resolve."),
        "rationale": (
            "REJECT from clause 2 (applicable + unchanged name => empty "
            "schedule): with allowMigrate=true and equal names the rival returns "
            "a non-empty schedule where the spec forces []. Binder spread: "
            "allowMigrate=true, EQUAL names, non-empty tail."),
        "witness": _wit('true "t" "t" [SchemaOp.other 0]'),
    },
    {
        "id": "weak-tail-on-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_TAIL_ON_NOOP),
        "refinement": (
            "the unchanged-name guard is PRESENT but incomplete: it suppresses "
            "the main table move on the unchanged-name branch yet still lets "
            "the dependent follow-up work run. A faithful real patch that "
            "skipped only the main-table call on that branch, without returning "
            "before the dependent-relation and link-table follow-up loops, "
            "would still issue schema work on an applicable rename whose "
            "stored name does not change — so the F2P's zero-query expectation "
            "still fails and it does NOT resolve, even though it looks like it "
            "has the guard."),
        "rationale": (
            "REJECT from clause 2 (applicable + unchanged name => EMPTY "
            "schedule, not merely a schedule without the main move): with "
            "allowMigrate=true, equal names and a non-empty tail the rival "
            "returns tailOps where the spec forces []. This is the lean "
            "analogue of nagini's weak-prepatch-bug, whose defect was exactly "
            "'follow-up work runs unconditionally, only the main move is "
            "gated'. It is NOT subsumed by weak-drop-noop-guard, which removes "
            "the guard entirely: this rival is correct on the whole proceed "
            "branch and on the not-applicable branch, and needs a non-empty "
            "tail at the EQUAL-name point to bite at all — so it pins that "
            "clause 2 demands an empty schedule rather than just the absence "
            "of the rename op."),
        "witness": _wit('true "t" "t" [SchemaOp.other 0]'),
    },
    {
        "id": "weak-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY),
        "refinement": (
            "always a no-op — never emits schema work even on a genuine rename. "
            "A faithful real patch that unconditionally returned early would "
            "make EVERY applicable, name-changing rename a silent no-op, so the "
            "table is never actually moved and the P2P rename expectations (a "
            "real rename DOES issue schema work) fail => does NOT resolve."),
        "rationale": (
            "REJECT from clause 3 (applicable + distinct names => "
            "renameTable::tailOps): on distinct names it returns [] where the "
            "spec forces the non-empty pinned term. Moves allowMigrate=true, "
            "DISTINCT names, non-empty tail."),
        "witness": _wit('true "a" "b" [SchemaOp.other 0]'),
    },
    {
        "id": "weak-drop-applicability",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_APPLIC),
        "refinement": (
            "drops the applicability guard, keeping only the unchanged-name "
            "guard. A faithful real patch that ran the body without checking "
            "applicability would issue schema work for a rename the router "
            "excluded from this connection — corrupting a database it was never "
            "meant to touch — so the applicability-dependent expectations fail "
            "=> does NOT resolve."),
        "rationale": (
            "REJECT from clause 1 (not applicable => empty schedule): with "
            "allowMigrate=false and distinct names the rival emits the pinned "
            "term where the spec forces []. The ONLY rival probing "
            "allowMigrate=false, so that binder is demonstrated live."),
        "witness": _wit('false "c" "d" [SchemaOp.other 0]'),
    },
    {
        "id": "weak-drop-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_TAIL),
        "refinement": (
            "on the proceed branch emits ONLY the main table move, dropping the "
            "dependent follow-up operations. A faithful real patch that returned "
            "after alter_db_table without running the related-objects / m2m "
            "follow-up loops would leave dependent FK columns and link tables "
            "pointing at the old table name, so the rename is applied "
            "incompletely and the dependent-relation expectations fail => does "
            "NOT resolve."),
        "rationale": (
            "REJECT from the passthrough part of clause 3: the spec appends the "
            "WHOLE tailOps input after the main move, the rival appends nothing, "
            "so with a non-empty tail `result` differs. Moves the tailOps binder "
            "to a non-empty singleton (the binder held at [] by several other "
            "rivals) at a distinct name pair."),
        "witness": _wit('true "e" "f" [SchemaOp.other 7]'),
    },
    {
        "id": "weak-swap-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAP_NAMES),
        "refinement": (
            "emits the main table move with the two stored names in the WRONG "
            "order (new-then-old). A faithful real patch that passed the table "
            "names to alter_db_table swapped would rename the table in the wrong "
            "direction, so the resulting table name is wrong and the rename "
            "expectations fail => does NOT resolve."),
        "rationale": (
            "REJECT from the name-order part of clause 3: the spec pins "
            "renameTable oldDbTable newDbTable, the rival emits renameTable "
            "newDbTable oldDbTable, distinct whenever the names differ, so "
            "`result` differs. Uses an empty tail at its own distinct name pair, "
            "isolating the name-order defect from the tail defects."),
        "witness": _wit('true "m" "n" []'),
    },
    {
        "id": "weak-tail-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_TAIL_ORDER),
        "refinement": (
            "emits the dependent follow-ups FIRST and the main table move last "
            "(order reversed). A faithful real patch that issued the FK/m2m "
            "follow-ups before moving the main table would rewrite dependent "
            "references against a table that has not been renamed yet, "
            "corrupting the migration => does NOT resolve."),
        "rationale": (
            "REJECT from the ordering part of clause 3: the spec pins "
            "renameTable::tailOps (main first), the rival returns "
            "tailOps++[main] (main last), distinct whenever tailOps is "
            "non-empty. Moves the tailOps binder to a non-empty singleton at a "
            "distinct name pair, separating the order defect from the drop-tail "
            "defect."),
        "witness": _wit('true "g" "h" [SchemaOp.other 3]'),
    },
    {
        "id": "weak-wrong-constructor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_WRONG_CTOR),
        "refinement": (
            "emits an operation of the WRONG KIND as the head of the schedule "
            "instead of the main table move, passing the dependent follow-ups "
            "through correctly. A faithful real patch that issued some other "
            "schema-editor call in place of the main table move would never "
            "actually move the table, so the rename does not reach the "
            "database and the rename expectations fail => does NOT resolve."),
        "rationale": (
            "REJECT from the head-op IDENTITY part of clause 3: the spec pins "
            "the head to `SchemaOp.renameTable oldDbTable newDbTable`, the "
            "rival emits a different constructor, so `result` differs even "
            "though the length and the whole tail agree. This is the only "
            "rival pinning the head op's CONSTRUCTOR: weak-swap-names keeps "
            "`renameTable` and permutes its arguments, and the length/order "
            "rivals keep the constructor too, so without this case a spec that "
            "pinned only the shape and arity of the head would pass the "
            "battery. Uses its own distinct pair \"x\"/\"y\" at an empty tail, "
            "isolating the constructor defect from the tail defects."),
        "witness": _wit('true "x" "y" []'),
    },
    {
        "id": "weak-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PARTIAL),
        "refinement": (
            "correct on the whole input domain EXCEPT one distinct-name pair, "
            "which it mis-classifies as unchanged and treats as a no-op. A "
            "faithful real patch whose unchanged-name test aliased one pair of "
            "genuinely-distinct db_table identities to 'unchanged' would skip "
            "the real rename for that pair, so the F2P/P2P for that genuine "
            "rename fail => does NOT resolve. Correct on the rest of the domain, "
            "so a byte-fuzzer that never hits the pair would miss it."),
        "rationale": (
            "REJECT from clause 3: on the mis-classified pair (distinct names) "
            "the rival returns [] where the spec forces the non-empty pinned "
            "term. Probed at exactly that pair, which no other rival uses as "
            "its refutation point. Note the claim this case DOES make: the "
            "rival agrees with gold on every input except that one pair, so "
            "the witness has to name the pair to refute at all — a witness at "
            "any other distinct-name pair would FAIL against this rival. That "
            "is the localized sub-domain the manifest claims, and it is why "
            "this case is not subsumed by weak-always-empty (which is wrong on "
            "EVERY distinct pair, hence refutable anywhere)."),
        "witness": _wit('true "p" "q" []'),
    },
]

# No AXIOM lane: the bundle consumes no `axiom` and declares no `opaque` callee
# (meta.axioms == []). The nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
