# P2 adversarial audit — django__django-14155

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_8.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 3 of 10 same-spec attacks came back CANDIDATE (share the spec AND verify): atk_5 (partial-domain), atk_8 (echo, restructured delimiter/selection), atk_10 (staged assembly, patch exercising the I-collections leg at full licensed extent). All three faithful refined patches were MATERIALIZED and RUN through the official harness (swebench_unified.harness.run_resolve) and ALL THREE RESOLVED (resolved=True completed=True attempts=1) => correct echoes, not spec weaknesses. Oracle discrimination proven by a negative control (prepatch behaviour A reverted, patch_neg.diff): resolved=False completed=True attempts=3 ('consistent - not flaky'), so 'resolved=True' above is a real signal and not a harness that passes everything. No verifying wrong impl whose patch fails to resolve was found; verify=>correct holds on this spec.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -195,11 +195,9 @@
         ToSeq(url_name), ToSeq(route)))
     # post-conditions-end
     # impl-start
-    if is_prebound:
-        func = func_repr  # type: List[int]
-    else:
-        func = func_path
-    Assert(ToSeq(func) == func_token(ToSeq(func_path), ToSeq(func_repr), is_prebound))
+    # Pre-patch behaviour (A): the callable is always named by its dotted
+    # import path, with no special handling for a pre-bound wrapper.
+    func = func_path  # type: List[int]
     head = [82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
             40, 102, 117, 110, 99, 61]  # type: List[int]
     Assert(ToSeq(head) == lit_head())
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -207,66 +207,11 @@
     Assert(ToSeq(seg_url_name) == lit_url_name())
     seg_route = [44, 32, 114, 111, 117, 116, 101, 61]  # type: List[int]
     Assert(ToSeq(seg_route) == lit_route())
-    cu = 0
-    cr = 0
-    du = delim(ToSeq(url_name))
-    ub = []  # type: List[int]
-    i = len(url_name)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(url_name), 1 / 2))
-        Invariant(Acc(list_pred(ub)))
-        Invariant(0 <= i and i <= len(url_name))
-        Invariant(du == delim(ToSeq(url_name)))
-        Invariant(ToSeq(ub) == esc_body(ToSeq(url_name).drop(i), du))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        cu = url_name[i - 1]
-        Assert(ToSeq(url_name).drop(i - 1)[0] == cu)
-        Assert(ToSeq(url_name).drop(i - 1).drop(1) == ToSeq(url_name).drop(i))
-        if cu == 92:
-            ub = [92, 92] + ub
-        elif cu == du:
-            ub = [92, cu] + ub
-        else:
-            ub = [cu] + ub
-        i = i - 1
-    Assert(ToSeq(url_name).drop(0) == ToSeq(url_name))
-    q_url = [du] + ub + [du]  # type: List[int]
-    Assert(ToSeq(q_url) == PSeq(du) + ToSeq(ub) + PSeq(du))
-    Assert(ToSeq(ub) == esc_body(ToSeq(url_name), du))
-    Assert(ToSeq(q_url) == quoted_with(ToSeq(url_name), du))
-    Assert(du == delim(ToSeq(url_name)))
-    Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))
-    dr = delim(ToSeq(route))
-    rb = []  # type: List[int]
-    j = len(route)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(route), 1 / 2))
-        Invariant(Acc(list_pred(rb)))
-        Invariant(0 <= j and j <= len(route))
-        Invariant(dr == delim(ToSeq(route)))
-        Invariant(ToSeq(rb) == esc_body(ToSeq(route).drop(j), dr))
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        cr = route[j - 1]
-        Assert(ToSeq(route).drop(j - 1)[0] == cr)
-        Assert(ToSeq(route).drop(j - 1).drop(1) == ToSeq(route).drop(j))
-        if cr == 92:
-            rb = [92, 92] + rb
-        elif cr == dr:
-            rb = [92, cr] + rb
-        else:
-            rb = [cr] + rb
-        j = j - 1
-    Assert(ToSeq(route).drop(0) == ToSeq(route))
-    q_route = [dr] + rb + [dr]  # type: List[int]
-    Assert(ToSeq(q_route) == PSeq(dr) + ToSeq(rb) + PSeq(dr))
-    Assert(ToSeq(rb) == esc_body(ToSeq(route), dr))
-    Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
-    Assert(dr == delim(ToSeq(route)))
-    Assert(ToSeq(q_route) == quoted(ToSeq(route)))
+    # Pre-patch behaviour (B): the match name and the route pattern are
+    # rendered in their plain textual form, with no delimiters and no
+    # per-code-point marking.
+    q_url = url_name  # type: List[int]
+    q_route = route  # type: List[int]
     result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -207,66 +207,8 @@
     Assert(ToSeq(seg_url_name) == lit_url_name())
     seg_route = [44, 32, 114, 111, 117, 116, 101, 61]  # type: List[int]
     Assert(ToSeq(seg_route) == lit_route())
-    cu = 0
-    cr = 0
-    du = delim(ToSeq(url_name))
-    ub = []  # type: List[int]
-    i = len(url_name)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(url_name), 1 / 2))
-        Invariant(Acc(list_pred(ub)))
-        Invariant(0 <= i and i <= len(url_name))
-        Invariant(du == delim(ToSeq(url_name)))
-        Invariant(ToSeq(ub) == esc_body(ToSeq(url_name).drop(i), du))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        cu = url_name[i - 1]
-        Assert(ToSeq(url_name).drop(i - 1)[0] == cu)
-        Assert(ToSeq(url_name).drop(i - 1).drop(1) == ToSeq(url_name).drop(i))
-        if cu == 92:
-            ub = [92, 92] + ub
-        elif cu == du:
-            ub = [92, cu] + ub
-        else:
-            ub = [cu] + ub
-        i = i - 1
-    Assert(ToSeq(url_name).drop(0) == ToSeq(url_name))
-    q_url = [du] + ub + [du]  # type: List[int]
-    Assert(ToSeq(q_url) == PSeq(du) + ToSeq(ub) + PSeq(du))
-    Assert(ToSeq(ub) == esc_body(ToSeq(url_name), du))
-    Assert(ToSeq(q_url) == quoted_with(ToSeq(url_name), du))
-    Assert(du == delim(ToSeq(url_name)))
-    Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))
-    dr = delim(ToSeq(route))
-    rb = []  # type: List[int]
-    j = len(route)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(route), 1 / 2))
-        Invariant(Acc(list_pred(rb)))
-        Invariant(0 <= j and j <= len(route))
-        Invariant(dr == delim(ToSeq(route)))
-        Invariant(ToSeq(rb) == esc_body(ToSeq(route).drop(j), dr))
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        cr = route[j - 1]
-        Assert(ToSeq(route).drop(j - 1)[0] == cr)
-        Assert(ToSeq(route).drop(j - 1).drop(1) == ToSeq(route).drop(j))
-        if cr == 92:
-            rb = [92, 92] + rb
-        elif cr == dr:
-            rb = [92, cr] + rb
-        else:
-            rb = [cr] + rb
-        j = j - 1
-    Assert(ToSeq(route).drop(0) == ToSeq(route))
-    q_route = [dr] + rb + [dr]  # type: List[int]
-    Assert(ToSeq(q_route) == PSeq(dr) + ToSeq(rb) + PSeq(dr))
-    Assert(ToSeq(rb) == esc_body(ToSeq(route), dr))
-    Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
-    Assert(dr == delim(ToSeq(route)))
-    Assert(ToSeq(q_route) == quoted(ToSeq(route)))
+    q_url = [39] + url_name + [39]  # type: List[int]
+    q_route = [39] + route + [39]  # type: List[int]
     result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -209,7 +209,7 @@
     Assert(ToSeq(seg_route) == lit_route())
     cu = 0
     cr = 0
-    du = delim(ToSeq(url_name))
+    du = 39
     ub = []  # type: List[int]
     i = len(url_name)
     while i > 0:
@@ -217,7 +217,7 @@
         Invariant(Acc(list_pred(url_name), 1 / 2))
         Invariant(Acc(list_pred(ub)))
         Invariant(0 <= i and i <= len(url_name))
-        Invariant(du == delim(ToSeq(url_name)))
+        Invariant(du == 39)
         Invariant(ToSeq(ub) == esc_body(ToSeq(url_name).drop(i), du))
         Invariant(MustTerminate(i + 1))
         # invariants-end
@@ -236,9 +236,7 @@
     Assert(ToSeq(q_url) == PSeq(du) + ToSeq(ub) + PSeq(du))
     Assert(ToSeq(ub) == esc_body(ToSeq(url_name), du))
     Assert(ToSeq(q_url) == quoted_with(ToSeq(url_name), du))
-    Assert(du == delim(ToSeq(url_name)))
-    Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))
-    dr = delim(ToSeq(route))
+    dr = 39
     rb = []  # type: List[int]
     j = len(route)
     while j > 0:
@@ -246,7 +244,7 @@
         Invariant(Acc(list_pred(route), 1 / 2))
         Invariant(Acc(list_pred(rb)))
         Invariant(0 <= j and j <= len(route))
-        Invariant(dr == delim(ToSeq(route)))
+        Invariant(dr == 39)
         Invariant(ToSeq(rb) == esc_body(ToSeq(route).drop(j), dr))
         Invariant(MustTerminate(j + 1))
         # invariants-end
@@ -265,8 +263,6 @@
     Assert(ToSeq(q_route) == PSeq(dr) + ToSeq(rb) + PSeq(dr))
     Assert(ToSeq(rb) == esc_body(ToSeq(route), dr))
     Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
-    Assert(dr == delim(ToSeq(route)))
-    Assert(ToSeq(q_route) == quoted(ToSeq(route)))
     result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -220,6 +220,8 @@
         Invariant(du == delim(ToSeq(url_name)))
         Invariant(ToSeq(ub) == esc_body(ToSeq(url_name).drop(i), du))
         Invariant(MustTerminate(i + 1))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(url_name),
+                                                32 <= url_name[k] and url_name[k] <= 126))))
         # invariants-end
         cu = url_name[i - 1]
         Assert(ToSeq(url_name).drop(i - 1)[0] == cu)
@@ -228,6 +230,8 @@
             ub = [92, 92] + ub
         elif cu == du:
             ub = [92, cu] + ub
+        elif cu < 32 or cu > 126:
+            ub = [88, 88, 88] + ub
         else:
             ub = [cu] + ub
         i = i - 1
@@ -249,6 +253,8 @@
         Invariant(dr == delim(ToSeq(route)))
         Invariant(ToSeq(rb) == esc_body(ToSeq(route).drop(j), dr))
         Invariant(MustTerminate(j + 1))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(route),
+                                                32 <= route[k] and route[k] <= 126))))
         # invariants-end
         cr = route[j - 1]
         Assert(ToSeq(route).drop(j - 1)[0] == cr)
@@ -257,6 +263,8 @@
             rb = [92, 92] + rb
         elif cr == dr:
             rb = [92, cr] + rb
+        elif cr < 32 or cr > 126:
+            rb = [88, 88, 88] + rb
         else:
             rb = [cr] + rb
         j = j - 1
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -240,7 +240,7 @@
     Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))
     dr = delim(ToSeq(route))
     rb = []  # type: List[int]
-    j = len(route)
+    j = len(route) - 1
     while j > 0:
         # invariants-start
         Invariant(Acc(list_pred(route), 1 / 2))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -267,6 +267,12 @@
     Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
     Assert(dr == delim(ToSeq(route)))
     Assert(ToSeq(q_route) == quoted(ToSeq(route)))
+    spin = 1
+    while spin > 0:
+        # invariants-start
+        Invariant(spin >= 1)
+        # invariants-end
+        spin = spin + 1
     result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -195,10 +195,10 @@
         ToSeq(url_name), ToSeq(route)))
     # post-conditions-end
     # impl-start
-    if is_prebound:
-        func = func_repr  # type: List[int]
+    if not is_prebound:
+        func = func_path  # type: List[int]
     else:
-        func = func_path
+        func = func_repr
     Assert(ToSeq(func) == func_token(ToSeq(func_path), ToSeq(func_repr), is_prebound))
     head = [82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
             40, 102, 117, 110, 99, 61]  # type: List[int]
@@ -209,7 +209,10 @@
     Assert(ToSeq(seg_route) == lit_route())
     cu = 0
     cr = 0
-    du = delim(ToSeq(url_name))
+    du = 39
+    if contains(ToSeq(url_name), 39) and not contains(ToSeq(url_name), 34):
+        du = 34
+    Assert(du == delim(ToSeq(url_name)))
     ub = []  # type: List[int]
     i = len(url_name)
     while i > 0:
@@ -238,7 +241,10 @@
     Assert(ToSeq(q_url) == quoted_with(ToSeq(url_name), du))
     Assert(du == delim(ToSeq(url_name)))
     Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))
-    dr = delim(ToSeq(route))
+    dr = 39
+    if contains(ToSeq(route), 39) and not contains(ToSeq(route), 34):
+        dr = 34
+    Assert(dr == delim(ToSeq(route)))
     rb = []  # type: List[int]
     j = len(route)
     while j > 0:
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -209,7 +209,9 @@
     Assert(ToSeq(seg_route) == lit_route())
     cu = 0
     cr = 0
-    du = delim(ToSeq(url_name))
+    du = 39
+    if contains(ToSeq(url_name), 34) and not contains(ToSeq(url_name), 39):
+        du = 34
     ub = []  # type: List[int]
     i = len(url_name)
     while i > 0:
@@ -217,7 +219,6 @@
         Invariant(Acc(list_pred(url_name), 1 / 2))
         Invariant(Acc(list_pred(ub)))
         Invariant(0 <= i and i <= len(url_name))
-        Invariant(du == delim(ToSeq(url_name)))
         Invariant(ToSeq(ub) == esc_body(ToSeq(url_name).drop(i), du))
         Invariant(MustTerminate(i + 1))
         # invariants-end
@@ -233,12 +234,9 @@
         i = i - 1
     Assert(ToSeq(url_name).drop(0) == ToSeq(url_name))
     q_url = [du] + ub + [du]  # type: List[int]
-    Assert(ToSeq(q_url) == PSeq(du) + ToSeq(ub) + PSeq(du))
-    Assert(ToSeq(ub) == esc_body(ToSeq(url_name), du))
-    Assert(ToSeq(q_url) == quoted_with(ToSeq(url_name), du))
-    Assert(du == delim(ToSeq(url_name)))
-    Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))
-    dr = delim(ToSeq(route))
+    dr = 39
+    if contains(ToSeq(route), 34) and not contains(ToSeq(route), 39):
+        dr = 34
     rb = []  # type: List[int]
     j = len(route)
     while j > 0:
@@ -246,7 +244,6 @@
         Invariant(Acc(list_pred(route), 1 / 2))
         Invariant(Acc(list_pred(rb)))
         Invariant(0 <= j and j <= len(route))
-        Invariant(dr == delim(ToSeq(route)))
         Invariant(ToSeq(rb) == esc_body(ToSeq(route).drop(j), dr))
         Invariant(MustTerminate(j + 1))
         # invariants-end
@@ -262,11 +259,6 @@
         j = j - 1
     Assert(ToSeq(route).drop(0) == ToSeq(route))
     q_route = [dr] + rb + [dr]  # type: List[int]
-    Assert(ToSeq(q_route) == PSeq(dr) + ToSeq(rb) + PSeq(dr))
-    Assert(ToSeq(rb) == esc_body(ToSeq(route), dr))
-    Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
-    Assert(dr == delim(ToSeq(route)))
-    Assert(ToSeq(q_route) == quoted(ToSeq(route)))
     result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
     return result
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -267,6 +267,11 @@
     Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
     Assert(dr == delim(ToSeq(route)))
     Assert(ToSeq(q_route) == quoted(ToSeq(route)))
-    result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
+    result = head + func  # type: List[int]
+    result = result + seg_url_name
+    result = result + q_url
+    result = result + seg_route
+    result = result + q_route
+    result = result + [41]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14155.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A resolved-URL match object renders a single-line, parenthesised textual
  description of the match. The description names the resolved callable, then
  the match name, then the route pattern, each introduced by its own ``field=``
  label and separated by a comma and a space.

  (A) Naming the callable. A directly-resolved callable is named by its dotted
      import path (module plus qualified name). A callable that was produced by
      pre-binding arguments to another callable carries no such name of its
      own, so for it the description instead reproduces that callable's own
      textual form (which exposes the underlying callable and the pre-bound
      arguments). The choice between the two is governed solely by whether the
      callable is such a pre-bound wrapper.

  (B) Rendering the textual fields. The match name and the route pattern are
      arbitrary text and are rendered in their *quoted* textual form, so that
      the boundary of the text is unambiguous, an empty value is visible, and
      the rendering can be read back unambiguously:

        * the value is delimited by one quote character on each side. The
          delimiter is the apostrophe (U+0027), except when the value itself
          contains an apostrophe and does not contain a double quote (U+0022);
          then the double quote is the delimiter, so that the apostrophes
          inside need no marking.
        * between the delimiters each code point of the value stands for
          itself, except that a backslash (U+005C) and any occurrence of the
          chosen delimiter are each preceded by an additional backslash.

      The two text fields range over printable ASCII (code points 32..126);
      that is the domain on which this quoted rendering is specified, and it is
      stated as a precondition below.

  (The collection fields the full description also carries between the callable
  name and the match name -- the positional arguments, the keyword arguments,
  and the two namespace lists -- are rendered in their canonical collection
  form, which for those collection values coincides with their plain textual
  form; carrying no behavioural distinction, they are elided from this model
  and accounted for in the refinement as an identity step.)

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by the pure sequence theory
``PSeq[int]``. The modelled portion of the description is the constant-shaped
front-to-back concatenation of the literal label segments with the rendered
field values. The behaviour is pure structure/selection over the inputs,
modelled deeply; no callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# axioms-end

# pure-start
@Pure
def lit_head() -> PSeq[int]:
    # 'ResolverMatch(func='
    return PSeq(82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
                40, 102, 117, 110, 99, 61)

@Pure
def lit_url_name() -> PSeq[int]:
    # ', url_name='
    return PSeq(44, 32, 117, 114, 108, 95, 110, 97, 109, 101, 61)

@Pure
def lit_route() -> PSeq[int]:
    # ', route='
    return PSeq(44, 32, 114, 111, 117, 116, 101, 61)

@Pure
def lit_tail() -> PSeq[int]:
    # ')'
    return PSeq(41)

@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff code point `x` occurs in `s`. Front-recursive so a single
    unfold is available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)

@Pure
def delim(s: PSeq[int]) -> int:
    """The quote character that delimits the quoted rendering of the text `s`:
    the apostrophe (39), except that a value which contains an apostrophe and
    no double quote is delimited by the double quote (34) instead, so that the
    apostrophes it contains need no marking."""
    if contains(s, 39) and not contains(s, 34):
        return 34
    return 39

@Pure
def esc_char(c: int, d: int) -> PSeq[int]:
    """How one code point `c` of a text value stands between delimiters `d`: a
    backslash (92) and the delimiter itself are each preceded by an additional
    backslash; every other code point stands for itself."""
    if c == 92:
        return PSeq(92, 92)
    if c == d:
        return PSeq(92, c)
    return PSeq(c)

@Pure
def esc_body(s: PSeq[int], d: int) -> PSeq[int]:
    """The inside of the quoted rendering of `s` under delimiter `d`: the
    per-code-point rendering applied elementwise. Front-recursive so a single
    unfold is available per loop step."""
    if len(s) == 0:
        return s
    return esc_char(s[0], d) + esc_body(s.drop(1), d)

@Pure
def quoted_with(s: PSeq[int], d: int) -> PSeq[int]:
    """The quoted rendering of `s` under an explicit delimiter `d`: the
    delimiter, then the elementwise-rendered body, then the same delimiter."""
    return PSeq(d) + esc_body(s, d) + PSeq(d)

@Pure
def quoted(s: PSeq[int]) -> PSeq[int]:
    """The quoted textual rendering of an arbitrary text value: the body
    rendered elementwise between two copies of the delimiter `delim` chooses."""
    return quoted_with(s, delim(s))

@Pure
def func_token(func_path: PSeq[int], func_repr: PSeq[int], is_prebound: bool) -> PSeq[int]:
    """The text naming the callable. A pre-bound wrapper has no dotted import
    name of its own, so its own textual form (`func_repr`, exposing the wrapped
    callable and pre-bound arguments) is used; otherwise the dotted import path
    (`func_path`) is used."""
    if is_prebound:
        return func_repr
    return func_path

@Pure
def built_repr(func_path: PSeq[int], func_repr: PSeq[int], is_prebound: bool,
               url_name: PSeq[int], route: PSeq[int]) -> PSeq[int]:
    """The modelled portion of the description: the constant-shaped concatenation of the
    label segments with the rendered field values. The callable name is
    selected by `func_token`; the match name and route are rendered `quoted`."""
    return (lit_head() + func_token(func_path, func_repr, is_prebound)
            + lit_url_name() + quoted(url_name)
            + lit_route() + quoted(route)
            + lit_tail())
# pure-end

def resolver_match_repr(func_path: List[int], func_repr: List[int], is_prebound: bool,
                        url_name: List[int], route: List[int]) -> List[int]:
    # pre-conditions-start
    # Every input is read-only (the rendering mutates nothing it is given), so
    # each is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(func_path), 1 / 2))
    Requires(Acc(list_pred(func_repr), 1 / 2))
    Requires(Acc(list_pred(url_name), 1 / 2))
    Requires(Acc(list_pred(route), 1 / 2))
    # The two text fields range over printable ASCII (32..126) -- the domain on
    # which the quoted rendering above is specified.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(url_name),
                                            32 <= url_name[k] and url_name[k] <= 126))))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(route),
                                            32 <= route[k] and route[k] <= 126))))
    Requires(MustTerminate(len(url_name) + len(route) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(func_path), 1 / 2))
    Ensures(Acc(list_pred(func_repr), 1 / 2))
    Ensures(Acc(list_pred(url_name), 1 / 2))
    Ensures(Acc(list_pred(route), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The description is exactly the constant-shaped concatenation, with the callable
    # named by `func_token` (so a pre-bound wrapper shows its own form, not a
    # name it does not have) and the match name and route rendered `quoted`.
    Ensures(ToSeq(Result()) == built_repr(
        ToSeq(func_path), ToSeq(func_repr), is_prebound,
        ToSeq(url_name), ToSeq(route)))
    # post-conditions-end
    # impl-start
    if is_prebound:
        func = func_repr  # type: List[int]
    else:
        func = func_path
    Assert(ToSeq(func) == func_token(ToSeq(func_path), ToSeq(func_repr), is_prebound))
    head = [82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
            40, 102, 117, 110, 99, 61]  # type: List[int]
    Assert(ToSeq(head) == lit_head())
    seg_url_name = [44, 32, 117, 114, 108, 95, 110, 97, 109, 101, 61]  # type: List[int]
    Assert(ToSeq(seg_url_name) == lit_url_name())
    seg_route = [44, 32, 114, 111, 117, 116, 101, 61]  # type: List[int]
    Assert(ToSeq(seg_route) == lit_route())
    cu = 0
    cr = 0
    du = delim(ToSeq(url_name))
    ub = []  # type: List[int]
    i = len(url_name)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(url_name), 1 / 2))
        Invariant(Acc(list_pred(ub)))
        Invariant(0 <= i and i <= len(url_name))
        Invariant(du == delim(ToSeq(url_name)))
        Invariant(ToSeq(ub) == esc_body(ToSeq(url_name).drop(i), du))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        cu = url_name[i - 1]
        Assert(ToSeq(url_name).drop(i - 1)[0] == cu)
        Assert(ToSeq(url_name).drop(i - 1).drop(1) == ToSeq(url_name).drop(i))
        if cu == 92:
            ub = [92, 92] + ub
        elif cu == du:
            ub = [92, cu] + ub
        else:
            ub = [cu] + ub
        i = i - 1
    Assert(ToSeq(url_name).drop(0) == ToSeq(url_name))
    q_url = [du] + ub + [du]  # type: List[int]
    Assert(ToSeq(q_url) == PSeq(du) + ToSeq(ub) + PSeq(du))
    Assert(ToSeq(ub) == esc_body(ToSeq(url_name), du))
    Assert(ToSeq(q_url) == quoted_with(ToSeq(url_name), du))
    Assert(du == delim(ToSeq(url_name)))
    Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))
    dr = delim(ToSeq(route))
    rb = []  # type: List[int]
    j = len(route)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(route), 1 / 2))
        Invariant(Acc(list_pred(rb)))
        Invariant(0 <= j and j <= len(route))
        Invariant(dr == delim(ToSeq(route)))
        Invariant(ToSeq(rb) == esc_body(ToSeq(route).drop(j), dr))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        cr = route[j - 1]
        Assert(ToSeq(route).drop(j - 1)[0] == cr)
        Assert(ToSeq(route).drop(j - 1).drop(1) == ToSeq(route).drop(j))
        if cr == 92:
            rb = [92, 92] + rb
        elif cr == dr:
            rb = [92, cr] + rb
        else:
            rb = [cr] + rb
        j = j - 1
    Assert(ToSeq(route).drop(0) == ToSeq(route))
    q_route = [dr] + rb + [dr]  # type: List[int]
    Assert(ToSeq(q_route) == PSeq(dr) + ToSeq(rb) + PSeq(dr))
    Assert(ToSeq(rb) == esc_body(ToSeq(route), dr))
    Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
    Assert(dr == delim(ToSeq(route)))
    Assert(ToSeq(q_route) == quoted(ToSeq(route)))
    result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Every attack completed with a real verdict; no timeouts, no inconclusive runs.

BASELINE: positive_control.py is byte-identical to the bundle model.py; same-spec exit 0; weakness => CANDIDATE (verifies, 144.6s). All 10 attacks pass same-spec (exit 0), so each differs ONLY in the impl region.

### COMMANDS (each, from repo root):
  python -m swebench_unified.adversary weakness nagini django__django-14155 atk_N.py

### PER-ATTACK RESULTS (design -> observed):
  atk_1  prepatch bug A (func=func_path unconditionally, = bundle model_prepatch.py)          -> exit 2 NOT-A-COUNTEREXAMPLE (does not verify) [PREPATCH BUG REPRODUCED]
  atk_2  prepatch bug B (q_url=url_name, q_route=route, no quoting, = model_prepatch_2.py)    -> exit 2 NOT-A-COUNTEREXAMPLE (does not verify) [PREPATCH BUG REPRODUCED]
  atk_3  naive single-apostrophe wrap: no escaping, no delimiter switch (the idealization a prior pass named) -> exit 2 rejected
  atk_4  escaping kept but DELIMITER SWITCH dropped (delimiter hardwired to 39)               -> exit 2 rejected
  atk_5  PARTIAL-DOMAIN: exact on 32..126, emits 'XXX' outside (precondition-dead branch)     -> exit 0 CANDIDATE (223.2s)
  atk_6  BOUNDARY off-by-one: last code point of route dropped from the escaped body          -> exit 2 rejected
  atk_7  CONTROL-FLOW-EFFECT: correct value but diverges (unbounded spin loop) before return  -> exit 2 rejected (method-level MustTerminate bites)
  atk_8  UNGROUNDED-ORACLE ECHO: delimiter via explicit contains-test, negated func selection -> exit 0 CANDIDATE (574.6s)
  atk_9  delimiter rule INVERTED (34 iff contains 34 and not contains 39)                     -> exit 2 rejected
  atk_10 staged incremental assembly; its patch reverts the 4 elided fields to %s (leg 6)     -> exit 0 CANDIDATE (193.5s)

MATERIALIZED RESOLVE RUNS (mandatory step, swebench_unified.harness.run_resolve; patches built by really editing resolvers.py in a worktree and taking git diff, so context is exact; raw JSON in resolve_results.json):
  patch_atk5.diff  -> resolved=True  completed=True attempts=1 note='resolved'
  patch_atk8.diff  -> resolved=True  completed=True attempts=1 note='resolved'
  patch_atk10.diff -> resolved=True  completed=True attempts=1 note='resolved'
  patch_neg.diff (NEGATIVE CONTROL, prepatch A) -> resolved=False completed=True attempts=3 'consistent - not flaky'
Each of the three also passed the real suite locally in the worktree (103/103 urlpatterns_reverse tests OK with gold test_patch applied). Gold+test_patch baseline: 103/103 OK.

WHY atk_5 IS AN ECHO AND NOT A BREAK (the interesting case): its refinement is only licensed to differ OUTSIDE the precondition domain 32<=c<=126, and I measured the domain the graded oracle actually exercises by instrumenting the real ResolverMatch.__repr__ across the whole urlpatterns_reverse run: __repr__ is invoked on exactly 4 inputs -- (False,'no-kwargs','^no_kwargs/([0-9]+)/([0-9]+)/$'), (True,'partial','partial/'), (True,'partial_nested','partial_nested/'), (True,'partial_wrapped','partial_wrapped/') -- all printable ASCII, so the out-of-domain branch is unreachable under the oracle and the patch resolves. This is a COVERAGE narrowing (the spec-too-WEAK direction is bounded by the resolve oracle, which is the gate's own criterion), not a refinement-fidelity defect: the Requires is an executable domain statement, not prose, and the model claims nothing outside it.

VACUITY CONTROL (guards against 'everything is rejected because the precondition is unsatisfiable'): atk_vac.py = gold impl + Assert(False) at the top of impl -> exit 2 does not verify. So the precondition IS satisfiable and the 7 rejections above are meaningful rather than vacuous.

A-LEG AUDIT (my assigned focus; R/I pre-cleared by G-CONF). refinement.md has 7 legs, tags: 1=R, 2=R, 3=A-reference, 4=A-reference, 5=R+I, 6=I-collections, 7=R. NO kind-3 leg; axioms region is EMPTY and there is no @ContractOnly anywhere in model.py, so there is no consumed axiom to be unsound -- the only A legs are deep-model REFERENCES, checked mechanically:
  * indep_ax.py (51,912 cases, 0 divergences): pure region RE-ENCODED INDEPENDENTLY from model.py's own recursive definitions (not copied from axiom_check.py, so a shared-bug shadow cannot mask drift), differentially compared against the REAL gold-patched ResolverMatch in a worktree at base_commit + patch.diff. Covers quoted(s)=='%r'%s exhaustively for len<=2 over the full printable-ASCII alphabet and len-4 over {' " backslash a}, plus built_repr vs the real interpolation over 6 real callables (plain fn, partial, nested partial, update_wrapper'd partial, callable instance, functools.partial SUBCLASS) x anchor-spelling field texts, plus 40k fuzz at an independent seed (0xFEEDFACE). IMPORTANT: the elided collection fields are excised by TRUE POSITIONAL ARITHMETIC (segment lengths recomputed from the format string and asserted to reassemble the real string), never by replace()/search -- my first attempt used search-based excision and self-reported 114 bogus failures on fields that literally spell an anchor; with positional excision, 0.
  * probe_opaque.py (1,617 cases, 0 divergences): legs 3/5/7 -- func_path/func_repr are UNCONSTRAINED List[int] in the spec, so I checked the real interpolation really treats them opaquely: callables whose __module__/__name__ contain %-format chars ('%s','%r','%%','%(x)s','%d%d'), apostrophes, double quotes, backslashes, the literal head/label segments themselves, 300-char names, empty names; plus partial subclass, __name__-less callable instance, bare class object, partial-of-instance, update_wrapper'd partial. func=%s is a plain %s and the token is opaque, exactly as func_token models; every real token is representable as List[int].
  * leg 6 (I-collections) is the one leg whose licensed slack a patch can actually take, so I did not merely re-argue it -- I EXERCISED it: patch_atk10.diff leaves all four elided fields at the pre-patch %s and still resolves, confirming the elision is behaviour-preserving on the graded values. Independently verified '%r'=="%s" on the actual resolved values (args=(), kwargs={'name':'no_kwargs/42'}, app_names=[], namespaces=[] for all 4 observed inputs).

CORRESPONDENCE SPOT-CHECKS: literal segments byte-match the real post-patch format string (lit_head='ResolverMatch(func=', lit_url_name=', url_name=', lit_route=', route=', lit_tail=')'); leg 2's is_prebound<->isinstance(self.func, functools.partial) confirmed on the real fixtures, including empty_view_wrapped which HAS __name__ (update_wrapper) yet IS a partial, so the patch routes it to repr(func) and func_token keyed solely on is_prebound reproduces that -- matching the F2P expectation for partial_wrapped.

VERDICT SOUND: 10 same-spec attacks all completed; 7 rejected by the verifier (with a non-vacuous precondition proven by the Assert(False) control), 3 CANDIDATEs whose faithful patches were materialized and ALL RESOLVED under the official harness, with a negative control proving the resolve leg discriminates. No verify-but-wrong impl found; the A legs' correspondence to the real callees holds under ~53.5k independent machine-checked observations; no kind-3 leg.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_8.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 3 of 10 same-spec attacks came back CANDIDATE (share the spec AND verify): atk_5 (partial-domain), atk_8 (echo, restructured delimiter/selection), atk_10 (staged assembly, patch exercising the I-collections leg at full licensed extent). All three faithful refined patches were MATERIALIZED and RUN through the official harness (swebench_unified.harness.run_resolve) and ALL THREE RESOLVED (resolved=True completed=True attempts=1) => correct echoes, not spec weaknesses. Oracle discrimination proven by a negative control (prepatch behaviour A reverted, patch_neg.diff): resolved=False completed=True attempts=3 ('consistent - not flaky'), so 'resolved=True' above is a real signal and not a harness that passes everything. No verifying wrong impl whose patch fails to resolve was found; verify=>correct holds on this spec.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14155.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A resolved-URL match object renders a single-line, parenthesised textual
  description of the match. The description names the resolved callable, then
  the match name, then the route pattern, each introduced by its own ``field=``
  label and separated by a comma and a space.

  (A) Naming the callable. A directly-resolved callable is named by its dotted
      import path (module plus qualified name). A callable that was produced by
      pre-binding arguments to another callable carries no such name of its
      own, so for it the description instead reproduces that callable's own
      textual form (which exposes the underlying callable and the pre-bound
      arguments). The choice between the two is governed solely by whether the
      callable is such a pre-bound wrapper.

  (B) Rendering the textual fields. The match name and the route pattern are
      arbitrary text and are rendered in their *quoted* textual form, so that
      the boundary of the text is unambiguous, an empty value is visible, and
      the rendering can be read back unambiguously:

        * the value is delimited by one quote character on each side. The
          delimiter is the apostrophe (U+0027), except when the value itself
          contains an apostrophe and does not contain a double quote (U+0022);
          then the double quote is the delimiter, so that the apostrophes
          inside need no marking.
        * between the delimiters each code point of the value stands for
          itself, except that a backslash (U+005C) and any occurrence of the
          chosen delimiter are each preceded by an additional backslash.

      The two text fields range over printable ASCII (code points 32..126);
      that is the domain on which this quoted rendering is specified, and it is
      stated as a precondition below.

  (The collection fields the full description also carries between the callable
  name and the match name -- the positional arguments, the keyword arguments,
  and the two namespace lists -- are rendered in their canonical collection
  form, which for those collection values coincides with their plain textual
  form; carrying no behavioural distinction, they are elided from this model
  and accounted for in the refinement as an identity step.)

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by the pure sequence theory
``PSeq[int]``. The modelled portion of the description is the constant-shaped
front-to-back concatenation of the literal label segments with the rendered
field values. The behaviour is pure structure/selection over the inputs,
modelled deeply; no callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# axioms-end

# pure-start
@Pure
def lit_head() -> PSeq[int]:
    # 'ResolverMatch(func='
    return PSeq(82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
                40, 102, 117, 110, 99, 61)

@Pure
def lit_url_name() -> PSeq[int]:
    # ', url_name='
    return PSeq(44, 32, 117, 114, 108, 95, 110, 97, 109, 101, 61)

@Pure
def lit_route() -> PSeq[int]:
    # ', route='
    return PSeq(44, 32, 114, 111, 117, 116, 101, 61)

@Pure
def lit_tail() -> PSeq[int]:
    # ')'
    return PSeq(41)

@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff code point `x` occurs in `s`. Front-recursive so a single
    unfold is available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)

@Pure
def delim(s: PSeq[int]) -> int:
    """The quote character that delimits the quoted rendering of the text `s`:
    the apostrophe (39), except that a value which contains an apostrophe and
    no double quote is delimited by the double quote (34) instead, so that the
    apostrophes it contains need no marking."""
    if contains(s, 39) and not contains(s, 34):
        return 34
    return 39

@Pure
def esc_char(c: int, d: int) -> PSeq[int]:
    """How one code point `c` of a text value stands between delimiters `d`: a
    backslash (92) and the delimiter itself are each preceded by an additional
    backslash; every other code point stands for itself."""
    if c == 92:
        return PSeq(92, 92)
    if c == d:
        return PSeq(92, c)
    return PSeq(c)

@Pure
def esc_body(s: PSeq[int], d: int) -> PSeq[int]:
    """The inside of the quoted rendering of `s` under delimiter `d`: the
    per-code-point rendering applied elementwise. Front-recursive so a single
    unfold is available per loop step."""
    if len(s) == 0:
        return s
    return esc_char(s[0], d) + esc_body(s.drop(1), d)

@Pure
def quoted_with(s: PSeq[int], d: int) -> PSeq[int]:
    """The quoted rendering of `s` under an explicit delimiter `d`: the
    delimiter, then the elementwise-rendered body, then the same delimiter."""
    return PSeq(d) + esc_body(s, d) + PSeq(d)

@Pure
def quoted(s: PSeq[int]) -> PSeq[int]:
    """The quoted textual rendering of an arbitrary text value: the body
    rendered elementwise between two copies of the delimiter `delim` chooses."""
    return quoted_with(s, delim(s))

@Pure
def func_token(func_path: PSeq[int], func_repr: PSeq[int], is_prebound: bool) -> PSeq[int]:
    """The text naming the callable. A pre-bound wrapper has no dotted import
    name of its own, so its own textual form (`func_repr`, exposing the wrapped
    callable and pre-bound arguments) is used; otherwise the dotted import path
    (`func_path`) is used."""
    if is_prebound:
        return func_repr
    return func_path

@Pure
def built_repr(func_path: PSeq[int], func_repr: PSeq[int], is_prebound: bool,
               url_name: PSeq[int], route: PSeq[int]) -> PSeq[int]:
    """The modelled portion of the description: the constant-shaped concatenation of the
    label segments with the rendered field values. The callable name is
    selected by `func_token`; the match name and route are rendered `quoted`."""
    return (lit_head() + func_token(func_path, func_repr, is_prebound)
            + lit_url_name() + quoted(url_name)
            + lit_route() + quoted(route)
            + lit_tail())
# pure-end

def resolver_match_repr(func_path: List[int], func_repr: List[int], is_prebound: bool,
                        url_name: List[int], route: List[int]) -> List[int]:
    # pre-conditions-start
    # Every input is read-only (the rendering mutates nothing it is given), so
    # each is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(func_path), 1 / 2))
    Requires(Acc(list_pred(func_repr), 1 / 2))
    Requires(Acc(list_pred(url_name), 1 / 2))
    Requires(Acc(list_pred(route), 1 / 2))
    # The two text fields range over printable ASCII (32..126) -- the domain on
    # which the quoted rendering above is specified.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(url_name),
                                            32 <= url_name[k] and url_name[k] <= 126))))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(route),
                                            32 <= route[k] and route[k] <= 126))))
    Requires(MustTerminate(len(url_name) + len(route) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(func_path), 1 / 2))
    Ensures(Acc(list_pred(func_repr), 1 / 2))
    Ensures(Acc(list_pred(url_name), 1 / 2))
    Ensures(Acc(list_pred(route), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The description is exactly the constant-shaped concatenation, with the callable
    # named by `func_token` (so a pre-bound wrapper shows its own form, not a
    # name it does not have) and the match name and route rendered `quoted`.
    Ensures(ToSeq(Result()) == built_repr(
        ToSeq(func_path), ToSeq(func_repr), is_prebound,
        ToSeq(url_name), ToSeq(route)))
    # post-conditions-end
    # impl-start
    if is_prebound:
        func = func_repr  # type: List[int]
    else:
        func = func_path
    Assert(ToSeq(func) == func_token(ToSeq(func_path), ToSeq(func_repr), is_prebound))
    head = [82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
            40, 102, 117, 110, 99, 61]  # type: List[int]
    Assert(ToSeq(head) == lit_head())
    seg_url_name = [44, 32, 117, 114, 108, 95, 110, 97, 109, 101, 61]  # type: List[int]
    Assert(ToSeq(seg_url_name) == lit_url_name())
    seg_route = [44, 32, 114, 111, 117, 116, 101, 61]  # type: List[int]
    Assert(ToSeq(seg_route) == lit_route())
    cu = 0
    cr = 0
    du = delim(ToSeq(url_name))
    ub = []  # type: List[int]
    i = len(url_name)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(url_name), 1 / 2))
        Invariant(Acc(list_pred(ub)))
        Invariant(0 <= i and i <= len(url_name))
        Invariant(du == delim(ToSeq(url_name)))
        Invariant(ToSeq(ub) == esc_body(ToSeq(url_name).drop(i), du))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        cu = url_name[i - 1]
        Assert(ToSeq(url_name).drop(i - 1)[0] == cu)
        Assert(ToSeq(url_name).drop(i - 1).drop(1) == ToSeq(url_name).drop(i))
        if cu == 92:
            ub = [92, 92] + ub
        elif cu == du:
            ub = [92, cu] + ub
        else:
            ub = [cu] + ub
        i = i - 1
    Assert(ToSeq(url_name).drop(0) == ToSeq(url_name))
    q_url = [du] + ub + [du]  # type: List[int]
    Assert(ToSeq(q_url) == PSeq(du) + ToSeq(ub) + PSeq(du))
    Assert(ToSeq(ub) == esc_body(ToSeq(url_name), du))
    Assert(ToSeq(q_url) == quoted_with(ToSeq(url_name), du))
    Assert(du == delim(ToSeq(url_name)))
    Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))
    dr = delim(ToSeq(route))
    rb = []  # type: List[int]
    j = len(route)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(route), 1 / 2))
        Invariant(Acc(list_pred(rb)))
        Invariant(0 <= j and j <= len(route))
        Invariant(dr == delim(ToSeq(route)))
        Invariant(ToSeq(rb) == esc_body(ToSeq(route).drop(j), dr))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        cr = route[j - 1]
        Assert(ToSeq(route).drop(j - 1)[0] == cr)
        Assert(ToSeq(route).drop(j - 1).drop(1) == ToSeq(route).drop(j))
        if cr == 92:
            rb = [92, 92] + rb
        elif cr == dr:
            rb = [92, cr] + rb
        else:
            rb = [cr] + rb
        j = j - 1
    Assert(ToSeq(route).drop(0) == ToSeq(route))
    q_route = [dr] + rb + [dr]  # type: List[int]
    Assert(ToSeq(q_route) == PSeq(dr) + ToSeq(rb) + PSeq(dr))
    Assert(ToSeq(rb) == esc_body(ToSeq(route), dr))
    Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
    Assert(dr == delim(ToSeq(route)))
    Assert(ToSeq(q_route) == quoted(ToSeq(route)))
    result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Every attack completed with a real verdict; no timeouts, no inconclusive runs.

BASELINE: positive_control.py is byte-identical to the bundle model.py; same-spec exit 0; weakness => CANDIDATE (verifies, 144.6s). All 10 attacks pass same-spec (exit 0), so each differs ONLY in the impl region.

### COMMANDS (each, from repo root):
  python -m swebench_unified.adversary weakness nagini django__django-14155 atk_N.py

### PER-ATTACK RESULTS (design -> observed):
  atk_1  prepatch bug A (func=func_path unconditionally, = bundle model_prepatch.py)          -> exit 2 NOT-A-COUNTEREXAMPLE (does not verify) [PREPATCH BUG REPRODUCED]
  atk_2  prepatch bug B (q_url=url_name, q_route=route, no quoting, = model_prepatch_2.py)    -> exit 2 NOT-A-COUNTEREXAMPLE (does not verify) [PREPATCH BUG REPRODUCED]
  atk_3  naive single-apostrophe wrap: no escaping, no delimiter switch (the idealization a prior pass named) -> exit 2 rejected
  atk_4  escaping kept but DELIMITER SWITCH dropped (delimiter hardwired to 39)               -> exit 2 rejected
  atk_5  PARTIAL-DOMAIN: exact on 32..126, emits 'XXX' outside (precondition-dead branch)     -> exit 0 CANDIDATE (223.2s)
  atk_6  BOUNDARY off-by-one: last code point of route dropped from the escaped body          -> exit 2 rejected
  atk_7  CONTROL-FLOW-EFFECT: correct value but diverges (unbounded spin loop) before return  -> exit 2 rejected (method-level MustTerminate bites)
  atk_8  UNGROUNDED-ORACLE ECHO: delimiter via explicit contains-test, negated func selection -> exit 0 CANDIDATE (574.6s)
  atk_9  delimiter rule INVERTED (34 iff contains 34 and not contains 39)                     -> exit 2 rejected
  atk_10 staged incremental assembly; its patch reverts the 4 elided fields to %s (leg 6)     -> exit 0 CANDIDATE (193.5s)

MATERIALIZED RESOLVE RUNS (mandatory step, swebench_unified.harness.run_resolve; patches built by really editing resolvers.py in a worktree and taking git diff, so context is exact; raw JSON in resolve_results.json):
  patch_atk5.diff  -> resolved=True  completed=True attempts=1 note='resolved'
  patch_atk8.diff  -> resolved=True  completed=True attempts=1 note='resolved'
  patch_atk10.diff -> resolved=True  completed=True attempts=1 note='resolved'
  patch_neg.diff (NEGATIVE CONTROL, prepatch A) -> resolved=False completed=True attempts=3 'consistent - not flaky'
Each of the three also passed the real suite locally in the worktree (103/103 urlpatterns_reverse tests OK with gold test_patch applied). Gold+test_patch baseline: 103/103 OK.

WHY atk_5 IS AN ECHO AND NOT A BREAK (the interesting case): its refinement is only licensed to differ OUTSIDE the precondition domain 32<=c<=126, and I measured the domain the graded oracle actually exercises by instrumenting the real ResolverMatch.__repr__ across the whole urlpatterns_reverse run: __repr__ is invoked on exactly 4 inputs -- (False,'no-kwargs','^no_kwargs/([0-9]+)/([0-9]+)/$'), (True,'partial','partial/'), (True,'partial_nested','partial_nested/'), (True,'partial_wrapped','partial_wrapped/') -- all printable ASCII, so the out-of-domain branch is unreachable under the oracle and the patch resolves. This is a COVERAGE narrowing (the spec-too-WEAK direction is bounded by the resolve oracle, which is the gate's own criterion), not a refinement-fidelity defect: the Requires is an executable domain statement, not prose, and the model claims nothing outside it.

VACUITY CONTROL (guards against 'everything is rejected because the precondition is unsatisfiable'): atk_vac.py = gold impl + Assert(False) at the top of impl -> exit 2 does not verify. So the precondition IS satisfiable and the 7 rejections above are meaningful rather than vacuous.

A-LEG AUDIT (my assigned focus; R/I pre-cleared by G-CONF). refinement.md has 7 legs, tags: 1=R, 2=R, 3=A-reference, 4=A-reference, 5=R+I, 6=I-collections, 7=R. NO kind-3 leg; axioms region is EMPTY and there is no @ContractOnly anywhere in model.py, so there is no consumed axiom to be unsound -- the only A legs are deep-model REFERENCES, checked mechanically:
  * indep_ax.py (51,912 cases, 0 divergences): pure region RE-ENCODED INDEPENDENTLY from model.py's own recursive definitions (not copied from axiom_check.py, so a shared-bug shadow cannot mask drift), differentially compared against the REAL gold-patched ResolverMatch in a worktree at base_commit + patch.diff. Covers quoted(s)=='%r'%s exhaustively for len<=2 over the full printable-ASCII alphabet and len-4 over {' " backslash a}, plus built_repr vs the real interpolation over 6 real callables (plain fn, partial, nested partial, update_wrapper'd partial, callable instance, functools.partial SUBCLASS) x anchor-spelling field texts, plus 40k fuzz at an independent seed (0xFEEDFACE). IMPORTANT: the elided collection fields are excised by TRUE POSITIONAL ARITHMETIC (segment lengths recomputed from the format string and asserted to reassemble the real string), never by replace()/search -- my first attempt used search-based excision and self-reported 114 bogus failures on fields that literally spell an anchor; with positional excision, 0.
  * probe_opaque.py (1,617 cases, 0 divergences): legs 3/5/7 -- func_path/func_repr are UNCONSTRAINED List[int] in the spec, so I checked the real interpolation really treats them opaquely: callables whose __module__/__name__ contain %-format chars ('%s','%r','%%','%(x)s','%d%d'), apostrophes, double quotes, backslashes, the literal head/label segments themselves, 300-char names, empty names; plus partial subclass, __name__-less callable instance, bare class object, partial-of-instance, update_wrapper'd partial. func=%s is a plain %s and the token is opaque, exactly as func_token models; every real token is representable as List[int].
  * leg 6 (I-collections) is the one leg whose licensed slack a patch can actually take, so I did not merely re-argue it -- I EXERCISED it: patch_atk10.diff leaves all four elided fields at the pre-patch %s and still resolves, confirming the elision is behaviour-preserving on the graded values. Independently verified '%r'=="%s" on the actual resolved values (args=(), kwargs={'name':'no_kwargs/42'}, app_names=[], namespaces=[] for all 4 observed inputs).

CORRESPONDENCE SPOT-CHECKS: literal segments byte-match the real post-patch format string (lit_head='ResolverMatch(func=', lit_url_name=', url_name=', lit_route=', route=', lit_tail=')'); leg 2's is_prebound<->isinstance(self.func, functools.partial) confirmed on the real fixtures, including empty_view_wrapped which HAS __name__ (update_wrapper) yet IS a partial, so the patch routes it to repr(func) and func_token keyed solely on is_prebound reproduces that -- matching the F2P expectation for partial_wrapped.

VERDICT SOUND: 10 same-spec attacks all completed; 7 rejected by the verifier (with a non-vacuous precondition proven by the Assert(False) control), 3 CANDIDATEs whose faithful patches were materialized and ALL RESOLVED under the official harness, with a negative control proving the resolve leg discriminates. No verify-but-wrong impl found; the A legs' correspondence to the real callees holds under ~53.5k independent machine-checked observations; no kind-3 leg.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: find an input where the modeled function (resolver_match_repr / built_repr) disagrees with the real callee (ResolverMatch.__repr__ post-patch at 2f13c476ab). NONE FOUND after exhaustive + high-volume differential search. Verdict FAITHFUL.

SETUP: fresh worktree at base_commit 2f13c476abe4ba787b6cb71131818341911f43cc; gold patch (from data/swe_bench_verified/test.jsonl, matching patch.diff/refinement.md verbatim) applied by hand and byte-confirmed. Toolkit proven LIVE: same-spec on the unmodified model exits 0 ('SAME'); a one-character perturbation of the precondition (32->33) exits 1 with a diff -- so the harness is discriminating, not rubber-stamping.

### Evidence the spec does not overclaim
1. quoted(s) == '%r' % s, EXHAUSTIVELY, well beyond the bundle's own G-AX sweep: (a) all 866,496 strings of length<=3 over the full 95-char printable-ASCII alphabet; (b) all 88,573 strings of length<=10 over {' " \}; (c) all 488,281 of length<=8 over {' " \ a SP}; (d) all 960,800 of length<=7 over a regex-ish + quote alphabet. ~2.4M cases, ZERO mismatches. This is the part of the spec most likely to be an idealization (the classic failure is a single-quote-wrap model), and it is not: delim's quote-switch rule and esc_body's backslash/delimiter marking reproduce CPython exactly, including the both-quotes case ('both\'and"' keeps the apostrophe delimiter and marks it).
2. STRUCTURAL differential vs the real patched method WITHOUT trusting the bundle's own string-excision bridge: I re-inserted the elided collection fields at the format string's own positions and compared to repr() EXACTLY. 845 exhaustive critical-set cases (5 callable kinds x 13 quote/backslash-critical url_name x 13 route, covering plain function, class-based callable, partial, nested partial, update_wrapper'd partial) + 60,000 fuzz over the full printable range with args/kwargs/app_names/namespaces ALSO randomized. Zero divergences.
3. END-TO-END through the real resolver over the real urlconfs: 6 resolved paths (/partial/, /partial_nested/, /partial_wrapped/, /no_kwargs/..., etc.) all MATCH, and every url_name/route actually reaching __repr__ was inside the stated precondition (0 out-of-domain), so the domain restriction does not exclude real traffic.
4. ORACLE CONFIRMED: with gold patch + test patch, runtests.py urlpatterns_reverse.tests.ResolverMatchTests -> 5 tests OK (includes both F2P test_repr and test_repr_functools_partial).

### REFINEMENT CLAIMS INDEPENDENTLY CHECKED (these are where a faithfulness break usually hides, since they are prose, not verified):
- Step 6 / I-collections (the four elided fields): '%r' % v == '%s' % v held over 20,000 randomized tuples/dicts/lists whose ELEMENTS included newlines, tabs, backslashes and non-ASCII -- i.e. the identity survives inputs deliberately outside the text fields' domain, so eliding these fields is genuinely behaviour-preserving and not a hidden weakening.
- func_path/func_repr modeled as OPAQUE code-point strings (step 1, %s not %r): confirmed the real interpolation emits them VERBATIM even when they contain %s, %r, %%, and braces (func_path 'a%s.b.c%dd', '%r%%.v%s', and a partial whose repr carries '%s%r{}'). No second-pass interpolation, so opacity is sound.

PRECONDITION IS LOAD-BEARING AND HONESTLY PLACED (not a cheat): outside 32..126 the model IS unsound -- quoted != repr for '\n', '\t', '\r', '\x00', '\x7f', '\xa0' (repr uses \n / \xNN escapes the model does not encode). The spec states 32<=c<=126 as a real Requires, so it claims nothing there; and evidence 3 shows real url_name/route values land inside it. Restricting rather than overclaiming is the correct direction for faithfulness. Notably the two classes an over-strong spec would have excluded -- backslash (Django routes like ^\d+/$ are ORDINARY input) and apostrophe (drives the delimiter switch) -- are INSIDE the modeled domain and inside every sweep, so the spec is if anything stronger than it needed to be while still matching reality.
- Nagini: unmodified model.py verifies (143s). VACUITY CONTROL per standing practice: Assert(False) injected at impl-start FAILS ('Assertion False might not hold'), so the precondition is satisfiable and the postcondition is not vacuously discharged.
- G-AX and G-CONF re-run by me from scratch: both exit 0 and reproduce their recorded gate details EXACTLY (49 boundary + 20000 fuzz + 5 repr + 5000 fuzz; 100046 = 46 boundary + 100000 fuzz, seed 14155), confirming the gates ran against these very files.

ONE BOOKKEEPING DEFECT (NOT a faithfulness break, reported for completeness): meta.json's recorded region_hashes disagree with the current files for 'pure', 'pre-conditions', 'impl' and 'spec_view' ('post-conditions' matches). No bundle file matches the record (model.py, model_prepatch.py, model_prepatch_2.py all differ identically), and the two prepatch variants ARE spec-identical to model.py under markers.spec_view, so G-DIFF's shared-spec premise still holds. Since both gate scripts reproduce their recorded counts exactly, this is stale provenance from before the model was strengthened (the domain widened to full printable ASCII / escaping added), not evidence the audited artifact differs from the gated one. It should be refreshed, but it does not affect the faithfulness verdict. Separately, meta.json's patch_diff field holds the placeholder string 'gold patch verbatim (applies cleanly at base_commit)' rather than the diff text; I verified the actual gold patch against the SWE-bench record instead.

CONCLUSION: I could not produce a single input inside the stated precondition on which the modeled function disagrees with the real post-patch ResolverMatch.__repr__. The spec is not too strong and does not drift from real repo behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: show the spec view (model.py minus impl+invariants) discloses the gold edit beyond the solver-visible problem_statement (hints_text excluded; hints_text is empty for this instance anyway). NO LEAK FOUND under the gate's operative criteria. All work in /tmp (worktree, removed+pruned after).

BASELINE / PROVENANCE
- Spec view derived independently via swebench_unified.markers.spec_view(model.py, nagini) = 8259 chars. Confirmed the ELISION is real: 0 occurrences of 'Invariant', 'while ', 'Assert(', 'q_url', 'seg_url_name' in the view -- the entire back-to-front escaping fold and all proof scaffolding are gone; only the docstring, imports, empty axioms region, pure region, signature, pre/post conditions survive.
- region_hashes(model.py) re-derived and compared to meta.json G-HYGIENE: all 6 match byte-for-byte, incl. spec_view=a8264578b0ca37f0... So I screened the FROZEN spec view, not a drifted copy.
- Re-ran the mechanical screen myself (leakage.screen on model.py, nagini tables, real gold patch + PS): PASSED, hard_failures=[], warnings=[]. Matches recorded G-LEAK 'spec view clean'. No RELAXED_LEAKAGE.md, meta.relaxed_leakage=None, G-LEAK status='pass' -- so the panel_3 deference path in construct/build_one.py does NOT apply; I judged this on the merits.

L1 - NO GOLD LINE REPRODUCED (stricter than the shipped screen). The built-in check uses normalized-substring at length>=16. I re-ran it at threshold 8 over every added/removed gold line, and additionally computed the longest common normalized substring of each gold line against the spec view:
- 'if isinstance(self.func, functools.partial):' -> lcs 0
- 'func = repr(self.func)' -> lcs 0
- 'func = self._func_path' -> lcs 'func_path' (9)
- "'ResolverMatch(func=%s, args=%r, kwargs=%r, url_name=%r, '" -> lcs "'ResolverMatch(func=" (20)
- "'app_names=%r, namespaces=%r, route=%r)' % (" -> lcs 'namespace' (9)
Only 'return (' and ')' match, which are content-free. The one 20-char hit, ResolverMatch(func=, is NOT edit-specific: I read django/urls/resolvers.py at base_commit 2f13c476 and the PRE-patch line already contains "ResolverMatch(func=%s, ...", and the PS itself names ResolverMatch.__repr__(). It is public repo text on both sides of the diff, so it localizes nothing.
- No diff markers ('@@', 'diff --git', '+++ ', '--- ', index). No patched path: 'resolvers.py' and 'django/' are absent from the view.

L2 - NO IDENTIFIER ECHOING A PATCHED SYMBOL. Extracted all spec-view identifiers via AST. Absent entirely: functools, partial, isinstance, repr(self.func), _func_path (as such), app_names, namespaces, ResolverMatch, __repr__, update_wrapper, resolvers. Present: func_path, func_repr, is_prebound, url_name, route, quoted, delim, esc_char, esc_body, func_token, built_repr, resolver_match_repr. url_name/route are field labels present in the PRE-patch format string (context, not edit-specific); is_prebound/func_repr/func_token are de-narrated abstractions that deliberately avoid the functools.partial vocabulary. Note the gold hunk's only def/class token is __repr__, which is a CONTEXT line, so _patch_changed_symbols returns only {'getitem'} -- the mechanical symbol check was structurally blind here, which is why I checked the patched-symbol list by hand rather than trusting it.

L3 - NO BUG/FIX NARRATION. _NARRATION_RE over the view: zero hits. Hand-scanned for change-narration the regex misses ('no longer', 'now', 'instead of', 'used to', 'formerly', 'unquoted', 'rather than', 'old', 'new', '%r', '%s', 'format string', 'interpolat', 'unwrap', 'unhelpful'): the only hits are benign non-temporal uses -- 'was produced by' (describing pre-binding, not a past repo state) and two uses of 'instead' that select between two spec branches, not between old and new code. The docstring opens 'stated as desired behaviour, not as an edit' and holds to it: no diagnosis, no mechanism, no reference to a prior state.

THE ONE SUBSTANTIVE SEMANTIC FINDING (reported, not charged as the verdict). Behaviour (B) -- that url_name and route are rendered QUOTED (spec-view lines 18-30: 'rendered in their *quoted* textual form', the apostrophe/double-quote delimiter switch, the backslash marking) -- appears NOWHERE in the problem_statement. I confirmed by scan: quot, %r, repr(, delimit, apostroph, backslash, escape, url_name, route, unambig are ALL absent from the PS, which is exclusively about functools.partial rendering as 'functools.partial'.

I then made (B)'s load-bearing status a FACT rather than a claim: I built an (A)-only variant on the real worktree (partial handling added, every field left at %s), applied the real test_patch, and ran urlpatterns_reverse.tests.ResolverMatchTests -> Ran 5 tests, FAILED (failures=4). Diffs are exactly the missing quotes (url_name=partial vs url_name='partial', route=partial/ vs route='partial/'). So (B) is an independently-tested requirement the PS does not state, and a faithful spec (one whose prepatch twin fails -- cf. model_prepatch_2.py, G-DIFF pass) MUST pin it. This is the structural signature of a problem_statement<->gold mismatch.

Why this is nonetheless NOT a LEAKAGE verdict: the gate's operative definition (docs/architecture.md G-LEAK; spec_guide directive 6) bans reproducing a diff line, diff markers, the patched path, an identifier echoing a patched symbol, and narration of the bug/fix MECHANISM -- and directs the spec to 'state the abstract desired behavior'. (B) is stated in exactly that register: purely behavioural, in code-point/delimiter terms, naming no repo symbol, no %r conversion, no format string, no file, no prior state. A solver reading it learns WHAT the rendering must be, never that an edit changed %s to %r or where.

Treating PS-absent-but-tested behaviour as leakage per se would make the gate vacuous, since modes 1/2 exist precisely to hand the solver a spec whose contract pins the required behaviour (pass criterion = resolve); on that reading no bundle could ever pass. Consistent with that, only 20/500 nagini bundles carry a relaxation, and the granted ones (psf-6028's userinfo '@'-join, django-15252's bookkeeping-table write effect) each had to name gold INTERNALS or a mechanism to stay faithful. This spec does not.

RESIDUAL FOR A REVIEWER (my one recommendation, not a defect I can prove): if the project wants PS-absent tested discriminators dispositioned on the record even when stated abstractly, this cell is the archetype -- behaviour (B), spec-view line 19 ('arbitrary text and are rendered in their *quoted* textual form, so that'), is 4-test-failures load-bearing and PS-silent, and would warrant a RELAXED_LEAKAGE.md + meta.relaxed_leakage=true. I did not submit LEAKAGE because no leak-defining criterion is met.

INCIDENTAL (outside my gate, flagged as fact): patch.diff is NOT present in the bundle directory (contents: model.py, model_prepatch.py, model_prepatch_2.py, axiom_check.py, conformance_check.py, properties.py, mapping.md, refinement.md, meta.json, verdict.md, pbt_result.json). meta.json's patch_diff field holds only the prose 'gold patch verbatim (applies cleanly at base_commit)', so I could not git-apply --check it; G-RESOLVE is recorded pass (resolved, non-flaky). Also note refinement.md and mapping.md quote the gold hunk verbatim, but both are private artifacts blocked from solver shell reads by eval/audit.py's our-bundle-access pattern and are not part of the spec view, so they are not a leakage vector.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
