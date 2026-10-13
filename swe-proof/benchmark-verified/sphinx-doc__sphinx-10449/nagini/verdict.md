# P2 adversarial audit — sphinx-doc__sphinx-10449

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
 def suppress_for_kind(object_kind: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(object_kind), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(object_kind), 1 / 2))
@@ -105,7 +103,6 @@
 def has_return_field_in(fields: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -119,7 +116,6 @@
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(found == has_return_field(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
@@ -136,7 +132,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
     Requires(Acc(list_pred(return_annotation), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -160,10 +155,9 @@
     no_return_field = not has_return_field_in(fields)
     Assert(no_return_field == (not has_return_field(ToSeq(fields))))
     if has_return and no_return_field:
-        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
-        if suppressed_none:
-            return None
-        # Render the field with the object's own return annotation as content.
+        # PRE-PATCH SKELETON: the return-type field is appended unconditionally
+        # for the documented object's return annotation, with no suppression of
+        # a 'None' return type for a container object kind.
         field = []  # type: List[int]
         j = 0
         while j < len(return_annotation):
@@ -172,10 +166,6 @@
             Invariant(Acc(list_pred(field)))
             Invariant(0 <= j and j <= len(return_annotation))
             Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
-            Invariant(not suppressed_none)
-            Invariant(suppressed_none
-                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
-            Invariant(MustTerminate(len(return_annotation) - j + 1))
             # invariants-end
             Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                    == return_annotation[j])
@@ -186,7 +176,6 @@
         Assert(ToSeq(return_annotation).take(len(return_annotation))
                == ToSeq(return_annotation))
         Assert(ToSeq(field) == ToSeq(return_annotation))
-        Assert(has_return and no_return_field and not suppressed_none)
         return field
     return None
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
 def suppress_for_kind(object_kind: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(object_kind), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(object_kind), 1 / 2))
@@ -98,14 +96,13 @@
     Ensures(Result() == (ToSeq(object_kind) == seq_class()))
     # post-conditions-end
     # impl-start
-    return ToSeq(object_kind) == seq_class()
+    return ToSeq(object_kind) != seq_class()
     # impl-end
 
 
 def has_return_field_in(fields: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -119,7 +116,6 @@
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(found == has_return_field(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
@@ -136,7 +132,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
     Requires(Acc(list_pred(return_annotation), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -175,7 +170,6 @@
             Invariant(not suppressed_none)
             Invariant(suppressed_none
                       == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
-            Invariant(MustTerminate(len(return_annotation) - j + 1))
             # invariants-end
             Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                    == return_annotation[j])
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
 def suppress_for_kind(object_kind: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(object_kind), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(object_kind), 1 / 2))
@@ -105,7 +103,6 @@
 def has_return_field_in(fields: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -114,15 +111,10 @@
     # impl-start
     found = False
     i = len(fields)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(fields), 1 / 2))
-        Invariant(0 <= i and i <= len(fields))
-        Invariant(found == has_return_field(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
-        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
+        Invariant(1 <= i and i <= len(fields) or len(fields) == 0)
+        Invariant(True)
         if is_return_field(fields[i - 1]):
             found = True
         i = i - 1
@@ -136,7 +128,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
     Requires(Acc(list_pred(return_annotation), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -175,7 +166,6 @@
             Invariant(not suppressed_none)
             Invariant(suppressed_none
                       == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
-            Invariant(MustTerminate(len(return_annotation) - j + 1))
             # invariants-end
             Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                    == return_annotation[j])
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
 def suppress_for_kind(object_kind: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(object_kind), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(object_kind), 1 / 2))
@@ -105,7 +103,6 @@
 def has_return_field_in(fields: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -119,7 +116,6 @@
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(found == has_return_field(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
@@ -136,7 +132,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
     Requires(Acc(list_pred(return_annotation), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -158,35 +153,11 @@
     # post-conditions-end
     # impl-start
     no_return_field = not has_return_field_in(fields)
-    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
     if has_return and no_return_field:
         suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
         if suppressed_none:
             return None
-        # Render the field with the object's own return annotation as content.
-        field = []  # type: List[int]
-        j = 0
-        while j < len(return_annotation):
-            # invariants-start
-            Invariant(Acc(list_pred(return_annotation), 1 / 2))
-            Invariant(Acc(list_pred(field)))
-            Invariant(0 <= j and j <= len(return_annotation))
-            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
-            Invariant(not suppressed_none)
-            Invariant(suppressed_none
-                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
-            Invariant(MustTerminate(len(return_annotation) - j + 1))
-            # invariants-end
-            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
-                   == return_annotation[j])
-            Assert(ToSeq(return_annotation).take(j + 1)
-                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
-            field.append(return_annotation[j])
-            j = j + 1
-        Assert(ToSeq(return_annotation).take(len(return_annotation))
-               == ToSeq(return_annotation))
-        Assert(ToSeq(field) == ToSeq(return_annotation))
-        Assert(has_return and no_return_field and not suppressed_none)
+        field = [78, 111, 110, 101]  # type: List[int]  # fixed 'None' content
         return field
     return None
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
 def suppress_for_kind(object_kind: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(object_kind), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(object_kind), 1 / 2))
@@ -105,7 +103,6 @@
 def has_return_field_in(fields: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -119,7 +116,6 @@
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(found == has_return_field(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
@@ -136,7 +132,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
     Requires(Acc(list_pred(return_annotation), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -158,35 +153,19 @@
     # post-conditions-end
     # impl-start
     no_return_field = not has_return_field_in(fields)
-    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
     if has_return and no_return_field:
-        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
+        suppressed_none = ToSeq(return_annotation) == seq_none() or suppress_void_return
         if suppressed_none:
             return None
-        # Render the field with the object's own return annotation as content.
         field = []  # type: List[int]
         j = 0
         while j < len(return_annotation):
-            # invariants-start
             Invariant(Acc(list_pred(return_annotation), 1 / 2))
             Invariant(Acc(list_pred(field)))
             Invariant(0 <= j and j <= len(return_annotation))
             Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
-            Invariant(not suppressed_none)
-            Invariant(suppressed_none
-                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
-            Invariant(MustTerminate(len(return_annotation) - j + 1))
-            # invariants-end
-            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
-                   == return_annotation[j])
-            Assert(ToSeq(return_annotation).take(j + 1)
-                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
             field.append(return_annotation[j])
             j = j + 1
-        Assert(ToSeq(return_annotation).take(len(return_annotation))
-               == ToSeq(return_annotation))
-        Assert(ToSeq(field) == ToSeq(return_annotation))
-        Assert(has_return and no_return_field and not suppressed_none)
         return field
     return None
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
 def suppress_for_kind(object_kind: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(object_kind), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(object_kind), 1 / 2))
@@ -105,7 +103,6 @@
 def has_return_field_in(fields: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -119,7 +116,6 @@
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(found == has_return_field(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
@@ -136,7 +132,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
     Requires(Acc(list_pred(return_annotation), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -158,35 +153,19 @@
     # post-conditions-end
     # impl-start
     no_return_field = not has_return_field_in(fields)
-    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
     if has_return and no_return_field:
-        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
+        suppressed_none = ToSeq(return_annotation) == seq_none()
         if suppressed_none:
             return None
-        # Render the field with the object's own return annotation as content.
         field = []  # type: List[int]
         j = 0
         while j < len(return_annotation):
-            # invariants-start
             Invariant(Acc(list_pred(return_annotation), 1 / 2))
             Invariant(Acc(list_pred(field)))
             Invariant(0 <= j and j <= len(return_annotation))
             Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
-            Invariant(not suppressed_none)
-            Invariant(suppressed_none
-                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
-            Invariant(MustTerminate(len(return_annotation) - j + 1))
-            # invariants-end
-            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
-                   == return_annotation[j])
-            Assert(ToSeq(return_annotation).take(j + 1)
-                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
             field.append(return_annotation[j])
             j = j + 1
-        Assert(ToSeq(return_annotation).take(len(return_annotation))
-               == ToSeq(return_annotation))
-        Assert(ToSeq(field) == ToSeq(return_annotation))
-        Assert(has_return and no_return_field and not suppressed_none)
         return field
     return None
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
 def suppress_for_kind(object_kind: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(object_kind), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(object_kind), 1 / 2))
@@ -105,7 +103,6 @@
 def has_return_field_in(fields: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -119,7 +116,6 @@
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(found == has_return_field(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
@@ -136,7 +132,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
     Requires(Acc(list_pred(return_annotation), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -157,36 +152,5 @@
                     opt_seq(Result()) == ToSeq(return_annotation)))
     # post-conditions-end
     # impl-start
-    no_return_field = not has_return_field_in(fields)
-    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
-    if has_return and no_return_field:
-        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
-        if suppressed_none:
-            return None
-        # Render the field with the object's own return annotation as content.
-        field = []  # type: List[int]
-        j = 0
-        while j < len(return_annotation):
-            # invariants-start
-            Invariant(Acc(list_pred(return_annotation), 1 / 2))
-            Invariant(Acc(list_pred(field)))
-            Invariant(0 <= j and j <= len(return_annotation))
-            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
-            Invariant(not suppressed_none)
-            Invariant(suppressed_none
-                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
-            Invariant(MustTerminate(len(return_annotation) - j + 1))
-            # invariants-end
-            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
-                   == return_annotation[j])
-            Assert(ToSeq(return_annotation).take(j + 1)
-                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
-            field.append(return_annotation[j])
-            j = j + 1
-        Assert(ToSeq(return_annotation).take(len(return_annotation))
-               == ToSeq(return_annotation))
-        Assert(ToSeq(field) == ToSeq(return_annotation))
-        Assert(has_return and no_return_field and not suppressed_none)
-        return field
     return None
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
 def suppress_for_kind(object_kind: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(object_kind), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(object_kind), 1 / 2))
@@ -105,7 +103,6 @@
 def has_return_field_in(fields: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -119,7 +116,6 @@
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(found == has_return_field(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
@@ -136,7 +132,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
     Requires(Acc(list_pred(return_annotation), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -158,35 +153,11 @@
     # post-conditions-end
     # impl-start
     no_return_field = not has_return_field_in(fields)
-    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
     if has_return and no_return_field:
         suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
         if suppressed_none:
             return None
-        # Render the field with the object's own return annotation as content.
         field = []  # type: List[int]
-        j = 0
-        while j < len(return_annotation):
-            # invariants-start
-            Invariant(Acc(list_pred(return_annotation), 1 / 2))
-            Invariant(Acc(list_pred(field)))
-            Invariant(0 <= j and j <= len(return_annotation))
-            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
-            Invariant(not suppressed_none)
-            Invariant(suppressed_none
-                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
-            Invariant(MustTerminate(len(return_annotation) - j + 1))
-            # invariants-end
-            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
-                   == return_annotation[j])
-            Assert(ToSeq(return_annotation).take(j + 1)
-                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
-            field.append(return_annotation[j])
-            j = j + 1
-        Assert(ToSeq(return_annotation).take(len(return_annotation))
-               == ToSeq(return_annotation))
-        Assert(ToSeq(field) == ToSeq(return_annotation))
-        Assert(has_return and no_return_field and not suppressed_none)
         return field
     return None
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
 def suppress_for_kind(object_kind: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(object_kind), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(object_kind), 1 / 2))
@@ -98,14 +96,13 @@
     Ensures(Result() == (ToSeq(object_kind) == seq_class()))
     # post-conditions-end
     # impl-start
-    return ToSeq(object_kind) == seq_class()
+    return ToSeq(object_kind) == seq_none()
     # impl-end
 
 
 def has_return_field_in(fields: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -119,7 +116,6 @@
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(found == has_return_field(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
@@ -136,7 +132,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(fields), 1 / 2))
     Requires(Acc(list_pred(return_annotation), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -175,7 +170,6 @@
             Invariant(not suppressed_none)
             Invariant(suppressed_none
                       == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
-            Invariant(MustTerminate(len(return_annotation) - j + 1))
             # invariants-end
             Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                    == return_annotation[j])
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-10449.

Behaviour under specification (stated as desired behaviour, not as an edit):

When type-hint information is rendered into a description-style field list and
the rendering target covers every annotation, a synthetic "return type" field
is appended for the documented object's return annotation under these rules:

  (1) A return-type field is appended exactly when the annotation set carries a
      return annotation AND the field list does not already declare a return
      type.

  (2) Documentation of a CONTAINER object (the kind whose body is itself a
      documented entity, e.g. the constructed thing rather than a plain
      callable) must NOT advertise a return type of "no value" (the textual
      annotation ``None``): for such an object, when the return annotation is
      exactly ``None``, no return-type field is appended. Every other return
      annotation, and every non-container object, still appends the field.

  (3) When a return-type field IS appended, its rendered content is the OBJECT'S
      OWN return annotation -- not the annotation of some other documented name.

The dispatch that selects rule (2) requests return-type suppression precisely
for the container object kind.

Strings (object kind, annotation text) are modelled as `List[int]` of Unicode
code points (Nagini bans `str` indexing); the existing field list is modelled
as a `List[int]` of per-field kind codes (a field that already declares a
return type is code 1, any other field is code 0). The pure sequence theory
`PSeq[int]` carries the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *

# axioms-start
# (No axiomatized callees: the changed behaviour is the append decision and its
# rendered content, modelled deeply below. No @ContractOnly is consumed.)
# axioms-end

# pure-start
@Pure
def seq_class() -> PSeq[int]:
    # 'class' as Unicode code points
    return PSeq(99, 108, 97, 115, 115)

@Pure
def seq_none() -> PSeq[int]:
    # 'None' as Unicode code points
    return PSeq(78, 111, 110, 101)

@Pure
def is_return_field(code: int) -> bool:
    """A field already declares a return type iff its kind code is 1."""
    return code == 1

@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The element sequence of an optional rendered field: its code points when
    a field is produced, the empty sequence when none is. Guards the None case
    so the spec can compare a produced field's content without indexing through
    None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)

@Pure
def has_return_field(fields: PSeq[int]) -> bool:
    """Whether the existing field list already declares a return type, i.e.
    some field is a return-type-declaring field. Front-recursive so a single
    unfold is available to callers."""
    if len(fields) == 0:
        return False
    return is_return_field(fields[0]) or has_return_field(fields.drop(1))

# pure-end

def suppress_for_kind(object_kind: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(object_kind), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(object_kind), 1 / 2))
    # Return-type suppression is requested exactly for the container object
    # kind (the one whose textual kind equals 'class').
    Ensures(Result() == (ToSeq(object_kind) == seq_class()))
    # post-conditions-end
    # impl-start
    return ToSeq(object_kind) == seq_class()
    # impl-end

def has_return_field_in(fields: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(fields), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fields), 1 / 2))
    Ensures(Result() == has_return_field(ToSeq(fields)))
    # post-conditions-end
    # impl-start
    found = False
    i = len(fields)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(0 <= i and i <= len(fields))
        Invariant(found == has_return_field(ToSeq(fields).drop(i)))
        # invariants-end
        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
        if is_return_field(fields[i - 1]):
            found = True
        i = i - 1
    return found
    # impl-end

def append_return_type(fields: List[int], has_return: bool,
                       return_annotation: List[int],
                       suppress_void_return: bool) -> Optional[List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(fields), 1 / 2))
    Requires(Acc(list_pred(return_annotation), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fields), 1 / 2))
    Ensures(Acc(list_pred(return_annotation), 1 / 2))
    # A return-type field is appended (Result is not None) exactly when there is
    # a return annotation, the list declares no return type yet, and we are not
    # suppressing a 'None' return type for a container object.
    Ensures(
        (Result() is not None)
        == (has_return
            and not has_return_field(ToSeq(fields))
            and not (suppress_void_return and ToSeq(return_annotation) == seq_none()))
    )
    # When a field IS appended, its content is exactly this object's own return
    # annotation (grounded in the input carrier, never some other name's text).
    Ensures(Implies(Result() is not None, Acc(list_pred(Result()))))
    Ensures(Implies(Result() is not None,
                    opt_seq(Result()) == ToSeq(return_annotation)))
    # post-conditions-end
    # impl-start
    no_return_field = not has_return_field_in(fields)
    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
    if has_return and no_return_field:
        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
        if suppressed_none:
            return None
        # Render the field with the object's own return annotation as content.
        field = []  # type: List[int]
        j = 0
        while j < len(return_annotation):
            # invariants-start
            Invariant(Acc(list_pred(return_annotation), 1 / 2))
            Invariant(Acc(list_pred(field)))
            Invariant(0 <= j and j <= len(return_annotation))
            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
            Invariant(not suppressed_none)
            Invariant(suppressed_none
                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
            # invariants-end
            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                   == return_annotation[j])
            Assert(ToSeq(return_annotation).take(j + 1)
                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
            field.append(return_annotation[j])
            j = j + 1
        Assert(ToSeq(return_annotation).take(len(return_annotation))
               == ToSeq(return_annotation))
        Assert(ToSeq(field) == ToSeq(return_annotation))
        Assert(has_return and no_return_field and not suppressed_none)
        return field
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 9 distinct same-spec wrong impls, all confirmed same-spec (spec_signature byte-identical) and all FAIL Nagini verification => NO CANDIDATE arose, so no refined patch / run_resolve was required by protocol. Positive control (gold model.py) VERIFIES (12.8s). Prepatch reproduced: atk_1 = model_prepatch's append_return_type body (drops the suppressed_none guard, appends unconditionally) — FAILS verification, spec rejects it (append-decision postcondition).

Attacks (all same-spec SAME; all `weakness` exit=2 NOT-A-COUNTEREXAMPLE / does not verify):
- atk_1: prepatch bug — unconditional append (drop suppressed_none guard). FAIL.
- atk_2: suppress_for_kind INVERTED (!= seq_class). FAIL: 'Postcondition of suppress_for_kind might not hold' (Result()==(ToSeq(object_kind)==seq_class())).
- atk_3: has_return_field_in off-by-one boundary (while i>1, skips first field). FAIL (has_return_field postcondition).
- atk_4: ungrounded-oracle echo — append fixed [78,111,110,101] ('None' codepoints) instead of return_annotation. FAIL (content postcondition).
- atk_5: control-flow-effect — suppress on OR instead of AND (suppressed_none = ...==seq_none() OR flag). FAIL (append-decision postcondition).
- atk_6: partial-domain — ignore suppress_void_return flag; suppress whenever annotation==None. FAIL (append-decision postcondition).
- atk_7: always return None (never append). FAIL: 'Postcondition of append_return_type might not hold' (append-decision equality).
- atk_8: append empty content []. FAIL: 'Postcondition ... Implies(Result() is not None, opt_seq(Result())==ToSeq(return_annotation))'.
- atk_9: suppress_for_kind compares to seq_none instead of seq_class. FAIL (suppress_for_kind postcondition).
Sampled direct-verifier runs (atk_2/7/8) confirm the failures are genuine, specific postcondition rejections — not infra noise.

Why no verifying-but-wrong impl exists: the spec's postconditions are COMPLETE equalities pinning every observable of all three functions: suppress_for_kind (Result()==(ToSeq(object_kind)==seq_class())); has_return_field_in (Result()==has_return_field(ToSeq(fields))); append_return_type (both the append-decision iff and the content opt_seq(Result())==ToSeq(return_annotation)). No functional freedom is left inside the impl regions.

Refinement audit: mapping.md §3 and refinement.md §C both declare NO @ContractOnly axioms (confirmed: model.py axioms region empty, only @Pure helpers). G-AX correctly skip/n/a. Every refinement leg is R (type refinement str<->List[int], node<->observed content) or I (identical concrete op); NO A-consumed/A-reference legs (vacuously satisfied — nothing to correspond to a real callee) and NO kind-3 unexpressible-changed-op leg. The changed behaviour (suppression gate A4, kind dispatch B2, content grounding A5) is spelled out directly in Nagini logic, and independently cross-checked by G-CONF (conformance_check.py, meta.json G-CONF=pass) differentially against the real patched sphinx.ext.autodoc.typehints.modify_field_list / merge_typehints over >=1e5 inputs. meta.json gates all pass. Model<->patch correspondence holds.

Protocol: attack verifications run concurrently in background batches of 3 (each Nagini check spawns JVM+Z3), collected — schedule only, pass criteria unchanged. >=5 attacks run, none breaks the spec => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-10449.

Behaviour under specification (stated as desired behaviour, not as an edit):

When type-hint information is rendered into a description-style field list and
the rendering target covers every annotation, a synthetic "return type" field
is appended for the documented object's return annotation under these rules:

  (1) A return-type field is appended exactly when the annotation set carries a
      return annotation AND the field list does not already declare a return
      type.

  (2) Documentation of a CONTAINER object (the kind whose body is itself a
      documented entity, e.g. the constructed thing rather than a plain
      callable) must NOT advertise a return type of "no value" (the textual
      annotation ``None``): for such an object, when the return annotation is
      exactly ``None``, no return-type field is appended. Every other return
      annotation, and every non-container object, still appends the field.

  (3) When a return-type field IS appended, its rendered content is the OBJECT'S
      OWN return annotation -- not the annotation of some other documented name.

The dispatch that selects rule (2) requests return-type suppression precisely
for the container object kind.

Strings (object kind, annotation text) are modelled as `List[int]` of Unicode
code points (Nagini bans `str` indexing); the existing field list is modelled
as a `List[int]` of per-field kind codes (a field that already declares a
return type is code 1, any other field is code 0). The pure sequence theory
`PSeq[int]` carries the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *

# axioms-start
# (No axiomatized callees: the changed behaviour is the append decision and its
# rendered content, modelled deeply below. No @ContractOnly is consumed.)
# axioms-end

# pure-start
@Pure
def seq_class() -> PSeq[int]:
    # 'class' as Unicode code points
    return PSeq(99, 108, 97, 115, 115)

@Pure
def seq_none() -> PSeq[int]:
    # 'None' as Unicode code points
    return PSeq(78, 111, 110, 101)

@Pure
def is_return_field(code: int) -> bool:
    """A field already declares a return type iff its kind code is 1."""
    return code == 1

@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The element sequence of an optional rendered field: its code points when
    a field is produced, the empty sequence when none is. Guards the None case
    so the spec can compare a produced field's content without indexing through
    None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)

@Pure
def has_return_field(fields: PSeq[int]) -> bool:
    """Whether the existing field list already declares a return type, i.e.
    some field is a return-type-declaring field. Front-recursive so a single
    unfold is available to callers."""
    if len(fields) == 0:
        return False
    return is_return_field(fields[0]) or has_return_field(fields.drop(1))

# pure-end

def suppress_for_kind(object_kind: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(object_kind), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(object_kind), 1 / 2))
    # Return-type suppression is requested exactly for the container object
    # kind (the one whose textual kind equals 'class').
    Ensures(Result() == (ToSeq(object_kind) == seq_class()))
    # post-conditions-end
    # impl-start
    return ToSeq(object_kind) == seq_class()
    # impl-end

def has_return_field_in(fields: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(fields), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fields), 1 / 2))
    Ensures(Result() == has_return_field(ToSeq(fields)))
    # post-conditions-end
    # impl-start
    found = False
    i = len(fields)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(0 <= i and i <= len(fields))
        Invariant(found == has_return_field(ToSeq(fields).drop(i)))
        # invariants-end
        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
        if is_return_field(fields[i - 1]):
            found = True
        i = i - 1
    return found
    # impl-end

def append_return_type(fields: List[int], has_return: bool,
                       return_annotation: List[int],
                       suppress_void_return: bool) -> Optional[List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(fields), 1 / 2))
    Requires(Acc(list_pred(return_annotation), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fields), 1 / 2))
    Ensures(Acc(list_pred(return_annotation), 1 / 2))
    # A return-type field is appended (Result is not None) exactly when there is
    # a return annotation, the list declares no return type yet, and we are not
    # suppressing a 'None' return type for a container object.
    Ensures(
        (Result() is not None)
        == (has_return
            and not has_return_field(ToSeq(fields))
            and not (suppress_void_return and ToSeq(return_annotation) == seq_none()))
    )
    # When a field IS appended, its content is exactly this object's own return
    # annotation (grounded in the input carrier, never some other name's text).
    Ensures(Implies(Result() is not None, Acc(list_pred(Result()))))
    Ensures(Implies(Result() is not None,
                    opt_seq(Result()) == ToSeq(return_annotation)))
    # post-conditions-end
    # impl-start
    no_return_field = not has_return_field_in(fields)
    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
    if has_return and no_return_field:
        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
        if suppressed_none:
            return None
        # Render the field with the object's own return annotation as content.
        field = []  # type: List[int]
        j = 0
        while j < len(return_annotation):
            # invariants-start
            Invariant(Acc(list_pred(return_annotation), 1 / 2))
            Invariant(Acc(list_pred(field)))
            Invariant(0 <= j and j <= len(return_annotation))
            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
            Invariant(not suppressed_none)
            Invariant(suppressed_none
                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
            # invariants-end
            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                   == return_annotation[j])
            Assert(ToSeq(return_annotation).take(j + 1)
                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
            field.append(return_annotation[j])
            j = j + 1
        Assert(ToSeq(return_annotation).take(len(return_annotation))
               == ToSeq(return_annotation))
        Assert(ToSeq(field) == ToSeq(return_annotation))
        Assert(has_return and no_return_field and not suppressed_none)
        return field
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 9 distinct same-spec wrong impls, all confirmed same-spec (spec_signature byte-identical) and all FAIL Nagini verification => NO CANDIDATE arose, so no refined patch / run_resolve was required by protocol. Positive control (gold model.py) VERIFIES (12.8s). Prepatch reproduced: atk_1 = model_prepatch's append_return_type body (drops the suppressed_none guard, appends unconditionally) — FAILS verification, spec rejects it (append-decision postcondition).

Attacks (all same-spec SAME; all `weakness` exit=2 NOT-A-COUNTEREXAMPLE / does not verify):
- atk_1: prepatch bug — unconditional append (drop suppressed_none guard). FAIL.
- atk_2: suppress_for_kind INVERTED (!= seq_class). FAIL: 'Postcondition of suppress_for_kind might not hold' (Result()==(ToSeq(object_kind)==seq_class())).
- atk_3: has_return_field_in off-by-one boundary (while i>1, skips first field). FAIL (has_return_field postcondition).
- atk_4: ungrounded-oracle echo — append fixed [78,111,110,101] ('None' codepoints) instead of return_annotation. FAIL (content postcondition).
- atk_5: control-flow-effect — suppress on OR instead of AND (suppressed_none = ...==seq_none() OR flag). FAIL (append-decision postcondition).
- atk_6: partial-domain — ignore suppress_void_return flag; suppress whenever annotation==None. FAIL (append-decision postcondition).
- atk_7: always return None (never append). FAIL: 'Postcondition of append_return_type might not hold' (append-decision equality).
- atk_8: append empty content []. FAIL: 'Postcondition ... Implies(Result() is not None, opt_seq(Result())==ToSeq(return_annotation))'.
- atk_9: suppress_for_kind compares to seq_none instead of seq_class. FAIL (suppress_for_kind postcondition).
Sampled direct-verifier runs (atk_2/7/8) confirm the failures are genuine, specific postcondition rejections — not infra noise.

Why no verifying-but-wrong impl exists: the spec's postconditions are COMPLETE equalities pinning every observable of all three functions: suppress_for_kind (Result()==(ToSeq(object_kind)==seq_class())); has_return_field_in (Result()==has_return_field(ToSeq(fields))); append_return_type (both the append-decision iff and the content opt_seq(Result())==ToSeq(return_annotation)). No functional freedom is left inside the impl regions.

Refinement audit: mapping.md §3 and refinement.md §C both declare NO @ContractOnly axioms (confirmed: model.py axioms region empty, only @Pure helpers). G-AX correctly skip/n/a. Every refinement leg is R (type refinement str<->List[int], node<->observed content) or I (identical concrete op); NO A-consumed/A-reference legs (vacuously satisfied — nothing to correspond to a real callee) and NO kind-3 unexpressible-changed-op leg. The changed behaviour (suppression gate A4, kind dispatch B2, content grounding A5) is spelled out directly in Nagini logic, and independently cross-checked by G-CONF (conformance_check.py, meta.json G-CONF=pass) differentially against the real patched sphinx.ext.autodoc.typehints.modify_field_list / merge_typehints over >=1e5 inputs. meta.json gates all pass. Model<->patch correspondence holds.

Protocol: attack verifications run concurrently in background batches of 3 (each Nagini check spawns JVM+Z3), collected — schedule only, pass criteria unchanged. >=5 attacks run, none breaks the spec => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) audit of sphinx-doc__sphinx-10449 nagini bundle. The modeled function `append_return_type` (+ `suppress_for_kind`, `has_return_field_in`) specifies the return-type emit block of the real patched `sphinx.ext.autodoc.typehints.modify_field_list`/`merge_typehints`.

EMPIRICAL: Set up sphinx 4.5.0 / docutils 0.17.1 over the patched worktree (git diff confirms patch.diff applied: suppress_rtype param + `if annotation=='None' and suppress_rtype: return` + objtype=='class' dispatch). Ran the bundle's conformance_check.py against the REAL patched functions: G-CONF OK, 100882 inputs (boundary grids + 70k flag-level + 30k kind-level fuzz, seed 10449), ZERO disagreements. The contract-stripped model impl equals the real callee across both tiers.

SPEC-DRIFT PROBE (main attack vector): The refinement abstracts the docutils field list to `List[int]` of per-field kind codes where code 1 = 'a field that already declares a return type' and the bijection is `'return' in arguments ⇔ has_return_field(fields)` (mapping.md §2). I probed whether this abstraction is TOO STRONG by noting the real code sets arguments['return'] not only from an `rtype` field but also from `:type return:` and `:param return:` fields. Direct real-repo test: fields ['type return'] / ['param return'] with has_return=True, ann='int', suppress=False => real does NOT append an rtype field (arguments['return'] is set). Under a NAIVE reading these would encode to code 0 and the model spec would predict append=True (apparent divergence).

HOWEVER this is not a spec defect: those fields DO declare a return type, so their FAITHFUL refined encoding is code 1, not code 0 — exactly matching the model. I verified completeness: the real append decision reads ONLY (`'return' in annotations`, `'return' in arguments`, `annotation=='None' and suppress_rtype`); every field realization partitions cleanly into code-1 (declares return: rtype / type return / param return → real suppresses) vs code-0 (param alpha, type beta, returns, raises, type foo → real appends).

No field induces an observable the model cannot express, and the content postcondition `opt_seq(Result())==ToSeq(return_annotation)` matches the gold's `annotation=annotations['return']` binding (the object's OWN return annotation, correcting the pre-patch leftover-loop-var bug).

Other spec facets checked: suppress_for_kind == (kind=='class') matches the gold objtype=='class' dispatch exactly; the None-suppression conjunction gate (A4) matches; non-'class' kinds and non-'None' annotations always append (verified in kind-level fuzz). No @ContractOnly axioms (G-AX n/a), so no axiom-fidelity attack surface. Spec markers/regions intact and consistent between model.py and model_prepatch.py (prepatch drops exactly the None-suppression guard, appends unconditionally — the intended G-DIFF sensitivity).

Conclusion: the spec neither over-constrains nor drifts from real repo behavior on any Requires-satisfying input; the modeled function agrees with the real callee everywhere tested (100k+ inputs) and on the targeted edge cases. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (no diff markers, no gold-patch line reproduced, no patched file path sphinx/ext/autodoc/typehints.py, no patched symbols modify_field_list/merge_typehints/suppress_rtype/insert_field_list embedded in spec-view identifiers or comments, no bug/fix narration). Semantic review: the spec view describes desired behavior abstractly. Its discriminating rule (2) — a 'container object' with return annotation exactly None gets no return-type field — is a direct formalization of the PUBLIC problem_statement, which already states the object is a class, the annotation is `-> None`, and the expected behavior is 'no return type listed for the class'. So rule (2) reveals nothing beyond the task. Rule (1) is generic pre-existing behavior. Rule (3) (appended content = the object's own return annotation) is the only element not literally in the problem statement, but it is stated as an abstract positive correctness property — it names no repo symbol, file, parameter, loop variable, or diff line, and does not reproduce any gold hunk. A solver still must locate the code (modify_field_list / merge_typehints) and implement the fix; the spec view does not trivialize gold-patch reconstruction. Not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).