# P2 adversarial audit — django__django-15930

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -120,7 +119,6 @@
     Requires(Acc(list_pred(pred_params), 1 / 2))
     Requires(Acc(list_pred(cons), 1 / 2))
     Requires(Acc(list_pred(cons_params), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(pred), 1 / 2))
@@ -143,163 +141,79 @@
     Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
     # post-conditions-end
     # impl-start
-    # Determine the predicate slot text and its parameters: the supplied
-    # predicate when non-empty, otherwise the constant always-true predicate.
+# PRE-PATCH: predicate slot = supplied pred verbatim, no substitution.
     cond_text = []  # type: List[int]
     cond_params = []  # type: List[int]
-    if len(pred) == 0:
-        k = 0
-        while k < len(true_predicate()):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(0 <= k and k <= len(true_predicate()))
-            Invariant(ToSeq(cond_text) == true_predicate().take(k))
-            Invariant(MustTerminate(len(true_predicate()) - k + 1))
-            # invariants-end
-            cond_text = cond_text + [true_predicate()[k]]
-            k = k + 1
-        Assert(true_predicate().take(len(true_predicate())) == true_predicate())
-        Assert(ToSeq(cond_text) == true_predicate())
-        k = 0
-        while k < len(true_params()):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_params)))
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(ToSeq(cond_text) == true_predicate())
-            Invariant(0 <= k and k <= len(true_params()))
-            Invariant(ToSeq(cond_params) == true_params().take(k))
-            Invariant(MustTerminate(len(true_params()) - k + 1))
-            # invariants-end
-            cond_params = cond_params + [true_params()[k]]
-            k = k + 1
-        Assert(true_params().take(len(true_params())) == true_params())
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the else branch proves the
-        # other disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
-    else:
-        k = 0
-        while k < len(pred):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(Acc(list_pred(pred), 1 / 2))
-            Invariant(len(pred) > 0)
-            Invariant(0 <= k and k <= len(pred))
-            Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
-            Invariant(MustTerminate(len(pred) - k + 1))
-            # invariants-end
-            cond_text = cond_text + [pred[k]]
-            k = k + 1
-        Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
-        k = 0
-        while k < len(pred_params):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_params)))
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(Acc(list_pred(pred), 1 / 2))
-            Invariant(Acc(list_pred(pred_params), 1 / 2))
-            Invariant(len(pred) > 0)
-            Invariant(ToSeq(cond_text) == ToSeq(pred))
-            Invariant(0 <= k and k <= len(pred_params))
-            Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
-            Invariant(MustTerminate(len(pred_params) - k + 1))
-            # invariants-end
-            cond_params = cond_params + [pred_params[k]]
-            k = k + 1
-        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
-        Assert(ToSeq(cond_params) == ToSeq(pred_params))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
-        Assert(len(pred) != 0)
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the if branch proves the other
-        # disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
-    # The disjunctive predicate-slot fact survives the merge. It pins cond_text
-    # and cond_params to the pure clause definitions and forces the predicate
-    # slot to be non-empty.
-    Assert(clause_text(ToSeq(pred), ToSeq(cons)) ==
-           lead() + ToSeq(cond_text) + sep() + ToSeq(cons))
-    Assert(clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)) ==
-           ToSeq(cond_params) + ToSeq(cons_params))
-    Assert(len(cond_text) > 0)
-    # Assemble lead + predicate-slot + sep + consequent.
+    k = 0
+    while k < len(pred):
+        Invariant(Acc(list_pred(cond_text)))
+        Invariant(Acc(list_pred(pred), 1 / 2))
+        Invariant(0 <= k and k <= len(pred))
+        Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
+        cond_text = cond_text + [pred[k]]
+        k = k + 1
+    Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
+    k = 0
+    while k < len(pred_params):
+        Invariant(Acc(list_pred(cond_params)))
+        Invariant(Acc(list_pred(cond_text)))
+        Invariant(Acc(list_pred(pred), 1 / 2))
+        Invariant(Acc(list_pred(pred_params), 1 / 2))
+        Invariant(ToSeq(cond_text) == ToSeq(pred))
+        Invariant(0 <= k and k <= len(pred_params))
+        Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
+        cond_params = cond_params + [pred_params[k]]
+        k = k + 1
+    Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
     text = []  # type: List[int]
     i = 0
     while i < len(lead()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(0 <= i and i <= len(lead()))
         Invariant(ToSeq(text) == lead().take(i))
-        Invariant(MustTerminate(len(lead()) - i + 1))
-        # invariants-end
         text = text + [lead()[i]]
         i = i + 1
     i = 0
     while i < len(cond_text):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(cond_text))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
-        Invariant(MustTerminate(len(cond_text) - i + 1))
-        # invariants-end
         text = text + [cond_text[i]]
         i = i + 1
     i = 0
     while i < len(sep()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(sep()))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
-        Invariant(MustTerminate(len(sep()) - i + 1))
-        # invariants-end
         text = text + [sep()[i]]
         i = i + 1
     i = 0
     while i < len(cons):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(Acc(list_pred(cons), 1 / 2))
         Invariant(0 <= i and i <= len(cons))
-        Invariant(ToSeq(text) ==
-                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
-        Invariant(MustTerminate(len(cons) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
         text = text + [cons[i]]
         i = i + 1
-    # Combined parameters: predicate-slot parameters then consequent parameters.
     params = []  # type: List[int]
     i = 0
     while i < len(cond_params):
-        # invariants-start
         Invariant(Acc(list_pred(params)))
         Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(0 <= i and i <= len(cond_params))
         Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
-        Invariant(MustTerminate(len(cond_params) - i + 1))
-        # invariants-end
         params = params + [cond_params[i]]
         i = i + 1
     i = 0
     while i < len(cons_params):
-        # invariants-start
         Invariant(Acc(list_pred(params)))
         Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(Acc(list_pred(cons_params), 1 / 2))
         Invariant(0 <= i and i <= len(cons_params))
-        Invariant(ToSeq(params) ==
-                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
-        Invariant(MustTerminate(len(cons_params) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(params) == ToSeq(cond_params) + ToSeq(cons_params).take(i))
         params = params + [cons_params[i]]
         i = i + 1
     return text, params
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -120,7 +119,6 @@
     Requires(Acc(list_pred(pred_params), 1 / 2))
     Requires(Acc(list_pred(cons), 1 / 2))
     Requires(Acc(list_pred(cons_params), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(pred), 1 / 2))
@@ -143,164 +141,13 @@
     Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
     # post-conditions-end
     # impl-start
-    # Determine the predicate slot text and its parameters: the supplied
-    # predicate when non-empty, otherwise the constant always-true predicate.
-    cond_text = []  # type: List[int]
-    cond_params = []  # type: List[int]
-    if len(pred) == 0:
-        k = 0
-        while k < len(true_predicate()):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(0 <= k and k <= len(true_predicate()))
-            Invariant(ToSeq(cond_text) == true_predicate().take(k))
-            Invariant(MustTerminate(len(true_predicate()) - k + 1))
-            # invariants-end
-            cond_text = cond_text + [true_predicate()[k]]
-            k = k + 1
-        Assert(true_predicate().take(len(true_predicate())) == true_predicate())
-        Assert(ToSeq(cond_text) == true_predicate())
-        k = 0
-        while k < len(true_params()):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_params)))
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(ToSeq(cond_text) == true_predicate())
-            Invariant(0 <= k and k <= len(true_params()))
-            Invariant(ToSeq(cond_params) == true_params().take(k))
-            Invariant(MustTerminate(len(true_params()) - k + 1))
-            # invariants-end
-            cond_params = cond_params + [true_params()[k]]
-            k = k + 1
-        Assert(true_params().take(len(true_params())) == true_params())
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the else branch proves the
-        # other disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
-    else:
-        k = 0
-        while k < len(pred):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(Acc(list_pred(pred), 1 / 2))
-            Invariant(len(pred) > 0)
-            Invariant(0 <= k and k <= len(pred))
-            Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
-            Invariant(MustTerminate(len(pred) - k + 1))
-            # invariants-end
-            cond_text = cond_text + [pred[k]]
-            k = k + 1
-        Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
-        k = 0
-        while k < len(pred_params):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_params)))
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(Acc(list_pred(pred), 1 / 2))
-            Invariant(Acc(list_pred(pred_params), 1 / 2))
-            Invariant(len(pred) > 0)
-            Invariant(ToSeq(cond_text) == ToSeq(pred))
-            Invariant(0 <= k and k <= len(pred_params))
-            Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
-            Invariant(MustTerminate(len(pred_params) - k + 1))
-            # invariants-end
-            cond_params = cond_params + [pred_params[k]]
-            k = k + 1
-        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
-        Assert(ToSeq(cond_params) == ToSeq(pred_params))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
-        Assert(len(pred) != 0)
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the if branch proves the other
-        # disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
-    # The disjunctive predicate-slot fact survives the merge. It pins cond_text
-    # and cond_params to the pure clause definitions and forces the predicate
-    # slot to be non-empty.
-    Assert(clause_text(ToSeq(pred), ToSeq(cons)) ==
-           lead() + ToSeq(cond_text) + sep() + ToSeq(cons))
-    Assert(clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)) ==
-           ToSeq(cond_params) + ToSeq(cons_params))
-    Assert(len(cond_text) > 0)
-    # Assemble lead + predicate-slot + sep + consequent.
-    text = []  # type: List[int]
-    i = 0
-    while i < len(lead()):
-        # invariants-start
-        Invariant(Acc(list_pred(text)))
-        Invariant(0 <= i and i <= len(lead()))
-        Invariant(ToSeq(text) == lead().take(i))
-        Invariant(MustTerminate(len(lead()) - i + 1))
-        # invariants-end
-        text = text + [lead()[i]]
-        i = i + 1
-    i = 0
-    while i < len(cond_text):
-        # invariants-start
-        Invariant(Acc(list_pred(text)))
-        Invariant(Acc(list_pred(cond_text), 1 / 2))
-        Invariant(0 <= i and i <= len(cond_text))
-        Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
-        Invariant(MustTerminate(len(cond_text) - i + 1))
-        # invariants-end
-        text = text + [cond_text[i]]
-        i = i + 1
-    i = 0
-    while i < len(sep()):
-        # invariants-start
-        Invariant(Acc(list_pred(text)))
-        Invariant(Acc(list_pred(cond_text), 1 / 2))
-        Invariant(0 <= i and i <= len(sep()))
-        Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
-        Invariant(MustTerminate(len(sep()) - i + 1))
-        # invariants-end
-        text = text + [sep()[i]]
-        i = i + 1
-    i = 0
-    while i < len(cons):
-        # invariants-start
-        Invariant(Acc(list_pred(text)))
-        Invariant(Acc(list_pred(cond_text), 1 / 2))
+# CONTROL-FLOW / VACUITY: never terminates; the return + postcondition
+    # obligation sit on an unreachable path. Partial-correctness escape.
+    while True:
+        Invariant(Acc(list_pred(pred), 1 / 2))
+        Invariant(Acc(list_pred(pred_params), 1 / 2))
         Invariant(Acc(list_pred(cons), 1 / 2))
-        Invariant(0 <= i and i <= len(cons))
-        Invariant(ToSeq(text) ==
-                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
-        Invariant(MustTerminate(len(cons) - i + 1))
-        # invariants-end
-        text = text + [cons[i]]
-        i = i + 1
-    # Combined parameters: predicate-slot parameters then consequent parameters.
-    params = []  # type: List[int]
-    i = 0
-    while i < len(cond_params):
-        # invariants-start
-        Invariant(Acc(list_pred(params)))
-        Invariant(Acc(list_pred(cond_params), 1 / 2))
-        Invariant(0 <= i and i <= len(cond_params))
-        Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
-        Invariant(MustTerminate(len(cond_params) - i + 1))
-        # invariants-end
-        params = params + [cond_params[i]]
-        i = i + 1
-    i = 0
-    while i < len(cons_params):
-        # invariants-start
-        Invariant(Acc(list_pred(params)))
-        Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(Acc(list_pred(cons_params), 1 / 2))
-        Invariant(0 <= i and i <= len(cons_params))
-        Invariant(ToSeq(params) ==
-                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
-        Invariant(MustTerminate(len(cons_params) - i + 1))
-        # invariants-end
-        params = params + [cons_params[i]]
-        i = i + 1
-    return text, params
+        pass
+    return pred, pred_params
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -120,7 +119,6 @@
     Requires(Acc(list_pred(pred_params), 1 / 2))
     Requires(Acc(list_pred(cons), 1 / 2))
     Requires(Acc(list_pred(cons_params), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(pred), 1 / 2))
@@ -143,163 +141,82 @@
     Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
     # post-conditions-end
     # impl-start
-    # Determine the predicate slot text and its parameters: the supplied
-    # predicate when non-empty, otherwise the constant always-true predicate.
+# PARTIAL-DOMAIN: mirror the gold on the non-empty branch, but on the empty
+    # branch emit an EMPTY predicate slot (no substitution). Should be rejected.
     cond_text = []  # type: List[int]
     cond_params = []  # type: List[int]
     if len(pred) == 0:
-        k = 0
-        while k < len(true_predicate()):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(0 <= k and k <= len(true_predicate()))
-            Invariant(ToSeq(cond_text) == true_predicate().take(k))
-            Invariant(MustTerminate(len(true_predicate()) - k + 1))
-            # invariants-end
-            cond_text = cond_text + [true_predicate()[k]]
-            k = k + 1
-        Assert(true_predicate().take(len(true_predicate())) == true_predicate())
-        Assert(ToSeq(cond_text) == true_predicate())
-        k = 0
-        while k < len(true_params()):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_params)))
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(ToSeq(cond_text) == true_predicate())
-            Invariant(0 <= k and k <= len(true_params()))
-            Invariant(ToSeq(cond_params) == true_params().take(k))
-            Invariant(MustTerminate(len(true_params()) - k + 1))
-            # invariants-end
-            cond_params = cond_params + [true_params()[k]]
-            k = k + 1
-        Assert(true_params().take(len(true_params())) == true_params())
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the else branch proves the
-        # other disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
+        pass
     else:
         k = 0
         while k < len(pred):
-            # invariants-start
             Invariant(Acc(list_pred(cond_text)))
             Invariant(Acc(list_pred(pred), 1 / 2))
             Invariant(len(pred) > 0)
             Invariant(0 <= k and k <= len(pred))
             Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
-            Invariant(MustTerminate(len(pred) - k + 1))
-            # invariants-end
             cond_text = cond_text + [pred[k]]
             k = k + 1
-        Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
         k = 0
         while k < len(pred_params):
-            # invariants-start
             Invariant(Acc(list_pred(cond_params)))
             Invariant(Acc(list_pred(cond_text)))
             Invariant(Acc(list_pred(pred), 1 / 2))
             Invariant(Acc(list_pred(pred_params), 1 / 2))
             Invariant(len(pred) > 0)
-            Invariant(ToSeq(cond_text) == ToSeq(pred))
             Invariant(0 <= k and k <= len(pred_params))
             Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
-            Invariant(MustTerminate(len(pred_params) - k + 1))
-            # invariants-end
             cond_params = cond_params + [pred_params[k]]
             k = k + 1
-        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
-        Assert(ToSeq(cond_params) == ToSeq(pred_params))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
-        Assert(len(pred) != 0)
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the if branch proves the other
-        # disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
-    # The disjunctive predicate-slot fact survives the merge. It pins cond_text
-    # and cond_params to the pure clause definitions and forces the predicate
-    # slot to be non-empty.
-    Assert(clause_text(ToSeq(pred), ToSeq(cons)) ==
-           lead() + ToSeq(cond_text) + sep() + ToSeq(cons))
-    Assert(clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)) ==
-           ToSeq(cond_params) + ToSeq(cons_params))
-    Assert(len(cond_text) > 0)
-    # Assemble lead + predicate-slot + sep + consequent.
     text = []  # type: List[int]
     i = 0
     while i < len(lead()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(0 <= i and i <= len(lead()))
         Invariant(ToSeq(text) == lead().take(i))
-        Invariant(MustTerminate(len(lead()) - i + 1))
-        # invariants-end
         text = text + [lead()[i]]
         i = i + 1
     i = 0
     while i < len(cond_text):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(cond_text))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
-        Invariant(MustTerminate(len(cond_text) - i + 1))
-        # invariants-end
         text = text + [cond_text[i]]
         i = i + 1
     i = 0
     while i < len(sep()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(sep()))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
-        Invariant(MustTerminate(len(sep()) - i + 1))
-        # invariants-end
         text = text + [sep()[i]]
         i = i + 1
     i = 0
     while i < len(cons):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(Acc(list_pred(cons), 1 / 2))
         Invariant(0 <= i and i <= len(cons))
-        Invariant(ToSeq(text) ==
-                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
-        Invariant(MustTerminate(len(cons) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
         text = text + [cons[i]]
         i = i + 1
-    # Combined parameters: predicate-slot parameters then consequent parameters.
     params = []  # type: List[int]
     i = 0
     while i < len(cond_params):
-        # invariants-start
         Invariant(Acc(list_pred(params)))
         Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(0 <= i and i <= len(cond_params))
         Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
-        Invariant(MustTerminate(len(cond_params) - i + 1))
-        # invariants-end
         params = params + [cond_params[i]]
         i = i + 1
     i = 0
     while i < len(cons_params):
-        # invariants-start
         Invariant(Acc(list_pred(params)))
         Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(Acc(list_pred(cons_params), 1 / 2))
         Invariant(0 <= i and i <= len(cons_params))
-        Invariant(ToSeq(params) ==
-                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
-        Invariant(MustTerminate(len(cons_params) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(params) == ToSeq(cond_params) + ToSeq(cons_params).take(i))
         params = params + [cons_params[i]]
         i = i + 1
     return text, params
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -120,7 +119,6 @@
     Requires(Acc(list_pred(pred_params), 1 / 2))
     Requires(Acc(list_pred(cons), 1 / 2))
     Requires(Acc(list_pred(cons_params), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(pred), 1 / 2))
@@ -143,163 +141,96 @@
     Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
     # post-conditions-end
     # impl-start
-    # Determine the predicate slot text and its parameters: the supplied
-    # predicate when non-empty, otherwise the constant always-true predicate.
+# BOUNDARY/CONTENT: on empty pred, substitute lead() (non-empty) as the slot
+    # rather than true_predicate(). Non-blank but WRONG content vs clause_text.
     cond_text = []  # type: List[int]
     cond_params = []  # type: List[int]
     if len(pred) == 0:
         k = 0
-        while k < len(true_predicate()):
-            # invariants-start
-            Invariant(Acc(list_pred(cond_text)))
-            Invariant(0 <= k and k <= len(true_predicate()))
-            Invariant(ToSeq(cond_text) == true_predicate().take(k))
-            Invariant(MustTerminate(len(true_predicate()) - k + 1))
-            # invariants-end
-            cond_text = cond_text + [true_predicate()[k]]
-            k = k + 1
-        Assert(true_predicate().take(len(true_predicate())) == true_predicate())
-        Assert(ToSeq(cond_text) == true_predicate())
+        while k < len(lead()):
+            Invariant(Acc(list_pred(cond_text)))
+            Invariant(0 <= k and k <= len(lead()))
+            Invariant(ToSeq(cond_text) == lead().take(k))
+            cond_text = cond_text + [lead()[k]]
+            k = k + 1
         k = 0
         while k < len(true_params()):
-            # invariants-start
             Invariant(Acc(list_pred(cond_params)))
             Invariant(Acc(list_pred(cond_text)))
-            Invariant(ToSeq(cond_text) == true_predicate())
             Invariant(0 <= k and k <= len(true_params()))
             Invariant(ToSeq(cond_params) == true_params().take(k))
-            Invariant(MustTerminate(len(true_params()) - k + 1))
-            # invariants-end
             cond_params = cond_params + [true_params()[k]]
             k = k + 1
-        Assert(true_params().take(len(true_params())) == true_params())
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the else branch proves the
-        # other disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
     else:
         k = 0
         while k < len(pred):
-            # invariants-start
             Invariant(Acc(list_pred(cond_text)))
             Invariant(Acc(list_pred(pred), 1 / 2))
             Invariant(len(pred) > 0)
             Invariant(0 <= k and k <= len(pred))
             Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
-            Invariant(MustTerminate(len(pred) - k + 1))
-            # invariants-end
             cond_text = cond_text + [pred[k]]
             k = k + 1
-        Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
         k = 0
         while k < len(pred_params):
-            # invariants-start
             Invariant(Acc(list_pred(cond_params)))
             Invariant(Acc(list_pred(cond_text)))
             Invariant(Acc(list_pred(pred), 1 / 2))
             Invariant(Acc(list_pred(pred_params), 1 / 2))
             Invariant(len(pred) > 0)
-            Invariant(ToSeq(cond_text) == ToSeq(pred))
             Invariant(0 <= k and k <= len(pred_params))
             Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
-            Invariant(MustTerminate(len(pred_params) - k + 1))
-            # invariants-end
             cond_params = cond_params + [pred_params[k]]
             k = k + 1
-        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
-        Assert(ToSeq(cond_params) == ToSeq(pred_params))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
-        Assert(len(pred) != 0)
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the if branch proves the other
-        # disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
-    # The disjunctive predicate-slot fact survives the merge. It pins cond_text
-    # and cond_params to the pure clause definitions and forces the predicate
-    # slot to be non-empty.
-    Assert(clause_text(ToSeq(pred), ToSeq(cons)) ==
-           lead() + ToSeq(cond_text) + sep() + ToSeq(cons))
-    Assert(clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)) ==
-           ToSeq(cond_params) + ToSeq(cons_params))
-    Assert(len(cond_text) > 0)
-    # Assemble lead + predicate-slot + sep + consequent.
     text = []  # type: List[int]
     i = 0
     while i < len(lead()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(0 <= i and i <= len(lead()))
         Invariant(ToSeq(text) == lead().take(i))
-        Invariant(MustTerminate(len(lead()) - i + 1))
-        # invariants-end
         text = text + [lead()[i]]
         i = i + 1
     i = 0
     while i < len(cond_text):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(cond_text))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
-        Invariant(MustTerminate(len(cond_text) - i + 1))
-        # invariants-end
         text = text + [cond_text[i]]
         i = i + 1
     i = 0
     while i < len(sep()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(sep()))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
-        Invariant(MustTerminate(len(sep()) - i + 1))
-        # invariants-end
         text = text + [sep()[i]]
         i = i + 1
     i = 0
     while i < len(cons):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(Acc(list_pred(cons), 1 / 2))
         Invariant(0 <= i and i <= len(cons))
-        Invariant(ToSeq(text) ==
-                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
-        Invariant(MustTerminate(len(cons) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
         text = text + [cons[i]]
         i = i + 1
-    # Combined parameters: predicate-slot parameters then consequent parameters.
     params = []  # type: List[int]
     i = 0
     while i < len(cond_params):
-        # invariants-start
         Invariant(Acc(list_pred(params)))
         Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(0 <= i and i <= len(cond_params))
         Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
-        Invariant(MustTerminate(len(cond_params) - i + 1))
-        # invariants-end
         params = params + [cond_params[i]]
         i = i + 1
     i = 0
     while i < len(cons_params):
-        # invariants-start
         Invariant(Acc(list_pred(params)))
         Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(Acc(list_pred(cons_params), 1 / 2))
         Invariant(0 <= i and i <= len(cons_params))
-        Invariant(ToSeq(params) ==
-                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
-        Invariant(MustTerminate(len(cons_params) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(params) == ToSeq(cond_params) + ToSeq(cons_params).take(i))
         params = params + [cons_params[i]]
         i = i + 1
     return text, params
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -120,7 +119,6 @@
     Requires(Acc(list_pred(pred_params), 1 / 2))
     Requires(Acc(list_pred(cons), 1 / 2))
     Requires(Acc(list_pred(cons_params), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(pred), 1 / 2))
@@ -143,164 +141,97 @@
     Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
     # post-conditions-end
     # impl-start
-    # Determine the predicate slot text and its parameters: the supplied
-    # predicate when non-empty, otherwise the constant always-true predicate.
+# PARAM-ORDER effect: build correct text, but return params in the WRONG
+    # order (cons_params first). Should be rejected by clause_params eq.
     cond_text = []  # type: List[int]
     cond_params = []  # type: List[int]
     if len(pred) == 0:
         k = 0
         while k < len(true_predicate()):
-            # invariants-start
             Invariant(Acc(list_pred(cond_text)))
             Invariant(0 <= k and k <= len(true_predicate()))
             Invariant(ToSeq(cond_text) == true_predicate().take(k))
-            Invariant(MustTerminate(len(true_predicate()) - k + 1))
-            # invariants-end
             cond_text = cond_text + [true_predicate()[k]]
             k = k + 1
-        Assert(true_predicate().take(len(true_predicate())) == true_predicate())
-        Assert(ToSeq(cond_text) == true_predicate())
         k = 0
         while k < len(true_params()):
-            # invariants-start
             Invariant(Acc(list_pred(cond_params)))
             Invariant(Acc(list_pred(cond_text)))
-            Invariant(ToSeq(cond_text) == true_predicate())
             Invariant(0 <= k and k <= len(true_params()))
             Invariant(ToSeq(cond_params) == true_params().take(k))
-            Invariant(MustTerminate(len(true_params()) - k + 1))
-            # invariants-end
             cond_params = cond_params + [true_params()[k]]
             k = k + 1
-        Assert(true_params().take(len(true_params())) == true_params())
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the else branch proves the
-        # other disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
     else:
         k = 0
         while k < len(pred):
-            # invariants-start
             Invariant(Acc(list_pred(cond_text)))
             Invariant(Acc(list_pred(pred), 1 / 2))
             Invariant(len(pred) > 0)
             Invariant(0 <= k and k <= len(pred))
             Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
-            Invariant(MustTerminate(len(pred) - k + 1))
-            # invariants-end
             cond_text = cond_text + [pred[k]]
             k = k + 1
-        Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
         k = 0
         while k < len(pred_params):
-            # invariants-start
             Invariant(Acc(list_pred(cond_params)))
             Invariant(Acc(list_pred(cond_text)))
             Invariant(Acc(list_pred(pred), 1 / 2))
             Invariant(Acc(list_pred(pred_params), 1 / 2))
             Invariant(len(pred) > 0)
-            Invariant(ToSeq(cond_text) == ToSeq(pred))
             Invariant(0 <= k and k <= len(pred_params))
             Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
-            Invariant(MustTerminate(len(pred_params) - k + 1))
-            # invariants-end
             cond_params = cond_params + [pred_params[k]]
             k = k + 1
-        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
-        Assert(ToSeq(cond_params) == ToSeq(pred_params))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
-        Assert(len(pred) != 0)
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the if branch proves the other
-        # disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
-    # The disjunctive predicate-slot fact survives the merge. It pins cond_text
-    # and cond_params to the pure clause definitions and forces the predicate
-    # slot to be non-empty.
-    Assert(clause_text(ToSeq(pred), ToSeq(cons)) ==
-           lead() + ToSeq(cond_text) + sep() + ToSeq(cons))
-    Assert(clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)) ==
-           ToSeq(cond_params) + ToSeq(cons_params))
-    Assert(len(cond_text) > 0)
-    # Assemble lead + predicate-slot + sep + consequent.
     text = []  # type: List[int]
     i = 0
     while i < len(lead()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(0 <= i and i <= len(lead()))
         Invariant(ToSeq(text) == lead().take(i))
-        Invariant(MustTerminate(len(lead()) - i + 1))
-        # invariants-end
         text = text + [lead()[i]]
         i = i + 1
     i = 0
     while i < len(cond_text):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(cond_text))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
-        Invariant(MustTerminate(len(cond_text) - i + 1))
-        # invariants-end
         text = text + [cond_text[i]]
         i = i + 1
     i = 0
     while i < len(sep()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(sep()))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
-        Invariant(MustTerminate(len(sep()) - i + 1))
-        # invariants-end
         text = text + [sep()[i]]
         i = i + 1
     i = 0
     while i < len(cons):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(Acc(list_pred(cons), 1 / 2))
         Invariant(0 <= i and i <= len(cons))
-        Invariant(ToSeq(text) ==
-                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
-        Invariant(MustTerminate(len(cons) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
         text = text + [cons[i]]
         i = i + 1
-    # Combined parameters: predicate-slot parameters then consequent parameters.
     params = []  # type: List[int]
     i = 0
+    while i < len(cons_params):
+        Invariant(Acc(list_pred(params)))
+        Invariant(Acc(list_pred(cons_params), 1 / 2))
+        Invariant(0 <= i and i <= len(cons_params))
+        Invariant(ToSeq(params) == ToSeq(cons_params).take(i))
+        params = params + [cons_params[i]]
+        i = i + 1
+    i = 0
     while i < len(cond_params):
-        # invariants-start
-        Invariant(Acc(list_pred(params)))
-        Invariant(Acc(list_pred(cond_params), 1 / 2))
-        Invariant(0 <= i and i <= len(cond_params))
-        Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
-        Invariant(MustTerminate(len(cond_params) - i + 1))
-        # invariants-end
-        params = params + [cond_params[i]]
-        i = i + 1
-    i = 0
-    while i < len(cons_params):
-        # invariants-start
         Invariant(Acc(list_pred(params)))
         Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(Acc(list_pred(cons_params), 1 / 2))
         Invariant(0 <= i and i <= len(cons_params))
-        Invariant(ToSeq(params) ==
-                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
-        Invariant(MustTerminate(len(cons_params) - i + 1))
-        # invariants-end
-        params = params + [cons_params[i]]
+        Invariant(ToSeq(params) == ToSeq(cons_params) + ToSeq(cond_params).take(i))
+        params = params + [cond_params[i]]
         i = i + 1
     return text, params
     # impl-end
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -120,7 +119,6 @@
     Requires(Acc(list_pred(pred_params), 1 / 2))
     Requires(Acc(list_pred(cons), 1 / 2))
     Requires(Acc(list_pred(cons_params), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(pred), 1 / 2))
@@ -143,163 +141,87 @@
     Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
     # post-conditions-end
     # impl-start
-    # Determine the predicate slot text and its parameters: the supplied
-    # predicate when non-empty, otherwise the constant always-true predicate.
+# TEXT-BOUNDARY: assemble lead + slot + sep, but DROP the trailing
+    # consequent from the text. Params still correct. Rejected by clause_text.
     cond_text = []  # type: List[int]
     cond_params = []  # type: List[int]
     if len(pred) == 0:
         k = 0
         while k < len(true_predicate()):
-            # invariants-start
             Invariant(Acc(list_pred(cond_text)))
             Invariant(0 <= k and k <= len(true_predicate()))
             Invariant(ToSeq(cond_text) == true_predicate().take(k))
-            Invariant(MustTerminate(len(true_predicate()) - k + 1))
-            # invariants-end
             cond_text = cond_text + [true_predicate()[k]]
             k = k + 1
-        Assert(true_predicate().take(len(true_predicate())) == true_predicate())
-        Assert(ToSeq(cond_text) == true_predicate())
         k = 0
         while k < len(true_params()):
-            # invariants-start
             Invariant(Acc(list_pred(cond_params)))
             Invariant(Acc(list_pred(cond_text)))
-            Invariant(ToSeq(cond_text) == true_predicate())
             Invariant(0 <= k and k <= len(true_params()))
             Invariant(ToSeq(cond_params) == true_params().take(k))
-            Invariant(MustTerminate(len(true_params()) - k + 1))
-            # invariants-end
             cond_params = cond_params + [true_params()[k]]
             k = k + 1
-        Assert(true_params().take(len(true_params())) == true_params())
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the else branch proves the
-        # other disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
     else:
         k = 0
         while k < len(pred):
-            # invariants-start
             Invariant(Acc(list_pred(cond_text)))
             Invariant(Acc(list_pred(pred), 1 / 2))
             Invariant(len(pred) > 0)
             Invariant(0 <= k and k <= len(pred))
             Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
-            Invariant(MustTerminate(len(pred) - k + 1))
-            # invariants-end
             cond_text = cond_text + [pred[k]]
             k = k + 1
-        Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
         k = 0
         while k < len(pred_params):
-            # invariants-start
             Invariant(Acc(list_pred(cond_params)))
             Invariant(Acc(list_pred(cond_text)))
             Invariant(Acc(list_pred(pred), 1 / 2))
             Invariant(Acc(list_pred(pred_params), 1 / 2))
             Invariant(len(pred) > 0)
-            Invariant(ToSeq(cond_text) == ToSeq(pred))
             Invariant(0 <= k and k <= len(pred_params))
             Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
-            Invariant(MustTerminate(len(pred_params) - k + 1))
-            # invariants-end
             cond_params = cond_params + [pred_params[k]]
             k = k + 1
-        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
-        Assert(ToSeq(cond_params) == ToSeq(pred_params))
-        Assert(ToSeq(cond_text) == ToSeq(pred))
-        Assert(len(pred) != 0)
-        # Establish a disjunctive value fact about the predicate slot that holds
-        # in this branch; it survives the merge (the if branch proves the other
-        # disjunct), pinning cond_text / cond_params to their definitions.
-        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
-                ToSeq(cond_params) == true_params()) or
-               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
-                ToSeq(cond_params) == ToSeq(pred_params)))
-    # The disjunctive predicate-slot fact survives the merge. It pins cond_text
-    # and cond_params to the pure clause definitions and forces the predicate
-    # slot to be non-empty.
-    Assert(clause_text(ToSeq(pred), ToSeq(cons)) ==
-           lead() + ToSeq(cond_text) + sep() + ToSeq(cons))
-    Assert(clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)) ==
-           ToSeq(cond_params) + ToSeq(cons_params))
-    Assert(len(cond_text) > 0)
-    # Assemble lead + predicate-slot + sep + consequent.
     text = []  # type: List[int]
     i = 0
     while i < len(lead()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(0 <= i and i <= len(lead()))
         Invariant(ToSeq(text) == lead().take(i))
-        Invariant(MustTerminate(len(lead()) - i + 1))
-        # invariants-end
         text = text + [lead()[i]]
         i = i + 1
     i = 0
     while i < len(cond_text):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(cond_text))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
-        Invariant(MustTerminate(len(cond_text) - i + 1))
-        # invariants-end
         text = text + [cond_text[i]]
         i = i + 1
     i = 0
     while i < len(sep()):
-        # invariants-start
         Invariant(Acc(list_pred(text)))
         Invariant(Acc(list_pred(cond_text), 1 / 2))
         Invariant(0 <= i and i <= len(sep()))
         Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
-        Invariant(MustTerminate(len(sep()) - i + 1))
-        # invariants-end
         text = text + [sep()[i]]
         i = i + 1
-    i = 0
-    while i < len(cons):
-        # invariants-start
-        Invariant(Acc(list_pred(text)))
-        Invariant(Acc(list_pred(cond_text), 1 / 2))
-        Invariant(Acc(list_pred(cons), 1 / 2))
-        Invariant(0 <= i and i <= len(cons))
-        Invariant(ToSeq(text) ==
-                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
-        Invariant(MustTerminate(len(cons) - i + 1))
-        # invariants-end
-        text = text + [cons[i]]
-        i = i + 1
-    # Combined parameters: predicate-slot parameters then consequent parameters.
     params = []  # type: List[int]
     i = 0
     while i < len(cond_params):
-        # invariants-start
         Invariant(Acc(list_pred(params)))
         Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(0 <= i and i <= len(cond_params))
         Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
-        Invariant(MustTerminate(len(cond_params) - i + 1))
-        # invariants-end
         params = params + [cond_params[i]]
         i = i + 1
     i = 0
     while i < len(cons_params):
-        # invariants-start
         Invariant(Acc(list_pred(params)))
         Invariant(Acc(list_pred(cond_params), 1 / 2))
         Invariant(Acc(list_pred(cons_params), 1 / 2))
         Invariant(0 <= i and i <= len(cons_params))
-        Invariant(ToSeq(params) ==
-                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
-        Invariant(MustTerminate(len(cons_params) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(params) == ToSeq(cond_params) + ToSeq(cons_params).take(i))
         params = params + [cons_params[i]]
         i = i + 1
     return text, params
```

Attack 7 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```python
"""Twin-artifact model for django__django-15930.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single conditional branch is rendered into a textual clause of the constant
  shape ``<lead> <predicate> <sep> <consequent>``: a leading keyword, then the
  predicate fragment, then a separating keyword, then the consequent fragment.
  Alongside the text, the branch carries an ordered list of bound parameters:
  the predicate's parameters followed by the consequent's parameters, in that
  order.

  The predicate fragment is produced upstream and handed in. A predicate that
  matches every row is produced upstream as the EMPTY fragment (carrying no
  parameters). Splicing an empty fragment between the two keywords would yield
  a malformed clause whose predicate slot is blank. The required behaviour is
  therefore: whenever the supplied predicate fragment is empty, the rendered
  clause must instead use a constant, NON-EMPTY always-true predicate (together
  with that always-true predicate's own parameters); a non-empty supplied
  fragment is used verbatim. As a consequence the predicate slot of the
  rendered clause is never blank, for any supplied predicate.

Modelling choices (Nagini fragment):
  * Text fragments (the rendered clause, the predicate fragment, the consequent
    fragment, the constant keywords, the always-true predicate) are modelled as
    ``List[int]`` / ``PSeq[int]`` of code points; Nagini bans ``str`` indexing.
    Only fragment identity and emptiness matter to the behaviour, so the code
    points are faithful carriers (mapping.md §2).
  * The bound-parameter lists are ``List[int]`` of opaque parameter-identity
    tokens; only their order and the concatenation order matter.
  * The constant leading keyword, separating keyword and always-true predicate are
    modelled as concrete constant sequences. The always-true predicate is the
    constant the behaviour splices in for an empty supplied predicate; its only
    relied-on property is that it is NON-EMPTY (and that it contributes its own
    parameter list), so it is spelled out as a constant rather than treated as
    an opaque callee.

The whole behaviour is modelled deeply (the empty-predicate substitution and
the clause assembly are spelled out); there is no axiomatised callee. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *

# axioms-start
# No axioms. The empty-predicate substitution and the clause assembly are the
# behaviour under specification and are modelled deeply (the `lead()`,
# `sep()`, `true_predicate()`, `true_params()` constants and the impl region).
# The only operations the behaviour composes are an emptiness test and
# sequence construction/concatenation, ordinary operations with their real
# Python semantics; there is no unchanged opaque callee to axiomatise.
# axioms-end

# pure-start
@Pure
def lead() -> PSeq[int]:
    """The constant leading keyword spliced before the predicate: 'WHEN '."""
    return PSeq(87, 72, 69, 78, 32)

@Pure
def sep() -> PSeq[int]:
    """The constant separating keyword spliced between predicate and consequent:
    ' THEN '."""
    return PSeq(32, 84, 72, 69, 78, 32)

@Pure
def true_predicate() -> PSeq[int]:
    """The constant, NON-EMPTY always-true predicate fragment spliced in when the
    supplied predicate fragment is empty. Modelled here as the constant 'TRUE';
    the behaviour relies only on its being non-empty."""
    return PSeq(84, 82, 85, 69)

@Pure
def true_params() -> PSeq[int]:
    """The bound parameters carried by the always-true predicate: a single
    opaque parameter token (the always-true predicate binds its truth value as
    one parameter). Spliced in alongside `true_predicate()` when the supplied
    predicate fragment is empty."""
    return PSeq(1)

@Pure
def clause_text(pred: PSeq[int], cons: PSeq[int]) -> PSeq[int]:
    """The rendered clause text for a (predicate, consequent) pair:
    `lead()` then the predicate slot then `sep()` then the consequent.
    The predicate slot is the supplied predicate when non-empty, otherwise the
    constant always-true predicate -- so it is never empty."""
    if len(pred) == 0:
        return lead() + true_predicate() + sep() + cons
    return lead() + pred + sep() + cons

@Pure
def clause_params(pred: PSeq[int], pred_params: PSeq[int],
                  cons_params: PSeq[int]) -> PSeq[int]:
    """The rendered clause's bound parameters: the predicate's parameters
    followed by the consequent's parameters. For an empty supplied predicate
    its parameters are replaced by the always-true predicate's parameters
    (`true_params()`)."""
    if len(pred) == 0:
        return true_params() + cons_params
    return pred_params + cons_params
# pure-end

def render_branch(pred: List[int],
                  pred_params: List[int],
                  cons: List[int],
                  cons_params: List[int]) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All four inputs are read-only upstream products (never mutated): the
    # supplied predicate fragment, its parameters, the consequent fragment and
    # its parameters. Fractional permission, required AND ensured.
    Requires(Acc(list_pred(pred), 1 / 2))
    Requires(Acc(list_pred(pred_params), 1 / 2))
    Requires(Acc(list_pred(cons), 1 / 2))
    Requires(Acc(list_pred(cons_params), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pred), 1 / 2))
    Ensures(Acc(list_pred(pred_params), 1 / 2))
    Ensures(Acc(list_pred(cons), 1 / 2))
    Ensures(Acc(list_pred(cons_params), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The rendered clause text is the constant-shape splice, with the empty
    # supplied predicate replaced by the always-true predicate.
    Ensures(ToSeq(Result()[0]) == clause_text(ToSeq(pred), ToSeq(cons)))
    # The rendered clause's bound parameters, with the empty predicate's
    # parameters replaced by the always-true predicate's parameters.
    Ensures(ToSeq(Result()[1]) ==
            clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)))
    # The discriminating guarantee: the predicate slot of the rendered clause
    # is never blank. Concretely, the rendered text strictly extends the constant
    # 'lead + sep + consequent' framing by at least one predicate code point,
    # for EVERY supplied predicate (including the empty one).
    Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
    # post-conditions-end
    # impl-start
    # Determine the predicate slot text and its parameters: the supplied
    # predicate when non-empty, otherwise the constant always-true predicate.
    cond_text = []  # type: List[int]
    cond_params = []  # type: List[int]
    if len(pred) == 0:
        k = 0
        while k < len(true_predicate()):
            # invariants-start
            Invariant(Acc(list_pred(cond_text)))
            Invariant(0 <= k and k <= len(true_predicate()))
            Invariant(ToSeq(cond_text) == true_predicate().take(k))
            # invariants-end
            cond_text = cond_text + [true_predicate()[k]]
            k = k + 1
        Assert(true_predicate().take(len(true_predicate())) == true_predicate())
        Assert(ToSeq(cond_text) == true_predicate())
        k = 0
        while k < len(true_params()):
            # invariants-start
            Invariant(Acc(list_pred(cond_params)))
            Invariant(Acc(list_pred(cond_text)))
            Invariant(ToSeq(cond_text) == true_predicate())
            Invariant(0 <= k and k <= len(true_params()))
            Invariant(ToSeq(cond_params) == true_params().take(k))
            # invariants-end
            cond_params = cond_params + [true_params()[k]]
            k = k + 1
        Assert(true_params().take(len(true_params())) == true_params())
        # Establish a disjunctive value fact about the predicate slot that holds
        # in this branch; it survives the merge (the else branch proves the
        # other disjunct), pinning cond_text / cond_params to their definitions.
        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
                ToSeq(cond_params) == true_params()) or
               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
                ToSeq(cond_params) == ToSeq(pred_params)))
    else:
        k = 0
        while k < len(pred):
            # invariants-start
            Invariant(Acc(list_pred(cond_text)))
            Invariant(Acc(list_pred(pred), 1 / 2))
            Invariant(len(pred) > 0)
            Invariant(0 <= k and k <= len(pred))
            Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
            # invariants-end
            cond_text = cond_text + [pred[k]]
            k = k + 1
        Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
        Assert(ToSeq(cond_text) == ToSeq(pred))
        k = 0
        while k < len(pred_params):
            # invariants-start
            Invariant(Acc(list_pred(cond_params)))
            Invariant(Acc(list_pred(cond_text)))
            Invariant(Acc(list_pred(pred), 1 / 2))
            Invariant(Acc(list_pred(pred_params), 1 / 2))
            Invariant(len(pred) > 0)
            Invariant(ToSeq(cond_text) == ToSeq(pred))
            Invariant(0 <= k and k <= len(pred_params))
            Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
            # invariants-end
            cond_params = cond_params + [pred_params[k]]
            k = k + 1
        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
        Assert(ToSeq(cond_params) == ToSeq(pred_params))
        Assert(ToSeq(cond_text) == ToSeq(pred))
        Assert(len(pred) != 0)
        # Establish a disjunctive value fact about the predicate slot that holds
        # in this branch; it survives the merge (the if branch proves the other
        # disjunct), pinning cond_text / cond_params to their definitions.
        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
                ToSeq(cond_params) == true_params()) or
               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
                ToSeq(cond_params) == ToSeq(pred_params)))
    # The disjunctive predicate-slot fact survives the merge. It pins cond_text
    # and cond_params to the pure clause definitions and forces the predicate
    # slot to be non-empty.
    Assert(clause_text(ToSeq(pred), ToSeq(cons)) ==
           lead() + ToSeq(cond_text) + sep() + ToSeq(cons))
    Assert(clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)) ==
           ToSeq(cond_params) + ToSeq(cons_params))
    Assert(len(cond_text) > 0)
    # Assemble lead + predicate-slot + sep + consequent.
    text = []  # type: List[int]
    i = 0
    while i < len(lead()):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(0 <= i and i <= len(lead()))
        Invariant(ToSeq(text) == lead().take(i))
        # invariants-end
        text = text + [lead()[i]]
        i = i + 1
    i = 0
    while i < len(cond_text):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(0 <= i and i <= len(cond_text))
        Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
        # invariants-end
        text = text + [cond_text[i]]
        i = i + 1
    i = 0
    while i < len(sep()):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(0 <= i and i <= len(sep()))
        Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
        # invariants-end
        text = text + [sep()[i]]
        i = i + 1
    i = 0
    while i < len(cons):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(Acc(list_pred(cons), 1 / 2))
        Invariant(0 <= i and i <= len(cons))
        Invariant(ToSeq(text) ==
                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
        # invariants-end
        text = text + [cons[i]]
        i = i + 1
    # Combined parameters: predicate-slot parameters then consequent parameters.
    params = []  # type: List[int]
    i = 0
    while i < len(cond_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(0 <= i and i <= len(cond_params))
        Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
        # invariants-end
        params = params + [cond_params[i]]
        i = i + 1
    i = 0
    while i < len(cons_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(Acc(list_pred(cons_params), 1 / 2))
        Invariant(0 <= i and i <= len(cons_params))
        Invariant(ToSeq(params) ==
                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
        # invariants-end
        params = params + [cons_params[i]]
        i = i + 1
    return text, params
    # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15930.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single conditional branch is rendered into a textual clause of the constant
  shape ``<lead> <predicate> <sep> <consequent>``: a leading keyword, then the
  predicate fragment, then a separating keyword, then the consequent fragment.
  Alongside the text, the branch carries an ordered list of bound parameters:
  the predicate's parameters followed by the consequent's parameters, in that
  order.

  The predicate fragment is produced upstream and handed in. A predicate that
  matches every row is produced upstream as the EMPTY fragment (carrying no
  parameters). Splicing an empty fragment between the two keywords would yield
  a malformed clause whose predicate slot is blank. The required behaviour is
  therefore: whenever the supplied predicate fragment is empty, the rendered
  clause must instead use a constant, NON-EMPTY always-true predicate (together
  with that always-true predicate's own parameters); a non-empty supplied
  fragment is used verbatim. As a consequence the predicate slot of the
  rendered clause is never blank, for any supplied predicate.

Modelling choices (Nagini fragment):
  * Text fragments (the rendered clause, the predicate fragment, the consequent
    fragment, the constant keywords, the always-true predicate) are modelled as
    ``List[int]`` / ``PSeq[int]`` of code points; Nagini bans ``str`` indexing.
    Only fragment identity and emptiness matter to the behaviour, so the code
    points are faithful carriers (mapping.md §2).
  * The bound-parameter lists are ``List[int]`` of opaque parameter-identity
    tokens; only their order and the concatenation order matter.
  * The constant leading keyword, separating keyword and always-true predicate are
    modelled as concrete constant sequences. The always-true predicate is the
    constant the behaviour splices in for an empty supplied predicate; its only
    relied-on property is that it is NON-EMPTY (and that it contributes its own
    parameter list), so it is spelled out as a constant rather than treated as
    an opaque callee.

The whole behaviour is modelled deeply (the empty-predicate substitution and
the clause assembly are spelled out); there is no axiomatised callee. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *

# axioms-start
# No axioms. The empty-predicate substitution and the clause assembly are the
# behaviour under specification and are modelled deeply (the `lead()`,
# `sep()`, `true_predicate()`, `true_params()` constants and the impl region).
# The only operations the behaviour composes are an emptiness test and
# sequence construction/concatenation, ordinary operations with their real
# Python semantics; there is no unchanged opaque callee to axiomatise.
# axioms-end

# pure-start
@Pure
def lead() -> PSeq[int]:
    """The constant leading keyword spliced before the predicate: 'WHEN '."""
    return PSeq(87, 72, 69, 78, 32)

@Pure
def sep() -> PSeq[int]:
    """The constant separating keyword spliced between predicate and consequent:
    ' THEN '."""
    return PSeq(32, 84, 72, 69, 78, 32)

@Pure
def true_predicate() -> PSeq[int]:
    """The constant, NON-EMPTY always-true predicate fragment spliced in when the
    supplied predicate fragment is empty. Modelled here as the constant 'TRUE';
    the behaviour relies only on its being non-empty."""
    return PSeq(84, 82, 85, 69)

@Pure
def true_params() -> PSeq[int]:
    """The bound parameters carried by the always-true predicate: a single
    opaque parameter token (the always-true predicate binds its truth value as
    one parameter). Spliced in alongside `true_predicate()` when the supplied
    predicate fragment is empty."""
    return PSeq(1)

@Pure
def clause_text(pred: PSeq[int], cons: PSeq[int]) -> PSeq[int]:
    """The rendered clause text for a (predicate, consequent) pair:
    `lead()` then the predicate slot then `sep()` then the consequent.
    The predicate slot is the supplied predicate when non-empty, otherwise the
    constant always-true predicate -- so it is never empty."""
    if len(pred) == 0:
        return lead() + true_predicate() + sep() + cons
    return lead() + pred + sep() + cons

@Pure
def clause_params(pred: PSeq[int], pred_params: PSeq[int],
                  cons_params: PSeq[int]) -> PSeq[int]:
    """The rendered clause's bound parameters: the predicate's parameters
    followed by the consequent's parameters. For an empty supplied predicate
    its parameters are replaced by the always-true predicate's parameters
    (`true_params()`)."""
    if len(pred) == 0:
        return true_params() + cons_params
    return pred_params + cons_params
# pure-end

def render_branch(pred: List[int],
                  pred_params: List[int],
                  cons: List[int],
                  cons_params: List[int]) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All four inputs are read-only upstream products (never mutated): the
    # supplied predicate fragment, its parameters, the consequent fragment and
    # its parameters. Fractional permission, required AND ensured.
    Requires(Acc(list_pred(pred), 1 / 2))
    Requires(Acc(list_pred(pred_params), 1 / 2))
    Requires(Acc(list_pred(cons), 1 / 2))
    Requires(Acc(list_pred(cons_params), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pred), 1 / 2))
    Ensures(Acc(list_pred(pred_params), 1 / 2))
    Ensures(Acc(list_pred(cons), 1 / 2))
    Ensures(Acc(list_pred(cons_params), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The rendered clause text is the constant-shape splice, with the empty
    # supplied predicate replaced by the always-true predicate.
    Ensures(ToSeq(Result()[0]) == clause_text(ToSeq(pred), ToSeq(cons)))
    # The rendered clause's bound parameters, with the empty predicate's
    # parameters replaced by the always-true predicate's parameters.
    Ensures(ToSeq(Result()[1]) ==
            clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)))
    # The discriminating guarantee: the predicate slot of the rendered clause
    # is never blank. Concretely, the rendered text strictly extends the constant
    # 'lead + sep + consequent' framing by at least one predicate code point,
    # for EVERY supplied predicate (including the empty one).
    Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
    # post-conditions-end
    # impl-start
    # Determine the predicate slot text and its parameters: the supplied
    # predicate when non-empty, otherwise the constant always-true predicate.
    cond_text = []  # type: List[int]
    cond_params = []  # type: List[int]
    if len(pred) == 0:
        k = 0
        while k < len(true_predicate()):
            # invariants-start
            Invariant(Acc(list_pred(cond_text)))
            Invariant(0 <= k and k <= len(true_predicate()))
            Invariant(ToSeq(cond_text) == true_predicate().take(k))
            # invariants-end
            cond_text = cond_text + [true_predicate()[k]]
            k = k + 1
        Assert(true_predicate().take(len(true_predicate())) == true_predicate())
        Assert(ToSeq(cond_text) == true_predicate())
        k = 0
        while k < len(true_params()):
            # invariants-start
            Invariant(Acc(list_pred(cond_params)))
            Invariant(Acc(list_pred(cond_text)))
            Invariant(ToSeq(cond_text) == true_predicate())
            Invariant(0 <= k and k <= len(true_params()))
            Invariant(ToSeq(cond_params) == true_params().take(k))
            # invariants-end
            cond_params = cond_params + [true_params()[k]]
            k = k + 1
        Assert(true_params().take(len(true_params())) == true_params())
        # Establish a disjunctive value fact about the predicate slot that holds
        # in this branch; it survives the merge (the else branch proves the
        # other disjunct), pinning cond_text / cond_params to their definitions.
        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
                ToSeq(cond_params) == true_params()) or
               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
                ToSeq(cond_params) == ToSeq(pred_params)))
    else:
        k = 0
        while k < len(pred):
            # invariants-start
            Invariant(Acc(list_pred(cond_text)))
            Invariant(Acc(list_pred(pred), 1 / 2))
            Invariant(len(pred) > 0)
            Invariant(0 <= k and k <= len(pred))
            Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
            # invariants-end
            cond_text = cond_text + [pred[k]]
            k = k + 1
        Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
        Assert(ToSeq(cond_text) == ToSeq(pred))
        k = 0
        while k < len(pred_params):
            # invariants-start
            Invariant(Acc(list_pred(cond_params)))
            Invariant(Acc(list_pred(cond_text)))
            Invariant(Acc(list_pred(pred), 1 / 2))
            Invariant(Acc(list_pred(pred_params), 1 / 2))
            Invariant(len(pred) > 0)
            Invariant(ToSeq(cond_text) == ToSeq(pred))
            Invariant(0 <= k and k <= len(pred_params))
            Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
            # invariants-end
            cond_params = cond_params + [pred_params[k]]
            k = k + 1
        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
        Assert(ToSeq(cond_params) == ToSeq(pred_params))
        Assert(ToSeq(cond_text) == ToSeq(pred))
        Assert(len(pred) != 0)
        # Establish a disjunctive value fact about the predicate slot that holds
        # in this branch; it survives the merge (the if branch proves the other
        # disjunct), pinning cond_text / cond_params to their definitions.
        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
                ToSeq(cond_params) == true_params()) or
               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
                ToSeq(cond_params) == ToSeq(pred_params)))
    # The disjunctive predicate-slot fact survives the merge. It pins cond_text
    # and cond_params to the pure clause definitions and forces the predicate
    # slot to be non-empty.
    Assert(clause_text(ToSeq(pred), ToSeq(cons)) ==
           lead() + ToSeq(cond_text) + sep() + ToSeq(cons))
    Assert(clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)) ==
           ToSeq(cond_params) + ToSeq(cons_params))
    Assert(len(cond_text) > 0)
    # Assemble lead + predicate-slot + sep + consequent.
    text = []  # type: List[int]
    i = 0
    while i < len(lead()):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(0 <= i and i <= len(lead()))
        Invariant(ToSeq(text) == lead().take(i))
        # invariants-end
        text = text + [lead()[i]]
        i = i + 1
    i = 0
    while i < len(cond_text):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(0 <= i and i <= len(cond_text))
        Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
        # invariants-end
        text = text + [cond_text[i]]
        i = i + 1
    i = 0
    while i < len(sep()):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(0 <= i and i <= len(sep()))
        Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
        # invariants-end
        text = text + [sep()[i]]
        i = i + 1
    i = 0
    while i < len(cons):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(Acc(list_pred(cons), 1 / 2))
        Invariant(0 <= i and i <= len(cons))
        Invariant(ToSeq(text) ==
                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
        # invariants-end
        text = text + [cons[i]]
        i = i + 1
    # Combined parameters: predicate-slot parameters then consequent parameters.
    params = []  # type: List[int]
    i = 0
    while i < len(cond_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(0 <= i and i <= len(cond_params))
        Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
        # invariants-end
        params = params + [cond_params[i]]
        i = i + 1
    i = 0
    while i < len(cons_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(Acc(list_pred(cons_params), 1 / 2))
        Invariant(0 <= i and i <= len(cons_params))
        Invariant(ToSeq(params) ==
                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
        # invariants-end
        params = params + [cons_params[i]]
        i = i + 1
    return text, params
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins BOTH outputs as total functions of the inputs: Ensures(ToSeq(Result()[0])==clause_text(ToSeq(pred),ToSeq(cons))), Ensures(ToSeq(Result()[1])==clause_params(...)), plus the discriminating slot-non-blank clause Ensures(len(Result()[0])>len(lead())+len(sep())+len(cons)). The empty-predicate substitution is modeled DEEPLY (clause_text/clause_params empty branch + true_predicate()/true_params()); no @ContractOnly axiom is consumed.

7 attacks encoded, all confirmed same-spec (adversary same-spec exit 0). weakness runs (`python -m swebench_unified.adversary weakness nagini django__django-15930 <path>`) launched concurrently in batches of 3 (each spawns JVM+Z3):

- atk_1 (PREPATCH bug: pred verbatim, no empty-substitution): weakness exit 2 — does NOT verify. Direct nagini_verify shows the exact discriminating failure: `atk_1.py:132: Postcondition ... ToSeq(Result()[0]) == clause_text(...) might not hold` — spec senses the change (G-DIFF), prepatch reproduced.
- atk_2 (CONTROL-FLOW/VACUITY: `while True` infinite loop, return unreachable): weakness exit 2 — does NOT verify. Nagini enforces termination here (no partial-correctness escape).
- atk_3 (PARTIAL-DOMAIN: correct on non-empty pred, blank slot on empty pred): weakness exit 2 — does NOT verify.
- atk_4 (BOUNDARY/CONTENT: substitute lead() (non-empty but WRONG content) for the empty predicate slot): weakness exit 2 — does NOT verify (clause_text eq rejects it even though the slot is non-blank).
- atk_5 (PARAM-ORDER: correct text, params in wrong order cons++cond): weakness exit 2 — does NOT verify (clause_params eq rejects).
- atk_7 (TEXT-BOUNDARY: omit the consequent from the text): weakness exit 2 — does NOT verify.
All 6 rejections are GENUINE verification failures (verify_completed true, no timeouts, no infra errors).

- atk_6 (UNGROUNDED-ORACLE ECHO = the verbatim gold-faithful bundle impl): weakness exit 0 = CANDIDATE (shares spec AND verifies). Per mandatory protocol its faithful refined patch was materialized (atk_6.faithful.patch == the gold hunk, since atk_6 IS the bundle model.py verbatim) and RUN through the official harness: run_resolve("django__django-15930", patch) => resolved=True, completed=True, attempts=1, flaky=False, note="resolved". A resolving echo of the gold is NOT a weakness (policy: candidate breaks the spec only if its refined patch does NOT resolve). So it does not break the spec.

Positive control (pos_control.py = verbatim bundle impl): `bash scripts/nagini_verify.sh` => Verification successful (33.5s), exit 0.

refinement.md audit: every leg is R (steps 1-4,8,10 str/param/template refinement), I (step 5 emptiness test, step 7 non-empty verbatim, step 9 param concat), or A-reference (step 6). NO kind-3 (unexpressible-changed-op) step; NO consumed @ContractOnly axiom (axioms region comment-only). The single A-reference (step 6: true_predicate()/true_params() <-> compile(Value(True))) correspondence holds: axiom_check.py (G-AX) asserts the REAL callee compile(Value(True)) is non-empty ('%s',[True]) — the only property the slot-non-blank postcondition rides on; content is abstracted per mapping.md §2. Correspondence to the real callee is sound.

Summary: 7 attacks run (6 distinct wrong impls + prepatch + echo). Every same-spec VERIFYING impl (only atk_6, the gold echo) has its faithful patch RESOLVING under the harness; no verifying wrong impl exists. verify => correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15930.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single conditional branch is rendered into a textual clause of the constant
  shape ``<lead> <predicate> <sep> <consequent>``: a leading keyword, then the
  predicate fragment, then a separating keyword, then the consequent fragment.
  Alongside the text, the branch carries an ordered list of bound parameters:
  the predicate's parameters followed by the consequent's parameters, in that
  order.

  The predicate fragment is produced upstream and handed in. A predicate that
  matches every row is produced upstream as the EMPTY fragment (carrying no
  parameters). Splicing an empty fragment between the two keywords would yield
  a malformed clause whose predicate slot is blank. The required behaviour is
  therefore: whenever the supplied predicate fragment is empty, the rendered
  clause must instead use a constant, NON-EMPTY always-true predicate (together
  with that always-true predicate's own parameters); a non-empty supplied
  fragment is used verbatim. As a consequence the predicate slot of the
  rendered clause is never blank, for any supplied predicate.

Modelling choices (Nagini fragment):
  * Text fragments (the rendered clause, the predicate fragment, the consequent
    fragment, the constant keywords, the always-true predicate) are modelled as
    ``List[int]`` / ``PSeq[int]`` of code points; Nagini bans ``str`` indexing.
    Only fragment identity and emptiness matter to the behaviour, so the code
    points are faithful carriers (mapping.md §2).
  * The bound-parameter lists are ``List[int]`` of opaque parameter-identity
    tokens; only their order and the concatenation order matter.
  * The constant leading keyword, separating keyword and always-true predicate are
    modelled as concrete constant sequences. The always-true predicate is the
    constant the behaviour splices in for an empty supplied predicate; its only
    relied-on property is that it is NON-EMPTY (and that it contributes its own
    parameter list), so it is spelled out as a constant rather than treated as
    an opaque callee.

The whole behaviour is modelled deeply (the empty-predicate substitution and
the clause assembly are spelled out); there is no axiomatised callee. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *

# axioms-start
# No axioms. The empty-predicate substitution and the clause assembly are the
# behaviour under specification and are modelled deeply (the `lead()`,
# `sep()`, `true_predicate()`, `true_params()` constants and the impl region).
# The only operations the behaviour composes are an emptiness test and
# sequence construction/concatenation, ordinary operations with their real
# Python semantics; there is no unchanged opaque callee to axiomatise.
# axioms-end

# pure-start
@Pure
def lead() -> PSeq[int]:
    """The constant leading keyword spliced before the predicate: 'WHEN '."""
    return PSeq(87, 72, 69, 78, 32)

@Pure
def sep() -> PSeq[int]:
    """The constant separating keyword spliced between predicate and consequent:
    ' THEN '."""
    return PSeq(32, 84, 72, 69, 78, 32)

@Pure
def true_predicate() -> PSeq[int]:
    """The constant, NON-EMPTY always-true predicate fragment spliced in when the
    supplied predicate fragment is empty. Modelled here as the constant 'TRUE';
    the behaviour relies only on its being non-empty."""
    return PSeq(84, 82, 85, 69)

@Pure
def true_params() -> PSeq[int]:
    """The bound parameters carried by the always-true predicate: a single
    opaque parameter token (the always-true predicate binds its truth value as
    one parameter). Spliced in alongside `true_predicate()` when the supplied
    predicate fragment is empty."""
    return PSeq(1)

@Pure
def clause_text(pred: PSeq[int], cons: PSeq[int]) -> PSeq[int]:
    """The rendered clause text for a (predicate, consequent) pair:
    `lead()` then the predicate slot then `sep()` then the consequent.
    The predicate slot is the supplied predicate when non-empty, otherwise the
    constant always-true predicate -- so it is never empty."""
    if len(pred) == 0:
        return lead() + true_predicate() + sep() + cons
    return lead() + pred + sep() + cons

@Pure
def clause_params(pred: PSeq[int], pred_params: PSeq[int],
                  cons_params: PSeq[int]) -> PSeq[int]:
    """The rendered clause's bound parameters: the predicate's parameters
    followed by the consequent's parameters. For an empty supplied predicate
    its parameters are replaced by the always-true predicate's parameters
    (`true_params()`)."""
    if len(pred) == 0:
        return true_params() + cons_params
    return pred_params + cons_params
# pure-end

def render_branch(pred: List[int],
                  pred_params: List[int],
                  cons: List[int],
                  cons_params: List[int]) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All four inputs are read-only upstream products (never mutated): the
    # supplied predicate fragment, its parameters, the consequent fragment and
    # its parameters. Fractional permission, required AND ensured.
    Requires(Acc(list_pred(pred), 1 / 2))
    Requires(Acc(list_pred(pred_params), 1 / 2))
    Requires(Acc(list_pred(cons), 1 / 2))
    Requires(Acc(list_pred(cons_params), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pred), 1 / 2))
    Ensures(Acc(list_pred(pred_params), 1 / 2))
    Ensures(Acc(list_pred(cons), 1 / 2))
    Ensures(Acc(list_pred(cons_params), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The rendered clause text is the constant-shape splice, with the empty
    # supplied predicate replaced by the always-true predicate.
    Ensures(ToSeq(Result()[0]) == clause_text(ToSeq(pred), ToSeq(cons)))
    # The rendered clause's bound parameters, with the empty predicate's
    # parameters replaced by the always-true predicate's parameters.
    Ensures(ToSeq(Result()[1]) ==
            clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)))
    # The discriminating guarantee: the predicate slot of the rendered clause
    # is never blank. Concretely, the rendered text strictly extends the constant
    # 'lead + sep + consequent' framing by at least one predicate code point,
    # for EVERY supplied predicate (including the empty one).
    Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
    # post-conditions-end
    # impl-start
    # Determine the predicate slot text and its parameters: the supplied
    # predicate when non-empty, otherwise the constant always-true predicate.
    cond_text = []  # type: List[int]
    cond_params = []  # type: List[int]
    if len(pred) == 0:
        k = 0
        while k < len(true_predicate()):
            # invariants-start
            Invariant(Acc(list_pred(cond_text)))
            Invariant(0 <= k and k <= len(true_predicate()))
            Invariant(ToSeq(cond_text) == true_predicate().take(k))
            # invariants-end
            cond_text = cond_text + [true_predicate()[k]]
            k = k + 1
        Assert(true_predicate().take(len(true_predicate())) == true_predicate())
        Assert(ToSeq(cond_text) == true_predicate())
        k = 0
        while k < len(true_params()):
            # invariants-start
            Invariant(Acc(list_pred(cond_params)))
            Invariant(Acc(list_pred(cond_text)))
            Invariant(ToSeq(cond_text) == true_predicate())
            Invariant(0 <= k and k <= len(true_params()))
            Invariant(ToSeq(cond_params) == true_params().take(k))
            # invariants-end
            cond_params = cond_params + [true_params()[k]]
            k = k + 1
        Assert(true_params().take(len(true_params())) == true_params())
        # Establish a disjunctive value fact about the predicate slot that holds
        # in this branch; it survives the merge (the else branch proves the
        # other disjunct), pinning cond_text / cond_params to their definitions.
        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
                ToSeq(cond_params) == true_params()) or
               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
                ToSeq(cond_params) == ToSeq(pred_params)))
    else:
        k = 0
        while k < len(pred):
            # invariants-start
            Invariant(Acc(list_pred(cond_text)))
            Invariant(Acc(list_pred(pred), 1 / 2))
            Invariant(len(pred) > 0)
            Invariant(0 <= k and k <= len(pred))
            Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
            # invariants-end
            cond_text = cond_text + [pred[k]]
            k = k + 1
        Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
        Assert(ToSeq(cond_text) == ToSeq(pred))
        k = 0
        while k < len(pred_params):
            # invariants-start
            Invariant(Acc(list_pred(cond_params)))
            Invariant(Acc(list_pred(cond_text)))
            Invariant(Acc(list_pred(pred), 1 / 2))
            Invariant(Acc(list_pred(pred_params), 1 / 2))
            Invariant(len(pred) > 0)
            Invariant(ToSeq(cond_text) == ToSeq(pred))
            Invariant(0 <= k and k <= len(pred_params))
            Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
            # invariants-end
            cond_params = cond_params + [pred_params[k]]
            k = k + 1
        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
        Assert(ToSeq(cond_params) == ToSeq(pred_params))
        Assert(ToSeq(cond_text) == ToSeq(pred))
        Assert(len(pred) != 0)
        # Establish a disjunctive value fact about the predicate slot that holds
        # in this branch; it survives the merge (the if branch proves the other
        # disjunct), pinning cond_text / cond_params to their definitions.
        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
                ToSeq(cond_params) == true_params()) or
               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
                ToSeq(cond_params) == ToSeq(pred_params)))
    # The disjunctive predicate-slot fact survives the merge. It pins cond_text
    # and cond_params to the pure clause definitions and forces the predicate
    # slot to be non-empty.
    Assert(clause_text(ToSeq(pred), ToSeq(cons)) ==
           lead() + ToSeq(cond_text) + sep() + ToSeq(cons))
    Assert(clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)) ==
           ToSeq(cond_params) + ToSeq(cons_params))
    Assert(len(cond_text) > 0)
    # Assemble lead + predicate-slot + sep + consequent.
    text = []  # type: List[int]
    i = 0
    while i < len(lead()):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(0 <= i and i <= len(lead()))
        Invariant(ToSeq(text) == lead().take(i))
        # invariants-end
        text = text + [lead()[i]]
        i = i + 1
    i = 0
    while i < len(cond_text):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(0 <= i and i <= len(cond_text))
        Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
        # invariants-end
        text = text + [cond_text[i]]
        i = i + 1
    i = 0
    while i < len(sep()):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(0 <= i and i <= len(sep()))
        Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
        # invariants-end
        text = text + [sep()[i]]
        i = i + 1
    i = 0
    while i < len(cons):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(Acc(list_pred(cons), 1 / 2))
        Invariant(0 <= i and i <= len(cons))
        Invariant(ToSeq(text) ==
                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
        # invariants-end
        text = text + [cons[i]]
        i = i + 1
    # Combined parameters: predicate-slot parameters then consequent parameters.
    params = []  # type: List[int]
    i = 0
    while i < len(cond_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(0 <= i and i <= len(cond_params))
        Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
        # invariants-end
        params = params + [cond_params[i]]
        i = i + 1
    i = 0
    while i < len(cons_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(Acc(list_pred(cons_params), 1 / 2))
        Invariant(0 <= i and i <= len(cons_params))
        Invariant(ToSeq(params) ==
                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
        # invariants-end
        params = params + [cons_params[i]]
        i = i + 1
    return text, params
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins BOTH outputs as total functions of the inputs: Ensures(ToSeq(Result()[0])==clause_text(ToSeq(pred),ToSeq(cons))), Ensures(ToSeq(Result()[1])==clause_params(...)), plus the discriminating slot-non-blank clause Ensures(len(Result()[0])>len(lead())+len(sep())+len(cons)). The empty-predicate substitution is modeled DEEPLY (clause_text/clause_params empty branch + true_predicate()/true_params()); no @ContractOnly axiom is consumed.

7 attacks encoded, all confirmed same-spec (adversary same-spec exit 0). weakness runs (`python -m swebench_unified.adversary weakness nagini django__django-15930 <path>`) launched concurrently in batches of 3 (each spawns JVM+Z3):

- atk_1 (PREPATCH bug: pred verbatim, no empty-substitution): weakness exit 2 — does NOT verify. Direct nagini_verify shows the exact discriminating failure: `atk_1.py:132: Postcondition ... ToSeq(Result()[0]) == clause_text(...) might not hold` — spec senses the change (G-DIFF), prepatch reproduced.
- atk_2 (CONTROL-FLOW/VACUITY: `while True` infinite loop, return unreachable): weakness exit 2 — does NOT verify. Nagini enforces termination here (no partial-correctness escape).
- atk_3 (PARTIAL-DOMAIN: correct on non-empty pred, blank slot on empty pred): weakness exit 2 — does NOT verify.
- atk_4 (BOUNDARY/CONTENT: substitute lead() (non-empty but WRONG content) for the empty predicate slot): weakness exit 2 — does NOT verify (clause_text eq rejects it even though the slot is non-blank).
- atk_5 (PARAM-ORDER: correct text, params in wrong order cons++cond): weakness exit 2 — does NOT verify (clause_params eq rejects).
- atk_7 (TEXT-BOUNDARY: omit the consequent from the text): weakness exit 2 — does NOT verify.
All 6 rejections are GENUINE verification failures (verify_completed true, no timeouts, no infra errors).

- atk_6 (UNGROUNDED-ORACLE ECHO = the verbatim gold-faithful bundle impl): weakness exit 0 = CANDIDATE (shares spec AND verifies). Per mandatory protocol its faithful refined patch was materialized (atk_6.faithful.patch == the gold hunk, since atk_6 IS the bundle model.py verbatim) and RUN through the official harness: run_resolve("django__django-15930", patch) => resolved=True, completed=True, attempts=1, flaky=False, note="resolved". A resolving echo of the gold is NOT a weakness (policy: candidate breaks the spec only if its refined patch does NOT resolve). So it does not break the spec.

Positive control (pos_control.py = verbatim bundle impl): `bash scripts/nagini_verify.sh` => Verification successful (33.5s), exit 0.

refinement.md audit: every leg is R (steps 1-4,8,10 str/param/template refinement), I (step 5 emptiness test, step 7 non-empty verbatim, step 9 param concat), or A-reference (step 6). NO kind-3 (unexpressible-changed-op) step; NO consumed @ContractOnly axiom (axioms region comment-only). The single A-reference (step 6: true_predicate()/true_params() <-> compile(Value(True))) correspondence holds: axiom_check.py (G-AX) asserts the REAL callee compile(Value(True)) is non-empty ('%s',[True]) — the only property the slot-non-blank postcondition rides on; content is abstracted per mapping.md §2. Correspondence to the real callee is sound.

Summary: 7 attacks run (6 distinct wrong impls + prepatch + echo). Every same-spec VERIFYING impl (only atk_6, the gold echo) has its faithful patch RESOLVING under the harness; no verifying wrong impl exists. verify => correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-15930 (nagini). Modeled function render_branch ↔ When.as_sql (django/db/models/expressions.py:1002), verified real callee and gold patch directly at base_commit worktree.

Real gold: condition_sql,condition_params=compile(self.condition); if condition_sql=="": condition_sql,condition_params=compile(Value(True))=("%s",[True]); text="WHEN "+condition_sql+" THEN "+result_sql; params=condition_params+result_params.

Model: text=lead()+(pred if len>0 else true_predicate())+sep()+cons; params=(pred_params if len>0 else true_params())+cons_params; plus discriminating postcond len(Result[0])>len(lead)+len(sep)+len(cons) (slot length >=1).

Input-by-input under documented abstraction (str<->List[int] codepoints; param list<->List[int] opaque tokens):
 * Substitution gate len(pred)==0 <-> condition_sql=="": identical (empty string = empty codepoint list).
 * Empty branch: model splices non-empty true_predicate()="TRUE"+true_params()=[1], discarding pred_params unconditionally; gold splices ("%s",[True]), discarding condition_params unconditionally. "TRUE"<->"%s" content is abstracted away; ONLY relied-on property is non-emptiness, asserted against REAL compile(Value(True)) by axiom_check.py (G-AX). [1]<->[True] one token. Match.
 * Non-empty branch: both use supplied fragment/params verbatim ++ result. Match.
 * Framing: lead()="WHEN " (5) / sep()=" THEN " (6) are the exact literal pieces of template "WHEN %(condition)s THEN %(result)s", trailing empty (decode-confirmed). Match.
 * Discriminating inequality == slot length >=1: does NOT over-claim; holds on real tree for both cases (non-empty stays >=1; empty->"%s" length 2).

No input found where the modeled function disagrees with real When.as_sql. The single abstraction (concrete "TRUE"/[1] for "%s"/[True]) is a sound identity/type abstraction whose load-bearing property (non-emptiness) is validated against the real callee. Nagini verifies exit 0 (30.5s) so spec is non-vacuous; G-CONF 100360 checked / 0 disagreements. Spec is NOT too strong. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen over the projected spec view PASSES (no diff markers, no reproduced gold-patch line, no patched file path django/db/models/expressions.py, no spec-view identifier or comment naming the patched repo symbols When/as_sql/Value, no bug/fix narration). Confirmed by running swebench_unified.leakage.screen on the real spec_view projection: hard_failures == [].

Semantic check (leakage beyond public problem_statement, NOT hints_text): the public problem_statement already discloses the full desired behavior -- Case() with ~Q(pk__in=[]) (the all-matching sentinel) produces malformed SQL 'CASE WHEN THEN true' (empty predicate slot causing 'syntax error at or near THEN'), and 'I expected behavior to annotate all rows with the value True since they all match.' The spec view formalizes exactly this: a branch rendered as <lead><predicate><sep><consequent>, and 'whenever the supplied predicate fragment is empty, the rendered clause must instead use a constant, NON-EMPTY always-true predicate ... the predicate slot ... is never blank.' This is the desired-behavior restatement the task itself supplies (empty condition -> always-true/True predicate), phrased abstractly as behavior rather than as an edit or code location.

It reveals nothing about the edit mechanics or site beyond the problem statement: it does not name When.as_sql, expressions.py, Value(True), the compiler.compile call, or the 'condition_sql == ""' test in the SOLVER-VISIBLE region. The gold-edit specifics (repo symbols, compile(Value(True)), the empty-string protocol) live only in mapping.md/refinement.md, which are auditor artifacts, not the consumer spec view.

The spec view carries only the irreducible behavioral content already public via the task, so it does not leak the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.