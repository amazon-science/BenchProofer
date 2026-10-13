"""properties.py — G-PBT falsification battery for django__django-11066 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and the ``theorem correct_renameContentType`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a multi-database world):

  renameContentType
      (world : Alias → List ContentTypeRec)
      (db routerChoice : Alias)
      (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec

  A rename runs against ONE designated database ``db``. The spec pins the
  ENTIRE resulting world at every alias ``a``:

    ∀ a, result a =
      if the located record (natural key (appLabel, oldModel)) is present in db
        then if persisting the rename to db would collide with db's unique
               (appLabel, newModel) key (newModel ≠ oldModel)
               then world a                      -- rejected + rolled back
             else if a = db then rename applied to db's store
             else world a                        -- every OTHER database untouched
      else world a                               -- located record absent

  ``Alias`` is ``Nat`` (identity encoding). ``routerChoice`` is a FREE input —
  the persistence layer's own destination choice; the desired behavior is that
  the result depends only on ``db`` and NEVER on ``routerChoice``.

  Independent, separately-attackable decisions folded into the one clause:

    * WHICH DATABASE receives the write — the spec pins it to ``db`` alone; a
      routed write to ``routerChoice`` (the free input) is the load-bearing bug.
      Pinned by ``db`` vs ``routerChoice`` and by the ``a = db`` selector.
    * WHETHER a colliding rename is rolled back — collision ⇒ every database
      identical to input. Pinned by the destination store's records and
      ``newModel``/``oldModel``.
    * WHICH RECORDS in the target store change — only the record matching
      ``(appLabel, oldModel)``; every other record in that store is left
      exactly as it was. Pinned by the store's non-matching records.
    * WHICH DATABASES change at all — only ``db``; every other alias's store is
      identical to its input (the outer frame). Pinned by the alias binder ``a``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION (nagini's #1 class, mandatory there because the
    inputs are held at fractional read-only permission) — VACUOUS as a
    PERMISSION attack. Lean is referentially transparent: ``world`` and the
    scalar inputs are immutable values, there is no half-permission to violate
    and no aliasing to overwrite. The SEMANTIC content of nagini's frame
    obligation — "the read-only inputs are not silently changed into the answer"
    — survives here as an explicit FRAME clause of the spec: every alias other
    than ``db`` (and every non-matching record within ``db``'s store) must equal
    its input. That frame IS attacked, by rivals that write to every database
    (weak-apply-every-database) or to every record (weak-rename-whole-store).
    No permission-violation substitute is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term built only from the inputs (``hasKey`` / ``renameConflicts`` /
    ``renameInStore`` over ``world``, ``db``, the keys), fully structural. The
    bundle declares no ``opaque``/``axiom`` (meta.json axioms == [],
    deep_model_references == []), so there is no answer key to echo. The honest
    analogue is the cheapest-correct POSITIVE CONTROL below.

  * PREPATCH ECHO / routed-write (the CENTRAL attack, nagini's ``weak-prepatch``)
    — APPLIES and is the load-bearing rival. The pre-fix persisted the rename
    WITHOUT naming an explicit destination, so the free ``routerChoice`` decided
    the write target. Whenever ``routerChoice ≠ db`` the rename lands on the
    wrong database and ``db`` is never updated — exactly the F2P sub-domain
    (``db`` = 'other', router = 'default').

  * PARTIAL-DOMAIN / dropped-guard rivals — APPLY. A rival that skips the
    unique-key rollback check (weak-drop-conflict-rollback) is correct except on
    the collision sub-domain, refuted precisely there.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen ``simp only [… saveTarget …]`` script is
tuned to the frozen form), so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at a concrete input. The spec is ``∀ a, result a = …`` over an
INFINITE alias domain, so a witness cannot ``decide`` the quantifier directly:
it ``intro``s the universal and instantiates it at the ONE alias where the rival
diverges (``h 0`` / ``h 1``), then discharges that ground disequality by
``decide``. Each witness was checked to HOLD of its rival and to FAIL on the
frozen solution (so it discriminates rather than asserting a tautology).

BINDER COVERAGE. Every input binder of the spec predicate is varied across the
reject witnesses:
  * ``routerChoice`` — the free input the fix turns on. Refuted at
    ``routerChoice ≠ db`` (weak-route-to-router, where the routed write misses
    ``db``) and held equal-or-irrelevant elsewhere.
  * the alias binder ``a`` of ``result a`` — the witnesses instantiate it at
    ``a = db`` (route/conflict/whole-store rivals) AND at ``a ≠ db`` (the
    apply-every-database rival), so the spec's per-alias dependence is exercised
    on both sides of the ``a = db`` split.
  * ``db`` — held at ``0`` for most witnesses and at ``1`` for the conflict
    witness, so it is not pinned to a single value.
  * ``appLabel`` / ``oldModel`` / ``newModel`` — held at ``0/0/1`` for most and
    at ``2/3/4`` for the conflict witness (distinct from every other binder), so
    the natural-key/rename identities are not pinned to one value either.
  * ``world`` — varied in shape: single-record, two-record-with-non-matching,
    and constant-across-aliases, so the store's contents drive distinct clauses.
``pts`` = 4 distinct scalar-argument points (two rivals share the scalar tuple
``(0,0,0,0,1)`` but differ in the ``world`` argument and the alias probed).

ADMISSIBILITY lane: PRESENT (``admiss-ground-f2p-routed``). The frozen
obligation is an unconditional ``∀``, so there is no precondition binder to
attack; on this total carrier the analogue of PRECOND-TOO-STRONG is the
obligation being UNSATISFIABLE at exactly an F2P-shaped input, which the case
tests by discharging the spec predicate BY EVALUATION at the concrete
``routerChoice ≠ db`` point before closing the frozen obligation verbatim. This
is the direction no ``expect="reject"`` case can see: a spec contradictory at
that input would still reject every rival there.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
routing decision and the record update are modeled structurally over the data,
so there is no axiom-soundness / axiom-containment obligation to probe here
(that lane belongs to G-AX regardless). AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-11066"

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
    "def implementation_renameContentType\n"
    "    (world : Alias → List ContentTypeRec)\n"
    "    (db routerChoice : Alias)\n"
    "    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do\n"
    "  -- Locate the record on the connection this operation is running against.\n"
    "  if !hasKey (world db) appLabel oldModel then\n"
    "    return world\n"
    "  -- The located record's model-name identity is updated and the change is\n"
    "  -- persisted to the connection the operation is running against.\n"
    "  let target := saveTarget routerChoice (some db)\n"
    "  -- The database receiving the write enforces the unique natural-key\n"
    "  -- constraint; a colliding rename is rejected and the surrounding\n"
    "  -- transaction rolls it back, so nothing is persisted anywhere.\n"
    "  if renameConflicts (world target) appLabel oldModel newModel then\n"
    "    return world\n"
    "  let mut updated := world\n"
    "  updated := fun a =>\n"
    "    if a = target then renameInStore (world target) appLabel oldModel newModel\n"
    "    else world a\n"
    "  return updated\n"
)

_PROOF_BODY = (
    "  intro world db routerChoice appLabel oldModel newModel a\n"
    "  show implementation_renameContentType world db routerChoice appLabel oldModel newModel a = _\n"
    "  by_cases h : hasKey (world db) appLabel oldModel\n"
    "  · by_cases hc : renameConflicts (world db) appLabel oldModel newModel\n"
    "    · simp only [implementation_renameContentType, saveTarget, Id.run, h, hc,\n"
    "        Bool.not_true, Bool.false_eq_true, if_false, if_true]\n"
    "      rfl\n"
    "    · simp only [implementation_renameContentType, saveTarget, Id.run, h, hc,\n"
    "        Bool.not_true, Bool.false_eq_true, if_false, if_true]\n"
    "      rfl\n"
    "  · simp only [implementation_renameContentType, saveTarget, Id.run, h,\n"
    "      Bool.not_false, if_true, Bool.false_eq_true, if_false]\n"
    "    rfl\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# PREPATCH ECHO (the load-bearing bug): persist WITHOUT naming an explicit
# destination, so the free routerChoice picks the write target. Correct whenever
# routerChoice = db; wrong precisely when they differ (the F2P sub-domain).
_ROUTE_TO_ROUTER = (
    "def implementation_renameContentType\n"
    "    (world : Alias → List ContentTypeRec)\n"
    "    (db routerChoice : Alias)\n"
    "    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do\n"
    "  if !hasKey (world db) appLabel oldModel then\n"
    "    return world\n"
    "  let target := saveTarget routerChoice none\n"
    "  if renameConflicts (world target) appLabel oldModel newModel then\n"
    "    return world\n"
    "  let mut updated := world\n"
    "  updated := fun a =>\n"
    "    if a = target then renameInStore (world target) appLabel oldModel newModel\n"
    "    else world a\n"
    "  return updated\n"
)

# DROP-CONFLICT-ROLLBACK: apply the rename unconditionally, skipping the
# unique-key collision check. Correct except on the collision sub-domain.
_DROP_CONFLICT = (
    "def implementation_renameContentType\n"
    "    (world : Alias → List ContentTypeRec)\n"
    "    (db routerChoice : Alias)\n"
    "    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do\n"
    "  if !hasKey (world db) appLabel oldModel then\n"
    "    return world\n"
    "  let target := saveTarget routerChoice (some db)\n"
    "  let mut updated := world\n"
    "  updated := fun a =>\n"
    "    if a = target then renameInStore (world target) appLabel oldModel newModel\n"
    "    else world a\n"
    "  return updated\n"
)

# APPLY-EVERY-DATABASE (outer frame violation): rename in EVERY database's store,
# not just the target's. Diverges at any OTHER alias that also holds the key.
_APPLY_EVERYWHERE = (
    "def implementation_renameContentType\n"
    "    (world : Alias → List ContentTypeRec)\n"
    "    (db routerChoice : Alias)\n"
    "    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do\n"
    "  if !hasKey (world db) appLabel oldModel then\n"
    "    return world\n"
    "  let target := saveTarget routerChoice (some db)\n"
    "  if renameConflicts (world target) appLabel oldModel newModel then\n"
    "    return world\n"
    "  let mut updated := world\n"
    "  updated := fun a => renameInStore (world a) appLabel oldModel newModel\n"
    "  return updated\n"
)

# RENAME-WHOLE-STORE (inner frame violation): in the target store, set EVERY
# record's model to newModel instead of only the matching one. Diverges when the
# target store holds a non-matching record.
_RENAME_WHOLE_STORE = (
    "def implementation_renameContentType\n"
    "    (world : Alias → List ContentTypeRec)\n"
    "    (db routerChoice : Alias)\n"
    "    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do\n"
    "  if !hasKey (world db) appLabel oldModel then\n"
    "    return world\n"
    "  let target := saveTarget routerChoice (some db)\n"
    "  if renameConflicts (world target) appLabel oldModel newModel then\n"
    "    return world\n"
    "  let mut updated := world\n"
    "  updated := fun a =>\n"
    "    if a = target then (world target).map (fun r => { r with model := newModel })\n"
    "    else world a\n"
    "  return updated\n"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — the
# explicit destination IS db, so name it directly (drop the `saveTarget … (some
# db)` indirection). Same value on every input; the theorem STATEMENT is
# byte-identical and the tactic body is re-proved for the new shape (the frozen
# script names `saveTarget`, which no longer appears). No helper/axiom/sorry.
_POS_DIRECT = (
    "def implementation_renameContentType\n"
    "    (world : Alias → List ContentTypeRec)\n"
    "    (db routerChoice : Alias)\n"
    "    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do\n"
    "  if !hasKey (world db) appLabel oldModel then\n"
    "    return world\n"
    "  let target := db\n"
    "  if renameConflicts (world target) appLabel oldModel newModel then\n"
    "    return world\n"
    "  let mut updated := world\n"
    "  updated := fun a =>\n"
    "    if a = target then renameInStore (world target) appLabel oldModel newModel\n"
    "    else world a\n"
    "  return updated\n"
)
_POS_DIRECT_PROOF = (
    "  intro world db routerChoice appLabel oldModel newModel a\n"
    "  show implementation_renameContentType world db routerChoice appLabel oldModel newModel a = _\n"
    "  by_cases h : hasKey (world db) appLabel oldModel\n"
    "  · by_cases hc : renameConflicts (world db) appLabel oldModel newModel\n"
    "    · simp only [implementation_renameContentType, Id.run, h, hc,\n"
    "        Bool.not_true, Bool.false_eq_true, if_false, if_true]\n"
    "      rfl\n"
    "    · simp only [implementation_renameContentType, Id.run, h, hc,\n"
    "        Bool.not_true, Bool.false_eq_true, if_false, if_true]\n"
    "      rfl\n"
    "  · simp only [implementation_renameContentType, Id.run, h,\n"
    "      Bool.not_false, if_true, Bool.false_eq_true, if_false]\n"
    "    rfl\n"
)

# GUARD-ORDER RESHAPE (a SECOND correct positive, on a different axis than
# `pos-explicit-target-inlined`): test the collision guard FIRST and the
# located-record guard second. The two guards are independent tests of the SAME
# store `world db`, so swapping their order cannot change the value: whenever
# either fires the answer is `world`, and the rename runs exactly when neither
# does. The proof must now case-split BOTH guards in both orders (the frozen
# script splits the located-record guard outermost and never reaches a
# no-record-yet-conflicting branch), so this exercises a genuinely different
# proof shape rather than a re-spelling.
_POS_GUARD_SWAP = (
    "def implementation_renameContentType\n"
    "    (world : Alias → List ContentTypeRec)\n"
    "    (db routerChoice : Alias)\n"
    "    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do\n"
    "  if renameConflicts (world db) appLabel oldModel newModel then\n"
    "    return world\n"
    "  if !hasKey (world db) appLabel oldModel then\n"
    "    return world\n"
    "  return fun a =>\n"
    "    if a = db then renameInStore (world db) appLabel oldModel newModel\n"
    "    else world a\n"
)
_POS_GUARD_SWAP_PROOF = (
    "  intro world db routerChoice appLabel oldModel newModel a\n"
    "  show implementation_renameContentType world db routerChoice appLabel oldModel newModel a = _\n"
    "  by_cases h : hasKey (world db) appLabel oldModel\n"
    "  · by_cases hc : renameConflicts (world db) appLabel oldModel newModel\n"
    "    · simp only [implementation_renameContentType, Id.run, h, hc,\n"
    "        Bool.not_true, Bool.false_eq_true, if_false, if_true]\n"
    "      rfl\n"
    "    · simp only [implementation_renameContentType, Id.run, h, hc,\n"
    "        Bool.not_true, Bool.false_eq_true, if_false, if_true]\n"
    "      rfl\n"
    "  · by_cases hc : renameConflicts (world db) appLabel oldModel newModel\n"
    "    · simp only [implementation_renameContentType, Id.run, h, hc,\n"
    "        Bool.not_false, Bool.false_eq_true, if_false, if_true]\n"
    "      rfl\n"
    "    · simp only [implementation_renameContentType, Id.run, h, hc,\n"
    "        Bool.not_false, Bool.false_eq_true, if_false, if_true]\n"
    "      rfl\n"
)

# ---------------------------------------------------------------------------
# ADMISSIBILITY (non-vacuity of the obligation at an F2P-shaped input).
#
# The frozen obligation is an unconditional `∀ world db routerChoice …`, so
# there is no precondition binder to attack head-on. On a TOTAL carrier the
# analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
# exactly an F2P-shaped input — a spec that is provable in the abstract but
# contradictory at the one point the failing test observes. This case tests that
# directly: BEFORE closing the frozen obligation verbatim, it discharges
# `problem_spec_renameContentType` at the concrete F2P-shaped point
#
#     world  = the record (0,0) present on alias 0 and nowhere else
#     db     = 0        (the designated database the operation runs against)
#     routerChoice = 1  (the free routing choice, DELIBERATELY ≠ db — the
#                        sub-domain the F2P observable lives in)
#     appLabel/oldModel/newModel = 0/0/1
#
# as a `have`, BY EVALUATION: `decide` at the alias that must change, and the
# frame branch at every other alias. Only the tactic body grows — no new
# declaration, no axiom, no assumption token, and the theorem STATEMENT stays
# byte-identical, so `variant_scope` holds and the frozen obligation is still
# the thing being closed. If the `have` failed, the spec would be unsatisfiable
# at precisely the routed-write input, which no `expect="reject"` case can see.
_ADMISS_PROOF = (
    "  have hF2P : problem_spec_renameContentType\n"
    "      (fun a => if a = 0 then [⟨0,0⟩] else []) 0 1 0 0 1\n"
    "      (implementation_renameContentType\n"
    "        (fun a => if a = 0 then [⟨0,0⟩] else []) 0 1 0 0 1) := by\n"
    "    intro a\n"
    "    by_cases ha : a = 0\n"
    "    · subst ha\n"
    "      decide\n"
    "    · show (if a = 0 then renameInStore _ 0 0 1 else _) = _\n"
    "      simp [ha]\n"
) + _PROOF_BODY


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation, the spec is SPEC-TOO-STRONG. The theorem STATEMENT is
    # byte-identical; the tactic body is re-proved for the new shape (the frozen
    # `simp only [… saveTarget …]` names a symbol the reshape no longer uses).
    # No helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-explicit-target-inlined",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_DIRECT), _PROOF_BODY, _POS_DIRECT_PROOF),
        "rationale": (
            "a correct reshape that drops the destination-selection indirection "
            "and names the explicit target directly (`let target := db` instead "
            "of `saveTarget routerChoice (some db)`) computes the same world on "
            "every input: the explicit destination always resolves to db, so the "
            "collision check, the `a = db` selector, and `renameInStore` are "
            "unchanged. It MUST satisfy the frozen obligation; if it cannot the "
            "spec is SPEC-TOO-STRONG. Proof: the `saveTarget`-free shape needs a "
            "`simp only` set without that lemma, after which each branch closes "
            "by `rfl` — no new declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL #2 (soundness, a DIFFERENT axis) — the two independent
    # guards over the same store are order-insensitive, so testing the collision
    # guard first is an equally faithful correct impl. Added by audit: the
    # battery previously carried a single positive, whose reshape was confined to
    # the destination-selection expression, so the guard STRUCTURE was never
    # probed from the soundness side at all.
    # =====================================================================
    {
        "id": "pos-guard-order-swapped",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_GUARD_SWAP), _PROOF_BODY, _POS_GUARD_SWAP_PROOF),
        "rationale": (
            "a correct reshape on an axis the first positive leaves untouched: "
            "the collision guard and the located-record guard are independent "
            "predicates of the SAME store `world db`, so evaluating them in the "
            "opposite order computes the same world at every input — whenever "
            "either fires the result is `world`, and the rename runs exactly when "
            "neither fires. It MUST satisfy the frozen obligation; if it cannot, "
            "the spec is over-constraining the guard order and is SPEC-TOO-STRONG. "
            "Proof: the reshape reaches a branch the frozen script never does (no "
            "located record AND a collision), so both guards are case-split in "
            "both orders and each of the four branches closes by `rfl` — no new "
            "declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane) — the obligation is shown
    # SATISFIABLE at a concrete F2P-shaped input, by evaluation, before the
    # frozen obligation is closed verbatim. Added by audit: the battery shipped
    # with no admissibility case, so the third direction this gate tests was
    # missing. See `_ADMISS_PROOF` for why the analogue on a total carrier is
    # satisfiability at the F2P point rather than a precondition binder.
    # =====================================================================
    {
        "id": "admiss-ground-f2p-routed",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the frozen obligation is an unconditional `∀`, so the carrier has no "
            "precondition binder to attack; the analogue of PRECOND-TOO-STRONG "
            "here is the obligation being UNSATISFIABLE at exactly an F2P-shaped "
            "input. This case discharges `problem_spec_renameContentType` BY "
            "EVALUATION at that concrete point — the record `(0,0)` present on "
            "alias 0 alone, `db = 0`, and `routerChoice = 1` chosen DELIBERATELY "
            "different from `db` (the sub-domain where the free routing choice and "
            "the designated database disagree, which is where the discriminating "
            "observable lives) — as a `have` closed by `decide` at the alias that "
            "must change and by the frame branch at every other alias, and only "
            "then closes the frozen obligation verbatim. So the spec is shown "
            "consistent at the very input the reject lane refutes rivals at, not "
            "merely provable in the abstract. Must verify; if the `have` failed, "
            "every `expect=\"reject\"` case would be refuting rivals against a "
            "spec that is contradictory there, and no reject case can detect "
            "that. Nothing is assumed: no new declaration, no axiom, no "
            "assumption token, the theorem STATEMENT is byte-identical, and the "
            "frozen tactic body is retained unchanged as the closing step."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation witness
    # pinning the violation at one concrete input, instantiated at the alias
    # where the rival diverges.
    # =====================================================================
    {
        "id": "weak-route-to-router",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ROUTE_TO_ROUTER),
        "refinement": (
            "this IS the pre-fix behavior: the write is persisted without naming "
            "an explicit destination, so the persistence layer's free routing "
            "choice decides the target database. Its faithful real patch is the "
            "pre-patch code itself, which the F2P observable defeats: with the "
            "operation running against one database while the router directs "
            "writes to another, the rename lands on the router's database and the "
            "designated one is never updated — the renamed record is absent where "
            "the test asserts it is present. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the routing decision: the spec pins `result db = "
            "renameInStore (world db) …` (rename applied to db) independent of "
            "`routerChoice`. At `db = 0`, `routerChoice = 1` with the record "
            "present on db 0 and no collision, the spec demands db 0's store be "
            "renamed; the rival writes to alias 1 and leaves alias 0 = its input, "
            "so `result 0` is wrong. Refuted where `routerChoice ≠ db`, varying "
            "the free routing binder off the value at which route-to-router "
            "coincides with the fix — if it verified the spec would admit the "
            "prepatch bug => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted at alias db (=0): the record lives on db 0, the router\n"
            "-- would route the write to alias 1, but the rename must land on db 0.\n"
            "-- The rival leaves db 0 untouched (it wrote to alias 1).\n"
            "example :\n"
            "    ¬ problem_spec_renameContentType\n"
            "        (fun a => if a = 0 then [⟨0,0⟩] else []) 0 1 0 0 1\n"
            "        (implementation_renameContentType\n"
            "          (fun a => if a = 0 then [⟨0,0⟩] else []) 0 1 0 0 1) := by\n"
            "  unfold problem_spec_renameContentType\n"
            "  intro h\n"
            "  exact absurd (h 0) (by decide)\n"
        ),
    },
    {
        "id": "weak-drop-conflict-rollback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_CONFLICT),
        "refinement": (
            "omitting the unique-key collision check corresponds to persisting "
            "the rename with no rollback when the destination key already exists. "
            "Its faithful real patch would drop the atomic/IntegrityError guard, "
            "which the pre-existing conflict test defends: renaming to a "
            "model-name identity already present in the same database must leave "
            "every database untouched, and this rival instead mutates the store. "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the rollback clause: when a record keyed "
            "`(appLabel, newModel)` already lives in db and `newModel ≠ oldModel`, "
            "the spec demands `result a = world a` for every a (nothing "
            "persisted). At `db = 1` with db 1 holding both `(2,3)` and `(2,4)` "
            "and renaming `3 → 4`, the rename collides; the spec keeps db 1 as-is "
            "but the rival applies the rename. Refuted on the collision "
            "sub-domain, at `db = 1` and identities `2/3/4` distinct from the "
            "other witnesses — if it verified the spec would not enforce rollback "
            "=> SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted at alias db (=1): db 1 already holds the destination key\n"
            "-- (2,4), so renaming (2,3)→(2,4) collides and must roll back, leaving\n"
            "-- db 1 unchanged. The rival applies the rename anyway.\n"
            "example :\n"
            "    ¬ problem_spec_renameContentType\n"
            "        (fun a => if a = 1 then [⟨2,3⟩, ⟨2,4⟩] else []) 1 1 2 3 4\n"
            "        (implementation_renameContentType\n"
            "          (fun a => if a = 1 then [⟨2,3⟩, ⟨2,4⟩] else []) 1 1 2 3 4) := by\n"
            "  unfold problem_spec_renameContentType\n"
            "  intro h\n"
            "  exact absurd (h 1) (by decide)\n"
        ),
    },
    {
        "id": "weak-apply-every-database",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_APPLY_EVERYWHERE),
        "refinement": (
            "renaming in every database rather than only the one the operation "
            "runs against corresponds to persisting the rename globally instead "
            "of on the designated connection. Its faithful real patch would apply "
            "the update across databases, changing rows the operation must leave "
            "untouched — a write to databases the migration was never directed "
            "at. It does NOT resolve (and would corrupt sibling databases sharing "
            "the same natural key)."
        ),
        "rationale": (
            "REJECT from the outer frame clause: for `a ≠ db` the spec demands "
            "`result a = world a` (every other database identical to its input). "
            "With `world` constant `[⟨0,0⟩]` across aliases, `db = 0`, and the "
            "rename `0 → 1` applied everywhere, the spec keeps alias 1 as "
            "`[⟨0,0⟩]` but the rival renames it to `[⟨0,1⟩]`. Refuted by "
            "instantiating the alias binder at `a = 1 ≠ db`, exercising the "
            "`a = db` split on its OTHER side — if it verified the spec would not "
            "confine the write to db => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted at an alias other than db (a = 1): every database holds\n"
            "-- (0,0); only db 0 may be renamed, so alias 1 must stay (0,0). The\n"
            "-- rival renames alias 1 too.\n"
            "example :\n"
            "    ¬ problem_spec_renameContentType\n"
            "        (fun _ => [⟨0,0⟩]) 0 0 0 0 1\n"
            "        (implementation_renameContentType\n"
            "          (fun _ => [⟨0,0⟩]) 0 0 0 0 1) := by\n"
            "  unfold problem_spec_renameContentType\n"
            "  intro h\n"
            "  exact absurd (h 1) (by decide)\n"
        ),
    },
    {
        "id": "weak-rename-whole-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RENAME_WHOLE_STORE),
        "refinement": (
            "setting every record's model-name identity in the target store, "
            "rather than only the located record's, corresponds to a bulk update "
            "instead of the single-row save the operation performs. Its faithful "
            "real patch would overwrite unrelated rows in the same database, "
            "changing content types the rename never named. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the inner frame clause: `renameInStore` changes only the "
            "record matching `(appLabel, oldModel)` and leaves all others exactly "
            "as they were. With db 0 holding a matching `(0,0)` and a non-matching "
            "`(5,5)`, renaming `0 → 1`, the spec keeps `(5,5)` intact while the "
            "rival rewrites it to `(5,1)`. Refuted where the target store contains "
            "a non-matching record — the sub-domain that pins per-record framing "
            "— so a rival that mishandles the within-store frame is caught => "
            "else SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted at alias db (=0): db 0 holds a matching (0,0) and a\n"
            "-- non-matching (5,5); only the matching record is renamed, so (5,5)\n"
            "-- must survive. The rival overwrites every record's model.\n"
            "example :\n"
            "    ¬ problem_spec_renameContentType\n"
            "        (fun a => if a = 0 then [⟨0,0⟩, ⟨5,5⟩] else []) 0 0 0 0 1\n"
            "        (implementation_renameContentType\n"
            "          (fun a => if a = 0 then [⟨0,0⟩, ⟨5,5⟩] else []) 0 0 0 0 1) := by\n"
            "  unfold problem_spec_renameContentType\n"
            "  intro h\n"
            "  exact absurd (h 0) (by decide)\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the routing decision and the
# record update are modeled directly over the data, so there is no in-model
# axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
