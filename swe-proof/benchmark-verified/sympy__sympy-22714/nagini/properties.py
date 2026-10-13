# properties.py — PBT falsification battery for sympy__sympy-22714.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Every spec case is a
# full model.py variant that shares the FROZEN spec (axioms/pure/pre/post
# regions) byte-for-byte and edits ONLY inside the single # impl-start /
# # impl-end region (incl. its nested # invariants block, which spec_view
# elides as part of the impl span), so same_spec is guaranteed by construction.
#
# Defended surface (read model.py + refinement.md + mapping.md + the F2P
# test_patch + axiom_check.py):
#
#   screen_coordinates(coord_kind, coord_verdict, coord_extra: List[int]) -> bool
#       Models the imaginary-coordinate screen inside Point.__new__ (the gold
#       hunk `if any(a.is_number and im(a) ...)` -> `... im(a).is_zero is False`).
#       Returns True iff the constructor takes the raising branch.
#
#       READ-ONLY inputs: ALL THREE parameters are Acc(list_pred(.), 1/2) in
#       both Requires and Ensures and in the loop Invariant — half permission,
#       so a frame-mutation rival that WRITES any of them must be rejected for
#       INSUFFICIENT PERMISSION (the #1 weakness class; MANDATORY here).
#
#       LOAD-BEARING postcondition clause:
#         Result() == any_triggering(ToSeq(coord_kind), ToSeq(coord_verdict))
#       any_triggering is @Pure but FULLY GROUNDED in the args: it unfolds
#       (front-recursive over the head) into coord_triggers(kind[i], verdict[i])
#       == (kind==1 and verdict==0) over the actual list elements. There is NO
#       opaque answer-key oracle, so there is no WRONG echo to build; an honest
#       echo of the fold IS the correct answer (see the pos-echo control).
#
#       coord_extra is the REDUNDANT third fact (bool(im(a)), the PRE-PATCH
#       discriminator). The spec NEVER mentions it. The headline rival keys the
#       rejection off coord_extra (or off the wrong verdict polarity) instead of
#       coord_verdict==0 — exactly the pre-patch bug (model_prepatch.py) and the
#       F2P delta test_issue_22684 (`with evaluate(False): Point(1, 2)`).
#
#   Proof shape (matters for the positive control): any_triggering is FRONT-
#   recursive (unfolds at the head), and the gold impl iterates BACKWARD (i from
#   len down to 0) maintaining rejected == any_triggering(drop(i), drop(i)) with
#   four framing Asserts that splice the head of drop(i-1) to element i-1 so a
#   single unfold relates step i-1 to step i. A FORWARD loop would need an
#   f(a+b)==f(a)+f(b) lemma the verifier can't auto-discharge (PBT_PLAN §4a/§5a
#   directive 3) — so the positive control keeps the backward loop and every
#   framing Assert/Invariant; it only reorders the trigger conjunction and binds
#   a local boolean (executable-shape change, gold proof preserved).
#
# Weakness classes attacked: frame-mutation (write coord_extra / coord_kind —
# MANDATORY, all inputs read-only), partial-domain (skip the first coordinate /
# the last), value-double-mask (key off the redundant coord_extra = the prepatch
# bug; constant True/False), wrong-polarity (trigger on the POSITIVE verdict).
# Plus a structurally-different positive control, a grounded-echo positive
# control, and an admissibility drain-assert. Ungrounded-oracle-echo is N/A (the
# oracle is grounded in the args) and is replaced by the honest echo control per
# PBT_PLAN §2/§4a. Control-flow-effect is N/A: the modeled value IS the entire
# raise/no-raise decision (Result() is the guard truth value), there is no
# raise/return/side-effect channel invisible to the value abstraction.
from pathlib import Path

INSTANCE = "sympy__sympy-22714"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- anchors (verbatim, unique in model.py impl region) ---------------------
# The trigger block (the only place that decides `rejected`) + the i decrement.
_TRIG = (
    "        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:\n"
    "            rejected = True\n"
    "        i = i - 1\n"
)
# The loop head, for variants that need to insert a write before the trigger.
_LOOP_PROLOGUE = (
    "    rejected = False\n"
    "    i = len(coord_kind)\n"
    "    while i > 0:\n"
)
# The final return, for the admissibility drain-assert.
_RETURN = (
    "        i = i - 1\n"
    "    return rejected\n"
)


# ============================ POSITIVE CONTROLS ==============================

# pos-reorder: structurally-different but CORRECT. Reorders the trigger
# conjunction (test verdict first, then kind) and binds the per-step decision to
# a local boolean before OR-ing into `rejected`. Same value mapping, different
# executable shape. KEEPS the backward loop and EVERY framing Assert/Invariant
# (directive 2/3): no proof obligation dropped. Must verify, else SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _TRIG,
    "        triggers = coord_verdict[i - 1] == 0 and coord_kind[i - 1] == 1\n"
    "        if triggers:\n"
    "            rejected = True\n"
    "        i = i - 1\n",
)

# pos-echo: cheapest HONEST impl — fold the loop's per-step decision through the
# GROUNDED @Pure helper coord_triggers (a pure fn of the two facts, fully
# unfolded) instead of inlining the `==1 and ==0` literals. coord_triggers is
# the grounded oracle, so this is the CORRECT answer, not an ungrounded echo.
# Must verify against Result()==any_triggering(...).
_POS_ECHO = _swap(
    _BASE, _TRIG,
    "        if coord_triggers(coord_kind[i - 1], coord_verdict[i - 1]):\n"
    "            rejected = True\n"
    "        i = i - 1\n",
)


# ============================== ADMISSIBILITY ===============================

# admiss: the precondition (three equal-length half-permission lists) admits a
# full backward traversal that drains the loop to i==0. The in-impl Asserts pin
# that at termination i==0 (the loop did run to completion under the precond)
# and Result() equals the fold over the WHOLE sequence — the postcondition form
# the gold proof ALREADY establishes, so no fresh trigger is introduced (avoids
# a drop(0)==identity proof gap, directive 5a-2/3). If the precondition could
# not carry the invariant to completion on a legitimate F2P-shaped input these
# fail => PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE, _RETURN,
    "        i = i - 1\n"
    "    Assert(i == 0)\n"
    "    Assert(rejected == any_triggering(\n"
    "        ToSeq(coord_kind), ToSeq(coord_verdict)))\n"
    "    return rejected\n",
)


# ============================ UNIQUENESS / REJECT ===========================

# rej-extra: THE pre-patch bug (model_prepatch.py). Keys the rejection off the
# REDUNDANT coord_extra fact (bool(im(a)), the pre-patch generator's second
# conjunct) instead of coord_verdict==0. value-double-mask: the spec never
# mentions coord_extra, so this rival reads a different dimension.
_REJ_EXTRA = _swap(
    _BASE, _TRIG,
    "        if coord_kind[i - 1] == 1 and coord_extra[i - 1] == 1:\n"
    "            rejected = True\n"
    "        i = i - 1\n",
)

# rej-polarity: trigger on the POSITIVE verdict (verdict==1) instead of the
# NEGATIVE outcome (verdict==0). Inverts the load-bearing polarity of the screen.
_REJ_POLARITY = _swap(
    _BASE, _TRIG,
    "        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 1:\n"
    "            rejected = True\n"
    "        i = i - 1\n",
)

# rej-drop-first: partial-domain — stop the loop one step early (while i > 1),
# so the FIRST coordinate (index 0) is never screened. Correct on every tuple
# whose only triggering coordinate is NOT first; diverges when coords[0] is the
# (sole) imaginary one.
_REJ_DROP_FIRST = _swap(
    _BASE,
    "    i = len(coord_kind)\n"
    "    while i > 0:\n",
    "    i = len(coord_kind)\n"
    "    while i > 1:\n",
)

# rej-const-false: value-double-mask — never reject (drop the whole screen).
# Correct on every all-accepting tuple, diverges on any genuinely imaginary
# coordinate. Anchored on the trigger block: delete the trigger entirely.
_REJ_CONST_FALSE = _swap(
    _BASE, _TRIG,
    "        i = i - 1\n",
)

# rej-frame-extra: FRAME-MUTATION (MANDATORY; all inputs Acc(.,1/2)). Keep the
# gold trigger logic verbatim, but additionally WRITE to the read-only
# coord_extra list inside the loop. coord_extra is irrelevant to the
# postcondition, so the VALUE result is unchanged — the rejection is attributable
# PURELY to the write under half permission (INSUFFICIENT PERMISSION), exactly
# the directive-5 probe a byte-fuzzer never constructs.
_REJ_FRAME_EXTRA = _swap(
    _BASE, _TRIG,
    "        coord_extra[i - 1] = 0\n"
    "        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:\n"
    "            rejected = True\n"
    "        i = i - 1\n",
)

# rej-frame-kind: FRAME-MUTATION on a different read-only input (coord_kind,
# which the postcondition DOES read). Overwrite coord_kind[i-1] to a non-looked-
# at kind to vacuously suppress the rejection. Half permission must reject the
# write for INSUFFICIENT PERMISSION before any value reasoning even applies.
_REJ_FRAME_KIND = _swap(
    _BASE, _TRIG,
    "        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:\n"
    "            rejected = True\n"
    "        coord_kind[i - 1] = 0\n"
    "        i = i - 1\n",
)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": "structurally-different CORRECT impl: trigger conjunction "
                     "reordered (verdict-first) and bound to a local boolean. "
                     "KEEPS the backward loop + all four framing Asserts + every "
                     "Invariant (directive 2/3), so the gold proof still "
                     "discharges. Must verify against Result()==any_triggering "
                     "(...). Else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ECHO,
        "rationale": "cheapest HONEST impl: fold the per-step decision through "
                     "the GROUNDED @Pure helper coord_triggers (a pure fn of the "
                     "two facts, fully unfolded) rather than inlining the "
                     "literals. coord_triggers is grounded in the args, so this "
                     "is the correct answer, not an ungrounded echo. Must verify "
                     "(positive control replacing ungrounded-oracle-echo, N/A).",
    },
    {
        "id": "admiss-drain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the precondition (three equal-length half-permission "
                     "lists) admits a full backward traversal: the in-impl "
                     "Asserts pin that the loop drains to i==0 and Result() "
                     "equals the fold over the WHOLE sequence (drop(0)==identity). "
                     "If the precond could not carry the invariant to completion "
                     "for a legitimate F2P-shaped input this fails => "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "rej-extra",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_EXTRA,
        "refinement": "reproduces the PRE-PATCH generator "
                      "(model_prepatch.py): keys the screen off the raw "
                      "truthiness bool(im(a)) (== coord_extra==1) instead of "
                      "im(a).is_zero is False (== coord_verdict==0). Its faithful "
                      "real patch is the UN-fixed line `if any(a.is_number and "
                      "im(a) ...)`: a concrete REAL coordinate under "
                      "evaluate(False) has bool(im(1))==True but is_zero==True, "
                      "so it WRONGLY raises ValueError('Imaginary coordinates "
                      "are not permitted.') — the F2P test_issue_22684 "
                      "(`with evaluate(False): Point(1, 2)`) FAILS. Does NOT "
                      "resolve.",
        "rationale": "rejected by Ensures(Result()==any_triggering(ToSeq("
                     "coord_kind), ToSeq(coord_verdict))): the fold reads "
                     "coord_verdict, NOT coord_extra (which the spec never "
                     "mentions). On the bug-witness row (kind=1, verdict=1, "
                     "extra=1) the spec demands Result()==False but this rival "
                     "returns True. [value-double-mask: reads the redundant "
                     "dimension the postcondition drops.]",
    },
    {
        "id": "rej-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_POLARITY,
        "refinement": "triggers on the POSITIVE verdict (verdict==1, "
                      "im(a).is_zero is True = a certified-real coordinate) "
                      "instead of the NEGATIVE outcome (verdict==0, certified "
                      "non-zero imaginary). Its faithful real patch would write "
                      "`im(a).is_zero is True` — it raises on ordinary REAL "
                      "points (the entire P2P suite: test_point / test_Point2D / "
                      "test_point3D) and PERMITS genuine imaginaries like 2*I. "
                      "Inverts the screen. Does NOT resolve (P2P regress + F2P "
                      "still wrong on the evaluate(False) real coord).",
        "rationale": "rejected by Ensures(Result()==any_triggering(...)): "
                     "coord_triggers pins the negative outcome (verdict==0); a "
                     "verdict==1 coordinate must NOT trigger. On any real point "
                     "(kind=1, verdict=1) the spec demands False, this rival "
                     "returns True. [partial-domain: diverges on every decided "
                     "coordinate.]",
    },
    {
        "id": "rej-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_DROP_FIRST,
        "refinement": "partial-domain: loops `while i > 1`, so the FIRST "
                      "coordinate (index 0) is never screened. Its faithful real "
                      "patch is `any(... for a in coords[1:])` — it ignores the "
                      "first coordinate of every Point, so an imaginary FIRST "
                      "coordinate (e.g. Point(2*I, 0)) is wrongly permitted. Does "
                      "NOT resolve: P2P points whose imaginary coord is first "
                      "stop raising, and the over-permit regresses the imaginary-"
                      "rejection behaviour the constructor must keep.",
        "rationale": "rejected by Ensures(Result()==any_triggering(ToSeq("
                     "coord_kind), ToSeq(coord_verdict))) and the loop Invariant "
                     "rejected==any_triggering(drop(i),drop(i)): stopping at i==1 "
                     "leaves rejected==any_triggering(drop(1),drop(1)), which "
                     "differs from the full-sequence fold whenever coordinate 0 "
                     "triggers. [partial-domain: drops the first element.]",
    },
    {
        "id": "rej-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_CONST_FALSE,
        "refinement": "value-double-mask: deletes the trigger entirely — never "
                      "rejects. Its faithful real patch removes the imaginary "
                      "screen, so `Point(2*I, 0)` and every genuinely imaginary "
                      "coordinate is wrongly accepted (no ValueError). Does NOT "
                      "resolve: the constructor must still raise on real "
                      "imaginaries (mapping.md §4: 2*I keeps coord_verdict==0).",
        "rationale": "rejected by Ensures(Result()==any_triggering(...)): a "
                     "constant False contradicts the fold on any tuple with a "
                     "triggering coordinate (kind=1, verdict=0). [value-double-"
                     "mask: collapses all branches to one value.]",
    },
    {
        "id": "rej-frame-extra",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_FRAME_EXTRA,
        "refinement": "FRAME-MUTATION: keeps the gold trigger VERBATIM but "
                      "additionally WRITES coord_extra[i-1]=0 each step. "
                      "coord_extra is a half-permission read-only input the "
                      "postcondition never mentions, so the value Result() is "
                      "unchanged — yet a faithful real patch that MUTATES the "
                      "caller's coordinate facts in place is not the gold patch "
                      "(the screen is a pure read over `coords`); such a write "
                      "would corrupt shared coordinate state and is not what "
                      "Point.__new__ does. Does NOT resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION (permission system, "
                     "NOT a postcondition clause): coord_extra is Acc(list_pred,"
                     "1/2) in Requires/Invariant/Ensures — half permission "
                     "forbids the element write `coord_extra[i-1]=0`. This is "
                     "the directive-5 probe; the gold invariants are kept "
                     "verbatim so the rejection is attributable to the write.",
    },
    {
        "id": "rej-frame-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_FRAME_KIND,
        "refinement": "FRAME-MUTATION on coord_kind (which the postcondition "
                      "DOES read): after the gold trigger, overwrite "
                      "coord_kind[i-1]=0 to scrub the looked-at kind. A faithful "
                      "real patch that rewrites the coordinate-kind facts in "
                      "place would change `coords` under the constructor — not "
                      "the gold pure-read screen. Does NOT resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: coord_kind is "
                     "Acc(list_pred,1/2) — half permission forbids the element "
                     "write `coord_kind[i-1]=0`. Second read-only-input frame "
                     "probe (directive 5); gold trigger kept verbatim so the "
                     "rejection is attributable to the write, not a value "
                     "disagreement.",
    },
]


# ================================ AXIOM LANE ================================
# meta.json axioms == [] — there is NO @ContractOnly consumed axiom. The changed
# per-coordinate test is modeled DEEPLY (coord_triggers / any_triggering over
# int-encoded facts), an A-REFERENCE validated by axiom_check.py (G-AX). We
# persist that real-callee soundness check as an axiom-lane probe: the deep model
# must equal the REAL post-patch SymPy guard
#   any(a.is_number and im(a).is_zero is False for a in coords)
# on representative + fuzzed coordinates UNDER BOTH evaluate(True)/(False)
# contexts (the bug is context-bound), and the bug witness (a concrete real
# coordinate under evaluate(False)) must be permitted by the fix. The probe
# imports only `sympy` (the repo under test) + stdlib and is self-contained (the
# runner mounts only the probe at /work, in the instance image where SymPy 1.10
# lives). This re-runs axiom_check.py's logic; apply_gold=True (post-patch SymPy).

_AX_PROBE = r'''
import itertools, random, sys

from sympy import (Integer, Rational, Float, I, pi, E, sqrt, Symbol, S,
                   sympify, oo, zoo, nan)
from sympy.functions.elementary.complexes import im
from sympy.core.parameters import evaluate


# --- model.py reference encodings (kept in lock-step with model.py / mapping) -
def enc_is_number(a):
    return 1 if (a.is_number is True) else 0


def enc_imag_is_zero(a):
    z = im(a).is_zero
    if z is True:
        return 1
    if z is False:
        return 0
    return -1            # None / undecided


def enc_imag_truthy(a):
    try:
        return 1 if bool(im(a)) else 0
    except TypeError:
        return 0


def coord_triggers(kind, verdict):
    # model.py @Pure: (kind == 1 and verdict == 0)
    return kind == 1 and verdict == 0


def any_triggering_model(coords):
    return any(coord_triggers(enc_is_number(a), enc_imag_is_zero(a))
               for a in coords)


# --- the REAL post-patch guard, evaluated with real SymPy --------------------
def per_coord_real(a):
    return bool(a.is_number) and (im(a).is_zero is False)


def real_guard(coords):
    return any(a.is_number and im(a).is_zero is False for a in coords)


def _safe_coord(a):
    """Obligation (1): per-coordinate deep model == real. Skip inputs where the
    real decidability facts themselves raise (degenerate nan/zoo arithmetic) —
    the real generator would also raise there, outside the modeled domain. An
    AssertionError (model != real on a well-defined coordinate) is NEVER
    swallowed."""
    try:
        ien = enc_is_number(a)
        izn = enc_imag_is_zero(a)
        real_v = per_coord_real(a)
    except (ValueError, TypeError, AttributeError, RecursionError):
        return
    model_v = coord_triggers(ien, izn)
    assert model_v == real_v, (
        "A-reference UNSOUND on coord %r: model coord_triggers=%r "
        "(is_number=%r, im.is_zero=%r) but real (is_number and is_zero is "
        "False)=%r" % (a, model_v, ien, izn, real_v))


def _safe_tuple(coords):
    """Obligation (2): the fold == real any(...) over the tuple."""
    try:
        model_v = any_triggering_model(coords)
        real_v = real_guard(coords)
    except (ValueError, TypeError, AttributeError, RecursionError):
        return
    assert model_v == real_v, (
        "A-reference UNSOUND on tuple %r: model any_triggering=%r but real "
        "any(...)=%r" % (list(coords), model_v, real_v))


real_atoms = [Integer(0), Integer(1), Integer(2), Integer(-3), Rational(1, 2),
              Rational(-7, 4), Float(0.5), Float(0.0), Float(-2.25), pi, E,
              sqrt(2), S.Zero, S.One, Integer(10) ** 9, sqrt(3) + 1]
imag_atoms = [I, 2 * I, -I, 3 * I, Rational(1, 2) * I, sqrt(2) * I, I * pi,
              Integer(5) * I]
complex_atoms = [1 + I, 2 - 3 * I, pi + E * I, sqrt(2) + I]
x = Symbol('x')
y = Symbol('y', real=True)
z = Symbol('z', imaginary=True)
w = Symbol('w', positive=True)
symbolic_atoms = [x, y, z, w, x + 1, 2 * x, x * y, x + I, x + y]
special_atoms = [oo, -oo, zoo, nan, S.Infinity]
singles = (real_atoms + imag_atoms + complex_atoms + symbolic_atoms
           + special_atoms)

n = 0
# Each coordinate under BOTH evaluation contexts (the bug is context-bound).
for ctx in (True, False):
    with evaluate(ctx):
        for a in singles:
            _safe_coord(a)
            n += 1

# Obligation (3): the bug witness. A concrete REAL coordinate under
# evaluate(False) is PERMITTED by the deep model (post-patch) although the
# pre-patch truthiness fact would have rejected it (the F2P delta).
with evaluate(False):
    a = Integer(1)
    if enc_is_number(a) != 1:
        print("FAIL witness: Integer(1) must be a number"); sys.exit(1)
    if enc_imag_truthy(a) != 1:
        print("FAIL witness: bool(im(Integer(1))) must be truthy under "
              "evaluate(False) (the pre-patch bug); got %r"
              % enc_imag_truthy(a)); sys.exit(1)
    if enc_imag_is_zero(a) != 1:
        print("FAIL witness: im(Integer(1)).is_zero must be True under "
              "evaluate(False); got %r" % enc_imag_is_zero(a)); sys.exit(1)
    if coord_triggers(enc_is_number(a), enc_imag_is_zero(a)) is not False:
        print("FAIL witness: post-patch deep model must PERMIT the real coord")
        sys.exit(1)
# The fix does NOT over-permit: a genuine imaginary still triggers.
if coord_triggers(enc_is_number(2 * I), enc_imag_is_zero(2 * I)) is not True:
    print("FAIL: genuine imaginary 2*I must still be certified imaginary")
    sys.exit(1)

# Tuple-level: every ordered pair from a representative pool + a triple fuzz,
# under both contexts (any() short-circuit + ordering exercised).
pool = [Integer(1), Integer(0), Rational(3, 2), Float(0.5), pi, sqrt(2),
        2 * I, I, 1 + I, x, y, z]
for ctx in (True, False):
    with evaluate(ctx):
        for combo in itertools.product(pool, repeat=2):
            _safe_tuple(combo)
        rng = random.Random(22714)
        for _ in range(3000):
            _safe_tuple(tuple(rng.choice(pool) for _ in range(3)))

# The literal issue repro tuple, constructed and via sympify, under evaluate(False).
with evaluate(False):
    _safe_tuple((Integer(1), Integer(2)))
    _safe_tuple((sympify('Integer(1)'), sympify('Integer(2)')))

# --- CONTAINMENT: every coordinate fact the MODEL can pass to coord_triggers --
# lies in coord_triggers' Requires domain. The model's kind in {0,1}
# (enc_is_number range) and verdict in {-1,0,1} (enc_imag_is_zero range);
# coord_triggers is defined (no precondition) over exactly that int domain and
# returns the looked-at-kind/negative-outcome conjunction. Covering verdict==-1
# (None / undecided), which the abstraction admits, is SOUND (it is accepted,
# never triggers). No caller-reachable (kind, verdict) lies outside this domain.
reachable = set()
for ctx in (True, False):
    with evaluate(ctx):
        for a in singles:
            try:
                reachable.add((enc_is_number(a), enc_imag_is_zero(a)))
            except (ValueError, TypeError, AttributeError, RecursionError):
                pass
domain = set(itertools.product((0, 1), (-1, 0, 1)))
outside = reachable - domain
if outside:
    print("FAIL containment: caller reaches (kind,verdict) outside "
          "coord_triggers domain: %r" % (outside,)); sys.exit(1)

print("AX OK: deep model coord_triggers / any_triggering == real SymPy "
      "(a.is_number and im(a).is_zero is False) on %d coordinate observations "
      "+ all 2-tuples of a 12-atom pool x2 contexts + 3000 triple fuzz; bug "
      "witness (real coord under evaluate(False)) permitted; genuine imaginary "
      "still triggers; %d reachable (kind,verdict) all in coord_triggers domain."
      % (n, len(reachable)))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-deepmodel-soundness",
        "axiom": "coord_triggers/any_triggering",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "the changed per-coordinate test is modeled DEEPLY (no "
                     "consumed axiom; meta.axioms==[]) as an A-reference. The "
                     "probe runs REAL SymPy (post-patch guard `a.is_number and "
                     "im(a).is_zero is False`) on representative + fuzzed "
                     "coordinates under BOTH evaluate(True)/(False) contexts and "
                     "asserts coord_triggers / any_triggering predict it exactly, "
                     "incl. the bug witness. Any disagreement => AXIOM-UNSOUND "
                     "(re-runs axiom_check.py's logic).",
    },
    {
        "id": "ax-deepmodel-containment",
        "axiom": "coord_triggers/any_triggering",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "every (kind, verdict) the model can pass to coord_triggers "
                     "is kind in {0,1} x verdict in {-1,0,1} (the enc_is_number / "
                     "enc_imag_is_zero ranges); coord_triggers is total over "
                     "exactly that int domain. The probe collects the reachable "
                     "set from real SymPy and asserts it lies inside the domain. "
                     "No caller-reachable fact is outside => not "
                     "AXIOM-TOO-WEAK-FOR-CALLER. (Same probe asserts containment.)",
    },
]
