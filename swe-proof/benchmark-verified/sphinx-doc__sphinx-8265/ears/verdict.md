# P2 adversarial audit — sphinx-doc__sphinx-8265

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
Naive fix (parenthesize visit_Tuple only, WITHOUT the is_simple_tuple guard in visit_Subscript) renders Tuple[int, int] as 'Tuple[(int, int)]' — REJECTED by probe_5 (R2.1/R2.2).
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control + R1.1/R1.4: a multi-element tuple renders parenthesized with ", " join.
import ast
import sphinx.pycode.ast as m

node = ast.parse("(1, 2, 3)", mode="eval").body
out = m.unparse(node)
print("(1, 2, 3) ->", repr(out))
ok = out == "(1, 2, 3)"
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.2: single-element tuple must still be enclosed in parentheses.
import ast
import sphinx.pycode.ast as m

node = ast.parse("(1,)", mode="eval").body
out = m.unparse(node)
print("(1,) ->", repr(out))
# R1.2 mandates the single element enclosed in parentheses.
ok = isinstance(out, str) and out.startswith("(") and out.endswith(")") and "1" in out
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R1.3: empty tuple renders as "()".
import ast
import sphinx.pycode.ast as m

node = ast.parse("()", mode="eval").body
out = m.unparse(node)
print("() ->", repr(out))
ok = out == "()"
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R1.5: a tuple default in a rendered function signature shows enclosing parens.
import ast
import sphinx.pycode.ast as m

src = "def add_lines(self, lines, color=(1, 1, 1), width=5, label=None, name=None): pass"
tree = ast.parse(src)
func = tree.body[0]
rendered = m.unparse(func.args)
print("signature ->", repr(rendered))
ok = "color=(1, 1, 1)" in rendered
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R2.1/R2.2: comma-separated subscription index stays unparenthesized.
import ast
import sphinx.pycode.ast as m

out = m.unparse(ast.parse("Tuple[int, int]", mode="eval").body)
print("Tuple[int, int] ->", repr(out))
ok = out == "Tuple[int, int]"
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R2.3: single-value subscript index renders ordinarily (a[b] -> a[b]).
import ast
import sphinx.pycode.ast as m

out = m.unparse(ast.parse("a[b]", mode="eval").body)
print("a[b] ->", repr(out))
ok = out == "a[b]"
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# R3.2/R3.3/R3.4/R3.5: other expression forms render unchanged.
import ast
import sphinx.pycode.ast as m

def u(s):
    return m.unparse(ast.parse(s, mode="eval").body)

cases = {
    "os.path": "os.path",          # attribute
    "sys": "sys",                  # name
    "1234": "1234",                # num literal
    "'str'": "'str'",              # str literal
    "b'bytes'": "b'bytes'",        # bytes literal
    "...": "...",                  # ellipsis
    "object()": "object()",        # call
    "[1, 2, 3]": "[1, 2, 3]",      # list display
    "{1, 2, 3}": "{1, 2, 3}",      # set display
    "{'a': 1}": "{'a': 1}",        # dict display
    "lambda x: 1": "lambda x: ...",# lambda
    "- 1": "- 1",                  # unary (base uses "%s %s")
    "+ a": "+ a",                  # unary
    "~ a": "~ a",                  # unary
    "not a": "not a",              # unary not
}
ok = True
for s, exp in cases.items():
    got = u(s)
    print(repr(s), "->", repr(got), "expected", repr(exp))
    if got != exp:
        ok = False
        print("  MISMATCH")

# R3.5: null input -> null result
n = m.unparse(None)
print("None ->", repr(n))
if n is not None:
    ok = False

print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control + R1.1/R1.4: a multi-element tuple renders parenthesized with ", " join.
import ast
import sphinx.pycode.ast as m

node = ast.parse("(1, 2, 3)", mode="eval").body
out = m.unparse(node)
print("(1, 2, 3) ->", repr(out))
ok = out == "(1, 2, 3)"
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8265: _UnparseVisitor tuple rendering. Base_commit tree is the CLASS-based visitor (visit_Tuple returns comma-join without parens; visit_Subscript un-guarded); NOT (an older function-based unparse). Diffs must target the class-based visitor at L174-178.

Probes (all HOLD on gold-patched tree, py3.9.20):
- probe_1 (R1.1/R1.4, POSITIVE CONTROL): (1,2,3) -> '(1, 2, 3)'. Patched: HOLDS. Base: VIOLATED ('1, 2, 3'). Discriminates.
- probe_2 (R1.2): single-element tuple enclosed in parens. Gold emits '(1)' (no trailing comma); probe only requires leading '(' + trailing ')' per the requirement wording, so it holds.
- probe_3 (R1.3): () -> '()'. HOLDS.
- probe_4 (R1.5): add_lines signature shows color=(1, 1, 1). Patched HOLDS; base VIOLATED ('color=1, 1, 1'). Second discriminator.
- probe_5 (R2.1/R2.2): Tuple[int, int] -> 'Tuple[int, int]' unparenthesized. HOLDS on gold; REJECTS the naive weak patch ('Tuple[(int, int)]').
- probe_6 (R2.3): a[b] -> 'a[b]'. HOLDS.
- probe_7 (R3.2-3.5): attribute/name/num/str/bytes/ellipsis/call/list/set/dict/lambda/unary(+,-,~,not)/None all render unchanged. HOLDS.

Candidate patch exercised: weak.diff (>=1 required, >=1 rejected floor met) — probes REJECT it via probe_5, demonstrating the suite discriminates the R2 subscription-regression that the gold's is_simple_tuple guard prevents. No requirement-conforming-yet-nonresolving alternative found: the only degree of freedom a weak reading permits is dropping the subscript guard, which the suite catches.

Conclusion: 7 probes hold on patched; positive control discriminates base vs patched (prepatch reproduced); the plausible naive fix is rejected. SOUND.

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
Naive fix (parenthesize visit_Tuple only, WITHOUT the is_simple_tuple guard in visit_Subscript) renders Tuple[int, int] as 'Tuple[(int, int)]' — REJECTED by probe_5 (R2.1/R2.2).
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
# Positive control + R1.1/R1.4: a multi-element tuple renders parenthesized with ", " join.
import ast
import sphinx.pycode.ast as m

node = ast.parse("(1, 2, 3)", mode="eval").body
out = m.unparse(node)
print("(1, 2, 3) ->", repr(out))
ok = out == "(1, 2, 3)"
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8265: _UnparseVisitor tuple rendering. Base_commit tree is the CLASS-based visitor (visit_Tuple returns comma-join without parens; visit_Subscript un-guarded); NOT (an older function-based unparse). Diffs must target the class-based visitor at L174-178.

Probes (all HOLD on gold-patched tree, py3.9.20):
- probe_1 (R1.1/R1.4, POSITIVE CONTROL): (1,2,3) -> '(1, 2, 3)'. Patched: HOLDS. Base: VIOLATED ('1, 2, 3'). Discriminates.
- probe_2 (R1.2): single-element tuple enclosed in parens. Gold emits '(1)' (no trailing comma); probe only requires leading '(' + trailing ')' per the requirement wording, so it holds.
- probe_3 (R1.3): () -> '()'. HOLDS.
- probe_4 (R1.5): add_lines signature shows color=(1, 1, 1). Patched HOLDS; base VIOLATED ('color=1, 1, 1'). Second discriminator.
- probe_5 (R2.1/R2.2): Tuple[int, int] -> 'Tuple[int, int]' unparenthesized. HOLDS on gold; REJECTS the naive weak patch ('Tuple[(int, int)]').
- probe_6 (R2.3): a[b] -> 'a[b]'. HOLDS.
- probe_7 (R3.2-3.5): attribute/name/num/str/bytes/ellipsis/call/list/set/dict/lambda/unary(+,-,~,not)/None all render unchanged. HOLDS.

Candidate patch exercised: weak.diff (>=1 required, >=1 rejected floor met) — probes REJECT it via probe_5, demonstrating the suite discriminates the R2 subscription-regression that the gold's is_simple_tuple guard prevents. No requirement-conforming-yet-nonresolving alternative found: the only degree of freedom a weak reading permits is dropping the subscript guard, which the suite catches.

Conclusion: 7 probes hold on patched; positive control discriminates base vs patched (prepatch reproduced); the plausible naive fix is rejected. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch modifies exactly two methods of _UnparseVisitor: visit_Tuple (wrap non-empty tuple in parens; empty stays '()') and visit_Subscript (render simple-tuple slice — non-empty, non-starred — without parens, handling both direct-slice and ast.Index-wrapped forms across Python versions). The requirements' modeling boundary (Req1 tuple rendering, Req2 subscription-index rendering incl. starred exclusion and version-agnostic Index handling, Req3 all-others-preserved) coincides precisely with the changed observable behavior. Req1.2 correctly demands only parenthesization of the single element, matching the patch's '(1)' output (the visitor drops the trailing comma, which is faithful to the code, not overspecified). No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from (a) the PUBLIC problem_statement — the add_lines(...color=(1,1,1)...) example and the tuple-parenthesization fix — and (b) legitimate localization of the change (naming sphinx/pycode/ast.py, _UnparseVisitor, the unparse helper). The hidden test_patch is a single one-line change to a parametrized case in tests/test_pycode_ast.py ('(1, 2, 3)' -> '(1, 2, 3)'); no test name, path, parametrization id, or verbatim test/gold line is quoted. Requirement 2 (Tuple[int, int] stays unparenthesized) and the Starred/index-node-container distinctions are derived from the gold edit's visit_Subscript logic but are stated as behavioral requirements using generic Python-AST vocabulary — the fix-invented identifier is_simple_tuple never appears. Requirement 3's enumeration of preserved expression forms mirrors the visitor's own visit_* methods (public in the source module) as a regression-preservation clause, not the test parametrization ids. This is faithful translation of tested behavior into requirements, not reconstruction of the hidden tests or gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
