# P2 adversarial audit — sphinx-doc__sphinx-9258

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

Counterexample / evidence:

```
Candidate patch `naive_pipe_no_whitespace` adds `|` (bare, no `\s*` on either side) to the delims alternation instead of `\s*\|\s*`. Under it, `int | str` splits into pieces `'int '`, `'|'`, `' str'`, so the emitted cross-reference targets are `'int '` and `' str'` — surrounding whitespace is NOT excluded from the target. This violates Req 1.3 / 2.3 (target must be exactly the type name, no adjacent whitespace/pipe) and Req 1.4 (the ` | ` separator text incl. its spaces must be preserved verbatim; here the spaces leak into the names). probe_1 and probe_2 REJECT it; probe_3 (spaceless `int|str`) still passes, confirming the discriminator is specifically the whitespace-absorption requirement the gold `\s*\|\s*` satisfies.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
from sphinx.domains.python import PyTypedField
class _Dom:
    def process_field_xref(self, refnode): pass
class _Env:
    ref_context = {}
    def get_domain(self, d): return _Dom()
def xrefs(target):
    return PyTypedField('x').make_xrefs('class', 'py', target, env=_Env())
def classify(nodes_list):
    # returns list of ('xref', target) or ('sep', text)
    out=[]
    for n in nodes_list:
        tgt = n.get('reftarget') if hasattr(n,'get') else None
        if type(n).__name__=='pending_xref' and tgt is not None:
            out.append(('xref', tgt, n.astext()))
        else:
            out.append(('sep', None, n.astext()))
    return out
import sys
res = classify(xrefs('int | str'))
print("OBSERVED:", res)
ok = (len(res)==3
      and res[0]==('xref','int','int')
      and res[1][0]=='sep' and res[1][2]==' | '
      and res[2]==('xref','str','str'))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
from sphinx.domains.python import PyTypedField
class _Dom:
    def process_field_xref(self, refnode): pass
class _Env:
    ref_context = {}
    def get_domain(self, d): return _Dom()
def xrefs(target):
    return PyTypedField('x').make_xrefs('class', 'py', target, env=_Env())
def classify(nodes_list):
    # returns list of ('xref', target) or ('sep', text)
    out=[]
    for n in nodes_list:
        tgt = n.get('reftarget') if hasattr(n,'get') else None
        if type(n).__name__=='pending_xref' and tgt is not None:
            out.append(('xref', tgt, n.astext()))
        else:
            out.append(('sep', None, n.astext()))
    return out
import sys
res = classify(xrefs('int | str | bytes'))
print("OBSERVED:", res)
ok = (len(res)==5
      and res[0]==('xref','int','int')
      and res[1][0]=='sep' and res[1][2]==' | '
      and res[2]==('xref','str','str')
      and res[3][0]=='sep' and res[3][2]==' | '
      and res[4]==('xref','bytes','bytes'))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
from sphinx.domains.python import PyTypedField
class _Dom:
    def process_field_xref(self, refnode): pass
class _Env:
    ref_context = {}
    def get_domain(self, d): return _Dom()
def xrefs(target):
    return PyTypedField('x').make_xrefs('class', 'py', target, env=_Env())
def classify(nodes_list):
    # returns list of ('xref', target) or ('sep', text)
    out=[]
    for n in nodes_list:
        tgt = n.get('reftarget') if hasattr(n,'get') else None
        if type(n).__name__=='pending_xref' and tgt is not None:
            out.append(('xref', tgt, n.astext()))
        else:
            out.append(('sep', None, n.astext()))
    return out
import sys
res = classify(xrefs('int|str'))
print("OBSERVED:", res)
# targets must be exactly int and str (no pipe/space), pipe is a separator
xr = [r for r in res if r[0]=='xref']
seps = [r for r in res if r[0]=='sep']
ok = ([r[1] for r in xr]==['int','str']
      and any('|' in s[2] for s in seps)
      and all('|' not in r[1] and ' ' not in r[1] for r in xr))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
from sphinx.domains.python import PyTypedField
class _Dom:
    def process_field_xref(self, refnode): pass
class _Env:
    ref_context = {}
    def get_domain(self, d): return _Dom()
def xrefs(target):
    return PyTypedField('x').make_xrefs('class', 'py', target, env=_Env())
def classify(nodes_list):
    # returns list of ('xref', target) or ('sep', text)
    out=[]
    for n in nodes_list:
        tgt = n.get('reftarget') if hasattr(n,'get') else None
        if type(n).__name__=='pending_xref' and tgt is not None:
            out.append(('xref', tgt, n.astext()))
        else:
            out.append(('sep', None, n.astext()))
    return out
import sys
res = classify(xrefs('int or str'))
print("OBSERVED:", res)
ok = (len(res)==3
      and res[0]==('xref','int','int')
      and res[1][0]=='sep' and 'or' in res[1][2]
      and res[2]==('xref','str','str'))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
from sphinx.domains.python import PyTypedField
class _Dom:
    def process_field_xref(self, refnode): pass
class _Env:
    ref_context = {}
    def get_domain(self, d): return _Dom()
def xrefs(target):
    return PyTypedField('x').make_xrefs('class', 'py', target, env=_Env())
def classify(nodes_list):
    # returns list of ('xref', target) or ('sep', text)
    out=[]
    for n in nodes_list:
        tgt = n.get('reftarget') if hasattr(n,'get') else None
        if type(n).__name__=='pending_xref' and tgt is not None:
            out.append(('xref', tgt, n.astext()))
        else:
            out.append(('sep', None, n.astext()))
    return out
import sys
res = classify(xrefs('List[int, str]'))
print("OBSERVED:", res)
xr = [r[1] for r in res if r[0]=='xref']
ok = ('List' in xr and 'int' in xr and 'str' in xr
      and any('[' in r[2] for r in res if r[0]=='sep')
      and any(']' in r[2] for r in res if r[0]=='sep'))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
from sphinx.domains.python import PyTypedField
class _Dom:
    def process_field_xref(self, refnode): pass
class _Env:
    ref_context = {}
    def get_domain(self, d): return _Dom()
def xrefs(target):
    return PyTypedField('x').make_xrefs('class', 'py', target, env=_Env())
def classify(nodes_list):
    # returns list of ('xref', target) or ('sep', text)
    out=[]
    for n in nodes_list:
        tgt = n.get('reftarget') if hasattr(n,'get') else None
        if type(n).__name__=='pending_xref' and tgt is not None:
            out.append(('xref', tgt, n.astext()))
        else:
            out.append(('sep', None, n.astext()))
    return out
import sys
res = classify(xrefs('MyType'))
print("OBSERVED:", res)
ok = (len(res)==1 and res[0]==('xref','MyType','MyType'))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
from sphinx.domains.python import PyTypedField
class _Dom:
    def process_field_xref(self, refnode): pass
class _Env:
    ref_context = {}
    def get_domain(self, d): return _Dom()
def xrefs(target):
    return PyTypedField('x').make_xrefs('class', 'py', target, env=_Env())
def classify(nodes_list):
    # returns list of ('xref', target) or ('sep', text)
    out=[]
    for n in nodes_list:
        tgt = n.get('reftarget') if hasattr(n,'get') else None
        if type(n).__name__=='pending_xref' and tgt is not None:
            out.append(('xref', tgt, n.astext()))
        else:
            out.append(('sep', None, n.astext()))
    return out
import sys
res = classify(xrefs('Callable[..., int]'))
print("OBSERVED:", res)
xr = [r[1] for r in res if r[0]=='xref']
# '...' must NOT be a cross-reference target
ok = ('Callable' in xr and 'int' in xr and '...' not in xr
      and all(r[1] != '...' for r in res if r[0]=='xref'))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
from sphinx.domains.python import PyTypedField
class _Dom:
    def process_field_xref(self, refnode): pass
class _Env:
    ref_context = {}
    def get_domain(self, d): return _Dom()
def xrefs(target):
    return PyTypedField('x').make_xrefs('class', 'py', target, env=_Env())
def classify(nodes_list):
    # returns list of ('xref', target) or ('sep', text)
    out=[]
    for n in nodes_list:
        tgt = n.get('reftarget') if hasattr(n,'get') else None
        if type(n).__name__=='pending_xref' and tgt is not None:
            out.append(('xref', tgt, n.astext()))
        else:
            out.append(('sep', None, n.astext()))
    return out
import sys
res = classify(xrefs('int | str'))
print("OBSERVED:", res)
ok = (len(res)==3
      and res[0]==('xref','int','int')
      and res[1][0]=='sep' and res[1][2]==' | '
      and res[2]==('xref','str','str'))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

PyXrefMixin.make_xrefs in sphinx/domains/python.py. Concrete class exercised: PyTypedField (PyXrefMixin is abstract — its super().make_xref requires a real domain/env). Probes stub env.ref_context={} and a no-op domain.process_field_xref. Nodes: pending_xref with reftarget for type names, emphasis for separators.

All 7 probes HOLD on the gold-patched tree. Base-tree results: pipe probes (1,2,3) FAIL at base (the whole spec is emitted as one xref, e.g. reftarget='int | str') — positive control discriminates; regression probes (4,5,6,7 = or/brackets+commas/no-sep/ellipsis) HOLD at both base and patched, confirming Req 3 no-regression criteria and that they don't spuriously pass.

Probe->requirement map: probe_1 = Req1.2/1.3/1.4 (A|B order, exact targets, verbatim ' | ') [POSITIVE CONTROL]; probe_2 = Req1.5/2.4 (A|B|C, three xrefs + two seps, order); probe_3 = Req2.3 (spaceless int|str, targets exclude pipe/space); probe_4 = Req3.1 ('or' kept); probe_5 = Req3.2 (brackets/commas kept, inner names xref'd); probe_6 = Req3.4 (no separator -> single xref); probe_7 = Req3.3 (ellipsis '...' stays a separator, not xref'd).

Candidate-patch results confirm suite discriminates a wrong implementation: naive_pipe_no_whitespace is rejected by probes 1&2. No probe-conforming alternative found that would fail the harness -> not a TOO-WEAK finding. Verdict SOUND: >=5 distinct probes all hold on patched, positive control fails at base and holds patched, >=1 candidate exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Candidate patch `naive_pipe_no_whitespace` adds `|` (bare, no `\s*` on either side) to the delims alternation instead of `\s*\|\s*`. Under it, `int | str` splits into pieces `'int '`, `'|'`, `' str'`, so the emitted cross-reference targets are `'int '` and `' str'` — surrounding whitespace is NOT excluded from the target. This violates Req 1.3 / 2.3 (target must be exactly the type name, no adjacent whitespace/pipe) and Req 1.4 (the ` | ` separator text incl. its spaces must be preserved verbatim; here the spaces leak into the names). probe_1 and probe_2 REJECT it; probe_3 (spaceless `int|str`) still passes, confirming the discriminator is specifically the whitespace-absorption requirement the gold `\s*\|\s*` satisfies.
```

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
from sphinx.domains.python import PyTypedField
class _Dom:
    def process_field_xref(self, refnode): pass
class _Env:
    ref_context = {}
    def get_domain(self, d): return _Dom()
def xrefs(target):
    return PyTypedField('x').make_xrefs('class', 'py', target, env=_Env())
def classify(nodes_list):
    # returns list of ('xref', target) or ('sep', text)
    out=[]
    for n in nodes_list:
        tgt = n.get('reftarget') if hasattr(n,'get') else None
        if type(n).__name__=='pending_xref' and tgt is not None:
            out.append(('xref', tgt, n.astext()))
        else:
            out.append(('sep', None, n.astext()))
    return out
import sys
res = classify(xrefs('int | str'))
print("OBSERVED:", res)
ok = (len(res)==3
      and res[0]==('xref','int','int')
      and res[1][0]=='sep' and res[1][2]==' | '
      and res[2]==('xref','str','str'))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

PyXrefMixin.make_xrefs in sphinx/domains/python.py. Concrete class exercised: PyTypedField (PyXrefMixin is abstract — its super().make_xref requires a real domain/env). Probes stub env.ref_context={} and a no-op domain.process_field_xref. Nodes: pending_xref with reftarget for type names, emphasis for separators.

All 7 probes HOLD on the gold-patched tree. Base-tree results: pipe probes (1,2,3) FAIL at base (the whole spec is emitted as one xref, e.g. reftarget='int | str') — positive control discriminates; regression probes (4,5,6,7 = or/brackets+commas/no-sep/ellipsis) HOLD at both base and patched, confirming Req 3 no-regression criteria and that they don't spuriously pass.

Probe->requirement map: probe_1 = Req1.2/1.3/1.4 (A|B order, exact targets, verbatim ' | ') [POSITIVE CONTROL]; probe_2 = Req1.5/2.4 (A|B|C, three xrefs + two seps, order); probe_3 = Req2.3 (spaceless int|str, targets exclude pipe/space); probe_4 = Req3.1 ('or' kept); probe_5 = Req3.2 (brackets/commas kept, inner names xref'd); probe_6 = Req3.4 (no separator -> single xref); probe_7 = Req3.3 (ellipsis '...' stays a separator, not xref'd).

Candidate-patch results confirm suite discriminates a wrong implementation: naive_pipe_no_whitespace is rejected by probes 1&2. No probe-conforming alternative found that would fail the harness -> not a TOO-WEAK finding. Verdict SOUND: >=5 distinct probes all hold on patched, positive control fails at base and holds patched, >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on the gold-patched /testbed image via nl_attack. Patched delims: (\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.). Confirmed classification: 'int | str' => [NAME 'int', SEP ' | ', NAME 'str']; 'A | B | C' => 3 names + 2 seps; 'bytes|str' also splits (pipe without spaces). Existing separators unchanged. Requirements pin the changed observable behavior (pipe recognition + no regression) at the correct boundary — the make_xrefs splitter.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the behavior (treat '|' + surrounding whitespace as a type separator on par with existing 'or'/brackets/commas/'...' in PyXrefMixin.make_xrefs) in prose. Naming the module/function is legitimate localization. No verbatim regex, no test names/paths/ids, no node-type identifiers (pending_xref/literal_emphasis/literal_strong) from the hidden test, no fix-invented identifiers. The 'int | str' example matches the test but is a canonical generic union example (problem_statement itself gives 'bytes | str'); Req 4's end-to-end rendering is a behavioral translation of the single test, not a reconstruction of its assert_node tree. 'A | B | C' generalizes beyond the 2-type hidden test. All content is public-problem-statement-consistent behavioral spec.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
