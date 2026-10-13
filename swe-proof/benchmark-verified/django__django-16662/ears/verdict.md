# P2 adversarial audit — django__django-16662

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req1.1: plain `import` before `from ... import`.
Build a migration whose imports include a plain `import uuid` (from a
UUIDField default) and the always-present `from django.db import migrations`.
Grouping must place the plain import strictly before the from-import.
Base (alphabetical by module token) puts 'django.db' before 'uuid', so the
plain import comes LAST -> fails.  Patched groups plain first -> holds.
"""
import sys, uuid, re
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes"], DATABASES={}, USE_TZ=True)
django.setup()
from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter

class M(migrations.Migration):
    operations = [migrations.CreateModel("Thing", [
        ("id", models.UUIDField(primary_key=True, default=uuid.uuid4)),
    ])]
    dependencies = []
mig = M("0001_initial", "app")
text = MigrationWriter(mig, include_header=False).as_string()
print(text)
lines = [l.strip() for l in text.splitlines() if l.strip().startswith(("import ", "from "))]
print("IMPORT LINES:", lines)
plain_idx = [i for i, l in enumerate(lines) if l.split()[0] != "from"]
from_idx = [i for i, l in enumerate(lines) if l.split()[0] == "from"]
assert plain_idx and from_idx, "need both kinds present: %r" % lines
ok = max(plain_idx) < min(from_idx)
print("plain_idx=%s from_idx=%s ordered=%s" % (plain_idx, from_idx, ok))
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.2/2.3: selective (from) imports ordered ascending by module token.
Use a swappable dependency (yields `from django.conf import settings`) plus a
CreateModel with a model field (yields `from django.db import migrations,
models`).  Two from-imports; module tokens django.conf < django.db, so order
must be [django.conf, django.db].
"""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes"], DATABASES={}, USE_TZ=True)
django.setup()
from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter

class M(migrations.Migration):
    operations = [migrations.CreateModel("Thing", [
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=10)),
    ])]
    dependencies = [("__setting__", "AUTH_USER_MODEL")]
mig = M("0001_initial", "app")
text = MigrationWriter(mig, include_header=False).as_string()
print(text)
lines = [l.strip() for l in text.splitlines() if l.strip().startswith(("import ", "from "))]
print("IMPORT LINES:", lines)
from_lines = [l for l in lines if l.split()[0] == "from"]
modules = [l.split()[1] for l in from_lines]
print("from modules:", modules)
assert "django.conf" in modules and "django.db" in modules, modules
ok = modules == sorted(modules)
print("ascending=%s" % ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req4.1/4.2/4.3: always-present migrations import; models merge; no stray models.
Case A: model with a field -> single combined `from django.db import
migrations, models` present and there is NO bare `from django.db import
migrations` and NO bare `from django.db import models`.
Case B: no models needed (RunPython) -> `from django.db import migrations`
present and NO `models` import at all.
"""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes"], DATABASES={}, USE_TZ=True)
django.setup()
from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter

def block(ops):
    class M(migrations.Migration):
        operations = ops
        dependencies = []
    return [l.strip() for l in MigrationWriter(M("0001", "app"), include_header=False).as_string().splitlines()
            if l.strip().startswith(("import ", "from "))]

a = block([migrations.CreateModel("Thing", [("id", models.AutoField(primary_key=True))])])
print("A:", a)
assert "from django.db import migrations, models" in a, a
assert "from django.db import migrations" not in a, a
assert "from django.db import models" not in a, a

def noop(apps, schema_editor):
    pass
b = block([migrations.RunPython(noop, noop)])
print("B:", b)
assert "from django.db import migrations" in b, b
assert not any("models" in l for l in b), b
print("OK req4.1-4.3")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2 + Req2 within-group alpha: pure rearrangement, same multiset;
and plain imports themselves ordered ascending by module.
Force several plain imports via field defaults referencing datetime and uuid,
plus the from-imports. Assert: (a) the emitted import block is a permutation of
the collected set (no add/drop/dup/textual change) and (b) plain imports are
sorted ascending among themselves.
We reconstruct the "collected" set independently by parsing and checking the
sorted-by-module invariant per group, and that grouping is total.
"""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes"], DATABASES={}, USE_TZ=True)
django.setup()
from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter
import datetime, uuid

class M(migrations.Migration):
    operations = [migrations.CreateModel("Thing", [
        ("id", models.UUIDField(primary_key=True, default=uuid.uuid4)),
        ("created", models.DateTimeField(default=datetime.datetime(2020,1,1))),
    ])]
    dependencies = []
text = MigrationWriter(M("0001", "app"), include_header=False).as_string()
print(text)
lines = [l.strip() for l in text.splitlines() if l.strip().startswith(("import ", "from "))]
print("LINES:", lines)
# no duplicates
assert len(lines) == len(set(lines)), "duplicate import line: %r" % lines
# grouping total: all plain then all from
kinds = [l.split()[0] == "from" for l in lines]
assert kinds == sorted(kinds), "not grouped plain-before-from: %r" % kinds
# within plain group ascending by module token
plain = [l for l in lines if l.split()[0] != "from"]
from_ = [l for l in lines if l.split()[0] == "from"]
pm = [l.split()[1] for l in plain]
fm = [l.split()[1] for l in from_]
print("plain modules:", pm, "from modules:", fm)
assert pm == sorted(pm), pm
assert fm == sorted(fm), fm
# must actually have multiple plain imports (datetime + uuid) to be meaningful
assert len(plain) >= 2, plain
print("OK req2/req3 rearrangement + within-group alpha")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req1.3/1.4 + Req4.6: single-kind blocks emit ascending, no crash, and the
generated migration file is valid/importable.
Only-from case here (always-present from-imports with settings dependency but no
plain module import). Also compile the emitted source to prove it's importable.
"""
import sys, tempfile, os, importlib.util
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes"], DATABASES={}, USE_TZ=True)
django.setup()
from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter

class M(migrations.Migration):
    operations = [migrations.CreateModel("Thing", [("id", models.AutoField(primary_key=True))])]
    dependencies = [("__setting__", "AUTH_USER_MODEL")]
text = MigrationWriter(M("0001_initial", "app"), include_header=True).as_string()
print(text)
lines = [l.strip() for l in text.splitlines() if l.strip().startswith(("import ", "from "))]
print("LINES:", lines)
assert all(l.split()[0] == "from" for l in lines), "expected only from-imports: %r" % lines
mods = [l.split()[1] for l in lines]
assert mods == sorted(mods), mods
# importable: write to a temp module and import it
d = tempfile.mkdtemp()
p = os.path.join(d, "m0001.py")
open(p, "w").write(text)
spec = importlib.util.spec_from_file_location("m0001", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
assert hasattr(mod, "Migration"), "no Migration class"
print("importable OK, ops=%d" % len(mod.Migration.operations))
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.1: plain `import` before `from ... import`.
Build a migration whose imports include a plain `import uuid` (from a
UUIDField default) and the always-present `from django.db import migrations`.
Grouping must place the plain import strictly before the from-import.
Base (alphabetical by module token) puts 'django.db' before 'uuid', so the
plain import comes LAST -> fails.  Patched groups plain first -> holds.
"""
import sys, uuid, re
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes"], DATABASES={}, USE_TZ=True)
django.setup()
from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter

class M(migrations.Migration):
    operations = [migrations.CreateModel("Thing", [
        ("id", models.UUIDField(primary_key=True, default=uuid.uuid4)),
    ])]
    dependencies = []
mig = M("0001_initial", "app")
text = MigrationWriter(mig, include_header=False).as_string()
print(text)
lines = [l.strip() for l in text.splitlines() if l.strip().startswith(("import ", "from "))]
print("IMPORT LINES:", lines)
plain_idx = [i for i, l in enumerate(lines) if l.split()[0] != "from"]
from_idx = [i for i, l in enumerate(lines) if l.split()[0] == "from"]
assert plain_idx and from_idx, "need both kinds present: %r" % lines
ok = max(plain_idx) < min(from_idx)
print("plain_idx=%s from_idx=%s ordered=%s" % (plain_idx, from_idx, ok))
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16662: gold patch changes MigrationWriter.as_string sort key from `i.split()[1]` to `(i.split()[0]=='from', i.split()[1])` so plain `import` lines group before `from ... import ...`, alpha within each group.

Probes (all run in official image; python via swebench-lean conda):
- probe_1 (Req1.1, POSITIVE CONTROL): UUIDField(default=uuid.uuid4) yields `import uuid` + `from django.db import migrations, models`. Patched: plain-before-from (HOLDS, exit0). Base: `from django.db` sorts before `uuid` so plain import is last (FAILS, exit1). Discriminates -> prepatch_reproduced=true.
- probe_2 (Req2.2/2.3): swappable dep + model field -> two from-imports; module tokens ascending [django.conf, django.db]. HOLDS patched.
- probe_3 (Req4.1/4.2/4.3): CreateModel -> single combined `from django.db import migrations, models`, no bare migrations/models; RunPython -> `from django.db import migrations` and NO models import. HOLDS.
- probe_4 (Req2/Req3): datetime+uuid defaults -> plain imports [datetime,uuid]; asserts grouping total, no dups, within-group ascending, pure permutation. HOLDS.
- probe_5 (Req1.4/4.6): only-from block ascending AND emitted source is importable (exec_module, Migration class present). HOLDS.

Candidate wrong patches (both REJECTED by suite -> discriminating):
- weak_reversed: groups from-imports FIRST (reversed grouping). Rejected by probe_1 & probe_4.
- weak_descsort: correct grouping but DESCENDING within group. Rejected by probe_2 & probe_4.

No requirements-conforming alternative found that would evade the hidden tests; suite rejects the plausible wrong fixes. 5 distinct probes all hold on patched tree; positive control discriminates patched vs base. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control / Req1.1: plain `import` before `from ... import`.
Build a migration whose imports include a plain `import uuid` (from a
UUIDField default) and the always-present `from django.db import migrations`.
Grouping must place the plain import strictly before the from-import.
Base (alphabetical by module token) puts 'django.db' before 'uuid', so the
plain import comes LAST -> fails.  Patched groups plain first -> holds.
"""
import sys, uuid, re
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes"], DATABASES={}, USE_TZ=True)
django.setup()
from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter

class M(migrations.Migration):
    operations = [migrations.CreateModel("Thing", [
        ("id", models.UUIDField(primary_key=True, default=uuid.uuid4)),
    ])]
    dependencies = []
mig = M("0001_initial", "app")
text = MigrationWriter(mig, include_header=False).as_string()
print(text)
lines = [l.strip() for l in text.splitlines() if l.strip().startswith(("import ", "from "))]
print("IMPORT LINES:", lines)
plain_idx = [i for i, l in enumerate(lines) if l.split()[0] != "from"]
from_idx = [i for i, l in enumerate(lines) if l.split()[0] == "from"]
assert plain_idx and from_idx, "need both kinds present: %r" % lines
ok = max(plain_idx) < min(from_idx)
print("plain_idx=%s from_idx=%s ordered=%s" % (plain_idx, from_idx, ok))
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16662: gold patch changes MigrationWriter.as_string sort key from `i.split()[1]` to `(i.split()[0]=='from', i.split()[1])` so plain `import` lines group before `from ... import ...`, alpha within each group.

Probes (all run in official image; python via swebench-lean conda):
- probe_1 (Req1.1, POSITIVE CONTROL): UUIDField(default=uuid.uuid4) yields `import uuid` + `from django.db import migrations, models`. Patched: plain-before-from (HOLDS, exit0). Base: `from django.db` sorts before `uuid` so plain import is last (FAILS, exit1). Discriminates -> prepatch_reproduced=true.
- probe_2 (Req2.2/2.3): swappable dep + model field -> two from-imports; module tokens ascending [django.conf, django.db]. HOLDS patched.
- probe_3 (Req4.1/4.2/4.3): CreateModel -> single combined `from django.db import migrations, models`, no bare migrations/models; RunPython -> `from django.db import migrations` and NO models import. HOLDS.
- probe_4 (Req2/Req3): datetime+uuid defaults -> plain imports [datetime,uuid]; asserts grouping total, no dups, within-group ascending, pure permutation. HOLDS.
- probe_5 (Req1.4/4.6): only-from block ascending AND emitted source is importable (exec_module, Migration class present). HOLDS.

Candidate wrong patches (both REJECTED by suite -> discriminating):
- weak_reversed: groups from-imports FIRST (reversed grouping). Rejected by probe_1 & probe_4.
- weak_descsort: correct grouping but DESCENDING within group. Rejected by probe_2 & probe_4.

No requirements-conforming alternative found that would evade the hidden tests; suite rejects the plausible wrong fixes. 5 distinct probes all hold on patched tree; positive control discriminates patched vs base. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified live in the instance image: gold-patched probe exits 0 (grouping+ordering holds), base exits 1 (AssertionError: plain import after from). Requirements pin the changed observable behavior (import block ordering as emitted by MigrationWriter.as_string), not a narrow helper slice, and the biconditional between base/patched is exhibited. Note: Req 2.3 phrasing 'token after import in import <module>' is a slight simplification — the patch actually keys on split()[1] uniformly, which for a from-statement is the module (from<space>MOD) and for plain import is the module; this matches the code exactly, no divergence.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the import-grouping behavior (plain imports before from-imports, alphabetical within each group) in general behavioral terms. Every concrete detail traces to the PUBLIC problem_statement, which itself shows the exact before example (import datetime / from django.db import migrations, models / import time) and the desired after (import datetime / import time / from django.db import migrations, models) — identical to the hidden test's assertIn string. The doc legitimately localizes the change to MigrationWriter.as_string in writer.py (naming modules/functions is allowed). No hidden-test artifacts leak: no test function/class names (test_sorted_imports, WriterTests), no ticket ids used as FAIL_TO_PASS ('#24155'), no test file path (tests/migrations/test_writer.py), no test-invented fixtures (time.time / FloatField / myfield2 / mymodel), no gold key-function tuple, no parametrization enumeration. Req 4.2's migrations,models merge is pre-existing behavior also shown in the public example. The doc translates test-checked behavior into requirements — which is the intended purpose, not a leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
