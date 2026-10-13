# P2 adversarial audit — sympy__sympy-18211

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_01.py`, `atk_02.py`, `atk_03.py`, `atk_04.py`, `atk_05.py`, `atk_06.py`, `atk_07.py`, `atk_09.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_08.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pc_correct.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_01.py` → rejected (same spec, does not verify — good)

```diff
@@ -250,11 +250,6 @@
     syms = rel.n_free
     Assert(syms == 1)
     x = rel.sym
-    try:
-        xset = solve_univariate(rel)  # type: SolutionSet
-    except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
-        xset = SolutionSet(True, rel.token, x, True)
+    xset = solve_univariate(rel)  # type: SolutionSet
     return xset
     # impl-end
```

Attack 2 — `atk_02.py` → rejected (same spec, does not verify — good)

```diff
@@ -253,8 +253,6 @@
     try:
         xset = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
-        xset = SolutionSet(True, rel.token, x, True)
+        xset = SolutionSet(True, rel.token, x, False)
     return xset
     # impl-end
```

Attack 3 — `atk_03.py` → rejected (same spec, does not verify — good)

```diff
@@ -253,8 +253,6 @@
     try:
         xset = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
-        xset = SolutionSet(True, rel.token, x, True)
+        xset = SolutionSet(True, x, x, True)
     return xset
     # impl-end
```

Attack 4 — `atk_04.py` → rejected (same spec, does not verify — good)

```diff
@@ -251,10 +251,9 @@
     Assert(syms == 1)
     x = rel.sym
     try:
-        xset = solve_univariate(rel)  # type: SolutionSet
+        ignored = solve_univariate(rel)  # type: SolutionSet
+        xset = SolutionSet(False, rel.token, x, True)
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 5 — `atk_05.py` → rejected (same spec, does not verify — good)

```diff
@@ -251,10 +251,9 @@
     Assert(syms == 1)
     x = rel.sym
     try:
-        xset = solve_univariate(rel)  # type: SolutionSet
+        ignored = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
-        xset = SolutionSet(True, rel.token, x, True)
+        pass
+    xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 6 — `atk_06.py` → rejected (same spec, does not verify — good)

```diff
@@ -250,11 +250,13 @@
     syms = rel.n_free
     Assert(syms == 1)
     x = rel.sym
+    n = rel.token
+    while n > 0:
+        Invariant(True)
+        n = n + 1
     try:
         xset = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 7 — `atk_07.py` → rejected (same spec, does not verify — good)

```diff
@@ -250,11 +250,9 @@
     syms = rel.n_free
     Assert(syms == 1)
     x = rel.sym
-    try:
+    if rel.solvability == 0:
         xset = solve_univariate(rel)  # type: SolutionSet
-    except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
+    else:
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 8 — `atk_08.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -251,10 +251,9 @@
     Assert(syms == 1)
     x = rel.sym
     try:
-        xset = solve_univariate(rel)  # type: SolutionSet
+        got = solve_univariate(rel)  # type: SolutionSet
+        xset = SolutionSet(got.is_fallback, got.cond, got.sym, got.over_reals)
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 9 — `atk_09.py` → rejected (same spec, does not verify — good)

```diff
@@ -250,11 +250,10 @@
     syms = rel.n_free
     Assert(syms == 1)
     x = rel.sym
+    xset = SolutionSet(True, rel.token, x, True)
     try:
         xset = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
-        xset = SolutionSet(True, rel.token, x, True)
+        pass
     return xset
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -251,10 +251,9 @@
     Assert(syms == 1)
     x = rel.sym
     try:
+        first = solve_univariate(rel)  # type: SolutionSet
         xset = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -250,11 +250,10 @@
     syms = rel.n_free
     Assert(syms == 1)
     x = rel.sym
-    try:
-        xset = solve_univariate(rel)  # type: SolutionSet
-    except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
+    if rel.solvability == 0:
+        xset = SolutionSet(False, solved_cond(rel), solved_sym(rel),
+                           solved_reals(rel))
+    else:
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -251,10 +251,10 @@
     Assert(syms == 1)
     x = rel.sym
     try:
-        xset = solve_univariate(rel)  # type: SolutionSet
+        ignored = solve_univariate(rel)  # type: SolutionSet
+        xset = SolutionSet(False, solved_cond(rel), solved_sym(rel),
+                           solved_reals(rel))
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -253,8 +253,6 @@
     try:
         xset = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
-        xset = SolutionSet(True, rel.token, x, True)
+        xset = SolutionSet(True, rel.token, rel.token, True)
     return xset
     # impl-end
```

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -253,8 +253,8 @@
     try:
         xset = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
+        xset = SolutionSet(True, rel.token, x, True)
+    except Exception:
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -253,8 +253,8 @@
     try:
         xset = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
         xset = SolutionSet(True, rel.token, x, True)
+        xset.cond = rel.token
+        xset.sym = x
     return xset
     # impl-end
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -247,14 +247,10 @@
                     and Result().over_reals == True))
     # post-conditions-end
     # impl-start
-    syms = rel.n_free
-    Assert(syms == 1)
     x = rel.sym
     try:
         xset = solve_univariate(rel)  # type: SolutionSet
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -252,9 +252,9 @@
     x = rel.sym
     try:
         xset = solve_univariate(rel)  # type: SolutionSet
+        if xset.is_fallback:
+            xset = SolutionSet(True, rel.token, x, True)
     except SolverUndecided:
-        # The solver is undecided: build the symbolic fallback set directly from
-        # the relation (its defining condition), the variable, over the reals.
         xset = SolutionSet(True, rel.token, x, True)
     return xset
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.py`

```python
"""Twin-artifact model for sympy__sympy-18211.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A univariate relation (a relation in exactly one free variable) is turned into
  the set of real values of that variable for which the relation holds. A
  general-purpose univariate solver is consulted for that solution set. The
  solver is partial: for some relations it determines the solution set as a
  concrete set, but for others it cannot determine it at all and signals that it
  is undecided.

  The behaviour pinned here is totality of the conversion. The conversion must
  return a set for EVERY univariate relation in its domain — it may never let the
  solver's "undecided" signal propagate to its caller. Concretely:

  (1) When the solver determines the solution set, the conversion returns EXACTLY
      that solver-produced set.

  (2) When the solver is undecided, the conversion returns the symbolic
      solution set built directly from the relation itself: the set of values of
      the variable that range over the whole real line and additionally satisfy
      the relation as an explicit defining condition. That fallback set carries
      the original relation as its condition, the conversion's variable as its
      bound symbol, and the whole real line as its base domain.

The relation is modelled abstractly by a small object carrying the count of its
free variables, an identity token for the relation, an identity token for its
single free variable, and a tag for whether the solver determines or is
undecided about its solution set. The discriminating observable is purely WHICH
set the conversion produces, not the symbolic contents of the relation, so the
relation's algebraic structure is not modelled. The solution set is modelled by
a small object carrying a tag distinguishing a solver-produced set from the
symbolic fallback, plus the fallback's defining condition / bound symbol /
base-domain fields. The univariate solver is an unchanged callee the conversion
invokes; it is axiomatised, and its undecided signal is a user-defined exception
class (a builtin exception in an `Exsures` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class SolverUndecided(Exception):
    """The univariate solver's signal that it cannot determine the solution set
    of the given relation. User-defined stand-in for the undecidability signal
    the solver raises on some relations (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass

class SolutionSet:
    """A solution set the conversion may return. `is_fallback` distinguishes the
    symbolic fallback set (built from the relation when the solver is undecided)
    from a concrete solver-produced set. For the fallback, `cond` is the relation
    carried as the explicit defining condition, `sym` is the bound variable, and
    `over_reals` records that the base domain is the whole real line."""

    def __init__(self, is_fallback: bool, cond: int, sym: int,
                 over_reals: bool) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_fallback) and Acc(self.cond) and Acc(self.sym)
                and Acc(self.over_reals))
        Ensures(self.is_fallback == is_fallback)
        Ensures(self.cond == cond)
        Ensures(self.sym == sym)
        Ensures(self.over_reals == over_reals)
        # post-conditions-end
        # impl-start
        self.is_fallback = is_fallback  # type: bool
        self.cond = cond                # type: int
        self.sym = sym                  # type: int
        self.over_reals = over_reals    # type: bool
        # impl-end

class Relation:
    """A relation under conversion: the count of its free variables, an identity
    token for the relation itself, an identity token for its single free
    variable, and a tag for whether the solver determines (`solvability == 0`) or
    is undecided about (`solvability == 1`) its solution set."""

    def __init__(self, n_free: int, token: int, sym: int,
                 solvability: int) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.n_free) and Acc(self.token) and Acc(self.sym)
                and Acc(self.solvability))
        Ensures(self.n_free == n_free)
        Ensures(self.token == token)
        Ensures(self.sym == sym)
        Ensures(self.solvability == solvability)
        # post-conditions-end
        # impl-start
        self.n_free = n_free            # type: int
        self.token = token              # type: int
        self.sym = sym                  # type: int
        self.solvability = solvability  # type: int
        # impl-end

# axioms-start
@Pure
@ContractOnly
def solved_cond(rel: Relation) -> int:
    """The defining-condition token of the set the solver produces when it
    determines a solution set (`solvability == 0`). Its value is left ABSTRACT —
    the proof needs only that the determined branch returns EXACTLY this callee's
    set (so the determined result is pinned to the solver's own returned set, not
    a value the conversion fabricates). Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Requires(Acc(rel.solvability, 1 / 4) and rel.solvability == 0)
    Ensures(True)

@Pure
@ContractOnly
def solved_sym(rel: Relation) -> int:
    """The `sym` field of the set the solver produces when it determines a
    solution set (`solvability == 0`). Value left ABSTRACT, like `solved_cond`:
    together the three accessors pin the determined branch to EXACTLY the
    solver's own returned set, field for field, so a verifying implementation
    cannot substitute a set that differs from the solver's in any modelled
    field. mapping.md §3 / axiom_check.py."""
    Requires(Acc(rel.solvability, 1 / 4) and rel.solvability == 0)
    Ensures(True)

@Pure
@ContractOnly
def solved_reals(rel: Relation) -> bool:
    """The `over_reals` field of the set the solver produces when it determines
    a solution set (`solvability == 0`). Value left ABSTRACT, like
    `solved_cond` / `solved_sym`: the determined-branch result is pinned to the
    solver's own returned set in EVERY modelled field. mapping.md §3 /
    axiom_check.py."""
    Requires(Acc(rel.solvability, 1 / 4) and rel.solvability == 0)
    Ensures(True)

@ContractOnly
def solve_univariate(rel: Relation) -> SolutionSet:
    """The general-purpose univariate solver (the unchanged callee the conversion
    invokes). It is partial: it determines the solution set as a concrete set on
    relations tagged `solvability == 0`, and is undecided (raising the
    undecidability signal) on relations tagged `solvability == 1`.

    DOMAIN CARVE-OUT (stated, not implicit). The tag `solvability` is a TOTAL
    function only over the two-way partition this axiom describes: the relations
    on which the solver either (0) returns a concrete set, or (1) signals
    undecidability via the undecidability signal. A relation on which the solver
    instead reports a domain error, a malformed-argument error, exhausts the
    recursion bound, or fails to terminate has NO `solvability` value — it is
    OUTSIDE this abstraction's domain by construction, because no `Relation`
    carrier can be built for it (`solvability ∈ {0,1}` has no preimage there).
    The precondition `solvability == 0 or solvability == 1` is therefore the
    stated mechanism that admits ONLY the return/undecidability-signal relations;
    the conversion's totality is claimed only over them, never over relations with
    any other solver outcome. (Directive 7: the axiom is not stronger than the real
    callee, because the real callee's other failure outcomes have no carrier in the
    abstraction and so are never asserted away.) mapping.md §3.1 / axiom_check.py.

    The weakest facts the proof needs over that domain: it returns normally on
    EXACTLY the determined tag — and the determined return is a concrete
    solver-produced set (NOT the symbolic fallback: `is_fallback` is False),
    pinned field-for-field to the solver's own returned set (condition token
    `solved_cond(rel)`, bound-symbol field `solved_sym(rel)`, base-domain field
    `solved_reals(rel)` — never values the conversion fabricates) — and it
    raises the undecidability signal on EXACTLY the undecided tag. Provenance +
    executable soundness check: mapping.md §3 / axiom_check.py.
    """
    Requires(Acc(rel.solvability, 1 / 2))
    # Stated domain carve-out: ONLY the return/undecidability-signal relations are
    # in the abstraction's domain; no carrier exists for any other solver outcome.
    Requires(rel.solvability == 0 or rel.solvability == 1)
    Requires(MustTerminate(2))
    Ensures(Acc(rel.solvability, 1 / 2))
    Ensures(rel.solvability == 0)
    Ensures(Acc(Result().is_fallback) and Acc(Result().cond)
            and Acc(Result().sym) and Acc(Result().over_reals))
    Ensures(Result().is_fallback == False)
    Ensures(Result().cond == solved_cond(rel))
    Ensures(Result().sym == solved_sym(rel))
    Ensures(Result().over_reals == solved_reals(rel))
    Exsures(SolverUndecided, Acc(rel.solvability, 1 / 2)
            and rel.solvability == 1)
# axioms-end

# pure-start
# (no module-level pure helpers required: the conversion's decision is stated
# inline over the relation's solvability tag and the result's fields.)
# pure-end

def solution_set_of_relation(rel: Relation) -> SolutionSet:
    # pre-conditions-start
    # The relation is univariate (exactly one free variable) and lies in the
    # solver's two-way domain: the solver either determines its solution set
    # (solvability 0) or is undecided about it (solvability 1, the undecidability
    # signal). Relations on which the solver reports any other outcome (a domain
    # error, a malformed-argument error, a recursion-bound exhaustion, or
    # non-termination) have NO solvability value and are OUTSIDE this domain by
    # construction; the totality pinned below is claimed only over the two-way
    # domain, never over those relations (matching the conversion, which catches
    # only the undecidability signal and lets any other solver outcome escape).
    Requires(Acc(rel.n_free, 1 / 2) and Acc(rel.token, 1 / 2)
             and Acc(rel.sym, 1 / 2) and Acc(rel.solvability, 1 / 2))
    Requires(rel.n_free == 1)
    Requires(rel.solvability == 0 or rel.solvability == 1)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rel.n_free, 1 / 2) and Acc(rel.token, 1 / 2)
            and Acc(rel.sym, 1 / 2) and Acc(rel.solvability, 1 / 2))
    Ensures(Acc(Result().is_fallback) and Acc(Result().cond)
            and Acc(Result().sym) and Acc(Result().over_reals))
    # Totality: the conversion returns a set for EVERY relation in its domain —
    # it never lets the solver's undecided signal escape (no Exsures declared, so
    # a normal return is required on both tags).
    #
    # When the solver determines the solution set, the conversion returns EXACTLY
    # that solver-produced set: a concrete set (not the fallback), pinned
    # field-for-field to the solver's own returned set (condition token, bound
    # symbol, base-domain flag — never values the conversion fabricates).
    Ensures(Implies(rel.solvability == 0,
                    Result().is_fallback == False
                    and Result().cond == solved_cond(rel)
                    and Result().sym == solved_sym(rel)
                    and Result().over_reals == solved_reals(rel)))
    # When the solver is undecided, the conversion returns the symbolic fallback
    # set built directly from the relation: it IS the fallback, it carries the
    # original relation as its defining condition, the conversion's variable as
    # its bound symbol, and the whole real line as its base domain.
    Ensures(Implies(rel.solvability == 1,
                    Result().is_fallback == True
                    and Result().cond == rel.token
                    and Result().sym == rel.sym
                    and Result().over_reals == True))
    # post-conditions-end
    # impl-start
    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    try:
        xset = solve_univariate(rel)  # type: SolutionSet
    except SolverUndecided:
        # The solver is undecided: build the symbolic fallback set directly from
        # the relation (its defining condition), the variable, over the reals.
        xset = SolutionSet(True, rel.token, x, True)
    return xset
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, sympy__sympy-18211 (nagini). 17 same-spec attacks encoded in , every one machine-checked to a verdict; no attack or resolve run was left incomplete. Emphasis per mandate on the A legs (solve_univariate + the three solved_* accessors) and model<->patch correspondence; R/I legs left to G-CONF but atk_16 probes A2's R+I leg directly.

**CONTROLS.** Positive control pc_correct.py (byte copy of model.py): `bash scripts/nagini_verify.sh pc_correct.py` -> "Verification successful" (18.4s, exit 0). Gold-patch resolve control patch_gold.diff (gold hunk regenerated mechanically through my own diff -u pipeline) -> run_resolve RESOLVED, F2P test_issue_18188 pass, 54/54 P2P pass, attempts=1. This validates the patch-materialization pipeline itself: an earlier round of hand-written hunk headers failed to apply ("malformed patch"), which is an infra failure and NOT a resolve verdict, so all patches were regenerated with `diff -u` against `git show <base_commit>:sympy/core/relational.py` and the gold control was re-run to prove the pipeline applies cleanly before any attack verdict was recorded.

**PREPATCH BUG REPRODUCED.** atk_01 (atk_01.py) is the pre-patch shape (`xset = solve_univariate(rel); return xset`, no try/except). `python -m swebench_unified.adversary weakness nagini sympy__sympy-18211 atk_01.py` -> exit 2, NOT-A-COUNTEREXAMPLE / does not verify. The spec senses the change exactly as refinement.md claims: the undeclared SolverUndecided escape violates the "method raises no exceptions" obligation (no Exsures on solution_set_of_relation).

SPEC REJECTED 9 of 17 (exit 2, weakness cmd as above, one per attack):
- atk_01 prepatch (no handler; undecided signal escapes).
- atk_02 boundary: fallback over_reals=False (base domain not the real line).
- atk_03 boundary: fallback cond = the symbol instead of the relation.
- atk_04 ungrounded-oracle echo: solver called, result discarded, determined set FABRICATED as SolutionSet(False, rel.token, x, True). Rejected by the field-for-field pin cond==solved_cond / sym==solved_sym / over_reals==solved_reals. This is the hole the three accessors exist to close, and they do close it.
- atk_05 partial-domain: always-fallback on BOTH tags (determined set discarded).
- atk_06 control-flow-effect: correct result but diverges first (`while n > 0: n = n + 1`); rejected by MustTerminate(3) at the method level.
- atk_07 control-flow-effect: branch on rel.solvability directly, never invoking the solver on the undecided tag; rejected (the determined leg cannot establish the solver-pinned fields without the call).
- atk_09 eager-effect: fallback constructed unconditionally then overwritten; rejected.
- atk_13 boundary: fallback sym = the relation token, i.e. ConditionSet's (sym, condition) arguments swapped; rejected.

8 CANDIDATES (weakness exit 0 = shares spec AND verifies). Per protocol EVERY one had its faithful refined patch materialized and EXECUTED through the official harness (`python run_resolve.py <name> patch_<name>.diff` wrapping swebench_unified.harness.run_resolve). ALL EIGHT RESOLVED (F2P test_issue_18188 pass, 54/54 P2P pass, completed=True):
- atk_08 rebuild determined set field-for-field (got.func(*got.args)) -> RESOLVED (attempts=1).
- atk_10 solver consulted twice, second result used -> RESOLVED (attempts=2, flaky=True: first attempt did not complete, second resolved; the solver is a pure deterministic function of the relation so the double call is genuinely behaviour-preserving).
- atk_11 A-LEG ECHO, the sharpest attack: impl branches on rel.solvability == 0 and builds the determined result purely from the spec-only @Pure accessors SolutionSet(False, solved_cond(rel), solved_sym(rel), solved_reals(rel)) WITHOUT the solver's returned object -> RESOLVED. Sound because those accessors DENOTE the fields of the real solver's returned set (mapping.md 3.2), and rel.solvability is not a field of a real Relational: the verdict is observable only by invoking the solver, so any faithful refinement must call it, and reconstructing its set from its own field values reproduces it.
- atk_12 same echo but with the solver invoked and its object discarded -> RESOLVED.
- atk_14 broad handler (`except Exception` also converting ValueError/TypeError/RecursionError into the fallback) -> RESOLVED. Notable: this changes behaviour OUTSIDE the modeled domain (mapping.md 3.1's stated carve-out) where the gold patch lets those escape, yet it resolves because the tests observe no such relation. This is the carve-out's real cost, and it is a spec-scope observation, not a verify-implies-correct violation: within the two-way domain the impl is exactly the gold patch, and no F2P/P2P test distinguishes them.
- atk_15 mutation-effect: fallback rebuilt from its own fields -> RESOLVED.
- atk_16 R-LEG (step A2): the real `assert len(syms) == 1` univariate guard DELETED -> RESOLVED. The Assert is a contract call the spec view keeps as a Requires(n_free == 1) precondition, so dropping it is invisible to the verifier; it is also invisible to the oracle because `_eval_as_set` is only ever reached through Boolean.as_set()/Relational.as_set() with len(free) == 1 already established (boolalg.py:145-147), making the assert defensive-only. Refinement.md A2 tags it R + I, which is accurate.
- atk_17 infeasible-guard / vacuous-branch (the known guarded-self-call pattern): rewrite a determined result into the fabricated fallback when it already looks like one. The axiom's Ensures(Result().is_fallback == False) makes the guard DEAD in the model, so it verifies while proving nothing about that path; its refinement (`if isinstance(xset, ConditionSet)`) is LIVE in the real code -> RESOLVED anyway, because axiom_check.py's G-AX probe independently confirms the real solver never returns the ConditionSet fallback on a determined relation, so the live branch is unreachable in fact. The dead guard is therefore backed by a checked axiom rather than by luck.

REFINEMENT.MD AUDIT (section C of the mandate). Six legs A1-A6, tagged R / R+I / A-consumed / I: no kind-3 (unexpressible-changed-op) leg, and meta.json deep_model_references == [] consistent with refinement.md section B's "no A-reference deep model" claim (correct: the change is an exception-handling addition modeled directly by the try/except in the impl, not a value computation needing a deep model).

The single A-consumed leg A4 (solve_univariate <-> solve_univariate_inequality(self, x, relational=False)) checks out against the repo at base_commit b4f1aa3540fe68d078d76e78ba59d022dd6df39f: callee at sympy/solvers/inequalities.py:397 with the documented `Raises NotImplementedError` docstring (lines 415-420) and raise sites at 531/561/587/593/595/820/911/986 exactly as mapping.md 1 lists them; called from relational.py:395.

A5's ConditionSet correspondence checks out: ConditionSet.`__new__`(cls, sym, condition, base_set=S.UniversalSet) at conditionset.py:117, so the gold patch's (x, self, S.Reals) maps positionally to SolutionSet(is_fallback=True, cond=rel.token, sym=x, over_reals=True) as claimed, and attacks atk_03/atk_13/atk_02 confirm the spec independently rejects perturbing each of those three fields. The solved_cond/solved_sym/solved_reals accessors are correctly tagged A-consumed rather than A-reference (value-abstract projections of the unchanged solver's one returned set, Ensures(True), no deep model to validate); atk_04's rejection is the machine evidence that they actually bind the determined branch.

**VERDICT:** SOUND (advisory). 17 attacks run to a verdict, 9 rejected by the spec including the prepatch bug, 8 verifying candidates all had faithful refined patches EXECUTED through the official harness and all 8 RESOLVED. No verifying wrong impl whose refined patch fails to resolve was found, so verify => correct is not falsified here. The one residual scope observation worth recording for the panel roles is atk_14: the stated domain carve-out (mapping.md 3.1) means a broad-handler impl that changes behaviour on out-of-domain relations both verifies and resolves. That is a bounded-scope property of the spec, disclosed in the artifacts and mirrored by the tests' own coverage, not a refinement-fidelity defect.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_01.py`, `atk_02.py`, `atk_03.py`, `atk_04.py`, `atk_05.py`, `atk_06.py`, `atk_07.py`, `atk_09.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_08.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pc_correct.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_01.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_02.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_03.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_04.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_05.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_06.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_07.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_08.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_09.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.py`

```python
"""Twin-artifact model for sympy__sympy-18211.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A univariate relation (a relation in exactly one free variable) is turned into
  the set of real values of that variable for which the relation holds. A
  general-purpose univariate solver is consulted for that solution set. The
  solver is partial: for some relations it determines the solution set as a
  concrete set, but for others it cannot determine it at all and signals that it
  is undecided.

  The behaviour pinned here is totality of the conversion. The conversion must
  return a set for EVERY univariate relation in its domain — it may never let the
  solver's "undecided" signal propagate to its caller. Concretely:

  (1) When the solver determines the solution set, the conversion returns EXACTLY
      that solver-produced set.

  (2) When the solver is undecided, the conversion returns the symbolic
      solution set built directly from the relation itself: the set of values of
      the variable that range over the whole real line and additionally satisfy
      the relation as an explicit defining condition. That fallback set carries
      the original relation as its condition, the conversion's variable as its
      bound symbol, and the whole real line as its base domain.

The relation is modelled abstractly by a small object carrying the count of its
free variables, an identity token for the relation, an identity token for its
single free variable, and a tag for whether the solver determines or is
undecided about its solution set. The discriminating observable is purely WHICH
set the conversion produces, not the symbolic contents of the relation, so the
relation's algebraic structure is not modelled. The solution set is modelled by
a small object carrying a tag distinguishing a solver-produced set from the
symbolic fallback, plus the fallback's defining condition / bound symbol /
base-domain fields. The univariate solver is an unchanged callee the conversion
invokes; it is axiomatised, and its undecided signal is a user-defined exception
class (a builtin exception in an `Exsures` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class SolverUndecided(Exception):
    """The univariate solver's signal that it cannot determine the solution set
    of the given relation. User-defined stand-in for the undecidability signal
    the solver raises on some relations (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass

class SolutionSet:
    """A solution set the conversion may return. `is_fallback` distinguishes the
    symbolic fallback set (built from the relation when the solver is undecided)
    from a concrete solver-produced set. For the fallback, `cond` is the relation
    carried as the explicit defining condition, `sym` is the bound variable, and
    `over_reals` records that the base domain is the whole real line."""

    def __init__(self, is_fallback: bool, cond: int, sym: int,
                 over_reals: bool) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_fallback) and Acc(self.cond) and Acc(self.sym)
                and Acc(self.over_reals))
        Ensures(self.is_fallback == is_fallback)
        Ensures(self.cond == cond)
        Ensures(self.sym == sym)
        Ensures(self.over_reals == over_reals)
        # post-conditions-end
        # impl-start
        self.is_fallback = is_fallback  # type: bool
        self.cond = cond                # type: int
        self.sym = sym                  # type: int
        self.over_reals = over_reals    # type: bool
        # impl-end

class Relation:
    """A relation under conversion: the count of its free variables, an identity
    token for the relation itself, an identity token for its single free
    variable, and a tag for whether the solver determines (`solvability == 0`) or
    is undecided about (`solvability == 1`) its solution set."""

    def __init__(self, n_free: int, token: int, sym: int,
                 solvability: int) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.n_free) and Acc(self.token) and Acc(self.sym)
                and Acc(self.solvability))
        Ensures(self.n_free == n_free)
        Ensures(self.token == token)
        Ensures(self.sym == sym)
        Ensures(self.solvability == solvability)
        # post-conditions-end
        # impl-start
        self.n_free = n_free            # type: int
        self.token = token              # type: int
        self.sym = sym                  # type: int
        self.solvability = solvability  # type: int
        # impl-end

# axioms-start
@Pure
@ContractOnly
def solved_cond(rel: Relation) -> int:
    """The defining-condition token of the set the solver produces when it
    determines a solution set (`solvability == 0`). Its value is left ABSTRACT —
    the proof needs only that the determined branch returns EXACTLY this callee's
    set (so the determined result is pinned to the solver's own returned set, not
    a value the conversion fabricates). Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Requires(Acc(rel.solvability, 1 / 4) and rel.solvability == 0)
    Ensures(True)

@Pure
@ContractOnly
def solved_sym(rel: Relation) -> int:
    """The `sym` field of the set the solver produces when it determines a
    solution set (`solvability == 0`). Value left ABSTRACT, like `solved_cond`:
    together the three accessors pin the determined branch to EXACTLY the
    solver's own returned set, field for field, so a verifying implementation
    cannot substitute a set that differs from the solver's in any modelled
    field. mapping.md §3 / axiom_check.py."""
    Requires(Acc(rel.solvability, 1 / 4) and rel.solvability == 0)
    Ensures(True)

@Pure
@ContractOnly
def solved_reals(rel: Relation) -> bool:
    """The `over_reals` field of the set the solver produces when it determines
    a solution set (`solvability == 0`). Value left ABSTRACT, like
    `solved_cond` / `solved_sym`: the determined-branch result is pinned to the
    solver's own returned set in EVERY modelled field. mapping.md §3 /
    axiom_check.py."""
    Requires(Acc(rel.solvability, 1 / 4) and rel.solvability == 0)
    Ensures(True)

@ContractOnly
def solve_univariate(rel: Relation) -> SolutionSet:
    """The general-purpose univariate solver (the unchanged callee the conversion
    invokes). It is partial: it determines the solution set as a concrete set on
    relations tagged `solvability == 0`, and is undecided (raising the
    undecidability signal) on relations tagged `solvability == 1`.

    DOMAIN CARVE-OUT (stated, not implicit). The tag `solvability` is a TOTAL
    function only over the two-way partition this axiom describes: the relations
    on which the solver either (0) returns a concrete set, or (1) signals
    undecidability via the undecidability signal. A relation on which the solver
    instead reports a domain error, a malformed-argument error, exhausts the
    recursion bound, or fails to terminate has NO `solvability` value — it is
    OUTSIDE this abstraction's domain by construction, because no `Relation`
    carrier can be built for it (`solvability ∈ {0,1}` has no preimage there).
    The precondition `solvability == 0 or solvability == 1` is therefore the
    stated mechanism that admits ONLY the return/undecidability-signal relations;
    the conversion's totality is claimed only over them, never over relations with
    any other solver outcome. (Directive 7: the axiom is not stronger than the real
    callee, because the real callee's other failure outcomes have no carrier in the
    abstraction and so are never asserted away.) mapping.md §3.1 / axiom_check.py.

    The weakest facts the proof needs over that domain: it returns normally on
    EXACTLY the determined tag — and the determined return is a concrete
    solver-produced set (NOT the symbolic fallback: `is_fallback` is False),
    pinned field-for-field to the solver's own returned set (condition token
    `solved_cond(rel)`, bound-symbol field `solved_sym(rel)`, base-domain field
    `solved_reals(rel)` — never values the conversion fabricates) — and it
    raises the undecidability signal on EXACTLY the undecided tag. Provenance +
    executable soundness check: mapping.md §3 / axiom_check.py.
    """
    Requires(Acc(rel.solvability, 1 / 2))
    # Stated domain carve-out: ONLY the return/undecidability-signal relations are
    # in the abstraction's domain; no carrier exists for any other solver outcome.
    Requires(rel.solvability == 0 or rel.solvability == 1)
    Requires(MustTerminate(2))
    Ensures(Acc(rel.solvability, 1 / 2))
    Ensures(rel.solvability == 0)
    Ensures(Acc(Result().is_fallback) and Acc(Result().cond)
            and Acc(Result().sym) and Acc(Result().over_reals))
    Ensures(Result().is_fallback == False)
    Ensures(Result().cond == solved_cond(rel))
    Ensures(Result().sym == solved_sym(rel))
    Ensures(Result().over_reals == solved_reals(rel))
    Exsures(SolverUndecided, Acc(rel.solvability, 1 / 2)
            and rel.solvability == 1)
# axioms-end

# pure-start
# (no module-level pure helpers required: the conversion's decision is stated
# inline over the relation's solvability tag and the result's fields.)
# pure-end

def solution_set_of_relation(rel: Relation) -> SolutionSet:
    # pre-conditions-start
    # The relation is univariate (exactly one free variable) and lies in the
    # solver's two-way domain: the solver either determines its solution set
    # (solvability 0) or is undecided about it (solvability 1, the undecidability
    # signal). Relations on which the solver reports any other outcome (a domain
    # error, a malformed-argument error, a recursion-bound exhaustion, or
    # non-termination) have NO solvability value and are OUTSIDE this domain by
    # construction; the totality pinned below is claimed only over the two-way
    # domain, never over those relations (matching the conversion, which catches
    # only the undecidability signal and lets any other solver outcome escape).
    Requires(Acc(rel.n_free, 1 / 2) and Acc(rel.token, 1 / 2)
             and Acc(rel.sym, 1 / 2) and Acc(rel.solvability, 1 / 2))
    Requires(rel.n_free == 1)
    Requires(rel.solvability == 0 or rel.solvability == 1)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rel.n_free, 1 / 2) and Acc(rel.token, 1 / 2)
            and Acc(rel.sym, 1 / 2) and Acc(rel.solvability, 1 / 2))
    Ensures(Acc(Result().is_fallback) and Acc(Result().cond)
            and Acc(Result().sym) and Acc(Result().over_reals))
    # Totality: the conversion returns a set for EVERY relation in its domain —
    # it never lets the solver's undecided signal escape (no Exsures declared, so
    # a normal return is required on both tags).
    #
    # When the solver determines the solution set, the conversion returns EXACTLY
    # that solver-produced set: a concrete set (not the fallback), pinned
    # field-for-field to the solver's own returned set (condition token, bound
    # symbol, base-domain flag — never values the conversion fabricates).
    Ensures(Implies(rel.solvability == 0,
                    Result().is_fallback == False
                    and Result().cond == solved_cond(rel)
                    and Result().sym == solved_sym(rel)
                    and Result().over_reals == solved_reals(rel)))
    # When the solver is undecided, the conversion returns the symbolic fallback
    # set built directly from the relation: it IS the fallback, it carries the
    # original relation as its defining condition, the conversion's variable as
    # its bound symbol, and the whole real line as its base domain.
    Ensures(Implies(rel.solvability == 1,
                    Result().is_fallback == True
                    and Result().cond == rel.token
                    and Result().sym == rel.sym
                    and Result().over_reals == True))
    # post-conditions-end
    # impl-start
    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    try:
        xset = solve_univariate(rel)  # type: SolutionSet
    except SolverUndecided:
        # The solver is undecided: build the symbolic fallback set directly from
        # the relation (its defining condition), the variable, over the reals.
        xset = SolutionSet(True, rel.token, x, True)
    return xset
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, sympy__sympy-18211 (nagini). 17 same-spec attacks encoded in , every one machine-checked to a verdict; no attack or resolve run was left incomplete. Emphasis per mandate on the A legs (solve_univariate + the three solved_* accessors) and model<->patch correspondence; R/I legs left to G-CONF but atk_16 probes A2's R+I leg directly.

**CONTROLS.** Positive control pc_correct.py (byte copy of model.py): `bash scripts/nagini_verify.sh pc_correct.py` -> "Verification successful" (18.4s, exit 0). Gold-patch resolve control patch_gold.diff (gold hunk regenerated mechanically through my own diff -u pipeline) -> run_resolve RESOLVED, F2P test_issue_18188 pass, 54/54 P2P pass, attempts=1. This validates the patch-materialization pipeline itself: an earlier round of hand-written hunk headers failed to apply ("malformed patch"), which is an infra failure and NOT a resolve verdict, so all patches were regenerated with `diff -u` against `git show <base_commit>:sympy/core/relational.py` and the gold control was re-run to prove the pipeline applies cleanly before any attack verdict was recorded.

**PREPATCH BUG REPRODUCED.** atk_01 (atk_01.py) is the pre-patch shape (`xset = solve_univariate(rel); return xset`, no try/except). `python -m swebench_unified.adversary weakness nagini sympy__sympy-18211 atk_01.py` -> exit 2, NOT-A-COUNTEREXAMPLE / does not verify. The spec senses the change exactly as refinement.md claims: the undeclared SolverUndecided escape violates the "method raises no exceptions" obligation (no Exsures on solution_set_of_relation).

SPEC REJECTED 9 of 17 (exit 2, weakness cmd as above, one per attack):
- atk_01 prepatch (no handler; undecided signal escapes).
- atk_02 boundary: fallback over_reals=False (base domain not the real line).
- atk_03 boundary: fallback cond = the symbol instead of the relation.
- atk_04 ungrounded-oracle echo: solver called, result discarded, determined set FABRICATED as SolutionSet(False, rel.token, x, True). Rejected by the field-for-field pin cond==solved_cond / sym==solved_sym / over_reals==solved_reals. This is the hole the three accessors exist to close, and they do close it.
- atk_05 partial-domain: always-fallback on BOTH tags (determined set discarded).
- atk_06 control-flow-effect: correct result but diverges first (`while n > 0: n = n + 1`); rejected by MustTerminate(3) at the method level.
- atk_07 control-flow-effect: branch on rel.solvability directly, never invoking the solver on the undecided tag; rejected (the determined leg cannot establish the solver-pinned fields without the call).
- atk_09 eager-effect: fallback constructed unconditionally then overwritten; rejected.
- atk_13 boundary: fallback sym = the relation token, i.e. ConditionSet's (sym, condition) arguments swapped; rejected.

8 CANDIDATES (weakness exit 0 = shares spec AND verifies). Per protocol EVERY one had its faithful refined patch materialized and EXECUTED through the official harness (`python run_resolve.py <name> patch_<name>.diff` wrapping swebench_unified.harness.run_resolve). ALL EIGHT RESOLVED (F2P test_issue_18188 pass, 54/54 P2P pass, completed=True):
- atk_08 rebuild determined set field-for-field (got.func(*got.args)) -> RESOLVED (attempts=1).
- atk_10 solver consulted twice, second result used -> RESOLVED (attempts=2, flaky=True: first attempt did not complete, second resolved; the solver is a pure deterministic function of the relation so the double call is genuinely behaviour-preserving).
- atk_11 A-LEG ECHO, the sharpest attack: impl branches on rel.solvability == 0 and builds the determined result purely from the spec-only @Pure accessors SolutionSet(False, solved_cond(rel), solved_sym(rel), solved_reals(rel)) WITHOUT the solver's returned object -> RESOLVED. Sound because those accessors DENOTE the fields of the real solver's returned set (mapping.md 3.2), and rel.solvability is not a field of a real Relational: the verdict is observable only by invoking the solver, so any faithful refinement must call it, and reconstructing its set from its own field values reproduces it.
- atk_12 same echo but with the solver invoked and its object discarded -> RESOLVED.
- atk_14 broad handler (`except Exception` also converting ValueError/TypeError/RecursionError into the fallback) -> RESOLVED. Notable: this changes behaviour OUTSIDE the modeled domain (mapping.md 3.1's stated carve-out) where the gold patch lets those escape, yet it resolves because the tests observe no such relation. This is the carve-out's real cost, and it is a spec-scope observation, not a verify-implies-correct violation: within the two-way domain the impl is exactly the gold patch, and no F2P/P2P test distinguishes them.
- atk_15 mutation-effect: fallback rebuilt from its own fields -> RESOLVED.
- atk_16 R-LEG (step A2): the real `assert len(syms) == 1` univariate guard DELETED -> RESOLVED. The Assert is a contract call the spec view keeps as a Requires(n_free == 1) precondition, so dropping it is invisible to the verifier; it is also invisible to the oracle because `_eval_as_set` is only ever reached through Boolean.as_set()/Relational.as_set() with len(free) == 1 already established (boolalg.py:145-147), making the assert defensive-only. Refinement.md A2 tags it R + I, which is accurate.
- atk_17 infeasible-guard / vacuous-branch (the known guarded-self-call pattern): rewrite a determined result into the fabricated fallback when it already looks like one. The axiom's Ensures(Result().is_fallback == False) makes the guard DEAD in the model, so it verifies while proving nothing about that path; its refinement (`if isinstance(xset, ConditionSet)`) is LIVE in the real code -> RESOLVED anyway, because axiom_check.py's G-AX probe independently confirms the real solver never returns the ConditionSet fallback on a determined relation, so the live branch is unreachable in fact. The dead guard is therefore backed by a checked axiom rather than by luck.

REFINEMENT.MD AUDIT (section C of the mandate). Six legs A1-A6, tagged R / R+I / A-consumed / I: no kind-3 (unexpressible-changed-op) leg, and meta.json deep_model_references == [] consistent with refinement.md section B's "no A-reference deep model" claim (correct: the change is an exception-handling addition modeled directly by the try/except in the impl, not a value computation needing a deep model).

The single A-consumed leg A4 (solve_univariate <-> solve_univariate_inequality(self, x, relational=False)) checks out against the repo at base_commit b4f1aa3540fe68d078d76e78ba59d022dd6df39f: callee at sympy/solvers/inequalities.py:397 with the documented `Raises NotImplementedError` docstring (lines 415-420) and raise sites at 531/561/587/593/595/820/911/986 exactly as mapping.md 1 lists them; called from relational.py:395.

A5's ConditionSet correspondence checks out: ConditionSet.`__new__`(cls, sym, condition, base_set=S.UniversalSet) at conditionset.py:117, so the gold patch's (x, self, S.Reals) maps positionally to SolutionSet(is_fallback=True, cond=rel.token, sym=x, over_reals=True) as claimed, and attacks atk_03/atk_13/atk_02 confirm the spec independently rejects perturbing each of those three fields. The solved_cond/solved_sym/solved_reals accessors are correctly tagged A-consumed rather than A-reference (value-abstract projections of the unchanged solver's one returned set, Ensures(True), no deep model to validate); atk_04's rejection is the machine evidence that they actually bind the determined branch.

**VERDICT:** SOUND (advisory). 17 attacks run to a verdict, 9 rejected by the spec including the prepatch bug, 8 verifying candidates all had faithful refined patches EXECUTED through the official harness and all 8 RESOLVED. No verifying wrong impl whose refined patch fails to resolve was found, so verify => correct is not falsified here. The one residual scope observation worth recording for the panel roles is atk_14: the stated domain carve-out (mapping.md 3.1) means a broad-handler impl that changes behaviour on out-of-domain relations both verifies and resolves. That is a bounded-scope property of the spec, disclosed in the artifacts and mirrored by the tests' own coverage, not a refinement-fidelity defect.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL attacker 2 (faithfulness-break) for sympy__sympy-18211 (Nagini). Reference =  worktree at base_commit b4f1aa3540 with patch.diff APPLIED (confirmed: `git diff --stat` shows sympy/core/relational.py +8/-1 and the try/except NotImplementedError -> ConditionSet(x, self, S.Reals) body is live at relational.py:389-403).

**MODELED FUNCTION:** solution_set_of_relation(rel) <-> Relational.`_eval_as_set`(self). Spec asserts two legs over the stated domain (n_free==1, solvability in {0,1}):
  (L0) solvability==0 -> is_fallback==False AND cond==solved_cond(rel) AND sym==solved_sym(rel) AND over_reals==solved_reals(rel) (i.e. EXACTLY the solver's own returned Set, field-for-field);
  (L1) solvability==1 -> is_fallback==True AND cond==rel.token AND sym==rel.sym AND over_reals==True (i.e. ConditionSet(x, self, S.Reals));
  plus TOTALITY (no Exsures => normal return required on both legs).

TOO-STRONG / DRIFT HUNT -- 6 independent attack angles, all NEGATIVE:

(1) Undecided-leg totality break. Hunted an in-domain solvability==1 relation on which the real patched `_eval_as_set` does NOT return normally, or returns a set the fallback postcondition does not describe. Attacked every ConditionSet.`__new__` collapse/raise path (conditionset.py:117-186): condition is S.true -> returns base_set (Reals, NOT a ConditionSet); S.false -> EmptySet; FiniteSet base -> Union; base_set is a ConditionSet -> arg merge/Dummy('lambda') rename; `not isinstance(sym, Symbol)` -> ValueError('non-symbol dummy not recognized in condition'). Built 33 tautological/contradictory relations via evaluate=False (Eq(x,x), Ge(`x**2`,0), Ge(tan(x),tan(x)), Lt(zeta(x),zeta(x)), Eq(sin(x)**2+cos(x)**2,1), ...) to force the S.true/S.false collapse ON the undecided leg. Result: every relation that collapses is DETERMINED (the solver returns Reals/EmptySet before any fallback is reached), so no collapse ever lands on L1. Zero divergences.

(2) Non-Symbol popped free symbol -> ConditionSet ValueError. The `sym` collapse path needs free_symbols=={self} with self not a Symbol. Enumerated every such class in the repo (grep 'def free_symbols' -A3 | 'return {self}'): Idx (tensor/indexed.py:751), RandomSymbol (stats/rv.py:273), BaseScalar (vector/scalar.py:49), Vector/BaseVector (vector/vector.py:376), QExpr/Operator/Ket (physics/quantum/qexpr.py:100), plus MatrixSymbol, Indexed, IndexedBase, AppliedUndef, Trace, Determinant. x 7 undecided shapes. Every non-Symbol carrier that reaches L1 (Idx, RandomSymbol, BaseScalar, BaseVector) still yields a well-formed ConditionSet with .sym==x, .condition==self, .base_set==Reals -- because xreplace({sym: Dummy('lambda')}) DOES leave the dummy free in the condition, so the ValueError branch is not reached. QOperator/QKet/MatrixSymbol carriers have is_extended_real False and short-circuit to EmptySet at inequalities.py:467 (DETERMINED leg, matched). Trace/Determinant DO make ConditionSet raise TypeError, but they are DETERMINED, so the fallback is never constructed -- L0 holds (EmptySet == solver's own set). Zero divergences.

(3) Determined-leg is_fallback==False pin. Asked whether solve_univariate_inequality(..., relational=False) ever ITSELF returns a ConditionSet (which would falsify Ensures(Result().is_fallback == False) and the L0 non-fallback pin). Over 742 + 740 + 160 determined observations across three sweeps: 0 ConditionSet returns, 0 non-Set returns. solvify (solveset.py:2137) converts a ConditionSet solveset into NotImplementedError rather than returning it, so the solver's return leg structurally cannot produce a ConditionSet.

(4) solved_cond/solved_sym/solved_reals purity (is solvability/the returned Set a FUNCTION of rel?). The solver allocates a fresh Dummy('gen', extended_real=True) at inequalities.py:470 when gen.is_extended_real is None, and the im(expanded_e)!=0 branch returns make_real.intersect(`_domain`) WITHOUT the .subs(gen,`_gen`) back-substitution -- a real Dummy-leak candidate that would make the @Pure accessors ill-defined. Fuzzed 1287 distinct relations incl. 18 hand-built imaginary-coefficient families (`I*x`>0, (1+I)*x**2>0, Eq((1+I)*x+(1-I),0), `I*sqrt`(x)>0, ...): 0 leaked Dummies in any returned set's free_symbols, 0 srepr/==-instability across repeat calls. Also varied global state -- clear_cache cold vs. warm, 700-frame deep stack, setrecursionlimit(400) -- over 13 probe relations spanning all outcome families: 0 DET<->UND flips, 0 in-domain<->carved-out flips, 0 determined-value changes. solvability is a genuine function of rel.

(5) Domain carve-out honesty (the classic 'totality of a partial callee' trap, SPEC_GUIDE directive 7). Confirmed the Requires(solvability==0 or ==1) carve-out is a STATED mechanism, not a silent strengthening: the real solver's other outcomes genuinely exist and are genuinely excluded. Measured 261 ValueError/TypeError (sign(x)>0, Eq(log(x),0), cbrt(x)>0, Piecewise), RecursionError (Eq(Min(1,x),0), Max(0,x)>1), and 10 timeouts/non-termination -- and verified the real PATCHED `_eval_as_set` ALSO raises/hangs on exactly those (it catches only NotImplementedError). So the abstraction and the gold patch agree on the excluded inputs; the axiom asserts nothing there. This is the sound direction (spec silent, not spec over-claiming) -- not a faithfulness defect.

(6) MASTER DIFFERENTIAL. 2370 distinct randomized univariate relations (seed 182110; 36 atom families x 6 relation constructors x 12 constants, incl. every shape flagged in mapping.md 3.1). In-domain: 742 DETERMINED + 1357 UNDECIDED = 2099 carriers; 271 correctly carved out. For each, compared the model's exact prediction against the REAL patched `_eval_as_set`: DET leg required ev == solver's own set AND isinstance(ev, Set) AND not isinstance(ev, ConditionSet); UND leg required ev is a ConditionSet with .sym==x, .condition==self, .base_set==Reals AND ev == ConditionSet(x,self,S.Reals). RESULT: 0 divergences.

**CORROBORATING FACTS:** bundle's axiom_check.py re-run against my own patched worktree exits 0 (2 F2P undecided, 18 determined, 9 broader-family classified with a non-empty 8-relation carve-out, 270 fuzz relations, no dichotomy violation). F2P confirmed live: Eq(`x*cos`(x)-`3*sin`(x),0).as_set() == ConditionSet(x, Eq(`x*cos`(x)-`3*sin`(x),0), Reals) (True), same for Eq(`x**2`+sqrt(`x*2`)+sin(x),0). P2P determined relations return the solver's own set verbatim (11/11 via direct `_eval_as_set`, bypassing the as_set periodicity guard at boolalg.py:151).

G-DIFF CONTROL (spec is sensitive, not vacuous): scripts/nagini_verify.sh on model.py -> 'Verification successful' (19.2s). On model_prepatch.py (identical spec byte-for-byte; impl differs only by dropping the try/except -- confirmed by unified diff, the sole hunk) -> 'Verification failed: mp.py:204: Assertion "method raises no exceptions" might not hold.' The frozen spec therefore rejects the pre-patch behavior on exactly the delta the patch introduces, i.e. the totality postcondition is doing real work.

**NOT-FOUND STATEMENT:** I could not exhibit any input on which the modeled function disagrees with the real patched callee. No over-strong Ensures, no drift, no smuggled totality. Every leg of the spec is a true statement about the patched repo, and the carve-out understates rather than overstates the callee.

**VERDICT:** FAITHFUL. diverging_input: none found (required to claim a defect; I claim none).

Caveat on coverage limits (no silent caps): my sweeps are finite -- 2370 distinct relations under a 6-8s per-call wall clock. Non-termination beyond that budget is classified as carved-out rather than probed further, and I did not attempt symbolic proof of ConditionSet.`__new__` total correctness over all Basic subclasses; the ValueError branch is argued unreachable-on-L1 empirically (all 4 non-Symbol L1 carriers) plus by reading the xreplace guard, not exhaustively.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL attacker 3 (leakage / gold-reconstruction) on sympy__sympy-18211/nagini. Verdict: NO-LEAKAGE.

**METHOD.** Extracted the exact consumer-visible spec view with swebench_unified.markers.spec_view(model.py, nagini.language) (245 lines; impl regions correctly elided to `...  # implementation elided`). Ran leakage.screen against the FROZEN dataset row (confirmed row['problem_statement'] == instance.json's). Judged against problem_statement ONLY, never hints_text. Cross-checked the base_commit source in a /tmp worktree (git worktree add -f  b4f1aa3540fe6).

**MECHANICAL RESULT:** rep.passed = True, zero hard failures (matches the recorded meta.json G-LEAK 'pass / spec view clean'; no RELAXED_LEAKAGE.md and relaxed_leakage is unset, so this is a strict pass, not a relaxation).

L1 (gold-diff reproduction) — NEGATIVE. Re-ran the changed-line check at a normalized threshold of 4 chars (the screen uses 8), i.e. deliberately more aggressive than the gate: ALL 9 gold changed lines miss. None of `from sympy.sets.conditionset import ConditionSet`, `xset = ConditionSet(x, self, S.Reals)`, `except NotImplementedError:`, `try:`, `return xset`, `# unsolvable equations/inequalities.` appears normalized in the view. No diff markers.

L2 (edit localization) — NEGATIVE. Zero occurrences in the view of: `sympy/core`, `relational`, `_eval_as_set`, `as_set`, `ConditionSet`/`conditionset`, `S.Reals`, `NotImplementedError`, `solveset`, `free_symbols`, `syms.pop`, `solve_univariate_inequality`, `nonzero` (the sole entry of `_patch_changed_symbols`, from the `def __nonzero__` section header). No patched file or dotted module path.

L3 (bug/fix narration) — NEGATIVE. No narration vocabulary (bug/fix/patched/previously/incorrectly/wrong/broken/regression). The docstring is written as a behavioral contract in the required register: it states desired behaviour ('The behaviour pinned here is totality of the conversion... it may never let the solver\'s undecided signal propagate to its caller'), not a diagnosis. Words like 'catches'/'escape'/'totality' describe the CONTRACT (why no Exsures is declared) rather than an edit; they carry no fix instruction. Crucially, no hints_text-only vocabulary appears: 'unsolvable', 'equations/inequalities', 'blocking' are all absent from the view — this is the single most common failure mode for this gate and the bundle avoids it.

ADVERSARIAL RECONSTRUCTION ATTEMPTS, and why each fails to establish leakage beyond the public problem_statement:

(1) The fallback's three fields. The view says the fallback 'carries the original relation as its condition, the conversion\'s variable as its bound symbol, and the whole real line as its base domain' (and Ensures cond==rel.token, sym==rel.sym, over_reals==True). This is the gold discriminator — but it is VERBATIM PUBLIC in the problem statement, which literally prints the expected answer `ConditionSet(n, Eq(n*cos(n) - 3*sin(n), 0), Reals)` plus the rendering `{n | n in R and n*cos(n) - 3*sin(n) = 0}`. Bound symbol n, condition = the relation itself, base domain = Reals are exactly the three fields the issue displays. Stating them adds nothing a consumer does not already read in the task.

(2) Totality / do-not-let-the-signal-escape. The PS title IS 'solveset raises NotImplementedError instead of returning ConditionSet' and its body says a ConditionSet 'should be returned... instead'. The raise-vs-return dichotomy is the public issue, not a leaked diagnosis.

(3) The `solve_univariate` axiom name and the 'univariate solver' framing. Checked against the worktree: at base_commit, relational.py:390-395 ALREADY reads `# self is univariate ...`, `from sympy.solvers.inequalities import solve_univariate_inequality`, and `return solve_univariate_inequality(self, x, relational=False)`. The callee is PRE-EXISTING context that the gold patch preserves, not fix-introduced (`_patch_new_symbols`(gold) == empty set). The view also does not name it verbatim — `solve_univariate` is the abstraction's own name. Naming the unchanged callee the pre-patch code already called localizes no edit.

(4) Test-identity leakage. Zero occurrences of `test_`, `18188`, `Eq(`, `cos`, `sqrt`, or any F2P/test_patch artifact. The F2P concrete inputs are absent; the docstring explicitly says the relation's algebraic structure is deliberately NOT modelled.

(5) The instance id `sympy__sympy-18211` appears in the module docstring line 1. Not a leak: instance_id is emitted to the consumer unconditionally by eval/dataset.as_dict, so it reveals nothing incremental.

(6) Nagini-mechanics asides ('a builtin exception in an Exsures crashes the translator', 'mapping.md §3 / axiom_check.py') are verifier-tooling notes and bundle cross-references, not repo/edit information; mapping.md is not shipped in the consumer view.

OBSERVATION (out of scope for this gate, recorded for completeness, NOT a finding). meta.json modeled_functions IS consumer-visible in spec modes and hands over repo_symbol 'sympy.core.relational.Relational.`_eval_as_set`' + repo_location 'sympy/core/relational.py:389', and its role string says 'with a total fallback when the solver is undecided'. That is by design (MODES_WITH_LOCALIZATION supplies changed_files/repo_symbol deliberately, isolating 'where to edit' from 'how'), and the fallback it names is public per point (1). My mandate is the spec view, which is clean.

**CONCLUSION.** Every discriminating fact stated in the spec view is derivable from the public problem_statement alone; nothing in the view names the patched file, function, callee-as-changed, exception type, or constructed class, and no gold line is reproduced even at a threshold twice as strict as the gate's. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
