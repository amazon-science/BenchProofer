#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-18211 (nagini).

Refutes (never proves) the refinement leg of the bundle: does the MODEL in
`model.py` actually agree with the REAL gold-patched repository function it
claims to model?

SHADOW
------
The `# impl-start` / `# impl-end` region of `model.py`'s
`solution_set_of_relation`, copied VERBATIM below with only the contract call
stripped (`Assert(syms == 1)`; no `Requires`/`Ensures`/`Invariant` live inside
the impl region). The two carrier classes `SolutionSet` and `Relation` are
likewise copied verbatim minus their `Requires`/`Ensures` lines. No
restructuring, no renaming, no "simplification": the shadow is the model's own
code, so a disagreement is a disagreement about the model, not about a
paraphrase of it.

The `@ContractOnly` callee `solve_univariate(rel)` has no body to copy, so it
CALLS THE REAL REPO FUNCTION it axiomatizes —
`sympy.solvers.inequalities.solve_univariate_inequality(self, x,
relational=False)` (`sympy/solvers/inequalities.py:397`, invoked from
`_eval_as_set` at `sympy/core/relational.py:395`) — and lifts its real return
value through the type bridge. The axiom is therefore exercised, not assumed:
its raise leg (`Exsures(SolverUndecided, ...)`) is driven by the real
`NotImplementedError` the real solver raises, and its return leg by the real
`Set` the real solver returns. The three `@Pure @ContractOnly` accessors
`solved_cond` / `solved_sym` / `solved_reals` are spec-only (they appear in no
impl region), and their abstract values are realized by the bridge below as
deterministic projections of the solver's own returned set.

ORACLE CHOICE — the real patched function, CALLED, not transliterated
--------------------------------------------------------------------
`Relational._eval_as_set(self)` — `sympy/core/relational.py:389` at
base_commit, gold-patched by `patch.diff` (the gate applies the gold patch to
/testbed and sets PYTHONPATH before this script runs; this script never applies
a patch itself). It is called directly on a real `Relational`: the velvet
sibling's oracle is the same gold-patched `_eval_as_set`, and driving it needs
nothing but a univariate sympy relation, which is buildable in-container. There
is no transliteration of the patched source anywhere in this file — the only
transliterated side is the SHADOW, which is by construction the model's own
Python.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
Concrete -> abstract (the direction inputs are generated in, so every generated
input satisfies the model's `Requires` by construction):

    real univariate `Relational` rel, popped free symbol x
      -> Relation(n_free = len(rel.free_symbols),        # == 1
                  token   = tok(rel),                   # identity of `self`
                  sym     = tok(x),                     # the popped symbol
                  solvability = the REAL solver's verdict on rel:
                                0 if it returns a Set,
                                1 if it raises NotImplementedError)

`tok` is a deterministic injective interning table over `srepr` strings, so
token equality is exactly structural equality of the underlying sympy object.

Abstract <- concrete for results (`alpha`, applied to BOTH sides so the diff is
between the two implementations and not between two encodings):

    real `Set` S returned/produced for (rel, x)
      -> ConditionSet:  SolutionSet(is_fallback=True,  cond=tok(S.condition),
                                    sym=tok(S.sym),    over_reals=(S.base_set == S.Reals))
      -> any other Set: SolutionSet(is_fallback=False, cond=tok(S),
                                    sym=tok(x),        over_reals=(S == S.Reals))

The second row realizes the abstract accessors: `solved_cond(rel) = tok(the
solver's own returned set)`, `solved_sym(rel) = tok(x)`, `solved_reals(rel) =
(the returned set is the whole real line)` — each a deterministic function of
rel, exactly as the axioms require, and `cond = tok(S)` makes the determined
leg's comparison as strong as full structural equality of the returned set.

The model's `Requires` (`n_free == 1` and `solvability in {0, 1}`) is the stated
domain carve-out of mapping.md §3.1: relations on which the real solver instead
reports a `ValueError` / `TypeError` / `RecursionError` or fails to terminate
have NO `solvability` value, hence NO `Relation` carrier. Those are classified
under a per-call wall-clock timeout and counted as DOMAIN-EXCLUDED in the final
report (never silently dropped), because no input can be built for them — not
because they disagree.

INPUTS
------
The model's ABSTRACT input space, modulo the identity tokens, is finite and
tiny: `n_free == 1` is forced by the `Requires` and `solvability in {0, 1}`, so
there are exactly TWO abstract shapes, i.e. the two branches of the impl. Both
are enumerated exhaustively, and each is lowered to MANY distinct concrete
relations (the tokens are what the fallback branch actually moves around, so the
concrete lowerings are where the fidelity risk lives):

  * boundary first — the exact F2P relation `Eq(x*cos(x) - 3*sin(x), 0)` (issue
    18188) and its companion `Eq(x**2 + sqrt(x*2) + sin(x), 0)`, the P2P
    `test_univariate_relational_as_set` relations (`x > 0`, `x >= 0`, `x < 0`,
    `x <= 0`, `Eq(x, 0)`, `Ne(x, 0)`, `x**2 >= 4`), the empty-solution and
    whole-line degenerate cases (`Eq(x**2 + 1, 0)` -> EmptySet,
    `x**2 + 1 > 0` -> Reals, which is the only case that drives
    `over_reals == True` on the determined leg), and further hand-picked
    relations on each side of the solver's determined/undecided split;
  * then seeded fuzz over bounded relation families (polynomials of degree 1-3
    with all six relation constructors; `x*f(x) - k*g(x)` trig relations; the
    F2P `x**2 + sqrt(k*x) + sin(x)` shape; exp/log/Abs relations) to widen the
    concrete pool.

The run FAILS if either impl branch is never taken (the anti-vacuity control: a
green G-CONF that exercised only the pass-through leg would certify nothing
about the branch the gold patch adds).

The real solver and the real `_eval_as_set` are pure deterministic functions of
the relation, so each DISTINCT relation is observed once (real solver call +
real oracle call) and memoized; every one of the >= 1e5 generated inputs is then
individually pushed through the FULL shadow (the verbatim impl region,
including the real-callee dispatch and the fallback `SolutionSet(...)`
construction) and individually diffed against the memoized oracle abstraction.
Pinned fuzz seed: 182110 (recorded in mapping.md §G-CONF).

Exit 0 iff zero disagreements; on a disagreement it prints the input relation
and both outputs and exits 1. stdlib + sympy (the library under test) only.
"""
import json
import random
import signal
import sys

from sympy import (S, Symbol, Eq, Ne, cos, sin, exp, sqrt, Abs, srepr)
from sympy.sets.conditionset import ConditionSet
from sympy.solvers.inequalities import solve_univariate_inequality

SEED = 182110
N_TOTAL = 100_000

# Per-call wall-clock budget. A relation the real solver cannot decide within it
# (e.g. 2*x**(1/3) + 3*x**2 - 3 <= 0, which loops inside solvify) has no
# `solvability` value and therefore NO `Relation` carrier: it is DOMAIN-EXCLUDED
# by the model's stated Requires (mapping.md §3.1), not a disagreement.
PER_CALL_TIMEOUT_S = 10

DETERMINED = 0   # in-domain: the real solver returned a Set
UNDECIDED = 1    # in-domain: the real solver raised NotImplementedError
EXCLUDED = -1    # out-of-domain: any other outcome / non-termination


# --------------------------------------------------------------------------- #
# SHADOW — copied verbatim from model.py, contracts stripped.                 #
# --------------------------------------------------------------------------- #

class SolverUndecided(Exception):
    """model.py: the univariate solver's undecidability signal (user-defined
    stand-in for the real `NotImplementedError`; mapping.md §2)."""
    pass


class SolutionSet:
    """model.py `SolutionSet` — impl region copied verbatim, contracts stripped."""

    def __init__(self, is_fallback, cond, sym, over_reals):
        # impl-start
        self.is_fallback = is_fallback  # type: bool
        self.cond = cond                # type: int
        self.sym = sym                  # type: int
        self.over_reals = over_reals    # type: bool
        # impl-end


class Relation:
    """model.py `Relation` — impl region copied verbatim, contracts stripped."""

    def __init__(self, n_free, token, sym, solvability):
        # impl-start
        self.n_free = n_free            # type: int
        self.token = token              # type: int
        self.sym = sym                  # type: int
        self.solvability = solvability  # type: int
        # impl-end


def solution_set_of_relation(rel):
    """model.py `solution_set_of_relation` — the `# impl-start` / `# impl-end`
    region copied VERBATIM; the only deletion is the contract call
    `Assert(syms == 1)`."""
    # impl-start
    syms = rel.n_free
    x = rel.sym
    try:
        xset = solve_univariate(rel)  # type: SolutionSet
    except SolverUndecided:
        # The solver is undecided: build the symbolic fallback set directly from
        # the relation (its defining condition), the variable, over the reals.
        xset = SolutionSet(True, rel.token, x, True)
    return xset
    # impl-end


# --------------------------------------------------------------------------- #
# Token table + type bridge (mapping.md §2)                                   #
# --------------------------------------------------------------------------- #

_TOKENS = {}
_CONCRETE = {}        # token of a relation -> (real relation, real symbol)


def tok(obj):
    """Deterministic injective interning of a sympy object to an int identity
    token: token equality is exactly `srepr` (structural) equality."""
    key = srepr(obj)
    t = _TOKENS.get(key)
    if t is None:
        t = len(_TOKENS) + 1
        _TOKENS[key] = t
    return t


def alpha(real_set, real_x):
    """Abstraction of a real sympy `Set` to the model's `SolutionSet` carrier
    (mapping.md §2). Applied to BOTH sides of the diff."""
    if isinstance(real_set, ConditionSet):
        return SolutionSet(True, tok(real_set.condition), tok(real_set.sym),
                           bool(real_set.base_set == S.Reals))
    return SolutionSet(False, tok(real_set), tok(real_x),
                       bool(real_set == S.Reals))


def observe(sol):
    """The four modelled fields of a `SolutionSet`, as a comparable tuple."""
    return (bool(sol.is_fallback), sol.cond, sol.sym, bool(sol.over_reals))


# --------------------------------------------------------------------------- #
# The REAL repo callees (the @ContractOnly axiom, and the oracle)             #
# --------------------------------------------------------------------------- #

class _CallTimeout(Exception):
    pass


def _alarm(signum, frame):  # noqa: ARG001
    raise _CallTimeout()


signal.signal(signal.SIGALRM, _alarm)

_SOLVER_OBS = {}      # relation token -> (tag, real Set or None)
_ORACLE_OBS = {}      # relation token -> ("set", real Set) | ("raise", name)
n_real_solver_calls = 0
n_real_oracle_calls = 0


def real_solver(real_rel, real_x):
    """Run the REAL unchanged callee the model axiomatizes as `solve_univariate`
    — `solve_univariate_inequality(self, x, relational=False)`
    (`sympy/solvers/inequalities.py:397`) — under a wall-clock budget, and
    classify its outcome. Memoized per distinct relation (it is a pure
    deterministic function of the relation)."""
    global n_real_solver_calls
    t = tok(real_rel)
    if t in _SOLVER_OBS:
        return _SOLVER_OBS[t]
    n_real_solver_calls += 1
    signal.alarm(PER_CALL_TIMEOUT_S)
    try:
        obs = (DETERMINED, solve_univariate_inequality(real_rel, real_x,
                                                      relational=False))
    except NotImplementedError:
        obs = (UNDECIDED, None)
    except _CallTimeout:
        obs = (EXCLUDED, "timeout/non-termination")
    except Exception as e:  # noqa: BLE001 — any other outcome is carved out
        obs = (EXCLUDED, "%s: %s" % (type(e).__name__, str(e)[:60]))
    finally:
        signal.alarm(0)
    _SOLVER_OBS[t] = obs
    return obs


def solve_univariate(rel):
    """The model's `@ContractOnly` callee, realized by the REAL repo function it
    axiomatizes: `solve_univariate_inequality(self, x, relational=False)`. The
    axiom's return leg is driven by the real returned `Set` (lifted through the
    bridge) and its `Exsures` leg by the real `NotImplementedError`."""
    real_rel, real_x = _CONCRETE[rel.token]
    tag, real_set = real_solver(real_rel, real_x)
    if tag == UNDECIDED:
        raise SolverUndecided()
    if tag == EXCLUDED:      # unreachable: the Requires carves these out
        raise AssertionError("out-of-domain relation reached the shadow: %r"
                             % (real_rel,))
    return alpha(real_set, real_x)


def real_oracle(real_rel):
    """ORACLE: the REAL gold-patched `Relational._eval_as_set(self)`
    (`sympy/core/relational.py:389`, patched by patch.diff before this runs),
    called directly. Memoized per distinct relation."""
    global n_real_oracle_calls
    t = tok(real_rel)
    if t in _ORACLE_OBS:
        return _ORACLE_OBS[t]
    n_real_oracle_calls += 1
    signal.alarm(PER_CALL_TIMEOUT_S)
    try:
        obs = ("set", real_rel._eval_as_set())
    except _CallTimeout:
        obs = ("raise", "timeout/non-termination")
    except Exception as e:  # noqa: BLE001
        obs = ("raise", type(e).__name__)
    finally:
        signal.alarm(0)
    _ORACLE_OBS[t] = obs
    return obs


# --------------------------------------------------------------------------- #
# Input generation                                                            #
# --------------------------------------------------------------------------- #

X = Symbol('x')
XR = Symbol('x', real=True)
CTORS = [lambda a, b: Eq(a, b), lambda a, b: Ne(a, b),
         lambda a, b: a < b, lambda a, b: a > b,
         lambda a, b: a <= b, lambda a, b: a >= b]


def boundary_relations():
    """Boundary cases first: the F2P shape, the P2P relations, the degenerate
    empty / whole-line sets, and hand-picked relations on both sides of the
    solver's determined/undecided split (so both impl branches are driven)."""
    out = []
    for v in (X, XR):
        out += [
            # --- the F2P relation of issue 18188 and its companion (undecided
            #     -> the fallback branch the gold patch adds)
            Eq(v * cos(v) - 3 * sin(v), 0),
            Eq(v ** 2 + sqrt(v * 2) + sin(v), 0),
            Eq(v * cos(v) - sin(v), 0),
            Eq(v - cos(v), 0),
            Eq(v * sin(v) - 2 * cos(v), 0),
            Eq(v ** 3 - v * cos(v), 0),
            Eq(sin(v) + v, 0),
            Eq(exp(v) + v, 0),
            # --- P2P test_univariate_relational_as_set relations (determined)
            v > 0, v >= 0, v < 0, v <= 0, Eq(v, 0), Ne(v, 0), v ** 2 >= 4,
            # --- degenerate determined sets: empty, singleton, whole line
            Eq(v ** 2 + 1, 0), Eq(v ** 2, 0), v ** 2 + 1 > 0, v ** 2 < 0,
            Eq(v - 3, 0), Eq(v ** 2, 4), v ** 2 < 4,
            (v - 1) * (v - 2) > 0, Abs(v) < 2, exp(v) > 2,
            sin(v) > 0, cos(v) <= 0,
        ]
    return out


def fuzz_relation(rng):
    """One draw from the bounded relation families."""
    v = rng.choice([X, XR])
    fam = rng.randrange(5)
    if fam == 0:                                   # polynomials -> determined
        a = rng.randint(1, 6)
        b = rng.randint(-6, 6)
        d = rng.choice([1, 2, 3])
        return rng.choice(CTORS)(a * v ** d + b, 0)
    if fam == 1:                                   # trig -> mostly undecided
        k = rng.randint(1, 5)
        f, g = rng.sample([cos, sin], 2)
        return rng.choice(CTORS)(v * f(v) - k * g(v), 0)
    if fam == 2:                                   # the F2P shape
        k = rng.randint(1, 4)
        return rng.choice(CTORS)(v ** 2 + sqrt(v * k) + sin(v), 0)
    if fam == 3:                                   # exp / log
        k = rng.randint(1, 4)
        return rng.choice(CTORS)(exp(v) + k * v, 0)
    k = rng.randint(1, 4)                          # Abs / mixed
    return rng.choice(CTORS)(Abs(v) - k, 0)


def build_pool(rng, n_fuzz_relations):
    """Concrete relations -> the model's `Relation` carrier, keeping ONLY the
    ones inside the model's Requires (n_free == 1 and solvability in {0, 1}).
    Returns (pool, n_excluded, n_skipped_nonunivariate, branch counts)."""
    pool = []
    seen = set()
    n_excluded = 0
    n_nonuni = 0
    branch = {DETERMINED: 0, UNDECIDED: 0}
    cands = boundary_relations() + [fuzz_relation(rng)
                                    for _ in range(n_fuzz_relations)]
    for real_rel in cands:
        if not isinstance(getattr(real_rel, "free_symbols", None), set):
            n_nonuni += 1
            continue
        if len(real_rel.free_symbols) != 1:        # not univariate: n_free != 1
            n_nonuni += 1
            continue
        key = srepr(real_rel)
        if key in seen:
            continue
        seen.add(key)
        real_x = real_rel.free_symbols.copy().pop()
        tag, _ = real_solver(real_rel, real_x)
        if tag == EXCLUDED:
            # No `solvability` carrier exists (mapping.md §3.1): the model's
            # Requires excludes this relation by construction.
            n_excluded += 1
            continue
        branch[tag] += 1
        t = tok(real_rel)
        _CONCRETE[t] = (real_rel, real_x)
        pool.append(Relation(len(real_rel.free_symbols), t, tok(real_x), tag))
    return pool, n_excluded, n_nonuni, branch


# --------------------------------------------------------------------------- #
# Main differential loop                                                      #
# --------------------------------------------------------------------------- #

def main():
    rng = random.Random(SEED)
    pool, n_excluded, n_nonuni, branch = build_pool(rng, 520)

    if not pool:
        print(json.dumps({"status": "fail", "instance": "sympy__sympy-18211",
                          "reason": "empty input pool"}))
        return 1

    disagreements = []
    checked = 0
    taken = {"determined": 0, "fallback": 0}

    # every generated input is pushed through the FULL shadow and diffed
    order = list(range(len(pool))) + [rng.randrange(len(pool))
                                      for _ in range(N_TOTAL - len(pool))]
    for i in order:
        rel = pool[i]
        real_rel, real_x = _CONCRETE[rel.token]
        checked += 1

        try:
            got = solution_set_of_relation(rel)    # SHADOW (verbatim impl)
        except SolverUndecided:
            # Totality is the modelled behaviour: the shadow must never let the
            # solver's undecidability signal escape. Report, don't crash — this
            # is precisely the pre-patch behaviour, so it must be legible.
            disagreements.append((srepr(real_rel),
                                  "shadow let SolverUndecided escape "
                                  "(totality violated)",
                                  repr(real_oracle(real_rel)[1])[:120]))
            continue
        taken["fallback" if got.is_fallback else "determined"] += 1

        kind, payload = real_oracle(real_rel)      # ORACLE (real patched fn)
        if kind == "raise":
            # The model's postcondition is TOTALITY over this domain: the real
            # patched function must return a set for every in-domain relation.
            disagreements.append((srepr(real_rel), repr(observe(got)),
                                  "oracle raised %s" % (payload,)))
        else:
            want = alpha(payload, real_x)
            if observe(got) != observe(want):
                disagreements.append((srepr(real_rel), repr(observe(got)),
                                      "%r  [%s]" % (observe(want),
                                                    repr(payload)[:120])))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs "
              "(shadow=model.py impl region, oracle=gold-patched "
              "Relational._eval_as_set):" % (len(disagreements), checked))
        for r, got, want in disagreements:
            print("  rel=%s\n    shadow=%s\n    oracle=%s" % (r, got, want))
        print(json.dumps({"status": "fail", "instance": "sympy__sympy-18211",
                          "disagreements": len(disagreements),
                          "inputs": checked, "seed": SEED}))
        return 1

    # anti-vacuity control: a run that never took the branch the gold patch adds
    # (or never took the pass-through branch) certifies nothing.
    if taken["fallback"] == 0 or taken["determined"] == 0:
        print("G-CONF FAIL: impl branch never exercised: %r" % (taken,))
        print(json.dumps({"status": "fail", "instance": "sympy__sympy-18211",
                          "reason": "branch not exercised", "taken": taken}))
        return 1

    print("G-CONF OK: model.py's solution_set_of_relation impl region (verbatim, "
          "@ContractOnly solve_univariate -> the REAL "
          "solve_univariate_inequality(self, x, relational=False)) agrees with "
          "the gold-patched Relational._eval_as_set on %d inputs "
          "(%d distinct in-domain relations: %d determined / %d undecided; "
          "%d domain-excluded, %d non-univariate rejected; seed=%d), "
          "0 disagreements."
          % (checked, len(pool), branch[DETERMINED], branch[UNDECIDED],
             n_excluded, n_nonuni, SEED))
    print(json.dumps({
        "status": "ok",
        "instance": "sympy__sympy-18211",
        "shadow": "model.py impl region of solution_set_of_relation (verbatim)",
        "oracle": "gold-patched Relational._eval_as_set "
                  "(sympy/core/relational.py:389), called",
        "axiom_callee": "solve_univariate_inequality(self, x, relational=False) "
                        "(sympy/solvers/inequalities.py:397), called",
        "inputs": checked,
        "distinct_relations": len(pool),
        "determined_branch_inputs": taken["determined"],
        "fallback_branch_inputs": taken["fallback"],
        "distinct_determined": branch[DETERMINED],
        "distinct_undecided": branch[UNDECIDED],
        "domain_excluded_relations": n_excluded,
        "nonunivariate_rejected": n_nonuni,
        "real_solver_calls": n_real_solver_calls,
        "real_oracle_calls": n_real_oracle_calls,
        "seed": SEED,
        "disagreements": 0,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
