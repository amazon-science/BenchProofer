# P2 adversarial audit — sympy__sympy-18763

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `posctl.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,43 +109,29 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # open-layout
     result = result + [92, 108, 101, 102, 116, 46, 32]
-    # open-delim (matched pair, before the body)
-    result = result + [92, 108, 101, 102, 116, 40]
-    # the body fragment, copied verbatim
+    # NO open_delim: body dropped straight in (the pre-patch behaviour)
     i = 0
     while i < len(body):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == open_layout() + open_delim()
-                  + ToSeq(body).take(i))
-        # invariants-end
+        Invariant(ToSeq(result) == open_layout() + ToSeq(body).take(i))
         result.append(body[i])
         i = i + 1
-    # close-delim (matched pair, after the body)
-    result = result + [92, 114, 105, 103, 104, 116, 41]
-    # mid-layout
     result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                        92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
-    # the condition fragment, copied verbatim
     j = 0
     while j < len(cond):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(cond))
-        Invariant(ToSeq(result) == open_layout() + open_delim()
-                  + ToSeq(body) + close_delim() + mid_layout()
-                  + ToSeq(cond).take(j))
-        # invariants-end
+        Invariant(ToSeq(result) == open_layout() + ToSeq(body)
+                  + mid_layout() + ToSeq(cond).take(j))
         result.append(cond[j])
         j = j + 1
-    # tail
     result = result + [32, 125, 125]
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,43 +109,22 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # open-layout
     result = result + [92, 108, 101, 102, 116, 46, 32]
-    # open-delim (matched pair, before the body)
     result = result + [92, 108, 101, 102, 116, 40]
-    # the body fragment, copied verbatim
-    i = 0
-    while i < len(body):
-        # invariants-start
-        Invariant(Acc(list_pred(body), 1 / 2))
-        Invariant(Acc(list_pred(cond), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == open_layout() + open_delim()
-                  + ToSeq(body).take(i))
-        # invariants-end
-        result.append(body[i])
-        i = i + 1
-    # close-delim (matched pair, after the body)
+    # body loop OMITTED — result correct only when body is empty
     result = result + [92, 114, 105, 103, 104, 116, 41]
-    # mid-layout
     result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                        92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
-    # the condition fragment, copied verbatim
     j = 0
     while j < len(cond):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(cond))
         Invariant(ToSeq(result) == open_layout() + open_delim()
-                  + ToSeq(body) + close_delim() + mid_layout()
-                  + ToSeq(cond).take(j))
-        # invariants-end
+                  + close_delim() + mid_layout() + ToSeq(cond).take(j))
         result.append(cond[j])
         j = j + 1
-    # tail
     result = result + [32, 125, 125]
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,43 +109,32 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # open-layout
     result = result + [92, 108, 101, 102, 116, 46, 32]
-    # open-delim (matched pair, before the body)
     result = result + [92, 108, 101, 102, 116, 40]
-    # the body fragment, copied verbatim
     i = 0
-    while i < len(body):
-        # invariants-start
+    while i < len(body) - 1:
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == open_layout() + open_delim()
                   + ToSeq(body).take(i))
-        # invariants-end
         result.append(body[i])
         i = i + 1
-    # close-delim (matched pair, after the body)
     result = result + [92, 114, 105, 103, 104, 116, 41]
-    # mid-layout
     result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                        92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
-    # the condition fragment, copied verbatim
     j = 0
     while j < len(cond):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(cond))
         Invariant(ToSeq(result) == open_layout() + open_delim()
-                  + ToSeq(body) + close_delim() + mid_layout()
-                  + ToSeq(cond).take(j))
-        # invariants-end
+                  + ToSeq(body).take(len(body) - 1) + close_delim()
+                  + mid_layout() + ToSeq(cond).take(j))
         result.append(cond[j])
         j = j + 1
-    # tail
     result = result + [32, 125, 125]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,43 +109,32 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # open-layout
     result = result + [92, 108, 101, 102, 116, 46, 32]
-    # open-delim (matched pair, before the body)
-    result = result + [92, 108, 101, 102, 116, 40]
-    # the body fragment, copied verbatim
+    result = result + [92, 114, 105, 103, 104, 116, 41]
     i = 0
     while i < len(body):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == open_layout() + open_delim()
+        Invariant(ToSeq(result) == open_layout() + close_delim()
                   + ToSeq(body).take(i))
-        # invariants-end
         result.append(body[i])
         i = i + 1
-    # close-delim (matched pair, after the body)
-    result = result + [92, 114, 105, 103, 104, 116, 41]
-    # mid-layout
+    result = result + [92, 108, 101, 102, 116, 40]
     result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                        92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
-    # the condition fragment, copied verbatim
     j = 0
     while j < len(cond):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(cond))
-        Invariant(ToSeq(result) == open_layout() + open_delim()
-                  + ToSeq(body) + close_delim() + mid_layout()
+        Invariant(ToSeq(result) == open_layout() + close_delim()
+                  + ToSeq(body) + open_delim() + mid_layout()
                   + ToSeq(cond).take(j))
-        # invariants-end
         result.append(cond[j])
         j = j + 1
-    # tail
     result = result + [32, 125, 125]
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,43 +109,32 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # open-layout
     result = result + [92, 108, 101, 102, 116, 46, 32]
-    # open-delim (matched pair, before the body)
-    result = result + [92, 108, 101, 102, 116, 40]
-    # the body fragment, copied verbatim
+    result = result + [91]
     i = 0
     while i < len(body):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == open_layout() + open_delim()
+        Invariant(ToSeq(result) == open_layout() + PSeq(91)
                   + ToSeq(body).take(i))
-        # invariants-end
         result.append(body[i])
         i = i + 1
-    # close-delim (matched pair, after the body)
-    result = result + [92, 114, 105, 103, 104, 116, 41]
-    # mid-layout
+    result = result + [93]
     result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                        92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
-    # the condition fragment, copied verbatim
     j = 0
     while j < len(cond):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(cond))
-        Invariant(ToSeq(result) == open_layout() + open_delim()
-                  + ToSeq(body) + close_delim() + mid_layout()
+        Invariant(ToSeq(result) == open_layout() + PSeq(91)
+                  + ToSeq(body) + PSeq(93) + mid_layout()
                   + ToSeq(cond).take(j))
-        # invariants-end
         result.append(cond[j])
         j = j + 1
-    # tail
     result = result + [32, 125, 125]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -109,32 +109,25 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # open-layout
+    # build the body group first: open_layout + open_delim + body + close_delim
     result = result + [92, 108, 101, 102, 116, 46, 32]
-    # open-delim (matched pair, before the body)
     result = result + [92, 108, 101, 102, 116, 40]
-    # the body fragment, copied verbatim
     i = 0
     while i < len(body):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == open_layout() + open_delim()
                   + ToSeq(body).take(i))
-        # invariants-end
         result.append(body[i])
         i = i + 1
-    # close-delim (matched pair, after the body)
     result = result + [92, 114, 105, 103, 104, 116, 41]
-    # mid-layout
+    # now append mid_layout, then the condition, then tail — same bytes, other structure
     result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                        92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
-    # the condition fragment, copied verbatim
     j = 0
     while j < len(cond):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
@@ -142,10 +135,8 @@
         Invariant(ToSeq(result) == open_layout() + open_delim()
                   + ToSeq(body) + close_delim() + mid_layout()
                   + ToSeq(cond).take(j))
-        # invariants-end
         result.append(cond[j])
         j = j + 1
-    # tail
     result = result + [32, 125, 125]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,43 +109,33 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # open-layout
     result = result + [92, 108, 101, 102, 116, 46, 32]
-    # open-delim (matched pair, before the body)
     result = result + [92, 108, 101, 102, 116, 40]
-    # the body fragment, copied verbatim
+    result = result + [92, 108, 101, 102, 116, 40]
     i = 0
     while i < len(body):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == open_layout() + open_delim()
-                  + ToSeq(body).take(i))
-        # invariants-end
+                  + open_delim() + ToSeq(body).take(i))
         result.append(body[i])
         i = i + 1
-    # close-delim (matched pair, after the body)
     result = result + [92, 114, 105, 103, 104, 116, 41]
-    # mid-layout
     result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                        92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
-    # the condition fragment, copied verbatim
     j = 0
     while j < len(cond):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(cond))
         Invariant(ToSeq(result) == open_layout() + open_delim()
-                  + ToSeq(body) + close_delim() + mid_layout()
-                  + ToSeq(cond).take(j))
-        # invariants-end
+                  + open_delim() + ToSeq(body) + close_delim()
+                  + mid_layout() + ToSeq(cond).take(j))
         result.append(cond[j])
         j = j + 1
-    # tail
     result = result + [32, 125, 125]
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,32 +109,23 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # open-layout
     result = result + [92, 108, 101, 102, 116, 46, 32]
-    # open-delim (matched pair, before the body)
     result = result + [92, 108, 101, 102, 116, 40]
-    # the body fragment, copied verbatim
     i = 0
     while i < len(body):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == open_layout() + open_delim()
                   + ToSeq(body).take(i))
-        # invariants-end
         result.append(body[i])
         i = i + 1
-    # close-delim (matched pair, after the body)
     result = result + [92, 114, 105, 103, 104, 116, 41]
-    # mid-layout
     result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                        92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
-    # the condition fragment, copied verbatim
     j = 0
     while j < len(cond):
-        # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(cond), 1 / 2))
         Invariant(Acc(list_pred(result)))
@@ -142,10 +133,8 @@
         Invariant(ToSeq(result) == open_layout() + open_delim()
                   + ToSeq(body) + close_delim() + mid_layout()
                   + ToSeq(cond).take(j))
-        # invariants-end
         result.append(cond[j])
         j = j + 1
-    # tail
-    result = result + [32, 125, 125]
+    # tail OMITTED
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `posctl.py`

```python
"""Twin-artifact model for sympy__sympy-18763.

Behaviour under specification (an abstract behavioural contract, not an edit):

  A renderer assembles a "restriction" layout from two already-rendered
  fragments: an inner BODY fragment and a CONDITION fragment. The assembled
  output is a constant surrounding layout in which the BODY is enclosed in its
  own matched delimiter pair so that it reads as ONE self-contained group,
  independent of whatever operator structure the body fragment carries. Element
  for element the result is:

      <open-layout> <open-delim> BODY <close-delim> <mid-layout> CONDITION <tail>

  where the four surrounding literals (`open-layout`, `open-delim` directly
  before the body, `close-delim` directly after it, `mid-layout`, `tail`) are
  constants. The body fragment therefore always appears bracketed by its
  own matched delimiter pair; a bare body that is dropped straight into the
  layout without that pair is NOT acceptable, because the surrounding layout's
  scaling delimiters would then bind to only part of a compound body.

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried over ``PSeq[int]`` via ``ToSeq``. The
literal layout fragments are spelled out as their ASCII code points in the
``pure`` region.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms. The two fragments BODY and CONDITION are
# already-rendered inputs; the operation under specification is purely the
# constant surrounding layout that assembles them. That layout — including the matched
# delimiter pair enclosing the body — is spelled out DEEPLY below as the pure
# constants and the `assembled` model, so there is no callee to axiomatize.)
# axioms-end


# pure-start
@Pure
def open_layout() -> PSeq[int]:
    # r'\left. '  -> the constant opening of the restriction layout
    return PSeq(92, 108, 101, 102, 116, 46, 32)


@Pure
def open_delim() -> PSeq[int]:
    # r'\left('   -> the scaling open delimiter placed directly before the body
    return PSeq(92, 108, 101, 102, 116, 40)


@Pure
def close_delim() -> PSeq[int]:
    # r'\right)'  -> the scaling close delimiter placed directly after the body
    return PSeq(92, 114, 105, 103, 104, 116, 41)


@Pure
def mid_layout() -> PSeq[int]:
    # r' \right|_{\substack{ '  -> layout between the body group and condition
    return PSeq(32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32)


@Pure
def tail() -> PSeq[int]:
    # r' }}'  -> the constant closing of the layout
    return PSeq(32, 125, 125)


@Pure
def assembled(body: PSeq[int], cond: PSeq[int]) -> PSeq[int]:
    """The fully assembled layout: the body enclosed in its own matched
    delimiter pair, dropped into the constant surrounding layout together with
    the condition fragment."""
    return (open_layout() + open_delim() + body + close_delim()
            + mid_layout() + cond + tail())
# pure-end


def format_restriction(body: List[int], cond: List[int]) -> List[int]:
    """Assemble the restriction layout from the already-rendered body and
    condition fragments, enclosing the body in its own matched delimiter pair."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    Requires(Acc(list_pred(cond), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(cond), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the result is exactly the constant layout with the body enclosed in its
    # matched delimiter pair (this is the load-bearing behavioural clause)
    Ensures(ToSeq(Result()) == assembled(ToSeq(body), ToSeq(cond)))
    # structural consequences that pin the body's enclosing delimiter pair:
    # the open delimiter sits immediately before the body, the close delimiter
    # immediately after it.
    Ensures(len(Result()) == len(open_layout()) + len(open_delim())
            + len(body) + len(close_delim()) + len(mid_layout())
            + len(cond) + len(tail()))
    Ensures(ToSeq(Result()).take(len(open_layout()) + len(open_delim()))
            == open_layout() + open_delim())
    Ensures(ToSeq(Result()).drop(len(open_layout()) + len(open_delim()))
            .take(len(body)) == ToSeq(body))
    Ensures(ToSeq(Result()).drop(len(open_layout()) + len(open_delim())
            + len(body)).take(len(close_delim())) == close_delim())
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # open-layout
    result = result + [92, 108, 101, 102, 116, 46, 32]
    # open-delim (matched pair, before the body)
    result = result + [92, 108, 101, 102, 116, 40]
    # the body fragment, copied verbatim
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(cond), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == open_layout() + open_delim()
                  + ToSeq(body).take(i))
        # invariants-end
        result.append(body[i])
        i = i + 1
    # close-delim (matched pair, after the body)
    result = result + [92, 114, 105, 103, 104, 116, 41]
    # mid-layout
    result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                       92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
    # the condition fragment, copied verbatim
    j = 0
    while j < len(cond):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(cond), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(cond))
        Invariant(ToSeq(result) == open_layout() + open_delim()
                  + ToSeq(body) + close_delim() + mid_layout()
                  + ToSeq(cond).take(j))
        # invariants-end
        result.append(cond[j])
        j = j + 1
    # tail
    result = result + [32, 125, 125]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: airtight functional equality. Postcondition `ToSeq(Result()) == assembled(ToSeq(body), ToSeq(cond))` plus structural take/drop clauses fully pin every output byte as a concrete function of inputs. `assembled` is a fully-concrete @Pure composition of open_layout+open_delim+body+close_delim+mid_layout+cond+tail, which I verified composes BYTE-FOR-BYTE to the gold post-change template r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (body,cond) (checked in /tmp: assembled('XY','C') == gold template, MATCH True; every fragment's code points decode to the exact LaTeX literals). meta.json confirms axioms:[] and deep_model_references:[].

A-LEG AUDIT (refinement.md): NONE exist. No consumed axioms, no A-reference deep models, no axiom_check.py. Every refinement leg is R (str<->List[int]; printf %s <-> verbatim code-point copy; str literals <-> code-point lists) or I (identical concrete byte sequences). No kind-3 (unexpressible-changed-op) steps. The 'no callee to axiomatize' claim is correct: _print_Subs's sub-calls (self._print, str.join) produce the already-rendered fragments latex_expr/latex_subs, which the model takes as the opaque read-only inputs body/cond (full generality, Acc 1/2); the patch changes ONLY the fixed surrounding template, modeled deeply as literal code-point segments. mapping.md symbol bindings all hold.

ATTACKS (all same-spec confirmed via `adversary same-spec`, exit 0; each run through `adversary weakness nagini sympy__sympy-18763`):
- atk_1 PREPATCH BUG: body dropped straight into layout with NO \left(...\right) pair. weakness EXIT=2 (does not verify) — spec rejects; PREPATCH REPRODUCED.
- atk_2 PARTIAL-DOMAIN: body loop omitted (correct only when body empty). EXIT=2 does not verify.
- atk_3 BOUNDARY off-by-one: loop `while i < len(body)-1` copies one fewer body element. EXIT=2 does not verify.
- atk_4 CONTROL-FLOW-EFFECT: swapped delimiters (close_delim before body, open_delim after). EXIT=2 does not verify.
- atk_5 UNGROUNDED/WRONG-BYTES: uses [ (91) and ] (93) instead of \left( / \right). EXIT=2 does not verify.
- atk_6 ECHO: behaviourally identical to gold (produces exactly assembled(body,cond)), restructured code (body group built as a block). weakness EXIT=0 => CANDIDATE (shares spec AND verifies). PER POLICY materialized faithful refined patch (= gold template edit, since behaviour is byte-identical) and ran run_resolve('sympy__sympy-18763', patch) under the OFFICIAL harness => RESOLVED: True, COMPLETED: True (run_id sbu-eq-atk6). A resolving echo is NOT a weakness (unified G-PANEL-1/G-EQ candidate->resolve policy). Does not break the spec.
- atk_7 DUPLICATE: open_delim emitted twice. EXIT=2 does not verify.
- atk_8 TAIL OMISSION: trailing ' }}' dropped. EXIT=2 does not verify.
Positive control posctl.py (= model.py, gold-faithful) VERIFIES via scripts/nagini_verify.sh, exit 0, 18.62s ('Verification successful').

### EXACT COMMANDS (project root, SBU_BENCHMARK_DIR=benchmark-verified, python=python):
  same-spec: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-18763 <atk>` (all exit 0)
  weakness:  `python -m swebench_unified.adversary weakness nagini sympy__sympy-18763 <atk>` (atk_1..5,7,8 exit 2; atk_6 exit 0)
  posctl:    `bash scripts/nagini_verify.sh posctl.py` (exit 0)
  resolve:   run_resolve('sympy__sympy-18763', atk_6_faithful.patch) => resolved=True
PARALLELISM: weakness/verify runs launched as concurrent background jobs in batches of <=3 (JVM+Z3 each), results collected; schedule only, pass criteria unchanged.

CONCLUSION: The spec is a complete byte-exact functional contract with no axioms/deep-model references, so verify => byte-identical to gold on all inputs => resolves. 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, wrong-bytes, duplicate, tail-omission, prepatch) were all REJECTED by the spec; the only verifying candidate (echo) resolves under the official harness. VERDICT: SOUND (verify => correct holds; no verify-but-wrong impl found).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `posctl.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `posctl.py`

```python
"""Twin-artifact model for sympy__sympy-18763.

Behaviour under specification (an abstract behavioural contract, not an edit):

  A renderer assembles a "restriction" layout from two already-rendered
  fragments: an inner BODY fragment and a CONDITION fragment. The assembled
  output is a constant surrounding layout in which the BODY is enclosed in its
  own matched delimiter pair so that it reads as ONE self-contained group,
  independent of whatever operator structure the body fragment carries. Element
  for element the result is:

      <open-layout> <open-delim> BODY <close-delim> <mid-layout> CONDITION <tail>

  where the four surrounding literals (`open-layout`, `open-delim` directly
  before the body, `close-delim` directly after it, `mid-layout`, `tail`) are
  constants. The body fragment therefore always appears bracketed by its
  own matched delimiter pair; a bare body that is dropped straight into the
  layout without that pair is NOT acceptable, because the surrounding layout's
  scaling delimiters would then bind to only part of a compound body.

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried over ``PSeq[int]`` via ``ToSeq``. The
literal layout fragments are spelled out as their ASCII code points in the
``pure`` region.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms. The two fragments BODY and CONDITION are
# already-rendered inputs; the operation under specification is purely the
# constant surrounding layout that assembles them. That layout — including the matched
# delimiter pair enclosing the body — is spelled out DEEPLY below as the pure
# constants and the `assembled` model, so there is no callee to axiomatize.)
# axioms-end


# pure-start
@Pure
def open_layout() -> PSeq[int]:
    # r'\left. '  -> the constant opening of the restriction layout
    return PSeq(92, 108, 101, 102, 116, 46, 32)


@Pure
def open_delim() -> PSeq[int]:
    # r'\left('   -> the scaling open delimiter placed directly before the body
    return PSeq(92, 108, 101, 102, 116, 40)


@Pure
def close_delim() -> PSeq[int]:
    # r'\right)'  -> the scaling close delimiter placed directly after the body
    return PSeq(92, 114, 105, 103, 104, 116, 41)


@Pure
def mid_layout() -> PSeq[int]:
    # r' \right|_{\substack{ '  -> layout between the body group and condition
    return PSeq(32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32)


@Pure
def tail() -> PSeq[int]:
    # r' }}'  -> the constant closing of the layout
    return PSeq(32, 125, 125)


@Pure
def assembled(body: PSeq[int], cond: PSeq[int]) -> PSeq[int]:
    """The fully assembled layout: the body enclosed in its own matched
    delimiter pair, dropped into the constant surrounding layout together with
    the condition fragment."""
    return (open_layout() + open_delim() + body + close_delim()
            + mid_layout() + cond + tail())
# pure-end


def format_restriction(body: List[int], cond: List[int]) -> List[int]:
    """Assemble the restriction layout from the already-rendered body and
    condition fragments, enclosing the body in its own matched delimiter pair."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    Requires(Acc(list_pred(cond), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(cond), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the result is exactly the constant layout with the body enclosed in its
    # matched delimiter pair (this is the load-bearing behavioural clause)
    Ensures(ToSeq(Result()) == assembled(ToSeq(body), ToSeq(cond)))
    # structural consequences that pin the body's enclosing delimiter pair:
    # the open delimiter sits immediately before the body, the close delimiter
    # immediately after it.
    Ensures(len(Result()) == len(open_layout()) + len(open_delim())
            + len(body) + len(close_delim()) + len(mid_layout())
            + len(cond) + len(tail()))
    Ensures(ToSeq(Result()).take(len(open_layout()) + len(open_delim()))
            == open_layout() + open_delim())
    Ensures(ToSeq(Result()).drop(len(open_layout()) + len(open_delim()))
            .take(len(body)) == ToSeq(body))
    Ensures(ToSeq(Result()).drop(len(open_layout()) + len(open_delim())
            + len(body)).take(len(close_delim())) == close_delim())
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # open-layout
    result = result + [92, 108, 101, 102, 116, 46, 32]
    # open-delim (matched pair, before the body)
    result = result + [92, 108, 101, 102, 116, 40]
    # the body fragment, copied verbatim
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(cond), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == open_layout() + open_delim()
                  + ToSeq(body).take(i))
        # invariants-end
        result.append(body[i])
        i = i + 1
    # close-delim (matched pair, after the body)
    result = result + [92, 114, 105, 103, 104, 116, 41]
    # mid-layout
    result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                       92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
    # the condition fragment, copied verbatim
    j = 0
    while j < len(cond):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(cond), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(cond))
        Invariant(ToSeq(result) == open_layout() + open_delim()
                  + ToSeq(body) + close_delim() + mid_layout()
                  + ToSeq(cond).take(j))
        # invariants-end
        result.append(cond[j])
        j = j + 1
    # tail
    result = result + [32, 125, 125]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: airtight functional equality. Postcondition `ToSeq(Result()) == assembled(ToSeq(body), ToSeq(cond))` plus structural take/drop clauses fully pin every output byte as a concrete function of inputs. `assembled` is a fully-concrete @Pure composition of open_layout+open_delim+body+close_delim+mid_layout+cond+tail, which I verified composes BYTE-FOR-BYTE to the gold post-change template r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (body,cond) (checked in /tmp: assembled('XY','C') == gold template, MATCH True; every fragment's code points decode to the exact LaTeX literals). meta.json confirms axioms:[] and deep_model_references:[].

A-LEG AUDIT (refinement.md): NONE exist. No consumed axioms, no A-reference deep models, no axiom_check.py. Every refinement leg is R (str<->List[int]; printf %s <-> verbatim code-point copy; str literals <-> code-point lists) or I (identical concrete byte sequences). No kind-3 (unexpressible-changed-op) steps. The 'no callee to axiomatize' claim is correct: _print_Subs's sub-calls (self._print, str.join) produce the already-rendered fragments latex_expr/latex_subs, which the model takes as the opaque read-only inputs body/cond (full generality, Acc 1/2); the patch changes ONLY the fixed surrounding template, modeled deeply as literal code-point segments. mapping.md symbol bindings all hold.

ATTACKS (all same-spec confirmed via `adversary same-spec`, exit 0; each run through `adversary weakness nagini sympy__sympy-18763`):
- atk_1 PREPATCH BUG: body dropped straight into layout with NO \left(...\right) pair. weakness EXIT=2 (does not verify) — spec rejects; PREPATCH REPRODUCED.
- atk_2 PARTIAL-DOMAIN: body loop omitted (correct only when body empty). EXIT=2 does not verify.
- atk_3 BOUNDARY off-by-one: loop `while i < len(body)-1` copies one fewer body element. EXIT=2 does not verify.
- atk_4 CONTROL-FLOW-EFFECT: swapped delimiters (close_delim before body, open_delim after). EXIT=2 does not verify.
- atk_5 UNGROUNDED/WRONG-BYTES: uses [ (91) and ] (93) instead of \left( / \right). EXIT=2 does not verify.
- atk_6 ECHO: behaviourally identical to gold (produces exactly assembled(body,cond)), restructured code (body group built as a block). weakness EXIT=0 => CANDIDATE (shares spec AND verifies). PER POLICY materialized faithful refined patch (= gold template edit, since behaviour is byte-identical) and ran run_resolve('sympy__sympy-18763', patch) under the OFFICIAL harness => RESOLVED: True, COMPLETED: True (run_id sbu-eq-atk6). A resolving echo is NOT a weakness (unified G-PANEL-1/G-EQ candidate->resolve policy). Does not break the spec.
- atk_7 DUPLICATE: open_delim emitted twice. EXIT=2 does not verify.
- atk_8 TAIL OMISSION: trailing ' }}' dropped. EXIT=2 does not verify.
Positive control posctl.py (= model.py, gold-faithful) VERIFIES via scripts/nagini_verify.sh, exit 0, 18.62s ('Verification successful').

### EXACT COMMANDS (project root, SBU_BENCHMARK_DIR=benchmark-verified, python=python):
  same-spec: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-18763 <atk>` (all exit 0)
  weakness:  `python -m swebench_unified.adversary weakness nagini sympy__sympy-18763 <atk>` (atk_1..5,7,8 exit 2; atk_6 exit 0)
  posctl:    `bash scripts/nagini_verify.sh posctl.py` (exit 0)
  resolve:   run_resolve('sympy__sympy-18763', atk_6_faithful.patch) => resolved=True
PARALLELISM: weakness/verify runs launched as concurrent background jobs in batches of <=3 (JVM+Z3 each), results collected; schedule only, pass criteria unchanged.

CONCLUSION: The spec is a complete byte-exact functional contract with no axioms/deep-model references, so verify => byte-identical to gold on all inputs => resolves. 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, wrong-bytes, duplicate, tail-omission, prepatch) were all REJECTED by the spec; the only verifying candidate (echo) resolves under the official harness. VERDICT: SOUND (verify => correct holds; no verify-but-wrong impl found).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) check for sympy__sympy-18763 nagini bundle. Real repo callee at base+gold: LatexPrinter._print_Subs returns r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr, latex_subs) (sympy/printing/latex.py:706-707) — a single printf substitution of two already-rendered fragments into a constant template. Model spec: Result == assembled(body,cond) = open_layout+open_delim+body+close_delim+mid_layout+cond+tail. Decoded the code-point literals: open_layout='\left. ', open_delim='\left(', close_delim='\right)', mid_layout=' \right|_{\substack{ ', tail=' }}'. The composition reproduces the gold template BYTE-FOR-BYTE (verified programmatically). Fuzzed 200k adversarial fragment values including '%','s','\','{','}' etc.: zero divergence between modeled assembled() and the real printf template. The spec domain (all List[int] code points) is a SUPERSET of real rendered fragments; since %s is verbatim single-pass insertion, every point in the domain agrees with the real callee, so no diverging input can exist. Spec is not over-strong: it pins exactly the discriminating \left(...\right) pair around the body (prepatch correctly fails, G-DIFF pass) without constraining anything beyond real behavior. same-spec on model.py: SAME (exit 0). No axioms/callees to over-approximate. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit inserts a matched scaling delimiter pair \left( ... \right) directly around the already-rendered body fragment (latex_expr) in LatexPrinter._print_Subs. The spec view (model.py open_delim/close_delim code-point constants + assembled/postconditions, mapping.md, refinement.md) does encode this discriminator, but it is ALREADY FULLY PUBLIC in problem_statement, which prints both the buggy output ('3 \left. - x + y \right|_{\substack{ x=1 }}') and the desired corrected output ('3 \left. \left(- x + y\right) \right|_{\substack{ x=1 }}'). Every literal in the spec (\left., \left(, \right), ' \right|_{\substack{ ', ' }}') corresponds to characters visible in the public before/after strings. Nothing in the spec view reveals the gold beyond problem_statement (hints_text is empty here anyway). Mechanical leakage.screen passes with zero hard_failures; same-spec on identity confirms spec region integrity.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
