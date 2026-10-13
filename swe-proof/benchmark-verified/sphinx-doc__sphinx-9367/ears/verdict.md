# P2 adversarial audit — sphinx-doc__sphinx-9367

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
"""R1.1/R1.3 positive control: single-element tuple renders with trailing comma."""
import ast
from sphinx.pycode.ast import unparse

node = ast.parse("(1,)", mode="eval").body
assert isinstance(node, ast.Tuple), "expected a Tuple node"
out = unparse(node)
print("single-element tuple (1,) ->", repr(out))
ok = out == "(1,)"
print("holds:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2: single comma immediately after element, no space, no extra comma.
Uses a non-trivial element to confirm the element itself is unparsed normally."""
import ast
from sphinx.pycode.ast import unparse

node = ast.parse("(a.b,)", mode="eval").body
assert isinstance(node, ast.Tuple)
out = unparse(node)
print("(a.b,) ->", repr(out))
ok = out == "(a.b,)"
# also verify no ', ' and exactly one comma
ok = ok and out.count(",") == 1 and ", " not in out
print("holds:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.1: empty tuple renders as ()."""
import ast
from sphinx.pycode.ast import unparse

node = ast.parse("()", mode="eval").body
assert isinstance(node, ast.Tuple)
out = unparse(node)
print("() ->", repr(out))
ok = out == "()"
print("holds:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.2: multi-element tuple joined by ', ', no trailing comma."""
import ast
from sphinx.pycode.ast import unparse

for src, exp in [("(1, 2, 3)", "(1, 2, 3)"), ("(1, 2)", "(1, 2)")]:
    node = ast.parse(src, mode="eval").body
    assert isinstance(node, ast.Tuple)
    out = unparse(node)
    print(src, "->", repr(out))
    if out != exp:
        print("MISMATCH expected", exp)
        raise SystemExit(1)
print("holds: True")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R2.3: other expression node kinds render unchanged (regression guard).
Covers names, attribute, num/str/bytes, unary op, list, set, dict, subscript,
lambda, ellipsis."""
import ast
from sphinx.pycode.ast import unparse

cases = {
    "foo": "foo",
    "a.b.c": "a.b.c",
    "1": "1",
    "'hi'": "'hi'",
    "b'x'": "b'x'",
    "-1": "- 1",
    "not x": "not x",
    "[1, 2]": "[1, 2]",
    "{1, 2}": "{1, 2}",
    "{1: 2}": "{1: 2}",
    "a[0]": "a[0]",
    "...": "...",
}
bad = []
for src, exp in cases.items():
    out = unparse(ast.parse(src, mode="eval").body)
    print(src, "->", repr(out), "(expect", repr(exp) + ")")
    if out != exp:
        bad.append((src, out, exp))
# lambda renders body as ellipsis (cut-down unparser)
lam = unparse(ast.parse("lambda x: x", mode="eval").body)
print("lambda x: x ->", repr(lam))
if lam != "lambda x: ...":
    bad.append(("lambda", lam, "lambda x: ..."))
print("mismatches:", bad)
raise SystemExit(0 if not bad else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1/R1.3 positive control: single-element tuple renders with trailing comma."""
import ast
from sphinx.pycode.ast import unparse

node = ast.parse("(1,)", mode="eval").body
assert isinstance(node, ast.Tuple), "expected a Tuple node"
out = unparse(node)
print("single-element tuple (1,) ->", repr(out))
ok = out == "(1,)"
print("holds:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes visit_Tuple in sphinx/pycode/ast.py to render single-element tuples with a trailing comma. Probes cover every acceptance criterion:
- probe_1 (R1.1/R1.3): (1,) -> '(1,)'. POSITIVE CONTROL: holds patched, FAILS at base ('(1)'). Reproduced at base.
- probe_2 (R1.2): (a.b,) -> '(a.b,)', exactly one comma, no ', ' separating space; element unparsed normally. FAILS at base ('(a.b)').
- probe_3 (R2.1): () -> '()'.
- probe_4 (R2.2): (1,2,3) -> '(1, 2, 3)' and (1,2) -> '(1, 2)', no trailing comma.
- probe_5 (R2.3 regression): names/attribute/num/str/bytes/unary/list/set/dict/subscript/lambda/ellipsis unchanged. (Note: this old sphinx image renders USub as '- 1' and lambda body as '...'; expectations pinned to actual gold behavior.)
All 5 HOLD on the patched tree. Positive control discriminates (fails base, holds patched).
CANDIDATE PATCH weak_partial.diff: implements the single-element case as '(%s ,)' (space before comma). Applies at base_commit; REJECTED by probe_1 and probe_2 (violates R1.2 'no separating space'), demonstrating the suite discriminates a plausibly-wrong fix. Probes 3/4/5 correctly still hold under it. No requirements-conforming-yet-wrong alternative found.

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
"""R1.1/R1.3 positive control: single-element tuple renders with trailing comma."""
import ast
from sphinx.pycode.ast import unparse

node = ast.parse("(1,)", mode="eval").body
assert isinstance(node, ast.Tuple), "expected a Tuple node"
out = unparse(node)
print("single-element tuple (1,) ->", repr(out))
ok = out == "(1,)"
print("holds:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes visit_Tuple in sphinx/pycode/ast.py to render single-element tuples with a trailing comma. Probes cover every acceptance criterion:
- probe_1 (R1.1/R1.3): (1,) -> '(1,)'. POSITIVE CONTROL: holds patched, FAILS at base ('(1)'). Reproduced at base.
- probe_2 (R1.2): (a.b,) -> '(a.b,)', exactly one comma, no ', ' separating space; element unparsed normally. FAILS at base ('(a.b)').
- probe_3 (R2.1): () -> '()'.
- probe_4 (R2.2): (1,2,3) -> '(1, 2, 3)' and (1,2) -> '(1, 2)', no trailing comma.
- probe_5 (R2.3 regression): names/attribute/num/str/bytes/unary/list/set/dict/subscript/lambda/ellipsis unchanged. (Note: this old sphinx image renders USub as '- 1' and lambda body as '...'; expectations pinned to actual gold behavior.)
All 5 HOLD on the patched tree. Positive control discriminates (fails base, holds patched).
CANDIDATE PATCH weak_partial.diff: implements the single-element case as '(%s ,)' (space before comma). Applies at base_commit; REJECTED by probe_1 and probe_2 (violates R1.2 'no separating space'), demonstrating the suite discriminates a plausibly-wrong fix. Probes 3/4/5 correctly still hold under it. No requirements-conforming-yet-wrong alternative found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a 3-branch rewrite of visit_Tuple in sphinx/pycode/ast.py (len==0 -> '()', len==1 -> '(x,)', else -> '(...)'). Probe on gold-patched instance image confirmed: single=(1,), empty=(), multi=(1, 2, 3), all assertions pass (exit 0). Requirements' modeling boundary correctly targets the changed observable (single-element trailing comma), not a narrow helper or unrelated slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The single-element tuple fix and its `(1,)`->`(1,)` example, plus the test file path, are all public in problem_statement. The `()` and `(1, 2, 3)` examples are obvious tuple behavior / the existing source branch. Req 2.3's node-kind enumeration mirrors the public visit_* handlers in sphinx/pycode/ast.py (legitimate localization of 'preserve existing behavior'), and while it loosely parallels the PASS_TO_PASS parametrization it transcribes no test ids, function names, parametrization strings, or gold/test code. No fix-invented identifiers (the change only edits visit_Tuple, named legitimately). Behavioral translation only.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
