# refinement.md — pytest-dev__pytest-5787

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `serializeReport`, `deserializeReport`, and `roundTripReport` `do` blocks,
plus the deep models `encode`/`decode`) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (deep model validated == real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A legs** (no foreign callee is axiomatized — §C), so G-CONF carries the
full mechanical burden and G-EQ audits only the narrative.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The serialization site — `_to_json` → `_report_to_json` (`reports.py:154`)

Gold hunks: `_to_json`'s body becomes `return _report_to_json(self)`; the new
module function `_report_to_json` adds `serialize_longrepr`, which for an
`ExceptionChainRepr` serializes the full `chain`:
```
+    if isinstance(rep.longrepr, ExceptionChainRepr):
+        result["chain"] = []
+        for repr_traceback, repr_crash, description in rep.longrepr.chain:
+            result["chain"].append((serialize_repr_traceback(repr_traceback),
+                                    serialize_repr_crash(repr_crash), description))
+    else:
+        result["chain"] = None
```

Modeled method: `serializeReport`, deep model `encode`.

| # | Solution.lean impl op (`serializeReport`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `r : TraceReport` | `self`'s `longrepr` rendered object | R | `ReprExceptionInfo` ↔ `.simple`, `ExceptionChainRepr` ↔ `.chained` (mapping.md §2). `isinstance(.., ExceptionChainRepr)` ↔ the `.chained` match arm. |
| A2 | `.simple t s xs => { text:=t, summary:=s, extras:=xs, chain := none }` | non-chain longrepr: `serialize_longrepr` stores `reprtraceback`/`reprcrash`/`sections` and `result["chain"] = None` | I + R | text/summary are the verbatim-preserved tokens carried by the unchanged per-link codec (R, mapping.md §2); `chain := none` ↔ `result["chain"] = None`. |
| A3 | `.chained ls xs =>` `last := ls.getLast?` `; { text := last.text, summary := last.summary, extras := xs, chain := some ls }` | `ExceptionChainRepr` branch: serialize the full `chain` list; top-level `reprtraceback`/`reprcrash` come from `chain[-1]` (`code.py:889-890`) | I + R | `chain := some ls` ↔ the gold-added `result["chain"] = [...]` over **all** links; `text/summary := last.*` ↔ the top-level fields echoing `chain[-1]`. Each serialized link's content is carried verbatim by `serialize_repr_traceback`/`serialize_repr_crash` (unchanged codec, R). This is the behavioral change: the whole chain is stored, not just the outermost link. |

## B. The deserialization site — `_from_json` → `_report_kwargs_from_json` (`reports.py:205`)

Gold hunk: `_from_json` becomes `kwargs = _report_kwargs_from_json(reportdict); return cls(**kwargs)`; `_report_kwargs_from_json` rebuilds a chain when present:
```
+    if reportdict["longrepr"]["chain"]:
+        chain = []
+        for repr_traceback_data, repr_crash_data, description in reportdict["longrepr"]["chain"]:
+            chain.append((deserialize_repr_traceback(...), deserialize_repr_crash(...), description))
+        exception_info = ExceptionChainRepr(chain)
+    else:
+        exception_info = ReprExceptionInfo(reprtraceback, reprcrash)
```

Modeled method: `deserializeReport`, deep model `decode`.

| # | Solution.lean impl op (`deserializeReport`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `match s.chain with` | `if reportdict["longrepr"]["chain"]:` | R | presence of the serialized link list ↔ `Serialized.chain = some _` vs `none` (mapping.md §2). |
| B2 | `some ls => .chained ls s.extras` | the `chain` branch: rebuild every link, `exception_info = ExceptionChainRepr(chain)`; sections restored by `addsection(*section)` | I + R | the gold-added branch: a stored chain rebuilds an `ExceptionChainRepr` preserving **all** links in order (each link's traceback/crash deserialized verbatim by the unchanged codec, R); `s.extras` ↔ the restored `sections`. |
| B3 | `none => .simple s.text s.summary s.extras` | the `else` branch: `exception_info = ReprExceptionInfo(reprtraceback, reprcrash)` | I + R | no stored chain rebuilds a single-exception representation from the top-level text/summary tokens (R) and restored sections. |

## B′. The lifecycle — `roundTripReport`

| # | Solution.lean op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| C1 | `let s ← serializeReport r` | `data = report._to_json()` | I | callee-under-spec: `prove_correct` supplies `serializeReport_correct` (`s = encode r`). |
| C2 | `let out ← deserializeReport s` | `loaded = report_class._from_json(data)` | I | callee-under-spec: `deserializeReport_correct` (`out = decode s`). Composition + `decode_encode` gives `out = r`. |

`roundTripReport`'s postcondition `out = r` is the exact property the F2P test
asserts: after `report_class._from_json(report._to_json())`, the loaded longrepr
is again an `ExceptionChainRepr` with `len(longrepr.chain) == 2` and both links'
content (`"ValueError('value error')"` in `str(tb1)`,
`"RuntimeError('runtime error')"` in `str(tb2)`, `desc1` the cause phrase,
`desc2 is None`) and `sections == [("title", "contents", "=")]` intact. With a
chained `r`, `decode (encode (.chained ls xs)) = .chained ls xs` — every link
preserved, not collapsed to one.

## Discriminating clause / prepatch

The behavioral change lives in the chain handling, reproduced by
`Solution_prepatch.lean` (byte-identical spec, G-DIFF): `serializeReport`'s
`.chained` pre-image keeps only the outermost link's text/summary and sets
`chain := none` (drops the link list) — exactly the pre-patch `_to_json`, which
serialized only the top-level `reprtraceback`/`reprcrash` and on deserialization
rebuilt a single `ReprExceptionInfo`. That reversion fails `s = encode r` on the
`.chained` arm (`chain := none ≠ some ls`), and would make `roundTripReport`
reconstruct `.simple last.text last.summary xs` instead of `.chained ls xs` —
collapsing the N-link chain to its outermost exception, exactly the bug
(#5786) the F2P `test_chained_exceptions` catches (`len(longrepr.chain) == 2`
fails). A single prepatch suffices: the whole observable change is on the one
F2P behavior (a serialize→deserialize round trip of a chained-exception report),
and the spec must stay byte-identical across the prepatch.

## C. No kind-3 (inexpressible-changed-op) steps; no A legs

Every step is R or I. The operation that genuinely changed — serializing and
restoring the **full exception chain** instead of only its outermost link
(A3/B2) — is modeled **directly** in the impl/deep-models, not behind an axiom.
The unchanged per-link codecs (`serialize_repr_*` / `deserialize_repr_*`) carry
their content verbatim through the round trip and are modeled as the
content-preserving R refinement (`Link.text`/`Link.summary` opaque tokens,
mapping.md §2), not as consumed axioms — the proof depends on nothing about them
beyond round-trip identity, which G-CONF exercises end-to-end against the real
codecs. There is therefore **no consumed axiom and no deep-model reference**
(`axioms` region empty; `meta.json axioms=[]`, `deep_model_references=[]`; G-AX
skips).

## D. verify(Solution) ⇒ resolved

`roundTripReport` verifies only if `serializeReport` stores the full chain (A3)
and `deserializeReport` rebuilds it (B2) — i.e. only the gold data-flow satisfies
the frozen spec (`decode_encode`). By R (longrepr-object ↔ `TraceReport`,
content-preserving link tokens) the verified lifecycle equals
`report_class._from_json(report._to_json())` on the tested inputs; G-CONF refutes
any R/I infidelity over fuzzed reports (including multi-link chains) by
differential execution against the patched real serialization functions.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this doc + G-CONF); there is no axiom trust
point for this bundle.
