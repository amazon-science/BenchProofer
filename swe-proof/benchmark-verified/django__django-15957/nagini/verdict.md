# P2 adversarial audit — django__django-15957

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
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class PrefetchQuery:
@@ -89,7 +88,6 @@
     Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Requires(Acc(query.membership_applied))
     Requires(not is_sliced(query))
-    Requires(MustTerminate(2))
     Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Ensures(Acc(query.membership_applied))
     Ensures(query.membership_applied == True)
@@ -119,7 +117,6 @@
     Requires(query.membership_applied == False)
     Requires(query.lower_bound is None and query.upper_bound is None)
     Requires(instance_count >= 0)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
@@ -151,19 +148,6 @@
     Ensures(query.offset_mark == 0 and query.limit_mark is None)
     # post-conditions-end
     # impl-start
-    if is_sliced(query):
-        low = query.offset_mark
-        high = query.limit_mark      # type: Optional[int]
-        # record the start offset as the lower position restriction
-        query.lower_bound = low
-        # record a finite stop limit as the upper position restriction
-        if high is not None:
-            query.upper_bound = high
-        # remove the slice so the membership predicate can be applied
-        query.offset_mark = 0
-        query.limit_mark = None
-    # at this point the query is no longer sliced; the membership predicate is
-    # applicable and is ANDed on (apply_membership requires not is_sliced).
     apply_membership(query)
     return query
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class PrefetchQuery:
@@ -89,7 +88,6 @@
     Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Requires(Acc(query.membership_applied))
     Requires(not is_sliced(query))
-    Requires(MustTerminate(2))
     Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Ensures(Acc(query.membership_applied))
     Ensures(query.membership_applied == True)
@@ -119,7 +117,6 @@
     Requires(query.membership_applied == False)
     Requires(query.lower_bound is None and query.upper_bound is None)
     Requires(instance_count >= 0)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
@@ -153,17 +150,12 @@
     # impl-start
     if is_sliced(query):
         low = query.offset_mark
-        high = query.limit_mark      # type: Optional[int]
-        # record the start offset as the lower position restriction
+        high = query.limit_mark
         query.lower_bound = low
-        # record a finite stop limit as the upper position restriction
         if high is not None:
             query.upper_bound = high
-        # remove the slice so the membership predicate can be applied
         query.offset_mark = 0
         query.limit_mark = None
-    # at this point the query is no longer sliced; the membership predicate is
-    # applicable and is ANDed on (apply_membership requires not is_sliced).
-    apply_membership(query)
+    query.membership_applied = True
     return query
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class PrefetchQuery:
@@ -89,7 +88,6 @@
     Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Requires(Acc(query.membership_applied))
     Requires(not is_sliced(query))
-    Requires(MustTerminate(2))
     Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Ensures(Acc(query.membership_applied))
     Ensures(query.membership_applied == True)
@@ -119,7 +117,6 @@
     Requires(query.membership_applied == False)
     Requires(query.lower_bound is None and query.upper_bound is None)
     Requires(instance_count >= 0)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
@@ -153,17 +150,12 @@
     # impl-start
     if is_sliced(query):
         low = query.offset_mark
-        high = query.limit_mark      # type: Optional[int]
-        # record the start offset as the lower position restriction
-        query.lower_bound = low
-        # record a finite stop limit as the upper position restriction
+        high = query.limit_mark
+        query.lower_bound = low + 1
         if high is not None:
             query.upper_bound = high
-        # remove the slice so the membership predicate can be applied
         query.offset_mark = 0
         query.limit_mark = None
-    # at this point the query is no longer sliced; the membership predicate is
-    # applicable and is ANDed on (apply_membership requires not is_sliced).
     apply_membership(query)
     return query
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class PrefetchQuery:
@@ -89,7 +88,6 @@
     Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Requires(Acc(query.membership_applied))
     Requires(not is_sliced(query))
-    Requires(MustTerminate(2))
     Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Ensures(Acc(query.membership_applied))
     Ensures(query.membership_applied == True)
@@ -119,7 +117,6 @@
     Requires(query.membership_applied == False)
     Requires(query.lower_bound is None and query.upper_bound is None)
     Requires(instance_count >= 0)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
@@ -153,17 +150,11 @@
     # impl-start
     if is_sliced(query):
         low = query.offset_mark
-        high = query.limit_mark      # type: Optional[int]
-        # record the start offset as the lower position restriction
+        high = query.limit_mark
         query.lower_bound = low
-        # record a finite stop limit as the upper position restriction
         if high is not None:
             query.upper_bound = high
-        # remove the slice so the membership predicate can be applied
         query.offset_mark = 0
-        query.limit_mark = None
-    # at this point the query is no longer sliced; the membership predicate is
-    # applicable and is ANDed on (apply_membership requires not is_sliced).
     apply_membership(query)
     return query
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class PrefetchQuery:
@@ -89,7 +88,6 @@
     Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Requires(Acc(query.membership_applied))
     Requires(not is_sliced(query))
-    Requires(MustTerminate(2))
     Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Ensures(Acc(query.membership_applied))
     Ensures(query.membership_applied == True)
@@ -119,7 +117,6 @@
     Requires(query.membership_applied == False)
     Requires(query.lower_bound is None and query.upper_bound is None)
     Requires(instance_count >= 0)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
@@ -151,19 +148,14 @@
     Ensures(query.offset_mark == 0 and query.limit_mark is None)
     # post-conditions-end
     # impl-start
+    apply_membership(query)
     if is_sliced(query):
         low = query.offset_mark
-        high = query.limit_mark      # type: Optional[int]
-        # record the start offset as the lower position restriction
+        high = query.limit_mark
         query.lower_bound = low
-        # record a finite stop limit as the upper position restriction
         if high is not None:
             query.upper_bound = high
-        # remove the slice so the membership predicate can be applied
         query.offset_mark = 0
         query.limit_mark = None
-    # at this point the query is no longer sliced; the membership predicate is
-    # applicable and is ANDed on (apply_membership requires not is_sliced).
-    apply_membership(query)
     return query
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class PrefetchQuery:
@@ -89,7 +88,6 @@
     Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Requires(Acc(query.membership_applied))
     Requires(not is_sliced(query))
-    Requires(MustTerminate(2))
     Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Ensures(Acc(query.membership_applied))
     Ensures(query.membership_applied == True)
@@ -119,7 +117,6 @@
     Requires(query.membership_applied == False)
     Requires(query.lower_bound is None and query.upper_bound is None)
     Requires(instance_count >= 0)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
@@ -151,19 +148,13 @@
     Ensures(query.offset_mark == 0 and query.limit_mark is None)
     # post-conditions-end
     # impl-start
-    if is_sliced(query):
-        low = query.offset_mark
-        high = query.limit_mark      # type: Optional[int]
-        # record the start offset as the lower position restriction
-        query.lower_bound = low
-        # record a finite stop limit as the upper position restriction
-        if high is not None:
-            query.upper_bound = high
-        # remove the slice so the membership predicate can be applied
-        query.offset_mark = 0
-        query.limit_mark = None
-    # at this point the query is no longer sliced; the membership predicate is
-    # applicable and is ANDed on (apply_membership requires not is_sliced).
+    low = query.offset_mark
+    high = query.limit_mark
+    query.lower_bound = low
+    if high is not None:
+        query.upper_bound = high
+    query.offset_mark = 0
+    query.limit_mark = None
     apply_membership(query)
     return query
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class PrefetchQuery:
@@ -89,7 +88,6 @@
     Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Requires(Acc(query.membership_applied))
     Requires(not is_sliced(query))
-    Requires(MustTerminate(2))
     Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Ensures(Acc(query.membership_applied))
     Ensures(query.membership_applied == True)
@@ -119,7 +117,6 @@
     Requires(query.membership_applied == False)
     Requires(query.lower_bound is None and query.upper_bound is None)
     Requires(instance_count >= 0)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
@@ -152,18 +149,13 @@
     # post-conditions-end
     # impl-start
     if is_sliced(query):
+        query.offset_mark = 0
+        query.limit_mark = None
         low = query.offset_mark
-        high = query.limit_mark      # type: Optional[int]
-        # record the start offset as the lower position restriction
+        high = query.limit_mark
         query.lower_bound = low
-        # record a finite stop limit as the upper position restriction
         if high is not None:
             query.upper_bound = high
-        # remove the slice so the membership predicate can be applied
-        query.offset_mark = 0
-        query.limit_mark = None
-    # at this point the query is no longer sliced; the membership predicate is
-    # applicable and is ANDed on (apply_membership requires not is_sliced).
     apply_membership(query)
     return query
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class PrefetchQuery:
@@ -89,7 +88,6 @@
     Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Requires(Acc(query.membership_applied))
     Requires(not is_sliced(query))
-    Requires(MustTerminate(2))
     Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Ensures(Acc(query.membership_applied))
     Ensures(query.membership_applied == True)
@@ -119,7 +117,6 @@
     Requires(query.membership_applied == False)
     Requires(query.lower_bound is None and query.upper_bound is None)
     Requires(instance_count >= 0)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
@@ -153,17 +150,13 @@
     # impl-start
     if is_sliced(query):
         low = query.offset_mark
-        high = query.limit_mark      # type: Optional[int]
-        # record the start offset as the lower position restriction
-        query.lower_bound = low
-        # record a finite stop limit as the upper position restriction
+        high = query.limit_mark
+        if low != 0:
+            query.lower_bound = low
         if high is not None:
             query.upper_bound = high
-        # remove the slice so the membership predicate can be applied
         query.offset_mark = 0
         query.limit_mark = None
-    # at this point the query is no longer sliced; the membership predicate is
-    # applicable and is ANDed on (apply_membership requires not is_sliced).
     apply_membership(query)
     return query
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class PrefetchQuery:
@@ -89,7 +88,6 @@
     Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Requires(Acc(query.membership_applied))
     Requires(not is_sliced(query))
-    Requires(MustTerminate(2))
     Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
     Ensures(Acc(query.membership_applied))
     Ensures(query.membership_applied == True)
@@ -119,7 +117,6 @@
     Requires(query.membership_applied == False)
     Requires(query.lower_bound is None and query.upper_bound is None)
     Requires(instance_count >= 0)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
@@ -153,17 +150,12 @@
     # impl-start
     if is_sliced(query):
         low = query.offset_mark
-        high = query.limit_mark      # type: Optional[int]
-        # record the start offset as the lower position restriction
-        query.lower_bound = low
-        # record a finite stop limit as the upper position restriction
+        high = query.limit_mark
+        query.lower_bound = high if high is not None else low
         if high is not None:
-            query.upper_bound = high
-        # remove the slice so the membership predicate can be applied
+            query.upper_bound = low
         query.offset_mark = 0
         query.limit_mark = None
-    # at this point the query is no longer sliced; the membership predicate is
-    # applicable and is ANDed on (apply_membership requires not is_sliced).
     apply_membership(query)
     return query
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15957.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A prefetch builds a related-object query by ANDing a membership predicate
  (the related objects belonging to the given parent instances) onto a query.
  The query may already have a slice taken on it (a start offset and an
  optional stop limit). The desired observable behaviour is:

    (1) The membership predicate is ALWAYS applied to produce the result, for
        every prefetch query — whether or not a slice was taken.

    (2) Taking a slice on a query and then applying a further predicate is not
        directly well-defined; doing it on a still-sliced query is an error.
        So a prefetch query that carries a slice must, by the time the
        membership predicate is applied, no longer be sliced: the result is a
        query that is NOT sliced.

    (3) The slice the caller asked for must not be lost when it is removed: the
        result still restricts each parent's related objects to exactly the
        same positions the original slice selected (the start offset, and the
        stop limit when one was given). Concretely the result records that
        restriction iff the query was originally sliced, and an upper
        restriction iff the original slice also had a finite stop limit.

The query is modelled as a minimal class carrying only the touched state: the
slice's start/stop marks, the predicates that have been applied to it, and two
opaque carrier fields (lower_bound/upper_bound) in which the result records the
position restriction described in (3). Field names and parent instances are
opaque to this behaviour and are carried as scalars.

The single step that is NOT a plain structural update is applying the
membership predicate. It is modelled as the callee `apply_membership`, which is
well-defined only on a query carrying no slice (its precondition); on success it
grants an unforgeable token (`membership_token`) recording that the predicate
was applied to a non-sliced query. The result of `bounded_prefetch` must carry
that token, so behaviour (1) cannot be satisfied by merely flagging the query —
it must actually route through a successful application on an unsliced query.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class PrefetchQuery:
    def __init__(self, offset_mark: int, limit_mark: Optional[int]) -> None:
        Requires(offset_mark >= 0)
        Requires(limit_mark is None or limit_mark >= 0)
        Ensures(Acc(self.offset_mark) and Acc(self.limit_mark))  # type: ignore
        Ensures(Acc(self.membership_applied))  # type: ignore
        Ensures(Acc(self.lower_bound) and Acc(self.upper_bound))  # type: ignore
        Ensures(self.offset_mark == offset_mark and self.limit_mark is limit_mark)  # type: ignore
        Ensures(self.membership_applied == False)  # type: ignore
        Ensures(self.lower_bound is None and self.upper_bound is None)  # type: ignore
        self.offset_mark = offset_mark          # slice start offset
        self.limit_mark = limit_mark            # slice stop limit (None = unbounded)
        self.membership_applied = False         # has the membership predicate been ANDed on?
        self.lower_bound = None                 # type: Optional[int]  # opaque lower position restriction
        self.upper_bound = None                 # type: Optional[int]  # opaque upper position restriction

# axioms-start
# Unforgeable capability token marking a query the membership predicate was
# applied to by a SUCCESSFUL (non-sliced) application step. It is abstract (no
# body), so nothing can fabricate it by hand; it can be obtained ONLY from the
# Ensures of apply_membership below, which grants it only when the query carried
# no slice at application time. The result of bounded_prefetch must carry this
# token, so a result the application step never produced on an unsliced query
# cannot satisfy the contract — applying the predicate to a still-sliced query
# is exactly the error the issue reports. Provenance + executable soundness
# check: mapping.md / axiom_check.py (G-AX).
@ContractOnly
@Predicate
def membership_token(query: PrefetchQuery) -> bool:
    pass

@ContractOnly
def apply_membership(query: PrefetchQuery) -> None:
    """Apply the membership predicate to the query. Applying a predicate is only
    well-defined while the query has NO slice taken on it: a query with a slice
    taken cannot accept a further predicate (the precondition models exactly
    that constraint). On a successful application it records that the predicate
    was applied AND grants the membership token on the query — the token nothing
    else can fabricate. Provenance + executable soundness check: mapping.md /
    axiom_check.py."""
    Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
    Requires(Acc(query.membership_applied))
    Requires(not is_sliced(query))
    Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
    Ensures(Acc(query.membership_applied))
    Ensures(query.membership_applied == True)
    Ensures(membership_token(query))
# axioms-end

# pure-start
@Pure
def is_sliced(query: PrefetchQuery) -> bool:
    """The query has a slice taken on it: either a non-zero start offset or a
    finite stop limit is present."""
    Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
    return query.offset_mark != 0 or query.limit_mark is not None
# pure-end

def bounded_prefetch(query: PrefetchQuery, member_code: int,
                     instance_count: int) -> PrefetchQuery:
    # pre-conditions-start
    Requires(Acc(query.offset_mark) and Acc(query.limit_mark))
    Requires(Acc(query.membership_applied))
    Requires(Acc(query.lower_bound) and Acc(query.upper_bound))
    Requires(query.offset_mark >= 0)
    Requires(query.limit_mark is None or query.limit_mark >= 0)
    # A freshly assembled prefetch query has no predicate applied yet.
    Requires(query.membership_applied == False)
    Requires(query.lower_bound is None and query.upper_bound is None)
    Requires(instance_count >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
    Ensures(Acc(query.membership_applied))
    Ensures(Acc(query.lower_bound) and Acc(query.upper_bound))
    Ensures(Result() is query)
    # (1) the membership predicate is always applied — and not merely flagged:
    #   the result must carry the unforgeable token that the application step
    #   grants ONLY when the query carried no slice at application time. Because
    #   the token cannot be fabricated, the result must have been produced by a
    #   successful application on an unsliced query (so a still-sliced query was
    #   first un-sliced), which is exactly the desired behaviour.
    Ensures(membership_token(query))
    Ensures(query.membership_applied == True)
    # (3) the position restriction preserves exactly the original slice.
    #   a lower restriction is recorded iff the query was originally sliced,
    #   and it carries the original start offset.
    Ensures(Old(is_sliced(query)) == (query.lower_bound is not None))
    Ensures(Implies(query.lower_bound is not None,
                    query.lower_bound == Old(query.offset_mark)))
    #   an upper restriction is recorded iff the query was originally sliced AND
    #   had a finite stop limit, and it carries that limit.
    Ensures((Old(is_sliced(query)) and Old(query.limit_mark) is not None)
            == (query.upper_bound is not None))
    Ensures(Implies(query.upper_bound is not None,
                    query.upper_bound == Old(query.limit_mark)))
    # (2) the resulting query is no longer sliced (so the predicate is applicable).
    Ensures(not is_sliced(query))
    Ensures(query.offset_mark == 0 and query.limit_mark is None)
    # post-conditions-end
    # impl-start
    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        # record the start offset as the lower position restriction
        query.lower_bound = low
        # record a finite stop limit as the upper position restriction
        if high is not None:
            query.upper_bound = high
        # remove the slice so the membership predicate can be applied
        query.offset_mark = 0
        query.limit_mark = None
    # at this point the query is no longer sliced; the membership predicate is
    # applicable and is ANDed on (apply_membership requires not is_sliced).
    apply_membership(query)
    return query
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Ran 9 distinct same-spec wrong impls through `adversary weakness nagini django__django-15957` (project root, python python; verifications run concurrently in batches of <=3 JVM+Z3). Every attack returned exit 2 = NOT-A-COUNTEREXAMPLE (same-spec held, verification FAILED) => NO CANDIDATE (no verifying wrong impl), so there is no faithful refined patch to materialize/run through resolve. Positive control (verbatim model.py impl) verifies (nagini_verify.sh exit 0, 13.6s). same-spec explicitly confirmed exit 0 on atk_1/atk_2/atk_8; negative control (spectamper.py, instance_count>=1) correctly fails same-spec (exit 1), showing the same-spec gate discriminates.

Attack roster (impl-region-only edits; axioms/@Pure/Requires/Ensures byte-identical):
- atk_1 prepatch bug: `apply_membership(query); return query` — fails apply_membership's `not is_sliced` precond + missing token/bounds/not-sliced posts. Reproduces the recorded prepatch failure (model_prepatch.py:157). exit 2.
- atk_2 ungrounded-oracle/flag-echo: full slice->bound + clear, but sets `membership_applied=True` instead of calling apply_membership => cannot obtain unforgeable membership_token(query) post. exit 2. (Directly exercises the load-bearing token cheat-closure.)
- atk_3 boundary/value: lower_bound=low+1 => violates `lower_bound==Old(offset_mark)`. exit 2.
- atk_4 partial-domain: forgets `limit_mark=None` => still sliced when finite limit => apply_membership precond + not-sliced post fail. exit 2.
- atk_5 control-flow-effect: apply_membership BEFORE clearing slice => precond violated on sliced query. exit 2.
- atk_6 presence-condition: records lower_bound unconditionally => violates `Old(is_sliced)==(lower_bound is not None)` on unsliced input. exit 2.
- atk_7 read-after-clear: clears marks then reads (records 0/None) => wrong bound values + presence. exit 2.
- atk_8 boundary limit-only slice: records lower_bound only when offset!=0, missing the offset==0/finite-limit slice => presence-iff-sliced violation. exit 2.
- atk_9 value-mixup: swaps limit into lower_bound and offset into upper_bound => value-equality posts fail. exit 2.

Refinement audit: all legs A1-A9/A8b are R / I / A-consumed / A-reference — NO kind-3. The two A-consumed axioms (apply_membership modeling the UNCHANGED QuerySet.filter/can_filter raise-on-sliced guard; membership_token abstract unforgeable capability) model an unchanged callee, not the function under change; the A-reference deep model (structural slice->bound translation) is validated == the real _filter_prefetch_queryset + Query slice machinery by axiom_check.py (G-AX pass, apply_gold=true, 5 helper + 6 is_sliced/clear_limits cases). Field bijection (offset_mark<->low_mark, limit_mark<->high_mark), strict-lower GreaterThan, inclusive-upper LessThanOrEqual-iff-finite, clear_limits, and filter-vs-raise all correspond to the gold hunk. The membership_token closes the directive-8 flag-echo cheat, empirically confirmed by atk_2 failing to verify. G-EQ SOUND: >=5 (9) distinct same-spec attacks run, none is a verifying counterexample; positive control verifies.

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
"""Twin-artifact model for django__django-15957.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A prefetch builds a related-object query by ANDing a membership predicate
  (the related objects belonging to the given parent instances) onto a query.
  The query may already have a slice taken on it (a start offset and an
  optional stop limit). The desired observable behaviour is:

    (1) The membership predicate is ALWAYS applied to produce the result, for
        every prefetch query — whether or not a slice was taken.

    (2) Taking a slice on a query and then applying a further predicate is not
        directly well-defined; doing it on a still-sliced query is an error.
        So a prefetch query that carries a slice must, by the time the
        membership predicate is applied, no longer be sliced: the result is a
        query that is NOT sliced.

    (3) The slice the caller asked for must not be lost when it is removed: the
        result still restricts each parent's related objects to exactly the
        same positions the original slice selected (the start offset, and the
        stop limit when one was given). Concretely the result records that
        restriction iff the query was originally sliced, and an upper
        restriction iff the original slice also had a finite stop limit.

The query is modelled as a minimal class carrying only the touched state: the
slice's start/stop marks, the predicates that have been applied to it, and two
opaque carrier fields (lower_bound/upper_bound) in which the result records the
position restriction described in (3). Field names and parent instances are
opaque to this behaviour and are carried as scalars.

The single step that is NOT a plain structural update is applying the
membership predicate. It is modelled as the callee `apply_membership`, which is
well-defined only on a query carrying no slice (its precondition); on success it
grants an unforgeable token (`membership_token`) recording that the predicate
was applied to a non-sliced query. The result of `bounded_prefetch` must carry
that token, so behaviour (1) cannot be satisfied by merely flagging the query —
it must actually route through a successful application on an unsliced query.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class PrefetchQuery:
    def __init__(self, offset_mark: int, limit_mark: Optional[int]) -> None:
        Requires(offset_mark >= 0)
        Requires(limit_mark is None or limit_mark >= 0)
        Ensures(Acc(self.offset_mark) and Acc(self.limit_mark))  # type: ignore
        Ensures(Acc(self.membership_applied))  # type: ignore
        Ensures(Acc(self.lower_bound) and Acc(self.upper_bound))  # type: ignore
        Ensures(self.offset_mark == offset_mark and self.limit_mark is limit_mark)  # type: ignore
        Ensures(self.membership_applied == False)  # type: ignore
        Ensures(self.lower_bound is None and self.upper_bound is None)  # type: ignore
        self.offset_mark = offset_mark          # slice start offset
        self.limit_mark = limit_mark            # slice stop limit (None = unbounded)
        self.membership_applied = False         # has the membership predicate been ANDed on?
        self.lower_bound = None                 # type: Optional[int]  # opaque lower position restriction
        self.upper_bound = None                 # type: Optional[int]  # opaque upper position restriction

# axioms-start
# Unforgeable capability token marking a query the membership predicate was
# applied to by a SUCCESSFUL (non-sliced) application step. It is abstract (no
# body), so nothing can fabricate it by hand; it can be obtained ONLY from the
# Ensures of apply_membership below, which grants it only when the query carried
# no slice at application time. The result of bounded_prefetch must carry this
# token, so a result the application step never produced on an unsliced query
# cannot satisfy the contract — applying the predicate to a still-sliced query
# is exactly the error the issue reports. Provenance + executable soundness
# check: mapping.md / axiom_check.py (G-AX).
@ContractOnly
@Predicate
def membership_token(query: PrefetchQuery) -> bool:
    pass

@ContractOnly
def apply_membership(query: PrefetchQuery) -> None:
    """Apply the membership predicate to the query. Applying a predicate is only
    well-defined while the query has NO slice taken on it: a query with a slice
    taken cannot accept a further predicate (the precondition models exactly
    that constraint). On a successful application it records that the predicate
    was applied AND grants the membership token on the query — the token nothing
    else can fabricate. Provenance + executable soundness check: mapping.md /
    axiom_check.py."""
    Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
    Requires(Acc(query.membership_applied))
    Requires(not is_sliced(query))
    Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
    Ensures(Acc(query.membership_applied))
    Ensures(query.membership_applied == True)
    Ensures(membership_token(query))
# axioms-end

# pure-start
@Pure
def is_sliced(query: PrefetchQuery) -> bool:
    """The query has a slice taken on it: either a non-zero start offset or a
    finite stop limit is present."""
    Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
    return query.offset_mark != 0 or query.limit_mark is not None
# pure-end

def bounded_prefetch(query: PrefetchQuery, member_code: int,
                     instance_count: int) -> PrefetchQuery:
    # pre-conditions-start
    Requires(Acc(query.offset_mark) and Acc(query.limit_mark))
    Requires(Acc(query.membership_applied))
    Requires(Acc(query.lower_bound) and Acc(query.upper_bound))
    Requires(query.offset_mark >= 0)
    Requires(query.limit_mark is None or query.limit_mark >= 0)
    # A freshly assembled prefetch query has no predicate applied yet.
    Requires(query.membership_applied == False)
    Requires(query.lower_bound is None and query.upper_bound is None)
    Requires(instance_count >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
    Ensures(Acc(query.membership_applied))
    Ensures(Acc(query.lower_bound) and Acc(query.upper_bound))
    Ensures(Result() is query)
    # (1) the membership predicate is always applied — and not merely flagged:
    #   the result must carry the unforgeable token that the application step
    #   grants ONLY when the query carried no slice at application time. Because
    #   the token cannot be fabricated, the result must have been produced by a
    #   successful application on an unsliced query (so a still-sliced query was
    #   first un-sliced), which is exactly the desired behaviour.
    Ensures(membership_token(query))
    Ensures(query.membership_applied == True)
    # (3) the position restriction preserves exactly the original slice.
    #   a lower restriction is recorded iff the query was originally sliced,
    #   and it carries the original start offset.
    Ensures(Old(is_sliced(query)) == (query.lower_bound is not None))
    Ensures(Implies(query.lower_bound is not None,
                    query.lower_bound == Old(query.offset_mark)))
    #   an upper restriction is recorded iff the query was originally sliced AND
    #   had a finite stop limit, and it carries that limit.
    Ensures((Old(is_sliced(query)) and Old(query.limit_mark) is not None)
            == (query.upper_bound is not None))
    Ensures(Implies(query.upper_bound is not None,
                    query.upper_bound == Old(query.limit_mark)))
    # (2) the resulting query is no longer sliced (so the predicate is applicable).
    Ensures(not is_sliced(query))
    Ensures(query.offset_mark == 0 and query.limit_mark is None)
    # post-conditions-end
    # impl-start
    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        # record the start offset as the lower position restriction
        query.lower_bound = low
        # record a finite stop limit as the upper position restriction
        if high is not None:
            query.upper_bound = high
        # remove the slice so the membership predicate can be applied
        query.offset_mark = 0
        query.limit_mark = None
    # at this point the query is no longer sliced; the membership predicate is
    # applicable and is ANDed on (apply_membership requires not is_sliced).
    apply_membership(query)
    return query
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Ran 9 distinct same-spec wrong impls through `adversary weakness nagini django__django-15957` (project root, python python; verifications run concurrently in batches of <=3 JVM+Z3). Every attack returned exit 2 = NOT-A-COUNTEREXAMPLE (same-spec held, verification FAILED) => NO CANDIDATE (no verifying wrong impl), so there is no faithful refined patch to materialize/run through resolve. Positive control (verbatim model.py impl) verifies (nagini_verify.sh exit 0, 13.6s). same-spec explicitly confirmed exit 0 on atk_1/atk_2/atk_8; negative control (spectamper.py, instance_count>=1) correctly fails same-spec (exit 1), showing the same-spec gate discriminates.

Attack roster (impl-region-only edits; axioms/@Pure/Requires/Ensures byte-identical):
- atk_1 prepatch bug: `apply_membership(query); return query` — fails apply_membership's `not is_sliced` precond + missing token/bounds/not-sliced posts. Reproduces the recorded prepatch failure (model_prepatch.py:157). exit 2.
- atk_2 ungrounded-oracle/flag-echo: full slice->bound + clear, but sets `membership_applied=True` instead of calling apply_membership => cannot obtain unforgeable membership_token(query) post. exit 2. (Directly exercises the load-bearing token cheat-closure.)
- atk_3 boundary/value: lower_bound=low+1 => violates `lower_bound==Old(offset_mark)`. exit 2.
- atk_4 partial-domain: forgets `limit_mark=None` => still sliced when finite limit => apply_membership precond + not-sliced post fail. exit 2.
- atk_5 control-flow-effect: apply_membership BEFORE clearing slice => precond violated on sliced query. exit 2.
- atk_6 presence-condition: records lower_bound unconditionally => violates `Old(is_sliced)==(lower_bound is not None)` on unsliced input. exit 2.
- atk_7 read-after-clear: clears marks then reads (records 0/None) => wrong bound values + presence. exit 2.
- atk_8 boundary limit-only slice: records lower_bound only when offset!=0, missing the offset==0/finite-limit slice => presence-iff-sliced violation. exit 2.
- atk_9 value-mixup: swaps limit into lower_bound and offset into upper_bound => value-equality posts fail. exit 2.

Refinement audit: all legs A1-A9/A8b are R / I / A-consumed / A-reference — NO kind-3. The two A-consumed axioms (apply_membership modeling the UNCHANGED QuerySet.filter/can_filter raise-on-sliced guard; membership_token abstract unforgeable capability) model an unchanged callee, not the function under change; the A-reference deep model (structural slice->bound translation) is validated == the real _filter_prefetch_queryset + Query slice machinery by axiom_check.py (G-AX pass, apply_gold=true, 5 helper + 6 is_sliced/clear_limits cases). Field bijection (offset_mark<->low_mark, limit_mark<->high_mark), strict-lower GreaterThan, inclusive-upper LessThanOrEqual-iff-finite, clear_limits, and filter-vs-raise all correspond to the gold hunk. The membership_token closes the directive-8 flag-echo cheat, empirically confirmed by atk_2 failing to verify. G-EQ SOUND: >=5 (9) distinct same-spec attacks run, none is a verifying counterexample; positive control verifies.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) verdict: FAITHFUL. The bundle models the gold-patch helper _filter_prefetch_queryset(queryset, field_name, instances) as bounded_prefetch. All checks run independently against the real repo at base_commit f387d024fc (worktree with the gold patch applied; Django 4.2.0a).

(1) same-spec on an identity copy of model.py => SAME (exit 0): the spec region is byte-identical (not tampered).

(2) nagini_verify.sh model.py => 'Verification successful' (13.68s): positive control verifies.
 axiom_check.py driven with against the REAL patched _filter_prefetch_queryset => G-AX OK (exit 0) across slice patterns (0,None),,(1,None),, and is_sliced/clear_limits cases.

(4) meta.json G-CONF: 100288 inputs, 0 disagreements, seed 15957.

(5) My own differential probe over 11 slice patterns including edge cases [0:0] (high=0), [10:], [3:], [0:10], [4:7] driving the real gold helper: EVERY modeled postcondition matched the real callee on every input, 0 divergences: membership predicate ALWAYS ANDed (membership_applied/token); lower_bound present iff Old(is_sliced) with value == low_mark (offset_mark); upper_bound present iff sliced AND finite high with value == high_mark (limit_mark); slice cleared so is_sliced becomes false afterward (marks reset to 0/None); model is_sliced (offset_mark!=0 or limit_mark is not None) agrees with real Query.is_sliced; and QuerySet.filter raises TypeError on a sliced query while succeeding on an unsliced one (validating apply_membership's Requires(not is_sliced) + token-on-unsliced-path).

The only representational difference — the model asserts Result() is query (mutates the carrier in place) whereas the real helper returns a queryset.filter() clone (out is qs == False) — is a carrier-identity abstraction, not a behavioral divergence: which bounds are recorded, membership application, and the unsliced result are all identical. No input found where the modeled function disagrees with the real repo, and the gold patch satisfies the spec on every tested input, so the spec is not too strong. (Note: G-PANEL-1 spec-too-WEAK is a separate attacker role and orthogonal to this too-strong/drift assessment.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). Independent gold-reconstruction judgment confirms NO-LEAKAGE:

Public problem_statement already discloses: prefetch fails on sliced querysets with 'AssertionError: Cannot filter a query once a slice has been taken', and the goal is to make slicing work in prefetch (return N example objects per parent).

The gold edit's DISTINCTIVE machinery — the new helper `_filter_prefetch_queryset`, `Window(RowNumber(), partition_by=..., order_by=...)`, `GreaterThan(window, low_mark)`, `LessThanOrEqual(window, high_mark)`, `clear_limits()`, `queryset.query.low_mark/high_mark` — appears NOWHERE in the spec view. The view uses only abstracted carrier vocabulary (offset_mark/limit_mark/lower_bound/upper_bound/membership_token/apply_membership). No diff markers, no patched file path (related_descriptors.py), no patched module dotted path, no bug/fix narration.

Behaviours (1)-(3) restate only the abstract correctness obligation that ANY correct fix must meet (predicate always applied; un-slice before applying the predicate; preserve the slice's per-position restriction), directly implied by the public premise. They do NOT reveal the gold's specific row-number Window approach — a solver must still independently discover that Django needs a RowNumber window predicate per partition to preserve slice positions.

The only overlapping token is `is_sliced`, which also occurs in a gold-added line (`queryset.query.is_sliced`). But it is a generic slice-presence predicate directly entailed by the problem statement's own 'sliced querysets'/'slice has been taken' wording; it localizes no edit, is not a def/class symbol introduced by the patch, and reveals nothing about the distinctive mechanism. Not a leak.

The spec view goes no further than public problem_statement + inherent correctness requirement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).