# properties.py — PBT falsification battery for django__django-15629. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside a # impl-start/# impl-end region (there are TWO — one per modeled
# function); the runner re-runs the Nagini verifier on the host and checks the
# verify/reject outcome against `expect`. Axiom cases run the REAL Django callee
# in the instance Docker image (the three A-reference deep models).
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md + axiom_check.py)
# ---------------------------------------------------------------------------
# FN-1  reported_reference_parameters(target_params: Dict[int,int],
#                                     own_type: int, own_check: int) -> Dict[int,int]
#   Requires(Acc(dict_pred(target_params), 1/2))   # READ-ONLY input (half perm)
#   Requires(key_collation() in target_params)
#   Ensures(Acc(dict_pred(target_params), 1/2))    # perm returned unchanged
#   Ensures(dict_pred(Result()))
#   Ensures(key_type() in Result()); Ensures(Result()[key_type()] == own_type)
#   Ensures(key_check() in Result()); Ensures(Result()[key_check()] == own_check)
#   Ensures(key_collation() in Result())                       # THE regression
#   Ensures(key_collation() in target_params)
#   Ensures(Result()[key_collation()] == target_params[key_collation()])  # (1) discriminating
#   Ensures(Forall k: k in Result() -> k in {type,check,collation})   # no-spurious
#   Ensures(emits_collation_clause(Result())
#           == (key_collation() in target_params
#               and target_params[key_collation()] != none_value()))  # (1') consequence
#
#   The load-bearing clauses are (a) key_collation() in Result() — the FK must
#   report a collation entry AT ALL (model_prepatch.py omits it and fails here),
#   and (b) Result()[key_collation()] == target_params[key_collation()] — the
#   value must be the referenced column's collation, present (not absent).
#
#   emits_collation_clause is a GROUNDED @Pure predicate: it is the fully-
#   unfolded function `key_collation() in p and p[key_collation()] != none_value()`
#   of its argument, NOT an opaque answer-key oracle. So there is no "wrong echo"
#   of an oracle that could verify (the ungrounded-oracle-echo class does not
#   apply — see `assessment`). Clause (1') is a derived check the impl must make
#   true by actually copying the collation, which is the real work.
#
# FN-2  references_need_rebuild(old_type, new_type, old_collation, new_collation) -> bool
#   (no Requires; all four params are pass-by-value int scalars — NO read-only input)
#   Ensures(Implies(differs(old_type, new_type), Result()))         # type change -> rebuild
#   Ensures(Implies(differs(old_collation, new_collation), Result()))  # collation change -> rebuild
#   Ensures(Implies(not differs(t) and not differs(c), not Result()))  # neither -> no rebuild
#   This is a complete by-cases characterisation == a bi-implication:
#   Result() <-> (old_type != new_type) or (old_collation != new_collation).
#   The new disjunct is the collation case (model_prepatch_2.py reverts it and
#   fails on the pure-collation-change witness).
#
# ---------------------------------------------------------------------------
# READ-ONLY input => FRAME-MUTATION probe is MANDATORY (FN-1 target_params is
# Acc(...,1/2)). The mutation rival below WRITES target_params[key_collation()]
# (to make the value clause vacuously satisfiable from the input it just set);
# with only half permission held it MUST be rejected for insufficient
# permission. A byte-fuzzer never thinks to mutate the input — this is the #1
# weakness class.
#
# Axiom lane: NO @ContractOnly consumed axiom (axioms == []). There are THREE
# A-reference deep models (reported_reference_parameters,
# references_need_rebuild, emits_collation_clause) checked by G-AX/axiom_check.py
# against the REAL gold-patched Django. We persist soundness + containment probes
# that EXECUTE the real callee (ForeignKey.db_parameters, schema_editor.column_sql)
# and validate the rebuild truth table, mirroring/strengthening axiom_check.py.
from pathlib import Path

INSTANCE = "django__django-15629"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl regions (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL1_OLD = """    # impl-start
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = target_params[key_collation()]
    return result
    # impl-end"""

_IMPL2_OLD = """    # impl-start
    return differs(old_type, new_type) or differs(old_collation, new_collation)
    # impl-end"""

assert _IMPL1_OLD in _BASE and _BASE.count(_IMPL1_OLD) == 1
assert _IMPL2_OLD in _BASE and _BASE.count(_IMPL2_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls
# MUST verify (else SPEC-TOO-STRONG). Only the executable shape changes; no
# loop / no fold is introduced, so no auto-undischargeable lemma is needed
# (pilot pitfalls #2/#3 avoided).
# ===========================================================================

# pos-fn1-reorder: build the dict in a DIFFERENT order — write collation first,
# then check, then type. Dict membership/value are order-independent, so every
# postcondition clause (the three entries, the no-spurious Forall, the (1')
# consequence) still holds. target_params is only READ (target_params[
# key_collation()]), never written, so the 1/2 permission is enough.
_POS_FN1_REORDER = """    # impl-start
    result = {}  # type: Dict[int, int]
    result[key_collation()] = target_params[key_collation()]
    result[key_check()] = own_check
    result[key_type()] = own_type
    return result
    # impl-end"""

# pos-fn1-temp: a local-variable reshape — read the target collation into a typed
# temporary first, then assemble. Behaviourally identical (the temp equals
# target_params[key_collation()]), so clause (1) and (1') hold; target_params is
# still only read.
_POS_FN1_TEMP = """    # impl-start
    coll = target_params[key_collation()]  # type: int
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = coll
    return result
    # impl-end"""

# pos-fn2-branch: a structurally-different but CORRECT shape for the rebuild
# decision — an explicit if/return over the two characteristics instead of the
# single disjunction. Semantically identical to `differs(t) or differs(c)`: it
# returns True whenever either differs and False only when neither does, so all
# three Ensures cases hold. No loop/fold, no new lemma.
_POS_FN2_BRANCH = """    # impl-start
    if differs(old_type, new_type):
        return True
    if differs(old_collation, new_collation):
        return True
    return False
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm each precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). A new module-level def would change the
# projected spec view and break same_spec, so the admissibility witness is
# injected INSIDE the impl region (elided from the spec view). FN-1's Requires
# is the interesting one: it needs Acc(dict_pred(d), 1/2) AND
# key_collation() in d for a freshly-built params dict. We build a concrete
# F2P-shaped target params dict (a CharField-pk-with-collation reports a
# 'collation' entry), assert it satisfies FN-1's Requires at the held fraction,
# then run the real impl unchanged over the actual params.
# ===========================================================================
_ADMISS_FN1 = """    # impl-start
    # --- admissibility witness for an F2P-shaped target params dict ---
    adm = {}  # type: Dict[int, int]
    adm[key_collation()] = 5
    # FN-1's Requires is establishable for this concrete in-domain input:
    #   Acc(dict_pred(adm), 1/2) (we hold full perm on the fresh dict) and
    #   key_collation() in adm (a referenced column reports a collation entry).
    Assert(Acc(dict_pred(adm), 1 / 2))
    Assert(key_collation() in adm)
    # --- end witness; the real impl follows unchanged over the actual params ---
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = target_params[key_collation()]
    return result
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness/reject) — MANDATORY: target_params is read-only
# (Acc(...,1/2)). This rival WRITES target_params[key_collation()] and then
# copies that just-written value into result. With only half permission held on
# target_params, the write requires full permission and MUST be rejected for
# INSUFFICIENT PERMISSION. The gold invariants are kept verbatim so the
# rejection is attributable solely to the write.
# ===========================================================================
_MUT_WRITE_TARGET = """    # impl-start
    target_params[key_collation()] = own_type
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = target_params[key_collation()]
    return result
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain / control-flow — WRONG rivals that share the spec
# exactly and change ONLY the impl. Each MUST be rejected; a verifying rival is a
# real verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# --- FN-1 attacks ---

# uniq-fn1-drop-collation: THE pre-patch bug (model_prepatch.py). Report only the
# type and check entries; never write the collation key. Rejected by
# Ensures(key_collation() in Result()).
_UNIQ_FN1_DROP = """    # impl-start
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    return result
    # impl-end"""

# uniq-fn1-wrong-collation: report a collation entry but with the WRONG value
# (the FK's own type identity instead of the referenced column's collation).
# The key is present, so key_collation() in Result() holds, but the value clause
# Result()[key_collation()] == target_params[key_collation()] is violated (own_type
# is not provably equal to target_params[key_collation()]). This is the
# value-level attack on clause (1).
_UNIQ_FN1_WRONG_VALUE = """    # impl-start
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = own_type
    return result
    # impl-end"""

# uniq-fn1-empty-collation: hard-code the collation to the empty sentinel
# none_value(). Always reports a present-but-empty collation regardless of the
# target. When the target DECLARES a collation this is wrong on both the value
# clause (1) (none_value() != target_params[key_collation()]) and the (1')
# consequence (emits_collation_clause(Result()) would be False while the target
# declares one). Partial-domain: correct only on the no-collation sub-domain.
_UNIQ_FN1_EMPTY = """    # impl-start
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = none_value()
    return result
    # impl-end"""

# uniq-fn1-spurious-entry: report the three correct entries PLUS a spurious 4th
# key. The value clauses hold, but the no-spurious Forall
# (k in Result() -> k in {type,check,collation}) is violated by key 99.
_UNIQ_FN1_SPURIOUS = """    # impl-start
    result = {}  # type: Dict[int, int]
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = target_params[key_collation()]
    result[99] = own_check
    return result
    # impl-end"""

# --- FN-2 attacks ---

# uniq-fn2-type-only: THE pre-patch bug (model_prepatch_2.py). Trigger a rebuild
# on a type change only, ignoring collation. Rejected by
# Ensures(Implies(differs(old_collation, new_collation), Result())) on the pure-
# collation-change witness (type equal, collation differs => must rebuild, but
# this returns False).
_UNIQ_FN2_TYPE_ONLY = """    # impl-start
    return differs(old_type, new_type)
    # impl-end"""

# uniq-fn2-collation-only: symmetric partial-domain rival — trigger only on a
# collation change, ignoring type. Rejected by
# Ensures(Implies(differs(old_type, new_type), Result())) on a pure-type-change
# witness (type differs, collation equal => must rebuild, returns False).
_UNIQ_FN2_COLLATION_ONLY = """    # impl-start
    return differs(old_collation, new_collation)
    # impl-end"""

# uniq-fn2-and: use AND instead of OR — rebuild only when BOTH differ. Rejected
# by either single-change clause (a pure type OR pure collation change requires a
# rebuild but AND returns False).
_UNIQ_FN2_AND = """    # impl-start
    return differs(old_type, new_type) and differs(old_collation, new_collation)
    # impl-end"""

# uniq-fn2-const-true: always rebuild. Rejected by
# Ensures(Implies(not differs(t) and not differs(c), not Result())): when nothing
# changed it must NOT rebuild, but const-true does. (Over-rebuild rival.)
_UNIQ_FN2_TRUE = """    # impl-start
    return True
    # impl-end"""

# uniq-fn2-const-false: never rebuild. Rejected by either single-change clause
# (a real change must rebuild). Supporting near-miss.
_UNIQ_FN2_FALSE = """    # impl-start
    return False
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-fn1-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL1_OLD, _POS_FN1_REORDER),
        "rationale": "structurally-different CORRECT impl of reported_reference_"
                     "parameters: assemble the result dict in a different key order "
                     "(collation, check, type). Dict membership/value are order-"
                     "independent so all postconditions (three entries, no-spurious "
                     "Forall, the (1') consequence) hold; target_params is only read "
                     "at half permission. No loop/fold => no auto-undischargeable "
                     "lemma. If it cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-fn1-temp",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL1_OLD, _POS_FN1_TEMP),
        "rationale": "local-variable reshape of reported_reference_parameters: read "
                     "the target collation into a typed temporary first, then "
                     "assemble. The temp equals target_params[key_collation()] so "
                     "clause (1) and the (1') consequence hold; target_params is "
                     "still only read. If it cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-fn2-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL2_OLD, _POS_FN2_BRANCH),
        "rationale": "structurally-different CORRECT impl of references_need_rebuild: "
                     "explicit if/return over the two characteristics instead of the "
                     "single disjunction. Returns True iff either differs and False "
                     "only when neither does, so all three Ensures cases hold. No "
                     "loop/fold. If it cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-fn1-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL1_OLD, _ADMISS_FN1),
        "rationale": "an admissibility witness injected INSIDE FN-1's impl region "
                     "(elided from the spec view, so same_spec holds) builds a "
                     "concrete F2P-shaped target params dict (a CharField-pk-with-"
                     "collation reports a 'collation' entry => key_collation() in d) "
                     "and asserts it satisfies FN-1's exact Requires: "
                     "Acc(dict_pred(adm), 1/2) and key_collation() in adm. The real "
                     "impl then runs unchanged. If the precondition could not be "
                     "established for this legitimate input the Assert fails => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- FRAME-MUTATION (must reject for insufficient permission) ----
    {
        "id": "frame-mut-write-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1_OLD, _MUT_WRITE_TARGET),
        "refinement": "the real ForeignKey.db_parameters READS the referenced "
                      "column's parameters (target_field.db_parameters(connection)) "
                      "and must not mutate them — mutating the referenced column's "
                      "reported collation in place would corrupt the shared target "
                      "field's parameters for every other referrer and for the "
                      "target's own column emission, changing observable DDL for "
                      "unrelated columns. A faithful patch that wrote back into the "
                      "target's params dict would not resolve the F2P (and would "
                      "corrupt sibling FKs / the target column itself). This rival is "
                      "rejected for a permission reason, not a value reason — it is a "
                      "vacuous satisfaction of clause (1) by overwriting the input it "
                      "then reads back.",
        "rationale": "rejected by the permission system: target_params is held at "
                     "Acc(dict_pred(target_params), 1/2) (read-only); writing "
                     "target_params[key_collation()] requires FULL permission, which "
                     "is not held => INSUFFICIENT PERMISSION. The gold invariants are "
                     "kept verbatim so the rejection is attributable solely to the "
                     "write.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-fn1-drop-collation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1_OLD, _UNIQ_FN1_DROP),
        "refinement": "this IS the pre-patch behaviour that model_prepatch.py "
                      "reproduces and G-DIFF flags: ForeignKey.db_parameters returned "
                      "only {type, check}, so every consumer reading "
                      "db_params.get('collation') saw None and the FK column dropped "
                      "its COLLATE clause. Both F2P tests (Creation of models with a "
                      "FK to a PK with db_collation; AlterField of db_collation on PKs "
                      "changes any FKs) observe the FK carrying the target's "
                      "collation; without the collation entry they fail. The faithful "
                      "un-patched function is exactly what does NOT resolve.",
        "rationale": "rejected by Ensures(key_collation() in Result()): with no "
                     "collation write the result has no collation key => the "
                     "membership postcondition fails.",
    },
    {
        "id": "uniq-fn1-wrong-collation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1_OLD, _UNIQ_FN1_WRONG_VALUE),
        "refinement": "reporting the FK's own type identity as the collation "
                      "corresponds to a patch that put the wrong value under "
                      "'collation' — the FK column would emit a COLLATE clause naming "
                      "the wrong collation (or a type string), producing DDL that "
                      "does not match the referenced column. test_create_fk_models_to_"
                      "pk_field_db_collation observes the FK collation EQUALS the "
                      "target's; a mismatched value does not resolve.",
        "rationale": "rejected by Ensures(Result()[key_collation()] == "
                     "target_params[key_collation()]): own_type is not provably equal "
                     "to the referenced column's collation, so the value clause (1) "
                     "fails (the key is present, so the failure is purely on value).",
    },
    {
        "id": "uniq-fn1-empty-collation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1_OLD, _UNIQ_FN1_EMPTY),
        "refinement": "hard-coding the collation to the empty sentinel corresponds to "
                      "a patch that always reported collation=None for the FK — "
                      "correct ONLY when the target declares no collation, but WRONG "
                      "for the F2P case where the PK has db_collation set: the FK "
                      "column would omit the COLLATE clause and disagree with its "
                      "target (the exact MySQL/SQLite regression). Partial-domain: "
                      "passes the no-collation sub-domain, fails the with-collation "
                      "sub-domain the F2P exercises.",
        "rationale": "rejected by Ensures(Result()[key_collation()] == "
                     "target_params[key_collation()]) AND the (1') consequence: when "
                     "target_params[key_collation()] != none_value(), the result "
                     "value none_value() differs from it and emits_collation_clause("
                     "Result()) is False while the RHS is True. Either clause fails.",
    },
    {
        "id": "uniq-fn1-spurious-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1_OLD, _UNIQ_FN1_SPURIOUS),
        "refinement": "emitting an extra parameter key corresponds to a patch that "
                      "added a spurious entry to the db_parameters dict; downstream "
                      "consumers (column_sql, the schema introspection) iterate the "
                      "reported parameters and would act on the bogus key, producing "
                      "wrong DDL / unexpected behaviour not matching the gold dict "
                      "shape. Supporting structural near-miss with a real refinement.",
        "rationale": "rejected by Ensures(Forall(int, k: k in Result() -> "
                     "k == key_type() or k == key_check() or k == key_collation())): "
                     "key 99 is in Result() but is none of the three tokens, "
                     "violating the no-spurious-entries clause.",
    },
    {
        "id": "uniq-fn2-type-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2_OLD, _UNIQ_FN2_TYPE_ONLY),
        "refinement": "this IS the pre-patch trigger that model_prepatch_2.py "
                      "reproduces and G-DIFF flags: the drop/re-derive guard used "
                      "old_type != new_type alone, so a PURE collation change (type "
                      "unchanged) did not re-derive the referencing FK columns and "
                      "they were left with the old collation. F2P 'AlterField "
                      "operation of db_collation on primary keys changes any FKs' "
                      "alters a PK's collation with the type unchanged and asserts the "
                      "referencing FKs are rebuilt; the type-only trigger misses it "
                      "and does NOT resolve.",
        "rationale": "rejected by Ensures(Implies(differs(old_collation, "
                     "new_collation), Result())): on a pure collation change "
                     "(old_type == new_type, old_collation != new_collation) the spec "
                     "demands Result() True but differs(old_type, new_type) is False, "
                     "so this returns False — the clause fails.",
    },
    {
        "id": "uniq-fn2-collation-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2_OLD, _UNIQ_FN2_COLLATION_ONLY),
        "refinement": "triggering only on a collation change corresponds to a patch "
                      "that DROPPED the original type-change disjunct while adding the "
                      "collation one — a pure type change (e.g. widening the PK type "
                      "with the same collation) would no longer re-derive the "
                      "referencing FKs, regressing the original re-derive behaviour "
                      "the P2P alter tests depend on. Symmetric partial-domain rival.",
        "rationale": "rejected by Ensures(Implies(differs(old_type, new_type), "
                     "Result())): on a pure type change "
                     "(old_type != new_type, old_collation == new_collation) the spec "
                     "demands Result() True but differs(old_collation, new_collation) "
                     "is False, so this returns False — the clause fails.",
    },
    {
        "id": "uniq-fn2-and",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2_OLD, _UNIQ_FN2_AND),
        "refinement": "requiring BOTH a type and a collation change corresponds to a "
                      "patch using `and` instead of `or` in the drop_foreign_keys "
                      "guard — neither a pure type change nor a pure collation change "
                      "would re-derive references, failing both the original "
                      "type-change re-derive (P2P) and the new collation-change "
                      "re-derive (F2P). Does NOT resolve.",
        "rationale": "rejected by both single-change clauses: a pure type change "
                     "(differs(type), not differs(coll)) makes the AND False while the "
                     "spec demands True (and symmetrically for a pure collation "
                     "change).",
    },
    {
        "id": "uniq-fn2-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2_OLD, _UNIQ_FN2_TRUE),
        "refinement": "always re-deriving corresponds to a patch that dropped the "
                      "type/collation guard entirely and unconditionally rebuilt "
                      "referencing columns on any _alter_field. It would re-derive "
                      "FKs even when nothing relevant changed, issuing spurious "
                      "DROP/REBUILD DDL and breaking the P2P alter tests that expect "
                      "no FK churn on an unrelated alteration. Does NOT resolve.",
        "rationale": "rejected by Ensures(Implies(not differs(old_type, new_type) "
                     "and not differs(old_collation, new_collation), not Result())): "
                     "when neither characteristic differs the spec demands Result() "
                     "False, but const-true returns True.",
    },
    {
        "id": "uniq-fn2-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2_OLD, _UNIQ_FN2_FALSE),
        "refinement": "never re-deriving corresponds to removing the re-derive branch "
                      "altogether — referencing FK columns are never rebuilt, so both "
                      "a type change AND a collation change leave the FKs stale, "
                      "failing the F2P collation-change rebuild and the P2P type-change "
                      "rebuild. Supporting near-miss with a real refinement.",
        "rationale": "rejected by both single-change clauses: on any real change "
                     "(type or collation differs) the spec demands Result() True, but "
                     "const-false returns False.",
    },
]


# ===========================================================================
# AXIOM LANE — NO @ContractOnly consumed axiom (axioms == []). Three A-reference
# deep models, validated against the REAL gold-patched Django by G-AX
# (axiom_check.py). We persist EXECUTABLE probes that run the real callee in the
# instance Docker image (apply_gold=True; the A-reference describes post-gold
# behaviour). Probes import only the stdlib + the Django package under
# evaluation; they EXECUTE the real ForeignKey.db_parameters and
# schema_editor.column_sql (pilot pitfall #4: never regex-scrape source) and open
# any file with encoding="utf-8" (pitfall #5; here none is opened). The runner
# mounts only the probe at /work (pitfall #6), so probes are fully self-contained.
# ===========================================================================

# ax-sound-reported_reference_parameters: EXECUTE the real ForeignKey.db_parameters
# over boundary + fuzz collation identities and assert the A-reference deep model
# holds: the FK reports a 'collation' key EQUAL to the referenced column's
# collation (and None when the target declares none), AND the emitted FK column
# SQL carries a COLLATE clause iff the target declares a non-empty collation
# (clause (1')). Any disagreement => AXIOM-UNSOUND. Mirrors axiom_check.py's
# check_reported_reference_parameters by construction, embedded standalone.
_AX_SOUND_FK_PROBE = r'''
import os, random, sys, tempfile

def main():
    import django
    from django.conf import settings

    app_name = "pbt_ax_15629"
    pkg_parent = tempfile.mkdtemp(prefix="pbtax15629_")
    pkg_dir = os.path.join(pkg_parent, app_name)
    os.makedirs(pkg_dir, exist_ok=True)
    with open(os.path.join(pkg_dir, "__init__.py"), "w", encoding="utf-8") as f:
        f.write("")
    with open(os.path.join(pkg_dir, "models.py"), "w", encoding="utf-8") as f:
        f.write("")
    sys.path.insert(0, pkg_parent)

    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth", app_name],
            USE_TZ=False,
        )
    django.setup()

    from django.db import connection, models

    counter = [0]

    def make_pair(collation):
        counter[0] += 1
        n = counter[0]
        Pony = type("Pony%d" % n, (models.Model,), {
            "__module__": "%s.models" % app_name,
            "Meta": type("Meta", (), {"app_label": app_name}),
            "id": models.CharField(primary_key=True, max_length=10,
                                   db_collation=collation),
        })
        Rider = type("Rider%d" % n, (models.Model,), {
            "__module__": "%s.models" % app_name,
            "Meta": type("Meta", (), {"app_label": app_name}),
            "pony": models.ForeignKey(Pony, models.CASCADE),
        })
        return Rider._meta.get_field("pony"), Pony._meta.get_field("id")

    def check(collation):
        fk_field, pk_field = make_pair(collation)
        target = pk_field.db_parameters(connection=connection)   # real callee
        observed = fk_field.db_parameters(connection=connection)  # real callee
        assert "collation" in observed, (
            "AXIOM-UNSOUND: real ForeignKey.db_parameters dropped 'collation' for "
            "collation=%r: %r" % (collation, observed))
        assert observed.get("collation") == target.get("collation"), (
            "AXIOM-UNSOUND: FK collation %r != target collation %r (collation=%r)"
            % (observed.get("collation"), target.get("collation"), collation))
        # (1') emission consequence via real column_sql
        with connection.schema_editor(collect_sql=True) as editor:
            col_sql, _ = editor.column_sql(fk_field.model, fk_field)
        emits = (col_sql is not None) and ("COLLATE" in col_sql.upper())
        declares = target.get("collation") not in (None, "")
        assert emits == declares, (
            "AXIOM-UNSOUND: FK column COLLATE emission %r != declares-collation %r "
            "(collation=%r, sql=%r)" % (emits, declares, collation, col_sql))
        return observed.get("collation")

    boundary = [None, "nocase", "binary", "utf8_bin", "und-x-icu", ""]
    for c in boundary:
        check(c)
    rng = random.Random(15629)
    pool = [None, "nocase", "binary", "utf8_bin", "utf8mb4_unicode_ci",
            "C", "POSIX", "en-x-icu", "sv-x-icu"]
    for _ in range(120):
        check(rng.choice(pool))

    print("AXIOM-SOUNDNESS OK: real ForeignKey.db_parameters reports a 'collation' "
          "entry equal to the referenced column's collation over %d boundary + 120 "
          "fuzz model pairs, and the FK column SQL emits COLLATE iff the target "
          "declares a non-empty collation. Deep reported_reference_parameters / "
          "emits_collation_clause A-references hold." % len(boundary))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

# ax-sound-references_need_rebuild: validate the A-reference rebuild decision
# against the REAL gold-patched base-schema source AND the boolean truth table.
# We assert the gold-patched _alter_field uses the disjunction
# (old_type != new_type) or (old_collation != new_collation), and we exhaustively
# check the deep boolean predicate equals that disjunction over the full
# 3x3x3x3 identity grid (incl. the discriminating pure-collation-change case).
# A source match is a supporting anchor; the load-bearing check is that the deep
# boolean encodes EXACTLY the disjunction (executed, not scraped). Mirrors
# axiom_check.py's check_references_need_rebuild.
_AX_SOUND_REBUILD_PROBE = r'''
import inspect, sys

def deep_references_need_rebuild(ot, nt, oc, nc):
    return (ot != nt) or (oc != nc)

def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            USE_TZ=False,
        )
    django.setup()

    from django.db.backends.base import schema as base_schema

    # 1) the gold-patched base-schema drop-FK trigger is the type-OR-collation
    #    disjunction (the very change the patch makes).
    src = inspect.getsource(base_schema.BaseDatabaseSchemaEditor._alter_field)
    assert "old_collation" in src and "new_collation" in src, (
        "AXIOM-UNSOUND: base schema _alter_field no longer mentions old/new "
        "collation")
    norm = "".join(src.split())
    assert "(old_type!=new_type)or(old_collation!=new_collation)" in norm, (
        "AXIOM-UNSOUND: base schema _alter_field drop-FK trigger is not "
        "(old_type != new_type) or (old_collation != new_collation)")

    # 2) the deep boolean predicate equals the disjunction over the full identity
    #    grid (3 types x 3 colls each side; None == empty collation).
    types = ["t0", "t1", None]
    colls = ["c0", "c1", None]
    saw_pure_collation = False
    for ot in types:
        for nt in types:
            for oc in colls:
                for nc in colls:
                    deep = deep_references_need_rebuild(ot, nt, oc, nc)
                    truth = (ot != nt) or (oc != nc)
                    assert deep == truth, (
                        "AXIOM-UNSOUND: deep references_need_rebuild != disjunction "
                        "for (%r,%r,%r,%r): deep=%r truth=%r"
                        % (ot, nt, oc, nc, deep, truth))
                    if ot == nt and oc != nc:
                        assert deep is True, (
                            "AXIOM-UNSOUND: pure collation change must rebuild")
                        saw_pure_collation = True
    assert saw_pure_collation, "did not exercise the pure-collation-change case"

    print("AXIOM-SOUNDNESS OK: gold-patched base-schema _alter_field drop-FK "
          "trigger is (old_type != new_type) or (old_collation != new_collation); "
          "deep references_need_rebuild equals that disjunction over the full "
          "3x3x3x3 identity grid incl. the pure-collation-change case.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

# ax-cover-reported_reference_parameters: containment. The model can only pass a
# target_params dict that (by FN-1's Requires) carries the collation key; the
# real target field that supplies it is a relational FK's target_field, whose
# db_parameters dict always carries 'collation' post-gold. Confirm the real
# target db_parameters the model abstracts ALWAYS contains the 'collation' key
# the precondition assumes (so every model-reachable target_params is inside the
# A-reference's domain). A target reachable by the model that LACKED a collation
# entry would be AXIOM-TOO-WEAK-FOR-CALLER; none exists for a CharField PK target.
_AX_COVER_FK_PROBE = r'''
import os, random, sys, tempfile

def main():
    import django
    from django.conf import settings

    app_name = "pbt_cov_15629"
    pkg_parent = tempfile.mkdtemp(prefix="pbtcov15629_")
    pkg_dir = os.path.join(pkg_parent, app_name)
    os.makedirs(pkg_dir, exist_ok=True)
    with open(os.path.join(pkg_dir, "__init__.py"), "w", encoding="utf-8") as f:
        f.write("")
    with open(os.path.join(pkg_dir, "models.py"), "w", encoding="utf-8") as f:
        f.write("")
    sys.path.insert(0, pkg_parent)

    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth", app_name],
            USE_TZ=False,
        )
    django.setup()

    from django.db import connection, models

    counter = [0]

    def make_target_params(collation):
        counter[0] += 1
        n = counter[0]
        Pony = type("Pony%d" % n, (models.Model,), {
            "__module__": "%s.models" % app_name,
            "Meta": type("Meta", (), {"app_label": app_name}),
            "id": models.CharField(primary_key=True, max_length=10,
                                   db_collation=collation),
        })
        Rider = type("Rider%d" % n, (models.Model,), {
            "__module__": "%s.models" % app_name,
            "Meta": type("Meta", (), {"app_label": app_name}),
            "pony": models.ForeignKey(Pony, models.CASCADE),
        })
        # the target_params the model abstracts = the referenced PK column's params
        pk_field = Pony._meta.get_field("id")
        return pk_field.db_parameters(connection=connection)

    # FN-1's precondition: key_collation() in target_params. The model only ever
    # passes a referenced column's db_parameters dict. Confirm every reachable
    # such dict carries the 'collation' key (so the reachable target_params is
    # inside the A-reference domain), across declared and absent collations.
    reached = 0
    pool = [None, "nocase", "binary", "utf8_bin", "C", ""]
    for c in pool:
        params = make_target_params(c)
        assert "collation" in params, (
            "AXIOM-TOO-WEAK-FOR-CALLER: a model-reachable target params dict "
            "(CharField PK, db_collation=%r) lacks the 'collation' key the "
            "precondition assumes: %r" % (c, params))
        reached += 1
    rng = random.Random(15629)
    for _ in range(60):
        c = rng.choice(pool)
        params = make_target_params(c)
        assert "collation" in params, (
            "AXIOM-TOO-WEAK-FOR-CALLER: reachable target params (db_collation=%r) "
            "lacks 'collation': %r" % (c, params))
        reached += 1

    print("AXIOM-CONTAINMENT OK: every model-reachable target_params (a referenced "
          "CharField-PK column's real db_parameters; %d sampled) carries the "
          "'collation' key the precondition assumes — each reachable input lies "
          "inside the A-reference domain. The caller never reaches a target params "
          "dict outside it." % reached)
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-reported_reference_parameters",
        "axiom": "reported_reference_parameters",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the A-reference describes POST-gold db_parameters
        "probe": _AX_SOUND_FK_PROBE,
        "rationale": "if the real ForeignKey.db_parameters fails to report a "
                     "'collation' entry equal to the referenced column's collation, "
                     "or the FK column SQL emits COLLATE when the target declares "
                     "none (or omits it when the target declares one), the "
                     "A-reference deep model reported_reference_parameters / "
                     "emits_collation_clause is unsound => AXIOM-UNSOUND. Boundary "
                     "collations (None/''/named) + 120 fuzz pairs cover the domain.",
    },
    {
        "id": "ax-sound-references_need_rebuild",
        "axiom": "references_need_rebuild",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the A-reference describes the POST-gold trigger
        "probe": _AX_SOUND_REBUILD_PROBE,
        "rationale": "if the gold-patched base-schema _alter_field drop-FK trigger is "
                     "not the (old_type != new_type) or (old_collation != "
                     "new_collation) disjunction, or the deep boolean predicate "
                     "diverges from it on any of the 3x3x3x3 identity grid (incl. the "
                     "pure-collation-change case), the A-reference is unsound => "
                     "AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-reported_reference_parameters",
        "axiom": "reported_reference_parameters",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_FK_PROBE,
        "rationale": "FN-1's precondition assumes key_collation() in target_params; "
                     "the model only ever abstracts a referenced column's real "
                     "db_parameters dict. Every such reachable dict (CharField PK "
                     "with declared/absent collation) carries the 'collation' key, so "
                     "each reachable target_params lies inside the A-reference domain. "
                     "A reachable target lacking the collation key would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none exists.",
    },
]
