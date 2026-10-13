# P2 adversarial audit — django__django-14155

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
"""R1.1/R1.2 positive control: partial func -> func= is repr(partial), revealing
the wrapped underlying function AND the pre-bound kwargs, not a bare dotted name."""
import functools, re, sys
from django.urls.resolvers import ResolverMatch

def my_view(request, template_name=None):
    return None

p = functools.partial(my_view, template_name='template.html')
m = ResolverMatch(p, (), {}, url_name='partial', route='partial/')
s = repr(m)
print("repr:", s)

mobj = re.search(r"func=(.*?), args=", s)
assert mobj, "cannot locate func= portion"
func_portion = mobj.group(1)
print("func_portion:", func_portion)

ok = (func_portion == repr(p)
      and 'my_view' in func_portion
      and "template_name='template.html'" in func_portion
      and func_portion.startswith('functools.partial('))
if not ok:
    print("FAIL: func= portion is not the partial's own repr revealing wrapped fn + kwargs")
    sys.exit(1)
# must NOT be the bare dotted class path
if func_portion == 'functools.partial':
    print("FAIL: bare dotted name")
    sys.exit(1)
print("HOLD")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2: partial carrying __name__/__module__ (via update_wrapper) STILL renders
func= from repr(partial), irrespective of those attributes -> not a dotted name."""
import functools, re, sys
from django.urls.resolvers import ResolverMatch

def my_view(request, template_name=None):
    return None

p = functools.partial(my_view, template_name='template.html')
functools.update_wrapper(p, my_view)  # gives p a __name__ and __module__
assert hasattr(p, '__name__')

m = ResolverMatch(p, (), {}, url_name='partial_wrapped', route='partial_wrapped/')
s = repr(m)
print("repr:", s)
mobj = re.search(r"func=(.*?), args=", s)
func_portion = mobj.group(1)
print("func_portion:", func_portion)

# Must be the partial object repr, not a dotted __module__.__name__ path.
if func_portion != repr(p):
    print("FAIL: func= not derived from partial's own repr")
    sys.exit(1)
if not func_portion.startswith('functools.partial('):
    print("FAIL: not rendered as partial object")
    sys.exit(1)
print("HOLD")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.1/R2.2/R2.3: metadata fields rendered with repr (%r) -> strings quoted.
url_name and route with special string values appear quoted."""
import re, sys
from django.urls.resolvers import ResolverMatch

def my_view(request):
    return None

m = ResolverMatch(my_view, ('42', '37'), {'a': 1},
                  url_name='no-kwargs', app_names=[], namespaces=[],
                  route='^no_kwargs/([0-9]+)/([0-9]+)/$')
s = repr(m)
print("repr:", s)

# url_name quoted
if "url_name='no-kwargs'" not in s:
    print("FAIL: url_name not quoted"); sys.exit(1)
# route quoted
if "route='^no_kwargs/([0-9]+)/([0-9]+)/$'" not in s:
    print("FAIL: route not quoted"); sys.exit(1)
# args as repr tuple
if "args=('42', '37')" not in s:
    print("FAIL: args not repr"); sys.exit(1)
# kwargs as repr dict
if "kwargs={'a': 1}" not in s:
    print("FAIL: kwargs not repr"); sys.exit(1)
# app_names/namespaces as repr lists
if "app_names=[]" not in s or "namespaces=[]" not in s:
    print("FAIL: app_names/namespaces not repr"); sys.exit(1)
print("HOLD")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.4: exact field order func,args,kwargs,url_name,app_names,namespaces,route
wrapped in ResolverMatch(...). Verifies structural order precisely."""
import re, sys
from django.urls.resolvers import ResolverMatch

def my_view(request):
    return None

m = ResolverMatch(my_view, (), {}, url_name='u', app_names=['a'],
                  namespaces=['n'], route='r/')
s = repr(m)
print("repr:", s)

pat = (r"^ResolverMatch\(func=.*, args=.*, kwargs=.*, url_name=.*, "
       r"app_names=.*, namespaces=.*, route=.*\)$")
if not re.match(pat, s):
    print("FAIL: field order/prefix/suffix wrong"); sys.exit(1)

# ensure the quoted repr forms present and in-order for the string fields
order = ['func=', 'args=', 'kwargs=', 'url_name=', 'app_names=', 'namespaces=', 'route=']
idxs = [s.index(k) for k in order]
if idxs != sorted(idxs):
    print("FAIL: fields not in mandated order"); sys.exit(1)
if not (s.startswith('ResolverMatch(') and s.endswith(')')):
    print("FAIL: missing wrapper"); sys.exit(1)
print("HOLD")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.1/R3.2: ordinary (non-partial) view still rendered as dotted module.name
path, NOT as a partial-object representation."""
import re, sys
from django.urls.resolvers import ResolverMatch

def my_view(request):
    return None

m = ResolverMatch(my_view, (), {}, url_name='x', route='x/')
s = repr(m)
print("repr:", s)
mobj = re.search(r"func=(.*?), args=", s)
func_portion = mobj.group(1)
print("func_portion:", func_portion)

expected = my_view.__module__ + '.' + my_view.__name__
if func_portion != expected:
    print("FAIL: func= not dotted path; got %r expected %r" % (func_portion, expected))
    sys.exit(1)
if 'functools.partial' in func_portion:
    print("FAIL: rendered as partial"); sys.exit(1)

# class-based view path too
class MyCBV:
    def __call__(self, request): return None
cbv = MyCBV()
m2 = ResolverMatch(cbv, (), {})
s2 = repr(m2)
print("cbv repr:", s2)
mobj2 = re.search(r"func=(.*?), args=", s2)
exp2 = cbv.__class__.__module__ + '.' + cbv.__class__.__name__
if mobj2.group(1) != exp2:
    print("FAIL: cbv func path"); sys.exit(1)
print("HOLD")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.1/R4.2: non-repr behavior preserved. Attributes func/args/kwargs retain
constructed values; indexing [0]/[1]/[2] returns func/args/kwargs; url_name,
app_name(s), namespace(s), route, view_name computed as before."""
import sys
from django.urls.resolvers import ResolverMatch

def my_view(request):
    return None

args = ('42', '37')
kwargs = {'k': 'v'}
m = ResolverMatch(my_view, args, kwargs, url_name='u',
                  app_names=['app', ''], namespaces=['ns1', 'ns2', ''],
                  route='r/')

assert m.func is my_view, "func changed"
assert m[0] is my_view, "index 0"
assert m.args == args and m[1] == args, "args"
assert m.kwargs == kwargs and m[2] == kwargs, "kwargs"
assert m.url_name == 'u', "url_name"
assert m.app_names == ['app'], ("app_names", m.app_names)
assert m.app_name == 'app', "app_name"
assert m.namespaces == ['ns1', 'ns2'], ("namespaces", m.namespaces)
assert m.namespace == 'ns1:ns2', "namespace"
assert m.route == 'r/', "route"
# view_name = namespaces + [url_name or func_path]
assert m.view_name == 'ns1:ns2:u', ("view_name", m.view_name)
print("attrs OK; view_name:", m.view_name)
print("HOLD")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1/R1.2 positive control: partial func -> func= is repr(partial), revealing
the wrapped underlying function AND the pre-bound kwargs, not a bare dotted name."""
import functools, re, sys
from django.urls.resolvers import ResolverMatch

def my_view(request, template_name=None):
    return None

p = functools.partial(my_view, template_name='template.html')
m = ResolverMatch(p, (), {}, url_name='partial', route='partial/')
s = repr(m)
print("repr:", s)

mobj = re.search(r"func=(.*?), args=", s)
assert mobj, "cannot locate func= portion"
func_portion = mobj.group(1)
print("func_portion:", func_portion)

ok = (func_portion == repr(p)
      and 'my_view' in func_portion
      and "template_name='template.html'" in func_portion
      and func_portion.startswith('functools.partial('))
if not ok:
    print("FAIL: func= portion is not the partial's own repr revealing wrapped fn + kwargs")
    sys.exit(1)
# must NOT be the bare dotted class path
if func_portion == 'functools.partial':
    print("FAIL: bare dotted name")
    sys.exit(1)
print("HOLD")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14155: ResolverMatch.__repr__ now (a) renders func= as repr(self.func) for functools.partial views, (b) renders args/kwargs/url_name/app_names/namespaces/route with %r.

Probes (each standalone, constructs ResolverMatch directly; no settings/pytest):
- probe_1 (R1.1/R1.2, POSITIVE CONTROL): partial func -> func= equals repr(partial), revealing wrapped fn (my_view) + pre-bound kwarg template_name='template.html', not bare 'functools.partial'. PATCHED HOLD; BASE VIOLATED (func=functools.partial). Discriminates.
- probe_2 (R1.2): partial with update_wrapper (__name__/__module__ set) STILL renders from repr(partial), not a dotted name. PATCHED HOLD; BASE VIOLATED (rendered dotted __main__.my_view).
- probe_3 (R2.1/R2.2/R2.3): url_name, route, args, kwargs, app_names, namespaces rendered via %r (strings quoted). PATCHED HOLD; BASE VIOLATED (url_name/route unquoted).
- probe_4 (R2.4): exact field order func,args,kwargs,url_name,app_names,namespaces,route wrapped in ResolverMatch(...). PATCHED HOLD; BASE HOLD (order unchanged by fix).
- probe_5 (R3.1/R3.2): ordinary function view AND class-based view render as dotted module.name path, no 'functools.partial'. PATCHED HOLD; BASE HOLD (regression check).
- probe_6 (R4.1/R4.2): func/args/kwargs attributes retain constructed values; indexing [0]/[1]/[2]; url_name/app_name(s)/namespace(s)/route/view_name computed as before (falsy filtering, ':'.join, namespaces+[url_name]). PATCHED HOLD; BASE HOLD.

All 6 probes HOLD on patched tree. Positive control (probe_1) fails at base -> discriminating power confirmed (also probes 2 & 3 fail at base).

Wrong-fix candidate 'quote_only_no_partial' (weak.diff): adds %r quoting to all metadata fields but keeps func=self._func_path (no partial branch) — the lazy reading that only addresses Requirement 2/3. Applies cleanly at base. Under it probes 3,4,5,6 HOLD but probes 1 & 2 (Requirement 1) are REJECTED. This demonstrates the suite discriminates a probe-nonconforming wrong fix; it is NOT a too-weak finding (probes correctly reject it, and it would fail the hidden test_repr_functools_partial). No requirement-conforming wrong patch found: the probe suite pins both the partial handling and the quoting, which jointly are exactly the gold behavior.

Note on meta.json: G-PANEL-3 (leakage) is stamped fail for this cell — Requirement 1's three sub-criteria mirror the hidden test's parametrized ids incl. update_wrapper, which is not derivable from the public problem statement. That is a leakage concern, orthogonal to G-EQ spec-fidelity; the requirements are faithful and not too weak, so G-EQ is SOUND.

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
"""R1.1/R1.2 positive control: partial func -> func= is repr(partial), revealing
the wrapped underlying function AND the pre-bound kwargs, not a bare dotted name."""
import functools, re, sys
from django.urls.resolvers import ResolverMatch

def my_view(request, template_name=None):
    return None

p = functools.partial(my_view, template_name='template.html')
m = ResolverMatch(p, (), {}, url_name='partial', route='partial/')
s = repr(m)
print("repr:", s)

mobj = re.search(r"func=(.*?), args=", s)
assert mobj, "cannot locate func= portion"
func_portion = mobj.group(1)
print("func_portion:", func_portion)

ok = (func_portion == repr(p)
      and 'my_view' in func_portion
      and "template_name='template.html'" in func_portion
      and func_portion.startswith('functools.partial('))
if not ok:
    print("FAIL: func= portion is not the partial's own repr revealing wrapped fn + kwargs")
    sys.exit(1)
# must NOT be the bare dotted class path
if func_portion == 'functools.partial':
    print("FAIL: bare dotted name")
    sys.exit(1)
print("HOLD")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14155: ResolverMatch.__repr__ now (a) renders func= as repr(self.func) for functools.partial views, (b) renders args/kwargs/url_name/app_names/namespaces/route with %r.

Probes (each standalone, constructs ResolverMatch directly; no settings/pytest):
- probe_1 (R1.1/R1.2, POSITIVE CONTROL): partial func -> func= equals repr(partial), revealing wrapped fn (my_view) + pre-bound kwarg template_name='template.html', not bare 'functools.partial'. PATCHED HOLD; BASE VIOLATED (func=functools.partial). Discriminates.
- probe_2 (R1.2): partial with update_wrapper (__name__/__module__ set) STILL renders from repr(partial), not a dotted name. PATCHED HOLD; BASE VIOLATED (rendered dotted __main__.my_view).
- probe_3 (R2.1/R2.2/R2.3): url_name, route, args, kwargs, app_names, namespaces rendered via %r (strings quoted). PATCHED HOLD; BASE VIOLATED (url_name/route unquoted).
- probe_4 (R2.4): exact field order func,args,kwargs,url_name,app_names,namespaces,route wrapped in ResolverMatch(...). PATCHED HOLD; BASE HOLD (order unchanged by fix).
- probe_5 (R3.1/R3.2): ordinary function view AND class-based view render as dotted module.name path, no 'functools.partial'. PATCHED HOLD; BASE HOLD (regression check).
- probe_6 (R4.1/R4.2): func/args/kwargs attributes retain constructed values; indexing [0]/[1]/[2]; url_name/app_name(s)/namespace(s)/route/view_name computed as before (falsy filtering, ':'.join, namespaces+[url_name]). PATCHED HOLD; BASE HOLD.

All 6 probes HOLD on patched tree. Positive control (probe_1) fails at base -> discriminating power confirmed (also probes 2 & 3 fail at base).

Wrong-fix candidate 'quote_only_no_partial' (weak.diff): adds %r quoting to all metadata fields but keeps func=self._func_path (no partial branch) — the lazy reading that only addresses Requirement 2/3. Applies cleanly at base. Under it probes 3,4,5,6 HOLD but probes 1 & 2 (Requirement 1) are REJECTED. This demonstrates the suite discriminates a probe-nonconforming wrong fix; it is NOT a too-weak finding (probes correctly reject it, and it would fail the hidden test_repr_functools_partial). No requirement-conforming wrong patch found: the probe suite pins both the partial handling and the quoting, which jointly are exactly the gold behavior.

Note on meta.json: G-PANEL-3 (leakage) is stamped fail for this cell — Requirement 1's three sub-criteria mirror the hidden test's parametrized ids incl. update_wrapper, which is not derivable from the public problem statement. That is a leakage concern, orthogonal to G-EQ spec-fidelity; the requirements are faithful and not too weak, so G-EQ is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes exactly one method, ResolverMatch.__repr__: branch on isinstance(self.func, functools.partial) -> repr(self.func) else self._func_path, and %r for all metadata fields. Requirements map 1:1. Crucially R1's criteria do NOT invent nested/update_wrapper-specific code paths — they describe uniform repr(self.func) behavior that happens to cover those cases, so no forbidden/mandated behavior mismatch. (The separate G-PANEL-3 leakage concern about mentioning update_wrapper is a leakage question, out of scope for faithfulness; behaviorally R1.3 is still true of the patched code.) Verified live via nl_attack probe on both patched (exit 0, ALL OK) and base (AssertionError on unquoted url_name).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the public problem_statement (ResolverMatch.__repr__ mishandling functools.partial) plus legitimate localization (naming ResolverMatch.__repr__ in django/urls/resolvers.py, which is fine). The field ordering (func, args, kwargs, url_name, app_names, namespaces, route) is intrinsic to the pre-existing __repr__ format string in the public source, not test-derived. The document does NOT transmit any hidden-test specifics: it omits the test names (test_repr, test_repr_functools_partial, test_resolver_match_on_request), the test path (tests/urlpatterns_reverse/tests.py), the parametrization cases ('partial','partial_nested','partial_wrapped' with 'template.html'/'nested_partial.html'), the concrete example URLs/routes (/no_kwargs/42/37/), and the empty_view identifier. Requirements are stated as general behavioral rules (repr each metadata field, use partial's own repr for func) rather than enumerating the three parametrized cases. No fix-invented identifiers appear. No verbatim gold lines. This is faithful behavioral translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
