# refinement.md — pytest-dev__pytest-7205

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_param_token` impl region and the deep `repr_quote` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, the proof uses the
axiom's `Ensures`, and **A-reference**, a deep model validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The parameter rendering site — `_show_fixture_action` (`src/_pytest/setuponly.py:69`)

Gold hunks:
```
  import pytest
+ from _pytest._io.saferepr import saferepr
  ...
  if hasattr(fixturedef, "cached_param"):
-     tw.write("[{}]".format(fixturedef.cached_param))
+     tw.write("[{}]".format(saferepr(fixturedef.cached_param, maxsize=42)))
```

The model function `render_param_token(param, maxsize)` models the token that
fills the `{}` between the constant `[` and `]` framing — the only content the
edit changes.

| # | model.py impl op (`render_param_token`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `param: List[int]` | `fixturedef.cached_param` (a `str` in the tested domain) | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | parameter `maxsize: int`, the gold's literal under spec | the literal argument `maxsize=42` | R | identical integer; `42 >= 2` and the tested params satisfy `len + 2 <= 42`, so the model's `Requires` are met by the gold call (mapping.md §2). |
| A3 | the result is `repr_quote(ToSeq(param))`, i.e. `' + param + '`, produced by prepending `[QUOTE]`, copying `param` code point by code point, then appending `QUOTE` | `saferepr(fixturedef.cached_param, maxsize=42)` | A-reference | the changed rendering is modeled **deeply**: `repr_quote` (the apostrophe delimiting in the `pure` region) and the verified loop in `render_param_token` ARE the size-limited programmer's representation on the tested domain. There is no consumed `saferepr` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `saferepr(_, maxsize=42)` on boundary + fuzz and asserts `saferepr(s, 42) == "'" + s + "'"`. The real callee IS that operation on this domain (mapping.md §3). |
| A4 | the `<= maxsize` postcondition discharged from `len(param) + 2 <= maxsize` | the `_ellipsize`-to-`maxsize` clamp inside `saferepr` | A-reference | `saferepr(_, 42)` never exceeds 42 characters; on the tested domain it equals the verbatim quoting, whose length is `len + 2 <= 42`. G-AX checks the `<= 42` bound on 5 000 long inputs as well (mapping.md §3). |
| A5 | `result` returned (a `List[int]`) and (in the repo) substituted into `"[{}]".format(...)` and `tw.write`-ed | `"[{}]".format(...)` / `tw.write(...)` | R + I | the `[`/`]` framing and `tw.write` are emitted identically pre- and post-patch (I); only the `{}` content differs, which A3 models. `str` ↔ `List[int]` for the substituted token (R). |

The discriminating content of the change — the parameter is shown as its
programmer's representation `'foo'` rather than its plain text `foo` — lives in
`repr_quote(s) == PSeq(39) + s + PSeq(39)` (model) ⇔ the `repr`-based
`saferepr(param, maxsize=42)` (real). The pre-patch rendering applied an
implicit `str(param)` (the bare `param`); `model_prepatch.py` reproduces that
(returns `param` with no delimiters) and **fails** the postcondition
`ToSeq(Result()) == repr_quote(ToSeq(param))` (and the `Result()[0] == QUOTE`
delimiter clauses), which is exactly the spec sensing the change (G-DIFF).

## B. The bytes-safety facet of the same change

The reported crash is a `BytesWarning` raised by the implicit `str()` on a
`bytes` parameter under `python -bb`. This is the SAME single edit (str-render →
saferepr-render); it is not a second site. Nagini cannot express the `-bb`
warning machinery, so the model captures the change through its *observable
display content* (the apostrophe delimiting, which the bulk of the F2P trace
tests observe), and the bytes-safety property is validated executably by
axiom_check.py: in a fresh `python -bb` subprocess (the F2P regression's exact
configuration) the new `saferepr(b'...', 42)` does not raise while the pre-patch
`"{}".format(b)` does. This is part of the A-reference of A3 (the helper renders
via `repr`, never an implicit `str()`), not a separate refinement step.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — rendering the parameter through the size-limited programmer's
representation — is modeled **deeply** (the spelled-out apostrophe delimiting
`repr_quote` consumed in `render_param_token`, step A3, an **A-reference**), not
hidden behind an axiom about the function under change: there is **no consumed
`saferepr` axiom**. The real `saferepr` appears only as the **A-reference** that
G-AX validates the deep model against. There are no A-consumed axioms in this
bundle.

## D. verify(model) ⇒ resolved

`render_param_token` verifies only if its output equals the apostrophe-delimited
verbatim parameter (A3) within the size bound (A4) — i.e. the programmer's
representation, never the plain text form. By R (`str` ↔ `List[int]`, the
identical `[`/`]`/`tw.write` framing and `maxsize=42`) the verified token equals
`saferepr(fixturedef.cached_param, maxsize=42)` on the tested parameters; by
G-AX the deep model `repr_quote` equals the real `saferepr(_, 42)` on that
domain and the real helper renders bytes without an implicit `str()` raise
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (here, the A-reference G-AX check) and refinement fidelity (this
document, G-EQ).
