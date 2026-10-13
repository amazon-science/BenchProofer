# refinement.md — psf__requests-1724

The operation-by-operation correspondence between `Solution.lean`'s `do` block
(the `normalizeMethod` impl region + the deep `upperSeq` model + the native
flavour stub) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (modeled callee — split into **A-consumed**, where the proof
uses the stub/axiom contract, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The construction site — `Session.request` (`requests/sessions.py`)

Gold hunks (`requests/sessions.py`):
```
- from .compat import cookielib, OrderedDict, urljoin, urlparse, urlunparse
+ from .compat import cookielib, OrderedDict, urljoin, urlparse, urlunparse, builtin_str
  ...
+
+        method = builtin_str(method)
+
         # Create the Request.
         req = Request(
             method = method.upper(),
```

The change coerces the caller-supplied `method` to the native text flavour
(`builtin_str(...)`) **before** the case-normalisation `method.upper()`, so the
method carried into the constructed `Request` is native regardless of the flavour
the caller passed.

| # | Solution.lean impl op (`normalizeMethod`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `text : List Char`, `native : Bool` | the supplied `method` (a text value) | R | a text value is modelled by its code-point sequence `List Char` plus a boolean recording the native-vs-non-native flavour (mapping.md §2). The two facets the change touches — content and flavour — are exactly these two carriers. |
| A2 | `flavour :| flavour = true` | `method = builtin_str(method)` | A-consumed | `builtin_str` is the **unchanged** native-text constructor the patch *adds a call to*; it is not the function under change. The proof consumes the stub's only contract (`flavour = true`, i.e. the produced value is native), which discharges the flavour postcondition `out.native = true`. The character content is unchanged by `builtin_str` (mapping.md §3.1), so it does not enter the content fold. G-AX runs the real `builtin_str` and confirms it always yields a native value. |
| A3 | the result chars are `upperSeq text`, i.e. the per-code-point ASCII upper map computed by the backward loop over `text` | `method.upper()` | A-reference | the case-normalisation is modelled **deeply**: `upperSeq` / `upperCp` (the spelled-out fold in the `pure` region) and the verified loop ARE the upper map. There is no consumed `upper` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `str.upper` on boundary + fuzz over the ASCII method-name domain and asserts `str.upper == upperSeq`. The real `str.upper` IS that per-code-point map on ASCII (mapping.md §3.2). |
| A4 | `return { chars := result, native := flavour }` — a token bundling upper-cased content + native flavour | `Request(method = method.upper(), …)` — the method field of the constructed request | R | the constructed `Request`'s `method` field is exactly `builtin_str(method).upper()`; `TextToken (chars, native)` is the type-refined image of that text value (content = `chars`, flavour = `native`). Every other `Request` field is untouched by the change and omitted (mapping.md §2). |

The discriminating content of the change — the carried method's **flavour must
not depend on the supplied flavour** — lives in `out.native = true` (model) ⇔ the
inserted `method = builtin_str(method)` coercion (real). The pre-image code
applied `.upper()` directly, so the carried flavour equalled the supplied
flavour; `Solution_prepatch.lean` reproduces that (`flavour := native`) and
**fails** the postcondition `out.native = true` on a non-native input — exactly
the spec sensing the change (G-DIFF). The content (loop-body) leg of the prepatch
proof discharges identically to the post-image proof; the sole unsolved goal is
`native = true`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The one operation that
genuinely *changed* — that the method is forced to the native flavour before
case-normalisation — is captured by the **A-consumed** native-flavour stub over
the **unchanged** callee `builtin_str` that the patch newly invokes, plus the
flavour postcondition. The case-normalisation `str.upper`, an **unchanged**
operation the code already performed, is modelled **deeply** (`upperSeq`, step
A3, an **A-reference**) and validated against the real callee by G-AX, not hidden
behind a consumed axiom. There is no consumed `upper` axiom and no dead axiom.

## C. verify(model) ⇒ resolved

`normalizeMethod` verifies only if (1) its output content equals the exact
per-code-point ASCII upper map of the supplied name and the length is preserved
(A3) and (2) its output flavour is native irrespective of the supplied flavour
(A2, the postcondition `out.native = true`). By R (text ↔ `List Char` + flavour
bool; `Request` field projection) the verified result equals
`builtin_str(method).upper()`; by G-AX the deep model `upperSeq` equals the real
`str.upper` (A-reference) and the real `builtin_str` meets the native-flavour
contract (A-consumed). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited callees — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
callee soundness (G-AX) and refinement fidelity (this document, G-EQ).
