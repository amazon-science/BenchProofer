# P2 adversarial audit — sphinx-doc__sphinx-10449

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.2 (POSITIVE CONTROL): class with return annotation 'None' under
# target="all" must NOT get an rtype field.
import types
from docutils import nodes
from sphinx import addnodes
from sphinx.ext.autodoc.typehints import merge_typehints


def run(objtype, annotations, target="all", typehints="description",
        prefields=None, fullname="mod.Obj"):
    sig = addnodes.desc_signature()
    sig['module'] = 'mod'
    sig['fullname'] = fullname.split('.', 1)[1] if '.' in fullname else fullname
    content = addnodes.desc_content()
    if prefields:
        fl = nodes.field_list()
        for fname, fbody in prefields:
            f = nodes.field()
            f += nodes.field_name('', fname)
            f += nodes.field_body('', nodes.paragraph('', fbody))
            fl += f
        content += fl
    desc = addnodes.desc()
    desc += sig
    desc += content
    cfg = types.SimpleNamespace(
        autodoc_typehints=typehints,
        autodoc_typehints_description_target=target,
        autodoc_typehints_format='fully-qualified')
    env = types.SimpleNamespace(temp_data={'annotations': {fullname: dict(annotations)}})
    app = types.SimpleNamespace(config=cfg, env=env)
    merge_typehints(app, 'py', objtype, content)
    return content


def fields(content):
    out = []
    for fl in content:
        if isinstance(fl, nodes.field_list):
            for f in fl:
                out.append((f[0].astext(), f[1].astext()))
    return out


c = run('class', {'x': 'int', 'return': 'None'})
fs = fields(c)
print("class None-return fields:", fs)
names = [n for n, _ in fs]
rtypes = [n for n in names if n == 'rtype']
if rtypes:
    print("FAIL: rtype emitted for class with None return")
    raise SystemExit(1)
print("PASS: no rtype for class None return")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2 (POSITIVE CONTROL): class with return annotation 'None' under
# target="all" must NOT get an rtype field.
import types
from docutils import nodes
from sphinx import addnodes
from sphinx.ext.autodoc.typehints import merge_typehints


def run(objtype, annotations, target="all", typehints="description",
        prefields=None, fullname="mod.Obj"):
    sig = addnodes.desc_signature()
    sig['module'] = 'mod'
    sig['fullname'] = fullname.split('.', 1)[1] if '.' in fullname else fullname
    content = addnodes.desc_content()
    if prefields:
        fl = nodes.field_list()
        for fname, fbody in prefields:
            f = nodes.field()
            f += nodes.field_name('', fname)
            f += nodes.field_body('', nodes.paragraph('', fbody))
            fl += f
        content += fl
    desc = addnodes.desc()
    desc += sig
    desc += content
    cfg = types.SimpleNamespace(
        autodoc_typehints=typehints,
        autodoc_typehints_description_target=target,
        autodoc_typehints_format='fully-qualified')
    env = types.SimpleNamespace(temp_data={'annotations': {fullname: dict(annotations)}})
    app = types.SimpleNamespace(config=cfg, env=env)
    merge_typehints(app, 'py', objtype, content)
    return content


def fields(content):
    out = []
    for fl in content:
        if isinstance(fl, nodes.field_list):
            for f in fl:
                out.append((f[0].astext(), f[1].astext()))
    return out


# Req 1.3 / 3.1: class with None return still emits type+param fields for params.
c = run('class', {'x': 'int', 'y': 'str', 'return': 'None'})
fs = fields(c); names=[n for n,_ in fs]
print("fields:", fs)
need = {'type x','param x','type y','param y'}
if not need.issubset(set(names)):
    print("FAIL: missing param/type fields", need - set(names)); raise SystemExit(1)
if 'rtype' in names:
    print("FAIL: rtype present"); raise SystemExit(1)
# check bodies
d=dict(fs)
if d['type x']!='int' or d['type y']!='str':
    print("FAIL: wrong type bodies"); raise SystemExit(1)
print("PASS"); raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.2 (POSITIVE CONTROL): class with return annotation 'None' under
# target="all" must NOT get an rtype field.
import types
from docutils import nodes
from sphinx import addnodes
from sphinx.ext.autodoc.typehints import merge_typehints


def run(objtype, annotations, target="all", typehints="description",
        prefields=None, fullname="mod.Obj"):
    sig = addnodes.desc_signature()
    sig['module'] = 'mod'
    sig['fullname'] = fullname.split('.', 1)[1] if '.' in fullname else fullname
    content = addnodes.desc_content()
    if prefields:
        fl = nodes.field_list()
        for fname, fbody in prefields:
            f = nodes.field()
            f += nodes.field_name('', fname)
            f += nodes.field_body('', nodes.paragraph('', fbody))
            fl += f
        content += fl
    desc = addnodes.desc()
    desc += sig
    desc += content
    cfg = types.SimpleNamespace(
        autodoc_typehints=typehints,
        autodoc_typehints_description_target=target,
        autodoc_typehints_format='fully-qualified')
    env = types.SimpleNamespace(temp_data={'annotations': {fullname: dict(annotations)}})
    app = types.SimpleNamespace(config=cfg, env=env)
    merge_typehints(app, 'py', objtype, content)
    return content


def fields(content):
    out = []
    for fl in content:
        if isinstance(fl, nodes.field_list):
            for f in fl:
                out.append((f[0].astext(), f[1].astext()))
    return out


# Req 1.4: class with NON-None return annotation DOES emit rtype with that body.
c = run('class', {'x':'int','return':'Foo'})
fs=fields(c); d=dict(fs)
print("fields:", fs)
if d.get('rtype')!='Foo':
    print("FAIL: expected rtype=Foo, got", d.get('rtype')); raise SystemExit(1)
print("PASS"); raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 1.2 (POSITIVE CONTROL): class with return annotation 'None' under
# target="all" must NOT get an rtype field.
import types
from docutils import nodes
from sphinx import addnodes
from sphinx.ext.autodoc.typehints import merge_typehints


def run(objtype, annotations, target="all", typehints="description",
        prefields=None, fullname="mod.Obj"):
    sig = addnodes.desc_signature()
    sig['module'] = 'mod'
    sig['fullname'] = fullname.split('.', 1)[1] if '.' in fullname else fullname
    content = addnodes.desc_content()
    if prefields:
        fl = nodes.field_list()
        for fname, fbody in prefields:
            f = nodes.field()
            f += nodes.field_name('', fname)
            f += nodes.field_body('', nodes.paragraph('', fbody))
            fl += f
        content += fl
    desc = addnodes.desc()
    desc += sig
    desc += content
    cfg = types.SimpleNamespace(
        autodoc_typehints=typehints,
        autodoc_typehints_description_target=target,
        autodoc_typehints_format='fully-qualified')
    env = types.SimpleNamespace(temp_data={'annotations': {fullname: dict(annotations)}})
    app = types.SimpleNamespace(config=cfg, env=env)
    merge_typehints(app, 'py', objtype, content)
    return content


def fields(content):
    out = []
    for fl in content:
        if isinstance(fl, nodes.field_list):
            for f in fl:
                out.append((f[0].astext(), f[1].astext()))
    return out


# Req 2.1: NON-class object (function) with None return DOES emit rtype None.
c = run('function', {'x':'int','return':'None'})
fs=fields(c); d=dict(fs)
print("function None-return fields:", fs)
if d.get('rtype')!='None':
    print("FAIL: function should keep rtype=None, got", d.get('rtype')); raise SystemExit(1)
print("PASS"); raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 1.2 (POSITIVE CONTROL): class with return annotation 'None' under
# target="all" must NOT get an rtype field.
import types
from docutils import nodes
from sphinx import addnodes
from sphinx.ext.autodoc.typehints import merge_typehints


def run(objtype, annotations, target="all", typehints="description",
        prefields=None, fullname="mod.Obj"):
    sig = addnodes.desc_signature()
    sig['module'] = 'mod'
    sig['fullname'] = fullname.split('.', 1)[1] if '.' in fullname else fullname
    content = addnodes.desc_content()
    if prefields:
        fl = nodes.field_list()
        for fname, fbody in prefields:
            f = nodes.field()
            f += nodes.field_name('', fname)
            f += nodes.field_body('', nodes.paragraph('', fbody))
            fl += f
        content += fl
    desc = addnodes.desc()
    desc += sig
    desc += content
    cfg = types.SimpleNamespace(
        autodoc_typehints=typehints,
        autodoc_typehints_description_target=target,
        autodoc_typehints_format='fully-qualified')
    env = types.SimpleNamespace(temp_data={'annotations': {fullname: dict(annotations)}})
    app = types.SimpleNamespace(config=cfg, env=env)
    merge_typehints(app, 'py', objtype, content)
    return content


def fields(content):
    out = []
    for fl in content:
        if isinstance(fl, nodes.field_list):
            for f in fl:
                out.append((f[0].astext(), f[1].astext()))
    return out


# Req 3.2: if rtype already declared, do NOT append another (even non-class non-None).
c = run('method', {'x':'int','return':'Bar'}, prefields=[('rtype','Existing')])
fs=fields(c); names=[n for n,_ in fs]
print("fields:", fs)
if names.count('rtype')!=1:
    print("FAIL: rtype count", names.count('rtype')); raise SystemExit(1)
if dict(fs)['rtype']!='Existing':
    print("FAIL: existing rtype overwritten"); raise SystemExit(1)
print("PASS"); raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 1.2 (POSITIVE CONTROL): class with return annotation 'None' under
# target="all" must NOT get an rtype field.
import types
from docutils import nodes
from sphinx import addnodes
from sphinx.ext.autodoc.typehints import merge_typehints


def run(objtype, annotations, target="all", typehints="description",
        prefields=None, fullname="mod.Obj"):
    sig = addnodes.desc_signature()
    sig['module'] = 'mod'
    sig['fullname'] = fullname.split('.', 1)[1] if '.' in fullname else fullname
    content = addnodes.desc_content()
    if prefields:
        fl = nodes.field_list()
        for fname, fbody in prefields:
            f = nodes.field()
            f += nodes.field_name('', fname)
            f += nodes.field_body('', nodes.paragraph('', fbody))
            fl += f
        content += fl
    desc = addnodes.desc()
    desc += sig
    desc += content
    cfg = types.SimpleNamespace(
        autodoc_typehints=typehints,
        autodoc_typehints_description_target=target,
        autodoc_typehints_format='fully-qualified')
    env = types.SimpleNamespace(temp_data={'annotations': {fullname: dict(annotations)}})
    app = types.SimpleNamespace(config=cfg, env=env)
    merge_typehints(app, 'py', objtype, content)
    return content


def fields(content):
    out = []
    for fl in content:
        if isinstance(fl, nodes.field_list):
            for f in fl:
                out.append((f[0].astext(), f[1].astext()))
    return out


# Req 3.3: documented_params/force_rtype mode unaffected by class suppression:
# a CLASS with non-None return under target=documented_params must still get rtype.
c = run('class', {'x':'int','return':'Baz'}, target='documented_params')
fs=fields(c); d=dict(fs)
print("documented_params class fields:", fs)
if d.get('rtype')!='Baz':
    print("FAIL: force_rtype should emit rtype=Baz, got", d.get('rtype')); raise SystemExit(1)
print("PASS"); raise SystemExit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 1.2 (POSITIVE CONTROL): class with return annotation 'None' under
# target="all" must NOT get an rtype field.
import types
from docutils import nodes
from sphinx import addnodes
from sphinx.ext.autodoc.typehints import merge_typehints


def run(objtype, annotations, target="all", typehints="description",
        prefields=None, fullname="mod.Obj"):
    sig = addnodes.desc_signature()
    sig['module'] = 'mod'
    sig['fullname'] = fullname.split('.', 1)[1] if '.' in fullname else fullname
    content = addnodes.desc_content()
    if prefields:
        fl = nodes.field_list()
        for fname, fbody in prefields:
            f = nodes.field()
            f += nodes.field_name('', fname)
            f += nodes.field_body('', nodes.paragraph('', fbody))
            fl += f
        content += fl
    desc = addnodes.desc()
    desc += sig
    desc += content
    cfg = types.SimpleNamespace(
        autodoc_typehints=typehints,
        autodoc_typehints_description_target=target,
        autodoc_typehints_format='fully-qualified')
    env = types.SimpleNamespace(temp_data={'annotations': {fullname: dict(annotations)}})
    app = types.SimpleNamespace(config=cfg, env=env)
    merge_typehints(app, 'py', objtype, content)
    return content


def fields(content):
    out = []
    for fl in content:
        if isinstance(fl, nodes.field_list):
            for f in fl:
                out.append((f[0].astext(), f[1].astext()))
    return out


# Req 3.5: appended rtype body must be the RETURN annotation, not a stale param value.
c = run('function', {'aaa':'ParamType','return':'RetType'})
fs=fields(c); d=dict(fs)
print("fields:", fs)
if d.get('rtype')!='RetType':
    print("FAIL: rtype body stale/wrong:", d.get('rtype')); raise SystemExit(1)
print("PASS"); raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.2 (POSITIVE CONTROL): class with return annotation 'None' under
# target="all" must NOT get an rtype field.
import types
from docutils import nodes
from sphinx import addnodes
from sphinx.ext.autodoc.typehints import merge_typehints


def run(objtype, annotations, target="all", typehints="description",
        prefields=None, fullname="mod.Obj"):
    sig = addnodes.desc_signature()
    sig['module'] = 'mod'
    sig['fullname'] = fullname.split('.', 1)[1] if '.' in fullname else fullname
    content = addnodes.desc_content()
    if prefields:
        fl = nodes.field_list()
        for fname, fbody in prefields:
            f = nodes.field()
            f += nodes.field_name('', fname)
            f += nodes.field_body('', nodes.paragraph('', fbody))
            fl += f
        content += fl
    desc = addnodes.desc()
    desc += sig
    desc += content
    cfg = types.SimpleNamespace(
        autodoc_typehints=typehints,
        autodoc_typehints_description_target=target,
        autodoc_typehints_format='fully-qualified')
    env = types.SimpleNamespace(temp_data={'annotations': {fullname: dict(annotations)}})
    app = types.SimpleNamespace(config=cfg, env=env)
    merge_typehints(app, 'py', objtype, content)
    return content


def fields(content):
    out = []
    for fl in content:
        if isinstance(fl, nodes.field_list):
            for f in fl:
                out.append((f[0].astext(), f[1].astext()))
    return out


c = run('class', {'x': 'int', 'return': 'None'})
fs = fields(c)
print("class None-return fields:", fs)
names = [n for n, _ in fs]
rtypes = [n for n in names if n == 'rtype']
if rtypes:
    print("FAIL: rtype emitted for class with None return")
    raise SystemExit(1)
print("PASS: no rtype for class None return")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

All 7 probes drive merge_typehints on a crafted desc node tree (stdlib+docutils+sphinx repo pkg; no pytest).

Probe->requirement mapping and results (patched tree):
- probe_1 (Req 1.2, POSITIVE CONTROL): class + return='None', target='all' => no rtype. HOLDS patched, FAILED at base (base emitted rtype=None). Discriminates.
- probe_2 (Req 1.3/3.1): class None-return still emits type/param fields for each param with correct bodies, no rtype. HOLDS.
- probe_3 (Req 1.4): class with non-None return ('Foo') still emits rtype=Foo. HOLDS.
- probe_4 (Req 2.1): function (non-class) with return='None' KEEPS rtype=None. HOLDS.
- probe_5 (Req 3.2): pre-existing rtype field => no duplicate appended, original preserved. HOLDS.
- probe_6 (Req 3.3): documented_params/force_rtype mode unaffected by class suppression; class non-None return still gets rtype=Baz. HOLDS.
- probe_7 (Req 3.5): appended rtype body is the return annotation, not a stale param value. HOLDS.

Wrong-fix candidate 'drop_all_None_rtype' (weak.diff): suppresses None rtype in modify_field_list for ALL objtypes (lazy reading ignoring the class-only boundary). REJECTED by probe_4 (function lost its rtype=None), while probe_1 still passed under it. Demonstrates the suite discriminates the wrong implementation permitted by a weak reading of Req 2.1.

All needed runs completed. >=5 distinct probes hold on patched; positive control fails at base and holds patched; >=1 candidate exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.2 (POSITIVE CONTROL): class with return annotation 'None' under
# target="all" must NOT get an rtype field.
import types
from docutils import nodes
from sphinx import addnodes
from sphinx.ext.autodoc.typehints import merge_typehints


def run(objtype, annotations, target="all", typehints="description",
        prefields=None, fullname="mod.Obj"):
    sig = addnodes.desc_signature()
    sig['module'] = 'mod'
    sig['fullname'] = fullname.split('.', 1)[1] if '.' in fullname else fullname
    content = addnodes.desc_content()
    if prefields:
        fl = nodes.field_list()
        for fname, fbody in prefields:
            f = nodes.field()
            f += nodes.field_name('', fname)
            f += nodes.field_body('', nodes.paragraph('', fbody))
            fl += f
        content += fl
    desc = addnodes.desc()
    desc += sig
    desc += content
    cfg = types.SimpleNamespace(
        autodoc_typehints=typehints,
        autodoc_typehints_description_target=target,
        autodoc_typehints_format='fully-qualified')
    env = types.SimpleNamespace(temp_data={'annotations': {fullname: dict(annotations)}})
    app = types.SimpleNamespace(config=cfg, env=env)
    merge_typehints(app, 'py', objtype, content)
    return content


def fields(content):
    out = []
    for fl in content:
        if isinstance(fl, nodes.field_list):
            for f in fl:
                out.append((f[0].astext(), f[1].astext()))
    return out


c = run('class', {'x': 'int', 'return': 'None'})
fs = fields(c)
print("class None-return fields:", fs)
names = [n for n, _ in fs]
rtypes = [n for n in names if n == 'rtype']
if rtypes:
    print("FAIL: rtype emitted for class with None return")
    raise SystemExit(1)
print("PASS: no rtype for class None return")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

All 7 probes drive merge_typehints on a crafted desc node tree (stdlib+docutils+sphinx repo pkg; no pytest).

Probe->requirement mapping and results (patched tree):
- probe_1 (Req 1.2, POSITIVE CONTROL): class + return='None', target='all' => no rtype. HOLDS patched, FAILED at base (base emitted rtype=None). Discriminates.
- probe_2 (Req 1.3/3.1): class None-return still emits type/param fields for each param with correct bodies, no rtype. HOLDS.
- probe_3 (Req 1.4): class with non-None return ('Foo') still emits rtype=Foo. HOLDS.
- probe_4 (Req 2.1): function (non-class) with return='None' KEEPS rtype=None. HOLDS.
- probe_5 (Req 3.2): pre-existing rtype field => no duplicate appended, original preserved. HOLDS.
- probe_6 (Req 3.3): documented_params/force_rtype mode unaffected by class suppression; class non-None return still gets rtype=Baz. HOLDS.
- probe_7 (Req 3.5): appended rtype body is the return annotation, not a stale param value. HOLDS.

Wrong-fix candidate 'drop_all_None_rtype' (weak.diff): suppresses None rtype in modify_field_list for ALL objtypes (lazy reading ignoring the class-only boundary). REJECTED by probe_4 (function lost its rtype=None), while probe_1 still passed under it. Demonstrates the suite discriminates the wrong implementation permitted by a weak reading of Req 2.1.

All needed runs completed. >=5 distinct probes hold on patched; positive control fails at base and holds patched; >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** R1.1-1.4: class + autodoc_typehints_description_target=='all' + recorded return 'None' -> no rtype field; non-'None' return still emits rtype; params untouched because suppression sits after the param loop -> matches patched code. R2.1-2.2: non-class objects take the else branch (no suppress_rtype), so a 'None' return still yields rtype -> matches. R3.1-3.6: 'documented_params' (force_rtype=True) and default (force_rtype=False) route through augment_descriptions_with_types, which the patch does NOT touch and which is unaffected by class suppression; verified its force_rtype/has_description/rtype!='None' logic is unchanged from base. R3.5 ('not a stale value') is exactly the added `annotation = annotations['return']` line — base code reused the leftover loop-variable `annotation`; the patch rebinds it. 'signature'/'none' paths untouched. Modeling boundary is correct and biconditional: it pins the changed observable behavior (class AND return=='None' under 'all' <=> suppress rtype) rather than a narrow slice, and explicitly preserves non-class and other-mode rendering. Base vs patched probes confirm the only behavioral delta is the class-None-rtype suppression. F2P test: test_autodoc_typehints_description_with_documented_init.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements localize the change to public module functions (merge_typehints, modify_field_list in sphinx/ext/autodoc/typehints.py) — legitimate. The core F2P behavior (suppress spurious 'Return type: None' for a class under autodoc_typehints='description') is exactly the public problem_statement's expected behavior. The fix-invented identifier `suppress_rtype` is NOT mentioned. No test names/paths/ids, no quoted test or gold code. Requirement 3.6's enumeration ('signature', 'none', overloads, type aliases, fully-qualified formatting, autoclass_content class/init/both) coincides with PASS_TO_PASS test names, but each item is a publicly documented Sphinx config knob/feature; this describes regression scope over public API rather than reconstructing the hidden test parametrization. The three description-target modes ('all'/'documented_params'/default) track code branches and the public autodoc_typehints_description_target config, not test cases. Behavioral translation, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
