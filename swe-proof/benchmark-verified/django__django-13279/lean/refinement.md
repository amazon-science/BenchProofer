# refinement.md — django__django-13279

Maps every operation in `implementation_encode` to its `patch.diff` counterpart
in `SessionBase.encode` (django/contrib/sessions/backends/base.py — see
mapping.md). Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** deep-modeled changed op validated == real callee, **I**
identical concrete op.

## Patch (post-patch `encode`)
```python
def encode(self, session_dict):
    "Return the given session dictionary serialized and encoded as a string."
    if settings.DEFAULT_HASHING_ALGORITHM == 'sha1':
        return self._legacy_encode(session_dict)
    return signing.dumps(
        session_dict, salt=self.key_salt, serializer=self.serializer, compress=True,
    )
```
(The patch also ADDS the `_legacy_encode` helper; its body — `base64(self._hash(
serialized) + b':' + serialized)` — is the concrete realization of the opaque
`legacyEncode` carrier, exercised by G-CONF.)

## Operation correspondence
| # | Lean op (`implementation_encode`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if algo == "sha1" then` | `if settings.DEFAULT_HASHING_ALGORITHM == 'sha1':` | R | `settings.DEFAULT_HASHING_ALGORITHM : str ↔ algo : String`; Python `==` on `str` ↔ Lean `==` on `String`. The discriminating literal `'sha1' ↔ "sha1"`. Type bijection in mapping.md. |
| 2 | `return legacyEncode session` | `return self._legacy_encode(session_dict)` | R | `self._legacy_encode ↔ legacyEncode` — the compatibility serialization scheme (added by the patch, but composed entirely of UNCHANGED callees: `self.serializer().dumps`, `self._hash` HMAC, `base64`). Declared `opaque` so the scheme can appear in the executable impl; G-CONF realizes it as the real `_legacy_encode`. `session_dict ↔ session`. |
| 3 | `return modernEncode session` | `return signing.dumps(session_dict, salt=self.key_salt, serializer=self.serializer, compress=True)` | R | `signing.dumps(...) ↔ modernEncode` — the standard scheme (the UNCHANGED pre-patch `encode` body). Declared `opaque`; G-CONF realizes it as the real `signing.dumps` (clock frozen for determinism — mapping.md). `session_dict ↔ session`. |

Every op is **R** (or the implicit early-return control flow, an **I** skeleton
op). **No A row is consumed:** `legacyEncode`/`modernEncode` are declared `opaque`
purely so the two unchanged serialization schemes can appear in the executable
impl, and the proof closes by case analysis on the format identifier (`algo ==
"sha1"`), consuming NO property of either scheme. There is no `axiom
legacyEncode_prop`/`modernEncode_prop`. Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The impl is all R/I (no A-tagged op), so `conformance_check.py` mechanically
differential-tests the impl shadow — `legacyEncode`/`modernEncode` realized as the
real `_legacy_encode` / `signing.dumps(..., compress=True)` — against the real
patched `SessionBase.encode` over ≥10^5 fuzzed `(algo, session_dict)` inputs, with
the clock frozen so the timestamped modern scheme is deterministic. The test pins
the DISPATCH (the only behavioral edit): `algo == 'sha1'` ⇒ legacy bytes;
otherwise ⇒ modern bytes. `conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` omits the dispatch (op #1/#2): it unconditionally
returns `modernEncode session`. That is exactly the pre-patch `encode`
(`return signing.dumps(..., compress=True)`, no `DEFAULT_HASHING_ALGORITHM`
branch) — the real bug from the issue: with the format identifier set to `'sha1'`
the current scheme is still emitted, producing a string the matching legacy
reader (`_legacy_decode`) cannot round-trip, so side-by-side instances during the
transition cannot decode each other's session data. It cannot satisfy
`problem_spec_encode` on the `algo = "sha1"` clause (which demands `result =
legacyEncode session`, distinct from `modernEncode session`), so its
`correct_encode` is unclosable ⇒ G-DIFF fails verification as required (confirmed
by `lean_verify` exit 1: the `algo = "sha1"` goal `pure (modernEncode session) =
legacyEncode session` cannot close). This is the behavior the FAIL_TO_PASS test
`test_default_hashing_algorith_legacy_decode` exercises (with
`DEFAULT_HASHING_ALGORITHM='sha1'`, `encode` then `_legacy_decode` must
round-trip the data).
