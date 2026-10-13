# P2 adversarial audit — django__django-12419

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
"""Positive control + Req2.1: under the built-in default config (no project
override), SecurityMiddleware.process_response attaches
Referrer-Policy: same-origin to a response lacking that header.
Holds on patched (default 'same-origin'); FAILS at base (default None)."""
import django
from django.conf import settings

settings.configure()  # uses global_settings defaults for everything
django.setup()

from django.http import HttpResponse
from django.middleware.security import SecurityMiddleware

mw = SecurityMiddleware(get_response=lambda r: r)
resp = HttpResponse("ok")
mw.process_response(None, resp)
val = resp.get("Referrer-Policy")
print("effective SECURE_REFERRER_POLICY:", repr(settings.SECURE_REFERRER_POLICY))
print("Referrer-Policy header:", repr(val))
assert val == "same-origin", f"expected 'same-origin', got {val!r}"
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1/1.2/1.3: the built-in default value of SECURE_REFERRER_POLICY
(as declared in global_settings, with no project override) SHALL be exactly
the single non-empty string 'same-origin'."""
from django.conf import global_settings

v = global_settings.SECURE_REFERRER_POLICY
print("global_settings.SECURE_REFERRER_POLICY:", repr(v))
assert v == "same-origin", f"expected 'same-origin', got {v!r}"
assert isinstance(v, str) and v.strip() != "", "must be non-empty string"
assert v is not None, "must not be the None/unset choice"
assert "," not in v, "must be a single policy value (no comma)"
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.2: header value carried verbatim (no surrounding whitespace, no extra
tokens) for the default single whitespace-free policy value. And Req2.3:
an existing Referrer-Policy header is left unchanged."""
import django
from django.conf import settings
settings.configure()
django.setup()

from django.http import HttpResponse
from django.middleware.security import SecurityMiddleware

mw = SecurityMiddleware(get_response=lambda r: r)

# verbatim value
resp = HttpResponse("ok")
mw.process_response(None, resp)
val = resp.get("Referrer-Policy")
print("verbatim header:", repr(val))
assert val == "same-origin", f"expected exactly 'same-origin', got {val!r}"
assert val == val.strip(), "no surrounding whitespace allowed"

# existing header preserved (Req2.3)
resp2 = HttpResponse("ok")
resp2["Referrer-Policy"] = "unsafe-url"
mw.process_response(None, resp2)
val2 = resp2.get("Referrer-Policy")
print("existing header after processing:", repr(val2))
assert val2 == "unsafe-url", f"existing header must be unchanged, got {val2!r}"
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req1.4: a project-declared SECURE_REFERRER_POLICY overrides the built-in
default; and Req2.4: when the effective value is None/unset, no
Referrer-Policy header is attached."""
import django
from django.conf import settings
# Project override to a custom value AND we will also test None.
settings.configure(SECURE_REFERRER_POLICY="strict-origin")
django.setup()

from django.http import HttpResponse
from django.middleware.security import SecurityMiddleware

# Req1.4: project override respected
assert settings.SECURE_REFERRER_POLICY == "strict-origin"
mw = SecurityMiddleware(get_response=lambda r: r)
resp = HttpResponse("ok")
mw.process_response(None, resp)
val = resp.get("Referrer-Policy")
print("override header:", repr(val))
assert val == "strict-origin", f"expected 'strict-origin', got {val!r}"

# Req2.4: None => no header. Rebind on the instance to simulate unset policy.
mw.referrer_policy = None
resp2 = HttpResponse("ok")
mw.process_response(None, resp2)
print("has Referrer-Policy when unset:", resp2.has_header("Referrer-Policy"))
assert not resp2.has_header("Referrer-Policy"), "must not attach header when unset"
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2/3.3: the referrer-policy default change is additive only. Under
the default config, the ONLY header added attributable to this change is
Referrer-Policy; all other headers the response would otherwise carry remain
present with their original values, and other security filters are unchanged.

Compare a default-config response to one where SECURE_REFERRER_POLICY is
forced to None (the historical behavior). The two responses must differ ONLY
by the presence of Referrer-Policy: same-origin; every other header must be
byte-identical. Also confirm X-Content-Type-Options (another security filter)
still behaves as before."""
import django
from django.conf import settings
settings.configure()
django.setup()

from django.http import HttpResponse
from django.middleware.security import SecurityMiddleware

def headers_of(referrer_policy):
    mw = SecurityMiddleware(get_response=lambda r: r)
    mw.referrer_policy = referrer_policy  # simulate historical None vs default
    resp = HttpResponse("ok")
    mw.process_response(None, resp)
    return {k: v for k, v in resp.items()}

hist = headers_of(None)                 # pre-change behavior
new = headers_of("same-origin")         # new default behavior

print("historical headers:", hist)
print("new headers:", new)

# Only difference must be the Referrer-Policy header.
added = set(new) - set(hist)
removed = set(hist) - set(new)
changed = {k for k in set(hist) & set(new) if hist[k] != new[k]}
print("added:", added, "removed:", removed, "changed:", changed)
assert added == {"Referrer-Policy"}, f"unexpected additions: {added}"
assert removed == set(), f"unexpected removals: {removed}"
assert changed == set(), f"unexpected value changes: {changed}"
assert new["Referrer-Policy"] == "same-origin"

# Other security filter still present & unchanged (nosniff default True).
assert new.get("X-Content-Type-Options") == "nosniff"
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req2.1: under the built-in default config (no project
override), SecurityMiddleware.process_response attaches
Referrer-Policy: same-origin to a response lacking that header.
Holds on patched (default 'same-origin'); FAILS at base (default None)."""
import django
from django.conf import settings

settings.configure()  # uses global_settings defaults for everything
django.setup()

from django.http import HttpResponse
from django.middleware.security import SecurityMiddleware

mw = SecurityMiddleware(get_response=lambda r: r)
resp = HttpResponse("ok")
mw.process_response(None, resp)
val = resp.get("Referrer-Policy")
print("effective SECURE_REFERRER_POLICY:", repr(settings.SECURE_REFERRER_POLICY))
print("Referrer-Policy header:", repr(val))
assert val == "same-origin", f"expected 'same-origin', got {val!r}"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12419: change SECURE_REFERRER_POLICY built-in default from None to 'same-origin' in global_settings.py. Gold patch is a one-line settings default change; the middleware Referrer-Policy attach logic is unchanged from base.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req2.1, POSITIVE CONTROL): default-config SecurityMiddleware.process_response attaches Referrer-Policy: same-origin. HOLDS patched; FAILS at base (header=None). Discriminates base vs patched.
- probe_2 (Req1.1/1.3): global_settings.SECURE_REFERRER_POLICY == 'same-origin', non-empty single-value string, not None, no comma. HOLDS.
- probe_3 (Req2.2/2.3): header value verbatim 'same-origin' (no whitespace/extra tokens); pre-existing Referrer-Policy header left unchanged. HOLDS.
- probe_4 (Req1.4/2.4): project-declared override respected ('strict-origin'); when effective policy is None, no header attached. HOLDS.
- probe_5 (Req3.1/3.2/3.3): additive-only — vs historical (None) behavior the ONLY header delta is the added Referrer-Policy; all other headers identical; X-Content-Type-Options filter unchanged. HOLDS.

Candidate patch (REQUIRED, exercised): weak_different_policy sets the default to 'strict-origin-when-cross-origin' — a plausibly-'conservative non-empty policy' a weak reading of Req1.3 ('non-empty, not unset') permits, but which violates Req1.1/1.2/2.1/2.2 (must be exactly 'same-origin'). REJECTED by the probe suite: probes 1, 2, 3 all fail under it (they pin exact 'same-origin'); probes 4/5 (which don't pin the default value) pass, as expected. This demonstrates the suite discriminates a wrong-value implementation.

All runs completed in the official image (python3.6/testbed). Verdict SOUND: >=5 distinct probes hold on patched, positive control discriminates (holds patched, fails at base), and >=1 requirements-plausible weak candidate is rejected.

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
"""Positive control + Req2.1: under the built-in default config (no project
override), SecurityMiddleware.process_response attaches
Referrer-Policy: same-origin to a response lacking that header.
Holds on patched (default 'same-origin'); FAILS at base (default None)."""
import django
from django.conf import settings

settings.configure()  # uses global_settings defaults for everything
django.setup()

from django.http import HttpResponse
from django.middleware.security import SecurityMiddleware

mw = SecurityMiddleware(get_response=lambda r: r)
resp = HttpResponse("ok")
mw.process_response(None, resp)
val = resp.get("Referrer-Policy")
print("effective SECURE_REFERRER_POLICY:", repr(settings.SECURE_REFERRER_POLICY))
print("Referrer-Policy header:", repr(val))
assert val == "same-origin", f"expected 'same-origin', got {val!r}"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12419: change SECURE_REFERRER_POLICY built-in default from None to 'same-origin' in global_settings.py. Gold patch is a one-line settings default change; the middleware Referrer-Policy attach logic is unchanged from base.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req2.1, POSITIVE CONTROL): default-config SecurityMiddleware.process_response attaches Referrer-Policy: same-origin. HOLDS patched; FAILS at base (header=None). Discriminates base vs patched.
- probe_2 (Req1.1/1.3): global_settings.SECURE_REFERRER_POLICY == 'same-origin', non-empty single-value string, not None, no comma. HOLDS.
- probe_3 (Req2.2/2.3): header value verbatim 'same-origin' (no whitespace/extra tokens); pre-existing Referrer-Policy header left unchanged. HOLDS.
- probe_4 (Req1.4/2.4): project-declared override respected ('strict-origin'); when effective policy is None, no header attached. HOLDS.
- probe_5 (Req3.1/3.2/3.3): additive-only — vs historical (None) behavior the ONLY header delta is the added Referrer-Policy; all other headers identical; X-Content-Type-Options filter unchanged. HOLDS.

Candidate patch (REQUIRED, exercised): weak_different_policy sets the default to 'strict-origin-when-cross-origin' — a plausibly-'conservative non-empty policy' a weak reading of Req1.3 ('non-empty, not unset') permits, but which violates Req1.1/1.2/2.1/2.2 (must be exactly 'same-origin'). REJECTED by the probe suite: probes 1, 2, 3 all fail under it (they pin exact 'same-origin'); probes 4/5 (which don't pin the default value) pass, as expected. This demonstrates the suite discriminates a wrong-value implementation.

All runs completed in the official image (python3.6/testbed). Verdict SOUND: >=5 distinct probes hold on patched, positive control discriminates (holds patched, fails at base), and >=1 requirements-plausible weak candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes exactly one line: SECURE_REFERRER_POLICY = None -> 'same-origin' in django/conf/global_settings.py. The requirements pin (a) the setting default, (b) the observable Referrer-Policy header via SecurityMiddleware.process_response, and (c) additivity. The modeling boundary is the changed observable behavior (header emission under default config), not a narrow slice. R2.2's verbatim/whitespace-free claim is consistent with the middleware's split/strip/join on a single whitespace-free value. Test_patch corroborates: middleware_headers now expects b'Referrer-Policy: same-origin'. No invented, mandated-but-absent, or forbidden-but-present behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit (SECURE_REFERRER_POLICY None->'same-origin') and the target value 'same-origin' are fully public in the problem_statement, which explicitly proposes changing the default to 'same-origin'. The requirements localize the change to global_settings.py and SecurityMiddleware.process_response (legitimate module naming) and translate behavior into EARS criteria. No test names/paths (project_template.test_settings.TestStartProjectSettings / test_middleware_headers), no quoted test code, no fix-invented identifiers. Crucially, the hidden test enumerates a specific ordered header list (Content-Length, Content-Type, Referrer-Policy, X-Content-Type-Options, X-Frame-Options); the requirements do NOT reproduce this enumeration — Req 3 speaks abstractly of 'every header the response would otherwise carry' without listing the concrete other headers or their order. Thus no test-shaped case enumeration reconstructs the hidden test.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
