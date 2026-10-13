# P2 adversarial audit — django__django-10914

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -46,7 +45,6 @@
 def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
     # pre-conditions-start
     # (no heap permissions: the override and result are immutable scalars.)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # An explicit per-instance override is used verbatim.
@@ -58,10 +56,7 @@
     Ensures(Implies(override is None, Result() == 420))
     # post-conditions-end
     # impl-start
-    # The project-wide default mode handed back when nothing is configured.
-    default = 420  # type: Optional[int]   # 0o644
-    # Resolution: an absent override falls back to the project-wide default;
-    # otherwise the override is used verbatim.
+    default = None  # type: Optional[int]
     if override is None:
         return default
     return override
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -46,7 +45,6 @@
 def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
     # pre-conditions-start
     # (no heap permissions: the override and result are immutable scalars.)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # An explicit per-instance override is used verbatim.
@@ -58,10 +56,7 @@
     Ensures(Implies(override is None, Result() == 420))
     # post-conditions-end
     # impl-start
-    # The project-wide default mode handed back when nothing is configured.
-    default = 420  # type: Optional[int]   # 0o644
-    # Resolution: an absent override falls back to the project-wide default;
-    # otherwise the override is used verbatim.
+    default = 511  # type: Optional[int]   # 0o777, wrong default
     if override is None:
         return default
     return override
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -46,7 +45,6 @@
 def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
     # pre-conditions-start
     # (no heap permissions: the override and result are immutable scalars.)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # An explicit per-instance override is used verbatim.
@@ -58,11 +56,6 @@
     Ensures(Implies(override is None, Result() == 420))
     # post-conditions-end
     # impl-start
-    # The project-wide default mode handed back when nothing is configured.
-    default = 420  # type: Optional[int]   # 0o644
-    # Resolution: an absent override falls back to the project-wide default;
-    # otherwise the override is used verbatim.
-    if override is None:
-        return default
-    return override
+    default = 420  # type: Optional[int]
+    return default
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -46,7 +45,6 @@
 def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
     # pre-conditions-start
     # (no heap permissions: the override and result are immutable scalars.)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # An explicit per-instance override is used verbatim.
@@ -58,11 +56,5 @@
     Ensures(Implies(override is None, Result() == 420))
     # post-conditions-end
     # impl-start
-    # The project-wide default mode handed back when nothing is configured.
-    default = 420  # type: Optional[int]   # 0o644
-    # Resolution: an absent override falls back to the project-wide default;
-    # otherwise the override is used verbatim.
-    if override is None:
-        return default
     return override
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -46,7 +45,6 @@
 def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
     # pre-conditions-start
     # (no heap permissions: the override and result are immutable scalars.)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # An explicit per-instance override is used verbatim.
@@ -58,10 +56,7 @@
     Ensures(Implies(override is None, Result() == 420))
     # post-conditions-end
     # impl-start
-    # The project-wide default mode handed back when nothing is configured.
-    default = 420  # type: Optional[int]   # 0o644
-    # Resolution: an absent override falls back to the project-wide default;
-    # otherwise the override is used verbatim.
+    default = 419  # type: Optional[int]   # 0o643, off-by-one
     if override is None:
         return default
     return override
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -46,7 +45,6 @@
 def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
     # pre-conditions-start
     # (no heap permissions: the override and result are immutable scalars.)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # An explicit per-instance override is used verbatim.
@@ -58,11 +56,8 @@
     Ensures(Implies(override is None, Result() == 420))
     # post-conditions-end
     # impl-start
-    # The project-wide default mode handed back when nothing is configured.
-    default = 420  # type: Optional[int]   # 0o644
-    # Resolution: an absent override falls back to the project-wide default;
-    # otherwise the override is used verbatim.
+    default = 420  # type: Optional[int]
     if override is None:
         return default
-    return override
+    return -override
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -46,7 +45,6 @@
 def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
     # pre-conditions-start
     # (no heap permissions: the override and result are immutable scalars.)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # An explicit per-instance override is used verbatim.
@@ -58,11 +56,6 @@
     Ensures(Implies(override is None, Result() == 420))
     # post-conditions-end
     # impl-start
-    # The project-wide default mode handed back when nothing is configured.
-    default = 420  # type: Optional[int]   # 0o644
-    # Resolution: an absent override falls back to the project-wide default;
-    # otherwise the override is used verbatim.
-    if override is None:
-        return default
-    return override
+    default = 256 + 128 + 16 + 8 + 4 + 4 + 4  # type: Optional[int]  # ==420 == 0o644
+    return default if override is None else override
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-10914.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A filesystem content store resolves the numeric permission mode it will
  apply to freshly stored content. The store may carry a per-instance override
  for this mode; when it does, that override is used verbatim. When the store
  carries NO per-instance override (the override is absent), the store falls
  back to a project-wide default mode, and that default mode is the definite
  octal value 0o644 (420 in decimal) rather than being absent.

  So the resolution is:
    * an explicit per-instance override passes through unchanged, and
    * in the absence of any override the effective mode is a concrete,
      non-absent permission value, 0o644.

The per-instance override and the resolved mode are modelled as ``Optional[int]``
(an absent value is ``None``; a present value is the integer the caller would
hand to a chmod-style primitive). The desired project-wide default is the
concrete integer 0o644, so the resolved mode is required to be a definite,
non-absent permission value whenever no override is configured.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the resolution is a total integer/None computation modelled
# deeply; it calls no opaque library callee.)
# axioms-end


# pure-start
@Pure
def default_mode() -> int:
    """The project-wide default numeric mode that should be handed to a
    chmod-style primitive when a store configures nothing more specific: a
    definite, owner-and-group-readable octal mode 0o644 (decimal 420)."""
    return 420  # 0o644
# pure-end


def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    # (no heap permissions: the override and result are immutable scalars.)
    # pre-conditions-end
    # post-conditions-start
    # An explicit per-instance override is used verbatim.
    Ensures(Implies(override is not None, Result() is override))
    # With no per-instance override the effective mode is the project-wide
    # default, the concrete octal value 0o644 == 420, and is NEVER absent.
    Ensures(Implies(override is None, Result() is not None))
    Ensures(Implies(override is None, Result() == default_mode()))
    Ensures(Implies(override is None, Result() == 420))
    # post-conditions-end
    # impl-start
    # The project-wide default mode handed back when nothing is configured.
    default = 420  # type: Optional[int]   # 0o644
    # Resolution: an absent override falls back to the project-wide default;
    # otherwise the override is used verbatim.
    if override is None:
        return default
    return override
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. The frozen spec for resolve_storage_mode(override: Optional[int]) is a TOTAL functional specification: Ensures(Implies(override is not None, Result() is override)) AND Ensures(Implies(override is None, Result() is not None)) AND Ensures(Implies(override is None, Result() == default_mode()==420)). It pins output on every input class.

A-LEG / MODEL-CORRESPONDENCE AUDIT: There are NO A-legs. axiom_check.py is absent; model.py has 0 @ContractOnly callees; axioms region is empty by design. mapping.md §3 correctly records callee provenance = None: the gold patch changes a module-level config VALUE (FILE_UPLOAD_PERMISSIONS: None -> 0o644 at global_settings.py:307), and the consuming resolver FileSystemStorage.file_permissions_mode = `_value_or_setting`(self.`_file_permissions_mode`, settings.FILE_UPLOAD_PERMISSIONS) with `_value_or_setting`(value,setting)=setting if value is None else value (storage.py:198-199,215-217) is fully expressible in Nagini and modeled DIRECTLY. refinement.md legs: A1 (override <-> self.`_file_permissions_mode`) = R on Optional[int] carrier; A2 (default=420 <-> FILE_UPLOAD_PERMISSIONS=0o644, the FIX) = I under R; A3 (if override is None: return default else return override <-> `_value_or_setting` body) = I under R. Every leg is R or I; NO kind-3, NO A-consumed/A-reference rows needed. conformance_check.py shadows the contract-stripped impl and diffs against the REAL patched FileSystemStorage.file_permissions_mode over boundary + 1e5 fuzz inputs (seed 10914) — correspondence is faithful.

atk_1 PREPATCH BUG default=None: weakness exit 2, does NOT verify (fails Implies(override is None, Result() is not None)). prepatch_reproduced=true.
- atk_2 WRONG CONSTANT default=511 (0o777): exit 2, does NOT verify (fails ==420).
- atk_3 CONTROL-FLOW ignores override, always returns 420: exit 2, does NOT verify (fails override passthrough).
- atk_4 PARTIAL-DOMAIN always returns override (None->None): exit 2, does NOT verify (fails None-branch).
- atk_5 BOUNDARY off-by-one default=419 (0o643): exit 2, does NOT verify.
- atk_6 CONTROL-FLOW-EFFECT returns -override in passthrough: exit 2, does NOT verify (fails Result() is override).
- atk_7 ECHO/behaviorally-correct: default computed arithmetically as 256+128+16+8+4+4+4 == 420 == 0o644, ternary passthrough: weakness exit 0 = CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies in 14.0s).

**MANDATORY RESOLVE ON THE CANDIDATE:** atk_7 is behaviorally identical to the gold (None->420, else override). Its faithful refined patch is exactly the gold edit FILE_UPLOAD_PERMISSIONS=0o644. Materialized at atk_7_patch.diff and EXECUTED through the official harness (python -m swebench_unified.run_evaluation, run_id sbu-audit-atk7-direct). RESULT: Instances resolved: 1; report.json resolved=true; FAIL_TO_PASS test_override_file_upload_permissions (test_utils.tests.OverrideSettingsTests) success; all PASS_TO_PASS success. Report saved report_atk_7.json. So the ONLY verifying same-spec impl RESOLVES — it does NOT break the spec (a resolving echo is not a weakness per current G-PANEL-1/G-EQ policy).

Re-ran the harness DIRECTLY under docker; it completed authoritatively with resolved=1. The resolve result is therefore executed and observed, not speculated.

**Positive control:** bundle model.py verifies (VERIFIED in 13.9s).

**CONCLUSION:** No same-spec verifying impl exists whose faithful patch fails to resolve. verify => correct holds. G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-10914.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A filesystem content store resolves the numeric permission mode it will
  apply to freshly stored content. The store may carry a per-instance override
  for this mode; when it does, that override is used verbatim. When the store
  carries NO per-instance override (the override is absent), the store falls
  back to a project-wide default mode, and that default mode is the definite
  octal value 0o644 (420 in decimal) rather than being absent.

  So the resolution is:
    * an explicit per-instance override passes through unchanged, and
    * in the absence of any override the effective mode is a concrete,
      non-absent permission value, 0o644.

The per-instance override and the resolved mode are modelled as ``Optional[int]``
(an absent value is ``None``; a present value is the integer the caller would
hand to a chmod-style primitive). The desired project-wide default is the
concrete integer 0o644, so the resolved mode is required to be a definite,
non-absent permission value whenever no override is configured.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the resolution is a total integer/None computation modelled
# deeply; it calls no opaque library callee.)
# axioms-end


# pure-start
@Pure
def default_mode() -> int:
    """The project-wide default numeric mode that should be handed to a
    chmod-style primitive when a store configures nothing more specific: a
    definite, owner-and-group-readable octal mode 0o644 (decimal 420)."""
    return 420  # 0o644
# pure-end


def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    # (no heap permissions: the override and result are immutable scalars.)
    # pre-conditions-end
    # post-conditions-start
    # An explicit per-instance override is used verbatim.
    Ensures(Implies(override is not None, Result() is override))
    # With no per-instance override the effective mode is the project-wide
    # default, the concrete octal value 0o644 == 420, and is NEVER absent.
    Ensures(Implies(override is None, Result() is not None))
    Ensures(Implies(override is None, Result() == default_mode()))
    Ensures(Implies(override is None, Result() == 420))
    # post-conditions-end
    # impl-start
    # The project-wide default mode handed back when nothing is configured.
    default = 420  # type: Optional[int]   # 0o644
    # Resolution: an absent override falls back to the project-wide default;
    # otherwise the override is used verbatim.
    if override is None:
        return default
    return override
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. The frozen spec for resolve_storage_mode(override: Optional[int]) is a TOTAL functional specification: Ensures(Implies(override is not None, Result() is override)) AND Ensures(Implies(override is None, Result() is not None)) AND Ensures(Implies(override is None, Result() == default_mode()==420)). It pins output on every input class.

A-LEG / MODEL-CORRESPONDENCE AUDIT: There are NO A-legs. axiom_check.py is absent; model.py has 0 @ContractOnly callees; axioms region is empty by design. mapping.md §3 correctly records callee provenance = None: the gold patch changes a module-level config VALUE (FILE_UPLOAD_PERMISSIONS: None -> 0o644 at global_settings.py:307), and the consuming resolver FileSystemStorage.file_permissions_mode = `_value_or_setting`(self.`_file_permissions_mode`, settings.FILE_UPLOAD_PERMISSIONS) with `_value_or_setting`(value,setting)=setting if value is None else value (storage.py:198-199,215-217) is fully expressible in Nagini and modeled DIRECTLY. refinement.md legs: A1 (override <-> self.`_file_permissions_mode`) = R on Optional[int] carrier; A2 (default=420 <-> FILE_UPLOAD_PERMISSIONS=0o644, the FIX) = I under R; A3 (if override is None: return default else return override <-> `_value_or_setting` body) = I under R. Every leg is R or I; NO kind-3, NO A-consumed/A-reference rows needed. conformance_check.py shadows the contract-stripped impl and diffs against the REAL patched FileSystemStorage.file_permissions_mode over boundary + 1e5 fuzz inputs (seed 10914) — correspondence is faithful.

atk_1 PREPATCH BUG default=None: weakness exit 2, does NOT verify (fails Implies(override is None, Result() is not None)). prepatch_reproduced=true.
- atk_2 WRONG CONSTANT default=511 (0o777): exit 2, does NOT verify (fails ==420).
- atk_3 CONTROL-FLOW ignores override, always returns 420: exit 2, does NOT verify (fails override passthrough).
- atk_4 PARTIAL-DOMAIN always returns override (None->None): exit 2, does NOT verify (fails None-branch).
- atk_5 BOUNDARY off-by-one default=419 (0o643): exit 2, does NOT verify.
- atk_6 CONTROL-FLOW-EFFECT returns -override in passthrough: exit 2, does NOT verify (fails Result() is override).
- atk_7 ECHO/behaviorally-correct: default computed arithmetically as 256+128+16+8+4+4+4 == 420 == 0o644, ternary passthrough: weakness exit 0 = CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies in 14.0s).

**MANDATORY RESOLVE ON THE CANDIDATE:** atk_7 is behaviorally identical to the gold (None->420, else override). Its faithful refined patch is exactly the gold edit FILE_UPLOAD_PERMISSIONS=0o644. Materialized at atk_7_patch.diff and EXECUTED through the official harness (python -m swebench_unified.run_evaluation, run_id sbu-audit-atk7-direct). RESULT: Instances resolved: 1; report.json resolved=true; FAIL_TO_PASS test_override_file_upload_permissions (test_utils.tests.OverrideSettingsTests) success; all PASS_TO_PASS success. Report saved report_atk_7.json. So the ONLY verifying same-spec impl RESOLVES — it does NOT break the spec (a resolving echo is not a weakness per current G-PANEL-1/G-EQ policy).

Re-ran the harness DIRECTLY under docker; it completed authoritatively with resolved=1. The resolve result is therefore executed and observed, not speculated.

**Positive control:** bundle model.py verifies (VERIFIED in 13.9s).

**CONCLUSION:** No same-spec verifying impl exists whose faithful patch fails to resolve. verify => correct holds. G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical to bundle (same-spec exit 0). Modeled function resolve_storage_mode(override) reproduces the real repo callee FileSystemStorage.file_permissions_mode = `_value_or_setting`(self.`_file_permissions_mode`, settings.FILE_UPLOAD_PERMISSIONS) post-patch. Verified against real source at the correct commit: storage.py:246-247 `_value_or_setting`(value, setting) = 'setting if value is None else value'; storage.py:264-266 property composes it; global_settings.py:325 FILE_UPLOAD_PERMISSIONS = 0o644. Thus real(override) = 420 if override is None else override. Model impl: default=420; return default if override is None else override. Differential over all input classes (None, 0, ±1, 420, 0o644, 0o777/511, 0o600, 0o755, ±2^63, 12345) shows byte-exact agreement — NO diverging input. The spec is NOT too strong: postconditions pin exactly the two real branches — override passthrough (override is not None ⟹ Result() is override, matching `_value_or_setting` returning value verbatim) and the None→420 fallback (override is None ⟹ Result() is not None and ==420). No extra clause over-constrains the override branch; 'is override' only requires verbatim passthrough. Optional[int] refinement is faithful (None ⇔ unspecified mode, int ⇔ os.chmod octal mode). Prepatch twin (default=None) correctly fails Implies(override is None, Result() is not None), matching F2P test test_override_file_upload_permissions. No opaque callee/axioms on this path. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage screen over the spec view (docstring + pure ref + pre/post-conditions; impl elided) for django__django-10914 nagini. The gold edit is a single value change: FILE_UPLOAD_PERMISSIONS = None -> 0o644 in django/conf/global_settings.py. The public problem_statement's TITLE is literally 'Set default FILE_UPLOAD_PERMISSION to 0o644.' so the target value 0o644 and the concept (a default file-upload permission mode) are fully public, NOT leaked. Every concrete gold fact appearing in the spec view is already in problem_statement: (1) the value 0o644 (==420) is the headline; (2) the 'default rather than being absent/None' contrast is what the problem_statement asks for (set a default). The spec view is otherwise abstracted away from the repo: it says 'filesystem content store', 'per-instance override', 'project-wide default mode' and models the resolution as Optional[int]. It does NOT name FILE_UPLOAD_PERMISSIONS, global_settings.py, FileSystemStorage, file_permissions_mode, `_value_or_setting`, or the storage-resolution rule — those repo-specific bindings live only in mapping.md/refinement.md, which are not part of the spec view. The override-passthrough postcondition (Result() is override) is a modeling generalization, not a gold-patch specific (the gold hunk touches only the default value). Nothing in the spec view discloses the gold edit beyond what problem_statement already states. Confirmed the spec view via swebench_unified.markers.spec_view with the nagini backend; impl region is correctly elided in the view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
