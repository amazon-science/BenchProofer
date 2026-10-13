# P2 adversarial audit — sympy__sympy-18763

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
"""Positive control (Req 1.4): coefficient * Subs keeps parens around whole body.
HOLDS on patched, FAILS at base."""
from sympy import Subs, latex
from sympy.abc import x, y
out = latex(3*Subs(-x+y, (x,), (1,)))
print("observed:", repr(out))
expected = r'3 \left. \left(- x + y\right) \right|_{\substack{ x=1 }}'
print("expected:", repr(expected))
import sys
sys.exit(0 if out == expected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.2/2.1/2.3: full-shape render of two-assignment Subs."""
from sympy import Subs, latex
from sympy.abc import x, y
out = latex(Subs(x*y, (x, y), (1, 2)))
print("observed:", repr(out))
expected = r'\left. \left(x y\right) \right|_{\substack{ x=1\\ y=2 }}'
print("expected:", repr(expected))
import sys
sys.exit(0 if out == expected else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.3: body always wrapped in \\left( ... \\right) even for atomic body.
Check the structural markers are present regardless of body structure."""
from sympy import Subs, latex
from sympy.abc import x, y, z
import sys
ok = True
for body in [x, x*y, -x+y, x**2 + z]:
    out = latex(Subs(body, (x,), (1,)))
    print("body", body, "->", repr(out))
    if r'\left(' not in out or r'\right)' not in out:
        print("  MISSING body parens")
        ok = False
    # the \left( must sit right after the opening \left.
    if r'\left. \left(' not in out:
        print("  parens not directly left of restriction")
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.5: outer restriction layout preserved: \\left. <group> \\right|_{\\substack{ ... }}
with exact surrounding single spaces."""
from sympy import Subs, latex
from sympy.abc import x, y
import re, sys
out = latex(Subs(x*y, (x,), (1,)))
print("observed:", repr(out))
pat = re.compile(r'^\\left\. \\left\(.*\\right\) \\right\|_\{\\substack\{ .* \}\}$')
sys.exit(0 if pat.match(out) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.2/2.3: assignment pairs rendered old=new in order, separated by '\\\\ '."""
from sympy import Subs, latex, Symbol
import sys
a, b, c = Symbol('a'), Symbol('b'), Symbol('c')
out = latex(Subs(a+b+c, (a, b, c), (1, 2, 3)))
print("observed:", repr(out))
# subscript must contain exactly the ordered pairs separated by '\\ '
sub = out.split(r'_{\substack{ ')[1].rsplit(r' }}', 1)[0]
print("subscript:", repr(sub))
expected_sub = r'a=1\\ b=2\\ c=3'
sys.exit(0 if sub == expected_sub else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 2.4: body rendered via normal recursive latex, no extra wrapping beyond
the Req-1 body parens. Strip the one body-paren layer and compare to bare latex."""
from sympy import Subs, latex
from sympy.abc import x, y
import sys
body = -x + y
out = latex(Subs(body, (x,), (1,)))
print("observed:", repr(out))
# extract what is between \left( and \right)
inner = out.split(r'\left(', 1)[1].rsplit(r'\right)', 1)[0]
print("inner:", repr(inner))
bare = latex(body)
print("bare body latex:", repr(bare))
sys.exit(0 if inner == bare else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 1.4): coefficient * Subs keeps parens around whole body.
HOLDS on patched, FAILS at base."""
from sympy import Subs, latex
from sympy.abc import x, y
out = latex(3*Subs(-x+y, (x,), (1,)))
print("observed:", repr(out))
expected = r'3 \left. \left(- x + y\right) \right|_{\substack{ x=1 }}'
print("expected:", repr(expected))
import sys
sys.exit(0 if out == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: _print_Subs in sympy/printing/latex.py must wrap the Subs body in \left(...\right).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.4, POSITIVE CONTROL): latex(3*Subs(-x+y,(x,),(1,))) == '3 \left. \left(- x + y\right) \right|_{\substack{ x=1 }}'. HOLDS patched, FAILS at base (base emits bare '- x + y'), so it discriminates the fix.
- probe_2 (Req 1.1/1.2/2.1/2.3): full-shape two-assignment Subs(x*y,(x,y),(1,2)) exact expected string.
- probe_3 (Req 1.1/1.3): body always wrapped with \left( immediately after \left. for atomic and compound bodies (x, x*y, -x+y, x**2+z).
- probe_4 (Req 2.1/2.5): regex enforces exact outer layout \left. \left(...\right) \right|_{\substack{ ... }} with the required single spaces.
- probe_5 (Req 2.2/2.3): three-assignment subscript rendered old=new in order, separated by '\\ ' => 'a=1\\ b=2\\ c=3'.
- probe_6 (Req 2.4): the inner group content equals the bare recursive latex of the body (no extra wrapping beyond the Req-1 parens).

DISCRIMINATION: weak candidate 'plain_parens' replaces \left(...\right) with literal (...). Req 1.1 explicitly mandates \left(/\right) sized delimiters, so this is a requirements-non-conforming lazy fix. Probes 1,2,3,4 all REJECT it (probe_3 shows body parens absent per the \left( marker; probes 1/2/4 show string/regex mismatch). This proves the suite distinguishes the correct sized-delimiter fix from a naive parenthesization.

VERDICT: SOUND — 6 distinct probes all hold on the patched tree, the positive control discriminates (holds patched / fails at base), and a plausibly-wrong requirements-non-conforming alternative is rejected by the suite.

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
"""Positive control (Req 1.4): coefficient * Subs keeps parens around whole body.
HOLDS on patched, FAILS at base."""
from sympy import Subs, latex
from sympy.abc import x, y
out = latex(3*Subs(-x+y, (x,), (1,)))
print("observed:", repr(out))
expected = r'3 \left. \left(- x + y\right) \right|_{\substack{ x=1 }}'
print("expected:", repr(expected))
import sys
sys.exit(0 if out == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: _print_Subs in sympy/printing/latex.py must wrap the Subs body in \left(...\right).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.4, POSITIVE CONTROL): latex(3*Subs(-x+y,(x,),(1,))) == '3 \left. \left(- x + y\right) \right|_{\substack{ x=1 }}'. HOLDS patched, FAILS at base (base emits bare '- x + y'), so it discriminates the fix.
- probe_2 (Req 1.1/1.2/2.1/2.3): full-shape two-assignment Subs(x*y,(x,y),(1,2)) exact expected string.
- probe_3 (Req 1.1/1.3): body always wrapped with \left( immediately after \left. for atomic and compound bodies (x, x*y, -x+y, x**2+z).
- probe_4 (Req 2.1/2.5): regex enforces exact outer layout \left. \left(...\right) \right|_{\substack{ ... }} with the required single spaces.
- probe_5 (Req 2.2/2.3): three-assignment subscript rendered old=new in order, separated by '\\ ' => 'a=1\\ b=2\\ c=3'.
- probe_6 (Req 2.4): the inner group content equals the bare recursive latex of the body (no extra wrapping beyond the Req-1 parens).

DISCRIMINATION: weak candidate 'plain_parens' replaces \left(...\right) with literal (...). Req 1.1 explicitly mandates \left(/\right) sized delimiters, so this is a requirements-non-conforming lazy fix. Probes 1,2,3,4 all REJECT it (probe_3 shows body parens absent per the \left( marker; probes 1/2/4 show string/regex mismatch). This proves the suite distinguishes the correct sized-delimiter fix from a naive parenthesization.

VERDICT: SOUND — 6 distinct probes all hold on the patched tree, the positive control discriminates (holds patched / fails at base), and a plausibly-wrong requirements-non-conforming alternative is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Change is a one-line string-template edit in _print_Subs. Requirements correctly (a) mandate the new \left(body\right) wrap regardless of body structure, (b) preserve the outer \left. ... \right|_{\substack{...}} layout, assignment pairing/=/separators, and surrounding spaces, and (c) capture the product-embedding case (3*Subs) that is the actual bug from the issue and the added F2P test. Both test-patch assertions match probe output. Faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The exact target LaTeX layout `\left. \left(<body>\right) \right|_{\substack{...}}`, the coefficient-times-Subs scenario, and the single-assignment `x=1` case are ALL public in problem_statement (which shows both the buggy and desired output verbatim). Requirements name the module/function (`_print_Subs`, sympy/printing/latex.py) — legitimate localization. Req 2.3's mention of the multi-pair `\ ` separator describes the printer's pre-existing (unchanged) multi-assignment behavior, derivable from source, not the hidden two-assignment test values `Subs(x*y,(x,y),(1,2))`. No test names/paths/ids (test_latex_subs), no quoted test code, no fix-invented identifiers (the one-line gold fix invents none), and no case enumeration mirroring the parametrization. Purely behavioral translation.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
