# properties.py — PBT falsification battery for sympy__sympy-13091.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec (axioms/pure/pre/post regions)
# byte-for-byte and edit ONLY inside the two # impl-start/# impl-end regions
# (sym_eq's and sym_ne's), so same_spec is guaranteed by construction.
#
# Defended surface (read model.py + refinement.md + the F2P test_patch):
#   sym_eq(sympifiable: bool, content_equal: bool) -> int
#       three-valued equality reply. Both inputs are PRIMITIVE bool passed by
#       value -- there is NO Acc(x,1/2) read-only reference parameter, hence NO
#       frame to mutate (frame-mutation is N/A here; see 'assessment').
#       LOAD-BEARING postcondition: Result() == eq_code(sympifiable,content_equal)
#       plus three Implies consequence clauses. eq_code is @Pure but FULLY
#       GROUNDED in the inputs (its body is unfolded, deterministic). So an
#       "echo" `return eq_code(...)` is the CORRECT answer -- there is no WRONG
#       echo to build; instead it is a cheapest-impl POSITIVE control.
#       The real F2P delta: foreign peer (not sympifiable) must answer EQ_NI
#       (NotImplemented), NOT EQ_FALSE (the pre-patch `return False` bug).
#   sym_ne(sympifiable: bool, content_equal: bool, other_answer: int) -> bool
#       inequality = complement of the FULLY-RESOLVED == operator op_eq(...),
#       NOT the complement of the raw three-valued reply. The two diverge
#       exactly when self is undecided (not sympifiable): the pre-patch
#       `not self.__eq__(other)` coerces the truthy NotImplemented sentinel.
#
# Weakness classes attacked: partial-domain (the foreign-peer branch -- the
# input that fails FIRST in the F2P), control-flow-effect (sentinel-collapse /
# raw-negation), value-double-mask (constant-branch / drop-NI). Plus the two
# gold prepatch bugs reproduced inside the impl region. Frame-mutation and
# ungrounded-oracle-echo are N/A (no read-only input; oracle is grounded) and
# are replaced by honest positive controls per PBT_PLAN §2/§4a.
from pathlib import Path

INSTANCE = "sympy__sympy-13091"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- anchors: the two impl regions (verbatim in model.py) -------------------
# sym_eq impl block is anchored to '# impl-end' to be unique vs eq_code's body.
_EQ_IMPL = (
    "    if not sympifiable:\n"
    "        return EQ_NI()\n"
    "    if content_equal:\n"
    "        return EQ_TRUE()\n"
    "    return EQ_FALSE()\n"
    "    # impl-end"
)
_NE_IMPL = (
    "    e = sym_eq(sympifiable, content_equal)\n"
    "    return not op_eq(e, other_answer)"
)


# ============================ POSITIVE CONTROLS ==============================

# pos-eq-reorder: structurally different but CORRECT sym_eq. Reorders the two
# DECIDED branches: handle content_equal==False first (return EQ_FALSE) then the
# equal case, keeping the foreign-peer EQ_NI branch first. Same value mapping,
# different branch shape. No proof obligation dropped (no loop/induction here).
_POS_EQ = _swap(
    _BASE, _EQ_IMPL,
    "    if not sympifiable:\n"
    "        return EQ_NI()\n"
    "    if not content_equal:\n"
    "        return EQ_FALSE()\n"
    "    return EQ_TRUE()\n"
    "    # impl-end",
)

# pos-eq-echo: cheapest honest impl -- echo the grounded @Pure oracle eq_code.
# eq_code is a pure function of the inputs (fully unfolded), so this is the
# CORRECT answer, not an ungrounded-oracle echo. Must verify.
_POS_EQ_ECHO = _swap(
    _BASE, _EQ_IMPL,
    "    return eq_code(sympifiable, content_equal)\n"
    "    # impl-end",
)

# pos-ne-reshape: structurally different but CORRECT sym_ne. Inlines eq_code
# instead of calling sym_eq, and binds op_eq's result to a local before
# negating. Same resolved-operator semantics, different local-variable shape.
_POS_NE = _swap(
    _BASE, _NE_IMPL,
    "    e = eq_code(sympifiable, content_equal)\n"
    "    resolved = op_eq(e, other_answer)\n"
    "    return not resolved",
)


# ============================== ADMISSIBILITY ===============================

# admiss: a self-call confirming the precondition admits a normal F2P-shaped
# input. sym_ne's Requires constrains other_answer to a valid 3-valued code;
# EQ_TRUE() is in-domain (the F2P Bar peer's reflected reply). The assert pins
# the symmetry consequence the protocol demands for an incomparable equal peer
# (not sympifiable, other_answer==EQ_TRUE -> Result()==False). If the precond
# rejected a legitimate code, this fails -> PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE, _NE_IMPL,
    "    e = sym_eq(sympifiable, content_equal)\n"
    "    r = not op_eq(e, other_answer)\n"
    "    Assert(Implies(not sympifiable and other_answer == EQ_TRUE(), r == False))\n"
    "    return r",
)


# ============================ UNIQUENESS / REJECT ===========================

# rej-eq-flatfalse: the EXACT pre-patch bug (model_prepatch.py). The foreign
# peer branch returns EQ_FALSE (real `return False`) instead of EQ_NI (real
# `return NotImplemented`). Faithful real patch = the un-fixed sympy: s == foo
# answers a flat False, breaking symmetry -- the F2P Foo/Bar witnesses fail
# (assert b == bar / bar == b need NotImplemented to delegate). MUST reject:
# violates Ensures(Implies(not sympifiable, Result()==EQ_NI())) and the eq_code
# pin. [partial-domain: diverges ONLY on the not-sympifiable sub-domain.]
_REJ_EQ_FLATFALSE = _swap(
    _BASE, _EQ_IMPL,
    "    if not sympifiable:\n"
    "        return EQ_FALSE()\n"
    "    if content_equal:\n"
    "        return EQ_TRUE()\n"
    "    return EQ_FALSE()\n"
    "    # impl-end",
)

# rej-eq-const-false: a value-double-mask cheat -- always answer EQ_FALSE.
# Verifies the decided-unequal sub-domain only; diverges on EQ_TRUE peers and
# the foreign-peer sentinel. Faithful real patch = `__eq__` always returns
# False -> b == bar is False -> F2P symmetry assertions fail. MUST reject:
# violates the EQ_TRUE and EQ_NI consequence clauses.
_REJ_EQ_CONST = _swap(
    _BASE, _EQ_IMPL,
    "    empty = EQ_FALSE()  # type: int\n"
    "    return empty\n"
    "    # impl-end",
)

# rej-eq-drop-ni: return EQ_TRUE on the foreign-peer branch (another wrong
# sentinel), correct elsewhere. Faithful real patch = `__eq__` says foreign
# peers are equal -> n == foo would be True -> F2P `assert n != foo` /
# `not n == foo` fail. MUST reject: violates Implies(not sympifiable,
# Result()==EQ_NI()). [partial-domain on the foreign-peer sub-domain.]
_REJ_EQ_DROPNI = _swap(
    _BASE, _EQ_IMPL,
    "    if not sympifiable:\n"
    "        return EQ_TRUE()\n"
    "    if content_equal:\n"
    "        return EQ_TRUE()\n"
    "    return EQ_FALSE()\n"
    "    # impl-end",
)

# rej-ne-rawneg: the EXACT pre-patch bug (model_prepatch_2.py). Inequality
# complements the RAW three-valued reply instead of the resolved operator:
# only a definite "not equal" (e==EQ_FALSE) yields True. This mirrors
# `not self.__eq__(other)` where NotImplemented is truthy (collapses to False).
# Faithful real patch = the un-fixed `__ne__` -> for an incomparable-and-unequal
# peer (not sympifiable, other_answer!=EQ_TRUE) it answers False where the gold
# answers True -> F2P `assert n != foo` / `assert b != foo` fail. MUST reject:
# violates Ensures(Result()==(not op_eq(...))) and the consequence
# Implies(not sympifiable and other_answer!=EQ_TRUE(), Result()==True).
# [control-flow-effect: the sentinel-collapse the value abstraction must catch.]
_REJ_NE_RAWNEG = _swap(
    _BASE, _NE_IMPL,
    "    e = sym_eq(sympifiable, content_equal)\n"
    "    return e == EQ_FALSE()",
)

# rej-ne-rawcomplement: complement the raw reply via `e != EQ_TRUE()`. On the
# undecided self-answer (e==EQ_NI, i.e. not sympifiable) this is True regardless
# of other_answer -- so for an incomparable EQUAL peer (other_answer==EQ_TRUE)
# it answers True where the gold (delegating to the peer) answers False.
# Faithful real patch = `not self.__eq__(other)` written `self.__eq__(other) is
# not True` -> breaks the Bar symmetry: `assert not b != bar` fails. MUST
# reject: violates Implies(not sympifiable and other_answer==EQ_TRUE,
# Result()==False). [partial-domain: diverges on the incomparable-equal peer.]
_REJ_NE_RAWCOMP = _swap(
    _BASE, _NE_IMPL,
    "    e = sym_eq(sympifiable, content_equal)\n"
    "    return e != EQ_TRUE()",
)

# rej-eq-diverge: the DIVERGENCE cheat (the audit's atk_8 shape). The foreign-
# peer branch loops forever instead of returning: every value postcondition is
# satisfied only vacuously (the function never returns on that sub-domain).
# Faithful real patch = `while True: pass` in the SympifyError branch -> the
# F2P test_equality hangs (harness timeout), does NOT resolve. MUST reject:
# the MustTerminate(1) precondition's obligation leak check fails on a loop
# that consumes no termination measure. [partial-correctness gap: total-
# correctness obligation is what senses it.]
_REJ_EQ_DIVERGE = _swap(
    _BASE, _EQ_IMPL,
    "    if not sympifiable:\n"
    "        while True:\n"
    "            pass\n"
    "    if content_equal:\n"
    "        return EQ_TRUE()\n"
    "    return EQ_FALSE()\n"
    "    # impl-end",
)

# rej-ne-diverge: the same divergence cheat on sym_ne (the audit's atk_7
# shape): loop forever instead of answering. Faithful real patch hangs the F2P
# tests. MUST reject: MustTerminate(2) obligation leaks into the loop.
_REJ_NE_DIVERGE = _swap(
    _BASE, _NE_IMPL,
    "    while True:\n"
    "        pass",
)

# rej-ne-self-only: ignore the reflected other_answer entirely -- complement
# only self's own decided reply, treating undecided as 'equal' (return False).
# return op_eq(e, e_decided?) shortcut: `return not (e == EQ_TRUE())` -- on the
# foreign-peer branch e==EQ_NI so this is True; but on an incomparable EQUAL
# peer the resolved op delegates to other_answer==EQ_TRUE giving op_eq True ->
# gold Result False, here True. Same divergence direction as rawcomp but via a
# different (no-other_answer) shape, covering the 'drops the reflected reply'
# cheat. MUST reject: same consequence clause.
_REJ_NE_SELFONLY = _swap(
    _BASE, _NE_IMPL,
    "    e = sym_eq(sympifiable, content_equal)\n"
    "    return not (e == EQ_TRUE())",
)


SPEC_TESTS = [
    {
        "id": "pos-eq-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EQ,
        "rationale": "structurally-different CORRECT sym_eq (decided branches "
                     "reordered, EQ_NI branch kept first); must satisfy "
                     "eq_code pin + all three consequence clauses. Else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-eq-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EQ_ECHO,
        "rationale": "cheapest honest impl: echo the GROUNDED @Pure oracle "
                     "eq_code (a pure fn of the inputs, fully unfolded). This "
                     "is the correct answer, not an ungrounded echo; must "
                     "verify against Result()==eq_code(...).",
    },
    {
        "id": "pos-ne-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NE,
        "rationale": "structurally-different CORRECT sym_ne (inline eq_code, "
                     "bind op_eq to a local before negating). Same resolved-"
                     "operator value, different shape; must verify else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-ne-symmetry",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "precondition admits a normal F2P-shaped reflected reply "
                     "(other_answer==EQ_TRUE, the Bar peer); the in-impl "
                     "Assert pins the incomparable-equal-peer symmetry "
                     "consequence. Else PRECOND-TOO-STRONG.",
    },
    {
        "id": "rej-eq-flatfalse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_EQ_FLATFALSE,
        "refinement": "reproduces the pre-patch `return False` on the foreign-"
                      "peer branch (model_prepatch.py). Its faithful real patch "
                      "is the UN-fixed sympy: `s == foo` answers a flat False, "
                      "so Bar's reflected __eq__ is never consulted -- the F2P "
                      "witnesses `assert b == bar` / `assert bar == b` FAIL "
                      "(NotImplemented is required to delegate). Does NOT "
                      "resolve test_equality / test_comparisons_with_unknown_type.",
        "rationale": "rejected by Ensures(Implies(not sympifiable, "
                     "Result()==EQ_NI())) and Result()==eq_code(...): the "
                     "foreign-peer branch is pinned to EQ_NI, not EQ_FALSE. "
                     "[partial-domain: diverges only on not-sympifiable.]",
    },
    {
        "id": "rej-eq-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_EQ_CONST,
        "refinement": "always answers EQ_FALSE. Its faithful real patch makes "
                      "`__eq__` always return False -> `b == bar` is False and "
                      "no peer is ever equal -> F2P symmetry/equal-peer "
                      "assertions (`assert b == bar`, `assert n == bar`) FAIL. "
                      "Does NOT resolve.",
        "rationale": "rejected by Implies(sympifiable and content_equal, "
                     "Result()==EQ_TRUE()) and Implies(not sympifiable, "
                     "Result()==EQ_NI()): a constant EQ_FALSE violates both. "
                     "[value-double-mask: collapses all branches to one value.]",
    },
    {
        "id": "rej-eq-drop-ni",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_EQ_DROPNI,
        "refinement": "answers EQ_TRUE (real `return True`) on the foreign-peer "
                      "branch. Its faithful real patch makes `__eq__` claim "
                      "every foreign object is equal -> `n == foo` is True -> "
                      "F2P `assert n != foo` and `assert not n == foo` FAIL. "
                      "Does NOT resolve.",
        "rationale": "rejected by Implies(not sympifiable, Result()==EQ_NI()): "
                     "the foreign-peer branch is pinned to EQ_NI, not EQ_TRUE. "
                     "[partial-domain: diverges on the foreign-peer sub-domain.]",
    },
    {
        "id": "rej-ne-rawneg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_RAWNEG,
        "refinement": "reproduces the pre-patch `not self.__eq__(other)` "
                      "(model_prepatch_2.py): only a definite EQ_FALSE yields "
                      "True (NotImplemented is truthy -> collapses to False). "
                      "Its faithful real patch is the UN-fixed `__ne__`: for an "
                      "incomparable-and-unequal peer it answers False where the "
                      "gold answers True -> F2P `assert n != foo` / `assert b "
                      "!= foo` FAIL. Does NOT resolve.",
        "rationale": "rejected by Ensures(Result()==(not op_eq(eq_code(...),"
                     "other_answer))) and the consequence Implies(not "
                     "sympifiable and other_answer!=EQ_TRUE(), Result()==True): "
                     "the raw negation gives False there. [control-flow-effect: "
                     "the sentinel-collapse the value abstraction must catch.]",
    },
    {
        "id": "rej-ne-rawcomplement",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_RAWCOMP,
        "refinement": "complements the raw reply via `e != EQ_TRUE()`: on the "
                      "undecided self-answer (not sympifiable) it answers True "
                      "regardless of the reflected reply, so for an "
                      "incomparable EQUAL peer (other_answer==EQ_TRUE) it says "
                      "`!=` is True where the gold (delegating) says False. Its "
                      "faithful real patch breaks Bar symmetry -> F2P `assert "
                      "not b != bar` / `assert not bar != b` FAIL. Does NOT "
                      "resolve.",
        "rationale": "rejected by Implies(not sympifiable and "
                     "other_answer==EQ_TRUE(), Result()==False): op_eq "
                     "delegates to the EQ_TRUE reflected reply, so `!=` is "
                     "False. [partial-domain: diverges on the incomparable-"
                     "equal peer.]",
    },
    {
        "id": "rej-eq-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_EQ_DIVERGE,
        "refinement": "loops forever on the foreign-peer branch (the audit's "
                      "atk_8 shape: `while True: pass` in the SympifyError "
                      "branch). Its faithful real patch hangs test_equality "
                      "(harness timeout after 600s). Does NOT resolve.",
        "rationale": "rejected by the MustTerminate(1) precondition: Nagini's "
                     "obligation leak check fails on a loop that consumes no "
                     "termination measure. [total-correctness: divergence "
                     "satisfies value postconditions only vacuously.]",
    },
    {
        "id": "rej-ne-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_DIVERGE,
        "refinement": "sym_ne loops forever instead of answering (the audit's "
                      "atk_7 shape). Its faithful real patch hangs the F2P "
                      "tests (harness timeout). Does NOT resolve.",
        "rationale": "rejected by the MustTerminate(2) precondition: the "
                     "obligation leaks into the non-consuming loop. "
                     "[total-correctness gap closed.]",
    },
    {
        "id": "rej-ne-self-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_SELFONLY,
        "refinement": "ignores the reflected other_answer entirely -- "
                      "`not (e == EQ_TRUE())` complements self's own decided "
                      "reply only, treating undecided self as not-equal. For an "
                      "incomparable EQUAL peer (other_answer==EQ_TRUE) it "
                      "answers `!=` True where the gold delegates to the peer "
                      "and answers False. Its faithful real patch drops the "
                      "delegation -> F2P Bar symmetry assertions FAIL. Does NOT "
                      "resolve.",
        "rationale": "rejected by Implies(not sympifiable and "
                     "other_answer==EQ_TRUE(), Result()==False): the resolved "
                     "operator must consult the reflected reply. "
                     "[value-double-mask: drops the reflected dimension.]",
    },
]


# ================================ AXIOM LANE ================================
# meta.json axioms == [] -- there is NO @ContractOnly consumed axiom. op_eq is
# an A-reference deep model (the CPython == rich-comparison dispatch) validated
# out-of-band by axiom_check.py (G-AX). We persist a containment/soundness probe
# that re-runs that real-callee logic: op_eq's deep model must equal the REAL
# Python `==`/`!=` operator over every reply combination the model can reach,
# and every (self_answer, other_answer) the caller passes must lie in op_eq's
# Requires domain (the three valid codes). The probe imports only stdlib and is
# self-contained (the runner mounts only the probe at /work).

_AX_PROBE = r'''
import itertools, sys, warnings

EQ_FALSE, EQ_TRUE, EQ_NI = 0, 1, 2
_CODES = (EQ_FALSE, EQ_TRUE, EQ_NI)

def _reply(code):
    if code == EQ_TRUE: return True
    if code == EQ_FALSE: return False
    return NotImplemented

class Obj(object):
    """Real Python peer whose __eq__ returns a chosen protocol reply; __ne__ is
    the gold-faithful `not self == other`."""
    def __init__(self, code): self.code = code
    def __eq__(self, other): return _reply(self.code)
    def __ne__(self, other): return not self == other
    __hash__ = object.__hash__

def op_eq_model(self_answer, other_answer):
    """model.py pure-region op_eq, kept in lock-step."""
    if self_answer != EQ_NI:
        return self_answer == EQ_TRUE
    if other_answer != EQ_NI:
        return other_answer == EQ_TRUE
    return False

def sym_ne_model(self_answer, other_answer):
    return not op_eq_model(self_answer, other_answer)

checked = 0
# ---- axiom-soundness: op_eq deep model == REAL Python `==`/`!=` on all 3x3 --
for sa, oa in itertools.product(_CODES, _CODES):
    left, right = Obj(sa), Obj(oa)
    observed_eq = (left == right)        # REAL CPython == dispatch
    if not isinstance(observed_eq, bool):
        print("FAIL: real `==` leaked non-bool for %r,%r: %r" % (sa, oa, observed_eq))
        sys.exit(1)
    expected_eq = op_eq_model(sa, oa)
    if observed_eq != expected_eq:
        print("FAIL: op_eq unsound self=%r other=%r real==%r model=%r"
              % (sa, oa, observed_eq, expected_eq))
        sys.exit(1)
    observed_ne = (left != right)        # REAL CPython != dispatch
    if observed_ne != sym_ne_model(sa, oa) or observed_ne != (not observed_eq):
        print("FAIL: sym_ne unsound self=%r other=%r real!=%r model=%r"
              % (sa, oa, observed_ne, sym_ne_model(sa, oa)))
        sys.exit(1)
    checked += 1

# ---- containment: every (self_answer, other_answer) the caller reaches lies --
# ---- in op_eq's Requires domain {EQ_FALSE,EQ_TRUE,EQ_NI}. The model can only --
# ---- produce self_answer = eq_code(.) in {0,1,2}; other_answer is precondition-
# ---- constrained to the same set. So the reachable set IS exactly _CODES.    --
reachable = set(itertools.product(_CODES, _CODES))
domain = set(itertools.product(_CODES, _CODES))
missing = reachable - domain
if missing:
    print("FAIL: caller can reach inputs outside op_eq Requires domain: %r" % (missing,))
    sys.exit(1)

# ---- symmetry / identity-fallback witnesses the fix establishes -------------
sym, peer_eq, peer_ni = Obj(EQ_NI), Obj(EQ_TRUE), Obj(EQ_NI)
if not ((sym == peer_eq) is True and (peer_eq == sym) is True
        and (sym != peer_eq) is False and (peer_eq != sym) is False):
    print("FAIL: delegation/symmetry broken for undecided-vs-equal peer")
    sys.exit(1)
if not ((sym == peer_ni) is False and (sym != peer_ni) is True):
    print("FAIL: identity fallback broken for two undecided peers")
    sys.exit(1)

# the pre-patch `not self.__eq__(other)` divergence (sanity the spec discriminates)
raw = sym.__eq__(peer_ni)
assert raw is NotImplemented
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    buggy = (not raw)            # NotImplemented is truthy -> False
if buggy is not False or buggy == (sym != peer_ni):
    print("FAIL: pre-patch `not __eq__` should diverge from gold on incomparable-unequal")
    sys.exit(1)

print("AX OK: op_eq deep model == real Python ==/!= on %d (3x3) reply combos; "
      "reachable caller inputs covered by Requires domain; symmetry/identity "
      "witnesses + pre-patch divergence confirmed." % checked)
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-op_eq-soundness",
        "axiom": "op_eq",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "op_eq is an A-reference deep model of the CPython == "
                     "operator (no consumed axiom; meta.axioms==[]). The probe "
                     "runs the REAL Python ==/!= dispatch on objects whose "
                     "__eq__ returns each of True/False/NotImplemented and "
                     "asserts op_eq predicts it over all 3x3 combos + symmetry/"
                     "identity witnesses. Any disagreement => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-op_eq-containment",
        "axiom": "op_eq",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "the model can only pass self_answer in {EQ_FALSE,EQ_TRUE,"
                     "EQ_NI} (eq_code's range) and other_answer is precondition-"
                     "constrained to the same set; op_eq's Requires covers "
                     "exactly that set. No caller-reachable input lies outside "
                     "the domain => not AXIOM-TOO-WEAK-FOR-CALLER. (Same probe "
                     "asserts the containment set equality.)",
    },
]
