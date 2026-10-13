# P2 adversarial audit — django__django-14580

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_6.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.2 / positive control: serializing models.Model reports
'from django.db import models' as a required import."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.writer import MigrationWriter

string, imports = MigrationWriter.serialize(models.Model)
print("string=", repr(string))
print("imports=", sorted(imports))
ok = 'from django.db import models' in set(imports)
print("has_models_import=", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1: serializing models.Model renders the source text 'models.Model'."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.writer import MigrationWriter

string, imports = MigrationWriter.serialize(models.Model)
print("string=", repr(string))
raise SystemExit(0 if string == "models.Model" else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.3: required imports for models.Model returned as a set (not a list)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.writer import MigrationWriter

string, imports = MigrationWriter.serialize(models.Model)
print("type(imports)=", type(imports).__name__)
raise SystemExit(0 if isinstance(imports, set) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2: round-trip. Evaluate the rendered text in a namespace built ONLY
from the reported imports; the result must be models.Model itself."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.writer import MigrationWriter

string, imports = MigrationWriter.serialize(models.Model)
print("string=", repr(string), "imports=", sorted(imports))
ns = {}
for imp in imports:
    exec(imp, ns)          # apply exactly the reported imports
val = eval(string, ns)     # 'models' must resolve purely from those imports
print("roundtrip is models.Model:", val is models.Model)
raise SystemExit(0 if val is models.Model else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2/3.3: preserve serialization of other types.
 - type(None) -> 'type(None)', no imports
 - a builtin type -> bare name, no imports
 - another (non-special, non-builtin) type -> 'module.qualname' + import of module."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.migrations.writer import MigrationWriter
import collections

ok = True

s, imp = MigrationWriter.serialize(type(None))
print("None:", repr(s), sorted(imp))
ok &= (s == "type(None)" and set(imp) == set())

s, imp = MigrationWriter.serialize(int)
print("int:", repr(s), sorted(imp))
ok &= (s == "int" and set(imp) == set())

s, imp = MigrationWriter.serialize(collections.OrderedDict)
print("OrderedDict:", repr(s), sorted(imp))
ok &= (s == "collections.OrderedDict" and set(imp) == {"import collections"})

print("all_ok=", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req1.4: a generated migration whose bases mix a plain mixin with
models.Model must still cause django.db.models to be imported, so the emitted
file references 'models' and imports & executes without NameError."""
import os, sys, re, tempfile
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models, migrations
from django.db.migrations.writer import MigrationWriter

d = tempfile.mkdtemp()
with open(os.path.join(d, "mymix.py"), "w") as f:
    f.write("class Mixin:\n    pass\n")
sys.path.insert(0, d)
import mymix

op = migrations.CreateModel(
    name="Thing", fields=[], bases=(mymix.Mixin, models.Model),
)
mig = type("Migration", (migrations.Migration,), {"operations": [op], "dependencies": []})
out = MigrationWriter(mig).as_string()
print("----- generated migration -----")
print(out)
print("-------------------------------")
refs_models = "models.Model" in out
# 'models' imported from django.db, possibly merged e.g. 'from django.db import migrations, models'
imports_models = bool(re.search(r"^from django\.db import .*\bmodels\b", out, re.M))
print("refs_models=", refs_models, "imports_models=", imports_models)
ns = {}
try:
    exec(compile(out, "gen_migration.py", "exec"), ns)
    importable = True
except NameError as e:
    print("NameError:", e); importable = False
print("importable=", importable)
raise SystemExit(0 if (refs_models and imports_models and importable) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_6.py`

```python
"""Req1.4: a generated migration whose bases mix a plain mixin with
models.Model must still cause django.db.models to be imported, so the emitted
file references 'models' and imports & executes without NameError."""
import os, sys, re, tempfile
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models, migrations
from django.db.migrations.writer import MigrationWriter

d = tempfile.mkdtemp()
with open(os.path.join(d, "mymix.py"), "w") as f:
    f.write("class Mixin:\n    pass\n")
sys.path.insert(0, d)
import mymix

op = migrations.CreateModel(
    name="Thing", fields=[], bases=(mymix.Mixin, models.Model),
)
mig = type("Migration", (migrations.Migration,), {"operations": [op], "dependencies": []})
out = MigrationWriter(mig).as_string()
print("----- generated migration -----")
print(out)
print("-------------------------------")
refs_models = "models.Model" in out
# 'models' imported from django.db, possibly merged e.g. 'from django.db import migrations, models'
imports_models = bool(re.search(r"^from django\.db import .*\bmodels\b", out, re.M))
print("refs_models=", refs_models, "imports_models=", imports_models)
ns = {}
try:
    exec(compile(out, "gen_migration.py", "exec"), ns)
    importable = True
except NameError as e:
    print("NameError:", e); importable = False
print("importable=", importable)
raise SystemExit(0 if (refs_models and imports_models and importable) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithful to gold patch. 6 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.2): imports set contains 'from django.db import models'. HOLDS patched, FAILS base (imports=[]).
- probe_2 (Req1.1): rendered text == 'models.Model'. HOLDS.
- probe_3 (Req1.3): imports returned as a set. HOLDS.
- probe_4 (Req2.1/2.2): round-trip — eval('models.Model') in a namespace built ONLY from reported imports yields models.Model. HOLDS patched, NameError at base/weak.
- probe_5 (Req3.1/3.2/3.3): type(None)->'type(None)'+{}, int->'int'+{}, OrderedDict->'collections.OrderedDict'+{'import collections'}. HOLDS.
- probe_6 (Req1.4, end-to-end + positive control): CreateModel with bases=(Mixin, models.Model) -> as_string() references models.Model, emits a 'from django.db import ... models' line, and the file exec()s without NameError. HOLDS patched (importable), FAILS base (NameError: name 'models' is not defined).

Discrimination: positive controls probe_1 and probe_6 both FAIL at base and HOLD patched.

Wrong-fix candidate weak.diff uses imports=['import django.db.models'] instead of 'from django.db import models'. This satisfies a lazy reading (it does import the module) but does NOT bind the name 'models'. REJECTED by probe_1 (import string mismatch), probe_4 (NameError on eval) and probe_6 (generated migration NameError) — confirming the suite discriminates a plausible wrong fix that would not resolve the hidden tests. The gold patch's exact 'from django.db import models' is the only conforming implementation the probes accept.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_6.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_6.py`

```python
"""Req1.4: a generated migration whose bases mix a plain mixin with
models.Model must still cause django.db.models to be imported, so the emitted
file references 'models' and imports & executes without NameError."""
import os, sys, re, tempfile
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models, migrations
from django.db.migrations.writer import MigrationWriter

d = tempfile.mkdtemp()
with open(os.path.join(d, "mymix.py"), "w") as f:
    f.write("class Mixin:\n    pass\n")
sys.path.insert(0, d)
import mymix

op = migrations.CreateModel(
    name="Thing", fields=[], bases=(mymix.Mixin, models.Model),
)
mig = type("Migration", (migrations.Migration,), {"operations": [op], "dependencies": []})
out = MigrationWriter(mig).as_string()
print("----- generated migration -----")
print(out)
print("-------------------------------")
refs_models = "models.Model" in out
# 'models' imported from django.db, possibly merged e.g. 'from django.db import migrations, models'
imports_models = bool(re.search(r"^from django\.db import .*\bmodels\b", out, re.M))
print("refs_models=", refs_models, "imports_models=", imports_models)
ns = {}
try:
    exec(compile(out, "gen_migration.py", "exec"), ns)
    importable = True
except NameError as e:
    print("NameError:", e); importable = False
print("importable=", importable)
raise SystemExit(0 if (refs_models and imports_models and importable) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithful to gold patch. 6 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.2): imports set contains 'from django.db import models'. HOLDS patched, FAILS base (imports=[]).
- probe_2 (Req1.1): rendered text == 'models.Model'. HOLDS.
- probe_3 (Req1.3): imports returned as a set. HOLDS.
- probe_4 (Req2.1/2.2): round-trip — eval('models.Model') in a namespace built ONLY from reported imports yields models.Model. HOLDS patched, NameError at base/weak.
- probe_5 (Req3.1/3.2/3.3): type(None)->'type(None)'+{}, int->'int'+{}, OrderedDict->'collections.OrderedDict'+{'import collections'}. HOLDS.
- probe_6 (Req1.4, end-to-end + positive control): CreateModel with bases=(Mixin, models.Model) -> as_string() references models.Model, emits a 'from django.db import ... models' line, and the file exec()s without NameError. HOLDS patched (importable), FAILS base (NameError: name 'models' is not defined).

Discrimination: positive controls probe_1 and probe_6 both FAIL at base and HOLD patched.

Wrong-fix candidate weak.diff uses imports=['import django.db.models'] instead of 'from django.db import models'. This satisfies a lazy reading (it does import the module) but does NOT bind the name 'models'. REJECTED by probe_1 (import string mismatch), probe_4 (NameError on eval) and probe_6 (generated migration NameError) — confirming the suite discriminates a plausible wrong fix that would not resolve the hidden tests. The gold patch's exact 'from django.db import models' is the only conforming implementation the probes accept.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a one-line change: special_cases entry for models.Model changes imports from [] to ['from django.db import models']. Requirements model exactly this boundary — the TypeSerializer special-case now declaring its required import — not a narrower slice. Probe on patched: Model:'models.Model' {'from django.db import models'} <set>; None:'type(None)' set(); int:'int' set(); CharField:'django.db.models.fields.CharField' {'import django.db.models.fields'}. Probe on base: base returns set() for Model, matching the pre-fix NameError scenario. No mandated behavior absent from patched code; no forbidden behavior present; boundary is the changed behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to TypeSerializer.serialize / MigrationWriter.serialize (legitimate). The import string 'from django.db import models' (Req 1.2) matches the one-line gold edit, but it is independently derivable from the PUBLIC problem_statement: models.py contains `from django.db import models` and the reported failure is `NameError: name 'models' is not defined`, so declaring that import is the direct behavioral fix, not leaked test content. Req 3's enumeration (type(None) with empty imports, builtins bare-name, other types module+qualname) mirrors the serializer's existing special_cases/dispatch logic in the source, not the hidden test parametrization. No test function names (test_serialize_type_model), file paths (tests/migrations/test_writer.py), assertion helpers (assertSerializedResultEqual), the verbatim expected tuple "('models.Model', {'from django.db import models'})", or fix-invented identifiers appear. Behavioral translation of what the tests check — which is the intended purpose — not transmission of the tests themselves.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
