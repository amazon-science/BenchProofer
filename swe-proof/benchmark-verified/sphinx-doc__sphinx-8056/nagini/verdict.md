# P2 adversarial audit — sphinx-doc__sphinx-8056

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2_notrim.py`, `atk_3_dropguard.py`, `atk_4_offbyone.py`, `atk_5_trimverbatim.py`, `atk_6_alwayssplit.py`, `atk_7_reversed.py`, `atk_8_emitempty.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                   type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -104,39 +102,15 @@
                     Result()[0] == ToSeq(name)))
     # post-conditions-end
     # impl-start
+    # PRE-PATCH SKELETON: the name field is consumed WITHOUT the per-comma
+    # expansion -- the requested-expansion flag is ignored, so a multi-name
+    # field is kept as one verbatim entry instead of being split into one entry
+    # per comma-separated name. (Reverts the fix; fails the count/content
+    # postcondition whenever an expanded multi-name field carries a comma.)
     result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
-    if multiple and len(name) > 0:
-        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
-        n = num_commas(ToSeq(name)) + 1
-        Assert(len(parts) == n)
-        i = 0
-        while i < n:
-            # invariants-start
-            Invariant(Acc(list_pred(name), 1 / 2))
-            Invariant(multiple and len(name) > 0)
-            Invariant(0 <= i and i <= n)
-            Invariant(n == num_commas(ToSeq(name)) + 1)
-            Invariant(parts == split_on_comma(ToSeq(name)))
-            Invariant(len(result) == i)
-            Invariant(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
-                [[result[k]]])))
-            Invariant(MustTerminate(n - i + 1))
-            # invariants-end
-            piece = trim(parts[i])  # type: PSeq[int]
-            old_result = result  # type: PSeq[PSeq[int]]
-            result = result + PSeq(piece)
-            Assert(len(result) == i + 1)
-            Assert(result[i] == piece)
-            Assert(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == old_result[k]),
-                [[result[k]]])))
-            i = i + 1
-        return result
-    else:
-        if len(name) > 0 or type_nonempty or desc_nonempty:
-            result = result + PSeq(ToSeq(name))
-            Assert(len(result) == 1)
-            Assert(result[0] == ToSeq(name))
-        return result
+    if len(name) > 0 or type_nonempty or desc_nonempty:
+        result = result + PSeq(ToSeq(name))
+        Assert(len(result) == 1)
+        Assert(result[0] == ToSeq(name))
+    return result
     # impl-end
```

Attack 2 — `atk_2_notrim.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                   type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -111,32 +109,18 @@
         Assert(len(parts) == n)
         i = 0
         while i < n:
-            # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(multiple and len(name) > 0)
             Invariant(0 <= i and i <= n)
             Invariant(n == num_commas(ToSeq(name)) + 1)
             Invariant(parts == split_on_comma(ToSeq(name)))
             Invariant(len(result) == i)
-            Invariant(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
-                [[result[k]]])))
-            Invariant(MustTerminate(n - i + 1))
-            # invariants-end
-            piece = trim(parts[i])  # type: PSeq[int]
-            old_result = result  # type: PSeq[PSeq[int]]
+            piece = parts[i]  # type: PSeq[int]  # BUG: no trim
             result = result + PSeq(piece)
-            Assert(len(result) == i + 1)
-            Assert(result[i] == piece)
-            Assert(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == old_result[k]),
-                [[result[k]]])))
             i = i + 1
         return result
     else:
         if len(name) > 0 or type_nonempty or desc_nonempty:
             result = result + PSeq(ToSeq(name))
-            Assert(len(result) == 1)
-            Assert(result[0] == ToSeq(name))
         return result
     # impl-end
```

Attack 3 — `atk_3_dropguard.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                   type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -111,7 +109,6 @@
         Assert(len(parts) == n)
         i = 0
         while i < n:
-            # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(multiple and len(name) > 0)
             Invariant(0 <= i and i <= n)
@@ -121,22 +118,12 @@
             Invariant(Forall(int, lambda k: (
                 Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                 [[result[k]]])))
-            Invariant(MustTerminate(n - i + 1))
-            # invariants-end
             piece = trim(parts[i])  # type: PSeq[int]
-            old_result = result  # type: PSeq[PSeq[int]]
             result = result + PSeq(piece)
-            Assert(len(result) == i + 1)
-            Assert(result[i] == piece)
-            Assert(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == old_result[k]),
-                [[result[k]]])))
             i = i + 1
         return result
     else:
-        if len(name) > 0 or type_nonempty or desc_nonempty:
+        if len(name) > 0:  # BUG: dropped `or type_nonempty or desc_nonempty`
             result = result + PSeq(ToSeq(name))
-            Assert(len(result) == 1)
-            Assert(result[0] == ToSeq(name))
         return result
     # impl-end
```

Attack 4 — `atk_4_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                   type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -110,33 +108,22 @@
         n = num_commas(ToSeq(name)) + 1
         Assert(len(parts) == n)
         i = 0
-        while i < n:
-            # invariants-start
+        while i < n - 1:  # BUG: drops the final run
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(multiple and len(name) > 0)
-            Invariant(0 <= i and i <= n)
+            Invariant(0 <= i and i <= n - 1)
             Invariant(n == num_commas(ToSeq(name)) + 1)
             Invariant(parts == split_on_comma(ToSeq(name)))
             Invariant(len(result) == i)
             Invariant(Forall(int, lambda k: (
                 Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                 [[result[k]]])))
-            Invariant(MustTerminate(n - i + 1))
-            # invariants-end
             piece = trim(parts[i])  # type: PSeq[int]
-            old_result = result  # type: PSeq[PSeq[int]]
             result = result + PSeq(piece)
-            Assert(len(result) == i + 1)
-            Assert(result[i] == piece)
-            Assert(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == old_result[k]),
-                [[result[k]]])))
             i = i + 1
         return result
     else:
         if len(name) > 0 or type_nonempty or desc_nonempty:
             result = result + PSeq(ToSeq(name))
-            Assert(len(result) == 1)
-            Assert(result[0] == ToSeq(name))
         return result
     # impl-end
```

Attack 5 — `atk_5_trimverbatim.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                   type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -111,7 +109,6 @@
         Assert(len(parts) == n)
         i = 0
         while i < n:
-            # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(multiple and len(name) > 0)
             Invariant(0 <= i and i <= n)
@@ -121,22 +118,12 @@
             Invariant(Forall(int, lambda k: (
                 Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                 [[result[k]]])))
-            Invariant(MustTerminate(n - i + 1))
-            # invariants-end
             piece = trim(parts[i])  # type: PSeq[int]
-            old_result = result  # type: PSeq[PSeq[int]]
             result = result + PSeq(piece)
-            Assert(len(result) == i + 1)
-            Assert(result[i] == piece)
-            Assert(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == old_result[k]),
-                [[result[k]]])))
             i = i + 1
         return result
     else:
         if len(name) > 0 or type_nonempty or desc_nonempty:
-            result = result + PSeq(ToSeq(name))
-            Assert(len(result) == 1)
-            Assert(result[0] == ToSeq(name))
+            result = result + PSeq(trim(ToSeq(name)))  # BUG: trims verbatim entry
         return result
     # impl-end
```

Attack 6 — `atk_6_alwayssplit.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                   type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -105,15 +103,14 @@
     # post-conditions-end
     # impl-start
     result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
-    if multiple and len(name) > 0:
+    if len(name) > 0:  # BUG: ignores `multiple`, always expands non-empty name
         parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
         n = num_commas(ToSeq(name)) + 1
         Assert(len(parts) == n)
         i = 0
         while i < n:
-            # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
-            Invariant(multiple and len(name) > 0)
+            Invariant(len(name) > 0)
             Invariant(0 <= i and i <= n)
             Invariant(n == num_commas(ToSeq(name)) + 1)
             Invariant(parts == split_on_comma(ToSeq(name)))
@@ -121,22 +118,12 @@
             Invariant(Forall(int, lambda k: (
                 Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                 [[result[k]]])))
-            Invariant(MustTerminate(n - i + 1))
-            # invariants-end
             piece = trim(parts[i])  # type: PSeq[int]
-            old_result = result  # type: PSeq[PSeq[int]]
             result = result + PSeq(piece)
-            Assert(len(result) == i + 1)
-            Assert(result[i] == piece)
-            Assert(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == old_result[k]),
-                [[result[k]]])))
             i = i + 1
         return result
     else:
-        if len(name) > 0 or type_nonempty or desc_nonempty:
+        if type_nonempty or desc_nonempty:
             result = result + PSeq(ToSeq(name))
-            Assert(len(result) == 1)
-            Assert(result[0] == ToSeq(name))
         return result
     # impl-end
```

Attack 7 — `atk_7_reversed.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                   type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -111,7 +109,6 @@
         Assert(len(parts) == n)
         i = 0
         while i < n:
-            # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(multiple and len(name) > 0)
             Invariant(0 <= i and i <= n)
@@ -119,24 +116,14 @@
             Invariant(parts == split_on_comma(ToSeq(name)))
             Invariant(len(result) == i)
             Invariant(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
+                Implies(0 <= k and k < i, result[k] == trim(parts[n - 1 - k])),
                 [[result[k]]])))
-            Invariant(MustTerminate(n - i + 1))
-            # invariants-end
-            piece = trim(parts[i])  # type: PSeq[int]
-            old_result = result  # type: PSeq[PSeq[int]]
+            piece = trim(parts[n - 1 - i])  # type: PSeq[int]  # BUG: reversed
             result = result + PSeq(piece)
-            Assert(len(result) == i + 1)
-            Assert(result[i] == piece)
-            Assert(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == old_result[k]),
-                [[result[k]]])))
             i = i + 1
         return result
     else:
         if len(name) > 0 or type_nonempty or desc_nonempty:
             result = result + PSeq(ToSeq(name))
-            Assert(len(result) == 1)
-            Assert(result[0] == ToSeq(name))
         return result
     # impl-end
```

Attack 8 — `atk_8_emitempty.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                   type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -111,7 +109,6 @@
         Assert(len(parts) == n)
         i = 0
         while i < n:
-            # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(multiple and len(name) > 0)
             Invariant(0 <= i and i <= n)
@@ -121,22 +118,11 @@
             Invariant(Forall(int, lambda k: (
                 Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                 [[result[k]]])))
-            Invariant(MustTerminate(n - i + 1))
-            # invariants-end
             piece = trim(parts[i])  # type: PSeq[int]
-            old_result = result  # type: PSeq[PSeq[int]]
             result = result + PSeq(piece)
-            Assert(len(result) == i + 1)
-            Assert(result[i] == piece)
-            Assert(Forall(int, lambda k: (
-                Implies(0 <= k and k < i, result[k] == old_result[k]),
-                [[result[k]]])))
             i = i + 1
         return result
     else:
-        if len(name) > 0 or type_nonempty or desc_nonempty:
-            result = result + PSeq(ToSeq(name))
-            Assert(len(result) == 1)
-            Assert(result[0] == ToSeq(name))
+        result = result + PSeq(ToSeq(name))  # BUG: always emit one entry, even all-empty
         return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8056.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documented entry consumed from a parameter section carries a *name field*
  (a run of text), a *type* and a *description*. The name field may name more
  than one entry at once, the individual names being separated by literal
  commas (for example ``"x1, x2"`` names two entries). When this "one entry per
  comma-separated name" expansion is requested AND the name field is non-empty,
  the consumer emits ONE entry per comma-separated name, each name trimmed of
  surrounding whitespace and each carrying the SHARED type and description of
  the original field. So a name field holding ``c`` commas yields ``c + 1``
  emitted entries, in left-to-right order, the k-th being the trimmed k-th
  comma-separated run.

  When the expansion is NOT requested, the field is emitted as a single entry
  whenever any of its name / type / description is non-empty (the name kept
  verbatim, commas and surrounding whitespace included); an entirely empty
  field is dropped.

Strings are modelled as ``List[int]`` / ``PSeq[int]`` of Unicode code points
(Nagini bans ``str`` indexing); the emitted sequence of names is carried as a
pure ``PSeq[PSeq[int]]``. The comma split and the whitespace trim are unchanged
stdlib string operations the consumer CALLS; they are axiomatized
(``split_on_comma`` / ``trim``) and their soundness is checked against the real
callees out-of-band by axiom_check.py (G-AX). The emitted sequence of names is
the modelled, F2P-discriminating output (type and description are shared
verbatim across every emitted entry, so the name sequence carries the whole
change).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def num_commas(s: PSeq[int]) -> int:
    """Number of comma (code point 44) separators in ``s``. The count of
    comma-separated runs is ``num_commas(s) + 1`` (an empty run still counts),
    matching ``len(text.split(',')) == text.count(',') + 1``."""
    Ensures(Result() >= 0)
    Ensures(Implies(len(s) == 0, Result() == 0))


@Pure
@ContractOnly
def split_on_comma(s: PSeq[int]) -> PSeq[PSeq[int]]:
    """Splitting ``s`` on every literal comma (unchanged ``str.split(',')``).
    Always yields ``num_commas(s) + 1`` runs, the k-th being the text between
    the k-th and (k+1)-th separator. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Ensures(len(Result()) == num_commas(s) + 1)


@Pure
@ContractOnly
def trim(s: PSeq[int]) -> PSeq[int]:
    """Whitespace-trimmed ``s`` (unchanged ``str.strip()``): the leading and
    trailing runs of whitespace are removed and interior content is preserved.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
# axioms-end


# pure-start
# (no extra pure helpers: the changed operation is the control-flow choice to
#  expand the name field; split/trim are the axiomatized unchanged callees.)
# pure-end


def emitted_names(name: List[int], multiple: bool,
                  type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    # When the per-comma expansion is requested and the name is non-empty, one
    # entry is emitted per comma-separated run (so num_commas + 1 in total),
    # the k-th being the whitespace-trimmed k-th run, in order. This is the
    # behaviour the multi-name field demands.
    Ensures(Implies(multiple and len(name) > 0,
                    len(Result()) == num_commas(ToSeq(name)) + 1))
    Ensures(Forall(int, lambda k: (
        Implies(multiple and len(name) > 0 and 0 <= k and k < len(Result()),
                Result()[k] == trim(split_on_comma(ToSeq(name))[k])),
        [[Result()[k]]])))
    # Otherwise the field is emitted as at most one entry: a single verbatim
    # name when any of name/type/description is non-empty, else nothing. The
    # name is NOT split (commas and surrounding whitespace are kept).
    Ensures(Implies(not (multiple and len(name) > 0),
                    len(Result()) <= 1))
    Ensures(Implies(not (multiple and len(name) > 0) and
                    (len(name) > 0 or type_nonempty or desc_nonempty),
                    len(Result()) == 1))
    Ensures(Implies(not (multiple and len(name) > 0) and
                    not len(name) > 0 and not type_nonempty and not desc_nonempty,
                    len(Result()) == 0))
    Ensures(Implies(not (multiple and len(name) > 0) and len(Result()) == 1,
                    Result()[0] == ToSeq(name)))
    # post-conditions-end
    # impl-start
    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            result = result + PSeq(ToSeq(name))
            Assert(len(result) == 1)
            Assert(result[0] == ToSeq(name))
        return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8056 (nagini). Bundle root: benchmark-verified/sphinx-doc__sphinx-8056/nagini. verifier env python; scripts/nagini_verify.sh.

SPEC SHAPE: emitted_names(name:List[int], multiple, type_nonempty, desc_nonempty) -> PSeq[PSeq[int]]. Postconditions fully pin Result in every flag combination and both branches: (multiple & name>0) => len==num_commas+1 AND forall k Result[k]==trim(split_on_comma(ToSeq(name))[k]); otherwise len<=1, ==1 iff (name>0 or type_nonempty or desc_nonempty), ==0 iff all-empty, and Result[0]==ToSeq(name) (verbatim, unsplit/untrimmed). Axiom `trim` is FULLY UNINTERPRETED (no Ensures); `split_on_comma` pins only length (==num_commas+1). Because trim is uninterpreted and the content clause is pinned to trim(split_on_comma(name)[k]), a verifying impl is FORCED to literally compute the gold expression — the spec is maximally tight.

BASELINE: positive_control (copy of gold model.py) VERIFIES (scripts/nagini_verify.sh, 11.8s, 'Verification successful'). prepatch.py (copy of model_prepatch.py; ignores `multiple`, always single verbatim entry) FAILS with exactly 'Postcondition ... Implies((multiple and len(name)>0), len(Result())==num_commas(ToSeq(name))+1) might not hold' — the F2P count discriminator. prepatch_reproduced=true.

ATTACKS (8 distinct wrong impls; impl region only edited, axioms/@Pure/Requires/Ensures byte-identical). All 8 confirmed SAME-spec via `adversary same-spec` (exit 0), then `adversary weakness nagini sphinx-doc__sphinx-8056 <f>` (exit 2 = NOT-A-COUNTEREXAMPLE for every one):
atk_1 = prepatch bug (ignore multiple).
atk_2_notrim = multiple-branch appends raw parts[i] (no trim) -> content clause violated.
atk_3_dropguard = else-branch keep-guard reduced to `len(name)>0` (partial-domain: type/desc-only field wrongly dropped).
atk_4_offbyone = multiple-branch loops i<n-1, drops final run (boundary/control-flow).
atk_5_trimverbatim = else-branch emits trim(name) instead of verbatim -> Result[0]==ToSeq(name) violated.
atk_6_alwayssplit = ignores `multiple`, always expands non-empty name (control-flow-effect: non-multiple len may be >1).
atk_7_reversed = emits runs in reversed order -> content clause violated.
atk_8_emitempty = else-branch always emits one entry (ungrounded, all-empty not dropped).
Every attack FULLY verified: zero CANDIDATEs (no verifying wrong impl), so there was no faithful refined patch to materialize/run through run_resolve.

### EXACT COMMANDS (from project root, SBU_BENCHMARK_DIR=benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8056 <atk>   # exit 0 all 8
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-8056 <atk>   # exit 2 all 8
  bash scripts/nagini_verify.sh <positive_control|prepatch>

G-AX: ran bundle axiom_check.py -> exit 0: 'num_commas/split_on_comma/trim axioms sound vs real str.count/str.split/str.strip; composed emitted_names == gold _consume_fields on 19 boundary + 30000 fuzz inputs x flag combos'. Composed observable equals gold patch's per-field _consume_fields across all (multiple,type,desc) combos incl. F2P 'x1, x2'->['x1','x2'] and non-expansion 'x1, x2'->['x1, x2'].

REFINEMENT.md AUDIT (A-leg focus): legs A1(R type refine str<->List[int]), A2(I bool), A3(R non-emptiness observable), A4(R+I truthy<->len>0), A5(A-consumed: split_on_comma<->str.split(','), trim<->str.strip(); proof consumes only the length Ensures, content discharged by construction), A6(R+I legacy keep-guard, verbatim name). No kind-3 (Section D): the genuinely-changed operation (control-flow choice to expand per comma) is modeled DIRECTLY in the impl `if multiple and len(name)>0` branch + loop, NOT hidden behind an axiom about the function under change; the 3 axioms cover only UNCHANGED stdlib callees whose correspondence to str.split/str.strip/str.count is validated by G-AX. No A-reference deep models in this bundle. Call-site change (multiple=True only in napoleon_use_param branch) captured by the `multiple` parameter (A2/A4); both configs pinned by the single frozen spec. Correspondence holds.

VERDICT: SOUND. >=5 (8) distinct same-spec attacks run and machine-checked; none verifies, so verify=>correct is not falsified; positive control verifies; prepatch bug reproduced; G-AX sound; refinement legs all R/A-consumed/I with valid callee correspondence. No verifying wrong impl exists to force a resolve run.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2_notrim.py`, `atk_3_dropguard.py`, `atk_4_offbyone.py`, `atk_5_trimverbatim.py`, `atk_6_alwayssplit.py`, `atk_7_reversed.py`, `atk_8_emitempty.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_notrim.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_dropguard.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_offbyone.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_trimverbatim.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_alwayssplit.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_reversed.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_emitempty.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8056.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documented entry consumed from a parameter section carries a *name field*
  (a run of text), a *type* and a *description*. The name field may name more
  than one entry at once, the individual names being separated by literal
  commas (for example ``"x1, x2"`` names two entries). When this "one entry per
  comma-separated name" expansion is requested AND the name field is non-empty,
  the consumer emits ONE entry per comma-separated name, each name trimmed of
  surrounding whitespace and each carrying the SHARED type and description of
  the original field. So a name field holding ``c`` commas yields ``c + 1``
  emitted entries, in left-to-right order, the k-th being the trimmed k-th
  comma-separated run.

  When the expansion is NOT requested, the field is emitted as a single entry
  whenever any of its name / type / description is non-empty (the name kept
  verbatim, commas and surrounding whitespace included); an entirely empty
  field is dropped.

Strings are modelled as ``List[int]`` / ``PSeq[int]`` of Unicode code points
(Nagini bans ``str`` indexing); the emitted sequence of names is carried as a
pure ``PSeq[PSeq[int]]``. The comma split and the whitespace trim are unchanged
stdlib string operations the consumer CALLS; they are axiomatized
(``split_on_comma`` / ``trim``) and their soundness is checked against the real
callees out-of-band by axiom_check.py (G-AX). The emitted sequence of names is
the modelled, F2P-discriminating output (type and description are shared
verbatim across every emitted entry, so the name sequence carries the whole
change).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def num_commas(s: PSeq[int]) -> int:
    """Number of comma (code point 44) separators in ``s``. The count of
    comma-separated runs is ``num_commas(s) + 1`` (an empty run still counts),
    matching ``len(text.split(',')) == text.count(',') + 1``."""
    Ensures(Result() >= 0)
    Ensures(Implies(len(s) == 0, Result() == 0))


@Pure
@ContractOnly
def split_on_comma(s: PSeq[int]) -> PSeq[PSeq[int]]:
    """Splitting ``s`` on every literal comma (unchanged ``str.split(',')``).
    Always yields ``num_commas(s) + 1`` runs, the k-th being the text between
    the k-th and (k+1)-th separator. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Ensures(len(Result()) == num_commas(s) + 1)


@Pure
@ContractOnly
def trim(s: PSeq[int]) -> PSeq[int]:
    """Whitespace-trimmed ``s`` (unchanged ``str.strip()``): the leading and
    trailing runs of whitespace are removed and interior content is preserved.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
# axioms-end


# pure-start
# (no extra pure helpers: the changed operation is the control-flow choice to
#  expand the name field; split/trim are the axiomatized unchanged callees.)
# pure-end


def emitted_names(name: List[int], multiple: bool,
                  type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    # When the per-comma expansion is requested and the name is non-empty, one
    # entry is emitted per comma-separated run (so num_commas + 1 in total),
    # the k-th being the whitespace-trimmed k-th run, in order. This is the
    # behaviour the multi-name field demands.
    Ensures(Implies(multiple and len(name) > 0,
                    len(Result()) == num_commas(ToSeq(name)) + 1))
    Ensures(Forall(int, lambda k: (
        Implies(multiple and len(name) > 0 and 0 <= k and k < len(Result()),
                Result()[k] == trim(split_on_comma(ToSeq(name))[k])),
        [[Result()[k]]])))
    # Otherwise the field is emitted as at most one entry: a single verbatim
    # name when any of name/type/description is non-empty, else nothing. The
    # name is NOT split (commas and surrounding whitespace are kept).
    Ensures(Implies(not (multiple and len(name) > 0),
                    len(Result()) <= 1))
    Ensures(Implies(not (multiple and len(name) > 0) and
                    (len(name) > 0 or type_nonempty or desc_nonempty),
                    len(Result()) == 1))
    Ensures(Implies(not (multiple and len(name) > 0) and
                    not len(name) > 0 and not type_nonempty and not desc_nonempty,
                    len(Result()) == 0))
    Ensures(Implies(not (multiple and len(name) > 0) and len(Result()) == 1,
                    Result()[0] == ToSeq(name)))
    # post-conditions-end
    # impl-start
    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            result = result + PSeq(ToSeq(name))
            Assert(len(result) == 1)
            Assert(result[0] == ToSeq(name))
        return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8056 (nagini). Bundle root: benchmark-verified/sphinx-doc__sphinx-8056/nagini. verifier env python; scripts/nagini_verify.sh.

SPEC SHAPE: emitted_names(name:List[int], multiple, type_nonempty, desc_nonempty) -> PSeq[PSeq[int]]. Postconditions fully pin Result in every flag combination and both branches: (multiple & name>0) => len==num_commas+1 AND forall k Result[k]==trim(split_on_comma(ToSeq(name))[k]); otherwise len<=1, ==1 iff (name>0 or type_nonempty or desc_nonempty), ==0 iff all-empty, and Result[0]==ToSeq(name) (verbatim, unsplit/untrimmed). Axiom `trim` is FULLY UNINTERPRETED (no Ensures); `split_on_comma` pins only length (==num_commas+1). Because trim is uninterpreted and the content clause is pinned to trim(split_on_comma(name)[k]), a verifying impl is FORCED to literally compute the gold expression — the spec is maximally tight.

BASELINE: positive_control (copy of gold model.py) VERIFIES (scripts/nagini_verify.sh, 11.8s, 'Verification successful'). prepatch.py (copy of model_prepatch.py; ignores `multiple`, always single verbatim entry) FAILS with exactly 'Postcondition ... Implies((multiple and len(name)>0), len(Result())==num_commas(ToSeq(name))+1) might not hold' — the F2P count discriminator. prepatch_reproduced=true.

ATTACKS (8 distinct wrong impls; impl region only edited, axioms/@Pure/Requires/Ensures byte-identical). All 8 confirmed SAME-spec via `adversary same-spec` (exit 0), then `adversary weakness nagini sphinx-doc__sphinx-8056 <f>` (exit 2 = NOT-A-COUNTEREXAMPLE for every one):
atk_1 = prepatch bug (ignore multiple).
atk_2_notrim = multiple-branch appends raw parts[i] (no trim) -> content clause violated.
atk_3_dropguard = else-branch keep-guard reduced to `len(name)>0` (partial-domain: type/desc-only field wrongly dropped).
atk_4_offbyone = multiple-branch loops i<n-1, drops final run (boundary/control-flow).
atk_5_trimverbatim = else-branch emits trim(name) instead of verbatim -> Result[0]==ToSeq(name) violated.
atk_6_alwayssplit = ignores `multiple`, always expands non-empty name (control-flow-effect: non-multiple len may be >1).
atk_7_reversed = emits runs in reversed order -> content clause violated.
atk_8_emitempty = else-branch always emits one entry (ungrounded, all-empty not dropped).
Every attack FULLY verified: zero CANDIDATEs (no verifying wrong impl), so there was no faithful refined patch to materialize/run through run_resolve.

### EXACT COMMANDS (from project root, SBU_BENCHMARK_DIR=benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8056 <atk>   # exit 0 all 8
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-8056 <atk>   # exit 2 all 8
  bash scripts/nagini_verify.sh <positive_control|prepatch>

G-AX: ran bundle axiom_check.py -> exit 0: 'num_commas/split_on_comma/trim axioms sound vs real str.count/str.split/str.strip; composed emitted_names == gold _consume_fields on 19 boundary + 30000 fuzz inputs x flag combos'. Composed observable equals gold patch's per-field _consume_fields across all (multiple,type,desc) combos incl. F2P 'x1, x2'->['x1','x2'] and non-expansion 'x1, x2'->['x1, x2'].

REFINEMENT.md AUDIT (A-leg focus): legs A1(R type refine str<->List[int]), A2(I bool), A3(R non-emptiness observable), A4(R+I truthy<->len>0), A5(A-consumed: split_on_comma<->str.split(','), trim<->str.strip(); proof consumes only the length Ensures, content discharged by construction), A6(R+I legacy keep-guard, verbatim name). No kind-3 (Section D): the genuinely-changed operation (control-flow choice to expand per comma) is modeled DIRECTLY in the impl `if multiple and len(name)>0` branch + loop, NOT hidden behind an axiom about the function under change; the 3 axioms cover only UNCHANGED stdlib callees whose correspondence to str.split/str.strip/str.count is validated by G-AX. No A-reference deep models in this bundle. Call-site change (multiple=True only in napoleon_use_param branch) captured by the `multiple` parameter (A2/A4); both configs pinned by the single frozen spec. Correspondence holds.

VERDICT: SOUND. >=5 (8) distinct same-spec attacks run and machine-checked; none verifies, so verify=>correct is not falsified; positive control verifies; prepatch bug reproduced; G-AX sound; refinement legs all R/A-consumed/I with valid callee correspondence. No verifying wrong impl exists to force a resolve run.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attacker (spec-too-strong / drift check) for sphinx-doc__sphinx-8056 nagini bundle.

MODELED FUNCTION: emitted_names(name:List[int], multiple, type_nonempty, desc_nonempty) -> PSeq[PSeq[int]]. It models the per-field body of GoogleDocstring._consume_fields (sphinx/ext/napoleon/docstring.py:269-280) as reached from _parse_parameters_section. Real code (confirmed byte-exact from the gold-patched worktree at base_commit e188d56):
  if multiple and _name:
      for name in _name.split(','): fields.append((name.strip(), _type, _desc))
  elif _name or _type or _desc:
      fields.append((_name, _type, _desc,))

### SPEC CLAIMS vs REAL BEHAVIOR:
  (a) multiple and len(name)>0 => len(Result)==num_commas+1, Result[k]==trim(split_on_comma(name)[k]). Real: split on ',' yields count(',')+1 runs, each .strip(). num_commas ~ str.count(','), split_on_comma ~ str.split(','), trim ~ str.strip(). EXACT match.
  (b) not(multiple and name>0): len<=1; ==1 iff name>0 or type or desc; else 0; and when ==1, Result[0]==name VERBATIM (unsplit/untrimmed). Real elif branch appends _name verbatim. EXACT match.

The spec is NOT too strong. It does not over-constrain: the multiple branch ignores type/desc exactly as the real code does; the verbatim (untrimmed, unsplit) single-entry claim matches the elif; empty-field drop matches.

### Evidence
- Nagini verify of model.py: PASS (11.72s).
- axiom_check.py (G-AX): PASS — 19 boundary + 30000 fuzz inputs x flag combos; its gold_consume transcription matches the real worktree source byte-for-byte.
- Independent differential fuzz (500,000 inputs, seed-varied, alphabet incl. exotic Unicode whitespace \xa0, \v, \f, \r, ideographic space) of modeled semantics vs real per-field emission: 0 mismatches, including boundary cases ',', ',,', ' ', whitespace-only names, '*args, **kwargs'.
- same-spec on identity model: exit 0 (spec region well-defined and intact).
- F2P discriminator 'x1, x2' -> ['x1','x2'] (multiple=True) / -> ['x1, x2'] (multiple=False) matches.

No diverging input exists: the modeled function agrees with the real callee on every tested input. The axioms cover only UNCHANGED stdlib callees (str.split/strip/count) and are validated against the real built-ins. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view authenticity confirmed: markers.region_hashes(model.py).spec_view == meta.json frozen hash 4045892a09ccf86c70ee503e5740f9a9a7c2fe4f14aba5fd4f35a486b9366eaa; the impl region is fully elided ('...  # implementation elided'), so the gold loop/split/strip mechanism is not present in the view. Mechanical leak screen (leakage.screen with the dataset gold patch + public problem_statement) returns passed=True, no hard_failures, no warnings.

Gold edit under test: `_consume_fields(..., multiple: bool = False)`; `if multiple and _name: for name in _name.split(','): fields.append((name.strip(), _type, _desc))`; `_parse_parameters_section` calls `_consume_fields(multiple=True)` under `napoleon_use_param`.

Lexical scan of the spec view for gold-edit localization — ALL ABSENT: _consume_fields, _parse_parameters_section, _parse_other_parameters_section, napoleon_use_param, _format_docutils_params, parse_type, prefer_type, fields.append, `.split(",")`, the module path sphinx.ext.napoleon, and the file docstring.py. No diff markers, no reproduced gold-patch lines, no bug/fix/regression narration.

The only substring hits are false positives / legitimate content: (a) `.strip()` and `split(',')` appear ONLY inside the axiom docstrings for the model's own axiomatized stdlib stand-ins `trim`/`split_on_comma`, documenting that they model CPython str.strip/str.split(',') — this is provenance for the axioms, not a disclosure of the gold edit's location or repo mechanism; (b) 'sphinx' appears only as the public instance_id in the module docstring header.

Crucially, the behavior the spec formalizes (a name field like "x1, x2" naming multiple comma-separated entries expanding into one trimmed entry per name, sharing type/desc) is ALREADY publicly disclosed by the problem_statement, which gives the exact `x1, x2 : array_like` example and the expected per-parameter rendering ("x1, x2 (array_like, optional) - Input arrays..."). The obvious implementation of that publicly-stated behavior is split-on-comma + trim, which a solver infers from the problem statement alone. The spec states desired behavior (its legitimate role) and provides no edit-localization (file/function/config-flag/call-site) beyond the public problem statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
