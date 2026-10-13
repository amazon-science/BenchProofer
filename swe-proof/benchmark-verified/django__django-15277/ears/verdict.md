# P2 adversarial audit — django__django-15277

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
"""Req 1.1 & 1.4 (POSITIVE CONTROL): a max_length=None CharField has no
MaxLengthValidator, and running its validation/clean path does not raise
TypeError. FAILS at base (validator attached -> TypeError)."""
import sys
from django.db.models.fields import CharField
from django.core import validators

f = CharField()  # max_length defaults to None
assert f.max_length is None, f"expected max_length None, got {f.max_length}"

ml = [v for v in f.validators if isinstance(v, validators.MaxLengthValidator)]
print("max_length:", f.max_length)
print("MaxLengthValidators attached:", len(ml))
if ml:
    print("FAIL: MaxLengthValidator present on max_length-less CharField")
    sys.exit(1)

# Req 1.4: clean must not raise TypeError comparing len against None
try:
    out = f.clean("hello world", None)
    print("clean returned:", repr(out))
except TypeError as e:
    print("FAIL: TypeError from clean:", e)
    sys.exit(1)

print("OK: no length validator and clean succeeds")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2 & 3.1: a non-None max_length CharField appends a MaxLengthValidator
that enforces the bound (value longer than max fails validation)."""
import sys
from django.db.models.fields import CharField
from django.core import validators
from django.core.exceptions import ValidationError

f = CharField(max_length=5)
ml = [v for v in f.validators if isinstance(v, validators.MaxLengthValidator)]
print("MaxLengthValidators attached:", len(ml))
if len(ml) != 1:
    print("FAIL: expected exactly one MaxLengthValidator")
    sys.exit(1)
if ml[0].limit_value != 5:
    print("FAIL: validator bound not 5:", ml[0].limit_value)
    sys.exit(1)

# enforcement: too-long value must fail
try:
    f.clean("toolong", None)
    print("FAIL: over-length value did not raise ValidationError")
    sys.exit(1)
except ValidationError:
    print("OK: over-length raised ValidationError")

# within-bound value ok
out = f.clean("ok", None)
print("clean short value:", repr(out))
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.3: existing validators are preserved in order, and the length
validator is only appended (last) when max_length is declared."""
import sys
from django.db.models.fields import CharField
from django.core import validators

# supply an explicit validator
def myval(v):
    return None

# with max_length: explicit validator preserved, MaxLengthValidator appended last
f = CharField(max_length=10, validators=[myval])
names = [type(v).__name__ if not (v is myval) else "myval" for v in f.validators]
print("validators (max_length=10):", names)
if "myval" not in names:
    print("FAIL: explicit validator not preserved")
    sys.exit(1)
ml_positions = [i for i, v in enumerate(f.validators)
                if isinstance(v, validators.MaxLengthValidator)]
if len(ml_positions) != 1:
    print("FAIL: expected one MaxLengthValidator")
    sys.exit(1)
# myval must come before the appended MaxLengthValidator
myval_pos = f.validators.index(myval)
if not (myval_pos < ml_positions[0]):
    print("FAIL: explicit validator not before appended MaxLengthValidator")
    sys.exit(1)

# without max_length: explicit validator preserved, NO MaxLengthValidator
g = CharField(validators=[myval])
gnames = [type(v).__name__ if not (v is myval) else "myval" for v in g.validators]
print("validators (no max_length):", gnames)
if myval not in g.validators:
    print("FAIL: explicit validator not preserved (no max_length)")
    sys.exit(1)
if any(isinstance(v, validators.MaxLengthValidator) for v in g.validators):
    print("FAIL: MaxLengthValidator appended despite no max_length")
    sys.exit(1)

print("OK: validators preserved in order; length validator only when max_length set")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1 & 2.2: Value._resolve_output_field for a string returns a CharField
with max_length None and no MaxLengthValidator; cleaning that string over the
resolved field with no model instance succeeds."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()
from django.db.models import Value
from django.db.models.fields import CharField
from django.core import validators

field = Value("test")._resolve_output_field()
print("resolved field type:", type(field).__name__)
if not isinstance(field, CharField):
    print("FAIL: string Value did not resolve to CharField")
    sys.exit(1)
if field.max_length is not None:
    print("FAIL: resolved CharField max_length not None:", field.max_length)
    sys.exit(1)
if any(isinstance(v, validators.MaxLengthValidator) for v in field.validators):
    print("FAIL: MaxLengthValidator present on resolved output field")
    sys.exit(1)

# Req 2.2: clean the string over the resolved field, no model instance
out = field.clean("test", None)
print("clean returned:", repr(out))
print("OK: string Value resolves to validator-less CharField and cleans")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.3 & 2.4: For each supported literal type, Value._resolve_output_field
resolves to the expected field type AND cleaning the resolved field over its own
value (no model instance) completes without exception. String -> CharField."""
import sys, uuid, datetime
from decimal import Decimal
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()
from django.db.models import Value
from django.db.models import fields as F

cases = [
    ("str", "test", F.CharField),
    ("bool", True, F.BooleanField),
    ("int", 3, F.IntegerField),
    ("float", 3.5, F.FloatField),
    ("date", datetime.date(2020, 1, 1), F.DateField),
    ("datetime", datetime.datetime(2020, 1, 1, 0, 0), F.DateTimeField),
    ("time", datetime.time(0, 0), F.TimeField),
    ("timedelta", datetime.timedelta(days=1), F.DurationField),
    ("decimal", Decimal("1.5"), F.DecimalField),
    ("bytes", b"x", F.BinaryField),
    ("uuid", uuid.uuid4(), F.UUIDField),
]
ok = True
for name, val, ftype in cases:
    field = Value(val)._resolve_output_field()
    same = isinstance(field, ftype)
    print(f"{name}: resolved {type(field).__name__} expected {ftype.__name__} match={same}")
    if not same:
        ok = False
        continue
    try:
        field.clean(val, None)
    except Exception as e:
        print(f"  FAIL: clean raised for {name}: {type(e).__name__}: {e}")
        ok = False
if not ok:
    sys.exit(1)
print("OK: all supported literals map to expected field type and clean cleanly")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.2: system check still reports the max_length error for a model
CharField declaring no max_length. Omitting the length validator does not
suppress fields.E120."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
    django.setup()
from django.db import models

class M(models.Model):
    name = models.CharField()  # no max_length
    class Meta:
        app_label = "check_probe"

field = M._meta.get_field("name")
errors = field.check()
ids = [e.id for e in errors]
print("check error ids:", ids)
if "fields.E120" not in ids:
    print("FAIL: expected fields.E120 for max_length-less model CharField")
    sys.exit(1)
print("OK: system check still reports fields.E120")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 3.3: BinaryField appends its MaxLengthValidator only when a non-None
max_length is declared (precedent that CharField now matches)."""
import sys
from django.db.models.fields import BinaryField
from django.core import validators

# no max_length -> no MaxLengthValidator
b = BinaryField()
print("BinaryField() max_length:", b.max_length)
if any(isinstance(v, validators.MaxLengthValidator) for v in b.validators):
    print("FAIL: BinaryField() attached MaxLengthValidator with no max_length")
    sys.exit(1)

# with max_length -> exactly one MaxLengthValidator with correct bound
b2 = BinaryField(max_length=8)
ml = [v for v in b2.validators if isinstance(v, validators.MaxLengthValidator)]
print("BinaryField(max_length=8) MaxLengthValidators:", len(ml))
if len(ml) != 1 or ml[0].limit_value != 8:
    print("FAIL: BinaryField(max_length=8) validator wrong")
    sys.exit(1)
print("OK: BinaryField construction behavior unchanged")
sys.exit(0)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
"""Req 3.4: other Value/expression behaviors preserved — equality, hashing,
deconstruction, repr, and explicit-output-field resolution unchanged."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()
from django.db.models import Value, IntegerField
from django.db.models.fields import CharField

v1 = Value("test")
v2 = Value("test")
# equality & hashing
if not (v1 == v2):
    print("FAIL: equal Values not equal"); sys.exit(1)
if hash(v1) != hash(v2):
    print("FAIL: equal Values hash differently"); sys.exit(1)
# repr
r = repr(v1)
print("repr:", r)
if "Value" not in r:
    print("FAIL: repr missing Value"); sys.exit(1)
# deconstruct round-trips
path, args, kwargs = v1.deconstruct()
print("deconstruct:", path, args, kwargs)
if args != ("test",):
    print("FAIL: deconstruct args wrong"); sys.exit(1)
# explicit output field respected
vexp = Value("x", output_field=IntegerField())
if not isinstance(vexp._output_field_or_none, IntegerField):
    print("FAIL: explicit output_field not respected"); sys.exit(1)
print("OK: Value equality/hash/deconstruct/repr/explicit-output preserved")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1 & 1.4 (POSITIVE CONTROL): a max_length=None CharField has no
MaxLengthValidator, and running its validation/clean path does not raise
TypeError. FAILS at base (validator attached -> TypeError)."""
import sys
from django.db.models.fields import CharField
from django.core import validators

f = CharField()  # max_length defaults to None
assert f.max_length is None, f"expected max_length None, got {f.max_length}"

ml = [v for v in f.validators if isinstance(v, validators.MaxLengthValidator)]
print("max_length:", f.max_length)
print("MaxLengthValidators attached:", len(ml))
if ml:
    print("FAIL: MaxLengthValidator present on max_length-less CharField")
    sys.exit(1)

# Req 1.4: clean must not raise TypeError comparing len against None
try:
    out = f.clean("hello world", None)
    print("clean returned:", repr(out))
except TypeError as e:
    print("FAIL: TypeError from clean:", e)
    sys.exit(1)

print("OK: no length validator and clean succeeds")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes cover Req1.1-1.4, Req2.1-2.4, Req3.1-3.4. All 8 HOLD on the gold-patched tree. Positive control probe_1 (Req1.1/1.4: max_length=None CharField has no MaxLengthValidator and clean() doesn't raise TypeError) FAILS at base (validator attached -> len>None TypeError) and HOLDS patched -> discriminates. Candidate 'remove_validator_entirely' deletes the append unconditionally (the lazy fix a weak reading of Req1.1 would permit); it is REJECTED by probe_2 (Req1.2/3.1 length enforcement: no validator on max_length=5 -> over-length no longer fails) and probe_3 (Req1.3: MaxLengthValidator must be appended when max_length is set). Suite discriminates wrong implementations. No VIOLATION or TOO-WEAK finding. (Note: meta.json records G-PANEL-3=LEAKAGE re Req3.4/ExpressionList; that is a separate leakage gate, out of scope for spec-fidelity/G-EQ which only concerns whether requirements match gold behavior and are non-trivially strong — they do.)

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
"""Req 1.1 & 1.4 (POSITIVE CONTROL): a max_length=None CharField has no
MaxLengthValidator, and running its validation/clean path does not raise
TypeError. FAILS at base (validator attached -> TypeError)."""
import sys
from django.db.models.fields import CharField
from django.core import validators

f = CharField()  # max_length defaults to None
assert f.max_length is None, f"expected max_length None, got {f.max_length}"

ml = [v for v in f.validators if isinstance(v, validators.MaxLengthValidator)]
print("max_length:", f.max_length)
print("MaxLengthValidators attached:", len(ml))
if ml:
    print("FAIL: MaxLengthValidator present on max_length-less CharField")
    sys.exit(1)

# Req 1.4: clean must not raise TypeError comparing len against None
try:
    out = f.clean("hello world", None)
    print("clean returned:", repr(out))
except TypeError as e:
    print("FAIL: TypeError from clean:", e)
    sys.exit(1)

print("OK: no length validator and clean succeeds")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes cover Req1.1-1.4, Req2.1-2.4, Req3.1-3.4. All 8 HOLD on the gold-patched tree. Positive control probe_1 (Req1.1/1.4: max_length=None CharField has no MaxLengthValidator and clean() doesn't raise TypeError) FAILS at base (validator attached -> len>None TypeError) and HOLDS patched -> discriminates. Candidate 'remove_validator_entirely' deletes the append unconditionally (the lazy fix a weak reading of Req1.1 would permit); it is REJECTED by probe_2 (Req1.2/3.1 length enforcement: no validator on max_length=5 -> over-length no longer fails) and probe_3 (Req1.3: MaxLengthValidator must be appended when max_length is set). Suite discriminates wrong implementations. No VIOLATION or TOO-WEAK finding. (Note: meta.json records G-PANEL-3=LEAKAGE re Req3.4/ExpressionList; that is a separate leakage gate, out of scope for spec-fidelity/G-EQ which only concerns whether requirements match gold behavior and are non-trivially strong — they do.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: the change is a one-line conditional guard in CharField.__init__; requirements pin the biconditional (attach validator iff max_length is not None) plus faithful preservation clauses (system check for model CharField still errors, BinaryField unchanged, other Value/expression behavior unchanged). No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior.

Counterexample / evidence:

```
N/A — no divergence found. Patched probe HOLDS (exit 0), base probe reproduces the TypeError.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally and stay within what the public problem_statement already exposes. The problem_statement itself already names Value._resolve_output_field, CharField(), max_length, MaxLengthValidator, the TypeError from comparing int > None, y.clean('1', model_instance=None), and the BinaryField.__init__ precedent — so Req 1/2 restating those (including 'clean ... with no model instance') is public, not test-derived. The gold patch introduces NO new identifiers (just `if self.max_length is not None:`), so there is nothing fix-invented to leak. Critically, the hidden test's distinctive artifact — the 11-element value_types parametrization list (str, True, 42, 3.14, datetime.date/datetime/time/timedelta, Decimal, b'', uuid.uuid4()) — is NOT reproduced or enumerated; the doc generalizes to 'any other literal type ... leaves its resolved field unaffected.' No test names, file paths (tests/expressions/tests.py), or the FAIL_TO_PASS test_raise_empty_expressionlist appear. Req 3.4's mention of 'explicit-output-field and decimal cases' corresponds to existing PASS_TO_PASS behaviors and reads as legitimate behavior-preservation prose (decimal output-field resolution is a natural, publicly-inferable case), not a mirror of the test parametrization. Naming the modules/functions (CharField.__init__, Value._resolve_output_field, BinaryField) is legitimate localization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
