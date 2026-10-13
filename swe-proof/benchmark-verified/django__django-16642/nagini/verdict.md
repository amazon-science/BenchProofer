# P2 adversarial audit — django__django-16642

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -151,7 +150,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(content_type), 1 / 2))
     Requires(Acc(list_pred(encoding), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content_type), 1 / 2))
@@ -180,21 +178,14 @@
     # post-conditions-end
     # impl-start
     enc = ToSeq(encoding)
-    if enc == tok_br():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 114, 111, 116, 108, 105]
     if enc == tok_bzip2():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 122, 105, 112]
     if enc == tok_compress():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
     if enc == tok_gzip():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 103, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 103, 122, 105, 112]
     if enc == tok_xz():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 120, 122]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 120, 122]
     result = []  # type: List[int]
     i = 0
     while i < len(content_type):
@@ -203,7 +194,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(content_type))
         Invariant(ToSeq(result) == ToSeq(content_type).take(i))
-        Invariant(MustTerminate(len(content_type) - i + 1))
         # invariants-end
         result = result + [content_type[i]]
         Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -151,7 +150,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(content_type), 1 / 2))
     Requires(Acc(list_pred(encoding), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content_type), 1 / 2))
@@ -181,20 +179,15 @@
     # impl-start
     enc = ToSeq(encoding)
     if enc == tok_br():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 114, 111, 116, 108, 105]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 122, 105, 112]
     if enc == tok_bzip2():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 122, 105, 112]
     if enc == tok_compress():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
     if enc == tok_gzip():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 103, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 103, 122, 105, 112]
     if enc == tok_xz():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 120, 122]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 120, 122]
     result = []  # type: List[int]
     i = 0
     while i < len(content_type):
@@ -203,7 +196,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(content_type))
         Invariant(ToSeq(result) == ToSeq(content_type).take(i))
-        Invariant(MustTerminate(len(content_type) - i + 1))
         # invariants-end
         result = result + [content_type[i]]
         Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -151,7 +150,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(content_type), 1 / 2))
     Requires(Acc(list_pred(encoding), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content_type), 1 / 2))
@@ -181,20 +179,15 @@
     # impl-start
     enc = ToSeq(encoding)
     if enc == tok_br():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 114, 111, 116, 108, 105]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 114, 111, 116, 108, 105]
     if enc == tok_bzip2():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 122, 105, 112]
     if enc == tok_compress():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
     if enc == tok_gzip():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 103, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 120, 122]
     if enc == tok_xz():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 120, 122]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 103, 122, 105, 112]
     result = []  # type: List[int]
     i = 0
     while i < len(content_type):
@@ -203,7 +196,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(content_type))
         Invariant(ToSeq(result) == ToSeq(content_type).take(i))
-        Invariant(MustTerminate(len(content_type) - i + 1))
         # invariants-end
         result = result + [content_type[i]]
         Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -151,7 +150,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(content_type), 1 / 2))
     Requires(Acc(list_pred(encoding), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content_type), 1 / 2))
@@ -181,20 +179,15 @@
     # impl-start
     enc = ToSeq(encoding)
     if enc == tok_br():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 114, 111, 116, 108, 105]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 114, 111, 116, 108, 105]
     if enc == tok_bzip2():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 122, 105, 112]
     if enc == tok_compress():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
     if enc == tok_gzip():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 103, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 103, 122, 105, 112]
     if enc == tok_xz():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 120, 122]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 120, 122]
     result = []  # type: List[int]
     i = 0
     while i < len(content_type):
@@ -203,12 +196,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(content_type))
         Invariant(ToSeq(result) == ToSeq(content_type).take(i))
-        Invariant(MustTerminate(len(content_type) - i + 1))
         # invariants-end
         result = result + [content_type[i]]
         Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
                == ToSeq(content_type).take(i + 1))
         i = i + 1
     Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
-    return result
+    return result + [0]
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -151,7 +150,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(content_type), 1 / 2))
     Requires(Acc(list_pred(encoding), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content_type), 1 / 2))
@@ -181,20 +179,13 @@
     # impl-start
     enc = ToSeq(encoding)
     if enc == tok_br():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 114, 111, 116, 108, 105]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 114, 111, 116, 108, 105]
     if enc == tok_bzip2():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 122, 105, 112]
-    if enc == tok_compress():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 122, 105, 112]
     if enc == tok_gzip():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 103, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 103, 122, 105, 112]
     if enc == tok_xz():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 120, 122]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 120, 122]
     result = []  # type: List[int]
     i = 0
     while i < len(content_type):
@@ -203,7 +194,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(content_type))
         Invariant(ToSeq(result) == ToSeq(content_type).take(i))
-        Invariant(MustTerminate(len(content_type) - i + 1))
         # invariants-end
         result = result + [content_type[i]]
         Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -151,7 +150,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(content_type), 1 / 2))
     Requires(Acc(list_pred(encoding), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content_type), 1 / 2))
@@ -180,21 +178,12 @@
     # post-conditions-end
     # impl-start
     enc = ToSeq(encoding)
-    if enc == tok_br():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 114, 111, 116, 108, 105]
     if enc == tok_bzip2():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 122, 105, 112]
-    if enc == tok_compress():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 98, 122, 105, 112]
     if enc == tok_gzip():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 103, 122, 105, 112]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 103, 122, 105, 112]
     if enc == tok_xz():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 120, 122]
+        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 45, 120, 122]
     result = []  # type: List[int]
     i = 0
     while i < len(content_type):
@@ -203,7 +192,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(content_type))
         Invariant(ToSeq(result) == ToSeq(content_type).take(i))
-        Invariant(MustTerminate(len(content_type) - i + 1))
         # invariants-end
         result = result + [content_type[i]]
         Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -151,7 +150,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(content_type), 1 / 2))
     Requires(Acc(list_pred(encoding), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content_type), 1 / 2))
@@ -180,21 +178,8 @@
     # post-conditions-end
     # impl-start
     enc = ToSeq(encoding)
-    if enc == tok_br():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 114, 111, 116, 108, 105]
-    if enc == tok_bzip2():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 98, 122, 105, 112]
-    if enc == tok_compress():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
-    if enc == tok_gzip():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 103, 122, 105, 112]
-    if enc == tok_xz():
-        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-                47, 120, 45, 120, 122]
+    if is_known_encoding(enc):
+        return []
     result = []  # type: List[int]
     i = 0
     while i < len(content_type):
@@ -203,7 +188,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(content_type))
         Invariant(ToSeq(result) == ToSeq(content_type).take(i))
-        Invariant(MustTerminate(len(content_type) - i + 1))
         # invariants-end
         result = result + [content_type[i]]
         Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16642.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a file response derives its content type automatically, the content type
  guessed from the file name is paired with a detected compression scheme (the
  "encoding"). Serving a compressed payload under the underlying (uncompressed)
  content type lets user agents silently decompress it, which is undesirable.
  The desired behaviour is therefore: every recognised compression scheme is
  mapped to its OWN dedicated content type, and the originally guessed content
  type is used only when no compression scheme was recognised.

  The set of recognised compression schemes that must each be mapped to a
  dedicated content type is exactly:

      "br"       -> "application/x-brotli"
      "bzip2"    -> "application/x-bzip"
      "compress" -> "application/x-compress"
      "gzip"     -> "application/gzip"
      "xz"       -> "application/x-xz"

  For any other encoding token (including the empty token meaning "no
  compression detected") the guessed content type passes through unchanged.

Strings (the encoding token and the content-type values) are modelled as
`List[int]` of Unicode code points (Nagini bans `str` indexing); the
specification is carried by the pure sequence theory `PSeq[int]`.

There are no axiomatized callees: the modelled operation is the table lookup
itself, which is fully expressible. The function receives the already-guessed
(content_type, encoding) pair as inputs; how that pair is obtained is unchanged
by the behaviour under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none: the modelled table-lookup operation is fully expressible; the
#  unchanged producer of the (content_type, encoding) pair is not consumed.)
# axioms-end

# pure-start
@Pure
def tok_br() -> PSeq[int]:
    # "br"
    return PSeq(98, 114)

@Pure
def tok_bzip2() -> PSeq[int]:
    # "bzip2"
    return PSeq(98, 122, 105, 112, 50)

@Pure
def tok_compress() -> PSeq[int]:
    # "compress"
    return PSeq(99, 111, 109, 112, 114, 101, 115, 115)

@Pure
def tok_gzip() -> PSeq[int]:
    # "gzip"
    return PSeq(103, 122, 105, 112)

@Pure
def tok_xz() -> PSeq[int]:
    # "xz"
    return PSeq(120, 122)

@Pure
def ct_brotli() -> PSeq[int]:
    # "application/x-brotli"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105)

@Pure
def ct_bzip() -> PSeq[int]:
    # "application/x-bzip"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112)

@Pure
def ct_compress() -> PSeq[int]:
    # "application/x-compress"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115)

@Pure
def ct_gzip() -> PSeq[int]:
    # "application/gzip"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112)

@Pure
def ct_xz() -> PSeq[int]:
    # "application/x-xz"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122)

@Pure
def is_known_encoding(enc: PSeq[int]) -> bool:
    """True iff the encoding token is one of the recognised compression
    schemes that must each receive a dedicated content type."""
    return (enc == tok_br() or enc == tok_bzip2() or enc == tok_compress()
            or enc == tok_gzip() or enc == tok_xz())

@Pure
def dedicated_type(enc: PSeq[int]) -> PSeq[int]:
    """The dedicated content type for a recognised compression scheme.

    Defined (non-empty) on exactly the five recognised tokens; the empty
    sequence stands for "no dedicated type" on any other token."""
    if enc == tok_br():
        return ct_brotli()
    if enc == tok_bzip2():
        return ct_bzip()
    if enc == tok_compress():
        return ct_compress()
    if enc == tok_gzip():
        return ct_gzip()
    if enc == tok_xz():
        return ct_xz()
    return PSeq(0).take(0)

@Pure
def resolved_type(content_type: PSeq[int], enc: PSeq[int]) -> PSeq[int]:
    """The content type after applying the compression-scheme table: the
    dedicated type for a recognised scheme, otherwise the guessed type."""
    if is_known_encoding(enc):
        return dedicated_type(enc)
    return content_type
# pure-end

def select_content_type(content_type: List[int], encoding: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(content_type), 1 / 2))
    Requires(Acc(list_pred(encoding), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content_type), 1 / 2))
    Ensures(Acc(list_pred(encoding), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the table lookup: dedicated type if the encoding is one of
    # the recognised compression schemes, otherwise the guessed content type.
    Ensures(ToSeq(Result()) == resolved_type(ToSeq(content_type), ToSeq(encoding)))
    # Every recognised compression scheme maps to its dedicated, non-empty
    # content type (so a compressed payload is never served under the guessed
    # uncompressed type). The two clauses for "br" and "compress" carry the
    # discriminating behaviour.
    Ensures(Implies(ToSeq(encoding) == tok_br(),
                    ToSeq(Result()) == ct_brotli()))
    Ensures(Implies(ToSeq(encoding) == tok_bzip2(),
                    ToSeq(Result()) == ct_bzip()))
    Ensures(Implies(ToSeq(encoding) == tok_compress(),
                    ToSeq(Result()) == ct_compress()))
    Ensures(Implies(ToSeq(encoding) == tok_gzip(),
                    ToSeq(Result()) == ct_gzip()))
    Ensures(Implies(ToSeq(encoding) == tok_xz(),
                    ToSeq(Result()) == ct_xz()))
    # When the encoding is not a recognised scheme the guessed type is kept.
    Ensures(Implies(not is_known_encoding(ToSeq(encoding)),
                    ToSeq(Result()) == ToSeq(content_type)))
    # post-conditions-end
    # impl-start
    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(ToSeq(result) == ToSeq(content_type).take(i))
        # invariants-end
        result = result + [content_type[i]]
        Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
               == ToSeq(content_type).take(i + 1))
        i = i + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is FULLY FUNCTIONAL: postcondition 1 pins Result to the total pure function resolved_type(ToSeq(content_type),ToSeq(encoding)) [model.py:160], re-pinned by five per-scheme Implies clauses (br/bzip2/compress/gzip/xz) and the not-is_known_encoding passthrough clause. No behavioral freedom => no room for a verifying-but-wrong impl.

ATTACKS (all editing ONLY the impl region, byte-identical outside it; confirmed via diff and `adversary same-spec` -> SAME exit 0 for all 7):
- atk_1 (partial-domain): drop the tok_br branch -> falls through to passthrough, returns content_type for enc=='br'. Half the prepatch bug.
- atk_2 (wrong-value/ungrounded-oracle): enc=='br' returns ct_bzip.
- atk_3 (value swap): gzip<->xz content types swapped.
- atk_4 (boundary): passthrough returns content_type + [0] (extra trailing byte).
- atk_5 (control-flow-effect): drop the tok_compress branch. Other half of prepatch bug.
- atk_6 (prepatch reproduction): drop BOTH tok_br and tok_compress -> exact pre-patch table {bzip2,gzip,xz}.
- atk_7 (ungrounded-oracle echo): return [] (dedicated_type's empty-sentinel) for every is_known_encoding, passthrough otherwise.

Commands run from project root with python:
python -m swebench_unified.adversary same-spec nagini django__django-16642 <atk_N.py>  (all -> SAME, exit 0)
python -m swebench_unified.adversary weakness  nagini django__django-16642 <atk_N.py>  (all -> NOT-A-COUNTEREXAMPLE 'attack does not verify', exit 2)
bash scripts/nagini_verify.sh positive_control.py  -> Verification successful, 16.13s, exit 0

RESULTS: NO CANDIDATE emerged (0/7 verify), so no faithful-patch resolve run was warranted. Direct `adversary verify` on representatives confirms rejections are GENUINE functional-postcondition failures, not incidental/masking errors:
  atk_1: FAILED 19.3s -- 'Postcondition ... Assertion (ToSeq(Result()) == resolved_type(...)) might not hold' at model line 160.
  atk_4: FAILED 16.7s -- same postcondition at line 160.
  atk_7: FAILED 13.2s -- 'Postcondition ... return type is correct might not hold' (Acc(list_pred(Result())) / functional clause).
Positive control (unmodified model.py copy) VERIFIES (16.13s).

REFINEMENT.MD A-LEG AUDIT: 4 legs A1(R)/A2(R)/A3(I+R)/A4(I+R); NO kind-3. refinement.md §C and mapping.md §3 assert no consumed axioms and no A-reference deep models -- mechanically confirmed: grep finds no @ContractOnly, axioms region is empty (comment only), all 12 @Pure helpers (tok_*, ct_*, is_known_encoding, dedicated_type, resolved_type) have concrete constructive bodies (no opaque callees). Thus there are NO A-legs whose callee correspondence could drift; the sole trust point is refinement fidelity. axiom_check.py PASSES (exit 0): re-confirms the five tok_*/ct_* code-point encodings byte-for-byte against the real dict keys/values, that mimetypes.guess_type emits 'br'/'compress' for *.br/*.Z, and dict.get==resolved_type over 5 schemes x 5 cts + 20000 fuzz. Gold patch (dataset) adds exactly the 'br' and 'compress' dict keys; A3/A4 correspondence to {...}.get(encoding, content_type) holds.

prepatch_reproduced=true: atk_6 reproduces the recorded prepatch bug (model_prepatch.py drops tok_br+tok_compress) and is correctly rejected by the functional postcondition, i.e. the spec senses the change (matches recorded G-DIFF fail at model_prepatch.py:160).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16642.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a file response derives its content type automatically, the content type
  guessed from the file name is paired with a detected compression scheme (the
  "encoding"). Serving a compressed payload under the underlying (uncompressed)
  content type lets user agents silently decompress it, which is undesirable.
  The desired behaviour is therefore: every recognised compression scheme is
  mapped to its OWN dedicated content type, and the originally guessed content
  type is used only when no compression scheme was recognised.

  The set of recognised compression schemes that must each be mapped to a
  dedicated content type is exactly:

      "br"       -> "application/x-brotli"
      "bzip2"    -> "application/x-bzip"
      "compress" -> "application/x-compress"
      "gzip"     -> "application/gzip"
      "xz"       -> "application/x-xz"

  For any other encoding token (including the empty token meaning "no
  compression detected") the guessed content type passes through unchanged.

Strings (the encoding token and the content-type values) are modelled as
`List[int]` of Unicode code points (Nagini bans `str` indexing); the
specification is carried by the pure sequence theory `PSeq[int]`.

There are no axiomatized callees: the modelled operation is the table lookup
itself, which is fully expressible. The function receives the already-guessed
(content_type, encoding) pair as inputs; how that pair is obtained is unchanged
by the behaviour under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none: the modelled table-lookup operation is fully expressible; the
#  unchanged producer of the (content_type, encoding) pair is not consumed.)
# axioms-end

# pure-start
@Pure
def tok_br() -> PSeq[int]:
    # "br"
    return PSeq(98, 114)

@Pure
def tok_bzip2() -> PSeq[int]:
    # "bzip2"
    return PSeq(98, 122, 105, 112, 50)

@Pure
def tok_compress() -> PSeq[int]:
    # "compress"
    return PSeq(99, 111, 109, 112, 114, 101, 115, 115)

@Pure
def tok_gzip() -> PSeq[int]:
    # "gzip"
    return PSeq(103, 122, 105, 112)

@Pure
def tok_xz() -> PSeq[int]:
    # "xz"
    return PSeq(120, 122)

@Pure
def ct_brotli() -> PSeq[int]:
    # "application/x-brotli"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105)

@Pure
def ct_bzip() -> PSeq[int]:
    # "application/x-bzip"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112)

@Pure
def ct_compress() -> PSeq[int]:
    # "application/x-compress"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115)

@Pure
def ct_gzip() -> PSeq[int]:
    # "application/gzip"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112)

@Pure
def ct_xz() -> PSeq[int]:
    # "application/x-xz"
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122)

@Pure
def is_known_encoding(enc: PSeq[int]) -> bool:
    """True iff the encoding token is one of the recognised compression
    schemes that must each receive a dedicated content type."""
    return (enc == tok_br() or enc == tok_bzip2() or enc == tok_compress()
            or enc == tok_gzip() or enc == tok_xz())

@Pure
def dedicated_type(enc: PSeq[int]) -> PSeq[int]:
    """The dedicated content type for a recognised compression scheme.

    Defined (non-empty) on exactly the five recognised tokens; the empty
    sequence stands for "no dedicated type" on any other token."""
    if enc == tok_br():
        return ct_brotli()
    if enc == tok_bzip2():
        return ct_bzip()
    if enc == tok_compress():
        return ct_compress()
    if enc == tok_gzip():
        return ct_gzip()
    if enc == tok_xz():
        return ct_xz()
    return PSeq(0).take(0)

@Pure
def resolved_type(content_type: PSeq[int], enc: PSeq[int]) -> PSeq[int]:
    """The content type after applying the compression-scheme table: the
    dedicated type for a recognised scheme, otherwise the guessed type."""
    if is_known_encoding(enc):
        return dedicated_type(enc)
    return content_type
# pure-end

def select_content_type(content_type: List[int], encoding: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(content_type), 1 / 2))
    Requires(Acc(list_pred(encoding), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content_type), 1 / 2))
    Ensures(Acc(list_pred(encoding), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the table lookup: dedicated type if the encoding is one of
    # the recognised compression schemes, otherwise the guessed content type.
    Ensures(ToSeq(Result()) == resolved_type(ToSeq(content_type), ToSeq(encoding)))
    # Every recognised compression scheme maps to its dedicated, non-empty
    # content type (so a compressed payload is never served under the guessed
    # uncompressed type). The two clauses for "br" and "compress" carry the
    # discriminating behaviour.
    Ensures(Implies(ToSeq(encoding) == tok_br(),
                    ToSeq(Result()) == ct_brotli()))
    Ensures(Implies(ToSeq(encoding) == tok_bzip2(),
                    ToSeq(Result()) == ct_bzip()))
    Ensures(Implies(ToSeq(encoding) == tok_compress(),
                    ToSeq(Result()) == ct_compress()))
    Ensures(Implies(ToSeq(encoding) == tok_gzip(),
                    ToSeq(Result()) == ct_gzip()))
    Ensures(Implies(ToSeq(encoding) == tok_xz(),
                    ToSeq(Result()) == ct_xz()))
    # When the encoding is not a recognised scheme the guessed type is kept.
    Ensures(Implies(not is_known_encoding(ToSeq(encoding)),
                    ToSeq(Result()) == ToSeq(content_type)))
    # post-conditions-end
    # impl-start
    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(ToSeq(result) == ToSeq(content_type).take(i))
        # invariants-end
        result = result + [content_type[i]]
        Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
               == ToSeq(content_type).take(i + 1))
        i = i + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is FULLY FUNCTIONAL: postcondition 1 pins Result to the total pure function resolved_type(ToSeq(content_type),ToSeq(encoding)) [model.py:160], re-pinned by five per-scheme Implies clauses (br/bzip2/compress/gzip/xz) and the not-is_known_encoding passthrough clause. No behavioral freedom => no room for a verifying-but-wrong impl.

ATTACKS (all editing ONLY the impl region, byte-identical outside it; confirmed via diff and `adversary same-spec` -> SAME exit 0 for all 7):
- atk_1 (partial-domain): drop the tok_br branch -> falls through to passthrough, returns content_type for enc=='br'. Half the prepatch bug.
- atk_2 (wrong-value/ungrounded-oracle): enc=='br' returns ct_bzip.
- atk_3 (value swap): gzip<->xz content types swapped.
- atk_4 (boundary): passthrough returns content_type + [0] (extra trailing byte).
- atk_5 (control-flow-effect): drop the tok_compress branch. Other half of prepatch bug.
- atk_6 (prepatch reproduction): drop BOTH tok_br and tok_compress -> exact pre-patch table {bzip2,gzip,xz}.
- atk_7 (ungrounded-oracle echo): return [] (dedicated_type's empty-sentinel) for every is_known_encoding, passthrough otherwise.

Commands run from project root with python:
python -m swebench_unified.adversary same-spec nagini django__django-16642 <atk_N.py>  (all -> SAME, exit 0)
python -m swebench_unified.adversary weakness  nagini django__django-16642 <atk_N.py>  (all -> NOT-A-COUNTEREXAMPLE 'attack does not verify', exit 2)
bash scripts/nagini_verify.sh positive_control.py  -> Verification successful, 16.13s, exit 0

RESULTS: NO CANDIDATE emerged (0/7 verify), so no faithful-patch resolve run was warranted. Direct `adversary verify` on representatives confirms rejections are GENUINE functional-postcondition failures, not incidental/masking errors:
  atk_1: FAILED 19.3s -- 'Postcondition ... Assertion (ToSeq(Result()) == resolved_type(...)) might not hold' at model line 160.
  atk_4: FAILED 16.7s -- same postcondition at line 160.
  atk_7: FAILED 13.2s -- 'Postcondition ... return type is correct might not hold' (Acc(list_pred(Result())) / functional clause).
Positive control (unmodified model.py copy) VERIFIES (16.13s).

REFINEMENT.MD A-LEG AUDIT: 4 legs A1(R)/A2(R)/A3(I+R)/A4(I+R); NO kind-3. refinement.md §C and mapping.md §3 assert no consumed axioms and no A-reference deep models -- mechanically confirmed: grep finds no @ContractOnly, axioms region is empty (comment only), all 12 @Pure helpers (tok_*, ct_*, is_known_encoding, dedicated_type, resolved_type) have concrete constructive bodies (no opaque callees). Thus there are NO A-legs whose callee correspondence could drift; the sole trust point is refinement fidelity. axiom_check.py PASSES (exit 0): re-confirms the five tok_*/ct_* code-point encodings byte-for-byte against the real dict keys/values, that mimetypes.guess_type emits 'br'/'compress' for *.br/*.Z, and dict.get==resolved_type over 5 schemes x 5 cts + 20000 fuzz. Gold patch (dataset) adds exactly the 'br' and 'compress' dict keys; A3/A4 correspondence to {...}.get(encoding, content_type) holds.

prepatch_reproduced=true: atk_6 reproduces the recorded prepatch bug (model_prepatch.py drops tok_br+tok_compress) and is correctly rejected by the functional postcondition, i.e. the spec senses the change (matches recorded G-DIFF fail at model_prepatch.py:160).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-16642 nagini bundle. Modeled callee select_content_type <-> the real {...}.get(encoding, content_type) table-lookup in FileResponse.set_headers (django/http/response.py:611-615). String carrier List[int] code points; spec over PSeq[int].

Spec region confirmed byte-identical to the bundle: `python -m swebench_unified.adversary same-spec nagini django__django-16642` returns exit 0 (SAME).

Real-boundary check against worktrees in /tmp:
- base_commit fbe850106b: dict has 3 keys {bzip2:application/x-bzip, gzip:application/gzip, xz:application/x-xz}.
- patched: dict adds br->application/x-brotli and compress->application/x-compress. This is the modeled (post-patch) callee.
- All 5 tok_* keys and 5 ct_* values in model.py are byte-exact code points of the real post-patch dict keys/values (independently recomputed from the real dict).

Differential fuzz of the model's resolved_type semantics vs the real dict.get: 0 divergences over 300,000 random cases (seed 16642) + 140 structured cases covering the 5 known keys x 7 content types plus None, empty, and near-misses (BR, Br, gz, Z, brotli, 'compress ', ' br', GZIP, bzip, lzma, zstd, deflate, identity). None/empty encoding -> [] -> is_known_encoding false -> passthrough of content_type, matching dict.get(None, content_type)==content_type. Passthrough loop returns a value-equal copy (ToSeq), observationally identical to the real default branch.

The postconditions (five Implies clauses, full resolved_type equality, passthrough clause) each state exactly the real callee's output; every clause is realized by the real function. The spec is strong but not stronger than reality. No input exists where the modeled function disagrees with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: add two rows ('br':'application/x-brotli', 'compress':'application/x-compress') to the compression-scheme->content-type dict in FileResponse.set_headers (django/http/response.py:611-615). Public problem_statement names the culprit encodings verbatim ('Improper guessing of Mime Type for "br" and "Z" file types'; .br/.Z mislabeled as text/html) but contains NO content-type values, no other scheme names, and no patch/dict text.

Spec-view analysis (docstring + pure region tok_*/ct_*/is_known_encoding/dedicated_type/resolved_type + pre/post-conditions/invariants; impl region is elided):

(1) Behavioral oracle, not edit narration: the spec pins correct output for every input via resolved_type + five Implies clauses (five schemes -> five dedicated content types + passthrough). A spec that omitted this would let any impl verify; treating a spec's statement of correct outputs as leakage would flag every well-formed bundle. This states WHAT is correct, not WHICH repo lines/structure to change.

(2) No patch-mechanics disclosure: the spec view never mentions dict/.get, response.py, set_headers, 'add keys', the pre-patch three-entry table, or the two-line-addition shape. Behavior is described abstractly ('every recognised compression scheme is mapped to its OWN dedicated content type'). Repo location / dict.get / prepatch reversion details live only in meta.json, refinement.md, mapping.md (auditor artifacts, NOT the spec view).

(3) The new-vs-problem_statement strings application/x-brotli / application/x-compress are the correctness oracle the spec must carry, not gold-edit reconstruction.

(4) Comment 'The two clauses for "br" and "compress" carry the discriminating behaviour' points at br/compress, but both (br, Z=compress) are already public in the problem_statement title; no info beyond it.

(5) Unchanged schemes bzip2/gzip/xz reveal nothing about the edit.

spec_view region hash d8aaa0f1... matches meta.json; G-LEAK lexical screen already 'spec view clean'. No spec-view line reconstructs the gold edit beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.