# P2 adversarial audit — django__django-13343

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
# Positive control + Req2.1: callable storage deconstructs to the ORIGINAL callable (identity).
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField
from django.core.files.storage import FileSystemStorage

my_storage = FileSystemStorage(location='$SCRATCH')
def get_storage():
    return my_storage

f = FileField(upload_to='u', storage=get_storage)
name, path, args, kwargs = f.deconstruct()
val = kwargs.get('storage', '<MISSING>')
print("deconstructed storage:", repr(val))
print("is original callable:", val is get_storage)
if val is get_storage:
    sys.exit(0)
print("FAIL: storage did not deconstruct to the original callable")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.1/1.2/1.3: callable retained (identity) AND runtime storage is the evaluated instance,
# AND the callable is evaluated exactly once at construction.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField
from django.core.files.storage import FileSystemStorage

calls = {"n": 0}
inst = FileSystemStorage(location='$SCRATCH')
def get_storage():
    calls["n"] += 1
    return inst

f = FileField(upload_to='u', storage=get_storage)
print("call count at construction:", calls["n"])
print("_storage_callable is original:", getattr(f, "_storage_callable", None) is get_storage)
print("runtime storage is evaluated instance:", f.storage is inst)
ok = (calls["n"] == 1) and (getattr(f, "_storage_callable", None) is get_storage) and (f.storage is inst)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.4 / Req2.2: plain (non-callable) non-default Storage instance -> no callable ref recorded,
# used directly, and deconstruct returns that same instance.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField
from django.core.files.storage import FileSystemStorage

inst = FileSystemStorage(location='$SCRATCH')
f = FileField(upload_to='u', storage=inst)
print("has _storage_callable:", hasattr(f, "_storage_callable"))
print("runtime storage is inst:", f.storage is inst)
name, path, args, kwargs = f.deconstruct()
print("deconstructed storage is inst:", kwargs.get('storage') is inst)
ok = (not hasattr(f, "_storage_callable")) and (f.storage is inst) and (kwargs.get('storage') is inst)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req1.5 / Req2.3: no storage arg -> default storage at runtime, no callable ref, and
# deconstruct OMITS the storage key.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField
from django.core.files.storage import default_storage

f = FileField(upload_to='u')
print("has _storage_callable:", hasattr(f, "_storage_callable"))
print("runtime storage is default:", f.storage is default_storage)
name, path, args, kwargs = f.deconstruct()
print("storage key present:", 'storage' in kwargs)
ok = (not hasattr(f, "_storage_callable")) and (f.storage is default_storage) and ('storage' not in kwargs)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req1.6 (SHALL keep): callable storage returning a non-Storage value raises TypeError at construction.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField

def bad_storage():
    return object()  # not a Storage

try:
    FileField(upload_to='u', storage=bad_storage)
    print("FAIL: no TypeError raised")
    sys.exit(1)
except TypeError as e:
    print("TypeError raised as expected:", e)
    sys.exit(0)
except Exception as e:
    print("FAIL: wrong exception type:", type(e).__name__, e)
    sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req2.6: deconstruct() is read-only wrt field state — runtime storage attribute still the
# evaluated instance afterward. Also idempotent across calls.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField
from django.core.files.storage import FileSystemStorage

inst = FileSystemStorage(location='$SCRATCH')
def get_storage():
    return inst

f = FileField(upload_to='u', storage=get_storage)
_ = f.deconstruct()
print("runtime storage after 1st deconstruct is inst:", f.storage is inst)
name, path, args, kwargs = f.deconstruct()
print("storage after 2nd deconstruct is original callable:", kwargs.get('storage') is get_storage)
print("runtime storage still inst:", f.storage is inst)
ok = (f.storage is inst) and (kwargs.get('storage') is get_storage)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req2.4/2.5 (SHALL keep): upload_to always present; callable upload_to preserved by identity;
# max_length default 100 omitted, non-default included.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField

def upload_fn(instance, filename):
    return filename

# callable upload_to, default max_length
f1 = FileField(upload_to=upload_fn)
_, _, _, k1 = f1.deconstruct()
print("upload_to present & identity:", 'upload_to' in k1, k1.get('upload_to') is upload_fn)
print("max_length omitted (default 100):", 'max_length' not in k1)

# non-default max_length
f2 = FileField(upload_to='u', max_length=250)
_, _, _, k2 = f2.deconstruct()
print("max_length included when non-default:", k2.get('max_length') == 250)
print("upload_to value preserved (str):", k2.get('upload_to') == 'u')

ok = ('upload_to' in k1 and k1.get('upload_to') is upload_fn and 'max_length' not in k1
       and k2.get('max_length') == 250 and k2.get('upload_to') == 'u')
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# Req3.2 / Req2.3: callable storage that RETURNS the project default storage ->
# runtime behaves as default AND deconstruct OMITS storage (since runtime storage IS default).
# This is a subtle boundary: gold uses `if self.storage is not default_storage`.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField
from django.core.files.storage import default_storage

def get_default():
    return default_storage

f = FileField(upload_to='u', storage=get_default)
print("runtime storage is default:", f.storage is default_storage)
_, _, _, k = f.deconstruct()
print("storage key present:", 'storage' in k)
ok = (f.storage is default_storage) and ('storage' not in k)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + Req2.1: callable storage deconstructs to the ORIGINAL callable (identity).
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField
from django.core.files.storage import FileSystemStorage

my_storage = FileSystemStorage(location='$SCRATCH')
def get_storage():
    return my_storage

f = FileField(upload_to='u', storage=get_storage)
name, path, args, kwargs = f.deconstruct()
val = kwargs.get('storage', '<MISSING>')
print("deconstructed storage:", repr(val))
print("is original callable:", val is get_storage)
if val is get_storage:
    sys.exit(0)
print("FAIL: storage did not deconstruct to the original callable")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes cover all 3 requirements. Results on gold-PATCHED tree: all 8 HOLD (exit 0). probe_1 (positive control, Req2.1 identity): FAILS at base (returns evaluated FileSystemStorage instance, not the callable) and HOLDS patched -> discriminates.

Coverage: probe_1 Req2.1 callable->original callable identity; probe_2 Req1.1/1.2/1.3 callable retained by identity + evaluated exactly once + runtime is evaluated instance; probe_3 Req1.4/2.2 plain non-default Storage instance: no callable ref, used directly, deconstructs to same instance; probe_4 Req1.5/2.3 no storage arg -> default storage, no ref, storage key omitted; probe_5 Req1.6 (SHALL keep) callable returning non-Storage raises TypeError at construction; probe_6 Req2.6 deconstruct read-only wrt field state + idempotent; probe_7 Req2.4/2.5 (SHALL keep) upload_to always present + callable identity, max_length default omitted / non-default included; probe_8 Req3.2/2.3 callable returning default storage -> runtime is default AND storage key omitted (the `is not default_storage` boundary).

CANDIDATE PATCH: weak.diff stores the callable but deconstruct() emits `lambda: self._storage_callable()` (a wrapper) instead of the original object. Probes 1 and 6 REJECT it (VIOLATED exit=1: identity not preserved), demonstrating the suite discriminates wrong implementations that only satisfy a weak reading of Req2.1. No probe-conforming wrong fix found; suite pins identity, evaluate-once, boundary omission, and all SHALL-keep regressions.

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
# Positive control + Req2.1: callable storage deconstructs to the ORIGINAL callable (identity).
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.db.models.fields.files import FileField
from django.core.files.storage import FileSystemStorage

my_storage = FileSystemStorage(location='$SCRATCH')
def get_storage():
    return my_storage

f = FileField(upload_to='u', storage=get_storage)
name, path, args, kwargs = f.deconstruct()
val = kwargs.get('storage', '<MISSING>')
print("deconstructed storage:", repr(val))
print("is original callable:", val is get_storage)
if val is get_storage:
    sys.exit(0)
print("FAIL: storage did not deconstruct to the original callable")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes cover all 3 requirements. Results on gold-PATCHED tree: all 8 HOLD (exit 0). probe_1 (positive control, Req2.1 identity): FAILS at base (returns evaluated FileSystemStorage instance, not the callable) and HOLDS patched -> discriminates.

Coverage: probe_1 Req2.1 callable->original callable identity; probe_2 Req1.1/1.2/1.3 callable retained by identity + evaluated exactly once + runtime is evaluated instance; probe_3 Req1.4/2.2 plain non-default Storage instance: no callable ref, used directly, deconstructs to same instance; probe_4 Req1.5/2.3 no storage arg -> default storage, no ref, storage key omitted; probe_5 Req1.6 (SHALL keep) callable returning non-Storage raises TypeError at construction; probe_6 Req2.6 deconstruct read-only wrt field state + idempotent; probe_7 Req2.4/2.5 (SHALL keep) upload_to always present + callable identity, max_length default omitted / non-default included; probe_8 Req3.2/2.3 callable returning default storage -> runtime is default AND storage key omitted (the `is not default_storage` boundary).

CANDIDATE PATCH: weak.diff stores the callable but deconstruct() emits `lambda: self._storage_callable()` (a wrapper) instead of the original object. Probes 1 and 6 REJECT it (VIOLATED exit=1: identity not preserved), demonstrating the suite discriminates wrong implementations that only satisfy a weak reading of Req2.1. No probe-conforming wrong fix found; suite pins identity, evaluate-once, boundary omission, and all SHALL-keep regressions.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch (django/db/models/fields/files.py) does exactly two things: (1) in __init__, when self.storage is callable, save self._storage_callable = self.storage before evaluating; (2) in deconstruct, emit getattr(self, '_storage_callable', self.storage) instead of self.storage. The requirements pin precisely this changed observable boundary (deconstruct reproduces the original callable, identity-preserved) rather than a narrow slice, and correctly retain the unchanged surrounding behavior (upload_to, max_length, default-omission, runtime evaluation, TypeError). FAIL_TO_PASS test is test_deconstruction (FieldCallableFileStorageTests), consistent with Req2. Probe: probe.py — exit 0 on patch, exit 1 on base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior only, staying within the public problem_statement plus general Django FileField semantics. No hidden-test content is transmitted: (1) no test path/name — the doc never mentions tests/file_storage/tests.py or test_deconstruction; (2) no fix-invented identifiers — the gold patch's private attr `_storage_callable` and the models' `callable_storage`/`storage_callable`/`Storage` names never appear; (3) 'identity preserved' (Req 1.3, 2.1) is a legitimate behavioral translation of the F2P assertion `assertIs(storage, callable_storage)`, not a quote of it; (4) the case enumeration (callable / callable-class / plain-instance / default / non-Storage->TypeError) mirrors pre-existing, documented FileField behavior scoped for regression, all derivable from the problem statement and the explicit upload_to parallel it draws — it describes behavior to preserve rather than reproducing the PASS_TO_PASS id list or parametrization. Naming files.py/deconstruct() is legitimate localization. No quoted test or gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
