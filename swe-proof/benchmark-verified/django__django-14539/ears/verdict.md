# P2 adversarial audit — django__django-14539

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
weak.diff (partial fix: fixes only the `middle` slice to `middle[:-punctuation_count]` but keeps the old `trail = middle[len(stripped):] + trail`) is REJECTED by probe_1 (Req 1.6) producing '...google.com/?q=1&lt</a>lt!...' and by probe_5 (Req 1.2/1.4 multi-entity) producing '...&lt&gt</a>t&gt!!...'. This demonstrates the suite discriminates a plausibly-wrong implementation.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from django.utils.html import urlize

got = urlize('Search for google.com/?q=1&lt! and see.')
expected = 'Search for <a href="http://google.com/?q=1%3C">google.com/?q=1&lt</a>! and see.'
print("got     :", repr(got))
print("expected:", repr(expected))
sys.exit(0 if got == expected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2.2 / 2.1: URL with no entities followed by '!' keeps URL in anchor, '!' after tag.
import sys
from django.utils.html import urlize

got = urlize('Go to www.google.com!')
print("got:", repr(got))
# URL stays inside link, trailing '!' emitted after closing tag
ok = got == 'Go to <a href="http://www.google.com">www.google.com</a>!'
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 3.1: text with no linkifiable URL/email returned unchanged.
# Req 3.4: invalid emails not linkified.
import sys
from django.utils.html import urlize

cases = [
    "just some ordinary text with no links.",
    "@invalid",
    "invalid@",
    "a@b@c.com",
    "user@.com",
]
allok = True
for c in cases:
    got = urlize(c)
    unchanged = (got == c)
    print(repr(c), "->", repr(got), "unchanged" if unchanged else "CHANGED")
    if "<a " in got:
        allok = False
    if not unchanged:
        allok = False
sys.exit(0 if allok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.2 & 3.3: catastrophic inputs returned unchanged and complete fast (linear time).
import sys, time
from django.utils.html import urlize

# long run of trailing punctuation appended to text
inp1 = ('a' + '!' * 50000) + 'b'
# long run of repeated @-containing text (email-detection stress)
inp2 = '@' * 50000 + 'A'

allok = True
for inp in (inp1, inp2):
    t0 = time.time()
    got = urlize(inp)
    dt = time.time() - t0
    unchanged = (got == inp)
    print("len=%d dt=%.3fs unchanged=%s" % (len(inp), dt, unchanged))
    if not unchanged:
        allok = False
    if dt > 10:
        print("TOO SLOW")
        allok = False
sys.exit(0 if allok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 1.2/1.3/1.4: multiple shortening entities + trailing punctuation.
# Count of chars moved to trail must equal punctuation on decoded string (2),
# NOT inflated/reduced by the encoded/decoded length difference.
import sys, html
from django.utils.html import urlize

inp = 'see google.com/?a=1&lt&gt!! ok'
got = urlize(inp)
print("got:", repr(got))

# Extract anchor visible text and the char immediately after </a>
import re
m = re.search(r'<a [^>]*>(.*?)</a>(.*?) ok', got)
if not m:
    print("no anchor match")
    sys.exit(1)
visible = m.group(1)
after = m.group(2)
print("visible:", repr(visible), "after:", repr(after))

# Both entities must remain inside the anchor visible text; only '!!' moved out.
ok = visible == 'google.com/?a=1&lt&gt' and after == '!!'
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 2.3 / 1.5: an entity whose textual form ends in ';' (e.g. &amp;) must NOT
# have its terminating semicolon stripped; candidate with no trailing punct on
# decoded string is left unchanged by the step. Link text should retain &amp;.
import sys
from django.utils.html import urlize

got = urlize('go google.com/?a=1&amp;b=2 end')
print("got:", repr(got))
import re
m = re.search(r'<a [^>]*>(.*?)</a>', got)
if not m:
    print("no anchor")
    sys.exit(1)
visible = m.group(1)
print("visible:", repr(visible))
# semicolon of &amp; retained inside link
ok = '&amp;b=2' in visible
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from django.utils.html import urlize

got = urlize('Search for google.com/?q=1&lt! and see.')
expected = 'Search for <a href="http://google.com/?q=1%3C">google.com/?q=1&lt</a>! and see.'
print("got     :", repr(got))
print("expected:", repr(expected))
sys.exit(0 if got == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Candidate weak.diff exercised and REJECTED by 2 probes. (weak2.diff was corrupt and not counted.)

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
weak.diff (partial fix: fixes only the `middle` slice to `middle[:-punctuation_count]` but keeps the old `trail = middle[len(stripped):] + trail`) is REJECTED by probe_1 (Req 1.6) producing '...google.com/?q=1&lt</a>lt!...' and by probe_5 (Req 1.2/1.4 multi-entity) producing '...&lt&gt</a>t&gt!!...'. This demonstrates the suite discriminates a plausibly-wrong implementation.
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
from django.utils.html import urlize

got = urlize('Search for google.com/?q=1&lt! and see.')
expected = 'Search for <a href="http://google.com/?q=1%3C">google.com/?q=1&lt</a>! and see.'
print("got     :", repr(got))
print("expected:", repr(expected))
sys.exit(0 if got == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Candidate weak.diff exercised and REJECTED by 2 probes. (weak2.diff was corrupt and not counted.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary is correct, not a narrow slice: requirements target the decoded-vs-original length-mismatch split (the exact source of the '&ltlt' duplication bug in the issue), and Req 1.4 explicitly generalizes beyond the single-entity example, matching the length-difference-agnostic patched formula. Req 2/3 accurately describe unchanged/preserved behavior. FAITHFUL.

Counterexample / evidence:

```
None found. Probe on gold-patched tree: urlize('Search for google.com/?q=1&lt! and see.') == 'Search for <a href="http://google.com/?q=1%3C">google.com/?q=1&lt</a>! and see.' (HOLDS, exit 0). Same probe --base VIOLATED (produced '...&lt</a>lt! and see.'), confirming the requirements pin the actual delta. Multi-entity check urlize('google.com/?q=1&lt&gt! and') == '<a href="http://google.com/?q=1%3C%3E">google.com/?q=1&lt&gt</a>! and' confirms Req 1.4 (count not inflated by 2 entities).
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The only concrete input/output example (Search for google.com/?q=1&lt! ... -> ...%3C">google.com/?q=1&lt</a>! and see.) is quoted verbatim from the PUBLIC problem_statement, so it is fair game. Requirement 1 is a legitimate behavioral translation of the gold edit in trim_punctuation (punctuation_count = len(middle_unescaped)-len(stripped); slice original by that count) without naming the fix-invented variable or quoting code; naming trim_punctuation/html.unescape/TRAILING_PUNCTUATION_CHARS and the set `.,:;!` is legitimate source-level localization. Requirement 3's stress/regression items loosely correspond to the hidden FAIL_TO_PASS test `test_urlize_unchanged_inputs`, but they are stated as behavioral categories (catastrophic-backtracking guard, invalid-email non-linkification) drawn from urlize's documented design rather than reproducing the test's input tuples, names, paths, or ids. No test names/paths (test_urlize, test_urlize_unchanged_inputs, TestUtilsHtml), no parametrization ids, no verbatim gold-patch lines, and no fix-invented identifiers appear. Borderline test-shaped prose in Req 3, but it remains behavioral, not a reconstruction of the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
