# properties.py — PBT falsification battery for sympy__sympy-11618.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant built by region-surgery that edits ONLY
# inside the `# impl-start` / `# impl-end` block (so the frozen spec — axioms,
# pure helpers, pre/post-conditions, signature — is byte-identical and
# same_spec holds). The runner stamps each with verify(host, Nagini) + same_spec.
#
# Defended surface (the spec this battery attacks):
#   point_distance(u: List[int], v: List[int]) -> int, where u and v are
#   READ-ONLY inputs (Acc(list_pred(u), 1/2) / Acc(list_pred(v), 1/2)). The
#   load-bearing postcondition is
#       Result() == root(psum(ToSeq(u), ToSeq(v),
#                             len(u) if len(u) >= len(v) else len(v)))
#   i.e. the result must be `root` of the squared-difference sum over EVERY axis
#   of the LARGER ambient dimension n = max(len(u), len(v)), with the shorter
#   vector zero-padded. `root` is a @Pure @ContractOnly opaque DETERMINISTIC
#   function with only Requires(x>=0)/Ensures(Result()>=0) — it pins no exact
#   value, so the discriminating content lives entirely in the ARGUMENT
#   `psum(..., max)`. A wrong impl that feeds root a different axis set / a
#   different sum produces root(other) and cannot equal root(psum(..., max)).
#
# Oracle grounding note (ungrounded-oracle class): `root` is NOT an answer-key
# oracle that an impl can echo — it takes a value derived from the inputs
# (psum over the args), fully unfolded by the pure region. There is no opaque
# "expected answer" to return; the only way to satisfy the postcondition is to
# build root's argument correctly. So the ungrounded-oracle-echo attack does not
# apply; in its place we supply an honest cheapest-correct positive control and
# the partial-domain attacks below (which corrupt root's argument).

from pathlib import Path

INSTANCE = "sympy__sympy-11618"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl-region body (everything between # impl-start and
# # impl-end, markers exclusive). Every variant is produced by _swap on _BASE
# touching ONLY text inside this block.
_GOLD_IMPL = """    n = len(u)
    if len(v) > n:
        n = len(v)
    acc = 0
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(u), 1 / 2))
        Invariant(Acc(list_pred(v), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        cu = 0
        if i < len(u):
            cu = u[i]
        cv = 0
        if i < len(v):
            cv = v[i]
        Assert(cu == coord(ToSeq(u), i))
        Assert(cv == coord(ToSeq(v), i))
        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
        acc = acc + (cu - cv) * (cu - cv)
        i = i + 1
    Assert(i == n)
    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
    Assert(acc == total)
    return root(total)"""


# Sanity: the gold impl text must appear verbatim and uniquely in _BASE.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drift — re-sync _GOLD_IMPL"


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — structurally different, still CORRECT.
#    Changes only the EXECUTABLE shape, keeps every gold invariant + per-axis
#    pin + the forward accumulation (so lemma_psum_unfold still discharges the
#    one-axis extension; NO loop-direction flip, NO dropped framing assert):
#      * compute n by starting from len(v) and lifting to len(u) (branch reorder
#        of the max), instead of starting from len(u);
#      * read cv before cu (statement reorder).
#    The postcondition argument n == max(len(u),len(v)) and the invariant
#    acc == psum(...,i) are unchanged, so the gold proof remains valid.
#    MUST verify — else SPEC-TOO-STRONG.
_POS_IMPL = """    n = len(v)
    if len(u) > n:
        n = len(u)
    acc = 0
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(u), 1 / 2))
        Invariant(Acc(list_pred(v), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        cv = 0
        if i < len(v):
            cv = v[i]
        cu = 0
        if i < len(u):
            cu = u[i]
        Assert(cu == coord(ToSeq(u), i))
        Assert(cv == coord(ToSeq(v), i))
        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
        acc = acc + (cu - cv) * (cu - cv)
        i = i + 1
    Assert(i == n)
    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
    Assert(acc == total)
    return root(total)"""


# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY — the precondition must ACCEPT a normal F2P-shaped input.
#    The Requires is permission-only (Acc(list_pred(u),1/2)); it places NO
#    length/value constraint, so an F2P-shaped pair like u=[1,0,2], v=[2,0]
#    (Point3D vs Point2D) is in-domain. We keep the full gold impl and add, at
#    the top of impl, derivable assertions that confirm the half-permission we
#    hold is real and usable (a 1/4 read share is obtainable; both lengths are
#    readable and non-negative). If this fails to verify => PRECOND-TOO-STRONG.
_ADMISS_IMPL = """    Assert(Acc(list_pred(u), 1 / 4))
    Assert(Acc(list_pred(v), 1 / 4))
    Assert(len(u) >= 0 and len(v) >= 0)
""" + _GOLD_IMPL


# ---------------------------------------------------------------------------
# 3. FRAME-MUTATION (MANDATORY — read-only inputs). A rival that WRITES to the
#    read-only input `u` to (vacuously) satisfy the postcondition. With only
#    Acc(list_pred(u), 1/2) the assignment u[0] = 0 requires FULL permission
#    and MUST be rejected for insufficient permission. Every gold invariant /
#    assert is kept verbatim so the rejection is attributable to the WRITE, not
#    to a proof gap. expect=reject.
#    Refinement: the repo callee receives `self.args` / `p.args`, which are
#    immutable coordinate tuples; a faithful real patch cannot mutate them, and
#    one that copied-then-mutated the coordinate vector before summing would
#    compute the distance from ALTERED coordinates — e.g. zeroing the first
#    coordinate turns Point3D(1,0,2).distance(Point2D(2,0)) from sqrt(5) into
#    sqrt(4)=2, failing F2P test_issue_11617. So a verifying mutator would be a
#    true verify⇏resolve break.
_FRAME_IMPL = _swap(
    _GOLD_IMPL,
    "    acc = 0\n    i = 0",
    "    u[0] = 0\n    acc = 0\n    i = 0",
)


# ---------------------------------------------------------------------------
# 4. PARTIAL-DOMAIN (min-truncation) — the LITERAL pre-patch bug. Walk the two
#    coordinate streams only as far as the SHORTER one reaches
#    (n = min(len(u),len(v))), dropping every axis present only in the longer
#    vector. Invariants/asserts are adjusted to the min-fold so this fails ONLY
#    on the postcondition (root(psum(...,min)) is not provably
#    root(psum(...,max)) when the longer tail is non-zero), exactly as
#    model_prepatch.py does. expect=reject.
#    Refinement: this is the pre-patch truncating zip. On F2P
#    Point3D(1,0,2).distance(Point2D(2,0)), min=2 gives sqrt((1-2)**2+0)=sqrt(1)=1,
#    not sqrt(5) — F2P test_issue_11617 FAILS. The canonical verify⇏resolve case.
_MIN_IMPL = """    n = len(u)
    if len(v) < n:
        n = len(v)
    acc = 0
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(u), 1 / 2))
        Invariant(Acc(list_pred(v), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == (len(u) if len(u) <= len(v) else len(v)))
        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        cu = 0
        if i < len(u):
            cu = u[i]
        cv = 0
        if i < len(v):
            cv = v[i]
        Assert(cu == coord(ToSeq(u), i))
        Assert(cv == coord(ToSeq(v), i))
        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
        acc = acc + (cu - cv) * (cu - cv)
        i = i + 1
    Assert(i == n)
    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) <= len(v) else len(v))
    Assert(acc == total)
    return root(total)"""


# ---------------------------------------------------------------------------
# 5. PARTIAL-DOMAIN (drop-last-axis) — correct on most of the domain but loses
#    the FINAL axis of the larger ambient dimension. n is set to max-1 (clamped
#    at 0). Invariant/asserts track n = max-1, so it can only fail on the
#    postcondition (psum over max-1 != psum over max when the last axis
#    contributes). expect=reject.
#    Refinement: on F2P Point3D(1,0,2).distance(Point2D(2,0)) the larger
#    dimension is 3, so this sums only axes 0,1 = (1-2)**2 + 0 = 1 -> sqrt(1)=1,
#    dropping axis 2's coordinate (2 -> +4). F2P expects sqrt(5); FAILS. A real
#    patch with an off-by-one upper bound (range(n-1) / max-1) would not resolve.
_DROPLAST_IMPL = """    m = len(u)
    if len(v) > m:
        m = len(v)
    n = m - 1
    if n < 0:
        n = 0
    acc = 0
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(u), 1 / 2))
        Invariant(Acc(list_pred(v), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(m == (len(u) if len(u) >= len(v) else len(v)))
        Invariant(n == (m - 1 if m - 1 >= 0 else 0))
        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        cu = 0
        if i < len(u):
            cu = u[i]
        cv = 0
        if i < len(v):
            cv = v[i]
        Assert(cu == coord(ToSeq(u), i))
        Assert(cv == coord(ToSeq(v), i))
        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
        acc = acc + (cu - cv) * (cu - cv)
        i = i + 1
    Assert(i == n)
    total = psum(ToSeq(u), ToSeq(v), n)
    Assert(acc == total)
    return root(total)"""


# ---------------------------------------------------------------------------
# 6. UNGROUNDED-CONSTANT echo (supporting) — the cheapest impl that ignores the
#    inputs and returns root(0). root(0) >= 0 satisfies root's own Ensures, but
#    the postcondition demands Result() == root(psum(...,max)); since root is a
#    DETERMINISTIC opaque function (not the constant 0), root(0) is not provably
#    equal to root(psum(...,max)) for an arbitrary input. expect=reject.
#    Refinement: returning 0 for every distance makes
#    Point3D(1,0,2).distance(Point2D(2,0)) == 0 != sqrt(5); F2P FAILS. This is
#    the degenerate "no work done" rival — a verifying one would mean the
#    postcondition does not actually pin root's argument to the padded sum.
_ZERO_IMPL = """    return root(0)"""


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: computes n = max by "
            "lifting from len(v) instead of len(u) and reads cv before cu; "
            "keeps every gold invariant/per-axis pin and the forward "
            "lemma_psum_unfold accumulation, so the gold proof stays valid. "
            "Must verify; if it cannot, the postcondition is SPEC-TOO-STRONG "
            "(rejects a faithful correct implementation)."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
        "rationale": (
            "the precondition is permission-only (Acc(list_pred,1/2)), placing "
            "no length/value constraint; an F2P-shaped pair (u=[1,0,2], "
            "v=[2,0]) is in-domain. The added top-of-impl assertions confirm a "
            "1/4 read share is derivable from the 1/2 held and both lengths are "
            "readable. Must verify; if it cannot, PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutate-readonly-u",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_IMPL),
        "refinement": (
            "the repo callee reads immutable coordinate tuples (self.args / "
            "p.args); a faithful patch cannot mutate them. One that copied and "
            "zeroed the first coordinate before summing would compute the "
            "distance from ALTERED coordinates: Point3D(1,0,2).distance("
            "Point2D(2,0)) would become sqrt((0-2)**2+0+4)=sqrt(8) (or sqrt(4) "
            "depending on which side), never sqrt(5) -> F2P test_issue_11617 "
            "FAILS. So a verifying mutator is a true verify-not-resolve break."
        ),
        "rationale": (
            "REJECT must come from the PERMISSION SYSTEM: u holds only "
            "Acc(list_pred(u),1/2); the write u[0]=0 needs full permission and "
            "is rejected for insufficient permission. Every gold "
            "invariant/assert is kept verbatim so the failure is attributable "
            "to the write, not a proof gap. If it verifies, the frame is "
            "unguarded (FRAME-MUTATION SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-min-truncation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _MIN_IMPL),
        "refinement": (
            "this is the literal PRE-PATCH truncating zip (n = min(len(u),"
            "len(v))), dropping every axis present only in the longer vector. "
            "On F2P Point3D(1,0,2).distance(Point2D(2,0)) min=2 gives "
            "sqrt((1-2)**2 + (0-0)**2) = sqrt(1) = 1, not sqrt(5); "
            "test_issue_11617 FAILS. The canonical verify-not-resolve rival "
            "(== model_prepatch.py)."
        ),
        "rationale": (
            "REJECT comes from the postcondition clause Result() == "
            "root(psum(...,max)): the impl returns root(psum(...,min)) and, "
            "because root is an OPAQUE DETERMINISTIC function, "
            "root(psum(...,min)) != root(psum(...,max)) whenever the longer "
            "vector has a non-zero tail. If it verifies, the spec does not "
            "force summation over the larger ambient dimension (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-drop-last-axis",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DROPLAST_IMPL),
        "refinement": (
            "off-by-one upper bound: sums axes 0..max-2, dropping the FINAL "
            "axis of the larger ambient dimension. On F2P Point3D(1,0,2)."
            "distance(Point2D(2,0)) max=3 so it sums axes 0,1 = 1, dropping "
            "axis 2 (coordinate 2 -> +4); gives sqrt(1)=1 not sqrt(5); "
            "test_issue_11617 FAILS. A real range(n-1)/max-1 bound would not "
            "resolve."
        ),
        "rationale": (
            "REJECT comes from Result() == root(psum(...,max)): the impl "
            "returns root(psum(...,max-1)), and the deterministic root makes "
            "that unequal to root(psum(...,max)) when the last axis "
            "contributes. If it verifies, the postcondition leaves the final "
            "axis unpinned (partial-domain SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "ungrounded-constant-root-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ZERO_IMPL),
        "refinement": (
            "returns root(0) for EVERY input, doing no work. Then "
            "Point3D(1,0,2).distance(Point2D(2,0)) == 0 != sqrt(5); "
            "test_issue_11617 FAILS (and every non-zero-distance P2P case "
            "fails too). A real patch returning a constant 0 distance would "
            "not resolve."
        ),
        "rationale": (
            "REJECT comes from Result() == root(psum(...,max)): root is a "
            "DETERMINISTIC opaque function, so root(0) is not provably equal to "
            "root(psum(...,max)) for an arbitrary input even though root(0)>=0 "
            "satisfies root's own Ensures. Confirms the postcondition pins "
            "root's ARGUMENT to the padded sum, not merely the sign of the "
            "result. If it verifies, the spec is hollow (SPEC-TOO-WEAK)."
        ),
    },
]


# No @ContractOnly axiom is consumed beyond `root`, and `psum` is an
# A-reference deep model. Both are already exercised in-container by
# axiom_check.py (G-AX) against the REAL patched sympy.geometry Point.distance
# and the real sympy.sqrt. We mirror the two G-AX obligations as PBT axiom
# probes so the battery re-runs them independently:
#   * axiom-soundness (root): the real sqrt is deterministic and non-negative
#     on every non-negative argument in root's Requires domain (x>=0).
#   * axiom-containment (root): every argument the MODEL can pass to root is
#     psum(...,max) which is Ensures(Result()>=0) >= 0, i.e. always inside
#     root's Requires domain x>=0 — re-checked by running the real distance and
#     confirming its squared sum is >= 0 across the modeled domain.
# Both probes import only sympy + stdlib, open nothing on disk, exit 0 iff the
# obligation holds.

_ROOT_SOUNDNESS_PROBE = r'''
import random, sys
from sympy import sqrt, Integer

# root axiom: Requires(x >= 0); Ensures(Result() >= 0). The proof consumes that
# root is a DETERMINISTIC function (equal args -> equal results) and
# non-negative. Confirm the REAL sympy.sqrt meets both on x >= 0.
def check(x):
    r1 = sqrt(Integer(x))
    r2 = sqrt(Integer(x))
    if r1 != r2:
        print("AXIOM-UNSOUND: sqrt not deterministic on %d: %r vs %r" % (x, r1, r2))
        sys.exit(1)
    if not bool(r1.is_nonnegative):
        print("AXIOM-UNSOUND: sqrt(%d) not non-negative: %r" % (x, r1))
        sys.exit(1)

boundary = [0, 1, 2, 3, 4, 5, 8, 9, 16, 25, 41, 61, 100, 99999, 10**6]
for x in boundary:
    check(x)
rng = random.Random(11618)
for _ in range(3000):
    check(rng.randint(0, 10 ** 7))
print("AXIOM-SOUND: real sqrt deterministic and non-negative on %d boundary + 3000 fuzz non-negative ints (root Requires domain x>=0)" % len(boundary))
sys.exit(0)
'''


_ROOT_CONTAINMENT_PROBE = r'''
import random, sys
from sympy import sqrt, Integer
from sympy.geometry import Point, Point2D, Point3D

# Containment: every argument the MODEL feeds to `root` is
# psum(u, v, max(len(u),len(v))) = sum of squared coordinate differences, which
# psum's Ensures pins to Result() >= 0. So the model can ONLY ever reach
# arguments in root's Requires domain (x >= 0). We confirm this empirically by
# computing that exact padded sum over the modeled domain (equal dim, or
# distinct concrete type) and asserting it is always >= 0 (never negative),
# i.e. always inside x >= 0. A negative reachable argument would be
# AXIOM-TOO-WEAK-FOR-CALLER. (Squares of integers are non-negative, so this
# must hold; the probe is the executable witness.)
def coord(s, i):
    return s[i] if i < len(s) else 0

def padded_squared_sum(u, v):
    n = max(len(u), len(v))
    t = 0
    for i in range(n):
        d = coord(u, i) - coord(v, i)
        t += d * d
    return t

def in_modeled_domain(pu, pv):
    return len(pu) == len(pv) or type(pu) is not type(pv)

# boundary args the model reaches, incl. the F2P witness orientation
boundary = [
    ([1, 0, 2], [2, 0]),       # F2P Point3D vs Point2D
    ([2, 0], [1, 0, 2]),
    ([0, 0], [0, 0]),          # zero sum
    ([4, -2, 6], [1, 2, 3]),
    ([0, 0, 0, 0, 5], [0, 0]), # large-gap distinct type
]
for u, v in boundary:
    s = padded_squared_sum(u, v)
    if s < 0:
        print("AXIOM-TOO-WEAK-FOR-CALLER: model reaches negative root arg %d on u=%r v=%r" % (s, u, v))
        sys.exit(1)
    # the squared sum is exactly what the real distance squares back to (real
    # callee on the modeled domain), confirming the reachable arg set:
    if u == [1, 0, 2] and v == [2, 0]:
        if Point3D(*u).distance(Point2D(*v)) != sqrt(Integer(s)):
            print("AXIOM containment: real F2P distance disagrees with sqrt(model arg)")
            sys.exit(1)

rng = random.Random(116180)
checked = 0
attempts = 0
while checked < 3000 and attempts < 50000:
    attempts += 1
    du = rng.randint(1, 5)
    dv = rng.randint(1, 5)
    u = [rng.randint(-6, 6) for _ in range(du)]
    v = [rng.randint(-6, 6) for _ in range(dv)]
    pu, pv = Point(u), Point(v)
    if not in_modeled_domain(pu, pv):
        continue
    s = padded_squared_sum(u, v)
    if s < 0:
        print("AXIOM-TOO-WEAK-FOR-CALLER: negative root arg %d on u=%r v=%r" % (s, u, v))
        sys.exit(1)
    checked += 1
print("AXIOM-COVERED: every model-reachable root argument is >= 0 (in root Requires x>=0) across %d boundary + %d fuzz modeled-domain pairs" % (len(boundary), checked))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-root-soundness",
        "axiom": "root",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _ROOT_SOUNDNESS_PROBE,
        "rationale": (
            "root models the UNCHANGED sympy.sqrt; the proof consumes only "
            "determinism + non-negativity on x>=0. If the real sqrt were "
            "non-deterministic or negative on a non-negative argument, the "
            "axiom would be AXIOM-UNSOUND. Mirrors axiom_check.py's root check."
        ),
    },
    {
        "id": "ax-root-containment",
        "axiom": "root",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _ROOT_CONTAINMENT_PROBE,
        "rationale": (
            "the only argument the model passes to root is psum(...,max), a sum "
            "of integer squares pinned >= 0 by psum's Ensures, hence always "
            "inside root's Requires domain x>=0. A reachable negative argument "
            "would be AXIOM-TOO-WEAK-FOR-CALLER. Confirmed empirically over the "
            "modeled domain, cross-checked against the real F2P distance."
        ),
    },
]
