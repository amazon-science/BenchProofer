# properties.py — PBT falsification battery for django__django-11066.
#
# NOT a Nagini module: a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec exactly (region-surgery: only the
# text strictly inside # impl-start / # impl-end is edited; the spec_view elides
# that whole region, so same_spec is guaranteed) and differ only in the impl.
#
# DEFENDED SURFACE (read from model.py):
#   persisted_db(db: List[int], routed: List[int]) -> List[int]
#   Requires: Acc(list_pred(db),1/2), Acc(list_pred(routed),1/2)   <-- BOTH inputs
#             READ-ONLY (half permission); len(db)>0; len(routed)>0
#   Ensures:  Acc(list_pred(db),1/2), Acc(list_pred(routed),1/2),
#             Acc(list_pred(Result()))   (result is a FRESH full-perm list)
#             alias_eq(ToSeq(Result()), ToSeq(db))   <-- THE load-bearing clause:
#             the resolved write-target alias equals `db`, REGARDLESS of `routed`.
#   alias_eq(a,b) := (a == b)  -- a @Pure helper that is GROUNDED in the args
#             (plain PSeq[int] equality of Result against the input `db`); it is
#             NOT an opaque answer-key, so there is no "wrong echo of the oracle"
#             that could verify. The only echo is `return routed`, which is the
#             prepatch bug and is genuinely caught (weak-prepatch-routed below).
#
# Refinement ground truth (refinement.md / mapping.md / G-AX):
#   db    <- schema_editor.connection.alias            (always a present alias)
#   routed<- router.db_for_write(...)  (A-reference)   (an arbitrary present alias,
#                                                        free to differ from db)
#   The gold patch adds `using=db` to content_type.save(...) so the write-target
#   resolution `using = using or router.db_for_write(...)` short-circuits to db.
#   The F2P test (test_existing_content_type_rename_other_database) sets the
#   router to return 'default' while the step's db is 'other': any impl whose
#   result is not provably db is the prepatch bug and does NOT resolve.
#
# No @ContractOnly axioms (meta.axioms == []); the only deep-model reference is
# the FREE INPUT `routed` (A-reference), validated by axiom_check.py / G-AX.
# Hence AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "django__django-11066"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body (everything strictly inside # impl-start / # impl-end).
# All region surgery replaces this single block, so same_spec is guaranteed.
_GOLD_IMPL = """    # using = explicit_alias or routing_policy_choice
    # An explicit alias is supplied (== db), so it is used directly; the
    # routing-policy fallback is reached only when no explicit alias is given.
    src = db if len(db) > 0 else routed  # type: List[int]
    # Copy the chosen alias into a fresh result carrier.
    target = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(db), 1 / 2))
        Invariant(Acc(list_pred(routed), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(len(db) > 0)
        Invariant(ToSeq(src) == ToSeq(db))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(target) == ToSeq(src).take(i))
        # invariants-end
        target = target + [src[i]]
        Assert(ToSeq(src).take(i) + PSeq(src[i]) == ToSeq(src).take(i + 1))
        i = i + 1
    return target"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


def _with_impl(new_impl_body: str) -> str:
    """Return model.py with the impl body replaced (spec untouched)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL — structurally-different but CORRECT (soundness).
# Reorder the resolution branch: pick `routed` only when db is absent, else db.
# Since the precondition guarantees len(db) > 0 the source is still db, so the
# gold invariants (ToSeq(src) == ToSeq(db)) remain valid verbatim. Only the
# executable shape of the ternary changes; the proof obligations are unchanged.
# MUST verify (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------
_POS_REORDER = """    # using = routing_policy_choice ONLY when no explicit alias; else explicit.
    # Branch reordered (db absent -> routed; otherwise db). len(db) > 0 holds by
    # precondition, so src == db exactly as in gold; all gold framing kept.
    src = routed if len(db) == 0 else db  # type: List[int]
    target = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(db), 1 / 2))
        Invariant(Acc(list_pred(routed), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(len(db) > 0)
        Invariant(ToSeq(src) == ToSeq(db))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(target) == ToSeq(src).take(i))
        # invariants-end
        target = target + [src[i]]
        Assert(ToSeq(src).take(i) + PSeq(src[i]) == ToSeq(src).take(i + 1))
        i = i + 1
    return target"""

# ---------------------------------------------------------------------------
# (2) POSITIVE CONTROL — honest cheapest correct impl (grounded-oracle control).
# alias_eq is grounded in the args, so there is no WRONG echo to exploit; the
# correct cheapest impl copies `db` itself (drops the `src` indirection). Loop
# is over db directly; framing pinned to db. MUST verify.
# ---------------------------------------------------------------------------
_POS_DIRECT = """    # The explicit alias is always present, so the resolved target is db itself.
    # Copy db directly into a fresh carrier (no `src` indirection).
    target = []  # type: List[int]
    i = 0
    while i < len(db):
        # invariants-start
        Invariant(Acc(list_pred(db), 1 / 2))
        Invariant(Acc(list_pred(routed), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(0 <= i and i <= len(db))
        Invariant(ToSeq(target) == ToSeq(db).take(i))
        # invariants-end
        target = target + [db[i]]
        Assert(ToSeq(db).take(i) + PSeq(db[i]) == ToSeq(db).take(i + 1))
        i = i + 1
    return target"""

# ---------------------------------------------------------------------------
# (3) ADMISSIBILITY — an IN-REGION self-call proves the precondition admits a
# normal, F2P-shaped input. Inside the impl region we build two fresh present
# alias carriers (an 'other'-like db and a 'default'-like routed, as in the F2P
# test) and recursively call persisted_db on them: this discharges the Requires
# (len>0 and lending a 1/2 share from the locally-owned full-perm carriers) for a
# legitimate input, then asserts the guaranteed Result==db. If the self-call
# cannot establish Requires for this normal input -> PRECOND-TOO-STRONG. The
# real persisted_db result is then computed by the gold body and returned, so the
# module still verifies. Edited strictly inside the impl region -> same_spec.
# ---------------------------------------------------------------------------
_ADMISS_IMPL = """    # --- admissibility self-call on an F2P-shaped input ---
    # Two present aliases that differ, mirroring the F2P (db 'other', router
    # 'default'); both are locally-owned full-perm carriers, so lending a 1/2
    # share to satisfy Requires(Acc(...,1/2)) is legitimate.
    a_db = [111, 116, 104, 101, 114]  # type: List[int]   # 'other'
    a_routed = [100, 101, 102, 97, 117, 108, 116]  # type: List[int]  # 'default'
    Assert(len(a_db) > 0)
    Assert(len(a_routed) > 0)
    a_res = persisted_db(a_db, a_routed)
    Assert(alias_eq(ToSeq(a_res), ToSeq(a_db)))
    # --- the real (gold) resolution for db/routed ---
    src = db if len(db) > 0 else routed  # type: List[int]
    target = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(db), 1 / 2))
        Invariant(Acc(list_pred(routed), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(len(db) > 0)
        Invariant(ToSeq(src) == ToSeq(db))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(target) == ToSeq(src).take(i))
        # invariants-end
        target = target + [src[i]]
        Assert(ToSeq(src).take(i) + PSeq(src[i]) == ToSeq(src).take(i + 1))
        i = i + 1
    return target"""


# ---------------------------------------------------------------------------
# (4) FRAME-MUTATION on `db` (uniqueness, MANDATORY — db is Acc(...,1/2)).
# A rival that tries to satisfy the postcondition by WRITING the read-only input
# `db` (here: append to db so it equals what we return). The half-permission on
# db forbids any write -> must REJECT for INSUFFICIENT PERMISSION. A fuzzer never
# thinks to mutate the input; this is the #1 weakness class.
# ---------------------------------------------------------------------------
_FRAME_MUT_DB = """    # ADVERSARY: write to the read-only input db, then return it. Acc(db,1/2)
    # forbids the write -> insufficient permission. (Returning db would also
    # violate Acc(list_pred(Result())) which demands a FRESH full-perm list.)
    db.append(0)
    return db"""

# ---------------------------------------------------------------------------
# (5) FRAME-MUTATION on `routed` (uniqueness, MANDATORY — routed is Acc(...,1/2)).
# A rival that overwrites the OTHER read-only input `routed` to make it match db,
# then returns it. Acc(routed,1/2) forbids the write -> REJECT for insufficient
# permission. Distinct from (4): proves BOTH read-only inputs are protected.
# ---------------------------------------------------------------------------
_FRAME_MUT_ROUTED = """    # ADVERSARY: mutate the read-only input routed and return it. Acc(routed,1/2)
    # forbids the write -> insufficient permission.
    routed.append(0)
    return routed"""

# ---------------------------------------------------------------------------
# (6) UNIQUENESS — the prepatch echo `return routed` (THE central attack).
# The postcondition pins Result == db and says NOTHING about routed; routed is a
# FREE input (the router's choice) unconstrained to equal db. Copying `routed`
# into a fresh carrier satisfies the freshness/permission clauses but cannot
# prove alias_eq(ToSeq(Result()), ToSeq(db)) for an arbitrary routed -> REJECT
# at the postcondition. This is exactly model_prepatch.py's behaviour.
# ---------------------------------------------------------------------------
_WEAK_PREPATCH = """    # ADVERSARY (prepatch bug): no explicit alias used; fall through to the
    # routing policy's choice `routed`. Copy routed into a fresh carrier.
    target = []  # type: List[int]
    i = 0
    while i < len(routed):
        # invariants-start
        Invariant(Acc(list_pred(db), 1 / 2))
        Invariant(Acc(list_pred(routed), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(0 <= i and i <= len(routed))
        Invariant(ToSeq(target) == ToSeq(routed).take(i))
        # invariants-end
        target = target + [routed[i]]
        Assert(ToSeq(routed).take(i) + PSeq(routed[i]) == ToSeq(routed).take(i + 1))
        i = i + 1
    return target"""

# ---------------------------------------------------------------------------
# (7) PARTIAL-DOMAIN — correct on a prefix, diverges on the LAST element.
# Copy db for indices 0..len-2 but take the final code point from `routed`. When
# db and routed agree on the last char (or len 1 with equal last) it equals db;
# it DIVERGES whenever the aliases' last code points differ (e.g. 'other' vs
# 'default'). The element-wise postcondition catches the diverging index ->
# REJECT. Forces the spec to pin every position, not just length.
# ---------------------------------------------------------------------------
_PARTIAL_DOMAIN = """    # ADVERSARY: copy db on the prefix but splice the LAST code point from the
    # routing choice `routed`. Equals db only when last code points coincide;
    # diverges on the F2P aliases (last char of 'other' != 'default').
    target = []  # type: List[int]
    i = 0
    while i < len(db):
        # invariants-start
        Invariant(Acc(list_pred(db), 1 / 2))
        Invariant(Acc(list_pred(routed), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(len(routed) > 0)
        Invariant(0 <= i and i <= len(db))
        # invariants-end
        if i == len(db) - 1:
            target = target + [routed[len(routed) - 1]]
        else:
            target = target + [db[i]]
        i = i + 1
    return target"""


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_REORDER),
        "rationale": (
            "Structurally-different CORRECT impl: the resolution ternary is "
            "reordered to `routed if len(db)==0 else db`. Since len(db)>0 by "
            "precondition the source is still db, so the gold invariant "
            "ToSeq(src)==ToSeq(db) and every framing assert remain valid "
            "verbatim. A faithful correct impl MUST verify; if it cannot -> "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_DIRECT),
        "rationale": (
            "Grounded-oracle positive control: alias_eq is grounded in the args "
            "(Result==db), so there is no wrong echo to exploit; the honest "
            "cheapest correct impl copies db directly (drops the `src` "
            "indirection) and loops over db with db-pinned framing. MUST verify "
            "(else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-fshaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS_IMPL),
        "rationale": (
            "A positive-control caller builds an F2P-shaped input (two present, "
            "differing aliases like 'other'/'default') and calls persisted_db, "
            "establishing the Requires (len>0, full perm to lend a 1/2 share) "
            "and asserting the guaranteed Result==db. The precondition must "
            "admit a normal input; if the call site cannot establish Requires "
            "-> PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-db",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT_DB),
        "refinement": (
            "A real patch that WRITES to the migration step's `db` alias carrier "
            "(schema_editor.connection.alias) to make the save target it is not "
            "the gold edit at all (the gold edit only passes `using=db`); it "
            "mutates shared connection state and would not be the one-token "
            "save(using=db,...) fix, so it would not resolve the F2P the way the "
            "gold patch does."
        ),
        "rationale": (
            "FRAME-MUTATION (#1 weakness class): db is a read-only input "
            "(Acc(list_pred(db),1/2)). Appending to db requires WRITE permission "
            "the caller never lent -> REJECT for INSUFFICIENT PERMISSION. (The "
            "gold invariants on db are kept verbatim, so the rejection is "
            "attributable to the write, not a spec change.) Also returning db "
            "would violate Acc(list_pred(Result())) which demands a fresh "
            "full-perm result."
        ),
    },
    {
        "id": "frame-mut-routed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT_ROUTED),
        "refinement": (
            "A real patch that mutates the router's returned alias object "
            "`routed` to coerce it to equal db is not the gold edit (which never "
            "touches the router result); it would corrupt the routing policy's "
            "value and is not the one-token save(using=db,...) change, so it does "
            "not faithfully reproduce the resolving patch."
        ),
        "rationale": (
            "FRAME-MUTATION on the SECOND read-only input: routed is "
            "Acc(list_pred(routed),1/2). Appending to routed needs WRITE "
            "permission never granted -> REJECT for INSUFFICIENT PERMISSION. "
            "Proves BOTH read-only inputs are protected, not just db."
        ),
    },
    {
        "id": "weak-prepatch-routed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_PREPATCH),
        "refinement": (
            "This IS the prepatch behaviour: returning the routing policy's "
            "choice `routed` corresponds to `content_type.save(update_fields=...)` "
            "with NO explicit alias, so Model.save_base resolves the write target "
            "to router.db_for_write(...). In the F2P test the router returns "
            "'default' while the step's db is 'other', so the renamed row lands "
            "in the WRONG database and "
            "test_existing_content_type_rename_other_database FAILS. "
            "model_prepatch.py is exactly this and is documented to fail the "
            "postcondition (G-DIFF)."
        ),
        "rationale": (
            "UNIQUENESS / partial-domain: the postcondition pins "
            "alias_eq(ToSeq(Result()), ToSeq(db)) and constrains routed NOT AT "
            "ALL; routed is a free input that may differ from db. A fresh copy of "
            "routed satisfies freshness/permission but cannot prove Result==db "
            "for an arbitrary routed -> REJECT at the postcondition clause. If it "
            "verified, the spec would admit the prepatch bug => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "partial-domain-last-elem",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_DOMAIN),
        "refinement": (
            "A patch that resolves the write target to db on all but the last "
            "code point, splicing the final char from the router's choice, is not "
            "any faithful save(using=...) edit: it would commit the row to a "
            "DB whose alias differs from db precisely when the router disagrees "
            "with db on the last character (e.g. 'other' vs 'default'), so the "
            "renamed row would not land in 'other' and the F2P would FAIL."
        ),
        "rationale": (
            "PARTIAL-DOMAIN: correct on the prefix but the final element is taken "
            "from `routed`. The result equals db only when the last code points "
            "coincide; it diverges on the F2P aliases. The element-wise "
            "postcondition alias_eq(ToSeq(Result()),ToSeq(db)) (full PSeq "
            "equality) catches the diverging last index -> REJECT. If it verified "
            "(spec pinning only e.g. length) => SPEC-TOO-WEAK."
        ),
    },
]


# No @ContractOnly axioms and no consumed deep-model axiom (meta.axioms == []).
# The single deep-model reference `routed` is a FREE INPUT (A-reference) whose
# soundness is validated by axiom_check.py / G-AX (real ConnectionRouter.
# db_for_write is independent of db; `using or router.db_for_write(...)` short-
# circuits to the explicit alias). There is no @ContractOnly Requires-domain to
# probe in this lane, so AXIOM_TESTS is empty by design (see assessment).
AXIOM_TESTS = []
