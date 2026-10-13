# P2 adversarial audit — django__django-11133

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
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")
from django.http import HttpResponse

# Req1.1 + positive control: memoryview at construction -> exact underlying bytes
raw = b"binary\x00\xff data"
mv = memoryview(raw)
r = HttpResponse(content=mv)
print("content:", repr(r.content))
print("expected:", repr(raw))
ok = (r.content == raw) and type(r.content) is bytes
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")
from django.http import HttpResponse

# Req1.2: memoryview assigned to .content property -> exact underlying bytes
raw = b"\x01\x02\x03payload\xfe"
r = HttpResponse()
r.content = memoryview(raw)
print("content:", repr(r.content))
print("expected:", repr(raw))
ok = (r.content == raw) and type(r.content) is bytes
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")
from django.http import HttpResponse

# Req1.3: memoryview body must NOT be rendered as its repr text
raw = b"hello-bytes"
mv = memoryview(raw)
reprtext = repr(mv)  # e.g. "<memory at 0x...>"
r = HttpResponse(content=mv)
print("content:", repr(r.content))
print("memoryview repr:", reprtext)
# content must not contain the '<memory at' repr text
ok = (b"<memory at" not in r.content) and (r.content == raw)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")
from django.http import HttpResponse
from django.http.response import HttpResponseBase

# Req1.4: make_bytes on a memoryview returns a bytes instance holding those bytes
raw = b"low\x00level\xaa"
r = HttpResponseBase()
out = r.make_bytes(memoryview(raw))
print("make_bytes out:", repr(out), "type:", type(out).__name__)
ok = (type(out) is bytes) and (out == raw)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")
from django.http import HttpResponse

# Req2: regressions preserved for bytes, str, int, iterable, non-default charset
fails = []

# 2.1 bytes unchanged
r = HttpResponse(content=b"raw-bytes")
if not (r.content == b"raw-bytes" and type(r.content) is bytes):
    fails.append(("bytes", r.content))

# 2.2 str encoded utf-8 default
r = HttpResponse(content="héllo")
if r.content != "héllo".encode("utf-8"):
    fails.append(("str-utf8", r.content))

# 2.4 int -> textual repr encoded
r = HttpResponse(content=12345)
if r.content != b"12345":
    fails.append(("int", r.content))

# 2.5 iterable concatenated in order
r = HttpResponse(content=[b"a", "b", 3])
if r.content != b"ab3":
    fails.append(("iterable", r.content))

# 2.6 always bytes
r = HttpResponse(content="x")
if type(r.content) is not bytes:
    fails.append(("type", type(r.content).__name__))

print("failures:", fails)
sys.exit(0 if not fails else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")
from django.http import HttpResponse
from django.http.response import HttpResponseBase

# Req2.3: non-default charset applied to str body via make_bytes
r = HttpResponseBase()
r._charset = "latin-1"
s = "café"
out = r.make_bytes(s)
print("latin-1 encode:", repr(out), "expected:", repr(s.encode("latin-1")))
ok = out == s.encode("latin-1")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")
from django.http import HttpResponse

# Req1.1 + positive control: memoryview at construction -> exact underlying bytes
raw = b"binary\x00\xff data"
mv = memoryview(raw)
r = HttpResponse(content=mv)
print("content:", repr(r.content))
print("expected:", repr(raw))
ok = (r.content == raw) and type(r.content) is bytes
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11133: make HttpResponse.make_bytes treat memoryview as byte-like. Gold patch changes `isinstance(value, bytes)` to `isinstance(value, (bytes, memoryview))` (branch returns bytes(value)).

Probes (all HOLD on gold-patched tree; requirement mapping):
- probe_1 (Req1.1, POSITIVE CONTROL): HttpResponse(content=memoryview(raw)).content == raw and is bytes. Patched: HOLDS (b'binary\x00\xff data'). Base: VIOLATED (content = b'<memory at 0x...>'). Discriminates.
- probe_2 (Req1.2): assign memoryview to .content property -> exact bytes. HOLDS.
- probe_3 (Req1.3): content must NOT contain '<memory at' repr text. HOLDS.
- probe_4 (Req1.4): make_bytes(memoryview) returns a `bytes` instance (type is bytes), not a memoryview. HOLDS on gold.
- probe_5 (Req2.1/2.2/2.4/2.5/2.6 regressions): bytes unchanged, str utf-8, int repr, iterable [b'a','b',3]->b'ab3', always bytes. HOLDS.
- probe_6 (Req2.3): non-default charset (latin-1) applied to str body. HOLDS.

Candidate wrong-fix (weak.diff): `if isinstance(value, memoryview): return value` (returns the memoryview object unchanged instead of bytes(value)). This satisfies content byte-equality (probes 1,2,3 HOLD because response content assembly bytes-ifies via b''.join) but VIOLATES Req1.4 which mandates make_bytes return a `bytes` instance. probe_4 REJECTS it (make_bytes out type: memoryview). This demonstrates the suite discriminates a plausibly-wrong reading of the requirements that omits the bytes() conversion.

All 6 probes hold on the gold-patched tree; positive control fails at base; the wrong-fix candidate is rejected by probe_4. Requirements are faithful and discriminating.

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
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")
from django.http import HttpResponse

# Req1.1 + positive control: memoryview at construction -> exact underlying bytes
raw = b"binary\x00\xff data"
mv = memoryview(raw)
r = HttpResponse(content=mv)
print("content:", repr(r.content))
print("expected:", repr(raw))
ok = (r.content == raw) and type(r.content) is bytes
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11133: make HttpResponse.make_bytes treat memoryview as byte-like. Gold patch changes `isinstance(value, bytes)` to `isinstance(value, (bytes, memoryview))` (branch returns bytes(value)).

Probes (all HOLD on gold-patched tree; requirement mapping):
- probe_1 (Req1.1, POSITIVE CONTROL): HttpResponse(content=memoryview(raw)).content == raw and is bytes. Patched: HOLDS (b'binary\x00\xff data'). Base: VIOLATED (content = b'<memory at 0x...>'). Discriminates.
- probe_2 (Req1.2): assign memoryview to .content property -> exact bytes. HOLDS.
- probe_3 (Req1.3): content must NOT contain '<memory at' repr text. HOLDS.
- probe_4 (Req1.4): make_bytes(memoryview) returns a `bytes` instance (type is bytes), not a memoryview. HOLDS on gold.
- probe_5 (Req2.1/2.2/2.4/2.5/2.6 regressions): bytes unchanged, str utf-8, int repr, iterable [b'a','b',3]->b'ab3', always bytes. HOLDS.
- probe_6 (Req2.3): non-default charset (latin-1) applied to str body. HOLDS.

Candidate wrong-fix (weak.diff): `if isinstance(value, memoryview): return value` (returns the memoryview object unchanged instead of bytes(value)). This satisfies content byte-equality (probes 1,2,3 HOLD because response content assembly bytes-ifies via b''.join) but VIOLATES Req1.4 which mandates make_bytes return a `bytes` instance. probe_4 REJECTS it (make_bytes out type: memoryview). This demonstrates the suite discriminates a plausibly-wrong reading of the requirements that omits the bytes() conversion.

All 6 probes hold on the gold-patched tree; positive control fails at base; the wrong-fix candidate is rejected by probe_4. Requirements are faithful and discriminating.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the observable behavior (HttpResponse.content through both construction and property assignment) rather than a narrow internal slice, correctly matching the make_bytes change. Boundary is right. Probe HOLDS on gold-patched (exit 0), and base yields the repr string confirming the twin fails.

Counterexample / evidence:

```
On base (unpatched), HttpResponse(memoryview(b'binary')).content == b'<memory at 0x...>' (repr fallback); on gold-patched it == b'binary'. This is the behavior the requirements pin, and it is exactly what the patch produces — no disagreement between requirements and patched code.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the PUBLIC problem_statement, which already demonstrates str/bytes/memoryview coercion with HttpResponse and shows the buggy repr output (b'<memory at 0x...>'). Localizing to HttpResponseBase.make_bytes in django/http/response.py is legitimate change-localization; make_bytes is the natural named routine, not a fix-invented identifier (the gold patch invents nothing new — it merely extends an isinstance tuple). No test names, paths, ids, or quoted test/gold code appear. Req 2's enumeration of preserved types (bytes, str, integer, iterable) mirrors general coercion behavior; the integer/iterable cases loosely correspond to existing PASS_TO_PASS tests (test_non_string_content, test_iter_content) but are described as behavioral invariants ('preserve existing coercion'), not as specific literal cases (no b'12345', no ['abc','def','ghi'], no test names). Req 1.4's 'return a bytes instance' reflects natural behavior (matches hints_text's public suggestion to cast memoryview to bytes) rather than transmitting the hidden test. This is faithful behavioral translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
