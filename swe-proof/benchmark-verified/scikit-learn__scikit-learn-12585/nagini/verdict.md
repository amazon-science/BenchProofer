# P2 adversarial audit — scikit-learn__scikit-learn-12585

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_4.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -159,16 +159,10 @@
     if (not est.has_introspect) or est.is_class_object:
         if not permit_fallback:
             raise NotCloneableError()
-        # Atomic reproduction of a leaf. A class object has no internal
-        # parameter state, so its atomic copy is reference-identical (returned
-        # as the same reference). A non-class leaf carries state, so its atomic
-        # copy is a fresh, distinct object.
-        if est.is_class_object:
-            return est
-        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
-                                est.is_class_object)
-        return atomic_copy
-    # Genuine instance: take apart and rebuild into a fresh, distinct object.
+        # Atomic reproduction: return the SAME reference for every leaf
+        # (identity). The spec constrains identity only for the class-object
+        # disjunct; returning est for a non-class leaf is left free.
+        return est
     rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                         est.is_class_object)
     return rebuilt
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,19 +156,10 @@
             is_leaf(est) and permit_fallback is False)
     # post-conditions-end
     # impl-start
-    if (not est.has_introspect) or est.is_class_object:
+    if not est.has_introspect:
         if not permit_fallback:
             raise NotCloneableError()
-        # Atomic reproduction of a leaf. A class object has no internal
-        # parameter state, so its atomic copy is reference-identical (returned
-        # as the same reference). A non-class leaf carries state, so its atomic
-        # copy is a fresh, distinct object.
-        if est.is_class_object:
-            return est
-        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
-                                est.is_class_object)
-        return atomic_copy
-    # Genuine instance: take apart and rebuild into a fresh, distinct object.
+        return est
     rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                         est.is_class_object)
     return rebuilt
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -159,17 +159,14 @@
     if (not est.has_introspect) or est.is_class_object:
         if not permit_fallback:
             raise NotCloneableError()
-        # Atomic reproduction of a leaf. A class object has no internal
-        # parameter state, so its atomic copy is reference-identical (returned
-        # as the same reference). A non-class leaf carries state, so its atomic
-        # copy is a fresh, distinct object.
         if est.is_class_object:
             return est
         atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                 est.is_class_object)
         return atomic_copy
-    # Genuine instance: take apart and rebuild into a fresh, distinct object.
     rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                         est.is_class_object)
+    while True:
+        pass
     return rebuilt
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -156,20 +156,14 @@
             is_leaf(est) and permit_fallback is False)
     # post-conditions-end
     # impl-start
-    if (not est.has_introspect) or est.is_class_object:
-        if not permit_fallback:
-            raise NotCloneableError()
-        # Atomic reproduction of a leaf. A class object has no internal
-        # parameter state, so its atomic copy is reference-identical (returned
-        # as the same reference). A non-class leaf carries state, so its atomic
-        # copy is a fresh, distinct object.
+    leaf = (not est.has_introspect) or est.is_class_object
+    if leaf and not permit_fallback:
+        raise NotCloneableError()
+    if leaf:
         if est.is_class_object:
             return est
-        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
-                                est.is_class_object)
-        return atomic_copy
-    # Genuine instance: take apart and rebuild into a fresh, distinct object.
-    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
-                        est.is_class_object)
-    return rebuilt
+        return Candidate(est.is_aggregate, est.has_introspect,
+                         est.is_class_object)
+    return Candidate(est.is_aggregate, est.has_introspect,
+                     est.is_class_object)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -159,16 +159,8 @@
     if (not est.has_introspect) or est.is_class_object:
         if not permit_fallback:
             raise NotCloneableError()
-        # Atomic reproduction of a leaf. A class object has no internal
-        # parameter state, so its atomic copy is reference-identical (returned
-        # as the same reference). A non-class leaf carries state, so its atomic
-        # copy is a fresh, distinct object.
-        if est.is_class_object:
-            return est
-        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
-                                est.is_class_object)
-        return atomic_copy
-    # Genuine instance: take apart and rebuild into a fresh, distinct object.
+        return Candidate(est.is_aggregate, est.has_introspect,
+                         est.is_class_object)
     rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                         est.is_class_object)
     return rebuilt
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -159,17 +159,9 @@
     if (not est.has_introspect) or est.is_class_object:
         if not permit_fallback:
             raise NotCloneableError()
-        # Atomic reproduction of a leaf. A class object has no internal
-        # parameter state, so its atomic copy is reference-identical (returned
-        # as the same reference). A non-class leaf carries state, so its atomic
-        # copy is a fresh, distinct object.
         if est.is_class_object:
             return est
-        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
-                                est.is_class_object)
-        return atomic_copy
-    # Genuine instance: take apart and rebuild into a fresh, distinct object.
-    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
-                        est.is_class_object)
-    return rebuilt
+        return Candidate(est.is_aggregate, est.has_introspect,
+                         est.is_class_object)
+    return est
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -157,18 +157,7 @@
     # post-conditions-end
     # impl-start
     if (not est.has_introspect) or est.is_class_object:
-        if not permit_fallback:
-            raise NotCloneableError()
-        # Atomic reproduction of a leaf. A class object has no internal
-        # parameter state, so its atomic copy is reference-identical (returned
-        # as the same reference). A non-class leaf carries state, so its atomic
-        # copy is a fresh, distinct object.
-        if est.is_class_object:
-            return est
-        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
-                                est.is_class_object)
-        return atomic_copy
-    # Genuine instance: take apart and rebuild into a fresh, distinct object.
+        return est
     rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                         est.is_class_object)
     return rebuilt
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-12585.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A generic copy routine reproduces a parameterised object. A candidate is
  classified by three observable, mutually-relevant properties: whether it is a
  plain aggregate (a list/tuple/set), whether it exposes the parameter
  introspection capability used to take it apart and rebuild it, and whether it
  is itself a *class object* rather than an *instance* of one.

  The routine's contract is about which candidates may be taken apart and
  rebuilt and which must be reproduced atomically:

    * A class object is NEVER taken apart and rebuilt, EVEN WHEN it exposes the
      introspection capability (a class exposes that capability as an attribute,
      but it is unusable without an instance to bind to). It is treated as a
      leaf: when the caller permits a fallback copy it is reproduced atomically,
      and an atomic reproduction of a class object yields THE SAME object (a
      class has no internal parameter state to deep-copy, so its reproduction is
      reference-identical to the input). When the caller forbids the fallback,
      such a candidate is refused.

    * Likewise any candidate that does not expose the introspection capability
      is a leaf, with the same permit/forbid behaviour. Such a leaf is also
      reproduced atomically when the fallback is permitted; that atomic
      reproduction need not be reference-identical (an atomic copy of a
      state-bearing leaf — e.g. a value carrier — may yield a distinct object).
      Only the class-object leaf carries the additional identity guarantee.

    * Only a genuine instance — one that exposes the introspection capability
      and is NOT a class object (and is not a plain aggregate) — is taken apart
      and rebuilt, producing a FRESH, distinct object.

  The discriminating guarantee the desired behaviour adds: a class object, when
  the fallback copy is permitted, is reproduced to the SAME object reference
  (identity preserved), instead of being mis-routed into the take-apart/rebuild
  path (which would fail outright on a class and, if it did not, would yield a
  distinct object). The identity guarantee is specific to the class-object leaf;
  a non-class leaf is only required to be reproduced atomically (and refused when
  the fallback is forbidden), not reference-identically.

The candidate is modelled as a minimal class carrying only the three
dispatch-relevant boolean properties. The refusal of an un-copyable leaf when
the fallback is forbidden is a user-defined exception (a builtin exception in an
`Exsures` crashes the Nagini translator; mapping.md §2).

Reproducing a candidate is a bounded dispatch step: it MUST terminate and
actually deliver its result (or its refusal) — a total-correctness obligation,
carried as MustTerminate in the precondition. An implementation that computes
the right value but diverges before returning it (e.g. an infinite loop
inserted into the copy routine) would satisfy every value postcondition only
vacuously and would hang the copy routine's caller forever instead of
delivering the reproduced object.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Candidate:
    def __init__(self, is_aggregate: bool, has_introspect: bool,
                 is_class_object: bool) -> None:
        # Constructing a candidate is a bounded step (three field writes);
        # its measure (1) is strictly below reproduce's (2) so the allocation
        # inside the copy routine discharges the caller's obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.is_aggregate, 1 / 2) and  # type: ignore
                self.is_aggregate == is_aggregate)
        Ensures(Acc(self.has_introspect, 1 / 2) and  # type: ignore
                self.has_introspect == has_introspect)
        Ensures(Acc(self.is_class_object, 1 / 2) and  # type: ignore
                self.is_class_object == is_class_object)
        self.is_aggregate = is_aggregate        # type: bool
        self.has_introspect = has_introspect      # type: bool
        self.is_class_object = is_class_object    # type: bool

class NotCloneableError(Exception):
    """Signals that the candidate is a leaf that cannot be reproduced atomically
    because the caller forbade the fallback copy. Stands in for the `TypeError`
    the desired behaviour raises (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""
    pass

# axioms-start
# (no axiomatized callees. The only operation this specification observes is the
# routine's own dispatch decision and the identity of what it returns on the
# leaf / non-leaf branches. The take-apart/rebuild machinery that a genuine
# instance delegates to is unchanged and unobserved here beyond the fact that it
# yields a fresh, distinct object — modelled deeply by allocating one.)
# axioms-end

# pure-start
@Pure
def is_leaf(c: Candidate) -> bool:
    """A candidate is a leaf (reproduced atomically, never taken apart) iff it
    does not expose the introspection capability OR it is a class object. The
    class-object disjunct is the discriminating property of the desired
    behaviour: a class exposes the capability as an attribute yet must still be
    treated as a leaf."""
    Requires(Acc(c.has_introspect, 1 / 4) and Acc(c.is_class_object, 1 / 4))
    return (not c.has_introspect) or c.is_class_object
# pure-end

def reproduce(est: Candidate, permit_fallback: bool) -> Candidate:
    # pre-conditions-start
    # `est` is read-only (its classification is observed, never mutated): held
    # at fractional permission so the postcondition cannot be satisfied by
    # overwriting the input.
    Requires(Acc(est.is_aggregate, 1 / 2))
    Requires(Acc(est.has_introspect, 1 / 2))
    Requires(Acc(est.is_class_object, 1 / 2))
    # The reproduced-atomically path is the one the tested behaviour exercises;
    # the aggregate path is a separate concern, excluded here.
    Requires(est.is_aggregate is False)
    # TERMINATION (total correctness): reproducing a candidate is a bounded
    # dispatch — classify, then either refuse, return the same reference, or
    # allocate one fresh object. It must actually DELIVER its result (or its
    # refusal). Without this obligation a diverging implementation (e.g. one
    # that spins forever on the rebuild path before returning the correct
    # fresh object) satisfies every value postcondition vacuously while never
    # handing its caller the reproduced object.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(est.is_aggregate, 1 / 2))
    Ensures(Acc(est.has_introspect, 1 / 2))
    Ensures(Acc(est.is_class_object, 1 / 2))
    # The input is never mutated.
    Ensures(est.is_aggregate == Old(est.is_aggregate))
    Ensures(est.has_introspect == Old(est.has_introspect))
    Ensures(est.is_class_object == Old(est.is_class_object))
    # A leaf reachable normally requires the fallback to be permitted (otherwise
    # the routine refuses — see the Exsures clause).
    Ensures(Implies(is_leaf(est), permit_fallback is True))
    # Discriminating guarantee: a CLASS-OBJECT leaf, with the fallback
    # permitted, is reproduced to the SAME object reference (identity preserved)
    # — a class has no internal parameter state to copy. In particular a class
    # object is NOT taken apart and rebuilt into a distinct object. (A non-class
    # leaf is only reproduced atomically; its atomic copy may be a distinct
    # object, so identity is NOT asserted there.)
    Ensures(Implies(is_leaf(est) and permit_fallback and est.is_class_object,
                    Result() is est))
    # A genuine instance (not a leaf) is taken apart and rebuilt into a FRESH,
    # distinct object — never the input.
    Ensures(Implies(not is_leaf(est), Result() is not est))
    # The routine refuses EXACTLY when a leaf meets a forbidden fallback. The
    # input is left intact (fractional permission returned) on the refusal path.
    Exsures(NotCloneableError, Acc(est.is_aggregate, 1 / 2) and
            Acc(est.has_introspect, 1 / 2) and Acc(est.is_class_object, 1 / 2) and
            is_leaf(est) and permit_fallback is False)
    # post-conditions-end
    # impl-start
    if (not est.has_introspect) or est.is_class_object:
        if not permit_fallback:
            raise NotCloneableError()
        # Atomic reproduction of a leaf. A class object has no internal
        # parameter state, so its atomic copy is reference-identical (returned
        # as the same reference). A non-class leaf carries state, so its atomic
        # copy is a fresh, distinct object.
        if est.is_class_object:
            return est
        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                est.is_class_object)
        return atomic_copy
    # Genuine instance: take apart and rebuild into a fresh, distinct object.
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC/IMPL: reproduce(est, permit_fallback) models sklearn.base.clone(estimator, safe) with permit_fallback == not safe, over the non-aggregate domain (Requires est.is_aggregate is False). is_leaf(c) == (not c.has_introspect) or c.is_class_object models the gold leaf guard `not hasattr(estimator,'get_params') or isinstance(estimator, type)` (the one-line gold change is the added is_class_object/isinstance(...,type) disjunct). All 7 attacks share the byte-identical spec (adversary same-spec exit 0 for each); positive_control.py (= bundle model.py) verifies (nagini_verify exit 0). verifier env python; SBU_BENCHMARK_DIR=benchmark-verified.

COMMANDS (per attack): python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-12585 <atk>; resolve via harness.run_resolve(iid, patch, timeout=1800/1800, retries=1).

STRUCTURAL FREEDOM AXIS: the spec pins everything except ONE axis — the non-class leaf (not has_introspect & not is_class_object) with permit_fallback=True asserts NO identity, so an impl may return est (identity) OR a fresh object. atk_1 is the deliberate exploit of exactly this freedom (returns est for the ENTIRE leaf branch). Its faithful real patch is `return copy.deepcopy(estimator)` -> `return estimator` in clone's `if not safe:` leaf branch (differs from gold only for non-class state-bearing leaf PARAMS: arrays/sparse/functions, where gold deep-copies distinct and atk_1 shares the reference).

### Attack results
- atk_1 (atk_1.py) non-class-leaf identity exploit: weakness exit 0 = CANDIDATE (shares spec AND verifies, 19.2s). Materialized faithful patch patch_atk_1.diff and RAN run_resolve TWICE independently: completed=True resolved=True attempts=1 flaky=False (both runs, run_ids sbu-eqaudit-atk1 and sbu-eqaudit-atk1confirm). RESOLVES. No P2P/F2P test observes leaf-param distinctness: test_clone/_2 assert only top-level `selector is not new_selector` (top object is a non-leaf, reconstructed fresh either way); test_clone_empty_array/_sparse_matrices assert assert_array_equal (VALUE equality, not identity/distinctness); test_clone_nan asserts identity which holds both ways (deepcopy(nan) is nan). F2P test_clone_estimator_types asserts clf.empty is clf2.empty for a CLASS param — preserved (class leaf still returns identity under both gold and atk_1). Hence the spec's non-class-leaf identity freedom is genuinely unobservable by the tests => sound.
- atk_2 (prepatch bug, drops is_class_object disjunct): weakness exit 2 = NOT-A-COUNTEREXAMPLE, genuine 'verification failed' (violates Implies(is_leaf, permit_fallback) & class-leaf identity). Prepatch reproduced.
- atk_3 (control-flow-effect: correct values then `while True: pass` on rebuild path): weakness exit 2, genuine verification failed — MustTerminate(2) obligation leaked (closes the diverging verified-but-hangs gap noted in refinement.md A8).
- atk_4 (ungrounded-oracle echo: gold semantics, control flow rearranged via `leaf` local): weakness exit 0 = CANDIDATE; faithful patch = gold patch verbatim; run_resolve completed=True resolved=True. Expected resolving echo, NOT a weakness.
- atk_5 (boundary: class-object leaf returns a FRESH Candidate): weakness exit 2, genuine verification failed — violates Implies(is_leaf & permit_fallback & is_class_object, Result() is est).
- atk_6 (non-leaf returns est): weakness exit 2, genuine verification failed — violates Implies(not is_leaf, Result() is not est).
- atk_7 (partial-domain: leaf never refuses when fallback forbidden): weakness exit 2, genuine verification failed — violates Exsures/Implies(is_leaf, permit_fallback is True).

REFINEMENT.MD AUDIT: legs A1,A2,A3,A5,A7,A8 are R (or R+I) refinements; A4 and A6 are A-reference (deep model of the changed dispatch predicate + per-disjunct copy.deepcopy fidelity), NO consumed @ContractOnly axiom, NO kind-3 (unexpressible-changed-op) leg. A-reference correspondence independently re-verified: axiom_check.py exit 0 (model is_leaf == real guard on 10 cases; copy.deepcopy(cls) is cls on 7 classes; copy.deepcopy(obj) is not obj on 4 non-class leaves; F2P identity end-to-end). Own spot-check confirmed copy.deepcopy(class) is class (identity), copy.deepcopy(np.array) is distinct+value-equal, copy.deepcopy(nan) is nan. The A-legs faithfully match the real clone callee ingredients.

VERDICT: SOUND. 7 distinct attacks run (2 genuine CANDIDATEs: atk_1 the free-axis exploit + atk_4 the echo). Every verifying candidate's materialized faithful patch RESOLVED under the official harness (atk_1 confirmed twice). No verify-but-not-resolved impl exists on the probed axes; the single behavioral freedom the spec leaves (non-class-leaf identity) is provably unobservable by the F2P+22 P2P tests. No spec weakness exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_4.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-12585.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A generic copy routine reproduces a parameterised object. A candidate is
  classified by three observable, mutually-relevant properties: whether it is a
  plain aggregate (a list/tuple/set), whether it exposes the parameter
  introspection capability used to take it apart and rebuild it, and whether it
  is itself a *class object* rather than an *instance* of one.

  The routine's contract is about which candidates may be taken apart and
  rebuilt and which must be reproduced atomically:

    * A class object is NEVER taken apart and rebuilt, EVEN WHEN it exposes the
      introspection capability (a class exposes that capability as an attribute,
      but it is unusable without an instance to bind to). It is treated as a
      leaf: when the caller permits a fallback copy it is reproduced atomically,
      and an atomic reproduction of a class object yields THE SAME object (a
      class has no internal parameter state to deep-copy, so its reproduction is
      reference-identical to the input). When the caller forbids the fallback,
      such a candidate is refused.

    * Likewise any candidate that does not expose the introspection capability
      is a leaf, with the same permit/forbid behaviour. Such a leaf is also
      reproduced atomically when the fallback is permitted; that atomic
      reproduction need not be reference-identical (an atomic copy of a
      state-bearing leaf — e.g. a value carrier — may yield a distinct object).
      Only the class-object leaf carries the additional identity guarantee.

    * Only a genuine instance — one that exposes the introspection capability
      and is NOT a class object (and is not a plain aggregate) — is taken apart
      and rebuilt, producing a FRESH, distinct object.

  The discriminating guarantee the desired behaviour adds: a class object, when
  the fallback copy is permitted, is reproduced to the SAME object reference
  (identity preserved), instead of being mis-routed into the take-apart/rebuild
  path (which would fail outright on a class and, if it did not, would yield a
  distinct object). The identity guarantee is specific to the class-object leaf;
  a non-class leaf is only required to be reproduced atomically (and refused when
  the fallback is forbidden), not reference-identically.

The candidate is modelled as a minimal class carrying only the three
dispatch-relevant boolean properties. The refusal of an un-copyable leaf when
the fallback is forbidden is a user-defined exception (a builtin exception in an
`Exsures` crashes the Nagini translator; mapping.md §2).

Reproducing a candidate is a bounded dispatch step: it MUST terminate and
actually deliver its result (or its refusal) — a total-correctness obligation,
carried as MustTerminate in the precondition. An implementation that computes
the right value but diverges before returning it (e.g. an infinite loop
inserted into the copy routine) would satisfy every value postcondition only
vacuously and would hang the copy routine's caller forever instead of
delivering the reproduced object.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Candidate:
    def __init__(self, is_aggregate: bool, has_introspect: bool,
                 is_class_object: bool) -> None:
        # Constructing a candidate is a bounded step (three field writes);
        # its measure (1) is strictly below reproduce's (2) so the allocation
        # inside the copy routine discharges the caller's obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.is_aggregate, 1 / 2) and  # type: ignore
                self.is_aggregate == is_aggregate)
        Ensures(Acc(self.has_introspect, 1 / 2) and  # type: ignore
                self.has_introspect == has_introspect)
        Ensures(Acc(self.is_class_object, 1 / 2) and  # type: ignore
                self.is_class_object == is_class_object)
        self.is_aggregate = is_aggregate        # type: bool
        self.has_introspect = has_introspect      # type: bool
        self.is_class_object = is_class_object    # type: bool

class NotCloneableError(Exception):
    """Signals that the candidate is a leaf that cannot be reproduced atomically
    because the caller forbade the fallback copy. Stands in for the `TypeError`
    the desired behaviour raises (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""
    pass

# axioms-start
# (no axiomatized callees. The only operation this specification observes is the
# routine's own dispatch decision and the identity of what it returns on the
# leaf / non-leaf branches. The take-apart/rebuild machinery that a genuine
# instance delegates to is unchanged and unobserved here beyond the fact that it
# yields a fresh, distinct object — modelled deeply by allocating one.)
# axioms-end

# pure-start
@Pure
def is_leaf(c: Candidate) -> bool:
    """A candidate is a leaf (reproduced atomically, never taken apart) iff it
    does not expose the introspection capability OR it is a class object. The
    class-object disjunct is the discriminating property of the desired
    behaviour: a class exposes the capability as an attribute yet must still be
    treated as a leaf."""
    Requires(Acc(c.has_introspect, 1 / 4) and Acc(c.is_class_object, 1 / 4))
    return (not c.has_introspect) or c.is_class_object
# pure-end

def reproduce(est: Candidate, permit_fallback: bool) -> Candidate:
    # pre-conditions-start
    # `est` is read-only (its classification is observed, never mutated): held
    # at fractional permission so the postcondition cannot be satisfied by
    # overwriting the input.
    Requires(Acc(est.is_aggregate, 1 / 2))
    Requires(Acc(est.has_introspect, 1 / 2))
    Requires(Acc(est.is_class_object, 1 / 2))
    # The reproduced-atomically path is the one the tested behaviour exercises;
    # the aggregate path is a separate concern, excluded here.
    Requires(est.is_aggregate is False)
    # TERMINATION (total correctness): reproducing a candidate is a bounded
    # dispatch — classify, then either refuse, return the same reference, or
    # allocate one fresh object. It must actually DELIVER its result (or its
    # refusal). Without this obligation a diverging implementation (e.g. one
    # that spins forever on the rebuild path before returning the correct
    # fresh object) satisfies every value postcondition vacuously while never
    # handing its caller the reproduced object.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(est.is_aggregate, 1 / 2))
    Ensures(Acc(est.has_introspect, 1 / 2))
    Ensures(Acc(est.is_class_object, 1 / 2))
    # The input is never mutated.
    Ensures(est.is_aggregate == Old(est.is_aggregate))
    Ensures(est.has_introspect == Old(est.has_introspect))
    Ensures(est.is_class_object == Old(est.is_class_object))
    # A leaf reachable normally requires the fallback to be permitted (otherwise
    # the routine refuses — see the Exsures clause).
    Ensures(Implies(is_leaf(est), permit_fallback is True))
    # Discriminating guarantee: a CLASS-OBJECT leaf, with the fallback
    # permitted, is reproduced to the SAME object reference (identity preserved)
    # — a class has no internal parameter state to copy. In particular a class
    # object is NOT taken apart and rebuilt into a distinct object. (A non-class
    # leaf is only reproduced atomically; its atomic copy may be a distinct
    # object, so identity is NOT asserted there.)
    Ensures(Implies(is_leaf(est) and permit_fallback and est.is_class_object,
                    Result() is est))
    # A genuine instance (not a leaf) is taken apart and rebuilt into a FRESH,
    # distinct object — never the input.
    Ensures(Implies(not is_leaf(est), Result() is not est))
    # The routine refuses EXACTLY when a leaf meets a forbidden fallback. The
    # input is left intact (fractional permission returned) on the refusal path.
    Exsures(NotCloneableError, Acc(est.is_aggregate, 1 / 2) and
            Acc(est.has_introspect, 1 / 2) and Acc(est.is_class_object, 1 / 2) and
            is_leaf(est) and permit_fallback is False)
    # post-conditions-end
    # impl-start
    if (not est.has_introspect) or est.is_class_object:
        if not permit_fallback:
            raise NotCloneableError()
        # Atomic reproduction of a leaf. A class object has no internal
        # parameter state, so its atomic copy is reference-identical (returned
        # as the same reference). A non-class leaf carries state, so its atomic
        # copy is a fresh, distinct object.
        if est.is_class_object:
            return est
        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                est.is_class_object)
        return atomic_copy
    # Genuine instance: take apart and rebuild into a fresh, distinct object.
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC/IMPL: reproduce(est, permit_fallback) models sklearn.base.clone(estimator, safe) with permit_fallback == not safe, over the non-aggregate domain (Requires est.is_aggregate is False). is_leaf(c) == (not c.has_introspect) or c.is_class_object models the gold leaf guard `not hasattr(estimator,'get_params') or isinstance(estimator, type)` (the one-line gold change is the added is_class_object/isinstance(...,type) disjunct). All 7 attacks share the byte-identical spec (adversary same-spec exit 0 for each); positive_control.py (= bundle model.py) verifies (nagini_verify exit 0). verifier env python; SBU_BENCHMARK_DIR=benchmark-verified.

COMMANDS (per attack): python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-12585 <atk>; resolve via harness.run_resolve(iid, patch, timeout=1800/1800, retries=1).

STRUCTURAL FREEDOM AXIS: the spec pins everything except ONE axis — the non-class leaf (not has_introspect & not is_class_object) with permit_fallback=True asserts NO identity, so an impl may return est (identity) OR a fresh object. atk_1 is the deliberate exploit of exactly this freedom (returns est for the ENTIRE leaf branch). Its faithful real patch is `return copy.deepcopy(estimator)` -> `return estimator` in clone's `if not safe:` leaf branch (differs from gold only for non-class state-bearing leaf PARAMS: arrays/sparse/functions, where gold deep-copies distinct and atk_1 shares the reference).

### Attack results
- atk_1 (atk_1.py) non-class-leaf identity exploit: weakness exit 0 = CANDIDATE (shares spec AND verifies, 19.2s). Materialized faithful patch patch_atk_1.diff and RAN run_resolve TWICE independently: completed=True resolved=True attempts=1 flaky=False (both runs, run_ids sbu-eqaudit-atk1 and sbu-eqaudit-atk1confirm). RESOLVES. No P2P/F2P test observes leaf-param distinctness: test_clone/_2 assert only top-level `selector is not new_selector` (top object is a non-leaf, reconstructed fresh either way); test_clone_empty_array/_sparse_matrices assert assert_array_equal (VALUE equality, not identity/distinctness); test_clone_nan asserts identity which holds both ways (deepcopy(nan) is nan). F2P test_clone_estimator_types asserts clf.empty is clf2.empty for a CLASS param — preserved (class leaf still returns identity under both gold and atk_1). Hence the spec's non-class-leaf identity freedom is genuinely unobservable by the tests => sound.
- atk_2 (prepatch bug, drops is_class_object disjunct): weakness exit 2 = NOT-A-COUNTEREXAMPLE, genuine 'verification failed' (violates Implies(is_leaf, permit_fallback) & class-leaf identity). Prepatch reproduced.
- atk_3 (control-flow-effect: correct values then `while True: pass` on rebuild path): weakness exit 2, genuine verification failed — MustTerminate(2) obligation leaked (closes the diverging verified-but-hangs gap noted in refinement.md A8).
- atk_4 (ungrounded-oracle echo: gold semantics, control flow rearranged via `leaf` local): weakness exit 0 = CANDIDATE; faithful patch = gold patch verbatim; run_resolve completed=True resolved=True. Expected resolving echo, NOT a weakness.
- atk_5 (boundary: class-object leaf returns a FRESH Candidate): weakness exit 2, genuine verification failed — violates Implies(is_leaf & permit_fallback & is_class_object, Result() is est).
- atk_6 (non-leaf returns est): weakness exit 2, genuine verification failed — violates Implies(not is_leaf, Result() is not est).
- atk_7 (partial-domain: leaf never refuses when fallback forbidden): weakness exit 2, genuine verification failed — violates Exsures/Implies(is_leaf, permit_fallback is True).

REFINEMENT.MD AUDIT: legs A1,A2,A3,A5,A7,A8 are R (or R+I) refinements; A4 and A6 are A-reference (deep model of the changed dispatch predicate + per-disjunct copy.deepcopy fidelity), NO consumed @ContractOnly axiom, NO kind-3 (unexpressible-changed-op) leg. A-reference correspondence independently re-verified: axiom_check.py exit 0 (model is_leaf == real guard on 10 cases; copy.deepcopy(cls) is cls on 7 classes; copy.deepcopy(obj) is not obj on 4 non-class leaves; F2P identity end-to-end). Own spot-check confirmed copy.deepcopy(class) is class (identity), copy.deepcopy(np.array) is distinct+value-equal, copy.deepcopy(nan) is nan. The A-legs faithfully match the real clone callee ingredients.

VERDICT: SOUND. 7 distinct attacks run (2 genuine CANDIDATEs: atk_1 the free-axis exploit + atk_4 the echo). Every verifying candidate's materialized faithful patch RESOLVED under the official harness (atk_1 confirmed twice). No verify-but-not-resolved impl exists on the probed axes; the single behavioral freedom the spec leaves (non-class-leaf identity) is provably unobservable by the F2P+22 P2P tests. No spec weakness exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical (same-spec exit 0; prepatch shares spec, differs only in impl). Model verifies under Nagini (18s); prepatch fails exactly at the discriminating postcondition Implies(is_leaf(est), permit_fallback is True). Checked all four spec obligations against real clone at base_commit bfc4a56 / gold 24e46410bd:
(1) leaf normal => permit_fallback: faithful (leaf + safe=True raises TypeError; permit_fallback = not safe).

(2) class-leaf + permit => Result() is est: faithful and robust. Stress-tested copy.deepcopy(cls) is cls across builtins, metaclasses, classes defining __deepcopy__/__reduce__/__reduce_ex__, enums — all identity. Mechanism confirmed: copy.deepcopy dispatches issubclass(type(x),type) -> _deepcopy_atomic BEFORE __deepcopy__, so no class-object can escape identity. Identity clause correctly SCOPED to is_class_object; non-class leaves assert no identity, faithfully modeling copy.deepcopy returning distinct objects (the prior TOO-STRONG 'identity for all leaves' defect is genuinely fixed and validated per-disjunct by axiom_check.py).

(3) non-leaf => Result() is not est: faithful for the entire realistic domain — klass(**params) allocates a fresh object for every BaseEstimator subclass (none override __new__), matching the P2P test_clone assertion 'selector is not new_selector'.
Exsures (leaf + forbidden fallback => refuse) matches real safe=True TypeError; MustTerminate(2) matches clone's bounded non-aggregate dispatch (closes the G-PANEL-1 divergence gap).
Toolkit: same-spec exit 0, nagini_verify exit 0, axiom_check.py exit 0 (G-AX SOUND on 10 classification cases + 7 class-identity + 4 non-class-distinct). No spec drift / no too-strong defect found.

(1) leaf normal => permit_fallback: faithful (leaf + safe=True raises TypeError; permit_fallback = not safe).

(2) class-leaf + permit => Result() is est: faithful and robust. Stress-tested copy.deepcopy(cls) is cls across builtins, metaclasses, classes defining __deepcopy__/__reduce__/__reduce_ex__, enums — all identity. Mechanism confirmed: copy.deepcopy dispatches issubclass(type(x),type) -> _deepcopy_atomic BEFORE __deepcopy__, so no class-object can escape identity. Identity clause correctly SCOPED to is_class_object; non-class leaves assert no identity, faithfully modeling copy.deepcopy returning distinct objects (the prior TOO-STRONG 'identity for all leaves' defect is genuinely fixed and validated per-disjunct by axiom_check.py).

(3) non-leaf => Result() is not est: faithful for the entire realistic domain — klass(**params) allocates a fresh object for every BaseEstimator subclass (none override __new__), matching the P2P test_clone assertion 'selector is not new_selector'.
Exsures (leaf + forbidden fallback => refuse) matches real safe=True TypeError; MustTerminate(2) matches clone's bounded non-aggregate dispatch (closes the G-PANEL-1 divergence gap).
Toolkit: same-spec exit 0, nagini_verify exit 0, axiom_check.py exit 0 (G-AX SOUND on 10 classification cases + 7 class-identity + 4 non-class-distinct). No spec drift / no too-strong defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py docstring + Candidate/NotCloneableError/is_leaf decls + reproduce pre/post/exsures (impl elided). Confirmed frozen spec: same_spec(model, model_prepatch)==True. Mechanical leakage.screen() passes clean (no diff markers, no patched file/module path, no narration term, no symbol echo); meta G-LEAK status=pass, no relaxed_leakage flag. Substantive test: the gold edit is the added `or isinstance(estimator, type)` disjunct in clone's leaf guard — and the PUBLIC problem_statement already discloses this verbatim in its 'Possible fix' section: `elif not hasattr(estimator, 'get_params') or isinstance(estimator, type):` (byte-identical to the gold-patch added line). Thus every discriminating fact the spec view carries (class objects treated as leaf, class-object identity under fallback copy) is downstream of what the task itself already gives away; nothing exceeds the problem_statement. Spec view uses only abstract carriers (reproduce/Candidate/is_leaf/has_introspect/is_class_object/permit_fallback) and never names sklearn/base.py, clone, or get_params. The lexical near-echo `NotCloneableError` (embeds 'clone') is not a leak: `clone` is explicitly public in the problem statement (`from sklearn.base import clone`), so it is exempt under the 'beyond problem_statement' bar. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
