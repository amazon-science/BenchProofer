# P2 adversarial audit — matplotlib__matplotlib-26208

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1_prepatch_h.py`, `atk_2_prepatch_v.py`, `atk_3_newdesc.py`, `atk_4_return_source.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5_conditional.py`, `atk_6_echo_reorg.py`, `atk_7_double_none.py` |

**Non-vacuity.** The positive control `model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_h.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -38,9 +37,6 @@
     """An opaque descriptor object. Only its object identity is observable."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present)
         self.present = True  # type: bool
 
@@ -50,9 +46,6 @@
     reference. A freshly constructed axis has no descriptor (None)."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.descriptor) and self.descriptor is None)
         self.descriptor = None  # type: Optional[UnitDescriptor]
 # pure-end
@@ -63,7 +56,6 @@
     # pre-conditions-start
     Requires(Acc(source_horizontal.descriptor, 1 / 2))
     Requires(source_horizontal.descriptor is not None)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_horizontal.descriptor, 1 / 2))
@@ -75,7 +67,6 @@
     # post-conditions-end
     # impl-start
     companion_horizontal = CoordinateAxis()
-    companion_horizontal.descriptor = source_horizontal.descriptor
     return companion_horizontal
     # impl-end
 
@@ -85,7 +76,6 @@
     # pre-conditions-start
     Requires(Acc(source_vertical.descriptor, 1 / 2))
     Requires(source_vertical.descriptor is not None)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_vertical.descriptor, 1 / 2))
```

Attack 2 — `atk_2_prepatch_v.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -38,9 +37,6 @@
     """An opaque descriptor object. Only its object identity is observable."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present)
         self.present = True  # type: bool
 
@@ -50,9 +46,6 @@
     reference. A freshly constructed axis has no descriptor (None)."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.descriptor) and self.descriptor is None)
         self.descriptor = None  # type: Optional[UnitDescriptor]
 # pure-end
@@ -63,7 +56,6 @@
     # pre-conditions-start
     Requires(Acc(source_horizontal.descriptor, 1 / 2))
     Requires(source_horizontal.descriptor is not None)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_horizontal.descriptor, 1 / 2))
@@ -85,7 +77,6 @@
     # pre-conditions-start
     Requires(Acc(source_vertical.descriptor, 1 / 2))
     Requires(source_vertical.descriptor is not None)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_vertical.descriptor, 1 / 2))
@@ -97,6 +88,5 @@
     # post-conditions-end
     # impl-start
     companion_vertical = CoordinateAxis()
-    companion_vertical.descriptor = source_vertical.descriptor
     return companion_vertical
     # impl-end
```

Attack 3 — `atk_3_newdesc.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -38,9 +37,6 @@
     """An opaque descriptor object. Only its object identity is observable."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present)
         self.present = True  # type: bool
 
@@ -50,9 +46,6 @@
     reference. A freshly constructed axis has no descriptor (None)."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.descriptor) and self.descriptor is None)
         self.descriptor = None  # type: Optional[UnitDescriptor]
 # pure-end
@@ -63,7 +56,6 @@
     # pre-conditions-start
     Requires(Acc(source_horizontal.descriptor, 1 / 2))
     Requires(source_horizontal.descriptor is not None)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_horizontal.descriptor, 1 / 2))
@@ -75,7 +67,7 @@
     # post-conditions-end
     # impl-start
     companion_horizontal = CoordinateAxis()
-    companion_horizontal.descriptor = source_horizontal.descriptor
+    companion_horizontal.descriptor = UnitDescriptor()
     return companion_horizontal
     # impl-end
 
@@ -85,7 +77,6 @@
     # pre-conditions-start
     Requires(Acc(source_vertical.descriptor, 1 / 2))
     Requires(source_vertical.descriptor is not None)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_vertical.descriptor, 1 / 2))
```

Attack 4 — `atk_4_return_source.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -38,9 +37,6 @@
     """An opaque descriptor object. Only its object identity is observable."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present)
         self.present = True  # type: bool
 
@@ -50,9 +46,6 @@
     reference. A freshly constructed axis has no descriptor (None)."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.descriptor) and self.descriptor is None)
         self.descriptor = None  # type: Optional[UnitDescriptor]
 # pure-end
@@ -63,7 +56,6 @@
     # pre-conditions-start
     Requires(Acc(source_horizontal.descriptor, 1 / 2))
     Requires(source_horizontal.descriptor is not None)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_horizontal.descriptor, 1 / 2))
@@ -74,9 +66,7 @@
     Ensures(Result().descriptor is not None)
     # post-conditions-end
     # impl-start
-    companion_horizontal = CoordinateAxis()
-    companion_horizontal.descriptor = source_horizontal.descriptor
-    return companion_horizontal
+    return source_horizontal
     # impl-end
 
 
@@ -85,7 +75,6 @@
     # pre-conditions-start
     Requires(Acc(source_vertical.descriptor, 1 / 2))
     Requires(source_vertical.descriptor is not None)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_vertical.descriptor, 1 / 2))
```

Attack 5 — `atk_5_conditional.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -38,9 +37,6 @@
     """An opaque descriptor object. Only its object identity is observable."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present)
         self.present = True  # type: bool
 
@@ -50,9 +46,6 @@
     reference. A freshly constructed axis has no descriptor (None)."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.descriptor) and self.descriptor is None)
         self.descriptor = None  # type: Optional[UnitDescriptor]
 # pure-end
@@ -63,7 +56,6 @@
     # pre-conditions-start
     Requires(Acc(source_horizontal.descriptor, 1 / 2))
     Requires(source_horizontal.descriptor is not None)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_horizontal.descriptor, 1 / 2))
@@ -75,7 +67,10 @@
     # post-conditions-end
     # impl-start
     companion_horizontal = CoordinateAxis()
-    companion_horizontal.descriptor = source_horizontal.descriptor
+    if source_horizontal.descriptor is not None:
+        companion_horizontal.descriptor = source_horizontal.descriptor
+    else:
+        companion_horizontal.descriptor = source_horizontal.descriptor
     return companion_horizontal
     # impl-end
 
@@ -85,7 +80,6 @@
     # pre-conditions-start
     Requires(Acc(source_vertical.descriptor, 1 / 2))
     Requires(source_vertical.descriptor is not None)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_vertical.descriptor, 1 / 2))
```

Attack 6 — `atk_6_echo_reorg.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -38,9 +37,6 @@
     """An opaque descriptor object. Only its object identity is observable."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present)
         self.present = True  # type: bool
 
@@ -50,9 +46,6 @@
     reference. A freshly constructed axis has no descriptor (None)."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.descriptor) and self.descriptor is None)
         self.descriptor = None  # type: Optional[UnitDescriptor]
 # pure-end
@@ -63,7 +56,6 @@
     # pre-conditions-start
     Requires(Acc(source_horizontal.descriptor, 1 / 2))
     Requires(source_horizontal.descriptor is not None)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_horizontal.descriptor, 1 / 2))
@@ -74,8 +66,9 @@
     Ensures(Result().descriptor is not None)
     # post-conditions-end
     # impl-start
+    shared_ref = source_horizontal.descriptor
     companion_horizontal = CoordinateAxis()
-    companion_horizontal.descriptor = source_horizontal.descriptor
+    companion_horizontal.descriptor = shared_ref
     return companion_horizontal
     # impl-end
 
@@ -85,7 +78,6 @@
     # pre-conditions-start
     Requires(Acc(source_vertical.descriptor, 1 / 2))
     Requires(source_vertical.descriptor is not None)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_vertical.descriptor, 1 / 2))
```

Attack 7 — `atk_7_double_none.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -38,9 +37,6 @@
     """An opaque descriptor object. Only its object identity is observable."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present)
         self.present = True  # type: bool
 
@@ -50,9 +46,6 @@
     reference. A freshly constructed axis has no descriptor (None)."""
 
     def __init__(self) -> None:
-        # level 1: the lowest level, so any obligated caller (level > 1) has
-        # room beneath it; the body is straight-line and loop-free.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.descriptor) and self.descriptor is None)
         self.descriptor = None  # type: Optional[UnitDescriptor]
 # pure-end
@@ -63,7 +56,6 @@
     # pre-conditions-start
     Requires(Acc(source_horizontal.descriptor, 1 / 2))
     Requires(source_horizontal.descriptor is not None)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_horizontal.descriptor, 1 / 2))
@@ -75,6 +67,7 @@
     # post-conditions-end
     # impl-start
     companion_horizontal = CoordinateAxis()
+    companion_horizontal.descriptor = UnitDescriptor()
     companion_horizontal.descriptor = source_horizontal.descriptor
     return companion_horizontal
     # impl-end
@@ -85,7 +78,6 @@
     # pre-conditions-start
     Requires(Acc(source_vertical.descriptor, 1 / 2))
     Requires(source_vertical.descriptor is not None)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(source_vertical.descriptor, 1 / 2))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `model.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-26208.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Each builder takes a source coordinate axis and returns a freshly built
  companion coordinate axis. When the source axis carries a non-None descriptor
  object, the returned companion axis must reference that very same descriptor
  object (reference identity, not merely an equal value), and therefore must
  itself be non-None.

  A newly constructed axis carries no descriptor (its descriptor is None).

The behaviour is exercised through two governed builder functions. Each is
modelled as its own contracted+implemented function, so each has its own
differential witness.

Modelling: a coordinate axis is a minimal object with only the touched field —
its descriptor reference. The descriptor itself is an opaque object whose only
relevant property is its identity, so it is modelled as a bare object
(`UnitDescriptor`); the specification pins reference identity (`is`), exactly
what the observable behaviour demands.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

# axioms-start
# (no axiomatized callees: the modelled change is a pure object-field
# propagation, spelled out directly; nothing the proof relies on is opaque.)
# axioms-end

# pure-start
class UnitDescriptor:
    """An opaque descriptor object. Only its object identity is observable."""

    def __init__(self) -> None:
        Ensures(Acc(self.present) and self.present)
        self.present = True  # type: bool

class CoordinateAxis:
    """A coordinate axis carrying only the touched field: its descriptor
    reference. A freshly constructed axis has no descriptor (None)."""

    def __init__(self) -> None:
        Ensures(Acc(self.descriptor) and self.descriptor is None)
        self.descriptor = None  # type: Optional[UnitDescriptor]
# pure-end

def build_companion_sharing_horizontal(
        source_horizontal: CoordinateAxis) -> CoordinateAxis:
    # pre-conditions-start
    Requires(Acc(source_horizontal.descriptor, 1 / 2))
    Requires(source_horizontal.descriptor is not None)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(source_horizontal.descriptor, 1 / 2))
    Ensures(source_horizontal.descriptor is not None)
    Ensures(Acc(Result().descriptor))
    # the companion's shared axis references the SAME descriptor object
    Ensures(Result().descriptor is source_horizontal.descriptor)
    Ensures(Result().descriptor is not None)
    # post-conditions-end
    # impl-start
    companion_horizontal = CoordinateAxis()
    companion_horizontal.descriptor = source_horizontal.descriptor
    return companion_horizontal
    # impl-end

def build_companion_sharing_vertical(
        source_vertical: CoordinateAxis) -> CoordinateAxis:
    # pre-conditions-start
    Requires(Acc(source_vertical.descriptor, 1 / 2))
    Requires(source_vertical.descriptor is not None)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(source_vertical.descriptor, 1 / 2))
    Ensures(source_vertical.descriptor is not None)
    Ensures(Acc(Result().descriptor))
    # the companion's shared axis references the SAME descriptor object
    Ensures(Result().descriptor is source_vertical.descriptor)
    Ensures(Result().descriptor is not None)
    # post-conditions-end
    # impl-start
    companion_vertical = CoordinateAxis()
    companion_vertical.descriptor = source_vertical.descriptor
    return companion_vertical
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Scratch dir Env: python (has swebench_unified),; run from project root.

SPEC UNDER TEST: two builder fns build_companion_sharing_{horizontal,vertical}; each postcondition pins EXACT reference identity Result().descriptor is source.descriptor AND Result().descriptor is not None AND full Acc(Result().descriptor), with only Acc(source.descriptor,1/2) incoming and precondition source.descriptor is not None. Genuine MULTI-SITE change (twinx x / twiny y): both fns must verify. Positive control model.py VERIFIES (10.05s) and is same-spec as itself.

COMMANDS (each attack): python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-26208 <path>. Results:
- atk_1_prepatch_h (omit copy at H, prepatch bug reproduced): EXIT 2 NOT-A-COUNTEREXAMPLE (does not verify — postcondition Result().descriptor is source fails). SPEC CAUGHT.
- atk_2_prepatch_v (omit copy at V): EXIT 2 (does not verify). SPEC CAUGHT.
- atk_3_newdesc (ungrounded-oracle style: companion.descriptor = fresh UnitDescriptor()): EXIT 2 (does not verify — identity to source fails). SPEC CAUGHT.
- atk_4_return_source (boundary/aliasing: return source_horizontal): EXIT 2 (does not verify — full Acc(Result().descriptor) unobtainable from 1/2 source permission). SPEC CAUGHT.
- atk_5_conditional (control-flow-effect: both branches copy source): EXIT 0 CANDIDATE (verifies 11.5s).
- atk_6_echo_reorg (intermediate-variable reorg of the copy): EXIT 0 CANDIDATE (verifies 11.2s).
- atk_7_double_none (dead write object() then copy source, last-write-wins): EXIT 0 CANDIDATE (verifies 10.3s).

RESOLVE on the 3 CANDIDATES' materialized faithful patches (run_resolve, official SWE-bench harness, matplotlib__matplotlib-26208, base_commit f0f133943d..., FAIL_TO_PASS test_twin_units[x,y]); all three diffs git-apply-check CLEAN at base_commit:
- atk_5_conditional -> resolved=True completed=True note='resolved'
- atk_6_echo_reorg  -> resolved=True completed=True note='resolved'
- atk_7_double_none -> resolved=True completed=True note='resolved'
All three are CORRECT ECHOES of the gold fix (each faithfully refines to ax2.<axis>.units = self.<axis>.units at both sites), so verify AND resolve => NOT spec weaknesses. No verifying same-spec impl produced a non-resolving faithful patch.

ATK_8_assume_vacuous (EXCLUDED from submitted attacks, reported for the record): impl `companion = CoordinateAxis(); Assume(companion.descriptor is source.descriptor); return companion`. adversary weakness returns EXIT 0 CANDIDATE (same-spec, verifies 10.4s) BECAUSE Assume injects the postcondition as an unproven fact. This is a BANNED-TOKEN cheat, NOT a spec weakness: nagini backend banned_tokens=('Assume(','Refute('); G-HYGIENE gates/hygiene.py _banned_calls rejects it (mechanically confirmed: atk_8 -> banned_calls=['Assume'] HYGIENE FAIL; atk_5/6/7 -> hygiene ok); prompts/nagini/quickref.md and worker.md forbid Assume/Refute.

It is a universal verifier-soundness defeat that would break EVERY Nagini spec identically, not evidence this spec is too weak; its faithful refinement is a runtime no-op (= prepatch, would not resolve), so submitting it would manufacture a spurious BROKEN against a sound spec. Deliberately withheld from `attacks`/`patches`. NOTE: the adversary `weakness` primitive and _derive_audit_verdict/check_attack do NOT screen banned tokens before the same-spec∧verify candidate check — reliance is on G-HYGIENE as a separate required gate; flagged for awareness but not a G-EQ defect.

REFINEMENT.MD A-LEG AUDIT: axioms region is EMPTY (confirmed model.py L29-32 + meta.json) => NO consumed @ContractOnly axiom, no A-consumed leg, no kind-3 trust point. Every leg in refinement.md tables is R (type refinement Axis<->CoordinateAxis, units<->descriptor, ax2.<axis>/self.<axis> <-> Result()/source) or I (H0/V0 unchanged builder body). The single A-REFERENCE — deep-model postcondition Result().descriptor is source.descriptor <=> gold hunk `ax2.<axis>.units = self.<axis>.units` — corresponds exactly to the real callee: the gold patch IS a reference-copy assignment at _base.py:4444 (twinx) / 4474 (twiny), and axiom_check.py (G-AX) validates it against real matplotlib twinx/twiny over 8 categorical scenarios (self-validating discrimination: patched vs prepatch regime). Correspondence HOLDS; corroborated independently by all three faithful echoes resolving. R/I legs are G-CONF's domain (not re-audited here per scope).

CONCLUSION: >=5 distinct wrong impls run (7 legitimate: 4 rejected by spec incl. prepatch bug at both sites, 3 verifying candidates all resolve). No verifying same-spec impl has a non-resolving faithful patch. A-legs sound (no consumed axiom; single A-reference corresponds to the real callee). => SOUND (verify => correct holds for this spec on the tested behaviour).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1_prepatch_h.py`, `atk_2_prepatch_v.py`, `atk_3_newdesc.py`, `atk_4_return_source.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5_conditional.py`, `atk_6_echo_reorg.py`, `atk_7_double_none.py` |

**Non-vacuity.** The positive control `model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch_h.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_prepatch_v.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_newdesc.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_return_source.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_conditional.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_echo_reorg.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_double_none.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `model.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-26208.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Each builder takes a source coordinate axis and returns a freshly built
  companion coordinate axis. When the source axis carries a non-None descriptor
  object, the returned companion axis must reference that very same descriptor
  object (reference identity, not merely an equal value), and therefore must
  itself be non-None.

  A newly constructed axis carries no descriptor (its descriptor is None).

The behaviour is exercised through two governed builder functions. Each is
modelled as its own contracted+implemented function, so each has its own
differential witness.

Modelling: a coordinate axis is a minimal object with only the touched field —
its descriptor reference. The descriptor itself is an opaque object whose only
relevant property is its identity, so it is modelled as a bare object
(`UnitDescriptor`); the specification pins reference identity (`is`), exactly
what the observable behaviour demands.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

# axioms-start
# (no axiomatized callees: the modelled change is a pure object-field
# propagation, spelled out directly; nothing the proof relies on is opaque.)
# axioms-end

# pure-start
class UnitDescriptor:
    """An opaque descriptor object. Only its object identity is observable."""

    def __init__(self) -> None:
        Ensures(Acc(self.present) and self.present)
        self.present = True  # type: bool

class CoordinateAxis:
    """A coordinate axis carrying only the touched field: its descriptor
    reference. A freshly constructed axis has no descriptor (None)."""

    def __init__(self) -> None:
        Ensures(Acc(self.descriptor) and self.descriptor is None)
        self.descriptor = None  # type: Optional[UnitDescriptor]
# pure-end

def build_companion_sharing_horizontal(
        source_horizontal: CoordinateAxis) -> CoordinateAxis:
    # pre-conditions-start
    Requires(Acc(source_horizontal.descriptor, 1 / 2))
    Requires(source_horizontal.descriptor is not None)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(source_horizontal.descriptor, 1 / 2))
    Ensures(source_horizontal.descriptor is not None)
    Ensures(Acc(Result().descriptor))
    # the companion's shared axis references the SAME descriptor object
    Ensures(Result().descriptor is source_horizontal.descriptor)
    Ensures(Result().descriptor is not None)
    # post-conditions-end
    # impl-start
    companion_horizontal = CoordinateAxis()
    companion_horizontal.descriptor = source_horizontal.descriptor
    return companion_horizontal
    # impl-end

def build_companion_sharing_vertical(
        source_vertical: CoordinateAxis) -> CoordinateAxis:
    # pre-conditions-start
    Requires(Acc(source_vertical.descriptor, 1 / 2))
    Requires(source_vertical.descriptor is not None)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(source_vertical.descriptor, 1 / 2))
    Ensures(source_vertical.descriptor is not None)
    Ensures(Acc(Result().descriptor))
    # the companion's shared axis references the SAME descriptor object
    Ensures(Result().descriptor is source_vertical.descriptor)
    Ensures(Result().descriptor is not None)
    # post-conditions-end
    # impl-start
    companion_vertical = CoordinateAxis()
    companion_vertical.descriptor = source_vertical.descriptor
    return companion_vertical
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Scratch dir Env: python (has swebench_unified),; run from project root.

SPEC UNDER TEST: two builder fns build_companion_sharing_{horizontal,vertical}; each postcondition pins EXACT reference identity Result().descriptor is source.descriptor AND Result().descriptor is not None AND full Acc(Result().descriptor), with only Acc(source.descriptor,1/2) incoming and precondition source.descriptor is not None. Genuine MULTI-SITE change (twinx x / twiny y): both fns must verify. Positive control model.py VERIFIES (10.05s) and is same-spec as itself.

COMMANDS (each attack): python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-26208 <path>. Results:
- atk_1_prepatch_h (omit copy at H, prepatch bug reproduced): EXIT 2 NOT-A-COUNTEREXAMPLE (does not verify — postcondition Result().descriptor is source fails). SPEC CAUGHT.
- atk_2_prepatch_v (omit copy at V): EXIT 2 (does not verify). SPEC CAUGHT.
- atk_3_newdesc (ungrounded-oracle style: companion.descriptor = fresh UnitDescriptor()): EXIT 2 (does not verify — identity to source fails). SPEC CAUGHT.
- atk_4_return_source (boundary/aliasing: return source_horizontal): EXIT 2 (does not verify — full Acc(Result().descriptor) unobtainable from 1/2 source permission). SPEC CAUGHT.
- atk_5_conditional (control-flow-effect: both branches copy source): EXIT 0 CANDIDATE (verifies 11.5s).
- atk_6_echo_reorg (intermediate-variable reorg of the copy): EXIT 0 CANDIDATE (verifies 11.2s).
- atk_7_double_none (dead write object() then copy source, last-write-wins): EXIT 0 CANDIDATE (verifies 10.3s).

RESOLVE on the 3 CANDIDATES' materialized faithful patches (run_resolve, official SWE-bench harness, matplotlib__matplotlib-26208, base_commit f0f133943d..., FAIL_TO_PASS test_twin_units[x,y]); all three diffs git-apply-check CLEAN at base_commit:
- atk_5_conditional -> resolved=True completed=True note='resolved'
- atk_6_echo_reorg  -> resolved=True completed=True note='resolved'
- atk_7_double_none -> resolved=True completed=True note='resolved'
All three are CORRECT ECHOES of the gold fix (each faithfully refines to ax2.<axis>.units = self.<axis>.units at both sites), so verify AND resolve => NOT spec weaknesses. No verifying same-spec impl produced a non-resolving faithful patch.

ATK_8_assume_vacuous (EXCLUDED from submitted attacks, reported for the record): impl `companion = CoordinateAxis(); Assume(companion.descriptor is source.descriptor); return companion`. adversary weakness returns EXIT 0 CANDIDATE (same-spec, verifies 10.4s) BECAUSE Assume injects the postcondition as an unproven fact. This is a BANNED-TOKEN cheat, NOT a spec weakness: nagini backend banned_tokens=('Assume(','Refute('); G-HYGIENE gates/hygiene.py _banned_calls rejects it (mechanically confirmed: atk_8 -> banned_calls=['Assume'] HYGIENE FAIL; atk_5/6/7 -> hygiene ok); prompts/nagini/quickref.md and worker.md forbid Assume/Refute.

It is a universal verifier-soundness defeat that would break EVERY Nagini spec identically, not evidence this spec is too weak; its faithful refinement is a runtime no-op (= prepatch, would not resolve), so submitting it would manufacture a spurious BROKEN against a sound spec. Deliberately withheld from `attacks`/`patches`. NOTE: the adversary `weakness` primitive and _derive_audit_verdict/check_attack do NOT screen banned tokens before the same-spec∧verify candidate check — reliance is on G-HYGIENE as a separate required gate; flagged for awareness but not a G-EQ defect.

REFINEMENT.MD A-LEG AUDIT: axioms region is EMPTY (confirmed model.py L29-32 + meta.json) => NO consumed @ContractOnly axiom, no A-consumed leg, no kind-3 trust point. Every leg in refinement.md tables is R (type refinement Axis<->CoordinateAxis, units<->descriptor, ax2.<axis>/self.<axis> <-> Result()/source) or I (H0/V0 unchanged builder body). The single A-REFERENCE — deep-model postcondition Result().descriptor is source.descriptor <=> gold hunk `ax2.<axis>.units = self.<axis>.units` — corresponds exactly to the real callee: the gold patch IS a reference-copy assignment at _base.py:4444 (twinx) / 4474 (twiny), and axiom_check.py (G-AX) validates it against real matplotlib twinx/twiny over 8 categorical scenarios (self-validating discrimination: patched vs prepatch regime). Correspondence HOLDS; corroborated independently by all three faithful echoes resolving. R/I legs are G-CONF's domain (not re-audited here per scope).

CONCLUSION: >=5 distinct wrong impls run (7 legitimate: 4 rejected by spec incl. prepatch bug at both sites, 3 verifying candidates all resolve). No verifying same-spec impl has a non-resolving faithful patch. A-legs sound (no consumed axiom; single A-reference corresponds to the real callee). => SOUND (verify => correct holds for this spec on the tested behaviour).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check on nagini bundle for matplotlib__matplotlib-26208. The two modeled functions build_companion_sharing_horizontal/vertical model twinx()/twiny() (lib/matplotlib/axes/_base.py). Spec per function: Requires(Acc(source.descriptor,1/2) and source.descriptor is not None); Ensures source.descriptor unchanged+non-None, Result().descriptor is source.descriptor (reference identity), Result().descriptor is not None.

Empirical validation against the REAL repo callee: installed matplotlib (3.6.3, pre-patch) confirmed the bug (companion.<axis>.units is None). I applied the gold hunks (ax2.xaxis.units=self.xaxis.units / ax2.yaxis.units=self.yaxis.units) to a copy and drove real twinx()/twiny() with unit-bearing categorical data: companion.<axis>.units IS source.<axis>.units (same object) and non-None on both directions across scenarios. The gold assignment is UNCONDITIONAL reference copy, so identity always holds within the precondition domain (source.units is not None). Source axis is only read, never mutated (matches Ensures). Companion's shared axis is a fresh distinct Axis (ax2.xaxis is not ax1.xaxis), consistent with modeling Result() as a freshly constructed CoordinateAxis.

The precondition source.descriptor is not None NARROWS the domain (a partial/weaker spec), the opposite of too-strong. On every input satisfying the precondition the modeled function agrees with the real callee; no diverging input exists. model.py verifies (Nagini: Verification successful, 10.95s). Type refinement Axis.units<->descriptor, identity-only, is sound. Verdict: FAITHFUL, no defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: insert `ax2.xaxis.units = self.xaxis.units` in twinx() and `ax2.yaxis.units = self.yaxis.units` in twiny() (lib/matplotlib/axes/_base.py) — propagate the unit descriptor to the twin axis by reference identity. Public problem_statement frames the bug as 'dataLims get replaced by inf for charts with twinx'; it names twinx/twiny (already public) but NEVER mentions `units`, the unit machinery, or the repo file — those appear only in hints_text (out of scope).

Spec-view checks:
- Mechanical screen (leakage.screen) PASSES: no hard failures. Verified via same LanguageTables the gate uses.
- No reproduced gold line: impl regions elided ('...  # implementation elided'); the discriminating assignment companion.descriptor = source.descriptor is NOT in the spec view.
- No patched file path (lib/matplotlib/axes/_base.py) and no module path in view.
- No patched-symbol echo: patched symbols are {twinx, twiny}, both already public in problem_statement; the spec uses abstract renames (CoordinateAxis, UnitDescriptor, descriptor, build_companion_sharing_horizontal/vertical). The repo field name `units` never appears anywhere in the spec view.
- No narration: comments describe desired behavior ('the companion's shared axis references the SAME descriptor object'), not the edit; none of bug/fix/patch/regression/previously appear.

Semantic reconstruction: the spec pins abstract reference-identity propagation of a 'descriptor' onto a freshly-built companion axis. This is the inherent behavior any faithful twin-artifact spec must state and does not disclose the repo-level localization (a `units` field assignment inside the specific twinx/twiny hunk) beyond what problem_statement already reveals (the twinx/twiny involvement). A solver could not reconstruct that the gold fix is a `units =` assignment from the 'descriptor' abstraction alone. Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).