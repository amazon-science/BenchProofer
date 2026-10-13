# refinement.md — sphinx-doc__sphinx-7985

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `classifyLocalLink` `do` block plus the deep `classify` / `hasUriScheme`
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses the
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The non-network arm — `check()` (`sphinx/builders/linkcheck.py:212-223`)

Gold hunk (the rewritten arm; the skip guard also drops `'ftp:'`):
```
- if len(uri) == 0 or uri.startswith(('#', 'mailto:', 'ftp:')):
+ if len(uri) == 0 or uri.startswith(('#', 'mailto:')):
      return 'unchecked', '', 0
  elif not uri.startswith(('http:', 'https:')):
-     return 'local', '', 0
+     if uri_re.match(uri):
+         return 'unchecked', '', 0          # non supported URI schemes (ex. ftp)
+     else:
+         if path.exists(path.join(self.srcdir, uri)):
+             return 'working', '', 0
+         else:
+             for rex in self.to_ignore:
+                 if rex.match(uri):
+                     return 'ignored', '', 0
+             else:
+                 return 'broken', '', 0
```

| # | Solution.lean impl op (`classifyLocalLink`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `uri : List Char` | `uri: str` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `s ↔ s.toList`, `startswith ↔ List.isPrefixOf`. |
| A2 | `require isHttp uri = false` | the `elif not uri.startswith(('http:', 'https:')):` guard that gates this arm | R + I | scopes the method to the non-network arm; `isHttp` is the concrete `startswith(('http:','https:'))` test (I), used as the precondition (R: the dataflow that reached this arm). |
| A3 | `if isUnchecked uri then .unchecked` | `if len(uri)==0 or uri.startswith(('#','mailto:')): return 'unchecked'` | I | concrete transliteration of the skip-without-resolution guard. `'ftp:'` is intentionally NOT in `isUnchecked` (the gold removed it); an `ftp:`/`ftp://` link now reaches the access-method test A4. |
| A4 | `else if hasUriScheme uri then .unchecked` | `if uri_re.match(uri): return 'unchecked'` | A-reference + I | the access-method detector is modeled **deeply** by `hasUriScheme` (pure region) — no consumed `uri_re` axiom. The control flow (`if … then .unchecked`) is **I**; the equality `hasUriScheme == bool(uri_re.match)` is the **A-reference** G-AX validates (mapping.md §3.1). |
| A5 | `else if fileExists then .working` | `if path.exists(path.join(self.srcdir, uri)): return 'working'` | R + I | `path.exists(...)` is an unchanged stdlib callee; its boolean result enters as the input `fileExists` (R: `bool ↔ Bool`). The branch (`then .working`) is **I**. |
| A6 | `else if anyIgnore then .ignored` | `for rex in self.to_ignore: if rex.match(uri): return 'ignored'` | R + I | the skip-pattern loop is unchanged; its "any match" result enters as the input `anyIgnore` (R: `bool ↔ Bool`). The branch (`then .ignored`) is **I**. |
| A7 | `else .missing` | the `for…else: return 'broken'` fall-through | I | concrete transliteration of the no-match fall-through (the `.missing` constructor maps to the `'broken'` status word, mapping.md §2). |
| A8 | result `out : Status` | the `(status, '', 0)` tuple `check()` returns | R | the modeled arm always emits `info=''`, `code=0`; only the status word carries behaviour (mapping.md §2). |

Discriminating content of the change — a resolvable local link is no longer left
as the blanket `'local'` verdict but is **resolved**: present file ⇒ `'working'`,
configured skip ⇒ `'ignored'`, else missing ⇒ `'broken'`. This lives in steps
A5–A7. The pre-patch arm returned `'local'` unconditionally;
`Solution_prepatch.lean` reproduces that (`else Status.localLink`) and **fails**
`out = classify uri fileExists anyIgnore` (G-DIFF) — e.g. on
`uri = "path/to/notfound"`, `fileExists = false`, `anyIgnore = false`: prepatch ⇒
`localLink`, spec ⇒ `.missing` (the real `'broken'` status word — the F2P
`test_defaults` line `[broken] path/to/notfound`).

## B. No consumed axioms

There are no `axiom` declarations and no `:|` callee stubs. The only modeled
callee, `uri_re.match`, is modeled **deeply** (`hasUriScheme`, an A-reference
validated by G-AX), not assumed. The two other callees the arm touches
(`path.exists`, the `self.to_ignore` match loop) are **unchanged** and enter the
model only as the boolean inputs `fileExists` / `anyIgnore` (their results are
method inputs, mapping.md §3.2) — no axiom, no stub.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operations that genuinely *changed* —
adding the access-method test and the resolve-the-local-target dispatch, and
dropping `'ftp:'` from the skip guard — are modeled **concretely** (the
nested-`if` over `hasUriScheme`/`fileExists`/`anyIgnore`, steps A3–A7), not
hidden behind an axiom about the function under change. The single deeply-modeled
callee (`uri_re.match`, A4) is an **A-reference**, G-AX-checked, not a consumed
axiom.

## D. verify(Solution) ⇒ resolved

`classifyLocalLink` verifies only if its output equals `classify` exactly: a
skip-without-resolution or explicit-access-method link is `unchecked`, and every
other local target is resolved to `working`/`ignored`/`.missing` by A5–A7 (never
the blanket `localLink`). By R (`str ↔ List Char`, `bool ↔ Bool`, the
abstracted `info=''`/`code=0`) the verified classifier equals the patched
non-network arm on the tested inputs; by G-AX the deep model `hasUriScheme`
equals the real `uri_re.match` (A-reference); by G-CONF the R/I transliteration
of the control flow agrees with `patch.diff`'s behaviour on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
