# P2 adversarial audit — sympy__sympy-20916

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

Counterexample / evidence:

```
Weak patch _name_with_digits_p = re.compile(r'^(\w+?)([0-9]+)$', re.U) makes Greek base pass (probe_1/6) but is REJECTED by probe_2 (Unicode Devanagari digits 'x१२' not peeled -> ('x१२',[],[])) and probe_4 (pure-digit name '123' wrongly split to ('1',[],['23']) because \w matches digits). Confirms requirements' Unicode-digit criterion (R1.4) and letters-only-base criterion (R2.1) discriminate the naive fix.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from sympy.printing.conventions import split_super_sub
# R1.1/1.3/1.5 POSITIVE CONTROL: Greek letter + digits -> base greek, digits subscript
r = split_super_sub('ω0')  # omega + '0'
print('omega0 ->', r)
latin = split_super_sub('w0')
print('w0 ->', latin)
ok = (r == ('ω', [], ['0'])) and (latin == ('w', [], ['0']))
# structural equivalence to latin
struct = (len(r[0]) == 1 and r[1] == latin[1] and r[2] == latin[2])
print('ok=', ok, 'struct=', struct)
sys.exit(0 if (ok and struct) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy.printing.conventions import split_super_sub
# R1.4: Unicode decimal digits recognized; mixed ascii+non-ascii digit run preserved
# Use Devanagari digits U+0966.. and arabic-indic. Also mixed.
name = 'x' + '१२'  # x + Devanagari 1,2
r = split_super_sub(name)
print('x + devanagari12 ->', r)
ok1 = r == ('x', [], ['१२'])
# mixed ascii + non-ascii digits
name2 = 'y' + '5१'
r2 = split_super_sub(name2)
print('y + 5 devanagari1 ->', r2)
ok2 = r2 == ('y', [], ['5१'])
print('ok1=', ok1, 'ok2=', ok2)
sys.exit(0 if (ok1 and ok2) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy.printing.conventions import split_super_sub
# R1.2 + R3.2: digit subscript inserted at FRONT, before explicit _ subs;
# superscript unaffected and recorded independently.
r = split_super_sub('alpha1_x^2')  # 'alpha' letters + '1', then _x sub, ^2 super
print('alpha1_x^2 ->', r)
# base name 'alpha1' peeled -> name 'alpha', digit '1' inserted front of subs, then 'x'
ok = r == ('alpha', ['2'], ['1', 'x'])
print('ok=', ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy.printing.conventions import split_super_sub
# R2: only peel when whole base is letters-then-digits; else untouched
cases = {
    '': ('', [], []),            # R2.3 empty
    'abc': ('abc', [], []),      # R2.2 no digits
    '1a': ('1a', [], []),        # doesn't begin with letter
    'a1b': ('a1b', [], []),      # extra chars after digit run
    '123': ('123', [], []),      # no letters
    'aa': ('aa', [], []),        # no digits
}
allok = True
for inp, exp in cases.items():
    got = split_super_sub(inp)
    ok = got == exp
    allok = allok and ok
    print(repr(inp), '->', got, 'exp', exp, ok)
sys.exit(0 if allok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy.printing.conventions import split_super_sub
# R3.1/3.4: ASCII-only regression cases keep working; marker parsing intact
cases = {
    'a_x^1': ('a', ['1'], ['x']),
    'var_sub1__sup_sub2': ('var', ['sup'], ['sub1', 'sub2']),
    'w0': ('w', [], ['0']),
    'w123': ('w', [], ['123']),
    'alpha42': ('alpha', [], ['42']),
    'x_1': ('x', [], ['1']),   # explicit marker only, base 'x', no digit-peel of base
}
allok = True
for inp, exp in cases.items():
    got = split_super_sub(inp)
    ok = got == exp
    allok = allok and ok
    print(repr(inp), '->', got, 'exp', exp, ok)
sys.exit(0 if allok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from sympy.printing.conventions import split_super_sub
# R3.3: marker-introduced non-ASCII content preserved verbatim; and greek multi-letter base
# Greek super/subscript content preserved
r = split_super_sub('x^ω')
print('x^omega ->', r)
ok1 = r == ('x', ['ω'], [])
r2 = split_super_sub('x_ω')
print('x_omega ->', r2)
ok2 = r2 == ('x', [], ['ω'])
# multi greek letters + digits (R1.5 multi-letter greek base)
r3 = split_super_sub('αβ12')
print('alphabeta12 ->', r3)
ok3 = r3 == ('αβ', [], ['12'])
print('ok1=',ok1,'ok2=',ok2,'ok3=',ok3)
sys.exit(0 if (ok1 and ok2 and ok3) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy.printing.conventions import split_super_sub
# R1.1/1.3/1.5 POSITIVE CONTROL: Greek letter + digits -> base greek, digits subscript
r = split_super_sub('ω0')  # omega + '0'
print('omega0 ->', r)
latin = split_super_sub('w0')
print('w0 ->', latin)
ok = (r == ('ω', [], ['0'])) and (latin == ('w', [], ['0']))
# structural equivalence to latin
struct = (len(r[0]) == 1 and r[1] == latin[1] and r[2] == latin[2])
print('ok=', ok, 'struct=', struct)
sys.exit(0 if (ok and struct) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements map: probe_1=R1.1/1.3/1.5 (Greek base + digit subscript, structurally identical to Latin) [POSITIVE CONTROL: HOLDS patched, VIOLATED at base]; probe_2=R1.4 (any Unicode decimal digit + mixed ascii/non-ascii run preserved verbatim); probe_3=R1.2+R3.2 (digit sub inserted at FRONT before explicit _ subs, superscript independent); probe_4=R2.1/2.2/2.3 (no spurious peel: empty, no-digits, non-letter-start, trailing junk, all-digits); probe_5=R3.1/3.4 (ASCII regression: docstring examples, single/multi-letter+digits, marker-only names); probe_6=R3.3+R1.5 (non-ASCII marker content verbatim, multi-Greek-letter base). All 6 HOLD on gold-patched tree; probe_1 & probe_6 VIOLATED at base (prepatch reproduced). Weak candidate applies at base_commit, satisfies some criteria but REJECTED by probes 2 and 4 -> suite discriminates. Gold patch uses r'^([^\W\d_]+)(\d+)$' with re.U which correctly excludes digits from the letter class. Verdict SOUND: >=5 distinct probes all hold, positive control discriminates, >=1 candidate exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak patch _name_with_digits_p = re.compile(r'^(\w+?)([0-9]+)$', re.U) makes Greek base pass (probe_1/6) but is REJECTED by probe_2 (Unicode Devanagari digits 'x१२' not peeled -> ('x१२',[],[])) and probe_4 (pure-digit name '123' wrongly split to ('1',[],['23']) because \w matches digits). Confirms requirements' Unicode-digit criterion (R1.4) and letters-only-base criterion (R2.1) discriminate the naive fix.
```

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
import sys
from sympy.printing.conventions import split_super_sub
# R1.1/1.3/1.5 POSITIVE CONTROL: Greek letter + digits -> base greek, digits subscript
r = split_super_sub('ω0')  # omega + '0'
print('omega0 ->', r)
latin = split_super_sub('w0')
print('w0 ->', latin)
ok = (r == ('ω', [], ['0'])) and (latin == ('w', [], ['0']))
# structural equivalence to latin
struct = (len(r[0]) == 1 and r[1] == latin[1] and r[2] == latin[2])
print('ok=', ok, 'struct=', struct)
sys.exit(0 if (ok and struct) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements map: probe_1=R1.1/1.3/1.5 (Greek base + digit subscript, structurally identical to Latin) [POSITIVE CONTROL: HOLDS patched, VIOLATED at base]; probe_2=R1.4 (any Unicode decimal digit + mixed ascii/non-ascii run preserved verbatim); probe_3=R1.2+R3.2 (digit sub inserted at FRONT before explicit _ subs, superscript independent); probe_4=R2.1/2.2/2.3 (no spurious peel: empty, no-digits, non-letter-start, trailing junk, all-digits); probe_5=R3.1/3.4 (ASCII regression: docstring examples, single/multi-letter+digits, marker-only names); probe_6=R3.3+R1.5 (non-ASCII marker content verbatim, multi-Greek-letter base). All 6 HOLD on gold-patched tree; probe_1 & probe_6 VIOLATED at base (prepatch reproduced). Weak candidate applies at base_commit, satisfies some criteria but REJECTED by probes 2 and 4 -> suite discriminates. Gold patch uses r'^([^\W\d_]+)(\d+)$' with re.U which correctly excludes digits from the letter class. Verdict SOUND: >=5 distinct probes all hold, positive control discriminates, >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes only the module-level regex _name_with_digits_p from r'^([a-zA-Z]+)([0-9]+)$' to r'^([^\W\d_]+)(\d+)$' with re.U, plus a comment capitalization. Requirements pin the observable return triple of split_super_sub — the exact changed observable behavior, correct modeling boundary (not a narrow slice/helper). All Unicode-awareness claims (any Unicode letter base, any Unicode decimal digit, front-insertion of peeled digits, unaffected superscripts, empty-input, preserved explicit-marker parsing) verified live in the instance image.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes split_super_sub behavior in general terms. It localizes the change to sympy/printing/conventions.py:split_super_sub and the module-level name-ending-in-digits pattern — legitimate localization already implied by the problem statement's symptom (ω0 vs w0). No test file path (test_conventions.py), no test function name (test_super_sub), no FAIL_TO_PASS id, no quoted test literals (w𝟙2𝟙, ω𝟙^α, etc.), no verbatim gold regex ([^\W\d_]+)(\d+) or re.U, and no fix-invented identifiers are transmitted. The Unicode-letter/Unicode-digit generalization is a behavioral description of the fix's intent, translatable directly from the problem statement (Greek letter ω vs Latin w). Borderline clauses Req 1.4 (mixed ASCII/non-ASCII digit runs preserved as one subscript) and Req 3.3 (non-ASCII marker content preserved verbatim) do parallel the exotic parametrized cases, but they are phrased as behavioral generalizations of 'any Unicode decimal digit / \d+ with re.U' rather than enumerations mirroring the specific test literals — a faithful implementer would derive both without seeing the tests. This is translating test-checked behavior into requirements (the intended activity), not transmitting the tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
