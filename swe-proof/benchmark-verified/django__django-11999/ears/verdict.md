# P2 adversarial audit — django__django-11999

**Backend:** `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
# Positive control / Req1.2 & Req1.3: a user-declared get_<field>_display
# must WIN over the auto-generated accessor and return the fixed value.
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                   DATABASES={})
django.setup()
from django.db import models

class FooBar(models.Model):
    foo_bar = models.CharField(max_length=10, choices=[('1','one'),('2','two')])
    class Meta:
        app_label = 'p1'
    def get_foo_bar_display(self):
        return "something"

obj = FooBar(foo_bar='1')
val = obj.get_foo_bar_display()
print("get_foo_bar_display() returned:", repr(val))
# Must be the user's fixed value, NOT the choices label 'one'.
assert val == "something", f"expected user value 'something', got {val!r}"
print("OK: user-declared accessor wins")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req2.2: auto-generated accessor returns the human label when value is a choice.
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                   DATABASES={})
django.setup()
from django.db import models

class M2(models.Model):
    f = models.CharField(max_length=10, choices=[('1','one'),('2','two')])
    class Meta:
        app_label = 'p2'

obj = M2(f='1')
val = obj.get_f_display()
print("get_f_display('1') =", repr(val))
assert val == "one", f"expected 'one', got {val!r}"
print("OK: label returned for known choice")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2.3: auto-generated accessor returns raw value unchanged for a value not
# among the choices.
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                   DATABASES={})
django.setup()
from django.db import models

class M3(models.Model):
    f = models.CharField(max_length=10, choices=[('1','one'),('2','two')])
    class Meta:
        app_label = 'p3'

obj = M3(f='9')
val = obj.get_f_display()
print("get_f_display('9') =", repr(val))
assert val == '9', f"expected raw '9', got {val!r}"
print("OK: raw value returned for unknown choice")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2.4: accessor installed for EVERY choices-field, incl. multiple on one
# model; non-overridden ones auto-generate. Also Req1.1: overridden one is kept.
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                   DATABASES={})
django.setup()
from django.db import models

class M4(models.Model):
    a = models.CharField(max_length=10, choices=[('1','A-one')])
    b = models.CharField(max_length=10, choices=[('2','B-two')])
    class Meta:
        app_label = 'p4'
    def get_b_display(self):
        return "custom-b"

obj = M4(a='1', b='2')
va = obj.get_a_display()
vb = obj.get_b_display()
print("a (auto) =", repr(va), "; b (overridden) =", repr(vb))
assert va == "A-one", f"expected auto label 'A-one', got {va!r}"
assert vb == "custom-b", f"expected user 'custom-b', got {vb!r}"
print("OK: multiple fields; auto for a, override kept for b")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3.1: a field WITHOUT choices must NOT get a get_<field>_display accessor.
# Req3.2: value descriptor still works regardless.
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                   DATABASES={})
django.setup()
from django.db import models

class M5(models.Model):
    plain = models.CharField(max_length=10)  # no choices
    class Meta:
        app_label = 'p5'

has_acc = hasattr(M5, 'get_plain_display')
print("hasattr get_plain_display:", has_acc)
assert not has_acc, "no-choices field must NOT get a display accessor"

obj = M5(plain='hi')
print("descriptor value:", repr(obj.plain))
assert obj.plain == 'hi', "value descriptor broken"
print("OK: no accessor for choiceless field; descriptor intact")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control / Req1.2 & Req1.3: a user-declared get_<field>_display
# must WIN over the auto-generated accessor and return the fixed value.
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                   DATABASES={})
django.setup()
from django.db import models

class FooBar(models.Model):
    foo_bar = models.CharField(max_length=10, choices=[('1','one'),('2','two')])
    class Meta:
        app_label = 'p1'
    def get_foo_bar_display(self):
        return "something"

obj = FooBar(foo_bar='1')
val = obj.get_foo_bar_display()
print("get_foo_bar_display() returned:", repr(val))
# Must be the user's fixed value, NOT the choices label 'one'.
assert val == "something", f"expected user value 'something', got {val!r}"
print("OK: user-declared accessor wins")
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes covering all three requirements. probe_1 (Req1.2/1.3, positive control): user-declared get_foo_bar_display returns fixed 'something' not choices label — HOLDS patched, VIOLATED at base (discriminates). probe_2 (Req2.2): auto accessor returns label 'one' for known choice — HOLDS. probe_3 (Req2.3): auto accessor returns raw '9' for unknown value — HOLDS. probe_4 (Req2.4+1.1): two choices-fields, auto for a + override kept for b — HOLDS patched, VIOLATED at base. probe_5 (Req3.1/3.2): choiceless field gets NO get_plain_display accessor, descriptor intact — HOLDS. Candidate 'weak_noop' is the naive fix that reformats the setattr but drops the hasattr guard (unconditional overwrite = the regression). Suite REJECTS it: probe_1 and probe_4 VIOLATED under it, probe_2 still holds. Suite discriminates wrong implementations; no too-weak or violation finding. All required runs completed.

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
# Positive control / Req1.2 & Req1.3: a user-declared get_<field>_display
# must WIN over the auto-generated accessor and return the fixed value.
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
                   DATABASES={})
django.setup()
from django.db import models

class FooBar(models.Model):
    foo_bar = models.CharField(max_length=10, choices=[('1','one'),('2','two')])
    class Meta:
        app_label = 'p1'
    def get_foo_bar_display(self):
        return "something"

obj = FooBar(foo_bar='1')
val = obj.get_foo_bar_display()
print("get_foo_bar_display() returned:", repr(val))
# Must be the user's fixed value, NOT the choices label 'one'.
assert val == "something", f"expected user value 'something', got {val!r}"
print("OK: user-declared accessor wins")
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes covering all three requirements. probe_1 (Req1.2/1.3, positive control): user-declared get_foo_bar_display returns fixed 'something' not choices label — HOLDS patched, VIOLATED at base (discriminates). probe_2 (Req2.2): auto accessor returns label 'one' for known choice — HOLDS. probe_3 (Req2.3): auto accessor returns raw '9' for unknown value — HOLDS. probe_4 (Req2.4+1.1): two choices-fields, auto for a + override kept for b — HOLDS patched, VIOLATED at base. probe_5 (Req3.1/3.2): choiceless field gets NO get_plain_display accessor, descriptor intact — HOLDS. Candidate 'weak_noop' is the naive fix that reformats the setattr but drops the hasattr guard (unconditional overwrite = the regression). Suite REJECTS it: probe_1 and probe_4 VIOLATED under it, probe_2 still holds. Suite discriminates wrong implementations; no too-weak or violation finding. All required runs completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe (probe.py): patched exit=0 (OK); base exit=1 failing at Req1 assertion `f.get_foo_bar_display()=='something'` -> got 'foo'. Verified: (a) user override returns 'something'; (b) auto-accessor returns label 'foo' for value in choices and raw value 9 for value not in choices; (c) plain field without choices has no get_plain_display. Modeling boundary matches the changed behavior, not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior, not the hidden test. Localizing identifiers (Field.contribute_to_class, django/db/models/fields/`__init__`.py, Model.`_get_FIELD_display` in base.py, partialmethod, flatchoices, the `self.choices is not None` guard) are legitimate change-localization; all are public Django API or appear in the public problem_statement (which already contains the full FooBar/choices=[(1,'foo'),(2,'bar')]/'something' example). The core requirement — install the auto-generated accessor only when the class does not already provide the attribute — is a behavioral translation of the gold hasattr-guard edit, which is exactly the intended purpose, not a leak. No test file path (tests/model_fields/tests.py), no test/class names (test_overriding_FIELD_display, GetFieldDisplayTests), no parametrization ids, no quoted test/gold code, and no fix-invented identifiers appear. Req 1.3 ('fixed value unrelated to choices labels') paraphrases behavior already shown in the public example rather than reproducing test-shaped enumerations. The literal test value 'something' and IntegerField specifics are NOT reproduced.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
