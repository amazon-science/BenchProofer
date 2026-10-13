# P2 adversarial audit — sphinx-doc__sphinx-7454

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
"""Positive control (Req 2.1): _parse_annotation("None") yields a single
pending_xref whose reftype is 'obj' (object kind), refdomain 'py', reftarget
'None', label 'None'. HOLDS on patched, FAILS at base (base emits reftype
'class')."""
import sys
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes

doctree = _parse_annotation("None")
xrefs = [n for n in doctree if isinstance(n, addnodes.pending_xref)]
print("nodes:", [type(n).__name__ for n in doctree])
if len(xrefs) != 1:
    print("FAIL: expected exactly one pending_xref, got", len(xrefs)); sys.exit(1)
x = xrefs[0]
print("reftype=%r refdomain=%r reftarget=%r label=%r" % (
    x.get("reftype"), x.get("refdomain"), x.get("reftarget"), x.astext()))
ok = (x.get("reftype") == "obj" and x.get("refdomain") == "py"
      and x.get("reftarget") == "None" and x.astext() == "None")
print("HOLDS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 3.1 / 2.2: plain class name 'int' -> single class-kind py xref,
target and label 'int'. Regression 'SHALL keep'."""
import sys
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes

doctree = _parse_annotation("int")
print("nodes:", [type(n).__name__ for n in doctree])
xrefs = [n for n in doctree if isinstance(n, addnodes.pending_xref)]
if len(xrefs) != 1:
    print("FAIL: expected one xref, got", len(xrefs)); sys.exit(1)
x = xrefs[0]
print("reftype=%r refdomain=%r reftarget=%r label=%r" % (
    x.get("reftype"), x.get("refdomain"), x.get("reftarget"), x.astext()))
ok = (x.get("reftype") == "class" and x.get("refdomain") == "py"
      and x.get("reftarget") == "int" and x.astext() == "int")
print("HOLDS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.2 / 1.x: subscripted 'List[int]' -> name xref, '[' punctuation,
inner xref, ']' punctuation; every token class-kind, py domain, target=label=text."""
import sys
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
from sphinx.addnodes import desc_sig_punctuation

doctree = _parse_annotation("List[int]")
seq = [(type(n).__name__, n.astext()) for n in doctree]
print("seq:", seq)
# Expected structure: pending_xref(List), punct([), pending_xref(int), punct(])
if len(doctree) != 4:
    print("FAIL: expected 4 nodes, got", len(doctree)); sys.exit(1)
n0, n1, n2, n3 = doctree
ok = True
if not (isinstance(n0, addnodes.pending_xref) and n0.get("reftype") == "class"
        and n0.get("refdomain") == "py" and n0.get("reftarget") == "List"
        and n0.astext() == "List"):
    ok = False; print("FAIL n0", n0.attributes if hasattr(n0,'attributes') else n0)
if not (isinstance(n1, desc_sig_punctuation) and n1.astext() == "["):
    ok = False; print("FAIL n1")
if not (isinstance(n2, addnodes.pending_xref) and n2.get("reftype") == "class"
        and n2.get("refdomain") == "py" and n2.get("reftarget") == "int"
        and n2.astext() == "int"):
    ok = False; print("FAIL n2")
if not (isinstance(n3, desc_sig_punctuation) and n3.astext() == "]"):
    ok = False; print("FAIL n3")
print("HOLDS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.3: reference kind is determined SOLELY by whether the token equals
'None'; domain, target, and label do NOT depend on that distinction. Compare
the 'None' xref against a non-None token 'int' xref: only reftype may differ;
domain must be 'py' and target==label==text for both."""
import sys
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes

def one_xref(text):
    dt = _parse_annotation(text)
    xs = [n for n in dt if isinstance(n, addnodes.pending_xref)]
    assert len(xs) == 1, (text, len(xs))
    return xs[0]

none_x = one_xref("None")
int_x = one_xref("int")
print("None:", none_x.get("refdomain"), none_x.get("reftype"), none_x.get("reftarget"), none_x.astext())
print("int :", int_x.get("refdomain"), int_x.get("reftype"), int_x.get("reftarget"), int_x.astext())

ok = True
# domain identical and 'py'
if not (none_x.get("refdomain") == int_x.get("refdomain") == "py"):
    ok = False; print("FAIL domain differs / not py")
# target == label == text for both
if not (none_x.get("reftarget") == none_x.astext() == "None"):
    ok = False; print("FAIL None target/label")
if not (int_x.get("reftarget") == int_x.astext() == "int"):
    ok = False; print("FAIL int target/label")
# reftype: None->obj, int->class (they must differ per the rule)
if none_x.get("reftype") != "obj":
    ok = False; print("FAIL None not obj")
if int_x.get("reftype") != "class":
    ok = False; print("FAIL int not class")
print("HOLDS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 1.5: an unparseable annotation still emits a SINGLE pending_xref for the
whole text with py domain, target=label=text. Use invalid expression '['."""
import sys
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes

bad = "[garbage"  # not a valid python expression
doctree = _parse_annotation(bad)
print("nodes:", [(type(n).__name__, n.astext()) for n in doctree])
xrefs = [n for n in doctree if isinstance(n, addnodes.pending_xref)]
if len(xrefs) != 1:
    print("FAIL: expected one xref for whole text, got", len(xrefs)); sys.exit(1)
x = xrefs[0]
print("reftype=%r refdomain=%r reftarget=%r label=%r" % (
    x.get("reftype"), x.get("refdomain"), x.get("reftarget"), x.astext()))
ok = (x.get("refdomain") == "py" and x.get("reftarget") == bad
      and x.astext() == bad)
# whole-text token is not 'None' so class kind
ok = ok and x.get("reftype") == "class"
print("HOLDS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.3: comma-separated / qualified names preserved. Tuple[int, str] and a
qualified name pathlib.Path -> class-kind py xref target=full text."""
import sys
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes

# comma-separated
dt = _parse_annotation("Tuple[int, str]")
xrefs = [x.get("reftarget") for x in dt if isinstance(x, addnodes.pending_xref)]
print("Tuple targets:", xrefs)
ok = xrefs == ["Tuple", "int", "str"]
for x in dt:
    if isinstance(x, addnodes.pending_xref):
        if x.get("reftype") != "class" or x.get("refdomain") != "py":
            ok = False; print("FAIL non-class token in Tuple")

# qualified name
dt2 = _parse_annotation("pathlib.Path")
x2 = [n for n in dt2 if isinstance(n, addnodes.pending_xref)]
print("qualified:", [(n.get("reftarget"), n.astext(), n.get("reftype")) for n in x2])
if len(x2) != 1 or x2[0].get("reftarget") != "pathlib.Path" or x2[0].get("reftype") != "class":
    ok = False; print("FAIL qualified name")
print("HOLDS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 2.1): _parse_annotation("None") yields a single
pending_xref whose reftype is 'obj' (object kind), refdomain 'py', reftarget
'None', label 'None'. HOLDS on patched, FAILS at base (base emits reftype
'class')."""
import sys
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes

doctree = _parse_annotation("None")
xrefs = [n for n in doctree if isinstance(n, addnodes.pending_xref)]
print("nodes:", [type(n).__name__ for n in doctree])
if len(xrefs) != 1:
    print("FAIL: expected exactly one pending_xref, got", len(xrefs)); sys.exit(1)
x = xrefs[0]
print("reftype=%r refdomain=%r reftarget=%r label=%r" % (
    x.get("reftype"), x.get("refdomain"), x.get("reftarget"), x.astext()))
ok = (x.get("reftype") == "obj" and x.get("refdomain") == "py"
      and x.get("reftarget") == "None" and x.astext() == "None")
print("HOLDS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: _parse_annotation.make_xref must emit reftype 'obj' for the token 'None' and 'class' for every other token, keeping refdomain='py', reftarget=text, label=text. Probes: p1 (Req2.1, positive control) None->single py/obj/None xref; p2 (Req3.1) int->class; p3 (Req3.2) List[int]->name-xref '[' inner-xref ']' all class; p4 (Req2.3) domain/target/label identical for None vs int, only reftype differs (None=obj,int=class); p5 (Req1.5) unparseable '[garbage' -> single whole-text py/class xref, target=label=text; p6 (Req3.3) Tuple[int,str] comma-split + qualified pathlib.Path preserved as class. Results: all 6 HOLD on gold-patched tree. Positive control p1 HOLDS patched (reftype='obj') and FAILS at base (reftype='class') -> discriminating power confirmed.

Candidate wrong patch weak.diff sets reftype='data' for None (a weak reading: 'some non-class object kind'): REJECTED by p1 and p4 (require 'obj' exactly), while p2/p3/p5/p6 still hold -> the suite discriminates a plausibly-wrong fix. That candidate would also fail the hidden F2P test tests/test_domain_py.py::test_parse_annotation which asserts reftype='obj'. No requirements-conforming alternative that fails the harness was found; requirements pin reftype to exactly the object kind, matching gold. Verdict SOUND.

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
"""Positive control (Req 2.1): _parse_annotation("None") yields a single
pending_xref whose reftype is 'obj' (object kind), refdomain 'py', reftarget
'None', label 'None'. HOLDS on patched, FAILS at base (base emits reftype
'class')."""
import sys
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes

doctree = _parse_annotation("None")
xrefs = [n for n in doctree if isinstance(n, addnodes.pending_xref)]
print("nodes:", [type(n).__name__ for n in doctree])
if len(xrefs) != 1:
    print("FAIL: expected exactly one pending_xref, got", len(xrefs)); sys.exit(1)
x = xrefs[0]
print("reftype=%r refdomain=%r reftarget=%r label=%r" % (
    x.get("reftype"), x.get("refdomain"), x.get("reftarget"), x.astext()))
ok = (x.get("reftype") == "obj" and x.get("refdomain") == "py"
      and x.get("reftarget") == "None" and x.astext() == "None")
print("HOLDS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: _parse_annotation.make_xref must emit reftype 'obj' for the token 'None' and 'class' for every other token, keeping refdomain='py', reftarget=text, label=text. Probes: p1 (Req2.1, positive control) None->single py/obj/None xref; p2 (Req3.1) int->class; p3 (Req3.2) List[int]->name-xref '[' inner-xref ']' all class; p4 (Req2.3) domain/target/label identical for None vs int, only reftype differs (None=obj,int=class); p5 (Req1.5) unparseable '[garbage' -> single whole-text py/class xref, target=label=text; p6 (Req3.3) Tuple[int,str] comma-split + qualified pathlib.Path preserved as class. Results: all 6 HOLD on gold-patched tree. Positive control p1 HOLDS patched (reftype='obj') and FAILS at base (reftype='class') -> discriminating power confirmed.

Candidate wrong patch weak.diff sets reftype='data' for None (a weak reading: 'some non-class object kind'): REJECTED by p1 and p4 (require 'obj' exactly), while p2/p3/p5/p6 still hold -> the suite discriminates a plausibly-wrong fix. That candidate would also fail the hidden F2P test tests/test_domain_py.py::test_parse_annotation which asserts reftype='obj'. No requirements-conforming alternative that fails the harness was found; requirements pin reftype to exactly the object kind, matching gold. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: make_xref sets reftype='obj' iff text=='None' else 'class'; domain='py', target=text, label=text unchanged. Probe on patched tree: None->(py,obj,None,None); int->(py,class,int,int); List[int]-> pending_xref(List,class)/'['/pending_xref(int,class)/']'; unparseable 'List[[['->single (py,class,'List[[[','List[[['). Probe --base: None->(py,class,None) confirming the sole behavioral discriminator. R1.1-1.4 (every token->py pending_xref, target=label=text) hold; R1.5 (SyntaxError fallback -> single whole-text xref) holds; R2.1 None->obj, R2.2 others->class, R2.3 kind solely from text=='None' hold; R3.1-3.4 (int single class xref, List[int] structure, class kind for non-None tokens, mode-independence) hold. Requirements pin the changed observable behavior, not a narrow helper slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements translate the public problem_statement (None must link to None's docs in signature mode, consistent with description mode) into behavioral EARS criteria. The core fix behavior (token 'None' -> object reference, all others -> class reference) is directly implied by the problem_statement, not derived from hidden tests. Named identifiers (_parse_annotation, sphinx/domains/python.py, pending_xref, desc_sig_punctuation, refdomain/reftype/reftarget) are pre-existing Sphinx API/internals used for legitimate localization, not fix-invented names. No test names/paths/ids, no quoted test or gold code. The List[int] node-structure enumeration (Req 3.2) mirrors a PRE-EXISTING (unchanged context) assertion in the test file and describes preserved parsing behavior, not the newly-added None test case; it reads as generic behavioral description of subscripted annotations. No case enumeration reconstructs the added parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
