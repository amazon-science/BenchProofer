# P2 adversarial audit — pydata__xarray-4687

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,25 +75,7 @@
     Ensures(Implies(mode == 1, ToSeq(Result()) == ToSeq(attrs[1])))
     # post-conditions-end
     # impl-start
+    # Pre-patch: mode never threaded into combine; result always empty.
     result = []  # type: List[int]
-    if mode == 0 and default_mode_drops():
-        return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
-    src = attrs[1]
-    i = 0
-    while i < len(src):
-        # invariants-start
-        Invariant(Acc(list_pred(attrs), 1 / 2))
-        Invariant(len(attrs) == 3)
-        Invariant(Acc(list_pred(attrs[1]), 1 / 2))
-        Invariant(src is attrs[1])
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(src))
-        Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
-        result.append(src[i])
-        i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,22 +78,18 @@
     result = []  # type: List[int]
     if mode == 0 and default_mode_drops():
         return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
-    src = attrs[1]
+    src = attrs[0]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(attrs), 1 / 2))
         Invariant(len(attrs) == 3)
         Invariant(Acc(list_pred(attrs[1]), 1 / 2))
-        Invariant(src is attrs[1])
+        Invariant(Acc(list_pred(attrs[0]), 1 / 2))
+        Invariant(src is attrs[0])
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
         result.append(src[i])
         i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,22 +78,18 @@
     result = []  # type: List[int]
     if mode == 0 and default_mode_drops():
         return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
-    src = attrs[1]
+    src = attrs[2]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(attrs), 1 / 2))
         Invariant(len(attrs) == 3)
         Invariant(Acc(list_pred(attrs[1]), 1 / 2))
-        Invariant(src is attrs[1])
+        Invariant(Acc(list_pred(attrs[2]), 1 / 2))
+        Invariant(src is attrs[2])
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
         result.append(src[i])
         i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,12 +78,9 @@
     result = []  # type: List[int]
     if mode == 0 and default_mode_drops():
         return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
     src = attrs[1]
     i = 0
-    while i < len(src):
-        # invariants-start
+    while i + 1 < len(src):
         Invariant(Acc(list_pred(attrs), 1 / 2))
         Invariant(len(attrs) == 3)
         Invariant(Acc(list_pred(attrs[1]), 1 / 2))
@@ -91,9 +88,7 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
         result.append(src[i])
         i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -76,14 +76,11 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if mode == 0 and default_mode_drops():
+    if mode == 1:
         return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
     src = attrs[1]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(attrs), 1 / 2))
         Invariant(len(attrs) == 3)
         Invariant(Acc(list_pred(attrs[1]), 1 / 2))
@@ -91,9 +88,7 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
         result.append(src[i])
         i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,12 +78,9 @@
     result = []  # type: List[int]
     if mode == 0 and default_mode_drops():
         return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
     src = attrs[1]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(attrs), 1 / 2))
         Invariant(len(attrs) == 3)
         Invariant(Acc(list_pred(attrs[1]), 1 / 2))
@@ -91,9 +88,7 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
-        result.append(src[i])
+        result.append(src[i] + 1)
         i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -76,14 +76,9 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if mode == 0 and default_mode_drops():
-        return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
     src = attrs[1]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(attrs), 1 / 2))
         Invariant(len(attrs) == 3)
         Invariant(Acc(list_pred(attrs[1]), 1 / 2))
@@ -91,9 +86,7 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
         result.append(src[i])
         i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,22 +78,20 @@
     result = []  # type: List[int]
     if mode == 0 and default_mode_drops():
         return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
     src = attrs[1]
+    if len(src) == 0:
+        src = attrs[0]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(attrs), 1 / 2))
         Invariant(len(attrs) == 3)
         Invariant(Acc(list_pred(attrs[1]), 1 / 2))
-        Invariant(src is attrs[1])
+        Invariant(Acc(list_pred(attrs[0]), 1 / 2))
+        Invariant(src is attrs[1] or src is attrs[0])
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
         result.append(src[i])
         i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
     return result
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,12 +78,9 @@
     result = []  # type: List[int]
     if mode == 0 and default_mode_drops():
         return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
     src = attrs[1]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(attrs), 1 / 2))
         Invariant(len(attrs) == 3)
         Invariant(Acc(list_pred(attrs[1]), 1 / 2))
@@ -91,9 +88,8 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
         result.append(src[i])
         i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
+    result.append(42)
     return result
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -76,14 +76,9 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if mode == 0 and default_mode_drops():
-        return result
-    # PRESERVE (or a non-dropping default): copy the first-choice operand's
-    # payload (positional index 1) element by element into the result.
     src = attrs[1]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(attrs), 1 / 2))
         Invariant(len(attrs) == 3)
         Invariant(Acc(list_pred(attrs[1]), 1 / 2))
@@ -91,9 +86,9 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        # invariants-end
         result.append(src[i])
         i = i + 1
-    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
+    if mode == 0:
+        return result
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-4687.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A conditional-selection operation takes three positional operands in a
  definite order -- a predicate operand, a first-choice operand, and a
  second-choice operand -- each carrying an attribute payload, and produces a
  result whose attribute payload is governed by an attribute-handling mode:

    * mode DEFAULT  -- the historical behaviour: the result carries no
      attribute payload (the empty payload), regardless of the operands.
    * mode PRESERVE -- the result carries exactly the attribute payload of the
      first-choice operand (the operand at positional slot one), so that an
      attribute payload on that operand survives the selection rather than
      being discarded.

The selection of which operand's payload survives is the load-bearing
behaviour: under PRESERVE the surviving payload is the one at positional slot
one (the first-choice operand), never that of the predicate operand
(slot zero) nor that of the second-choice operand (slot two), and never the
empty payload when the first-choice operand carries one.

Attribute payloads are modelled as `List[int]` (an opaque content-identified
payload; equality of payloads is content equality). The three operands'
payloads are presented in positional order as a `List[List[int]]` of length 3.
The DEFAULT mode resolves through an unchanged global-option reader, modelled
by the `default_mode_drops` axiom: under the ambient default configuration that
reader yields the dropping (empty-payload) behaviour.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def default_mode_drops() -> bool:
    """Unchanged global-option reader: when the attribute-handling mode is left
    unspecified, the ambient default configuration resolves it to the dropping
    behaviour (the result carries the empty attribute payload). Provenance and
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() == True)
# axioms-end


# pure-start
@Pure
def empty_payload() -> PSeq[int]:
    """The empty attribute payload."""
    return PSeq(0).take(0)
# pure-end


def select_payload(attrs: List[List[int]], mode: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(attrs), 1 / 2))
    Requires(len(attrs) == 3)
    Requires(Acc(list_pred(attrs[1]), 1 / 2))
    # mode 0 == DEFAULT (unspecified), mode 1 == PRESERVE
    Requires(mode == 0 or mode == 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(attrs), 1 / 2))
    Ensures(len(attrs) == 3)
    Ensures(Acc(list_pred(attrs[1]), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # DEFAULT mode drops every operand's payload: the result is empty.
    Ensures(Implies(mode == 0, ToSeq(Result()) == empty_payload()))
    # PRESERVE mode keeps exactly the first-choice operand's payload (index 1):
    # not the predicate operand's (index 0), not the second-choice operand's
    # (index 2), and not the empty payload when index 1 carries one.
    Ensures(Implies(mode == 1, ToSeq(Result()) == ToSeq(attrs[1])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if mode == 0 and default_mode_drops():
        return result
    # PRESERVE (or a non-dropping default): copy the first-choice operand's
    # payload (positional index 1) element by element into the result.
    src = attrs[1]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(attrs), 1 / 2))
        Invariant(len(attrs) == 3)
        Invariant(Acc(list_pred(attrs[1]), 1 / 2))
        Invariant(src is attrs[1])
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for pydata__xarray-4687 (nagini). module run via python (SBU_PYTHON). Positive control = bundle model.py verbatim: `bash scripts/nagini_verify.sh .../pos_control.py` => VERIFIED (15.3s).

SPEC SHAPE: select_payload(attrs: List[List[int]] len 3, mode in {0,1}). Requires grants Acc(list_pred(attrs),1/2) + Acc(list_pred(attrs[1]),1/2) ONLY (not attrs[0]/attrs[2]). Postconditions fully pin output CONTENT on the entire modeled domain: mode==0 -> ToSeq(Result())==empty_payload() (empty); mode==1 -> ToSeq(Result())==ToSeq(attrs[1]). No slack anywhere in the domain.

10 DISTINCT same-spec wrong impls built (spec byte-identical, only impl region edited; `adversary same-spec` returns SAME for all 10). weakness runs done concurrently in batches of 3 (each = JVM+Z3):
 atk_1 prepatch bug (always empty) -> EXIT2, fails mode==1 postcondition (prepatch reproduced).
 atk_2 PRESERVE picks index 0 (cond) -> EXIT2, insufficient permission to read attrs[0].
 atk_3 PRESERVE picks index 2 (y) -> EXIT2, insufficient permission to read attrs[2].
 atk_4 off-by-one (drops last elt) -> EXIT2, fails mode==1 postcondition.
 atk_5 control-flow swap (mode0 keeps / mode1 drops) -> EXIT2, fails mode==1 postcondition.
 atk_6 value corruption (src[i]+1) -> EXIT2, fails content loop invariant.
 atk_7 ungrounded-oracle echo (attrs[1] for BOTH modes) -> EXIT2, fails mode==0 postcondition.
 atk_8 partial-domain (empty attrs[1] -> return attrs[0]) -> EXIT2, insufficient permission to read attrs[0].
 atk_9 suffix corruption (append 42) -> EXIT2, fails mode==1 postcondition.
 atk_10 mode==0 returns attrs[1] not empty -> EXIT2, fails mode==0 postcondition.

Command for each: `python -m swebench_unified.adversary weakness nagini pydata__xarray-4687 <atk>` (outputs in weak_N.out). Failure reasons confirmed genuine via direct `scripts/nagini_verify.sh` (real Postcondition/Invariant/permission errors, NOT syntax/infra artifacts). ZERO CANDIDATEs (no attack shares-spec-AND-verifies), so no faithful patch needed materializing -> no run_resolve required; falsification attempted and failed for all 10.

The index-0/index-2 attacks are blocked structurally (spec grants read permission only to attrs[1]), and all content deviations are caught by the two exact-content postconditions -> the spec admits no incorrect impl.

REFINEMENT.MD A-LEG AUDIT: every leg is R / A-consumed / A-reference / I, NO kind-3. A3 (A-consumed) default_mode_drops <-> unchanged _get_keep_attrs(default=False): weakest-fact axiom, validated by axiom_check.py::check_default_resolves_to_drop against real installed xarray (OPTIONS['keep_attrs']=='default', resolves to False->drop); moreover the mode==0 postcondition pins empty independently. A4 (A-reference) PRESERVE deep model ToSeq(Result())==ToSeq(attrs[1]) <-> merge_attrs(lambda attrs,context: attrs[1]): the genuinely-changed combine op is modeled DEEPLY (spelled-out index-1 copy loop), NOT hidden behind a consumed axiom; validated == real merge_attrs on 6 boundary + 5000 fuzz lists and end-to-end (preserved.attrs=={'attr':'x'}, != cond, != y) by axiom_check.py. A1/A2/A5 are R (None/True<->0/1; positional [cond,x,y]=[0,1,2] so index1=x=first-choice; dict payload<->List[int] content). Correspondence to the real callees holds. Gold patch (patch.diff) matches: adds keep_attrs=None, resolves None via _get_keep_attrs(default=False), installs lambda attrs,context: attrs[1] on True, threads keep_attrs into apply_ufunc.

VERDICT SOUND: >=5 (10) distinct same-spec wrong impls run, none verifies (no CANDIDATE), positive control verifies, prepatch reproduced, refinement A-legs sound. verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-4687.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A conditional-selection operation takes three positional operands in a
  definite order -- a predicate operand, a first-choice operand, and a
  second-choice operand -- each carrying an attribute payload, and produces a
  result whose attribute payload is governed by an attribute-handling mode:

    * mode DEFAULT  -- the historical behaviour: the result carries no
      attribute payload (the empty payload), regardless of the operands.
    * mode PRESERVE -- the result carries exactly the attribute payload of the
      first-choice operand (the operand at positional slot one), so that an
      attribute payload on that operand survives the selection rather than
      being discarded.

The selection of which operand's payload survives is the load-bearing
behaviour: under PRESERVE the surviving payload is the one at positional slot
one (the first-choice operand), never that of the predicate operand
(slot zero) nor that of the second-choice operand (slot two), and never the
empty payload when the first-choice operand carries one.

Attribute payloads are modelled as `List[int]` (an opaque content-identified
payload; equality of payloads is content equality). The three operands'
payloads are presented in positional order as a `List[List[int]]` of length 3.
The DEFAULT mode resolves through an unchanged global-option reader, modelled
by the `default_mode_drops` axiom: under the ambient default configuration that
reader yields the dropping (empty-payload) behaviour.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def default_mode_drops() -> bool:
    """Unchanged global-option reader: when the attribute-handling mode is left
    unspecified, the ambient default configuration resolves it to the dropping
    behaviour (the result carries the empty attribute payload). Provenance and
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() == True)
# axioms-end


# pure-start
@Pure
def empty_payload() -> PSeq[int]:
    """The empty attribute payload."""
    return PSeq(0).take(0)
# pure-end


def select_payload(attrs: List[List[int]], mode: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(attrs), 1 / 2))
    Requires(len(attrs) == 3)
    Requires(Acc(list_pred(attrs[1]), 1 / 2))
    # mode 0 == DEFAULT (unspecified), mode 1 == PRESERVE
    Requires(mode == 0 or mode == 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(attrs), 1 / 2))
    Ensures(len(attrs) == 3)
    Ensures(Acc(list_pred(attrs[1]), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # DEFAULT mode drops every operand's payload: the result is empty.
    Ensures(Implies(mode == 0, ToSeq(Result()) == empty_payload()))
    # PRESERVE mode keeps exactly the first-choice operand's payload (index 1):
    # not the predicate operand's (index 0), not the second-choice operand's
    # (index 2), and not the empty payload when index 1 carries one.
    Ensures(Implies(mode == 1, ToSeq(Result()) == ToSeq(attrs[1])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if mode == 0 and default_mode_drops():
        return result
    # PRESERVE (or a non-dropping default): copy the first-choice operand's
    # payload (positional index 1) element by element into the result.
    src = attrs[1]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(attrs), 1 / 2))
        Invariant(len(attrs) == 3)
        Invariant(Acc(list_pred(attrs[1]), 1 / 2))
        Invariant(src is attrs[1])
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for pydata__xarray-4687 (nagini). module run via python (SBU_PYTHON). Positive control = bundle model.py verbatim: `bash scripts/nagini_verify.sh .../pos_control.py` => VERIFIED (15.3s).

SPEC SHAPE: select_payload(attrs: List[List[int]] len 3, mode in {0,1}). Requires grants Acc(list_pred(attrs),1/2) + Acc(list_pred(attrs[1]),1/2) ONLY (not attrs[0]/attrs[2]). Postconditions fully pin output CONTENT on the entire modeled domain: mode==0 -> ToSeq(Result())==empty_payload() (empty); mode==1 -> ToSeq(Result())==ToSeq(attrs[1]). No slack anywhere in the domain.

10 DISTINCT same-spec wrong impls built (spec byte-identical, only impl region edited; `adversary same-spec` returns SAME for all 10). weakness runs done concurrently in batches of 3 (each = JVM+Z3):
 atk_1 prepatch bug (always empty) -> EXIT2, fails mode==1 postcondition (prepatch reproduced).
 atk_2 PRESERVE picks index 0 (cond) -> EXIT2, insufficient permission to read attrs[0].
 atk_3 PRESERVE picks index 2 (y) -> EXIT2, insufficient permission to read attrs[2].
 atk_4 off-by-one (drops last elt) -> EXIT2, fails mode==1 postcondition.
 atk_5 control-flow swap (mode0 keeps / mode1 drops) -> EXIT2, fails mode==1 postcondition.
 atk_6 value corruption (src[i]+1) -> EXIT2, fails content loop invariant.
 atk_7 ungrounded-oracle echo (attrs[1] for BOTH modes) -> EXIT2, fails mode==0 postcondition.
 atk_8 partial-domain (empty attrs[1] -> return attrs[0]) -> EXIT2, insufficient permission to read attrs[0].
 atk_9 suffix corruption (append 42) -> EXIT2, fails mode==1 postcondition.
 atk_10 mode==0 returns attrs[1] not empty -> EXIT2, fails mode==0 postcondition.

Command for each: `python -m swebench_unified.adversary weakness nagini pydata__xarray-4687 <atk>` (outputs in weak_N.out). Failure reasons confirmed genuine via direct `scripts/nagini_verify.sh` (real Postcondition/Invariant/permission errors, NOT syntax/infra artifacts). ZERO CANDIDATEs (no attack shares-spec-AND-verifies), so no faithful patch needed materializing -> no run_resolve required; falsification attempted and failed for all 10.

The index-0/index-2 attacks are blocked structurally (spec grants read permission only to attrs[1]), and all content deviations are caught by the two exact-content postconditions -> the spec admits no incorrect impl.

REFINEMENT.MD A-LEG AUDIT: every leg is R / A-consumed / A-reference / I, NO kind-3. A3 (A-consumed) default_mode_drops <-> unchanged _get_keep_attrs(default=False): weakest-fact axiom, validated by axiom_check.py::check_default_resolves_to_drop against real installed xarray (OPTIONS['keep_attrs']=='default', resolves to False->drop); moreover the mode==0 postcondition pins empty independently. A4 (A-reference) PRESERVE deep model ToSeq(Result())==ToSeq(attrs[1]) <-> merge_attrs(lambda attrs,context: attrs[1]): the genuinely-changed combine op is modeled DEEPLY (spelled-out index-1 copy loop), NOT hidden behind a consumed axiom; validated == real merge_attrs on 6 boundary + 5000 fuzz lists and end-to-end (preserved.attrs=={'attr':'x'}, != cond, != y) by axiom_check.py. A1/A2/A5 are R (None/True<->0/1; positional [cond,x,y]=[0,1,2] so index1=x=first-choice; dict payload<->List[int] content). Correspondence to the real callees holds. Gold patch (patch.diff) matches: adds keep_attrs=None, resolves None via _get_keep_attrs(default=False), installs lambda attrs,context: attrs[1] on True, threads keep_attrs into apply_ufunc.

VERDICT SOUND: >=5 (10) distinct same-spec wrong impls run, none verifies (no CANDIDATE), positive control verifies, prepatch reproduced, refinement A-legs sound. verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for pydata__xarray-4687 nagini bundle. Spec region byte-identical (same-spec exit 0 on model echo); model verifies with pinned Nagini (14.8s).

Modeled domain (Requires): mode in {0,1}, attrs is List[List[int]] of fixed length 3. keep_attrs bool/str/callable general forms are explicitly out of domain and not exercised by the F2P test.

DEFAULT (mode==0): spec Ensures Result()==empty_payload(). Real repo path: keep_attrs=None -> _get_keep_attrs(default=False) -> False -> 'drop' -> {}. Confirmed against installed xarray 0.15.1: OPTIONS['keep_attrs']=='default' and _get_keep_attrs(default=False) is False. Matches spec.

PRESERVE (mode==1): spec Ensures ToSeq(Result())==ToSeq(attrs[1]). Real repo path: gold patch installs combiner `lambda attrs, context: attrs[1]`; merge_attrs callable branch returns combine_attrs(variable_attrs, context)=attrs[1] (= x.attrs, positional index 1). Simulated the real base_commit merge_attrs callable-branch semantics across the modeled domain (empty payloads, distinct payloads, mixed) -- every case yields attrs[1], matching the spec.

The only merge_attrs edge case (`not variable_attrs -> None`) fires solely on an EMPTY operand list, which is outside the modeled domain (length fixed at 3, always truthy). No divergence exists in the modeled domain. The spec is a faithful abstraction, refined per mapping.md/refinement.md; it is neither too strong nor drifting from real repo behavior. Note: the worktree was at an unrelated old commit (1757dff) with the patch pre-applied and no numpy, so I grounded real-callee checks on the verbatim gold patch plus a directly installed xarray.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Evaluated the canonical spec view (recomputed via swebench_unified.markers.spec_view with get_backend('nagini').language; matches the frozen model.py, impl region elided as '... implementation elided — supplied by the consumer'). The gold edit (patch.diff) is a code change to xarray/core/computation.py::where: add param keep_attrs=None; resolve None via _get_keep_attrs(default=False); for True install combiner `lambda attrs, context: attrs[1]`; thread keep_attrs into apply_ufunc. The spec view discloses NONE of this mechanism. It is written in fully abstracted behavioural terms ('conditional-selection operation', 'three positional operands', 'attribute-handling mode DEFAULT/PRESERVE', 'attribute payload as List[int]'), with the impl region elided. No gold-patch/repo symbols appear anywhere in the view: no `where`, `keep_attrs`, `apply_ufunc`, `merge_attrs`, `_get_keep_attrs`, `lambda`, `attrs[1]`, `xarray`, `DataArray`, `computation.py`. The axiom is abstracted as an 'unchanged global-option reader' whose provenance points only to doc/check files (mapping.md / axiom_check.py), which are NOT part of the spec view. The only precise fact the spec pins is the required postcondition — PRESERVE keeps exactly the first-choice/positional-index-1 operand's payload (never index 0 predicate, never index 2, never empty). This is the behavioural contract any solution must satisfy, stated as desired behaviour not as an edit, and is fully anticipated by the PUBLIC problem_statement: the issue title 'xr.where not preserving attributes', the request that 'Attributes should be preserved or at least there should be a choice (e.g. pass kwargs to apply_ufunc so keep_attrs=True can be passed)', and the second MCVE whose Expected Output is x's attrs ({'foo':'bar'}). The spec therefore reveals strictly LESS than the public problem_statement (which even names apply_ufunc/keep_attrs), and nothing about HOW the gold patch implements it. G-LEAK lexical screen in meta.json also passed. Comparison intentionally excludes hints_text; even so, no leakage beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
