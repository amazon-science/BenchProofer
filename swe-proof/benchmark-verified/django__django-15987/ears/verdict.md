# P2 adversarial audit — django__django-15987

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
"""Req 1.1/1.2/1.5 + positive control: a FIXTURE_DIRS entry given as a Path
object naming an app's default fixtures dir SHALL be detected as a collision
and raise ImproperlyConfigured naming that app + the dir."""
import os, sys
from pathlib import Path
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DATABASES={},
    FIXTURE_DIRS=[],
)
import django
django.setup()

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.management.commands.loaddata import Command

app = apps.get_app_config("auth")
app_fixtures = os.path.join(app.path, "fixtures")
print("app_fixtures =", app_fixtures)

settings.FIXTURE_DIRS = [Path(app_fixtures)]
cmd = Command()
cmd.app_label = None
try:
    dirs = cmd.fixture_dirs
    print("NO ERROR RAISED, dirs =", dirs)
    sys.exit(1)
except ImproperlyConfigured as e:
    msg = str(e)
    print("raised ImproperlyConfigured:", msg)
    ok = ("auth" in msg) and (app_fixtures in msg)
    print("names app+dir:", ok)
    sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.3 (regression): a FIXTURE_DIRS entry given as a plain STRING naming an
app's default fixtures dir SHALL still be detected and raise ImproperlyConfigured
naming that app."""
import os, sys
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DATABASES={},
    FIXTURE_DIRS=[],
)
import django
django.setup()

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.management.commands.loaddata import Command

app = apps.get_app_config("auth")
app_fixtures = os.path.join(app.path, "fixtures")
settings.FIXTURE_DIRS = [app_fixtures]  # plain string
cmd = Command()
cmd.app_label = None
try:
    dirs = cmd.fixture_dirs
    print("NO ERROR RAISED, dirs =", dirs)
    sys.exit(1)
except ImproperlyConfigured as e:
    msg = str(e)
    print("raised:", msg)
    sys.exit(0 if ("auth" in msg and app_fixtures in msg) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1 (regression): duplicate entries in FIXTURE_DIRS SHALL raise
ImproperlyConfigured reporting duplicates."""
import sys
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DATABASES={},
    FIXTURE_DIRS=[],
)
import django
django.setup()

from django.core.exceptions import ImproperlyConfigured
from django.core.management.commands.loaddata import Command

settings.FIXTURE_DIRS = ["$SCRATCH", "$SCRATCH"]
cmd = Command()
cmd.app_label = None
try:
    dirs = cmd.fixture_dirs
    print("NO ERROR, dirs =", dirs)
    sys.exit(1)
except ImproperlyConfigured as e:
    msg = str(e)
    print("raised:", msg)
    sys.exit(0 if "duplicat" in msg.lower() else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.2/2.3/2.4/2.6: with no collision and no duplicates, the property SHALL
return the assembled list = each app's EXISTING default fixtures dir, then the
FIXTURE_DIRS entries, then the current dir, each realpath-normalized. Uses a
Path entry that does NOT collide (a temp dir) to also cover 2.3."""
import os, sys, tempfile
from pathlib import Path
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DATABASES={},
    FIXTURE_DIRS=[],
)
import django
django.setup()

from django.apps import apps
from django.core.management.commands.loaddata import Command

td = tempfile.mkdtemp(prefix="fixt_")
settings.FIXTURE_DIRS = [Path(td)]  # non-colliding Path
cmd = Command()
cmd.app_label = None
dirs = cmd.fixture_dirs
print("dirs =", dirs)

# Build expected composition.
expected = []
for app_config in apps.get_app_configs():
    ad = os.path.join(app_config.path, "fixtures")
    if os.path.isdir(ad):
        expected.append(ad)
expected.append(td)
expected.append("")
expected = [os.path.realpath(d) for d in expected]
print("expected =", expected)

if dirs != expected:
    print("MISMATCH")
    sys.exit(1)
# Path entry included, cwd at end, all normalized (absolute)
if os.path.realpath(td) not in dirs:
    print("Path entry missing"); sys.exit(1)
if dirs[-1] != os.path.realpath(""):
    print("cwd not last"); sys.exit(1)
if not all(os.path.isabs(d) for d in dirs):
    print("not all abs"); sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 1.4 + 2.5: collision guard applies across ALL installed apps even when a
specific app_label is targeted, and reports the FIRST offending app in
app-iteration order. We set app_label to a DIFFERENT app than the colliding one
(collision on 'auth', target 'contenttypes'), and expect it still raises naming
'auth'. Also checks 'first in iteration order' by making the first-iterated
colliding app the one reported."""
import os, sys
from pathlib import Path
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DATABASES={},
    FIXTURE_DIRS=[],
)
import django
django.setup()

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.management.commands.loaddata import Command

order = [ac.label for ac in apps.get_app_configs()]
print("iteration order:", order)
auth = apps.get_app_config("auth")
ct = apps.get_app_config("contenttypes")
auth_fx = os.path.join(auth.path, "fixtures")
ct_fx = os.path.join(ct.path, "fixtures")

# Both collide (as Path objects); expect the FIRST in iteration order reported.
first_label = order[0]
first_fx = os.path.join(apps.get_app_config(first_label).path, "fixtures")
settings.FIXTURE_DIRS = [Path(auth_fx), Path(ct_fx)]

cmd = Command()
cmd.app_label = "contenttypes"  # target a specific app; guard must still fire
try:
    dirs = cmd.fixture_dirs
    print("NO ERROR, dirs =", dirs)
    sys.exit(1)
except ImproperlyConfigured as e:
    msg = str(e)
    print("raised:", msg)
    # must name the first-iterated offending app
    ok = (first_label in msg) and (first_fx in msg)
    print("reports first offending app (%s):" % first_label, ok)
    sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1/1.2/1.5 + positive control: a FIXTURE_DIRS entry given as a Path
object naming an app's default fixtures dir SHALL be detected as a collision
and raise ImproperlyConfigured naming that app + the dir."""
import os, sys
from pathlib import Path
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DATABASES={},
    FIXTURE_DIRS=[],
)
import django
django.setup()

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.management.commands.loaddata import Command

app = apps.get_app_config("auth")
app_fixtures = os.path.join(app.path, "fixtures")
print("app_fixtures =", app_fixtures)

settings.FIXTURE_DIRS = [Path(app_fixtures)]
cmd = Command()
cmd.app_label = None
try:
    dirs = cmd.fixture_dirs
    print("NO ERROR RAISED, dirs =", dirs)
    sys.exit(1)
except ImproperlyConfigured as e:
    msg = str(e)
    print("raised ImproperlyConfigured:", msg)
    ok = ("auth" in msg) and (app_fixtures in msg)
    print("names app+dir:", ok)
    sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements pin the fixture_dirs default-collision check to compare textual locations so a Path entry naming an app's default fixtures dir is rejected like a string. Gold patch: `if app_dir in [str(d) for d in fixture_dirs]`.

Probes (all run in the official docker image):
- probe_1 (Req 1.1/1.2/1.5, POSITIVE CONTROL): Path(auth_fixtures) in FIXTURE_DIRS -> ImproperlyConfigured naming 'auth' + the dir. HOLDS patched; VIOLATED at base (no error, dir silently accepted); VIOLATED under weak candidate. Discriminates.
- probe_2 (Req 1.3 regression): plain-string entry still rejected. HOLDS patched AND base (unchanged behavior).
- probe_3 (Req 2.1 regression): duplicate FIXTURE_DIRS entries -> 'contains duplicates'. HOLDS both.
- probe_4 (Req 2.2/2.3/2.4/2.6): non-colliding Path entry accepted; returned list == [existing app default dirs..., FIXTURE_DIRS entries..., cwd], each realpath-normalized. HOLDS both.
- probe_5 (Req 1.4/2.5): collision guard fires across ALL apps even with app_label targeted at a different app, and reports the FIRST offending app in iteration order (contenttypes before auth). HOLDS patched; VIOLATED at base and under weak candidate.

Candidate patch weak.diff: `if str(app_dir) in fixture_dirs` — stringifies the (already-string) default dir instead of the entries. Rejected by probe_1 and probe_5 (Path entries still compare unequal to the string default), so it does NOT satisfy the probe suite => not a too-weak escape; demonstrates the suite discriminates a plausible wrong fix. probes 2/3/4 pass under it (expected, they don't touch the Path case).

Conclusion: >=5 distinct probes all hold on the gold-patched tree, positive control fails at base (prepatch reproduced), and a requirements-relevant wrong fix is rejected. Spec is faithful and discriminating -> SOUND.

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
"""Req 1.1/1.2/1.5 + positive control: a FIXTURE_DIRS entry given as a Path
object naming an app's default fixtures dir SHALL be detected as a collision
and raise ImproperlyConfigured naming that app + the dir."""
import os, sys
from pathlib import Path
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DATABASES={},
    FIXTURE_DIRS=[],
)
import django
django.setup()

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.management.commands.loaddata import Command

app = apps.get_app_config("auth")
app_fixtures = os.path.join(app.path, "fixtures")
print("app_fixtures =", app_fixtures)

settings.FIXTURE_DIRS = [Path(app_fixtures)]
cmd = Command()
cmd.app_label = None
try:
    dirs = cmd.fixture_dirs
    print("NO ERROR RAISED, dirs =", dirs)
    sys.exit(1)
except ImproperlyConfigured as e:
    msg = str(e)
    print("raised ImproperlyConfigured:", msg)
    ok = ("auth" in msg) and (app_fixtures in msg)
    print("names app+dir:", ok)
    sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements pin the fixture_dirs default-collision check to compare textual locations so a Path entry naming an app's default fixtures dir is rejected like a string. Gold patch: `if app_dir in [str(d) for d in fixture_dirs]`.

Probes (all run in the official docker image):
- probe_1 (Req 1.1/1.2/1.5, POSITIVE CONTROL): Path(auth_fixtures) in FIXTURE_DIRS -> ImproperlyConfigured naming 'auth' + the dir. HOLDS patched; VIOLATED at base (no error, dir silently accepted); VIOLATED under weak candidate. Discriminates.
- probe_2 (Req 1.3 regression): plain-string entry still rejected. HOLDS patched AND base (unchanged behavior).
- probe_3 (Req 2.1 regression): duplicate FIXTURE_DIRS entries -> 'contains duplicates'. HOLDS both.
- probe_4 (Req 2.2/2.3/2.4/2.6): non-colliding Path entry accepted; returned list == [existing app default dirs..., FIXTURE_DIRS entries..., cwd], each realpath-normalized. HOLDS both.
- probe_5 (Req 1.4/2.5): collision guard fires across ALL apps even with app_label targeted at a different app, and reports the FIRST offending app in iteration order (contenttypes before auth). HOLDS patched; VIOLATED at base and under weak candidate.

Candidate patch weak.diff: `if str(app_dir) in fixture_dirs` — stringifies the (already-string) default dir instead of the entries. Rejected by probe_1 and probe_5 (Path entries still compare unequal to the string default), so it does NOT satisfy the probe suite => not a too-weak escape; demonstrates the suite discriminates a plausible wrong fix. probes 2/3/4 pass under it (expected, they don't touch the Path case).

Conclusion: >=5 distinct probes all hold on the gold-patched tree, positive control fails at base (prepatch reproduced), and a requirements-relevant wrong fix is rejected. Spec is faithful and discriminating -> SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reconstructed full patched fixture_dirs via inspect.getsource inside the image and functionally exercised all five behavioral requirements with live probes on the gold-patched tree; all held. patch.diff and instance.json patch agree (single-line str() coercion in the membership test). No forbidden/invented/mis-boundaried behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the behavioral fix (per-application default-directory collision check must compare textual locations so that a FIXTURE_DIRS entry given as a pathlib.Path is rejected identically to a string) — a legitimate translation of the gold edit `app_dir in [str(d) for d in fixture_dirs]`, not a transmission of it. Naming loaddata.py / fixture_dirs / Command / ImproperlyConfigured / os.path.join is legitimate localization. No test file path, test function/class names, parametrization ids, docstrings, or verbatim test/gold code are quoted. The FAIL_TO_PASS docstring text ('settings.FIXTURE_DIRS cannot contain a default fixtures directory...') is not reproduced verbatim. Req 1.4 (first offending app in iteration order) is derivable from reading the loop, not from any test. Req 2.6's enumeration (relative paths / strings / dot segments) loosely echoes existing PASS_TO_PASS regression test names but describes general path-handling behavior to be preserved rather than reconstructing hidden test cases; borderline but does not cross into leakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
