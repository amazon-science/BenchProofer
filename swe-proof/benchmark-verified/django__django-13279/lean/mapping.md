# mapping.md — django__django-13279

## Instance
- repo: django/django
- base_commit: 6e9c5ee88fc948e05b4a7d9f82a8861ed2b0343d
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch makes `SessionBase.encode` (django/contrib/sessions/backends/base.py)
dispatch between two interchangeable serialization schemes based on the configured
serialization-format identifier `settings.DEFAULT_HASHING_ALGORITHM`:

```python
def encode(self, session_dict):
    "Return the given session dictionary serialized and encoded as a string."
    if settings.DEFAULT_HASHING_ALGORITHM == 'sha1':
        return self._legacy_encode(session_dict)
    return signing.dumps(
        session_dict, salt=self.key_salt, serializer=self.serializer, compress=True,
    )
```

Pre-patch, `encode` unconditionally produced the current (Django ≥ 3.1)
`signing.dumps`-based string. The patch additionally **adds** the helper
`_legacy_encode`, which rebuilds the pre-3.1 serialization format
(`base64(hmac_hex + b':' + serialized)`), i.e. exactly the format the
pre-existing, UNCHANGED `_legacy_decode` already reads:

```python
def _legacy_encode(self, session_dict):
    serialized = self.serializer().dumps(session_dict)
    hash = self._hash(serialized)
    return base64.b64encode(hash.encode() + b':' + serialized).decode('ascii')
```

The single observable behavioral change at the `encode` site is the **dispatch**:
when the configured identifier equals `'sha1'`, `encode` now emits the legacy
format (which the unchanged `_legacy_decode` round-trips); otherwise it emits the
current format unchanged. This is what lets two instances of the same project
interoperate during the 3.0→3.1 transition (problem statement).

## Symbol binding
| Lean symbol | Python source @ base_commit / patch |
|---|---|
| `implementation_encode` | `SessionBase.encode` (backends/base.py:109) — the dispatch the patch introduces |
| `problem_spec_encode`   | the post-condition `encode` must satisfy after the patch |
| `legacyEncode`          | `SessionBase._legacy_encode` (added by the patch): the pre-3.1 legacy serialization scheme |
| `modernEncode`          | the unchanged current scheme: `signing.dumps(session_dict, salt=self.key_salt, serializer=self.serializer, compress=True)` |
| `SessionDict`           | `session_dict` (a Python dict) |

`legacyEncode` and `modernEncode` are declared `opaque` (pure carriers) so the two
serialization schemes can appear in the executable impl. The modeled behavior is
*which* scheme `encode` selects, not the internal bytes of either scheme — neither
internal is inspected by the spec, and the proof consumes no property of either
(it closes by case analysis on the format identifier). Hence NO `axiom _prop` is
declared.

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `algo : String` | `settings.DEFAULT_HASHING_ALGORITHM` (str) | the configured serialization-format identifier; `'sha1'` selects the legacy scheme |
| `session : SessionDict` (`List (String × String)`) | `session_dict` (dict) | the session data to serialize; passed opaquely to both schemes |
| `legacyEncode session : String` | `self._legacy_encode(session_dict)` (str) | the legacy-format string |
| `modernEncode session : String` | `signing.dumps(...)` (str) | the current-format string |
| result `: String` | return value of `encode` (str) | the serialized string |

`String` ↔ Python `str` is the identity bijection. `algo = "sha1"` (Lean
`String` `=`) ↔ Python `settings.DEFAULT_HASHING_ALGORITHM == 'sha1'`.

`SessionDict` is modeled as `List (String × String)` purely as an inert carrier:
neither opaque scheme's modeled signature inspects it, so its internal shape is
immaterial to the spec. G-CONF bridges it to a real Python dict.

## Callee provenance / flag deps
- `modernEncode` ↔ `signing.dumps(...)` — UNCHANGED callee (the pre-patch `encode`
  body). Non-deterministic in production: `signing.dumps` appends a timestamp via
  `TimestampSigner`. G-CONF freezes the clock (`time.time`) so both the shadow and
  the real patched `encode` produce identical bytes for a given input.
- `legacyEncode` ↔ `_legacy_encode` (added by the patch) — composed entirely of
  UNCHANGED callees (`self.serializer().dumps`, `self._hash` (HMAC), `base64`),
  and is fully deterministic.
- Flag dependency: the dispatch is gated on `settings.DEFAULT_HASHING_ALGORITHM`.
  The discriminating value `'sha1'` is named verbatim in the public
  `problem_statement` ("setting DEFAULT_HASHING_ALGORITHM to 'sha1'"). G-CONF
  fuzzes `algo ∈ {'sha1', non-'sha1' values}`.

## G-CONF fuzz seed
- pinned seed: `13279`
- ≥10^5 fuzzed `(algo, session_dict)` pairs; `algo` drawn from a pool biased toward
  `'sha1'` / `'sha256'` / random strings; `session_dict` drawn from a pool of
  small JSON-serializable string→value dicts. The clock is frozen so the modern
  scheme is deterministic.
