# P2 adversarial audit — sympy__sympy-20154

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,35 +90,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # The live working value the walk advances IN PLACE across steps: it starts
-    # before the first step and is incremented one step at a time (never
-    # recomputed from scratch), exactly as the enumerator advances its single
-    # working record from one state to the next.
-    work = 0
-    i = 0
-    while i < steps:
-        # invariants-start
-        Invariant(0 <= i and i <= steps)
-        Invariant(Acc(list_pred(result)))
-        Invariant(len(result) == i)
-        # The working value carries the running state from the previous step.
-        Invariant(work == i)
-        # Every already-gathered record holds the snapshot of its own step --
-        # an INDEPENDENT value that subsequent steps never disturb.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == state_at(k)))))
-        # The loop consumes the termination obligation: steps - i is the
-        # strictly decreasing, bounded-below measure.
-        Invariant(MustTerminate(steps - i + 1))
-        # invariants-end
-        # Advance the working state in place by one step (the enumerator's
-        # mutation step): the record now holds the state for step i.
-        work = work + 1
-        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
-        # step): the current value is recorded by value, so later mutations of
-        # the working state leave this gathered record untouched.
-        snap = work
-        result.append(snap)
-        i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,35 +90,19 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # The live working value the walk advances IN PLACE across steps: it starts
-    # before the first step and is incremented one step at a time (never
-    # recomputed from scratch), exactly as the enumerator advances its single
-    # working record from one state to the next.
     work = 0
     i = 0
     while i < steps:
-        # invariants-start
         Invariant(0 <= i and i <= steps)
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == i)
-        # The working value carries the running state from the previous step.
         Invariant(work == i)
-        # Every already-gathered record holds the snapshot of its own step --
-        # an INDEPENDENT value that subsequent steps never disturb.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == state_at(k)))))
-        # The loop consumes the termination obligation: steps - i is the
-        # strictly decreasing, bounded-below measure.
+            result[k] == k))))
         Invariant(MustTerminate(steps - i + 1))
-        # invariants-end
-        # Advance the working state in place by one step (the enumerator's
-        # mutation step): the record now holds the state for step i.
-        work = work + 1
-        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
-        # step): the current value is recorded by value, so later mutations of
-        # the working state leave this gathered record untouched.
         snap = work
         result.append(snap)
+        work = work + 1
         i = i + 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,34 +90,18 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # The live working value the walk advances IN PLACE across steps: it starts
-    # before the first step and is incremented one step at a time (never
-    # recomputed from scratch), exactly as the enumerator advances its single
-    # working record from one state to the next.
     work = 0
     i = 0
     while i < steps:
-        # invariants-start
         Invariant(0 <= i and i <= steps)
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == i)
-        # The working value carries the running state from the previous step.
         Invariant(work == i)
-        # Every already-gathered record holds the snapshot of its own step --
-        # an INDEPENDENT value that subsequent steps never disturb.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == state_at(k)))))
-        # The loop consumes the termination obligation: steps - i is the
-        # strictly decreasing, bounded-below measure.
         Invariant(MustTerminate(steps - i + 1))
-        # invariants-end
-        # Advance the working state in place by one step (the enumerator's
-        # mutation step): the record now holds the state for step i.
         work = work + 1
-        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
-        # step): the current value is recorded by value, so later mutations of
-        # the working state leave this gathered record untouched.
         snap = work
+        if i == 0:
+            snap = 999
         result.append(snap)
         i = i + 1
     return result
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,33 +90,15 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # The live working value the walk advances IN PLACE across steps: it starts
-    # before the first step and is incremented one step at a time (never
-    # recomputed from scratch), exactly as the enumerator advances its single
-    # working record from one state to the next.
     work = 0
     i = 0
     while i < steps:
-        # invariants-start
         Invariant(0 <= i and i <= steps)
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == i)
-        # The working value carries the running state from the previous step.
-        Invariant(work == i)
-        # Every already-gathered record holds the snapshot of its own step --
-        # an INDEPENDENT value that subsequent steps never disturb.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == state_at(k)))))
-        # The loop consumes the termination obligation: steps - i is the
-        # strictly decreasing, bounded-below measure.
+        Invariant(work == 2 * i)
         Invariant(MustTerminate(steps - i + 1))
-        # invariants-end
-        # Advance the working state in place by one step (the enumerator's
-        # mutation step): the record now holds the state for step i.
-        work = work + 1
-        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
-        # step): the current value is recorded by value, so later mutations of
-        # the working state leave this gathered record untouched.
+        work = work + 2
         snap = work
         result.append(snap)
         i = i + 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,35 +90,27 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # The live working value the walk advances IN PLACE across steps: it starts
-    # before the first step and is incremented one step at a time (never
-    # recomputed from scratch), exactly as the enumerator advances its single
-    # working record from one state to the next.
     work = 0
     i = 0
     while i < steps:
-        # invariants-start
         Invariant(0 <= i and i <= steps)
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == i)
-        # The working value carries the running state from the previous step.
         Invariant(work == i)
-        # Every already-gathered record holds the snapshot of its own step --
-        # an INDEPENDENT value that subsequent steps never disturb.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == state_at(k)))))
-        # The loop consumes the termination obligation: steps - i is the
-        # strictly decreasing, bounded-below measure.
         Invariant(MustTerminate(steps - i + 1))
-        # invariants-end
-        # Advance the working state in place by one step (the enumerator's
-        # mutation step): the record now holds the state for step i.
         work = work + 1
-        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
-        # step): the current value is recorded by value, so later mutations of
-        # the working state leave this gathered record untouched.
         snap = work
         result.append(snap)
         i = i + 1
+    j = 0
+    while j < len(result):
+        Invariant(0 <= j and j <= len(result))
+        Invariant(Acc(list_pred(result)))
+        Invariant(len(result) == steps)
+        Invariant(MustTerminate(len(result) - j + 1))
+        result[j] = work
+        j = j + 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,35 +90,15 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # The live working value the walk advances IN PLACE across steps: it starts
-    # before the first step and is incremented one step at a time (never
-    # recomputed from scratch), exactly as the enumerator advances its single
-    # working record from one state to the next.
-    work = 0
     i = 0
     while i < steps:
-        # invariants-start
         Invariant(0 <= i and i <= steps)
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == i)
-        # The working value carries the running state from the previous step.
-        Invariant(work == i)
-        # Every already-gathered record holds the snapshot of its own step --
-        # an INDEPENDENT value that subsequent steps never disturb.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == state_at(k)))))
-        # The loop consumes the termination obligation: steps - i is the
-        # strictly decreasing, bounded-below measure.
         Invariant(MustTerminate(steps - i + 1))
-        # invariants-end
-        # Advance the working state in place by one step (the enumerator's
-        # mutation step): the record now holds the state for step i.
-        work = work + 1
-        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
-        # step): the current value is recorded by value, so later mutations of
-        # the working state leave this gathered record untouched.
-        snap = work
-        result.append(snap)
+        result.append(state_at(i))
         i = i + 1
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,35 +90,7 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # The live working value the walk advances IN PLACE across steps: it starts
-    # before the first step and is incremented one step at a time (never
-    # recomputed from scratch), exactly as the enumerator advances its single
-    # working record from one state to the next.
-    work = 0
-    i = 0
-    while i < steps:
-        # invariants-start
-        Invariant(0 <= i and i <= steps)
-        Invariant(Acc(list_pred(result)))
-        Invariant(len(result) == i)
-        # The working value carries the running state from the previous step.
-        Invariant(work == i)
-        # Every already-gathered record holds the snapshot of its own step --
-        # an INDEPENDENT value that subsequent steps never disturb.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == state_at(k)))))
-        # The loop consumes the termination obligation: steps - i is the
-        # strictly decreasing, bounded-below measure.
-        Invariant(MustTerminate(steps - i + 1))
-        # invariants-end
-        # Advance the working state in place by one step (the enumerator's
-        # mutation step): the record now holds the state for step i.
-        work = work + 1
-        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
-        # step): the current value is recorded by value, so later mutations of
-        # the working state leave this gathered record untouched.
-        snap = work
-        result.append(snap)
-        i = i + 1
+    while True:
+        result = result
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-20154.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An enumerator walks a sequence of states, advancing a single working value as
  it goes, and hands out one record per step. The desired contract is that the
  sequence of records HANDED OUT, when gathered into a list, faithfully records
  the state at the moment of each step:

    * record number i, once gathered, reflects the working state AS IT WAS at
      step i -- not as it later became;
    * because successive steps genuinely change the working state, the gathered
      records have pairwise-different values: gathering an n-step walk yields n
      records that increase step by step, recovering the full per-step history.

  The defective behaviour this rules out is handing out a live alias of the
  working state on every step, so that every gathered record tracks the SAME
  evolving state. Under that defect, once the walk has finished all gathered
  records read back as the FINAL state, and the per-step history is lost
  (gathering an n-step walk would yield n identical records).

Gathering an n-step walk is a bounded computation: the gather MUST terminate
and actually deliver its list of records (a total-correctness obligation,
carried as MustTerminate in the precondition). Nagini is a partial-correctness
verifier by default, so without the obligation a non-terminating
implementation would satisfy every value postcondition only vacuously and
would never hand the gathered records to the caller.

The working state is modelled by an integer; the gathered records by a
`List[int]` whose element i is the value recorded for step i (`str` indexing
and rich containers are unavailable in Nagini; the multiplicity mapping the
real enumerator maintains is abstracted to its per-step changing value). The
walk's value at step i is pinned by a pure spec function `state_at`, chosen
strictly increasing so successive steps genuinely differ -- which is exactly
what an aliasing enumerator (whose gathered records all collapse to the final
value) cannot reproduce. No callee is axiomatized: gathering the walk and
recording an independent per-step snapshot are pure value/structure logic,
modelled deeply (the real-Python record-duplication primitive the enumerator
builds on is validated out-of-band by axiom_check.py / G-AX as an A-reference).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: gathering the walk and recording an independent per-step
# snapshot are pure value/structure logic, modelled deeply. The
# record-duplication primitive the enumerator builds on is validated against
# its real Python semantics out-of-band by axiom_check.py (G-AX) as an
# A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def state_at(i: int) -> int:
    """The working value recorded for step i. Successive steps genuinely change
    it, so the per-step values are pairwise distinct; modelled as the
    strictly-increasing identity i+1 so step i differs from step j."""
    Requires(i >= 0)
    Ensures(Result() == i + 1)
    return i + 1
# pure-end


def gather_walk(steps: int) -> List[int]:
    # pre-conditions-start
    Requires(steps >= 0)
    # TERMINATION: the gather must actually ANSWER — walking a finite number
    # of steps and recording one value per step is a bounded computation.
    # Nagini is a partial-correctness verifier by default, so without this
    # obligation a non-terminating implementation (e.g. an endless loop)
    # satisfies every Ensures vacuously; the real gather always returns the
    # collected records to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The gather list is fully owned, holding one record per step.
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == steps)
    # Record i recovers the working state AT ITS OWN step. Because state_at is
    # strictly increasing, the gathered records are pairwise different: this is
    # precisely the per-step history that an aliasing enumerator -- whose
    # gathered records all collapse onto the final state -- cannot satisfy.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(Result()),
        Result()[i] == state_at(i)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # The live working value the walk advances IN PLACE across steps: it starts
    # before the first step and is incremented one step at a time (never
    # recomputed from scratch), exactly as the enumerator advances its single
    # working record from one state to the next.
    work = 0
    i = 0
    while i < steps:
        # invariants-start
        Invariant(0 <= i and i <= steps)
        Invariant(Acc(list_pred(result)))
        Invariant(len(result) == i)
        # The working value carries the running state from the previous step.
        Invariant(work == i)
        # Every already-gathered record holds the snapshot of its own step --
        # an INDEPENDENT value that subsequent steps never disturb.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == state_at(k)))))
        # The loop consumes the termination obligation: steps - i is the
        # strictly decreasing, bounded-below measure.
        Invariant(MustTerminate(steps - i + 1))
        # invariants-end
        # Advance the working state in place by one step (the enumerator's
        # mutation step): the record now holds the state for step i.
        work = work + 1
        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
        # step): the current value is recorded by value, so later mutations of
        # the working state leave this gathered record untouched.
        snap = work
        result.append(snap)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC ANALYSIS: gather_walk's postcondition is a fully-determined functional spec: Acc(list_pred(Result())) + len(Result())==steps + Forall i in [0,len): Result()[i]==state_at(i)==i+1, with Requires(MustTerminate(2)). Any verifying impl must produce exactly [1,2,...,steps] and terminate. The single genuinely-changed op (yield ms -> yield ms.copy(): independent per-step snapshot vs live alias) is modeled DEEPLY via by-value capture snap=work carried by result[i]==state_at(i); no consumed axiom. refinement.md legs are R (A1,A2,A4,A5) and A-reference (A3, the dict.copy independence), with §B asserting no kind-3. Verified the A-reference correspondence: axiom_check.py (G-AX) run locally exits 0 (sympy 1.14.0): dict.copy() independence probe passes AND real partitions() snapshot history matches one-at-a-time truth with pairwise-distinct neighbours, and the no-copy gather collapses to the final shared object — the deep by-value model corresponds to the real ms.copy() semantics.

BASELINES: positive_control.py verifies (Verification successful, 16.8s, exit 0). prepatch.py (model_prepatch.py) FAILS verify on the value postcondition: 'Postcondition of gather_walk might not hold ... Result()[i] == state_at(i)' (exit 1) — prepatch bug reproduced (aliasing write-back collapses every record to final state). All 7 attack preambles are byte-identical to model.py up to # impl-start (diff clean); only the impl region was edited.

ATTACKS — cmd: python -m swebench_unified.adversary weakness nagini sympy__sympy-20154 <path> (SBU_BENCHMARK_DIR=benchmark-verified), run concurrently in batches of 3:
- atk_1.py (partial-domain: return [] regardless): NOT-A-COUNTEREXAMPLE, verify failed (wrong len) — exit 2.
- atk_2.py (boundary/off-by-one: snapshot before increment => result[i]==i): NOT-A-COUNTEREXAMPLE, verify failed — exit 2.
- atk_3.py (partial-domain: correct except step 0 records 999): NOT-A-COUNTEREXAMPLE, verify failed — exit 2.
- atk_4.py (boundary: double increment => result[i]==2*(i+1)): NOT-A-COUNTEREXAMPLE, verify failed — exit 2.
- atk_5.py (control-flow-effect: correct build then second pass clobbers all records to final work value — aliasing collapse variant distinct from prepatch): NOT-A-COUNTEREXAMPLE, verify failed — exit 2.
- atk_6.py (ungrounded-oracle echo: append state_at(i) directly): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (18.3s) — exit 0. same-spec confirmed SAME.
- atk_7.py (control-flow: infinite while-True loop, no MustTerminate discharge): NOT-A-COUNTEREXAMPLE, verify failed on termination obligation — exit 2.

CANDIDATE RESOLVE (mandatory materialize+run): atk_6 records an INDEPENDENT per-step snapshot state_at(i)==i+1, i.e. output [1,2,...,steps] — behaviorally IDENTICAL to the positive control / gold model, differing only in how the correct per-step value is computed (direct state_at vs work+1). Its faithful refined patch is therefore the gold .copy() patch (patch.diff verbatim). Materialized as atk_6_faithful.patch and RUN through the official harness: harness.run_resolve('sympy__sympy-20154', patch, run_id='sbu-audit-atk6', timeout=1800, retries=1) => RESOLVED: True, COMPLETED: True, NOTE: 'resolved'. This is a resolving echo of the gold, NOT a weakness (per the resolved G-PANEL-1 echo-attack policy: a same-spec verifying attack whose refined patch RESOLVES is not a spec weakness).

CONCLUSION: 7 distinct wrong/echo impls attempted (partial-domain x2, boundary x2, control-flow-effect, ungrounded-oracle echo, divergence). Every value-wrong impl (atk_1-5) is REJECTED by the spec's fully-pinned postcondition; the divergent impl (atk_7) is rejected by MustTerminate; the only CANDIDATE (atk_6) is behaviorally correct and its materialized faithful patch RESOLVES. No verifying wrong impl exists whose faithful patch fails to resolve => verify does not admit an incorrect impl. refinement.md audit clean (all legs R / A-reference / I; no kind-3; A-reference correspondence validated by G-AX exit 0). VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-20154.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An enumerator walks a sequence of states, advancing a single working value as
  it goes, and hands out one record per step. The desired contract is that the
  sequence of records HANDED OUT, when gathered into a list, faithfully records
  the state at the moment of each step:

    * record number i, once gathered, reflects the working state AS IT WAS at
      step i -- not as it later became;
    * because successive steps genuinely change the working state, the gathered
      records have pairwise-different values: gathering an n-step walk yields n
      records that increase step by step, recovering the full per-step history.

  The defective behaviour this rules out is handing out a live alias of the
  working state on every step, so that every gathered record tracks the SAME
  evolving state. Under that defect, once the walk has finished all gathered
  records read back as the FINAL state, and the per-step history is lost
  (gathering an n-step walk would yield n identical records).

Gathering an n-step walk is a bounded computation: the gather MUST terminate
and actually deliver its list of records (a total-correctness obligation,
carried as MustTerminate in the precondition). Nagini is a partial-correctness
verifier by default, so without the obligation a non-terminating
implementation would satisfy every value postcondition only vacuously and
would never hand the gathered records to the caller.

The working state is modelled by an integer; the gathered records by a
`List[int]` whose element i is the value recorded for step i (`str` indexing
and rich containers are unavailable in Nagini; the multiplicity mapping the
real enumerator maintains is abstracted to its per-step changing value). The
walk's value at step i is pinned by a pure spec function `state_at`, chosen
strictly increasing so successive steps genuinely differ -- which is exactly
what an aliasing enumerator (whose gathered records all collapse to the final
value) cannot reproduce. No callee is axiomatized: gathering the walk and
recording an independent per-step snapshot are pure value/structure logic,
modelled deeply (the real-Python record-duplication primitive the enumerator
builds on is validated out-of-band by axiom_check.py / G-AX as an A-reference).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: gathering the walk and recording an independent per-step
# snapshot are pure value/structure logic, modelled deeply. The
# record-duplication primitive the enumerator builds on is validated against
# its real Python semantics out-of-band by axiom_check.py (G-AX) as an
# A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def state_at(i: int) -> int:
    """The working value recorded for step i. Successive steps genuinely change
    it, so the per-step values are pairwise distinct; modelled as the
    strictly-increasing identity i+1 so step i differs from step j."""
    Requires(i >= 0)
    Ensures(Result() == i + 1)
    return i + 1
# pure-end


def gather_walk(steps: int) -> List[int]:
    # pre-conditions-start
    Requires(steps >= 0)
    # TERMINATION: the gather must actually ANSWER — walking a finite number
    # of steps and recording one value per step is a bounded computation.
    # Nagini is a partial-correctness verifier by default, so without this
    # obligation a non-terminating implementation (e.g. an endless loop)
    # satisfies every Ensures vacuously; the real gather always returns the
    # collected records to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The gather list is fully owned, holding one record per step.
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == steps)
    # Record i recovers the working state AT ITS OWN step. Because state_at is
    # strictly increasing, the gathered records are pairwise different: this is
    # precisely the per-step history that an aliasing enumerator -- whose
    # gathered records all collapse onto the final state -- cannot satisfy.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(Result()),
        Result()[i] == state_at(i)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # The live working value the walk advances IN PLACE across steps: it starts
    # before the first step and is incremented one step at a time (never
    # recomputed from scratch), exactly as the enumerator advances its single
    # working record from one state to the next.
    work = 0
    i = 0
    while i < steps:
        # invariants-start
        Invariant(0 <= i and i <= steps)
        Invariant(Acc(list_pred(result)))
        Invariant(len(result) == i)
        # The working value carries the running state from the previous step.
        Invariant(work == i)
        # Every already-gathered record holds the snapshot of its own step --
        # an INDEPENDENT value that subsequent steps never disturb.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == state_at(k)))))
        # The loop consumes the termination obligation: steps - i is the
        # strictly decreasing, bounded-below measure.
        Invariant(MustTerminate(steps - i + 1))
        # invariants-end
        # Advance the working state in place by one step (the enumerator's
        # mutation step): the record now holds the state for step i.
        work = work + 1
        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
        # step): the current value is recorded by value, so later mutations of
        # the working state leave this gathered record untouched.
        snap = work
        result.append(snap)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC ANALYSIS: gather_walk's postcondition is a fully-determined functional spec: Acc(list_pred(Result())) + len(Result())==steps + Forall i in [0,len): Result()[i]==state_at(i)==i+1, with Requires(MustTerminate(2)). Any verifying impl must produce exactly [1,2,...,steps] and terminate. The single genuinely-changed op (yield ms -> yield ms.copy(): independent per-step snapshot vs live alias) is modeled DEEPLY via by-value capture snap=work carried by result[i]==state_at(i); no consumed axiom. refinement.md legs are R (A1,A2,A4,A5) and A-reference (A3, the dict.copy independence), with §B asserting no kind-3. Verified the A-reference correspondence: axiom_check.py (G-AX) run locally exits 0 (sympy 1.14.0): dict.copy() independence probe passes AND real partitions() snapshot history matches one-at-a-time truth with pairwise-distinct neighbours, and the no-copy gather collapses to the final shared object — the deep by-value model corresponds to the real ms.copy() semantics.

BASELINES: positive_control.py verifies (Verification successful, 16.8s, exit 0). prepatch.py (model_prepatch.py) FAILS verify on the value postcondition: 'Postcondition of gather_walk might not hold ... Result()[i] == state_at(i)' (exit 1) — prepatch bug reproduced (aliasing write-back collapses every record to final state). All 7 attack preambles are byte-identical to model.py up to # impl-start (diff clean); only the impl region was edited.

ATTACKS — cmd: python -m swebench_unified.adversary weakness nagini sympy__sympy-20154 <path> (SBU_BENCHMARK_DIR=benchmark-verified), run concurrently in batches of 3:
- atk_1.py (partial-domain: return [] regardless): NOT-A-COUNTEREXAMPLE, verify failed (wrong len) — exit 2.
- atk_2.py (boundary/off-by-one: snapshot before increment => result[i]==i): NOT-A-COUNTEREXAMPLE, verify failed — exit 2.
- atk_3.py (partial-domain: correct except step 0 records 999): NOT-A-COUNTEREXAMPLE, verify failed — exit 2.
- atk_4.py (boundary: double increment => result[i]==2*(i+1)): NOT-A-COUNTEREXAMPLE, verify failed — exit 2.
- atk_5.py (control-flow-effect: correct build then second pass clobbers all records to final work value — aliasing collapse variant distinct from prepatch): NOT-A-COUNTEREXAMPLE, verify failed — exit 2.
- atk_6.py (ungrounded-oracle echo: append state_at(i) directly): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (18.3s) — exit 0. same-spec confirmed SAME.
- atk_7.py (control-flow: infinite while-True loop, no MustTerminate discharge): NOT-A-COUNTEREXAMPLE, verify failed on termination obligation — exit 2.

CANDIDATE RESOLVE (mandatory materialize+run): atk_6 records an INDEPENDENT per-step snapshot state_at(i)==i+1, i.e. output [1,2,...,steps] — behaviorally IDENTICAL to the positive control / gold model, differing only in how the correct per-step value is computed (direct state_at vs work+1). Its faithful refined patch is therefore the gold .copy() patch (patch.diff verbatim). Materialized as atk_6_faithful.patch and RUN through the official harness: harness.run_resolve('sympy__sympy-20154', patch, run_id='sbu-audit-atk6', timeout=1800, retries=1) => RESOLVED: True, COMPLETED: True, NOTE: 'resolved'. This is a resolving echo of the gold, NOT a weakness (per the resolved G-PANEL-1 echo-attack policy: a same-spec verifying attack whose refined patch RESOLVES is not a spec weakness).

CONCLUSION: 7 distinct wrong/echo impls attempted (partial-domain x2, boundary x2, control-flow-effect, ungrounded-oracle echo, divergence). Every value-wrong impl (atk_1-5) is REJECTED by the spec's fully-pinned postcondition; the divergent impl (atk_7) is rejected by MustTerminate; the only CANDIDATE (atk_6) is behaviorally correct and its materialized faithful patch RESOLVES. No verifying wrong impl exists whose faithful patch fails to resolve => verify does not admit an incorrect impl. refinement.md audit clean (all legs R / A-reference / I; no kind-3; A-reference correspondence validated by G-AX exit 0). VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same-spec exit 0). Model models list(partitions(...)) via gather_walk with state_at(i)=i+1 (strictly increasing => pairwise-distinct, independent per-step records), abstracting the yield ms.copy() change. Verified against the REAL repo at base_commit bdb49c4 (& _patch): pre-patch list(partitions(6,k=2)) returns [{1:6},{1:6},{1:6},{1:6}] all aliasing one dict = modeled defect; true history is 4 distinct dicts. (2) Post-patch yields ms.copy(): gathered records are independent objects and pairwise-distinct partitions. Fuzzed 5000 arg tuples incl size=True and n=0/1 edges: 0 runs with non-distinct or aliased gathered partitions -> the strictly-increasing/distinct abstraction is faithful (not stronger than reality) on the observable the F2P tests probe. model.py verifies (16.9s); model_prepatch.py fails the value postcondition (spec is discriminating, non-vacuous); MustTerminate rules out vacuous divergence; axiom_check.py (G-AX) passes against the real partitions(). No input found where the modeled function disagrees with the real callee. Spec is faithful, not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + axioms/pure/pre/post regions; impl elided) does not leak the gold edit beyond the public problem_statement. The public problem_statement already discloses the entire defect and fix: partitions() reuses/aliases the output dictionaries so list(partitions()) gives an apparently wrong result, and the remedy is to copy the dictionary before yielding. The spec view only restates this discriminator abstractly: gathered record i must reflect the state at its own step (independent snapshots, strictly-increasing => pairwise-distinct) vs the ruled-out defect where records alias the live working state and all collapse to the FINAL state. No leak-vectors present: (a) no gold-diff line reproduced (e.g. 'yield ms.copy()' not present); (b) no diff markers; (c) no patched file path/module (sympy/utilities/iterables.py) or repo symbols (partitions, ms, .copy) named anywhere in the spec view; (d) no narration terms (bug/fix/patch/regression/etc.). Mechanical G-LEAK screen (leakage.screen over nagini spec_view vs frozen patch+problem_statement) returns passed=True with zero hard failures. The MustTerminate(2) precondition is a Nagini partial-correctness modeling artifact (vacuous-divergence guard), not a disclosure of the gold edit. mapping.md/refinement.md/axiom_check.py are audit-only artifacts, not part of the solver-visible spec view. All discriminating behavior in the spec is already public via the task statement, so no gold reconstruction beyond problem_statement is possible.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
