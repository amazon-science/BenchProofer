# refinement.md — django__django-13279

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`encodeSession` `do` block, plus the deep `legacyEncoding` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A**
(opaque callee — **A-consumed** where the proof uses a Prop axiom's `ensures`,
**A-reference** where a deep model / opaque building block is validated == the
real callee by G-AX), or **I** (identical concrete op). Every step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The encode dispatch — `SessionBase.encode` (`base.py:109`)

Gold hunk:
```
 def encode(self, session_dict):
     "Return the given session dictionary serialized and encoded as a string."
+    # RemovedInDjango40Warning: DEFAULT_HASHING_ALGORITHM will be removed.
+    if settings.DEFAULT_HASHING_ALGORITHM == 'sha1':
+        return self._legacy_encode(session_dict)
     return signing.dumps(
         session_dict, salt=self.key_salt, serializer=self.serializer, compress=True,
     )
```
plus the added method:
```
+def _legacy_encode(self, session_dict):
+    serialized = self.serializer().dumps(session_dict)
+    hash = self._hash(serialized)
+    return base64.b64encode(hash.encode() + b':' + serialized).decode('ascii')
```

| # | Solution.lean impl op (`encodeSession`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `sessionData : SessionData` | `session_dict` arg | R | session dict ↔ abstract `SessionData` (mapping.md §2). G-CONF enumerates concrete JSON dicts. |
| A2 | param `legacyHashMode : Bool` | `settings.DEFAULT_HASHING_ALGORITHM == 'sha1'` | R | the dispatch bit. `True ↔ 'sha1'`, `False ↔ otherwise` (mapping.md §2). |
| A3 | `if legacyHashMode then … else …` | `if settings.DEFAULT_HASHING_ALGORITHM == 'sha1': … ; return signing.dumps(…)` | I | the CHANGED control-flow op: a single concrete flag dispatch. Transliterated 1:1 by G-CONF. |
| A4 | legacy branch `legacyEncoding sessionData` = `wrap (hashOf (serialize d)) (serialize d)` | `self._legacy_encode(session_dict)` = `b64encode(_hash(serializer().dumps(d)).encode()+b':'+serializer().dumps(d))` | A-reference + I | the new behavior is modeled DEEPLY as the exact composition of UNCHANGED primitives (`serialize`=`serializer().dumps`, `hashOf`=`_hash`, `wrap`=base64 packaging). The composition ops are **I** (transliterated by G-CONF); the soundness fact (this composition is read back by the unchanged `_legacy_decode`) is the **A-reference** G-AX validates (mapping.md §3.1). NO consumed axiom about `_legacy_encode`. |
| A5 | standard branch `standardEncoding sessionData` | `signing.dumps(session_dict, salt=self.key_salt, serializer=self.serializer, compress=True)` | A-reference | the UNCHANGED standard path. `standardEncoding` is the opaque building block; G-CONF leaves it as the real `signing.dumps`; G-AX validates `decode(signing.dumps d) == d` (mapping.md §3.2). |
| A6 | `return result` (`Encoded`) | `return …` (the encoded `str`) | R | encoded string ↔ abstract `Encoded`; G-CONF compares the real strings byte-for-byte. |

Discriminating content of the change — in legacy mode the output must be the
legacy-compatibility form (not the standard signed form) — lives in the
postcondition `legacyHashMode = true → out = legacyEncoding sessionData`. The
pre-patch `encode` had no dispatch and always returned the standard form;
`Solution_prepatch.lean` reproduces that and **fails** exactly that clause
(`standardEncoding sessionData = legacyEncoding sessionData` is unprovable for
distinct opaque encoders) — G-DIFF.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the flag
dispatch and the new legacy encoding — is modeled **concretely** (A3, the `if`)
and **deeply** (A4, the spelled-out `legacyEncoding` composition), NOT hidden
behind an axiom about the function under change. There is no consumed Prop axiom
about `_legacy_encode` or `encode`. The opaque symbols name only UNCHANGED
building blocks (`serialize`/`hashOf`/`wrap`/`standardEncoding`), each an
A-reference validated against its real base-commit callee by G-AX.

## C. verify(Solution) ⇒ resolved

`encodeSession` verifies only if its output is `legacyEncoding sessionData` in
legacy mode (A4) and `standardEncoding sessionData` otherwise (A5). By R
(`SessionData`/`Encoded`/`Bool` bijections) the verified dispatch equals the
patched `encode` on every input/mode; by G-AX the deep model `legacyEncoding` is
read back by the unchanged `_legacy_decode` (A-reference) — the property the
public report demands — and the standard path round-trips through the unchanged
loader (A-reference); by G-CONF the R/I transliteration of the dispatch agrees
byte-for-byte with `patch.diff`'s behaviour on ≥10⁵ inputs across both modes.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and validated unchanged callees — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: building-
block soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
