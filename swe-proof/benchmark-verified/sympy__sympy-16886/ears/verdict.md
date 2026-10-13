# P2 adversarial audit — sympy__sympy-16886

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1.1 + Req1.3: encode_morse("1") == ".----" ; occurrences represented
from sympy.crypto.crypto import encode_morse
r = encode_morse("1")
print("encode_morse('1') =", repr(r))
r2 = encode_morse("A1B")
print("encode_morse('A1B') =", repr(r2))
ok = (r == ".----") and (".----" in r2.split("|"))
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.2: no character maps to "----" (four dashes, no leading dot)
from sympy.crypto.crypto import encode_morse
# encoding "1" must not be "----"
r = encode_morse("1")
print("encode_morse('1') =", repr(r))
# also ensure "----" is not the encoding of any single supported char
import sympy.crypto.crypto as c
rev = getattr(c, "morse_char", None)
found_four_dash = False
if rev is not None:
    for ch, sym in rev.items():
        if sym == "----":
            found_four_dash = True
            print("char mapping to '----':", repr(ch))
print("morse_char present:", rev is not None)
ok = (r != "----") and (not found_four_dash)
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2.1/2.3: all digits 0-9 encode to correct symbols, joined by '|'
from sympy.crypto.crypto import encode_morse
expected = {"0":"-----","1":".----","2":"..---","3":"...--","4":"....-",
            "5":".....","6":"-....","7":"--...","8":"---..","9":"----."}
allok = True
for d,s in expected.items():
    got = encode_morse(d)
    print(d, "->", repr(got), "expected", repr(s))
    if got != s: allok = False
seq = encode_morse("0123456789")
exp_seq = "|".join(expected[d] for d in "0123456789")
print("seq =", repr(seq))
print("exp =", repr(exp_seq))
ok = allok and (seq == exp_seq)
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.1: decode_morse(".----") == "1"
from sympy.crypto.crypto import decode_morse
r = decode_morse(".----")
print("decode_morse('.----') =", repr(r))
import sys; sys.exit(0 if r == "1" else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3.3/3.4: letters A-Z and punctuation unchanged (standard values)
from sympy.crypto.crypto import encode_morse
letters = {
 "A":".-","B":"-...","C":"-.-.","D":"-..","E":".","F":"..-.","G":"--.",
 "H":"....","I":"..","J":".---","K":"-.-","L":".-..","M":"--","N":"-.",
 "O":"---","P":".--.","Q":"--.-","R":".-.","S":"...","T":"-","U":"..-",
 "V":"...-","W":".--","X":"-..-","Y":"-.--","Z":"--.."}
punct = {".":".-.-.-",",":"--..--",":":"---...",";":"-.-.-.","?":"..--..",
 "-":"-....-","_":"..--.-","(":"-.--.",")":"-.--.-","'":".----.",
 "=":"-...-","+":".-.-.","/":"-..-.","@":".--.-.","$":"...-..-","!":"-.-.--"}
allok=True
for ch,s in {**letters,**punct}.items():
    got=encode_morse(ch)
    if got!=s:
        allok=False
        print("MISMATCH",repr(ch),"->",repr(got),"expected",repr(s))
print("all letters+punct ok:", allok)
import sys; sys.exit(0 if allok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req3.2/3.5/3.6: round-trip, custom sep, unmapped chars omitted
from sympy.crypto.crypto import encode_morse, decode_morse
txt="HELLO WORLD 123"
enc=encode_morse(txt)
dec=decode_morse(enc)
print("enc=",repr(enc)); print("dec=",repr(dec))
rt = dec == "HELLO WORLD 123"
S="#"  # not a mapped Morse char
e1=encode_morse("SO", sep=S)
print("custom sep SO ->",repr(e1))
sep_ok = (e1 == "{}{}{}".format("...",S,"---"))
e2=encode_morse("A B", sep=S)
print("A B custom ->",repr(e2))
word_ok = (e2 == "{}{}{}{}".format(".-",S,S,"-..."))
e3=encode_morse("A%B")
print("A%B ->",repr(e3))
omit_ok = e3 == "{}|{}".format(".-","-...")
print("rt,sep,word,omit:",rt,sep_ok,word_ok,omit_ok)
ok = rt and sep_ok and word_ok and omit_ok
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.1 + Req1.3: encode_morse("1") == ".----" ; occurrences represented
from sympy.crypto.crypto import encode_morse
r = encode_morse("1")
print("encode_morse('1') =", repr(r))
r2 = encode_morse("A1B")
print("encode_morse('A1B') =", repr(r2))
ok = (r == ".----") and (".----" in r2.split("|"))
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes covering Req1.1/1.3 (probe_1), Req1.2 no-'----'-mapping (probe_2), Req2.1/2.3 all-digit symbols+join (probe_3), Req3.1 decode '.----' (probe_4), Req3.3/3.4 letters+punctuation unchanged (probe_5), Req3.2/3.5/3.6 round-trip/custom-sep/omit-unmapped (probe_6). All 6 HOLD on gold-patched tree. Positive controls: probe_1, probe_3 fail at base (base maps '1'->'----'); probe_4 fails at base. prepatch_reproduced=true.

Candidate patches: (1) 'wrong' maps '1'->'-...-' (a wrong symbol) — REJECTED by probes 1,3,4,6 (probe_2/5 still pass, as expected), demonstrating suite discriminates wrong impls. (2) 'weak' adds '.----':'1' while KEEPING '----':'1' in the source dict — passes ALL 6 probes. This is NOT a too-weak finding: last-key-wins makes the reverse (char->morse) table map '1'->'.----' identically to gold, so encode_morse('1')=='.----' and the hidden FAIL_TO_PASS test (encode_morse('12345')) passes; it is a behaviorally-equivalent alternate fix that also resolves. Requirements do not mandate the internal dict shape, only observable encode/decode behavior, which is faithfully pinned. No probe-conforming patch that fails the harness was found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Req1.1 + Req1.3: encode_morse("1") == ".----" ; occurrences represented
from sympy.crypto.crypto import encode_morse
r = encode_morse("1")
print("encode_morse('1') =", repr(r))
r2 = encode_morse("A1B")
print("encode_morse('A1B') =", repr(r2))
ok = (r == ".----") and (".----" in r2.split("|"))
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes covering Req1.1/1.3 (probe_1), Req1.2 no-'----'-mapping (probe_2), Req2.1/2.3 all-digit symbols+join (probe_3), Req3.1 decode '.----' (probe_4), Req3.3/3.4 letters+punctuation unchanged (probe_5), Req3.2/3.5/3.6 round-trip/custom-sep/omit-unmapped (probe_6). All 6 HOLD on gold-patched tree. Positive controls: probe_1, probe_3 fail at base (base maps '1'->'----'); probe_4 fails at base. prepatch_reproduced=true.

Candidate patches: (1) 'wrong' maps '1'->'-...-' (a wrong symbol) — REJECTED by probes 1,3,4,6 (probe_2/5 still pass, as expected), demonstrating suite discriminates wrong impls. (2) 'weak' adds '.----':'1' while KEEPING '----':'1' in the source dict — passes ALL 6 probes. This is NOT a too-weak finding: last-key-wins makes the reverse (char->morse) table map '1'->'.----' identically to gold, so encode_morse('1')=='.----' and the hidden FAIL_TO_PASS test (encode_morse('12345')) passes; it is a behaviorally-equivalent alternate fix that also resolves. Requirements do not mandate the internal dict shape, only observable encode/decode behavior, which is faithfully pinned. No probe-conforming patch that fails the harness was found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe HOLDS on gold-patched tree (exit 0) and VIOLATED at base (exit 1), confirming the requirements pin the changed observable behavior (digit-1 Morse mapping + full digit table + round-trip), not a narrow slice. R1.2 (must NOT map '1' to bare four-dashes) and R3.3/R3.4 (letters/punctuation unchanged), R3.5 (custom sep), R3.6 (omit unmapped) all correspond to the single-line change and preserved surrounding behavior. Requirements are faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe correcting the digit '1' Morse mapping (public in problem_statement) plus surrounding behavior. The full ten-digit symbol table in Req 2.1 is standard International Morse Code (general knowledge, derivable from the public fix), not a reproduction of the hidden test's specific strings '12345'/'67890' or their split. The doc describes general behavior ('consecutive digits joined by the letter separator') rather than mirroring the test parametrization. Punctuation list in Req 3.4 reflects the module's own table, not the test's '!@#$%^&*()_+' string. No test file paths, test function names (test_encode_morse/test_decode_morse), parametrization ids, quoted test/gold code, or fix-invented identifiers are transmitted. Naming the module/functions is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
