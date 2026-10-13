# P2 adversarial audit — sphinx-doc__sphinx-7757

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
"""Positive control: Req1.4 — (a, b=0, /, c=1) full expected shape."""
import sys
from sphinx.util.inspect import signature_from_str
from inspect import Parameter

sig = signature_from_str('(a, b=0, /, c=1)')
p = sig.parameters
keys = list(p.keys())
print("keys:", keys)
for k in keys:
    print(k, p[k].kind, repr(p[k].default))

ok = (
    keys == ['a', 'b', 'c']
    and p['a'].kind == Parameter.POSITIONAL_ONLY and p['a'].default is Parameter.empty
    and p['b'].kind == Parameter.POSITIONAL_ONLY and p['b'].default == '0'
    and p['c'].kind == Parameter.POSITIONAL_OR_KEYWORD and p['c'].default == '1'
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3 & Req2.2: positional-only without default stays empty; rightmost alignment.
Signature (a, b, c=1, /) : three posonly, one default -> only c carries '1'."""
import sys
from sphinx.util.inspect import signature_from_str
from inspect import Parameter

sig = signature_from_str('(a, b, c=1, /)')
p = sig.parameters
for k in p:
    print(k, p[k].kind, repr(p[k].default))
ok = (
    list(p) == ['a', 'b', 'c']
    and all(p[k].kind == Parameter.POSITIONAL_ONLY for k in ['a', 'b', 'c'])
    and p['a'].default is Parameter.empty
    and p['b'].default is Parameter.empty
    and p['c'].default == '1'
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3: combined positional run right-to-left across the / boundary.
(a, b=1, /, c=2, d=3): 4 positional params, 3 supplied defaults ->
rightmost 3 (b,c,d) carry defaults, a is empty; defaults spill onto posonly b."""
import sys
from sphinx.util.inspect import signature_from_str
from inspect import Parameter

sig = signature_from_str('(a, b=1, /, c=2, d=3)')
p = sig.parameters
for k in p:
    print(k, p[k].kind, repr(p[k].default))
ok = (
    list(p) == ['a', 'b', 'c', 'd']
    and p['a'].kind == Parameter.POSITIONAL_ONLY and p['a'].default is Parameter.empty
    and p['b'].kind == Parameter.POSITIONAL_ONLY and p['b'].default == '1'
    and p['c'].kind == Parameter.POSITIONAL_OR_KEYWORD and p['c'].default == '2'
    and p['d'].kind == Parameter.POSITIONAL_OR_KEYWORD and p['d'].default == '3'
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1-3.5: regression — kwonly defaults, varargs kinds, annotations, return annotation.
Signature: (x: int, y=2, *args, k: str = 'a', m, **kw) -> bool"""
import sys
from sphinx.util.inspect import signature_from_str
from inspect import Parameter

sig = signature_from_str("(x: int, y=2, *args, k: str = 'a', m, **kw) -> bool")
p = sig.parameters
for k in p:
    print(k, p[k].kind, "def=", repr(p[k].default), "ann=", repr(p[k].annotation))
print("return:", repr(sig.return_annotation))
ok = (
    list(p) == ['x', 'y', 'args', 'k', 'm', 'kw']
    and p['x'].kind == Parameter.POSITIONAL_OR_KEYWORD and p['x'].default is Parameter.empty and p['x'].annotation == 'int'
    and p['y'].kind == Parameter.POSITIONAL_OR_KEYWORD and p['y'].default == '2' and p['y'].annotation is Parameter.empty
    and p['args'].kind == Parameter.VAR_POSITIONAL and p['args'].default is Parameter.empty
    and p['k'].kind == Parameter.KEYWORD_ONLY and p['k'].default == "'a'" and p['k'].annotation == 'str'
    and p['m'].kind == Parameter.KEYWORD_ONLY and p['m'].default is Parameter.empty
    and p['kw'].kind == Parameter.VAR_KEYWORD and p['kw'].default is Parameter.empty
    and sig.return_annotation == 'bool'
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.6: various literal/expression default forms rendered as source text.
Req3.7: invalid signature raises SyntaxError. Also posonly default expr forms."""
import sys
from sphinx.util.inspect import signature_from_str
from inspect import Parameter

# 3.6: posonly params carrying rich default expressions
sig = signature_from_str("(a=None, b=[1, 2], c={'x': 1}, /)")
p = sig.parameters
for k in p:
    print(k, p[k].kind, repr(p[k].default))
ok_defaults = (
    p['a'].kind == Parameter.POSITIONAL_ONLY and p['a'].default == 'None'
    and p['b'].default in ('[1, 2]',)
    and p['c'].default in ("{'x': 1}",)
)

# 3.7: syntax error
ok_syntax = False
try:
    signature_from_str("(a, /, b, ??)")
except SyntaxError:
    ok_syntax = True
    print("SyntaxError raised as required")
except Exception as e:
    print("wrong exception:", type(e).__name__)

ok = ok_defaults and ok_syntax
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1.4 — (a, b=0, /, c=1) full expected shape."""
import sys
from sphinx.util.inspect import signature_from_str
from inspect import Parameter

sig = signature_from_str('(a, b=0, /, c=1)')
p = sig.parameters
keys = list(p.keys())
print("keys:", keys)
for k in keys:
    print(k, p[k].kind, repr(p[k].default))

ok = (
    keys == ['a', 'b', 'c']
    and p['a'].kind == Parameter.POSITIONAL_ONLY and p['a'].default is Parameter.empty
    and p['b'].kind == Parameter.POSITIONAL_ONLY and p['b'].default == '0'
    and p['c'].kind == Parameter.POSITIONAL_OR_KEYWORD and p['c'].default == '1'
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover signature_from_str preserving defaults on positional-only params. 5 probes: P1 (Req1.4, positive control) exact shape of (a,b=0,/,c=1); P2 (Req1.3/2.2) (a,b,c=1,/) posonly right-alignment, only rightmost carries default; P3 (Req2.1/2.2/2.3) combined-run right-to-left across the / boundary (a,b=1,/,c=2,d=3); P4 (Req3.1-3.5 regression) kwonly defaults, *args/**kw kinds, annotations, return annotation; P5 (Req3.6/3.7) rich default expr forms on posonly + SyntaxError on invalid input.

Results on PATCHED tree: all 5 HOLD (exit 0). At BASE: P1,P2,P3,P5 VIOLATED (exit 1), P4 HOLDS (pure regression, correctly unchanged). Positive control P1 fails at base and holds patched -> discriminates; prepatch reproduced.

Wrong-fix candidate 'naive_posonly_group_alignment' (weak.diff): right-aligns args.defaults independently WITHIN the posonly group instead of treating posonly+pos-or-kw as one combined run. Verified applies at base_commit. Probe results under candidate: P1 VIOLATED (b gets empty instead of '0' because defaults consumed by pos-or-kw loop), P3 VIOLATED (a wrongly gets '2'). So the suite REJECTS this plausible-but-wrong partial fix -> requirements are not too weak on Req2's combined-run semantics. P2/P4/P5 happen to hold under it (no cross-boundary default there). Suite discriminates wrong implementations; >=5 probes hold patched; positive control discriminates -> SOUND.

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
"""Positive control: Req1.4 — (a, b=0, /, c=1) full expected shape."""
import sys
from sphinx.util.inspect import signature_from_str
from inspect import Parameter

sig = signature_from_str('(a, b=0, /, c=1)')
p = sig.parameters
keys = list(p.keys())
print("keys:", keys)
for k in keys:
    print(k, p[k].kind, repr(p[k].default))

ok = (
    keys == ['a', 'b', 'c']
    and p['a'].kind == Parameter.POSITIONAL_ONLY and p['a'].default is Parameter.empty
    and p['b'].kind == Parameter.POSITIONAL_ONLY and p['b'].default == '0'
    and p['c'].kind == Parameter.POSITIONAL_OR_KEYWORD and p['c'].default == '1'
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover signature_from_str preserving defaults on positional-only params. 5 probes: P1 (Req1.4, positive control) exact shape of (a,b=0,/,c=1); P2 (Req1.3/2.2) (a,b,c=1,/) posonly right-alignment, only rightmost carries default; P3 (Req2.1/2.2/2.3) combined-run right-to-left across the / boundary (a,b=1,/,c=2,d=3); P4 (Req3.1-3.5 regression) kwonly defaults, *args/**kw kinds, annotations, return annotation; P5 (Req3.6/3.7) rich default expr forms on posonly + SyntaxError on invalid input.

Results on PATCHED tree: all 5 HOLD (exit 0). At BASE: P1,P2,P3,P5 VIOLATED (exit 1), P4 HOLDS (pure regression, correctly unchanged). Positive control P1 fails at base and holds patched -> discriminates; prepatch reproduced.

Wrong-fix candidate 'naive_posonly_group_alignment' (weak.diff): right-aligns args.defaults independently WITHIN the posonly group instead of treating posonly+pos-or-kw as one combined run. Verified applies at base_commit. Probe results under candidate: P1 VIOLATED (b gets empty instead of '0' because defaults consumed by pos-or-kw loop), P3 VIOLATED (a wrongly gets '2'). So the suite REJECTS this plausible-but-wrong partial fix -> requirements are not too weak on Req2's combined-run semantics. P2/P4/P5 happen to hold under it (no cross-boundary default there). Suite discriminates wrong implementations; >=5 probes hold patched; positive control discriminates -> SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch modifies signature_from_str to build a combined `defaults` list left-padded with Parameter.empty to `positionals = len(posonlyargs)+len(args)`, then indexes posonly defaults by i and pok defaults by i+posonlyargs. Requirement 2's 'single ordered positional run, rightmost k get the k defaults' is a precise natural-language rendering of exactly that left-pad-then-index logic. The modeling boundary is the changed observable behavior (Parameter.default across the whole positional run), not a narrow branch. Probe HOLDS on patched tree (exit 0), VIOLATED on base (exit 1 at the b='0' assertion).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The signature example `(a, b=0, /, c=1)` and its a/b/c outcomes (Req 1.4) come straight from the PUBLIC problem_statement (`foo(a, b=0, /, c=1)`) — not from the hidden test. The hidden test's only distinguishing content is the exact assertions (kinds POSITIONAL_ONLY/POSITIONAL_OR_KEYWORD, defaults '0'/'1'/empty), which are simply the correct behavior implied by the public repro. Named symbols — signature_from_str, sphinx/util/inspect.py, Parameter.POSITIONAL_ONLY/POSITIONAL_OR_KEYWORD/KEYWORD_ONLY/VAR_POSITIONAL/VAR_KEYWORD/empty — are legitimate localization plus Python stdlib names, not fix-invented. The gold patch's actual new identifiers (posonlyargs, positionals, defaults list, the right-to-left insert loop) do NOT appear verbatim; Req 2's right-to-left alignment is a behavioral description of Python default semantics, not quoted gold code. No test file paths, test/function names, or parametrization ids are present. Req 3's enumeration of parameter kinds describes general parser behavior, not test cases (the F2P test only exercises positional-only defaults). No leakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
