# P2 adversarial audit — django__django-12325

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,6 @@
 """
 from typing import Dict, List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(related_key), 1 / 2))
     # The two lists are parallel: one entry per scanned relation.
     Requires(len(is_parent_link) == len(related_key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_parent_link), 1 / 2))
@@ -139,10 +137,8 @@
             related_key[j] in result
             and result[related_key[j]] >= j),
             [[is_parent_link[j]]])))
-        Invariant(MustTerminate(len(is_parent_link) - i + 1))
         # invariants-end
-        if is_parent_link[i]:
-            result[related_key[i]] = i
+        result[related_key[i]] = i
         i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,6 @@
 """
 from typing import Dict, List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(related_key), 1 / 2))
     # The two lists are parallel: one entry per scanned relation.
     Requires(len(is_parent_link) == len(related_key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_parent_link), 1 / 2))
@@ -139,9 +137,8 @@
             related_key[j] in result
             and result[related_key[j]] >= j),
             [[is_parent_link[j]]])))
-        Invariant(MustTerminate(len(is_parent_link) - i + 1))
         # invariants-end
-        if is_parent_link[i]:
+        if is_parent_link[i] and related_key[i] not in result:
             result[related_key[i]] = i
         i = i + 1
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,6 @@
 """
 from typing import Dict, List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(related_key), 1 / 2))
     # The two lists are parallel: one entry per scanned relation.
     Requires(len(is_parent_link) == len(related_key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_parent_link), 1 / 2))
@@ -139,9 +137,8 @@
             related_key[j] in result
             and result[related_key[j]] >= j),
             [[is_parent_link[j]]])))
-        Invariant(MustTerminate(len(is_parent_link) - i + 1))
         # invariants-end
-        if is_parent_link[i]:
+        if is_parent_link[i] and i > 0:
             result[related_key[i]] = i
         i = i + 1
     return result
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,6 @@
 """
 from typing import Dict, List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(related_key), 1 / 2))
     # The two lists are parallel: one entry per scanned relation.
     Requires(len(is_parent_link) == len(related_key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_parent_link), 1 / 2))
@@ -139,9 +137,8 @@
             related_key[j] in result
             and result[related_key[j]] >= j),
             [[is_parent_link[j]]])))
-        Invariant(MustTerminate(len(is_parent_link) - i + 1))
         # invariants-end
-        if is_parent_link[i]:
+        if is_parent_link[i] or related_key[i] == 0:
             result[related_key[i]] = i
         i = i + 1
     return result
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,6 @@
 """
 from typing import Dict, List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(related_key), 1 / 2))
     # The two lists are parallel: one entry per scanned relation.
     Requires(len(is_parent_link) == len(related_key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_parent_link), 1 / 2))
@@ -116,7 +114,7 @@
     # impl-start
     result = {}  # type: Dict[int, int]
     i = 0
-    while i < len(is_parent_link):
+    while i < len(is_parent_link) - 1:
         # invariants-start
         Invariant(Acc(list_pred(is_parent_link), 1 / 2))
         Invariant(Acc(list_pred(related_key), 1 / 2))
@@ -139,7 +137,6 @@
             related_key[j] in result
             and result[related_key[j]] >= j),
             [[is_parent_link[j]]])))
-        Invariant(MustTerminate(len(is_parent_link) - i + 1))
         # invariants-end
         if is_parent_link[i]:
             result[related_key[i]] = i
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,6 @@
 """
 from typing import Dict, List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(related_key), 1 / 2))
     # The two lists are parallel: one entry per scanned relation.
     Requires(len(is_parent_link) == len(related_key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_parent_link), 1 / 2))
@@ -139,9 +137,8 @@
             related_key[j] in result
             and result[related_key[j]] >= j),
             [[is_parent_link[j]]])))
-        Invariant(MustTerminate(len(is_parent_link) - i + 1))
         # invariants-end
-        if is_parent_link[i]:
+        if is_parent_link[i] and i % 2 == 0:
             result[related_key[i]] = i
         i = i + 1
     return result
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,6 @@
 """
 from typing import Dict, List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(related_key), 1 / 2))
     # The two lists are parallel: one entry per scanned relation.
     Requires(len(is_parent_link) == len(related_key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_parent_link), 1 / 2))
@@ -139,10 +137,9 @@
             related_key[j] in result
             and result[related_key[j]] >= j),
             [[is_parent_link[j]]])))
-        Invariant(MustTerminate(len(is_parent_link) - i + 1))
         # invariants-end
-        if is_parent_link[i]:
-            result[related_key[i]] = i
+        is_parent_link[i] = True
+        result[related_key[i]] = i
         i = i + 1
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,6 @@
 """
 from typing import Dict, List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(related_key), 1 / 2))
     # The two lists are parallel: one entry per scanned relation.
     Requires(len(is_parent_link) == len(related_key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(is_parent_link), 1 / 2))
@@ -139,10 +137,9 @@
             related_key[j] in result
             and result[related_key[j]] >= j),
             [[is_parent_link[j]]])))
-        Invariant(MustTerminate(len(is_parent_link) - i + 1))
         # invariants-end
         if is_parent_link[i]:
-            result[related_key[i]] = i
+            result[related_key[i]] = i - 1
         i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12325.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a class participates in multi-table inheritance, the framework scans the
  one-to-one relations declared on its bases and records, per related model, the
  single relation that links the child to that parent. That recorded relation is
  later promoted to be the child's primary key. Among several one-to-one
  relations that happen to target the SAME related model, only the relation that
  is explicitly designated as a parent link is eligible to be recorded; an
  ordinary one-to-one relation that merely happens to point at the same related
  model must never be recorded, regardless of the order in which the relations
  were declared. Consequently:

    (1) Every recorded relation is a designated parent link. An ordinary
        one-to-one relation -- even one whose target coincides with a parent --
        is never recorded, so the relation later promoted to primary key is
        always a genuine parent link. (This is what removes the spurious
        configuration error the issue reports.)

    (2) Declaration order is irrelevant. A designated parent link to a given
        related model is recorded whether it is declared before or after an
        ordinary one-to-one relation to that same model; an ordinary relation
        declared after a parent link cannot displace it.

    (3) Every related model that has at least one designated parent link among
        the scanned relations ends up with a recorded relation for it, so a
        legitimate inheritance link is never lost.

    (4) Among several designated parent links to the SAME related model, the
        one scanned LAST is the one recorded (a later designated parent link
        overwrites an earlier one, mirroring the repository's last-writer-wins
        dict recording). The recorded relation is therefore never an earlier
        parent link than any other parent link to that model.

Modelling choices (Nagini fragment):
  * The scanned one-to-one relations are modelled by two parallel lists indexed
    by relation position: ``is_parent_link[i]`` is whether relation ``i`` is a
    designated parent link, and ``related_key[i]`` is the identity token of the
    related model that relation ``i`` targets (the repository derives this token
    from the related model via the unchanged key-derivation callee; mapping.md
    §2). Equal tokens model the same related model.
  * The per-related-model record is a ``Dict[int, int]`` mapping a related-model
    token to the POSITION of the recorded relation. Recording a position rather
    than an opaque object keeps the chosen relation's designation observable,
    so the guarantee "every recorded relation is a parent link" is expressible
    directly on the carrier.

Both input lists are read-only and held at fractional permission; the record is
built fresh and returned at full permission. No string indexing is used (Nagini
bans it). The behaviour is modelled deeply (the eligibility filter and the
per-model recording are spelled out in the impl region); there is no
axiomatised callee. Markers (machine-parsed) delimit the spec/proof/impl
regions.
"""
from typing import Dict, List
from nagini_contracts.contracts import *

# axioms-start
# No axioms: the per-related-model recording (with its eligibility filter) is
# the behaviour under specification and is spelled out deeply in the impl
# region. The related-model token is the result of an UNCHANGED key-derivation
# callee, abstracted to the int carrier ``related_key[i]`` (a type refinement,
# mapping.md §2); it is not called inside any contract and so is not an axiom.
# axioms-end

# pure-start
# No pure helpers: the specification is phrased directly over the parallel
# input lists and the result dictionary.
# pure-end

def select_inheritance_links(is_parent_link: List[bool],
                             related_key: List[int]) -> Dict[int, int]:
    # pre-conditions-start
    # Both inputs are read-only; fractional permission (directive 5).
    Requires(Acc(list_pred(is_parent_link), 1 / 2))
    Requires(Acc(list_pred(related_key), 1 / 2))
    # The two lists are parallel: one entry per scanned relation.
    Requires(len(is_parent_link) == len(related_key))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(is_parent_link), 1 / 2))
    Ensures(Acc(list_pred(related_key), 1 / 2))
    Ensures(dict_pred(Result()))
    Ensures(len(is_parent_link) == len(related_key))
    # (1) Every recorded relation is a designated parent link, and the position
    #     it records is a real relation position whose target is that key. An
    #     ordinary one-to-one relation is therefore never recorded -- the
    #     relation promoted to primary key downstream is always a parent link.
    Ensures(Forall(int, lambda k: (Implies(
        k in Result(),
        0 <= Result()[k] and Result()[k] < len(is_parent_link)
        and Result()[k] < len(related_key)
        and is_parent_link[Result()[k]]
        and related_key[Result()[k]] == k),
        [[k in Result()]])))
    # (3)+(4) Every related model that has a designated parent link among the
    #     scanned relations ends up recorded (no legitimate inheritance link is
    #     ever lost, independently of declaration order, clause (2)), and the
    #     recorded position is not earlier than ANY designated parent link
    #     targeting that model. Together with clause (1) the recorded position
    #     is therefore exactly the LAST designated parent-link position for
    #     that related model (last-writer-wins, clause (4)) -- the spec pins
    #     WHICH relation is recorded, not merely that some parent link is.
    Ensures(Forall(int, lambda i: (Implies(
        0 <= i and i < len(is_parent_link) and is_parent_link[i],
        related_key[i] in Result()
        and Result()[related_key[i]] >= i),
        [[is_parent_link[i]]])))
    # post-conditions-end
    # impl-start
    result = {}  # type: Dict[int, int]
    i = 0
    while i < len(is_parent_link):
        # invariants-start
        Invariant(Acc(list_pred(is_parent_link), 1 / 2))
        Invariant(Acc(list_pred(related_key), 1 / 2))
        Invariant(dict_pred(result))
        Invariant(len(is_parent_link) == len(related_key))
        Invariant(0 <= i and i <= len(is_parent_link))
        # Every recorded position is a parent link from the processed prefix,
        # and records the key it actually targets.
        Invariant(Forall(int, lambda k: (Implies(
            k in result,
            0 <= result[k] and result[k] < i
            and result[k] < len(related_key)
            and is_parent_link[result[k]]
            and related_key[result[k]] == k),
            [[k in result]])))
        # Every parent link in the processed prefix has been recorded, at a
        # position not earlier than itself (last-writer-wins).
        Invariant(Forall(int, lambda j: (Implies(
            0 <= j and j < i and is_parent_link[j],
            related_key[j] in result
            and result[related_key[j]] >= j),
            [[is_parent_link[j]]])))
        # invariants-end
        if is_parent_link[i]:
            result[related_key[i]] = i
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement-fidelity) audit of django__django-12325 nagini bundle. Spec is fully pinned: clause(1) forces every recorded key k to map to a valid position with is_parent_link True and related_key==k; clause(3)+(4) force related_key[i] in Result() and Result()[related_key[i]]>=i for every parent-link i, so Result()[k] must equal the LAST parent-link position for k and the recorded key-set is exactly {related_key[i]:is_parent_link[i]}. The abstract function is uniquely determined.

POSITIVE CONTROL: cp model.py -> positive_control.py; `bash scripts/nagini_verify.sh .../positive_control.py` => exit 0, Verification successful, 14.58s. Spec is not too strong.

8 same-spec wrong impls (impl region ONLY edited; axioms/@Pure/Requires/Ensures byte-identical). `adversary same-spec nagini django__django-12325 atk_N.py` => exit 0 (SAME) for all 8. `adversary weakness nagini django__django-12325 atk_N.py` => exit 2 (NOT-A-COUNTEREXAMPLE: does not verify) for ALL 8. atk_1 no-filter/prepatch (record every relation, last-writer-wins) -> rejected (clause 1). This IS the prepatch behaviour, so the spec senses the prepatch bug (prepatch_reproduced). atk_2 first-writer-wins (keep earliest parent link per key; clauses 1&3 hold) -> rejected. Direct verify: 'Loop invariant might not be preserved ... result[related_key[j]] >= j' (clause 4), exit 1, 20.15s.

This is the exact ungrounded/pre-repair G-PANEL-1 weakness class; clause (4) now catches it. atk_3 partial-domain skip position 0 -> rejected (clause 3). atk_4 value-partial-domain: record ordinary rel when related_key==0 -> rejected (clause 1). atk_5 boundary off-by-one: `while i < len-1` misses last relation -> rejected (clause 3). atk_6 control-flow-effect: record parent links only at even i -> rejected (clause 3). atk_7 frame-mutation: forge is_parent_link[i]=True then record all -> rejected. Direct verify: 'The precondition of is_parent_link[i] = True might not hold. There might be insufficient permission.' exit 1, 13.27s (permission system, read-only input Acc(...,1/2)). atk_8 off-by-one value: record i-1 instead of i -> rejected (clause 1 related_key[Result()[k]]==k / clause 4). Spot-checked atk_2 and atk_7 directly under a 400s timeout to confirm genuine semantic failures (exit 1, ~13-20s), not contention/false-timeouts.

ZERO CANDIDATEs (no impl both shares spec AND verifies besides the correct one) => no faithful refined patch to materialize/resolve-run. verify=>correct not falsified.

A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[]. refinement.md legs A1(R),A2(I over refined bool),A3(R),A4(R),B1(I proof-level, guard removal is a consequence of clause 1),B2(I import drop). No kind-3 (unexpressible-changed-op) leg. No @ContractOnly callee; the unchanged callees isinstance/resolve_relation/make_model_tuple are type-refined into the int/bool carrier (mapping.md 2), never contracted inside Requires/Ensures, so G-AX is vacuous and axiom_check.py is a positive sanity check only. The model<->patch correspondence (is_parent_link[i] <-> field.remote_field.parent_link identity; related_key[i] <-> make_model_tuple(resolve_relation(new_class, field.remote_field.model)) token; result[k]=i <-> parent_links[key]=field with position recovering field identity) holds and is an honest R/I refinement of behaviour unchanged by the patch. A-legs sound.

VERDICT: SOUND. >=5 (8) distinct adversarial attacks across partial-domain, value-partial-domain, boundary, control-flow-effect, first-writer-wins (pre-repair panel-1 class), prepatch-echo, and frame-mutation classes all failed to verify against the frozen spec; positive control verifies; no verifying wrong impl exists, so no non-resolving faithful patch. verify=>correct not broken for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12325.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a class participates in multi-table inheritance, the framework scans the
  one-to-one relations declared on its bases and records, per related model, the
  single relation that links the child to that parent. That recorded relation is
  later promoted to be the child's primary key. Among several one-to-one
  relations that happen to target the SAME related model, only the relation that
  is explicitly designated as a parent link is eligible to be recorded; an
  ordinary one-to-one relation that merely happens to point at the same related
  model must never be recorded, regardless of the order in which the relations
  were declared. Consequently:

    (1) Every recorded relation is a designated parent link. An ordinary
        one-to-one relation -- even one whose target coincides with a parent --
        is never recorded, so the relation later promoted to primary key is
        always a genuine parent link. (This is what removes the spurious
        configuration error the issue reports.)

    (2) Declaration order is irrelevant. A designated parent link to a given
        related model is recorded whether it is declared before or after an
        ordinary one-to-one relation to that same model; an ordinary relation
        declared after a parent link cannot displace it.

    (3) Every related model that has at least one designated parent link among
        the scanned relations ends up with a recorded relation for it, so a
        legitimate inheritance link is never lost.

    (4) Among several designated parent links to the SAME related model, the
        one scanned LAST is the one recorded (a later designated parent link
        overwrites an earlier one, mirroring the repository's last-writer-wins
        dict recording). The recorded relation is therefore never an earlier
        parent link than any other parent link to that model.

Modelling choices (Nagini fragment):
  * The scanned one-to-one relations are modelled by two parallel lists indexed
    by relation position: ``is_parent_link[i]`` is whether relation ``i`` is a
    designated parent link, and ``related_key[i]`` is the identity token of the
    related model that relation ``i`` targets (the repository derives this token
    from the related model via the unchanged key-derivation callee; mapping.md
    §2). Equal tokens model the same related model.
  * The per-related-model record is a ``Dict[int, int]`` mapping a related-model
    token to the POSITION of the recorded relation. Recording a position rather
    than an opaque object keeps the chosen relation's designation observable,
    so the guarantee "every recorded relation is a parent link" is expressible
    directly on the carrier.

Both input lists are read-only and held at fractional permission; the record is
built fresh and returned at full permission. No string indexing is used (Nagini
bans it). The behaviour is modelled deeply (the eligibility filter and the
per-model recording are spelled out in the impl region); there is no
axiomatised callee. Markers (machine-parsed) delimit the spec/proof/impl
regions.
"""
from typing import Dict, List
from nagini_contracts.contracts import *

# axioms-start
# No axioms: the per-related-model recording (with its eligibility filter) is
# the behaviour under specification and is spelled out deeply in the impl
# region. The related-model token is the result of an UNCHANGED key-derivation
# callee, abstracted to the int carrier ``related_key[i]`` (a type refinement,
# mapping.md §2); it is not called inside any contract and so is not an axiom.
# axioms-end

# pure-start
# No pure helpers: the specification is phrased directly over the parallel
# input lists and the result dictionary.
# pure-end

def select_inheritance_links(is_parent_link: List[bool],
                             related_key: List[int]) -> Dict[int, int]:
    # pre-conditions-start
    # Both inputs are read-only; fractional permission (directive 5).
    Requires(Acc(list_pred(is_parent_link), 1 / 2))
    Requires(Acc(list_pred(related_key), 1 / 2))
    # The two lists are parallel: one entry per scanned relation.
    Requires(len(is_parent_link) == len(related_key))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(is_parent_link), 1 / 2))
    Ensures(Acc(list_pred(related_key), 1 / 2))
    Ensures(dict_pred(Result()))
    Ensures(len(is_parent_link) == len(related_key))
    # (1) Every recorded relation is a designated parent link, and the position
    #     it records is a real relation position whose target is that key. An
    #     ordinary one-to-one relation is therefore never recorded -- the
    #     relation promoted to primary key downstream is always a parent link.
    Ensures(Forall(int, lambda k: (Implies(
        k in Result(),
        0 <= Result()[k] and Result()[k] < len(is_parent_link)
        and Result()[k] < len(related_key)
        and is_parent_link[Result()[k]]
        and related_key[Result()[k]] == k),
        [[k in Result()]])))
    # (3)+(4) Every related model that has a designated parent link among the
    #     scanned relations ends up recorded (no legitimate inheritance link is
    #     ever lost, independently of declaration order, clause (2)), and the
    #     recorded position is not earlier than ANY designated parent link
    #     targeting that model. Together with clause (1) the recorded position
    #     is therefore exactly the LAST designated parent-link position for
    #     that related model (last-writer-wins, clause (4)) -- the spec pins
    #     WHICH relation is recorded, not merely that some parent link is.
    Ensures(Forall(int, lambda i: (Implies(
        0 <= i and i < len(is_parent_link) and is_parent_link[i],
        related_key[i] in Result()
        and Result()[related_key[i]] >= i),
        [[is_parent_link[i]]])))
    # post-conditions-end
    # impl-start
    result = {}  # type: Dict[int, int]
    i = 0
    while i < len(is_parent_link):
        # invariants-start
        Invariant(Acc(list_pred(is_parent_link), 1 / 2))
        Invariant(Acc(list_pred(related_key), 1 / 2))
        Invariant(dict_pred(result))
        Invariant(len(is_parent_link) == len(related_key))
        Invariant(0 <= i and i <= len(is_parent_link))
        # Every recorded position is a parent link from the processed prefix,
        # and records the key it actually targets.
        Invariant(Forall(int, lambda k: (Implies(
            k in result,
            0 <= result[k] and result[k] < i
            and result[k] < len(related_key)
            and is_parent_link[result[k]]
            and related_key[result[k]] == k),
            [[k in result]])))
        # Every parent link in the processed prefix has been recorded, at a
        # position not earlier than itself (last-writer-wins).
        Invariant(Forall(int, lambda j: (Implies(
            0 <= j and j < i and is_parent_link[j],
            related_key[j] in result
            and result[related_key[j]] >= j),
            [[is_parent_link[j]]])))
        # invariants-end
        if is_parent_link[i]:
            result[related_key[i]] = i
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement-fidelity) audit of django__django-12325 nagini bundle. Spec is fully pinned: clause(1) forces every recorded key k to map to a valid position with is_parent_link True and related_key==k; clause(3)+(4) force related_key[i] in Result() and Result()[related_key[i]]>=i for every parent-link i, so Result()[k] must equal the LAST parent-link position for k and the recorded key-set is exactly {related_key[i]:is_parent_link[i]}. The abstract function is uniquely determined.

POSITIVE CONTROL: cp model.py -> positive_control.py; `bash scripts/nagini_verify.sh .../positive_control.py` => exit 0, Verification successful, 14.58s. Spec is not too strong.

8 same-spec wrong impls (impl region ONLY edited; axioms/@Pure/Requires/Ensures byte-identical). `adversary same-spec nagini django__django-12325 atk_N.py` => exit 0 (SAME) for all 8. `adversary weakness nagini django__django-12325 atk_N.py` => exit 2 (NOT-A-COUNTEREXAMPLE: does not verify) for ALL 8. atk_1 no-filter/prepatch (record every relation, last-writer-wins) -> rejected (clause 1). This IS the prepatch behaviour, so the spec senses the prepatch bug (prepatch_reproduced). atk_2 first-writer-wins (keep earliest parent link per key; clauses 1&3 hold) -> rejected. Direct verify: 'Loop invariant might not be preserved ... result[related_key[j]] >= j' (clause 4), exit 1, 20.15s.

This is the exact ungrounded/pre-repair G-PANEL-1 weakness class; clause (4) now catches it. atk_3 partial-domain skip position 0 -> rejected (clause 3). atk_4 value-partial-domain: record ordinary rel when related_key==0 -> rejected (clause 1). atk_5 boundary off-by-one: `while i < len-1` misses last relation -> rejected (clause 3). atk_6 control-flow-effect: record parent links only at even i -> rejected (clause 3). atk_7 frame-mutation: forge is_parent_link[i]=True then record all -> rejected. Direct verify: 'The precondition of is_parent_link[i] = True might not hold. There might be insufficient permission.' exit 1, 13.27s (permission system, read-only input Acc(...,1/2)). atk_8 off-by-one value: record i-1 instead of i -> rejected (clause 1 related_key[Result()[k]]==k / clause 4). Spot-checked atk_2 and atk_7 directly under a 400s timeout to confirm genuine semantic failures (exit 1, ~13-20s), not contention/false-timeouts.

ZERO CANDIDATEs (no impl both shares spec AND verifies besides the correct one) => no faithful refined patch to materialize/resolve-run. verify=>correct not falsified.

A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[]. refinement.md legs A1(R),A2(I over refined bool),A3(R),A4(R),B1(I proof-level, guard removal is a consequence of clause 1),B2(I import drop). No kind-3 (unexpressible-changed-op) leg. No @ContractOnly callee; the unchanged callees isinstance/resolve_relation/make_model_tuple are type-refined into the int/bool carrier (mapping.md 2), never contracted inside Requires/Ensures, so G-AX is vacuous and axiom_check.py is a positive sanity check only. The model<->patch correspondence (is_parent_link[i] <-> field.remote_field.parent_link identity; related_key[i] <-> make_model_tuple(resolve_relation(new_class, field.remote_field.model)) token; result[k]=i <-> parent_links[key]=field with position recovering field identity) holds and is an honest R/I refinement of behaviour unchanged by the patch. A-legs sound.

VERDICT: SOUND. >=5 (8) distinct adversarial attacks across partial-domain, value-partial-domain, boundary, control-flow-effect, first-writer-wins (pre-repair panel-1 class), prepatch-echo, and frame-mutation classes all failed to verify against the frozen spec; positive control verifies; no verifying wrong impl exists, so no non-resolving faithful patch. verify=>correct not broken for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Model select_inheritance_links verifies with the pinned Nagini verifier (exit 0, 14.87s) and its impl region is the gold-patched ModelBase.__new__ parent-link loop verbatim under the refinement in mapping.md §2 (scanned OneToOneFields -> position-indexed parallel lists; is_parent_link[i] <-> field.remote_field.parent_link identity on bool; related_key[i] <-> make_model_tuple(resolve_relation(...)) unchanged-callee int token; dict value = position <-> field object).

Confirmed against the real repo at base_commit 29c126bb (base.py:193-207): the patched loop records parent_links[key] = field only for OneToOneFields with parent_link=True, and Python dict assignment is last-writer-wins in scan order.

The two postconditions faithfully (not over-strongly) describe the repo output on ALL inputs:
  (1) every recorded key maps to a valid parent-link position with matching key <-> repo records only parent-link fields under the derived key;
  (2) every parent-link position i has its key recorded at position >= i, which with (1) pins the recorded position to be exactly the LAST-scanned parent-link position per key <-> the repo dict's last-writer-wins semantics.
Clause (2)'s '>= i' is NOT an over-constraint: the real repo genuinely does last-writer-wins (later assignment overwrites earlier for the same key), so no input exists where the real callee's output would violate the spec. Since the abstraction of the gold loop itself verifies against the frozen spec, the modeled function agrees with the real callee on every input.

Sanity checks: prepatch model (unconditional record, no filter) correctly FAILS postcondition clause (1) (G-DIFF sensed the change). No axiomatized callee (G-AX vacuous). No diverging input found; spec is not too strong and does not drift from repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch lines, no patched file paths, no patched-symbol echo, no narration). Semantic gold-reconstruction check: the spec view contains NONE of the edit-localizing repo symbols (remote_field, ImproperlyConfigured, __new__, _prepare, make_model_tuple, resolve_relation, local_fields, ModelBase) nor the changed files. The only terms present (parent_link, one-to-one/OneToOneField, 'configuration error') are all already public in the problem_statement (the issue explicitly shows OneToOneField fields, 'Add parent_link=True', and the ImproperlyConfigured error). The docstring states desired behavior — record only the designated parent-link relation, order-independent — which is exactly what the public bug report asks for; it does not disclose the specific code edit (the added `and field.remote_field.parent_link` conjunct or the removed guard). spec_view hash matches meta.json region_hashes.spec_view. meta records G-LEAK status=pass; bundle not relaxed. No leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).