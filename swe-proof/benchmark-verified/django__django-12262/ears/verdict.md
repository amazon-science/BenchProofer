# P2 adversarial audit — django__django-12262

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 10 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 10 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py`, `probe_10.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (10):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def greet(*, greeting='hello'):
    return greeting
eng = make(reg)
out = render(eng, "{% greet greeting='hi' %}")
print("observed render:", repr(out))
assert out == 'hi', "expected 'hi', got %r" % out
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def greet(*, greeting='hello'):
    return greeting
eng = make(reg)
out = render(eng, "{% greet %}")
print("observed render:", repr(out))
assert out == 'hello', "expected 'hello', got %r" % out
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def greet(*, greeting='hello'):
    return greeting
eng = make(reg)
try:
    render(eng, "{% greet greeting='a' greeting='b' %}")
    print("NO ERROR RAISED"); sys.exit(1)
except TemplateSyntaxError as e:
    msg = str(e)
    print("observed msg:", repr(msg))
    expected = "'greet' received multiple values for keyword argument 'greeting'"
    if msg != expected:
        print("MISMATCH expected:", repr(expected)); sys.exit(1)
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def greet(*, greeting='hello'):
    return greeting
eng = make(reg)
try:
    render(eng, "{% greet bogus='x' %}")
    print("NO ERROR RAISED"); sys.exit(1)
except TemplateSyntaxError as e:
    msg = str(e)
    print("observed msg:", repr(msg))
    expected = "'greet' received unexpected keyword argument 'bogus'"
    if msg != expected:
        print("MISMATCH expected:", repr(expected)); sys.exit(1)
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def greet(*, greeting):   # no default -> required
    return greeting
eng = make(reg)
try:
    render(eng, "{% greet %}")
    print("NO ERROR RAISED"); sys.exit(1)
except TemplateSyntaxError as e:
    msg = str(e)
    print("observed msg:", repr(msg))
    if "did not receive value(s) for the argument(s)" not in msg or "greeting" not in msg:
        print("MISMATCH"); sys.exit(1)
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.inclusion_tag('t.html')
def inc(*, greeting='hello'):
    return {'g': greeting}
# monkeypatch template loading: inclusion_tag needs a template. Use from_string via a fake.
# Instead render with a simple template file substitute:
from django.template import Template, Context as C
# override get_template resolution by giving the tag a compiled template through OPTIONS is messy;
# simpler: test parse_bits path directly via the inclusion tag compile (parsing happens at compile time).
eng = make(reg)
# Parsing/kwarg-binding occurs at *render* for inclusion? Actually args parsed at compile (parse_bits in compile_func).
try:
    tmpl = eng.from_string("{% load mylib %}{% inc greeting='hi' %}")
    print("compiled OK (parse_bits accepted keyword-only override)")
except TemplateSyntaxError as e:
    print("parse_bits REJECTED:", repr(str(e))); sys.exit(1)
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def f(a):
    return a
eng = make(reg)
try:
    render(eng, "{% f a=1 a=2 %}")
    print("NO ERROR"); sys.exit(1)
except TemplateSyntaxError as e:
    msg = str(e)
    print("observed:", repr(msg))
    expected = "'f' received multiple values for keyword argument 'a'"
    if msg != expected:
        print("MISMATCH expected", repr(expected)); sys.exit(1)
sys.exit(0)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def f(**kwargs):
    return kwargs.get('anything', 'MISSING')
eng = make(reg)
out = render(eng, "{% f anything='ok' %}")
print("observed:", repr(out))
assert out == 'ok', out
sys.exit(0)
```

Attack 9 — `probe_9.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def f(a):
    return a
eng = make(reg)
ok = True
try:
    render(eng, "{% f 1 2 %}")
    print("too-many: NO ERROR"); ok=False
except TemplateSyntaxError as e:
    print("too-many msg:", repr(str(e)))
    if "too many positional arguments" not in str(e): ok=False
# positional after keyword
reg2 = Library()
@reg2.simple_tag
def g(a, b):
    return a
eng2 = make(reg2)
try:
    render(eng2, "{% g a=1 2 %}")
    print("after-kw: NO ERROR"); ok=False
except TemplateSyntaxError as e:
    print("after-kw msg:", repr(str(e)))
    if "positional argument(s) after some keyword argument(s)" not in str(e): ok=False
sys.exit(0 if ok else 1)
```

Attack 10 — `probe_10.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def f(a, b):
    return "%s-%s" % (a, b)
eng = make(reg)
out = render(eng, "{% f a=1 b=2 %}")
print("observed:", repr(out))
assert out == '1-2', out
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def greet(*, greeting='hello'):
    return greeting
eng = make(reg)
out = render(eng, "{% greet greeting='hi' %}")
print("observed render:", repr(out))
assert out == 'hi', "expected 'hi', got %r" % out
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Target: django/template/library.py parse_bits mishandling of keyword-only params. Gold changes the unexpected-kwarg guard from `param not in unhandled_kwargs` to `param not in kwonly`.

Probes (all via real template compile/render with Engine+Library; simple_tag and inclusion_tag):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): kwonly-with-default `def greet(*,greeting='hello')`, `{% greet greeting='hi' %}` -> renders 'hi'. HOLDS patched; FAILS at base (TemplateSyntaxError unexpected kwarg). Discriminates.
- probe_2 (Req1.3): omit kwonly default -> renders 'hello'. HOLDS.
- probe_3 (Req2/2.3): duplicate kwonly `greeting='a' greeting='b'` -> exact msg "'greet' received multiple values for keyword argument 'greeting'" (NOT unexpected). HOLDS patched; at base gives the WRONG 'unexpected keyword argument' diagnostic (violation confirmed at base).
- probe_4 (Req3.1/3.2): genuine unexpected `bogus='x'` -> exact "'greet' received unexpected keyword argument 'bogus'". HOLDS.
- probe_5 (Req4.1/4.2): required kwonly (no default) omitted -> "did not receive value(s)... 'greeting'". HOLDS.
- probe_6 (Req5.4 parity): inclusion_tag with kwonly default overridden by keyword compiles (parse_bits accepts). HOLDS.
- probe_7 (Req2.4): positional param supplied twice by keyword `a=1 a=2` -> multiple-values msg. HOLDS.
- probe_8 (Req3.3): `**kwargs` collects unexpected keyword. HOLDS.
- probe_9 (Req5.1/5.2): too-many-positional and positional-after-keyword still raise. HOLDS.
- probe_10 (Req5.3): positional params supplied by keyword name accepted/filled. HOLDS.

All 10 HOLD on gold-patched tree. Positive control probe_1 HOLDS patched / FAILS base -> discriminating power confirmed.

Candidate wrong-fix `weak_reject.diff`: replaces guard with a never-true condition (accept every keyword, matching the lazy 'just stop rejecting kwonly' reading). It satisfies Req1/Req2 but probe_4 REJECTS it (VIOLATED: genuine unexpected kwarg leaks through to the callable, TypeError). This demonstrates the suite discriminates wrong implementations; it is NOT a too-weak finding. No probe-conforming alternative found.

Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 10 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 10 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py`, `probe_10.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (10):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

Attack 9 — `probe_9.py` → holds on the patched tree (good)

Attack 10 — `probe_10.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':False,'OPTIONS':{}}], INSTALLED_APPS=[])
django.setup()
from django.template import Library, Context
from django.template.engine import Engine
from django.template.base import TemplateSyntaxError

def make(register):
    eng = Engine(libraries={}, builtins=[])
    eng.template_libraries['mylib'] = register
    return eng

def render(eng, src):
    return eng.from_string("{% load mylib %}" + src).render(Context({}))
reg = Library()
@reg.simple_tag
def greet(*, greeting='hello'):
    return greeting
eng = make(reg)
out = render(eng, "{% greet greeting='hi' %}")
print("observed render:", repr(out))
assert out == 'hi', "expected 'hi', got %r" % out
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Target: django/template/library.py parse_bits mishandling of keyword-only params. Gold changes the unexpected-kwarg guard from `param not in unhandled_kwargs` to `param not in kwonly`.

Probes (all via real template compile/render with Engine+Library; simple_tag and inclusion_tag):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): kwonly-with-default `def greet(*,greeting='hello')`, `{% greet greeting='hi' %}` -> renders 'hi'. HOLDS patched; FAILS at base (TemplateSyntaxError unexpected kwarg). Discriminates.
- probe_2 (Req1.3): omit kwonly default -> renders 'hello'. HOLDS.
- probe_3 (Req2/2.3): duplicate kwonly `greeting='a' greeting='b'` -> exact msg "'greet' received multiple values for keyword argument 'greeting'" (NOT unexpected). HOLDS patched; at base gives the WRONG 'unexpected keyword argument' diagnostic (violation confirmed at base).
- probe_4 (Req3.1/3.2): genuine unexpected `bogus='x'` -> exact "'greet' received unexpected keyword argument 'bogus'". HOLDS.
- probe_5 (Req4.1/4.2): required kwonly (no default) omitted -> "did not receive value(s)... 'greeting'". HOLDS.
- probe_6 (Req5.4 parity): inclusion_tag with kwonly default overridden by keyword compiles (parse_bits accepts). HOLDS.
- probe_7 (Req2.4): positional param supplied twice by keyword `a=1 a=2` -> multiple-values msg. HOLDS.
- probe_8 (Req3.3): `**kwargs` collects unexpected keyword. HOLDS.
- probe_9 (Req5.1/5.2): too-many-positional and positional-after-keyword still raise. HOLDS.
- probe_10 (Req5.3): positional params supplied by keyword name accepted/filled. HOLDS.

All 10 HOLD on gold-patched tree. Positive control probe_1 HOLDS patched / FAILS base -> discriminating power confirmed.

Candidate wrong-fix `weak_reject.diff`: replaces guard with a never-true condition (accept every keyword, matching the lazy 'just stop rejecting kwonly' reading). It satisfies Req1/Req2 but probe_4 REJECTS it (VIOLATED: genuine unexpected kwarg leaks through to the callable, TypeError). This demonstrates the suite discriminates wrong implementations; it is NOT a too-weak finding. No probe-conforming alternative found.

Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes parse_bits: `if param not in params and param not in unhandled_kwargs` -> `... and param not in kwonly`. This makes any declared keyword-only param (with or without default) an accepted keyword arg and routes a duplicated kwonly to the later multiple-values check rather than the unexpected-keyword branch. Verified live in the instance image via full template rendering with simple_tag and inclusion_tag: R1.1/1.2 {% hello greeting='hi' %}->'hi world' (kwonly-with-default accepted, supplied value used); R1.3 {% hello %}->'hello world' (default); R2.1-2.3 {% hi greeting='hi' greeting='ho' %}->"'hi' received multiple values for keyword argument 'greeting'" (kwonly dup = multiple-values, NOT unexpected); R2.4 {% pos a='x' a='y' %}->"'pos' received multiple values for keyword argument 'a'" (positional-by-name dup); R3.1/3.2 {% hi bogus='x' %}->"'hi' received unexpected keyword argument 'bogus'"; R3.3 {% kw a='1' extra='2' %}->OK, extra collected into **kwargs; R4.1/4.2 {% hi %}->"'hi' did not receive value(s) for the argument(s): 'greeting'"; R4.3 covered by R1.3; R5.1 too-many-positional, R5.2 positional-after-keyword, R5.3 {% pos a='x' %}->OK all as specified; R5.4 inclusion_tag gives identical override/unexpected/multiple-values messages as simple_tag. The requirements model the full changed observable behavior (accept/reject/diagnostic across both tag types), matching the exact issue-reported scenarios (hello greeting='hi' and hi duplicate). Message string forms in R2.2/R3.2 match verbatim. Boundary is correct, not a single-branch slice.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements only reuse content already public in the problem_statement: the example signature `def f(*, greeting='hello')` mirrors the ticket's `def hello(*, greeting='hello')`, and both quoted error-message forms ('received multiple values for keyword argument', 'received unexpected keyword argument') appear verbatim in the public problem_statement. No hidden-test artifacts leak: the tag names used by the tests (simple_keyword_only_default/param, inclusion_keyword_only_default), the parameter name `kwarg`, the default value 42, override value 37, test file paths (tests/template_tests/...), and test function names (test_simple_tags, test_inclusion_tag_errors, etc.) are all absent. The gold patch's fix-invented reference (`kwonly`) does not appear — 'keyword-only parameter' is standard Python terminology. Naming parse_bits/simple_tag/inclusion_tag/Library is legitimate localization. Req 4's 'did not receive value(s) for the argument(s)' phrasing describes preexisting missing-arg behavior as a requirement rather than enumerating the parametrized test cases. The document describes behavior, not the tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
