# refinement.md — psf__requests-1724

The operation-by-operation correspondence between `model.py`'s implementation
(the `normalize_method` impl region + the deep `upper_seq` model + the live
`to_native` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

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

The fix coerces the caller-supplied `method` to the native text flavour
(`builtin_str(...)`) **before** the case-normalisation `method.upper()`, so the
method carried into the constructed `Request` is native regardless of the
flavour the caller passed. (On Python 2 a `unicode` method would otherwise stay
`unicode` through `.upper()` and later contaminate the byte-string headers.)

| # | model.py impl op (`normalize_method`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `chars: List[int]`, `native: bool` | the supplied `method` (a `str`/`unicode` text value) | R | a text value is modelled by its code-point sequence `List[int]` plus a boolean recording the native-vs-non-native flavour (mapping.md §2). The two facets the bug touches — content and flavour — are exactly these two carriers. |
| A2 | `native_flavour = to_native(ToSeq(chars))` | `method = builtin_str(method)` | A-consumed | `builtin_str` is the **unchanged** native-text constructor the patch *adds a call to*; it is not the function under change. `to_native` is the flavour of the value it produces for the supplied content, and the axiom's only `Ensures` — `native_form(Result())`, the opaque "that flavour is a native one" — is what discharges the second half of the flavour postcondition. The first half, `Result().native == to_native(ToSeq(chars))`, is what makes this step **mandatory**: the produced flavour is left uninterpreted, so no implementation can name it without applying `to_native` to the supplied content, i.e. without this real call (mapping.md §3.1 "Why not `Ensures(Result() == True)`"). The character content is unchanged by `builtin_str` (mapping.md §3.1), so it does not enter the content fold. G-AX runs the real `builtin_str` and confirms it always yields a native value. |
| A3 | the result chars are `upper_seq(ToSeq(chars))`, i.e. the per-code-point ASCII upper map computed by the backward loop over `chars` | `method.upper()` | A-reference | the case-normalisation operation is modelled **deeply**: `upper_seq` / `upper_cp` (the spelled-out fold in the `pure` region) and the verified loop ARE the upper map. There is no consumed `upper` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `str.upper` on boundary + fuzz over the ASCII method-name domain and asserts `str.upper == upper_seq`. The real `str.upper` IS that per-code-point map on ASCII (mapping.md §3.2). |
| A0 | `Requires(MustTerminate(3))` on `normalize_method`, `MustTerminate(1)` on the carrier constructor, and a decreasing `MustTerminate` measure on the content loop | the patched step is straight-line code — one `builtin_str` call, one `.upper()` call, one `Request(...)` construction — every part of which returns | I | the modeled step terminates for the same reason the real one does: nothing in it is recursive or unbounded, and the content loop is a bounded backward walk over the supplied name. The obligation claims no more than the real code establishes, and it is load-bearing: without it a rival may do all the modeled work and then diverge, proving every value clause from an unreachable state (properties.py `diverge-after-fold`), while its refinement is a request that never returns. |
| A4 | `return TextToken(out, native_flavour)` — a value bundling upper-cased content + native flavour | `Request(method = method.upper(), …)` — the method field of the constructed request | R | the constructed `Request`'s `method` field is exactly `builtin_str(method).upper()`; `TextToken(chars, native)` is the type-refined image of that text value (content = `chars`, flavour = `native`). Every other `Request` field is untouched by the bug and omitted (mapping.md §2). |

The discriminating content of the change — the carried method's **flavour must
not depend on the supplied flavour** — lives in `Result().native ==
to_native(ToSeq(chars))` (model) ⇔ the inserted `method = builtin_str(method)`
coercion (real). The pre-patch code applied `.upper()` directly, so the carried
flavour equalled the supplied flavour; `model_prepatch.py` reproduces that
(`native_flavour = native`) and **fails** that postcondition — the supplied
flavour is not the constructor's product for the supplied content — exactly the
spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The one operation that
genuinely *changed* — that the method is forced to the native flavour before
case-normalisation — is captured by the **A-consumed** `to_native` axiom over
the **unchanged** callee `builtin_str` that the patch newly invokes, plus the
flavour postcondition. The case-normalisation `str.upper`, an **unchanged**
operation the code already performed, is modelled **deeply** (`upper_seq`,
step A3, an **A-reference**) and validated against the real callee by G-AX, not
hidden behind a consumed axiom. There is no consumed `upper` axiom and no dead
axiom: `to_native` is consumed by the flavour postcondition, and `native_form`
is consumed by it too — `to_native`'s `Ensures` is its only source and the
postcondition its only demand.

## C. verify(model) ⇒ resolved

`normalize_method` verifies only if (1) its output content equals the exact
per-code-point ASCII upper map of the supplied name (A3), (2) its output flavour
IS the one the native-flavour constructor yields for the supplied name — not
merely a flavour the implementation asserts to be native — (A2, the
postcondition `Result().native == to_native(ToSeq(chars))` with `to_native`
uninterpreted), and (3) it returns (A0). Clause (2) is what carries the
inference: since the produced flavour is uninterpreted, a verifying
implementation must have applied the constructor to the supplied name, which
under R is the real `builtin_str(method)` call; the content clause then pins the
rest to `.upper()`. So by R (text ↔ `List[int]` + flavour bool; `Request` field
projection) the verified result equals `builtin_str(method).upper()`; by G-AX
the deep model `upper_seq` equals the real `str.upper` (A-reference) and the
real `builtin_str` meets the `to_native` axiom, i.e. its result really is of the
native flavour (A-consumed, `native_form`). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
