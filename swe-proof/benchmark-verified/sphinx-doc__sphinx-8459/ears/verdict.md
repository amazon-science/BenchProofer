# P2 adversarial audit — sphinx-doc__sphinx-8459

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
"""Positive control (Req 1.2/1.3/1.4/1.5): description mode + type aliases.

Builds a text doc for a function whose params/return are annotated with a name
that is a key in autodoc_type_aliases. The rendered Parameters and Return type
must show the ALIAS value, not the resolved underlying type.

HOLDS on patched tree; FAILS at base (where description mode ignores aliases).
"""
import os, sys, tempfile, shutil

def build(typehints, aliases):
    src = tempfile.mkdtemp()
    out = tempfile.mkdtemp()
    # target module: use PEP 563 string annotations so 'myint' is a forward ref
    mod = os.path.join(src, "target_mod")
    os.makedirs(mod)
    with open(os.path.join(mod, "__init__.py"), "w") as f:
        f.write(
            "from __future__ import annotations\n"
            "myint = int\n"
            "def add(x: myint, y: myint) -> myint:\n"
            "    '''docstring'''\n"
            "    return x + y\n"
        )
    with open(os.path.join(src, "conf.py"), "w") as f:
        f.write(
            "import os, sys\n"
            "sys.path.insert(0, os.path.abspath('.'))\n"
            "extensions = ['sphinx.ext.autodoc']\n"
            "autodoc_typehints = %r\n"
            "autodoc_type_aliases = %r\n"
            % (typehints, aliases)
        )
    with open(os.path.join(src, "index.rst"), "w") as f:
        f.write(".. autofunction:: target_mod.add\n")
    from sphinx.application import Sphinx
    from sphinx.util.docutils import docutils_namespace
    with docutils_namespace():
        app = Sphinx(src, src, out, os.path.join(out, ".doctree"), "text",
                     freshenv=True, status=None, warning=sys.stderr)
        app.build()
    text = open(os.path.join(out, "index.txt")).read()
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(out, ignore_errors=True)
    return text

text = build("description", {"myint": "myint"})
print("=== rendered text ===")
print(text)

# Parameters should show 'myint' (alias), not 'int'
ok_params = text.count("myint") >= 2
ok_return = "Return type:" in text and "myint" in text.split("Return type:")[1]
no_int = "(*int*)" not in text and not text.split("Return type:")[-1].strip().startswith("int")
print("ok_params:", ok_params, "ok_return:", ok_return, "no_int_leak:", no_int)
if ok_params and ok_return and no_int:
    print("HOLDS")
    sys.exit(0)
print("VIOLATION")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.5: description-mode aliased labels EQUAL signature-mode aliased labels
for the same callable & alias mapping.

Build twice (signature vs description) and compare the alias tokens.
"""
import os, sys, tempfile, shutil, re

def build(typehints, aliases):
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp()
    mod = os.path.join(src, "tmod2"); os.makedirs(mod)
    open(os.path.join(mod, "__init__.py"), "w").write(
        "from __future__ import annotations\n"
        "myint = int\n"
        "def add(x: myint, y: myint) -> myint:\n"
        "    '''docstring'''\n"
        "    return x + y\n")
    open(os.path.join(src, "conf.py"), "w").write(
        "import os, sys\nsys.path.insert(0, os.path.abspath('.'))\n"
        "extensions = ['sphinx.ext.autodoc']\n"
        "autodoc_typehints = %r\nautodoc_type_aliases = %r\n" % (typehints, aliases))
    open(os.path.join(src, "index.rst"), "w").write(".. autofunction:: tmod2.add\n")
    from sphinx.application import Sphinx
    from sphinx.util.docutils import docutils_namespace
    with docutils_namespace():
        app = Sphinx(src, src, out, os.path.join(out, ".doctree"), "text",
                     freshenv=True, status=None, warning=sys.stderr)
        app.build()
    text = open(os.path.join(out, "index.txt")).read()
    shutil.rmtree(src, ignore_errors=True); shutil.rmtree(out, ignore_errors=True)
    return text

sig = build("signature", {"myint": "myint"})
desc = build("description", {"myint": "myint"})
print("=== signature mode ===\n", sig)
print("=== description mode ===\n", desc)

# signature mode: alias appears inline in the sig line "add(x: myint, y: myint) -> myint"
sig_labels = set(re.findall(r"myint", sig))
desc_labels = set(re.findall(r"myint", desc))
sig_has = "myint" in sig
desc_has = desc.count("myint") >= 3  # 2 params + 1 return
# neither should show resolved 'int' token as a type label
print("sig shows alias:", sig_has, "desc shows alias(>=3):", desc_has)
if sig_has and desc_has:
    print("HOLDS"); sys.exit(0)
print("VIOLATION"); sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1 + 2.4 + 1.2/1.3: mixed aliased + non-aliased params via record_typehints.

With autodoc_type_aliases={'myint':'myint'}:
 - aliased params/return record the alias-aware label 'myint' (NOT resolved 'int')
 - a non-aliased param (str) records its default rendering 'str'
 - entries are in declaration order, 'return' key last.
"""
import sys

class FakeConfig:
    autodoc_type_aliases = {"myint": "myint"}
class FakeEnv:
    def __init__(self): self.temp_data = {}
class FakeApp:
    def __init__(self):
        self.config = FakeConfig(); self.env = FakeEnv()

ns = {}
exec("from __future__ import annotations\n"
     "myint = int\n"
     "def fn(x: myint, z: str, y: myint) -> myint:\n    return None\n", ns)
fn = ns["fn"]

from sphinx.ext.autodoc.typehints import record_typehints
app = FakeApp()
record_typehints(app, "function", "mymod.fn", fn, {}, None, None)
ann = app.env.temp_data["annotations"]["mymod.fn"]
keys = list(ann.keys())
print("recorded:", dict(ann), "keys:", keys)

ok_nonalias = ann.get("z") == "str"                       # Req 2.1
ok_alias = ann.get("x") == "myint" and ann.get("y") == "myint" and ann.get("return") == "myint"  # 1.2/1.3
no_resolve = "int" not in {ann.get("x"), ann.get("y"), ann.get("return")}  # not resolved to 'int'
ok_order = keys == ["x", "z", "y", "return"]              # Req 2.4
print("nonalias(str):", ok_nonalias, "alias(myint):", ok_alias,
      "not-resolved-to-int:", no_resolve, "order:", ok_order)
if ok_nonalias and ok_alias and no_resolve and ok_order:
    print("HOLDS"); sys.exit(0)
print("VIOLATION"); sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.2/2.3: no annotation -> no entry; unannotated return -> no 'return' key.

record_typehints must not fabricate type entries for unannotated params or an
unannotated return.
"""
import sys

class FakeConfig:
    autodoc_type_aliases = {"myint": "myint"}
class FakeEnv:
    def __init__(self): self.temp_data = {}
class FakeApp:
    def __init__(self):
        self.config = FakeConfig(); self.env = FakeEnv()

ns = {}
exec(
    "from __future__ import annotations\n"
    "myint = int\n"
    "def fn(a: myint, b, c):\n"   # a annotated; b,c not; no return annotation
    "    return None\n", ns)
fn = ns["fn"]

from sphinx.ext.autodoc.typehints import record_typehints
app = FakeApp()
record_typehints(app, "function", "m.fn", fn, {}, None, None)
ann = app.env.temp_data["annotations"]["m.fn"]
print("recorded:", dict(ann), "keys:", list(ann.keys()))

ok_a = ann.get("a") == "myint"
ok_no_b = "b" not in ann
ok_no_c = "c" not in ann
ok_no_ret = "return" not in ann
print("a recorded:", ok_a, "no b:", ok_no_b, "no c:", ok_no_c, "no return:", ok_no_ret)
if ok_a and ok_no_b and ok_no_c and ok_no_ret:
    print("HOLDS"); sys.exit(0)
print("VIOLATION"); sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.7: description mode, NO aliases configured -> default renderings, and
Req 2.8: signature-introspection error -> record nothing, don't propagate.
"""
import sys

class FakeConfig:
    autodoc_type_aliases = {}
class FakeEnv:
    def __init__(self): self.temp_data = {}
class FakeApp:
    def __init__(self):
        self.config = FakeConfig(); self.env = FakeEnv()

from sphinx.ext.autodoc.typehints import record_typehints

# 2.7: no aliases -> default rendering 'int'
ns = {}
exec("from __future__ import annotations\n"
     "def fn(x: int) -> int:\n    return x\n", ns)
app = FakeApp()
record_typehints(app, "function", "m.fn", ns["fn"], {}, None, None)
ann = app.env.temp_data["annotations"].get("m.fn", {})
print("no-alias annotations:", dict(ann))
ok_default = ann.get("x") == "int" and ann.get("return") == "int"

# 2.8: object whose signature cannot be determined -> no error, record nothing
class Weird:
    pass
bad = Weird()  # callable? no. Use a callable that raises on inspect.
class BadCallable:
    def __call__(self): pass
    @property
    def __signature__(self):
        raise ValueError("cannot determine signature")
bad2 = BadCallable()
app2 = FakeApp()
try:
    record_typehints(app2, "function", "m.bad", bad2, {}, None, None)
    propagated = False
except Exception as e:
    propagated = True
    print("ERROR propagated:", repr(e))
recorded_bad = app2.env.temp_data.get("annotations", {}).get("m.bad")
print("no-alias default ok:", ok_default, "error propagated:", propagated,
      "recorded for bad:", recorded_bad)
# Acceptable: either no annotation entry, or an empty OrderedDict, for bad obj.
ok_err = (not propagated) and (not recorded_bad)
if ok_default and ok_err:
    print("HOLDS"); sys.exit(0)
print("VIOLATION"); sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 2.6: autodoc_typehints='none' -> no type hints in signature OR description,
even with aliases configured.
"""
import os, sys, tempfile, shutil

def build(typehints, aliases):
    src = tempfile.mkdtemp(); out = tempfile.mkdtemp()
    mod = os.path.join(src, "tmod6"); os.makedirs(mod)
    open(os.path.join(mod, "__init__.py"), "w").write(
        "from __future__ import annotations\n"
        "myint = int\n"
        "def add(x: myint, y: myint) -> myint:\n"
        "    '''docstring'''\n    return x + y\n")
    open(os.path.join(src, "conf.py"), "w").write(
        "import os, sys\nsys.path.insert(0, os.path.abspath('.'))\n"
        "extensions = ['sphinx.ext.autodoc']\n"
        "autodoc_typehints = %r\nautodoc_type_aliases = %r\n" % (typehints, aliases))
    open(os.path.join(src, "index.rst"), "w").write(".. autofunction:: tmod6.add\n")
    from sphinx.application import Sphinx
    from sphinx.util.docutils import docutils_namespace
    with docutils_namespace():
        app = Sphinx(src, src, out, os.path.join(out, ".doctree"), "text",
                     freshenv=True, status=None, warning=sys.stderr)
        app.build()
    text = open(os.path.join(out, "index.txt")).read()
    shutil.rmtree(src, ignore_errors=True); shutil.rmtree(out, ignore_errors=True)
    return text

text = build("none", {"myint": "myint"})
print("=== none mode ===\n", text)
no_return_type = "Return type:" not in text
no_alias_label = "myint" not in text
# signature should be add(x, y) with no annotations
print("no 'Return type:':", no_return_type, "no 'myint' label:", no_alias_label)
if no_return_type and no_alias_label:
    print("HOLDS"); sys.exit(0)
print("VIOLATION"); sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 1.2/1.3/1.4/1.5): description mode + type aliases.

Builds a text doc for a function whose params/return are annotated with a name
that is a key in autodoc_type_aliases. The rendered Parameters and Return type
must show the ALIAS value, not the resolved underlying type.

HOLDS on patched tree; FAILS at base (where description mode ignores aliases).
"""
import os, sys, tempfile, shutil

def build(typehints, aliases):
    src = tempfile.mkdtemp()
    out = tempfile.mkdtemp()
    # target module: use PEP 563 string annotations so 'myint' is a forward ref
    mod = os.path.join(src, "target_mod")
    os.makedirs(mod)
    with open(os.path.join(mod, "__init__.py"), "w") as f:
        f.write(
            "from __future__ import annotations\n"
            "myint = int\n"
            "def add(x: myint, y: myint) -> myint:\n"
            "    '''docstring'''\n"
            "    return x + y\n"
        )
    with open(os.path.join(src, "conf.py"), "w") as f:
        f.write(
            "import os, sys\n"
            "sys.path.insert(0, os.path.abspath('.'))\n"
            "extensions = ['sphinx.ext.autodoc']\n"
            "autodoc_typehints = %r\n"
            "autodoc_type_aliases = %r\n"
            % (typehints, aliases)
        )
    with open(os.path.join(src, "index.rst"), "w") as f:
        f.write(".. autofunction:: target_mod.add\n")
    from sphinx.application import Sphinx
    from sphinx.util.docutils import docutils_namespace
    with docutils_namespace():
        app = Sphinx(src, src, out, os.path.join(out, ".doctree"), "text",
                     freshenv=True, status=None, warning=sys.stderr)
        app.build()
    text = open(os.path.join(out, "index.txt")).read()
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(out, ignore_errors=True)
    return text

text = build("description", {"myint": "myint"})
print("=== rendered text ===")
print(text)

# Parameters should show 'myint' (alias), not 'int'
ok_params = text.count("myint") >= 2
ok_return = "Return type:" in text and "myint" in text.split("Return type:")[1]
no_int = "(*int*)" not in text and not text.split("Return type:")[-1].strip().startswith("int")
print("ok_params:", ok_params, "ok_return:", ok_return, "no_int_leak:", no_int)
if ok_params and ok_return and no_int:
    print("HOLDS")
    sys.exit(0)
print("VIOLATION")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8459: gold fix passes type_aliases into inspect.signature() inside record_typehints so description-mode typehints honour autodoc_type_aliases like signature mode.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req 1.2/1.3/1.4/1.5): full text build, autodoc_typehints='description', autodoc_type_aliases={'myint':'myint'}; Parameters show '(*myint*)' and Return type 'myint' with no 'int' leak. HOLDS patched (exit0), FAILS at base (exit1: shows 'int' for params and return) => prepatch_reproduced=True, discriminating.
- probe_2 (Req 1.5): signature-mode vs description-mode both render the alias 'myint' for the same callable/mapping. HOLDS.
- probe_3 (Req 1.2/1.3/2.1/2.4): direct record_typehints call; aliased params x,y and return record 'myint' (not resolved 'int'), non-aliased param z records default 'str', keys in declaration order [x,z,y,return]. HOLDS.
- probe_4 (Req 2.2/2.3): unannotated params b,c produce no entry; unannotated return produces no 'return' key; annotated a recorded as 'myint'. HOLDS.
- probe_5 (Req 2.7/2.8): no aliases -> default 'int' renderings; object whose signature raises -> no error propagated, no annotation recorded (empty OrderedDict). HOLDS.
- probe_6 (Req 2.6): autodoc_typehints='none' with aliases configured -> no 'Return type:' field and no 'myint' label anywhere. HOLDS.

CANDIDATE PATCH exercised & REJECTED (demonstrates discrimination): weak.diff applies type_aliases ONLY to the return annotation, leaving parameter annotations resolved to 'int'. Under weak.diff: probe_1 FAILS (params show int), probe_3 FAILS (x,y='int'), probe_4 FAILS (a='int'); probe_6 still holds. This is the lazy partial fix a weak reading permits and the suite catches it — confirming the requirements as encoded are not too weak on the parameter-substitution criterion.

Note: initial probe_3/probe_4 mis-modeled alias semantics (expected value-substitution); corrected after empirically confirming the mechanism uses type_aliases as get_type_hints localns so the alias KEY name is preserved (e.g. {'myint':'myint'} keeps label 'myint' rather than resolving to 'int'). This matches the hidden test's confoverride {'myint':'myint'}.

All 6 probes hold on patched; positive control discriminates base vs patched; wrong-fix candidate rejected. Verdict SOUND.

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
"""Positive control (Req 1.2/1.3/1.4/1.5): description mode + type aliases.

Builds a text doc for a function whose params/return are annotated with a name
that is a key in autodoc_type_aliases. The rendered Parameters and Return type
must show the ALIAS value, not the resolved underlying type.

HOLDS on patched tree; FAILS at base (where description mode ignores aliases).
"""
import os, sys, tempfile, shutil

def build(typehints, aliases):
    src = tempfile.mkdtemp()
    out = tempfile.mkdtemp()
    # target module: use PEP 563 string annotations so 'myint' is a forward ref
    mod = os.path.join(src, "target_mod")
    os.makedirs(mod)
    with open(os.path.join(mod, "__init__.py"), "w") as f:
        f.write(
            "from __future__ import annotations\n"
            "myint = int\n"
            "def add(x: myint, y: myint) -> myint:\n"
            "    '''docstring'''\n"
            "    return x + y\n"
        )
    with open(os.path.join(src, "conf.py"), "w") as f:
        f.write(
            "import os, sys\n"
            "sys.path.insert(0, os.path.abspath('.'))\n"
            "extensions = ['sphinx.ext.autodoc']\n"
            "autodoc_typehints = %r\n"
            "autodoc_type_aliases = %r\n"
            % (typehints, aliases)
        )
    with open(os.path.join(src, "index.rst"), "w") as f:
        f.write(".. autofunction:: target_mod.add\n")
    from sphinx.application import Sphinx
    from sphinx.util.docutils import docutils_namespace
    with docutils_namespace():
        app = Sphinx(src, src, out, os.path.join(out, ".doctree"), "text",
                     freshenv=True, status=None, warning=sys.stderr)
        app.build()
    text = open(os.path.join(out, "index.txt")).read()
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(out, ignore_errors=True)
    return text

text = build("description", {"myint": "myint"})
print("=== rendered text ===")
print(text)

# Parameters should show 'myint' (alias), not 'int'
ok_params = text.count("myint") >= 2
ok_return = "Return type:" in text and "myint" in text.split("Return type:")[1]
no_int = "(*int*)" not in text and not text.split("Return type:")[-1].strip().startswith("int")
print("ok_params:", ok_params, "ok_return:", ok_return, "no_int_leak:", no_int)
if ok_params and ok_return and no_int:
    print("HOLDS")
    sys.exit(0)
print("VIOLATION")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8459: gold fix passes type_aliases into inspect.signature() inside record_typehints so description-mode typehints honour autodoc_type_aliases like signature mode.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req 1.2/1.3/1.4/1.5): full text build, autodoc_typehints='description', autodoc_type_aliases={'myint':'myint'}; Parameters show '(*myint*)' and Return type 'myint' with no 'int' leak. HOLDS patched (exit0), FAILS at base (exit1: shows 'int' for params and return) => prepatch_reproduced=True, discriminating.
- probe_2 (Req 1.5): signature-mode vs description-mode both render the alias 'myint' for the same callable/mapping. HOLDS.
- probe_3 (Req 1.2/1.3/2.1/2.4): direct record_typehints call; aliased params x,y and return record 'myint' (not resolved 'int'), non-aliased param z records default 'str', keys in declaration order [x,z,y,return]. HOLDS.
- probe_4 (Req 2.2/2.3): unannotated params b,c produce no entry; unannotated return produces no 'return' key; annotated a recorded as 'myint'. HOLDS.
- probe_5 (Req 2.7/2.8): no aliases -> default 'int' renderings; object whose signature raises -> no error propagated, no annotation recorded (empty OrderedDict). HOLDS.
- probe_6 (Req 2.6): autodoc_typehints='none' with aliases configured -> no 'Return type:' field and no 'myint' label anywhere. HOLDS.

CANDIDATE PATCH exercised & REJECTED (demonstrates discrimination): weak.diff applies type_aliases ONLY to the return annotation, leaving parameter annotations resolved to 'int'. Under weak.diff: probe_1 FAILS (params show int), probe_3 FAILS (x,y='int'), probe_4 FAILS (a='int'); probe_6 still holds. This is the lazy partial fix a weak reading permits and the suite catches it — confirming the requirements as encoded are not too weak on the parameter-substitution criterion.

Note: initial probe_3/probe_4 mis-modeled alias semantics (expected value-substitution); corrected after empirically confirming the mechanism uses type_aliases as get_type_hints localns so the alias KEY name is preserved (e.g. {'myint':'myint'} keeps label 'myint' rather than resolving to 'int'). This matches the hidden test's confoverride {'myint':'myint'}.

All 6 probes hold on patched; positive control discriminates base vs patched; wrong-fix candidate rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Confirmed base tree uses inspect.signature(obj) without type_aliases (no alias applied), patched tree adds type_aliases=app.config.autodoc_type_aliases. Requirements correctly model the biconditional: alias present → substituted label, absent → default. Boundary is correct (both params AND return, not a single branch).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior at the appropriate abstraction level and do not transmit hidden-test or gold-edit content. Module/function localization (sphinx/ext/autodoc/typehints.py, record_typehints, autodoc-process-signature, inspect.signature, type_aliases mapping) is legitimate and largely derivable from the public problem_statement's reproduction; naming the change site is required, not a leak. None of the hidden-test specifics appear: the test's alias key 'myint', the target function target.annotations.sum, parameters x/y, the text-builder expected output block, and the test name/path (tests/test_ext_autodoc_configs.py::test_autodoc_typehints_description_and_type_aliases) are all absent. The gold one-liner (passing type_aliases=app.config.autodoc_type_aliases into inspect.signature) is described as a behavioral requirement (resolve annotations via the alias mapping before storing labels), not quoted. Case enumerations (signature/description/none modes; alias present vs absent) track the public config option's documented values and the bug report, not the test parametrization (which is a single case). Req 2.4's declaration-order/return-key wording describes the pre-existing recording data structure, not test assertions.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
