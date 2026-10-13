# P2 adversarial audit — sphinx-doc__sphinx-9673

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
"""POSITIVE CONTROL. Req 1.1/1.2: a plural 'returns' description field with a
return annotation and no rtype => an rtype field carrying the annotation is appended.
HOLDS on patched, FAILS at base (base only recognized singular 'return')."""
import sys
from docutils import nodes
from sphinx.ext.autodoc.typehints import augment_descriptions_with_types


def field(name_text, body="x"):
    f = nodes.field()
    f += nodes.field_name('', name_text)
    f += nodes.field_body('', nodes.paragraph('', body))
    return f


fl = nodes.field_list()
fl += field('returns', 'the result')
annotations = {'return': 'int'}

augment_descriptions_with_types(fl, annotations)

names = [f[0].astext() for f in fl]
rtypes = [f[1].astext() for f in fl if f[0].astext().split()[0] == 'rtype']
print("field names:", names)
print("rtype bodies:", rtypes)

ok = ('rtype' in names) and rtypes == ['int']
if not ok:
    print("FAIL: expected a single rtype field with body 'int'")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2: the return name must NOT be emitted as a parameter type field,
under either spelling. With a plural 'returns' description and a 'return' annotation,
there must be NO 'type return' or 'type returns' field; only an rtype field."""
import sys
from docutils import nodes
from sphinx.ext.autodoc.typehints import augment_descriptions_with_types


def field(name_text, body="x"):
    f = nodes.field()
    f += nodes.field_name('', name_text)
    f += nodes.field_body('', nodes.paragraph('', body))
    return f


fl = nodes.field_list()
fl += field('returns', 'the result')
annotations = {'return': 'int'}

augment_descriptions_with_types(fl, annotations)
names = [f[0].astext() for f in fl]
print("field names:", names)

bad = [n for n in names if n in ('type return', 'type returns')]
if bad:
    print("FAIL: return emitted as parameter type field:", bad)
    sys.exit(1)
if 'rtype' not in names:
    print("FAIL: no rtype field")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2/3.3: preserve singular-return behavior.
(a) singular 'return' desc + annotation, no rtype => rtype appended (regression - holds at base too).
(b) if rtype already present (plural returns) => no additional rtype.
(c) if return not documented => no rtype appended (force_rtype=False)."""
import sys
from docutils import nodes
from sphinx.ext.autodoc.typehints import augment_descriptions_with_types


def field(name_text, body="x"):
    f = nodes.field()
    f += nodes.field_name('', name_text)
    f += nodes.field_body('', nodes.paragraph('', body))
    return f


def rtype_count(fl):
    return sum(1 for f in fl if f[0].astext().split()[0] == 'rtype')


# (a) singular return, no rtype
fl = nodes.field_list()
fl += field('return', 'the result')
augment_descriptions_with_types(fl, {'return': 'int'})
a = rtype_count(fl) == 1 and [f[1].astext() for f in fl if f[0].astext().split()[0]=='rtype'] == ['int']
print("(a) singular->rtype appended:", rtype_count(fl))

# (b) already has rtype (with plural returns desc): no duplicate
fl2 = nodes.field_list()
fl2 += field('returns', 'the result')
fl2 += field('rtype', 'str')
augment_descriptions_with_types(fl2, {'return': 'int'})
b = rtype_count(fl2) == 1
print("(b) already-typed no duplicate; rtype count:", rtype_count(fl2))

# (c) return not documented at all: no rtype
fl3 = nodes.field_list()
fl3 += field('param x', 'p')
augment_descriptions_with_types(fl3, {'return': 'int'})
c = rtype_count(fl3) == 0
print("(c) undocumented return no rtype; count:", rtype_count(fl3))

if a and b and c:
    print("PASS")
    sys.exit(0)
print("FAIL", a, b, c)
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 4: preserve parameter type augmentation.
(a) described-but-untyped param + annotation => 'type <name>' appended.
(b) already typed param => no duplicate type.
(c) undocumented param => no type field."""
import sys
from docutils import nodes
from sphinx.ext.autodoc.typehints import augment_descriptions_with_types


def field(name_text, body="x"):
    f = nodes.field()
    f += nodes.field_name('', name_text)
    f += nodes.field_body('', nodes.paragraph('', body))
    return f


def type_fields(fl):
    return [f[0].astext() for f in fl if f[0].astext().split()[0] == 'type']


# (a)
fl = nodes.field_list()
fl += field('param x', 'the x')
augment_descriptions_with_types(fl, {'x': 'int'})
a = 'type x' in type_fields(fl)
print("(a) type fields:", type_fields(fl))

# (b) already typed via 'param x yyy' shorthand -> has_type
fl2 = nodes.field_list()
fl2 += field('param str x', 'the x')  # :param str x: sets has_description & has_type
augment_descriptions_with_types(fl2, {'x': 'int'})
b = type_fields(fl2) == []
print("(b) already-typed no dup; type fields:", type_fields(fl2))

# (c) undocumented param
fl3 = nodes.field_list()
fl3 += field('param y', 'the y')
augment_descriptions_with_types(fl3, {'x': 'int', 'y': 'str'})
tf = type_fields(fl3)
c = 'type x' not in tf and 'type y' in tf
print("(c) type fields:", tf)

if a and b and c:
    print("PASS")
    sys.exit(0)
print("FAIL", a, b, c)
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 5.1: the "all" target path (modify_field_list) is unchanged - it augments
param/type for all params and appends rtype for the return. The fix touched only
augment_descriptions_with_types, so modify_field_list must still add rtype for a
return annotation even with NO return field documented."""
import sys
from docutils import nodes
from sphinx.ext.autodoc.typehints import modify_field_list


def field(name_text, body="x"):
    f = nodes.field()
    f += nodes.field_name('', name_text)
    f += nodes.field_body('', nodes.paragraph('', body))
    return f


fl = nodes.field_list()
fl += field('param x', 'the x')
modify_field_list(fl, {'x': 'int', 'return': 'bool'})

names = [f[0].astext() for f in fl]
print("field names:", names)
rtypes = [f[1].astext() for f in fl if f[0].astext().split()[0] == 'rtype']
ok = ('type x' in names) and ('rtype' in names) and rtypes == ['bool']
if not ok:
    print("FAIL: 'all' target did not augment as expected")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL. Req 1.1/1.2: a plural 'returns' description field with a
return annotation and no rtype => an rtype field carrying the annotation is appended.
HOLDS on patched, FAILS at base (base only recognized singular 'return')."""
import sys
from docutils import nodes
from sphinx.ext.autodoc.typehints import augment_descriptions_with_types


def field(name_text, body="x"):
    f = nodes.field()
    f += nodes.field_name('', name_text)
    f += nodes.field_body('', nodes.paragraph('', body))
    return f


fl = nodes.field_list()
fl += field('returns', 'the result')
annotations = {'return': 'int'}

augment_descriptions_with_types(fl, annotations)

names = [f[0].astext() for f in fl]
rtypes = [f[1].astext() for f in fl if f[0].astext().split()[0] == 'rtype']
print("field names:", names)
print("rtype bodies:", rtypes)

ok = ('rtype' in names) and rtypes == ['int']
if not ok:
    print("FAIL: expected a single rtype field with body 'int'")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9673. Bug: augment_descriptions_with_types only recognized singular 'return' as a return description, so Napoleon-style 'returns' fields got no rtype under autodoc_typehints=description + target=documented. Gold fix: accept parts[0] in ('return','returns') for has_description, and skip name in ('return','returns') in the param-type loop. NOTE: the image ships an OLDER typehints.py whose augment_descriptions_with_types has NO force_rtype param and a positional-only signature; probes were adjusted to the 2-arg signature actually present.

5 probes, all HOLD on patched:
- probe_1 (POSITIVE CONTROL, Req1.1/1.2): plural 'returns' desc + return annotation, no rtype => single rtype field body 'int'. PATCHED PASS; BASE FAIL (base yields ['returns'], no rtype). Discriminates.
- probe_2 (Req2.1/2.2): return never emitted as 'type return'/'type returns'; only rtype. PATCHED PASS.
- probe_3 (Req3.1/3.2/3.3): singular 'return'->rtype appended; existing rtype not duplicated; undocumented return => no rtype. PATCHED PASS.
- probe_4 (Req4.1/4.2/4.3): described-untyped param gains 'type x'; already-typed no dup; undocumented param no type. PATCHED PASS.
- probe_5 (Req5.1): 'all'-target modify_field_list still augments param/type and appends rtype for return annotation. PATCHED PASS.

Base runs: probe_1 FAIL, probe_2 FAIL at base — prepatch reproduced.

Candidate wrong-fix (weak.diff): recognizes 'returns' but stores it under key 'returns' in has_description (not 'return'), while the rtype block checks 'return' in has_description — the lazy/partial fix a weak reading permits. Probe suite REJECTS it: probe_1 FAIL (no rtype), probe_2 FAIL (no rtype). probes 3/4/5 pass. Demonstrates the suite discriminates wrong implementations. No requirements-conforming-yet-wrong patch found => no TOO-WEAK finding. Verdict SOUND: >=5 probes hold patched, positive control discriminates, >=1 candidate exercised and rejected.

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
"""POSITIVE CONTROL. Req 1.1/1.2: a plural 'returns' description field with a
return annotation and no rtype => an rtype field carrying the annotation is appended.
HOLDS on patched, FAILS at base (base only recognized singular 'return')."""
import sys
from docutils import nodes
from sphinx.ext.autodoc.typehints import augment_descriptions_with_types


def field(name_text, body="x"):
    f = nodes.field()
    f += nodes.field_name('', name_text)
    f += nodes.field_body('', nodes.paragraph('', body))
    return f


fl = nodes.field_list()
fl += field('returns', 'the result')
annotations = {'return': 'int'}

augment_descriptions_with_types(fl, annotations)

names = [f[0].astext() for f in fl]
rtypes = [f[1].astext() for f in fl if f[0].astext().split()[0] == 'rtype']
print("field names:", names)
print("rtype bodies:", rtypes)

ok = ('rtype' in names) and rtypes == ['int']
if not ok:
    print("FAIL: expected a single rtype field with body 'int'")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9673. Bug: augment_descriptions_with_types only recognized singular 'return' as a return description, so Napoleon-style 'returns' fields got no rtype under autodoc_typehints=description + target=documented. Gold fix: accept parts[0] in ('return','returns') for has_description, and skip name in ('return','returns') in the param-type loop. NOTE: the image ships an OLDER typehints.py whose augment_descriptions_with_types has NO force_rtype param and a positional-only signature; probes were adjusted to the 2-arg signature actually present.

5 probes, all HOLD on patched:
- probe_1 (POSITIVE CONTROL, Req1.1/1.2): plural 'returns' desc + return annotation, no rtype => single rtype field body 'int'. PATCHED PASS; BASE FAIL (base yields ['returns'], no rtype). Discriminates.
- probe_2 (Req2.1/2.2): return never emitted as 'type return'/'type returns'; only rtype. PATCHED PASS.
- probe_3 (Req3.1/3.2/3.3): singular 'return'->rtype appended; existing rtype not duplicated; undocumented return => no rtype. PATCHED PASS.
- probe_4 (Req4.1/4.2/4.3): described-untyped param gains 'type x'; already-typed no dup; undocumented param no type. PATCHED PASS.
- probe_5 (Req5.1): 'all'-target modify_field_list still augments param/type and appends rtype for return annotation. PATCHED PASS.

Base runs: probe_1 FAIL, probe_2 FAIL at base — prepatch reproduced.

Candidate wrong-fix (weak.diff): recognizes 'returns' but stores it under key 'returns' in has_description (not 'return'), while the rtype block checks 'return' in has_description — the lazy/partial fix a weak reading permits. Probe suite REJECTS it: probe_1 FAIL (no rtype), probe_2 FAIL (no rtype). probes 3/4/5 pass. Demonstrates the suite discriminates wrong implementations. No requirements-conforming-yet-wrong patch found => no TOO-WEAK finding. Verdict SOUND: >=5 probes hold patched, positive control discriminates, >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified by standalone probe run via nl_attack in the instance image. Patched tree: plural 'returns' -> ['returns','rtype'] (Req 1,2); singular 'return' -> ['return','rtype'] (Req 3.1); undocumented -> [] no rtype (Req 3.3); pre-existing rtype -> single rtype, no dup (Req 3.2); described param -> 'type x' added (Req 4.1). No 'type return'/'type returns' ever emitted (Req 2.2). Base-commit probe fails precisely at the plural-returns assertion, confirming the modeling boundary equals the changed behavior. Req 5 (all-target / other typehint modes / annotation recording) is untouched by the 2-line diff, so faithful by omission.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes behavior (accepting the plural 'returns' keyword as equivalent to singular 'return' for return-description detection, emitting a single rtype field, skipping the return name in per-parameter augmentation, preserving 'all'/other typehint modes) that is fully derivable from the public problem_statement (whose reproduction docstring shows 'Returns:') and hints_text (which contrasts :return: vs :returns:). Naming merge_typehints / augment_descriptions_with_types and the module sphinx/ext/autodoc/typehints.py is legitimate localization matching the gold source, not test content. No hidden-test artifacts appear: none of the test's fixture identifiers (decr/incr/tuple_args), the concrete expected strings ('decremented number', 'int'), the test function name (test_autodoc_typehints_description_no_undoc), the test file path, or any parametrization ids are quoted or mirrored. Requirements 1-5 translate the tests into general behavioral obligations rather than enumerating the specific test cases.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
