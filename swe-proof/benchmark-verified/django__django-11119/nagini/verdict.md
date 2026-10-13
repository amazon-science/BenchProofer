# P2 adversarial audit — django__django-11119

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -97,7 +96,6 @@
 def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -112,35 +110,19 @@
                     ToSeq(Result()) == ToSeq(value)))
     # post-conditions-end
     # impl-start
-    # The context built for rendering inherits the renderer's policy flag.
     ctx_autoescape = engine_autoescape
     result = []  # type: List[int]
     if ctx_autoescape:
-        i = len(value)
-        while i > 0:
+        i = 0
+        while i < len(value):
             # invariants-start
             Invariant(Acc(list_pred(value), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
-            Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
-            Invariant(MustTerminate(i + 1))
+            Invariant(ToSeq(result) == ToSeq(value).take(i))
             # invariants-end
-            c = value[i - 1]
-            Assert(ToSeq(value).drop(i - 1)[0] == c)
-            Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
-            if c == 38:
-                result = [38, 97, 109, 112, 59] + result
-            elif c == 60:
-                result = [38, 108, 116, 59] + result
-            elif c == 62:
-                result = [38, 103, 116, 59] + result
-            elif c == 34:
-                result = [38, 113, 117, 111, 116, 59] + result
-            elif c == 39:
-                result = [38, 35, 51, 57, 59] + result
-            else:
-                result = [c] + result
-            i = i - 1
+            result = result + [value[i]]
+            i = i + 1
     else:
         i = 0
         while i < len(value):
@@ -149,7 +131,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(result) == ToSeq(value).take(i))
-            Invariant(MustTerminate(len(value) - i + 1))
             # invariants-end
             result = result + [value[i]]
             i = i + 1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -97,7 +96,6 @@
 def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -112,7 +110,6 @@
                     ToSeq(Result()) == ToSeq(value)))
     # post-conditions-end
     # impl-start
-    # The context built for rendering inherits the renderer's policy flag.
     ctx_autoescape = engine_autoescape
     result = []  # type: List[int]
     if ctx_autoescape:
@@ -123,7 +120,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
-            Invariant(MustTerminate(i + 1))
             # invariants-end
             c = value[i - 1]
             Assert(ToSeq(value).drop(i - 1)[0] == c)
@@ -142,16 +138,29 @@
                 result = [c] + result
             i = i - 1
     else:
-        i = 0
-        while i < len(value):
+        i = len(value)
+        while i > 0:
             # invariants-start
             Invariant(Acc(list_pred(value), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
-            Invariant(ToSeq(result) == ToSeq(value).take(i))
-            Invariant(MustTerminate(len(value) - i + 1))
+            Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
             # invariants-end
-            result = result + [value[i]]
-            i = i + 1
+            c = value[i - 1]
+            Assert(ToSeq(value).drop(i - 1)[0] == c)
+            Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
+            if c == 38:
+                result = [38, 97, 109, 112, 59] + result
+            elif c == 60:
+                result = [38, 108, 116, 59] + result
+            elif c == 62:
+                result = [38, 103, 116, 59] + result
+            elif c == 34:
+                result = [38, 113, 117, 111, 116, 59] + result
+            elif c == 39:
+                result = [38, 35, 51, 57, 59] + result
+            else:
+                result = [c] + result
+            i = i - 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -97,7 +96,6 @@
 def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -112,10 +110,20 @@
                     ToSeq(Result()) == ToSeq(value)))
     # post-conditions-end
     # impl-start
-    # The context built for rendering inherits the renderer's policy flag.
     ctx_autoescape = engine_autoescape
     result = []  # type: List[int]
     if ctx_autoescape:
+        i = 0
+        while i < len(value):
+            # invariants-start
+            Invariant(Acc(list_pred(value), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= i and i <= len(value))
+            Invariant(ToSeq(result) == ToSeq(value).take(i))
+            # invariants-end
+            result = result + [value[i]]
+            i = i + 1
+    else:
         i = len(value)
         while i > 0:
             # invariants-start
@@ -123,7 +131,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
-            Invariant(MustTerminate(i + 1))
             # invariants-end
             c = value[i - 1]
             Assert(ToSeq(value).drop(i - 1)[0] == c)
@@ -141,17 +148,5 @@
             else:
                 result = [c] + result
             i = i - 1
-    else:
-        i = 0
-        while i < len(value):
-            # invariants-start
-            Invariant(Acc(list_pred(value), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(value))
-            Invariant(ToSeq(result) == ToSeq(value).take(i))
-            Invariant(MustTerminate(len(value) - i + 1))
-            # invariants-end
-            result = result + [value[i]]
-            i = i + 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -97,7 +96,6 @@
 def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -112,18 +110,16 @@
                     ToSeq(Result()) == ToSeq(value)))
     # post-conditions-end
     # impl-start
-    # The context built for rendering inherits the renderer's policy flag.
     ctx_autoescape = engine_autoescape
     result = []  # type: List[int]
     if ctx_autoescape:
         i = len(value)
-        while i > 0:
+        while i > 1:
             # invariants-start
             Invariant(Acc(list_pred(value), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
-            Invariant(MustTerminate(i + 1))
             # invariants-end
             c = value[i - 1]
             Assert(ToSeq(value).drop(i - 1)[0] == c)
@@ -149,7 +145,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(result) == ToSeq(value).take(i))
-            Invariant(MustTerminate(len(value) - i + 1))
             # invariants-end
             result = result + [value[i]]
             i = i + 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -97,7 +96,6 @@
 def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -112,7 +110,6 @@
                     ToSeq(Result()) == ToSeq(value)))
     # post-conditions-end
     # impl-start
-    # The context built for rendering inherits the renderer's policy flag.
     ctx_autoescape = engine_autoescape
     result = []  # type: List[int]
     if ctx_autoescape:
@@ -123,7 +120,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
-            Invariant(MustTerminate(i + 1))
             # invariants-end
             c = value[i - 1]
             Assert(ToSeq(value).drop(i - 1)[0] == c)
@@ -131,7 +127,7 @@
             if c == 38:
                 result = [38, 97, 109, 112, 59] + result
             elif c == 60:
-                result = [38, 108, 116, 59] + result
+                result = [38, 108, 116] + result
             elif c == 62:
                 result = [38, 103, 116, 59] + result
             elif c == 34:
@@ -149,7 +145,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(result) == ToSeq(value).take(i))
-            Invariant(MustTerminate(len(value) - i + 1))
             # invariants-end
             result = result + [value[i]]
             i = i + 1
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -97,7 +96,6 @@
 def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -112,7 +110,6 @@
                     ToSeq(Result()) == ToSeq(value)))
     # post-conditions-end
     # impl-start
-    # The context built for rendering inherits the renderer's policy flag.
     ctx_autoescape = engine_autoescape
     result = []  # type: List[int]
     if ctx_autoescape:
@@ -123,7 +120,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
-            Invariant(MustTerminate(i + 1))
             # invariants-end
             c = value[i - 1]
             Assert(ToSeq(value).drop(i - 1)[0] == c)
@@ -134,10 +130,6 @@
                 result = [38, 108, 116, 59] + result
             elif c == 62:
                 result = [38, 103, 116, 59] + result
-            elif c == 34:
-                result = [38, 113, 117, 111, 116, 59] + result
-            elif c == 39:
-                result = [38, 35, 51, 57, 59] + result
             else:
                 result = [c] + result
             i = i - 1
@@ -149,7 +141,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(result) == ToSeq(value).take(i))
-            Invariant(MustTerminate(len(value) - i + 1))
             # invariants-end
             result = result + [value[i]]
             i = i + 1
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -97,7 +96,6 @@
 def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -112,46 +110,7 @@
                     ToSeq(Result()) == ToSeq(value)))
     # post-conditions-end
     # impl-start
-    # The context built for rendering inherits the renderer's policy flag.
     ctx_autoescape = engine_autoescape
     result = []  # type: List[int]
-    if ctx_autoescape:
-        i = len(value)
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(value), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(value))
-            Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            c = value[i - 1]
-            Assert(ToSeq(value).drop(i - 1)[0] == c)
-            Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
-            if c == 38:
-                result = [38, 97, 109, 112, 59] + result
-            elif c == 60:
-                result = [38, 108, 116, 59] + result
-            elif c == 62:
-                result = [38, 103, 116, 59] + result
-            elif c == 34:
-                result = [38, 113, 117, 111, 116, 59] + result
-            elif c == 39:
-                result = [38, 35, 51, 57, 59] + result
-            else:
-                result = [c] + result
-            i = i - 1
-    else:
-        i = 0
-        while i < len(value):
-            # invariants-start
-            Invariant(Acc(list_pred(value), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(value))
-            Invariant(ToSeq(result) == ToSeq(value).take(i))
-            Invariant(MustTerminate(len(value) - i + 1))
-            # invariants-end
-            result = result + [value[i]]
-            i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11119.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configured renderer carries an auto-escaping policy flag. When it renders a
  context value into a template, that policy MUST govern whether the value is
  HTML-escaped:

    * policy ON  -> the value is HTML-escaped: each of the five HTML-significant
      code points is replaced by its constant entity sequence, every other code
      point passing through unchanged (the per-code-point substitution);
    * policy OFF -> the value is emitted verbatim, with NO escaping applied.

  The rendering context inherits the renderer's policy flag; it is NOT forced to
  the escaping default. So a renderer whose policy is OFF emits an angle-bracket
  value such as ``<...>`` unchanged, while a renderer whose policy is ON emits
  it escaped (``&lt;...&gt;``).

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

The HTML-escape of a value is modelled deeply as a verified per-code-point
substitution (`escaped_seq`); its equality to the real escaping callee is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom. The
operation under specification is the *policy-conditioned choice* between the
escaped form and the verbatim form, not the escaping itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def seq_amp() -> PSeq[int]:
    # '&amp;'
    return PSeq(38, 97, 109, 112, 59)


@Pure
def seq_lt() -> PSeq[int]:
    # '&lt;'
    return PSeq(38, 108, 116, 59)


@Pure
def seq_gt() -> PSeq[int]:
    # '&gt;'
    return PSeq(38, 103, 116, 59)


@Pure
def seq_quot() -> PSeq[int]:
    # '&quot;'
    return PSeq(38, 113, 117, 111, 116, 59)


@Pure
def seq_apos_dec() -> PSeq[int]:
    # '&#39;'  (the apostrophe entity emitted at this code base)
    return PSeq(38, 35, 51, 57, 59)


@Pure
def entity(c: int) -> PSeq[int]:
    """Entity sequence emitted for a single code point under escaping: the five
    significant ones expand, every other code point maps to itself."""
    if c == 38:        # '&'
        return seq_amp()
    if c == 60:        # '<'
        return seq_lt()
    if c == 62:        # '>'
        return seq_gt()
    if c == 34:        # '"'
        return seq_quot()
    if c == 39:        # "'"
        return seq_apos_dec()
    return PSeq(c)


@Pure
def escaped_seq(s: PSeq[int]) -> PSeq[int]:
    """The escape of a whole sequence: concatenate the per-code-point entity
    sequences. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))
# pure-end


def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendering context inherits the renderer's policy flag, and that flag
    # decides escaping: ON => escaped per-code-point substitution; OFF =>
    # verbatim. The OFF clause is the discriminating one (escaping must NOT be
    # forced when the policy is OFF).
    Ensures(Implies(engine_autoescape == True,
                    ToSeq(Result()) == escaped_seq(ToSeq(value))))
    Ensures(Implies(engine_autoescape == False,
                    ToSeq(Result()) == ToSeq(value)))
    # post-conditions-end
    # impl-start
    # The context built for rendering inherits the renderer's policy flag.
    ctx_autoescape = engine_autoescape
    result = []  # type: List[int]
    if ctx_autoescape:
        i = len(value)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(value))
            Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
            # invariants-end
            c = value[i - 1]
            Assert(ToSeq(value).drop(i - 1)[0] == c)
            Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
            if c == 38:
                result = [38, 97, 109, 112, 59] + result
            elif c == 60:
                result = [38, 108, 116, 59] + result
            elif c == 62:
                result = [38, 103, 116, 59] + result
            elif c == 34:
                result = [38, 113, 117, 111, 116, 59] + result
            elif c == 39:
                result = [38, 35, 51, 57, 59] + result
            else:
                result = [c] + result
            i = i - 1
    else:
        i = 0
        while i < len(value):
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(value))
            Invariant(ToSeq(result) == ToSeq(value).take(i))
            # invariants-end
            result = result + [value[i]]
            i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TOTAL, TIGHT functional spec: render_value(value: List[int], engine_autoescape: bool). engine_autoescape is a bool, so the two postconditions Ensures(Implies(engine_autoescape==True, ToSeq(Result())==escaped_seq(ToSeq(value)))) / Ensures(Implies(engine_autoescape==False, ToSeq(Result())==ToSeq(value))) cover the whole domain and pin the result content exactly (escaped-per-code-point when ON, verbatim when OFF). No domain slack for a verifying wrong impl to hide in.

ATTACKS (all, only impl region edited; spec region byte-identical for all 7, confirmed by `python -m swebench_unified.adversary same-spec nagini django__django-11119 <path>` = exit 0 / SAME). Verification command per attack: `python -m swebench_unified.adversary weakness nagini django__django-11119 <path>` (swebench-lean env, run concurrently 3-at-a-time as background jobs).
  - atk_1.py: never-escape (verbatim in BOTH branches; ungrounded/identity echo) -> NOT-A-COUNTEREXAMPLE, does not verify (fails ON/escaped clause), exit 2.
  - atk_2.py: always-escape (ignore flag, escape in both branches; prepatch-family but structurally distinct) -> does not verify (fails OFF/verbatim clause), exit 2.
  - atk_3.py: SWAPPED branches (verbatim on ON, escape on OFF) -> does not verify, exit 2.
  - atk_4.py: BOUNDARY off-by-one in escape loop (`while i > 1`, drops first code point) -> does not verify, exit 2.
  - atk_5.py: WRONG entity ('<'(60) -> [38,108,116], i.e. '&lt' missing ';') -> does not verify, exit 2.
  - atk_6.py: PARTIAL-DOMAIN escape (only &,<,> escaped; '"'(34) and "'"(39) fall through verbatim) -> does not verify, exit 2.
  - atk_7.py: CONTROL-FLOW-EFFECT / constant (return empty result unconditionally) -> does not verify, exit 2.

Positive control pos_control.py (= gold model.py impl) -> CANDIDATE (shares spec AND verifies, 18.2s), as expected. Prepatch prepatch.py (ctx_autoescape=True forced) -> does not verify (fails OFF/verbatim clause) => spec senses the bug (G-DIFF holds), prepatch_reproduced=true.

NO verifying wrong impl (CANDIDATE) was found besides the gold control, so there is no faithful refined patch to materialize/run_resolve; the verify=>correct falsification path is closed. patches={} accordingly.

A-REFERENCE correspondence (A4, the only kind-A obligation; axioms region is EMPTY, no consumed axioms): independently re-derived escaped_seq deep model == real django.utils.html.escape (str.translate(_html_escapes)) at base_commit d4df5e1b over 200,012 inputs (boundary + 200k fuzz over the 5 significant chars, ordinary ASCII, unicode e-acute/bullet, whitespace) => 0 divergences. Apostrophe entity = &#39; (PSeq 38,35,51,57,59), correct for THIS base_commit (html.escape/&#x27; switch is later django-11276). translate maps each input char independently (no re-scan of emitted entities), matching the front-recursive fold. F2P witness '<script>' confirmed both ways: OFF -> '<script>' verbatim, ON -> '&lt;script&gt;'. A5 verbatim branch str(value)==value confirmed on witnesses.

REFINEMENT.MD LEG AUDIT: A1=R (str<->List[int]), A2=I (self.autoescape bool identity), A3=R (the CHANGED op modeled concretely as ctx_autoescape=engine_autoescape, i.e. Context(context, autoescape=self.autoescape) inheriting the flag; identity on the boolean, NOT axiomatized), A4=A-reference (escaped_seq deep model, G-AX validated == django.utils.html.escape), A5=R+I (str(value) identity), A6=R (mark_safe only sets SafeString flag, no content change). No kind-3 (unexpressible-changed-op) legs; no @ContractOnly consumed axioms. A-legs' correspondence to the real callees holds.

Protocol: 7 distinct wrong impls (>=5 required) all machine-verified as rejected; prepatch reproduced; positive control verifies; A-reference re-checked independently. None breaks the spec => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11119.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configured renderer carries an auto-escaping policy flag. When it renders a
  context value into a template, that policy MUST govern whether the value is
  HTML-escaped:

    * policy ON  -> the value is HTML-escaped: each of the five HTML-significant
      code points is replaced by its constant entity sequence, every other code
      point passing through unchanged (the per-code-point substitution);
    * policy OFF -> the value is emitted verbatim, with NO escaping applied.

  The rendering context inherits the renderer's policy flag; it is NOT forced to
  the escaping default. So a renderer whose policy is OFF emits an angle-bracket
  value such as ``<...>`` unchanged, while a renderer whose policy is ON emits
  it escaped (``&lt;...&gt;``).

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

The HTML-escape of a value is modelled deeply as a verified per-code-point
substitution (`escaped_seq`); its equality to the real escaping callee is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom. The
operation under specification is the *policy-conditioned choice* between the
escaped form and the verbatim form, not the escaping itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def seq_amp() -> PSeq[int]:
    # '&amp;'
    return PSeq(38, 97, 109, 112, 59)


@Pure
def seq_lt() -> PSeq[int]:
    # '&lt;'
    return PSeq(38, 108, 116, 59)


@Pure
def seq_gt() -> PSeq[int]:
    # '&gt;'
    return PSeq(38, 103, 116, 59)


@Pure
def seq_quot() -> PSeq[int]:
    # '&quot;'
    return PSeq(38, 113, 117, 111, 116, 59)


@Pure
def seq_apos_dec() -> PSeq[int]:
    # '&#39;'  (the apostrophe entity emitted at this code base)
    return PSeq(38, 35, 51, 57, 59)


@Pure
def entity(c: int) -> PSeq[int]:
    """Entity sequence emitted for a single code point under escaping: the five
    significant ones expand, every other code point maps to itself."""
    if c == 38:        # '&'
        return seq_amp()
    if c == 60:        # '<'
        return seq_lt()
    if c == 62:        # '>'
        return seq_gt()
    if c == 34:        # '"'
        return seq_quot()
    if c == 39:        # "'"
        return seq_apos_dec()
    return PSeq(c)


@Pure
def escaped_seq(s: PSeq[int]) -> PSeq[int]:
    """The escape of a whole sequence: concatenate the per-code-point entity
    sequences. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))
# pure-end


def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendering context inherits the renderer's policy flag, and that flag
    # decides escaping: ON => escaped per-code-point substitution; OFF =>
    # verbatim. The OFF clause is the discriminating one (escaping must NOT be
    # forced when the policy is OFF).
    Ensures(Implies(engine_autoescape == True,
                    ToSeq(Result()) == escaped_seq(ToSeq(value))))
    Ensures(Implies(engine_autoescape == False,
                    ToSeq(Result()) == ToSeq(value)))
    # post-conditions-end
    # impl-start
    # The context built for rendering inherits the renderer's policy flag.
    ctx_autoescape = engine_autoescape
    result = []  # type: List[int]
    if ctx_autoescape:
        i = len(value)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(value))
            Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
            # invariants-end
            c = value[i - 1]
            Assert(ToSeq(value).drop(i - 1)[0] == c)
            Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
            if c == 38:
                result = [38, 97, 109, 112, 59] + result
            elif c == 60:
                result = [38, 108, 116, 59] + result
            elif c == 62:
                result = [38, 103, 116, 59] + result
            elif c == 34:
                result = [38, 113, 117, 111, 116, 59] + result
            elif c == 39:
                result = [38, 35, 51, 57, 59] + result
            else:
                result = [c] + result
            i = i - 1
    else:
        i = 0
        while i < len(value):
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(value))
            Invariant(ToSeq(result) == ToSeq(value).take(i))
            # invariants-end
            result = result + [value[i]]
            i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TOTAL, TIGHT functional spec: render_value(value: List[int], engine_autoescape: bool). engine_autoescape is a bool, so the two postconditions Ensures(Implies(engine_autoescape==True, ToSeq(Result())==escaped_seq(ToSeq(value)))) / Ensures(Implies(engine_autoescape==False, ToSeq(Result())==ToSeq(value))) cover the whole domain and pin the result content exactly (escaped-per-code-point when ON, verbatim when OFF). No domain slack for a verifying wrong impl to hide in.

ATTACKS (all, only impl region edited; spec region byte-identical for all 7, confirmed by `python -m swebench_unified.adversary same-spec nagini django__django-11119 <path>` = exit 0 / SAME). Verification command per attack: `python -m swebench_unified.adversary weakness nagini django__django-11119 <path>` (swebench-lean env, run concurrently 3-at-a-time as background jobs).
  - atk_1.py: never-escape (verbatim in BOTH branches; ungrounded/identity echo) -> NOT-A-COUNTEREXAMPLE, does not verify (fails ON/escaped clause), exit 2.
  - atk_2.py: always-escape (ignore flag, escape in both branches; prepatch-family but structurally distinct) -> does not verify (fails OFF/verbatim clause), exit 2.
  - atk_3.py: SWAPPED branches (verbatim on ON, escape on OFF) -> does not verify, exit 2.
  - atk_4.py: BOUNDARY off-by-one in escape loop (`while i > 1`, drops first code point) -> does not verify, exit 2.
  - atk_5.py: WRONG entity ('<'(60) -> [38,108,116], i.e. '&lt' missing ';') -> does not verify, exit 2.
  - atk_6.py: PARTIAL-DOMAIN escape (only &,<,> escaped; '"'(34) and "'"(39) fall through verbatim) -> does not verify, exit 2.
  - atk_7.py: CONTROL-FLOW-EFFECT / constant (return empty result unconditionally) -> does not verify, exit 2.

Positive control pos_control.py (= gold model.py impl) -> CANDIDATE (shares spec AND verifies, 18.2s), as expected. Prepatch prepatch.py (ctx_autoescape=True forced) -> does not verify (fails OFF/verbatim clause) => spec senses the bug (G-DIFF holds), prepatch_reproduced=true.

NO verifying wrong impl (CANDIDATE) was found besides the gold control, so there is no faithful refined patch to materialize/run_resolve; the verify=>correct falsification path is closed. patches={} accordingly.

A-REFERENCE correspondence (A4, the only kind-A obligation; axioms region is EMPTY, no consumed axioms): independently re-derived escaped_seq deep model == real django.utils.html.escape (str.translate(_html_escapes)) at base_commit d4df5e1b over 200,012 inputs (boundary + 200k fuzz over the 5 significant chars, ordinary ASCII, unicode e-acute/bullet, whitespace) => 0 divergences. Apostrophe entity = &#39; (PSeq 38,35,51,57,59), correct for THIS base_commit (html.escape/&#x27; switch is later django-11276). translate maps each input char independently (no re-scan of emitted entities), matching the front-recursive fold. F2P witness '<script>' confirmed both ways: OFF -> '<script>' verbatim, ON -> '&lt;script&gt;'. A5 verbatim branch str(value)==value confirmed on witnesses.

REFINEMENT.MD LEG AUDIT: A1=R (str<->List[int]), A2=I (self.autoescape bool identity), A3=R (the CHANGED op modeled concretely as ctx_autoescape=engine_autoescape, i.e. Context(context, autoescape=self.autoescape) inheriting the flag; identity on the boolean, NOT axiomatized), A4=A-reference (escaped_seq deep model, G-AX validated == django.utils.html.escape), A5=R+I (str(value) identity), A6=R (mark_safe only sets SafeString flag, no content change). No kind-3 (unexpressible-changed-op) legs; no @ContractOnly consumed axioms. A-legs' correspondence to the real callees holds.

Protocol: 7 distinct wrong impls (>=5 required) all machine-verified as rejected; prepatch reproduced; positive control verifies; A-reference re-checked independently. None breaks the spec => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the spec (render_value) to the real callee behavior on the modeled domain was checked and holds.

MODELED FUNCTION: render_value(value: List[int], engine_autoescape: bool) with postconditions:
  - engine_autoescape==True  => ToSeq(Result) == escaped_seq(ToSeq(value))  (full HTML escape)
  - engine_autoescape==False => ToSeq(Result) == ToSeq(value)               (verbatim)

REAL REPO PATH (base_commit d4df5e1b): Engine.render_to_string builds Context(context, autoescape=self.autoescape) after the gold patch; the renderer render_value_in_context (django/template/base.py:961-975) does: if context.autoescape: conditional_escape(value) else str(value). For a plain (non-SafeData, non-Promise) str value, conditional_escape reduces to django.utils.html.escape, and template_localtime/localize are no-ops. escape = mark_safe(str(text).translate(_html_escapes)) — a per-code-point substitution (& < > " ' -> entities, else identity). This is exactly the model's escaped_seq fold; apostrophe->&#39; matches this base_commit (the &#x27; switch is a later commit).

### Evidence
1. axiom_check.py run against the repo's actual django.utils.html => EXIT 0 (23 boundary + 20000 fuzz inputs, F2P witness '<script>' verbatim/escaped confirmed).
2. Independent fuzz: 200,000 random strings over a wide Unicode alphabet (code points 0x00-0x300 plus significant/entity/emoji chars) comparing real escape() vs escaped_seq and str() identity => 0 divergences.
3. str.translate maps each input character independently with no re-scan of emitted entities, so no over-/under-escaping edge exists that the per-code-point fold would miss.

The spec is NOT too strong: it is scoped to the F2P domain (plain str values), where the real behavior is precisely full-escape-or-verbatim gated on the engine autoescape flag. The prepatch model (ctx_autoescape=True forced) correctly fails the OFF/verbatim clause, so the spec genuinely senses the bug (G-DIFF). No consumed axioms; the only kind-A obligation (escape A-reference) is validated equal to the real callee. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical to the bundle (spec_view hash fcdd0e80575b0a20757c9ea586e0879632caf3596c5ac8b5c36480375e246481 matches meta G-HYGIENE). Assessed the rendered spec view (module docstring + axioms/pure/pre/post regions; impl elided) against the PUBLIC problem_statement only (not hints_text).

Gold edit: django/template/engine.py `Context(context)` -> `Context(context, autoescape=self.autoescape)` — the rendering Context must inherit the engine's autoescape attribute instead of the forced default True.

Public problem_statement already discloses the mechanism at full resolution: 'Engine.render_to_string() should honor the autoescape attribute'; 'a Context is created without specifying the engine autoescape attribute'; 'if you create an engine with autoescape=False ... the result will always be autoescaped.' The fix (honor the engine flag) is directly derivable from this text.

Spec view content is a strictly behavioral restatement contained within that disclosure: the postconditions Implies(engine_autoescape==True, Result==escaped_seq(value)) / Implies(engine_autoescape==False, Result==value), and the docstring lines 'The rendering context inherits the renderer's policy flag; it is NOT forced to the escaping default.' These are abstract observable-behavior statements. The spec view does NOT quote the gold code token `Context(context, autoescape=self.autoescape)`, does NOT name `self.autoescape`, the file `engine.py`, the line number, or the changed callsite — those specifics appear only in refinement.md/mapping.md, which are OUTSIDE the spec view.

The deep escaping machinery (entity/escaped_seq, entity code points, &#39; etc.) exceeds the problem statement in detail but models the UNCHANGED escape callee (A-reference); it does not reveal the gold edit, which does not touch escaping. G-LEAK is a lexical screen over the spec view; no line lexically or semantically discloses the gold edit beyond the public problem_statement. No non-obvious implementation choice is leaked.

Conclusion: the spec view does not leak the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
