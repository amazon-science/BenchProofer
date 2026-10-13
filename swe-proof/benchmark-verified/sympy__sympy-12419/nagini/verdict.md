# P2 adversarial audit — sympy__sympy-12419

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `model_base.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,10 +105,8 @@
     Ensures(Implies(eq_class(i, j) == EQ_UNKNOWN, Result() == DEFERRED))
     # post-conditions-end
     # impl-start
-    e = eq_class(i, j)
-    if e == EQ_TRUE:
+    if struct_eq(i, j):
         return ONE
-    elif e == EQ_FALSE:
+    else:
         return ZERO
-    return DEFERRED
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -107,8 +107,8 @@
     # impl-start
     e = eq_class(i, j)
     if e == EQ_TRUE:
+        return ZERO
+    elif e == EQ_FALSE:
         return ONE
-    elif e == EQ_FALSE:
-        return ZERO
     return DEFERRED
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -110,5 +110,5 @@
         return ONE
     elif e == EQ_FALSE:
         return ZERO
-    return DEFERRED
+    return ZERO
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -110,5 +110,5 @@
         return ONE
     elif e == EQ_FALSE:
         return ZERO
-    return DEFERRED
+    return ONE
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,10 +105,5 @@
     Ensures(Implies(eq_class(i, j) == EQ_UNKNOWN, Result() == DEFERRED))
     # post-conditions-end
     # impl-start
-    e = eq_class(i, j)
-    if e == EQ_TRUE:
-        return ONE
-    elif e == EQ_FALSE:
-        return ZERO
-    return DEFERRED
+    return eq_class(i, j)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,10 +105,10 @@
     Ensures(Implies(eq_class(i, j) == EQ_UNKNOWN, Result() == DEFERRED))
     # post-conditions-end
     # impl-start
+    if struct_eq(i, j):
+        return ONE
     e = eq_class(i, j)
-    if e == EQ_TRUE:
-        return ONE
-    elif e == EQ_FALSE:
+    if e == EQ_FALSE:
         return ZERO
     return DEFERRED
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,6 +106,8 @@
     # post-conditions-end
     # impl-start
     e = eq_class(i, j)
+    while e != EQ_TRUE and e != EQ_FALSE and e != EQ_UNKNOWN:
+        e = eq_class(i, j)
     if e == EQ_TRUE:
         return ONE
     elif e == EQ_FALSE:
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -106,9 +106,9 @@
     # post-conditions-end
     # impl-start
     e = eq_class(i, j)
-    if e == EQ_TRUE:
-        return ONE
-    elif e == EQ_FALSE:
+    if e == EQ_FALSE:
         return ZERO
-    return DEFERRED
+    if e == EQ_UNKNOWN:
+        return DEFERRED
+    return ONE
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_base.py`

```python
"""Twin-artifact model for sympy__sympy-12419.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The (i, j) entry of an identity matrix, where i and j are index expressions
  that may be symbolic. The entry depends on the *symbolic* equality of the two
  indices, classified three ways by the unchanged equality decision procedure:

    - if the two indices are decidably EQUAL, the entry is the unit value;
    - if they are decidably UNEQUAL, the entry is the zero value;
    - if equality cannot be decided (the indices are symbolic and neither
      provably equal nor provably unequal), the entry is the deferred symbolic
      value.

  Producing the entry is a single bounded decision: the operation MUST
  terminate and deliver its result (a total-correctness obligation, carried as
  ``MustTerminate`` in the precondition). An implementation that diverges
  before returning — e.g. by re-invoking the entry on the same indices, or
  spinning in a loop — would satisfy the value postconditions only vacuously
  and never deliver an entry; the real operation always returns.

Index expressions are modelled as opaque `int` identity tags; the model never
does arithmetic on them. The result is a 3-valued *tag* identifying which of
the three cell values the entry is (unit / zero / deferred symbolic), not a
number to be summed. Two unchanged equality callees are axiomatized: the 3-valued
equality decision `eq_class` (the equality of the two index expressions,
classified as provably-equal / provably-unequal / undecided) and the structural
identity `struct_eq` (tree-level sameness of the two expressions); their
soundness — including the structural-identity ⟹ provably-equal link — is checked
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# The three outcomes of the unchanged equality-decision callee.
EQ_FALSE = 0    # the two indices are provably unequal
EQ_TRUE = 1     # the two indices are provably equal
EQ_UNKNOWN = 2  # equality of the two indices is undecided

# The three possible cell values, as pairwise-distinct tags. Chosen disjoint
# from the EQ_* codes so the entry cannot be produced by echoing the classifier;
# it must be produced by genuinely branching on it.
ZERO = 10       # the zero cell value
ONE = 11        # the unit cell value
DEFERRED = 12   # the deferred symbolic cell value


# axioms-start
@Pure
@ContractOnly
def eq_class(i: int, j: int) -> int:
    """Unchanged callee: the equality-decision procedure for the two index
    expressions, read as a 3-valued outcome (provably-equal / provably-unequal /
    undecided). Returns one of EQ_TRUE, EQ_FALSE, EQ_UNKNOWN. Reflexive:
    identical indices are decidably equal. The weakest contract the proof needs
    — it does NOT claim any undecided pair is decided.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() == EQ_FALSE or Result() == EQ_TRUE
            or Result() == EQ_UNKNOWN)
    Ensures(Implies(i == j, Result() == EQ_TRUE))


@Pure
@ContractOnly
def struct_eq(i: int, j: int) -> bool:
    """Unchanged callee: structural (tree) identity of two index expressions
    (Python `==`). Reflexive. Structural identity is a SUFFICIENT condition for
    the equality decision: it implies the equality-decision callee classifies
    the pair as provably-equal (the converse does NOT hold — two structurally-
    distinct expressions may still be equal or undecided).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(i == j, Result()))
    Ensures(Implies(Result(), eq_class(i, j) == EQ_TRUE))
# axioms-end


# pure-start
# (no deep-model helpers: the changed operation is a 3-way branch on the
#  axiomatized equality callee, modelled directly in the impl.)
# pure-end


def diagonal_unit_entry(i: int, j: int) -> int:
    # pre-conditions-start
    # TERMINATION: producing the entry is a bounded, loop-free decision that
    # always returns a cell value. An implementation that diverges would meet
    # the value postconditions only vacuously and never deliver an entry;
    # this obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The entry is exactly one of the three cell tags.
    Ensures(Result() == ZERO or Result() == ONE or Result() == DEFERRED)
    # Decidably equal indices -> the unit cell.
    Ensures(Implies(eq_class(i, j) == EQ_TRUE, Result() == ONE))
    # Decidably unequal indices -> the zero cell.
    Ensures(Implies(eq_class(i, j) == EQ_FALSE, Result() == ZERO))
    # Undecided indices -> the deferred symbolic cell.
    Ensures(Implies(eq_class(i, j) == EQ_UNKNOWN, Result() == DEFERRED))
    # post-conditions-end
    # impl-start
    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    return DEFERRED
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-12419 (nagini). SOUND. All work, root env python python, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: eq_class trichotomy axiom (Result in {EQ_FALSE,EQ_TRUE,EQ_UNKNOWN}) + three Implies postconditions pinning Result on every eq_class outcome (EQ_TRUE->ONE, EQ_FALSE->ZERO, EQ_UNKNOWN->DEFERRED) + Requires(MustTerminate(2)). Cell tags {10,11,12} disjoint from EQ codes {0,1,2} block echo. This fully determines the output on every input; any verifying impl must be behaviorally identical to gold.

atk_1 PREPATCH BUG reproduced (struct_eq-only: if struct_eq return ONE else ZERO) -> EXIT 2 NOT-A-COUNTEREXAMPLE (does not verify; spec senses the change). prepatch_reproduced=true.
- atk_2 swapped values (EQ_TRUE->ZERO, EQ_FALSE->ONE) -> EXIT 2 does-not-verify.
- atk_3 partial-domain: undecided->ZERO (the exact real bug) -> EXIT 2 does-not-verify.
- atk_4 boundary: undecided->ONE -> EXIT 2 does-not-verify.
- atk_5 ungrounded-oracle echo: return eq_class(i,j) directly -> EXIT 2 does-not-verify (ill-typed vs cell tags).
- atk_6 control-flow-effect: struct_eq short-circuit to ONE then eq_class for rest -> EXIT 2 does-not-verify (EQ_TRUE-but-not-struct pairs unprovable, matching §B).
- atk_7 divergence: while-loop spin before returning correct values -> EXIT 2 does-not-verify (MustTerminate(2) rejects; A6 obligation working).
- atk_8 CORRECT alternative phrasing (eq is S.false->ZERO first, then unknown->DEFERRED, else ONE) -> EXIT 0 CANDIDATE (shares spec AND verifies, 20s). This is behaviorally identical to gold, NOT a wrong impl.

MANDATORY RESOLVE on the sole CANDIDATE (atk_8): materialized its faithful refined patch (patches[atk_8]; gold import hunks verbatim + isomorphic _entry: eq=Eq(i,j); if eq is S.false: return S.Zero; if eq is not S.true: return KroneckerDelta(i,j); return S.One) and RAN it through the official harness via harness.run_resolve(sympy__sympy-12419, timeout=1800). RESULT: RESOLVED=True, COMPLETED=True. So the verifying candidate resolves => it does NOT break the spec (verify=>correct holds here). Gold patch control also RESOLVED=True COMPLETED=True; positive control model_base.py VERIFIED in 20.1s.

REFINEMENT.MD AUDIT: every leg R / A-consumed / I (A1 R type-refinement; A2 A-consumed eq_class; A3/A4 R+I; A5 R; A6 I termination; §B struct_eq A-consumed). NO kind-3: the changed op (3-way branch) is modeled directly on the axiomatized unchanged callee eq_class, not behind an axiom about _entry. A-leg correspondence holds: eq_class<->Eq(i,j) 3-valued read and struct_eq<->Python == are grounded by axiom_check.py (G-AX), which imports only sympy and runs the REAL callees; consumed axioms (trichotomy, reflexivity, one-directional struct_eq->EQ_TRUE link) forge no decidedness and cannot over-strengthen.

CONCLUSION: no verifying-but-wrong impl exists; the one verifying candidate resolves. verify=>correct on this bundle. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `model_base.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_base.py`

```python
"""Twin-artifact model for sympy__sympy-12419.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The (i, j) entry of an identity matrix, where i and j are index expressions
  that may be symbolic. The entry depends on the *symbolic* equality of the two
  indices, classified three ways by the unchanged equality decision procedure:

    - if the two indices are decidably EQUAL, the entry is the unit value;
    - if they are decidably UNEQUAL, the entry is the zero value;
    - if equality cannot be decided (the indices are symbolic and neither
      provably equal nor provably unequal), the entry is the deferred symbolic
      value.

  Producing the entry is a single bounded decision: the operation MUST
  terminate and deliver its result (a total-correctness obligation, carried as
  ``MustTerminate`` in the precondition). An implementation that diverges
  before returning — e.g. by re-invoking the entry on the same indices, or
  spinning in a loop — would satisfy the value postconditions only vacuously
  and never deliver an entry; the real operation always returns.

Index expressions are modelled as opaque `int` identity tags; the model never
does arithmetic on them. The result is a 3-valued *tag* identifying which of
the three cell values the entry is (unit / zero / deferred symbolic), not a
number to be summed. Two unchanged equality callees are axiomatized: the 3-valued
equality decision `eq_class` (the equality of the two index expressions,
classified as provably-equal / provably-unequal / undecided) and the structural
identity `struct_eq` (tree-level sameness of the two expressions); their
soundness — including the structural-identity ⟹ provably-equal link — is checked
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# The three outcomes of the unchanged equality-decision callee.
EQ_FALSE = 0    # the two indices are provably unequal
EQ_TRUE = 1     # the two indices are provably equal
EQ_UNKNOWN = 2  # equality of the two indices is undecided

# The three possible cell values, as pairwise-distinct tags. Chosen disjoint
# from the EQ_* codes so the entry cannot be produced by echoing the classifier;
# it must be produced by genuinely branching on it.
ZERO = 10       # the zero cell value
ONE = 11        # the unit cell value
DEFERRED = 12   # the deferred symbolic cell value


# axioms-start
@Pure
@ContractOnly
def eq_class(i: int, j: int) -> int:
    """Unchanged callee: the equality-decision procedure for the two index
    expressions, read as a 3-valued outcome (provably-equal / provably-unequal /
    undecided). Returns one of EQ_TRUE, EQ_FALSE, EQ_UNKNOWN. Reflexive:
    identical indices are decidably equal. The weakest contract the proof needs
    — it does NOT claim any undecided pair is decided.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() == EQ_FALSE or Result() == EQ_TRUE
            or Result() == EQ_UNKNOWN)
    Ensures(Implies(i == j, Result() == EQ_TRUE))


@Pure
@ContractOnly
def struct_eq(i: int, j: int) -> bool:
    """Unchanged callee: structural (tree) identity of two index expressions
    (Python `==`). Reflexive. Structural identity is a SUFFICIENT condition for
    the equality decision: it implies the equality-decision callee classifies
    the pair as provably-equal (the converse does NOT hold — two structurally-
    distinct expressions may still be equal or undecided).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(i == j, Result()))
    Ensures(Implies(Result(), eq_class(i, j) == EQ_TRUE))
# axioms-end


# pure-start
# (no deep-model helpers: the changed operation is a 3-way branch on the
#  axiomatized equality callee, modelled directly in the impl.)
# pure-end


def diagonal_unit_entry(i: int, j: int) -> int:
    # pre-conditions-start
    # TERMINATION: producing the entry is a bounded, loop-free decision that
    # always returns a cell value. An implementation that diverges would meet
    # the value postconditions only vacuously and never deliver an entry;
    # this obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The entry is exactly one of the three cell tags.
    Ensures(Result() == ZERO or Result() == ONE or Result() == DEFERRED)
    # Decidably equal indices -> the unit cell.
    Ensures(Implies(eq_class(i, j) == EQ_TRUE, Result() == ONE))
    # Decidably unequal indices -> the zero cell.
    Ensures(Implies(eq_class(i, j) == EQ_FALSE, Result() == ZERO))
    # Undecided indices -> the deferred symbolic cell.
    Ensures(Implies(eq_class(i, j) == EQ_UNKNOWN, Result() == DEFERRED))
    # post-conditions-end
    # impl-start
    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    return DEFERRED
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-12419 (nagini). SOUND. All work, root env python python, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: eq_class trichotomy axiom (Result in {EQ_FALSE,EQ_TRUE,EQ_UNKNOWN}) + three Implies postconditions pinning Result on every eq_class outcome (EQ_TRUE->ONE, EQ_FALSE->ZERO, EQ_UNKNOWN->DEFERRED) + Requires(MustTerminate(2)). Cell tags {10,11,12} disjoint from EQ codes {0,1,2} block echo. This fully determines the output on every input; any verifying impl must be behaviorally identical to gold.

atk_1 PREPATCH BUG reproduced (struct_eq-only: if struct_eq return ONE else ZERO) -> EXIT 2 NOT-A-COUNTEREXAMPLE (does not verify; spec senses the change). prepatch_reproduced=true.
- atk_2 swapped values (EQ_TRUE->ZERO, EQ_FALSE->ONE) -> EXIT 2 does-not-verify.
- atk_3 partial-domain: undecided->ZERO (the exact real bug) -> EXIT 2 does-not-verify.
- atk_4 boundary: undecided->ONE -> EXIT 2 does-not-verify.
- atk_5 ungrounded-oracle echo: return eq_class(i,j) directly -> EXIT 2 does-not-verify (ill-typed vs cell tags).
- atk_6 control-flow-effect: struct_eq short-circuit to ONE then eq_class for rest -> EXIT 2 does-not-verify (EQ_TRUE-but-not-struct pairs unprovable, matching §B).
- atk_7 divergence: while-loop spin before returning correct values -> EXIT 2 does-not-verify (MustTerminate(2) rejects; A6 obligation working).
- atk_8 CORRECT alternative phrasing (eq is S.false->ZERO first, then unknown->DEFERRED, else ONE) -> EXIT 0 CANDIDATE (shares spec AND verifies, 20s). This is behaviorally identical to gold, NOT a wrong impl.

MANDATORY RESOLVE on the sole CANDIDATE (atk_8): materialized its faithful refined patch (patches[atk_8]; gold import hunks verbatim + isomorphic _entry: eq=Eq(i,j); if eq is S.false: return S.Zero; if eq is not S.true: return KroneckerDelta(i,j); return S.One) and RAN it through the official harness via harness.run_resolve(sympy__sympy-12419, timeout=1800). RESULT: RESOLVED=True, COMPLETED=True. So the verifying candidate resolves => it does NOT break the spec (verify=>correct holds here). Gold patch control also RESOLVED=True COMPLETED=True; positive control model_base.py VERIFIED in 20.1s.

REFINEMENT.MD AUDIT: every leg R / A-consumed / I (A1 R type-refinement; A2 A-consumed eq_class; A3/A4 R+I; A5 R; A6 I termination; §B struct_eq A-consumed). NO kind-3: the changed op (3-way branch) is modeled directly on the axiomatized unchanged callee eq_class, not behind an axiom about _entry. A-leg correspondence holds: eq_class<->Eq(i,j) 3-valued read and struct_eq<->Python == are grounded by axiom_check.py (G-AX), which imports only sympy and runs the REAL callees; consumed axioms (trichotomy, reflexivity, one-directional struct_eq->EQ_TRUE link) forge no decidedness and cannot over-strengthen.

CONCLUSION: no verifying-but-wrong impl exists; the one verifying candidate resolves. verify=>correct on this bundle. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of the spec (diagonal_unit_entry) vs the real Identity._entry at base_commit 479939f8. No divergence found; spec is FAITHFUL (not too strong / no drift).

Evidence:
1. Base-commit worktree (HEAD=479939f8, gold patch applied): real Identity._entry (matexpr.py:478) is exactly `eq=Eq(i,j); if eq is S.true: S.One; elif eq is S.false: S.Zero; return KroneckerDelta(i,j)` — 1:1 with model's ONE/ZERO/DEFERRED 3-way branch on eq_class.
2. G-AX axiom_check.py run against real sympy at base_commit: PASS (20 reflexive + 400 ordered pairs; trichotomy, reflexivity, struct_eq->EQ_TRUE link all hold; 5 structurally-distinct-but-undecided witnesses).
3. Direct faithfulness probe over 23-element index pool (528 ordered pairs incl. non-integer symbols a, S.Half, S.Pi): real _entry returns S.One iff Eq==true, S.Zero iff Eq==false, and a KroneckerDelta that is NEVER S.One/S.Zero on the EQ_UNKNOWN branch — 0 divergences. The spec's postconditions (ZERO/ONE/DEFERRED pairwise distinct, exactly-one-of-three, and the three Implies clauses) all match reality; no input makes the modeled function disagree with the real callee.
4. Model verifies in Nagini (16.3s) — spec satisfiable, not vacuously strong; MustTerminate(2) sound (real _entry is loop-free straight-line, admits every terminating faithful impl, rejects only divergence).

The spec is neither too strong nor drifting: it precisely characterizes the gold post-patch behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the consumer spec view (spec_view(model.py) with the impl region elided), the only artifact the consumer sees; refinement.md and mapping.md — which DO name KroneckerDelta/Eq/_entry — are NOT part of the spec view.

Mechanical G-LEAK screen: passed=True, hard_failures=[] (re-run against gold patch + public problem_statement).

Gold edit (matexpr.py Identity._entry): `eq = Eq(i,j); if eq is S.true: return S.One; elif eq is S.false: return S.Zero; return KroneckerDelta(i,j)`, plus Eq/KroneckerDelta import hunks. The repo-specific mechanism (KroneckerDelta, the three Eq/S.true/S.false reads, the _entry method) is disclosed ONLY in hints_text (smichr's comments), never in the public problem_statement.

Spec-view findings, all clean beyond the public problem_statement:
- No gold-patch identifiers appear: no `KroneckerDelta`, `Eq`, `_entry`, `S.One`, `S.Zero`, `is S.true`/`is S.false`. Carrier names are abstract (`diagonal_unit_entry`, `eq_class`, `struct_eq`, `ONE`/`ZERO`/`DEFERRED`).
- Tag codes are deliberately disjoint ({10,11,12} vs {0,1,2}) — an explicit anti-echo/anti-leak measure, not a leak.
- Postconditions state the abstract input→output behaviour (decidably-equal→unit, decidably-unequal→zero, undecided→deferred symbolic). This is the definitional WHAT of the spec, not the HOW of the repo edit. The 'deferred symbolic value when equality is undecided' discriminator is expressed only at the abstract behavioural level (no KroneckerDelta named), which is unavoidable for a faithful spec — and it is exactly the general correctness property the public problem_statement (double Sum evaluating to 0 instead of n) is asking to be fixed.
- Domain vocabulary ('identity matrix', symbolic 'index expressions') already appears in the public problem_statement.
- MustTerminate/total-correctness framing is a Nagini modeling artifact, not gold-edit content.

No spec-view line quotes the gold edit's repo-specific mechanism or hints-only content. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
