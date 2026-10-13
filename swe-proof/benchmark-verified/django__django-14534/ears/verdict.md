# P2 adversarial audit — django__django-14534

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
"""Positive control (Req 2.1): with a custom auto_id, a subwidget's
id_for_label SHALL reflect that auto_id-derived prefix + positional index,
matching the id the widget layer stored in the option attrs.
HOLDS on patched tree, must FAIL at base (base builds 'id_%s_%s')."""
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False)
django.setup()
from django import forms

class F(forms.Form):
    choices = forms.MultipleChoiceField(
        choices=[('a', 'A'), ('b', 'B')],
        widget=forms.CheckboxSelectMultiple,
    )

# Custom auto_id format string (non-default)
f = F(auto_id='custom_%s')
bf = f['choices']
subs = list(bf.subwidgets)
observed = [sw.id_for_label for sw in subs]
# The actual rendered id stored by the widget layer:
rendered = [sw.data['attrs'].get('id') for sw in subs]
print("id_for_label:", observed)
print("rendered id  :", rendered)
ok = observed == rendered
# with custom_%s prefix the ids must start with custom_choices
ok = ok and all(v and v.startswith('custom_choices') for v in observed)
print("match:", ok)
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.2: id_for_label returns exactly self.data['attrs']['id']
unchanged, for the default auto_id scheme too."""
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False)
django.setup()
from django import forms

class F(forms.Form):
    choices = forms.MultipleChoiceField(
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C')],
        widget=forms.CheckboxSelectMultiple,
    )

f = F()  # default auto_id 'id_%s'
bf = f['choices']
ok = True
for sw in bf.subwidgets:
    stored = sw.data['attrs'].get('id')
    got = sw.id_for_label
    print("stored:", stored, "id_for_label:", got)
    if got != stored:
        ok = False
print("all equal:", ok)
import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.3 / 3.4: when auto_id is disabled (no 'id' in attrs),
id_for_label SHALL return None (not a synthesized identifier), and the
option still renders and exposes choice_label."""
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False)
django.setup()
from django import forms

class F(forms.Form):
    choices = forms.MultipleChoiceField(
        choices=[('a', 'A'), ('b', 'B')],
        widget=forms.CheckboxSelectMultiple,
    )

f = F(auto_id=False)  # disables automatic id generation
bf = f['choices']
ok = True
for sw in bf.subwidgets:
    attrs = sw.data['attrs']
    got = sw.id_for_label
    print("attrs has id:", 'id' in attrs, "id_for_label:", repr(got),
          "choice_label:", repr(sw.choice_label))
    if got is not None:
        ok = False
    # option still renders and exposes label
    if not sw.choice_label:
        ok = False
    _ = str(sw)  # must not raise
print("all None + labels present:", ok)
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.4: the reported identifier is derived SOLELY from the attrs
mapping; name and index SHALL NOT influence the returned value. We mutate
name/index on the BoundWidget and confirm id_for_label is unchanged; and
mutate attrs['id'] and confirm it follows attrs."""
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False)
django.setup()
from django import forms

class F(forms.Form):
    choices = forms.MultipleChoiceField(
        choices=[('a', 'A'), ('b', 'B')],
        widget=forms.CheckboxSelectMultiple,
    )

f = F()
bf = f['choices']
sw = list(bf.subwidgets)[0]
base_val = sw.id_for_label
print("baseline id_for_label:", base_val)

# Corrupt name/index — must NOT change the result
sw.data['name'] = 'ZZZ'
sw.data['index'] = '999'
after_name = sw.id_for_label
print("after name/index mutation:", after_name)

# Change attrs['id'] — result MUST follow attrs
sw.data['attrs'] = dict(sw.data['attrs'])
sw.data['attrs']['id'] = 'SENTINEL_ID'
after_attr = sw.id_for_label
print("after attrs['id']=SENTINEL_ID:", after_attr)

ok = (after_name == base_val) and (after_attr == 'SENTINEL_ID')
print("solely-from-attrs:", ok)
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.2: successive subwidgets differ by the per-option index component,
matching ids on the input elements. And Req 2.3: values equal the id the
widget layer placed in attrs. Uses a custom auto_id."""
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False)
django.setup()
from django import forms

class F(forms.Form):
    choices = forms.MultipleChoiceField(
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C')],
        widget=forms.CheckboxSelectMultiple,
    )

f = F(auto_id='pfx_%s')
bf = f['choices']
subs = list(bf.subwidgets)
ids = [sw.id_for_label for sw in subs]
print("ids:", ids)
# distinct, ordered by index suffix _0 _1 _2
ok = len(set(ids)) == len(ids)
ok = ok and all(ids[i].endswith('_%d' % i) for i in range(len(ids)))
ok = ok and all(ids[i] == subs[i].data['attrs'].get('id') for i in range(len(ids)))
# common prefix reflects auto_id
ok = ok and all(v.startswith('pfx_choices') for v in ids)
print("index-differentiated & attr-matched:", ok)
import sys
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2/3.3 (subwidget count/order/label/markup unaffected) and
Req 3.5 (BoundField.id_for_label unchanged: honors explicit widget id else
auto id) — tested on a plain field where the field-level id is meaningful."""
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False)
django.setup()
from django import forms

class F(forms.Form):
    choices = forms.MultipleChoiceField(
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C')],
        widget=forms.CheckboxSelectMultiple,
    )

f = F()
bf = f['choices']
subs = list(bf.subwidgets)
ok = len(subs) == 3
print("count:", len(subs))
labels = [sw.choice_label for sw in subs]
print("labels:", labels)
ok = ok and labels == ['A', 'B', 'C']
for sw in subs:
    m = str(sw)
    if 'checkbox' not in m:
        ok = False

# Req 3.5: field-level id_for_label on a plain field
class G(forms.Form):
    name = forms.CharField()
    other = forms.CharField(widget=forms.TextInput(attrs={'id': 'EXP'}))

g = G()
auto = g['name'].id_for_label
exp = g['other'].id_for_label
print("field auto id:", auto, "field explicit id:", exp)
ok = ok and auto == 'id_name' and exp == 'EXP'
print("regression ok:", ok)
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 2.1): with a custom auto_id, a subwidget's
id_for_label SHALL reflect that auto_id-derived prefix + positional index,
matching the id the widget layer stored in the option attrs.
HOLDS on patched tree, must FAIL at base (base builds 'id_%s_%s')."""
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False)
django.setup()
from django import forms

class F(forms.Form):
    choices = forms.MultipleChoiceField(
        choices=[('a', 'A'), ('b', 'B')],
        widget=forms.CheckboxSelectMultiple,
    )

# Custom auto_id format string (non-default)
f = F(auto_id='custom_%s')
bf = f['choices']
subs = list(bf.subwidgets)
observed = [sw.id_for_label for sw in subs]
# The actual rendered id stored by the widget layer:
rendered = [sw.data['attrs'].get('id') for sw in subs]
print("id_for_label:", observed)
print("rendered id  :", rendered)
ok = observed == rendered
# with custom_%s prefix the ids must start with custom_choices
ok = ok and all(v and v.startswith('custom_choices') for v in observed)
print("match:", ok)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: BoundWidget.id_for_label should return self.data['attrs'].get('id') instead of the hard-coded 'id_%s_%s' % (name, index). Gold patch does exactly that.

Probes (all run in the official Docker image):
- probe_1 (Req 2.1, POSITIVE CONTROL): custom auto_id='custom_%s' -> id_for_label must equal the widget-layer-stored attrs['id'] (custom_choices_N). FAIL at base (base returns id_choices_N), HOLDS patched. Discriminates.
- probe_2 (Req 1.1/1.2): default auto_id -> id_for_label == attrs['id'] exactly, unchanged. HOLDS patched.
- probe_3 (Req 1.3/3.4): auto_id=False -> no 'id' in attrs -> id_for_label is None; option still renders and exposes choice_label. HOLDS patched.
- probe_4 (Req 1.4): mutating name/index does not change result; mutating attrs['id'] to SENTINEL_ID does. Confirms value derived solely from attrs. HOLDS patched.
- probe_5 (Req 2.2/2.3): custom auto_id='pfx_%s' -> three subwidget ids distinct, suffixed _0/_1/_2, all equal to attrs['id'], prefixed pfx_choices. HOLDS patched.
- probe_6 (Req 3.1/3.2/3.3/3.5): subwidget count/order/labels/markup unaffected; field-level BoundField.id_for_label still honors explicit widget id else auto id (id_name / EXP). HOLDS on BOTH base and patched (behavior genuinely unchanged, as required).

Candidate weak patch (weak.diff): returns 'id_%s_%s'%(name,index) but None when attrs has no id. This is the lazy fix a naive reading permits — it satisfies the None-when-no-id criterion. REJECTED by probe_1 (custom auto_id -> id_choices_N != custom_choices_N), probe_4 (follows name/index not attrs), probe_5 (ignores auto_id prefix). Suite discriminates the wrong implementation; passes probe_2/3/6 only. Confirms requirements are not too weak on the auto_id/attrs-derivation dimension.

All 6 probes hold on the patched tree; positive control fails at base and holds patched; >=1 candidate exercised and rejected. Verdict SOUND.

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
"""Positive control (Req 2.1): with a custom auto_id, a subwidget's
id_for_label SHALL reflect that auto_id-derived prefix + positional index,
matching the id the widget layer stored in the option attrs.
HOLDS on patched tree, must FAIL at base (base builds 'id_%s_%s')."""
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False)
django.setup()
from django import forms

class F(forms.Form):
    choices = forms.MultipleChoiceField(
        choices=[('a', 'A'), ('b', 'B')],
        widget=forms.CheckboxSelectMultiple,
    )

# Custom auto_id format string (non-default)
f = F(auto_id='custom_%s')
bf = f['choices']
subs = list(bf.subwidgets)
observed = [sw.id_for_label for sw in subs]
# The actual rendered id stored by the widget layer:
rendered = [sw.data['attrs'].get('id') for sw in subs]
print("id_for_label:", observed)
print("rendered id  :", rendered)
ok = observed == rendered
# with custom_%s prefix the ids must start with custom_choices
ok = ok and all(v and v.startswith('custom_choices') for v in observed)
print("match:", ok)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: BoundWidget.id_for_label should return self.data['attrs'].get('id') instead of the hard-coded 'id_%s_%s' % (name, index). Gold patch does exactly that.

Probes (all run in the official Docker image):
- probe_1 (Req 2.1, POSITIVE CONTROL): custom auto_id='custom_%s' -> id_for_label must equal the widget-layer-stored attrs['id'] (custom_choices_N). FAIL at base (base returns id_choices_N), HOLDS patched. Discriminates.
- probe_2 (Req 1.1/1.2): default auto_id -> id_for_label == attrs['id'] exactly, unchanged. HOLDS patched.
- probe_3 (Req 1.3/3.4): auto_id=False -> no 'id' in attrs -> id_for_label is None; option still renders and exposes choice_label. HOLDS patched.
- probe_4 (Req 1.4): mutating name/index does not change result; mutating attrs['id'] to SENTINEL_ID does. Confirms value derived solely from attrs. HOLDS patched.
- probe_5 (Req 2.2/2.3): custom auto_id='pfx_%s' -> three subwidget ids distinct, suffixed _0/_1/_2, all equal to attrs['id'], prefixed pfx_choices. HOLDS patched.
- probe_6 (Req 3.1/3.2/3.3/3.5): subwidget count/order/labels/markup unaffected; field-level BoundField.id_for_label still honors explicit widget id else auto id (id_name / EXP). HOLDS on BOTH base and patched (behavior genuinely unchanged, as required).

Candidate weak patch (weak.diff): returns 'id_%s_%s'%(name,index) but None when attrs has no id. This is the lazy fix a naive reading permits — it satisfies the None-when-no-id criterion. REJECTED by probe_1 (custom auto_id -> id_choices_N != custom_choices_N), probe_4 (follows name/index not attrs), probe_5 (ignores auto_id prefix). Suite discriminates the wrong implementation; passes probe_2/3/6 only. Confirms requirements are not too weak on the auto_id/attrs-derivation dimension.

All 6 probes hold on the patched tree; positive control fails at base and holds patched; >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a one-line change in django/forms/boundfield.py: BoundWidget.id_for_label now returns self.data['attrs'].get('id') instead of 'id_%s_%s' % (name, index). Req 1 correctly pins the changed observable behavior (attrs['id'] lookup, unchanged value, None fallback, no name/index influence). Req 2 correctly captures the motivating custom-auto_id case (verified: custom_%s propagates). Req 3 correctly scopes the regression surface and explicitly leaves the DISTINCT field-level BoundField.id_for_label unchanged — a good boundary distinction, not a mis-pin. No requirement mandates behavior the code lacks, forbids behavior it has, or pins a narrow slice. Boundary is the changed property itself.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes only behavior and localizes the change to modules/functions already named in the PUBLIC problem_statement (BoundWidget.id_for_label, BoundField.subwidgets, ChoiceWidget.create_option/options, self.data['attrs']['id'], the defective 'id_%s_%s'%(name,index) template, CheckboxSelectMultiple, custom auto_id, and the distinction from BoundField.id_for_label). No hidden-test content is transmitted: the test file path (tests/forms_tests/tests/test_forms.py), test names (test_boundfield_subwidget_id_for_label, test_iterable_boundfield_select), and the concrete parametrization (auto_id='prefix_%s' -> 'prefix_field_0'/'prefix_field_1', choices [('a','A'),('b','B')], auto_id=False -> None) never appear. Req 1 AC3 (return None when no 'id' present) reflects the gold's .get('id') semantics as a behavioral requirement, not a transcription of a test case, and does not enumerate the parametrized values. Req 2/3 translate test-checked behavior into generic behavioral requirements — the legitimate purpose of the spec — without mirroring the test's case list. No verbatim gold lines beyond what the problem_statement already quotes, no fix-invented identifiers leaked.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
