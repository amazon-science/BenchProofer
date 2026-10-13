# P2 adversarial audit — django__django-14311

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
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(parent), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -93,9 +91,9 @@
                     ToSeq(Result()) == ToSeq(parent)))
     # post-conditions-end
     # impl-start
-    sentinel = marks_entry(ToSeq(name))
+    # PREPATCH bug: use enclosing package unconditionally when non-empty.
     result = []  # type: List[int]
-    if sentinel and len(parent) > 0:
+    if len(parent) > 0:
         i = 0
         while i < len(parent):
             # invariants-start
@@ -104,14 +102,11 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(parent))
             Invariant(len(parent) > 0)
-            Invariant(marks_entry(ToSeq(name)))
             Invariant(ToSeq(result) == ToSeq(parent).take(i))
-            Invariant(MustTerminate(len(parent) - i + 1))
             # invariants-end
             result = result + [parent[i]]
             i = i + 1
         Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
     else:
         i = 0
         while i < len(name):
@@ -120,13 +115,10 @@
             Invariant(Acc(list_pred(parent), 1 / 4))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(name))
-            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
             Invariant(ToSeq(result) == ToSeq(name).take(i))
-            Invariant(MustTerminate(len(name) - i + 1))
             # invariants-end
             result = result + [name[i]]
             i = i + 1
         Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(parent), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -93,40 +91,20 @@
                     ToSeq(Result()) == ToSeq(parent)))
     # post-conditions-end
     # impl-start
-    sentinel = marks_entry(ToSeq(name))
+    # Partial-domain wrong: always reproduce the qualified name, never the
+    # parent package -- wrong on package-entry inputs.
     result = []  # type: List[int]
-    if sentinel and len(parent) > 0:
-        i = 0
-        while i < len(parent):
-            # invariants-start
-            Invariant(Acc(list_pred(parent), 1 / 4))
-            Invariant(Acc(list_pred(name), 1 / 4))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(parent))
-            Invariant(len(parent) > 0)
-            Invariant(marks_entry(ToSeq(name)))
-            Invariant(ToSeq(result) == ToSeq(parent).take(i))
-            Invariant(MustTerminate(len(parent) - i + 1))
-            # invariants-end
-            result = result + [parent[i]]
-            i = i + 1
-        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
-    else:
-        i = 0
-        while i < len(name):
-            # invariants-start
-            Invariant(Acc(list_pred(name), 1 / 4))
-            Invariant(Acc(list_pred(parent), 1 / 4))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(name))
-            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
-            Invariant(ToSeq(result) == ToSeq(name).take(i))
-            Invariant(MustTerminate(len(name) - i + 1))
-            # invariants-end
-            result = result + [name[i]]
-            i = i + 1
-        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
+    i = 0
+    while i < len(name):
+        # invariants-start
+        Invariant(Acc(list_pred(name), 1 / 4))
+        Invariant(Acc(list_pred(parent), 1 / 4))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= i and i <= len(name))
+        Invariant(ToSeq(result) == ToSeq(name).take(i))
+        # invariants-end
+        result = result + [name[i]]
+        i = i + 1
+    Assert(ToSeq(name).take(len(name)) == ToSeq(name))
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(parent), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -93,9 +91,10 @@
                     ToSeq(Result()) == ToSeq(parent)))
     # post-conditions-end
     # impl-start
+    # Control-flow wrong: invert the classifier gate.
     sentinel = marks_entry(ToSeq(name))
     result = []  # type: List[int]
-    if sentinel and len(parent) > 0:
+    if (not sentinel) and len(parent) > 0:
         i = 0
         while i < len(parent):
             # invariants-start
@@ -104,14 +103,11 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(parent))
             Invariant(len(parent) > 0)
-            Invariant(marks_entry(ToSeq(name)))
             Invariant(ToSeq(result) == ToSeq(parent).take(i))
-            Invariant(MustTerminate(len(parent) - i + 1))
             # invariants-end
             result = result + [parent[i]]
             i = i + 1
         Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
     else:
         i = 0
         while i < len(name):
@@ -120,13 +116,10 @@
             Invariant(Acc(list_pred(parent), 1 / 4))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(name))
-            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
             Invariant(ToSeq(result) == ToSeq(name).take(i))
-            Invariant(MustTerminate(len(name) - i + 1))
             # invariants-end
             result = result + [name[i]]
             i = i + 1
         Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(parent), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -93,40 +91,18 @@
                     ToSeq(Result()) == ToSeq(parent)))
     # post-conditions-end
     # impl-start
-    sentinel = marks_entry(ToSeq(name))
+    # Boundary wrong: copy name but stop one element short.
     result = []  # type: List[int]
-    if sentinel and len(parent) > 0:
-        i = 0
-        while i < len(parent):
-            # invariants-start
-            Invariant(Acc(list_pred(parent), 1 / 4))
-            Invariant(Acc(list_pred(name), 1 / 4))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(parent))
-            Invariant(len(parent) > 0)
-            Invariant(marks_entry(ToSeq(name)))
-            Invariant(ToSeq(result) == ToSeq(parent).take(i))
-            Invariant(MustTerminate(len(parent) - i + 1))
-            # invariants-end
-            result = result + [parent[i]]
-            i = i + 1
-        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
-    else:
-        i = 0
-        while i < len(name):
-            # invariants-start
-            Invariant(Acc(list_pred(name), 1 / 4))
-            Invariant(Acc(list_pred(parent), 1 / 4))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(name))
-            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
-            Invariant(ToSeq(result) == ToSeq(name).take(i))
-            Invariant(MustTerminate(len(name) - i + 1))
-            # invariants-end
-            result = result + [name[i]]
-            i = i + 1
-        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
+    i = 0
+    while i < len(name) - 1:
+        # invariants-start
+        Invariant(Acc(list_pred(name), 1 / 4))
+        Invariant(Acc(list_pred(parent), 1 / 4))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= i and i <= len(name))
+        Invariant(ToSeq(result) == ToSeq(name).take(i))
+        # invariants-end
+        result = result + [name[i]]
+        i = i + 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(parent), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -93,6 +91,8 @@
                     ToSeq(Result()) == ToSeq(parent)))
     # post-conditions-end
     # impl-start
+    # Wrong: build the gold selection, then mutate result by appending an
+    # extra code point (a trailing 'x') so the value differs.
     sentinel = marks_entry(ToSeq(name))
     result = []  # type: List[int]
     if sentinel and len(parent) > 0:
@@ -106,12 +106,9 @@
             Invariant(len(parent) > 0)
             Invariant(marks_entry(ToSeq(name)))
             Invariant(ToSeq(result) == ToSeq(parent).take(i))
-            Invariant(MustTerminate(len(parent) - i + 1))
             # invariants-end
             result = result + [parent[i]]
             i = i + 1
-        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
     else:
         i = 0
         while i < len(name):
@@ -122,11 +119,9 @@
             Invariant(0 <= i and i <= len(name))
             Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
             Invariant(ToSeq(result) == ToSeq(name).take(i))
-            Invariant(MustTerminate(len(name) - i + 1))
             # invariants-end
             result = result + [name[i]]
             i = i + 1
-        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
+    result = result + [120]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(parent), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -93,40 +91,7 @@
                     ToSeq(Result()) == ToSeq(parent)))
     # post-conditions-end
     # impl-start
-    sentinel = marks_entry(ToSeq(name))
+    # Ungrounded/degenerate: always return the empty sequence.
     result = []  # type: List[int]
-    if sentinel and len(parent) > 0:
-        i = 0
-        while i < len(parent):
-            # invariants-start
-            Invariant(Acc(list_pred(parent), 1 / 4))
-            Invariant(Acc(list_pred(name), 1 / 4))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(parent))
-            Invariant(len(parent) > 0)
-            Invariant(marks_entry(ToSeq(name)))
-            Invariant(ToSeq(result) == ToSeq(parent).take(i))
-            Invariant(MustTerminate(len(parent) - i + 1))
-            # invariants-end
-            result = result + [parent[i]]
-            i = i + 1
-        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
-    else:
-        i = 0
-        while i < len(name):
-            # invariants-start
-            Invariant(Acc(list_pred(name), 1 / 4))
-            Invariant(Acc(list_pred(parent), 1 / 4))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(name))
-            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
-            Invariant(ToSeq(result) == ToSeq(name).take(i))
-            Invariant(MustTerminate(len(name) - i + 1))
-            # invariants-end
-            result = result + [name[i]]
-            i = i + 1
-        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(parent), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -93,9 +91,23 @@
                     ToSeq(Result()) == ToSeq(parent)))
     # post-conditions-end
     # impl-start
+    # Inverted selection: entry-package -> return NAME; non-entry w/ parent ->
+    # return PARENT. Exactly the wrong branch assignment.
     sentinel = marks_entry(ToSeq(name))
     result = []  # type: List[int]
     if sentinel and len(parent) > 0:
+        i = 0
+        while i < len(name):
+            # invariants-start
+            Invariant(Acc(list_pred(name), 1 / 4))
+            Invariant(Acc(list_pred(parent), 1 / 4))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= i and i <= len(name))
+            Invariant(ToSeq(result) == ToSeq(name).take(i))
+            # invariants-end
+            result = result + [name[i]]
+            i = i + 1
+    else:
         i = 0
         while i < len(parent):
             # invariants-start
@@ -103,30 +115,9 @@
             Invariant(Acc(list_pred(name), 1 / 4))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(parent))
-            Invariant(len(parent) > 0)
-            Invariant(marks_entry(ToSeq(name)))
             Invariant(ToSeq(result) == ToSeq(parent).take(i))
-            Invariant(MustTerminate(len(parent) - i + 1))
             # invariants-end
             result = result + [parent[i]]
             i = i + 1
-        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
-    else:
-        i = 0
-        while i < len(name):
-            # invariants-start
-            Invariant(Acc(list_pred(name), 1 / 4))
-            Invariant(Acc(list_pred(parent), 1 / 4))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(name))
-            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
-            Invariant(ToSeq(result) == ToSeq(name).take(i))
-            Invariant(MustTerminate(len(name) - i + 1))
-            # invariants-end
-            result = result + [name[i]]
-            i = i + 1
-        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(parent), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -93,9 +91,10 @@
                     ToSeq(Result()) == ToSeq(parent)))
     # post-conditions-end
     # impl-start
+    # Boundary wrong: on entry names, return parent even when parent is empty.
     sentinel = marks_entry(ToSeq(name))
     result = []  # type: List[int]
-    if sentinel and len(parent) > 0:
+    if sentinel:
         i = 0
         while i < len(parent):
             # invariants-start
@@ -103,15 +102,11 @@
             Invariant(Acc(list_pred(name), 1 / 4))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(parent))
-            Invariant(len(parent) > 0)
             Invariant(marks_entry(ToSeq(name)))
             Invariant(ToSeq(result) == ToSeq(parent).take(i))
-            Invariant(MustTerminate(len(parent) - i + 1))
             # invariants-end
             result = result + [parent[i]]
             i = i + 1
-        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
     else:
         i = 0
         while i < len(name):
@@ -120,13 +115,10 @@
             Invariant(Acc(list_pred(parent), 1 / 4))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(name))
-            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
+            Invariant(not marks_entry(ToSeq(name)))
             Invariant(ToSeq(result) == ToSeq(name).take(i))
-            Invariant(MustTerminate(len(name) - i + 1))
             # invariants-end
             result = result + [name[i]]
             i = i + 1
-        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14311.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a development process was launched by interpreting a module via the
  interpreter's module-execution mechanism, the relaunch command must name the
  SAME module that was originally run.  The launched unit is characterised by
  two code-point strings:

    * its fully-qualified import name ``name`` (e.g. ``pkg.sub.tool``);
    * its enclosing package name ``parent`` (e.g. ``pkg.sub``), empty when the
      unit is top level.

  Whether a qualified ``name`` denotes a package executed through its entry
  file (rather than a directly-named module) is decided by an opaque
  classifier ``marks_entry`` -- the module-execution machinery's own
  classification, modelled as an unchanged callee (axioms region).

  The module-name argument to reproduce is:

    * the enclosing package ``parent`` exactly when ``name`` denotes a package
      executed through its entry file (``marks_entry(name)``) AND a non-empty
      ``parent`` exists;
    * otherwise the qualified import name ``name`` itself.

  So a directly-named module ``pkg.sub.tool`` reproduces as ``pkg.sub.tool``
  (not its parent package ``pkg.sub``), while a package executed through its
  entry file reproduces as the package.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over the pure sequence theory
``PSeq[int]``.  The entry-file classification (``marks_entry``) is an unchanged
boundary callee modelled as a fully opaque ``@Pure @ContractOnly`` function (no
contract is consumed); its real implementation is validated out-of-band, code
point for code point, by axiom_check.py (G-AX) -- an A-reference the deep model
is checked against.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def marks_entry(name: PSeq[int]) -> bool:
    """Whether the qualified module name ``name`` denotes a package executed
    through its entry file (rather than a directly-named module).  This is the
    unchanged classification performed by the module-execution machinery; the
    selection logic under specification calls it but does not change it.

    The proof treats it as an entirely opaque boundary classifier (no contract
    is consumed).  The concrete classifier it stands in for is validated == the
    real selector code-point-for-code-point by axiom_check.py / G-AX -- an
    A-reference callee the deep model is checked against, not an axiom whose
    Ensures the proof relies on."""
    pass
# axioms-end

# pure-start
@Pure
def module_arg(name: PSeq[int], parent: PSeq[int]) -> PSeq[int]:
    """The module-name argument reproduced for the relaunch command."""
    if marks_entry(name) and len(parent) > 0:
        return parent
    return name
# pure-end

def select_module_name(name: List[int], parent: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(parent), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(parent), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reproduced argument is the qualified name itself unless the name
    # denotes a package executed through its entry file with a non-empty
    # enclosing package, in which case it is the enclosing package.
    Ensures(ToSeq(Result()) == module_arg(ToSeq(name), ToSeq(parent)))
    # Discriminating consequence: a directly-named module (name not an
    # entry-file package) reproduces as the name, NOT the parent package.
    Ensures(Implies(not marks_entry(ToSeq(name)),
                    ToSeq(Result()) == ToSeq(name)))
    # A package executed through its entry file reproduces as the package.
    Ensures(Implies(marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0,
                    ToSeq(Result()) == ToSeq(parent)))
    # post-conditions-end
    # impl-start
    sentinel = marks_entry(ToSeq(name))
    result = []  # type: List[int]
    if sentinel and len(parent) > 0:
        i = 0
        while i < len(parent):
            # invariants-start
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(parent))
            Invariant(len(parent) > 0)
            Invariant(marks_entry(ToSeq(name)))
            Invariant(ToSeq(result) == ToSeq(parent).take(i))
            # invariants-end
            result = result + [parent[i]]
            i = i + 1
        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
    else:
        i = 0
        while i < len(name):
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(name))
            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
            Invariant(ToSeq(result) == ToSeq(name).take(i))
            # invariants-end
            result = result + [name[i]]
            i = i + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: model.py's postcondition line 84 `Ensures(ToSeq(Result()) == module_arg(ToSeq(name), ToSeq(parent)))` FULLY PINS the observable output to a deterministic function of the inputs; lines 87-91 are discriminating corollaries. `module_arg` is grounded over the real input carriers on top of the opaque A-reference `marks_entry` (@Pure @ContractOnly, bare `pass`, NO Ensures -> proof consumes no contract). A value-complete spec: no verifying impl can produce a value differing from the gold selection.

TOOLING: module env python. Attacks built by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures/Invariants byte-identical); all 8 + positive_control confirmed SAME by `python -m swebench_unified.adversary same-spec nagini django__django-14311 <f>` (rc=0).

POSITIVE CONTROL: `bash scripts/nagini_verify.sh positive_control.py` -> 'Verification successful' (13.12s), rc=0.

ALL returned rc=2 (NOT-A-COUNTEREXAMPLE: verification failed):
atk_1 = PREPATCH BUG (copy parent unconditionally when non-empty) -> rc=2. Prepatch reproduced.
atk_2 = PARTIAL-DOMAIN (always return name, never parent) -> rc=2.
atk_3 = CONTROL-FLOW / inverted gate ((not sentinel) and parent -> parent) -> rc=2.
atk_4 = BOUNDARY off-by-one (copy name, stop one short: take(len-1)) -> rc=2.
atk_5 = CONTROL-FLOW-EFFECT (build gold selection then append extra code point 120) -> rc=2.
atk_6 = UNGROUNDED/DEGENERATE (always return []) -> rc=2 (proves value postcond truly binds; constant cannot discharge it).
atk_7 = INVERTED SELECTION (entry+parent -> return NAME; non-entry+parent -> return PARENT) -> rc=2.
atk_8 = BOUNDARY on A-reference guard (return parent whenever marks_entry, dropping len(parent)>0 -> empty on entry-name with empty parent) -> rc=2.
No attack reached CANDIDATE (shares-spec AND verifies), so there is NO faithful patch to materialize/resolve; patches={} accordingly.

A-LEG AUDIT (refinement.md §A): A1/A3/A6 = R (str<->List[int]; str truthiness<->len>0; args+=['-m',name] list-wrap identity). A2 = A-reference: `marks_entry` is @Pure @ContractOnly, bare `pass`, NO Ensures -> proof uses NO contract; validated == real gold classifier `name=='__main__' or name.endswith('.__main__')` code-point-for-code-point by G-AX. A4/A5 = R+I (element-wise copy = identity on value <-> name=spec.parent/spec.name). NO A-consumed legs (correct: no axiom Ensures exists), NO kind-3 legs (refinement.md §C confirmed). G-AX EXECUTED: `python axiom_check.py` -> 'G-AX OK: module_arg deep model ... validated == real str selector ... 16 boundary x 6 parents + 40000 fuzz inputs', rc=0. A-reference correspondence to the real callee HOLDS and matches mapping.md §3.1.

CONCLUSION: verify => correct holds here. The value-complete postcondition (grounded module_arg over real inputs, uninterpreted marks_entry) forces any verifying impl to reproduce the gold selection. 8 attacks (prepatch, partial-domain, boundary x2, control-flow-effect x2, ungrounded-oracle echo, inverted selection) all rejected; positive control verifies; G-AX A-reference sound. Verdict SOUND.

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
"""Twin-artifact model for django__django-14311.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a development process was launched by interpreting a module via the
  interpreter's module-execution mechanism, the relaunch command must name the
  SAME module that was originally run.  The launched unit is characterised by
  two code-point strings:

    * its fully-qualified import name ``name`` (e.g. ``pkg.sub.tool``);
    * its enclosing package name ``parent`` (e.g. ``pkg.sub``), empty when the
      unit is top level.

  Whether a qualified ``name`` denotes a package executed through its entry
  file (rather than a directly-named module) is decided by an opaque
  classifier ``marks_entry`` -- the module-execution machinery's own
  classification, modelled as an unchanged callee (axioms region).

  The module-name argument to reproduce is:

    * the enclosing package ``parent`` exactly when ``name`` denotes a package
      executed through its entry file (``marks_entry(name)``) AND a non-empty
      ``parent`` exists;
    * otherwise the qualified import name ``name`` itself.

  So a directly-named module ``pkg.sub.tool`` reproduces as ``pkg.sub.tool``
  (not its parent package ``pkg.sub``), while a package executed through its
  entry file reproduces as the package.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over the pure sequence theory
``PSeq[int]``.  The entry-file classification (``marks_entry``) is an unchanged
boundary callee modelled as a fully opaque ``@Pure @ContractOnly`` function (no
contract is consumed); its real implementation is validated out-of-band, code
point for code point, by axiom_check.py (G-AX) -- an A-reference the deep model
is checked against.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def marks_entry(name: PSeq[int]) -> bool:
    """Whether the qualified module name ``name`` denotes a package executed
    through its entry file (rather than a directly-named module).  This is the
    unchanged classification performed by the module-execution machinery; the
    selection logic under specification calls it but does not change it.

    The proof treats it as an entirely opaque boundary classifier (no contract
    is consumed).  The concrete classifier it stands in for is validated == the
    real selector code-point-for-code-point by axiom_check.py / G-AX -- an
    A-reference callee the deep model is checked against, not an axiom whose
    Ensures the proof relies on."""
    pass
# axioms-end

# pure-start
@Pure
def module_arg(name: PSeq[int], parent: PSeq[int]) -> PSeq[int]:
    """The module-name argument reproduced for the relaunch command."""
    if marks_entry(name) and len(parent) > 0:
        return parent
    return name
# pure-end

def select_module_name(name: List[int], parent: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(parent), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(parent), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reproduced argument is the qualified name itself unless the name
    # denotes a package executed through its entry file with a non-empty
    # enclosing package, in which case it is the enclosing package.
    Ensures(ToSeq(Result()) == module_arg(ToSeq(name), ToSeq(parent)))
    # Discriminating consequence: a directly-named module (name not an
    # entry-file package) reproduces as the name, NOT the parent package.
    Ensures(Implies(not marks_entry(ToSeq(name)),
                    ToSeq(Result()) == ToSeq(name)))
    # A package executed through its entry file reproduces as the package.
    Ensures(Implies(marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0,
                    ToSeq(Result()) == ToSeq(parent)))
    # post-conditions-end
    # impl-start
    sentinel = marks_entry(ToSeq(name))
    result = []  # type: List[int]
    if sentinel and len(parent) > 0:
        i = 0
        while i < len(parent):
            # invariants-start
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(parent))
            Invariant(len(parent) > 0)
            Invariant(marks_entry(ToSeq(name)))
            Invariant(ToSeq(result) == ToSeq(parent).take(i))
            # invariants-end
            result = result + [parent[i]]
            i = i + 1
        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(parent))
    else:
        i = 0
        while i < len(name):
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(name))
            Invariant(not (marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0))
            Invariant(ToSeq(result) == ToSeq(name).take(i))
            # invariants-end
            result = result + [name[i]]
            i = i + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(module_arg(ToSeq(name), ToSeq(parent)) == ToSeq(name))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: model.py's postcondition line 84 `Ensures(ToSeq(Result()) == module_arg(ToSeq(name), ToSeq(parent)))` FULLY PINS the observable output to a deterministic function of the inputs; lines 87-91 are discriminating corollaries. `module_arg` is grounded over the real input carriers on top of the opaque A-reference `marks_entry` (@Pure @ContractOnly, bare `pass`, NO Ensures -> proof consumes no contract). A value-complete spec: no verifying impl can produce a value differing from the gold selection.

TOOLING: module env python. Attacks built by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures/Invariants byte-identical); all 8 + positive_control confirmed SAME by `python -m swebench_unified.adversary same-spec nagini django__django-14311 <f>` (rc=0).

POSITIVE CONTROL: `bash scripts/nagini_verify.sh positive_control.py` -> 'Verification successful' (13.12s), rc=0.

ALL returned rc=2 (NOT-A-COUNTEREXAMPLE: verification failed):
atk_1 = PREPATCH BUG (copy parent unconditionally when non-empty) -> rc=2. Prepatch reproduced.
atk_2 = PARTIAL-DOMAIN (always return name, never parent) -> rc=2.
atk_3 = CONTROL-FLOW / inverted gate ((not sentinel) and parent -> parent) -> rc=2.
atk_4 = BOUNDARY off-by-one (copy name, stop one short: take(len-1)) -> rc=2.
atk_5 = CONTROL-FLOW-EFFECT (build gold selection then append extra code point 120) -> rc=2.
atk_6 = UNGROUNDED/DEGENERATE (always return []) -> rc=2 (proves value postcond truly binds; constant cannot discharge it).
atk_7 = INVERTED SELECTION (entry+parent -> return NAME; non-entry+parent -> return PARENT) -> rc=2.
atk_8 = BOUNDARY on A-reference guard (return parent whenever marks_entry, dropping len(parent)>0 -> empty on entry-name with empty parent) -> rc=2.
No attack reached CANDIDATE (shares-spec AND verifies), so there is NO faithful patch to materialize/resolve; patches={} accordingly.

A-LEG AUDIT (refinement.md §A): A1/A3/A6 = R (str<->List[int]; str truthiness<->len>0; args+=['-m',name] list-wrap identity). A2 = A-reference: `marks_entry` is @Pure @ContractOnly, bare `pass`, NO Ensures -> proof uses NO contract; validated == real gold classifier `name=='__main__' or name.endswith('.__main__')` code-point-for-code-point by G-AX. A4/A5 = R+I (element-wise copy = identity on value <-> name=spec.parent/spec.name). NO A-consumed legs (correct: no axiom Ensures exists), NO kind-3 legs (refinement.md §C confirmed). G-AX EXECUTED: `python axiom_check.py` -> 'G-AX OK: module_arg deep model ... validated == real str selector ... 16 boundary x 6 parents + 40000 fuzz inputs', rc=0. A-reference correspondence to the real callee HOLDS and matches mapping.md §3.1.

CONCLUSION: verify => correct holds here. The value-complete postcondition (grounded module_arg over real inputs, uninterpreted marks_entry) forces any verifying impl to reproduce the gold selection. 8 attacks (prepatch, partial-domain, boundary x2, control-flow-effect x2, ungrounded-oracle echo, inverted selection) all rejected; positive control verifies; G-AX A-reference sound. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-14311 (Nagini). Modeled function select_module_name / module_arg models the gold patch's -m argument selection in get_child_arguments() (django/utils/autoreload.py:225-231). Gold (verified verbatim from dataset test.jsonl patch): name = spec.parent if (spec.name=='__main__' or spec.name.endswith('.__main__')) and spec.parent else spec.name; args += ['-m', name]. Model: module_arg = parent if marks_entry(name) and len(parent)>0 else name, marks_entry = opaque classifier for name=='__main__' or name.endswith('.__main__').

Checks: is pre-patch base (unconditional __main__.__spec__.parent for -m); gold applies the discriminating change. INDEPENDENT differential test in faith14311.py — transcribed gold selection directly from dataset, compared code-point-for-code-point over 200,000 randomized inputs (segment dotted names with __main__/__main/main__ segments + char-level fuzz incl. astral code points é/•/𝔘) plus all boundary cases (''/__main__/.__main__/foo.__main__/x__main__/my__main__/__main__x/pkg.__main__.sub/a.b.__main__c × 6 parents incl empty and unicode). ZERO divergences. (3) Refinement soundness exact: str<->List[int] via ord is a bijection; spec.parent truthiness (str falsy iff empty) <-> len(parent)>0 is exact; args+=['-m',name] is identity on modeled value. marks_entry is fully opaque @Pure @ContractOnly (no Ensures consumed) so cannot over-constrain the impl; the changed selection is grounded over the real input carriers. The modeled function agrees with the real post-patch repo callee on every input in its domain — spec is neither too strong nor drifting. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view) PASSES: no diff markers, no reproduced gold-patch lines (>=8 chars), no patched file path (django/utils/autoreload.py) or dotted module path, no spec-view identifier embedding a patched repo symbol, no bug/fix narration. Confirmed none of {__main__, .__main__, endswith, __spec__, autoreload, get_child_arguments, runserver, 'python -m'} appear anywhere in the spec view.

Semantic gold-reconstruction analysis: the gold edit has two components.

(1) The behavioral change -- a directly-named dotted module foo.bar.baz must reproduce as '-m foo.bar.baz' rather than its parent '-m foo.bar' -- is ALREADY PUBLIC verbatim in problem_statement ('When a dotted name for a module (for example, foo.bar.baz where baz.py resides under foo/bar) is specified like -m foo.bar.baz, the resulting arguments end up being -m foo.bar, which is uncalled for'), which also contrasts it with the package-with-__main__.py case. So module_arg's stated behavior (return name unless it is an entry-file package with non-empty parent) is a legitimate restatement of publicly-stated DESIRED behavior, not a leak.

(2) The concrete classification mechanism spec.name == '__main__' or spec.name.endswith('.__main__') -- which is only surfaced in hints_text, NOT problem_statement -- is deliberately kept OPAQUE in the spec view: marks_entry is @Pure @ContractOnly with a body of `pass` and no revealing Ensures. Its docstring describes it abstractly ('denotes a package executed through its entry file') and never mentions __main__ or endswith. The concrete str classifier lives only in the audit files (mapping.md / axiom_check.py), which are NOT part of the consumer spec view.

The spec view thus operates at the same abstraction level the public problem statement already establishes and hides the gold's specific implementation trigger (the .__main__ suffix test). No spec-view line reconstructs the gold edit beyond problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
