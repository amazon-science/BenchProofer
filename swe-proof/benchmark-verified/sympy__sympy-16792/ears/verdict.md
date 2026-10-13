# P2 adversarial audit — sympy__sympy-16792

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# R1.1 + R1.3 (POSITIVE CONTROL): MatrixSymbol absent from expr -> array metadata & `double *x`
import sys
from sympy import MatrixSymbol
from sympy.utilities.codegen import CodeGen, codegen

x = MatrixSymbol('x', 2, 1)
cg = CodeGen()
r = cg.routine('test', 1.0, argument_sequence=(x,))
args = [a for a in r.arguments if str(a.name) == 'x']
assert len(args) == 1, "x must be in input args"
dims = getattr(args[0], 'dimensions', None)
sys.stderr.write("dimensions=%r\n" % (dims,))

# C signature must declare pointer
[(cn, cc)] = codegen(('test', 1.0), 'C', 'test', header=False, empty=False,
                     argument_sequence=(x,))[:1]
sys.stderr.write("C source:\n%s\n" % cc)
ok_meta = bool(dims)  # non-empty dimensions == array metadata
ok_ptr = 'double *x' in cc
sys.stderr.write("ok_meta=%s ok_ptr=%s\n" % (ok_meta, ok_ptr))
sys.exit(0 if (ok_meta and ok_ptr) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.2: shape sizes d_1..d_k -> per-axis inclusive range (0, d_i - 1)
import sys
from sympy import MatrixSymbol
from sympy.utilities.codegen import CodeGen

x = MatrixSymbol('x', 3, 4)  # shape (3,4)
cg = CodeGen()
r = cg.routine('test', 1.0, argument_sequence=(x,))
arg = [a for a in r.arguments if str(a.name) == 'x'][0]
dims = list(getattr(arg, 'dimensions', []) or [])
sys.stderr.write("dimensions=%r\n" % (dims,))
expected = [(0, 2), (0, 3)]
got = [(int(lo), int(hi)) for (lo, hi) in dims]
sys.stderr.write("got=%r expected=%r\n" % (got, expected))
sys.exit(0 if got == expected else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R1.4 + R2.1 + R2.2: plain scalar absent from expr -> no metadata, by-value, order preserved,
# constant still returned.
import sys
from sympy import Symbol, MatrixSymbol
from sympy.utilities.codegen import CodeGen, codegen

s = Symbol('s')          # plain scalar, absent from expr
x = MatrixSymbol('x', 2, 1)  # array, absent from expr
cg = CodeGen()
r = cg.routine('test', 1.0, argument_sequence=(x, s))
names = [str(a.name) for a in r.arguments]
sys.stderr.write("arg order=%r\n" % names)
# ordering preserved (R2.2)
assert names == ['x', 's'], "order must match argument_sequence"
sarg = [a for a in r.arguments if str(a.name) == 's'][0]
sdims = getattr(sarg, 'dimensions', None)
sys.stderr.write("scalar s dims=%r\n" % (sdims,))
# scalar must carry NO index-bound metadata (R1.4)
assert not sdims, "scalar must have no dimensions"

[(cn, cc)] = codegen(('test', 1.0), 'C', 'test', header=False, empty=False,
                     argument_sequence=(x, s))[:1]
sys.stderr.write("C source:\n%s\n" % cc)
assert 'double *x' in cc, "x should be pointer"
assert 'double s' in cc and 'double *s' not in cc, "s should be by-value scalar"
assert 'test_result = 1.0' in cc, "constant result must be returned (R2.1)"
# scalar appears before... check order in signature via the arg-list only
sig = [l for l in cc.splitlines() if l.startswith('double test(')][0]
sys.stderr.write("sig=%r\n" % sig)
arglist = sig[sig.index('(')+1: sig.rindex(')')]
assert arglist.index('*x') < arglist.index(' s'), "x before s in signature"
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2.3: unused array arg SHALL NOT alter body/result compared to when it is absent.
import sys
from sympy import MatrixSymbol, Symbol
from sympy.utilities.codegen import codegen

a = Symbol('a')
expr = 2*a + 1  # depends only on a
x = MatrixSymbol('x', 2, 1)

# without the padding arg
[(_, base)] = codegen(('test', expr), 'C', 'test', header=False, empty=False,
                      argument_sequence=(a,))[:1]
# with the padding arg
[(_, padded)] = codegen(('test', expr), 'C', 'test', header=False, empty=False,
                        argument_sequence=(a, x))[:1]
sys.stderr.write("base:\n%s\npadded:\n%s\n" % (base, padded))

def body(src):
    lines = src.splitlines()
    # keep the result-computation lines (not the signature)
    return [l for l in lines if 'test_result' in l]

bb, pb = body(base), body(padded)
sys.stderr.write("base body=%r\npadded body=%r\n" % (bb, pb))
assert bb == pb, "body/result must be identical whether or not x is present"
# padded must include x as pointer
assert 'double *x' in padded
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3.1 + R3.2 + R3.6: regression - array arg present -> pointer w/ metadata;
# scalar present -> by-value; mixed with an absent MatrixSymbol pad.
import sys
from sympy import MatrixSymbol, Symbol
from sympy.utilities.codegen import CodeGen, codegen

a = Symbol('a')
M = MatrixSymbol('M', 2, 2)   # present in expr
pad = MatrixSymbol('P', 3, 1) # absent MatrixSymbol pad
expr = M[0, 0] + a
cg = CodeGen()
r = cg.routine('test', expr, argument_sequence=(M, a, pad))
byname = {str(x.name): x for x in r.arguments}
sys.stderr.write("args=%r\n" % {k: getattr(v,'dimensions',None) for k,v in byname.items()})
# M present array -> has dims (R3.1)
assert byname['M'].dimensions, "present array M must have dims"
# a present scalar -> no dims (R3.2)
assert not byname['a'].dimensions, "present scalar a must have no dims"
# pad absent MatrixSymbol -> dims (R3.6 / R1.1)
assert byname['P'].dimensions, "absent MatrixSymbol pad must have dims"

[(_, cc)] = codegen(('test', expr), 'C', 'test', header=False, empty=False,
                    argument_sequence=(M, a, pad))[:1]
sys.stderr.write("C:\n%s\n" % cc)
assert 'double *M' in cc
assert 'double a' in cc and 'double *a' not in cc
assert 'double *P' in cc
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R3.4: argument_sequence requesting an argument not part of routine -> raise CodeGenArgumentListError
import sys
from sympy import Symbol
from sympy.utilities.codegen import CodeGen, CodeGenArgumentListError

a = Symbol('a')
b = Symbol('b')  # not in expr at all -> but with argument_sequence padding is allowed for absent...
# Requirement 3.4 concerns an argument that is NOT part of the routine: i.e. a
# symbol in the expr that is missing from the sequence. Build expr with a and b,
# but only request a -> b is missing -> error.
cg = CodeGen()
expr = a + b
try:
    cg.routine('test', expr, argument_sequence=(a,))
    sys.stderr.write("NO ERROR RAISED\n")
    sys.exit(1)
except CodeGenArgumentListError as e:
    sys.stderr.write("raised CodeGenArgumentListError: %s missing=%r\n" % (e, getattr(e,'missing_args',None)))
    sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# R3.3: no explicit argument_sequence -> metadata/order derived from expr symbols;
# array symbols carry dims, scalars none. (regression)
import sys
from sympy import MatrixSymbol, Symbol, IndexedBase, Idx
from sympy.utilities.codegen import CodeGen

a = Symbol('a')
n = Symbol('n', integer=True)
A = IndexedBase('A')
i = Idx('i', n)
# expr referencing indexed array A[i] and scalar a
expr = A[i] * a
cg = CodeGen()
r = cg.routine('test', expr, argument_sequence=None)
byname = {str(x.name): x for x in r.arguments}
sys.stderr.write("args=%r\n" % {k: getattr(v,'dimensions',None) for k,v in byname.items()})
assert 'A' in byname and byname['A'].dimensions, "indexed array A must carry dims"
assert 'a' in byname and not byname['a'].dimensions, "scalar a must carry none"
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1 + R1.3 (POSITIVE CONTROL): MatrixSymbol absent from expr -> array metadata & `double *x`
import sys
from sympy import MatrixSymbol
from sympy.utilities.codegen import CodeGen, codegen

x = MatrixSymbol('x', 2, 1)
cg = CodeGen()
r = cg.routine('test', 1.0, argument_sequence=(x,))
args = [a for a in r.arguments if str(a.name) == 'x']
assert len(args) == 1, "x must be in input args"
dims = getattr(args[0], 'dimensions', None)
sys.stderr.write("dimensions=%r\n" % (dims,))

# C signature must declare pointer
[(cn, cc)] = codegen(('test', 1.0), 'C', 'test', header=False, empty=False,
                     argument_sequence=(x,))[:1]
sys.stderr.write("C source:\n%s\n" % cc)
ok_meta = bool(dims)  # non-empty dimensions == array metadata
ok_ptr = 'double *x' in cc
sys.stderr.write("ok_meta=%s ok_ptr=%s\n" % (ok_meta, ok_ptr))
sys.exit(0 if (ok_meta and ok_ptr) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering all normative acceptance criteria; all HOLD on the gold-patched tree.

Probes (criterion -> result base | patched):
- probe_1 (R1.1+R1.3, POSITIVE CONTROL): MatrixSymbol('x',2,1) absent from expr=1.0 with argument_sequence=(x,) -> arg carries dimensions metadata AND C signature is `double *x`. VIOLATED@base | HOLDS@patched (discriminates).
- probe_2 (R1.2): MatrixSymbol shape (3,4) -> per-axis inclusive ranges exactly [(0,2),(0,3)] (0..size-1). HOLDS@patched.
- probe_3 (R1.4+R2.1+R2.2): plain Symbol s absent from expr, sequence (x,s) -> s has NO dims and emits by-value `double s`, x is `double *x`, constant 1.0 still returned, order preserved x-before-s. HOLDS@patched.
- probe_4 (R2.3): unused MatrixSymbol pad does not alter body/result vs when absent (result lines identical). HOLDS@patched.
- probe_5 (R3.1+R3.2+R3.6): mixed present-array M (dims/pointer), present-scalar a (no dims/by-value), absent-MatrixSymbol pad P (dims/pointer). HOLDS@patched.
- probe_6 (R3.4): sequence omitting a symbol that IS in the expr -> CodeGenArgumentListError raised. HOLDS@patched.
- probe_7 (R3.3): no argument_sequence -> IndexedBase A[i] carries dims, scalar a carries none. HOLDS@patched.

Candidate wrong patches (both apply at base_commit; probe suite REJECTS both):
- weak_A: emits a single dummy dimension [(0,0)] for any shaped absent arg (pointer emission is correct, so probe_1 HOLDS) but WRONG shape -> probe_2 REJECTS (dims != [(0,2),(0,3)]).
- weak_B: MatrixSymbol-only guard with 1-based inclusive range [(1,d)] -> probe_2 REJECTS (dims != 0..size-1). Confirms the suite pins R1.2's exact 0-based convention, not merely 'is a pointer'.

Note on the prior recorded G-EQ/G-PANEL VIOLATION (probe_3.py in run bcptlsm1): it used an IndexedBase argument absent from the expression and asserted pointer emission. The gold patch DOES emit that IndexedBase case as a scalar (`double A`) because argument_sequence normalizes IndexedBase->label (plain Symbol) before the new guard, so isinstance(symbol,(IndexedBase,MatrixSymbol)) never matches. However, NONE of the acceptance criteria mandate IndexedBase-absent-from-expr behavior: R1.1, R1.3 and R3.6 all say specifically 'a MatrixSymbol argument'; the IndexedBase mention appears only in the non-normative Introduction ('a MatrixSymbol, or an IndexedBase/its label') describing general array metadata, not as a SHALL. The single hidden test (test_ccode_unused_array_arg) exercises only MatrixSymbol. Thus the IndexedBase probe encodes a behavior the requirements do NOT mandate; it is an over-reach beyond the acceptance criteria, not a genuine spec-too-weak/violation finding. Every behavior actually mandated by the numbered acceptance criteria holds on the gold-patched tree, and the suite rejects plausibly-wrong alternatives.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# R1.1 + R1.3 (POSITIVE CONTROL): MatrixSymbol absent from expr -> array metadata & `double *x`
import sys
from sympy import MatrixSymbol
from sympy.utilities.codegen import CodeGen, codegen

x = MatrixSymbol('x', 2, 1)
cg = CodeGen()
r = cg.routine('test', 1.0, argument_sequence=(x,))
args = [a for a in r.arguments if str(a.name) == 'x']
assert len(args) == 1, "x must be in input args"
dims = getattr(args[0], 'dimensions', None)
sys.stderr.write("dimensions=%r\n" % (dims,))

# C signature must declare pointer
[(cn, cc)] = codegen(('test', 1.0), 'C', 'test', header=False, empty=False,
                     argument_sequence=(x,))[:1]
sys.stderr.write("C source:\n%s\n" % cc)
ok_meta = bool(dims)  # non-empty dimensions == array metadata
ok_ptr = 'double *x' in cc
sys.stderr.write("ok_meta=%s ok_ptr=%s\n" % (ok_meta, ok_ptr))
sys.exit(0 if (ok_meta and ok_ptr) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering all normative acceptance criteria; all HOLD on the gold-patched tree.

Probes (criterion -> result base | patched):
- probe_1 (R1.1+R1.3, POSITIVE CONTROL): MatrixSymbol('x',2,1) absent from expr=1.0 with argument_sequence=(x,) -> arg carries dimensions metadata AND C signature is `double *x`. VIOLATED@base | HOLDS@patched (discriminates).
- probe_2 (R1.2): MatrixSymbol shape (3,4) -> per-axis inclusive ranges exactly [(0,2),(0,3)] (0..size-1). HOLDS@patched.
- probe_3 (R1.4+R2.1+R2.2): plain Symbol s absent from expr, sequence (x,s) -> s has NO dims and emits by-value `double s`, x is `double *x`, constant 1.0 still returned, order preserved x-before-s. HOLDS@patched.
- probe_4 (R2.3): unused MatrixSymbol pad does not alter body/result vs when absent (result lines identical). HOLDS@patched.
- probe_5 (R3.1+R3.2+R3.6): mixed present-array M (dims/pointer), present-scalar a (no dims/by-value), absent-MatrixSymbol pad P (dims/pointer). HOLDS@patched.
- probe_6 (R3.4): sequence omitting a symbol that IS in the expr -> CodeGenArgumentListError raised. HOLDS@patched.
- probe_7 (R3.3): no argument_sequence -> IndexedBase A[i] carries dims, scalar a carries none. HOLDS@patched.

Candidate wrong patches (both apply at base_commit; probe suite REJECTS both):
- weak_A: emits a single dummy dimension [(0,0)] for any shaped absent arg (pointer emission is correct, so probe_1 HOLDS) but WRONG shape -> probe_2 REJECTS (dims != [(0,2),(0,3)]).
- weak_B: MatrixSymbol-only guard with 1-based inclusive range [(1,d)] -> probe_2 REJECTS (dims != 0..size-1). Confirms the suite pins R1.2's exact 0-based convention, not merely 'is a pointer'.

Note on the prior recorded G-EQ/G-PANEL VIOLATION (probe_3.py in run bcptlsm1): it used an IndexedBase argument absent from the expression and asserted pointer emission. The gold patch DOES emit that IndexedBase case as a scalar (`double A`) because argument_sequence normalizes IndexedBase->label (plain Symbol) before the new guard, so isinstance(symbol,(IndexedBase,MatrixSymbol)) never matches. However, NONE of the acceptance criteria mandate IndexedBase-absent-from-expr behavior: R1.1, R1.3 and R3.6 all say specifically 'a MatrixSymbol argument'; the IndexedBase mention appears only in the non-normative Introduction ('a MatrixSymbol, or an IndexedBase/its label') describing general array metadata, not as a SHALL. The single hidden test (test_ccode_unused_array_arg) exercises only MatrixSymbol. Thus the IndexedBase probe encodes a behavior the requirements do NOT mandate; it is an over-reach beyond the acceptance criteria, not a genuine spec-too-weak/violation finding. Every behavior actually mandated by the numbered acceptance criteria holds on the gold-patched tree, and the suite rejects plausibly-wrong alternatives.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on gold-patched instance image via nl_attack. Requirements correctly pin the MatrixSymbol-absent→pointer boundary that the issue and hidden test exercise, and correctly leave scalar-absent→by-value unchanged. The IndexedBase-scalar observation cited by the earlier G-PANEL-2/G-EQ fail is genuine code behavior but the requirements do NOT mandate the opposite for IndexedBase — R1.1/R1.3/R3.6 are MatrixSymbol-only. Modeling absent-IndexedBase→array would OVERCLAIM relative to the patched code; the spec avoids that. No requirement forbids behavior the code has, mandates behavior it lacks, mis-pins the boundary, or invents behavior. FAITHFUL.

Counterexample / evidence:

```
MatrixSymbol('x',2,1), expr=1.0, argument_sequence=(x,) → `double f(double *x)`, arg dimensions=[(0,1),(0,0)] (matches R1.1/R1.2/R1.3). Symbol('y') absent → `double g(double y)` (R1.4). Mixed (a,x) → `double mix(double a, double *x)` order preserved (R2.2). occurring MatrixSymbol → `double *x` (R3.1); occurring scalar → `double a` (R3.3); unknown requested arg → CodeGenArgumentListError (R3.4). All confirmed on patched tree.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md translates the public problem_statement into behavioral EARS requirements. Everything present is public-derivable: the incorrect `double x` vs correct `double *x` C signature, MatrixSymbol array arg absent from expression, constant expression (1.0), argument_sequence, cython/C codegen — all appear in the problem_statement. Identifiers named (codegen, CodeGen.routine, CCodeGen, MatrixSymbol, IndexedBase, InputArgument, argument_sequence) are legitimate localization of the change site; InputArgument is the real class, not a fix-invented identifier. The (0, dim-1) per-axis index-bound convention (Req 1.2) mirrors the gold's `dimensions(s)` helper but is stated as a general behavioral rule, not as quoted code. No hidden-test artifacts leak: the test function name test_ccode_unused_array_arg, the test file path (sympy/utilities/tests/test_codegen.py), the `test`/`test_result` symbol names, and the exact expected C string do NOT appear. Only one hidden test exists, so there is no parametrization to mirror; the requirement enumerations (scalar vs array, in-expr vs absent) reflect the behavioral matrix, not test cases.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
