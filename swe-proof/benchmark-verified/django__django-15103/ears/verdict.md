# P2 adversarial audit — django__django-15103

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
"""Req1.1/1.2 + positive control: json_script callable with value only -> no id attr."""
import sys
from django.utils.html import json_script

try:
    out = json_script({"a": 1})
except TypeError as e:
    print("FAIL: json_script raised TypeError with single arg:", e)
    sys.exit(1)

out = str(out)
print("observed:", out)
if 'id=' in out:
    print("FAIL: id attribute present when none supplied")
    sys.exit(1)
if not out.startswith('<script type="application/json">'):
    print("FAIL: unexpected opening tag")
    sys.exit(1)
if not out.endswith('</script>'):
    print("FAIL: no closing tag")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3/3.4: with a non-empty identifier the output is identical to prior with-id behavior."""
import sys
from django.utils.html import json_script

out = str(json_script({"a": 1}, "myid"))
print("observed:", out)
expected = '<script id="myid" type="application/json">{"a": 1}</script>'
if out != expected:
    print("FAIL: expected", expected)
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3.2: HTML/XML special chars <,>,& escaped as unicode escapes in body (both id and no-id)."""
import sys
from django.utils.html import json_script

val = {"a": "<script>&</script>"}
for eid in (None, "x"):
    out = str(json_script(val, eid) if eid else json_script(val))
    print("eid=%r observed:" % eid, out)
    # raw special chars must NOT appear in the encoded body
    body = out.split(">", 1)[1].rsplit("</script>", 1)[0]
    if "<" in body or ">" in body or "&" in body:
        print("FAIL: unescaped special char in body")
        sys.exit(1)
    # the unicode escape sequences must be present
    if "\\u003C" not in body or "\\u003E" not in body or "\\u0026" not in body:
        print("FAIL: expected unicode escapes missing")
        sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1: DjangoJSONEncoder used (dates/Decimals). Also no-id case."""
import sys
import datetime
from decimal import Decimal
from django.utils.html import json_script

val = {"d": datetime.date(2020, 1, 2), "n": Decimal("1.5")}
out = str(json_script(val))
print("observed:", out)
if '"2020-01-02"' not in out:
    print("FAIL: date not encoded via DjangoJSONEncoder")
    sys.exit(1)
if "1.5" not in out:
    print("FAIL: Decimal not encoded")
    sys.exit(1)
if 'id=' in out:
    print("FAIL: unexpected id attr")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3/2.4: template filter optional arg, matches utility function, id escaping (Req3.3)."""
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(TEMPLATES=[{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {},
    }], INSTALLED_APPS=[])
django.setup()

from django.template import Template, Context
from django.utils.html import json_script

# no-arg filter
t = Template("{{ v|json_script }}")
r = t.render(Context({"v": {"a": 1}}))
print("no-arg:", r)
if r != str(json_script({"a": 1})):
    print("FAIL: no-arg filter != utility no-id")
    sys.exit(1)
if 'id=' in r:
    print("FAIL: id attr present with no-arg filter")
    sys.exit(1)

# with-arg filter matches utility
t2 = Template('{{ v|json_script:"myid" }}')
r2 = t2.render(Context({"v": {"a": 1}}))
print("with-arg:", r2)
if r2 != str(json_script({"a": 1}, "myid")):
    print("FAIL: with-arg filter != utility with-id")
    sys.exit(1)

# Req3.3: id attribute escaped like a substituted format_html arg
out = str(json_script({"a": 1}, '"><b>'))
print("escaped-id:", out)
if '<b>' in out or '"><b>' in out:
    print("FAIL: id not escaped")
    sys.exit(1)
if '&lt;b&gt;' not in out or '&quot;' not in out:
    print("FAIL: expected html-escaped id chars missing")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req1.5: result marked safe for direct HTML inclusion (SafeString)."""
import sys
from django.utils.html import json_script
from django.utils.safestring import SafeString

out = json_script({"a": "<b>"})
print("type:", type(out), "value:", out)
if not isinstance(out, SafeString):
    print("FAIL: output not SafeString/marked safe")
    sys.exit(1)
out2 = json_script({"a": 1}, "x")
if not isinstance(out2, SafeString):
    print("FAIL: with-id output not SafeString")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req1.2: empty-string identifier is treated as absent -> no id attribute."""
import sys
from django.utils.html import json_script

out = str(json_script({"a": 1}, ""))
print("observed:", out)
if 'id=' in out:
    print("FAIL: empty-string id produced an id attribute")
    sys.exit(1)
if out != '<script type="application/json">{"a": 1}</script>':
    print("FAIL: unexpected output")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1/1.2 + positive control: json_script callable with value only -> no id attr."""
import sys
from django.utils.html import json_script

try:
    out = json_script({"a": 1})
except TypeError as e:
    print("FAIL: json_script raised TypeError with single arg:", e)
    sys.exit(1)

out = str(out)
print("observed:", out)
if 'id=' in out:
    print("FAIL: id attribute present when none supplied")
    sys.exit(1)
if not out.startswith('<script type="application/json">'):
    print("FAIL: unexpected opening tag")
    sys.exit(1)
if not out.endswith('</script>'):
    print("FAIL: no closing tag")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover: R1.1/1.2 single-arg call yields no id attr (probe_1, positive control), R1.3/3.4 exact with-id output (probe_2), R3.2 unicode-escape of <,>,& in both id/no-id cases (probe_3), R3.1 DjangoJSONEncoder dates/Decimals (probe_4), R2.1-2.4 template filter no-arg/with-arg matching utility + R3.3 id escaping (probe_5), R1.5 SafeString (probe_6), R1.2 empty-string identifier treated as absent (probe_7). All 7 HOLD on gold-patched tree. Positive controls probe_1/probe_5/probe_7 FAIL at base (TypeError/TemplateSyntaxError / id="" rendered). Wrong-fix candidate weak.diff (element_id default = "" but code path unchanged, so always renders id="") is REJECTED by probe_1 and probe_7 — proving the suite discriminates the lazy 'make arg optional without guarding empty' fix that a weak reading of the requirements would permit. Suite has discriminating power and no probe-conforming alternative found that fails hidden tests. Verdict SOUND.

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
"""Req1.1/1.2 + positive control: json_script callable with value only -> no id attr."""
import sys
from django.utils.html import json_script

try:
    out = json_script({"a": 1})
except TypeError as e:
    print("FAIL: json_script raised TypeError with single arg:", e)
    sys.exit(1)

out = str(out)
print("observed:", out)
if 'id=' in out:
    print("FAIL: id attribute present when none supplied")
    sys.exit(1)
if not out.startswith('<script type="application/json">'):
    print("FAIL: unexpected opening tag")
    sys.exit(1)
if not out.endswith('</script>'):
    print("FAIL: no closing tag")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover: R1.1/1.2 single-arg call yields no id attr (probe_1, positive control), R1.3/3.4 exact with-id output (probe_2), R3.2 unicode-escape of <,>,& in both id/no-id cases (probe_3), R3.1 DjangoJSONEncoder dates/Decimals (probe_4), R2.1-2.4 template filter no-arg/with-arg matching utility + R3.3 id escaping (probe_5), R1.5 SafeString (probe_6), R1.2 empty-string identifier treated as absent (probe_7). All 7 HOLD on gold-patched tree. Positive controls probe_1/probe_5/probe_7 FAIL at base (TypeError/TemplateSyntaxError / id="" rendered). Wrong-fix candidate weak.diff (element_id default = "" but code path unchanged, so always renders id="") is REJECTED by probe_1 and probe_7 — proving the suite discriminates the lazy 'make arg optional without guarding empty' fix that a weak reading of the requirements would permit. Suite has discriminating power and no probe-conforming alternative found that fails hidden tests. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch makes element_id optional (default None) in both django.utils.html.json_script and the defaultfilters wrapper; branches on truthiness to include/omit the id attribute while preserving DjangoJSONEncoder encoding, _json_script_escapes translation, and format_html/mark_safe structure. Requirements 1-3 pin exactly this observable behavior at the correct boundary (both no-id and with-id cases, plus the empty-id edge). No mandated/forbidden behavior diverges from the code.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe only behavior derivable from the public problem_statement (make element_id optional; no id => no id attribute; with id => id attribute; preserve encoding/escaping). No test names, file paths, parametrization ids, or verbatim test/gold code appear. Named identifiers (json_script, element_id, format_html, DjangoJSONEncoder, conditional_escape, strip_tags, urlize) are all pre-existing public API used to localize the change, not fix-invented. Concrete test literals ({}, {'key':'value'}, the escaping fixture string) are NOT reproduced. Req 3.5's enumeration of other html-module functions is a plausible 'don't-regress-the-module' scope statement and does not mirror the PASS_TO_PASS set (it omits escapejs/linebreaks/smart_urlquote which are in PASS_TO_PASS). Behavior is translated into requirements — the legitimate purpose — without transmitting the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
