# P2 adversarial audit — django__django-12308

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
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.admin_utils.settings")
# Fallback minimal settings if that module doesn't exist
import django.conf as _c
if not _c.settings.configured:
    _c.settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_I18N=False)
django.setup()
from django.db import models
from django.contrib.admin.utils import display_for_field

# Req 1.1 / 1.2: dict rendered as valid JSON (double quotes), not python repr
out = display_for_field({'foo': 'bar'}, models.JSONField(), '-')
print("observed:", repr(out))
ok = out == '{"foo": "bar"}'
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django, django.conf as _c
if not _c.settings.configured:
    _c.settings.configure(DEBUG=True, USE_I18N=False, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.contrib.admin.utils import display_for_field
# Req 1.4: a plain string routed to JSON branch is JSON-encoded -> 'a' becomes '"a"'
out = display_for_field('a', models.JSONField(), '-')
print("observed:", repr(out))
ok = out == '"a"'
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django, django.conf as _c
if not _c.settings.configured:
    _c.settings.configure(DEBUG=True, USE_I18N=False, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.contrib.admin.utils import display_for_field
# Req 1.3: value that cannot serialize (tuple key) raises TypeError in get_prep_value
# -> fall back to display_for_value (python repr), NOT propagate error.
value = {('a', 'b'): 'c'}
out = display_for_field(value, models.JSONField(), '-')
print("observed:", repr(out))
# display_for_value of a dict -> str(dict)
ok = out == "{('a', 'b'): 'c'}"
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django, django.conf as _c
if not _c.settings.configured:
    _c.settings.configure(DEBUG=True, USE_I18N=False, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.contrib.admin.utils import display_for_field
# Req 2.1: None on a JSONField returns empty placeholder, NOT the JSON branch.
empty = '(empty)'
out = display_for_field(None, models.JSONField(), empty)
print("observed:", repr(out))
ok = out == empty
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django, django.conf as _c
if not _c.settings.configured:
    _c.settings.configure(DEBUG=True, USE_I18N=False, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.contrib.admin.utils import display_for_field
# Req 2.2: an empty (falsey) JSON value renders via the GENERIC value renderer,
# NOT the JSON prep routine. Empty string discriminates:
#   generic display_for_value('') -> ''
#   JSON get_prep_value('')       -> '""'
out = display_for_field('', models.JSONField(), '-')
print("observed:", repr(out))
ok = out == ''
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django, django.conf as _c
if not _c.settings.configured:
    _c.settings.configure(DEBUG=True, USE_I18N=False, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.contrib.admin.utils import display_for_field
# Req 2.3 / 2.5: existing branches unchanged (JSON branch does not intercept them).
checks = []
# Integer field with thousand separators (number formatting utilities)
out_int = display_for_field(12345, models.IntegerField(), '-')
checks.append(("int 12345", out_int, out_int in ('12,345', '12345')))
# Float
out_float = display_for_field(12345.6789, models.FloatField(), '-')
checks.append(("float", out_float, out_float in ('12345.6789', '12,345.6789')))
# BooleanField -> uses _boolean_icon (HTML img), not repr
out_bool = display_for_field(True, models.BooleanField(), '-')
checks.append(("bool", out_bool, 'img' in str(out_bool).lower() or 'icon' in str(out_bool).lower()))
# Choices field
f = models.CharField(choices=[('x', 'ex'), ('y', 'why')])
out_choice = display_for_field('x', f, '-')
checks.append(("choice", out_choice, out_choice == 'ex'))
ok = all(c[2] for c in checks)
for name, val, good in checks:
    print(name, "->", repr(val), "OK" if good else "BAD")
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import django, django.conf as _c
if not _c.settings.configured:
    _c.settings.configure(DEBUG=True, USE_I18N=False, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"])
django.setup()
from django.db import models
from django.contrib.admin.utils import label_for_field
# Req 3.1 / 3.2: label_for_field resolves a concrete JSONField's verbose name;
# with return_attr the resolved attr is None.
class M(models.Model):
    data = models.JSONField(verbose_name='my data blob')
    class Meta:
        app_label = 'admin_utils_probe'
label = label_for_field('data', M)
print("label:", repr(label))
lbl2, attr = label_for_field('data', M, return_attr=True)
print("return_attr:", repr(lbl2), repr(attr))
ok = (label == 'my data blob') and (attr is None)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.admin_utils.settings")
# Fallback minimal settings if that module doesn't exist
import django.conf as _c
if not _c.settings.configured:
    _c.settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_I18N=False)
django.setup()
from django.db import models
from django.contrib.admin.utils import display_for_field

# Req 1.1 / 1.2: dict rendered as valid JSON (double quotes), not python repr
out = display_for_field({'foo': 'bar'}, models.JSONField(), '-')
print("observed:", repr(out))
ok = out == '{"foo": "bar"}'
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12308: display_for_field must render read-only JSONField values via field.get_prep_value (valid JSON), with a TypeError fallback to display_for_value.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): {'foo':'bar'} -> '{"foo": "bar"}' (valid JSON, not python repr). PATCHED: holds ('{"foo": "bar"}'). BASE: FAILS ("{'foo': 'bar'}") => discriminates.
- probe_2 (Req 1.4): plain string 'a' -> '"a"' (JSON-encoded). PATCHED holds; BASE FAILS ('a'). Also a discriminating leg.
- probe_3 (Req 1.3): unserializable value {('a','b'):'c'} raises TypeError in get_prep_value -> must fall back to display_for_value giving "{('a', 'b'): 'c'}". PATCHED holds.
- probe_4 (Req 2.1): None on JSONField -> empty placeholder, not JSON branch. Holds.
- probe_5 (Req 2.2): empty string '' on JSONField -> generic renderer '' (NOT get_prep_value which would give '""'). Holds. Discriminates JSON-branch-intercepts-falsey.
- probe_6 (Req 2.3/2.5): int/float/bool/choices branches unchanged (12345, 12345.6789, boolean icon HTML, choice label 'ex'). Holds.
- probe_7 (Req 3.1/3.2): label_for_field resolves JSONField verbose_name 'my data blob'; return_attr -> None. Holds.

CANDIDATE PATCH (weak.diff): adds the JSONField branch but OMITS the try/except TypeError fallback (a partial/naive fix a weak reading permits). REJECTED by probe_3 — the tuple-key value raises TypeError('keys must be a string') and propagates, exactly the hidden-test's 'Invalid JSON' case ({('a','b'):'c'} -> "{('a', 'b'): 'c'}"). probe_1/2/4/5/6/7 still pass under it, so probe_3 is the discriminating obligation. This demonstrates the suite rejects wrong implementations.

All 7 probes hold on patched; positive control (probe_1) fails at base (prepatch_reproduced=true); >=1 candidate exercised and rejected. Verdict SOUND.

Note on G-PANEL-2 (recorded fail in meta.json): Req 1.4 prose says the string is 'returned' as its JSON encoding ('a' -> '"a"'), which the gold behavior does produce. The panel's 'pass-through of already-serialized JSON' objection concerns a differently-worded reading; the encoded criterion (probe_2) is faithful to gold and discriminates base. That is a faithfulness (G-PANEL-2) concern, not a spec-too-weak / spec-too-strong (G-EQ) defect.

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
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.admin_utils.settings")
# Fallback minimal settings if that module doesn't exist
import django.conf as _c
if not _c.settings.configured:
    _c.settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_I18N=False)
django.setup()
from django.db import models
from django.contrib.admin.utils import display_for_field

# Req 1.1 / 1.2: dict rendered as valid JSON (double quotes), not python repr
out = display_for_field({'foo': 'bar'}, models.JSONField(), '-')
print("observed:", repr(out))
ok = out == '{"foo": "bar"}'
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12308: display_for_field must render read-only JSONField values via field.get_prep_value (valid JSON), with a TypeError fallback to display_for_value.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): {'foo':'bar'} -> '{"foo": "bar"}' (valid JSON, not python repr). PATCHED: holds ('{"foo": "bar"}'). BASE: FAILS ("{'foo': 'bar'}") => discriminates.
- probe_2 (Req 1.4): plain string 'a' -> '"a"' (JSON-encoded). PATCHED holds; BASE FAILS ('a'). Also a discriminating leg.
- probe_3 (Req 1.3): unserializable value {('a','b'):'c'} raises TypeError in get_prep_value -> must fall back to display_for_value giving "{('a', 'b'): 'c'}". PATCHED holds.
- probe_4 (Req 2.1): None on JSONField -> empty placeholder, not JSON branch. Holds.
- probe_5 (Req 2.2): empty string '' on JSONField -> generic renderer '' (NOT get_prep_value which would give '""'). Holds. Discriminates JSON-branch-intercepts-falsey.
- probe_6 (Req 2.3/2.5): int/float/bool/choices branches unchanged (12345, 12345.6789, boolean icon HTML, choice label 'ex'). Holds.
- probe_7 (Req 3.1/3.2): label_for_field resolves JSONField verbose_name 'my data blob'; return_attr -> None. Holds.

CANDIDATE PATCH (weak.diff): adds the JSONField branch but OMITS the try/except TypeError fallback (a partial/naive fix a weak reading permits). REJECTED by probe_3 — the tuple-key value raises TypeError('keys must be a string') and propagates, exactly the hidden-test's 'Invalid JSON' case ({('a','b'):'c'} -> "{('a', 'b'): 'c'}"). probe_1/2/4/5/6/7 still pass under it, so probe_3 is the discriminating obligation. This demonstrates the suite rejects wrong implementations.

All 7 probes hold on patched; positive control (probe_1) fails at base (prepatch_reproduced=true); >=1 candidate exercised and rejected. Verdict SOUND.

Note on G-PANEL-2 (recorded fail in meta.json): Req 1.4 prose says the string is 'returned' as its JSON encoding ('a' -> '"a"'), which the gold behavior does produce. The panel's 'pass-through of already-serialized JSON' objection concerns a differently-worded reading; the encoded criterion (probe_2) is faithful to gold and discriminates base. That is a faithfulness (G-PANEL-2) concern, not a spec-too-weak / spec-too-strong (G-EQ) defect.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds `elif isinstance(field, models.JSONField) and value: try: return field.get_prep_value(value) except TypeError: return display_for_value(...)` to display_for_field, positioned after choices/boolean/date/decimal/file branches and before else. Requirements 1.1-1.4 and 2.1-2.5 map exactly onto this branch and its guard; the modeled boundary is the added JSONField branch (the changed observable behavior), not a narrower slice. Req 3 (label_for_field preservation) is honored since the patch does not touch label_for_field. FAIL_TO_PASS includes test_label_for_field but that is a test-registration artifact (a JSONField added to a test model); no label behavior changed, consistent with Req3's 'unchanged' framing. No over-mandate, no forbidding of present behavior, no invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements paraphrase, not leak. The {"foo":"bar"}/{'foo':'bar'} example (Req1.2) and the get_prep_value/InvalidJSONInput-TypeError approach are all disclosed by the PUBLIC problem_statement. The gold identifier get_prep_value is paraphrased as 'value-preparation routine'; display_for_value is a pre-existing public function (legitimate localization). No test names/paths/ids, no quoted test or gold code appear. The doc does NOT mirror the test parametrization: the hidden test's list case ['a','b'] is never mentioned, and the empty-value enumeration in Req2.2 is behavioral and untested. The string->"a" illustration (Req1.4) is the closest to a test case but describes a genuine property of the encoder routine rather than transmitting the parametrized case. All content is either public or a behavioral translation.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
