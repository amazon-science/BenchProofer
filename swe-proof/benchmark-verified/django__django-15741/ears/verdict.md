# P2 adversarial audit — django__django-15741

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
"""Positive control / R1.1, R1.2, R2.6: get_format accepts a lazy format_type,
returns without TypeError, equals the concrete-string result, and returns a
concrete str (not a proxy). FAILS at base (TypeError in getattr)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_L10N=True, USE_TZ=True,
                        INSTALLED_APPS=[], DATABASES={})
django.setup()

from django.utils import formats
from django.utils.translation import gettext_lazy
from django.utils.functional import Promise

lazy_name = gettext_lazy("H:i")
try:
    res_lazy = formats.get_format(lazy_name)
except Exception as e:
    print("FAIL: get_format raised on lazy format_type:", type(e).__name__, e)
    raise SystemExit(1)

res_concrete = formats.get_format("H:i")
print("lazy result:", repr(res_lazy), "type:", type(res_lazy).__name__)
print("concrete result:", repr(res_concrete))

ok = True
if res_lazy != res_concrete:
    print("FAIL: lazy result != concrete result")
    ok = False
if isinstance(res_lazy, Promise):
    print("FAIL: lazy result is a deferred proxy, not a concrete value")
    ok = False
if not isinstance(res_lazy, str):
    print("FAIL: lazy result is not a str:", type(res_lazy))
    ok = False
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.3, R2.2: lazy format_type naming a recognized localized format returns
that locale's value, identical to the concrete name. Use DATE_FORMAT under an
active language with format modules (en)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_L10N=True, USE_TZ=True,
                        INSTALLED_APPS=[], DATABASES={})
django.setup()

from django.utils import formats
from django.utils.translation import gettext_lazy, override

ok = True
with override("en"):
    lazy_res = formats.get_format(gettext_lazy("DATE_FORMAT"))
    conc_res = formats.get_format("DATE_FORMAT")
    print("en DATE_FORMAT lazy:", repr(lazy_res), "concrete:", repr(conc_res))
    if lazy_res != conc_res:
        print("FAIL: en mismatch"); ok = False
    # must be a real localized value, not just echoing the name back
    if lazy_res == "DATE_FORMAT":
        print("FAIL: returned the name unchanged, no localized value"); ok = False
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.1, R2.3, R2.4: concrete-string behavior preserved.
- known localized format DATE_FORMAT -> value from settings/modules (not name)
- unknown name -> returned unchanged
- known setting with l10n disabled -> value from settings
"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_L10N=True, USE_TZ=True,
                        INSTALLED_APPS=[], DATABASES={})
django.setup()

from django.utils import formats

ok = True
# unknown name returned unchanged (R2.4)
unknown = formats.get_format("this-is-not-a-format-name")
print("unknown ->", repr(unknown))
if unknown != "this-is-not-a-format-name":
    print("FAIL: unknown name not returned unchanged"); ok = False

# known setting resolved to settings value when l10n disabled (R2.3)
val = formats.get_format("DATE_FORMAT", use_l10n=False)
print("DATE_FORMAT (l10n off) ->", repr(val))
if val != settings.DATE_FORMAT:
    print("FAIL: l10n-off DATE_FORMAT != settings.DATE_FORMAT"); ok = False

# DECIMAL_SEPARATOR known setting concrete (R2.1)
ds = formats.get_format("DECIMAL_SEPARATOR", use_l10n=False)
print("DECIMAL_SEPARATOR (l10n off) ->", repr(ds))
if ds != settings.DECIMAL_SEPARATOR:
    print("FAIL: DECIMAL_SEPARATOR mismatch"); ok = False

print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.2, R3.3: the `date` template filter with a lazy format arg (_("H:i"))
renders identical, fully-evaluated concrete output as the concrete arg.
Mirrors the issue's use case. Input midnight time -> expected concrete str.
FAILS at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_L10N=True, USE_TZ=True,
                        INSTALLED_APPS=[],
                        TEMPLATES=[{
                            "BACKEND": "django.template.backends.django.DjangoTemplates",
                            "DIRS": [], "APP_DIRS": False,
                            "OPTIONS": {}}],
                        DATABASES={})
django.setup()

from datetime import time
from django.template import engines
from django.utils.functional import Promise

dj = engines["django"]
ctx = {"t": time(0, 0)}

def render(src):
    return dj.from_string(src).render(ctx)

out_lazy = render('{{ t|date:_("H:i") }}')
out_conc = render('{{ t|date:"H:i" }}')
print("lazy render:", repr(out_lazy))
print("concrete render:", repr(out_conc))

ok = True
if isinstance(out_lazy, Promise):
    print("FAIL: rendered output is a proxy"); ok = False
if out_lazy != out_conc:
    print("FAIL: lazy render != concrete render"); ok = False
if out_lazy != "00:00":
    print("FAIL: expected '00:00', got", repr(out_lazy)); ok = False
if not out_lazy:
    print("FAIL: empty result"); ok = False
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.1: the date/time formatting helpers (date_format/time_format) accept a
lazy format arg and produce output identical to the concrete arg. Also R1.4:
text-equal names yield equal results regardless of concrete/lazy origin."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_L10N=True, USE_TZ=True,
                        INSTALLED_APPS=[], DATABASES={})
django.setup()

from datetime import datetime, time
from django.utils import formats
from django.utils.translation import gettext_lazy

ok = True
dt = datetime(2023, 1, 2, 13, 45, 0)

# date_format with lazy format
df_lazy = formats.date_format(dt, gettext_lazy("Y-m-d H:i"))
df_conc = formats.date_format(dt, "Y-m-d H:i")
print("date_format lazy:", repr(df_lazy), "concrete:", repr(df_conc))
if df_lazy != df_conc:
    print("FAIL: date_format lazy != concrete"); ok = False

# time_format with lazy format
tf_lazy = formats.time_format(time(9, 5), gettext_lazy("H:i"))
tf_conc = formats.time_format(time(9, 5), "H:i")
print("time_format lazy:", repr(tf_lazy), "concrete:", repr(tf_conc))
if tf_lazy != tf_conc:
    print("FAIL: time_format lazy != concrete"); ok = False

# R1.4: two distinct lazy objects with equal text -> equal get_format result
a = formats.get_format(gettext_lazy("H:i"))
b = formats.get_format("H:i")
if a != b:
    print("FAIL: R1.4 text-equal names differ"); ok = False

print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / R1.1, R1.2, R2.6: get_format accepts a lazy format_type,
returns without TypeError, equals the concrete-string result, and returns a
concrete str (not a proxy). FAILS at base (TypeError in getattr)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_L10N=True, USE_TZ=True,
                        INSTALLED_APPS=[], DATABASES={})
django.setup()

from django.utils import formats
from django.utils.translation import gettext_lazy
from django.utils.functional import Promise

lazy_name = gettext_lazy("H:i")
try:
    res_lazy = formats.get_format(lazy_name)
except Exception as e:
    print("FAIL: get_format raised on lazy format_type:", type(e).__name__, e)
    raise SystemExit(1)

res_concrete = formats.get_format("H:i")
print("lazy result:", repr(res_lazy), "type:", type(res_lazy).__name__)
print("concrete result:", repr(res_concrete))

ok = True
if res_lazy != res_concrete:
    print("FAIL: lazy result != concrete result")
    ok = False
if isinstance(res_lazy, Promise):
    print("FAIL: lazy result is a deferred proxy, not a concrete value")
    ok = False
if not isinstance(res_lazy, str):
    print("FAIL: lazy result is not a str:", type(res_lazy))
    ok = False
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-15741: gold patch adds `format_type = str(format_type)` in get_format so lazy (gettext_lazy) format names resolve instead of raising TypeError in getattr().

Probes (all HOLD on patched tree):
- probe_1 (R1.1/R1.2/R2.6, POSITIVE CONTROL): get_format(gettext_lazy('H:i')) returns without TypeError, equals concrete-string result 'H:i', and is a concrete str (not a Promise). Patched: HOLDS. Base: VIOLATED (TypeError: getattr(): attribute name must be string). Discriminates.
- probe_2 (R1.3/R2.2): under override('en'), get_format(lazy('DATE_FORMAT')) == get_format('DATE_FORMAT') == 'N j, Y' (real localized value, not the name). HOLDS patched.
- probe_3 (R2.1/R2.3/R2.4): concrete-string behavior preserved — unknown name returned unchanged; DATE_FORMAT/DECIMAL_SEPARATOR with use_l10n=False fall back to settings values. HOLDS patched.
- probe_4 (R3.2/R3.3): date template filter {{ t|date:_('H:i') }} with t=time(0,0) renders '00:00', identical to concrete arg, fully-evaluated str (not a proxy, not empty). HOLDS patched.
- probe_5 (R3.1/R1.4): date_format/time_format accept lazy format args and match concrete output; text-equal names yield equal get_format results. HOLDS patched.

Candidate wrong-fix (weak.diff): coerces `format = str(format)` only inside date_format/time_format helpers, NOT in get_format. This is the lazy partial fix a weak reading of R3 permits (it fixes the date-filter path but not R1). REJECTED by the suite: probe_1 VIOLATED (direct get_format(lazy) still raises TypeError), probe_2 VIOLATED, probe_5 VIOLATED (time_format path with lazy still hits raw get_format? no — helpers coerce, but probe_5 also calls get_format(lazy) directly for R1.4 → raises). probes 3/4 HOLD under it. Because probe_1/2/5 reject it, the candidate does not conform to the probe suite → suite discriminates wrong implementations (not a TOO-WEAK finding).

Protocol satisfied: 5 distinct probes all hold patched; positive control fails at base and holds patched (prepatch reproduced); >=1 candidate exercised and REJECTED. No probe fails on the patched tree; no probe-conforming alternative found. Verdict SOUND.

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
"""Positive control / R1.1, R1.2, R2.6: get_format accepts a lazy format_type,
returns without TypeError, equals the concrete-string result, and returns a
concrete str (not a proxy). FAILS at base (TypeError in getattr)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, USE_L10N=True, USE_TZ=True,
                        INSTALLED_APPS=[], DATABASES={})
django.setup()

from django.utils import formats
from django.utils.translation import gettext_lazy
from django.utils.functional import Promise

lazy_name = gettext_lazy("H:i")
try:
    res_lazy = formats.get_format(lazy_name)
except Exception as e:
    print("FAIL: get_format raised on lazy format_type:", type(e).__name__, e)
    raise SystemExit(1)

res_concrete = formats.get_format("H:i")
print("lazy result:", repr(res_lazy), "type:", type(res_lazy).__name__)
print("concrete result:", repr(res_concrete))

ok = True
if res_lazy != res_concrete:
    print("FAIL: lazy result != concrete result")
    ok = False
if isinstance(res_lazy, Promise):
    print("FAIL: lazy result is a deferred proxy, not a concrete value")
    ok = False
if not isinstance(res_lazy, str):
    print("FAIL: lazy result is not a str:", type(res_lazy))
    ok = False
print("HOLDS" if ok else "VIOLATED")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-15741: gold patch adds `format_type = str(format_type)` in get_format so lazy (gettext_lazy) format names resolve instead of raising TypeError in getattr().

Probes (all HOLD on patched tree):
- probe_1 (R1.1/R1.2/R2.6, POSITIVE CONTROL): get_format(gettext_lazy('H:i')) returns without TypeError, equals concrete-string result 'H:i', and is a concrete str (not a Promise). Patched: HOLDS. Base: VIOLATED (TypeError: getattr(): attribute name must be string). Discriminates.
- probe_2 (R1.3/R2.2): under override('en'), get_format(lazy('DATE_FORMAT')) == get_format('DATE_FORMAT') == 'N j, Y' (real localized value, not the name). HOLDS patched.
- probe_3 (R2.1/R2.3/R2.4): concrete-string behavior preserved — unknown name returned unchanged; DATE_FORMAT/DECIMAL_SEPARATOR with use_l10n=False fall back to settings values. HOLDS patched.
- probe_4 (R3.2/R3.3): date template filter {{ t|date:_('H:i') }} with t=time(0,0) renders '00:00', identical to concrete arg, fully-evaluated str (not a proxy, not empty). HOLDS patched.
- probe_5 (R3.1/R1.4): date_format/time_format accept lazy format args and match concrete output; text-equal names yield equal get_format results. HOLDS patched.

Candidate wrong-fix (weak.diff): coerces `format = str(format)` only inside date_format/time_format helpers, NOT in get_format. This is the lazy partial fix a weak reading of R3 permits (it fixes the date-filter path but not R1). REJECTED by the suite: probe_1 VIOLATED (direct get_format(lazy) still raises TypeError), probe_2 VIOLATED, probe_5 VIOLATED (time_format path with lazy still hits raw get_format? no — helpers coerce, but probe_5 also calls get_format(lazy) directly for R1.4 → raises). probes 3/4 HOLD under it. Because probe_1/2/5 reject it, the candidate does not conform to the probe suite → suite discriminates wrong implementations (not a TOO-WEAK finding).

Protocol satisfied: 5 distinct probes all hold patched; positive control fails at base and holds patched (prepatch reproduced); >=1 candidate exercised and REJECTED. No probe fails on the patched tree; no probe-conforming alternative found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed both gold-patched (exit 0) and base (exit 1, TypeError as described in issue). Requirements model the changed observable behavior (get_format accepting a lazy format name and behaving as the forced-str equivalent) at the correct boundary, including the downstream date filter path. No invented, forbidden, or mis-bounded behavior detected.

Counterexample / evidence:

```
N/A — patched behavior confirmed by probe (gold: lazy=='N j, Y'==concrete, type str, unknown name passthrough; base: TypeError).
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Hidden tests: test_get_format_lazy_format (get_format(gettext_lazy("DATE_FORMAT")) == "N j, Y") and test_date_lazy ({{ t|date:_("H:i") }} with time(0,0) -> "00:00"). The requirements.md describes behavior only. Module/function localization (get_format, date_format/time_format, django.template.defaultfilters date filter, gettext_lazy, the TypeError, the Y-m-d example) are all present in the PUBLIC problem_statement and are legitimate. No test names/paths/ids, no parametrization ids, no quoted test or gold code, no fix-invented identifiers. The gold one-liner (format_type = str(format_type)) is rendered as a behavioral requirement ('treat the format name purely by its concrete text content'), not transmitted. The hidden-test constants are NOT leaked: "N j, Y" and "00:00" and time(0,0) appear nowhere. The only borderline token is Requirement 3.2's illustrative _("H:i"), which does match test_date_lazy's format string but not the problem_statement's Y-m-d; however it is a single common example presented as 'for example', omits the test's input/expected-output, and does not reconstruct the hidden test (no case enumeration mirroring parametrization). It reads as behavioral illustration, not test transmission. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
