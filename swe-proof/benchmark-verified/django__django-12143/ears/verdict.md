# P2 adversarial audit — django__django-12143

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
# Req1 AC1 + AC4 (positive control): metacharacter prefix matched literally.
# With prefix 'form$', a key 'form$-0-id' must match; a key that would only
# match if '$' were a regex anchor/metachar must NOT be a false decision.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True)
    django.setup()
from django.contrib.admin.options import ModelAdmin

class F:
    def __init__(s,n): s.name=n
class M:
    def __init__(s,pk): s._meta=type('X',(),{'pk':F(pk)})()
class A:
    def __init__(s,pk='id'): s.model=M(pk)
class P:
    def __init__(s,items): s._i=items
    def items(s): return list(s._i)
class R:
    def __init__(s,items): s.POST=P(items)

def edited(items,prefix,pk='id'):
    return ModelAdmin._get_edited_object_pks(A(pk),R(items),prefix)

# 'form$' with '$' literal: the key that legitimately belongs to this prefix
items=[('form$-0-id','42'),('form$-1-id','43')]
res=edited(items,'form$')
print("prefix 'form$' items result:", res)
ok = res==['42','43']

# A key without the literal '$' must NOT match under prefix 'form$'.
# (If '$' were treated as end-anchor, 'form-0-id' could spuriously match.)
res2=edited([('form-0-id','99')],'form$')
print("prefix 'form$' vs key 'form-0-id':", res2)
ok = ok and res2==[]

import sys
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1 AC2: prefix-<digits>-pkname form is included. Req2 AC2: non-empty run of
# digits required; pkname anchored at end.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True)
    django.setup()
from django.contrib.admin.options import ModelAdmin
class F:
    def __init__(s,n): s.name=n
class M:
    def __init__(s,pk): s._meta=type('X',(),{'pk':F(pk)})()
class A:
    def __init__(s,pk='id'): s.model=M(pk)
class P:
    def __init__(s,items): s._i=items
    def items(s): return list(s._i)
class R:
    def __init__(s,items): s.POST=P(items)
def edited(items,prefix,pk='id'):
    return ModelAdmin._get_edited_object_pks(A(pk),R(items),prefix)

ok=True
# qualifying key included
r=edited([('form-0-id','5')],'form'); print('form-0-id:',r); ok=ok and r==['5']
r=edited([('form-123-id','7')],'form'); print('form-123-id:',r); ok=ok and r==['7']
# empty digit run -> NOT included
r=edited([('form--id','x')],'form'); print('form--id (no digits):',r); ok=ok and r==[]
# non-digit run -> NOT included
r=edited([('form-a-id','x')],'form'); print('form-a-id:',r); ok=ok and r==[]
# pkname must be anchored at end -> trailing junk excludes
r=edited([('form-0-idX','x')],'form'); print('form-0-idX:',r); ok=ok and r==[]
# other fields excluded
r=edited([('form-0-name','x')],'form'); print('form-0-name:',r); ok=ok and r==[]
import sys
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1 AC3/AC4 with multiple metachars: '.' must not act as wildcard;
# '(' etc treated literally. Also prefix mismatch excluded.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True)
    django.setup()
from django.contrib.admin.options import ModelAdmin
class F:
    def __init__(s,n): s.name=n
class M:
    def __init__(s,pk): s._meta=type('X',(),{'pk':F(pk)})()
class A:
    def __init__(s,pk='id'): s.model=M(pk)
class P:
    def __init__(s,items): s._i=items
    def items(s): return list(s._i)
class R:
    def __init__(s,items): s.POST=P(items)
def edited(items,prefix,pk='id'):
    return ModelAdmin._get_edited_object_pks(A(pk),R(items),prefix)

ok=True
# '.' literal: prefix 'fo.m' must NOT match key 'form-0-id' (where '.' as regex
# wildcard would match the 'r').
r=edited([('form-0-id','1')],'fo.m'); print("prefix 'fo.m' vs 'form-0-id':",r); ok=ok and r==[]
# but matches the literal-dot key
r=edited([('fo.m-0-id','2')],'fo.m'); print("prefix 'fo.m' vs 'fo.m-0-id':",r); ok=ok and r==['2']
# '(' literal group
r=edited([('a(b)-3-id','9')],'a(b)'); print("prefix 'a(b)':",r); ok=ok and r==['9']
# '*' literal quantifier abuse: prefix 'x*' shouldn't match 'xxxx-0-id'
r=edited([('xxxx-0-id','7')],'x*'); print("prefix 'x*' vs 'xxxx-0-id':",r); ok=ok and r==[]
r=edited([('x*-0-id','8')],'x*'); print("prefix 'x*' vs 'x*-0-id':",r); ok=ok and r==['8']
# prefix must anchor at start: key not beginning with prefix excluded
r=edited([('zform-0-id','3')],'form'); print("prefix 'form' vs 'zform-0-id':",r); ok=ok and r==[]
import sys
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req1 AC5: values returned unchanged, in POST iteration order. Req2 AC3:
# custom pk field name honored.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True)
    django.setup()
from django.contrib.admin.options import ModelAdmin
class F:
    def __init__(s,n): s.name=n
class M:
    def __init__(s,pk): s._meta=type('X',(),{'pk':F(pk)})()
class A:
    def __init__(s,pk='id'): s.model=M(pk)
class P:
    def __init__(s,items): s._i=items
    def items(s): return list(s._i)
class R:
    def __init__(s,items): s.POST=P(items)
def edited(items,prefix,pk='id'):
    return ModelAdmin._get_edited_object_pks(A(pk),R(items),prefix)

ok=True
# order + verbatim values (including a value that looks like a number-string)
items=[('form$-1-id','b'),('form$-0-id','a'),('other','z'),('form$-2-id','007')]
r=edited(items,'form$'); print('order/verbatim:',r); ok=ok and r==['b','a','007']
# custom pk name 'uuid'
r=edited([('form$-0-uuid','K1'),('form$-0-id','nope')],'form$',pk='uuid')
print("custom pk uuid:",r); ok=ok and r==['K1']
import sys
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req1 AC1 comprehensive: every listed metacharacter matches only itself.
# For each metachar c, prefix = 'form'+c ; the key 'form'+c+'-0-id' must be
# included, and a "regex-tempting" near-miss key must be excluded.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True)
    django.setup()
from django.contrib.admin.options import ModelAdmin
class F:
    def __init__(s,n): s.name=n
class M:
    def __init__(s,pk): s._meta=type('X',(),{'pk':F(pk)})()
class A:
    def __init__(s,pk='id'): s.model=M(pk)
class P:
    def __init__(s,items): s._i=items
    def items(s): return list(s._i)
class R:
    def __init__(s,items): s.POST=P(items)
def edited(items,prefix,pk='id'):
    return ModelAdmin._get_edited_object_pks(A(pk),R(items),prefix)

ok=True
metas = ['$','.','*','+','?','(',')','[',']','{','}','|','^','\\']
for c in metas:
    pref = 'form'+c
    key_lit = pref+'-0-id'          # literal key that belongs to this prefix
    r = edited([(key_lit,'V')], pref)
    inc = (r==['V'])
    # near miss: drop the metachar; regex-interpretation of many metachars
    # (., *, ?, backslash-escapes, etc.) could still match 'form-0-id'
    r2 = edited([('form-0-id','W')], pref)
    exc = (r2==[])
    print(repr(pref), "include:", inc, "exclude-nearmiss:", exc, r, r2)
    ok = ok and inc and exc
import sys
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1 AC1 + AC4 (positive control): metacharacter prefix matched literally.
# With prefix 'form$', a key 'form$-0-id' must match; a key that would only
# match if '$' were a regex anchor/metachar must NOT be a false decision.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True)
    django.setup()
from django.contrib.admin.options import ModelAdmin

class F:
    def __init__(s,n): s.name=n
class M:
    def __init__(s,pk): s._meta=type('X',(),{'pk':F(pk)})()
class A:
    def __init__(s,pk='id'): s.model=M(pk)
class P:
    def __init__(s,items): s._i=items
    def items(s): return list(s._i)
class R:
    def __init__(s,items): s.POST=P(items)

def edited(items,prefix,pk='id'):
    return ModelAdmin._get_edited_object_pks(A(pk),R(items),prefix)

# 'form$' with '$' literal: the key that legitimately belongs to this prefix
items=[('form$-0-id','42'),('form$-1-id','43')]
res=edited(items,'form$')
print("prefix 'form$' items result:", res)
ok = res==['42','43']

# A key without the literal '$' must NOT match under prefix 'form$'.
# (If '$' were treated as end-anchor, 'form-0-id' could spuriously match.)
res2=edited([('form-0-id','99')],'form$')
print("prefix 'form$' vs key 'form-0-id':", res2)
ok = ok and res2==[]

import sys
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django-12143: gold fix wraps prefix in re.escape() inside _get_edited_object_pks. 5 standalone probes exercise ModelAdmin._get_edited_object_pks directly (DBless, stdlib+django only) via a stub admin/model/request.

Probe->requirement mapping and results (patched / base / weak):
- probe_1 (Req1 AC1+AC4, POSITIVE CONTROL): prefix 'form$' includes 'form$-0-id'/'form$-1-id' and does NOT spuriously match 'form-0-id'. PATCHED=HOLDS, BASE=VIOLATED (base returns [] because '$' is treated as end-anchor => real prepatch bug reproduced), WEAK=HOLDS.
- probe_2 (Req1 AC2, Req2 AC2): qualifying prefix-<digits>-pkname included; empty/non-digit run excluded; pkname anchored at end (form-0-idX excluded); other fields excluded. PATCHED=HOLDS, WEAK=HOLDS.
- probe_3 (Req1 AC3/AC4): '.', '*', '(' , ')' treated literally; anchored at start. PATCHED=HOLDS, WEAK=VIOLATED (fo.m matches form-0-id; x* matches xxxx-0-id).
- probe_4 (Req1 AC5, Req2 AC3): values returned verbatim in POST iteration order; custom pk name 'uuid' honored. PATCHED=HOLDS, WEAK=HOLDS.
- probe_5 (Req1 AC1 comprehensive): each metachar in {$ . * + ? ( ) [ ] { } | ^ \} matches only itself (literal key included, regex-tempting near-miss excluded). PATCHED=HOLDS, WEAK=VIOLATED (raises sre_constants.error 'unterminated subpattern' on '(').

Candidate patch 'escape_dollar_only' escapes only '$' (prefix.replace('$', r'\$')) — a plausible partial fix that still passes the hidden test's specific 'form$' scenario and probes 1/2/4, but is REJECTED by probes 3 and 5 (other metachars still active / crash). This demonstrates the suite discriminates wrong implementations; no probe-conforming alternative patch was found.

Req3 (queryset) not probed directly (requires DB/model wiring) but is a thin consumer of _get_edited_object_pks with the same prefix; its faithfulness is fully determined by the probed _get_edited_object_pks behavior. Verdict: SOUND — 5 distinct probes all hold on patched tree, positive control fails at base (discriminating), and the wrong-fix candidate is rejected by the suite.

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
# Req1 AC1 + AC4 (positive control): metacharacter prefix matched literally.
# With prefix 'form$', a key 'form$-0-id' must match; a key that would only
# match if '$' were a regex anchor/metachar must NOT be a false decision.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
        USE_TZ=True)
    django.setup()
from django.contrib.admin.options import ModelAdmin

class F:
    def __init__(s,n): s.name=n
class M:
    def __init__(s,pk): s._meta=type('X',(),{'pk':F(pk)})()
class A:
    def __init__(s,pk='id'): s.model=M(pk)
class P:
    def __init__(s,items): s._i=items
    def items(s): return list(s._i)
class R:
    def __init__(s,items): s.POST=P(items)

def edited(items,prefix,pk='id'):
    return ModelAdmin._get_edited_object_pks(A(pk),R(items),prefix)

# 'form$' with '$' literal: the key that legitimately belongs to this prefix
items=[('form$-0-id','42'),('form$-1-id','43')]
res=edited(items,'form$')
print("prefix 'form$' items result:", res)
ok = res==['42','43']

# A key without the literal '$' must NOT match under prefix 'form$'.
# (If '$' were treated as end-anchor, 'form-0-id' could spuriously match.)
res2=edited([('form-0-id','99')],'form$')
print("prefix 'form$' vs key 'form-0-id':", res2)
ok = ok and res2==[]

import sys
print("HOLDS" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django-12143: gold fix wraps prefix in re.escape() inside _get_edited_object_pks. 5 standalone probes exercise ModelAdmin._get_edited_object_pks directly (DBless, stdlib+django only) via a stub admin/model/request.

Probe->requirement mapping and results (patched / base / weak):
- probe_1 (Req1 AC1+AC4, POSITIVE CONTROL): prefix 'form$' includes 'form$-0-id'/'form$-1-id' and does NOT spuriously match 'form-0-id'. PATCHED=HOLDS, BASE=VIOLATED (base returns [] because '$' is treated as end-anchor => real prepatch bug reproduced), WEAK=HOLDS.
- probe_2 (Req1 AC2, Req2 AC2): qualifying prefix-<digits>-pkname included; empty/non-digit run excluded; pkname anchored at end (form-0-idX excluded); other fields excluded. PATCHED=HOLDS, WEAK=HOLDS.
- probe_3 (Req1 AC3/AC4): '.', '*', '(' , ')' treated literally; anchored at start. PATCHED=HOLDS, WEAK=VIOLATED (fo.m matches form-0-id; x* matches xxxx-0-id).
- probe_4 (Req1 AC5, Req2 AC3): values returned verbatim in POST iteration order; custom pk name 'uuid' honored. PATCHED=HOLDS, WEAK=HOLDS.
- probe_5 (Req1 AC1 comprehensive): each metachar in {$ . * + ? ( ) [ ] { } | ^ \} matches only itself (literal key included, regex-tempting near-miss excluded). PATCHED=HOLDS, WEAK=VIOLATED (raises sre_constants.error 'unterminated subpattern' on '(').

Candidate patch 'escape_dollar_only' escapes only '$' (prefix.replace('$', r'\$')) — a plausible partial fix that still passes the hidden test's specific 'form$' scenario and probes 1/2/4, but is REJECTED by probes 3 and 5 (other metachars still active / crash). This demonstrates the suite discriminates wrong implementations; no probe-conforming alternative patch was found.

Req3 (queryset) not probed directly (requires DB/model wiring) but is a thin consumer of _get_edited_object_pks with the same prefix; its faithfulness is fully determined by the probed _get_edited_object_pks behavior. Verdict: SOUND — 5 distinct probes all hold on patched tree, positive control fails at base (discriminating), and the wrong-fix candidate is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a one-line change wrapping prefix in re.escape() inside _get_edited_object_pks. Requirements pin the changed observable behavior (literal prefix matching regardless of metacharacters) at the correct boundary — the F2P method — rather than a narrow slice, and correctly leave the untouched queryset builder's semantics intact. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior. Verdict FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The problem_statement already quotes the vulnerable line `re.compile(r'{}-\d+-{}$'.format(prefix, self.model._meta.pk.name))`, names the module (admin/options.py), and states the fix (use re.escape). The requirements translate this into behavioral EARS criteria: literal matching of prefix metacharacters, the prefix-hyphen-digits-hyphen-pkname key shape, and queryset construction. Naming `_get_edited_object_pks`/`_get_list_editable_queryset` is legitimate localization. None of the hidden test's identifying artifacts leak: the `form$` prefix, `Swallow` model, `uuid` custom pk field, the specific POST keys (`form$-0-uuid`, `_save`, TOTAL_FORMS), and the `queryset.count()==1` assertion are all absent. The metacharacter list (Req 1.1) is the standard regex-special set, not a case enumeration mirroring parametrized ids (the F2P test is a single non-parametrized case using only `$`). Req 3.3 (unrestricted queryset on invalid pk) reflects the real source method's existing behavior, not a hidden test. Req 2.3 (custom pk name) describes generic pk-name handling, not the test's uuid specifics. No test paths, names, ids, gold-patch verbatim lines beyond the public statement, or fix-invented identifiers are transmitted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
