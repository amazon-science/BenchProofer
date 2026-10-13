# P2 adversarial audit — django__django-16661

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
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(model_has_auto_identity) == len(prev_is_relation))
     Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
     Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
@@ -185,7 +183,6 @@
                                                  ToSeq(model_has_auto_identity).drop(i),
                                                  ToSeq(segment_targets_prior_hop).drop(i),
                                                  i == 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         # The facts of segment i-1 (the new head); list index ties to PSeq index.
         pr = prev_is_relation[i - 1]
@@ -203,10 +200,7 @@
         if i - 1 == 0:
             keep = True  # type: bool
         else:
-            keep = keep_at(pr, field_is_parent_link[i - 1],
-                           field_is_auto_identity[i - 1],
-                           model_has_auto_identity[i - 1],
-                           segment_targets_prior_hop[i - 1])
+            keep = pr and not field_is_prior_hop_target[i - 1]
         if keep:
             result = [1] + result
         else:
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(model_has_auto_identity) == len(prev_is_relation))
     Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
     Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
@@ -185,7 +183,6 @@
                                                  ToSeq(model_has_auto_identity).drop(i),
                                                  ToSeq(segment_targets_prior_hop).drop(i),
                                                  i == 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         # The facts of segment i-1 (the new head); list index ties to PSeq index.
         pr = prev_is_relation[i - 1]
@@ -200,13 +197,7 @@
         Assert(ToSeq(field_is_auto_identity).drop(i - 1).drop(1) == ToSeq(field_is_auto_identity).drop(i))
         Assert(ToSeq(model_has_auto_identity).drop(i - 1).drop(1) == ToSeq(model_has_auto_identity).drop(i))
         Assert(ToSeq(segment_targets_prior_hop).drop(i - 1).drop(1) == ToSeq(segment_targets_prior_hop).drop(i))
-        if i - 1 == 0:
-            keep = True  # type: bool
-        else:
-            keep = keep_at(pr, field_is_parent_link[i - 1],
-                           field_is_auto_identity[i - 1],
-                           model_has_auto_identity[i - 1],
-                           segment_targets_prior_hop[i - 1])
+        keep = True  # type: bool
         if keep:
             result = [1] + result
         else:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(model_has_auto_identity) == len(prev_is_relation))
     Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
     Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
@@ -185,7 +183,6 @@
                                                  ToSeq(model_has_auto_identity).drop(i),
                                                  ToSeq(segment_targets_prior_hop).drop(i),
                                                  i == 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         # The facts of segment i-1 (the new head); list index ties to PSeq index.
         pr = prev_is_relation[i - 1]
@@ -203,10 +200,7 @@
         if i - 1 == 0:
             keep = True  # type: bool
         else:
-            keep = keep_at(pr, field_is_parent_link[i - 1],
-                           field_is_auto_identity[i - 1],
-                           model_has_auto_identity[i - 1],
-                           segment_targets_prior_hop[i - 1])
+            keep = False
         if keep:
             result = [1] + result
         else:
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(model_has_auto_identity) == len(prev_is_relation))
     Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
     Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
@@ -185,7 +183,6 @@
                                                  ToSeq(model_has_auto_identity).drop(i),
                                                  ToSeq(segment_targets_prior_hop).drop(i),
                                                  i == 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         # The facts of segment i-1 (the new head); list index ties to PSeq index.
         pr = prev_is_relation[i - 1]
@@ -203,10 +200,10 @@
         if i - 1 == 0:
             keep = True  # type: bool
         else:
-            keep = keep_at(pr, field_is_parent_link[i - 1],
-                           field_is_auto_identity[i - 1],
-                           model_has_auto_identity[i - 1],
-                           segment_targets_prior_hop[i - 1])
+            keep = (pr
+                    and not field_is_auto_identity[i - 1]
+                    and ((not model_has_auto_identity[i - 1])
+                         or (not segment_targets_prior_hop[i - 1])))
         if keep:
             result = [1] + result
         else:
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(model_has_auto_identity) == len(prev_is_relation))
     Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
     Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
@@ -185,7 +183,6 @@
                                                  ToSeq(model_has_auto_identity).drop(i),
                                                  ToSeq(segment_targets_prior_hop).drop(i),
                                                  i == 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         # The facts of segment i-1 (the new head); list index ties to PSeq index.
         pr = prev_is_relation[i - 1]
@@ -203,10 +200,10 @@
         if i - 1 == 0:
             keep = True  # type: bool
         else:
-            keep = keep_at(pr, field_is_parent_link[i - 1],
-                           field_is_auto_identity[i - 1],
-                           model_has_auto_identity[i - 1],
-                           segment_targets_prior_hop[i - 1])
+            keep = (pr
+                    and not field_is_parent_link[i - 1]
+                    and ((not model_has_auto_identity[i - 1])
+                         or (not segment_targets_prior_hop[i - 1])))
         if keep:
             result = [1] + result
         else:
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(model_has_auto_identity) == len(prev_is_relation))
     Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
     Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
@@ -185,7 +183,6 @@
                                                  ToSeq(model_has_auto_identity).drop(i),
                                                  ToSeq(segment_targets_prior_hop).drop(i),
                                                  i == 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         # The facts of segment i-1 (the new head); list index ties to PSeq index.
         pr = prev_is_relation[i - 1]
@@ -203,10 +200,11 @@
         if i - 1 == 0:
             keep = True  # type: bool
         else:
-            keep = keep_at(pr, field_is_parent_link[i - 1],
-                           field_is_auto_identity[i - 1],
-                           model_has_auto_identity[i - 1],
-                           segment_targets_prior_hop[i - 1])
+            keep = (pr
+                    and not field_is_parent_link[i - 1]
+                    and not field_is_auto_identity[i - 1]
+                    and ((not model_has_auto_identity[i - 1])
+                         and (not segment_targets_prior_hop[i - 1])))
         if keep:
             result = [1] + result
         else:
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(model_has_auto_identity) == len(prev_is_relation))
     Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
     Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
@@ -185,7 +183,6 @@
                                                  ToSeq(model_has_auto_identity).drop(i),
                                                  ToSeq(segment_targets_prior_hop).drop(i),
                                                  i == 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         # The facts of segment i-1 (the new head); list index ties to PSeq index.
         pr = prev_is_relation[i - 1]
@@ -203,10 +200,7 @@
         if i - 1 == 0:
             keep = True  # type: bool
         else:
-            keep = keep_at(pr, field_is_parent_link[i - 1],
-                           field_is_auto_identity[i - 1],
-                           model_has_auto_identity[i - 1],
-                           segment_targets_prior_hop[i - 1])
+            keep = pr and segment_targets_prior_hop[i - 1]
         if keep:
             result = [1] + result
         else:
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16661.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An administrative permission check walks a multi-segment relation path
  (a sequence of segments joined by a separator) one segment at a time. Each
  segment resolves, against the model reached so far, to a field carrying a
  small bundle of structural facts. The walk accumulates the subsequence of
  segments that begin a NEW relational hop -- the "retained" segments -- and a
  later membership test on that retained subsequence decides whether the whole
  path is an allowed filter.

  A segment is retained exactly when it is the FIRST segment, or when the
  segment immediately before it reached a relation AND the segment's own field
  begins a genuinely new relational hop rather than naming a value already
  reachable from the prior model directly. The only segments treated as
  already-reachable are those whose field is one of the prior model's
  concrete-inheritance parent links (the case the issue identifies as wrongly
  conflated with a foreign key used as a primary key). A relation segment that
  merely SERVES AS the reached model's primary key is a genuinely new hop, not a
  concrete-inheritance shortcut, and must be retained.

  The decisive consequence the specification pins: when an intermediate segment
  resolves to a relation field that is the reached model's primary key but is
  NOT a concrete-inheritance parent link, that segment IS retained -- so the
  full path is preserved and the membership test sees the complete relation
  path (rather than the spuriously shortened path the issue reports).

The segments are modelled as parallel `List[bool]` of per-segment structural
facts (a faithful projection of the field bundle each segment resolves to); the
retention outcome is carried as a `List[int]` retention mask -- one flag per
segment, 1 iff that segment is retained -- pinned by the pure front-recursive
fold `retained_mask`. No callee is axiomatized: the retention rule is pure
decision logic over the per-segment facts, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The retention rule is pure per-segment decision logic over
# already-resolved structural facts about each segment (carried as the per-
# segment boolean vectors below: whether the prior segment reached a relation,
# and the structural properties that decide whether this segment's field begins
# a genuinely new relational hop). How each segment resolves to those facts is
# unchanged by the behaviour under specification and is not modelled. The rule
# is spelled out deeply, not hidden behind an axiom.
# axioms-end


# pure-start
@Pure
def keep_at(prev_is_relation: bool,
            field_is_parent_link: bool,
            field_is_auto_identity: bool,
            model_has_auto_identity: bool,
            segment_targets_prior_hop: bool) -> bool:
    """Whether a NON-first segment begins a new relational hop and is therefore
    retained, given the structural facts resolved for it.

    Retained exactly when the prior segment reached a relation and the segment's
    field begins a genuinely new relational hop -- i.e. it is not one of the
    prior model's concrete-inheritance parent links and does not merely name a
    value already reachable from the prior model directly. A relation segment
    that serves as the reached model's primary key is a new hop, not such a
    shortcut, and is retained. The boolean facts below are the projection of
    that decision (one structural fact per conjunct)."""
    return (prev_is_relation
            and not field_is_parent_link
            and not field_is_auto_identity
            and ((not model_has_auto_identity)
                 or (not segment_targets_prior_hop)))


@Pure
def retained_mask(prev_is_relation: PSeq[bool],
                  field_is_parent_link: PSeq[bool],
                  field_is_auto_identity: PSeq[bool],
                  model_has_auto_identity: PSeq[bool],
                  segment_targets_prior_hop: PSeq[bool],
                  first: bool) -> PSeq[int]:
    """The retention mask over the suffix the argument sequences represent:
    element k is 1 iff that suffix's segment k is retained, else 0. Front-
    recursive on the head (structural `.drop(1)`) so a single unfold is
    available per loop step. `first` marks whether the head is the very first
    segment of the whole path (always retained); every non-first segment is
    retained exactly per `keep_at` on its resolved facts."""
    Requires(len(field_is_parent_link) == len(prev_is_relation))
    Requires(len(field_is_auto_identity) == len(prev_is_relation))
    Requires(len(model_has_auto_identity) == len(prev_is_relation))
    Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
    Ensures(len(Result()) == len(prev_is_relation))
    if len(prev_is_relation) == 0:
        return PSeq(0).take(0)
    rest = retained_mask(prev_is_relation.drop(1), field_is_parent_link.drop(1),
                         field_is_auto_identity.drop(1),
                         model_has_auto_identity.drop(1),
                         segment_targets_prior_hop.drop(1), False)
    if first or keep_at(prev_is_relation[0], field_is_parent_link[0],
                        field_is_auto_identity[0], model_has_auto_identity[0],
                        segment_targets_prior_hop[0]):
        return PSeq(1) + rest
    return PSeq(0) + rest
# pure-end


def retained_segments(prev_is_relation: List[bool],
                      field_is_parent_link: List[bool],
                      field_is_auto_identity: List[bool],
                      model_has_auto_identity: List[bool],
                      segment_targets_prior_hop: List[bool],
                      field_is_prior_hop_target: List[bool]) -> List[int]:
    # pre-conditions-start
    # All per-segment fact vectors are read-only and equinumerous with the path.
    Requires(Acc(list_pred(prev_is_relation), 1 / 2))
    Requires(Acc(list_pred(field_is_parent_link), 1 / 2))
    Requires(Acc(list_pred(field_is_auto_identity), 1 / 2))
    Requires(Acc(list_pred(model_has_auto_identity), 1 / 2))
    Requires(Acc(list_pred(segment_targets_prior_hop), 1 / 2))
    Requires(Acc(list_pred(field_is_prior_hop_target), 1 / 2))
    Requires(len(field_is_parent_link) == len(prev_is_relation))
    Requires(len(field_is_auto_identity) == len(prev_is_relation))
    Requires(len(model_has_auto_identity) == len(prev_is_relation))
    Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
    Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
    Ensures(Acc(list_pred(field_is_parent_link), 1 / 2))
    Ensures(Acc(list_pred(field_is_auto_identity), 1 / 2))
    Ensures(Acc(list_pred(model_has_auto_identity), 1 / 2))
    Ensures(Acc(list_pred(segment_targets_prior_hop), 1 / 2))
    Ensures(Acc(list_pred(field_is_prior_hop_target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the retention mask: one flag per path segment, in order.
    Ensures(len(Result()) == len(prev_is_relation))
    # The fact vectors stay equinumerous as pure sequences (read-only).
    Ensures(len(ToSeq(field_is_parent_link)) == len(ToSeq(prev_is_relation)))
    Ensures(len(ToSeq(field_is_auto_identity)) == len(ToSeq(prev_is_relation)))
    Ensures(len(ToSeq(model_has_auto_identity)) == len(ToSeq(prev_is_relation)))
    Ensures(len(ToSeq(segment_targets_prior_hop)) == len(ToSeq(prev_is_relation)))
    # The retention mask is exactly the per-segment retention fold over the
    # whole path; the head is the first segment (`first=True`).
    Ensures(ToSeq(Result()) == retained_mask(ToSeq(prev_is_relation),
                                             ToSeq(field_is_parent_link),
                                             ToSeq(field_is_auto_identity),
                                             ToSeq(model_has_auto_identity),
                                             ToSeq(segment_targets_prior_hop),
                                             True))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    n = len(prev_is_relation)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(prev_is_relation), 1 / 2))
        Invariant(Acc(list_pred(field_is_parent_link), 1 / 2))
        Invariant(Acc(list_pred(field_is_auto_identity), 1 / 2))
        Invariant(Acc(list_pred(model_has_auto_identity), 1 / 2))
        Invariant(Acc(list_pred(segment_targets_prior_hop), 1 / 2))
        Invariant(Acc(list_pred(field_is_prior_hop_target), 1 / 2))
        Invariant(len(field_is_parent_link) == len(prev_is_relation))
        Invariant(len(field_is_auto_identity) == len(prev_is_relation))
        Invariant(len(model_has_auto_identity) == len(prev_is_relation))
        Invariant(len(segment_targets_prior_hop) == len(prev_is_relation))
        Invariant(n == len(prev_is_relation))
        Invariant(len(ToSeq(prev_is_relation)) == n)
        Invariant(len(ToSeq(field_is_parent_link)) == n)
        Invariant(len(ToSeq(field_is_auto_identity)) == n)
        Invariant(len(ToSeq(model_has_auto_identity)) == n)
        Invariant(len(ToSeq(segment_targets_prior_hop)) == n)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n - i)
        # `result` is the retention mask over the suffix from segment i: its head
        # is segment i, the first segment of the whole path only when i == 0.
        Invariant(ToSeq(result) == retained_mask(ToSeq(prev_is_relation).drop(i),
                                                 ToSeq(field_is_parent_link).drop(i),
                                                 ToSeq(field_is_auto_identity).drop(i),
                                                 ToSeq(model_has_auto_identity).drop(i),
                                                 ToSeq(segment_targets_prior_hop).drop(i),
                                                 i == 0))
        # invariants-end
        # The facts of segment i-1 (the new head); list index ties to PSeq index.
        pr = prev_is_relation[i - 1]
        Assert(ToSeq(prev_is_relation).drop(i - 1)[0] == pr)
        Assert(ToSeq(field_is_parent_link).drop(i - 1)[0] == field_is_parent_link[i - 1])
        Assert(ToSeq(field_is_auto_identity).drop(i - 1)[0] == field_is_auto_identity[i - 1])
        Assert(ToSeq(model_has_auto_identity).drop(i - 1)[0] == model_has_auto_identity[i - 1])
        Assert(ToSeq(segment_targets_prior_hop).drop(i - 1)[0] == segment_targets_prior_hop[i - 1])
        # drop(i-1) is the head (segment i-1) followed by drop(i).
        Assert(ToSeq(prev_is_relation).drop(i - 1).drop(1) == ToSeq(prev_is_relation).drop(i))
        Assert(ToSeq(field_is_parent_link).drop(i - 1).drop(1) == ToSeq(field_is_parent_link).drop(i))
        Assert(ToSeq(field_is_auto_identity).drop(i - 1).drop(1) == ToSeq(field_is_auto_identity).drop(i))
        Assert(ToSeq(model_has_auto_identity).drop(i - 1).drop(1) == ToSeq(model_has_auto_identity).drop(i))
        Assert(ToSeq(segment_targets_prior_hop).drop(i - 1).drop(1) == ToSeq(segment_targets_prior_hop).drop(i))
        if i - 1 == 0:
            keep = True  # type: bool
        else:
            keep = keep_at(pr, field_is_parent_link[i - 1],
                           field_is_auto_identity[i - 1],
                           model_has_auto_identity[i - 1],
                           segment_targets_prior_hop[i - 1])
        if keep:
            result = [1] + result
        else:
            result = [0] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 distinct same-spec wrong impls, all edit ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; same-spec exit 0 for all 7 + positive control). All 7 come back weakness exit=2 with genuine 'verification failed' (NOT timeout/infra: outputs grepped, no timeout/124/inconclusive markers). No CANDIDATE arose, so there is no faithful refined patch to materialize/resolve.

Commands (env: swebench-lean venv, SBU_BENCHMARK_DIR=benchmark-verified):
python -m swebench_unified.adversary same-spec nagini django__django-16661 <atk> -> exit 0 (all 7 + pos)
python -m swebench_unified.adversary weakness nagini django__django-16661 <atk> -> exit 2 (all 7)
bash scripts/nagini_verify.sh pos_control.py -> exit 0 ('Verification successful', 22.12s)

Attack taxonomy: atk_1 = prepatch bug (keep = pr and not field_is_prior_hop_target[i-1]) — PREPATCH REPRODUCED, fails verify (the [1,0,1] vs [1,1,1] FK-as-PK witness). atk_2 = ungrounded-oracle echo (always keep=True). atk_3 = control-flow-effect (keep only first segment, else False). atk_4 = partial-domain (drop field_is_parent_link conjunct). atk_5 = partial-domain (drop field_is_auto_identity conjunct). atk_6 = boundary/logic (AND instead of OR in the auto-identity/targets-prior guard). atk_7 = ungrounded-oracle echo (keep iff segment_targets_prior_hop). Each is behaviourally distinct from the gold on some fact combination and each is REJECTED by the spec.

Why SOUND is expected structurally: postcondition ToSeq(Result()) == retained_mask(ToSeq(prev_is_relation), ..., True) fully pins the output mask over the ENTIRE boolean fact domain. Preconditions restrict only length-equality + Acc(list_pred,1/2) read-only permission — no domain restriction — so the fact vectors range over all reachable combinations. Any verifying impl must equal retained_mask everywhere.

Refinement audit (A-legs focus): axioms region is empty — NO A-consumed, NO A-reference axioms. G-AX vacuous. keep_at/retained_mask model the retention rule DEEPLY. All operation legs are R or I; no kind-3 (unexpressible-changed-op). Term-for-term correspondence to gold hunk (options.py:467-471) verified: prev_is_relation<->prev_field.is_relation; not field_is_parent_link<->field not in model._meta.parents.values(); not field_is_auto_identity<->field is not model._meta.auto_field; (not model_has_auto_identity or not segment_targets_prior_hop)<->(auto_field is None or part not in to_fields); first-segment always-retain<->'not prev_field' disjunct. Unchanged membership test is an I-step deterministic in the mask (model<->patch correspondence holds). No divergence found.

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
"""Twin-artifact model for django__django-16661.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An administrative permission check walks a multi-segment relation path
  (a sequence of segments joined by a separator) one segment at a time. Each
  segment resolves, against the model reached so far, to a field carrying a
  small bundle of structural facts. The walk accumulates the subsequence of
  segments that begin a NEW relational hop -- the "retained" segments -- and a
  later membership test on that retained subsequence decides whether the whole
  path is an allowed filter.

  A segment is retained exactly when it is the FIRST segment, or when the
  segment immediately before it reached a relation AND the segment's own field
  begins a genuinely new relational hop rather than naming a value already
  reachable from the prior model directly. The only segments treated as
  already-reachable are those whose field is one of the prior model's
  concrete-inheritance parent links (the case the issue identifies as wrongly
  conflated with a foreign key used as a primary key). A relation segment that
  merely SERVES AS the reached model's primary key is a genuinely new hop, not a
  concrete-inheritance shortcut, and must be retained.

  The decisive consequence the specification pins: when an intermediate segment
  resolves to a relation field that is the reached model's primary key but is
  NOT a concrete-inheritance parent link, that segment IS retained -- so the
  full path is preserved and the membership test sees the complete relation
  path (rather than the spuriously shortened path the issue reports).

The segments are modelled as parallel `List[bool]` of per-segment structural
facts (a faithful projection of the field bundle each segment resolves to); the
retention outcome is carried as a `List[int]` retention mask -- one flag per
segment, 1 iff that segment is retained -- pinned by the pure front-recursive
fold `retained_mask`. No callee is axiomatized: the retention rule is pure
decision logic over the per-segment facts, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The retention rule is pure per-segment decision logic over
# already-resolved structural facts about each segment (carried as the per-
# segment boolean vectors below: whether the prior segment reached a relation,
# and the structural properties that decide whether this segment's field begins
# a genuinely new relational hop). How each segment resolves to those facts is
# unchanged by the behaviour under specification and is not modelled. The rule
# is spelled out deeply, not hidden behind an axiom.
# axioms-end


# pure-start
@Pure
def keep_at(prev_is_relation: bool,
            field_is_parent_link: bool,
            field_is_auto_identity: bool,
            model_has_auto_identity: bool,
            segment_targets_prior_hop: bool) -> bool:
    """Whether a NON-first segment begins a new relational hop and is therefore
    retained, given the structural facts resolved for it.

    Retained exactly when the prior segment reached a relation and the segment's
    field begins a genuinely new relational hop -- i.e. it is not one of the
    prior model's concrete-inheritance parent links and does not merely name a
    value already reachable from the prior model directly. A relation segment
    that serves as the reached model's primary key is a new hop, not such a
    shortcut, and is retained. The boolean facts below are the projection of
    that decision (one structural fact per conjunct)."""
    return (prev_is_relation
            and not field_is_parent_link
            and not field_is_auto_identity
            and ((not model_has_auto_identity)
                 or (not segment_targets_prior_hop)))


@Pure
def retained_mask(prev_is_relation: PSeq[bool],
                  field_is_parent_link: PSeq[bool],
                  field_is_auto_identity: PSeq[bool],
                  model_has_auto_identity: PSeq[bool],
                  segment_targets_prior_hop: PSeq[bool],
                  first: bool) -> PSeq[int]:
    """The retention mask over the suffix the argument sequences represent:
    element k is 1 iff that suffix's segment k is retained, else 0. Front-
    recursive on the head (structural `.drop(1)`) so a single unfold is
    available per loop step. `first` marks whether the head is the very first
    segment of the whole path (always retained); every non-first segment is
    retained exactly per `keep_at` on its resolved facts."""
    Requires(len(field_is_parent_link) == len(prev_is_relation))
    Requires(len(field_is_auto_identity) == len(prev_is_relation))
    Requires(len(model_has_auto_identity) == len(prev_is_relation))
    Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
    Ensures(len(Result()) == len(prev_is_relation))
    if len(prev_is_relation) == 0:
        return PSeq(0).take(0)
    rest = retained_mask(prev_is_relation.drop(1), field_is_parent_link.drop(1),
                         field_is_auto_identity.drop(1),
                         model_has_auto_identity.drop(1),
                         segment_targets_prior_hop.drop(1), False)
    if first or keep_at(prev_is_relation[0], field_is_parent_link[0],
                        field_is_auto_identity[0], model_has_auto_identity[0],
                        segment_targets_prior_hop[0]):
        return PSeq(1) + rest
    return PSeq(0) + rest
# pure-end


def retained_segments(prev_is_relation: List[bool],
                      field_is_parent_link: List[bool],
                      field_is_auto_identity: List[bool],
                      model_has_auto_identity: List[bool],
                      segment_targets_prior_hop: List[bool],
                      field_is_prior_hop_target: List[bool]) -> List[int]:
    # pre-conditions-start
    # All per-segment fact vectors are read-only and equinumerous with the path.
    Requires(Acc(list_pred(prev_is_relation), 1 / 2))
    Requires(Acc(list_pred(field_is_parent_link), 1 / 2))
    Requires(Acc(list_pred(field_is_auto_identity), 1 / 2))
    Requires(Acc(list_pred(model_has_auto_identity), 1 / 2))
    Requires(Acc(list_pred(segment_targets_prior_hop), 1 / 2))
    Requires(Acc(list_pred(field_is_prior_hop_target), 1 / 2))
    Requires(len(field_is_parent_link) == len(prev_is_relation))
    Requires(len(field_is_auto_identity) == len(prev_is_relation))
    Requires(len(model_has_auto_identity) == len(prev_is_relation))
    Requires(len(segment_targets_prior_hop) == len(prev_is_relation))
    Requires(len(field_is_prior_hop_target) == len(prev_is_relation))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prev_is_relation), 1 / 2))
    Ensures(Acc(list_pred(field_is_parent_link), 1 / 2))
    Ensures(Acc(list_pred(field_is_auto_identity), 1 / 2))
    Ensures(Acc(list_pred(model_has_auto_identity), 1 / 2))
    Ensures(Acc(list_pred(segment_targets_prior_hop), 1 / 2))
    Ensures(Acc(list_pred(field_is_prior_hop_target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the retention mask: one flag per path segment, in order.
    Ensures(len(Result()) == len(prev_is_relation))
    # The fact vectors stay equinumerous as pure sequences (read-only).
    Ensures(len(ToSeq(field_is_parent_link)) == len(ToSeq(prev_is_relation)))
    Ensures(len(ToSeq(field_is_auto_identity)) == len(ToSeq(prev_is_relation)))
    Ensures(len(ToSeq(model_has_auto_identity)) == len(ToSeq(prev_is_relation)))
    Ensures(len(ToSeq(segment_targets_prior_hop)) == len(ToSeq(prev_is_relation)))
    # The retention mask is exactly the per-segment retention fold over the
    # whole path; the head is the first segment (`first=True`).
    Ensures(ToSeq(Result()) == retained_mask(ToSeq(prev_is_relation),
                                             ToSeq(field_is_parent_link),
                                             ToSeq(field_is_auto_identity),
                                             ToSeq(model_has_auto_identity),
                                             ToSeq(segment_targets_prior_hop),
                                             True))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    n = len(prev_is_relation)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(prev_is_relation), 1 / 2))
        Invariant(Acc(list_pred(field_is_parent_link), 1 / 2))
        Invariant(Acc(list_pred(field_is_auto_identity), 1 / 2))
        Invariant(Acc(list_pred(model_has_auto_identity), 1 / 2))
        Invariant(Acc(list_pred(segment_targets_prior_hop), 1 / 2))
        Invariant(Acc(list_pred(field_is_prior_hop_target), 1 / 2))
        Invariant(len(field_is_parent_link) == len(prev_is_relation))
        Invariant(len(field_is_auto_identity) == len(prev_is_relation))
        Invariant(len(model_has_auto_identity) == len(prev_is_relation))
        Invariant(len(segment_targets_prior_hop) == len(prev_is_relation))
        Invariant(n == len(prev_is_relation))
        Invariant(len(ToSeq(prev_is_relation)) == n)
        Invariant(len(ToSeq(field_is_parent_link)) == n)
        Invariant(len(ToSeq(field_is_auto_identity)) == n)
        Invariant(len(ToSeq(model_has_auto_identity)) == n)
        Invariant(len(ToSeq(segment_targets_prior_hop)) == n)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n - i)
        # `result` is the retention mask over the suffix from segment i: its head
        # is segment i, the first segment of the whole path only when i == 0.
        Invariant(ToSeq(result) == retained_mask(ToSeq(prev_is_relation).drop(i),
                                                 ToSeq(field_is_parent_link).drop(i),
                                                 ToSeq(field_is_auto_identity).drop(i),
                                                 ToSeq(model_has_auto_identity).drop(i),
                                                 ToSeq(segment_targets_prior_hop).drop(i),
                                                 i == 0))
        # invariants-end
        # The facts of segment i-1 (the new head); list index ties to PSeq index.
        pr = prev_is_relation[i - 1]
        Assert(ToSeq(prev_is_relation).drop(i - 1)[0] == pr)
        Assert(ToSeq(field_is_parent_link).drop(i - 1)[0] == field_is_parent_link[i - 1])
        Assert(ToSeq(field_is_auto_identity).drop(i - 1)[0] == field_is_auto_identity[i - 1])
        Assert(ToSeq(model_has_auto_identity).drop(i - 1)[0] == model_has_auto_identity[i - 1])
        Assert(ToSeq(segment_targets_prior_hop).drop(i - 1)[0] == segment_targets_prior_hop[i - 1])
        # drop(i-1) is the head (segment i-1) followed by drop(i).
        Assert(ToSeq(prev_is_relation).drop(i - 1).drop(1) == ToSeq(prev_is_relation).drop(i))
        Assert(ToSeq(field_is_parent_link).drop(i - 1).drop(1) == ToSeq(field_is_parent_link).drop(i))
        Assert(ToSeq(field_is_auto_identity).drop(i - 1).drop(1) == ToSeq(field_is_auto_identity).drop(i))
        Assert(ToSeq(model_has_auto_identity).drop(i - 1).drop(1) == ToSeq(model_has_auto_identity).drop(i))
        Assert(ToSeq(segment_targets_prior_hop).drop(i - 1).drop(1) == ToSeq(segment_targets_prior_hop).drop(i))
        if i - 1 == 0:
            keep = True  # type: bool
        else:
            keep = keep_at(pr, field_is_parent_link[i - 1],
                           field_is_auto_identity[i - 1],
                           model_has_auto_identity[i - 1],
                           segment_targets_prior_hop[i - 1])
        if keep:
            result = [1] + result
        else:
            result = [0] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 distinct same-spec wrong impls, all edit ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; same-spec exit 0 for all 7 + positive control). All 7 come back weakness exit=2 with genuine 'verification failed' (NOT timeout/infra: outputs grepped, no timeout/124/inconclusive markers). No CANDIDATE arose, so there is no faithful refined patch to materialize/resolve.

Commands (env: swebench-lean venv, SBU_BENCHMARK_DIR=benchmark-verified):
python -m swebench_unified.adversary same-spec nagini django__django-16661 <atk> -> exit 0 (all 7 + pos)
python -m swebench_unified.adversary weakness nagini django__django-16661 <atk> -> exit 2 (all 7)
bash scripts/nagini_verify.sh pos_control.py -> exit 0 ('Verification successful', 22.12s)

Attack taxonomy: atk_1 = prepatch bug (keep = pr and not field_is_prior_hop_target[i-1]) — PREPATCH REPRODUCED, fails verify (the [1,0,1] vs [1,1,1] FK-as-PK witness). atk_2 = ungrounded-oracle echo (always keep=True). atk_3 = control-flow-effect (keep only first segment, else False). atk_4 = partial-domain (drop field_is_parent_link conjunct). atk_5 = partial-domain (drop field_is_auto_identity conjunct). atk_6 = boundary/logic (AND instead of OR in the auto-identity/targets-prior guard). atk_7 = ungrounded-oracle echo (keep iff segment_targets_prior_hop). Each is behaviourally distinct from the gold on some fact combination and each is REJECTED by the spec.

Why SOUND is expected structurally: postcondition ToSeq(Result()) == retained_mask(ToSeq(prev_is_relation), ..., True) fully pins the output mask over the ENTIRE boolean fact domain. Preconditions restrict only length-equality + Acc(list_pred,1/2) read-only permission — no domain restriction — so the fact vectors range over all reachable combinations. Any verifying impl must equal retained_mask everywhere.

Refinement audit (A-legs focus): axioms region is empty — NO A-consumed, NO A-reference axioms. G-AX vacuous. keep_at/retained_mask model the retention rule DEEPLY. All operation legs are R or I; no kind-3 (unexpressible-changed-op). Term-for-term correspondence to gold hunk (options.py:467-471) verified: prev_is_relation<->prev_field.is_relation; not field_is_parent_link<->field not in model._meta.parents.values(); not field_is_auto_identity<->field is not model._meta.auto_field; (not model_has_auto_identity or not segment_targets_prior_hop)<->(auto_field is None or part not in to_fields); first-segment always-retain<->'not prev_field' disjunct. Unchanged membership test is an I-step deterministic in the mask (model<->patch correspondence holds). No divergence found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo) confirmed.

Machine facts:
- `scripts/nagini_verify.sh model.py` => Verification successful (17.28s).
- `same-spec nagini django__django-16661` on the bundle model => SAME (spec region byte-identical).
- `axiom_check.py` runs clean: 16 discriminating fact-combinations, F2P post-patch mask [1,1,1] vs pre-patch [1,0,1].

Spec-to-repo correspondence (django/contrib/admin/options.py:467-475, ModelAdmin.lookup_allowed retention condition at base_commit d687febce5). The modeled `keep_at` is a term-for-term transcription of the post-patch condition:
  prev_is_relation            <-> prev_field.is_relation
  not field_is_parent_link    <-> field not in model._meta.parents.values()
  not field_is_auto_identity  <-> field is not model._meta.auto_field
  (not model_has_auto_identity or not segment_targets_prior_hop)
                              <-> (model._meta.auto_field is None or part not in getattr(prev_field,'to_fields',[]))
The disjunctive precedence and the `not prev_field` (always-retain first segment) disjunct both match: prev_field is None only on segment 0, handled by `i-1==0 -> keep=True`; any non-None Field is truthy. `retained_mask` folds one append-decision per segment, matching `relation_parts.append(part)` across the loop; the unchanged join/isdisjoint membership test (I-step) consumes the mask.

The abstraction projects each real segment to its resolved boolean structural facts and models the decision deeply over that domain. The modeled predicate never disagrees with the real post-patch condition on any combination of the projected facts (exhaustively checked over the 2^6 fact space in axiom_check: post-patch predicate is exactly reproduced). `field_is_prior_hop_target` is carried read-only and correctly NOT consulted by the post-patch impl, faithful to the gold removing that reference. No input exists where the modeled function disagrees with the real callee's retention behavior. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Computed the exact nagini spec view via swebench_unified.markers.spec_view over model.py (backend nagini). Spec view = module docstring + empty axioms region + visible pure region (keep_at, retained_mask) + pre/post-condition regions of retained_segments; impl region is elided. same-spec self-check exits 0 (spec region byte-identical).

Lexical screen: the spec view contains ZERO gold-patch/Django code symbols. Searched _meta, parents, auto_field, to_fields, path_infos, options.py, lookup_allowed, relation_parts, ForeignKey, OneToOneField, list_filter, LOOKUP_SEP, prev_field, get_field, target_fields, primary_key, Disallowed, base_commit, .diff, and the model names (Waiter/Restaurant/Place/Country) -- none present. Only 'django' (from the instance-id in the docstring header) and 'admin' (substring of 'administrative') appear. The concrete change site (django/contrib/admin/options.py:467-471) and all its symbols appear ONLY in refinement.md and mapping.md, which are NOT shown to the implementer.

Beyond-problem_statement check: the public problem_statement already names ModelAdmin.lookup_allowed / DisallowedModelAdminLookup, diagnoses that a FK-used-as-primary-key is wrongly conflated with concrete inheritance, explains the spurious shortening of restaurant__place__country to restaurant__country, and supplies the full failing test. The docstring is explicitly 'stated as desired behaviour, not as an edit'; it restates that same diagnosis and the demanded outcome (retain the full relation path). The keep_at conjuncts (field_is_parent_link, field_is_auto_identity, model_has_auto_identity, segment_targets_prior_hop) are neutral abstract structural-fact booleans over List[bool] vectors -- they pin the correct retention boundary (the spec's legitimate job) but name no Django mechanism to edit and give no code-level reconstruction of the gold hunk. The implementer's task (build a retention mask over boolean vectors) is not the gold code edit. A faithful behavioral spec necessarily corresponds to the fix; that correspondence alone is not leakage. No spec-view line reconstructs the gold edit beyond the public problem_statement.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
