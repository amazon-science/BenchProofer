# P2 adversarial audit — sympy__sympy-15809

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,19 +280,13 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 1 (prepatch reproduction): the stale empty-args guard is back.
+    if len(operands) == 0:
+        raise EmptyReductionRejected()
     if has_noncomparable_operand(operands):
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,19 +280,10 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
-    if has_noncomparable_operand(operands):
-        raise NonComparableOperand()
+    # ATTACK 2: the comparability pre-filter's rejection is dropped entirely;
+    # a non-comparable collection silently flows into the result branches.
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,21 +280,14 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 3: the canonical-set pass's failure is swallowed and turned into a
+    # normal identity return instead of being propagated.
     if has_noncomparable_operand(operands):
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
-        raise ReductionUndefined()
+        return identity
     count = canonical_count(operands)  # type: int
     if count == 0:
         return identity
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,25 +280,16 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 4 (boundary): count == 1 also returns the identity element, i.e. the
+    # empty-canonical-set branch swallows the single-survivor branch.
     if has_noncomparable_operand(operands):
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
-    if count == 0:
+    if count <= 1:
         return identity
-    if count == 1:
-        return single
     return aggregate
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,25 +280,18 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 5 (boundary): the single-survivor and many-survivor outcomes are
+    # swapped.
     if has_noncomparable_operand(operands):
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
     if count == 0:
         return identity
     if count == 1:
-        return single
-    return aggregate
+        return aggregate
+    return single
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,19 +280,12 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 6: an absorbing operand collapses the reduction to the lattice
+    # IDENTITY rather than to its annihilator.
     if has_noncomparable_operand(operands):
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
-        return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
+        return identity
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,19 +280,11 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
-    if has_noncomparable_operand(operands):
+    # ATTACK 7 (A-leg / exclusivity): the two decisive scan events are read as
+    # independent CONTAINMENT tests, so a collection carrying the annihilator is
+    # rejected as non-comparable instead of collapsing to it.
+    if has_noncomparable_operand(operands) or has_absorbing_operand(operands):
         raise NonComparableOperand()
-    if has_absorbing_operand(operands):
-        return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,24 +280,18 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 8 (partial domain): the empty-canonical-set branch is keyed on the
+    # raw operand cardinality, so it only fires for the literally empty
+    # collection; any other collection whose canonical set is empty aggregates.
     if has_noncomparable_operand(operands):
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
+    if len(operands) == 0:
+        return identity
     count = canonical_count(operands)  # type: int
-    if count == 0:
-        return identity
     if count == 1:
         return single
     return aggregate
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,19 +280,13 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
-    if has_noncomparable_operand(operands):
+    # ATTACK 9 (ungrounded oracle / vacuous guard): the comparability rejection is
+    # guarded by `identity == zero`, which the precondition forbids, so the raise
+    # is dead code and the rejection never actually happens.
+    if has_noncomparable_operand(operands) and identity == zero:
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,24 +280,19 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 10 (termination / control-flow-effect): on the empty collection the
+    # reduction spins forever instead of returning the identity element. It never
+    # returns a wrong value -- it never returns at all.
     if has_noncomparable_operand(operands):
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
     if count == 0:
-        return identity
+        while True:
+            count = count + 1
     if count == 1:
         return single
     return aggregate
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,19 +280,12 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 11 (A-leg): the two unchanged failures are conflated -- a
+    # non-comparable first scan event raises the canonical-set pass's error.
     if has_noncomparable_operand(operands):
-        raise NonComparableOperand()
+        raise ReductionUndefined()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,24 +280,18 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 12: the empty-canonical-set branch yields the single-survivor value
+    # rather than the lattice identity, so the empty collection does not return
+    # the identity element -- the pinned behaviour itself is broken.
     if has_noncomparable_operand(operands):
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
         raise ReductionUndefined()
     count = canonical_count(operands)  # type: int
     if count == 0:
-        return identity
+        return single
     if count == 1:
         return single
     return aggregate
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -280,21 +280,15 @@
             and not canonical_reduction_defined(operands))
     # post-conditions-end
     # impl-start
-    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
-    #  is absent: the empty collection is handled by the empty-canonical-set
-    #  branch below, returning the identity element.)
-    # The unchanged comparability pre-filter rejects a non-comparable operand
-    # before any result branch (the empty collection passes, having no operand).
+    # ATTACK 13 (A-leg, mirror of atk_11): a clean scan whose canonical-set pass
+    # is undefined raises the SCAN's comparability rejection instead of the
+    # pass's own failure -- the two unchanged failures are conflated the other way.
     if has_noncomparable_operand(operands):
         raise NonComparableOperand()
     if has_absorbing_operand(operands):
         return zero
-    # The survivors reach the canonical-set pass, which compares them against one
-    # another; where it cannot, it yields no canonical set and its failure
-    # propagates (the empty collection is defined here, having nothing to
-    # compare).
     if not canonical_reduction_defined(operands):
-        raise ReductionUndefined()
+        raise NonComparableOperand()
     count = canonical_count(operands)  # type: int
     if count == 0:
         return identity
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for sympy__sympy-15809.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lattice reduction (the associative-commutative fold that selects an extreme
  element from a collection of comparable operands) is a TOTAL operation over
  every operand collection its stages can carry through — INCLUDING the EMPTY
  collection. The construction proceeds in stages over the operands:

    * A single pre-filter SCANS the operands in collection order and stops at
      the FIRST operand that is decisive for the whole reduction. Exactly which
      event the scan meets first determines the outcome:

        - if that operand is not comparable within the lattice's order, the
          whole reduction fails with a non-comparable-operand error;
        - if that operand is the lattice's absorbing element (its annihilator),
          the whole reduction collapses to that annihilator.

      An operand that is neither is passed over and the scan continues. Because
      one scan has one first decisive event, AT MOST ONE of the two can fire on
      any given collection: whichever the scan reaches first wins, and the other
      is never observed even when such an operand also occurs later in the
      collection. (The empty collection contains no operand, so the scan meets
      neither event and can never reject it nor collapse it.)

    * The operands the scan passed over are then reduced to a canonical set by
      a pass that COMPARES survivors AGAINST ONE ANOTHER. That pass is PARTIAL,
      and it makes a DIFFERENT observation than the scan: the scan judges each
      operand ON ITS OWN, so an operand it passes over can still fail to compare
      against another survivor — and then this pass yields no canonical set at
      all, propagating its own comparison failure, and the whole reduction fails
      with a reduction-undefined error. A collection whose scan already decided
      the outcome never reaches this pass. The empty collection reduces to the
      empty set (a pass with nothing to compare cannot fail).

    * If the canonical set is empty, the reduction returns the lattice's
      IDENTITY element (the neutral element of the fold — the value an empty
      fold must yield). If it has a single member, the reduction returns that
      member. Otherwise the reduction returns the assembled aggregate.

  The behaviour pinned here: the reduction of the EMPTY operand collection
  RETURNS NORMALLY and yields the lattice identity element — it is never
  rejected. (For the maximum the identity is negative infinity; for the
  minimum it is positive infinity — the neutral element each empty fold must
  return.) More generally, whenever the canonical operand set is empty the
  result is exactly the identity element, whatever caused the set to be empty.
  In contrast, the two failures above are UNCHANGED and remain obligatory on the
  collections that reach them: a reduction whose scan meets a non-comparable
  operand FIRST is STILL rejected with the non-comparable-operand error, and one
  that reaches the canonical-set pass and cannot compare its survivors STILL
  fails with the reduction-undefined error. Comparability of every operand the
  scan reaches, and reducibility of the survivors it passes over, remain
  preconditions of every NON-empty reduction. Neither failure can happen on the
  empty collection: it has no operand for the scan to reach and nothing for the
  reduction pass to compare.

The operand collection is modelled as ``List[int]`` (each operand abstracted to
an opaque int; the reduction observes only collection cardinality, WHICH of the
two decisive scan events fires first (if either), whether the canonical-set pass
is defined, and the canonical-set cardinality, not operand payloads). The
lattice's identity and annihilator elements are distinct opaque int sentinels
passed in. The four unchanged pre-reduction observations — the two decisive
outcomes of the ordered scan, the definedness of the canonical-set pass and the
cardinality it yields — are axiomatized at their weakest sufficient contracts
(an empty collection triggers neither scan event, is reducible, and reduces to
the empty set; the two scan events are mutually exclusive because one ordered
scan has one first decisive event; and a canonical cardinality exists only where
that pass is defined). Each rejection is a user-defined exception class
(a builtin exception in an ``Exsures`` crashes the Nagini translator; mapping.md
§2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class EmptyReductionRejected(Exception):
    """Signals that the reduction rejected its operand collection for being
    empty. Stands in for the `ValueError` a stale implementation raises on an
    empty collection; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2). The pinned behaviour FORBIDS this on the empty
    collection."""

class NonComparableOperand(Exception):
    """Signals that the reduction rejected its operand collection because the
    ordered pre-filter scan met an operand that is not comparable within the
    lattice's order. Stands in for the `ValueError` the unchanged scan raises on
    such an operand; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2). This rejection is REQUIRED exactly when the
    non-comparable event is the scan's FIRST decisive event."""

class ReductionUndefined(Exception):
    """Signals that the reduction failed because the canonical-set pass, reached
    with the operands the scan passed over, could not compare them against one
    another and propagated its own comparison failure instead of yielding a
    canonical set. Stands in for whatever error that unchanged pass propagates
    (mapping.md §2); a builtin exception in an `Exsures` crashes the Nagini
    translator. This failure is REQUIRED exactly when the scan is clean, no
    absorbing operand collapses the reduction, and the pass is undefined."""

# axioms-start
@Pure
@ContractOnly
def has_noncomparable_operand(operands: List[int]) -> bool:
    """Unchanged ordered pre-filter scan, non-comparable outcome: whether the
    scan over the operands in collection order meets a NON-COMPARABLE operand as
    its FIRST decisive event. This is NOT "the collection contains a
    non-comparable operand": a collection may carry one and still not be
    rejected, because the scan stops earlier at an absorbing operand and
    collapses instead. The only property the proof consumes is that an EMPTY
    collection has no operand for the scan to reach, so this event can never
    fire on it. Weakest sufficient contract; provenance + executable soundness
    check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Ensures(Implies(len(operands) == 0, not Result()))

@Pure
@ContractOnly
def has_absorbing_operand(operands: List[int]) -> bool:
    """Unchanged ordered pre-filter scan, absorbing outcome: whether the scan
    over the operands in collection order meets the lattice's ABSORBING element
    (the annihilator that collapses the whole reduction) as its FIRST decisive
    event. As above this is NOT mere containment: an absorbing operand that the
    scan never reaches — because it stops earlier at a non-comparable operand —
    does not collapse the reduction. The properties the proof consumes: an EMPTY
    collection has no operand for the scan to reach, so this event can never fire
    on it; and it is EXCLUSIVE with the non-comparable event, since one ordered
    scan has exactly one first decisive event. Weakest sufficient contract;
    provenance + executable soundness check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Ensures(Implies(len(operands) == 0, not Result()))
    Ensures(Implies(Result(), not has_noncomparable_operand(operands)))

@Pure
@ContractOnly
def canonical_reduction_defined(operands: List[int]) -> bool:
    """Unchanged canonical-set pass, DEFINEDNESS outcome: whether that pass
    yields a canonical set at all, rather than propagating a comparison failure
    over the survivors the scan passed over. It is a different observation from
    the scan's per-operand one: the scan judges each operand ALONE, this pass
    compares survivors AGAINST ONE ANOTHER, so an operand the scan passes over
    can still be one this pass cannot place. Vacuously true on a collection whose
    scan already decided the outcome, since the pass is then never reached. The
    only property the proof consumes is that an EMPTY collection leaves this pass
    nothing to compare, so it cannot fail on it. Weakest sufficient contract;
    provenance + executable soundness check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Ensures(Implies(len(operands) == 0, Result()))

@Pure
@ContractOnly
def canonical_count(operands: List[int]) -> int:
    """Unchanged canonical-set reduction: the number of operands surviving the
    redundancy-removal/normalisation pass. PARTIAL — a canonical cardinality
    exists only where that pass is defined, which is why the definedness axiom
    above guards this one's `Requires`: a pass that propagated a comparison
    failure produced no canonical set and so has no count to report. Where it is
    defined the properties the proof consumes are: the count is never negative,
    and an EMPTY collection reduces to the empty canonical set (count 0).
    Weakest sufficient contract; provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Requires(canonical_reduction_defined(operands))
    Ensures(Result() >= 0)
    Ensures(Implies(len(operands) == 0, Result() == 0))
# axioms-end

# pure-start
# (no module-level pure helpers required: the reduction's result selection is
# concrete control flow over the canonical-set cardinality, stated directly.)
# pure-end

def lattice_reduce(operands: List[int], identity: int, zero: int,
                   single: int, aggregate: int) -> int:
    # pre-conditions-start
    # The operand collection is read, not mutated (fractional permission).
    Requires(Acc(list_pred(operands), 1 / 2))
    # The four possible NORMAL outcomes are distinct values, so each
    # postcondition clause pins exactly one branch (the identity branch is the
    # discriminating one): identity (empty canonical set), zero (absorbing
    # operand seen), single (one survivor), aggregate (many survivors).
    Requires(identity != zero and identity != single and identity != aggregate)
    Requires(zero != single and zero != aggregate and single != aggregate)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(operands), 1 / 2))
    # On every collection the stages can carry through — the scan's first
    # decisive event is not the non-comparable one, AND the canonical-set pass is
    # defined (vacuously so when the scan already decided the outcome) — the
    # reduction is TOTAL: it always returns one of the four outcomes and never
    # raises. Returning normally on the empty collection is therefore guaranteed:
    # by their axioms the empty collection has no non-comparable first event and
    # is reducible, and no Exsures below admits a rejection there.
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and canonical_reduction_defined(operands),
                    Result() == identity or Result() == zero
                    or Result() == single or Result() == aggregate))
    # An absorbing operand collapses the reduction to the annihilator (among
    # comparable operands).
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and has_absorbing_operand(operands),
                    Result() == zero))
    # The discriminating clause: when the canonical operand set is empty (the
    # scan decided nothing and the canonical-set pass is defined) the result is
    # the IDENTITY element. The empty operand collection is the primary witness
    # (no non-comparable operand, no absorbing operand, reducible, empty
    # canonical set), so the reduction of the empty collection returns normally
    # and yields identity. The count is read only under the definedness
    # antecedent, which is that observation's precondition.
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and not has_absorbing_operand(operands)
                    and canonical_reduction_defined(operands),
                    Implies(canonical_count(operands) == 0,
                            Result() == identity)))
    Ensures(Implies(len(operands) == 0, Result() == identity))
    # A single survivor is returned as itself; many survivors aggregate.
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and not has_absorbing_operand(operands)
                    and canonical_reduction_defined(operands),
                    Implies(canonical_count(operands) == 1,
                            Result() == single)))
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and not has_absorbing_operand(operands)
                    and canonical_reduction_defined(operands),
                    Implies(canonical_count(operands) >= 2,
                            Result() == aggregate)))
    # A NORMAL return is admissible ONLY when the scan's first decisive event is
    # not the non-comparable one: equivalently, a reduction whose scan meets a
    # non-comparable operand FIRST MUST be rejected (it can never return a
    # value). This OBLIGATES the rejection on that path — the Exsures below only
    # grants PERMISSION to raise; this postcondition forbids the alternative
    # (silently returning a value), which is exactly what the unchanged scan
    # forbids. It does NOT obligate a rejection merely because a non-comparable
    # operand occurs somewhere in the collection: when the scan stops earlier at
    # an absorbing operand the reduction collapses to the annihilator instead,
    # and the exclusivity axiom above makes that path provable.
    Ensures(not has_noncomparable_operand(operands))
    # The mirror obligation for the canonical-set pass: a NORMAL return is
    # admissible only when the scan already decided the outcome (the absorbing
    # event fired, so the pass is never reached) or that pass is DEFINED. So a
    # reduction that reaches the pass and cannot compare its survivors can never
    # return a value either; it MUST propagate the reduction-undefined failure.
    # The Exsures below only grants permission to raise it — this clause forbids
    # the alternative, which is exactly what the unchanged pass forbids.
    Ensures(has_absorbing_operand(operands)
            or canonical_reduction_defined(operands))
    # The read permission to the operand collection is returned on the
    # exceptional path too (the collection is never mutated).
    Exsures(NonComparableOperand, Acc(list_pred(operands), 1 / 2))
    Exsures(ReductionUndefined, Acc(list_pred(operands), 1 / 2))
    # A reduction whose scan meets a non-comparable operand first is REJECTED
    # with the non-comparable-operand error — comparability of every operand the
    # scan reaches is a precondition of every non-empty reduction, and the
    # unchanged scan still enforces it. (The empty collection has no operand, so
    # this is never raised on it; the axiom's empty-collection property
    # guarantees that.)
    Exsures(NonComparableOperand, has_noncomparable_operand(operands))
    # A reduction whose scan is clean and uncollapsed, and whose canonical-set
    # pass then cannot compare the survivors against one another, FAILS with the
    # reduction-undefined error — reducibility of the survivors the scan passes
    # over is a precondition of every non-empty reduction, and the unchanged pass
    # still enforces it. This failure is admissible ONLY on that exact class: not
    # where the scan rejects (the clause above owns that path), not where an
    # absorbing operand collapses the reduction before the pass is reached, and
    # never on the empty collection, which by the definedness axiom leaves the
    # pass nothing to compare.
    Exsures(ReductionUndefined, not has_noncomparable_operand(operands)
            and not has_absorbing_operand(operands)
            and not canonical_reduction_defined(operands))
    # post-conditions-end
    # impl-start
    if has_noncomparable_operand(operands):
        raise NonComparableOperand()
    if has_absorbing_operand(operands):
        return zero
    if not canonical_reduction_defined(operands):
        raise ReductionUndefined()
    count = canonical_count(operands)  # type: int
    if count == 0:
        return identity
    if count == 1:
        return single
    return aggregate
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. 13 same-spec wrong impls, ALL rejected by the frozen spec; positive control verifies (22.9s) and its faithful patch RESOLVES. No CANDIDATE wrong impl arose, so verify=>correct is not falsified here.

**Protocol:** every attack copied model.py and edited ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical). `adversary same-spec` returned exit 0 (SAME) for all 13 + the control. `adversary weakness nagini sympy__sympy-15809 <f>` run 3-way concurrent (JVM+Z3 per check).

COMMAND (each): python -m swebench_unified.adversary weakness nagini sympy__sympy-15809 atk_N.py

### RESULTS (exit 2 = NOT-A-COUNTEREXAMPLE / spec rejected = good):
 atk_1  PREPATCH REPRO (stale `if len(operands)==0: raise EmptyReductionRejected()`) -> exit 2. prepatch bug reproduced and rejected.
 atk_2  drops the unchanged non-comparable rejection (control-flow-effect) -> exit 2. Nagini: `Assertion (not has_noncomparable... and not has_absorbing... and not canonical_reduction_defined) might not hold` at the ReductionUndefined Exsures -- i.e. Ensures(not has_noncomparable_operand) supplies the OBLIGATION, closing the hole a prior audit flagged as atk_2.
 atk_3  swallows the canonical-set failure, returns identity instead -> exit 2.
 atk_4  BOUNDARY: count<=1 folded into the identity branch -> exit 2.
 atk_5  BOUNDARY: single/aggregate swapped -> exit 2.
 atk_6  absorbing branch collapses to identity, not the annihilator -> exit 2.
 atk_7  A-LEG/EXCLUSIVITY: reads the two scan events as CONTAINMENT tests, so an annihilator-bearing collection is rejected rather than collapsing -> exit 2. The exclusivity Ensures on has_absorbing_operand is load-bearing, not decorative.
 atk_8  PARTIAL-DOMAIN: identity branch keyed on raw operand cardinality (len==0) instead of the canonical-set count -> exit 2. Nagini names exactly `Implies(canonical_count==0, Result()==identity)`.
 atk_9  UNGROUNDED-ORACLE/vacuous guard: nc raise hidden behind `identity == zero`, which the precondition forbids, so the raise is dead code -> exit 2. (Guarded self-calls going vacuous is a known failure mode; the spec catches it here.)
 atk_10 TERMINATION: diverges (while True) on the empty collection rather than returning identity -> exit 2. MustTerminate(2) at the method level rejects it.
 atk_11 A-LEG: nc first event raises ReductionUndefined (failures conflated) -> exit 2.
 atk_12 breaks the FIX itself: empty canonical set yields `single`, not identity -> exit 2.
 atk_13 A-LEG mirror of atk_11: undefined pass raises NonComparableOperand -> exit 2.

POSITIVE CONTROL /pc.py: `weakness` exit 0 (CANDIDATE: shares spec AND verifies, 22.9s) -- expected, it IS the gold impl. Per protocol I materialized its faithful refined patch (= patch.diff verbatim, the A3 guard deletion) and RAN the official harness:
  python -c 'run_resolve("sympy__sympy-15809", patch)'  ->  RESOLVED= True
  FAIL_TO_PASS: test_Min, test_Max both success; PASS_TO_PASS: all 10 success; FAIL_TO_FAIL/PASS_TO_FAIL empty.
So the one verifying impl's faithful patch DOES resolve -- no verify/correct divergence. (Note: only a WRONG verifying impl could break the gate; none existed.)

A-LEG AUDIT (my mandate) -- independently re-driven against the REAL callee, not taken from axiom_check.py. Cloned the upstream repository at base_commit 28d913d3 into scratch, applied patch.diff, drove sympy 1.4.dev directly, consuming the real `_new_args_filter` for the scan's first event: A3 (the fix): Min()==oo, Max()==-oo; scan([])==ok for both. Empty returns identity, never raises. MATCHES. A3b/A4 EXCLUSIVITY: Min(-oo,I)=-oo and Max(oo,I)=oo (scan=absorbing) vs Min(I,-oo)/Max(I,oo) raise ValueError (scan=noncomparable); also behind a comparable symbol, both orders. The constructor's observable equals the scan's FIRST event in all 8 cases.

Confirms these are first-decisive-event predicates, NOT containment tests -- and atk_7 shows the model would be UNFAITHFUL under the containment reading. A4b: reproduced 18/84 collections whose scan is CLEAN yet whose canonical-set pass FAILS (TypeError from Expr.`__ge__` via `_find_localzeros`/`_is_connected`) -- e.g. Min(x, x+I), Min(x,a,x+`2*I`). Matches meta.json's recorded 18 exactly. Asserted the key soundness property myself: scan clean => the reduction NEVER raises the scan's own comparability ValueError, so the two observations really are distinct. The leg is reachable, not dead.

This is precisely the G-PANEL-2 UNFAITHFUL finding ([x, x+I], canonical_count total => spec-too-strong), and the frozen model has since been repaired: canonical_count is now PARTIAL (Requires(canonical_reduction_defined)) with the definedness predicate + its Exsures/obligation pair carrying the leg. The old defect does not survive in this model. A3b obligation: Min/Max of I, (I,x), (zoo,1), nan, (x,I) -- scan=noncomparable and real=ValueError agree in all 10. A5/A6/A7: Min(x)=x (count 1 -> operand), Min(x,x)=x (collapses to 1), Min(x,a)=Min(a,x) (count 2 -> aggregate). All A-leg assertions passed.

The four axioms claim only their weakest empty-collection/non-negativity/exclusivity properties; none over-claims, and each Ensures I could attack (exclusivity via atk_7, partiality via atk_3/atk_13, count-vs-cardinality via atk_8) is load-bearing.

**REFINEMENT.MD AUDIT:** legs A1,A2,A7,A8 = R; A3 = R+I; A3b,A4,A4b,A5 = A-consumed; A6 = A-consumed+I. NO kind-3 (unexpressible-changed-op) leg, and deep_model_references is empty in meta.json, consistent with §B's "no A-reference deep model" claim -- correct, since the change is a control-flow deletion, not a string/numeric transform, so there is no deep model to mis-key. Every A-leg cites a real file:line in the UNCHANGED callees (`_new_args_filter` :521-523/:525-526, `_collapse_arguments` :373-506, `_find_localzeros` :536-560, `_is_connected` :552/:574, expr.py:295) and I confirmed each behaviourally above. The changed operation (A3) is modeled DIRECTLY as the absence of the leading raise, not axiomatized away -- the honest encoding.

CAVEAT (advisory, not a gate failure): the spec observes only cardinality + which decisive event fires + definedness + canonical count, so it cannot distinguish WHICH survivor `single` denotes or which aggregate is assembled (A7/A8 are pure R legs to opaque sentinels). A wrong impl returning the wrong survivor is outside the modeled abstraction. That is inherent to the sentinel refinement and is covered mechanically by G-CONF (100282 checks, 0 disagreements, all 6 branches hit) rather than by G-EQ; it is not a hole the A legs could close. Since the patch under specification is a pure guard deletion that touches none of that selection logic, the abstraction is adequate for THIS delta.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

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

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for sympy__sympy-15809.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lattice reduction (the associative-commutative fold that selects an extreme
  element from a collection of comparable operands) is a TOTAL operation over
  every operand collection its stages can carry through — INCLUDING the EMPTY
  collection. The construction proceeds in stages over the operands:

    * A single pre-filter SCANS the operands in collection order and stops at
      the FIRST operand that is decisive for the whole reduction. Exactly which
      event the scan meets first determines the outcome:

        - if that operand is not comparable within the lattice's order, the
          whole reduction fails with a non-comparable-operand error;
        - if that operand is the lattice's absorbing element (its annihilator),
          the whole reduction collapses to that annihilator.

      An operand that is neither is passed over and the scan continues. Because
      one scan has one first decisive event, AT MOST ONE of the two can fire on
      any given collection: whichever the scan reaches first wins, and the other
      is never observed even when such an operand also occurs later in the
      collection. (The empty collection contains no operand, so the scan meets
      neither event and can never reject it nor collapse it.)

    * The operands the scan passed over are then reduced to a canonical set by
      a pass that COMPARES survivors AGAINST ONE ANOTHER. That pass is PARTIAL,
      and it makes a DIFFERENT observation than the scan: the scan judges each
      operand ON ITS OWN, so an operand it passes over can still fail to compare
      against another survivor — and then this pass yields no canonical set at
      all, propagating its own comparison failure, and the whole reduction fails
      with a reduction-undefined error. A collection whose scan already decided
      the outcome never reaches this pass. The empty collection reduces to the
      empty set (a pass with nothing to compare cannot fail).

    * If the canonical set is empty, the reduction returns the lattice's
      IDENTITY element (the neutral element of the fold — the value an empty
      fold must yield). If it has a single member, the reduction returns that
      member. Otherwise the reduction returns the assembled aggregate.

  The behaviour pinned here: the reduction of the EMPTY operand collection
  RETURNS NORMALLY and yields the lattice identity element — it is never
  rejected. (For the maximum the identity is negative infinity; for the
  minimum it is positive infinity — the neutral element each empty fold must
  return.) More generally, whenever the canonical operand set is empty the
  result is exactly the identity element, whatever caused the set to be empty.
  In contrast, the two failures above are UNCHANGED and remain obligatory on the
  collections that reach them: a reduction whose scan meets a non-comparable
  operand FIRST is STILL rejected with the non-comparable-operand error, and one
  that reaches the canonical-set pass and cannot compare its survivors STILL
  fails with the reduction-undefined error. Comparability of every operand the
  scan reaches, and reducibility of the survivors it passes over, remain
  preconditions of every NON-empty reduction. Neither failure can happen on the
  empty collection: it has no operand for the scan to reach and nothing for the
  reduction pass to compare.

The operand collection is modelled as ``List[int]`` (each operand abstracted to
an opaque int; the reduction observes only collection cardinality, WHICH of the
two decisive scan events fires first (if either), whether the canonical-set pass
is defined, and the canonical-set cardinality, not operand payloads). The
lattice's identity and annihilator elements are distinct opaque int sentinels
passed in. The four unchanged pre-reduction observations — the two decisive
outcomes of the ordered scan, the definedness of the canonical-set pass and the
cardinality it yields — are axiomatized at their weakest sufficient contracts
(an empty collection triggers neither scan event, is reducible, and reduces to
the empty set; the two scan events are mutually exclusive because one ordered
scan has one first decisive event; and a canonical cardinality exists only where
that pass is defined). Each rejection is a user-defined exception class
(a builtin exception in an ``Exsures`` crashes the Nagini translator; mapping.md
§2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class EmptyReductionRejected(Exception):
    """Signals that the reduction rejected its operand collection for being
    empty. Stands in for the `ValueError` a stale implementation raises on an
    empty collection; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2). The pinned behaviour FORBIDS this on the empty
    collection."""

class NonComparableOperand(Exception):
    """Signals that the reduction rejected its operand collection because the
    ordered pre-filter scan met an operand that is not comparable within the
    lattice's order. Stands in for the `ValueError` the unchanged scan raises on
    such an operand; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2). This rejection is REQUIRED exactly when the
    non-comparable event is the scan's FIRST decisive event."""

class ReductionUndefined(Exception):
    """Signals that the reduction failed because the canonical-set pass, reached
    with the operands the scan passed over, could not compare them against one
    another and propagated its own comparison failure instead of yielding a
    canonical set. Stands in for whatever error that unchanged pass propagates
    (mapping.md §2); a builtin exception in an `Exsures` crashes the Nagini
    translator. This failure is REQUIRED exactly when the scan is clean, no
    absorbing operand collapses the reduction, and the pass is undefined."""

# axioms-start
@Pure
@ContractOnly
def has_noncomparable_operand(operands: List[int]) -> bool:
    """Unchanged ordered pre-filter scan, non-comparable outcome: whether the
    scan over the operands in collection order meets a NON-COMPARABLE operand as
    its FIRST decisive event. This is NOT "the collection contains a
    non-comparable operand": a collection may carry one and still not be
    rejected, because the scan stops earlier at an absorbing operand and
    collapses instead. The only property the proof consumes is that an EMPTY
    collection has no operand for the scan to reach, so this event can never
    fire on it. Weakest sufficient contract; provenance + executable soundness
    check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Ensures(Implies(len(operands) == 0, not Result()))

@Pure
@ContractOnly
def has_absorbing_operand(operands: List[int]) -> bool:
    """Unchanged ordered pre-filter scan, absorbing outcome: whether the scan
    over the operands in collection order meets the lattice's ABSORBING element
    (the annihilator that collapses the whole reduction) as its FIRST decisive
    event. As above this is NOT mere containment: an absorbing operand that the
    scan never reaches — because it stops earlier at a non-comparable operand —
    does not collapse the reduction. The properties the proof consumes: an EMPTY
    collection has no operand for the scan to reach, so this event can never fire
    on it; and it is EXCLUSIVE with the non-comparable event, since one ordered
    scan has exactly one first decisive event. Weakest sufficient contract;
    provenance + executable soundness check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Ensures(Implies(len(operands) == 0, not Result()))
    Ensures(Implies(Result(), not has_noncomparable_operand(operands)))

@Pure
@ContractOnly
def canonical_reduction_defined(operands: List[int]) -> bool:
    """Unchanged canonical-set pass, DEFINEDNESS outcome: whether that pass
    yields a canonical set at all, rather than propagating a comparison failure
    over the survivors the scan passed over. It is a different observation from
    the scan's per-operand one: the scan judges each operand ALONE, this pass
    compares survivors AGAINST ONE ANOTHER, so an operand the scan passes over
    can still be one this pass cannot place. Vacuously true on a collection whose
    scan already decided the outcome, since the pass is then never reached. The
    only property the proof consumes is that an EMPTY collection leaves this pass
    nothing to compare, so it cannot fail on it. Weakest sufficient contract;
    provenance + executable soundness check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Ensures(Implies(len(operands) == 0, Result()))

@Pure
@ContractOnly
def canonical_count(operands: List[int]) -> int:
    """Unchanged canonical-set reduction: the number of operands surviving the
    redundancy-removal/normalisation pass. PARTIAL — a canonical cardinality
    exists only where that pass is defined, which is why the definedness axiom
    above guards this one's `Requires`: a pass that propagated a comparison
    failure produced no canonical set and so has no count to report. Where it is
    defined the properties the proof consumes are: the count is never negative,
    and an EMPTY collection reduces to the empty canonical set (count 0).
    Weakest sufficient contract; provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Requires(canonical_reduction_defined(operands))
    Ensures(Result() >= 0)
    Ensures(Implies(len(operands) == 0, Result() == 0))
# axioms-end

# pure-start
# (no module-level pure helpers required: the reduction's result selection is
# concrete control flow over the canonical-set cardinality, stated directly.)
# pure-end

def lattice_reduce(operands: List[int], identity: int, zero: int,
                   single: int, aggregate: int) -> int:
    # pre-conditions-start
    # The operand collection is read, not mutated (fractional permission).
    Requires(Acc(list_pred(operands), 1 / 2))
    # The four possible NORMAL outcomes are distinct values, so each
    # postcondition clause pins exactly one branch (the identity branch is the
    # discriminating one): identity (empty canonical set), zero (absorbing
    # operand seen), single (one survivor), aggregate (many survivors).
    Requires(identity != zero and identity != single and identity != aggregate)
    Requires(zero != single and zero != aggregate and single != aggregate)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(operands), 1 / 2))
    # On every collection the stages can carry through — the scan's first
    # decisive event is not the non-comparable one, AND the canonical-set pass is
    # defined (vacuously so when the scan already decided the outcome) — the
    # reduction is TOTAL: it always returns one of the four outcomes and never
    # raises. Returning normally on the empty collection is therefore guaranteed:
    # by their axioms the empty collection has no non-comparable first event and
    # is reducible, and no Exsures below admits a rejection there.
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and canonical_reduction_defined(operands),
                    Result() == identity or Result() == zero
                    or Result() == single or Result() == aggregate))
    # An absorbing operand collapses the reduction to the annihilator (among
    # comparable operands).
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and has_absorbing_operand(operands),
                    Result() == zero))
    # The discriminating clause: when the canonical operand set is empty (the
    # scan decided nothing and the canonical-set pass is defined) the result is
    # the IDENTITY element. The empty operand collection is the primary witness
    # (no non-comparable operand, no absorbing operand, reducible, empty
    # canonical set), so the reduction of the empty collection returns normally
    # and yields identity. The count is read only under the definedness
    # antecedent, which is that observation's precondition.
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and not has_absorbing_operand(operands)
                    and canonical_reduction_defined(operands),
                    Implies(canonical_count(operands) == 0,
                            Result() == identity)))
    Ensures(Implies(len(operands) == 0, Result() == identity))
    # A single survivor is returned as itself; many survivors aggregate.
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and not has_absorbing_operand(operands)
                    and canonical_reduction_defined(operands),
                    Implies(canonical_count(operands) == 1,
                            Result() == single)))
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and not has_absorbing_operand(operands)
                    and canonical_reduction_defined(operands),
                    Implies(canonical_count(operands) >= 2,
                            Result() == aggregate)))
    # A NORMAL return is admissible ONLY when the scan's first decisive event is
    # not the non-comparable one: equivalently, a reduction whose scan meets a
    # non-comparable operand FIRST MUST be rejected (it can never return a
    # value). This OBLIGATES the rejection on that path — the Exsures below only
    # grants PERMISSION to raise; this postcondition forbids the alternative
    # (silently returning a value), which is exactly what the unchanged scan
    # forbids. It does NOT obligate a rejection merely because a non-comparable
    # operand occurs somewhere in the collection: when the scan stops earlier at
    # an absorbing operand the reduction collapses to the annihilator instead,
    # and the exclusivity axiom above makes that path provable.
    Ensures(not has_noncomparable_operand(operands))
    # The mirror obligation for the canonical-set pass: a NORMAL return is
    # admissible only when the scan already decided the outcome (the absorbing
    # event fired, so the pass is never reached) or that pass is DEFINED. So a
    # reduction that reaches the pass and cannot compare its survivors can never
    # return a value either; it MUST propagate the reduction-undefined failure.
    # The Exsures below only grants permission to raise it — this clause forbids
    # the alternative, which is exactly what the unchanged pass forbids.
    Ensures(has_absorbing_operand(operands)
            or canonical_reduction_defined(operands))
    # The read permission to the operand collection is returned on the
    # exceptional path too (the collection is never mutated).
    Exsures(NonComparableOperand, Acc(list_pred(operands), 1 / 2))
    Exsures(ReductionUndefined, Acc(list_pred(operands), 1 / 2))
    # A reduction whose scan meets a non-comparable operand first is REJECTED
    # with the non-comparable-operand error — comparability of every operand the
    # scan reaches is a precondition of every non-empty reduction, and the
    # unchanged scan still enforces it. (The empty collection has no operand, so
    # this is never raised on it; the axiom's empty-collection property
    # guarantees that.)
    Exsures(NonComparableOperand, has_noncomparable_operand(operands))
    # A reduction whose scan is clean and uncollapsed, and whose canonical-set
    # pass then cannot compare the survivors against one another, FAILS with the
    # reduction-undefined error — reducibility of the survivors the scan passes
    # over is a precondition of every non-empty reduction, and the unchanged pass
    # still enforces it. This failure is admissible ONLY on that exact class: not
    # where the scan rejects (the clause above owns that path), not where an
    # absorbing operand collapses the reduction before the pass is reached, and
    # never on the empty collection, which by the definedness axiom leaves the
    # pass nothing to compare.
    Exsures(ReductionUndefined, not has_noncomparable_operand(operands)
            and not has_absorbing_operand(operands)
            and not canonical_reduction_defined(operands))
    # post-conditions-end
    # impl-start
    if has_noncomparable_operand(operands):
        raise NonComparableOperand()
    if has_absorbing_operand(operands):
        return zero
    if not canonical_reduction_defined(operands):
        raise ReductionUndefined()
    count = canonical_count(operands)  # type: int
    if count == 0:
        return identity
    if count == 1:
        return single
    return aggregate
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. 13 same-spec wrong impls, ALL rejected by the frozen spec; positive control verifies (22.9s) and its faithful patch RESOLVES. No CANDIDATE wrong impl arose, so verify=>correct is not falsified here.

**Protocol:** every attack copied model.py and edited ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical). `adversary same-spec` returned exit 0 (SAME) for all 13 + the control. `adversary weakness nagini sympy__sympy-15809 <f>` run 3-way concurrent (JVM+Z3 per check).

COMMAND (each): python -m swebench_unified.adversary weakness nagini sympy__sympy-15809 atk_N.py

### RESULTS (exit 2 = NOT-A-COUNTEREXAMPLE / spec rejected = good):
 atk_1  PREPATCH REPRO (stale `if len(operands)==0: raise EmptyReductionRejected()`) -> exit 2. prepatch bug reproduced and rejected.
 atk_2  drops the unchanged non-comparable rejection (control-flow-effect) -> exit 2. Nagini: `Assertion (not has_noncomparable... and not has_absorbing... and not canonical_reduction_defined) might not hold` at the ReductionUndefined Exsures -- i.e. Ensures(not has_noncomparable_operand) supplies the OBLIGATION, closing the hole a prior audit flagged as atk_2.
 atk_3  swallows the canonical-set failure, returns identity instead -> exit 2.
 atk_4  BOUNDARY: count<=1 folded into the identity branch -> exit 2.
 atk_5  BOUNDARY: single/aggregate swapped -> exit 2.
 atk_6  absorbing branch collapses to identity, not the annihilator -> exit 2.
 atk_7  A-LEG/EXCLUSIVITY: reads the two scan events as CONTAINMENT tests, so an annihilator-bearing collection is rejected rather than collapsing -> exit 2. The exclusivity Ensures on has_absorbing_operand is load-bearing, not decorative.
 atk_8  PARTIAL-DOMAIN: identity branch keyed on raw operand cardinality (len==0) instead of the canonical-set count -> exit 2. Nagini names exactly `Implies(canonical_count==0, Result()==identity)`.
 atk_9  UNGROUNDED-ORACLE/vacuous guard: nc raise hidden behind `identity == zero`, which the precondition forbids, so the raise is dead code -> exit 2. (Guarded self-calls going vacuous is a known failure mode; the spec catches it here.)
 atk_10 TERMINATION: diverges (while True) on the empty collection rather than returning identity -> exit 2. MustTerminate(2) at the method level rejects it.
 atk_11 A-LEG: nc first event raises ReductionUndefined (failures conflated) -> exit 2.
 atk_12 breaks the FIX itself: empty canonical set yields `single`, not identity -> exit 2.
 atk_13 A-LEG mirror of atk_11: undefined pass raises NonComparableOperand -> exit 2.

POSITIVE CONTROL /pc.py: `weakness` exit 0 (CANDIDATE: shares spec AND verifies, 22.9s) -- expected, it IS the gold impl. Per protocol I materialized its faithful refined patch (= patch.diff verbatim, the A3 guard deletion) and RAN the official harness:
  python -c 'run_resolve("sympy__sympy-15809", patch)'  ->  RESOLVED= True
  FAIL_TO_PASS: test_Min, test_Max both success; PASS_TO_PASS: all 10 success; FAIL_TO_FAIL/PASS_TO_FAIL empty.
So the one verifying impl's faithful patch DOES resolve -- no verify/correct divergence. (Note: only a WRONG verifying impl could break the gate; none existed.)

A-LEG AUDIT (my mandate) -- independently re-driven against the REAL callee, not taken from axiom_check.py. Cloned the upstream repository at base_commit 28d913d3 into scratch, applied patch.diff, drove sympy 1.4.dev directly, consuming the real `_new_args_filter` for the scan's first event: A3 (the fix): Min()==oo, Max()==-oo; scan([])==ok for both. Empty returns identity, never raises. MATCHES. A3b/A4 EXCLUSIVITY: Min(-oo,I)=-oo and Max(oo,I)=oo (scan=absorbing) vs Min(I,-oo)/Max(I,oo) raise ValueError (scan=noncomparable); also behind a comparable symbol, both orders. The constructor's observable equals the scan's FIRST event in all 8 cases.

Confirms these are first-decisive-event predicates, NOT containment tests -- and atk_7 shows the model would be UNFAITHFUL under the containment reading. A4b: reproduced 18/84 collections whose scan is CLEAN yet whose canonical-set pass FAILS (TypeError from Expr.`__ge__` via `_find_localzeros`/`_is_connected`) -- e.g. Min(x, x+I), Min(x,a,x+`2*I`). Matches meta.json's recorded 18 exactly. Asserted the key soundness property myself: scan clean => the reduction NEVER raises the scan's own comparability ValueError, so the two observations really are distinct. The leg is reachable, not dead.

This is precisely the G-PANEL-2 UNFAITHFUL finding ([x, x+I], canonical_count total => spec-too-strong), and the frozen model has since been repaired: canonical_count is now PARTIAL (Requires(canonical_reduction_defined)) with the definedness predicate + its Exsures/obligation pair carrying the leg. The old defect does not survive in this model. A3b obligation: Min/Max of I, (I,x), (zoo,1), nan, (x,I) -- scan=noncomparable and real=ValueError agree in all 10. A5/A6/A7: Min(x)=x (count 1 -> operand), Min(x,x)=x (collapses to 1), Min(x,a)=Min(a,x) (count 2 -> aggregate). All A-leg assertions passed.

The four axioms claim only their weakest empty-collection/non-negativity/exclusivity properties; none over-claims, and each Ensures I could attack (exclusivity via atk_7, partiality via atk_3/atk_13, count-vs-cardinality via atk_8) is load-bearing.

**REFINEMENT.MD AUDIT:** legs A1,A2,A7,A8 = R; A3 = R+I; A3b,A4,A4b,A5 = A-consumed; A6 = A-consumed+I. NO kind-3 (unexpressible-changed-op) leg, and deep_model_references is empty in meta.json, consistent with §B's "no A-reference deep model" claim -- correct, since the change is a control-flow deletion, not a string/numeric transform, so there is no deep model to mis-key. Every A-leg cites a real file:line in the UNCHANGED callees (`_new_args_filter` :521-523/:525-526, `_collapse_arguments` :373-506, `_find_localzeros` :536-560, `_is_connected` :552/:574, expr.py:295) and I confirmed each behaviourally above. The changed operation (A3) is modeled DIRECTLY as the absence of the leading raise, not axiomatized away -- the honest encoding.

CAVEAT (advisory, not a gate failure): the spec observes only cardinality + which decisive event fires + definedness + canonical count, so it cannot distinguish WHICH survivor `single` denotes or which aggregate is assembled (A7/A8 are pure R legs to opaque sentinels). A wrong impl returning the wrong survivor is outside the modeled abstraction. That is inherent to the sentinel refinement and is covered mechanically by G-CONF (100282 checks, 0 disagreements, all 6 branches hit) rather than by G-EQ; it is not a hole the A legs could close. Since the patch under specification is a pure guard deletion that touches none of that selection logic, the abstraction is adequate for THIS delta.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SPEC REGION INTEGRITY: `adversary same-spec nagini sympy__sympy-15809` on a byte-copy of the bundle model.py => exit 0 ("SAME"). Bundle model.py verifies under the pinned verifier: `scripts/nagini_verify.sh` => "Verification successful" (22.6s).

**WHAT I ATTACKED.** Faithfulness here means: for every operand collection, the modeled `lattice_reduce` (impl + the 4 @ContractOnly axioms' contracts) must agree with the real PATCHED `MinMaxBase.__new__` (miscellaneous.py:341). I built an independent harness () that, per input, reads the predicate values off the REAL unchanged callees (`_new_args_filter` for the scan's first decisive event; `_collapse_arguments`+`_find_localzeros` for definedness/count), evaluates the model impl on them, runs the real `Min`/`Max`, and then checks EVERY spec clause: the 4 axiom Ensures, the 4 outcome-decode clauses (identity/zero/single/aggregate decoded to cls.identity/cls.zero/list(args).pop()/the assembled aggregate), the exception-type bridge, and crucially BOTH obligation Ensures (`not has_noncomparable_operand` and `has_absorbing_operand or canonical_reduction_defined`), which are what a spec-too-strong defect would break.

### RESULTS (all 0 problems):
1. Broad differential, seed 20260815: 15,518 comparisons, 0 problems. Branch tally: identity 1079, zero 488, single 2561, aggregate 4483, reject 6669, undefined 238 (TypeError 178 / NotImplementedError 60) — all six branches live, so no branch is dead/unexercised.
2. Large fresh-seed fuzz (seed 777333, 30k fuzz collections/lattice): 63,518 comparisons, 0 problems.
3. Exotic-operand hunt (8,094 comparisons): ~60 hand-picked operand kinds — Interval, FiniteSet, Matrix, MatrixSymbol, ImageSet, S.Reals, relationals, And/Or/Not, Sum/Integral/Derivative/Limit, Order, sign, arg, conjugate, im/re, gamma/zeta/besselj/LambertW/polylog, factorial/binomial, KroneckerDelta/DiracDelta/Heaviside, floor/ceiling/frac/Mod, Piecewise with I/nan branches, Float('inf'/'nan'), oo+I, zoo+1, roots of negatives — alone, doubled, and crossed with 9 comparable controls. 0 problems.
4. Forged pathological nested nodes (bypassing `__new__` via Expr.`__new__` to plant cls.zero / I / x+I / cls.identity / empty INSIDE a nested node, which `_new_args_filter` re-yields WITHOUT re-checking comparability): 0 problems. This was my best spec-too-strong candidate and it holds — e.g. Max(forged Max(I,x)) has a CLEAN scan yet the real ctor raises TypeError, and the spec correctly predicts ReductionUndefined there (not a normal return), because `canonical_reduction_defined` is False. A scan-only spec would have been UNFAITHFUL here; the bundle's separate definedness axiom is exactly what saves it.

### Targeted clause-by-clause confirmations
- The load-bearing EXCLUSIVITY clause (`Implies(Result(), not has_noncomparable_operand)` on `has_absorbing_operand`) matches reality on both orders: Min(-oo,I)=-oo / Min(I,-oo) raises; Max(oo,I)=oo / Max(I,oo) raises; also behind a comparable symbol and with repeats. A containment reading would have been unfaithful on the first of each pair; the bundle gets it right.
- The PINNED behaviour: Min()==oo==Min.identity, Max()==-oo==Max.identity, scan clean, pass defined, count 0. Stable under 9 kwarg variants (evaluate=False/True, real, positive, integer, commutative, combinations, unknown kwarg) — empty->identity in all 18 cases, never a raise.
- Non-empty inputs reaching the count==0 identity branch (cls.identity-only operands, e.g. Min(oo), Min(oo,oo,oo)) all return cls.identity, matching the model's more-general `count==0 => identity` clause rather than only the empty case.
- **UNAXIOMATIZED TAIL:** over 10,181 inputs where scan is clean AND the pass is defined (so the spec's four-outcome totality clause FORBIDS raising), the real ctor raised 0 times. So `list(args).pop()` / `Expr.__new__` assembly never falsifies the totality clause — the spec is not too strong.
- DETERMINISM (@Pure soundness): `_find_localzeros` iterates a frozenset with id()-based comparisons, so I re-ran the full predicate+outcome vector under PYTHONHASHSEED=0/1/12345/999 — byte-identical JSON (414,735 bytes each), 0 differing keys across ~8.5k inputs/seed. The axioms are genuine functions of the operand list.
- **EXCEPTION BRIDGE:** SympifyError is a ValueError subclass, so sympify failures route to NonComparableOperand on BOTH the model and oracle side consistently — no hidden mismatch. The ReductionUndefined decode was checked against the pass's ACTUAL propagated type (TypeError vs NotImplementedError), not merely "it raised".
- Bundle's own axiom_check.py re-run against my worktree: exit 0, 6208 observations, 18 non-trivial undefined-pass collections — so the ReductionUndefined leg is reachable, not dead.

**NON-FINDING I EXPLICITLY CLEARED:** `evaluate=False` changes the outcome branch on 72/19,518 inputs (e.g. Min(Max(2,y), sqrt(2)) is `single` by default but `aggregate` with evaluate=False, since `_collapse_arguments` is skipped). This is NOT a faithfulness defect: `**assumptions` is outside the modeled signature (mapping.md §1 binds `lattice_reduce` to the collection + the four sentinels only), the axioms are read off the real callees in whichever mode the oracle runs, the F2P behaviour (empty->identity) is invariant under every kwarg I tried, and the patch touches none of this. The delta is a property of the unchanged `_collapse_arguments`, identical in base and patched.

**NON-VACUITY CONTROL:** model_prepatch.py shares the exact spec (same-spec exit 0) and FAILS the pinned verifier — "method only raises exceptions of types NonComparableOperand, ReductionUndefined" might not hold — so the spec genuinely senses the patch delta and my FAITHFUL verdict is not a rubber-stamp on a vacuous spec.

I also confirmed I did not commit the briefing's warned-against error: I used the patch-APPLIED worktree as the reference for the modeled function, so the empty-collection behaviour (Min()==oo) is agreement, not a divergence. Comparing against base would have manufactured a false UNFAITHFUL on exactly the patch delta.

**CONCLUSION:** no diverging input found; the spec is neither too strong nor drifted. VERDICT FAITHFUL. Residual risk is the usual finite-search one (the operand space is infinite), concentrated in operand kinds none of my ~60 exotic classes or the fuzz pool reached, but the two structurally-suspicious classes (unaxiomatized assembly tail, nested re-yield without re-check) were both probed directly and both hold. No bundle file was modified;

Counterexample / evidence:

```
none — no faithfulness counterexample exists on the evidence gathered; the spec is not too strong and does not drift from real repo behavior
```

**SPEC REGION INTEGRITY:** `adversary same-spec nagini sympy__sympy-15809` on a byte-copy of the bundle model.py => exit 0 ("SAME"). Bundle model.py verifies under the pinned verifier: `scripts/nagini_verify.sh` => "Verification successful" (22.6s).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. Judged the CONSUMER SPEC VIEW only = markers.spec_view(model.py, nagini/python backend) -- module docstring + 3 exception classes + axioms + pure + pre/post-conditions, impl region collapsed. I confirmed the elision is real: spec_view.txt lines 282-284 are exactly `# impl-start / ...  # implementation elided -- supplied by the consumer / # impl-end`. This matters here, because the impl region of model.py DOES name the edit shape verbatim (`(The stale guard \`if len(operands) == 0: raise EmptyReductionRejected()\` is absent: ...)`) and model_prepatch.py's impl region says `PRE-PATCH (stale): the reduction REJECTS the empty operand collection up front`. Neither reaches the consumer -- both live strictly inside impl-start/impl-end and are projected away. Had they been in a spec region this would have been LEAKAGE; they are not.

**NO RELAXATION IN THIS BUNDLE.** There is no RELAXED_LEAKAGE.md and meta.json has no `relaxed_leakage` key (checked: `'relaxed_leakage' in meta` -> False; meta keys are additional_change_sites, ax_apply_gold, axioms, base_commit, changed_files, ..., region_hashes, repo, schema_version, string_modeling, version). So I judged this as an ordinary strict-mode leakage review, not as an inherited disposition, and no unavoidability argument needed re-deriving.

GOLD EDIT (from the frozen row, data/swe_bench_verified/test.jsonl). sympy/functions/elementary/miscellaneous.py, MinMaxBase.`__new__` -- a pure DELETION of two lines, `if not args:` / `raise ValueError("The Max/Min functions must have arguments.")`, so control falls through to the pre-existing `if not args: return cls.identity` at :361 and Max()->-oo, Min()->oo. Confirmed against a throwaway worktree of the upstream repository at base_commit 28d913d3cead6c5646307ffa6540b21d65059dfd (read :339-370 pre-patch, then removed the worktree; all work in /tmp, bundle untouched).

PROBLEM_STATEMENT BASELINE (solver-visible; hints_text deliberately NOT used as a baseline). "Zero-argument Min() and Max() / Right now Min() and Max() with no arguments raise ValueError: The Max/Min functions must have arguments. It might be mathematically more convenient to have them return oo and -oo, respectively." So THREE facts are already public: (a) the empty-argument case is the subject; (b) it currently raises ValueError; (c) the desired results are oo for Min and -oo for Max. The spec's discriminating clause -- `Ensures(Implies(len(operands) == 0, Result() == identity))` plus the docstring's "for the maximum the identity is negative infinity; for the minimum it is positive infinity" -- is a restatement of (c), which is the public ASK, not the hidden edit.

MECHANICAL HALF -- MY OWN RUN, not the recorded gate. Re-ran leakage.screen(model.py, nagini backend, row.patch, row.problem_statement, row.test_patch): hard_failures = [] and warnings = [] (empty both). Independently:
- L1 gold-diff lines: changed_lines = ['if not args:', 'raise ValueError("The Max/Min functions must have arguments.")']; neither normalized form occurs in the normalized view. Substring sweep for `not args`, `raise ValueError`, `must have arguments`, `no arguments`, `zero-argument` -> 0 hits each.
- L1 diff markers ('@@', 'diff --git', '+++ ', '--- ', '\nindex ') -> absent.
- L2 patched path `sympy/functions/elementary/miscellaneous.py` and its dotted form -> 0 hits; `miscellaneous` -> 0. The only `sympy` occurrence in the view is the instance-id in the docstring header, a uniform convention across bundles, not edit-localization.
- L2/L4/L5 changed_symbols = {'real_root'} (harvested from the hunk section header, not from the edit) -- no spec-view identifier embeds it, no comment names it.
- L3 narration: leakage.`_NARRATION_RE`.findall(view) == [] (zero hits for bug/fix/patched/pre-patch/regression/previously/incorrectly/wrong/broken). Per my own prior note that G-LEAK trips on 'fixed'/'copy' in measure prose, I checked specifically: that false-positive mode does not fire on this bundle.
- Repo-symbol sweep beyond the screen: MinMaxBase, LatticeOp, `_new_args_filter`, `_find_localzeros`, `_collapse_arguments`, ShortCircuit, `_argset`, sympify, frozenset, `__new__`, Infinity, `Min`, `Max` -> ALL 0 occurrences in the view. The spec speaks only abstracted lattice vocabulary (operands / identity / annihilator / canonical set / survivors).
- Edit-SHAPE vocabulary sweep (the thing a lexical screen would miss): delete/remove/up front/early -> 0 hits. `stale` -> 1 hit and `guard` -> 1 hit, both benign on inspection: line 81 "Stands in for the `ValueError` a stale implementation raises on an empty collection" restates public fact (b) -- the problem_statement itself says the current code raises ValueError on no arguments -- and line 164 "the definedness axiom above guards this one's `Requires`" is Nagini contract vocabulary about canonical_count's precondition, nothing to do with the deleted `if not args` guard. Neither names the deletion, its file, its method, or its position.

SEMANTIC HALF -- IS THE DISCRIMINATOR LOAD-BEARING, AND IS ANYTHING BEYOND IT DISCLOSED? Ran the strip test in the sound direction: the two twins share a BYTE-IDENTICAL spec view (spec_view(model.py) == spec_view(model_prepatch.py) -> True; same_spec -> True; sha da4e821c5d4d...), so the entire gold/pre-patch difference lives in the elided impl and NO spec-region byte encodes which twin is which. I then confirmed the discriminator is genuinely load-bearing rather than decorative: `bash scripts/nagini_verify.sh gold.py` -> "Verification successful" (13.5s, exit 0), and the same spec against the PRE-patch impl -> "Verification failed ... Postcondition of lattice_reduce might not hold.

Assertion \"method only raises exceptions of types NonComparableOperand, ReductionUndefined\" might not hold" (exit 1). So the empty-collection clause discriminates, and it discriminates on exactly the public ask. Everything the view says beyond that clause is UNCHANGED behaviour being PRESERVED (the non-comparable-operand rejection, the reduction-undefined failure, the single/aggregate branches, the annihilator collapse) -- describing behaviour the gold patch does not touch is not disclosure of the gold edit, and none of it tells a solver where or what to delete.

**NO ARTIFACT ADDRESSED ME.** Ran leakage.reviewer_directed over every text file in the bundle -> zero hits in all of them, and a manual grep for `submit NO-LEAKAGE|record NO-LEAKAGE|the honest verdict|recording convention|dear auditor/reviewer/panel|leakage panel` across refinement.md, mapping.md, model.py, model_prepatch.py, axiom_check.py, conformance_check.py -> no matches. Nothing in this bundle tried to steer my recording.

TWO OBSERVATIONS FOR THE RECORD, NEITHER A LEAKAGE FINDING (out of my facet, flagged so they are not lost):
1. meta.json `region_hashes` is STALE w.r.t. the shipped model.py: I recomputed markers.region_hashes(model.py) and axioms / impl / pre-conditions / post-conditions / spec_view ALL mismatch the recorded values (only `pure` and the null `invariants` agree). It is not a spec_view-convention difference -- model_prepatch.py mismatches the same five. This is consistent with the recorded G-EQ / G-PANEL / G-PANEL-1/2/3 gates carrying sources.model.py digest 4004444a... while G-LEAK, G-VERIFY, G-AX, G-CONF, G-GOLD, G-MUT, G-PBT carry the current cc0269f5... -- i.e. the model was refined (meta.refinement_applied_3rd_pass documents a D4 spec-too-strong fix to canonical_count) and the region_hashes block plus the panel gate records were not recomputed. Because my mechanical half is my OWN re-run against the current cc0269f5 bytes, my verdict does not depend on the stale block.
2. Consequently the prior G-PANEL-3 record (agent_verdict NO-LEAKAGE, digest 4004444a) is a measurement of a superseded model. Mine is on the shipped one. Separately, G-PANEL-2 is recorded `fail` (faithfulness: canonical_count modeled TOTAL while the real `_find_localzeros` is PARTIAL on [x, x+I]) against that same stale digest -- a faithfulness question, not a leakage one, and not mine to re-dispose; noting only that my NO-LEAKAGE is scoped to leakage and asserts nothing about that gate.

**CONCLUSION.** The spec view discloses exactly the publicly-asked-for behaviour -- empty reduction returns the lattice identity, oo for Min / -oo for Max -- and nothing about the deletion that implements it: not the file, not MinMaxBase.`__new__`, not the `if not args` guard, not the error string, not the fact that the fix is a removal. NO-LEAKAGE.

**SCOPE.** Judged the CONSUMER SPEC VIEW only = markers.spec_view(model.py, nagini/python backend) -- module docstring + 3 exception classes + axioms + pure + pre/post-conditions, impl region collapsed. I confirmed the elision is real: spec_view.txt lines 282-284 are exactly `# impl-start / ...  # implementation elided -- supplied by the consumer / # impl-end`. This matters here, because the impl region of model.py DOES name the edit shape verbatim (`(The stale guard \`if len(operands) == 0: raise EmptyReductionRejected()\` is absent: ...)`) and model_prepatch.py's impl region says `PRE-PATCH (stale): the reduction REJECTS the empty operand collection up front`. Neither reaches the consumer -- both live strictly inside impl-start/impl-end and are projected away. Had they been in a spec region this would have been LEAKAGE; they are not.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
