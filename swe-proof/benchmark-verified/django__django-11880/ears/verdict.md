# P2 adversarial audit — django__django-11880

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
"""Positive control / Req1-crit1: deepcopy gives a DISTINCT error_messages dict object."""
import copy
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django import forms

f = forms.CharField()
g = copy.deepcopy(f)
same = g.error_messages is f.error_messages
print("f.error_messages id:", id(f.error_messages))
print("g.error_messages id:", id(g.error_messages))
print("same object:", same)
# criterion holds iff they are DIFFERENT objects
raise SystemExit(1 if same else 0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1-crit2: copy's error_messages has same keys/values as original, incl. overrides."""
import copy
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django import forms

f = forms.CharField(error_messages={'required': 'CUSTOM REQ', 'invalid': 'CUSTOM INV'})
g = copy.deepcopy(f)
print("orig:", dict(f.error_messages))
print("copy:", dict(g.error_messages))
ok = dict(f.error_messages) == dict(g.error_messages) and g.error_messages.get('required') == 'CUSTOM REQ'
# also a subclass with its own default_error_messages
h = forms.EmailField()
h2 = copy.deepcopy(h)
print("email orig:", dict(h.error_messages))
print("email copy:", dict(h2.error_messages))
# copy must reproduce whatever keys/values the original had (subclass defaults included)
ok = ok and dict(h.error_messages) == dict(h2.error_messages) and len(h2.error_messages) >= 1
print("ok:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1-crit3: mutating one copy's error_messages does NOT affect original or other copies."""
import copy
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django import forms

f = forms.CharField()
a = copy.deepcopy(f)
b = copy.deepcopy(f)
a.error_messages['required'] = 'MUTATED'
a.error_messages['newkey'] = 'X'
print("orig required:", f.error_messages.get('required'))
print("b required:", b.error_messages.get('required'))
print("orig has newkey:", 'newkey' in f.error_messages)
print("b has newkey:", 'newkey' in b.error_messages)
ok = (f.error_messages.get('required') != 'MUTATED'
      and b.error_messages.get('required') != 'MUTATED'
      and 'newkey' not in f.error_messages
      and 'newkey' not in b.error_messages)
print("ok:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req1-crit4 + Req2-crit1/2/3: preserved type, independent widget & validators, equal attrs."""
import copy
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django import forms
from django.core.validators import MaxLengthValidator

class MyField(forms.CharField):
    pass

f = MyField(required=False, label='L', initial='I', help_text='H', disabled=True, label_suffix=':')
g = copy.deepcopy(f)

type_ok = type(g) is MyField
widget_ok = g.widget is not f.widget
validators_ok = (g.validators is not f.validators) and (list(g.validators) == list(f.validators))
attrs_ok = (g.required == f.required and g.label == f.label and g.initial == f.initial
            and g.help_text == f.help_text and g.disabled == f.disabled
            and g.label_suffix == f.label_suffix)

# mutating widget/validators independence
g.validators.append(MaxLengthValidator(5))
indep = len(f.validators) != len(g.validators)

print("type_ok:", type_ok, "widget_ok:", widget_ok, "validators_ok:", validators_ok,
      "attrs_ok:", attrs_ok, "indep_validators:", indep)
ok = type_ok and widget_ok and validators_ok and attrs_ok and indep
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2-crit4: fresh field per form instance (independent error_messages across instances)."""
import copy
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django import forms

class MyForm(forms.Form):
    name = forms.CharField()

a = MyForm()
b = MyForm()
fa = a.fields['name']
fb = b.fields['name']
print("distinct field objs:", fa is not fb)
print("distinct error_messages:", fa.error_messages is not fb.error_messages)
fa.error_messages['required'] = 'CHANGED'
print("b unaffected:", fb.error_messages.get('required') != 'CHANGED')
ok = (fa is not fb) and (fa.error_messages is not fb.error_messages) and (fb.error_messages.get('required') != 'CHANGED')
print("ok:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2-crit5: multi-value field sub-fields duplicated independently (incl. error_messages)."""
import copy
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django import forms

f = forms.SplitDateTimeField()
g = copy.deepcopy(f)
print("field distinct:", g is not f)
print("fields list distinct:", g.fields is not f.fields)
sub_distinct = all(g.fields[i] is not f.fields[i] for i in range(len(f.fields)))
print("subfields distinct:", sub_distinct)
# each subfield owns its own error_messages
em_distinct = all(g.fields[i].error_messages is not f.fields[i].error_messages
                  for i in range(len(f.fields)))
print("subfield error_messages distinct:", em_distinct)
# mutation isolation
g.fields[0].error_messages['required'] = 'ZZZ'
iso = f.fields[0].error_messages.get('required') != 'ZZZ'
print("mutation isolated:", iso)
ok = (g is not f) and (g.fields is not f.fields) and sub_distinct and em_distinct and iso
print("ok:", ok)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1-crit1: deepcopy gives a DISTINCT error_messages dict object."""
import copy
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django import forms

f = forms.CharField()
g = copy.deepcopy(f)
same = g.error_messages is f.error_messages
print("f.error_messages id:", id(f.error_messages))
print("g.error_messages id:", id(g.error_messages))
print("same object:", same)
# criterion holds iff they are DIFFERENT objects
raise SystemExit(1 if same else 0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements mandate: Field.__deepcopy__ must give the copy its OWN error_messages dict (Req1-c1) with the SAME keys/values incl. overrides (Req1-c2), mutation-isolated from original/other copies (Req1-c3), same exact class (Req1-c4); and preserve prior guarantees: independent widget (Req2-c1), new validators list w/ same contents (Req2-c2), equal scalar attrs (Req2-c3), fresh field per form instance (Req2-c4), independent sub-field deepcopy for multi-value fields (Req2-c5). Gold patch adds `result.error_messages = self.error_messages.copy()`.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1-c1, POSITIVE CONTROL): copy.error_messages is a distinct object. HOLDS patched, FAILS at base (base shares the same dict) => discriminates.
- probe_2 (Req1-c2): copy reproduces same keys/values incl. constructor override and subclass defaults. HOLDS patched.
- probe_3 (Req1-c3): mutating one copy's error_messages leaves original + sibling copy unchanged. HOLDS patched; FAILS at base (confirms the real bug).
- probe_4 (Req1-c4 + Req2-c1/c2/c3): exact subclass type, independent widget, new-but-equal validators list w/ mutation isolation, equal scalar attrs. HOLDS patched.
- probe_5 (Req2-c4): two form instances have distinct field objects + distinct error_messages; mutating one instance's field does not leak. HOLDS patched.
- probe_6 (Req2-c5): SplitDateTimeField sub-fields each independently deep-copied incl. own error_messages, mutation-isolated. HOLDS patched.

Candidate wrong patches (>=1 rejected required, none survive):
- weak_noop (`result.error_messages = self.error_messages`, still shared): REJECTED by probes 1,3,5,6.
- weak_emptydict (`result.error_messages = {}`, independent object but empty): REJECTED by probe_2 (violates same-contents Req1-c2).
No requirements-conforming alternative found that would leave hidden tests unresolved; the suite catches both the naive share and the empty-dict fixes. Note probe_2 initially had a bug asserting 'invalid' in EmailField defaults (this Django version's EmailField default_error_messages omits it); corrected to assert dict-equality only. Ran with conda env python (bare `python` absent).

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
"""Positive control / Req1-crit1: deepcopy gives a DISTINCT error_messages dict object."""
import copy
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False)
    django.setup()
from django import forms

f = forms.CharField()
g = copy.deepcopy(f)
same = g.error_messages is f.error_messages
print("f.error_messages id:", id(f.error_messages))
print("g.error_messages id:", id(g.error_messages))
print("same object:", same)
# criterion holds iff they are DIFFERENT objects
raise SystemExit(1 if same else 0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements mandate: Field.__deepcopy__ must give the copy its OWN error_messages dict (Req1-c1) with the SAME keys/values incl. overrides (Req1-c2), mutation-isolated from original/other copies (Req1-c3), same exact class (Req1-c4); and preserve prior guarantees: independent widget (Req2-c1), new validators list w/ same contents (Req2-c2), equal scalar attrs (Req2-c3), fresh field per form instance (Req2-c4), independent sub-field deepcopy for multi-value fields (Req2-c5). Gold patch adds `result.error_messages = self.error_messages.copy()`.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1-c1, POSITIVE CONTROL): copy.error_messages is a distinct object. HOLDS patched, FAILS at base (base shares the same dict) => discriminates.
- probe_2 (Req1-c2): copy reproduces same keys/values incl. constructor override and subclass defaults. HOLDS patched.
- probe_3 (Req1-c3): mutating one copy's error_messages leaves original + sibling copy unchanged. HOLDS patched; FAILS at base (confirms the real bug).
- probe_4 (Req1-c4 + Req2-c1/c2/c3): exact subclass type, independent widget, new-but-equal validators list w/ mutation isolation, equal scalar attrs. HOLDS patched.
- probe_5 (Req2-c4): two form instances have distinct field objects + distinct error_messages; mutating one instance's field does not leak. HOLDS patched.
- probe_6 (Req2-c5): SplitDateTimeField sub-fields each independently deep-copied incl. own error_messages, mutation-isolated. HOLDS patched.

Candidate wrong patches (>=1 rejected required, none survive):
- weak_noop (`result.error_messages = self.error_messages`, still shared): REJECTED by probes 1,3,5,6.
- weak_emptydict (`result.error_messages = {}`, independent object but empty): REJECTED by probe_2 (violates same-contents Req1-c2).
No requirements-conforming alternative found that would leave hidden tests unresolved; the suite catches both the naive share and the empty-dict fixes. Note probe_2 initially had a bug asserting 'invalid' in EmailField defaults (this Django version's EmailField default_error_messages omits it); corrected to assert dict-equality only. Ran with conda env python (bare `python` absent).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe: gold-patched HOLDS (exit 0), base VIOLATED at Req1.1. Boundary is correct — error_messages independence is the changed behavior; preservation clauses correctly framed as 'continue/keep intact'.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md restates the public problem_statement (Field.__deepcopy__ shallow-copies and shares the error_messages dict) and derives behavioral requirements from it. All named identifiers are public Django API (__deepcopy__, error_messages, validators, widget, MultiValueField) or appear in the problem_statement; none are fix-invented (the gold's sole new token is the stdlib `.copy()`). Req 1.2's mention of 'error_messages constructor argument or by a subclass' and Req 1.4's same-class-preservation echo what the hidden test (CustomCharField subclass overriding error_messages, assertIsInstance + assertIsNot) verifies, but these are legitimate behavioral translations of generic deepcopy/override semantics, not quoted test code, test names ('test_field_deep_copy_error_messages'), paths, or the specific literal 'Form custom error message.'. Req 2.5 (multi-value subfield deep copy) corresponds to a PASS_TO_PASS regression test but describes documented behavior, not a leaked case enumeration. No reconstruction of the hidden tests beyond describing behavior.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
