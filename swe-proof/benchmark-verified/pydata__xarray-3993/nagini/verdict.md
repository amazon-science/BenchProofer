# P2 adversarial audit — pydata__xarray-3993

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -120,6 +120,11 @@
     if dim is not None and coord is None:
         coord = dim
         deprecated = True
+    else:
+        # primary-selector path: DIVERGE instead of answering. Every Ensures
+        # would hold vacuously if MustTerminate(2) does not reject this.
+        while True:
+            pass
 
     return Routed(coord, deprecated)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -120,6 +120,9 @@
     if dim is not None and coord is None:
         coord = dim
         deprecated = True
+    if coord is None and dim is None:
+        while True:
+            pass
 
     return Routed(coord, deprecated)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -120,6 +120,10 @@
     if dim is not None and coord is None:
         coord = dim
         deprecated = True
+    else:
+        n = 0
+        while n >= 0:
+            n = n + 1
 
     return Routed(coord, deprecated)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -116,10 +116,9 @@
     if dim is not None and coord is not None:
         raise ConflictingSelection()
 
-    deprecated = False
-    if dim is not None and coord is None:
-        coord = dim
-        deprecated = True
+    chosen = coord
+    if dim is not None:
+        chosen = dim
 
-    return Routed(coord, deprecated)
+    return Routed(chosen, False)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -120,6 +120,7 @@
     if dim is not None and coord is None:
         coord = dim
         deprecated = True
+        return Routed(coord, deprecated)
 
-    return Routed(coord, deprecated)
+    return Routed(dim, deprecated)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -113,9 +113,6 @@
     Exsures(ConflictingSelection, dim is not None and coord is not None)
     # post-conditions-end
     # impl-start
-    if dim is not None and coord is not None:
-        raise ConflictingSelection()
-
     deprecated = False
     if dim is not None and coord is None:
         coord = dim
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -116,10 +116,7 @@
     if dim is not None and coord is not None:
         raise ConflictingSelection()
 
-    deprecated = False
-    if dim is not None and coord is None:
-        coord = dim
-        deprecated = True
-
-    return Routed(coord, deprecated)
+    legacy_only = dim is not None and coord is None
+    routed = dim if legacy_only else coord
+    return Routed(routed, legacy_only)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-3993.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A coordinate-consuming operation accepts the coordinate it works along through
  a primary selector, while also continuing to accept the same selection through
  a now-superseded alternate selector that is kept only for backward
  compatibility. The desired routing of a single call is:

    * Supplying BOTH selectors at once is contradictory and is refused: the
      call signals the caller with a conflicting-selection failure and performs
      no computation.
    * Supplying ONLY the alternate (legacy) selector is still honoured: the
      computation proceeds along exactly that coordinate, but the call must also
      raise a forward-looking deprecation signal advising the caller to migrate
      to the primary selector.
    * Supplying ONLY the primary selector proceeds along that coordinate with
      no deprecation signal.

  The coordinate the computation is actually carried out along is, in every
  honoured case, exactly the one named by whichever single selector was supplied
  (the legacy selector when only it is given, the primary selector otherwise).

  The behaviour pinned here is the SELECTION ROUTING and its two signals: the
  refusal on a double selection, and — the discriminating obligation — that a
  call made through the legacy selector alone both proceeds along that
  coordinate AND emits the deprecation signal (which a call through the primary
  selector does not).

A coordinate selector is modelled abstractly by an integer identifier, with
``None`` meaning "not supplied"; the work the call then performs along the chosen
coordinate is unchanged and unobserved here. The conflicting-selection failure
is a user-defined exception class (a builtin exception in an ``Exsures`` crashes
the Nagini translator). The honoured-call outcome is a small result object
carrying the coordinate chosen and whether the deprecation signal was emitted.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ConflictingSelection(Exception):
    """The conflicting-selection failure surfaced to the caller when BOTH the
    primary and the legacy selector are supplied at once. User-defined stand-in
    for the value-error the desired behaviour requires (a builtin exception in
    an ``Exsures`` crashes the Nagini translator; mapping.md §2)."""
    pass


class Routed:
    """Observable outcome of an honoured call (mapping.md §2):

      * ``coord`` is the coordinate identifier the call actually works along —
        the single selector that was supplied.
      * ``deprecated`` is whether the forward-looking deprecation signal was
        emitted on this call (True exactly when the call was made through the
        legacy selector alone)."""

    def __init__(self, coord: Optional[int], deprecated: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.coord) and Acc(self.deprecated))
        Ensures(self.coord is coord and self.deprecated == deprecated)
        self.coord = coord            # type: Optional[int]
        self.deprecated = deprecated  # type: bool


# axioms-start
# (no axiomatized callee: the changed function reads only its two selector
#  arguments and routes them; the work it then performs along the chosen
#  coordinate is unchanged, independent of the routing decision, and unobserved
#  by this specification.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the routing decision is stated inline
#  over the two selector arguments.)
# pure-end


def select_coordinate(coord: Optional[int], dim: Optional[int]) -> Routed:
    # pre-conditions-start
    # The two selectors are abstract coordinate identifiers; ``None`` means the
    # selector was not supplied. ``coord`` is the primary selector, ``dim`` the
    # superseded legacy selector. Plain Optional[int] values, no heap permission.
    # TERMINATION: every honoured call must actually ANSWER (return its routed
    # outcome) and every refused call must actually raise — the routing decision
    # is a bounded prologue over two arguments. Without this obligation a
    # non-terminating implementation (e.g. one that diverges on the
    # primary-selector path instead of proceeding) satisfies every Ensures
    # vacuously; the real behaviour requires the call to complete.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # A normal return is reachable only when at most one selector is supplied
    # (supplying both is the refused case, below).
    Ensures(not (dim is not None and coord is not None))
    Ensures(Acc(Result().coord) and Acc(Result().deprecated))
    # ROUTING: the call works along exactly the single selector that was supplied
    # — the legacy selector when only it is given, the primary selector otherwise.
    Ensures(Implies(dim is not None and coord is None, Result().coord is dim))
    Ensures(Implies(not (dim is not None and coord is None), Result().coord is coord))
    # DEPRECATION SIGNAL: a call made through the legacy selector alone both
    # proceeds (returns normally, above) AND emits the deprecation signal; a call
    # through the primary selector (or with neither) does NOT emit it. This is
    # the discriminating obligation the behaviour change introduces.
    Ensures(Result().deprecated == (dim is not None and coord is None))
    # REFUSAL: supplying both selectors at once is contradictory and must NOT
    # return normally — it is surfaced as the conflicting-selection failure, and
    # ONLY then.
    Exsures(ConflictingSelection, dim is not None and coord is not None)
    # post-conditions-end
    # impl-start
    if dim is not None and coord is not None:
        raise ConflictingSelection()

    deprecated = False
    if dim is not None and coord is None:
        coord = dim
        deprecated = True

    return Routed(coord, deprecated)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: select_coordinate(coord, dim) fully pins the observable Routed via Ensures (coord identity for both routing branches + deprecated bool == (dim!=None and coord==None)) and Exsures (ConflictingSelection iff both supplied), under Requires(MustTerminate(2)). No axioms, no @Pure helpers, no ContractOnly callees (meta: axioms=[], deep_model_references=[]) — every refinement leg is R or I (§C, confirmed against spec+mapping; no kind-3). axiom_check.py run: rc=0, 'deep routing model == gold DataArray.integrate prologue on 20036 cases'.

ATTACK SUITE (all same-spec confirmed via `adversary same-spec`, rc=0; verify via `adversary weakness nagini pydata__xarray-3993 <path>`):
- atk_1.py control-flow-effect / VACUITY: `while True: pass` on the primary-selector path. weakness rc=2 NOT-A-COUNTEREXAMPLE (verification failed) — MustTerminate(2) rejects. This is the historical vacuity hole the obligation closes.
- atk_2.py VACUITY on neither-supplied (both None) path: diverge. weakness rc=2 rejected.
- atk_3.py control-flow-effect: unbounded `while n>=0: n+=1` (non-decreasing measure). weakness rc=2 rejected.
- atk_4.py PREPATCH BUG (partial-domain): route dim through as coord but Routed(chosen, False) — never emit deprecation. weakness rc=2 rejected (fails Ensures deprecated==...). PREPATCH REPRODUCED = the spec senses the change / pytest.warns(FutureWarning).
- atk_5.py boundary/swapped routing: return Routed(dim, ...) on primary-only path (dim is None there). weakness rc=2 rejected (fails Result().coord is coord).
- atk_6.py refusal boundary: omit the both-supplied guard (route coord instead of raising). weakness rc=2 rejected (fails Ensures not(both) / Exsures).
- atk_7.py ungrounded-oracle ECHO: gold-equivalent, respelled (`legacy_only = dim is not None and coord is None; routed = dim if legacy_only else coord; Routed(routed, legacy_only)`). weakness rc=0 CANDIDATE (shares spec AND verifies, 12.5s).

ECHO CANDIDATE RESOLVE (mandatory): materialized atk_7's faithful refined patch (gold verbatim except the `legacy_only` refactor of the routing body — behaviourally identical; validated `git apply --check` clean at base_commit 8cc34cb4). run_resolve('pydata__xarray-3993', atk_7_patch) => resolved=True, completed=True, attempts=1, not flaky; F2P 2/2 success (test_integrate[True], test_integrate[False]), P2P 2398/2398 success, 0 failures, patch_successfully_applied=True. => atk_7 is a resolving echo, NOT a weakness (per G-PANEL-1/G-EQ echo policy).

CONTROLS: pos_control.py (exact gold impl) weakness rc=0 CANDIDATE (verifies, 12.7s). GOLD patch run_resolve => resolved=True (F2P 2/2, P2P 2398/2398) — harness healthy at audit time. (Note: two earlier run_resolve attempts returned completed=False 'no report' due to heavy concurrent audit-concurrent runs docker contention + one corrupt hand-written hunk header; both re-run cleanly after regenerating the patch via git-diff in the testbed and retrying — final results are completed=True.)

CONCLUSION: The single verifying wrong-shaped candidate is a gold-equivalent echo whose faithful patch RESOLVES; all six genuinely-incorrect impls (3 divergence-vacuity, prepatch, swapped-routing, no-refusal) are REJECTED by the spec. verify => correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-3993.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A coordinate-consuming operation accepts the coordinate it works along through
  a primary selector, while also continuing to accept the same selection through
  a now-superseded alternate selector that is kept only for backward
  compatibility. The desired routing of a single call is:

    * Supplying BOTH selectors at once is contradictory and is refused: the
      call signals the caller with a conflicting-selection failure and performs
      no computation.
    * Supplying ONLY the alternate (legacy) selector is still honoured: the
      computation proceeds along exactly that coordinate, but the call must also
      raise a forward-looking deprecation signal advising the caller to migrate
      to the primary selector.
    * Supplying ONLY the primary selector proceeds along that coordinate with
      no deprecation signal.

  The coordinate the computation is actually carried out along is, in every
  honoured case, exactly the one named by whichever single selector was supplied
  (the legacy selector when only it is given, the primary selector otherwise).

  The behaviour pinned here is the SELECTION ROUTING and its two signals: the
  refusal on a double selection, and — the discriminating obligation — that a
  call made through the legacy selector alone both proceeds along that
  coordinate AND emits the deprecation signal (which a call through the primary
  selector does not).

A coordinate selector is modelled abstractly by an integer identifier, with
``None`` meaning "not supplied"; the work the call then performs along the chosen
coordinate is unchanged and unobserved here. The conflicting-selection failure
is a user-defined exception class (a builtin exception in an ``Exsures`` crashes
the Nagini translator). The honoured-call outcome is a small result object
carrying the coordinate chosen and whether the deprecation signal was emitted.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ConflictingSelection(Exception):
    """The conflicting-selection failure surfaced to the caller when BOTH the
    primary and the legacy selector are supplied at once. User-defined stand-in
    for the value-error the desired behaviour requires (a builtin exception in
    an ``Exsures`` crashes the Nagini translator; mapping.md §2)."""
    pass


class Routed:
    """Observable outcome of an honoured call (mapping.md §2):

      * ``coord`` is the coordinate identifier the call actually works along —
        the single selector that was supplied.
      * ``deprecated`` is whether the forward-looking deprecation signal was
        emitted on this call (True exactly when the call was made through the
        legacy selector alone)."""

    def __init__(self, coord: Optional[int], deprecated: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.coord) and Acc(self.deprecated))
        Ensures(self.coord is coord and self.deprecated == deprecated)
        self.coord = coord            # type: Optional[int]
        self.deprecated = deprecated  # type: bool


# axioms-start
# (no axiomatized callee: the changed function reads only its two selector
#  arguments and routes them; the work it then performs along the chosen
#  coordinate is unchanged, independent of the routing decision, and unobserved
#  by this specification.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the routing decision is stated inline
#  over the two selector arguments.)
# pure-end


def select_coordinate(coord: Optional[int], dim: Optional[int]) -> Routed:
    # pre-conditions-start
    # The two selectors are abstract coordinate identifiers; ``None`` means the
    # selector was not supplied. ``coord`` is the primary selector, ``dim`` the
    # superseded legacy selector. Plain Optional[int] values, no heap permission.
    # TERMINATION: every honoured call must actually ANSWER (return its routed
    # outcome) and every refused call must actually raise — the routing decision
    # is a bounded prologue over two arguments. Without this obligation a
    # non-terminating implementation (e.g. one that diverges on the
    # primary-selector path instead of proceeding) satisfies every Ensures
    # vacuously; the real behaviour requires the call to complete.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # A normal return is reachable only when at most one selector is supplied
    # (supplying both is the refused case, below).
    Ensures(not (dim is not None and coord is not None))
    Ensures(Acc(Result().coord) and Acc(Result().deprecated))
    # ROUTING: the call works along exactly the single selector that was supplied
    # — the legacy selector when only it is given, the primary selector otherwise.
    Ensures(Implies(dim is not None and coord is None, Result().coord is dim))
    Ensures(Implies(not (dim is not None and coord is None), Result().coord is coord))
    # DEPRECATION SIGNAL: a call made through the legacy selector alone both
    # proceeds (returns normally, above) AND emits the deprecation signal; a call
    # through the primary selector (or with neither) does NOT emit it. This is
    # the discriminating obligation the behaviour change introduces.
    Ensures(Result().deprecated == (dim is not None and coord is None))
    # REFUSAL: supplying both selectors at once is contradictory and must NOT
    # return normally — it is surfaced as the conflicting-selection failure, and
    # ONLY then.
    Exsures(ConflictingSelection, dim is not None and coord is not None)
    # post-conditions-end
    # impl-start
    if dim is not None and coord is not None:
        raise ConflictingSelection()

    deprecated = False
    if dim is not None and coord is None:
        coord = dim
        deprecated = True

    return Routed(coord, deprecated)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: select_coordinate(coord, dim) fully pins the observable Routed via Ensures (coord identity for both routing branches + deprecated bool == (dim!=None and coord==None)) and Exsures (ConflictingSelection iff both supplied), under Requires(MustTerminate(2)). No axioms, no @Pure helpers, no ContractOnly callees (meta: axioms=[], deep_model_references=[]) — every refinement leg is R or I (§C, confirmed against spec+mapping; no kind-3). axiom_check.py run: rc=0, 'deep routing model == gold DataArray.integrate prologue on 20036 cases'.

ATTACK SUITE (all same-spec confirmed via `adversary same-spec`, rc=0; verify via `adversary weakness nagini pydata__xarray-3993 <path>`):
- atk_1.py control-flow-effect / VACUITY: `while True: pass` on the primary-selector path. weakness rc=2 NOT-A-COUNTEREXAMPLE (verification failed) — MustTerminate(2) rejects. This is the historical vacuity hole the obligation closes.
- atk_2.py VACUITY on neither-supplied (both None) path: diverge. weakness rc=2 rejected.
- atk_3.py control-flow-effect: unbounded `while n>=0: n+=1` (non-decreasing measure). weakness rc=2 rejected.
- atk_4.py PREPATCH BUG (partial-domain): route dim through as coord but Routed(chosen, False) — never emit deprecation. weakness rc=2 rejected (fails Ensures deprecated==...). PREPATCH REPRODUCED = the spec senses the change / pytest.warns(FutureWarning).
- atk_5.py boundary/swapped routing: return Routed(dim, ...) on primary-only path (dim is None there). weakness rc=2 rejected (fails Result().coord is coord).
- atk_6.py refusal boundary: omit the both-supplied guard (route coord instead of raising). weakness rc=2 rejected (fails Ensures not(both) / Exsures).
- atk_7.py ungrounded-oracle ECHO: gold-equivalent, respelled (`legacy_only = dim is not None and coord is None; routed = dim if legacy_only else coord; Routed(routed, legacy_only)`). weakness rc=0 CANDIDATE (shares spec AND verifies, 12.5s).

ECHO CANDIDATE RESOLVE (mandatory): materialized atk_7's faithful refined patch (gold verbatim except the `legacy_only` refactor of the routing body — behaviourally identical; validated `git apply --check` clean at base_commit 8cc34cb4). run_resolve('pydata__xarray-3993', atk_7_patch) => resolved=True, completed=True, attempts=1, not flaky; F2P 2/2 success (test_integrate[True], test_integrate[False]), P2P 2398/2398 success, 0 failures, patch_successfully_applied=True. => atk_7 is a resolving echo, NOT a weakness (per G-PANEL-1/G-EQ echo policy).

CONTROLS: pos_control.py (exact gold impl) weakness rc=0 CANDIDATE (verifies, 12.7s). GOLD patch run_resolve => resolved=True (F2P 2/2, P2P 2398/2398) — harness healthy at audit time. (Note: two earlier run_resolve attempts returned completed=False 'no report' due to heavy concurrent audit-concurrent runs docker contention + one corrupt hand-written hunk header; both re-run cleanly after regenerating the patch via git-diff in the testbed and retrying — final results are completed=True.)

CONCLUSION: The single verifying wrong-shaped candidate is a gold-equivalent echo whose faithful patch RESOLVES; all six genuinely-incorrect impls (3 divergence-vacuity, prepatch, swapped-routing, no-refusal) are REJECTED by the spec. verify => correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical to the bundle (same-spec exit 0) and the model verifies under the pinned Nagini verifier (exit 0). Faithfulness assessed against the real repo callee — the gold DataArray.integrate routing prologue (xarray/core/dataarray.py post-patch): `if dim is not None and coord is not None: raise ValueError(...)`; `if dim is not None and coord is None: coord = dim; warnings.warn(FutureWarning)`; else route coord. The model's Ensures/Exsures encode exactly this three-way decision: (1) Exsures(ConflictingSelection, both supplied) ↔ the ValueError refusal; (2) Ensures(not both) forces raise-only on the both-supplied input; (3) routing Ensures — coord=dim when only dim, coord otherwise — matches the gold coord resolution; (4) Ensures(deprecated == (dim is not None and coord is None)) ↔ the conditional FutureWarning; (5) MustTerminate(2) matches the loop-free straight-line real prologue (no divergence). Independent exhaustive decision-table comparison of the abstracted spec vs the real prologue over the full (coord,dim) ∈ {None,present}² enumeration plus fuzz found 0 divergences, corroborated by G-AX (20036 cases) and G-CONF (100324 checked, 0 disagreements). The Optional[int] abstraction (None ↔ not-supplied, distinct ints ↔ distinct selectors) is injective on the only observation the real callee makes on these arguments (`is None`), so it introduces no drift. The spec is neither too strong (no postcondition excludes a real behavior) nor drifting from repo behavior. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures). Rigorous semantic review confirms no leak beyond the public problem_statement.

Public problem_statement already discloses: the two competing arg names `coord` and `dim`, that DataArray.integrate uses `dim` vs Dataset.integrate `coord`, that `coord` is intended, literal calls `ds.integrate(coord='x')`/`da.integrate(dim='x')`, and explicitly asks 'whether it requires a deprecation cycle?'.

Spec view uses ONLY identifiers `coord`/`dim` (public vocabulary) and states desired routing behavior (refuse both, legacy-only proceeds+deprecation signal, primary-only silent) — the deprecation is the very open question the public task poses, so it is within public scope. A spec necessarily states desired behavior; this is not edit-localization.

Verified ABSENT from spec view: patched method `integrate`, classes `DataArray`/`Dataset`, file paths xarray/core/dataarray.py & dataset.py, `warnings.warn`, `FutureWarning`, `ValueError`, version `0.19.0`, `trapez`, `_to_temp_dataset`, `differentiate`. Only 'xarray' occurrence is the public instance-id string in the module docstring header ('pydata__xarray-3993'). Comments are abstract (backward compatibility / legacy selector / deprecation signal) with no narration terms (bug/fix/etc.). Changed gold symbols {integrate, differentiate} appear nowhere as identifiers or comment text. model.py and model_prepatch.py share the same spec signature (same_spec=True), confirming the frozen spec is consumer-facing.

No spec-view line pinpoints the gold edit beyond what problem_statement already makes public.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
