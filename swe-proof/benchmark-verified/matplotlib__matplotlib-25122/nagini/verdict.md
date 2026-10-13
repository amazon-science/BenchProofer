# P2 adversarial audit — matplotlib__matplotlib-25122

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_2.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -189,7 +189,7 @@
         weight = window[i - 1]
         Assert(ToSeq(window).drop(i - 1)[0] == weight)
         Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
-        total = weight * weight + total
+        total = magnitude(weight) * magnitude(weight) + total
         i = i - 1
     Assert(squares_are_sign_blind(ToSeq(window)))
     return total
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -149,7 +149,7 @@
         weight = window[i - 1]
         Assert(ToSeq(window).drop(i - 1)[0] == weight)
         Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
-        total = weight + total
+        total = magnitude(weight) + total
         i = i - 1
     return total
     # impl-end
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -149,7 +149,7 @@
         weight = window[i - 1]
         Assert(ToSeq(window).drop(i - 1)[0] == weight)
         Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
-        total = weight + total
+        total = total + weight
         i = i - 1
     return total
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -149,7 +149,8 @@
         weight = window[i - 1]
         Assert(ToSeq(window).drop(i - 1)[0] == weight)
         Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
-        total = weight + total
+        tmp = weight + weight
+        total = tmp - weight + total
         i = i - 1
     return total
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -189,7 +189,7 @@
         weight = window[i - 1]
         Assert(ToSeq(window).drop(i - 1)[0] == weight)
         Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
-        total = weight * weight + total
+        total = total + weight * weight
         i = i - 1
     Assert(squares_are_sign_blind(ToSeq(window)))
     return total
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,7 +135,7 @@
     # post-conditions-end
     # impl-start
     total = 0
-    i = len(window)
+    i = len(window) - 1 if len(window) > 0 else 0
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(window), 1 / 2))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -151,6 +151,10 @@
         Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
         total = weight + total
         i = i - 1
+    j = 1
+    while j > 0:
+        Invariant(Acc(list_pred(window), 1 / 2))
+        j = j
     return total
     # impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25122.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a windowed segment of a signal is turned into a spectral estimate, the
  estimate is divided by a normalisation factor that compensates for the energy
  the analysis window removes. Two such normalisation factors are formed from
  the window's per-sample weights:

    (1) the AMPLITUDE normalisation -- the running total of the window's
        per-sample weights, taken with their sign. A window weight may be
        negative, and a negative weight must SUBTRACT from the total: the factor
        is the algebraic sum of the weights, NOT the sum of their magnitudes.
        (For a window that dips below zero these two totals disagree; the
        algebraic sum is the correct one.)

    (2) the POWER normalisation -- the running total of the SQUARES of the
        window's per-sample weights. Because squaring discards sign, this total
        is unaffected by whether each weight is taken with its sign or by its
        magnitude: the two readings of (2) always coincide.

  The desired behaviour: factor (1) is the signed running total of the weights;
  factor (2) is the running total of their squares. The amplitude factor is the
  locus that a window with negative weights makes observable.

The window weights are modelled as `List[int]` (the specification is carried by
`PSeq[int]`): the distinguishing behaviour is purely a question of SIGN
handling in the running total -- whether a negative weight subtracts or its
magnitude is added -- which is independent of the weights' real magnitudes, so
signed integers (which already carry both signs) are a faithful, precision-free
carrier (refinement.md states the bijection). The two totals are spelled out as
front-recursive folds so a single unfold is available per loop step.

Each divisor is a bounded, straight-line reduction over one window and MUST
terminate and actually DELIVER its total to the caller (a total-correctness
obligation, carried as ``MustTerminate`` in the preconditions). Nagini is a
partial-correctness verifier by default, so without this obligation a
non-terminating implementation (e.g. an unbounded loop before the return)
satisfies every ``Ensures`` vacuously; the real normalisation divisor is
always computed and used by ``_spectral_helper``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: both normalisation totals are the changed operations
#  themselves and are modelled DEEPLY as spelled-out folds below; they are
#  validated == the real array reductions out-of-band by axiom_check.py / G-AX,
#  not consumed as @ContractOnly contracts.)
# axioms-end


# pure-start
@Pure
def signed_sum(w: PSeq[int]) -> int:
    """The signed (algebraic) running total of the window weights: each weight
    contributes with its own sign, so a negative weight subtracts. Front-
    recursive (one unfold per loop step)."""
    if len(w) == 0:
        return 0
    return w[0] + signed_sum(w.drop(1))


@Pure
def magnitude(x: int) -> int:
    """The magnitude of a single weight (its sign discarded)."""
    if x < 0:
        return -x
    return x


@Pure
def magnitude_sum(w: PSeq[int]) -> int:
    """The running total of the weight MAGNITUDES (each weight's sign discarded
    before adding). Coincides with `signed_sum` only when no weight is negative;
    it is the quantity the desired amplitude factor must NOT use."""
    if len(w) == 0:
        return 0
    return magnitude(w[0]) + magnitude_sum(w.drop(1))


@Pure
def square_sum(w: PSeq[int]) -> int:
    """The running total of the SQUARES of the window weights. Front-recursive."""
    if len(w) == 0:
        return 0
    return w[0] * w[0] + square_sum(w.drop(1))


@Pure
def magnitude_square_sum(w: PSeq[int]) -> int:
    """The running total of the squares of the weight MAGNITUDES."""
    if len(w) == 0:
        return 0
    return magnitude(w[0]) * magnitude(w[0]) + magnitude_square_sum(w.drop(1))


@Pure
def squares_are_sign_blind(w: PSeq[int]) -> bool:
    """Lemma: squaring discards sign pointwise, so the squared-weight total
    reads the same whether each weight is taken with its sign or by its
    magnitude. This pins WHY the power factor (2) is insensitive to the sign
    treatment. Always holds; proven by induction on the front of the sequence.
    """
    Ensures(Result())
    Ensures(square_sum(w) == magnitude_square_sum(w))
    if len(w) == 0:
        return True
    return squares_are_sign_blind(w.drop(1))
# pure-end


def amplitude_loss_divisor(window: List[int]) -> int:
    # pre-conditions-start
    # The window weights are read, never mutated: fractional permission.
    Requires(Acc(list_pred(window), 1 / 2))
    # TERMINATION: the divisor must actually ANSWER (deliver the signed total
    # to the normalisation) -- it is one bounded pass over the window. Nagini
    # is a partial-correctness verifier by default, so without this obligation
    # a non-terminating implementation (an unbounded loop before the return)
    # would satisfy the value postcondition vacuously; the real reduction
    # always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(window), 1 / 2))
    # The amplitude normalisation factor is the SIGNED running total of the
    # window weights -- negative weights subtract. Grounded structurally in the
    # input weights via the spelled-out signed fold, not pinned to an oracle.
    Ensures(Result() == signed_sum(ToSeq(window)))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(window)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(window), 1 / 2))
        Invariant(0 <= i and i <= len(window))
        Invariant(total == signed_sum(ToSeq(window).drop(i)))
        # the loop consumes the caller's termination obligation with a
        # strictly decreasing measure (i), discharging MustTerminate(2)
        # from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        weight = window[i - 1]
        Assert(ToSeq(window).drop(i - 1)[0] == weight)
        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
        total = weight + total
        i = i - 1
    return total
    # impl-end


def power_loss_divisor(window: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(window), 1 / 2))
    # TERMINATION: the divisor must actually ANSWER (deliver the squared total
    # to the normalisation) -- one bounded pass over the window; a diverging
    # implementation satisfies the value postconditions only vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(window), 1 / 2))
    # The power normalisation factor is the running total of the SQUARED window
    # weights.
    Ensures(Result() == square_sum(ToSeq(window)))
    # Squaring is sign-blind, so this factor reads the same whether the weights
    # are taken with their sign or by their magnitude -- the power factor is not
    # the locus of the negative-weight observation.
    Ensures(square_sum(ToSeq(window)) == magnitude_square_sum(ToSeq(window)))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(window)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(window), 1 / 2))
        Invariant(0 <= i and i <= len(window))
        Invariant(total == square_sum(ToSeq(window).drop(i)))
        # the loop consumes the caller's termination obligation with a
        # strictly decreasing measure (i), discharging MustTerminate(2)
        # from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        weight = window[i - 1]
        Assert(ToSeq(window).drop(i - 1)[0] == weight)
        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
        total = weight * weight + total
        i = i - 1
    Assert(squares_are_sign_blind(ToSeq(window)))
    return total
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for matplotlib__matplotlib-25122 (nagini). Project root, env swebench-lean.

SPEC SHAPE: two contracted divisors, each with an EXACT value postcondition. amplitude_loss_divisor: Ensures(Result()==signed_sum(ToSeq(window))) (=window.sum(), the fix Sigma w). power_loss_divisor: Ensures(Result()==square_sum(ToSeq(window))) (=(window**2).sum()) AND Ensures(square_sum==magnitude_square_sum) (the site-3 sign-blind no-op lemma). Axioms region is EMPTY (no @ContractOnly consumed axioms -> no A-consumed legs); folds are DEEP models validated ==real numpy by G-AX/axiom_check.py (A-reference). Gold patch touches 4 sites: 1,2 magnitude/complex amplitude (Sigma|w|->Sigma w), 4 psd-spectrum ((Sigma|w|)^2->(Sigma w)^2), 3 psd-density ((np.abs(w)**2).sum()->(w**2).sum(), a NO-OP).

POSITIVE CONTROL: model.py verified (bash nagini_verify.sh -> exit 0, 16.4s).

### ATTACKS (all same-spec exit 0; weakness = adversary weakness nagini matplotlib__matplotlib-25122 <f>):
- atk_1 [CANDIDATE, exit 0]: power divisor computes magnitude(weight)*magnitude(weight) (Sigma|w|^2) instead of weight*weight. Verifies because square_sum==magnitude_square_sum holds universally (the B3 lemma). FAITHFUL PATCH = fix sites 1,2,4 but LEAVE site 3 at prepatch (np.abs(window)**2).sum(). THIS IS THE KEY TEST of the B3 no-op claim. RESOLVE RESULT: RESOLVED=True (report sbu-diag-atk1: FAIL_TO_PASS 12/12 success, PASS_TO_PASS 2476/0). => B3 machine-confirmed; verify=>correct holds for this candidate.
- atk_2 [NOT-A-COUNTEREXAMPLE, exit 2]: amplitude prepatch bug total=magnitude(weight)+total (Sigma|w|). Verification FAILED (spec's loop invariant total==signed_sum(...drop(i)) rejects it). PREPATCH REPRODUCED = true; the spec senses the amplitude bug (G-DIFF).
- atk_3 [CANDIDATE, exit 0]: amplitude total=total+weight (forward accumulation), value-identical to gold. Faithful patch = GOLD patch. RESOLVE: RESOLVED=True (report sbu-diag-gold2: FAIL_TO_PASS 12/12, PASS_TO_PASS 2476/0). Same gold patch also serves atk_4, atk_5.
- atk_4 [CANDIDATE, exit 0]: control-flow-effect rewrite tmp=weight+weight; total=tmp-weight+total (net = +weight), value-identical to gold. Faithful patch = GOLD (resolved, per sbu-diag-gold2).
- atk_5 [CANDIDATE, exit 0]: power total=total+weight*weight (forward), value-identical to gold. Faithful patch = GOLD (resolved).
- atk_6 [NOT-A-COUNTEREXAMPLE, exit 2]: amplitude loop starts at len-1 (drops last weight) -> wrong value. Verification FAILED (postcondition Result()==signed_sum rejects). Spec correctly rejects a partial-domain wrong impl.
- atk_7 [NOT-A-COUNTEREXAMPLE, exit 2]: non-terminating spin loop before return (unbounded while j>0). Verification FAILED -> MustTerminate(2) obligation correctly rejects the divergent impl. Confirms R0 total-correctness leg is load-bearing.

Resolve runs must be SERIAL: cache_level=env removes the shared image on completion, so two concurrent run_resolve on the same instance race and both fail with 'no report' (observed first). Re-run singly -> both completed and RESOLVED=True.

EVERY verifying candidate's faithful refined patch was MATERIALIZED and RUN through the official harness; all resolved. patch_gold.diff (atk_3/4/5) resolved; patch_atk_1.diff (site-3 reverted) resolved. Both apply cleanly (git apply --check exit 0 against the base_commit image).

REFINEMENT.MD AUDIT: every leg is R / A-reference / I; NO kind-3 and NO A-consumed (empty axioms region). R0 MustTerminate=R (confirmed load-bearing by atk_7). R1 List[int]<->window array=R, precision-free (sign-only bug; axiom_check validates on real float flattop window). R2/A2 signed_sum<->window.sum() and R3/B1 square_sum<->(window**2).sum() = R+A-reference, validated ==real numpy by G-AX (axiom_check.py re-run independently -> exit 0). A3/B2 exact value posts = R+I; site-4 squaring is divisor*divisor (identical concrete op). B3 square_sum==magnitude_square_sum (site-3 no-op) = I, the sole degree of freedom the spec admits -> tested directly by atk_1's materialized patch, RESOLVED. Correspondence of A-reference callees to the real numpy reductions holds.

The prior recorded G-EQ INCONCLUSIVE (2 attacks inconclusive) and G-PANEL-1 WEAK (atk_2 verifies) reflect the pre-fix policy where a same-spec verifying candidate was flagged without running its refined patch. Under the resolve-step policy, every verifying candidate here (incl. the site-3-no-op class atk_1) has a faithful patch that RESOLVES. No verifying wrong-impl produces a non-resolving faithful patch.

VERDICT: SOUND. 7 attacks run (5 same-spec+verifying candidates fully resolve-tested, 2 correctly rejected by the spec). No break found; verify=>correct holds on all machine-checked evidence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_2.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25122.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a windowed segment of a signal is turned into a spectral estimate, the
  estimate is divided by a normalisation factor that compensates for the energy
  the analysis window removes. Two such normalisation factors are formed from
  the window's per-sample weights:

    (1) the AMPLITUDE normalisation -- the running total of the window's
        per-sample weights, taken with their sign. A window weight may be
        negative, and a negative weight must SUBTRACT from the total: the factor
        is the algebraic sum of the weights, NOT the sum of their magnitudes.
        (For a window that dips below zero these two totals disagree; the
        algebraic sum is the correct one.)

    (2) the POWER normalisation -- the running total of the SQUARES of the
        window's per-sample weights. Because squaring discards sign, this total
        is unaffected by whether each weight is taken with its sign or by its
        magnitude: the two readings of (2) always coincide.

  The desired behaviour: factor (1) is the signed running total of the weights;
  factor (2) is the running total of their squares. The amplitude factor is the
  locus that a window with negative weights makes observable.

The window weights are modelled as `List[int]` (the specification is carried by
`PSeq[int]`): the distinguishing behaviour is purely a question of SIGN
handling in the running total -- whether a negative weight subtracts or its
magnitude is added -- which is independent of the weights' real magnitudes, so
signed integers (which already carry both signs) are a faithful, precision-free
carrier (refinement.md states the bijection). The two totals are spelled out as
front-recursive folds so a single unfold is available per loop step.

Each divisor is a bounded, straight-line reduction over one window and MUST
terminate and actually DELIVER its total to the caller (a total-correctness
obligation, carried as ``MustTerminate`` in the preconditions). Nagini is a
partial-correctness verifier by default, so without this obligation a
non-terminating implementation (e.g. an unbounded loop before the return)
satisfies every ``Ensures`` vacuously; the real normalisation divisor is
always computed and used by ``_spectral_helper``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: both normalisation totals are the changed operations
#  themselves and are modelled DEEPLY as spelled-out folds below; they are
#  validated == the real array reductions out-of-band by axiom_check.py / G-AX,
#  not consumed as @ContractOnly contracts.)
# axioms-end


# pure-start
@Pure
def signed_sum(w: PSeq[int]) -> int:
    """The signed (algebraic) running total of the window weights: each weight
    contributes with its own sign, so a negative weight subtracts. Front-
    recursive (one unfold per loop step)."""
    if len(w) == 0:
        return 0
    return w[0] + signed_sum(w.drop(1))


@Pure
def magnitude(x: int) -> int:
    """The magnitude of a single weight (its sign discarded)."""
    if x < 0:
        return -x
    return x


@Pure
def magnitude_sum(w: PSeq[int]) -> int:
    """The running total of the weight MAGNITUDES (each weight's sign discarded
    before adding). Coincides with `signed_sum` only when no weight is negative;
    it is the quantity the desired amplitude factor must NOT use."""
    if len(w) == 0:
        return 0
    return magnitude(w[0]) + magnitude_sum(w.drop(1))


@Pure
def square_sum(w: PSeq[int]) -> int:
    """The running total of the SQUARES of the window weights. Front-recursive."""
    if len(w) == 0:
        return 0
    return w[0] * w[0] + square_sum(w.drop(1))


@Pure
def magnitude_square_sum(w: PSeq[int]) -> int:
    """The running total of the squares of the weight MAGNITUDES."""
    if len(w) == 0:
        return 0
    return magnitude(w[0]) * magnitude(w[0]) + magnitude_square_sum(w.drop(1))


@Pure
def squares_are_sign_blind(w: PSeq[int]) -> bool:
    """Lemma: squaring discards sign pointwise, so the squared-weight total
    reads the same whether each weight is taken with its sign or by its
    magnitude. This pins WHY the power factor (2) is insensitive to the sign
    treatment. Always holds; proven by induction on the front of the sequence.
    """
    Ensures(Result())
    Ensures(square_sum(w) == magnitude_square_sum(w))
    if len(w) == 0:
        return True
    return squares_are_sign_blind(w.drop(1))
# pure-end


def amplitude_loss_divisor(window: List[int]) -> int:
    # pre-conditions-start
    # The window weights are read, never mutated: fractional permission.
    Requires(Acc(list_pred(window), 1 / 2))
    # TERMINATION: the divisor must actually ANSWER (deliver the signed total
    # to the normalisation) -- it is one bounded pass over the window. Nagini
    # is a partial-correctness verifier by default, so without this obligation
    # a non-terminating implementation (an unbounded loop before the return)
    # would satisfy the value postcondition vacuously; the real reduction
    # always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(window), 1 / 2))
    # The amplitude normalisation factor is the SIGNED running total of the
    # window weights -- negative weights subtract. Grounded structurally in the
    # input weights via the spelled-out signed fold, not pinned to an oracle.
    Ensures(Result() == signed_sum(ToSeq(window)))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(window)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(window), 1 / 2))
        Invariant(0 <= i and i <= len(window))
        Invariant(total == signed_sum(ToSeq(window).drop(i)))
        # the loop consumes the caller's termination obligation with a
        # strictly decreasing measure (i), discharging MustTerminate(2)
        # from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        weight = window[i - 1]
        Assert(ToSeq(window).drop(i - 1)[0] == weight)
        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
        total = weight + total
        i = i - 1
    return total
    # impl-end


def power_loss_divisor(window: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(window), 1 / 2))
    # TERMINATION: the divisor must actually ANSWER (deliver the squared total
    # to the normalisation) -- one bounded pass over the window; a diverging
    # implementation satisfies the value postconditions only vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(window), 1 / 2))
    # The power normalisation factor is the running total of the SQUARED window
    # weights.
    Ensures(Result() == square_sum(ToSeq(window)))
    # Squaring is sign-blind, so this factor reads the same whether the weights
    # are taken with their sign or by their magnitude -- the power factor is not
    # the locus of the negative-weight observation.
    Ensures(square_sum(ToSeq(window)) == magnitude_square_sum(ToSeq(window)))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(window)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(window), 1 / 2))
        Invariant(0 <= i and i <= len(window))
        Invariant(total == square_sum(ToSeq(window).drop(i)))
        # the loop consumes the caller's termination obligation with a
        # strictly decreasing measure (i), discharging MustTerminate(2)
        # from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        weight = window[i - 1]
        Assert(ToSeq(window).drop(i - 1)[0] == weight)
        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))
        total = weight * weight + total
        i = i - 1
    Assert(squares_are_sign_blind(ToSeq(window)))
    return total
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for matplotlib__matplotlib-25122 (nagini). Project root, env swebench-lean.

SPEC SHAPE: two contracted divisors, each with an EXACT value postcondition. amplitude_loss_divisor: Ensures(Result()==signed_sum(ToSeq(window))) (=window.sum(), the fix Sigma w). power_loss_divisor: Ensures(Result()==square_sum(ToSeq(window))) (=(window**2).sum()) AND Ensures(square_sum==magnitude_square_sum) (the site-3 sign-blind no-op lemma). Axioms region is EMPTY (no @ContractOnly consumed axioms -> no A-consumed legs); folds are DEEP models validated ==real numpy by G-AX/axiom_check.py (A-reference). Gold patch touches 4 sites: 1,2 magnitude/complex amplitude (Sigma|w|->Sigma w), 4 psd-spectrum ((Sigma|w|)^2->(Sigma w)^2), 3 psd-density ((np.abs(w)**2).sum()->(w**2).sum(), a NO-OP).

POSITIVE CONTROL: model.py verified (bash nagini_verify.sh -> exit 0, 16.4s).

### ATTACKS (all same-spec exit 0; weakness = adversary weakness nagini matplotlib__matplotlib-25122 <f>):
- atk_1 [CANDIDATE, exit 0]: power divisor computes magnitude(weight)*magnitude(weight) (Sigma|w|^2) instead of weight*weight. Verifies because square_sum==magnitude_square_sum holds universally (the B3 lemma). FAITHFUL PATCH = fix sites 1,2,4 but LEAVE site 3 at prepatch (np.abs(window)**2).sum(). THIS IS THE KEY TEST of the B3 no-op claim. RESOLVE RESULT: RESOLVED=True (report sbu-diag-atk1: FAIL_TO_PASS 12/12 success, PASS_TO_PASS 2476/0). => B3 machine-confirmed; verify=>correct holds for this candidate.
- atk_2 [NOT-A-COUNTEREXAMPLE, exit 2]: amplitude prepatch bug total=magnitude(weight)+total (Sigma|w|). Verification FAILED (spec's loop invariant total==signed_sum(...drop(i)) rejects it). PREPATCH REPRODUCED = true; the spec senses the amplitude bug (G-DIFF).
- atk_3 [CANDIDATE, exit 0]: amplitude total=total+weight (forward accumulation), value-identical to gold. Faithful patch = GOLD patch. RESOLVE: RESOLVED=True (report sbu-diag-gold2: FAIL_TO_PASS 12/12, PASS_TO_PASS 2476/0). Same gold patch also serves atk_4, atk_5.
- atk_4 [CANDIDATE, exit 0]: control-flow-effect rewrite tmp=weight+weight; total=tmp-weight+total (net = +weight), value-identical to gold. Faithful patch = GOLD (resolved, per sbu-diag-gold2).
- atk_5 [CANDIDATE, exit 0]: power total=total+weight*weight (forward), value-identical to gold. Faithful patch = GOLD (resolved).
- atk_6 [NOT-A-COUNTEREXAMPLE, exit 2]: amplitude loop starts at len-1 (drops last weight) -> wrong value. Verification FAILED (postcondition Result()==signed_sum rejects). Spec correctly rejects a partial-domain wrong impl.
- atk_7 [NOT-A-COUNTEREXAMPLE, exit 2]: non-terminating spin loop before return (unbounded while j>0). Verification FAILED -> MustTerminate(2) obligation correctly rejects the divergent impl. Confirms R0 total-correctness leg is load-bearing.

Resolve runs must be SERIAL: cache_level=env removes the shared image on completion, so two concurrent run_resolve on the same instance race and both fail with 'no report' (observed first). Re-run singly -> both completed and RESOLVED=True.

EVERY verifying candidate's faithful refined patch was MATERIALIZED and RUN through the official harness; all resolved. patch_gold.diff (atk_3/4/5) resolved; patch_atk_1.diff (site-3 reverted) resolved. Both apply cleanly (git apply --check exit 0 against the base_commit image).

REFINEMENT.MD AUDIT: every leg is R / A-reference / I; NO kind-3 and NO A-consumed (empty axioms region). R0 MustTerminate=R (confirmed load-bearing by atk_7). R1 List[int]<->window array=R, precision-free (sign-only bug; axiom_check validates on real float flattop window). R2/A2 signed_sum<->window.sum() and R3/B1 square_sum<->(window**2).sum() = R+A-reference, validated ==real numpy by G-AX (axiom_check.py re-run independently -> exit 0). A3/B2 exact value posts = R+I; site-4 squaring is divisor*divisor (identical concrete op). B3 square_sum==magnitude_square_sum (site-3 no-op) = I, the sole degree of freedom the spec admits -> tested directly by atk_1's materialized patch, RESOLVED. Correspondence of A-reference callees to the real numpy reductions holds.

The prior recorded G-EQ INCONCLUSIVE (2 attacks inconclusive) and G-PANEL-1 WEAK (atk_2 verifies) reflect the pre-fix policy where a same-spec verifying candidate was flagged without running its refined patch. Under the resolve-step policy, every verifying candidate here (incl. the site-3-no-op class atk_1) has a faithful patch that RESOLVES. No verifying wrong-impl produces a non-resolving faithful patch.

VERDICT: SOUND. 7 attacks run (5 same-spec+verifying candidates fully resolve-tested, 2 correctly rejected by the spec). No break found; verify=>correct holds on all machine-checked evidence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled functions and the real callees on the abstracted domain.

Spec region models two divisors of matplotlib.mlab._spectral_helper (base_commit 5ec2bd2):
- amplitude_loss_divisor(window) == signed_sum(ToSeq(window)) <-> real post-patch window.sum() (sites 398/403/430; squared at 430)
- power_loss_divisor(window) == square_sum(ToSeq(window)) <-> real (window**2).sum() (site 427)

Checks performed:
1. Spec integrity: `same-spec nagini matplotlib__matplotlib-25122 <model.py>` -> SAME (exit 0). Spec region byte-identical.
2. Model verifies: scripts/nagini_verify.sh model.py -> 'Verification successful' (exit 0, 15.5s).
3. G-AX / axiom_check.py logic: signed_sum/square_sum/magnitude_sum/magnitude_square_sum == real numpy reductions on 16 boundary + 20000 fuzz windows (recorded pass).
4. Independent divergence hunt over List[int] domain (300k random windows, weights +-100000, len 0-60): 0 divergences of signed_sum vs np.array(w).sum() and square_sum vs (np.array(w)**2).sum(). The folds are exact algebraic reductions and match the real callee on every integer input.
5. float->int refinement is behaviour-faithful for the tested property: the fixed bug (Sum|w| -> Sum w, and its square) is a pure SIGN property, observable exactly when a weight is negative, independent of magnitude/precision. The F2P test test_psd_window_flattop uses np.isclose so float summation rounding is unobservable; the real discriminator win.sum()**2 != np.abs(win).sum()**2 fires on the real negative-weight flattop window, while site-3 density (window**2).sum() is a genuine no-op on that same float window. float_encoding=null justified. Confirmed against the real base_commit source: sites 398/403 (np.abs(window).sum()), 427 ((np.abs(window)**2).sum()), 430 (np.abs(window).sum()**2).
6. Not too strong: MustTerminate(2) matches the real bounded ndarray reductions (total correctness), not an over-strong claim; power_loss_divisor's extra postcondition square_sum==magnitude_square_sum is a universally-true sign-blindness lemma (site-3 no-op) that excludes no real behaviour.

Conclusion: no input exists where the modeled function disagrees with the real callee within the abstracted domain, and the abstraction is faithful for the tested sign behaviour. Spec is not too strong / does not drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch lines >=8 chars, no patched file/module path, no spec-view identifier embedding the only distinctive patched symbol 'spectral_helper', no narration terms). Semantic check against the SOLVER-VISIBLE problem_statement (NOT hints_text): the spec view discloses nothing beyond what the public task already states. The gold edit is dropping np.abs() in mlab._spectral_helper's window normalization (amplitude divisor Σ|w|→Σw; power divisor is a no-op since squaring is sign-blind). The public problem_statement is already extremely explicit: it names 'mlab._spectral_helper', states 'The np.abs is not needed, and give wrong result for window with negative value, such as flattop', and prints the exact discriminating quantity np.abs(window).sum()**2 - window.sum()**2. The spec view's core content — factor (1) is the signed algebraic sum, NOT the sum of magnitudes, and this disagrees only when a window has negative weights (flattop) — is precisely that public disclosure restated as desired behaviour. Factor (2) sum-of-squares sign-blindness corresponds to a NO-OP gold hunk (site 3), so restating it leaks no behavior-changing edit. The token '_spectral_helper' in the docstring appears verbatim in the public problem_statement, so it is not a leak (leak.py correctly skips symbols already in the problem statement). No spec-view line reveals a gold-edit specific beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
