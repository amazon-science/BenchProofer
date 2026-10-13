# P2 adversarial audit — django__django-15104

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control (Req1.1 / Req1.2): a related field whose deconstruction OMITS
# the 'to' entry must normalize WITHOUT raising, carrying kwargs over unchanged.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState

class HardcodedForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        kwargs['to'] = 'testapp.Author'
        super().__init__(*args, **kwargs)
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['to']
        return name, path, args, kwargs

f = HardcodedForeignKey(on_delete=models.CASCADE)
assert f.remote_field and f.remote_field.model, "field must point at another model"

ad = MigrationAutodetector(ProjectState(), ProjectState())
try:
    out = ad.only_relation_agnostic_fields({'author': f})
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    raise SystemExit(1)
print("OK normalized:", out)
# kwargs carried over: 'to' was absent, must still be absent, nothing removed erroneously
kwargs = out[0][2]
assert 'to' not in kwargs, "unexpected 'to' present"
print("OK: no crash, kwargs carried over unchanged")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.3: adding a new model with a hardcoded-target related field between two
# states -> exactly one CreateModel change for that model, no error.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState, ModelState

class HardcodedForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        kwargs['to'] = 'testapp.Author'
        super().__init__(*args, **kwargs)
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['to']
        return name, path, args, kwargs

author = ModelState('testapp','Author',[('id', models.AutoField(primary_key=True))])
book = ModelState('testapp','Book',[
    ('id', models.AutoField(primary_key=True)),
    ('author', HardcodedForeignKey(on_delete=models.CASCADE)),
])
before = ProjectState(); before.add_model(author)
after = ProjectState(); after.add_model(author); after.add_model(book)

ad = MigrationAutodetector(before, after)
try:
    changes = ad._detect_changes()
except Exception as e:
    print("FAIL: change detection aborted:", type(e).__name__, e); raise SystemExit(1)
migs = changes.get('testapp', [])
print("num migrations:", len(migs))
assert len(migs)==1, "expected exactly 1 migration"
ops = migs[0].operations
optypes = [type(o).__name__ for o in ops]
print("op types:", optypes)
assert optypes==['CreateModel'], "expected single CreateModel"
assert ops[0].name=='Book', "created model must be Book"
print("OK: exactly one CreateModel(Book)")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2.1/2.2: a related field that DOES record 'to' -> 'to' removed, but path,
# args and every other kwarg preserved.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState

f = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='things')
ad = MigrationAutodetector(ProjectState(), ProjectState())
# reference: raw deconstruction
ref = ad.deep_deconstruct(f)
print("raw kwargs:", ref[2])
assert 'to' in ref[2], "sanity: raw deconstruction should contain 'to'"
out = ad.only_relation_agnostic_fields({'x': f})[0]
print("normalized:", out)
assert 'to' not in out[2], "FAIL: 'to' not removed"
# path and args unchanged
assert out[0]==ref[0], "path changed"
assert out[1]==ref[1], "args changed"
# every other kwarg unchanged
expected = {k:v for k,v in ref[2].items() if k!='to'}
assert out[2]==expected, ("other kwargs changed", out[2], expected)
print("OK: 'to' removed, path/args/other-kwargs preserved")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.1: a non-relational field is carried over verbatim (path/args/kwargs).
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState

f = models.CharField(max_length=42, null=True, default='hi')
assert not (f.remote_field and f.remote_field.model), "must be non-relational"
ad = MigrationAutodetector(ProjectState(), ProjectState())
ref = ad.deep_deconstruct(f)
out = ad.only_relation_agnostic_fields({'x': f})[0]
print("ref:", ref)
print("out:", out)
assert out==ref, "FAIL: non-relational field not carried over verbatim"
print("OK: non-relational field verbatim")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3.2: fields visited in sorted order, one entry per field, no drop/dup/reorder.
# Also Req3.3: 'to' removed only for relational fields.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState

class HardcodedForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        kwargs['to'] = 'testapp.Author'
        super().__init__(*args, **kwargs)
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['to']
        return name, path, args, kwargs

fields = {
    'zeta': models.IntegerField(default=1),
    'alpha': models.ForeignKey('auth.User', on_delete=models.CASCADE),  # has 'to'
    'mid': HardcodedForeignKey(on_delete=models.CASCADE),               # no 'to'
    'beta': models.CharField(max_length=5),
}
ad = MigrationAutodetector(ProjectState(), ProjectState())
out = ad.only_relation_agnostic_fields(fields)
print("count:", len(out))
assert len(out)==len(fields), "field count mismatch (drop/dup)"
# reconstruct which entry maps to which by comparing to per-field normalization
# order must be sorted(field names): alpha, beta, mid, zeta
sorted_names = sorted(fields.keys())
print("sorted names:", sorted_names)
for i, nm in enumerate(sorted_names):
    single = ad.only_relation_agnostic_fields({nm: fields[nm]})[0]
    assert out[i]==single, ("order/content mismatch at", i, nm, out[i], single)
# relational ('alpha') had 'to' removed; non-relational never has 'to'
alpha = out[sorted_names.index('alpha')]
assert 'to' not in alpha[2], "alpha 'to' should be removed"
beta = out[sorted_names.index('beta')]
assert 'to' not in beta[2], "non-relational shouldn't have 'to'"
print("OK: sorted order, one-per-field, no drop/dup/reorder; 'to' handling correct")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control (Req1.1 / Req1.2): a related field whose deconstruction OMITS
# the 'to' entry must normalize WITHOUT raising, carrying kwargs over unchanged.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState

class HardcodedForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        kwargs['to'] = 'testapp.Author'
        super().__init__(*args, **kwargs)
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['to']
        return name, path, args, kwargs

f = HardcodedForeignKey(on_delete=models.CASCADE)
assert f.remote_field and f.remote_field.model, "field must point at another model"

ad = MigrationAutodetector(ProjectState(), ProjectState())
try:
    out = ad.only_relation_agnostic_fields({'author': f})
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    raise SystemExit(1)
print("OK normalized:", out)
# kwargs carried over: 'to' was absent, must still be absent, nothing removed erroneously
kwargs = out[0][2]
assert 'to' not in kwargs, "unexpected 'to' present"
print("OK: no crash, kwargs carried over unchanged")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the gold fix (django/db/migrations/autodetector.py: `del deconstruction[2]['to']` -> `deconstruction[2].pop('to', None)`).

Probes (all exit 0 iff criterion holds; all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): a related field whose deconstruction omits 'to' normalizes without raising, kwargs carried over. HOLDS patched; FAILS at base with KeyError 'to' (prepatch reproduced) -> discriminating.
- probe_2 (Req1.3): adding a new model with a hardcoded-target related field yields exactly one CreateModel(Book), no error. HOLDS patched.
- probe_3 (Req2.1/2.2): a related field that DOES record 'to' has 'to' removed while path/args/all other kwargs preserved. HOLDS patched.
- probe_4 (Req3.1): a non-relational field carried over verbatim (path/args/kwargs). HOLDS patched.
- probe_5 (Req3.2/3.3): fields visited in sorted order, one-per-field, no drop/dup/reorder; 'to' removed only for relational fields. HOLDS patched.

Candidate patches:
- wrong_drop_removal.diff (lazy/partial reading: delete the 'to'-removal branch entirely). Tolerates missing 'to' so passes Req1 probes (1,2) and Req3.1 (4), but VIOLATES Req2 -> REJECTED by probe_3 (assert 'to' not removed) and probe_5 (alpha 'to' not removed). Demonstrates the suite discriminates a wrong fix.
- weak_tryexcept.diff (try/except KeyError around the del): behaviorally equivalent to the gold pop() approach; PASSES all 5 probes and would also resolve the hidden test -> a legitimate equivalent fix, NOT a too-weak finding.

No requirements-conforming alternative that fails the hidden test was found: the F2P behavior (no KeyError while still stripping 'to' for real targets) is exactly what probes 1-3/5 pin. Verdict SOUND: >=5 probes hold, positive control discriminates (patched pass / base KeyError), and at least one wrong candidate is rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Positive control (Req1.1 / Req1.2): a related field whose deconstruction OMITS
# the 'to' entry must normalize WITHOUT raising, carrying kwargs over unchanged.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                        DATABASES={}, USE_TZ=False)
django.setup()
from django.db import models
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState

class HardcodedForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        kwargs['to'] = 'testapp.Author'
        super().__init__(*args, **kwargs)
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['to']
        return name, path, args, kwargs

f = HardcodedForeignKey(on_delete=models.CASCADE)
assert f.remote_field and f.remote_field.model, "field must point at another model"

ad = MigrationAutodetector(ProjectState(), ProjectState())
try:
    out = ad.only_relation_agnostic_fields({'author': f})
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    raise SystemExit(1)
print("OK normalized:", out)
# kwargs carried over: 'to' was absent, must still be absent, nothing removed erroneously
kwargs = out[0][2]
assert 'to' not in kwargs, "unexpected 'to' present"
print("OK: no crash, kwargs carried over unchanged")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the gold fix (django/db/migrations/autodetector.py: `del deconstruction[2]['to']` -> `deconstruction[2].pop('to', None)`).

Probes (all exit 0 iff criterion holds; all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): a related field whose deconstruction omits 'to' normalizes without raising, kwargs carried over. HOLDS patched; FAILS at base with KeyError 'to' (prepatch reproduced) -> discriminating.
- probe_2 (Req1.3): adding a new model with a hardcoded-target related field yields exactly one CreateModel(Book), no error. HOLDS patched.
- probe_3 (Req2.1/2.2): a related field that DOES record 'to' has 'to' removed while path/args/all other kwargs preserved. HOLDS patched.
- probe_4 (Req3.1): a non-relational field carried over verbatim (path/args/kwargs). HOLDS patched.
- probe_5 (Req3.2/3.3): fields visited in sorted order, one-per-field, no drop/dup/reorder; 'to' removed only for relational fields. HOLDS patched.

Candidate patches:
- wrong_drop_removal.diff (lazy/partial reading: delete the 'to'-removal branch entirely). Tolerates missing 'to' so passes Req1 probes (1,2) and Req3.1 (4), but VIOLATES Req2 -> REJECTED by probe_3 (assert 'to' not removed) and probe_5 (alpha 'to' not removed). Demonstrates the suite discriminates a wrong fix.
- weak_tryexcept.diff (try/except KeyError around the del): behaviorally equivalent to the gold pop() approach; PASSES all 5 probes and would also resolve the hidden test -> a legitimate equivalent fix, NOT a too-weak finding.

No requirements-conforming alternative that fails the hidden test was found: the F2P behavior (no KeyError while still stripping 'to' for real targets) is exactly what probes 1-3/5 pin. Verdict SOUND: >=5 probes hold, positive control discriminates (patched pass / base KeyError), and at least one wrong candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed in the instance image. BASE (unpatched) reproduces the issue exactly: MigrationAutodetector with a CustomFKField that hardcodes 'to' and drops it from deconstruct() crashes with KeyError: 'to' at autodetector.py:99 (matches the problem_statement traceback). GOLD-PATCHED: (Req1) same scenario yields a single CreateModel change with no error [REQ1_OK ['CreateModel']]; (Req2) a normal ForeignKey('testapp.Target') is still made target-agnostic — deconstructed kwargs = {'on_delete': CASCADE} with 'to' removed and other kwargs preserved; (Req3) a CharField(max_length=5) is carried over verbatim {'max_length': 5}. Requirements correctly model the changed observable behavior (tolerant target removal) and the biconditional boundary (remove 'to' iff field.remote_field.model and the entry is present), matching the real code and issue. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md localizes the change to the public function only_relation_agnostic_fields and describes behavior (tolerate absent target entry; KeyError avoidance; single create-model result). All of this is derivable from the PUBLIC problem_statement, which already contains a full reproduction, the KeyError traceback pointing at only_relation_agnostic_fields, the custom FK that hardcodes 'to' and deletes it in deconstruct(), and the proposed fix (del -> pop('to', None)) plus the len(changes)==1 assertion. The document contains NONE of the hidden-test identifiers: no test name test_add_custom_fk_with_hardcoded_to, no HardcodedForeignKey/testapp.Author/Book, no assertNumberMigrations/assertOperationTypes('CreateModel')/assertOperationAttributes, no test file path or parametrization ids, and no verbatim gold-patch line. Req 1.3's 'single create-model change for the added model' is behavioral and already implied by the public repro; it mirrors expected behavior, not the test's parametrized structure. No semantic leakage beyond the problem_statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
