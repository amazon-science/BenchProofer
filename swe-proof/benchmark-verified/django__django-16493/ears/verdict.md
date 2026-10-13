# P2 adversarial audit — django__django-16493

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
"""Positive control. Req1.2 + Req1.3 + Req1.1:
callable storage returning default_storage -> deconstruct includes 'storage'
kwarg whose value is the original callable (identity). HOLDS patched, FAILS base."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], MEDIA_ROOT="$SCRATCH")
django.setup()

from django.db.models.fields.files import FileField
from django.core.files.storage import default_storage


def get_default_storage():
    return default_storage


f = FileField(upload_to="foo", storage=get_default_storage)
name, path, args, kwargs = f.deconstruct()
print("kwargs:", kwargs)
if "storage" not in kwargs:
    print("FAIL: storage kwarg omitted for callable returning default_storage")
    sys.exit(1)
if kwargs["storage"] is not get_default_storage:
    print("FAIL: storage value is not the original callable:", kwargs["storage"])
    sys.exit(1)
print("OK: storage kwarg present and is the original callable")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.1: callable storage returning NON-default storage -> deconstruct
includes 'storage' whose value is the original callable (identity-preserved),
not the evaluated instance."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], MEDIA_ROOT="$SCRATCH")
django.setup()

from django.db.models.fields.files import FileField
from django.core.files.storage import FileSystemStorage

other = FileSystemStorage(location="$SCRATCH")


def get_other():
    return other


f = FileField(upload_to="foo", storage=get_other)
name, path, args, kwargs = f.deconstruct()
print("kwargs:", kwargs)
if "storage" not in kwargs:
    print("FAIL: storage kwarg omitted for non-default callable")
    sys.exit(1)
if kwargs["storage"] is not get_other:
    print("FAIL: storage value is not the original callable:", kwargs["storage"])
    sys.exit(1)
print("OK: non-default callable preserved by identity")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.3: concrete (non-callable) non-default storage instance -> deconstruct
includes 'storage' whose value is that instance.
Also Req3.1/Req3.2: default storage cases omit 'storage'."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], MEDIA_ROOT="$SCRATCH")
django.setup()

from django.db.models.fields.files import FileField
from django.core.files.storage import FileSystemStorage, default_storage

inst = FileSystemStorage(location="$SCRATCH")
f = FileField(upload_to="foo", storage=inst)
name, path, args, kwargs = f.deconstruct()
print("non-default instance kwargs:", kwargs)
if kwargs.get("storage") is not inst:
    print("FAIL: non-default instance not recorded by identity")
    sys.exit(1)

# Req3.1: no storage arg -> omit
f2 = FileField(upload_to="foo")
_, _, _, kwargs2 = f2.deconstruct()
print("no-arg kwargs:", kwargs2)
if "storage" in kwargs2:
    print("FAIL: storage kwarg present when no storage supplied")
    sys.exit(1)

# Req3.2: explicit default_storage instance -> omit
f3 = FileField(upload_to="foo", storage=default_storage)
_, _, _, kwargs3 = f3.deconstruct()
print("default-instance kwargs:", kwargs3)
if "storage" in kwargs3:
    print("FAIL: storage kwarg present for explicit default_storage instance")
    sys.exit(1)

print("OK: non-default instance recorded; default cases omitted")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req4: unrelated deconstruction behavior preserved.
- always include upload_to
- omit max_length when default 100
- name/path/args unchanged from base Field deconstruction."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], MEDIA_ROOT="$SCRATCH")
django.setup()

from django.db.models.fields.files import FileField

f = FileField(upload_to="uploads/")
name, path, args, kwargs = f.deconstruct()
print("name,path,args,kwargs:", name, path, args, kwargs)

if kwargs.get("upload_to") != "uploads/":
    print("FAIL: upload_to not included/correct")
    sys.exit(1)
if "max_length" in kwargs:
    print("FAIL: max_length present when default 100")
    sys.exit(1)
if path != "django.db.models.FileField":
    print("FAIL: import path unexpected:", path)
    sys.exit(1)
if args != []:
    print("FAIL: positional args unexpected:", args)
    sys.exit(1)

# non-default max_length must be kept
f2 = FileField(upload_to="uploads/", max_length=200)
_, _, _, kwargs2 = f2.deconstruct()
print("maxlen200 kwargs:", kwargs2)
if kwargs2.get("max_length") != 200:
    print("FAIL: non-default max_length dropped")
    sys.exit(1)

print("OK: upload_to kept, max_length default omitted, path/args intact")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req5: construction semantics preserved.
- callable evaluated once, returned instance is active storage (self.storage)
- callable stored on _storage_callable
- non-storage return -> TypeError
- no arg -> active storage is default_storage."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], MEDIA_ROOT="$SCRATCH")
django.setup()

from django.db.models.fields.files import FileField
from django.core.files.storage import FileSystemStorage, default_storage

other = FileSystemStorage(location="$SCRATCH")
calls = {"n": 0}


def make():
    calls["n"] += 1
    return other


f = FileField(upload_to="foo", storage=make)
print("calls after init:", calls["n"], "storage is other:", f.storage is other)
if calls["n"] != 1:
    print("FAIL: callable not evaluated exactly once")
    sys.exit(1)
if f.storage is not other:
    print("FAIL: active storage is not the evaluated instance")
    sys.exit(1)
if getattr(f, "_storage_callable", None) is not make:
    print("FAIL: _storage_callable not preserved")
    sys.exit(1)

# non-storage return -> TypeError
def bad():
    return 42

try:
    FileField(upload_to="foo", storage=bad)
    print("FAIL: no TypeError for non-storage callable return")
    sys.exit(1)
except TypeError as e:
    print("got TypeError:", e)

# no arg -> default_storage
f2 = FileField(upload_to="foo")
if f2.storage is not default_storage:
    print("FAIL: default active storage not default_storage")
    sys.exit(1)

print("OK: construction semantics preserved")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req1.2 + Req1.3 + Req1.1:
callable storage returning default_storage -> deconstruct includes 'storage'
kwarg whose value is the original callable (identity). HOLDS patched, FAILS base."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], MEDIA_ROOT="$SCRATCH")
django.setup()

from django.db.models.fields.files import FileField
from django.core.files.storage import default_storage


def get_default_storage():
    return default_storage


f = FileField(upload_to="foo", storage=get_default_storage)
name, path, args, kwargs = f.deconstruct()
print("kwargs:", kwargs)
if "storage" not in kwargs:
    print("FAIL: storage kwarg omitted for callable returning default_storage")
    sys.exit(1)
if kwargs["storage"] is not get_default_storage:
    print("FAIL: storage value is not the original callable:", kwargs["storage"])
    sys.exit(1)
print("OK: storage kwarg present and is the original callable")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: FileField.deconstruct() must base the storage include/omit decision on the ORIGINAL reference (callable when supplied, else instance) and record the callable by identity.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req1.1/1.2/1.3): callable returning default_storage -> 'storage' kwarg present AND value IS the original callable (identity). PATCHED exit0; BASE exit1 (kwarg omitted) -> discriminates.
- probe_2 (Req2.1): callable returning non-default storage -> 'storage' present, value is original callable by identity.
- probe_3 (Req2.3/Req3.1/Req3.2): non-default concrete instance recorded by identity; no-arg omits; explicit default_storage instance omits.
- probe_4 (Req4.1/4.2/4.3): upload_to always included; default max_length=100 omitted; path=django.db.models.FileField, args=[]; non-default max_length=200 kept.
- probe_5 (Req5.1/5.2/5.3): callable evaluated exactly once, active storage is returned instance, _storage_callable preserved; non-storage return raises TypeError; no-arg -> default_storage active.

CANDIDATE PATCH (weak.diff): fixes the include/omit decision (uses original reference) BUT records self.storage (the evaluated instance) rather than the callable — the lazy fix a weak reading permits. REJECTED by probe_1 and probe_2 (identity lost), confirming the suite discriminates the wrong fix that would break Req1.3/Req2.1 and the hidden identity-preservation tests. probes 3/4/5 correctly still hold under it (those criteria unaffected).

Verdict SOUND: >=5 distinct probes all hold on patched; positive control fails at base (prepatch reproduced); >=1 wrong candidate exercised and REJECTED.

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
"""Positive control. Req1.2 + Req1.3 + Req1.1:
callable storage returning default_storage -> deconstruct includes 'storage'
kwarg whose value is the original callable (identity). HOLDS patched, FAILS base."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], MEDIA_ROOT="$SCRATCH")
django.setup()

from django.db.models.fields.files import FileField
from django.core.files.storage import default_storage


def get_default_storage():
    return default_storage


f = FileField(upload_to="foo", storage=get_default_storage)
name, path, args, kwargs = f.deconstruct()
print("kwargs:", kwargs)
if "storage" not in kwargs:
    print("FAIL: storage kwarg omitted for callable returning default_storage")
    sys.exit(1)
if kwargs["storage"] is not get_default_storage:
    print("FAIL: storage value is not the original callable:", kwargs["storage"])
    sys.exit(1)
print("OK: storage kwarg present and is the original callable")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: FileField.deconstruct() must base the storage include/omit decision on the ORIGINAL reference (callable when supplied, else instance) and record the callable by identity.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req1.1/1.2/1.3): callable returning default_storage -> 'storage' kwarg present AND value IS the original callable (identity). PATCHED exit0; BASE exit1 (kwarg omitted) -> discriminates.
- probe_2 (Req2.1): callable returning non-default storage -> 'storage' present, value is original callable by identity.
- probe_3 (Req2.3/Req3.1/Req3.2): non-default concrete instance recorded by identity; no-arg omits; explicit default_storage instance omits.
- probe_4 (Req4.1/4.2/4.3): upload_to always included; default max_length=100 omitted; path=django.db.models.FileField, args=[]; non-default max_length=200 kept.
- probe_5 (Req5.1/5.2/5.3): callable evaluated exactly once, active storage is returned instance, _storage_callable preserved; non-storage return raises TypeError; no-arg -> default_storage active.

CANDIDATE PATCH (weak.diff): fixes the include/omit decision (uses original reference) BUT records self.storage (the evaluated instance) rather than the callable — the lazy fix a weak reading permits. REJECTED by probe_1 and probe_2 (identity lost), confirming the suite discriminates the wrong fix that would break Req1.3/Req2.1 and the hidden identity-preservation tests. probes 3/4/5 correctly still hold under it (those criteria unaffected).

Verdict SOUND: >=5 distinct probes all hold on patched; positive control fails at base (prepatch reproduced); >=1 wrong candidate exercised and REJECTED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch replaces `if self.storage is not default_storage: kwargs['storage']=getattr(self,'_storage_callable',self.storage)` with computing `storage=getattr(self,'_storage_callable',self.storage)` FIRST and testing `if storage is not default_storage`. The requirements pin exactly this observable change: the include/omit decision and recorded value are based on the ORIGINAL reference (callable when supplied) via identity against default_storage — Requirement 1 (esp. 1.2 the overlooked default_storage-returning callable case from the issue), Req 3 (identity-based omit), Req 2 (non-default preservation), Req 4/5 (unchanged surrounding behavior). Modeling boundary is correct: it targets the changed deconstruct() decision, not a narrow branch or helper. Probe confirmed ALL OK (exit 0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md translates the public problem_statement (callable storage that returns default_storage being wrongly omitted by deconstruct; self.storage evaluated vs original reference) into EARS behavioral criteria. No hidden-test content transmitted: no test function/class names (test_deconstruction_storage_callable_default, callable_default_storage, storage_callable_default), no test file paths, no parametrization ids, no quoted test/gold code. `_storage_callable` named in the intro is a pre-existing FileField attribute (from the #31941 fix), not a fix-invented identifier, and naming the involved module/attribute is legitimate localization. The gold's key expression getattr(self,'_storage_callable',self.storage) is described as behavior (base decision on the original reference), not transmitted verbatim. The case enumeration (callable->default, callable->non-default, callable-class object, concrete non-default instance, no-arg default) maps to natural behavioral partitions and existing PASS_TO_PASS behaviors, not a mirror of the hidden test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
