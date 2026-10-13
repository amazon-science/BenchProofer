# refinement.md — django__django-11119

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`valueToDisplay` `do` block, the callee-under-spec `escapeCodepoints`, and the
deep `escapedSeq`/`entity` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-reference** (a deep model validated == the
real callee by `axiom_check.py` / G-AX; there is **no consumed axiom**), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg and this narrative are audited by **G-EQ**. Claim:
*any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The render site — `Engine.render_to_string` (`django/template/engine.py:150`)

Gold hunk (body line 171):
```
         if isinstance(context, Context):
             return t.render(context)
         else:
-            return t.render(Context(context))
+            return t.render(Context(context, autoescape=self.autoescape))
```

The single changed token threads `autoescape=self.autoescape` into the `Context`
constructor. `Context.__init__` defaults `autoescape=True`
(`django/template/context.py:137`); pre-patch the engine's configured
`self.autoescape` was dropped, so the rendering context always escaped. The
observable change: a context value is escaped **iff the engine's policy says
so**, instead of always. Downstream, `render_value_in_context`
(`django/template/base.py:962`) branches on `context.autoescape`: escape via
`conditional_escape(str(value))` when on, plain `str(value)` when off.

| # | Solution.lean impl op (`valueToDisplay`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `encodeMarkup : Bool` | `self.autoescape` (`engine.py:44`), now passed as `Context(context, autoescape=self.autoescape)` | R | the escaping policy flag `bool` ↔ `Bool`; `True`/`False` ↔ `true`/`false`; the threaded value becomes `context.autoescape` (mapping.md §2). |
| A2 | param `value : List Char` | a context value `{'obj': <str>}` rendered by `{{ obj }}` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. `str(value)`/`template_localtime`/`localize` are identities on plain-`str` inputs (mapping.md §2). |
| A3 | `if encodeMarkup then escapeCodepoints value else pure value` | `render_value_in_context`: `if context.autoescape: conditional_escape(str(value)) else: str(value)` (`base.py:970-973`) reached because the patched `Context` now carries `self.autoescape` | I (under R) | the value is escaped iff the (now correctly threaded) policy is on, else returned verbatim. The flag governs the branch — exactly the `if encodeMarkup` selection. The bug was that pre-patch this branch always took the escape leg. |
| A4 | `escapeCodepoints value` ⇒ `escapedSeq value`: the per-code-point substitution (backward `while` fold) | `conditional_escape(str(value))` ≡ `escape(value)` for a plain `str`, = `str(value).translate(_html_escapes)` (`html.py:36`) | A-reference + I | the escaping callee is modeled **deeply**: `escapedSeq`/`entity` (pure region) and the verified loop ARE the substitution `& → &amp;`, `< → &lt;`, `> → &gt;`, `" → &quot;`, `' → &#39;`, else identity. No consumed escape axiom. The fold ops (`entity c`, `++`, the loop) are **I** (transliterated by G-CONF); the equality of that deep model to the real escaping callee is the **A-reference** G-AX validates. mapping.md §3.1. |
| A5 | result `out` (`List Char`) is the rendered value text | `t.render(...)` emits the value's display text into the template stream (here wrapped by the literal `obj:`/`\n` TextNodes) | R + I | the rendered character content the F2P test observes equals `out`; the fixed surrounding template literal is an I passthrough (mapping.md §2). |

Discriminating content of the change lives in **A3**: post-patch, when the
policy is OFF (`encodeMarkup = false`) the value is rendered **verbatim**;
pre-patch the context was built with the default `autoescape=True`, so the value
was **always escaped**. `Solution_prepatch.lean` reproduces the pre-patch
skeleton (`out ← escapeCodepoints value` unconditionally — always escape) and
**fails** the postcondition on the `encodeMarkup = false` clause (G-DIFF,
confirmed: unsolved goal `x = if encodeMarkup then escapedSeq value else value`
with `x = escapedSeq value`). This is precisely the F2P test
`test_autoescape_off`: `Engine(autoescape=False).render_to_string(...)` of
`{'obj': '<script>'}` must give `obj:<script>\n`, not `obj:&lt;script&gt;\n`.

## B. The legacy apostrophe encoding (commit-pinned)

At THIS `base_commit` the escaper is `str.translate(_html_escapes)` with
`' → &#39;` (legacy decimal). `entity '\'' = "&#39;".toList` encodes that. The
later Django switch to `html.escape` (apostrophe → `&#x27;`) is a **different
instance** (11276) and is NOT imported here — G-AX would fail if the model used
`&#x27;`. (mapping.md §3.1.)

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely changed —
*whether the rendering escapes the value*, governed by the threaded policy flag
— is modeled **concretely** (the `if encodeMarkup` selection, A3), not hidden
behind an axiom about the function under change. There is **no consumed axiom**:
the only callee in the escape leg, the markup escaper, is **unchanged** and is
modeled **deeply** as the A-reference `escapedSeq` (validated == the real callee
by G-AX, mapping.md §3) — modeling it as a consumed axiom would be a dead axiom.

## D. Read-only inputs / directive 5

Both inputs are read-only: neither `encodeMarkup` nor `value` is declared `mut`,
and the rendering mutates nothing (directive 5: an unmutated param needs no
`mut` and no `ensures xOld = x`). The result is a **fresh** list (built by the
escape copy loop, or `value` returned verbatim) — a wrong impl cannot satisfy
the postcondition by overwriting an input; it must *produce* the policy-correct
display text. Because the spec pins both branches (escaped when on, verbatim
when off), the only impl that verifies is the one that honors the flag — which
is why the always-escape prepatch cannot verify.

## E. verify(Solution) ⇒ resolved

`valueToDisplay` verifies only if its result is the per-code-point escape when
`encodeMarkup` is on AND the verbatim value when off (the postcondition). By R
(`bool ↔ Bool`, `str ↔ List Char`, the `str()`/`mark_safe`/template-literal
identities) the verified rendering equals the patched
`Context(context, autoescape=self.autoescape)` path on the tested inputs; by
G-AX the deep model `escapedSeq` equals the real escaping callee (A-reference);
by G-CONF the R/I transliteration agrees with `patch.diff`'s `render_to_string`
behaviour over both autoescape settings on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of plan §1.1: refinement
fidelity (this doc, G-EQ + G-CONF) and callee-reference soundness (G-AX); there
is no consumed axiom.
