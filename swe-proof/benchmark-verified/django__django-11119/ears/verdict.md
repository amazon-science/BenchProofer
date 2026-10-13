# P2 adversarial audit — django__django-11119

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
"""Req1.1 / positive control: Engine(autoescape=False).render_to_string with
plain data must NOT escape interpolated values."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True)
django.setup()
import os, tempfile
from django.template.engine import Engine

d = tempfile.mkdtemp()
with open(os.path.join(d, "t.html"), "w") as f:
    f.write("X{{ v }}Y")

eng = Engine(dirs=[d], autoescape=False)
out = eng.render_to_string("t.html", {"v": '<a>&"\''})
print("output:", repr(out))
expected = 'X<a>&"\'Y'
if out == expected:
    print("HOLDS: unescaped as configured")
    raise SystemExit(0)
print("VIOLATION: got", repr(out), "expected", repr(expected))
raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 / 2.3: Engine(autoescape=True) [default] with plain data must ESCAPE
interpolated values."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True)
django.setup()
import os, tempfile
from django.template.engine import Engine

d = tempfile.mkdtemp()
with open(os.path.join(d, "t.html"), "w") as f:
    f.write("X{{ v }}Y")

eng = Engine(dirs=[d])  # default autoescape=True
assert eng.autoescape is True
out = eng.render_to_string("t.html", {"v": '<a>&"\''})
print("output:", repr(out))
expected = 'X&lt;a&gt;&amp;&quot;&#39;Y'
if out == expected:
    print("HOLDS: escaped as configured")
    raise SystemExit(0)
print("FAIL: got", repr(out), "expected", repr(expected))
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.4: literal (non-interpolated) template text is unchanged regardless of
autoescape setting. Literal HTML chars in the template stay verbatim under
both engines; only the interpolated value differs."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True)
django.setup()
import os, tempfile
from django.template.engine import Engine

d = tempfile.mkdtemp()
# literal contains HTML-significant chars in the STATIC text
with open(os.path.join(d, "t.html"), "w") as f:
    f.write("<b>&amp;</b>[{{ v }}]")

eng_f = Engine(dirs=[d], autoescape=False)
eng_t = Engine(dirs=[d], autoescape=True)
out_f = eng_f.render_to_string("t.html", {"v": "z"})
out_t = eng_t.render_to_string("t.html", {"v": "z"})
print("false-engine:", repr(out_f))
print("true-engine :", repr(out_t))
lit = "<b>&amp;</b>[z]"
ok = out_f == lit and out_t == lit
if ok:
    print("HOLDS: literal text unchanged under both settings")
    raise SystemExit(0)
print("FAIL: literal text altered")
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1 / 2.2: If caller supplies a Context, it is used as-is and the engine's
autoescape must NOT override the context's own autoescape setting.
Engine(autoescape=False) but Context(autoescape=True) -> value ESCAPED.
Engine(autoescape=True) but Context(autoescape=False) -> value NOT escaped."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True)
django.setup()
import os, tempfile
from django.template.engine import Engine
from django.template.context import Context

d = tempfile.mkdtemp()
with open(os.path.join(d, "t.html"), "w") as f:
    f.write("{{ v }}")

eng_false = Engine(dirs=[d], autoescape=False)
eng_true = Engine(dirs=[d], autoescape=True)

# context autoescape=True wins over engine False
out1 = eng_false.render_to_string("t.html", Context({"v": "<x>"}, autoescape=True))
# context autoescape=False wins over engine True
out2 = eng_true.render_to_string("t.html", Context({"v": "<x>"}, autoescape=False))
print("engineFalse/ctxTrue:", repr(out1))
print("engineTrue/ctxFalse:", repr(out2))
if out1 == "&lt;x&gt;" and out2 == "<x>":
    print("HOLDS: supplied Context governs escaping")
    raise SystemExit(0)
print("FAIL: engine overrode supplied context")
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1: render_to_string with a list/tuple of names renders the first
LOADABLE template, preserving selection order & not-found fallthrough."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True)
django.setup()
import os, tempfile
from django.template.engine import Engine
from django.template.exceptions import TemplateDoesNotExist

d = tempfile.mkdtemp()
with open(os.path.join(d, "second.html"), "w") as f:
    f.write("SECOND{{ v }}")
with open(os.path.join(d, "third.html"), "w") as f:
    f.write("THIRD")

eng = Engine(dirs=[d], autoescape=False)
# first name missing -> should fall through to second.html
out = eng.render_to_string(["missing.html", "second.html", "third.html"], {"v": "<z>"})
print("list output:", repr(out))
if out != "SECOND<z>":
    print("FAIL: wrong template selected:", repr(out))
    raise SystemExit(1)

# all missing -> TemplateDoesNotExist
try:
    eng.render_to_string(["nope1.html", "nope2.html"])
    print("FAIL: expected TemplateDoesNotExist")
    raise SystemExit(1)
except TemplateDoesNotExist:
    print("HOLDS: order preserved and not-found raised")
    raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.4: Engine.get_default() returns the single configured Django templates
engine, and raises when none configured. (Preserve unrelated behavior.)"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {"autoescape": False},
        }],
    )
django.setup()
from django.template.engine import Engine

eng = Engine.get_default()
print("default engine autoescape:", eng.autoescape)
# The configured OPTIONS set autoescape False; get_default must surface that engine.
if eng.autoescape is not False:
    print("FAIL: get_default did not return configured engine")
    raise SystemExit(1)

# Now check the "none configured" error path with a fresh settings-less call is
# hard here; instead verify get_default is stable/idempotent.
eng2 = Engine.get_default()
if eng is eng2:
    print("HOLDS: get_default returns configured engine consistently")
    raise SystemExit(0)
print("FAIL: get_default not consistent")
raise SystemExit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1 / positive control: Engine(autoescape=False).render_to_string with
plain data must NOT escape interpolated values."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True)
django.setup()
import os, tempfile
from django.template.engine import Engine

d = tempfile.mkdtemp()
with open(os.path.join(d, "t.html"), "w") as f:
    f.write("X{{ v }}Y")

eng = Engine(dirs=[d], autoescape=False)
out = eng.render_to_string("t.html", {"v": '<a>&"\''})
print("output:", repr(out))
expected = 'X<a>&"\'Y'
if out == expected:
    print("HOLDS: unescaped as configured")
    raise SystemExit(0)
print("VIOLATION: got", repr(out), "expected", repr(expected))
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: render_to_string builds Context(context, autoescape=self.autoescape) for plain data (django/template/engine.py). Six probes, all HOLD on patched tree:
- probe_1 (Req1.1, POSITIVE CONTROL): Engine(autoescape=False)+plain data emits interpolated HTML chars verbatim. HOLDS patched, FAILS at base (base escapes) => discriminates.
- probe_2 (Req1.2/2.3): Engine default autoescape=True escapes interpolated value. HOLDS. (This Django version escapes ' as &#39;, not &#x27; — corrected expectation.)
- probe_3 (Req1.4): literal template HTML text unchanged under both False/True engines.
- probe_4 (Req2.1/2.2): supplied Context's own autoescape governs, engine does NOT override (both directions).
- probe_5 (Req3.1): list of names renders first LOADABLE, preserves order; all-missing raises TemplateDoesNotExist.
- probe_6 (Req3.4): get_default returns configured engine (autoescape=False from OPTIONS), consistently.

CANDIDATE PATCH exercised: weak_hardcode_false.diff hardcodes Context(context, autoescape=False) instead of self.autoescape. It satisfies probe_1 and probe_4 but is REJECTED by probe_2 (default engine no longer escapes) => suite discriminates wrong implementations. No probe-conforming alternative found. Verdict SOUND.

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
"""Req1.1 / positive control: Engine(autoescape=False).render_to_string with
plain data must NOT escape interpolated values."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True)
django.setup()
import os, tempfile
from django.template.engine import Engine

d = tempfile.mkdtemp()
with open(os.path.join(d, "t.html"), "w") as f:
    f.write("X{{ v }}Y")

eng = Engine(dirs=[d], autoescape=False)
out = eng.render_to_string("t.html", {"v": '<a>&"\''})
print("output:", repr(out))
expected = 'X<a>&"\'Y'
if out == expected:
    print("HOLDS: unescaped as configured")
    raise SystemExit(0)
print("VIOLATION: got", repr(out), "expected", repr(expected))
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: render_to_string builds Context(context, autoescape=self.autoescape) for plain data (django/template/engine.py). Six probes, all HOLD on patched tree:
- probe_1 (Req1.1, POSITIVE CONTROL): Engine(autoescape=False)+plain data emits interpolated HTML chars verbatim. HOLDS patched, FAILS at base (base escapes) => discriminates.
- probe_2 (Req1.2/2.3): Engine default autoescape=True escapes interpolated value. HOLDS. (This Django version escapes ' as &#39;, not &#x27; — corrected expectation.)
- probe_3 (Req1.4): literal template HTML text unchanged under both False/True engines.
- probe_4 (Req2.1/2.2): supplied Context's own autoescape governs, engine does NOT override (both directions).
- probe_5 (Req3.1): list of names renders first LOADABLE, preserves order; all-missing raises TemplateDoesNotExist.
- probe_6 (Req3.4): get_default returns configured engine (autoescape=False from OPTIONS), consistently.

CANDIDATE PATCH exercised: weak_hardcode_false.diff hardcodes Context(context, autoescape=False) instead of self.autoescape. It satisfies probe_1 and probe_4 but is REJECTED by probe_2 (default engine no longer escapes) => suite discriminates wrong implementations. No probe-conforming alternative found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed observable behavior biconditionally (both False and True engines) rather than a narrow slice, and correctly distinguish the plain-data path (rewrapped with engine autoescape) from the pre-built Context path (used as-is). No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior. Modeling boundary is exactly the changed line.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The FAIL_TO_PASS behavior (test_autoescape_off) is fully covered by the PUBLIC problem_statement, which already names Engine.render_to_string, the autoescape=False path, and the un-propagated Context construction. The doc uses the generic HTML-escape set (< > & " ') as illustration, NOT the test's actual payload '<script>', and never mentions the template file test_context.html, any test/class names, ids, or parametrization. Naming django/template/engine.py, base.py, render_value_in_context, and Context is legitimate localization. The one gold-edit token (autoescape=self.autoescape) is directly implied by the problem_statement itself. Requirement 3 enumerates loader priority / cached-loader precedence / origin / get_default(one|several|none) which coincides with the PASS_TO_PASS set, but these are the intrinsic branch structure of the public Engine methods being guarded against regression (derivable from source), not a reconstruction of the hidden tests. No quoted test/gold code, no fix-invented identifiers beyond the public wording. Borderline item noted but does not rise to leakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
