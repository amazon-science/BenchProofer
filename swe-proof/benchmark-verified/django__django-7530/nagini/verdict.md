# P2 adversarial audit — django__django-7530

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_prepatch.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     Requires(Acc(list_pred(owner), 1 / 2))
     Requires(Acc(list_pred(member), 1 / 2))
     Requires(len(owner) == len(member))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(owner), 1 / 2))
@@ -85,7 +83,6 @@
         Invariant(0 <= i and i <= len(owner))
         Invariant(ToSeq(result) ==
                   gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         o = owner[i - 1]
         m = member[i - 1]
@@ -93,7 +90,7 @@
         Assert(ToSeq(member).drop(i - 1)[0] == m)
         Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
         Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
-        if o == target:
+        if o != target:
             result = [m] + result
         i = i - 1
     return result
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     Requires(Acc(list_pred(owner), 1 / 2))
     Requires(Acc(list_pred(member), 1 / 2))
     Requires(len(owner) == len(member))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(owner), 1 / 2))
@@ -85,7 +83,6 @@
         Invariant(0 <= i and i <= len(owner))
         Invariant(ToSeq(result) ==
                   gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         o = owner[i - 1]
         m = member[i - 1]
@@ -93,7 +90,7 @@
         Assert(ToSeq(member).drop(i - 1)[0] == m)
         Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
         Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
-        if o == target:
+        if o == target and m != target:
             result = [m] + result
         i = i - 1
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     Requires(Acc(list_pred(owner), 1 / 2))
     Requires(Acc(list_pred(member), 1 / 2))
     Requires(len(owner) == len(member))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(owner), 1 / 2))
@@ -85,16 +83,10 @@
         Invariant(0 <= i and i <= len(owner))
         Invariant(ToSeq(result) ==
                   gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         o = owner[i - 1]
         m = member[i - 1]
-        Assert(ToSeq(owner).drop(i - 1)[0] == o)
-        Assert(ToSeq(member).drop(i - 1)[0] == m)
-        Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
-        Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
-        if o == target:
-            result = [m] + result
+        result = [m] + result
         i = i - 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     Requires(Acc(list_pred(owner), 1 / 2))
     Requires(Acc(list_pred(member), 1 / 2))
     Requires(len(owner) == len(member))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(owner), 1 / 2))
@@ -76,7 +74,7 @@
     # impl-start
     result = []  # type: List[int]
     i = len(owner)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(owner), 1 / 2))
         Invariant(Acc(list_pred(member), 1 / 2))
@@ -85,7 +83,6 @@
         Invariant(0 <= i and i <= len(owner))
         Invariant(ToSeq(result) ==
                   gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         o = owner[i - 1]
         m = member[i - 1]
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     Requires(Acc(list_pred(owner), 1 / 2))
     Requires(Acc(list_pred(member), 1 / 2))
     Requires(len(owner) == len(member))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(owner), 1 / 2))
@@ -85,7 +83,6 @@
         Invariant(0 <= i and i <= len(owner))
         Invariant(ToSeq(result) ==
                   gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         o = owner[i - 1]
         m = member[i - 1]
@@ -94,7 +91,7 @@
         Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
         Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
         if o == target:
-            result = [m] + result
+            result = result + [m]
         i = i - 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     Requires(Acc(list_pred(owner), 1 / 2))
     Requires(Acc(list_pred(member), 1 / 2))
     Requires(len(owner) == len(member))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(owner), 1 / 2))
@@ -85,16 +83,7 @@
         Invariant(0 <= i and i <= len(owner))
         Invariant(ToSeq(result) ==
                   gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        o = owner[i - 1]
-        m = member[i - 1]
-        Assert(ToSeq(owner).drop(i - 1)[0] == o)
-        Assert(ToSeq(member).drop(i - 1)[0] == m)
-        Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
-        Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
-        if o == target:
-            result = [m] + result
         i = i - 1
     return result
     # impl-end
```

Attack 7 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     Requires(Acc(list_pred(owner), 1 / 2))
     Requires(Acc(list_pred(member), 1 / 2))
     Requires(len(owner) == len(member))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(owner), 1 / 2))
@@ -83,18 +81,17 @@
         Invariant(len(owner) == len(member))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(owner))
-        Invariant(ToSeq(result) ==
-                  gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
-        Invariant(MustTerminate(i + 1))
+        Invariant(ToSeq(result) == ToSeq(member).drop(i))
         # invariants-end
         o = owner[i - 1]
         m = member[i - 1]
-        Assert(ToSeq(owner).drop(i - 1)[0] == o)
         Assert(ToSeq(member).drop(i - 1)[0] == m)
-        Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
         Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
-        if o == target:
-            result = [m] + result
+        # PRE-PATCH BUG: the project-wide member list is returned for every
+        # group (the group argument is ignored), so members of OTHER groups are
+        # gathered too. Equivalent to consulting the whole roster instead of
+        # just `target`'s members: the `o == target` guard is absent.
+        result = [m] + result
         i = i - 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-7530.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A pre-flight check consults a per-database routing policy with one
  (group, member) pair for every member that should be examined for a given
  group. The project keeps a flat roster of members; each member belongs to
  exactly one group. The roster is two aligned streams: `owner[k]` is the
  group of the k-th member and `member[k]` is that member's identifier.

  When the examined members for a group `target` are gathered, the gathered
  sequence must be EXACTLY the members that belong to `target`, in roster
  order: a member is gathered iff its recorded group equals `target`. No member
  of a different group is offered for this group (which would feed the routing
  policy a combination that does not exist — a member of one group presented
  under a different group's label), and no member belonging to `target` is
  omitted.

Members and groups are modelled as `List[int]` identifiers; the specification is
carried by the pure sequence theory `PSeq[int]`. The selection is modelled
DEEPLY as a front-recursive membership filter (`gathered`); nothing is consumed
as an axiom — the real roster lookup is validated == this deep model by
axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No consumed @ContractOnly axiom. The members-for-a-group selection is the
#  operation under specification; it is modelled DEEPLY in the `pure` region and
#  the verified impl as the spelled-out membership filter over the roster, and
#  validated == the real roster lookup by axiom_check.py / G-AX as an
#  A-reference. Nothing here is consumed as an axiom.)
# axioms-end

# pure-start
@Pure
def gathered(owner: PSeq[int], member: PSeq[int], target: int) -> PSeq[int]:
    """The members belonging to `target`, in roster order: the front-to-back
    concatenation of each member kept iff its recorded group equals `target`.
    Front-recursive so a single unfold is available per loop step."""
    if len(owner) == 0 or len(member) == 0:
        return PSeq(0).take(0)
    if owner[0] == target:
        return PSeq(member[0]) + gathered(owner.drop(1), member.drop(1), target)
    return gathered(owner.drop(1), member.drop(1), target)
# pure-end

def members_for_group(owner: List[int], member: List[int], target: int) -> List[int]:
    # pre-conditions-start
    # The roster is read-only: gathering members mutates nothing it is given,
    # so each stream is required AND ensured at fractional permission
    # (directive 5). The two streams are aligned one entry per member.
    Requires(Acc(list_pred(owner), 1 / 2))
    Requires(Acc(list_pred(member), 1 / 2))
    Requires(len(owner) == len(member))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(owner), 1 / 2))
    Ensures(Acc(list_pred(member), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The gathered sequence is EXACTLY the members belonging to `target`, in
    # roster order. This pins the discriminating behaviour: every gathered
    # member is one whose group is `target` (soundness — no foreign-group member
    # is offered under this group's label) and every member of `target` is
    # present (completeness).
    Ensures(ToSeq(Result()) == gathered(ToSeq(owner), ToSeq(member), target))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(owner)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(owner), 1 / 2))
        Invariant(Acc(list_pred(member), 1 / 2))
        Invariant(len(owner) == len(member))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(owner))
        Invariant(ToSeq(result) ==
                  gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
        # invariants-end
        o = owner[i - 1]
        m = member[i - 1]
        Assert(ToSeq(owner).drop(i - 1)[0] == o)
        Assert(ToSeq(member).drop(i - 1)[0] == m)
        Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
        Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
        if o == target:
            result = [m] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition `ToSeq(Result()) == gathered(ToSeq(owner), ToSeq(member), target)` is a TOTAL FUNCTIONAL EQUALITY that fully pins the output sequence as a function of inputs; the deep model `gathered` is spelled out in the @Pure region (no consumed axiom). Therefore no wrong impl can verify, and no verifying-wrong-impl exists to materialize a non-resolving patch for.

 Positive control (model.py copy) verifies: `bash scripts/nagini_verify.sh positive_control.py` -> 'Verification successful' (18.56s, exit 0).

7 same-spec wrong impls (only the impl region edited; axioms/@Pure/Requires/Ensures byte-identical), each run with `python -m swebench_unified.adversary weakness nagini django__django-7530 <path>`; ALL returned exit 2 = NOT-A-COUNTEREXAMPLE (attack does not verify -- spec rejected it). NONE returned exit 0 (CANDIDATE), so there is no verifying candidate to build a faithful refined patch for; patches={} accordingly.

Attacks (class -> observed): atk_prepatch (guard dropped, project-wide) -> exit2 rejected; atk_1 (control-flow-effect: inverted guard o!=target) -> exit2; atk_2 (partial-domain: extra spurious m!=target filter) -> exit2; atk_3 (prepatch echo, no guard) -> exit2; atk_4 (boundary off-by-one i>1, drops entry 0) -> exit2; atk_5 (control-flow-effect: result+[m] reverses roster order) -> exit2; atk_6 (ungrounded-oracle echo: always-empty result) -> exit2. same-spec confirmation: `adversary same-spec` on atk_1 and atk_6 -> exit 0 ('SAME -- attack shares the bundle's exact specification'); direct `nagini_verify.sh atk_5.py` -> 'Verification failed' with 'Loop invariant might not be preserved ... (ToSeq(result) == gathered(...))' (exit 1), confirming the postcondition is what rejects wrong impls.

prepatch_reproduced=true: atk_prepatch = bundle's model_prepatch.py (guard dropped, invariant ToSeq(result)==ToSeq(member).drop(i)) fails verification.

A-leg / correspondence audit: refinement.md legs are A1=R (str app_label<->int target, equality only), A2=R (registry model/app tagging <-> two aligned List[int] streams), A3=A-reference (deep model `gathered`/verified loop <-> apps.get_app_config(app_label).get_models()), A4=I (yielded model paired with app_label in UNCHANGED router.allow_migrate/any/check_consistent_history). No kind-3 leg; no consumed @ContractOnly axiom (axioms region empty by design). A-reference validated LIVE: ran axiom_check.py (G-AX) with a temp Django>=3.2 install (PYTHONPATH=djlibs) -> 'G-AX OK: deep model `gathered` == real apps.get_app_config(label).get_models() for 2 apps / 5 models; pre-patch apps.get_models(label) returns the project-wide set (bug witnessed).' exit 0. Correspondence holds: real callee yields exactly the queried app's models (soundness+completeness) == gathered; pre-patch apps.get_models(label) binds label to include_auto_created and returns project-wide set. meta.json records G-AX pass (Docker run) and G-CONF pass (100007 inputs, 0 disagreements).

Env note: adversary/nagini_verify must run with python (default PATH python lacks swebench_unified). All >=5 attacks fully verified; none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_prepatch.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-7530.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A pre-flight check consults a per-database routing policy with one
  (group, member) pair for every member that should be examined for a given
  group. The project keeps a flat roster of members; each member belongs to
  exactly one group. The roster is two aligned streams: `owner[k]` is the
  group of the k-th member and `member[k]` is that member's identifier.

  When the examined members for a group `target` are gathered, the gathered
  sequence must be EXACTLY the members that belong to `target`, in roster
  order: a member is gathered iff its recorded group equals `target`. No member
  of a different group is offered for this group (which would feed the routing
  policy a combination that does not exist — a member of one group presented
  under a different group's label), and no member belonging to `target` is
  omitted.

Members and groups are modelled as `List[int]` identifiers; the specification is
carried by the pure sequence theory `PSeq[int]`. The selection is modelled
DEEPLY as a front-recursive membership filter (`gathered`); nothing is consumed
as an axiom — the real roster lookup is validated == this deep model by
axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No consumed @ContractOnly axiom. The members-for-a-group selection is the
#  operation under specification; it is modelled DEEPLY in the `pure` region and
#  the verified impl as the spelled-out membership filter over the roster, and
#  validated == the real roster lookup by axiom_check.py / G-AX as an
#  A-reference. Nothing here is consumed as an axiom.)
# axioms-end

# pure-start
@Pure
def gathered(owner: PSeq[int], member: PSeq[int], target: int) -> PSeq[int]:
    """The members belonging to `target`, in roster order: the front-to-back
    concatenation of each member kept iff its recorded group equals `target`.
    Front-recursive so a single unfold is available per loop step."""
    if len(owner) == 0 or len(member) == 0:
        return PSeq(0).take(0)
    if owner[0] == target:
        return PSeq(member[0]) + gathered(owner.drop(1), member.drop(1), target)
    return gathered(owner.drop(1), member.drop(1), target)
# pure-end

def members_for_group(owner: List[int], member: List[int], target: int) -> List[int]:
    # pre-conditions-start
    # The roster is read-only: gathering members mutates nothing it is given,
    # so each stream is required AND ensured at fractional permission
    # (directive 5). The two streams are aligned one entry per member.
    Requires(Acc(list_pred(owner), 1 / 2))
    Requires(Acc(list_pred(member), 1 / 2))
    Requires(len(owner) == len(member))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(owner), 1 / 2))
    Ensures(Acc(list_pred(member), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The gathered sequence is EXACTLY the members belonging to `target`, in
    # roster order. This pins the discriminating behaviour: every gathered
    # member is one whose group is `target` (soundness — no foreign-group member
    # is offered under this group's label) and every member of `target` is
    # present (completeness).
    Ensures(ToSeq(Result()) == gathered(ToSeq(owner), ToSeq(member), target))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(owner)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(owner), 1 / 2))
        Invariant(Acc(list_pred(member), 1 / 2))
        Invariant(len(owner) == len(member))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(owner))
        Invariant(ToSeq(result) ==
                  gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
        # invariants-end
        o = owner[i - 1]
        m = member[i - 1]
        Assert(ToSeq(owner).drop(i - 1)[0] == o)
        Assert(ToSeq(member).drop(i - 1)[0] == m)
        Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
        Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
        if o == target:
            result = [m] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition `ToSeq(Result()) == gathered(ToSeq(owner), ToSeq(member), target)` is a TOTAL FUNCTIONAL EQUALITY that fully pins the output sequence as a function of inputs; the deep model `gathered` is spelled out in the @Pure region (no consumed axiom). Therefore no wrong impl can verify, and no verifying-wrong-impl exists to materialize a non-resolving patch for.

 Positive control (model.py copy) verifies: `bash scripts/nagini_verify.sh positive_control.py` -> 'Verification successful' (18.56s, exit 0).

7 same-spec wrong impls (only the impl region edited; axioms/@Pure/Requires/Ensures byte-identical), each run with `python -m swebench_unified.adversary weakness nagini django__django-7530 <path>`; ALL returned exit 2 = NOT-A-COUNTEREXAMPLE (attack does not verify -- spec rejected it). NONE returned exit 0 (CANDIDATE), so there is no verifying candidate to build a faithful refined patch for; patches={} accordingly.

Attacks (class -> observed): atk_prepatch (guard dropped, project-wide) -> exit2 rejected; atk_1 (control-flow-effect: inverted guard o!=target) -> exit2; atk_2 (partial-domain: extra spurious m!=target filter) -> exit2; atk_3 (prepatch echo, no guard) -> exit2; atk_4 (boundary off-by-one i>1, drops entry 0) -> exit2; atk_5 (control-flow-effect: result+[m] reverses roster order) -> exit2; atk_6 (ungrounded-oracle echo: always-empty result) -> exit2. same-spec confirmation: `adversary same-spec` on atk_1 and atk_6 -> exit 0 ('SAME -- attack shares the bundle's exact specification'); direct `nagini_verify.sh atk_5.py` -> 'Verification failed' with 'Loop invariant might not be preserved ... (ToSeq(result) == gathered(...))' (exit 1), confirming the postcondition is what rejects wrong impls.

prepatch_reproduced=true: atk_prepatch = bundle's model_prepatch.py (guard dropped, invariant ToSeq(result)==ToSeq(member).drop(i)) fails verification.

A-leg / correspondence audit: refinement.md legs are A1=R (str app_label<->int target, equality only), A2=R (registry model/app tagging <-> two aligned List[int] streams), A3=A-reference (deep model `gathered`/verified loop <-> apps.get_app_config(app_label).get_models()), A4=I (yielded model paired with app_label in UNCHANGED router.allow_migrate/any/check_consistent_history). No kind-3 leg; no consumed @ContractOnly axiom (axioms region empty by design). A-reference validated LIVE: ran axiom_check.py (G-AX) with a temp Django>=3.2 install (PYTHONPATH=djlibs) -> 'G-AX OK: deep model `gathered` == real apps.get_app_config(label).get_models() for 2 apps / 5 models; pre-patch apps.get_models(label) returns the project-wide set (bug witnessed).' exit 0. Correspondence holds: real callee yields exactly the queried app's models (soundness+completeness) == gathered; pre-patch apps.get_models(label) binds label to include_auto_created and returns project-wide set. meta.json records G-AX pass (Docker run) and G-CONF pass (100007 inputs, 0 disagreements).

Env note: adversary/nagini_verify must run with python (default PATH python lacks swebench_unified). All >=5 attacks fully verified; none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift) assessed for django__django-7530 nagini bundle. The modeled function members_for_group / gathered pins the per-app model-selection behavior of the makemigrations history-consistency pre-check: the fix changes `for model in apps.get_models(app_label)` (project-wide, arg bound to include_auto_created) to `for model in apps.get_app_config(app_label).get_models()` (exactly the models owned by app_label, in registration order). The spec models this as: result == gathered(owner, member, target) = member[k] for each k with owner[k]==target, in order.

Machine checks run against the REAL patched repo at base_commit f8fab6f9 (worktree, py3.8 + pytz):
- conformance_check.py (G-CONF): shadow contract-stripped impl == real apps.get_app_config(label).get_models() on 100007 (roster,target) inputs across two legs (bulk registry comparison + in-situ end-to-end `makemigrations` command with a recording router), 0 disagreements. Element-for-element and in registration order.
- axiom_check.py (G-AX): deep model gathered == real callee on disjoint two-app registry; pre-patch apps.get_models(label) returns the project-wide set (bug witnessed).

Drift analysis: the only real-callee nuance not literally in `gathered` is the auto_created/swapped filter inside get_models. Per mapping.md §3.1 the owner/member streams are defined to be the registry's already-filtered models, and the conformance harness builds both the streams and the real answer from the same registry, so the filter is orthogonal to the pinned ownership property and cannot yield a divergence within the stated int type-bridge (app-label->int, (label,object_name)->int). Ordering, empty-app rosters, and boundary rosters are all covered. The spec is neither too strong nor drifting: the modeled function agrees with the real repo callee on every tested input including the full command path. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Charge: does the consumer spec view leak the gold edit beyond the public problem_statement (not hints_text)?

Gold edit (patch.diff): `- for model in apps.get_models(app_label)` / `+ for model in apps.get_app_config(app_label).get_models()` in django/core/management/commands/makemigrations.py — narrowing the per-app router pre-check iterable from the project-wide model list to the app's own models.

Public problem_statement ALREADY discloses this behavior functionally: 'makemigrations incorrectly calls allow_migrate() for each app with all the models in the project rather than for each app with the app's models ... passing invalid combinations for shards since not all shards have the same models.' So the correct behavior (consult each app with only its own models) is public.

Spec view (computed via markers.spec_view over model.py: docstring + `gathered` pure def + members_for_group pre/post-conditions, impl elided) is strictly MORE ABSTRACT than the problem statement:
- Generic ints/streams vocabulary (owner/member/target/roster/group), no Django terms.
- Names NO gold-specific repo symbol: `get_app_config`, `get_models`, `apps`, `allow_migrate`, `makemigrations`, `AppConfig` do not appear anywhere in the spec view.
- No diff markers, no patched file path/module path, no bug/fix/pre-patch narration.
- Pins exactly the ownership property (gather members whose recorded group == target; soundness+completeness) which is precisely what problem_statement already states publicly.

The gold-specific API/file/pre-patch disclosures (`get_app_config().get_models()`, file paths, `apps.get_models(app_label)` bug) live ONLY in the audit documents mapping.md / refinement.md — NOT in the consumer spec view that G-LEAK/G-PANEL-3 screens.

Mechanical G-LEAK screen (leakage.screen) run independently: PASSED with zero hard failures. Changed symbols = {'handle'} (non-distinctive, absent from spec view); no reproduced gold line, no diff marker, no path.

Conclusion: spec view leaks nothing about the gold edit beyond the already-public problem_statement; it is a faithful, abstracted spec. No relaxation was needed or relied upon.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.