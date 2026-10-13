# P2 adversarial audit — django__django-13964

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # The referenced object has been saved, so it carries a real (non-empty)
     # stored key — this is the branch reached once the referenced key is known.
     Requires(len(related_key) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(target.fk))
@@ -107,8 +105,10 @@
                     stored_seq(target.fk) == Old(stored_seq(target.fk))))
     # post-conditions-end
     # impl-start
-    if is_empty_placeholder(target.fk):
-        # Adopt the referenced object's stored key into the local attribute.
+    if not is_empty_placeholder(target.fk):
+        # Deliberate non-empty key: leave untouched.
+        pass
+    else:
         adopted = []  # type: List[int]
         i = 0
         while i < len(related_key):
@@ -119,7 +119,6 @@
             Invariant(0 <= i and i <= len(related_key))
             Invariant(len(adopted) == i)
             Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
-            Invariant(MustTerminate(len(related_key) - i + 1))
             # invariants-end
             adopted.append(related_key[i])
             i = i + 1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # The referenced object has been saved, so it carries a real (non-empty)
     # stored key — this is the branch reached once the referenced key is known.
     Requires(len(related_key) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(target.fk))
@@ -107,22 +105,19 @@
                     stored_seq(target.fk) == Old(stored_seq(target.fk))))
     # post-conditions-end
     # impl-start
-    if is_empty_placeholder(target.fk):
-        # Adopt the referenced object's stored key into the local attribute.
-        adopted = []  # type: List[int]
-        i = 0
-        while i < len(related_key):
-            # invariants-start
-            Invariant(Acc(list_pred(related_key), 1 / 2))
-            Invariant(Acc(list_pred(adopted)))
-            Invariant(len(related_key) > 0)
-            Invariant(0 <= i and i <= len(related_key))
-            Invariant(len(adopted) == i)
-            Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
-            Invariant(MustTerminate(len(related_key) - i + 1))
-            # invariants-end
-            adopted.append(related_key[i])
-            i = i + 1
-        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
-        target.fk = adopted
+    adopted = []  # type: List[int]
+    i = 0
+    while i < len(related_key):
+        # invariants-start
+        Invariant(Acc(list_pred(related_key), 1 / 2))
+        Invariant(Acc(list_pred(adopted)))
+        Invariant(len(related_key) > 0)
+        Invariant(0 <= i and i <= len(related_key))
+        Invariant(len(adopted) == i)
+        Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
+        # invariants-end
+        adopted.append(related_key[i])
+        i = i + 1
+    Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
+    target.fk = adopted
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # The referenced object has been saved, so it carries a real (non-empty)
     # stored key — this is the branch reached once the referenced key is known.
     Requires(len(related_key) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(target.fk))
@@ -108,10 +106,9 @@
     # post-conditions-end
     # impl-start
     if is_empty_placeholder(target.fk):
-        # Adopt the referenced object's stored key into the local attribute.
         adopted = []  # type: List[int]
         i = 0
-        while i < len(related_key):
+        while i < len(related_key) - 1:
             # invariants-start
             Invariant(Acc(list_pred(related_key), 1 / 2))
             Invariant(Acc(list_pred(adopted)))
@@ -119,10 +116,8 @@
             Invariant(0 <= i and i <= len(related_key))
             Invariant(len(adopted) == i)
             Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
-            Invariant(MustTerminate(len(related_key) - i + 1))
             # invariants-end
             adopted.append(related_key[i])
             i = i + 1
-        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
         target.fk = adopted
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # The referenced object has been saved, so it carries a real (non-empty)
     # stored key — this is the branch reached once the referenced key is known.
     Requires(len(related_key) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(target.fk))
@@ -107,8 +105,7 @@
                     stored_seq(target.fk) == Old(stored_seq(target.fk))))
     # post-conditions-end
     # impl-start
-    if is_empty_placeholder(target.fk):
-        # Adopt the referenced object's stored key into the local attribute.
+    if target.fk is None:
         adopted = []  # type: List[int]
         i = 0
         while i < len(related_key):
@@ -119,7 +116,6 @@
             Invariant(0 <= i and i <= len(related_key))
             Invariant(len(adopted) == i)
             Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
-            Invariant(MustTerminate(len(related_key) - i + 1))
             # invariants-end
             adopted.append(related_key[i])
             i = i + 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # The referenced object has been saved, so it carries a real (non-empty)
     # stored key — this is the branch reached once the referenced key is known.
     Requires(len(related_key) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(target.fk))
@@ -108,21 +106,16 @@
     # post-conditions-end
     # impl-start
     if is_empty_placeholder(target.fk):
-        # Adopt the referenced object's stored key into the local attribute.
         adopted = []  # type: List[int]
-        i = 0
-        while i < len(related_key):
+        i = len(related_key)
+        while i > 0:
             # invariants-start
             Invariant(Acc(list_pred(related_key), 1 / 2))
             Invariant(Acc(list_pred(adopted)))
             Invariant(len(related_key) > 0)
             Invariant(0 <= i and i <= len(related_key))
-            Invariant(len(adopted) == i)
-            Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
-            Invariant(MustTerminate(len(related_key) - i + 1))
             # invariants-end
+            i = i - 1
             adopted.append(related_key[i])
-            i = i + 1
-        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
         target.fk = adopted
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # The referenced object has been saved, so it carries a real (non-empty)
     # stored key — this is the branch reached once the referenced key is known.
     Requires(len(related_key) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(target.fk))
@@ -107,22 +105,6 @@
                     stored_seq(target.fk) == Old(stored_seq(target.fk))))
     # post-conditions-end
     # impl-start
-    if is_empty_placeholder(target.fk):
-        # Adopt the referenced object's stored key into the local attribute.
-        adopted = []  # type: List[int]
-        i = 0
-        while i < len(related_key):
-            # invariants-start
-            Invariant(Acc(list_pred(related_key), 1 / 2))
-            Invariant(Acc(list_pred(adopted)))
-            Invariant(len(related_key) > 0)
-            Invariant(0 <= i and i <= len(related_key))
-            Invariant(len(adopted) == i)
-            Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
-            Invariant(MustTerminate(len(related_key) - i + 1))
-            # invariants-end
-            adopted.append(related_key[i])
-            i = i + 1
-        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
-        target.fk = adopted
+    if False:
+        target.fk = related_key
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # The referenced object has been saved, so it carries a real (non-empty)
     # stored key — this is the branch reached once the referenced key is known.
     Requires(len(related_key) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(target.fk))
@@ -108,7 +106,6 @@
     # post-conditions-end
     # impl-start
     if is_empty_placeholder(target.fk):
-        # Adopt the referenced object's stored key into the local attribute.
         adopted = []  # type: List[int]
         i = 0
         while i < len(related_key):
@@ -119,10 +116,9 @@
             Invariant(0 <= i and i <= len(related_key))
             Invariant(len(adopted) == i)
             Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
-            Invariant(MustTerminate(len(related_key) - i + 1))
             # invariants-end
             adopted.append(related_key[i])
             i = i + 1
-        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
+        Assert(ToSeq(adopted) == ToSeq(related_key))
         target.fk = adopted
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13964.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When persisting an object that holds a reference to another, already-saved
  object, the reference is carried locally by a stored-key attribute. If that
  local attribute currently holds an EMPTY PLACEHOLDER value, the persisting
  object adopts the referenced object's stored key into it before the row is
  written, so the two ends agree.

  An "empty placeholder" is any of the recognized empty values a freshly
  initialized key attribute can take: the absent marker (``None``) AND the empty
  textual value (the empty character sequence used by a textual key). Both must
  be treated as unset and overwritten with the referenced object's key. This is
  the crux: a textual key initialized to the empty sequence is just as unset as
  an absent numeric key, and must likewise be filled.

  If, on the other hand, the local attribute ALREADY holds a non-empty stored
  key, it is a deliberate value and must be left exactly as it is.

The local stored-key attribute is modelled as an ``Optional[List[int]]`` of
Unicode code points: the absent marker is ``None`` (an unset numeric key), the
empty sequence ``[]`` is the empty textual value, and a non-empty list is a
concrete textual key. These three are genuinely distinct — ``None`` is NOT the
empty sequence. The referenced object's stored key is a non-empty ``List[int]``
(it has been saved, so it carries a real key).

No callee is axiomatized: the behaviour is emptiness/membership logic over the
object's own attribute and the referenced key, modelled deeply. The set of
recognized empty placeholders is a well-known constant collection; its two
members relevant here (the absent marker and the empty sequence) are spelled out
in the ``is_empty_placeholder`` predicate. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def is_empty_placeholder(value: Optional[List[int]]) -> bool:
    """True iff `value` is one of the recognized empty placeholder values that
    a not-yet-assigned stored-key attribute can hold: the absent marker
    (`None`) or the empty character sequence (`[]`). A non-empty sequence is a
    concrete key and is NOT an empty placeholder. The absent marker and the
    empty sequence are distinct values that BOTH count as empty."""
    Requires(Implies(value is not None, Acc(list_pred(value), 1 / 4)))
    if value is None:
        return True
    return len(value) == 0


@Pure
def stored_seq(value: Optional[List[int]]) -> PSeq[int]:
    """The character sequence currently stored: the value's own sequence when a
    concrete key is present, the empty sequence for the absent marker."""
    Requires(Implies(value is not None, Acc(list_pred(value), 1 / 4)))
    if value is None:
        return PSeq(0).take(0)
    return ToSeq(value)
# pure-end


class SaveTarget:
    def __init__(self, fk: Optional[List[int]]) -> None:
        Requires(Implies(fk is not None, Acc(list_pred(fk))))
        Ensures(Acc(self.fk) and self.fk is fk)  # type: ignore
        Ensures(Implies(self.fk is not None, Acc(list_pred(self.fk))))  # type: ignore
        self.fk = fk


def adopt_referenced_key_if_unset(target: SaveTarget, related_key: List[int]) -> None:
    # pre-conditions-start
    # The local stored-key attribute is the only mutated object (full
    # permission, exact post-state stated below). `related_key` is read-only:
    # required AND ensured at fractional permission (directive 5).
    Requires(Acc(target.fk))
    Requires(Implies(target.fk is not None, Acc(list_pred(target.fk))))
    Requires(Acc(list_pred(related_key), 1 / 2))
    # The referenced object has been saved, so it carries a real (non-empty)
    # stored key — this is the branch reached once the referenced key is known.
    Requires(len(related_key) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(target.fk))
    Ensures(Acc(list_pred(related_key), 1 / 2))
    # The attribute always ends holding a concrete, non-empty stored key.
    Ensures(target.fk is not None)
    Ensures(Acc(list_pred(target.fk)))
    Ensures(len(target.fk) > 0)
    # (1) The discriminating guarantee: if the attribute held an empty
    # placeholder on entry — the absent marker OR the empty character sequence —
    # it now holds the referenced object's stored key. The empty-sequence case
    # is exactly the one that must be filled here.
    Ensures(Implies(Old(is_empty_placeholder(target.fk)),
                    stored_seq(target.fk) == ToSeq(related_key)))
    # (2) Faithfulness: a deliberately-set, non-empty stored key is preserved
    # untouched (same object, same contents).
    Ensures(Implies(not Old(is_empty_placeholder(target.fk)),
                    target.fk is Old(target.fk) and
                    stored_seq(target.fk) == Old(stored_seq(target.fk))))
    # post-conditions-end
    # impl-start
    if is_empty_placeholder(target.fk):
        # Adopt the referenced object's stored key into the local attribute.
        adopted = []  # type: List[int]
        i = 0
        while i < len(related_key):
            # invariants-start
            Invariant(Acc(list_pred(related_key), 1 / 2))
            Invariant(Acc(list_pred(adopted)))
            Invariant(len(related_key) > 0)
            Invariant(0 <= i and i <= len(related_key))
            Invariant(len(adopted) == i)
            Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
            # invariants-end
            adopted.append(related_key[i])
            i = i + 1
        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
        target.fk = adopted
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Positive control (bundle model.py) VERIFIES (15.1s). Prepatch (model_prepatch.py, branch `if target.fk is None:`) FAILS verification: 'Postcondition ... Assertion (len(target.fk) > 0) might not hold' at :94 — G-DIFF reproduced.

7 same-spec wrong-impl attacks (all confirmed same-spec via `adversary same-spec` — impl-region-only edits, axioms/@Pure/Requires/Ensures byte-identical):
- atk_2 (control-flow-effect: unconditional overwrite, drops emptiness guard, clobbers deliberate non-empty key) => weakness: NOT-A-COUNTEREXAMPLE, does not verify (fails faithfulness clause 2).
- atk_3 (boundary: off-by-one, copies related_key[:len-1]) => does not verify (content mismatch vs clause 1).
- atk_4 (partial-domain: `if target.fk is None:` only = prepatch bug re-encoded) => does not verify (fails len>0 on empty-sequence '' case).
- atk_5 (boundary/content: reversed copy) => does not verify.
- atk_6 (control-flow: no-op `if False`, never fills) => does not verify.
- atk_1 (echo #1: `if not is_empty_placeholder: pass else: <copy loop>` — behaviorally identical to gold, different code shape) => CANDIDATE (shares spec AND verifies, 15.9s).
- atk_7 (echo #2: same guard, drop-based Assert(ToSeq(adopted)==ToSeq(related_key)) closing) => CANDIDATE (shares spec AND verifies, 15.0s).

Both CANDIDATEs are behavioral echoes of the gold: they fill the local key with related_key's exact content iff the attribute is an empty placeholder, and leave a non-empty key untouched. Their faithful refined patch is therefore the gold widening (`getattr(self, field.attname) is None` -> `in field.empty_values`), byte-identical to patch.diff (sha1 ae279243... == bundle patch.diff). MATERIALIZED both faithful patches and RAN run_resolve('django__django-13964', ..., timeout=1800): resolved=True, completed=True, note='resolved'. FAIL_TO_PASS test_save_fk_after_parent_with_non_numeric_pk_set_on_child SUCCESS; all 35 PASS_TO_PASS SUCCESS; 0 failures. Per policy (2026-08-06) a same-spec verifying echo whose faithful patch RESOLVES is NOT a weakness. No verifying wrong impl produced a non-resolving patch => verify does not admit an incorrect (non-resolving) implementation here.

refinement.md audit: axioms region empty (meta.json axioms=[]) — confirms 'no consumed @ContractOnly axiom'. Legs: A1 (R: self+FK attribute -> SaveTarget.fk), A2 (R: obj.pk -> related_key, obj.pk-not-None guard -> len>0), A3 (A-reference: `in field.empty_values` modeled deeply by is_empty_placeholder), A4 (I: setattr(...obj.pk) store, attr-name+carrier refined by R), A5 (I: elif not firing / faithfulness). No kind-3 (unexpressible-changed-op) step. A3 correspondence VALID: axiom_check.py (G-AX) reads REAL field.empty_values (=[None,'',[],(),{}], inherited Field default) and asserts membership == is_empty_placeholder on {None,'','foo','0','jeff'} per FK field, and drives REAL Model._prepare_related_fields_for_save end-to-end (textual-key adoption + numeric absent-marker adoption + non-empty-key preservation). Unreachable members [],(),{} irrelevant for scalar FK value; reachable domain {None->empty, ''->empty, concrete-key->not-empty} matches exactly. R/I legs mechanically covered by G-CONF.

Commands:
- bash scripts/nagini_verify.sh <atk> (positive control pass, prepatch fail)
- run_resolve('django__django-13964', faithful_atk_1.diff) => resolved=True.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13964.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When persisting an object that holds a reference to another, already-saved
  object, the reference is carried locally by a stored-key attribute. If that
  local attribute currently holds an EMPTY PLACEHOLDER value, the persisting
  object adopts the referenced object's stored key into it before the row is
  written, so the two ends agree.

  An "empty placeholder" is any of the recognized empty values a freshly
  initialized key attribute can take: the absent marker (``None``) AND the empty
  textual value (the empty character sequence used by a textual key). Both must
  be treated as unset and overwritten with the referenced object's key. This is
  the crux: a textual key initialized to the empty sequence is just as unset as
  an absent numeric key, and must likewise be filled.

  If, on the other hand, the local attribute ALREADY holds a non-empty stored
  key, it is a deliberate value and must be left exactly as it is.

The local stored-key attribute is modelled as an ``Optional[List[int]]`` of
Unicode code points: the absent marker is ``None`` (an unset numeric key), the
empty sequence ``[]`` is the empty textual value, and a non-empty list is a
concrete textual key. These three are genuinely distinct — ``None`` is NOT the
empty sequence. The referenced object's stored key is a non-empty ``List[int]``
(it has been saved, so it carries a real key).

No callee is axiomatized: the behaviour is emptiness/membership logic over the
object's own attribute and the referenced key, modelled deeply. The set of
recognized empty placeholders is a well-known constant collection; its two
members relevant here (the absent marker and the empty sequence) are spelled out
in the ``is_empty_placeholder`` predicate. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def is_empty_placeholder(value: Optional[List[int]]) -> bool:
    """True iff `value` is one of the recognized empty placeholder values that
    a not-yet-assigned stored-key attribute can hold: the absent marker
    (`None`) or the empty character sequence (`[]`). A non-empty sequence is a
    concrete key and is NOT an empty placeholder. The absent marker and the
    empty sequence are distinct values that BOTH count as empty."""
    Requires(Implies(value is not None, Acc(list_pred(value), 1 / 4)))
    if value is None:
        return True
    return len(value) == 0


@Pure
def stored_seq(value: Optional[List[int]]) -> PSeq[int]:
    """The character sequence currently stored: the value's own sequence when a
    concrete key is present, the empty sequence for the absent marker."""
    Requires(Implies(value is not None, Acc(list_pred(value), 1 / 4)))
    if value is None:
        return PSeq(0).take(0)
    return ToSeq(value)
# pure-end


class SaveTarget:
    def __init__(self, fk: Optional[List[int]]) -> None:
        Requires(Implies(fk is not None, Acc(list_pred(fk))))
        Ensures(Acc(self.fk) and self.fk is fk)  # type: ignore
        Ensures(Implies(self.fk is not None, Acc(list_pred(self.fk))))  # type: ignore
        self.fk = fk


def adopt_referenced_key_if_unset(target: SaveTarget, related_key: List[int]) -> None:
    # pre-conditions-start
    # The local stored-key attribute is the only mutated object (full
    # permission, exact post-state stated below). `related_key` is read-only:
    # required AND ensured at fractional permission (directive 5).
    Requires(Acc(target.fk))
    Requires(Implies(target.fk is not None, Acc(list_pred(target.fk))))
    Requires(Acc(list_pred(related_key), 1 / 2))
    # The referenced object has been saved, so it carries a real (non-empty)
    # stored key — this is the branch reached once the referenced key is known.
    Requires(len(related_key) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(target.fk))
    Ensures(Acc(list_pred(related_key), 1 / 2))
    # The attribute always ends holding a concrete, non-empty stored key.
    Ensures(target.fk is not None)
    Ensures(Acc(list_pred(target.fk)))
    Ensures(len(target.fk) > 0)
    # (1) The discriminating guarantee: if the attribute held an empty
    # placeholder on entry — the absent marker OR the empty character sequence —
    # it now holds the referenced object's stored key. The empty-sequence case
    # is exactly the one that must be filled here.
    Ensures(Implies(Old(is_empty_placeholder(target.fk)),
                    stored_seq(target.fk) == ToSeq(related_key)))
    # (2) Faithfulness: a deliberately-set, non-empty stored key is preserved
    # untouched (same object, same contents).
    Ensures(Implies(not Old(is_empty_placeholder(target.fk)),
                    target.fk is Old(target.fk) and
                    stored_seq(target.fk) == Old(stored_seq(target.fk))))
    # post-conditions-end
    # impl-start
    if is_empty_placeholder(target.fk):
        # Adopt the referenced object's stored key into the local attribute.
        adopted = []  # type: List[int]
        i = 0
        while i < len(related_key):
            # invariants-start
            Invariant(Acc(list_pred(related_key), 1 / 2))
            Invariant(Acc(list_pred(adopted)))
            Invariant(len(related_key) > 0)
            Invariant(0 <= i and i <= len(related_key))
            Invariant(len(adopted) == i)
            Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
            # invariants-end
            adopted.append(related_key[i])
            i = i + 1
        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
        target.fk = adopted
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Positive control (bundle model.py) VERIFIES (15.1s). Prepatch (model_prepatch.py, branch `if target.fk is None:`) FAILS verification: 'Postcondition ... Assertion (len(target.fk) > 0) might not hold' at :94 — G-DIFF reproduced.

7 same-spec wrong-impl attacks (all confirmed same-spec via `adversary same-spec` — impl-region-only edits, axioms/@Pure/Requires/Ensures byte-identical):
- atk_2 (control-flow-effect: unconditional overwrite, drops emptiness guard, clobbers deliberate non-empty key) => weakness: NOT-A-COUNTEREXAMPLE, does not verify (fails faithfulness clause 2).
- atk_3 (boundary: off-by-one, copies related_key[:len-1]) => does not verify (content mismatch vs clause 1).
- atk_4 (partial-domain: `if target.fk is None:` only = prepatch bug re-encoded) => does not verify (fails len>0 on empty-sequence '' case).
- atk_5 (boundary/content: reversed copy) => does not verify.
- atk_6 (control-flow: no-op `if False`, never fills) => does not verify.
- atk_1 (echo #1: `if not is_empty_placeholder: pass else: <copy loop>` — behaviorally identical to gold, different code shape) => CANDIDATE (shares spec AND verifies, 15.9s).
- atk_7 (echo #2: same guard, drop-based Assert(ToSeq(adopted)==ToSeq(related_key)) closing) => CANDIDATE (shares spec AND verifies, 15.0s).

Both CANDIDATEs are behavioral echoes of the gold: they fill the local key with related_key's exact content iff the attribute is an empty placeholder, and leave a non-empty key untouched. Their faithful refined patch is therefore the gold widening (`getattr(self, field.attname) is None` -> `in field.empty_values`), byte-identical to patch.diff (sha1 ae279243... == bundle patch.diff). MATERIALIZED both faithful patches and RAN run_resolve('django__django-13964', ..., timeout=1800): resolved=True, completed=True, note='resolved'. FAIL_TO_PASS test_save_fk_after_parent_with_non_numeric_pk_set_on_child SUCCESS; all 35 PASS_TO_PASS SUCCESS; 0 failures. Per policy (2026-08-06) a same-spec verifying echo whose faithful patch RESOLVES is NOT a weakness. No verifying wrong impl produced a non-resolving patch => verify does not admit an incorrect (non-resolving) implementation here.

refinement.md audit: axioms region empty (meta.json axioms=[]) — confirms 'no consumed @ContractOnly axiom'. Legs: A1 (R: self+FK attribute -> SaveTarget.fk), A2 (R: obj.pk -> related_key, obj.pk-not-None guard -> len>0), A3 (A-reference: `in field.empty_values` modeled deeply by is_empty_placeholder), A4 (I: setattr(...obj.pk) store, attr-name+carrier refined by R), A5 (I: elif not firing / faithfulness). No kind-3 (unexpressible-changed-op) step. A3 correspondence VALID: axiom_check.py (G-AX) reads REAL field.empty_values (=[None,'',[],(),{}], inherited Field default) and asserts membership == is_empty_placeholder on {None,'','foo','0','jeff'} per FK field, and drives REAL Model._prepare_related_fields_for_save end-to-end (textual-key adoption + numeric absent-marker adoption + non-empty-key preservation). Unreachable members [],(),{} irrelevant for scalar FK value; reachable domain {None->empty, ''->empty, concrete-key->not-empty} matches exactly. R/I legs mechanically covered by G-CONF.

Commands:
- bash scripts/nagini_verify.sh <atk> (positive control pass, prepatch fail)
- run_resolve('django__django-13964', faithful_atk_1.diff) => resolved=True.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real) audit of nagini bundle django__django-13964. Spec region byte-identical (same-spec on verbatim model.py copy => SAME, exit 0). Gold change reconstructed (base.py:936 `getattr(self,field.attname) is None` -> `in field.empty_values`) and applied to a fresh base_commit (f39634ff22) worktree in /tmp; bundle itself has no patch.diff but mapping.md/refinement.md fully pin the one-line change. Evidence the modeled function `adopt_referenced_key_if_unset` does NOT disagree with the real callee `Model._prepare_related_fields_for_save` on any input in its Requires domain: (1) bundle G-CONF (shadow contract-stripped impl vs REAL patched method) 100,286 inputs, 0 disagreements. (2) My independent spec-postcondition fuzz driving the REAL method and checking all three Ensures clauses directly (not via shadow): 80,000 randomized + boundary inputs over the Requires domain (related_key/obj.pk non-empty), 0 violations — end always non-empty; empty-placeholder local (None or '') adopts referenced key; non-empty local preserved untouched. (3) A-reference holds: real field.empty_values=[None,'',[],(),{}]; membership on {None,'','foo','0','jeff'} matches is_empty_placeholder on every value the FK attr can take. The spec's Requires(len(related_key)>0) excludes only obj.pk=='' (unreachable: branch runs past the `if obj.pk is None: raise` guard and a saved textual PK is non-empty) — a defensible domain narrowing, not a strengthening/disagreement. No diverging input found; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes cleanly (no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier or comment embedding a patched repo symbol, no bug/fix narration). Confirmed via swebench_unified.leakage.screen over the projected spec view (impl region elided): PASSED=True, zero hard failures.

Semantic check (the part the lexical screen can miss): the gold edit widens the FK emptiness test from `getattr(self, field.attname) is None` to `... in field.empty_values` (django/db/models/base.py:936, _prepare_related_fields_for_save), so an empty string '' — not only None — is treated as unset and overwritten with the referenced object's pk. The discriminating content of that fix is ALREADY PUBLIC in the problem_statement: it explicitly states the non-numeric CharField-PK scenario and that 'Instead of product_id being populated with product.sku, it is set to emptystring' and the parent 'does not see the primary key's change'. The requirement that an empty-string local FK adopt the referenced key is thus solver-visible from the task text.

The spec view states this only as abstract desired behaviour ('stated as desired behaviour, not as an edit'): an 'empty placeholder' = absent marker (None) OR empty sequence ([]), both filled with the referenced key; a non-empty key preserved. It does NOT name the patched file (base.py), the patched method (_prepare_related_fields_for_save), field.attname, obj.pk, or the constant field.empty_values, and does not reproduce the `is None`->`in field.empty_values` change. The gold-localizing details (field.empty_values, base.py:936, method name) appear ONLY in mapping.md / refinement.md, which are auditor artifacts, not the consumer spec view. Nothing in the spec view reconstructs the gold edit beyond what the public problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
