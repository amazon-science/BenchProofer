# mapping.md — django__django-13279

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6e9c5ee88fc948e05b4a7d9f82a8861ed2b0343d`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each opaque building block.

Repo file under change: `django/contrib/sessions/backends/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `encodeSession (sessionData) (legacyHashMode : Bool)` | `SessionBase.encode(self, session_dict)` — `django/contrib/sessions/backends/base.py:109` | the modeled changed function (the session encoder); `legacyHashMode` ↔ `settings.DEFAULT_HASHING_ALGORITHM == 'sha1'` |
| `legacyEncoding (d)` *(deep model — pure region)* | the body the patch's `_legacy_encode` runs (`serializer().dumps` → `_hash` → base64 packaging), i.e. the legacy-compatibility textual form | pure spec: the legacy encoding, spelled out as a composition of unchanged primitives — NOT axiomatized (it is the new behavior) |
| `serialize` *(opaque — unchanged callee)* | `self.serializer().dumps` — the configured session serializer (`django/contrib/sessions/serializers.py`, JSON serializer) | unchanged building block: session data → serialized bytes |
| `hashOf` *(opaque — unchanged callee)* | `SessionBase._hash` — `base.py:104` | unchanged building block: salted keyed content hash of a serialized form (present at base_commit) |
| `wrap` *(opaque — unchanged primitive)* | `base64.b64encode(hash.encode() + b':' + serialized).decode('ascii')` | unchanged stdlib packaging: combine a hash + serialized form into one reversible textual blob |
| `standardEncoding` *(opaque — unchanged callee)* | `signing.dumps(session_dict, salt=self.key_salt, serializer=self.serializer, compress=True)` — `base.py:111` (the pre-existing standard path), inverted by `SessionBase.decode` (`base.py:116`) | unchanged building block: the standard signed-and-compressed encoding |

The patch ADDS the method `_legacy_encode` (`base.py` post-patch) and an `encode`
dispatch on `settings.DEFAULT_HASHING_ALGORITHM`. `_legacy_encode` is the operation
under spec; per directive 7 it is NOT axiomatized. It is modeled deeply by
`legacyEncoding` as the exact composition of the unchanged primitives above —
each of which exists at `base_commit`, so G-AX validates the model without ever
calling the patch-introduced method. The unchanged reader `_legacy_decode`
(`base.py:124`, present at base) is what closes the soundness loop (§3).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) and G-AX use to translate values. The carriers are kept
abstract (`Nat` aliases) because only the *structure* of the encoder's output is
observed: which encoding (legacy composition vs standard form) is produced for a
given mode. G-CONF bridges to the real Python value domain.

| repo reality | Lean carrier | bijection / justification |
|---|---|---|
| a session dictionary `session_dict` (JSON-serializable) | `SessionData` (abstract) | the encoder's input; G-CONF enumerates concrete JSON dicts (the only values these backends carry under the JSON serializer) |
| `DEFAULT_HASHING_ALGORITHM == 'sha1'` | `legacyHashMode : Bool` | `True` ↔ `'sha1'`; `False` ↔ any other value (G-CONF uses `'sha256'`, the default). The single bit the `encode` dispatch branches on. |
| `serializer().dumps(session_dict)` (bytes) | `Serialized` (abstract), via `serialize` | unchanged serialization |
| `_hash(serialized)` (hex str) | `Hash` (abstract), via `hashOf` | unchanged salted keyed hash |
| the final encoded string (legacy base64 blob OR standard signed string) | `Encoded` (abstract) | the observed output; G-CONF compares the real Python strings byte-for-byte |

The carriers are opaque identities: the spec pins `encodeSession`'s output to
`legacyEncoding sessionData` (legacy mode) or `standardEncoding sessionData`
(standard mode), structural equalities to the actual composition of the input —
never to a free-floating oracle (directive 8). G-CONF refutes the R/I dispatch
against the patched `encode`; G-AX validates the building blocks (§3).

## 3. Callee / building-block provenance (kind-A — checked by G-AX)

The changed operation is the `encode` dispatch and the new legacy encoding. The
legacy encoding is modeled DEEPLY (`legacyEncoding = wrap (hashOf (serialize d))
(serialize d)`), NOT behind an axiom — there is no consumed Prop axiom about
`_legacy_encode`. The opaque symbols name only UNCHANGED building blocks, and the
soundness obligations tie the deep model to the inverse performed by an unchanged
reader.

### 3.1 The legacy composition ↔ the unchanged legacy reader (A-reference)
`legacyEncoding` composes `serialize` (= `self.serializer().dumps`), `hashOf`
(= `self._hash`, `base.py:104`, unchanged), and `wrap` (= `base64.b64encode(
hash.encode() + b':' + serialized).decode('ascii')`). The gold `_legacy_encode`
IS exactly this composition. The soundness property the public report demands —
data written in the legacy mode must be decodable during the transition — is
checked by G-AX as

    self._legacy_decode( legacyEncoding(d) ) == d

against the REAL `_legacy_decode` (`base.py:124`), which is UNCHANGED and present
at base_commit. Because `_legacy_decode` splits on `b':'`, recomputes `_hash` over
the serialized part, compares it (constant-time) to the stored hash, and reloads
the serialized payload, the composition round-trips iff `wrap`/`hashOf`/`serialize`
are the pieces it expects — which is what makes `legacyEncoding` the faithful deep
model of the new `_legacy_encode`. G-AX runs entirely at base_commit (no patch).

### 3.2 The standard path ↔ its loader (A-reference)
`standardEncoding` = `signing.dumps(..., compress=True)` (`base.py:111`,
unchanged). G-AX checks `self.decode(signing.dumps(d, ...)) == d` against the REAL
unchanged `decode`/`signing.loads`. Both predate the patch.

**Soundness check (G-AX):** `axiom_check.py` drives the real base-commit callees
over 13 boundary + ~5000 fuzz JSON session dicts under `DEFAULT_HASHING_ALGORITHM
= 'sha1'` (legacy) and `'sha256'` (standard), asserting both round trips. Imports
only stdlib + django. Exit 0 iff every obligation holds. Crucially it NEVER calls
`_legacy_encode` (the patch-introduced method, absent at base) — it reconstructs
the composition from base primitives.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13279`**. It runs WITH
the patch applied (the oracle is the patched `encode`); it freezes `time.time` to
`1_600_000_000.0` so the timestamped standard form is byte-stable, and it sets
`settings.DEFAULT_HASHING_ALGORITHM` BEFORE computing each of the shadow and the
oracle (the standard signer's HMAC algorithm — hence its signature — depends on
it). The shadow transliterates the R/I dispatch: the legacy branch as the deep
composition (base callees), the standard branch left as the real `signing.dumps`
(A-tagged). Diffs byte-for-byte over ≥10⁵ inputs across both modes; 0 disagreements.
