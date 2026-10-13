# P2 adversarial audit — sympy__sympy-15976

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_pc.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1: undecorated symbol -> bare mi, one text child = name, no wrapper
import sys
from sympy import Symbol
from sympy.printing.mathml import MathMLPresentationPrinter
p = MathMLPresentationPrinter()
e = p._print_Symbol(Symbol('x'))
print("node:", e.nodeName, "xml:", e.toxml())
ok = (e.nodeName == 'mi'
      and len(e.childNodes) == 1
      and e.childNodes[0].nodeType == e.TEXT_NODE
      and e.childNodes[0].data == 'x')
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2: subscript-only -> top-level msub, child0 mi=base, child1 subscript, no mi wrapper
import sys
from sympy import Symbol
from sympy.printing.mathml import MathMLPresentationPrinter
p = MathMLPresentationPrinter()
e = p._print_Symbol(Symbol('x_2'))
print("node:", e.nodeName, "xml:", e.toxml())
c = e.childNodes
ok = (e.nodeName == 'msub'
      and len(c) == 2
      and c[0].nodeName == 'mi' and c[0].childNodes[0].data == 'x'
      and c[1].nodeName == 'mi' and c[1].childNodes[0].data == '2')
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 3: superscript-only -> top-level msup, child0 mi=base, child1 supers
import sys
from sympy import Symbol
from sympy.printing.mathml import MathMLPresentationPrinter
p = MathMLPresentationPrinter()
e = p._print_Symbol(Symbol('x^2'))
print("node:", e.nodeName, "xml:", e.toxml())
c = e.childNodes
ok = (e.nodeName == 'msup'
      and len(c) == 2
      and c[0].nodeName == 'mi' and c[0].childNodes[0].data == 'x'
      and c[1].nodeName == 'mi' and c[1].childNodes[0].data == '2')
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 4: sub+super -> msubsup, children [mi base, subs, supers] in order
import sys
from sympy import Symbol
from sympy.printing.mathml import MathMLPresentationPrinter
p = MathMLPresentationPrinter()
e = p._print_Symbol(Symbol('x^3_2'))
print("node:", e.nodeName, "xml:", e.toxml())
c = e.childNodes
ok = (e.nodeName == 'msubsup'
      and len(c) == 3
      and c[0].nodeName == 'mi' and c[0].childNodes[0].data == 'x'
      and c[1].nodeName == 'mi' and c[1].childNodes[0].data == '2'   # subscript first
      and c[2].nodeName == 'mi' and c[2].childNodes[0].data == '3')  # superscript second
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 5: multi-piece decoration -> mrow with mi, mo(" "), mi ...
import sys
from sympy import Symbol
from sympy.printing.mathml import MathMLPresentationPrinter
from sympy.printing.conventions import split_super_sub
p = MathMLPresentationPrinter()
name, supers, subs = split_super_sub('x_a_b')
print("split x_a_b:", name, supers, subs)
assert len(subs) >= 2, subs
e = p._print_Symbol(Symbol('x_a_b'))
print("node:", e.nodeName, "xml:", e.toxml())
# top-level msub, second child is the subscript collection = mrow
coll = e.childNodes[1]
c = coll.childNodes
ok = (e.nodeName == 'msub'
      and coll.nodeName == 'mrow'
      and len(c) == 3
      and c[0].nodeName == 'mi' and c[0].childNodes[0].data == subs[0]
      and c[1].nodeName == 'mo' and c[1].childNodes[0].data == ' '
      and c[2].nodeName == 'mi' and c[2].childNodes[0].data == subs[1])
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 6: bold style sets mathvariant=bold on top-level element; plain does not
import sys
from sympy import Symbol
from sympy.printing.mathml import MathMLPresentationPrinter
p = MathMLPresentationPrinter()
ok = True
# bold on undecorated -> mi with mathvariant bold
e = p._print_Symbol(Symbol('x'), style='bold')
print("bold x:", e.nodeName, e.toxml())
ok &= (e.nodeName == 'mi' and e.getAttribute('mathvariant') == 'bold')
# bold on scripted -> attribute on msub itself (outermost), not a wrapper
e2 = p._print_Symbol(Symbol('x_2'), style='bold')
print("bold x_2:", e2.nodeName, e2.toxml())
ok &= (e2.nodeName == 'msub' and e2.getAttribute('mathvariant') == 'bold')
# plain -> no mathvariant
e3 = p._print_Symbol(Symbol('x_2'))
print("plain x_2:", e3.toxml())
ok &= (e3.getAttribute('mathvariant') == '')
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 7: regression. MatrixSymbol renders same structure as ordinary symbol (with style);
# content printer Symbol unchanged (still wraps as ci). No stray outer mi wrapper for scripted symbol.
import sys
from sympy import Symbol, MatrixSymbol
from sympy.printing.mathml import MathMLPresentationPrinter, MathMLContentPrinter
pp = MathMLPresentationPrinter()
# 7.3: MatrixSymbol structure equals ordinary symbol
ms = MatrixSymbol('A_2', 2, 2)
e_ms = pp._print_MatrixSymbol(ms)
e_sym = pp._print_Symbol(Symbol('A_2'))
print("matrixsym:", e_ms.toxml())
print("sym:      ", e_sym.toxml())
ok = (e_ms.nodeName == e_sym.nodeName == 'msub' and e_ms.toxml() == e_sym.toxml())
# 7.4: content printer Symbol unchanged -> node name 'ci'
cp = MathMLContentPrinter()
ci = cp._print_Symbol(Symbol('x'))
print("content x:", ci.nodeName, ci.toxml())
ok &= (ci.nodeName == 'ci')
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_pc.py` → holds on the patched tree (good)

```python
# POSITIVE CONTROL: scripted symbol top-level must NOT be an mi wrapper.
# Base bug wraps as <mi><msub>...</msub></mi>. Patched: top-level is msub.
import sys
from sympy import Symbol
from sympy.printing.mathml import MathMLPresentationPrinter
p = MathMLPresentationPrinter()
ok = True
for nm, exp in [('x_2','msub'), ('x^2','msup'), ('x^3_2','msubsup')]:
    e = p._print_Symbol(Symbol(nm))
    print(nm, "->", e.nodeName, e.toxml())
    ok &= (e.nodeName == exp)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_pc.py`

```python
# POSITIVE CONTROL: scripted symbol top-level must NOT be an mi wrapper.
# Base bug wraps as <mi><msub>...</msub></mi>. Patched: top-level is msub.
import sys
from sympy import Symbol
from sympy.printing.mathml import MathMLPresentationPrinter
p = MathMLPresentationPrinter()
ok = True
for nm, exp in [('x_2','msub'), ('x^2','msup'), ('x^3_2','msubsup')]:
    e = p._print_Symbol(Symbol(nm))
    print(nm, "->", e.nodeName, e.toxml())
    ok &= (e.nodeName == exp)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-15976: MathMLPresentationPrinter._print_Symbol dropped the redundant outer <mi> wrapper around scripted symbols. 7 requirement probes + 1 positive control, all run in the official Docker image.

### PER-PROBE RESULTS (patched tree, base tree):
- probe_1 (Req 1.1-1.3): undecorated Symbol('x') -> node 'mi' with exactly one text child 'x'. HOLDS patched.
- probe_2 (Req 2.1-2.4): Symbol('x_2') -> top-level 'msub', child0 mi='x', child1 mi='2', no outer wrapper. HOLDS patched; VIOLATED at base (base wraps in <mi>).
- probe_3 (Req 3.1-3.4): Symbol('x^2') -> top-level 'msup', child0 mi base, child1 mi supers. HOLDS patched; VIOLATED at base.
- probe_4 (Req 4.1-4.4): Symbol('x^3_2') -> top-level 'msubsup', children [mi base, subscript '2', superscript '3'] (subs before supers). HOLDS patched; VIOLATED at base.
- probe_5 (Req 5.1-5.4): Symbol('x_a_b') multi-piece subscript -> collection is 'mrow' with [mi a, mo=' ', mi b] in order. HOLDS patched.
- probe_6 (Req 6.1-6.3): style='bold' sets mathvariant='bold' on the OUTERMOST element (mi for 'x', msub for 'x_2'); plain has no mathvariant. HOLDS patched.
- probe_7 (Req 7.3, 7.4): _print_MatrixSymbol('A_2') produces identical markup to _print_Symbol('A_2') (msub, byte-identical xml); content printer _print_Symbol still yields node 'ci' (unchanged). HOLDS patched.
- probe_pc (POSITIVE CONTROL, core fix, Req 2/3/4 anti-wrapper): scripted symbols x_2/x^2/x^3_2 have top-level node msub/msup/msubsup (not the buggy outer 'mi'). HOLDS patched; FAILS at base (exit 1). Discriminating power confirmed.

CANDIDATE WRONG PATCH (weak.diff): applies the gold structural fix but SWAPS the msubsup child order (appends supers before subs), violating Req 4.3. Runs at base_commit. Under this candidate probe_4 is REJECTED (VIOLATED) while the other 7 hold -> the suite discriminates a requirements-nonconforming implementation. This is NOT a too-weak finding (a probe rejects it); it demonstrates discrimination.

Verdict SOUND: all 5+ (8) probes hold on the gold-patched tree, the positive control discriminates base vs patched, and a plausible wrong-fix is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_pc.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_pc.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_pc.py`

```python
# POSITIVE CONTROL: scripted symbol top-level must NOT be an mi wrapper.
# Base bug wraps as <mi><msub>...</msub></mi>. Patched: top-level is msub.
import sys
from sympy import Symbol
from sympy.printing.mathml import MathMLPresentationPrinter
p = MathMLPresentationPrinter()
ok = True
for nm, exp in [('x_2','msub'), ('x^2','msup'), ('x^3_2','msubsup')]:
    e = p._print_Symbol(Symbol(nm))
    print(nm, "->", e.nodeName, e.toxml())
    ok &= (e.nodeName == exp)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-15976: MathMLPresentationPrinter._print_Symbol dropped the redundant outer <mi> wrapper around scripted symbols. 7 requirement probes + 1 positive control, all run in the official Docker image.

### PER-PROBE RESULTS (patched tree, base tree):
- probe_1 (Req 1.1-1.3): undecorated Symbol('x') -> node 'mi' with exactly one text child 'x'. HOLDS patched.
- probe_2 (Req 2.1-2.4): Symbol('x_2') -> top-level 'msub', child0 mi='x', child1 mi='2', no outer wrapper. HOLDS patched; VIOLATED at base (base wraps in <mi>).
- probe_3 (Req 3.1-3.4): Symbol('x^2') -> top-level 'msup', child0 mi base, child1 mi supers. HOLDS patched; VIOLATED at base.
- probe_4 (Req 4.1-4.4): Symbol('x^3_2') -> top-level 'msubsup', children [mi base, subscript '2', superscript '3'] (subs before supers). HOLDS patched; VIOLATED at base.
- probe_5 (Req 5.1-5.4): Symbol('x_a_b') multi-piece subscript -> collection is 'mrow' with [mi a, mo=' ', mi b] in order. HOLDS patched.
- probe_6 (Req 6.1-6.3): style='bold' sets mathvariant='bold' on the OUTERMOST element (mi for 'x', msub for 'x_2'); plain has no mathvariant. HOLDS patched.
- probe_7 (Req 7.3, 7.4): _print_MatrixSymbol('A_2') produces identical markup to _print_Symbol('A_2') (msub, byte-identical xml); content printer _print_Symbol still yields node 'ci' (unchanged). HOLDS patched.
- probe_pc (POSITIVE CONTROL, core fix, Req 2/3/4 anti-wrapper): scripted symbols x_2/x^2/x^3_2 have top-level node msub/msup/msubsup (not the buggy outer 'mi'). HOLDS patched; FAILS at base (exit 1). Discriminating power confirmed.

CANDIDATE WRONG PATCH (weak.diff): applies the gold structural fix but SWAPS the msubsup child order (appends supers before subs), violating Req 4.3. Runs at base_commit. Under this candidate probe_4 is REJECTED (VIOLATED) while the other 7 hold -> the suite discriminates a requirements-nonconforming implementation. This is NOT a too-weak finding (a probe rejects it); it demonstrates discrimination.

Verdict SOUND: all 5+ (8) probes hold on the gold-patched tree, the positive control discriminates base vs patched, and a plausible wrong-fix is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The pre-patch code created x=<mi> and appended msub/msup/msubsup into it, yielding the redundant <mi><msub>...</msub></mi> wrapper that broke Safari rendering (the issue). The gold patch reassigns x directly to the scripted element (or mname for undecorated), removing the outer mi, and moves the bold-attribute set to after x is finalized so it lands on the top-level element. Requirements 1-6 pin exactly this changed observable behavior (the top-level node name and absence of the mi wrapper), which is the correct modeling boundary — not a narrow slice/single branch. Requirement 4's child order (sub before sup) and Requirement 5's mrow/mo separator layout are preserved verbatim from pre-patch and correctly required. Requirement 7 correctly fences off unchanged behavior (content printer, MatrixSymbol structure). Probes on gold-patched tree pass exit 0 for all requirements.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the behavioral fix (remove the redundant outer <mi> wrapper so a scripted symbol renders as msub/msup/msubsup, or a bare mi when undecorated) and localize it to _print_Symbol (reached via _print_MatrixSymbol/_print_RandomSymbol) in sympy/printing/mathml.py. All of this is legitimate: naming the module/method localizes the change, and the four decoration branches (none / subs-only / sups-only / both) mirror the gold patch's own control-flow structure and the natural behavior space, not the test list. Example names cited (x2 from the public problem_statement; x^2, x_2, x^3_2, x__2 as illustrative sub/superscript notation) are standard SymPy syntax describing behavior; crucially the doc does NOT expose the multi-piece test inputs (x_2_a, x^2^a, x__2__a, x__3_2) — Req 5 states the multi-piece mrow/mo/space layout generically as behavior. The mrow/mo/mi node names and the ' ' separator come from the pre-existing join() helper preserved by the gold (not fix-invented). No test file path, no test function name (test_presentation_symbol), no quoted assertion code (nodeName/childNodes/nodeValue chains), no parametrization ids, and no fix-invented identifiers appear. The document translates what the tests check into requirements — the intended purpose — without transmitting the tests themselves.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
