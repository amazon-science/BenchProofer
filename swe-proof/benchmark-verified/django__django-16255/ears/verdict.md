# P2 adversarial audit — django__django-16255

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_empty_callable.py`, `probe_2_nonempty_max.py`, `probe_3_noncallable.py`, `probe_4_typeerror.py`, `probe_5_index_view.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_empty_callable.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_empty_callable.py` → holds on the patched tree (good)

```python
# Req 1.1 & 1.2 (POSITIVE CONTROL): callable lastmod + empty items()
# -> returns None sentinel, no exception. Must HOLD patched, FAIL at base.
import datetime
from django.contrib.sitemaps import Sitemap

class EmptySitemap(Sitemap):
    def items(self):
        return []
    def lastmod(self, item):
        return datetime.datetime(2020, 1, 1)

s = EmptySitemap()
assert callable(s.lastmod), "lastmod must be callable in this scenario"
try:
    r = s.get_latest_lastmod()
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)
print("returned:", repr(r))
if r is None:
    raise SystemExit(0)
print("expected None sentinel, got", repr(r))
raise SystemExit(1)
```

Attack 2 — `probe_2_nonempty_max.py` → holds on the patched tree (good)

```python
# Req 2.1: callable lastmod + non-empty items -> returns the greatest timestamp.
import datetime
from django.contrib.sitemaps import Sitemap

DATES = {
    "a": datetime.datetime(2019, 5, 1),
    "b": datetime.datetime(2021, 12, 31),  # max
    "c": datetime.datetime(2020, 1, 1),
}

class PopSitemap(Sitemap):
    def items(self):
        return ["a", "b", "c"]
    def lastmod(self, item):
        return DATES[item]

r = PopSitemap().get_latest_lastmod()
print("returned:", repr(r))
if r == datetime.datetime(2021, 12, 31):
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 3 — `probe_3_noncallable.py` → holds on the patched tree (good)

```python
# Req 2.2 & 2.3: non-callable lastmod returned unchanged; no lastmod attr -> None.
import datetime
from django.contrib.sitemaps import Sitemap

class FixedSitemap(Sitemap):
    lastmod = datetime.datetime(2022, 6, 15)
    def items(self):
        return [1, 2, 3]

r = FixedSitemap().get_latest_lastmod()
print("fixed lastmod returned:", repr(r))
ok1 = (r == datetime.datetime(2022, 6, 15))

# no lastmod attr at all -> base Sitemap.lastmod is None (non-callable) -> None
class NoLastmod(Sitemap):
    def items(self):
        return [1, 2, 3]

r2 = NoLastmod().get_latest_lastmod()
print("no-lastmod returned:", repr(r2))
ok2 = (r2 is None)

# non-callable None value explicitly
class NoneLastmod(Sitemap):
    lastmod = None
    def items(self):
        return [1]
r3 = NoneLastmod().get_latest_lastmod()
print("None-value lastmod returned:", repr(r3))
ok3 = (r3 is None)

raise SystemExit(0 if (ok1 and ok2 and ok3) else 1)
```

Attack 4 — `probe_4_typeerror.py` → holds on the patched tree (good)

```python
# Req 2.4: callable lastmod producing mutually-incomparable values (TypeError
# during max) -> get_latest_lastmod returns None, does not raise.
import datetime
from django.contrib.sitemaps import Sitemap

class MixedSitemap(Sitemap):
    def items(self):
        return ["dt", "int"]
    def lastmod(self, item):
        # datetime vs int are not comparable in py3 -> TypeError inside max()
        return datetime.datetime(2020, 1, 1) if item == "dt" else 5

s = MixedSitemap()
try:
    r = s.get_latest_lastmod()
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)
print("returned:", repr(r))
raise SystemExit(0 if r is None else 1)
```

Attack 5 — `probe_5_index_view.py` → holds on the patched tree (good)

```python
# Req 1.3 & 1.4 & 2.5: sitemap index view with an empty callable-lastmod
# section renders a well-formed index that lists the <loc>, omits Last-Modified;
# and with a populated section sets Last-Modified to the greatest timestamp.
import datetime

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        ALLOWED_HOSTS=["*"],
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django.contrib.sitemaps",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "DIRS": [],
            "OPTIONS": {},
        }],
        ROOT_URLCONF=__name__,
    )
django.setup()

from django.contrib.sitemaps import Sitemap, views
from django.test import RequestFactory
from django.urls import path

urlpatterns = [
    path("sitemap-<section>.xml", views.sitemap, {"sitemaps": {}},
         name="django.contrib.sitemaps.views.sitemap"),
]

class EmptyCallable(Sitemap):
    location = "/location/"
    def items(self):
        return []
    def lastmod(self, obj):
        return obj.lastmod

class Populated(Sitemap):
    location = "/location/"
    def items(self):
        return [type("O", (), {"lastmod": datetime.datetime(2021, 3, 4)})()]
    def lastmod(self, obj):
        return obj.lastmod

rf = RequestFactory()

# --- empty section: must render, list loc, omit Last-Modified ---
req = rf.get("/callable-lastmod-no-items/index.xml")
req.META["SERVER_NAME"] = "example.com"
req.META["SERVER_PORT"] = "80"
resp = views.index(req, {"callable-lastmod": EmptyCallable})
resp.render()
body = resp.content.decode()
print("EMPTY index status:", resp.status_code)
print("EMPTY has Last-Modified:", "Last-Modified" in resp)
print("EMPTY body:", body)
ok_render = resp.status_code == 200
ok_loc = "<loc>" in body and "sitemap-callable-lastmod.xml" in body
ok_no_lm = "Last-Modified" not in resp
ok_wellformed = "<sitemapindex" in body and "</sitemapindex>" in body

# --- populated section: Last-Modified present, == greatest timestamp ---
req2 = rf.get("/p/index.xml")
req2.META["SERVER_NAME"] = "example.com"
req2.META["SERVER_PORT"] = "80"
resp2 = views.index(req2, {"callable-lastmod": Populated})
resp2.render()
from django.utils.http import http_date
expected = http_date(datetime.datetime(2021, 3, 4).timestamp())
print("POP has Last-Modified:", "Last-Modified" in resp2, resp2.get("Last-Modified"))
ok_pop = ("Last-Modified" in resp2) and (resp2["Last-Modified"] == expected)

allok = ok_render and ok_loc and ok_no_lm and ok_wellformed and ok_pop
print("checks:", dict(render=ok_render, loc=ok_loc, no_lm=ok_no_lm,
                      wellformed=ok_wellformed, pop=ok_pop))
raise SystemExit(0 if allok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_empty_callable.py`

```python
# Req 1.1 & 1.2 (POSITIVE CONTROL): callable lastmod + empty items()
# -> returns None sentinel, no exception. Must HOLD patched, FAIL at base.
import datetime
from django.contrib.sitemaps import Sitemap

class EmptySitemap(Sitemap):
    def items(self):
        return []
    def lastmod(self, item):
        return datetime.datetime(2020, 1, 1)

s = EmptySitemap()
assert callable(s.lastmod), "lastmod must be callable in this scenario"
try:
    r = s.get_latest_lastmod()
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)
print("returned:", repr(r))
if r is None:
    raise SystemExit(0)
print("expected None sentinel, got", repr(r))
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16255: get_latest_lastmod() must return None (not raise ValueError) when lastmod is callable and items() is empty. Gold patch adds default=None to max().

Probe suite (all HOLD on gold-patched tree; run in official Docker image via nl_attack):
- probe_1_empty_callable (Req 1.1/1.2, POSITIVE CONTROL): callable lastmod + empty items -> returns None, no exception. HOLDS patched; FAILS at base with 'ValueError: max() arg is an empty sequence'. Discriminates.
- probe_2_nonempty_max (Req 2.1): callable lastmod + non-empty items -> greatest timestamp (2021-12-31). HOLDS.
- probe_3_noncallable (Req 2.2/2.3): non-callable lastmod returned unchanged; missing lastmod attr -> None; lastmod=None -> None. HOLDS.
- probe_4_typeerror (Req 2.4): callable lastmod yielding mutually-incomparable values (datetime vs int) -> None via TypeError branch, no raise. HOLDS.
- probe_5_index_view (Req 1.3/1.4/2.5): index() view with empty callable-lastmod section renders 200, lists <loc>, well-formed <sitemapindex>, omits Last-Modified; populated section sets Last-Modified to greatest timestamp. HOLDS.

Candidate wrong-fix (weak_partial.diff): guards the empty-items case (if not items: return None; else max(items)) but DROPS the try/except TypeError. A lazy reading of Req 1 permits this. It is REJECTED by probe_4 ('TypeError: >' not supported between int and datetime) while passing probes 1,2,3,5 — proving the suite discriminates a plausibly-wrong partial fix that would regress the pre-existing TypeError-tolerance (Req 2.4).

All needed runs completed cleanly in-container. >=5 probes hold patched, positive control discriminates (fails base / holds patched), and >=1 candidate is exercised and rejected. No requirements VIOLATION found and no requirements-conforming patch that fails to resolve was found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_empty_callable.py`, `probe_2_nonempty_max.py`, `probe_3_noncallable.py`, `probe_4_typeerror.py`, `probe_5_index_view.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_empty_callable.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_empty_callable.py` → holds on the patched tree (good)

Attack 2 — `probe_2_nonempty_max.py` → holds on the patched tree (good)

Attack 3 — `probe_3_noncallable.py` → holds on the patched tree (good)

Attack 4 — `probe_4_typeerror.py` → holds on the patched tree (good)

Attack 5 — `probe_5_index_view.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_empty_callable.py`

```python
# Req 1.1 & 1.2 (POSITIVE CONTROL): callable lastmod + empty items()
# -> returns None sentinel, no exception. Must HOLD patched, FAIL at base.
import datetime
from django.contrib.sitemaps import Sitemap

class EmptySitemap(Sitemap):
    def items(self):
        return []
    def lastmod(self, item):
        return datetime.datetime(2020, 1, 1)

s = EmptySitemap()
assert callable(s.lastmod), "lastmod must be callable in this scenario"
try:
    r = s.get_latest_lastmod()
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)
print("returned:", repr(r))
if r is None:
    raise SystemExit(0)
print("expected None sentinel, got", repr(r))
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16255: get_latest_lastmod() must return None (not raise ValueError) when lastmod is callable and items() is empty. Gold patch adds default=None to max().

Probe suite (all HOLD on gold-patched tree; run in official Docker image via nl_attack):
- probe_1_empty_callable (Req 1.1/1.2, POSITIVE CONTROL): callable lastmod + empty items -> returns None, no exception. HOLDS patched; FAILS at base with 'ValueError: max() arg is an empty sequence'. Discriminates.
- probe_2_nonempty_max (Req 2.1): callable lastmod + non-empty items -> greatest timestamp (2021-12-31). HOLDS.
- probe_3_noncallable (Req 2.2/2.3): non-callable lastmod returned unchanged; missing lastmod attr -> None; lastmod=None -> None. HOLDS.
- probe_4_typeerror (Req 2.4): callable lastmod yielding mutually-incomparable values (datetime vs int) -> None via TypeError branch, no raise. HOLDS.
- probe_5_index_view (Req 1.3/1.4/2.5): index() view with empty callable-lastmod section renders 200, lists <loc>, well-formed <sitemapindex>, omits Last-Modified; populated section sets Last-Modified to greatest timestamp. HOLDS.

Candidate wrong-fix (weak_partial.diff): guards the empty-items case (if not items: return None; else max(items)) but DROPS the try/except TypeError. A lazy reading of Req 1 permits this. It is REJECTED by probe_4 ('TypeError: >' not supported between int and datetime) while passing probes 1,2,3,5 — proving the suite discriminates a plausibly-wrong partial fix that would regress the pre-existing TypeError-tolerance (Req 2.4).

All needed runs completed cleanly in-container. >=5 probes hold patched, positive control discriminates (fails base / holds patched), and >=1 candidate is exercised and rejected. No requirements VIOLATION found and no requirements-conforming patch that fails to resolve was found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a one-line change: max([...]) -> max([...], default=None) in Sitemap.get_latest_lastmod(). The requirements correctly model the changed observable behavior (get_latest_lastmod return contract) at the right boundary rather than a narrow slice, and correctly treat views.index() as the pre-existing consumer whose Last-Modified header omission is preserved. Requirement 2.4 (TypeError->None) is genuinely preserved by the untouched except TypeError branch. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior only. No hidden-test identifiers leak: the test name (test_callable_sitemod_no_items), fixture class (CallableLastmodNoItemsSitemap), URL path (/callable-lastmod-no-items/index.xml), and test file path do not appear. Every technical detail present (get_latest_lastmod, callable lastmod, empty items, ValueError, TypeError->None, None sentinel, Last-Modified header omission) is already disclosed in the PUBLIC problem_statement, which quotes the full traceback and a candidate diff. The gold fix's specific mechanism (max([...], default=None)) is not reconstructed — requirements describe the outcome ('return None sentinel rather than raise'), which is behavioral. Module/function localization is legitimate. Requirement 2's preserved-behavior cases are general regression descriptions, not a mirror of the single FAIL_TO_PASS parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
