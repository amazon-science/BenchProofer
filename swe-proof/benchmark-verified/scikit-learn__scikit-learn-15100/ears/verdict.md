# P2 adversarial audit — scikit-learn__scikit-learn-15100

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from sklearn.feature_extraction.text import strip_accents_unicode

# R1.1 + positive control: decomposed base + combining mark -> base only
s = "n" + "̃"  # n followed by COMBINING TILDE
out = strip_accents_unicode(s)
print("input=%r out=%r" % (s, out))
sys.exit(0 if out == "n" else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sklearn.feature_extraction.text import strip_accents_unicode

# R1.2: precomposed and decomposed forms yield same result
precomposed = "ñ"          # ñ single code point
decomposed = "n" + "̃"      # n + combining tilde
a = strip_accents_unicode(precomposed)
b = strip_accents_unicode(decomposed)
print("precomposed->%r decomposed->%r" % (a, b))
sys.exit(0 if a == b else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sklearn.feature_extraction.text import strip_accents_unicode

# R1.3: string of only combining marks -> empty string
s = "̃́̈"  # three standalone combining marks
out = strip_accents_unicode(s)
print("input=%r out=%r" % (s, out))
sys.exit(0 if out == "" else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sklearn.feature_extraction.text import strip_accents_unicode

# R1.4: single base char carrying multiple combining marks -> base char only
s = "e" + "́" + "̂" + "̈"  # e with acute, circumflex, diaeresis
out = strip_accents_unicode(s)
print("input=%r out=%r" % (s, out))
sys.exit(0 if out == "e" else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sklearn.feature_extraction.text import strip_accents_unicode

# R2.1/R2.2: precomposed accented string -> base letters, order preserved
s = "àéîõü"  # à é î õ ü
out = strip_accents_unicode(s)
print("input=%r out=%r" % (s, out))
sys.exit(0 if out == "aeiou" else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from sklearn.feature_extraction.text import strip_accents_unicode

# R3.1/R3.2: pure ASCII (incl. non-letter chars) returned unchanged and identical object semantics
s = "Hello, World! 123 #@$%\t\n"
out = strip_accents_unicode(s)
print("input=%r out=%r" % (s, out))
sys.exit(0 if out == s else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
from sklearn.feature_extraction.text import strip_accents_ascii

# R4.1: strip_accents_ascii still transliterates to ASCII base letters
s = "àéî ñ"  # "àéî ñ"
out = strip_accents_ascii(s)
print("input=%r out=%r" % (s, out))
ok = out == "aei n" and all(ord(c) < 128 for c in out)
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import sys
from sklearn.feature_extraction.text import strip_accents_unicode

# R4.4: accepts any python string and always returns a string; R4.3 via vectorizer
from sklearn.feature_extraction.text import CountVectorizer

for s in ["", "abc", "n" + "̃", "ñ", "̃"]:
    out = strip_accents_unicode(s)
    assert isinstance(out, str), (s, out)

# R4.3: vectorizer with strip_accents="unicode" strips decomposed accents
cv = CountVectorizer(strip_accents="unicode")
pp = cv.build_preprocessor()
# preprocessor lowercases + strip_accents; check decomposed == precomposed
d = pp("N" + "̃")
p = pp("Ñ")  # Ñ
print("decomposed->%r precomposed->%r" % (d, p))
sys.exit(0 if (d == p and "̃" not in d) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sklearn.feature_extraction.text import strip_accents_unicode

# R1.1 + positive control: decomposed base + combining mark -> base only
s = "n" + "̃"  # n followed by COMBINING TILDE
out = strip_accents_unicode(s)
print("input=%r out=%r" % (s, out))
sys.exit(0 if out == "n" else 1)
```

Prepatch bug re-encoded as an attack: `True`.

strip_accents_unicode accent-stripping fix (scikit-learn 15100). 8 probes cover all criteria:
- probe_1 (R1.1, POSITIVE CONTROL): decomposed 'n'+combining-tilde -> 'n'. HOLDS patched, VIOLATED at base (out='ñ').
- probe_2 (R1.2): precomposed 'ñ' and decomposed form yield same result. HOLDS patched; VIOLATED at base.
- probe_3 (R1.3): string of only combining marks -> ''. HOLDS patched; VIOLATED at base.
- probe_4 (R1.4): single base + multiple combining marks -> base only. HOLDS patched; VIOLATED at base.
- probe_5 (R2.1/2.2): precomposed 'àéîõü' -> 'aeiou'. HOLDS patched.
- probe_6 (R3.1/3.2): pure-ASCII incl. punctuation/whitespace unchanged. HOLDS patched.
- probe_7 (R4.1): strip_accents_ascii still transliterates to ASCII. HOLDS patched.
- probe_8 (R4.3/4.4): always returns str; CountVectorizer(strip_accents='unicode') preprocessor treats decomposed==precomposed. HOLDS patched.

Positive control discriminates: probes 1-4 all VIOLATED at base (fail-to-strip on decomposed input), HOLD on gold patch.

Candidate wrong-fix weak_A (drop combining marks from raw string WITHOUT NFKD normalization): REJECTED by suite — probe_2 (precomposed 'ñ' left as 'ñ' since it has no standalone combining marks), probe_5 (precomposed accents untouched -> 'àéîõü'), and probe_8 (vectorizer decomposed!=precomposed) all fail. This is exactly the fix a weak reading (Req 1 only) would permit and it would not resolve the hidden tests (precomposed cases in test_strip_accents). Suite demonstrably discriminates wrong implementations.

Verdict SOUND: >=5 distinct probes all hold on patched tree, positive control discriminates (holds patched, fails base), and a plausibly-wrong alternative patch is rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sklearn.feature_extraction.text import strip_accents_unicode

# R1.1 + positive control: decomposed base + combining mark -> base only
s = "n" + "̃"  # n followed by COMBINING TILDE
out = strip_accents_unicode(s)
print("input=%r out=%r" % (s, out))
sys.exit(0 if out == "n" else 1)
```

Prepatch bug re-encoded as an attack: `True`.

strip_accents_unicode accent-stripping fix (scikit-learn 15100). 8 probes cover all criteria:
- probe_1 (R1.1, POSITIVE CONTROL): decomposed 'n'+combining-tilde -> 'n'. HOLDS patched, VIOLATED at base (out='ñ').
- probe_2 (R1.2): precomposed 'ñ' and decomposed form yield same result. HOLDS patched; VIOLATED at base.
- probe_3 (R1.3): string of only combining marks -> ''. HOLDS patched; VIOLATED at base.
- probe_4 (R1.4): single base + multiple combining marks -> base only. HOLDS patched; VIOLATED at base.
- probe_5 (R2.1/2.2): precomposed 'àéîõü' -> 'aeiou'. HOLDS patched.
- probe_6 (R3.1/3.2): pure-ASCII incl. punctuation/whitespace unchanged. HOLDS patched.
- probe_7 (R4.1): strip_accents_ascii still transliterates to ASCII. HOLDS patched.
- probe_8 (R4.3/4.4): always returns str; CountVectorizer(strip_accents='unicode') preprocessor treats decomposed==precomposed. HOLDS patched.

Positive control discriminates: probes 1-4 all VIOLATED at base (fail-to-strip on decomposed input), HOLD on gold patch.

Candidate wrong-fix weak_A (drop combining marks from raw string WITHOUT NFKD normalization): REJECTED by suite — probe_2 (precomposed 'ñ' left as 'ñ' since it has no standalone combining marks), probe_5 (precomposed accents untouched -> 'àéîõü'), and probe_8 (vectorizer decomposed!=precomposed) all fail. This is exactly the fix a weak reading (Req 1 only) would permit and it would not resolve the hidden tests (precomposed cases in test_strip_accents). Suite demonstrably discriminates wrong implementations.

Verdict SOUND: >=5 distinct probes all hold on patched tree, positive control discriminates (holds patched, fails base), and a plausibly-wrong alternative patch is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch replaces the `normalized == s` short-circuit with an ASCII-encode try/except: ASCII strings are returned verbatim (R3), non-ASCII strings are NFKD-decomposed with combining marks dropped (R1/R2). Requirements correctly frame the decision as 'contains a non-ASCII code point' rather than 'already decomposed'. R4 is a preservation clause (ascii helper + vectorizers unchanged), consistent with the diff touching only strip_accents_unicode. Probe HOLDS on patched (exit 0, ALL PASS), VIOLATED on base.

Counterexample / evidence:

```
None. Base (unpatched) probe VIOLATES exactly the R1 decomposed case: strip_accents_unicode('n'+U+0303) returns 'ñ' unstripped, while patched returns 'n' — matching the issue and the requirements' modeled boundary.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe strip_accents_unicode's behavior and localize the change to sklearn/feature_extraction/text.py (legitimate). The hidden test adds three inline asserts beyond the public problem_statement: decomposed o+diaeresis -> 'o', pure combining marks -> '', and multiple combining marks on one base -> base. Requirement 1 AC 1.3 (combining-marks-only -> empty string) and AC 1.4 (single base + multiple combining marks -> base only) do correspond to test cases 2 and 3. However these are not leaks: (a) no test names/paths/ids, no quoted test or gold code, no fix-invented identifiers appear; (b) the doc uses ONLY the problem_statement's own n-with-tilde example, never the test's code points (̈, ̄, 'o'); (c) both edge cases are deterministic, mechanical consequences of the algorithm already fully stated in AC 2.2 ('NFKD decomposition with every combining mark discarded') and the Introduction's description of the fix — any author understanding the described behavior derives 'all marks, no base -> empty' and 'multiple marks -> base' without seeing the tests. This is behavioral translation, which is the intended purpose, not transcription of the hidden tests. The non-parametrized inline test structure is not mirrored. The gold edit (ASCII-encode try/except) is not reflected as an implementation prescription; the doc specifies observable behavior only.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
