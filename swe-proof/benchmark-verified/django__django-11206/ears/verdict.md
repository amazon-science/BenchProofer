# P2 adversarial audit — django__django-11206

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1.5 (positive control): extremely small Decimal with fixed decimal_pos
renders as padded zero, NOT exponential. Should FAIL at base, HOLD patched."""
import sys
from decimal import Decimal
from django.conf import settings
if not settings.configured:
    settings.configure(USE_L10N=False, USE_I18N=False, USE_THOUSAND_SEPARATOR=False)
from django.utils.numberformat import format as nformat

got = nformat(Decimal('1e-200'), '.', decimal_pos=2)
print("nformat(Decimal('1e-200'), '.', decimal_pos=2) =>", repr(got))
ok = got == '0.00'
print("expected '0.00'; ok =", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2/R1.3: sub-precision zero for various decimal_pos, including dp=0 -> '0'
and boundary strictly-below values."""
import sys
from decimal import Decimal
from django.conf import settings
if not settings.configured:
    settings.configure(USE_L10N=False, USE_I18N=False, USE_THOUSAND_SEPARATOR=False)
from django.utils.numberformat import format as nformat

cases = [
    (Decimal('9e-19'), 2, '0.00'),      # from hidden test
    (Decimal('0.001'), 2, '0.00'),      # below 0.01
    (Decimal('-0.001'), 2, '0.00'),     # negative below cutoff -> plain zero (no sign)
    (Decimal('.00000000000099'), 0, '0'),  # dp=0, below 0.1 -> '0'
    (Decimal('0.05'), 0, '0'),          # below 0.1, dp=0 -> '0'
    (Decimal('1e-9'), 8, '0.00000000'),
]
ok = True
for val, dp, exp in cases:
    got = nformat(val, '.', decimal_pos=dp)
    good = got == exp
    ok = ok and good
    print(f"nformat({val!r}, '.', decimal_pos={dp}) => {got!r} (expected {exp!r}) {'OK' if good else 'FAIL'}")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.4/R3.5: value >= cutoff must NOT be zeroed. Exact-boundary renders own
digits (0.01), and value just at/above the cutoff renders itself."""
import sys
from decimal import Decimal
from django.conf import settings
if not settings.configured:
    settings.configure(USE_L10N=False, USE_I18N=False, USE_THOUSAND_SEPARATOR=False)
from django.utils.numberformat import format as nformat

cases = [
    (Decimal('0.01'), 2, '0.01'),       # exactly the cutoff -> own digits
    (Decimal('0.02'), 2, '0.02'),
    (Decimal('0.1'), 1, '0.1'),
    (Decimal('0.1'), 0, '0'),           # 0.1 == cutoff for dp=0; not < so renders own -> truncated to '0'
    (Decimal('0.00000001'), 8, '0.00000001'),  # == cutoff for dp=8
]
ok = True
for val, dp, exp in cases:
    got = nformat(val, '.', decimal_pos=dp)
    good = got == exp
    ok = ok and good
    print(f"nformat({val!r}, '.', decimal_pos={dp}) => {got!r} (expected {exp!r}) {'OK' if good else 'FAIL'}")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.1/R2.2/R2.3: very large (>200 digit) decimals keep exponential notation,
with and without decimal_pos; small-value zeroing must not suppress it."""
import sys
from decimal import Decimal
from django.conf import settings
if not settings.configured:
    settings.configure(USE_L10N=False, USE_I18N=False, USE_THOUSAND_SEPARATOR=False)
from django.utils.numberformat import format as nformat

cases = [
    (Decimal('9e9999'), None, '9e+9999'),
    (Decimal('9e9999'), 3, '9.000e+9999'),
    (Decimal('9e201'), None, '9e+201'),
    (Decimal('1.2345e999'), 2, '1.23e+999'),
    (Decimal('9e-999'), None, '9e-999'),         # very small, no dp -> exponential
    (Decimal('1' + '0'*300), 3, '1.000e+300'),
    # >200-digit SMALL value WITH dp: R1.5 zeroing fires before exponential -> '0.000'
    (Decimal('0.{}1234'.format('0'*299)), 3, '0.000'),
]
ok = True
for val, dp, exp in cases:
    got = nformat(val, '.', dp)
    good = got == exp
    ok = ok and good
    print(f"decimal_pos={dp} => {got!r} (expected {exp!r}) {'OK' if good else 'FAIL'}")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.1-R3.4: ordinary Decimal formatting unchanged (truncation, padding, sign,
no-dp fractional presentation, grouping incl. exponential-source integral)."""
import sys
from decimal import Decimal
from django.conf import settings
if not settings.configured:
    settings.configure(USE_L10N=False, USE_I18N=False, USE_THOUSAND_SEPARATOR=False)
from django.utils.numberformat import format as nformat

ok = True
def chk(got, exp, label):
    global ok
    good = got == exp
    ok = ok and good
    print(f"{label} => {got!r} (expected {exp!r}) {'OK' if good else 'FAIL'}")

chk(nformat(Decimal('1234'), '.'), '1234', "Decimal('1234')")
chk(nformat(Decimal('1234.2'), '.'), '1234.2', "Decimal('1234.2')")
chk(nformat(Decimal('1234'), '.', decimal_pos=2), '1234.00', "1234 dp2")
chk(nformat(Decimal('-1234.33'), '.', decimal_pos=1), '-1234.3', "neg trunc sign")
chk(nformat(Decimal('3.'), '.'), '3', "Decimal('3.') no dp")
chk(nformat(Decimal('3.0'), '.'), '3.0', "Decimal('3.0') no dp")
chk(nformat(Decimal('1e16'), '.', thousand_sep=',', grouping=3, force_grouping=True),
    '10,000,000,000,000,000', "1e16 grouping")
chk(nformat(Decimal('1e16'), '.', decimal_pos=2, thousand_sep=',', grouping=3, force_grouping=True),
    '10,000,000,000,000,000.00', "1e16 grouping dp2")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.1-R4.4: non-Decimal inputs unaffected. Also Decimal SUBCLASS custom
__format__ is preserved (the subprecision path must not bypass __format__ for
in-range values). EuroDecimal('1.23') -> '€ 1,23'."""
import sys
from decimal import Decimal
from django.conf import settings
if not settings.configured:
    settings.configure(USE_L10N=False, USE_I18N=False, USE_THOUSAND_SEPARATOR=False)
from django.utils.numberformat import format as nformat

ok = True
def chk(got, exp, label):
    global ok
    good = got == exp
    ok = ok and good
    print(f"{label} => {got!r} (expected {exp!r}) {'OK' if good else 'FAIL'}")

# float no fractional, no dp -> ".0"
chk(nformat(3.0, '.'), '3.0', "float 3.0 no dp")
# int / string padding, grouping, sign
chk(nformat(1234, '.', decimal_pos=2), '1234.00', "int 1234 dp2")
chk(nformat('1234', '.', decimal_pos=2), '1234.00', "str 1234 dp2")
chk(nformat('-1234.33', '.', decimal_pos=1), '-1234.3', "str neg trunc")
chk(nformat(1234, '.', grouping=2, thousand_sep=',', force_grouping=True), '12,34', "int grouping")
# very large int, no dp -> full fixed-point digits
big = 10**250
chk(nformat(big, '.'), '1' + '0'*250, "big int no dp")
# small float with dp must NOT be zeroed (non-Decimal, so rule doesn't apply)
chk(nformat(0.001, '.', decimal_pos=2), '0.00', "float 0.001 dp2 (truncation, not rule)")
# Decimal subclass with custom __format__ preserved
class EuroDecimal(Decimal):
    def __format__(self, spec, **kw):
        return '€ {}'.format(super().__format__(spec, **kw))
chk(nformat(EuroDecimal('1.23'), ','), '€ 1,23', "EuroDecimal subclass")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.5 (positive control): extremely small Decimal with fixed decimal_pos
renders as padded zero, NOT exponential. Should FAIL at base, HOLD patched."""
import sys
from decimal import Decimal
from django.conf import settings
if not settings.configured:
    settings.configure(USE_L10N=False, USE_I18N=False, USE_THOUSAND_SEPARATOR=False)
from django.utils.numberformat import format as nformat

got = nformat(Decimal('1e-200'), '.', decimal_pos=2)
print("nformat(Decimal('1e-200'), '.', decimal_pos=2) =>", repr(got))
ok = got == '0.00'
print("expected '0.00'; ok =", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; all re-run via nl_attack on the instance image, patch applied cleanly.

Coverage vs requirements:
- probe_1 (R1.5, POSITIVE CONTROL): nformat(Decimal('1e-200'),'.',decimal_pos=2) => '0.00' patched; '1.00e-200' at BASE (fails) => discriminates.
- probe_2 (R1.2/R1.3): sub-precision zeroing for dp=2 (0.001, -0.001), dp=0 (.00000000000099, 0.05 -> '0'), dp=8 (1e-9 -> '0.00000000'). Negative below cutoff yields plain '0.00' (no sign).
- probe_3 (R1.4/R3.5): boundary NOT zeroed — 0.01 (==cutoff) -> '0.01', 0.02 -> '0.02', 0.1 dp1 -> '0.1', 0.1 dp0 -> '0', 0.00000001 dp8 -> '0.00000001'.
- probe_4 (R2.1/R2.2/R2.3 + R1.5 ordering): >200-digit values keep exponential (9e9999, 9e201, 1.2345e999 dp2, 9e-999, 1e300 dp3); CRITICALLY the >200-digit SMALL value Decimal('0.<299 zeros>1234') dp3 renders '0.000' (subprecision zeroing fires BEFORE exponential) — this matches the gold test_patch edit ('1.234e-300' -> '0.000').
- probe_5 (R3.1-R3.4): ordinary Decimal formatting unchanged — truncation, padding, sign, no-dp fractional (Decimal('3.') -> '3', Decimal('3.0') -> '3.0'), grouping incl. exponential-source integral (1e16).
- probe_6 (R4.1-R4.4): non-Decimal inputs unaffected (float 3.0 -> '3.0', int/str padding+grouping, big int 10**250 full fixed-point, float 0.001 dp2 -> '0.00' via truncation not the rule) + Decimal subclass custom __format__ preserved (EuroDecimal('1.23') -> '€ 1,23').

DISCRIMINATION: weak.diff places the R1 zeroing AFTER/inside the else-branch of the >200-digit exponential check (a naive reading that only zeroes 'normal' magnitudes). It is REJECTED by probe_1 (1e-200 still '1.00e-200' — that value's abs(exp)+len(digits) exceeds 200 so it takes the exponential branch and never reaches the misplaced check) and by probe_4 (1.234e-300 renders exponential instead of '0.000', the exact gold F2P discriminator). probes 2/3/5/6 pass under weak.diff, confirming the suite isolates the R1.5 ordering requirement rather than blanket-passing. So the requirements (specifically R1.5's 'before any decision about using exponential notation') correctly forbid the lazy fix that would fail the hidden tests.

Initial probe_4 authoring error: I first encoded expected '1.234e-300' from the test-patched file view; the gold test_patch actually changes it to '0.000'. Corrected before submission; both patched-holds and weak-rejects confirmed after correction.

Note (context, not part of this gate): meta.json records G-PANEL-3 (leakage) = fail because the EuroDecimal '€ 1,23' fixture in the spec is not derivable from the public problem statement. That is a leakage concern, orthogonal to spec fidelity/too-weak; the G-EQ (spec-fidelity) verdict is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.5 (positive control): extremely small Decimal with fixed decimal_pos
renders as padded zero, NOT exponential. Should FAIL at base, HOLD patched."""
import sys
from decimal import Decimal
from django.conf import settings
if not settings.configured:
    settings.configure(USE_L10N=False, USE_I18N=False, USE_THOUSAND_SEPARATOR=False)
from django.utils.numberformat import format as nformat

got = nformat(Decimal('1e-200'), '.', decimal_pos=2)
print("nformat(Decimal('1e-200'), '.', decimal_pos=2) =>", repr(got))
ok = got == '0.00'
print("expected '0.00'; ok =", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; all re-run via nl_attack on the instance image, patch applied cleanly.

Coverage vs requirements:
- probe_1 (R1.5, POSITIVE CONTROL): nformat(Decimal('1e-200'),'.',decimal_pos=2) => '0.00' patched; '1.00e-200' at BASE (fails) => discriminates.
- probe_2 (R1.2/R1.3): sub-precision zeroing for dp=2 (0.001, -0.001), dp=0 (.00000000000099, 0.05 -> '0'), dp=8 (1e-9 -> '0.00000000'). Negative below cutoff yields plain '0.00' (no sign).
- probe_3 (R1.4/R3.5): boundary NOT zeroed — 0.01 (==cutoff) -> '0.01', 0.02 -> '0.02', 0.1 dp1 -> '0.1', 0.1 dp0 -> '0', 0.00000001 dp8 -> '0.00000001'.
- probe_4 (R2.1/R2.2/R2.3 + R1.5 ordering): >200-digit values keep exponential (9e9999, 9e201, 1.2345e999 dp2, 9e-999, 1e300 dp3); CRITICALLY the >200-digit SMALL value Decimal('0.<299 zeros>1234') dp3 renders '0.000' (subprecision zeroing fires BEFORE exponential) — this matches the gold test_patch edit ('1.234e-300' -> '0.000').
- probe_5 (R3.1-R3.4): ordinary Decimal formatting unchanged — truncation, padding, sign, no-dp fractional (Decimal('3.') -> '3', Decimal('3.0') -> '3.0'), grouping incl. exponential-source integral (1e16).
- probe_6 (R4.1-R4.4): non-Decimal inputs unaffected (float 3.0 -> '3.0', int/str padding+grouping, big int 10**250 full fixed-point, float 0.001 dp2 -> '0.00' via truncation not the rule) + Decimal subclass custom __format__ preserved (EuroDecimal('1.23') -> '€ 1,23').

DISCRIMINATION: weak.diff places the R1 zeroing AFTER/inside the else-branch of the >200-digit exponential check (a naive reading that only zeroes 'normal' magnitudes). It is REJECTED by probe_1 (1e-200 still '1.00e-200' — that value's abs(exp)+len(digits) exceeds 200 so it takes the exponential branch and never reaches the misplaced check) and by probe_4 (1.234e-300 renders exponential instead of '0.000', the exact gold F2P discriminator). probes 2/3/5/6 pass under weak.diff, confirming the suite isolates the R1.5 ordering requirement rather than blanket-passing. So the requirements (specifically R1.5's 'before any decision about using exponential notation') correctly forbid the lazy fix that would fail the hidden tests.

Initial probe_4 authoring error: I first encoded expected '1.234e-300' from the test-patched file view; the gold test_patch actually changes it to '0.000'. Corrected before submission; both patched-holds and weak-rejects confirmed after correction.

Note (context, not part of this gate): meta.json records G-PANEL-3 (leakage) = fail because the EuroDecimal '€ 1,23' fixture in the spec is not derivable from the public problem statement. That is a leakage concern, orthogonal to spec fidelity/too-weak; the G-EQ (spec-fidelity) verdict is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Base-vs-patched probe confirms the change site: at base commit Decimal('-1e-200') dp=2 renders '-1.00e-200' (exponential), while gold-patched renders '0.00' — the sole behavioral divergence, exactly the requirements' modeling boundary. Requirements correctly scope the adjustment to Decimal + decimal_pos not None, place it before the exponential cutoff (R2.3/R1.5), use strict-less-than with the boundary rendering its own digits (R1.4/R3.5), and leave all other formatting unchanged. No unfaithful mandate, forbidden-but-present behavior, wrong boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior only. All concrete examples (decimal_pos=2, 0.00, 0.01, 1.00e-200, order-of-10^-200) trace to the PUBLIC problem_statement, which already shows nformat(Decimal('1e-200'),'.',decimal_pos=2) -> '1.00e-200' and 1e-199 -> '0.00'. The gold's invented identifier `cutoff` never appears; the cutoff formula is rendered as a behavioral rule ('ten raised to the negative of the decimal places'), which is legitimate spec translation. The single changed test parametrization ('0.'+'0'*299+'1234', 3, '0.000') is NOT reproduced: the doc never cites the '1234' coefficient or the 300-digit construction, only generic 'order of 10^-200/10^-300' magnitudes. No test file path, no test function/class names (test_decimal_numbers, test_decimal_subclass), no parametrization ids, no quoted test/gold lines. The '~200 total digits' cutoff (Req 2) and the decimal_pos=0 -> 0.1 edge (Req 1.3) describe the gold algorithm / pre-existing behavior for localization, not test cases. Naming the module/function is legitimate localization. Requirements are general behavioral acceptance criteria, not a mirror of the test's case list.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
