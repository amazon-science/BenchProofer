# P2 adversarial audit — sphinx-doc__sphinx-8035

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -93,7 +92,6 @@
     # option-state tag, 0/1/2 as documented above.
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(0 <= mode and mode <= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -120,15 +118,8 @@
                     Result() is False))
     # post-conditions-end
     # impl-start
-    if not (has_doc or undoc_members):
-        return False
-    if mode == 0:
-        return False
-    if mode == 1:
-        return True
-    if filtered_inherited:
-        return False
-    return membername in ToSeq(names)
+    option_given = mode != 0
+    return option_given and (has_doc or undoc_members)
     # impl-end
 
 
@@ -151,7 +142,6 @@
     # list of names. Both lists are read only here (fractional permission).
     Requires(Acc(list_pred(members), 1 / 2))
     Requires(Acc(list_pred(extra), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(members), 1 / 2))
@@ -182,7 +172,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(members))
             Invariant(ToSeq(result) == ToSeq(members).take(i))
-            Invariant(MustTerminate(len(members) - i + 1))
             # invariants-end
             result = result + [members[i]]
             i = i + 1
@@ -196,7 +185,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(members))
         Invariant(ToSeq(result) == ToSeq(members).take(i))
-        Invariant(MustTerminate(len(members) - i + 1))
         # invariants-end
         result = result + [members[i]]
         i = i + 1
@@ -214,7 +202,6 @@
                                                  members[k] in ToSeq(result)))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                  extra[k] in ToSeq(result)))))
-        Invariant(MustTerminate(len(extra) - j + 1))
         # invariants-end
         m = extra[j]
         present = m in ToSeq(result)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -93,7 +92,6 @@
     # option-state tag, 0/1/2 as documented above.
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(0 <= mode and mode <= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -128,7 +126,7 @@
         return True
     if filtered_inherited:
         return False
-    return membername in ToSeq(names)
+    return True
     # impl-end
 
 
@@ -151,7 +149,6 @@
     # list of names. Both lists are read only here (fractional permission).
     Requires(Acc(list_pred(members), 1 / 2))
     Requires(Acc(list_pred(extra), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(members), 1 / 2))
@@ -182,7 +179,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(members))
             Invariant(ToSeq(result) == ToSeq(members).take(i))
-            Invariant(MustTerminate(len(members) - i + 1))
             # invariants-end
             result = result + [members[i]]
             i = i + 1
@@ -196,7 +192,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(members))
         Invariant(ToSeq(result) == ToSeq(members).take(i))
-        Invariant(MustTerminate(len(members) - i + 1))
         # invariants-end
         result = result + [members[i]]
         i = i + 1
@@ -214,7 +209,6 @@
                                                  members[k] in ToSeq(result)))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                  extra[k] in ToSeq(result)))))
-        Invariant(MustTerminate(len(extra) - j + 1))
         # invariants-end
         m = extra[j]
         present = m in ToSeq(result)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -93,7 +92,6 @@
     # option-state tag, 0/1/2 as documented above.
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(0 <= mode and mode <= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -128,7 +126,7 @@
         return True
     if filtered_inherited:
         return False
-    return membername in ToSeq(names)
+    return not (membername in ToSeq(names))
     # impl-end
 
 
@@ -151,7 +149,6 @@
     # list of names. Both lists are read only here (fractional permission).
     Requires(Acc(list_pred(members), 1 / 2))
     Requires(Acc(list_pred(extra), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(members), 1 / 2))
@@ -182,7 +179,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(members))
             Invariant(ToSeq(result) == ToSeq(members).take(i))
-            Invariant(MustTerminate(len(members) - i + 1))
             # invariants-end
             result = result + [members[i]]
             i = i + 1
@@ -196,7 +192,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(members))
         Invariant(ToSeq(result) == ToSeq(members).take(i))
-        Invariant(MustTerminate(len(members) - i + 1))
         # invariants-end
         result = result + [members[i]]
         i = i + 1
@@ -214,7 +209,6 @@
                                                  members[k] in ToSeq(result)))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                  extra[k] in ToSeq(result)))))
-        Invariant(MustTerminate(len(extra) - j + 1))
         # invariants-end
         m = extra[j]
         present = m in ToSeq(result)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -93,7 +92,6 @@
     # option-state tag, 0/1/2 as documented above.
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(0 <= mode and mode <= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -126,8 +124,6 @@
         return False
     if mode == 1:
         return True
-    if filtered_inherited:
-        return False
     return membername in ToSeq(names)
     # impl-end
 
@@ -151,7 +147,6 @@
     # list of names. Both lists are read only here (fractional permission).
     Requires(Acc(list_pred(members), 1 / 2))
     Requires(Acc(list_pred(extra), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(members), 1 / 2))
@@ -182,7 +177,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(members))
             Invariant(ToSeq(result) == ToSeq(members).take(i))
-            Invariant(MustTerminate(len(members) - i + 1))
             # invariants-end
             result = result + [members[i]]
             i = i + 1
@@ -196,7 +190,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(members))
         Invariant(ToSeq(result) == ToSeq(members).take(i))
-        Invariant(MustTerminate(len(members) - i + 1))
         # invariants-end
         result = result + [members[i]]
         i = i + 1
@@ -214,7 +207,6 @@
                                                  members[k] in ToSeq(result)))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                  extra[k] in ToSeq(result)))))
-        Invariant(MustTerminate(len(extra) - j + 1))
         # invariants-end
         m = extra[j]
         present = m in ToSeq(result)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -93,7 +92,6 @@
     # option-state tag, 0/1/2 as documented above.
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(0 <= mode and mode <= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -124,10 +122,10 @@
         return False
     if mode == 0:
         return False
+    if filtered_inherited:
+        return False
     if mode == 1:
         return True
-    if filtered_inherited:
-        return False
     return membername in ToSeq(names)
     # impl-end
 
@@ -151,7 +149,6 @@
     # list of names. Both lists are read only here (fractional permission).
     Requires(Acc(list_pred(members), 1 / 2))
     Requires(Acc(list_pred(extra), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(members), 1 / 2))
@@ -182,7 +179,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(members))
             Invariant(ToSeq(result) == ToSeq(members).take(i))
-            Invariant(MustTerminate(len(members) - i + 1))
             # invariants-end
             result = result + [members[i]]
             i = i + 1
@@ -196,7 +192,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(members))
         Invariant(ToSeq(result) == ToSeq(members).take(i))
-        Invariant(MustTerminate(len(members) - i + 1))
         # invariants-end
         result = result + [members[i]]
         i = i + 1
@@ -214,7 +209,6 @@
                                                  members[k] in ToSeq(result)))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                  extra[k] in ToSeq(result)))))
-        Invariant(MustTerminate(len(extra) - j + 1))
         # invariants-end
         m = extra[j]
         present = m in ToSeq(result)
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -93,7 +92,6 @@
     # option-state tag, 0/1/2 as documented above.
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(0 <= mode and mode <= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -151,7 +149,6 @@
     # list of names. Both lists are read only here (fractional permission).
     Requires(Acc(list_pred(members), 1 / 2))
     Requires(Acc(list_pred(extra), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(members), 1 / 2))
@@ -177,13 +174,10 @@
         result = []  # type: List[int]
         i = 0
         while i < len(members):
-            # invariants-start
             Invariant(Acc(list_pred(members), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(members))
             Invariant(ToSeq(result) == ToSeq(members).take(i))
-            Invariant(MustTerminate(len(members) - i + 1))
-            # invariants-end
             result = result + [members[i]]
             i = i + 1
         Assert(ToSeq(members).take(len(members)) == ToSeq(members))
@@ -191,20 +185,16 @@
     result = []
     i = 0
     while i < len(members):
-        # invariants-start
         Invariant(Acc(list_pred(members), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(members))
         Invariant(ToSeq(result) == ToSeq(members).take(i))
-        Invariant(MustTerminate(len(members) - i + 1))
-        # invariants-end
         result = result + [members[i]]
         i = i + 1
     Assert(ToSeq(members).take(len(members)) == ToSeq(members))
     Assert(ToSeq(result) == ToSeq(members))
     j = 0
     while j < len(extra):
-        # invariants-start
         Invariant(Acc(list_pred(members), 1 / 2))
         Invariant(Acc(list_pred(extra), 1 / 2))
         Invariant(Acc(list_pred(result)))
@@ -214,12 +204,7 @@
                                                  members[k] in ToSeq(result)))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                  extra[k] in ToSeq(result)))))
-        Invariant(MustTerminate(len(extra) - j + 1))
-        # invariants-end
-        m = extra[j]
-        present = m in ToSeq(result)
-        if not present:
-            result = result + [m]
+        result = result + [extra[j]]
         Assert(extra[j] in ToSeq(result))
         j = j + 1
     return result
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -93,7 +92,6 @@
     # option-state tag, 0/1/2 as documented above.
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(0 <= mode and mode <= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -151,7 +149,6 @@
     # list of names. Both lists are read only here (fractional permission).
     Requires(Acc(list_pred(members), 1 / 2))
     Requires(Acc(list_pred(extra), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(members), 1 / 2))
@@ -177,13 +174,10 @@
         result = []  # type: List[int]
         i = 0
         while i < len(members):
-            # invariants-start
             Invariant(Acc(list_pred(members), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(members))
             Invariant(ToSeq(result) == ToSeq(members).take(i))
-            Invariant(MustTerminate(len(members) - i + 1))
-            # invariants-end
             result = result + [members[i]]
             i = i + 1
         Assert(ToSeq(members).take(len(members)) == ToSeq(members))
@@ -191,20 +185,16 @@
     result = []
     i = 0
     while i < len(members):
-        # invariants-start
         Invariant(Acc(list_pred(members), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(members))
         Invariant(ToSeq(result) == ToSeq(members).take(i))
-        Invariant(MustTerminate(len(members) - i + 1))
-        # invariants-end
         result = result + [members[i]]
         i = i + 1
     Assert(ToSeq(members).take(len(members)) == ToSeq(members))
     Assert(ToSeq(result) == ToSeq(members))
     j = 0
     while j < len(extra):
-        # invariants-start
         Invariant(Acc(list_pred(members), 1 / 2))
         Invariant(Acc(list_pred(extra), 1 / 2))
         Invariant(Acc(list_pred(result)))
@@ -214,13 +204,12 @@
                                                  members[k] in ToSeq(result)))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                  extra[k] in ToSeq(result)))))
-        Invariant(MustTerminate(len(extra) - j + 1))
-        # invariants-end
         m = extra[j]
         present = m in ToSeq(result)
         if not present:
             result = result + [m]
         Assert(extra[j] in ToSeq(result))
         j = j + 1
+    result = result + [999999]
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -93,7 +92,6 @@
     # option-state tag, 0/1/2 as documented above.
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(0 <= mode and mode <= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -151,7 +149,6 @@
     # list of names. Both lists are read only here (fractional permission).
     Requires(Acc(list_pred(members), 1 / 2))
     Requires(Acc(list_pred(extra), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(members), 1 / 2))
@@ -177,34 +174,28 @@
         result = []  # type: List[int]
         i = 0
         while i < len(members):
-            # invariants-start
             Invariant(Acc(list_pred(members), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(members))
             Invariant(ToSeq(result) == ToSeq(members).take(i))
-            Invariant(MustTerminate(len(members) - i + 1))
-            # invariants-end
             result = result + [members[i]]
             i = i + 1
-        Assert(ToSeq(members).take(len(members)) == ToSeq(members))
+        if len(extra) > 0:
+            result = result + [extra[0]]
         return result
     result = []
     i = 0
     while i < len(members):
-        # invariants-start
         Invariant(Acc(list_pred(members), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(members))
         Invariant(ToSeq(result) == ToSeq(members).take(i))
-        Invariant(MustTerminate(len(members) - i + 1))
-        # invariants-end
         result = result + [members[i]]
         i = i + 1
     Assert(ToSeq(members).take(len(members)) == ToSeq(members))
     Assert(ToSeq(result) == ToSeq(members))
     j = 0
     while j < len(extra):
-        # invariants-start
         Invariant(Acc(list_pred(members), 1 / 2))
         Invariant(Acc(list_pred(extra), 1 / 2))
         Invariant(Acc(list_pred(result)))
@@ -214,8 +205,6 @@
                                                  members[k] in ToSeq(result)))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                  extra[k] in ToSeq(result)))))
-        Invariant(MustTerminate(len(extra) - j + 1))
-        # invariants-end
         m = extra[j]
         present = m in ToSeq(result)
         if not present:
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8035.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an automatic-documentation pass collects the members of an object and
  must decide whether to keep a member that is considered private, the option
  that controls private members can be in one of three states, and the keep
  decision depends on which state it is in:

    (a) the option was NOT supplied -> no private member is kept;
    (b) the option was supplied with NO argument (the "all-private" form)
        -> a private member is kept exactly when it is documentable in the
        usual sense (it has documentation, or undocumented members are being
        kept);
    (c) the option was supplied with an explicit list of names -> a private
        member is kept exactly when its OWN name appears in that list, it is
        otherwise documentable, and it is not an inherited member that is being
        filtered out. A private member whose name is NOT in the list is
        dropped, even though OTHER names are listed.

  The crucial point distinguishing (c) from a coarse on/off control: supplying
  a non-empty list of names does NOT keep every private member; it keeps
  exactly the named ones. An undocumentable private member is never kept in any
  state.

  A second behaviour is the merge of the various ``*-members`` selectors into
  the explicit member list: when the principal member selector is the
  "all-members" form, the merge is a no-op; otherwise each name from each
  supplementary selector that is given as an explicit list (not the all-form)
  is appended to the member list if it is not already present, preserving order
  and avoiding duplicates.

Member names are modelled as ``int`` identity tokens; a list of names is a
``List[int]`` of such tokens (Nagini bans ``str`` indexing). The three option
states are encoded by an explicit ``mode`` tag (0 = absent, 1 = all-form,
2 = explicit list) carrying its list payload, which is the faithful refinement
of the ``None`` / sentinel-object / list trichotomy the real option uses.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms: the keep decision and the merge are pure boolean /
#  sequence logic over the abstract option tag, the name tokens and the
#  documentability flags, spelled out in full. There is no unchanged opaque
#  callee whose contract the proof consumes.)
# axioms-end


# pure-start
@Pure
def documentable(has_doc: bool, undoc_members: bool) -> bool:
    """A member is documentable in the usual sense when it carries
    documentation, or undocumented members are being retained."""
    return has_doc or undoc_members


@Pure
def keep_private(mode: int, names: PSeq[int], membername: int,
                 has_doc: bool, undoc_members: bool,
                 filtered_inherited: bool) -> bool:
    """The keep decision for a member that is considered private, as a pure
    function of the option's three states.

      mode 0 (absent)        -> never kept
      mode 1 (all-form)      -> kept iff documentable
      mode 2 (explicit list) -> kept iff documentable, not a filtered inherited
                                member, and this member's name is in the list

    The inherited-member filter applies only to the explicit-list state; the
    all-form keeps every documentable private member.
    """
    if not documentable(has_doc, undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    return (not filtered_inherited) and (membername in names)
# pure-end


def keep_private_member(mode: int, names: List[int], membername: int,
                        has_doc: bool, undoc_members: bool,
                        filtered_inherited: bool) -> bool:
    # pre-conditions-start
    # ``names`` (the explicit list payload of the option) is read only here:
    # fractional permission, returned unchanged (directive 5). ``mode`` is the
    # option-state tag, 0/1/2 as documented above.
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(0 <= mode and mode <= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    # The decision equals the pure three-state rule.
    Ensures(Result() == keep_private(mode, ToSeq(names), membername,
                                     has_doc, undoc_members, filtered_inherited))
    # An undocumentable member is never kept, in any option state.
    Ensures(Implies(not documentable(has_doc, undoc_members),
                    Result() is False))
    # Absent option: never kept.
    Ensures(Implies(mode == 0, Result() is False))
    # All-form: kept exactly when documentable (the inherited-member filter
    # does not apply to the all-form).
    Ensures(Implies(mode == 1,
                    Result() == documentable(has_doc, undoc_members)))
    # Explicit list: a documentable, non-filtered member is kept iff its OWN
    # name is in the list. This is the discriminating clause: a non-empty list
    # does NOT keep every private member, only the named ones.
    Ensures(Implies(mode == 2 and documentable(has_doc, undoc_members)
                    and not filtered_inherited,
                    Result() == (membername in ToSeq(names))))
    Ensures(Implies(mode == 2 and documentable(has_doc, undoc_members)
                    and not filtered_inherited and not (membername in ToSeq(names)),
                    Result() is False))
    # post-conditions-end
    # impl-start
    if not (has_doc or undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    if filtered_inherited:
        return False
    return membername in ToSeq(names)
    # impl-end


@Pure
def merged_at(orig: PSeq[int], extra: PSeq[int], i: int) -> bool:
    """Membership predicate for the merge result built from ``orig`` by
    appending the as-yet-unseen names of ``extra``: ``i`` indexes ``extra`` and
    the name is appended exactly when it is not already in ``orig`` and not in
    the already-processed prefix of ``extra``."""
    Requires(0 <= i and i < len(extra))
    return (not (extra[i] in orig)) and (not (extra[i] in extra.take(i)))


def merge_selector_names(members_is_all: bool, members: List[int],
                         extra: List[int]) -> List[int]:
    # pre-conditions-start
    # ``members`` is the principal member list being extended; ``members_is_all``
    # is True when the principal selector is the all-members form (so the merge
    # is a no-op). ``extra`` is one supplementary selector given as an explicit
    # list of names. Both lists are read only here (fractional permission).
    Requires(Acc(list_pred(members), 1 / 2))
    Requires(Acc(list_pred(extra), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(members), 1 / 2))
    Ensures(Acc(list_pred(extra), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # All-members form: the merge is a no-op, the member list is unchanged.
    Ensures(Implies(members_is_all, ToSeq(Result()) == ToSeq(members)))
    # Otherwise the result begins with the original member list (order kept) ...
    Ensures(Implies(not members_is_all,
                    ToSeq(Result()).take(len(members)) == ToSeq(members)))
    # ... and every original member is still present.
    Ensures(Implies(not members_is_all,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                   members[k] in ToSeq(Result()))))))
    # ... and every extra name is now present (it was appended if new, or was
    # already there) — the supplementary selector's names are all included.
    Ensures(Implies(not members_is_all,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(extra),
                                                   extra[k] in ToSeq(Result()))))))
    # post-conditions-end
    # impl-start
    if members_is_all:
        result = []  # type: List[int]
        i = 0
        while i < len(members):
            # invariants-start
            Invariant(Acc(list_pred(members), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(members))
            Invariant(ToSeq(result) == ToSeq(members).take(i))
            # invariants-end
            result = result + [members[i]]
            i = i + 1
        Assert(ToSeq(members).take(len(members)) == ToSeq(members))
        return result
    result = []
    i = 0
    while i < len(members):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(members))
        Invariant(ToSeq(result) == ToSeq(members).take(i))
        # invariants-end
        result = result + [members[i]]
        i = i + 1
    Assert(ToSeq(members).take(len(members)) == ToSeq(members))
    Assert(ToSeq(result) == ToSeq(members))
    j = 0
    while j < len(extra):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(extra), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(extra))
        Invariant(ToSeq(result).take(len(members)) == ToSeq(members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                 members[k] in ToSeq(result)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                 extra[k] in ToSeq(result)))))
        # invariants-end
        m = extra[j]
        present = m in ToSeq(result)
        if not present:
            result = result + [m]
        Assert(extra[j] in ToSeq(result))
        j = j + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit (verify=>correct) for sphinx-doc__sphinx-8035 nagini. Prior pass was INCONCLUSIVE (3 merge candidates verified but resolve timed out under load). Re-ran to COMPLETION under calm load. VERDICT: SOUND.

env python with SBU_BENCHMARK_DIR=benchmark-verified, SBU_BENCHMARK=swe_bench_verified.

SPEC SURFACE. Two modeled functions. (1) keep_private_member: keep decision FULLY PINNED by the unconditional postcondition Result()==keep_private(mode,ToSeq(names),membername,has_doc,undoc_members,filtered_inherited) over the entire precondition domain (0<=mode<=2). No wrong keep impl can verify. (2) merge_selector_names: ALL branch tightly pinned (ToSeq(Result())==ToSeq(members)); NON-ALL branch LOOSE (postconditions require only prefix==members + Forall(members present) + Forall(extra present); NO anti-duplicate and NO no-spurious-element clause). This loose branch is the only exploitable surface.

CRITICAL RESOLVE FACT (verified): all 3 graded tests (F2P tests/test_ext_autodoc_private_members.py::test_private_members + P2P test_private_field, test_private_field_and_private_members) pass options={'members': None, ...}. members_option(None) is the ALL sentinel (G-AX asserts this), so merge_members_option hits its early no-op `if options.get('members') is ALL: return`. The non-ALL merge branch is DEAD CODE w.r.t. the test suite; deviations there cannot change the resolve outcome. The discriminating F2P behaviour lives entirely in the keep decision (site A), which is pinned.

ATTACKS (8 distinct wrong impls; each same-spec exit 0, then adversary weakness / resolve run concurrently in batches of 3, JVM+Z3 each). Commands per attack:
  same-spec: python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8035 <atk>
  weakness:  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-8035 <atk>
  resolve:   python do_resolve.py <patch> <label>  (wraps harness.run_resolve timeout=1800 retries=1)

KEEP-DECISION attacks (site A, must FAIL verify — all rejected):
- atk_1.py PREPATCH collapse: option_given=(mode!=0); return option_given and (has_doc or undoc_members). weakness exit 2 (verification failed). Prepatch bug reproduced.
- atk_2.py control-flow-effect: mode==2 returns True for any documentable non-filtered member (ignores names list). weakness exit 2.
- atk_3.py boundary/negation: mode==2 returns not(membername in names). weakness exit 2.
- atk_4.py partial-domain: drops the filtered_inherited clause for mode 2. weakness exit 2.
- atk_5.py mode-1 boundary: applies the inherited filter to the all-form (gold does NOT). weakness exit 2.
  => site A is airtight; every keep-decision deviation is rejected by the unconditional postcondition.

MERGE attacks:
- atk_6.py drop dedup guard -> unconditional append (duplicates): weakness exit 0 CANDIDATE (verifies 18.8s). Faithful patch patch_atk_6.diff (gold verbatim except merge body drops the `if member not in members` guard) -> run_resolve RESOLVED (resolved=true, completed=true, attempts=1, flaky=false).
- atk_7.py ungrounded/spurious-element: correct dedup then members.append('__sbu_spurious_token__') (the loose Forall postconditions forbid neither duplicates nor spurious elements): weakness exit 0 CANDIDATE (verifies 18.4s). Faithful patch patch_atk_7.diff -> run_resolve RESOLVED.
- atk_8.py MERGE ALL-branch deviation (append extra[0] in the members_is_all case): weakness exit 2 (verification FAILED) — the ALL branch's ToSeq(Result())==ToSeq(members) postcondition rejects it. Confirms the ALL branch is pinned.

POSITIVE CONTROL: positive_control.py (unmodified model.py) -> nagini_verify.sh VERIFIED (15.2s, exit 0).
GOLD ORACLE SANITY: patch.diff verbatim -> run_resolve RESOLVED (harness + prebuilt image up; run_id sbu-audit-eq-vufplkm-gold).

WHY SOUND. Every verifying wrong impl (atk_6, atk_7) is a merge NON-ALL-branch deviation whose faithful refined patch RESOLVES, because that branch never executes on the graded tests (members is ALL -> early return). The loose merge spec therefore admits NO impl whose faithful patch fails to resolve: verify=>correct holds on the tested surface. The keep decision — the actual F2P discriminator — is fully pinned and rejects every keep-side variant (atk_1..5) and the ALL-branch variant (atk_8). No verifying wrong-impl's materialized patch fails resolve.

REFINEMENT.MD AUDIT (A-legs + correspondence). All 8 legs are R / I / A-reference; NO kind-3. A1 R (option trichotomy None/ALL/List <-> mode 0/1/2 + names; str name <-> int token). A2 I+R (identical outer `if documentable ... else keep=False`). A3 R (None<->mode==0). A4 R (ALL<->mode==1; inherited filter NOT applied to all-form — matches gold, confirmed). A5 R (is_filtered_inherited_member(membername) <-> filtered_inherited boolean, internals unchanged by patch). A6 R (list membership; discriminating clause). B1 R (members all-form<->members_is_all no-op). B2 R+I (append-if-absent). A-reference correspondence checked by axiom_check.py (G-AX=pass): its gold_keep_private oracle is a VERBATIM transcription of the post-patch filter_members branch in patch.diff (None->False / ALL->True / filtered_inherited->False / else membername in private_members / undocumentable->False) and model_keep_private matches keep_private; A-reference 2 imports the REAL sphinx.ext.autodoc.merge_members_option and asserts equality over 5000 randomized inputs (genuine callee, not a self-echo). Correspondence holds; the two deep models bind to the real post-patch callees per mapping.md.

PROTOCOL MET: prior-named counterexamples re-encoded (merge dedup-drop, spurious-token), prepatch bug re-encoded (atk_1, reproduced), plus >=4 further distinct wrong impls across the required families (partial-domain atk_4, boundary/negation atk_3, control-flow-effect atk_2, ungrounded-oracle-echo atk_7, all-branch atk_8, mode-1-boundary atk_5). Every CANDIDATE's faithful patch materialized and RUN through the official harness (executed run_resolve, not speculation); none breaks the spec. Verifications run concurrently <=3 at a time.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8035.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an automatic-documentation pass collects the members of an object and
  must decide whether to keep a member that is considered private, the option
  that controls private members can be in one of three states, and the keep
  decision depends on which state it is in:

    (a) the option was NOT supplied -> no private member is kept;
    (b) the option was supplied with NO argument (the "all-private" form)
        -> a private member is kept exactly when it is documentable in the
        usual sense (it has documentation, or undocumented members are being
        kept);
    (c) the option was supplied with an explicit list of names -> a private
        member is kept exactly when its OWN name appears in that list, it is
        otherwise documentable, and it is not an inherited member that is being
        filtered out. A private member whose name is NOT in the list is
        dropped, even though OTHER names are listed.

  The crucial point distinguishing (c) from a coarse on/off control: supplying
  a non-empty list of names does NOT keep every private member; it keeps
  exactly the named ones. An undocumentable private member is never kept in any
  state.

  A second behaviour is the merge of the various ``*-members`` selectors into
  the explicit member list: when the principal member selector is the
  "all-members" form, the merge is a no-op; otherwise each name from each
  supplementary selector that is given as an explicit list (not the all-form)
  is appended to the member list if it is not already present, preserving order
  and avoiding duplicates.

Member names are modelled as ``int`` identity tokens; a list of names is a
``List[int]`` of such tokens (Nagini bans ``str`` indexing). The three option
states are encoded by an explicit ``mode`` tag (0 = absent, 1 = all-form,
2 = explicit list) carrying its list payload, which is the faithful refinement
of the ``None`` / sentinel-object / list trichotomy the real option uses.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms: the keep decision and the merge are pure boolean /
#  sequence logic over the abstract option tag, the name tokens and the
#  documentability flags, spelled out in full. There is no unchanged opaque
#  callee whose contract the proof consumes.)
# axioms-end


# pure-start
@Pure
def documentable(has_doc: bool, undoc_members: bool) -> bool:
    """A member is documentable in the usual sense when it carries
    documentation, or undocumented members are being retained."""
    return has_doc or undoc_members


@Pure
def keep_private(mode: int, names: PSeq[int], membername: int,
                 has_doc: bool, undoc_members: bool,
                 filtered_inherited: bool) -> bool:
    """The keep decision for a member that is considered private, as a pure
    function of the option's three states.

      mode 0 (absent)        -> never kept
      mode 1 (all-form)      -> kept iff documentable
      mode 2 (explicit list) -> kept iff documentable, not a filtered inherited
                                member, and this member's name is in the list

    The inherited-member filter applies only to the explicit-list state; the
    all-form keeps every documentable private member.
    """
    if not documentable(has_doc, undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    return (not filtered_inherited) and (membername in names)
# pure-end


def keep_private_member(mode: int, names: List[int], membername: int,
                        has_doc: bool, undoc_members: bool,
                        filtered_inherited: bool) -> bool:
    # pre-conditions-start
    # ``names`` (the explicit list payload of the option) is read only here:
    # fractional permission, returned unchanged (directive 5). ``mode`` is the
    # option-state tag, 0/1/2 as documented above.
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(0 <= mode and mode <= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    # The decision equals the pure three-state rule.
    Ensures(Result() == keep_private(mode, ToSeq(names), membername,
                                     has_doc, undoc_members, filtered_inherited))
    # An undocumentable member is never kept, in any option state.
    Ensures(Implies(not documentable(has_doc, undoc_members),
                    Result() is False))
    # Absent option: never kept.
    Ensures(Implies(mode == 0, Result() is False))
    # All-form: kept exactly when documentable (the inherited-member filter
    # does not apply to the all-form).
    Ensures(Implies(mode == 1,
                    Result() == documentable(has_doc, undoc_members)))
    # Explicit list: a documentable, non-filtered member is kept iff its OWN
    # name is in the list. This is the discriminating clause: a non-empty list
    # does NOT keep every private member, only the named ones.
    Ensures(Implies(mode == 2 and documentable(has_doc, undoc_members)
                    and not filtered_inherited,
                    Result() == (membername in ToSeq(names))))
    Ensures(Implies(mode == 2 and documentable(has_doc, undoc_members)
                    and not filtered_inherited and not (membername in ToSeq(names)),
                    Result() is False))
    # post-conditions-end
    # impl-start
    if not (has_doc or undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    if filtered_inherited:
        return False
    return membername in ToSeq(names)
    # impl-end


@Pure
def merged_at(orig: PSeq[int], extra: PSeq[int], i: int) -> bool:
    """Membership predicate for the merge result built from ``orig`` by
    appending the as-yet-unseen names of ``extra``: ``i`` indexes ``extra`` and
    the name is appended exactly when it is not already in ``orig`` and not in
    the already-processed prefix of ``extra``."""
    Requires(0 <= i and i < len(extra))
    return (not (extra[i] in orig)) and (not (extra[i] in extra.take(i)))


def merge_selector_names(members_is_all: bool, members: List[int],
                         extra: List[int]) -> List[int]:
    # pre-conditions-start
    # ``members`` is the principal member list being extended; ``members_is_all``
    # is True when the principal selector is the all-members form (so the merge
    # is a no-op). ``extra`` is one supplementary selector given as an explicit
    # list of names. Both lists are read only here (fractional permission).
    Requires(Acc(list_pred(members), 1 / 2))
    Requires(Acc(list_pred(extra), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(members), 1 / 2))
    Ensures(Acc(list_pred(extra), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # All-members form: the merge is a no-op, the member list is unchanged.
    Ensures(Implies(members_is_all, ToSeq(Result()) == ToSeq(members)))
    # Otherwise the result begins with the original member list (order kept) ...
    Ensures(Implies(not members_is_all,
                    ToSeq(Result()).take(len(members)) == ToSeq(members)))
    # ... and every original member is still present.
    Ensures(Implies(not members_is_all,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                   members[k] in ToSeq(Result()))))))
    # ... and every extra name is now present (it was appended if new, or was
    # already there) — the supplementary selector's names are all included.
    Ensures(Implies(not members_is_all,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(extra),
                                                   extra[k] in ToSeq(Result()))))))
    # post-conditions-end
    # impl-start
    if members_is_all:
        result = []  # type: List[int]
        i = 0
        while i < len(members):
            # invariants-start
            Invariant(Acc(list_pred(members), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(members))
            Invariant(ToSeq(result) == ToSeq(members).take(i))
            # invariants-end
            result = result + [members[i]]
            i = i + 1
        Assert(ToSeq(members).take(len(members)) == ToSeq(members))
        return result
    result = []
    i = 0
    while i < len(members):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(members))
        Invariant(ToSeq(result) == ToSeq(members).take(i))
        # invariants-end
        result = result + [members[i]]
        i = i + 1
    Assert(ToSeq(members).take(len(members)) == ToSeq(members))
    Assert(ToSeq(result) == ToSeq(members))
    j = 0
    while j < len(extra):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(extra), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(extra))
        Invariant(ToSeq(result).take(len(members)) == ToSeq(members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                 members[k] in ToSeq(result)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                 extra[k] in ToSeq(result)))))
        # invariants-end
        m = extra[j]
        present = m in ToSeq(result)
        if not present:
            result = result + [m]
        Assert(extra[j] in ToSeq(result))
        j = j + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit (verify=>correct) for sphinx-doc__sphinx-8035 nagini. Prior pass was INCONCLUSIVE (3 merge candidates verified but resolve timed out under load). Re-ran to COMPLETION under calm load. VERDICT: SOUND.

env python with SBU_BENCHMARK_DIR=benchmark-verified, SBU_BENCHMARK=swe_bench_verified.

SPEC SURFACE. Two modeled functions. (1) keep_private_member: keep decision FULLY PINNED by the unconditional postcondition Result()==keep_private(mode,ToSeq(names),membername,has_doc,undoc_members,filtered_inherited) over the entire precondition domain (0<=mode<=2). No wrong keep impl can verify. (2) merge_selector_names: ALL branch tightly pinned (ToSeq(Result())==ToSeq(members)); NON-ALL branch LOOSE (postconditions require only prefix==members + Forall(members present) + Forall(extra present); NO anti-duplicate and NO no-spurious-element clause). This loose branch is the only exploitable surface.

CRITICAL RESOLVE FACT (verified): all 3 graded tests (F2P tests/test_ext_autodoc_private_members.py::test_private_members + P2P test_private_field, test_private_field_and_private_members) pass options={'members': None, ...}. members_option(None) is the ALL sentinel (G-AX asserts this), so merge_members_option hits its early no-op `if options.get('members') is ALL: return`. The non-ALL merge branch is DEAD CODE w.r.t. the test suite; deviations there cannot change the resolve outcome. The discriminating F2P behaviour lives entirely in the keep decision (site A), which is pinned.

ATTACKS (8 distinct wrong impls; each same-spec exit 0, then adversary weakness / resolve run concurrently in batches of 3, JVM+Z3 each). Commands per attack:
  same-spec: python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8035 <atk>
  weakness:  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-8035 <atk>
  resolve:   python do_resolve.py <patch> <label>  (wraps harness.run_resolve timeout=1800 retries=1)

KEEP-DECISION attacks (site A, must FAIL verify — all rejected):
- atk_1.py PREPATCH collapse: option_given=(mode!=0); return option_given and (has_doc or undoc_members). weakness exit 2 (verification failed). Prepatch bug reproduced.
- atk_2.py control-flow-effect: mode==2 returns True for any documentable non-filtered member (ignores names list). weakness exit 2.
- atk_3.py boundary/negation: mode==2 returns not(membername in names). weakness exit 2.
- atk_4.py partial-domain: drops the filtered_inherited clause for mode 2. weakness exit 2.
- atk_5.py mode-1 boundary: applies the inherited filter to the all-form (gold does NOT). weakness exit 2.
  => site A is airtight; every keep-decision deviation is rejected by the unconditional postcondition.

MERGE attacks:
- atk_6.py drop dedup guard -> unconditional append (duplicates): weakness exit 0 CANDIDATE (verifies 18.8s). Faithful patch patch_atk_6.diff (gold verbatim except merge body drops the `if member not in members` guard) -> run_resolve RESOLVED (resolved=true, completed=true, attempts=1, flaky=false).
- atk_7.py ungrounded/spurious-element: correct dedup then members.append('__sbu_spurious_token__') (the loose Forall postconditions forbid neither duplicates nor spurious elements): weakness exit 0 CANDIDATE (verifies 18.4s). Faithful patch patch_atk_7.diff -> run_resolve RESOLVED.
- atk_8.py MERGE ALL-branch deviation (append extra[0] in the members_is_all case): weakness exit 2 (verification FAILED) — the ALL branch's ToSeq(Result())==ToSeq(members) postcondition rejects it. Confirms the ALL branch is pinned.

POSITIVE CONTROL: positive_control.py (unmodified model.py) -> nagini_verify.sh VERIFIED (15.2s, exit 0).
GOLD ORACLE SANITY: patch.diff verbatim -> run_resolve RESOLVED (harness + prebuilt image up; run_id sbu-audit-eq-vufplkm-gold).

WHY SOUND. Every verifying wrong impl (atk_6, atk_7) is a merge NON-ALL-branch deviation whose faithful refined patch RESOLVES, because that branch never executes on the graded tests (members is ALL -> early return). The loose merge spec therefore admits NO impl whose faithful patch fails to resolve: verify=>correct holds on the tested surface. The keep decision — the actual F2P discriminator — is fully pinned and rejects every keep-side variant (atk_1..5) and the ALL-branch variant (atk_8). No verifying wrong-impl's materialized patch fails resolve.

REFINEMENT.MD AUDIT (A-legs + correspondence). All 8 legs are R / I / A-reference; NO kind-3. A1 R (option trichotomy None/ALL/List <-> mode 0/1/2 + names; str name <-> int token). A2 I+R (identical outer `if documentable ... else keep=False`). A3 R (None<->mode==0). A4 R (ALL<->mode==1; inherited filter NOT applied to all-form — matches gold, confirmed). A5 R (is_filtered_inherited_member(membername) <-> filtered_inherited boolean, internals unchanged by patch). A6 R (list membership; discriminating clause). B1 R (members all-form<->members_is_all no-op). B2 R+I (append-if-absent). A-reference correspondence checked by axiom_check.py (G-AX=pass): its gold_keep_private oracle is a VERBATIM transcription of the post-patch filter_members branch in patch.diff (None->False / ALL->True / filtered_inherited->False / else membername in private_members / undocumentable->False) and model_keep_private matches keep_private; A-reference 2 imports the REAL sphinx.ext.autodoc.merge_members_option and asserts equality over 5000 randomized inputs (genuine callee, not a self-echo). Correspondence holds; the two deep models bind to the real post-patch callees per mapping.md.

PROTOCOL MET: prior-named counterexamples re-encoded (merge dedup-drop, spurious-token), prepatch bug re-encoded (atk_1, reproduced), plus >=4 further distinct wrong impls across the required families (partial-domain atk_4, boundary/negation atk_3, control-flow-effect atk_2, ungrounded-oracle-echo atk_7, all-branch atk_8, mode-1-boundary atk_5). Every CANDIDATE's faithful patch materialized and RUN through the official harness (executed run_resolve, not speculation); none breaks the spec. Verifications run concurrently <=3 at a time.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the nagini bundle of sphinx-doc__sphinx-8035. Modeled functions: keep_private / keep_private_member (private-member keep decision) and merged_at / merge_selector_names (the *-members merge). Both are DEEP models (no @ContractOnly axioms consumed) validated == the real post-patch callees.

Empirical verification against the REAL repo (applied gold patch to, PYTHONPATH-imported sphinx.ext.autodoc):
- keep_private: 0 mismatches across ALL three option states — built through the REAL members_option converter (None -> mode 0; members_option(None) is ALL -> mode 1; explicit lists incl. the empty-list edge members_option('')==[] -> mode 2) — crossed with name x has_doc x undoc_members x filtered_inherited. Exactly reproduces the gold branch: undocumentable => False; None => False; ALL => True (inherited filter NOT applied to all-form); else filtered_inherited => False, otherwise membername in list.
- merge_selector_names: matches the REAL sphinx.ext.autodoc.merge_members_option over 5000 randomized inputs on both branches (members_is_all no-op; else append-if-absent preserving order/dedup).
- axiom_check.py (G-AX) exits 0 both offline and with the real callees.

Type abstraction is faithful: str names -> int identity tokens (only equality/membership observed, equality-preserving); None/ALL/List[str] -> mode 0/1/2 + names payload (bijective, built via the real converter). The precondition 0<=mode<=2 exactly covers the three real option states; no real input falls outside it. The postconditions are exact equalities to the pure rule (Result() == keep_private(...)), not over-constraints — the impl provably satisfies them and they match real behavior on every input.

Scope note (not a divergence): merge_selector_names models ONE supplementary selector rather than iterating both {'private-members','special-members'}; on any single-selector input it agrees with the real callee, and the composite real effect is the fold of single-selector merges, so no diverging input exists within the modeled signature. The F2P discriminator (private-members='_public_function' drops private_function) is enforced by A6 / the mode-2 postcondition. same-spec passes on the model; spec region byte-identical. No input found where the modeled function disagrees with the real callee. G-EQ=fail / G-PANEL-1=fail on this cell are separate (spec-too-weak / echo lane), not a faithfulness/drift defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK mechanical screen passes cleanly (no hard failures). Verified independently beyond the lexical screen:

1. Spec view = model.py docstring + axioms/pure/pre/post regions (impl elided). No repo file path (sphinx/ext/autodoc/__init__.py absent). No diff markers, no reproduced gold-patch line, no narration terms (bug/fix/patch/pre-patch/etc.).

2. No patched repo symbol appears in spec-view identifiers or comments. Gold changed symbols are {ClassDocumenter, ModuleDocumenter, bool_option, is_filtered_inherited_member, merge_members_option, merge_special_members_option} plus the ALL sentinel and members_option converter. The model uses only abstract names (keep_private, keep_private_member, merge_selector_names, merged_at, documentable) and an option-trichotomy encoding (mode 0/1/2 + List[int] tokens) — none echoes a repo symbol.

3. The core three-state keep behavior (private-members can take an explicit list; only named members kept) is EXACTLY what the public problem_statement requests ('for :private-members: to take arguments, similarly to how :members: currently works'). Stating this desired behavior is the legitimate function of a correctness spec, not edit-disclosure.

4. The second modeled behavior (merge of *-members selectors) goes beyond the problem statement but is phrased purely as abstract desired behaviour over model carriers, with no repo symbol/path/edit exposed. A solver cannot reconstruct the gold patch (target file, bool_option->members_option option-spec change, ALL sentinel, new helper name/call sites, branch structure) from the spec view.

Leakage is judged against problem_statement only (not hints_text; hints were empty anyway). Conclusion: the spec view does not leak the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
