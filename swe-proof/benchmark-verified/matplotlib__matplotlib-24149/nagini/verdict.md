# P2 adversarial audit — matplotlib__matplotlib-24149

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,10 +133,10 @@
                     len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
     # post-conditions-end
     # impl-start
-    if any_finite(ToSeq(seq)):
-        rep = first_finite(ToSeq(seq))
-    else:
-        rep = first_unconditional(ToSeq(seq))
+    # ATTACK: prepatch bug — call first-finite selector with NO fallback for the
+    # all-non-finite case. first_finite's Requires(any_finite) is unmet when the
+    # sequence has no finite element.
+    rep = first_finite(ToSeq(seq))
     return rep
     # impl-end
 
```

Attack 2 — `atk_2.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -133,10 +133,15 @@
                     len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
     # post-conditions-end
     # impl-start
+    # ATTACK: compute the CORRECT representative, then diverge before returning.
+    # Under partial correctness the value postconditions hold vacuously; the
+    # faithful real patch would hang Axes.bar. MustTerminate(2) must reject this.
     if any_finite(ToSeq(seq)):
         rep = first_finite(ToSeq(seq))
     else:
         rep = first_unconditional(ToSeq(seq))
+    while True:
+        Invariant(True)
     return rep
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,10 +133,13 @@
                     len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
     # post-conditions-end
     # impl-start
+    # ATTACK: swap the selectors. Under any_finite return the FIRST element
+    # unconditionally (wrong when leading element is non-finite); in the else
+    # branch call first_finite whose precondition any_finite is false.
     if any_finite(ToSeq(seq)):
+        rep = first_unconditional(ToSeq(seq))
+    else:
         rep = first_finite(ToSeq(seq))
-    else:
-        rep = first_unconditional(ToSeq(seq))
     return rep
     # impl-end
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,10 +133,10 @@
                     len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
     # post-conditions-end
     # impl-start
-    if any_finite(ToSeq(seq)):
-        rep = first_finite(ToSeq(seq))
-    else:
-        rep = first_unconditional(ToSeq(seq))
+    # ATTACK: ungrounded constant echo (the old directive-8 hole). Returns a
+    # finite flag (1) regardless of WHICH element is first-finite. Passes a bare
+    # Result()!=0 but not the value-pinned first_finite_value postcondition.
+    rep = 1
     return rep
     # impl-end
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,10 +133,10 @@
                     len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
     # post-conditions-end
     # impl-start
-    if any_finite(ToSeq(seq)):
-        rep = first_finite(ToSeq(seq))
-    else:
-        rep = first_unconditional(ToSeq(seq))
+    # ATTACK: ignore the any_finite guard entirely; always return the first
+    # element unconditionally. Wrong whenever a leading element is non-finite
+    # but a later element is finite (first_unconditional != first_finite_value).
+    rep = first_unconditional(ToSeq(seq))
     return rep
     # impl-end
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,10 +133,17 @@
                     len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
     # post-conditions-end
     # impl-start
+    # ATTACK: second nontermination shape — an unbounded increasing counter loop
+    # (no decreasing measure) after computing the right value. MustTerminate(2)
+    # must reject: the loop cannot exhibit a strictly decreasing measure.
     if any_finite(ToSeq(seq)):
         rep = first_finite(ToSeq(seq))
     else:
         rep = first_unconditional(ToSeq(seq))
+    i = 0
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     return rep
     # impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24149.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A width-conversion helper picks one representative coordinate out of a
  non-empty sequence of coordinate values, used to anchor a unit-aware width
  addition. Each value is either finite or non-finite (a not-a-number /
  missing value). The representative is chosen as follows, and the choice must
  always succeed for a non-empty sequence:

    (1) If the sequence contains at least one finite value, the representative
        is the FIRST finite value (so a leading non-finite value is skipped in
        favour of a real coordinate). The representative is therefore finite.

    (2) If the sequence contains NO finite value at all (every value is
        non-finite), the representative is the FIRST value of the sequence
        unconditionally. The selection must still return a value in this case
        — an all-non-finite sequence yields a (non-finite) representative
        rather than failing — so that drawing an artifact whose coordinates
        are entirely non-finite remains a defined, total operation.

  The two coordinate sources fed to this helper (the original positions and
  their unit-converted form) are each selected by this same rule.

  Selection is a bounded, loop-free choice between two selectors: it MUST
  actually deliver the representative to its caller (total correctness,
  carried as a MustTerminate obligation in the preconditions). An
  implementation that diverges before returning would satisfy the value
  postconditions only vacuously and would never anchor the width addition.

A coordinate sequence is modelled as ``List[int]`` of per-element finiteness
flags (0 == the element is non-finite; non-zero == the element is finite). The
unchanged "first finite element" and "first element unconditionally" selectors
are axiomatized callees over ``PSeq[int]`` (their provenance + executable
soundness check live in mapping.md / axiom_check.py); the "is there any finite
element" predicate driving the choice is spelled out deeply as a front-recursive
fold (``any_finite``). The selection functions return the chosen flag.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def first_finite(s: PSeq[int]) -> int:
    """First finite element selector (unchanged community callee), restricted
    to the flag carrier. It returns a value only when a finite element exists;
    on a sequence with no finite element it does not return normally (the
    caller must guard that case). Weakest contract the proof needs: under the
    "some element is finite" precondition the returned value is THE first finite
    element of the sequence (which is therefore itself finite, i.e. non-zero) —
    the identity of the selected element, not merely the fact that it is finite.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(any_finite(s))
    Ensures(Result() == first_finite_value(s))


@Pure
@ContractOnly
def first_unconditional(s: PSeq[int]) -> int:
    """First element selector (unchanged community callee), restricted to the
    flag carrier. It returns the first element of a non-empty sequence
    unconditionally, regardless of finiteness. Weakest contract the proof needs:
    the returned flag equals the first element's flag.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(s) > 0)
    Ensures(Result() == s[0])
# axioms-end


# pure-start
@Pure
def any_finite(s: PSeq[int]) -> bool:
    """Whether the sequence contains at least one finite element (a flag that
    is non-zero). The empty sequence contains none (`False`). Front-recursive so
    one unfold is available to callers."""
    if len(s) == 0:
        return False
    return (s[0] != 0) or any_finite(s.drop(1))


@Pure
def first_finite_value(s: PSeq[int]) -> int:
    """The first finite element of the sequence — the leftmost element whose
    flag is non-zero — when one exists. Front-recursive over the input carrier
    (one unfold per leading non-finite element), so it is a structural function
    of the sequence itself, not an opaque oracle: it skips leading non-finite
    flags and yields the first finite one. Used to PIN the selected
    representative to the actual chosen element of the input (not merely to its
    finiteness)."""
    Requires(any_finite(s))
    if s[0] != 0:
        return s[0]
    return first_finite_value(s.drop(1))
# pure-end


def select_position_x0(seq: List[int]) -> int:
    """Pick the representative of the original-position coordinate sequence:
    the first finite value, or — when no value is finite — the first value
    unconditionally."""
    # pre-conditions-start
    Requires(Acc(list_pred(seq), 1 / 2))
    Requires(len(seq) > 0)
    # TERMINATION: the selection is a bounded, loop-free choice between the
    # two selectors and MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body (e.g. an endless loop
    # before the return) satisfies the value postconditions only vacuously
    # yet never delivers the representative to the caller; the desired
    # selection always returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seq), 1 / 2))
    # (1) when some value is finite, the representative is THE first finite
    #     value of the input — the actual selected element (identity), not just
    #     its finiteness. A constant of the asserted property (any finite flag)
    #     no longer discharges this: it must equal the input's own first finite
    #     element, which only the selector applied to the input produces.
    Ensures(Implies(any_finite(ToSeq(seq)),
                    Result() == first_finite_value(ToSeq(seq))))
    # (2) when NO value is finite, the selection still returns a value: the
    #     first element unconditionally (which is itself non-finite). This is
    #     the total-selection guarantee the all-non-finite input demands.
    Ensures(len(ToSeq(seq)) == len(seq))
    Ensures(Implies(not any_finite(ToSeq(seq)),
                    len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
    # post-conditions-end
    # impl-start
    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep
    # impl-end


def select_position_xconv(seq: List[int]) -> int:
    """Pick the representative of the unit-converted coordinate sequence by the
    same rule: the first finite value, or — when no value is finite — the first
    value unconditionally."""
    # pre-conditions-start
    Requires(Acc(list_pred(seq), 1 / 2))
    Requires(len(seq) > 0)
    # TERMINATION: the selection is a bounded, loop-free choice between the
    # two selectors and MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body (e.g. an endless loop
    # before the return) satisfies the value postconditions only vacuously
    # yet never delivers the representative to the caller; the desired
    # selection always returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seq), 1 / 2))
    # (1) when some value is finite, the representative is THE first finite
    #     value of the input — the actual selected element (identity), not just
    #     its finiteness. A constant of the asserted property (any finite flag)
    #     no longer discharges this: it must equal the input's own first finite
    #     element, which only the selector applied to the input produces.
    Ensures(Implies(any_finite(ToSeq(seq)),
                    Result() == first_finite_value(ToSeq(seq))))
    # (2) when NO value is finite, the selection still returns a value: the
    #     first element unconditionally (which is itself non-finite).
    Ensures(len(ToSeq(seq)) == len(seq))
    Ensures(Implies(not any_finite(ToSeq(seq)),
                    len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
    # post-conditions-end
    # impl-start
    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit of matplotlib__matplotlib-24149 (nagini). env SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=$PWD/benchmark-verified. All commands run from project root.

**SPEC SHAPE:** each selection function fully PINS Result() in both regimes -- Ensures(Implies(any_finite(ToSeq(seq)), Result()==first_finite_value(ToSeq(seq)))) and Ensures(Implies(not any_finite, len>0 and Result()==ToSeq(seq)[0])) -- plus Requires(MustTerminate(2)). So any value-wrong or nonterminating rival is provably rejected. The A-legs are the only trust surface; concentrated there.

ATTACKS (all edit ONLY the impl region; axioms/@Pure/Requires/Ensures byte-identical; same-spec CONFIRMED for all 6 via `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-24149 <f>` -> SAME):
- atk_1.py (prepatch bug): x0 impl = `rep = first_finite(ToSeq(seq)); return rep` (no fallback). weakness -> exit 2 NOT-A-COUNTEREXAMPLE. Direct verify error: "The precondition of function first_finite might not hold. Assertion any_finite(s) might not hold." => PREPATCH REPRODUCED (the missing except-StopIteration / all-non-finite crash).
- atk_2.py (control-flow-effect / nonterm, atk_4/atk_7 lineage): correct value computed then `while True: Invariant(True)`. weakness -> exit 2. Direct verify: `Type error: dead.code (@145.0)` -- a front-end translation refusal, so NOT JUDGED: the spec never ruled on this program and it counts in neither tally; the shape is unexpressible in nagini's fragment, so this file did not test the method-level MustTerminate, and whether that clause rejects a translatable diverging rival is a separate question atk_2 does not settle.
- atk_3.py (swapped selectors): under any_finite return first_unconditional, else first_finite. weakness -> exit 2. Error: "Postcondition ... Result()==first_finite_value(ToSeq(seq)) might not hold."
- atk_4.py (ungrounded-oracle echo, the directive-8 hole): `rep = 1`. weakness -> exit 2. Error: postcond(1) Result()==first_finite_value fails -- identity is pinned, a finite constant no longer discharges.
- atk_5.py (partial-domain / ignore guard): always `first_unconditional(ToSeq(seq))`. weakness -> exit 2. Error: postcond(1) fails (wrong on leading-non-finite-then-finite, e.g. [0,1]).
- atk_6.py (second nonterm shape / boundary): correct value then `i=0; while i>=0: Invariant(i>=0); i=i+1`. weakness -> exit 2. Error: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." (MustTerminate).

**Exit codes:** every `adversary weakness nagini ...` returned exit 2 (NOT-A-COUNTEREXAMPLE: shares spec but does NOT verify). NO attack came back a CANDIDATE, so NO faithful-patch materialization / run_resolve run was triggered (that step fires only for a verifying wrong-impl). patches={} accordingly.

**POSITIVE CONTROL:** positive_control.py = verbatim model.py. `bash scripts/nagini_verify.sh` -> exit 0, "Verification successful" (15.38s).

REFINEMENT.MD AUDIT (kind check + A-leg correspondence): all legs A1-A6/B1-B6 are R (A1/B1 finiteness-flag abstraction; A5/B5 return-value flow), A-reference+R (A2/B2 deep any_finite <-> StopIteration domain), A-consumed (A3/B3 first_finite<->cbook.`_safe_first_finite`; A4/B4 first_unconditional<->cbook.safe_first_element), or I (A5/B5 totality, A6/B6 MustTerminate<->bounded loop-free code). NO kind-3 leg. Plus A-reference deep model first_finite_value pins value/identity. The A-legs' correspondence to the real callees is executably validated by axiom_check.py (G-AX, meta exit 0): imports real matplotlib.cbook, materializes distinct finite floats + NaN over 11 boundary + 20000 fuzz patterns, asserts `_safe_first_finite` returns the value at the first-finite index (identity, not just finiteness) and safe_first_element returns element[0] -- byte-matching the axiom Ensures. base_commit-mode probe confirms `_safe_first_finite` raises StopIteration on all-non-finite (negation of any_finite) => Requires(any_finite) is the weakest sound guard, and witnesses the exact regression.

**CONCLUSION:** The spec admits no verifying wrong impl across prepatch-bug, nonterm(x2), swap, constant-echo, and ignore-guard rivals; the fully-pinned postconditions + MustTerminate discharge each. No verify-but-doesn't-resolve counterexample exists. verify=>correct holds. Verdict SOUND (>=5 distinct attacks run, none breaks; positive control verifies; no resolve run needed since no candidate).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24149.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A width-conversion helper picks one representative coordinate out of a
  non-empty sequence of coordinate values, used to anchor a unit-aware width
  addition. Each value is either finite or non-finite (a not-a-number /
  missing value). The representative is chosen as follows, and the choice must
  always succeed for a non-empty sequence:

    (1) If the sequence contains at least one finite value, the representative
        is the FIRST finite value (so a leading non-finite value is skipped in
        favour of a real coordinate). The representative is therefore finite.

    (2) If the sequence contains NO finite value at all (every value is
        non-finite), the representative is the FIRST value of the sequence
        unconditionally. The selection must still return a value in this case
        — an all-non-finite sequence yields a (non-finite) representative
        rather than failing — so that drawing an artifact whose coordinates
        are entirely non-finite remains a defined, total operation.

  The two coordinate sources fed to this helper (the original positions and
  their unit-converted form) are each selected by this same rule.

  Selection is a bounded, loop-free choice between two selectors: it MUST
  actually deliver the representative to its caller (total correctness,
  carried as a MustTerminate obligation in the preconditions). An
  implementation that diverges before returning would satisfy the value
  postconditions only vacuously and would never anchor the width addition.

A coordinate sequence is modelled as ``List[int]`` of per-element finiteness
flags (0 == the element is non-finite; non-zero == the element is finite). The
unchanged "first finite element" and "first element unconditionally" selectors
are axiomatized callees over ``PSeq[int]`` (their provenance + executable
soundness check live in mapping.md / axiom_check.py); the "is there any finite
element" predicate driving the choice is spelled out deeply as a front-recursive
fold (``any_finite``). The selection functions return the chosen flag.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def first_finite(s: PSeq[int]) -> int:
    """First finite element selector (unchanged community callee), restricted
    to the flag carrier. It returns a value only when a finite element exists;
    on a sequence with no finite element it does not return normally (the
    caller must guard that case). Weakest contract the proof needs: under the
    "some element is finite" precondition the returned value is THE first finite
    element of the sequence (which is therefore itself finite, i.e. non-zero) —
    the identity of the selected element, not merely the fact that it is finite.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(any_finite(s))
    Ensures(Result() == first_finite_value(s))


@Pure
@ContractOnly
def first_unconditional(s: PSeq[int]) -> int:
    """First element selector (unchanged community callee), restricted to the
    flag carrier. It returns the first element of a non-empty sequence
    unconditionally, regardless of finiteness. Weakest contract the proof needs:
    the returned flag equals the first element's flag.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(s) > 0)
    Ensures(Result() == s[0])
# axioms-end


# pure-start
@Pure
def any_finite(s: PSeq[int]) -> bool:
    """Whether the sequence contains at least one finite element (a flag that
    is non-zero). The empty sequence contains none (`False`). Front-recursive so
    one unfold is available to callers."""
    if len(s) == 0:
        return False
    return (s[0] != 0) or any_finite(s.drop(1))


@Pure
def first_finite_value(s: PSeq[int]) -> int:
    """The first finite element of the sequence — the leftmost element whose
    flag is non-zero — when one exists. Front-recursive over the input carrier
    (one unfold per leading non-finite element), so it is a structural function
    of the sequence itself, not an opaque oracle: it skips leading non-finite
    flags and yields the first finite one. Used to PIN the selected
    representative to the actual chosen element of the input (not merely to its
    finiteness)."""
    Requires(any_finite(s))
    if s[0] != 0:
        return s[0]
    return first_finite_value(s.drop(1))
# pure-end


def select_position_x0(seq: List[int]) -> int:
    """Pick the representative of the original-position coordinate sequence:
    the first finite value, or — when no value is finite — the first value
    unconditionally."""
    # pre-conditions-start
    Requires(Acc(list_pred(seq), 1 / 2))
    Requires(len(seq) > 0)
    # TERMINATION: the selection is a bounded, loop-free choice between the
    # two selectors and MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body (e.g. an endless loop
    # before the return) satisfies the value postconditions only vacuously
    # yet never delivers the representative to the caller; the desired
    # selection always returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seq), 1 / 2))
    # (1) when some value is finite, the representative is THE first finite
    #     value of the input — the actual selected element (identity), not just
    #     its finiteness. A constant of the asserted property (any finite flag)
    #     no longer discharges this: it must equal the input's own first finite
    #     element, which only the selector applied to the input produces.
    Ensures(Implies(any_finite(ToSeq(seq)),
                    Result() == first_finite_value(ToSeq(seq))))
    # (2) when NO value is finite, the selection still returns a value: the
    #     first element unconditionally (which is itself non-finite). This is
    #     the total-selection guarantee the all-non-finite input demands.
    Ensures(len(ToSeq(seq)) == len(seq))
    Ensures(Implies(not any_finite(ToSeq(seq)),
                    len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
    # post-conditions-end
    # impl-start
    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep
    # impl-end


def select_position_xconv(seq: List[int]) -> int:
    """Pick the representative of the unit-converted coordinate sequence by the
    same rule: the first finite value, or — when no value is finite — the first
    value unconditionally."""
    # pre-conditions-start
    Requires(Acc(list_pred(seq), 1 / 2))
    Requires(len(seq) > 0)
    # TERMINATION: the selection is a bounded, loop-free choice between the
    # two selectors and MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body (e.g. an endless loop
    # before the return) satisfies the value postconditions only vacuously
    # yet never delivers the representative to the caller; the desired
    # selection always returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seq), 1 / 2))
    # (1) when some value is finite, the representative is THE first finite
    #     value of the input — the actual selected element (identity), not just
    #     its finiteness. A constant of the asserted property (any finite flag)
    #     no longer discharges this: it must equal the input's own first finite
    #     element, which only the selector applied to the input produces.
    Ensures(Implies(any_finite(ToSeq(seq)),
                    Result() == first_finite_value(ToSeq(seq))))
    # (2) when NO value is finite, the selection still returns a value: the
    #     first element unconditionally (which is itself non-finite).
    Ensures(len(ToSeq(seq)) == len(seq))
    Ensures(Implies(not any_finite(ToSeq(seq)),
                    len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))
    # post-conditions-end
    # impl-start
    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit of matplotlib__matplotlib-24149 (nagini). env SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=$PWD/benchmark-verified. All commands run from project root.

**SPEC SHAPE:** each selection function fully PINS Result() in both regimes -- Ensures(Implies(any_finite(ToSeq(seq)), Result()==first_finite_value(ToSeq(seq)))) and Ensures(Implies(not any_finite, len>0 and Result()==ToSeq(seq)[0])) -- plus Requires(MustTerminate(2)). So any value-wrong or nonterminating rival is provably rejected. The A-legs are the only trust surface; concentrated there.

ATTACKS (all edit ONLY the impl region; axioms/@Pure/Requires/Ensures byte-identical; same-spec CONFIRMED for all 6 via `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-24149 <f>` -> SAME):
- atk_1.py (prepatch bug): x0 impl = `rep = first_finite(ToSeq(seq)); return rep` (no fallback). weakness -> exit 2 NOT-A-COUNTEREXAMPLE. Direct verify error: "The precondition of function first_finite might not hold. Assertion any_finite(s) might not hold." => PREPATCH REPRODUCED (the missing except-StopIteration / all-non-finite crash).
- atk_2.py (control-flow-effect / nonterm, atk_4/atk_7 lineage): correct value computed then `while True: Invariant(True)`. weakness -> exit 2. Direct verify: `Type error: dead.code (@145.0)` -- a front-end translation refusal, so NOT JUDGED: the spec never ruled on this program and it counts in neither tally; the shape is unexpressible in nagini's fragment, so this file did not test the method-level MustTerminate, and whether that clause rejects a translatable diverging rival is a separate question atk_2 does not settle.
- atk_3.py (swapped selectors): under any_finite return first_unconditional, else first_finite. weakness -> exit 2. Error: "Postcondition ... Result()==first_finite_value(ToSeq(seq)) might not hold."
- atk_4.py (ungrounded-oracle echo, the directive-8 hole): `rep = 1`. weakness -> exit 2. Error: postcond(1) Result()==first_finite_value fails -- identity is pinned, a finite constant no longer discharges.
- atk_5.py (partial-domain / ignore guard): always `first_unconditional(ToSeq(seq))`. weakness -> exit 2. Error: postcond(1) fails (wrong on leading-non-finite-then-finite, e.g. [0,1]).
- atk_6.py (second nonterm shape / boundary): correct value then `i=0; while i>=0: Invariant(i>=0); i=i+1`. weakness -> exit 2. Error: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." (MustTerminate).

**Exit codes:** every `adversary weakness nagini ...` returned exit 2 (NOT-A-COUNTEREXAMPLE: shares spec but does NOT verify). NO attack came back a CANDIDATE, so NO faithful-patch materialization / run_resolve run was triggered (that step fires only for a verifying wrong-impl). patches={} accordingly.

**POSITIVE CONTROL:** positive_control.py = verbatim model.py. `bash scripts/nagini_verify.sh` -> exit 0, "Verification successful" (15.38s).

REFINEMENT.MD AUDIT (kind check + A-leg correspondence): all legs A1-A6/B1-B6 are R (A1/B1 finiteness-flag abstraction; A5/B5 return-value flow), A-reference+R (A2/B2 deep any_finite <-> StopIteration domain), A-consumed (A3/B3 first_finite<->cbook.`_safe_first_finite`; A4/B4 first_unconditional<->cbook.safe_first_element), or I (A5/B5 totality, A6/B6 MustTerminate<->bounded loop-free code). NO kind-3 leg. Plus A-reference deep model first_finite_value pins value/identity. The A-legs' correspondence to the real callees is executably validated by axiom_check.py (G-AX, meta exit 0): imports real matplotlib.cbook, materializes distinct finite floats + NaN over 11 boundary + 20000 fuzz patterns, asserts `_safe_first_finite` returns the value at the first-finite index (identity, not just finiteness) and safe_first_element returns element[0] -- byte-matching the axiom Ensures. base_commit-mode probe confirms `_safe_first_finite` raises StopIteration on all-non-finite (negation of any_finite) => Requires(any_finite) is the weakest sound guard, and witnesses the exact regression.

**CONCLUSION:** The spec admits no verifying wrong impl across prepatch-bug, nonterm(x2), swap, constant-echo, and ignore-guard rivals; the fully-pinned postconditions + MustTerminate discharge each. No verify-but-doesn't-resolve counterexample exists. verify=>correct holds. Verdict SOUND (>=5 distinct attacks run, none breaks; positive control verifies; no resolve run needed since no candidate).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness assessment (spec-too-strong / drift check) for matplotlib__matplotlib-24149 nagini bundle. The spec is NOT too strong; the modeled functions agree with the real repo callees on every input.

Real repo (patched `_convert_dx`, `_axes`.py:2181-2189, base_commit af39f1edff): for each of x0/xconv, `try: v=cbook._safe_first_finite(v); except StopIteration: v=cbook.safe_first_element(v)`. `_safe_first_finite` (list path) = next(val for val in obj if safe_isfinite(val)) -> first FINITE element, or raises StopIteration iff no element is finite. safe_first_element -> `_safe_first_finite`(skip_nonfinite=False) -> next(iter(obj)) = first element unconditionally. safe_isfinite: None->False, scalar->np.isfinite(val), non-scalar/TypeError->True.

Model (select_position_x0/xconv): if any_finite(seq): first_finite(seq) else first_unconditional(seq); post (1) any_finite => Result==first_finite_value(seq) (input's leftmost non-zero flag), (2) not any_finite => Result==seq[0]. Carrier: List[int] finiteness flags (flag!=0 <-> safe_isfinite true).

Input-class agreement:
- >=1 finite element: real returns first finite element == first_finite_value. MATCH.
- all non-finite (e.g. [nan], the F2P regression input, in-domain since len>0 and non-empty): real raises then falls back to safe_first_element == seq[0]; model returns seq[0]. MATCH.
- leading NaN then finite: real skips NaN, returns first finite; model post(1) pins first_finite_value. MATCH.
No diverging input found.

MustTerminate(2) is stronger than partial correctness but is FAITHFUL: the real gold patch (bounded try/except over a finite-sequence generator step) always returns, so the real callee satisfies the obligation; it rejects only diverging rivals, not real behavior. Not drift.

**Evidence:** model.py verifies (nagini_verify.sh, 14.7s). same-spec identity check on model.py, model_prepatch.py, model_prepatch_2.py all = SAME (exact spec shared). axiom_check.py validates both A-consumed axioms (first_finite / first_unconditional) against the REAL matplotlib.cbook over 11 boundary + 20000 fuzz patterns, including identity-pinning (distinct finite floats) and the base_commit StopIteration domain == not any_finite. Postconditions are pinned to the input's actual first-finite element (first_finite_value fold), closing the ungrounded-marker hole; a constant-echo cannot discharge post(1). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the SOLVER-VISIBLE problem_statement only (not hints_text, which carries the actual gold diff). Mechanical G-LEAK screen passes ("spec view clean"), and semantic review confirms no over-disclosure.

**Gold edit:** adds `except StopIteration: x0 = cbook.safe_first_element(x0)` (and the xconv twin) to the two try-blocks in Axes.`_convert_dx` — i.e. when `_safe_first_finite` finds no finite element, fall back to the first element unconditionally.

What the PUBLIC problem_statement already reveals: (a) the crash is a StopIteration inside Axes.`_convert_dx`(dx, x0, xconv, convert) -> cbook.`_safe_first_finite` -> `next(val for val in obj if safe_isfinite(val))`; (b) the Expected outcome: ax.bar([np.nan],[np.nan]) should return a BarCollection with one Rectangle having nan for x (i.e. the selection must still yield a non-finite value rather than crash); (c) the variable names x0/xconv (traceback literally shows `_convert_dx`(dx, x0, xconv, convert)).

The spec view expresses exactly this desired behavior abstractly and totally: (1) if any finite value -> first finite; (2) else -> first value unconditionally, as a defined/total operation. This is the natural behavioral spec directly derivable from the public expected-outcome, not a disclosure of the edit mechanism.

No gold-diff artifact appears in the spec view: scanned and found ZERO occurrences of StopIteration, except, try, cbook, safe_first_element, `_safe_first_finite`, `_convert_dx`/convert_dx, `_axes`, safe_isfinite, bar. No diff markers, no patched file path, no narration terms (bug/fix/regression/etc.). Callees are abstracted (first_finite, first_unconditional, any_finite, first_finite_value) — no spec-view identifier embeds the only distinctive patched symbol (convert_dx). All docstrings describe behavior, not the edit.

Everything the spec exposes is either already public via problem_statement or an abstract behavioral restatement of the public expected outcome. relaxed_leakage flag absent; no RELAXED_LEAKAGE.md — pure NO-LEAKAGE, no deferral needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
