# P2 adversarial audit — sympy__sympy-13615

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -112,18 +112,11 @@
         Invariant(Acc(list_pred(out)))
         Invariant(Acc(list_pred(undecided)))
         Invariant(0 <= i and i <= len(other))
-        Invariant(ToSeq(out) == keep_out(ToSeq(other).drop(i)))
-        Invariant(ToSeq(undecided) == keep_undecided(ToSeq(other).drop(i)))
         # invariants-end
         e = other[i - 1]
-        Assert(ToSeq(other).drop(i - 1)[0] == e)
-        Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))
         v = verdict(e)
-        if v == DEFINITELY_OUT:
+        if v != DEFINITELY_IN:
             out = [e] + out
-        elif v == UNDECIDED:
-            undecided = [e] + undecided
         i = i - 1
-    Assert(ToSeq(other).drop(0) == ToSeq(other))
     return out, undecided
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,7 +106,7 @@
     out = []  # type: List[int]
     undecided = []  # type: List[int]
     i = len(other)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(other), 1 / 2))
         Invariant(Acc(list_pred(out)))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -120,9 +120,9 @@
         Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))
         v = verdict(e)
         if v == DEFINITELY_OUT:
+            undecided = [e] + undecided
+        elif v == UNDECIDED:
             out = [e] + out
-        elif v == UNDECIDED:
-            undecided = [e] + undecided
         i = i - 1
     Assert(ToSeq(other).drop(0) == ToSeq(other))
     return out, undecided
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,10 +119,10 @@
         Assert(ToSeq(other).drop(i - 1)[0] == e)
         Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))
         v = verdict(e)
-        if v == DEFINITELY_OUT:
+        if v == UNDECIDED:
+            undecided = [e] + undecided
+        else:
             out = [e] + out
-        elif v == UNDECIDED:
-            undecided = [e] + undecided
         i = i - 1
     Assert(ToSeq(other).drop(0) == ToSeq(other))
     return out, undecided
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -118,11 +118,7 @@
         e = other[i - 1]
         Assert(ToSeq(other).drop(i - 1)[0] == e)
         Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))
-        v = verdict(e)
-        if v == DEFINITELY_OUT:
-            out = [e] + out
-        elif v == UNDECIDED:
-            undecided = [e] + undecided
+        out = [e] + out
         i = i - 1
     Assert(ToSeq(other).drop(0) == ToSeq(other))
     return out, undecided
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,6 +123,7 @@
             out = [e] + out
         elif v == UNDECIDED:
             undecided = [e] + undecided
+            out = [e] + out
         i = i - 1
     Assert(ToSeq(other).drop(0) == ToSeq(other))
     return out, undecided
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,25 +105,22 @@
     # impl-start
     out = []  # type: List[int]
     undecided = []  # type: List[int]
-    i = len(other)
-    while i > 0:
+    i = 0
+    while i < len(other):
         # invariants-start
         Invariant(Acc(list_pred(other), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(Acc(list_pred(undecided)))
         Invariant(0 <= i and i <= len(other))
-        Invariant(ToSeq(out) == keep_out(ToSeq(other).drop(i)))
-        Invariant(ToSeq(undecided) == keep_undecided(ToSeq(other).drop(i)))
+        Invariant(ToSeq(out) == keep_out(ToSeq(other).take(i)))
+        Invariant(ToSeq(undecided) == keep_undecided(ToSeq(other).take(i)))
         # invariants-end
-        e = other[i - 1]
-        Assert(ToSeq(other).drop(i - 1)[0] == e)
-        Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))
+        e = other[i]
         v = verdict(e)
-        if v == DEFINITELY_OUT:
-            out = [e] + out
-        elif v == UNDECIDED:
-            undecided = [e] + undecided
-        i = i - 1
-    Assert(ToSeq(other).drop(0) == ToSeq(other))
+        if v == UNDECIDED:
+            undecided = undecided + [e]
+        else:
+            out = out + [e]
+        i = i + 1
     return out, undecided
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13615.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Removing the members of one set from a finite collection of elements, when
  membership of an element cannot always be decided.  For each element of the
  finite collection a three-valued membership oracle reports one of:

      * DEFINITELY-IN  - the element is certainly a member of the set being
        removed;
      * DEFINITELY-OUT - the element is certainly NOT a member;
      * UNDECIDED       - membership cannot be settled (e.g. the element is a
        free placeholder whose value is unknown).

  The result partitions the elements into TWO collections, preserving the
  original order within each:

      * the DEFINITELY-OUT elements form a concrete finite collection - they
        are known to survive the removal;
      * the UNDECIDED elements are NOT discarded and NOT asserted to survive;
        they are carried in a separate, still-pending collection that records
        that their membership is unresolved.

  The DEFINITELY-IN elements appear in neither collection.  The essential
  property: an element whose membership is UNDECIDED must never be placed in
  the concrete "survivors" collection, because doing so would silently assert a
  fact (that it is not a member) that has not been established; it belongs only
  to the pending collection.

Elements are modelled as opaque integer handles; the membership oracle is an
unchanged deterministic pure callee over those handles, collapsed to the three
verdicts {DEFINITELY_OUT=0, DEFINITELY_IN=1, UNDECIDED=2} (axioms region).  The
two output collections are returned as a pair of `List[int]`; the specification
of each is carried by `PSeq[int]` via `ToSeq`, as the order-preserving
sub-selection of the input by verdict (the front-recursive folds `keep_out` /
`keep_undecided`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


DEFINITELY_OUT = 0
DEFINITELY_IN = 1
UNDECIDED = 2


# axioms-start
@Pure
@ContractOnly
def verdict(el: int) -> int:
    """The unchanged membership oracle, as a deterministic map over element
    handles collapsed to three verdicts: 0 = DEFINITELY-OUT (certainly not a
    member), 1 = DEFINITELY-IN (certainly a member), 2 = UNDECIDED (membership
    cannot be settled).  Only totality + the three-value range is relied upon:
    every element is classified into exactly one verdict, and the impl reads the
    SAME verdict the spec folds read (determinism).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(0 <= Result() and Result() <= 2)
# axioms-end


# pure-start
@Pure
def keep_out(s: PSeq[int]) -> PSeq[int]:
    """Order-preserving sub-selection of the elements whose verdict is
    DEFINITELY-OUT.  Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if verdict(s[0]) == DEFINITELY_OUT:
        return PSeq(s[0]) + keep_out(s.drop(1))
    return keep_out(s.drop(1))


@Pure
def keep_undecided(s: PSeq[int]) -> PSeq[int]:
    """Order-preserving sub-selection of the elements whose verdict is
    UNDECIDED.  Front-recursive (one unfold per loop step)."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if verdict(s[0]) == UNDECIDED:
        return PSeq(s[0]) + keep_undecided(s.drop(1))
    return keep_undecided(s.drop(1))
# pure-end


def complement_finite(other: List[int]) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(other), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(other), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The survivors collection (component 0) is EXACTLY the DEFINITELY-OUT
    # elements, in order.
    Ensures(ToSeq(Result()[0]) == keep_out(ToSeq(other)))
    # The pending collection (component 1) is EXACTLY the UNDECIDED elements,
    # in order.
    Ensures(ToSeq(Result()[1]) == keep_undecided(ToSeq(other)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    undecided = []  # type: List[int]
    i = len(other)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(Acc(list_pred(undecided)))
        Invariant(0 <= i and i <= len(other))
        Invariant(ToSeq(out) == keep_out(ToSeq(other).drop(i)))
        Invariant(ToSeq(undecided) == keep_undecided(ToSeq(other).drop(i)))
        # invariants-end
        e = other[i - 1]
        Assert(ToSeq(other).drop(i - 1)[0] == e)
        Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))
        v = verdict(e)
        if v == DEFINITELY_OUT:
            out = [e] + out
        elif v == UNDECIDED:
            undecided = [e] + undecided
        i = i - 1
    Assert(ToSeq(other).drop(0) == ToSeq(other))
    return out, undecided
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Attacked the A-legs / model-patch correspondence of the two-postcondition partition spec (survivors == keep_out(other), pending == keep_undecided(other)). Positive control (model.py impl verbatim) verifies: `bash scripts/nagini_verify.sh .../positive_control.py` -> exit 0, 'Verification successful' 14.58s.

7 same-spec wrong impls built by editing ONLY the impl region (axioms/@Pure folds/Requires/Ensures byte-identical); all confirmed same-spec (`adversary same-spec ...` exit 0 for all 7). Then `python -m swebench_unified.adversary weakness nagini sympy__sympy-13615 .../atk_N.py` run concurrently in batches of 3 (JVM+Z3 per check):
  - atk_1 = PREPATCH BUG (if v != DEFINITELY_IN: out=[e]+out, undecided left empty) -> EXIT 2, 'attack does not verify' (bug reproduced & rejected: it puts verdict-2 elems into survivors, violating ToSeq(Result()[0])==keep_out).
  - atk_2 = BOUNDARY off-by-one (while i>1 drops index 0) -> EXIT 2.
  - atk_3 = BUCKET SWAP (OUT->undecided, UNDECIDED->out) -> EXIT 2.
  - atk_4 = CONTROL-FLOW-EFFECT / IN-leak (else: out=[e]+out folds DEFINITELY_IN into survivors) -> EXIT 2.
  - atk_5 = UNGROUNDED-ORACLE ECHO (return all input as survivors, ignore verdict) -> EXIT 2.
  - atk_6 = DUPLICATE (UNDECIDED placed in BOTH out and undecided) -> EXIT 2.
  - atk_7 = FORWARD-APPEND variant (i=0..len, take(i) invariants, non-UNDECIDED incl. IN leaks into out) -> EXIT 2.
Every attack returned EXIT 2 (NOT-A-COUNTEREXAMPLE): the spec rejected all of them. NO CANDIDATE (verifying wrong impl) emerged, so there was no faithful refined patch to materialize/resolve -- verify did not imply an incorrect impl for any attack.

Why tight: both output components are pinned exactly as deterministic functions of the input carrier via keep_out/keep_undecided folds over per-element verdict; zero output freedom, so any verifying impl is behaviourally the gold three-way partition. No answer-key oracle equated to Result(); read-only `other` held at Acc(list_pred,1/2) required+ensured (no mutate-to-pass).

Refinement audit: legs A1(R), A2(R/I), A3(A-consumed), A4(R/I+A-reference), A5(R/I+A-reference), A6(I), A7(R) -- all R/A-consumed/A-reference/I, NO kind-3. A-consumed `verdict` carries only Ensures(0<=Result()<=2) (weakest sufficient: totality+range) over the UNCHANGED callee Set.contains collapsed by ternary_sift. A-reference folds keep_out/keep_undecided validated == gold sifted[False]/sifted[None] buckets by axiom_check.py (imports only sympy + stdlib; runs real Set.contains over 112 pairs+400 fuzz asserting range {0,1,2}, and gold-patched _complement structural equality vs Union(FiniteSet(out),Complement(FiniteSet(undecided),self,evaluate=False)) over 54 boundary+400 fuzz on interval/unbounded removal sets; FAIL_TO_PASS witness Complement(FiniteSet(x,y,2),Interval(-10,10))==Complement(FiniteSet(x,y),Interval(-10,10)) asserted; prepatch confirmed detectably different). Correspondence to the real callees holds. All commands run from project root under the swebench-lean venv with.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13615.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Removing the members of one set from a finite collection of elements, when
  membership of an element cannot always be decided.  For each element of the
  finite collection a three-valued membership oracle reports one of:

      * DEFINITELY-IN  - the element is certainly a member of the set being
        removed;
      * DEFINITELY-OUT - the element is certainly NOT a member;
      * UNDECIDED       - membership cannot be settled (e.g. the element is a
        free placeholder whose value is unknown).

  The result partitions the elements into TWO collections, preserving the
  original order within each:

      * the DEFINITELY-OUT elements form a concrete finite collection - they
        are known to survive the removal;
      * the UNDECIDED elements are NOT discarded and NOT asserted to survive;
        they are carried in a separate, still-pending collection that records
        that their membership is unresolved.

  The DEFINITELY-IN elements appear in neither collection.  The essential
  property: an element whose membership is UNDECIDED must never be placed in
  the concrete "survivors" collection, because doing so would silently assert a
  fact (that it is not a member) that has not been established; it belongs only
  to the pending collection.

Elements are modelled as opaque integer handles; the membership oracle is an
unchanged deterministic pure callee over those handles, collapsed to the three
verdicts {DEFINITELY_OUT=0, DEFINITELY_IN=1, UNDECIDED=2} (axioms region).  The
two output collections are returned as a pair of `List[int]`; the specification
of each is carried by `PSeq[int]` via `ToSeq`, as the order-preserving
sub-selection of the input by verdict (the front-recursive folds `keep_out` /
`keep_undecided`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


DEFINITELY_OUT = 0
DEFINITELY_IN = 1
UNDECIDED = 2


# axioms-start
@Pure
@ContractOnly
def verdict(el: int) -> int:
    """The unchanged membership oracle, as a deterministic map over element
    handles collapsed to three verdicts: 0 = DEFINITELY-OUT (certainly not a
    member), 1 = DEFINITELY-IN (certainly a member), 2 = UNDECIDED (membership
    cannot be settled).  Only totality + the three-value range is relied upon:
    every element is classified into exactly one verdict, and the impl reads the
    SAME verdict the spec folds read (determinism).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(0 <= Result() and Result() <= 2)
# axioms-end


# pure-start
@Pure
def keep_out(s: PSeq[int]) -> PSeq[int]:
    """Order-preserving sub-selection of the elements whose verdict is
    DEFINITELY-OUT.  Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if verdict(s[0]) == DEFINITELY_OUT:
        return PSeq(s[0]) + keep_out(s.drop(1))
    return keep_out(s.drop(1))


@Pure
def keep_undecided(s: PSeq[int]) -> PSeq[int]:
    """Order-preserving sub-selection of the elements whose verdict is
    UNDECIDED.  Front-recursive (one unfold per loop step)."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if verdict(s[0]) == UNDECIDED:
        return PSeq(s[0]) + keep_undecided(s.drop(1))
    return keep_undecided(s.drop(1))
# pure-end


def complement_finite(other: List[int]) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(other), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(other), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The survivors collection (component 0) is EXACTLY the DEFINITELY-OUT
    # elements, in order.
    Ensures(ToSeq(Result()[0]) == keep_out(ToSeq(other)))
    # The pending collection (component 1) is EXACTLY the UNDECIDED elements,
    # in order.
    Ensures(ToSeq(Result()[1]) == keep_undecided(ToSeq(other)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    undecided = []  # type: List[int]
    i = len(other)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(Acc(list_pred(undecided)))
        Invariant(0 <= i and i <= len(other))
        Invariant(ToSeq(out) == keep_out(ToSeq(other).drop(i)))
        Invariant(ToSeq(undecided) == keep_undecided(ToSeq(other).drop(i)))
        # invariants-end
        e = other[i - 1]
        Assert(ToSeq(other).drop(i - 1)[0] == e)
        Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))
        v = verdict(e)
        if v == DEFINITELY_OUT:
            out = [e] + out
        elif v == UNDECIDED:
            undecided = [e] + undecided
        i = i - 1
    Assert(ToSeq(other).drop(0) == ToSeq(other))
    return out, undecided
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Attacked the A-legs / model-patch correspondence of the two-postcondition partition spec (survivors == keep_out(other), pending == keep_undecided(other)). Positive control (model.py impl verbatim) verifies: `bash scripts/nagini_verify.sh .../positive_control.py` -> exit 0, 'Verification successful' 14.58s.

7 same-spec wrong impls built by editing ONLY the impl region (axioms/@Pure folds/Requires/Ensures byte-identical); all confirmed same-spec (`adversary same-spec ...` exit 0 for all 7). Then `python -m swebench_unified.adversary weakness nagini sympy__sympy-13615 .../atk_N.py` run concurrently in batches of 3 (JVM+Z3 per check):
  - atk_1 = PREPATCH BUG (if v != DEFINITELY_IN: out=[e]+out, undecided left empty) -> EXIT 2, 'attack does not verify' (bug reproduced & rejected: it puts verdict-2 elems into survivors, violating ToSeq(Result()[0])==keep_out).
  - atk_2 = BOUNDARY off-by-one (while i>1 drops index 0) -> EXIT 2.
  - atk_3 = BUCKET SWAP (OUT->undecided, UNDECIDED->out) -> EXIT 2.
  - atk_4 = CONTROL-FLOW-EFFECT / IN-leak (else: out=[e]+out folds DEFINITELY_IN into survivors) -> EXIT 2.
  - atk_5 = UNGROUNDED-ORACLE ECHO (return all input as survivors, ignore verdict) -> EXIT 2.
  - atk_6 = DUPLICATE (UNDECIDED placed in BOTH out and undecided) -> EXIT 2.
  - atk_7 = FORWARD-APPEND variant (i=0..len, take(i) invariants, non-UNDECIDED incl. IN leaks into out) -> EXIT 2.
Every attack returned EXIT 2 (NOT-A-COUNTEREXAMPLE): the spec rejected all of them. NO CANDIDATE (verifying wrong impl) emerged, so there was no faithful refined patch to materialize/resolve -- verify did not imply an incorrect impl for any attack.

Why tight: both output components are pinned exactly as deterministic functions of the input carrier via keep_out/keep_undecided folds over per-element verdict; zero output freedom, so any verifying impl is behaviourally the gold three-way partition. No answer-key oracle equated to Result(); read-only `other` held at Acc(list_pred,1/2) required+ensured (no mutate-to-pass).

Refinement audit: legs A1(R), A2(R/I), A3(A-consumed), A4(R/I+A-reference), A5(R/I+A-reference), A6(I), A7(R) -- all R/A-consumed/A-reference/I, NO kind-3. A-consumed `verdict` carries only Ensures(0<=Result()<=2) (weakest sufficient: totality+range) over the UNCHANGED callee Set.contains collapsed by ternary_sift. A-reference folds keep_out/keep_undecided validated == gold sifted[False]/sifted[None] buckets by axiom_check.py (imports only sympy + stdlib; runs real Set.contains over 112 pairs+400 fuzz asserting range {0,1,2}, and gold-patched _complement structural equality vs Union(FiniteSet(out),Complement(FiniteSet(undecided),self,evaluate=False)) over 54 boundary+400 fuzz on interval/unbounded removal sets; FAIL_TO_PASS witness Complement(FiniteSet(x,y,2),Interval(-10,10))==Complement(FiniteSet(x,y),Interval(-10,10)) asserted; prepatch confirmed detectably different). Correspondence to the real callees holds. All commands run from project root under the swebench-lean venv with.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec is FAITHFUL: on every input where the spec makes a claim, the modeled function agrees with the real gold-patched callee. No diverging input exists within the spec's claimed surface.

Evidence:
1. same-spec: atk13615.py (=bundle model.py) shares the frozen spec byte-identically (exit 0).
2. Positive control: bundle model verifies under pinned Nagini (Verification successful, 13.08s).
3. Bucket-level fidelity (the ONLY thing the two postconditions claim): 3000 randomized fuzz cases across ALL removal-set kinds (Interval bounded/open/half-infinite, FiniteSet, S.Naturals/Integers/Reals) x a pool of symbols/integers/rationals/compound exprs, comparing the model's keep_out/keep_undecided buckets against the REAL gold ternary_sift(sift)[False]/[None] buckets at base_commit 50d8a102 with the gold hunk applied (sympy 1.1.2.dev, py3.9). Result: 3000 checked, 0 mismatches. keep_out selects exactly verdict-0 (S.false) elements in order; keep_undecided selects exactly verdict-2 (unevaluated Contains) elements in order; DEFINITELY_IN (S.true) dropped from both.
4. verdict axiom (totality + range {0,1,2}) holds on every case; axiom_check.py itself reruns clean.
5. FAIL_TO_PASS witness Complement(FiniteSet(x,y,2),Interval(-10,10)) == Complement(FiniteSet(x,y),Interval(-10,10)) passes on patched source (Interval removal, squarely inside the modeled domain).

The single documented divergence — FiniteSet-vs-FiniteSet removal, e.g. Complement(FiniteSet(x,y,2),FiniteSet(2,3,4)): real assembles {x,y}\{3,4} — is NOT spec drift: it lives entirely in the UNCHANGED downstream Complement(FiniteSet,FiniteSet) subtrahend-pruning reduction the patch does not touch, and the model makes NO postcondition about the assembled Union/Complement (mapping.md §2/§3, refinement.md A7). Its only two claims are the buckets, which match exactly even in that case (buckets False=[], None=[x,y], True=[2]). The exclusion of FiniteSet-removal from the structural e2e comparison is honestly and load-bearingly documented, not a hidden over-strengthening. Spec is not too strong (and G-DIFF/PBT show prepatch + weak variants correctly rejected, so not too weak either).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Assessed the actual solver-facing spec view rendered by markers.spec_view(model.py, nagini): module docstring + `from typing import List, Tuple` / `from nagini_contracts.contracts import *` + the three verdict constants + verdict axiom (@Pure @ContractOnly, Ensures(0<=Result()<=2)) + keep_out/keep_undecided pure folds + complement_finite signature/pre/postconditions, with the impl region collapsed to `...`. same-spec on atk.py (=bundle model.py) exits 0 — spec region byte-identical to the frozen bundle.

Public baseline (problem_statement, NOT hints_text): `Complement(FiniteSet(x,y,2), Interval(-10,10))` returns `{x, y}` but `{x, y} \ [-10,10]` is expected. This publicly discloses the desired behaviour: definitely-in numbers (2) are removed, but undecidable-membership symbols (x, y) must be CARRIED in an unevaluated set-minus rather than silently dropped/asserted-out. The three-way distinction is directly readable from this public example.

Spec-view content vs. that baseline: the docstring restates that desired behaviour ABSTRACTLY over opaque int handles — a three-valued membership oracle (OUT=0/IN=1/UNDECIDED=2), OUT elements forming a concrete survivors collection (keep_out), UNDECIDED carried in a separate still-pending collection (keep_undecided), IN elements in neither. This 'what' is exactly the public expected output. Specifying correct behaviour is a spec's job and is not leakage when the behaviour is already public.

Gold-patch mechanism is ABSENT from the spec view: token scan of the rendered view finds no `sift`, `ternary_sift`, `evaluate=false`, `self.contains`, `FiniteSet`, `Interval`, `_complement`, `sets.py`, or `defaultdict`. (`complement` appears only in the modeled function name `complement_finite`; `sympy` only in the instance-id title `sympy__sympy-13615` — both trivially public.) All gold machinery (the ternary_sift closure, sift, `Union(FiniteSet(*sifted[False]), Complement(FiniteSet(*sifted[None]), self, evaluate=False) if sifted[None] else S.EmptySet)`) appears ONLY in (a) the elided impl region and (b) refinement.md/mapping.md, which are audit artifacts, not part of the solver spec view.

The two postconditions (ToSeq(Result()[0])==keep_out(ToSeq(other)), ToSeq(Result()[1])==keep_undecided(ToSeq(other))) express order-preserving structural selection by the opaque verdict oracle; they are satisfiable by ANY order-preserving three-way partition and do not reveal the sift-based implementation strategy. No spec-view line discloses the gold edit beyond what problem_statement already makes public. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
