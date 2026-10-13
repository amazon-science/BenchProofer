# P2 adversarial audit — sympy__sympy-22456

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

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
ptext = "foo"
from sympy.codegen.ast import String
s = String(ptext)
rebuilt = s.func(*s.args)
print("args =", repr(s.args))
print("rebuilt =", repr(rebuilt), "eq =", rebuilt == s)
ok = (rebuilt == s)
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2 & 2.2: args empty (atomic, no positional children)
import sys
from sympy.codegen.ast import String
s = String("foo")
print("args =", repr(s.args))
sys.exit(0 if s.args == () else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.3 & 1.4: func() with no positional args yields equal object, preserving text
import sys
from sympy.codegen.ast import String
s = String("foo")
rebuilt = s.func()
print("rebuilt =", repr(rebuilt), "eq =", rebuilt == s, "text =", rebuilt.text)
sys.exit(0 if (rebuilt == s and rebuilt.text == s.text == "foo") else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.1: is_Atom true
import sys
from sympy.codegen.ast import String
s = String("foo")
print("is_Atom =", s.is_Atom)
sys.exit(0 if s.is_Atom is True else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3: keyword reconstruction preserved & kwargs empty
import sys
from sympy.codegen.ast import String
s = String("foo")
kw = s.kwargs()
rebuilt = s.func(**kw)
print("kwargs =", repr(kw), "rebuilt =", repr(rebuilt), "eq =", rebuilt == s)
sys.exit(0 if (kw == {} and rebuilt == s) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 4: text access, equality, subclass inequality, str, repr
import sys
from sympy.codegen.ast import String, QuotedString
s = String("foo")
s2 = String("foo")
q = QuotedString("foo")
checks = {
    "text": s.text == "foo",
    "eq_equal_text": s == s2,
    "subclass_neq": (q != s),
    "subclass_text": q.text == "foo" == s.text,
    "str": str(s) == "foo",
    "repr": repr(s) == "String('foo')",
}
print(checks)
sys.exit(0 if all(checks.values()) else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 5: other AST classes keep func(*args)==self, incl. node embedding String
import sys
from sympy.codegen.ast import (Assignment, Variable, Declaration, CodeBlock,
                               Type, Pointer, aug_assign, String, Comment)
from sympy import Symbol, Integer
x, y = Symbol('x'), Symbol('y')
objs = []
objs.append(Assignment(x, y))
objs.append(aug_assign(x, '+', y))
objs.append(Type('int'))
objs.append(Variable(x, type=Type('integer')))
objs.append(Pointer(x))
objs.append(Declaration(Variable(x, type=Type('integer'))))
objs.append(CodeBlock(Assignment(x, y), Assignment(y, x)))
objs.append(Comment("hello"))  # embeds a String
bad = []
for o in objs:
    r = o.func(*o.args)
    if r != o:
        bad.append((type(o).__name__, repr(o), repr(r)))
print("checked", len(objs), "bad:", bad)
# Comment embedding a String must still construct/compare/render correctly
c = Comment("hi")
print("comment str/repr:", str(c), "|", repr(c))
sys.exit(0 if not bad else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
ptext = "foo"
from sympy.codegen.ast import String
s = String(ptext)
rebuilt = s.func(*s.args)
print("args =", repr(s.args))
print("rebuilt =", repr(rebuilt), "eq =", rebuilt == s)
ok = (rebuilt == s)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle sympy__sympy-22456: String must satisfy positional argument invariance obj.func(*obj.args)==obj (Req1), be atomic (Req2), preserve kwargs reconstruction (Req3), preserve text/eq/subclass-neq/str/repr (Req4), and not regress other AST nodes (Req5).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2): func(*args)==self and args==(). Positive control.
- probe_2 (Req1.2/2.2): args==() empty.
- probe_3 (Req1.3/1.4): func() with no positional args yields equal object preserving text.
- probe_4 (Req2.1): is_Atom is True.
- probe_5 (Req3.1/3.2): kwargs()=={} and func(**kwargs())==self.
- probe_6 (Req4.1-4.5): text access, equality, QuotedString subclass != base, str=='foo', repr==String('foo').
- probe_7 (Req5.1/5.3): func(*args)==self for Assignment, aug_assign, Type, Variable, Pointer, Declaration, CodeBlock, and Comment (which embeds a String); Comment still renders correctly.

Positive control: probe_1 FAILS at base with TypeError: No value for 'text' given and attribute has no default (obj.func(*obj.args) crashes because text is not in args and had no default). Reproduced at base (prepatch_reproduced=true).

Candidate wrong-fix (weak.diff): adds defaults={'text':''} to String so func(*args) stops crashing but reconstructs an empty String. The suite REJECTS it: probe_1 (rebuilt String() != String('foo')), probe_3 (text=='' not 'foo'), probe_5 (kwargs()=={'text':'foo'} not empty — violates Req3.2), and probe_7 (Comment('hello') rebuilds to Comment() — Req5.3 regression). This demonstrates the suite discriminates the lazy/partial fix that a weak reading of the requirements would permit.

All 5+ probes hold on patched; positive control discriminates base vs patched; >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

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
ptext = "foo"
from sympy.codegen.ast import String
s = String(ptext)
rebuilt = s.func(*s.args)
print("args =", repr(s.args))
print("rebuilt =", repr(rebuilt), "eq =", rebuilt == s)
ok = (rebuilt == s)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle sympy__sympy-22456: String must satisfy positional argument invariance obj.func(*obj.args)==obj (Req1), be atomic (Req2), preserve kwargs reconstruction (Req3), preserve text/eq/subclass-neq/str/repr (Req4), and not regress other AST nodes (Req5).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2): func(*args)==self and args==(). Positive control.
- probe_2 (Req1.2/2.2): args==() empty.
- probe_3 (Req1.3/1.4): func() with no positional args yields equal object preserving text.
- probe_4 (Req2.1): is_Atom is True.
- probe_5 (Req3.1/3.2): kwargs()=={} and func(**kwargs())==self.
- probe_6 (Req4.1-4.5): text access, equality, QuotedString subclass != base, str=='foo', repr==String('foo').
- probe_7 (Req5.1/5.3): func(*args)==self for Assignment, aug_assign, Type, Variable, Pointer, Declaration, CodeBlock, and Comment (which embeds a String); Comment still renders correctly.

Positive control: probe_1 FAILS at base with TypeError: No value for 'text' given and attribute has no default (obj.func(*obj.args) crashes because text is not in args and had no default). Reproduced at base (prepatch_reproduced=true).

Candidate wrong-fix (weak.diff): adds defaults={'text':''} to String so func(*args) stops crashing but reconstructs an empty String. The suite REJECTS it: probe_1 (rebuilt String() != String('foo')), probe_3 (text=='' not 'foo'), probe_5 (kwargs()=={'text':'foo'} not empty — violates Req3.2), and probe_7 (Comment('hello') rebuilds to Comment() — Req5.3 regression). This demonstrates the suite discriminates the lazy/partial fix that a weak reading of the requirements would permit.

All 5+ probes hold on patched; positive control discriminates base vs patched; >=1 candidate exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Base commit VIOLATES the pinned behavior: s.func(*s.args) raises TypeError('No value for text given') at base, and passes on patched tree — confirming the requirements model the actual observable change, not a helper detail. Issue asks precisely for func(*args)==expr invariance for String. Requirements are grounded and correct.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe observable public behavior of the `String` class in `sympy/codegen/ast.py`. The central acceptance criterion (`obj.func(*obj.args)` equals `obj`) is verbatim the PUBLIC problem_statement, which explicitly states both `expr.func(*expr.args) == expr` and `expr.func(**expr.kwargs()) == expr`. 

The hidden test simply appends one line `assert st.func(*st.args) == st` to the pre-existing `test_String`; FAIL_TO_PASS is only `test_String`. Nothing in requirements.md quotes the test, names the test function/file/path, cites ids, or reproduces the gold patch lines. 

Secondary criteria (is_Atom true, empty args, empty kwargs, `.text` access, equality, subclass inequality, `repr` -> `String('foo')`, `_sympystr` producing bare text) all describe public attributes/behavior readable directly from ast.py; the identifiers (is_Atom, args, kwargs, func, Atom) are existing public sympy API, not fix-invented. The repr example uses `foo`, not the test's `foobar`, so it's illustrative, not a copied gold/test literal. 

Req 5's enumeration of other AST node classes (assignment, node, type, variable, pointer, declaration, code-block, control-flow, function-related) parallels the PASS_TO_PASS set only insofar as those are the public classes in the module — legitimate localization of the no-regression scope, not test-shaped case enumeration. No semantic leak of hidden-test or gold content beyond the problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
