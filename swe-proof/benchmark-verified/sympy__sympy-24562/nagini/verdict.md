# P2 adversarial audit — sympy__sympy-24562

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_recurse.py`, `atk_2_prepatch.py`, `atk_3_num_drop.py`, `atk_4_swap.py`, `atk_5_loop.py`, `atk_6_den_drop.py`, `atk_7_aux_n1.py`, `atk_8_partial.py` |

**Non-vacuity.** The positive control `atk_pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_recurse.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,5 @@
     Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
     # post-conditions-end
     # impl-start
-    # The integer value of the divisor's textual numerator.
-    q_value = read_int(ToSeq(q_digits))  # type: int
-    # The numerator picks up the divisor's denominator; the denominator picks
-    # up the dividend's denominator and the divisor's integer value.
-    out_num = p_num * q_den  # type: int
-    out_den = p_den * q_value  # type: int
-    return (out_num, out_den)
+    return combine_ratio(p_num, p_den, q_digits, q_den)
     # impl-end
```

Attack 2 — `atk_2_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,7 @@
     Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
     # post-conditions-end
     # impl-start
-    # The integer value of the divisor's textual numerator.
-    q_value = read_int(ToSeq(q_digits))  # type: int
-    # The numerator picks up the divisor's denominator; the denominator picks
-    # up the dividend's denominator and the divisor's integer value.
     out_num = p_num * q_den  # type: int
-    out_den = p_den * q_value  # type: int
+    out_den = aux_value(ToSeq(q_digits), p_den)  # type: int
     return (out_num, out_den)
     # impl-end
```

Attack 3 — `atk_3_num_drop.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,8 @@
     Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
     # post-conditions-end
     # impl-start
-    # The integer value of the divisor's textual numerator.
     q_value = read_int(ToSeq(q_digits))  # type: int
-    # The numerator picks up the divisor's denominator; the denominator picks
-    # up the dividend's denominator and the divisor's integer value.
-    out_num = p_num * q_den  # type: int
+    out_num = p_num  # type: int
     out_den = p_den * q_value  # type: int
     return (out_num, out_den)
     # impl-end
```

Attack 4 — `atk_4_swap.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,8 @@
     Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
     # post-conditions-end
     # impl-start
-    # The integer value of the divisor's textual numerator.
     q_value = read_int(ToSeq(q_digits))  # type: int
-    # The numerator picks up the divisor's denominator; the denominator picks
-    # up the dividend's denominator and the divisor's integer value.
-    out_num = p_num * q_den  # type: int
-    out_den = p_den * q_value  # type: int
+    out_num = p_num * q_value  # type: int
+    out_den = p_den * q_den  # type: int
     return (out_num, out_den)
     # impl-end
```

Attack 5 — `atk_5_loop.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,10 @@
     Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
     # post-conditions-end
     # impl-start
-    # The integer value of the divisor's textual numerator.
     q_value = read_int(ToSeq(q_digits))  # type: int
-    # The numerator picks up the divisor's denominator; the denominator picks
-    # up the dividend's denominator and the divisor's integer value.
-    out_num = p_num * q_den  # type: int
-    out_den = p_den * q_value  # type: int
-    return (out_num, out_den)
+    i = 0  # type: int
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
+    return (p_num * q_den, p_den * q_value)
     # impl-end
```

Attack 6 — `atk_6_den_drop.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,8 @@
     Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
     # post-conditions-end
     # impl-start
-    # The integer value of the divisor's textual numerator.
     q_value = read_int(ToSeq(q_digits))  # type: int
-    # The numerator picks up the divisor's denominator; the denominator picks
-    # up the dividend's denominator and the divisor's integer value.
     out_num = p_num * q_den  # type: int
-    out_den = p_den * q_value  # type: int
+    out_den = q_value  # type: int
     return (out_num, out_den)
     # impl-end
```

Attack 7 — `atk_7_aux_n1.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,7 @@
     Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
     # post-conditions-end
     # impl-start
-    # The integer value of the divisor's textual numerator.
-    q_value = read_int(ToSeq(q_digits))  # type: int
-    # The numerator picks up the divisor's denominator; the denominator picks
-    # up the dividend's denominator and the divisor's integer value.
     out_num = p_num * q_den  # type: int
-    out_den = p_den * q_value  # type: int
+    out_den = p_den * aux_value(ToSeq(q_digits), 1)  # type: int
     return (out_num, out_den)
     # impl-end
```

Attack 8 — `atk_8_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,12 @@
     Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
     # post-conditions-end
     # impl-start
-    # The integer value of the divisor's textual numerator.
     q_value = read_int(ToSeq(q_digits))  # type: int
-    # The numerator picks up the divisor's denominator; the denominator picks
-    # up the dividend's denominator and the divisor's integer value.
-    out_num = p_num * q_den  # type: int
+    if q_den == 1:
+        out_num = p_num  # WRONG when q_den==1? p_num*1==p_num so actually correct; use 0 to be wrong
+        out_num = 0
+    else:
+        out_num = p_num * q_den
     out_den = p_den * q_value  # type: int
     return (out_num, out_den)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-24562.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A ratio is formed by dividing one operand (the dividend) by another (the
  divisor). Each operand is an exact rational: the dividend has numerator
  `p_num` and positive denominator `p_den`; the divisor has numerator `q_num`
  -- supplied in textual form as a sequence of decimal-digit characters whose
  value is the integer it spells -- and positive denominator `q_den`.

  The constructed ratio is the quotient of the two operands,
  `(p_num / p_den) / (q_num / q_den)`, expressed as an integer
  numerator/denominator pair before any common-factor reduction:

      numerator   == p_num * q_den
      denominator == p_den * q_num

  where `q_num` is the integer value of the divisor's textual numerator. Both
  component integers are ordinary products of the operands' integer parts.

The divisor's textual numerator is modelled as `List[int]` of decimal-digit
code points (Nagini bans `str` indexing); the sequence theory `PSeq[int]`
carries the specification. The integer value of a digit sequence is named by
the function `read_int`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def read_int(digits: PSeq[int]) -> int:
    """The integer value of a non-empty all-digit sequence of decimal code
    points (the value the digit characters spell, e.g. the sequence `1 0 0`
    has value one hundred). Weakest contract the proof needs: a non-empty
    all-digit sequence has a non-negative integer value.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(digits) >= 1)
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(digits),
                 48 <= digits[k] and digits[k] <= 57), [[digits[k]]])))
    Ensures(Result() >= 0)


@Pure
@ContractOnly
def aux_value(digits: PSeq[int], n: int) -> int:
    """An auxiliary integer-valued function of a non-empty all-digit sequence
    and a positive multiplicity `n`. Its value is deliberately left
    unspecified -- the contract asserts only that it is a non-negative integer
    and, in particular, does NOT relate it to `read_int(digits)` in any way.
    A correct result therefore cannot depend on this quantity.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(digits) >= 1)
    Requires(n >= 1)
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(digits),
                 48 <= digits[k] and digits[k] <= 57), [[digits[k]]])))
    Ensures(Result() >= 0)
# axioms-end


# pure-start
# (no pure helpers required)
# pure-end


def combine_ratio(p_num: int, p_den: int,
                  q_digits: List[int], q_den: int) -> Tuple[int, int]:
    # pre-conditions-start
    Requires(Acc(list_pred(q_digits), 1 / 2))
    # The dividend is an exact ratio with a positive denominator.
    Requires(p_den >= 1)
    # The divisor's numerator is a non-empty digit sequence; its denominator
    # is positive.
    Requires(len(q_digits) >= 1)
    Requires(len(ToSeq(q_digits)) >= 1)
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(ToSeq(q_digits)),
                 48 <= ToSeq(q_digits)[k] and ToSeq(q_digits)[k] <= 57),
         [[ToSeq(q_digits)[k]]])))
    Requires(q_den >= 1)
    # The combination must terminate: the caller grants a finite obligation,
    # so a diverging implementation (frozen loop / unbounded self-call)
    # cannot satisfy this contract.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(q_digits), 1 / 2))
    Ensures(len(ToSeq(q_digits)) >= 1)
    Ensures(Forall(int, lambda k:
        (Implies(0 <= k and k < len(ToSeq(q_digits)),
                 48 <= ToSeq(q_digits)[k] and ToSeq(q_digits)[k] <= 57),
         [[ToSeq(q_digits)[k]]])))
    # The quotient's numerator is the dividend's numerator scaled by the
    # divisor's denominator.
    Ensures(Result()[0] == p_num * q_den)
    # The quotient's denominator is the dividend's denominator scaled by the
    # integer value of the divisor's textual numerator.
    Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
    # post-conditions-end
    # impl-start
    q_value = read_int(ToSeq(q_digits))  # type: int
    # accumulate denominator in the other order; read token before numerator
    acc = 1  # type: int
    acc = acc * p_den
    acc = acc * q_value
    num = q_den * p_num  # type: int
    return (num, acc)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. This bundle was REPAIRED today (Aug 13): the prior audit recorded BROKEN via atk_10_recurse (unconditional self-recursion verified because the OLD frozen spec lacked MustTerminate — only PARTIAL correctness). The repair added Requires(MustTerminate(1)) AND the numerator pin Ensures(Result()[0]==p_num*q_den) (the old spec pinned only the denominator).

PROTOCOL EXECUTED. 8 distinct same-spec wrong impls, all same-spec exit 0, all weakness exit 2 (verification failed — genuine rejections, confirmed by reading each out_*.txt = 'attack does not verify', not timeouts). Runs were batched 3-at-a-time as background jobs (each spawns JVM+Z3). Command form: `python -m swebench_unified.adversary weakness nagini sympy__sympy-24562 <atk>.py`.
  - atk_1_recurse (control-flow / prior CE re-encoded): `return combine_ratio(...)` unconditional self-recursion -> FAILS now (MustTerminate(1) rejects it; the exact hole that made the prior version BROKEN is closed).
  - atk_2_prepatch (the prepatch bug): out_den = aux_value(ToSeq(q_digits), p_den) -> fails A6 (Result()[1]==p_den*read_int).
  - atk_3_num_drop: out_num = p_num (drops q_den) -> fails A5.
  - atk_4_swap: numerator/denominator factors swapped -> fails A5.
  - atk_5_loop (control-flow-effect): `while i>=0: i+=1` then correct return -> FAILS (MustTerminate rejects diverging body).
  - atk_6_den_drop: out_den = q_value (drops p_den) -> fails A6.
  - atk_7_aux_n1 (ungrounded-oracle echo): out_den = p_den*aux_value(...,1) -> fails A6 (aux_value unpinned, cannot prove == read_int).
  - atk_8_partial (partial-domain/boundary): out_num=0 on q_den==1 branch -> fails A5.

CANDIDATE handling (protocol step 2): the ONLY weakness exit 0 is atk_pos_control — a STRUCTURALLY-DIFFERENT CORRECT impl (denominator accumulated 1*p_den*read_int in the other order, token read before numerator formed), verifies in 16.9s. Its faithful refined patch is the gold patch VERBATIM (it computes the identical pre-reduction pair (p_num*q_den, p_den*read_int(q_digits)) = gold's (p, Q)). MATERIALIZED to faithful_atk_pos_control.diff and RAN through the official harness: run_resolve('sympy__sympy-24562', patch, run_id='sbu-eq-poscontrol') -> completed=True, resolved=True. So the sole verifying candidate's faithful patch RESOLVES => verify does NOT admit an unresolving impl. (This is the required non-vacuity + resolve check, not speculation.)

G-AX (A-leg correspondence): `python axiom_check.py` -> exit 0: read_int (A-consumed) sound on 12 boundary + 20000 fuzz all-digit tokens vs fractions.Fraction(s).numerator, Requires-excluded boundary (14) confirmed; aux_value (A-reference) sound on 8 boundary + 5000 fuzz vs fractions.Fraction(s*n).numerator; discriminating fact int(s*n)!=n*int(s) confirmed (4530/5000 differ). Both A-legs' docstrings are neutral (no bug->fix mechanism leaked); model.py's proof never references aux_value.

refinement.md leg audit: A1(R) A2(R) A3(R) A4(A-consumed read_int) A5(I+R) A6(I) A7(R+I) — every leg R/A-consumed/A-reference/I, NO kind-3. The one genuinely changed op (fresh-accumulator denominator vs in-place reuse of textual q) is captured by the model(read-then-scale, verified) vs prepatch(repeat-then-read = unpinned aux_value, fails) contrast; no @ContractOnly axiom stands in for the changed accumulation. Correspondence holds.

prepatch_reproduced=true: model_prepatch.py's impl uses aux_value(ToSeq(q_digits), p_den) for the denominator, matching atk_2 (rejected by A6). No verifying wrong impl's faithful patch fails to resolve; nothing breaks the spec after >=8 attacks + the mandatory candidate resolve run.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_recurse.py`, `atk_2_prepatch.py`, `atk_3_num_drop.py`, `atk_4_swap.py`, `atk_5_loop.py`, `atk_6_den_drop.py`, `atk_7_aux_n1.py`, `atk_8_partial.py` |

**Non-vacuity.** The positive control `atk_pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_recurse.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_prepatch.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_num_drop.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_swap.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_loop.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_den_drop.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_aux_n1.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_partial.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-24562.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A ratio is formed by dividing one operand (the dividend) by another (the
  divisor). Each operand is an exact rational: the dividend has numerator
  `p_num` and positive denominator `p_den`; the divisor has numerator `q_num`
  -- supplied in textual form as a sequence of decimal-digit characters whose
  value is the integer it spells -- and positive denominator `q_den`.

  The constructed ratio is the quotient of the two operands,
  `(p_num / p_den) / (q_num / q_den)`, expressed as an integer
  numerator/denominator pair before any common-factor reduction:

      numerator   == p_num * q_den
      denominator == p_den * q_num

  where `q_num` is the integer value of the divisor's textual numerator. Both
  component integers are ordinary products of the operands' integer parts.

The divisor's textual numerator is modelled as `List[int]` of decimal-digit
code points (Nagini bans `str` indexing); the sequence theory `PSeq[int]`
carries the specification. The integer value of a digit sequence is named by
the function `read_int`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def read_int(digits: PSeq[int]) -> int:
    """The integer value of a non-empty all-digit sequence of decimal code
    points (the value the digit characters spell, e.g. the sequence `1 0 0`
    has value one hundred). Weakest contract the proof needs: a non-empty
    all-digit sequence has a non-negative integer value.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(digits) >= 1)
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(digits),
                 48 <= digits[k] and digits[k] <= 57), [[digits[k]]])))
    Ensures(Result() >= 0)


@Pure
@ContractOnly
def aux_value(digits: PSeq[int], n: int) -> int:
    """An auxiliary integer-valued function of a non-empty all-digit sequence
    and a positive multiplicity `n`. Its value is deliberately left
    unspecified -- the contract asserts only that it is a non-negative integer
    and, in particular, does NOT relate it to `read_int(digits)` in any way.
    A correct result therefore cannot depend on this quantity.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(digits) >= 1)
    Requires(n >= 1)
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(digits),
                 48 <= digits[k] and digits[k] <= 57), [[digits[k]]])))
    Ensures(Result() >= 0)
# axioms-end


# pure-start
# (no pure helpers required)
# pure-end


def combine_ratio(p_num: int, p_den: int,
                  q_digits: List[int], q_den: int) -> Tuple[int, int]:
    # pre-conditions-start
    Requires(Acc(list_pred(q_digits), 1 / 2))
    # The dividend is an exact ratio with a positive denominator.
    Requires(p_den >= 1)
    # The divisor's numerator is a non-empty digit sequence; its denominator
    # is positive.
    Requires(len(q_digits) >= 1)
    Requires(len(ToSeq(q_digits)) >= 1)
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(ToSeq(q_digits)),
                 48 <= ToSeq(q_digits)[k] and ToSeq(q_digits)[k] <= 57),
         [[ToSeq(q_digits)[k]]])))
    Requires(q_den >= 1)
    # The combination must terminate: the caller grants a finite obligation,
    # so a diverging implementation (frozen loop / unbounded self-call)
    # cannot satisfy this contract.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(q_digits), 1 / 2))
    Ensures(len(ToSeq(q_digits)) >= 1)
    Ensures(Forall(int, lambda k:
        (Implies(0 <= k and k < len(ToSeq(q_digits)),
                 48 <= ToSeq(q_digits)[k] and ToSeq(q_digits)[k] <= 57),
         [[ToSeq(q_digits)[k]]])))
    # The quotient's numerator is the dividend's numerator scaled by the
    # divisor's denominator.
    Ensures(Result()[0] == p_num * q_den)
    # The quotient's denominator is the dividend's denominator scaled by the
    # integer value of the divisor's textual numerator.
    Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
    # post-conditions-end
    # impl-start
    q_value = read_int(ToSeq(q_digits))  # type: int
    # accumulate denominator in the other order; read token before numerator
    acc = 1  # type: int
    acc = acc * p_den
    acc = acc * q_value
    num = q_den * p_num  # type: int
    return (num, acc)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. This bundle was REPAIRED today (Aug 13): the prior audit recorded BROKEN via atk_10_recurse (unconditional self-recursion verified because the OLD frozen spec lacked MustTerminate — only PARTIAL correctness). The repair added Requires(MustTerminate(1)) AND the numerator pin Ensures(Result()[0]==p_num*q_den) (the old spec pinned only the denominator).

PROTOCOL EXECUTED. 8 distinct same-spec wrong impls, all same-spec exit 0, all weakness exit 2 (verification failed — genuine rejections, confirmed by reading each out_*.txt = 'attack does not verify', not timeouts). Runs were batched 3-at-a-time as background jobs (each spawns JVM+Z3). Command form: `python -m swebench_unified.adversary weakness nagini sympy__sympy-24562 <atk>.py`.
  - atk_1_recurse (control-flow / prior CE re-encoded): `return combine_ratio(...)` unconditional self-recursion -> FAILS now (MustTerminate(1) rejects it; the exact hole that made the prior version BROKEN is closed).
  - atk_2_prepatch (the prepatch bug): out_den = aux_value(ToSeq(q_digits), p_den) -> fails A6 (Result()[1]==p_den*read_int).
  - atk_3_num_drop: out_num = p_num (drops q_den) -> fails A5.
  - atk_4_swap: numerator/denominator factors swapped -> fails A5.
  - atk_5_loop (control-flow-effect): `while i>=0: i+=1` then correct return -> FAILS (MustTerminate rejects diverging body).
  - atk_6_den_drop: out_den = q_value (drops p_den) -> fails A6.
  - atk_7_aux_n1 (ungrounded-oracle echo): out_den = p_den*aux_value(...,1) -> fails A6 (aux_value unpinned, cannot prove == read_int).
  - atk_8_partial (partial-domain/boundary): out_num=0 on q_den==1 branch -> fails A5.

CANDIDATE handling (protocol step 2): the ONLY weakness exit 0 is atk_pos_control — a STRUCTURALLY-DIFFERENT CORRECT impl (denominator accumulated 1*p_den*read_int in the other order, token read before numerator formed), verifies in 16.9s. Its faithful refined patch is the gold patch VERBATIM (it computes the identical pre-reduction pair (p_num*q_den, p_den*read_int(q_digits)) = gold's (p, Q)). MATERIALIZED to faithful_atk_pos_control.diff and RAN through the official harness: run_resolve('sympy__sympy-24562', patch, run_id='sbu-eq-poscontrol') -> completed=True, resolved=True. So the sole verifying candidate's faithful patch RESOLVES => verify does NOT admit an unresolving impl. (This is the required non-vacuity + resolve check, not speculation.)

G-AX (A-leg correspondence): `python axiom_check.py` -> exit 0: read_int (A-consumed) sound on 12 boundary + 20000 fuzz all-digit tokens vs fractions.Fraction(s).numerator, Requires-excluded boundary (14) confirmed; aux_value (A-reference) sound on 8 boundary + 5000 fuzz vs fractions.Fraction(s*n).numerator; discriminating fact int(s*n)!=n*int(s) confirmed (4530/5000 differ). Both A-legs' docstrings are neutral (no bug->fix mechanism leaked); model.py's proof never references aux_value.

refinement.md leg audit: A1(R) A2(R) A3(R) A4(A-consumed read_int) A5(I+R) A6(I) A7(R+I) — every leg R/A-consumed/A-reference/I, NO kind-3. The one genuinely changed op (fresh-accumulator denominator vs in-place reuse of textual q) is captured by the model(read-then-scale, verified) vs prepatch(repeat-then-read = unpinned aux_value, fails) contrast; no @ContractOnly axiom stands in for the changed accumulation. Correspondence holds.

prepatch_reproduced=true: model_prepatch.py's impl uses aux_value(ToSeq(q_digits), p_den) for the denominator, matching atk_2 (rejected by A6). No verifying wrong impl's faithful patch fails to resolve; nothing breaks the spec after >=8 attacks + the mandatory candidate resolve run.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check of combine_ratio's spec against the REAL PATCHED repo callee (the integer-combination block of Rational.__new__ after the gold patch, base_commit b1cb676c). The spec pins two postconditions: Result()[0] == p_num*q_den and Result()[1] == p_den*read_int(ToSeq(q_digits)). This is the exact pre-reduction quotient (p_num/p_den)/(read_int/q_den) = (p_num*q_den)/(p_den*read_int); the subsequent gcd reduction is unchanged and ratio-preserving, so the pinned pre-reduction pair transfers to the observed reduced result.

Evidence the modeled function AGREES with the real callee on every in-domain input (no diverging input found):
1. Bundle conformance_check.py run against a freshly gold-patched testbed (verified the Q-accumulator patch applied): 'G-CONF OK ... 100117 inputs (117 boundary + 100000 fuzz)', 0 disagreements. Comparison is by ratio (Fraction(out_num,out_den) == Fraction(r.p,r.q)), with zero-den mapped to NaN/zoo.
2. Independent adversarial probe (300170 inputs) recomputing spec_pair = (p_num*q_den, p_den*read_int(tok)) vs real Rational(Rational(p_num,p_den,1), Rational(qv,q_den,1)) over targeted edge cases (zero-value tokens '0','00','000'; leading-zero tokens '007','0100','100100'; huge magnitudes up to 1e50; fractional divisors q_den up to 1e15; negatives) plus 200k random inputs within the Requires domain: 0 disagreements.

The read_int axiom (Requires all-digit token len>=1; Ensures Result()>=0) is a sound UNDER-approximation of the real textual-integer reader (fractions.Fraction(s).numerator), not too strong: it constrains the callee only where the reader genuinely returns a non-negative int, and the tightened all-digit precondition excludes signed/non-digit inputs where the reader could be negative or raise (validated by axiom_check.py G-AX). The aux_value axiom is unpinned and not referenced by model.py's proof/postconditions, so it cannot make the consumer spec too strong.

Model verifies under the pinned Nagini verifier (Verification successful, 14.25s). Spec region is the audited frozen spec. No input found on which the modeled function disagrees with the real patched callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = projected model.py (docstring + read_int/aux_value axiom contracts + combine_ratio pre/post-conditions; impl elided). Mechanical G-LEAK screen PASSES (no hard failures) — verified via leakage.screen against the frozen row. Semantic review confirms no leak beyond public problem_statement.

Gold edit: introduce a fresh accumulator Q so the divisor's TEXTUAL numerator is read as a number exactly once (patch: Q=1; q*=p.q -> Q*=p.q; q=q.p -> Q*=q.p; else Q*=int(q); q=Q), replacing the pre-patch reuse of variable q that caused string repetition ('100'*2='100100'). Problem_statement discloses only the symptom Rational('0.5','100')==1/100100 vs 1/200; no mechanism.

Spec view checks: (1) no diff markers; (2) patched path sympy/core/numbers.py and module dotted name appear only in the HIDDEN mapping.md, not the spec view; (3) patch touches no distinctive def/class symbol (__new__ is non-distinctive), so no identifier/comment symbol echo; (4) no bug/fix/regression narration in any spec-view comment/docstring; (5) the axiom docstrings avoid the mechanism — aux_value is named neutrally, is UNUSED by model.py, and its docstring explicitly states it is unspecified and does NOT relate to read_int, disclosing nothing about the string-repetition root cause (that meaning lives only in hidden mapping.md/axiom_check.py); (6) textual operands ('0.5','100') are already public in the issue.

The spec states the CORRECT behavior (numerator == p_num*q_den, denominator == p_den*read_int(q_num) = read-once-then-scale). Stating correct behavior is a spec's legitimate function and is not a reproduction of the gold diff or its bug->fix mechanism; a solver cannot reconstruct the fresh-accumulator/variable-reuse edit from the spec view beyond the public problem statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
