# P2 adversarial audit — django__django-13297

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_db.py`, `probe_strmethods.py`, `probe_resolve_equal.py`, `probe_warning.py`, `probe_deferred_noeager.py`, `probe_keys_order.py`, `probe_int_arith.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_db.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_db.py` → holds on the patched tree (good)

```python
"""POSITIVE CONTROL / R1.3: a wrapped URL string kwarg used directly as a DB
query filter value SHALL be accepted as its underlying type without manual
coercion. We mimic the ORM query path: CharField prepares the value for the DB
(get_prep_value / get_db_prep_value), then it is bound as a sqlite parameter.

At BASE the wrapper is a SimpleLazyObject: get_prep_value returns the
SimpleLazyObject unchanged (isinstance str is True), and the sqlite backend
rejects it ("Error binding parameter - unsupported type"). On the PATCHED tree
the wrapper delegates str, get_prep_value coerces to a real str, and binding
succeeds. Must HOLD patched, FAIL at base."""
import warnings
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[])
django.setup()

from django.db import connection
from django.db.models import CharField
from django.views.generic.base import _wrap_url_kwargs_with_deprecation_warning

w = _wrap_url_kwargs_with_deprecation_warning({'slug': 'my-slug'})['slug']

field = CharField(max_length=64)
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    # exactly what the ORM does to turn a lookup RHS into a DB parameter
    prepared = field.get_db_prep_value(w, connection, prepared=False)

print("prepared value:", repr(prepared), "type:", type(prepared).__name__)

with connection.cursor() as cur:
    cur.execute("CREATE TABLE t (slug varchar(64))")
    cur.execute("INSERT INTO t (slug) VALUES ('my-slug')")
    # bind the ORM-prepared value as a real query parameter
    cur.execute("SELECT slug FROM t WHERE slug = %s", [prepared])
    row = cur.fetchone()

print("query result:", row)
assert row is not None and row[0] == 'my-slug', row
print("DB filter accepted the wrapped URL kwarg without manual coercion: OK")
```

Attack 2 — `probe_strmethods.py` → holds on the patched tree (good)

```python
"""R1.1/R1.2/R4.3: the wrapper delegates the underlying str's methods,
operators, and text conversion; each behaves as on the real value."""
import warnings
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[])
django.setup()

from django.views.generic.base import _wrap_url_kwargs_with_deprecation_warning

val = 'Hello-World'
w = _wrap_url_kwargs_with_deprecation_warning({'k': val})['k']

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    checks = {
        'upper': w.upper() == val.upper(),
        'startswith': w.startswith('Hello') == True,
        'replace': w.replace('-', '_') == 'Hello_World',
        'concat': (w + '!') == 'Hello-World!',
        'index': w[0] == 'H',
        'len': len(w) == len(val),
        'str': str(w) == val,
    }
print(checks)
assert all(checks.values()), checks
print("str method/operator/conversion delegation: OK")
```

Attack 3 — `probe_resolve_equal.py` → holds on the patched tree (good)

```python
"""R1.4/R4.3: resolving through the wrapper yields exactly the original value
(equal, same text form), nothing added or dropped."""
import warnings
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[])
django.setup()

from django.views.generic.base import _wrap_url_kwargs_with_deprecation_warning

for val in ['abc', 'my-slug', '']:
    w = _wrap_url_kwargs_with_deprecation_warning({'k': val})['k']
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        assert w == val, (repr(w), repr(val))
        assert str(w) == val
print("resolved value equals original: OK")
```

Attack 4 — `probe_warning.py` → holds on the patched tree (good)

```python
"""R2.2/R3.4: first consumption emits a RemovedInDjango40Warning whose message
names the argument and points to view.kwargs. R2.4: suppressed warnings still
resolve correctly."""
import warnings
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[])
django.setup()

from django.utils.deprecation import RemovedInDjango40Warning
from django.views.generic.base import _wrap_url_kwargs_with_deprecation_warning

wrapped = _wrap_url_kwargs_with_deprecation_warning({'artist_name': 'bowie'})
w = wrapped['artist_name']

with warnings.catch_warnings(record=True) as rec:
    warnings.simplefilter('always')
    _ = w.upper()  # first consumption

msgs = [x for x in rec if issubclass(x.category, RemovedInDjango40Warning)]
assert msgs, "no RemovedInDjango40Warning emitted on consumption"
text = str(msgs[0].message)
print("warning:", text)
assert 'artist_name' in text, "warning does not name the argument"
assert 'view.kwargs' in text, "warning does not point to view.kwargs"

# R2.4: suppressed -> still resolves
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    w2 = _wrap_url_kwargs_with_deprecation_warning({'k': 'val'})['k']
    assert str(w2) == 'val'
print("named one-time deprecation + suppressed-still-resolves: OK")
```

Attack 5 — `probe_deferred_noeager.py` → holds on the patched tree (good)

```python
"""R2.1/R2.3: wrapping is deferred — building the wrappers emits NO warning;
only consumption does. Never-consumed wrappers emit no notice."""
import warnings
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[])
django.setup()

from django.utils.deprecation import RemovedInDjango40Warning
from django.views.generic.base import _wrap_url_kwargs_with_deprecation_warning

with warnings.catch_warnings(record=True) as rec:
    warnings.simplefilter('always')
    wrapped = _wrap_url_kwargs_with_deprecation_warning({'a': 'x', 'b': 'y'})
    # do NOT consume any wrapper
dep = [x for x in rec if issubclass(x.category, RemovedInDjango40Warning)]
print("warnings before consumption:", len(dep))
assert len(dep) == 0, "deprecation emitted eagerly / without consumption"
print("no eager resolution, no warning until consumed: OK")
```

Attack 6 — `probe_keys_order.py` → holds on the patched tree (good)

```python
"""R3.1/R3.2/R3.3: one wrapper per captured kwarg, same key set, order
preserved. R3.4: each wrapper's notice keyed to its own name."""
import warnings
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[])
django.setup()

from django.utils.deprecation import RemovedInDjango40Warning
from django.views.generic.base import _wrap_url_kwargs_with_deprecation_warning

src = {'first': 'A', 'second': 'B', 'third': 'C'}
wrapped = _wrap_url_kwargs_with_deprecation_warning(src)
assert list(wrapped.keys()) == list(src.keys()), (list(wrapped.keys()), list(src.keys()))
print("keys/order:", list(wrapped.keys()))

# each wrapper keyed to its own name
for name, expected in src.items():
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter('always')
        assert str(wrapped[name]) == expected
    dep = [x for x in rec if issubclass(x.category, RemovedInDjango40Warning)]
    assert dep, f"no warning for {name}"
    assert name in str(dep[0].message), f"warning for {name} not keyed to it: {dep[0].message}"
print("per-key wrapper, order, name-keyed notice: OK")
```

Attack 7 — `probe_int_arith.py` → holds on the patched tree (good)

```python
"""R1.1/R1.2/R4.4: the wrapper delegates the underlying value's OWN type
interface (not a hardcoded one). For an int URL kwarg, arithmetic operators and
int() conversion SHALL behave as on the real int. Gold uses type(value), so an
int value yields an int-delegating proxy. A fix that hardcodes `str` would not
expose int arithmetic and is rejected here."""
import warnings
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[])
django.setup()

from django.views.generic.base import _wrap_url_kwargs_with_deprecation_warning

w = _wrap_url_kwargs_with_deprecation_warning({'pk': 41})['pk']
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    checks = {
        'add': (w + 1) == 42,
        'mul': (w * 2) == 82,
        'int': int(w) == 41,
        'eq': w == 41,
        'lt': (w < 100) == True,
    }
print(checks)
assert all(checks.values()), checks
print("int arithmetic/operator delegation via underlying type: OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_db.py`

```python
"""POSITIVE CONTROL / R1.3: a wrapped URL string kwarg used directly as a DB
query filter value SHALL be accepted as its underlying type without manual
coercion. We mimic the ORM query path: CharField prepares the value for the DB
(get_prep_value / get_db_prep_value), then it is bound as a sqlite parameter.

At BASE the wrapper is a SimpleLazyObject: get_prep_value returns the
SimpleLazyObject unchanged (isinstance str is True), and the sqlite backend
rejects it ("Error binding parameter - unsupported type"). On the PATCHED tree
the wrapper delegates str, get_prep_value coerces to a real str, and binding
succeeds. Must HOLD patched, FAIL at base."""
import warnings
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[])
django.setup()

from django.db import connection
from django.db.models import CharField
from django.views.generic.base import _wrap_url_kwargs_with_deprecation_warning

w = _wrap_url_kwargs_with_deprecation_warning({'slug': 'my-slug'})['slug']

field = CharField(max_length=64)
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    # exactly what the ORM does to turn a lookup RHS into a DB parameter
    prepared = field.get_db_prep_value(w, connection, prepared=False)

print("prepared value:", repr(prepared), "type:", type(prepared).__name__)

with connection.cursor() as cur:
    cur.execute("CREATE TABLE t (slug varchar(64))")
    cur.execute("INSERT INTO t (slug) VALUES ('my-slug')")
    # bind the ORM-prepared value as a real query parameter
    cur.execute("SELECT slug FROM t WHERE slug = %s", [prepared])
    row = cur.fetchone()

print("query result:", row)
assert row is not None and row[0] == 'my-slug', row
print("DB filter accepted the wrapped URL kwarg without manual coercion: OK")
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover all 4 requirements and hold on the gold-patched tree. Positive control (probe_db, R1.3): mimics the ORM query path (CharField.get_db_prep_value then sqlite parameter binding) for a wrapped URL string kwarg — HOLDS patched (get_prep_value yields a real str, binds cleanly) and VIOLATED at base (SimpleLazyObject binding raises sqlite3.InterfaceError 'unsupported type'), so it discriminates base vs patched. Note: binding the raw wrapper directly (without the ORM get_prep_value coercion) fails on BOTH trees because the patched __proxy__ is not type-identity str (consistent with the G-PANEL-2 observation); the requirement is method delegation, and the ORM prep path exercises exactly the R1.3 DB-filter behavior the gold fix restores.

Coverage: probe_db=R1.3; probe_strmethods=R1.1/R1.2/R4.3 (str methods/operators/str()); probe_resolve_equal=R1.4/R4.3; probe_warning=R2.2/R2.4/R3.4 (named RemovedInDjango40Warning + view.kwargs, suppressed-still-resolves); probe_deferred_noeager=R2.1/R2.3 (no eager warning, none until consumed); probe_keys_order=R3.1/R3.2/R3.3 (per-key wrapper, key set, order, name-keyed notice); probe_int_arith=R1.1/R1.2/R4.4 (delegates the underlying value's OWN type via type(value), not a hardcoded str — int arithmetic works). Candidate wrong-fix patches, BOTH rejected by the suite:

(1) weak_strcoerce places the raw value into the context (no deferral) — REJECTED by probe_warning and probe_keys_order (no deprecation notice emitted);

(2) weak_lazy_str uses lazy(access_value, str) hardcoding str instead of type(value) — passes all string/warning probes but REJECTED by probe_int_arith (int kwarg loses arithmetic delegation). Suite discriminates both plausible weak readings; no too-weak candidate survives. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_db.py`, `probe_strmethods.py`, `probe_resolve_equal.py`, `probe_warning.py`, `probe_deferred_noeager.py`, `probe_keys_order.py`, `probe_int_arith.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_db.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_db.py` → holds on the patched tree (good)

Attack 2 — `probe_strmethods.py` → holds on the patched tree (good)

Attack 3 — `probe_resolve_equal.py` → holds on the patched tree (good)

Attack 4 — `probe_warning.py` → holds on the patched tree (good)

Attack 5 — `probe_deferred_noeager.py` → holds on the patched tree (good)

Attack 6 — `probe_keys_order.py` → holds on the patched tree (good)

Attack 7 — `probe_int_arith.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_db.py`

```python
"""POSITIVE CONTROL / R1.3: a wrapped URL string kwarg used directly as a DB
query filter value SHALL be accepted as its underlying type without manual
coercion. We mimic the ORM query path: CharField prepares the value for the DB
(get_prep_value / get_db_prep_value), then it is bound as a sqlite parameter.

At BASE the wrapper is a SimpleLazyObject: get_prep_value returns the
SimpleLazyObject unchanged (isinstance str is True), and the sqlite backend
rejects it ("Error binding parameter - unsupported type"). On the PATCHED tree
the wrapper delegates str, get_prep_value coerces to a real str, and binding
succeeds. Must HOLD patched, FAIL at base."""
import warnings
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[])
django.setup()

from django.db import connection
from django.db.models import CharField
from django.views.generic.base import _wrap_url_kwargs_with_deprecation_warning

w = _wrap_url_kwargs_with_deprecation_warning({'slug': 'my-slug'})['slug']

field = CharField(max_length=64)
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    # exactly what the ORM does to turn a lookup RHS into a DB parameter
    prepared = field.get_db_prep_value(w, connection, prepared=False)

print("prepared value:", repr(prepared), "type:", type(prepared).__name__)

with connection.cursor() as cur:
    cur.execute("CREATE TABLE t (slug varchar(64))")
    cur.execute("INSERT INTO t (slug) VALUES ('my-slug')")
    # bind the ORM-prepared value as a real query parameter
    cur.execute("SELECT slug FROM t WHERE slug = %s", [prepared])
    row = cur.fetchone()

print("query result:", row)
assert row is not None and row[0] == 'my-slug', row
print("DB filter accepted the wrapped URL kwarg without manual coercion: OK")
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover all 4 requirements and hold on the gold-patched tree. Positive control (probe_db, R1.3): mimics the ORM query path (CharField.get_db_prep_value then sqlite parameter binding) for a wrapped URL string kwarg — HOLDS patched (get_prep_value yields a real str, binds cleanly) and VIOLATED at base (SimpleLazyObject binding raises sqlite3.InterfaceError 'unsupported type'), so it discriminates base vs patched. Note: binding the raw wrapper directly (without the ORM get_prep_value coercion) fails on BOTH trees because the patched __proxy__ is not type-identity str (consistent with the G-PANEL-2 observation); the requirement is method delegation, and the ORM prep path exercises exactly the R1.3 DB-filter behavior the gold fix restores.

Coverage: probe_db=R1.3; probe_strmethods=R1.1/R1.2/R4.3 (str methods/operators/str()); probe_resolve_equal=R1.4/R4.3; probe_warning=R2.2/R2.4/R3.4 (named RemovedInDjango40Warning + view.kwargs, suppressed-still-resolves); probe_deferred_noeager=R2.1/R2.3 (no eager warning, none until consumed); probe_keys_order=R3.1/R3.2/R3.3 (per-key wrapper, key set, order, name-keyed notice); probe_int_arith=R1.1/R1.2/R4.4 (delegates the underlying value's OWN type via type(value), not a hardcoded str — int arithmetic works). Candidate wrong-fix patches, BOTH rejected by the suite:

(1) weak_strcoerce places the raw value into the context (no deferral) — REJECTED by probe_warning and probe_keys_order (no deprecation notice emitted);

(2) weak_lazy_str uses lazy(access_value, str) hardcoding str instead of type(value) — passes all string/warning probes but REJECTED by probe_int_arith (int kwarg loses arithmetic delegation). Suite discriminates both plausible weak readings; no too-weak candidate survives. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch replaces @SimpleLazyObject with lazy(access_value, type(value))(), i.e. a functional.lazy __proxy__ that delegates the underlying type's methods/operators/str() while deferring resolution + one-time RemovedInDjango40Warning. Probed on gold-patched tree via nl_attack: keys ['offer_slug','n'] preserved; type(s)=='__proxy__', isinstance(s,str)==False (matches R1.1/intro disclaimer, NOT a violation); s.upper()=='MY-SLUG' with exactly 1 RemovedInDjango40Warning naming 'offer_slug' and directing to view.kwargs (R1.2/R2.2); int wrapper +3 == 10 (R1.2 operators); str(s)=='my-slug', s=='my-slug' True (R1.4/R4.3); unconsumed wrapper emits 0 warnings (R2.3). The base commit (SimpleLazyObject) actually had isinstance(s,str)==True — the patch makes type-identity WORSE while fixing DB binding via delegation, exactly what the requirements describe. The prior G-PANEL-2 fail's own note concedes 'R1.3/R4 capture faithfully' the real DB-fixing effect and that the fix is method delegation, not type identity — its UNFAITHFUL verdict is an artifact of testing a type-identity property the requirements explicitly disclaim.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the fix behaviorally without transmitting hidden-test/gold content. Identifiers present are all either source-code names used for legitimate localization (_wrap_url_kwargs_with_deprecation_warning, TemplateView.get, base.py, RemovedInDjango40Warning, view.kwargs) or already public in problem_statement (SimpleLazyObject, the URL-slug/database-filter crash scenario). The gold's invented mechanism (SimpleLazyObject -> lazy(access_value, type(value))) is NOT named — the doc only states the behavioral requirement that the wrapper delegate the underlying value's methods/operators/conversions. No hidden test artifacts leak: test name test_template_params_filtering, the Artist model, 'Rene Magritte', ArtistView, and artist_name are all absent. The slug/DB-filter example matches the problem_statement's offer_slug/get_object_or_404 case, not the test's Artist.objects.get. The isinstance/type() parenthetical is a behavioral-boundary clarification the tests don't check, not a leak. No case enumeration mirroring the single-parameter test.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
