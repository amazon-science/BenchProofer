# P2 adversarial audit — sphinx-doc__sphinx-7889

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 10 same-spec attacks run; 3 verified (atk_7/8/9) and ALL THREE materialized faithful patches RESOLVED under the official harness (F2P test_MockObject + all 5 P2P passing, patch_successfully_applied=True) => correct echoes, not spec weaknesses. verify=>correct holds on every probe.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -122,18 +122,11 @@
             == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
     # post-conditions-end
     # impl-start
-    # Reduce the index to its textual rendering FIRST, so the string-only
-    # fabricator receives an honest string for EVERY index.  The rendering is
-    # always textual, so the fabricator's textual precondition (name_is_text)
-    # is met unconditionally -- independent of key_is_text.
-    name_is_text = True
-    name = render_text(ToSeq(key_text))
-    # Hand the (now textual) name to the fabricator; its textual precondition
-    # name_is_text is discharged here.  This call is the operation that fails
-    # for a non-textual name argument.
+    # PREPATCH: index handed on UNCHANGED, no textual rendering first.
+    name_is_text = key_is_text
+    name = ToSeq(key_text)
     produced = display_name(name_is_text, name, ToSeq(module))
-    Assert(produced == ToSeq(module) + PSeq(46) + name)
-    # Materialise the display name the fabricator describes.
+
     result = []  # type: List[int]
     i = 0
     while i < len(module):
@@ -142,14 +135,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # Bounded loop: the strictly decreasing, bounded-below measure
-        # len(module) - i discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(module) - i + 1))
         # invariants-end
         result = result + [module[i]]
         Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(module))
     result = result + [46]
     j = 0
     while j < len(key_text):
@@ -159,13 +149,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(key_text))
         Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
-        # Bounded loop: measure len(key_text) - j, strictly decreasing and
-        # bounded below, discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(key_text) - j + 1))
         # invariants-end
         result = result + [key_text[j]]
         Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -167,5 +167,19 @@
         Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
         j = j + 1
     Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
+    # DIVERGENCE: spin forever instead of delivering the placeholder.
+    # All permissions the postcondition needs are carried through the
+    # loop, and the display-name equality is maintained -- so under a
+    # PARTIAL-correctness reading this body satisfies the postcondition
+    # vacuously while never returning the placeholder.  Only
+    # MustTerminate can reject it.
+    while 0 < 1:
+        # invariants-start
+        Invariant(Acc(list_pred(module), 1 / 2))
+        Invariant(Acc(list_pred(key_text), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
+        # invariants-end
+        result = result
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -122,18 +122,10 @@
             == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
     # post-conditions-end
     # impl-start
-    # Reduce the index to its textual rendering FIRST, so the string-only
-    # fabricator receives an honest string for EVERY index.  The rendering is
-    # always textual, so the fabricator's textual precondition (name_is_text)
-    # is met unconditionally -- independent of key_is_text.
     name_is_text = True
     name = render_text(ToSeq(key_text))
-    # Hand the (now textual) name to the fabricator; its textual precondition
-    # name_is_text is discharged here.  This call is the operation that fails
-    # for a non-textual name argument.
     produced = display_name(name_is_text, name, ToSeq(module))
-    Assert(produced == ToSeq(module) + PSeq(46) + name)
-    # Materialise the display name the fabricator describes.
+
     result = []  # type: List[int]
     i = 0
     while i < len(module):
@@ -142,15 +134,12 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # Bounded loop: the strictly decreasing, bounded-below measure
-        # len(module) - i discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(module) - i + 1))
         # invariants-end
         result = result + [module[i]]
         Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(module))
-    result = result + [46]
+    result = result + [47]
     j = 0
     while j < len(key_text):
         # invariants-start
@@ -159,13 +148,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(key_text))
         Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
-        # Bounded loop: measure len(key_text) - j, strictly decreasing and
-        # bounded below, discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(key_text) - j + 1))
         # invariants-end
         result = result + [key_text[j]]
         Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -122,18 +122,9 @@
             == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
     # post-conditions-end
     # impl-start
-    # Reduce the index to its textual rendering FIRST, so the string-only
-    # fabricator receives an honest string for EVERY index.  The rendering is
-    # always textual, so the fabricator's textual precondition (name_is_text)
-    # is met unconditionally -- independent of key_is_text.
     name_is_text = True
     name = render_text(ToSeq(key_text))
-    # Hand the (now textual) name to the fabricator; its textual precondition
-    # name_is_text is discharged here.  This call is the operation that fails
-    # for a non-textual name argument.
     produced = display_name(name_is_text, name, ToSeq(module))
-    Assert(produced == ToSeq(module) + PSeq(46) + name)
-    # Materialise the display name the fabricator describes.
     result = []  # type: List[int]
     i = 0
     while i < len(module):
@@ -142,30 +133,25 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # Bounded loop: the strictly decreasing, bounded-below measure
-        # len(module) - i discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(module) - i + 1))
         # invariants-end
         result = result + [module[i]]
         Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(module))
     result = result + [46]
-    j = 0
-    while j < len(key_text):
-        # invariants-start
-        Invariant(Acc(list_pred(module), 1 / 2))
-        Invariant(Acc(list_pred(key_text), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(key_text))
-        Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
-        # Bounded loop: measure len(key_text) - j, strictly decreasing and
-        # bounded below, discharges the caller-held termination obligation.
-        Invariant(MustTerminate(len(key_text) - j + 1))
-        # invariants-end
-        result = result + [key_text[j]]
-        Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
-        j = j + 1
-    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
+    if key_is_text:
+        j = 0
+        while j < len(key_text):
+            # invariants-start
+            Invariant(Acc(list_pred(module), 1 / 2))
+            Invariant(Acc(list_pred(key_text), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= j and j <= len(key_text))
+            Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
+            Invariant(MustTerminate(len(key_text) - j + 1))
+            # invariants-end
+            result = result + [key_text[j]]
+            Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
+            j = j + 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -122,18 +122,10 @@
             == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
     # post-conditions-end
     # impl-start
-    # Reduce the index to its textual rendering FIRST, so the string-only
-    # fabricator receives an honest string for EVERY index.  The rendering is
-    # always textual, so the fabricator's textual precondition (name_is_text)
-    # is met unconditionally -- independent of key_is_text.
     name_is_text = True
     name = render_text(ToSeq(key_text))
-    # Hand the (now textual) name to the fabricator; its textual precondition
-    # name_is_text is discharged here.  This call is the operation that fails
-    # for a non-textual name argument.
     produced = display_name(name_is_text, name, ToSeq(module))
-    Assert(produced == ToSeq(module) + PSeq(46) + name)
-    # Materialise the display name the fabricator describes.
+
     result = []  # type: List[int]
     i = 0
     while i < len(module):
@@ -142,30 +134,24 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # Bounded loop: the strictly decreasing, bounded-below measure
-        # len(module) - i discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(module) - i + 1))
         # invariants-end
         result = result + [module[i]]
         Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(module))
     result = result + [46]
     j = 0
-    while j < len(key_text):
+    while j < len(key_text) - 1:
         # invariants-start
         Invariant(Acc(list_pred(module), 1 / 2))
         Invariant(Acc(list_pred(key_text), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(key_text))
         Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
-        # Bounded loop: measure len(key_text) - j, strictly decreasing and
-        # bounded below, discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(key_text) - j + 1))
         # invariants-end
         result = result + [key_text[j]]
         Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -122,18 +122,11 @@
             == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
     # post-conditions-end
     # impl-start
-    # Reduce the index to its textual rendering FIRST, so the string-only
-    # fabricator receives an honest string for EVERY index.  The rendering is
-    # always textual, so the fabricator's textual precondition (name_is_text)
-    # is met unconditionally -- independent of key_is_text.
     name_is_text = True
     name = render_text(ToSeq(key_text))
-    # Hand the (now textual) name to the fabricator; its textual precondition
-    # name_is_text is discharged here.  This call is the operation that fails
-    # for a non-textual name argument.
     produced = display_name(name_is_text, name, ToSeq(module))
-    Assert(produced == ToSeq(module) + PSeq(46) + name)
-    # Materialise the display name the fabricator describes.
+    module[0] = 65
+
     result = []  # type: List[int]
     i = 0
     while i < len(module):
@@ -142,14 +135,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # Bounded loop: the strictly decreasing, bounded-below measure
-        # len(module) - i discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(module) - i + 1))
         # invariants-end
         result = result + [module[i]]
         Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(module))
     result = result + [46]
     j = 0
     while j < len(key_text):
@@ -159,13 +149,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(key_text))
         Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
-        # Bounded loop: measure len(key_text) - j, strictly decreasing and
-        # bounded below, discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(key_text) - j + 1))
         # invariants-end
         result = result + [key_text[j]]
         Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -122,18 +122,10 @@
             == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
     # post-conditions-end
     # impl-start
-    # Reduce the index to its textual rendering FIRST, so the string-only
-    # fabricator receives an honest string for EVERY index.  The rendering is
-    # always textual, so the fabricator's textual precondition (name_is_text)
-    # is met unconditionally -- independent of key_is_text.
     name_is_text = True
-    name = render_text(ToSeq(key_text))
-    # Hand the (now textual) name to the fabricator; its textual precondition
-    # name_is_text is discharged here.  This call is the operation that fails
-    # for a non-textual name argument.
+    name = PSeq()  # type: PSeq[int]
     produced = display_name(name_is_text, name, ToSeq(module))
-    Assert(produced == ToSeq(module) + PSeq(46) + name)
-    # Materialise the display name the fabricator describes.
+
     result = []  # type: List[int]
     i = 0
     while i < len(module):
@@ -142,14 +134,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # Bounded loop: the strictly decreasing, bounded-below measure
-        # len(module) - i discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(module) - i + 1))
         # invariants-end
         result = result + [module[i]]
         Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(module))
     result = result + [46]
     j = 0
     while j < len(key_text):
@@ -159,13 +148,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(key_text))
         Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
-        # Bounded loop: measure len(key_text) - j, strictly decreasing and
-        # bounded below, discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(key_text) - j + 1))
         # invariants-end
         result = result + [key_text[j]]
         Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -122,18 +122,14 @@
             == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
     # post-conditions-end
     # impl-start
-    # Reduce the index to its textual rendering FIRST, so the string-only
-    # fabricator receives an honest string for EVERY index.  The rendering is
-    # always textual, so the fabricator's textual precondition (name_is_text)
-    # is met unconditionally -- independent of key_is_text.
     name_is_text = True
     name = render_text(ToSeq(key_text))
-    # Hand the (now textual) name to the fabricator; its textual precondition
-    # name_is_text is discharged here.  This call is the operation that fails
-    # for a non-textual name argument.
     produced = display_name(name_is_text, name, ToSeq(module))
-    Assert(produced == ToSeq(module) + PSeq(46) + name)
-    # Materialise the display name the fabricator describes.
+    if 0 in ToSeq(key_text):
+        Assert(False)
+        result2 = []  # type: List[int]
+        return result2
+
     result = []  # type: List[int]
     i = 0
     while i < len(module):
@@ -142,14 +138,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # Bounded loop: the strictly decreasing, bounded-below measure
-        # len(module) - i discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(module) - i + 1))
         # invariants-end
         result = result + [module[i]]
         Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(module))
     result = result + [46]
     j = 0
     while j < len(key_text):
@@ -159,13 +152,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(key_text))
         Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
-        # Bounded loop: measure len(key_text) - j, strictly decreasing and
-        # bounded below, discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(key_text) - j + 1))
         # invariants-end
         result = result + [key_text[j]]
         Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
     return result
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -122,18 +122,6 @@
             == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
     # post-conditions-end
     # impl-start
-    # Reduce the index to its textual rendering FIRST, so the string-only
-    # fabricator receives an honest string for EVERY index.  The rendering is
-    # always textual, so the fabricator's textual precondition (name_is_text)
-    # is met unconditionally -- independent of key_is_text.
-    name_is_text = True
-    name = render_text(ToSeq(key_text))
-    # Hand the (now textual) name to the fabricator; its textual precondition
-    # name_is_text is discharged here.  This call is the operation that fails
-    # for a non-textual name argument.
-    produced = display_name(name_is_text, name, ToSeq(module))
-    Assert(produced == ToSeq(module) + PSeq(46) + name)
-    # Materialise the display name the fabricator describes.
     result = []  # type: List[int]
     i = 0
     while i < len(module):
@@ -142,14 +130,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # Bounded loop: the strictly decreasing, bounded-below measure
-        # len(module) - i discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(module) - i + 1))
         # invariants-end
         result = result + [module[i]]
         Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(module))
     result = result + [46]
     j = 0
     while j < len(key_text):
@@ -159,13 +144,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(key_text))
         Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
-        # Bounded loop: measure len(key_text) - j, strictly decreasing and
-        # bounded below, discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(key_text) - j + 1))
         # invariants-end
         result = result + [key_text[j]]
         Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
     return result
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -122,18 +122,9 @@
             == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
     # post-conditions-end
     # impl-start
-    # Reduce the index to its textual rendering FIRST, so the string-only
-    # fabricator receives an honest string for EVERY index.  The rendering is
-    # always textual, so the fabricator's textual precondition (name_is_text)
-    # is met unconditionally -- independent of key_is_text.
     name_is_text = True
-    name = render_text(ToSeq(key_text))
-    # Hand the (now textual) name to the fabricator; its textual precondition
-    # name_is_text is discharged here.  This call is the operation that fails
-    # for a non-textual name argument.
-    produced = display_name(name_is_text, name, ToSeq(module))
-    Assert(produced == ToSeq(module) + PSeq(46) + name)
-    # Materialise the display name the fabricator describes.
+    produced = display_name(name_is_text, ToSeq(module), render_text(ToSeq(key_text)))
+
     result = []  # type: List[int]
     i = 0
     while i < len(module):
@@ -142,14 +133,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # Bounded loop: the strictly decreasing, bounded-below measure
-        # len(module) - i discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(module) - i + 1))
         # invariants-end
         result = result + [module[i]]
         Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(module))
     result = result + [46]
     j = 0
     while j < len(key_text):
@@ -159,13 +147,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(key_text))
         Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
-        # Bounded loop: measure len(key_text) - j, strictly decreasing and
-        # bounded below, discharges the caller-held termination obligation.
         Invariant(MustTerminate(len(key_text) - j + 1))
         # invariants-end
         result = result + [key_text[j]]
         Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7889.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A placeholder object that stands in for an unavailable import must support
  being *subscripted* by an arbitrary index value and, for ANY such index,
  yield a fresh placeholder whose human-readable display name is

      <module> "." <text-of-the-index>

  where <text-of-the-index> is the canonical textual rendering of whatever
  index value was supplied.  The index need NOT already be textual: a
  non-textual index (e.g. a type parameter used to write a parametrised
  generic) is just as valid as a textual one, and the operation must still
  succeed and name the result after the index's textual rendering.

  The helper that fabricates the placeholder subclass is defined ONLY for an
  honest textual name: it builds the display name by textual concatenation and
  uses the name to construct the subclass.  Both require an honest string, and
  constructing the subclass additionally rejects a name carrying a NUL code
  point or a surrogate code point (neither has a valid encoded-text form for a
  class name).

A value is modelled as a pair (is_text, text): `text` is the `List[int]` of
Unicode code points of its canonical textual rendering, and `is_text` records
whether the value is *already* textual.  Textual rendering is total: every
value has a rendering and the rendering is itself textual, so handing the
rendering on always satisfies a string-only consumer, whereas handing a raw
subscript value on only does so when that value was already textual.  The
subclass-fabrication helper is the unchanged callee, modelled by the
`@ContractOnly` contract `display_name`, whose precondition is exactly that its
name argument is an honest textual name (validated == the real helper by
axiom_check.py / G-AX).

Subscripting is bounded work — render the index, fabricate the placeholder,
materialise its display name — and must actually RETURN that placeholder to
its caller.  A partial-correctness reading would let a diverging body satisfy
the display-name postcondition vacuously, so the contract carries an explicit
total-correctness obligation (MustTerminate).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def display_name(name_is_text: bool, name: PSeq[int],
                 module: PSeq[int]) -> PSeq[int]:
    """The unchanged placeholder-subclass fabricator, abstracted to the one
    observable property the subscript behaviour pins: the display name it
    assigns is `module`, a single separator code point, then `name`.

    It is DEFINED ONLY for a textual `name` (`name_is_text`) whose code points
    are all honest scalar values: no NUL (code point 0) and no surrogate code
    point (55296..57343).  The body concatenates `name` onto a string (failing
    for a non-textual argument) AND constructs a class object named `name` --
    class construction rejects a name containing a NUL code point, and it also
    rejects a surrogate code point because a surrogate has no encoded-text
    form for the class name.  All three halves of this precondition are the
    weakest the proof needs and match the real helper -- it claims nothing on
    inputs the real helper rejects.  Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX).
    """
    Requires(name_is_text and not (0 in name))
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(name),
        not (55296 <= name[k] and name[k] <= 57343))))
    Ensures(Result() == module + PSeq(46) + name)   # 46 == ord('.')
# axioms-end

# pure-start
@Pure
def render_text(value_text: PSeq[int]) -> PSeq[int]:
    """Canonical textual rendering of a value, as the code-point sequence of
    its text.  Rendering is the identity on the text content (every value
    already carries its canonical textual form here); crucially its result is
    always textual, regardless of whether the value itself was textual."""
    Ensures(Result() == value_text)
    return value_text
# pure-end

def subscript_placeholder(key_is_text: bool, key_text: List[int],
                          module: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(key_text), 1 / 2))
    Requires(Acc(list_pred(module), 1 / 2))
    # The index's textual rendering consists of honest scalar code points: no
    # interior NUL (code point 0) and no surrogate code point (55296..57343).
    # True of the textual rendering of every index the operation must handle
    # (type parameters, types, numbers, ordinary names), and required by the
    # string-only fabricator, which rejects a name carrying either kind of
    # non-scalar code point.
    Requires(not (0 in ToSeq(key_text)))
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(key_text),
        not (55296 <= ToSeq(key_text)[k] and ToSeq(key_text)[k] <= 57343))))
    # TERMINATION: subscripting must actually DELIVER the placeholder -- it is
    # bounded work (render the index, fabricate, materialise the display
    # name).  Nagini is a partial-correctness verifier by default, so without
    # this obligation an implementation that diverges before returning would
    # satisfy the display-name postcondition vacuously yet never produce the
    # placeholder; the real operation always returns one.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key_text), 1 / 2))
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The display name of the produced placeholder is the module, a single
    # separator code point, then the textual rendering of the index -- and this
    # holds for EVERY index, textual or not (the postcondition does NOT assume
    # key_is_text).  This is exactly the display name the textual-only fabricator
    # assigns to a name handed to it (its Ensures: module ++ [sep] ++ name); here
    # the name is the index's textual rendering.
    Ensures(ToSeq(Result())
            == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
    # post-conditions-end
    # impl-start
    # Reduce the index to its textual rendering FIRST, so the string-only
    # fabricator receives an honest string for EVERY index.  The rendering is
    # always textual, so the fabricator's textual precondition (name_is_text)
    # is met unconditionally -- independent of key_is_text.
    name_is_text = True
    name = render_text(ToSeq(key_text))
    # Hand the (now textual) name to the fabricator; its textual precondition
    # name_is_text is discharged here.  This call is the operation that fails
    # for a non-textual name argument.
    produced = display_name(name_is_text, name, ToSeq(module))
    Assert(produced == ToSeq(module) + PSeq(46) + name)
    # Materialise the display name the fabricator describes.
    result = []  # type: List[int]
    i = 0
    while i < len(module):
        # invariants-start
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(module))
        Invariant(ToSeq(result) == ToSeq(module).take(i))
        # Bounded loop: the strictly decreasing, bounded-below measure
        # len(module) - i discharges the caller-held termination obligation.
        Invariant(MustTerminate(len(module) - i + 1))
        # invariants-end
        result = result + [module[i]]
        Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
        i = i + 1
    Assert(ToSeq(result) == ToSeq(module))
    result = result + [46]
    j = 0
    while j < len(key_text):
        # invariants-start
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(key_text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(key_text))
        Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
        # Bounded loop: measure len(key_text) - j, strictly decreasing and
        # bounded below, discharges the caller-held termination obligation.
        Invariant(MustTerminate(len(key_text) - j + 1))
        # invariants-end
        result = result + [key_text[j]]
        Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
        j = j + 1
    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, sphinx-doc__sphinx-7889 (nagini). Scratch: All 11 files (10 attacks + positive control) confirmed byte-identical spec via `adversary same-spec`; only the impl region was edited (positive_control.py is byte-identical to bundle model.py).

COMMANDS: per file, `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7889 <f>.py` (SBU_ATTACK_VERIFY_TIMEOUT=900), results in res/<f>.{out,exit}; rejection reasons via `adversary verify ...` in res/<f>.why; resolve via harness.run_resolve(timeout=2400, retries=1) in res/<f>.resolve.

REJECTED (exit 2, same-spec, does NOT verify) - each on its INTENDED obligation, confirmed from the verifier error text:
- atk_1 PREPATCH BUG re-encoded (name_is_text = key_is_text; raw index handed to the string-only fabricator): 'precondition of function display_name might not hold. Assertion name_is_text might not hold' = the modelled image of the real _make_subclass(TypeVar) TypeError. PREPATCH REPRODUCED.
- atk_2 DIVERGENCE / control-flow-effect (unbounded `while 0 < 1` inserted before the return, carrying ALL permissions and the display-name equality as invariants so a partial-correctness reading would satisfy the postcondition vacuously): 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context' = MustTerminate(2) genuinely closes the vacuity hole. NOTE: my first two atk_2 drafts failed for BOGUS reasons (a redeclared `result` type error, then an invariant well-formedness/permission error); I rewrote it twice until it failed on TERMINATION specifically, so the MustTerminate leg is really exercised rather than accidentally rejected.
- atk_3 wrong separator (47='/' instead of 46='.'): loop invariant / display-name equality fails.
- atk_4 PARTIAL DOMAIN + control-flow effect (append the rendered index only `if key_is_text`, i.e. emit 'module.' for a TypeVar index instead of raising): Postcondition of subscript_placeholder might not hold - the postcondition deliberately does NOT assume key_is_text, so the whole partial-domain class is excluded.
- atk_5 BOUNDARY off-by-one (`while j < len(key_text) - 1`, drops the last code point: '~T'->'~'): Postcondition fails; also covers the empty-index boundary.
- atk_6 SIDE EFFECT on a read-only-lent input (`module[0] = 65`, the repo image of corrupting self.__display_name__ for every later placeholder): 'precondition of module[0] = 65 might not hold. There might be insufficient permission' - the Acc(...,1/2) fractional permission forbids it.
- atk_10 A-LEG ARGUMENT SWAP (hand `module` to the fabricator as the NAME and the rendered index as the module): 'precondition of function display_name might not hold. Assertion (not (0 in name)) might not hold'. This is the key A-leg check: the caller's precondition constrains ONLY key_text (module is deliberately unconstrained), so the axiom's NUL/surrogate halves are genuinely DISCHARGED FROM the caller's contract and cannot be satisfied by an arbitrary argument. The A-consumed leg is load-bearing, not decorative.

CANDIDATES (exit 0, same-spec AND verify) - all three materialized to faithful refined patches (generated in a real clone at base_commit ec9af606, so each applies) and RUN through the official harness:
- atk_7 UNGROUNDED-ORACLE ECHO / A-leg decoupling: the fabricator IS called with an honest EMPTY name (textual precondition discharged) but never receives the index rendering; the display name comes from the loops alone. RESOLVED=True COMPLETED=True, patch_applied=True, F2P=['test_MockObject'] success / failure=[], all 5 P2P success.
- atk_8 VACUOUS-GUARD partial domain: branch on `0 in key_text`, made infeasible by the caller's precondition (Assert(False) inside is the control that the branch is dead), returning [] there. RESOLVED=True COMPLETED=True, F2P+P2P all pass. The dead branch is unreachable in the real repo too (a NUL-bearing rendering is out of domain and the real type() raises ValueError there), so the echo is behaviourally faithful.
- atk_9 A-LEG DROPPED entirely: no fabricator call; _make_subclass's body inlined at the subscript site. RESOLVED=True COMPLETED=True, F2P+P2P all pass.
All three are CORRECT ECHOES of the gold (they still coerce the index with str(key) before the name is used), NOT spec weaknesses - per build_one._derive_audit_verdict a candidate whose patch resolves must not fail the gate.

WHY TIGHT: the postcondition ToSeq(Result()) == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)), with render_text pinned to the identity by its own Ensures, fully determines the output as module ++ [46] ++ key_text INDEPENDENT of key_is_text; MustTerminate(2) forbids divergence; the fractional Acc permissions forbid input mutation. Any same-spec verifying impl must therefore deliver exactly the gold display content for EVERY index, textual or not - which is precisely the str(key) coercion the gold patch adds.

REFINEMENT.MD AUDIT (all legs R / A-consumed / A-reference / I; NO kind-3): legs 1,2 = R (key: Any <-> (key_is_text, key_text: List[int]) with key_is_text == isinstance(key,str), key_text == [ord(c) for c in str(key)]; str <-> List[int] code points) - correct, and the str->Any signature widening is exactly the issue's content.

Leg 3 = I + A-reference (render_text <-> str(key)) - this is the leg carrying the FIX and it is modelled DEEPLY (name_is_text = True because the rendering is always textual), not hidden behind an axiom about the changed function __getitem__; I falsification-probed the A-reference claim that str() is total and str-valued: it holds for TypeVar/int/type/tuple/slice/Ellipsis/None/str, and the only counterexamples (__str__ raising, __str__ returning non-str, __str__ = None) break the GOLD PATCH identically, so they are not a model<->patch divergence.

Leg 4 = A-consumed (display_name <-> the UNCHANGED callee _make_subclass, mock.py:71-76) - correspondence verified by direct execution against a verbatim replica of the real callee body (probe_type.py): all 20 axiom-ADMITTED names ('', '~T', '.', dotted, space, newline, tab, digit-leading, non-ASCII, astral U+1F600, U+10FFFF, U+FEFF, U+2028, 10k-long, U+D7FF and U+E000 just outside the surrogate window, 0x01, 0x7f) SUCCEED with Ensures __display_name__ == module + '.' + name holding exactly, and all 5 EXCLUDED classes raise (TypeVar/int/list -> TypeError, NUL -> ValueError, lone surrogate -> UnicodeEncodeError). So the three-half precondition is the weakest sound one - no over-claim (nothing promised where the real callee raises) and no under-claim gap I could exploit.

Leg 5 = R (loop materialisation <-> the fabricated subclass's __display_name__, with the trailing () instantiation folded in as observationally irrelevant to the F2P assertions, which check only construction success, __doc__ and isinstance) - sound for this test set. The '## No kind-3' section is present and its claim checks out: the genuinely-changed operation is leg 3, modelled deeply.

VERDICT SOUND: 10 distinct same-spec attacks (>= 5 floor) all run to completion; the prepatch bug reproduced and rejected on the exact modelled TypeError; the positive control verifies (18.6s); 3 candidates ALL resolve-checked through the official harness and all RESOLVED. No verifying wrong impl whose faithful patch fails to resolve was found - verify => correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 10 same-spec attacks run; 3 verified (atk_7/8/9) and ALL THREE materialized faithful patches RESOLVED under the official harness (F2P test_MockObject + all 5 P2P passing, patch_successfully_applied=True) => correct echoes, not spec weaknesses. verify=>correct holds on every probe.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7889.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A placeholder object that stands in for an unavailable import must support
  being *subscripted* by an arbitrary index value and, for ANY such index,
  yield a fresh placeholder whose human-readable display name is

      <module> "." <text-of-the-index>

  where <text-of-the-index> is the canonical textual rendering of whatever
  index value was supplied.  The index need NOT already be textual: a
  non-textual index (e.g. a type parameter used to write a parametrised
  generic) is just as valid as a textual one, and the operation must still
  succeed and name the result after the index's textual rendering.

  The helper that fabricates the placeholder subclass is defined ONLY for an
  honest textual name: it builds the display name by textual concatenation and
  uses the name to construct the subclass.  Both require an honest string, and
  constructing the subclass additionally rejects a name carrying a NUL code
  point or a surrogate code point (neither has a valid encoded-text form for a
  class name).

A value is modelled as a pair (is_text, text): `text` is the `List[int]` of
Unicode code points of its canonical textual rendering, and `is_text` records
whether the value is *already* textual.  Textual rendering is total: every
value has a rendering and the rendering is itself textual, so handing the
rendering on always satisfies a string-only consumer, whereas handing a raw
subscript value on only does so when that value was already textual.  The
subclass-fabrication helper is the unchanged callee, modelled by the
`@ContractOnly` contract `display_name`, whose precondition is exactly that its
name argument is an honest textual name (validated == the real helper by
axiom_check.py / G-AX).

Subscripting is bounded work — render the index, fabricate the placeholder,
materialise its display name — and must actually RETURN that placeholder to
its caller.  A partial-correctness reading would let a diverging body satisfy
the display-name postcondition vacuously, so the contract carries an explicit
total-correctness obligation (MustTerminate).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def display_name(name_is_text: bool, name: PSeq[int],
                 module: PSeq[int]) -> PSeq[int]:
    """The unchanged placeholder-subclass fabricator, abstracted to the one
    observable property the subscript behaviour pins: the display name it
    assigns is `module`, a single separator code point, then `name`.

    It is DEFINED ONLY for a textual `name` (`name_is_text`) whose code points
    are all honest scalar values: no NUL (code point 0) and no surrogate code
    point (55296..57343).  The body concatenates `name` onto a string (failing
    for a non-textual argument) AND constructs a class object named `name` --
    class construction rejects a name containing a NUL code point, and it also
    rejects a surrogate code point because a surrogate has no encoded-text
    form for the class name.  All three halves of this precondition are the
    weakest the proof needs and match the real helper -- it claims nothing on
    inputs the real helper rejects.  Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX).
    """
    Requires(name_is_text and not (0 in name))
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(name),
        not (55296 <= name[k] and name[k] <= 57343))))
    Ensures(Result() == module + PSeq(46) + name)   # 46 == ord('.')
# axioms-end

# pure-start
@Pure
def render_text(value_text: PSeq[int]) -> PSeq[int]:
    """Canonical textual rendering of a value, as the code-point sequence of
    its text.  Rendering is the identity on the text content (every value
    already carries its canonical textual form here); crucially its result is
    always textual, regardless of whether the value itself was textual."""
    Ensures(Result() == value_text)
    return value_text
# pure-end

def subscript_placeholder(key_is_text: bool, key_text: List[int],
                          module: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(key_text), 1 / 2))
    Requires(Acc(list_pred(module), 1 / 2))
    # The index's textual rendering consists of honest scalar code points: no
    # interior NUL (code point 0) and no surrogate code point (55296..57343).
    # True of the textual rendering of every index the operation must handle
    # (type parameters, types, numbers, ordinary names), and required by the
    # string-only fabricator, which rejects a name carrying either kind of
    # non-scalar code point.
    Requires(not (0 in ToSeq(key_text)))
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(key_text),
        not (55296 <= ToSeq(key_text)[k] and ToSeq(key_text)[k] <= 57343))))
    # TERMINATION: subscripting must actually DELIVER the placeholder -- it is
    # bounded work (render the index, fabricate, materialise the display
    # name).  Nagini is a partial-correctness verifier by default, so without
    # this obligation an implementation that diverges before returning would
    # satisfy the display-name postcondition vacuously yet never produce the
    # placeholder; the real operation always returns one.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key_text), 1 / 2))
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The display name of the produced placeholder is the module, a single
    # separator code point, then the textual rendering of the index -- and this
    # holds for EVERY index, textual or not (the postcondition does NOT assume
    # key_is_text).  This is exactly the display name the textual-only fabricator
    # assigns to a name handed to it (its Ensures: module ++ [sep] ++ name); here
    # the name is the index's textual rendering.
    Ensures(ToSeq(Result())
            == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
    # post-conditions-end
    # impl-start
    # Reduce the index to its textual rendering FIRST, so the string-only
    # fabricator receives an honest string for EVERY index.  The rendering is
    # always textual, so the fabricator's textual precondition (name_is_text)
    # is met unconditionally -- independent of key_is_text.
    name_is_text = True
    name = render_text(ToSeq(key_text))
    # Hand the (now textual) name to the fabricator; its textual precondition
    # name_is_text is discharged here.  This call is the operation that fails
    # for a non-textual name argument.
    produced = display_name(name_is_text, name, ToSeq(module))
    Assert(produced == ToSeq(module) + PSeq(46) + name)
    # Materialise the display name the fabricator describes.
    result = []  # type: List[int]
    i = 0
    while i < len(module):
        # invariants-start
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(module))
        Invariant(ToSeq(result) == ToSeq(module).take(i))
        # Bounded loop: the strictly decreasing, bounded-below measure
        # len(module) - i discharges the caller-held termination obligation.
        Invariant(MustTerminate(len(module) - i + 1))
        # invariants-end
        result = result + [module[i]]
        Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
        i = i + 1
    Assert(ToSeq(result) == ToSeq(module))
    result = result + [46]
    j = 0
    while j < len(key_text):
        # invariants-start
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(key_text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(key_text))
        Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
        # Bounded loop: measure len(key_text) - j, strictly decreasing and
        # bounded below, discharges the caller-held termination obligation.
        Invariant(MustTerminate(len(key_text) - j + 1))
        # invariants-end
        result = result + [key_text[j]]
        Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
        j = j + 1
    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, sphinx-doc__sphinx-7889 (nagini). Scratch: All 11 files (10 attacks + positive control) confirmed byte-identical spec via `adversary same-spec`; only the impl region was edited (positive_control.py is byte-identical to bundle model.py).

COMMANDS: per file, `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7889 <f>.py` (SBU_ATTACK_VERIFY_TIMEOUT=900), results in res/<f>.{out,exit}; rejection reasons via `adversary verify ...` in res/<f>.why; resolve via harness.run_resolve(timeout=2400, retries=1) in res/<f>.resolve.

REJECTED (exit 2, same-spec, does NOT verify) - each on its INTENDED obligation, confirmed from the verifier error text:
- atk_1 PREPATCH BUG re-encoded (name_is_text = key_is_text; raw index handed to the string-only fabricator): 'precondition of function display_name might not hold. Assertion name_is_text might not hold' = the modelled image of the real _make_subclass(TypeVar) TypeError. PREPATCH REPRODUCED.
- atk_2 DIVERGENCE / control-flow-effect (unbounded `while 0 < 1` inserted before the return, carrying ALL permissions and the display-name equality as invariants so a partial-correctness reading would satisfy the postcondition vacuously): 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context' = MustTerminate(2) genuinely closes the vacuity hole. NOTE: my first two atk_2 drafts failed for BOGUS reasons (a redeclared `result` type error, then an invariant well-formedness/permission error); I rewrote it twice until it failed on TERMINATION specifically, so the MustTerminate leg is really exercised rather than accidentally rejected.
- atk_3 wrong separator (47='/' instead of 46='.'): loop invariant / display-name equality fails.
- atk_4 PARTIAL DOMAIN + control-flow effect (append the rendered index only `if key_is_text`, i.e. emit 'module.' for a TypeVar index instead of raising): Postcondition of subscript_placeholder might not hold - the postcondition deliberately does NOT assume key_is_text, so the whole partial-domain class is excluded.
- atk_5 BOUNDARY off-by-one (`while j < len(key_text) - 1`, drops the last code point: '~T'->'~'): Postcondition fails; also covers the empty-index boundary.
- atk_6 SIDE EFFECT on a read-only-lent input (`module[0] = 65`, the repo image of corrupting self.__display_name__ for every later placeholder): 'precondition of module[0] = 65 might not hold. There might be insufficient permission' - the Acc(...,1/2) fractional permission forbids it.
- atk_10 A-LEG ARGUMENT SWAP (hand `module` to the fabricator as the NAME and the rendered index as the module): 'precondition of function display_name might not hold. Assertion (not (0 in name)) might not hold'. This is the key A-leg check: the caller's precondition constrains ONLY key_text (module is deliberately unconstrained), so the axiom's NUL/surrogate halves are genuinely DISCHARGED FROM the caller's contract and cannot be satisfied by an arbitrary argument. The A-consumed leg is load-bearing, not decorative.

CANDIDATES (exit 0, same-spec AND verify) - all three materialized to faithful refined patches (generated in a real clone at base_commit ec9af606, so each applies) and RUN through the official harness:
- atk_7 UNGROUNDED-ORACLE ECHO / A-leg decoupling: the fabricator IS called with an honest EMPTY name (textual precondition discharged) but never receives the index rendering; the display name comes from the loops alone. RESOLVED=True COMPLETED=True, patch_applied=True, F2P=['test_MockObject'] success / failure=[], all 5 P2P success.
- atk_8 VACUOUS-GUARD partial domain: branch on `0 in key_text`, made infeasible by the caller's precondition (Assert(False) inside is the control that the branch is dead), returning [] there. RESOLVED=True COMPLETED=True, F2P+P2P all pass. The dead branch is unreachable in the real repo too (a NUL-bearing rendering is out of domain and the real type() raises ValueError there), so the echo is behaviourally faithful.
- atk_9 A-LEG DROPPED entirely: no fabricator call; _make_subclass's body inlined at the subscript site. RESOLVED=True COMPLETED=True, F2P+P2P all pass.
All three are CORRECT ECHOES of the gold (they still coerce the index with str(key) before the name is used), NOT spec weaknesses - per build_one._derive_audit_verdict a candidate whose patch resolves must not fail the gate.

WHY TIGHT: the postcondition ToSeq(Result()) == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)), with render_text pinned to the identity by its own Ensures, fully determines the output as module ++ [46] ++ key_text INDEPENDENT of key_is_text; MustTerminate(2) forbids divergence; the fractional Acc permissions forbid input mutation. Any same-spec verifying impl must therefore deliver exactly the gold display content for EVERY index, textual or not - which is precisely the str(key) coercion the gold patch adds.

REFINEMENT.MD AUDIT (all legs R / A-consumed / A-reference / I; NO kind-3): legs 1,2 = R (key: Any <-> (key_is_text, key_text: List[int]) with key_is_text == isinstance(key,str), key_text == [ord(c) for c in str(key)]; str <-> List[int] code points) - correct, and the str->Any signature widening is exactly the issue's content.

Leg 3 = I + A-reference (render_text <-> str(key)) - this is the leg carrying the FIX and it is modelled DEEPLY (name_is_text = True because the rendering is always textual), not hidden behind an axiom about the changed function __getitem__; I falsification-probed the A-reference claim that str() is total and str-valued: it holds for TypeVar/int/type/tuple/slice/Ellipsis/None/str, and the only counterexamples (__str__ raising, __str__ returning non-str, __str__ = None) break the GOLD PATCH identically, so they are not a model<->patch divergence.

Leg 4 = A-consumed (display_name <-> the UNCHANGED callee _make_subclass, mock.py:71-76) - correspondence verified by direct execution against a verbatim replica of the real callee body (probe_type.py): all 20 axiom-ADMITTED names ('', '~T', '.', dotted, space, newline, tab, digit-leading, non-ASCII, astral U+1F600, U+10FFFF, U+FEFF, U+2028, 10k-long, U+D7FF and U+E000 just outside the surrogate window, 0x01, 0x7f) SUCCEED with Ensures __display_name__ == module + '.' + name holding exactly, and all 5 EXCLUDED classes raise (TypeVar/int/list -> TypeError, NUL -> ValueError, lone surrogate -> UnicodeEncodeError). So the three-half precondition is the weakest sound one - no over-claim (nothing promised where the real callee raises) and no under-claim gap I could exploit.

Leg 5 = R (loop materialisation <-> the fabricated subclass's __display_name__, with the trailing () instantiation folded in as observationally irrelevant to the F2P assertions, which check only construction success, __doc__ and isinstance) - sound for this test set. The '## No kind-3' section is present and its claim checks out: the genuinely-changed operation is leg 3, modelled deeply.

VERDICT SOUND: 10 distinct same-spec attacks (>= 5 floor) all run to completion; the prepatch bug reproduced and rejected on the exact modelled TypeError; the positive control verifies (18.6s); 3 candidates ALL resolve-checked through the official harness and all RESOLVED. No verifying wrong impl whose faithful patch fails to resolve was found - verify => correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: find an input where the modeled `subscript_placeholder` spec disagrees with the real `_MockObject.__getitem__` / `_make_subclass` at base_commit ec9af606c. NONE FOUND after exhaustive + fuzz differential testing.

SETUP. Worktree of sphinx-doc_sphinx.git at ec9af606c under /tmp (removed after). Real `sphinx/ext/autodoc/mock.py` loaded standalone via a source-exec loader with only `sphinx.util.logging` stubbed (the full package import dies on an unrelated jinja2 `environmentfilter` incompatibility), in two variants: unpatched, and patched by textual substitution of the gold hunk (anchor asserted present). So `mock[key]` IS the real patched subscript and `_make_subclass` IS the real callee -- nothing transliterated.

EVIDENCE 1 -- domain boundary is EXACT, not conservative (the strongest over-claim vector). Exhaustive sweep of all 1,114,112 code points, each as a SOLE index and as an INTERIOR index ('a'+c+'b'), through the real patched `__getitem__`: rejects are exactly {0x0 -> ValueError, 0xD800..0xDFFF -> UnicodeEncodeError} in both positions. That is byte-for-byte the two exclusions the spec's `Requires` carves out (`not (0 in ToSeq(key_text))` and the surrogate Forall). Zero unexpected-ok (spec would have been too weak) and zero unexpected-err (spec would have been too strong / drifted). Every in-domain result equalled `module + '.' + key_text`, matching the Ensures. A separate bare `type(name,(object,),{})` sweep over all code points reproduced the identical reject set, confirming the rejection lives in `type()` as mapping.md sec 3.1 claims.

EVIDENCE 2 -- differential fuzz, spec postcondition vs real patched repo: 40,448 Requires-satisfying samples, 0 disagreements. Keys spanned the F2P shape `TypeVar('T')` (the issue's `mock.SomeClass[T]`), covariant TypeVars, classes, `int`/`object`/`type`/`Exception`, 10**40, floats incl. inf/nan, None, bools, list/tuple/dict/frozenset/bytes/complex/Ellipsis/range/slice, `typing.List[int]`/`Optional`/`Any`/`Union`, builtins, `_MockObject` and instances, NotImplemented, 5000-char strings, and astral/BMP-boundary/combining/BOM/line-separator code points; modules included '', 'a.b', and deliberately NUL-bearing and surrogate-bearing modules. The NUL/surrogate modules all AGREE, confirming the spec correctly leaves `module` unconstrained (the callee only concatenates it) -- an unnecessary module precondition would have been drift, and there isn't one.

EVIDENCE 3 -- the A-consumed axiom `display_name` does not over-claim on its declared domain: 64,708 direct calls to the real `_make_subclass` (exhaustive 2-char cross product over a 33-element boundary code-point set x 6 modules, + 60,000 seeded fuzz over all non-surrogate code points, + names of length 1/1k/100k/1M). Zero Ensures violations, zero unexpected raises, and every result `issubclass` of the real `_MockObject`. So the precondition is sufficient (nothing in-domain raises) and evidence 1 shows it is necessary (everything excluded does raise) -- it is the weakest matching contract, as mapping.md claims.

EVIDENCE 4 -- the folded-in `()` instantiation and subclass identity are faithful: 20,000 fuzzed names, every `_make_subclass(name, module, _MockObject)()` succeeded with correct `__display_name__` and `isinstance`. Iterated subscripting chains correctly (`mod.~T.<class 'int'>.x.5...`), a 2000-deep chain returns, and a 500k-char module x 500k-char key returns a 1,000,001-char display name -- corroborating that the real operation is bounded work that always returns, so the `MustTerminate(2)` total-correctness obligation is faithful (strengthening, but not drift: real never diverges).

EVIDENCE 5 -- spec region byte-identical (`same-spec` RC=0 on an unmodified copy) and the bundle model verifies under the pinned verifier (`nagini_verify.sh` -> 'Verification successful', RC=0), so the artifact I audited is the shipped one.

### CANDIDATE DIVERGENCES CONSIDERED AND REJECTED (not spec defects):
(a) Non-deterministic `__str__`: a key whose `__str__` increments a counter yields bridge `key_text='call1'` while the real call produces `'mod.call2'`. This is an artifact of the type-abstraction bijection `key_text == [ord(c) for c in str(key)]`, which presumes `str` is a function of the value; the real `__getitem__` calls `str(key)` exactly once and names the result after THAT rendering, which is precisely what the spec says. No single-valued input diverges.
(b) `__str__` that raises (`RuntimeError`): the value has no bridge image at all, so no `key_text` exists and the spec asserts nothing. Silence, not a wrong claim.
(c) Parent with a non-`str` `__display_name__` makes the real code raise `TypeError`, but the model carrier for `module` is `List[int]` (always textual) and this state is unreachable in the real repo: the class default is the `str` `'_MockObject'` and `_make_subclass` always assigns `module + '.' + name`, itself a `str`.

CONCLUSION: the spec neither over-claims nor drifts. Its accept/reject boundary coincides exactly with CPython's `type()` name validation as exercised through the real patched `__getitem__`, its postcondition matches the real display name on every tested in-domain input, its axiom is sound on its full declared domain, and its termination obligation reflects real behaviour. No diverging input exists to cite, so I do not claim a faithfulness defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: judged the consumer spec view of model.py (markers.spec_view with NaginiBackend.language) against the SOLVER-VISIBLE problem_statement only; hints_text is empty and was excluded by rule.

### Machine-checked facts
1. Mechanical screen: leakage.screen(model.py, nagini, patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. No relaxation flag set (relaxed_leakage absent, no RELAXED_LEAKAGE.md, recorded G-LEAK status=pass), so the honor-the-relaxation path does not apply.
2. Patched artifacts vs spec view: patched file 'sphinx/ext/autodoc/mock.py' -> absent from spec view. Distinctive patched symbols {'getitem','iter'} -> both absent. None of the 4 gold changed lines (def __getitem__(self, key: str/Any) ...; return _make_subclass(key/str(key), self.__display_name__, self.__class__)()) appear in any form. Spec-view identifiers are wholly abstract: subscript_placeholder, display_name, render_text, key_is_text, key_text, module, name, name_is_text, value_text -- no echo of __getitem__, _make_subclass, str, Any, or __display_name__. No diff markers.
3. DISCRIMINATOR CONFINEMENT (the decisive test): same_spec(model.py, model_prepatch.py) = True and their spec views are BYTE-IDENTICAL (sha 015f97068669bb92b1b816505e2f0163176efcaafc79fb766de74a5f65ff229c for both). A full-text diff of the two files shows the ONLY textual difference lies inside impl-start..impl-end (name_is_text = True / name = render_text(...) vs name_is_text = key_is_text / name = ToSeq(key_text)). The gold-vs-prepatch discriminator is therefore provably invisible in the consumer view, which renders the impl region as '...  # implementation elided'.

### Attacks I mounted and why each fails
(a) 'render_text in the pure region names the fix.' Strongest available attack, and it fails on three grounds: (i) the public problem_statement ALREADY discloses the fix shape verbatim -- 'a TypeError is thrown as Autodoc's `mock._make_subclass` attempts to concatenate a `str` to a `TypeVar`' plus 'Expected: docs can still be built when generics are involved'. A solver reading only the public text already knows the str-only callee is being handed a TypeVar and must receive text. (ii) render_text is the IDENTITY (Ensures(Result() == value_text)), so the postcondition is semantically just module ++ [46] ++ key_text; it is spec vocabulary needed to state the observable at all, not a pointer into the impl. (iii) It is not even load-bearing: an impl could set name = ToSeq(key_text) directly and still verify, so its presence does not dictate the edit.

(b) 'display_name's name_is_text Requires leaks the discriminator's dual.' Fails: the flag sits on the axiom modelling the UNCHANGED callee _make_subclass, and its str-only nature is exactly what the problem_statement states. The impl-side choice of what to pass for that flag is the discriminator, and per fact 3 it is elided.

(c) 'The docstring narrates the change.' Fails: it is phrased as desired behaviour ('stated as desired behaviour, not as an edit'), and the narration vocabulary scan over the spec view found no hit -- only 'diverges before returning' (termination prose) and 'not as an edit' (an explicit disclaimer), neither of which localizes anything.

(d) 'The NUL/surrogate preconditions are extra-public detail.' Conceded that CPython type() rejecting NUL/surrogate class names is NOT in the problem_statement -- but it is not edit-discriminating: it constrains the input domain, appears IDENTICALLY in the pre-patch spec view (fact 3), and gives a solver no purchase on the str-coercion edit. It is callee-faithfulness detail (G-AX territory), not leakage.

(e) 'Instance id in docstring line 1.' Names the repo/instance, not the edit; the problem_statement itself identifies the project and issue nearly uniquely. Metadata by bundle convention, not gold-edit leakage.

CONCLUSION: everything the spec view reveals about the change is either already public in problem_statement or non-discriminating; the gold edit is confined to the elided impl region, proven by byte-identical spec views between the gold and pre-patch models. NO-LEAKAGE.

OUT-OF-GATE OBSERVATION (does not affect this verdict, flagged for the bundle owner): meta.json's TOP-LEVEL region_hashes block is stale relative to the released bytes. Current model.py (clean in git, no local edits) hashes to spec_view=015f9706..., axioms=d848e64b..., which matches meta.gates['G-HYGIENE'].data.region_hashes exactly; the top-level block records spec_view=063fc2fe... plus differing axioms/pre-conditions/invariants/impl. Since G-HYGIENE is the authority for region hashes and its record matches the live bytes, I judged the live artifact, and the screen above ran on those same bytes. The stale top-level copy appears to be a leftover from an earlier revision and is a bookkeeping inconsistency worth restamping.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
