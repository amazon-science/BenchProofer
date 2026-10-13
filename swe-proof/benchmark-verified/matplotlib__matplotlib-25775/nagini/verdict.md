# P2 adversarial audit — matplotlib__matplotlib-25775

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -47,7 +46,6 @@
 
 class Glyph:
     def __init__(self, pref: bool) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
         Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
         self.pref = pref      # type: bool
@@ -56,7 +54,6 @@
 
 def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
     # pre-conditions-start
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().pref))
@@ -69,6 +66,7 @@
     g = Glyph(default)
     if supplied is not None:
         set_pref(g, supplied)
+    g.dirty = False
     return g
     # impl-end
 
@@ -77,7 +75,6 @@
     # pre-conditions-start
     Requires(Acc(g.pref))
     Requires(Acc(g.dirty))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref) and g.pref == value)
@@ -93,7 +90,6 @@
 def get_pref(g: Glyph) -> bool:
     # pre-conditions-start
     Requires(Acc(g.pref, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref, 1 / 2))
@@ -110,7 +106,6 @@
     Requires(Acc(dst.pref))
     Requires(Acc(dst.dirty))
     Requires(Acc(src.pref, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(src.pref, 1 / 2))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -47,7 +46,6 @@
 
 class Glyph:
     def __init__(self, pref: bool) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
         Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
         self.pref = pref      # type: bool
@@ -56,7 +54,6 @@
 
 def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
     # pre-conditions-start
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().pref))
@@ -67,8 +64,6 @@
     # post-conditions-end
     # impl-start
     g = Glyph(default)
-    if supplied is not None:
-        set_pref(g, supplied)
     return g
     # impl-end
 
@@ -77,7 +72,6 @@
     # pre-conditions-start
     Requires(Acc(g.pref))
     Requires(Acc(g.dirty))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref) and g.pref == value)
@@ -93,7 +87,6 @@
 def get_pref(g: Glyph) -> bool:
     # pre-conditions-start
     Requires(Acc(g.pref, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref, 1 / 2))
@@ -110,7 +103,6 @@
     Requires(Acc(dst.pref))
     Requires(Acc(dst.dirty))
     Requires(Acc(src.pref, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(src.pref, 1 / 2))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -47,7 +46,6 @@
 
 class Glyph:
     def __init__(self, pref: bool) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
         Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
         self.pref = pref      # type: bool
@@ -56,7 +54,6 @@
 
 def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
     # pre-conditions-start
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().pref))
@@ -77,7 +74,6 @@
     # pre-conditions-start
     Requires(Acc(g.pref))
     Requires(Acc(g.dirty))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref) and g.pref == value)
@@ -85,7 +81,6 @@
     Ensures(Acc(g.dirty) and g.dirty)
     # post-conditions-end
     # impl-start
-    g.pref = value
     g.dirty = True
     # impl-end
 
@@ -93,7 +88,6 @@
 def get_pref(g: Glyph) -> bool:
     # pre-conditions-start
     Requires(Acc(g.pref, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref, 1 / 2))
@@ -110,7 +104,6 @@
     Requires(Acc(dst.pref))
     Requires(Acc(dst.dirty))
     Requires(Acc(src.pref, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(src.pref, 1 / 2))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -47,7 +46,6 @@
 
 class Glyph:
     def __init__(self, pref: bool) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
         Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
         self.pref = pref      # type: bool
@@ -56,7 +54,6 @@
 
 def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
     # pre-conditions-start
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().pref))
@@ -67,7 +64,7 @@
     # post-conditions-end
     # impl-start
     g = Glyph(default)
-    if supplied is not None:
+    if supplied is not None and supplied:
         set_pref(g, supplied)
     return g
     # impl-end
@@ -77,7 +74,6 @@
     # pre-conditions-start
     Requires(Acc(g.pref))
     Requires(Acc(g.dirty))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref) and g.pref == value)
@@ -93,7 +89,6 @@
 def get_pref(g: Glyph) -> bool:
     # pre-conditions-start
     Requires(Acc(g.pref, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref, 1 / 2))
@@ -110,7 +105,6 @@
     Requires(Acc(dst.pref))
     Requires(Acc(dst.dirty))
     Requires(Acc(src.pref, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(src.pref, 1 / 2))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -47,7 +46,6 @@
 
 class Glyph:
     def __init__(self, pref: bool) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
         Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
         self.pref = pref      # type: bool
@@ -56,7 +54,6 @@
 
 def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
     # pre-conditions-start
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().pref))
@@ -77,7 +74,6 @@
     # pre-conditions-start
     Requires(Acc(g.pref))
     Requires(Acc(g.dirty))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref) and g.pref == value)
@@ -93,7 +89,6 @@
 def get_pref(g: Glyph) -> bool:
     # pre-conditions-start
     Requires(Acc(g.pref, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref, 1 / 2))
@@ -110,7 +105,6 @@
     Requires(Acc(dst.pref))
     Requires(Acc(dst.dirty))
     Requires(Acc(src.pref, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(src.pref, 1 / 2))
@@ -121,5 +115,5 @@
     # post-conditions-end
     # impl-start
     dst.pref = src.pref
-    dst.dirty = True
+    dst.dirty = False
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -47,7 +46,6 @@
 
 class Glyph:
     def __init__(self, pref: bool) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
         Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
         self.pref = pref      # type: bool
@@ -56,7 +54,6 @@
 
 def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
     # pre-conditions-start
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().pref))
@@ -77,7 +74,6 @@
     # pre-conditions-start
     Requires(Acc(g.pref))
     Requires(Acc(g.dirty))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref) and g.pref == value)
@@ -93,7 +89,6 @@
 def get_pref(g: Glyph) -> bool:
     # pre-conditions-start
     Requires(Acc(g.pref, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref, 1 / 2))
@@ -101,7 +96,7 @@
     Ensures(Result() == g.pref)
     # post-conditions-end
     # impl-start
-    return g.pref
+    return True
     # impl-end
 
 
@@ -110,7 +105,6 @@
     Requires(Acc(dst.pref))
     Requires(Acc(dst.dirty))
     Requires(Acc(src.pref, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(src.pref, 1 / 2))
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -47,7 +46,6 @@
 
 class Glyph:
     def __init__(self, pref: bool) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
         Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
         self.pref = pref      # type: bool
@@ -56,7 +54,6 @@
 
 def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
     # pre-conditions-start
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().pref))
@@ -69,6 +66,8 @@
     g = Glyph(default)
     if supplied is not None:
         set_pref(g, supplied)
+    else:
+        g.dirty = False
     return g
     # impl-end
 
@@ -77,7 +76,6 @@
     # pre-conditions-start
     Requires(Acc(g.pref))
     Requires(Acc(g.dirty))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref) and g.pref == value)
@@ -93,7 +91,6 @@
 def get_pref(g: Glyph) -> bool:
     # pre-conditions-start
     Requires(Acc(g.pref, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(g.pref, 1 / 2))
@@ -110,7 +107,6 @@
     Requires(Acc(dst.pref))
     Requires(Acc(dst.dirty))
     Requires(Acc(src.pref, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(src.pref, 1 / 2))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25775.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A drawable glyph object carries its own per-object edge-smoothing preference,
  rather than always deferring to a single global default. The desired
  behaviour is exactly:

    (1) Construction. A glyph is created with an optional preference argument.
        When that argument is omitted (the absent value), the object's stored
        preference is the global default supplied at construction time. When
        the argument is supplied, the object's stored preference is exactly the
        supplied value, overriding the global default.

    (2) Read-back. Querying a glyph's preference returns exactly the value it
        currently stores.

    (3) Update. Setting a glyph's preference to a value makes a subsequent query
        return that value, and marks the object as needing redraw.

    (4) Copying. Adopting another glyph's visual state copies the source glyph's
        stored preference, so the destination subsequently reports the source's
        value.

The preference is a boolean; "absent" is modelled by the optional ``None``.
The object is modelled as a minimal class carrying only the one touched field
(its stored preference) plus a redraw flag.  This is the per-object state whose
presence/absence the tested behaviour distinguishes from the global default.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no callee is axiomatized: the behaviour is pure in-object state — a stored
# preference, its read-back, its update, and its copy — modelled deeply.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Glyph:
    def __init__(self, pref: bool) -> None:
        Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
        Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
        self.pref = pref      # type: bool
        self.dirty = True     # type: bool


def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().pref))
    Ensures(Acc(Result().dirty))
    # (1) absent argument -> the global default; supplied argument -> that value
    Ensures(Implies(supplied is None, Result().pref == default))
    Ensures(Implies(supplied is not None, Result().pref == supplied))
    # post-conditions-end
    # impl-start
    g = Glyph(default)
    if supplied is not None:
        set_pref(g, supplied)
    return g
    # impl-end


def set_pref(g: Glyph, value: bool) -> None:
    # pre-conditions-start
    Requires(Acc(g.pref))
    Requires(Acc(g.dirty))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(g.pref) and g.pref == value)
    # (3) update marks the object as needing redraw
    Ensures(Acc(g.dirty) and g.dirty)
    # post-conditions-end
    # impl-start
    g.pref = value
    g.dirty = True
    # impl-end


def get_pref(g: Glyph) -> bool:
    # pre-conditions-start
    Requires(Acc(g.pref, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(g.pref, 1 / 2))
    # (2) read-back returns exactly the stored preference
    Ensures(Result() == g.pref)
    # post-conditions-end
    # impl-start
    return g.pref
    # impl-end


def copy_state(dst: Glyph, src: Glyph) -> None:
    # pre-conditions-start
    Requires(Acc(dst.pref))
    Requires(Acc(dst.dirty))
    Requires(Acc(src.pref, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(src.pref, 1 / 2))
    Ensures(Acc(dst.pref) and Acc(dst.dirty))
    # (4) destination adopts the source's stored preference
    Ensures(dst.pref == src.pref)
    Ensures(dst.dirty)
    # post-conditions-end
    # impl-start
    dst.pref = src.pref
    dst.dirty = True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec surface: model.py has ZERO axioms and ZERO deep-model references (meta axioms=[], deep_model_references=[]; no @ContractOnly/@Pure) — the A-legs are genuinely vacuous, so refinement fidelity is the only trust point. Verified refinement.md legs A1-A5/B1-B2/C1/D1-D2/E are all R or I (no kind-3, no dead axioms); mapping.md modeled_functions bind build_glyph<->Text.__init__/_reset_visual_defaults, set_pref<->set_antialiased, get_pref<->get_antialiased, copy_state<->update_from correctly at base_commit.

Spec strength: every test-observable value is pinned. build_glyph pins Result().pref on BOTH branches (Implies(supplied is None, ==default) and Implies(supplied is not None, ==supplied)); set_pref pins g.pref==value AND g.dirty; get_pref pins Result()==g.pref under a read-only Acc(g.pref,1/2) frame; copy_state pins dst.pref==src.pref, dst.dirty, and preserves src under Acc(src.pref,1/2).

The ONLY spec gap: build_glyph's postcondition requires Acc(Result().dirty) but NOT its value, so an impl may set dirty(<->stale) to any value at construction and still verify. I attacked this gap with TWO distinct verifying candidates and materialized+resolved each faithful patch.

Attacks (7), each run via `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25775 <path>` (concurrent, <=3 JVMs):
- atk_1 (dirty-gap, unconditional): build_glyph sets g.dirty=False after (optional) set_pref. weakness exit 0 = CANDIDATE (shares spec + verifies, 10.3s). Faithful patch patch_atk1.diff (self.stale=False at end of _reset_visual_defaults). run_resolve: RESOLVED (7/7 F2P, 89/89 P2P, 0 failures) — does NOT break spec.
- atk_7 (dirty-gap, else-branch): build_glyph sets g.dirty=False only when supplied is None. weakness exit 0 = CANDIDATE (9.8s). Faithful patch patch_atk7.diff (else: self.stale=False in the antialiased guard). run_resolve: RESOLVED (7/7 F2P, 89/89 P2P, 0 failures) — does NOT break spec.
- atk_2 (prepatch bug #1, ungrounded override): build_glyph ignores supplied (always default). weakness exit 2 = verification FAILED (spec's Implies(supplied is not None, ==supplied) rejects it). Reproduces prepatch model_prepatch.py.
- atk_3 (prepatch bug #2, no-op setter): set_pref only sets dirty, doesn't store value. weakness exit 2 = FAILED (g.pref==value rejects it). Reproduces model_prepatch_2.py.
- atk_4 (partial-domain): build_glyph honors supplied only when truthy (`if supplied is not None and supplied`). weakness exit 2 = FAILED (breaks supplied==False case, spec catches it).
- atk_5 (control-flow-effect): copy_state sets dst.dirty=False. weakness exit 2 = FAILED (copy_state pins dst.dirty True).
- atk_6 (ungrounded-oracle echo/boundary): get_pref returns constant True. weakness exit 2 = FAILED (Result()==g.pref rejects it).

Positive control: positive_control.py (verbatim model.py) VERIFIES (9.72s). Gold patch (control) run_resolve: RESOLVED (7/7 F2P, 89/89 P2P). prepatch_reproduced=true (atk_2 and atk_3 mirror the two shipped prepatch models and fail verification as expected).

Conclusion: the sole spec gap (unpinned construction-time dirty/stale value) is BENIGN — Text.__init__ calls self.update(kwargs) after _reset_visual_defaults and no hidden test (incl. test_text_stale in P2P) observes construction-time stale in a way that a stale=False break flips; both faithful materializations resolve identically to gold. No same-spec verifying impl was found whose faithful patch fails to resolve. verify=>correct holds on this bundle. VERDICT: SOUND.

Commands:
  bash scripts/nagini_verify.sh positive_control.py  -> exit 0
  python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25775 {1..7}.py  -> exits 0,2,2,2,2,2,0
  python resolve.py {gold,atk1,atk7} <patch> (run_resolve, timeout 3600)  -> all resolved=true, completed=true

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25775.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A drawable glyph object carries its own per-object edge-smoothing preference,
  rather than always deferring to a single global default. The desired
  behaviour is exactly:

    (1) Construction. A glyph is created with an optional preference argument.
        When that argument is omitted (the absent value), the object's stored
        preference is the global default supplied at construction time. When
        the argument is supplied, the object's stored preference is exactly the
        supplied value, overriding the global default.

    (2) Read-back. Querying a glyph's preference returns exactly the value it
        currently stores.

    (3) Update. Setting a glyph's preference to a value makes a subsequent query
        return that value, and marks the object as needing redraw.

    (4) Copying. Adopting another glyph's visual state copies the source glyph's
        stored preference, so the destination subsequently reports the source's
        value.

The preference is a boolean; "absent" is modelled by the optional ``None``.
The object is modelled as a minimal class carrying only the one touched field
(its stored preference) plus a redraw flag.  This is the per-object state whose
presence/absence the tested behaviour distinguishes from the global default.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no callee is axiomatized: the behaviour is pure in-object state — a stored
# preference, its read-back, its update, and its copy — modelled deeply.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Glyph:
    def __init__(self, pref: bool) -> None:
        Ensures(Acc(self.pref) and self.pref == pref)        # type: ignore
        Ensures(Acc(self.dirty) and self.dirty)              # type: ignore
        self.pref = pref      # type: bool
        self.dirty = True     # type: bool


def build_glyph(default: bool, supplied: Optional[bool]) -> Glyph:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().pref))
    Ensures(Acc(Result().dirty))
    # (1) absent argument -> the global default; supplied argument -> that value
    Ensures(Implies(supplied is None, Result().pref == default))
    Ensures(Implies(supplied is not None, Result().pref == supplied))
    # post-conditions-end
    # impl-start
    g = Glyph(default)
    if supplied is not None:
        set_pref(g, supplied)
    return g
    # impl-end


def set_pref(g: Glyph, value: bool) -> None:
    # pre-conditions-start
    Requires(Acc(g.pref))
    Requires(Acc(g.dirty))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(g.pref) and g.pref == value)
    # (3) update marks the object as needing redraw
    Ensures(Acc(g.dirty) and g.dirty)
    # post-conditions-end
    # impl-start
    g.pref = value
    g.dirty = True
    # impl-end


def get_pref(g: Glyph) -> bool:
    # pre-conditions-start
    Requires(Acc(g.pref, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(g.pref, 1 / 2))
    # (2) read-back returns exactly the stored preference
    Ensures(Result() == g.pref)
    # post-conditions-end
    # impl-start
    return g.pref
    # impl-end


def copy_state(dst: Glyph, src: Glyph) -> None:
    # pre-conditions-start
    Requires(Acc(dst.pref))
    Requires(Acc(dst.dirty))
    Requires(Acc(src.pref, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(src.pref, 1 / 2))
    Ensures(Acc(dst.pref) and Acc(dst.dirty))
    # (4) destination adopts the source's stored preference
    Ensures(dst.pref == src.pref)
    Ensures(dst.dirty)
    # post-conditions-end
    # impl-start
    dst.pref = src.pref
    dst.dirty = True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec surface: model.py has ZERO axioms and ZERO deep-model references (meta axioms=[], deep_model_references=[]; no @ContractOnly/@Pure) — the A-legs are genuinely vacuous, so refinement fidelity is the only trust point. Verified refinement.md legs A1-A5/B1-B2/C1/D1-D2/E are all R or I (no kind-3, no dead axioms); mapping.md modeled_functions bind build_glyph<->Text.__init__/_reset_visual_defaults, set_pref<->set_antialiased, get_pref<->get_antialiased, copy_state<->update_from correctly at base_commit.

Spec strength: every test-observable value is pinned. build_glyph pins Result().pref on BOTH branches (Implies(supplied is None, ==default) and Implies(supplied is not None, ==supplied)); set_pref pins g.pref==value AND g.dirty; get_pref pins Result()==g.pref under a read-only Acc(g.pref,1/2) frame; copy_state pins dst.pref==src.pref, dst.dirty, and preserves src under Acc(src.pref,1/2).

The ONLY spec gap: build_glyph's postcondition requires Acc(Result().dirty) but NOT its value, so an impl may set dirty(<->stale) to any value at construction and still verify. I attacked this gap with TWO distinct verifying candidates and materialized+resolved each faithful patch.

Attacks (7), each run via `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25775 <path>` (concurrent, <=3 JVMs):
- atk_1 (dirty-gap, unconditional): build_glyph sets g.dirty=False after (optional) set_pref. weakness exit 0 = CANDIDATE (shares spec + verifies, 10.3s). Faithful patch patch_atk1.diff (self.stale=False at end of _reset_visual_defaults). run_resolve: RESOLVED (7/7 F2P, 89/89 P2P, 0 failures) — does NOT break spec.
- atk_7 (dirty-gap, else-branch): build_glyph sets g.dirty=False only when supplied is None. weakness exit 0 = CANDIDATE (9.8s). Faithful patch patch_atk7.diff (else: self.stale=False in the antialiased guard). run_resolve: RESOLVED (7/7 F2P, 89/89 P2P, 0 failures) — does NOT break spec.
- atk_2 (prepatch bug #1, ungrounded override): build_glyph ignores supplied (always default). weakness exit 2 = verification FAILED (spec's Implies(supplied is not None, ==supplied) rejects it). Reproduces prepatch model_prepatch.py.
- atk_3 (prepatch bug #2, no-op setter): set_pref only sets dirty, doesn't store value. weakness exit 2 = FAILED (g.pref==value rejects it). Reproduces model_prepatch_2.py.
- atk_4 (partial-domain): build_glyph honors supplied only when truthy (`if supplied is not None and supplied`). weakness exit 2 = FAILED (breaks supplied==False case, spec catches it).
- atk_5 (control-flow-effect): copy_state sets dst.dirty=False. weakness exit 2 = FAILED (copy_state pins dst.dirty True).
- atk_6 (ungrounded-oracle echo/boundary): get_pref returns constant True. weakness exit 2 = FAILED (Result()==g.pref rejects it).

Positive control: positive_control.py (verbatim model.py) VERIFIES (9.72s). Gold patch (control) run_resolve: RESOLVED (7/7 F2P, 89/89 P2P). prepatch_reproduced=true (atk_2 and atk_3 mirror the two shipped prepatch models and fail verification as expected).

Conclusion: the sole spec gap (unpinned construction-time dirty/stale value) is BENIGN — Text.__init__ calls self.update(kwargs) after _reset_visual_defaults and no hidden test (incl. test_text_stale in P2P) observes construction-time stale in a way that a stale=False break flips; both faithful materializations resolve identically to gold. No same-spec verifying impl was found whose faithful patch fails to resolve. verify=>correct holds on this bundle. VERDICT: SOUND.

Commands:
  bash scripts/nagini_verify.sh positive_control.py  -> exit 0
  python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25775 {1..7}.py  -> exits 0,2,2,2,2,2,0
  python resolve.py {gold,atk1,atk7} <patch> (run_resolve, timeout 3600)  -> all resolved=true, completed=true

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo) confirmed for all four modeled functions against the gold-patched matplotlib.text.Text (mapping.md bindings). Checked exhaustively over the finite domain (bool default × Optional[bool] supplied × both 'absent' spellings, plus set/get/copy interleavings); no diverging input found.

Per-callee correspondence:
- build_glyph(default,supplied) ↔ Text.__init__/_reset_visual_defaults: real sets self._antialiased=rcParams['text.antialiased'] (=default) then `if antialiased is not None: self.set_antialiased(antialiased)`. Spec's two Implies clauses (supplied is None → pref==default; supplied not None → pref==supplied) match exactly. stale/dirty is True post-construct (empirically confirmed on base repo).
- set_pref ↔ set_antialiased: _antialiased=value; stale=True — identical; postconditions g.pref==value ∧ g.dirty match.
- get_pref ↔ get_antialiased: return self._antialiased — identical; Acc(g.pref,1/2) read-only frame is faithful.
- copy_state ↔ update_from: self._antialiased=other._antialiased; self.stale=True with source untouched — matches; fractional Requires(src.pref,1/2) mirrors read-only source.

The bool/Optional[bool] domain restriction equals the tested F2P domain (a sound abstraction of the boolean flag, not an over-constraint). No modeled postcondition asserts behaviour the real callee lacks; the spec is neither too strong nor drifting. same-spec toolkit confirms the model shares the bundle's exact spec (exit 0). Note: could not build the patched extension modules in-worktree (numpy/_c_internal_utils unbuilt), so the runtime G-CONF fuzz was verified by source-reading the gold patch hunks rather than execution; every mapped op is a literal assignment, so this does not weaken the FAITHFUL finding.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged against the public problem_statement only (not hints_text). The problem_statement already discloses the full edit intent: '[ENH]: Add get/set_antialiased to Text objects'; that Text currently retrieves antialiasing via global rcParams['text.antialias'] and should be per-artist configurable via set_antialiased plus a getter; 'also adjusting Annotations accordingly'; and 'use that info in the drawing stage' (replacing the rcParams access with GraphicsContext state).

Mechanical screen: leakage.screen PASSES (rep.passed=True, hard_failures=[]). Spec view (markers.spec_view) reproduced and inspected manually.

Spec view leaks nothing beyond the public statement:
- Identifiers fully abstracted: Glyph, pref, dirty, build_glyph, set_pref, get_pref, copy_state. None embeds a patched repo symbol (set_antialiased, get_antialiased, update_from, _reset_visual_defaults, draw, draw_text, get_rotation_mode). No L2/L5 identifier collision.
- Domain term deliberately paraphrased as 'edge-smoothing preference'; 'antialiased'/'antialiasing' and 'rcParams' never appear in the spec view.
- No patched file path (text.py, backend_agg.py, backend_cairo.py), no dotted module path, no diff/patch marker, no gold-patch line reproduced.
- Docstring states DESIRED BEHAVIOUR ('stated as desired behaviour, not as an edit') across four clauses: construct-with-default-or-override (clause 1 = the per-artist configurability the statement requests), read-back (clause 2 = the getter), update-marks-redraw (clause 3 = the setter), copy-visual-state (clause 4). No bug/fix narration.

The only facet not stated verbatim in the problem_statement is clause (4) (copy/update_from propagation of the new attribute). It is expressed purely as an abstract behavioural property of adopting another glyph's visual state, with no named repo method, file, or reproduced patch text — a natural refinement of the publicized per-object feature, not a localization or reconstruction of the gold edit. No spec-view line localizes the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
