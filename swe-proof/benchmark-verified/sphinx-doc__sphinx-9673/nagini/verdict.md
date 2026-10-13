# P2 adversarial audit — sphinx-doc__sphinx-9673

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_17.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,7 @@
         c = field_kinds[i - 1]
         Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
         Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
-        if c == 2 or c == 3:
+        if c == 2:
             # a field classified as describing the return value
             described = True
         elif c == 4:
@@ -135,7 +135,7 @@
     Ensures(Result() == (name == return_key_a or name == return_key_b))
     # post-conditions-end
     # impl-start
-    if name == return_key_a or name == return_key_b:
+    if name == return_key_a:
         return True
     return False
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,6 +93,7 @@
     # impl-start
     described = False
     typed = False
+    plural = False
     i = len(field_kinds)
     while i > 0:
         # invariants-start
@@ -106,14 +107,16 @@
         Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
         Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
         if c == 2 or c == 3:
-            # a field classified as describing the return value
             described = True
         elif c == 4:
-            # a field classified as declaring the return type
             typed = True
+        if c == 3:
+            plural = True
         i = i - 1
     if return_annotated:
         if described and not typed:
+            if plural:
+                return augment_return_typefield(field_kinds, return_annotated)
             return True
     return False
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,6 +93,7 @@
     # impl-start
     described = False
     typed = False
+    plural = False
     i = len(field_kinds)
     while i > 0:
         # invariants-start
@@ -106,14 +107,20 @@
         Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
         Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
         if c == 2 or c == 3:
-            # a field classified as describing the return value
             described = True
         elif c == 4:
-            # a field classified as declaring the return type
             typed = True
+        if c == 3:
+            plural = True
         i = i - 1
     if return_annotated:
         if described and not typed:
+            if plural:
+                j = 1
+                while j > 0:
+                    Invariant(Acc(list_pred(field_kinds), 1 / 2))
+                    Invariant(j > 0)
+                    j = j + 1
             return True
     return False
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,6 +91,12 @@
                          not has_return_type(ToSeq(field_kinds))))
     # post-conditions-end
     # impl-start
+    if len(field_kinds) == 0:
+        return False
+    if len(field_kinds) == 1:
+        if return_annotated and field_kinds[0] == 2:
+            return True
+        return False
     described = False
     typed = False
     i = len(field_kinds)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,10 +94,10 @@
     described = False
     typed = False
     i = len(field_kinds)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(field_kinds), 1 / 2))
-        Invariant(0 <= i and i <= len(field_kinds))
+        Invariant(1 <= i and i <= len(field_kinds))
         Invariant(described == has_return_description(ToSeq(field_kinds).drop(i)))
         Invariant(typed == has_return_type(ToSeq(field_kinds).drop(i)))
         Invariant(MustTerminate(i + 1))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -113,7 +113,7 @@
             typed = True
         i = i - 1
     if return_annotated:
-        if described and not typed:
+        if described:
             return True
     return False
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,7 +135,7 @@
     Ensures(Result() == (name == return_key_a or name == return_key_b))
     # post-conditions-end
     # impl-start
-    if name == return_key_a or name == return_key_b:
+    if name == return_key_b:
         return True
     return False
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,7 +135,9 @@
     Ensures(Result() == (name == return_key_a or name == return_key_b))
     # post-conditions-end
     # impl-start
-    if name == return_key_a or name == return_key_b:
+    if name == return_key_a:
         return True
+    if name == return_key_b:
+        return name_is_return_key(name, return_key_a, return_key_b)
     return False
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,7 @@
         c = field_kinds[i - 1]
         Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
         Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
-        if c == 2 or c == 3:
+        if c == 3:
             # a field classified as describing the return value
             described = True
         elif c == 4:
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,7 +135,13 @@
     Ensures(Result() == (name == return_key_a or name == return_key_b))
     # post-conditions-end
     # impl-start
-    if name == return_key_a or name == return_key_b:
+    if name == return_key_a:
+        return True
+    if name == return_key_b:
+        fresh = []  # type: List[int]
+        fresh.append(3)
+        if augment_return_typefield(fresh, True):
+            return name_is_return_key(name, return_key_b, return_key_a)
         return True
     return False
     # impl-end
```

Attack 11 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,11 @@
         Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
         Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
         if c == 2 or c == 3:
-            # a field classified as describing the return value
             described = True
         elif c == 4:
-            # a field classified as declaring the return type
             typed = True
+        if c == 3:
+            field_kinds[i - 1] = 0
         i = i - 1
     if return_annotated:
         if described and not typed:
```

Attack 12 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,6 +93,7 @@
     # impl-start
     described = False
     typed = False
+    plural = False
     i = len(field_kinds)
     while i > 0:
         # invariants-start
@@ -106,14 +107,21 @@
         Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
         Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
         if c == 2 or c == 3:
-            # a field classified as describing the return value
             described = True
         elif c == 4:
-            # a field classified as declaring the return type
             typed = True
+        if c == 3:
+            plural = True
         i = i - 1
     if return_annotated:
         if described and not typed:
+            if plural:
+                j = 1
+                while j > 0:
+                    Invariant(Acc(list_pred(field_kinds), 1 / 2))
+                    Invariant(j > 0)
+                    Invariant(MustTerminate(j + 1))
+                    j = j + 1
             return True
     return False
     # impl-end
```

Attack 13 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,30 +91,6 @@
                          not has_return_type(ToSeq(field_kinds))))
     # post-conditions-end
     # impl-start
-    described = False
-    typed = False
-    i = len(field_kinds)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(field_kinds), 1 / 2))
-        Invariant(0 <= i and i <= len(field_kinds))
-        Invariant(described == has_return_description(ToSeq(field_kinds).drop(i)))
-        Invariant(typed == has_return_type(ToSeq(field_kinds).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = field_kinds[i - 1]
-        Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
-        Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
-        if c == 2 or c == 3:
-            # a field classified as describing the return value
-            described = True
-        elif c == 4:
-            # a field classified as declaring the return type
-            typed = True
-        i = i - 1
-    if return_annotated:
-        if described and not typed:
-            return True
     return False
     # impl-end
 
@@ -135,7 +111,5 @@
     Ensures(Result() == (name == return_key_a or name == return_key_b))
     # post-conditions-end
     # impl-start
-    if name == return_key_a or name == return_key_b:
-        return True
     return False
     # impl-end
```

Attack 14 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -92,30 +92,37 @@
     # post-conditions-end
     # impl-start
     described = False
-    typed = False
     i = len(field_kinds)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(field_kinds), 1 / 2))
         Invariant(0 <= i and i <= len(field_kinds))
         Invariant(described == has_return_description(ToSeq(field_kinds).drop(i)))
-        Invariant(typed == has_return_type(ToSeq(field_kinds).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field_kinds[i - 1]
         Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
         Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
         if c == 2 or c == 3:
-            # a field classified as describing the return value
             described = True
-        elif c == 4:
-            # a field classified as declaring the return type
+        i = i - 1
+    typed = False
+    k = len(field_kinds)
+    while k > 0:
+        # invariants-start
+        Invariant(Acc(list_pred(field_kinds), 1 / 2))
+        Invariant(0 <= k and k <= len(field_kinds))
+        Invariant(typed == has_return_type(ToSeq(field_kinds).drop(k)))
+        Invariant(described == has_return_description(ToSeq(field_kinds)))
+        Invariant(MustTerminate(k + 1))
+        # invariants-end
+        d = field_kinds[k - 1]
+        Assert(ToSeq(field_kinds).drop(k - 1)[0] == d)
+        Assert(ToSeq(field_kinds).drop(k - 1).drop(1) == ToSeq(field_kinds).drop(k))
+        if d == 4:
             typed = True
-        i = i - 1
-    if return_annotated:
-        if described and not typed:
-            return True
-    return False
+        k = k - 1
+    return return_annotated and described and not typed
     # impl-end
 
 
@@ -135,7 +142,5 @@
     Ensures(Result() == (name == return_key_a or name == return_key_b))
     # post-conditions-end
     # impl-start
-    if name == return_key_a or name == return_key_b:
-        return True
-    return False
+    return name == return_key_a or name == return_key_b
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9673.

Behaviour under specification (stated as desired behaviour, not as an edit):

When type-hint information is folded into an already-rendered description, the
routine decides whether to emit a return-type entry. Whether the return value
carries a textual description is read off the description fields already
present, via the classification of clause (1): a return value that the
description documents is one whose type must end up shown.

  (1) Given the collection of existing description fields, the return value is
      considered to HAVE a textual description exactly when at least one field
      is classified as describing the return value. It is considered to ALREADY
      HAVE a declared type exactly when at least one field is classified as
      declaring the return type.

  (2) A fresh return-type entry is emitted exactly when all three hold: the
      object carries a return annotation, the return value has a textual
      description (clause 1), and it does not already have a declared type.

Independently, when iterating the annotated names to back-fill parameter types,
a name that stands for the return value is skipped: it is not a parameter, and
the return value is handled by clause (2).

Type abstraction: each existing field is reduced to an integer "kind" code
determined by its leading token, and the description fields are carried by a
read-only `List[int]` of these codes. Codes 2 and 3 are the kinds classified as
describing the return value; code 4 is the kind classified as declaring the
return type; any other code is a field that does not bear on the return
decision. `return_annotated` carries whether a return annotation exists. The
name carriers `return_key_a` / `return_key_b` are the identifiers that stand for
the return value. The two classification predicates are front-recursive pure
sequence folds.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. The field classification and the return decision are pure
# structural logic, modelled deeply (`has_return_description` /
# `has_return_type`). The leading-token split of each field name is upstream of
# the modelled decision and is not consumed here.
# axioms-end

# pure-start
@Pure
def has_return_description(kinds: PSeq[int]) -> bool:
    """True iff the field collection contains a field classified as describing
    the return value -- code 2 or code 3. Front-recursive so a single unfold is
    available per loop step; uniformly false on the empty collection."""
    if len(kinds) == 0:
        return False
    return kinds[0] == 2 or kinds[0] == 3 or has_return_description(kinds.drop(1))

@Pure
def has_return_type(kinds: PSeq[int]) -> bool:
    """True iff the field collection contains a field classified as declaring
    the return type (code 4). Front-recursive; uniformly false on the empty
    collection."""
    if len(kinds) == 0:
        return False
    return kinds[0] == 4 or has_return_type(kinds.drop(1))
# pure-end

def augment_return_typefield(field_kinds: List[int], return_annotated: bool) -> bool:
    # pre-conditions-start
    # The existing description fields are read-only: fractional permission,
    # required AND ensured.
    Requires(Acc(list_pred(field_kinds), 1 / 2))
    # The emission decision below is claimed of EVERY run, not only of the runs
    # that reach a return: for any collection of existing description fields the
    # routine must reach the decision in finitely many steps. Level 2 leaves
    # room strictly below it for the obligations of whatever a body calls.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field_kinds), 1 / 2))
    # A fresh return-type entry is emitted exactly when: a return annotation
    # exists, the return value has a textual description, and it does not
    # already carry a declared type. Every field code classified as describing
    # the return value contributes to the description alike.
    Ensures(Result() == (return_annotated and
                         has_return_description(ToSeq(field_kinds)) and
                         not has_return_type(ToSeq(field_kinds))))
    # post-conditions-end
    # impl-start
    described = False
    typed = False
    i = len(field_kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(field_kinds), 1 / 2))
        Invariant(0 <= i and i <= len(field_kinds))
        Invariant(described == has_return_description(ToSeq(field_kinds).drop(i)))
        Invariant(typed == has_return_type(ToSeq(field_kinds).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = field_kinds[i - 1]
        Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
        Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
        if c == 2 or c == 3:
            # a field classified as describing the return value
            described = True
        elif c == 4:
            # a field classified as declaring the return type
            typed = True
        i = i - 1
    if return_annotated:
        if described and not typed:
            return True
    return False
    # impl-end

def name_is_return_key(name: int, return_key_a: int, return_key_b: int) -> bool:
    # pre-conditions-start
    # `return_key_a`/`return_key_b` are the identifiers that stand for the
    # return value; all three carriers are scalars (no permission).
    # The answer below is likewise claimed of EVERY run: the routine must decide
    # in finitely many steps whether the name it was handed stands for the
    # return value. A level above the emission decision, so a body here may
    # consult that decision and still sit strictly above its obligation.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # A name that stands for the return value is the one name skipped when
    # back-filling parameter types.
    Ensures(Result() == (name == return_key_a or name == return_key_b))
    # post-conditions-end
    # impl-start
    if name == return_key_a or name == return_key_b:
        return True
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ RE-AUDIT of a REPAIRED spec. Context the runner should not miss: the recorded G-EQ/G-PANEL-1 verdict in meta.json is BROKEN (checked_at 20:51), keyed on the prior pass's atk_7 -- a guarded non-terminating SELF-DELEGATION that verified under a spec with NO termination obligation. model.py was subsequently rewritten (21:40) to add `Requires(MustTerminate(2))` / `Requires(MustTerminate(6))` and `Invariant(MustTerminate(i + 1))`. I re-encoded that exact counterexample and it is now REJECTED, so the repair holds and the stale BROKEN record is superseded.

14 same-spec attacks submitted, all confirmed byte-identical spec view via `adversary same-spec` AND diffed to prove non-impl regions are untouched. Verdict SOUND: 12 rejected for the INTENDED reason, 2 candidates verified and BOTH of their faithful patches RESOLVED (correct echoes, not weaknesses).

Command form (per attack): `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9673 atk_N.py`; failure reasons read back with `bash scripts/nagini_verify.sh <file>`. Attacks were verified in concurrent batches of 3.

### PER-ATTACK RESULTS (exit code, then the verifier's OWN error line -- I checked every rejection is semantic, not incidental):
* atk_1  PREPATCH BUG re-encoded, BOTH hunks (loop sets described only on c==2; skip guard only return_key_a) -> exit 2. 'Loop invariant might not be preserved. described == has_return_description(...drop(i))' + 'Postcondition of name_is_return_key might not hold'. => prepatch_reproduced.
* atk_2  THE PRIOR COUNTEREXAMPLE (gold loop + guarded non-terminating self-delegation under the plural guard) -> exit 2. 'Obligation leak check failed. Callee augment_return_typefield might not take all unsatisfied obligations from the caller.' REGRESSION CONFIRMED FIXED.
* atk_3  control-flow-effect: inner loop that never exits, NO obligation on it -> exit 2. 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.'
* atk_4  partial-domain: len==1 fast path (the F2P shape) recognising only the SHORT spelling -> exit 2. 'Postcondition of augment_return_typefield might not hold.'
* atk_5  boundary/off-by-one: `while i > 1` (index 0 never classified), invariant weakened to 1<=i -> exit 2. 'Loop invariant might not hold on entry. 1 <= i might not hold.'
* atk_6  ungrounded-oracle echo: drops the third conjunct (`if described:` without `and not typed`) -> exit 2. 'Postcondition of augment_return_typefield might not hold.'
* atk_7  hunk-2 wrong: only the PLURAL return name skipped -> exit 2. 'Postcondition of name_is_return_key might not hold.'
* atk_8  hunk-2 analogue of the prior break: guarded self-delegation inside name_is_return_key (level 6) -> exit 2. 'Obligation leak check failed. Callee name_is_return_key...'. The leg a hunk-1-only repair would have missed IS covered.
* atk_9  mirror error: plural-only recognition (c==3 sets described, c==2 does not) -> exit 2. 'Loop invariant might not be preserved.'
* atk_10 probes the LEVEL GAP (name_is_return_key at 6 may call downward to 2): builds a fresh list, delegates, re-delegates -> exit 2. 'Obligation leak check failed.' The gap opens no unbounded chain.
* atk_12 HEAP-EFFECT, probing leg A1's read-only claim directly (mutates field_kinds[i-1]=0) -> exit 2. 'The precondition of field_kinds[(i - 1)] = 0 might not hold. There might be insufficient permission.' The 1/2 fractional permission genuinely enforces read-only.
* atk_13 SHARPEST probe of the repair: inner non-terminating loop that DOES carry `Invariant(MustTerminate(j + 1))` with a measure that does not decrease (j grows) -> exit 2. 'Obligation leak check failed. Loop might not keep promise to terminate.' The obligation is checked for a genuine DECREASE, not merely for being present -- this is the memory-note failure mode (loop invariants alone do not reject a diverging rival) and it is closed at the method level.
* atk_14 VACUITY/non-vacuity control: both legs constant `return False` -> exit 2, BOTH postconditions cited. The two @Pure folds are not degenerate; the spec is not vacuously satisfiable.
* atk_17 CANDIDATE (exit 0, verifies): correct RESHAPE -- two separate backward loops (one per predicate) instead of one fused loop, emission collapsed to a single boolean expression, both legs expression-bodied. Materialized faithful patch patch_atk17.diff (built from the REAL base-commit file via `git show 5fb51fb1...:sphinx/ext/autodoc/typehints.py`), containing BOTH gold hunks verbatim plus the two-pass reshape. EXECUTED run_resolve (run_id geq-audit-atk17): resolved=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS 1/1 pass, PASS_TO_PASS 24/24 pass. => CORRECT ECHO, not a weakness. Hunk-2 anchor care: `if name == 'return':` occurs TWICE in the file (merge_typehints ~line 108 and the back-fill loop line 159); my patch edits only the back-fill loop, anchored on the preceding `for name in annotations:`, as the gold patch does. Cross-checked offline first: 10922 cases (every field-multiset of length <=6 over the 4 code classes x both annotation settings), 0 divergences from gold.
* POSITIVE CONTROL pos_control.py = frozen model.py byte-identical (cmp confirms) -> `weakness` exit 0 CANDIDATE, verifies in 13.6s as required. Its faithful patch IS the gold patch; run separately through run_resolve (run_id geq-audit-posctrl) as an independent oracle control: resolved=True, FAIL_TO_PASS 1/1, PASS_TO_PASS 24/24. This also establishes the oracle CAN certify on this instance, so the resolve outcomes above are meaningful evidence.

### NOT SUBMITTED AS EVIDENCE (reported for honesty, per my note that a retained attack label must carry the real oracle verdict):
* atk_11.py (exception route: `raise ValueError()` under the plural guard, no Exsures clause) -- Nagini output was 'Translation failed / Not supported: Unsupported builtin function' at the raise site. check_attack labels this verifies=False verify_completed=True, i.e. it would COUNT as a rejection, but the verifier never reached a semantic verdict, so scoring it in the reject lane would credit the spec with a rejection it never made. EXCLUDED from my attack list. The exception-effect route is therefore UNPROBED by me on this bundle -- a residual gap I am flagging rather than papering over, though note the model's `bool` return type and the absence of any Exsures means an exception-raising refinement is not expressible in this modeling anyway.
* atk_15.py / atk_16.py -- intended as correct reshapes; both failed, but on MY OWN proof-annotation gap, not spec over-tightness: atk_15 used a forward loop with `take(i)` against front-recursive folds (needs a back-extension lemma), atk_16 lost the `described` fact across its second loop. I did not stop at 'the spec rejected a correct impl' -- I fixed the framing in atk_17 (same two-loop shape + `Invariant(described == has_return_description(ToSeq(field_kinds)))` carried through loop 2) and it VERIFIES. This is the important over-tightness control: the spec is pinned to the DECISION, not to the gold's traversal or branch shape, so the 12 rejections above are informative rather than artifacts of a spec that only accepts one syntactic shape.

A-LEG / MODEL-CORRESPONDENCE AUDIT (my assigned focus):
* Legs: refinement.md has NO A-consumed and NO A-reference legs, and this is CORRECT, not an evasion. Independently confirmed: `grep -c ContractOnly model.py` = 0; meta.json `axioms` = [] and `deep_model_references` = []. Every leg (A1-A5, B1-B2) is R or I; there is no kind-3 (unexpressible-changed-op) step. The changed operation really is pure integer/sequence classification, so there is no library callee to ground and no G-AX trust point to abuse.
* Line-number claims spot-checked against the real base-commit file and ALL hold exactly: typehints.py:130 `def augment_descriptions_with_types(`, :152 `elif parts[0] == 'return':` (hunk 1), :155 `has_type.add('return')`, :158-160 the back-fill `for name in annotations:` / `if name == 'return':` / `continue` (hunk 2), :168 `if 'return' in annotations:`, :173 `node += field`. patch.diff is the gold patch verbatim and its two hunks match mapping.md's quoted hunks.
* axiom_check.py re-run: exit 0, 'model decision functions == patched augment_descriptions_with_types return logic over 51555 field-lists (exhaustive len<=4 + 50000 fuzz) + name_is_return_key + the plural return-description discriminator.' As mapping.md §3 states, it is a structural cross-check with no in-container callee execution -- appropriate for a zero-axiom bundle, and it does assert the F2P discriminator (plural-only field + annotation + no rtype => emit under patched, NOT under prepatch).
* A5/mapping §2 row 3 correspondence ('model bool Result <-> the appended rtype node') is the leg the PRIOR break exploited: it presumes the function RETURNS. That presumption is now DISCHARGED by the frozen contract rather than assumed, which is exactly what atk_2/atk_3/atk_8/atk_10/atk_13 test from five different directions.

### DOCUMENTATION DEFECT (advisory, NOT a soundness break -- flagged because it is the thing most likely to regress):
refinement.md and mapping.md are STALE with respect to the repair: `grep -n 'MustTerminate|terminat'` returns NOTHING in either file. The obligation that is now load-bearing for the whole verify=>resolve argument is undocumented. Concretely, refinement.md §D still reasons 'augment_return_typefield verifies only if its Result equals ...', and that inference is only valid BECAUSE MustTerminate is present -- under partial correctness 'verifies' does not entail 'has a Result at all', which is precisely how the prior atk_7 broke this bundle. §D should name the termination obligation as a premise, and §A/§B should carry a leg for it (I would tag it I: the real code's loops are plainly finite `for field in fields` / `for name in annotations`, so the obligation costs the gold refinement nothing -- confirmed by pos_control verifying with it).

Recommend also adding atk_2 (this file: the prior counterexample) as a permanent G-PBT reject case so a future edit that drops MustTerminate cannot silently re-open the hole; note that G-CONF/G-AX/G-MUT/G-PBT all diff a contract-STRIPPED transliteration and are therefore structurally blind to a missing termination obligation -- only a G-EQ attack against the frozen contract can see it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_17.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

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

Attack 11 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9673.

Behaviour under specification (stated as desired behaviour, not as an edit):

When type-hint information is folded into an already-rendered description, the
routine decides whether to emit a return-type entry. Whether the return value
carries a textual description is read off the description fields already
present, via the classification of clause (1): a return value that the
description documents is one whose type must end up shown.

  (1) Given the collection of existing description fields, the return value is
      considered to HAVE a textual description exactly when at least one field
      is classified as describing the return value. It is considered to ALREADY
      HAVE a declared type exactly when at least one field is classified as
      declaring the return type.

  (2) A fresh return-type entry is emitted exactly when all three hold: the
      object carries a return annotation, the return value has a textual
      description (clause 1), and it does not already have a declared type.

Independently, when iterating the annotated names to back-fill parameter types,
a name that stands for the return value is skipped: it is not a parameter, and
the return value is handled by clause (2).

Type abstraction: each existing field is reduced to an integer "kind" code
determined by its leading token, and the description fields are carried by a
read-only `List[int]` of these codes. Codes 2 and 3 are the kinds classified as
describing the return value; code 4 is the kind classified as declaring the
return type; any other code is a field that does not bear on the return
decision. `return_annotated` carries whether a return annotation exists. The
name carriers `return_key_a` / `return_key_b` are the identifiers that stand for
the return value. The two classification predicates are front-recursive pure
sequence folds.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. The field classification and the return decision are pure
# structural logic, modelled deeply (`has_return_description` /
# `has_return_type`). The leading-token split of each field name is upstream of
# the modelled decision and is not consumed here.
# axioms-end

# pure-start
@Pure
def has_return_description(kinds: PSeq[int]) -> bool:
    """True iff the field collection contains a field classified as describing
    the return value -- code 2 or code 3. Front-recursive so a single unfold is
    available per loop step; uniformly false on the empty collection."""
    if len(kinds) == 0:
        return False
    return kinds[0] == 2 or kinds[0] == 3 or has_return_description(kinds.drop(1))

@Pure
def has_return_type(kinds: PSeq[int]) -> bool:
    """True iff the field collection contains a field classified as declaring
    the return type (code 4). Front-recursive; uniformly false on the empty
    collection."""
    if len(kinds) == 0:
        return False
    return kinds[0] == 4 or has_return_type(kinds.drop(1))
# pure-end

def augment_return_typefield(field_kinds: List[int], return_annotated: bool) -> bool:
    # pre-conditions-start
    # The existing description fields are read-only: fractional permission,
    # required AND ensured.
    Requires(Acc(list_pred(field_kinds), 1 / 2))
    # The emission decision below is claimed of EVERY run, not only of the runs
    # that reach a return: for any collection of existing description fields the
    # routine must reach the decision in finitely many steps. Level 2 leaves
    # room strictly below it for the obligations of whatever a body calls.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field_kinds), 1 / 2))
    # A fresh return-type entry is emitted exactly when: a return annotation
    # exists, the return value has a textual description, and it does not
    # already carry a declared type. Every field code classified as describing
    # the return value contributes to the description alike.
    Ensures(Result() == (return_annotated and
                         has_return_description(ToSeq(field_kinds)) and
                         not has_return_type(ToSeq(field_kinds))))
    # post-conditions-end
    # impl-start
    described = False
    typed = False
    i = len(field_kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(field_kinds), 1 / 2))
        Invariant(0 <= i and i <= len(field_kinds))
        Invariant(described == has_return_description(ToSeq(field_kinds).drop(i)))
        Invariant(typed == has_return_type(ToSeq(field_kinds).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = field_kinds[i - 1]
        Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
        Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
        if c == 2 or c == 3:
            # a field classified as describing the return value
            described = True
        elif c == 4:
            # a field classified as declaring the return type
            typed = True
        i = i - 1
    if return_annotated:
        if described and not typed:
            return True
    return False
    # impl-end

def name_is_return_key(name: int, return_key_a: int, return_key_b: int) -> bool:
    # pre-conditions-start
    # `return_key_a`/`return_key_b` are the identifiers that stand for the
    # return value; all three carriers are scalars (no permission).
    # The answer below is likewise claimed of EVERY run: the routine must decide
    # in finitely many steps whether the name it was handed stands for the
    # return value. A level above the emission decision, so a body here may
    # consult that decision and still sit strictly above its obligation.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # A name that stands for the return value is the one name skipped when
    # back-filling parameter types.
    Ensures(Result() == (name == return_key_a or name == return_key_b))
    # post-conditions-end
    # impl-start
    if name == return_key_a or name == return_key_b:
        return True
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ RE-AUDIT of a REPAIRED spec. Context the runner should not miss: the recorded G-EQ/G-PANEL-1 verdict in meta.json is BROKEN (checked_at 20:51), keyed on the prior pass's atk_7 -- a guarded non-terminating SELF-DELEGATION that verified under a spec with NO termination obligation. model.py was subsequently rewritten (21:40) to add `Requires(MustTerminate(2))` / `Requires(MustTerminate(6))` and `Invariant(MustTerminate(i + 1))`. I re-encoded that exact counterexample and it is now REJECTED, so the repair holds and the stale BROKEN record is superseded.

14 same-spec attacks submitted, all confirmed byte-identical spec view via `adversary same-spec` AND diffed to prove non-impl regions are untouched. Verdict SOUND: 12 rejected for the INTENDED reason, 2 candidates verified and BOTH of their faithful patches RESOLVED (correct echoes, not weaknesses).

Command form (per attack): `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9673 atk_N.py`; failure reasons read back with `bash scripts/nagini_verify.sh <file>`. Attacks were verified in concurrent batches of 3.

### PER-ATTACK RESULTS (exit code, then the verifier's OWN error line -- I checked every rejection is semantic, not incidental):
* atk_1  PREPATCH BUG re-encoded, BOTH hunks (loop sets described only on c==2; skip guard only return_key_a) -> exit 2. 'Loop invariant might not be preserved. described == has_return_description(...drop(i))' + 'Postcondition of name_is_return_key might not hold'. => prepatch_reproduced.
* atk_2  THE PRIOR COUNTEREXAMPLE (gold loop + guarded non-terminating self-delegation under the plural guard) -> exit 2. 'Obligation leak check failed. Callee augment_return_typefield might not take all unsatisfied obligations from the caller.' REGRESSION CONFIRMED FIXED.
* atk_3  control-flow-effect: inner loop that never exits, NO obligation on it -> exit 2. 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.'
* atk_4  partial-domain: len==1 fast path (the F2P shape) recognising only the SHORT spelling -> exit 2. 'Postcondition of augment_return_typefield might not hold.'
* atk_5  boundary/off-by-one: `while i > 1` (index 0 never classified), invariant weakened to 1<=i -> exit 2. 'Loop invariant might not hold on entry. 1 <= i might not hold.'
* atk_6  ungrounded-oracle echo: drops the third conjunct (`if described:` without `and not typed`) -> exit 2. 'Postcondition of augment_return_typefield might not hold.'
* atk_7  hunk-2 wrong: only the PLURAL return name skipped -> exit 2. 'Postcondition of name_is_return_key might not hold.'
* atk_8  hunk-2 analogue of the prior break: guarded self-delegation inside name_is_return_key (level 6) -> exit 2. 'Obligation leak check failed. Callee name_is_return_key...'. The leg a hunk-1-only repair would have missed IS covered.
* atk_9  mirror error: plural-only recognition (c==3 sets described, c==2 does not) -> exit 2. 'Loop invariant might not be preserved.'
* atk_10 probes the LEVEL GAP (name_is_return_key at 6 may call downward to 2): builds a fresh list, delegates, re-delegates -> exit 2. 'Obligation leak check failed.' The gap opens no unbounded chain.
* atk_12 HEAP-EFFECT, probing leg A1's read-only claim directly (mutates field_kinds[i-1]=0) -> exit 2. 'The precondition of field_kinds[(i - 1)] = 0 might not hold. There might be insufficient permission.' The 1/2 fractional permission genuinely enforces read-only.
* atk_13 SHARPEST probe of the repair: inner non-terminating loop that DOES carry `Invariant(MustTerminate(j + 1))` with a measure that does not decrease (j grows) -> exit 2. 'Obligation leak check failed. Loop might not keep promise to terminate.' The obligation is checked for a genuine DECREASE, not merely for being present -- this is the memory-note failure mode (loop invariants alone do not reject a diverging rival) and it is closed at the method level.
* atk_14 VACUITY/non-vacuity control: both legs constant `return False` -> exit 2, BOTH postconditions cited. The two @Pure folds are not degenerate; the spec is not vacuously satisfiable.
* atk_17 CANDIDATE (exit 0, verifies): correct RESHAPE -- two separate backward loops (one per predicate) instead of one fused loop, emission collapsed to a single boolean expression, both legs expression-bodied. Materialized faithful patch patch_atk17.diff (built from the REAL base-commit file via `git show 5fb51fb1...:sphinx/ext/autodoc/typehints.py`), containing BOTH gold hunks verbatim plus the two-pass reshape. EXECUTED run_resolve (run_id geq-audit-atk17): resolved=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS 1/1 pass, PASS_TO_PASS 24/24 pass. => CORRECT ECHO, not a weakness. Hunk-2 anchor care: `if name == 'return':` occurs TWICE in the file (merge_typehints ~line 108 and the back-fill loop line 159); my patch edits only the back-fill loop, anchored on the preceding `for name in annotations:`, as the gold patch does. Cross-checked offline first: 10922 cases (every field-multiset of length <=6 over the 4 code classes x both annotation settings), 0 divergences from gold.
* POSITIVE CONTROL pos_control.py = frozen model.py byte-identical (cmp confirms) -> `weakness` exit 0 CANDIDATE, verifies in 13.6s as required. Its faithful patch IS the gold patch; run separately through run_resolve (run_id geq-audit-posctrl) as an independent oracle control: resolved=True, FAIL_TO_PASS 1/1, PASS_TO_PASS 24/24. This also establishes the oracle CAN certify on this instance, so the resolve outcomes above are meaningful evidence.

### NOT SUBMITTED AS EVIDENCE (reported for honesty, per my note that a retained attack label must carry the real oracle verdict):
* atk_11.py (exception route: `raise ValueError()` under the plural guard, no Exsures clause) -- Nagini output was 'Translation failed / Not supported: Unsupported builtin function' at the raise site. check_attack labels this verifies=False verify_completed=True, i.e. it would COUNT as a rejection, but the verifier never reached a semantic verdict, so scoring it in the reject lane would credit the spec with a rejection it never made. EXCLUDED from my attack list. The exception-effect route is therefore UNPROBED by me on this bundle -- a residual gap I am flagging rather than papering over, though note the model's `bool` return type and the absence of any Exsures means an exception-raising refinement is not expressible in this modeling anyway.
* atk_15.py / atk_16.py -- intended as correct reshapes; both failed, but on MY OWN proof-annotation gap, not spec over-tightness: atk_15 used a forward loop with `take(i)` against front-recursive folds (needs a back-extension lemma), atk_16 lost the `described` fact across its second loop. I did not stop at 'the spec rejected a correct impl' -- I fixed the framing in atk_17 (same two-loop shape + `Invariant(described == has_return_description(ToSeq(field_kinds)))` carried through loop 2) and it VERIFIES. This is the important over-tightness control: the spec is pinned to the DECISION, not to the gold's traversal or branch shape, so the 12 rejections above are informative rather than artifacts of a spec that only accepts one syntactic shape.

A-LEG / MODEL-CORRESPONDENCE AUDIT (my assigned focus):
* Legs: refinement.md has NO A-consumed and NO A-reference legs, and this is CORRECT, not an evasion. Independently confirmed: `grep -c ContractOnly model.py` = 0; meta.json `axioms` = [] and `deep_model_references` = []. Every leg (A1-A5, B1-B2) is R or I; there is no kind-3 (unexpressible-changed-op) step. The changed operation really is pure integer/sequence classification, so there is no library callee to ground and no G-AX trust point to abuse.
* Line-number claims spot-checked against the real base-commit file and ALL hold exactly: typehints.py:130 `def augment_descriptions_with_types(`, :152 `elif parts[0] == 'return':` (hunk 1), :155 `has_type.add('return')`, :158-160 the back-fill `for name in annotations:` / `if name == 'return':` / `continue` (hunk 2), :168 `if 'return' in annotations:`, :173 `node += field`. patch.diff is the gold patch verbatim and its two hunks match mapping.md's quoted hunks.
* axiom_check.py re-run: exit 0, 'model decision functions == patched augment_descriptions_with_types return logic over 51555 field-lists (exhaustive len<=4 + 50000 fuzz) + name_is_return_key + the plural return-description discriminator.' As mapping.md §3 states, it is a structural cross-check with no in-container callee execution -- appropriate for a zero-axiom bundle, and it does assert the F2P discriminator (plural-only field + annotation + no rtype => emit under patched, NOT under prepatch).
* A5/mapping §2 row 3 correspondence ('model bool Result <-> the appended rtype node') is the leg the PRIOR break exploited: it presumes the function RETURNS. That presumption is now DISCHARGED by the frozen contract rather than assumed, which is exactly what atk_2/atk_3/atk_8/atk_10/atk_13 test from five different directions.

### DOCUMENTATION DEFECT (advisory, NOT a soundness break -- flagged because it is the thing most likely to regress):
refinement.md and mapping.md are STALE with respect to the repair: `grep -n 'MustTerminate|terminat'` returns NOTHING in either file. The obligation that is now load-bearing for the whole verify=>resolve argument is undocumented. Concretely, refinement.md §D still reasons 'augment_return_typefield verifies only if its Result equals ...', and that inference is only valid BECAUSE MustTerminate is present -- under partial correctness 'verifies' does not entail 'has a Result at all', which is precisely how the prior atk_7 broke this bundle. §D should name the termination obligation as a premise, and §A/§B should carry a leg for it (I would tag it I: the real code's loops are plainly finite `for field in fields` / `for name in annotations`, so the obligation costs the gold refinement nothing -- confirmed by pos_control verifying with it).

Recommend also adding atk_2 (this file: the prior counterexample) as a permanent G-PBT reject case so a future edit that drops MustTerminate cannot silently re-open the hole; note that G-CONF/G-AX/G-MUT/G-PBT all diff a contract-STRIPPED transliteration and are therefore structurally blind to a missing termination obligation -- only a G-EQ attack against the frozen contract can see it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP. Bundle read-only; Built two git worktrees of the upstream repository at base_commit 5fb51fb1467dc5eea7505402c3c5d9b378d3b441: wt (base) and wtp (base + the gold patch applied by hand and diff-verified: 3 insertions/3 deletions in sphinx/ext/autodoc/typehints.py). Per the brief, wtp is the reference for the modelled function; base is the reference only for untouched callees (there are none consumed here — zero axioms).

**SPEC INTEGRITY.** model.py in /tmp is byte-identical to the bundle (md5 5a833a8c8c39fa45d6f1a66777f69402 both). scripts/nagini_verify.sh on that copy: exit 0, 'Verification successful' (12.4s). So the frozen spec + impl really do verify; the postcondition Result() == (return_annotated and has_return_description(ToSeq(field_kinds)) and not has_return_type(ToSeq(field_kinds))) is provable, and MustTerminate(2)/(6) make the decision total, not vacuous on a subset of runs.

MY OWN ORACLE (not the bundle's). I wrote three independent harnesses that CALL the real patched function on freshly built docutils field_lists and observe the appended fields (an appended field named exactly 'rtype' <=> Result True; the back-fill loop only ever appends 'type <name>', so the observable is exact):

  (1) diff.py — exhaustive over code words of length ≤4 over the 6-code alphabet {param,type,return,returns,rtype,other} x both return_annotated settings x 2 random realizations each, plus 4000 longer random lists (≤10 fields) with extra non-'return' annotation keys: 10,220 cases, 0 divergences. Both the spec folds AND the loop impl were checked against the oracle on every case (three-way spec==impl==real).

  (2) diff2.py — exhaustive over code words of length ≤5 x both settings with randomized realizations and randomized extra annotation keys (including a spurious 'returns' annotation key): 18,662 cases, 0 divergences.

  (3) diff3.py — the strongest one: EVERY realization enumerated rather than sampled (all 24 concrete field-name spellings x all positions, lists of length ≤3, both settings): 28,850 cases, 0 divergences. This rules out the failure mode where one spelling inside a declared code class behaves unlike its class.
Total 57,732 in-bridge cases, 0 divergences.

**TOO-STRONG PROBES SPECIFICALLY.** A too-strong spec would show up as the model claiming emission where the real function emits nothing, or claiming no-emission where it emits. I targeted exactly that:
  - Ordering/multiplicity: ['returns v','rtype int'] and ['rtype int','returns v'] both -> real appends nothing; spec False (has_return_type kills it regardless of order). Agrees.
  - Missing annotation: ['returns v'] with annotations {} -> real nothing, spec False. Agrees.
  - Empty field list with return annotation -> real nothing, spec False (has_return_description False on empty). Agrees.
  - Case/near-miss homographs that must NOT count as return descriptions: 'Return', 'RETURNS', 'return:', 'returns:', 'returned', 'rtypes', 'ret', 'return\nv', ' return v' (leading space => parts[0]==''), '  rtype' — real appends nothing for each; all are code 5 in the bridge, spec False. Agrees. Notably 'Returns' (the Google-header homograph) and 'return\nv' are correctly code-5, i.e. the spec is NOT over-claiming on them.
  - Whitespace-tolerant true positives: 'return  x', 'returns  n' (re.split(' +',...) collapses runs) -> real appends rtype; codes 2/3, spec True. Agrees, so the spec is not under-claiming either.
  - F2P shape reproduced directly: single field 'returns decremented number' + annotations {a,b,return} -> real (patched) appends 'rtype'. Spec True. This is the exact test_autodoc_typehints_description_no_undoc behaviour, and it is the delta the patch introduces — correctly attributed to wtp, not treated as drift.

HUNK 2 (name_is_return_key). Driven through the real function with the single field 'param <NAME>' and annotations {NAME:'int'}, so the skip guard is the only thing that can suppress the 'type <NAME>' field. Exhaustive over the reachable name pool {return, returns, x, rtype, Return, returned, self}: model (name==return_key_a or name==return_key_b) == real skipped, 7/7 agree. 'return' -> skipped (and rtype appended instead), 'returns' -> skipped, everything else -> 'type <name>' appended. Ensures is exactly right, neither strengthened nor weakened.

BUNDLE'S OWN GATE, RE-RUN BY ME against my hand-patched wtp (not the bundle's container): conformance_check.py prints G-CONF OK, checked 123733, disagreements 0, seed 9673, with branch_hits showing described_short 195948 / described_plural 206969 / typed 185082 / other 263650 / loop_zero 5334 / result_true 13854 / result_false 109857 — so no branch is dead and the pass is not vacuous. Its 3 out_of_bridge_probe_divergences match my own degenerate-probe findings exactly, which independently corroborates that the bundle disclosed the full extent of its lossiness rather than hiding a case.

**WHY THE DEGENERATE CASES ARE NOT DRIFT.** mapping.md §2 defines the residual class as 'any other token ... it does not bear on the return decision'. 'param return' has leading token 'param' but its derived name is 'return', so it DOES bear on the decision — hence it fails the class definition and is outside the modelled domain by construction, not by convenience. The bundle names all three shapes, runs them as a labelled non-gating probe, prints the divergences in the gated JSON output, and cites the prior G-PANEL-2 adjudication. Per my memory note 'Retained attack labels carry the oracle verdict', re-judging this already-adjudicated, fully-disclosed boundary as the reject lane would be inventing spec weakness. The abstraction is lossy at an unreachable point and says so; the modelled decision agrees with the real patched callee everywhere in its stated domain.

RESIDUAL RISK (recorded, not gating). The bridge's residual class is defined by a semantic property ('does not touch the return key') rather than syntactically, which is what makes the three degenerate names an exclusion rather than a modelled case. This narrows the domain but does not weaken or over-strengthen the spec on any input a real Python signature can produce.

Counterexample / evidence:

```
None. No input where the modelled function disagrees with the real patched callee inside the declared type bridge.
```

**SETUP.** Bundle read-only; Built two git worktrees of the upstream repository at base_commit 5fb51fb1467dc5eea7505402c3c5d9b378d3b441: wt (base) and wtp (base + the gold patch applied by hand and diff-verified: 3 insertions/3 deletions in sphinx/ext/autodoc/typehints.py). Per the brief, wtp is the reference for the modelled function; base is the reference only for untouched callees (there are none consumed here — zero axioms).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** MEASURED.

**SPEC VIEW RE-DERIVED:** markers.spec_view(model.py, nagini) -> module docstring + axioms + pure + pre/post regions; impl regions elided. same_spec(model.py, model_prepatch.py) = True (only the two impl lines differ: `c == 2 or c == 3` vs `c == 2`; `name == return_key_a or name == return_key_b` vs `name == return_key_a`).

MECHANICAL SCREEN (my run): leakage.screen(model.py, nagini, gold_patch, problem_statement) -> hard_failures=[], warnings=[]. Spec view quotes no diff line, names no patched path (sphinx/ext/autodoc/typehints.py) or symbol (augment_descriptions_with_types). Token sweep over the spec view: 'returns', 'plural', 'singular', 'spelling', 'synonym', 'rtype', 'parts[0]', 'napoleon', ':return', 'has_description', 'has_type', 'interchangeable', 'alias', 'variant' -- ALL ABSENT.

FACET RE-CONFIRMED = the singular/plural return-description synonym (gold: `parts[0] in ('return','returns')` and `name in ('return','returns')`).

UNAVOIDABILITY RE-DERIVED MYSELF via the strip test (the load-bearing control), not inherited:
  1. nagini_verify.sh model.py -> 'Verification successful', exit 0 (15.65s).
  2. nagini_verify.sh model_prepatch.py -> FAILS, exit 1, on exactly the two discriminating clauses: loop invariant `described == has_return_description(ToSeq(field_kinds).drop(i))` (hunk 1) and the postcondition of name_is_return_key (hunk 2).
  3. **STRIP TEST:** I removed the discriminator from the SPEC only -- `kinds[0] == 3` out of the @Pure has_return_description body, and `or name == return_key_b` out of the name_is_return_key postcondition -- and left the PRE-patch impl. Result: 'Verification successful', exit 0 (12.36s). The stripped clauses are therefore LOAD-BEARING: without them the pre-patch impl satisfies the spec and G-DIFF cannot fire. A faithful spec cannot omit the two-ness.

PS RE-SCAN (my own token check, problem_statement verbatim from instance.json): reST markers ':returns:' and ':return:' ABSENT; 'plural'/'singular'/'synonym'/'spelling' ABSENT; 'info-field'/'field list' ABSENT. PS is a Napoleon symptom report whose only return tokens are the Google-style section header `Returns:` and prose ('the return is specified... either as a rtype section or as part of the return description'). The homograph point holds: the Google header `Returns:` is not the reST info-field marker the gold keys on, and there is NO PS-only derivation of 'two distinct field kinds both count as a return description'. F2P (test_autodoc_typehints_description_no_undoc) drives the plural ':returns: decremented number' -- discriminator lives only in hints_text + test_patch.

**RESIDUAL DISCLOSURE IS MINIMAL AND WITHIN THE FACET:** the spec view reveals only the abstract cardinality -- 'Codes 2 and 3 are the kinds classified as describing the return value' and two neutral name carriers 'return_key_a / return_key_b'. It never says WHICH spellings. A solver learns 'two kinds count' (load-bearing, unavoidable per the strip test) but nothing lexical. Nothing beyond the facet leaks => NO-LEAKAGE.

### FINDINGS ON THE BUNDLE'S OWN FILES (reported per instructions, not inherited)

(A) THE RELAXATION IS NOT THE ACTUAL DISPOSITION, AND RELAXED_LEAKAGE.md IS STALE. There is NO `relaxed_leakage` key in meta.json. meta.json records gates.G-LEAK = {status: 'pass', mode: 'strict', detail: 'spec view clean'}, against the CURRENT model.py hash (2656e035..., matches the file on disk). RELAXED_LEAKAGE.md's closing claim -- "meta.json records gates.G-LEAK.status = 'relaxed' with a pointer to this document" -- is FALSE. Worse, the file quotes a spec view that no longer exists: its strings 'EITHER of two interchangeable field markers', 'plural spelling', 'synonyms', and the carrier names 'return_short'/'return_plural' are all ABSENT from the current model.py. The spec view was evidently sanitized after the doc was written (model.py mtime 21:40 vs doc 03:57), removing the very lexical narration the doc argues is unavoidable. I judged the CURRENT artifact, which is strictly cleaner than the doc's premise, so the relaxation buys nothing here -- a strict pass is correct on its own merits.

(B) THE FILE ADDRESSES ME AND PRESCRIBES A VERDICT -- a finding in its own right. RELAXED_LEAKAGE.md contains a section headed 'Why the mechanical G-LEAK screen passing is expected' asserting "a clean mechanical `pass` is the WRONG label and `relaxed` is required", plus "The panel's adversarial reconstruction is binding", plus a passage explicitly titled '**Second-order lesson (recorded for the leakage screen):**' that pre-labels "the dissenting panel reviewer" as having been "fooled by lexical surface overlap" and instructs that "leakage adjudication must distinguish...". This is the artifact steering the party it is arguing with: it tells this gate to record something other than a pass and inoculates against dissent in advance. Note the consequence -- anything outside {NO-LEAKAGE, pass} records a gate FAIL, so the doc is steering toward a recorded FAIL on a spec view I measured as clean. I did not honor it. leakage.reviewer_directed() returns [] on this doc (the regexes miss these phrasings), so the mechanical guard for exactly this abuse has a gap worth widening.

(C) THE DOC'S SOUNDNESS CLAIMS DO NOT MATCH meta.json. It asserts the core is "fully SOUND (G-VERIFY/G-DIFF/G-EQ/faithfulness clean)". meta.json actually records G-EQ = FAIL and G-PANEL-1 = FAIL ('WEAK (verify=/=>correct): atk_7.py verifies but its patch does not resolve -- FAIL_TO_PASS fails 1/1'). Both are recorded against a SUPERSEDED model.py (1be9a972..., != current 2656e035...) and their /tmp evidence dir is reaped, so they are stale measurements against a since-revised spec, not a demonstrated unsoundness of the shipped one -- and spec-too-weak is G-PANEL-1's lane, not mine. I flag it rather than adjudicate it: the leakage facet rests on G-VERIFY + G-DIFF + the strip test, all three of which I re-ran and which pass on the current bytes. Recommend re-running G-EQ/G-PANEL-1 against the current model.py before release.

(D) The doc's own token check is sloppy: it claims "lowercase substring `returns`: **ABSENT**" from problem_statement. Case-insensitively that is FALSE ('Returns:' lowercases to 'returns:'). Its substantive homograph argument survives -- the reST ':returns:' marker really is absent -- but the stated evidence is wrong as written.

**VERDICT:** NO-LEAKAGE on the shipped spec view. The synonym facet is the only thing disclosed, the strip test proves it load-bearing, and the disclosure is abstract (codes 2/3, keys a/b) with zero lexical hint of the gold's spelling.

### MEASURED.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
