# P2 adversarial audit — django__django-12193

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
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.forms.widgets import CheckboxInput

# Req1.1: get_context must NOT mutate caller's attrs when checked.
w = CheckboxInput()
attrs = {"id": "x"}
before = dict(attrs)
ctx = w.get_context("f", True, attrs)
print("attrs after:", attrs)
if attrs != before:
    print("FAIL: caller attrs mutated")
    sys.exit(1)
if "checked" in attrs:
    print("FAIL: checked leaked into caller attrs")
    sys.exit(1)
print("PASS: caller attrs untouched")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.forms.widgets import CheckboxInput

# Req1.2: returned context attrs include checked=True when checked.
w = CheckboxInput()
attrs = {"id": "x"}
ctx = w.get_context("f", True, attrs)
cattrs = ctx["widget"]["attrs"]
print("context attrs:", cattrs)
if cattrs.get("checked") is not True:
    print("FAIL: context attrs missing checked=True")
    sys.exit(1)
# distinct from caller object
if cattrs is attrs:
    print("FAIL: context attrs is the SAME object as caller attrs")
    sys.exit(1)
print("PASS: context has checked=True in distinct dict")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.forms.widgets import CheckboxInput

# Req1.3: reuse one attrs dict across mix of checked/unchecked; each reflects own value.
w = CheckboxInput()
shared = {"class": "c"}
# first render checked
c1 = w.get_context("f1", True, shared)["widget"]["attrs"]
# then render unchecked using same dict object
c2 = w.get_context("f2", False, shared)["widget"]["attrs"]
print("c1:", c1)
print("c2:", c2)
print("shared:", shared)
if c1.get("checked") is not True:
    print("FAIL: checked render lost checked")
    sys.exit(1)
if "checked" in c2:
    print("FAIL: unchecked render spuriously checked (mutation bug)")
    sys.exit(1)
if "checked" in shared:
    print("FAIL: shared dict retained checked")
    sys.exit(1)
print("PASS: each render reflects own state; shared dict clean")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.forms.widgets import CheckboxInput

# Req1.4: attrs=None + checked value -> no error, context checked=True.
# Req1.5: unchecked -> no checked key in produced context.
w = CheckboxInput()
ctx = w.get_context("f", True, None)
cattrs = ctx["widget"]["attrs"]
print("None-attrs checked context:", cattrs)
if cattrs.get("checked") is not True:
    print("FAIL: None attrs checked did not produce checked=True")
    sys.exit(1)

# unchecked path (Req1.5)
attrs = {"id": "x"}
before = dict(attrs)
ctx2 = w.get_context("f", False, attrs)
c2 = ctx2["widget"]["attrs"]
print("unchecked context attrs:", c2, "caller attrs:", attrs)
if "checked" in c2:
    print("FAIL: unchecked introduced checked into context")
    sys.exit(1)
if attrs != before:
    print("FAIL: unchecked path mutated caller attrs")
    sys.exit(1)
print("PASS: None-checked and unchecked semantics correct")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.forms.widgets import CheckboxInput

# Req2: rendered HTML checked marker + value attribute semantics; Req2.4 type=checkbox.
w = CheckboxInput()

def render(val):
    return w.render("f", val)

# checked cases
for v in [True, "hello", 5]:
    html = render(v)
    if "checked" not in html:
        print("FAIL: checked marker missing for", repr(v), html)
        sys.exit(1)
# unchecked cases
for v in [False, None, ""]:
    html = render(v)
    if "checked" in html:
        print("FAIL: checked marker present for unchecked", repr(v), html)
        sys.exit(1)
# value attribute: non-empty non-bool -> value present
h = render("hello")
print(h)
if 'value="hello"' not in h:
    print("FAIL: value attr missing for string value")
    sys.exit(1)
# True/False/None/"" -> no value attr
for v in [True, False, None, ""]:
    h = render(v)
    if "value=" in h:
        print("FAIL: value attr present for", repr(v), h)
        sys.exit(1)
# type=checkbox
if 'type="checkbox"' not in render(True):
    print("FAIL: not rendered as checkbox type")
    sys.exit(1)
print("PASS: rendering semantics preserved")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.forms.widgets import CheckboxInput

# Req3: custom check_test honored; exceptions propagate; default check.
# Req4: value_from_datadict + value_omitted_from_data.

# custom check_test
w = CheckboxInput(check_test=lambda v: v == "yes")
if "checked" not in w.render("f", "yes"):
    print("FAIL: custom check_test truthy not marked checked")
    sys.exit(1)
if "checked" in w.render("f", "no"):
    print("FAIL: custom check_test falsy marked checked")
    sys.exit(1)

# exception propagates
def boom(v):
    raise ValueError("boom")
we = CheckboxInput(check_test=boom)
try:
    we.get_context("f", "x", {})
    print("FAIL: exception was suppressed")
    sys.exit(1)
except ValueError:
    pass

# default check
wd = CheckboxInput()
if not wd.check_test("anything"):
    print("FAIL: default check_test false for truthy")
    sys.exit(1)
for v in [False, None, ""]:
    if wd.check_test(v):
        print("FAIL: default check_test true for", repr(v))
        sys.exit(1)

# Req4.1 absent -> False
wv = CheckboxInput()
if wv.value_from_datadict({}, {}, "f") is not False:
    print("FAIL: absent name not False")
    sys.exit(1)
# Req4.2 true/false case-insensitive
if wv.value_from_datadict({"f": "true"}, {}, "f") is not True:
    print("FAIL: 'true' not True")
    sys.exit(1)
if wv.value_from_datadict({"f": "FALSE"}, {}, "f") is not False:
    print("FAIL: 'FALSE' not False")
    sys.exit(1)
# other -> bool coercion
if wv.value_from_datadict({"f": "1"}, {}, "f") is not True:
    print("FAIL: '1' not True")
    sys.exit(1)
# Req4.3 never omitted
if wv.value_omitted_from_data({}, {}, "f") is not False:
    print("FAIL: value_omitted not False")
    sys.exit(1)
print("PASS: check_test + value extraction preserved")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.forms.widgets import CheckboxInput

# Req1.1: get_context must NOT mutate caller's attrs when checked.
w = CheckboxInput()
attrs = {"id": "x"}
before = dict(attrs)
ctx = w.get_context("f", True, attrs)
print("attrs after:", attrs)
if attrs != before:
    print("FAIL: caller attrs mutated")
    sys.exit(1)
if "checked" in attrs:
    print("FAIL: checked leaked into caller attrs")
    sys.exit(1)
print("PASS: caller attrs untouched")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probe->requirement mapping and observed results:
- probe_1 (Req1.1): get_context must not mutate caller attrs when checked. PATCHED: HOLDS (attrs stays {'id':'x'}). BASE: FAILS (attrs gains 'checked'). WEAK: FAILS. => positive control, discriminates.
- probe_2 (Req1.2): returned context attrs include checked=True in a dict distinct from caller. PATCHED: HOLDS.
- probe_3 (Req1.3): reuse one attrs dict across checked-then-unchecked; each reflects own state; shared dict clean. PATCHED: HOLDS. BASE: FAILS (second unchecked render spuriously checked). WEAK: FAILS. => also a positive-control-strength discriminator.
- probe_4 (Req1.4 & 1.5): attrs=None+checked -> context checked=True no error; unchecked -> no checked key and caller attrs unchanged. PATCHED: HOLDS.
- probe_5 (Req2.1-2.4 regression): rendered HTML checked marker for True/'hello'/5; absent for False/None/''; value attr present for non-empty non-bool, omitted for True/False/None/''; type=checkbox. PATCHED: HOLDS. BASE: HOLDS (regression criterion, correctly non-discriminating).
- probe_6 (Req3 & Req4 regression): custom check_test honored, exceptions propagate, default check semantics; value_from_datadict absent->False, true/false case-insensitive, other->bool; value_omitted_from_data always False. PATCHED: HOLDS. BASE: HOLDS.

Positive control probe_1: FAILS at base (mutation bug reproduced), HOLDS patched -> discriminating power confirmed. prepatch_reproduced=true.

Candidate patch 'weak_mutates_nonNone_attrs': the lazy partial fix that only fixes the attrs-is-None branch (attrs={'checked':True}) but keeps attrs['checked']=True when attrs is non-None — i.e. still mutates the caller's dict in the common case, the actual SplitArrayWidget bug. REJECTED by probe_1 and probe_3 (both VIOLATED under --patch). This demonstrates the suite discriminates a wrong-but-plausible implementation, so the requirements are not too weak on the core mutation criterion.

Gold patch (attrs = {**(attrs or {}), 'checked': True}) satisfies all probes. Verdict SOUND.

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
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.forms.widgets import CheckboxInput

# Req1.1: get_context must NOT mutate caller's attrs when checked.
w = CheckboxInput()
attrs = {"id": "x"}
before = dict(attrs)
ctx = w.get_context("f", True, attrs)
print("attrs after:", attrs)
if attrs != before:
    print("FAIL: caller attrs mutated")
    sys.exit(1)
if "checked" in attrs:
    print("FAIL: checked leaked into caller attrs")
    sys.exit(1)
print("PASS: caller attrs untouched")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probe->requirement mapping and observed results:
- probe_1 (Req1.1): get_context must not mutate caller attrs when checked. PATCHED: HOLDS (attrs stays {'id':'x'}). BASE: FAILS (attrs gains 'checked'). WEAK: FAILS. => positive control, discriminates.
- probe_2 (Req1.2): returned context attrs include checked=True in a dict distinct from caller. PATCHED: HOLDS.
- probe_3 (Req1.3): reuse one attrs dict across checked-then-unchecked; each reflects own state; shared dict clean. PATCHED: HOLDS. BASE: FAILS (second unchecked render spuriously checked). WEAK: FAILS. => also a positive-control-strength discriminator.
- probe_4 (Req1.4 & 1.5): attrs=None+checked -> context checked=True no error; unchecked -> no checked key and caller attrs unchanged. PATCHED: HOLDS.
- probe_5 (Req2.1-2.4 regression): rendered HTML checked marker for True/'hello'/5; absent for False/None/''; value attr present for non-empty non-bool, omitted for True/False/None/''; type=checkbox. PATCHED: HOLDS. BASE: HOLDS (regression criterion, correctly non-discriminating).
- probe_6 (Req3 & Req4 regression): custom check_test honored, exceptions propagate, default check semantics; value_from_datadict absent->False, true/false case-insensitive, other->bool; value_omitted_from_data always False. PATCHED: HOLDS. BASE: HOLDS.

Positive control probe_1: FAILS at base (mutation bug reproduced), HOLDS patched -> discriminating power confirmed. prepatch_reproduced=true.

Candidate patch 'weak_mutates_nonNone_attrs': the lazy partial fix that only fixes the attrs-is-None branch (attrs={'checked':True}) but keeps attrs['checked']=True when attrs is non-None — i.e. still mutates the caller's dict in the common case, the actual SplitArrayWidget bug. REJECTED by probe_1 and probe_3 (both VIOLATED under --patch). This demonstrates the suite discriminates a wrong-but-plausible implementation, so the requirements are not too weak on the core mutation criterion.

Gold patch (attrs = {**(attrs or {}), 'checked': True}) satisfies all probes. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe run in instance image: patched HOLDS (exit 0), base VIOLATED (AssertionError: {'foo':'bar','checked':True}). Verified Req1.1-1.5 (no mutation, distinct dict, checked=True preserved, attrs=None case, unchecked case leaves no checked key), Req2 (value render omitted for True/None, present for 'hello'), Req3.2 (custom check_test exception propagates), Req4 (value_from_datadict true/false/int, value_omitted_from_data always False). All preserved-behavior requirements match unchanged code; the changed-behavior requirement (Req1) is pinned at the correct modeling boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes behavior, not the hidden tests. The core defect (CheckboxInput.get_context mutating the caller's attrs dict, causing SplitArrayField/BooleanField widgets to stay checked after the first True) is already fully public in the problem_statement, including the module/method and line reference. Naming django/forms/widgets.py and CheckboxInput.get_context is legitimate localization. Requirements translate what to verify into behavioral SHALL statements: no mutation of caller attrs (F2P test_get_context_does_not_mutate_attrs), reuse across mixed checked/unchecked renders (test_checkbox_get_context_attrs, SplitArrayWidget scenario already in problem_statement), and preservation of rendering/value-extraction/omission behavior (PASS_TO_PASS). No test file paths, function/class names, parametrization ids, or verbatim gold-patch lines appear. The gold fix (`attrs = {**(attrs or {}), 'checked': True}`) introduces no new identifier that leaks. The value_from_datadict 'true'/'false' case-insensitive and value_omitted-always-False descriptions restate existing public widget behavior, not test-specific enumerations. No reconstruction of hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
