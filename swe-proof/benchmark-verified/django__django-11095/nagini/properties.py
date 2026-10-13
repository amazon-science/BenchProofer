"""PBT falsification battery for django__django-11095.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TESTS case is a full model.py variant that shares the FROZEN spec exactly
(same_spec) and edits ONLY inside an `# impl-start`/`# impl-end` region; it is
checked by the Nagini verifier on the host. Each AXIOM_TESTS case is a
self-contained probe run in the instance Docker image against the real Django
callees (the A-reference deep models).

Defended surface of this instance (read model.py + refinement.md):

  Two cooperating, read-only operations over an AdminView whose three collections
  (`configured`, `reported`, `granted`) are all held at HALF permission
  (Acc(..., 1/2)) in BOTH the Requires and the Ensures — i.e. every input is
  read-only and must stay framed.

  * select_applicable_editors  — models the default get_inlines hook. Load-bearing
    postcondition: ToSeq(Result()) == ToSeq(self.configured)  (identity copy of
    the configured collection, in order; nothing dropped/added/reordered).

  * materialize_editors        — models get_inline_instances (THE FIX). Load-bearing
    postcondition: ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted))
    The result is built from the hook's REPORT (self.reported), filtered by the
    per-entry permission flag, NOT from self.configured. Precond:
    len(self.reported) == len(self.granted).

  The oracle `kept` is a @Pure fold that is FULLY GROUNDED in the inputs
  (reported, granted) — it is not an opaque answer-key, so there is no "echo a
  wrong marker and verify" attack; the cheapest honest impl that satisfies the
  post IS the correct one. The ungrounded-oracle-echo class therefore does not
  apply here (see the positive control instead). All other classes do apply.

The F2P test (test_get_inline_instances_override_get_inlines) overrides
get_inlines to return self.inlines[:1] / [1:2] / [] and asserts the materialised
editor classes equal exactly the (overridden) report. Pre-patch the loop iterated
self.inlines (== configured) and ignored the override — that is the partial-domain
break encoded below (a rival materialising from `configured` is correct only when
reported == configured, i.e. exactly the non-override domain the test excludes).
"""
from pathlib import Path

INSTANCE = "django__django-11095"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two impl regions, verbatim from model.py, used as the unique `old`
# anchors for region surgery. Editing ONLY between these markers guarantees
# same_spec (the spec_view elides the whole impl region incl. invariants).
# ---------------------------------------------------------------------------

_SELECT_IMPL = """    # impl-start
    result = []  # type: List[int]
    i = len(self.configured)
    while i > 0:
        # invariants-start
        Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(self.configured))
        Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
        Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
        result = [self.configured[i - 1]] + result
        i = i - 1
    return result
    # impl-end"""

_MATERIALIZE_IMPL = """    # impl-start
    result = []  # type: List[int]
    j = len(self.reported)
    while j > 0:
        # invariants-start
        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
        Invariant(len(self.reported) == len(self.granted))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(self.reported))
        Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
        Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
        Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
        Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
        cls = self.reported[j - 1]
        if self.granted[j - 1] != 0:
            result = [cls] + result
        j = j - 1
    return result
    # impl-end"""

assert _SELECT_IMPL in _BASE and _BASE.count(_SELECT_IMPL) == 1, "select impl anchor drift"
assert _MATERIALIZE_IMPL in _BASE and _BASE.count(_MATERIALIZE_IMPL) == 1, "materialize impl anchor drift"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-different but CORRECT impls
# must verify.  Both keep the gold backward/front-prepend loop shape (the
# `kept` fold is front-recursive, so a forward-append would need an
# f(a+b) lemma the verifier will not auto-discharge — pitfall #3) and keep
# every framing Assert the loop invariant needs (pitfall #2); the structural
# difference is a reorder of the (order-independent) framing asserts plus a
# renamed loop counter via an extra local.  If a faithful correct impl cannot
# verify => SPEC-TOO-STRONG.
# ===========================================================================

_POS_SELECT = _swap(_BASE, _SELECT_IMPL, """    # impl-start
    # Positive control: same correct backward copy, but the two order-independent
    # framing asserts are swapped and the loop counter is carried in a renamed
    # local `k`.  Keeps every gold proof obligation; only the executable shape
    # is reshaped.  Must verify.
    out = []  # type: List[int]
    k = len(self.configured)
    while k > 0:
        # invariants-start
        Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= k and k <= len(self.configured))
        Invariant(ToSeq(out) == ToSeq(self.configured).drop(k))
        Invariant(MustTerminate(k + 1))
        # invariants-end
        Assert(ToSeq(self.configured).drop(k - 1).drop(1) == ToSeq(self.configured).drop(k))
        Assert(ToSeq(self.configured).drop(k - 1)[0] == self.configured[k - 1])
        out = [self.configured[k - 1]] + out
        k = k - 1
    return out
    # impl-end""")

_POS_MATERIALIZE = _swap(_BASE, _MATERIALIZE_IMPL, """    # impl-start
    # Positive control: same correct backward report-filtered build, but with the
    # four framing asserts regrouped (granted-side first, then reported-side) and
    # the loop counter carried in a renamed local `t`.  Every gold proof
    # obligation is preserved; only the executable shape is reshaped.  Must verify.
    out = []  # type: List[int]
    t = len(self.reported)
    while t > 0:
        # invariants-start
        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
        Invariant(len(self.reported) == len(self.granted))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= t and t <= len(self.reported))
        Invariant(len(ToSeq(self.reported).drop(t)) == len(ToSeq(self.granted).drop(t)))
        Invariant(ToSeq(out) == kept(ToSeq(self.reported).drop(t), ToSeq(self.granted).drop(t)))
        Invariant(MustTerminate(t + 1))
        # invariants-end
        Assert(ToSeq(self.granted).drop(t - 1)[0] == self.granted[t - 1])
        Assert(ToSeq(self.granted).drop(t - 1).drop(1) == ToSeq(self.granted).drop(t))
        Assert(ToSeq(self.reported).drop(t - 1)[0] == self.reported[t - 1])
        Assert(ToSeq(self.reported).drop(t - 1).drop(1) == ToSeq(self.reported).drop(t))
        elem = self.reported[t - 1]
        if self.granted[t - 1] != 0:
            out = [elem] + out
        t = t - 1
    return out
    # impl-end""")


# ===========================================================================
# ADMISSIBILITY — the precondition must accept a normal F2P-shaped input.
# We add, AFTER the (unchanged) gold materialize loop returns, an unreachable
# self-call site guarded by `if False:` that constructs an AdminView and calls
# materialize_editors, asserting its Requires (len(reported)==len(granted)) is
# establishable for a freshly-built (empty) view.  The guard keeps it dead at
# runtime but Nagini still type/contract-checks the call.  If the precondition
# could not be established for a legitimate input the call site would fail to
# verify => PRECOND-TOO-STRONG.  Edited ONLY inside materialize's impl region.
# ===========================================================================

_ADMISS = _swap(_BASE, _MATERIALIZE_IMPL, """    # impl-start
    result = []  # type: List[int]
    j = len(self.reported)
    while j > 0:
        # invariants-start
        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
        Invariant(len(self.reported) == len(self.granted))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(self.reported))
        Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
        Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
        Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
        Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
        cls = self.reported[j - 1]
        if self.granted[j - 1] != 0:
            result = [cls] + result
        j = j - 1
    # Admissibility: a fresh AdminView (empty, index-aligned reported/granted)
    # is a legitimate F2P-shaped input — its Requires (len(reported)==len(granted),
    # all collections at 1/2) must be establishable at a real call site.
    if request == 0 and request != 0:  # statically dead; still contract-checked
        v = AdminView()
        Assert(len(v.reported) == len(v.granted))
        m = materialize_editors(v, request, obj)
        Assert(ToSeq(m) == kept(ToSeq(v.reported), ToSeq(v.granted)))
    return result
    # impl-end""")


# ===========================================================================
# FRAME-MUTATION (uniqueness, MANDATORY) — every input is read-only (Acc 1/2).
# A rival that WRITES to a read-only input to "satisfy" the postcondition must
# be REJECTED for INSUFFICIENT PERMISSION.  We keep the gold invariants/asserts
# verbatim so the only thing that changes is the illegal write, making the
# rejection attributable to the write rather than a proof gap.
# ===========================================================================

# (a) materialize writes to self.reported (the input it reads).  With only
# Acc(self.reported, 1/2) it cannot store to the field -> insufficient permission.
_FRAME_REPORTED = _swap(_BASE, _MATERIALIZE_IMPL, """    # impl-start
    # FRAME-MUTATION rival: overwrite the read-only input `self.reported`.  Only
    # half permission is held => this MUST be rejected for insufficient permission.
    self.reported = []  # type: ignore
    result = []  # type: List[int]
    j = len(self.reported)
    while j > 0:
        # invariants-start
        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
        Invariant(len(self.reported) == len(self.granted))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(self.reported))
        Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
        Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
        Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
        Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
        cls = self.reported[j - 1]
        if self.granted[j - 1] != 0:
            result = [cls] + result
        j = j - 1
    return result
    # impl-end""")

# (b) select writes to self.configured (the input it reads).  Same illegal write.
_FRAME_CONFIGURED = _swap(_BASE, _SELECT_IMPL, """    # impl-start
    # FRAME-MUTATION rival: overwrite the read-only input `self.configured`.  Only
    # half permission is held => this MUST be rejected for insufficient permission.
    self.configured = []  # type: ignore
    result = []  # type: List[int]
    i = len(self.configured)
    while i > 0:
        # invariants-start
        Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(self.configured))
        Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
        Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
        result = [self.configured[i - 1]] + result
        i = i - 1
    return result
    # impl-end""")


# ===========================================================================
# PARTIAL-DOMAIN (uniqueness) — THE central differential of this instance.
# A rival that materialises from `self.configured` instead of the hook's
# report `self.reported`.  It is correct on the sub-domain reported==configured
# (the non-override case) but DIVERGES exactly on the override sub-domain the
# F2P test exercises (reported = inlines[:1] / [1:2] / []).  It must be REJECTED
# by the postcondition kept(reported, granted).  This is the pre-patch bug.
# ===========================================================================

_PARTIAL_CONFIGURED = _swap(_BASE, _MATERIALIZE_IMPL, """    # impl-start
    # PARTIAL-DOMAIN rival (the pre-patch bug): build from the CONFIGURED
    # collection, ignoring the hook's report.  Correct iff reported==configured
    # AND every entry granted; diverges on the override domain the F2P test
    # exercises.  Must be rejected by kept(reported, granted) over `reported`.
    result = []  # type: List[int]
    i = len(self.configured)
    while i > 0:
        # invariants-start
        Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(self.configured))
        Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
        Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
        result = [self.configured[i - 1]] + result
        i = i - 1
    return result
    # impl-end""")

# A second partial-domain rival: materialise from the report but DROP the
# permission filter (return the whole report).  Correct iff every granted flag
# is set (the F2P MockSuperUser case) but diverges whenever some context grants
# nothing — must be rejected by the `kept` fold (which drops granted==0 entries).
_PARTIAL_NOFILTER = _swap(_BASE, _MATERIALIZE_IMPL, """    # impl-start
    # PARTIAL-DOMAIN rival: iterate the report but IGNORE the permission flag,
    # keeping every reported entry.  Correct only when every granted flag is set;
    # diverges when a context grants nothing.  Must be rejected by `kept`.
    result = []  # type: List[int]
    j = len(self.reported)
    while j > 0:
        # invariants-start
        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
        Invariant(len(self.reported) == len(self.granted))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(self.reported))
        Invariant(ToSeq(result) == ToSeq(self.reported).drop(j))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
        result = [self.reported[j - 1]] + result
        j = j - 1
    return result
    # impl-end""")

# A partial-domain rival on SELECT: report a narrowed selection (drop the first
# configured entry) instead of the full configured collection.  Correct only
# when configured is empty; diverges on every non-empty view.  The default-hook
# postcondition ToSeq(Result())==ToSeq(self.configured) must reject it.
_PARTIAL_SELECT_DROP = _swap(_BASE, _SELECT_IMPL, """    # impl-start
    # PARTIAL-DOMAIN rival: the default selection drops the FIRST configured
    # entry (reports configured[1:]).  Correct only for an empty configured
    # collection; diverges otherwise.  Must be rejected by
    # ToSeq(Result()) == ToSeq(self.configured).
    result = []  # type: List[int]
    i = len(self.configured)
    while i > 1:
        # invariants-start
        Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(self.configured))
        Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
        Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
        result = [self.configured[i - 1]] + result
        i = i - 1
    return result
    # impl-end""")


# ===========================================================================
# SUPPORTING near-miss (uniqueness) — a cheap mechanical mutant that still
# carries a real refinement: reverse the materialised order (front-append the
# WRONG way) so a context with two distinct reported classes is reversed.  The
# F2P scenario observes order (type of result[0]); a reversal would mis-order
# multi-entry reports.  Must be rejected by the order-sensitive `kept` fold.
# ===========================================================================

_NEARMISS_REVERSE = _swap(_BASE, _MATERIALIZE_IMPL, """    # impl-start
    # SUPPORTING near-miss: forward iteration appending to the END reverses the
    # kept order relative to the front-recursive `kept` fold.  Diverges on any
    # report with >=2 kept entries of distinct identity; must be rejected.
    result = []  # type: List[int]
    j = 0
    while j < len(self.reported):
        # invariants-start
        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
        Invariant(len(self.reported) == len(self.granted))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(self.reported))
        Invariant(MustTerminate(len(self.reported) - j + 1))
        # invariants-end
        cls = self.reported[j]
        if self.granted[j] != 0:
            result = result + [cls]
        j = j + 1
    return result
    # impl-end""")


SPEC_TESTS = [
    {
        "id": "pos-select-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SELECT,
        "rationale": "structurally-different but CORRECT default hook (reordered "
                     "order-independent framing asserts, renamed counter `k`, gold "
                     "backward-copy shape kept). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-materialize-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATERIALIZE,
        "rationale": "structurally-different but CORRECT materialisation (regrouped "
                     "framing asserts, renamed counter `t`, gold backward front-prepend "
                     "shape kept to match the front-recursive `kept` fold; no forward-"
                     "append lemma needed). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-fresh-view",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "a statically-dead but contract-checked self-call on a fresh "
                     "AdminView establishes materialize's Requires "
                     "(len(reported)==len(granted), all collections at 1/2) for a "
                     "legitimate F2P-shaped input. Must verify, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-write-reported",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_REPORTED,
        "refinement": "A real patch that REASSIGNS self.inlines/the reported list "
                      "inside get_inline_instances would corrupt the admin's "
                      "configured inlines for every subsequent request and would NOT "
                      "make the F2P override test pass (the test reads get_inlines "
                      "independently); a verifying mutating rival is a true "
                      "verify-not-resolve break. Only Acc(self.reported,1/2) is held.",
        "rationale": "permission system: writing self.reported with only half "
                     "permission must be rejected for INSUFFICIENT PERMISSION.",
    },
    {
        "id": "frame-write-configured",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_CONFIGURED,
        "refinement": "A real get_inlines that mutates self.inlines would destroy the "
                      "configured collection (and break every PASS_TO_PASS admin view "
                      "that reads inlines); it does not resolve the F2P. Only "
                      "Acc(self.configured,1/2) is held.",
        "rationale": "permission system: writing self.configured with only half "
                     "permission must be rejected for INSUFFICIENT PERMISSION.",
    },
    {
        "id": "partial-materialize-from-configured",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_CONFIGURED,
        "refinement": "This IS the pre-patch behaviour (loop over self.inlines): it "
                      "ignores the get_inlines override, so the F2P "
                      "test_get_inline_instances_override_get_inlines FAILS (it "
                      "materialises both configured inlines for an override that "
                      "reports [] or a 1-element subset). model_prepatch.py is exactly "
                      "this and is documented to fail the postcondition.",
        "rationale": "postcondition clause ToSeq(Result())==kept(ToSeq(self.reported),"
                     "ToSeq(self.granted)) pins to `reported`; building from "
                     "`configured` diverges whenever reported != configured.",
    },
    {
        "id": "partial-materialize-no-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_NOFILTER,
        "refinement": "Dropping the permission guard (the has_*_permission `or`) keeps "
                      "editors a real request must NOT see; a real patch that removed "
                      "the `continue` would expose unauthorised inlines and fail the "
                      "permission PASS_TO_PASS tests — it does not faithfully resolve.",
        "rationale": "the `kept` fold drops granted==0 entries; returning the whole "
                     "report diverges whenever any granted flag is 0.",
    },
    {
        "id": "partial-select-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_SELECT_DROP,
        "refinement": "A default get_inlines that returned self.inlines[1:] would drop "
                      "the first configured inline from every default admin, breaking "
                      "the existing non-override behaviour (the PASS_TO_PASS views that "
                      "render all configured inlines); it does not resolve.",
        "rationale": "default-hook postcondition ToSeq(Result())==ToSeq(self.configured) "
                     "rejects any narrowing of the configured collection.",
    },
    {
        "id": "nearmiss-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NEARMISS_REVERSE,
        "refinement": "Materialising the kept editors in reversed order would render "
                      "inline editors out of their declared order; the F2P observes "
                      "result[0]'s class for a single-entry report (so single-entry "
                      "passes) but the spec's order clause and any multi-inline admin "
                      "ordering test diverge. A supporting near-miss with a real "
                      "ordering refinement, not a substitute for the reasoned attacks.",
        "rationale": "the front-recursive `kept` fold pins order; appending to the end "
                     "in forward iteration reverses it, diverging on >=2 distinct kept "
                     "entries.",
    },
]


# ===========================================================================
# AXIOM lane — this bundle consumes NO @ContractOnly axioms (meta.axioms == []).
# Both modelled operations are A-reference deep models, validated == the real
# Django callees by axiom_check.py / G-AX.  We carry that soundness check here
# (strengthened to fuzz the override sub-domains) as an axiom-soundness probe so
# the A-reference fidelity is part of the persisted, re-runnable battery.  The
# probe embeds axiom_check.py's logic and runs the REAL ModelAdmin.get_inlines /
# get_inline_instances in-container WITH GOLD APPLIED (the base image has no
# get_inlines, so apply_gold=True).  containment is trivial here: the model only
# passes index-aligned List[int] views (len(reported)==len(granted)); the deep
# model has no narrower Requires domain to escape — noted, no separate case.
# ===========================================================================

_AXIOM_PROBE = r'''
import sys

# --- A-reference soundness: the deep models must equal the REAL Django callees.
# SKIP (exit 0) ONLY if Django itself is not importable (run outside container).
try:
    import django  # noqa: F401
except ImportError as exc:
    print("AX SKIP: Django not importable: %r" % (exc,))
    sys.exit(0)

from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django.contrib.admin",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db import models

site = AdminSite()

class Episode(models.Model):
    class Meta:
        app_label = "contenttypes"

class Media(models.Model):
    content_type = models.ForeignKey(ContentType, models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    class Meta:
        app_label = "contenttypes"

class MediaInline(GenericTabularInline):
    model = Media

class AlternateInline(GenericTabularInline):
    model = Media

class MockSuperUser:
    def has_perm(self, perm, obj=None):
        return True
    def has_module_perms(self, app_label):
        return True

class MockRequest:
    pass

request = MockRequest()
request.user = MockSuperUser()

def cls_seq(instances):
    return [type(i) for i in instances]

obs = 0

# (default hook) deep model `select_applicable_editors`: ToSeq(Result())==ToSeq(configured)
# => the real get_inlines reports exactly the configured inlines in order, and the
# default materialisation builds one editor per configured inline.
class DefaultAdmin(admin.ModelAdmin):
    inlines = (AlternateInline, MediaInline)

da = DefaultAdmin(Episode, site)
assert list(da.get_inlines(request, None)) == [AlternateInline, MediaInline], \
    "default get_inlines must report configured inlines in order (select deep model)"
assert cls_seq(da.get_inline_instances(request)) == [AlternateInline, MediaInline], \
    "default materialisation must build one editor per configured inline, in order"
obs += 1

# (materialisation deep model) `materialize_editors`: ToSeq(Result())==kept(reported,granted),
# pinned to the hook's REPORT.  Fuzz the override sub-domains the F2P test exercises
# AND extra orderings to try to make the real callee disagree with the deep model.
class EpisodeAdmin(admin.ModelAdmin):
    inlines = (AlternateInline, MediaInline)
    def get_inlines(self, request, obj):
        if hasattr(request, "name"):
            if request.name == "alternate":
                return self.inlines[:1]
            elif request.name == "media":
                return self.inlines[1:2]
            elif request.name == "both_rev":
                return (MediaInline, AlternateInline)
            elif request.name == "both":
                return (AlternateInline, MediaInline)
        return []

ma = EpisodeAdmin(Episode, site)

# empty report => no editors materialised (NOT the configured two): tracks the report.
assert list(ma.get_inlines(request, None)) == [], "override (no name) must report []"
assert ma.get_inline_instances(request) == [], \
    "materialisation must track the empty report, not the configured inlines"
obs += 1

# Each override sub-domain: result classes == report, in report order, and the report
# DIFFERS from the configured collection (genuinely exercises the override).
cases = [
    ("alternate", [AlternateInline]),
    ("media", [MediaInline]),
    ("both_rev", [MediaInline, AlternateInline]),   # report order != configured order
    ("both", [AlternateInline, MediaInline]),
]
for name, expected_report in cases:
    request.name = name
    reported = list(ma.get_inlines(request, None))
    assert reported == expected_report, \
        "override get_inlines(%r) report %r != expected %r" % (name, reported, expected_report)
    instances = ma.get_inline_instances(request)
    assert cls_seq(instances) == expected_report, \
        ("materialisation must build editors from the hook's report %r (in order), "
         "not from configured %r" % (reported, list(ma.inlines)))
    obs += 1

# Discriminator: at least one exercised report differs from the configured collection.
request.name = "alternate"
assert list(ma.get_inlines(request, None)) != list(ma.inlines), \
    "test scenario must exercise a report differing from the configured collection"

print("AX OK: A-reference deep models (select_applicable_editors / "
      "materialize_editors) validated against the real ModelAdmin.get_inlines / "
      "get_inline_instances over %d observations; materialisation tracks the "
      "hook's report (incl. reordered and empty overrides), not the configured "
      "collection." % (obs,))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-aref-deepmodels-sound",
        "axiom": "select_applicable_editors+materialize_editors (A-reference deep models)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_PROBE,
        "rationale": "the two deep models must equal the real Django callees on every "
                     "caller-reachable input. Runs the real ModelAdmin.get_inlines / "
                     "get_inline_instances with gold applied, fuzzing the override "
                     "sub-domains (empty, single, reordered pair); if the real callee "
                     "disagrees with kept(reported,granted)/ToSeq(configured), the "
                     "A-reference is UNSOUND. Mirrors axiom_check.py (G-AX), widened.",
    },
]
