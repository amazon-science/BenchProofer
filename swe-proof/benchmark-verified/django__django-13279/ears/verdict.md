# P2 adversarial audit — django__django-13279

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
# Req 1.1 / 1.2 (positive control): under DEFAULT_HASHING_ALGORITHM=='sha1',
# encode() returns pre-3.1 legacy format = b64(hash + b':' + serialized),
# using the same serializer & _hash the legacy read path expects.
import sys, base64, django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='k'*50, DEFAULT_HASHING_ALGORITHM='sha1',
    INSTALLED_APPS=['django.contrib.sessions'], DATABASES={}, USE_TZ=False)
django.setup()
from django.contrib.sessions.backends.base import SessionBase

s = SessionBase()
d = {'user_id': 42, 'foo': 'bar'}
enc = s.encode(d)
print('encoded:', enc)

# Must NOT be the signing-based format (which contains a ':' at top level and
# starts with a version/compression marker after b64). Verify legacy structure:
try:
    raw = base64.b64decode(enc.encode('ascii'))
except Exception as e:
    print('FAIL: not base64:', e); sys.exit(1)

if b':' not in raw:
    print('FAIL: no ":" separator in decoded payload'); sys.exit(1)

expected_hash, serialized = raw.split(b':', 1)
computed = s._hash(serialized)
print('stored hash :', expected_hash.decode())
print('computed    :', computed)
if expected_hash.decode() != computed:
    print('FAIL: hash does not match _hash(serialized)'); sys.exit(1)

# serialized must be the serializer's dump of the dict
if s.serializer().loads(serialized) != d:
    print('FAIL: serialized payload does not round-trip via serializer'); sys.exit(1)

# And it must NOT equal the signing.dumps format (top-level, non-legacy)
from django.core import signing
signed = signing.dumps(d, salt=s.key_salt, serializer=s.serializer, compress=True)
if enc == signed:
    print('FAIL: encode produced signing-based format, not legacy'); sys.exit(1)

print('PASS: legacy interchange format produced under sha1')
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.3 / 1.4: encode under sha1, decode() via pre-3.1 fallback yields original dict.
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='k'*50, DEFAULT_HASHING_ALGORITHM='sha1',
    INSTALLED_APPS=['django.contrib.sessions'], DATABASES={}, USE_TZ=False)
django.setup()
from django.contrib.sessions.backends.base import SessionBase

s = SessionBase()
for d in [{}, {'x': 1}, {'user_id': 7, 'nested': {'a': [1, 2, 3]}, 's': 'unicode-é'}]:
    enc = s.encode(d)
    dec = s.decode(enc)
    print('orig:', d, '-> dec:', dec)
    if dec != d:
        print('FAIL: decode(encode(d)) != d'); sys.exit(1)
    # Also confirm the legacy read path itself accepts it directly.
    if s._legacy_decode(enc) != d:
        print('FAIL: _legacy_decode(encode(d)) != d'); sys.exit(1)
print('PASS: sha1 encode round-trips through decode and legacy path')
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1 / 2.3: under non-legacy algorithm, encode() returns current signing-based
# format (== signing.dumps), and decode round-trips.
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='k'*50, DEFAULT_HASHING_ALGORITHM='sha256',
    INSTALLED_APPS=['django.contrib.sessions'], DATABASES={}, USE_TZ=False)
django.setup()
from django.contrib.sessions.backends.base import SessionBase
from django.core import signing

s = SessionBase()
d = {'user_id': 99, 'k': 'v'}
enc = s.encode(d)
print('encoded:', enc)

# It must be a signing-based value: signing.loads must accept it directly.
loaded = signing.loads(enc, salt=s.key_salt, serializer=s.serializer)
if loaded != d:
    print('FAIL: signing.loads did not recover dict'); sys.exit(1)

# And it must NOT be legacy format: legacy decode of a signing value should not
# silently equal d (it should fail to authenticate -> {}).
if s.decode(enc) != d:
    print('FAIL: decode did not round-trip'); sys.exit(1)

# Structural: signing format contains a top-level ':' separator and is not the
# b64(hash:serialized) shape. Confirm encode == signing.dumps output shape by
# checking it parses as signing (already done) — the discriminator is probe_5.
print('PASS: non-legacy uses signing-based format and round-trips')
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.1 / 3.2 / 3.3: decode() reads BOTH current signing format and pre-3.1 legacy
# format; and returns {} (not raise) on garbage/tampered data.
import sys, base64, django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='k'*50, DEFAULT_HASHING_ALGORITHM='sha256',
    INSTALLED_APPS=['django.contrib.sessions'], DATABASES={}, USE_TZ=False)
django.setup()
from django.contrib.sessions.backends.base import SessionBase
from django.core import signing

s = SessionBase()
d = {'user_id': 5, 'v': [1, 2]}

# 3.1 current signing format
signed = signing.dumps(d, salt=s.key_salt, serializer=s.serializer, compress=True)
if s.decode(signed) != d:
    print('FAIL: decode of signing format'); sys.exit(1)

# 3.2 legacy format built by hand (independent of encode)
serialized = s.serializer().dumps(d)
h = s._hash(serialized)
legacy = base64.b64encode(h.encode() + b':' + serialized).decode('ascii')
if s.decode(legacy) != d:
    print('FAIL: decode of legacy format'); sys.exit(1)

# 3.3 garbage -> {} without raising
for bad in ['not-valid!!!', '', base64.b64encode(b'zzzz:garbage').decode('ascii')]:
    try:
        r = s.decode(bad)
    except Exception as e:
        print('FAIL: decode raised on garbage:', repr(bad), e); sys.exit(1)
    if r != {}:
        print('FAIL: garbage did not decode to {}:', repr(bad), r); sys.exit(1)

print('PASS: decode reads both formats and tolerates garbage')
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.5 / 1.2: legacy encoding is identical regardless of backend, and is
# byte-identical to the independent pre-3.1 construction (interchangeability:
# an old-code instance must be able to read it). This is the discriminating probe.
import sys, base64, django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='k'*50, DEFAULT_HASHING_ALGORITHM='sha1',
    INSTALLED_APPS=['django.contrib.sessions'], DATABASES={}, USE_TZ=False)
django.setup()

from django.contrib.sessions.backends.base import SessionBase
from django.contrib.sessions.backends.cache import SessionStore as CacheStore
from django.contrib.sessions.backends.signed_cookies import SessionStore as CookieStore

d = {'user_id': 321, 'msg': 'hello'}

def independent_legacy(store):
    # Reconstruct what a pre-3.1 instance would write for this class.
    serialized = store.serializer().dumps(d)
    h = store._hash(serialized)
    return base64.b64encode(h.encode() + b':' + serialized).decode('ascii')

for cls in (SessionBase, CacheStore, CookieStore):
    store = cls()
    enc = store.encode(d)
    expected = independent_legacy(store)
    print(cls.__name__, 'enc==independent-legacy:', enc == expected)
    if enc != expected:
        print('FAIL:', cls.__name__, 'encode is not the pre-3.1 interchange bytes')
        print('  got     :', enc)
        print('  expected:', expected)
        sys.exit(1)
    # And an independent legacy reader recovers d
    raw = base64.b64decode(enc.encode('ascii'))
    stored_hash, serialized = raw.split(b':', 1)
    if store._hash(serialized) != stored_hash.decode():
        print('FAIL: hash mismatch for', cls.__name__); sys.exit(1)
    if store.serializer().loads(serialized) != d:
        print('FAIL: payload mismatch for', cls.__name__); sys.exit(1)

print('PASS: legacy encode is backend-independent, interchange-format bytes')
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1 / 1.2 (positive control): under DEFAULT_HASHING_ALGORITHM=='sha1',
# encode() returns pre-3.1 legacy format = b64(hash + b':' + serialized),
# using the same serializer & _hash the legacy read path expects.
import sys, base64, django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='k'*50, DEFAULT_HASHING_ALGORITHM='sha1',
    INSTALLED_APPS=['django.contrib.sessions'], DATABASES={}, USE_TZ=False)
django.setup()
from django.contrib.sessions.backends.base import SessionBase

s = SessionBase()
d = {'user_id': 42, 'foo': 'bar'}
enc = s.encode(d)
print('encoded:', enc)

# Must NOT be the signing-based format (which contains a ':' at top level and
# starts with a version/compression marker after b64). Verify legacy structure:
try:
    raw = base64.b64decode(enc.encode('ascii'))
except Exception as e:
    print('FAIL: not base64:', e); sys.exit(1)

if b':' not in raw:
    print('FAIL: no ":" separator in decoded payload'); sys.exit(1)

expected_hash, serialized = raw.split(b':', 1)
computed = s._hash(serialized)
print('stored hash :', expected_hash.decode())
print('computed    :', computed)
if expected_hash.decode() != computed:
    print('FAIL: hash does not match _hash(serialized)'); sys.exit(1)

# serialized must be the serializer's dump of the dict
if s.serializer().loads(serialized) != d:
    print('FAIL: serialized payload does not round-trip via serializer'); sys.exit(1)

# And it must NOT equal the signing.dumps format (top-level, non-legacy)
from django.core import signing
signed = signing.dumps(d, salt=s.key_salt, serializer=s.serializer, compress=True)
if enc == signed:
    print('FAIL: encode produced signing-based format, not legacy'); sys.exit(1)

print('PASS: legacy interchange format produced under sha1')
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13279: encode() must produce the pre-3.1 legacy interchange format when DEFAULT_HASHING_ALGORITHM=='sha1'.

Probes (all run in the official image):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): under sha1, encode() output is b64(hash + b':' + serialized), hash==_hash(serialized), serializer round-trips, and NOT signing.dumps. PATCHED: HOLDS. BASE: FAIL (encode gives signing format, not base64/no ':'). Discriminates.
- probe_2 (Req 1.3/1.4): encode(sha1) round-trips through both decode() and _legacy_decode() for {}, simple, and nested/unicode dicts. PATCHED: HOLDS. BASE: FAIL.
- probe_3 (Req 2.1/2.3): under non-legacy (sha256) encode() is signing-based (signing.loads recovers dict) and round-trips. HOLDS on both trees (regression check).
- probe_4 (Req 3.1/3.2/3.3): decode() reads current signing format AND a hand-built legacy value, and returns {} without raising on garbage/tampered input. HOLDS on both trees (regression check).
- probe_5 (Req 1.2/3.5, DISCRIMINATOR): legacy encode is byte-identical to an independent pre-3.1 reconstruction across SessionBase, CacheStore, CookieStore (backend-independent interchange bytes). PATCHED: HOLDS. BASE: FAIL.

Positive control (probe_1) FAILS at base and HOLDS patched => prepatch_reproduced=true. probes 2 and 5 also discriminate.

Wrong-fix candidate weak.diff (guards on sha1 but returns base64 of the serialized payload with NO MAC hash — the lazy fix a weak reading permits): applies at base_commit; REJECTED by probes 1, 2, and 5 (missing hash / broken round-trip / wrong bytes). This demonstrates the suite discriminates requirement-conforming-looking but wrong implementations. No requirement-conforming candidate that survives the suite was found, so no TOO-WEAK finding.

All 5 probes hold on the gold-patched tree; positive control discriminates; a plausible wrong fix is rejected. Verdict SOUND.

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
# Req 1.1 / 1.2 (positive control): under DEFAULT_HASHING_ALGORITHM=='sha1',
# encode() returns pre-3.1 legacy format = b64(hash + b':' + serialized),
# using the same serializer & _hash the legacy read path expects.
import sys, base64, django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='k'*50, DEFAULT_HASHING_ALGORITHM='sha1',
    INSTALLED_APPS=['django.contrib.sessions'], DATABASES={}, USE_TZ=False)
django.setup()
from django.contrib.sessions.backends.base import SessionBase

s = SessionBase()
d = {'user_id': 42, 'foo': 'bar'}
enc = s.encode(d)
print('encoded:', enc)

# Must NOT be the signing-based format (which contains a ':' at top level and
# starts with a version/compression marker after b64). Verify legacy structure:
try:
    raw = base64.b64decode(enc.encode('ascii'))
except Exception as e:
    print('FAIL: not base64:', e); sys.exit(1)

if b':' not in raw:
    print('FAIL: no ":" separator in decoded payload'); sys.exit(1)

expected_hash, serialized = raw.split(b':', 1)
computed = s._hash(serialized)
print('stored hash :', expected_hash.decode())
print('computed    :', computed)
if expected_hash.decode() != computed:
    print('FAIL: hash does not match _hash(serialized)'); sys.exit(1)

# serialized must be the serializer's dump of the dict
if s.serializer().loads(serialized) != d:
    print('FAIL: serialized payload does not round-trip via serializer'); sys.exit(1)

# And it must NOT equal the signing.dumps format (top-level, non-legacy)
from django.core import signing
signed = signing.dumps(d, salt=s.key_salt, serializer=s.serializer, compress=True)
if enc == signed:
    print('FAIL: encode produced signing-based format, not legacy'); sys.exit(1)

print('PASS: legacy interchange format produced under sha1')
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13279: encode() must produce the pre-3.1 legacy interchange format when DEFAULT_HASHING_ALGORITHM=='sha1'.

Probes (all run in the official image):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): under sha1, encode() output is b64(hash + b':' + serialized), hash==_hash(serialized), serializer round-trips, and NOT signing.dumps. PATCHED: HOLDS. BASE: FAIL (encode gives signing format, not base64/no ':'). Discriminates.
- probe_2 (Req 1.3/1.4): encode(sha1) round-trips through both decode() and _legacy_decode() for {}, simple, and nested/unicode dicts. PATCHED: HOLDS. BASE: FAIL.
- probe_3 (Req 2.1/2.3): under non-legacy (sha256) encode() is signing-based (signing.loads recovers dict) and round-trips. HOLDS on both trees (regression check).
- probe_4 (Req 3.1/3.2/3.3): decode() reads current signing format AND a hand-built legacy value, and returns {} without raising on garbage/tampered input. HOLDS on both trees (regression check).
- probe_5 (Req 1.2/3.5, DISCRIMINATOR): legacy encode is byte-identical to an independent pre-3.1 reconstruction across SessionBase, CacheStore, CookieStore (backend-independent interchange bytes). PATCHED: HOLDS. BASE: FAIL.

Positive control (probe_1) FAILS at base and HOLDS patched => prepatch_reproduced=true. probes 2 and 5 also discriminate.

Wrong-fix candidate weak.diff (guards on sha1 but returns base64 of the serialized payload with NO MAC hash — the lazy fix a weak reading permits): applies at base_commit; REJECTED by probes 1, 2, and 5 (missing hash / broken round-trip / wrong bytes). This demonstrates the suite discriminates requirement-conforming-looking but wrong implementations. No requirement-conforming candidate that survives the suite was found, so no TOO-WEAK finding.

All 5 probes hold on the gold-patched tree; positive control discriminates; a plausible wrong fix is rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `if settings.DEFAULT_HASHING_ALGORITHM == 'sha1': return self._legacy_encode(...)` to encode() plus the _legacy_encode helper. Req 1.1 pins the exact switch condition ('sha1'), Req 1.2 exactly describes _legacy_encode (base64(hash.encode()+b':'+serialized)), Req 2 pins the non-legacy signing branch and that format choice depends solely on the setting, Req 3 covers the preserved dual-path decode()/_legacy_decode() fallback and empty-dict-on-failure. Modeling boundary is the changed observable encode() behavior, not a narrow slice. Probe confirmed sha1 roundtrip, sha256 roundtrip, and legacy≠signing on patched; base fails (Incorrect padding = signing output) as expected.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Document names only pre-existing public identifiers (SessionBase.encode/decode, _legacy_decode, DEFAULT_HASHING_ALGORITHM='sha1') — all present in the codebase or the problem_statement. The fix-invented helper _legacy_encode is NOT disclosed. Req 1.2's byte-layout of the legacy format (base64(hash + ':' + serialized)) matches the gold body but is fully derivable from the already-existing public _legacy_decode() (the pre-3.1 read path), so it's legitimate behavioral spec, not gold-transmission. Req 3.4's backend list (cookie/cache/cache+db/file/database/custom-db/time-zone) tracks PASS_TO_PASS test classes but these are Django's standard public session backends — localization, not parametrization reconstruction. No test names/paths/ids, no quoted test code, no test-shaped case enumeration mirroring the single FAIL_TO_PASS test.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
