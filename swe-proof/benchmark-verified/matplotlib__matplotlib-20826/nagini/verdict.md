# P2 adversarial audit — matplotlib__matplotlib-20826

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(d), 1 / 2))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -87,7 +85,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -113,7 +110,7 @@
                                            k in tick_kw and Result()[k] == tick_kw[k]))))
     # post-conditions-end
     # impl-start
-    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
+    result = {}  # type: Dict[int, bool]
     result[refreshed_key()] = flag_enabled and selection_covers
     return result
     # impl-end
@@ -126,7 +123,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -144,7 +140,7 @@
                                            k in tick_kw and Result()[k] == tick_kw[k]))))
     # post-conditions-end
     # impl-start
-    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
+    result = {}  # type: Dict[int, bool]
     result[refreshed_key()] = flag_enabled and selection_covers
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(d), 1 / 2))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -87,7 +85,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -114,7 +111,7 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    result[refreshed_key()] = flag_enabled or selection_covers
     return result
     # impl-end
 
@@ -126,7 +123,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -145,6 +141,6 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    result[refreshed_key()] = flag_enabled or selection_covers
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(d), 1 / 2))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -87,7 +85,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -114,7 +111,7 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    result[refreshed_key()] = flag_enabled
     return result
     # impl-end
 
@@ -126,7 +123,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -145,6 +141,6 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    result[refreshed_key()] = flag_enabled
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(d), 1 / 2))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -87,7 +85,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -115,6 +112,7 @@
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
     result[refreshed_key()] = flag_enabled and selection_covers
+    result[1] = flag_enabled and selection_covers
     return result
     # impl-end
 
@@ -126,7 +124,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -146,5 +143,6 @@
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
     result[refreshed_key()] = flag_enabled and selection_covers
+    result[1] = flag_enabled and selection_covers
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(d), 1 / 2))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -87,7 +85,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -114,7 +111,8 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    if flag_enabled and selection_covers:
+        result[refreshed_key()] = True
     return result
     # impl-end
 
@@ -126,7 +124,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -145,6 +142,7 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    if flag_enabled and selection_covers:
+        result[refreshed_key()] = True
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(d), 1 / 2))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -87,7 +85,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -113,9 +110,8 @@
                                            k in tick_kw and Result()[k] == tick_kw[k]))))
     # post-conditions-end
     # impl-start
-    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
-    return result
+    tick_kw[refreshed_key()] = flag_enabled and selection_covers
+    return tick_kw
     # impl-end
 
 
@@ -126,7 +122,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -144,7 +139,6 @@
                                            k in tick_kw and Result()[k] == tick_kw[k]))))
     # post-conditions-end
     # impl-start
-    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
-    return result
+    tick_kw[refreshed_key()] = flag_enabled and selection_covers
+    return tick_kw
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(d), 1 / 2))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -87,7 +85,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -114,7 +111,8 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    grid_on = flag_enabled and selection_covers  # type: bool
+    result[refreshed_key()] = grid_on
     return result
     # impl-end
 
@@ -126,7 +124,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -145,6 +142,7 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    grid_on = flag_enabled and selection_covers  # type: bool
+    result[refreshed_key()] = grid_on
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(d), 1 / 2))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -87,7 +85,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -114,7 +111,7 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    result[refreshed_key()] = selection_covers and flag_enabled
     return result
     # impl-end
 
@@ -126,7 +123,6 @@
     # The input mapping is read-only (the result is a related mapping):
     # fractional permission (directive 5).
     Requires(Acc(dict_pred(tick_kw), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(tick_kw), 1 / 2))
@@ -145,6 +141,6 @@
     # post-conditions-end
     # impl-start
     result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
-    result[refreshed_key()] = flag_enabled and selection_covers
+    result[refreshed_key()] = selection_covers and flag_enabled
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-20826.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An axis keeps a mapping of tick-appearance settings (e.g. which sides show
  tick marks, whether tick labels are drawn, and other per-side visibility
  flags). When the axis is re-initialised for re-use, exactly one designated
  appearance entry of that mapping is refreshed from two ambient configuration
  flags -- the entry is on exactly when the first flag is enabled AND the
  configured selection covers this mapping's tick class -- WHILE every other
  previously-established entry of the mapping is preserved exactly as it was.

  The consequence that matters: settings a caller has stored to hide tick marks
  and tick labels on one side (as happens for the inner members of a set of
  linked, shared axes) survive re-initialisation. Re-initialising the axis
  refreshes only the one designated entry; it does not discard the other
  appearance entries and therefore does not cause ticks or tick labels that
  should be hidden to reappear.

  There are two such mappings -- one for the major tick class, one for the minor
  tick class. They are re-initialised identically except for which selection
  covers them: the major mapping's designated entry is on when the selection is
  the all-inclusive one or the major one; the minor mapping's designated entry
  is on when the selection is the all-inclusive one or the minor one.

Modelling choices (Nagini fragment):
  * Each tick-appearance mapping is a ``Dict[int, bool]`` from a setting-name
    token to its on/off value; only key membership and the boolean values are
    observed, so integer-keyed identity is the faithful carrier (mapping.md
    section 2). The designated refreshed entry is the module-level constant
    ``refreshed_key()``; any other setting (e.g. a side-hiding tick/label
    visibility flag) is a distinct key.
  * Re-initialisation yields the new tick-appearance mapping (the resulting
    state), so each operation RETURNS a ``Dict[int, bool]`` and reads its input
    mapping only (held at fractional permission, directive 5 -- the result is a
    related mapping, the input itself is not observed mutated).
  * The two ambient configuration flags are ``bool`` parameters: ``flag_enabled``
    (the first ambient flag) and ``selection_covers`` (the configured selection
    covers this mapping's tick class). booleans need no permission. The computed
    designated value is ``flag_enabled and selection_covers`` -- exactly the
    conjunction the configuration prescribes.
  * ``dict_carry_over`` is the unchanged mapping-copy primitive (a fresh mapping
    with the same key/value content as its argument); it is axiomatized and its
    soundness is checked against the real copy primitive out-of-band by
    axiom_check.py (G-AX). It is the WEAKEST contract the proof needs.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
@ContractOnly
def dict_carry_over(d: Dict[int, bool]) -> Dict[int, bool]:
    """The unchanged mapping-copy primitive: returns a FRESH mapping with the
    same key/value content as ``d`` -- every key carried over with its value and
    no key introduced; ``d`` is read-only. Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(d), 1 / 2))
    Ensures(Acc(dict_pred(d), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    Ensures(Forall(int, lambda k: (Implies(k in d,
                                           k in Result() and Result()[k] == d[k]))))
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
                                           k in d and Result()[k] == d[k]))))
# axioms-end


# pure-start
@Pure
def refreshed_key() -> int:
    # The setting-name token for the one designated entry that is refreshed.
    return 0
# pure-end


def reinit_tick_kw_major(tick_kw: Dict[int, bool],
                         flag_enabled: bool,
                         selection_covers: bool) -> Dict[int, bool]:
    # pre-conditions-start
    # The input mapping is read-only (the result is a related mapping):
    # fractional permission (directive 5).
    Requires(Acc(dict_pred(tick_kw), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(tick_kw), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # (1) The one designated entry is present on exit and equals the prescribed
    #     conjunction: the first ambient flag is enabled AND the configured
    #     selection covers this (major) tick class.
    Ensures(refreshed_key() in Result())
    Ensures(Result()[refreshed_key()] == (flag_enabled and selection_covers))
    # (2) Every OTHER entry present on entry is preserved exactly -- present in
    #     the result with the same value. This is the survival guarantee:
    #     appearance settings (e.g. a side-hiding tick/label flag) stored before
    #     re-initialisation are not discarded. An implementation that drops them
    #     cannot verify.
    Ensures(Forall(int, lambda k: (Implies(k in tick_kw and k != refreshed_key(),
                                           k in Result() and Result()[k] == tick_kw[k]))))
    # (3) The result introduces no entry other than the designated entry:
    #     any key in the result other than the designated key was present on
    #     entry with the same value. Stated forward so it constrains spurious
    #     additions.
    Ensures(Forall(int, lambda k: (Implies(k in Result() and k != refreshed_key(),
                                           k in tick_kw and Result()[k] == tick_kw[k]))))
    # post-conditions-end
    # impl-start
    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
    result[refreshed_key()] = flag_enabled and selection_covers
    return result
    # impl-end


def reinit_tick_kw_minor(tick_kw: Dict[int, bool],
                         flag_enabled: bool,
                         selection_covers: bool) -> Dict[int, bool]:
    # pre-conditions-start
    # The input mapping is read-only (the result is a related mapping):
    # fractional permission (directive 5).
    Requires(Acc(dict_pred(tick_kw), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(tick_kw), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # (1) The one designated entry is present on exit and equals the prescribed
    #     conjunction for the minor tick class.
    Ensures(refreshed_key() in Result())
    Ensures(Result()[refreshed_key()] == (flag_enabled and selection_covers))
    # (2) Every OTHER entry present on entry is preserved exactly.
    Ensures(Forall(int, lambda k: (Implies(k in tick_kw and k != refreshed_key(),
                                           k in Result() and Result()[k] == tick_kw[k]))))
    # (3) The result introduces no entry other than the designated entry.
    Ensures(Forall(int, lambda k: (Implies(k in Result() and k != refreshed_key(),
                                           k in tick_kw and Result()[k] == tick_kw[k]))))
    # post-conditions-end
    # impl-start
    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
    result[refreshed_key()] = flag_enabled and selection_covers
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Project root, SBU_BENCHMARK_DIR=benchmark-verified, verifier via python -m swebench_unified.adversary. All 8 attacks share the spec byte-for-byte outside the impl region (verified by diffing non-impl regions against model.py; positive control same-spec EXIT 0).

WEAKNESS RESULTS (cmd: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-20826 <atk>`), run concurrently in batches of 3 (each spawns JVM+Z3):
 - atk_1 PREPATCH bug (result={}; drops other keys): EXIT 2 does-not-verify. Direct verify shows it fails EXACTLY postcondition clause (2) preservation on BOTH sites (reinit_tick_kw_major/minor) — G-DIFF sensed, prepatch reproduced.
 - atk_2 OR instead of AND: EXIT 2 (fails clause 1).
 - atk_3 partial-domain (value=flag_enabled only): EXIT 2 (fails clause 1 when selection_covers false).
 - atk_4 spurious key introduced (result[1]=...): EXIT 2 (fails clause 3).
 - atk_5 control-flow-effect (set grid key only when conjunction true): EXIT 2 (fails clause 1 present/value when false).
 - atk_6 ungrounded/aliasing: mutate input tick_kw held at 1/2 permission and return it: EXIT 2 (fails to verify — insufficient permission / read-only violation).
 - atk_7 EQUIVALENT (temp bool var): EXIT 0 CANDIDATE (verifies 15.5s).
 - atk_8 EQUIVALENT (commuted conjunction selection_covers and flag_enabled): EXIT 0 CANDIDATE (verifies 15.5s).

Positive control (unmodified model.py): verify VERIFIED 15.1s.

MANDATORY RESOLVE STEP for the 2 CANDIDATEs: materialized faithful refined patches (mapping.md correspondence refreshed_key->gridOn, flag_enabled->rcParams['axes.grid'], selection_covers->which in ('both','major'/'minor')) and ran the official harness swebench_unified.harness.run_resolve (timeout 1800, retries 1) alongside a gold baseline:
 - gold: resolved=True, FAIL_TO_PASS success=1 fail=0 (baseline harness sanity — image/oracle work).
 - atk_7 faithful patch: resolved=True, FAIL_TO_PASS success=1 fail=0 — DOES resolve, does NOT break the spec.
 - atk_8 faithful patch: resolved=True, FAIL_TO_PASS success=1 fail=0 — DOES resolve, does NOT break the spec.

Both verifying candidates are behaviorally identical to gold (temp-var / commuted AND), so their patches resolve — the correct SOUND outcome (no verify AND NOT resolve). No verify-but-wrong impl found.

WHY NO WEAKNESS EXISTS: the spec is a COMPLETE functional spec — the three postconditions per function pin the observable output content exactly: (1) key refreshed_key() present with value == (flag_enabled and selection_covers); (2) every other input key preserved with same value; (3) no key other than refreshed_key() beyond those preserved. Any verifying impl must be content-identical to gold on all inputs, so verify=>correct.

REFINEMENT.MD A-LEG AUDIT: legs A1 (param, R str->int token), A2 (dict_carry_over, A-reference — deep model of the UNCHANGED dict(d)/d.copy() primitive, validated == real primitive by axiom_check.py/G-AX; correspondence holds: gold preserves keys by in-place mutation, model by fresh equal mapping, consumer _get_tick reads by content not identity), A3 (grid-key assignment, R+I — token<->gridOn, conjunction identical), A4 (return result <-> mutated object left, R). No kind-3 unexpressible-changed-op step; the genuinely-changed operation is modeled DEEPLY (explicit carry-over + assignment with preservation postconditions), not hidden behind a consumed axiom. The one axiom covers an unchanged language primitive and is A-reference. Correspondence to the real callees holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-20826.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An axis keeps a mapping of tick-appearance settings (e.g. which sides show
  tick marks, whether tick labels are drawn, and other per-side visibility
  flags). When the axis is re-initialised for re-use, exactly one designated
  appearance entry of that mapping is refreshed from two ambient configuration
  flags -- the entry is on exactly when the first flag is enabled AND the
  configured selection covers this mapping's tick class -- WHILE every other
  previously-established entry of the mapping is preserved exactly as it was.

  The consequence that matters: settings a caller has stored to hide tick marks
  and tick labels on one side (as happens for the inner members of a set of
  linked, shared axes) survive re-initialisation. Re-initialising the axis
  refreshes only the one designated entry; it does not discard the other
  appearance entries and therefore does not cause ticks or tick labels that
  should be hidden to reappear.

  There are two such mappings -- one for the major tick class, one for the minor
  tick class. They are re-initialised identically except for which selection
  covers them: the major mapping's designated entry is on when the selection is
  the all-inclusive one or the major one; the minor mapping's designated entry
  is on when the selection is the all-inclusive one or the minor one.

Modelling choices (Nagini fragment):
  * Each tick-appearance mapping is a ``Dict[int, bool]`` from a setting-name
    token to its on/off value; only key membership and the boolean values are
    observed, so integer-keyed identity is the faithful carrier (mapping.md
    section 2). The designated refreshed entry is the module-level constant
    ``refreshed_key()``; any other setting (e.g. a side-hiding tick/label
    visibility flag) is a distinct key.
  * Re-initialisation yields the new tick-appearance mapping (the resulting
    state), so each operation RETURNS a ``Dict[int, bool]`` and reads its input
    mapping only (held at fractional permission, directive 5 -- the result is a
    related mapping, the input itself is not observed mutated).
  * The two ambient configuration flags are ``bool`` parameters: ``flag_enabled``
    (the first ambient flag) and ``selection_covers`` (the configured selection
    covers this mapping's tick class). booleans need no permission. The computed
    designated value is ``flag_enabled and selection_covers`` -- exactly the
    conjunction the configuration prescribes.
  * ``dict_carry_over`` is the unchanged mapping-copy primitive (a fresh mapping
    with the same key/value content as its argument); it is axiomatized and its
    soundness is checked against the real copy primitive out-of-band by
    axiom_check.py (G-AX). It is the WEAKEST contract the proof needs.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
@ContractOnly
def dict_carry_over(d: Dict[int, bool]) -> Dict[int, bool]:
    """The unchanged mapping-copy primitive: returns a FRESH mapping with the
    same key/value content as ``d`` -- every key carried over with its value and
    no key introduced; ``d`` is read-only. Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(d), 1 / 2))
    Ensures(Acc(dict_pred(d), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    Ensures(Forall(int, lambda k: (Implies(k in d,
                                           k in Result() and Result()[k] == d[k]))))
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
                                           k in d and Result()[k] == d[k]))))
# axioms-end


# pure-start
@Pure
def refreshed_key() -> int:
    # The setting-name token for the one designated entry that is refreshed.
    return 0
# pure-end


def reinit_tick_kw_major(tick_kw: Dict[int, bool],
                         flag_enabled: bool,
                         selection_covers: bool) -> Dict[int, bool]:
    # pre-conditions-start
    # The input mapping is read-only (the result is a related mapping):
    # fractional permission (directive 5).
    Requires(Acc(dict_pred(tick_kw), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(tick_kw), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # (1) The one designated entry is present on exit and equals the prescribed
    #     conjunction: the first ambient flag is enabled AND the configured
    #     selection covers this (major) tick class.
    Ensures(refreshed_key() in Result())
    Ensures(Result()[refreshed_key()] == (flag_enabled and selection_covers))
    # (2) Every OTHER entry present on entry is preserved exactly -- present in
    #     the result with the same value. This is the survival guarantee:
    #     appearance settings (e.g. a side-hiding tick/label flag) stored before
    #     re-initialisation are not discarded. An implementation that drops them
    #     cannot verify.
    Ensures(Forall(int, lambda k: (Implies(k in tick_kw and k != refreshed_key(),
                                           k in Result() and Result()[k] == tick_kw[k]))))
    # (3) The result introduces no entry other than the designated entry:
    #     any key in the result other than the designated key was present on
    #     entry with the same value. Stated forward so it constrains spurious
    #     additions.
    Ensures(Forall(int, lambda k: (Implies(k in Result() and k != refreshed_key(),
                                           k in tick_kw and Result()[k] == tick_kw[k]))))
    # post-conditions-end
    # impl-start
    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
    result[refreshed_key()] = flag_enabled and selection_covers
    return result
    # impl-end


def reinit_tick_kw_minor(tick_kw: Dict[int, bool],
                         flag_enabled: bool,
                         selection_covers: bool) -> Dict[int, bool]:
    # pre-conditions-start
    # The input mapping is read-only (the result is a related mapping):
    # fractional permission (directive 5).
    Requires(Acc(dict_pred(tick_kw), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(tick_kw), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # (1) The one designated entry is present on exit and equals the prescribed
    #     conjunction for the minor tick class.
    Ensures(refreshed_key() in Result())
    Ensures(Result()[refreshed_key()] == (flag_enabled and selection_covers))
    # (2) Every OTHER entry present on entry is preserved exactly.
    Ensures(Forall(int, lambda k: (Implies(k in tick_kw and k != refreshed_key(),
                                           k in Result() and Result()[k] == tick_kw[k]))))
    # (3) The result introduces no entry other than the designated entry.
    Ensures(Forall(int, lambda k: (Implies(k in Result() and k != refreshed_key(),
                                           k in tick_kw and Result()[k] == tick_kw[k]))))
    # post-conditions-end
    # impl-start
    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
    result[refreshed_key()] = flag_enabled and selection_covers
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Project root, SBU_BENCHMARK_DIR=benchmark-verified, verifier via python -m swebench_unified.adversary. All 8 attacks share the spec byte-for-byte outside the impl region (verified by diffing non-impl regions against model.py; positive control same-spec EXIT 0).

WEAKNESS RESULTS (cmd: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-20826 <atk>`), run concurrently in batches of 3 (each spawns JVM+Z3):
 - atk_1 PREPATCH bug (result={}; drops other keys): EXIT 2 does-not-verify. Direct verify shows it fails EXACTLY postcondition clause (2) preservation on BOTH sites (reinit_tick_kw_major/minor) — G-DIFF sensed, prepatch reproduced.
 - atk_2 OR instead of AND: EXIT 2 (fails clause 1).
 - atk_3 partial-domain (value=flag_enabled only): EXIT 2 (fails clause 1 when selection_covers false).
 - atk_4 spurious key introduced (result[1]=...): EXIT 2 (fails clause 3).
 - atk_5 control-flow-effect (set grid key only when conjunction true): EXIT 2 (fails clause 1 present/value when false).
 - atk_6 ungrounded/aliasing: mutate input tick_kw held at 1/2 permission and return it: EXIT 2 (fails to verify — insufficient permission / read-only violation).
 - atk_7 EQUIVALENT (temp bool var): EXIT 0 CANDIDATE (verifies 15.5s).
 - atk_8 EQUIVALENT (commuted conjunction selection_covers and flag_enabled): EXIT 0 CANDIDATE (verifies 15.5s).

Positive control (unmodified model.py): verify VERIFIED 15.1s.

MANDATORY RESOLVE STEP for the 2 CANDIDATEs: materialized faithful refined patches (mapping.md correspondence refreshed_key->gridOn, flag_enabled->rcParams['axes.grid'], selection_covers->which in ('both','major'/'minor')) and ran the official harness swebench_unified.harness.run_resolve (timeout 1800, retries 1) alongside a gold baseline:
 - gold: resolved=True, FAIL_TO_PASS success=1 fail=0 (baseline harness sanity — image/oracle work).
 - atk_7 faithful patch: resolved=True, FAIL_TO_PASS success=1 fail=0 — DOES resolve, does NOT break the spec.
 - atk_8 faithful patch: resolved=True, FAIL_TO_PASS success=1 fail=0 — DOES resolve, does NOT break the spec.

Both verifying candidates are behaviorally identical to gold (temp-var / commuted AND), so their patches resolve — the correct SOUND outcome (no verify AND NOT resolve). No verify-but-wrong impl found.

WHY NO WEAKNESS EXISTS: the spec is a COMPLETE functional spec — the three postconditions per function pin the observable output content exactly: (1) key refreshed_key() present with value == (flag_enabled and selection_covers); (2) every other input key preserved with same value; (3) no key other than refreshed_key() beyond those preserved. Any verifying impl must be content-identical to gold on all inputs, so verify=>correct.

REFINEMENT.MD A-LEG AUDIT: legs A1 (param, R str->int token), A2 (dict_carry_over, A-reference — deep model of the UNCHANGED dict(d)/d.copy() primitive, validated == real primitive by axiom_check.py/G-AX; correspondence holds: gold preserves keys by in-place mutation, model by fresh equal mapping, consumer _get_tick reads by content not identity), A3 (grid-key assignment, R+I — token<->gridOn, conjunction identical), A4 (return result <-> mutated object left, R). No kind-3 unexpressible-changed-op step; the genuinely-changed operation is modeled DEEPLY (explicit carry-over + assignment with preservation postconditions), not hidden behind a consumed axiom. The one axiom covers an unchanged language primitive and is A-reference. Correspondence to the real callees holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacker role (2) faithfulness-break: sought an input where the modeled functions (reinit_tick_kw_major/minor) disagree with the real repo callee (Axis.clear's tick-keyword re-initialisation at base_commit a0d2e39). No such input exists.

Real behavior confirmed from the repo: gold patch replaces the two `_reset_*_tick_kw()` calls (each did `dict.clear()` then set only `gridOn`) with an IN-PLACE assignment `self._<which>_tick_kw['gridOn'] = mpl.rcParams['axes.grid'] and mpl.rcParams['axes.grid.which'] in ('both','<which>')`, leaving every other previously-stored key intact. This yields resulting mapping state = {all prior keys preserved} ∪ {gridOn := grids_on AND which_match}.

Model spec postconditions capture exactly this: (1) refreshed_key()==0 present with value (flag_enabled and selection_covers); (2) every other entry present on entry preserved with same value; (3) no key introduced other than refreshed_key(). This is neither too strong nor too weak vs the real content-level state — the consumer (_get_tick reads **tick_kw by content, not identity), so fresh-equal-mapping vs in-place mutation is observationally identical (mapping.md §2). str→int token abstraction is faithful (only key membership + boolean visibility values observed).

Evidence: model verifies (nagini_verify.sh exit 0, 15.8s); axiom_check.py exit 0 (boundary incl. side-hiding flags {tick1On,label1On}=False + 20000 fuzz, validates both dict_carry_over==dict(d) AND end-to-end fixed re-init, and that buggy empty-then-set differs whenever a non-grid key exists). Independent 200k-input differential sweep of the modeled function vs a faithful mirror of the gold operation: 0 divergences. Spec region byte-identical (untouched; only auditing, no bundle edits). No drift; the spec is faithful to the real callee on all inputs.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py projection only (mapping.md and refinement.md are explicitly auditor-only, non-consumer-visible per their own audit-doc notes and meta.json gates.G-LEAK). Mechanical G-LEAK screen PASSES (no diff markers, no reproduced gold line, no patched file path lib/matplotlib/axis.py, no narration terms, no spec-view identifier embedding the only distinctive changed symbol 'clear'). Gold edit: in Axis.clear, replace self._reset_{major,minor}_tick_kw() calls with in-place self._{major,minor}_tick_kw['gridOn'] = (mpl.rcParams['axes.grid'] and mpl.rcParams['axes.grid.which'] in ('both','major'/'minor')). The spec view is fully DE-NARRATED: gridOn->refreshed_key(), axes.grid->flag_enabled, the which-membership test->selection_covers; the strings 'gridOn','axes.grid','rcParams','_reset_*_tick_kw' and the file/module path never appear in model.py. Public problem_statement already discloses the observable behavior the spec encodes: ax.clear() wrongly un-hides shared-axis tick labels and adds ticks that should be hidden; expected outcome is that the hidden ticks/labels survive clear(). The spec's preservation guarantee (one designated entry refreshed WHILE all other entries preserved) is exactly the desired behavior implied by the public statement (hidden settings survive re-initialisation), not the edit mechanism. The 'value = conjunction of two ambient flags' clause abstractly pins the refreshed entry's correct value (needed for any sound spec) without naming grid/rcParams mechanics, so it does not enable gold-patch reconstruction beyond the public problem_statement. No spec-view line leaks the gold edit beyond problem_statement (hints_text not consulted, per policy).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
