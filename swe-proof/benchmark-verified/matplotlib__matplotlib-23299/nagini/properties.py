"""properties.py — PBT falsification battery for matplotlib__matplotlib-23299.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only the
# impl-start .. # impl-end region is edited via _swap) and are checked by Nagini
verify + markers.same_spec. There is NO @ContractOnly axiom in this bundle
(meta.axioms == []); the snapshot / distinguished-key drop / per-key revert is
modelled DEEPLY over a real Dict[int,int] and validated == the CPython dict
copy/del/update primitives (an A-reference) by axiom_check.py. AXIOM_TESTS
therefore carries a single A-reference soundness probe (self-contained: it
reproduces the gold patch's exact control flow over a real dict and asserts the
frozen postconditions on boundary + fuzz inputs, embedding axiom_check.py's
logic so no bundle file need be mounted in-container).

DEFENDED SURFACE (why these cases and not byte-fuzz):
  restore_after_temporary_overrides(params, entry_resolved, entry_other,
                                    new_resolved, other_override) -> None
  models the rc_context() save->body->revert lifecycle. `params` is a
  Dict[int,int] held at FULL permission (Acc(dict_pred(params))) because it is
  GENUINELY MUTATED in place (the live rcParams). The four load-bearing
  postcondition clauses:
    (1) SURVIVE   params[key_resolved()] == new_resolved   (the FIX: the
        distinguished 'backend' key keeps the body-set value; NOT reverted)
    (2) REVERT    params[key_other()] == entry_other       (an ordinary key is
        reverted to its entry value)
    (3) NO-SPURIOUS  Forall k: k in params ==> Old(k in params)
    (4) FRAME/FULL-REVERT  Forall k: k in params and k != key_resolved()
        ==> params[k] == Old(params[k])   (every NON-distinguished pre-existing
        key is reverted to its entry value -- closes the third-key scope hole)

  FRAME-MUTATION (directive 5 / project #1 weakness class) — IS IT APPLICABLE?
  The classic frame-mutation attack (overwrite a half-permission read-only input
  Acc(x,1/2) to satisfy a postcondition vacuously, expecting rejection for
  INSUFFICIENT PERMISSION) does NOT apply here: there is NO Acc(x,1/2) read-only
  input. `params` is the only heap object and it is held at FULL permission by
  design (it is the thing the function mutates). has_readonly_input = False, so
  frame_mutation_included is vacuously satisfied. The ANALOG of a frame
  condition for a full-permission mutated mapping is postcondition clause (4)
  (the explicit full-revert Forall), and that IS attacked below by the
  corrupt-third-key rival (weak-corrupt-third-key) — a write to a pre-existing
  key the contract requires to be framed/reverted. So the frame surface is
  defended and adversarially probed; it is just not the half-permission variant.

  UNGROUNDED-ORACLE ECHO — NOT APPLICABLE. The postcondition pins outputs to
  new_resolved / entry_other / Old(params[k]) — all GROUNDED in the args and the
  pre-state (no opaque @Pure answer-key to echo). key_resolved()/key_other() are
  constants (0/1), not a function of the secret answer. There is no "wrong echo"
  to build; per directive 2 we instead carry honest structurally-different
  positive controls (pos-reorder-writes, pos-local-rename).

  The genuine uniqueness attacks are: reverting the distinguished key (the
  PRE-patch bug, fails SURVIVE); not reverting / wrong-reverting an ordinary key
  (fails REVERT); and corrupting a third pre-existing key (fails the FRAME/
  no-spurious clauses). Each carries the refinement argument that its faithful
  real patch would NOT resolve the F2P/P2P.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23299"
FLOAT_ENCODING = None  # meta.float_encoding is null; integer key/value tokens, no --float-encoding

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl region, anchored on unique substrings inside
# # impl-start .. # impl-end. Every variant edits ONLY here -> same_spec holds.
# ---------------------------------------------------------------------------

# The entire gold impl body (between the markers, markers excluded). We rebuild
# it per variant by surgically replacing one of the anchors below.
_GOLD_SNAPSHOT = """    saved = {}  # type: Dict[int, int]
    saved[key_other()] = params[key_other()]"""

_GOLD_BODY_WRITES = """    params[key_resolved()] = new_resolved
    params[key_other()] = other_override"""

_GOLD_REVERT = """    if key_other() in saved:
        params[key_other()] = saved[key_other()]"""


# === POSITIVE CONTROL 1 (soundness, must verify) ===========================
# Structurally-different CORRECT impl: REORDER the two body writes (ordinary key
# written first, then the distinguished key). Identical net pre-revert state,
# different statement order. No invariant/lemma is involved (straight-line
# assignment), so this is a safe reshape (directives 2/3 N/A — there is no loop
# or fold). Must verify; else SPEC-TOO-STRONG.
_POS1_BODY_WRITES = """    params[key_other()] = other_override
    params[key_resolved()] = new_resolved"""


# === POSITIVE CONTROL 2 (soundness, must verify) ===========================
# Local-variable RESHAPE: bind the ordinary key's entry value to a typed local
# before recording it into the snapshot dict, and revert from that same local.
# Same data flow, different local structure. Must verify; else SPEC-TOO-STRONG.
_POS2_SNAPSHOT = """    snap_other = params[key_other()]  # type: int
    saved = {}  # type: Dict[int, int]
    saved[key_other()] = snap_other"""


# === ADMISSIBILITY (precondition not too strong, must verify) ==============
# Insert, at the very top of the impl, Asserts of facts that the Requires must
# make available for a normal F2P-shaped input (both observed keys present, the
# distinguished key distinct from the ordinary key, the pinned entry values).
# If the precondition were unsatisfiable / contradictory (vacuously False), the
# whole spec would be degenerate; these Asserts confirm the Requires admits a
# normal input. The gold impl is left intact, so the postcondition still holds.
_ADMISS_INSERT = """    Assert(key_resolved() in params)
    Assert(key_other() in params)
    Assert(key_resolved() != key_other())
    Assert(params[key_resolved()] == entry_resolved)
    Assert(params[key_other()] == entry_other)
    saved = {}  # type: Dict[int, int]
    saved[key_other()] = params[key_other()]"""


# === UNIQUENESS rivals (must be REJECTED) ==================================

# --- weak-revert-distinguished: the PRE-patch bug. The snapshot ALSO records
# the distinguished key, and the revert writes its entry value back, so the
# body-set value does NOT survive. Fails postcondition (1) SURVIVE.
_REVERT_DISTINGUISHED_SNAPSHOT = """    saved = {}  # type: Dict[int, int]
    saved[key_resolved()] = params[key_resolved()]
    saved[key_other()] = params[key_other()]"""
_REVERT_DISTINGUISHED_REVERT = """    if key_resolved() in saved:
        params[key_resolved()] = saved[key_resolved()]
    if key_other() in saved:
        params[key_other()] = saved[key_other()]"""

# --- weak-no-revert-ordinary: the ordinary key is NEVER reverted; it keeps the
# body's temporary override value. Fails postcondition (2) REVERT.
_NO_REVERT = """    if key_other() in saved:
        params[key_other()] = params[key_other()]"""

# --- weak-revert-wrong-value: the ordinary key is "reverted" to new_resolved
# (the distinguished body value) instead of its snapshotted entry value. A
# partial-domain rival: correct only on the sub-domain new_resolved == entry_other.
# Fails postcondition (2) on the generic input.
_REVERT_WRONG = """    if key_other() in saved:
        params[key_other()] = new_resolved"""

# --- weak-corrupt-third-key: the gold impl PLUS a write to a third key token
# (key 2, a non-distinguished key the contract requires to be framed). This is
# the FRAME-CONDITION analog probe for a full-permission mutated mapping: it
# corrupts a pre-existing non-backend key (if 2 was present on entry it now
# violates clause (4); if 2 was absent it now violates clause (3)). Fails the
# FRAME/no-spurious postcondition either way.
_CORRUPT_THIRD = """    if key_other() in saved:
        params[key_other()] = saved[key_other()]
    params[2] = 999"""


SPEC_TESTS = [
    # ----- soundness / positive controls (must verify) --------------------
    {
        "id": "pos-reorder-writes",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_BODY_WRITES, _POS1_BODY_WRITES),
        "rationale": (
            "structurally-different CORRECT impl: the two body writes are "
            "REORDERED (ordinary key first, distinguished key second). The "
            "pre-revert state is identical, the revert is unchanged, so all four "
            "postcondition clauses still hold. Straight-line assignment, no loop "
            "invariant or fold lemma involved (directives 2/3 N/A). Must verify; "
            "if not, SPEC-TOO-STRONG (the spec would reject a trivially-correct "
            "reordering of the gold impl)."
        ),
    },
    {
        "id": "pos-local-rename",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_SNAPSHOT, _POS2_SNAPSHOT),
        "rationale": (
            "local-variable RESHAPE positive control: the ordinary key's entry "
            "value is bound to a typed local (snap_other) before being recorded "
            "into the snapshot dict; the revert still reads from saved. Same data "
            "flow, different local structure. Keeps the gold revert/body intact, "
            "so the postcondition is still discharged. Must verify; else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-requires-facts",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_SNAPSHOT, _ADMISS_INSERT),
        "rationale": (
            "admissibility: Asserts (at the top of the impl) the Requires-derived "
            "facts for a normal F2P-shaped input -- both observed keys present, "
            "the distinguished key distinct from the ordinary key, and the pinned "
            "entry values. These must be provable from the precondition, "
            "confirming the Requires admits a normal input (else the precondition "
            "would be vacuously False / contradictory => PRECOND-TOO-STRONG). The "
            "gold snapshot/body/revert is preserved, so the postcondition still "
            "verifies. Must verify."
        ),
    },
    # ----- uniqueness rivals (must be rejected) ---------------------------
    {
        "id": "weak-revert-distinguished",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _GOLD_SNAPSHOT, _REVERT_DISTINGUISHED_SNAPSHOT),
            _GOLD_REVERT, _REVERT_DISTINGUISHED_REVERT,
        ),
        "refinement": (
            "this IS the PRE-patch (model_prepatch.py shape): the snapshot keeps "
            "the distinguished key and the exit-time revert (dict.update over the "
            "full snapshot) writes its stale entry value back. Its faithful real "
            "patch is exactly the pre-patch code (orig = rcParams.copy() with no "
            "`del orig['backend']`), which FAILS FAIL_TO_PASS "
            "test_no_backend_reset_rccontext: rcParams['backend'] set to "
            "'module://aardvark' inside rc_context() is reverted to the stale "
            "value on exit. A verifying rival here would be a true "
            "verify-but-not-resolve break."
        ),
        "rationale": (
            "rejected by postcondition (1) SURVIVE: params[key_resolved()] is "
            "reverted to entry_resolved, but the Ensures requires it to equal "
            "new_resolved; these differ whenever new_resolved != entry_resolved "
            "(the F2P scenario). Rejection comes from the survive clause, not from "
            "any framing/permission issue."
        ),
    },
    {
        "id": "weak-no-revert-ordinary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_REVERT, _NO_REVERT),
        "refinement": (
            "the ordinary key is never reverted -- it keeps the body's temporary "
            "override value across the exit. A faithful real patch that omitted "
            "`dict.update(rcParams, orig)` (or never snapshotted the ordinary "
            "keys) leaves every non-backend rcParam permanently mutated by the "
            "context body, which FAILS PASS_TO_PASS test_rcparams_reset_after_fail "
            "(rc_context must restore the ordinary rcParams to their entry values "
            "on exit/failure). verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition (2) REVERT: params[key_other()] ends at "
            "other_override (the body value), but the Ensures requires entry_other; "
            "these differ whenever other_override != entry_other. Also fails the "
            "FRAME clause (4) for k == key_other(). Rejection comes from the "
            "revert/frame clauses."
        ),
    },
    {
        "id": "weak-revert-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_REVERT, _REVERT_WRONG),
        "refinement": (
            "a PARTIAL-DOMAIN rival: the ordinary key is 'reverted' to "
            "new_resolved (the distinguished body value) instead of its "
            "snapshotted entry value -- correct only on the measure-zero "
            "sub-domain new_resolved == entry_other. A faithful real patch that "
            "wrote the wrong saved value into a non-backend rcParam on revert "
            "would corrupt that setting, failing PASS_TO_PASS "
            "test_rcparams_reset_after_fail on any input where the body value "
            "differs from the entry value. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition (2) REVERT: params[key_other()] == "
            "new_resolved but the Ensures requires entry_other; for a generic "
            "input new_resolved != entry_other so the clause fails. (Also fails "
            "FRAME clause (4) for k == key_other().) The spec pins the EXACT "
            "reverted value, not merely 'some revert happened'."
        ),
    },
    {
        "id": "weak-corrupt-third-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_REVERT, _CORRUPT_THIRD),
        "refinement": (
            "the FRAME-condition probe for a full-permission mutated mapping: the "
            "gold impl PLUS a write `params[2] = 999` to a third, non-distinguished "
            "key. A faithful real patch whose revert corrupts (or introduces) a "
            "non-backend rcParam other than the two observed keys would leave that "
            "setting at a garbage value after the context exits, FAILING "
            "PASS_TO_PASS test_rcparams_reset_after_fail (which asserts the FULL "
            "set of ordinary rcParams is restored to its entry state, not just one "
            "key). This is exactly the third-key scope-loss the gold's full-"
            "snapshot revert prevents. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by the FRAME/no-spurious clauses: if key 2 was present on "
            "entry, postcondition (4) requires params[2] == Old(params[2]) but the "
            "rival makes it 999; if key 2 was absent on entry, postcondition (3) "
            "requires `2 in params ==> Old(2 in params)` which now fails. Either "
            "way the verifier cannot discharge clauses (3)/(4). This is the "
            "frame-defense (clause 4) doing its job for the full-permission "
            "mutated mapping -- the analog of the half-permission frame-mutation "
            "reject for a read-only input."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane: NO @ContractOnly axiom (meta.axioms == []). The only callees are
# CPython dict copy/del/update -- an A-reference deep model. Per PBT_PLAN §2.4 /
# §4a, an A-reference deep model is checked the same way as an axiom: the real
# primitive must equal the deep model on every caller-reachable input. The probe
# below is SELF-CONTAINED (stdlib only) and reproduces the gold patch's exact
# control flow over a real dict (snapshot -> drop distinguished key -> body
# override -> dict.update revert), asserting model.py's frozen postconditions
# (1) survive, (2) revert, (3) no spurious key, AND (4) the FRAME/full-revert
# clause on boundary + 20000 fuzz inputs, including mappings carrying extra
# untouched keys (the caller-reachable third-key domain). It exits 0 iff every
# obligation holds. This is axiom_check.py's logic embedded directly so no
# bundle file need be mounted in-container (directive 6).
# ---------------------------------------------------------------------------

_AREF_PROBE = r'''
import random
import sys

# model.py constants (lock-step with the pure region: key_resolved/key_other).
KEY_RESOLVED = 0   # distinguished key ('backend')
KEY_OTHER = 1      # representative ordinary key


def real_restore(params, new_resolved, other_override):
    # The gold patch's exact control flow over a REAL dict:
    #   orig = dict(rcParams.copy()); del orig['backend']
    #   <body overrides keys>; dict.update(rcParams, orig)
    orig = dict(params.copy())
    if KEY_RESOLVED in orig:
        del orig[KEY_RESOLVED]          # del orig['backend'] -- the fix
    params[KEY_RESOLVED] = new_resolved
    params[KEY_OTHER] = other_override
    dict.update(params, orig)


def check(params, new_resolved, other_override):
    old = dict(params)
    entry_other = old[KEY_OTHER]
    real_restore(params, new_resolved, other_override)
    # (1) survive: distinguished key keeps the body-set value.
    assert KEY_RESOLVED in params and params[KEY_RESOLVED] == new_resolved, (
        "survive: %r != %r" % (params.get(KEY_RESOLVED, "<absent>"), new_resolved))
    # (2) revert: ordinary key reverted to its entry value.
    assert KEY_OTHER in params and params[KEY_OTHER] == entry_other, (
        "revert: %r != %r" % (params.get(KEY_OTHER, "<absent>"), entry_other))
    # (3) no spurious key: every exit key was an entry key.
    for k in params:
        assert k in old, "spurious key %r" % (k,)
    # (4) FRAME/full-revert: every NON-distinguished entry key reverted to its
    #     entry value (and none dropped).
    for k in old:
        if k != KEY_RESOLVED:
            assert k in params and params[k] == old[k], (
                "frame: key %r is %r, expected %r"
                % (k, params.get(k, "<absent>"), old[k]))


def main():
    AUTO, AARDVARK = 100, 200
    boundary = [
        (AUTO, 5, AARDVARK, 7),   # F2P: body overrides distinguished -> survives
        (AUTO, 5, AUTO, 7),
        (AARDVARK, 5, AUTO, 7),
        (3, 3, 3, 3),
        (3, 4, 5, 6),
        (-1, -2, -3, -4),
        (0, 0, 0, 0),
    ]
    for er, eo, nr, oo in boundary:
        check({KEY_RESOLVED: er, KEY_OTHER: eo}, nr, oo)
    # mappings carrying extra untouched keys -- the caller-reachable third-key
    # domain the FRAME clause (4) defends.
    for er, eo, nr, oo in boundary:
        params = {KEY_RESOLVED: er, KEY_OTHER: eo, 9: 90, 10: 100}
        old = dict(params)
        real_restore(params, nr, oo)
        assert params[KEY_RESOLVED] == nr
        assert params[KEY_OTHER] == eo
        assert params[9] == old[9] and params[10] == old[10], "frame extra keys"
        for k in params:
            assert k in old, "spurious key %r" % (k,)
    rng = random.Random(23299)
    for _ in range(20000):
        er = rng.randint(-50, 50)
        eo = rng.randint(-50, 50)
        nr = rng.randint(-50, 50)
        oo = rng.randint(-50, 50)
        params = {KEY_RESOLVED: er, KEY_OTHER: eo}
        for _ in range(rng.randint(0, 4)):
            params[rng.randint(2, 30)] = rng.randint(-50, 50)
        check(params, nr, oo)
    print("A-REF OK: deep model (snapshot + distinguished-key drop + per-key "
          "revert) == real dict copy/del/update on %d boundary + 20000 fuzz "
          "cases; survive + revert + no-spurious + FRAME all hold" % len(boundary))
    sys.exit(0)


main()
'''

AXIOM_TESTS = [
    {
        "id": "aref-dict-primitives-sound",
        "axiom": "restore_after_temporary_overrides deep model (dict copy/del/update A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AREF_PROBE,
        "rationale": (
            "There is no @ContractOnly axiom; the only callees are CPython dict "
            "copy/del/update, modelled DEEPLY as an A-reference. The deep model "
            "must equal the real dict primitives on every caller-reachable input. "
            "The probe reproduces the gold patch's exact control flow over a real "
            "dict and asserts model.py's frozen postconditions (survive / revert / "
            "no-spurious / FRAME full-revert) on boundary + fuzz inputs, including "
            "mappings with extra untouched keys (the third-key domain clause (4) "
            "defends). Exit 0 iff the A-reference is sound; any violation => the "
            "deep model diverges from the real primitives. Stdlib-only and "
            "self-contained (directive 6); calls the real dict ops, never scrapes "
            "source (directive 4)."
        ),
    },
]
