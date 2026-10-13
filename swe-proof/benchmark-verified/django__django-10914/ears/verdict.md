# P2 adversarial audit — django__django-10914

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure()
django.setup()
from django.core.files.storage import default_storage, FileSystemStorage
val = default_storage.file_permissions_mode
print("default_storage.file_permissions_mode =", oct(val) if isinstance(val,int) else repr(val))
# also fresh instance with no per-instance override
fs = FileSystemStorage()
print("fresh FileSystemStorage().file_permissions_mode =", oct(fs.file_permissions_mode) if isinstance(fs.file_permissions_mode,int) else repr(fs.file_permissions_mode))
ok = (val == 0o644) and (val is not None) and (fs.file_permissions_mode == 0o644)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
from django.conf import global_settings
v = global_settings.FILE_UPLOAD_PERMISSIONS
print("global_settings.FILE_UPLOAD_PERMISSIONS =", oct(v) if isinstance(v,int) else repr(v))
ok = (v == 0o644) and (v is not None)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure()
django.setup()
from django.test.utils import override_settings
from django.core.files.storage import FileSystemStorage
with override_settings(FILE_UPLOAD_PERMISSIONS=0o600):
    fs = FileSystemStorage()
    m = fs.file_permissions_mode
    print("overridden to 0o600 -> file_permissions_mode =", oct(m) if isinstance(m,int) else repr(m))
    ok = (m == 0o600)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure()
django.setup()
from django.test.utils import override_settings
from django.core.files.storage import FileSystemStorage
with override_settings(FILE_UPLOAD_PERMISSIONS=0o600):
    fs = FileSystemStorage(file_permissions_mode=0o755)
    m = fs.file_permissions_mode
    print("per-instance 0o755 with setting 0o600 -> ", oct(m) if isinstance(m,int) else repr(m))
    ok = (m == 0o755)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure()
django.setup()
from django.test.utils import override_settings
from django.core.files.storage import FileSystemStorage
with override_settings(FILE_UPLOAD_PERMISSIONS=None):
    fs = FileSystemStorage()
    m = fs.file_permissions_mode
    print("setting None -> file_permissions_mode =", repr(m))
    ok = (m is None)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings, global_settings
if not settings.configured:
    settings.configure()
django.setup()
from django.test.utils import override_settings
from django.core.files.storage import FileSystemStorage
gdef = global_settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS
print("global default FILE_UPLOAD_DIRECTORY_PERMISSIONS =", repr(gdef))
fs = FileSystemStorage()
print("default directory_permissions_mode =", repr(fs.directory_permissions_mode))
ok1 = (gdef is None) and (fs.directory_permissions_mode is None)
with override_settings(FILE_UPLOAD_DIRECTORY_PERMISSIONS=0o755):
    fs2 = FileSystemStorage()
    print("overridden dir perms ->", oct(fs2.directory_permissions_mode) if isinstance(fs2.directory_permissions_mode,int) else repr(fs2.directory_permissions_mode))
    ok2 = (fs2.directory_permissions_mode == 0o755)
ok = ok1 and ok2
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import os, tempfile, django
from django.conf import settings
if not settings.configured:
    settings.configure()
django.setup()
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
d = tempfile.mkdtemp()
# default mode should be 0o644
fs = FileSystemStorage(location=d)
name = fs.save("probe_default.txt", ContentFile(b"hello"))
path = fs.path(name)
mode_default = os.stat(path).st_mode & 0o777
print("default-saved file mode =", oct(mode_default))
ok1 = (mode_default == 0o644)

# explicit mode 0o600
fs2 = FileSystemStorage(location=d, file_permissions_mode=0o600)
name2 = fs2.save("probe_600.txt", ContentFile(b"hi"))
mode2 = os.stat(fs2.path(name2)).st_mode & 0o777
print("0o600-saved file mode =", oct(mode2))
ok2 = (mode2 == 0o600)

ok = ok1 and ok2
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure()
django.setup()
from django.core.files.storage import default_storage, FileSystemStorage
val = default_storage.file_permissions_mode
print("default_storage.file_permissions_mode =", oct(val) if isinstance(val,int) else repr(val))
# also fresh instance with no per-instance override
fs = FileSystemStorage()
print("fresh FileSystemStorage().file_permissions_mode =", oct(fs.file_permissions_mode) if isinstance(fs.file_permissions_mode,int) else repr(fs.file_permissions_mode))
ok = (val == 0o644) and (val is not None) and (fs.file_permissions_mode == 0o644)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: make FILE_UPLOAD_PERMISSIONS default to 0o644 (django__django-10914). 7 probes cover every acceptance criterion; all HOLD on the gold-patched tree.

Probe->criterion mapping and per-tree results:
- probe_1 (Req 1.2/1.3, POSITIVE CONTROL): default_storage & fresh FileSystemStorage().file_permissions_mode == 0o644 (not None). PATCHED=HOLD, BASE=FAIL (None), WEAK=FAIL (0o600). Discriminates.
- probe_2 (Req 1.1): global_settings.FILE_UPLOAD_PERMISSIONS == 0o644. PATCHED=HOLD, BASE=FAIL (None), WEAK=FAIL (0o600).
- probe_3 (Req 2.1): override_settings(FILE_UPLOAD_PERMISSIONS=0o600) -> effective 0o600. PATCHED=HOLD, WEAK=HOLD.
- probe_4 (Req 2.2): per-instance file_permissions_mode=0o755 wins over setting 0o600. PATCHED=HOLD.
- probe_5 (Req 2.3): setting=None + no per-instance -> effective None (OS-dependent opt-out preserved). PATCHED=HOLD.
- probe_6 (Req 3.1/3.2): FILE_UPLOAD_DIRECTORY_PERMISSIONS default None; override to 0o755 respected. PATCHED=HOLD (regression 'SHALL keep' criterion).
- probe_7 (Req 2.4): saving a file actually applies the concrete mode via chmod; default-saved file = 0o644, explicit 0o600 = 0o600. PATCHED=HOLD, WEAK=FAIL (default-saved becomes 0o600). Note probe_7 also HOLDS at base because the test host umask happens to yield 0o644 for the default case, so it is a regression/behavior probe, not the discriminator.

Weak candidate 'weak_0o600' (sets default to 0o600 instead of 0o644): a plausible wrong fix that still gives a consistent, non-None default and passes the override/per-instance/None criteria (probes 3,4,5,6). REJECTED by the suite via probes 1, 2, and 7 (default must be exactly 0o644). This demonstrates the suite discriminates a specific wrong value; it also would not resolve the hidden tests, which assert 0o644 exactly.

All required runs completed cleanly in the official image (patch applied cleanly each time). No requirement is unfaithful/too-strong (all mandated behaviors hold on gold) and no probe-conforming wrong fix was found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure()
django.setup()
from django.core.files.storage import default_storage, FileSystemStorage
val = default_storage.file_permissions_mode
print("default_storage.file_permissions_mode =", oct(val) if isinstance(val,int) else repr(val))
# also fresh instance with no per-instance override
fs = FileSystemStorage()
print("fresh FileSystemStorage().file_permissions_mode =", oct(fs.file_permissions_mode) if isinstance(fs.file_permissions_mode,int) else repr(fs.file_permissions_mode))
ok = (val == 0o644) and (val is not None) and (fs.file_permissions_mode == 0o644)
print("HOLDS" if ok else "FAILS")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: make FILE_UPLOAD_PERMISSIONS default to 0o644 (django__django-10914). 7 probes cover every acceptance criterion; all HOLD on the gold-patched tree.

Probe->criterion mapping and per-tree results:
- probe_1 (Req 1.2/1.3, POSITIVE CONTROL): default_storage & fresh FileSystemStorage().file_permissions_mode == 0o644 (not None). PATCHED=HOLD, BASE=FAIL (None), WEAK=FAIL (0o600). Discriminates.
- probe_2 (Req 1.1): global_settings.FILE_UPLOAD_PERMISSIONS == 0o644. PATCHED=HOLD, BASE=FAIL (None), WEAK=FAIL (0o600).
- probe_3 (Req 2.1): override_settings(FILE_UPLOAD_PERMISSIONS=0o600) -> effective 0o600. PATCHED=HOLD, WEAK=HOLD.
- probe_4 (Req 2.2): per-instance file_permissions_mode=0o755 wins over setting 0o600. PATCHED=HOLD.
- probe_5 (Req 2.3): setting=None + no per-instance -> effective None (OS-dependent opt-out preserved). PATCHED=HOLD.
- probe_6 (Req 3.1/3.2): FILE_UPLOAD_DIRECTORY_PERMISSIONS default None; override to 0o755 respected. PATCHED=HOLD (regression 'SHALL keep' criterion).
- probe_7 (Req 2.4): saving a file actually applies the concrete mode via chmod; default-saved file = 0o644, explicit 0o600 = 0o600. PATCHED=HOLD, WEAK=FAIL (default-saved becomes 0o600). Note probe_7 also HOLDS at base because the test host umask happens to yield 0o644 for the default case, so it is a regression/behavior probe, not the discriminator.

Weak candidate 'weak_0o600' (sets default to 0o600 instead of 0o644): a plausible wrong fix that still gives a consistent, non-None default and passes the override/per-instance/None criteria (probes 3,4,5,6). REJECTED by the suite via probes 1, 2, and 7 (default must be exactly 0o644). This demonstrates the suite discriminates a specific wrong value; it also would not resolve the hidden tests, which assert 0o644 exactly.

All required runs completed cleanly in the official image (patch applied cleanly each time). No requirement is unfaithful/too-strong (all mandated behaviors hold on gold) and no probe-conforming wrong fix was found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the actual changed observable behavior — the resolution of file_permissions_mode driven by the setting default, plus the preserved override/per-instance/None fallbacks and untouched directory-permission behavior. This matches FileSystemStorage's Setting-based lazy property resolution (setting > constructor arg > default). Boundary is correct (not a narrow slice), nothing forbidden that the code does, nothing invented. Base probe confirms divergence: base has FILE_UPLOAD_PERMISSIONS=None.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The single hidden-test value (0o644) is already public in the problem_statement ('Set default FILE_UPLOAD_PERMISSION to 0o644'). All named identifiers (FileSystemStorage, default_storage, file_permissions_mode, FILE_UPLOAD_PERMISSIONS, FILE_UPLOAD_DIRECTORY_PERMISSIONS, directory_permissions_mode, global_settings.py) are public Django API used to legitimately localize the change. The doc does NOT reveal the test file path/name (tests/test_utils/tests.py :: OverrideSettingsTests.test_override_file_upload_permissions), the specific 0o777 override constant the test uses, or any fix-invented identifier (the gold edit merely flips None->0o644). Override requirements are phrased generically ('any concrete numeric mode') rather than enumerating the test's cases. No case-enumeration reconstructs the parametrization. Requirement 3 (directory permissions unchanged) describes legitimate scoping consistent with a pre-existing PASS_TO_PASS test, not a transmission of hidden test code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
