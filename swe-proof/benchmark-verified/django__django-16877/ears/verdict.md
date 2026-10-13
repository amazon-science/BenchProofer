# P2 adversarial audit — django__django-16877

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
"""Positive control: escapeseq is registered and escapes ordinary elements.
Req 1.1 (registered) + 1.4 (ordinary escaped). Must HOLD patched, FAIL at base."""
import sys
from django.template.defaultfilters import register

filt = register.filters.get("escapeseq")
if filt is None:
    print("FAIL: escapeseq not registered in default filter library")
    sys.exit(1)

out = filt(["a&b", "<x>", "c"])
print("escapeseq output:", out)
if list(out) != ["a&amp;b", "&lt;x&gt;", "c"]:
    print("FAIL: ordinary elements not escaped as expected")
    sys.exit(1)
print("PASS: escapeseq registered and escapes ordinary elements")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2: returns a list with exactly one entry per input element, preserving order.
Req 1.3: each entry == conditional_escape(element)."""
import sys
from django.template.defaultfilters import register
from django.utils.html import conditional_escape

filt = register.filters["escapeseq"]
inp = ["z", "a&b", "1", "<t>", "last"]
out = filt(inp)
print("type:", type(out).__name__, "output:", out)
if not isinstance(out, list):
    print("FAIL: output is not a list")
    sys.exit(1)
if len(out) != len(inp):
    print("FAIL: length mismatch", len(out), len(inp))
    sys.exit(1)
expected = [conditional_escape(x) for x in inp]
if out != expected:
    print("FAIL: entries not equal to conditional_escape per element / order not preserved")
    print("expected:", expected)
    sys.exit(1)
print("PASS: list, one-per-element, order preserved, each == conditional_escape")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.5 / 2.2: already-safe elements left unchanged (no double escaping)."""
import sys
from django.template.defaultfilters import register
from django.utils.safestring import mark_safe, SafeString
from django.utils.html import conditional_escape

filt = register.filters["escapeseq"]
safe_el = mark_safe("<b>bold</b>")
inp = [safe_el, "plain&"]
out = filt(inp)
print("output:", out)
# safe element must be unchanged (not re-escaped)
if str(out[0]) != "<b>bold</b>":
    print("FAIL: already-safe element was escaped:", out[0])
    sys.exit(1)
if str(out[1]) != "plain&amp;":
    print("FAIL: ordinary element not escaped:", out[1])
    sys.exit(1)
# match conditional_escape exactly
if out != [conditional_escape(x) for x in inp]:
    print("FAIL: does not match conditional_escape")
    sys.exit(1)
print("PASS: safe element unchanged, ordinary escaped")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.3: escapeseq registered with is_safe=True so output treated as safe
(downstream autoescape does not double-escape). Also Req 2.1: same results
regardless of autoescape state (rendered via template)."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {},
        }],
    )
django.setup()

from django.template import engines
from django.template.defaultfilters import register

# is_safe flag on the filter
filt = register.filters["escapeseq"]
print("is_safe:", getattr(filt, "is_safe", None))
if getattr(filt, "is_safe", False) is not True:
    print("FAIL: escapeseq not registered with is_safe=True")
    sys.exit(1)

dj = engines["django"]
ctx = {"lst": ["a&b", "<x>"]}

t_on = dj.from_string('{{ lst|escapeseq|join:"," }}')
r_on = t_on.render(ctx)
t_off = dj.from_string('{% autoescape off %}{{ lst|escapeseq|join:"," }}{% endautoescape %}')
r_off = t_off.render(ctx)
print("autoescape on :", repr(r_on))
print("autoescape off:", repr(r_off))

expected = "a&amp;b,&lt;x&gt;"
if r_on != expected:
    print("FAIL: autoescape-on render wrong (double escaping?)", r_on)
    sys.exit(1)
if r_off != expected:
    print("FAIL: autoescape-off render wrong", r_off)
    sys.exit(1)
if r_on != r_off:
    print("FAIL: autoescape on/off differ")
    sys.exit(1)
print("PASS: is_safe=True, same output on/off, join no double-escape")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.3 regression: existing safe, safeseq, escape filters unchanged."""
import sys
from django.template.defaultfilters import register
from django.utils.safestring import mark_safe

safe = register.filters["safe"]
safeseq = register.filters["safeseq"]
escape = register.filters["escape"]

# escape filter: escapes ordinary text, deferred/eager gives &amp; etc
e = escape("a&b<c>")
print("escape:", repr(str(e)))
if str(e) != "a&amp;b&lt;c&gt;":
    print("FAIL: escape filter changed")
    sys.exit(1)

# safe filter: marks unchanged
s = safe("<x>")
print("safe:", repr(str(s)))
if str(s) != "<x>":
    print("FAIL: safe filter changed")
    sys.exit(1)

# safeseq: returns list of safe strings unchanged text
ss = safeseq(["<a>", "b&"])
print("safeseq:", ss)
if [str(x) for x in ss] != ["<a>", "b&"]:
    print("FAIL: safeseq filter changed")
    sys.exit(1)

print("PASS: safe/safeseq/escape unchanged")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: escapeseq is registered and escapes ordinary elements.
Req 1.1 (registered) + 1.4 (ordinary escaped). Must HOLD patched, FAIL at base."""
import sys
from django.template.defaultfilters import register

filt = register.filters.get("escapeseq")
if filt is None:
    print("FAIL: escapeseq not registered in default filter library")
    sys.exit(1)

out = filt(["a&b", "<x>", "c"])
print("escapeseq output:", out)
if list(out) != ["a&amp;b", "&lt;x&gt;", "c"]:
    print("FAIL: ordinary elements not escaped as expected")
    sys.exit(1)
print("PASS: escapeseq registered and escapes ordinary elements")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: add `escapeseq` filter = per-element conditional_escape returning a list, registered is_safe=True.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1 registered + 1.4 ordinary escaped) — POSITIVE CONTROL: HOLDS patched, VIOLATED at base (escapeseq not registered). Discriminates.
- probe_2 (Req 1.2 list/one-per-element/order + 1.3 each == conditional_escape): HOLDS.
- probe_3 (Req 1.5 / 2.2 already-safe element left unchanged, ordinary escaped): HOLDS.
- probe_4 (Req 2.3 is_safe=True + 2.1 same output autoescape on/off via template + 3.1/3.2 join no double-escape): HOLDS patched.
- probe_5 (Req 3.3 regression: safe/safeseq/escape unchanged): HOLDS.

Candidate patch `weak_no_is_safe`: identical to gold but registers escapeseq with @register.filter (omitting is_safe=True) — the lazy partial fix a weak reading permits. REJECTED by probe_4 (is_safe: None, and would double-escape downstream under autoescape). This demonstrates the suite discriminates a requirements-violating implementation (Req 2.3 / 3.2). Note the official hidden tests include an autoescape-on join case that this weak patch would also fail.

All runs completed cleanly in the official image. 5 distinct probes hold on patched, positive control discriminates base, and a plausible wrong-fix is rejected.

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
"""Positive control: escapeseq is registered and escapes ordinary elements.
Req 1.1 (registered) + 1.4 (ordinary escaped). Must HOLD patched, FAIL at base."""
import sys
from django.template.defaultfilters import register

filt = register.filters.get("escapeseq")
if filt is None:
    print("FAIL: escapeseq not registered in default filter library")
    sys.exit(1)

out = filt(["a&b", "<x>", "c"])
print("escapeseq output:", out)
if list(out) != ["a&amp;b", "&lt;x&gt;", "c"]:
    print("FAIL: ordinary elements not escaped as expected")
    sys.exit(1)
print("PASS: escapeseq registered and escapes ordinary elements")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: add `escapeseq` filter = per-element conditional_escape returning a list, registered is_safe=True.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1 registered + 1.4 ordinary escaped) — POSITIVE CONTROL: HOLDS patched, VIOLATED at base (escapeseq not registered). Discriminates.
- probe_2 (Req 1.2 list/one-per-element/order + 1.3 each == conditional_escape): HOLDS.
- probe_3 (Req 1.5 / 2.2 already-safe element left unchanged, ordinary escaped): HOLDS.
- probe_4 (Req 2.3 is_safe=True + 2.1 same output autoescape on/off via template + 3.1/3.2 join no double-escape): HOLDS patched.
- probe_5 (Req 3.3 regression: safe/safeseq/escape unchanged): HOLDS.

Candidate patch `weak_no_is_safe`: identical to gold but registers escapeseq with @register.filter (omitting is_safe=True) — the lazy partial fix a weak reading permits. REJECTED by probe_4 (is_safe: None, and would double-escape downstream under autoescape). This demonstrates the suite discriminates a requirements-violating implementation (Req 2.3 / 3.2). Note the official hidden tests include an autoescape-on join case that this weak patch would also fail.

All runs completed cleanly in the official image. 5 distinct probes hold on patched, positive control discriminates base, and a plausible wrong-fix is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds escapeseq = [conditional_escape(obj) for obj in value] with is_safe=True. Probe HOLDS on patched tree, VIOLATED at base (filter absent). Requirements pin the actual changed observable behavior (per-element conditional_escape returning a list, registered as safe), not a narrow slice. No mandated-but-absent, forbidden-but-present, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document names the changed module (django/template/defaultfilters.py), the new filter (escapeseq), the join composition, and the safeseq/safe analogy — all present in the public problem_statement. It references conditional_escape and is_safe/safe-for-HTML output semantics, but these are existing Django API/behavior legitimately used to localize and describe the change, not fix-invented identifiers. The HTML-escaping examples (&->&amp;, <->&lt;, >->&gt;) are generic HTML-escaping facts, not the test's specific fixtures ('x&y', '<p>') or expected strings ('x&amp;y, &lt;p&gt;'). No test file path (test_escapeseq.py), class/function names (EscapeseqTests, test_basic, test_autoescape_off, test_chain_join, test_chain_join_autoescape_off), parametrization ids, or verbatim gold-patch lines ([conditional_escape(obj) for obj in value]) appear. The three requirements translate tested behavior into behavioral obligations rather than enumerating the test cases.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
