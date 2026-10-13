# P2 adversarial audit — pydata__xarray-6461

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_8.py` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
                      present[x_pos] == x_attrs))
     # A scalar second argument carries the empty mapping (identity 0).
     Requires(Implies(x_pos == -1, x_attrs == 0))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(present), 1 / 2))
@@ -65,5 +63,7 @@
     Ensures(Result() == x_attrs)
     # post-conditions-end
     # impl-start
+    if 0 <= x_pos and x_pos < len(present):
+        return present[x_pos]
     return x_attrs
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
                      present[x_pos] == x_attrs))
     # A scalar second argument carries the empty mapping (identity 0).
     Requires(Implies(x_pos == -1, x_attrs == 0))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(present), 1 / 2))
@@ -65,5 +63,7 @@
     Ensures(Result() == x_attrs)
     # post-conditions-end
     # impl-start
-    return x_attrs
+    if 0 <= x_pos and x_pos < len(present):
+        return present[x_pos]
+    return 0
     # impl-end
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
                      present[x_pos] == x_attrs))
     # A scalar second argument carries the empty mapping (identity 0).
     Requires(Implies(x_pos == -1, x_attrs == 0))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(present), 1 / 2))
@@ -65,5 +63,7 @@
     Ensures(Result() == x_attrs)
     # post-conditions-end
     # impl-start
+    if x_pos == -1:
+        return 0
     return x_attrs
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
                      present[x_pos] == x_attrs))
     # A scalar second argument carries the empty mapping (identity 0).
     Requires(Implies(x_pos == -1, x_attrs == 0))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(present), 1 / 2))
@@ -65,5 +63,5 @@
     Ensures(Result() == x_attrs)
     # post-conditions-end
     # impl-start
-    return x_attrs
+    return present[x_pos]
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
                      present[x_pos] == x_attrs))
     # A scalar second argument carries the empty mapping (identity 0).
     Requires(Implies(x_pos == -1, x_attrs == 0))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(present), 1 / 2))
@@ -65,5 +63,5 @@
     Ensures(Result() == x_attrs)
     # post-conditions-end
     # impl-start
-    return x_attrs
+    return present[1]
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
                      present[x_pos] == x_attrs))
     # A scalar second argument carries the empty mapping (identity 0).
     Requires(Implies(x_pos == -1, x_attrs == 0))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(present), 1 / 2))
@@ -65,5 +63,7 @@
     Ensures(Result() == x_attrs)
     # post-conditions-end
     # impl-start
+    if 0 <= x_pos and x_pos + 1 < len(present):
+        return present[x_pos + 1]
     return x_attrs
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
                      present[x_pos] == x_attrs))
     # A scalar second argument carries the empty mapping (identity 0).
     Requires(Implies(x_pos == -1, x_attrs == 0))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(present), 1 / 2))
@@ -65,5 +63,5 @@
     Ensures(Result() == x_attrs)
     # post-conditions-end
     # impl-start
-    return x_attrs
+    return 0
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
                      present[x_pos] == x_attrs))
     # A scalar second argument carries the empty mapping (identity 0).
     Requires(Implies(x_pos == -1, x_attrs == 0))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(present), 1 / 2))
@@ -65,5 +63,12 @@
     Ensures(Result() == x_attrs)
     # post-conditions-end
     # impl-start
+    i = 0
+    while i < len(present):
+        Invariant(Acc(list_pred(present), 1 / 2))
+        Invariant(0 <= i and i <= len(present))
+        if present[i] == x_attrs:
+            return present[i]
+        i += 1
     return x_attrs
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6461.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the conditional-selection routine is asked to preserve the attributes
  of its SECOND positional argument, the attribute mapping it preserves is the
  attribute mapping that BELONGS TO that second argument. If the second
  argument is a bare scalar (it carries no attribute mapping of its own), the
  preserved mapping is the empty mapping.

  The routine is also handed the list of attribute mappings of exactly those
  arguments that actually carry one, in argument order. That list is NOT a
  reliable positional handle on the second argument: a scalar argument
  contributes no entry, so the second argument's mapping need not sit at any
  constant offset in the list (and may be absent from it entirely). The preserved
  mapping must therefore be the second argument's OWN mapping, regardless of
  its position in that list (or its absence from it).

Attribute mappings are modelled as opaque integer identities (distinct
mappings have distinct identities; the empty mapping, which is also what a
scalar carries, is the identity 0). `present` is the list of identities of the
arguments that carry a mapping, in order. `x_attrs` is the identity of the
second argument's own mapping. `x_pos` locates the second argument's mapping
inside `present` (-1 when the second argument carries no mapping, i.e. it is a
scalar). The carried structural fact — an entry actually present in `present`
agrees with the owning argument's identity — is required so the result must be
the second argument's mapping as PRODUCED from that argument, not merely a
value read at a constant list offset.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the changed operation is modelled deeply as the
#  selection of the second argument's own attribute identity.)
# axioms-end


# pure-start
# (No pure helpers needed.)
# pure-end


def attrs_to_keep(present: List[int], x_attrs: int, x_pos: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(present), 1 / 2))
    # `x_pos` locates the second argument's own mapping within `present`, or is
    # -1 when the second argument carries no mapping (it is a scalar).
    Requires(x_pos == -1 or (0 <= x_pos and x_pos < len(present)))
    # When the second argument's mapping is present in the list, the list entry
    # at that position is exactly the second argument's own mapping.
    Requires(Implies(0 <= x_pos and x_pos < len(present),
                     present[x_pos] == x_attrs))
    # A scalar second argument carries the empty mapping (identity 0).
    Requires(Implies(x_pos == -1, x_attrs == 0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(present), 1 / 2))
    # The preserved mapping is the second argument's OWN mapping.
    Ensures(Result() == x_attrs)
    # post-conditions-end
    # impl-start
    return x_attrs
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: attrs_to_keep postcondition is a HARD EQUALITY Ensures(Result()==x_attrs), and x_attrs is fully pinned by the preconditions (present[x_pos]==x_attrs when 0<=x_pos<len(present); x_attrs==0 when x_pos==-1). Therefore every impl that verifies must provably return exactly x_attrs, i.e. is behaviorally identical to gold `getattr(x,"attrs",{})` on all admissible inputs. This makes the spec maximally tight; there is no room for a verifying-but-wrong impl.

A-LEG AUDIT (refinement.md sec B / mapping.md sec 3): bundle declares NO axiomatized callee (@ContractOnly), NO @Pure helper, NO A-reference deep model, hence no axiom_check.py. Verified by inspection of model.py: axioms region empty (comment only), only symbol is attrs_to_keep, no @Pure/@ContractOnly/Assume. All legs A1-A5 are R (type refinement) or I (identical op); A4 return x_attrs == real `getattr(x,"attrs",{})` under the dict<->int identity refinement of A2. No kind-3 step. The claimed model<->patch correspondence to the real `where` keep_attrs lambda holds.

### ATTACKS (8, all same-spec byte-identical to model.py spec region; env, benchmark root benchmark-verified):
Command form: `python -m swebench_unified.adversary weakness nagini pydata__xarray-6461 <atk>`
- atk_1 (control-flow: guarded present[x_pos] else x_attrs): weakness EXIT=0 CANDIDATE (verified 11.8s).
- atk_2 (control-flow: guarded present[x_pos] else 0): weakness EXIT=0 CANDIDATE (verified 12.0s).
- atk_3 (branch on scalar sentinel -> 0 else x_attrs): weakness EXIT=0 CANDIDATE (verified 11.9s).
- atk_4 (partial-domain: unguarded return present[x_pos]): weakness EXIT=2 REJECTED (verification failed - OOB on scalar).
- atk_5 (prepatch echo: return present[1]): weakness EXIT=2 REJECTED (fails on OOB when len<2) => PREPATCH BUG REPRODUCED.
- atk_6 (boundary/off-by-one: present[x_pos+1] else x_attrs): weakness EXIT=2 REJECTED (postcondition violated).
- atk_7 (ungrounded-oracle echo: return 0): weakness EXIT=2 REJECTED (postcondition fails when x_attrs!=0).
- atk_8 (control-flow-effect: linear search present for ==x_attrs, else x_attrs): weakness EXIT=0 CANDIDATE (verified 10.3s).

RESOLVE RUNS (protocol step 2 - materialized faithful patch RUN through official harness via swebench_unified.harness.run_resolve, timeout 1800, retries 1):
Command form: `python resolve_one.py atk_N patch_atk_N.diff`
- atk_1 -> resolved=True completed=True (patch byte-identical to gold body).
- atk_2 -> resolved=True completed=True (patch byte-identical to gold body).
- atk_3 -> resolved=True completed=True (distinct faithful form: {} if not hasattr(x,'attrs') else getattr(x,'attrs',{})).
- atk_8 -> resolved=True completed=True (distinct faithful form: next((a for a in attrs if a==getattr(x,'attrs',{})), getattr(x,'attrs',{}))).
Positive control (model.py impl 'return x_attrs') verifies: VERIFIED 12.6s.

CONCLUSION: All 4 verifying candidates' faithful refined patches RESOLVE under the official harness; all wrong-mechanism impls (positional-offset read, unguarded read, off-by-one, ungrounded constant) are REJECTED by the verifier. No verify=>correct gap exists. verify does NOT admit an incorrect impl for this bundle. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_8.py` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6461.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the conditional-selection routine is asked to preserve the attributes
  of its SECOND positional argument, the attribute mapping it preserves is the
  attribute mapping that BELONGS TO that second argument. If the second
  argument is a bare scalar (it carries no attribute mapping of its own), the
  preserved mapping is the empty mapping.

  The routine is also handed the list of attribute mappings of exactly those
  arguments that actually carry one, in argument order. That list is NOT a
  reliable positional handle on the second argument: a scalar argument
  contributes no entry, so the second argument's mapping need not sit at any
  constant offset in the list (and may be absent from it entirely). The preserved
  mapping must therefore be the second argument's OWN mapping, regardless of
  its position in that list (or its absence from it).

Attribute mappings are modelled as opaque integer identities (distinct
mappings have distinct identities; the empty mapping, which is also what a
scalar carries, is the identity 0). `present` is the list of identities of the
arguments that carry a mapping, in order. `x_attrs` is the identity of the
second argument's own mapping. `x_pos` locates the second argument's mapping
inside `present` (-1 when the second argument carries no mapping, i.e. it is a
scalar). The carried structural fact — an entry actually present in `present`
agrees with the owning argument's identity — is required so the result must be
the second argument's mapping as PRODUCED from that argument, not merely a
value read at a constant list offset.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the changed operation is modelled deeply as the
#  selection of the second argument's own attribute identity.)
# axioms-end


# pure-start
# (No pure helpers needed.)
# pure-end


def attrs_to_keep(present: List[int], x_attrs: int, x_pos: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(present), 1 / 2))
    # `x_pos` locates the second argument's own mapping within `present`, or is
    # -1 when the second argument carries no mapping (it is a scalar).
    Requires(x_pos == -1 or (0 <= x_pos and x_pos < len(present)))
    # When the second argument's mapping is present in the list, the list entry
    # at that position is exactly the second argument's own mapping.
    Requires(Implies(0 <= x_pos and x_pos < len(present),
                     present[x_pos] == x_attrs))
    # A scalar second argument carries the empty mapping (identity 0).
    Requires(Implies(x_pos == -1, x_attrs == 0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(present), 1 / 2))
    # The preserved mapping is the second argument's OWN mapping.
    Ensures(Result() == x_attrs)
    # post-conditions-end
    # impl-start
    return x_attrs
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: attrs_to_keep postcondition is a HARD EQUALITY Ensures(Result()==x_attrs), and x_attrs is fully pinned by the preconditions (present[x_pos]==x_attrs when 0<=x_pos<len(present); x_attrs==0 when x_pos==-1). Therefore every impl that verifies must provably return exactly x_attrs, i.e. is behaviorally identical to gold `getattr(x,"attrs",{})` on all admissible inputs. This makes the spec maximally tight; there is no room for a verifying-but-wrong impl.

A-LEG AUDIT (refinement.md sec B / mapping.md sec 3): bundle declares NO axiomatized callee (@ContractOnly), NO @Pure helper, NO A-reference deep model, hence no axiom_check.py. Verified by inspection of model.py: axioms region empty (comment only), only symbol is attrs_to_keep, no @Pure/@ContractOnly/Assume. All legs A1-A5 are R (type refinement) or I (identical op); A4 return x_attrs == real `getattr(x,"attrs",{})` under the dict<->int identity refinement of A2. No kind-3 step. The claimed model<->patch correspondence to the real `where` keep_attrs lambda holds.

### ATTACKS (8, all same-spec byte-identical to model.py spec region; env, benchmark root benchmark-verified):
Command form: `python -m swebench_unified.adversary weakness nagini pydata__xarray-6461 <atk>`
- atk_1 (control-flow: guarded present[x_pos] else x_attrs): weakness EXIT=0 CANDIDATE (verified 11.8s).
- atk_2 (control-flow: guarded present[x_pos] else 0): weakness EXIT=0 CANDIDATE (verified 12.0s).
- atk_3 (branch on scalar sentinel -> 0 else x_attrs): weakness EXIT=0 CANDIDATE (verified 11.9s).
- atk_4 (partial-domain: unguarded return present[x_pos]): weakness EXIT=2 REJECTED (verification failed - OOB on scalar).
- atk_5 (prepatch echo: return present[1]): weakness EXIT=2 REJECTED (fails on OOB when len<2) => PREPATCH BUG REPRODUCED.
- atk_6 (boundary/off-by-one: present[x_pos+1] else x_attrs): weakness EXIT=2 REJECTED (postcondition violated).
- atk_7 (ungrounded-oracle echo: return 0): weakness EXIT=2 REJECTED (postcondition fails when x_attrs!=0).
- atk_8 (control-flow-effect: linear search present for ==x_attrs, else x_attrs): weakness EXIT=0 CANDIDATE (verified 10.3s).

RESOLVE RUNS (protocol step 2 - materialized faithful patch RUN through official harness via swebench_unified.harness.run_resolve, timeout 1800, retries 1):
Command form: `python resolve_one.py atk_N patch_atk_N.diff`
- atk_1 -> resolved=True completed=True (patch byte-identical to gold body).
- atk_2 -> resolved=True completed=True (patch byte-identical to gold body).
- atk_3 -> resolved=True completed=True (distinct faithful form: {} if not hasattr(x,'attrs') else getattr(x,'attrs',{})).
- atk_8 -> resolved=True completed=True (distinct faithful form: next((a for a in attrs if a==getattr(x,'attrs',{})), getattr(x,'attrs',{}))).
Positive control (model.py impl 'return x_attrs') verifies: VERIFIED 12.6s.

CONCLUSION: All 4 verifying candidates' faithful refined patches RESOLVE under the official harness; all wrong-mechanism impls (positional-offset read, unguarded read, off-by-one, ungrounded constant) are REJECTED by the verifier. No verify=>correct gap exists. verify does NOT admit an incorrect impl for this bundle. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real patched callee. Model: attrs_to_keep(present,x_attrs,x_pos) -> x_attrs with post Result()==x_attrs. Real repo (base 851dadeb, patched): keep_attrs=lambda attrs,context: getattr(x,'attrs',{}) at xarray/core/computation.py:1832 — returns the second positional arg's own attrs, ignoring the attrs list entirely. Under mapping.md's dict<->int identity abstraction (empty/scalar -> 0), x_attrs == identity of getattr(x,'attrs',{}). Evidence: (1) shipped conformance_check.py against the REAL patched repo = 0 disagreements over 101041 inputs (15 boundary + 100000 captured-callback fuzz + 1026 end-to-end, pinned seed 6461); (2) independent probe capturing the genuine constructed callback over 20000 random scalar/DataArray second-arg configs, feeding arbitrary 'present' lists = 0 divergences (real cb ignores the list, returns x's attrs = x_attrs); (3) model.py verifies in Nagini (10.8s); (4) same-spec toolkit confirms spec region byte-identical. Preconditions faithfully encode the objs=[a.attrs for a in _all_of_type(args,DataArray)] structure (present[x_pos]==x_attrs in-bounds; scalar => x_pos==-1,x_attrs==0). The spec is exactly as strong as the real behavior — no over-constraint, no drift. Spec senses both faces of the bug (prepatch present[1] fails on bounds; guarded prepatch fails Result()==x_attrs when x_pos!=1), consistent with the gold's IndexError-on-scalar fix. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (swebench_unified.leakage.screen over spec_view) passes with zero hard failures: no diff markers, no gold-patch line reproduced (>=8 normalized chars), no patched file path (xarray/core/computation.py absent), no patched-symbol identifier/comment collision, no narration terms. Verified by direct run.

Semantic review of the spec view vs. the PUBLIC problem_statement (not hints_text):
- Gold edit: `keep_attrs = lambda attrs, context: attrs[1]` -> `getattr(x, "attrs", {})`. The problem_statement ALREADY publicly quotes the buggy line `attrs[1]`, the in-code comment 'keep the attributes of x, the second parameter, by default', the scalar-second-arg repro `xr.where(cond, 1, 0)`, and the `IndexError: list index out of range`. So the desired behavior (return the second positional argument's OWN attrs; the positional index breaks for a scalar) is fully public already.
- The spec view describes that same behavior abstractly: preserved mapping is the second argument's own mapping (postcondition `Result() == x_attrs`), the list `present` is not a reliable positional handle, and a scalar carries the empty mapping (identity 0). It abstracts dicts to opaque int identities and reveals nothing about the concrete gold fix expression (`getattr`, `{}`) beyond what the public issue states.
- The only patched repo symbol, `where`, is already public via `xr.where` in the problem_statement, so the mechanical symbol check correctly skips it.

The tight postcondition specifies the publicly-stated target behavior; it does not disclose the gold edit beyond the problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
