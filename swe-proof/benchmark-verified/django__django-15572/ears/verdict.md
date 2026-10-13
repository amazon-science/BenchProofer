# P2 adversarial audit — django__django-15572

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1 / Req1.4 (POSITIVE CONTROL): an empty-string entry in a
DjangoTemplates backend's engine.dirs must NOT contribute the project root
(cwd) to the returned set.  Holds on patched, fails at base."""
import os
from pathlib import Path

import django
from django.conf import settings

BASE = Path(os.getcwd())
real_dir = str(BASE / "real_templates")

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["", real_dir],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
)
django.setup()

from django.template.autoreload import get_template_directories

dirs = get_template_directories()
cwd = Path.cwd()
print("returned dirs:", sorted(str(d) for d in dirs))
print("cwd:", cwd)

if cwd in dirs:
    print("FAIL: project root (cwd) was added from empty entry")
    raise SystemExit(1)
if (cwd / Path(real_dir)) not in dirs and Path(real_dir) not in dirs:
    print("FAIL: real dir missing")
    raise SystemExit(1)
print("PASS: empty entry ignored, real dir present")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 / Req1.4: a loader whose get_dirs() returns an empty-string entry
must NOT contribute the project root (cwd) to the returned set, while a valid
loader-reported dir IS included (Req2.2)."""
import os
from pathlib import Path

import django
from django.conf import settings

BASE = Path(os.getcwd())
loader_dir = str(BASE / "loader_templates")

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
)
django.setup()

from django.template import engines
from django.template.backends.django import DjangoTemplates
from django.template.autoreload import get_template_directories


class FakeLoader:
    def __init__(self, dirs):
        self._dirs = dirs

    def get_dirs(self):
        return self._dirs


backend = [b for b in engines.all() if isinstance(b, DjangoTemplates)][0]
backend.engine.template_loaders = [FakeLoader(["", loader_dir])]

dirs = get_template_directories()
cwd = Path.cwd()
print("returned dirs:", sorted(str(d) for d in dirs))
print("cwd:", cwd)

if cwd in dirs:
    print("FAIL: project root added from empty loader entry")
    raise SystemExit(1)
if Path(loader_dir) not in dirs:
    print("FAIL: valid loader dir missing")
    raise SystemExit(1)
print("PASS: empty loader entry ignored, valid loader dir present")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.3: if the ONLY directory entries across all backends and loaders are
empty strings, get_template_directories() SHALL return an EMPTY set."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["", ""],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
)
django.setup()

from django.template import engines
from django.template.backends.django import DjangoTemplates
from django.template.autoreload import get_template_directories


class FakeLoader:
    def get_dirs(self):
        return ["", ""]


backend = [b for b in engines.all() if isinstance(b, DjangoTemplates)][0]
backend.engine.template_loaders = [FakeLoader()]

dirs = get_template_directories()
print("returned dirs:", sorted(str(d) for d in dirs))
if dirs != set():
    print("FAIL: expected empty set, got", dirs)
    raise SystemExit(1)
print("PASS: empty set returned")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.3 (regression): loader-reported directories that lie inside Django's
own tree SHALL keep being excluded from the returned set."""
import os
from pathlib import Path

import django
from django.conf import settings

BASE = Path(os.getcwd())
outside_dir = str(BASE / "app_templates")

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
)
django.setup()

import django as dj
from django.template import engines
from django.template.backends.django import DjangoTemplates
from django.template.autoreload import get_template_directories

django_root = Path(dj.__file__).parent
inside_dir = str(django_root / "forms" / "templates")


class FakeLoader:
    def get_dirs(self):
        return [inside_dir, outside_dir]


backend = [b for b in engines.all() if isinstance(b, DjangoTemplates)][0]
backend.engine.template_loaders = [FakeLoader()]

dirs = get_template_directories()
print("returned dirs:", sorted(str(d) for d in dirs))
print("django-internal dir:", inside_dir)

if Path(inside_dir) in dirs:
    print("FAIL: django-internal dir was NOT excluded")
    raise SystemExit(1)
if Path(outside_dir) not in dirs:
    print("FAIL: non-django loader dir missing")
    raise SystemExit(1)
print("PASS: django-internal dir excluded, outside dir kept")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.2/3.3/3.4 (regression): template_changed() behavior.
- a .py file change returns None (no template change, no reset)
- a non-py file under a collected template dir resets loaders and returns True
- a non-py file NOT under any collected dir returns None"""
import os
from pathlib import Path

import django
from django.conf import settings

BASE = Path(os.getcwd())
tpl_dir = BASE / "watched_templates"

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["", str(tpl_dir)],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
)
django.setup()

from django.template import autoreload as ar

reset_calls = []
orig_reset = ar.reset_loaders
ar.reset_loaders = lambda: reset_calls.append(1)

# 1. .py file under the template dir -> no change reported, no reset
py_path = tpl_dir / "sub" / "module.py"
r1 = ar.template_changed(None, file_path=py_path)
print("py file result:", r1, "reset_calls:", len(reset_calls))
if r1 is not None or reset_calls:
    print("FAIL: .py change should be ignored")
    raise SystemExit(1)

# 2. non-py file under the template dir -> reset + True
html_path = tpl_dir / "sub" / "index.html"
r2 = ar.template_changed(None, file_path=html_path)
print("html-in-dir result:", r2, "reset_calls:", len(reset_calls))
if r2 is not True or len(reset_calls) != 1:
    print("FAIL: non-py file under template dir should reset+return True")
    raise SystemExit(1)

# 3. non-py file NOT under any collected dir -> None, no extra reset
outside = BASE / "elsewhere" / "index.html"
r3 = ar.template_changed(None, file_path=outside)
print("html-outside result:", r3, "reset_calls:", len(reset_calls))
if r3 is not None or len(reset_calls) != 1:
    print("FAIL: non-py file outside template dirs should not report change")
    raise SystemExit(1)

print("PASS: change-detection behavior correct")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2.1 / Req2.6 (regression): a NON-EMPTY entry that normalizes to cwd
(e.g. ".") SHALL still be included as an absolute path. This guards against a
lazy fix that simply discards cwd from the result."""
import os
from pathlib import Path

import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["."],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
)
django.setup()

from django.template.autoreload import get_template_directories

dirs = get_template_directories()
cwd = Path.cwd()
print("returned dirs:", sorted(str(d) for d in dirs))
print("cwd:", cwd)

# "." joined onto cwd normalizes to cwd
if cwd not in dirs:
    print("FAIL: non-empty '.' entry did not yield cwd")
    raise SystemExit(1)
print("PASS: non-empty '.' entry correctly yields cwd")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 / Req1.4 (POSITIVE CONTROL): an empty-string entry in a
DjangoTemplates backend's engine.dirs must NOT contribute the project root
(cwd) to the returned set.  Holds on patched, fails at base."""
import os
from pathlib import Path

import django
from django.conf import settings

BASE = Path(os.getcwd())
real_dir = str(BASE / "real_templates")

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["", real_dir],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
)
django.setup()

from django.template.autoreload import get_template_directories

dirs = get_template_directories()
cwd = Path.cwd()
print("returned dirs:", sorted(str(d) for d in dirs))
print("cwd:", cwd)

if cwd in dirs:
    print("FAIL: project root (cwd) was added from empty entry")
    raise SystemExit(1)
if (cwd / Path(real_dir)) not in dirs and Path(real_dir) not in dirs:
    print("FAIL: real dir missing")
    raise SystemExit(1)
print("PASS: empty entry ignored, real dir present")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully describe the gold fix (filter falsy entries from BOTH backend.engine.dirs AND loader.get_dirs()). 6 probes, all HOLD on gold-patched tree.

Probe->criterion->results:
- probe_1 (Req1.1/1.4, POSITIVE CONTROL): empty '' in engine.dirs must not add cwd. PATCHED pass / BASE fail (base returns {/testbed, /testbed/real_templates}). Discriminates.
- probe_2 (Req1.2/1.4, Req2.2): empty '' from loader.get_dirs() must not add cwd; valid loader dir kept. PATCHED pass / BASE fail.
- probe_3 (Req1.3): only-empty entries across backends+loaders => empty set. PATCHED pass ([]) / BASE fail ({/testbed}).
- probe_4 (Req2.3): django-internal loader dir excluded, outside dir kept. PATCHED pass / BASE pass (pure regression guard, not expected to discriminate).
- probe_5 (Req3.2/3.3/3.4): template_changed .py->None/no-reset; non-py in dir->reset+True; non-py outside->None. PATCHED pass / BASE fail (at base cwd is watched so the 'outside' html spuriously reports change).
- probe_6 (Req2.1/2.6): non-empty '.' entry (normalizes to cwd) must STILL yield cwd. PATCHED pass / BASE pass — guards against a lazy discard-cwd fix.

Candidate wrong patches, both REJECTED by the suite:
- weak_partial.diff: filters only engine.dirs (`if dir`) but NOT loader.get_dirs(). REJECTED by probe_2 (loader '' still adds cwd) and probe_3 (non-empty set). This is exactly the partial reading a weak spec would permit; the loader-side criteria (Req1.2) catch it.
- weak_discardcwd.diff: keeps empty entries but strips cwd from the final set (`{item for item in items if item != cwd}`). Superficially passes the empty-entry probes but REJECTED by probe_6: a legitimate '.' DIRS entry (which normalizes to cwd) is wrongly dropped, violating Req2.1/2.6.

No requirement is too strong (every mandated behavior holds on gold-patched tree) and none is too weak (both requirements-plausible wrong fixes are rejected by >=1 probe). SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 / Req1.4 (POSITIVE CONTROL): an empty-string entry in a
DjangoTemplates backend's engine.dirs must NOT contribute the project root
(cwd) to the returned set.  Holds on patched, fails at base."""
import os
from pathlib import Path

import django
from django.conf import settings

BASE = Path(os.getcwd())
real_dir = str(BASE / "real_templates")

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["", real_dir],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
)
django.setup()

from django.template.autoreload import get_template_directories

dirs = get_template_directories()
cwd = Path.cwd()
print("returned dirs:", sorted(str(d) for d in dirs))
print("cwd:", cwd)

if cwd in dirs:
    print("FAIL: project root (cwd) was added from empty entry")
    raise SystemExit(1)
if (cwd / Path(real_dir)) not in dirs and Path(real_dir) not in dirs:
    print("FAIL: real dir missing")
    raise SystemExit(1)
print("PASS: empty entry ignored, real dir present")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements faithfully describe the gold fix (filter falsy entries from BOTH backend.engine.dirs AND loader.get_dirs()). 6 probes, all HOLD on gold-patched tree.

Probe->criterion->results:
- probe_1 (Req1.1/1.4, POSITIVE CONTROL): empty '' in engine.dirs must not add cwd. PATCHED pass / BASE fail (base returns {/testbed, /testbed/real_templates}). Discriminates.
- probe_2 (Req1.2/1.4, Req2.2): empty '' from loader.get_dirs() must not add cwd; valid loader dir kept. PATCHED pass / BASE fail.
- probe_3 (Req1.3): only-empty entries across backends+loaders => empty set. PATCHED pass ([]) / BASE fail ({/testbed}).
- probe_4 (Req2.3): django-internal loader dir excluded, outside dir kept. PATCHED pass / BASE pass (pure regression guard, not expected to discriminate).
- probe_5 (Req3.2/3.3/3.4): template_changed .py->None/no-reset; non-py in dir->reset+True; non-py outside->None. PATCHED pass / BASE fail (at base cwd is watched so the 'outside' html spuriously reports change).
- probe_6 (Req2.1/2.6): non-empty '.' entry (normalizes to cwd) must STILL yield cwd. PATCHED pass / BASE pass — guards against a lazy discard-cwd fix.

Candidate wrong patches, both REJECTED by the suite:
- weak_partial.diff: filters only engine.dirs (`if dir`) but NOT loader.get_dirs(). REJECTED by probe_2 (loader '' still adds cwd) and probe_3 (non-empty set). This is exactly the partial reading a weak spec would permit; the loader-side criteria (Req1.2) catch it.
- weak_discardcwd.diff: keeps empty entries but strips cwd from the final set (`{item for item in items if item != cwd}`). Superficially passes the empty-entry probes but REJECTED by probe_6: a legitimate '.' DIRS entry (which normalizes to cwd) is wrongly dropped, violating Req2.1/2.6.

No requirement is too strong (every mandated behavior holds on gold-patched tree) and none is too weak (both requirements-plausible wrong fixes are rejected by >=1 probe). SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe HOLDS on gold (RESULT ['/testbed/more','/testbed/templates'], cwd absent), VIOLATED at base (project root watched). Both changed sources (engine.dirs and loader.get_dirs) are covered by requirements 1.1 and 1.2 respectively — modeling boundary matches the changed observable behavior, no narrow-slice defect. is_django_path exclusion (Req 2.3) and non-DjangoTemplates/no-get_dirs skips (Req 2.4) match unchanged source. Req 3 accurately reflects the untouched template_changed (.py suffix skip, parent-dir match resets loaders/returns True).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior using only pre-existing source identifiers (get_template_directories, template_changed, reset_loaders, backend.engine.dirs, loader.get_dirs, is_django_path, to_path, Path.cwd) — legitimate localization. The gold edit invents no new identifier (just adds `if dir` / `if directory and ...` guards), so nothing fix-invented can leak. No test file path, no test function/class names (test_template_dirs_ignore_empty_path, TemplateReloadTests, Jinja2TemplateReloadTests), no parametrization ids, no quoted test/gold code. The empty-string->project-root regression and the os.getenv(...).split(',') = [''] example come directly from the public problem_statement. Requirement 3's change-detection prose (.py suffix -> no reset; non-py under a watched dir -> reset) reflects the actual template_changed() source logic, readable from the module, not the hidden tests; it describes preserved behavior rather than reconstructing the FAIL_TO_PASS/PASS_TO_PASS cases.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
