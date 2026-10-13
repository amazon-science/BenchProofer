# P2 adversarial audit — django__django-15161

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models

v = models.Value(42)
path, args, kwargs = v.deconstruct()
print("Value.deconstruct path =", path, "args=", args, "kwargs=", kwargs)
assert path == "django.db.models.Value", path
print("OK Req1.1")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.models.functions import Lower

# Req1.2-1.6 + Req1.7: each exact-type instance deconstructs to public path,
# and that path resolves back to the same class object.
cases = [
    (models.Func(models.F('x'), function='UPPER'), "django.db.models.Func", models.Func),
    (models.ExpressionWrapper(models.F('x'), output_field=models.IntegerField()),
     "django.db.models.ExpressionWrapper", models.ExpressionWrapper),
    (models.When(models.Q(x=1), then=models.Value(1)), "django.db.models.When", models.When),
    (models.Case(models.When(models.Q(x=1), then=1)), "django.db.models.Case", models.Case),
    (models.OrderBy(models.F('x')), "django.db.models.OrderBy", models.OrderBy),
]
from importlib import import_module
ok = True
for obj, expected, cls in cases:
    path = obj.deconstruct()[0]
    mod, _, name = expected.rpartition('.')
    resolved = getattr(import_module(mod), name)
    print(type(obj).__name__, "->", path, "resolves to", resolved)
    if path != expected:
        print("  MISMATCH expected", expected); ok = False
    if resolved is not cls:
        print("  RESOLVE MISMATCH"); ok = False
assert ok
print("OK Req1.2-1.7")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models

# Req2.1: Value(single) -> args=(value,), kwargs={}
v = models.Value(42)
path, args, kwargs = v.deconstruct()
print("Value(42):", path, args, kwargs)
assert args == (42,), args
assert kwargs == {}, kwargs

# Req2.2: Value with explicit output_field
of = models.IntegerField()
v2 = models.Value(42, output_field=of)
path2, args2, kwargs2 = v2.deconstruct()
print("Value(42, output_field):", path2, args2, kwargs2)
assert args2 == (42,), args2
assert set(kwargs2) == {"output_field"}, kwargs2
# the output_field must deconstruct identically to the supplied field
assert kwargs2["output_field"].deconstruct() == of.deconstruct(), kwargs2["output_field"].deconstruct()
assert path2 == "django.db.models.Value", path2
print("OK Req2.1/2.2")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models

# Req3.1: a subclass whose runtime type is not exactly the configured class
# must deconstruct to its OWN module+name, not the configured simplified path.
class MyValue(models.Value):
    pass

mv = MyValue(7)
path = mv.deconstruct()[0]
print("MyValue.deconstruct path =", path)
assert path != "django.db.models.Value", path
# own fully-qualified location: defining module joined to class name
assert path == MyValue.__module__ + ".MyValue", path
print("OK Req3.1 subclass fallback")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.writer import MigrationWriter

# Req4: serialize an Index whose expressions are built ONLY from the affected
# expression classes: a Func call, a Case/When with a wrapped Value, an
# ExpressionWrapper, and an OrderBy. Rendered code must use models.<Name>,
# imports must be exactly {from django.db import models}, and the internal
# 'expressions' submodule must NOT appear.
index = models.Index(
    models.Func(models.F('name'), function='LOWER'),
    models.Case(models.When(models.Q(x=1), then=models.Value('a')), default=models.Value('b')),
    models.ExpressionWrapper(models.F('y'), output_field=models.IntegerField()),
    models.OrderBy(models.F('z')),
    name='idx',
)
string, imports = MigrationWriter.serialize(index)
print("SERIALIZED:", string)
print("IMPORTS:", imports)

assert "django.db.models.expressions" not in string, string
assert "models.Func" in string, string
assert "models.Case" in string, string
assert "models.When" in string, string
assert "models.Value" in string, string
assert "models.ExpressionWrapper" in string, string
assert "models.OrderBy" in string, string
# Req4.2: imports exactly the single models import
assert imports == {"from django.db import models"}, imports
# Req4.3: structure preserved
assert "then=" in string, string
assert "default=" in string, string
assert "output_field=" in string, string
print("OK Req4")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.writer import MigrationWriter

# Req5.1: F still deconstructs to django.db.models.F
fp = models.F('x').deconstruct()
print("F.deconstruct:", fp)
assert fp[0] == "django.db.models.F", fp

# Req5.4 / 5.3: serializing a value that does NOT reference models must not
# pull in the models import. A plain int serializes to just "42" with no imports.
s_int, imp_int = MigrationWriter.serialize(42)
print("int serialize:", s_int, imp_int)
assert s_int == "42", s_int
assert imp_int == set(), imp_int
assert "from django.db import models" not in imp_int

# datetime -> its own import, no spurious models import
import datetime
s_dt, imp_dt = MigrationWriter.serialize(datetime.date(2020, 1, 1))
print("date serialize:", s_dt, imp_dt)
assert "import datetime" in imp_dt, imp_dt
assert "from django.db import models" not in imp_dt, imp_dt
print("OK Req5.1/5.3/5.4")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.writer import MigrationWriter

# Req4: serialize an Index whose expressions are built ONLY from the affected
# expression classes: a Func call, a Case/When with a wrapped Value, an
# ExpressionWrapper, and an OrderBy. Rendered code must use models.<Name>,
# imports must be exactly {from django.db import models}, and the internal
# 'expressions' submodule must NOT appear.
index = models.Index(
    models.Func(models.F('name'), function='LOWER'),
    models.Case(models.When(models.Q(x=1), then=models.Value('a')), default=models.Value('b')),
    models.ExpressionWrapper(models.F('y'), output_field=models.IntegerField()),
    models.OrderBy(models.F('z')),
    name='idx',
)
string, imports = MigrationWriter.serialize(index)
print("SERIALIZED:", string)
print("IMPORTS:", imports)

assert "django.db.models.expressions" not in string, string
assert "models.Func" in string, string
assert "models.Case" in string, string
assert "models.When" in string, string
assert "models.Value" in string, string
assert "models.ExpressionWrapper" in string, string
assert "models.OrderBy" in string, string
# Req4.2: imports exactly the single models import
assert imports == {"from django.db import models"}, imports
# Req4.3: structure preserved
assert "then=" in string, string
assert "default=" in string, string
assert "output_field=" in string, string
print("OK Req4")
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; all requirements covered.

Probe coverage:
- probe_1 (Req1.1): Value instance deconstructs to 'django.db.models.Value'. HOLDS patched, FAILS base.
- probe_2 (Req1.2-1.7): Func/ExpressionWrapper/When/Case/OrderBy each deconstruct to their public path AND that path resolves back to the identical class object (importability). HOLDS patched.
- probe_3 (Req2.1/2.2): Value(v) -> args=(v,), kwargs={}; Value(v, output_field=of) -> args=(v,), kwargs={'output_field': of'} where of deconstructs identically. HOLDS patched.
- probe_4 (Req3.1): a Value subclass falls back to its own module+name, NOT the configured simplified path. HOLDS patched.
- probe_5 (Req4.1/4.2/4.3 — POSITIVE CONTROL): serialize an Index built only from Func/Case/When/Value/ExpressionWrapper/OrderBy; rendered code uses models.<Name>, contains no 'django.db.models.expressions', preserves then=/default=/output_field=, and imports == {'from django.db import models'}. HOLDS patched (exit 0), VIOLATED at base (exit 1: base emits django.db.models.expressions.* and extra imports). Confirms discriminating power / prepatch reproduced.
- probe_6 (Req5.1/5.3/5.4): F still deconstructs to django.db.models.F; plain int serializes to '42' with empty import set; datetime.date serializes with 'import datetime' and NO spurious models import. HOLDS patched.

Candidate patch (REQUIRED floor met): weak_value_only decorates ONLY Value with deconstructible(path=...), a partial/lazy fix a weak reading permits. Under it, probe_1/3/4/6 HOLD but probe_2 is REJECTED (Func/ExpressionWrapper/When/Case/OrderBy still deconstruct to internal 'django.db.models.expressions.*') and probe_5 is REJECTED (serialized Index still contains django.db.models.expressions). This demonstrates the suite discriminates wrong implementations and admits no obvious too-weak fix.

Note on probe design: an early probe_5 draft used functions.Lower (a Func subclass in functions.text) which legitimately adds its own import — that reflected my probe, not a spec defect; corrected to use models.Func directly. All runs completed in the official Docker image; no INCONCLUSIVE runs.

Verdict SOUND: >=5 probes all hold on the patched tree, the positive control discriminates (patched HOLDS / base VIOLATED), and the constructed partial-fix candidate is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.writer import MigrationWriter

# Req4: serialize an Index whose expressions are built ONLY from the affected
# expression classes: a Func call, a Case/When with a wrapped Value, an
# ExpressionWrapper, and an OrderBy. Rendered code must use models.<Name>,
# imports must be exactly {from django.db import models}, and the internal
# 'expressions' submodule must NOT appear.
index = models.Index(
    models.Func(models.F('name'), function='LOWER'),
    models.Case(models.When(models.Q(x=1), then=models.Value('a')), default=models.Value('b')),
    models.ExpressionWrapper(models.F('y'), output_field=models.IntegerField()),
    models.OrderBy(models.F('z')),
    name='idx',
)
string, imports = MigrationWriter.serialize(index)
print("SERIALIZED:", string)
print("IMPORTS:", imports)

assert "django.db.models.expressions" not in string, string
assert "models.Func" in string, string
assert "models.Case" in string, string
assert "models.When" in string, string
assert "models.Value" in string, string
assert "models.ExpressionWrapper" in string, string
assert "models.OrderBy" in string, string
# Req4.2: imports exactly the single models import
assert imports == {"from django.db import models"}, imports
# Req4.3: structure preserved
assert "then=" in string, string
assert "default=" in string, string
assert "output_field=" in string, string
print("OK Req4")
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; all requirements covered.

Probe coverage:
- probe_1 (Req1.1): Value instance deconstructs to 'django.db.models.Value'. HOLDS patched, FAILS base.
- probe_2 (Req1.2-1.7): Func/ExpressionWrapper/When/Case/OrderBy each deconstruct to their public path AND that path resolves back to the identical class object (importability). HOLDS patched.
- probe_3 (Req2.1/2.2): Value(v) -> args=(v,), kwargs={}; Value(v, output_field=of) -> args=(v,), kwargs={'output_field': of'} where of deconstructs identically. HOLDS patched.
- probe_4 (Req3.1): a Value subclass falls back to its own module+name, NOT the configured simplified path. HOLDS patched.
- probe_5 (Req4.1/4.2/4.3 — POSITIVE CONTROL): serialize an Index built only from Func/Case/When/Value/ExpressionWrapper/OrderBy; rendered code uses models.<Name>, contains no 'django.db.models.expressions', preserves then=/default=/output_field=, and imports == {'from django.db import models'}. HOLDS patched (exit 0), VIOLATED at base (exit 1: base emits django.db.models.expressions.* and extra imports). Confirms discriminating power / prepatch reproduced.
- probe_6 (Req5.1/5.3/5.4): F still deconstructs to django.db.models.F; plain int serializes to '42' with empty import set; datetime.date serializes with 'import datetime' and NO spurious models import. HOLDS patched.

Candidate patch (REQUIRED floor met): weak_value_only decorates ONLY Value with deconstructible(path=...), a partial/lazy fix a weak reading permits. Under it, probe_1/3/4/6 HOLD but probe_2 is REJECTED (Func/ExpressionWrapper/When/Case/OrderBy still deconstruct to internal 'django.db.models.expressions.*') and probe_5 is REJECTED (serialized Index still contains django.db.models.expressions). This demonstrates the suite discriminates wrong implementations and admits no obvious too-weak fix.

Note on probe design: an early probe_5 draft used functions.Lower (a Func subclass in functions.text) which legitimately adds its own import — that reflected my probe, not a spec defect; corrected to use models.Func directly. All runs completed in the official Docker image; no INCONCLUSIVE runs.

Verdict SOUND: >=5 probes all hold on the patched tree, the positive control discriminates (patched HOLDS / base VIOLATED), and the constructed partial-fix candidate is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch adds @deconstructible(path='django.db.models.<Name>') to Func, Value, ExpressionWrapper, When, Case, OrderBy in django/db/models/expressions.py. The EARS requirements pin exactly the changed observable behavior (simplified import path in deconstruct/serialize) at the correct boundary: they scope to exact runtime type (Req3.1 subclass fallback is the actual deconstructible behavior), preserve args/kwargs (Req2), and preserve F and unrelated serialization (Req5). No mandated behavior the code lacks, no forbidden behavior it has, no narrow-slice mis-boundary, no invented behavior. Probes run in the instance image confirm all claims on the gold-patched tree.

Counterexample / evidence:

```
N/A — no requirement disagrees with patched behavior.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements name the affected classes (Func, Value, ExpressionWrapper, When, Case, OrderBy), module (django/db/models/expressions.py), decorator (deconstructible/path), and serializer (MigrationWriter.serialize) — all legitimate localization derivable from the gold patch, not the hidden tests. The public-path targets generalize the problem_statement's F example. Req 4.1's composite 'index' example structurally echoes test_serialize_complex_func_index, but ALL test literals are stripped (no 'rating'/'ABS'/'special'/'X'/'other'/'pages'/'complex_func_index', no test names/paths/ids, no quoted assertion strings); it describes behavior abstractly using already-legitimately-named types. Kwarg names then/default/output_field are public Django API, not fix-invented identifiers. This is behavioral translation, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
