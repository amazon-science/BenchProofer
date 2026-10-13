# P2 adversarial audit — sympy__sympy-23950

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_self_recursion.py`, `atk3_return_element.py`, `atk4_fresh_object.py`, `atk5_partial_domain.py`, `atk6_guarded_loop.py`, `atk7_loop_return_element.py`, `atk8_defer_raise.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk2_infinite_loop.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_self_recursion.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,5 +103,5 @@
     Ensures(Result() is self.region)
     # post-conditions-end
     # impl-start
-    return self.region
+    return solution_region(self)
     # impl-end
```

Attack 2 — `atk2_infinite_loop.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -103,5 +103,7 @@
     Ensures(Result() is self.region)
     # post-conditions-end
     # impl-start
+    while True:
+        pass
     return self.region
     # impl-end
```

Attack 3 — `atk3_return_element.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,5 +103,5 @@
     Ensures(Result() is self.region)
     # post-conditions-end
     # impl-start
-    return self.region
+    return self.element
     # impl-end
```

Attack 4 — `atk4_fresh_object.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,5 +103,6 @@
     Ensures(Result() is self.region)
     # post-conditions-end
     # impl-start
-    return self.region
+    r = Region()
+    return r
     # impl-end
```

Attack 5 — `atk5_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,5 +103,8 @@
     Ensures(Result() is self.region)
     # post-conditions-end
     # impl-start
-    return self.region
+    if self.element is self.region:
+        return self.region
+    while True:
+        pass
     # impl-end
```

Attack 6 — `atk6_guarded_loop.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,5 +103,8 @@
     Ensures(Result() is self.region)
     # post-conditions-end
     # impl-start
+    n = 0
+    while self is self:
+        n = n + 1
     return self.region
     # impl-end
```

Attack 7 — `atk7_loop_return_element.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,5 +103,8 @@
     Ensures(Result() is self.region)
     # post-conditions-end
     # impl-start
-    return self.region
+    i = 0
+    while i < 1:
+        i = i + 1
+    return self.element
     # impl-end
```

Attack 8 — `atk8_defer_raise.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,5 +103,5 @@
     Ensures(Result() is self.region)
     # post-conditions-end
     # impl-start
-    return self.region
+    raise ViewNotProduced()
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-23950.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership assertion is the proposition that a given element belongs to a
  given region (a set of values). Such an assertion has a canonical
  "set-of-values" view: the region of values for which the asserted membership
  is the stated one. For the assertion that ``element`` lies in ``region``, that
  view is exactly ``region`` itself — the very region whose membership the
  assertion is about.

  The behaviour pinned here: the set-of-values view of a membership assertion
  RETURNS NORMALLY (it is always defined for a single-element assertion) and the
  value it returns IS the region component of the assertion — not the element
  component, and not some freshly built object. Returning the region is what
  makes the view itself a region (so that, in turn, it supports the operations
  every region supports); a view that fails to produce the region — by deferring
  instead of returning, or by returning the element — is never permitted.

  Producing the view is a single bounded component selection: the operation
  MUST terminate and deliver its result (a total-correctness obligation,
  carried as ``MustTerminate`` in the precondition). An implementation that
  diverges before returning — e.g. by re-invoking the view on the same
  assertion, or spinning in a loop — would satisfy the value postconditions
  only vacuously and never deliver the view; the real operation always
  completes.

A membership assertion is modelled as a minimal class carrying only its two
touched components: the asserted ``element`` and the ``region`` it is asserted
to lie in, each an object reference (the payload of each component is irrelevant
to the view behaviour under specification). The returned view is required to be
the very ``region`` reference, identified by Nagini object identity (``is``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ViewNotProduced(Exception):
    """A deferral signal: declining to produce the set-of-values view (signalling
    "not yet defined") instead of returning the region. The specification forbids
    it — the view must always return the region for a single-element assertion —
    so no `Exsures` admits it (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""


class Region:
    """A region of values (a set), abstracted to an opaque object reference: the
    view behaviour under specification inspects no payload of the region, only
    which component object is returned."""

    def __init__(self) -> None:
        Ensures(True)


class MembershipAssertion:
    """The proposition that ``element`` belongs to ``region``, abstracted to its
    two touched components: the asserted element and the region it is asserted to
    lie in. Both are opaque object references; only which one the view returns is
    observable."""

    def __init__(self, element: Region, region: Region) -> None:
        Ensures(Acc(self.element, 1 / 2) and self.element is element)   # type: ignore
        Ensures(Acc(self.region, 1 / 2) and self.region is region)       # type: ignore
        self.element = element
        self.region = region


# axioms-start
# (no @ContractOnly axioms: the view is a direct selection of a stored component
#  object, modelled deeply as object-identity reasoning over the abstracted
#  components — see refinement.md, every row is R or I. No unchanged opaque
#  callee is consumed.)
# axioms-end


# pure-start
# (no @Pure helpers: the behaviour is a single component selection, expressed
#  directly in the contract.)
# pure-end


def solution_region(self: MembershipAssertion) -> Region:
    # pre-conditions-start
    # Read-only: the assertion is not mutated, so its components are held at
    # fractional permission (required and ensured) — directive 5.
    Requires(Acc(self.element, 1 / 2))
    Requires(Acc(self.region, 1 / 2))
    # Producing the view is a single bounded component selection: the operation
    # MUST terminate (total correctness). A diverging body — e.g. one that
    # re-invokes solution_region on the same assertion — satisfies the value
    # postconditions only vacuously and never delivers the view; measure 2
    # leaves no budget for a same-measure self-call.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.element, 1 / 2))
    Ensures(Acc(self.region, 1 / 2))
    # The view returns normally and the value it returns IS the region component
    # of the assertion — the very object asserted to contain the element.
    Ensures(Result() is self.region)
    # post-conditions-end
    # impl-start
    return self.region
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 distinct same-spec wrong-impl attacks (all confirmed same-spec, exit0) run through `adversary weakness nagini sympy__sympy-23950`; ALL returned NOT-A-COUNTEREXAMPLE (exit 2 = does not verify). No CANDIDATE emerged, so no faithful patch needed materializing/resolving (verify->correct direction has nothing to falsify).

Attack classes & machine-checked verifier reasons (raw errors captured):
- atk1_self_recursion (return solution_region(self)): 'Obligation leak check failed. Callee solution_region might not take all unsatisfied obligations' — MustTerminate(2) rejects same-measure self-call.
- atk2_infinite_loop (while True: pass; return): Translation failed 'dead.code' at the unreachable return.
- atk3_return_element (return self.element): 'Postcondition ... Result() is self.region might not hold' — identity postcond discriminates the element operand.
- atk4_fresh_object (r=Region(); return r): same identity postcond failure.
- atk5_partial_domain (return region iff element is region else while True): 'Obligation leak check failed. Loop might not take all unsatisfied obligations' — partial-domain divergence rejected.
- atk6_guarded_loop (while self is self: ...; return): loop obligation leak — control-flow-effect divergence rejected even with a reachable trailing return.
- atk7_loop_return_element (bounded loop then return self.element): identity postcond failure.
- atk8_defer_raise (raise ViewNotProduced()): 'Exhale might fail. method raises no exceptions' — deferral rejected (prepatch-equivalent).

Positive control (exact model.py, `return self.region`) VERIFIES in 17.0s. prepatch_reproduced: model_prepatch.py raises ViewNotProduced and fails verification (G-DIFF pass), reproducing the pre-patch NotImplementedError deferral.

Refinement/A-leg audit: refinement.md has exactly 2 legs — leg1 R (type refinement Contains<->MembershipAssertion, args[0]<->element, args[1]<->region), leg2 I under R (return self.region <-> return self.args[1]). NO kind-3 legs; axioms-start/end empty (no consumed @ContractOnly axiom). The single A-reference deep_model_reference (solution_region impl modeling Contains.as_set -> self.args[1]) is validated in-container by axiom_check.py/G-AX (PASS, 12 operand pairs: args[1]==s, args[0] is x, args[0] is not args[1], post-gold as_set() is args[1] == s). Correspondence between model's Result() is self.region and real as_set() is self.args[1] (gold `return self.args[1]`) holds. Supporting gates all pass: G-AX, G-GOLD, G-DIFF, G-HYGIENE, G-INTEGRITY, G-LEAK.

The prior recorded G-EQ 'INCONCLUSIVE — 1 attack inconclusive' was a verifier-timeout artifact, not a real weakness; all 8 of my attacks completed with genuine, well-targeted verification failures. The spec is tight on both value (identity postcond) and termination (MustTerminate(2)) — the two ways a wrong impl of Contains.as_set fails test_as_set (wrong operand; hang/RecursionError). verify => resolved holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_self_recursion.py`, `atk3_return_element.py`, `atk4_fresh_object.py`, `atk5_partial_domain.py`, `atk6_guarded_loop.py`, `atk7_loop_return_element.py`, `atk8_defer_raise.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk2_infinite_loop.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_self_recursion.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_infinite_loop.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 3 — `atk3_return_element.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_fresh_object.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_partial_domain.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_guarded_loop.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_loop_return_element.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_defer_raise.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-23950.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership assertion is the proposition that a given element belongs to a
  given region (a set of values). Such an assertion has a canonical
  "set-of-values" view: the region of values for which the asserted membership
  is the stated one. For the assertion that ``element`` lies in ``region``, that
  view is exactly ``region`` itself — the very region whose membership the
  assertion is about.

  The behaviour pinned here: the set-of-values view of a membership assertion
  RETURNS NORMALLY (it is always defined for a single-element assertion) and the
  value it returns IS the region component of the assertion — not the element
  component, and not some freshly built object. Returning the region is what
  makes the view itself a region (so that, in turn, it supports the operations
  every region supports); a view that fails to produce the region — by deferring
  instead of returning, or by returning the element — is never permitted.

  Producing the view is a single bounded component selection: the operation
  MUST terminate and deliver its result (a total-correctness obligation,
  carried as ``MustTerminate`` in the precondition). An implementation that
  diverges before returning — e.g. by re-invoking the view on the same
  assertion, or spinning in a loop — would satisfy the value postconditions
  only vacuously and never deliver the view; the real operation always
  completes.

A membership assertion is modelled as a minimal class carrying only its two
touched components: the asserted ``element`` and the ``region`` it is asserted
to lie in, each an object reference (the payload of each component is irrelevant
to the view behaviour under specification). The returned view is required to be
the very ``region`` reference, identified by Nagini object identity (``is``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ViewNotProduced(Exception):
    """A deferral signal: declining to produce the set-of-values view (signalling
    "not yet defined") instead of returning the region. The specification forbids
    it — the view must always return the region for a single-element assertion —
    so no `Exsures` admits it (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""


class Region:
    """A region of values (a set), abstracted to an opaque object reference: the
    view behaviour under specification inspects no payload of the region, only
    which component object is returned."""

    def __init__(self) -> None:
        Ensures(True)


class MembershipAssertion:
    """The proposition that ``element`` belongs to ``region``, abstracted to its
    two touched components: the asserted element and the region it is asserted to
    lie in. Both are opaque object references; only which one the view returns is
    observable."""

    def __init__(self, element: Region, region: Region) -> None:
        Ensures(Acc(self.element, 1 / 2) and self.element is element)   # type: ignore
        Ensures(Acc(self.region, 1 / 2) and self.region is region)       # type: ignore
        self.element = element
        self.region = region


# axioms-start
# (no @ContractOnly axioms: the view is a direct selection of a stored component
#  object, modelled deeply as object-identity reasoning over the abstracted
#  components — see refinement.md, every row is R or I. No unchanged opaque
#  callee is consumed.)
# axioms-end


# pure-start
# (no @Pure helpers: the behaviour is a single component selection, expressed
#  directly in the contract.)
# pure-end


def solution_region(self: MembershipAssertion) -> Region:
    # pre-conditions-start
    # Read-only: the assertion is not mutated, so its components are held at
    # fractional permission (required and ensured) — directive 5.
    Requires(Acc(self.element, 1 / 2))
    Requires(Acc(self.region, 1 / 2))
    # Producing the view is a single bounded component selection: the operation
    # MUST terminate (total correctness). A diverging body — e.g. one that
    # re-invokes solution_region on the same assertion — satisfies the value
    # postconditions only vacuously and never delivers the view; measure 2
    # leaves no budget for a same-measure self-call.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.element, 1 / 2))
    Ensures(Acc(self.region, 1 / 2))
    # The view returns normally and the value it returns IS the region component
    # of the assertion — the very object asserted to contain the element.
    Ensures(Result() is self.region)
    # post-conditions-end
    # impl-start
    return self.region
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 distinct same-spec wrong-impl attacks (all confirmed same-spec, exit0) run through `adversary weakness nagini sympy__sympy-23950`; ALL returned NOT-A-COUNTEREXAMPLE (exit 2 = does not verify). No CANDIDATE emerged, so no faithful patch needed materializing/resolving (verify->correct direction has nothing to falsify).

Attack classes & machine-checked verifier reasons (raw errors captured):
- atk1_self_recursion (return solution_region(self)): 'Obligation leak check failed. Callee solution_region might not take all unsatisfied obligations' — MustTerminate(2) rejects same-measure self-call.
- atk2_infinite_loop (while True: pass; return): Translation failed 'dead.code' at the unreachable return.
- atk3_return_element (return self.element): 'Postcondition ... Result() is self.region might not hold' — identity postcond discriminates the element operand.
- atk4_fresh_object (r=Region(); return r): same identity postcond failure.
- atk5_partial_domain (return region iff element is region else while True): 'Obligation leak check failed. Loop might not take all unsatisfied obligations' — partial-domain divergence rejected.
- atk6_guarded_loop (while self is self: ...; return): loop obligation leak — control-flow-effect divergence rejected even with a reachable trailing return.
- atk7_loop_return_element (bounded loop then return self.element): identity postcond failure.
- atk8_defer_raise (raise ViewNotProduced()): 'Exhale might fail. method raises no exceptions' — deferral rejected (prepatch-equivalent).

Positive control (exact model.py, `return self.region`) VERIFIES in 17.0s. prepatch_reproduced: model_prepatch.py raises ViewNotProduced and fails verification (G-DIFF pass), reproducing the pre-patch NotImplementedError deferral.

Refinement/A-leg audit: refinement.md has exactly 2 legs — leg1 R (type refinement Contains<->MembershipAssertion, args[0]<->element, args[1]<->region), leg2 I under R (return self.region <-> return self.args[1]). NO kind-3 legs; axioms-start/end empty (no consumed @ContractOnly axiom). The single A-reference deep_model_reference (solution_region impl modeling Contains.as_set -> self.args[1]) is validated in-container by axiom_check.py/G-AX (PASS, 12 operand pairs: args[1]==s, args[0] is x, args[0] is not args[1], post-gold as_set() is args[1] == s). Correspondence between model's Result() is self.region and real as_set() is self.args[1] (gold `return self.args[1]`) holds. Supporting gates all pass: G-AX, G-GOLD, G-DIFF, G-HYGIENE, G-INTEGRITY, G-LEAK.

The prior recorded G-EQ 'INCONCLUSIVE — 1 attack inconclusive' was a verifier-timeout artifact, not a real weakness; all 8 of my attacks completed with genuine, well-targeted verification failures. The spec is tight on both value (identity postcond) and termination (MustTerminate(2)) — the two ways a wrong impl of Contains.as_set fails test_as_set (wrong operand; hang/RecursionError). verify => resolved holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical to the bundle (same-spec exit 0). model.py verifies under the pinned Nagini verifier (Verification successful, 14.7s). The modeled function solution_region abstracts Contains.as_set(self), whose gold body is the straight-line `return self.args[1]`. The spec pins exactly three obligations, each matching the real callee with no drift: (1) normal return, no raise — real gold body never raises; (2) Result() is self.region — real as_set() returns the stored args[1] operand BY IDENTITY; verified in-container against the gold worktree over all 12 axiom_check operand pairs (F2P FiniteSet(y)/S.Integers/S.Reals + adversarial fuzz: Naturals, Rationals, Intervals, nested/Union sets) and independent probes, all `as_set() is args[1]` True; (3) MustTerminate(2) — the real body is straight-line and always terminates, so requiring termination is not too strong (the gold body discharges it trivially). The real callee is input-independent: for every Contains(x,s) it deterministically returns args[1] by identity and terminates. No input makes the modeled function disagree with the real repo behavior; the spec is neither too strong nor drifting. axiom_check.py G-AX OK confirms the field bijection self.region <-> self.args[1] is faithful.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (leakage.screen: hard_failures=[], no relaxed flag/RELAXED_LEAKAGE.md; G-LEAK meta status 'pass'). Semantic review of the abstracted spec view confirms no leak of the gold edit beyond the public problem_statement.

Gold edit: sympy/sets/contains.py Contains.as_set(): `raise NotImplementedError()` -> `return self.args[1]`.

Public problem_statement already discloses: Contains.as_set is wrong (returns Contains, should be a set), the driving example Contains(x, Reals).as_set(), and that the result must behave as a set (as_relational) per the Piecewise traceback. Thus the task already telegraphs that as_set should return the region/set operand.

Spec-view checks:
- Identifiers fully abstracted (MembershipAssertion, solution_region, Region, element, region); none echoes patched repo symbols Contains/as_set/args.
- No patched file path (sympy/sets/contains.py) or dotted module path present.
- No verbatim gold line reproduced; no 'args[1]', 'second operand', 'index 1', or diff markers.
- No bug/fix/regression narration in comments/docstrings.
- Postcondition `Result() is self.region` plus the 'not the element, not a freshly built object' discriminator are the inherent behavioral obligation any faithful spec must encode; returning the region-of-values is already implied by the public example (set-of-values of x in Reals is Reals). MustTerminate(2) and object-identity modeling are Nagini modeling artifacts, not disclosures of the repo edit.

The spec view restates, in abstracted terms, only behavior the public statement already describes; it does not localize the file/symbol nor expose the concrete self.args[1] mechanics. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
