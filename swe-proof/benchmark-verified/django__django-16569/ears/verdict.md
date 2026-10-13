# P2 adversarial audit — django__django-16569

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
"""Positive control: Req1.2 — can_delete=True, can_delete_extra=False, empty_form
accessible without TypeError, and empty_form has NO deletion field (Req2.7).
HOLDS on patched, FAILS at base (raises TypeError)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=True)
django.setup()
from django import forms
from django.forms.formsets import formset_factory, DELETION_FIELD_NAME


class F(forms.Form):
    name = forms.CharField(required=False)


FS = formset_factory(F, can_delete=True, can_delete_extra=False)
fs = FS()
try:
    ef = fs.empty_form
except Exception as e:
    print("empty_form raised:", type(e).__name__, e)
    raise SystemExit(1)

has_del = DELETION_FIELD_NAME in ef.fields
print("empty_form accessed OK; deletion field present:", has_del)
# empty_form is positionless -> must NOT have deletion field
raise SystemExit(0 if not has_del else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1/1.3: add_fields(form, None) completes without exception for EVERY
combination of can_delete/can_delete_extra."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=True)
django.setup()
from django import forms
from django.forms.formsets import formset_factory


class F(forms.Form):
    name = forms.CharField(required=False)


ok = True
for cd in (True, False):
    for cde in (True, False):
        FS = formset_factory(F, can_delete=cd, can_delete_extra=cde)
        fs = FS()
        form = F()
        try:
            fs.add_fields(form, None)
            print(f"can_delete={cd} can_delete_extra={cde}: OK")
        except Exception as e:
            print(f"can_delete={cd} can_delete_extra={cde}: RAISED {type(e).__name__}: {e}")
            ok = False
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.3: can_delete=True, can_delete_extra=True, index=None -> deletion field
STILL attached (regardless of index). Also Req2.1 biconditional 'extra' arm."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=True)
django.setup()
from django import forms
from django.forms.formsets import formset_factory, DELETION_FIELD_NAME


class F(forms.Form):
    name = forms.CharField(required=False)


FS = formset_factory(F, can_delete=True, can_delete_extra=True)
fs = FS()
form = F()
fs.add_fields(form, None)
has_del = DELETION_FIELD_NAME in form.fields
print("can_delete_extra=True, index=None -> deletion field present:", has_del)
raise SystemExit(0 if has_del else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.4/2.5/2.6: can_delete=True, can_delete_extra=False. Positioned forms:
index < initial_form_count -> deletion field; index >= -> no field; index=None -> no field."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=True)
django.setup()
from django import forms
from django.forms.formsets import formset_factory, DELETION_FIELD_NAME


class F(forms.Form):
    name = forms.CharField(required=False)


# 2 initial forms => initial_form_count = 2
FS = formset_factory(F, can_delete=True, can_delete_extra=False, extra=1)
fs = FS(initial=[{"name": "a"}, {"name": "b"}])
ifc = fs.initial_form_count()
print("initial_form_count =", ifc)
assert ifc == 2, ifc

ok = True
# index 0,1 -> below ifc -> should have deletion
for idx in (0, 1):
    form = F()
    fs.add_fields(form, idx)
    present = DELETION_FIELD_NAME in form.fields
    print(f"index={idx} (<{ifc}) deletion present:", present)
    ok = ok and present
# index 2 -> >= ifc -> no deletion (extra form)
form = F()
fs.add_fields(form, 2)
present = DELETION_FIELD_NAME in form.fields
print(f"index=2 (>= {ifc}) deletion present:", present)
ok = ok and (not present)
# index None -> no deletion
form = F()
fs.add_fields(form, None)
present = DELETION_FIELD_NAME in form.fields
print("index=None deletion present:", present)
ok = ok and (not present)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2.2: can_delete=False -> NEVER attach deletion field, regardless of
can_delete_extra/index. Req3.1: ordering field behavior preserved."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=True)
django.setup()
from django import forms
from django.forms.formsets import (
    formset_factory, DELETION_FIELD_NAME, ORDERING_FIELD_NAME,
)


class F(forms.Form):
    name = forms.CharField(required=False)


ok = True
# can_delete=False: no deletion field ever
for cde in (True, False):
    for idx in (None, 0, 5):
        FS = formset_factory(F, can_delete=False, can_delete_extra=cde)
        fs = FS()
        form = F()
        fs.add_fields(form, idx)
        if DELETION_FIELD_NAME in form.fields:
            print(f"BAD: deletion attached with can_delete=False cde={cde} idx={idx}")
            ok = False
print("can_delete=False never attaches deletion:", ok)

# Ordering: can_order=True. initial positioned form gets 1-based initial value;
# positionless form gets ordering field with no initial value.
FS = formset_factory(F, can_order=True, extra=1)
fs = FS(initial=[{"name": "a"}, {"name": "b"}])
# positioned initial form index 0 -> initial = 1
form = F()
fs.add_fields(form, 0)
of = form.fields.get(ORDERING_FIELD_NAME)
print("index=0 ordering initial:", getattr(of, "initial", "MISSING"))
ok = ok and of is not None and of.initial == 1
# positionless -> ordering field present, no initial
form = F()
fs.add_fields(form, None)
of = form.fields.get(ORDERING_FIELD_NAME)
print("index=None ordering initial:", getattr(of, "initial", "MISSING"))
ok = ok and of is not None and not of.initial
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1.2 — can_delete=True, can_delete_extra=False, empty_form
accessible without TypeError, and empty_form has NO deletion field (Req2.7).
HOLDS on patched, FAILS at base (raises TypeError)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=True)
django.setup()
from django import forms
from django.forms.formsets import formset_factory, DELETION_FIELD_NAME


class F(forms.Form):
    name = forms.CharField(required=False)


FS = formset_factory(F, can_delete=True, can_delete_extra=False)
fs = FS()
try:
    ef = fs.empty_form
except Exception as e:
    print("empty_form raised:", type(e).__name__, e)
    raise SystemExit(1)

has_del = DELETION_FIELD_NAME in ef.fields
print("empty_form accessed OK; deletion field present:", has_del)
# empty_form is positionless -> must NOT have deletion field
raise SystemExit(0 if not has_del else 1)
```

Prepatch bug re-encoded as an attack: `True`.

All 5 probes HOLD on gold-patched tree. Positive control probe_1 (Req1.2/Req2.7: empty_form accessible AND empty_form must lack the deletion field for can_delete=True/can_delete_extra=False) FAILS at base with TypeError '<' not supported between NoneType and int — discriminating power confirmed. probe_2 also reproduces the base crash (Req1.1/1.3). Probe coverage: p1=Req1.2+2.7 (empty_form no delete field); p2=Req1.1/1.3 (add_fields(None) total over all can_delete/can_delete_extra combos); p3=Req2.3 (can_delete_extra=True,index=None still attaches); p4=Req2.4/2.5/2.6 (index<ifc attach, index>=ifc no, None no); p5=Req2.2 (can_delete=False never attaches) + Req3.1 (ordering: index0 initial=1, None no initial). Wrong-fix candidate weak.diff coerces the crash away with 'index is None or index < initial_form_count', which wrongly attaches the deletion field to positionless/empty_form. It is REJECTED by probe_1 (empty_form gains delete field) and probe_4 (index=None gains delete field), while passing probes 2/3/5 — demonstrating the suite discriminates a plausible naive fix on Req2.4/2.7. No requirements-conforming weak fix found.

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
"""Positive control: Req1.2 — can_delete=True, can_delete_extra=False, empty_form
accessible without TypeError, and empty_form has NO deletion field (Req2.7).
HOLDS on patched, FAILS at base (raises TypeError)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_TZ=True)
django.setup()
from django import forms
from django.forms.formsets import formset_factory, DELETION_FIELD_NAME


class F(forms.Form):
    name = forms.CharField(required=False)


FS = formset_factory(F, can_delete=True, can_delete_extra=False)
fs = FS()
try:
    ef = fs.empty_form
except Exception as e:
    print("empty_form raised:", type(e).__name__, e)
    raise SystemExit(1)

has_del = DELETION_FIELD_NAME in ef.fields
print("empty_form accessed OK; deletion field present:", has_del)
# empty_form is positionless -> must NOT have deletion field
raise SystemExit(0 if not has_del else 1)
```

Prepatch bug re-encoded as an attack: `True`.

All 5 probes HOLD on gold-patched tree. Positive control probe_1 (Req1.2/Req2.7: empty_form accessible AND empty_form must lack the deletion field for can_delete=True/can_delete_extra=False) FAILS at base with TypeError '<' not supported between NoneType and int — discriminating power confirmed. probe_2 also reproduces the base crash (Req1.1/1.3). Probe coverage: p1=Req1.2+2.7 (empty_form no delete field); p2=Req1.1/1.3 (add_fields(None) total over all can_delete/can_delete_extra combos); p3=Req2.3 (can_delete_extra=True,index=None still attaches); p4=Req2.4/2.5/2.6 (index<ifc attach, index>=ifc no, None no); p5=Req2.2 (can_delete=False never attaches) + Req3.1 (ordering: index0 initial=1, None no initial). Wrong-fix candidate weak.diff coerces the crash away with 'index is None or index < initial_form_count', which wrongly attaches the deletion field to positionless/empty_form. It is REJECTED by probe_1 (empty_form gains delete field) and probe_4 (index=None gains delete field), while passing probes 2/3/5 — demonstrating the suite discriminates a plausible naive fix on Req2.4/2.7. No requirements-conforming weak fix found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes exactly one condition: `index < initial_form_count` -> `index is not None and index < initial_form_count`. The requirements pin the full changed observable behavior (deletion-field decision biconditional across all can_delete/can_delete_extra/index combinations, plus preservation of ordering behavior), not a narrow slice. Boundary is correct: modeled the whole add_fields deletion decision including the positionless (index=None) case that the fix targets. Probe: probe.py — patched exit 0, base exit 1 (TypeError NoneType < int).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement is exceptionally complete: it names the affected attributes (can_delete, can_delete_extra, index, empty_form), the exact crash (TypeError: '<' not supported between NoneType and int), the buggy line `if self.can_delete and (self.can_delete_extra or index < initial_form_count):`, AND the exact suggested fix `(index is not None and index < initial_form_count)`. Everything in requirements.md is a behavioral translation of this public content. No hidden-test artifacts appear: the test name (test_disable_delete_extra_formset_forms), file path (forms_tests/tests/test_formsets.py), class names (FormsFormsetTestCase / Jinja2FormsFormsetTestCase), and the added assertion `assertNotIn('DELETE', formset.empty_form.fields)` are absent. The hidden test adds a SINGLE assertion (not parametrized), so Requirement 2's combination enumeration is derived from the logical truth-table of the publicly-disclosed fix expression, not from test parametrization. Naming add_fields/empty_form/BaseFormSet/DELETION_FIELD_NAME is legitimate localization. Requirement 2.7 and Req 3's ordering-field details describe general documented formset behavior, not test-specific cases.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
