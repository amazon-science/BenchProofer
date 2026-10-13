# P2 adversarial audit — django__django-11095

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_default_returns_inlines.py`, `probe_2_sources_from_hook.py`, `probe_3_empty_hook.py`, `probe_4_permission_filtering.py`, `probe_5_formsets_use_hook.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2_sources_from_hook.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_default_returns_inlines.py` → holds on the patched tree (good)

```python
# R1.1 & R1.2: get_inlines(request, obj) exists and, when not customized,
# returns the instance's `inlines` attribute (same object).
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes','django.contrib.auth',
        'django.contrib.admin','django.contrib.messages','django.contrib.sessions'])
django.setup()
from django.contrib.admin.options import ModelAdmin

if not hasattr(ModelAdmin, "get_inlines"):
    print("FAIL: ModelAdmin has no get_inlines hook"); sys.exit(1)

ma = ModelAdmin.__new__(ModelAdmin)
sentinel = ["INLINE_A", "INLINE_B"]
ma.inlines = sentinel
ret = ModelAdmin.get_inlines(ma, request=None, obj=None)
print("get_inlines returned:", ret)
if ret is not sentinel and list(ret) != list(sentinel):
    print("FAIL: default get_inlines did not return the inlines attribute"); sys.exit(1)
print("OK: default get_inlines returns inlines attribute")
sys.exit(0)
```

Attack 2 — `probe_2_sources_from_hook.py` → holds on the patched tree (good)

```python
# R2.1 & R2.2 & R1.3: get_inline_instances sources classes from get_inlines,
# NOT from self.inlines directly. Override the hook to return a different set;
# the built instances must reflect exactly the hook's classes, in order.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes','django.contrib.auth',
        'django.contrib.admin','django.contrib.messages','django.contrib.sessions'])
django.setup()
from django.contrib.admin.options import ModelAdmin

# Fake inline classes: constructed with (model, admin_site); permission methods
# all grant, so none are filtered out.
def make(name):
    class Inline:
        _name = name
        def __init__(self, model, admin_site):
            self.model = model; self.admin_site = admin_site
            self.max_num = None
        def has_view_or_change_permission(self, request, obj=None): return True
        def has_add_permission(self, request, obj=None): return True
        def has_delete_permission(self, request, obj=None): return True
    Inline.__name__ = name
    return Inline

A, B, C = make("A"), make("B"), make("C")

class MA(ModelAdmin):
    inlines = [A]           # attribute says only A
    def __init__(self):
        self.model = object(); self.admin_site = object()
    def get_inlines(self, request, obj):
        return [C, B]       # hook says C then B

ma = MA()
insts = ma.get_inline_instances(request=None, obj=None)
types = [type(i) for i in insts]
print("instance types:", [t.__name__ for t in types])
if types != [C, B]:
    print("FAIL: get_inline_instances did not use hook classes in order (expected [C, B])")
    sys.exit(1)
print("OK: instances built from hook, exactly [C, B] in order")
sys.exit(0)
```

Attack 3 — `probe_3_empty_hook.py` → holds on the patched tree (good)

```python
# R2.3: when the hook returns an empty collection, get_inline_instances returns [].
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes','django.contrib.auth',
        'django.contrib.admin','django.contrib.messages','django.contrib.sessions'])
django.setup()
from django.contrib.admin.options import ModelAdmin

class Dummy:
    def __init__(self, model, admin_site): pass
    def has_view_or_change_permission(self, r, o=None): return True
    def has_add_permission(self, r, o=None): return True
    def has_delete_permission(self, r, o=None): return True

class MA(ModelAdmin):
    inlines = [Dummy]   # attribute non-empty; hook empty
    def __init__(self):
        self.model = object(); self.admin_site = object()
    def get_inlines(self, request, obj):
        return []

ma = MA()
insts = ma.get_inline_instances(request=None, obj=None)
print("instances:", insts)
if insts != []:
    print("FAIL: expected empty list from empty hook"); sys.exit(1)
print("OK: empty hook -> empty instance list")
sys.exit(0)
```

Attack 4 — `probe_4_permission_filtering.py` → holds on the patched tree (good)

```python
# R3.2 & R3.3 & R3.4: existing permission behavior preserved.
# - inline granting NONE of view/change/add/delete is excluded when request given
# - inline lacking add permission gets max_num=0
# - inline constructed with (self.model, self.admin_site)
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes','django.contrib.auth',
        'django.contrib.admin','django.contrib.messages','django.contrib.sessions'])
django.setup()
from django.contrib.admin.options import ModelAdmin

MODEL = object(); SITE = object()

def inline_cls(name, view, add, delete):
    class Inline:
        def __init__(self, model, admin_site):
            self.model = model; self.admin_site = admin_site; self.max_num = None
        def has_view_or_change_permission(self, r, o=None): return view
        def has_add_permission(self, r, o=None): return add
        def has_delete_permission(self, r, o=None): return delete
    Inline.__name__ = name
    return Inline

Granted   = inline_cls("Granted", True, True, True)     # kept, max_num untouched
NoPerm    = inline_cls("NoPerm", False, False, False)   # excluded
NoAdd     = inline_cls("NoAdd", True, False, True)       # kept, max_num->0

class MA(ModelAdmin):
    def __init__(self):
        self.model = MODEL; self.admin_site = SITE
    def get_inlines(self, request, obj):
        return [Granted, NoPerm, NoAdd]

req = object()  # truthy request
ma = MA()
insts = ma.get_inline_instances(request=req, obj=None)
names = [type(i).__name__ for i in insts]
print("kept:", names)
if names != ["Granted", "NoAdd"]:
    print("FAIL: permission filtering wrong; expected [Granted, NoAdd]"); sys.exit(1)

by = {type(i).__name__: i for i in insts}
if by["Granted"].max_num is not None:
    print("FAIL: Granted.max_num changed unexpectedly:", by["Granted"].max_num); sys.exit(1)
if by["NoAdd"].max_num != 0:
    print("FAIL: NoAdd inline should have max_num==0, got", by["NoAdd"].max_num); sys.exit(1)
for i in insts:
    if i.model is not MODEL or i.admin_site is not SITE:
        print("FAIL: inline not constructed from admin model/site"); sys.exit(1)
print("OK: filtering, max_num=0, and construction preserved")
sys.exit(0)
```

Attack 5 — `probe_5_formsets_use_hook.py` → holds on the patched tree (good)

```python
# R3.5: get_formsets_with_inlines yields formsets corresponding to the inline
# instances produced through the hook (one per instance, in order, paired).
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes','django.contrib.auth',
        'django.contrib.admin','django.contrib.messages','django.contrib.sessions'])
django.setup()
from django.contrib.admin.options import ModelAdmin

def inline_cls(name):
    class Inline:
        def __init__(self, model, admin_site):
            self.model = model; self.admin_site = admin_site; self.max_num = None
        def has_view_or_change_permission(self, r, o=None): return True
        def has_add_permission(self, r, o=None): return True
        def has_delete_permission(self, r, o=None): return True
        def get_formset(self, request, obj=None):
            return ("FS", name)
    Inline.__name__ = name
    return Inline

X, Y = inline_cls("X"), inline_cls("Y")

class MA(ModelAdmin):
    def __init__(self):
        self.model = object(); self.admin_site = object()
    def get_inlines(self, request, obj):
        return [X, Y]

ma = MA()
pairs = list(ma.get_formsets_with_inlines(request=None, obj=None))
print("pairs:", [(fs, type(inl).__name__) for fs, inl in pairs])
if len(pairs) != 2:
    print("FAIL: expected 2 formset/inline pairs"); sys.exit(1)
for (fs, inl), expected in zip(pairs, [X, Y]):
    if type(inl) is not expected:
        print("FAIL: inline order/type mismatch"); sys.exit(1)
    if fs != ("FS", expected.__name__):
        print("FAIL: formset does not correspond to its inline"); sys.exit(1)
print("OK: formsets correspond to hook-produced inlines, in order")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2_sources_from_hook.py`

```python
# R2.1 & R2.2 & R1.3: get_inline_instances sources classes from get_inlines,
# NOT from self.inlines directly. Override the hook to return a different set;
# the built instances must reflect exactly the hook's classes, in order.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes','django.contrib.auth',
        'django.contrib.admin','django.contrib.messages','django.contrib.sessions'])
django.setup()
from django.contrib.admin.options import ModelAdmin

# Fake inline classes: constructed with (model, admin_site); permission methods
# all grant, so none are filtered out.
def make(name):
    class Inline:
        _name = name
        def __init__(self, model, admin_site):
            self.model = model; self.admin_site = admin_site
            self.max_num = None
        def has_view_or_change_permission(self, request, obj=None): return True
        def has_add_permission(self, request, obj=None): return True
        def has_delete_permission(self, request, obj=None): return True
    Inline.__name__ = name
    return Inline

A, B, C = make("A"), make("B"), make("C")

class MA(ModelAdmin):
    inlines = [A]           # attribute says only A
    def __init__(self):
        self.model = object(); self.admin_site = object()
    def get_inlines(self, request, obj):
        return [C, B]       # hook says C then B

ma = MA()
insts = ma.get_inline_instances(request=None, obj=None)
types = [type(i) for i in insts]
print("instance types:", [t.__name__ for t in types])
if types != [C, B]:
    print("FAIL: get_inline_instances did not use hook classes in order (expected [C, B])")
    sys.exit(1)
print("OK: instances built from hook, exactly [C, B] in order")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11095: adds ModelAdmin.get_inlines(request, obj) hook (returns self.inlines) and rewires get_inline_instances to source classes from it. Probe suite:
- probe_1 (R1.1,R1.2): get_inlines exists and default returns the inlines attribute. HOLDS patched.
- probe_2 (R2.1,R2.2,R1.3, POSITIVE CONTROL): override hook to return [C,B] while inlines=[A]; get_inline_instances must build exactly [C,B] in order. HOLDS patched, VIOLATED at base (base builds [A] from self.inlines) -> discriminates.
- probe_3 (R2.3): empty hook -> [] even when inlines non-empty. HOLDS patched.
- probe_4 (R3.2,R3.3,R3.4): permission filtering (exclude no-perm inline), max_num=0 for no-add inline, construction from (model, admin_site). HOLDS patched.
- probe_5 (R3.5): get_formsets_with_inlines yields one formset per hook-produced inline, paired and in order. HOLDS patched.
All 5 HOLD on gold-patched tree; positive control fails at base (prepatch reproduced).

Candidate wrong-fix weak.diff adds get_inlines hook but leaves get_inline_instances reading self.inlines directly (the lazy R1-only reading). Probes 2,3,4,5 all REJECT it (probe_1 still holds). Demonstrates the suite discriminates a requirements-partial implementation; no requirements-conforming-yet-wrong patch found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_default_returns_inlines.py`, `probe_2_sources_from_hook.py`, `probe_3_empty_hook.py`, `probe_4_permission_filtering.py`, `probe_5_formsets_use_hook.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2_sources_from_hook.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_default_returns_inlines.py` → holds on the patched tree (good)

Attack 2 — `probe_2_sources_from_hook.py` → holds on the patched tree (good)

Attack 3 — `probe_3_empty_hook.py` → holds on the patched tree (good)

Attack 4 — `probe_4_permission_filtering.py` → holds on the patched tree (good)

Attack 5 — `probe_5_formsets_use_hook.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2_sources_from_hook.py`

```python
# R2.1 & R2.2 & R1.3: get_inline_instances sources classes from get_inlines,
# NOT from self.inlines directly. Override the hook to return a different set;
# the built instances must reflect exactly the hook's classes, in order.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        'django.contrib.contenttypes','django.contrib.auth',
        'django.contrib.admin','django.contrib.messages','django.contrib.sessions'])
django.setup()
from django.contrib.admin.options import ModelAdmin

# Fake inline classes: constructed with (model, admin_site); permission methods
# all grant, so none are filtered out.
def make(name):
    class Inline:
        _name = name
        def __init__(self, model, admin_site):
            self.model = model; self.admin_site = admin_site
            self.max_num = None
        def has_view_or_change_permission(self, request, obj=None): return True
        def has_add_permission(self, request, obj=None): return True
        def has_delete_permission(self, request, obj=None): return True
    Inline.__name__ = name
    return Inline

A, B, C = make("A"), make("B"), make("C")

class MA(ModelAdmin):
    inlines = [A]           # attribute says only A
    def __init__(self):
        self.model = object(); self.admin_site = object()
    def get_inlines(self, request, obj):
        return [C, B]       # hook says C then B

ma = MA()
insts = ma.get_inline_instances(request=None, obj=None)
types = [type(i) for i in insts]
print("instance types:", [t.__name__ for t in types])
if types != [C, B]:
    print("FAIL: get_inline_instances did not use hook classes in order (expected [C, B])")
    sys.exit(1)
print("OK: instances built from hook, exactly [C, B] in order")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11095: adds ModelAdmin.get_inlines(request, obj) hook (returns self.inlines) and rewires get_inline_instances to source classes from it. Probe suite:
- probe_1 (R1.1,R1.2): get_inlines exists and default returns the inlines attribute. HOLDS patched.
- probe_2 (R2.1,R2.2,R1.3, POSITIVE CONTROL): override hook to return [C,B] while inlines=[A]; get_inline_instances must build exactly [C,B] in order. HOLDS patched, VIOLATED at base (base builds [A] from self.inlines) -> discriminates.
- probe_3 (R2.3): empty hook -> [] even when inlines non-empty. HOLDS patched.
- probe_4 (R3.2,R3.3,R3.4): permission filtering (exclude no-perm inline), max_num=0 for no-add inline, construction from (model, admin_site). HOLDS patched.
- probe_5 (R3.5): get_formsets_with_inlines yields one formset per hook-produced inline, paired and in order. HOLDS patched.
All 5 HOLD on gold-patched tree; positive control fails at base (prepatch reproduced).

Candidate wrong-fix weak.diff adds get_inlines hook but leaves get_inline_instances reading self.inlines directly (the lazy R1-only reading). Probes 2,3,4,5 all REJECT it (probe_1 still holds). Demonstrates the suite discriminates a requirements-partial implementation; no requirements-conforming-yet-wrong patch found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Req1 (hook exists, defaults to inlines attr, overridable) = patch hunk 1. Req2 (get_inline_instances sources from hook, exact classes/order, empty->[], single->that type) = patch hunk 2; verified by probe. Req3 (permission filtering, max_num=0 on no-add, model/site construction, formsets unchanged) correctly describes the UNCHANGED surrounding loop the diff preserves — faithful backward-compat framing, not invented behavior. Boundary is correctly pinned at the changed observable behavior (hook drives instantiation).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The two named entities in the spec (get_inlines, get_inline_instances) are both explicitly in the public problem_statement; the `inlines` attribute is standard public Django API. No test file path, test class/function name (test_get_inline_instances_override_get_inlines / generic_inline_admin / EpisodeAdmin / MediaInline / AlternateInline / Episode / Media), parametrization id, or quoted test/gold code appears. The only fix-introduced identifier (get_inlines) is public. Req 3's permission-filtering and max_num=0 details describe PRE-EXISTING options.py behavior (visible as gold-patch context, not fix-invented) framed as backward-compat preservation. Req 2's empty-collection and single-class acceptance criteria are generic behavioral translations, not a reconstruction of the test's ('alternate',...)/('media',...) parametrization — the spec never mentions request.name dispatch or the two concrete inline classes. Legitimate localization + behavioral translation throughout.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
