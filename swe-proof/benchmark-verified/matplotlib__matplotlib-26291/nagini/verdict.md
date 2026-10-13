# P2 adversarial audit — matplotlib__matplotlib-26291

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # context that, when absent, is not recoverable on this object.)
     Requires(Acc(self.measurements) and Acc(self.measured_with))
     Requires(context > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with)
@@ -97,7 +95,6 @@
     Requires(self.measurements == 0)
     # A supplied drawing context, when present, is a present (positive) handle.
     Requires(Implies(renderer is not None, renderer > 0))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with))
@@ -115,6 +112,7 @@
     # impl-start
     eff = renderer  # type: Optional[int]
     if eff is None:
-        eff = axes_context(ax)
-    measure(self, eff)
+        measure(self, 0)
+    else:
+        measure(self, eff)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # context that, when absent, is not recoverable on this object.)
     Requires(Acc(self.measurements) and Acc(self.measured_with))
     Requires(context > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with)
@@ -97,7 +95,6 @@
     Requires(self.measurements == 0)
     # A supplied drawing context, when present, is a present (positive) handle.
     Requires(Implies(renderer is not None, renderer > 0))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with))
@@ -115,6 +112,6 @@
     # impl-start
     eff = renderer  # type: Optional[int]
     if eff is None:
-        eff = axes_context(ax)
+        eff = 1
     measure(self, eff)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # context that, when absent, is not recoverable on this object.)
     Requires(Acc(self.measurements) and Acc(self.measured_with))
     Requires(context > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with)
@@ -97,7 +95,6 @@
     Requires(self.measurements == 0)
     # A supplied drawing context, when present, is a present (positive) handle.
     Requires(Implies(renderer is not None, renderer > 0))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with))
@@ -115,6 +112,6 @@
     # impl-start
     eff = renderer  # type: Optional[int]
     if eff is None:
-        eff = axes_context(ax)
+        eff = axes_context(ax) + 1
     measure(self, eff)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # context that, when absent, is not recoverable on this object.)
     Requires(Acc(self.measurements) and Acc(self.measured_with))
     Requires(context > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with)
@@ -97,7 +95,6 @@
     Requires(self.measurements == 0)
     # A supplied drawing context, when present, is a present (positive) handle.
     Requires(Implies(renderer is not None, renderer > 0))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with))
@@ -117,4 +114,5 @@
     if eff is None:
         eff = axes_context(ax)
     measure(self, eff)
+    measure(self, eff)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # context that, when absent, is not recoverable on this object.)
     Requires(Acc(self.measurements) and Acc(self.measured_with))
     Requires(context > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with)
@@ -97,7 +95,6 @@
     Requires(self.measurements == 0)
     # A supplied drawing context, when present, is a present (positive) handle.
     Requires(Implies(renderer is not None, renderer > 0))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with))
@@ -113,8 +110,6 @@
     Ensures(Implies(renderer is None, self.measured_with == axes_context(ax)))
     # post-conditions-end
     # impl-start
-    eff = renderer  # type: Optional[int]
-    if eff is None:
-        eff = axes_context(ax)
+    eff = axes_context(ax)  # type: int
     measure(self, eff)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # context that, when absent, is not recoverable on this object.)
     Requires(Acc(self.measurements) and Acc(self.measured_with))
     Requires(context > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with)
@@ -97,7 +95,6 @@
     Requires(self.measurements == 0)
     # A supplied drawing context, when present, is a present (positive) handle.
     Requires(Implies(renderer is not None, renderer > 0))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with))
@@ -115,6 +112,5 @@
     # impl-start
     eff = renderer  # type: Optional[int]
     if eff is None:
-        eff = axes_context(ax)
-    measure(self, eff)
+        measure(self, axes_context(ax))
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # context that, when absent, is not recoverable on this object.)
     Requires(Acc(self.measurements) and Acc(self.measured_with))
     Requires(context > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with)
@@ -97,7 +95,6 @@
     Requires(self.measurements == 0)
     # A supplied drawing context, when present, is a present (positive) handle.
     Requires(Implies(renderer is not None, renderer > 0))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with))
@@ -113,8 +110,8 @@
     Ensures(Implies(renderer is None, self.measured_with == axes_context(ax)))
     # post-conditions-end
     # impl-start
-    eff = renderer  # type: Optional[int]
-    if eff is None:
-        eff = axes_context(ax)
-    measure(self, eff)
+    if renderer is None:
+        measure(self, axes_context(ax))
+    else:
+        measure(self, renderer)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # context that, when absent, is not recoverable on this object.)
     Requires(Acc(self.measurements) and Acc(self.measured_with))
     Requires(context > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with)
@@ -97,7 +95,6 @@
     Requires(self.measurements == 0)
     # A supplied drawing context, when present, is a present (positive) handle.
     Requires(Implies(renderer is not None, renderer > 0))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.measurements) and Acc(self.measured_with))
@@ -113,8 +110,9 @@
     Ensures(Implies(renderer is None, self.measured_with == axes_context(ax)))
     # post-conditions-end
     # impl-start
-    eff = renderer  # type: Optional[int]
-    if eff is None:
-        eff = axes_context(ax)
-    measure(self, eff)
+    self.measurements = 1
+    if renderer is None:
+        self.measured_with = axes_context(ax)
+    else:
+        self.measured_with = renderer
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `model.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-26291.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A positioning callable computes the placement of an inset region. It is
  invoked with an axes and, optionally, a drawing context (a renderer).
  Some callers — for instance one that measures a figure's contents while
  saving it — invoke the callable WITHOUT a drawing context (the context
  argument is absent).

  Computing the placement requires a usable drawing context: the extent and
  offset of the region can only be measured against a present (non-absent)
  drawing context.

  The behaviour required of the callable:

    (1) When invoked WITHOUT a drawing context, it must still perform the
        measurement against a present (non-absent) drawing context — namely
        the one resolved from the host axes by the unchanged drawing-context
        source (not an arbitrary substitute context).

    (2) When invoked WITH a drawing context, it performs the measurement
        against the supplied context unchanged.

  In both cases the measurement is performed exactly once against a present
  (non-absent) drawing context; when a context was supplied it is the supplied
  one, and when none was supplied it is the one the host axes resolves.

The drawing context is modelled as ``Optional[int]`` (absent is ``None``;
present is an opaque positive handle). When none is supplied, a present context
is obtained from an unchanged opaque primitive, axiomatized to always yield a
present handle; the measurement is pinned to exactly that resolved context. The
measurement is an unchanged opaque primitive whose precondition is that it is
handed a present context; it is run exactly once and records the handle it was
handed, so "measured against the resolved present context" is stated exactly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def axes_context(ax: int) -> int:
    """The unchanged drawing-context source used when no context is supplied.
    It always yields a PRESENT handle — a positive opaque code, never the
    absent sentinel. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Ensures(Result() > 0)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end

class Locator:
    def __init__(self) -> None:
        Ensures(Acc(self.measurements) and self.measurements == 0)  # type: ignore
        Ensures(Acc(self.measured_with) and self.measured_with == 0)  # type: ignore
        self.measurements = 0  # type: int
        # The handle the measurement primitive was last handed (0 = the
        # measurement has not run yet; present handles are positive).
        self.measured_with = 0  # type: int

def measure(self: Locator, context: int) -> None:
    # pre-conditions-start
    # The measurement can only be performed against a PRESENT drawing context.
    # (Modelled as: the handle must be a present, positive code. The absent
    # sentinel None is not even of this parameter's type — handing None here is
    # rejected statically, mirroring the real measurement dereferencing a
    # context that, when absent, is not recoverable on this object.)
    Requires(Acc(self.measurements) and Acc(self.measured_with))
    Requires(context > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.measurements) and Acc(self.measured_with)
            and self.measurements == Old(self.measurements) + 1
            and self.measured_with == context)
    # post-conditions-end
    # impl-start
    self.measurements = self.measurements + 1
    self.measured_with = context
    # impl-end

def call(self: Locator, ax: int, renderer: Optional[int]) -> None:
    # pre-conditions-start
    Requires(Acc(self.measurements) and Acc(self.measured_with))
    Requires(self.measurements == 0)
    # A supplied drawing context, when present, is a present (positive) handle.
    Requires(Implies(renderer is not None, renderer > 0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.measurements) and Acc(self.measured_with))
    # The measurement is performed exactly once...
    Ensures(self.measurements == 1)
    # ...against a PRESENT drawing context...
    Ensures(self.measured_with > 0)
    # ...which is the supplied one when one was supplied,
    Ensures(Implies(renderer is not None, self.measured_with == renderer))
    # ...and otherwise (no context supplied) exactly the one the host axes
    # resolves via the unchanged drawing-context source — not an arbitrary
    # substitute present context.
    Ensures(Implies(renderer is None, self.measured_with == axes_context(ax)))
    # post-conditions-end
    # impl-start
    eff = renderer  # type: Optional[int]
    if eff is None:
        eff = axes_context(ax)
    measure(self, eff)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec at benchmark-verified/matplotlib__matplotlib-26291/nagini. SBU_BENCHMARK_DIR=benchmark-verified, PY=python; all commands from repo root.

### 8 same-spec wrong-impl attacks (all byte-identical spec; same-spec exit=0 each)
Cmd per attack: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-26291 atk_N.py`
  atk_1 (prepatch bug re-encoded: no-renderer branch threads absent context `measure(self,0)`): NOT-A-COUNTEREXAMPLE, does not verify (fails measure's Requires(context>0)). exit=2.
  atk_2 (ungrounded-oracle echo: substitute fresh constant `eff=1` for resolved context): does not verify (fails pinned equality measured_with==axes_context(ax)). exit=2.
  atk_3 (substitute-source: `eff=axes_context(ax)+1`, opaque, not provably ==axes_context(ax)): does not verify. exit=2.
  atk_4 (boundary/count: measure twice): does not verify (fails measurements==1). exit=2.
  atk_5 (control-flow-effect: measure present branch against resolved ctx not supplied renderer): does not verify (fails renderer is not None => measured_with==renderer). exit=2.
  atk_6 (partial-domain: only measure on no-renderer branch, skip supplied): does not verify (fails measurements==1 on supplied path). exit=2.
  atk_7 (echo, gold-equivalent control flow: None->axes_context(ax), else renderer, then measure): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies). exit=0.
  atk_8 (ungrounded-oracle/bypass: directly assign measurements=1 & measured_with without invoking measure primitive): CANDIDATE-COUNTEREXAMPLE. exit=0.

=== Materialized faithful refined patches for BOTH candidates -> official harness (run_resolve) ===
Both candidates are behavioral echoes of the gold: atk_7's control flow IS the gold hunk; atk_8's observables (measurements==1; measured_with = resolved context on None-path / supplied renderer otherwise) have NO repo field (mapping.md §2 auxiliary observables) so the only faithful repo realization of 'one measurement occurred against that present context' is the gold behavior (resolve renderer from host axes then run get_window_extent/get_offset). Faithful patch for each = the gold hunk. Verified md5 8663df58e52da092e71c975c7978076c == benchmark-verified/.../patch.diff (identical).
Executed: run_resolve('matplotlib__matplotlib-26291', <faithful patch>, run_id='sbu763-faithful', timeout=1800).
RESULT: resolved=True completed=True attempts=1 flaky=False note='resolved'. => Neither verifying wrong impl's faithful patch fails to resolve; spec is NOT broken.
(An earlier run_resolve returned completed=False due to contention/infra error, NOT a resolve verdict — correctly treated as inconclusive, re-run to completion.)

### Positive control
`bash scripts/nagini_verify.sh .../model.py` -> Verification successful (22.5s), exit=0.

### Prepatch reproduced
`bash scripts/nagini_verify.sh .../model_prepatch.py` -> Verification failed: model_prepatch.py:118:9 error: precondition of measure might not hold, Assertion (context > 0) might not hold. exit=1. Matches refinement.md's documented F2P isolation (no-renderer path threads absent context). atk_1 re-encodes the same bug in model.py's impl region and likewise fails to verify.

### refinement.md leg audit (A-legs + correspondence)
Leg 1 `eff=renderer` = R (type refinement, G-CONF domain). Leg 2 `if eff is None: eff=axes_context(ax)` = A-consumed + I: axiom axes_context <-> unchanged callee ax.figure._get_renderer() (Figure._get_renderer, figure.py:2731). G-AX/axiom_check.py exercises the REAL callee over 10 witnesses (plain/multi-subplot/inset-regression/varied size+dpi) asserting present+usable (not None; hasattr points_to_pixels) = Result()>0; runs RC=0 at base_commit (does not exercise the unpatched savefig bug). Correspondence holds; G-AX=pass. Leg 3 `measure(self,eff)` = R, modeled DEEPLY (measurements/measured_with observables + Requires(context>0)), not axiomatized. self.axes=ax = I(omitted), F2P-invisible. No kind-3 legs; meta deep_model_references=[] (no A-reference legs to audit); exactly one A-consumed axiom over an UNCHANGED callee. Consistent.

CONCLUSION: The pinned no-renderer clause (measured_with==axes_context(ax) with axes_context opaque @Pure) defeats every substitute-source/ungrounded-oracle/constant attack (atk_2/3/5), the prepatch/absent-context attack (atk_1), and count/domain attacks (atk_4/6). The only impls that verify (atk_7 echo, atk_8 counter-bypass) both refine to the gold patch, which RESOLVES under the official harness. No verifying wrong impl exists whose faithful patch fails to resolve. verify => correct holds. Note meta records G-PANEL-1=fail; that is the historical presence-only weakness the spec was later pinned against (documented in refinement.md §'discriminating clause') and is orthogonal to this G-EQ refinement-fidelity verdict.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `model.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-26291.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A positioning callable computes the placement of an inset region. It is
  invoked with an axes and, optionally, a drawing context (a renderer).
  Some callers — for instance one that measures a figure's contents while
  saving it — invoke the callable WITHOUT a drawing context (the context
  argument is absent).

  Computing the placement requires a usable drawing context: the extent and
  offset of the region can only be measured against a present (non-absent)
  drawing context.

  The behaviour required of the callable:

    (1) When invoked WITHOUT a drawing context, it must still perform the
        measurement against a present (non-absent) drawing context — namely
        the one resolved from the host axes by the unchanged drawing-context
        source (not an arbitrary substitute context).

    (2) When invoked WITH a drawing context, it performs the measurement
        against the supplied context unchanged.

  In both cases the measurement is performed exactly once against a present
  (non-absent) drawing context; when a context was supplied it is the supplied
  one, and when none was supplied it is the one the host axes resolves.

The drawing context is modelled as ``Optional[int]`` (absent is ``None``;
present is an opaque positive handle). When none is supplied, a present context
is obtained from an unchanged opaque primitive, axiomatized to always yield a
present handle; the measurement is pinned to exactly that resolved context. The
measurement is an unchanged opaque primitive whose precondition is that it is
handed a present context; it is run exactly once and records the handle it was
handed, so "measured against the resolved present context" is stated exactly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def axes_context(ax: int) -> int:
    """The unchanged drawing-context source used when no context is supplied.
    It always yields a PRESENT handle — a positive opaque code, never the
    absent sentinel. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Ensures(Result() > 0)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end

class Locator:
    def __init__(self) -> None:
        Ensures(Acc(self.measurements) and self.measurements == 0)  # type: ignore
        Ensures(Acc(self.measured_with) and self.measured_with == 0)  # type: ignore
        self.measurements = 0  # type: int
        # The handle the measurement primitive was last handed (0 = the
        # measurement has not run yet; present handles are positive).
        self.measured_with = 0  # type: int

def measure(self: Locator, context: int) -> None:
    # pre-conditions-start
    # The measurement can only be performed against a PRESENT drawing context.
    # (Modelled as: the handle must be a present, positive code. The absent
    # sentinel None is not even of this parameter's type — handing None here is
    # rejected statically, mirroring the real measurement dereferencing a
    # context that, when absent, is not recoverable on this object.)
    Requires(Acc(self.measurements) and Acc(self.measured_with))
    Requires(context > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.measurements) and Acc(self.measured_with)
            and self.measurements == Old(self.measurements) + 1
            and self.measured_with == context)
    # post-conditions-end
    # impl-start
    self.measurements = self.measurements + 1
    self.measured_with = context
    # impl-end

def call(self: Locator, ax: int, renderer: Optional[int]) -> None:
    # pre-conditions-start
    Requires(Acc(self.measurements) and Acc(self.measured_with))
    Requires(self.measurements == 0)
    # A supplied drawing context, when present, is a present (positive) handle.
    Requires(Implies(renderer is not None, renderer > 0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.measurements) and Acc(self.measured_with))
    # The measurement is performed exactly once...
    Ensures(self.measurements == 1)
    # ...against a PRESENT drawing context...
    Ensures(self.measured_with > 0)
    # ...which is the supplied one when one was supplied,
    Ensures(Implies(renderer is not None, self.measured_with == renderer))
    # ...and otherwise (no context supplied) exactly the one the host axes
    # resolves via the unchanged drawing-context source — not an arbitrary
    # substitute present context.
    Ensures(Implies(renderer is None, self.measured_with == axes_context(ax)))
    # post-conditions-end
    # impl-start
    eff = renderer  # type: Optional[int]
    if eff is None:
        eff = axes_context(ax)
    measure(self, eff)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec at benchmark-verified/matplotlib__matplotlib-26291/nagini. SBU_BENCHMARK_DIR=benchmark-verified, PY=python; all commands from repo root.

### 8 same-spec wrong-impl attacks (all byte-identical spec; same-spec exit=0 each)
Cmd per attack: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-26291 atk_N.py`
  atk_1 (prepatch bug re-encoded: no-renderer branch threads absent context `measure(self,0)`): NOT-A-COUNTEREXAMPLE, does not verify (fails measure's Requires(context>0)). exit=2.
  atk_2 (ungrounded-oracle echo: substitute fresh constant `eff=1` for resolved context): does not verify (fails pinned equality measured_with==axes_context(ax)). exit=2.
  atk_3 (substitute-source: `eff=axes_context(ax)+1`, opaque, not provably ==axes_context(ax)): does not verify. exit=2.
  atk_4 (boundary/count: measure twice): does not verify (fails measurements==1). exit=2.
  atk_5 (control-flow-effect: measure present branch against resolved ctx not supplied renderer): does not verify (fails renderer is not None => measured_with==renderer). exit=2.
  atk_6 (partial-domain: only measure on no-renderer branch, skip supplied): does not verify (fails measurements==1 on supplied path). exit=2.
  atk_7 (echo, gold-equivalent control flow: None->axes_context(ax), else renderer, then measure): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies). exit=0.
  atk_8 (ungrounded-oracle/bypass: directly assign measurements=1 & measured_with without invoking measure primitive): CANDIDATE-COUNTEREXAMPLE. exit=0.

=== Materialized faithful refined patches for BOTH candidates -> official harness (run_resolve) ===
Both candidates are behavioral echoes of the gold: atk_7's control flow IS the gold hunk; atk_8's observables (measurements==1; measured_with = resolved context on None-path / supplied renderer otherwise) have NO repo field (mapping.md §2 auxiliary observables) so the only faithful repo realization of 'one measurement occurred against that present context' is the gold behavior (resolve renderer from host axes then run get_window_extent/get_offset). Faithful patch for each = the gold hunk. Verified md5 8663df58e52da092e71c975c7978076c == benchmark-verified/.../patch.diff (identical).
Executed: run_resolve('matplotlib__matplotlib-26291', <faithful patch>, run_id='sbu763-faithful', timeout=1800).
RESULT: resolved=True completed=True attempts=1 flaky=False note='resolved'. => Neither verifying wrong impl's faithful patch fails to resolve; spec is NOT broken.
(An earlier run_resolve returned completed=False due to contention/infra error, NOT a resolve verdict — correctly treated as inconclusive, re-run to completion.)

### Positive control
`bash scripts/nagini_verify.sh .../model.py` -> Verification successful (22.5s), exit=0.

### Prepatch reproduced
`bash scripts/nagini_verify.sh .../model_prepatch.py` -> Verification failed: model_prepatch.py:118:9 error: precondition of measure might not hold, Assertion (context > 0) might not hold. exit=1. Matches refinement.md's documented F2P isolation (no-renderer path threads absent context). atk_1 re-encodes the same bug in model.py's impl region and likewise fails to verify.

### refinement.md leg audit (A-legs + correspondence)
Leg 1 `eff=renderer` = R (type refinement, G-CONF domain). Leg 2 `if eff is None: eff=axes_context(ax)` = A-consumed + I: axiom axes_context <-> unchanged callee ax.figure._get_renderer() (Figure._get_renderer, figure.py:2731). G-AX/axiom_check.py exercises the REAL callee over 10 witnesses (plain/multi-subplot/inset-regression/varied size+dpi) asserting present+usable (not None; hasattr points_to_pixels) = Result()>0; runs RC=0 at base_commit (does not exercise the unpatched savefig bug). Correspondence holds; G-AX=pass. Leg 3 `measure(self,eff)` = R, modeled DEEPLY (measurements/measured_with observables + Requires(context>0)), not axiomatized. self.axes=ax = I(omitted), F2P-invisible. No kind-3 legs; meta deep_model_references=[] (no A-reference legs to audit); exactly one A-consumed axiom over an UNCHANGED callee. Consistent.

CONCLUSION: The pinned no-renderer clause (measured_with==axes_context(ax) with axes_context opaque @Pure) defeats every substitute-source/ungrounded-oracle/constant attack (atk_2/3/5), the prepatch/absent-context attack (atk_1), and count/domain attacks (atk_4/6). The only impls that verify (atk_7 echo, atk_8 counter-bypass) both refine to the gold patch, which RESOLVES under the official harness. No verifying wrong impl exists whose faithful patch fails to resolve. verify => correct holds. Note meta records G-PANEL-1=fail; that is the historical presence-only weakness the spec was later pinned against (documented in refinement.md §'discriminating clause') and is orthogonal to this G-EQ refinement-fidelity verdict.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for matplotlib__matplotlib-26291 nagini. Verified: model.py verifies (nagini exit 0, 18.7s); model_prepatch.py fails exactly at measure's Requires(context>0) on the renderer-is-None branch (model_pre.py:118), mirroring the real pre-patch AttributeError; same-spec(prepatch) exit 0 (spec regions byte-identical). Axiom axes_context (Ensures Result()>0) is executably sound over the REAL repo callee ax.figure._get_renderer(): axiom_check.py passes exit 0 over 10 witnesses (plain axes, 2 subplots, inset-regression axes incl. inset_axes, 5 figure size/dpi shapes), all returning a present renderer with points_to_pixels.

Model-vs-gold correspondence, checked per input class:
- renderer supplied (present handle): model requires measured_with==renderer, measurements==1. Gold: measures window-extent+offset against the supplied renderer once. AGREE.
- renderer is None: model requires measured_with==axes_context(ax). Gold inserts `if renderer is None: renderer = ax.figure._get_renderer()` then measures against it; axes_context IS that callee. AGREE.
- measurements==1: __call__ has no loops; the two get_window_extent/get_offset calls share one renderer, abstracted as a single measure recording that renderer. AGREE.

The pinned equality measured_with==axes_context(ax) (rather than presence-only) is calibrated exactly to gold: gold satisfies it (not too strong — no gold behavior is rejected), and it excludes substitute-renderer impls (not too weak). No input exists on which the modeled call disagrees with the real AnchoredLocatorBase.__call__ under the stated type abstraction. Spec is faithful; no divergence.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rendered the consumer spec view via markers.spec_view(NaginiBackend.language) over model.py and diffed disclosure against the PUBLIC problem_statement (hints_text excluded per instructions).

Gold edit: `if renderer is None: renderer = ax.figure._get_renderer()` in AnchoredLocatorBase.__call__ (lib/mpl_toolkits/axes_grid1/inset_locator.py).

Spec-view findings:
- Both impl regions (measure() and call()) are elided to `...  # implementation elided — supplied by the consumer`, so the gold body (if eff is None: eff = axes_context(ax); measure(self, eff)) is absent from the spec view.
- Lexical scan of the spec view for repo/gold symbols found NONE present: _get_renderer, inset_locator, AnchoredLocator(Base), get_window_extent, get_offset, offsetbox, _tight_bbox, tight_bbox, savefig, print_figure, ax.figure — all absent. The gold callee ax.figure._get_renderer() appears ONLY in mapping.md / refinement.md (audit docs, not the consumer spec view).
- The only occurrence of 'figure' in the spec view is the abstract prose "one that measures a figure's contents while saving it", which is more explicit and directly present in the public problem_statement.
- The spec discloses only abstract desired behaviour — 'when no context is supplied, measure against the context the host axes resolves' — encoded as Implies(renderer is None, measured_with == axes_context(ax)) where axes_context is an opaque @Pure @ContractOnly with only Ensures(Result() > 0). It names neither the repo callee nor the edit.

Comparison to PUBLIC problem_statement: the problem_statement already includes the full traceback naming __call__(self, ax, renderer), self.get_window_extent(renderer), self.get_offset(...), the literal `if renderer is None:` branch, and the failing `renderer = self.figure._get_renderer()` line (plus that self.figure is None). The spec view is STRICTLY MORE ABSTRACT than the public statement — it reveals less about the mechanism, not more. Nothing in the spec view leaks the gold edit beyond what the public problem_statement already exposes.

Note: G-PANEL-1/G-EQ record a separate spec-strength (spec-too-weak / inconclusive) matter; a spec that admits weaker impls is the opposite of leaking the gold edit and is out of scope for leakage.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
