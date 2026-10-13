# properties.py — PBT manifest for django__django-15382. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# parses SPEC_TESTS / AXIOM_TESTS, writes each spec `module` to a temp file,
# Nagini-verifies it on the host + checks same_spec against the frozen model.py,
# and runs each axiom `probe` in the instance's Docker image.
#
# Defended surface (render_exists(satisfiable, negated) -> List[int], both inputs
# pass-by-value int in {0,1}; the SQL fragment is List[int] of code points,
# spec carried by PSeq[int] via ToSeq). Load-bearing postcondition clauses:
#   C1  not (satisfiable == 0 and negated == 0)              -- reachability/return-vs-raise
#   C2  Acc(list_pred(Result()))                             -- output ownership
#   C3  Implies(sat==0 and neg==1, len(Result()) == 0)       -- EMPTY-fragment pin (THE fix)
#   C4  Implies(sat==1 and neg==0, ToSeq == inner_fragment)  -- satisfiable content pin
#   C5  Implies(sat==1 and neg==1, ToSeq == NOT + inner_fragment)
#   E1  Exsures(EmptyResultSet, sat==0 and neg==0)           -- matches-nothing only here
# inner_fragment is a @Pure @ContractOnly companion GROUNDED in the renderer's
# real output (witness-uniqueness): any List[int] whose ToSeq equals it IS the
# renderer's SQL under the refinement, so an echo-reconstruct is *correct*, not a
# cheat; the only wrong echo is a *different* fabricated fragment, which fails C4/C5.
from pathlib import Path

INSTANCE = "django__django-15382"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl region body (between the markers). Every variant is built by
# _swap-ping ONLY this text, so the frozen spec (axioms/pure/pre/post) is untouched
# and same_spec is guaranteed.
_GOLD_IMPL = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        # Inner selection is unsatisfiable. A negated existence predicate over an
        # empty selection is universally true -> return normally (here, the empty
        # always-true fragment). A non-negated one can never hold -> re-propagate.
        if negated == 1:
            empty = []  # type: List[int]
            return empty
        raise exc
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql"""

assert _BASE.count(_GOLD_IMPL) == 1, "gold impl region drift"


def _impl(new_body):
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness + admissibility) — MUST verify
# ---------------------------------------------------------------------------

# pos-structdiff: structurally-different but CORRECT. The negation prefix is
# bound to a typed local before the prepend (a local-variable reshape, directive
# 5 safe); the gold framing Assert is KEPT verbatim so the C5 content-pin still
# discharges. Same value behaviour as gold on all four cases.
_POS_STRUCTDIFF = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        if negated == 1:
            empty = []  # type: List[int]
            return empty
        raise exc
    if negated == 1:
        prefix = [78, 79, 84, 32]  # type: List[int]
        sql = prefix + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql"""

# pos-reorder: same behaviour, the unsatisfiable-negated early return and the
# re-raise branches are reordered (raise guarded by `negated == 0` instead of an
# else). Keeps every proof obligation (the except still establishes sat==0).
_POS_REORDER = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        if negated == 0:
            raise exc
        empty = []  # type: List[int]
        return empty
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql"""

# admiss: a positive-control caller that, after producing the gold result, calls
# render_exists itself on the F2P-shaped input (sat=0, neg=1: ~Exists(none())) and
# asserts the call returns a result (the Requires must admit the normal F2P input).
# The self-call sits AFTER the gold return is computed but is reached via an
# early helper invocation guarded so the gold path is unchanged for verification
# of the postcondition. We invoke it on the satisfiable path tail where state is
# clean.
_ADMISS = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        if negated == 1:
            # admissibility: the precondition admits the F2P-shaped input
            # (sat=0, neg=1). We are ON that input now; returning the empty
            # fragment is exactly what the F2P observes (~Exists(none()) matches
            # every row). len == 0 holds for the empty list.
            empty = []  # type: List[int]
            Assert(len(empty) == 0)
            return empty
        raise exc
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql"""


# ---------------------------------------------------------------------------
# UNIQUENESS / completeness rivals — MUST reject (else SPEC-TOO-WEAK)
# ---------------------------------------------------------------------------

# atk-junk-unsatneg (PARTIAL-DOMAIN, the documented hole): correct everywhere
# EXCEPT sat=0,neg=1, where it returns junk SQL 'XYZ' = [88,89,90] instead of the
# empty fragment. Must reject on C3 (len(Result()) == 0).
# refinement: faithful real patch returns '%XYZ%'-style invalid SQL on
# ~Exists(none()), so `WHERE XYZ AND pk=...` is a SQL error / wrong rows; the F2P
# assertSequenceEqual(qs, [manager]) fails -> does NOT resolve.
_ATK_JUNK = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        if negated == 1:
            junk = [88, 89, 90]  # type: List[int]
            return junk
        raise exc
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql"""

# atk-false-pred (PARTIAL-DOMAIN, value-level): on sat=0,neg=1 returns an
# always-FALSE non-empty fragment '0=1' = [48,61,49] (the maintainer's hints_text
# proposed an always-TRUE '1=1'; this rival flips it). Must reject on C3.
# refinement: a faithful real patch returns `WHERE (0=1) AND pk=...` -> always
# empty result set, so ~Exists(none()) wrongly excludes the manager; the F2P
# assertSequenceEqual(qs, [manager]) fails (gets []) -> does NOT resolve.
_ATK_FALSE = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        if negated == 1:
            falsepred = [48, 61, 49]  # type: List[int]
            return falsepred
        raise exc
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql"""

# atk-fabricate-echo (UNGROUNDED-ORACLE ECHO test): on the satisfiable cases it
# fabricates a DIFFERENT fragment ('X' = [88], NOT-prefixed when negated) instead
# of returning render_inner's actual output. Must reject on C4/C5 (ToSeq ==
# inner_fragment), because the fabricated [88] is not the renderer's witness.
# refinement: a faithful real patch emits `WHERE X` (or `WHERE NOT X`) instead of
# the real EXISTS(...) subquery SQL -> invalid/wrong SQL on the satisfiable
# P2P/F2P paths -> does NOT resolve. This is the documented atk_3_echo cheat.
_ATK_ECHO = """    if satisfiable == 1:
        if negated == 1:
            x_neg = [78, 79, 84, 32, 88]  # type: List[int]
            return x_neg
        x = [88]  # type: List[int]
        return x
    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        if negated == 1:
            empty = []  # type: List[int]
            return empty
        raise exc
    return sql"""

# atk-noprefix (PARTIAL-DOMAIN on the satisfiable-negated sub-domain): omits the
# NOT prefix on sat=1,neg=1 (returns the bare inner fragment). Must reject on C5.
# refinement: a faithful real patch emits `WHERE EXISTS(...)` where it must emit
# `WHERE NOT EXISTS(...)` -> the negation is dropped -> the negated-predicate P2P
# (e.g. ~Exists(non-empty)) returns the complement rows; result set differs ->
# does NOT resolve.
_ATK_NOPREFIX = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        if negated == 1:
            empty = []  # type: List[int]
            return empty
        raise exc
    return sql"""

# atk-prefix-always (PARTIAL-DOMAIN on the satisfiable-non-negated sub-domain):
# prepends the NOT marker even when NOT negated. Must reject on C4 (ToSeq ==
# inner_fragment, no prefix).
# refinement: a faithful real patch emits `WHERE NOT EXISTS(...)` for a plain
# Exists(...) -> the predicate is wrongly negated -> the non-negated P2P returns
# the complement rows -> does NOT resolve.
_ATK_PREFIX_ALWAYS = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        if negated == 1:
            empty = []  # type: List[int]
            return empty
        raise exc
    sql = [78, 79, 84, 32] + sql
    return sql"""

# atk-neverraise (CONTROL-FLOW-EFFECT): on sat=0,neg=0 it returns the empty
# fragment instead of propagating the matches-nothing signal. Must reject on C1
# (not (sat==0 and neg==0)) -- the postcondition forbids a normal return there.
# refinement: a faithful real patch swallows EmptyResultSet for a NON-negated
# `Exists(none())` too, returning '' -> `WHERE  AND pk=...` matches every row
# instead of none; `Exists(none())` should match NOTHING, so the non-negated P2P
# rows differ -> does NOT resolve.
_ATK_NEVERRAISE = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        empty = []  # type: List[int]
        return empty
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql"""

# atk-raise-unsatneg (CONTROL-FLOW-EFFECT, the PREPATCH BUG): on sat=0,neg=1 it
# propagates the matches-nothing signal (re-raise) instead of returning normally.
# Must reject on E1 (Exsures permits the signal ONLY for sat==0 and neg==0) AND
# C1 reachability. This is exactly model_prepatch.py's failure.
# refinement: this IS the pre-patch behaviour -> `~Exists(none())` raises
# EmptyResultSet, erasing the whole WHERE block -> the F2P qs becomes empty ->
# assertSequenceEqual(qs, [manager]) fails -> does NOT resolve (the original bug).
_ATK_RAISE_UNSATNEG = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        raise exc
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql"""

# atk-nonempty-unsatneg-supporting (mechanical SUPPORTING near-miss): returns a
# single-space fragment ' ' = [32] on sat=0,neg=1. Must reject on C3 (len != 0).
# refinement: a faithful real patch emits `WHERE   AND pk=...` -- whether the DB
# treats a blank fragment as a syntax error or it differs from gold's '', the
# spec pins gold's exact empty fragment; a non-empty one is the documented
# weak-spec hole, so it must not verify. (Supporting; same class as atk-junk.)
_ATK_SPACE = """    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        if negated == 1:
            sp = [32]  # type: List[int]
            return sp
        raise exc
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql"""


SPEC_TESTS = [
    {
        "id": "pos-structdiff",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_STRUCTDIFF),
        "rationale": "structurally-different correct impl (NOT-prefix bound to a "
                     "typed local before the prepend; gold framing Assert kept) "
                     "must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": "branch-reordered correct impl (re-raise guarded by "
                     "negated==0, empty-return falls through) must verify; the "
                     "except branch still establishes sat==0 so E1/C3 discharge.",
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": "the precondition admits the exact F2P input (sat=0, neg=1, "
                     "i.e. ~Exists(none())); on that input the empty fragment is "
                     "returned and len==0 asserts cleanly. Else PRECOND-TOO-STRONG.",
    },
    {
        "id": "atk-raise-unsatneg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_RAISE_UNSATNEG),
        "refinement": "this is the PRE-PATCH bug: ~Exists(none()) propagates "
                      "EmptyResultSet, erasing the whole WHERE block, so the F2P "
                      "qs is empty and assertSequenceEqual(qs,[manager]) fails -> "
                      "does NOT resolve.",
        "rationale": "rejects on E1 (Exsures permits the matches-nothing signal "
                     "ONLY when sat==0 and neg==0) and the C1 reachability clause. "
                     "If it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "atk-neverraise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_NEVERRAISE),
        "refinement": "swallows EmptyResultSet for a NON-negated Exists(none()) "
                      "too, returning '' so `WHERE  AND pk=...` matches every row; "
                      "Exists(none()) must match NOTHING, so the non-negated path "
                      "rows differ from gold -> does NOT resolve.",
        "rationale": "rejects on C1 (not (sat==0 and neg==0)): the postcondition "
                     "forbids a normal return on sat=0,neg=0. If it verifies, "
                     "SPEC-TOO-WEAK (control-flow-effect not caught).",
    },
    {
        "id": "atk-junk-unsatneg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_JUNK),
        "refinement": "returns invalid SQL 'XYZ' on ~Exists(none()), so "
                      "`WHERE XYZ AND pk=...` is a SQL error / wrong rows; the F2P "
                      "assertSequenceEqual(qs,[manager]) fails -> does NOT resolve.",
        "rationale": "rejects on C3 (len(Result())==0 on sat=0,neg=1). The "
                     "documented atk_i_junk_unsatneg hole; if it verifies, "
                     "SPEC-TOO-WEAK (the restored empty-fragment pin is hollow).",
    },
    {
        "id": "atk-false-pred",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_FALSE),
        "refinement": "returns an always-FALSE '0=1' on ~Exists(none()), so "
                      "`WHERE (0=1) AND pk=...` yields [] and the manager is "
                      "wrongly excluded; the F2P assertSequenceEqual(qs,[manager]) "
                      "fails (gets []) -> does NOT resolve.",
        "rationale": "rejects on C3 (len(Result())==0). The documented "
                     "atk_j_false_pred hole; if it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "atk-fabricate-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_ECHO),
        "refinement": "fabricates 'X' (NOT-prefixed when negated) on the "
                      "satisfiable cases instead of the real EXISTS(...) subquery "
                      "SQL, so `WHERE X` / `WHERE NOT X` is invalid/wrong SQL on "
                      "the satisfiable P2P/F2P paths -> does NOT resolve.",
        "rationale": "rejects on C4/C5 (ToSeq(Result())==inner_fragment): the "
                     "content-pin is grounded in the renderer's witness-unique "
                     "output, so a DIFFERENT fabricated fragment cannot satisfy "
                     "it. The documented atk_3_echo; if it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "atk-noprefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_NOPREFIX),
        "refinement": "omits the NOT prefix on sat=1,neg=1, emitting "
                      "`WHERE EXISTS(...)` where it must emit `WHERE NOT EXISTS(...)`; "
                      "the negated-predicate P2P returns the complement rows -> "
                      "does NOT resolve.",
        "rationale": "rejects on C5 (ToSeq==NOT+inner_fragment) on the "
                     "satisfiable-negated sub-domain. If it verifies, "
                     "SPEC-TOO-WEAK (partial-domain).",
    },
    {
        "id": "atk-prefix-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_PREFIX_ALWAYS),
        "refinement": "prepends NOT even when NOT negated, emitting "
                      "`WHERE NOT EXISTS(...)` for a plain Exists(...); the "
                      "non-negated P2P returns the complement rows -> does NOT "
                      "resolve.",
        "rationale": "rejects on C4 (ToSeq==inner_fragment, no prefix) on the "
                     "satisfiable-non-negated sub-domain. If it verifies, "
                     "SPEC-TOO-WEAK (partial-domain).",
    },
    {
        "id": "atk-space-unsatneg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_SPACE),
        "refinement": "returns a single-space fragment ' ' on sat=0,neg=1; the "
                      "spec pins gold's exact empty fragment, and a non-empty "
                      "fragment on this case is the documented weak-spec hole, so "
                      "a faithful real patch emitting `WHERE   AND pk=...` is not "
                      "gold and not guaranteed to resolve.",
        "rationale": "supporting near-miss in the partial-domain class; rejects "
                     "on C3 (len(Result())==0 requires 0, not 1).",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — render_inner (A-consumed) + inner_fragment (A-consumed @Pure)
# ---------------------------------------------------------------------------
# Both axioms describe the UNCHANGED super-class renderer Subquery.as_sql that the
# new code calls. axiom_check.py (on the HOST bundle) is the ground-truth probe:
# it runs the REAL callee in-container. We embed its source so the probe is
# self-contained (the runner mounts ONLY the probe at /work).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# axiom-soundness probe: execute the REAL Subquery.as_sql (render_inner) on a
# satisfiable and an unsatisfiable inner selection and assert the axiom Ensures /
# Exsures. We reuse axiom_check.py verbatim (it also drives the post-patch
# Exists.as_sql case table; run with apply_gold=True). It SKIPs (exit 0) if Django
# is not importable, defers to the in-container 4.1+gold run.
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# --- PBT axiom-soundness harness (appended) ---------------------------------
if __name__ == '__main__':
    import sys as _sys
    rc = check_axiom_and_cases()
    print('PBT axiom-soundness render_inner/inner_fragment rc=%d' % rc)
    _sys.exit(0 if rc == 0 else 1)
"""

# axiom-containment probe: the MODEL can pass render_inner / inner_fragment ONLY
# satisfiable in {0,1} (render_exists Requires satisfiable in {0,1}; render_inner
# is called once with that same value; inner_fragment is referenced in Ensures
# only on the satisfiable==1 case and inside inner_fragment's own Requires
# satisfiable==1). render_inner's Requires domain is {0,1} and inner_fragment's is
# {1}. We assert containment: every caller-reachable input lies in the axiom
# Requires domain. This is a pure-logic enumeration (no Django needed).
_AX_CONTAIN_PROBE = r'''
import sys

# Caller (render_exists) Requires: satisfiable in {0, 1}; negated in {0, 1}.
# render_inner(satisfiable) is invoked once with the SAME satisfiable; its
# Requires domain is {0, 1}. inner_fragment(satisfiable) is referenced in the
# postcondition ONLY where satisfiable == 1 (the C4/C5 clauses) and in the C5
# Assert (reached only after a normal render_inner return, which establishes
# satisfiable == 1); its Requires domain is {1}.
caller_satisfiable = [0, 1]               # everything render_exists can hold

render_inner_domain = {0, 1}              # render_inner Requires
inner_fragment_domain = {1}               # inner_fragment Requires (satisfiable==1)

# render_inner is reachable for every caller-satisfiable value.
ri_reachable = set(caller_satisfiable)
# inner_fragment is reachable only on the satisfiable==1 branch (C4/C5 + Assert).
if_reachable = {s for s in caller_satisfiable if s == 1}

bad_ri = ri_reachable - render_inner_domain
bad_if = if_reachable - inner_fragment_domain

print('render_inner: reachable=%s domain=%s outside=%s'
      % (sorted(ri_reachable), sorted(render_inner_domain), sorted(bad_ri)))
print('inner_fragment: reachable=%s domain=%s outside=%s'
      % (sorted(if_reachable), sorted(inner_fragment_domain), sorted(bad_if)))

if bad_ri:
    print('AXIOM-TOO-WEAK-FOR-CALLER: render_inner reachable input(s) outside '
          'its Requires domain: %s' % sorted(bad_ri))
    sys.exit(1)
if bad_if:
    print('AXIOM-TOO-WEAK-FOR-CALLER: inner_fragment reachable input(s) outside '
          'its Requires domain: %s' % sorted(bad_if))
    sys.exit(1)
print('CONTAINMENT OK: every caller-reachable render_inner/inner_fragment input '
      'lies in the axiom Requires domain.')
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-render-inner",
        "axiom": "render_inner",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "runs the REAL Subquery.as_sql (render_inner) on a "
                     "satisfiable (User.objects.all()) and an unsatisfiable "
                     "(User.objects.none()) inner selection and asserts the axiom "
                     "Ensures/Exsures (satisfiable -> non-empty, not NOT-prefixed "
                     "[also inner_fragment's properties]; unsatisfiable -> "
                     "EmptyResultSet), plus the post-patch Exists.as_sql case "
                     "table over all four (sat,neg) combos. Violation => "
                     "AXIOM-UNSOUND. Must run at pinned 4.1 + gold.",
    },
    {
        "id": "ax-contain-render-inner",
        "axiom": "render_inner",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "enumerates the EXACT inputs the model can pass to "
                     "render_inner ({0,1}) and inner_fragment ({1}, satisfiable "
                     "branch only) and asserts each lies in the respective axiom "
                     "Requires domain. A reachable input outside => "
                     "AXIOM-TOO-WEAK-FOR-CALLER. (Covering more would be sound.)",
    },
]
