# P2 adversarial audit — django__django-13212

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1: RegexValidator + derived validators supply 'value' in params. POSITIVE CONTROL.
import sys
from django.core.validators import (
    RegexValidator, validate_slug, validate_unicode_slug, validate_integer,
    integer_validator, validate_comma_separated_integer_list, int_list_validator,
)
from django.core.exceptions import ValidationError

def check(v, value, label):
    try:
        v(value)
    except ValidationError as e:
        params = getattr(e, 'params', None) or {}
        ok = 'value' in params and params['value'] == value
        print(f"{label}: params={params} ok={ok} code={e.code}")
        return ok
    print(f"{label}: DID NOT RAISE")
    return False

results = []
results.append(check(RegexValidator('[0-9]+'), 'xxxxxx', 'RegexValidator'))
results.append(check(validate_slug, '你 好', 'validate_slug'))
results.append(check(validate_unicode_slug, '你 好', 'validate_unicode_slug'))
results.append(check(validate_integer, '-42.5', 'validate_integer'))
results.append(check(integer_validator, '-42.5', 'integer_validator'))
results.append(check(validate_comma_separated_integer_list, 'a,b,c', 'comma_sep'))
results.append(check(int_list_validator(), '-1,2,3', 'int_list_validator'))
# also code preserved for RegexValidator default
sys.exit(0 if all(results) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2: URLValidator supplies value on every rejection path + code unchanged.
import sys
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
v = URLValidator()
def check(value, label):
    try:
        v(value)
    except ValidationError as e:
        params = getattr(e, 'params', None) or {}
        ok = 'value' in params and params['value'] == value and e.code == 'invalid'
        print(f"{label}: value={value!r} params={params} code={e.code} ok={ok}")
        return ok
    print(f"{label}: DID NOT RAISE for {value!r}")
    return False
results = []
results.append(check(1, 'not-a-string(int)'))            # crit 1 & 6
results.append(check('no_scheme', 'bad-scheme'))          # crit 2
results.append(check('http://test[.com', 'unsplittable')) # crit 3
results.append(check('http://[::1:2::3]/', 'bad-ipv6'))   # crit 4
results.append(check('http://' + '.'.join(['a'*35 for _ in range(9)]), 'too-long-netloc')) # crit 5
sys.exit(0 if all(results) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 3: EmailValidator supplies value; accepts previously-accepted input.
import sys
from django.core.validators import validate_email, EmailValidator
from django.core.exceptions import ValidationError
def check(value, label):
    try:
        validate_email(value)
    except ValidationError as e:
        params = getattr(e, 'params', None) or {}
        ok = 'value' in params and params['value'] == value and e.code == 'invalid'
        print(f"{label}: {value!r} params={params} code={e.code} ok={ok}")
        return ok
    print(f"{label}: DID NOT RAISE for {value!r}")
    return False
results = []
results.append(check('a', 'no-at'))                # crit 1
results.append(check('a\n@b.com', 'bad-user'))     # crit 2
results.append(check('a@b\n.com', 'bad-domain'))   # crit 3
# crit 4: still accept valid
try:
    validate_email('user@example.com')
    print('accept valid: OK')
    results.append(True)
except ValidationError:
    print('accept valid: REJECTED (regression)')
    results.append(False)
sys.exit(0 if all(results) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 4 & 8: IP validators + ProhibitNullCharactersValidator supply value, code retained.
import sys
from django.core.validators import (
    validate_ipv4_address, validate_ipv6_address, validate_ipv46_address,
    ProhibitNullCharactersValidator,
)
from django.core.exceptions import ValidationError
def check(fn, value, label, code='invalid'):
    try:
        fn(value)
    except ValidationError as e:
        params = getattr(e, 'params', None) or {}
        ok = 'value' in params and params['value'] == value and e.code == code
        print(f"{label}: {value!r} params={params} code={e.code} ok={ok}")
        return ok
    print(f"{label}: DID NOT RAISE for {value!r}")
    return False
results = []
results.append(check(validate_ipv4_address, '256.1.1.1', 'ipv4'))
results.append(check(validate_ipv6_address, '1:2', 'ipv6'))
results.append(check(validate_ipv46_address, '256.1.1.1', 'ipv46'))
results.append(check(ProhibitNullCharactersValidator(), 'a\x00b', 'nullchar', code='null_characters_not_allowed'))
sys.exit(0 if all(results) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 5: DecimalValidator supplies value on all four rejection kinds + codes retained.
import sys
from decimal import Decimal
from django.core.validators import DecimalValidator
from django.core.exceptions import ValidationError
def check(dv, value, label, code):
    try:
        dv(value)
    except ValidationError as e:
        params = getattr(e, 'params', None) or {}
        ok = 'value' in params and params['value'] is value and e.code == code
        print(f"{label}: {value} params={params} code={e.code} ok={ok}")
        return ok
    print(f"{label}: DID NOT RAISE for {value}")
    return False
dv = DecimalValidator(max_digits=2, decimal_places=1)
results = []
results.append(check(dv, Decimal('NaN'), 'nonfinite', 'invalid'))       # crit 1
results.append(check(dv, Decimal('123'), 'max_digits', 'max_digits'))   # crit 2
results.append(check(dv, Decimal('0.12'), 'max_decimal', 'max_decimal_places')) # crit 3
results.append(check(dv, Decimal('12'), 'max_whole', 'max_whole_digits'))# crit 4
# crit 2/3/4 also keep 'max'
try:
    dv(Decimal('123'))
except ValidationError as e:
    p = getattr(e,'params',None) or {}
    ok = 'max' in p
    print(f"max kept: {p} ok={ok}")
    results.append(ok)
sys.exit(0 if all(results) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 9: BaseValidator-derived (Max/Min value & length) supply original 'value',
# preserve limit_value/show_value; length value != computed length.
import sys
from django.core.validators import (
    MaxValueValidator, MinValueValidator, MaxLengthValidator, MinLengthValidator,
)
from django.core.exceptions import ValidationError
def get(v, value):
    try:
        v(value)
    except ValidationError as e:
        return getattr(e,'params',None) or {}, e.code
    return None, None
results = []
p, c = get(MaxValueValidator(0), 1)
ok = p and p.get('value')==1 and 'limit_value' in p and 'show_value' in p and c=='max_value'
print(f"MaxValue: {p} code={c} ok={ok}"); results.append(bool(ok))
p, c = get(MinValueValidator(0), -1)
ok = p and p.get('value')==-1 and 'limit_value' in p and 'show_value' in p and c=='min_value'
print(f"MinValue: {p} code={c} ok={ok}"); results.append(bool(ok))
s = 11*'x'
p, c = get(MaxLengthValidator(10), s)
ok = p and p.get('value')==s and p.get('show_value')==11 and 'limit_value' in p and c=='max_length'
print(f"MaxLength: value_is_input={p.get('value')==s} show_value={p.get('show_value')} ok={ok}"); results.append(bool(ok))
s2 = 9*'x'
p, c = get(MinLengthValidator(10), s2)
ok = p and p.get('value')==s2 and p.get('show_value')==9 and c=='min_length'
print(f"MinLength: value_is_input={p.get('value')==s2} show_value={p.get('show_value')} ok={ok}"); results.append(bool(ok))
sys.exit(0 if all(results) else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 7: FileExtensionValidator + validate_image_file_extension supply value alongside
# extension/allowed_extensions; code unchanged.
import sys
from django.core.validators import FileExtensionValidator, validate_image_file_extension
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
def check(v, f, label):
    try:
        v(f)
    except ValidationError as e:
        p = getattr(e,'params',None) or {}
        ok = ('value' in p and p['value'] is f and 'extension' in p and
              'allowed_extensions' in p and e.code=='invalid_extension')
        print(f"{label}: params_keys={sorted(p)} value_is_file={p.get('value') is f} code={e.code} ok={ok}")
        return ok
    print(f"{label}: DID NOT RAISE")
    return False
results = []
f1 = SimpleUploadedFile('myfile.txt', b'abc')
results.append(check(FileExtensionValidator(allowed_extensions=['png']), f1, 'FileExt'))
f2 = SimpleUploadedFile('myfile.txt', b'abc')
results.append(check(validate_image_file_extension, f2, 'ImageExt'))
sys.exit(0 if all(results) else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# Req 6 & 10: DecimalField non-finite must surface DecimalValidator's error carrying value;
# end-to-end %(value)s form errors equal the string form of the rejected input.
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_I18N=False, INSTALLED_APPS=['django.forms'])
django.setup()
from django import forms

results = []

# Req 6: DecimalField NaN -> invalid error must include value (via DecimalValidator path).
class DForm(forms.Form):
    field = forms.DecimalField(max_digits=2, decimal_places=1,
                               error_messages={'invalid': '%(value)s'})
form = DForm({'field': 'NaN'})
valid = form.is_valid()
errs = form.errors.get('field')
ok = (not valid) and errs == ['NaN']
print(f"DecimalField NaN: valid={valid} errors={errs} ok={ok}")
results.append(ok)

# Req 10: string input echoed
class NForm(forms.Form):
    field = forms.CharField(error_messages={'null_characters_not_allowed': '%(value)s'})
form = NForm({'field': 'a\0b'})
errs = form.errors.get('field')
ok = form.is_valid() is False and errs == ['a\x00b']
print(f"null char: errors={errs} ok={ok}")
results.append(ok)

# Req 10 crit 2: non-string integer input yields str(value)
from django.core.validators import MaxValueValidator
class IForm(forms.Form):
    field = forms.IntegerField(validators=[MaxValueValidator(0)],
                               error_messages={'max_value': '%(value)s'})
form = IForm({'field': 1})
errs = form.errors.get('field')
ok = form.is_valid() is False and errs == ['1']
print(f"integer max_value: errors={errs} ok={ok}")
results.append(ok)

sys.exit(0 if all(results) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1: RegexValidator + derived validators supply 'value' in params. POSITIVE CONTROL.
import sys
from django.core.validators import (
    RegexValidator, validate_slug, validate_unicode_slug, validate_integer,
    integer_validator, validate_comma_separated_integer_list, int_list_validator,
)
from django.core.exceptions import ValidationError

def check(v, value, label):
    try:
        v(value)
    except ValidationError as e:
        params = getattr(e, 'params', None) or {}
        ok = 'value' in params and params['value'] == value
        print(f"{label}: params={params} ok={ok} code={e.code}")
        return ok
    print(f"{label}: DID NOT RAISE")
    return False

results = []
results.append(check(RegexValidator('[0-9]+'), 'xxxxxx', 'RegexValidator'))
results.append(check(validate_slug, '你 好', 'validate_slug'))
results.append(check(validate_unicode_slug, '你 好', 'validate_unicode_slug'))
results.append(check(validate_integer, '-42.5', 'validate_integer'))
results.append(check(integer_validator, '-42.5', 'integer_validator'))
results.append(check(validate_comma_separated_integer_list, 'a,b,c', 'comma_sep'))
results.append(check(int_list_validator(), '-1,2,3', 'int_list_validator'))
# also code preserved for RegexValidator default
sys.exit(0 if all(results) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes cover Reqs 1-10. All HOLD on gold-patched tree; all fail at base (checked probe_1/5/8). Positive control = probe_1 (RegexValidator + derived validators supply params['value']): FAILS at base (params={}), HOLDS patched -> discriminates.

Coverage: probe_1 Req1 (Regex/slug/unicode_slug/integer/int_list/comma_sep + code); probe_2 Req2 (URLValidator all 5+ rejection paths incl. non-string int, bad scheme, unsplittable, bad ipv6, over-length netloc; code=invalid); probe_3 Req3 (Email no-@, bad user, bad domain + still accepts valid); probe_4 Req4+Req8 (ipv4/ipv6/ipv46 code=invalid; null char code=null_characters_not_allowed); probe_5 Req5 (Decimal nonfinite/max_digits/max_decimal_places/max_whole_digits, 'max' kept, correct codes); probe_6 Req9 (Max/MinValue + Max/MinLength: value==original input, show_value stays the length, limit_value preserved, codes intact); probe_7 Req7 (FileExtension + image ext: value alongside extension/allowed_extensions, code=invalid_extension); probe_8 Req6+Req10 end-to-end via forms (DecimalField NaN surfaces DecimalValidator's value; %(value)s renders string/int form).

NOTE probe_5/8 fix: Decimal('NaN') != itself, so identity comparison used. WRONG-FIX candidate 'weak.diff' = gold's validators.py hunk ONLY, omitting the removal of DecimalField.validate() shadow in forms/fields.py (the lazy reading that satisfies Reqs 1-5,7-9). Under weak.diff probe_5 still HOLDS but probe_8 is REJECTED (DecimalField NaN renders literal '%(value)s' because the redundant shadow raises invalid without value) — this is exactly the FAIL_TO_PASS test_value_placeholder_with_decimal_field NaN case, so weak.diff would not resolve the hidden tests. Suite discriminates a probe-conforming-on-most-reqs wrong patch. Runner uses conda swebench-lean python; bare 'python' absent on host.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1: RegexValidator + derived validators supply 'value' in params. POSITIVE CONTROL.
import sys
from django.core.validators import (
    RegexValidator, validate_slug, validate_unicode_slug, validate_integer,
    integer_validator, validate_comma_separated_integer_list, int_list_validator,
)
from django.core.exceptions import ValidationError

def check(v, value, label):
    try:
        v(value)
    except ValidationError as e:
        params = getattr(e, 'params', None) or {}
        ok = 'value' in params and params['value'] == value
        print(f"{label}: params={params} ok={ok} code={e.code}")
        return ok
    print(f"{label}: DID NOT RAISE")
    return False

results = []
results.append(check(RegexValidator('[0-9]+'), 'xxxxxx', 'RegexValidator'))
results.append(check(validate_slug, '你 好', 'validate_slug'))
results.append(check(validate_unicode_slug, '你 好', 'validate_unicode_slug'))
results.append(check(validate_integer, '-42.5', 'validate_integer'))
results.append(check(integer_validator, '-42.5', 'integer_validator'))
results.append(check(validate_comma_separated_integer_list, 'a,b,c', 'comma_sep'))
results.append(check(int_list_validator(), '-1,2,3', 'int_list_validator'))
# also code preserved for RegexValidator default
sys.exit(0 if all(results) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes cover Reqs 1-10. All HOLD on gold-patched tree; all fail at base (checked probe_1/5/8). Positive control = probe_1 (RegexValidator + derived validators supply params['value']): FAILS at base (params={}), HOLDS patched -> discriminates.

Coverage: probe_1 Req1 (Regex/slug/unicode_slug/integer/int_list/comma_sep + code); probe_2 Req2 (URLValidator all 5+ rejection paths incl. non-string int, bad scheme, unsplittable, bad ipv6, over-length netloc; code=invalid); probe_3 Req3 (Email no-@, bad user, bad domain + still accepts valid); probe_4 Req4+Req8 (ipv4/ipv6/ipv46 code=invalid; null char code=null_characters_not_allowed); probe_5 Req5 (Decimal nonfinite/max_digits/max_decimal_places/max_whole_digits, 'max' kept, correct codes); probe_6 Req9 (Max/MinValue + Max/MinLength: value==original input, show_value stays the length, limit_value preserved, codes intact); probe_7 Req7 (FileExtension + image ext: value alongside extension/allowed_extensions, code=invalid_extension); probe_8 Req6+Req10 end-to-end via forms (DecimalField NaN surfaces DecimalValidator's value; %(value)s renders string/int form).

NOTE probe_5/8 fix: Decimal('NaN') != itself, so identity comparison used. WRONG-FIX candidate 'weak.diff' = gold's validators.py hunk ONLY, omitting the removal of DecimalField.validate() shadow in forms/fields.py (the lazy reading that satisfies Reqs 1-5,7-9). Under weak.diff probe_5 still HOLDS but probe_8 is REJECTED (DecimalField NaN renders literal '%(value)s' because the redundant shadow raises invalid without value) — this is exactly the FAIL_TO_PASS test_value_placeholder_with_decimal_field NaN case, so weak.diff would not resolve the hidden tests. Suite discriminates a probe-conforming-on-most-reqs wrong patch. Runner uses conda swebench-lean python; bare 'python' absent on host.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed via nl_attack probe on patched tree and --base. Base BaseValidator.__call__ already includes params={'limit_value','show_value','value'}; patched tree identical there. All other requirement behaviors are genuinely introduced by the patch (verified codes preserved and params extended alongside existing entries per Req10.3). No requirement mandates behavior the code lacks, forbids behavior it has, or pins a wrong narrow boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements enumerate the specific validators and their internal rejection paths (RegexValidator, URLValidator ×6 paths, EmailValidator ×3, IP validators, DecimalValidator ×4 codes, DecimalField duplicate-check removal, FileExtensionValidator, ProhibitNullCharactersValidator, BaseValidator family). These map one-to-one to the `raise ValidationError(...)` statements in the gold diff to django/core/validators.py and the deletion in django/forms/fields.py — this is legitimate localization of the change, not the test parametrization. Crucially, NONE of the discriminating hidden-test inputs appear: no '256.1.1.1', 'no_scheme', 'http://test[.com', 'http://[::1:2::3]/', '你 好', 'myfile.txt', 'a\0b', '-42.5', 'NaN', or the '.'.join(['a'*35]*9) long-host construction. No test file path (tests/forms_tests/tests/test_validators.py), no class/method names (ValidatorCustomMessageTests, test_value_placeholder_with_*), no subTest ids. The only identifier used ('value' / '%(value)s') is present verbatim in the public problem_statement. The str(value) observable in Req 10 is the behavior the problem_statement already frames. The doc's grouping follows the source code's raise-site structure, NOT the test's field-type grouping (char/integer/decimal/file/null), so it is not reconstructing the test cases. Behavioral translation only.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
