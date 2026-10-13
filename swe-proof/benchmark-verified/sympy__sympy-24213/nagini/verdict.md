# P2 adversarial audit — sympy__sympy-24213

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_3.py`, `atk_6.py` |

**Non-vacuity.** The positive control `model_orig.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,6 +138,10 @@
             Exists(int, lambda i: (0 <= i and i < len(red) and red[i] != red[0])))
     # post-conditions-end
     # impl-start
+    # Pre-patch (buggy) skeleton: rejection is driven by the SURFACE
+    # descriptions -- a naive identity comparison of how each dimension is
+    # written -- rather than by the canonical reductions.  Two addends that are
+    # physically equivalent but written differently are therefore rejected.
     i = 1
     while i < len(surf):
         # invariants-start
@@ -147,16 +151,17 @@
         Invariant(len(surf) >= 1)
         Invariant(1 <= i and i <= len(surf))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 red[k] == red[0]))))
+                                                 surf[k] == surf[0]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                  red[k] == reduction_of(surf[k])))))
         # the addend loop consumes the caller's termination obligation with a
         # strictly decreasing measure (len(surf) - i), discharging
-        # MustTerminate(2) from the precondition.
+        # MustTerminate(2) from the precondition; the prepatch must keep
+        # failing on the SPEC (the Exsures), not on an obligation leak.
         Invariant(MustTerminate(len(surf) - i + 1))
         # invariants-end
-        # Reject iff this addend is not physically equivalent to the first.
-        if not equivalent(red[0], red[i]):
+        # Reject iff this addend's surface description differs from the first.
+        if surf[i] != surf[0]:
             raise DimensionMismatch()
         i = i + 1
     return red[0]
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -150,14 +150,11 @@
                                                  red[k] == red[0]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                  red[k] == reduction_of(surf[k])))))
-        # the addend loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(surf) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(surf) - i + 1))
         # invariants-end
-        # Reject iff this addend is not physically equivalent to the first.
         if not equivalent(red[0], red[i]):
-            raise DimensionMismatch()
+            while True:
+                pass
         i = i + 1
     return red[0]
     # impl-end
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -150,13 +150,9 @@
                                                  red[k] == red[0]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                  red[k] == reduction_of(surf[k])))))
-        # the addend loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(surf) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(surf) - i + 1))
         # invariants-end
-        # Reject iff this addend is not physically equivalent to the first.
-        if not equivalent(red[0], red[i]):
+        if red[i] != red[0]:
             raise DimensionMismatch()
         i = i + 1
     return red[0]
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,7 +139,7 @@
     # post-conditions-end
     # impl-start
     i = 1
-    while i < len(surf):
+    while i < len(surf) - 1:
         # invariants-start
         Invariant(Acc(list_pred(surf), 1 / 2))
         Invariant(Acc(list_pred(red), 1 / 2))
@@ -150,12 +150,8 @@
                                                  red[k] == red[0]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                  red[k] == reduction_of(surf[k])))))
-        # the addend loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(surf) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(surf) - i + 1))
         # invariants-end
-        # Reject iff this addend is not physically equivalent to the first.
         if not equivalent(red[0], red[i]):
             raise DimensionMismatch()
         i = i + 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -150,14 +150,9 @@
                                                  red[k] == red[0]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                  red[k] == reduction_of(surf[k])))))
-        # the addend loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(surf) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(surf) - i + 1))
         # invariants-end
-        # Reject iff this addend is not physically equivalent to the first.
-        if not equivalent(red[0], red[i]):
-            raise DimensionMismatch()
+        raise DimensionMismatch()
         i = i + 1
     return red[0]
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -150,13 +150,9 @@
                                                  red[k] == red[0]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                  red[k] == reduction_of(surf[k])))))
-        # the addend loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(surf) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(surf) - i + 1))
         # invariants-end
-        # Reject iff this addend is not physically equivalent to the first.
-        if not equivalent(red[0], red[i]):
+        if not equivalent(red[i], red[0]):
             raise DimensionMismatch()
         i = i + 1
     return red[0]
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -150,14 +150,8 @@
                                                  red[k] == red[0]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                  red[k] == reduction_of(surf[k])))))
-        # the addend loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(surf) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(surf) - i + 1))
         # invariants-end
-        # Reject iff this addend is not physically equivalent to the first.
-        if not equivalent(red[0], red[i]):
-            raise DimensionMismatch()
         i = i + 1
     return red[0]
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_orig.py`

```python
"""Twin-artifact model for sympy__sympy-24213.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the magnitude of a sum is reduced to its overall physical dimension, the
  dimensions contributed by the individual addends must agree.  The agreement
  that is required is *physical equivalence of dimensions*, NOT identity of the
  way a dimension happens to be written.

  Every dimension has a canonical reduction to a multiset of base dimensions
  raised to integer powers (its dimensional dependencies).  Two dimensions are
  physically equivalent exactly when these canonical reductions coincide, even
  if their surface descriptions differ (for instance a "velocity" written
  directly versus the same physical quantity written as "acceleration times
  time").  The reduction-to-base-dimensions step is the unchanged engine the
  comparison consults; its weakest relevant guarantees are that it is a genuine
  function of the dimension (equal surface descriptions reduce equally) and that
  it agrees with the engine the rest of the system already uses (validated
  against the real engine out-of-band by axiom_check.py / G-AX).

  Desired behaviour of reducing a sum's dimension:

    * If every addend's dimension is physically equivalent to the first
      addend's dimension, the reduction succeeds and reports the common
      dimension; the addends' magnitudes are combined.

    * If some addend's dimension is NOT physically equivalent to the first
      addend's dimension, the reduction is rejected (it signals a dimension
      mismatch).

  The point that matters: a later addend whose surface description differs from
  the first but whose canonical reduction is the same must be ACCEPTED, not
  rejected.  Rejection is driven by inequivalent canonical reductions, never by
  differing surface descriptions alone.

  Reducing a sum's dimension is a bounded pass over its finitely many addends:
  the operation MUST terminate, either returning the common dimension or
  signalling the mismatch (a total-correctness obligation, carried as
  MustTerminate in the precondition).  An implementation that diverges before
  returning or raising would satisfy the value postconditions only vacuously
  and would never deliver a verdict to the caller.

Modelling choices (Nagini fragment):
  * A dimension is modelled by two observable facets carried in parallel lists,
    one entry per addend of the sum:
      - ``red[i]`` (an ``int``): the identity of the dimension's canonical
        reduction to base dimensions.  Two dimensions are physically equivalent
        iff their reduction identities are equal; this is exactly what the
        equivalence test consults via the reduction engine.
      - ``surf[i]`` (an ``int``): the identity of the dimension's surface
        description, which a naive identity comparison consults.
    The engine is a genuine function of the surface description, so equal
    surface descriptions reduce equally: ``surf[i] == surf[j] ==> red[i] ==
    red[j]`` (the model's standing well-formedness assumption).  The converse
    does NOT hold -- two different surface descriptions may reduce to the same
    base dimensions -- and that is the discriminating case.
  * The reduction engine ``reduction_of`` is the unchanged callee; the
    equivalence test is the deep model ``equivalent`` (reduction identities
    equal).
  * The sum has at least one addend; the first establishes the reference
    dimension every other addend is compared against.

No string indexing is used (Nagini bans it).  List access under quantifiers is
guarded by explicit in-bounds conjuncts.  Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class DimensionMismatch(Exception):
    """Signalled when a sum mixes dimensions that are not physically
    equivalent (the rejection the reduction performs)."""
    pass


# axioms-start
@Pure
@ContractOnly
def reduction_of(surface: int) -> int:
    """The unchanged reduction engine: maps a dimension's surface description to
    the identity of its canonical reduction to base dimensions.  As a pure
    function it is automatically a genuine function of the surface description --
    the only guarantee the proof needs -- so a dimension always reduces the same
    way and the rest of the system's notion of "same base dimensions" is shared.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX)."""
    pass
# axioms-end


# pure-start
@Pure
def equivalent(red_a: int, red_b: int) -> bool:
    """Physical equivalence of two dimensions: their canonical reductions to
    base dimensions coincide.  The reductions are obtained from the surface
    descriptions via the reduction engine; equivalence consults the reductions
    ONLY -- never the surface descriptions directly.  This is the whole content
    of the comparison the desired behaviour requires."""
    return red_a == red_b
# pure-end


def collect_sum_dimension(surf: List[int], red: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(surf), 1 / 2))
    Requires(Acc(list_pred(red), 1 / 2))
    # The two facets describe the same addends, and there is at least one.
    Requires(len(surf) == len(red))
    Requires(len(surf) >= 1)
    # The reduction engine is a genuine function of the surface description:
    # each addend's reduction identity is what the engine yields for its
    # surface description.
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(surf),
                                            red[i] == reduction_of(surf[i])))))
    # Reducing a sum's dimension is a bounded pass over its finitely many
    # addends: the operation MUST terminate, either returning the common
    # dimension or signalling the mismatch (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously and
    # would never deliver a verdict to the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(surf), 1 / 2))
    Ensures(Acc(list_pred(red), 1 / 2))
    Ensures(len(surf) == len(red) and len(red) >= 1)
    # Success path: the reduction reports the common reduction identity, which
    # it reaches exactly when EVERY addend is physically equivalent to the first
    # (equal canonical reduction), regardless of differing surface descriptions.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(red),
                                           red[i] == red[0]))))
    Ensures(Result() == red[0])
    # Rejection path: signalled exactly when some addend is NOT physically
    # equivalent to the first (its canonical reduction differs).
    Exsures(DimensionMismatch,
            Acc(list_pred(surf), 1 / 2) and Acc(list_pred(red), 1 / 2) and
            len(surf) == len(red) and len(red) >= 1 and
            Exists(int, lambda i: (0 <= i and i < len(red) and red[i] != red[0])))
    # post-conditions-end
    # impl-start
    i = 1
    while i < len(surf):
        # invariants-start
        Invariant(Acc(list_pred(surf), 1 / 2))
        Invariant(Acc(list_pred(red), 1 / 2))
        Invariant(len(surf) == len(red))
        Invariant(len(surf) >= 1)
        Invariant(1 <= i and i <= len(surf))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 red[k] == red[0]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                 red[k] == reduction_of(surf[k])))))
        # the addend loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(surf) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(surf) - i + 1))
        # invariants-end
        # Reject iff this addend is not physically equivalent to the first.
        if not equivalent(red[0], red[i]):
            raise DimensionMismatch()
        i = i + 1
    return red[0]
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: (env: python, SBU_BENCHMARK_DIR=benchmark-verified). 7 same-spec attacks (same-spec exit 0 for all 7). Weakness cmd: `python -m swebench_unified.adversary weakness nagini sympy__sympy-24213 <atk>`.

SPEC TIGHTNESS: postconditions fully pin the observable — Ensures success returns red[0] iff Forall i red[i]==red[0]; Exsures(DimensionMismatch) permitted iff Exists i red[i]!=red[0]; Requires(MustTerminate(2)) closes divergence. Raise/no-raise decision is bound to reduction-equality (red), not surface (surf).

### Attack results
- atk_1 (prepatch, surf-compare `if surf[i]!=surf[0]`): NOT-A-COUNTEREXAMPLE, does not verify — fails Exsures (raises when reductions equal but surface differs). Prepatch bug reproduced.
- atk_2 (control-flow-effect, `while True: pass` in place of raise): NOT-A-COUNTEREXAMPLE, does not verify — MustTerminate obligation leak. Divergence correctly rejected.
- atk_3 (red-echo, `if red[i]!=red[0]`): CANDIDATE (verifies 24.9s). Faithful patch = gold verbatim (equivalent_dims(dim,addend_dim)). run_resolve => resolved=True, completed=True, attempts=1.
- atk_4 (partial-domain, loop `i<len(surf)-1` skips last addend): NOT-A-COUNTEREXAMPLE, does not verify — fails success Forall (returns red[0] without checking last addend).
- atk_5 (control-flow-effect, unconditional raise in loop): NOT-A-COUNTEREXAMPLE, does not verify — fails Exsures (raises even when all reductions equal).
- atk_6 (ungrounded-oracle echo, symmetric args `equivalent(red[i],red[0])`): CANDIDATE (verifies 20.2s). Faithful patch = symmetric equivalent_dims(addend_dim,dim). run_resolve => resolved=True, completed=True, attempts=1.
- atk_7 (control-flow-effect, no guard, never raise): NOT-A-COUNTEREXAMPLE, does not verify — fails success Forall.

BOTH CANDIDATES' FAITHFUL PATCHES RESOLVE => not weaknesses (verify => correct on these). This clears the stale G-PANEL-1 'fail' recorded in verdict.md (atk_3 echo flagged under the OLD derivation that dropped the resolve step); under the 2026-08-06 fixed policy a resolving echo is not a weakness.

Positive control model_orig.py verifies (scripts/nagini_verify.sh exit 0, 20.6s, 'Verification successful').

REFINEMENT.MD LEG AUDIT (against real source at base_commit e8c22f6): all legs R / A-consumed / A-reference / I, NO kind-3.
- A3 (A-reference): deep model equivalent(red_a,red_b)==(red_a==red_b) vs real DimensionSystem.equivalent_dims(dim1,dim2) which literally returns get_dimensional_dependencies(dim1)==get_dimensional_dependencies(dim2) (dimensions.py:428-431 confirmed). Reduction-equality by construction; correspondence holds.
- A5 (A-consumed): reduction_of ↔ get_dimensional_dependencies (dimensions.py:422-426), encodes only weakest used property (genuine @Pure function of the dimension). Real engine is deterministic. Correct weakest-guarantee.
- A1/A2/A4/A6 = R/I (Dimension<->(surf,red) facets; loop shape; ValueError<->DimensionMismatch; return dim<->red[0]; factor accumulation unchanged/unmodeled). A7 = I (MustTerminate models the finite for-loop's totality). Discriminating case (velocity vs acceleration*time: distinct surf, equal red) is exactly what atk_1 prepatch fails and gold accepts.

VERDICT: SOUND — 7 attacks run (>=5), the only 2 verifying same-spec impls have faithful patches that RESOLVE; spec is neither too weak nor mis-refined.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_3.py`, `atk_6.py` |

**Non-vacuity.** The positive control `model_orig.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_orig.py`

```python
"""Twin-artifact model for sympy__sympy-24213.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the magnitude of a sum is reduced to its overall physical dimension, the
  dimensions contributed by the individual addends must agree.  The agreement
  that is required is *physical equivalence of dimensions*, NOT identity of the
  way a dimension happens to be written.

  Every dimension has a canonical reduction to a multiset of base dimensions
  raised to integer powers (its dimensional dependencies).  Two dimensions are
  physically equivalent exactly when these canonical reductions coincide, even
  if their surface descriptions differ (for instance a "velocity" written
  directly versus the same physical quantity written as "acceleration times
  time").  The reduction-to-base-dimensions step is the unchanged engine the
  comparison consults; its weakest relevant guarantees are that it is a genuine
  function of the dimension (equal surface descriptions reduce equally) and that
  it agrees with the engine the rest of the system already uses (validated
  against the real engine out-of-band by axiom_check.py / G-AX).

  Desired behaviour of reducing a sum's dimension:

    * If every addend's dimension is physically equivalent to the first
      addend's dimension, the reduction succeeds and reports the common
      dimension; the addends' magnitudes are combined.

    * If some addend's dimension is NOT physically equivalent to the first
      addend's dimension, the reduction is rejected (it signals a dimension
      mismatch).

  The point that matters: a later addend whose surface description differs from
  the first but whose canonical reduction is the same must be ACCEPTED, not
  rejected.  Rejection is driven by inequivalent canonical reductions, never by
  differing surface descriptions alone.

  Reducing a sum's dimension is a bounded pass over its finitely many addends:
  the operation MUST terminate, either returning the common dimension or
  signalling the mismatch (a total-correctness obligation, carried as
  MustTerminate in the precondition).  An implementation that diverges before
  returning or raising would satisfy the value postconditions only vacuously
  and would never deliver a verdict to the caller.

Modelling choices (Nagini fragment):
  * A dimension is modelled by two observable facets carried in parallel lists,
    one entry per addend of the sum:
      - ``red[i]`` (an ``int``): the identity of the dimension's canonical
        reduction to base dimensions.  Two dimensions are physically equivalent
        iff their reduction identities are equal; this is exactly what the
        equivalence test consults via the reduction engine.
      - ``surf[i]`` (an ``int``): the identity of the dimension's surface
        description, which a naive identity comparison consults.
    The engine is a genuine function of the surface description, so equal
    surface descriptions reduce equally: ``surf[i] == surf[j] ==> red[i] ==
    red[j]`` (the model's standing well-formedness assumption).  The converse
    does NOT hold -- two different surface descriptions may reduce to the same
    base dimensions -- and that is the discriminating case.
  * The reduction engine ``reduction_of`` is the unchanged callee; the
    equivalence test is the deep model ``equivalent`` (reduction identities
    equal).
  * The sum has at least one addend; the first establishes the reference
    dimension every other addend is compared against.

No string indexing is used (Nagini bans it).  List access under quantifiers is
guarded by explicit in-bounds conjuncts.  Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class DimensionMismatch(Exception):
    """Signalled when a sum mixes dimensions that are not physically
    equivalent (the rejection the reduction performs)."""
    pass


# axioms-start
@Pure
@ContractOnly
def reduction_of(surface: int) -> int:
    """The unchanged reduction engine: maps a dimension's surface description to
    the identity of its canonical reduction to base dimensions.  As a pure
    function it is automatically a genuine function of the surface description --
    the only guarantee the proof needs -- so a dimension always reduces the same
    way and the rest of the system's notion of "same base dimensions" is shared.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX)."""
    pass
# axioms-end


# pure-start
@Pure
def equivalent(red_a: int, red_b: int) -> bool:
    """Physical equivalence of two dimensions: their canonical reductions to
    base dimensions coincide.  The reductions are obtained from the surface
    descriptions via the reduction engine; equivalence consults the reductions
    ONLY -- never the surface descriptions directly.  This is the whole content
    of the comparison the desired behaviour requires."""
    return red_a == red_b
# pure-end


def collect_sum_dimension(surf: List[int], red: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(surf), 1 / 2))
    Requires(Acc(list_pred(red), 1 / 2))
    # The two facets describe the same addends, and there is at least one.
    Requires(len(surf) == len(red))
    Requires(len(surf) >= 1)
    # The reduction engine is a genuine function of the surface description:
    # each addend's reduction identity is what the engine yields for its
    # surface description.
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(surf),
                                            red[i] == reduction_of(surf[i])))))
    # Reducing a sum's dimension is a bounded pass over its finitely many
    # addends: the operation MUST terminate, either returning the common
    # dimension or signalling the mismatch (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously and
    # would never deliver a verdict to the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(surf), 1 / 2))
    Ensures(Acc(list_pred(red), 1 / 2))
    Ensures(len(surf) == len(red) and len(red) >= 1)
    # Success path: the reduction reports the common reduction identity, which
    # it reaches exactly when EVERY addend is physically equivalent to the first
    # (equal canonical reduction), regardless of differing surface descriptions.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(red),
                                           red[i] == red[0]))))
    Ensures(Result() == red[0])
    # Rejection path: signalled exactly when some addend is NOT physically
    # equivalent to the first (its canonical reduction differs).
    Exsures(DimensionMismatch,
            Acc(list_pred(surf), 1 / 2) and Acc(list_pred(red), 1 / 2) and
            len(surf) == len(red) and len(red) >= 1 and
            Exists(int, lambda i: (0 <= i and i < len(red) and red[i] != red[0])))
    # post-conditions-end
    # impl-start
    i = 1
    while i < len(surf):
        # invariants-start
        Invariant(Acc(list_pred(surf), 1 / 2))
        Invariant(Acc(list_pred(red), 1 / 2))
        Invariant(len(surf) == len(red))
        Invariant(len(surf) >= 1)
        Invariant(1 <= i and i <= len(surf))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 red[k] == red[0]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                 red[k] == reduction_of(surf[k])))))
        # the addend loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(surf) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(surf) - i + 1))
        # invariants-end
        # Reject iff this addend is not physically equivalent to the first.
        if not equivalent(red[0], red[i]):
            raise DimensionMismatch()
        i = i + 1
    return red[0]
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: (env: python, SBU_BENCHMARK_DIR=benchmark-verified). 7 same-spec attacks (same-spec exit 0 for all 7). Weakness cmd: `python -m swebench_unified.adversary weakness nagini sympy__sympy-24213 <atk>`.

SPEC TIGHTNESS: postconditions fully pin the observable — Ensures success returns red[0] iff Forall i red[i]==red[0]; Exsures(DimensionMismatch) permitted iff Exists i red[i]!=red[0]; Requires(MustTerminate(2)) closes divergence. Raise/no-raise decision is bound to reduction-equality (red), not surface (surf).

### Attack results
- atk_1 (prepatch, surf-compare `if surf[i]!=surf[0]`): NOT-A-COUNTEREXAMPLE, does not verify — fails Exsures (raises when reductions equal but surface differs). Prepatch bug reproduced.
- atk_2 (control-flow-effect, `while True: pass` in place of raise): NOT-A-COUNTEREXAMPLE, does not verify — MustTerminate obligation leak. Divergence correctly rejected.
- atk_3 (red-echo, `if red[i]!=red[0]`): CANDIDATE (verifies 24.9s). Faithful patch = gold verbatim (equivalent_dims(dim,addend_dim)). run_resolve => resolved=True, completed=True, attempts=1.
- atk_4 (partial-domain, loop `i<len(surf)-1` skips last addend): NOT-A-COUNTEREXAMPLE, does not verify — fails success Forall (returns red[0] without checking last addend).
- atk_5 (control-flow-effect, unconditional raise in loop): NOT-A-COUNTEREXAMPLE, does not verify — fails Exsures (raises even when all reductions equal).
- atk_6 (ungrounded-oracle echo, symmetric args `equivalent(red[i],red[0])`): CANDIDATE (verifies 20.2s). Faithful patch = symmetric equivalent_dims(addend_dim,dim). run_resolve => resolved=True, completed=True, attempts=1.
- atk_7 (control-flow-effect, no guard, never raise): NOT-A-COUNTEREXAMPLE, does not verify — fails success Forall.

BOTH CANDIDATES' FAITHFUL PATCHES RESOLVE => not weaknesses (verify => correct on these). This clears the stale G-PANEL-1 'fail' recorded in verdict.md (atk_3 echo flagged under the OLD derivation that dropped the resolve step); under the 2026-08-06 fixed policy a resolving echo is not a weakness.

Positive control model_orig.py verifies (scripts/nagini_verify.sh exit 0, 20.6s, 'Verification successful').

REFINEMENT.MD LEG AUDIT (against real source at base_commit e8c22f6): all legs R / A-consumed / A-reference / I, NO kind-3.
- A3 (A-reference): deep model equivalent(red_a,red_b)==(red_a==red_b) vs real DimensionSystem.equivalent_dims(dim1,dim2) which literally returns get_dimensional_dependencies(dim1)==get_dimensional_dependencies(dim2) (dimensions.py:428-431 confirmed). Reduction-equality by construction; correspondence holds.
- A5 (A-consumed): reduction_of ↔ get_dimensional_dependencies (dimensions.py:422-426), encodes only weakest used property (genuine @Pure function of the dimension). Real engine is deterministic. Correct weakest-guarantee.
- A1/A2/A4/A6 = R/I (Dimension<->(surf,red) facets; loop shape; ValueError<->DimensionMismatch; return dim<->red[0]; factor accumulation unchanged/unmodeled). A7 = I (MustTerminate models the finite for-loop's totality). Discriminating case (velocity vs acceleration*time: distinct surf, equal red) is exactly what atk_1 prepatch fails and gold accepts.

VERDICT: SOUND — 7 attacks run (>=5), the only 2 verifying same-spec impls have faithful patches that RESOLVE; spec is neither too weak nor mis-refined.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No faithfulness break found. The spec is neither too strong nor drifting from the real repo (Add branch of UnitSystem._collect_factor_and_dimension, patched guard `if not equivalent_dims(dim, addend_dim): raise`).

Evidence run against the real worktree (base @ e8c22f6-era; patched copy):
1. Spec integrity: `same-spec nagini sympy__sympy-24213` on model_prepatch => SAME (byte-identical spec, only impl region differs). model.py verifies with pinned Nagini (22.4s, 'Verification successful'); model_prepatch.py correctly FAILS the Exsures postcondition (spec senses the change / G-DIFF).
2. A-reference: bundled axiom_check.py passes against the real sympy engine (729 pairs + 4000 fuzz + velocity==acceleration*time witness, 0 mismatch). The real DimensionSystem.equivalent_dims literally returns get_dimensional_dependencies(d1)==get_dimensional_dependencies(d2), so equivalent(red_a,red_b)==(red_a==red_b) is exact — not spec-strengthening.
3. End-to-end raise-decision parity on the patched real code vs the model on multi-addend sums: v1+a1*t1 (equivalent -> no raise), v1+m1 (inequivalent -> raise), v1+a1*t1+m1 (raise), l1+l1 (no raise), a1*t1+v1 (no raise). All AGREE with model_raises (some red[i]!=red[0]).
4. A-consumed axiom (reduction_of a genuine @Pure function) is the weakest used property; a weakest-guarantee axiom cannot be too strong.
5. MustTerminate(2) is faithful: the real Add branch is a bounded for-loop over a finite tuple that always returns (factor,dim) or raises ValueError.
6. Domain scoping is honest: inputs whose real reduction raises TypeError (symbolic/non-integer Pow) admit no red[i] satisfying the precondition Requires(red[i]==reduction_of(surf[i])), so they are out of the model's domain; pre- and post-patch propagate that raise identically via the unchanged engine. Legitimate scope restriction, not disagreement.

Return-value abstraction (model returns red[0]; real returns (factor, dim)) is unobserved by the graded oracle: F2P test_issue_24211 checks only WHETHER a ValueError is raised. No in-domain input found where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py docstring + reduction_of axiom + pure `equivalent` + pre/post-conditions of collect_sum_dimension; impl region is elided ('... supplied by the consumer'). mapping.md/refinement.md are NOT part of the consumer spec view (they alone name unitsystem.py, the `dim != addend_dim` guard, equivalent_dims, get_dimensional_dependencies) and are excluded from leakage consideration.

What the spec view discloses: addends of a sum must agree by physical equivalence of *canonical reductions to base dimensions* (dimensional dependencies), NOT by identity of surface description; an addend written differently but reducing to the same base dimensions must be ACCEPTED, rejection only on inequivalent reductions. This is exactly the contract the PUBLIC problem_statement already demands: it says _collect_factor_and_dimension 'does not detect equivalent dimensions in addition' and gives the concrete witness a1*t1 + v1 where Dimension(velocity) vs Dimension(acceleration*time) are physically equivalent yet wrongly raise ValueError. 'Canonical reduction to base dimensions' is sympy-domain knowledge directly implied by that velocity-vs-acceleration*time example in the public statement, not new disclosure.

Nothing in the spec view discloses the gold EDIT beyond the public statement: the changed repo file (unitsystem.py), the changed function name (_collect_factor_and_dimension), the pre-patch guard `dim != addend_dim`, and the gold API calls (equivalent_dims / get_dimensional_dependencies) appear nowhere in the spec view. The spec expresses the required behavioral contract abstractly (int surf/red facets), which is spec fidelity, not gold reconstruction. The MustTerminate/total-correctness clauses are a verification-soundness guard, not edit disclosure. Confirmed against test.jsonl problem_statement and gold patch; G-LEAK lexical screen also passed clean. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
