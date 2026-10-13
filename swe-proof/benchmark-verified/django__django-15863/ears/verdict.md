# P2 adversarial audit — django__django-15863

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2/1.3 + positive control: exact preservation of high-precision Decimal
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_TZ=False, INSTALLED_APPS=[])
    django.setup()
from decimal import Decimal
from django.template.defaultfilters import floatformat

val = Decimal('42.12345678901234567890')
got = floatformat(val, 20)
want = '42.12345678901234567890'
print("input=", val, "arg=20 -> got=", got, "want=", want)
assert got == want, f"expected {want}, got {got}"
print("OK exact preservation")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.4 / 2.2: round the EXACT Decimal (half up) when p < fractional digits.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_TZ=False, INSTALLED_APPS=[])
    django.setup()
from decimal import Decimal
from django.template.defaultfilters import floatformat

# Digit at rounding boundary requires exact value; float approx would corrupt it.
cases = [
    (Decimal('42.12345678901234567890'), 2, '42.12'),
    (Decimal('0.125'), 2, '0.13'),   # round half up on exact
    (Decimal('2.5'), 0, '3'),
]
for v, p, want in cases:
    got = floatformat(v, p)
    print(f"floatformat({v!r},{p}) = {got!r} want {want!r}")
    assert got == want, f"{v} p={p}: expected {want}, got {got}"
print("OK exact rounding")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1/2.5/2.4: float + numeric-string formatting unchanged; float-convertible objects.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_TZ=False, INSTALLED_APPS=[])
    django.setup()
from django.template.defaultfilters import floatformat

class F:
    def __float__(self): return 7.55

cases = [
    (7.7, 0, '8'),
    (7.0, 0, '7'),
    (0.7, -1, '0.7'),
    (7.7, -1, '7.7'),
    (7.0, -1, '7'),        # negative/default drops trailing zeros -> integer
    (7.7, None, '7.7'),    # omitted arg == -1
    ("foo", -1, ''),       # non-numeric -> empty
    (34.23234, 3, '34.232'),
    (F(), 1, '7.6'),       # float-convertible object -> half-up round of 7.55
    ('7.7', 0, '8'),       # numeric string
]
for v, p, want in cases:
    got = floatformat(v) if p is None else floatformat(v, p)
    print(f"floatformat({v!r},{p}) = {got!r} want {want!r}")
    assert got == want, f"{v!r} p={p}: expected {want!r}, got {got!r}"
print("OK float/string/regression behavior")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2/3.3/3.4: invalid arg, special values, zero / -0 handling.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_TZ=False, INSTALLED_APPS=[])
    django.setup()
from decimal import Decimal
from django.template.defaultfilters import floatformat

# 3.2: bad arg -> textual input unchanged
assert floatformat(13.1234, "bar") == "13.1234", floatformat(13.1234, "bar")
# 3.3: inf / nan
assert floatformat(float("inf")) == "inf", floatformat(float("inf"))
assert floatformat(float("-inf")) == "-inf", floatformat(float("-inf"))
assert floatformat(float("nan")) == "nan", floatformat(float("nan"))
# 3.4: zero without negative sign
assert floatformat(0, 6) == "0.000000", floatformat(0, 6)
# 3.4: negative rounding to zero -> no spurious -0
assert floatformat(-0.1, 0) == "0", floatformat(-0.1, 0)
assert floatformat(-0.01, 1) == "0.0", floatformat(-0.01, 1)
# 3.1 non-numeric -> empty
assert floatformat("abc") == "", floatformat("abc")
print("OK special/invalid/zero handling")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4.1-4.4: g/u/gu/ug suffixes and bare-suffix default place count.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_L10N=True, USE_TZ=False, INSTALLED_APPS=[])
    django.setup()
from django.template.defaultfilters import floatformat
from django.utils import translation

# 4.1 g grouping honors active locale thousand separator
with translation.override("en"):
    assert floatformat(10000, "g") == "10,000", floatformat(10000, "g")
    assert floatformat(66666.666, "1g") == "66,666.7", floatformat(66666.666, "1g")
with translation.override("de"):
    assert floatformat(10000, "g") == "10.000", floatformat(10000, "g")
    assert floatformat(66666.666, "1g") == "66.666,7", floatformat(66666.666, "1g")

# 4.2 u unlocalizes: period decimal separator regardless of locale
with translation.override("de"):
    assert floatformat(66666.666, "2") == "66666,67", floatformat(66666.666, "2")
    assert floatformat(66666.666, "2u") == "66666.67", floatformat(66666.666, "2u")

# 4.3 combined gu/ug accepted (both grouping+unlocalize; here no sep shown w/o
# THOUSAND_SEPARATOR setting, but must not error and must use period decimal)
with translation.override("de"):
    assert floatformat(66666.666, "2gu") == "66666.67", floatformat(66666.666, "2gu")
    assert floatformat(66666.666, "2ug") == "66666.67", floatformat(66666.666, "2ug")

# 4.4 bare u/g with no leading digits -> default place count (-1)
with translation.override("de"):
    # default place count is -1 (show 1 place when fractional part exists)
    assert floatformat(66666.666, "u") == "66666.7", floatformat(66666.666, "u")
print("OK grouping/unlocalize suffixes")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1/1.2/1.3 + positive control: exact preservation of high-precision Decimal
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_TZ=False, INSTALLED_APPS=[])
    django.setup()
from decimal import Decimal
from django.template.defaultfilters import floatformat

val = Decimal('42.12345678901234567890')
got = floatformat(val, 20)
want = '42.12345678901234567890'
print("input=", val, "arg=20 -> got=", got, "want=", want)
assert got == want, f"expected {want}, got {got}"
print("OK exact preservation")
```

Prepatch bug re-encoded as an attack: `True`.

Fix is repr(text)->str(text) in floatformat: Decimal repr 'Decimal(...)' fails to parse, falls back to lossy float(); str() gives an exact-parseable decimal string.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2/1.3, POSITIVE CONTROL): floatformat(Decimal('42.12345678901234567890'),20)=='42.12345678901234567890'. HOLDS patched, FAILS at base (base got '42.12345678901234400000' — binary-float corruption). Discriminates.
- probe_2 (Req 1.4/2.2): p<fractional digits rounds the EXACT decimal half-up (42.123...->'42.12', 0.125->'0.13', 2.5->'3'). HOLDS.
- probe_3 (Req 2.1/2.4/2.5/3.1): float rounding, negative/default trailing-zero drop, omitted arg==-1, float-convertible object (7.55->'7.6'), numeric string, non-numeric->''. HOLDS.
- probe_4 (Req 3.1/3.2/3.3/3.4): bad arg returns input text; inf/-inf/nan strings; 0 with places no sign; -0.1->'0' no spurious -0. HOLDS.
- probe_5 (Req 4.1-4.4): g grouping per en/de locale, u unlocalize (de comma->period), gu/ug combined, bare-u default -1. HOLDS.

Candidate patch weak.diff (repr(float(text))): a plausible-wrong fix that still routes through binary float. Probe suite REJECTS it — probe_1 fails (precision loss), probe_3 & probe_4 fail (float('foo') raises ValueError not caught, breaks non-numeric->'' contract). Demonstrates the suite discriminates wrong implementations.

>=5 distinct probes all hold on patched; positive control fails at base (prepatch reproduced). SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1/1.2/1.3 + positive control: exact preservation of high-precision Decimal
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_TZ=False, INSTALLED_APPS=[])
    django.setup()
from decimal import Decimal
from django.template.defaultfilters import floatformat

val = Decimal('42.12345678901234567890')
got = floatformat(val, 20)
want = '42.12345678901234567890'
print("input=", val, "arg=20 -> got=", got, "want=", want)
assert got == want, f"expected {want}, got {got}"
print("OK exact preservation")
```

Prepatch bug re-encoded as an attack: `True`.

Fix is repr(text)->str(text) in floatformat: Decimal repr 'Decimal(...)' fails to parse, falls back to lossy float(); str() gives an exact-parseable decimal string.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2/1.3, POSITIVE CONTROL): floatformat(Decimal('42.12345678901234567890'),20)=='42.12345678901234567890'. HOLDS patched, FAILS at base (base got '42.12345678901234400000' — binary-float corruption). Discriminates.
- probe_2 (Req 1.4/2.2): p<fractional digits rounds the EXACT decimal half-up (42.123...->'42.12', 0.125->'0.13', 2.5->'3'). HOLDS.
- probe_3 (Req 2.1/2.4/2.5/3.1): float rounding, negative/default trailing-zero drop, omitted arg==-1, float-convertible object (7.55->'7.6'), numeric string, non-numeric->''. HOLDS.
- probe_4 (Req 3.1/3.2/3.3/3.4): bad arg returns input text; inf/-inf/nan strings; 0 with places no sign; -0.1->'0' no spurious -0. HOLDS.
- probe_5 (Req 4.1-4.4): g grouping per en/de locale, u unlocalize (de comma->period), gu/ug combined, bare-u default -1. HOLDS.

Candidate patch weak.diff (repr(float(text))): a plausible-wrong fix that still routes through binary float. Probe suite REJECTS it — probe_1 fails (precision loss), probe_3 & probe_4 fail (float('foo') raises ValueError not caught, breaks non-numeric->'' contract). Demonstrates the suite discriminates wrong implementations.

>=5 distinct probes all hold on patched; positive control fails at base (prepatch reproduced). SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is the single-line coercion change repr(text) -> str(text) in floatformat. The changed observable behavior is exact-value preservation for Decimal inputs, which Requirement 1 pins directly and biconditionally (base twin diverges: base probe exits 1 on the exact-Decimal assertion). Requirements 2-4 correctly fence the UNCHANGED behaviors (float rounding, special values, sign, non-numeric, bad-arg, locale suffixes) as invariants of the fix. The modeling boundary is correct: it targets the coercion step / observable output, not a narrow branch. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The only concrete numeric example in requirements.md (Decimal('42.12345678901234567890') @ 20 places -> 42.12345678901234400000) is copied directly from the PUBLIC problem_statement's MWE, so it is not leaked. The hidden test's distinguishing fixture (Decimal('123456.123456789012345678901') @ 21 -> exact) never appears. No test names (test_inputs), file paths (tests/template_tests/filter_tests/test_floatformat.py), parametrization ids, or quoted gold code appear. The gold edit is repr(text)->str(text); the doc describes the behavior ('not route through a binary floating-point approximation') without naming the str() call or any fix-invented identifier. Module/function localization (defaultfilters.py, floatformat(text, arg=-1)) is legitimate. The Req 2-4 acceptance criteria (float rounding, g/u suffixes, infinity/NaN, zero/-0) map to documented filter behavior and PASS_TO_PASS coverage in a behavioral, non-test-shaped way.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
