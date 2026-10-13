# P2 adversarial audit — django__django-13670

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -52,7 +51,6 @@
     # pre-conditions-start
     # Calendar years handled by the renderer are positive (datetime: 1..9999).
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -68,7 +66,16 @@
     Ensures(Result()[1] == units_digit(year % 100))
     # post-conditions-end
     # impl-start
-    v = year % 100
-    result = [tens_digit(v), units_digit(v)]  # type: List[int]
+    # Render the full decimal expansion of the year (its 1..4 digits, most
+    # significant first) and keep every character from the third onward.
+    digits = []  # type: List[int]
+    if year >= 1000:
+        digits = digits + [48 + (year // 1000) % 10]
+    if year >= 100:
+        digits = digits + [48 + (year // 100) % 10]
+    if year >= 10:
+        digits = digits + [48 + (year // 10) % 10]
+    digits = digits + [48 + year % 10]
+    result = digits[2:]  # type: List[int]
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -52,7 +51,6 @@
     # pre-conditions-start
     # Calendar years handled by the renderer are positive (datetime: 1..9999).
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -69,6 +67,6 @@
     # post-conditions-end
     # impl-start
     v = year % 100
-    result = [tens_digit(v), units_digit(v)]  # type: List[int]
+    result = [units_digit(v), tens_digit(v)]  # type: List[int]
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -52,7 +51,6 @@
     # pre-conditions-start
     # Calendar years handled by the renderer are positive (datetime: 1..9999).
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -68,7 +66,7 @@
     Ensures(Result()[1] == units_digit(year % 100))
     # post-conditions-end
     # impl-start
-    v = year % 100
+    v = (year + 1) % 100
     result = [tens_digit(v), units_digit(v)]  # type: List[int]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -52,7 +51,6 @@
     # pre-conditions-start
     # Calendar years handled by the renderer are positive (datetime: 1..9999).
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -68,7 +66,11 @@
     Ensures(Result()[1] == units_digit(year % 100))
     # post-conditions-end
     # impl-start
-    v = year % 100
-    result = [tens_digit(v), units_digit(v)]  # type: List[int]
-    return result
+    if year < 1000:
+        v = year % 100
+        result = [tens_digit(v), units_digit(v)]  # type: List[int]
+        return result
+    w = (year // 100) % 100
+    result2 = [tens_digit(w), units_digit(w)]  # type: List[int]
+    return result2
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -52,7 +51,6 @@
     # pre-conditions-start
     # Calendar years handled by the renderer are positive (datetime: 1..9999).
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -69,6 +67,9 @@
     # post-conditions-end
     # impl-start
     v = year % 100
+    if v < 10:
+        small = [units_digit(v)]  # type: List[int]
+        return small
     result = [tens_digit(v), units_digit(v)]  # type: List[int]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -21,7 +21,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -52,7 +51,6 @@
     # pre-conditions-start
     # Calendar years handled by the renderer are positive (datetime: 1..9999).
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -68,7 +66,6 @@
     Ensures(Result()[1] == units_digit(year % 100))
     # post-conditions-end
     # impl-start
-    v = year % 100
-    result = [tens_digit(v), units_digit(v)]  # type: List[int]
+    result = [48, 48]  # type: List[int]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13670.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The abbreviated-year rendering takes a calendar year and produces its two
  least-significant decimal digits as a fixed-width, two-character string, with
  a leading zero supplied whenever the value is below ten. Concretely, writing
  ``v`` for the year reduced modulo one hundred (so ``0 <= v <= 99``), the
  result is exactly two characters: the tens digit ``v // 10`` followed by the
  units digit ``v % 10``, each rendered as its decimal-digit character. The
  output therefore always has length two regardless of the magnitude of the
  year — a year such as four renders as ``04`` and a year such as forty-two
  renders as ``42`` — matching the conventional two-digit abbreviation.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); ``ord('0') == 48``. The calendar year is an ``int``. No
library callee is involved — the rendering is pure integer arithmetic and
digit emission, so it is modelled deeply and no operation is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (no library callee is invoked; the rendering is modelled deeply, so there is
# no @ContractOnly axiom.)
# axioms-end

# pure-start
@Pure
def tens_digit(v: int) -> int:
    """Code point of the tens digit of a value in 0..99."""
    Requires(0 <= v and v <= 99)
    Ensures(Result() == 48 + (v // 10))
    return 48 + (v // 10)

@Pure
def units_digit(v: int) -> int:
    """Code point of the units digit of a value in 0..99."""
    Requires(0 <= v and v <= 99)
    Ensures(Result() == 48 + (v % 10))
    return 48 + (v % 10)
# pure-end

def abbreviated_year(year: int) -> List[int]:
    # pre-conditions-start
    # Calendar years handled by the renderer are positive (datetime: 1..9999).
    Requires(1 <= year and year <= 9999)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The rendering is always exactly two characters wide.
    Ensures(len(Result()) == 2)
    # Both characters are decimal-digit code points (0x30..0x39).
    Ensures(48 <= Result()[0] and Result()[0] <= 57)
    Ensures(48 <= Result()[1] and Result()[1] <= 57)
    # The two characters are the tens then units digit of the year reduced
    # modulo one hundred — so a leading zero is emitted below ten, and the
    # value is grounded entirely in the input year's arithmetic.
    Ensures(Result()[0] == tens_digit(year % 100))
    Ensures(Result()[1] == units_digit(year % 100))
    # post-conditions-end
    # impl-start
    v = year % 100
    result = [tens_digit(v), units_digit(v)]  # type: List[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle: django__django-13670 nagini; project root (env python, SBU_BENCHMARK_DIR=benchmark-verified).

SPEC SHAPE (why hard to break): abbreviated_year's postcondition FULLY PINS the output element-wise for every admitted input — len(Result())==2, Result()[0]==tens_digit(year%100), Result()[1]==units_digit(year%100), plus 0x30..0x39 digit ranges; the @Pure helpers tens_digit/units_digit are themselves pinned by Ensures. This leaves ZERO behavioural freedom, so any behaviourally-wrong impl cannot verify.

7 same-spec attacks built by editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; adversary same-spec = exit 0 SAME for all 7). Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-13670 atk_N.py`.
- atk_1.py PREPATCH bug (deep str(year)[2:] slice, from model_prepatch.py): same-spec, does NOT verify (verification failed) — spec senses the change (G-DIFF). prepatch reproduced.
- atk_2.py swap tens/units digits: same-spec, does NOT verify.
- atk_3.py boundary off-by-one ((year+1)%100): same-spec, does NOT verify.
- atk_4.py partial-domain (correct for year<1000, uses (year//100)%100 for year>=1000): same-spec, does NOT verify.
- atk_5.py control-flow-effect (drops leading zero for v<10, returns 1-char list): same-spec, does NOT verify (violates len==2 / element pin).
- atk_6.py ungrounded-oracle echo (hardcoded [48,48] == '00'): same-spec, does NOT verify (violates element pin for year%100 != 0).
- POSITIVE CONTROL positive_control.py (gold impl, verbatim model.py): same-spec AND verifies (11.5s). Gold patch.diff run through official run_resolve => completed=True, resolved=True (infra sanity + verify⇒correct confirmed).

atk_7.py (Assume(False) vacuous verify) EXCLUDED FROM SUBMITTED ATTACKS AS A NON-COUNTEREXAMPLE: it came back CANDIDATE (weakness exit 0: shares spec AND verifies, 12.3s) and I materialized its faithful patch (impl semantically returns '00' since Assume is proof-only) and RAN it through the official harness (run_resolve) => completed=True, resolved=False (consistent across 3 attempts). Literally that is the BROKEN trigger, BUT it verifies ONLY because Assume(False) poisons the verification path. `Assume(` is a BANNED TOKEN in the nagini backend (src/swebench_unified/backends/nagini.py banned_tokens=('Assume(','Refute(')), independently rejected by G-HYGIENE (confirmed via gates.hygiene._banned_calls => {'Assume'}).

It has no repo/runtime semantics and would vacuously verify against ANY postcondition — i.e. it would 'break' EVERY nagini bundle in existence. That is verifier unsoundness, not a weakness of THIS spec. The runner's check_attack does not apply the hygiene screen, so submitting atk_7 would manufacture a spurious universal BROKEN (a false positive). I deliberately do not submit it. All artifacts retained: atk_7.py, patch_atk_7.diff, resolve_atk7.txt, patch_gold.diff, resolve_gold.txt.

A-LEG / deep-model audit (the focus): refinement.md has 5 legs — #1 R (self.data.year<->int year, range 1..9999), #2 I (year%100 modulo), #3 A-reference (tens_digit == tens position of '%02d'%v), #4 A-reference (units_digit == units position), #5 R (str<->List[int] code points, width 2). NO kind-3 step and NO A-consumed axiom: the one changed op (two-digit decimal rendering) is modeled DEEPLY, not axiomatized. G-AX axiom_check.py run => exit 0: 'deep model == real "%02d"%(year%100) on all 9999 years (1..9999); width 2 + digit code points; old str(year)[2:] differs on 999 years (incl. all sub-100).' The A-reference correspondence to the real callee expression thus holds EXHAUSTIVELY over the admitted domain. mapping.md callee provenance = None (language %-formatting, deep model) — consistent.

Conclusion: every legitimate same-spec wrong impl (6/6) is rejected by the fully-pinning postcondition; the only verifying wrong impl exploits a banned verifier escape (not a spec property); positive control verifies and gold resolves; A-legs validated by G-AX over the full domain. verify(model) ⇒ resolved holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13670.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The abbreviated-year rendering takes a calendar year and produces its two
  least-significant decimal digits as a fixed-width, two-character string, with
  a leading zero supplied whenever the value is below ten. Concretely, writing
  ``v`` for the year reduced modulo one hundred (so ``0 <= v <= 99``), the
  result is exactly two characters: the tens digit ``v // 10`` followed by the
  units digit ``v % 10``, each rendered as its decimal-digit character. The
  output therefore always has length two regardless of the magnitude of the
  year — a year such as four renders as ``04`` and a year such as forty-two
  renders as ``42`` — matching the conventional two-digit abbreviation.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); ``ord('0') == 48``. The calendar year is an ``int``. No
library callee is involved — the rendering is pure integer arithmetic and
digit emission, so it is modelled deeply and no operation is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (no library callee is invoked; the rendering is modelled deeply, so there is
# no @ContractOnly axiom.)
# axioms-end

# pure-start
@Pure
def tens_digit(v: int) -> int:
    """Code point of the tens digit of a value in 0..99."""
    Requires(0 <= v and v <= 99)
    Ensures(Result() == 48 + (v // 10))
    return 48 + (v // 10)

@Pure
def units_digit(v: int) -> int:
    """Code point of the units digit of a value in 0..99."""
    Requires(0 <= v and v <= 99)
    Ensures(Result() == 48 + (v % 10))
    return 48 + (v % 10)
# pure-end

def abbreviated_year(year: int) -> List[int]:
    # pre-conditions-start
    # Calendar years handled by the renderer are positive (datetime: 1..9999).
    Requires(1 <= year and year <= 9999)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The rendering is always exactly two characters wide.
    Ensures(len(Result()) == 2)
    # Both characters are decimal-digit code points (0x30..0x39).
    Ensures(48 <= Result()[0] and Result()[0] <= 57)
    Ensures(48 <= Result()[1] and Result()[1] <= 57)
    # The two characters are the tens then units digit of the year reduced
    # modulo one hundred — so a leading zero is emitted below ten, and the
    # value is grounded entirely in the input year's arithmetic.
    Ensures(Result()[0] == tens_digit(year % 100))
    Ensures(Result()[1] == units_digit(year % 100))
    # post-conditions-end
    # impl-start
    v = year % 100
    result = [tens_digit(v), units_digit(v)]  # type: List[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle: django__django-13670 nagini; project root (env python, SBU_BENCHMARK_DIR=benchmark-verified).

SPEC SHAPE (why hard to break): abbreviated_year's postcondition FULLY PINS the output element-wise for every admitted input — len(Result())==2, Result()[0]==tens_digit(year%100), Result()[1]==units_digit(year%100), plus 0x30..0x39 digit ranges; the @Pure helpers tens_digit/units_digit are themselves pinned by Ensures. This leaves ZERO behavioural freedom, so any behaviourally-wrong impl cannot verify.

7 same-spec attacks built by editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; adversary same-spec = exit 0 SAME for all 7). Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-13670 atk_N.py`.
- atk_1.py PREPATCH bug (deep str(year)[2:] slice, from model_prepatch.py): same-spec, does NOT verify (verification failed) — spec senses the change (G-DIFF). prepatch reproduced.
- atk_2.py swap tens/units digits: same-spec, does NOT verify.
- atk_3.py boundary off-by-one ((year+1)%100): same-spec, does NOT verify.
- atk_4.py partial-domain (correct for year<1000, uses (year//100)%100 for year>=1000): same-spec, does NOT verify.
- atk_5.py control-flow-effect (drops leading zero for v<10, returns 1-char list): same-spec, does NOT verify (violates len==2 / element pin).
- atk_6.py ungrounded-oracle echo (hardcoded [48,48] == '00'): same-spec, does NOT verify (violates element pin for year%100 != 0).
- POSITIVE CONTROL positive_control.py (gold impl, verbatim model.py): same-spec AND verifies (11.5s). Gold patch.diff run through official run_resolve => completed=True, resolved=True (infra sanity + verify⇒correct confirmed).

atk_7.py (Assume(False) vacuous verify) EXCLUDED FROM SUBMITTED ATTACKS AS A NON-COUNTEREXAMPLE: it came back CANDIDATE (weakness exit 0: shares spec AND verifies, 12.3s) and I materialized its faithful patch (impl semantically returns '00' since Assume is proof-only) and RAN it through the official harness (run_resolve) => completed=True, resolved=False (consistent across 3 attempts). Literally that is the BROKEN trigger, BUT it verifies ONLY because Assume(False) poisons the verification path. `Assume(` is a BANNED TOKEN in the nagini backend (src/swebench_unified/backends/nagini.py banned_tokens=('Assume(','Refute(')), independently rejected by G-HYGIENE (confirmed via gates.hygiene._banned_calls => {'Assume'}).

It has no repo/runtime semantics and would vacuously verify against ANY postcondition — i.e. it would 'break' EVERY nagini bundle in existence. That is verifier unsoundness, not a weakness of THIS spec. The runner's check_attack does not apply the hygiene screen, so submitting atk_7 would manufacture a spurious universal BROKEN (a false positive). I deliberately do not submit it. All artifacts retained: atk_7.py, patch_atk_7.diff, resolve_atk7.txt, patch_gold.diff, resolve_gold.txt.

A-LEG / deep-model audit (the focus): refinement.md has 5 legs — #1 R (self.data.year<->int year, range 1..9999), #2 I (year%100 modulo), #3 A-reference (tens_digit == tens position of '%02d'%v), #4 A-reference (units_digit == units position), #5 R (str<->List[int] code points, width 2). NO kind-3 step and NO A-consumed axiom: the one changed op (two-digit decimal rendering) is modeled DEEPLY, not axiomatized. G-AX axiom_check.py run => exit 0: 'deep model == real "%02d"%(year%100) on all 9999 years (1..9999); width 2 + digit code points; old str(year)[2:] differs on 999 years (incl. all sub-100).' The A-reference correspondence to the real callee expression thus holds EXHAUSTIVELY over the admitted domain. mapping.md callee provenance = None (language %-formatting, deep model) — consistent.

Conclusion: every legitimate same-spec wrong impl (6/6) is rejected by the fully-pinning postcondition; the only verifying wrong impl exploits a banned verifier escape (not a spec property); positive control verifies and gold resolves; A-legs validated by G-AX over the full domain. verify(model) ⇒ resolved holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) audit for django__django-13670 nagini. The modeled function abbreviated_year(year) maps to the real post-patch callee DateFormat.y() = '%02d' % (self.data.year % 100) at the target line (dateformat.py:310, patched body). Checked the model's contract-stripped impl against the REAL callee imported over the ENTIRE admitted domain (years 1..9999, exhaustive): 0 divergences. For every v=year%100 in 0..99, '%02d' % v == chr(48+v//10)+chr(48+v%10), exactly what tens_digit/units_digit emit; str<->List[int] via ord bridge. The postconditions are strong and non-vacuous: len(Result())==2, both elements in 0x30..0x39, and element-wise equality to tens_digit/units_digit(year%100) — the model verifies (Nagini: Verification successful, 12.9s) and pins the output uniquely, so the spec is neither too strong (it admits exactly the real renderer's outputs) nor drifting. Precondition domain 1<=year<=9999 matches datetime MINYEAR..MAXYEAR, the real callee's operating range. No diverging input exists; spec is FAITHFUL to real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: hard_failures=[], no relaxed flag, no RELAXED_LEAKAGE.md). Semantic review of the consumer spec view (markers.spec_view over model.py) confirms no leakage beyond the public problem_statement:

- Gold edit: `return str(self.data.year)[2:]` -> `return '%02d' % (self.data.year % 100)` in django/utils/dateformat.py (DateFormat.y). The discriminator is two-digit, zero-padded abbreviated year.
- The PUBLIC problem_statement already fully discloses the desired behavior: it shows `%y` should yield '23' for year 123 (not '3'), and references 99/9 similarly, explicitly matching Python datetime/PHP two-digit-with-leading-zeros semantics. The target behavior is therefore public.
- Spec view content: module docstring + contracts state only DESIRED behavior ('two least-significant decimal digits as a fixed-width two-character string, leading zero when below ten', 'four renders as 04', 'forty-two renders as 42'; Ensures len==2, tens/units digit of year%100). This is exactly the behavior the problem statement already spells out.
- No gold-diff line reproduced in the spec view (verified: none of the 4 changed lines appear normalized in view_norm). No diff markers. Patched file path django/utils/dateformat.py absent from spec view. No patched repo symbol echoed (changed_symbols is empty). No bug/fix/regression narration; impl region is elided (`...`) in the projection, and the pure region is stated as forward behavior, not an edit.
- The verbatim gold hunk and pre-patch expression (`str(self.data.year)[2:]`) appear ONLY in refinement.md and mapping.md, which are audit-side artifacts, not the consumer spec view.

Nothing in the spec view localizes or reconstructs the gold edit beyond what the public task already reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
