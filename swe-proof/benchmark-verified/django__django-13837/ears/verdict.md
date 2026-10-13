# P2 adversarial audit — django__django-13837

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
## Positive control. Req 1.1 + 1.2: a NON-django package launched with -m must
## be relaunched as `-m <that package>`, using the actual __main__.__spec__.parent
## label, NOT hard-coded 'django'.
import sys, types
from unittest import mock
import importlib.machinery
from django.utils import autoreload

fake = types.ModuleType('__main__')
fake.__spec__ = importlib.machinery.ModuleSpec('mypkg.__main__', loader=None)
assert fake.__spec__.parent == 'mypkg', fake.__spec__.parent

with mock.patch.dict(sys.modules, {'__main__': fake}), \
     mock.patch('sys.argv', ['/some/where/__main__.py', 'runserver']), \
     mock.patch('sys.warnoptions', []):
    got = autoreload.get_child_arguments()

expected = [sys.executable, '-m', 'mypkg', 'runserver']
print('got     :', got)
print('expected:', expected)
sys.exit(0 if got == expected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
## Req 1.3: launched as `python -m django` -> `-m django` + trailing args preserved.
import sys, types
from unittest import mock
import importlib.machinery
from django.utils import autoreload

fake = types.ModuleType('__main__')
fake.__spec__ = importlib.machinery.ModuleSpec('django.__main__', loader=None)
assert fake.__spec__.parent == 'django'

with mock.patch.dict(sys.modules, {'__main__': fake}), \
     mock.patch('sys.argv', ['/x/django/__main__.py', 'runserver', '--noreload']), \
     mock.patch('sys.warnoptions', []):
    got = autoreload.get_child_arguments()

expected = [sys.executable, '-m', 'django', 'runserver', '--noreload']
print('got     :', got)
print('expected:', expected)
sys.exit(0 if got == expected else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
## Req 1.4 + 2.2: module launch preserves warning options AND trailing args
## exactly (argv[1:] in original order). Multiple trailing args + -W tokens.
import sys, types
from unittest import mock
import importlib.machinery
from django.utils import autoreload

fake = types.ModuleType('__main__')
fake.__spec__ = importlib.machinery.ModuleSpec('mypkg.__main__', loader=None)

with mock.patch.dict(sys.modules, {'__main__': fake}), \
     mock.patch('sys.argv', ['entry', 'runserver', '0:8000', '--extra', 'x']), \
     mock.patch('sys.warnoptions', ['error', 'ignore::DeprecationWarning']):
    got = autoreload.get_child_arguments()

expected = [sys.executable, '-Werror', '-Wignore::DeprecationWarning',
            '-m', 'mypkg', 'runserver', '0:8000', '--extra', 'x']
print('got     :', got)
print('expected:', expected)
sys.exit(0 if got == expected else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
## Req 3.1 + 2.1: non-module launch, script exists on disk -> interpreter +
## warn prefix + verbatim argv replay. Also Req 1.5: spec present but parent
## empty (top-level module, not a package) must NOT be treated as module launch.
import sys, types, os, tempfile
from unittest import mock
import importlib.machinery
from django.utils import autoreload

# Real existing script path.
fd, script = tempfile.mkstemp(suffix='.py'); os.close(fd)

# __spec__ with empty parent (e.g. `python -m somemodule` at top level) -> NOT module branch.
fake = types.ModuleType('__main__')
fake.__spec__ = importlib.machinery.ModuleSpec('toplevelmod', loader=None)
assert fake.__spec__.parent == ''

with mock.patch.dict(sys.modules, {'__main__': fake}), \
     mock.patch('sys.argv', [script, 'runserver', '--flag']), \
     mock.patch('sys.warnoptions', ['error']):
    got = autoreload.get_child_arguments()

expected = [sys.executable, '-Werror', script, 'runserver', '--flag']
print('got     :', got)
print('expected:', expected)
os.unlink(script)
sys.exit(0 if got == expected else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
## Req 3.4: non-module launch, script path missing and no fallback entry points
## exist -> RuntimeError mentioning the script does not exist.
import sys, types
from unittest import mock
import importlib.machinery
from django.utils import autoreload

fake = types.ModuleType('__main__')
fake.__spec__ = None  # not a module launch

missing = '/nonexistent/definitely/not/here/script.py'
with mock.patch.dict(sys.modules, {'__main__': fake}), \
     mock.patch('sys.argv', [missing, 'runserver']), \
     mock.patch('sys.warnoptions', []):
    try:
        got = autoreload.get_child_arguments()
        print('NO RAISE, got:', got)
        sys.exit(1)
    except RuntimeError as e:
        print('RuntimeError:', e)
        sys.exit(0 if 'does not exist' in str(e).lower() else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
## Req 3.3: non-module launch, script missing but <name>-script.py sibling
## exists -> interpreter + warn prefix + script entry + trailing args.
import sys, types, os, tempfile
from unittest import mock
import importlib.machinery
from django.utils import autoreload

d = tempfile.mkdtemp()
name = os.path.join(d, 'myprog')          # sys.argv[0], does not exist
scriptpy = name + '-script.py'            # sibling that DOES exist
open(scriptpy, 'w').close()

fake = types.ModuleType('__main__')
fake.__spec__ = None

with mock.patch.dict(sys.modules, {'__main__': fake}), \
     mock.patch('sys.argv', [name, 'runserver']), \
     mock.patch('sys.warnoptions', []):
    got = autoreload.get_child_arguments()

expected = [sys.executable, scriptpy, 'runserver']
print('got     :', got)
print('expected:', expected)
sys.exit(0 if got == expected else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
## Positive control. Req 1.1 + 1.2: a NON-django package launched with -m must
## be relaunched as `-m <that package>`, using the actual __main__.__spec__.parent
## label, NOT hard-coded 'django'.
import sys, types
from unittest import mock
import importlib.machinery
from django.utils import autoreload

fake = types.ModuleType('__main__')
fake.__spec__ = importlib.machinery.ModuleSpec('mypkg.__main__', loader=None)
assert fake.__spec__.parent == 'mypkg', fake.__spec__.parent

with mock.patch.dict(sys.modules, {'__main__': fake}), \
     mock.patch('sys.argv', ['/some/where/__main__.py', 'runserver']), \
     mock.patch('sys.warnoptions', []):
    got = autoreload.get_child_arguments()

expected = [sys.executable, '-m', 'mypkg', 'runserver']
print('got     :', got)
print('expected:', expected)
sys.exit(0 if got == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13837: get_child_arguments() must relaunch ANY `python -m <pkg>` entry point using __main__.__spec__.parent, not the hard-coded 'django' + __file__ comparison.

Probes (all HOLD on gold-patched tree; run in official image via nl_attack):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): non-django pkg 'mypkg' launched via -m -> ['-m','mypkg','runserver']. PATCHED: holds. BASE: FAILS (base raises RuntimeError 'Script ... does not exist' because it only recognizes django-by-__file__) => discriminates.
- probe_2 (Req 1.3): `python -m django` preserved -> ['-m','django','runserver','--noreload']. holds.
- probe_3 (Req 1.4/2.2): warn options (-Werror -Wignore::DeprecationWarning) preserved before -m, plus exact trailing argv[1:] order. holds.
- probe_4 (Req 3.1/2.1/1.5): __spec__.parent=='' (top-level module) NOT treated as -m launch; existing script -> interpreter+-Werror+verbatim argv. holds.
- probe_5 (Req 3.4): __spec__ None, script missing, no fallbacks -> RuntimeError 'does not exist'. holds.
- probe_6 (Req 3.3): __spec__ None, script missing but <name>-script.py sibling exists -> interpreter+script entry+trailing args. holds.

Candidate wrong patch 'hardcode_django_label' (weak.diff): detects -m launch via __spec__ correctly but always appends the literal 'django' label. REJECTED by probe_1 (got '-m django' vs expected '-m mypkg') and probe_3 (same), while probe_2 still passes. This demonstrates the suite discriminates the lazy/partial fix a weak reading permits. This candidate would also fail the hidden test test_run_as_non_django_module (expects '-m utils_tests.test_module').

All 6 probes HOLD patched; positive control FAILS at base and HOLDS patched; >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
## Positive control. Req 1.1 + 1.2: a NON-django package launched with -m must
## be relaunched as `-m <that package>`, using the actual __main__.__spec__.parent
## label, NOT hard-coded 'django'.
import sys, types
from unittest import mock
import importlib.machinery
from django.utils import autoreload

fake = types.ModuleType('__main__')
fake.__spec__ = importlib.machinery.ModuleSpec('mypkg.__main__', loader=None)
assert fake.__spec__.parent == 'mypkg', fake.__spec__.parent

with mock.patch.dict(sys.modules, {'__main__': fake}), \
     mock.patch('sys.argv', ['/some/where/__main__.py', 'runserver']), \
     mock.patch('sys.warnoptions', []):
    got = autoreload.get_child_arguments()

expected = [sys.executable, '-m', 'mypkg', 'runserver']
print('got     :', got)
print('expected:', expected)
sys.exit(0 if got == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13837: get_child_arguments() must relaunch ANY `python -m <pkg>` entry point using __main__.__spec__.parent, not the hard-coded 'django' + __file__ comparison.

Probes (all HOLD on gold-patched tree; run in official image via nl_attack):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): non-django pkg 'mypkg' launched via -m -> ['-m','mypkg','runserver']. PATCHED: holds. BASE: FAILS (base raises RuntimeError 'Script ... does not exist' because it only recognizes django-by-__file__) => discriminates.
- probe_2 (Req 1.3): `python -m django` preserved -> ['-m','django','runserver','--noreload']. holds.
- probe_3 (Req 1.4/2.2): warn options (-Werror -Wignore::DeprecationWarning) preserved before -m, plus exact trailing argv[1:] order. holds.
- probe_4 (Req 3.1/2.1/1.5): __spec__.parent=='' (top-level module) NOT treated as -m launch; existing script -> interpreter+-Werror+verbatim argv. holds.
- probe_5 (Req 3.4): __spec__ None, script missing, no fallbacks -> RuntimeError 'does not exist'. holds.
- probe_6 (Req 3.3): __spec__ None, script missing but <name>-script.py sibling exists -> interpreter+script entry+trailing args. holds.

Candidate wrong patch 'hardcode_django_label' (weak.diff): detects -m launch via __spec__ correctly but always appends the literal 'django' label. REJECTED by probe_1 (got '-m django' vs expected '-m mypkg') and probe_3 (same), while probe_2 still passes. This demonstrates the suite discriminates the lazy/partial fix a weak reading permits. This candidate would also fail the hidden test test_run_as_non_django_module (expects '-m utils_tests.test_module').

All 6 probes HOLD patched; positive control FAILS at base and HOLDS patched; >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch replaces the sys.argv[0]==django.__main__.__file__ comparison with a general check on __main__.__spec__ is not None and __main__.__spec__.parent, using that parent as the -m label. Requirements pin the FULL changed observable behavior of get_child_arguments across all branches (module launch generalized to any package, django preserved, script/exe/-script.py/RuntimeError branches unchanged), and correctly capture Req1.5 (spec-based detection, not __file__). Modeling boundary is the whole function, biconditional on module-launch detection — the right boundary, not a narrow slice. All acceptance criteria verified by live probe on the patched tree (exit 0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already discloses the complete fix algorithm (use __main__.__spec__ and __spec__.parent, 'python -m pkg iff __main__.__spec__.parent == "pkg"', avoiding __file__). requirements.md restates this as behavioral acceptance criteria without transmitting hidden-test material: no test names/paths (test_run_as_non_django_module never named), no fixture identifier (utils_tests.test_module / test_module/__main__.py never mentioned; non-django case kept generic as 'a differently named package'), no quoted test or gold code, no parametrization ids. Named symbols (get_child_arguments, restart_with_reloader, __main__.__spec__, sys.argv[0], __file__) are all public via problem_statement or legitimate localization. Req 3's fallback branches (exe-suffix, <name>-script.py, RuntimeError) describe pre-existing preserved source behavior (gold diff only touches the module-detection branch) as regression framing, not hidden-test reconstruction. The -Wall in Req 2/3.5 is an illustrative example of the generally-described -W<option> mechanism corresponding to pre-existing PASS_TO_PASS behavior, not a test-shaped case enumeration.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
