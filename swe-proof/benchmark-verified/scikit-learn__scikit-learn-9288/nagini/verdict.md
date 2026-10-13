# P2 adversarial audit — scikit-learn__scikit-learn-9288

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     kept result is strategy-independent."""
     # pre-conditions-start
     Requires(n_restarts >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -104,29 +102,14 @@
     # post-conditions-end
     # impl-start
     start = source_state(config)
-    cur = start
+    shared = draw(start)
     result = []  # type: List[int]
     i = 0
     while i < n_restarts:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_restarts)
         Invariant(len(result) == i)
-        # "what is built ++ the draw vector of the rest == the whole vector":
-        # `result` is the first i restart seeds and `cur` is the state the i-th
-        # restart's seed is drawn at, so the draw vector of the remaining
-        # n-i restarts from `cur` completes exactly the full vector.
-        Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
-                  seed_vector(start, n_restarts))
-        Invariant(MustTerminate(n_restarts - i + 1))
-        # invariants-end
-        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
-        # its head draw at `cur` followed by the vector from the advanced state
-        # -- exactly the move performed below.
-        Assert(seed_vector(cur, n_restarts - i) ==
-               PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
-        result = result + [draw(cur)]
-        cur = advance(cur)
+        result = result + [shared]
         i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     kept result is strategy-independent."""
     # pre-conditions-start
     Requires(n_restarts >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -103,26 +101,16 @@
     Ensures(ToSeq(Result()) == seed_vector(source_state(config), n_restarts))
     # post-conditions-end
     # impl-start
-    start = source_state(config)
+    start = advance(source_state(config))
     cur = start
     result = []  # type: List[int]
     i = 0
     while i < n_restarts:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_restarts)
         Invariant(len(result) == i)
-        # "what is built ++ the draw vector of the rest == the whole vector":
-        # `result` is the first i restart seeds and `cur` is the state the i-th
-        # restart's seed is drawn at, so the draw vector of the remaining
-        # n-i restarts from `cur` completes exactly the full vector.
         Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
                   seed_vector(start, n_restarts))
-        Invariant(MustTerminate(n_restarts - i + 1))
-        # invariants-end
-        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
-        # its head draw at `cur` followed by the vector from the advanced state
-        # -- exactly the move performed below.
         Assert(seed_vector(cur, n_restarts - i) ==
                PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
         result = result + [draw(cur)]
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     kept result is strategy-independent."""
     # pre-conditions-start
     Requires(n_restarts >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,25 +106,11 @@
     result = []  # type: List[int]
     i = 0
     while i < n_restarts:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_restarts)
         Invariant(len(result) == i)
-        # "what is built ++ the draw vector of the rest == the whole vector":
-        # `result` is the first i restart seeds and `cur` is the state the i-th
-        # restart's seed is drawn at, so the draw vector of the remaining
-        # n-i restarts from `cur` completes exactly the full vector.
-        Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
-                  seed_vector(start, n_restarts))
-        Invariant(MustTerminate(n_restarts - i + 1))
-        # invariants-end
-        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
-        # its head draw at `cur` followed by the vector from the advanced state
-        # -- exactly the move performed below.
-        Assert(seed_vector(cur, n_restarts - i) ==
-               PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
+        cur = advance(cur)
         result = result + [draw(cur)]
-        cur = advance(cur)
         i = i + 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     kept result is strategy-independent."""
     # pre-conditions-start
     Requires(n_restarts >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -103,26 +101,19 @@
     Ensures(ToSeq(Result()) == seed_vector(source_state(config), n_restarts))
     # post-conditions-end
     # impl-start
+    if n_restarts == 1:
+        # partial-domain: wrong seed on the single-restart boundary only
+        return [draw(advance(source_state(config)))]
     start = source_state(config)
     cur = start
     result = []  # type: List[int]
     i = 0
     while i < n_restarts:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_restarts)
         Invariant(len(result) == i)
-        # "what is built ++ the draw vector of the rest == the whole vector":
-        # `result` is the first i restart seeds and `cur` is the state the i-th
-        # restart's seed is drawn at, so the draw vector of the remaining
-        # n-i restarts from `cur` completes exactly the full vector.
         Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
                   seed_vector(start, n_restarts))
-        Invariant(MustTerminate(n_restarts - i + 1))
-        # invariants-end
-        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
-        # its head draw at `cur` followed by the vector from the advanced state
-        # -- exactly the move performed below.
         Assert(seed_vector(cur, n_restarts - i) ==
                PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
         result = result + [draw(cur)]
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     kept result is strategy-independent."""
     # pre-conditions-start
     Requires(n_restarts >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,25 +106,16 @@
     result = []  # type: List[int]
     i = 0
     while i < n_restarts:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_restarts)
         Invariant(len(result) == i)
-        # "what is built ++ the draw vector of the rest == the whole vector":
-        # `result` is the first i restart seeds and `cur` is the state the i-th
-        # restart's seed is drawn at, so the draw vector of the remaining
-        # n-i restarts from `cur` completes exactly the full vector.
         Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
                   seed_vector(start, n_restarts))
-        Invariant(MustTerminate(n_restarts - i + 1))
-        # invariants-end
-        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
-        # its head draw at `cur` followed by the vector from the advanced state
-        # -- exactly the move performed below.
         Assert(seed_vector(cur, n_restarts - i) ==
                PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
         result = result + [draw(cur)]
         cur = advance(cur)
         i = i + 1
+    result = result + [draw(cur)]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     kept result is strategy-independent."""
     # pre-conditions-start
     Requires(n_restarts >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,24 +106,15 @@
     result = []  # type: List[int]
     i = 0
     while i < n_restarts:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_restarts)
         Invariant(len(result) == i)
-        # "what is built ++ the draw vector of the rest == the whole vector":
-        # `result` is the first i restart seeds and `cur` is the state the i-th
-        # restart's seed is drawn at, so the draw vector of the remaining
-        # n-i restarts from `cur` completes exactly the full vector.
         Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
                   seed_vector(start, n_restarts))
-        Invariant(MustTerminate(n_restarts - i + 1))
-        # invariants-end
-        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
-        # its head draw at `cur` followed by the vector from the advanced state
-        # -- exactly the move performed below.
         Assert(seed_vector(cur, n_restarts - i) ==
                PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
-        result = result + [draw(cur)]
+        d = draw(cur)
+        result = result + [d]
         cur = advance(cur)
         i = i + 1
     return result
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     kept result is strategy-independent."""
     # pre-conditions-start
     Requires(n_restarts >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,24 +106,10 @@
     result = []  # type: List[int]
     i = 0
     while i < n_restarts:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_restarts)
         Invariant(len(result) == i)
-        # "what is built ++ the draw vector of the rest == the whole vector":
-        # `result` is the first i restart seeds and `cur` is the state the i-th
-        # restart's seed is drawn at, so the draw vector of the remaining
-        # n-i restarts from `cur` completes exactly the full vector.
-        Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
-                  seed_vector(start, n_restarts))
-        Invariant(MustTerminate(n_restarts - i + 1))
-        # invariants-end
-        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
-        # its head draw at `cur` followed by the vector from the advanced state
-        # -- exactly the move performed below.
-        Assert(seed_vector(cur, n_restarts - i) ==
-               PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
-        result = result + [draw(cur)]
+        result = [draw(cur)] + result
         cur = advance(cur)
         i = i + 1
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-9288.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A clustering routine performs several independent restarts from a configured
  pseudo-random source, then keeps the best restart. The routine offers two
  execution strategies (a single-worker strategy and a multi-worker strategy),
  selected by a resource count, but BOTH strategies must explore the same
  restarts so the kept result does not depend on which strategy is used.

  To guarantee this, the per-restart randomness must be drawn ONCE, up front,
  as a single vector of independent restart seeds taken from the configured
  source: restart i is run from `seed_vector[i]`, the i-th draw of the shared
  source. Every execution strategy then consumes that same vector, so the
  restart that restart i explores is a function of the configured source alone
  and is identical across strategies.

  The consequence the specification pins is that the single-worker strategy's
  per-restart seeds are NOT taken from a differently-evolving source than the
  multi-worker strategy's; both equal the one up-front draw vector. Restart i is
  seeded from the i-th draw (the (i)-fold-advanced state of the source), so the
  vector advances across restarts and is shared verbatim by both strategies.

The pseudo-random source's internal state is modelled as an integer. Obtaining
the source's initial state from the configuration, advancing it by one draw, and
reading the integer seed a draw yields are unchanged primitives, modelled as
abstract pure functions (`source_state`, `advance`, `draw`) whose real
counterparts are validated out-of-band by axiom_check.py (G-AX). The up-front
restart-seed vector is modelled deeply as a front-recursive fold (`seed_vector`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def source_state(config: int) -> int:
    """Initial internal state of the pseudo-random source obtained from an
    integer configuration value (the unchanged configuration-to-source step).
    Abstract: the proof relies only on this being a deterministic function of
    the configuration, not on any particular value. Real counterpart +
    executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def advance(state: int) -> int:
    """Internal state of the pseudo-random source after one draw advances it
    (the unchanged per-draw state transition). Abstract: the proof relies only
    on it being a deterministic function of the current state. That the real
    transition actually MOVES the state (so successive restart seeds differ) is
    the discriminating fact validated by axiom_check.py (G-AX), not a consumed
    contract here. Real counterpart: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def draw(state: int) -> int:
    """The integer restart seed yielded by a single draw taken at source state
    `state` (the unchanged read of a draw's value). Abstract: a deterministic
    function of the current state. Real counterpart: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def seed_vector(s: int, n: int) -> PSeq[int]:
    """The up-front vector of `n` independent restart seeds drawn from one
    shared source starting at state `s`: restart 0 takes the draw at `s`,
    restart 1 the draw at `advance(s)`, restart k the draw at the k-fold advance
    of `s`. Front-recursive on `n` so a single unfold is available per loop
    step. This is the one vector both execution strategies must consume."""
    Requires(n >= 0)
    if n == 0:
        return PSeq(0).take(0)
    return PSeq(draw(s)) + seed_vector(advance(s), n - 1)
# pure-end


def restart_seeds(config: int, n_restarts: int) -> List[int]:
    """The per-restart seeds the single-worker strategy uses for `n_restarts`
    restarts from the source configured by integer `config`. Element k is the
    integer seed restart k is run from. The specification requires this to be
    the SAME up-front draw vector the multi-worker strategy consumes, so the
    kept result is strategy-independent."""
    # pre-conditions-start
    Requires(n_restarts >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n_restarts)
    # The per-restart seeds are the one up-front draw vector from the source's
    # initial state: restart k is seeded from the k-th draw (the k-fold-advanced
    # state), the identical vector the multi-worker strategy consumes.
    Ensures(ToSeq(Result()) == seed_vector(source_state(config), n_restarts))
    # post-conditions-end
    # impl-start
    start = source_state(config)
    cur = start
    result = []  # type: List[int]
    i = 0
    while i < n_restarts:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n_restarts)
        Invariant(len(result) == i)
        # "what is built ++ the draw vector of the rest == the whole vector":
        # `result` is the first i restart seeds and `cur` is the state the i-th
        # restart's seed is drawn at, so the draw vector of the remaining
        # n-i restarts from `cur` completes exactly the full vector.
        Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
                  seed_vector(start, n_restarts))
        # invariants-end
        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
        # its head draw at `cur` followed by the vector from the advanced state
        # -- exactly the move performed below.
        Assert(seed_vector(cur, n_restarts - i) ==
               PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
        result = result + [draw(cur)]
        cur = advance(cur)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Baseline: positive_control (gold model.py) VERIFIES (13.5s); prepatch (model_prepatch.py) FAILS the postcondition (Postcondition of restart_seeds might not hold: ToSeq(Result())==seed_vector(...)) and is same-spec => prepatch_reproduced=true. All 7 attacks are byte-identical in spec/axioms/@Pure/Requires/Ensures (same-spec exit 0), editing only the impl region.

Attacks (cmd: python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-9288 <path>):
- atk_1.py (control-flow/ungrounded-oracle: prepatch shared-value bug, every restart emits draw(start)): NOT-A-COUNTEREXAMPLE, does not verify (exit 2).
- atk_2.py (boundary/skip-first: start=advance(source_state(config))): does not verify (exit 2).
- atk_3.py (control-flow-effect: advance-then-draw swap, cur=advance(cur) before draw): does not verify (exit 2).
- atk_4.py (partial-domain: special-cases n_restarts==1 to a wrong seed): does not verify (exit 2).
- atk_5.py (boundary/off-by-one length: appends one extra draw(cur) after loop): does not verify (exit 2).
- atk_7.py (reversed content: result=[draw(cur)]+result, wrong order): does not verify (exit 2).
- atk_6.py (echo / behaviorally-correct restructuring: temp d=draw(cur) then append, identical output vector): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (13.1s, exit 0).

For the ONE candidate (atk_6): its output equals the gold seed vector byte-for-byte (postcondition ToSeq(Result())==seed_vector(source_state(config), n_restarts) totally pins the result), so its faithful refined patch IS patch.diff verbatim. Materialized at atk_6.faithful.patch and executed via swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-9288', patch, timeout=3600): RESOLVED=True, completed=True. A resolving echo is not a weakness (fixed G-PANEL-1/G-EQ resolve-step policy). No verifying wrong impl whose faithful patch fails to resolve was found.

Refinement audit: refinement.md legs = 3 R + 2 A-reference + 0 A-consumed + 0 kind-3 (matches §B). Abstract callees source_state/advance/draw carry NO Ensures (weakest abstraction) so the proof consumes no callee contract; the discriminating 'advancing up-front vector' fact is validated empirically against real numpy RandomState + patched sklearn KMeans by axiom_check.py (G-AX). A-reference correspondence to the real callees (check_random_state int-branch RandomState(config); randint(int32.max, size=n_init) as the position-dependent up-front draw vector consumed verbatim by both n_jobs branches) holds and is exercised by axiom_check's three obligations. meta gates G-AX/G-EQ/G-DIFF/G-RESOLVE/G-VERIFY/G-PANEL-1 all pass. The postcondition fully constrains Result() on all valid inputs, so verify=>correct: any verifying impl reproduces the exact gold seed vector and its faithful refinement resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-9288.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A clustering routine performs several independent restarts from a configured
  pseudo-random source, then keeps the best restart. The routine offers two
  execution strategies (a single-worker strategy and a multi-worker strategy),
  selected by a resource count, but BOTH strategies must explore the same
  restarts so the kept result does not depend on which strategy is used.

  To guarantee this, the per-restart randomness must be drawn ONCE, up front,
  as a single vector of independent restart seeds taken from the configured
  source: restart i is run from `seed_vector[i]`, the i-th draw of the shared
  source. Every execution strategy then consumes that same vector, so the
  restart that restart i explores is a function of the configured source alone
  and is identical across strategies.

  The consequence the specification pins is that the single-worker strategy's
  per-restart seeds are NOT taken from a differently-evolving source than the
  multi-worker strategy's; both equal the one up-front draw vector. Restart i is
  seeded from the i-th draw (the (i)-fold-advanced state of the source), so the
  vector advances across restarts and is shared verbatim by both strategies.

The pseudo-random source's internal state is modelled as an integer. Obtaining
the source's initial state from the configuration, advancing it by one draw, and
reading the integer seed a draw yields are unchanged primitives, modelled as
abstract pure functions (`source_state`, `advance`, `draw`) whose real
counterparts are validated out-of-band by axiom_check.py (G-AX). The up-front
restart-seed vector is modelled deeply as a front-recursive fold (`seed_vector`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def source_state(config: int) -> int:
    """Initial internal state of the pseudo-random source obtained from an
    integer configuration value (the unchanged configuration-to-source step).
    Abstract: the proof relies only on this being a deterministic function of
    the configuration, not on any particular value. Real counterpart +
    executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def advance(state: int) -> int:
    """Internal state of the pseudo-random source after one draw advances it
    (the unchanged per-draw state transition). Abstract: the proof relies only
    on it being a deterministic function of the current state. That the real
    transition actually MOVES the state (so successive restart seeds differ) is
    the discriminating fact validated by axiom_check.py (G-AX), not a consumed
    contract here. Real counterpart: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def draw(state: int) -> int:
    """The integer restart seed yielded by a single draw taken at source state
    `state` (the unchanged read of a draw's value). Abstract: a deterministic
    function of the current state. Real counterpart: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def seed_vector(s: int, n: int) -> PSeq[int]:
    """The up-front vector of `n` independent restart seeds drawn from one
    shared source starting at state `s`: restart 0 takes the draw at `s`,
    restart 1 the draw at `advance(s)`, restart k the draw at the k-fold advance
    of `s`. Front-recursive on `n` so a single unfold is available per loop
    step. This is the one vector both execution strategies must consume."""
    Requires(n >= 0)
    if n == 0:
        return PSeq(0).take(0)
    return PSeq(draw(s)) + seed_vector(advance(s), n - 1)
# pure-end


def restart_seeds(config: int, n_restarts: int) -> List[int]:
    """The per-restart seeds the single-worker strategy uses for `n_restarts`
    restarts from the source configured by integer `config`. Element k is the
    integer seed restart k is run from. The specification requires this to be
    the SAME up-front draw vector the multi-worker strategy consumes, so the
    kept result is strategy-independent."""
    # pre-conditions-start
    Requires(n_restarts >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n_restarts)
    # The per-restart seeds are the one up-front draw vector from the source's
    # initial state: restart k is seeded from the k-th draw (the k-fold-advanced
    # state), the identical vector the multi-worker strategy consumes.
    Ensures(ToSeq(Result()) == seed_vector(source_state(config), n_restarts))
    # post-conditions-end
    # impl-start
    start = source_state(config)
    cur = start
    result = []  # type: List[int]
    i = 0
    while i < n_restarts:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n_restarts)
        Invariant(len(result) == i)
        # "what is built ++ the draw vector of the rest == the whole vector":
        # `result` is the first i restart seeds and `cur` is the state the i-th
        # restart's seed is drawn at, so the draw vector of the remaining
        # n-i restarts from `cur` completes exactly the full vector.
        Invariant(ToSeq(result) + seed_vector(cur, n_restarts - i) ==
                  seed_vector(start, n_restarts))
        # invariants-end
        # The remaining vector is non-empty (i < n_restarts), so it unfolds to
        # its head draw at `cur` followed by the vector from the advanced state
        # -- exactly the move performed below.
        Assert(seed_vector(cur, n_restarts - i) ==
               PSeq(draw(cur)) + seed_vector(advance(cur), n_restarts - i - 1))
        result = result + [draw(cur)]
        cur = advance(cur)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Baseline: positive_control (gold model.py) VERIFIES (13.5s); prepatch (model_prepatch.py) FAILS the postcondition (Postcondition of restart_seeds might not hold: ToSeq(Result())==seed_vector(...)) and is same-spec => prepatch_reproduced=true. All 7 attacks are byte-identical in spec/axioms/@Pure/Requires/Ensures (same-spec exit 0), editing only the impl region.

Attacks (cmd: python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-9288 <path>):
- atk_1.py (control-flow/ungrounded-oracle: prepatch shared-value bug, every restart emits draw(start)): NOT-A-COUNTEREXAMPLE, does not verify (exit 2).
- atk_2.py (boundary/skip-first: start=advance(source_state(config))): does not verify (exit 2).
- atk_3.py (control-flow-effect: advance-then-draw swap, cur=advance(cur) before draw): does not verify (exit 2).
- atk_4.py (partial-domain: special-cases n_restarts==1 to a wrong seed): does not verify (exit 2).
- atk_5.py (boundary/off-by-one length: appends one extra draw(cur) after loop): does not verify (exit 2).
- atk_7.py (reversed content: result=[draw(cur)]+result, wrong order): does not verify (exit 2).
- atk_6.py (echo / behaviorally-correct restructuring: temp d=draw(cur) then append, identical output vector): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (13.1s, exit 0).

For the ONE candidate (atk_6): its output equals the gold seed vector byte-for-byte (postcondition ToSeq(Result())==seed_vector(source_state(config), n_restarts) totally pins the result), so its faithful refined patch IS patch.diff verbatim. Materialized at atk_6.faithful.patch and executed via swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-9288', patch, timeout=3600): RESOLVED=True, completed=True. A resolving echo is not a weakness (fixed G-PANEL-1/G-EQ resolve-step policy). No verifying wrong impl whose faithful patch fails to resolve was found.

Refinement audit: refinement.md legs = 3 R + 2 A-reference + 0 A-consumed + 0 kind-3 (matches §B). Abstract callees source_state/advance/draw carry NO Ensures (weakest abstraction) so the proof consumes no callee contract; the discriminating 'advancing up-front vector' fact is validated empirically against real numpy RandomState + patched sklearn KMeans by axiom_check.py (G-AX). A-reference correspondence to the real callees (check_random_state int-branch RandomState(config); randint(int32.max, size=n_init) as the position-dependent up-front draw vector consumed verbatim by both n_jobs branches) holds and is exercised by axiom_check's three obligations. meta gates G-AX/G-EQ/G-DIFF/G-RESOLVE/G-VERIFY/G-PANEL-1 all pass. The postcondition fully constrains Result() on all valid inputs, so verify=>correct: any verifying impl reproduces the exact gold seed vector and its faithful refinement resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/spec-too-strong audit of scikit-learn__scikit-learn-9288 (Nagini). No diverging input found; the modeled restart_seeds agrees with the real post-patch callee on the entire reachable domain.

INTEGRITY: spec region byte-identical (adversary same-spec on an identical copy of model.py returns SAME, exit 0). model.py VERIFIES with pinned Nagini (11.0s, exit 0) -- genuine green.

### Why not too strong
1) The abstract callees source_state/advance/draw carry NO Ensures (@Pure @ContractOnly, A-reference). A spec cannot be over-strong via a callee that asserts nothing about its value -- the weakest faithful abstraction. The only discriminating obligation is the single postcondition P3: ToSeq(Result()) == seed_vector(source_state(config), n_restarts), the front-recursive advancing draw fold [draw(s), draw(advance(s)), ...].
2) Verified P3's structural claim directly against REAL numpy (numpy 1.26.4): RandomState(cfg).randint(int32.max, size=n) equals n successive scalar randint draws IN ORDER, and entries are distinct/advancing, for cfg in 0..29 and n in {1,2,10,50,257}. This is exactly the front-recursive fold seed_vector encodes -- ordering and advancing structure are faithful, not idealized/over-specified.
3) Boundary n_restarts=0 is faithful: real randint(size=0)==[] matches seed_vector(s,0)==[] (== PSeq(0).take(0)). n<0 excluded by Requires(n>=0).
4) Type abstraction (int config; identity on the int branch of check_random_state) matches the tested F2P call random_state=0.
5) Elided machinery (X, weights, init, Parallel, argmin/best_inertia selection) is unchanged by the patch and orthogonal to the F2P discriminator (n_jobs=1 vs n_jobs=2 labels_ equality), which holds iff both strategies consume the same per-restart seed vector -- exactly what P3 pins. model_prepatch.py (constant shared list) fails P3 as expected (G-DIFF sensing).

Note: axiom_check.py's end-to-end KMeans(n_jobs=...) sub-check errors under the locally-installed sklearn 1.3.0 (n_jobs kwarg removed upstream) -- that is environment drift affecting the separate G-AX gate, NOT a faithfulness defect; A-reference 1/2 (the fold-advances and live-object-diverges obligations) I re-verified independently against real numpy. No input where the modeled function diverges from the real repo's post-patch seed vector.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view is byte-identical to the audited bundle: computed spec_view sha256 06c66bf4f57e79aa947e0355028ca178f9502bdc4271350009f1414e565e4bf0 == meta.region_hashes.spec_view (and matches the sha referenced in the recorded G-PANEL-3 note). Bundle is NOT relaxed (relaxed_leakage null, no RELAXED_LEAKAGE.md), so this is a genuine strict judgment. Mechanical G-LEAK screen passes independently (no diff markers, no reproduced gold-patch line, no patched file path/module, no spec-view identifier embedding the sole changed symbol 'k_means', no bug/fix narration).

Judged the spec view (docstring + axioms source_state/advance/draw + pure seed_vector + restart_seeds pre/post-conditions, impl+invariants elided) against the PUBLIC problem_statement ONLY (hints_text excluded per policy).

Gold edit = hoist `seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)` above the n_jobs branch split and loop `for seed in seeds`/`random_state=seed` in the single-worker branch. The public problem_statement already states the full observable symptom (KMeans inertia differs for n_jobs=1 vs n_jobs>1) and the required invariant (result identical regardless of n_jobs); pinning that required-correct behavior is the intrinsic job of a spec, not leakage. The spec view names NO repo entity that enables reconstruction: no KMeans/k_means, randint, RandomState, n_init, n_jobs, inertia/argmin, int32 constant, filename sklearn/cluster/k_means_.py, or any patch code fragment. The internal data-flow is carried entirely by modeling-only abstract A-reference symbols (source_state/advance/draw/seed_vector) and generic prose ('clustering routine', 'execution strategies selected by a resource count', 'keeps the best restart').

The 'draw once up front as a single shared vector, every strategy consumes it' framing is the logically-forced behavioral condition for the publicly-stated n_jobs-invariance, not disclosure of the concrete edit; it overlaps conceptually with the (excluded) hints' diagnosis but adds no repo-level reconstruction beyond the public statement. The concrete file/line/numpy-call are absent, so the gold edit cannot be copied out of the spec view. Concurs with G-LEAK ('spec view clean') and the prior recorded G-PANEL-3 verdict.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
