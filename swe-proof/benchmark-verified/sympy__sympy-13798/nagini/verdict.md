# P2 adversarial audit — sympy__sympy-13798

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_partial_domain.py`, `atk_2_boundary_drop_spacing.py`, `atk_3_ctrlflow_swap_seps.py`, `atk_4_none_blank.py`, `atk_5_offbyone.py`, `atk_6_dot_always.py`, `atk_7_trimmed_exploit.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def general_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -186,41 +184,19 @@
     if sym is None:
         return [32]
     s = ToSeq(sym)
-    Assert(s == ToSeq(sym))
     if s == tok_dot():
-        Assert(general_sep_of(sym) == token_sep(s))
         return [32, 92, 99, 100, 111, 116, 32]
     if s == tok_times():
-        Assert(general_sep_of(sym) == token_sep(s))
         return [32, 92, 116, 105, 109, 101, 115, 32]
     if s == tok_ldot():
-        Assert(general_sep_of(sym) == token_sep(s))
         return [32, 92, 44, 46, 92, 44, 32]
-    Assert(not is_known_token(s))
-    Assert(general_sep_of(sym) == ToSeq(sym))
-    res = []  # type: List[int]
-    i = 0
-    while i < len(sym):
-        # invariants-start
-        Invariant(Acc(list_pred(sym), 1 / 2))
-        Invariant(Acc(list_pred(res)))
-        Invariant(0 <= i and i <= len(sym))
-        Invariant(ToSeq(res) == ToSeq(sym).take(i))
-        Invariant(general_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
-        # invariants-end
-        Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
-        res = res + [sym[i]]
-        i = i + 1
-    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
-    return res
+    return [32]
     # impl-end
 
 
 def numeric_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -257,7 +233,6 @@
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
         Invariant(numeric_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
         # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
```

Attack 2 — `atk_2_boundary_drop_spacing.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def general_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -207,7 +205,6 @@
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
         Invariant(general_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
         # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
@@ -220,7 +217,6 @@
 def numeric_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -232,33 +228,19 @@
     if sym is None:
         return [32, 92, 99, 100, 111, 116, 32]
     s = ToSeq(sym)
-    Assert(s == ToSeq(sym))
     if s == tok_dot():
-        Assert(numeric_sep_of(sym) == token_sep(s))
         return [32, 92, 99, 100, 111, 116, 32]
     if s == tok_times():
-        Assert(numeric_sep_of(sym) == token_sep(s))
         return [32, 92, 116, 105, 109, 101, 115, 32]
     if s == tok_ldot():
-        Assert(numeric_sep_of(sym) == token_sep(s))
         return [32, 92, 44, 46, 92, 44, 32]
-    Assert(not is_known_token(s))
-    t = trimmed(s)
-    if is_spacing_only(t):
-        Assert(numeric_sep_of(sym) == sep_dot())
-        return [32, 92, 99, 100, 111, 116, 32]
-    Assert(numeric_sep_of(sym) == ToSeq(sym))
     res = []  # type: List[int]
     i = 0
     while i < len(sym):
-        # invariants-start
         Invariant(Acc(list_pred(sym), 1 / 2))
         Invariant(Acc(list_pred(res)))
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
-        Invariant(numeric_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
-        # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
         i = i + 1
```

Attack 3 — `atk_3_ctrlflow_swap_seps.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def general_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -186,33 +184,22 @@
     if sym is None:
         return [32]
     s = ToSeq(sym)
-    Assert(s == ToSeq(sym))
     if s == tok_dot():
-        Assert(general_sep_of(sym) == token_sep(s))
         return [32, 92, 99, 100, 111, 116, 32]
     if s == tok_times():
-        Assert(general_sep_of(sym) == token_sep(s))
+        return [32, 92, 44, 46, 92, 44, 32]
+    if s == tok_ldot():
         return [32, 92, 116, 105, 109, 101, 115, 32]
-    if s == tok_ldot():
-        Assert(general_sep_of(sym) == token_sep(s))
-        return [32, 92, 44, 46, 92, 44, 32]
-    Assert(not is_known_token(s))
-    Assert(general_sep_of(sym) == ToSeq(sym))
     res = []  # type: List[int]
     i = 0
     while i < len(sym):
-        # invariants-start
         Invariant(Acc(list_pred(sym), 1 / 2))
         Invariant(Acc(list_pred(res)))
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
-        Invariant(general_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
-        # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
         i = i + 1
-    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
     return res
     # impl-end
 
@@ -220,7 +207,6 @@
 def numeric_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -257,7 +243,6 @@
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
         Invariant(numeric_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
         # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
```

Attack 4 — `atk_4_none_blank.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def general_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -207,7 +205,6 @@
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
         Invariant(general_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
         # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
@@ -220,7 +217,6 @@
 def numeric_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -230,7 +226,7 @@
     # post-conditions-end
     # impl-start
     if sym is None:
-        return [32, 92, 99, 100, 111, 116, 32]
+        return [32]
     s = ToSeq(sym)
     Assert(s == ToSeq(sym))
     if s == tok_dot():
@@ -257,7 +253,6 @@
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
         Invariant(numeric_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
         # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
```

Attack 5 — `atk_5_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def general_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -186,33 +184,20 @@
     if sym is None:
         return [32]
     s = ToSeq(sym)
-    Assert(s == ToSeq(sym))
     if s == tok_dot():
-        Assert(general_sep_of(sym) == token_sep(s))
         return [32, 92, 99, 100, 111, 116, 32]
     if s == tok_times():
-        Assert(general_sep_of(sym) == token_sep(s))
         return [32, 92, 116, 105, 109, 101, 115, 32]
     if s == tok_ldot():
-        Assert(general_sep_of(sym) == token_sep(s))
         return [32, 92, 44, 46, 92, 44, 32]
-    Assert(not is_known_token(s))
-    Assert(general_sep_of(sym) == ToSeq(sym))
     res = []  # type: List[int]
-    i = 0
+    i = 1
     while i < len(sym):
-        # invariants-start
         Invariant(Acc(list_pred(sym), 1 / 2))
         Invariant(Acc(list_pred(res)))
         Invariant(0 <= i and i <= len(sym))
-        Invariant(ToSeq(res) == ToSeq(sym).take(i))
-        Invariant(general_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
-        # invariants-end
-        Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
         i = i + 1
-    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
     return res
     # impl-end
 
@@ -220,7 +205,6 @@
 def numeric_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -257,7 +241,6 @@
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
         Invariant(numeric_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
         # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
```

Attack 6 — `atk_6_dot_always.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def general_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -207,7 +205,6 @@
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
         Invariant(general_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
         # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
@@ -220,7 +217,6 @@
 def numeric_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -232,36 +228,11 @@
     if sym is None:
         return [32, 92, 99, 100, 111, 116, 32]
     s = ToSeq(sym)
-    Assert(s == ToSeq(sym))
     if s == tok_dot():
-        Assert(numeric_sep_of(sym) == token_sep(s))
         return [32, 92, 99, 100, 111, 116, 32]
     if s == tok_times():
-        Assert(numeric_sep_of(sym) == token_sep(s))
         return [32, 92, 116, 105, 109, 101, 115, 32]
     if s == tok_ldot():
-        Assert(numeric_sep_of(sym) == token_sep(s))
         return [32, 92, 44, 46, 92, 44, 32]
-    Assert(not is_known_token(s))
-    t = trimmed(s)
-    if is_spacing_only(t):
-        Assert(numeric_sep_of(sym) == sep_dot())
-        return [32, 92, 99, 100, 111, 116, 32]
-    Assert(numeric_sep_of(sym) == ToSeq(sym))
-    res = []  # type: List[int]
-    i = 0
-    while i < len(sym):
-        # invariants-start
-        Invariant(Acc(list_pred(sym), 1 / 2))
-        Invariant(Acc(list_pred(res)))
-        Invariant(0 <= i and i <= len(sym))
-        Invariant(ToSeq(res) == ToSeq(sym).take(i))
-        Invariant(numeric_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
-        # invariants-end
-        Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
-        res = res + [sym[i]]
-        i = i + 1
-    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
-    return res
+    return [32, 92, 99, 100, 111, 116, 32]
     # impl-end
```

Attack 7 — `atk_7_trimmed_exploit.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -174,7 +173,6 @@
 def general_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -207,7 +205,6 @@
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
         Invariant(general_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
         # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
@@ -220,7 +217,6 @@
 def numeric_separator(sym: Optional[List[int]]) -> List[int]:
     # pre-conditions-start
     Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
@@ -232,36 +228,23 @@
     if sym is None:
         return [32, 92, 99, 100, 111, 116, 32]
     s = ToSeq(sym)
-    Assert(s == ToSeq(sym))
     if s == tok_dot():
-        Assert(numeric_sep_of(sym) == token_sep(s))
         return [32, 92, 99, 100, 111, 116, 32]
     if s == tok_times():
-        Assert(numeric_sep_of(sym) == token_sep(s))
         return [32, 92, 116, 105, 109, 101, 115, 32]
     if s == tok_ldot():
-        Assert(numeric_sep_of(sym) == token_sep(s))
         return [32, 92, 44, 46, 92, 44, 32]
-    Assert(not is_known_token(s))
-    t = trimmed(s)
-    if is_spacing_only(t):
-        Assert(numeric_sep_of(sym) == sep_dot())
-        return [32, 92, 99, 100, 111, 116, 32]
-    Assert(numeric_sep_of(sym) == ToSeq(sym))
+    if is_spacing_only(s):
+        return [32, 92, 99, 100, 111, 116, 32]
     res = []  # type: List[int]
     i = 0
     while i < len(sym):
-        # invariants-start
         Invariant(Acc(list_pred(sym), 1 / 2))
         Invariant(Acc(list_pred(res)))
         Invariant(0 <= i and i <= len(sym))
         Invariant(ToSeq(res) == ToSeq(sym).take(i))
-        Invariant(numeric_sep_of(sym) == ToSeq(sym))
-        Invariant(MustTerminate(len(sym) - i + 1))
-        # invariants-end
         Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
         res = res + [sym[i]]
         i = i + 1
-    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
     return res
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-13798.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A LaTeX printer accepts a multiplication-separator selector that may be the
  unset value (modelled here as ``None``) or a token string. Four selector
  tokens are *recognised* and map to a constant LaTeX separator each; the unset
  value behaves like the blank separator. From the selector the printer derives
  two separators:

    (1) the general separator used between non-numeric factors;
    (2) the separator used between two numeric factors.

  Desired behaviour:

    * For a recognised selector (the unset value, or one of the four tokens)
      BOTH derived separators are the constant LaTeX string associated with that
      selector — except that for the unset value the *numeric* separator is the
      one associated with the centred-dot token (numbers are never juxtaposed
      with only a blank between them).

    * For an UNRECOGNISED selector token the general separator is the selector
      string verbatim (the caller's own choice is honoured). The numeric
      separator is then the centred-dot string when the selector — with leading
      and trailing blanks removed — is one of the recognised "spacing only"
      tokens (the empty token, a single space, or one of the bare LaTeX spacing
      commands), and otherwise is again the selector string verbatim.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by ``PSeq[int]``. The unset
selector is modelled by ``None`` (an ``Optional`` carrier). The whitespace-
trimming callee used by the numeric branch is an unchanged library operation
and is axiomatised (``trimmed``); its soundness is checked against the real
callee out of band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def trimmed(s: PSeq[int]) -> PSeq[int]:
    """Whitespace-trim of a token (the unchanged library ``str.strip`` callee),
    restricted to the property the numeric branch relies on: a token that has
    no leading or trailing ASCII blank is returned unchanged. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(no_outer_blank(s), Result() == s))
# axioms-end

# pure-start
@Pure
def tok_ldot() -> PSeq[int]:
    # "ldot"
    return PSeq(108, 100, 111, 116)

@Pure
def tok_dot() -> PSeq[int]:
    # "dot"
    return PSeq(100, 111, 116)

@Pure
def tok_times() -> PSeq[int]:
    # "times"
    return PSeq(116, 105, 109, 101, 115)

@Pure
def sep_blank() -> PSeq[int]:
    # " "  (separator for the unset selector)
    return PSeq(32)

@Pure
def sep_ldot() -> PSeq[int]:
    # r" \,.\, "
    return PSeq(32, 92, 44, 46, 92, 44, 32)

@Pure
def sep_dot() -> PSeq[int]:
    # r" \cdot "  (the centred-dot separator)
    return PSeq(32, 92, 99, 100, 111, 116, 32)

@Pure
def sep_times() -> PSeq[int]:
    # r" \times "
    return PSeq(32, 92, 116, 105, 109, 101, 115, 32)

@Pure
def is_known_token(s: PSeq[int]) -> bool:
    """A non-unset selector that is one of the four recognised tokens."""
    return s == tok_dot() or s == tok_times() or s == tok_ldot()

@Pure
def token_sep(s: PSeq[int]) -> PSeq[int]:
    """The constant LaTeX separator associated with a recognised non-unset
    token. (Only consulted under is_known_token(s).)"""
    if s == tok_dot():
        return sep_dot()
    if s == tok_times():
        return sep_times()
    return sep_ldot()

@Pure
def is_spacing_only(t: PSeq[int]) -> bool:
    """A trimmed token that consists solely of LaTeX spacing: the empty token,
    a single space, or a bare spacing command."""
    return (t == PSeq(0).take(0)            # ""
            or t == PSeq(32)                # " "
            or t == PSeq(92)                # "\\"
            or t == PSeq(92, 44)            # "\\,"
            or t == PSeq(92, 58)            # "\\:"
            or t == PSeq(92, 59)            # "\\;"
            or t == PSeq(92, 113, 117, 97, 100))   # "\\quad"

@Pure
def is_visible_ascii(c: int) -> bool:
    """A printable ASCII code point other than the space (33..126). No code
    point trimmed by the library whitespace-trim falls in this range, so a token
    bounded by such code points is returned unchanged by the trim."""
    return 33 <= c and c <= 126

@Pure
def no_outer_blank(s: PSeq[int]) -> bool:
    """A token the whitespace-trim leaves unchanged: empty, or bounded on both
    ends by a printable non-space ASCII code point (conservatively excludes
    every code point the trim could strip)."""
    return (len(s) == 0) or (is_visible_ascii(s[0])
                             and is_visible_ascii(s[len(s) - 1]))

@Pure
def general_sep_of(sym: Optional[List[int]]) -> PSeq[int]:
    """Desired general separator: blank for the unset selector, the constant
    separator for a recognised token, the selector verbatim otherwise."""
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 4)))
    if sym is None:
        return sep_blank()
    if is_known_token(ToSeq(sym)):
        return token_sep(ToSeq(sym))
    return ToSeq(sym)

@Pure
def numeric_sep_of(sym: Optional[List[int]]) -> PSeq[int]:
    """Desired numeric separator: centred dot for the unset selector, the
    constant separator for a recognised token, otherwise centred dot when the trimmed
    selector is spacing-only and the selector verbatim when it is not."""
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 4)))
    if sym is None:
        return sep_dot()
    if is_known_token(ToSeq(sym)):
        return token_sep(ToSeq(sym))
    if is_spacing_only(trimmed(ToSeq(sym))):
        return sep_dot()
    return ToSeq(sym)
# pure-end

def general_separator(sym: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The general separator is exactly the desired derivation of the selector.
    Ensures(ToSeq(Result()) == general_sep_of(sym))
    # post-conditions-end
    # impl-start
    if sym is None:
        return [32]
    s = ToSeq(sym)
    Assert(s == ToSeq(sym))
    if s == tok_dot():
        Assert(general_sep_of(sym) == token_sep(s))
        return [32, 92, 99, 100, 111, 116, 32]
    if s == tok_times():
        Assert(general_sep_of(sym) == token_sep(s))
        return [32, 92, 116, 105, 109, 101, 115, 32]
    if s == tok_ldot():
        Assert(general_sep_of(sym) == token_sep(s))
        return [32, 92, 44, 46, 92, 44, 32]
    Assert(not is_known_token(s))
    Assert(general_sep_of(sym) == ToSeq(sym))
    res = []  # type: List[int]
    i = 0
    while i < len(sym):
        # invariants-start
        Invariant(Acc(list_pred(sym), 1 / 2))
        Invariant(Acc(list_pred(res)))
        Invariant(0 <= i and i <= len(sym))
        Invariant(ToSeq(res) == ToSeq(sym).take(i))
        Invariant(general_sep_of(sym) == ToSeq(sym))
        # invariants-end
        Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
        res = res + [sym[i]]
        i = i + 1
    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
    return res
    # impl-end

def numeric_separator(sym: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The numeric separator is exactly the desired derivation of the selector.
    Ensures(ToSeq(Result()) == numeric_sep_of(sym))
    # post-conditions-end
    # impl-start
    if sym is None:
        return [32, 92, 99, 100, 111, 116, 32]
    s = ToSeq(sym)
    Assert(s == ToSeq(sym))
    if s == tok_dot():
        Assert(numeric_sep_of(sym) == token_sep(s))
        return [32, 92, 99, 100, 111, 116, 32]
    if s == tok_times():
        Assert(numeric_sep_of(sym) == token_sep(s))
        return [32, 92, 116, 105, 109, 101, 115, 32]
    if s == tok_ldot():
        Assert(numeric_sep_of(sym) == token_sep(s))
        return [32, 92, 44, 46, 92, 44, 32]
    Assert(not is_known_token(s))
    t = trimmed(s)
    if is_spacing_only(t):
        Assert(numeric_sep_of(sym) == sep_dot())
        return [32, 92, 99, 100, 111, 116, 32]
    Assert(numeric_sep_of(sym) == ToSeq(sym))
    res = []  # type: List[int]
    i = 0
    while i < len(sym):
        # invariants-start
        Invariant(Acc(list_pred(sym), 1 / 2))
        Invariant(Acc(list_pred(res)))
        Invariant(0 <= i and i <= len(sym))
        Invariant(ToSeq(res) == ToSeq(sym).take(i))
        Invariant(numeric_sep_of(sym) == ToSeq(sym))
        # invariants-end
        Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
        res = res + [sym[i]]
        i = i + 1
    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL (all run from project root with SBU_BENCHMARK_DIR=benchmark-verified, PY=python; nagini env swebench-nagini-verifier). Attacks verified in parallel batches of 3 (each spawns JVM+Z3).

SPEC SHAPE: Both functions carry a MAXIMALLY-TIGHT postcondition pinning output exactly to the frozen pure oracle: general_separator has Ensures(ToSeq(Result()) == general_sep_of(sym)); numeric_separator has Ensures(ToSeq(Result()) == numeric_sep_of(sym)). Any same-spec impl that verifies is therefore behaviorally equal to the pure derivations general_sep_of/numeric_sep_of on EVERY input. There is no functional freedom the verifier would let slip, so no verifying wrong impl can exist -> no faithful patch to resolve-run. I falsified this claim with 7 distinct wrong impls; all were rejected.

POSITIVE CONTROL: pos_control.py = model.py verbatim. `python -m swebench_unified.adversary verify nagini sympy__sympy-13798 .../pos_control.py` => VERIFIED in 14.5s, EXIT=0.

ATTACKS (each edits ONLY impl region(s); axioms/@Pure/Requires/Ensures byte-identical; same-spec confirmed). Command for each: `python -m swebench_unified.adversary weakness nagini sympy__sympy-13798 <path>`: atk_1_partial_domain.py (PREPATCH BUG re-encoded: general fall-through returns blank [32] for an unrecognised token instead of verbatim) -> EXIT=2, 'attack does not verify' (spec rejected).

Reproduces the prepatch KeyError/unhonoured-selector defect. atk_2_boundary_drop_spacing.py (numeric drops the is_spacing_only->dot branch, returns verbatim for all unrecognised) -> EXIT=2, does not verify. atk_3_ctrlflow_swap_seps.py (control-flow-effect: general swaps the tok_times<->tok_ldot separator literals) -> EXIT=2, does not verify. atk_4_none_blank.py (numeric None-branch returns blank [32] instead of sep_dot()) -> EXIT=2, does not verify. atk_5_offbyone.py (general fall-through loop starts i=1, drops sym[0]) -> EXIT=2, does not verify. atk_6_dot_always.py (ungrounded-oracle echo: numeric returns sep_dot() for EVERY unrecognised token, even non-spacing like '*') -> EXIT=2, does not verify. atk_7_trimmed_exploit.py (targets the A-reference: branches on is_spacing_only(s) RAW instead of is_spacing_only(trimmed(s))) -> same-spec EXIT=0, weakness EXIT=2 does not verify. Confirms the numeric postcondition genuinely pins the trimmed branch even though the proof does not consume the trimmed Ensures (functional-congruence claim is real, not a hole).

REFINEMENT.md A-LEG AUDIT: The only non-R/I leg is B3 `trimmed` <-> `str.strip()` (A-reference), bound by mapping.md §3.1 to the unchanged builtin str.strip() called post-patch inside the second except KeyError at sympy/printing/latex.py. G-AX executable check: `python .../axiom_check.py` => 'G-AX OK ... sound on 192 boundary + 80000 fuzz inputs; thin-space selector \, confirmed spacing-only', EXIT=0. The axiom's sole Ensures (no_outer_blank(s) => s.strip()==s) never over-claims against the REAL str.strip, and the discriminating fact '\,'.strip()=='\,' is pinned. Correspondence to the real callee holds. §C 'no kind-3' confirmed against model.py: the changed try/except logic is modeled DEEPLY (general_sep_of/numeric_sep_of + matching impl loops), not axiomatized; only the unchanged str.strip is an axiom, and it is A-reference (not A-consumed) — falsification of the not-consumed claim via atk_7 shows the postcondition still binds the branch.

VERDICT: SOUND. 7 same-spec wrong impls (incl. re-encoded prepatch bug + partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, off-by-one, and A-reference/trimmed-exploit classes) were run through `adversary weakness`; NONE is a CANDIDATE (none both shares the spec AND verifies). Positive control verifies; G-AX sound. No verifying wrong impl => no materialized patch to resolve (patches={}). verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_partial_domain.py`, `atk_2_boundary_drop_spacing.py`, `atk_3_ctrlflow_swap_seps.py`, `atk_4_none_blank.py`, `atk_5_offbyone.py`, `atk_6_dot_always.py`, `atk_7_trimmed_exploit.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_partial_domain.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_boundary_drop_spacing.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_ctrlflow_swap_seps.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_none_blank.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_offbyone.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_dot_always.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_trimmed_exploit.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-13798.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A LaTeX printer accepts a multiplication-separator selector that may be the
  unset value (modelled here as ``None``) or a token string. Four selector
  tokens are *recognised* and map to a constant LaTeX separator each; the unset
  value behaves like the blank separator. From the selector the printer derives
  two separators:

    (1) the general separator used between non-numeric factors;
    (2) the separator used between two numeric factors.

  Desired behaviour:

    * For a recognised selector (the unset value, or one of the four tokens)
      BOTH derived separators are the constant LaTeX string associated with that
      selector — except that for the unset value the *numeric* separator is the
      one associated with the centred-dot token (numbers are never juxtaposed
      with only a blank between them).

    * For an UNRECOGNISED selector token the general separator is the selector
      string verbatim (the caller's own choice is honoured). The numeric
      separator is then the centred-dot string when the selector — with leading
      and trailing blanks removed — is one of the recognised "spacing only"
      tokens (the empty token, a single space, or one of the bare LaTeX spacing
      commands), and otherwise is again the selector string verbatim.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by ``PSeq[int]``. The unset
selector is modelled by ``None`` (an ``Optional`` carrier). The whitespace-
trimming callee used by the numeric branch is an unchanged library operation
and is axiomatised (``trimmed``); its soundness is checked against the real
callee out of band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def trimmed(s: PSeq[int]) -> PSeq[int]:
    """Whitespace-trim of a token (the unchanged library ``str.strip`` callee),
    restricted to the property the numeric branch relies on: a token that has
    no leading or trailing ASCII blank is returned unchanged. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(no_outer_blank(s), Result() == s))
# axioms-end

# pure-start
@Pure
def tok_ldot() -> PSeq[int]:
    # "ldot"
    return PSeq(108, 100, 111, 116)

@Pure
def tok_dot() -> PSeq[int]:
    # "dot"
    return PSeq(100, 111, 116)

@Pure
def tok_times() -> PSeq[int]:
    # "times"
    return PSeq(116, 105, 109, 101, 115)

@Pure
def sep_blank() -> PSeq[int]:
    # " "  (separator for the unset selector)
    return PSeq(32)

@Pure
def sep_ldot() -> PSeq[int]:
    # r" \,.\, "
    return PSeq(32, 92, 44, 46, 92, 44, 32)

@Pure
def sep_dot() -> PSeq[int]:
    # r" \cdot "  (the centred-dot separator)
    return PSeq(32, 92, 99, 100, 111, 116, 32)

@Pure
def sep_times() -> PSeq[int]:
    # r" \times "
    return PSeq(32, 92, 116, 105, 109, 101, 115, 32)

@Pure
def is_known_token(s: PSeq[int]) -> bool:
    """A non-unset selector that is one of the four recognised tokens."""
    return s == tok_dot() or s == tok_times() or s == tok_ldot()

@Pure
def token_sep(s: PSeq[int]) -> PSeq[int]:
    """The constant LaTeX separator associated with a recognised non-unset
    token. (Only consulted under is_known_token(s).)"""
    if s == tok_dot():
        return sep_dot()
    if s == tok_times():
        return sep_times()
    return sep_ldot()

@Pure
def is_spacing_only(t: PSeq[int]) -> bool:
    """A trimmed token that consists solely of LaTeX spacing: the empty token,
    a single space, or a bare spacing command."""
    return (t == PSeq(0).take(0)            # ""
            or t == PSeq(32)                # " "
            or t == PSeq(92)                # "\\"
            or t == PSeq(92, 44)            # "\\,"
            or t == PSeq(92, 58)            # "\\:"
            or t == PSeq(92, 59)            # "\\;"
            or t == PSeq(92, 113, 117, 97, 100))   # "\\quad"

@Pure
def is_visible_ascii(c: int) -> bool:
    """A printable ASCII code point other than the space (33..126). No code
    point trimmed by the library whitespace-trim falls in this range, so a token
    bounded by such code points is returned unchanged by the trim."""
    return 33 <= c and c <= 126

@Pure
def no_outer_blank(s: PSeq[int]) -> bool:
    """A token the whitespace-trim leaves unchanged: empty, or bounded on both
    ends by a printable non-space ASCII code point (conservatively excludes
    every code point the trim could strip)."""
    return (len(s) == 0) or (is_visible_ascii(s[0])
                             and is_visible_ascii(s[len(s) - 1]))

@Pure
def general_sep_of(sym: Optional[List[int]]) -> PSeq[int]:
    """Desired general separator: blank for the unset selector, the constant
    separator for a recognised token, the selector verbatim otherwise."""
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 4)))
    if sym is None:
        return sep_blank()
    if is_known_token(ToSeq(sym)):
        return token_sep(ToSeq(sym))
    return ToSeq(sym)

@Pure
def numeric_sep_of(sym: Optional[List[int]]) -> PSeq[int]:
    """Desired numeric separator: centred dot for the unset selector, the
    constant separator for a recognised token, otherwise centred dot when the trimmed
    selector is spacing-only and the selector verbatim when it is not."""
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 4)))
    if sym is None:
        return sep_dot()
    if is_known_token(ToSeq(sym)):
        return token_sep(ToSeq(sym))
    if is_spacing_only(trimmed(ToSeq(sym))):
        return sep_dot()
    return ToSeq(sym)
# pure-end

def general_separator(sym: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The general separator is exactly the desired derivation of the selector.
    Ensures(ToSeq(Result()) == general_sep_of(sym))
    # post-conditions-end
    # impl-start
    if sym is None:
        return [32]
    s = ToSeq(sym)
    Assert(s == ToSeq(sym))
    if s == tok_dot():
        Assert(general_sep_of(sym) == token_sep(s))
        return [32, 92, 99, 100, 111, 116, 32]
    if s == tok_times():
        Assert(general_sep_of(sym) == token_sep(s))
        return [32, 92, 116, 105, 109, 101, 115, 32]
    if s == tok_ldot():
        Assert(general_sep_of(sym) == token_sep(s))
        return [32, 92, 44, 46, 92, 44, 32]
    Assert(not is_known_token(s))
    Assert(general_sep_of(sym) == ToSeq(sym))
    res = []  # type: List[int]
    i = 0
    while i < len(sym):
        # invariants-start
        Invariant(Acc(list_pred(sym), 1 / 2))
        Invariant(Acc(list_pred(res)))
        Invariant(0 <= i and i <= len(sym))
        Invariant(ToSeq(res) == ToSeq(sym).take(i))
        Invariant(general_sep_of(sym) == ToSeq(sym))
        # invariants-end
        Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
        res = res + [sym[i]]
        i = i + 1
    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
    return res
    # impl-end

def numeric_separator(sym: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(sym is not None, Acc(list_pred(sym), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The numeric separator is exactly the desired derivation of the selector.
    Ensures(ToSeq(Result()) == numeric_sep_of(sym))
    # post-conditions-end
    # impl-start
    if sym is None:
        return [32, 92, 99, 100, 111, 116, 32]
    s = ToSeq(sym)
    Assert(s == ToSeq(sym))
    if s == tok_dot():
        Assert(numeric_sep_of(sym) == token_sep(s))
        return [32, 92, 99, 100, 111, 116, 32]
    if s == tok_times():
        Assert(numeric_sep_of(sym) == token_sep(s))
        return [32, 92, 116, 105, 109, 101, 115, 32]
    if s == tok_ldot():
        Assert(numeric_sep_of(sym) == token_sep(s))
        return [32, 92, 44, 46, 92, 44, 32]
    Assert(not is_known_token(s))
    t = trimmed(s)
    if is_spacing_only(t):
        Assert(numeric_sep_of(sym) == sep_dot())
        return [32, 92, 99, 100, 111, 116, 32]
    Assert(numeric_sep_of(sym) == ToSeq(sym))
    res = []  # type: List[int]
    i = 0
    while i < len(sym):
        # invariants-start
        Invariant(Acc(list_pred(sym), 1 / 2))
        Invariant(Acc(list_pred(res)))
        Invariant(0 <= i and i <= len(sym))
        Invariant(ToSeq(res) == ToSeq(sym).take(i))
        Invariant(numeric_sep_of(sym) == ToSeq(sym))
        # invariants-end
        Assert(ToSeq(sym).take(i + 1) == ToSeq(sym).take(i) + PSeq(sym[i]))
        res = res + [sym[i]]
        i = i + 1
    Assert(ToSeq(sym).take(len(sym)) == ToSeq(sym))
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL (all run from project root with SBU_BENCHMARK_DIR=benchmark-verified, PY=python; nagini env swebench-nagini-verifier). Attacks verified in parallel batches of 3 (each spawns JVM+Z3).

SPEC SHAPE: Both functions carry a MAXIMALLY-TIGHT postcondition pinning output exactly to the frozen pure oracle: general_separator has Ensures(ToSeq(Result()) == general_sep_of(sym)); numeric_separator has Ensures(ToSeq(Result()) == numeric_sep_of(sym)). Any same-spec impl that verifies is therefore behaviorally equal to the pure derivations general_sep_of/numeric_sep_of on EVERY input. There is no functional freedom the verifier would let slip, so no verifying wrong impl can exist -> no faithful patch to resolve-run. I falsified this claim with 7 distinct wrong impls; all were rejected.

POSITIVE CONTROL: pos_control.py = model.py verbatim. `python -m swebench_unified.adversary verify nagini sympy__sympy-13798 .../pos_control.py` => VERIFIED in 14.5s, EXIT=0.

ATTACKS (each edits ONLY impl region(s); axioms/@Pure/Requires/Ensures byte-identical; same-spec confirmed). Command for each: `python -m swebench_unified.adversary weakness nagini sympy__sympy-13798 <path>`: atk_1_partial_domain.py (PREPATCH BUG re-encoded: general fall-through returns blank [32] for an unrecognised token instead of verbatim) -> EXIT=2, 'attack does not verify' (spec rejected).

Reproduces the prepatch KeyError/unhonoured-selector defect. atk_2_boundary_drop_spacing.py (numeric drops the is_spacing_only->dot branch, returns verbatim for all unrecognised) -> EXIT=2, does not verify. atk_3_ctrlflow_swap_seps.py (control-flow-effect: general swaps the tok_times<->tok_ldot separator literals) -> EXIT=2, does not verify. atk_4_none_blank.py (numeric None-branch returns blank [32] instead of sep_dot()) -> EXIT=2, does not verify. atk_5_offbyone.py (general fall-through loop starts i=1, drops sym[0]) -> EXIT=2, does not verify. atk_6_dot_always.py (ungrounded-oracle echo: numeric returns sep_dot() for EVERY unrecognised token, even non-spacing like '*') -> EXIT=2, does not verify. atk_7_trimmed_exploit.py (targets the A-reference: branches on is_spacing_only(s) RAW instead of is_spacing_only(trimmed(s))) -> same-spec EXIT=0, weakness EXIT=2 does not verify. Confirms the numeric postcondition genuinely pins the trimmed branch even though the proof does not consume the trimmed Ensures (functional-congruence claim is real, not a hole).

REFINEMENT.md A-LEG AUDIT: The only non-R/I leg is B3 `trimmed` <-> `str.strip()` (A-reference), bound by mapping.md §3.1 to the unchanged builtin str.strip() called post-patch inside the second except KeyError at sympy/printing/latex.py. G-AX executable check: `python .../axiom_check.py` => 'G-AX OK ... sound on 192 boundary + 80000 fuzz inputs; thin-space selector \, confirmed spacing-only', EXIT=0. The axiom's sole Ensures (no_outer_blank(s) => s.strip()==s) never over-claims against the REAL str.strip, and the discriminating fact '\,'.strip()=='\,' is pinned. Correspondence to the real callee holds. §C 'no kind-3' confirmed against model.py: the changed try/except logic is modeled DEEPLY (general_sep_of/numeric_sep_of + matching impl loops), not axiomatized; only the unchanged str.strip is an axiom, and it is A-reference (not A-consumed) — falsification of the not-consumed claim via atk_7 shows the postcondition still binds the branch.

VERDICT: SOUND. 7 same-spec wrong impls (incl. re-encoded prepatch bug + partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, off-by-one, and A-reference/trimmed-exploit classes) were run through `adversary weakness`; NONE is a CANDIDATE (none both shares the spec AND verifies). Positive control verifies; G-AX sound. No verifying wrong impl => no materialized patch to resolve (patches={}). verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec faithfully models the patched LatexPrinter.__init__ separator derivation. Verified three independent ways: model.py verifies in Nagini (13.9s), so impl == pure derivations general_sep_of/numeric_sep_of exactly; the bundle's differential conformance_check.py, run against the REAL patched repo worktree at base_commit 7121bdf (patch applied), passes on 100,000 inputs (369 boundary + 820 exhaustive len<=3 + 98,811 fuzz) with 0 disagreements between the contract-stripped shadow impl (calling real str.strip) and LatexPrinter._settings['mul_symbol_latex'/'mul_symbol_latex_numbers']; my own probe reimplementing the pure spec over strings vs. the real repo across 383 adversarial edge inputs (astral-plane and exotic Unicode whitespace \x1c-\x1f, \xa0, 
, 　, ﻿, whitespace-padded near-tokens, recognised tokens, spacing-only tokens) found 0 divergences and no in-domain oracle raise. The general separator is verbatim-on-unrecognised (matches except KeyError path); the numeric separator maps None->\cdot (mul_symbol_table[None or 'dot']), recognised tokens to their table value, spacing-only-after-strip to \cdot, else verbatim — all matching the gold try/except blocks. The trimmed axiom is a sound over-approximation of str.strip (G-AX) and is not proof-consumed; numeric postcondition discharges by functional congruence. No input where the modeled functions disagree with the real callee was found; spec is neither too strong nor drifted.

, 　, ﻿, whitespace-padded near-tokens, recognised tokens, spacing-only tokens) found 0 divergences and no in-domain oracle raise. The general separator is verbatim-on-unrecognised (matches except KeyError path); the numeric separator maps None->\cdot (mul_symbol_table[None or 'dot']), recognised tokens to their table value, spacing-only-after-strip to \cdot, else verbatim — all matching the gold try/except blocks. The trimmed axiom is a sound over-approximation of str.strip (G-AX) and is not proof-consumed; numeric postcondition discharges by functional congruence. No input where the modeled functions disagree with the real callee was found; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged leakage of the GOLD EDIT against the spec view (spec_view over model.py) relative to the public problem_statement only (not hints_text). Ran the mechanical G-LEAK screen (swebench_unified.leakage.screen, NaginiBackend, frozen problem_statement + gold patch): PASSED, zero hard failures. Independent review of the edit-localization signals:

(1) File path leak: NONE. The patched repo file 'sympy/printing/latex.py' and its dotted module path never appear in the spec view.
(2) Patched repo symbols: NONE named. The gold hunk lives in LatexPrinter.__init__ and keys on the dict 'mul_symbol_table'; neither 'LatexPrinter', '__init__', nor 'mul_symbol_table' appears in the spec view. The only library callee referenced is str.strip (a builtin, correctly excluded from patch-symbol collision), surfaced only via the abstract axiom name 'trimmed'. Modeled functions general_separator/numeric_separator are model-invented names, not repo symbols.
(3) Diff mechanics: NONE. No diff markers; no gold-patch line reproduced. Critically, the actual MECHANISM of the gold change (wrapping two unguarded dict lookups in try/except KeyError, and the seven-element membership list) is nowhere reflected in the spec view — the spec is purely declarative over general_sep_of/numeric_sep_of.
(4) Bug/fix narration: NONE. Docstrings state behaviour 'as desired behaviour, not as an edit'; no pre-patch/regression/fix wording in the spec-view comments.

The spec view does fully specify the target behaviour (unrecognised selector honoured verbatim for the general separator; spacing-only-after-trim selectors mapped to the centred dot for numbers) — which is richer than the problem_statement's request to 'allow an arbitrary mul_symbol such as \,'. But that is the legitimate correctness oracle a twin-artifact spec must carry; G-PANEL-3/G-LEAK target leakage of the EDIT (file, repo symbols, diff structure, edit narration), none of which is present. The gold's implementation strategy (try/except defaulting) is not recoverable from the view. No RELAXED_LEAKAGE.md deferral was needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
