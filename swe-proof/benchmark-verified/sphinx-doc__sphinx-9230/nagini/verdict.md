# P2 adversarial audit — sphinx-doc__sphinx-9230

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies (2 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch_name.py`, `atk_prepatch_type.py`, `atk_wrong_secondlast_name.py`, `atk_wrong_firstonly_type.py`, `atk_partial_domain_name.py`, `atk_echo_forward_type.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_nonterm_name.py`, `atk_nonterm_type.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo_name.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch_name.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 SPACE = 32   # " " — the single separator between elements of a rendered type
 
@@ -98,7 +97,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -109,10 +107,35 @@
             == PSeq(encode_name(last_token(ToSeq(tokens)))))
     # post-conditions-end
     # impl-start
-    last = tokens[len(tokens) - 1]  # type: int
-    Assert(last_token(ToSeq(tokens)) == last)
-    result = [encode_name(last)]  # type: List[int]
-    Assert(ToSeq(result) == PSeq(encode_name(last)))
+    # PRE-PATCH (buggy): a LEFT-most split takes the first token as the type and
+    # leaves EVERYTHING AFTER the first token as the name (the remainder of a
+    # single split). The name is therefore the join of tokens t1 .. t(n-1).
+    tokens_s = ToSeq(tokens)  # type: PSeq[int]
+    n = len(tokens)  # type: int
+    result = []  # type: List[int]
+    i = n
+    while i > 1:
+        # invariants-start
+        Invariant(Acc(list_pred(tokens), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(tokens_s == ToSeq(tokens))
+        Invariant(n == len(tokens))
+        Invariant(1 <= i and i <= n)
+        Invariant(ToSeq(result) == joined(tokens_s.drop(i)))
+        # invariants-end
+        elt = tokens[i - 1]  # type: int
+        Assert(tokens_s.drop(i - 1)[0] == elt)
+        Assert(tokens_s.drop(i - 1).drop(1) == tokens_s.drop(i))
+        if i == n:
+            result = [encode_name(elt)]
+            Assert(ToSeq(result) == joined(tokens_s.drop(i - 1)))
+        else:
+            result = [encode_name(elt), SPACE] + result
+            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
+                   + joined(tokens_s.drop(i)))
+            Assert(ToSeq(result) == joined(tokens_s.drop(i - 1)))
+        i = i - 1
+    Assert(ToSeq(result) == joined(tokens_s.drop(1)))
     return result
     # impl-end
 
@@ -123,7 +146,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -144,7 +166,6 @@
         Invariant(prefix_len == len(tokens) - 1)
         Invariant(0 <= i and i <= prefix_len)
         Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         elt = tokens[i - 1]  # type: int
         Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
```

Attack 2 — `atk_prepatch_type.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 SPACE = 32   # " " — the single separator between elements of a rendered type
 
@@ -98,7 +97,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -123,7 +121,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -132,34 +129,11 @@
     Ensures(ToSeq(Result()) == joined(ToSeq(tokens).take(len(tokens) - 1)))
     # post-conditions-end
     # impl-start
-    tokens_s = ToSeq(tokens)  # type: PSeq[int]
-    prefix_len = len(tokens) - 1  # type: int
-    result = []  # type: List[int]
-    i = prefix_len
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(tokens), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(tokens_s == ToSeq(tokens))
-        Invariant(prefix_len == len(tokens) - 1)
-        Invariant(0 <= i and i <= prefix_len)
-        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        elt = tokens[i - 1]  # type: int
-        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
-        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
-               == tokens_s.take(prefix_len).drop(i))
-        if i == prefix_len:
-            # last token of the prefix: no trailing separator
-            result = [encode_name(elt)]
-            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
-        else:
-            result = [encode_name(elt), SPACE] + result
-            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
-                   + joined(tokens_s.take(prefix_len).drop(i)))
-            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
-        i = i - 1
-    Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
+    # PRE-PATCH (buggy): a LEFT-most split takes only the FIRST token as the
+    # type (the head of a single split), dropping every later token of a
+    # multi-token type. The type is therefore just t0.
+    first = tokens[0]  # type: int
+    result = [encode_name(first)]  # type: List[int]
+    Assert(ToSeq(result) == PSeq(encode_name(first)))
     return result
     # impl-end
```

Attack 3 — `atk_wrong_secondlast_name.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 SPACE = 32   # " " — the single separator between elements of a rendered type
 
@@ -98,7 +97,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -109,10 +107,8 @@
             == PSeq(encode_name(last_token(ToSeq(tokens)))))
     # post-conditions-end
     # impl-start
-    last = tokens[len(tokens) - 1]  # type: int
-    Assert(last_token(ToSeq(tokens)) == last)
+    last = tokens[len(tokens) - 2]  # type: int
     result = [encode_name(last)]  # type: List[int]
-    Assert(ToSeq(result) == PSeq(encode_name(last)))
     return result
     # impl-end
 
@@ -123,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -144,7 +139,6 @@
         Invariant(prefix_len == len(tokens) - 1)
         Invariant(0 <= i and i <= prefix_len)
         Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         elt = tokens[i - 1]  # type: int
         Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
```

Attack 4 — `atk_wrong_firstonly_type.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 SPACE = 32   # " " — the single separator between elements of a rendered type
 
@@ -98,7 +97,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -123,7 +121,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -132,34 +129,7 @@
     Ensures(ToSeq(Result()) == joined(ToSeq(tokens).take(len(tokens) - 1)))
     # post-conditions-end
     # impl-start
-    tokens_s = ToSeq(tokens)  # type: PSeq[int]
-    prefix_len = len(tokens) - 1  # type: int
-    result = []  # type: List[int]
-    i = prefix_len
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(tokens), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(tokens_s == ToSeq(tokens))
-        Invariant(prefix_len == len(tokens) - 1)
-        Invariant(0 <= i and i <= prefix_len)
-        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        elt = tokens[i - 1]  # type: int
-        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
-        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
-               == tokens_s.take(prefix_len).drop(i))
-        if i == prefix_len:
-            # last token of the prefix: no trailing separator
-            result = [encode_name(elt)]
-            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
-        else:
-            result = [encode_name(elt), SPACE] + result
-            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
-                   + joined(tokens_s.take(prefix_len).drop(i)))
-            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
-        i = i - 1
-    Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
+    first = tokens[0]  # type: int
+    result = [encode_name(first)]  # type: List[int]
     return result
     # impl-end
```

Attack 5 — `atk_partial_domain_name.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 SPACE = 32   # " " — the single separator between elements of a rendered type
 
@@ -98,7 +97,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -109,10 +107,11 @@
             == PSeq(encode_name(last_token(ToSeq(tokens)))))
     # post-conditions-end
     # impl-start
-    last = tokens[len(tokens) - 1]  # type: int
-    Assert(last_token(ToSeq(tokens)) == last)
-    result = [encode_name(last)]  # type: List[int]
-    Assert(ToSeq(result) == PSeq(encode_name(last)))
+    result = []  # type: List[int]
+    if len(tokens) == 2:
+        result = [encode_name(tokens[len(tokens) - 1])]
+    else:
+        result = [encode_name(tokens[0])]
     return result
     # impl-end
 
@@ -123,7 +122,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -144,7 +142,6 @@
         Invariant(prefix_len == len(tokens) - 1)
         Invariant(0 <= i and i <= prefix_len)
         Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         elt = tokens[i - 1]  # type: int
         Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
```

Attack 6 — `atk_nonterm_name.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 SPACE = 32   # " " — the single separator between elements of a rendered type
 
@@ -98,7 +97,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -109,10 +107,11 @@
             == PSeq(encode_name(last_token(ToSeq(tokens)))))
     # post-conditions-end
     # impl-start
-    last = tokens[len(tokens) - 1]  # type: int
-    Assert(last_token(ToSeq(tokens)) == last)
-    result = [encode_name(last)]  # type: List[int]
-    Assert(ToSeq(result) == PSeq(encode_name(last)))
+    result = [encode_name(tokens[len(tokens) - 1])]  # type: List[int]
+    while True:
+        Invariant(Acc(list_pred(result)))
+        Invariant(Acc(list_pred(tokens), 1 / 2))
+        pass
     return result
     # impl-end
 
@@ -123,7 +122,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -144,7 +142,6 @@
         Invariant(prefix_len == len(tokens) - 1)
         Invariant(0 <= i and i <= prefix_len)
         Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         elt = tokens[i - 1]  # type: int
         Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
```

Attack 7 — `atk_nonterm_type.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 SPACE = 32   # " " — the single separator between elements of a rendered type
 
@@ -98,7 +97,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -123,7 +121,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -132,34 +129,10 @@
     Ensures(ToSeq(Result()) == joined(ToSeq(tokens).take(len(tokens) - 1)))
     # post-conditions-end
     # impl-start
-    tokens_s = ToSeq(tokens)  # type: PSeq[int]
-    prefix_len = len(tokens) - 1  # type: int
     result = []  # type: List[int]
-    i = prefix_len
-    while i > 0:
-        # invariants-start
+    while True:
+        Invariant(Acc(list_pred(result)))
         Invariant(Acc(list_pred(tokens), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(tokens_s == ToSeq(tokens))
-        Invariant(prefix_len == len(tokens) - 1)
-        Invariant(0 <= i and i <= prefix_len)
-        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        elt = tokens[i - 1]  # type: int
-        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
-        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
-               == tokens_s.take(prefix_len).drop(i))
-        if i == prefix_len:
-            # last token of the prefix: no trailing separator
-            result = [encode_name(elt)]
-            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
-        else:
-            result = [encode_name(elt), SPACE] + result
-            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
-                   + joined(tokens_s.take(prefix_len).drop(i)))
-            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
-        i = i - 1
-    Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
+        pass
     return result
     # impl-end
```

Attack 8 — `atk_echo_forward_type.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 SPACE = 32   # " " — the single separator between elements of a rendered type
 
@@ -98,7 +97,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -123,7 +121,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -135,31 +132,24 @@
     tokens_s = ToSeq(tokens)  # type: PSeq[int]
     prefix_len = len(tokens) - 1  # type: int
     result = []  # type: List[int]
-    i = prefix_len
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < prefix_len:
         Invariant(Acc(list_pred(tokens), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(tokens_s == ToSeq(tokens))
         Invariant(prefix_len == len(tokens) - 1)
         Invariant(0 <= i and i <= prefix_len)
-        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        elt = tokens[i - 1]  # type: int
-        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
-        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
-               == tokens_s.take(prefix_len).drop(i))
-        if i == prefix_len:
-            # last token of the prefix: no trailing separator
+        Invariant(ToSeq(result) == joined(tokens_s.take(i)))
+        elt = tokens[i]  # type: int
+        Assert(tokens_s.take(i + 1).drop(i)[0] == elt)
+        if i == 0:
             result = [encode_name(elt)]
-            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
+            Assert(ToSeq(result) == joined(tokens_s.take(i + 1)))
         else:
-            result = [encode_name(elt), SPACE] + result
-            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
-                   + joined(tokens_s.take(prefix_len).drop(i)))
-            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
-        i = i - 1
+            result = result + [SPACE, encode_name(elt)]
+            Assert(ToSeq(result) == joined(tokens_s.take(i)) + PSeq(SPACE) + PSeq(encode_name(elt)))
+            Assert(joined(tokens_s.take(i)) + PSeq(SPACE) + PSeq(encode_name(elt)) == joined(tokens_s.take(i + 1)))
+        i = i + 1
     Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
     return result
     # impl-end
```

Attack 9 — `atk_echo_name.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 SPACE = 32   # " " — the single separator between elements of a rendered type
 
@@ -98,7 +97,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -109,9 +107,11 @@
             == PSeq(encode_name(last_token(ToSeq(tokens)))))
     # post-conditions-end
     # impl-start
-    last = tokens[len(tokens) - 1]  # type: int
+    n = len(tokens)  # type: int
+    last = tokens[n - 1]  # type: int
     Assert(last_token(ToSeq(tokens)) == last)
-    result = [encode_name(last)]  # type: List[int]
+    result = []  # type: List[int]
+    result = [encode_name(last)] + result
     Assert(ToSeq(result) == PSeq(encode_name(last)))
     return result
     # impl-end
@@ -123,7 +123,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(tokens), 1 / 2))
     Requires(len(tokens) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tokens), 1 / 2))
@@ -144,7 +143,6 @@
         Invariant(prefix_len == len(tokens) - 1)
         Invariant(0 <= i and i <= prefix_len)
         Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         elt = tokens[i - 1]  # type: int
         Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9230.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A typed field argument is a run of tokens (a token is one maximal
  whitespace-free chunk). The whole run carries two pieces of information: a
  parameter name and a parameter type description. The type description may
  itself span several tokens (e.g. a comma-separated generic such as
  ``dict(str, str)``). The desired parse assigns these two pieces structurally
  over the run t0 t1 ... t(n-1) of n >= 2 tokens:

    (1) the parsed name is exactly the FINAL element of the run, t(n-1); and
    (2) the parsed type is the ordered PREFIX of the run — every element before
        the last, t0 t1 ... t(n-2), in their original order, separated by a
        single space — so that none of the leading tokens of a multi-token type
        is dropped.

  When the prefix is a single token the result is just (t0, t1); when the
  prefix spans several tokens every one of them is retained, in order, ahead of
  the name.

Modelling choices (Nagini fragment):
  * `str` indexing/iteration crashes Nagini, so the argument is modelled as the
    sequence of its tokens. Each token is one distinct symbol (an `int >= 0`);
    the run is a `List[int]` (carrier) / `PSeq[int]` (specification). The
    rendered type re-emits each prefix element separated by a single space;
    mapping.md records that the run abstracts the maximal whitespace-free chunks
    of the real string and that the modelled domain is single-space-separated
    input (so the single-space rendering reproduces the original type text).
  * A token is emitted into a rendered type via `encode_name`, kept disjoint
    from the separator code point so a token is never confused with the
    separating space.
  * The structural parse is modelled DEEPLY (a front-recursive prefix fold +
    verified construction loops), not behind a consumed axiom; on the modelled
    single-space-separated domain axiom_check.py (G-AX) validates it against the
    real `str` behaviour as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

SPACE = 32   # " " — the single separator between elements of a rendered type

# axioms-start
# No consumed axioms. The structural assignment of name (final element) and type
# (ordered prefix) is the behaviour under specification and is modelled deeply
# (the pure fold below + the impl loops spell it out). The only library behaviour
# relied on is that re-emitting a token prefix separated by single spaces
# reproduces the original type text WHEN the input is single-space-separated;
# this is validated out-of-band by axiom_check.py (G-AX) as an A-reference on
# that modelled domain, not consumed as an axiom.
# axioms-end

# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)

@Pure
def encode_name(t: int) -> int:
    """Encode a token disjointly from the separator code point, so a token can
    never be confused with the separating space in a rendered type. Tokens are
    emitted as (token + 256)."""
    return t + 256

@Pure
def last_token(run: PSeq[int]) -> int:
    """The final token of a non-empty run."""
    Requires(len(run) >= 1)
    return run[len(run) - 1]

@Pure
def joined(run: PSeq[int]) -> PSeq[int]:
    """The single-space-separated rendering of a run of tokens, in order.
    Front-recursive so a single unfold is available per construction step.
    Empty for an empty run; the lone token for a single-token run; otherwise
    every token in order separated by one space."""
    if len(run) == 0:
        return empty_seq()
    if len(run) == 1:
        return PSeq(encode_name(run[0]))
    return PSeq(encode_name(run[0])) + PSeq(SPACE) + joined(run.drop(1))
# pure-end

def parsed_argument_name(tokens: List[int]) -> List[int]:
    """The parsed parameter name of a typed argument: the FINAL element of the
    run (rendered as a one-element sequence). Per (1)."""
    # pre-conditions-start
    Requires(Acc(list_pred(tokens), 1 / 2))
    Requires(len(tokens) >= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The name is exactly the last token, rendered as a one-token sequence.
    Ensures(len(ToSeq(tokens)) == len(tokens) and len(ToSeq(tokens)) >= 2
            and ToSeq(Result())
            == PSeq(encode_name(last_token(ToSeq(tokens)))))
    # post-conditions-end
    # impl-start
    last = tokens[len(tokens) - 1]  # type: int
    Assert(last_token(ToSeq(tokens)) == last)
    result = [encode_name(last)]  # type: List[int]
    Assert(ToSeq(result) == PSeq(encode_name(last)))
    return result
    # impl-end

def parsed_argument_type(tokens: List[int]) -> List[int]:
    """The parsed type of a typed argument: the ordered PREFIX of the run —
    every element before the last, separated by single spaces. Per (2)."""
    # pre-conditions-start
    Requires(Acc(list_pred(tokens), 1 / 2))
    Requires(len(tokens) >= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The type is the join of every token up to (but excluding) the last.
    Ensures(ToSeq(Result()) == joined(ToSeq(tokens).take(len(tokens) - 1)))
    # post-conditions-end
    # impl-start
    tokens_s = ToSeq(tokens)  # type: PSeq[int]
    prefix_len = len(tokens) - 1  # type: int
    result = []  # type: List[int]
    i = prefix_len
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(tokens_s == ToSeq(tokens))
        Invariant(prefix_len == len(tokens) - 1)
        Invariant(0 <= i and i <= prefix_len)
        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
        # invariants-end
        elt = tokens[i - 1]  # type: int
        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
               == tokens_s.take(prefix_len).drop(i))
        if i == prefix_len:
            # last token of the prefix: no trailing separator
            result = [encode_name(elt)]
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        else:
            result = [encode_name(elt), SPACE] + result
            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
                   + joined(tokens_s.take(prefix_len).drop(i)))
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        i = i - 1
    Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. sphinx-doc__sphinx-9230 nagini bundle. Scratch dir: Project root: (module run via python -m swebench_unified.adversary).

SPEC SHAPE: two modeled functions with postconditions pinning EXACT output sequences over PSeq[int]. parsed_argument_name: ToSeq(Result())==PSeq(encode_name(last_token(ToSeq(tokens)))) (name = final token). parsed_argument_type: ToSeq(Result())==joined(ToSeq(tokens).take(len-1)) (type = ordered leading prefix, single-space rendered). No consumed axioms (axioms region empty, no @ContractOnly). Deep-model references validated by axiom_check.py (G-AX).

POSITIVE CONTROL: positive_control.py (= model.py) verifies, exit 0 (bash scripts/nagini_verify.sh, ~13-16s).

PREPATCH REPRODUCED (spec catches the bug): both prepatch skeletons share spec byte-identical (same-spec exit 0) and FAIL to verify against the frozen spec (weakness exit 2 = NOT-A-COUNTEREXAMPLE, verification failed):
 - atk_prepatch_name.py (=model_prepatch.py): name = joined(tokens.drop(1)) [old split remainder] -> fails name postcondition for n>=3.
 - atk_prepatch_type.py (=model_prepatch_2.py): type = first token only -> fails type postcondition for n>=3.

### ATTACK LEDGER (cmd: adversary weakness nagini sphinx-doc__sphinx-9230 <file>; all same-spec exit 0 first).
REJECTED by spec (exit 2, GOOD): atk_prepatch_name, atk_prepatch_type, atk_wrong_secondlast_name (name=t[n-2]), atk_wrong_firstonly_type (type=t0 only, distinct construction from prepatch_2), atk_partial_domain_name (correct only when len==2, else t0 -> spec quantifies all len>=2 so caught), atk_echo_forward_type (forward-loop type impl; my proof annotations insufficient -> did not verify).

NOT JUDGED (front end refused the program, so the spec never ruled on it and it counts in neither tally): atk_nonterm_name / atk_nonterm_type (while True: -> Nagini 'Type error: dead.code' at the return, translation fails) never reached the verifier; that establishes only that this attack shape is unexpressible in Nagini's fragment, not that the control-flow-effect angle is closed — whether the frozen spec's method-level MustTerminate would reject a TRANSLATABLE diverging rival is a separate question these two do not settle. CANDIDATE (exit 0 = same-spec AND verifies): atk_echo_name.py -- a behaviorally-correct echo of parsed_argument_name (name=last token via prepend construction).

Its faithful refined patch is the gold rsplit one-liner; materialized as patch (see patches map) and RUN through official harness run_resolve('sphinx-doc__sphinx-9230', patch) => completed=True, resolved=True. Correct echo (verifies AND resolves) -> NOT a weakness.

EXCLUDED-AND-DISCLOSED framework escapes (deliberately NOT in the attacks list): atk_assume_name.py and atk_assume_type.py inject Assume(False) then return an empty list; they come back CANDIDATE (same-spec exit 0, verify exit 0, ~13-14s) because partial-correctness verification is poisoned by the false assumption. I do NOT count these as G-EQ counterexamples because:

(1) 'Assume(' is a G-HYGIENE BANNED TOKEN for the nagini backend (backends/nagini.py banned_tokens=('Assume(','Refute(')); verified programmatically that gates.hygiene._banned_calls flags ['Assume'] on both files and [] on positive_control -> such a bundle can never ship;

(2) Assume(False) verifies against ANY postcondition in ANY bundle, so it is a verifier-vacuity escape, not evidence THIS spec is too weak;

(3) it is a proof-only annotation with NO faithful executable refinement of any real repo operation -- any honest materialization of the actual code is the correct behavior (=> gold patch => resolves, executed resolved=True above). Screened by G-HYGIENE, not G-EQ. Submitting them (with or without a patch) would only force a spurious mechanized fail. I checked the whole spec: there is no MustTerminate/termination obligation, which is why I probed non-termination (atk_nonterm_*) — but Nagini's translator rejects the unreachable return as dead.code, so that angle does not yield a verifying wrong impl either.

REFINEMENT.MD AUDIT (A-legs + correspondence): legs A1/B1 = R (str <-> List[int] of whitespace tokens, mapping.md §2). A2 = R + A-reference: name=last_token, G-AX confirms == real str.rsplit(None,1) name side on ALL inputs (separator-insensitive). B2 = R + A-reference (single-space domain): type=joined(take(n-1)), G-AX confirms == real argtype ONLY on single-space-separated input; the modeled-domain restriction is stated explicitly (mapping.md §2/§3.1, meta deep_model_references) and the out-of-domain (multi-whitespace/tab/leading) divergence is DEMONSTRATED, not dodged. No kind-3 (unexpressible-changed-op) legs; NO consumed axioms. axiom_check.py (G-AX) executed: exit 0, de-rigged (fuzzes real callee native whitespace domain: 7 boundary + 4 tested-fieldarg + 325 in-domain + 19675 excluded fuzz + 4 explicit witnesses; asserts old split(None,1) wrong for n>=3; <2-token ValueError path identical). A-reference correspondence to the real callee holds.

CONCLUSION: Every hygiene-clean wrong impl that reached the verifier (partial-domain, boundary, first-token truncation, second-to-last, prepatch reversions) is REJECTED by the frozen spec; the two control-flow-effect/non-termination shapes never reached it (the front end refused to translate them), so the spec never ruled on them and that angle is untested here. The only same-spec verifying hygiene-clean impl is a behaviorally-correct echo whose faithful patch RESOLVES (executed). The Assume(False) vacuity cheats are G-HYGIENE-banned framework escapes with no faithful patch, not G-EQ weaknesses. Attack floor met (9 legitimate attacks >= 5), prepatch reproduced, positive control verifies, G-AX passes. verify => correct holds for this spec on the tested/modeled domain. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies (2 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch_name.py`, `atk_prepatch_type.py`, `atk_wrong_secondlast_name.py`, `atk_wrong_firstonly_type.py`, `atk_partial_domain_name.py`, `atk_echo_forward_type.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_nonterm_name.py`, `atk_nonterm_type.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo_name.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch_name.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_prepatch_type.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_wrong_secondlast_name.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_wrong_firstonly_type.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_partial_domain_name.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_nonterm_name.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 7 — `atk_nonterm_type.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 8 — `atk_echo_forward_type.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_echo_name.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9230.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A typed field argument is a run of tokens (a token is one maximal
  whitespace-free chunk). The whole run carries two pieces of information: a
  parameter name and a parameter type description. The type description may
  itself span several tokens (e.g. a comma-separated generic such as
  ``dict(str, str)``). The desired parse assigns these two pieces structurally
  over the run t0 t1 ... t(n-1) of n >= 2 tokens:

    (1) the parsed name is exactly the FINAL element of the run, t(n-1); and
    (2) the parsed type is the ordered PREFIX of the run — every element before
        the last, t0 t1 ... t(n-2), in their original order, separated by a
        single space — so that none of the leading tokens of a multi-token type
        is dropped.

  When the prefix is a single token the result is just (t0, t1); when the
  prefix spans several tokens every one of them is retained, in order, ahead of
  the name.

Modelling choices (Nagini fragment):
  * `str` indexing/iteration crashes Nagini, so the argument is modelled as the
    sequence of its tokens. Each token is one distinct symbol (an `int >= 0`);
    the run is a `List[int]` (carrier) / `PSeq[int]` (specification). The
    rendered type re-emits each prefix element separated by a single space;
    mapping.md records that the run abstracts the maximal whitespace-free chunks
    of the real string and that the modelled domain is single-space-separated
    input (so the single-space rendering reproduces the original type text).
  * A token is emitted into a rendered type via `encode_name`, kept disjoint
    from the separator code point so a token is never confused with the
    separating space.
  * The structural parse is modelled DEEPLY (a front-recursive prefix fold +
    verified construction loops), not behind a consumed axiom; on the modelled
    single-space-separated domain axiom_check.py (G-AX) validates it against the
    real `str` behaviour as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

SPACE = 32   # " " — the single separator between elements of a rendered type

# axioms-start
# No consumed axioms. The structural assignment of name (final element) and type
# (ordered prefix) is the behaviour under specification and is modelled deeply
# (the pure fold below + the impl loops spell it out). The only library behaviour
# relied on is that re-emitting a token prefix separated by single spaces
# reproduces the original type text WHEN the input is single-space-separated;
# this is validated out-of-band by axiom_check.py (G-AX) as an A-reference on
# that modelled domain, not consumed as an axiom.
# axioms-end

# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)

@Pure
def encode_name(t: int) -> int:
    """Encode a token disjointly from the separator code point, so a token can
    never be confused with the separating space in a rendered type. Tokens are
    emitted as (token + 256)."""
    return t + 256

@Pure
def last_token(run: PSeq[int]) -> int:
    """The final token of a non-empty run."""
    Requires(len(run) >= 1)
    return run[len(run) - 1]

@Pure
def joined(run: PSeq[int]) -> PSeq[int]:
    """The single-space-separated rendering of a run of tokens, in order.
    Front-recursive so a single unfold is available per construction step.
    Empty for an empty run; the lone token for a single-token run; otherwise
    every token in order separated by one space."""
    if len(run) == 0:
        return empty_seq()
    if len(run) == 1:
        return PSeq(encode_name(run[0]))
    return PSeq(encode_name(run[0])) + PSeq(SPACE) + joined(run.drop(1))
# pure-end

def parsed_argument_name(tokens: List[int]) -> List[int]:
    """The parsed parameter name of a typed argument: the FINAL element of the
    run (rendered as a one-element sequence). Per (1)."""
    # pre-conditions-start
    Requires(Acc(list_pred(tokens), 1 / 2))
    Requires(len(tokens) >= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The name is exactly the last token, rendered as a one-token sequence.
    Ensures(len(ToSeq(tokens)) == len(tokens) and len(ToSeq(tokens)) >= 2
            and ToSeq(Result())
            == PSeq(encode_name(last_token(ToSeq(tokens)))))
    # post-conditions-end
    # impl-start
    last = tokens[len(tokens) - 1]  # type: int
    Assert(last_token(ToSeq(tokens)) == last)
    result = [encode_name(last)]  # type: List[int]
    Assert(ToSeq(result) == PSeq(encode_name(last)))
    return result
    # impl-end

def parsed_argument_type(tokens: List[int]) -> List[int]:
    """The parsed type of a typed argument: the ordered PREFIX of the run —
    every element before the last, separated by single spaces. Per (2)."""
    # pre-conditions-start
    Requires(Acc(list_pred(tokens), 1 / 2))
    Requires(len(tokens) >= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The type is the join of every token up to (but excluding) the last.
    Ensures(ToSeq(Result()) == joined(ToSeq(tokens).take(len(tokens) - 1)))
    # post-conditions-end
    # impl-start
    tokens_s = ToSeq(tokens)  # type: PSeq[int]
    prefix_len = len(tokens) - 1  # type: int
    result = []  # type: List[int]
    i = prefix_len
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(tokens_s == ToSeq(tokens))
        Invariant(prefix_len == len(tokens) - 1)
        Invariant(0 <= i and i <= prefix_len)
        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
        # invariants-end
        elt = tokens[i - 1]  # type: int
        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
               == tokens_s.take(prefix_len).drop(i))
        if i == prefix_len:
            # last token of the prefix: no trailing separator
            result = [encode_name(elt)]
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        else:
            result = [encode_name(elt), SPACE] + result
            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
                   + joined(tokens_s.take(prefix_len).drop(i)))
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        i = i - 1
    Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. sphinx-doc__sphinx-9230 nagini bundle. Scratch dir: Project root: (module run via python -m swebench_unified.adversary).

SPEC SHAPE: two modeled functions with postconditions pinning EXACT output sequences over PSeq[int]. parsed_argument_name: ToSeq(Result())==PSeq(encode_name(last_token(ToSeq(tokens)))) (name = final token). parsed_argument_type: ToSeq(Result())==joined(ToSeq(tokens).take(len-1)) (type = ordered leading prefix, single-space rendered). No consumed axioms (axioms region empty, no @ContractOnly). Deep-model references validated by axiom_check.py (G-AX).

POSITIVE CONTROL: positive_control.py (= model.py) verifies, exit 0 (bash scripts/nagini_verify.sh, ~13-16s).

PREPATCH REPRODUCED (spec catches the bug): both prepatch skeletons share spec byte-identical (same-spec exit 0) and FAIL to verify against the frozen spec (weakness exit 2 = NOT-A-COUNTEREXAMPLE, verification failed):
 - atk_prepatch_name.py (=model_prepatch.py): name = joined(tokens.drop(1)) [old split remainder] -> fails name postcondition for n>=3.
 - atk_prepatch_type.py (=model_prepatch_2.py): type = first token only -> fails type postcondition for n>=3.

### ATTACK LEDGER (cmd: adversary weakness nagini sphinx-doc__sphinx-9230 <file>; all same-spec exit 0 first).
REJECTED by spec (exit 2, GOOD): atk_prepatch_name, atk_prepatch_type, atk_wrong_secondlast_name (name=t[n-2]), atk_wrong_firstonly_type (type=t0 only, distinct construction from prepatch_2), atk_partial_domain_name (correct only when len==2, else t0 -> spec quantifies all len>=2 so caught), atk_echo_forward_type (forward-loop type impl; my proof annotations insufficient -> did not verify).

NOT JUDGED (front end refused the program, so the spec never ruled on it and it counts in neither tally): atk_nonterm_name / atk_nonterm_type (while True: -> Nagini 'Type error: dead.code' at the return, translation fails) never reached the verifier; that establishes only that this attack shape is unexpressible in Nagini's fragment, not that the control-flow-effect angle is closed — whether the frozen spec's method-level MustTerminate would reject a TRANSLATABLE diverging rival is a separate question these two do not settle. CANDIDATE (exit 0 = same-spec AND verifies): atk_echo_name.py -- a behaviorally-correct echo of parsed_argument_name (name=last token via prepend construction).

Its faithful refined patch is the gold rsplit one-liner; materialized as patch (see patches map) and RUN through official harness run_resolve('sphinx-doc__sphinx-9230', patch) => completed=True, resolved=True. Correct echo (verifies AND resolves) -> NOT a weakness.

EXCLUDED-AND-DISCLOSED framework escapes (deliberately NOT in the attacks list): atk_assume_name.py and atk_assume_type.py inject Assume(False) then return an empty list; they come back CANDIDATE (same-spec exit 0, verify exit 0, ~13-14s) because partial-correctness verification is poisoned by the false assumption. I do NOT count these as G-EQ counterexamples because:

(1) 'Assume(' is a G-HYGIENE BANNED TOKEN for the nagini backend (backends/nagini.py banned_tokens=('Assume(','Refute(')); verified programmatically that gates.hygiene._banned_calls flags ['Assume'] on both files and [] on positive_control -> such a bundle can never ship;

(2) Assume(False) verifies against ANY postcondition in ANY bundle, so it is a verifier-vacuity escape, not evidence THIS spec is too weak;

(3) it is a proof-only annotation with NO faithful executable refinement of any real repo operation -- any honest materialization of the actual code is the correct behavior (=> gold patch => resolves, executed resolved=True above). Screened by G-HYGIENE, not G-EQ. Submitting them (with or without a patch) would only force a spurious mechanized fail. I checked the whole spec: there is no MustTerminate/termination obligation, which is why I probed non-termination (atk_nonterm_*) — but Nagini's translator rejects the unreachable return as dead.code, so that angle does not yield a verifying wrong impl either.

REFINEMENT.MD AUDIT (A-legs + correspondence): legs A1/B1 = R (str <-> List[int] of whitespace tokens, mapping.md §2). A2 = R + A-reference: name=last_token, G-AX confirms == real str.rsplit(None,1) name side on ALL inputs (separator-insensitive). B2 = R + A-reference (single-space domain): type=joined(take(n-1)), G-AX confirms == real argtype ONLY on single-space-separated input; the modeled-domain restriction is stated explicitly (mapping.md §2/§3.1, meta deep_model_references) and the out-of-domain (multi-whitespace/tab/leading) divergence is DEMONSTRATED, not dodged. No kind-3 (unexpressible-changed-op) legs; NO consumed axioms. axiom_check.py (G-AX) executed: exit 0, de-rigged (fuzzes real callee native whitespace domain: 7 boundary + 4 tested-fieldarg + 325 in-domain + 19675 excluded fuzz + 4 explicit witnesses; asserts old split(None,1) wrong for n>=3; <2-token ValueError path identical). A-reference correspondence to the real callee holds.

CONCLUSION: Every hygiene-clean wrong impl that reached the verifier (partial-domain, boundary, first-token truncation, second-to-last, prepatch reversions) is REJECTED by the frozen spec; the two control-flow-effect/non-termination shapes never reached it (the front end refused to translate them), so the spec never ruled on them and that angle is untested here. The only same-spec verifying hygiene-clean impl is a behaviorally-correct echo whose faithful patch RESOLVES (executed). The Assume(False) vacuity cheats are G-HYGIENE-banned framework escapes with no faithful patch, not G-EQ weaknesses. Attack floor met (9 legitimate attacks >= 5), prepatch reproduced, positive control verifies, G-AX passes. verify => correct holds for this spec on the tested/modeled domain. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness holds on the entire modeled domain. The two modeled functions reduce exactly to str.rsplit(None,1): parsed_argument_name = last token; parsed_argument_type = joined(take(n-1)) = single-space rendering of the leading n-1 tokens. Gold patch is split(None,1)->rsplit(None,1) at sphinx/util/docfields.py:301 (confirmed base commit 567ff2271 uses split). Independent verification: (1) 500,000-input fuzz over the modeled single-space-separated domain (len(tokens)>=2) found ZERO divergences between the model and the real str.rsplit(None,1); (2) bundle's axiom_check.py runs exit 0 with 20k native-domain fuzz + boundary + tested-fieldarg witnesses; (3) the F2P input ':param Dict[str, str] params:' -> fieldarg 'Dict[str, str] params' is single-space (in-domain), and both model and rsplit yield ('Dict[str, str]','params'), so resolve coverage is intact; the ':type items: Tuple[str, ...]' case uses a non-split path. The ONLY place the model differs from the real callee is genuine multi-whitespace/tab/leading input (e.g. 'dict(str,  str) opc_meta', 'int\t\tname'), where the single-space rejoin differs from rsplit's verbatim left piece. That is NOT unfaithful drift: it is an explicitly documented modeled-domain restriction (mapping.md sec2/3.1) that axiom_check.py both WITNESSES (real divergence required) and asserts the restriction for; the name side stays separator-insensitive and matches on all inputs, and no F2P/P2P tested input falls in the excluded sub-domain. Could not run conformance_check.py against the real repo (base-commit source incompatible with the venv's py3.11: 'from types import Union'), but the model's semantics are provably identical to rsplit on the modeled domain, so no diverging input exists within the domain the spec claims. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Extracted the consumer-facing spec view via markers.spec_view(model.py, NaginiBackend): both impl regions are elided ('... implementation elided — supplied by the consumer'); what remains is the module docstring, imports, the axioms comment ('No consumed axioms'), the @Pure helpers (empty_seq/encode_name/last_token/joined), and the pre/post-conditions of parsed_argument_name and parsed_argument_type.

Mechanical G-LEAK screen: PASS (no hard failures). Gold patch = the one-liner in sphinx/util/docfields.py:301 changing `fieldarg.split(None, 1)` -> `fieldarg.rsplit(None, 1)`. Changed symbols = {'transform'}; changed files = sphinx/util/docfields.py; changed lines = the split/rsplit pair. None appear in the spec view.

Independent fingerprint check over the lowercased spec view: 'split', 'rsplit', 'docfields', 'fieldarg', 'maxsplit', ':param', 'argtype', 'argname', 'sphinx/util', base_commit prefix — ALL absent. No diff markers, no patched file path, no repo function/symbol, no line number.

Semantic leakage assessment vs the PUBLIC problem_statement (dataset row, NOT hints_text): the problem_statement already fully discloses the desired behavior — for ':param dict(str, str) opc_meta:' the buggy render is 'str) opc_meta (dict(str,)' (type = first token, name = remainder) and the EXPECTED render is 'opc_meta (dict(str,str))' i.e. name = last whitespace token, type = everything before it. The spec view formalizes exactly and only this: (1) parsed name = FINAL element of the run; (2) parsed type = ordered PREFIX (every element before the last), single-space rejoined. Postconditions encode the same (name == PSeq(encode_name(last_token(...))), type == joined(take(len-1))). The 'dict(str, str)' docstring example is lifted verbatim from the public problem_statement. The only extra 'hint' (single-space-separated domain) is a Nagini modeling restriction (whitespace runs collapse to one SPACE), not gold-edit information. Everything in the spec view is derivable from the problem_statement's own expected-vs-actual rendering.

The gold hunk text and file:line 'sphinx/util/docfields.py:301' are quoted only in refinement.md and mapping.md, which are audit/derivation artifacts and NOT part of the consumer-facing spec view — out of scope for this gate.

relaxed_leakage flag: None; no RELAXED_LEAKAGE.md — no relaxation deferral needed. Conclusion: the spec view leaks no gold-edit information beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.