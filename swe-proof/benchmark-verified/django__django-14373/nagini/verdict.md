# P2 adversarial audit — django__django-14373

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
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def render_year(year: int) -> List[int]:
     # pre-conditions-start
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -118,11 +116,23 @@
     Ensures(Result()[0] == 48 + year // 1000)
     # post-conditions-end
     # impl-start
+    # ATTACK atk_1 (prepatch-bug reproduction): the bare decimal rendering that
+    # drops most-significant leading zeros — a sub-1000 year yields <4 chars.
     result = []  # type: List[int]
-    result.append(digit(thousands(year)))
-    result.append(digit(hundreds(year)))
-    result.append(digit(tens(year)))
-    result.append(digit(units(year)))
-    Assert(ToSeq(result) == four_field(year))
+    started = False
+    d3 = thousands(year)
+    if d3 > 0:
+        result.append(digit(d3))
+        started = True
+    d2 = hundreds(year)
+    if started or d2 > 0:
+        result.append(digit(d2))
+        started = True
+    d1 = tens(year)
+    if started or d1 > 0:
+        result.append(digit(d1))
+        started = True
+    d0 = units(year)
+    result.append(digit(d0))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def render_year(year: int) -> List[int]:
     # pre-conditions-start
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -118,11 +116,13 @@
     Ensures(Result()[0] == 48 + year // 1000)
     # post-conditions-end
     # impl-start
+    # ATTACK atk_2 (digit transposition): tens and units places swapped. Still
+    # four ASCII digits, still len 4, but the reconstruction / four_field clause
+    # should catch it (e.g. year 1234 -> '1243').
     result = []  # type: List[int]
     result.append(digit(thousands(year)))
     result.append(digit(hundreds(year)))
+    result.append(digit(units(year)))
     result.append(digit(tens(year)))
-    result.append(digit(units(year)))
-    Assert(ToSeq(result) == four_field(year))
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def render_year(year: int) -> List[int]:
     # pre-conditions-start
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -118,11 +116,19 @@
     Ensures(Result()[0] == 48 + year // 1000)
     # post-conditions-end
     # impl-start
+    # ATTACK atk_3 (partial-domain / control-flow branch): render correctly for
+    # four-digit years but pad a sub-1000 year with a SPACE (32) style filler in
+    # the thousands slot instead of the zero digit — mimics '%4d' rather than
+    # '%04d'. Should be rejected: the leading-digit and all-ASCII-digit clauses
+    # fail when thousands==0.
     result = []  # type: List[int]
-    result.append(digit(thousands(year)))
+    d3 = thousands(year)
+    if d3 > 0:
+        result.append(digit(d3))
+    else:
+        result.append(32)  # space filler, not the zero digit
     result.append(digit(hundreds(year)))
     result.append(digit(tens(year)))
     result.append(digit(units(year)))
-    Assert(ToSeq(result) == four_field(year))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def render_year(year: int) -> List[int]:
     # pre-conditions-start
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -118,11 +116,14 @@
     Ensures(Result()[0] == 48 + year // 1000)
     # post-conditions-end
     # impl-start
+    # ATTACK atk_4 (boundary / inline-arithmetic off-by-one): compute the units
+    # place as (year % 10 + 1) % 10 — a +1 rotation of the last digit. Still an
+    # ASCII digit and still len 4, but the reconstruction / four_field clauses
+    # must reject it (e.g. year 1999 -> '1990').
     result = []  # type: List[int]
     result.append(digit(thousands(year)))
     result.append(digit(hundreds(year)))
     result.append(digit(tens(year)))
-    result.append(digit(units(year)))
-    Assert(ToSeq(result) == four_field(year))
+    result.append(digit((year % 10 + 1) % 10))
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def render_year(year: int) -> List[int]:
     # pre-conditions-start
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -118,11 +116,14 @@
     Ensures(Result()[0] == 48 + year // 1000)
     # post-conditions-end
     # impl-start
+    # ATTACK atk_5 (ungrounded-oracle echo): return a hardcoded constant field
+    # '1999' for every year, echoing a single test witness rather than computing
+    # the year. Length 4 and all ASCII digits, but reconstruction fails for any
+    # year != 1999.
     result = []  # type: List[int]
-    result.append(digit(thousands(year)))
-    result.append(digit(hundreds(year)))
-    result.append(digit(tens(year)))
-    result.append(digit(units(year)))
-    Assert(ToSeq(result) == four_field(year))
+    result.append(digit(1))
+    result.append(digit(9))
+    result.append(digit(9))
+    result.append(digit(9))
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -26,7 +26,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def render_year(year: int) -> List[int]:
     # pre-conditions-start
     Requires(1 <= year and year <= 9999)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -118,11 +116,19 @@
     Ensures(Result()[0] == 48 + year // 1000)
     # post-conditions-end
     # impl-start
+    # ATTACK atk_6 (control-flow-effect / full reversal): build the field least
+    # significant first, then reverse-append into result so the digits come out
+    # units..thousands. Length 4, all ASCII digits, but MS-first reconstruction
+    # and the leading-digit clause reject it (e.g. 1234 -> '4321').
+    tmp = []  # type: List[int]
+    tmp.append(digit(units(year)))
+    tmp.append(digit(tens(year)))
+    tmp.append(digit(hundreds(year)))
+    tmp.append(digit(thousands(year)))
     result = []  # type: List[int]
-    result.append(digit(thousands(year)))
-    result.append(digit(hundreds(year)))
-    result.append(digit(tens(year)))
-    result.append(digit(units(year)))
-    Assert(ToSeq(result) == four_field(year))
+    result.append(tmp[0])
+    result.append(tmp[1])
+    result.append(tmp[2])
+    result.append(tmp[3])
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14373.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A calendar year (a positive integer in the supported range) is rendered as
  its decimal representation in a CONSTANT FOUR-CHARACTER field, left-padded
  with the zero digit when the value has fewer than four significant digits. So a
  one-, two- or three-digit year still produces exactly four characters, the
  leading positions carrying '0', while a four-digit year produces its own
  four digits. Concretely the rendered field is

      <thousands><hundreds><tens><units>

  where each position holds the ASCII decimal digit for that place value of the
  year; for a year below 1000 the high positions are the zero digit, never
  dropped. Every character of the result is an ASCII decimal digit and the four
  place-value digits, read most-significant first, reconstruct the year exactly.

Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
zero-padded constant-width decimal rendering is the changed operation and is
modelled DEEPLY as the spelled-out place-value digit decomposition; there is
no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the constant-width zero-padded decimal rendering is
#  modelled deeply as a place-value digit decomposition of expressible pieces.)
# axioms-end


# pure-start
@Pure
def digit(d: int) -> int:
    """The ASCII code point of a single decimal digit value 0..9."""
    Requires(0 <= d and d <= 9)
    Ensures(48 <= Result() and Result() <= 57)
    Ensures(Result() == 48 + d)
    return 48 + d


@Pure
def thousands(year: int) -> int:
    """Thousands place value of a four-digit-range year."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return year // 1000


@Pure
def hundreds(year: int) -> int:
    """Hundreds place value."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return (year // 100) % 10


@Pure
def tens(year: int) -> int:
    """Tens place value."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return (year // 10) % 10


@Pure
def units(year: int) -> int:
    """Units place value."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return year % 10


@Pure
def four_field(year: int) -> PSeq[int]:
    """The four-character zero-padded decimal field for a supported year: the
    ASCII digits of the thousands, hundreds, tens and units place values, most
    significant first. Always four code points; leading zeros are retained."""
    Requires(0 <= year and year <= 9999)
    Ensures(len(Result()) == 4)
    return PSeq(digit(thousands(year)),
                digit(hundreds(year)),
                digit(tens(year)),
                digit(units(year)))
# pure-end


def render_year(year: int) -> List[int]:
    # pre-conditions-start
    Requires(1 <= year and year <= 9999)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The rendered field is the deep place-value decomposition.
    Ensures(ToSeq(Result()) == four_field(year))
    # Constant width: exactly four characters regardless of magnitude — this is
    # the zero-padding guarantee that distinguishes a sub-1000 year from its
    # bare significant digits.
    Ensures(len(Result()) == 4)
    # Every character is an ASCII decimal digit.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
                                           48 <= Result()[k] and Result()[k] <= 57),
                                    [[Result()[k]]])))
    # The four place-value digits, most significant first, reconstruct the year.
    Ensures((Result()[0] - 48) * 1000
            + (Result()[1] - 48) * 100
            + (Result()[2] - 48) * 10
            + (Result()[3] - 48) == year)
    # The leading (thousands) position is exactly the thousands digit, which for
    # any year below 1000 is the zero digit and is never dropped.
    Ensures(Result()[0] == 48 + year // 1000)
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    result.append(digit(thousands(year)))
    result.append(digit(hundreds(year)))
    result.append(digit(tens(year)))
    result.append(digit(units(year)))
    Assert(ToSeq(result) == four_field(year))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of django__django-14373 nagini bundle (render_year / DateFormat.Y '%04d' zero-padding). Focused on A-legs + model<->patch correspondence (R/I legs are G-CONF-covered).

SPEC STRENGTH: render_year's postcondition pins the output COMPLETELY over the entire precondition domain 1<=year<=9999: ToSeq(Result())==four_field(year) (exact place-value field), plus len==4, every char an ASCII digit (48..57), MS-first place-value reconstruction == year, and leading position == 48+year//1000. The precondition domain exactly matches the real self.data.year domain (datetime.MINYEAR=1..MAXYEAR=9999). This is a full functional spec, not a partial oracle.

ATTACK BATTERY (all copied from bundle model.py, ONLY the impl region edited; spec prefix lines 1-117 confirmed byte-identical; all 6 confirmed same-spec via `adversary same-spec` exit 0):
- atk_1 (prepatch-bug reproduction: leading-zero-stripping bare decimal render) -> weakness exit 2 (does NOT verify). Spec senses the change (G-DIFF): prepatch reproduced.
- atk_2 (digit transposition, tens<->units) -> exit 2 (does NOT verify).
- atk_3 (partial-domain/control-flow: '%4d' space-pad (32) in thousands slot when year<1000) -> exit 2 (does NOT verify).
- atk_4 (boundary/inline off-by-one: units = (year%10+1)%10) -> exit 2 (does NOT verify).
- atk_5 (ungrounded-oracle echo: hardcoded constant '1999') -> exit 2 (does NOT verify).
- atk_6 (control-flow-effect full reversal: digits emitted units..thousands) -> exit 2 (does NOT verify).

Commands:
  PY -m swebench_unified.adversary same-spec nagini django__django-14373 <atk> => all exit 0 (SAME)
  PY -m swebench_unified.adversary weakness nagini django__django-14373 <atk_N> => all exit 2 (NOT-A-COUNTEREXAMPLE: does not verify)
  PY -m swebench_unified.adversary verify nagini django__django-14373 positive_control.py => VERIFIED in 13.7s (exit 0)
Run concurrently in batches of <=3 JVMs (batch1: pc+atk_1+atk_2; batch2: atk_3+atk_4+atk_5; batch3: atk_6).

NO CANDIDATE emerged (no same-spec impl both shares the spec AND verifies other than the correct one), so there was NO faithful refined patch to materialize/run through run_resolve. patches={} accordingly. verify=>correct is upheld: every wrong impl is rejected by the verifier.

A-LEG / refinement.md AUDIT (plan §4): three legs, all R or A-reference, no consumed axiom, NO kind-3 (unexpressible changed-op) leg.
  A1 (R): year:int, 1<=year<=9999 <-> self.data.year; bound = CPython datetime year domain. Correct.
  A2 (A-reference): deep model four_field (place-value decomposition digit/thousands/hundreds/tens/units) validated == real '%04d' % self.data.year. axiom_check.py RUN: exit 0 — 'G-AX OK: four_field deep model (== %04d rendering) sound on all 9999 supported years + 10 boundary witnesses' (exhaustive 1..9999 sweep + boundary witnesses 1->0001, 999->0999, etc.). Correspondence to the real callee holds over the entire domain.
  A3 (R): str <-> List[int] ASCII code-point carrier; DateFormat.format concatenation preserved. Correct.
The single changed operation (fixed-width zero-padded decimal render) is modelled DEEPLY and grounded via A2, not hidden behind an axiom about the function under change. Correspondence audited and holds.

VERDICT: SOUND. >=5 distinct attacks (6) + prepatch bug all run and none breaks the spec; positive control verifies; axiom_check (A-reference grounding) passes; refinement legs are all R/A-reference with valid callee correspondence and no kind-3. verify=>correct holds for this bundle.

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
"""Twin-artifact model for django__django-14373.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A calendar year (a positive integer in the supported range) is rendered as
  its decimal representation in a CONSTANT FOUR-CHARACTER field, left-padded
  with the zero digit when the value has fewer than four significant digits. So a
  one-, two- or three-digit year still produces exactly four characters, the
  leading positions carrying '0', while a four-digit year produces its own
  four digits. Concretely the rendered field is

      <thousands><hundreds><tens><units>

  where each position holds the ASCII decimal digit for that place value of the
  year; for a year below 1000 the high positions are the zero digit, never
  dropped. Every character of the result is an ASCII decimal digit and the four
  place-value digits, read most-significant first, reconstruct the year exactly.

Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
zero-padded constant-width decimal rendering is the changed operation and is
modelled DEEPLY as the spelled-out place-value digit decomposition; there is
no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the constant-width zero-padded decimal rendering is
#  modelled deeply as a place-value digit decomposition of expressible pieces.)
# axioms-end


# pure-start
@Pure
def digit(d: int) -> int:
    """The ASCII code point of a single decimal digit value 0..9."""
    Requires(0 <= d and d <= 9)
    Ensures(48 <= Result() and Result() <= 57)
    Ensures(Result() == 48 + d)
    return 48 + d


@Pure
def thousands(year: int) -> int:
    """Thousands place value of a four-digit-range year."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return year // 1000


@Pure
def hundreds(year: int) -> int:
    """Hundreds place value."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return (year // 100) % 10


@Pure
def tens(year: int) -> int:
    """Tens place value."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return (year // 10) % 10


@Pure
def units(year: int) -> int:
    """Units place value."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return year % 10


@Pure
def four_field(year: int) -> PSeq[int]:
    """The four-character zero-padded decimal field for a supported year: the
    ASCII digits of the thousands, hundreds, tens and units place values, most
    significant first. Always four code points; leading zeros are retained."""
    Requires(0 <= year and year <= 9999)
    Ensures(len(Result()) == 4)
    return PSeq(digit(thousands(year)),
                digit(hundreds(year)),
                digit(tens(year)),
                digit(units(year)))
# pure-end


def render_year(year: int) -> List[int]:
    # pre-conditions-start
    Requires(1 <= year and year <= 9999)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The rendered field is the deep place-value decomposition.
    Ensures(ToSeq(Result()) == four_field(year))
    # Constant width: exactly four characters regardless of magnitude — this is
    # the zero-padding guarantee that distinguishes a sub-1000 year from its
    # bare significant digits.
    Ensures(len(Result()) == 4)
    # Every character is an ASCII decimal digit.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
                                           48 <= Result()[k] and Result()[k] <= 57),
                                    [[Result()[k]]])))
    # The four place-value digits, most significant first, reconstruct the year.
    Ensures((Result()[0] - 48) * 1000
            + (Result()[1] - 48) * 100
            + (Result()[2] - 48) * 10
            + (Result()[3] - 48) == year)
    # The leading (thousands) position is exactly the thousands digit, which for
    # any year below 1000 is the zero digit and is never dropped.
    Ensures(Result()[0] == 48 + year // 1000)
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    result.append(digit(thousands(year)))
    result.append(digit(hundreds(year)))
    result.append(digit(tens(year)))
    result.append(digit(units(year)))
    Assert(ToSeq(result) == four_field(year))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of django__django-14373 nagini bundle (render_year / DateFormat.Y '%04d' zero-padding). Focused on A-legs + model<->patch correspondence (R/I legs are G-CONF-covered).

SPEC STRENGTH: render_year's postcondition pins the output COMPLETELY over the entire precondition domain 1<=year<=9999: ToSeq(Result())==four_field(year) (exact place-value field), plus len==4, every char an ASCII digit (48..57), MS-first place-value reconstruction == year, and leading position == 48+year//1000. The precondition domain exactly matches the real self.data.year domain (datetime.MINYEAR=1..MAXYEAR=9999). This is a full functional spec, not a partial oracle.

ATTACK BATTERY (all copied from bundle model.py, ONLY the impl region edited; spec prefix lines 1-117 confirmed byte-identical; all 6 confirmed same-spec via `adversary same-spec` exit 0):
- atk_1 (prepatch-bug reproduction: leading-zero-stripping bare decimal render) -> weakness exit 2 (does NOT verify). Spec senses the change (G-DIFF): prepatch reproduced.
- atk_2 (digit transposition, tens<->units) -> exit 2 (does NOT verify).
- atk_3 (partial-domain/control-flow: '%4d' space-pad (32) in thousands slot when year<1000) -> exit 2 (does NOT verify).
- atk_4 (boundary/inline off-by-one: units = (year%10+1)%10) -> exit 2 (does NOT verify).
- atk_5 (ungrounded-oracle echo: hardcoded constant '1999') -> exit 2 (does NOT verify).
- atk_6 (control-flow-effect full reversal: digits emitted units..thousands) -> exit 2 (does NOT verify).

Commands:
  PY -m swebench_unified.adversary same-spec nagini django__django-14373 <atk> => all exit 0 (SAME)
  PY -m swebench_unified.adversary weakness nagini django__django-14373 <atk_N> => all exit 2 (NOT-A-COUNTEREXAMPLE: does not verify)
  PY -m swebench_unified.adversary verify nagini django__django-14373 positive_control.py => VERIFIED in 13.7s (exit 0)
Run concurrently in batches of <=3 JVMs (batch1: pc+atk_1+atk_2; batch2: atk_3+atk_4+atk_5; batch3: atk_6).

NO CANDIDATE emerged (no same-spec impl both shares the spec AND verifies other than the correct one), so there was NO faithful refined patch to materialize/run through run_resolve. patches={} accordingly. verify=>correct is upheld: every wrong impl is rejected by the verifier.

A-LEG / refinement.md AUDIT (plan §4): three legs, all R or A-reference, no consumed axiom, NO kind-3 (unexpressible changed-op) leg.
  A1 (R): year:int, 1<=year<=9999 <-> self.data.year; bound = CPython datetime year domain. Correct.
  A2 (A-reference): deep model four_field (place-value decomposition digit/thousands/hundreds/tens/units) validated == real '%04d' % self.data.year. axiom_check.py RUN: exit 0 — 'G-AX OK: four_field deep model (== %04d rendering) sound on all 9999 supported years + 10 boundary witnesses' (exhaustive 1..9999 sweep + boundary witnesses 1->0001, 999->0999, etc.). Correspondence to the real callee holds over the entire domain.
  A3 (R): str <-> List[int] ASCII code-point carrier; DateFormat.format concatenation preserved. Correct.
The single changed operation (fixed-width zero-padded decimal render) is modelled DEEPLY and grounded via A2, not hidden behind an axiom about the function under change. Correspondence audited and holds.

VERDICT: SOUND. >=5 distinct attacks (6) + prepatch bug all run and none breaks the spec; positive control verifies; axiom_check (A-reference grounding) passes; refinement legs are all R/A-reference with valid callee correspondence and no kind-3. verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function render_year(year) models DateFormat.Y post-patch = '%04d' % self.data.year (dateformat.py:317). Precondition 1<=year<=9999 exactly matches the real self.data.year domain (datetime.MINYEAR=1..MAXYEAR=9999): not too strong (excludes no real input), not too weak. Exhaustively compared EVERY postcondition clause (len==4, all-ASCII-digits, place-value reconstruction (r0-48)*1000+...+(r3-48)==year, leading digit r0==48+year//1000, ToSeq==four_field) against the real operation '%04d' % year over the entire 1..9999 domain: ZERO divergences. axiom_check.py passes (exit 0) confirming the deep model four_field == '%04d' rendering on all 9999 years + 10 boundary witnesses (1->'0001', 999->'0999', etc.). model.py verifies under pinned Nagini (exit 0, 12.3s). same-spec tooling confirms the spec region is byte-identical. No diverging input exists; the spec is faithful to the real repo behavior — no defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures): no diff markers, no reproduced gold-patch line, no patched file path/module (django/utils/dateformat.py absent), no spec-view identifier embedding the patched symbol 'Y' (the model names its function render_year / four_field), no narration terms.

Semantic review confirms NO-LEAKAGE. Gold edit: `def Y(self): return '%04d' % self.data.year`. The public problem_statement already discloses the full desired behavior: 'The Y specifier ... is supposed to always return a four-digit year padded with zeros. This doesn't seem to be the case for year < 1000.' The spec view formalizes exactly that publicly-known intent — a constant four-character field, zero-padded, leading zeros retained for years below 1000, reconstructing the year from four place-value ASCII digits. This is a faithful specification of already-public behavior, not a disclosure of the edit beyond the problem statement.

No gold-specific mechanism is revealed: the '%04d' format string, the symbol Y, the file path, and the datetime.year source appear only in the audit-side docs (mapping.md/refinement.md), which are NOT part of the consumer spec view. The docstring phrase 'the changed operation' refers to behavior at the abstraction level the problem statement already sets and does not identify the edit. Spec region verified byte-consistent (same-spec region only differs in impl). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
