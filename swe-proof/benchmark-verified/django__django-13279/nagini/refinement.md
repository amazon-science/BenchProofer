# refinement.md — django__django-13279

The operation-by-operation correspondence between `model.py`'s implementation
(the `serialize` impl region, the deep `legacy_read` model, and the two
consumed axioms) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — split into **A-consumed**, where
the proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The serializer regime branch — `encode()` (`base.py:109`)

Gold hunk:
```
 def encode(self, session_dict):
     "Return the given session dictionary serialized and encoded as a string."
+    # RemovedInDjango40Warning: DEFAULT_HASHING_ALGORITHM will be removed.
+    if settings.DEFAULT_HASHING_ALGORITHM == 'sha1':
+        return self._legacy_encode(session_dict)
     return signing.dumps(
         session_dict, salt=self.key_salt, serializer=self.serializer,
         compress=True,
     )
```
and the added helper:
```
+def _legacy_encode(self, session_dict):
+    # RemovedInDjango40Warning.
+    serialized = self.serializer().dumps(session_dict)
+    hash = self._hash(serialized)
+    return base64.b64encode(hash.encode() + b':' + serialized).decode('ascii')
```

| # | model.py impl op (`serialize`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `payload: List[int]` | `session_dict` (serialized by `self.serializer().dumps`) | R | dict→bytes serialization is an unchanged invertible identity layer folded into the payload carrier `List[int]`/`PSeq[int]` (mapping.md §2). |
| A2 | parameter `algorithm: int`; branch `if algorithm == ALGO_LEGACY` | `if settings.DEFAULT_HASHING_ALGORITHM == 'sha1'` | R | `'sha1'` ↔ `ALGO_LEGACY (0)`; any other value (default `'sha256'`) ↔ the `!= ALGO_LEGACY` arm (mapping.md §2). The control-flow branch is identical in shape. |
| A3 | legacy arm: `return Frame(FMT_LEGACY, keyed_digest(body), body)` where `body = ToSeq(payload)` | `return self._legacy_encode(session_dict)` → `b64encode(self._hash(serialized).encode()+b':'+serialized)` | R + A-consumed | the legacy frame is built deeply: the `Frame{tag=FMT_LEGACY, mac=keyed_digest(payload), payload}` structure mirrors `(hash, b':', serialized)`; `base64`/`split(b':',1)` are invertible wrappers (R, mapping.md §2). The hash field is `keyed_digest` (A-consumed, §3.1) ↔ `self._hash`. |
| A4 | modern arm: `return modern_serialize(ToSeq(payload))` | `return signing.dumps(session_dict, salt=..., serializer=..., compress=True)` | A-consumed | `modern_serialize` is the unchanged `signing.dumps` callee; the proof consumes `tag == FMT_MODERN` AND that the emitted modern frame carries exactly the given payload with its own modern signature (`payload == p`, `mac == modern_digest(p)`), which closes the modern-regime postcondition `modern_read(Result...) == ToSeq(payload)` — the modern round trip `signing.loads(signing.dumps(d)) == d` the unchanged `decode` performs on every modern session (mapping.md §3.2). An impl that hands `signing.dumps` a DIFFERENT record (empty, constant, truncated) violates this clause. |

## B. The legacy reader (round-trip target) — `_legacy_decode()` (`base.py:124`)

`_legacy_decode` is unchanged by the patch; it is the reader the F2P test rounds
back through. The model spells it out deeply as `legacy_read`:

| # | model.py construct | repo op | tag | justification |
|---|---|---|---|---|
| B1 | `legacy_read(tag, mac, payload)`: accept iff `tag==FMT_LEGACY and mac==keyed_digest(payload)`, return `payload`, else `empty_payload()` | `_legacy_decode`: `b64decode`→`split(b':',1)`→`constant_time_compare(hash, self._hash(serialized))`→`serializer().loads(serialized)` else `{}` | R + A-consumed | deep model: the tag/structure check ↔ "is a legacy frame"; `mac==keyed_digest(payload)` ↔ `constant_time_compare(hash, self._hash(serialized))` (constant-time vs plain equality is observationally the same boolean; A-consumed `keyed_digest` §3.1); returning `payload` ↔ `serializer().loads(serialized)` composed with the folded-out serializer identity; `empty_payload()` ↔ `{}` (mapping.md §2). |
| B2 | postcondition `Implies(algorithm==ALGO_LEGACY, legacy_read(Result().tag, Result().mac, Result().payload) == ToSeq(payload))` | the F2P obligation: `with DEFAULT_HASHING_ALGORITHM='sha1': _legacy_decode(encode(data)) == data` | A-consumed + I | the round-trip identity closes because `legacy_read(FMT_LEGACY, keyed_digest(p), p)` returns `p` (the carried digest equals the recomputed digest, by determinism of `keyed_digest`, §3.1). This is exactly `test_default_hashing_algorith_legacy_decode`. |
| B3 | postcondition `Implies(algorithm != ALGO_LEGACY, modern_read(Result().tag, Result().mac, Result().payload) == ToSeq(payload))` with the deep `modern_read` (accept iff `tag==FMT_MODERN and mac==modern_digest(payload)`, return `payload`, else empty) | the P2P observable under the default modern regime: `signing.loads(encode(data)) == data` (the unchanged `decode`'s accepting arm), exercised by `test_decode`/`test_save`/`test_cycle`/`test_store` across the session backends | A-consumed + I | the round-trip identity closes because `modern_serialize(p)` carries exactly `p` with `modern_digest(p)` (§3.2 facts 2–3), so `modern_read` returns `p`. This pins the modern arm's CARRIED RECORD to the input — an impl that ships a different record in a modern-tagged frame fails this clause, matching the real suite where every modern session round-trips through `signing.loads`. |

## C. Why the pre-patch fails the spec (G-DIFF)

The pre-patch `encode` unconditionally `return signing.dumps(...)`.
`model_prepatch.py` reproduces this (`return modern_serialize(ToSeq(payload))`
regardless of `algorithm`). In the legacy regime its result has
`tag == FMT_MODERN` (the `modern_serialize` axiom), so
`legacy_read(FMT_MODERN, …) == empty_payload()`, and the postcondition B2
`empty_payload() == ToSeq(payload)` does not hold for a non-empty payload.
Nagini fails exactly on that clause (verified: "Postcondition of serialize might
not hold … legacy_read(...) == ToSeq(payload)"). The real consequence is the
F2P failure: pre-patch, `_legacy_decode(encode(data))` returns `{}`, not `data`.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — the new
regime branch routing the legacy regime through the legacy framing — is modeled
**deeply** (the `if algorithm == ALGO_LEGACY` branch building the legacy `Frame`,
plus the deep `legacy_read`), not hidden behind an axiom about the function under
change. The three consumed axioms (`keyed_digest`, `modern_digest`,
`modern_serialize`) cover only **unchanged** callees the new code invokes
(`self._hash`, the modern signature, and `signing.dumps`). There is no consumed
axiom about `encode` / `_legacy_encode` / `_legacy_decode` themselves.

## E. verify(model) ⇒ resolved

`serialize` verifies only if, under the legacy regime, the emitted frame is read
back by the legacy reader to the exact input payload (B2), which forces the
legacy-framing branch (A3) — an impl cannot satisfy it by echoing a constant,
because closing `legacy_read` requires a frame whose carried `mac` equals
`keyed_digest(payload)` for the actual `payload` (an opaque pure digest it cannot
fabricate for a wrong payload), and `legacy_read` of a modern-tagged frame is
empty. Symmetrically, under the modern regime the emitted frame must be read back
by the modern reader to the exact input payload (B3): closing `modern_read`
requires a modern-tagged frame whose carried `mac` equals `modern_digest` of the
CARRIED payload and whose carried payload equals the input — the only verifying
route is `modern_serialize(ToSeq(payload))` (or an equivalent frame), so an impl
that ships the empty record, a constant, or a truncated record in the modern
frame is rejected. By R (dict↔payload serializer identity, str-flag↔int
selector, base64/split wrappers) the verified serializer equals the gold
`encode` on the tested records IN BOTH regimes; by G-AX the deep
`legacy_read`/legacy-framing/`modern_read` equal the real
`_legacy_decode`/`_legacy_encode`/`signing.loads` round trips and the axioms
over-approximate `self._hash`, the modern signature, and `signing.dumps`.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
