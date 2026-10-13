# P2 adversarial audit — django__django-11477

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_omit_absent.py`, `probe_2_present_kept.py`, `probe_3_positional_fallback.py`, `probe_4_named_suppresses_positional.py`, `probe_5_regression.py`, `probe_6_translate_url.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_omit_absent.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak_a candidate patch: kwargs={k:v for ... if v is not None} (filters None, satisfies Req 1/4) BUT keeps `args = () if match.groupdict() else match.groups()` — i.e. the positional-fallback decision keyed on the RAW groupdict. For pattern r'^(\w+)/(?:(?P<opt>\w+)/)?$' on 'pos/', gold returns kwargs={}, args=('pos', None); weak_a returns kwargs={}, args=() — dropping the positional captures. This is exactly the second defect in the requirements intro (Req 2.3). probe_3 REJECTS it.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_omit_absent.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2 (POSITIVE CONTROL): absent optional named group must be omitted from kwargs.
import re
from django.urls.resolvers import RegexPattern
p = RegexPattern(r'^(?:(?P<opt>\w+)/)?required/(?P<req>\w+)/$')
path, args, kwargs = p.match('required/foo/')
print("kwargs:", kwargs, "args:", args, "leftover:", repr(path))
assert 'opt' not in kwargs, "absent optional group leaked into kwargs"
assert kwargs == {'req': 'foo'}, kwargs
print("OK: absent optional omitted")
```

Attack 2 — `probe_2_present_kept.py` → holds on the patched tree (good)

```python
# Req 1.3 / 3.3: present optional named group must appear mapped to its captured text.
from django.urls.resolvers import RegexPattern
p = RegexPattern(r'^(?:(?P<opt>\w+)/)?required/(?P<req>\w+)/$')
path, args, kwargs = p.match('bar/required/foo/')
print("kwargs:", kwargs, "args:", args)
assert kwargs == {'opt': 'bar', 'req': 'foo'}, kwargs
assert args == (), args
print("OK: present captures kept")
```

Attack 3 — `probe_3_positional_fallback.py` → holds on the patched tree (good)

```python
# Req 2.2/2.3: when all named groups are optional and absent, kwargs must be EMPTY
# and positional-argument tuple must be the pattern's positional captures (match.groups()).
import re
from django.urls.resolvers import RegexPattern
rx = r'^(\w+)/(?:(?P<opt>\w+)/)?$'
p = RegexPattern(rx)
path, args, kwargs = p.match('pos/')
print("kwargs:", kwargs, "args:", args)
assert kwargs == {}, ("expected empty kwargs (no named capture survived), got %r" % (kwargs,))
expected = re.search(rx, 'pos/').groups()
print("match.groups():", expected)
assert args == expected, ("args must equal match.groups()=%r, got %r" % (expected, args))
assert args, "positional captures must be exposed (non-empty)"
print("OK: empty kwargs + positional captures exposed")
```

Attack 4 — `probe_4_named_suppresses_positional.py` → holds on the patched tree (good)

```python
# Req 2.1: when a named capture survives, kwargs returned and args empty even if positional groups exist.
from django.urls.resolvers import RegexPattern
p = RegexPattern(r'^(\w+)/(?P<opt>\w+)/$')
path, args, kwargs = p.match('pos/named/')
print("kwargs:", kwargs, "args:", args)
assert kwargs == {'opt': 'named'}, kwargs
assert args == (), args
print("OK: surviving named capture suppresses positional")
```

Attack 5 — `probe_5_regression.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2: leftover path preserved; no-match returns None.
from django.urls.resolvers import RegexPattern
p = RegexPattern(r'^prefix/(?P<req>\w+)/')  # not anchored at end -> leftover
res = p.match('prefix/abc/tail/rest')
print("result:", res)
path, args, kwargs = res
assert path == 'tail/rest', repr(path)
assert kwargs == {'req': 'abc'}, kwargs
# no-match
assert p.match('nomatch') is None, "expected None on no-match"
print("OK: leftover preserved and no-match None")
```

Attack 6 — `probe_6_translate_url.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2: translate_url must not emit literal "None" for absent optional named group.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_I18N=True,
        SECRET_KEY='x',
        ROOT_URLCONF='urlconf_mod',
        LANGUAGE_CODE='en',
        LANGUAGES=[('en','English'),('nl','Dutch')],
        MIDDLEWARE=[],
        DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],
    )
django.setup()
import sys, types
from django.urls import re_path, path
from django.utils.translation import gettext_lazy as _

def view(request, *a, **k):
    return None

mod = types.ModuleType('urlconf_mod')
# optional named group 'sub'
mod.urlpatterns = [
    re_path(r'^(?:(?P<sub>[a-z]+)/)?page/$', view, name='pg'),
]
sys.modules['urlconf_mod'] = mod

from django.urls.base import translate_url
from django.utils.translation import override

with override('en'):
    out = translate_url('/page/', 'nl')
print("translate_url('/page/','nl') ->", out)
assert 'None' not in out, "literal None leaked into translated URL"
assert out == '/page/', out
print("OK: no None in translated URL for absent optional group")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_omit_absent.py`

```python
# Req 1.1/1.2 (POSITIVE CONTROL): absent optional named group must be omitted from kwargs.
import re
from django.urls.resolvers import RegexPattern
p = RegexPattern(r'^(?:(?P<opt>\w+)/)?required/(?P<req>\w+)/$')
path, args, kwargs = p.match('required/foo/')
print("kwargs:", kwargs, "args:", args, "leftover:", repr(path))
assert 'opt' not in kwargs, "absent optional group leaked into kwargs"
assert kwargs == {'req': 'foo'}, kwargs
print("OK: absent optional omitted")
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: kwargs = {k:v for k,v in groupdict().items() if v is not None}; args = () if kwargs else match.groups(). All 6 probes HOLD on gold-patched tree. Positive control probe_1 (Req 1.1/1.2, absent optional omitted): HOLD patched / FAIL base (AssertionError 'opt' leaked). Probe results — probe_1 (Req1.1/1.2): patched HOLD, base VIOLATED. probe_2 (Req1.3/3.3 present kept): patched HOLD, base HOLD (regression). probe_3 (Req2.2/2.3 positional fallback = match.groups()): patched HOLD, base VIOLATED (kwargs={'opt':None}), weak_a REJECTED. probe_4 (Req2.1 named suppresses positional): patched HOLD. probe_5 (Req3.1/3.2 leftover path + no-match None): patched HOLD. probe_6 (Req4.1/4.2 translate_url no literal None): patched HOLD (translate_url('/page/','nl')->'/page/'). weak_a candidate: probes 1,2,4,5,6 HOLD, probe_3 REJECTS -> suite discriminates the wrong-fix; not a too-weak finding. All infra runs completed (no timeouts/apply failures on final patch). Verdict SOUND: >=5 probes hold on patched tree, positive control discriminates base vs patched, and >=1 candidate patch exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_omit_absent.py`, `probe_2_present_kept.py`, `probe_3_positional_fallback.py`, `probe_4_named_suppresses_positional.py`, `probe_5_regression.py`, `probe_6_translate_url.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_omit_absent.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak_a candidate patch: kwargs={k:v for ... if v is not None} (filters None, satisfies Req 1/4) BUT keeps `args = () if match.groupdict() else match.groups()` — i.e. the positional-fallback decision keyed on the RAW groupdict. For pattern r'^(\w+)/(?:(?P<opt>\w+)/)?$' on 'pos/', gold returns kwargs={}, args=('pos', None); weak_a returns kwargs={}, args=() — dropping the positional captures. This is exactly the second defect in the requirements intro (Req 2.3). probe_3 REJECTS it.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_omit_absent.py` → holds on the patched tree (good)

Attack 2 — `probe_2_present_kept.py` → holds on the patched tree (good)

Attack 3 — `probe_3_positional_fallback.py` → holds on the patched tree (good)

Attack 4 — `probe_4_named_suppresses_positional.py` → holds on the patched tree (good)

Attack 5 — `probe_5_regression.py` → holds on the patched tree (good)

Attack 6 — `probe_6_translate_url.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_omit_absent.py`

```python
# Req 1.1/1.2 (POSITIVE CONTROL): absent optional named group must be omitted from kwargs.
import re
from django.urls.resolvers import RegexPattern
p = RegexPattern(r'^(?:(?P<opt>\w+)/)?required/(?P<req>\w+)/$')
path, args, kwargs = p.match('required/foo/')
print("kwargs:", kwargs, "args:", args, "leftover:", repr(path))
assert 'opt' not in kwargs, "absent optional group leaked into kwargs"
assert kwargs == {'req': 'foo'}, kwargs
print("OK: absent optional omitted")
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: kwargs = {k:v for k,v in groupdict().items() if v is not None}; args = () if kwargs else match.groups(). All 6 probes HOLD on gold-patched tree. Positive control probe_1 (Req 1.1/1.2, absent optional omitted): HOLD patched / FAIL base (AssertionError 'opt' leaked). Probe results — probe_1 (Req1.1/1.2): patched HOLD, base VIOLATED. probe_2 (Req1.3/3.3 present kept): patched HOLD, base HOLD (regression). probe_3 (Req2.2/2.3 positional fallback = match.groups()): patched HOLD, base VIOLATED (kwargs={'opt':None}), weak_a REJECTED. probe_4 (Req2.1 named suppresses positional): patched HOLD. probe_5 (Req3.1/3.2 leftover path + no-match None): patched HOLD. probe_6 (Req4.1/4.2 translate_url no literal None): patched HOLD (translate_url('/page/','nl')->'/page/'). weak_a candidate: probes 1,2,4,5,6 HOLD, probe_3 REJECTS -> suite discriminates the wrong-fix; not a too-weak finding. All infra runs completed (no timeouts/apply failures on final patch). Verdict SOUND: >=5 probes hold on patched tree, positive control discriminates base vs patched, and >=1 candidate patch exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary check: the requirements pin the actual changed observable — the kwargs mapping excludes None-valued named groups and the args/kwargs choice depends on surviving named captures, not raw groupdict non-emptiness (R2.3), exactly matching the diff. R2.2's wording 'pattern's positional captures' correctly denotes match.groups() (verified args == ('foo', None), not a filtered tuple), avoiding an over-tight claim. Base probe confirms the pre-patch bug (opt:None present). No mandated behavior absent from code, no forbidden behavior present, no invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the None-filtering behavior (gold: kwargs comprehension dropping None) and the positional-vs-kwargs fallback (gold: args = () if kwargs else match.groups()) as behavioral requirements — the intended translation of test-checked behavior, not transmission of the tests. No hidden-test artifacts appear: no test names (test_re_path_with_optional_parameter, test_translate_url_utility, named_optional_terminated), no test file paths, no fix/test-invented identifiers (arg1/arg2, regex_optional, with-arguments, the .html optional segment), no specific parametrized URLs (/regex_optional/1/2/, /optional/1/), and no quoted test or gold code. Module/function localization (RegexPattern.match, resolvers.py, base.py, resolve/reverse/translate_url) is legitimate; translate_url + missing optional named groups is public via problem_statement. Req 1.4's 'one required + one optional group' is the minimal defining case of the fix, not a mirror of the test's concrete ids/URLs.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
