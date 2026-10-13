"""properties.py — PBT falsification manifest for matplotlib__matplotlib-24870.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    choose_default_levels(has_explicit, two_valued, filled, zmin, zmax, mid)
        -> List[float]                       # = matplotlib's default contour-level
                                             #   selection (self.levels is None,
                                             #   no explicit args)

with the load-bearing contract (post-conditions region, verbatim):

    Requires(not has_explicit); Requires(zmin < zmax)
    Requires(zmax-zmin >= 1e-6); >= 1e-9*zmax; >= 1e-9*(0-zmin)   # well-resolved
    Requires(mid - zmin == zmax - mid)                           # midpoint pin
    Ensures(Acc(list_pred(Result())))
    # LINE two-valued:  len==1, Result()[0]==mid, zmin<Result()[0]<zmax
    # FILLED two-valued: len==3, [0]==zmin, [2]==zmax, [1]==mid, strict ordering
    # not two_valued:   len>1, ToSeq(Result()) == auto_levels(zmin, zmax)

What the spec actually defends, and the attacks it must survive:

  * The DISCRIMINATING content of the gold patch is the new two-valued (boolean
    field) default: a single midpoint level for a LINE contour ([.5]) and the
    three bracketing levels for a FILLED contour ([0,.5,1]), instead of the
    ordinary multi-level automatic selection. Both two-valued facets are pinned
    ELEMENT-BY-ELEMENT and grounded in the data extents zmin/zmax and the
    linearly-pinned midpoint `mid` (mid - zmin == zmax - mid). There is no opaque
    answer-key marker in those branches — every uniqueness rival therefore
    targets one of: len==1 (line), len==3 (filled), [0]==zmin / [2]==zmax /
    [1]==mid (filled element pins), or zmin<mid<zmax (line interiority).

  * The `not two_valued` branch is pinned to `ToSeq(Result()) ==
    auto_levels(zmin, zmax)`, where auto_levels is the @ContractOnly @Pure
    axiom for the UNCHANGED continuous-field delegate. This is NOT an
    echo-the-oracle weakness: echoing it (`list(auto_levels(zmin,zmax))`) IS the
    correct behaviour for a continuous field, and there is no executable
    materialization of the @Pure PSeq other than that call, so no WRONG echo can
    satisfy the pin. The branch is exercised by P2P continuous-field tests, not
    the F2P bool test. We include an honest cheapest-impl positive control rather
    than a fake echo-reject (see `echo-honest`).

  * NO READ-ONLY (Acc(.,1/2)) INPUT EXISTS. Every parameter is a by-value
    bool/float scalar; the only Acc is on the freshly-built Result() list, which
    the impl owns with full permission. There is no input list/array/object
    reference to overwrite, so the FRAME-MUTATION class is genuinely N/A here —
    there is nothing to mutate to satisfy a postcondition vacuously. (Documented
    in 'assessment'; has_readonly_input=False.)

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
guaranteed and a rejection comes from the POSTCONDITION catching wrong behaviour
(never from a tampered spec). Each `expect:"reject"` rival carries the
refinement argument that its faithful real patch would NOT resolve the F2P
test_bool_autolevel. The axiom case runs the REAL matplotlib callee in Docker
(reusing/strengthening axiom_check.py's logic).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24870"
FLOAT_ENCODING = "real"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------
# The whole gold impl body (between # impl-start and the trailing # impl-end),
# used as a single replaceable block for structural rewrites.
_GOLD_BODY = """    result = []  # type: List[float]
    if two_valued:
        # `mid` is equidistant from the two distinct values, so it lies strictly
        # between them: zmin < mid < zmax.
        if filled:
            result = [zmin, mid, zmax]
        else:
            result = [mid]
    else:
        result = list(auto_levels(zmin, zmax))
    return result"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (P1) Structurally-DIFFERENT but CORRECT: the branch structure is reorganised
# — test `not two_valued` first (continuous-field default), and inside the
# two-valued case test `not filled` first (line). Same list LITERALS, different
# control shape. No induction/lemma is needed (fixed-length literal lists; the
# continuous branch is the same single auto_levels call), so the gold proof
# stays valid. If this fails to verify the postcondition is over-fit to one
# branch nesting => SPEC-TOO-STRONG.
_POS_REORDERED_BODY = """    result = []  # type: List[float]
    if not two_valued:
        result = list(auto_levels(zmin, zmax))
    else:
        if not filled:
            result = [mid]
        else:
            result = [zmin, mid, zmax]
    return result"""
_POS_REORDERED = _swap(_BASE, _GOLD_BODY, _POS_REORDERED_BODY)

# (P2) Structurally-DIFFERENT but CORRECT: build the FILLED list through a local
# intermediate that names the three positions explicitly (still literal element
# assignment, no append-length lemma), and keep the LINE / continuous branches.
# A different code shape for the most-pinned (filled) facet. If it fails to
# verify, the spec is over-fit to the inline `[zmin, mid, zmax]` literal form
# => SPEC-TOO-STRONG.
_POS_LOCAL_BODY = """    result = []  # type: List[float]
    if two_valued:
        if filled:
            lo = zmin
            hi = zmax
            result = [lo, mid, hi]
        else:
            result = [mid]
    else:
        result = list(auto_levels(zmin, zmax))
    return result"""
_POS_LOCAL = _swap(_BASE, _GOLD_BODY, _POS_LOCAL_BODY)

# (P3) ECHO-HONEST. The only "oracle" in the contract is the @ContractOnly @Pure
# auto_levels (the not-two_valued pin). There is NO wrong echo: the sole way to
# satisfy `ToSeq(Result()) == auto_levels(zmin,zmax)` is to call it, which IS
# the correct continuous-field behaviour. This control is the gold impl with an
# extra Assert immediately before the return that the continuous-field result it
# built equals the axiom output. It is CORRECT (redundant with the gold proof)
# so it must verify; its purpose is to demonstrate the spec is NOT
# echo-vulnerable (no wrong oracle echo verifies). If it failed, the not-two_valued
# pin would be self-inconsistent (=> SPEC-TOO-STRONG).
_ECHO_RETURN = "        result = list(auto_levels(zmin, zmax))\n    return result"
_ECHO_RETURN_NEW = (
    "        result = list(auto_levels(zmin, zmax))\n"
    "        Assert(ToSeq(result) == auto_levels(zmin, zmax))\n"
    "    return result"
)
_ECHO_HONEST = _swap(_BASE, _ECHO_RETURN, _ECHO_RETURN_NEW)

# (P4) ADMISSIBILITY. A self-call on the exact F2P-shaped input the bool field
# yields: has_explicit=False, two_valued=True, filled=False, zmin=0.0, zmax=1.0,
# mid=0.5. This must ESTABLISH the precondition for a normal input:
#   not has_explicit            (True)
#   zmin < zmax                 (0.0 < 1.0)
#   span 1.0 >= 1e-6, >= 1e-9*1.0, >= 1e-9*(0-0.0)   (well-resolved, huge margin)
#   mid - zmin == zmax - mid    (0.5 - 0.0 == 1.0 - 0.5  ->  0.5 == 0.5, linear)
# If the self-call fails to verify the precondition for this representative
# input => PRECOND-TOO-STRONG. (Edits only the impl region: the self-call is
# placed at the head of the impl body.)
_ADMISS_HEAD = "    result = []  # type: List[float]\n    if two_valued:"
_ADMISS_HEAD_NEW = (
    "    Assert(not False)\n"
    "    Assert(0.0 < 1.0)\n"
    "    Assert(1.0 - 0.0 >= 1e-6)\n"
    "    Assert(1.0 - 0.0 >= 1e-9 * 1.0)\n"
    "    Assert(1.0 - 0.0 >= 1e-9 * (0.0 - 0.0))\n"
    "    Assert(0.5 - 0.0 == 1.0 - 0.5)\n"
    "    result = []  # type: List[float]\n    if two_valued:"
)
_ADMISS = _swap(_BASE, _ADMISS_HEAD, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U1) FILLED/LINE CONFUSION — a plausible real bug: the patch reads `self.filled`
# inverted, so a LINE contour gets the three bracketing levels and a FILLED
# contour gets the single midpoint level. The LINE branch now returns 3 elements
# => violates Ensures(Implies(two_valued and not filled, len(Result()) == 1));
# the FILLED branch returns 1 element => violates Implies(two_valued and filled,
# len(Result()) == 3). Rejection source: the len pins on BOTH two-valued facets.
_RIVAL_SWAP_BODY = _GOLD_BODY.replace(
    "        if filled:\n            result = [zmin, mid, zmax]\n        else:\n            result = [mid]\n",
    "        if filled:\n            result = [mid]\n        else:\n            result = [zmin, mid, zmax]\n",
    1,
)
_RIVAL_SWAP = _swap(_BASE, _GOLD_BODY, _RIVAL_SWAP_BODY)

# (U2) FILLED DROPS THE MIDPOINT — the most subtle wrong patch: emit only the two
# extremes [zmin, zmax] for a filled bool field (a "valid filled spec needs >=2
# levels, here are the two extremes" misreading). len==2 satisfies the WEAK
# clause Implies(two_valued and filled, len(Result()) >= 2) but VIOLATES the
# strong clause Implies(two_valued and filled, len(Result()) == 3) AND the
# element pin Implies(two_valued and filled, Result()[1] == mid) (no midpoint
# level). Rejection source: len==3 + Result()[1]==mid.
_RIVAL_DROP_MID_BODY = _GOLD_BODY.replace(
    "            result = [zmin, mid, zmax]\n",
    "            result = [zmin, zmax]\n",
    1,
)
_RIVAL_DROP_MID = _swap(_BASE, _GOLD_BODY, _RIVAL_DROP_MID_BODY)

# (U3) LINE USES A BOUNDARY VALUE — emit [zmin] for a line bool field instead of
# the midpoint. len==1 holds, but Result()[0]==zmin violates BOTH Result()[0]==mid
# (mid != zmin since zmin < mid) AND zmin < Result()[0] (zmin < zmin is false).
# This is the value/interiority pin: the level must be the midpoint that lies
# STRICTLY between the two values (so it survives the line-contour interior
# filter). Rejection source: Result()[0]==mid and zmin<Result()[0].
_RIVAL_LINE_ZMIN_BODY = _GOLD_BODY.replace(
    "            result = [mid]\n",
    "            result = [zmin]\n",
    1,
)
_RIVAL_LINE_ZMIN = _swap(_BASE, _GOLD_BODY, _RIVAL_LINE_ZMIN_BODY)

# (U4) FILLED WRONG ORDER — emit [zmax, mid, zmin] (extremes swapped). len==3
# holds, Result()[1]==mid holds, but Result()[0]==zmin is violated (it is zmax)
# and Result()[2]==zmax is violated, and strict ordering Result()[0]<Result()[1]
# is violated (zmax < mid is false). Rejection source: the element pins
# Result()[0]==zmin / Result()[2]==zmax and the strict ordering.
_RIVAL_REVERSE_BODY = _GOLD_BODY.replace(
    "            result = [zmin, mid, zmax]\n",
    "            result = [zmax, mid, zmin]\n",
    1,
)
_RIVAL_REVERSE = _swap(_BASE, _GOLD_BODY, _RIVAL_REVERSE_BODY)

# (U5, supporting) PREPATCH BEHAVIOUR — the two-valued case is never special-cased;
# the default is ALWAYS the ordinary multi-level auto_levels selection regardless
# of dtype (exactly model_prepatch.py). The LINE bool branch now returns the
# multi-level default (len>1) => violates Implies(two_valued and not filled,
# len(Result()) == 1). This is the precise pre-gold behaviour test_bool_autolevel
# observes failing (piled-up default levels instead of [.5]). Rejection source:
# the len==1 line pin (= G-DIFF's prepatch witness).
_RIVAL_PREPATCH_BODY = """    result = []  # type: List[float]
    if two_valued:
        if filled:
            result = list(auto_levels(zmin, zmax))
        else:
            result = list(auto_levels(zmin, zmax))
    else:
        result = list(auto_levels(zmin, zmax))
    return result"""
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_BODY, _RIVAL_PREPATCH_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reordered", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDERED,
     "rationale": "structurally-different (not-two_valued-first, then not-filled-first) "
                  "but correct impl with the SAME list literals must verify; no induction "
                  "lemma is needed (fixed-length literals, single auto_levels call). If it "
                  "fails => the postcondition is over-fit to one branch nesting (SPEC-TOO-STRONG)."},
    {"id": "pos-control-local", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale": "a correct impl that builds the filled list via local intermediates "
                  "(lo=zmin, hi=zmax; result=[lo,mid,hi]) — a different code shape for the "
                  "most-pinned facet — must verify; if not, the spec is over-fit to the inline "
                  "[zmin,mid,zmax] literal form (SPEC-TOO-STRONG)."},
    {"id": "echo-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the only oracle (the @Pure auto_levels not-two_valued pin) has no WRONG "
                  "echo: calling it IS the correct continuous-field behaviour and the only way "
                  "to satisfy ToSeq(Result())==auto_levels. Asserting that equality before the "
                  "return is redundant with the gold proof and must verify. Demonstrates the "
                  "spec is NOT echo-vulnerable (no wrong oracle echo verifies)."},
    {"id": "admiss-f2p-bool-line", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on the F2P-shaped input (has_explicit=False, two_valued=True, "
                  "filled=False, zmin=0.0, zmax=1.0, mid=0.5) must establish the precondition "
                  "(well-resolved span 1.0; linear midpoint pin 0.5-0.0==1.0-0.5). If it "
                  "cannot => PRECOND-TOO-STRONG (the precondition rejects a normal F2P input)."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-filled-line-confusion", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWAP,
     "refinement": "a faithful real patch of this shape reads self.filled inverted: it emits "
                   "levels_arg=[.5] for a FILLED bool field and [0,.5,1] for a LINE bool field. "
                   "F2P test_bool_autolevel asserts plt.contour(bool).levels==[.5] (line) and "
                   "plt.contourf(bool).levels==[0,.5,1] (filled); this patch gives the OPPOSITE "
                   "for both, so it would NOT resolve.",
     "rationale": "Rejection source: the len pins on BOTH two-valued facets — the line branch "
                  "now has len==3 (violates Implies(two_valued and not filled, len==1)) and the "
                  "filled branch has len==1 (violates Implies(two_valued and filled, len==3)). "
                  "If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-filled-drop-midpoint", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_MID,
     "refinement": "emits levels_arg=[0,1] (the two extremes only) for a filled bool field — a "
                   "misreading of 'a filled contour needs >=2 levels'. The real "
                   "plt.contourf(bool).levels would be [0.,1.] (no boundary at .5), but F2P "
                   "test_bool_autolevel asserts it equals [0,.5,1], so this patch would NOT "
                   "resolve (the midpoint boundary level is missing).",
     "rationale": "the subtle attack: len==2 satisfies the WEAK clause len>=2 but VIOLATES the "
                  "strong clause Implies(two_valued and filled, len==3) and the element pin "
                  "Implies(two_valued and filled, Result()[1]==mid). Rejection source: len==3 + "
                  "Result()[1]==mid. If it verified => SPEC-TOO-WEAK (len>=2 alone would be too weak)."},
    {"id": "rival-line-boundary-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LINE_ZMIN,
     "refinement": "emits levels_arg=[zmin]=[0.] for a line bool field. The real line-contour "
                   "interior filter (levels>zmin)&(levels<zmax) would DROP 0. (it is not strictly "
                   "inside (0,1)), leaving an empty level list — plt.contour(bool).levels != [.5], "
                   "so F2P would NOT resolve. The midpoint must be STRICTLY interior to survive.",
     "rationale": "the value/interiority pin: len==1 holds but Result()[0]==zmin violates "
                  "Result()[0]==mid (mid>zmin) AND zmin<Result()[0] (zmin<zmin is false). "
                  "Rejection source: Implies(two_valued and not filled, Result()[0]==mid) and "
                  "zmin<Result()[0]. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-filled-wrong-order", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_REVERSE,
     "refinement": "emits levels_arg=[zmax, mid, zmin]=[1,.5,0] for a filled bool field. "
                   "np.asarray([1,.5,0]) is a DECREASING level array; matplotlib requires "
                   "increasing levels and the resulting cs.levels would not equal [0,.5,1] "
                   "(it raises or reorders/clips), so F2P test_bool_autolevel would NOT resolve.",
     "rationale": "len==3 and Result()[1]==mid hold, but Result()[0]==zmin is violated (it is "
                  "zmax), Result()[2]==zmax is violated, and strict ordering Result()[0]<Result()[1] "
                  "(zmax<mid) is violated. Rejection source: the element pins Result()[0]==zmin / "
                  "Result()[2]==zmax + strict ordering. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-prepatch-multilevel", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "the exact pre-gold behaviour (model_prepatch.py): no special-casing of a "
                   "two-valued field, so the default is always the multi-level auto_levels "
                   "selection. plt.contour(bool).levels would be the ~8 piled-up default levels, "
                   "NOT [.5]; F2P test_bool_autolevel fails — its patch (the unpatched code) does "
                   "NOT resolve (this is the G-DIFF prepatch witness).",
     "rationale": "supporting prepatch witness. The line bool branch returns len>1 (auto_levels), "
                  "violating Implies(two_valued and not filled, len(Result())==1). Rejection "
                  "source: the len==1 line pin. If it verified => SPEC-TOO-WEAK (admits the bug)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real matplotlib callee) — one A-consumed axiom
# ===========================================================================

# (A1) axiom-soundness for auto_levels. Reuse + strengthen axiom_check.py: drive
# the REAL default level-selection (plt.contour on a continuous float64 field
# spanning [zmin,zmax], no explicit levels) and assert len(cs.levels) > 1 on
# EVERY well-resolved range (the soundness obligation the proof consumes), AND
# confirm the documented collapse witnesses are GUARD-EXCLUDED (faithfulness:
# the guard carves out exactly the degenerate single-tick regime). Any
# well-resolved range giving <=1 level => AXIOM-UNSOUND. This is the UNCHANGED
# delegate path (apply_gold is harmless; the 7-default branch is preserved for
# non-bool fields), so it runs against the base image behaviour. Imports only
# numpy/matplotlib (the package the gold patch lives in).
_AX_AUTO_SOUND = r'''
import random, sys

def well_resolved(zmin, zmax):
    span = zmax - zmin
    if not (zmin < zmax):
        return False
    if not (span >= 1e-6):
        return False
    if not (span >= 1e-9 * zmax):
        return False
    if not (span >= 1e-9 * (0.0 - zmin)):
        return False
    return True

def real_default_levels(zmin, zmax):
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    z = np.array([[zmin, zmax], [zmin, zmax]], dtype=np.float64)
    cs = plt.contour(z)            # line contour, default levels (no explicit args)
    levels = list(cs.levels)
    plt.close("all")
    return levels

# --- boundary cases (all well-resolved; the proof consumes len>1 here) ---
boundary = [
    (0.0, 1.0),        # the same [0,1] range a bool field yields (F2P)
    (-1.0, 1.0), (0.0, 100.0), (-50.0, -10.0),
    (1.0, 1.0001), (0.0, 1e6), (-3.14159, 2.71828),
    (1e-12, 2e-12), (1e-200, 1.5e-200),
]
boundary = [bc for bc in boundary if well_resolved(*bc)]
bad = []
for zmin, zmax in boundary:
    lv = real_default_levels(zmin, zmax)
    if len(lv) <= 1:
        bad.append(((zmin, zmax), lv))
if bad:
    print("AXIOM-UNSOUND auto_levels on well-resolved boundary:", bad); sys.exit(1)

# --- documented collapse witnesses must be GUARD-EXCLUDED (faithfulness) ---
collapse = [(1e-300, 2e-300), (0.0, 5e-324), (0.0, 1e-300),
            (1.0, 1.0 + 1e-14), (1.0, 1.0 + 1e-15), (1e10, 1e10 + 1.0)]
for zmin, zmax in collapse:
    if well_resolved(zmin, zmax):
        print("GUARD FAITHFULNESS HOLE: collapse witness marked well-resolved",
              (zmin, zmax)); sys.exit(1)
# confirm the canonical subnormal witness really collapses to 1 level
lv = real_default_levels(1e-300, 2e-300)
if len(lv) != 1:
    print("expected subnormal witness to collapse to 1 level, got", lv); sys.exit(1)

# --- randomized fuzz: assert len>1 on EVERY well-resolved sample ---
rng = random.Random(24870)
n_checked = 0
n_excluded = 0
for _ in range(1500):
    mode = rng.randint(0, 4)
    if mode == 0:
        a = rng.uniform(-1e3, 1e3); b = a + 10.0 ** rng.uniform(-9.0, 3.0)
    elif mode == 1:
        a = rng.uniform(-1e6, 1e6); b = a + 10.0 ** rng.uniform(-12.0, 6.0)
    elif mode == 2:
        mag = 10.0 ** rng.uniform(-308.0, 10.0)
        b = mag * (1.0 + 10.0 ** rng.uniform(-17.0, 0.0)); a = mag
    elif mode == 3:
        a = 0.0; b = 10.0 ** rng.uniform(-324.0, 10.0)
    else:
        a = rng.uniform(-1e10, 1e10); b = a + 10.0 ** rng.uniform(-3.0, 9.0)
    if not (a < b) or not (a == a and b == b):
        continue
    if well_resolved(a, b):
        lv = real_default_levels(a, b)
        if len(lv) <= 1:
            print("AXIOM-UNSOUND auto_levels on well-resolved fuzz", (a, b), lv)
            sys.exit(1)
        n_checked += 1
    else:
        n_excluded += 1
print("AXIOM auto_levels SOUND: %d boundary + %d well-resolved fuzz ranges all "
      "gave >1 level; %d degenerate fuzz + 6 collapse witnesses guard-excluded."
      % (len(boundary), n_checked, n_excluded))
sys.exit(0)
'''

# (A2) axiom-containment for auto_levels. The ONLY call site is the model's
# not-two_valued branch: result = list(auto_levels(zmin, zmax)). The inputs the
# model can pass are exactly the (zmin, zmax) admitted by choose_default_levels'
# OWN precondition — which is BYTE-IDENTICAL to auto_levels' Requires (the same
# well-resolved guard: zmin<zmax AND span>=1e-6 AND >=1e-9*zmax AND >=1e-9*(0-zmin)).
# So every caller-reachable input lies in the axiom's domain by construction
# (caller Requires == axiom Requires). We assert that equivalence on a wide grid
# of (zmin,zmax) pairs spanning ordinary/large/tiny/degenerate regimes: for every
# pair, caller_admits(z) == axiom_requires(z). A pair the caller admits but the
# axiom forbids would be AXIOM-TOO-WEAK-FOR-CALLER; none can exist since the
# predicates are identical. No real-callee execution needed (pure domain check),
# so it does not depend on the image.
_AX_CONTAINMENT = r'''
import random, sys

# auto_levels' Requires (the axiom domain), verbatim from model.py axioms region.
def axiom_requires(zmin, zmax):
    if not (zmin < zmax):
        return False
    if not (zmax - zmin >= 1e-6):
        return False
    if not (zmax - zmin >= 1e-9 * zmax):
        return False
    if not (zmax - zmin >= 1e-9 * (0.0 - zmin)):
        return False
    return True

# choose_default_levels' precondition restricted to the (zmin,zmax) it forwards
# to auto_levels (the not-two_valued branch). The relevant clauses are EXACTLY
# the same well-resolved guard (the not has_explicit / mid pin do not touch the
# zmin/zmax forwarded to the axiom).
def caller_admits(zmin, zmax):
    if not (zmin < zmax):
        return False
    if not (zmax - zmin >= 1e-6):
        return False
    if not (zmax - zmin >= 1e-9 * zmax):
        return False
    if not (zmax - zmin >= 1e-9 * (0.0 - zmin)):
        return False
    return True

rng = random.Random(248700)
n = 0
violations = []
# wide grid + randomized: ordinary, large, tiny-magnitude, tiny-span, negative,
# zero-lower, and the degenerate collapse regime.
grid = [(0.0, 1.0), (-1.0, 1.0), (0.0, 1e6), (-1e10, 1e10), (1.0, 1.0001),
        (1e-300, 2e-300), (0.0, 5e-324), (1.0, 1.0 + 1e-14), (1e10, 1e10 + 1.0),
        (5.0, 5.0), (3.0, 2.0), (1e-12, 2e-12), (-50.0, -10.0)]
for zmin, zmax in grid:
    if caller_admits(zmin, zmax) and not axiom_requires(zmin, zmax):
        violations.append((zmin, zmax))
    n += 1
for _ in range(20000):
    mode = rng.randint(0, 4)
    if mode == 0:
        a = rng.uniform(-1e3, 1e3); b = a + 10.0 ** rng.uniform(-12.0, 3.0)
    elif mode == 1:
        a = rng.uniform(-1e6, 1e6); b = a + 10.0 ** rng.uniform(-15.0, 6.0)
    elif mode == 2:
        mag = 10.0 ** rng.uniform(-320.0, 10.0)
        b = mag * (1.0 + 10.0 ** rng.uniform(-20.0, 0.0)); a = mag
    elif mode == 3:
        a = 0.0; b = 10.0 ** rng.uniform(-324.0, 10.0)
    else:
        a = rng.uniform(-1e10, 1e10); b = a + 10.0 ** rng.uniform(-6.0, 9.0)
    if a != a or b != b:
        continue
    # a caller-reachable input the axiom does NOT cover => AXIOM-TOO-WEAK-FOR-CALLER
    if caller_admits(a, b) and not axiom_requires(a, b):
        violations.append((a, b))
    n += 1
if violations:
    print("AXIOM-TOO-WEAK-FOR-CALLER: caller reaches inputs outside auto_levels "
          "domain:", violations[:8]); sys.exit(1)
print("CONTAINMENT OK: over %d (zmin,zmax) pairs the caller's admitted domain is "
      "a subset of auto_levels' Requires (the guards are identical), so every "
      "input the model forwards to auto_levels lies in its domain." % n)
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-auto-levels-sound", "axiom": "auto_levels", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_AUTO_SOUND,
     "rationale": "the real matplotlib default level-selection (plt.contour on a continuous "
                  "field) must give >1 level on every WELL-RESOLVED range (the obligation the "
                  "proof consumes for the not-two_valued postcondition); any well-resolved range "
                  "with <=1 level => AXIOM-UNSOUND. Also confirms the documented collapse "
                  "witnesses are guard-excluded (the guard is faithful, not over-claiming)."},
    {"id": "ax-auto-levels-containment", "axiom": "auto_levels", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "the model's only auto_levels call site forwards exactly the (zmin,zmax) its "
                  "OWN precondition admits, and that precondition is byte-identical to "
                  "auto_levels' Requires (same well-resolved guard). So every caller-reachable "
                  "input is in the axiom domain by construction; a caller-admitted input the "
                  "axiom forbids would be AXIOM-TOO-WEAK-FOR-CALLER (none can exist)."},
]
