# P2 adversarial audit — django__django-13512

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.1/1.3 (positive control): display_for_field on a non-ASCII JSONField value
# must return literal non-ASCII chars, not \uXXXX escapes.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.contrib.admin.utils import display_for_field
from django.db import models

f = models.JSONField()
val = {'greeting': '中国', 'list': ['jaźń']}
out = display_for_field(val, f, '-')
print('OUT:', repr(out))
ok = ('中国' in out) and ('jaźń' in out) and ('\\u' not in out)
# must still be valid JSON
import json
parsed = json.loads(out)
print('PARSED:', parsed)
assert parsed == val, 'roundtrip mismatch'
print('HOLDS' if ok else 'FAILS')
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2: ASCII JSONField value output unchanged == standard compact JSON serialization.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.contrib.admin.utils import display_for_field
from django.db import models
import json

f = models.JSONField()
for val in [{'a': 1, 'b': [1, 2, 3]}, [1, 2, {'x': 'y'}], 'hello', 42, True]:
    out = display_for_field(val, f, '-')
    # standard compact notation via the field's encoder (default None encoder == json.dumps default)
    expected = json.dumps(val, ensure_ascii=False, cls=f.encoder)
    print(repr(val), '->', repr(out), 'expected', repr(expected))
    assert out == expected, f'mismatch for {val!r}'
print('HOLDS')
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.4: unserializable JSONField value -> fall back to display_for_value, no raise.
# Req 1.6: None -> empty_value_display.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.contrib.admin.utils import display_for_field, display_for_value
from django.db import models

f = models.JSONField()

# Unserializable: keys that are not valid JSON object keys -> TypeError inside json.dumps
bad = {(1, 2): 'x'}
try:
    out = display_for_field(bad, f, '-')
except Exception as e:
    print('RAISED', repr(e)); import sys; sys.exit(1)
expected = display_for_value(bad, '-')
print('BAD OUT:', repr(out), 'expected fallback', repr(expected))
assert out == expected, 'did not fall back to display_for_value'

# None -> empty value display
out_none = display_for_field(None, f, 'EMPTY')
print('NONE OUT:', repr(out_none))
assert out_none == 'EMPTY', 'None not mapped to empty_value_display'
print('HOLDS')
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 1.5: display_for_field uses the field's custom encoder.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.contrib.admin.utils import display_for_field
from django.db import models
import json, datetime

class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return 'ENCODED_DATE'
        return super().default(o)

f = models.JSONField(encoder=MyEncoder)
val = {'d': datetime.date(2020, 1, 1), 'x': '中国'}
out = display_for_field(val, f, '-')
print('OUT:', repr(out))
# Without the custom encoder json.dumps would raise TypeError -> would fall back.
# With encoder honored, the date is serialized to ENCODED_DATE and non-ASCII preserved.
ok = ('ENCODED_DATE' in out) and ('中国' in out) and ('\\u' not in out)
print('HOLDS' if ok else 'FAILS')
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 2.1/2.2/2.3: forms JSONField.prepare_value preserves non-ASCII literally.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.forms.fields import JSONField
import json

f = JSONField()

# 2.2: bare string
s = f.prepare_value('中国')
print('STR:', repr(s))
assert s == '"中国"', f'string mismatch: {s!r}'

# 2.3: dict and list with non-ASCII
d = f.prepare_value({'a': '中国', 'b': 'jaźń'})
print('DICT:', repr(d))
assert '中国' in d and 'jaźń' in d and '\\u' not in d
assert json.loads(d) == {'a': '中国', 'b': 'jaźń'}

l = f.prepare_value(['你好，世界', 'jaźń'])
print('LIST:', repr(l))
assert '你好，世界' in l and 'jaźń' in l and '\\u' not in l

# emoji / multi-code-unit
e = f.prepare_value({'a': '😀🐱'})
print('EMOJI:', repr(e))
assert '😀🐱' in e and '\\u' not in e
print('HOLDS')
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 2.4: all-ASCII prepare_value unchanged; None -> 'null'; string double-quoted.
# Req 2.5: InvalidJSONInput passthrough. Req 2.6: custom encoder honored.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.forms.fields import JSONField
from django.forms.fields import InvalidJSONInput
import json, datetime

f = JSONField()
# 2.4
assert f.prepare_value(None) == 'null', f.prepare_value(None)
assert f.prepare_value('hello') == '"hello"'
assert f.prepare_value({'a': 1, 'b': 2}) == json.dumps({'a': 1, 'b': 2}, ensure_ascii=False)
print('ASCII ok')

# 2.5 InvalidJSONInput passthrough (str subclass)
bad = InvalidJSONInput('{not json')
out = f.prepare_value(bad)
print('INVALID:', repr(out))
assert out == bad and out is bad or out == '{not json'
assert out == '{not json', 'InvalidJSONInput not passed through unchanged'

# 2.6 custom encoder
class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return 'ENC_DATE'
        return super().default(o)
f2 = JSONField(encoder=MyEncoder)
out2 = f2.prepare_value({'d': datetime.date(2020,1,1), 'x': '中国'})
print('ENC:', repr(out2))
assert 'ENC_DATE' in out2 and '中国' in out2 and '\\u' not in out2
print('HOLDS')
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2: has_changed key-order-insensitive; True vs 1 changed; parsing valid/invalid.
# initial is a Python value; data is submitted text.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.forms.fields import JSONField
from django.core.exceptions import ValidationError

f = JSONField()
# equal JSON regardless of key ordering -> unchanged
assert f.has_changed({'a': 1, 'b': 2}, '{"b": 2, "a": 1}') is False, 'key order should be unchanged'
# True vs 1 -> changed
assert f.has_changed({'a': True}, '{"a": 1}') is True, 'True vs 1 should be changed'
print('has_changed ok')

# to_python: valid JSON accepted
assert f.to_python('{"x": 1}') == {'x': 1}
# bare JSON string -> marked JSON string
v = f.to_python('"hi"')
print('bare string:', repr(v), type(v).__name__)
assert v == 'hi' and type(v).__name__ == 'JSONString'
# invalid JSON rejected
try:
    f.to_python('{not json')
    print('NO ERROR'); import sys; sys.exit(1)
except ValidationError:
    pass
print('HOLDS')
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2: label_for_field resolves labels; raises on unknown name.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.contrib.admin.utils import label_for_field
from django.contrib.auth.models import User

# model field name
assert label_for_field('username', User) == 'username'
# __str__ special name -> str(model._meta.verbose_name)
assert label_for_field('__str__', User) == str(User._meta.verbose_name)
# callable
def a_callable(obj):
    return 'x'
a_callable.short_description = 'My Callable'
assert label_for_field(a_callable, User) == 'My Callable'
# return_attr
label, attr = label_for_field('username', User, return_attr=True)
assert label == 'username'
print('labels ok:', label, attr)

# unknown -> AttributeError with model name in message
try:
    label_for_field('nonexistent_zzz', User)
    print('NO RAISE'); import sys; sys.exit(1)
except AttributeError as e:
    print('RAISED:', e)
    assert 'User' in str(e)
print('HOLDS')
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1/1.3 (positive control): display_for_field on a non-ASCII JSONField value
# must return literal non-ASCII chars, not \uXXXX escapes.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.contrib.admin.utils import display_for_field
from django.db import models

f = models.JSONField()
val = {'greeting': '中国', 'list': ['jaźń']}
out = display_for_field(val, f, '-')
print('OUT:', repr(out))
ok = ('中国' in out) and ('jaźń' in out) and ('\\u' not in out)
# must still be valid JSON
import json
parsed = json.loads(out)
print('PARSED:', parsed)
assert parsed == val, 'roundtrip mismatch'
print('HOLDS' if ok else 'FAILS')
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes covering all 4 requirements. Coverage: probe_1 (R1.1/1.3, positive control) admin display_for_field preserves literal non-ASCII + valid-JSON roundtrip; probe_2 (R1.2) ASCII display output == standard compact json.dumps; probe_3 (R1.4/1.6) unserializable value falls back to display_for_value, None->empty_value_display; probe_4 (R1.5) field custom encoder honored in display; probe_5 (R2.1/2.2/2.3) prepare_value preserves non-ASCII for str/dict/list/emoji; probe_6 (R2.4/2.5/2.6) ASCII unchanged + None->'null' + InvalidJSONInput passthrough + custom encoder; probe_7 (R3.1/3.2) has_changed key-order-insensitive & True!=1, to_python valid/invalid/JSONString; probe_8 (R4.1/4.2) label_for_field resolves field/__str__/callable/return_attr and raises AttributeError naming model on unknown.

All 8 HOLD on patched tree. Positive control probe_1 FAILS at base (outputs 中国 escapes) => discriminating power confirmed.

Weak candidates (both apply cleanly at base):
- weak_forms_only (partial fix: only forms/fields.py gets ensure_ascii=False, admin untouched): REJECTED by probe_1 and probe_4 (admin still escapes).
- weak_no_encoder (both paths get ensure_ascii=False but drop cls=field.encoder): REJECTED by probe_4 (admin) and probe_6 (forms) — custom encoder no longer honored, and probe_4 raises on the date value.

Suite discriminates wrong implementations; no probe-conforming alternative found. Note: meta.json records G-PANEL-3 (leakage) fail re: spec prose enumerating UTF-16-code-unit/Latin-Extended cases mirroring hidden test parametrization — that is a leakage concern, orthogonal to G-EQ spec-strength which is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Req 1.1/1.3 (positive control): display_for_field on a non-ASCII JSONField value
# must return literal non-ASCII chars, not \uXXXX escapes.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True, SECRET_KEY='x')
    django.setup()
from django.contrib.admin.utils import display_for_field
from django.db import models

f = models.JSONField()
val = {'greeting': '中国', 'list': ['jaźń']}
out = display_for_field(val, f, '-')
print('OUT:', repr(out))
ok = ('中国' in out) and ('jaźń' in out) and ('\\u' not in out)
# must still be valid JSON
import json
parsed = json.loads(out)
print('PARSED:', parsed)
assert parsed == val, 'roundtrip mismatch'
print('HOLDS' if ok else 'FAILS')
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes covering all 4 requirements. Coverage: probe_1 (R1.1/1.3, positive control) admin display_for_field preserves literal non-ASCII + valid-JSON roundtrip; probe_2 (R1.2) ASCII display output == standard compact json.dumps; probe_3 (R1.4/1.6) unserializable value falls back to display_for_value, None->empty_value_display; probe_4 (R1.5) field custom encoder honored in display; probe_5 (R2.1/2.2/2.3) prepare_value preserves non-ASCII for str/dict/list/emoji; probe_6 (R2.4/2.5/2.6) ASCII unchanged + None->'null' + InvalidJSONInput passthrough + custom encoder; probe_7 (R3.1/3.2) has_changed key-order-insensitive & True!=1, to_python valid/invalid/JSONString; probe_8 (R4.1/4.2) label_for_field resolves field/__str__/callable/return_attr and raises AttributeError naming model on unknown.

All 8 HOLD on patched tree. Positive control probe_1 FAILS at base (outputs 中国 escapes) => discriminating power confirmed.

Weak candidates (both apply cleanly at base):
- weak_forms_only (partial fix: only forms/fields.py gets ensure_ascii=False, admin untouched): REJECTED by probe_1 and probe_4 (admin still escapes).
- weak_no_encoder (both paths get ensure_ascii=False but drop cls=field.encoder): REJECTED by probe_4 (admin) and probe_6 (forms) — custom encoder no longer honored, and probe_4 raises on the date value.

Suite discriminates wrong implementations; no probe-conforming alternative found. Note: meta.json records G-PANEL-3 (leakage) fail re: spec prose enumerating UTF-16-code-unit/Latin-Extended cases mirroring hidden test parametrization — that is a leakage concern, orthogonal to G-EQ spec-strength which is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is two one-line edits: admin/utils.py display_for_field JSONField branch changes field.get_prep_value(value) → json.dumps(value, ensure_ascii=False, cls=field.encoder); forms/fields.py prepare_value adds ensure_ascii=False. Requirements 1 and 2 pin exactly the two changed observable paths (non-ASCII literal output) and their preserved edge behaviors (encoder use=R1.5/R2.6, TypeError fallback=R1.4, None/empty=R1.6/R2.4, InvalidJSONInput passthrough=R2.5). Note the ASCII-equivalence claim in R1.2 ("same output as before") is technically only approximately true since base used get_prep_value and patch uses json.dumps — but for standard JSON-serializable ASCII values both yield identical compact JSON (verified {"a":1} → {"a": 1} identical), and R1.2 is scoped to ASCII content where they agree, so no divergence. Requirements 3 and 4 are 'unchanged' guards on non-touched behavior, consistent with the patch not modifying those paths. Modeling boundary is correct: it pins the changed behavior (ensure_ascii=False effect) biconditionally against base, not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to the two real functions (display_for_field, JSONField.prepare_value) and their modules — legitimate. All behavioral criteria are translations of what the tests check into requirements, not transmissions of the tests. No test names/paths/ids, no quoted test/gold code, no fix-invented identifiers appear. The only concrete example (a Chinese string preserved verbatim) is already public in the problem_statement (json.dumps('中国') → escapes). The test's other data points (emoji '😀🐱', Polish 'jaźń', array case) are NOT reproduced in prose. 'field's encoder' references genuine public API, not an invented identifier. Borderline lines considered and cleared: R1-AC4 ('a mapping whose keys are not valid JSON object keys') echoes the test's tuple-key invalid-JSON tuple, but it describes the general TypeError-fallback behavior present in the gold (`except TypeError: return display_for_value(...)`) rather than quoting the case; R1-AC2/R2-AC4 enumerating objects/arrays/scalars is generic JSON structure, not a mirror of specific parametrized ids. None rises to reconstructing the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
