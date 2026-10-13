# P2 adversarial audit — django__django-16642

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
# Req1 crit1: .br -> application/x-brotli  (POSITIVE CONTROL)
import os, tempfile
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DEFAULT_CHARSET="utf-8")
    django.setup()
from django.http import FileResponse
d = tempfile.mkdtemp()
p = os.path.join(d, "test.html.br")
with open(p, "wb") as f: f.write(b"x")
r = FileResponse(open(p, "rb"))
ct = r.headers["Content-Type"]
print("Content-Type:", ct, "Content-Encoding:", r.headers.get("Content-Encoding"))
assert ct == "application/x-brotli", ct
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1 crit2: .Z -> application/x-compress
import os, tempfile, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DEFAULT_CHARSET="utf-8"); django.setup()
from django.http import FileResponse
d=tempfile.mkdtemp(); p=os.path.join(d,"test.html.Z")
open(p,"wb").write(b"x")
r=FileResponse(open(p,"rb")); ct=r.headers["Content-Type"]
print("Content-Type:",ct)
assert ct=="application/x-compress", ct
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1 crit3+4: .html.br/.html.Z NOT text/html and no Content-Encoding
import os, tempfile, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DEFAULT_CHARSET="utf-8"); django.setup()
from django.http import FileResponse
d=tempfile.mkdtemp()
ok=True
for nm,exp in [("a.html.br","application/x-brotli"),("a.html.Z","application/x-compress")]:
    p=os.path.join(d,nm); open(p,"wb").write(b"x")
    r=FileResponse(open(p,"rb")); ct=r.headers["Content-Type"]; ce=r.headers.get("Content-Encoding")
    print(nm,"->",ct,"CE=",ce)
    if ct=="text/html" or ct!=exp or ce is not None: ok=False
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req2: preserve gzip/bzip2/xz mappings
import os, tempfile, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DEFAULT_CHARSET="utf-8"); django.setup()
from django.http import FileResponse
d=tempfile.mkdtemp(); ok=True
for nm,exp in [("a.html.gz","application/gzip"),("a.html.bz2","application/x-bzip"),("a.html.xz","application/x-xz")]:
    p=os.path.join(d,nm); open(p,"wb").write(b"x")
    r=FileResponse(open(p,"rb")); ct=r.headers["Content-Type"]
    print(nm,"->",ct)
    if ct!=exp: ok=False
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3: plain known type, empty/unknown -> octet-stream, explicit not overridden
import os, tempfile, io, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DEFAULT_CHARSET="utf-8"); django.setup()
from django.http import FileResponse
d=tempfile.mkdtemp(); ok=True
# plain html
p=os.path.join(d,"a.html"); open(p,"wb").write(b"x")
r=FileResponse(open(p,"rb")); print("html->",r.headers["Content-Type"])
if r.headers["Content-Type"]!="text/html": ok=False
# unknown/no name buffer
r2=FileResponse(io.BytesIO(b"x")); print("buffer->",r2.headers["Content-Type"])
if r2.headers["Content-Type"]!="application/octet-stream": ok=False
# explicit content type must not be overridden even for .br
p2=os.path.join(d,"b.html.br"); open(p2,"wb").write(b"x")
r3=FileResponse(open(p2,"rb"), content_type="text/plain"); print("explicit->",r3.headers["Content-Type"])
if r3.headers["Content-Type"]!="text/plain": ok=False
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req4: Content-Length and Content-Disposition preserved for named seekable file
import os, tempfile, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DEFAULT_CHARSET="utf-8"); django.setup()
from django.http import FileResponse
d=tempfile.mkdtemp(); p=os.path.join(d,"a.html.br")
open(p,"wb").write(b"hello world")
r=FileResponse(open(p,"rb"), as_attachment=True)
cl=r.headers.get("Content-Length"); cd=r.headers.get("Content-Disposition")
print("Content-Length:",cl,"Content-Disposition:",cd)
ok = (cl=="11") and (cd is not None and "attachment" in cd and "a.html.br" in cd)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1 crit1: .br -> application/x-brotli  (POSITIVE CONTROL)
import os, tempfile
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DEFAULT_CHARSET="utf-8")
    django.setup()
from django.http import FileResponse
d = tempfile.mkdtemp()
p = os.path.join(d, "test.html.br")
with open(p, "wb") as f: f.write(b"x")
r = FileResponse(open(p, "rb"))
ct = r.headers["Content-Type"]
print("Content-Type:", ct, "Content-Encoding:", r.headers.get("Content-Encoding"))
assert ct == "application/x-brotli", ct
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: FileResponse.set_headers maps compression encodings (mimetypes.guess_type) to compression-specific Content-Type. Gold patch adds 'br'->application/x-brotli and 'compress'->application/x-compress to the existing dict.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1, POSITIVE CONTROL): test.html.br -> application/x-brotli. HOLDS patched; FAILS at base (base gives text/html). Discriminates.
- probe_2 (Req1.2): test.html.Z -> application/x-compress. HOLDS patched; FAILS at base (text/html).
- probe_3 (Req1.3/1.4): .html.br and .html.Z NOT served as text/html and Content-Encoding unset. HOLDS patched.
- probe_4 (Req2): gzip/bzip2/xz mappings preserved (application/gzip, application/x-bzip, application/x-xz). HOLDS.
- probe_5 (Req3): plain a.html->text/html; nameless buffer->application/octet-stream; explicit content_type on a .br file not overridden. HOLDS.
- probe_6 (Req4): named seekable .br file yields Content-Length=11 and Content-Disposition attachment with filename. HOLDS.

Candidate wrong-fix (weak.diff): partial fix adding only 'br' but omitting 'compress'. REJECTED by probe_2 (a.html.Z -> text/html) and probe_3. Demonstrates the suite discriminates an incomplete implementation that a lazy reading of Requirement 1 might permit.

prepatch_reproduced=true (probe_1 exits 1 at base with AssertionError text/html). Verdict SOUND: >=6 distinct probes covering all 4 requirements hold on patched tree, positive control discriminates base vs patched, and a plausibly-wrong partial patch is rejected.

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
# Req1 crit1: .br -> application/x-brotli  (POSITIVE CONTROL)
import os, tempfile
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DEFAULT_CHARSET="utf-8")
    django.setup()
from django.http import FileResponse
d = tempfile.mkdtemp()
p = os.path.join(d, "test.html.br")
with open(p, "wb") as f: f.write(b"x")
r = FileResponse(open(p, "rb"))
ct = r.headers["Content-Type"]
print("Content-Type:", ct, "Content-Encoding:", r.headers.get("Content-Encoding"))
assert ct == "application/x-brotli", ct
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: FileResponse.set_headers maps compression encodings (mimetypes.guess_type) to compression-specific Content-Type. Gold patch adds 'br'->application/x-brotli and 'compress'->application/x-compress to the existing dict.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1, POSITIVE CONTROL): test.html.br -> application/x-brotli. HOLDS patched; FAILS at base (base gives text/html). Discriminates.
- probe_2 (Req1.2): test.html.Z -> application/x-compress. HOLDS patched; FAILS at base (text/html).
- probe_3 (Req1.3/1.4): .html.br and .html.Z NOT served as text/html and Content-Encoding unset. HOLDS patched.
- probe_4 (Req2): gzip/bzip2/xz mappings preserved (application/gzip, application/x-bzip, application/x-xz). HOLDS.
- probe_5 (Req3): plain a.html->text/html; nameless buffer->application/octet-stream; explicit content_type on a .br file not overridden. HOLDS.
- probe_6 (Req4): named seekable .br file yields Content-Length=11 and Content-Disposition attachment with filename. HOLDS.

Candidate wrong-fix (weak.diff): partial fix adding only 'br' but omitting 'compress'. REJECTED by probe_2 (a.html.Z -> text/html) and probe_3. Demonstrates the suite discriminates an incomplete implementation that a lazy reading of Requirement 1 might permit.

prepatch_reproduced=true (probe_1 exits 1 at base with AssertionError text/html). Verdict SOUND: >=6 distinct probes covering all 4 requirements hold on patched tree, positive control discriminates base vs patched, and a plausibly-wrong partial patch is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds exactly two entries to the encoding→content_type dict in FileResponse.set_headers: 'br':'application/x-brotli' and 'compress':'application/x-compress', leaving bzip2/gzip/xz mappings intact and all other header logic (Content-Length, Content-Disposition, explicit content_type) untouched. Requirements pin the changed observable behavior (the mapping outcome for br/compress) biconditionally and correctly scope the preserved behaviors. Modeling boundary is the full changed behavior, not a narrow slice. Probe run on patched tree (HOLDS exit 0) confirmed all mappings; mimetypes.guess_type returns encoding 'br'/'compress' as expected. Faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior, not the hidden tests. The two target encodings (.br, .Z) are already named in the PUBLIC problem_statement (br/Z file types serving as text/html). The output strings application/x-brotli and application/x-compress are the required behavioral outputs — stating expected outputs is legitimate spec translation, not test transmission. The gzip/bzip2/xz mappings (Req 2) are preexisting source behavior in set_headers, publicly visible in the repo, not hidden-test content. No test file path (tests/responses/test_fileresponse.py), no test/class/function names, no parametrization ids, no quoted gold/test code, and no fix-invented identifiers appear. The .html.br/.html.Z examples mirror the public problem_statement's test.html.br/test.html.Z, not the hidden test's .tar.br/.tar.Z fixtures. Naming set_headers/FileResponse/mimetypes.guess_type is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
