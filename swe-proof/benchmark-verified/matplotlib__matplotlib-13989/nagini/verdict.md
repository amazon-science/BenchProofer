# P2 adversarial audit — matplotlib__matplotlib-13989

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pc_correct.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                              stacked: bool, range_value: int) -> Dict[int, int]:
     # pre-conditions-start
     Requires(KEY_RANGE() != KEY_DENSITY())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(Result()))
@@ -104,6 +102,8 @@
     if not multi_precomputed:
         hist_kwargs[KEY_RANGE()] = range_value
     if density and not stacked:
-        hist_kwargs[KEY_DENSITY()] = 1
+        fresh = {}  # type: Dict[int, int]
+        fresh[KEY_DENSITY()] = 1
+        hist_kwargs = fresh
     return hist_kwargs
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                              stacked: bool, range_value: int) -> Dict[int, int]:
     # pre-conditions-start
     Requires(KEY_RANGE() != KEY_DENSITY())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(Result()))
@@ -103,7 +101,5 @@
     hist_kwargs = {}  # type: Dict[int, int]
     if not multi_precomputed:
         hist_kwargs[KEY_RANGE()] = range_value
-    if density and not stacked:
-        hist_kwargs[KEY_DENSITY()] = 1
     return hist_kwargs
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                              stacked: bool, range_value: int) -> Dict[int, int]:
     # pre-conditions-start
     Requires(KEY_RANGE() != KEY_DENSITY())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(Result()))
@@ -103,7 +101,7 @@
     hist_kwargs = {}  # type: Dict[int, int]
     if not multi_precomputed:
         hist_kwargs[KEY_RANGE()] = range_value
-    if density and not stacked:
+    if density:
         hist_kwargs[KEY_DENSITY()] = 1
     return hist_kwargs
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                              stacked: bool, range_value: int) -> Dict[int, int]:
     # pre-conditions-start
     Requires(KEY_RANGE() != KEY_DENSITY())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(Result()))
@@ -102,7 +100,7 @@
     # impl-start
     hist_kwargs = {}  # type: Dict[int, int]
     if not multi_precomputed:
-        hist_kwargs[KEY_RANGE()] = range_value
+        hist_kwargs[KEY_RANGE()] = range_value + 1
     if density and not stacked:
         hist_kwargs[KEY_DENSITY()] = 1
     return hist_kwargs
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                              stacked: bool, range_value: int) -> Dict[int, int]:
     # pre-conditions-start
     Requires(KEY_RANGE() != KEY_DENSITY())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(Result()))
@@ -105,5 +103,6 @@
         hist_kwargs[KEY_RANGE()] = range_value
     if density and not stacked:
         hist_kwargs[KEY_DENSITY()] = 1
+    hist_kwargs[KEY_RANGE() + KEY_DENSITY() + 1] = 7
     return hist_kwargs
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                              stacked: bool, range_value: int) -> Dict[int, int]:
     # pre-conditions-start
     Requires(KEY_RANGE() != KEY_DENSITY())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(Result()))
@@ -104,6 +102,6 @@
     if not multi_precomputed:
         hist_kwargs[KEY_RANGE()] = range_value
     if density and not stacked:
-        hist_kwargs[KEY_DENSITY()] = 1
+        hist_kwargs[KEY_DENSITY()] = 0
     return hist_kwargs
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
                              stacked: bool, range_value: int) -> Dict[int, int]:
     # pre-conditions-start
     Requires(KEY_RANGE() != KEY_DENSITY())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(Result()))
@@ -101,7 +99,7 @@
     # post-conditions-end
     # impl-start
     hist_kwargs = {}  # type: Dict[int, int]
-    if not multi_precomputed:
+    if multi_precomputed:
         hist_kwargs[KEY_RANGE()] = range_value
     if density and not stacked:
         hist_kwargs[KEY_DENSITY()] = 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-13989.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A histogram-drawing routine assembles the keyword options it will forward to
  the underlying histogram computation into a single options mapping. Two
  options may be placed in that mapping:

    * an explicit value range, recorded under the range key. It is recorded
      exactly when the routine is responsible for constraining the binning to a
      given interval -- i.e. in the single-pass case where the bins are not
      pre-computed across several datasets. (In the multi-dataset pre-computed
      case the interval is folded into the pre-computed bins instead, so the
      range key is not placed in the mapping.)

    * a normalisation flag, recorded under the density key. It is recorded
      exactly when normalisation is requested and the datasets are not being
      stacked.

  The behaviour that matters: these two options are INDEPENDENT entries of the
  one mapping. Recording the normalisation flag must not disturb a range entry
  that was already placed: whenever the range was recorded, it remains present
  with its original value in the mapping that is finally forwarded, regardless
  of whether the normalisation flag is also recorded. Symmetrically, the
  normalisation flag is present exactly in the requested-and-not-stacked case
  and absent otherwise, and the range entry is present exactly in the
  single-pass case and absent otherwise.

Modelling choices (Nagini fragment):
  * The options mapping is a ``Dict[int, int]`` from an option-name token to its
    recorded value. ``KEY_RANGE``/``KEY_DENSITY`` are the two option-name
    tokens; only membership (is the option recorded) and per-option value are
    observed, so an integer carrier is faithful (mapping.md S2).
  * The routine builds and returns the freshly-created options mapping (a local
    that is assembled before being forwarded). The runtime conditions that
    select each branch -- whether the bins are pre-computed across several
    datasets, whether normalisation is requested, whether datasets are stacked
    -- are explicit boolean parameters. The range value to record is an opaque
    integer token (only its preservation is observed). The normalisation flag
    records as 1 when requested.

No string indexing is used (Nagini bans it). The behaviour is modelled deeply
(the mapping assembly is spelled out in the impl region); there is no
axiomatised callee. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import Dict
from nagini_contracts.contracts import *

# axioms-start
# No axioms: the mapping assembly is the behaviour under specification and is
# spelled out deeply in the impl region. There is no unchanged opaque callee to
# axiomatise (the downstream histogram computation that consumes the mapping is
# not modelled -- only the assembly of the mapping it receives is).
# axioms-end

# pure-start
@Pure
def KEY_RANGE() -> int:
    # Option-name token under which an explicit value range is recorded.
    return 0

@Pure
def KEY_DENSITY() -> int:
    # Option-name token under which the normalisation flag is recorded.
    return 1
# pure-end

def assemble_binning_options(multi_precomputed: bool, density: bool,
                             stacked: bool, range_value: int) -> Dict[int, int]:
    # pre-conditions-start
    Requires(KEY_RANGE() != KEY_DENSITY())
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(Result()))
    # The range entry is present exactly in the single-pass case, and when it
    # is present it carries exactly the supplied range value. Crucially this
    # holds REGARDLESS of whether the normalisation flag is also recorded: a
    # recorded range survives the recording of the density flag.
    Ensures(Implies(not multi_precomputed,
                    KEY_RANGE() in Result()
                    and Result()[KEY_RANGE()] == range_value))
    Ensures(Implies(multi_precomputed, not (KEY_RANGE() in Result())))
    # The normalisation flag is present exactly when normalisation is requested
    # and the datasets are not stacked, and then records as 1.
    Ensures(Implies(density and not stacked,
                    KEY_DENSITY() in Result()
                    and Result()[KEY_DENSITY()] == 1))
    Ensures(Implies(not (density and not stacked),
                    not (KEY_DENSITY() in Result())))
    # The forwarded mapping contains only the two recognised option entries:
    # every key present is the range key or the density key, never any other.
    Ensures(Forall(int, lambda k: Implies(k in Result(),
                    k == KEY_RANGE() or k == KEY_DENSITY())))
    # post-conditions-end
    # impl-start
    hist_kwargs = {}  # type: Dict[int, int]
    if not multi_precomputed:
        hist_kwargs[KEY_RANGE()] = range_value
    if density and not stacked:
        hist_kwargs[KEY_DENSITY()] = 1
    return hist_kwargs
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. matplotlib__matplotlib-13989 nagini. Ran with SBU_BENCHMARK_DIR=benchmark-verified (stated root absent on host). Verifier: python -m swebench_unified.adversary.

SPEC TOTALITY: assemble_binning_options postconditions FULLY determine the output Dict[int,int] for every input: KEY_RANGE present iff (not multi_precomputed) carrying exactly range_value; KEY_DENSITY present iff (density and not stacked) carrying exactly 1; plus a Forall closure clause banning any third key. A total spec => any same-spec verifying impl equals gold behaviour, so no verify-not-correct gap expected. Attacked with 7 DISTINCT wrong impls (impl-region-only edits; axioms/@Pure/Requires/Ensures byte-identical; all 7 confirmed same-spec SAME).

atk_1 PREPATCH-BUG (density branch rebinds hist_kwargs to fresh 1-key dict, dropping range): EXIT=2 NOT-A-COUNTEREXAMPLE (verification failed). Impl region byte-identical (modulo comments) to bundle model_prepatch.py; that file independently fails nagini_verify on the range-survival clause (prepatch_reproduced=true).
- atk_2 PARTIAL-DOMAIN (never records density flag): EXIT=2 rejected.
- atk_3 BOUNDARY (drops the `not stacked` guard: records density on `if density`): EXIT=2 rejected.
- atk_4 CONTROL-FLOW-EFFECT (records range_value+1, wrong value): EXIT=2 rejected.
- atk_5 EXTRA-KEY (adds a third option key, violating Forall closure): EXIT=2 rejected.
- atk_6 UNGROUNDED-ORACLE ECHO (stores density flag as 0 not 1): EXIT=2 rejected.
- atk_7 INVERTED-CONDITION (records range in multi_precomputed case): EXIT=2 rejected.
No attack came back CANDIDATE, so per protocol no faithful-patch resolve runs were triggered (step 2 only applies to verifying attacks).

POSITIVE CONTROL: pc_correct.py (bundle model.py verbatim) weakness EXIT=0 CANDIDATE (shares spec AND verifies, 12.2s) — its refined patch is the gold patch, which resolves (G-RESOLVE).

REFINEMENT.MD AUDIT: legs A1-A4 all R/I under a single A-reference (deep-model kwargs assembly); refinement.md §C explicitly declares NO kind-3 and NO A-consumed rows, consistent with model.py (empty axioms block, no @ContractOnly). A-reference correspondence to the real Axes.hist kwargs assembly + real numpy.histogram validated by G-AX: ran axiom_check.py (numpy 1.26.4) -> exit 0 ('G-AX OK ... deep model == real Axes.hist assembly on 8 boundary + 5000 fuzz tuples; base_commit rebind drops range in F2P config; real numpy.histogram spans interval iff range preserved'). The A-reference maps 'range'<->KEY_RANGE, 'density'<->KEY_DENSITY, multi_precomputed<->(not input_empty and len(x)>1) faithfully.

CONCLUSION: every same-spec wrong impl is rejected by the verifier (no verifying wrong impl exists to materialize/resolve), positive control verifies, prepatch reproduced, G-AX sound, refinement legs clean. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pc_correct.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-13989.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A histogram-drawing routine assembles the keyword options it will forward to
  the underlying histogram computation into a single options mapping. Two
  options may be placed in that mapping:

    * an explicit value range, recorded under the range key. It is recorded
      exactly when the routine is responsible for constraining the binning to a
      given interval -- i.e. in the single-pass case where the bins are not
      pre-computed across several datasets. (In the multi-dataset pre-computed
      case the interval is folded into the pre-computed bins instead, so the
      range key is not placed in the mapping.)

    * a normalisation flag, recorded under the density key. It is recorded
      exactly when normalisation is requested and the datasets are not being
      stacked.

  The behaviour that matters: these two options are INDEPENDENT entries of the
  one mapping. Recording the normalisation flag must not disturb a range entry
  that was already placed: whenever the range was recorded, it remains present
  with its original value in the mapping that is finally forwarded, regardless
  of whether the normalisation flag is also recorded. Symmetrically, the
  normalisation flag is present exactly in the requested-and-not-stacked case
  and absent otherwise, and the range entry is present exactly in the
  single-pass case and absent otherwise.

Modelling choices (Nagini fragment):
  * The options mapping is a ``Dict[int, int]`` from an option-name token to its
    recorded value. ``KEY_RANGE``/``KEY_DENSITY`` are the two option-name
    tokens; only membership (is the option recorded) and per-option value are
    observed, so an integer carrier is faithful (mapping.md S2).
  * The routine builds and returns the freshly-created options mapping (a local
    that is assembled before being forwarded). The runtime conditions that
    select each branch -- whether the bins are pre-computed across several
    datasets, whether normalisation is requested, whether datasets are stacked
    -- are explicit boolean parameters. The range value to record is an opaque
    integer token (only its preservation is observed). The normalisation flag
    records as 1 when requested.

No string indexing is used (Nagini bans it). The behaviour is modelled deeply
(the mapping assembly is spelled out in the impl region); there is no
axiomatised callee. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import Dict
from nagini_contracts.contracts import *

# axioms-start
# No axioms: the mapping assembly is the behaviour under specification and is
# spelled out deeply in the impl region. There is no unchanged opaque callee to
# axiomatise (the downstream histogram computation that consumes the mapping is
# not modelled -- only the assembly of the mapping it receives is).
# axioms-end

# pure-start
@Pure
def KEY_RANGE() -> int:
    # Option-name token under which an explicit value range is recorded.
    return 0

@Pure
def KEY_DENSITY() -> int:
    # Option-name token under which the normalisation flag is recorded.
    return 1
# pure-end

def assemble_binning_options(multi_precomputed: bool, density: bool,
                             stacked: bool, range_value: int) -> Dict[int, int]:
    # pre-conditions-start
    Requires(KEY_RANGE() != KEY_DENSITY())
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(Result()))
    # The range entry is present exactly in the single-pass case, and when it
    # is present it carries exactly the supplied range value. Crucially this
    # holds REGARDLESS of whether the normalisation flag is also recorded: a
    # recorded range survives the recording of the density flag.
    Ensures(Implies(not multi_precomputed,
                    KEY_RANGE() in Result()
                    and Result()[KEY_RANGE()] == range_value))
    Ensures(Implies(multi_precomputed, not (KEY_RANGE() in Result())))
    # The normalisation flag is present exactly when normalisation is requested
    # and the datasets are not stacked, and then records as 1.
    Ensures(Implies(density and not stacked,
                    KEY_DENSITY() in Result()
                    and Result()[KEY_DENSITY()] == 1))
    Ensures(Implies(not (density and not stacked),
                    not (KEY_DENSITY() in Result())))
    # The forwarded mapping contains only the two recognised option entries:
    # every key present is the range key or the density key, never any other.
    Ensures(Forall(int, lambda k: Implies(k in Result(),
                    k == KEY_RANGE() or k == KEY_DENSITY())))
    # post-conditions-end
    # impl-start
    hist_kwargs = {}  # type: Dict[int, int]
    if not multi_precomputed:
        hist_kwargs[KEY_RANGE()] = range_value
    if density and not stacked:
        hist_kwargs[KEY_DENSITY()] = 1
    return hist_kwargs
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. matplotlib__matplotlib-13989 nagini. Ran with SBU_BENCHMARK_DIR=benchmark-verified (stated root absent on host). Verifier: python -m swebench_unified.adversary.

SPEC TOTALITY: assemble_binning_options postconditions FULLY determine the output Dict[int,int] for every input: KEY_RANGE present iff (not multi_precomputed) carrying exactly range_value; KEY_DENSITY present iff (density and not stacked) carrying exactly 1; plus a Forall closure clause banning any third key. A total spec => any same-spec verifying impl equals gold behaviour, so no verify-not-correct gap expected. Attacked with 7 DISTINCT wrong impls (impl-region-only edits; axioms/@Pure/Requires/Ensures byte-identical; all 7 confirmed same-spec SAME).

atk_1 PREPATCH-BUG (density branch rebinds hist_kwargs to fresh 1-key dict, dropping range): EXIT=2 NOT-A-COUNTEREXAMPLE (verification failed). Impl region byte-identical (modulo comments) to bundle model_prepatch.py; that file independently fails nagini_verify on the range-survival clause (prepatch_reproduced=true).
- atk_2 PARTIAL-DOMAIN (never records density flag): EXIT=2 rejected.
- atk_3 BOUNDARY (drops the `not stacked` guard: records density on `if density`): EXIT=2 rejected.
- atk_4 CONTROL-FLOW-EFFECT (records range_value+1, wrong value): EXIT=2 rejected.
- atk_5 EXTRA-KEY (adds a third option key, violating Forall closure): EXIT=2 rejected.
- atk_6 UNGROUNDED-ORACLE ECHO (stores density flag as 0 not 1): EXIT=2 rejected.
- atk_7 INVERTED-CONDITION (records range in multi_precomputed case): EXIT=2 rejected.
No attack came back CANDIDATE, so per protocol no faithful-patch resolve runs were triggered (step 2 only applies to verifying attacks).

POSITIVE CONTROL: pc_correct.py (bundle model.py verbatim) weakness EXIT=0 CANDIDATE (shares spec AND verifies, 12.2s) — its refined patch is the gold patch, which resolves (G-RESOLVE).

REFINEMENT.MD AUDIT: legs A1-A4 all R/I under a single A-reference (deep-model kwargs assembly); refinement.md §C explicitly declares NO kind-3 and NO A-consumed rows, consistent with model.py (empty axioms block, no @ContractOnly). A-reference correspondence to the real Axes.hist kwargs assembly + real numpy.histogram validated by G-AX: ran axiom_check.py (numpy 1.26.4) -> exit 0 ('G-AX OK ... deep model == real Axes.hist assembly on 8 boundary + 5000 fuzz tuples; base_commit rebind drops range in F2P config; real numpy.histogram spans interval iff range preserved'). The A-reference maps 'range'<->KEY_RANGE, 'density'<->KEY_DENSITY, multi_precomputed<->(not input_empty and len(x)>1) faithfully.

CONCLUSION: every same-spec wrong impl is rejected by the verifier (no verifying wrong impl exists to materialize/resolve), positive control verifies, prepatch reproduced, G-AX sound, refinement legs clean. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence; spec is faithful to the real patched Axes.hist. Evidence: (1) model.py verifies under pinned Nagini (exit 0, 11.9s); (2) adversary same-spec confirms the model shares the bundle's exact spec region (exit 0). Spec target: the assembly of hist_kwargs forwarded to np.histogram in the patched Axes.hist (lib/matplotlib/axes/_axes.py, base_commit a3e2897bfa). Gold one-liner: `hist_kwargs = dict(density=density)` -> `hist_kwargs['density'] = density` (in-place write preserving the previously-recorded 'range' entry). The model's 4 postconditions: (a) range key present iff not multi_precomputed, carrying the supplied range_value (preservation only); (b) multi_precomputed => range key absent; (c) density key present iff (density and not stacked), value 1; (d) only {KEY_RANGE, KEY_DENSITY} keys ever present. The three boolean params map to resolved runtime conditions per mapping.md: multi_precomputed = (not input_empty and nx>1); density = bool(density) or bool(normed); stacked = stacked_arg or histtype=='barstacked'. I faithfully transcribed the real assembly (lines 6604-6698) over abstract inputs and cross-checked vs the spec: EXHAUSTIVE sweep over all discrete combos of (input_empty, nx in 0..3, density_arg in {None,False,True}, normed_arg in {None,True} excluding the simultaneous-ValueError path, stacked_arg, histtype in {bar,barstacked,step}) = 0 divergences; and 200,000 random fuzz inputs = 0 divergences. The conformance_check.py drives the REAL method via a capture-and-abort np.histogram wrapper and is well-constructed (1e5 fuzz + boundary, seed 13989). Could not execute the compiled matplotlib at base_commit directly (py3.11 wheel/build unavailable; source tree lacks compiled ext), so empirical validation used a faithful transcription of the branch logic rather than a live import; the logic is simple, self-contained, and the trace/mapping.md are internally consistent. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `hist_kwargs = dict(density=density)` -> `hist_kwargs['density'] = density` (density branch must write in-place, not rebind, so a previously recorded 'range' key survives into the forwarded kwargs). The public problem_statement already discloses the ENTIRE discriminating behavior: title 'hist() no longer respects range=... when density=True', a repro `plt.hist(np.random.rand(10),"auto",range=(0,1),density=True)`, expected bins spanning [0,1], and 'this bug doesn't happen if density=False'. So the range<->density interaction is fully public.

Spec-view assessment:

(1) Mechanical G-LEAK screen (leakage.screen over spec_view) PASSES — no diff markers, no gold-patch line reproduced (changed lines `hist_kwargs = dict(density=density)` / `hist_kwargs['density'] = density` do not appear in the view), no patched file path (lib/matplotlib/axes/_axes.py absent), no patched module dotted path, no spec-view identifier/comment echoing patched symbol 'hist' (the token 'hist' does not appear as a word in the view; and 'hist' is anyway public in the problem_statement), and no narration words (bug/fix/regression/broken/previously/incorrectly/wrong/patch).

(2) The impl region is ELIDED in the consumer view (`...  # implementation elided`), so the actual fix mechanism (rebind-vs-in-place) is NOT shown.

(3) The docstring and postconditions describe only the desired observable behavior ('recording the normalisation flag must not disturb a range entry already placed') via abstract int tokens KEY_RANGE/KEY_DENSITY; the words 'range' and 'density' are the public matplotlib API kwarg names named verbatim in the problem_statement.

(4) The rebind/mutation detail that constitutes the edit lives only in refinement.md / mapping.md, which are auditor docs, NOT the solver-visible spec view.

Conclusion: the spec view reveals only behavior the public issue already fully specifies, and does not disclose HOW to fix it beyond the problem_statement. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.