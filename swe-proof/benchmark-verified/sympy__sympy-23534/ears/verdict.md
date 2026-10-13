# P2 adversarial audit — sympy__sympy-23534

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.2 (positive control): symbols(('q:2','u:2'), cls=Function) yields
UndefinedFunction instances in both groups, structured as two sub-tuples."""
import sys
from sympy import symbols
from sympy.core.function import Function, UndefinedFunction

res = symbols(('q:2', 'u:2'), cls=Function)
print("result:", res)
print("types:", [[type(x).__name__ for x in grp] for grp in res])

ok = (
    isinstance(res, tuple) and len(res) == 2
    and all(isinstance(grp, tuple) and len(grp) == 2 for grp in res)
    and all(isinstance(x, UndefinedFunction) for grp in res for x in grp)
)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.4: nested collection - cls applied at every level of nesting.
Use a doubly-nested collection; all leaves must be UndefinedFunction."""
import sys
from sympy import symbols
from sympy.core.function import Function, UndefinedFunction

res = symbols((('a', 'b'), ('c:2',)), cls=Function)
print("result:", res)

def leaves(x):
    if isinstance(x, (tuple, list)):
        for e in x:
            yield from leaves(e)
    else:
        yield x

lv = list(leaves(res))
print("leaf types:", [type(x).__name__ for x in lv])
ok = len(lv) >= 3 and all(isinstance(x, UndefinedFunction) for x in lv)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.3 + Req2.1/2.2: collection WITHOUT cls -> default Symbol; structure,
outer container type (list), ordering, and range expansion preserved."""
import sys
from sympy import symbols
from sympy.core.symbol import Symbol

res = symbols(['q:2', 'u:2'])   # list input
print("result:", res, "outer type:", type(res).__name__)

ok = (
    isinstance(res, list) and len(res) == 2
    and all(isinstance(g, tuple) and len(g) == 2 for g in res)
    and all(isinstance(x, Symbol) and type(x).__name__ == 'Symbol' for g in res for x in g)
    and str(res[0][0]) == 'q0' and str(res[0][1]) == 'q1'
    and str(res[1][0]) == 'u0' and str(res[1][1]) == 'u1'
)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.3: assumptions applied to every object in a collection, alongside cls-less.
And Req2.3 with cls: assumptions still forwarded when cls given."""
import sys
from sympy import symbols
from sympy.core.symbol import Symbol

res = symbols(('x:2', 'y:2'), real=True, positive=True)
print("result:", res)
allobj = [x for g in res for x in g]
ok = len(allobj) == 4 and all(x.is_real and x.is_positive for x in allobj)

# integer assumption with a nested range spec (groups are tuples)
res2 = symbols(('m:2', 'n:2'), integer=True)
allobj2 = [x for g in res2 for x in g]
ok = ok and all(x.is_integer for x in allobj2)
print("real/pos ok:", all(x.is_real and x.is_positive for x in allobj))
print("integer ok:", all(x.is_integer for x in allobj2))
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3: single-string regression protection.
3.1 cls applied for single string; 3.2 range/comma parsing; 3.3 scalar contract;
3.4 assumptions; 3.5 malformed input raises."""
import sys
from sympy import symbols
from sympy.core.symbol import Symbol
from sympy.core.function import UndefinedFunction

ok = True

# 3.1 single string cls=Function
fs = symbols('f,g,h', cls=__import__('sympy').Function)
print("3.1:", fs, [type(x).__name__ for x in fs])
ok = ok and all(isinstance(x, UndefinedFunction) for x in fs)

# 3.2 range parsing / ordering
r = symbols('a:3')
print("3.2:", r)
ok = ok and tuple(str(x) for x in r) == ('a0', 'a1', 'a2')

# 3.3 scalar vs sequence
s = symbols('z')
print("3.3:", s, type(s).__name__)
ok = ok and isinstance(s, Symbol) and not isinstance(s, tuple)
seq = symbols('z,')  # trailing comma forces sequence
ok = ok and isinstance(seq, tuple) and len(seq) == 1

# 3.4 assumptions single string
p = symbols('p', positive=True)
ok = ok and p.is_positive

# 3.5 malformed raises
raised = False
try:
    symbols('')
except ValueError:
    raised = True
print("3.5 empty raised:", raised)
ok = ok and raised

raised2 = False
try:
    symbols('a:')  # range missing end -> should error
except (ValueError, Exception):
    raised2 = True
print("3.5 range-missing-end raised:", raised2)
ok = ok and raised2

print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.2 (positive control): symbols(('q:2','u:2'), cls=Function) yields
UndefinedFunction instances in both groups, structured as two sub-tuples."""
import sys
from sympy import symbols
from sympy.core.function import Function, UndefinedFunction

res = symbols(('q:2', 'u:2'), cls=Function)
print("result:", res)
print("types:", [[type(x).__name__ for x in grp] for grp in res])

ok = (
    isinstance(res, tuple) and len(res) == 2
    and all(isinstance(grp, tuple) and len(grp) == 2 for grp in res)
    and all(isinstance(x, UndefinedFunction) for grp in res for x in grp)
)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix: in the non-string branch of symbols(), recursion changed from symbols(name, **args) to symbols(name, cls=cls, **args). Probe coverage: probe_1 (Req1.2, positive control) symbols(('q:2','u:2'),cls=Function) -> two sub-tuples of UndefinedFunction; probe_2 (Req1.4) doubly-nested collection, cls applied at all levels; probe_3 (Req1.3/2.1/2.2) collection without cls -> Symbol, list outer type preserved, range expansion/order q0,q1,u0,u1; probe_4 (Req2.3) real/positive & integer assumptions applied to every object in nested-range collections; probe_5 (Req3.1-3.5) single-string regression: cls=Function, range parsing a0..a2, scalar-vs-sequence contract, positive assumption, empty & missing-end errors. Results: all 5 HOLD on gold-patched tree. Positive control probe_1 FAILS at base (objects are Symbol not UndefinedFunction) => discriminating. Candidate patches: noop.diff (comment only, cls still not forwarded) rejected by probes 1&2; weak.diff (forwards cls but drops **args in recursion) rejected by probe_4 (assumptions lost). Both requirements-plausible wrong fixes are caught; suite discriminates. No too-weak patch found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Req1.2 (positive control): symbols(('q:2','u:2'), cls=Function) yields
UndefinedFunction instances in both groups, structured as two sub-tuples."""
import sys
from sympy import symbols
from sympy.core.function import Function, UndefinedFunction

res = symbols(('q:2', 'u:2'), cls=Function)
print("result:", res)
print("types:", [[type(x).__name__ for x in grp] for grp in res])

ok = (
    isinstance(res, tuple) and len(res) == 2
    and all(isinstance(grp, tuple) and len(grp) == 2 for grp in res)
    and all(isinstance(x, UndefinedFunction) for grp in res for x in grp)
)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix: in the non-string branch of symbols(), recursion changed from symbols(name, **args) to symbols(name, cls=cls, **args). Probe coverage: probe_1 (Req1.2, positive control) symbols(('q:2','u:2'),cls=Function) -> two sub-tuples of UndefinedFunction; probe_2 (Req1.4) doubly-nested collection, cls applied at all levels; probe_3 (Req1.3/2.1/2.2) collection without cls -> Symbol, list outer type preserved, range expansion/order q0,q1,u0,u1; probe_4 (Req2.3) real/positive & integer assumptions applied to every object in nested-range collections; probe_5 (Req3.1-3.5) single-string regression: cls=Function, range parsing a0..a2, scalar-vs-sequence contract, positive assumption, empty & missing-end errors. Results: all 5 HOLD on gold-patched tree. Positive control probe_1 FAILS at base (objects are Symbol not UndefinedFunction) => discriminating. Candidate patches: noop.diff (comment only, cls still not forwarded) rejected by probes 1&2; weak.diff (forwards cls but drops **args in recursion) rejected by probe_4 (assumptions lost). Both requirements-plausible wrong fixes are caught; suite discriminates. No too-weak patch found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a one-liner: in symbols(), the non-string `names` collection branch changes `result.append(symbols(name, **args))` to `symbols(name, cls=cls, **args)`, forwarding the caller's cls into recursive processing. Requirements pin exactly this observable change. Verified on patched tree: symbols(('q:2','u:2'), cls=Function) -> each element isinstance UndefinedFunction (Req1.2); deep nesting (('a','b'),('c','d')) all UndefinedFunction (Req1.4); default no-cls -> Symbol (Req1.3); outer container type preserved as list for list input (Req2.1); real=True applied to grouped objects (Req2.3); single-string 'f,g,h' cls=Function -> UndefinedFunction (Req3.1); scalar 'x' -> Symbol not tuple (Req3.3); symbols('') raises ValueError (Req3.5). At base_commit the nested cls probe fails (q[0] is Symbol, AssertionError) exactly as the problem_statement's 'Actual result'. The requirements model the changed behavior (cls honored uniformly across nested/grouped collections) rather than a narrow slice, and the regression clauses correctly describe preserved behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document's driving example `symbols(('q:2', 'u:2'), cls=Function)` and the expected `UndefinedFunction`/`Symbol` result types are taken verbatim from the PUBLIC problem_statement (which contains that exact code and expected/actual result). The hidden test (test_symbols, asserting `type(symbols(('q:2','u:2'), cls=Function)[0][0]) == UndefinedFunction`) merely encodes that same public example, so echoing it is not a leak. The gold edit (`symbols(name, cls=cls, **args)`) invents no new identifier — `cls` is a documented public kwarg. No test file paths, function names (test_symbols etc.), parametrization ids, or verbatim gold lines appear. Requirement 3's enumeration of string-parsing forms (colon/lettered/parenthesized ranges, escaped separators, empty spec, missing end) describes general documented `symbols` behavior for regression protection, not the hidden test's cases — the PASS_TO_PASS/FAIL_TO_PASS sets do not enumerate these. Naming the module/function under change is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
