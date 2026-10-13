# mapping.md — django__django-13279

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6e9c5ee88fc948e05b4a7d9f82a8861ed2b0343d`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/contrib/sessions/backends/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serialize(payload, algorithm)` | `SessionBase.encode(self, session_dict)` — `django/contrib/sessions/backends/base.py:109` | the modeled changed function (the serializer that gained a regime branch) |
| `algorithm` parameter | `settings.DEFAULT_HASHING_ALGORITHM` — read inside `encode` post-patch (`base.py:111-112`); global default `django/conf/global_settings.py:443` (`'sha256'`) | the compatibility-regime selector; `'sha1'` ↔ `ALGO_LEGACY`, anything else (the `'sha256'` default) ↔ `ALGO_MODERN` |
| `legacy_serialize` (inlined in `serialize`'s legacy branch; deep model) | `SessionBase._legacy_encode(self, session_dict)` — added by the patch at `base.py` (`serialized = serializer().dumps(...)`, `hash = self._hash(serialized)`, `b64encode(hash.encode()+b':'+serialized)`) | deep model of the legacy frame builder |
| `legacy_read(tag, mac, payload)` (deep model) | `SessionBase._legacy_decode(self, session_data)` — `base.py:124-141` (`b64decode`, `split(b':',1)`, `constant_time_compare(hash, self._hash(serialized))`, else `{}`) | deep model of the legacy reader (the round-trip target of the F2P test) |
| `keyed_digest(payload)` *(axiom — A-consumed)* | `SessionBase._hash(value)` → `salted_hmac(key_salt, value).hexdigest()` — `base.py:104-107`; `salted_hmac` `django/utils/crypto.py` | unchanged keyed-MAC hex digest used by both legacy encode and legacy decode |
| `modern_digest(payload)` *(axiom — A-consumed)* | the keyed signature `signing.dumps`/`signing.loads` compute over the carried payload (`django/core/signing.py` `Signer.signature` → `salted_hmac(...)`) | unchanged modern keyed signature; a pure deterministic function of the carried payload (the timestamp component is folded into the invertible frame wrapper, mapping.md §2) |
| `modern_serialize(payload)` *(axiom — A-consumed)* | `signing.dumps(session_dict, salt=..., serializer=..., compress=True)` — `base.py:111-114`; `django/core/signing.py:93` | unchanged modern signed serializer; its output is a modern frame (NOT a legacy frame) carrying exactly the given payload plus that payload's modern signature, so `signing.loads` (the modern reader) recovers exactly the record |
| `modern_read(tag, mac, payload)` (deep model) | `signing.loads(session_data, salt=..., serializer=...)` — `django/core/signing.py:106`; the accepting arm of `SessionBase.decode` (`base.py:117-121`) | deep model of the modern reader: accepts a modern frame whose carried signature matches the freshly recomputed modern signature of the payload and returns the payload, else the empty record (the round-trip target of the P2P modern-regime session tests) |
| `Frame{tag,mac,payload}` | the transportable string produced by `encode` and consumed by `_legacy_decode` | minimal carrier object: which frame format, the carried hash field, the serialized payload |

The pre-patch behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view): `encode` (`base.py:109-114`)
unconditionally `return signing.dumps(...)` — it never consulted the regime
selector, so under the legacy regime it emitted a modern frame that
`_legacy_decode` cannot read back.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `session_dict` (a small `dict`) serialized by `self.serializer().dumps(...)` to `bytes` | `List[int]` of the serialized payload octets (`payload`), specified over `PSeq[int]` via `ToSeq` | the unchanged serializer round trip `serializer().loads(serializer().dumps(d)) == d` is an invertible identity layer folded into the payload carrier (it is not the changed operation); the F2P round trip on the record holds iff the round trip on the serialized payload holds |
| `settings.DEFAULT_HASHING_ALGORITHM` (a `str`, `'sha1'` or `'sha256'`) | `int` selector `algorithm` | `'sha1'` ↔ `ALGO_LEGACY (0)`; every other value (default `'sha256'`) ↔ `ALGO_MODERN (1)` (the `!= ALGO_LEGACY` branch) |
| the transportable encoded `str` (`base64`-wrapped frame) | `Frame{tag, mac, payload}` | `base64`/`.decode('ascii')` is an invertible wrapper (b64decode∘b64encode = identity) folded out; `tag` abstracts "is this the legacy frame format the legacy reader accepts"; `mac` ↔ the leading hex `hash` field; `payload` ↔ the trailing `serialized` octets after the `b':'` separator |
| the `hash.encode() + b':' + serialized` framing | `Frame(FMT_LEGACY, keyed_digest(payload), payload)` | the leading hex hash carries no `b':'`, so `split(b':', 1)` recovers exactly `(hash, serialized)`; abstracted to the structured `Frame` fields (no byte-level split needed) |
| `constant_time_compare(hash.decode(), self._hash(serialized))` | `mac == keyed_digest(payload)` | constant-time vs. plain equality is observationally the same boolean; both compare the carried digest to the recomputed digest |
| empty session `{}` returned on a failed legacy decode | `empty_payload()` (the empty `PSeq[int]`) | a failed legacy read yields the empty record |

`bytes`/`str` indexing is banned in Nagini, so payloads are `List[int]` /
`PSeq[int]`; the byte-level `split`/`base64` plumbing is an invertible wrapper
abstracted by the `Frame` fields.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `keyed_digest` ↔ `SessionBase._hash` / `salted_hmac().hexdigest()` (A-consumed)
**Callee:** `_hash(value)` (`base.py:104-107`) returns
`salted_hmac(key_salt, value).hexdigest()` — a salted keyed-HMAC hex digest.
The proof consumes exactly one property of it: it is a **deterministic function
of its argument** (equal payloads yield equal digests), which Nagini derives
from `@Pure`. This is precisely the property that makes the legacy round trip
close: the digest carried in the legacy frame (`keyed_digest(payload)`) equals
the digest the legacy reader recomputes (`keyed_digest(payload)`), so the
constant-time comparison succeeds and the payload is returned. The axiom is the
**weakest** sufficient contract (`Ensures(True)`; determinism is implicit in
`@Pure`), not the full HMAC definition.

A second relied-on fact — the hex digest contains no `b':'` separator byte, so
`split(b':', 1)` cleanly recovers `(hash, serialized)` — is handled in the model
by the structured `Frame` carrier (no byte-level split), and is recorded here for
the G-AX check (`hexdigest()` is `[0-9a-f]*`, which never contains `:` = 0x3A).

### 3.2 `modern_serialize` ↔ `signing.dumps` (A-consumed) and `modern_digest` ↔ the modern signature
**Callee:** `signing.dumps(session_dict, salt=self.key_salt,
serializer=self.serializer, compress=True)` (`base.py:111-114`;
`django/core/signing.py:93`). The proof consumes three facts:

  1. its output is a **modern frame, not a legacy frame** — i.e.
     `modern_serialize(p).tag == FMT_MODERN`, so the legacy reader
     (`legacy_read`) does not accept it and yields the empty record. This is the
     real observed behaviour: a modern signed string fed to `_legacy_decode`
     fails the `constant_time_compare(hash, self._hash(...))` check (its
     structure/embedded signature does not match a freshly recomputed `_hash` of
     the split payload) and returns `{}` — exactly what the pre-patch bug
     exhibited under the legacy regime;
  2. the modern frame **carries exactly the given payload**
     (`modern_serialize(p).payload == p`) — `signing.dumps` signs and transports
     the record it was handed, not some other record; and
  3. the carried signature is the payload's own modern signature
     (`modern_serialize(p).mac == modern_digest(p)`), where `modern_digest` ↔
     the keyed signature `signing.dumps`/`signing.loads` compute over the
     transported payload (`django/core/signing.py`, `Signer.signature` via
     `salted_hmac`); like `keyed_digest` it is consumed only as a pure
     deterministic function of its argument (`Ensures(True)` + `@Pure`).

Facts 2–3 are what close the modern-regime round trip
`modern_read(modern_serialize(p)) == p` ↔ the real
`signing.loads(signing.dumps(d)) == d` that the unchanged `decode` performs on
every modern session (the P2P `test_decode`/`test_cycle` observable). The axiom
still claims no byte-level internal structure of `signing.dumps` (base64,
compression flag, timestamp are folded into the invertible wrapper, §2).

**Soundness check (G-AX):** `axiom_check.py` runs the REAL Django callees in a
configured environment:
  - For `modern_serialize`: builds a real `SessionBase`-style encode via
    `signing.dumps(...)` and asserts `_legacy_decode(that) == {}` for a range of
    record payloads (so feeding a modern frame to the legacy reader yields the
    empty record — the modern-tag fact), AND asserts the modern round trip
    `signing.loads(signing.dumps(data)) == data` (the carried-payload +
    matching-signature facts, i.e. `modern_read(modern_serialize(p)) == p`).
  - For `keyed_digest`: asserts `_hash` is deterministic and that
    `_hash(serialized)` never contains `':'`.
  - For the legacy round trip (the deep model, §below): asserts
    `_legacy_decode(_legacy_encode(data)) == data` over boundary + fuzz records,
    AND that with `DEFAULT_HASHING_ALGORITHM='sha1'` the patched
    `encode` routes through `_legacy_encode` so `_legacy_decode(encode(data))
    == data` (the F2P property), while the pre-patch `encode` (always
    `signing.dumps`) gives `_legacy_decode(encode(data)) == {} != data`.
Exit 0 iff every obligation holds. Imports only Django + stdlib (the modules the
patch itself uses); nothing test-private.

**Conformance check (G-CONF):** `conformance_check.py` runs the contract-stripped
impl region (shadow) against the real patched `SessionBase.encode` (oracle)
in-container on >= 1e5 Requires-satisfying inputs (boundary + fuzz records,
each crossed with both regime selector values). Pinned fuzz seed: 13279.

## 4. Deep models (not axioms)

`legacy_read` and the legacy branch of `serialize` (the `Frame(FMT_LEGACY,
keyed_digest(payload), payload)` construction) spell out the legacy framing and
reader **deeply** in the `pure`/`impl` regions. Likewise `modern_read` spells
out the modern reader (accept a modern-tagged frame whose carried signature
matches the recomputed `modern_digest` of the payload, return the payload,
else the empty record) — the acceptance shape of `signing.loads` / the modern
arm of `decode`. They are NOT consumed axioms; their fidelity to
`_legacy_encode`/`_legacy_decode`/`signing.loads` is validated by
`axiom_check.py` (G-AX) via the real round trips
`_legacy_decode(_legacy_encode(d)) == d` and `signing.loads(signing.dumps(d))
== d`. The only consumed axioms are the unchanged callees in §3
(`keyed_digest`, `modern_digest`, `modern_serialize`).
