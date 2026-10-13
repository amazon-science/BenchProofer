# P2 adversarial audit — django__django-12276

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
"""Positive control / Req 1.2: FileInput with truthy initial => required marker NOT used (falsy)."""
from django.forms.widgets import FileInput
w = FileInput()
res = w.use_required_attribute("some_stored_file.txt")
print("FileInput.use_required_attribute('some_stored_file.txt') =", res)
import sys
sys.exit(0 if not res else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1: FileInput with falsy initial (None) => required marker IS used (truthy)."""
from django.forms.widgets import FileInput
w = FileInput()
res = w.use_required_attribute(None)
print("FileInput.use_required_attribute(None) =", res)
import sys
sys.exit(0 if res else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.3: FileInput decision == conjunction of base rule and (not initial), across cases."""
from django.forms.widgets import FileInput, Widget
w = FileInput()
ok = True
for initial in [None, "", 0, "f.txt", "x", 5]:
    base = Widget.use_required_attribute(w, initial)  # base rule
    expected = bool(base and not initial)
    got = bool(w.use_required_attribute(initial))
    print("initial=%r base=%r expected=%r got=%r" % (initial, base, expected, got))
    if got != expected:
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2: Rendered FileField(FileInput) HTML includes 'required' iff no initial data.
Also Req 2.3: markup otherwise identical (only 'required' differs)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False,
                        INSTALLED_APPS=[], DATABASES={})
    django.setup()
from django import forms

class F(forms.Form):
    f = forms.FileField(widget=forms.FileInput)

# no initial
html_no = str(F().as_p())
# truthy initial via form initial
html_init = str(F(initial={"f": "stored.txt"}).as_p())
print("no-initial html:", html_no)
print("with-initial html:", html_init)

import re
def field_input(html):
    m = re.search(r'<input[^>]*type="file"[^>]*>', html)
    return m.group(0) if m else None

in_no = field_input(html_no)
in_init = field_input(html_init)
print("no-initial input:", in_no)
print("with-initial input:", in_init)

ok = True
if in_no is None or 'required' not in in_no:
    print("FAIL: no-initial input missing required")
    ok = False
if in_init is None or 'required' in in_init:
    print("FAIL: with-initial input should not have required")
    ok = False
# Req 2.3: identical except required
if in_no and in_init:
    stripped = in_no.replace(' required', '').replace('required', '')
    if stripped != in_init:
        print("FAIL: markup differs beyond required attr:", repr(stripped), repr(in_init))
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.1: ClearableFileInput preserves suppression: truthy initial => falsy; falsy initial => truthy."""
from django.forms.widgets import ClearableFileInput
w = ClearableFileInput()
r_init = w.use_required_attribute("stored.txt")
r_none = w.use_required_attribute(None)
print("Clearable truthy-initial =", r_init, " none-initial =", r_none)
import sys
sys.exit(0 if (not r_init and r_none) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.2: non-file widgets unaffected by initial. TextInput required regardless of initial;
hidden input never required."""
from django.forms.widgets import TextInput, HiddenInput
t = TextInput()
h = HiddenInput()
ok = True
for initial in [None, "x", "value"]:
    if not t.use_required_attribute(initial):
        print("FAIL: TextInput should be required for initial=%r" % (initial,))
        ok = False
    if h.use_required_attribute(initial):
        print("FAIL: HiddenInput should never be required, initial=%r" % (initial,))
        ok = False
print("TextInput/HiddenInput behavior checked, ok=", ok)
import sys
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 3.3 & 3.4: FileInput never emits stored value into markup; value_omitted_from_data
true exactly when name not in files."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False,
                        INSTALLED_APPS=[], DATABASES={})
    django.setup()
from django.forms.widgets import FileInput
w = FileInput()
ok = True
# 3.3: rendering never includes stored value
html = w.render("myfile", "stored_secret.txt")
print("rendered:", html)
if "stored_secret.txt" in html:
    print("FAIL: stored value leaked into markup")
    ok = False
if 'value=' in html:
    print("FAIL: value attribute present")
    ok = False
# 3.4: value_omitted_from_data
o_absent = w.value_omitted_from_data({}, {}, "myfile")
o_present = w.value_omitted_from_data({}, {"myfile": object()}, "myfile")
print("omitted when absent =", o_absent, " when present =", o_present)
if not o_absent or o_present:
    print("FAIL: value_omitted_from_data semantics wrong")
    ok = False
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.2: FileInput with truthy initial => required marker NOT used (falsy)."""
from django.forms.widgets import FileInput
w = FileInput()
res = w.use_required_attribute("some_stored_file.txt")
print("FileInput.use_required_attribute('some_stored_file.txt') =", res)
import sys
sys.exit(0 if not res else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-12276: FileInput.use_required_attribute must suppress required when initial is truthy (moved up from ClearableFileInput). 7 probes cover all criteria:
- probe_1 (Req 1.2, positive control): FileInput truthy initial => falsy. HOLDS patched, FAILS/VIOLATED at base (base returns True). Discriminates.
- probe_2 (Req 1.1): FileInput None initial => truthy. HOLDS patched.
- probe_3 (Req 1.3): decision == base AND not initial across {None,'',0,'f.txt','x',5}. HOLDS patched.
- probe_4 (Req 2.1/2.2/2.3, also positive control): rendered FileField HTML includes 'required' iff no initial, and markup otherwise identical. HOLDS patched, FAILS at base.
- probe_5 (Req 3.1): ClearableFileInput still suppresses on truthy initial, allows on None. HOLDS patched.
- probe_6 (Req 3.2): TextInput required regardless of initial; HiddenInput never required. HOLDS patched.
- probe_7 (Req 3.3/3.4): FileInput never emits stored value into markup; value_omitted_from_data True iff name not in files. HOLDS patched.

All 7 HOLD on gold-patched tree. Positive control fails at base and holds patched (prepatch reproduced).

Candidate wrong-fix (weak.diff): `super().use_required_attribute(initial) and initial` (missing `not`) — REJECTED by probes 1,2,3,4,5 (VIOLATED). Probes 6,7 hold (unrelated to the bug). This demonstrates the suite discriminates wrong implementations. No requirements-conforming-yet-harness-failing alternative was found; the requirements (esp. Req 1.3's exact conjunction and Req 2.3's markup-identity) pin the fix precisely. Verdict SOUND.

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
"""Positive control / Req 1.2: FileInput with truthy initial => required marker NOT used (falsy)."""
from django.forms.widgets import FileInput
w = FileInput()
res = w.use_required_attribute("some_stored_file.txt")
print("FileInput.use_required_attribute('some_stored_file.txt') =", res)
import sys
sys.exit(0 if not res else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-12276: FileInput.use_required_attribute must suppress required when initial is truthy (moved up from ClearableFileInput). 7 probes cover all criteria:
- probe_1 (Req 1.2, positive control): FileInput truthy initial => falsy. HOLDS patched, FAILS/VIOLATED at base (base returns True). Discriminates.
- probe_2 (Req 1.1): FileInput None initial => truthy. HOLDS patched.
- probe_3 (Req 1.3): decision == base AND not initial across {None,'',0,'f.txt','x',5}. HOLDS patched.
- probe_4 (Req 2.1/2.2/2.3, also positive control): rendered FileField HTML includes 'required' iff no initial, and markup otherwise identical. HOLDS patched, FAILS at base.
- probe_5 (Req 3.1): ClearableFileInput still suppresses on truthy initial, allows on None. HOLDS patched.
- probe_6 (Req 3.2): TextInput required regardless of initial; HiddenInput never required. HOLDS patched.
- probe_7 (Req 3.3/3.4): FileInput never emits stored value into markup; value_omitted_from_data True iff name not in files. HOLDS patched.

All 7 HOLD on gold-patched tree. Positive control fails at base and holds patched (prepatch reproduced).

Candidate wrong-fix (weak.diff): `super().use_required_attribute(initial) and initial` (missing `not`) — REJECTED by probes 1,2,3,4,5 (VIOLATED). Probes 6,7 hold (unrelated to the bug). This demonstrates the suite discriminates wrong implementations. No requirements-conforming-yet-harness-failing alternative was found; the requirements (esp. Req 1.3's exact conjunction and Req 2.3's markup-identity) pin the fix precisely. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the exact changed observable behavior (the use_required_attribute boundary on FileInput), not a narrow slice or unrelated helper. value_omitted_from_data (Req 3.4) is correctly described as unchanged for FileInput (`name not in files`); the diff only removes the override on ClearableFileInput's separate value_omitted, not FileInput's. No mandated behavior absent from the patch; no forbidden behavior present.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already names FileInput, ClearableFileInput, use_required_attribute(), the required HTML attribute, django/forms/widgets.py L454, and the 'file already set when editing a model instance' scenario. The requirements localize the change to FileInput.use_required_attribute (legitimate) and translate behavior (initial truthy => suppress required; rendered <input type=file> includes/omits required) into EARS criteria. No hidden-test artifacts are transmitted: no test function/class names (test_use_required_attribute, test_filefield_with_fileinput_required), no test file paths, no parametrization ids, no verbatim test HTML strings ('resume.txt', '<tr><th>File1:</th>...'), and no verbatim gold-patch line (super().use_required_attribute(initial) and not initial). The gold introduces no invented identifiers to leak. Req 3.3/3.4 restate pre-existing base FileInput behavior (value_omitted_from_data = name not in files) for preservation/localization; this describes existing behavior rather than transcribing a test assertion, and the method is public Django API. Case enumerations are behavioral (falsy vs truthy initial), matching the domain, not mirroring a bespoke test parametrization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
