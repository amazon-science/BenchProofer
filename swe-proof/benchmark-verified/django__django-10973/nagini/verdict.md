# P2 adversarial audit — django__django-10973

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_4.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -45,7 +44,6 @@
 def password_env_value(passwd: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(passwd), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(passwd), 1 / 2))
@@ -59,17 +57,14 @@
     result = []  # type: List[int]
     i = 0
     while i < len(passwd):
-        # invariants-start
         Invariant(Acc(list_pred(passwd), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(passwd))
-        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
-        Invariant(MustTerminate(len(passwd) - i + 1))
-        # invariants-end
         c = passwd[i]
-        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
-        result = result + [c]
+        if c == 58:
+            result = result + [92, 58]
+        else:
+            result = result + [c]
         i = i + 1
-    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -45,7 +44,6 @@
 def password_env_value(passwd: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(passwd), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(passwd), 1 / 2))
@@ -58,18 +56,14 @@
     # impl-start
     result = []  # type: List[int]
     i = 0
-    while i < len(passwd):
-        # invariants-start
+    while i + 1 < len(passwd):
         Invariant(Acc(list_pred(passwd), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(passwd))
         Invariant(ToSeq(result) == ToSeq(passwd).take(i))
-        Invariant(MustTerminate(len(passwd) - i + 1))
-        # invariants-end
         c = passwd[i]
         Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
         result = result + [c]
         i = i + 1
-    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -45,7 +44,6 @@
 def password_env_value(passwd: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(passwd), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(passwd), 1 / 2))
@@ -57,19 +55,15 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
+    if len(passwd) > 0:
+        result = result + [passwd[0]]
     i = 0
     while i < len(passwd):
-        # invariants-start
         Invariant(Acc(list_pred(passwd), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(passwd))
-        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
-        Invariant(MustTerminate(len(passwd) - i + 1))
-        # invariants-end
         c = passwd[i]
-        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
         result = result + [c]
         i = i + 1
-    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -45,7 +44,6 @@
 def password_env_value(passwd: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(passwd), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(passwd), 1 / 2))
@@ -57,19 +55,8 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(passwd):
-        # invariants-start
+    while True:
         Invariant(Acc(list_pred(passwd), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(passwd))
-        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
-        Invariant(MustTerminate(len(passwd) - i + 1))
-        # invariants-end
-        c = passwd[i]
-        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -45,7 +44,6 @@
 def password_env_value(passwd: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(passwd), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(passwd), 1 / 2))
@@ -57,19 +55,15 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(passwd):
-        # invariants-start
+    i = len(passwd)
+    while i > 0:
         Invariant(Acc(list_pred(passwd), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(passwd))
-        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
-        Invariant(MustTerminate(len(passwd) - i + 1))
-        # invariants-end
-        c = passwd[i]
-        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
+        Invariant(ToSeq(result) == ToSeq(passwd).drop(i))
+        c = passwd[i - 1]
+        Assert(ToSeq(passwd).drop(i - 1) == PSeq(c) + ToSeq(passwd).drop(i))
+        result = [c] + result
+        i = i - 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -45,7 +44,6 @@
 def password_env_value(passwd: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(passwd), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(passwd), 1 / 2))
@@ -56,20 +54,5 @@
     Ensures((len(Result()) > 0) == (len(passwd) > 0))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    i = 0
-    while i < len(passwd):
-        # invariants-start
-        Invariant(Acc(list_pred(passwd), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(passwd))
-        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
-        Invariant(MustTerminate(len(passwd) - i + 1))
-        # invariants-end
-        c = passwd[i]
-        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
-    return result
+    return passwd
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -45,7 +44,6 @@
 def password_env_value(passwd: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(passwd), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(passwd), 1 / 2))
@@ -57,19 +55,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(passwd):
-        # invariants-start
-        Invariant(Acc(list_pred(passwd), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(passwd))
-        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
-        Invariant(MustTerminate(len(passwd) - i + 1))
-        # invariants-end
-        c = passwd[i]
-        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -45,7 +44,6 @@
 def password_env_value(passwd: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(passwd), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(passwd), 1 / 2))
@@ -59,17 +57,8 @@
     result = []  # type: List[int]
     i = 0
     while i < len(passwd):
-        # invariants-start
         Invariant(Acc(list_pred(passwd), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(passwd))
-        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
-        Invariant(MustTerminate(len(passwd) - i + 1))
-        # invariants-end
-        c = passwd[i]
-        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
-        result = result + [c]
-        i = i + 1
-    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-10973.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  The database shell launcher makes the connection password available to the
  child process through a dedicated mechanism. The value exposed to the child
  for the password is the password sequence itself — element i of the exposed
  value is code point i of the input password, for every position — so the
  exposed value equals the input password and has the same length.

  The mechanism is populated (the exposed value is non-empty) exactly when the
  input password is non-empty.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
returned `List[int]` is the value exposed to the child for the password; it is
populated (the mechanism is active) exactly when its length is positive, which
holds exactly when the input password is non-empty.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the changed behaviour is modelled deeply — the exposed
# value is pinned to the input password element-wise. The proof consumes no
# @ContractOnly contract.)
# axioms-end


# pure-start
# pure-end


# impl-start
# (Proof/impl-only region, elided from the consumer-visible spec view. The
# post-patch model below needs no reference helpers: the exposed value is the
# input password element for element, spelled out directly in the loop.)
# impl-end


def password_env_value(passwd: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(passwd), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(passwd), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The exposed value equals the password element for element.
    Ensures(ToSeq(Result()) == ToSeq(passwd))
    # The mechanism is populated exactly when the password is non-empty.
    Ensures((len(Result()) > 0) == (len(passwd) > 0))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(passwd):
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
        # invariants-end
        c = passwd[i]
        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. env python; verifier scripts/nagini_verify.sh. Spec fully pins the output element-for-element via Ensures(ToSeq(Result())==ToSeq(passwd)) plus the redundant populated-iff clause; axioms==[], one A-reference (pgpass_quote_seq==_escape_pgpass, lives only in model_prepatch.py). All 8 attacks share byte-identical spec (adversary same-spec exit 0).

### WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini django__django-10973 <atk>):
- atk_1.py (prepatch bug: inline colon->'\:' quoting): NOT-A-COUNTEREXAMPLE, fails verify (Postcondition ToSeq(Result())==ToSeq(passwd) might not hold). This reproduces the prepatch quoting behaviour (prepatch_reproduced=true; model_prepatch.py's pgpass_quote_seq form).
- atk_2.py (partial-domain, drops last element, loop i+1<len): NOT-A-COUNTEREXAMPLE, fails verify (postcondition).
- atk_3.py (boundary: duplicates first element): NOT-A-COUNTEREXAMPLE, fails verify (postcondition).
- atk_4.py (control-flow-effect: while True, unreachable return): NOT-A-COUNTEREXAMPLE, Translation failed 'Type error: dead.code' — Nagini rejects the unreachable return; vacuous non-termination blocked.
- atk_5.py (correct verbatim copy built BACKWARD, [c]+result with Invariant ToSeq(result)==ToSeq(passwd).drop(i)): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 12.5s). Behaviourally identical to gold (verbatim copy, present-iff-nonempty); its faithful refined patch IS the gold patch. run_resolve('django__django-10973', gold_patch, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved'. So this echo does NOT break the spec (verify AND resolve) — expected per the resolving-echo policy.
- atk_6.py (ungrounded-oracle echo: return passwd directly, only 1/2 perm held): NOT-A-COUNTEREXAMPLE, fails verify (cannot Ensure full Acc(list_pred(Result())) on the aliased input).
- atk_7.py (control-flow: always return []): NOT-A-COUNTEREXAMPLE, fails verify (postcondition).
- atk_8.py (conditional infinite loop for non-empty passwd, no progress): NOT-A-COUNTEREXAMPLE, fails verify (postcondition at loop-exit).

Direct-verify diagnostics confirm atk_2/3/7/8 fail on exactly 'Postcondition ... Assertion (ToSeq(Result()) == ToSeq(passwd)) might not hold' (genuine spec rejection, ~11-13s, not infra timeout); atk_4 fails on dead.code.

A-LEG AUDIT: axiom_check.py (G-AX) exit 0 — pgpass_quote_seq A-reference == real _escape_pgpass on 15 boundary + 20000 fuzz, verbatim exposure holds, colon/backslash divergence witnesses present. meta axioms==[] (no A-consumed leg). refinement.md legs A1(R),A2(R+I),A3(I),A4(R) all R/I; the sole deep model is A-reference (pgpass_quote_seq), defined only in model_prepatch.py's elided impl region, absent from model.py spec view. No kind-3. Correspondence to real callees (runshell_db password exposure / _escape_pgpass) holds.

Positive control (exact model.py) verifies: 'Verification successful' (11.6s).

CONCLUSION: The postcondition is a total, output-pinning equality; the only same-spec verifying impl found is an order-permuted but behaviourally-identical copy whose faithful patch resolves. verify => correct holds for the attack surface exercised. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_4.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-10973.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  The database shell launcher makes the connection password available to the
  child process through a dedicated mechanism. The value exposed to the child
  for the password is the password sequence itself — element i of the exposed
  value is code point i of the input password, for every position — so the
  exposed value equals the input password and has the same length.

  The mechanism is populated (the exposed value is non-empty) exactly when the
  input password is non-empty.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
returned `List[int]` is the value exposed to the child for the password; it is
populated (the mechanism is active) exactly when its length is positive, which
holds exactly when the input password is non-empty.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the changed behaviour is modelled deeply — the exposed
# value is pinned to the input password element-wise. The proof consumes no
# @ContractOnly contract.)
# axioms-end


# pure-start
# pure-end


# impl-start
# (Proof/impl-only region, elided from the consumer-visible spec view. The
# post-patch model below needs no reference helpers: the exposed value is the
# input password element for element, spelled out directly in the loop.)
# impl-end


def password_env_value(passwd: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(passwd), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(passwd), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The exposed value equals the password element for element.
    Ensures(ToSeq(Result()) == ToSeq(passwd))
    # The mechanism is populated exactly when the password is non-empty.
    Ensures((len(Result()) > 0) == (len(passwd) > 0))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(passwd):
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
        # invariants-end
        c = passwd[i]
        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. env python; verifier scripts/nagini_verify.sh. Spec fully pins the output element-for-element via Ensures(ToSeq(Result())==ToSeq(passwd)) plus the redundant populated-iff clause; axioms==[], one A-reference (pgpass_quote_seq==_escape_pgpass, lives only in model_prepatch.py). All 8 attacks share byte-identical spec (adversary same-spec exit 0).

### WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini django__django-10973 <atk>):
- atk_1.py (prepatch bug: inline colon->'\:' quoting): NOT-A-COUNTEREXAMPLE, fails verify (Postcondition ToSeq(Result())==ToSeq(passwd) might not hold). This reproduces the prepatch quoting behaviour (prepatch_reproduced=true; model_prepatch.py's pgpass_quote_seq form).
- atk_2.py (partial-domain, drops last element, loop i+1<len): NOT-A-COUNTEREXAMPLE, fails verify (postcondition).
- atk_3.py (boundary: duplicates first element): NOT-A-COUNTEREXAMPLE, fails verify (postcondition).
- atk_4.py (control-flow-effect: while True, unreachable return): NOT-A-COUNTEREXAMPLE, Translation failed 'Type error: dead.code' — Nagini rejects the unreachable return; vacuous non-termination blocked.
- atk_5.py (correct verbatim copy built BACKWARD, [c]+result with Invariant ToSeq(result)==ToSeq(passwd).drop(i)): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 12.5s). Behaviourally identical to gold (verbatim copy, present-iff-nonempty); its faithful refined patch IS the gold patch. run_resolve('django__django-10973', gold_patch, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved'. So this echo does NOT break the spec (verify AND resolve) — expected per the resolving-echo policy.
- atk_6.py (ungrounded-oracle echo: return passwd directly, only 1/2 perm held): NOT-A-COUNTEREXAMPLE, fails verify (cannot Ensure full Acc(list_pred(Result())) on the aliased input).
- atk_7.py (control-flow: always return []): NOT-A-COUNTEREXAMPLE, fails verify (postcondition).
- atk_8.py (conditional infinite loop for non-empty passwd, no progress): NOT-A-COUNTEREXAMPLE, fails verify (postcondition at loop-exit).

Direct-verify diagnostics confirm atk_2/3/7/8 fail on exactly 'Postcondition ... Assertion (ToSeq(Result()) == ToSeq(passwd)) might not hold' (genuine spec rejection, ~11-13s, not infra timeout); atk_4 fails on dead.code.

A-LEG AUDIT: axiom_check.py (G-AX) exit 0 — pgpass_quote_seq A-reference == real _escape_pgpass on 15 boundary + 20000 fuzz, verbatim exposure holds, colon/backslash divergence witnesses present. meta axioms==[] (no A-consumed leg). refinement.md legs A1(R),A2(R+I),A3(I),A4(R) all R/I; the sole deep model is A-reference (pgpass_quote_seq), defined only in model_prepatch.py's elided impl region, absent from model.py spec view. No kind-3. Correspondence to real callees (runshell_db password exposure / _escape_pgpass) holds.

Positive control (exact model.py) verifies: 'Verification successful' (11.6s).

CONCLUSION: The postcondition is a total, output-pinning equality; the only same-spec verifying impl found is an order-permuted but behaviourally-identical copy whose faithful patch resolves. verify => correct holds for the attack surface exercised. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical with the bundle (same-spec exit 0). The modeled function password_env_value(passwd: List[int]) carries two postconditions: (1) ToSeq(Result()) == ToSeq(passwd) — exposed value equals the password verbatim, code point for code point; (2) (len(Result()) > 0) == (len(passwd) > 0) — populated iff the password is non-empty.

Real post-patch callee (gold patch verbatim, django/db/backends/postgresql/client.py DatabaseClient.runshell_db): subprocess_env = os.environ.copy(); if passwd: subprocess_env['PGPASSWORD'] = str(passwd); subprocess.run(args, check=True, env=subprocess_env). Under the mapping.md str<->List[int] code-point carrier: (a) str(passwd) on a str is the identity, so the value the child sees for PGPASSWORD equals the password verbatim, matching postcondition (1); (b) `if passwd:` for a str is truthy <=> non-empty <=> len>0, and PGPASSWORD is set iff so — an absent entry bridges to the empty list, matching postcondition (2). The gold patch DELETES _escape_pgpass, so the post-patch value has no colon/backslash quoting; the legacy quoting (`:`->`\:`, `\`->`\\`) is correctly confined to model_prepatch.py (the differential twin), not this spec — so the spec is not too strong on colon/backslash inputs.

Machine evidence: G-CONF conformance_check.py ran the contract-stripped shadow impl against the REAL patched runshell_db (subprocess.run recorded) over 100,020 inputs (20 boundary incl. ':', '\', doubled/mixed, accented, beyond-BMP, pgpass-line-shaped, long, plus 100k seeded fuzz drawing heavily on ':' and '\') with 0 disagreements. I found no input within the stated abstraction where the modeled function disagrees with the real callee. Spec sits at the correct modeling boundary; not too strong, no drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (rendered via markers.spec_view with the nagini backend) exposes only: (1) an abstract module docstring describing the desired behaviour — the value exposed to the child for the password equals the input password element-for-element and is populated exactly when the input password is non-empty; (2) the List[int]/PSeq[int] type-carrier note; (3) the `password_env_value` signature with postconditions `ToSeq(Result()) == ToSeq(passwd)` and `(len(Result())>0)==(len(passwd)>0)`. Both impl regions are elided ('implementation elided — supplied by the consumer'); the axioms and pure regions are empty.

The public problem_statement already discloses the gold mechanism verbatim: 'Use subprocess.run and PGPASSWORD for client in postgres backend … pass a custom environment for the subprocess … set PGPASSWORD.' The spec's core postcondition (password exposed verbatim, present iff non-empty) is the natural, abstract specification of that publicly-stated desired behaviour and is derivable from the problem statement alone.

Crucially, the spec view does NOT narrate the discriminator/removed mechanism: no mention of `_escape_pgpass`, `.pgpass`, `NamedTemporaryFile`, PGPASSFILE, colon/backslash escaping, or code points 58/92. That removed-quoting content lives only in model_prepatch.py's module-level impl region (elided from the spec view) and in refinement.md/mapping.md (not part of the consumer spec view). Keyword scan of the spec view for escape/pgpass/quote/colon/backslash/58/92/subprocess/os.environ/legacy/removed found none.

Machine checks: markers.same_spec(model, prepatch)=True (spec byte-identical to the failing prepatch, so the spec itself carries no impl-distinguishing content); leakage.screen(model, nagini, gold_patch) => LeakageReport(hard_failures=[], warnings=[]). The spec does not reconstruct the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
