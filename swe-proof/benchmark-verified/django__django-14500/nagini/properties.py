# properties.py — PBT falsification battery for django__django-14500.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a FULL model.py variant that edits ONLY the impl region (so the
# frozen spec is byte-identical -> same_spec); Nagini verify decides verify/reject.
# Each AXIOM_TEST is a self-contained probe run in the instance Docker image with
# the gold patch applied; it CALLS the real post-gold callee and exits 0 iff the
# deep-model A-reference obligation holds.
#
# Defended surface (reasoned from model.py, not a corruption template):
#   keys_leaving_applied_set(own_key: int, replaced_keys: PSeq[int]) -> List[int]
#   Requires(True)                                  # maximally permissive
#   Ensures(Acc(list_pred(Result())))               # fresh list
#   Ensures(ToSeq(Result()) == replaced_keys + PSeq(own_key))   # LOAD-BEARING
#
# The load-bearing clause is a sequence equality GROUNDED ENTIRELY in the two
# args (no opaque @Pure oracle / answer-key to echo: the "oracle" literally IS
# `replaced_keys + PSeq(own_key)`), so there is no ungrounded-oracle echo class.
# There is also NO read-only heap input: own_key is an int VALUE and
# replaced_keys is a PSeq[int] mathematical VALUE (no Acc(...) permission to
# write through); the only heap object is the freshly-built Result(). So the
# frame-mutation class is N/A (justified in the parent 'assessment').
#
# The single discriminating behaviour the gold patch introduces (refinement A4):
# the migration's OWN key is recorded UNCONDITIONALLY (after the replaced-key
# loop) rather than only in the non-replacement `else:`. The F2P test
# test_migrate_marks_replacement_unapplied migrates 0001_squashed_0002 (which
# replaces 0001_initial + 0002_second, i.e. replaced_keys has length 2), unapplies
# it, and asserts the SQUASH (own) key is no longer in applied_migrations().
# Membership is a SET, so recording ORDER is invisible to the F2P observable; the
# genuine verify-not-resolve breaks therefore all key on the own-key recording.

from pathlib import Path

INSTANCE = "django__django-14500"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region of model.py (verified gold), copied verbatim so we can
# region-surgery against it. Editing ONLY between impl-start/impl-end keeps the
# spec view byte-identical (same_spec).
_GOLD_IMPL = """    result = []  # type: List[int]
    # For replacement migrations, record each replaced key as no-longer-applied,
    # in listed order.
    i = 0
    while i < len(replaced_keys):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(replaced_keys))
        # The recorded keys so far are exactly the first `i` replaced keys.
        Invariant(ToSeq(result) == replaced_keys.take(i))
        Invariant(MustTerminate(len(replaced_keys) - i + 1))
        # invariants-end
        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
        result = result + [replaced_keys[i]]
        i = i + 1
    Assert(replaced_keys.take(i) == replaced_keys)
    # Then record the migration's own key as no-longer-applied -- always.
    result = result + [own_key]
    return result"""

# Sanity: the gold impl text must appear verbatim in _BASE (else model.py drifted).
assert _GOLD_IMPL in _BASE, "gold impl region drifted from model.py"


def _with_impl(new_impl_body: str) -> str:
    """Return model.py with the gold impl body replaced by new_impl_body.
    Edits ONLY inside the impl region -> same_spec preserved."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl.
#    Local-variable reshape: bind the per-iteration key and the trailing own
#    key into named locals before appending. Keeps EVERY gold invariant/assert
#    (per pilot calibration #2/#3: do not touch the proof obligations the loop
#    needs; change only the executable shape). MUST verify -> else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_IMPL = """    result = []  # type: List[int]
    # Same build, reshaped: name the per-iteration replaced key and the trailing
    # own key in locals before appending (structural variant, same proof).
    i = 0
    while i < len(replaced_keys):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(replaced_keys))
        # The recorded keys so far are exactly the first `i` replaced keys.
        Invariant(ToSeq(result) == replaced_keys.take(i))
        Invariant(MustTerminate(len(replaced_keys) - i + 1))
        # invariants-end
        k = replaced_keys[i]
        Assert(replaced_keys.take(i) + PSeq(k) == replaced_keys.take(i + 1))
        result = result + [k]
        i = i + 1
    Assert(replaced_keys.take(i) == replaced_keys)
    tail = own_key
    result = result + [tail]
    return result"""

# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY — the precondition (Requires(True)) must admit a normal
#    F2P-shaped input AND the impl must be able to ESTABLISH the postcondition.
#    We keep the gold build and add an in-region self-check that the produced
#    sequence equals the pinned postcondition value, then return. If this cannot
#    verify the spec is unreachable/PRECOND-TOO-STRONG. MUST verify.
# ---------------------------------------------------------------------------
_ADMISS_IMPL = """    result = []  # type: List[int]
    i = 0
    while i < len(replaced_keys):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(replaced_keys))
        Invariant(ToSeq(result) == replaced_keys.take(i))
        Invariant(MustTerminate(len(replaced_keys) - i + 1))
        # invariants-end
        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
        result = result + [replaced_keys[i]]
        i = i + 1
    Assert(replaced_keys.take(i) == replaced_keys)
    result = result + [own_key]
    # admissibility self-check: the precondition admits this build and the
    # postcondition value is reachable for a normal (F2P-shaped) input.
    Assert(ToSeq(result) == replaced_keys + PSeq(own_key))
    return result"""

# ---------------------------------------------------------------------------
# 3. UNIQUENESS — the PRE-PATCH bug verbatim: own key recorded ONLY in the
#    `else:` (non-replacement) branch. For non-empty replaced_keys the result is
#    `replaced_keys` (no trailing own_key) -> postcondition
#    ToSeq(Result()) == replaced_keys + PSeq(own_key) FAILS. MUST reject.
# ---------------------------------------------------------------------------
_PREPATCH_IMPL = """    result = []  # type: List[int]
    if len(replaced_keys) > 0:
        i = 0
        while i < len(replaced_keys):
            # invariants-start
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(replaced_keys))
            Invariant(ToSeq(result) == replaced_keys.take(i))
            Invariant(MustTerminate(len(replaced_keys) - i + 1))
            # invariants-end
            Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
            result = result + [replaced_keys[i]]
            i = i + 1
        Assert(replaced_keys.take(i) == replaced_keys)
    else:
        result = result + [own_key]
    return result"""

# ---------------------------------------------------------------------------
# 4. UNIQUENESS — own key never recorded at all (only the replaced keys are
#    appended). result == replaced_keys for every input -> postcondition fails
#    (missing trailing own_key) even on empty replaced_keys ([] vs [own_key]).
#    MUST reject.
# ---------------------------------------------------------------------------
_OWN_OMITTED_IMPL = """    result = []  # type: List[int]
    i = 0
    while i < len(replaced_keys):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(replaced_keys))
        Invariant(ToSeq(result) == replaced_keys.take(i))
        Invariant(MustTerminate(len(replaced_keys) - i + 1))
        # invariants-end
        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
        result = result + [replaced_keys[i]]
        i = i + 1
    Assert(replaced_keys.take(i) == replaced_keys)
    return result"""

# ---------------------------------------------------------------------------
# 5. PARTIAL-DOMAIN — correct on the short sub-domain (len(replaced_keys) <= 1)
#    but wrong for len >= 2: the trailing own key is appended ONLY when there is
#    at most one replaced key. For length-0 and length-1 inputs the result is
#    correct; for length >= 2 (which is exactly the F2P witness, length 2) the
#    own key is dropped -> postcondition fails. MUST reject.
# ---------------------------------------------------------------------------
_PARTIAL_IMPL = """    result = []  # type: List[int]
    i = 0
    while i < len(replaced_keys):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(replaced_keys))
        Invariant(ToSeq(result) == replaced_keys.take(i))
        Invariant(MustTerminate(len(replaced_keys) - i + 1))
        # invariants-end
        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
        result = result + [replaced_keys[i]]
        i = i + 1
    Assert(replaced_keys.take(i) == replaced_keys)
    if len(replaced_keys) <= 1:
        result = result + [own_key]
    return result"""

# ---------------------------------------------------------------------------
# 6. UNIQUENESS (supporting) — over-recording: appends a SPURIOUS key not
#    derivable from the inputs (own_key + 1000) after the correct own key. The
#    pinned sequence has exactly the replaced keys followed by the single own
#    key, so this extra element -> postcondition fails. MUST reject.
# ---------------------------------------------------------------------------
_SPURIOUS_IMPL = """    result = []  # type: List[int]
    i = 0
    while i < len(replaced_keys):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(replaced_keys))
        Invariant(ToSeq(result) == replaced_keys.take(i))
        Invariant(MustTerminate(len(replaced_keys) - i + 1))
        # invariants-end
        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
        result = result + [replaced_keys[i]]
        i = i + 1
    Assert(replaced_keys.take(i) == replaced_keys)
    result = result + [own_key]
    result = result + [own_key + 1000]
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_IMPL),
        "rationale": (
            "structurally-different but behaviourally-identical impl (per-iteration "
            "replaced key and trailing own key bound to named locals before append) "
            "keeping every gold loop invariant/assert; must verify, else "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "admiss-self-check",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS_IMPL),
        "rationale": (
            "Requires(True) must admit a normal F2P-shaped input and the impl must "
            "be able to ESTABLISH the postcondition; the in-region "
            "Assert(ToSeq(result)==replaced_keys+PSeq(own_key)) self-check verifies, "
            "so the precondition is not too strong / the postcondition is reachable."),
    },
    {
        "id": "weak-prepatch-else-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PREPATCH_IMPL),
        "refinement": (
            "This is the PRE-PATCH branch verbatim: the own key is recorded only in "
            "the non-replacement `else:`. Its faithful real patch leaves the own-key "
            "record_unapplied inside the else, so a rolled-back REPLACEMENT migration "
            "(0001_squashed_0002, replaced_keys length 2) never records its own key -- "
            "the squash key stays in applied_migrations() and the F2P assertion "
            "assertNotIn(('migrations','0001_squashed_0002'), applied) FAILS. Does NOT "
            "resolve."),
        "rationale": (
            "rejected by Ensures(ToSeq(Result())==replaced_keys+PSeq(own_key)): for "
            "non-empty replaced_keys the result is replaced_keys (missing the trailing "
            "own_key). Discriminating clause A4 (unconditional own-key append)."),
    },
    {
        "id": "weak-own-omitted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_OWN_OMITTED_IMPL),
        "refinement": (
            "The own key is NEVER recorded (only the replaced keys are appended). Its "
            "faithful real patch drops self.recorder.record_unapplied(migration.app_label, "
            "migration.name) entirely, so the squash key is never marked unapplied and "
            "the F2P assertNotIn FAILS for every replacement migration. Does NOT resolve."),
        "rationale": (
            "rejected by the postcondition: result == replaced_keys on every input "
            "(even empty: [] vs the required [own_key]); the trailing PSeq(own_key) is "
            "absent."),
    },
    {
        "id": "weak-partial-domain-len2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_IMPL),
        "refinement": (
            "Correct on the short sub-domain (len(replaced_keys) <= 1: 0 or 1 replaced "
            "key) but drops the own-key append for len >= 2. The F2P witness "
            "0001_squashed_0002 replaces TWO migrations (0001_initial + 0002_second), so "
            "replaced_keys length is exactly 2: its faithful real patch (own key recorded "
            "only when there are at most one replaced key) never records the squash's own "
            "key, the squash stays applied and the F2P assertNotIn FAILS. Does NOT resolve."),
        "rationale": (
            "rejected by the postcondition on the length>=2 sub-domain: result == "
            "replaced_keys (no trailing own_key), so it does not equal "
            "replaced_keys+PSeq(own_key)."),
    },
    {
        "id": "weak-spurious-extra-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_SPURIOUS_IMPL),
        "refinement": (
            "Over-recording (supporting case): records an extra key (own_key+1000) not "
            "derivable from the inputs. Its faithful real patch issues an extra "
            "record_unapplied for an unrelated migration that was not part of this "
            "roll-back, marking an unrelated migration unapplied -- corrupting the "
            "applied set beyond what the roll-back should touch (would break the "
            "applied-set bookkeeping the P2P state tests rely on). Does NOT resolve."),
        "rationale": (
            "rejected by the exact sequence equality: the pinned sequence is "
            "replaced_keys followed by the SINGLE own key; the extra trailing element "
            "makes ToSeq(Result()) longer than replaced_keys+PSeq(own_key)."),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — this bundle consumes NO @ContractOnly axiom, but it HAS an
# A-reference deep model: keys_leaving_applied_set is validated == the REAL
# post-gold unapply_migration recording branch (meta.deep_model_references,
# G-AX / axiom_check.py). The probe below re-establishes that A-reference by
# CALLING the real callee (pilot calibration #4: never scrape source).
#
# It drives the REAL post-gold MigrationExecutor.unapply_migration with fake=True
# (which skips the `if not fake:` schema-editor block, so no DB/connection is
# touched) on a capturing recorder stub, captures the actual ordered sequence of
# record_unapplied(app_label, name) calls, and asserts it equals the deep model's
# build (each replaced key in order, then the own key UNCONDITIONALLY) over the
# F2P witness + boundary + exhaustive small enumeration + randomized fuzz. It
# also confirms the pre-patch differential is real (own key would stay applied if
# recorded only in the else). Containment: every callee input the model can reach
# (own_key any int, replaced_keys any finite int sequence -- Requires(True)) is in
# the real branch's domain, which accepts any (app_label,name) pair sequence.
# stdlib-only; opens nothing; exits 0 iff every observation matches.
# ---------------------------------------------------------------------------

_AXIOM_PROBE = r'''
import itertools
import random
import sys

# Real post-gold callee lives in the instance image with the gold patch applied.
from django.db.migrations.executor import MigrationExecutor


class _CapturingRecorder(object):
    """Stub MigrationRecorder: record_unapplied(app, name) just captures the call."""
    def __init__(self):
        self.calls = []

    def record_unapplied(self, app_label, name):
        self.calls.append((app_label, name))


def _as_key(k):
    """Normalise a model-level key to the real callee's (app_label, name) pair.

    The deep model abstracts a migration key to a single int code; the REAL
    unapply_migration recording branch (`for app_label, name in migration.replaces`
    and `record_unapplied(migration.app_label, migration.name)`) requires a
    2-tuple (app_label, name). The F2P witness already supplies (app_label, name)
    tuples directly; the exhaustive/fuzz lanes supply bare int codes. Map a bare
    int code injectively onto a canonical ("c", str(code)) pair so it drives the
    real branch through the same control flow, and pass through anything that is
    already a 2-tuple unchanged. The mapping is a bijection on the captured
    sequence, so the per-call equality (real == model) is preserved."""
    if isinstance(k, tuple):
        return k
    return ("c", str(k))


class _FakeMigration(object):
    """Minimal stand-in for a migration: only the attributes the recording branch
    of unapply_migration touches (replaces, app_label, name, atomic)."""
    def __init__(self, own, replaces):
        own_key = _as_key(own)
        self.app_label = own_key[0]
        self.name = own_key[1]
        self.replaces = [_as_key(r) for r in replaces]
        self.atomic = True

    def unapply(self, state, schema_editor):  # not reached with fake=True
        return state


def real_recorded(own, replaces):
    """Run the REAL post-gold unapply_migration recording branch (fake=True skips
    the schema-editor block, so no connection/DB is needed) and return the ordered
    list of record_unapplied(app_label, name) calls it issues, re-projected back to
    the model's key space so it is directly comparable to model_recorded()."""
    exe = object.__new__(MigrationExecutor)  # bypass __init__ (needs a connection)
    exe.recorder = _CapturingRecorder()
    exe.progress_callback = None
    mig = _FakeMigration(own, replaces)
    # Call the REAL method (unbound) on our stub executor; fake=True -> no schema work.
    MigrationExecutor.unapply_migration(exe, None, mig, fake=True)
    # Invert _as_key so the captured (app_label, name) calls compare against the
    # original model-level keys (ints stay ints; genuine tuple keys stay tuples).
    forward = {}
    for k in list(replaces) + [own]:
        forward[_as_key(k)] = k
    return [forward[call] for call in exe.recorder.calls]


def model_recorded(own, replaces):
    """The deep-model keys_leaving_applied_set build (model.py): each replaced key
    in listed order, then the own key UNCONDITIONALLY."""
    result = []
    for k in replaces:
        result = result + [k]
    result = result + [own]
    return result


def buggy_recorded(own, replaces):
    """The PRE-patch branch: own key only in the else (non-replacement) case."""
    recorded = []
    if replaces:
        for k in replaces:
            recorded.append(k)
    else:
        recorded.append(own)
    return recorded


def check(own, replaces):
    real = real_recorded(own, replaces)
    model = model_recorded(own, replaces)
    assert real == model, (
        "A-reference UNSOUND: real post-gold unapply_migration recorded %r but the "
        "deep model recorded %r for own=%r replaces=%r" % (real, model, own, replaces))
    # discriminating property: own key is recorded unconditionally.
    assert own in real, "own key %r not recorded by real branch for replaces=%r" % (own, replaces)
    for k in replaces:
        assert k in real, "replaced key %r not recorded for own=%r" % (k, own)


def main():
    # --- F2P witness: 0001_squashed_0002 replaces 0001_initial + 0002_second ---
    own = ("migrations", "0001_squashed_0002")
    rep = [("migrations", "0001_initial"), ("migrations", "0002_second")]
    real = real_recorded(own, rep)
    assert real == rep + [own], ("F2P witness mismatch:", real)
    assert own in set(real), "F2P: squash own key must be recorded (leaves applied set)"
    # pre-patch differential is real: the buggy branch would NOT record the own key.
    assert own not in set(buggy_recorded(own, rep)), (
        "differential broken: buggy branch should omit the squash own key")
    check(own, rep)

    # non-replacement migration: records only its own key.
    assert real_recorded(("a", "0001"), []) == [("a", "0001")]
    check(("a", "0001"), [])

    # --- exhaustive small enumeration over an integer-coded key universe -------
    # (the model abstracts (app_label,name) pairs to int codes; any hashable key
    # exercises the same control flow). own x replaced-lists length 0..4 over 5 keys.
    universe = [0, 1, 2, 3, 4]
    for o in universe:
        for length in range(0, 5):
            for reps in itertools.product(universe, repeat=length):
                check(o, list(reps))

    # --- randomized fuzz (caller-reachable domain: any int own, any finite seq) -
    rng = random.Random(14500)
    for _ in range(20000):
        o = rng.randint(-50, 50)
        n = rng.randint(0, 10)
        reps = [rng.randint(-50, 50) for _ in range(n)]
        check(o, reps)

    print("AX OK: real post-gold unapply_migration recording branch == deep model "
          "keys_leaving_applied_set (each replaced key, then own key unconditionally) "
          "on F2P witness + boundary + exhaustive (own x len0-4 over 5 keys) + 20000 "
          "fuzz; pre-patch differential confirmed (own key omitted by the buggy else).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "ax-aref-unapply-recording",
        "axiom": "keys_leaving_applied_set",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_PROBE,
        "rationale": (
            "A-reference deep-model soundness: drives the REAL post-gold "
            "MigrationExecutor.unapply_migration recording branch (fake=True, capturing "
            "recorder stub) and asserts the captured record_unapplied sequence equals "
            "the deep model's build (each replaced key in order, then the own key "
            "unconditionally) on the F2P witness + boundary + exhaustive + 20000 fuzz. "
            "Any disagreement => the deep model is not a faithful reference of the real "
            "fixed branch."),
    },
    {
        "id": "ax-aref-containment",
        "axiom": "keys_leaving_applied_set",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AXIOM_PROBE,
        "rationale": (
            "Containment: the model's Requires(True) lets the caller reach own_key = "
            "any int and replaced_keys = any finite int sequence; the real "
            "unapply_migration recording branch accepts any (app_label,name) key and any "
            "iterable migration.replaces, so every caller-reachable input lies in the "
            "real branch's domain (the same probe enumerates own x replaced-lists "
            "length 0-4 plus fuzz over that whole reachable domain and the real callee "
            "agrees on each). No reachable input is outside the covered domain."),
    },
]
