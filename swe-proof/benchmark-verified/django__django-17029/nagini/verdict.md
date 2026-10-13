# P2 adversarial audit — django__django-17029

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -82,5 +82,4 @@
     # post-conditions-end
     # impl-start
     registry.swappable_cache_occupancy = 0
-    registry.models_cache_occupancy = 0
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -82,5 +82,5 @@
     # post-conditions-end
     # impl-start
     registry.swappable_cache_occupancy = 0
-    registry.models_cache_occupancy = 0
+    registry.models_cache_occupancy = 1
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -81,6 +81,9 @@
     Ensures(registry.swappable_cache_occupancy == 0)
     # post-conditions-end
     # impl-start
+    i = 0
+    while i < 3:
+        i += 1
     registry.swappable_cache_occupancy = 0
     registry.models_cache_occupancy = 0
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -81,6 +81,8 @@
     Ensures(registry.swappable_cache_occupancy == 0)
     # post-conditions-end
     # impl-start
+    while True:
+        pass
     registry.swappable_cache_occupancy = 0
     registry.models_cache_occupancy = 0
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -81,6 +81,5 @@
     Ensures(registry.swappable_cache_occupancy == 0)
     # post-conditions-end
     # impl-start
-    registry.swappable_cache_occupancy = 0
-    registry.models_cache_occupancy = 0
+    clear_all_caches(registry)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -81,6 +81,6 @@
     Ensures(registry.swappable_cache_occupancy == 0)
     # post-conditions-end
     # impl-start
-    registry.swappable_cache_occupancy = 0
+    registry.swappable_cache_occupancy = registry.models_cache_occupancy
     registry.models_cache_occupancy = 0
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,6 +81,10 @@
     Ensures(registry.swappable_cache_occupancy == 0)
     # post-conditions-end
     # impl-start
+    m = registry.models_cache_occupancy
+    s = registry.swappable_cache_occupancy
+    registry.models_cache_occupancy = m
+    registry.swappable_cache_occupancy = s
     registry.swappable_cache_occupancy = 0
     registry.models_cache_occupancy = 0
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,6 +81,6 @@
     Ensures(registry.swappable_cache_occupancy == 0)
     # post-conditions-end
     # impl-start
-    registry.swappable_cache_occupancy = 0
-    registry.models_cache_occupancy = 0
+    registry.swappable_cache_occupancy = registry.swappable_cache_occupancy - registry.swappable_cache_occupancy
+    registry.models_cache_occupancy = registry.models_cache_occupancy * 0
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -81,6 +81,8 @@
     Ensures(registry.swappable_cache_occupancy == 0)
     # post-conditions-end
     # impl-start
-    registry.swappable_cache_occupancy = 0
-    registry.models_cache_occupancy = 0
+    if registry.models_cache_occupancy > 0:
+        registry.models_cache_occupancy = 0
+    if registry.swappable_cache_occupancy > 0:
+        registry.swappable_cache_occupancy = 0
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-17029.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An application registry keeps several memoizing lookup methods, each backed
  by its own bounded result cache whose occupancy (the number of distinct
  argument tuples whose result is currently retained) can be observed. The
  registry exposes a single cache-reset operation whose documented promise is
  to discard ALL of those retained results — every memoizing method's cache —
  so that immediately afterwards each cache's occupancy is zero, regardless of
  how full any of them was beforehand. A reset that leaves any one method's
  retained results in place would violate that promise: a later observer would
  still see stale memoized values for that method.

  The reset is a bounded, straight-line operation: it MUST terminate and
  return to its caller (a total-correctness obligation, carried as
  MustTerminate in the precondition). A reset that diverges never delivers
  the emptied caches to any later observer, so it does not honour the
  promise either.

The registry is modelled as a minimal class carrying only the touched state:
one non-negative occupancy counter per memoizing method (here the all-models
lookup and the swappable-settings-name lookup). The reset operation clears
every counter to zero. No string/float content is involved, so the carrier
types are plain ints; no library callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Registry:
    def __init__(self, models_cache_occupancy: int,
                 swappable_cache_occupancy: int) -> None:
        Requires(models_cache_occupancy >= 0)
        Requires(swappable_cache_occupancy >= 0)
        # Constructing a registry is bounded work; the strictly smaller
        # measure (1 < 2) lets a caller holding MustTerminate(2) construct
        # a fresh registry without leaking its obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.models_cache_occupancy) and  # type: ignore
                self.models_cache_occupancy == models_cache_occupancy)  # type: ignore
        Ensures(Acc(self.swappable_cache_occupancy) and  # type: ignore
                self.swappable_cache_occupancy == swappable_cache_occupancy)  # type: ignore
        self.models_cache_occupancy = models_cache_occupancy
        self.swappable_cache_occupancy = swappable_cache_occupancy

# axioms-start
# (no library callee is axiomatized: the reset is a pure state operation on the
#  registry's own observable cache occupancies, modelled directly.)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end

def clear_all_caches(registry: Registry) -> None:
    # pre-conditions-start
    Requires(Acc(registry.models_cache_occupancy))
    Requires(Acc(registry.swappable_cache_occupancy))
    # The reset performs a bounded amount of straight-line work and MUST
    # terminate (total correctness). Under partial-correctness semantics a
    # diverging body (e.g. `while True: pass` inserted before the clears)
    # would satisfy the two zero-occupancy postconditions only vacuously,
    # yet would never return to its caller and never deliver the emptied
    # caches to any later observer; this obligation rejects any such
    # implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(registry.models_cache_occupancy))
    Ensures(Acc(registry.swappable_cache_occupancy))
    # EVERY memoizing method's cache is emptied: each occupancy is zero
    # afterwards, no matter what it was before.
    Ensures(registry.models_cache_occupancy == 0)
    Ensures(registry.swappable_cache_occupancy == 0)
    # post-conditions-end
    # impl-start
    registry.swappable_cache_occupancy = 0
    registry.models_cache_occupancy = 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verify => correct holds for the frozen G-EQ spec of django__django-17029 (clear_all_caches). PY=python (the swebench_unified module resolves only there; the nagini verifier is invoked internally by the adversary).

SPEC SUMMARY: clear_all_caches(registry) impl region may touch ONLY the two int fields registry.models_cache_occupancy / registry.swappable_cache_occupancy (only they carry Acc in the precondition). Both postconditions demand *_cache_occupancy == 0 UNCONDITIONALLY, plus Requires(MustTerminate(2)) (total correctness). Any verifying impl must set BOTH occupancies to 0 AND terminate => behaviourally the gold patch (clear BOTH @functools.cache methods).

atk_1.py (partial-domain: clear only swappable) -> exit 2 NOT-A-COUNTEREXAMPLE (verify fails: models_cache_occupancy==0 might not hold).
- atk_2.py (boundary/wrong-value: models=1) -> exit 2 (rejected).
- atk_3.py (control-flow-effect: bounded no-op `while i<3` loop then clear both, loop takes no obligation) -> exit 2 (obligation-leak: loop must take MustTerminate(2)).
- atk_4.py (divergence: `while True: pass` before clears -- classic G-PANEL-1 atk_7 shape) -> exit 2 (MustTerminate rejects it; vacuous postcond satisfaction impossible).
- atk_5.py (self-recursion at non-decreasing measure: clear_all_caches(registry)) -> exit 2 (obligation-leak: callee non-decreasing measure).
- atk_6.py (partial-via-copy: swappable = models_cache_occupancy; models=0) -> exit 2 (swappable may stay >0).
- atk_9.py (control-flow: conditional `if >0` clears each) -> exit 2 (models==0 might not hold on that path branch structure).
- atk_7.py (ungrounded-oracle ECHO: redundant identity reads+writes m/s then clear BOTH to 0) -> exit 0 CANDIDATE (verifies, same spec). Net behaviour == gold.
- atk_8.py (arithmetic-zeroing ECHO: swappable = x-x; models = x*0) -> exit 0 CANDIDATE (verifies, same spec). Net behaviour == gold (both fields = 0).
- atk_prepatch.py (model_prepatch reproduction: drops swappable write) -> exit 2, reproduces bug (postcondition swappable_cache_occupancy==0 might not hold) => spec SENSES the change (G-DIFF). prepatch_reproduced=true.
- positive_control.py (= bundle model.py) -> weakness exit 0 (verifies).

MANDATORY RESOLVE ON THE VERIFYING CANDIDATES (atk_7 AND atk_8): each candidate's faithful refined patch, under the refinement map (field = 0 <-> method.cache_clear(); identity/arithmetic-zeroing reads-writes have no cache-mutating counterpart), IS the gold clear-both patch. Both faithful patches are byte-identical (sha1 5bf7371c76b615548c33159fe2007d8b6e1cbf83) to each other and to the gold single-line add of self.get_swappable_settings_name.cache_clear(). Materialized at atk_7_faithful.patch and atk_8_faithful.patch. EXECUTED via the official harness (docker, run_evaluation, dataset princeton-nlp/SWE-bench_Verified, timeout 1800). First run_resolve() attempt returned completed=False 'no report -- harness error' (the known transient race with the concurrent).

Pre-pulled mirror.gcr.io/swebench/sweb.eval.x86_64.django_1776_django-17029:latest + retagged, then ran run_evaluation manually (run_id sbu-audit-eq-z2eh-manual). Progress bar: ✓=1, ✖=0, error=0. The final make_run_report crashed on a container-inspect 404 during POST-RUN cleanup (contention), AFTER the per-instance evaluation completed, so no top-level summary was written -- but the per-instance report.json was written: report.json (copied to atk7_atk8_faithful_resolve_report.json): resolved=true, patch_successfully_applied=true, FAIL_TO_PASS success=[test_clear_cache (apps.tests.AppsTests.test_clear_cache)], all PASS_TO_PASS success (44), zero failures. => BOTH verifying candidates' faithful patches RESOLVE. They are RESOLVING ECHOES of gold, NOT spec weaknesses (2026-08-06 G-PANEL-1 echo-attack policy). verify does NOT diverge from correct.

REFINEMENT.MD LEG AUDIT: A1 = R (Apps <-> minimal Registry, only touched state). A2 = R + A-reference (swappable_cache_occupancy=0 <-> get_swappable_settings_name.cache_clear(), the ADDED gold line). A3 = R + A-reference (models_cache_occupancy=0 <-> get_models.cache_clear(), pre-existing). A4 = R (MustTerminate(2) <-> bounded straight-line clear_cache() + finite app_configs loop, returns). NO kind-3 (unexpressible-changed-op) legs: the genuinely-changed op (clearing the swappable cache) is modeled DIRECTLY as swappable_cache_occupancy=0, not hidden behind an axiom. meta.axioms=[] (no consumed @ContractOnly axiom); the proof postconditions are concrete int equalities on the registry's own state.

A-REFERENCE CORRESPONDENCE VALIDATED (G-AX): ran benchmark-verified/django__django-17029/nagini/axiom_check.py -> exit 0: 'functools.cache cache_clear() A-reference sound -- currsize==0 after clear from 9 boundary + 2000 fuzz occupancies and repeated-refill cases; per-wrapper independence confirmed'. It exercises the REAL CPython functools.cache callee (the exact module get_models/get_swappable_settings_name are wrapped with), matching mapping.md 2/3 and meta.deep_model_references[0]. Correspondence holds.

CONCLUSION: 7 distinct wrong-impl classes (partial-domain, boundary/wrong-value, control-flow-effect no-op loop, divergence, self-recursion, partial-via-copy, conditional control-flow) all REJECTED by the spec; both verifying candidates (echo, arithmetic-echo) resolve under the official harness; prepatch reproduces the bug (G-DIFF); positive control verifies; no kind-3 legs; A-reference validated against the real callee. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-17029.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An application registry keeps several memoizing lookup methods, each backed
  by its own bounded result cache whose occupancy (the number of distinct
  argument tuples whose result is currently retained) can be observed. The
  registry exposes a single cache-reset operation whose documented promise is
  to discard ALL of those retained results — every memoizing method's cache —
  so that immediately afterwards each cache's occupancy is zero, regardless of
  how full any of them was beforehand. A reset that leaves any one method's
  retained results in place would violate that promise: a later observer would
  still see stale memoized values for that method.

  The reset is a bounded, straight-line operation: it MUST terminate and
  return to its caller (a total-correctness obligation, carried as
  MustTerminate in the precondition). A reset that diverges never delivers
  the emptied caches to any later observer, so it does not honour the
  promise either.

The registry is modelled as a minimal class carrying only the touched state:
one non-negative occupancy counter per memoizing method (here the all-models
lookup and the swappable-settings-name lookup). The reset operation clears
every counter to zero. No string/float content is involved, so the carrier
types are plain ints; no library callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Registry:
    def __init__(self, models_cache_occupancy: int,
                 swappable_cache_occupancy: int) -> None:
        Requires(models_cache_occupancy >= 0)
        Requires(swappable_cache_occupancy >= 0)
        # Constructing a registry is bounded work; the strictly smaller
        # measure (1 < 2) lets a caller holding MustTerminate(2) construct
        # a fresh registry without leaking its obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.models_cache_occupancy) and  # type: ignore
                self.models_cache_occupancy == models_cache_occupancy)  # type: ignore
        Ensures(Acc(self.swappable_cache_occupancy) and  # type: ignore
                self.swappable_cache_occupancy == swappable_cache_occupancy)  # type: ignore
        self.models_cache_occupancy = models_cache_occupancy
        self.swappable_cache_occupancy = swappable_cache_occupancy

# axioms-start
# (no library callee is axiomatized: the reset is a pure state operation on the
#  registry's own observable cache occupancies, modelled directly.)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end

def clear_all_caches(registry: Registry) -> None:
    # pre-conditions-start
    Requires(Acc(registry.models_cache_occupancy))
    Requires(Acc(registry.swappable_cache_occupancy))
    # The reset performs a bounded amount of straight-line work and MUST
    # terminate (total correctness). Under partial-correctness semantics a
    # diverging body (e.g. `while True: pass` inserted before the clears)
    # would satisfy the two zero-occupancy postconditions only vacuously,
    # yet would never return to its caller and never deliver the emptied
    # caches to any later observer; this obligation rejects any such
    # implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(registry.models_cache_occupancy))
    Ensures(Acc(registry.swappable_cache_occupancy))
    # EVERY memoizing method's cache is emptied: each occupancy is zero
    # afterwards, no matter what it was before.
    Ensures(registry.models_cache_occupancy == 0)
    Ensures(registry.swappable_cache_occupancy == 0)
    # post-conditions-end
    # impl-start
    registry.swappable_cache_occupancy = 0
    registry.models_cache_occupancy = 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verify => correct holds for the frozen G-EQ spec of django__django-17029 (clear_all_caches). PY=python (the swebench_unified module resolves only there; the nagini verifier is invoked internally by the adversary).

SPEC SUMMARY: clear_all_caches(registry) impl region may touch ONLY the two int fields registry.models_cache_occupancy / registry.swappable_cache_occupancy (only they carry Acc in the precondition). Both postconditions demand *_cache_occupancy == 0 UNCONDITIONALLY, plus Requires(MustTerminate(2)) (total correctness). Any verifying impl must set BOTH occupancies to 0 AND terminate => behaviourally the gold patch (clear BOTH @functools.cache methods).

atk_1.py (partial-domain: clear only swappable) -> exit 2 NOT-A-COUNTEREXAMPLE (verify fails: models_cache_occupancy==0 might not hold).
- atk_2.py (boundary/wrong-value: models=1) -> exit 2 (rejected).
- atk_3.py (control-flow-effect: bounded no-op `while i<3` loop then clear both, loop takes no obligation) -> exit 2 (obligation-leak: loop must take MustTerminate(2)).
- atk_4.py (divergence: `while True: pass` before clears -- classic G-PANEL-1 atk_7 shape) -> exit 2 (MustTerminate rejects it; vacuous postcond satisfaction impossible).
- atk_5.py (self-recursion at non-decreasing measure: clear_all_caches(registry)) -> exit 2 (obligation-leak: callee non-decreasing measure).
- atk_6.py (partial-via-copy: swappable = models_cache_occupancy; models=0) -> exit 2 (swappable may stay >0).
- atk_9.py (control-flow: conditional `if >0` clears each) -> exit 2 (models==0 might not hold on that path branch structure).
- atk_7.py (ungrounded-oracle ECHO: redundant identity reads+writes m/s then clear BOTH to 0) -> exit 0 CANDIDATE (verifies, same spec). Net behaviour == gold.
- atk_8.py (arithmetic-zeroing ECHO: swappable = x-x; models = x*0) -> exit 0 CANDIDATE (verifies, same spec). Net behaviour == gold (both fields = 0).
- atk_prepatch.py (model_prepatch reproduction: drops swappable write) -> exit 2, reproduces bug (postcondition swappable_cache_occupancy==0 might not hold) => spec SENSES the change (G-DIFF). prepatch_reproduced=true.
- positive_control.py (= bundle model.py) -> weakness exit 0 (verifies).

MANDATORY RESOLVE ON THE VERIFYING CANDIDATES (atk_7 AND atk_8): each candidate's faithful refined patch, under the refinement map (field = 0 <-> method.cache_clear(); identity/arithmetic-zeroing reads-writes have no cache-mutating counterpart), IS the gold clear-both patch. Both faithful patches are byte-identical (sha1 5bf7371c76b615548c33159fe2007d8b6e1cbf83) to each other and to the gold single-line add of self.get_swappable_settings_name.cache_clear(). Materialized at atk_7_faithful.patch and atk_8_faithful.patch. EXECUTED via the official harness (docker, run_evaluation, dataset princeton-nlp/SWE-bench_Verified, timeout 1800). First run_resolve() attempt returned completed=False 'no report -- harness error' (the known transient race with the concurrent).

Pre-pulled mirror.gcr.io/swebench/sweb.eval.x86_64.django_1776_django-17029:latest + retagged, then ran run_evaluation manually (run_id sbu-audit-eq-z2eh-manual). Progress bar: ✓=1, ✖=0, error=0. The final make_run_report crashed on a container-inspect 404 during POST-RUN cleanup (contention), AFTER the per-instance evaluation completed, so no top-level summary was written -- but the per-instance report.json was written: report.json (copied to atk7_atk8_faithful_resolve_report.json): resolved=true, patch_successfully_applied=true, FAIL_TO_PASS success=[test_clear_cache (apps.tests.AppsTests.test_clear_cache)], all PASS_TO_PASS success (44), zero failures. => BOTH verifying candidates' faithful patches RESOLVE. They are RESOLVING ECHOES of gold, NOT spec weaknesses (2026-08-06 G-PANEL-1 echo-attack policy). verify does NOT diverge from correct.

REFINEMENT.MD LEG AUDIT: A1 = R (Apps <-> minimal Registry, only touched state). A2 = R + A-reference (swappable_cache_occupancy=0 <-> get_swappable_settings_name.cache_clear(), the ADDED gold line). A3 = R + A-reference (models_cache_occupancy=0 <-> get_models.cache_clear(), pre-existing). A4 = R (MustTerminate(2) <-> bounded straight-line clear_cache() + finite app_configs loop, returns). NO kind-3 (unexpressible-changed-op) legs: the genuinely-changed op (clearing the swappable cache) is modeled DIRECTLY as swappable_cache_occupancy=0, not hidden behind an axiom. meta.axioms=[] (no consumed @ContractOnly axiom); the proof postconditions are concrete int equalities on the registry's own state.

A-REFERENCE CORRESPONDENCE VALIDATED (G-AX): ran benchmark-verified/django__django-17029/nagini/axiom_check.py -> exit 0: 'functools.cache cache_clear() A-reference sound -- currsize==0 after clear from 9 boundary + 2000 fuzz occupancies and repeated-refill cases; per-wrapper independence confirmed'. It exercises the REAL CPython functools.cache callee (the exact module get_models/get_swappable_settings_name are wrapped with), matching mapping.md 2/3 and meta.deep_model_references[0]. Correspondence holds.

CONCLUSION: 7 distinct wrong-impl classes (partial-domain, boundary/wrong-value, control-flow-effect no-op loop, divergence, self-recursion, partial-via-copy, conditional control-flow) all REJECTED by the spec; both verifying candidates (echo, arithmetic-echo) resolve under the official harness; prepatch reproduces the bug (G-DIFF); positive control verifies; no kind-3 legs; A-reference validated against the real callee. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function clear_all_caches(registry) models Apps.clear_cache() at django/apps/registry.py:370 (patched: adds self.get_swappable_settings_name.cache_clear()). Spec = precondition {Acc on both occupancy fields, MustTerminate(2)} + postcondition {models_cache_occupancy==0 AND swappable_cache_occupancy==0}. Carrier bridge: each int field <-> that @functools.cache method's cache_info().currsize.

Faithfulness check against the REAL callee at base_commit (worktree, patched registry.py verified: two @functools.cache methods at lines 168/283, added swappable cache_clear at 376). Empirical run: filled both caches (models currsize=2, swap currsize=2), called apps.clear_cache(), observed models=0 AND swap=0. The real clear_cache() unconditionally calls cache_clear() on BOTH wrappers, so currsize==0 for both on return, from ANY starting occupancy. This exactly matches the two zero-occupancy postconditions.

Precondition faithfulness: (a) occupancy>=0 / Acc — currsize is always a non-negative int and the fields always exist, so the precondition excludes no real input state; it is not over-strong. (b) MustTerminate(2) — real clear_cache() is straight-line (two cache_clear() calls + a bounded loop over the finite app_configs dict); it terminates on every real call. The obligation therefore holds on every real input, not a restriction that hides divergent real behavior. No real input is excluded by the precondition.

Model verifies (nagini_verify.sh exit 0, 11.55s). No input found where the modeled function disagrees with the real Apps.clear_cache() on the modeled observable (both caches end at currsize 0). Postconditions are neither too weak nor too strong relative to real behavior; precondition does not drift from real reachable states. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit is one added line: `self.get_swappable_settings_name.cache_clear()` in Apps.clear_cache(); the discriminator is that clear_cache must ALSO empty the swappable-settings-name cache. That discriminator is FULLY PUBLIC in the problem_statement, which literally states 'Apps.clear_cache() does not clear get_swappable_settings_name cache' and 'I propose to add: self.get_swappable_settings_name.cache_clear() line to def clear_cache.' Thus get_swappable_settings_name, clear_cache, cache, and functools are all solver-visible. Mechanical G-LEAK screen passes clean (rep.passed=True, no hard failures): no diff markers, no patched file path/module, no verbatim gold-patch line (`self.get_swappable_settings_name.cache_clear()` does not appear normalized in the spec view — impl elided; the changed symbol `clear_cache` is public), no narration terms. Spec region byte-identical with the twin (same-spec exit 0). The spec-view behavioral prose ('every memoizing method's cache emptied, occupancy zero afterwards, incl. the swappable-settings-name one') adds nothing beyond the problem statement. The `get_models`/all-models mention is context, not leak: get_models is the pre-existing (unchanged) cleared cache, not the gold edit. MustTerminate/while-True material is generic, abstract model machinery, not edit narration. No spec-view line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).