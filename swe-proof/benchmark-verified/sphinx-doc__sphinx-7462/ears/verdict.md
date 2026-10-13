# P2 adversarial audit — sphinx-doc__sphinx-7462

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
# R1.1/R1.3 (positive control): _parse_annotation("Tuple[()]") renders as Tuple [ ( ) ]
import sys
from sphinx.domains.python import _parse_annotation
try:
    nodes = _parse_annotation("Tuple[()]")
except Exception as e:
    print("CRASH:", type(e).__name__, e); sys.exit(1)
texts = [n.astext() for n in nodes]
print("texts:", texts)
# Expect Tuple, [, (, ), ]
if texts == ["Tuple", "[", "(", ")", "]"]:
    print("OK order matches Tuple[()]"); sys.exit(0)
print("MISMATCH"); sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.1/R1.2: bare empty tuple AST node -> exactly ( then ), no exception, no pop-empty
import sys, ast
import sphinx.domains.python as P
# reach inner unparse via _parse_annotation on "()" which parses to empty Tuple
try:
    nodes = P._parse_annotation("()")
except Exception as e:
    print("CRASH:", type(e).__name__, e); sys.exit(1)
texts = [n.astext() for n in nodes]
print("texts for '()':", texts)
if texts == ["(", ")"]:
    print("OK empty tuple -> ( )"); sys.exit(0)
print("MISMATCH"); sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R2.1/R2.2: pycode ast.unparse of empty tuple node returns literal "()"
import sys, ast
from sphinx.pycode.ast import unparse, parse
mod = parse("()")
node = mod.body[0].value
assert isinstance(node, ast.Tuple), type(node)
s = unparse(node)
print("unparse(()):", repr(s))
if s == "()":
    print("OK"); sys.exit(0)
print("MISMATCH (empty string or other)"); sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R3.2/R3.3: pycode unparse keeps non-empty tuple as "int, int"; subscript Tuple[int, int]
import sys, ast
from sphinx.pycode.ast import unparse, parse
def u(src):
    return unparse(parse(src).body[0].value)
a = u("(1, 2, 3)")
b = u("Tuple[int, int]")
print("tuple:", repr(a), "subscript:", repr(b))
ok = (a == "1, 2, 3") and (b == "Tuple[int, int]")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3.1/R3.4: display unparse non-empty tuple: elements separated by ", ", no trailing sep
import sys
from sphinx.domains.python import _parse_annotation
nodes = _parse_annotation("Tuple[int, int]")
texts = [n.astext() for n in nodes]
print("Tuple[int,int] ->", texts)
# Expect: Tuple, [, int, ", ", int, ]
if texts == ["Tuple", "[", "int", ", ", "int", "]"]:
    print("OK"); sys.exit(0)
print("MISMATCH"); sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R3.3 regression: variety of other forms render unchanged via pycode unparse
import sys
from sphinx.pycode.ast import unparse, parse
def u(src): return unparse(parse(src).body[0].value)
cases = {
    "a.b.c": "a.b.c",
    "[1, 2, 3]": "[1, 2, 3]",
    "{1, 2, 3}": "{1, 2, 3}",
    "'str'": "'str'",
    "...": "...",
    "object()": "object()",
    "- 1": "- 1",
}
ok = True
for src, exp in cases.items():
    got = u(src)
    print(f"{src!r} -> {got!r} (exp {exp!r})")
    if got != exp: ok = False
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1/R1.3 (positive control): _parse_annotation("Tuple[()]") renders as Tuple [ ( ) ]
import sys
from sphinx.domains.python import _parse_annotation
try:
    nodes = _parse_annotation("Tuple[()]")
except Exception as e:
    print("CRASH:", type(e).__name__, e); sys.exit(1)
texts = [n.astext() for n in nodes]
print("texts:", texts)
# Expect Tuple, [, (, ), ]
if texts == ["Tuple", "[", "(", ")", "]"]:
    print("OK order matches Tuple[()]"); sys.exit(0)
print("MISMATCH"); sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes vs requirements:
- probe_1 (R1.1/R1.3, POSITIVE CONTROL): _parse_annotation('Tuple[()]') -> node texts ['Tuple','[','(',')',']']. Patched: HOLDS. Base: FAILS with IndexError: pop from empty list (prepatch reproduced). weak_partial: HOLDS.
- probe_2 (R1.1/R1.2): bare empty tuple '()' via _parse_annotation -> ['(',')'], no exception. Patched HOLDS; base crashes IndexError.
- probe_3 (R2.1/R2.2): sphinx.pycode.ast.unparse(empty Tuple node) == '()'. Patched HOLDS; base returns '' (VIOLATED); weak_partial (display-only fix) also VIOLATED -> demonstrates suite discriminates.
- probe_4 (R3.2/R3.3 regression): pycode unparse '(1,2,3)'->'1, 2, 3', 'Tuple[int,int]' subscript preserved. HOLDS.
- probe_5 (R3.1/R3.4 regression): display unparse 'Tuple[int, int]' -> ['Tuple','[','int',', ','int',']'] (', ' separator, no trailing sep). HOLDS.
- probe_6 (R3.3 regression): dotted name, list, set, str, ellipsis, call, unary-op all unchanged. HOLDS.

All 6 probes hold on gold-patched tree. Positive control discriminates (fails at base). CANDIDATE PATCH weak_partial.diff (gold's domains/python.py hunk only, omitting the pycode/ast.py hunk — the lazy partial fix a weak reading of R2 permits) is REJECTED by probe_3, proving the suite catches wrong/partial implementations. Requirements faithfully and completely capture the gold fix; not too strong, not too weak.

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
# R1.1/R1.3 (positive control): _parse_annotation("Tuple[()]") renders as Tuple [ ( ) ]
import sys
from sphinx.domains.python import _parse_annotation
try:
    nodes = _parse_annotation("Tuple[()]")
except Exception as e:
    print("CRASH:", type(e).__name__, e); sys.exit(1)
texts = [n.astext() for n in nodes]
print("texts:", texts)
# Expect Tuple, [, (, ), ]
if texts == ["Tuple", "[", "(", ")", "]"]:
    print("OK order matches Tuple[()]"); sys.exit(0)
print("MISMATCH"); sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes vs requirements:
- probe_1 (R1.1/R1.3, POSITIVE CONTROL): _parse_annotation('Tuple[()]') -> node texts ['Tuple','[','(',')',']']. Patched: HOLDS. Base: FAILS with IndexError: pop from empty list (prepatch reproduced). weak_partial: HOLDS.
- probe_2 (R1.1/R1.2): bare empty tuple '()' via _parse_annotation -> ['(',')'], no exception. Patched HOLDS; base crashes IndexError.
- probe_3 (R2.1/R2.2): sphinx.pycode.ast.unparse(empty Tuple node) == '()'. Patched HOLDS; base returns '' (VIOLATED); weak_partial (display-only fix) also VIOLATED -> demonstrates suite discriminates.
- probe_4 (R3.2/R3.3 regression): pycode unparse '(1,2,3)'->'1, 2, 3', 'Tuple[int,int]' subscript preserved. HOLDS.
- probe_5 (R3.1/R3.4 regression): display unparse 'Tuple[int, int]' -> ['Tuple','[','int',', ','int',']'] (', ' separator, no trailing sep). HOLDS.
- probe_6 (R3.3 regression): dotted name, list, set, str, ellipsis, call, unary-op all unchanged. HOLDS.

All 6 probes hold on gold-patched tree. Positive control discriminates (fails at base). CANDIDATE PATCH weak_partial.diff (gold's domains/python.py hunk only, omitting the pycode/ast.py hunk — the lazy partial fix a weak reading of R2 permits) is REJECTED by probe_3, proving the suite catches wrong/partial implementations. Requirements faithfully and completely capture the gold fix; not too strong, not too weak.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds an else-branch to the ast.Tuple handling in both sphinx/domains/python.py (inner unparse, empty → '(' ')' punctuation nodes instead of result.pop() on empty list) and sphinx/pycode/ast.py (empty → '()' string). Requirements 1-3 correctly and biconditionally model both changed branches plus the unchanged non-empty path. Probe on patched tree confirmed all claims; exit 0.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the empty-tuple fix in behavioral terms and legitimately localize it to the two changed modules/functions (sphinx/domains/python.py::_parse_annotation inner unparse, sphinx/pycode/ast.py::unparse) — all already public via the problem_statement (which names python.py, unparse, result.pop, the IndexError, Tuple[()], and the expected 'build succeeds' outcome).

Examined potential semantic leaks:
- Req 1.3 enumerates the node sequence for Tuple[()] (Tuple ref, '[', '(', ')', ']'). This mirrors the hidden test_parse_annotation assertion, but it is the directly-implied correct behavior (Tuple[()] must render as the characters 'Tuple[()]'), stated in prose — it does NOT reproduce the test's node-type identifiers (pending_xref/desc_sig_punctuation/assert_node) or test name/path. Behavioral translation, not test transmission.
- Req 2.1/2.2 ('()' literal, not empty string) matches the hidden parametrized case ('()','()') but is the obvious source-text behavior for an empty tuple; no id or quoted test line appears.
- Req 3.3 lists supported AST forms (names, subscripts, lists, sets, dicts, literals, ellipsis, None, ops, lambda, calls). This overlaps test_pycode_ast parametrization ids, but these are exactly the branches in the existing sphinx/pycode/ast.py::unparse source that any spec author must read to localize a regression guard — derivable from the code, not uniquely from the test enumeration. The 'int, int' example (Req 3.2) is illustrative, not a verbatim gold/test line.
- No fix-invented identifiers exist (gold patch only adds an if node.elts/else branch — no new names).

No test names, file paths, parametrization ids, quoted test/gold code, or test-shaped case enumerations beyond what the problem_statement and the source modules already expose.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
