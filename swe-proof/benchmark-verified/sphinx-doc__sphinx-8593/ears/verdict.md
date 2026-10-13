# P2 adversarial audit — sphinx-doc__sphinx-8593

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
"""POSITIVE CONTROL / Requirement 2.1 & 2.2:
When a module is documented with all members requested and an underscore-named
module variable is documented ':meta public:', that variable SHALL appear as a
data member, reporting its module and value and retaining the :meta public:
field.

Holds on patched tree; must FAIL at base (data members ignored :meta before fix).
"""
import sys, os

def build_and_autodoc(options, module_body):
    sys.path.insert(0, '/testbed/tests')
    os.chdir('/testbed')
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as sphinx_path
    from test_ext_autodoc import do_autodoc
    root = '/testbed/tests/roots/test-ext-autodoc'
    modname = 'target._probe_mod'
    modpath = os.path.join(root, 'target', '_probe_mod.py')
    with open(modpath, 'w') as f:
        f.write(module_body)
    app = SphinxTestApp('dummy', srcdir=sphinx_path(root))
    try:
        return list(do_autodoc(app, 'module', modname, options))
    finally:
        app.cleanup()
        try: os.remove(modpath)
        except OSError: pass
        sys.modules.pop(modname, None)

MODULE = (
    "_PUBLIC_CONSTANT = None  #: :meta public:\n"
)

out = build_and_autodoc({"members": None}, MODULE)
print("OUTPUT:")
for l in out:
    print(repr(l))

joined = "\n".join(out)
ok = (".. py:data:: _PUBLIC_CONSTANT" in joined
      and ":module: target._probe_mod" in joined
      and ":value: None" in joined
      and ":meta public:" in joined)
# ensure the data-block for _PUBLIC_CONSTANT specifically carries module & value & meta
present = ".. py:data:: _PUBLIC_CONSTANT" in joined
print("present:", present, "criterion:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 3.1:
When all members requested with default visibility, a module-level variable
documented ':meta private:' SHALL NOT appear in the output, even though its
name does not begin with an underscore.
"""
import sys, os

def build_and_autodoc(options, module_body):
    sys.path.insert(0, '/testbed/tests')
    os.chdir('/testbed')
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as sphinx_path
    from test_ext_autodoc import do_autodoc
    root = '/testbed/tests/roots/test-ext-autodoc'
    modname = 'target._probe_mod'
    modpath = os.path.join(root, 'target', '_probe_mod.py')
    with open(modpath, 'w') as f:
        f.write(module_body)
    app = SphinxTestApp('dummy', srcdir=sphinx_path(root))
    try:
        return list(do_autodoc(app, 'module', modname, options))
    finally:
        app.cleanup()
        try: os.remove(modpath)
        except OSError: pass
        sys.modules.pop(modname, None)

MODULE = (
    "PRIVATE_CONSTANT = None  #: :meta private:\n"
    "NORMAL_CONSTANT = 1  #: an ordinary public constant\n"
)

out = build_and_autodoc({"members": None}, MODULE)
print("OUTPUT:")
for l in out:
    print(repr(l))
joined = "\n".join(out)
hidden = ".. py:data:: PRIVATE_CONSTANT" not in joined
# sanity: the ordinary public var IS shown (so we know docs were generated)
normal_shown = ".. py:data:: NORMAL_CONSTANT" in joined
print("PRIVATE_CONSTANT hidden:", hidden, "NORMAL shown:", normal_shown)
sys.exit(0 if (hidden and normal_shown) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 3.2 & 4.1 & 4.2:
When private members are explicitly requested (private-members naming the var),
a ':meta private:' module variable AND a ':meta public:' underscore variable
covered by the request SHALL be included as data members, reporting module,
value and retaining their :meta field.
Mirrors the F2P test_private_members / test_private_field_and_private_members.
"""
import sys, os

def build_and_autodoc(options, module_body):
    sys.path.insert(0, '/testbed/tests')
    os.chdir('/testbed')
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as sphinx_path
    from test_ext_autodoc import do_autodoc
    root = '/testbed/tests/roots/test-ext-autodoc'
    modname = 'target._probe_mod'
    modpath = os.path.join(root, 'target', '_probe_mod.py')
    with open(modpath, 'w') as f:
        f.write(module_body)
    app = SphinxTestApp('dummy', srcdir=sphinx_path(root))
    try:
        return list(do_autodoc(app, 'module', modname, options))
    finally:
        app.cleanup()
        try: os.remove(modpath)
        except OSError: pass
        sys.modules.pop(modname, None)

MODULE = (
    "PRIVATE_CONSTANT = None  #: :meta private:\n"
    "_PUBLIC_CONSTANT = None  #: :meta public:\n"
)

# private-members requested generally (None => ALL private members)
out = build_and_autodoc({"members": None, "private-members": None}, MODULE)
print("OUTPUT:")
for l in out:
    print(repr(l))
joined = "\n".join(out)

def has_data_block(name, meta):
    # find the data:: name line, then check module/value/meta appear after it
    marker = ".. py:data:: %s" % name
    i = joined.find(marker)
    if i < 0:
        return False
    seg = joined[i:i+200]
    return (":module: target._probe_mod" in seg and ":value: None" in seg and meta in seg)

priv_ok = has_data_block("PRIVATE_CONSTANT", ":meta private:")
pub_ok = has_data_block("_PUBLIC_CONSTANT", ":meta public:")
print("PRIVATE_CONSTANT block ok:", priv_ok, "_PUBLIC_CONSTANT block ok:", pub_ok)
sys.exit(0 if (priv_ok and pub_ok) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 5.5 & 4.3 (preserve existing collection behavior):
When an explicit list of member names is requested, collection returns, in the
requested order, the entry for each requested name that exists; a requested
name that does not exist on the module is omitted.
"""
import sys, os

def build_and_autodoc(options, module_body):
    sys.path.insert(0, '/testbed/tests')
    os.chdir('/testbed')
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as sphinx_path
    from test_ext_autodoc import do_autodoc
    root = '/testbed/tests/roots/test-ext-autodoc'
    modname = 'target._probe_mod'
    modpath = os.path.join(root, 'target', '_probe_mod.py')
    with open(modpath, 'w') as f:
        f.write(module_body)
    app = SphinxTestApp('dummy', srcdir=sphinx_path(root))
    try:
        return list(do_autodoc(app, 'module', modname, options))
    finally:
        app.cleanup()
        try: os.remove(modpath)
        except OSError: pass
        sys.modules.pop(modname, None)

MODULE = (
    "ALPHA = 1  #: alpha var\n"
    "BETA = 2   #: beta var\n"
    "GAMMA = 3  #: gamma var\n"
)

# request BETA and ALPHA plus a nonexistent name; GAMMA not requested.
# (Render order is set by member-order, not by the collected order, so we only
#  assert MEMBERSHIP: requested-existing present, others absent.)
out = build_and_autodoc({"members": "BETA,ALPHA,DOES_NOT_EXIST"}, MODULE)
joined = "\n".join(out)

iB = joined.find(".. py:data:: BETA")
iA = joined.find(".. py:data:: ALPHA")
iG = joined.find(".. py:data:: GAMMA")
iN = joined.find("DOES_NOT_EXIST")
beta_present = iB >= 0
alpha_present = iA >= 0
gamma_absent = iG < 0                                # not requested -> absent
missing_absent = iN < 0                              # nonexistent -> omitted
ok = beta_present and alpha_present and gamma_absent and missing_absent
print("beta_present:", beta_present, "alpha_present:", alpha_present,
      "gamma_absent:", gamma_absent, "missing_omitted:", missing_absent, "OK:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 5.1 & 5.2 (preserve existing behavior — annotation-only members):
Collection includes one additional entry for every annotation-only member (a
name with a declared type but no bound value); its entry is the annotation-only
sentinel rather than a concrete value, so it is documented WITHOUT a :value:.
"""
import sys, os

def build_and_autodoc(options, module_body):
    sys.path.insert(0, '/testbed/tests')
    os.chdir('/testbed')
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as sphinx_path
    from test_ext_autodoc import do_autodoc
    root = '/testbed/tests/roots/test-ext-autodoc'
    modname = 'target._probe_mod'
    modpath = os.path.join(root, 'target', '_probe_mod.py')
    with open(modpath, 'w') as f:
        f.write(module_body)
    app = SphinxTestApp('dummy', srcdir=sphinx_path(root))
    try:
        return list(do_autodoc(app, 'module', modname, options))
    finally:
        app.cleanup()
        try: os.remove(modpath)
        except OSError: pass
        sys.modules.pop(modname, None)

# CONCRETE has a value; ANNONLY is annotation-only (declared type, no value)
MODULE = (
    "CONCRETE = 5  #: a concrete value\n"
    "ANNONLY: int  #: annotation only\n"
)

out = build_and_autodoc({"members": None}, MODULE)
joined = "\n".join(out)

# annotation-only member is collected/emitted, marked with the annotation-only
# sentinel => it gets a :type: but NO concrete :value:.
i_ann = joined.find(".. py:data:: ANNONLY")
ann_present = i_ann >= 0
# bound the ANNONLY block to the next data directive so we don't read into CONCRETE
nxt = joined.find(".. py:data::", i_ann + 1) if ann_present else -1
seg = joined[i_ann:(nxt if nxt > 0 else len(joined))] if ann_present else ""
ann_no_value = ann_present and (":value:" not in seg)
ann_type = ann_present and (":type: int" in seg)
# concrete member is collected and reports its concrete value
i_con = joined.find(".. py:data:: CONCRETE")
concrete_present = i_con >= 0
ok = ann_present and ann_no_value and ann_type and concrete_present
if not ok:
    for l in out:
        print(repr(l))
print("RESULT ANNONLY_present=%s no_value=%s type_int=%s CONCRETE_present=%s OK=%s"
      % (ann_present, ann_no_value, ann_type, concrete_present, ok))
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 5.4 (preserve existing behavior — __all__ export list):
When all members requested and the module declares a non-empty __all__, every
collected entry is returned; entries whose name is not in __all__ are
suppressed (not emitted). Here KEEP is in __all__, DROP is not.
"""
import sys, os

def build_and_autodoc(options, module_body):
    sys.path.insert(0, '/testbed/tests')
    os.chdir('/testbed')
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as sphinx_path
    from test_ext_autodoc import do_autodoc
    root = '/testbed/tests/roots/test-ext-autodoc'
    modname = 'target._probe_mod'
    modpath = os.path.join(root, 'target', '_probe_mod.py')
    with open(modpath, 'w') as f:
        f.write(module_body)
    app = SphinxTestApp('dummy', srcdir=sphinx_path(root))
    try:
        return list(do_autodoc(app, 'module', modname, options))
    finally:
        app.cleanup()
        try: os.remove(modpath)
        except OSError: pass
        sys.modules.pop(modname, None)

MODULE = (
    "__all__ = ['KEEP']\n"
    "KEEP = 1  #: kept\n"
    "DROP = 2  #: dropped\n"
)

out = build_and_autodoc({"members": None}, MODULE)
print("OUTPUT:")
for l in out:
    print(repr(l))
joined = "\n".join(out)
keep_shown = ".. py:data:: KEEP" in joined
drop_hidden = ".. py:data:: DROP" not in joined
print("KEEP shown:", keep_shown, "DROP suppressed:", drop_hidden)
sys.exit(0 if (keep_shown and drop_hidden) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL / Requirement 2.1 & 2.2:
When a module is documented with all members requested and an underscore-named
module variable is documented ':meta public:', that variable SHALL appear as a
data member, reporting its module and value and retaining the :meta public:
field.

Holds on patched tree; must FAIL at base (data members ignored :meta before fix).
"""
import sys, os

def build_and_autodoc(options, module_body):
    sys.path.insert(0, '/testbed/tests')
    os.chdir('/testbed')
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as sphinx_path
    from test_ext_autodoc import do_autodoc
    root = '/testbed/tests/roots/test-ext-autodoc'
    modname = 'target._probe_mod'
    modpath = os.path.join(root, 'target', '_probe_mod.py')
    with open(modpath, 'w') as f:
        f.write(module_body)
    app = SphinxTestApp('dummy', srcdir=sphinx_path(root))
    try:
        return list(do_autodoc(app, 'module', modname, options))
    finally:
        app.cleanup()
        try: os.remove(modpath)
        except OSError: pass
        sys.modules.pop(modname, None)

MODULE = (
    "_PUBLIC_CONSTANT = None  #: :meta public:\n"
)

out = build_and_autodoc({"members": None}, MODULE)
print("OUTPUT:")
for l in out:
    print(repr(l))

joined = "\n".join(out)
ok = (".. py:data:: _PUBLIC_CONSTANT" in joined
      and ":module: target._probe_mod" in joined
      and ":value: None" in joined
      and ":meta public:" in joined)
# ensure the data-block for _PUBLIC_CONSTANT specifically carries module & value & meta
present = ".. py:data:: _PUBLIC_CONSTANT" in joined
print("present:", present, "criterion:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-8593: module-level data members must honour :meta public:/:meta private:. Probes exercise the automodule 'module' documenter via tests/test_ext_autodoc.do_autodoc against a self-injected target._probe_mod (gold patch.diff does NOT include the test_patch, so probes supply their own module).

Probe->requirement mapping and results (patched / base):
- probe_1 (POSITIVE CONTROL, Req 2.1/2.2): underscore var :meta public: appears as data member w/ module+value+meta. HOLDS patched; VIOLATED at base (present:False) -> discriminates.
- probe_2 (Req 3.1): PRIVATE_CONSTANT :meta private: hidden under default visibility while ordinary public var shown. HOLDS patched.
- probe_3 (Req 3.2/4.1/4.2): with private-members requested, both PRIVATE_CONSTANT (meta private) and _PUBLIC_CONSTANT (meta public) emitted w/ module+value+meta. HOLDS patched.
- probe_4 (Req 5.5/4.3): explicit members list returns requested-existing (ALPHA,BETA), omits unrequested GAMMA and nonexistent DOES_NOT_EXIST. HOLDS patched.
- probe_5 (Req 5.1/5.2): annotation-only member ANNONLY gets :type: and NO :value: sentinel; concrete member reports :value:. HOLDS patched.
- probe_6 (Req 5.4): __all__ export list suppresses non-listed DROP, keeps KEEP. HOLDS patched.

Candidate patch weak_A (partial/naive fix): gold patch with docstring="\n".join(docstring) replaced by docstring="" in both ObjectMember constructions -- wires the ObjectMember plumbing (Req 1 shape) but never carries the actual attribute comment, so extract_metadata never sees :meta fields. REJECTED by probe_1 (public underscore var stays hidden) and probe_2 (private var not hidden) -> suite discriminates a plausibly-wrong implementation. weak_A applies cleanly at base_commit (derived from gold patch.diff; context identical).

6 distinct probes all hold on patched tree; positive control fails at base and holds patched; >=1 requirements-plausible candidate exercised and REJECTED. Verdict SOUND.

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
"""POSITIVE CONTROL / Requirement 2.1 & 2.2:
When a module is documented with all members requested and an underscore-named
module variable is documented ':meta public:', that variable SHALL appear as a
data member, reporting its module and value and retaining the :meta public:
field.

Holds on patched tree; must FAIL at base (data members ignored :meta before fix).
"""
import sys, os

def build_and_autodoc(options, module_body):
    sys.path.insert(0, '/testbed/tests')
    os.chdir('/testbed')
    from sphinx.testing.util import SphinxTestApp
    from sphinx.testing.path import path as sphinx_path
    from test_ext_autodoc import do_autodoc
    root = '/testbed/tests/roots/test-ext-autodoc'
    modname = 'target._probe_mod'
    modpath = os.path.join(root, 'target', '_probe_mod.py')
    with open(modpath, 'w') as f:
        f.write(module_body)
    app = SphinxTestApp('dummy', srcdir=sphinx_path(root))
    try:
        return list(do_autodoc(app, 'module', modname, options))
    finally:
        app.cleanup()
        try: os.remove(modpath)
        except OSError: pass
        sys.modules.pop(modname, None)

MODULE = (
    "_PUBLIC_CONSTANT = None  #: :meta public:\n"
)

out = build_and_autodoc({"members": None}, MODULE)
print("OUTPUT:")
for l in out:
    print(repr(l))

joined = "\n".join(out)
ok = (".. py:data:: _PUBLIC_CONSTANT" in joined
      and ":module: target._probe_mod" in joined
      and ":value: None" in joined
      and ":meta public:" in joined)
# ensure the data-block for _PUBLIC_CONSTANT specifically carries module & value & meta
present = ".. py:data:: _PUBLIC_CONSTANT" in joined
print("present:", present, "criterion:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-8593: module-level data members must honour :meta public:/:meta private:. Probes exercise the automodule 'module' documenter via tests/test_ext_autodoc.do_autodoc against a self-injected target._probe_mod (gold patch.diff does NOT include the test_patch, so probes supply their own module).

Probe->requirement mapping and results (patched / base):
- probe_1 (POSITIVE CONTROL, Req 2.1/2.2): underscore var :meta public: appears as data member w/ module+value+meta. HOLDS patched; VIOLATED at base (present:False) -> discriminates.
- probe_2 (Req 3.1): PRIVATE_CONSTANT :meta private: hidden under default visibility while ordinary public var shown. HOLDS patched.
- probe_3 (Req 3.2/4.1/4.2): with private-members requested, both PRIVATE_CONSTANT (meta private) and _PUBLIC_CONSTANT (meta public) emitted w/ module+value+meta. HOLDS patched.
- probe_4 (Req 5.5/4.3): explicit members list returns requested-existing (ALPHA,BETA), omits unrequested GAMMA and nonexistent DOES_NOT_EXIST. HOLDS patched.
- probe_5 (Req 5.1/5.2): annotation-only member ANNONLY gets :type: and NO :value: sentinel; concrete member reports :value:. HOLDS patched.
- probe_6 (Req 5.4): __all__ export list suppresses non-listed DROP, keeps KEEP. HOLDS patched.

Candidate patch weak_A (partial/naive fix): gold patch with docstring="\n".join(docstring) replaced by docstring="" in both ObjectMember constructions -- wires the ObjectMember plumbing (Req 1 shape) but never carries the actual attribute comment, so extract_metadata never sees :meta fields. REJECTED by probe_1 (public underscore var stays hidden) and probe_2 (private var not hidden) -> suite discriminates a plausibly-wrong implementation. weak_A applies cleanly at base_commit (derived from gold patch.diff; context identical).

6 distinct probes all hold on patched tree; positive control fails at base and holds patched; >=1 requirements-plausible candidate exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Change is in ModuleDocumenter.get_object_members/new get_module_members (sphinx 3.5.0). Probed on gold-patched instance image: F2P tests test_private_field + test_private_members + test_private_field_and_private_members all pass (3 passed). ObjectMember default docstring is None but the new code always passes docstring="\n".join(...) so entries carry '' not None, matching Req1.2. Annotation-only members get INSTANCEATTR (Req5.2 confirmed True). want_all with __all__ marks non-members skipped=True and returns flag False; empty __all__ returns flag True (Req5.3/5.4). Explicit member list returns requested existing names in order, emits missing-attribute warning for nonexistent (Req5.5, Req4.3). Modeling boundary correctly targets the changed observable member-collection behavior, not a narrow helper slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally at the granularity of the public problem_statement (`:meta public:`/`:meta private:` ignored for module-level variables) and legitimately localizes to ModuleDocumenter.get_object_members / Documenter.filter_members / extract_metadata. None of the hidden-test-only artifacts are transmitted: no test file paths or function names (test_private_field, test_private_members, test_private_field_and_private_members), no test constant identifiers (PRIVATE_CONSTANT, _PUBLIC_CONSTANT, _public_function), no module name target.private, no verbatim rendered-output lines (`:value: None`, `:module: target.private`), and no fix-invented identifier is quoted as an obligation. Requirement 2/3/4 phrasings (`:meta public:` reveals underscore var; `:meta private:` hides non-underscore var; private-members by general request or by naming) are direct behavioral translations of the bug, not enumerations mirroring the parametrized cases with their specific names/values. Requirement 5's __all__/suppression/annotation-only-sentinel detail reflects preserved existing behavior of the gold code and is described generically (no INSTANCEATTR literal, no skipped flag naming). This is a faithful spec, not a test reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
