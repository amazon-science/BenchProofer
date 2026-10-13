# P2 adversarial audit — sphinx-doc__sphinx-8056

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
"""R1.1/R1.2/R1.6 + positive control: comma-grouped names expand to individual
:param:/:type: entries under napoleon_use_param, each carrying shared type+desc."""
import sys
from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import NumpyDocstring

docstring = """\
Parameters
----------
x1, x2 : array_like
    Input arrays, description of `x1`, `x2`.
"""
config = Config(napoleon_use_param=True)
out = str(NumpyDocstring(docstring, config))
print(repr(out))

lines = out.splitlines()
# Expect separate :param x1: and :param x2: plus separate :type x1:/:type x2:
have_param_x1 = any(l.startswith(':param x1:') for l in lines)
have_param_x2 = any(l.startswith(':param x2:') for l in lines)
have_type_x1 = any(l.startswith(':type x1:') and 'array_like' in l for l in lines)
have_type_x2 = any(l.startswith(':type x2:') and 'array_like' in l for l in lines)
# NOT a single merged entry
no_merged = not any('x1, x2' in l for l in lines)

print("param_x1", have_param_x1, "param_x2", have_param_x2,
      "type_x1", have_type_x1, "type_x2", have_type_x2, "no_merged", no_merged)

ok = have_param_x1 and have_param_x2 and have_type_x1 and have_type_x2 and no_merged
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.3 + R1.5 + R2.2: whitespace stripped from each name; order preserved;
type qualifier (', optional') preserved on every expanded entry."""
import sys
from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import NumpyDocstring

docstring = """\
Parameters
----------
x1,  x2 ,x3 : int, optional
    Some inputs.
"""
config = Config(napoleon_use_param=True)
out = str(NumpyDocstring(docstring, config))
print(repr(out))
lines = out.splitlines()

# names have no surrounding whitespace
param_names = [l[len(':param '):].rstrip(':').split(':')[0]
               for l in lines if l.startswith(':param ')]
# reconstruct actual param tokens
params = []
for l in lines:
    if l.startswith(':param '):
        rest = l[len(':param '):]
        name = rest.split(':', 1)[0]
        params.append(name)
print("params", params)
order_ok = params == ['x1', 'x2', 'x3']

# type qualifier preserved for each
types = [l for l in lines if l.startswith(':type ')]
print("types", types)
def has_type(name):
    return any(l.startswith(':type %s:' % name) and 'int' in l and 'optional' in l
               for l in lines)
type_ok = has_type('x1') and has_type('x2') and has_type('x3')

ok = order_ok and type_ok
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.4 + R2.3: single name -> exactly one entry; variadic *args/**kwargs
remain correctly escaped in the emitted output."""
import sys
from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import NumpyDocstring

config = Config(napoleon_use_param=True)

# single name
ds1 = """\
Parameters
----------
arg1 : int
    A single arg.
"""
out1 = str(NumpyDocstring(ds1, config))
print("SINGLE:", repr(out1))
lines1 = out1.splitlines()
n_param = sum(1 for l in lines1 if l.startswith(':param '))
single_ok = (n_param == 1 and any(l.startswith(':param arg1:') for l in lines1)
             and any(l.startswith(':type arg1:') and 'int' in l for l in lines1))

# variadic escaping
ds2 = """\
Parameters
----------
*args, **kwargs : int
    Variadic.
"""
out2 = str(NumpyDocstring(ds2, config))
print("VARIADIC:", repr(out2))
lines2 = out2.splitlines()
# escaped forms should be \*args and \*\*kwargs
esc_args = any(r'\*args' in l for l in lines2 if l.startswith(':param'))
esc_kwargs = any(r'\*\*kwargs' in l for l in lines2 if l.startswith(':param'))
print("esc_args", esc_args, "esc_kwargs", esc_kwargs)

ok = single_ok and esc_args and esc_kwargs
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1: with napoleon_use_param DISABLED, Parameters section is NOT split on
commas -> single merged entry, formatted as before (no :param: docutils)."""
import sys
from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import NumpyDocstring

docstring = """\
Parameters
----------
x1, x2 : array_like
    Input arrays.
"""
config = Config(napoleon_use_param=False)
out = str(NumpyDocstring(docstring, config))
print(repr(out))
lines = out.splitlines()

# No docutils :param: lines when disabled
no_param_lines = not any(l.startswith(':param') for l in lines)
# The grouped name stays together, not split
merged = any('x1, x2' in l or 'x1,x2' in l for l in lines)
print("no_param_lines", no_param_lines, "merged", merged)

ok = no_param_lines and merged
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.2/R3.3: comma-splitting does NOT apply to other sections. Under
napoleon_use_param=True, a Keyword Arguments / Raises field with commas keeps
its name intact (single entry)."""
import sys
from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import NumpyDocstring

config = Config(napoleon_use_param=True)

# Other Parameters: commas should NOT split (uses _format_fields path)
ds = """\
Other Parameters
----------------
a, b : int
    Two things.
"""
out = str(NumpyDocstring(ds, config))
print("OTHER PARAMS:", repr(out))
lines = out.splitlines()
# should NOT produce :param a: / :param b: split; name stays 'a, b'
no_split = not (any(':param a:' in l for l in lines) and any(':param b:' in l for l in lines))
kept = any('a, b' in l for l in lines)
print("no_split", no_split, "kept", kept)

ok = no_split and kept
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1/R1.2/R1.6 + positive control: comma-grouped names expand to individual
:param:/:type: entries under napoleon_use_param, each carrying shared type+desc."""
import sys
from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import NumpyDocstring

docstring = """\
Parameters
----------
x1, x2 : array_like
    Input arrays, description of `x1`, `x2`.
"""
config = Config(napoleon_use_param=True)
out = str(NumpyDocstring(docstring, config))
print(repr(out))

lines = out.splitlines()
# Expect separate :param x1: and :param x2: plus separate :type x1:/:type x2:
have_param_x1 = any(l.startswith(':param x1:') for l in lines)
have_param_x2 = any(l.startswith(':param x2:') for l in lines)
have_type_x1 = any(l.startswith(':type x1:') and 'array_like' in l for l in lines)
have_type_x2 = any(l.startswith(':type x2:') and 'array_like' in l for l in lines)
# NOT a single merged entry
no_merged = not any('x1, x2' in l for l in lines)

print("param_x1", have_param_x1, "param_x2", have_param_x2,
      "type_x1", have_type_x1, "type_x2", have_type_x2, "no_merged", no_merged)

ok = have_param_x1 and have_param_x2 and have_type_x1 and have_type_x2 and no_merged
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1, R1.1/1.2/1.6) discriminates: at base it emits a single merged ':param x1, x2:' / ':type x1, x2:' entry (FAIL), patched it emits separate :param x1:/:param x2: with :type x1:/:type x2: (HOLD). Coverage: probe_1 R1.1/R1.2/R1.6 (expansion + shared type/desc + docutils :param:/:type: output); probe_2 R1.3/R1.5/R2.2 (whitespace strip, source order x1,x2,x3, ', optional' qualifier preserved on each entry); probe_3 R1.4 (single name -> exactly one entry) + R2.3 (variadic \*args/\*\*kwargs escaping preserved); probe_4 R3.1 (use_param disabled -> NO split, no docutils :param:, grouped name kept as 'x1, x2'); probe_5 R3.2/R3.3 (Other Parameters section not comma-split).

Wrong-fix candidate (weak.diff): identical to gold but omits .strip() on the split names. It is REJECTED by probe_1 (emits ':param  x2:' with leading space) and probe_2 (emits names ['x1','  x2 ','x3']), demonstrating the suite discriminates the R1.3 whitespace criterion. No too-weak finding: the only requirements-conforming-looking alternative I could construct fails at least one probe. Note: meta.json records G-PANEL-3=LEAKAGE (Requirement 4's enumeration transcribes the hidden PASS_TO_PASS regression suite) but that is a leakage concern outside G-EQ's spec-fidelity scope; the mandated behaviors themselves all hold on the patched tree and the suite discriminates a wrong fix.

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
"""R1.1/R1.2/R1.6 + positive control: comma-grouped names expand to individual
:param:/:type: entries under napoleon_use_param, each carrying shared type+desc."""
import sys
from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import NumpyDocstring

docstring = """\
Parameters
----------
x1, x2 : array_like
    Input arrays, description of `x1`, `x2`.
"""
config = Config(napoleon_use_param=True)
out = str(NumpyDocstring(docstring, config))
print(repr(out))

lines = out.splitlines()
# Expect separate :param x1: and :param x2: plus separate :type x1:/:type x2:
have_param_x1 = any(l.startswith(':param x1:') for l in lines)
have_param_x2 = any(l.startswith(':param x2:') for l in lines)
have_type_x1 = any(l.startswith(':type x1:') and 'array_like' in l for l in lines)
have_type_x2 = any(l.startswith(':type x2:') and 'array_like' in l for l in lines)
# NOT a single merged entry
no_merged = not any('x1, x2' in l for l in lines)

print("param_x1", have_param_x1, "param_x2", have_param_x2,
      "type_x1", have_type_x1, "type_x2", have_type_x2, "no_merged", no_merged)

ok = have_param_x1 and have_param_x2 and have_type_x1 and have_type_x2 and no_merged
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on the gold-patched tree; positive control (probe_1, R1.1/1.2/1.6) discriminates: at base it emits a single merged ':param x1, x2:' / ':type x1, x2:' entry (FAIL), patched it emits separate :param x1:/:param x2: with :type x1:/:type x2: (HOLD). Coverage: probe_1 R1.1/R1.2/R1.6 (expansion + shared type/desc + docutils :param:/:type: output); probe_2 R1.3/R1.5/R2.2 (whitespace strip, source order x1,x2,x3, ', optional' qualifier preserved on each entry); probe_3 R1.4 (single name -> exactly one entry) + R2.3 (variadic \*args/\*\*kwargs escaping preserved); probe_4 R3.1 (use_param disabled -> NO split, no docutils :param:, grouped name kept as 'x1, x2'); probe_5 R3.2/R3.3 (Other Parameters section not comma-split).

Wrong-fix candidate (weak.diff): identical to gold but omits .strip() on the split names. It is REJECTED by probe_1 (emits ':param  x2:' with leading space) and probe_2 (emits names ['x1','  x2 ','x3']), demonstrating the suite discriminates the R1.3 whitespace criterion. No too-weak finding: the only requirements-conforming-looking alternative I could construct fails at least one probe. Note: meta.json records G-PANEL-3=LEAKAGE (Requirement 4's enumeration transcribes the hidden PASS_TO_PASS regression suite) but that is a leakage concern outside G-EQ's spec-fidelity scope; the mandated behaviors themselves all hold on the patched tree and the suite discriminates a wrong fix.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `multiple` kwarg to `_consume_fields`, splitting `_name.split(',')` with `.strip()`, wired ONLY into `_parse_parameters_section` under napoleon_use_param via `_format_docutils_params`. The requirements pin exactly this changed observable behavior (comma-name expansion in the Parameters section under use_param), correctly scope out other sections and the use_param=False path, and correctly note the empty-name guard (`if multiple and _name`). Modeling boundary is correct — it targets the changed behavior, not a narrow slice. Probes run on gold-patched image, all HOLDS (exit 0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally and localizes it to legitimately-named pre-existing public symbols (sphinx/ext/napoleon/docstring.py, _parse_parameters_section, _format_docutils_params, _consume_field). The core behavior — splitting comma-grouped Numpy parameter names, stripping whitespace, sharing type/description, confining the split to the napoleon_use_param Parameters path — is all derivable from the PUBLIC problem_statement (which contains the exact `x1, x2 : array_like` example, the description text, the `, optional` failure, and the expected split rendering). No hidden-test content is transmitted: the fix-invented `multiple` flag is NOT named; no test file path, test/class names (test_multiple_parameters, NumpyDocstringTest), parametrization ids ([x,/*args,/*x,]), or verbatim gold/test lines appear. Req 2.3 (variadic *args/**kwargs escaping preserved) is not in the problem_statement and loosely corresponds to test_escape_args_and_kwargs, but it is phrased as preservation of pre-existing behavior and is a natural consequence of comma-splitting a name — a behavioral requirement, not a reconstruction of the test's specific input/output cases or its parametrization enumeration. No test-shaped enumeration that mirrors the gold's `:param x1:/:type x1:` / `:param x2:/:type x2:` expected strings; the document stays at the level of 'each listed name produces its own :param:/:type: lines'.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
