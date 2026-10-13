# P2 adversarial audit — matplotlib__matplotlib-20859

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ParentRejected(Exception):
@@ -56,7 +55,6 @@
     when the parent is a coordinate-system artist)."""
 
     def __init__(self, tag: int, host_canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.tag) and self.tag == tag)
         Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
         self.tag = tag                # type: int
@@ -68,7 +66,6 @@
     identity of the canvas the new artist belongs to."""
 
     def __init__(self, is_coords: bool, canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
         Ensures(Acc(self.canvas) and self.canvas == canvas)
         self.is_coords = is_coords  # type: bool
@@ -108,7 +105,6 @@
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(parent.tag, 1 / 2))
     Requires(Acc(parent.host_canvas, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.tag, 1 / 2))
@@ -137,7 +133,7 @@
     # impl-start
     if is_coords_artist(parent.tag):
         return Attached(True, parent.host_canvas)
-    elif in_canvas_family(parent.tag):
+    elif parent.tag == TAG_TOPLEVEL:
         return Attached(False, parent.tag)
     else:
         raise ParentRejected()
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ParentRejected(Exception):
@@ -56,7 +55,6 @@
     when the parent is a coordinate-system artist)."""
 
     def __init__(self, tag: int, host_canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.tag) and self.tag == tag)
         Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
         self.tag = tag                # type: int
@@ -68,7 +66,6 @@
     identity of the canvas the new artist belongs to."""
 
     def __init__(self, is_coords: bool, canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
         Ensures(Acc(self.canvas) and self.canvas == canvas)
         self.is_coords = is_coords  # type: bool
@@ -108,7 +105,6 @@
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(parent.tag, 1 / 2))
     Requires(Acc(parent.host_canvas, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.tag, 1 / 2))
@@ -137,8 +133,6 @@
     # impl-start
     if is_coords_artist(parent.tag):
         return Attached(True, parent.host_canvas)
-    elif in_canvas_family(parent.tag):
-        return Attached(False, parent.tag)
     else:
         raise ParentRejected()
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ParentRejected(Exception):
@@ -56,7 +55,6 @@
     when the parent is a coordinate-system artist)."""
 
     def __init__(self, tag: int, host_canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.tag) and self.tag == tag)
         Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
         self.tag = tag                # type: int
@@ -68,7 +66,6 @@
     identity of the canvas the new artist belongs to."""
 
     def __init__(self, is_coords: bool, canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
         Ensures(Acc(self.canvas) and self.canvas == canvas)
         self.is_coords = is_coords  # type: bool
@@ -108,7 +105,6 @@
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(parent.tag, 1 / 2))
     Requires(Acc(parent.host_canvas, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.tag, 1 / 2))
@@ -136,9 +132,9 @@
     # post-conditions-end
     # impl-start
     if is_coords_artist(parent.tag):
-        return Attached(True, parent.host_canvas)
+        return Attached(False, parent.host_canvas)
     elif in_canvas_family(parent.tag):
-        return Attached(False, parent.tag)
+        return Attached(True, parent.tag)
     else:
         raise ParentRejected()
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ParentRejected(Exception):
@@ -56,7 +55,6 @@
     when the parent is a coordinate-system artist)."""
 
     def __init__(self, tag: int, host_canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.tag) and self.tag == tag)
         Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
         self.tag = tag                # type: int
@@ -68,7 +66,6 @@
     identity of the canvas the new artist belongs to."""
 
     def __init__(self, is_coords: bool, canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
         Ensures(Acc(self.canvas) and self.canvas == canvas)
         self.is_coords = is_coords  # type: bool
@@ -108,7 +105,6 @@
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(parent.tag, 1 / 2))
     Requires(Acc(parent.host_canvas, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.tag, 1 / 2))
@@ -138,7 +134,7 @@
     if is_coords_artist(parent.tag):
         return Attached(True, parent.host_canvas)
     elif in_canvas_family(parent.tag):
-        return Attached(False, parent.tag)
+        return Attached(False, parent.host_canvas)
     else:
         raise ParentRejected()
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ParentRejected(Exception):
@@ -56,7 +55,6 @@
     when the parent is a coordinate-system artist)."""
 
     def __init__(self, tag: int, host_canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.tag) and self.tag == tag)
         Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
         self.tag = tag                # type: int
@@ -68,7 +66,6 @@
     identity of the canvas the new artist belongs to."""
 
     def __init__(self, is_coords: bool, canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
         Ensures(Acc(self.canvas) and self.canvas == canvas)
         self.is_coords = is_coords  # type: bool
@@ -108,7 +105,6 @@
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(parent.tag, 1 / 2))
     Requires(Acc(parent.host_canvas, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.tag, 1 / 2))
@@ -135,9 +131,9 @@
             and (not in_canvas_family(parent.tag)))
     # post-conditions-end
     # impl-start
-    if is_coords_artist(parent.tag):
+    if parent.tag == TAG_COORDS:
         return Attached(True, parent.host_canvas)
-    elif in_canvas_family(parent.tag):
+    elif parent.tag == TAG_TOPLEVEL or parent.tag == TAG_NESTED:
         return Attached(False, parent.tag)
     else:
         raise ParentRejected()
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ParentRejected(Exception):
@@ -56,7 +55,6 @@
     when the parent is a coordinate-system artist)."""
 
     def __init__(self, tag: int, host_canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.tag) and self.tag == tag)
         Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
         self.tag = tag                # type: int
@@ -68,7 +66,6 @@
     identity of the canvas the new artist belongs to."""
 
     def __init__(self, is_coords: bool, canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
         Ensures(Acc(self.canvas) and self.canvas == canvas)
         self.is_coords = is_coords  # type: bool
@@ -108,7 +105,6 @@
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(parent.tag, 1 / 2))
     Requires(Acc(parent.host_canvas, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.tag, 1 / 2))
@@ -135,9 +131,11 @@
             and (not in_canvas_family(parent.tag)))
     # post-conditions-end
     # impl-start
-    if is_coords_artist(parent.tag):
+    coords = is_coords_artist(parent.tag)
+    family = in_canvas_family(parent.tag)
+    if coords:
         return Attached(True, parent.host_canvas)
-    elif in_canvas_family(parent.tag):
+    elif family:
         return Attached(False, parent.tag)
     else:
         raise ParentRejected()
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ParentRejected(Exception):
@@ -56,7 +55,6 @@
     when the parent is a coordinate-system artist)."""
 
     def __init__(self, tag: int, host_canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.tag) and self.tag == tag)
         Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
         self.tag = tag                # type: int
@@ -68,7 +66,6 @@
     identity of the canvas the new artist belongs to."""
 
     def __init__(self, is_coords: bool, canvas: int) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
         Ensures(Acc(self.canvas) and self.canvas == canvas)
         self.is_coords = is_coords  # type: bool
@@ -108,7 +105,6 @@
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(parent.tag, 1 / 2))
     Requires(Acc(parent.host_canvas, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.tag, 1 / 2))
@@ -137,8 +133,6 @@
     # impl-start
     if is_coords_artist(parent.tag):
         return Attached(True, parent.host_canvas)
-    elif in_canvas_family(parent.tag):
+    else:
         return Attached(False, parent.tag)
-    else:
-        raise ParentRejected()
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-20859.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A plotting-container artist is attached to a *parent*. The parent may be one
  of two unrelated families:

    * a coordinate-system artist (the kind that itself already belongs to an
      enclosing canvas), or
    * any member of the canvas-surface family. That family has a common base
      type, and the family includes BOTH the whole top-level canvas AND a
      nested canvas region carved out of a larger canvas. A nested region is a
      genuine member of the canvas-surface family (it shares the family's base
      type) even though it is not the top-level canvas type.

  The behaviour pinned here is how the attachment classifies the parent and
  what canvas the new artist comes to belong to:

    * if the parent is a coordinate-system artist, the artist is flagged as
      belonging to coordinates, and the canvas it belongs to is the canvas that
      coordinate-system artist already sits on;
    * otherwise, if the parent is ANY member of the canvas-surface family
      (the top-level canvas OR a nested region alike), the artist is flagged as
      not-coordinates and the canvas it belongs to is the parent itself;
    * otherwise the attachment is rejected.

  The discriminating case: a nested canvas region is a member of the
  canvas-surface family, so attaching the artist to it must SUCCEED — flag
  not-coordinates and make the artist belong to that nested region — and must
  NOT be rejected merely because the nested region is not the top-level canvas
  type.

The parent is modelled by a small object carrying a family tag and the identity
of the canvas it already sits on. Membership in the canvas-surface family is a
pure predicate over the tag that mirrors the real subtype relation (the nested
region and the top-level canvas both carry the family base type). Rejection is
a user-defined exception (a builtin exception in an `Exsures` crashes the Nagini
translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class ParentRejected(Exception):
    """Signals a parent that belongs to neither family (the `TypeError` the
    desired behaviour raises). A builtin exception in an `Exsures` crashes the
    Nagini translator (mapping.md §2)."""


class Parent:
    """A candidate parent. `tag` identifies its class family; `host_canvas`
    is the identity of the canvas the parent itself already sits on (only used
    when the parent is a coordinate-system artist)."""

    def __init__(self, tag: int, host_canvas: int) -> None:
        Ensures(Acc(self.tag) and self.tag == tag)
        Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
        self.tag = tag                # type: int
        self.host_canvas = host_canvas  # type: int


class Attached:
    """The outcome of a successful attachment: the coordinates flag and the
    identity of the canvas the new artist belongs to."""

    def __init__(self, is_coords: bool, canvas: int) -> None:
        Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
        Ensures(Acc(self.canvas) and self.canvas == canvas)
        self.is_coords = is_coords  # type: bool
        self.canvas = canvas        # type: int


# Class-family tags (distinct identities; the exact integers are immaterial,
# only the subtype relation below matters).
TAG_COORDS = 0      # a coordinate-system artist
TAG_TOPLEVEL = 1    # the top-level canvas type
TAG_NESTED = 2      # a nested canvas region (shares the family base type)
TAG_FOREIGN = 3     # something in neither family


# pure-start
@Pure
def is_coords_artist(tag: int) -> bool:
    """Whether the parent is a coordinate-system artist."""
    return tag == TAG_COORDS


@Pure
def in_canvas_family(tag: int) -> bool:
    """Whether the parent is a member of the canvas-surface family, i.e. its
    class carries the family base type. BOTH the top-level canvas and a nested
    canvas region are members (they share the base type); a coordinate-system
    artist and a foreign object are not. Mirrors the real subtype relation
    (mapping.md §3)."""
    return tag == TAG_TOPLEVEL or tag == TAG_NESTED
# pure-end


def attach(parent: Parent) -> Attached:
    # pre-conditions-start
    # The parent is read-only (the attachment inspects it but does not mutate
    # it); fractional permission, required and ensured, so no caller can satisfy
    # a postcondition vacuously by overwriting the input.
    Requires(Acc(parent.tag, 1 / 2))
    Requires(Acc(parent.host_canvas, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(parent.tag, 1 / 2))
    Ensures(Acc(parent.host_canvas, 1 / 2))
    # Returns normally (a successful attachment) exactly when the parent is a
    # coordinate-system artist OR any member of the canvas-surface family.
    Ensures(is_coords_artist(parent.tag) or in_canvas_family(parent.tag))
    # On success the result carries full permission to a fresh outcome object.
    Ensures(Acc(Result().is_coords) and Acc(Result().canvas))
    # Coordinate-system parent: flagged as coordinates, belongs to the canvas
    # the parent already sits on.
    Ensures(Implies(is_coords_artist(parent.tag),
                    Result().is_coords and Result().canvas == parent.host_canvas))
    # Any canvas-family parent (top-level OR nested region alike): flagged as
    # not-coordinates, belongs to the parent itself. Pinned for EVERY family
    # member so the nested region is not excluded.
    Ensures(Implies(in_canvas_family(parent.tag),
                    (not Result().is_coords) and Result().canvas == parent.tag))
    # Rejects (raises) exactly when the parent belongs to neither family.
    Exsures(ParentRejected,
            Acc(parent.tag, 1 / 2)
            and Acc(parent.host_canvas, 1 / 2)
            and (not is_coords_artist(parent.tag))
            and (not in_canvas_family(parent.tag)))
    # post-conditions-end
    # impl-start
    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    elif in_canvas_family(parent.tag):
        return Attached(False, parent.tag)
    else:
        raise ParentRejected()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of matplotlib__matplotlib-20859/nagini.

SPEC SHAPE: attach(parent) is FULLY pinned by the postconditions for every tag class: is_coords_artist(tag) => (is_coords=True, canvas=host_canvas); in_canvas_family(tag) => (is_coords=False, canvas=parent.tag); else raise ParentRejected. is_coords_artist/in_canvas_family are @Pure deep models over the tag; NO @ContractOnly axiom (meta axioms=[]).

POSITIVE CONTROL: pos_control.py (= bundle model.py) verifies in 11.3s (scripts/nagini_verify.sh exit 0).

### ATTACKS (7 run, >=5; command: python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-20859 <atk>):
- atk_1.py PREPATCH BUG (narrow `parent.tag == TAG_TOPLEVEL`, rejects NESTED): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Prepatch bug reproduced/rejected by spec (matches model_prepatch.py; the Exsures `not in_canvas_family` + family postcondition sense the NESTED case).
- atk_2.py PARTIAL-DOMAIN (reject all canvas-family): does not verify (exit 2).
- atk_3.py BOUNDARY (coords flags swapped): does not verify (exit 2).
- atk_4.py CONTROL-FLOW-EFFECT (family parent attaches to host_canvas not itself): does not verify (exit 2).
- atk_7.py UNGROUNDED/ effect (foreign returns instead of raising, no reject branch): does not verify (exit 2).
- atk_5.py ECHO (inline tag comparisons parent.tag==TAG_COORDS / ==TAG_TOPLEVEL or ==TAG_NESTED): CANDIDATE (shares spec AND verifies, 13.4s). Faithful refined patch = gold verbatim. run_resolve => RESOLVED=True COMPLETED=True attempts=1 flaky=False (see resolve_atk_5.txt).
- atk_6.py ECHO (precompute booleans coords/family then branch): CANDIDATE (shares spec AND verifies, 12.6s). Faithful refined patch = gold with the elif wrapped in a bool() no-op (behaviourally identical; applies within gold hunk footprint). run_resolve => RESOLVED=True COMPLETED=True attempts=1 flaky=False (see resolve_atk_6.txt).

Both verifying candidates are behavioural echoes of the gold dispatch; each materialized faithful patch RESOLVES under the official harness (run_resolve, timeout 1800). No verifying wrong-impl produced a non-resolving patch => verify does NOT admit an incorrect impl here.

REFINEMENT.MD LEG AUDIT: A1=R, A2=R+A-reference, A3=A-reference+R, A4=R. Section B: no kind-3 (the one genuinely changed op, Figure->FigureBase widening, is modelled DEEPLY via in_canvas_family, not behind an axiom about the function under change). No A-consumed legs: model.py has no @ContractOnly, meta.axioms=[]. The single A-reference (in_canvas_family/is_coords_artist deep model) is validated by G-AX: axiom_check.py exit 0 -- deep model == real matplotlib issubclass over Axes/Figure/SubFigure/Line2D, including discriminator SubFigure in FigureBase and SubFigure not in Figure. Correspondence to the real callees (isinstance(parent, Axes)/(parent, FigureBase)) holds.

VERDICT: SOUND. >=5 attacks run, prepatch reproduced, positive control verifies, both verifying candidates' materialized faithful patches resolve; refinement legs are all R/A-reference/I with no kind-3 and the A-reference correspondence holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-20859.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A plotting-container artist is attached to a *parent*. The parent may be one
  of two unrelated families:

    * a coordinate-system artist (the kind that itself already belongs to an
      enclosing canvas), or
    * any member of the canvas-surface family. That family has a common base
      type, and the family includes BOTH the whole top-level canvas AND a
      nested canvas region carved out of a larger canvas. A nested region is a
      genuine member of the canvas-surface family (it shares the family's base
      type) even though it is not the top-level canvas type.

  The behaviour pinned here is how the attachment classifies the parent and
  what canvas the new artist comes to belong to:

    * if the parent is a coordinate-system artist, the artist is flagged as
      belonging to coordinates, and the canvas it belongs to is the canvas that
      coordinate-system artist already sits on;
    * otherwise, if the parent is ANY member of the canvas-surface family
      (the top-level canvas OR a nested region alike), the artist is flagged as
      not-coordinates and the canvas it belongs to is the parent itself;
    * otherwise the attachment is rejected.

  The discriminating case: a nested canvas region is a member of the
  canvas-surface family, so attaching the artist to it must SUCCEED — flag
  not-coordinates and make the artist belong to that nested region — and must
  NOT be rejected merely because the nested region is not the top-level canvas
  type.

The parent is modelled by a small object carrying a family tag and the identity
of the canvas it already sits on. Membership in the canvas-surface family is a
pure predicate over the tag that mirrors the real subtype relation (the nested
region and the top-level canvas both carry the family base type). Rejection is
a user-defined exception (a builtin exception in an `Exsures` crashes the Nagini
translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class ParentRejected(Exception):
    """Signals a parent that belongs to neither family (the `TypeError` the
    desired behaviour raises). A builtin exception in an `Exsures` crashes the
    Nagini translator (mapping.md §2)."""


class Parent:
    """A candidate parent. `tag` identifies its class family; `host_canvas`
    is the identity of the canvas the parent itself already sits on (only used
    when the parent is a coordinate-system artist)."""

    def __init__(self, tag: int, host_canvas: int) -> None:
        Ensures(Acc(self.tag) and self.tag == tag)
        Ensures(Acc(self.host_canvas) and self.host_canvas == host_canvas)
        self.tag = tag                # type: int
        self.host_canvas = host_canvas  # type: int


class Attached:
    """The outcome of a successful attachment: the coordinates flag and the
    identity of the canvas the new artist belongs to."""

    def __init__(self, is_coords: bool, canvas: int) -> None:
        Ensures(Acc(self.is_coords) and self.is_coords == is_coords)
        Ensures(Acc(self.canvas) and self.canvas == canvas)
        self.is_coords = is_coords  # type: bool
        self.canvas = canvas        # type: int


# Class-family tags (distinct identities; the exact integers are immaterial,
# only the subtype relation below matters).
TAG_COORDS = 0      # a coordinate-system artist
TAG_TOPLEVEL = 1    # the top-level canvas type
TAG_NESTED = 2      # a nested canvas region (shares the family base type)
TAG_FOREIGN = 3     # something in neither family


# pure-start
@Pure
def is_coords_artist(tag: int) -> bool:
    """Whether the parent is a coordinate-system artist."""
    return tag == TAG_COORDS


@Pure
def in_canvas_family(tag: int) -> bool:
    """Whether the parent is a member of the canvas-surface family, i.e. its
    class carries the family base type. BOTH the top-level canvas and a nested
    canvas region are members (they share the base type); a coordinate-system
    artist and a foreign object are not. Mirrors the real subtype relation
    (mapping.md §3)."""
    return tag == TAG_TOPLEVEL or tag == TAG_NESTED
# pure-end


def attach(parent: Parent) -> Attached:
    # pre-conditions-start
    # The parent is read-only (the attachment inspects it but does not mutate
    # it); fractional permission, required and ensured, so no caller can satisfy
    # a postcondition vacuously by overwriting the input.
    Requires(Acc(parent.tag, 1 / 2))
    Requires(Acc(parent.host_canvas, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(parent.tag, 1 / 2))
    Ensures(Acc(parent.host_canvas, 1 / 2))
    # Returns normally (a successful attachment) exactly when the parent is a
    # coordinate-system artist OR any member of the canvas-surface family.
    Ensures(is_coords_artist(parent.tag) or in_canvas_family(parent.tag))
    # On success the result carries full permission to a fresh outcome object.
    Ensures(Acc(Result().is_coords) and Acc(Result().canvas))
    # Coordinate-system parent: flagged as coordinates, belongs to the canvas
    # the parent already sits on.
    Ensures(Implies(is_coords_artist(parent.tag),
                    Result().is_coords and Result().canvas == parent.host_canvas))
    # Any canvas-family parent (top-level OR nested region alike): flagged as
    # not-coordinates, belongs to the parent itself. Pinned for EVERY family
    # member so the nested region is not excluded.
    Ensures(Implies(in_canvas_family(parent.tag),
                    (not Result().is_coords) and Result().canvas == parent.tag))
    # Rejects (raises) exactly when the parent belongs to neither family.
    Exsures(ParentRejected,
            Acc(parent.tag, 1 / 2)
            and Acc(parent.host_canvas, 1 / 2)
            and (not is_coords_artist(parent.tag))
            and (not in_canvas_family(parent.tag)))
    # post-conditions-end
    # impl-start
    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    elif in_canvas_family(parent.tag):
        return Attached(False, parent.tag)
    else:
        raise ParentRejected()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of matplotlib__matplotlib-20859/nagini.

SPEC SHAPE: attach(parent) is FULLY pinned by the postconditions for every tag class: is_coords_artist(tag) => (is_coords=True, canvas=host_canvas); in_canvas_family(tag) => (is_coords=False, canvas=parent.tag); else raise ParentRejected. is_coords_artist/in_canvas_family are @Pure deep models over the tag; NO @ContractOnly axiom (meta axioms=[]).

POSITIVE CONTROL: pos_control.py (= bundle model.py) verifies in 11.3s (scripts/nagini_verify.sh exit 0).

### ATTACKS (7 run, >=5; command: python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-20859 <atk>):
- atk_1.py PREPATCH BUG (narrow `parent.tag == TAG_TOPLEVEL`, rejects NESTED): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Prepatch bug reproduced/rejected by spec (matches model_prepatch.py; the Exsures `not in_canvas_family` + family postcondition sense the NESTED case).
- atk_2.py PARTIAL-DOMAIN (reject all canvas-family): does not verify (exit 2).
- atk_3.py BOUNDARY (coords flags swapped): does not verify (exit 2).
- atk_4.py CONTROL-FLOW-EFFECT (family parent attaches to host_canvas not itself): does not verify (exit 2).
- atk_7.py UNGROUNDED/ effect (foreign returns instead of raising, no reject branch): does not verify (exit 2).
- atk_5.py ECHO (inline tag comparisons parent.tag==TAG_COORDS / ==TAG_TOPLEVEL or ==TAG_NESTED): CANDIDATE (shares spec AND verifies, 13.4s). Faithful refined patch = gold verbatim. run_resolve => RESOLVED=True COMPLETED=True attempts=1 flaky=False (see resolve_atk_5.txt).
- atk_6.py ECHO (precompute booleans coords/family then branch): CANDIDATE (shares spec AND verifies, 12.6s). Faithful refined patch = gold with the elif wrapped in a bool() no-op (behaviourally identical; applies within gold hunk footprint). run_resolve => RESOLVED=True COMPLETED=True attempts=1 flaky=False (see resolve_atk_6.txt).

Both verifying candidates are behavioural echoes of the gold dispatch; each materialized faithful patch RESOLVES under the official harness (run_resolve, timeout 1800). No verifying wrong-impl produced a non-resolving patch => verify does NOT admit an incorrect impl here.

REFINEMENT.MD LEG AUDIT: A1=R, A2=R+A-reference, A3=A-reference+R, A4=R. Section B: no kind-3 (the one genuinely changed op, Figure->FigureBase widening, is modelled DEEPLY via in_canvas_family, not behind an axiom about the function under change). No A-consumed legs: model.py has no @ContractOnly, meta.axioms=[]. The single A-reference (in_canvas_family/is_coords_artist deep model) is validated by G-AX: axiom_check.py exit 0 -- deep model == real matplotlib issubclass over Axes/Figure/SubFigure/Line2D, including discriminator SubFigure in FigureBase and SubFigure not in Figure. Correspondence to the real callees (isinstance(parent, Axes)/(parent, FigureBase)) holds.

VERDICT: SOUND. >=5 attacks run, prepatch reproduced, positive control verifies, both verifying candidates' materialized faithful patches resolve; refinement legs are all R/A-reference/I with no kind-3 and the A-reference correspondence holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on nagini/matplotlib__matplotlib-20859. The modeled function `attach` (abstracting the parent-classification dispatch in Legend.__init__, legend.py:433-442) is FAITHFUL to the real callee — the spec does not drift from or over-strengthen real repo behavior.

Evidence:
1. same-spec: the bundle model is recognized as sharing the exact frozen spec (exit 0); spec region intact.
2. Nagini verify of the bundle model: 'Verification successful', 11.14s, exit 0.
3. G-AX (axiom_check.py) passes: the deep model predicates in_canvas_family/is_coords_artist agree with the REAL issubclass relation over Axes/Figure/SubFigure/Line2D, and the discriminating facts hold (issubclass(SubFigure,FigureBase) True; issubclass(SubFigure,Figure) False). No @ContractOnly axiom consumed — the only opaque fact is the subtype relation, validated as an A-reference.
4. Real-repo behavior check (installed matplotlib, real matplotlib.legend.Legend): dispatch matches the model on ALL four representative parents:
   - Axes  -> isaxes=True,  leg.figure is ax.figure (== host_canvas)  [model: is_coords=True, canvas==host_canvas]
   - Figure -> isaxes=False, leg.figure is fig (== parent)            [model: is_coords=False, canvas==parent]
   - SubFigure (nested) -> isaxes=False, leg.figure is subfig         [model: is_coords=False, canvas==parent] — the discriminating F2P case (test_subfigure_legend)
   - Line2D (foreign) -> TypeError 'Legend needs either Axes or FigureBase as parent'  [model: raise ParentRejected]
5. Modeling of set_figure as a plain assignment is faithful for the produced inputs: the legend begins with self.figure is None, so set_figure's no-op / already-set RuntimeError guards (artist.py:719) provably never fire.

Mutual exclusivity (Axes vs FigureBase) is real (verified), matching the model's tag partition, so the isinstance ordering in the real dispatch introduces no divergence. No input in the modeled domain makes the spec disagree with the real callee; the spec is not too strong. No diverging input found -> FAITHFUL, no defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit (patch.diff): in lib/matplotlib/legend.py, `from matplotlib.figure import Figure` -> `FigureBase` and `elif isinstance(parent, Figure)` -> `elif isinstance(parent, FigureBase)`, plus the TypeError message updated to 'either Axes or FigureBase' — so a SubFigure (a FigureBase but NOT a Figure) is accepted as a legend parent instead of rejected.

Baseline (public problem_statement) ALREADY discloses the entire fix: it is titled 'Adding a legend to a SubFigure doesn't work', gives the exact repro (subfig.legend()), quotes the verbatim TypeError('Legend needs either Axes or Figure as parent'), links legend.py L433-442, and states literally 'Changing L437 here to check against FigureBase fixes it.' That hands the solver the real class names (Figure, FigureBase, SubFigure), the file/line, and the Figure-vs-FigureBase base-type distinction. (hints_text is excluded from the baseline per instructions, but the fix is already fully in problem_statement.)

Spec view (impl region elided via markers.spec_view over NaginiBackend; regenerated and inspected — only the impl region is replaced by `...`) is STRICTLY MORE ABSTRACT than the public baseline:
  - Contains NO real class names (no Figure/FigureBase/SubFigure/Axes/Legend), NO file paths, NO line numbers, NO isinstance/issubclass, no gold-patch tokens.
  - Uses only abstracted vocabulary: 'coordinate-system artist' (Axes), 'canvas-surface family / common base type' (FigureBase), 'top-level canvas' (Figure), 'nested canvas region' (SubFigure).
  - Frames behaviour 'as desired behaviour, not as an edit' and pins the discriminating case (nested region shares the family base type => attachment must SUCCEED, not be rejected).

Every discriminating fact in the spec view (a nested canvas region shares the family base type and so must be accepted) is exactly and no more than what the problem_statement already states in concrete terms. The only concrete identifiers present are the public instance_id (matplotlib__matplotlib-20859), a Nagini-translator workaround note, and mapping.md pointers — none of which reconstruct the gold edit beyond what problem_statement already gives. Nothing in the spec view lets a solver reconstruct the gold edit beyond the public problem_statement; it is strictly weaker/more abstract. G-LEAK (lexical) also passes ('spec view clean'). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.
