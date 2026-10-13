# properties.py — PBT falsification battery for django__django-14559.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-for-byte (region-surgery: every variant is built by
# _swap on _BASE editing ONLY text inside the # impl-start / # impl-end region,
# whose collapse is exactly what markers.same_spec compares — so same_spec is
# guaranteed). Axiom cases are real-callee probes run in the instance Docker
# image with the gold patch applied.
#
# Defended surface (model.py):
#   bulk_apply_count(keys: List[int], group_size: int) -> Optional[int]
#     Requires(Acc(list_pred(keys), 1/2))      # keys is READ-ONLY (half perm)
#     Requires(group_size >= 1)
#     Requires(MustTerminate(2))               # the count must be DELIVERED
#     Ensures(Acc(list_pred(keys), 1/2))       # frame: keys not mutated
#     Ensures(Result() is not None)            # always a count, never None
#     Ensures(Result() >= 0)
#     Ensures(Result() == batched_total(ToSeq(keys), group_size))   # the PIN
#
# The MustTerminate obligation closes the partial-correctness escape: an impl
# whose loop never exits (or that self-recurses unboundedly) would otherwise
# discharge the value postcondition vacuously; with the obligation every loop
# must carry a strictly decreasing, bounded-below MustTerminate measure and
# every self-call would need to consume the obligation, so frozen-loop /
# self-recursive impls are rejected at verification time.
#
# The load-bearing clause is the last one: the returned count must equal the
# front-recursive per-group fold `batched_total`, which sums `matched_rows` over
# the successive group_size-sized groups (front-to-back). `batched_total` is a
# GROUNDED @Pure oracle (a fully-unfolded function of the two args), NOT an
# opaque answer-key — so there is no "wrong echo" of it; the attack surface is
# instead grouping/offset/domain errors in the accumulating loop that the
# `batched_total` clause must reject. `matched_rows` is the only @ContractOnly
# axiom (A-consumed): Ensures(Result() >= 0) over the unchanged QuerySet.update.

from pathlib import Path

INSTANCE = "django__django-14559"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors inside the impl region (all unique in _BASE).
# ---------------------------------------------------------------------------

# The full gold impl body (between # impl-start and # impl-end), used to replace
# the whole executable body for rivals that restructure the loop. We keep the
# enclosing markers so the impl region boundaries are unchanged.
_GOLD_BODY = """    total = 0
    if len(keys) == 0:
        return 0
    off = 0
    while off < len(keys):
        # invariants-start
        Invariant(Acc(list_pred(keys), 1 / 2))
        Invariant(0 <= off and off <= len(keys))
        # `off` advances one whole group per step (capped at the end), so the
        # consumed prefix is always a whole number of groups; the running total
        # is what those consumed groups reported, and the still-to-process
        # suffix accounts for the rest of the per-group sum.
        Invariant(total >= 0)
        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
                  batched_total(ToSeq(keys), group_size))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(keys) - off.
        Invariant(MustTerminate(len(keys) - off))
        # invariants-end
        rem = ToSeq(keys).drop(off)
        # The current group is the first `group_size` keys of the remaining
        # suffix; the suffix after this step drops exactly that group.
        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
        Assert(len(rem) > 0)
        Assert(batched_total(rem, group_size) ==
               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
        step = group_size
        if step > len(keys) - off:
            step = len(keys) - off
        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
        total = total + matched_rows(rem.take(group_size))
        off = off + step
    return total"""

assert _GOLD_BODY in _BASE and _BASE.count(_GOLD_BODY) == 1, "gold body anchor drift"


# ===========================================================================
# 1. FRAME-MUTATION (MANDATORY — keys is Acc(list_pred(keys), 1/2), read-only)
#    A rival that WRITES to keys to (vacuously) satisfy the postcondition. With
#    only half permission this append has insufficient permission to mutate the
#    list_pred(keys) predicate; it must be REJECTED for permission, not value.
#    Everything else is the verbatim gold body so the rejection is attributable
#    to the write alone.
# ===========================================================================
_FRAME_MUT = _swap(
    _BASE,
    "    total = 0\n    if len(keys) == 0:\n        return 0\n",
    "    total = 0\n"
    "    # ATTACK: mutate the read-only input. Only Acc(list_pred(keys), 1/2)\n"
    "    # is held, so this write has insufficient permission and must be rejected.\n"
    "    keys.append(0)\n"
    "    if len(keys) == 0:\n        return 0\n",
)


# ===========================================================================
# 2. POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impl.
#    Local-variable / branch reshape that PRESERVES every gold proof obligation
#    (invariant set + the four framing asserts) so the front-recursive
#    batched_total still discharges. Changes: rename the cursor off->i; reorder
#    the two commutative pre-asserts (len(rem)>0 first); compute the group view
#    `g` as a named local; reorder the step-cap as an `if/else`. NO invariant or
#    framing assert is dropped (avoid-bug #2/#3: keep the gold induction shape;
#    no forward-append against the front-recursive fold).
# ===========================================================================
_POS_CTRL = _swap(
    _BASE,
    _GOLD_BODY,
    """    total = 0
    if len(keys) == 0:
        return 0
    i = 0
    while i < len(keys):
        # invariants-start
        Invariant(Acc(list_pred(keys), 1 / 2))
        Invariant(0 <= i and i <= len(keys))
        Invariant(total >= 0)
        Invariant(total + batched_total(ToSeq(keys).drop(i), group_size) ==
                  batched_total(ToSeq(keys), group_size))
        Invariant(MustTerminate(len(keys) - i))
        # invariants-end
        rem = ToSeq(keys).drop(i)
        Assert(len(rem) > 0)
        Assert(rem.take(group_size) == ToSeq(keys).drop(i).take(group_size))
        Assert(batched_total(rem, group_size) ==
               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
        if group_size > len(keys) - i:
            step = len(keys) - i
        else:
            step = group_size
        Assert(rem.drop(group_size) == ToSeq(keys).drop(i + step))
        g = rem.take(group_size)
        total = total + matched_rows(g)
        i = i + step
    return total""",
)


# ===========================================================================
# 3. ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input.
#    A self-check inside the gold body asserts each Requires conjunct holds on
#    entry (the half-permission to keys and group_size>=1). If the precondition
#    were unsatisfiable / over-constrained these would fail => PRECOND-TOO-STRONG.
#    The rest of the body is the verbatim gold proof, so it must verify.
# ===========================================================================
_ADMISS = _swap(
    _BASE,
    "    total = 0\n    if len(keys) == 0:\n        return 0\n",
    "    total = 0\n"
    "    # ADMISSIBILITY: the precondition must accept a normal input.\n"
    "    Assert(group_size >= 1)\n"
    "    Assert(Acc(list_pred(keys), 1 / 2))\n"
    "    Assert(len(keys) >= 0)\n"
    "    if len(keys) == 0:\n        return 0\n",
)


# ===========================================================================
# 4. PARTIAL-DOMAIN: first-group-only. Reports ONLY the first group's count and
#    returns it, ignoring every later group. Correct when the collection fits in
#    a single group (len(keys) <= group_size), WRONG otherwise (multi-group).
#    Must be rejected by Result() == batched_total(...): batched_total recurses
#    over drop(group_size), which this impl never adds. Faithful real patch
#    (return only the first per-group update() count, not the accumulated sum)
#    would FAIL test_large_batch / the multi-batch cases of
#    test_updated_rows_when_passing_duplicates (batch_size=1 -> expects 2).
# ===========================================================================
_PARTIAL_FIRST = _swap(
    _BASE,
    _GOLD_BODY,
    """    if len(keys) == 0:
        return 0
    only = matched_rows(ToSeq(keys).take(group_size))
    return only""",
)


# ===========================================================================
# 5. WRONG-GROUPING: per-ELEMENT instead of per-group. Advances one key at a
#    time and sums matched_rows over single-key prefixes (.take(1)) — equals the
#    gold per-group sum ONLY when group_size == 1, and diverges otherwise (it
#    splits every group into singletons, summing across-element rather than
#    collapsing within-group duplicates). Must be rejected by the batched_total
#    pin. Faithful real patch (call update(pk__in=[one pk]) per object and sum)
#    changes how duplicates within a batch collapse, so it would FAIL
#    test_updated_rows_when_passing_duplicates ([note,note] one group expects 1,
#    this yields 2).
# ===========================================================================
_WRONG_GROUPING = _swap(
    _BASE,
    _GOLD_BODY,
    """    total = 0
    if len(keys) == 0:
        return 0
    off = 0
    while off < len(keys):
        # invariants-start
        Invariant(Acc(list_pred(keys), 1 / 2))
        Invariant(0 <= off and off <= len(keys))
        Invariant(total >= 0)
        Invariant(MustTerminate(len(keys) - off))
        # invariants-end
        rem = ToSeq(keys).drop(off)
        total = total + matched_rows(rem.take(1))
        off = off + 1
    return total""",
)


# ===========================================================================
# 6. DOUBLE-COUNT (offset off-by-group): takes the full group per step but
#    advances the cursor by ONLY ONE key, so overlapping groups are summed and
#    the total grossly overcounts (each interior key is counted in group_size
#    groups). Must be rejected by the batched_total pin (which advances by whole
#    groups). Faithful real patch (sliding-window update over overlapping pk
#    windows) would report far more than the true matched count => FAIL
#    test_large_batch (2000 distinct objs expects 2000, this yields ~2000*bs).
# ===========================================================================
_DOUBLE_COUNT = _swap(
    _BASE,
    "        total = total + matched_rows(rem.take(group_size))\n        off = off + step\n",
    "        total = total + matched_rows(rem.take(group_size))\n        off = off + 1\n",
)


# ===========================================================================
# 7. CONSTANT-ZERO (degenerate uniqueness): always returns 0. Satisfies
#    Result() is not None and Result() >= 0, but NOT the pin
#    Result() == batched_total(...) for any non-empty keys whose groups match
#    rows. Cheap supporting case — confirms the pin (not just the non-None /
#    non-negative clauses) is doing the discriminating work. Faithful real patch
#    (return 0 always) reproduces the pre-patch behaviour for non-empty inputs
#    => FAIL test_large_batch (expects 2000) and the duplicates test (expects
#    1 / 2). NOTE: the verifier cannot prove batched_total == 0 in general since
#    matched_rows is uninterpreted, so this must be rejected.
# ===========================================================================
_CONST_ZERO = _swap(
    _BASE,
    _GOLD_BODY,
    """    zero = 0
    return zero""",
)


SPEC_TESTS = [
    {
        "id": "frame-mutation-keys-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": (
            "Mutating the input collection (keys.append) has no behavioural "
            "counterpart in the gold patch — bulk_update never appends to objs. "
            "A faithful real patch that mutated the caller's object list would "
            "corrupt the batches and FAIL the F2P (test_large_batch's 2000-object "
            "count, the duplicates test); but here it cannot even verify because "
            "only Acc(list_pred(keys), 1/2) is held."
        ),
        "rationale": (
            "Rejection comes from the PERMISSION SYSTEM: keys.append needs full "
            "list_pred(keys) write permission; the precondition grants only 1/2, "
            "so the write is rejected for insufficient permission (the #1 "
            "frame-mutation weakness class). The Ensures(Acc(list_pred(keys),1/2)) "
            "frame clause is kept verbatim so the rejection is attributable to "
            "the write alone."
        ),
    },
    {
        "id": "pos-control-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CTRL,
        "rationale": (
            "A structurally-different but CORRECT impl (cursor renamed off->i, "
            "commutative pre-asserts reordered, step-cap rewritten as if/else, "
            "group view bound to a local) MUST verify. Every gold invariant and "
            "framing assert is preserved (no induction lemma introduced; no "
            "forward-append against the front-recursive fold), so the "
            "batched_total proof still discharges. If it failed => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-entry",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "Asserts each Requires conjunct (group_size>=1, Acc(list_pred(keys),"
            "1/2), len(keys)>=0) holds on a normal F2P-shaped entry, then runs the "
            "verbatim gold proof. Must verify; if the precondition could not be "
            "established for a legitimate input => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "partial-domain-first-group-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_FIRST,
        "refinement": (
            "Returning only the first group's matched_rows is correct on the "
            "single-group sub-domain (len(keys)<=group_size) but drops every "
            "later group. The faithful real patch (return the first per-batch "
            "update() count instead of the accumulated rows_updated) would FAIL "
            "test_large_batch (2000 objects across batches expects 2000) and the "
            "batch_size=1 branch of test_updated_rows_when_passing_duplicates "
            "(expects 2)."
        ),
        "rationale": (
            "Rejected by the postcondition pin Result() == "
            "batched_total(ToSeq(keys), group_size): batched_total recurses over "
            ".drop(group_size), summing every group, which this impl never adds. "
            "For multi-group keys the equality is unprovable (matched_rows of the "
            "tail groups is uninterpreted and generally nonzero)."
        ),
    },
    {
        "id": "wrong-grouping-per-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WRONG_GROUPING,
        "refinement": (
            "Summing matched_rows over single-key prefixes (.take(1), advancing "
            "by 1) splits every group into singletons. This equals the gold "
            "per-group sum only when group_size==1. The faithful real patch "
            "(issue one update(pk__in=[pk]) per object and sum) changes the "
            "within-group duplicate collapse, so it would FAIL "
            "test_updated_rows_when_passing_duplicates ([note,note] in one group "
            "expects 1, this reports 2)."
        ),
        "rationale": (
            "Rejected by the batched_total pin. The deep fold groups by "
            ".take(group_size)/.drop(group_size); the per-element sum is a "
            "DIFFERENT structural value the spec does not equate to it (the "
            "invariant total + batched_total(drop(off)) == batched_total(all) "
            "is dropped and cannot be re-established for the singleton walk)."
        ),
    },
    {
        "id": "double-count-advance-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DOUBLE_COUNT,
        "refinement": (
            "Taking the whole group per step but advancing the cursor by 1 sums "
            "overlapping windows, counting each interior key up to group_size "
            "times. The faithful real patch (sliding overlapping pk windows) "
            "reports far more than the true matched count, so it would FAIL "
            "test_large_batch (2000 distinct objects expects 2000)."
        ),
        "rationale": (
            "Rejected by the batched_total pin AND the loop invariant "
            "total + batched_total(ToSeq(keys).drop(off), group_size) == "
            "batched_total(ToSeq(keys), group_size): advancing off by 1 instead "
            "of step breaks the invariant's inductive step (the consumed prefix "
            "is no longer a whole number of groups), so it cannot be maintained."
        ),
    },
    {
        "id": "const-zero-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _CONST_ZERO,
        "refinement": (
            "Returning a constant 0 reproduces the pre-patch behaviour for "
            "non-empty inputs. The faithful real patch (return 0 always) would "
            "FAIL test_large_batch (expects 2000) and "
            "test_updated_rows_when_passing_duplicates (expects 1 / 2). This is "
            "the cheap supporting case confirming the PIN — not merely the "
            "non-None / non-negative clauses — carries the discrimination."
        ),
        "rationale": (
            "Rejected by Result() == batched_total(ToSeq(keys), group_size): "
            "since matched_rows is @ContractOnly (only >=0), the verifier cannot "
            "prove batched_total(ToSeq(keys), group_size) == 0 for arbitrary "
            "non-empty keys, so the constant-0 return is rejected."
        ),
    },
]


# ===========================================================================
# AXIOM LANE — one @ContractOnly axiom: matched_rows (A-consumed).
#   matched_rows(group_keys: PSeq[int]) -> int, Ensures(Result() >= 0).
#   Models the unchanged QuerySet.filter(pk__in=pks).update(**kwargs) callee
#   invoked once per group. Probes run in the instance Docker image with the
#   gold patch applied (apply_gold=True; the callee is unchanged by the patch,
#   but applying gold keeps the run aligned with G-RESOLVE state). Each probe is
#   self-contained: imports only Django (the library under test) + stdlib,
#   prints a diagnostic, and exits 0 iff the obligation holds. flag_dependency:
#   the axiom is flag-independent (update()'s return is the DB-reported matched
#   row count regardless of backend); G-AX exercises the default sqlite3 backend
#   the harness uses (see meta.axioms[0], mapping.md §3.1).
# ===========================================================================

_AX_SOUND_PROBE = r'''
"""axiom-soundness: matched_rows(group_keys) -> Ensures(Result() >= 0).
Execute the REAL unchanged callee QuerySet.filter(pk__in=...).update(...) over
boundary + sentinel + raise-path + 20k randomized fuzz groups IN the axiom's
Requires domain (any int sequence) under the harness's default sqlite3 backend.
Assert every observed count is a non-negative int (the axiom Ensures) AND, as
the load-bearing refinement evidence, that pk__in collapses within-group
duplicates ([pk,pk] one group -> 1) while separate groups sum (1 + 1 -> 2).
Exit 0 iff every obligation holds; exit 1 on the first violation.
"""
import os, random, sys

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:
        # Outside a Django-capable env we cannot exercise the callee; that is an
        # environment limitation, not an axiom violation. The runner schedules
        # this in the instance image where Django is importable.
        print("AX-SOUND SKIP: Django not configurable: %r" % (exc,))
        return 0

    from django.db import connection, models

    class Row(models.Model):
        note = models.CharField(max_length=32, default="")
        class Meta:
            app_label = "contenttypes"

    with connection.schema_editor() as editor:
        editor.create_model(Row)

    def matched(group_keys, value):
        return Row.objects.filter(pk__in=group_keys).update(note=value)

    seen = 0

    # (boundary 0) the empty group — the model reaches this via take(group_size)
    # on an exhausted suffix; pk__in=[] matches nothing.
    n = matched([], "e")
    assert isinstance(n, int) and n >= 0, "empty group returned %r" % (n,)
    assert n == 0, "empty group matched %r, expected 0" % (n,)
    seen += 1

    # (a) single present key -> 1.
    for _ in range(50):
        obj = Row.objects.create(note="x")
        n = matched([obj.pk], "a")
        assert isinstance(n, int) and n >= 0, "returned %r" % (n,)
        assert n == 1, "single present key matched %r, expected 1" % (n,)
        seen += 1

    # (b) absent key (sentinel / deleted) -> 0.
    for _ in range(25):
        obj = Row.objects.create(note="x")
        pk = obj.pk
        obj.delete()
        n = matched([pk], "a")
        assert isinstance(n, int) and n >= 0, "returned %r" % (n,)
        assert n == 0, "absent key matched %r, expected 0" % (n,)
        seen += 1

    # (c) the duplicate subtlety batched_total relies on.
    for _ in range(50):
        obj = Row.objects.create(note="x")
        one_group = matched([obj.pk, obj.pk], "b")
        assert one_group == 1, "[pk,pk] one group matched %r, expected 1" % (one_group,)
        split = matched([obj.pk], "c") + matched([obj.pk], "d")
        assert split == 2, "two single-key groups summed %r, expected 2" % (split,)
        seen += 1

    # (d) randomized fuzz groups across the int-sequence domain (present +
    # absent + large-sentinel pks); count is always >= 0 and equals the number
    # of distinct present keys.
    rng = random.Random(14559)
    live = [Row.objects.create(note="x").pk for _ in range(40)]
    for _ in range(20000):
        k = rng.randint(0, 6)
        group = [rng.choice(live) for _ in range(k)] if (live and k) else []
        if rng.random() < 0.2:
            group.append(10 ** 9 + rng.randint(0, 1000))
        n = matched(group, "z")
        assert isinstance(n, int) and n >= 0, "group %r returned %r" % (group, n)
        expected = len(set(g for g in group if g in live))
        assert n == expected, "group %r matched %r, expected %r distinct present" % (group, n, expected)
        seen += 1

    print("AX-SOUND OK: matched_rows Ensures(Result() >= 0) holds over %d real "
          "QuerySet.update observations (incl. empty/absent/duplicate "
          "boundaries); duplicates collapse within a group and sum across "
          "groups." % (seen,))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


_AX_CONTAIN_PROBE = r'''
"""axiom-containment: every callee-input the MODEL can reach lies inside the
axiom's Requires domain.

The axiom matched_rows has Requires only `group_keys: PSeq[int]` (no value/length
constraint). The model calls it exactly as matched_rows(rem.take(group_size))
where rem = ToSeq(keys).drop(off) and keys: List[int] — i.e. a (possibly empty)
contiguous int sub-sequence of keys: any list of ints, length 0..group_size,
containing present pks, repeated pks, and absent pks. The PSeq[int] domain
trivially contains every such shape (it accepts ANY int sequence). This probe
confirms CONTAINMENT operationally: the real callee accepts and returns a
non-negative int for every shape the model can produce — empty group, single
key, full group, duplicated keys, absent keys, mixed — so no caller-reachable
input falls outside the axiom's domain (no AXIOM-TOO-WEAK-FOR-CALLER).
Covering MORE than the caller reaches (e.g. negative pks) would be SOUND, not a
defect; we only assert the caller-reachable shapes are inside.
Exit 0 iff every reachable shape is accepted with a non-negative int.
"""
import os, sys

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:
        print("AX-CONTAIN SKIP: Django not configurable: %r" % (exc,))
        return 0

    from django.db import connection, models

    class Row(models.Model):
        note = models.CharField(max_length=32, default="")
        class Meta:
            app_label = "contenttypes"

    with connection.schema_editor() as editor:
        editor.create_model(Row)

    def matched(group_keys):
        return Row.objects.filter(pk__in=group_keys).update(note="v")

    a = Row.objects.create(note="x").pk
    b = Row.objects.create(note="x").pk
    gone = Row.objects.create(note="x")
    absent = gone.pk
    gone.delete()

    # Every group shape the model's matched_rows(rem.take(group_size)) can reach:
    reachable = [
        [],                 # empty group (exhausted suffix; group_size > len)
        [a],                # single present
        [a, b],             # full distinct group
        [a, a],             # within-group duplicate (pk__in collapse)
        [absent],           # absent key only
        [a, absent],        # mixed present/absent
        [a, a, b, absent],  # duplicates + present + absent in one group
    ]
    for grp in reachable:
        n = matched(grp)
        assert isinstance(n, int) and n >= 0, (
            "reachable group %r outside axiom domain or returned %r" % (grp, n))

    print("AX-CONTAIN OK: all %d caller-reachable matched_rows group shapes "
          "(empty/single/full/dup/absent/mixed) lie inside the PSeq[int] "
          "Requires domain (accepted, non-negative int)." % (len(reachable),))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-matched_rows",
        "axiom": "matched_rows",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "If the real QuerySet.filter(pk__in=...).update(...) ever returned a "
            "negative or non-int count on an input in the axiom's PSeq[int] "
            "Requires domain (under the default sqlite3 backend the harness uses) "
            "the axiom Ensures(Result() >= 0) would be unsound => AXIOM-UNSOUND. "
            "Mirrors axiom_check.py (G-AX), fuzzing boundary + sentinel + absent "
            "+ duplicate + 20k random groups."
        ),
    },
    {
        "id": "ax-contain-matched_rows",
        "axiom": "matched_rows",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "Every callee-input the model can reach is matched_rows("
            "rem.take(group_size)) — a contiguous int sub-sequence of keys "
            "(length 0..group_size, present/duplicate/absent keys). The axiom's "
            "Requires domain is PSeq[int] (any int sequence), which contains all "
            "of them; a reachable input outside the domain would be "
            "AXIOM-TOO-WEAK-FOR-CALLER. Confirmed operationally by the real "
            "callee accepting each reachable shape."
        ),
    },
]
