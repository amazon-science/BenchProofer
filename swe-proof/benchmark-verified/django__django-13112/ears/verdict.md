# P2 adversarial audit — django__django-13112

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
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import ForeignKey, CASCADE

# Req 1.1/1.2 (positive control): app-qualified FK string keeps app-label case,
# lowercases model-name segment.
f = ForeignKey('DJ_RegLogin.Category', on_delete=CASCADE)
name, path, args, kwargs = f.deconstruct()
to = kwargs['to']
print("deconstructed to =", repr(to))
expected = 'DJ_RegLogin.category'
if to != expected:
    print("FAIL: expected", repr(expected))
    raise SystemExit(1)
print("PASS")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import ForeignKey, CASCADE

# Req 1.4: the deconstructed value SHALL differ from the fully-lowercased form
# whenever the app-label segment has an upper-case char.
ref = 'DJ_RegLogin.Category'
f = ForeignKey(ref, on_delete=CASCADE)
to = f.deconstruct()[3]['to']
print("to =", repr(to), " lower =", repr(ref.lower()))
if to == ref.lower():
    print("FAIL: equals fully-lowercased form")
    raise SystemExit(1)
# and specifically the app-label segment upper-case chars preserved
if to.split('.')[0] != 'DJ_RegLogin':
    print("FAIL: app label not preserved")
    raise SystemExit(1)
print("PASS")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import ForeignKey, CASCADE

# Req 2.1: bare string (no '.') lowercased entirely.
f = ForeignKey('MyModel', on_delete=CASCADE)
to = f.deconstruct()[3]['to']
print("bare to =", repr(to))
if to != 'mymodel':
    print("FAIL")
    raise SystemExit(1)
print("PASS")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={})
django.setup()
from django.db.models import ForeignKey, CASCADE
from django.contrib.auth.models import User

# Req 2.2: non-string target (a model class) -> model's label_lower.
f = ForeignKey(User, on_delete=CASCADE)
to = f.deconstruct()[3]['to']
print("class to =", repr(to), " label_lower =", repr(User._meta.label_lower))
if to != User._meta.label_lower:
    print("FAIL")
    raise SystemExit(1)
# also confirm on_delete kwarg preserved (Req 2.3)
kwargs = f.deconstruct()[3]
print("on_delete =", kwargs.get('on_delete'))
if kwargs.get('on_delete') is not CASCADE:
    print("FAIL: on_delete not preserved")
    raise SystemExit(1)
print("PASS")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import ManyToManyField

# Req 2.4: M2M string reference retained VERBATIM (both segments), bare and qualified.
for ref in ('DJ_RegLogin.Category', 'Category', 'MyModel'):
    f = ManyToManyField(ref)
    to = f.deconstruct()[3]['to']
    print(ref, "->", repr(to))
    if to != ref:
        print("FAIL: M2M altered", ref, "->", to)
        raise SystemExit(1)
print("PASS")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
django.setup()

from django.db import models
from django.db.migrations.state import ModelState, ProjectState

# Req 3.1/3.2/3.3: build state from the DECONSTRUCTED forms of FK and M2M fields
# whose target is an app-qualified string with a mixed-case app label. Every
# lazy reference must still name the correctly-cased app label so the registry
# renders and reports the same number of models added.
app_label = "DJ_RegLogin"

fk = models.ForeignKey("%s.Author" % app_label, models.CASCADE)
m2m = models.ManyToManyField("%s.Author" % app_label)
fk_to = fk.deconstruct()[3]['to']
m2m_to = m2m.deconstruct()[3]['to']
print("fk_to =", repr(fk_to), " m2m_to =", repr(m2m_to))

# Every lazy reference must still name app label with matching case (Req 3.3)
for to in (fk_to, m2m_to):
    seg = to.split('.')[0]
    if seg != app_label:
        print("FAIL: app label case lost:", repr(to))
        raise SystemExit(1)

# Rebuild state using the deconstructed reference strings
ps = ProjectState()
ps.add_model(ModelState(app_label, "Author", [
    ("id", models.AutoField(primary_key=True)),
]))
ps.add_model(ModelState(app_label, "Book", [
    ("id", models.AutoField(primary_key=True)),
    ("author", models.ForeignKey(fk_to, models.CASCADE)),
]))
ps.add_model(ModelState(app_label, "Magazine", [
    ("id", models.AutoField(primary_key=True)),
    ("authors", models.ManyToManyField(m2m_to)),
]))

apps = ps.apps  # renders registry; raises on dangling lazy refs
n = len(apps.get_models())
print("rendered models:", n)
if n != 3:
    print("FAIL: expected 3 models, got", n)
    raise SystemExit(1)
print("PASS")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import ForeignKey, CASCADE

# Req 1.1/1.2 (positive control): app-qualified FK string keeps app-label case,
# lowercases model-name segment.
f = ForeignKey('DJ_RegLogin.Category', on_delete=CASCADE)
name, path, args, kwargs = f.deconstruct()
to = kwargs['to']
print("deconstructed to =", repr(to))
expected = 'DJ_RegLogin.category'
if to != expected:
    print("FAIL: expected", repr(expected))
    raise SystemExit(1)
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes covering all three requirements, all HOLD on the gold-patched tree.

Probe->criterion->result (base | patched | weak-candidate):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): FK 'DJ_RegLogin.Category' deconstructs to 'DJ_RegLogin.category'. base=VIOLATED ('dj_reglogin.category') | patched=HOLDS | weak=VIOLATED.
- probe_2 (Req 1.4): deconstructed 'to' differs from fully-lowercased form and app label preserved. base=VIOLATED | patched=HOLDS | weak=VIOLATED.
- probe_3 (Req 2.1): bare string 'MyModel' -> 'mymodel'. patched=HOLDS | weak=HOLDS.
- probe_4 (Req 2.2/2.3): model class target -> label_lower ('auth.user'); on_delete kwarg preserved. patched=HOLDS | weak=HOLDS.
- probe_5 (Req 2.4): M2M string references retained verbatim (bare + qualified). patched=HOLDS | weak=HOLDS.
- probe_6 (Req 3.1/3.2/3.3): rebuild ProjectState from deconstructed FK+M2M forms with mixed-case app label; registry renders, get_models()==3, every lazy ref keeps app-label case. base would fail (dangling ref) | patched=HOLDS | weak=VIOLATED (FK app label lowercased to 'dj_reglogin.author').

Positive control (probe_1) FAILS at base and HOLDS patched => discriminating power confirmed (prepatch_reproduced=true).

Weak candidate ('lowercase_app_label', weak.diff): the naive fix that splits on '.' but lowercases BOTH segments (the lazy misreading of Req 1). Satisfies probes 3/4/5 but is REJECTED by probes 1, 2, and 6 — demonstrating the suite discriminates the wrong-app-label implementation the hidden test targets. No requirements-conforming alternative patch found that passes all probes.

Verdict: SOUND. >=5 probes all hold on patched, positive control discriminates base vs patched, and >=1 candidate patch is exercised and rejected.

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
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db.models import ForeignKey, CASCADE

# Req 1.1/1.2 (positive control): app-qualified FK string keeps app-label case,
# lowercases model-name segment.
f = ForeignKey('DJ_RegLogin.Category', on_delete=CASCADE)
name, path, args, kwargs = f.deconstruct()
to = kwargs['to']
print("deconstructed to =", repr(to))
expected = 'DJ_RegLogin.category'
if to != expected:
    print("FAIL: expected", repr(expected))
    raise SystemExit(1)
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes covering all three requirements, all HOLD on the gold-patched tree.

Probe->criterion->result (base | patched | weak-candidate):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): FK 'DJ_RegLogin.Category' deconstructs to 'DJ_RegLogin.category'. base=VIOLATED ('dj_reglogin.category') | patched=HOLDS | weak=VIOLATED.
- probe_2 (Req 1.4): deconstructed 'to' differs from fully-lowercased form and app label preserved. base=VIOLATED | patched=HOLDS | weak=VIOLATED.
- probe_3 (Req 2.1): bare string 'MyModel' -> 'mymodel'. patched=HOLDS | weak=HOLDS.
- probe_4 (Req 2.2/2.3): model class target -> label_lower ('auth.user'); on_delete kwarg preserved. patched=HOLDS | weak=HOLDS.
- probe_5 (Req 2.4): M2M string references retained verbatim (bare + qualified). patched=HOLDS | weak=HOLDS.
- probe_6 (Req 3.1/3.2/3.3): rebuild ProjectState from deconstructed FK+M2M forms with mixed-case app label; registry renders, get_models()==3, every lazy ref keeps app-label case. base would fail (dangling ref) | patched=HOLDS | weak=VIOLATED (FK app label lowercased to 'dj_reglogin.author').

Positive control (probe_1) FAILS at base and HOLDS patched => discriminating power confirmed (prepatch_reproduced=true).

Weak candidate ('lowercase_app_label', weak.diff): the naive fix that splits on '.' but lowercases BOTH segments (the lazy misreading of Req 1). Satisfies probes 3/4/5 but is REJECTED by probes 1, 2, and 6 — demonstrating the suite discriminates the wrong-app-label implementation the hidden test targets. No requirements-conforming alternative patch found that passes all probes.

Verdict: SOUND. >=5 probes all hold on patched, positive control discriminates base vs patched, and >=1 candidate patch is exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: in ForeignObject.deconstruct, when the string model ref contains '.', split into app_label/model_name and lowercase only model_name; else lowercase whole string. Requirements track this precisely. Req 1.1 uses split('.') semantics matching the code (single '.'). Req 2.3 (other kwargs unchanged) is trivially true — diff touches only the 'to' branch. Req 3 is the issue-level end-to-end consequence (project-state render / makemigrations no longer crashes with mixed-case app label), a faithful higher-level restatement not contradicted by code. Probes run in instance image: patched HOLDS exit=0, base confirms prior lowercasing behavior.

Counterexample / evidence:

```
No divergence found. Base tree: FK qualified -> 'dj_reglogin.category', M2M -> 'DJ_RegLogin.Category'. Patched tree: FK qualified -> 'DJ_RegLogin.category', M2M -> 'DJ_RegLogin.Category'. The only behavioral delta (FK app-label case preservation) is exactly what Req 1 mandates and Req 2.4 correctly asserts M2M is unchanged.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change (django/db/models/fields/related.py, deconstruct path, kwargs['to']) using public Django API names and translates the fix into behavioral requirements. No hidden-test artifacts leak: no test function name (test_reference_mixed_case_app_label), file path (tests/migrations/test_state.py), class (StateTests), or FAIL_TO_PASS id appears. The gold's invented locals (app_label, model_name) are not named; the doc uses generic 'app-label segment'/'model-name segment' prose. The FK+M2M+mixed-case-app-label scenario in Requirement 3 is already fully public in problem_statement (Content has ForeignKey(Category) + ManyToManyField(Site) under app 'DJ_RegLogin', with the ValueError about lazy reference to a lowercased app). Requirement 3.2's 'model count equals models added' is a behavioral outcome, not a quoted assertion or an enumerated parametrization list. M2M-verbatim clause reflects pre-existing behavior/scope, not the gold edit.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
