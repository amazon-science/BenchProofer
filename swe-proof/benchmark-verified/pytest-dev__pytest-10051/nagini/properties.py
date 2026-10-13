# properties.py — PBT falsification battery for pytest-dev__pytest-10051.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that SHARE the frozen spec (only the impl region is swapped,
# guaranteed by region-surgery via _swap) and are checked by Nagini verify +
# same_spec; axiom cases are real-callee probes checked in Docker.
#
# Defended surface (read model.py / refinement.md):
#   discard_captured(buf, view): empty buf.items leaving it EMPTY, the SAME
#   object (identity preserved), so the earlier-handed-out observer reference
#   `view` (== buf.items on entry, by Requires) still names the buffer's live
#   list afterwards. The load-bearing, DISCRIMINATING clause is
#       Ensures(buf.items is Old(buf.items))   and   Ensures(view is buf.items)
#   — emptiness alone (len==0) is satisfiable by the buggy rebind buf.items=[].
#   append_then_visible(buf, view, item): a subsequently captured item is
#   visible through the still-aliased view (len/value pinned on BOTH names).
#
# Termination: both functions carry Requires(MustTerminate(2)) and the consumed
# empty_in_place axiom carries Requires(MustTerminate(1)), so a same-spec
# implementation that diverges (bare self-recursion, or an endless loop before
# returning) is REJECTED by Nagini's obligation leak check instead of
# vacuously satisfying the Ensures. This closes the divergence loophole the
# earlier audit exploited (atk_recursion_discard / atk_empty_then_recurse).
#
# Permission shape: both functions hold FULL permission on the single shared
# object via `Acc(buf.items) and Acc(list_pred(buf.items))`. There is NO
# half-permission Acc(x,1/2) read-only input — `view` carries no independent
# permission, only the aliasing constraint `view is buf.items`. So the classic
# half-permission frame-mutation probe (reject for INSUFFICIENT PERMISSION) does
# NOT apply here; see 'assessment'. The instance-specific analogue of a frame
# attack is the REBIND: a write that the permission system allows but that the
# identity postcondition must reject — that is the central uniqueness rival.

from pathlib import Path

INSTANCE = "pytest-dev__pytest-10051"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ----------------------------------------------------------------------------
# Region anchors. We edit ONLY text strictly inside the two # impl-start /
# # impl-end regions, so spec_signature (which masks impl regions) is unchanged
# => same_spec holds for every variant.
# ----------------------------------------------------------------------------

# discard_captured impl region (gold body): in-place empty, identity preserved.
_DISCARD_GOLD = (
    "    # impl-start\n"
    "    # buf.items.clear()  -- empty the existing list in place, preserving its\n"
    "    # object identity (and hence the observer's earlier reference to it).\n"
    "    empty_in_place(buf.items)\n"
    "    return\n"
    "    # impl-end"
)

# append_then_visible impl region (gold body).
_APPEND_GOLD = (
    "    # impl-start\n"
    "    buf.items.append(item)\n"
    "    return\n"
    "    # impl-end"
)


# ===========================================================================
# discard_captured rivals / controls
# ===========================================================================

# (S1) POSITIVE CONTROL (soundness): structurally-different but CORRECT impl.
# Reshape: take a local alias of the field, empty THROUGH the local, and assert
# the precondition alias to exhibit admissibility. Identity is still preserved
# (the field is never reassigned; empty_in_place preserves the pointed-to list's
# identity), so all three postcondition clauses hold. MUST verify.
_POS_DISCARD = _swap(
    _BASE,
    _DISCARD_GOLD,
    (
        "    # impl-start\n"
        "    # Structural reshape of the gold body: empty the list through a\n"
        "    # local alias of the field rather than naming the field inline.\n"
        "    # Identity is preserved because the field is never reassigned.\n"
        "    Assert(view is buf.items)  # admissibility: precond delivered the alias\n"
        "    lst = buf.items  # type: List[int]\n"
        "    empty_in_place(lst)\n"
        "    return\n"
        "    # impl-end"
    ),
)

# (S2) REBIND-ORPHANS (uniqueness, reject): the literal prepatch bug. Rebind the
# field to a BRAND-NEW empty list. Emptiness (len==0) holds, but the new list is
# a DIFFERENT object => Ensures(buf.items is Old(buf.items)) FAILS, and
# consequently Ensures(view is buf.items) FAILS (view still names the old list).
_REBIND_DISCARD = _swap(
    _BASE,
    _DISCARD_GOLD,
    (
        "    # impl-start\n"
        "    buf.items = []\n"
        "    return\n"
        "    # impl-end"
    ),
)

# (S3) CLEAR-THEN-REBIND (uniqueness, reject): do the real work (empty in place)
# but then throw away identity by rebinding to a fresh list. len==0 holds; the
# fresh list breaks identity (buf.items is Old(buf.items)) and the alias
# (view is buf.items). A "looks like it did the work" variant of the rebind bug.
_CLEAR_THEN_REBIND = _swap(
    _BASE,
    _DISCARD_GOLD,
    (
        "    # impl-start\n"
        "    empty_in_place(buf.items)\n"
        "    buf.items = []\n"
        "    return\n"
        "    # impl-end"
    ),
)

# (S4) NO-OP / PARTIAL-DOMAIN (uniqueness, reject): leave the list untouched.
# Identity is trivially preserved (buf.items is Old(buf.items) holds, view alias
# holds), but emptiness Ensures(len(buf.items) == 0) FAILS whenever the buffer
# held >= 1 captured item on entry (the F2P clears a non-empty 'call' list).
_NOOP_DISCARD = _swap(
    _BASE,
    _DISCARD_GOLD,
    (
        "    # impl-start\n"
        "    return\n"
        "    # impl-end"
    ),
)

# (S8) SELF-RECURSION (uniqueness, reject): the divergence loophole the earlier
# audit exploited. A bare self-call would, under partial correctness, satisfy
# every Ensures vacuously (the call's own contract discharges them) while the
# translated patch recurses forever (RecursionError / hang) and does NOT
# resolve. Rejected by the termination obligation: the callee's MustTerminate(2)
# measure is not strictly below the caller's remaining obligation, so Nagini's
# obligation leak check fails.
_RECURSE_DISCARD = _swap(
    _BASE,
    _DISCARD_GOLD,
    (
        "    # impl-start\n"
        "    discard_captured(buf, view)\n"
        "    return\n"
        "    # impl-end"
    ),
)

# (S9) WORK-THEN-RECURSE (uniqueness, reject): does the real work (in-place
# empty) and THEN self-recurses — the exact shape of the audit's
# atk_empty_then_recurse. Postconditions would all hold at the recursive call's
# contract, but the implementation never returns; rejected by the same
# obligation leak check.
_EMPTY_THEN_RECURSE = _swap(
    _BASE,
    _DISCARD_GOLD,
    (
        "    # impl-start\n"
        "    empty_in_place(buf.items)\n"
        "    discard_captured(buf, view)\n"
        "    return\n"
        "    # impl-end"
    ),
)


# ===========================================================================
# append_then_visible rivals / controls
# ===========================================================================

# (S5) POSITIVE CONTROL (soundness): structurally-different but CORRECT append
# through a local alias of the field. Visibility on both names still holds.
_POS_APPEND = _swap(
    _BASE,
    _APPEND_GOLD,
    (
        "    # impl-start\n"
        "    Assert(view is buf.items)  # admissibility: precond delivered the alias\n"
        "    lst = buf.items  # type: List[int]\n"
        "    lst.append(item)\n"
        "    return\n"
        "    # impl-end"
    ),
)

# (S6) WRONG-VALUE / PARTIAL-DOMAIN (uniqueness, reject): append a fixed 0 rather
# than the captured item. len==1 holds, but Ensures(buf.items[0] == item) (and
# view[0] == item) FAILS for every item != 0 — i.e. on all but one point of the
# value domain. The F2P logs a record whose message must round-trip exactly.
_WRONGVAL_APPEND = _swap(
    _BASE,
    _APPEND_GOLD,
    (
        "    # impl-start\n"
        "    buf.items.append(0)\n"
        "    return\n"
        "    # impl-end"
    ),
)

# (S7) REBIND-ON-APPEND (uniqueness, reject): replace the field with a fresh
# one-element list. The buffer ends up holding the item (len==1, items[0]==item)
# but the new list is a DIFFERENT object => the alias is orphaned, so
# Ensures(view is buf.items) and the view-visibility clauses
# (len(view)==1, view[0]==item) FAIL: view still names the old empty list.
_REBIND_APPEND = _swap(
    _BASE,
    _APPEND_GOLD,
    (
        "    # impl-start\n"
        "    fresh = [item]  # type: List[int]\n"
        "    buf.items = fresh\n"
        "    return\n"
        "    # impl-end"
    ),
)


SPEC_TESTS = [
    {
        "id": "pos-control-discard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DISCARD,
        "rationale": (
            "A structurally-different but correct discard (empty the list "
            "through a local alias of the field; the field is never reassigned "
            "so identity is preserved) must verify. The embedded "
            "Assert(view is buf.items) doubles as an ADMISSIBILITY witness: the "
            "precondition admits the F2P-shaped input (a buffer whose captured "
            "list is aliased by the observer reference). If this cannot verify "
            "the spec would be SPEC-TOO-STRONG / PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "rebind-orphans-discard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REBIND_DISCARD,
        "refinement": (
            "This is the prepatch bug verbatim: handler.reset() does "
            "self.records = [] (rebind to a fresh list). Its faithful real patch "
            "leaves LogCaptureFixture.clear routed to the rebinding reset, so the "
            "per-phase get_records('call') reference (stash[caplog_records_key]"
            "['call'], wired at logging.py:699) is orphaned — it keeps pointing "
            "at the OLD detached list. The F2P test_clear_for_call_stage asserts "
            "caplog.get_records('call') == [] after clear AND that a record "
            "logged after clear is visible through get_records('call'); with the "
            "rebind the orphaned reference still shows the pre-clear records and "
            "never sees the post-clear record => F2P FAILS. So a verifying rebind "
            "is a true verify-not-resolve break."
        ),
        "rationale": (
            "Rejected by the postcondition Ensures(buf.items is Old(buf.items)) "
            "(clause 2) and consequently Ensures(view is buf.items) (clause 3): "
            "the fresh list is a different object. This is the discriminating "
            "clause; model_prepatch.py fails here (G-DIFF)."
        ),
    },
    {
        "id": "clear-then-rebind-discard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _CLEAR_THEN_REBIND,
        "refinement": (
            "Empties in place (the real work) but then rebinds to a fresh empty "
            "list. Observationally identical to the prepatch rebind: the live "
            "field points at a NEW object, so the previously-handed-out "
            "get_records('call') reference is orphaned exactly as in "
            "rebind-orphans, and test_clear_for_call_stage FAILS (the post-clear "
            "record is never visible through the stale reference). Doing the work "
            "and then discarding identity does not resolve the F2P."
        ),
        "rationale": (
            "Rejected by Ensures(buf.items is Old(buf.items)) and "
            "Ensures(view is buf.items): the final value of buf.items is a fresh "
            "object distinct from Old(buf.items)."
        ),
    },
    {
        "id": "noop-discard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NOOP_DISCARD,
        "refinement": (
            "A clear that does nothing keeps identity (so it would pass the "
            "identity check) but leaves the captured records in place. The F2P "
            "logs 'a_call_log' before clear and asserts caplog.get_records"
            "('call') == [] AFTER clear; a no-op clear leaves get_records('call') "
            "== ['a_call_log'] (and the P2P test_clear asserts not "
            "len(caplog.records)) => F2P/P2P FAIL. A no-op patch does not resolve."
        ),
        "rationale": (
            "Rejected by Ensures(len(buf.items) == 0) (clause 1) on the "
            "non-empty sub-domain the F2P exercises: doing nothing leaves the "
            "pre-existing items in the list."
        ),
    },
    {
        "id": "recursion-discard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RECURSE_DISCARD,
        "refinement": (
            "A bare self-recursive discard never returns: its faithful real "
            "patch makes LogCaptureFixture.clear call itself, so any test that "
            "calls caplog.clear() (the F2P test_clear_for_call_stage does) "
            "hits infinite recursion (RecursionError) and FAILS — the patch "
            "does not resolve. Under partial correctness it would verify "
            "vacuously; the MustTerminate obligation rejects it."
        ),
        "rationale": (
            "Rejected by the termination obligation: the self-call cannot take "
            "the caller's unsatisfied MustTerminate(2) obligation (measure not "
            "strictly decreasing), so Nagini reports an obligation leak."
        ),
    },
    {
        "id": "empty-then-recurse-discard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _EMPTY_THEN_RECURSE,
        "refinement": (
            "Empties in place (the real work) and then self-recurses — the "
            "audit's atk_empty_then_recurse shape verbatim. The translated "
            "patch clears the records and then recurses forever inside "
            "caplog.clear(); the F2P test never gets past the clear() call "
            "(RecursionError), so the patch does not resolve."
        ),
        "rationale": (
            "Rejected by the termination obligation (obligation leak at the "
            "self-call), exactly as recursion-discard; doing the work first "
            "does not license divergence afterwards."
        ),
    },
    {
        "id": "pos-control-append",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_APPEND,
        "rationale": (
            "A structurally-different but correct capture (append through a "
            "local alias of the field) must verify; the alias guarantees the new "
            "item is visible on both buf.items and view. Embedded Assert is the "
            "admissibility witness for the post-discard precondition (aliased, "
            "empty). If it cannot verify the spec is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "wrongval-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WRONGVAL_APPEND,
        "refinement": (
            "Appends a fixed 0 instead of the captured item. The real "
            "LogCaptureHandler.emit appends the actual LogRecord; a patch that "
            "fabricated a different record would make the F2P assertion "
            "[x.message for x in caplog.get_records('call')] == "
            "['a_call_log_after_clear'] FAIL (the message would not round-trip). "
            "Correct on exactly one value point (item==0) and wrong on the rest "
            "of the domain, so it does not resolve."
        ),
        "rationale": (
            "Rejected by Ensures(buf.items[0] == item) and Ensures(view[0] == "
            "item): the appended value 0 does not equal an arbitrary item."
        ),
    },
    {
        "id": "rebind-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REBIND_APPEND,
        "refinement": (
            "Replaces the field with a fresh [item] list instead of appending. "
            "The buffer would hold the item, but the previously-handed-out "
            "observer reference (get_records('call')) is orphaned to the old "
            "empty list. The F2P checks the post-clear record THROUGH "
            "get_records('call'); with a rebinding emit that reference never sees "
            "the new record => F2P FAILS. Real emit never rebinds self.records."
        ),
        "rationale": (
            "Rejected by Ensures(view is buf.items), Ensures(len(view) == 1) and "
            "Ensures(view[0] == item): rebinding orphans `view`, which still "
            "names the old empty list (len 0)."
        ),
    },
]


# ===========================================================================
# Axiom lane: empty_in_place (A-consumed) == real list.clear().
# Reuse/strengthen axiom_check.py's logic. The runner mounts ONLY the probe at
# /work, so the probe is fully self-contained (stdlib only; list.clear is a
# builtin). apply_gold is irrelevant for a language builtin but set True for
# consistency with the post-gold call site (self.records.clear()).
# ===========================================================================

_AX_SOUND_PROBE = r'''
import random, sys

def check_clear_preserves_identity(elements):
    # axiom-soundness: real list.clear() empties in place (len==0) AND preserves
    # object identity (xs is Old(xs)); an alias taken before tracks the live list.
    xs = list(elements)
    xs_id = id(xs)
    alias = xs
    assert alias is xs
    xs.clear()                       # the REAL in-place emptying builtin
    assert len(xs) == 0, "list.clear() left %d elements" % len(xs)            # Ensures len==0
    assert id(xs) == xs_id, "list.clear() did not preserve object identity"   # Ensures xs is Old(xs)
    assert alias is xs, "alias diverged after clear()"
    assert len(alias) == 0, "alias does not see the cleared list as empty"
    xs.append(1234)
    assert alias is xs and len(alias) == 1 and alias[0] == 1234, (
        "alias does not track an item appended after clear()")

def check_rebind_orphans_alias(elements):
    # CONTRAST: the buggy rebind xs=[] does NOT preserve identity (negative
    # control proving the identity clause is the discriminating one).
    if not elements:
        return
    xs = list(elements)
    alias = xs
    xs = []
    assert alias is not xs, "rebind unexpectedly kept identity"
    assert len(alias) == len(elements), "old object should be unchanged by rebind"
    xs.append(1234)
    assert len(alias) == len(elements), (
        "orphaned alias should NOT see items appended to the rebound list")

def main():
    rng = random.Random(10051)
    boundary = [
        [],
        [0],
        [1, 2, 3],
        list(range(100)),
        [None, "x", 3.5, (1, 2)],
    ]
    for elements in boundary:
        check_clear_preserves_identity(elements)
        check_rebind_orphans_alias(elements)
    for _ in range(20000):
        n = rng.randint(0, 30)
        elements = [rng.randint(-1000, 1000) for _ in range(n)]
        check_clear_preserves_identity(elements)
        check_rebind_orphans_alias(elements)
    # del xs[:] is the documented equivalent of list.clear(): check it too.
    ys = [1, 2, 3]
    ys_id = id(ys)
    a2 = ys
    del ys[:]
    assert len(ys) == 0 and id(ys) == ys_id and a2 is ys, "del xs[:] not identity-preserving"
    print("axiom empty_in_place == real list.clear(): SOUND on 5 boundary + "
          "20000 fuzz inputs (len==0, identity preserved, alias tracks live "
          "list); del xs[:] equivalent confirmed; rebind contrast confirmed.")
    sys.exit(0)

main()
'''


_AX_COVER_PROBE = r'''
import sys
# axiom-containment: every input the MODEL can pass to empty_in_place lies in the
# axiom's Requires domain (Acc(list_pred(xs)) -- a well-formed list under full
# permission). The model calls empty_in_place EXACTLY once, in discard_captured,
# as empty_in_place(buf.items), where buf.items is a List[int] held under full
# permission Acc(buf.items) and Acc(list_pred(buf.items)) by the precondition.
# There is no other call site and no branch that constructs a different argument.
# So the entire reachable callee-input set is { a valid List[int] }, which is
# exactly the axiom's domain (a real list). Covering the int-list domain is the
# precise caller-reachable set (no float/None/other-type argument is reachable),
# so the axiom is neither too weak nor mis-scoped for the caller.
#
# We DEMONSTRATE the containment by enumerating the shapes the caller can reach
# (empty, singleton, many, heterogeneous standing in for List[int]) and asserting
# the real callee accepts each (it is total on lists -> in-domain).
cases = [
    [],
    [0],
    [1, 2, 3],
    list(range(100)),
    [None, "x", 3.5, (1, 2)],
]
for c in cases:
    xs = list(c)
    before = id(xs)
    xs.clear()                       # in-domain => accepted, no error
    assert len(xs) == 0 and id(xs) == before
print("axiom-containment OK: the only caller-reachable argument to "
      "empty_in_place is buf.items (a full-permission List[int]); every such "
      "input lies in the axiom's Requires domain (a valid list). No "
      "out-of-domain (float/None/non-list) argument is reachable from the model.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-empty_in_place",
        "axiom": "empty_in_place",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "empty_in_place is A-consumed for the real Python builtin "
            "list.clear() (the post-gold call self.records.clear()). The axiom "
            "Ensures len(xs)==0, Acc(list_pred(xs)), and the crux xs is Old(xs). "
            "If the real list.clear() ever left elements, changed object "
            "identity, or orphaned a pre-taken alias, the axiom would be "
            "AXIOM-UNSOUND. Fuzzes 5 boundary + 20000 random lists plus the "
            "documented del xs[:] equivalent; exits 0 iff every obligation holds."
        ),
    },
    {
        "id": "ax-cover-empty_in_place",
        "axiom": "empty_in_place",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "Containment: the model's only call site is "
            "empty_in_place(buf.items) in discard_captured, with buf.items a "
            "full-permission List[int]. Every caller-reachable argument is a "
            "valid list, which is exactly the axiom's Requires domain "
            "(Acc(list_pred(xs))). No float/None/non-list argument is reachable, "
            "so the axiom is not AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
]
