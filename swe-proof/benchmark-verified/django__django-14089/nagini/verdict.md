# P2 adversarial audit — django__django-14089

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.py`, `atk_forward.py`, `atk_forward_loop.py`, `atk_offbyone.py`, `atk_dup.py`, `atk_partial.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -23,7 +23,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # enumeration mutates nothing it is given, so the input is required AND
     # ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(elements), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elements), 1 / 2))
@@ -60,6 +58,8 @@
     Ensures(ToSeq(Result()) == rev(ToSeq(elements)))
     # post-conditions-end
     # impl-start
+    # Pre-patch skeleton: no distinct backward enumeration is provided, so the
+    # traversal hands back the elements in their forward (insertion) order.
     result = []  # type: List[int]
     i = len(elements)
     while i > 0:
@@ -67,13 +67,12 @@
         Invariant(Acc(list_pred(elements), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(elements))
-        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))
-        Invariant(MustTerminate(i + 1))
+        Invariant(ToSeq(result) == ToSeq(elements).drop(i))
         # invariants-end
         e = elements[i - 1]
         Assert(ToSeq(elements).drop(i - 1)[0] == e)
         Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))
-        result = result + [e]
+        result = [e] + result
         i = i - 1
     return result
     # impl-end
```

Attack 2 — `atk_forward.py` → rejected (same spec, does not verify — good)

```diff
@@ -23,7 +23,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # enumeration mutates nothing it is given, so the input is required AND
     # ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(elements), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elements), 1 / 2))
@@ -60,20 +58,5 @@
     Ensures(ToSeq(Result()) == rev(ToSeq(elements)))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    i = len(elements)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(elements), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(elements))
-        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        e = elements[i - 1]
-        Assert(ToSeq(elements).drop(i - 1)[0] == e)
-        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))
-        result = result + [e]
-        i = i - 1
-    return result
+    return elements
     # impl-end
```

Attack 3 — `atk_forward_loop.py` → rejected (same spec, does not verify — good)

```diff
@@ -23,7 +23,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # enumeration mutates nothing it is given, so the input is required AND
     # ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(elements), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elements), 1 / 2))
@@ -63,17 +61,11 @@
     result = []  # type: List[int]
     i = len(elements)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(elements), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(elements))
-        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         e = elements[i - 1]
-        Assert(ToSeq(elements).drop(i - 1)[0] == e)
-        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))
-        result = result + [e]
+        result = [e] + result
         i = i - 1
     return result
     # impl-end
```

Attack 4 — `atk_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -23,7 +23,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # enumeration mutates nothing it is given, so the input is required AND
     # ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(elements), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elements), 1 / 2))
@@ -62,17 +60,11 @@
     # impl-start
     result = []  # type: List[int]
     i = len(elements)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(elements), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(elements))
-        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(1 <= i and i <= len(elements))
         e = elements[i - 1]
-        Assert(ToSeq(elements).drop(i - 1)[0] == e)
-        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))
         result = result + [e]
         i = i - 1
     return result
```

Attack 5 — `atk_dup.py` → rejected (same spec, does not verify — good)

```diff
@@ -23,7 +23,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # enumeration mutates nothing it is given, so the input is required AND
     # ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(elements), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elements), 1 / 2))
@@ -63,17 +61,11 @@
     result = []  # type: List[int]
     i = len(elements)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(elements), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(elements))
-        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         e = elements[i - 1]
-        Assert(ToSeq(elements).drop(i - 1)[0] == e)
-        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))
-        result = result + [e]
+        result = result + [e] + [e]
         i = i - 1
     return result
     # impl-end
```

Attack 6 — `atk_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -23,7 +23,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # enumeration mutates nothing it is given, so the input is required AND
     # ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(elements), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elements), 1 / 2))
@@ -60,20 +58,8 @@
     Ensures(ToSeq(Result()) == rev(ToSeq(elements)))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    i = len(elements)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(elements), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(elements))
-        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        e = elements[i - 1]
-        Assert(ToSeq(elements).drop(i - 1)[0] == e)
-        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))
-        result = result + [e]
-        i = i - 1
+    result = elements
+    if len(elements) <= 1:
+        return result
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14089.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An insertion-ordered collection of distinct elements supports enumeration in
  BOTH directions. Forward enumeration visits the elements in the order they
  were inserted; backward enumeration visits exactly the same elements in the
  opposite order. Concretely, the backward enumeration of the collection is the
  reversal of its forward enumeration: its first element is the collection's
  last element, its second element is the collection's second-to-last, and so
  on, so that element k of the backward enumeration is element (n-1-k) of the
  forward enumeration for a collection of n elements. Backward enumeration is a
  one-shot traversal (an iterator) and leaves the collection itself unchanged.

The ordered contents are modelled as `List[int]` of element keys in insertion
order (the collection stores distinct keys preserving their insertion order).
The specification is carried by the pure sequence theory `PSeq[int]`: `rev` is
the sequence-reversal the backward enumeration must equal. No callee is
axiomatized: the reversal is membership/structure logic over the input,
modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def rev(s: PSeq[int]) -> PSeq[int]:
    """The reversal of a sequence: the reversal of its tail followed by its
    head. Front-recursive (one unfold per element) so a backward impl loop that
    appends the head each step can discharge it."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return rev(s.drop(1)) + PSeq(s[0])
# pure-end


def reverse_order(elements: List[int]) -> List[int]:
    # pre-conditions-start
    # The collection's ordered contents are read-only: producing the backward
    # enumeration mutates nothing it is given, so the input is required AND
    # ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(elements), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elements), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The backward enumeration is exactly the reversal of the forward
    # enumeration: same elements, opposite order, same length. This pins the
    # discriminating behaviour — a traversal that preserves (rather than
    # reverses) the order, or drops/duplicates elements, cannot satisfy it.
    Ensures(ToSeq(Result()) == rev(ToSeq(elements)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(elements)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(elements), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(elements))
        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))
        # invariants-end
        e = elements[i - 1]
        Assert(ToSeq(elements).drop(i - 1)[0] == e)
        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))
        result = result + [e]
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT OF django__django-14089 nagini bundle. Spec is a FULLY FUNCTIONAL deep spec: postcondition `ToSeq(Result()) == rev(ToSeq(elements))` pins the output to the exact element-wise reversal of the forward enumeration for every List[int]. rev is spelled out deeply in the @Pure region (front-recursive). axioms region EMPTY (no consumed @ContractOnly axiom).

SAME-SPEC + WEAKNESS results (project root; cmd `python -m swebench_unified.adversary weakness nagini django__django-14089 <atk>`):
- positive_control.py: `bash scripts/nagini_verify.sh` -> Verification successful (13.6s). Same-spec (unchanged model.py).
- atk_prepatch.py (PREPATCH BUG, faithful pre-patch skeleton, result=[e]+result => forward order): SAME-SPEC, weakness EXIT=2 -> does NOT verify (fails reversal postcondition). Prepatch reproduced.
- atk_forward.py (return elements, identity/forward): SAME-SPEC, EXIT=2 -> does NOT verify.
- atk_forward_loop.py (correct-shaped loop but result=[e]+result => forward order): SAME-SPEC, EXIT=2 -> does NOT verify.
- atk_offbyone.py (boundary: loop stops at i>1, drops last reversal element): SAME-SPEC, EXIT=2 -> does NOT verify.
- atk_dup.py (control-flow-effect: appends each element twice, wrong length): SAME-SPEC, EXIT=2 -> does NOT verify.
- atk_partial.py (partial-domain: identity, accidentally correct only for len<=1): SAME-SPEC, EXIT=2 -> does NOT verify.
All 6 hygiene-clean wrong impls REJECTED by the spec; positive control verifies. Attack floor (min_attacks=5) met with 6.

UNGROUNDED-ORACLE ECHO PROBE (the decisive vector for a no-axiom deep spec): atk_assume_false.py (`Assume(False); return elements`) and atk_empty_assume.py (`Assume(ToSeq(result)==rev(...)); return []`) both come back CANDIDATE (same-spec AND `verifies` EXIT=0) because Assume short-circuits Nagini. HOWEVER these are NOT admissible model.py impls and are NOT submitted as attacks: `Assume(` is a G-HYGIENE banned_token for nagini (backends/nagini.py:28) — confirmed hygiene._run_python returns FAIL 'banned calls: [Assume]' on both, PASS on the clean impls/positive control. Assume(False) verifies ANY spec, so counting it would flag every nagini bundle as broken — a universal verifier-soundness escape hatch / harness artifact, not a weakness of THIS spec. atk_assume_post.py (result=elements + Assume(post)) additionally fails verification on the return permission (aliasing), EXIT=2. Files retained in scratch (atk_assume_false.py, atk_empty_assume.py, atk_assume_post.py) for the record but excluded from the attacks list so the mechanized derivation (which lacks a hygiene screen) is not driven to a false BROKEN.

G-AX (A-reference soundness): axiom_check.py EXIT=0 -> 'rev deep model (== reversed(dict)) sound on 15 boundary + 20000 fuzz inputs; backward traversal is an Iterator and read-only'. Validates list(reversed(dict.fromkeys(items))) == rev(list(d)), Iterator-ness (F2P type obligation, §B), and read-only frame.

refinement.md AUDIT: legs A1=R (OrderedSet ordered contents <-> List[int] insertion-order keys), A2=A-reference (backward enumeration modeled deeply by rev + verified loop; validated == reversed(self.dict) by G-AX, NO consumed axiom), A3=R+I (fresh iterator, read-only 1/2 permission). Iterator-ness (§B) = A-reference on the same real callee. §C: NO kind-3 step — the one changed op (adding reversed backward enumeration) is modeled deeply, not hidden behind an axiom about the function under change. A-leg correspondence to the real callees (reversed(dict), iter(dict)) holds and is machine-checked by G-AX. Gold patch (patch.diff) = verbatim `__reversed__` returning reversed(self.dict); it resolves (G-RESOLVE).

VERDICT: SOUND. No admissible (hygiene-clean) same-spec verifying impl whose faithful patch fails to resolve exists; the deep functional postcondition rejects every genuine wrong impl; A-reference deep model is G-AX-sound; refinement.md is R/A-reference/I with no kind-3.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.py`, `atk_forward.py`, `atk_forward_loop.py`, `atk_offbyone.py`, `atk_dup.py`, `atk_partial.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_forward.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_forward_loop.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_offbyone.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_dup.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_partial.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14089.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An insertion-ordered collection of distinct elements supports enumeration in
  BOTH directions. Forward enumeration visits the elements in the order they
  were inserted; backward enumeration visits exactly the same elements in the
  opposite order. Concretely, the backward enumeration of the collection is the
  reversal of its forward enumeration: its first element is the collection's
  last element, its second element is the collection's second-to-last, and so
  on, so that element k of the backward enumeration is element (n-1-k) of the
  forward enumeration for a collection of n elements. Backward enumeration is a
  one-shot traversal (an iterator) and leaves the collection itself unchanged.

The ordered contents are modelled as `List[int]` of element keys in insertion
order (the collection stores distinct keys preserving their insertion order).
The specification is carried by the pure sequence theory `PSeq[int]`: `rev` is
the sequence-reversal the backward enumeration must equal. No callee is
axiomatized: the reversal is membership/structure logic over the input,
modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def rev(s: PSeq[int]) -> PSeq[int]:
    """The reversal of a sequence: the reversal of its tail followed by its
    head. Front-recursive (one unfold per element) so a backward impl loop that
    appends the head each step can discharge it."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return rev(s.drop(1)) + PSeq(s[0])
# pure-end


def reverse_order(elements: List[int]) -> List[int]:
    # pre-conditions-start
    # The collection's ordered contents are read-only: producing the backward
    # enumeration mutates nothing it is given, so the input is required AND
    # ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(elements), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elements), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The backward enumeration is exactly the reversal of the forward
    # enumeration: same elements, opposite order, same length. This pins the
    # discriminating behaviour — a traversal that preserves (rather than
    # reverses) the order, or drops/duplicates elements, cannot satisfy it.
    Ensures(ToSeq(Result()) == rev(ToSeq(elements)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(elements)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(elements), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(elements))
        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))
        # invariants-end
        e = elements[i - 1]
        Assert(ToSeq(elements).drop(i - 1)[0] == e)
        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))
        result = result + [e]
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT OF django__django-14089 nagini bundle. Spec is a FULLY FUNCTIONAL deep spec: postcondition `ToSeq(Result()) == rev(ToSeq(elements))` pins the output to the exact element-wise reversal of the forward enumeration for every List[int]. rev is spelled out deeply in the @Pure region (front-recursive). axioms region EMPTY (no consumed @ContractOnly axiom).

SAME-SPEC + WEAKNESS results (project root; cmd `python -m swebench_unified.adversary weakness nagini django__django-14089 <atk>`):
- positive_control.py: `bash scripts/nagini_verify.sh` -> Verification successful (13.6s). Same-spec (unchanged model.py).
- atk_prepatch.py (PREPATCH BUG, faithful pre-patch skeleton, result=[e]+result => forward order): SAME-SPEC, weakness EXIT=2 -> does NOT verify (fails reversal postcondition). Prepatch reproduced.
- atk_forward.py (return elements, identity/forward): SAME-SPEC, EXIT=2 -> does NOT verify.
- atk_forward_loop.py (correct-shaped loop but result=[e]+result => forward order): SAME-SPEC, EXIT=2 -> does NOT verify.
- atk_offbyone.py (boundary: loop stops at i>1, drops last reversal element): SAME-SPEC, EXIT=2 -> does NOT verify.
- atk_dup.py (control-flow-effect: appends each element twice, wrong length): SAME-SPEC, EXIT=2 -> does NOT verify.
- atk_partial.py (partial-domain: identity, accidentally correct only for len<=1): SAME-SPEC, EXIT=2 -> does NOT verify.
All 6 hygiene-clean wrong impls REJECTED by the spec; positive control verifies. Attack floor (min_attacks=5) met with 6.

UNGROUNDED-ORACLE ECHO PROBE (the decisive vector for a no-axiom deep spec): atk_assume_false.py (`Assume(False); return elements`) and atk_empty_assume.py (`Assume(ToSeq(result)==rev(...)); return []`) both come back CANDIDATE (same-spec AND `verifies` EXIT=0) because Assume short-circuits Nagini. HOWEVER these are NOT admissible model.py impls and are NOT submitted as attacks: `Assume(` is a G-HYGIENE banned_token for nagini (backends/nagini.py:28) — confirmed hygiene._run_python returns FAIL 'banned calls: [Assume]' on both, PASS on the clean impls/positive control. Assume(False) verifies ANY spec, so counting it would flag every nagini bundle as broken — a universal verifier-soundness escape hatch / harness artifact, not a weakness of THIS spec. atk_assume_post.py (result=elements + Assume(post)) additionally fails verification on the return permission (aliasing), EXIT=2. Files retained in scratch (atk_assume_false.py, atk_empty_assume.py, atk_assume_post.py) for the record but excluded from the attacks list so the mechanized derivation (which lacks a hygiene screen) is not driven to a false BROKEN.

G-AX (A-reference soundness): axiom_check.py EXIT=0 -> 'rev deep model (== reversed(dict)) sound on 15 boundary + 20000 fuzz inputs; backward traversal is an Iterator and read-only'. Validates list(reversed(dict.fromkeys(items))) == rev(list(d)), Iterator-ness (F2P type obligation, §B), and read-only frame.

refinement.md AUDIT: legs A1=R (OrderedSet ordered contents <-> List[int] insertion-order keys), A2=A-reference (backward enumeration modeled deeply by rev + verified loop; validated == reversed(self.dict) by G-AX, NO consumed axiom), A3=R+I (fresh iterator, read-only 1/2 permission). Iterator-ness (§B) = A-reference on the same real callee. §C: NO kind-3 step — the one changed op (adding reversed backward enumeration) is modeled deeply, not hidden behind an axiom about the function under change. A-leg correspondence to the real callees (reversed(dict), iter(dict)) holds and is machine-checked by G-AX. Gold patch (patch.diff) = verbatim `__reversed__` returning reversed(self.dict); it resolves (G-RESOLVE).

VERDICT: SOUND. No admissible (hygiene-clean) same-spec verifying impl whose faithful patch fails to resolve exists; the deep functional postcondition rejects every genuine wrong impl; A-reference deep model is G-AX-sound; refinement.md is R/A-reference/I with no kind-3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14089 nagini. Modeled function reverse_order(elements) has postcondition ToSeq(Result()) == rev(ToSeq(elements)) — the result must be the exact element-wise reversal of the forward enumeration. Real callee is the gold-patch's new OrderedSet.__reversed__(self): `return reversed(self.dict)`, where self.dict = dict.fromkeys(iterable or ()) (distinct keys, insertion order) and __iter__ returns iter(self.dict). Therefore reversed(self.dict) yields exactly the keys in reverse insertion order = reversal of the forward enumeration list. The spec matches the real behavior exactly; it is neither too strong nor drifted.

Evidence (all worktree, base_commit d01709aae21..., gold patch applied):
- model.py verifies under pinned Nagini (scripts/nagini_verify.sh, exit 0, 'Verification successful').
- axiom_check.py (G-AX) passes: rev deep model == reversed(dict), reversed is a collections.abc.Iterator, and materializing it is read-only, over 15 boundary + 20000 fuzz inputs.
- conformance_check.py (G-CONF) run against the ACTUALLY-patched repo: 'G-CONF OK ... on 100018 inputs ... zero disagreements'.
- Independent adversarial probe by me: 320k+ inputs including duplicate collapsing, negatives, strings, None, True/False — zero divergence between rev(list(iter(oset))) and list(reversed(oset)).

No diverging input exists: reversed over an insertion-ordered distinct-key dict is mathematically the reversal of iter over the same dict. Bundle spec is FAITHFUL to the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The consumer spec view (docstring + axioms/pure/pre/post regions; impl elided to '...') reveals nothing about the gold edit beyond the public problem_statement, which already says: 'Allow calling reversed() on an OrderedSet ... add a __reversed__() method to OrderedSet.' The spec view only restates this behaviorally ('an insertion-ordered collection ... backward enumeration is the reversal of its forward enumeration'), abstracting the carrier to List[int]. Checks: (1) mechanical leakage.screen -> passed=True, zero hard failures. (2) No diff markers, no gold-patch line ('return reversed(self.dict)') reproduced, no patched file path (django/utils/datastructures.py) or module path in the spec view. (3) Spec-view identifiers are reverse_order/rev/elements — no verbatim echo of OrderedSet/self.dict; patch changed symbols {reversed, discard}: 'reversed' is already public in the problem statement, 'discard' does not appear. (4) No bug/fix/patch/prepatch narration in spec-view comments. (5) mapping.md and refinement.md do quote the gold hunk verbatim and name the file path, but they are auditor-facing derivation docs, NOT the consumer spec view that G-LEAK/panel-3 screens (solution_src spec view only). No relaxed_leakage flag; strict evaluation. Spec view does not leak the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
