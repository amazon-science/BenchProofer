# P2 adversarial audit — django__django-15382

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EmptyResultSet(Exception):
@@ -83,7 +82,6 @@
     is the callee the predicate renderer invokes and does NOT change. Provenance +
     executable soundness: mapping.md / axiom_check.py (A-consumed)."""
     Requires(satisfiable == 0 or satisfiable == 1)
-    Requires(MustTerminate(2))
     Ensures(satisfiable == 1)
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
@@ -103,7 +101,6 @@
     # pre-conditions-start
     Requires(satisfiable == 0 or satisfiable == 1)
     Requires(negated == 0 or negated == 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The matches-nothing signal is observable ONLY on the non-negated
@@ -129,18 +126,8 @@
     Exsures(EmptyResultSet, satisfiable == 0 and negated == 0)
     # post-conditions-end
     # impl-start
-    try:
-        sql = render_inner(satisfiable)  # type: List[int]
-    except EmptyResultSet as exc:
-        # Inner selection is unsatisfiable. A negated existence predicate over an
-        # empty selection is universally true -> return normally (here, the empty
-        # always-true fragment). A non-negated one can never hold -> re-propagate.
-        if negated == 1:
-            empty = []  # type: List[int]
-            return empty
-        raise exc
+    sql = render_inner(satisfiable)  # type: List[int]
     if negated == 1:
         sql = [78, 79, 84, 32] + sql
-        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
     return sql
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EmptyResultSet(Exception):
@@ -83,7 +82,6 @@
     is the callee the predicate renderer invokes and does NOT change. Provenance +
     executable soundness: mapping.md / axiom_check.py (A-consumed)."""
     Requires(satisfiable == 0 or satisfiable == 1)
-    Requires(MustTerminate(2))
     Ensures(satisfiable == 1)
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
@@ -103,7 +101,6 @@
     # pre-conditions-start
     Requires(satisfiable == 0 or satisfiable == 1)
     Requires(negated == 0 or negated == 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The matches-nothing signal is observable ONLY on the non-negated
@@ -132,15 +129,9 @@
     try:
         sql = render_inner(satisfiable)  # type: List[int]
     except EmptyResultSet as exc:
-        # Inner selection is unsatisfiable. A negated existence predicate over an
-        # empty selection is universally true -> return normally (here, the empty
-        # always-true fragment). A non-negated one can never hold -> re-propagate.
-        if negated == 1:
-            empty = []  # type: List[int]
-            return empty
-        raise exc
+        empty = []  # type: List[int]
+        return empty
     if negated == 1:
         sql = [78, 79, 84, 32] + sql
-        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
     return sql
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EmptyResultSet(Exception):
@@ -83,7 +82,6 @@
     is the callee the predicate renderer invokes and does NOT change. Provenance +
     executable soundness: mapping.md / axiom_check.py (A-consumed)."""
     Requires(satisfiable == 0 or satisfiable == 1)
-    Requires(MustTerminate(2))
     Ensures(satisfiable == 1)
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
@@ -103,7 +101,6 @@
     # pre-conditions-start
     Requires(satisfiable == 0 or satisfiable == 1)
     Requires(negated == 0 or negated == 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The matches-nothing signal is observable ONLY on the non-negated
@@ -132,15 +129,12 @@
     try:
         sql = render_inner(satisfiable)  # type: List[int]
     except EmptyResultSet as exc:
-        # Inner selection is unsatisfiable. A negated existence predicate over an
-        # empty selection is universally true -> return normally (here, the empty
-        # always-true fragment). A non-negated one can never hold -> re-propagate.
         if negated == 1:
             empty = []  # type: List[int]
             return empty
         raise exc
+    fabricated = [88]  # type: List[int]
     if negated == 1:
-        sql = [78, 79, 84, 32] + sql
-        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
-    return sql
+        fabricated = [78, 79, 84, 32] + fabricated
+    return fabricated
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EmptyResultSet(Exception):
@@ -83,7 +82,6 @@
     is the callee the predicate renderer invokes and does NOT change. Provenance +
     executable soundness: mapping.md / axiom_check.py (A-consumed)."""
     Requires(satisfiable == 0 or satisfiable == 1)
-    Requires(MustTerminate(2))
     Ensures(satisfiable == 1)
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
@@ -103,7 +101,6 @@
     # pre-conditions-start
     Requires(satisfiable == 0 or satisfiable == 1)
     Requires(negated == 0 or negated == 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The matches-nothing signal is observable ONLY on the non-negated
@@ -132,15 +129,11 @@
     try:
         sql = render_inner(satisfiable)  # type: List[int]
     except EmptyResultSet as exc:
-        # Inner selection is unsatisfiable. A negated existence predicate over an
-        # empty selection is universally true -> return normally (here, the empty
-        # always-true fragment). A non-negated one can never hold -> re-propagate.
         if negated == 1:
-            empty = []  # type: List[int]
-            return empty
+            nonempty = [48]  # type: List[int]
+            return nonempty
         raise exc
     if negated == 1:
         sql = [78, 79, 84, 32] + sql
-        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
     return sql
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EmptyResultSet(Exception):
@@ -83,7 +82,6 @@
     is the callee the predicate renderer invokes and does NOT change. Provenance +
     executable soundness: mapping.md / axiom_check.py (A-consumed)."""
     Requires(satisfiable == 0 or satisfiable == 1)
-    Requires(MustTerminate(2))
     Ensures(satisfiable == 1)
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
@@ -103,7 +101,6 @@
     # pre-conditions-start
     Requires(satisfiable == 0 or satisfiable == 1)
     Requires(negated == 0 or negated == 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The matches-nothing signal is observable ONLY on the non-negated
@@ -132,15 +129,11 @@
     try:
         sql = render_inner(satisfiable)  # type: List[int]
     except EmptyResultSet as exc:
-        # Inner selection is unsatisfiable. A negated existence predicate over an
-        # empty selection is universally true -> return normally (here, the empty
-        # always-true fragment). A non-negated one can never hold -> re-propagate.
         if negated == 1:
             empty = []  # type: List[int]
             return empty
         raise exc
-    if negated == 1:
+    if negated == 0:
         sql = [78, 79, 84, 32] + sql
-        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
     return sql
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EmptyResultSet(Exception):
@@ -83,7 +82,6 @@
     is the callee the predicate renderer invokes and does NOT change. Provenance +
     executable soundness: mapping.md / axiom_check.py (A-consumed)."""
     Requires(satisfiable == 0 or satisfiable == 1)
-    Requires(MustTerminate(2))
     Ensures(satisfiable == 1)
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
@@ -103,7 +101,6 @@
     # pre-conditions-start
     Requires(satisfiable == 0 or satisfiable == 1)
     Requires(negated == 0 or negated == 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The matches-nothing signal is observable ONLY on the non-negated
@@ -132,15 +129,9 @@
     try:
         sql = render_inner(satisfiable)  # type: List[int]
     except EmptyResultSet as exc:
-        # Inner selection is unsatisfiable. A negated existence predicate over an
-        # empty selection is universally true -> return normally (here, the empty
-        # always-true fragment). A non-negated one can never hold -> re-propagate.
         if negated == 1:
             empty = []  # type: List[int]
             return empty
         raise exc
-    if negated == 1:
-        sql = [78, 79, 84, 32] + sql
-        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
     return sql
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EmptyResultSet(Exception):
@@ -83,7 +82,6 @@
     is the callee the predicate renderer invokes and does NOT change. Provenance +
     executable soundness: mapping.md / axiom_check.py (A-consumed)."""
     Requires(satisfiable == 0 or satisfiable == 1)
-    Requires(MustTerminate(2))
     Ensures(satisfiable == 1)
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
@@ -103,7 +101,6 @@
     # pre-conditions-start
     Requires(satisfiable == 0 or satisfiable == 1)
     Requires(negated == 0 or negated == 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The matches-nothing signal is observable ONLY on the non-negated
@@ -130,17 +127,24 @@
     # post-conditions-end
     # impl-start
     try:
-        sql = render_inner(satisfiable)  # type: List[int]
+        rendered = render_inner(satisfiable)  # type: List[int]
     except EmptyResultSet as exc:
-        # Inner selection is unsatisfiable. A negated existence predicate over an
-        # empty selection is universally true -> return normally (here, the empty
-        # always-true fragment). A non-negated one can never hold -> re-propagate.
         if negated == 1:
             empty = []  # type: List[int]
             return empty
         raise exc
+    # echo-reconstruct: rebuild the same content into a fresh list
+    sql = []  # type: List[int]
+    i = 0
+    while i < len(rendered):
+        Invariant(Acc(list_pred(rendered)))
+        Invariant(Acc(list_pred(sql)))
+        Invariant(0 <= i and i <= len(rendered))
+        Invariant(ToSeq(sql) == ToSeq(rendered).take(i))
+        sql.append(rendered[i])
+        i = i + 1
+    Assert(ToSeq(sql) == inner_fragment(satisfiable))
     if negated == 1:
         sql = [78, 79, 84, 32] + sql
-        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
     return sql
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EmptyResultSet(Exception):
@@ -83,7 +82,6 @@
     is the callee the predicate renderer invokes and does NOT change. Provenance +
     executable soundness: mapping.md / axiom_check.py (A-consumed)."""
     Requires(satisfiable == 0 or satisfiable == 1)
-    Requires(MustTerminate(2))
     Ensures(satisfiable == 1)
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
@@ -103,7 +101,6 @@
     # pre-conditions-start
     Requires(satisfiable == 0 or satisfiable == 1)
     Requires(negated == 0 or negated == 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The matches-nothing signal is observable ONLY on the non-negated
@@ -132,15 +129,10 @@
     try:
         sql = render_inner(satisfiable)  # type: List[int]
     except EmptyResultSet as exc:
-        # Inner selection is unsatisfiable. A negated existence predicate over an
-        # empty selection is universally true -> return normally (here, the empty
-        # always-true fragment). A non-negated one can never hold -> re-propagate.
         if negated == 1:
             empty = []  # type: List[int]
             return empty
         raise exc
-    if negated == 1:
-        sql = [78, 79, 84, 32] + sql
-        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
+    sql = [78, 79, 84, 32] + sql
     return sql
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15382.

Behaviour under specification (an abstract behavioural contract over the result,
NOT an edit or a diagnosis):

  A negatable existence predicate over an inner sub-selection is rendered to a
  fragment of result text. Rendering the inner sub-selection is delegated to a
  shared (unchanged) sub-selection renderer, which has two outcomes: for a
  SATISFIABLE inner selection it yields a non-empty inner fragment; for an
  UNSATISFIABLE one it signals the "matches-nothing" condition.

  The predicate also carries a negation flag. The result of rendering the
  predicate, by case, is:

    * inner selection satisfiable, not negated  -> the inner fragment;
    * inner selection satisfiable, negated      -> the inner fragment with the
                                                    negation marker prepended;
    * inner selection unsatisfiable, negated     -> a result that, in the
                                                    surrounding condition, holds
                                                    for every row (the negation
                                                    of "exists no row of an empty
                                                    selection");
    * inner selection unsatisfiable, not negated -> the matches-nothing condition
                                                    (an existence test over an
                                                    empty selection never holds).

  The behaviour the surrounding condition observes is whether the predicate
  reduces to "matches every row" or to the matches-nothing condition, and (on the
  satisfiable cases) whether the rendered inner fragment carries the negation
  marker. On the satisfiable cases the result is exactly the inner fragment as
  produced by the shared renderer, with the negation marker prepended iff the
  predicate is negated.

Result text is modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``. The
shared sub-selection renderer is an axiomatized callee that either returns a
non-empty fragment or signals the matches-nothing condition according to whether
the inner selection is satisfiable; its satisfiable-case content is named by a
``@Pure`` companion so the result content can be pinned to what the renderer
actually produces.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

class EmptyResultSet(Exception):
    """The "matches-nothing" signal. User-defined stand-in (a builtin exception
    in an ``Exsures`` crashes the Nagini translator; mapping.md §2). It is the
    signal the shared sub-selection renderer raises for an unsatisfiable inner
    selection, and the signal the predicate renderer propagates on the
    non-negated unsatisfiable case.
    """
    pass

# axioms-start
@Pure
@ContractOnly
def inner_fragment(satisfiable: int) -> PSeq[int]:
    """The CONTENT of the fragment the shared sub-selection renderer produces for
    a satisfiable inner selection (the @Pure companion of ``render_inner``).
    Naming the content as a pure function of the input lets the predicate
    renderer's postcondition pin the satisfiable result to what the renderer
    actually produces (directive 8: ground the result in the modeled renderer's
    output, never an echoable constant). Weakest properties the proof needs:
    non-empty, and it does not itself begin with the negation marker (so the
    marker is observable only when the predicate renderer prepends it)."""
    Requires(satisfiable == 1)
    Ensures(len(Result()) > 0)
    Ensures(Result().take(len(not_prefix())) != not_prefix())

@ContractOnly
def render_inner(satisfiable: int) -> List[int]:
    """The shared, UNCHANGED sub-selection renderer (the predicate's super-class
    rendering of its inner selection). Weakest contract the proof needs: it
    signals the matches-nothing condition exactly when the inner selection is
    unsatisfiable (``satisfiable == 0``); otherwise it returns, with full
    ownership, the fragment whose content is ``inner_fragment(satisfiable)``. It
    is the callee the predicate renderer invokes and does NOT change. Provenance +
    executable soundness: mapping.md / axiom_check.py (A-consumed)."""
    Requires(satisfiable == 0 or satisfiable == 1)
    Ensures(satisfiable == 1)
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
    Exsures(EmptyResultSet, satisfiable == 0)
# axioms-end

# pure-start
@Pure
def not_prefix() -> PSeq[int]:
    # 'NOT ' — the negation marker prepended to a rendered predicate fragment.
    return PSeq(78, 79, 84, 32)
# pure-end

def render_exists(satisfiable: int, negated: int) -> List[int]:
    # pre-conditions-start
    Requires(satisfiable == 0 or satisfiable == 1)
    Requires(negated == 0 or negated == 1)
    # pre-conditions-end
    # post-conditions-start
    # The matches-nothing signal is observable ONLY on the non-negated
    # unsatisfiable case; every other case returns normally. In particular the
    # negated unsatisfiable case returns normally rather than propagating the
    # signal, and its result is the EMPTY fragment: an empty fragment contributes
    # no restriction, so the surrounding condition holds for every row (the
    # negation of "exists no row of an empty selection"). Pinning the empty
    # fragment is what makes that row-set observable behaviour discriminating —
    # a non-empty fragment on this case would impose a spurious restriction and
    # change the observed rows.
    Ensures(not (satisfiable == 0 and negated == 0))
    Ensures(Acc(list_pred(Result())))
    Ensures(Implies(satisfiable == 0 and negated == 1, len(Result()) == 0))
    # Satisfiable cases: the result is exactly the inner fragment the shared
    # renderer produced, with the negation marker prepended iff negated. Pinned to
    # the renderer's actual output content (directive 8: grounded, not echoable):
    Ensures(Implies(satisfiable == 1 and negated == 0,
                    ToSeq(Result()) == inner_fragment(satisfiable)))
    Ensures(Implies(satisfiable == 1 and negated == 1,
                    ToSeq(Result()) == not_prefix() + inner_fragment(satisfiable)))
    # Non-negated unsatisfiable: the matches-nothing signal is propagated.
    Exsures(EmptyResultSet, satisfiable == 0 and negated == 0)
    # post-conditions-end
    # impl-start
    try:
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
    return sql
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of django__django-15382 nagini bundle. Focus on A-legs + model<->patch correspondence (R/I legs mechanically covered by G-CONF).

SPEC STRENGTH: render_exists(satisfiable, negated) has a finite 4-point abstract domain (satisfiable,negated in {0,1}), and the spec PINS every point exactly to gold behaviour, leaving no observable slack:
  * sat=1,neg=0 -> ToSeq(Result()) == inner_fragment(satisfiable)  (exact content, grounded in the modeled renderer output)
  * sat=1,neg=1 -> ToSeq(Result()) == not_prefix() + inner_fragment(satisfiable)
  * sat=0,neg=1 -> returns normally AND len(Result())==0 (empty fragment; <-> gold `return '', ()`)
  * sat=0,neg=0 -> Exsures(EmptyResultSet); plus not(sat==0 and neg==0) reachability excludes the signal everywhere else.

REFINEMENT.md AUDIT: all legs are R / A-consumed / I -- section C explicitly claims no kind-3 and no A-reference, which holds: the changed op (catch EmptyResultSet on negated path + return empty) is modeled DIRECTLY as try/except control flow in render_exists (A3-A5), not hidden behind an axiom. The one axiomatized callee render_inner (+ its @Pure companion inner_fragment) is A-consumed and corresponds to the UNCHANGED super-class Subquery.as_sql (mapping.md 3.1); its soundness is executable via axiom_check.py (G-AX) and G-CONF re-drives the real patched Exists.as_sql over >=1e5 inputs across all four combos. The A-legs' correspondence to the real callees holds.

atk_1 (prepatch bug: unguarded render_inner) -> weakness exit 2, does-not-verify: EmptyResultSet escapes on sat=0,neg=1, fails Exsures. PREPATCH REPRODUCED (matches model_prepatch.py rationale in refinement.md).
atk_2 (partial-domain: return [] for all unsat, never raise) -> exit 2: fails required raise on sat=0,neg=0 (Exsures / not(sat0&neg0)).
atk_3 (ungrounded-oracle echo: fabricate [88]/NOT+[88]) -> exit 2: fails ToSeq==inner_fragment on satisfiable cases; the directive-8 grounding clause rejects fabricated constants.
atk_4 (boundary: non-empty [48]='0' on sat=0,neg=1) -> exit 2: fails len(Result())==0 clause -- the pin that stops a spurious-restriction always-false/junk fragment that would not resolve.
atk_5 (control-flow-effect: prefix NOT on wrong polarity neg==0) -> exit 2: fails both satisfiable postconditions.
atk_6 (control-flow-effect: drop NOT prefix entirely) -> exit 2: fails sat=1,neg=1 (missing not_prefix).
atk_7 (legit echo-reconstruct: rebuild inner_fragment element-wise into fresh List) -> exit 2: proof-gap on my own Assert(ToSeq(sql)==inner_fragment) (loop invariant not strong enough to prove element equality); NOT a spec weakness -- behaviourally identical to gold and would resolve if provable, so not a counterexample either way.
atk_8 (case-swap: prepend NOT on all satisfiable incl neg==0) -> exit 2: fails sat=1,neg=0 (ToSeq==inner_fragment).

NO CANDIDATE: not one same-spec attack verified, so there is no verifying wrong-impl whose faithful refined patch needed materializing + run_resolve. Positive control (bundle model.py verbatim) VERIFIES (Nagini, 10.58s). The spec pins every point of the finite domain to the exact resolving behaviour; verify==>correct holds on the tested inputs. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15382.

Behaviour under specification (an abstract behavioural contract over the result,
NOT an edit or a diagnosis):

  A negatable existence predicate over an inner sub-selection is rendered to a
  fragment of result text. Rendering the inner sub-selection is delegated to a
  shared (unchanged) sub-selection renderer, which has two outcomes: for a
  SATISFIABLE inner selection it yields a non-empty inner fragment; for an
  UNSATISFIABLE one it signals the "matches-nothing" condition.

  The predicate also carries a negation flag. The result of rendering the
  predicate, by case, is:

    * inner selection satisfiable, not negated  -> the inner fragment;
    * inner selection satisfiable, negated      -> the inner fragment with the
                                                    negation marker prepended;
    * inner selection unsatisfiable, negated     -> a result that, in the
                                                    surrounding condition, holds
                                                    for every row (the negation
                                                    of "exists no row of an empty
                                                    selection");
    * inner selection unsatisfiable, not negated -> the matches-nothing condition
                                                    (an existence test over an
                                                    empty selection never holds).

  The behaviour the surrounding condition observes is whether the predicate
  reduces to "matches every row" or to the matches-nothing condition, and (on the
  satisfiable cases) whether the rendered inner fragment carries the negation
  marker. On the satisfiable cases the result is exactly the inner fragment as
  produced by the shared renderer, with the negation marker prepended iff the
  predicate is negated.

Result text is modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``. The
shared sub-selection renderer is an axiomatized callee that either returns a
non-empty fragment or signals the matches-nothing condition according to whether
the inner selection is satisfiable; its satisfiable-case content is named by a
``@Pure`` companion so the result content can be pinned to what the renderer
actually produces.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

class EmptyResultSet(Exception):
    """The "matches-nothing" signal. User-defined stand-in (a builtin exception
    in an ``Exsures`` crashes the Nagini translator; mapping.md §2). It is the
    signal the shared sub-selection renderer raises for an unsatisfiable inner
    selection, and the signal the predicate renderer propagates on the
    non-negated unsatisfiable case.
    """
    pass

# axioms-start
@Pure
@ContractOnly
def inner_fragment(satisfiable: int) -> PSeq[int]:
    """The CONTENT of the fragment the shared sub-selection renderer produces for
    a satisfiable inner selection (the @Pure companion of ``render_inner``).
    Naming the content as a pure function of the input lets the predicate
    renderer's postcondition pin the satisfiable result to what the renderer
    actually produces (directive 8: ground the result in the modeled renderer's
    output, never an echoable constant). Weakest properties the proof needs:
    non-empty, and it does not itself begin with the negation marker (so the
    marker is observable only when the predicate renderer prepends it)."""
    Requires(satisfiable == 1)
    Ensures(len(Result()) > 0)
    Ensures(Result().take(len(not_prefix())) != not_prefix())

@ContractOnly
def render_inner(satisfiable: int) -> List[int]:
    """The shared, UNCHANGED sub-selection renderer (the predicate's super-class
    rendering of its inner selection). Weakest contract the proof needs: it
    signals the matches-nothing condition exactly when the inner selection is
    unsatisfiable (``satisfiable == 0``); otherwise it returns, with full
    ownership, the fragment whose content is ``inner_fragment(satisfiable)``. It
    is the callee the predicate renderer invokes and does NOT change. Provenance +
    executable soundness: mapping.md / axiom_check.py (A-consumed)."""
    Requires(satisfiable == 0 or satisfiable == 1)
    Ensures(satisfiable == 1)
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
    Exsures(EmptyResultSet, satisfiable == 0)
# axioms-end

# pure-start
@Pure
def not_prefix() -> PSeq[int]:
    # 'NOT ' — the negation marker prepended to a rendered predicate fragment.
    return PSeq(78, 79, 84, 32)
# pure-end

def render_exists(satisfiable: int, negated: int) -> List[int]:
    # pre-conditions-start
    Requires(satisfiable == 0 or satisfiable == 1)
    Requires(negated == 0 or negated == 1)
    # pre-conditions-end
    # post-conditions-start
    # The matches-nothing signal is observable ONLY on the non-negated
    # unsatisfiable case; every other case returns normally. In particular the
    # negated unsatisfiable case returns normally rather than propagating the
    # signal, and its result is the EMPTY fragment: an empty fragment contributes
    # no restriction, so the surrounding condition holds for every row (the
    # negation of "exists no row of an empty selection"). Pinning the empty
    # fragment is what makes that row-set observable behaviour discriminating —
    # a non-empty fragment on this case would impose a spurious restriction and
    # change the observed rows.
    Ensures(not (satisfiable == 0 and negated == 0))
    Ensures(Acc(list_pred(Result())))
    Ensures(Implies(satisfiable == 0 and negated == 1, len(Result()) == 0))
    # Satisfiable cases: the result is exactly the inner fragment the shared
    # renderer produced, with the negation marker prepended iff negated. Pinned to
    # the renderer's actual output content (directive 8: grounded, not echoable):
    Ensures(Implies(satisfiable == 1 and negated == 0,
                    ToSeq(Result()) == inner_fragment(satisfiable)))
    Ensures(Implies(satisfiable == 1 and negated == 1,
                    ToSeq(Result()) == not_prefix() + inner_fragment(satisfiable)))
    # Non-negated unsatisfiable: the matches-nothing signal is propagated.
    Exsures(EmptyResultSet, satisfiable == 0 and negated == 0)
    # post-conditions-end
    # impl-start
    try:
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
    return sql
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of django__django-15382 nagini bundle. Focus on A-legs + model<->patch correspondence (R/I legs mechanically covered by G-CONF).

SPEC STRENGTH: render_exists(satisfiable, negated) has a finite 4-point abstract domain (satisfiable,negated in {0,1}), and the spec PINS every point exactly to gold behaviour, leaving no observable slack:
  * sat=1,neg=0 -> ToSeq(Result()) == inner_fragment(satisfiable)  (exact content, grounded in the modeled renderer output)
  * sat=1,neg=1 -> ToSeq(Result()) == not_prefix() + inner_fragment(satisfiable)
  * sat=0,neg=1 -> returns normally AND len(Result())==0 (empty fragment; <-> gold `return '', ()`)
  * sat=0,neg=0 -> Exsures(EmptyResultSet); plus not(sat==0 and neg==0) reachability excludes the signal everywhere else.

REFINEMENT.md AUDIT: all legs are R / A-consumed / I -- section C explicitly claims no kind-3 and no A-reference, which holds: the changed op (catch EmptyResultSet on negated path + return empty) is modeled DIRECTLY as try/except control flow in render_exists (A3-A5), not hidden behind an axiom. The one axiomatized callee render_inner (+ its @Pure companion inner_fragment) is A-consumed and corresponds to the UNCHANGED super-class Subquery.as_sql (mapping.md 3.1); its soundness is executable via axiom_check.py (G-AX) and G-CONF re-drives the real patched Exists.as_sql over >=1e5 inputs across all four combos. The A-legs' correspondence to the real callees holds.

atk_1 (prepatch bug: unguarded render_inner) -> weakness exit 2, does-not-verify: EmptyResultSet escapes on sat=0,neg=1, fails Exsures. PREPATCH REPRODUCED (matches model_prepatch.py rationale in refinement.md).
atk_2 (partial-domain: return [] for all unsat, never raise) -> exit 2: fails required raise on sat=0,neg=0 (Exsures / not(sat0&neg0)).
atk_3 (ungrounded-oracle echo: fabricate [88]/NOT+[88]) -> exit 2: fails ToSeq==inner_fragment on satisfiable cases; the directive-8 grounding clause rejects fabricated constants.
atk_4 (boundary: non-empty [48]='0' on sat=0,neg=1) -> exit 2: fails len(Result())==0 clause -- the pin that stops a spurious-restriction always-false/junk fragment that would not resolve.
atk_5 (control-flow-effect: prefix NOT on wrong polarity neg==0) -> exit 2: fails both satisfiable postconditions.
atk_6 (control-flow-effect: drop NOT prefix entirely) -> exit 2: fails sat=1,neg=1 (missing not_prefix).
atk_7 (legit echo-reconstruct: rebuild inner_fragment element-wise into fresh List) -> exit 2: proof-gap on my own Assert(ToSeq(sql)==inner_fragment) (loop invariant not strong enough to prove element equality); NOT a spec weakness -- behaviourally identical to gold and would resolve if provable, so not a counterexample either way.
atk_8 (case-swap: prepend NOT on all satisfiable incl neg==0) -> exit 2: fails sat=1,neg=0 (ToSeq==inner_fragment).

NO CANDIDATE: not one same-spec attack verified, so there is no verifying wrong-impl whose faithful refined patch needed materializing + run_resolve. Positive control (bundle model.py verbatim) VERIFIES (Nagini, 10.58s). The spec pins every point of the finite domain to the exact resolving behaviour; verify==>correct holds on the tested inputs. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-15382 nagini bundle. Modeled function render_exists(satisfiable, negated), domain satisfiable,negated in {0,1} — a finite 4-point domain. Real callee = gold-patched Exists.as_sql (django/db/models/expressions.py:1212).

Ground-truth verification:
1. Built worktree at base_commit 770d3e6a4ce8... and applied the exact gold patch (try/except EmptyResultSet + `if self.negated: return '', ()` + `NOT {}`.format). git apply clean; hunk matches patch.diff/refinement.md verbatim.
2. Directly probed the REAL gold-patched Exists.as_sql on all 4 (satisfiable,negated) points via a fresh in-memory Django (sqlite, auth.User):
   - sat=1,neg=0 -> returns 'EXISTS(SELECT (1) AS "a" FROM "auth_user" LIMIT 1)' (non-empty, no NOT prefix)
   - sat=1,neg=1 -> returns 'NOT EXISTS(...)' (NOT prefixed)
   - sat=0,neg=0 -> RAISES EmptyResultSet
   - sat=0,neg=1 -> returns '' (empty fragment, len 0)
3. These match the spec postconditions exactly: Exsures(EmptyResultSet) only on sat0neg0; not(sat0&neg0) reachability; len(Result())==0 on sat0neg1; ToSeq(Result())==inner_fragment(satisfiable) on sat1neg0; ==not_prefix()+inner_fragment(satisfiable) on sat1neg1. Inner fragment content is genuinely independent of the negation flag (both satisfiable cases render identical EXISTS(...) content), so pinning both to inner_fragment(satisfiable) is faithful, not spec-too-strong.
4. Ran the bundle's own conformance_check.py with: G-CONF OK, 100128 differential checks (boundary pool cross-product + 25000 fuzz trials x 4 combos, seed 15382), ZERO disagreements between the contract-stripped shadow impl and the real patched Exists.as_sql.

The input domain is finite and fully enumerated; the modeled function agrees with the real callee at every one of the 4 abstract points (and across 100k concrete queryset instantiations). No input exists where the spec disagrees with real repo behavior. The spec is neither too strong nor drifted. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py projected, impl elided to '...') screened for gold-edit leakage against the PUBLIC problem_statement only (not hints_text). Findings:

1) Mechanical G-LEAK screen passes (0 hard failures); recorded meta status = pass, not relaxed. Confirmed independently via leakage.screen().

2) No gold-diff line reproduced, no diff markers, no patched file path/module. The gold hunk (try: super().as_sql(...) except EmptyResultSet: if self.negated: return '', ()) is nowhere present in the spec view.

3) Distinctive changed repo symbols = {'invert'} (from the def __invert__ hunk header). 'invert' does not appear anywhere in the spec view. Repo bindings (Exists, Subquery.as_sql, self.negated, expressions.py, NothingNode) live ONLY in the audit-only mapping.md / refinement.md, which are NOT part of the consumer spec view.

4) 'EmptyResultSet' is named in the spec view but appears VERBATIM in the public problem_statement (>>> print(qs.query) -> EmptyResultSet), so it is already public and not a leak.

5) No bug/fix/patch/pre-patch narration in spec-view comments; comments describe target behavior by case, not the edit or the pre-patch defect.

6) Gold-reconstruction test: the spec states the correct four-case behavior in fully abstracted terms (negatable existence predicate, shared sub-selection renderer, inner fragment, List[int]/PSeq[int] code-point carrier). Describing target behavior is precisely what a spec is; it supplies none of the concrete repo bindings (file/function/try-except/return '', ()) required to reconstruct the gold patch. The negated-unsatisfiable -> empty always-true clause is exactly the behavior entailed by the PUBLIC symptom ('filter on ~Exists(empty queryset) removes whole WHERE block'), not information beyond the problem_statement.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
