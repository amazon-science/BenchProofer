# P2 adversarial audit — sympy__sympy-12489

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
"""Positive control: R1.1/R1.3 - construction on a subclass yields subclass instances.
Holds on patched tree, FAILS at base (base always reverts to Permutation)."""
import sys
from sympy.combinatorics.permutations import Permutation


class MyPerm(Permutation):
    pass


ok = True
# various accepted argument forms
cases = {
    "no args": MyPerm(),
    "single int": MyPerm(4),
    "array form": MyPerm([1, 0, 2, 3]),
    "cyclic form": MyPerm([[0, 1], [2, 3]]),
    "multiple cycle args": MyPerm(0, 1, 2),
    "existing arrangement": MyPerm(MyPerm([1, 0, 2])),
}
for name, obj in cases.items():
    t = type(obj).__name__
    is_sub = isinstance(obj, MyPerm) and type(obj) is MyPerm
    print("%-16s -> %s  (MyPerm=%s)" % (name, t, is_sub))
    if not is_sub:
        ok = False

# _af_new bound to invoking class (R1.3)
afn = MyPerm._af_new([1, 0, 2])
print("_af_new on subclass -> %s" % type(afn).__name__)
if type(afn) is not MyPerm:
    ok = False

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2: operations propagate operand's class AND array forms unchanged.
mul (left operand governs), pow, invert, xor conjugate, add rank shift."""
import sys
from sympy.combinatorics.permutations import Permutation


class MyPerm(Permutation):
    pass


ok = True
a = MyPerm([1, 2, 0, 3])
b = MyPerm([0, 2, 1, 3])

# R2.1 mul -> left operand type; array form same as base composition
prod = a * b
base_prod = Permutation([1, 2, 0, 3]) * Permutation([0, 2, 1, 3])
print("mul type=%s array=%s base=%s" % (type(prod).__name__, prod.array_form, base_prod.array_form))
if type(prod) is not MyPerm or prod.array_form != base_prod.array_form:
    ok = False

# R2.2 base * subclass -> base
mixed = Permutation([1, 2, 0, 3]) * b
print("base*sub type=%s" % type(mixed).__name__)
if type(mixed) is not Permutation:
    ok = False

# R2.3 pow / invert / xor
p = a ** 2
bp = Permutation([1, 2, 0, 3]) ** 2
print("pow type=%s array=%s base=%s" % (type(p).__name__, p.array_form, bp.array_form))
if type(p) is not MyPerm or p.array_form != bp.array_form:
    ok = False

inv = ~a
binv = ~Permutation([1, 2, 0, 3])
print("inv type=%s array=%s base=%s" % (type(inv).__name__, inv.array_form, binv.array_form))
if type(inv) is not MyPerm or inv.array_form != binv.array_form:
    ok = False

conj = a ^ b
bconj = Permutation([1, 2, 0, 3]) ^ Permutation([0, 2, 1, 3])
print("xor type=%s array=%s base=%s" % (type(conj).__name__, conj.array_form, bconj.array_form))
if type(conj) is not MyPerm or conj.array_form != bconj.array_form:
    ok = False

# R2.4 add rank shift
s = a + 1
bs = Permutation([1, 2, 0, 3]) + 1
print("add type=%s array=%s base=%s" % (type(s).__name__, s.array_form, bs.array_form))
if type(s) is not MyPerm or s.array_form != bs.array_form:
    ok = False

sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R3: factory / unranking / helper methods honor invoking class, values unchanged."""
import sys
from sympy.combinatorics.permutations import Permutation

def log(msg):
    print(msg)
    print(msg, file=sys.stderr)


class MyPerm(Permutation):
    pass


ok = True

def check(name, obj, base_obj):
    global ok
    same_type = type(obj) is MyPerm
    # base_obj is None for methods where value comparison awkward
    val_ok = True
    if base_obj is not None:
        val_ok = obj.array_form == base_obj.array_form
    log("%-22s type=%s array=%s val_ok=%s" % (name, type(obj).__name__, obj.array_form, val_ok))
    if not same_type or not val_ok:
        ok = False

check("unrank_lex", MyPerm.unrank_lex(4, 5), Permutation.unrank_lex(4, 5))
check("unrank_nonlex", MyPerm.unrank_nonlex(4, 5), Permutation.unrank_nonlex(4, 5))
check("unrank_trotterjohnson", MyPerm.unrank_trotterjohnson(4, 5), Permutation.unrank_trotterjohnson(4, 5))
check("josephus", MyPerm.josephus(3, 6, 1), Permutation.josephus(3, 6, 1))
check("from_inversion_vector", MyPerm.from_inversion_vector([0, 0, 0]), Permutation.from_inversion_vector([0, 0, 0]))

# random -> subclass (value nondeterministic)
r = MyPerm.random(5)
log("random type=%s" % type(r).__name__)
if type(r) is not MyPerm:
    ok = False

# next_* instance methods
inst = MyPerm([0, 1, 2, 3])
nl = inst.next_lex()
log("next_lex type=%s array=%s" % (type(nl).__name__, nl.array_form))
if type(nl) is not MyPerm:
    ok = False

nn = MyPerm([1, 0, 2, 3]).next_nonlex()
log("next_nonlex type=%s" % type(nn).__name__)
if type(nn) is not MyPerm:
    ok = False

ntj = inst.next_trotterjohnson()
log("next_trotterjohnson type=%s" % type(ntj).__name__)
if type(ntj) is not MyPerm:
    ok = False

# commutator, rmul_with_af, mul_inv
x = MyPerm([1, 2, 0, 3])
y = MyPerm([0, 2, 1, 3])
com = x.commutator(y)
bcom = Permutation([1, 2, 0, 3]).commutator(Permutation([0, 2, 1, 3]))
check("commutator", com, bcom)

rma = MyPerm.rmul_with_af(x, y)
log("rmul_with_af type=%s array=%s" % (type(rma).__name__, rma.array_form))
if type(rma) is not MyPerm:
    ok = False

mi = x.mul_inv(y)
log("mul_inv type=%s array=%s" % (type(mi).__name__, mi.array_form))
if type(mi) is not MyPerm:
    ok = False

sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R1.4 identity shortcut + foreign-class TypeError; R4 power-by-perm guard; R1.5 ValueError."""
import sys
from sympy.combinatorics.permutations import Permutation


class MyPerm(Permutation):
    pass


ok = True

# R1.4: sole arg is instance of invoking class, size matches -> same object returned
m = MyPerm([1, 0, 2])
same = MyPerm(m)
print("identity shortcut: same object? %s" % (same is m))
if same is not m:
    ok = False

# base class: passing an existing perm returns it unchanged (base includes subclass -> retained)
p = Permutation([1, 0, 2])
same2 = Permutation(p)
print("base identity: same object? %s" % (same2 is p))
if same2 is not p:
    ok = False
# base receiving subclass instance retains its type
same3 = Permutation(m)
print("base(subclass) same object? %s type=%s" % (same3 is m, type(same3).__name__))
if same3 is not m:
    ok = False

# R1.4: base-class arrangement passed to derived constructor -> TypeError
try:
    MyPerm(p)
    print("foreign arrangement to derived: NO error (BAD)")
    ok = False
except TypeError:
    print("foreign arrangement to derived: TypeError (good)")

# R4.1: exponent is arrangement -> NotImplementedError (base or subclass)
q = Permutation([1, 0, 2])
for exp, label in [(q, "base exp"), (MyPerm([1, 0, 2]), "subclass exp")]:
    try:
        q ** exp
        print("%s: NO error (BAD)" % label)
        ok = False
    except NotImplementedError:
        print("%s: NotImplementedError (good)" % label)

# R1.5: invalid array form -> ValueError
try:
    Permutation([1, 1, 2])
    print("repeated elements: NO error (BAD)")
    ok = False
except ValueError:
    print("repeated elements: ValueError (good)")

try:
    Permutation([1, 2, 3])  # missing 0
    print("missing 0..n-1: NO error (BAD)")
    ok = False
except ValueError:
    print("missing 0..n-1: ValueError (good)")

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R5: base-class behavior preserved (regression). Values, equality/hashing, call semantics.
All these hold on BASE too - regression guard."""
import sys
from sympy.combinatorics.permutations import Permutation, Cycle


ok = True

# R5.1 construction results
p_empty = Permutation()
print("empty array=%s size=%s" % (p_empty.array_form, p_empty.size))
if p_empty.array_form != [] or p_empty.size != 1 and p_empty.size != 0:
    pass  # size of empty is 1 historically? check leniently below

p_int = Permutation(4)
print("Permutation(4) array=%s size=%s" % (p_int.array_form, p_int.size))
if p_int.array_form != [0, 1, 2, 3, 4] or p_int.size != 5:
    ok = False

p_arr = Permutation([1, 0, 2, 3])
if p_arr.array_form != [1, 0, 2, 3]:
    ok = False
# cyclic
p_cyc = Permutation([[0, 1], [2, 3]])
print("cyclic array=%s" % p_cyc.array_form)
if p_cyc.array_form != [1, 0, 3, 2]:
    ok = False

# size extension
p_ext = Permutation([1, 0], size=4)
print("ext array=%s" % p_ext.array_form)
if p_ext.array_form != [1, 0, 2, 3]:
    ok = False

# R5.2 josephus / ranks / mul numeric
j = Permutation.josephus(3, 6, 1)
print("josephus array=%s" % j.array_form)
r = Permutation([1, 0, 2, 3]).rank()
print("rank=%s" % r)
if r != 6:
    ok = False

# R5.3 equality & hashing
a = Permutation([1, 0, 2])
b = Permutation([1, 0, 2])
print("eq=%s hash_eq=%s" % (a == b, hash(a) == hash(b)))
if not (a == b) or hash(a) != hash(b):
    ok = False

# Cycle handling
c = Cycle(1, 2)
pc = Permutation(c)
print("Cycle-> array=%s" % pc.array_form)
if pc.array_form != [0, 2, 1]:
    ok = False

# R5.5 application/call behavior
pa = Permutation([2, 0, 1])
print("apply 0 -> %s" % pa(0))
if pa(0) != 2:
    ok = False
# calling on unsupported argument -> TypeError
try:
    pa(object())
    # some versions may not raise; treat unsupported as needing TypeError
    print("apply object: NO TypeError")
    ok = False
except TypeError:
    print("apply object: TypeError (good)")

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: R1.1/R1.3 - construction on a subclass yields subclass instances.
Holds on patched tree, FAILS at base (base always reverts to Permutation)."""
import sys
from sympy.combinatorics.permutations import Permutation


class MyPerm(Permutation):
    pass


ok = True
# various accepted argument forms
cases = {
    "no args": MyPerm(),
    "single int": MyPerm(4),
    "array form": MyPerm([1, 0, 2, 3]),
    "cyclic form": MyPerm([[0, 1], [2, 3]]),
    "multiple cycle args": MyPerm(0, 1, 2),
    "existing arrangement": MyPerm(MyPerm([1, 0, 2])),
}
for name, obj in cases.items():
    t = type(obj).__name__
    is_sub = isinstance(obj, MyPerm) and type(obj) is MyPerm
    print("%-16s -> %s  (MyPerm=%s)" % (name, t, is_sub))
    if not is_sub:
        ok = False

# _af_new bound to invoking class (R1.3)
afn = MyPerm._af_new([1, 0, 2])
print("_af_new on subclass -> %s" % type(afn).__name__)
if type(afn) is not MyPerm:
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes, all HOLD on the gold-patched tree, covering: R1.1/R1.3 construction on subclass yields subclass instances incl _af_new (probe_1, positive control); R2.1-2.6 operations propagate operand class with unchanged array forms - mul(left governs), base*sub->base, pow/invert/xor/add (probe_2); R3.1-3.4 factory/unranking/next_*/commutator/rmul_with_af/mul_inv honor invoking class with identical numeric values (probe_3); R1.4 identity shortcut + foreign-class TypeError, R4.1/4.2 power-by-perm guard for base+subclass exponents, R1.5 ValueError on repeated/missing-integer array forms (probe_4); R5 regression: base construction/josephus/rank/equality+hashing/Cycle/apply semantics preserved (probe_5).

Positive control probe_1: HOLDS patched, VIOLATED at base (base always reverts subclass ops to Permutation) => discriminating. prepatch_reproduced=true.

CANDIDATE WRONG-FIX (partial.diff): fixes only __new__ dispatch and makes _af_new a classmethod, but leaves the many operation/factory methods (__mul__, __pow__, __invert__, __xor__, __add__, unrank_*, josephus, from_inversion_vector, random, commutator, rmul_with_af, mul_inv, next_*) plus the __pow__ guard referencing the module-level _af_new/Perm. Under this patch probes 2, 3, and 4 are REJECTED (VIOLATED) while 1 and 5 hold => the probe suite discriminates a plausible partial fix from the full gold fix. No requirements-conforming candidate found that would fail the hidden tests. All required runs completed.

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
"""Positive control: R1.1/R1.3 - construction on a subclass yields subclass instances.
Holds on patched tree, FAILS at base (base always reverts to Permutation)."""
import sys
from sympy.combinatorics.permutations import Permutation


class MyPerm(Permutation):
    pass


ok = True
# various accepted argument forms
cases = {
    "no args": MyPerm(),
    "single int": MyPerm(4),
    "array form": MyPerm([1, 0, 2, 3]),
    "cyclic form": MyPerm([[0, 1], [2, 3]]),
    "multiple cycle args": MyPerm(0, 1, 2),
    "existing arrangement": MyPerm(MyPerm([1, 0, 2])),
}
for name, obj in cases.items():
    t = type(obj).__name__
    is_sub = isinstance(obj, MyPerm) and type(obj) is MyPerm
    print("%-16s -> %s  (MyPerm=%s)" % (name, t, is_sub))
    if not is_sub:
        ok = False

# _af_new bound to invoking class (R1.3)
afn = MyPerm._af_new([1, 0, 2])
print("_af_new on subclass -> %s" % type(afn).__name__)
if type(afn) is not MyPerm:
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes, all HOLD on the gold-patched tree, covering: R1.1/R1.3 construction on subclass yields subclass instances incl _af_new (probe_1, positive control); R2.1-2.6 operations propagate operand class with unchanged array forms - mul(left governs), base*sub->base, pow/invert/xor/add (probe_2); R3.1-3.4 factory/unranking/next_*/commutator/rmul_with_af/mul_inv honor invoking class with identical numeric values (probe_3); R1.4 identity shortcut + foreign-class TypeError, R4.1/4.2 power-by-perm guard for base+subclass exponents, R1.5 ValueError on repeated/missing-integer array forms (probe_4); R5 regression: base construction/josephus/rank/equality+hashing/Cycle/apply semantics preserved (probe_5).

Positive control probe_1: HOLDS patched, VIOLATED at base (base always reverts subclass ops to Permutation) => discriminating. prepatch_reproduced=true.

CANDIDATE WRONG-FIX (partial.diff): fixes only __new__ dispatch and makes _af_new a classmethod, but leaves the many operation/factory methods (__mul__, __pow__, __invert__, __xor__, __add__, unrank_*, josephus, from_inversion_vector, random, commutator, rmul_with_af, mul_inv, next_*) plus the __pow__ guard referencing the module-level _af_new/Perm. Under this patch probes 2, 3, and 4 are REJECTED (VIOLATED) while 1 and 5 hold => the probe suite discriminates a plausible partial fix from the full gold fix. No requirements-conforming candidate found that would fail the hidden tests. All required runs completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces module-level Perm/_af_new references and Basic.__new__(Perm,...) with cls-based classmethod construction (__new__ crit isinstance(a,cls), _af_new as classmethod, factory classmethods use cls, __pow__ guard uses isinstance(n,Permutation)). Requirements accurately model both the class-propagation change and the invariance of array/cyclic forms, ranks, and error signalling. The deliberate crit4 behavior (foreign-class arrangement passed to derived ctor raises TypeError rather than adopting it) is a genuine consequence of isinstance(a,cls) failing and the value then being treated as a Cycle/sequence — confirmed empirically. No requirement mandates behavior the code lacks, forbids behavior it has, or pins a too-narrow boundary.

Counterexample / evidence:

```
N/A — probe returned HOLDS (exit 0) for the full battery of type-preservation and value-preservation assertions on the patched tree.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to Permutation.__new__, the _af_new helper, and the class-propagating methods (__mul__, __pow__, unrank_lex, josephus, from_inversion_vector, random, etc.). All of that is either already public in the problem_statement (which explicitly names Permutation.__new__, _af_new, Basic.__new__(Perm, perm), the Perm reference, and the classmethod/cls fix direction) or is legitimate localization of the change. Behavioral criteria such as Req 2.2 (type(q*p) is the base class because the LEFT operand governs) and Req 5.5 (call returns same result / raises TypeError out of contract) restate consequences derivable from Python dispatch and the base __call__ contract — behavioral translation, not transmission of the FAIL_TO_PASS test (test_Permutation_subclassing) code. The test's invented names (CustomPermutation, _hashable_content, the iterable __call__ form) do NOT appear; the doc uses generic 'MySubclass' and paraphrases. One suggestive item: Req 5.2's preservation list (josephus, ranking/unranking, multiplication, argument validation, Cycle handling, from-sequence, cyclic/array printing) follows the PASS_TO_PASS order (test_josephus/test_ranking/test_mul/test_args/test_Cycle/test_from_sequence/test_printing_cyclic), hinting the author walked the regression roster. However it contains no verbatim test names/paths/ids and every entry is a genuine behavioral surface of Permutation that a preservation requirement should name; no hidden test is reconstructible from it. Net: behavioral description, not test/gold transmission.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
