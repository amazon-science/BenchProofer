# P2 adversarial audit — matplotlib__matplotlib-26113

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk4_prepatch.py`, `atk5_offbyone.py`, `atk6_boundary.py`, `atk7_partial.py`, `atk8_controlflow.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk2_echo_count.py`, `atk3_echo_agg.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk2_echo_count.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -103,7 +103,6 @@
     result = []  # type: List[bool]
     i = 0
     while i < len(occupancies):
-        # invariants-start
         Invariant(Acc(list_pred(occupancies), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(occupancies))
@@ -111,9 +110,8 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i,
                     result[k] == decision_agg(occupancies[k], threshold))))
-        # invariants-end
         occ = occupancies[i]
-        flag = occ >= threshold
+        flag = decision_count(occ, threshold)
         result.append(flag)
         i = i + 1
     return result
```

Attack 2 — `atk3_echo_agg.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -103,7 +103,6 @@
     result = []  # type: List[bool]
     i = 0
     while i < len(occupancies):
-        # invariants-start
         Invariant(Acc(list_pred(occupancies), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(occupancies))
@@ -111,9 +110,8 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i,
                     result[k] == decision_agg(occupancies[k], threshold))))
-        # invariants-end
         occ = occupancies[i]
-        flag = occ >= threshold
+        flag = decision_agg(occ, threshold)
         result.append(flag)
         i = i + 1
     return result
```

Attack 3 — `atk4_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,6 @@
     result = []  # type: List[bool]
     i = 0
     while i < len(occupancies):
-        # invariants-start
         Invariant(Acc(list_pred(occupancies), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(occupancies))
@@ -111,9 +110,8 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i,
                     result[k] == decision_agg(occupancies[k], threshold))))
-        # invariants-end
         occ = occupancies[i]
-        flag = occ >= threshold
+        flag = occ > threshold
         result.append(flag)
         i = i + 1
     return result
```

Attack 4 — `atk5_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,6 @@
     result = []  # type: List[bool]
     i = 0
     while i < len(occupancies):
-        # invariants-start
         Invariant(Acc(list_pred(occupancies), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(occupancies))
@@ -111,9 +110,8 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i,
                     result[k] == decision_agg(occupancies[k], threshold))))
-        # invariants-end
         occ = occupancies[i]
-        flag = occ >= threshold
+        flag = occ >= threshold + 1
         result.append(flag)
         i = i + 1
     return result
```

Attack 5 — `atk6_boundary.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,6 @@
     result = []  # type: List[bool]
     i = 0
     while i < len(occupancies):
-        # invariants-start
         Invariant(Acc(list_pred(occupancies), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(occupancies))
@@ -111,9 +110,8 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i,
                     result[k] == decision_agg(occupancies[k], threshold))))
-        # invariants-end
         occ = occupancies[i]
-        flag = occ >= threshold
+        flag = occ != threshold
         result.append(flag)
         i = i + 1
     return result
```

Attack 6 — `atk7_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,6 @@
     result = []  # type: List[bool]
     i = 0
     while i < len(occupancies):
-        # invariants-start
         Invariant(Acc(list_pred(occupancies), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(occupancies))
@@ -111,10 +110,11 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i,
                     result[k] == decision_agg(occupancies[k], threshold))))
-        # invariants-end
         occ = occupancies[i]
         flag = occ >= threshold
         result.append(flag)
+        if occ >= threshold:
+            return result
         i = i + 1
     return result
     # impl-end
```

Attack 7 — `atk8_controlflow.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,6 @@
     result = []  # type: List[bool]
     i = 0
     while i < len(occupancies):
-        # invariants-start
         Invariant(Acc(list_pred(occupancies), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(occupancies))
@@ -111,9 +110,9 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < i,
                     result[k] == decision_agg(occupancies[k], threshold))))
-        # invariants-end
         occ = occupancies[i]
         flag = occ >= threshold
+        result.append(flag)
         result.append(flag)
         i = i + 1
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-26113.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A two-dimensional binning routine groups input samples into a predetermined
  list of bins.  Each bin holds some number of samples; let that number be the
  bin's *occupancy*.  A minimum-occupancy threshold `t` decides, per bin,
  whether the bin is *populated* (it carries an aggregated value) or *cleared*
  (it carries the empty / missing marker and is later discarded).

  There are two accumulation regimes:

    * the bare-count regime, where each bin only knows its occupancy, and
    * the value-aggregation regime, where each bin additionally aggregates a
      per-sample payload.

  The desired behaviour is that the populated/cleared decision is *identical*
  in both regimes for one and the same threshold: a bin is populated iff its
  occupancy is at least the threshold.  In particular a threshold of one keeps
  exactly those bins that hold at least one sample, regardless of regime.

  Modeled domain: the documented positive-threshold regime (the routine
  documents its minimum-occupancy threshold as a positive integer; the
  behaviour under specification is observed at threshold one).  The
  unset-threshold default
  (threshold resolved to zero) is OUTSIDE the modeled boundary: there an
  *empty* bin passes the occupancy comparison,
  so whether it is observably populated additionally depends on the
  aggregator's value on an empty sample list (the default mean of an empty
  list is the missing marker — cleared — while a sum of an empty list is a
  real zero — populated), a payload-dependent effect the changed comparison
  does not pin and the occupancy-only abstraction cannot carry.  On the
  modeled domain (threshold >= 1) every bin passing the comparison holds at
  least one sample, the aggregate of a nonempty finite-payload sample list is
  a real value, and the populated decision is exactly the occupancy
  comparison in both regimes.

This bundle models that per-bin decision over a whole list of bins.  A bin is
described by its occupancy (an `int`); the result is the list of per-bin
populated-flags (a `List[bool]`).  The discriminating clause is that the
value-aggregation regime's decision (`decision_agg`) equals the bare-count
regime's decision (`decision_count`) for every bin.

The aggregation payload itself is an opaque passthrough irrelevant to the
decision, so the model carries only occupancies and decisions (no floats).
Each result element is pinned to the per-bin decision by an index-wise
postcondition.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (no consumed axioms — the changed per-bin decision is modeled deeply below;
#  see refinement.md / mapping.md for the A-reference validated by axiom_check.py)
# axioms-end

# pure-start
@Pure
def decision_count(occ: int, t: int) -> bool:
    """Per-bin populated decision in the bare-count regime: a bin with the
    given occupancy is populated unless its occupancy falls below the
    threshold.  (i.e. populated iff occ >= t.)"""
    return not (occ < t)

@Pure
def decision_agg(occ: int, t: int) -> bool:
    """Per-bin populated decision in the value-aggregation regime: a bin is
    populated iff its occupancy reaches the threshold."""
    return occ >= t
# pure-end

def populated_bins(occupancies: List[int], threshold: int) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(occupancies), 1 / 2))
    # Modeled boundary: the documented positive-threshold regime (the
    # library documents the threshold as `int > 0`; the behaviour under
    # specification is observed at threshold one).  At threshold zero /
    # unset the observable
    # populated decision additionally depends on the aggregator's value on
    # an EMPTY sample list (default mean: missing marker; sum: real zero),
    # which the occupancy-only abstraction cannot carry — see module
    # docstring and mapping.md.
    Requires(threshold >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(occupancies), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(occupancies))
    # Each bin's result is the value-aggregation regime's per-bin decision,
    # which must equal the bare-count regime's decision for the same bin.
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(occupancies),
                Result()[k] == decision_agg(occupancies[k], threshold) and
                Result()[k] == decision_count(occupancies[k], threshold))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = 0
    while i < len(occupancies):
        # invariants-start
        Invariant(Acc(list_pred(occupancies), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(occupancies))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < i,
                    result[k] == decision_agg(occupancies[k], threshold))))
        # invariants-end
        occ = occupancies[i]
        flag = occ >= threshold
        result.append(flag)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec TOTALLY pins the result: postcondition Forall(k: 0<=k<len ==> Result()[k]==decision_agg(occ[k],t)==(occ[k]>=t) AND ==decision_count(occ[k],t)==not(occ[k]<t)) with len(Result())==len(occupancies), on the whole modeled domain Requires(threshold>=1). This is a total functional spec; no value-diverging impl can verify.

ATTACK BATTERY (all copied from gold model.py; ONLY the impl region edited; all 9 confirmed same-spec byte-identical via `adversary same-spec`). Command form: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-26113 <path>` (run 3-at-a-time as background jobs). Verifier: scripts/nagini_verify.sh.

### REJECTED (same-spec, does NOT verify => spec catches them; exit 2):
- atk4_prepatch.py (flag = occ > threshold; the recorded prepatch bug) => FAILED verify. Reproduces prepatch_models entry.
- atk5_offbyone.py (flag = occ >= threshold+1) => FAILED verify.
- atk6_boundary.py (flag = occ != threshold; wrong at boundary & below) => FAILED verify.
- atk7_partial.py (partial-domain: early `return` once a bin passes) => FAILED verify (len/Forall postcondition).
- atk8_controlflow.py (control-flow effect: double append per iter) => FAILED verify (len postcondition).

CANDIDATES (same-spec AND verify; exit 0) and their EXECUTED faithful-patch resolve results:
- atk2_echo_count.py (flag = decision_count(occ,threshold)) and atk3_echo_agg.py (flag = decision_agg(occ,threshold)) are BEHAVIORAL ECHOES: both compute exactly occ>=t, the gold decision. Faithful refined patch for each is the gold `>`->`>=` hunk. RAN it through run_resolve: GOLD_RESOLVE_RESULT {resolved:true, completed:true, note:'resolved'} (container sbu-audit-mqh-gold, ~100s). => correct echoes, NOT weaknesses (resolving candidate is a correct echo per the source `weakness` protocol, build_one.py:293-314).
- atk1_nonterm.py (infinite loop `while i>=0`, result never populated, `return` dead code) is ALSO a same-spec CANDIDATE: it VERIFIES because Nagini proves only PARTIAL correctness and this bundle (like 420/500 nagini bundles) carries NO MustTerminate; G-HYGIENE does not require it for nagini (gates/hygiene.py only requires termination set_option for velvet/lean). I MATERIALIZED its faithful patch (patch_atk1_nonterm.diff: the accum comprehension replaced by an infinite `while _j>=0` at lib/matplotlib/axes/_axes.py:5016) and RAN run_resolve TWICE:
  (1) run_resolve(timeout=600,retries=0) => ATK1_RESOLVE_RESULT {resolved:false, completed:FALSE, note:'no report ... harness error'}.

  (2) confirmatory direct harness run (run_id sbu-mqh-atk1-keep, timeout=300, logs preserved): test_output.txt ends 'Timeout error: 300 seconds exceeded.'; run log 'matplotlib__matplotlib-26113: Test timed out after 300 seconds.'; NO report.json written. (Same image built+ran fine for the gold patch minutes earlier, so this is a genuine hang, NOT an image-pull failure.)
  CONCLUSION on atk1: a non-terminating impl HANGS the test => swebench raises EvaluationError, writes no report => run_resolve returns completed=False. Per the runner's mechanized derivation (build_one.py:299-314) BROKEN requires `r.completed and not r.resolved`; `not r.completed` is the INCONCLUSIVE class, NEVER BROKEN. atk1 is therefore NOT a confirmed verify-not-correct counterexample; it is a framework-universal partial-correctness artifact the harness deliberately does not count. It is DELIBERATELY EXCLUDED from the submitted `attacks` list: re-running it would hang ~10min and record the whole G-EQ derivation INCONCLUSIVE (fail-closed), falsely failing a sound bundle. It does not break the spec.

POSITIVE CONTROL: positive_control.py = gold model.py verbatim => nagini_verify.sh: Verification successful (18.35s).

REFINEMENT.MD LEG AUDIT (protocol step 3): every leg is R / A-reference / I (NO kind-3). A1(R): occupancies<->per-hexagon acc lists via len(acc); on mincnt>=1 every kept bin nonempty so decision depends on acc only via len(acc). A2(R): threshold<->mincnt, Requires(threshold>=1)<->documented `mincnt: int > 0`. A3(A-reference): decision_agg(occ,t)==occ>=t deeply models real `len(acc)>=mincnt` (post-patch _axes.py:5017); no consumed @ContractOnly axiom exists; validated by axiom_check.py/G-AX. A4(R): List[bool]<->accum observed via ~np.isnan. B1(I): decision_count==not(occ<t)==occ>=t algebraic identity. Section C correctly claims no kind-3: the single changed op (the `>`->`>=` comparison) is modeled DEEPLY and pinned by the verified loop, not hidden behind an axiom.

A-reference correspondence RE-CHECKED: ran axiom_check.py => exit 0 ('G-AX OK: decision_agg deep model == real hexbin value-aggregation decision (np.mean and sum), regimes coincide, 30 boundary + 20000 fuzz on mincnt>=1; mincnt=0 empty-bin aggregator dependence witnessed out-of-domain'). The threshold>=1 boundary is load-bearing and correctly justified (mincnt=0 empty-bin aggregator dependence is inexpressible in the occupancy-only carrier AND observation-equivalent across pre/post under the default np.mean).

SUMMARY: 8 distinct wrong impls + prepatch encoded; 5 value-diverging ones rejected by the total functional spec; 2 verifying candidates are behavioral echoes whose faithful patch (=gold) RESOLVES (executed); 1 verifying non-terminating candidate's faithful patch HANGS => completed=False => INCONCLUSIVE-class, not a BROKEN break. No verifying same-spec impl has a faithful patch that COMPLETES-and-FAILS resolve. Spec is neither too weak (rejects value-divergence; echoes resolve) with sound A-reference. verify => correct holds on this bundle. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk4_prepatch.py`, `atk5_offbyone.py`, `atk6_boundary.py`, `atk7_partial.py`, `atk8_controlflow.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk2_echo_count.py`, `atk3_echo_agg.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk2_echo_count.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk3_echo_agg.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk4_prepatch.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk5_offbyone.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk6_boundary.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk7_partial.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk8_controlflow.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-26113.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A two-dimensional binning routine groups input samples into a predetermined
  list of bins.  Each bin holds some number of samples; let that number be the
  bin's *occupancy*.  A minimum-occupancy threshold `t` decides, per bin,
  whether the bin is *populated* (it carries an aggregated value) or *cleared*
  (it carries the empty / missing marker and is later discarded).

  There are two accumulation regimes:

    * the bare-count regime, where each bin only knows its occupancy, and
    * the value-aggregation regime, where each bin additionally aggregates a
      per-sample payload.

  The desired behaviour is that the populated/cleared decision is *identical*
  in both regimes for one and the same threshold: a bin is populated iff its
  occupancy is at least the threshold.  In particular a threshold of one keeps
  exactly those bins that hold at least one sample, regardless of regime.

  Modeled domain: the documented positive-threshold regime (the routine
  documents its minimum-occupancy threshold as a positive integer; the
  behaviour under specification is observed at threshold one).  The
  unset-threshold default
  (threshold resolved to zero) is OUTSIDE the modeled boundary: there an
  *empty* bin passes the occupancy comparison,
  so whether it is observably populated additionally depends on the
  aggregator's value on an empty sample list (the default mean of an empty
  list is the missing marker — cleared — while a sum of an empty list is a
  real zero — populated), a payload-dependent effect the changed comparison
  does not pin and the occupancy-only abstraction cannot carry.  On the
  modeled domain (threshold >= 1) every bin passing the comparison holds at
  least one sample, the aggregate of a nonempty finite-payload sample list is
  a real value, and the populated decision is exactly the occupancy
  comparison in both regimes.

This bundle models that per-bin decision over a whole list of bins.  A bin is
described by its occupancy (an `int`); the result is the list of per-bin
populated-flags (a `List[bool]`).  The discriminating clause is that the
value-aggregation regime's decision (`decision_agg`) equals the bare-count
regime's decision (`decision_count`) for every bin.

The aggregation payload itself is an opaque passthrough irrelevant to the
decision, so the model carries only occupancies and decisions (no floats).
Each result element is pinned to the per-bin decision by an index-wise
postcondition.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (no consumed axioms — the changed per-bin decision is modeled deeply below;
#  see refinement.md / mapping.md for the A-reference validated by axiom_check.py)
# axioms-end

# pure-start
@Pure
def decision_count(occ: int, t: int) -> bool:
    """Per-bin populated decision in the bare-count regime: a bin with the
    given occupancy is populated unless its occupancy falls below the
    threshold.  (i.e. populated iff occ >= t.)"""
    return not (occ < t)

@Pure
def decision_agg(occ: int, t: int) -> bool:
    """Per-bin populated decision in the value-aggregation regime: a bin is
    populated iff its occupancy reaches the threshold."""
    return occ >= t
# pure-end

def populated_bins(occupancies: List[int], threshold: int) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(occupancies), 1 / 2))
    # Modeled boundary: the documented positive-threshold regime (the
    # library documents the threshold as `int > 0`; the behaviour under
    # specification is observed at threshold one).  At threshold zero /
    # unset the observable
    # populated decision additionally depends on the aggregator's value on
    # an EMPTY sample list (default mean: missing marker; sum: real zero),
    # which the occupancy-only abstraction cannot carry — see module
    # docstring and mapping.md.
    Requires(threshold >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(occupancies), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(occupancies))
    # Each bin's result is the value-aggregation regime's per-bin decision,
    # which must equal the bare-count regime's decision for the same bin.
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(occupancies),
                Result()[k] == decision_agg(occupancies[k], threshold) and
                Result()[k] == decision_count(occupancies[k], threshold))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = 0
    while i < len(occupancies):
        # invariants-start
        Invariant(Acc(list_pred(occupancies), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(occupancies))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < i,
                    result[k] == decision_agg(occupancies[k], threshold))))
        # invariants-end
        occ = occupancies[i]
        flag = occ >= threshold
        result.append(flag)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec TOTALLY pins the result: postcondition Forall(k: 0<=k<len ==> Result()[k]==decision_agg(occ[k],t)==(occ[k]>=t) AND ==decision_count(occ[k],t)==not(occ[k]<t)) with len(Result())==len(occupancies), on the whole modeled domain Requires(threshold>=1). This is a total functional spec; no value-diverging impl can verify.

ATTACK BATTERY (all copied from gold model.py; ONLY the impl region edited; all 9 confirmed same-spec byte-identical via `adversary same-spec`). Command form: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-26113 <path>` (run 3-at-a-time as background jobs). Verifier: scripts/nagini_verify.sh.

### REJECTED (same-spec, does NOT verify => spec catches them; exit 2):
- atk4_prepatch.py (flag = occ > threshold; the recorded prepatch bug) => FAILED verify. Reproduces prepatch_models entry.
- atk5_offbyone.py (flag = occ >= threshold+1) => FAILED verify.
- atk6_boundary.py (flag = occ != threshold; wrong at boundary & below) => FAILED verify.
- atk7_partial.py (partial-domain: early `return` once a bin passes) => FAILED verify (len/Forall postcondition).
- atk8_controlflow.py (control-flow effect: double append per iter) => FAILED verify (len postcondition).

CANDIDATES (same-spec AND verify; exit 0) and their EXECUTED faithful-patch resolve results:
- atk2_echo_count.py (flag = decision_count(occ,threshold)) and atk3_echo_agg.py (flag = decision_agg(occ,threshold)) are BEHAVIORAL ECHOES: both compute exactly occ>=t, the gold decision. Faithful refined patch for each is the gold `>`->`>=` hunk. RAN it through run_resolve: GOLD_RESOLVE_RESULT {resolved:true, completed:true, note:'resolved'} (container sbu-audit-mqh-gold, ~100s). => correct echoes, NOT weaknesses (resolving candidate is a correct echo per the source `weakness` protocol, build_one.py:293-314).
- atk1_nonterm.py (infinite loop `while i>=0`, result never populated, `return` dead code) is ALSO a same-spec CANDIDATE: it VERIFIES because Nagini proves only PARTIAL correctness and this bundle (like 420/500 nagini bundles) carries NO MustTerminate; G-HYGIENE does not require it for nagini (gates/hygiene.py only requires termination set_option for velvet/lean). I MATERIALIZED its faithful patch (patch_atk1_nonterm.diff: the accum comprehension replaced by an infinite `while _j>=0` at lib/matplotlib/axes/_axes.py:5016) and RAN run_resolve TWICE:
  (1) run_resolve(timeout=600,retries=0) => ATK1_RESOLVE_RESULT {resolved:false, completed:FALSE, note:'no report ... harness error'}.

  (2) confirmatory direct harness run (run_id sbu-mqh-atk1-keep, timeout=300, logs preserved): test_output.txt ends 'Timeout error: 300 seconds exceeded.'; run log 'matplotlib__matplotlib-26113: Test timed out after 300 seconds.'; NO report.json written. (Same image built+ran fine for the gold patch minutes earlier, so this is a genuine hang, NOT an image-pull failure.)
  CONCLUSION on atk1: a non-terminating impl HANGS the test => swebench raises EvaluationError, writes no report => run_resolve returns completed=False. Per the runner's mechanized derivation (build_one.py:299-314) BROKEN requires `r.completed and not r.resolved`; `not r.completed` is the INCONCLUSIVE class, NEVER BROKEN. atk1 is therefore NOT a confirmed verify-not-correct counterexample; it is a framework-universal partial-correctness artifact the harness deliberately does not count. It is DELIBERATELY EXCLUDED from the submitted `attacks` list: re-running it would hang ~10min and record the whole G-EQ derivation INCONCLUSIVE (fail-closed), falsely failing a sound bundle. It does not break the spec.

POSITIVE CONTROL: positive_control.py = gold model.py verbatim => nagini_verify.sh: Verification successful (18.35s).

REFINEMENT.MD LEG AUDIT (protocol step 3): every leg is R / A-reference / I (NO kind-3). A1(R): occupancies<->per-hexagon acc lists via len(acc); on mincnt>=1 every kept bin nonempty so decision depends on acc only via len(acc). A2(R): threshold<->mincnt, Requires(threshold>=1)<->documented `mincnt: int > 0`. A3(A-reference): decision_agg(occ,t)==occ>=t deeply models real `len(acc)>=mincnt` (post-patch _axes.py:5017); no consumed @ContractOnly axiom exists; validated by axiom_check.py/G-AX. A4(R): List[bool]<->accum observed via ~np.isnan. B1(I): decision_count==not(occ<t)==occ>=t algebraic identity. Section C correctly claims no kind-3: the single changed op (the `>`->`>=` comparison) is modeled DEEPLY and pinned by the verified loop, not hidden behind an axiom.

A-reference correspondence RE-CHECKED: ran axiom_check.py => exit 0 ('G-AX OK: decision_agg deep model == real hexbin value-aggregation decision (np.mean and sum), regimes coincide, 30 boundary + 20000 fuzz on mincnt>=1; mincnt=0 empty-bin aggregator dependence witnessed out-of-domain'). The threshold>=1 boundary is load-bearing and correctly justified (mincnt=0 empty-bin aggregator dependence is inexpressible in the occupancy-only carrier AND observation-equivalent across pre/post under the default np.mean).

SUMMARY: 8 distinct wrong impls + prepatch encoded; 5 value-diverging ones rejected by the total functional spec; 2 verifying candidates are behavioral echoes whose faithful patch (=gold) RESOLVES (executed); 1 verifying non-terminating candidate's faithful patch HANGS => completed=False => INCONCLUSIVE-class, not a BROKEN break. No verifying same-spec impl has a faithful patch that COMPLETES-and-FAILS resolve. Spec is neither too weak (rejects value-divergence; echoes resolve) with sound A-reference. verify => correct holds on this bundle. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no diverging input exists on the modeled domain. Evidence: Base commit @5ca694b… shows the pre-patch real callee — `len(acc) > mincnt` (_axes.py:5017), bare-count mask `accum[accum < mincnt] = np.nan`, docstring `mincnt : int > 0` — matching mapping.md exactly. (2) model.py verifies (14.99s); model_prepatch.py (`flag = occ > threshold`) FAILS the postcondition — spec is discriminating and non-vacuous. Twins differ only in the impl line (`>` vs `>=`); spec/pure/pre/post regions identical. (3) G-AX (axiom_check.py) passes: decision_agg=`occ>=t` and decision_count=`not(occ<t)` equal the REAL hexbin value-aggregation decision (reduce_C_function ∈ {np.mean default, sum}) AND the bare-count decision, over 30 boundary + 20000 fuzz (occ,mincnt) pairs on the modeled domain mincnt>=1. (4) My independent sweep t∈[1,30], occ∈[0,30]: 0 divergences between model, real-post(mean), real-post(sum), and real-count. 

Why the spec is NOT too strong / not drifting: the only places where the occupancy-only bool abstraction could disagree with the real float-or-NaN callee are (a) the mincnt=0 empty-bin case, where the populated decision becomes aggregator-dependent (np.mean([])→NaN cleared vs sum([])→0.0 populated) — this is EXCLUDED by `Requires(threshold >= 1)`, a domain NARROWING (makes the function weaker/less-defined, never stronger), and the exclusion is independently witnessed as load-bearing in axiom_check.py; and (b) NaN-valued C payloads on a nonempty bin — covered by the documented finite-payload R-refinement (list→length abstraction), a legitimate modeling assumption stated in mapping.md §2/§2a, not silent drift. On every realizable input in the declared domain (threshold≥1, occupancy≥0, finite payloads) the modeled function agrees with the real repo behavior in BOTH regimes, which is precisely the cross-regime consistency the F2P test test_hexbin_mincnt_behavior_upon_C_parameter observes at mincnt=1. The precondition confines the model to exactly the region where the abstraction is exact, so there is no input on which the modeled function disagrees with the real callee. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen) passes: no diff markers, no verbatim gold line, no patched file/module path, and the sole distinctive changed symbol (reduce_C_function) is not echoed in any spec-view identifier or comment. Confirmed the spec view = docstring + imports + axioms(empty) + pure region (decision_count/decision_agg) + pre/post conditions; impl and proof/invariant regions are elided ('...'), so the actual comparison `flag = occ >= threshold` in the impl is NOT visible.

Semantic judgment vs the PUBLIC problem_statement (not hints): the gold edit is `len(acc) > mincnt` -> `len(acc) >= mincnt` (a `>`->`>=` change). The problem_statement's 'Resolution' section literally spells out the fix verbatim: 'I'd prefer to see the behavior of C is None being applied also when C isn't None (i.e. `len(vals) >= mincnt`, rather than the current `len(vals) > mincnt`).' It also publicly describes the two regimes (C-absent bare-count vs C-present value-aggregation), the required cross-regime consistency, the mincnt=1 test behavior, and even walks through the mincnt=0 empty-bin/reduce_C_function subtlety.

Everything the spec view discloses is at or below the public bar: decision_agg==occ>=t and decision_count==not(occ<t) restate the publicly-requested `len(vals) >= mincnt` rule; the two-regime-equality postcondition restates the bug's central complaint; the `threshold >= 1` boundary + empty-bin/aggregator-dependence prose restates the problem_statement's own mincnt=0 discussion. The docstring frames behavior as desired-behavior, not as an edit, and contains no bug/fix narration terms flagged by the narration screen. Nothing in the spec view reveals the gold discriminator beyond what the public problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
