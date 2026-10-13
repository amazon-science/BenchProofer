# P2 adversarial audit — django__django-11276

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
# Req 1: escape emits &#x27; for single-quote (positive control)
from django.utils.html import escape
out = str(escape("a'b'c"))
print("observed:", repr(out))
assert out == "a&#x27;b&#x27;c", out
assert "&#39;" not in out, "legacy decimal form present"
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2: other HTML-significant chars unchanged; non-special chars untouched
from django.utils.html import escape
out = str(escape('&<>"' + "abc 123 é"))
print("observed:", repr(out))
assert out == "&amp;&lt;&gt;&quot;abc 123 é", out
# non-special char left unchanged
assert str(escape("x")) == "x"
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 3: ampersand-first ordering, no double-escape; empty input; re-escapes existing entities
from django.utils.html import escape
# ampersands introduced by replacements not re-escaped
out = str(escape("<a>&'\""))
print("mixed:", repr(out))
assert out == "&lt;a&gt;&amp;&#x27;&quot;", out
# empty
assert str(escape("")) == "", repr(escape(""))
# already-escaped input: & of existing entity gets escaped again
out2 = str(escape("&amp;"))
print("preescaped:", repr(out2))
assert out2 == "&amp;amp;", out2
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 4: non-string coercion, safe-marked result, lazy preservation
from django.utils.html import escape
from django.utils.safestring import SafeString
from django.utils.functional import lazy

# non-string coercion
out = str(escape(12 < 3 and 1 or 5))  # int 5
print("int:", repr(out))
assert out == "5", out
# object with str containing quote
class C:
    def __str__(self): return "x'y"
out2 = str(escape(C()))
print("obj:", repr(out2))
assert out2 == "x&#x27;y", out2
# safe-marked
r = escape("a'b")
assert isinstance(r, SafeString), type(r)
# lazy preservation
lazystr = lazy(lambda: "l'z", str)
res = escape(lazystr())
print("lazy:", repr(str(res)))
assert str(res) == "l&#x27;z", str(res)
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 5: urlize decodes HTML entities (full standards-based set) into the link target.
# The href is smart_urlquote(html.unescape(middle)), so decoded chars appear percent-encoded.
import re
from django.utils.html import urlize

def href(out):
    m = re.search(r'href="([^"]*)"', out)
    return m.group(1) if m else None

# Named entity beyond the five ad-hoc ones (&copy;) must be decoded => © => %C2%A9
h1 = href(urlize("http://example.com/?q=&copy;x"))
print("copy href:", h1)
assert h1 == "http://example.com/?q=%C2%A9x", h1

# Hex numeric single-quote entity (&#x27;) must be decoded => ' => %27
h2 = href(urlize("http://example.com/?a=&#x27;b"))
print("hex apos href:", h2)
assert h2 == "http://example.com/?a=%27b", h2

# Decimal single-quote entity (&#39;) still decoded => ' => %27
h3 = href(urlize("http://example.com/?a=&#39;b"))
print("dec apos href:", h3)
assert h3 == "http://example.com/?a=%27b", h3

print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 5.3 / 6: trailing punctuation not stripped when it's part of an entity;
# and entity-free linking unchanged (regression)
from django.utils.html import urlize
# entity-free basic link + trailing punctuation trimmed as before
out = urlize("Visit http://example.com.")
print("basic:", out)
assert '<a href="http://example.com"' in out, out
assert out.endswith("."), out  # trailing period preserved outside link
# www link
out2 = urlize("go to www.example.com now")
print("www:", out2)
assert 'href="http://www.example.com"' in out2, out2
# email
out3 = urlize("mail me foo@example.com ok")
print("email:", out3)
assert 'href="mailto:foo@example.com"' in out3, out3
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1: escape emits &#x27; for single-quote (positive control)
from django.utils.html import escape
out = str(escape("a'b'c"))
print("observed:", repr(out))
assert out == "a&#x27;b&#x27;c", out
assert "&#39;" not in out, "legacy decimal form present"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover two changes in django/utils/html.py: (a) escape() emits &#x27; instead of &#39; for single-quote, all other escaping unchanged; (b) urlize() uses standards-based html.unescape() instead of the ad-hoc 5-entity unescaper before building link targets / trimming trailing punctuation.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1): escape("a'b'c")=="a&#x27;b&#x27;c", no &#39;. POSITIVE CONTROL: HOLDS patched, FAILS base (base gives a&#39;b&#39;c). Discriminates.
- probe_2 (Req 2): &,<,>," escape to &amp;&lt;&gt;&quot;; non-special chars untouched. HOLDS.
- probe_3 (Req 3): ampersand-first (no double-escape), empty->empty, existing entity's & re-escaped (&amp; -> &amp;amp;). HOLDS.
- probe_4 (Req 4): int coercion ->"5", obj __str__ with quote ->x&#x27;y, SafeString instance, lazy value escapes to l&#x27;z. HOLDS.
- probe_5 (Req 5): urlize href targets decode a NAMED entity beyond the ad-hoc five (&copy;->%C2%A9) and both single-quote forms (&#x27;,&#39; -> %27). HOLDS patched, FAILS base (base yields &amp;copy%3B garbage). Second discriminator.
- probe_6 (Req 6 regression): entity-free http/www/mailto linking and trailing-punctuation trim preserved. HOLDS.

Candidate patch escape_only_weak (weak.diff): only flips the escape() translation table entry to &#x27;, leaving urlize's ad-hoc unescape() intact. Satisfies Req 1-4 (probes 1-4 HOLD) but probe_5 REJECTS it (urlize still can't decode &copy;) — demonstrates the suite discriminates a plausible partial fix. This is the exact lazy reading a weak spec would permit, and the runner can confirm it fails the hidden urlize tests.

>=5 distinct probes all hold on patched; positive control (probe_1) discriminates patched vs base (prepatch_reproduced=true); a probe-conforming-on-escape wrong fix is rejected by probe_5. Verdict SOUND.

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
# Req 1: escape emits &#x27; for single-quote (positive control)
from django.utils.html import escape
out = str(escape("a'b'c"))
print("observed:", repr(out))
assert out == "a&#x27;b&#x27;c", out
assert "&#39;" not in out, "legacy decimal form present"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover two changes in django/utils/html.py: (a) escape() emits &#x27; instead of &#39; for single-quote, all other escaping unchanged; (b) urlize() uses standards-based html.unescape() instead of the ad-hoc 5-entity unescaper before building link targets / trimming trailing punctuation.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1): escape("a'b'c")=="a&#x27;b&#x27;c", no &#39;. POSITIVE CONTROL: HOLDS patched, FAILS base (base gives a&#39;b&#39;c). Discriminates.
- probe_2 (Req 2): &,<,>," escape to &amp;&lt;&gt;&quot;; non-special chars untouched. HOLDS.
- probe_3 (Req 3): ampersand-first (no double-escape), empty->empty, existing entity's & re-escaped (&amp; -> &amp;amp;). HOLDS.
- probe_4 (Req 4): int coercion ->"5", obj __str__ with quote ->x&#x27;y, SafeString instance, lazy value escapes to l&#x27;z. HOLDS.
- probe_5 (Req 5): urlize href targets decode a NAMED entity beyond the ad-hoc five (&copy;->%C2%A9) and both single-quote forms (&#x27;,&#39; -> %27). HOLDS patched, FAILS base (base yields &amp;copy%3B garbage). Second discriminator.
- probe_6 (Req 6 regression): entity-free http/www/mailto linking and trailing-punctuation trim preserved. HOLDS.

Candidate patch escape_only_weak (weak.diff): only flips the escape() translation table entry to &#x27;, leaving urlize's ad-hoc unescape() intact. Satisfies Req 1-4 (probes 1-4 HOLD) but probe_5 REJECTS it (urlize still can't decode &copy;) — demonstrates the suite discriminates a plausible partial fix. This is the exact lazy reading a weak spec would permit, and the runner can confirm it fails the hidden urlize tests.

>=5 distinct probes all hold on patched; positive control (probe_1) discriminates patched vs base (prepatch_reproduced=true); a probe-conforming-on-escape wrong fix is rejected by probe_5. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch replaces the private _html_escapes translate table with stdlib html.escape() (which emits &#x27; for apostrophe) and replaces urlize's ad-hoc 5-entity unescape() with html.unescape(). Requirements pin the changed OBSERVABLE behavior (the apostrophe entity form, both branches of escape's callers, and urlize's full-entity decoding used in trim_punctuation and both url branches) rather than a narrow slice — modeling boundary is correct. All probes exit 0 on the gold-patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the PUBLIC problem_statement and the general design. The single-quote change from &#39; to &#x27; is stated verbatim in the problem_statement ('html.escape() converts ' to &#x27 rather than &#39'), so Requirement 1's specification of &#x27; is public, not leaked. The enumerated downstream consumers (form widgets, form/field errors, admin model/method docs, technical debug/exception report, addslashes/title/make_list filters, url template tag, urlize) are genuine real call sites of escape() and legitimate localization of where behavior is observable — the problem_statement itself notes escape() is 'called numerous times when rendering templates.' Although these consumers happen to correspond to the touched test files, the document never transmits the tests: no test names, node-ids, file paths, quoted test or gold code appear. The gold's new identifiers html.escape/html.unescape are NOT named — they are described generically as 'the Python standard library escaper' and 'standards-based HTML unescaping.' The urlize wrapping-punctuation parametrization ('<>','[]','""',"''") is not mirrored as a case list; it is described abstractly as 'balanced wrapping punctuation.' The full-entity-decoding requirement (both &#39; and &#x27; forms decoded) follows from the code change (private 5-entity unescape -> html.unescape) and is behavioral, not test-shaped. All content is behavioral translation of the spec, which is the intended purpose of the document.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
