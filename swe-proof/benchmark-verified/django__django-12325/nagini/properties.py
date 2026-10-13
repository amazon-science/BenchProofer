"""PBT falsification battery for django__django-12325.

NOT a Nagini module: a manifest of adversarial cases the runner
(swebench_nagini.pbt) executes. Spec cases are full model.py variants that share
the FROZEN spec byte-for-byte (only the impl region — markers # impl-start /
# impl-end, invariants included — is edited) and are checked by Nagini verify +
markers.same_spec. There is no axiomatized callee / @Pure oracle in this bundle,
so AXIOM_TESTS = [].

Defended surface (from model.py):
  select_inheritance_links(is_parent_link: List[bool], related_key: List[int])
                          -> Dict[int, int]
  * BOTH inputs are READ-ONLY: Requires(Acc(list_pred(.), 1/2)). => the
    frame-mutation probe is MANDATORY: any rival that WRITES an input to satisfy
    a postcondition vacuously must be rejected for INSUFFICIENT PERMISSION.
  * Postcondition clause (1): for every k in Result(), Result()[k] is a valid
    position with is_parent_link[Result()[k]] True and related_key[Result()[k]]
    == k. (Every recorded relation is a designated parent link targeting that
    key.)
  * Postcondition clause (3)+(4): every i with is_parent_link[i] True has
    related_key[i] in Result() AND Result()[related_key[i]] >= i. (No
    designated parent link is lost, and the recorded position is the LAST
    parent-link position for its key — last-writer-wins, pinning WHICH
    relation is recorded, exactly like the repo's dict assignment.)
  * The postcondition is GROUNDED directly in the input arrays (no @Pure
    answer-key to echo), so there is no ungrounded-oracle-echo lane; instead a
    cheapest honest positive control is included (see 'assessment').
"""
from pathlib import Path

INSTANCE = "django__django-12325"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The gold impl body (inside # impl-start / # impl-end), used as the swap anchor.
_GOLD_IMPL = (
    "        if is_parent_link[i]:\n"
    "            result[related_key[i]] = i\n"
    "        i = i + 1"
)
assert _GOLD_IMPL in _BASE

# Anchor at the top of the impl region (just after impl-start) for the
# admissibility self-call.
_IMPL_TOP = "    result = {}  # type: Dict[int, int]\n    i = 0"
assert _IMPL_TOP in _BASE


# ---------------------------------------------------------------------------
# 1) POSITIVE CONTROL — local-variable reshape (correct; MUST verify).
# Reads each flag/key into a local before recording. Keeps every gold loop
# invariant verbatim, so the gold proof obligations are unchanged; only the
# executable shape differs. If this fails => SPEC-TOO-STRONG.
_POS_LOCAL = _swap(
    _BASE, _GOLD_IMPL,
    "        pl = is_parent_link[i]\n"
    "        key = related_key[i]\n"
    "        if pl:\n"
    "            result[key] = i\n"
    "        i = i + 1",
)

# ---------------------------------------------------------------------------
# 2) POSITIVE CONTROL — branch reorder (correct; MUST verify).
# Negate the eligibility test and skip the ordinary case; record in the else.
# Behaviourally identical to gold (records exactly the parent links). Keeps the
# gold invariants verbatim. If this fails => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _GOLD_IMPL,
    "        if not is_parent_link[i]:\n"
    "            i = i + 1\n"
    "        else:\n"
    "            result[related_key[i]] = i\n"
    "            i = i + 1",
)

# ---------------------------------------------------------------------------
# 3) ADMISSIBILITY — self-call on an F2P-shaped input (MUST verify).
# Before the gold loop, build two fresh parallel lists modelling the issue's
# scenario (a designated parent link + an ordinary OneToOneField to the SAME
# related model, key token 7) and call the function. The precondition
# (Acc(.,1/2) on each list, equal lengths) is established from full permission
# on the freshly-built lists. If the call fails to verify => PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE, _IMPL_TOP,
    "    # admissibility: the precondition must accept a normal F2P-shaped input\n"
    "    # (a designated parent link and an ordinary relation to the same model).\n"
    "    fresh_pl = [True, False]  # type: List[bool]\n"
    "    fresh_rk = [7, 7]  # type: List[int]\n"
    "    Assert(Acc(list_pred(fresh_pl), 1 / 2))\n"
    "    Assert(Acc(list_pred(fresh_rk), 1 / 2))\n"
    "    Assert(len(fresh_pl) == len(fresh_rk))\n"
    "    result = {}  # type: Dict[int, int]\n"
    "    i = 0",
)

# ---------------------------------------------------------------------------
# 4) FRAME-MUTATION on is_parent_link (WRONG; MUST reject — insufficient perm).
# The cheat: overwrite is_parent_link[i] := True, THEN record every relation
# unconditionally. Clause (1)'s is_parent_link[Result()[k]] would then hold
# vacuously (the input has been forged to report every recorded position as a
# parent link). With only Acc(list_pred(is_parent_link), 1/2), the write
# `is_parent_link[i] = True` cannot be discharged => verification must fail for
# INSUFFICIENT PERMISSION (the permission system), NOT clause (1).
_FRAME_IPL = _swap(
    _BASE, _GOLD_IMPL,
    "        is_parent_link[i] = True\n"
    "        result[related_key[i]] = i\n"
    "        i = i + 1",
)

# ---------------------------------------------------------------------------
# 5) FRAME-MUTATION on related_key (WRONG; MUST reject — insufficient perm).
# Supporting frame probe on the OTHER read-only input: forge related_key[i] to
# i so that related_key[Result()[k]] == k holds for whatever key we record. With
# Acc(list_pred(related_key), 1/2) the write cannot be discharged => rejected for
# INSUFFICIENT PERMISSION.
_FRAME_RK = _swap(
    _BASE, _GOLD_IMPL,
    "        if is_parent_link[i]:\n"
    "            related_key[i] = i\n"
    "            result[related_key[i]] = i\n"
    "        i = i + 1",
)

# ---------------------------------------------------------------------------
# 6) UNIQUENESS — no eligibility filter (the PRE-PATCH bug; MUST reject).
# Record EVERY scanned relation, last-writer-wins (the buggy loop). An ordinary
# one-to-one relation that targets a parent is recorded, so some k in Result()
# has is_parent_link[Result()[k]] False => clause (1) is violated. This is
# exactly model_prepatch.py's behaviour and must be rejected.
_WEAK_ALL = _swap(
    _BASE, _GOLD_IMPL,
    "        result[related_key[i]] = i\n"
    "        i = i + 1",
)

# ---------------------------------------------------------------------------
# 7) UNIQUENESS / PARTIAL-DOMAIN — skip the first scanned relation (MUST reject).
# Apply the eligibility filter correctly EXCEPT at position 0: a designated
# parent link declared first is never recorded. When the genuine parent link is
# the first scanned relation, its key is absent from Result() => clause (3)
# (Forall i: is_parent_link[i] ==> related_key[i] in Result()) is violated.
_WEAK_SKIP0 = _swap(
    _BASE, _GOLD_IMPL,
    "        if is_parent_link[i] and i > 0:\n"
    "            result[related_key[i]] = i\n"
    "        i = i + 1",
)

# ---------------------------------------------------------------------------
# 8) UNIQUENESS / VALUE-PARTIAL-DOMAIN — record non-parent-links on a value
# sub-domain (MUST reject). Record parent links always (keeps clause (3)), but
# ALSO record an ordinary relation whenever its key token is 0. On that
# sub-domain Result() then contains a key whose recorded position is NOT a parent
# link => clause (1) is violated. Targets the value abstraction directly, a class
# a byte-fuzzer never reaches.
_WEAK_VALUE = _swap(
    _BASE, _GOLD_IMPL,
    "        if is_parent_link[i] or related_key[i] == 0:\n"
    "            result[related_key[i]] = i\n"
    "        i = i + 1",
)


# ---------------------------------------------------------------------------
# 9) UNIQUENESS — FIRST-writer-wins (WRONG; MUST reject). Record a parent link
# only if its key is not already recorded, so the FIRST designated parent link
# per related model wins instead of the LAST. Clauses (1) and (3) both still
# hold (every recorded position is a parent link targeting its key; no parent
# link's key is lost), so under the pre-repair spec this wrong impl VERIFIED —
# the exact weakness class the G-PANEL-1 auditor exploited. Clause (4)
# (Result()[related_key[i]] >= i for every parent link i) is violated whenever
# two designated parent links target the same model: the recorded position is
# the earlier one. Must be rejected by clause (4).
_WEAK_FIRSTWINS = _swap(
    _BASE, _GOLD_IMPL,
    "        if is_parent_link[i] and related_key[i] not in result:\n"
    "            result[related_key[i]] = i\n"
    "        i = i + 1",
)


SPEC_TESTS = [
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCAL,
        "rationale": "structurally-different but CORRECT impl (each flag/key read "
                     "into a local before recording); records exactly the parent "
                     "links, gold invariants kept verbatim. Must verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": "branch-reordered correct impl: skip the ordinary case, "
                     "record in the else. Behaviourally identical to gold; gold "
                     "invariants kept verbatim. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the precondition (Acc(.,1/2) on each list, equal lengths) "
                     "must accept a normal F2P-shaped input (a parent link + an "
                     "ordinary relation to the same model); the clauses are "
                     "asserted AT the witness rather than exercised by a self-call, "
                     "because the model now carries Requires(MustTerminate(2)) and a "
                     "same-level self-call on a non-shrinking argument is an "
                     "obligation leak Nagini is right to refuse. Else "
                     "PRECOND-TOO-STRONG. NEGATIVE CONTROL (measured): move the "
                     "witness outside the frozen equal-length clause, "
                     "fresh_rk = [7, 7, 7] against fresh_pl = [True, False], and "
                     "the probe REJECTS: `Assert might fail. Assertion "
                     "(len(fresh_pl) == len(fresh_rk)) might not hold.` So the "
                     "asserted domain is a real check, not a restatement.",
    },
    {
        "id": "frame-mutation-write-is_parent_link",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_IPL,
        "refinement": "The faithful real patch sets field.remote_field.parent_link "
                      "= True on every scanned OneToOneField before recording it. "
                      "That forges the designation of ordinary relations: _prepare "
                      "would promote a non-parent-link field that now reports "
                      "parent_link=True, so the spurious clash/config behaviour the "
                      "F2P tests assert is changed (test_clash_parent_link expects "
                      "the ordinary relation to still produce E304/E305 clash "
                      "errors against an unmodified parent_link flag; "
                      "test_onetoone_with_parent_model relies on the ordinary "
                      "relation NOT being treated as a parent link). It does not "
                      "resolve.",
        "rationale": "is_parent_link is read-only (Acc(list_pred,1/2)); the write "
                     "is_parent_link[i] = True cannot be discharged. Rejection comes "
                     "from the PERMISSION SYSTEM (insufficient permission), not from "
                     "clause (1) (which the forged input would otherwise satisfy "
                     "vacuously). #1 weakness class.",
    },
    {
        "id": "frame-mutation-write-related_key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_RK,
        "refinement": "A faithful patch that rewrote the derived related-model "
                      "token (make_model_tuple(resolve_relation(...))) to the "
                      "relation's own position would key parent_links by a bogus "
                      "identity; _prepare collects self.parents keyed by the real "
                      "related model, so the parent link would be filed under the "
                      "wrong parent and the MTI link would be lost. Does not "
                      "resolve.",
        "rationale": "related_key is read-only (Acc(list_pred,1/2)); the write "
                     "related_key[i] = i cannot be discharged. Rejection comes from "
                     "the PERMISSION SYSTEM. Supporting frame probe on the second "
                     "read-only input.",
    },
    {
        "id": "weak-no-filter-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_ALL,
        "refinement": "This is the PRE-PATCH behaviour verbatim (model_prepatch.py): "
                      "record every scanned one-to-one relation, last-writer-wins, "
                      "with no parent_link filter. An ordinary OneToOneField that "
                      "targets a parent displaces / stands in for the genuine "
                      "parent link, so _prepare promotes a non-parent-link field and "
                      "raises ImproperlyConfigured('Add parent_link=True ...') — "
                      "exactly the bug. test_onetoone_with_parent_model still fails. "
                      "Does not resolve.",
        "rationale": "Clause (1) Forall k in Result(): is_parent_link[Result()[k]] "
                     "is violated whenever the last relation written for a key is "
                     "ordinary. Rejection comes from POSTCONDITION clause (1).",
    },
    {
        "id": "weak-skip-first-relation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_SKIP0,
        "refinement": "Faithful patch: `if i and isinstance(field, OneToOneField) "
                      "and field.remote_field.parent_link:` — i.e. never record the "
                      "FIRST scanned relation. When the designated parent link is "
                      "declared first (the issue's second, 'Works' ordering has the "
                      "parent link first only in some declarations; test_clash_"
                      "parent_link and test_onetoone_with_parent_model both exercise "
                      "a parent link that can be the first scanned field), it is "
                      "lost, self.parents has no entry for that parent, and the MTI "
                      "link / pk setup breaks. Does not resolve.",
        "rationale": "Clause (3) Forall i: is_parent_link[i] ==> related_key[i] in "
                     "Result() is violated for a parent link at position 0. "
                     "Rejection comes from POSTCONDITION clause (3) (partial-domain: "
                     "correct on i>0, wrong on the first element).",
    },
    {
        "id": "weak-record-nonparent-on-key0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_VALUE,
        "refinement": "Faithful patch: `if field.remote_field.parent_link or "
                      "make_model_tuple(related) == <some fixed model token>:` — "
                      "records an ordinary relation whenever it targets one "
                      "particular related model. For that target, _prepare promotes "
                      "an ordinary (non-parent-link) field and raises "
                      "ImproperlyConfigured for it; the F2P assertion that ordinary "
                      "relations to a parent are not promoted fails on that "
                      "sub-domain. Does not resolve.",
        "rationale": "Clause (1) is violated on the value sub-domain related_key[i] "
                     "== 0: a recorded position there is is_parent_link False. "
                     "Rejection comes from POSTCONDITION clause (1) (value-partial-"
                     "domain — invisible to a byte fuzzer).",
    },
    {
        "id": "weak-first-writer-wins",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_FIRSTWINS,
        "refinement": "Faithful patch: `if isinstance(field, OneToOneField) and "
                      "field.remote_field.parent_link and make_model_tuple(related) "
                      "not in parent_links:` — the FIRST designated parent link to "
                      "a related model is kept and later ones are ignored, instead "
                      "of the repo's last-writer-wins dict assignment. When two "
                      "designated parent links target the same parent, _prepare "
                      "promotes a DIFFERENT field object than the patched repo "
                      "does (self.parents holds the first, not the last), so pk "
                      "promotion / field identity downstream diverges from the "
                      "gold patch. Does not refine the patched behaviour.",
        "rationale": "Clauses (1) and (3) still hold for this wrong impl (every "
                     "recorded position is a parent link targeting its key; no "
                     "key is lost), which is exactly how it slipped past the "
                     "pre-repair spec (the G-PANEL-1 finding). Clause (4) "
                     "Result()[related_key[i]] >= i is violated for the LATER of "
                     "two parent links to the same key. Rejection comes from "
                     "POSTCONDITION clause (4) (tie-breaking / which-relation "
                     "pinning).",
    },
]


# No @ContractOnly axioms and no A-reference deep models in this bundle
# (meta.json axioms = [], deep_model_references = []; the unchanged
# isinstance/resolve_relation/make_model_tuple callees are type-refined into the
# int/bool carrier, never contracted). G-AX is vacuous; nothing to probe.
AXIOM_TESTS = []
