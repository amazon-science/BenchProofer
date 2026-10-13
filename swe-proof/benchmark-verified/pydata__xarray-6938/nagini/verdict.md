# P2 adversarial audit — pydata__xarray-6938

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_8.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.py`, `atk_6.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,7 +156,7 @@
     Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
     # post-conditions-end
     # impl-start
-    return independent_clone(self)
+    return self
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,7 +156,7 @@
     Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
     # post-conditions-end
     # impl-start
-    return independent_clone(self)
+    return CoordVar(self.dims)
     # impl-end
 
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,7 +156,20 @@
     Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
     # post-conditions-end
     # impl-start
-    return independent_clone(self)
+    s_old = ToSeq(self.dims)  # type: PSeq[int]
+    new_dims = []  # type: List[int]
+    i = 0
+    while i < len(self.dims) - 1:
+        Invariant(Acc(self.dims, 1 / 4))
+        Invariant(Acc(list_pred(self.dims), 1 / 4))
+        Invariant(Acc(list_pred(new_dims)))
+        Invariant(ToSeq(self.dims) == s_old)
+        Invariant(0 <= i and i <= len(s_old))
+        Invariant(ToSeq(new_dims) == s_old.take(i))
+        Invariant(MustTerminate(len(self.dims) - i + 1))
+        new_dims.append(self.dims[i])
+        i = i + 1
+    return CoordVar(new_dims)
     # impl-end
 
 
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -156,7 +156,21 @@
     Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
     # post-conditions-end
     # impl-start
-    return independent_clone(self)
+    s_old = ToSeq(self.dims)  # type: PSeq[int]
+    new_dims = []  # type: List[int]
+    i = 0
+    while i < len(self.dims):
+        Invariant(Acc(self.dims, 1 / 4))
+        Invariant(Acc(list_pred(self.dims), 1 / 4))
+        Invariant(Acc(list_pred(new_dims)))
+        Invariant(ToSeq(self.dims) == s_old)
+        Invariant(0 <= i and i <= len(s_old))
+        Invariant(ToSeq(new_dims) == s_old.take(i))
+        Invariant(MustTerminate(len(self.dims) - i + 1))
+        new_dims.append(self.dims[i])
+        i = i + 1
+    Assert(s_old.take(len(s_old)) == s_old)
+    return CoordVar(new_dims)
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,6 +156,7 @@
     Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
     # post-conditions-end
     # impl-start
+    self.dims.append(self.dims[0])
     return independent_clone(self)
     # impl-end
 
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -156,7 +156,8 @@
     Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
     # post-conditions-end
     # impl-start
-    return independent_clone(self)
+    tmp = independent_clone(self)  # type: CoordVar
+    return independent_clone(tmp)
     # impl-end
 
 
```

Attack 7 — `atk_7.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -156,6 +156,9 @@
     Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
     # post-conditions-end
     # impl-start
+    while True:
+        Invariant(Acc(self.dims, 1 / 2))
+        Invariant(Acc(list_pred(self.dims), 1 / 2))
     return independent_clone(self)
     # impl-end
 
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,7 +156,7 @@
     Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
     # post-conditions-end
     # impl-start
-    return independent_clone(self)
+    return as_coordinate(self)
     # impl-end
 
 
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,7 +156,8 @@
     Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
     # post-conditions-end
     # impl-start
-    return independent_clone(self)
+    empty = []  # type: List[int]
+    return CoordVar(empty)
     # impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6938.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Re-presenting a one-dimensional coordinate variable as a coordinate variable
  must yield an INDEPENDENT object, never an alias of the receiver. Concretely:

    (1) the returned object is a distinct object from the receiver (a fresh
        allocation, not the receiver itself);
    (2) the returned object initially carries the same dimension-name tuple as
        the receiver;
    (3) the returned object owns its own dimension-name storage, so that later
        reassigning the result's dimension names leaves the receiver's
        dimension names unchanged.

The coordinate variable is modelled as a small object whose only touched field
is its dimension-name tuple `dims`, carried as a `List[int]` of name codes
(Nagini bans `str` indexing, and the tested observation is purely the tuple of
dimension names). Object independence is captured by Nagini's permission
discipline: the receiver is read-only (fractional permission, required AND
ensured), while the result is handed FULL write permission to its own `dims`
field -- a guarantee an aliasing result (one that returns the receiver itself)
cannot satisfy, since the receiver's retained read permission plus the result's
full write permission would exceed the total available permission.

A second exercised behaviour: re-presenting the variable in its plain
(non-coordinate) form likewise yields a distinct object that observes exactly
the receiver's stored dimension names.

All re-presentation operations are TOTAL: each carries a MustTerminate
obligation in its precondition. The real callees are bounded, straight-line
copies (tuple copy + fresh allocation) that always return; an implementation
that diverges would satisfy the value/identity postconditions only vacuously
and would never deliver the re-presented variable to the caller (swap_dims
would hang instead of returning the swapped dataset).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no axiomatized callees: the changed behaviour -- independent allocation vs.
# aliasing -- is modelled deeply via the permission discipline, not behind an
# axiom.)
# axioms-end

# pure-start
# (no pure helpers needed.)
# pure-end

class CoordVar:
    """A one-dimensional coordinate variable. The only field the studied
    behaviour touches is `dims`, the tuple of dimension names (modelled as a
    `List[int]` of name codes)."""

    def __init__(self, dims: List[int]) -> None:
        # pre-conditions-start
        Requires(Acc(list_pred(dims)))
        # Construction is a single field write: it MUST terminate. The strictly
        # smallest measure (1) lets every re-presentation holding a larger
        # obligation invoke the constructor without leaking its own obligation.
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.dims))
        Ensures(Acc(list_pred(self.dims)))
        Ensures(self.dims is dims)
        Ensures(ToSeq(self.dims) == Old(ToSeq(dims)))
        # post-conditions-end
        # impl-start
        self.dims = dims  # type: List[int]
        # impl-end

def independent_clone(self: CoordVar) -> CoordVar:
    # pre-conditions-start
    Requires(Acc(self.dims, 1 / 2))
    Requires(Acc(list_pred(self.dims), 1 / 2))
    # The copy is a bounded element-wise walk over the receiver's dims: it
    # MUST terminate. Measure 2 > the constructor's 1, so the fresh-allocation
    # call discharges without leaking the obligation. A diverging clone would
    # never hand the caller the promised independent object.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.dims, 1 / 2))
    Ensures(Acc(list_pred(self.dims), 1 / 2))
    Ensures(Acc(Result().dims))
    Ensures(Acc(list_pred(Result().dims)))
    # The receiver's dimension names are unchanged.
    Ensures(ToSeq(self.dims) == Old(ToSeq(self.dims)))
    # The copy is a distinct object owning its own dimension-name storage.
    Ensures(Result() is not self)
    Ensures(Result().dims is not self.dims)
    # ... carrying the same dimension names as the receiver.
    Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
    # post-conditions-end
    # impl-start
    s_old = ToSeq(self.dims)  # type: PSeq[int]
    new_dims = []  # type: List[int]
    i = 0
    while i < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(new_dims)))
        Invariant(ToSeq(self.dims) == s_old)
        Invariant(0 <= i and i <= len(s_old))
        Invariant(ToSeq(new_dims) == s_old.take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure, discharging MustTerminate(2).
        Invariant(MustTerminate(len(self.dims) - i + 1))
        # invariants-end
        new_dims.append(self.dims[i])
        i = i + 1
    Assert(i == len(s_old))
    Assert(s_old.take(len(s_old)) == s_old)
    Assert(ToSeq(new_dims) == s_old)
    res = CoordVar(new_dims)
    Assert(ToSeq(res.dims) == s_old)
    Assert(ToSeq(self.dims) == s_old)
    Assert(ToSeq(res.dims) == ToSeq(self.dims))
    return res
    # impl-end

def as_coordinate(self: CoordVar) -> CoordVar:
    # pre-conditions-start
    Requires(Acc(self.dims, 1 / 2))
    Requires(Acc(list_pred(self.dims), 1 / 2))
    # The re-presentation is a bounded operation that always returns; callers
    # depend on it RETURNING the independent object before reassigning that
    # object's dims. It MUST terminate: an implementation that loops forever
    # would satisfy the value clauses only vacuously and is rejected here.
    # Measure 3 > independent_clone's 2.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The receiver is read-only and survives unchanged.
    Ensures(Acc(self.dims, 1 / 2))
    Ensures(Acc(list_pred(self.dims), 1 / 2))
    Ensures(ToSeq(self.dims) == Old(ToSeq(self.dims)))
    # The result is an INDEPENDENT object: a distinct allocation owning its own
    # dimension-name storage with FULL write permission, so a caller may
    # reassign the result's dims without touching the receiver's dims.
    Ensures(Acc(Result().dims))
    Ensures(Acc(list_pred(Result().dims)))
    Ensures(Result() is not self)
    Ensures(Result().dims is not self.dims)
    # ... and it initially carries the receiver's dimension names.
    Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
    # post-conditions-end
    # impl-start
    return independent_clone(self)
    # impl-end

def as_plain(self: CoordVar) -> CoordVar:
    # pre-conditions-start
    Requires(Acc(self.dims, 1 / 2))
    Requires(Acc(list_pred(self.dims), 1 / 2))
    # The plain re-presentation is likewise a bounded copy that always
    # returns: it MUST terminate. Measure 4 strictly dominates the sibling
    # re-presentations (constructor 1, clone 2, coordinate 3), so a caller
    # holding this obligation can still invoke any of them.
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.dims, 1 / 2))
    Ensures(Acc(list_pred(self.dims), 1 / 2))
    Ensures(Acc(Result().dims))
    Ensures(Acc(list_pred(Result().dims)))
    Ensures(Result() is not self)
    Ensures(Result().dims is not self.dims)
    # The plain re-presentation carries exactly the receiver's dimension names.
    Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
    # post-conditions-end
    # impl-start
    base_dims = []  # type: List[int]
    j = 0
    while j < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(base_dims)))
        Invariant(0 <= j and j <= len(self.dims))
        Invariant(ToSeq(base_dims) == ToSeq(self.dims).take(j))
        # strictly decreasing measure discharges MustTerminate(4).
        Invariant(MustTerminate(len(self.dims) - j + 1))
        # invariants-end
        base_dims.append(self.dims[j])
        j = j + 1
    Assert(ToSeq(self.dims).take(len(self.dims)) == ToSeq(self.dims))
    return CoordVar(base_dims)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Re-audit of pydata__xarray-6938 nagini bundle under the fixed derivation (post-2026-08-06 candidate->resolve for panel_1). NOTE ON PRIOR VERDICT: meta.json/verdict.md recorded G-EQ=fail / G-PANEL-1=fail citing 'atk_2.py verifies but its patch does not resolve', but the attack source was NOT retained, and (b) it predates the 2026-08-06 fix where 'the unified mechanization had DROPPED the resolve step for panel_1 only' (the audit protocol). Per the audit protocol this is an echo-attack false positive class -> 'Do NOT escalate; re-run the audit.' I re-audited from scratch and cannot reproduce any real weakness.

ENV: SBU_BENCHMARK_DIR=benchmark-verified; python=python;

POSITIVE CONTROL: bash scripts/nagini_verify.sh positive_control.py -> 'Verification successful' (18.88s). PREPATCH REPRODUCED: model_prepatch.py (as_coordinate `return self`) -> 'Postcondition of as_coordinate might not hold. There might be insufficient permission to access Result().dims.' (exit 1) — the alias->copy change is sensed (G-DIFF).

### ATTACKS (all confirmed same-spec via `adversary same-spec`, exit 0; only the as_coordinate impl region edited):
- atk_1 (prepatch-echo `return self`): weakness NOT-A-COUNTEREXAMPLE; verify FAIL: 'insufficient permission to access Result().dims'.
- atk_2 (distinct object, SHARED dims storage `return CoordVar(self.dims)`): NOT-A-CE; verify FAIL: 'precondition of method CoordVar ... insufficient permission to access list_pred(dims)' (3/2>1 caught).
- atk_3 (partial-domain, off-by-one copy dropping last elem): NOT-A-CE; verify FAIL: 'Assertion (ToSeq(Result().dims) == ToSeq(self.dims)) might not hold'.
- atk_4 (ungrounded-oracle echo #1, inline element-wise copy): CANDIDATE (same-spec + verifies). Faithful refined patch = gold `return self.copy()` (+annotation/sibling ._dims hunks). RESOLVE EXECUTED: {completed:true, resolved:TRUE, attempts:1, flaky:false}.
- atk_5 (control-flow-effect: `self.dims.append(...)` before copy): NOT-A-CE; verify FAIL: 'precondition of self.dims[0] might not hold' (only 1/2 read perm — cannot mutate receiver).
- atk_6 (ungrounded-oracle echo #2, double-clone): CANDIDATE (same-spec + verifies). Faithful refined patch byte-identical to atk_4/gold. RESOLVE EXECUTED: {completed:true, resolved:TRUE, attempts:1, flaky:false}.
- atk_7 (`while True` non-termination): NOT JUDGED — the front end refused to translate the program ('dead.code'), so it never reached the verifier, the spec never ruled on it, and it counts in neither tally; the shape is unexpressible in Nagini's fragment, so this file did not exercise the spec's method-level MustTerminate, and whether that clause would reject a TRANSLATABLE diverging rival is a separate question this attack does not settle.
- atk_8 (recursive non-termination `return as_coordinate(self)`): NOT-A-CE; verify FAIL: 'Obligation leak check failed. Callee as_coordinate might not take all unsatisfied obligations from the caller' — confirms the MustTerminate/totality leg A5 is load-bearing.
- atk_9 (ungrounded-oracle: constant empty dims): NOT-A-CE; verify FAIL: 'Assertion (ToSeq(Result().dims) == ToSeq(self.dims)) might not hold'.

EVERY VERIFYING CANDIDATE'S FAITHFUL PATCH RESOLVED (executed, not speculated). No verifying wrong impl exists whose faithful patch fails to resolve.

REFINEMENT.MD LEG AUDIT (all R/A-reference/I; NO consumed axioms, NO kind-3): A1=R (object<->CoordVar; dims tuple<->List[int]; tuple-eq<->ToSeq-eq). A2=A-reference (independent_clone deep-models self.copy()->_replace->type(self)(copy.copy(self._dims),...)); validated by G-AX (meta status=pass). A3=R+I (element-copy loop <-> copy.copy(self._dims)). A4=A-reference (distinct allocation <-> disjoint full write perm on Result().dims). A5=R (MustTerminate totality; real callee straight-line). B1=I/obligation (swap_dims var.dims=dims write is safe by Result().dims is not self.dims). C1=R+I (to_base_variable sibling, already fresh). D=annotation-only (no model node). E=explicitly no kind-3.

A-REFERENCE FIDELITY: the one apparent over-strength (`Result().dims is not self.dims` vs real `copy.copy(tuple)` returning the SAME tuple) is observationally identical because the model maps the dims-setter to FIELD REBINDING and real tuples are immutable — the F2P does `b.dims = ('y',)` (rebind), so shared tuple storage is safe; confirmed by G-PANEL-2 (pass) and G-AX (pass) over F2P #6931 + 5 boundary + 2000 fuzz. F2P `test_to_index_variable_copy` checks exactly `a is not b` and dims-mutation-independence, which the spec pins precisely.

CONCLUSION: The spec admits a verifying impl iff that impl returns a distinct object with independent dims-storage carrying the receiver's dim names (i.e. self.copy() semantics) — whose faithful refinement IS the resolving gold patch. verify=>correct holds on this bundle. SOUND (>=9 attacks run; 2 candidates both resolve; none breaks it).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_8.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.py`, `atk_6.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6938.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Re-presenting a one-dimensional coordinate variable as a coordinate variable
  must yield an INDEPENDENT object, never an alias of the receiver. Concretely:

    (1) the returned object is a distinct object from the receiver (a fresh
        allocation, not the receiver itself);
    (2) the returned object initially carries the same dimension-name tuple as
        the receiver;
    (3) the returned object owns its own dimension-name storage, so that later
        reassigning the result's dimension names leaves the receiver's
        dimension names unchanged.

The coordinate variable is modelled as a small object whose only touched field
is its dimension-name tuple `dims`, carried as a `List[int]` of name codes
(Nagini bans `str` indexing, and the tested observation is purely the tuple of
dimension names). Object independence is captured by Nagini's permission
discipline: the receiver is read-only (fractional permission, required AND
ensured), while the result is handed FULL write permission to its own `dims`
field -- a guarantee an aliasing result (one that returns the receiver itself)
cannot satisfy, since the receiver's retained read permission plus the result's
full write permission would exceed the total available permission.

A second exercised behaviour: re-presenting the variable in its plain
(non-coordinate) form likewise yields a distinct object that observes exactly
the receiver's stored dimension names.

All re-presentation operations are TOTAL: each carries a MustTerminate
obligation in its precondition. The real callees are bounded, straight-line
copies (tuple copy + fresh allocation) that always return; an implementation
that diverges would satisfy the value/identity postconditions only vacuously
and would never deliver the re-presented variable to the caller (swap_dims
would hang instead of returning the swapped dataset).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no axiomatized callees: the changed behaviour -- independent allocation vs.
# aliasing -- is modelled deeply via the permission discipline, not behind an
# axiom.)
# axioms-end

# pure-start
# (no pure helpers needed.)
# pure-end

class CoordVar:
    """A one-dimensional coordinate variable. The only field the studied
    behaviour touches is `dims`, the tuple of dimension names (modelled as a
    `List[int]` of name codes)."""

    def __init__(self, dims: List[int]) -> None:
        # pre-conditions-start
        Requires(Acc(list_pred(dims)))
        # Construction is a single field write: it MUST terminate. The strictly
        # smallest measure (1) lets every re-presentation holding a larger
        # obligation invoke the constructor without leaking its own obligation.
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.dims))
        Ensures(Acc(list_pred(self.dims)))
        Ensures(self.dims is dims)
        Ensures(ToSeq(self.dims) == Old(ToSeq(dims)))
        # post-conditions-end
        # impl-start
        self.dims = dims  # type: List[int]
        # impl-end

def independent_clone(self: CoordVar) -> CoordVar:
    # pre-conditions-start
    Requires(Acc(self.dims, 1 / 2))
    Requires(Acc(list_pred(self.dims), 1 / 2))
    # The copy is a bounded element-wise walk over the receiver's dims: it
    # MUST terminate. Measure 2 > the constructor's 1, so the fresh-allocation
    # call discharges without leaking the obligation. A diverging clone would
    # never hand the caller the promised independent object.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.dims, 1 / 2))
    Ensures(Acc(list_pred(self.dims), 1 / 2))
    Ensures(Acc(Result().dims))
    Ensures(Acc(list_pred(Result().dims)))
    # The receiver's dimension names are unchanged.
    Ensures(ToSeq(self.dims) == Old(ToSeq(self.dims)))
    # The copy is a distinct object owning its own dimension-name storage.
    Ensures(Result() is not self)
    Ensures(Result().dims is not self.dims)
    # ... carrying the same dimension names as the receiver.
    Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
    # post-conditions-end
    # impl-start
    s_old = ToSeq(self.dims)  # type: PSeq[int]
    new_dims = []  # type: List[int]
    i = 0
    while i < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(new_dims)))
        Invariant(ToSeq(self.dims) == s_old)
        Invariant(0 <= i and i <= len(s_old))
        Invariant(ToSeq(new_dims) == s_old.take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure, discharging MustTerminate(2).
        Invariant(MustTerminate(len(self.dims) - i + 1))
        # invariants-end
        new_dims.append(self.dims[i])
        i = i + 1
    Assert(i == len(s_old))
    Assert(s_old.take(len(s_old)) == s_old)
    Assert(ToSeq(new_dims) == s_old)
    res = CoordVar(new_dims)
    Assert(ToSeq(res.dims) == s_old)
    Assert(ToSeq(self.dims) == s_old)
    Assert(ToSeq(res.dims) == ToSeq(self.dims))
    return res
    # impl-end

def as_coordinate(self: CoordVar) -> CoordVar:
    # pre-conditions-start
    Requires(Acc(self.dims, 1 / 2))
    Requires(Acc(list_pred(self.dims), 1 / 2))
    # The re-presentation is a bounded operation that always returns; callers
    # depend on it RETURNING the independent object before reassigning that
    # object's dims. It MUST terminate: an implementation that loops forever
    # would satisfy the value clauses only vacuously and is rejected here.
    # Measure 3 > independent_clone's 2.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The receiver is read-only and survives unchanged.
    Ensures(Acc(self.dims, 1 / 2))
    Ensures(Acc(list_pred(self.dims), 1 / 2))
    Ensures(ToSeq(self.dims) == Old(ToSeq(self.dims)))
    # The result is an INDEPENDENT object: a distinct allocation owning its own
    # dimension-name storage with FULL write permission, so a caller may
    # reassign the result's dims without touching the receiver's dims.
    Ensures(Acc(Result().dims))
    Ensures(Acc(list_pred(Result().dims)))
    Ensures(Result() is not self)
    Ensures(Result().dims is not self.dims)
    # ... and it initially carries the receiver's dimension names.
    Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
    # post-conditions-end
    # impl-start
    return independent_clone(self)
    # impl-end

def as_plain(self: CoordVar) -> CoordVar:
    # pre-conditions-start
    Requires(Acc(self.dims, 1 / 2))
    Requires(Acc(list_pred(self.dims), 1 / 2))
    # The plain re-presentation is likewise a bounded copy that always
    # returns: it MUST terminate. Measure 4 strictly dominates the sibling
    # re-presentations (constructor 1, clone 2, coordinate 3), so a caller
    # holding this obligation can still invoke any of them.
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.dims, 1 / 2))
    Ensures(Acc(list_pred(self.dims), 1 / 2))
    Ensures(Acc(Result().dims))
    Ensures(Acc(list_pred(Result().dims)))
    Ensures(Result() is not self)
    Ensures(Result().dims is not self.dims)
    # The plain re-presentation carries exactly the receiver's dimension names.
    Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
    # post-conditions-end
    # impl-start
    base_dims = []  # type: List[int]
    j = 0
    while j < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(base_dims)))
        Invariant(0 <= j and j <= len(self.dims))
        Invariant(ToSeq(base_dims) == ToSeq(self.dims).take(j))
        # strictly decreasing measure discharges MustTerminate(4).
        Invariant(MustTerminate(len(self.dims) - j + 1))
        # invariants-end
        base_dims.append(self.dims[j])
        j = j + 1
    Assert(ToSeq(self.dims).take(len(self.dims)) == ToSeq(self.dims))
    return CoordVar(base_dims)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Re-audit of pydata__xarray-6938 nagini bundle under the fixed derivation (post-2026-08-06 candidate->resolve for panel_1). NOTE ON PRIOR VERDICT: meta.json/verdict.md recorded G-EQ=fail / G-PANEL-1=fail citing 'atk_2.py verifies but its patch does not resolve', but the attack source was NOT retained, and (b) it predates the 2026-08-06 fix where 'the unified mechanization had DROPPED the resolve step for panel_1 only' (the audit protocol). Per the audit protocol this is an echo-attack false positive class -> 'Do NOT escalate; re-run the audit.' I re-audited from scratch and cannot reproduce any real weakness.

ENV: SBU_BENCHMARK_DIR=benchmark-verified; python=python;

POSITIVE CONTROL: bash scripts/nagini_verify.sh positive_control.py -> 'Verification successful' (18.88s). PREPATCH REPRODUCED: model_prepatch.py (as_coordinate `return self`) -> 'Postcondition of as_coordinate might not hold. There might be insufficient permission to access Result().dims.' (exit 1) — the alias->copy change is sensed (G-DIFF).

### ATTACKS (all confirmed same-spec via `adversary same-spec`, exit 0; only the as_coordinate impl region edited):
- atk_1 (prepatch-echo `return self`): weakness NOT-A-COUNTEREXAMPLE; verify FAIL: 'insufficient permission to access Result().dims'.
- atk_2 (distinct object, SHARED dims storage `return CoordVar(self.dims)`): NOT-A-CE; verify FAIL: 'precondition of method CoordVar ... insufficient permission to access list_pred(dims)' (3/2>1 caught).
- atk_3 (partial-domain, off-by-one copy dropping last elem): NOT-A-CE; verify FAIL: 'Assertion (ToSeq(Result().dims) == ToSeq(self.dims)) might not hold'.
- atk_4 (ungrounded-oracle echo #1, inline element-wise copy): CANDIDATE (same-spec + verifies). Faithful refined patch = gold `return self.copy()` (+annotation/sibling ._dims hunks). RESOLVE EXECUTED: {completed:true, resolved:TRUE, attempts:1, flaky:false}.
- atk_5 (control-flow-effect: `self.dims.append(...)` before copy): NOT-A-CE; verify FAIL: 'precondition of self.dims[0] might not hold' (only 1/2 read perm — cannot mutate receiver).
- atk_6 (ungrounded-oracle echo #2, double-clone): CANDIDATE (same-spec + verifies). Faithful refined patch byte-identical to atk_4/gold. RESOLVE EXECUTED: {completed:true, resolved:TRUE, attempts:1, flaky:false}.
- atk_7 (`while True` non-termination): NOT JUDGED — the front end refused to translate the program ('dead.code'), so it never reached the verifier, the spec never ruled on it, and it counts in neither tally; the shape is unexpressible in Nagini's fragment, so this file did not exercise the spec's method-level MustTerminate, and whether that clause would reject a TRANSLATABLE diverging rival is a separate question this attack does not settle.
- atk_8 (recursive non-termination `return as_coordinate(self)`): NOT-A-CE; verify FAIL: 'Obligation leak check failed. Callee as_coordinate might not take all unsatisfied obligations from the caller' — confirms the MustTerminate/totality leg A5 is load-bearing.
- atk_9 (ungrounded-oracle: constant empty dims): NOT-A-CE; verify FAIL: 'Assertion (ToSeq(Result().dims) == ToSeq(self.dims)) might not hold'.

EVERY VERIFYING CANDIDATE'S FAITHFUL PATCH RESOLVED (executed, not speculated). No verifying wrong impl exists whose faithful patch fails to resolve.

REFINEMENT.MD LEG AUDIT (all R/A-reference/I; NO consumed axioms, NO kind-3): A1=R (object<->CoordVar; dims tuple<->List[int]; tuple-eq<->ToSeq-eq). A2=A-reference (independent_clone deep-models self.copy()->_replace->type(self)(copy.copy(self._dims),...)); validated by G-AX (meta status=pass). A3=R+I (element-copy loop <-> copy.copy(self._dims)). A4=A-reference (distinct allocation <-> disjoint full write perm on Result().dims). A5=R (MustTerminate totality; real callee straight-line). B1=I/obligation (swap_dims var.dims=dims write is safe by Result().dims is not self.dims). C1=R+I (to_base_variable sibling, already fresh). D=annotation-only (no model node). E=explicitly no kind-3.

A-REFERENCE FIDELITY: the one apparent over-strength (`Result().dims is not self.dims` vs real `copy.copy(tuple)` returning the SAME tuple) is observationally identical because the model maps the dims-setter to FIELD REBINDING and real tuples are immutable — the F2P does `b.dims = ('y',)` (rebind), so shared tuple storage is safe; confirmed by G-PANEL-2 (pass) and G-AX (pass) over F2P #6931 + 5 boundary + 2000 fuzz. F2P `test_to_index_variable_copy` checks exactly `a is not b` and dims-mutation-independence, which the spec pins precisely.

CONCLUSION: The spec admits a verifying impl iff that impl returns a distinct object with independent dims-storage carrying the receiver's dim names (i.e. self.copy() semantics) — whose faithful refinement IS the resolving gold patch. verify=>correct holds on this bundle. SOUND (>=9 attacks run; 2 candidates both resolve; none breaks it).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness confirmed against the REAL post-patch callee (gold patch applied cleanly at base_commit c4e40d99; repo built). Spec region byte-identical with the bundle (same-spec exit 0); bundle model verifies (14.8s). Ran IndexVariable.to_index_variable / Variable.to_base_variable / to_index_variable on the F2P scenario (issue #6931), 5 boundary 1-D index variables, ~3000 randomized fuzz cases, and extra edge cases: ZERO divergences on the four spec-pinned observables — (1) Result() is not self (distinct object), (2) Result().dims == self.dims initially (ToSeq equality), (3) reassigning Result().dims leaves self.dims unchanged (independence), (4) MustTerminate/total correctness (callees are straight-line bounded copies that always return). The only clause that superficially looks stronger than reality is Result().dims is not self.dims (distinct STORAGE): I empirically confirmed the real repo SHARES the tuple (b._dims IS a._dims == True, since copy.copy of a tuple returns the same object). This is NOT an observable disagreement: the model carries dims as a mutable List[int] with the setter mapped to field REBINDING (mapping.md §2), while the real repo achieves the identical mutation-independence via tuple immutability + setter rebinding. The tested observable (reassign result.dims -> receiver.dims unchanged) holds in BOTH on every input; .dims is an immutable tuple so only rebinding is possible, making the storage-identity difference invisible to any caller. No input was found on which the modeled function's observable behavior disagrees with the real callee. No spec drift or over-strength.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py docstring + spec regions (Requires/Ensures/Invariant/type decls) with impl bodies elided. Symbols are all generic model names (CoordVar, dims:List[int], independent_clone/as_coordinate/as_plain); none echo the gold-edit repo symbols. Verified against the patch's distinctive changed-symbol set {equals, get_level_variable, level_names, name, swap_dims, to_base_variable, to_index, to_index_variable, values}: only 'swap_dims' appears in the spec view (docstring line ~34), and swap_dims is the literal subject of the public problem_statement (title '.swap_dims() can modify original object'), so it leaks nothing beyond public text. The gold-edit-localizing symbols to_index_variable / to_base_variable / copy / IndexVariable / _replace / variable.py do NOT appear anywhere in the spec view. The encoded property (re-presenting a coordinate variable must yield an INDEPENDENT object, and reassigning the result's dims must not touch the receiver's dims) is directly derivable from the public problem_statement, which already states swap_dims mutates the original via the .dims of a data var swapped to a dimension coordinate, and that the reporter expected NO mutation. The verbatim gold edit (return self -> return self.copy()) and exact fix site live only in refinement.md / mapping.md / meta.json (auditor artifacts, not solver-visible). Mechanical G-LEAK screen re-run: passed=True, zero hard failures. Not a relaxed bundle (no relaxed_leakage flag / RELAXED_LEAKAGE.md), so no deferral applies. No spec-view line discloses the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
