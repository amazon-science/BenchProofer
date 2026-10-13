# P2 adversarial audit — django__django-11749

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -105,12 +103,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(actions))
         Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         a = actions[i - 1]
         Assert(ToSeq(actions).drop(i - 1)[0] == a)
         Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
-        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
+        if mandatory(a) and supplied(a):
             result = [a] + result
         i = i - 1
     return result
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -105,12 +103,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(actions))
         Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         a = actions[i - 1]
         Assert(ToSeq(actions).drop(i - 1)[0] == a)
         Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
-        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
+        if supplied(a):
             result = [a] + result
         i = i - 1
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -99,13 +97,12 @@
     # impl-start
     result = []  # type: List[int]
     i = len(actions)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(actions), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(actions))
         Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         a = actions[i - 1]
         Assert(ToSeq(actions).drop(i - 1)[0] == a)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -105,12 +103,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(actions))
         Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         a = actions[i - 1]
         Assert(ToSeq(actions).drop(i - 1)[0] == a)
         Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
-        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
+        if supplied(a) and (mandatory(a) and in_mandated_set(a)):
             result = [a] + result
         i = i - 1
     return result
```

Attack 5 — `atk_6.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -98,20 +96,11 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(actions)
-    while i > 0:
+    while True:
         # invariants-start
         Invariant(Acc(list_pred(actions), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(actions))
-        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        a = actions[i - 1]
-        Assert(ToSeq(actions).drop(i - 1)[0] == a)
-        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
-        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
-            result = [a] + result
-        i = i - 1
+        result = result
     return result
     # impl-end
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -105,13 +103,12 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(actions))
         Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         a = actions[i - 1]
         Assert(ToSeq(actions).drop(i - 1)[0] == a)
         Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
         if supplied(a) and (mandatory(a) or in_mandated_set(a)):
-            result = [a] + result
+            result = result + [a]
         i = i - 1
     return result
     # impl-end
```

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -104,12 +102,10 @@
         Invariant(Acc(list_pred(actions), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(actions))
+        Invariant(0 > 1)
         Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         a = actions[i - 1]
-        Assert(ToSeq(actions).drop(i - 1)[0] == a)
-        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
         if supplied(a) and (mandatory(a) or in_mandated_set(a)):
             result = [a] + result
         i = i - 1
```

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -105,12 +103,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(actions))
         Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         a = actions[i - 1]
         Assert(ToSeq(actions).drop(i - 1)[0] == a)
         Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
-        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
+        if supplied(a) and in_mandated_set(a):
             result = [a] + result
         i = i - 1
     return result
```

Attack 9 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -105,9 +103,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(actions))
         Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         a = actions[i - 1]
+        if a >= 8:
+            i = i - 1
+            continue
         Assert(ToSeq(actions).drop(i - 1)[0] == a)
         Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
         if supplied(a) and (mandatory(a) or in_mandated_set(a)):
```

Attack 10 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,7 +86,6 @@
 def select_forwarded(actions: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(actions), 1 / 2))
-    Requires(MustTerminate(len(actions) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(actions), 1 / 2))
@@ -97,21 +95,5 @@
     Ensures(ToSeq(Result()) == forwarded_seq(ToSeq(actions)))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    i = len(actions)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(actions), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(actions))
-        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        a = actions[i - 1]
-        Assert(ToSeq(actions).drop(i - 1)[0] == a)
-        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
-        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
-            result = [a] + result
-        i = i - 1
-    return result
+    return actions
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11749.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Before a command's option defaults are computed, the caller-supplied keyword
  options must be threaded through the option parser for every option whose
  presence the parser would otherwise INSIST on. An option's value, when the
  caller supplied it, is forwarded to the parser exactly when that option is
  one the parser obliges the caller to provide. An option is obliged when it
  is individually mandatory OR when it belongs to a set of alternatives of
  which the parser mandates that at least one be supplied. Forwarding preserves
  the parser's declaration order, and an option whose value the caller did not
  supply is never forwarded.

  Concretely: the forwarded sequence is the order-preserving sub-list of the
  declared options for which (the caller supplied this option) AND (the option
  is itself mandatory OR it is a member of a mandated set of alternatives).
  An option that is a member of a mandated alternative set but is not itself
  individually mandatory is still forwarded; the previous omission of such
  options is exactly the gap this contract closes.

Each declared option is modelled by an integer carrying three independent
boolean facts as separate low bits (Nagini bans richer object graphs in a
sequence): whether the caller supplied this option (`supplied`), whether the
option is individually mandatory (`mandatory`), and whether the option belongs
to a mandated set of alternatives (`in_mandated_set`). The forwarded result is
the order-preserving filter of the declared options under the forwarding
predicate, carried as `PSeq[int]` (the per-option formatted argument string is
the same on both sides of the change, so each forwarded option corresponds to
exactly one forwarded argument; only membership of the forwarded set changed).

No callee is axiomatized: the change is pure selection logic over the declared
options, modelled deeply. Markers (machine-parsed) delimit the spec / proof /
impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# axioms-end

# pure-start
@Pure
def supplied(a: int) -> bool:
    """The caller supplied a value for this option (its destination is present
    among the caller-supplied keyword options)."""
    return a % 2 == 1

@Pure
def mandatory(a: int) -> bool:
    """The option is individually mandatory."""
    return (a // 2) % 2 == 1

@Pure
def in_mandated_set(a: int) -> bool:
    """The option belongs to a set of alternatives of which at least one is
    mandated to be supplied."""
    return (a // 4) % 2 == 1

@Pure
def forward(a: int) -> bool:
    """An option's caller-supplied value is forwarded to the parser exactly when
    the caller supplied it AND it is obliged: either individually mandatory, or
    a member of a mandated set of alternatives."""
    return supplied(a) and (mandatory(a) or in_mandated_set(a))

@Pure
def forwarded_seq(s: PSeq[int]) -> PSeq[int]:
    """The forwarded options: the order-preserving sub-list of the declared
    options that satisfy `forward`. Front-recursive so a single unfold is
    available per declared option."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if forward(s[0]):
        return PSeq(s[0]) + forwarded_seq(s.drop(1))
    return forwarded_seq(s.drop(1))
# pure-end

def select_forwarded(actions: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(actions), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(actions), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The forwarded options are exactly the order-preserving filter of the
    # declared options under the forwarding predicate.
    Ensures(ToSeq(Result()) == forwarded_seq(ToSeq(actions)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
            result = [a] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No hygiene-legal, same-spec, Nagini-VERIFYING impl of the frozen spec exists whose faithful refined patch fails to resolve. 10 distinct hygiene-clean same-spec wrong impls were run through `adversary weakness nagini django__django-11749`; ALL were rejected by the verifier (exit 2, 'attack does not verify — spec rejected'). Positive control verifies (exit 0, 12.8s); gold patch resolves (executed, resolved=True).

WHY THE SPEC IS TIGHT: the postcondition `Ensures(ToSeq(Result()) == forwarded_seq(ToSeq(actions)))` pins the output as a TOTAL, DETERMINISTIC pure function of the input. The @Pure model region (forward/forwarded_seq) is frozen spec (only the impl region is editable). There is no precondition restricting element values (all 8 bit-combinations + out-of-domain ints are in scope) and only Acc(...,1/2) read-only permission on `actions` — so there is no partial-domain slack and no mutation slack. Any editable impl that verifies must reproduce forwarded_seq exactly.

### ATTACKS RUN (all; command per file: `python -m swebench_unified.adversary weakness nagini django__django-11749 <file>`):
- atk_1.py PREPATCH BUG (mandatory & supplied only; drops in_mandated_set disjunct) -> exit 2 REJECTED (prepatch_reproduced: the exact model_prepatch.py predicate; spec senses the change, G-DIFF).
- atk_2.py over-forward (supplied only) -> exit 2 REJECTED.
- atk_3.py boundary off-by-one (while i>1, drops first declared option) -> exit 2 REJECTED.
- atk_4.py wrong predicate (mandatory AND in_mandated_set) -> exit 2 REJECTED.
- atk_6.py control-flow/non-termination (while True) -> exit 2, NOT JUDGED (Nagini: 'dead.code' — unreachable return): the front end refused to translate the program, so the verifier never ran and the spec never ruled on it; it counts in neither tally. All this establishes is that the attack shape is unexpressible in Nagini's fragment — this file did not exercise the spec's method-level MustTerminate, and whether that clause would reject a TRANSLATABLE diverging rival is a separate question it does not settle.
- atk_7.py control-flow-effect (reversed output order, result+[a]) -> exit 2 REJECTED.
- atk_8.py hygiene-clean ungrounded-oracle attempt (contradictory loop Invariant 0>1, no banned token) -> exit 2 REJECTED (invariant not established on entry; cannot fake vacuity without a banned token).
- atk_9.py in_mandated_set only (drop mandatory disjunct) -> exit 2 REJECTED.
- atk_10.py partial-domain (skip encodings a>=8) -> exit 2 REJECTED (spec domain is all ints; out-of-range still decoded by bit predicates).
- atk_11.py identity (return actions) -> exit 2 REJECTED.

ATK_5 (Assume(False)) — CANDIDATE but DISQUALIFIED, NOT a break, DELIBERATELY NOT LISTED IN attacks: `adversary weakness` reported CANDIDATE (shares spec AND verifies, 12.4s) because the weakness primitive checks only same_spec AND verifies and does NOT run G-HYGIENE. But `Assume(` is a BANNED TOKEN (backends/nagini.py: banned_tokens=('Assume(','Refute(')). Confirmed mechanically: gates.hygiene._run_python(atk_5) -> FAIL 'banned calls: [Assume]' (pos_control and atk_1 both PASS hygiene). An Assume(False) impl verifies VACUOUSLY against ANY spec, including a perfect one, and has no real-code counterpart, so no genuine faithful refinement leg exists — it is precisely the harness cheat the banned-token list exists to block, not a spec weakness.

Per protocol I still materialized its behavioral faithful patch (forward-nothing: `False and ...` in the comprehension predicate, atk_5_faithful.patch) and RAN it: `run_resolve('django__django-11749', <patch>)` -> completed=True, resolved=FALSE ('patch did not resolve'). So atk_5's patch does not resolve — but atk_5 is hygiene-ILLEGAL, so this does NOT prove verify⇏correct (accepting it would false-fail EVERY nagini bundle). CRITICAL: neither nagini_verify.sh nor _derive_audit_verdict screens banned tokens (only the separate G-HYGIENE gate does), so I intentionally EXCLUDE atk_5 from the submitted attacks list; listing it would make the runner record a spurious BROKEN.

HARNESS EVIDENCE (executed via docker, benchmark swe_bench_verified, retries=0): GOLD patch.diff -> resolved=True/completed=True (oracle sanity: correct patch resolves). ATK5_FAITHFUL forward-nothing patch -> resolved=False/completed=True (incorrect impl's patch does not resolve, as expected).

REFINEMENT.md AUDIT (task 3): legs A1-A6 are all R (type refinement) or I (identical) — NO kind-3 (unexpressible-changed-op) and NO kind-A/axiom legs. axioms region is empty (region_text=''), no @ContractOnly in model.py, and axiom_check.py correctly ABSENT (no G-AX obligation). §B/§3 justified: the one genuinely-changed op (forwarding predicate + the new `in_mandated_set` disjunct that closes the mutually-exclusive-required-group gap) is modeled DEEPLY in the frozen @Pure region (forward + order-preserving fold forwarded_seq), not hidden behind an axiom; the group scan folds into a single per-action boolean and the per-option formatted string is unchanged pre/post-patch.

A2/A3/A4 correspondence to the REAL argparse callees (opt.required, opt.dest in options, membership of a required mutually-exclusive group) is mechanically corroborated by conformance_check.py, which realizes each of the 3 bits through real argparse structures (required=True; add_mutually_exclusive_group(required=True); post-insertion required=True for the bit1&bit2 combo the public API forbids) and compares the contract-stripped impl vs the real patched call_command over 100,585+ inputs (585 boundary + 100000 fuzz, seed 11749). No A-reference/A-consumed leg to validate against a callee (there are none), so the A-leg audit reduces to confirming their absence — confirmed.

CONCLUSION: The falsification floor is met (10 >= 5 distinct hygiene-clean attacks, all rejected; prepatch bug reproduced and rejected; positive control verifies), no hygiene-legal verifying wrong impl exists, and the only 'candidate' is a banned-token vacuity cheat that G-HYGIENE rejects. verify ⇒ correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_11.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11749.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Before a command's option defaults are computed, the caller-supplied keyword
  options must be threaded through the option parser for every option whose
  presence the parser would otherwise INSIST on. An option's value, when the
  caller supplied it, is forwarded to the parser exactly when that option is
  one the parser obliges the caller to provide. An option is obliged when it
  is individually mandatory OR when it belongs to a set of alternatives of
  which the parser mandates that at least one be supplied. Forwarding preserves
  the parser's declaration order, and an option whose value the caller did not
  supply is never forwarded.

  Concretely: the forwarded sequence is the order-preserving sub-list of the
  declared options for which (the caller supplied this option) AND (the option
  is itself mandatory OR it is a member of a mandated set of alternatives).
  An option that is a member of a mandated alternative set but is not itself
  individually mandatory is still forwarded; the previous omission of such
  options is exactly the gap this contract closes.

Each declared option is modelled by an integer carrying three independent
boolean facts as separate low bits (Nagini bans richer object graphs in a
sequence): whether the caller supplied this option (`supplied`), whether the
option is individually mandatory (`mandatory`), and whether the option belongs
to a mandated set of alternatives (`in_mandated_set`). The forwarded result is
the order-preserving filter of the declared options under the forwarding
predicate, carried as `PSeq[int]` (the per-option formatted argument string is
the same on both sides of the change, so each forwarded option corresponds to
exactly one forwarded argument; only membership of the forwarded set changed).

No callee is axiomatized: the change is pure selection logic over the declared
options, modelled deeply. Markers (machine-parsed) delimit the spec / proof /
impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# axioms-end

# pure-start
@Pure
def supplied(a: int) -> bool:
    """The caller supplied a value for this option (its destination is present
    among the caller-supplied keyword options)."""
    return a % 2 == 1

@Pure
def mandatory(a: int) -> bool:
    """The option is individually mandatory."""
    return (a // 2) % 2 == 1

@Pure
def in_mandated_set(a: int) -> bool:
    """The option belongs to a set of alternatives of which at least one is
    mandated to be supplied."""
    return (a // 4) % 2 == 1

@Pure
def forward(a: int) -> bool:
    """An option's caller-supplied value is forwarded to the parser exactly when
    the caller supplied it AND it is obliged: either individually mandatory, or
    a member of a mandated set of alternatives."""
    return supplied(a) and (mandatory(a) or in_mandated_set(a))

@Pure
def forwarded_seq(s: PSeq[int]) -> PSeq[int]:
    """The forwarded options: the order-preserving sub-list of the declared
    options that satisfy `forward`. Front-recursive so a single unfold is
    available per declared option."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if forward(s[0]):
        return PSeq(s[0]) + forwarded_seq(s.drop(1))
    return forwarded_seq(s.drop(1))
# pure-end

def select_forwarded(actions: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(actions), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(actions), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The forwarded options are exactly the order-preserving filter of the
    # declared options under the forwarding predicate.
    Ensures(ToSeq(Result()) == forwarded_seq(ToSeq(actions)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
            result = [a] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No hygiene-legal, same-spec, Nagini-VERIFYING impl of the frozen spec exists whose faithful refined patch fails to resolve. 10 distinct hygiene-clean same-spec wrong impls were run through `adversary weakness nagini django__django-11749`; ALL were rejected by the verifier (exit 2, 'attack does not verify — spec rejected'). Positive control verifies (exit 0, 12.8s); gold patch resolves (executed, resolved=True).

WHY THE SPEC IS TIGHT: the postcondition `Ensures(ToSeq(Result()) == forwarded_seq(ToSeq(actions)))` pins the output as a TOTAL, DETERMINISTIC pure function of the input. The @Pure model region (forward/forwarded_seq) is frozen spec (only the impl region is editable). There is no precondition restricting element values (all 8 bit-combinations + out-of-domain ints are in scope) and only Acc(...,1/2) read-only permission on `actions` — so there is no partial-domain slack and no mutation slack. Any editable impl that verifies must reproduce forwarded_seq exactly.

### ATTACKS RUN (all; command per file: `python -m swebench_unified.adversary weakness nagini django__django-11749 <file>`):
- atk_1.py PREPATCH BUG (mandatory & supplied only; drops in_mandated_set disjunct) -> exit 2 REJECTED (prepatch_reproduced: the exact model_prepatch.py predicate; spec senses the change, G-DIFF).
- atk_2.py over-forward (supplied only) -> exit 2 REJECTED.
- atk_3.py boundary off-by-one (while i>1, drops first declared option) -> exit 2 REJECTED.
- atk_4.py wrong predicate (mandatory AND in_mandated_set) -> exit 2 REJECTED.
- atk_6.py control-flow/non-termination (while True) -> exit 2, NOT JUDGED (Nagini: 'dead.code' — unreachable return): the front end refused to translate the program, so the verifier never ran and the spec never ruled on it; it counts in neither tally. All this establishes is that the attack shape is unexpressible in Nagini's fragment — this file did not exercise the spec's method-level MustTerminate, and whether that clause would reject a TRANSLATABLE diverging rival is a separate question it does not settle.
- atk_7.py control-flow-effect (reversed output order, result+[a]) -> exit 2 REJECTED.
- atk_8.py hygiene-clean ungrounded-oracle attempt (contradictory loop Invariant 0>1, no banned token) -> exit 2 REJECTED (invariant not established on entry; cannot fake vacuity without a banned token).
- atk_9.py in_mandated_set only (drop mandatory disjunct) -> exit 2 REJECTED.
- atk_10.py partial-domain (skip encodings a>=8) -> exit 2 REJECTED (spec domain is all ints; out-of-range still decoded by bit predicates).
- atk_11.py identity (return actions) -> exit 2 REJECTED.

ATK_5 (Assume(False)) — CANDIDATE but DISQUALIFIED, NOT a break, DELIBERATELY NOT LISTED IN attacks: `adversary weakness` reported CANDIDATE (shares spec AND verifies, 12.4s) because the weakness primitive checks only same_spec AND verifies and does NOT run G-HYGIENE. But `Assume(` is a BANNED TOKEN (backends/nagini.py: banned_tokens=('Assume(','Refute(')). Confirmed mechanically: gates.hygiene._run_python(atk_5) -> FAIL 'banned calls: [Assume]' (pos_control and atk_1 both PASS hygiene). An Assume(False) impl verifies VACUOUSLY against ANY spec, including a perfect one, and has no real-code counterpart, so no genuine faithful refinement leg exists — it is precisely the harness cheat the banned-token list exists to block, not a spec weakness.

Per protocol I still materialized its behavioral faithful patch (forward-nothing: `False and ...` in the comprehension predicate, atk_5_faithful.patch) and RAN it: `run_resolve('django__django-11749', <patch>)` -> completed=True, resolved=FALSE ('patch did not resolve'). So atk_5's patch does not resolve — but atk_5 is hygiene-ILLEGAL, so this does NOT prove verify⇏correct (accepting it would false-fail EVERY nagini bundle). CRITICAL: neither nagini_verify.sh nor _derive_audit_verdict screens banned tokens (only the separate G-HYGIENE gate does), so I intentionally EXCLUDE atk_5 from the submitted attacks list; listing it would make the runner record a spurious BROKEN.

HARNESS EVIDENCE (executed via docker, benchmark swe_bench_verified, retries=0): GOLD patch.diff -> resolved=True/completed=True (oracle sanity: correct patch resolves). ATK5_FAITHFUL forward-nothing patch -> resolved=False/completed=True (incorrect impl's patch does not resolve, as expected).

REFINEMENT.md AUDIT (task 3): legs A1-A6 are all R (type refinement) or I (identical) — NO kind-3 (unexpressible-changed-op) and NO kind-A/axiom legs. axioms region is empty (region_text=''), no @ContractOnly in model.py, and axiom_check.py correctly ABSENT (no G-AX obligation). §B/§3 justified: the one genuinely-changed op (forwarding predicate + the new `in_mandated_set` disjunct that closes the mutually-exclusive-required-group gap) is modeled DEEPLY in the frozen @Pure region (forward + order-preserving fold forwarded_seq), not hidden behind an axiom; the group scan folds into a single per-action boolean and the per-option formatted string is unchanged pre/post-patch.

A2/A3/A4 correspondence to the REAL argparse callees (opt.required, opt.dest in options, membership of a required mutually-exclusive group) is mechanically corroborated by conformance_check.py, which realizes each of the 3 bits through real argparse structures (required=True; add_mutually_exclusive_group(required=True); post-insertion required=True for the bit1&bit2 combo the public API forbids) and compares the contract-stripped impl vs the real patched call_command over 100,585+ inputs (585 boundary + 100000 fuzz, seed 11749). No A-reference/A-consumed leg to validate against a callee (there are none), so the A-leg audit reduces to confirming their absence — confirmed.

CONCLUSION: The falsification floor is met (10 >= 5 distinct hygiene-clean attacks, all rejected; prepatch bug reproduced and rejected; positive control verifies), no hygiene-legal verifying wrong impl exists, and the only 'candidate' is a banned-token vacuity cheat that G-HYGIENE rejects. verify ⇒ correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) audit of nagini bundle django__django-11749. The modeled function select_forwarded's spec agrees with the real callee on every input; no diverging input exists.

Real callee (worktree at base_commit 350123f38c with gold patch applied), django/core/management/__init__.py, the parse_args += comprehension:
  '{}={}'.format(min(opt.option_strings), arg_options[opt.dest])
  for opt in parser_actions if (opt.dest in options and (opt.required or opt in mutually_exclusive_required_options))
where mutually_exclusive_required_options = {opt for group in parser._mutually_exclusive_groups for opt in group._group_actions if group.required}.

Model: forward(a) = supplied(a) and (mandatory(a) or in_mandated_set(a)); forwarded_seq is the order-preserving filter under forward. Bit encoding is a faithful 1:1 abstraction: bit0=supplied ↔ (opt.dest in options); bit1=mandatory ↔ opt.required; bit2=in_mandated_set ↔ (opt in mutually_exclusive_required_options). These are the only three per-action facts the real predicate reads, they are independent (all 8 combos reachable), and the per-option formatted string is identical pre/post-patch so membership+order is the only observable — exactly what forwarded_seq pins. The predicate boolean structure (and of supplied with or of the two obligation bits, short-circuit-irrelevant pure logic) is identical to the real one.

Checks performed:
- nagini_verify.sh model.py => Verification successful (11.14s).
- same-spec self-check on model.py => SAME (spec region byte-identical / intact).
- model_prepatch.py (weaker impl: mandatory(a) and supplied(a), matching the PRE-patch predicate opt.required and opt.dest in options) => Verification FAILED on the loop invariant. So the spec is NOT too strong in the drift sense but is exactly strong enough to sense the gold change (rejects the pre-patch behavior on supplied ∧ in_mandated_set ∧ ¬mandatory — the F2P config test_mutually_exclusive_group_required_options).
- Confirmed the worktree carries the gold post-patch predicate matching mapping.md/refinement.md.

The spec neither over-constrains (it demands exactly the post-patch filter) nor drifts from repo behavior. No @ContractOnly axiom to worry about. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK (leakage/gold-reconstruction) judged against the PUBLIC problem_statement only.

Mechanical screen: leakage.screen(model.py, nagini, gold_patch, problem_statement) → PASSED (no hard failures, no warnings). Confirmed spec_view is the docstring + imports + @Pure model (supplied/mandatory/in_mandated_set/forward/forwarded_seq) + select_forwarded signature/contracts; impl region is elided.

Manual review of the spec view:
- No diff markers (@@, diff --git, +++, index) present.
- No patched file path (django/core/management/__init__.py) or dotted module path in view.
- No patched repo symbols named: call_command, parse_args, parser_actions, _mutually_exclusive_groups, _group_actions, get_actions, arg_options, option_strings — none appear. Spec-view identifiers (supplied, mandatory, in_mandated_set, forward, forwarded_seq, select_forwarded, PSeq, actions) are all abstract model names, not repo symbols.
- No reproduced gold-patch line (e.g. the comprehension predicate or the set-comprehension) appears in the view.
- No bug/fix narration keywords (bug/fix/patch/previously/incorrectly/regression). The phrase 'the previous omission of such options is exactly the gap this contract closes' is behavioral framing, not edit narration, and contains no _NARRATION token.

Beyond-problem_statement check: the public problem_statement is a full bug report that already (a) quotes the buggy predicate `for opt in parser._actions if opt.required and opt.dest in options`, (b) states the desired fix — that arguments belonging to a `required=True` mutually-exclusive group must be forwarded even though each member is individually `required=False`, and (c) shows the exact group setup (`add_mutually_exclusive_group(required=True)`). The spec view expresses precisely this behavior in abstracted terms ('mandated set of alternatives', 'obliged', 'individually mandatory'), revealing nothing about the edit that the problem_statement does not already make public. The gold edit cannot be reconstructed from the spec view beyond what the task already discloses.

Conclusion: no line of the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.