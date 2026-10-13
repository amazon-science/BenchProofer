# refinement.md — django__django-16502

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `responseBody` and `prepareMeta` `do` blocks, plus the deep `bodyFor` /
`adjustMeta` models) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (a free-input/deep model validated == the
real callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The body-stripping site — new `finish_response` override (`basehttp.py:156`)

Gold hunk (added method):
```python
def finish_response(self):
    if self.environ["REQUEST_METHOD"] == "HEAD":
        try:
            deque(self.result, maxlen=0)  # Consume iterator.
            if not self.headers_sent:
                self.send_headers()
        finally:
            self.close()
    else:
        super().finish_response()
```

| # | Solution.lean impl op (`responseBody`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `isHead : Bool` | `self.environ["REQUEST_METHOD"] == "HEAD"` | R | method string ↔ Bool (mapping.md §2). |
| A2 | parameter `chunks : List (List Char)` | the application output iterable `self.result` | R + A-reference | chunk bytes ↔ `List Char` (mapping.md §2). That the body-bearing emission of `self.result` is the in-order concatenation is the unchanged base `BaseHandler.finish_response` write loop — an **A-reference** G-AX validates (mapping.md §3.1). |
| A3 | `out = bodyFor isHead chunks` = `[]` when `isHead`, else `chunks.flatten` | bodyless branch consumes the iterator and writes no body / else `super().finish_response()` writes the chunks in order | A-reference + I | the changed body operation is modeled **deeply** by `bodyFor`; the branch (`if isHead then [] else flatten`) is **I** (concrete, transliterated by G-CONF); equality of `chunks.flatten` to the real base emission is the **A-reference**. mapping.md §3.1. |

Discriminating content of the change — body emitted for HEAD — lives in
`bodyFor true chunks = []`. The pre-patch `ServerHandler` had no override, so the
base wrote the body unconditionally; `Solution_prepatch.lean` reproduces that
(`responseBody` returns `chunks.flatten` regardless of `isHead`) and **fails**
`out = bodyFor isHead chunks` on the discriminating clause
`isHead = true → out = []` (G-DIFF).

## B. The header-adjustment site — `cleanup_headers` (`basehttp.py:131`)

Gold hunk:
```python
def cleanup_headers(self):
    super().cleanup_headers()
+   if self.environ["REQUEST_METHOD"] == "HEAD" and "Content-Length" in self.headers:
+       del self.headers["Content-Length"]
-   if "Content-Length" not in self.headers:
+   if self.environ["REQUEST_METHOD"] != "HEAD" and "Content-Length" not in self.headers:
        self.headers["Connection"] = "close"
    elif not isinstance(self.request_handler.server, socketserver.ThreadingMixIn):
        self.headers["Connection"] = "close"
    if self.headers.get("Connection") == "close":
        self.request_handler.close_connection = True
```

| # | Solution.lean impl op (`prepareMeta`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `m.hasLength` (entry) | `"Content-Length" in self.headers` after `super().cleanup_headers()` | R + A-reference | length-present Boolean (mapping.md §2). Computed by the unchanged base callee — A-reference (mapping.md §3.2). |
| B2 | `len := if isHead then false else m.hasLength` | `if HEAD and "Content-Length" in self.headers: del self.headers["Content-Length"]` | I | clearing the length declaration for a bodyless request ↔ setting `hasLength=false` when `isHead`. |
| B3 | `term := if (!isHead && !len) then true else if !isThreadingServer then true else m.terminate` | `if method != HEAD and "Content-Length" not in headers: Connection=close` / `elif not ThreadingMixIn: Connection=close` | I | the close-marking ladder, branch-for-branch. `len` here is the **post-clear** length flag (B2), matching that the `del` runs before the `if`. |
| B4 | `willTerm := if term then true else m.willTerminate` | `if headers.get("Connection")=="close": close_connection=True` | I | committing to close when marked; otherwise preserved. |
| B5 | `out.terminate`, `out.willTerminate`, `out.hasLength` returned; `m` unchanged elsewhere | the post-state of `self.headers` / `close_connection` | R | exit-state bijection (mapping.md §2). `m` is read-only (not `mut`); the model returns a fresh `ResponseMeta`, so no unchanged field is silently overwritten (directive 5). |

Discriminating content — for HEAD, a present `Content-Length` is removed and the
`Connection: close` is *not* forced merely because length is now absent. The
pre-patch `cleanup_headers` never cleared the length and forced
`Connection: close` whenever `"Content-Length" not in self.headers`;
`Solution_prepatch_2.lean` reproduces that (`prepareMeta` never clears `len` for
HEAD and drives `term` off `!len` without the `!isHead` guard) and **fails**
`out = adjustMeta isHead isThreadingServer m` on the HEAD clauses (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. Both operations that genuinely *changed* — the body
emitted for a bodyless request, and the length/close adjustment — are modeled
**deeply** (`bodyFor`, `adjustMeta`), not hidden behind an axiom about the
function under change. There is no consumed axiom; the only A legs are
**A-reference** abstractions of the two **unchanged** base `wsgiref` callees
(body emission, length-declaration), validated by G-AX.

## D. verify(Solution) ⇒ resolved

`responseBody` verifies only if its output is empty for a bodyless request and
the in-order chunk concatenation otherwise (A3); `prepareMeta` verifies only if
it clears the length declaration for a bodyless request and follows the close
ladder exactly (B2–B4). By R (method ↔ Bool, header-presence ↔ Bool, chunk
bytes ↔ `List Char`) the verified models equal the patched
`finish_response` / `cleanup_headers` on the tested inputs; by G-AX the base
emission equals `chunks.flatten` and the base length-declaration equals
`hasLength` (A-reference); by G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE). Trust points are exactly the
two of plan §1.1: A-reference soundness (G-AX) and refinement fidelity (this
doc, G-EQ + G-CONF).
