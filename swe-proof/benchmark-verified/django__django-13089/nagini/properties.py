# properties.py — PBT falsification battery for django__django-13089.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py source whose SPEC (axioms/pure/pre/post-
# conditions/signatures) is byte-identical to the frozen model.py — only text
# INSIDE the single `# impl-start`/`# impl-end` region is changed — checked by
# markers.same_spec. Spec cases are checked by Nagini verify on the host.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py + refinement.md + mapping.md + meta.json)
# ---------------------------------------------------------------------------
# ONE modeled function:
#   boundary_for_prune(row: Optional[List[int]]) -> Optional[int]
#     Models DatabaseCache._cull's prune-boundary decision: the gold patch wraps
#     the `cursor.fetchone()[0]` subscript-and-DELETE in an `if last_cache_key:`
#     presence guard so an empty culling SELECT never crashes with
#     "'NoneType' object is not subscriptable".
#
#   Requires(Implies(row is not None, Acc(list_pred(row), 1/2)))   <-- READ-ONLY
#   Requires(Implies(row is not None, len(row) > 0))                   input
#   Ensures(Implies(row is not None, Acc(list_pred(row), 1/2)))    <-- frame: the
#   Ensures(Implies(row is not None, len(row) > 0))                   caller keeps
#                                                                      its half
#   Ensures((Result() is None) == (row is None))    <-- DISCRIMINATING clause:
#                                                       a prune is issued (a key
#                                                       produced) IFF a row is
#                                                       present; absent => None,
#                                                       never index the absent row
#   Ensures(Implies(row is not None, Result() == row[0]))  <-- GROUNDED oracle:
#                                                       the produced key is exactly
#                                                       the row's first column
#
# `row` is held at Acc(list_pred(row), 1/2) (Requires AND Ensures) => READ-ONLY
# => the FRAME-MUTATION probe (directive 5) is MANDATORY.
#
# UNGROUNDED-ORACLE: N/A. The load-bearing output clause `Result() == row[0]` is
# GROUNDED in the argument (the row's own first column), and `(Result() is None)
# == (row is None)` is grounded in the argument's presence. There is NO opaque
# @Pure answer-key / exact-marker an impl could echo without doing the work: an
# impl that "echoes the oracle" is just the CORRECT impl. So instead of a wrong
# echo we ship an honest cheapest-impl positive control (pos-control-ternary).
#
# CONTROL-FLOW-EFFECT: N/A. The function's only observable is the produced
# Optional[int] — "is a prune issued, and with what key". There is no raise /
# side-effect channel distinct from that value (the real patch's distinction
# "execute the DELETE or not" is exactly the Result()-is-None abstraction). A
# capability-token rival would add no discrimination here; justified in assessment.
#
# Each expect="reject" rival carries the refinement argument that its faithful
# real patch would NOT resolve the F2P/P2P — so a verifying rival is a true
# verify⇏resolve break, not an artifact. F2P:
#   test_cull_delete_when_store_empty (DBCacheTests, DBCacheWithTimeZoneTests)
#   — forces _cull with _max_entries=-1 so the culling SELECT returns no boundary
#     row, then asserts the just-set record SURVIVES (assertIs(has_key(...),True)),
#     i.e. NO DELETE may be issued for the absent row.
from pathlib import Path

INSTANCE = "django__django-13089"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The one and only impl region in model.py (verbatim, inside # impl-start/end).
_GOLD_IMPL = """    if row is not None:
        last = row[0]
        return last
    return None
"""
assert _GOLD_IMPL in _BASE and _BASE.count(_GOLD_IMPL) == 1, "impl region drift"


def _impl(new_body: str) -> str:
    """Return _BASE with the gold impl-region body swapped for new_body. The swap
    edits ONLY text between the markers, so markers.same_spec is preserved."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# =============================================================================
# POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT; verify.
# If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
# No loop / fold here, so there is no induction-lemma trap (directives 2 & 3).
# =============================================================================

# Branch-REORDER: handle the absent case FIRST (early-return None), then read the
# present row's first column. Behaviourally identical to the gold impl; the
# subscript still sits under a presence guard (the `if row is None` early return),
# so the len(row)>0 precondition for row[0] is established on the fall-through.
_POS_REORDER = """    if row is None:
        return None
    return row[0]
"""

# Honest cheapest-impl "echo" of the grounded oracle via a conditional expression
# (no statement-level branch). Result() == row[0] when present, None when absent —
# exactly what the grounded postcondition asks for. This is the closest thing to
# an "oracle echo" the spec admits, and because the oracle is grounded it is the
# CORRECT impl and MUST verify.
_POS_TERNARY = """    out = row[0] if row is not None else None  # type: Optional[int]
    return out
"""

# =============================================================================
# ADMISSIBILITY — the precondition must accept a normal F2P-shaped input.
# Keep the gold impl shape and ASSERT the present-row precondition is establishable
# inside the present branch; the absent branch demonstrates the None path. If this
# cannot verify => PRECOND-TOO-STRONG.
# =============================================================================
_ADMISS = """    if row is not None:
        Assert(len(row) > 0)       # present-row Requires is establishable
        Assert(Acc(list_pred(row), 1 / 2))
        last = row[0]
        return last
    return None
"""

# =============================================================================
# FRAME-MUTATION (MANDATORY) — `row` is read-only (Acc(list_pred(row), 1/2)).
# A rival that WRITES the half-permission input to satisfy the postcondition must
# be REJECTED for INSUFFICIENT PERMISSION. Gold value-behaviour kept verbatim so
# the rejection is attributable ONLY to the write, not to a wrong value.
# =============================================================================
_FRAME_MUTATE = """    if row is not None:
        row[0] = row[0]            # WRITE to read-only Acc(list_pred(row),1/2)
        last = row[0]
        return last
    return None
"""

# =============================================================================
# UNIQUENESS / PARTIAL-DOMAIN rivals — same spec, wrong impl; MUST be rejected.
# If any VERIFIES => SPEC-TOO-WEAK.
# =============================================================================

# (A) PREPATCH DEFECT — drop the presence guard entirely (the exact bug). On
# row is None the subscript row[0] has no establishable len(row)>0 precondition
# => must be REJECTED (this is what model_prepatch.py reproduces / G-DIFF).
_NOGUARD = """    last = row[0]
    return last
"""

# (B) PARTIAL-DOMAIN, absent sub-domain — present handled correctly, but the
# absent case fabricates a non-None boundary key (0). Violates
# (Result() is None) == (row is None) on row is None.
_ABSENT_FAKE = """    if row is not None:
        last = row[0]
        return last
    return 0
"""

# (C) PARTIAL-DOMAIN, present sub-domain — absent handled correctly (None), but a
# present row produces the WRONG key (a constant 0, not row[0]). Violates
# Implies(row is not None, Result() == row[0]).
_PRESENT_WRONG = """    if row is not None:
        return 0
    return None
"""

# (D) FLIP — doubly wrong (supporting near-miss): None when a row IS present (a
# prune skipped though due) and a fabricated 0 when absent (a prune issued though
# none is due). Uses only constants so the rejection is attributable to the SPEC
# (the two postcondition clauses) and not to a subscript/permission error.
_FLIP = """    if row is not None:
        return None
    return 0
"""

SPEC_TESTS = [
    # ---- POSITIVE CONTROLS (soundness, expect verify) ----
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": "branch-reorder (handle absent first, then read present row[0]) "
                     "is behaviourally identical to the gold impl and keeps the "
                     "subscript under a presence guard; a structurally-different "
                     "CORRECT impl MUST verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-control-ternary",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_TERNARY),
        "rationale": "honest cheapest-impl: conditional expression row[0] if present "
                     "else None. Since the oracle is GROUNDED (Result()==row[0]), the "
                     "grounded 'echo' is the CORRECT impl and MUST verify. Doubles as "
                     "the UNGROUNDED-ORACLE lane's positive control (no wrong echo exists).",
    },
    # ---- ADMISSIBILITY (expect verify) ----
    {
        "id": "admiss-present-and-absent",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": "the precondition admits a normal F2P-shaped input: inside the "
                     "present branch Assert(len(row)>0) and Assert(Acc(list_pred(row),1/2)) "
                     "both hold, and the absent branch reaches the None path. If the "
                     "Requires could not be established => PRECOND-TOO-STRONG.",
    },
    # ---- FRAME-MUTATION (MANDATORY, expect reject) ----
    {
        "id": "frame-mutation-write-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUTATE),
        "refinement": "a faithful real patch that WRITES the fetched DB row "
                      "(cursor.fetchone() result) before reading row[0] would mutate "
                      "the driver's row object — not what the gold patch does (it only "
                      "reads last_cache_key[0]); it does not resolve the F2P, which is "
                      "purely about guarding the read on presence. The point is the "
                      "spec must REJECT it for permission, proving the read-only frame "
                      "is enforced (else SPEC-TOO-WEAK: the read-only contract is hollow).",
        "rationale": "row is held at Acc(list_pred(row), 1/2) (Requires AND Ensures). "
                     "Assigning row[0] needs the FULL list_pred permission, which the "
                     "spec never grants => Nagini rejects for INSUFFICIENT PERMISSION. "
                     "Gold value-behaviour kept verbatim so the rejection is attributable "
                     "solely to the write.",
    },
    # ---- PARTIAL-DOMAIN / prepatch defect (expect reject) ----
    {
        "id": "noguard-prepatch-defect",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NOGUARD),
        "refinement": "this is the EXACT pre-patch bug: cursor.fetchone()[0] with no "
                      "presence guard. On an empty culling SELECT (the F2P scenario: "
                      "_max_entries=-1, store empty) fetchone() is None and [0] raises "
                      "'NoneType' object is not subscriptable — _cull crashes, the just-"
                      "set record is not retained, F2P test_cull_delete_when_store_empty "
                      "FAILS. Its faithful real patch does NOT resolve.",
        "rationale": "on row is None the subscript row[0] has no establishable "
                     "len(row)>0 precondition (granted only when row is not None) => "
                     "Nagini rejects the subscript obligation. This is what "
                     "model_prepatch.py reproduces (G-DIFF).",
    },
    {
        "id": "partial-absent-fabricates-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ABSENT_FAKE),
        "refinement": "present rows are handled exactly like gold, so this passes "
                      "test_cull / test_zero_cull (P2P, populated store). But it "
                      "fabricates a boundary key (0) for the ABSENT row, i.e. its real "
                      "patch would issue a DELETE WHERE cache_key < 0 when the culling "
                      "SELECT returned nothing — pruning against a phantom boundary. "
                      "In the F2P (empty store) the just-set record could be deleted "
                      "=> assertIs(has_key('force_cull_delete'), True) FAILS. Does NOT resolve.",
        "rationale": "violates the discriminating clause (Result() is None) == (row is None): "
                     "on row is None it returns 0 (not None). Spec rejects it.",
    },
    {
        "id": "partial-present-wrong-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PRESENT_WRONG),
        "refinement": "the absent case is handled correctly (None, no prune), so it "
                      "passes the F2P empty-store test. But on a PRESENT row it returns "
                      "a constant 0 instead of the boundary row[0], i.e. its real patch "
                      "would DELETE WHERE cache_key < 0 rather than < last_cache_key[0] — "
                      "the wrong rows are pruned on a populated store, breaking "
                      "test_cull/test_zero_cull (P2P). Does NOT resolve.",
        "rationale": "violates the grounded oracle Implies(row is not None, "
                     "Result() == row[0]): a present row must produce row[0], not 0. "
                     "Spec rejects it.",
    },
    {
        "id": "flip-doubly-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FLIP),
        "refinement": "doubly wrong (supporting near-miss): None for a present row "
                      "(no prune when one is due) and a fabricated 0 for the absent row "
                      "(a prune when none is due). The faithful real patch issues the "
                      "DELETE exactly backwards — pruning the empty store (F2P fails) "
                      "and skipping the prune on a full store (test_cull P2P fails). "
                      "Does NOT resolve on either subdomain.",
        "rationale": "violates BOTH (Result() is None) == (row is None) (returns 0 when "
                     "row is None) and the grounded oracle on the present branch "
                     "(returns None != row[0]). Spec rejects it.",
    },
]

# No @ContractOnly axiom and no A-reference deep model (meta.axioms == [],
# deep_model_references == []). The changed behaviour is modeled DEEPLY as
# optional-row logic over `row`; the proof consumes no callee contract. The
# DB-API fetchone() optional-row shape the refinement relies on is the standard
# PEP 249 contract, documented and exercised by axiom_check.py (G-AX vacuous).
# There is therefore no axiom-soundness / axiom-containment obligation.
AXIOM_TESTS = []
