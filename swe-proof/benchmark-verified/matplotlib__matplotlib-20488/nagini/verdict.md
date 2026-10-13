# P2 adversarial audit — matplotlib__matplotlib-20488

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # finite arithmetic on the data range), so it compares against zero — i.e.
     # it is either zero-or-below or strictly positive.
     Requires(lower_bound <= 0.0 or lower_bound > 0.0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the active normalization is logarithmic the sanitised lower bound is
@@ -72,11 +70,7 @@
     # post-conditions-end
     # impl-start
     result = lower_bound
-    if is_log and lower_bound <= 0.0:
+    if is_log and lower_bound < 0.0:
         result = eps
-    else:
-        # Either not logarithmic, or the candidate is already strictly positive;
-        # in the logarithmic branch the result therefore stays positive.
-        Assert(Implies(is_log, lower_bound > 0.0))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # finite arithmetic on the data range), so it compares against zero — i.e.
     # it is either zero-or-below or strictly positive.
     Requires(lower_bound <= 0.0 or lower_bound > 0.0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the active normalization is logarithmic the sanitised lower bound is
@@ -72,11 +70,7 @@
     # post-conditions-end
     # impl-start
     result = lower_bound
-    if is_log and lower_bound <= 0.0:
+    if is_log:
         result = eps
-    else:
-        # Either not logarithmic, or the candidate is already strictly positive;
-        # in the logarithmic branch the result therefore stays positive.
-        Assert(Implies(is_log, lower_bound > 0.0))
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # finite arithmetic on the data range), so it compares against zero — i.e.
     # it is either zero-or-below or strictly positive.
     Requires(lower_bound <= 0.0 or lower_bound > 0.0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the active normalization is logarithmic the sanitised lower bound is
@@ -72,11 +70,5 @@
     # post-conditions-end
     # impl-start
     result = lower_bound
-    if is_log and lower_bound <= 0.0:
-        result = eps
-    else:
-        # Either not logarithmic, or the candidate is already strictly positive;
-        # in the logarithmic branch the result therefore stays positive.
-        Assert(Implies(is_log, lower_bound > 0.0))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # finite arithmetic on the data range), so it compares against zero — i.e.
     # it is either zero-or-below or strictly positive.
     Requires(lower_bound <= 0.0 or lower_bound > 0.0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the active normalization is logarithmic the sanitised lower bound is
@@ -72,11 +70,7 @@
     # post-conditions-end
     # impl-start
     result = lower_bound
-    if is_log and lower_bound <= 0.0:
+    if is_log or lower_bound <= 0.0:
         result = eps
-    else:
-        # Either not logarithmic, or the candidate is already strictly positive;
-        # in the logarithmic branch the result therefore stays positive.
-        Assert(Implies(is_log, lower_bound > 0.0))
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # finite arithmetic on the data range), so it compares against zero — i.e.
     # it is either zero-or-below or strictly positive.
     Requires(lower_bound <= 0.0 or lower_bound > 0.0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the active normalization is logarithmic the sanitised lower bound is
@@ -72,11 +70,7 @@
     # post-conditions-end
     # impl-start
     result = lower_bound
-    if is_log and lower_bound <= 0.0:
+    if is_log and lower_bound <= eps:
         result = eps
-    else:
-        # Either not logarithmic, or the candidate is already strictly positive;
-        # in the logarithmic branch the result therefore stays positive.
-        Assert(Implies(is_log, lower_bound > 0.0))
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # finite arithmetic on the data range), so it compares against zero — i.e.
     # it is either zero-or-below or strictly positive.
     Requires(lower_bound <= 0.0 or lower_bound > 0.0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the active normalization is logarithmic the sanitised lower bound is
@@ -73,10 +71,6 @@
     # impl-start
     result = lower_bound
     if is_log and lower_bound <= 0.0:
-        result = eps
-    else:
-        # Either not logarithmic, or the candidate is already strictly positive;
-        # in the logarithmic branch the result therefore stays positive.
-        Assert(Implies(is_log, lower_bound > 0.0))
+        result = lower_bound + eps
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # finite arithmetic on the data range), so it compares against zero — i.e.
     # it is either zero-or-below or strictly positive.
     Requires(lower_bound <= 0.0 or lower_bound > 0.0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the active normalization is logarithmic the sanitised lower bound is
@@ -71,12 +69,8 @@
     Ensures(Implies(not (is_log and lower_bound <= 0.0), Result() == lower_bound))
     # post-conditions-end
     # impl-start
-    result = lower_bound
-    if is_log and lower_bound <= 0.0:
-        result = eps
-    else:
-        # Either not logarithmic, or the candidate is already strictly positive;
-        # in the logarithmic branch the result therefore stays positive.
-        Assert(Implies(is_log, lower_bound > 0.0))
+    result = eps
+    if not is_log and lower_bound > 0.0:
+        result = lower_bound
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-20488.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Before a real-valued lower bound is handed to a logarithmic normalization, it
  must be sanitised. A logarithmic normalization is only defined on strictly
  positive numbers, so whenever it is the active normalization the lower bound
  that reaches it MUST be strictly positive. Concretely, given

    * a flag saying whether the active normalization is logarithmic,
    * a candidate lower bound (an arbitrary finite real number that, after the
      resampling round trip, may have landed at zero or below), and
    * a strictly positive floor value (the smallest positive magnitude the
      working numeric type can represent),

  the sanitised lower bound is:

    * the floor value, when the normalization is logarithmic AND the candidate
      lower bound is zero or negative (the candidate is unusable for a log scale
      and is replaced by the smallest positive magnitude); and
    * the candidate lower bound unchanged, in every other case (a non-log
      normalization, or a candidate that is already strictly positive — these
      pass through untouched).

  The guarantee the issue demands: when the normalization is logarithmic the
  sanitised lower bound is always strictly positive, including at the boundary
  where the candidate is exactly zero.

The candidate bound and the floor are interpreted real numbers (verified with
`--float-encoding=real`); the flag is a bool. The behaviour is a sign/zero
conditional on real numbers, so it is modelled directly over floats.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: the behaviour is a direct real-number conditional)
# axioms-end


# pure-start
# (no pure helpers needed)
# pure-end


def sanitized_lower_bound(is_log: bool, lower_bound: float, eps: float) -> float:
    # pre-conditions-start
    # The floor value is the smallest positive magnitude of the working numeric
    # type, hence strictly positive.
    Requires(eps > 0.0)
    # The candidate lower bound is a genuine ordered real number (it arises from
    # finite arithmetic on the data range), so it compares against zero — i.e.
    # it is either zero-or-below or strictly positive.
    Requires(lower_bound <= 0.0 or lower_bound > 0.0)
    # pre-conditions-end
    # post-conditions-start
    # When the active normalization is logarithmic the sanitised lower bound is
    # ALWAYS strictly positive (a log scale is undefined at and below zero) —
    # this is the property the failing case demands, and it must hold even when
    # the candidate is exactly zero.
    Ensures(Implies(is_log, Result() > 0.0))
    # When a sanitisation is actually required (logarithmic AND the candidate is
    # zero or negative) the result is exactly the positive floor value.
    Ensures(Implies(is_log and lower_bound <= 0.0, Result() == eps))
    # Otherwise the candidate lower bound passes through completely unchanged.
    Ensures(Implies(not (is_log and lower_bound <= 0.0), Result() == lower_bound))
    # post-conditions-end
    # impl-start
    result = lower_bound
    if is_log and lower_bound <= 0.0:
        result = eps
    else:
        Assert(Implies(is_log, lower_bound > 0.0))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 distinct same-spec wrong impls encoded (impl region ONLY; axioms/@Pure/Requires/Ensures byte-identical, confirmed by `adversary same-spec` exit 0 for all 7). All ran through `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-20488 <path>`; NONE verified => zero CANDIDATEs => no faithful patch to materialize (patches={}).

ENV NOTE: swebench_unified is importable only from python (the nagini-verifier env lacks it). weakness/verify auto-apply the bundle meta float-encoding=real; bare scripts/nagini_verify.sh omits it and spuriously fails the postcondition, so the positive control was checked via `adversary verify` (VERIFIED 13.8s).

### ATTACK RESULTS (all NOT-A-COUNTEREXAMPLE: same-spec AND verification failed):
- atk_1 (prepatch bug: strict `< 0.0` misses exact zero) — fails Ensures(Implies(is_log,Result()>0)) & clause2 at is_log,lb=0.
- atk_2 (always eps in log branch) — fails clause3 Result()==lb at is_log,lb>0.
- atk_3 (pure pass-through, no sanitization) — fails clause1&2 at is_log,lb<=0.
- atk_4 (wrong connective is_log OR lb<=0) — fails clause3 at non-log,lb<=0.
- atk_5 (wrong threshold lb<=eps) — fails clause3 at is_log,0<lb<eps.
- atk_6 (ungrounded-oracle echo lb+eps in fix branch) — clause2 requires exactly ==eps and clause1 fails for lb<0.
- atk_7 (control-flow-effect: result=eps default + narrowed pass-through) — fails clause3 at non-log / positive-lb combos.

POSITIVE CONTROL: pos_control.py VERIFIED (13.8s). PREPATCH: model_prepatch.py FAILED postcondition Implies(is_log,Result()>0) — real bug reproduced.

WHY SOUND (spec is tight): the three Ensures clauses partition the WHOLE input domain — over reals the precondition `lb<=0.0 or lb>0.0` is total modulo NaN (excluded), so clauses 2 (Implies(is_log and lb<=0, Result()==eps)) and 3 (Implies(not(is_log and lb<=0), Result()==lb)) pin the EXACT output for every input; clause 1 is a redundant guarantee. No functionally-wrong impl can satisfy all three.

A-LEG / CORRESPONDENCE AUDIT (refinement.md): 5 legs, all tagged R or I — NO axiomatized callees, so correctly NO A-consumed / A-reference rows and NO kind-3 step. Legs: (1) result=lb R↔s_vmin numpy-float; (2) is_log R/I↔isinstance(self.norm,LogNorm) unchanged across patch; (3) lb<=0.0 I↔s_vmin<=0 the corrected boundary; (4) result=eps R↔np.finfo(scaled_dtype).eps; (5) else/return I↔fall-through. The single real-callee grounding (eps>0 ↔ np.finfo(dtype).eps>0, plus isinstance→bool abstraction) is validated by axiom_check.py (G-AX): OK — np.finfo(...).eps strictly positive for float16/32/64/128, and model_fixed/model_prepatch == real post/pre-patch logic differing exactly at (is_log, s_vmin==0) over 72 boundary + 50000 fuzz inputs. mapping.md file:line binding (lib/matplotlib/image.py:534-537 @ base_commit) is consistent with the modeled hunk. Correspondence holds; no gap between verify and correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-20488.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Before a real-valued lower bound is handed to a logarithmic normalization, it
  must be sanitised. A logarithmic normalization is only defined on strictly
  positive numbers, so whenever it is the active normalization the lower bound
  that reaches it MUST be strictly positive. Concretely, given

    * a flag saying whether the active normalization is logarithmic,
    * a candidate lower bound (an arbitrary finite real number that, after the
      resampling round trip, may have landed at zero or below), and
    * a strictly positive floor value (the smallest positive magnitude the
      working numeric type can represent),

  the sanitised lower bound is:

    * the floor value, when the normalization is logarithmic AND the candidate
      lower bound is zero or negative (the candidate is unusable for a log scale
      and is replaced by the smallest positive magnitude); and
    * the candidate lower bound unchanged, in every other case (a non-log
      normalization, or a candidate that is already strictly positive — these
      pass through untouched).

  The guarantee the issue demands: when the normalization is logarithmic the
  sanitised lower bound is always strictly positive, including at the boundary
  where the candidate is exactly zero.

The candidate bound and the floor are interpreted real numbers (verified with
`--float-encoding=real`); the flag is a bool. The behaviour is a sign/zero
conditional on real numbers, so it is modelled directly over floats.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: the behaviour is a direct real-number conditional)
# axioms-end


# pure-start
# (no pure helpers needed)
# pure-end


def sanitized_lower_bound(is_log: bool, lower_bound: float, eps: float) -> float:
    # pre-conditions-start
    # The floor value is the smallest positive magnitude of the working numeric
    # type, hence strictly positive.
    Requires(eps > 0.0)
    # The candidate lower bound is a genuine ordered real number (it arises from
    # finite arithmetic on the data range), so it compares against zero — i.e.
    # it is either zero-or-below or strictly positive.
    Requires(lower_bound <= 0.0 or lower_bound > 0.0)
    # pre-conditions-end
    # post-conditions-start
    # When the active normalization is logarithmic the sanitised lower bound is
    # ALWAYS strictly positive (a log scale is undefined at and below zero) —
    # this is the property the failing case demands, and it must hold even when
    # the candidate is exactly zero.
    Ensures(Implies(is_log, Result() > 0.0))
    # When a sanitisation is actually required (logarithmic AND the candidate is
    # zero or negative) the result is exactly the positive floor value.
    Ensures(Implies(is_log and lower_bound <= 0.0, Result() == eps))
    # Otherwise the candidate lower bound passes through completely unchanged.
    Ensures(Implies(not (is_log and lower_bound <= 0.0), Result() == lower_bound))
    # post-conditions-end
    # impl-start
    result = lower_bound
    if is_log and lower_bound <= 0.0:
        result = eps
    else:
        Assert(Implies(is_log, lower_bound > 0.0))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 distinct same-spec wrong impls encoded (impl region ONLY; axioms/@Pure/Requires/Ensures byte-identical, confirmed by `adversary same-spec` exit 0 for all 7). All ran through `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-20488 <path>`; NONE verified => zero CANDIDATEs => no faithful patch to materialize (patches={}).

ENV NOTE: swebench_unified is importable only from python (the nagini-verifier env lacks it). weakness/verify auto-apply the bundle meta float-encoding=real; bare scripts/nagini_verify.sh omits it and spuriously fails the postcondition, so the positive control was checked via `adversary verify` (VERIFIED 13.8s).

### ATTACK RESULTS (all NOT-A-COUNTEREXAMPLE: same-spec AND verification failed):
- atk_1 (prepatch bug: strict `< 0.0` misses exact zero) — fails Ensures(Implies(is_log,Result()>0)) & clause2 at is_log,lb=0.
- atk_2 (always eps in log branch) — fails clause3 Result()==lb at is_log,lb>0.
- atk_3 (pure pass-through, no sanitization) — fails clause1&2 at is_log,lb<=0.
- atk_4 (wrong connective is_log OR lb<=0) — fails clause3 at non-log,lb<=0.
- atk_5 (wrong threshold lb<=eps) — fails clause3 at is_log,0<lb<eps.
- atk_6 (ungrounded-oracle echo lb+eps in fix branch) — clause2 requires exactly ==eps and clause1 fails for lb<0.
- atk_7 (control-flow-effect: result=eps default + narrowed pass-through) — fails clause3 at non-log / positive-lb combos.

POSITIVE CONTROL: pos_control.py VERIFIED (13.8s). PREPATCH: model_prepatch.py FAILED postcondition Implies(is_log,Result()>0) — real bug reproduced.

WHY SOUND (spec is tight): the three Ensures clauses partition the WHOLE input domain — over reals the precondition `lb<=0.0 or lb>0.0` is total modulo NaN (excluded), so clauses 2 (Implies(is_log and lb<=0, Result()==eps)) and 3 (Implies(not(is_log and lb<=0), Result()==lb)) pin the EXACT output for every input; clause 1 is a redundant guarantee. No functionally-wrong impl can satisfy all three.

A-LEG / CORRESPONDENCE AUDIT (refinement.md): 5 legs, all tagged R or I — NO axiomatized callees, so correctly NO A-consumed / A-reference rows and NO kind-3 step. Legs: (1) result=lb R↔s_vmin numpy-float; (2) is_log R/I↔isinstance(self.norm,LogNorm) unchanged across patch; (3) lb<=0.0 I↔s_vmin<=0 the corrected boundary; (4) result=eps R↔np.finfo(scaled_dtype).eps; (5) else/return I↔fall-through. The single real-callee grounding (eps>0 ↔ np.finfo(dtype).eps>0, plus isinstance→bool abstraction) is validated by axiom_check.py (G-AX): OK — np.finfo(...).eps strictly positive for float16/32/64/128, and model_fixed/model_prepatch == real post/pre-patch logic differing exactly at (is_log, s_vmin==0) over 72 boundary + 50000 fuzz inputs. mapping.md file:line binding (lib/matplotlib/image.py:534-537 @ base_commit) is consistent with the modeled hunk. Correspondence holds; no gap between verify and correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function sanitized_lower_bound(is_log, lower_bound, eps) is a faithful abstraction of the gold-patched lower-bound guard in matplotlib.image._ImageBase._make_image (lib/matplotlib/image.py:534-537 at base_commit b7ce415c). Real callee (byte-identical across every repo worktree copy in /tmp): `if isinstance(self.norm, mcolors.LogNorm) and s_vmin <= 0: s_vmin = np.finfo(scaled_dtype).eps`.

Type abstraction is sound: isinstance(self.norm, LogNorm) -> is_log:bool (the only bit consulted; isinstance is unchanged by the patch); s_vmin numpy float scalar -> lower_bound:float (real encoding); np.finfo(scaled_dtype).eps -> eps with Requires(eps>0.0), which holds for every floating dtype (float32~1.19e-7, float64~2.22e-16). Precondition `lower_bound <= 0.0 or lower_bound > 0.0` excludes only NaN, which cannot reach this hunk (vrange arises from finite arithmetic on the autoscaled range) — so the spec is NOT too strong for the reachable domain.

VERIFIED: (1) model.py verifies under Nagini with --float-encoding=real (meta declares float_encoding=real), exit 0, 11.85s. (Note: default nagini_verify.sh without --float-encoding fails — expected, not a defect; the pinned config passes it.) (2) same-spec on the bundle model returns exit 0. (3) Independent differential in /tmp: model impl region (contract-stripped) vs the REAL patched statement over 200,600 inputs — boundary grid (0.0, -0.0, subnormals 5e-324, ±eps32/64, eps/2, ±1e20/1e308, ±inf, numpy float32/float64 carriers) x {LogNorm, LogNorm(vmin,vmax)} and {Normalize, NoNorm, PowerNorm} x {float32,float64}, plus 200k seeded fuzz (seed 20488): 0 divergences. Boundary case is_log=True, lower_bound==0.0: both real (s_vmin<=0 True -> eps) and model (Result==eps>0) agree — this is exactly the F2P fix the postcondition Implies(is_log, Result()>0.0) pins.

No diverging input exists; spec is neither too strong nor too weak relative to the real repo behavior on the reachable (non-NaN) domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + pre/post-conditions) describes only ABSTRACTED behavior, revealing no localization of the gold edit beyond what the public problem_statement already exposes. Checks: (1) No patched file path — 'lib/matplotlib/image.py' never appears (function is standalone `sanitized_lower_bound`, not `_make_image`, the patched symbol). (2) No repo symbols — 'logarithmic normalization' (never LogNorm/mcolors.LogNorm), 'candidate lower bound' (never s_vmin), 'floor value / smallest positive magnitude' (never np.finfo(scaled_dtype).eps). (3) No verbatim gold-patch line, no diff markers, no module path. (4) No bug/fix narration keywords in comments/docstring. The mechanical leakage.screen() returns passed=True with zero hard_failures; meta records G-LEAK status 'pass'; bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md). The only sensitive phrase — 'always strictly positive, including at the boundary where the candidate is exactly zero' — is legitimate BEHAVIOR specification (the <0 -> <=0 discriminator expressed as a property), not edit reconstruction: the solver must still independently locate _make_image, the isinstance guard, s_vmin, and eps. The problem_statement already publicly names LogNorm, vmin/vmax, and the 'Invalid vmin or vmax' ValueError, so the spec reveals strictly LESS edit-localization than the public task. No gold edit leaks beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
