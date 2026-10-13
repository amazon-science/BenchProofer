# P2 adversarial audit — matplotlib__matplotlib-22719

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -58,7 +57,6 @@
     sequence whose per-element numeric classification is given by *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -78,7 +76,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(every == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -87,7 +84,7 @@
             every = False
         i = i - 1
     Assert(ToSeq(flags).drop(i) == ToSeq(flags))
-    return len(flags) > 0 and every
+    return every
     # impl-end
 
 
@@ -97,7 +94,6 @@
     *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -117,7 +113,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(classify == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -58,7 +57,6 @@
     sequence whose per-element numeric classification is given by *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -78,7 +76,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(every == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -87,7 +84,7 @@
             every = False
         i = i - 1
     Assert(ToSeq(flags).drop(i) == ToSeq(flags))
-    return len(flags) > 0 and every
+    return len(flags) > 1 and every
     # impl-end
 
 
@@ -97,7 +94,6 @@
     *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -117,7 +113,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(classify == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -58,7 +57,6 @@
     sequence whose per-element numeric classification is given by *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -78,7 +76,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(every == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -87,7 +84,7 @@
             every = False
         i = i - 1
     Assert(ToSeq(flags).drop(i) == ToSeq(flags))
-    return len(flags) > 0 and every
+    return len(flags) > 0
     # impl-end
 
 
@@ -97,7 +94,6 @@
     *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -117,7 +113,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(classify == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -58,7 +57,6 @@
     sequence whose per-element numeric classification is given by *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -78,7 +76,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(every == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -97,7 +94,6 @@
     *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -117,7 +113,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(classify == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -126,5 +121,5 @@
             classify = False
         i = i - 1
     Assert(ToSeq(flags).drop(i) == ToSeq(flags))
-    return len(flags) > 0 and classify
+    return classify
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -58,7 +57,6 @@
     sequence whose per-element numeric classification is given by *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -78,7 +76,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(every == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -87,7 +84,7 @@
             every = False
         i = i - 1
     Assert(ToSeq(flags).drop(i) == ToSeq(flags))
-    return len(flags) > 0 and every
+    return len(flags) >= 1 and every
     # impl-end
 
 
@@ -97,7 +94,6 @@
     *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -117,7 +113,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(classify == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -58,7 +57,6 @@
     sequence whose per-element numeric classification is given by *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -78,7 +76,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(every == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -97,7 +94,6 @@
     *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -117,7 +113,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(classify == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -126,5 +121,5 @@
             classify = False
         i = i - 1
     Assert(ToSeq(flags).drop(i) == ToSeq(flags))
-    return len(flags) > 0 and classify
+    return classify and len(flags) > 0
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -58,7 +57,6 @@
     sequence whose per-element numeric classification is given by *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -78,7 +76,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(every == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -97,7 +94,6 @@
     *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -117,7 +113,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(classify == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
@@ -126,5 +121,5 @@
             classify = False
         i = i - 1
     Assert(ToSeq(flags).drop(i) == ToSeq(flags))
-    return len(flags) > 0 and classify
+    return len(flags) > 0 or classify
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -58,7 +57,6 @@
     sequence whose per-element numeric classification is given by *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -78,12 +76,11 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(every == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
         Assert(ToSeq(flags).drop(i - 1).drop(1) == ToSeq(flags).drop(i))
-        if c == 0:
+        if c != 0:
             every = False
         i = i - 1
     Assert(ToSeq(flags).drop(i) == ToSeq(flags))
@@ -97,7 +94,6 @@
     *flags*."""
     # pre-conditions-start
     Requires(Acc(list_pred(flags), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -117,7 +113,6 @@
         Invariant(Acc(list_pred(flags), 1 / 2))
         Invariant(0 <= i and i <= len(flags))
         Invariant(classify == all_classify(ToSeq(flags).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = flags[i - 1]
         Assert(ToSeq(flags).drop(i - 1)[0] == c)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-22719.

Behaviour under specification (stated as desired behaviour, not as an edit):

The categorical-unit machinery inspects a sequence of incoming values and,
when *every* value satisfies a per-element classification, emits an advisory
message:

  (1) When converting a sequence whose every element classifies as a bare
      number (numeric and not a string/bytes object), a deprecation advisory
      about numeric pass-through is emitted. The advisory MUST be emitted only
      when the sequence is non-empty: an empty sequence carries no numeric
      value to advise about, so it produces NO advisory — even though "every
      element classifies as a number" is vacuously satisfied by an empty
      sequence.

  (2) When registering a sequence of category labels whose every element is a
      string parsable as a float or a date, an informational advisory about
      categorical-vs-numeric plotting is emitted. Likewise it MUST be emitted
      only for a non-empty sequence: an empty sequence yields NO advisory, even
      though the "all parsable" condition is vacuously satisfied when empty.

In both cases the decision is exactly ``non-empty(sequence) AND all-elements-
classify``. The universally-quantified "all elements classify" predicate is
vacuously true on the empty sequence, so the non-emptiness conjunct is what
suppresses the spurious advisory on empty input.

A value sequence is modelled as ``List[int]`` of per-element classification
flags (0 == the element does NOT satisfy the per-element predicate; non-zero ==
it does). The per-element predicate is the real, unchanged classifier
(numeric-and-not-text in (1); string-parsable-as-float-or-date in (2)); its
result for each element is the modelled flag. The whole-sequence "all classify"
property is spelled out deeply as a front-recursive fold (`all_classify`) so a
single unfold is available per loop step. The decision functions return whether
the advisory is emitted.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# pure-start
@Pure
def all_classify(s: PSeq[int]) -> bool:
    """Whether EVERY element of *s* satisfies the per-element classification
    (its flag is non-zero). The empty sequence satisfies this vacuously
    (`True`). Front-recursive so one unfold is available to callers."""
    if len(s) == 0:
        return True
    return (s[0] != 0) and all_classify(s.drop(1))
# pure-end


def should_warn_numeric_passthrough(flags: List[int]) -> bool:
    """Decide whether the numeric-pass-through advisory is emitted for a value
    sequence whose per-element numeric classification is given by *flags*."""
    # pre-conditions-start
    Requires(Acc(list_pred(flags), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    # The advisory fires iff the sequence is non-empty AND every element
    # classifies. The non-emptiness conjunct is what suppresses the advisory
    # on the empty sequence (where all_classify is vacuously True).
    Ensures(Result() == (len(flags) > 0 and all_classify(ToSeq(flags))))
    # An empty sequence NEVER triggers the advisory, regardless of the
    # (vacuous) classification verdict.
    Ensures(Implies(len(flags) == 0, not Result()))
    # post-conditions-end
    # impl-start
    every = True
    i = len(flags)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(flags), 1 / 2))
        Invariant(0 <= i and i <= len(flags))
        Invariant(every == all_classify(ToSeq(flags).drop(i)))
        # invariants-end
        c = flags[i - 1]
        Assert(ToSeq(flags).drop(i - 1)[0] == c)
        Assert(ToSeq(flags).drop(i - 1).drop(1) == ToSeq(flags).drop(i))
        if c == 0:
            every = False
        i = i - 1
    Assert(ToSeq(flags).drop(i) == ToSeq(flags))
    return len(flags) > 0 and every
    # impl-end


def should_log_numeric_strings(flags: List[int]) -> bool:
    """Decide whether the all-parsable-as-numbers informational advisory is
    emitted for a label sequence whose per-element parsability is given by
    *flags*."""
    # pre-conditions-start
    Requires(Acc(list_pred(flags), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    # The advisory fires iff the sequence is non-empty AND every element
    # classifies. The non-emptiness conjunct suppresses the advisory on the
    # empty sequence (where all_classify is vacuously True).
    Ensures(Result() == (len(flags) > 0 and all_classify(ToSeq(flags))))
    # An empty sequence NEVER triggers the advisory, regardless of the
    # (vacuous) classification verdict.
    Ensures(Implies(len(flags) == 0, not Result()))
    # post-conditions-end
    # impl-start
    classify = True
    i = len(flags)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(flags), 1 / 2))
        Invariant(0 <= i and i <= len(flags))
        Invariant(classify == all_classify(ToSeq(flags).drop(i)))
        # invariants-end
        c = flags[i - 1]
        Assert(ToSeq(flags).drop(i - 1)[0] == c)
        Assert(ToSeq(flags).drop(i - 1).drop(1) == ToSeq(flags).drop(i))
        if c == 0:
            classify = False
        i = i - 1
    Assert(ToSeq(flags).drop(i) == ToSeq(flags))
    return len(flags) > 0 and classify
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND for matplotlib__matplotlib-22719 (nagini). Spec fully pins output: Result() == (len(flags) > 0 and all_classify(ToSeq(flags))) at both decision functions, plus Implies(len==0, not Result()). Positive control (bundle model.py copy) VERIFIES (nagini_verify.sh exit 0, 10.6s).

ATTACKS (all built by copying bundle model.py, editing ONLY impl region; run: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-22719 <path>`):
- atk_1.py: site-1 (should_warn_numeric_passthrough) returns `every` (drops len>0 guard) = PREPATCH BUG site 1. weakness exit 2 -> NOT-A-COUNTEREXAMPLE (verification failed): spec rejects it. PREPATCH REPRODUCED.
- atk_2.py: site-1 returns `len(flags) > 1 and every` (boundary off-by-one). exit 2, verify fails.
- atk_3.py: site-1 returns `len(flags) > 0` alone (drops classify conjunct). exit 2, verify fails.
- atk_4.py: site-2 (should_log_numeric_strings) returns `classify` (drops len guard) = prepatch bug site 2. exit 2, verify fails.
- atk_7.py: site-2 returns `len(flags) > 0 OR classify` (control-flow: and->or). exit 2, verify fails.
- atk_8.py: site-1 inverted classifier update `if c != 0: every=False` (ungrounded control-flow effect). exit 2, verify fails.
- atk_5.py: site-1 returns `len(flags) >= 1 and every` (semantic echo of >0). weakness exit 0 -> CANDIDATE (shares spec AND verifies, 11.8s). Faithful refined patch materialized (patch_atk_5.diff: convert guard `values.size >= 1 and is_numlike`, update site gold). run_resolve('matplotlib__matplotlib-22719') => RESOLVED=True, COMPLETED=True. Patch applied cleanly in container.
- atk_6.py: site-2 returns `classify and len(flags) > 0` (reordered conjunction, semantic echo). weakness exit 0 -> CANDIDATE (verifies, 11.4s). Faithful refined patch (patch_atk_6.diff: convert site gold, update guard `convertible and data.size`). run_resolve => RESOLVED=True, COMPLETED=True. Applied cleanly.

Both verifying candidates' faithful refined patches RESOLVE under the official harness -> NO verify-does-not-imply-correct break. Runner will re-run.)

REFINEMENT.MD AUDIT (A-leg focus): meta.json axioms=[] and NO @ContractOnly / IOOperation / Predicate in model.py -> zero consumed axioms, no dead axiom, no kind-3 (unexpressible-changed-op) leg. The only changed operation (the non-emptiness guard X.size and ...) is modeled DEEPLY as `len(flags) > 0 and ...` (legs A3/B3, tag R). The unchanged universal 'all classify' verdict is the single A-reference deep model `all_classify` (front-recursive @Pure fold), validated by axiom_check.py (G-AX): ran clean -- `all_classify == real all(...)/convertible left-fold` incl. vacuous truth all([])==True, size<->len bijection on np.atleast_1d(np.array(..,dtype=object)), and full patched decision == model Ensures over 9 boundary + 20000 fuzz cases (exit 0). A-legs correspond faithfully to the real callees (category.py:58-60 all(...); category.py:224-230 convertible fold; ndarray.size). R/I legs (per-element classifier flag abstraction A1/B1, ndarray.size<->len, boolean-and emit decision A4/B4) are G-CONF territory. All legs R / A-reference / I; no A-consumed row needed and none present.

VERDICT: SOUND. >=5 attacks run (8 total: 6 verify-rejected wrong impls incl. both prepatch bugs + 2 verifying echoes), both verifying candidates' materialized faithful patches RESOLVE. No same-spec verifying wrong impl breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-22719.

Behaviour under specification (stated as desired behaviour, not as an edit):

The categorical-unit machinery inspects a sequence of incoming values and,
when *every* value satisfies a per-element classification, emits an advisory
message:

  (1) When converting a sequence whose every element classifies as a bare
      number (numeric and not a string/bytes object), a deprecation advisory
      about numeric pass-through is emitted. The advisory MUST be emitted only
      when the sequence is non-empty: an empty sequence carries no numeric
      value to advise about, so it produces NO advisory — even though "every
      element classifies as a number" is vacuously satisfied by an empty
      sequence.

  (2) When registering a sequence of category labels whose every element is a
      string parsable as a float or a date, an informational advisory about
      categorical-vs-numeric plotting is emitted. Likewise it MUST be emitted
      only for a non-empty sequence: an empty sequence yields NO advisory, even
      though the "all parsable" condition is vacuously satisfied when empty.

In both cases the decision is exactly ``non-empty(sequence) AND all-elements-
classify``. The universally-quantified "all elements classify" predicate is
vacuously true on the empty sequence, so the non-emptiness conjunct is what
suppresses the spurious advisory on empty input.

A value sequence is modelled as ``List[int]`` of per-element classification
flags (0 == the element does NOT satisfy the per-element predicate; non-zero ==
it does). The per-element predicate is the real, unchanged classifier
(numeric-and-not-text in (1); string-parsable-as-float-or-date in (2)); its
result for each element is the modelled flag. The whole-sequence "all classify"
property is spelled out deeply as a front-recursive fold (`all_classify`) so a
single unfold is available per loop step. The decision functions return whether
the advisory is emitted.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# pure-start
@Pure
def all_classify(s: PSeq[int]) -> bool:
    """Whether EVERY element of *s* satisfies the per-element classification
    (its flag is non-zero). The empty sequence satisfies this vacuously
    (`True`). Front-recursive so one unfold is available to callers."""
    if len(s) == 0:
        return True
    return (s[0] != 0) and all_classify(s.drop(1))
# pure-end


def should_warn_numeric_passthrough(flags: List[int]) -> bool:
    """Decide whether the numeric-pass-through advisory is emitted for a value
    sequence whose per-element numeric classification is given by *flags*."""
    # pre-conditions-start
    Requires(Acc(list_pred(flags), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    # The advisory fires iff the sequence is non-empty AND every element
    # classifies. The non-emptiness conjunct is what suppresses the advisory
    # on the empty sequence (where all_classify is vacuously True).
    Ensures(Result() == (len(flags) > 0 and all_classify(ToSeq(flags))))
    # An empty sequence NEVER triggers the advisory, regardless of the
    # (vacuous) classification verdict.
    Ensures(Implies(len(flags) == 0, not Result()))
    # post-conditions-end
    # impl-start
    every = True
    i = len(flags)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(flags), 1 / 2))
        Invariant(0 <= i and i <= len(flags))
        Invariant(every == all_classify(ToSeq(flags).drop(i)))
        # invariants-end
        c = flags[i - 1]
        Assert(ToSeq(flags).drop(i - 1)[0] == c)
        Assert(ToSeq(flags).drop(i - 1).drop(1) == ToSeq(flags).drop(i))
        if c == 0:
            every = False
        i = i - 1
    Assert(ToSeq(flags).drop(i) == ToSeq(flags))
    return len(flags) > 0 and every
    # impl-end


def should_log_numeric_strings(flags: List[int]) -> bool:
    """Decide whether the all-parsable-as-numbers informational advisory is
    emitted for a label sequence whose per-element parsability is given by
    *flags*."""
    # pre-conditions-start
    Requires(Acc(list_pred(flags), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    # The advisory fires iff the sequence is non-empty AND every element
    # classifies. The non-emptiness conjunct suppresses the advisory on the
    # empty sequence (where all_classify is vacuously True).
    Ensures(Result() == (len(flags) > 0 and all_classify(ToSeq(flags))))
    # An empty sequence NEVER triggers the advisory, regardless of the
    # (vacuous) classification verdict.
    Ensures(Implies(len(flags) == 0, not Result()))
    # post-conditions-end
    # impl-start
    classify = True
    i = len(flags)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(flags), 1 / 2))
        Invariant(0 <= i and i <= len(flags))
        Invariant(classify == all_classify(ToSeq(flags).drop(i)))
        # invariants-end
        c = flags[i - 1]
        Assert(ToSeq(flags).drop(i - 1)[0] == c)
        Assert(ToSeq(flags).drop(i - 1).drop(1) == ToSeq(flags).drop(i))
        if c == 0:
            classify = False
        i = i - 1
    Assert(ToSeq(flags).drop(i) == ToSeq(flags))
    return len(flags) > 0 and classify
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND for matplotlib__matplotlib-22719 (nagini). Spec fully pins output: Result() == (len(flags) > 0 and all_classify(ToSeq(flags))) at both decision functions, plus Implies(len==0, not Result()). Positive control (bundle model.py copy) VERIFIES (nagini_verify.sh exit 0, 10.6s).

ATTACKS (all built by copying bundle model.py, editing ONLY impl region; run: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-22719 <path>`):
- atk_1.py: site-1 (should_warn_numeric_passthrough) returns `every` (drops len>0 guard) = PREPATCH BUG site 1. weakness exit 2 -> NOT-A-COUNTEREXAMPLE (verification failed): spec rejects it. PREPATCH REPRODUCED.
- atk_2.py: site-1 returns `len(flags) > 1 and every` (boundary off-by-one). exit 2, verify fails.
- atk_3.py: site-1 returns `len(flags) > 0` alone (drops classify conjunct). exit 2, verify fails.
- atk_4.py: site-2 (should_log_numeric_strings) returns `classify` (drops len guard) = prepatch bug site 2. exit 2, verify fails.
- atk_7.py: site-2 returns `len(flags) > 0 OR classify` (control-flow: and->or). exit 2, verify fails.
- atk_8.py: site-1 inverted classifier update `if c != 0: every=False` (ungrounded control-flow effect). exit 2, verify fails.
- atk_5.py: site-1 returns `len(flags) >= 1 and every` (semantic echo of >0). weakness exit 0 -> CANDIDATE (shares spec AND verifies, 11.8s). Faithful refined patch materialized (patch_atk_5.diff: convert guard `values.size >= 1 and is_numlike`, update site gold). run_resolve('matplotlib__matplotlib-22719') => RESOLVED=True, COMPLETED=True. Patch applied cleanly in container.
- atk_6.py: site-2 returns `classify and len(flags) > 0` (reordered conjunction, semantic echo). weakness exit 0 -> CANDIDATE (verifies, 11.4s). Faithful refined patch (patch_atk_6.diff: convert site gold, update guard `convertible and data.size`). run_resolve => RESOLVED=True, COMPLETED=True. Applied cleanly.

Both verifying candidates' faithful refined patches RESOLVE under the official harness -> NO verify-does-not-imply-correct break. Runner will re-run.)

REFINEMENT.MD AUDIT (A-leg focus): meta.json axioms=[] and NO @ContractOnly / IOOperation / Predicate in model.py -> zero consumed axioms, no dead axiom, no kind-3 (unexpressible-changed-op) leg. The only changed operation (the non-emptiness guard X.size and ...) is modeled DEEPLY as `len(flags) > 0 and ...` (legs A3/B3, tag R). The unchanged universal 'all classify' verdict is the single A-reference deep model `all_classify` (front-recursive @Pure fold), validated by axiom_check.py (G-AX): ran clean -- `all_classify == real all(...)/convertible left-fold` incl. vacuous truth all([])==True, size<->len bijection on np.atleast_1d(np.array(..,dtype=object)), and full patched decision == model Ensures over 9 boundary + 20000 fuzz cases (exit 0). A-legs correspond faithfully to the real callees (category.py:58-60 all(...); category.py:224-230 convertible fold; ndarray.size). R/I legs (per-element classifier flag abstraction A1/B1, ndarray.size<->len, boolean-and emit decision A4/B4) are G-CONF territory. All legs R / A-reference / I; no A-consumed row needed and none present.

VERDICT: SOUND. >=5 attacks run (8 total: 6 verify-rejected wrong impls incl. both prepatch bugs + 2 verifying echoes), both verifying candidates' materialized faithful patches RESOLVE. No same-spec verifying wrong impl breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break assessment for matplotlib__matplotlib-22719 (nagini). The bundle models two real callees: StrCategoryConverter.convert (decision `values.size and is_numlike`) and UnitData.update (decision `data.size and convertible`), both as should_*(flags) == (len(flags) > 0 and all_classify(flags)). Nagini verifies model.py (exit 0, 17.9s).

The only bridge that could break faithfulness is `values.size > 0 ↔ len(flags) > 0`, since numpy `.size` (product of shape) differs from Python-iteration count for multi-dimensional / zero-width arrays (e.g. `[[]]` iterates once but `.size == 0`; `[[],[]]` iterates twice, size 0). I probed exactly this class: in every such case the iterated sub-elements are empty arrays that FAIL the per-element classifier (is_numlike-and-not-text / _str_is_convertible), so all flags are 0 → model returns False, which matches the real code (real sees size==0 → advisory off). No divergence.

Evidence: (1) shipped axiom_check.py G-AX passes (9 boundary + 20000 fuzz); (2) shipped conformance_check.py G-CONF passes, 100042 inputs, 0 disagreements; (3) my INDEPENDENT differential fuzz against the REAL matplotlib callees — 20 exotic boundary inputs (nested arrays, numpy int64/float32/bool_/datetime64 scalars, memoryview, bytearray, complex, inf/nan, tuples, 0-d and empty ndarrays) + 30000 convert + 30000 update random cases with broad pools and an independent seed (999) — produced 0 divergences (one input raised inside the classifier, decided before the guard, not a spec disagreement).

The modeled decision functions agree with the real repo callees on every probed input, including the multi-dimensional-array edge that stresses the size↔len abstraction. The spec is not too strong and does not drift from real behavior. No diverging input exists; verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view projection of model.py: module docstring + signatures + Requires/Ensures + region markers; impl elided) does not leak the gold edit beyond the public problem_statement.

Gold edit: add non-emptiness guard to two if-conditions in lib/matplotlib/category.py — `if is_numlike:`->`if values.size and is_numlike:` (convert) and `if convertible:`->`if data.size and convertible:` (update) so empty data emits no advisory.

Already public in problem_statement (not hints): the bug is a confusing deprecation warning triggered by EMPTY data on category-unit axes; expected outcome is no warning / 'continue producing artists with no data'; and the pasted traceback literally shows `category.py in convert`, line `61  if is_numlike:` calling `warn_deprecated`. So the file, the guarded condition, and the empty-input fix intent are all solver-visible.

Spec view content is an ABSTRACT behavioral postcondition over List[int] flags: Result() == (len(flags) > 0 and all_classify(ToSeq(flags))) plus Implies(len==0, not Result()). This encodes exactly the publicly-stated desired behavior (empty -> no advisory) and localizes nothing beyond it.

Mechanical screen leakage.screen() PASSES (hard_failures empty): no diff markers; no gold-patch changed line reproduced (the discriminating tokens `values.size`/`data.size`/`is_numlike`/`convertible` never appear in the spec view — it uses len(flags)>0 and all_classify); patched path category.py / dotted module not present; no spec-view identifier or comment names a patched repo symbol (convert/update/is_numlike/convertible); no narration keywords (bug/fix/patch/previously/wrong/broken/etc.).

The leak-relevant repo specifics (values.size, is_numlike, category.py:61, StrCategoryConverter.convert, UnitData.update) live ONLY in refinement.md/mapping.md, which are auditor artifacts NOT part of the consumer spec view G-PANEL-3/G-LEAK judges. Bundle has no patch.diff file; patch_diff sourced from frozen row. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
