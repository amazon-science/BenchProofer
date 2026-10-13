# P2 adversarial audit — django__django-16485

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
reject.diff (wrap the quantize call in try/except ValueError -> return input_val) crashes-avoidance without the short-circuit: floatformat('0.00',0) and floatformat(Decimal('0.00'),0) both return '0.00' instead of the mandated '0'. probe_1 and probe_2 REJECT it, demonstrating the suite discriminates a wrong fix.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1.2: floatformat("0.00", 0) SHALL return "0" (positive control candidate)
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False, INSTALLED_APPS=[])
django.setup()
from django.template.defaultfilters import floatformat

try:
    got = floatformat("0.00", 0)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("floatformat('0.00', 0) =", repr(got))
sys.exit(0 if got == "0" else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.3: floatformat(Decimal("0.00"), 0) SHALL return "0"
import sys
from decimal import Decimal
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False, INSTALLED_APPS=[])
django.setup()
from django.template.defaultfilters import floatformat

try:
    got = floatformat(Decimal("0.00"), 0)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("floatformat(Decimal('0.00'), 0) =", repr(got))
sys.exit(0 if got == "0" else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.1/1.4: whole nonzero value with place count 0 renders bare integer, no exception, no ValueError
import sys
from decimal import Decimal
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False, INSTALLED_APPS=[])
django.setup()
from django.template.defaultfilters import floatformat

cases = [
    ("7.00", "7"),
    (Decimal("42.000"), "42"),
    ("123.0", "123"),
    (Decimal("-5.00"), "-5"),
]
ok = True
for val, exp in cases:
    try:
        got = floatformat(val, 0)
    except Exception as e:
        print("RAISED for", repr(val), ":", type(e).__name__, e)
        ok = False
        continue
    print("floatformat(%r, 0) = %r (expect %r)" % (val, got, exp))
    if got != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2: regression - negative counts, fractional rounding half-up, positive padding, default -1
import sys
from decimal import Decimal
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False, INSTALLED_APPS=[])
django.setup()
from django.template.defaultfilters import floatformat

cases = [
    # (value, arg, expected)
    ("7.00", -1, "7"),          # 2.1 whole + negative -> integer
    (Decimal("34.00000"), -3, "34"),  # 2.1
    ("34.23234", 3, "34.232"),  # 2.2 fractional rounded to abs(count)
    ("34.23234", -3, "34.232"), # 2.2 sign of count doesn't matter for fractional
    ("7", 2, "7.00"),           # 2.3 whole + positive -> trailing zeros
    ("2.5", 0, "3"),            # 2.4 round half away from zero -> 3
    ("1.5", 0, "2"),            # round half away from zero
    (34.23234, None, "34.2"),   # 2.5 default -1
    (34.00000, None, "34"),     # 2.5 default drops fractional when whole
    ("0.00", -1, "0"),          # negative zero-ish
]
ok = True
for val, arg, exp in cases:
    if arg is None:
        got = floatformat(val)
    else:
        got = floatformat(val, arg)
    print("floatformat(%r, %r) = %r (expect %r)" % (val, arg, got, exp))
    if got != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3: suffixes (g/u/gu), bad arg returns input, bad value returns "", inf/nan, negative zero
import sys
from decimal import Decimal
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_L10N=True, USE_TZ=False, INSTALLED_APPS=[])
django.setup()
from django.template.defaultfilters import floatformat
from django.utils import translation

ok = True
def check(desc, got, exp):
    global ok
    print("%s = %r (expect %r)" % (desc, got, exp))
    if got != exp:
        ok = False

# 3.4 non-integer arg -> return original input value
check("floatformat('1.23', 'foo')", floatformat("1.23", "foo"), "1.23")
# 3.5 non-numeric value -> ""
check("floatformat('abc', 2)", floatformat("abc", 2), "")
check("floatformat(None, 2)", floatformat(None, 2), "")
# 3.6 inf / nan -> string repr, not numeric rounding
check("floatformat('inf', 2)", floatformat("inf", 2), "inf")
check("floatformat('nan', 2)", floatformat("nan", 2), "nan")
# 3.7 negative zero should not have spurious sign
check("floatformat('-0.0', 0)", floatformat("-0.0", 0), "0")
check("floatformat(Decimal('-0.00'), 0)", floatformat(Decimal("-0.00"), 0), "0")

# 3.1 grouping suffix 'g' forces thousand grouping
with translation.override("en"):
    check("floatformat('1234.5', '2g')", floatformat("1234.5", "2g"), "1,234.50")
    # 3.2 unlocalize suffix 'u'
    # with l10n active, comma grouping off by u
    check("floatformat('1234.5', '2u')", floatformat("1234.5", "2u"), "1234.50")

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.2: floatformat("0.00", 0) SHALL return "0" (positive control candidate)
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False, INSTALLED_APPS=[])
django.setup()
from django.template.defaultfilters import floatformat

try:
    got = floatformat("0.00", 0)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("floatformat('0.00', 0) =", repr(got))
sys.exit(0 if got == "0" else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirement: floatformat whole-value short-circuit must apply for place count <=0 (was <0). Gold patch changes `p < 0` to `p <= 0`.

Probes (all run in the official image; runner re-executes):
- probe_1 (Req 1.2): floatformat('0.00',0)=='0'. PATCHED: HOLDS. BASE: FAILS. POSITIVE CONTROL — discriminates.
- probe_2 (Req 1.3): floatformat(Decimal('0.00'),0)=='0'. PATCHED HOLDS; BASE FAILS (same ValueError).
- probe_3 (Req 1.1/1.4): whole nonzero values ('7.00','123.0',Decimal('42.000'),Decimal('-5.00')) at p=0 render bare int, no exception. PATCHED HOLDS. (Also holds at base — these did not hit prec=0, so not a control.)
- probe_4 (Req 2.1-2.5): regression — whole+negative->int, fractional rounded to abs(count) regardless of sign, whole+positive trailing zeros, ROUND_HALF_UP (2.5->3,1.5->2), default arg -1. PATCHED HOLDS.
- probe_5 (Req 3.1-3.7): g/u suffixes force grouping/unlocalize, non-integer arg returns input unchanged, non-numeric/None value returns '', inf/nan return string repr, negative-zero renders '0' without spurious sign. PATCHED HOLDS.

Candidate patches (both apply at base_commit):
- reject.diff: try/except around quantize returning input_val. REJECTED by probe_1 & probe_2 (returns '0.00'). Proves suite has discriminating power against a plausibly-lazy fix.
- weak.diff: prec=max(1, abs(p)+units+1). Passes ALL 5 probes. Routes p=0 whole values through the general path but still yields '0'. I believe this is a genuinely-correct ALTERNATIVE fix (not too-weak) and expect it to resolve the official harness; submitting so the runner can confirm. If it does NOT resolve, this is a TOO-WEAK finding.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, positive control (probe_1) holds patched and fails at base (prepatch reproduced), and at least one candidate (reject.diff) is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
reject.diff (wrap the quantize call in try/except ValueError -> return input_val) crashes-avoidance without the short-circuit: floatformat('0.00',0) and floatformat(Decimal('0.00'),0) both return '0.00' instead of the mandated '0'. probe_1 and probe_2 REJECT it, demonstrating the suite discriminates a wrong fix.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.2: floatformat("0.00", 0) SHALL return "0" (positive control candidate)
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False, INSTALLED_APPS=[])
django.setup()
from django.template.defaultfilters import floatformat

try:
    got = floatformat("0.00", 0)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("floatformat('0.00', 0) =", repr(got))
sys.exit(0 if got == "0" else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirement: floatformat whole-value short-circuit must apply for place count <=0 (was <0). Gold patch changes `p < 0` to `p <= 0`.

Probes (all run in the official image; runner re-executes):
- probe_1 (Req 1.2): floatformat('0.00',0)=='0'. PATCHED: HOLDS. BASE: FAILS. POSITIVE CONTROL — discriminates.
- probe_2 (Req 1.3): floatformat(Decimal('0.00'),0)=='0'. PATCHED HOLDS; BASE FAILS (same ValueError).
- probe_3 (Req 1.1/1.4): whole nonzero values ('7.00','123.0',Decimal('42.000'),Decimal('-5.00')) at p=0 render bare int, no exception. PATCHED HOLDS. (Also holds at base — these did not hit prec=0, so not a control.)
- probe_4 (Req 2.1-2.5): regression — whole+negative->int, fractional rounded to abs(count) regardless of sign, whole+positive trailing zeros, ROUND_HALF_UP (2.5->3,1.5->2), default arg -1. PATCHED HOLDS.
- probe_5 (Req 3.1-3.7): g/u suffixes force grouping/unlocalize, non-integer arg returns input unchanged, non-numeric/None value returns '', inf/nan return string repr, negative-zero renders '0' without spurious sign. PATCHED HOLDS.

Candidate patches (both apply at base_commit):
- reject.diff: try/except around quantize returning input_val. REJECTED by probe_1 & probe_2 (returns '0.00'). Proves suite has discriminating power against a plausibly-lazy fix.
- weak.diff: prec=max(1, abs(p)+units+1). Passes ALL 5 probes. Routes p=0 whole values through the general path but still yields '0'. I believe this is a genuinely-correct ALTERNATIVE fix (not too-weak) and expect it to resolve the official harness; submitting so the runner can confirm. If it does NOT resolve, this is a TOO-WEAK finding.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, positive control (probe_1) holds patched and fails at base (prepatch reproduced), and at least one candidate (reject.diff) is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed patched vs base with settings.configure(). Patched: '0.00'/0->'0', Decimal('0.00')/0->'0', '1.00'/0->'1', '1.5'/0->'2', '1.5'/-1->'1.5', '1'(default)->'1', '34.23234'/0->'34', '-0.0'/0->'0', '0.5'/0->'1', '2.5'/0->'3', '1.23'/2->'1.23'. Base identical except '0.00'/0 and Decimal('0.00')/0 raise ValueError. Confirms Req1 (crash fix), Req2 (rounding half-up, default -1, negative/positive counts preserved), Req3 (neg-zero no spurious sign). Modeling boundary is the changed observable behavior, not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The only concrete cases pinned (floatformat('0.00', 0) -> '0' and Decimal('0.00') with arg 0 -> '0', both raising the ValueError precision crash) are lifted directly from the PUBLIC problem_statement, which literally contains these two calls and the ValueError message. The gold one-liner (p < 0 -> p <= 0) is described behaviorally as extending the whole-value short-circuit to a non-positive (zero-or-negative) place count — legitimate localization of the change, not the diff itself. Naming the module/function (django/template/defaultfilters.py, floatformat(text, arg=-1)) is legitimate localization. Requirements 2-3 enumerate documented floatformat behaviors (negative places, positive rounding half-up, grouping 'g'/unlocalize 'u'/'gu'/'ug' suffixes, infinity/NaN, negative-zero) which loosely correspond to PASS_TO_PASS test function names, but these are public/documented filter behaviors described in prose, not verbatim test code, test paths, parametrization ids, or fix-invented identifiers. No hidden test file path, test/class/function name, or gold-patch line is transmitted beyond the public problem_statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
