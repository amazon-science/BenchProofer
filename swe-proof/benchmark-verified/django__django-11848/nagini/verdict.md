# P2 adversarial audit — django__django-11848

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.py`, `atk_2_boundary.py`, `atk_3_partial.py`, `atk_4_offby100.py`, `atk_5_swapped.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6_echo_pure.py`, `atk_7_echo_alt.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # A genuine two-digit year, and a real (four-digit) reference calendar year.
     Requires(0 <= two_digit_year and two_digit_year < 100)
     Requires(reference_year >= 1000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly the reference-relative expansion of the input.
@@ -76,11 +74,9 @@
     Ensures(reference_year - Result() < 150)
     # post-conditions-end
     # impl-start
-    base = reference_year - (reference_year % 100)
-    if two_digit_year - (reference_year % 100) > 50:
-        # More than fifty years ahead: roll back to the previous century.
-        result = two_digit_year + base - 100
+    if two_digit_year < 70:
+        result = two_digit_year + 2000
     else:
-        result = two_digit_year + base
+        result = two_digit_year + 1900
     return result
     # impl-end
```

Attack 2 — `atk_2_boundary.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # A genuine two-digit year, and a real (four-digit) reference calendar year.
     Requires(0 <= two_digit_year and two_digit_year < 100)
     Requires(reference_year >= 1000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly the reference-relative expansion of the input.
@@ -77,8 +75,7 @@
     # post-conditions-end
     # impl-start
     base = reference_year - (reference_year % 100)
-    if two_digit_year - (reference_year % 100) > 50:
-        # More than fifty years ahead: roll back to the previous century.
+    if two_digit_year - (reference_year % 100) >= 50:
         result = two_digit_year + base - 100
     else:
         result = two_digit_year + base
```

Attack 3 — `atk_3_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # A genuine two-digit year, and a real (four-digit) reference calendar year.
     Requires(0 <= two_digit_year and two_digit_year < 100)
     Requires(reference_year >= 1000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly the reference-relative expansion of the input.
@@ -77,10 +75,6 @@
     # post-conditions-end
     # impl-start
     base = reference_year - (reference_year % 100)
-    if two_digit_year - (reference_year % 100) > 50:
-        # More than fifty years ahead: roll back to the previous century.
-        result = two_digit_year + base - 100
-    else:
-        result = two_digit_year + base
+    result = two_digit_year + base
     return result
     # impl-end
```

Attack 4 — `atk_4_offby100.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # A genuine two-digit year, and a real (four-digit) reference calendar year.
     Requires(0 <= two_digit_year and two_digit_year < 100)
     Requires(reference_year >= 1000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly the reference-relative expansion of the input.
@@ -78,9 +76,8 @@
     # impl-start
     base = reference_year - (reference_year % 100)
     if two_digit_year - (reference_year % 100) > 50:
-        # More than fifty years ahead: roll back to the previous century.
+        result = two_digit_year + base - 200
+    else:
         result = two_digit_year + base - 100
-    else:
-        result = two_digit_year + base
     return result
     # impl-end
```

Attack 5 — `atk_5_swapped.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # A genuine two-digit year, and a real (four-digit) reference calendar year.
     Requires(0 <= two_digit_year and two_digit_year < 100)
     Requires(reference_year >= 1000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly the reference-relative expansion of the input.
@@ -78,9 +76,8 @@
     # impl-start
     base = reference_year - (reference_year % 100)
     if two_digit_year - (reference_year % 100) > 50:
-        # More than fifty years ahead: roll back to the previous century.
+        result = two_digit_year + base
+    else:
         result = two_digit_year + base - 100
-    else:
-        result = two_digit_year + base
     return result
     # impl-end
```

Attack 6 — `atk_6_echo_pure.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # A genuine two-digit year, and a real (four-digit) reference calendar year.
     Requires(0 <= two_digit_year and two_digit_year < 100)
     Requires(reference_year >= 1000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly the reference-relative expansion of the input.
@@ -76,11 +74,5 @@
     Ensures(reference_year - Result() < 150)
     # post-conditions-end
     # impl-start
-    base = reference_year - (reference_year % 100)
-    if two_digit_year - (reference_year % 100) > 50:
-        # More than fifty years ahead: roll back to the previous century.
-        result = two_digit_year + base - 100
-    else:
-        result = two_digit_year + base
-    return result
+    return resolved_year(two_digit_year, reference_year)
     # impl-end
```

Attack 7 — `atk_7_echo_alt.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # A genuine two-digit year, and a real (four-digit) reference calendar year.
     Requires(0 <= two_digit_year and two_digit_year < 100)
     Requires(reference_year >= 1000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly the reference-relative expansion of the input.
@@ -77,10 +75,8 @@
     # post-conditions-end
     # impl-start
     base = reference_year - (reference_year % 100)
-    if two_digit_year - (reference_year % 100) > 50:
-        # More than fifty years ahead: roll back to the previous century.
-        result = two_digit_year + base - 100
-    else:
-        result = two_digit_year + base
+    result = two_digit_year + base
+    if result - reference_year > 50:
+        result = result - 100
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11848.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A two-digit calendar year (0..99), taken from a legacy date stamp, must be
  expanded to a full four-digit year RELATIVE TO A REFERENCE YEAR. The rule,
  per the HTTP date specification:

    * the expanded year shares the same last two digits as the two-digit input;
    * it lies in the reference year's century when that places it no more than
      fifty years ahead of the reference year;
    * a value that would otherwise fall MORE THAN fifty years in the future of
      the reference year is instead taken to mean the most recent past year with
      those same last two digits (i.e. it rolls back one century).

  Equivalently, writing `c` for the reference year's last two digits and
  `base` for its century start (reference year minus `c`): the result is
  `input + base` when `input - c <= 50`, and `input + base - 100` otherwise.

The reference year is supplied by the (unchanged) wall-clock source the caller
consults; it is modelled here as an explicit parameter `reference_year`. The
whole computation is exact integer arithmetic.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the changed operation is exact integer arithmetic,
# modelled deeply in the `pure` region below. The reference year is an explicit
# integer parameter standing in for the unchanged wall-clock source — see
# mapping.md / axiom_check.py for its provenance and soundness check.)
# axioms-end


# pure-start
@Pure
def century_start(reference_year: int) -> int:
    """The start of the reference year's century (reference year with its last
    two digits cleared)."""
    return reference_year - (reference_year % 100)


@Pure
def resolved_year(two_digit_year: int, reference_year: int) -> int:
    """The full year a two-digit year denotes relative to `reference_year`:
    same last two digits, placed in the reference century unless that would be
    more than fifty years ahead — in which case the previous century is used."""
    Requires(reference_year >= 0)
    if two_digit_year - (reference_year % 100) > 50:
        return two_digit_year + century_start(reference_year) - 100
    return two_digit_year + century_start(reference_year)
# pure-end


def expand_two_digit_year(two_digit_year: int, reference_year: int) -> int:
    # pre-conditions-start
    # A genuine two-digit year, and a real (four-digit) reference calendar year.
    Requires(0 <= two_digit_year and two_digit_year < 100)
    Requires(reference_year >= 1000)
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the reference-relative expansion of the input.
    Ensures(Result() == resolved_year(two_digit_year, reference_year))
    # It preserves the last two digits of the input.
    Ensures(Result() % 100 == two_digit_year)
    # It is never more than fifty years ahead of the reference year ...
    Ensures(Result() - reference_year <= 50)
    # ... and never more than (49 years + most of a century) behind it, i.e. the
    # chosen year is the most recent one with those last two digits that is not
    # excessively future.
    Ensures(reference_year - Result() < 150)
    # post-conditions-end
    # impl-start
    base = reference_year - (reference_year % 100)
    if two_digit_year - (reference_year % 100) > 50:
        # More than fifty years ahead: roll back to the previous century.
        result = two_digit_year + base - 100
    else:
        result = two_digit_year + base
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins Result() == resolved_year(two_digit_year, reference_year) as an EXACT function of inputs over the full domain (0<=tdy<100, ref>=1000), so any verifying impl equals the gold arithmetic everywhere, in particular on all F2P-pinned reference years (2019/2020/2048). All 7 attacks share the byte-identical spec (same-spec exit 0). python=python; adversary cmd: `python -m swebench_unified.adversary weakness nagini django__django-11848 <atk>`.

WRONG IMPLS, ALL REJECTED (exit 2, spec caught them):
- atk_1_prepatch.py: fixed cutoff at 70 (the prepatch bug) -> NOT-A-COUNTEREXAMPLE (does not verify). PREPATCH REPRODUCED: spec rejects the exact prepatch skeleton.
- atk_2_boundary.py: threshold >50 changed to >=50 (boundary off-by-one) -> does not verify.
- atk_3_partial.py: always same-century branch (partial domain) -> does not verify.
- atk_4_offby100.py: extra -100 in both branches -> does not verify.
- atk_5_swapped.py: swapped roll-back/same-century branches (control-flow-effect) -> does not verify.

CANDIDATES (share spec AND verify) -> materialized faithful patch AND RAN official harness run_evaluation (SWE-bench_Verified, swebench namespace, image latest):
- atk_6_echo_pure.py: impl `return resolved_year(...)` == gold arithmetic. Faithful patch = gold patch verbatim. RESOLVE RESULT: resolved=true, patch_successfully_applied=true, FAIL_TO_PASS success=[test_parsing_rfc850, test_parsing_year_less_than_70], failures=[]. Report: report.json
- atk_7_echo_alt.py: equivalent alt arithmetic (year+=century_start; if year-ref>50: year-=100; algebraically == gold since (tdy+cc)-cy == tdy-cy%100). Faithful patch transcribes that arithmetic. RESOLVE RESULT: resolved=true, applied=true, both F2P tests pass, failures=[]. Report: report.json

BOTH verifying candidates RESOLVE -> neither is a verify-but-incorrect witness; spec is NOT too weak. (Note: harness.run_resolve initially returned completed=false 'no report/image pull failure' for both due to a transient concurrent image-prune race from other concurrent runs sharing /var/lib/docker; a manual re-run of run_evaluation once the django image was cached produced clean reports for both, resolved=true.)

POSITIVE CONTROL: positive_control.py (copy of model.py) verifies (Verification successful, 10.68s).

REFINEMENT.MD AUDIT: legs A1 (R, tdy identity), A2 (A-reference, reference_year<->utcnow().year), A3-A6 (I, identical arithmetic), A7 (R, Result identity), plus resolved_year/century_start deep model (A-reference). No kind-3 (unexpressible-changed-op) leg: the changed two-digit-year expansion is modelled DEEPLY as exact integer arithmetic, not hidden behind an axiom. No @ContractOnly axiom consumed (axioms-start/end region is comment-only). A-reference correspondence confirmed by G-AX (axiom_check.py exit 0): resolved_year == real patch arithmetic on 202,200 boundary+exhaustive+fuzz inputs + 7 F2P-pinned cases, and utcnow().year is a plain int>=1000 (==2026). All A-legs' correspondence to real callees holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.py`, `atk_2_boundary.py`, `atk_3_partial.py`, `atk_4_offby100.py`, `atk_5_swapped.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6_echo_pure.py`, `atk_7_echo_alt.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_boundary.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_offby100.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_swapped.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_echo_pure.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_echo_alt.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11848.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A two-digit calendar year (0..99), taken from a legacy date stamp, must be
  expanded to a full four-digit year RELATIVE TO A REFERENCE YEAR. The rule,
  per the HTTP date specification:

    * the expanded year shares the same last two digits as the two-digit input;
    * it lies in the reference year's century when that places it no more than
      fifty years ahead of the reference year;
    * a value that would otherwise fall MORE THAN fifty years in the future of
      the reference year is instead taken to mean the most recent past year with
      those same last two digits (i.e. it rolls back one century).

  Equivalently, writing `c` for the reference year's last two digits and
  `base` for its century start (reference year minus `c`): the result is
  `input + base` when `input - c <= 50`, and `input + base - 100` otherwise.

The reference year is supplied by the (unchanged) wall-clock source the caller
consults; it is modelled here as an explicit parameter `reference_year`. The
whole computation is exact integer arithmetic.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the changed operation is exact integer arithmetic,
# modelled deeply in the `pure` region below. The reference year is an explicit
# integer parameter standing in for the unchanged wall-clock source — see
# mapping.md / axiom_check.py for its provenance and soundness check.)
# axioms-end


# pure-start
@Pure
def century_start(reference_year: int) -> int:
    """The start of the reference year's century (reference year with its last
    two digits cleared)."""
    return reference_year - (reference_year % 100)


@Pure
def resolved_year(two_digit_year: int, reference_year: int) -> int:
    """The full year a two-digit year denotes relative to `reference_year`:
    same last two digits, placed in the reference century unless that would be
    more than fifty years ahead — in which case the previous century is used."""
    Requires(reference_year >= 0)
    if two_digit_year - (reference_year % 100) > 50:
        return two_digit_year + century_start(reference_year) - 100
    return two_digit_year + century_start(reference_year)
# pure-end


def expand_two_digit_year(two_digit_year: int, reference_year: int) -> int:
    # pre-conditions-start
    # A genuine two-digit year, and a real (four-digit) reference calendar year.
    Requires(0 <= two_digit_year and two_digit_year < 100)
    Requires(reference_year >= 1000)
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the reference-relative expansion of the input.
    Ensures(Result() == resolved_year(two_digit_year, reference_year))
    # It preserves the last two digits of the input.
    Ensures(Result() % 100 == two_digit_year)
    # It is never more than fifty years ahead of the reference year ...
    Ensures(Result() - reference_year <= 50)
    # ... and never more than (49 years + most of a century) behind it, i.e. the
    # chosen year is the most recent one with those last two digits that is not
    # excessively future.
    Ensures(reference_year - Result() < 150)
    # post-conditions-end
    # impl-start
    base = reference_year - (reference_year % 100)
    if two_digit_year - (reference_year % 100) > 50:
        # More than fifty years ahead: roll back to the previous century.
        result = two_digit_year + base - 100
    else:
        result = two_digit_year + base
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins Result() == resolved_year(two_digit_year, reference_year) as an EXACT function of inputs over the full domain (0<=tdy<100, ref>=1000), so any verifying impl equals the gold arithmetic everywhere, in particular on all F2P-pinned reference years (2019/2020/2048). All 7 attacks share the byte-identical spec (same-spec exit 0). python=python; adversary cmd: `python -m swebench_unified.adversary weakness nagini django__django-11848 <atk>`.

WRONG IMPLS, ALL REJECTED (exit 2, spec caught them):
- atk_1_prepatch.py: fixed cutoff at 70 (the prepatch bug) -> NOT-A-COUNTEREXAMPLE (does not verify). PREPATCH REPRODUCED: spec rejects the exact prepatch skeleton.
- atk_2_boundary.py: threshold >50 changed to >=50 (boundary off-by-one) -> does not verify.
- atk_3_partial.py: always same-century branch (partial domain) -> does not verify.
- atk_4_offby100.py: extra -100 in both branches -> does not verify.
- atk_5_swapped.py: swapped roll-back/same-century branches (control-flow-effect) -> does not verify.

CANDIDATES (share spec AND verify) -> materialized faithful patch AND RAN official harness run_evaluation (SWE-bench_Verified, swebench namespace, image latest):
- atk_6_echo_pure.py: impl `return resolved_year(...)` == gold arithmetic. Faithful patch = gold patch verbatim. RESOLVE RESULT: resolved=true, patch_successfully_applied=true, FAIL_TO_PASS success=[test_parsing_rfc850, test_parsing_year_less_than_70], failures=[]. Report: report.json
- atk_7_echo_alt.py: equivalent alt arithmetic (year+=century_start; if year-ref>50: year-=100; algebraically == gold since (tdy+cc)-cy == tdy-cy%100). Faithful patch transcribes that arithmetic. RESOLVE RESULT: resolved=true, applied=true, both F2P tests pass, failures=[]. Report: report.json

BOTH verifying candidates RESOLVE -> neither is a verify-but-incorrect witness; spec is NOT too weak. (Note: harness.run_resolve initially returned completed=false 'no report/image pull failure' for both due to a transient concurrent image-prune race from other concurrent runs sharing /var/lib/docker; a manual re-run of run_evaluation once the django image was cached produced clean reports for both, resolved=true.)

POSITIVE CONTROL: positive_control.py (copy of model.py) verifies (Verification successful, 10.68s).

REFINEMENT.MD AUDIT: legs A1 (R, tdy identity), A2 (A-reference, reference_year<->utcnow().year), A3-A6 (I, identical arithmetic), A7 (R, Result identity), plus resolved_year/century_start deep model (A-reference). No kind-3 (unexpressible-changed-op) leg: the changed two-digit-year expansion is modelled DEEPLY as exact integer arithmetic, not hidden behind an axiom. No @ContractOnly axiom consumed (axioms-start/end region is comment-only). A-reference correspondence confirmed by G-AX (axiom_check.py exit 0): resolved_year == real patch arithmetic on 202,200 boundary+exhaustive+fuzz inputs + 7 F2P-pinned cases, and utcnow().year is a plain int>=1000 (==2026). All A-legs' correspondence to real callees holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical (same-spec exit 0). The modeled function expand_two_digit_year / resolved_year reproduces the gold-patch two-digit-year expansion arithmetic exactly: current_century = ref - ref%100; if year - ref%100 > 50 then year += cc-100 else year += cc. Fuzzed the deep model against the exact real patch arithmetic (transcribed from django/utils/http.py post-patch, confirmed in the worktree) over reference years 1000..2999, boundary 9999, 2026, plus 5000 random refs, each across all 100 two-digit inputs (0..99): 0 model-vs-real divergences. All four postconditions hold on the real value everywhere in that range: Result()==resolved_year (0 fail), Result()%100==input (0 fail), Result()-ref<=50 (0 fail), ref-Result()<150 (0 fail). Preconditions (0<=input<100 established by the `if year < 100:` guard + RFC850 (?P<year>\d{2}) regex; ref>=1000) match the real domain and are not over-strong. reference_year is a faithful value abstraction of the unchanged utcnow().year source (identity on the int; G-AX confirms utcnow().year is int>=1000). No input found where the spec disagrees with the real callee — spec is faithful, not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). Semantic review of the spec view confirms no leakage beyond the public problem_statement:

- No diff markers, no patched file path (django/utils/http.py), no patched module dotted-path, and no patched repo symbols (parse_http_date, current_century/current_year, utcnow) appear in the spec view.
- No bug/fix narration in spec-view comments/docstrings.

Everything the spec discloses is already public in the problem_statement's RFC 7231 quote and description:
  * '50 years in the future -> most recent past year with the same last two digits' == the spec's threshold + century-rollback rule (post-conditions and resolved_year).
  * 'comparing versus the current year' == the reference_year-relative expansion (the whole model is parameterized on reference_year).
  * The buggy fixed cutoff (0-69 -> 2000s, 70-99 -> 1900s) is described publicly; the spec models the CORRECT reference-relative rule, not the diff.

The century-start arithmetic (input + base, input + base - 100) is a faithful FORMALIZATION of the publicly-stated RFC rule, not a disclosure of gold-edit specifics. No line in the spec view reveals the gold edit beyond the problem_statement (hints_text not considered per policy).

Note: model_prepatch.py contains the pre-patch fixed-cutoff skeleton with a 'Pre-patch (buggy)' comment, but that file is NOT part of the consumer spec view and is not scanned by G-LEAK, so it is not a leak of the shipped spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
